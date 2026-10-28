"""Replay an audited local dataset. No network access."""
import argparse
from pathlib import Path
from src.evaluation.models import ReplayConfig
from src.evaluation.store import load_dataset, write_json, write_jsonl, digest
from src.evaluation.replay import replay
from src.evaluation.metrics import report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--config", required=True, type=Path)
    args = parser.parse_args()
    manifest, observations = load_dataset(args.dataset)
    config = ReplayConfig.model_validate_json(args.config.read_text(encoding="utf-8-sig"))
    run = args.dataset / "runs" / digest(config.model_dump(mode="json"))[:16]
    if run.exists():
        raise SystemExit("Run already exists; preserve outputs/labels. Use a new configuration for a new run.")
    cases = replay(observations, manifest, config)
    write_json(run / "config.json", config.model_dump(mode="json"))
    write_jsonl(run / "replay_cases.jsonl", [c for c in cases if c.split != "holdout"])
    write_jsonl(run / "holdout_cases.jsonl", [c for c in cases if c.split == "holdout"])
    write_jsonl(run / "excluded_observations.jsonl", [
        {"observation": o.model_dump(mode="json"), "reason":
         "fixture_nonmarket" if o.is_fixture and o.data_type in ("fundamental", "news") else
         "unknown_available_at" if o.available_at is None or o.availability_basis == "unknown" else
         "stream_not_enabled_v0"}
        for o in observations if o.data_type in ("fundamental", "news") or o.available_at is None or o.availability_basis == "unknown"])
    write_json(run / "summary.json", report(observations, cases))
    write_json(run / "run_manifest.json", {"dataset_version": manifest.dataset_version,
        "config_hash": digest(config.model_dump(mode="json")), "score_version": "v0", "context_version": config.context_version,
        "case_count": len(cases), "cases_hash": digest([c.model_dump(mode="json") for c in cases])})
    print(f"Replay complete: {len(cases)} cases; run={run}")


if __name__ == "__main__":
    main()
