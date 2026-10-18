"""Pure SecuritiesSummary evidence normalization; no acquisition or qualification grant.

Date-only totals are NOT tick activity. This contract deliberately cannot satisfy
the existing UI's verified same-observation shares/VND contract by itself.
"""
from datetime import datetime
import copy
import hashlib
import json
from decimal import Decimal, InvalidOperation
from fractions import Fraction
import re
from zoneinfo import ZoneInfo


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


PROVISIONAL_CONTRACT = 'ssi-provisional-market-v1'
VN = ZoneInfo('Asia/Ho_Chi_Minh')
MAX_SAFE = Decimal(9007199254740991)


def _receipt_time(value):
    if not isinstance(value, str):
        raise ValueError('Missing receipt time')
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        raise ValueError('Invalid receipt time') from None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError('Receipt time requires an offset')
    return parsed


def _convention_metric(raw, field, unit, *, positive=False, integer=False):
    if isinstance(raw, bool) or not isinstance(raw, (str, int, float)) or len(str(raw)) > 128:
        raise ValueError('Missing or invalid provisional amount')
    if isinstance(raw, str) and not re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?', raw):
        raise ValueError('Invalid provisional numeric representation')
    try:
        value = Decimal(str(raw))
    except InvalidOperation:
        raise ValueError('Invalid provisional amount') from None
    if not value.is_finite() or value < 0 or positive and value <= 0 or value > MAX_SAFE:
        raise ValueError('Provisional amount outside numeric contract')
    if integer and value != value.to_integral_value():
        raise ValueError('Fractional shares are not supported')
    if Decimal(str(float(value))) != value:
        raise ValueError('Lossy provisional numeric transport')
    return dict(field=field, raw_value=raw, value=int(value) if value == value.to_integral_value() else float(value),
                normalized_decimal=str(value), unit=unit, multiplier=1,
                qualification='PROVISIONAL_INTERNAL', unit_authority='owner_engineering_convention')


