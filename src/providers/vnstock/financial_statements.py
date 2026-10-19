"""Audited VCI REST statement boundary. Raw padding is never financial truth."""
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from src.schemas.financials import FinancialLine, FinancialSourceContext, StatementObservation, StatementReceipt

SECTIONS = {'income': 'INCOME_STATEMENT', 'balance': 'BALANCE_SHEET', 'cash': 'CASH_FLOW'}
MAP = {
    'income': {
        'revenue': ('isa3', r'^net sales$'),
        'gross_profit': ('isa5', r'^gross profit$'),
        'net_profit': ('isa20', r'after tax'),
        'profit_parent': ('isa22', r'attributable to parent'),
        'eps_reported': ('isa23', r'eps basic.*vnd'),
        'operating_income': ('isb38', r'^total operating income$'),
        'net_interest_income': ('isb27', r'^net interest income$'),
    },
    'balance': {
        'total_assets': ('bsa53', r'^total assets$'),
        'total_liabilities': ('bsa54', r'^(total )?liabilities$'),
        'equity': ('bsa78', r"^owner'?s equity$"),
        'current_assets': ('bsa1', r'^current assets$'),
        'current_liabilities': ('bsa55', r'^current liabilities$'),
        'inventory': ('bsa15', r'^inventories,? net$'),
        'cash_equivalents': ('bsa2', r'^cash and cash equivalents$'),
        'short_debt': ('bsa56', r'^short.term borrowings$'),
        'long_debt': ('bsa71', r'^long.term borrowings$'),
        'customer_loans': ('bsb104', r'^loans and advances to customers$'),
        'customer_deposits': ('bsb113', r'^deposits from customers$'),
    },
    'cash': {
        'cash_operating': ('cfa18', r'^net cash (inflows/\(outflows\)|flows|from).*operating activities$'),
        'cash_investing': ('cfa26', r'^net cash (inflows/\(outflows\)|flows|from).*investing activities$'),
        'cash_financing': ('cfa34', r'^net cash (inflows/\(outflows\)|flows|from).*financing activities$'),
        'capex_signed': ('cfa19', r'^purchases of fixed assets and other long term assets$'),
        'cash_net_change': ('cfa35', r'^net increase.*cash and cash equivalents$'),
        'cash_beginning': ('cfa36', r'^cash and cash equivalents at (the )?beginning of period$'),
        'cash_ending': ('cfa38', r'^cash and cash equivalents at (the )?end of (the )?period$'),
    },
}
NON_FINANCIAL_ONLY = {'revenue', 'gross_profit', 'current_assets', 'current_liabilities', 'inventory', 'cash_equivalents', 'short_debt', 'long_debt'}
BANK_ONLY = {'operating_income', 'net_interest_income', 'customer_loans', 'customer_deposits'}


