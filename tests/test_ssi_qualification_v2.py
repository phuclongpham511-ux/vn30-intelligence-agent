"""Saved ACB regression plus explicitly simulated edge cases; no live requests."""
import copy
import json
from pathlib import Path
import unittest
from decimal import localcontext
from src.services.market_summary import normalize_provisional_market, compare_provisional_snapshots, audit_icb_metadata

FIXTURES = Path(__file__).parent / 'fixtures'
MASTER = json.loads((FIXTURES / 'ssi-master-acb-20261016.json').read_text(encoding='utf8'))
SUMMARY = json.loads((FIXTURES / 'ssi-summary-acb-20261016.json').read_text(encoding='utf8'))
NOW = '2026-10-17T14:00:00+00:00'
RECEIPT = dict(fetched_at=MASTER['received_at'], document_sha256=MASTER['evidence_sha256'])


def packet(*, fetched=None, amount=None, volume=None, source_time=None, symbol=None, exchange=None, day=None):
    master, summary, security = copy.deepcopy(MASTER['record']), copy.deepcopy(SUMMARY['record']), copy.deepcopy(MASTER['security']['record'])
    if symbol:
        for row in (master, summary, security): row['symbol'] = symbol
    if exchange:
        master['board'] = security['board'] = exchange
    if day: master['tradingDate'] = summary['tradingDate'] = day
    if amount is not None: summary['totalMatchValue'] = amount
    if volume is not None: summary['totalMatch'] = volume
    receipt = dict(fetched_at=fetched or SUMMARY['received_at'], document_sha256=SUMMARY['evidence_sha256'], source_timestamp=source_time)
    return normalize_provisional_market(master, summary, security=security, master_receipt=RECEIPT,
        summary_receipt=receipt, identity_receipt=RECEIPT, now=NOW)


class SnapshotComparisonTests(unittest.TestCase):
    def test_saved_acb_repeated_snapshot_replaces_not_sums_and_stays_historical(self):
        before = packet(); current = packet(fetched='2026-10-17T13:28:00+00:00')
        original = copy.deepcopy((before, current))
        result = compare_provisional_snapshots(before, current, now=NOW)
        self.assertEqual(result['latest']['matched']['volume']['value'], 5160300)
        self.assertEqual(result['latest']['matched']['value']['value'], 106488260000)
        self.assertEqual(result['changes']['volume']['status'], 'unchanged')
        self.assertEqual(result['source_freshness']['status'], 'stale')
        self.assertFalse(result['public_display_eligible']); self.assertFalse(result['live_two_round_acceptance'])
        self.assertEqual((before, current), original)

    def test_simulated_correction_decreases_are_retained_not_repaired(self):
        result = compare_provisional_snapshots(packet(volume='3', amount='61800'),
            packet(volume='2', amount='41200', fetched='2026-10-17T13:28:00+00:00'), now=NOW)
        self.assertEqual(result['changes']['volume'], dict(numerator=-1, denominator=1, status='decreased'))
        self.assertEqual(result['latest']['matched']['volume']['raw_value'], '2')
        self.assertTrue(result['review_required']); self.assertFalse(result['public_display_eligible'])

    def test_exact_increase_and_average_ignore_decimal_context(self):
        with localcontext() as ctx:
            ctx.prec = 2
            result = compare_provisional_snapshots(packet(volume='2', amount='41200'),
                packet(volume='3', amount='61800', fetched='2026-10-17T13:28:00+00:00'), now=NOW)
        self.assertEqual(result['changes']['value']['numerator'], 20600)
        self.assertEqual(result['implied_average_vnd_per_share']['numerator'], 20600)
        self.assertEqual(result['implied_average_vnd_per_share']['denominator'], 1)

    def test_zero_volume_never_divides_by_zero(self):
        result = compare_provisional_snapshots(packet(volume='0', amount='0'),
            packet(volume='0', amount='0', fetched='2026-10-17T13:28:00+00:00'), now=NOW)
        self.assertIsNone(result['implied_average_vnd_per_share'])

    def test_date_venue_symbol_and_receipt_order_mismatches_fail_closed(self):
        for current in (packet(symbol='DEMOA', fetched='2026-10-17T13:28:00+00:00'),
                        packet(exchange='HNX', fetched='2026-10-17T13:28:00+00:00'),
                        packet(day='2026/10/15', fetched='2026-10-17T13:28:00+00:00'),
                        packet(), packet(fetched='2026-10-17T13:26:48+00:00')):
            with self.subTest(current=current['key']), self.assertRaises(ValueError):
                compare_provisional_snapshots(packet(), current, now=NOW)

    def test_tampered_values_or_public_flags_cannot_be_promoted(self):
        for field, value in (('public_display_eligible', True), ('qualification', 'VERIFIED')):
            altered = packet(); altered[field] = value
            with self.assertRaises(ValueError): compare_provisional_snapshots(altered, packet(fetched='2026-10-17T13:28:00+00:00'), now=NOW)
        altered = packet(); altered['matched']['volume']['value'] = 1
        with self.assertRaises(ValueError): compare_provisional_snapshots(altered, packet(fetched='2026-10-17T13:28:00+00:00'), now=NOW)

    def test_source_time_is_not_fetch_time_and_regression_requires_review(self):
        result = compare_provisional_snapshots(packet(source_time='2026-10-16T07:00:00Z'),
            packet(source_time='2026-10-16T06:59:00Z', fetched='2026-10-17T13:28:00+00:00'), now=NOW)
        self.assertIn('source_time_regressed', result['flags']); self.assertTrue(result['review_required'])
        self.assertNotEqual(result['latest']['matched']['source_timestamp'], result['latest']['matched']['fetched_at'])


