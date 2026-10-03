"""D2 v1 metadata admission. Never opens certificate references or payloads.

PASS establishes consistency of declared custodian metadata only. Authenticity,
file identity/reparse-point checks and payload hash verification belong to a future
authorized adapter. No real-data loading is enabled by this module.
"""
from datetime import date, datetime
import ntpath
import posixpath
from pathlib import PurePosixPath, PureWindowsPath
from typing import Annotated, Literal

from pydantic import Field, StringConstraints, ValidationError
from src.evaluation.models import EvaluationModel

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
SHA256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
State = Literal["CERTIFIED", "UNVERIFIED", "MISSING", "NOT_APPLICABLE"]
Completeness = Literal["COMPLETE", "UNKNOWN", "INCOMPLETE"]
REQUIRED_STUDIES = frozenset(("validation-v1", "validation-v2", "development-v3"))


class Instrument(EvaluationModel):
    instrument_id: Text
    ticker: Text


class Scope(EvaluationModel):
    source: Text
    source_version: Text
    snapshot_id: Text
    authorized_path: Text
    instruments: tuple[Instrument, ...] = Field(min_length=1)
    start: date
    end: date
    exchange: Text


class Certificate(EvaluationModel):
    status: State = "MISSING"
    issuer: Text | None = None
    version: Text | None = None
    evidence_reference: Text | None = None
    scope: Scope | None = None
    normalized_sha256: SHA256 | None = None
    reasons: tuple[Text, ...] = ()


class Certificates(EvaluationModel):
    historical_universe: Certificate | None = None
    comparability: Certificate | None = None
    provenance: Certificate | None = None
    exchange_calendar: Certificate | None = None


class HashStatus(EvaluationModel):
    status: State = "MISSING"
    snapshot_id: Text | None = None
    sha256: SHA256 | None = None
    reasons: tuple[Text, ...] = ()


class AcquisitionStatus(EvaluationModel):
    status: State = "MISSING"
    value: datetime | None = None
    reasons: tuple[Text, ...] = ()


class AdmissionManifest(EvaluationModel):
    schema_version: Literal["d2-admission-v1"]
    scope: Scope
    source_classification: Literal["SAFE_TO_INSPECT", "PROTECTED_OR_POSSIBLY_PROTECTED", "UNKNOWN"] = "UNKNOWN"
    certification_status: State = "MISSING"
    certification_reasons: tuple[Text, ...] = ()
    acquisition: AcquisitionStatus = Field(default_factory=AcquisitionStatus)
    raw_hash: HashStatus = Field(default_factory=HashStatus)
    normalized_hash: HashStatus = Field(default_factory=HashStatus)
    certificates: Certificates = Field(default_factory=Certificates)
    protected_ledger_version: Text | None = None
    availability_policy_version: Text | None = None


class AdmissionRequest(EvaluationModel):
    path: Text
    start: date
    end: date
    instruments: tuple[Instrument, ...] = Field(min_length=1)
    source: Text
    source_version: Text
    snapshot_id: Text
    payload_kind: Literal["raw", "normalized"]
    sha256: SHA256


class StudyCoverage(EvaluationModel):
    study_id: Text
    completeness: Completeness = "UNKNOWN"
    provenance: Text | None = None


class ExclusionRecord(EvaluationModel):
    study_id: Text
    instrument_id: Text | None = None
    ticker: Text | None = None
    session: date
    event_ids: tuple[Text, ...] = ()
    episode_id: Text | None = None
    episode_start: date | None = None
    episode_end: date | None = None
    reason: Text
    provenance: Text
    completeness: Completeness = "UNKNOWN"


class ExclusionLedger(EvaluationModel):
    schema_version: Literal["d2-exclusions-v1"]
    version: Text
    scope: Scope
    completeness: Completeness = "UNKNOWN"
    issuer: Text | None = None
    provenance: Text | None = None
    coverage: tuple[StudyCoverage, ...] = ()
    records: tuple[ExclusionRecord, ...] = ()


class AdmissionMetadata(EvaluationModel):
    manifest: AdmissionManifest
    request: AdmissionRequest
    ledger: ExclusionLedger | None = None


def _decision(reasons):
    return {"decision": "BLOCKED" if reasons else "PASS", "reasons": sorted(set(reasons)),
            "payload_loaded": False, "real_loader_enabled": False, "scope": "DECLARED_METADATA_ONLY"}


def _path_key(value):
    """Lexical identity only; never resolve symlinks, stat a path, or open a file."""
    windows = PureWindowsPath(value)
    path = windows if windows.drive else PurePosixPath(value)
    if (not path.is_absolute() or ".." in path.parts or "\x00" in value
            or value.startswith(("\\\\?\\", "\\\\.\\"))):
        return None
    if windows.drive:
        if any(":" in part for part in windows.parts[1:]):
            return None
        return ntpath.normcase(ntpath.normpath(value))
    return posixpath.normpath(value)


