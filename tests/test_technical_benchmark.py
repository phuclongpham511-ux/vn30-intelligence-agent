"""Synthetic-only tests at the offline benchmark's public boundaries."""
from datetime import date, timedelta

import pytest


def history(values):
    return [{"session": (date(2020, 1, 1) + timedelta(days=i)).isoformat(),
             "value": value, "comparable": True} for i, value in enumerate(values)]


@pytest.mark.parametrize("value,status,direction", [(57, "EXISTS", "up"),
                         (-57, "EXISTS", "down"), (56, "DOES_NOT_EXIST", "up")])
def test_d1_nearest_rank_equality_and_signed_price(value, status, direction):
    from src.evaluation.benchmark.facts import factual_inputs
    result = factual_inputs("abnormal_price_move", "2021-01-01", value, history(range(1, 61)))
    assert (result["q95"], result["order_index"], result["predicate_result"], result["direction"]) == (
        57, 57, status, direction)


@pytest.mark.parametrize("n,status", [(59, "UNRESOLVED"), (60, "EXISTS")])
def test_d1_minimum_and_current_exclusion(n, status):
    from src.evaluation.benchmark.facts import factual_inputs
    rows = history([10] * n) + [{"session": "2021-01-01", "value": 99999, "comparable": True}]
    result = factual_inputs("unusual_volume", "2021-01-01", 10, rows)
    assert result["n"] == n
    assert result["predicate_result"] == status


def test_d1_last_252_valid_priors_not_last_252_rows():
    from src.evaluation.benchmark.facts import factual_inputs
    rows = history([999] * 20 + [10] * 252 + [None] * 5)
    result = factual_inputs("unusual_volume", "2021-01-01", 10, rows)
    assert (result["n"], result["q95"], result["predicate_result"]) == (252, 10, "EXISTS")
    assert len(result["excluded"]) == 5


@pytest.mark.parametrize("value,comparable,status", [(1, True, "DOES_NOT_EXIST"),
                         (None, True, "UNRESOLVED"), (100, False, "UNRESOLVED")])
def test_volume_high_only_and_invalid_evidence(value, comparable, status):
    from src.evaluation.benchmark.facts import factual_inputs
    result = factual_inputs("unusual_volume", "2021-01-01", value,
                            history([10] * 60), comparable=comparable)
    assert result["predicate_result"] == status


@pytest.mark.parametrize("family,direction", [("abnormal_price_move", "up"), ("unusual_volume", "HIGH")])
def test_episode_continuation_close_reentry_without_fixed_day_gap(family, direction):
    from src.evaluation.benchmark.episodes import link_episodes
    rows = [{"session": day, "predicate_result": result, "direction": direction,
             "continuous": True} for day, result in [("2020-01-01", "EXISTS"),
             ("2020-01-07", "EXISTS"), ("2020-01-08", "DOES_NOT_EXIST"), ("2020-01-09", "EXISTS")]]
    links = link_episodes("fixture-stock", family, rows)
    assert [r["lifecycle"] for r in links] == ["ANCHOR", "CONTINUATION", "CLOSED", "ANCHOR"]
    assert links[0]["episode_id"] == links[1]["episode_id"] == links[2]["episode_id"]
    assert links[3]["episode_id"] != links[0]["episode_id"]


def test_price_reversal_closes_previous_episode():
    from src.evaluation.benchmark.episodes import link_episodes
    rows = [{"session": f"2020-01-0{i}", "predicate_result": "EXISTS", "direction": direction,
             "continuous": True} for i, direction in enumerate(["up", "down"], 1)]
    a, b = link_episodes("fixture-stock", "abnormal_price_move", rows)
    assert b["closed_episode_id"] == a["episode_id"]
    assert b["episode_id"] != a["episode_id"]


@pytest.mark.parametrize("family,values,expected", [
    ("ma_cross", [-1, 1, 2, -1], ["ANCHOR", "CONTINUATION", "ANCHOR"]),
    ("rsi_regime_entry", [69, 71, 75, 70, 72], ["ANCHOR", "CONTINUATION", "CLOSED", "ANCHOR"]),
    ("rsi_regime_entry", [31, 29, 25, 30, 28], ["ANCHOR", "CONTINUATION", "CLOSED", "ANCHOR"]),
])
def test_regime_continuity_is_not_a_new_transition(family, values, expected):
    from src.evaluation.benchmark.facts import transition_inputs
    from src.evaluation.benchmark.episodes import link_episodes
    rows = [{"session": f"2020-01-0{i}", "continuous": True,
             **transition_inputs(family, before, after)}
            for i, (before, after) in enumerate(zip(values, values[1:]), 1)]
    links = link_episodes("fixture-stock", family, rows)
    assert [r["lifecycle"] for r in links] == expected
    assert rows[1]["predicate_result"] == "DOES_NOT_EXIST"
    assert links[0]["episode_id"] == links[1]["episode_id"]
    assert links[-1]["episode_id"] != links[0]["episode_id"]


