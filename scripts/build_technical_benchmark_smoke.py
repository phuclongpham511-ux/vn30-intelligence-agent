"""Phase 1 synthetic-only build. No real-data loader, official sampler or scoring CLI."""
import argparse
from copy import deepcopy
from datetime import date, timedelta
from hashlib import sha256
import json
from pathlib import Path
import subprocess

from src.evaluation.benchmark.builder import BASELINE, build_group
from src.evaluation.benchmark.inputs import InputPermit, load_authorized, preflight
from src.evaluation.benchmark.package import write_package
from src.evaluation.store import canonical, digest, write_json

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data/evaluation/technical_benchmark_v1_phase1"
GOVERNANCE = [
    "TECHNICAL_D1_FACTUAL_ABNORMALITY_DECISION.md", "TECHNICAL_D2_DATA_FRAME_PIT_DECISION.md",
    "TECHNICAL_D3_MONITORING_CONTEXT_DECISION.md", "TECHNICAL_D4_EPISODE_POLICY_DECISION.md",
    "TECHNICAL_D5_DELIVERY_POLICY_DECISION.md", "TECHNICAL_D6_STUDY_REVIEWER_DECISION.md",
    "TECHNICAL_DECISION_REVIEW_PROTOCOL.md", "TECHNICAL_STOCK_DAY_BENCHMARK_SPEC.md",
    "TECHNICAL_ANNOTATION_HANDBOOK_V1.md", "TECHNICAL_STOCK_DAY_DESIGN_AUDIT.md",
]
D2_V2_COMMIT = "91232b00a3c9e9b124f5570c449254bf22e2de04"
ACTIVE_D2 = "docs/TECHNICAL_D2_DATA_FRAME_PIT_DECISION_V3.md"
# Owner-authorized Step A / A.1 document contents, pinned independently of HEAD.
# A future authorized revision must update these pins explicitly; no auto-freeze.
AUTHORIZED_STEP_A = {
    "TECHNICAL_D6_STUDY_REVIEWER_DECISION.md": "7bf125d40ddf8cd145994d4e0ed43676db8b4953b542f0059591636ed147db0e",
    "TECHNICAL_STOCK_DAY_BENCHMARK_SPEC.md": "4dfefea6c6503f33b13b5e6a49f938dcfdc5abe514897a5028a0ec885f96f7f7",
    "TECHNICAL_D2_DATA_FRAME_PIT_DECISION_V3.md": "e9a2905106a141b2b604e202c50836f669d35251853f727168abb8c931893b3c",
    "TECHNICAL_D2_DECISION_REVIEW_V2_TO_V3.md": "cbb2bdb9790c971db6f165505fd759d487868e405471daa860788750b9afd228",
    "TECHNICAL_BENCHMARK_POPULATION_DIRECTION_REVIEW_V4.md": "d03e5549a482a21b04047dcb3f332a43a862f17a59bc775a067dcef7913d92b5",
}


def verify_governance(document_root=ROOT):
    """Fail closed against explicit authorities; HEAD ancestry is not approval.

    Compare Git-normalized text so Windows CRLF checkout is not a policy edit.
    Receipts still record raw working-file hashes for exact resume integrity.
    """
    for commit in (BASELINE, D2_V2_COMMIT):
        subprocess.run(["git", "merge-base", "--is-ancestor", commit, "HEAD"], cwd=ROOT, check=True)
    versions = ["TECHNICAL_D2_DATA_FRAME_PIT_DECISION_V2.md", "TECHNICAL_D2_DECISION_REVIEW_V1_TO_V2.md"]
    paths = list(dict.fromkeys(GOVERNANCE + versions + list(AUTHORIZED_STEP_A)))
    hashes = {}
    for name in paths:
        path = "docs/" + name
        expected = AUTHORIZED_STEP_A.get(name)
        if expected is None:
            commit = D2_V2_COMMIT if name in versions or name in {
                "TECHNICAL_ANNOTATION_HANDBOOK_V1.md", "TECHNICAL_STOCK_DAY_DESIGN_AUDIT.md"
            } else BASELINE
            content = subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=ROOT)
            expected = sha256(content.replace(b"\r\n", b"\n")).hexdigest()
        content = (Path(document_root) / path).read_bytes()
        if sha256(content.replace(b"\r\n", b"\n")).hexdigest() != expected:
            raise ValueError("Unauthorized governance mutation: " + path)
        hashes[path] = sha256(content).hexdigest()
    return hashes


