"""Immutable datasets and append-only human reviews, all under ignored data/."""
import hashlib
import json
from pathlib import Path
from src.evaluation.models import HistoricalObservation, DatasetManifest, ReplayCase, HumanReview

ROOT = Path(__file__).resolve().parents[2] / "data" / "evaluation"


def canonical(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False, default=str)


def digest(value) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False, default=str), encoding="utf-8")
    temporary.replace(path)


def write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text("".join(canonical(row.model_dump(mode="json") if hasattr(row, "model_dump") else row) + "\n" for row in rows), encoding="utf-8")
    temporary.replace(path)


def read_jsonl(path: Path, model):
    return [model.model_validate_json(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def validate_observations(rows):
    seen = set()
    for row in rows:
        key = (row.ticker, row.data_type, row.observation_time)
        if key in seen:
            raise ValueError(f"Duplicate observation: {key}")
        seen.add(key)
    return sorted(rows, key=lambda r: (r.ticker, r.data_type, r.observation_time))


def save_dataset(root: Path, rows, manifest: DatasetManifest):
    rows = validate_observations(rows)
    content = [r.model_dump(mode="json") for r in rows]
    if digest(content) != manifest.content_sha256 or len(rows) != manifest.observation_count:
        raise ValueError("Manifest does not match observations")
    directory = root / "datasets" / manifest.dataset_version
    if directory.exists():
        old, loaded = load_dataset(directory)
        if old != manifest or loaded != rows:
            raise ValueError("Refusing to replace an existing dataset version")
        return directory
    directory.mkdir(parents=True)
    write_jsonl(directory / "observations.jsonl", rows)
    write_json(directory / "manifest.json", manifest.model_dump(mode="json"))
    return directory


def load_dataset(directory: Path):
    manifest = DatasetManifest.model_validate_json((directory / "manifest.json").read_text(encoding="utf-8"))
    rows = validate_observations(read_jsonl(directory / "observations.jsonl", HistoricalObservation))
    if len(rows) != manifest.observation_count or digest([r.model_dump(mode="json") for r in rows]) != manifest.content_sha256:
        raise ValueError("Dataset integrity check failed")
    return manifest, rows


def save_reviews(path: Path, reviews: list[HumanReview], cases: list[ReplayCase]):
    indexed = {c.case_id: c for c in cases}
    old = read_jsonl(path, HumanReview) if path.exists() else []
    keys = {(r.case_id, r.review_version) for r in old}
    for review in reviews:
        case = indexed.get(review.case_id)
        if case is None or case.split == "holdout":
            raise ValueError("Unknown or protected holdout case")
        if (review.case_id, review.review_version) in keys:
            raise ValueError("Review version already exists; append a new version")
        keys.add((review.case_id, review.review_version))
    write_jsonl(path, old + reviews)
