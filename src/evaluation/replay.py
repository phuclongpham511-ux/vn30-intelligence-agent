"""Chronological, provider-free replay of normalized market observations."""
from dataclasses import replace, asdict
from datetime import date
from src.analytics.market import technical_history, market_snapshot
from src.materiality.detectors import detect_market_events
from src.materiality.service import evaluate_candidate
from .context import build_context
from .event_memory import EventMemory
from .models import ReplayCase
from .store import digest, validate_observations


def replay(observations, manifest, config):
    observations = validate_observations(observations)
    benchmark = {o.payload.date: o for o in observations if o.data_type == "benchmark"
                 and o.ticker == manifest.benchmark and o.available_at is not None and not o.is_fixture}
    market = sorted((o for o in observations if o.data_type == "market" and o.available_at is not None
                     and o.availability_basis != "unknown"),
                    key=lambda o: (o.available_at, o.ticker, o.observation_time))
    histories, features, memories = {}, {}, {}
    cases = []
    for observation in market:
        current = observation.payload
        now = observation.available_at
        era = "stress" if current.date < config.primary_start else "primary"
        key = (observation.ticker, era)
        history = histories.setdefault(key, [])
        past = features.setdefault(key, [])
        memory = memories.setdefault(key, EventMemory())
        if history and current.date <= history[-1].payload.date:
            # Late/revised observations cannot rewrite a previously replayed state.
            raise ValueError("Out-of-order availability; use a separately versioned dataset")
        if history and (current.source != history[-1].source or current.currency != history[-1].payload.currency):
            raise ValueError("Mixed source/currency history")
        bars = [o.payload for o in history] + [current]
        technicals = technical_history(observation.ticker, bars, observation.source)
        snapshot = market_snapshot(observation.ticker, bars, observation.source)
        previous = technicals[-2] if len(technicals) > 1 else None
        excess, benchmark_evidence = None, []
        if previous:
            pair = [benchmark.get(previous.date), benchmark.get(current.date)]
            if all(b is not None and b.available_at <= now and b.availability_basis != "unknown" for b in pair):
                b0, b1 = pair
                if b0.source == b1.source and b0.payload.currency == b1.payload.currency:
                    benchmark_return = market_snapshot(b1.ticker, [b0.payload, b1.payload], b1.source).daily_return
                    excess = snapshot.daily_return - benchmark_return
                    benchmark_evidence = [b.model_dump(mode="json") for b in pair]
        raw, contexts = build_context(snapshot, technicals[-1], past, current.volume, excess, config)
        for event, context in contexts.items():
            contexts[event] = replace(context, days_since_similar_event=memory.days_since(observation.ticker, event, now))
        # A fixture anywhere in the expanding indicator prefix contaminates its outputs.
        fixture = observation.is_fixture or any(o.is_fixture for o in history)
        candidates = detect_market_events(previous, technicals[-1], contexts, is_fixture=fixture)
        flags = []
        if manifest.adjustment_basis == "unknown":
            flags.append("adjustment_semantics_unknown")
        if observation.availability_basis == "end_of_day_assumption":
            flags.append("modeled_end_of_day_availability")
        if snapshot.daily_return is not None and abs(snapshot.daily_return) >= .15:
            flags.append("suspected_corporate_action_or_extreme_move")
        for candidate in candidates:
            candidate = replace(candidate, reason_codes=candidate.reason_codes + tuple(flags))
            result = evaluate_candidate(candidate)
            normalized = {name: getattr(candidate, name) for name in ("own_history_abnormality",
                "market_relative_abnormality", "sector_relative_abnormality", "economic_magnitude")}
            provenance = {"dataset_version": manifest.dataset_version,
                "dataset_sha256": manifest.content_sha256, "source": observation.source,
                "adjustment_basis": manifest.adjustment_basis, "is_fixture": fixture,
                "observation_time": observation.observation_time, "available_at": now.isoformat(),
                "availability_basis": observation.availability_basis,
                "prefix_start": history[0].observation_time if history else observation.observation_time,
                "prefix_sessions": len(bars), "benchmark_evidence": benchmark_evidence,
                "limitations": manifest.known_limitations}
            case_id = digest({"dataset": manifest.dataset_version, "config": config.model_dump(mode="json"),
                              "candidate": asdict(candidate), "replay_time": now})[:24]
            cases.append(ReplayCase(case_id=case_id, ticker=observation.ticker, replay_time=now,
                event_type=candidate.event_type, category=candidate.category.value, candidate=candidate,
                significance=result.components.significance, novelty=result.components.novelty,
                confidence=result.components.confidence, base_score=result.base_score,
                raw_context_features=raw, normalized_context_features=normalized,
                reason_codes=list(result.reason_codes), excluded=result.excluded, exclusion_reason=result.exclusion_reason,
                source_provenance=provenance, context_version=config.context_version, split=config.split(current.date)))
            memory.record(observation.ticker, candidate.event_type, now)
        history.append(observation)
        past.append(raw)
    return cases
