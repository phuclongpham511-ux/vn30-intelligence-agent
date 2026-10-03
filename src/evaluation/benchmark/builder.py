"""Synthetic-proven offline stock-day builder; official input remains fail-closed."""
from datetime import date, datetime
from statistics import mean, pstdev

from src.analytics.market import rolling_indicators
from src.schemas.data import MarketBar
from src.evaluation.store import digest
from .episodes import link_episodes
from .facts import FAMILIES, factual_inputs, finite, transition_inputs
from .inputs import eod, visible_bar

BASELINE = "ceb944bab2e33e09a6d1586c31d1f8d8e271cde7"
VERSION = "technical-benchmark-v1-phase1"
BAR_FIELDS = {"ticker", "session", "open", "high", "low", "close", "volume", "source", "currency",
              "price_comparable", "volume_comparable", "availability_basis", "available_at", "downloaded_at"}


def _price_valid(row):
    return (row is not None and row.get("price_comparable") is True
            and all(finite(row.get(k)) and row[k] > 0 for k in ("open", "high", "low", "close"))
            and row["low"] <= min(row["open"], row["close"])
            and row["high"] >= max(row["open"], row["close"]))


def _volume_valid(row):
    return row is not None and row.get("volume_comparable") is True and finite(row.get("volume")) and row["volume"] >= 0


def _return(before, after):
    if not _price_valid(before) or not _price_valid(after):
        return None
    return after["close"] / before["close"] - 1


def _id(instrument, session, provenance, family=None):
    return digest([VERSION, provenance["logical_snapshot"], provenance["version"], instrument, session, family])[:24]


def _validate_scope(snapshot, ticker, session):
    if snapshot.get("is_fixture") is not True:
        raise PermissionError("Real data certification adapter unavailable; no automatic legacy reuse")
    if date.fromisoformat(session) >= date(2025, 1, 1):
        raise PermissionError("Research dates must be pre-2025")
    provenance = snapshot["provenance"]
    for field in ("source", "version", "logical_snapshot", "calendar_version", "adjustment_semantics",
                  "comparability_evidence", "exclusion_version"):
        if not provenance.get(field):
            raise PermissionError(f"Missing source/certification metadata: {field}")
    members = []
    for member in snapshot["membership"]:
        at = datetime.fromisoformat(member["available_at"])
        if at.utcoffset() is None:
            raise ValueError("Membership availability must be timezone-aware")
        if (member["ticker"] == ticker and member["start"] <= session
                and (member["end"] is None or session <= member["end"]) and at <= eod(session)):
            members.append(member)
    if len(members) != 1 or not all(members[0].get(k) for k in ("source", "version", "instrument", "exchange")):
        raise PermissionError("Historical membership not uniquely established as-of cutoff")
    return members[0]


