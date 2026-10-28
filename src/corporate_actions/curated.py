"""Validated local notices; receipt time is assigned on import, never backfilled."""
from pathlib import Path
from typing import Literal
from .models import ActionModel, CorporateActionNotice


class CuratedDataset(ActionModel):
    dataset_version: str
    source_kind: Literal['curated_verified']
    limitations: tuple[str, ...]
    notices: tuple[CorporateActionNotice, ...]


def load_curated(path: Path) -> CuratedDataset:
    return CuratedDataset.model_validate_json(path.read_text(encoding='utf-8-sig'))


def ingest_curated(repository, dataset: CuratedDataset):
    counts = {'inserted': 0, 'duplicate': 0, 'revision': 0}
    # Normalized input has no observed_at field. No historical receipt-time option.
    for notice in dataset.notices:
        counts[repository.ingest(notice).status] += 1
    return counts