def synthetic_snapshot():
    """Explicit fixture universe/calendar/actions; never evidence about real securities."""
    sessions, day = [], date(2020, 1, 1)
    while len(sessions) < 100:
        if day.weekday() < 5:
            sessions.append(day.isoformat())
        day += timedelta(days=1)
    bars, close = [], 100.0
    for i, session in enumerate(sessions):
        close *= 1 + (.05 if i in (78, 79, 80) else -.03 if i == 81 else .002 if i % 3 else -.001)
        for ticker, value in (("SYN_A", close), ("VN30", 1000 + i)):
            bars.append({"ticker": ticker, "session": session, "open": value, "high": value,
                         "low": value, "close": value, "volume": 800 if i in (78, 79) else 100 + i % 13 * 10,
                         "price_comparable": True, "volume_comparable": True,
                         "availability_basis": "end_of_day_assumption", "available_at": None,
                         "source": "synthetic", "currency": "VND", "downloaded_at": None})
    return {"is_fixture": True, "calendar": sessions, "bars": bars,
            "membership": [{"ticker": "SYN_A", "instrument": "synthetic-stock-a", "exchange": "SYNTHETIC",
                            "start": sessions[0], "end": None, "available_at": sessions[0] + "T00:00:00+07:00",
                            "source": "synthetic-membership", "version": "v1"}],
            "provenance": {"source": "synthetic", "version": "smoke-v1", "logical_snapshot": "synthetic-smoke-v1",
                           "calendar_version": "fixture-weekdays-v1", "adjustment_semantics": "synthetic-no-actions",
                           "comparability_evidence": "known_fixture_construction", "exclusion_version": "synthetic-no-real-records"}}


def _immutable(path, content):
    if path.exists():
        if path.read_bytes() != content:
            raise FileExistsError(f"Immutable artifact differs: {path}; use a new versioned output directory")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(content)


