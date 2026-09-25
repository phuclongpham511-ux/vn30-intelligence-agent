"""Validate and append human-authored labels without editing replay results."""
import argparse
from pathlib import Path
from src.evaluation.models import ReplayCase, HumanReview
from src.evaluation.store import read_jsonl, save_reviews, load_dataset, write_json, write_jsonl
from src.evaluation.metrics import report
import json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("labels", type=Path)
    args = parser.parse_args()
    cases = read_jsonl(args.run / "replay_cases.jsonl", ReplayCase)
    reviews = read_jsonl(args.labels, HumanReview)
    save_reviews(args.run / "human_reviews.jsonl", reviews, cases)
    saved = read_jsonl(args.run / "human_reviews.jsonl", HumanReview)
    latest = {}
    for review in sorted(saved, key=lambda r: (r.reviewed_at, r.review_version)):
        latest[review.case_id] = review
    indexed = {c.case_id: c for c in cases}
    write_jsonl(args.run / "reviewed_benchmark.jsonl", [
        {"case": indexed[r.case_id].model_dump(mode="json"), "human_review": r.model_dump(mode="json")}
        for r in latest.values()])
    _, observations = load_dataset(args.run.parents[1])
    holdout = read_jsonl(args.run / "holdout_cases.jsonl", ReplayCase)
    queue = [json.loads(line) for line in (args.run / "review_queue.jsonl").read_text(encoding="utf-8").splitlines()]
    write_json(args.run / "summary.json", report(observations, cases + holdout, queue, saved))
    print(f"Appended {len(reviews)} human reviews; original cases unchanged.")


if __name__ == "__main__":
    main()
