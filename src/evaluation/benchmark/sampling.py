"""D6 hash sampling primitives only; no official frame is selected by Phase 1."""
from src.evaluation.store import digest

D6_QUOTAS = {"development_representative": 80, "development_enriched": 40,
             "fresh_validation": 60, "development_reviewer_b": 36}
EVIDENCE_RULES = {"multiple_conditions", "quality", "episode_boundary", "raw_market_disagreement", "potential_high_demand"}


def sample_frame(frame, count, *, seed, frame_version, component, evidence_rule=None, excluded_ids=()):
    if not seed or not frame_version or type(count) is not int or count < 0:
        raise ValueError("Freeze seed, frame version and nonnegative quota")
    if component not in ("REPRESENTATIVE", "ENRICHED", "REVIEWER_B", "FRESH_VALIDATION"):
        raise ValueError("Unknown sampling component")
    if len({row["group_id"] for row in frame}) != len(frame):
        raise ValueError("Duplicate frame stock-days")
    if component == "ENRICHED" and evidence_rule not in EVIDENCE_RULES:
        raise ValueError("Freeze a permitted evidence-only enrichment rule")
    if component != "ENRICHED" and evidence_rule is not None:
        raise ValueError("Representative/control sampling cannot be evidence enriched")
    excluded = set(excluded_ids)
    eligible = [r for r in frame if r["group_id"] not in excluded and
                (component != "ENRICHED" or evidence_rule in r.get("evidence_tags", []))]
    if len(eligible) < count:
        raise ValueError("Insufficient eligible groups; do not silently replace or weaken eligibility")
    ordered = sorted(eligible, key=lambda r: (digest([seed, frame_version, component, r["group_id"]]), r["group_id"]))
    return [{**row, "sampling_component": component, "sampling_seed": seed,
             "frame_version": frame_version, "sampling_rule": "sha256-order-v1",
             "inclusion_reason": evidence_rule or "deterministic_hash_control",
             "inclusion_probability": None, "probability_reason": "fixed_seed_design_no_randomization_claim"}
            for row in ordered[:count]]


def reviewer_subset(development, seed, frame_version):
    if len(development) * 3 % 10:
        raise ValueError("30% must be an exact integer; freeze any different rounding policy")
    return sample_frame(development, len(development) * 3 // 10, seed=seed,
                        frame_version=frame_version, component="REVIEWER_B")


def quarantine_validation(development, validation):
    """Conservative split-component closure; never changes earlier as-of episodes."""
    groups = development + validation
    if len({r["group_id"] for r in groups}) != len(groups):
        raise ValueError("Stock-day occurs in multiple partitions")
    contaminated = {r["group_id"] for r in development}
    contaminated.update(r["group_id"] for r in groups if r.get("boundary_unresolved"))
    while True:
        episodes = {e for r in groups if r["group_id"] in contaminated for e in r.get("episode_ids", []) if e}
        expanded = contaminated | {r["group_id"] for r in groups if episodes.intersection(r.get("episode_ids", []))}
        if expanded == contaminated:
            break
        contaminated = expanded
    ordered = sorted(validation, key=lambda r: r["group_id"])
    return {"eligible": [r for r in ordered if r["group_id"] not in contaminated],
            "quarantined": [{**r, "quarantine_reason": "shared_episode_component_or_unresolved_boundary"}
                            for r in ordered if r["group_id"] in contaminated]}
