"""Session-scoped append-only ingestion and deterministic as-of source views."""
from datetime import date, datetime, timezone
from hashlib import sha256
import json

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select
from src.schemas.stocks import SymbolRequest
from .models import (ActionType, CorporateActionContext, CorporateActionNotice,
                     CorporateActionObservation, IngestionResult, aware_utc)
from .storage import CorporateActionRecord


def content_hash(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                             allow_nan=False).encode()).hexdigest()


class CorporateActionRepository:
    def __init__(self, session):
        self.session = session

    def ingest(self, notice: CorporateActionNotice, *, received_at=None):
        # Explicit receipt injection supports simulations; imports default to actual UTC.
        now = aware_utc(received_at or datetime.now(timezone.utc))
        payload = notice.model_dump(mode='json')
        action_id = content_hash([notice.source, notice.source_id or notice.source_url,
                                  notice.component_id or f'{notice.symbol}:{notice.action_type.value}'])
        latest = self.session.exec(select(CorporateActionRecord).where(
            CorporateActionRecord.action_id == action_id).order_by(CorporateActionRecord.observed_at.desc())).first()
        version = content_hash(payload)
        if latest:
            previous = CorporateActionObservation.model_validate(latest.payload)
            if now < previous.observed_at:
                raise ValueError('Receipt time precedes existing knowledge')
            if latest.content_hash == version:
                return IngestionResult(status='duplicate', observation=previous)
            if now == previous.observed_at:
                raise ValueError('Conflicting revisions at the same receipt time')
        observation = CorporateActionObservation(**notice.model_dump(), action_id=action_id,
            observation_id=content_hash([action_id, now.isoformat(), version]), observed_at=now)
        self.session.add(CorporateActionRecord(id=observation.observation_id, action_id=action_id,
            observed_at=now, content_hash=version, payload=observation.model_dump(mode='json')))
        self.session.commit()
        return IngestionResult(status='revision' if latest else 'inserted', observation=observation)

    def get_known_actions_as_of(self, *, as_of: datetime):
        cutoff = aware_utc(as_of)
        # Choose revisions before filtering symbol/date: corrections can change either.
        rows = self.session.exec(select(CorporateActionRecord).where(
            CorporateActionRecord.observed_at <= cutoff).order_by(CorporateActionRecord.observed_at,
                                                                CorporateActionRecord.id)).all()
        latest = {}
        for row in rows:
            latest[row.action_id] = CorporateActionObservation.model_validate(row.payload)
        return tuple(latest[k] for k in sorted(latest))

    def get_actions_for_symbol(self, symbol: str, *, as_of: datetime):
        symbol = SymbolRequest(ticker=symbol).symbol
        return tuple(a for a in self.get_known_actions_as_of(as_of=as_of) if a.symbol == symbol)

    def get_actions_effective_on(self, symbol: str, session_date: date, *, as_of: datetime):
        return tuple(a for a in self.get_actions_for_symbol(symbol, as_of=as_of)
            if a.verified and not a.withdrawn and a.action_type != ActionType.OTHER
            and a.effective_date is not None and a.effective_date == session_date)

    def context_for(self, symbol: str, session_date: date, *, as_of: datetime):
        cutoff = aware_utc(as_of)
        try:
            actions = self.get_actions_effective_on(symbol, session_date, as_of=cutoff)
        except SQLAlchemyError:
            return CorporateActionContext(as_of=cutoff, reason='source_unavailable')
        return CorporateActionContext(status='KNOWN_MATCH' if actions else 'UNKNOWN', as_of=cutoff,
            actions=actions, reason='verified_exact_session' if actions else 'not_observed')
