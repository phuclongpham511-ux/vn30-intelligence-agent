"""Attach inspectable context after detection/scoring, leaving the candidate intact."""
from dataclasses import replace
from datetime import date, datetime

from .models import CorporateActionContext, aware_utc


TECHNICAL_TYPES = frozenset(('abnormal_price_move', 'unusual_volume', 'ma_cross',
    'rsi_regime_entry', 'bollinger_lower_reversal_volume', 'bollinger_upper_reversal_volume'))


def event_session(candidate):
    value = candidate.observed_at
    if isinstance(value, datetime):
        raise ValueError('Technical context requires an explicit session date, not a timestamp')
    return value if isinstance(value, date) else date.fromisoformat(value)


def context_for_candidate(candidate, repository, *, generated_at):
    now = aware_utc(generated_at)
    if repository is None or candidate.event_type.value not in TECHNICAL_TYPES:
        return CorporateActionContext()
    return repository.context_for(candidate.ticker, event_session(candidate), as_of=now)


def enrich_result(result, repository, *, generated_at):
    context = context_for_candidate(result.candidate, repository, generated_at=generated_at)
    return replace(result, corporate_action_context=context)
