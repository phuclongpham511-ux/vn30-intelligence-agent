"""Offline, reviewed filing boundary feeding the existing financial engine.

No discovery, network, database, source fallback or public permission grant.
The hash authenticates the saved extraction, not an unavailable PDF binary.
"""
from datetime import date, datetime
from decimal import Decimal
import hashlib
import re
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
from src.providers.vnstock.financial_statements import MAP, content_hash
from src.schemas.financials import (FinancialPacket, FinancialLine,
    FinancialSourceContext, StatementObservation, StatementReceipt)


FIELDS = {'revenue': 'income', 'net_profit': 'income', 'total_assets': 'balance',
          'total_liabilities': 'balance', 'equity': 'balance'}
LABELS = {'revenue': 'Net revenue', 'net_profit': 'Profit after tax',
          'total_assets': 'Total assets', 'total_liabilities': 'Total liabilities', 'equity': 'Total equity'}


class StrictEvidence(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, allow_inf_nan=False)


class FilingField(StrictEvidence):
    field: Literal['revenue', 'net_profit', 'total_assets', 'total_liabilities', 'equity']
    code: str = Field(min_length=1, max_length=32)
    label: str = Field(min_length=1, max_length=200)
    page: int = Field(ge=1, le=10000)  # One-based PDF page, not printed page.
    printed_page: str = Field(min_length=1, max_length=32)
    source_row: str = Field(min_length=1, max_length=2000)
    raw_values: list[str] = Field(min_length=1, max_length=4)


class FilingEvidence(StrictEvidence):
    contract: Literal['reviewed-filing-v1']
    ticker: str = Field(pattern=r'^[A-Z0-9]{1,20}$')
    issuer: str = Field(min_length=1, max_length=200)
    exchange: Literal['HOSE', 'HNX', 'UPCOM']
    profile: Literal['non_financial', 'bank', 'financial_other']
    source: str = Field(pattern=r'^issuer:[A-Za-z0-9_.:-]+$')
    document_url: str
    discovery_url: str
    document_title: str = Field(min_length=1, max_length=300)
    extraction_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    # Deliberately separate from extraction_sha256. No binary receipt in V5.
    document_sha256: None = None
    observed_at: str
    published_date: str | None = None
    publication_quote: str | None = None
    consolidation: Literal['consolidated', 'standalone']
    basis_quote: str
    identity_quote: str
    period_quote: str
    year_columns: list[int] = Field(min_length=1, max_length=4)
    year_header: str
    period_starts: list[str]
    period_ends: list[str]
    currency: Literal['VND']
    original_unit: Literal['VND', 'thousand VND', 'million VND', 'billion VND']
    unit_quote: str
    thousands_separator: Literal['.', ',', 'none']
    extraction_method: Literal['reviewed_page_text']
    confidence: Literal['text_and_arithmetic_verified_not_visual']
    review_reference: str = Field(min_length=1, max_length=300)
    fields: list[FilingField] = Field(min_length=1, max_length=20)


def _https(url):
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('Invalid filing evidence URL')


def _amount(raw, separator):
    pattern = r'-?\d+' if separator == 'none' else rf'-?\d{{1,3}}(?:\{separator}\d{{3}})*'
    if len(raw) > 64 or not re.fullmatch(pattern, raw):
        raise ValueError('Invalid original monetary token')
    return Decimal(raw.replace(separator, '') if separator != 'none' else raw)


