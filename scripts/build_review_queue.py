"""Create an offline human-review batch; never includes holdout."""
import argparse
from pathlib import Path
from src.evaluation.models import ReplayCase, HumanReview
from src.evaluation.store import read_jsonl, write_jsonl, write_json, load_dataset
from src.evaluation.metrics import report
from src.evaluation.triage import build_review_queue


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--size", type=int, default=30)
    args = parser.parse_args()
    path = args.run / "review_queue.jsonl"
    if path.exists():
        raise SystemExit("Review queue exists; preserve the current batch.")
    cases = read_jsonl(args.run / "replay_cases.jsonl", ReplayCase)
    queue = build_review_queue(cases, args.size)
    write_jsonl(path, queue)
    write_jsonl(args.run / "human_reviews.jsonl", []) if not (args.run / "human_reviews.jsonl").exists() else None
    write_json(args.run / "review_instructions.json", {
        "verdict": ["approve", "reject", "modify", "uncertain"],
        "attention_level": {"0": "ignore", "1": "low", "2": "material", "3": "critical"},
        "instruction": "Supply HumanReview records in a separate JSONL file, then use scripts.import_human_reviews. Do not edit original cases.",
        "queue_size": len(queue), "human_labels_fabricated": False})
    _, observations = load_dataset(args.run.parents[1])
    holdout = read_jsonl(args.run / "holdout_cases.jsonl", ReplayCase)
    reviews = read_jsonl(args.run / "human_reviews.jsonl", HumanReview)
    write_json(args.run / "summary.json", report(observations, cases + holdout, queue, reviews))
    print(f"Review queue: {len(queue)} cases at {path}")


if __name__ == "__main__":
    main()
