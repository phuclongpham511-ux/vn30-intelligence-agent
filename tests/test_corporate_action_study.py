"""Research-only boundaries and overlap arithmetic; no provider requests."""
from datetime import date

import pytest

from research.provenance.technical_data_readiness_v1.corporate_action_study import (
    SAMPLE, overlap_counts, session_distance, validate_scope,
)


def test_scope_checks_before_acquisition():
    cohort = {r['symbol'] for r in SAMPLE}
    validate_scope(SAMPLE, cohort, {'studies': []})
    with pytest.raises(ValueError, match='protected'):
        validate_scope(SAMPLE, cohort, {'studies': [{'records': [{'ticker': 'GAS'}]}]})
    with pytest.raises(ValueError, match='Cohort'):
        validate_scope(SAMPLE, set(), {'studies': []})
    with pytest.raises(ValueError, match='Date'):
        validate_scope([{**SAMPLE[0], 'end': '2025-01-01'}], cohort, {'studies': []})


def test_distance_counts_observed_sessions_and_keeps_missing_unknown():
    days = [date(2024, 9, d) for d in (12, 13, 16, 17, 18, 19, 20)]
    assert session_distance(days, days[2], days[1]) == 1
    assert session_distance(days, days[0], days[1]) == -1
    assert session_distance(days, date(2024, 9, 14), days[1]) is None
    assert session_distance(days, days[1], date(2024, 9, 14)) is None
    events = [(d, 'unusual_volume') for d in days]
    counts = overlap_counts(events, days, days[3])
    assert [counts[str(w)]['inside']['unusual_volume'] for w in range(4)] == [1, 3, 5, 7]
    assert [counts[str(w)]['outside']['unusual_volume'] for w in range(4)] == [6, 4, 2, 0]
    assert counts['0']['inside']['abnormal_price_move'] == 0
    with pytest.raises(ValueError, match='Missing'):
        overlap_counts(events, days, date(2024, 9, 14))
    with pytest.raises(ValueError, match='Missing'):
        overlap_counts([], days, date(2024, 9, 14))
