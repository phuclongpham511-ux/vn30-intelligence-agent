"""Internal conventions over saved evidence, never a provider probe."""
import copy
import json
from pathlib import Path
import unittest

from src.services.market_summary import normalize_provisional_market

ROOT = Path(__file__).parent / 'fixtures'
MASTER = json.loads((ROOT / 'ssi-master-acb-20261016.json').read_text(encoding='utf-8'))
SUMMARY = json.loads((ROOT / 'ssi-summary-acb-20261016.json').read_text(encoding='utf-8'))
NOW = '2026-10-17T14:00:00+00:00'


def packet(master=None, summary=None, security=None, **kwargs):
    return normalize_provisional_market(
        copy.deepcopy(master if master is not None else MASTER['record']),
        copy.deepcopy(summary if summary is not None else SUMMARY['record']),
        security=copy.deepcopy(security if security is not None else MASTER['security']['record']),
        master_receipt=kwargs.pop('master_receipt', {'fetched_at': MASTER['received_at'], 'document_sha256': MASTER['evidence_sha256']}),
        summary_receipt=kwargs.pop('summary_receipt', {'fetched_at': SUMMARY['received_at'], 'document_sha256': SUMMARY['evidence_sha256']}),
        identity_receipt=kwargs.pop('identity_receipt', {'fetched_at': MASTER['security']['received_at'], 'document_sha256': MASTER['evidence_sha256']}),
        now=kwargs.pop('now', NOW), **kwargs)


class ProvisionalMarketTests(unittest.TestCase):
    def test_offline_generator_matches_frontend_saved_packet(self):
        from scripts.prepare_ssi_provisional import saved_packet
        target = Path(__file__).parents[1] / 'frontend/app/internal/ssi-market/saved-acb.json'
        stored = json.loads(target.read_text(encoding='utf-8'))
        generated = saved_packet(ROOT / 'ssi-master-acb-20261016.json', ROOT / 'ssi-summary-acb-20261016.json', stored['freshness']['evaluated_at'])
        self.assertEqual(generated, stored)

    def test_explicit_conflicting_currency_or_units_are_not_overridden_by_conventions(self):
        for kind, patch in [('master', {'currency': 'USD'}), ('master', {'priceUnit': 'thousand VND'}),
                            ('summary', {'volume_unit': 'lots'}), ('summary', {'valueUnit': 'USD'})]:
            with self.subTest(kind=kind, patch=patch), self.assertRaises(ValueError):
                packet(**{kind: {**{'master': MASTER['record'], 'summary': SUMMARY['record']}[kind], **patch}})

    def test_missing_or_conflicting_exchange_never_becomes_an_inferred_venue(self):
        for kind in ('master', 'security'):
            row = copy.deepcopy(MASTER['record'] if kind == 'master' else MASTER['security']['record'])
            row.pop('board')
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                packet(**{kind: row})
        security = {**MASTER['security']['record'], 'exchange': 'HNX'}
        with self.assertRaises(ValueError):
            packet(security=security)

    def test_receipt_times_and_hashes_fail_closed(self):
        for name in ('master_receipt', 'summary_receipt', 'identity_receipt'):
            for patch in [{'document_sha256': 'bad'}, {'fetched_at': '2026-10-17T20:26:48'},
                          {'fetched_at': '2026-10-18T00:00:00Z'},
                          {'source_timestamp': '2026-10-18T00:00:00Z'}, {'source_timestamp': 'bad'}]:
                receipt = {'fetched_at': MASTER['received_at'], 'document_sha256': MASTER['evidence_sha256'], **patch}
                with self.subTest(name=name, patch=patch), self.assertRaises(ValueError):
                    packet(**{name: receipt})
        with self.assertRaises(ValueError):
            packet(summary_receipt={'fetched_at': '2026-10-15T00:00:00Z', 'document_sha256': SUMMARY['evidence_sha256']})

    def test_plausibility_is_exact_even_under_low_decimal_context_precision(self):
        from decimal import localcontext
        master = {**MASTER['record'], 'floor': '20600', 'ceiling': '20600'}
        summary = {**SUMMARY['record'], 'totalMatch': '3', 'totalMatchValue': '61800'}
        with localcontext() as context:
            context.prec = 2
            self.assertEqual(packet(master=master, summary=summary)['matched']['value']['value'], 61800)
            with self.assertRaises(ValueError):
                packet(master=master, summary={**summary, 'totalMatchValue': '61801'})

    def test_unrepresentable_transport_values_are_rejected_without_rescaling(self):
        for value in ['9007199254740992', '20600.000000000000001', '1e-4000', '20_600', ' 20600 ', '0x5078']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                packet(master={**MASTER['record'], 'floor': value})

    def test_saved_acb_conventions_are_not_certification(self):
        p = packet()
        self.assertEqual(p['key'], {'symbol': 'ACB', 'exchange': 'HOSE', 'trading_date': '2026-10-16'})
        self.assertEqual(p['bands']['ceiling']['value'], 22000)
        self.assertEqual(p['bands']['floor']['value'], 19200)
        self.assertEqual(p['bands']['reference']['value'], 20600)
        self.assertEqual(p['matched']['volume']['value'], 5160300)
        self.assertEqual(p['matched']['value']['value'], 106488260000)
        self.assertEqual(p['qualification'], 'PROVISIONAL_INTERNAL')
        self.assertFalse(p['public_display_eligible'])
        self.assertEqual(p['matched']['trade_inclusion'], 'provisional_unverified')
        self.assertEqual(p['freshness']['status'], 'stale')
        self.assertIsNone(p['matched']['source_timestamp'])
        self.assertEqual(p['matched']['fetched_at'], SUMMARY['received_at'])
        for key in ('ceiling', 'floor', 'reference'):
            self.assertEqual(p['bands'][key]['unit'], 'VND/share')
            self.assertEqual(p['bands'][key]['multiplier'], 1)
        self.assertEqual(p['matched']['volume']['unit'], 'shares')
        self.assertEqual(p['matched']['value']['unit'], 'VND')

    def test_inputs_and_receipts_remain_inspectable_and_immutable(self):
        m, s, identity = copy.deepcopy(MASTER['record']), copy.deepcopy(SUMMARY['record']), copy.deepcopy(MASTER['security']['record'])
        before = copy.deepcopy((m, s, identity))
        p = packet(m, s, identity)
        self.assertEqual((m, s, identity), before)
        self.assertEqual(p['receipts']['summary']['raw_record'], s)
        self.assertEqual(p['receipts']['master']['raw_record'], m)
        self.assertEqual(len(p['receipts']['master']['record_sha256']), 64)
        self.assertEqual(p['bands']['ceiling']['raw_value'], m['ceiling'])

    def test_no_summing_successive_snapshots_and_no_value_substitution(self):
        first, second = packet(), packet()
        self.assertEqual(first['matched']['volume'], second['matched']['volume'])
        self.assertEqual(second['matched']['aggregation'], 'snapshot_do_not_sum')
        self.assertNotEqual(second['matched']['value']['value'], 20600 * 5160300)
        with self.assertRaises(ValueError):
            packet(summary={**SUMMARY['record'], 'totalMatchValue': None})

    def test_zero_pair_and_equal_price_bands_are_valid(self):
        p = packet(master={**MASTER['record'], 'floor': '20600', 'ceiling': '20600'},
                   summary={**SUMMARY['record'], 'totalMatch': '0', 'totalMatchValue': '0'})
        self.assertEqual(p['matched']['value']['value'], 0)

    def test_observation_time_is_separate_and_missing_time_never_becomes_fresh(self):
        same_day = '2026-10-16T07:00:00+00:00'
        # Move receipt times to this same-day scenario explicitly; these are simulated timestamps.
        from unittest.mock import patch
        with patch.dict(MASTER, received_at=same_day), patch.dict(SUMMARY, received_at=same_day), patch.dict(MASTER['security'], received_at=same_day):
            p = packet(now=same_day)
            self.assertEqual(p['freshness']['status'], 'unverified')
            self.assertIsNone(p['matched']['source_timestamp'])
            receipt = {'fetched_at': same_day, 'source_timestamp': same_day, 'document_sha256': SUMMARY['evidence_sha256']}
            self.assertEqual(packet(now=same_day, summary_receipt=receipt)['freshness']['status'], 'fresh')
            later = '2026-10-16T07:03:00+00:00'
            self.assertEqual(packet(now=later, summary_receipt=receipt)['freshness']['status'], 'stale')


