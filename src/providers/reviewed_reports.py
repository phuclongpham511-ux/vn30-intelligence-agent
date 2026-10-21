"""Offline, hash-pinned original-report evidence for the existing financial engine.

Selected annual fields only. Page text/transcriptions and rendered pages remain
private. A review is not an audit opinion, publication vintage or public licence.
"""
from datetime import date, datetime
from decimal import Decimal
import hashlib
from pathlib import Path
import re
from typing import Literal
from pydantic import Field
from src.providers.financial_filings import StrictEvidence, _https
from src.providers.vnstock.financial_statements import MAP, NON_FINANCIAL_ONLY, BANK_ONLY, content_hash
from src.schemas.financials import FinancialPacket, FinancialSourceContext, FinancialLine, StatementObservation, StatementReceipt

FIELD_KIND = {field: kind for kind, fields in MAP.items() for field in fields}


class PageEvidence(StrictEvidence):
    number: int = Field(ge=1, le=10000)
    text: str = Field(min_length=1, max_length=50000)
    text_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    image_file: str
    image_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    method: Literal['pdf_text_and_visual_review', 'visual_transcription']


class Quote(StrictEvidence):
    page: int
    text: str = Field(min_length=1, max_length=4000)


class ReportAmount(StrictEvidence):
    field: str
    code: str = Field(min_length=1, max_length=100)
    code_kind: Literal['printed_statement_code', 'reviewed_row_locator']
    label: str = Field(min_length=1, max_length=300)
    year: int = Field(ge=1900, le=2200)
    raw_token: str = Field(min_length=1, max_length=64)
    column_periods: list[str] = Field(min_length=1, max_length=4)
    column_values: list[str] = Field(min_length=1, max_length=4)
    source_row: Quote
    column_header: Quote
    unit_quote: Quote
    unit: Literal['VND', 'thousand VND', 'million VND', 'billion VND', 'VND/share']
    period_start: str | None = None
    period_end: str


class ReviewedReport(StrictEvidence):
    contract: Literal['reviewed-report-v2']
    ticker: str = Field(pattern=r'^[A-Z0-9]{1,20}$')
    source: str = Field(pattern=r'^issuer:[A-Za-z0-9_.:-]+$')
    issuer: str = Field(min_length=1, max_length=300)
    profile: Literal['non_financial', 'bank', 'financial_other']
    company_type: Literal['CT', 'NH', 'CK', 'BH']
    document_url: str
    discovery_url: str
    document_file: str
    document_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    observed_at: str
    review_reference: str = Field(min_length=1, max_length=300)
    scope: Literal['consolidated', 'standalone']
    scope_quote: Quote
    identity_quote: Quote
    calendar_quote: Quote
    currency_quote: Quote
    pages: list[PageEvidence] = Field(min_length=1, max_length=50)
    amounts: list[ReportAmount] = Field(min_length=1, max_length=1000)


def pinned_file(root, filename, digest, bound):
    path = (root / filename).resolve(strict=True)
    if not path.is_relative_to(root) or path.stat().st_size > bound:
        raise ValueError('Report evidence path or size invalid')
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError('Report evidence hash mismatch')
    return data