def normalize_provisional_market(master: dict, summary: dict, *, security: dict,
                                 master_receipt: dict, summary_receipt: dict,
                                 identity_receipt: dict, now: str) -> dict:
    """Pure, opt-in consumer contract. No SSI certification, rights grant or I/O.

    Inputs may come from existing caches or saved receipts. Success never changes
    the old unqualified normalizer or produces a qualified live-price/activity DTO.
    A pair is a replacement snapshot; no previous snapshot or accumulation exists.
    """
    if not all(isinstance(row, dict) for row in (master, summary, security)):
        raise ValueError('Invalid market record')
    if not all(isinstance(receipt, dict) for receipt in (master_receipt, summary_receipt, identity_receipt)):
        raise ValueError('Invalid source receipt')
    symbol = security.get('symbol')
    exchange = security.get('board', security.get('exchange'))
    if not isinstance(symbol, str) or not re.fullmatch(r'[A-Z0-9]{1,20}', symbol) or exchange not in ('HOSE', 'HNX', 'UPCOM') or security.get('stockType') != 'Stock':
        raise ValueError('Ordinary equity identity is not established')
    for row in (master, summary, security):
        if row.get('symbol') != symbol or any(row[key] != exchange for key in ('board', 'exchange') if key in row):
            raise ValueError('Conflicting instrument or exchange')
    if not any(key in master for key in ('board', 'exchange')):
        raise ValueError('MasterData exchange is required')
    for row in (master, summary):
        if 'currency' in row and row['currency'] != 'VND':
            raise ValueError('Conflicting explicit currency')
    for row, keys, allowed in ((master, ('price_unit', 'priceUnit'), ('VND', 'VND/share')),
                               (summary, ('volume_unit', 'volumeUnit'), ('shares',)),
                               (summary, ('value_unit', 'valueUnit'), ('VND',))):
        if any(row[key] not in allowed for key in keys if key in row):
            raise ValueError('Conflicting explicit source unit')
    observed_now = _receipt_time(now)
    evidence = normalize_summary_pair(summary, expected_symbol=symbol, retrieved_at=summary_receipt.get('fetched_at'))
    trading_date = evidence['trading_date']
    if master.get('tradingDate') != summary.get('tradingDate') or trading_date > observed_now.astimezone(VN).date().isoformat():
        raise ValueError('Inconsistent or future trading date')

    receipts = {}
    for name, row, receipt, source in (
        ('master', master, master_receipt, 'SSI:FastConnect:v3:MasterData'),
        ('summary', summary, summary_receipt, 'SSI:FastConnect:v3:SecuritiesSummary'),
        ('identity', security, identity_receipt, 'SSI:FastConnect:v3:SecuritiesInfo'),
    ):
        if not isinstance(receipt, dict) or not re.fullmatch(r'[a-f0-9]{64}', str(receipt.get('document_sha256', ''))):
            raise ValueError('Missing source document receipt')
        fetched = _receipt_time(receipt.get('fetched_at'))
        source_time = receipt.get('source_timestamp')
        if fetched > observed_now or name != 'identity' and fetched.astimezone(VN).date().isoformat() < trading_date:
            raise ValueError('Inconsistent fetch chronology')
        if source_time is not None:
            stamp = _receipt_time(source_time)
            if stamp > fetched or name != 'identity' and stamp.astimezone(VN).date().isoformat() != trading_date:
                raise ValueError('Inconsistent source timestamp')
        raw = json.dumps(row, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()
        if len(raw) > 65536:
            raise ValueError('Market record exceeds evidence bound')
        receipts[name] = dict(source=source, fetched_at=receipt['fetched_at'], source_timestamp=source_time,
            document_sha256=receipt['document_sha256'], record_sha256=hashlib.sha256(raw).hexdigest(),
            raw_record=copy.deepcopy(row))

    bands = {key: _convention_metric(master.get(field), field, 'VND/share', positive=True)
             for key, field in (('floor', 'floor'), ('reference', 'refPrice'), ('ceiling', 'ceiling'))}
    floor, reference, ceiling = (Decimal(bands[key]['normalized_decimal']) for key in ('floor', 'reference', 'ceiling'))
    if not floor <= reference <= ceiling:
        raise ValueError('Invalid price-band ordering')
    volume = _convention_metric(evidence['volume']['raw_value'], 'totalMatch', 'shares', integer=True)
    value = _convention_metric(evidence['value']['raw_value'], 'totalMatchValue', 'VND')
    quantity, consideration = Decimal(volume['normalized_decimal']), Decimal(value['normalized_decimal'])
    # Exact rational bounds, independent of the process Decimal precision. This
    # is not a substitute GT calculation. A contradiction is
    # rejected, not clamped, rescaled, reconciled or silently repaired.
    if (quantity == 0) != (consideration == 0) or not Fraction(floor) * Fraction(quantity) <= Fraction(consideration) <= Fraction(ceiling) * Fraction(quantity):
        raise ValueError('Matched value/volume is implausible within the supplied bands')
    source_time = receipts['summary']['source_timestamp']
    freshness = 'stale' if trading_date != observed_now.astimezone(VN).date().isoformat() else (
        'unverified' if source_time is None else 'fresh' if (observed_now - _receipt_time(source_time)).total_seconds() <= 120 else 'stale')
    return dict(contract=PROVISIONAL_CONTRACT, qualification='PROVISIONAL_INTERNAL',
        convention_version='woofi-owner-market-conventions-v1', public_display_eligible=False,
        certification='NOT_SSI_CERTIFIED', display_rights='NOT_QUALIFIED_FOR_PUBLIC',
        key=dict(symbol=symbol, exchange=exchange, trading_date=trading_date),
        bands={**bands, 'source_timestamp': receipts['master']['source_timestamp'], 'fetched_at': receipts['master']['fetched_at'],
               'effectiveness': 'trading_day_provisional'},
        matched=dict(volume=volume, value=value, cumulative=True, aggregation='snapshot_do_not_sum',
                     trade_inclusion='provisional_unverified', scope='instrument_trading_day_not_all_market',
                     source_timestamp=source_time, fetched_at=receipts['summary']['fetched_at']),
        freshness=dict(status=freshness, evaluated_at=now, max_source_age_seconds=120,
                       reason='previous_trading_date' if trading_date != observed_now.astimezone(VN).date().isoformat() else
                       'source_time_unavailable' if source_time is None else 'source_time_age'),
        validation=dict(identity='PASS', date_alignment='PASS', bands='PASS', totals='PASS', plausibility='PASS'),
        receipts=receipts)
