"""Descriptive reporting only. No unsupported accuracy claims."""
from collections import Counter, defaultdict
from statistics import mean, median


def distribution(values):
    values = sorted(v for v in values if v is not None)
    return {"count": len(values), "min": min(values) if values else None,
            "median": median(values) if values else None,
            "mean": mean(values) if values else None, "max": max(values) if values else None}


def report(observations, cases, queue=(), reviews=()):
    indexed = {c.case_id: c for c in cases}
    latest = {}
    for r in sorted(reviews, key=lambda r: (r.reviewed_at, r.review_version)):
        if r.case_id not in indexed or indexed[r.case_id].split == "holdout":
            raise ValueError("Unknown or protected holdout label")
        latest[r.case_id] = r
    result = {"status": "descriptive_only", "raw_observations": len(observations),
        "observations_by_stream": dict(Counter(o.data_type for o in observations)),
        "unknown_available_at": sum(o.available_at is None for o in observations),
        "unsupported_nonmarket_records": sum(o.data_type in ("fundamental", "news") for o in observations),
        "detected_candidates": len(cases), "scored": sum(not c.excluded for c in cases),
        "excluded": sum(c.excluded for c in cases),
        "by_type": dict(Counter(c.event_type.value for c in cases)),
        "by_ticker": dict(Counter(c.ticker for c in cases)),
        "by_period": dict(Counter(c.replay_time.strftime("%Y-%m") for c in cases)),
        "by_split": dict(Counter(c.split for c in cases)),
        "base_by_split": {s: distribution(c.base_score for c in cases if c.split == s)
                          for s in ("calibration", "validation", "stress", "unassigned")},
        "holdout_policy": "Scores withheld from development summaries and review queues; separate holdout cases remain sealed for Phase 3 evaluation.",
        "missing_channels": dict(Counter(k for c in cases for k,v in c.normalized_context_features.items() if v is None)),
        "exclusion_reasons": dict(Counter(c.exclusion_reason for c in cases if c.excluded)),
        "flags": dict(Counter(r for c in cases for r in c.reason_codes)),
        "repeat_within_5_days": sum(c.candidate.days_since_similar_event is not None
                                     and c.candidate.days_since_similar_event <= 5 for c in cases),
        "review_queue_size": len(queue),
        "queue_by_type": dict(Counter(item["event"] for item in queue)),
        "queue_by_selection": dict(Counter(item["selection_reason"] for item in queue)),
        "human_reviewed_cases": len(latest),
        "review_verdicts": dict(Counter(r.verdict for r in latest.values())),
        "reviewed_batch_present": bool(latest),
        "benchmark_status": "human_labels_present_not_accuracy_validated" if latest else "awaiting_human_review"}
    by_attention = defaultdict(list)
    disagreements = Counter()
    for review in latest.values():
        case = indexed[review.case_id]
        by_attention[review.attention_level].append(case.base_score)
        if review.verdict in ("reject", "modify", "uncertain"):
            disagreements[case.event_type.value] += 1
    result["base_by_attention_level"] = {str(k): distribution(v) for k,v in by_attention.items()}
    result["event_types_with_review_disagreement"] = dict(disagreements)
    return result