def filing_packet(evidence, extraction):
    """Normalize only reviewed fields, with hash/row/column/identity checks.

    The reviewed manifest is operator evidence, not untrusted provider metadata.
    It carries no public rights. Arithmetic failure rejects rather than repairs.
    """
    e = FilingEvidence.model_validate(evidence)
    if hashlib.sha256(extraction.encode('utf-8')).hexdigest() != e.extraction_sha256:
        raise ValueError('Filing extraction hash mismatch')
    _https(e.document_url)
    _https(e.discovery_url)
    if e.document_url not in extraction or e.discovery_url not in extraction:
        raise ValueError('Filing references missing from extraction')
    observed = datetime.fromisoformat(e.observed_at)
    if observed.tzinfo is None:
        raise ValueError('Acquisition time must include timezone')
    if len(set(e.year_columns)) != len(e.year_columns) or any(not 1900 <= y <= 2200 for y in e.year_columns):
        raise ValueError('Invalid filing year columns')
    if len(e.period_starts) != len(e.year_columns) or len(e.period_ends) != len(e.year_columns):
        raise ValueError('Incomplete fiscal boundaries')
    for year, start, end in zip(e.year_columns, e.period_starts, e.period_ends):
        a, b = date.fromisoformat(start), date.fromisoformat(end)
        if a != date(year, 1, 1) or b != date(year, 12, 31):
            raise ValueError('Invalid annual financial period')
    if not re.search(r'1 (?:tháng 1|January).*31 (?:tháng 12|December)', e.period_quote, re.I):
        raise ValueError('Calendar-year boundaries lack original evidence')
    for quote in (e.identity_quote, e.basis_quote, e.period_quote, e.year_header, e.unit_quote):
        if not quote or quote not in extraction:
            raise ValueError('Missing filing qualification evidence')
    if not re.search(r'\b' + re.escape(e.ticker) + r'\b', e.identity_quote) or e.issuer not in extraction or e.exchange not in extraction:
        raise ValueError('Wrong filing issuer')
    basis_word = 'HỢP NHẤT' if e.consolidation == 'consolidated' else 'RIÊNG'
    # Explicit reviewed terminology; no basis inference from numbers or ticker.
    if basis_word not in e.basis_quote and (e.consolidation.upper() not in e.basis_quote.upper()):
        raise ValueError('Reporting basis contradicts evidence')
    if 'VND' not in e.unit_quote or any(str(y) not in e.year_header for y in e.year_columns):
        raise ValueError('Missing currency/year header')
    if [e.year_header.find(str(y)) for y in e.year_columns] != sorted(e.year_header.find(str(y)) for y in e.year_columns):
        raise ValueError('Year column order mismatch')
    if e.published_date is not None:
        published = date.fromisoformat(e.published_date)
        if not e.publication_quote or e.publication_quote not in extraction or published.strftime('%d/%m/%Y') not in e.publication_quote or published > observed.date():
            raise ValueError('Unverified publication date')
    multiplier = {'VND': 1, 'thousand VND': 1000, 'million VND': 1000000, 'billion VND': 1000000000}[e.original_unit]
    # Scaling must be explicit in the captured statement header, not merely VND.
    if multiplier != 1 and e.original_unit not in e.unit_quote:
        raise ValueError('Amount scale lacks original evidence')
    if multiplier == 1 and re.search(r'thousand|million|billion|nghìn|ngàn|triệu|tỷ', e.unit_quote, re.I):
        raise ValueError('Amount scale contradicts original header')
    rows, duplicates, codes = {}, [], {}
    for item in e.fields:
        if e.profile != 'non_financial' and item.field == 'revenue':
            raise ValueError('Generic revenue is not a qualified banking definition')
        clean_row = re.sub(r'L\d+@P\d+: ?', '', item.source_row).replace('\n', ' ')
        if item.source_row not in extraction or item.label not in clean_row or not clean_row.startswith(item.code + ' '):
            raise ValueError('Missing original line evidence')
        # Captured page markers prevent a correct value being attributed elsewhere.
        if f'@P{item.page-1}:' not in item.source_row:
            # Manifests use the full captured row with its L..@P.. prefix below.
            raise ValueError('Missing original page reference')
        if len(item.raw_values) != len(e.year_columns):
            raise ValueError('Incomplete original columns')
        # Match complete trailing column tokens, never a substring or note/code.
        if clean_row.split()[-len(e.year_columns):] != item.raw_values:
            raise ValueError('Original amount column mismatch')
        kind = FIELDS[item.field]
        code_key = (kind, item.code)
        if code_key in codes and codes[code_key] != item.field:
            raise ValueError('Conflicting canonical mapping for original code')
        codes[code_key] = item.field
        for index, (year, raw) in enumerate(zip(e.year_columns, item.raw_values)):
            number = _amount(raw, e.thousands_separator) * multiplier
            if abs(number) > 2**53-1 or item.field in ('revenue', 'total_assets', 'total_liabilities') and number < 0:
                raise ValueError('Invalid normalized amount')
            key = (kind, str(year), item.field)
            record = dict(field=item.field, code=item.code, original_label=item.label,
                original_value=raw, normalized_value=int(number), original_unit=e.original_unit,
                multiplier=multiplier, page=item.page, printed_page=item.printed_page,
                source_row=item.source_row, period_start=e.period_starts[index], period_end=e.period_ends[index])
            if key in rows:
                if rows[key] != record:
                    raise ValueError('Conflicting duplicate filing field')
                duplicates.append(list(key))
            rows[key] = record
    identities = []
    for year in e.year_columns:
        values = {field: r['normalized_value'] for (kind, period, field), r in rows.items() if period == str(year)}
        complete = all(k in values for k in ('total_assets', 'total_liabilities', 'equity'))
        residual = values['total_assets'] - values['total_liabilities'] - values['equity'] if complete else None
        if residual is not None and residual != 0:
            raise ValueError('Contradictory balance identity; no silent repair')
        identities.append(dict(period=str(year), status='PASS' if complete else 'UNVERIFIED', residual=residual))
    reports = {}
    for kind in MAP:
        observations = []
        for year in sorted(e.year_columns):
            selected = {f: r for (k, p, f), r in rows.items() if k == kind and p == str(year)}
            if not selected:
                continue
            fields = {field: selected[field]['normalized_value'] if field in selected else None for field in MAP[kind]}
            context = FinancialSourceContext(fiscal_year=year,
                period_start=next(iter(selected.values()))['period_start'], period_end=next(iter(selected.values()))['period_end'],
                original_currency=e.currency, original_unit=e.original_unit, amount_multiplier=multiplier,
                unit_evidence='original_filing', record_sha256=content_hash(selected),
                original_metadata=dict(extraction_verified=True, evidence_kind='saved_web_pdf_text_not_binary',
                    document_url=e.document_url, document_title=e.document_title, document_sha256=None,
                    extraction_sha256=e.extraction_sha256, discovery_url=e.discovery_url,
                    publication_date=e.published_date, review_reference=e.review_reference,
                    observation_time_definition='saved_receipt_assembly_not_issuer_event_or_http_time',
                    extraction_method=e.extraction_method, confidence=e.confidence, fields=selected,
                    version_policy='preserved_vintage_no_automatic_restatement_selection'))
            observations.append(StatementObservation(ticker=e.ticker, source=e.source, statement=kind,
                period=str(year), frequency='annual', basis='point_in_time' if kind == 'balance' else 'annual',
                consolidation=e.consolidation, fields=fields, field_codes={f:r['code'] for f,r in selected.items()},
                source_dates={'publicDate': e.published_date}, source_context=context,
                items=[FinancialLine(code=r['code'], name_en=LABELS[f], name_vi=r['original_label'],
                    value=r['normalized_value'], raw_value=float(_amount(r['original_value'], e.thousands_separator)),
                    unit='VND') for f,r in selected.items()]))
        reports[kind] = StatementReceipt(statement=kind, status='healthy' if observations else 'unavailable',
            observations=observations, observed_at=observed, source_url=e.document_url,
            content_sha256=content_hash([o.model_dump(mode='json') for o in observations]) if observations else None)
    packet = FinancialPacket(ticker=e.ticker, source=e.source, source_version='reviewed-filing-v1',
        profile=e.profile, company_type='CT' if e.profile == 'non_financial' else 'NH' if e.profile == 'bank' else 'UNKNOWN',
        metadata_sha256=content_hash(e.model_dump()), reports=reports, is_fixture=False)
    return packet, dict(balance_identities=identities, duplicates=duplicates,
        normalized_fields=len(rows), public_activation=False, binary_document_verified=False)


