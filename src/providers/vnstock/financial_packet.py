"""One bounded, cached financial packet through the existing vnstock VCI transport."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from importlib.metadata import version
from src.providers.vnstock.financial_statements import SECTIONS, content_hash, normalize_statement
from src.schemas.financials import FinancialPacket, StatementReceipt


def metadata_rows(payload):
    if not isinstance(payload, dict):
        raise ValueError('Invalid VCI financial metadata')
    result = []
    for section in SECTIONS.values():
        items = payload.get(section, [])
        if not isinstance(items, list) or len(items) > 400:
            raise ValueError('Invalid metadata collection')
        for item in items:
            if not isinstance(item, dict):
                raise ValueError('Invalid metadata item')
            result.append(dict(report_name=section, field_name=item.get('field'),
                name=item.get('titleVi'), en_name=item.get('titleEn'), parent=item.get('parent')))
    return result


def issuer_profile(company_type, metadata):
    labels = {item['field_name']: str(item.get('en_name') or '').casefold().strip()
              for item in metadata if item['report_name'] == SECTIONS['income']}
    if company_type == 'NH' and labels.get('isb38') == 'total operating income':
        return 'bank'
    if company_type in ('CK', 'BH'):
        return 'financial_other'
    if company_type == 'CT' and labels.get('isa3') == 'net sales' and labels.get('isa5') == 'gross profit':
        return 'non_financial'
    return 'unknown'


def packet_from_payloads(ticker, source, company_type, metadata, reports, *, source_version,
                         observed_at=None, urls=None, is_fixture=False):
    profile = issuer_profile(company_type, metadata)
    receipts = {}
    urls = urls or {}
    for kind in SECTIONS:
        try:
            receipts[kind] = normalize_statement(ticker, source, kind, reports[kind], metadata, profile,
                observed_at=(observed_at or {}).get(kind), source_url=urls.get(kind, ''))
        except (ValueError, KeyError, TypeError) as exc:
            receipts[kind] = StatementReceipt(statement=kind, status='error',
                observed_at=(observed_at or {}).get(kind) or datetime.now(timezone.utc),
                source_url=urls.get(kind, ''), error_type=type(exc).__name__)
    return FinancialPacket(ticker=ticker, source=source, source_version=source_version,
        company_type=company_type if company_type in ('CT', 'NH', 'CK', 'BH') else 'UNKNOWN',
        profile=profile, metadata_sha256=content_hash(metadata), reports=receipts, is_fixture=is_fixture)


def fetch_packet(symbol, sdk):
    # The existing SDK creates public VCI headers/session and classifies the issuer.
    # Avoid its financial DataFrame helpers: head(4) loses history; fillna(0) loses missingness.
    finance = sdk().Finance(symbol=symbol, source='VCI').provider
    from vnstock.core.utils.client import send_request
    base = f'{finance.base_url}/v1/company/{symbol}/financial-statement'

    def read(url, params=None):
        result = send_request(url=url, headers=finance.headers, method='GET', params=params,
            payload=None, show_log=False, timeout=15, request_mode='direct')
        if not isinstance(result, dict) or result.get('data') is None:
            raise ValueError('Missing VCI financial response')
        return result['data'], datetime.now(timezone.utc)

    metadata = metadata_rows(read(base + '/metrics')[0])
    def report(kind):
        try:
            return kind, read(base, {'section': SECTIONS[kind]})
        except (Exception, SystemExit):
            # No immediate retry; failures remain visible until the next cache interval.
            return kind, (None, datetime.now(timezone.utc))
    with ThreadPoolExecutor(max_workers=3) as pool:
        captured = dict(pool.map(report, SECTIONS))
    return packet_from_payloads(symbol, 'vnstock:VCI', finance.com_type_code, metadata,
        {kind: item[0] for kind, item in captured.items()}, source_version=version('vnstock'),
        observed_at={kind: item[1] for kind, item in captured.items()},
        urls={kind: base + '?section=' + section for kind, section in SECTIONS.items()})
