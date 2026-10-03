"""Metadata-only D2 contracts; every certificate and identity here is synthetic."""
from copy import deepcopy

import pytest


def certified_metadata():
    scope = {"source": "synthetic-provider", "source_version": "fixture-v1",
             "snapshot_id": "synthetic-snapshot-v1", "authorized_path": "C:/approved/fixture.json",
             "instruments": [{"instrument_id": "fixture-id", "ticker": "SYN"}],
             "start": "2020-01-01", "end": "2020-12-31", "exchange": "SYNTHETIC"}
    certificate = {"status": "CERTIFIED", "issuer": "synthetic-custodian",
                   "version": "fixture-cert-v1", "evidence_reference": "fixture:certificate",
                   "scope": scope, "normalized_sha256": "a" * 64, "reasons": []}
    return {
        "manifest": {"schema_version": "d2-admission-v1", "scope": scope,
                     "source_classification": "SAFE_TO_INSPECT", "certification_status": "CERTIFIED",
                     "certification_reasons": [], "availability_policy_version": "d2-eod-availability-v1",
                     "protected_ledger_version": "synthetic-ledger-v1",
                     "acquisition": {"status": "CERTIFIED", "value": "2021-01-01T01:00:00+00:00"},
                     "raw_hash": {"status": "CERTIFIED", "snapshot_id": "synthetic-snapshot-v1", "sha256": "b" * 64},
                     "normalized_hash": {"status": "CERTIFIED", "snapshot_id": "synthetic-snapshot-v1", "sha256": "a" * 64},
                     "certificates": {name: deepcopy(certificate) for name in
                                      ("historical_universe", "comparability", "provenance", "exchange_calendar")}},
        "request": {"path": "C:/approved/fixture.json", "start": "2020-03-01", "end": "2020-03-02",
                    "instruments": [{"instrument_id": "fixture-id", "ticker": "SYN"}],
                    "source": "synthetic-provider", "source_version": "fixture-v1",
                    "snapshot_id": "synthetic-snapshot-v1", "payload_kind": "normalized", "sha256": "a" * 64},
        "ledger": {"schema_version": "d2-exclusions-v1", "version": "synthetic-ledger-v1",
                   "scope": scope, "completeness": "COMPLETE", "issuer": "synthetic-custodian",
                   "provenance": "fixture:complete-exclusions", "records": [],
                   "coverage": [{"study_id": study, "completeness": "COMPLETE", "provenance": "fixture:" + study}
                                for study in ("validation-v1", "validation-v2", "development-v3")]},
    }


def test_certified_metadata_passes_without_reading_files(monkeypatch):
    from pathlib import Path
    from src.evaluation.benchmark.admission import validate_real_data_admission
    def forbidden(*args, **kwargs):
        pytest.fail("Metadata gate attempted filesystem access")
    for name in ("open", "read_bytes", "read_text", "stat", "resolve"):
        monkeypatch.setattr(Path, name, forbidden)
    result = validate_real_data_admission(certified_metadata())
    assert result == {"decision": "PASS", "reasons": [], "payload_loaded": False,
                      "real_loader_enabled": False, "scope": "DECLARED_METADATA_ONLY"}


@pytest.mark.parametrize("certificate,reason", [
    ("historical_universe", "B2_HISTORICAL_UNIVERSE_NOT_CERTIFIED"),
    ("comparability", "B3_COMPARABILITY_NOT_CERTIFIED"),
    ("provenance", "B4_PROVENANCE_NOT_CERTIFIED"),
    ("exchange_calendar", "B5_CALENDAR_NOT_CERTIFIED"),
])
@pytest.mark.parametrize("state", [None, "MISSING", "UNVERIFIED", "NOT_APPLICABLE"])
def test_mandatory_certificate_never_downgrades_to_warning(certificate, reason, state):
    from src.evaluation.benchmark.admission import validate_real_data_admission
    metadata = certified_metadata()
    metadata["manifest"]["certificates"][certificate] = None if state is None else {"status": state}
    result = validate_real_data_admission(metadata)
    assert result["decision"] == "BLOCKED"
    assert reason in result["reasons"]


def test_empty_or_malformed_metadata_is_blocked():
    from src.evaluation.benchmark.admission import validate_real_data_admission
    assert validate_real_data_admission({})["decision"] == "BLOCKED"
    assert validate_real_data_admission(None)["decision"] == "BLOCKED"