def icb(symbol='DEMOA', **patch):
    return dict(symbol=symbol, board='HOSE', stockType='Stock', icbCode='0301', icbName='DEMO classification', **patch)


class IcbEvidenceTests(unittest.TestCase):
    def test_original_pair_is_retained_without_taxonomy_or_effective_date_inference(self):
        row = icb(firstTradingDate='2020/01/01'); original = copy.deepcopy(row)
        result = audit_icb_metadata([row], receipt=RECEIPT); item = result['items'][0]
        self.assertEqual(item['icb_code'], '0301'); self.assertEqual(item['raw_records'], [original])
        for key in ('taxonomy_level', 'taxonomy_version', 'classification_effective_at'): self.assertIsNone(item[key])
        self.assertFalse(item['public_display_eligible']); self.assertEqual(row, original)
        self.assertEqual(result['coverage']['HNX']['sampled'], 0)

    def test_duplicate_rows_do_not_inflate_sample_coverage(self):
        result = audit_icb_metadata([icb(), icb()], receipt=RECEIPT)
        self.assertEqual(result['coverage']['HOSE'], dict(sampled=1, paired=1)); self.assertEqual(result['duplicate_rows'], 1)

    def test_conflicting_assignments_or_code_names_are_not_usable_pairs(self):
        for rows in ([icb(), {**icb(), 'icbCode': '0401'}],
                     [icb(), {**icb('DEMOB'), 'icbName': 'DEMO conflicting name'}]):
            result = audit_icb_metadata(rows, receipt=RECEIPT)
            self.assertTrue(all(row['status'] == 'CONFLICT' and row['icb_code'] is None for row in result['items']))
            self.assertEqual(result['coverage']['HOSE']['paired'], 0)

    def test_partial_identity_invalid_metadata_and_non_equities_do_not_become_classified(self):
        result = audit_icb_metadata([{**icb(), 'icbName': None}, {**icb('DEMOB'), 'icbCode': 301},
                                    {**icb('DEMOC'), 'exchange': 'HNX'}, {**icb('DEMOD'), 'stockType': 'ETF'}], receipt=RECEIPT)
        self.assertEqual(result['coverage']['HOSE'], dict(sampled=2, paired=0))
        self.assertEqual(len(result['invalid_rows']), 1); self.assertEqual(result['excluded_nonordinary_rows'], 1)

    def test_missing_variant_of_same_symbol_is_not_overwritten_by_complete_row(self):
        result = audit_icb_metadata([icb(), {**icb(), 'icbCode': None}], receipt=RECEIPT)
        self.assertEqual(result['items'][0]['status'], 'INCOMPLETE'); self.assertIsNone(result['items'][0]['icb_code'])

    def test_bad_receipts_and_unbounded_inputs_fail_closed(self):
        for receipt in ({}, {**RECEIPT, 'document_sha256': 'bad'}, {**RECEIPT, 'fetched_at': '2026-10-17'}):
            with self.assertRaises(ValueError): audit_icb_metadata([icb()], receipt=receipt)
        with self.assertRaises(ValueError): audit_icb_metadata([icb()] * 5001, receipt=RECEIPT)

    def test_record_provenance_is_bounded_and_non_json_values_are_rejected(self):
        result = audit_icb_metadata([icb()], receipt=RECEIPT)
        self.assertEqual(len(result['items'][0]['record_sha256'][0]), 64)
        self.assertEqual(result['freshness'], 'UNQUALIFIED_EFFECTIVE_TIME_UNKNOWN')
        for row in (icb(extra='x' * 65536), icb(extra=float('nan'))):
            with self.assertRaises(ValueError): audit_icb_metadata([row], receipt=RECEIPT)


if __name__ == '__main__': unittest.main()