def reconcile_filing(left, right):
    """Compare, never merge/overwrite, source periods and vintages."""
    if left.ticker != right.ticker:
        raise ValueError('Cannot reconcile different issuers')
    result = []
    for kind, receipt in left.reports.items():
        counterparts = {o.period:o for o in right.reports.get(kind, StatementReceipt(statement=kind,
            status='unavailable', observed_at=receipt.observed_at, source_url='')).observations}
        for observation in receipt.observations:
            other = counterparts.get(observation.period)
            for field, value in observation.fields.items():
                if value is None:
                    continue
                alternative = other.fields.get(field) if other else None
                basis = 'UNKNOWN' if other is None or other.consolidation is None else 'MATCH' if observation.consolidation == other.consolidation else 'CONFLICT'
                same = alternative is not None and Decimal(str(value)) == Decimal(str(alternative))
                same_receipt = receipt.content_sha256 == right.reports[kind].content_sha256 if kind in right.reports else False
                official_context, comparison_context = observation.source_context, other.source_context if other else None
                original_unit = comparison_context.original_unit if comparison_context else None
                boundaries = (comparison_context.period_start, comparison_context.period_end) if comparison_context else (None, None)
                period_status = 'MISSING' if other is None else 'LABEL_MATCH_BOUNDARIES_UNVERIFIED'
                if all(boundaries) and official_context:
                    period_status = 'MATCH' if boundaries == (official_context.period_start, official_context.period_end) else 'CONFLICT'
                result.append(dict(period=observation.period, field=field, official_value=value,
                    comparison_value=alternative, numeric='UNAVAILABLE' if alternative is None else 'MATCH' if same else 'CONFLICT',
                    basis=basis, comparison_source=right.source, official_source=left.source,
                    unit_comparison='VND_NORMALIZED' if other and other.currency == observation.currency else 'UNKNOWN',
                    official_original_unit=official_context.original_unit if official_context else None,
                    comparison_original_unit=original_unit,
                    original_unit_comparison='UNKNOWN' if original_unit is None or official_context is None else 'MATCH' if original_unit == official_context.original_unit else 'DIFFERENT',
                    period_comparison=period_status,
                    vintage='RECEIPT_CONTRADICTION' if same_receipt and alternative is not None and not same else 'DUPLICATE_RECEIPT' if same_receipt else 'DISTINCT_RECEIPTS',
                    restatement='UNPROVEN_POSSIBLE_VERSION_DIFFERENCE' if alternative is not None and not same else 'NOT_INFERRED'))
    return result
