"""Pure, fixture-only VCI events mapping. No SDK calls, writes or verification grants."""
from datetime import date
import json
import math
import re

from src.corporate_actions.models import ActionTerms, CorporateActionNotice
from src.corporate_actions.repository import content_hash
from src.schemas.stocks import SymbolRequest


MAPPING_VERSION = 'vnstock-vci-events-offline-v1'
MAX_EXACT_NUMBER = 2**53 - 1
# Fixture vocabulary, not a claim that every upstream event uses these labels.
TYPE_LABELS = {
    'cash dividend': ('DIV', 'cash_dividend'), 'cổ tức bằng tiền': ('DIV', 'cash_dividend'),
    'stock dividend': ('DIV', 'stock_dividend'), 'cổ tức bằng cổ phiếu': ('DIV', 'stock_dividend'),
    'bonus shares': ('ISS', 'bonus_shares'), 'cổ phiếu thưởng': ('ISS', 'bonus_shares'),
    'rights offering': ('ISS', 'rights_offering'), 'quyền mua cổ phiếu': ('ISS', 'rights_offering'),
}


def _action_type(raw):
    labels = [raw[key] for key in ('action_type_en', 'action_type_vi') if raw.get(key) is not None]
    definitions = [TYPE_LABELS.get(value.strip().casefold()) if isinstance(value, str) else None for value in labels]
    if not definitions or any(item is None for item in definitions):
        raise ValueError('unsupported_event_type')
    if len(set(definitions)) != 1:
        raise ValueError('ambiguous_event_type')
    code, action_type = definitions[0]
    if raw.get('event_code') != code:
        raise ValueError('event_code_type_conflict')
    return action_type


def _number(value):
    if value is None:
        return None
    if type(value) not in (int, float) or not 0 <= value <= MAX_EXACT_NUMBER or not math.isfinite(value):
        raise ValueError('invalid_numeric_term')
    return value


def _date(value):
    if value is None or value == '':
        return None
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('ambiguous_date_precision')
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError('invalid_calendar_date') from None


def normalize_event(row, *, requested_symbol, semantics_reference, amount_unit=None, ratio_basis=None):
    """Map one synthetic SDK-shaped record; declarations are not upstream proof.

    Raw fields and explicit semantic declarations survive in existing evidence_text.
    Knowledge time belongs to CorporateActionRepository.ingest(received_at=...),
    never to the source revision. Every result remains unverified and a fixture.
    """
    if not isinstance(row, dict) or any(not isinstance(key, str) for key in row):
        raise ValueError('invalid_event_record')
    try:
        serialized = json.dumps(row, sort_keys=True, ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError):
        raise ValueError('non_json_event_record') from None
    if len(serialized) > 4000:
        raise ValueError('oversized_event_record')
    raw = json.loads(serialized)
    symbol = SymbolRequest(ticker=requested_symbol).symbol
    if raw.get('symbol') is not None and raw['symbol'] != symbol:
        raise ValueError('event_owner_mismatch')
    vendor_id = raw.get('id')
    if (type(vendor_id) not in (str, int) or not str(vendor_id).strip()
            or str(vendor_id) != str(vendor_id).strip() or len(str(vendor_id)) > 128
            or any(ord(c) < 32 for c in str(vendor_id))
            or type(vendor_id) is int and not 0 <= vendor_id <= MAX_EXACT_NUMBER):
        raise ValueError('missing_or_invalid_event_id')
    if not isinstance(semantics_reference, str) or not semantics_reference.strip() or len(semantics_reference) > 200:
        raise ValueError('missing_semantics_reference')
    action_type = _action_type(raw)
    if amount_unit not in (None, 'VND/share'):
        raise ValueError('unsupported_amount_unit')
    if ratio_basis not in (None, 'fraction_new_per_old', 'percent_new_per_old'):
        raise ValueError('unsupported_ratio_basis')
    cash = action_type == 'cash_dividend'
    amount = _number(raw.get('value_per_share')) if cash else None
    if amount is not None and amount_unit != 'VND/share':
        raise ValueError('amount_unit_required')
    ratio = _number(raw.get('exercise_ratio')) if not cash else None
    if ratio is not None:
        if ratio_basis is None:
            raise ValueError('ratio_basis_required')
        ratio = ratio / 100 if ratio_basis == 'percent_new_per_old' else ratio
        if ratio <= 0:
            raise ValueError('nonpositive_share_ratio')
    ex_date, record = (_date(raw.get(key)) for key in ('exright_date', 'record_date'))
    payment = _date(raw.get('payout_date')) if cash else None
    if ex_date and record and ex_date > record or record and payment and payment < record:
        raise ValueError('contradictory_event_dates')
    mapped_fields = {'id', 'symbol', 'event_code', 'action_type_en', 'action_type_vi',
        'event_title_vi', 'event_title_en', 'exright_date', 'record_date', 'public_date'}
    mapped_fields.update(('value_per_share', 'payout_date') if cash else ('exercise_ratio',))
    evidence = dict(mapping_contract=MAPPING_VERSION, sdk_contract_reference='vnstock==4.0.2 Company.events (static)',
        requested_symbol=symbol, semantics_reference=semantics_reference,
        amount_unit=amount_unit, ratio_basis=ratio_basis, raw_record=raw, raw_record_sha256=content_hash(raw),
        unmapped_fields=sorted(set(raw) - mapped_fields))
    evidence_text = json.dumps(evidence, sort_keys=True, ensure_ascii=False, allow_nan=False)
    if len(evidence_text) > 6000:
        raise ValueError('oversized_event_evidence')
    return CorporateActionNotice(symbol=symbol, action_type=action_type,
        source='vnstock:VCI:events', source_id=f'{symbol}:{vendor_id}', component_id='event',
        source_revision=content_hash(evidence), source_title=raw.get('event_title_vi') or raw.get('event_title_en'),
        evidence_text=evidence_text, effective_date=ex_date, record_date=record, payment_date=payment,
        announced_on=_date(raw.get('public_date')),
        terms=ActionTerms(cash_vnd_per_share=amount, new_shares_per_old=ratio),
        verified=False, is_fixture=True, withdrawn=False,
        verification_note=f'{MAPPING_VERSION}: offline synthetic fixture; no source verification or public-use rights granted.')