def content_hash(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def finite_value(value):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError('Non-numeric financial source value')
    return float(value) if math.isfinite(value) else None


def normalize_statement(ticker, source, kind, payload, metadata, profile, *, observed_at=None, source_url=''):
    observed_at = observed_at or datetime.now(timezone.utc)
    if not isinstance(payload, dict) or not {'years', 'quarters'} <= payload.keys():
        raise ValueError('Unexpected VCI statement envelope')
    catalog = {}
    alternatives = {}
    conflicts = set()
    for item in metadata:
        if item.get('report_name') != SECTIONS[kind]:
            continue
        code = item.get('field_name')
        if code is None:  # Source grouping headers have no numerical field.
            continue
        if not isinstance(code, str) or not code:
            raise ValueError('Invalid financial metadata code')
        label = {key: item.get(key) if isinstance(item.get(key), str) else None for key in ('name', 'en_name', 'parent')}
        if code in catalog and label not in alternatives[code]:
            conflicts.add(code)
        catalog.setdefault(code, item)
        alternatives.setdefault(code, []).append(label)
    if not catalog:
        raise ValueError('Statement metadata is unavailable')
    result = []
    seen = set()
    for bucket in ('years', 'quarters'):
        if not isinstance(payload[bucket], list):
            raise ValueError('Invalid statement collection')
        if len(payload[bucket]) > 160:
            raise ValueError('Financial collection exceeds bounded history')
        for raw in payload[bucket]:
            if not isinstance(raw, dict) or raw.get('ticker') != ticker:
                raise ValueError('Wrong financial statement owner')
            if raw.get('currency', 'VND') != 'VND' or raw.get('unit', 'VND') != 'VND':
                raise ValueError('Unsupported financial currency or amount unit')
            year, quarter = raw.get('yearReport'), raw.get('lengthReport')
            if type(year) is not int or not 1900 <= year <= 2200 or type(quarter) is not int:
                raise ValueError('Invalid source reporting period')
            if bucket == 'years' and quarter != 5 or bucket == 'quarters' and not 1 <= quarter <= 4:
                raise ValueError('Period does not match the source collection')
            period = str(year) if bucket == 'years' else f'{year}-Q{quarter}'
            if period in seen:
                raise ValueError('Duplicate financial reporting period')
            seen.add(period)
            fields, codes, diagnostics = {}, {}, ['conflicted_metadata:' + code for code in sorted(conflicts)]
            for field, (code, expected) in MAP[kind].items():
                fields[field] = None
                definition = catalog.get(code)
                if definition is None or code not in raw:
                    continue
                if code in conflicts:
                    continue
                name = str(definition.get('en_name') or '').casefold().strip()
                if not re.search(expected, name):
                    diagnostics.append('conflicted_metadata:' + code)
                    continue
                if field in NON_FINANCIAL_ONLY and profile != 'non_financial' or field in BANK_ONLY and profile != 'bank':
                    continue
                fields[field] = finite_value(raw[code])
                codes[field] = code
            items = []
            for code, definition in catalog.items():
                if code not in raw:
                    continue
                value = finite_value(raw[code])
                conflicted = 'conflicted_metadata:' + code in diagnostics
                parent = definition.get('parent')
                items.append(FinancialLine(code=code, name_en=str(definition.get('en_name') or code),
                    name_vi=str(definition.get('name') or code), parent=parent if isinstance(parent, str) else None,
                    unit='VND/share' if code in ('isa23', 'isa24') else 'VND',
                    value=None if conflicted else value, raw_value=value,
                    semantic_status='conflicted' if conflicted else 'reported', source_labels=alternatives[code]))
            # Quarterly flow convention was audited against annual totals and cash roll-forward.
            basis = 'point_in_time' if kind == 'balance' else 'annual' if bucket == 'years' else raw.get('flowBasis', 'standalone')
            if basis not in ('point_in_time', 'annual', 'standalone', 'ytd', 'unknown'):
                raise ValueError('Unrecognized source flow basis')
            source_dates = {key: raw.get(key) if isinstance(raw.get(key), str) else None for key in ('publicDate', 'updateDate', 'createDate')}
            consolidation = raw.get('consolidation')
            if consolidation not in (None, 'consolidated', 'standalone'):
                raise ValueError('Unrecognized consolidation basis')
            # Missing currency/unit are recorded as missing source metadata even though
            # this adapter retains its previously audited VND x1 transport contract.
            # Raw audit/restatement flags are evidence only: their provider semantics
            # and fiscal boundaries have not been qualified. Do not infer either.
            context = FinancialSourceContext(fiscal_year=year,
                fiscal_quarter=quarter if bucket == 'quarters' else None,
                original_currency=raw.get('currency'), original_unit=raw.get('unit'),
                record_sha256=content_hash(raw), original_metadata={key: raw[key] for key in
                    ('consolidation', 'flowBasis', 'periodStart', 'periodEnd', 'isAudited',
                     'auditStatus', 'isRestated', 'restatementStatus', 'publicDate', 'updateDate', 'createDate')
                    if key in raw})
            result.append(StatementObservation(ticker=ticker, source=source, statement=kind, period=period,
                frequency='annual' if bucket == 'years' else 'quarterly', basis=basis,
                consolidation=consolidation, source_dates=source_dates, fields=fields, field_codes=codes,
                items=items, diagnostics=diagnostics, source_context=context))
    return StatementReceipt(statement=kind, status='healthy' if result else 'unavailable',
        observations=sorted(result, key=lambda row: row.period), observed_at=observed_at,
        content_sha256=content_hash(payload), source_url=source_url)