def run_phase1(output=OUTPUT):
    output = Path(output).resolve()
    governance_hashes = verify_governance()
    code_paths = ["src/evaluation/benchmark/" + name + ".py" for name in (
        "__init__", "facts", "episodes", "inputs", "builder", "sampling", "package", "population")]
    code_paths += ["scripts/build_technical_benchmark_smoke.py", "src/analytics/market.py", "src/evaluation/store.py"]
    code_hashes = {p: sha256((ROOT / p).read_bytes()).hexdigest() for p in code_paths}
    receipt_path = output / "phase1_receipt.json"
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        if receipt["code_hashes"] != code_hashes or receipt["governance_hashes"] != governance_hashes:
            raise ValueError("Frozen smoke inputs changed; create a new versioned output, do not overwrite")
        for relative, expected in receipt["artifact_hashes"].items():
            if sha256((output / relative).read_bytes()).hexdigest() != expected:
                raise ValueError("Completed artifact failed resume integrity check: " + relative)
        return receipt
    completed = []
    def checkpoint(phase):
        completed.append(phase)
        write_json(output / "status.json", {"governance_commit": BASELINE, "completed": completed,
                   "active_d2_authority": ACTIVE_D2, "d2_v2_governance_commit": D2_V2_COMMIT,
                   "phase": phase, "official_generation": False, "data_access": "SYNTHETIC_ONLY",
                   "code_hashes": code_hashes, "governance_hashes": governance_hashes})
    checkpoint("BASELINE_VERIFIED")
    snapshot = synthetic_snapshot()
    raw = (canonical(snapshot) + "\n").encode()
    raw_path = output / "synthetic_input.json"
    _immutable(raw_path, raw)
    permit = InputPermit(str(raw_path), snapshot["calendar"][0], snapshot["calendar"][-1],
                         "synthetic", "smoke-v1", sha256(raw).hexdigest(), ("SYN_A", "VN30"), {}, True)
    snapshot = load_authorized(raw_path, permit=permit, start=permit.start, end=permit.end, source=permit.source)
    checkpoint("SYNTHETIC_ALLOWLIST_AND_CHECKSUM_VERIFIED")
    days = snapshot["calendar"][78:81]
    groups = [build_group(snapshot, "SYN_A", day) for day in days]
    # Persist constructed outputs before the independent prefix comparison.
    inventory = {"is_fixture": True, "input_sha256": sha256(raw).hexdigest(),
                 "governance_hashes": governance_hashes, "code_hashes": code_hashes,
                 "logical_snapshot": snapshot["provenance"]["logical_snapshot"]}
    first = write_package(output / "smoke", groups, source_inventory=inventory)
    checkpoint("SMOKE_PACKAGE_WRITTEN")
    prefix_checks = []
    for day, full_group in zip(days, groups):
        prefix = deepcopy(snapshot)
        prefix["calendar"] = [d for d in prefix["calendar"] if d <= day]
        prefix["bars"] = [r for r in prefix["bars"] if r["session"] <= day]
        truncated = build_group(prefix, "SYN_A", day)
        if canonical(truncated) != canonical(full_group):
            raise AssertionError("PIT/prefix invariance failed")
        prefix_checks.append({"session": day, "full_sha256": digest(full_group),
                              "prefix_sha256": digest(truncated), "result": "PASS"})
    _immutable(output / "prefix_checks.json", (canonical(prefix_checks) + "\n").encode())
    checkpoint("PREFIX_INVARIANCE_PASSED")
    shuffled = deepcopy(snapshot)
    shuffled["bars"].reverse()
    rebuilt = [build_group(shuffled, "SYN_A", day) for day in reversed(days)]
    second = write_package(output / "rebuild", rebuilt, source_inventory=inventory)
    if first != second:
        raise AssertionError("Rebuild manifest mismatch")
    checkpoint("DETERMINISTIC_REBUILD_PASSED")
    # No official permit/custodian certificate was supplied. Never scan legacy data
    # or protected manifests to try to manufacture the missing certification.
    result = preflight(None)
    result["blocker_details"] = {
        "safe_input_allowlist": "No certified real-source snapshot/path/date/instrument/hash allowlist supplied",
        "historical_vn30_membership": "No verified as-of historical membership evidence supplied",
        "corporate_action_comparability": "No verified PIT price/volume adjustment and comparability evidence supplied",
        "source_version_provenance": "No certified real provider/version/logical snapshot and raw checksums supplied",
        "exchange_calendar": "No certified historical exchange calendar/session-state source supplied",
        "protected_data_exclusion": "No custodian-certified exclusion/freshness metadata supplied for closed V1/V2 and reviewed V3",
    }
    result["implementation_limitations"] = ["Real-data certificate verification adapter remains disabled",
        "Candidate capture and human reference construction are not run; inventory/reference completeness is not claimed",
        "Known late or unknown publication is excluded rather than replaying source revisions"]
    _immutable(output / "preflight.json", (canonical(result) + "\n").encode())
    artifacts = ["synthetic_input.json", "prefix_checks.json", "preflight.json"]
    for folder in ("smoke", "rebuild"):
        artifacts.extend(folder + "/" + name for name in [*first["files"], "run_manifest.json"])
    receipt = {"governance_commit": BASELINE, "governance_hashes": governance_hashes, "code_hashes": code_hashes,
               "active_d2_authority": ACTIVE_D2, "d2_v2_governance_commit": D2_V2_COMMIT,
               "benchmark_status": "SMOKE_ONLY_NOT_BENCHMARK", "smoke_groups": len(groups),
               "prefix_invariance": "PASS", "deterministic_rebuild": "PASS", "official_generation": False,
               "preflight": result, "tests": "See separate pytest results; not inferred from smoke success",
               "artifact_hashes": {p: sha256((output / p).read_bytes()).hexdigest() for p in artifacts}}
    _immutable(receipt_path, (canonical(receipt) + "\n").encode())
    checkpoint("PHASE1_COMPLETE_BLOCKED_BY_DATA_OR_PROVENANCE")
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    receipt = run_phase1(args.output)
    print(canonical({"smoke_groups": receipt["smoke_groups"], "prefix_invariance": receipt["prefix_invariance"],
                     "deterministic_rebuild": receipt["deterministic_rebuild"], "preflight": receipt["preflight"]["status"]}))
