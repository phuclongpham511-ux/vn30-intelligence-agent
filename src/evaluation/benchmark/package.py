"""Immutable canonical smoke package. No annotations, scoring, or official build."""
from hashlib import sha256
from pathlib import Path

from src.evaluation.store import canonical, digest
from .builder import BASELINE, VERSION
from .facts import FAMILIES


def write_package(directory, groups, *, source_inventory):
    if not groups or any(g["group"].get("benchmark_status") != "SMOKE_ONLY_NOT_BENCHMARK"
                         or g["group"].get("is_fixture") is not True for g in groups):
        raise PermissionError("Phase 1 writer accepts synthetic smoke only")
    groups = sorted(groups, key=lambda g: g["group"]["group_id"])
    if len({g["group"]["group_id"] for g in groups}) != len(groups):
        raise ValueError("Duplicate group IDs")
    for bundle in groups:
        group, evidence = bundle["group"], bundle["evidence"]
        if (group["evidence_sha256"] != digest(evidence) or evidence["group_id"] != group["group_id"]
                or evidence["packet_id"] != group["evidence_id"]):
            raise ValueError("Broken evidence hash/link")
        opportunities = bundle["opportunities"]
        if len(opportunities) != 4 or {o["family"] for o in opportunities} != set(FAMILIES):
            raise ValueError("Incomplete four-family inventory")
        ids = {o["opportunity_id"] for o in opportunities}
        if len(ids) != 4 or set(group["opportunity_ids"]) != ids:
            raise ValueError("Broken opportunity IDs")
        if len(bundle["episode_links"]) != 4:
            raise ValueError("Incomplete episode evidence")
        for row in opportunities + bundle["episode_links"]:
            if row["group_id"] != group["group_id"] or row["opportunity_id"] not in ids:
                raise ValueError("Broken opportunity/episode join")
    tables = {
        "groups.jsonl": [g["group"] for g in groups],
        "opportunities.jsonl": sorted([o for g in groups for o in g["opportunities"]], key=lambda o: o["opportunity_id"]),
        "evidence.jsonl": [g["evidence"] for g in groups],
        "episode_links.jsonl": sorted([e for g in groups for e in g["episode_links"]], key=lambda e: (e["group_id"], e["family"])),
        "annotations_raw.jsonl": [], "annotations_adjudicated.jsonl": [],
        "insights.jsonl": [], "candidates.jsonl": [],
        "delivery_obligations.jsonl": [
            {"group_id": g["group"]["group_id"], "policy": "D5-v1", "required_delivery": "NO",
             "reason": "approved_ordinary_technical_v1_policy", "benchmark_status": "SMOKE_ONLY_NOT_BENCHMARK"}
            for g in groups],
    }
    counts = {"groups": len(groups), "opportunities": len(groups) * 4, "episode_links": len(groups) * 4}
    checks = {"referential_integrity": "PASS", "four_family_inventory": "PASS",
              "reference_complete": "NOT_RUN", "candidate_capture": "NOT_RUN",
              "official_data_certification": "NOT_RUN", "split_isolation": "NOT_APPLICABLE_SMOKE",
              "human_annotations": "NOT_RUN", "prefix_invariance": "NOT_RUN_EXTERNAL_TEST",
              "deterministic_rebuild": "NOT_RUN_EXTERNAL_TEST"}
    files = {name: "".join(canonical(row) + "\n" for row in rows).encode("utf-8") for name, rows in tables.items()}
    integrity = {"counts": counts, "checks": checks, "denominator_groups": len(groups),
                 "affected_ids": [g["group"]["group_id"] for g in groups],
                 "evidence_complete_groups": sum(g["group"]["evidence_complete"] for g in groups),
                 "reference_complete_groups": 0, "inventory_complete_groups": 0,
                 "limitation": "Synthetic construction only; no detector capture or human reference adjudication"}
    files["integrity.json"] = (canonical(integrity) + "\n").encode()
    files["source_inventory.json"] = (canonical(source_inventory) + "\n").encode()
    manifest = {"schema_version": "1", "build_version": VERSION, "governance_commit": BASELINE,
                "benchmark_status": "SMOKE_ONLY_NOT_BENCHMARK", "is_fixture": True,
                "serialization": "UTF-8 canonical sorted JSON keys, compact separators, LF, no NaN",
                "counts": counts, "checks": checks,
                "files": {name: sha256(content).hexdigest() for name, content in sorted(files.items())},
                "annotation_status": "UNANNOTATED", "official_sample_membership": False}
    files["run_manifest.json"] = (canonical(manifest) + "\n").encode()
    directory = Path(directory)
    # Validate existing expected files before any mutation; resume only identical bytes.
    for name, content in files.items():
        target = directory / name
        if target.exists() and target.read_bytes() != content:
            raise FileExistsError(f"Immutable package conflict: {target}")
    directory.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        target = directory / name
        if not target.exists():
            with target.open("xb") as stream:
                stream.write(content)
    return manifest