def test_missing_episode_continuity_is_not_bridged_or_closed():
    from src.evaluation.benchmark.episodes import link_episodes
    rows = [{"session": f"2020-01-0{i}", "predicate_result": result, "direction": "up",
             "continuous": continuous} for i, (result, continuous) in enumerate(
                 [("EXISTS", True), ("UNRESOLVED", False), ("EXISTS", True)], 1)]
    links = link_episodes("fixture-stock", "abnormal_price_move", rows)
    assert links[1]["lifecycle"] == links[2]["lifecycle"] == "UNRESOLVED"
    assert links[2]["episode_id"] is None
    assert links[1]["closed_episode_id"] is None


@pytest.mark.parametrize("change", [{"start": "2025-01-01", "end": "2025-01-02"},
                                  {"source": "other"}, {"path": "unapproved.json"}])
def test_unauthorized_input_rejected_before_opening(tmp_path, monkeypatch, change):
    from pathlib import Path
    from src.evaluation.benchmark.inputs import InputPermit, load_authorized
    permit = InputPermit(path=str(tmp_path / "safe.json"), start="2020-01-01", end="2020-12-31",
                         source="synthetic", version="v1", sha256="0" * 64,
                         instruments=("SYN",), certifications={}, is_fixture=True)
    args = {"path": permit.path, "start": "2020-01-01", "end": "2020-12-31", "source": "synthetic", **change}
    def forbidden_read(*args, **kwargs):
        pytest.fail("Unauthorized file was opened")
    monkeypatch.setattr(Path, "read_bytes", forbidden_read)
    with pytest.raises(PermissionError):
        load_authorized(permit=permit, **args)


def test_official_preflight_fails_closed_without_certificates():
    from src.evaluation.benchmark.inputs import preflight
    result = preflight(None)
    assert result["status"] == "BLOCKED_BY_DATA_OR_PROVENANCE"
    assert set(result["blockers"]) == {"safe_input_allowlist", "historical_vn30_membership",
        "corporate_action_comparability", "source_version_provenance", "exchange_calendar",
        "protected_data_exclusion"}


def synthetic_snapshot(n=85):
    sessions, day = [], date(2020, 1, 1)
    while len(sessions) < n:
        if day.weekday() < 5:
            sessions.append(day.isoformat())
        day += timedelta(days=1)
    bars = []
    for i, session in enumerate(sessions):
        for ticker, close in [("SYN", 100 * 1.001 ** i), ("VN30", 1000 + i)]:
            bars.append({"ticker": ticker, "session": session, "open": close, "high": close,
                         "low": close, "close": close, "volume": 100 + i % 11 * 5,
                         "price_comparable": True, "volume_comparable": True,
                         "availability_basis": "end_of_day_assumption", "available_at": None,
                         "source": "synthetic", "currency": "VND", "downloaded_at": None})
    return {"is_fixture": True, "calendar": sessions, "bars": bars,
            "membership": [{"ticker": "SYN", "instrument": "synthetic-instrument",
                            "exchange": "SYNTHETIC", "start": sessions[0], "end": None,
                            "available_at": sessions[0] + "T00:00:00+07:00",
                            "source": "synthetic-universe", "version": "v1"}],
            "provenance": {"source": "synthetic", "version": "v1", "logical_snapshot": "fixture-v1",
                           "calendar_version": "synthetic-weekday-v1", "adjustment_semantics": "synthetic-no-actions",
                           "comparability_evidence": "synthetic-construction", "exclusion_version": "synthetic-no-real-cases"}}