def _ledger_reasons(manifest, ledger):
    if ledger is None:
        return ["B6_LEDGER_NOT_COMPLETE"]
    reasons = []
    scope = manifest.scope
    if ledger.completeness != "COMPLETE" or not ledger.issuer or not ledger.provenance:
        reasons.append("B6_LEDGER_NOT_COMPLETE")
    if ledger.version != manifest.protected_ledger_version or ledger.scope != scope:
        reasons.append("B6_LEDGER_IDENTITY_MISMATCH")
    studies = {c.study_id for c in ledger.coverage}
    if (not REQUIRED_STUDIES.issubset(studies) or len(studies) != len(ledger.coverage)
            or any(c.completeness != "COMPLETE" or not c.provenance for c in ledger.coverage)):
        reasons.append("B6_STUDY_COVERAGE_INCOMPLETE")
    instruments = {i.instrument_id for i in scope.instruments}
    tickers = {i.ticker for i in scope.instruments}
    for record in ledger.records:
        if (record.completeness != "COMPLETE" or not (record.instrument_id or record.ticker)
                or record.study_id not in studies):
            reasons.append("B6_EXCLUSION_RECORD_INCOMPLETE")
        # Match either identity conservatively; a renamed ticker cannot bypass an ID.
        relevant = record.instrument_id in instruments or record.ticker in tickers
        if relevant and scope.start <= record.session <= scope.end:
            reasons.append("B6_PROTECTED_STOCKDAY_IN_SOURCE")
        if record.episode_id or record.episode_start or record.episode_end:
            if (record.episode_start is None or record.episode_end is None
                    or record.episode_start > record.episode_end
                    or not record.episode_start <= record.session <= record.episode_end):
                reasons.append("B6_EPISODE_SCOPE_UNRESOLVED")
            elif relevant and record.episode_start <= scope.end and scope.start <= record.episode_end:
                reasons.append("B6_PROTECTED_EPISODE_IN_SOURCE")
    return reasons


def validate_real_data_admission(metadata):
    """Validate supplied metadata in memory; null/unknown never implies certified."""
    try:
        bundle = AdmissionMetadata.model_validate(metadata)
    except ValidationError as exc:
        return _decision(["INVALID_METADATA:" + ".".join(map(str, error["loc"]))
                          for error in exc.errors(include_input=False)])
    manifest, request = bundle.manifest, bundle.request
    scope = manifest.scope
    reasons = []
    if manifest.source_classification != "SAFE_TO_INSPECT":
        reasons.append("B1_SOURCE_NOT_SAFE")
    if manifest.certification_status != "CERTIFIED":
        reasons.append("B1_MANIFEST_NOT_CERTIFIED")
    if _path_key(scope.authorized_path) is None or _path_key(request.path) != _path_key(scope.authorized_path):
        reasons.append("B1_UNAUTHORIZED_PATH")
    if not scope.start <= request.start <= request.end <= scope.end < date(2025, 1, 1):
        reasons.append("B1_UNAUTHORIZED_DATE_RANGE")
    allowed = {(i.instrument_id, i.ticker) for i in scope.instruments}
    requested = {(i.instrument_id, i.ticker) for i in request.instruments}
    if (not requested.issubset(allowed) or len(allowed) != len(scope.instruments)
            or len(requested) != len(request.instruments)
            or len({i.instrument_id for i in scope.instruments}) != len(scope.instruments)
            or len({i.ticker for i in scope.instruments}) != len(scope.instruments)):
        reasons.append("B1_UNAUTHORIZED_INSTRUMENT")
    if (scope.source, scope.source_version) != (request.source, request.source_version):
        reasons.append("B4_SOURCE_IDENTITY_MISMATCH")
    for value in (manifest.raw_hash, manifest.normalized_hash):
        if value.status != "CERTIFIED" or value.sha256 is None:
            reasons.append("B4_HASH_NOT_CERTIFIED")
        if value.snapshot_id != scope.snapshot_id:
            reasons.append("B4_SNAPSHOT_HASH_MISMATCH")
    expected_hash = manifest.raw_hash if request.payload_kind == "raw" else manifest.normalized_hash
    if request.snapshot_id != scope.snapshot_id or request.sha256 != expected_hash.sha256:
        reasons.append("B4_SNAPSHOT_HASH_MISMATCH")
    acquisition = manifest.acquisition
    if (acquisition.status != "CERTIFIED" or acquisition.value is None
            or acquisition.value.utcoffset() is None):
        reasons.append("B4_ACQUISITION_NOT_CERTIFIED")
    if manifest.availability_policy_version != "d2-eod-availability-v1":
        reasons.append("D2_PIT_POLICY_NOT_CERTIFIED")
    for name, code in (("historical_universe", "B2_HISTORICAL_UNIVERSE_NOT_CERTIFIED"),
                       ("comparability", "B3_COMPARABILITY_NOT_CERTIFIED"),
                       ("provenance", "B4_PROVENANCE_NOT_CERTIFIED"),
                       ("exchange_calendar", "B5_CALENDAR_NOT_CERTIFIED")):
        cert = getattr(manifest.certificates, name)
        if (cert is None or cert.status != "CERTIFIED" or not cert.issuer or not cert.version
                or not cert.evidence_reference):
            reasons.append(code)
        elif cert.scope != manifest.scope or cert.normalized_sha256 != manifest.normalized_hash.sha256:
            reasons.append(code + ":SCOPE_OR_HASH_MISMATCH")
    reasons.extend(_ledger_reasons(manifest, bundle.ledger))
    return _decision(reasons)


class AdmissionBlocked(PermissionError):
    def __init__(self, decision):
        self.decision = decision
        super().__init__("Real data admission BLOCKED: " + ", ".join(decision["reasons"]))


class RealDataLoaderDisabled(PermissionError):
    def __init__(self, decision):
        self.decision = decision
        super().__init__("Metadata PASS; real-data loading remains disabled in Phase 1.5B")


def request_real_payload(metadata, *, payload_loader):
    """Future injection seam. Validation always precedes the disabled loader boundary.

    The callback is deliberately NEVER invoked, even on PASS. There is no enable
    flag; a later authorized implementation must verify the physical file and
    certificates without treating this metadata verdict as official readiness.
    """
    decision = validate_real_data_admission(metadata)
    if decision["decision"] != "PASS":
        raise AdmissionBlocked(decision)
    raise RealDataLoaderDisabled(decision)
