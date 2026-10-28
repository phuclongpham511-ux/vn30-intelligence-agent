"""Lossless repository reads and managed acquisition at existing public seams."""
from datetime import date, datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from src.corporate_actions.models import CorporateActionNotice
from src.corporate_actions.repository import CorporateActionRepository
from src.corporate_actions.storage import CorporateActionRecord

NOW = datetime(2026, 10, 1, tzinfo=timezone.utc)


def notice(**changes):
    return CorporateActionNotice.model_validate(dict(symbol='ABC', source='synthetic',
        source_id='notice', action_type='cash_dividend', verified=True,
        effective_date='2026-10-05', is_fixture=True) | changes)


def test_stored_dividend_extensions_round_trip_without_rewriting_provenance(session):
    repository = CorporateActionRepository(session)
    old = repository.ingest(notice(), received_at=NOW).observation
    stored = session.get(CorporateActionRecord, old.observation_id)
    payload = old.model_dump(mode='json') | dict(source_updated_at='2026-09-30T12:00:00Z',
        source_title='Original source title', evidence_text='Original evidence.\r\nNo normalization.')
    stored.payload = payload
    session.add(stored); session.commit()
    known = repository.get_known_actions_as_of(as_of=NOW)[0]
    assert known.source_title == payload['source_title']
    assert known.evidence_text == payload['evidence_text']
    assert known.source_updated_at == datetime(2026, 9, 30, 12, tzinfo=timezone.utc)
    assert repository.context_for('ABC', date(2026, 10, 5), as_of=NOW).actions[0] == known
    session.refresh(stored)
    assert stored.payload == payload  # read does not migrate, truncate or rewrite JSON


def test_legacy_notice_serialization_and_duplicate_identity_stay_unchanged(session):
    repository = CorporateActionRepository(session)
    original = repository.ingest(notice(), received_at=NOW).observation
    assert not {'source_updated_at', 'source_title', 'evidence_text'} & original.model_dump().keys()
    again = repository.ingest(notice(), received_at=NOW+timedelta(days=1))
    assert again.status == 'duplicate' and again.observation == original
    with pytest.raises(ValidationError):
        notice(unrecognized_provenance='must not be silently dropped')


def test_unresolved_correction_withholds_context_only_after_receipt(session):
    repository = CorporateActionRepository(session)
    repository.ingest(notice(), received_at=NOW)
    repository.ingest(notice(source_id='correction', action_type='other', verified=False,
        verification_note='Unresolved correction: requires association'),
        received_at=NOW+timedelta(days=1))
    assert repository.context_for('ABC', date(2026, 10, 5), as_of=NOW).status == 'KNOWN_MATCH'
    current = repository.context_for('ABC', date(2026, 10, 5), as_of=NOW+timedelta(days=1))
    assert current.status == 'UNKNOWN' and current.reason == 'pending_verification'
    assert len(repository.get_actions_for_symbol('ABC', as_of=NOW+timedelta(days=1))) == 2