def test_builder_has_four_independent_opportunities_and_no_human_labels():
    from src.evaluation.benchmark.builder import build_group
    snapshot = synthetic_snapshot()
    result = build_group(snapshot, "SYN", snapshot["calendar"][-1])
    assert {o["family"] for o in result["opportunities"]} == {
        "abnormal_price_move", "unusual_volume", "ma_cross", "rsi_regime_entry"}
    assert all(o["existence"] == "unannotated" for o in result["opportunities"])
    assert result["group"]["reference_complete"] is False
    assert result["group"]["expected_response_state"] is None
    assert result["group"]["prior_exposure_mode"] == "CONTROLLED_AS_IF_EMPTY"
    assert result["group"]["required_delivery"] == "NO"
    assert result["evidence"]["current"]["timestamp_assurance"] == "ASSUMED"


def test_missing_market_does_not_invalidate_price_predicate_or_fill_future():
    from src.evaluation.benchmark.builder import build_group
    snapshot = synthetic_snapshot(90)
    session = snapshot["calendar"][84]
    snapshot["bars"] = [r for r in snapshot["bars"] if not (r["ticker"] == "VN30" and r["session"] == session)]
    result = build_group(snapshot, "SYN", session)
    assert result["evidence"]["benchmark"]["return"] is None
    assert result["evidence"]["benchmark"]["excess_return"] is None
    assert result["evidence"]["facts"]["abnormal_price_move"]["predicate_result"] != "UNRESOLVED"


def test_market_uses_exact_same_interval_endpoints():
    from src.evaluation.benchmark.builder import build_group
    snapshot = synthetic_snapshot()
    for row in snapshot["bars"]:
        if row["ticker"] == "VN30" and row["session"] in snapshot["calendar"][-2:]:
            close = 1000 if row["session"] == snapshot["calendar"][-2] else 1100
            row.update({k: close for k in ("open", "high", "low", "close")})
    result = build_group(snapshot, "SYN", snapshot["calendar"][-1])
    market = result["evidence"]["benchmark"]
    assert market["return"] == pytest.approx(.1)
    assert market["excess_return"] == pytest.approx(-.099)
    assert market["start"] == snapshot["calendar"][-2]


def test_full_prefix_invariance_and_input_order_independence():
    from copy import deepcopy
    from src.evaluation.benchmark.builder import build_group
    from src.evaluation.store import canonical
    full = synthetic_snapshot(95)
    day = full["calendar"][84]
    truncated = deepcopy(full)
    truncated["calendar"] = [d for d in full["calendar"] if d <= day]
    truncated["bars"] = [r for r in full["bars"] if r["session"] <= day]
    expected = canonical(build_group(truncated, "SYN", day))
    assert canonical(build_group(full, "SYN", day)) == expected
    full["bars"].reverse()
    full["calendar"].reverse()
    assert canonical(build_group(full, "SYN", day)) == expected


def test_late_available_and_noncomparable_evidence_stays_unresolved():
    from src.evaluation.benchmark.builder import build_group
    snapshot = synthetic_snapshot()
    last = snapshot["calendar"][-1]
    row = next(r for r in snapshot["bars"] if r["ticker"] == "SYN" and r["session"] == last)
    row["price_comparable"] = False
    row["volume"] = None
    result = build_group(snapshot, "SYN", last)
    assert result["evidence"]["facts"]["abnormal_price_move"]["predicate_result"] == "UNRESOLVED"
    assert result["evidence"]["facts"]["unusual_volume"]["predicate_result"] == "UNRESOLVED"
    row["available_at"] = last + "T23:59:59-05:00"
    result = build_group(snapshot, "SYN", last)
    assert result["evidence"]["current"] is None
    assert result["group"]["data_state"] == "TECHNICAL_DATA_UNAVAILABLE_OR_INCOMPLETE"


def test_missing_membership_and_real_unverified_inputs_are_rejected():
    from src.evaluation.benchmark.builder import build_group
    snapshot = synthetic_snapshot()
    snapshot["membership"] = []
    with pytest.raises(PermissionError, match="membership"):
        build_group(snapshot, "SYN", snapshot["calendar"][-1])
    snapshot = synthetic_snapshot()
    snapshot["is_fixture"] = False
    with pytest.raises(PermissionError, match="certif"):
        build_group(snapshot, "SYN", snapshot["calendar"][-1])