def rejection_case(kind, patch):
    kwargs = {kind: {**{'master': MASTER['record'], 'summary': SUMMARY['record'], 'security': MASTER['security']['record']}[kind], **patch}}
    with unittest.TestCase().assertRaises(ValueError):
        packet(**kwargs)


CASES = [
    ('master', {'symbol': 'OTHER'}), ('master', {'symbol': ' acb'}),
    ('master', {'board': 'HNX'}), ('master', {'exchange': 'HNX'}),
    ('security', {'board': 'DERIVATIVES'}), ('security', {'stockType': 'ETF Product'}),
    ('summary', {'tradingDate': '2026/10/15'}), ('master', {'tradingDate': '2026/02/30'}),
    ('master', {'ceiling': 'NaN'}), ('master', {'floor': '-1'}),
    ('master', {'refPrice': '0'}), ('master', {'floor': '23000'}),
    ('master', {'refPrice': '23000'}), ('master', {'ceiling': True}),
    ('summary', {'totalMatch': '-1'}), ('summary', {'totalMatch': '1.5'}),
    ('summary', {'totalMatchValue': 'Infinity'}), ('summary', {'totalMatchValue': None}),
    ('summary', {'totalMatch': '0', 'totalMatchValue': '1'}),
    ('summary', {'totalMatch': '1', 'totalMatchValue': '0'}),
    ('summary', {'totalMatchValue': '999999999999'}),
    ('summary', {'totalMatchValue': '1'}),
    ('summary', {'totalMatch': '9007199254740992'}),
    ('summary', {'totalMatch': '1e1000000'}),
    ('summary', {'board': 'HNX'}), ('summary', {'symbol': 'OTHER'}),
]
for i, (kind, patch) in enumerate(CASES):
    setattr(ProvisionalMarketTests, f'test_rejection_{i:02}', lambda self, kind=kind, patch=patch: rejection_case(kind, patch))

if __name__ == '__main__':
    unittest.main()
