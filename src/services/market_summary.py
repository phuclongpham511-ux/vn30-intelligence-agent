"""Pure SecuritiesSummary evidence normalization; no acquisition or qualification grant.

Date-only totals are NOT tick activity. This contract deliberately cannot satisfy
the existing UI's verified same-observation shares/VND contract by itself.
"""
from datetime import datetime
from decimal import Decimal, InvalidOperation
import re


def normalize_summary_pair(row: dict, *, retrieved_at: str, expected_symbol: str) -> dict:
    """Retain one coherent original record, including missing vs zero and unknown units."""
    if not isinstance(expected_symbol, str) or not isinstance(row, dict) or row.get('symbol') != expected_symbol or not re.fullmatch(r'[A-Z0-9]{1,20}', expected_symbol):
        raise ValueError('Summary instrument mismatch')
    day = row.get('tradingDate')
    if not isinstance(day, str) or not re.fullmatch(r'\d{4}/\d{2}/\d{2}', day):
        raise ValueError('Invalid summary trading date')
    trading_date = datetime.strptime(day, '%Y/%m/%d').date().isoformat()
    retrieval = datetime.fromisoformat(retrieved_at)
    if retrieval.tzinfo is None or retrieval.utcoffset() is None:
        raise ValueError('Retrieval time requires an offset')

    def metric(field):
        raw = row.get(field)
        if isinstance(raw, str) and len(raw) > 128:
            raise ValueError('Summary amount exceeds normalization bound')
        value, status = None, 'missing'
        if raw is not None and raw != '':
            status = 'invalid'
            if not isinstance(raw, bool) and isinstance(raw, (str, int, float)):
                try:
                    parsed = Decimal(str(raw))
                    if parsed.is_finite() and parsed >= 0:
                        value, status = str(parsed), 'present'
                except InvalidOperation:
                    pass
        return dict(field=field, raw_value=raw, normalized_decimal=value,
                    value_status=status, unit=None, unit_verification='unverified',
                    qualification='unqualified')

    volume, value = metric('totalMatch'), metric('totalMatchValue')
    present = sum(m['value_status'] == 'present' for m in (volume, value))
    return dict(symbol=expected_symbol, source='SSI:FastConnect:v3:SecuritiesSummary',
                trading_date=trading_date, raw_trading_date=day, retrieved_at=retrieved_at,
                source_observed_at=None, temporal_granularity='trading_date',
                scope='matched', scope_verification='partial', cumulative_interval='trading_day',
                includes_negotiated_trades=None, regular_board_odd_lot_scope='unverified',
                freshness='unverified', finality='unverified', display_rights='unverified',
                completeness='complete_pair' if present == 2 else 'partial_pair' if present else 'missing_pair',
                qualification='partial' if present else 'unavailable',
                volume=volume, value=value,
                negotiated_fields={k: row.get(k) for k in ('totalDeal', 'totalDealValue')},
                live_display_eligible=False)