def test_sampling_order_seed_and_component_are_reproducible():
    from src.evaluation.benchmark.sampling import sample_frame, reviewer_subset
    frame = [{"group_id": str(i), "evidence_tags": ["quality"] if i % 2 else [], "is_fixture": True} for i in range(10)]
    a = sample_frame(frame, 4, seed="fixture-seed", frame_version="fixture-frame-v1", component="REPRESENTATIVE")
    b = sample_frame(list(reversed(frame)), 4, seed="fixture-seed", frame_version="fixture-frame-v1", component="REPRESENTATIVE")
    assert a == b and len({r["group_id"] for r in a}) == 4
    assert all(r["sampling_component"] == "REPRESENTATIVE" for r in a)
    enriched = sample_frame(frame, 2, seed="fixture-seed", frame_version="fixture-frame-v1", component="ENRICHED",
                            evidence_rule="quality")
    assert all("quality" in row["evidence_tags"] for row in enriched)
    assert len(reviewer_subset(frame, "fixture-reviewers", "fixture-frame-v1")) == 3
    with pytest.raises(ValueError):
        sample_frame(frame, 20, seed="fixture-seed", frame_version="fixture-frame-v1", component="REPRESENTATIVE")


def test_validation_quarantine_propagates_whole_connected_episode_groups():
    from src.evaluation.benchmark.sampling import quarantine_validation
    development = [{"group_id": "d", "episode_ids": ["e1"]}]
    validation = [{"group_id": "v1", "episode_ids": ["e1", "e2"]},
                  {"group_id": "v2", "episode_ids": ["e2"]},
                  {"group_id": "v3", "episode_ids": ["e3"], "boundary_unresolved": True},
                  {"group_id": "v4", "episode_ids": ["e4"]}]
    result = quarantine_validation(development, validation)
    assert [r["group_id"] for r in result["eligible"]] == ["v4"]
    assert {r["group_id"] for r in result["quarantined"]} == {"v1", "v2", "v3"}
    assert development == [{"group_id": "d", "episode_ids": ["e1"]}]


def test_smoke_package_deterministic_immutable_and_explicitly_not_benchmark(tmp_path):
    from src.evaluation.benchmark.builder import build_group
    from src.evaluation.benchmark.package import write_package
    snapshot = synthetic_snapshot()
    groups = [build_group(snapshot, "SYN", d) for d in snapshot["calendar"][-2:]]
    first = write_package(tmp_path / "first", groups, source_inventory={"fixture": "v1"})
    second = write_package(tmp_path / "second", list(reversed(groups)), source_inventory={"fixture": "v1"})
    assert first == second
    assert first["benchmark_status"] == "SMOKE_ONLY_NOT_BENCHMARK"
    assert first["counts"] == {"groups": 2, "opportunities": 8, "episode_links": 8}
    assert first["checks"]["referential_integrity"] == "PASS"
    assert first["checks"]["reference_complete"] == "NOT_RUN"
    for name in first["files"]:
        assert (tmp_path / "first" / name).read_bytes() == (tmp_path / "second" / name).read_bytes()
    assert (tmp_path / "first" / "annotations_raw.jsonl").read_bytes() == b""
    assert write_package(tmp_path / "first", groups, source_inventory={"fixture": "v1"}) == first
    (tmp_path / "first" / "evidence.jsonl").write_text("tampered")
    with pytest.raises(FileExistsError):
        write_package(tmp_path / "first", groups, source_inventory={"fixture": "v1"})


def test_complete_phase1_smoke_receipt_and_safe_resume(tmp_path):
    from scripts.build_technical_benchmark_smoke import run_phase1
    first = run_phase1(tmp_path)
    second = run_phase1(tmp_path)
    assert first == second
    assert first["prefix_invariance"] == first["deterministic_rebuild"] == "PASS"
    assert first["smoke_groups"] == 3
    assert first["preflight"]["status"] == "BLOCKED_BY_DATA_OR_PROVENANCE"
    assert first["official_generation"] is False
    assert first["governance_commit"] == "ceb944bab2e33e09a6d1586c31d1f8d8e271cde7"
    assert first["active_d2_authority"] == "docs/TECHNICAL_D2_DATA_FRAME_PIT_DECISION_V3.md"
    assert all("docs/" + name in first["governance_hashes"] for name in (
        "TECHNICAL_D2_DATA_FRAME_PIT_DECISION.md",
        "TECHNICAL_D2_DATA_FRAME_PIT_DECISION_V2.md",
        "TECHNICAL_D2_DATA_FRAME_PIT_DECISION_V3.md"))
    assert "docs/TECHNICAL_BENCHMARK_POPULATION_DIRECTION_REVIEW_V4.md" in first["governance_hashes"]


