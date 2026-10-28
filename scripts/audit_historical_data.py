"""Audit real provider coverage and persist the exact audited observations locally."""
import argparse
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from src.evaluation.acquisition import collect, VN
from src.evaluation.store import ROOT, save_dataset, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tickers", nargs="+")
    parser.add_argument("--start", type=date.fromisoformat, default=date(2000,1,1), help="Configurable source discovery lower bound")
    parser.add_argument("--end", type=date.fromisoformat, default=datetime.now(VN).date() - timedelta(days=1))
    parser.add_argument("--benchmark", default="VN30")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    manifest, observations = collect(args.tickers, args.start, args.end, args.benchmark or None)
    directory = save_dataset(args.root, observations, manifest)
    write_json(directory / "audit.json", manifest.model_dump(mode="json"))
    print(json.dumps({"dataset_directory": str(directory), **manifest.model_dump(mode="json")}, indent=2))
    if any(not manifest.coverage["tickers"][t]["sessions"] for t in manifest.tickers):
        raise SystemExit("Incomplete audit: at least one ticker has no market observations; inspect errors.")


if __name__ == "__main__":
    main()
