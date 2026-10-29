"""One bounded, cached financial packet through the existing vnstock VCI transport."""
from datetime import datetime, timezone
from importlib.metadata import version
import math
import re
import time
import pandas as pd
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


GUEST_SDK_PERIODS = 4
MAX_SDK_PERIODS = 8


def _sdk_period_limit():
    try:
        # Resolve only after loading the caller's SDK. Importing this adapter or
        # reading saved captures must never initialize authentication/network IO.
        from vnai.beam.patching import get_max_periods
        limit = get_max_periods()
    except (Exception, SystemExit):
        return GUEST_SDK_PERIODS
    return limit if type(limit) is int and limit in (GUEST_SDK_PERIODS, MAX_SDK_PERIODS) else GUEST_SDK_PERIODS


def _metadata_from_sdk(frame):
    required = {'report_name', 'field_name', 'name', 'en_name', 'parent'}
    if not isinstance(frame, pd.DataFrame) or frame.columns.duplicated().any() or not required <= set(frame.columns):
        raise ValueError('Unexpected VCI SDK metadata schema')
    output = {section: [] for section in SECTIONS.values()}
    def clean(value):
        return None if value is None or pd.isna(value) else value
    for item in frame.to_dict('records'):
        section = item.get('report_name')
        if section not in output:
            continue
        output[section].append(dict(field=clean(item.get('field_name')), titleVi=clean(item.get('name')),
            titleEn=clean(item.get('en_name')), parent=clean(item.get('parent'))))
    return output


def _frame_to_payload(symbol, kind, frequency, frame, metadata, *, max_periods=GUEST_SDK_PERIODS):
    if not isinstance(frame, pd.DataFrame) or frame.columns.duplicated().any():
        raise ValueError('Unexpected VCI SDK statement schema')
    if not {'item_id', 'item', 'item_en'} <= set(frame.columns):
        raise ValueError('VCI SDK statement labels are unavailable')
    period_pattern = r'\d{4}-Q[1-4]' if frequency == 'quarterly' else r'\d{4}'
    periods = [str(column) for column in frame.columns if re.fullmatch(period_pattern, str(column))]
    if len(periods) > max_periods:
        raise ValueError('VCI SDK returned more periods than its bounded public method')
    metadata_codes = {item.get('field') for item in metadata.get(SECTIONS[kind], []) if item.get('field')}
    if frame['item_id'].isna().any() or frame['item_id'].duplicated().any():
        raise ValueError('Ambiguous VCI SDK statement field identities')
    codes = [str(value) for value in frame['item_id'].tolist()]
    if not set(codes) <= metadata_codes:
        raise ValueError('VCI SDK statement fields do not match its source metadata')
    bucket = 'quarters' if frequency == 'quarterly' else 'years'
    rows = []
    for period in periods:
        year = int(period[:4])
        quarter = int(period[-1]) if frequency == 'quarterly' else 5
        row = {'ticker': symbol, 'yearReport': year, 'lengthReport': quarter}
        for item in frame.to_dict('records'):
            value = item[period]
            if value is None or pd.isna(value):
                row[str(item['item_id'])] = None
                continue
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                raise ValueError('VCI SDK returned a non-finite or non-numeric statement value')
            row[str(item['item_id'])] = float(value)
        rows.append(row)
    return bucket, rows


def fetch_packet(symbol, sdk, *, request_pause_seconds=0):
    """Acquire a bounded VCI packet through vnstock's public Finance API.

    Respect the SDK's Guest/Community decision, with an eight-period ceiling.
    Unknown entitlement keeps the Guest bound. Do not call the underlying REST
    endpoint or request uncapped source history. Missing SDK metadata stays
    unknown in the normalized packet.
    """
    symbol = str(symbol).strip().upper()
    if not re.fullmatch(r'[A-Z0-9]{1,20}', symbol):
        raise ValueError('Invalid ticker')
    finance = sdk().Finance(symbol=symbol, source='VCI', period='quarter', get_all=False, show_log=False)
    max_periods = _sdk_period_limit()
    provider = finance.provider
    if request_pause_seconds:
        time.sleep(request_pause_seconds)
    metadata_frame = provider._get_ratio_dict(format='dataframe', show_log=False)
    raw_metadata = _metadata_from_sdk(metadata_frame)
    metadata = metadata_rows(raw_metadata)
    reports, observed_at, frequency_errors = {}, {}, {}
    base = f'{provider.base_url}/v1/company/{symbol}/financial-statement'
    urls = {}
    method_names = {'income': 'income_statement', 'balance': 'balance_sheet', 'cash': 'cash_flow'}
    for kind, method_name in method_names.items():
        combined = {'years': [], 'quarters': []}
        stamps = []
        errors = {}
        for frequency, period in (('quarterly', 'quarter'), ('annual', 'year')):
            bucket = 'quarters' if frequency == 'quarterly' else 'years'
            try:
                frame = getattr(finance, method_name)(period=period, lang='en', dropna=False, show_log=False)
                stamps.append(datetime.now(timezone.utc))
                bucket, rows = _frame_to_payload(symbol, kind, frequency, frame, raw_metadata,
                                                 max_periods=max_periods)
                combined[bucket] = rows
            except (Exception, SystemExit) as exc:
                combined[bucket] = []
                errors[frequency] = type(exc).__name__
            if request_pause_seconds:
                time.sleep(request_pause_seconds)
        reports[kind] = combined
        observed_at[kind] = max(stamps) if stamps else datetime.now(timezone.utc)
        if not any(combined.values()) and errors:
            reports[kind] = None
        if errors:
            frequency_errors[kind] = errors
        urls[kind] = base
    packet = packet_from_payloads(symbol, 'vnstock:VCI', provider.com_type_code, metadata, reports,
        source_version=version('vnstock'), observed_at=observed_at,
        urls=urls)
    for kind, errors in frequency_errors.items():
        for observation in packet.reports[kind].observations:
            observation.diagnostics.extend(f'sdk_{frequency}_read_error:{error}' for frequency, error in errors.items())
    return packet
