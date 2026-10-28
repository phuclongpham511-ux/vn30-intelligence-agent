"""Scoped evidence history, not a second scoring or event-memory engine."""
from datetime import datetime, timezone

from pydantic import field_validator
from sqlmodel import select
from src.materiality.models import MaterialityResult
from .context import TECHNICAL_TYPES, enrich_result
from .models import ActionModel, CorporateActionContext, aware_utc
from .repository import content_hash
from .storage import TechnicalContextEvent, TechnicalContextUpdate


class ContextUpdate(ActionModel):
    update_id: str
    enriched_at: datetime
    context: CorporateActionContext

    @field_validator('enriched_at')
    @classmethod
    def utc_time(cls, value):
        return aware_utc(value)


class RecordedTechnicalEvent(ActionModel):
    event_id: str
    generated_at: datetime
    result: MaterialityResult
    updates: tuple[ContextUpdate, ...] = ()

    @field_validator('generated_at')
    @classmethod
    def utc_time(cls, value):
        return aware_utc(value)


class TechnicalContextHistory:
    def __init__(self, repository):
        self.repository = repository
        self.session = repository.session

    def record(self, event_id: str, result: MaterialityResult, *, generated_at: datetime):
        if not event_id.strip() or result.candidate.event_type.value not in TECHNICAL_TYPES:
            raise ValueError('A stable Technical event ID is required')
        now = aware_utc(generated_at)
        # Re-query at generation, even if caller supplied later enriched evidence.
        original = RecordedTechnicalEvent(event_id=event_id, generated_at=now,
            result=enrich_result(result, self.repository, generated_at=now))
        payload = original.model_dump(mode='json')
        existing = self.session.get(TechnicalContextEvent, event_id)
        if existing:
            if existing.payload != payload:
                raise ValueError('Original event is immutable; append a context update')
        else:
            self.session.add(TechnicalContextEvent(id=event_id, generated_at=now, payload=payload))
            self.session.commit()
        return self.get(event_id, as_of=now)

    def get(self, event_id: str, *, as_of: datetime):
        cutoff = aware_utc(as_of)
        row = self.session.get(TechnicalContextEvent, event_id)
        if row is None:
            raise KeyError(event_id)
        original = RecordedTechnicalEvent.model_validate(row.payload)
        if original.generated_at > cutoff:
            raise KeyError('Event was not yet generated')
        updates = self.session.exec(select(TechnicalContextUpdate).where(
            TechnicalContextUpdate.event_id == event_id, TechnicalContextUpdate.enriched_at <= cutoff
        ).order_by(TechnicalContextUpdate.enriched_at, TechnicalContextUpdate.id)).all()
        return original.model_copy(update={'updates': tuple(ContextUpdate.model_validate(u.payload) for u in updates)})

    def append_update(self, event_id: str, *, enriched_at: datetime | None = None):
        now = aware_utc(enriched_at or datetime.now(timezone.utc))
        # Inspect latest stored history first: backdated writes must never rewrite it.
        event = self.get(event_id, as_of=datetime.max.replace(tzinfo=timezone.utc))
        last_time = event.updates[-1].enriched_at if event.updates else event.generated_at
        if now <= last_time:
            raise ValueError('Context updates must follow existing event history')
        context = enrich_result(event.result, self.repository, generated_at=now).corporate_action_context
        previous = event.updates[-1].context if event.updates else event.result.corporate_action_context
        if context.model_dump(exclude={'as_of'}) == previous.model_dump(exclude={'as_of'}):
            return event
        update = ContextUpdate(update_id=content_hash([event_id, now.isoformat(), context.model_dump(mode='json')]),
            enriched_at=now, context=context)
        self.session.add(TechnicalContextUpdate(id=update.update_id, event_id=event_id,
            enriched_at=now, payload=update.model_dump(mode='json')))
        self.session.commit()
        return self.get(event_id, as_of=now)
