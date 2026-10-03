"""D4 cutoff-local machine episode evidence, never human relationship labels."""
from src.evaluation.store import digest
from .facts import FAMILIES


def link_episodes(instrument, family, rows):
    if family not in FAMILIES:
        raise ValueError("Unknown event family")
    ordered = sorted(rows, key=lambda r: r["session"])
    if len({r["session"] for r in ordered}) != len(ordered):
        raise ValueError("Duplicate episode sessions")
    active, direction, uncertain = None, None, False
    links = []
    for row in ordered:
        result, closed, lifecycle = row["predicate_result"], None, "NONE"
        regime_family = family in FAMILIES[2:]
        regime = row.get("regime") if regime_family else row.get("direction")
        continuity = row.get("continuous", False)
        valid = result != "UNRESOLVED" and continuity
        if not valid:
            uncertain, lifecycle = True, "UNRESOLVED"
        elif regime_family:
            if result == "EXISTS":
                closed = active if not uncertain else None
                active = digest(["d4-v1", instrument, family, row["session"], regime])[:24]
                direction, uncertain, lifecycle = regime, False, "ANCHOR"
            elif family == "rsi_regime_entry" and regime is None:
                closed = active if not uncertain else None
                active, direction, uncertain, lifecycle = None, None, False, "CLOSED" if closed else "NONE"
            elif regime is None or uncertain or not active or regime != direction:
                uncertain, lifecycle = True, "UNRESOLVED"
            else:
                lifecycle = "CONTINUATION"
        elif result == "DOES_NOT_EXIST":
            closed = active if not uncertain else None
            active, direction, uncertain, lifecycle = None, None, False, "CLOSED" if closed else "NONE"
        elif uncertain or regime not in ("up", "down", "HIGH"):
            uncertain, lifecycle = True, "UNRESOLVED"
        elif active and regime == direction:
            lifecycle = "CONTINUATION"
        else:
            closed = active
            active = digest(["d4-v1", instrument, family, row["session"], regime])[:24]
            direction, lifecycle = regime, "ANCHOR"
        links.append({"link_id": digest(["d4-link-v1", instrument, family, row["session"]])[:24],
                      "family": family, "session": row["session"], "lifecycle": lifecycle,
                      "episode_id": None if uncertain else active or closed,
                      "closed_episode_id": closed, "prior_unresolved_episode_id": active if uncertain else None,
                      "relationship": "UNRESOLVED" if uncertain else "same_episode" if lifecycle == "CONTINUATION" else "separate",
                      "reason": "unresolved_continuity_or_anchor" if uncertain else None,
                      "as_of": row["session"], "human_relationship_status": "unannotated"})
    return links