@pytest.mark.parametrize("section,key,value,reason", [
    ("request", "path", "C:/other/fixture.json", "B1_UNAUTHORIZED_PATH"),
    ("request", "path", "C:/approved/../approved/fixture.json", "B1_UNAUTHORIZED_PATH"),
    ("request", "start", "2019-12-31", "B1_UNAUTHORIZED_DATE_RANGE"),
    ("request", "end", "2025-01-01", "B1_UNAUTHORIZED_DATE_RANGE"),
    ("request", "end", "2020-01-01", "B1_UNAUTHORIZED_DATE_RANGE"),
    ("request", "instruments", [{"instrument_id": "fixture-id", "ticker": "OTHER"}], "B1_UNAUTHORIZED_INSTRUMENT"),
    ("request", "source", "different-provider", "B4_SOURCE_IDENTITY_MISMATCH"),
    ("request", "source_version", "different-version", "B4_SOURCE_IDENTITY_MISMATCH"),
    ("request", "snapshot_id", "different-snapshot", "B4_SNAPSHOT_HASH_MISMATCH"),
    ("request", "sha256", "c" * 64, "B4_SNAPSHOT_HASH_MISMATCH"),
    ("manifest", "source_classification", "UNKNOWN", "B1_SOURCE_NOT_SAFE"),
    ("manifest", "source_classification", "PROTECTED_OR_POSSIBLY_PROTECTED", "B1_SOURCE_NOT_SAFE"),
    ("manifest", "certification_status", "UNVERIFIED", "B1_MANIFEST_NOT_CERTIFIED"),
    ("manifest", "availability_policy_version", None, "D2_PIT_POLICY_NOT_CERTIFIED"),
    ("ledger", "completeness", "INCOMPLETE", "B6_LEDGER_NOT_COMPLETE"),
    ("ledger", "completeness", "UNKNOWN", "B6_LEDGER_NOT_COMPLETE"),
    ("ledger", "version", "different-version", "B6_LEDGER_IDENTITY_MISMATCH"),
])
def test_admission_rejects_unauthorized_or_uncertified_metadata(section, key, value, reason):
    from src.evaluation.benchmark.admission import validate_real_data_admission
    metadata = certified_metadata()
    metadata[section][key] = value
    result = validate_real_data_admission(metadata)
    assert result["decision"] == "BLOCKED"
    assert reason in result["reasons"]


@pytest.mark.parametrize("field", ["raw_hash", "normalized_hash", "acquisition"])
def test_missing_provenance_status_is_not_certification(field):
    from src.evaluation.benchmark.admission import validate_real_data_admission
    metadata = certified_metadata()
    metadata["manifest"][field] = {"status": "MISSING"}
    assert validate_real_data_admission(metadata)["decision"] == "BLOCKED"


def test_hash_record_must_identify_same_snapshot():
    from src.evaluation.benchmark.admission import validate_real_data_admission
    metadata = certified_metadata()
    metadata["manifest"]["raw_hash"]["snapshot_id"] = "wrong-snapshot"
    assert "B4_SNAPSHOT_HASH_MISMATCH" in validate_real_data_admission(metadata)["reasons"]


def test_ledger_needs_complete_study_coverage_and_scope():
    from src.evaluation.benchmark.admission import validate_real_data_admission
    metadata = certified_metadata()
    metadata["ledger"]["coverage"].pop()
    assert "B6_STUDY_COVERAGE_INCOMPLETE" in validate_real_data_admission(metadata)["reasons"]
    metadata = certified_metadata()
    metadata["ledger"]["scope"] = deepcopy(metadata["ledger"]["scope"])
    metadata["ledger"]["scope"]["end"] = "2020-02-01"
    assert "B6_LEDGER_IDENTITY_MISMATCH" in validate_real_data_admission(metadata)["reasons"]


def exclusion_record(**changes):
    return {"study_id": "validation-v1", "instrument_id": "fixture-id", "ticker": "SYN",
            "session": "2020-07-01", "event_ids": ["fixture-event"], "episode_id": None,
            "reason": "previously reviewed", "provenance": "fixture:custodian-exclusion",
            "completeness": "COMPLETE", **changes}


def test_protected_stockday_outside_requested_slice_still_blocks_whole_file():
    from src.evaluation.benchmark.admission import validate_real_data_admission
    metadata = certified_metadata()
    # July is outside the requested March slice, but INSIDE the file's authorized scope.
    metadata["ledger"]["records"] = [exclusion_record()]
    result = validate_real_data_admission(metadata)
    assert "B6_PROTECTED_STOCKDAY_IN_SOURCE" in result["reasons"]