@pytest.mark.parametrize("name", [
    "TECHNICAL_D1_FACTUAL_ABNORMALITY_DECISION.md",
    "TECHNICAL_D2_DATA_FRAME_PIT_DECISION.md",
    "TECHNICAL_D2_DATA_FRAME_PIT_DECISION_V2.md",
    "TECHNICAL_D2_DATA_FRAME_PIT_DECISION_V3.md",
    "TECHNICAL_STOCK_DAY_BENCHMARK_SPEC.md",
    "TECHNICAL_BENCHMARK_POPULATION_DIRECTION_REVIEW_V4.md",
    "TECHNICAL_D2_DECISION_REVIEW_V2_TO_V3.md",
])
def test_governance_lineage_rejects_unauthorized_mutation(tmp_path, name):
    from scripts.build_technical_benchmark_smoke import ROOT, verify_governance
    hashes = verify_governance()
    for relative in hashes:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / relative).read_bytes())
    assert verify_governance(tmp_path) == hashes
    target = tmp_path / "docs" / name
    target.write_bytes(target.read_bytes() + b"\nUNAUTHORIZED POLICY EDIT\n")
    with pytest.raises(ValueError, match="Unauthorized governance mutation"):
        verify_governance(tmp_path)


def test_governance_lineage_missing_authority_fails(tmp_path):
    from scripts.build_technical_benchmark_smoke import verify_governance
    with pytest.raises(FileNotFoundError):
        verify_governance(tmp_path)


def test_safe_synthetic_loader_checks_hash_and_loads_no_unapproved_files(tmp_path):
    from hashlib import sha256
    from dataclasses import replace
    from src.evaluation.benchmark.inputs import InputPermit, load_authorized
    from src.evaluation.store import canonical
    snapshot = synthetic_snapshot()
    path = tmp_path / "synthetic.json"
    content = canonical(snapshot).encode()
    path.write_bytes(content)
    permit = InputPermit(str(path), snapshot["calendar"][0], snapshot["calendar"][-1],
                         "synthetic", "v1", sha256(content).hexdigest(), ("SYN", "VN30"), {}, True)
    args = dict(path=path, start=permit.start, end=permit.end, source=permit.source)
    assert load_authorized(permit=permit, **args) == snapshot
    with pytest.raises(ValueError, match="checksum"):
        load_authorized(permit=replace(permit, sha256="0" * 64), **args)


def test_missing_prior_session_never_becomes_a_multisession_daily_move():
    from src.evaluation.benchmark.builder import build_group
    snapshot = synthetic_snapshot()
    previous = snapshot["calendar"][-2]
    snapshot["bars"] = [r for r in snapshot["bars"] if not (r["ticker"] == "SYN" and r["session"] == previous)]
    result = build_group(snapshot, "SYN", snapshot["calendar"][-1])
    assert result["evidence"]["signed_return"] is None
    assert result["evidence"]["facts"]["ma_cross"]["predicate_result"] == "UNRESOLVED"
    assert all(e["lifecycle"] == "UNRESOLVED" for e in result["episode_links"])


def test_flat_price_equality_preserves_neutral_direction_and_no_fabricated_episode():
    from src.evaluation.benchmark.facts import factual_inputs
    from src.evaluation.benchmark.episodes import link_episodes
    fact = factual_inputs("abnormal_price_move", "2021-01-01", 0, history([0] * 60))
    assert (fact["predicate_result"], fact["direction"]) == ("EXISTS", "neutral")
    links = link_episodes("SYN", "abnormal_price_move", [{"session": "2021-01-01", "continuous": True, **fact}])
    assert links[0]["episode_id"] is None


def test_nonboolean_comparability_cannot_certify_d1_evidence():
    from src.evaluation.benchmark.facts import factual_inputs
    fact = factual_inputs("unusual_volume", "2021-01-01", 100, history([10] * 60), comparable="unknown")
    assert fact["predicate_result"] == "UNRESOLVED"


def test_builder_rejects_label_or_score_contamination_of_input_rows():
    from src.evaluation.benchmark.builder import build_group
    snapshot = synthetic_snapshot()
    snapshot["bars"][-2]["human_attention"] = 3
    with pytest.raises(ValueError, match="Unexpected.*fields"):
        build_group(snapshot, "SYN", snapshot["calendar"][-1])