def build_group(snapshot, ticker, session):
    """Build all four checks and evidence without consuming detector output or labels.

    Real-source admission intentionally needs a future verified-certificate adapter.
    Known post-session-EOD observations are excluded, including from historical
    computations; their availability is never replaced with an assumed timestamp.
    """
    member = _validate_scope(snapshot, ticker, session)
    provenance, instrument = snapshot["provenance"], member["instrument"]
    sessions = sorted(d for d in snapshot["calendar"] if d <= session)
    if not sessions or sessions[-1] != session or len(set(sessions)) != len(sessions):
        raise ValueError("Missing/duplicate session in versioned calendar")
    rows, exclusions = {}, []
    for raw in snapshot["bars"]:
        if raw["session"] > session or raw["ticker"] not in (ticker, "VN30"):
            continue
        if set(raw) - BAR_FIELDS:
            raise ValueError("Unexpected input fields; scores/labels cannot enter evidence")
        key = (raw["ticker"], raw["session"])
        if key in rows:
            raise ValueError("Duplicate source observations")
        if raw["source"] != provenance["source"] or raw.get("currency") != "VND":
            raise ValueError("Mixed source/currency; normalize explicitly before admission")
        if raw["session"] not in sessions:
            raise ValueError("Observation outside certified calendar")
        # Reuse normalized OHLCV validation whenever all fields are present.
        if all(raw.get(k) is not None for k in ("open", "high", "low", "close", "volume")):
            MarketBar(ticker=raw["ticker"], date=raw["session"], source=raw["source"],
                      **{k: raw[k] for k in ("open", "high", "low", "close", "volume")})
        row = visible_bar(raw, eod(raw["session"]))
        rows[key] = row
        if row is None:
            exclusions.append({"ticker": raw["ticker"], "session": raw["session"],
                               "reason": "not_visible_at_session_eod_or_unknown_timing"})

    state, closes, price_history, volume_history = [], [], [], []
    for i, day in enumerate(sessions):
        current = rows.get((ticker, day))
        previous = rows.get((ticker, sessions[i - 1])) if i else None
        price_continuous = _price_valid(previous) and _price_valid(current)
        volume_continuous = _volume_valid(previous) and _volume_valid(current)
        raw_return = _return(previous, current)
        if _price_valid(current):
            if not price_continuous:
                closes = []
            closes.append(current["close"])
            ma20, ma50, rsi = rolling_indicators(closes)
            indicators = {"ma20": ma20[-1], "ma50": ma50[-1], "rsi14": rsi[-1]}
        else:
            closes, indicators = [], {"ma20": None, "ma50": None, "rsi14": None}
        prior_indicators = state[-1]["indicators"] if state else {"ma20": None, "ma50": None, "rsi14": None}
        def spread(values):
            return values["ma20"] - values["ma50"] if all(finite(values[k]) for k in ("ma20", "ma50")) else None
        facts = {
            "abnormal_price_move": factual_inputs("abnormal_price_move", day, raw_return, price_history,
                                                   comparable=price_continuous),
            "unusual_volume": factual_inputs("unusual_volume", day, current.get("volume") if current else None,
                                             volume_history, comparable=_volume_valid(current)),
            "ma_cross": transition_inputs("ma_cross", spread(prior_indicators), spread(indicators), continuous=price_continuous),
            "rsi_regime_entry": transition_inputs("rsi_regime_entry", prior_indicators["rsi14"], indicators["rsi14"],
                                                   continuous=price_continuous),
        }
        state.append({"session": day, "indicators": indicators, "prior_indicators": prior_indicators,
                      "raw_return": raw_return, "facts": facts, "price_continuous": price_continuous,
                      "volume_continuous": volume_continuous})
        price_history.append({"session": day, "value": raw_return, "comparable": price_continuous})
        volume_history.append({"session": day, "value": current.get("volume") if current else None,
                               "comparable": _volume_valid(current)})

    current_state = state[-1]
    current = rows.get((ticker, session))
    previous_day = sessions[-2] if len(sessions) > 1 else None
    previous = rows.get((ticker, previous_day))
    market_before, market_after = rows.get(("VN30", previous_day)), rows.get(("VN30", session))
    market_return = _return(market_before, market_after) if current_state["raw_return"] is not None else None
    raw_return = current_state["raw_return"]
    excess = raw_return - market_return if raw_return is not None and market_return is not None else None
    group_id = _id(instrument, session, provenance)
    opportunity_ids = {family: _id(instrument, session, provenance, family) for family in FAMILIES}
    packet_id = digest([group_id, "evidence-v1"])[:24]
    common = {"schema_version": "1", "benchmark_version": VERSION, "is_fixture": True,
              "benchmark_status": "SMOKE_ONLY_NOT_BENCHMARK", "supersedes": None}
    opportunities, episode_links, recurrence = [], [], {}
    for family in FAMILIES:
        fact = current_state["facts"][family]
        opportunities.append({**common, "opportunity_id": opportunity_ids[family], "group_id": group_id,
                              "family": family, "scope": "abnormal_condition" if family in FAMILIES[:2] else "transition",
                              "sub_opportunity_key": "daily_check", "existence": "unannotated",
                              "reference_annotation": None, "expected_evidence_ids": [packet_id],
                              "observed_direction": fact["direction"], "machine_predicate_result": fact["predicate_result"],
                              "quality_reason": fact["reason"], "provenance_reference": packet_id,
                              "inventory_method": "calendar_four_family_checks_independent_of_detector"})
        links = link_episodes(instrument, family, [
            {"session": s["session"], **s["facts"][family],
             "continuous": s["volume_continuous"] if family == "unusual_volume" else s["price_continuous"]}
            for s in state])
        episode_links.append({**common, **links[-1], "group_id": group_id,
                              "opportunity_id": opportunity_ids[family], "evidence_ids": [packet_id],
                              "as_of_cutoff": eod(session).isoformat()})
        past = [s for s in state[:-1] if s["facts"][family]["predicate_result"] == "EXISTS"
                and s["facts"][family]["direction"] == fact["direction"]]
        recurrence[family] = {"past_predicate_opportunity_ids": [_id(instrument, s["session"], provenance, family) for s in past],
                              "days_since_similar_event": (date.fromisoformat(session) - date.fromisoformat(past[-1]["session"])).days if past else None,
                              "unit": "calendar_days", "null_reason": None if past else "none_observed_in_authorized_history",
                              "history_start": sessions[0], "history_is_user_exposure": False}
    volumes = [h["value"] for h in current_state["facts"]["unusual_volume"]["history"]]
    avg = mean(volumes) if volumes else None
    std = pstdev(volumes) if volumes else None
    volume = current["volume"] if _volume_valid(current) else None
    visible_inputs = [row for _, row in sorted(rows.items()) if row is not None]
    evidence = {**common, "packet_id": packet_id, "group_id": group_id,
                "cutoff": eod(session).isoformat(), "timezone": "Asia/Ho_Chi_Minh",
                "current": current, "previous": previous,
                "indicators": current_state["indicators"], "prior_indicators": current_state["prior_indicators"],
                "indicator_version": "src.analytics.market.rolling_indicators:SMA20-SMA50-Wilder14",
                "indicator_gap_policy": "restart_on_unresolved_price_continuity",
                "facts": current_state["facts"], "signed_return": raw_return,
                "return_definition": "close(t)/close(previous_calendar_session)-1",
                "benchmark": {"ticker": "VN30", "start": previous_day, "end": session,
                              "prior": market_before, "current": market_after, "return": market_return,
                              "excess_return": excess, "absolute_excess_return": abs(excess) if excess is not None else None,
                              "null_reason": None if market_return is not None else "missing_or_invalid_exact_interval_pair"},
                "volume_context": {"volume": volume, "prior_mean": avg, "n": len(volumes),
                                   "ratio": volume / avg if volume is not None and avg else None,
                                   "z_score": (volume - avg) / std if volume is not None and std else None,
                                   "null_reason": "missing_input_or_undefined_denominator" if volume is None or not std else None},
                "sector_context": {"value": None, "reason": "not_available"},
                "economic_context": {"value": None, "reason": "not_available"},
                "market_history": recurrence, "episode_as_of": episode_links,
                "exposure": {"prior_exposure_mode": "CONTROLLED_AS_IF_EMPTY", "policy": "D3-v1",
                             "provenance": "controlled_benchmark_scenario", "delivery_history": None},
                "source": provenance, "membership": member, "calendar_sessions": sessions,
                "input_subset": visible_inputs, "input_subset_sha256": digest(visible_inputs),
                "excluded_inputs": sorted(exclusions, key=lambda r: (r["ticker"], r["session"]))}
    factual_complete = all(f["predicate_result"] != "UNRESOLVED" for f in current_state["facts"].values())
    group = {**common, "group_id": group_id, "ticker": ticker, "instrument": instrument,
             "exchange": member["exchange"], "session": session, "cutoff": eod(session).isoformat(),
             "membership": member, "governance_commit": BASELINE, "prior_exposure_mode": "CONTROLLED_AS_IF_EMPTY",
             "opportunity_ids": list(opportunity_ids.values()), "evidence_id": packet_id, "evidence_sha256": digest(evidence),
             "opportunity_inventory_complete": True, "inventory_complete": False,
             "candidate_inventory_status": "NOT_RUN_PHASE1", "candidate_ids": None,
             "evidence_complete": factual_complete and market_return is not None,
             "reference_complete": False, "completeness_reasons": ["candidate_capture_not_run", "human_reference_unannotated"],
             "data_state": "AVAILABLE" if factual_complete else "TECHNICAL_DATA_UNAVAILABLE_OR_INCOMPLETE",
             "expected_response_state": None, "expected_response_reason": "requires_independent_human_reference",
             "complete_reference_insight_set": None, "overflow": None,
             "attention_budget_max": 3, "required_delivery": "NO", "delivery_policy": "D5-v1",
             "sampling_component": "SMOKE", "split": "NON_BENCHMARK", "inclusion_probability": None,
             "inclusion_reason": "synthetic_framework_verification_only", "processed": True}
    return {"group": group, "opportunities": opportunities, "evidence": evidence, "episode_links": episode_links}