def test_metadata_only_exclusion_has_no_labels_and_supports_outside_scope():
    from src.evaluation.benchmark.admission import ExclusionLedger, validate_real_data_admission
    metadata = certified_metadata()
    metadata["ledger"]["records"] = [exclusion_record(session="2019-07-01")]
    ledger = ExclusionLedger.model_validate(metadata["ledger"])
    assert ledger.records[0].session.isoformat() == "2019-07-01"
    assert validate_real_data_admission(metadata)["decision"] == "PASS"
    metadata["ledger"]["records"][0]["attention"] = 3
    assert validate_real_data_admission(metadata)["decision"] == "BLOCKED"


@pytest.mark.parametrize("episode", [
    {"episode_id": "fixture-episode", "episode_start": "2019-12-20", "episode_end": "2020-01-02"},
    {"episode_id": "fixture-episode"},
])
def test_episode_overlap_or_unknown_boundary_fails_closed(episode):
    from src.evaluation.benchmark.admission import validate_real_data_admission
    metadata = certified_metadata()
    metadata["ledger"]["records"] = [exclusion_record(session="2019-12-20", **episode)]
    assert validate_real_data_admission(metadata)["decision"] == "BLOCKED"


def test_decision_is_deterministic_and_does_not_mutate_metadata():
    from src.evaluation.benchmark.admission import validate_real_data_admission
    metadata = certified_metadata()
    metadata["manifest"]["certification_status"] = "MISSING"
    metadata["ledger"]["completeness"] = "UNKNOWN"
    before = deepcopy(metadata)
    a = validate_real_data_admission(metadata)
    b = validate_real_data_admission(dict(reversed(list(metadata.items()))))
    assert a == b and a["reasons"] == sorted(set(a["reasons"]))
    assert metadata == before


@pytest.mark.parametrize("blocked", [True, False])
def test_future_loading_seam_never_invokes_loader_in_this_phase(blocked):
    from unittest.mock import Mock
    from src.evaluation.benchmark.admission import (
        AdmissionBlocked, RealDataLoaderDisabled, request_real_payload,
    )
    metadata = certified_metadata()
    if blocked:
        metadata["manifest"]["source_classification"] = "UNKNOWN"
    loader = Mock(side_effect=AssertionError("Real payload must never be opened"))
    expected = AdmissionBlocked if blocked else RealDataLoaderDisabled
    with pytest.raises(expected) as exc:
        request_real_payload(metadata, payload_loader=loader)
    assert exc.value.decision["decision"] == ("BLOCKED" if blocked else "PASS")
    loader.assert_not_called()


@pytest.mark.parametrize("field,value", [
    ("scope", None), ("issuer", None), ("evidence_reference", None),
    ("normalized_sha256", "d" * 64),
])
def test_certified_word_cannot_replace_certificate_evidence_or_identity(field, value):
    from src.evaluation.benchmark.admission import validate_real_data_admission
    metadata = certified_metadata()
    metadata["manifest"]["certificates"]["comparability"][field] = value
    assert validate_real_data_admission(metadata)["decision"] == "BLOCKED"


def test_full_source_scope_cannot_include_holdout_even_for_pre2025_request():
    from src.evaluation.benchmark.admission import validate_real_data_admission
    metadata = certified_metadata()
    metadata["manifest"]["scope"]["end"] = "2025-01-01"
    assert "B1_UNAUTHORIZED_DATE_RANGE" in validate_real_data_admission(metadata)["reasons"]


@pytest.mark.parametrize("mutation", [
    {"instrument_id": None, "ticker": None}, {"completeness": "UNKNOWN"},
    {"completeness": "INCOMPLETE"}, {"study_id": "uncovered-study"},
])
def test_incomplete_exclusion_record_cannot_be_treated_as_safe(mutation):
    from src.evaluation.benchmark.admission import validate_real_data_admission
    metadata = certified_metadata()
    metadata["ledger"]["records"] = [exclusion_record(session="2019-01-01", **mutation)]
    assert "B6_EXCLUSION_RECORD_INCOMPLETE" in validate_real_data_admission(metadata)["reasons"]


def test_no_protected_ledger_is_blocked():
    from src.evaluation.benchmark.admission import validate_real_data_admission
    metadata = certified_metadata()
    metadata["ledger"] = None
    assert "B6_LEDGER_NOT_COMPLETE" in validate_real_data_admission(metadata)["reasons"]