def report_packet(manifest, directory):
    """Validate selected values against reviewed source rows/columns, never infer.

    Page image hashes authenticate the exact pages reviewed by the operator;
    this function does not claim to perform OCR or audit the issuer accounts.
    """
    e = ReviewedReport.model_validate(manifest)
    root = Path(directory).resolve(strict=True)
    _https(e.document_url); _https(e.discovery_url)
    binary = pinned_file(root, e.document_file, e.document_sha256, 40_000_000)
    if not binary.startswith(b'%PDF-'):
        raise ValueError('Original report is not a PDF')
    observed = datetime.fromisoformat(e.observed_at)
    if observed.tzinfo is None or observed.utcoffset() is None:
        raise ValueError('Report receipt time needs timezone')
    if e.profile != {'CT': 'non_financial', 'NH': 'bank', 'CK': 'financial_other', 'BH': 'financial_other'}[e.company_type]:
        raise ValueError('Report model contradicts issuer type')
    pages = {}
    for page in e.pages:
        if page.number in pages or hashlib.sha256(page.text.encode()).hexdigest() != page.text_sha256:
            raise ValueError('Ambiguous or changed source page')
        data = pinned_file(root, page.image_file, page.image_sha256, 8_000_000)
        if not data.startswith(b'\x89PNG\r\n\x1a\n'):
            raise ValueError('Reviewed page image is not PNG')
        pages[page.number] = page

    def quote(q):
        if q.page not in pages or q.text not in pages[q.page].text:
            raise ValueError('Missing original page quote')
        return q.text

    for q in (e.scope_quote, e.identity_quote, e.calendar_quote, e.currency_quote):
        quote(q)
    scope = quote(e.scope_quote).casefold()
    if not any(s in scope for s in (('hợp nhất', 'consolidated') if e.scope == 'consolidated' else ('riêng', 'separate', 'standalone'))):
        raise ValueError('Scope lacks explicit original evidence')
    if e.issuer not in quote(e.identity_quote):
        raise ValueError('Report issuer identity mismatch')
    if not re.search(r'(1 tháng 1|01/01|1 January).*?(31 tháng 12|31/12|31 December)', quote(e.calendar_quote), re.I | re.S):
        raise ValueError('Only explicit calendar-year statements supported')
    if not re.search(r'VND|đồng Việt Nam|Vietnamese [Dd]ong', quote(e.currency_quote)):
        raise ValueError('Currency lacks original evidence')
    grouped = {}
    for a in e.amounts:
        # FX is a reviewed reconciliation line, not a new headline metric.
        kind = 'cash' if a.field == 'cash_fx_effect' else FIELD_KIND.get(a.field)
        if kind is None or a.field in NON_FINANCIAL_ONLY and e.profile != 'non_financial' or a.field in BANK_ONLY and e.profile != 'bank':
            raise ValueError('Unsupported field or issuer model')
        start, end = date.fromisoformat(a.period_start) if a.period_start else None, date.fromisoformat(a.period_end)
        if end != date(a.year, 12, 31) or (kind != 'balance' and start != date(a.year, 1, 1)) or (start and start != date(a.year, 1, 1)):
            raise ValueError('Unsupported or contradictory fiscal boundaries')
        source_row, header, unit_quote = quote(a.source_row), quote(a.column_header), quote(a.unit_quote)
        if a.label not in source_row or str(a.year) not in header:
            raise ValueError('Original field/column missing')
        if a.code_kind == 'printed_statement_code' and not re.search(r'(?<!\w)' + re.escape(a.code) + r'(?!\w)', source_row):
            raise ValueError('Original statement code missing')
        if a.code_kind == 'reviewed_row_locator' and not a.code.startswith('row:'):
            raise ValueError('Reviewer locator must be distinguished from printed code')
        # The selected token is a complete original cell, not a code/note substring.
        if (len(a.column_periods) != len(a.column_values) or len(set(a.column_periods)) != len(a.column_periods)
                or str(a.year) not in a.column_periods
                or a.column_values[a.column_periods.index(str(a.year))] != a.raw_token
                or source_row.split()[-len(a.column_values):] != a.column_values):
            raise ValueError('Original monetary cell missing')
        token = a.raw_token
        if not re.fullmatch(r'(?:-?\d{1,3}(?:[.,]\d{3})*|-?\d+|\(\d{1,3}(?:[.,]\d{3})*\))', token):
            raise ValueError('Ambiguous monetary token')
        raw = Decimal(token.strip('()').replace('.', '').replace(',', '')) * (-1 if token.startswith('(') else 1)
        eps = a.field == 'eps_reported'
        if eps != (a.unit == 'VND/share'):
            raise ValueError('Per-share amounts must not use statement money scale')
        scales = {'VND': 1, 'thousand VND': 1000, 'million VND': 1000000, 'billion VND': 1000000000, 'VND/share': 1}
        wording = {'VND': r'\bVND\b|Đồng', 'thousand VND': r'nghìn|ngàn|thousand', 'million VND': r'[Tt]riệu|million', 'billion VND': r'tỷ|billion', 'VND/share': r'đồng/cổ phiếu|VND/share'}
        if not re.search(wording[a.unit], unit_quote) or a.unit == 'VND' and re.search(r'triệu|nghìn|ngàn|tỷ|million|thousand|billion', unit_quote, re.I):
            raise ValueError('Source amount scale mismatch')
        value = raw * scales[a.unit]
        if abs(value) > 2**53 - 1:
            raise ValueError('Amount exceeds safe financial precision')
        record = dict(field=a.field, code=a.code, code_kind=a.code_kind, label=a.label,
            original_value=token, normalized_value=int(value), original_unit=a.unit,
            multiplier=scales[a.unit], page=a.source_row.page, period_start=a.period_start,
            period_end=a.period_end, source_row=a.source_row.model_dump(), column_header=a.column_header.model_dump())
        bucket = grouped.setdefault((kind, str(a.year)), {})
        if a.field in bucket:
            raise ValueError('Duplicate report field/period')
        bucket[a.field] = record
    # Contradictory balance identities withhold that statement's qualification,
    # not unrelated income/cash statements. Raw evidence stays inspectable.
    reports, checks = {}, []
    for kind in MAP:
        observations = []
        for (selected_kind, period), records in sorted(grouped.items()):
            if selected_kind != kind:
                continue
            complete = all(f in records for f in ('total_assets', 'total_liabilities', 'equity'))
            residual = (records['total_assets']['normalized_value'] - records['total_liabilities']['normalized_value'] - records['equity']['normalized_value']) if complete else None
            valid = residual is None or abs(residual) <= max(1, abs(records['total_assets']['normalized_value']) * 1e-6)
            balance_identity='PASS' if complete and valid else 'FAIL' if complete else 'NOT_TESTED'
            checks.append(dict(statement=kind, period=period, balance_identity='PASS' if complete and valid else 'FAIL' if not valid else 'NOT_TESTED', residual=residual))
            cash_fields = ('cash_operating','cash_investing','cash_financing','cash_net_change')
            cash_residual = (sum(records[f]['normalized_value'] for f in cash_fields[:3]) - records['cash_net_change']['normalized_value']) if all(f in records for f in cash_fields) else None
            endpoint_residual = (records['cash_beginning']['normalized_value'] + records['cash_net_change']['normalized_value']
                + records.get('cash_fx_effect',{}).get('normalized_value',0) - records['cash_ending']['normalized_value']) if all(f in records for f in ('cash_beginning','cash_net_change','cash_ending')) else None
            tolerance = max(r['multiplier'] for r in records.values()) * 2
            cash_identity = 'NOT_TESTED' if cash_residual is None else 'PASS' if abs(cash_residual) <= tolerance else 'FAIL'
            endpoint_identity = 'PASS' if endpoint_residual is not None and abs(endpoint_residual) <= tolerance else 'NOT_RECONCILED_WITHOUT_FX_EVIDENCE'
            if kind == 'cash':
                checks[-1].update(cash_flow_identity=cash_identity, cash_flow_residual=cash_residual,
                    cash_endpoint_identity=endpoint_identity, cash_endpoint_residual=endpoint_residual)
                valid = valid and cash_identity != 'FAIL'
            context = FinancialSourceContext(fiscal_year=int(period),
                period_start=f'{period}-01-01' if kind != 'balance' else None, period_end=f'{period}-12-31',
                original_currency='VND', original_unit=next(iter(records.values()))['original_unit'],
                amount_multiplier=next(iter(records.values()))['multiplier'], unit_evidence='original_filing',
                record_sha256=content_hash(records),
                original_metadata=dict(extraction_verified=True, binary_sha256=e.document_sha256,
                    page_image_verified=True, document_url=e.document_url, discovery_url=e.discovery_url,
                    review_reference=e.review_reference, fields=records, evidence_kind='reviewed_original_pdf',
                    metadata_origin='reported', publication_date=None, publication_time_qualified=False,
                    balance_identity=balance_identity,
                    cash_flow_identity=cash_identity, cash_endpoint_identity=endpoint_identity,
                    page_evidence={str(n): dict(text_sha256=p.text_sha256, image_sha256=p.image_sha256, method=p.method) for n,p in pages.items()}))
            observations.append(StatementObservation(ticker=e.ticker, source=e.source, statement=kind,
                period=period, frequency='annual', basis='point_in_time' if kind == 'balance' else 'annual',
                consolidation=e.scope, source_context=context,
                fields={f: records[f]['normalized_value'] if f in records else None for f in MAP[kind]},
                field_codes={f:r['code'] for f,r in records.items()},
                items=[FinancialLine(code=r['code'], name_en=f.replace('_',' '), name_vi=r['label'],
                    value=r['normalized_value'], raw_value=float(Decimal(r['original_value'].strip('()').replace('.','').replace(',','')) * (-1 if r['original_value'].startswith('(') else 1)),
                    unit='VND/share' if f == 'eps_reported' else 'VND') for f,r in records.items()],
                diagnostics=[] if valid else ['balance_identity_failed']))
        reports[kind] = StatementReceipt(statement=kind, status='healthy' if observations else 'unavailable',
            observations=observations, observed_at=observed, source_url=e.document_url,
            content_sha256=content_hash([o.model_dump(mode='json') for o in observations]) if observations else None)
    return FinancialPacket(ticker=e.ticker, source=e.source, source_version='reviewed-report-v2',
        company_type=e.company_type, profile=e.profile, metadata_sha256=content_hash(e.model_dump()),
        reports=reports), dict(checks=checks, selected_reported_fields=len(e.amounts), public_activated=False)
