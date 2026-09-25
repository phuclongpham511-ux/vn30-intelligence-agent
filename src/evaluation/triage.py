"""Deterministic stratified review sampling; holdout is never queued."""
from collections import Counter
from .store import digest


def build_review_queue(cases, size=30, splits=("calibration", "stress")):
    if size < 1 or "holdout" in splits:
        raise ValueError("Positive size and non-holdout splits required")
    pool = [c for c in cases if c.split in splits]
    counts = Counter(c.event_type for c in pool)
    def score(c):
        return c.base_score if c.base_score is not None else -1
    def spread(c):
        values = [v for v in c.normalized_context_features.values() if v is not None]
        return max(values) - min(values) if len(values) >= 2 else 0
    groups = {
        "high_base": sorted(pool, key=lambda c: (-score(c), c.case_id)),
        "low_or_borderline_base": sorted((c for c in pool if c.base_score is not None), key=lambda c: (score(c), c.case_id)),
        "channel_disagreement": sorted((c for c in pool if spread(c) > 0), key=lambda c: (-spread(c), c.case_id)),
        "excluded_or_incomplete": sorted((c for c in pool if c.excluded or c.confidence < 1), key=lambda c: c.case_id),
        "repeated_event": sorted((c for c in pool if c.candidate.days_since_similar_event is not None
                                   and c.candidate.days_since_similar_event <= 5), key=lambda c: c.case_id),
        "rare_event_type": sorted(pool, key=lambda c: (counts[c.event_type], c.case_id)),
        "suspected_corporate_action": sorted((c for c in pool if "suspected_corporate_action_or_extreme_move" in c.reason_codes), key=lambda c: c.case_id),
        # Hash ordering is a stable pseudorandom control, without random module/global state.
        "hash_control": sorted(pool, key=lambda c: digest("review-control-v1:" + c.case_id)),
    }
    selected, reasons = {}, {}
    while len(selected) < min(size, len(pool)):
        changed = False
        for label, group in groups.items():
            while group and group[0].case_id in selected:
                group.pop(0)
            if group and len(selected) < size:
                case = group.pop(0)
                selected[case.case_id] = case
                reasons[case.case_id] = label
                changed = True
        if not changed:
            break
    return [{"case_id": c.case_id, "selection_reason": reasons[c.case_id],
             "review_prompt": "Judge attention-worthiness at this date using only this evidence. Do not use later outcomes. Unknown adjustments may warrant uncertain.",
             "event": c.event_type.value, "ticker": c.ticker, "date": c.replay_time.isoformat(),
             "scores": {"S": c.significance, "N": c.novelty, "C": c.confidence, "Base": c.base_score},
             "evidence": [e.__dict__ for e in c.candidate.evidence],
             "case": c.model_dump(mode="json"),
             "human_review": None} for c in selected.values()]
