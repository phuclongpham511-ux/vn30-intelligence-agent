"""Refresh descriptive reporting from local immutable replay outputs and human labels."""
import argparse
import json
from pathlib import Path
from src.evaluation.models import ReplayCase, HumanReview
from src.evaluation.store import read_jsonl, load_dataset, write_json, write_jsonl
from src.evaluation.metrics import report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    args = parser.parse_args()
    _, observations = load_dataset(args.run.parents[1])
    cases = read_jsonl(args.run / "replay_cases.jsonl", ReplayCase)
    holdout = read_jsonl(args.run / "holdout_cases.jsonl", ReplayCase)
    queue_path = args.run / "review_queue.jsonl"
    queue = [json.loads(line) for line in queue_path.read_text(encoding="utf-8").splitlines()] if queue_path.exists() else []
    reviews_path = args.run / "human_reviews.jsonl"
    reviews = read_jsonl(reviews_path, HumanReview) if reviews_path.exists() else []
    summary = report(observations, cases + holdout, queue, reviews)
    write_json(args.run / "summary.json", summary)
    write_jsonl(args.run / "excluded_observations.jsonl", [
        {"observation": o.model_dump(mode="json"), "reason":
         "fixture_nonmarket" if o.is_fixture and o.data_type in ("fundamental", "news") else
         "unknown_available_at" if o.available_at is None or o.availability_basis == "unknown" else
         "stream_not_enabled_v0"}
        for o in observations if o.data_type in ("fundamental", "news") or o.available_at is None or o.availability_basis == "unknown"])
    print(json.dumps({k: summary[k] for k in ("detected_candidates", "review_queue_size", "human_reviewed_cases", "benchmark_status")}, indent=2))


if __name__ == "__main__":
    main()
