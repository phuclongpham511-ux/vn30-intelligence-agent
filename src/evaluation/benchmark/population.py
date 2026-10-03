"""D2 V3 evaluation-population boundary; no provider access or engine features."""
from dataclasses import dataclass
from datetime import date
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Literal

from pydantic import StrictBool, ValidationError
from src.evaluation.models import EvaluationModel

COHORT_PATH = Path(__file__).resolve().parents[3] / 'research/provenance/technical_benchmark_population_v1/BENCHMARK_COHORT_V1.json'
COHORT_SHA256 = 'b02ee0d77c48ed097dd068a6290f8bb0e26785f7f8b6125423948d696a36f499'
CLAIM_SCOPE = ('The Technical Materiality engine was evaluated on a frozen VN30 deployment '
               'cohort across historical market regimes in 2020–2024. The primary benchmark '
               'does not reproduce or claim representativeness of point-in-time historical '
               'VN30 membership.')


@dataclass(frozen=True)
class Cohort:
    cohort_id: str
    cohort_version: str
    normalized_cohort_sha256: str
    tickers: tuple[str, ...]


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key: ' + key)
        result[key] = value
    return result


def load_cohort(path=COHORT_PATH):
    """Read only the explicit frozen artifact; never repair or refresh membership."""
    data = json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=_unique_object)
    required = {'cohort_id': 'BENCHMARK_COHORT_V1', 'cohort_version': '1.0.0',
                'index_name': 'VN30', 'review_cycle': '2026-07', 'effective_from': '2026-08-03',
                'effective_date_derivation': 'RULE_DERIVED_FROM_OFFICIAL_HOSE_GROUND_RULES',
                'normalization_version': 'ticker-uppercase-trim-unique-sort-v1',
                'certification_status': 'COHORT_SOURCE_CERTIFIED',
                'normalized_cohort_sha256': COHORT_SHA256}
    if not isinstance(data, dict) or any(data.get(k) != v for k, v in required.items()):
        raise ValueError('Invalid cohort authority or certification')
    tickers = data.get('tickers')
    if (not isinstance(tickers, list) or len(tickers) != 30
            or any(not isinstance(t, str) or re.fullmatch(r'[A-Z0-9]+', t) is None for t in tickers)
            or tickers != sorted(set(tickers))):
        raise ValueError('Require exactly 30 unique normalized sorted tickers')
    # Frozen B1.1 hash scope: never trust a scope supplied by a replacement file.
    excluded = {'normalized_cohort_sha256', 'normalized_cohort_sha256_scope',
                'captured_at', 'certification_status', 'notes'}
    core = {k: v for k, v in data.items() if k not in excluded}
    content = json.dumps(core, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
    if sha256(content.encode('utf-8')).hexdigest() != COHORT_SHA256:
        raise ValueError('Cohort hash mismatch')
    return Cohort(data['cohort_id'], data['cohort_version'], COHORT_SHA256, tuple(tickers))


class ListingEvidence(EvaluationModel):
    status: Literal['PRE_LISTING', 'LISTING_STATUS_UNKNOWN', 'LISTED_AND_TRADING']
    ticker: str
    session: date
    first_trading_session: date | None = None
    source_kind: Literal['EXCHANGE_NOTICE', 'CERTIFIED_LISTING_RECORD'] | None = None
    source: str | None = None
    version: str | None = None
    evidence_reference: str | None = None
    certification_status: Literal['CERTIFIED', 'UNVERIFIED', 'MISSING'] = 'MISSING'


class PriorSession(EvaluationModel):
    session: date
    valid: StrictBool = False
    comparable: StrictBool = False
    is_trading_session: StrictBool = False


class StockDayEligibility(EvaluationModel):
    ticker: str
    session: date
    component: Literal['REPRESENTATIVE', 'ENRICHED_DIAGNOSTIC']
    listing: ListingEvidence
    prior_sessions: tuple[PriorSession, ...] = ()
    historical_membership_status: Literal['YES', 'NO', 'UNKNOWN'] = 'UNKNOWN'
    diagnostic_purpose: str | None = None
    diagnostic_reason: str | None = None


def evaluate_eligibility(cohort, metadata):
    """Evaluate declared metadata only, not authenticity or B3–B6 certification.

    Session flags must come from later certified data preparation. This seam
    opens no history, does not infer listing, and cannot authorize sampling.
    """
    result = {'decision': 'UNRESOLVED', 'reasons': [], 'prior_valid_sessions': None,
              'official_sampling_enabled': False, 'historical_membership_status': 'UNKNOWN',
              'cohort_id': cohort.cohort_id, 'cohort_sha256': cohort.normalized_cohort_sha256}
    def finish(decision, reason):
        return {**result, 'decision': decision, 'reasons': [reason]}
    try:
        row = StockDayEligibility.model_validate(metadata)
    except ValidationError:
        return finish('UNRESOLVED', 'INVALID_ELIGIBILITY_METADATA')
    result.update(historical_membership_status=row.historical_membership_status,
                  component=row.component, diagnostic_purpose=row.diagnostic_purpose,
                  diagnostic_reason=row.diagnostic_reason)
    if row.ticker not in cohort.tickers:
        return finish('INELIGIBLE', 'OUTSIDE_FROZEN_COHORT')
    if not date(2020, 1, 1) <= row.session < date(2025, 1, 1):
        return finish('INELIGIBLE', 'OUTSIDE_BENCHMARK_FRAME')
    listing = row.listing
    if listing.status == 'PRE_LISTING':
        return finish('INELIGIBLE', 'PRE_LISTING')
    if listing.status == 'LISTING_STATUS_UNKNOWN':
        return finish('UNRESOLVED', 'LISTING_STATUS_UNKNOWN')
    if (listing.ticker != row.ticker or listing.session != row.session
            or listing.certification_status != 'CERTIFIED' or not listing.source_kind
            or not all(v and v.strip() for v in (listing.source, listing.version, listing.evidence_reference))
            or listing.first_trading_session is None or listing.first_trading_session > row.session):
        return finish('UNRESOLVED', 'LISTING_PROVENANCE_UNRESOLVED')
    sessions = [p.session for p in row.prior_sessions]
    if len(sessions) != len(set(sessions)):
        return finish('UNRESOLVED', 'DUPLICATE_HISTORY_SESSIONS')
    count = sum(listing.first_trading_session <= p.session < row.session
                and p.valid and p.comparable and p.is_trading_session for p in row.prior_sessions)
    result['prior_valid_sessions'] = count
    if count < 60:
        if (row.component == 'ENRICHED_DIAGNOSTIC'
                and row.diagnostic_purpose in {'insufficient_history', 'unavailable_evidence', 'fail_closed_behavior'}
                and row.diagnostic_reason and row.diagnostic_reason.strip()):
            return finish('ELIGIBLE', 'DECLARED_EARLY_HISTORY_DIAGNOSTIC_ONLY')
        return finish('INELIGIBLE', 'INSUFFICIENT_PRIOR_VALID_SESSIONS')
    return finish('ELIGIBLE', 'COHORT_LISTING_HISTORY_ELIGIBLE_PENDING_DATA_ADMISSION')
