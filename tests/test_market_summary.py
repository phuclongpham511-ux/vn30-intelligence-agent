"""Offline tests. Saved actual provider response establishes structure, not live eligibility."""
import copy
import json
from pathlib import Path

import unittest

from src.services.market_summary import normalize_summary_pair

EVIDENCE = json.loads((Path(__file__).parent/'fixtures/ssi-summary-acb-20261016.json').read_text(encoding='utf-8'))


def normalize(row=None, **kwargs):
    return normalize_summary_pair(copy.deepcopy(EVIDENCE['record']) if row is None else row,
                                  retrieved_at=kwargs.get('retrieved_at', EVIDENCE['received_at']),
                                  expected_symbol=kwargs.get('expected_symbol', 'ACB'))


def _check_saved_actual_pair_retains_source_date_raw_values_and_unqualified_units():
    original = copy.deepcopy(EVIDENCE['record'])
    result = normalize(original)
    assert original == EVIDENCE['record']
    assert result['source'] == 'SSI:FastConnect:v3:SecuritiesSummary'
    assert result['trading_date'] == '2026-10-16'
    assert result['volume']['field'] == 'totalMatch'
    assert result['volume']['raw_value'] == '5160300'
    assert result['value']['field'] == 'totalMatchValue'
    assert result['value']['normalized_decimal'] == '106488260000'
    for key in ('volume', 'value'):
        assert result[key]['unit'] is None
        assert result[key]['unit_verification'] == 'unverified'
        assert result[key]['qualification'] == 'unqualified'
    assert result['source_observed_at'] is None  # Retrieval never becomes source time.
    assert result['freshness'] == result['finality'] == result['display_rights'] == 'unverified'
    assert result['completeness'] == 'complete_pair'
    assert result['scope'] == 'matched' and result['scope_verification'] == 'partial'
    assert result['negotiated_fields'] == {'totalDeal': None, 'totalDealValue': None}
    assert result['includes_negotiated_trades'] is None
    assert not result['live_display_eligible']


def metric_case(raw, normalized, status):
    row = {**EVIDENCE['record'], 'totalMatch': raw}
    result = normalize(row)
    assert result['volume']['raw_value'] == raw
    assert result['volume']['normalized_decimal'] == normalized
    assert result['volume']['value_status'] == status
    assert not result['live_display_eligible']


def _check_partial_pair_never_synthesizes_traded_value_from_close_or_other_totals():
    row = {**EVIDENCE['record'], 'totalMatchValue': None, 'totalForeignBuyValue': '999', 'totalDealValue': '500'}
    result = normalize(row)
    assert result['completeness'] == 'partial_pair'
    assert result['value']['normalized_decimal'] is None
    assert result['value']['raw_value'] is None
    assert result['negotiated_fields']['totalDealValue'] == '500'


def mismatch_case(patch):
    with unittest.TestCase().assertRaises(ValueError):
        normalize({**EVIDENCE['record'], **patch})


def _check_retrieval_requires_timezone_and_cannot_certify_current_freshness():
    with unittest.TestCase().assertRaises(ValueError):
        normalize(retrieved_at='2026-10-17T20:26:48')
    result = normalize(retrieved_at='2026-10-19T09:30:00+07:00')
    assert result['trading_date'] == '2026-10-16'
    assert result['source_observed_at'] is None and result['freshness'] == 'unverified'
    assert not result['live_display_eligible']


class SummaryEvidenceTests(unittest.TestCase):
    test_saved_actual_pair = staticmethod(_check_saved_actual_pair_retains_source_date_raw_values_and_unqualified_units)
    test_partial_pair = staticmethod(_check_partial_pair_never_synthesizes_traded_value_from_close_or_other_totals)
    test_retrieval_time = staticmethod(_check_retrieval_requires_timezone_and_cannot_certify_current_freshness)

    def test_amount_bound(self):
        with self.assertRaises(ValueError):
            normalize({**EVIDENCE['record'], 'totalMatch': '1'*129})

for index, case in enumerate([(None,None,'missing'),('',None,'missing'),('0','0','present'),(0,'0','present'),('90071992547409930001','90071992547409930001','present'),('1.25','1.25','present'),('-1',None,'invalid'),('NaN',None,'invalid'),('Infinity',None,'invalid'),(True,None,'invalid'),({},None,'invalid'),('bad',None,'invalid')]):
    setattr(SummaryEvidenceTests, f'test_metric_{index:02}', lambda self, case=case: metric_case(*case))
for index, patch in enumerate([{'symbol':'OTHER'},{'tradingDate':'2026/02/30'},{'tradingDate':'2026-10-16'},{'tradingDate':None}]):
    setattr(SummaryEvidenceTests, f'test_identity_date_{index:02}', lambda self, patch=patch: mismatch_case(patch))
