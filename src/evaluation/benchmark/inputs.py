"""D2 pre-load boundary. Certificates are custodian attestations, not inferred data facts."""
from dataclasses import dataclass
from datetime import date, datetime, time
from hashlib import sha256
import json
from pathlib import Path
from zoneinfo import ZoneInfo

ZONE = ZoneInfo("Asia/Ho_Chi_Minh")
CERTIFICATES = ("historical_vn30_membership", "corporate_action_comparability",
                "source_version_provenance", "exchange_calendar", "protected_data_exclusion")


def eod(session):
    return datetime.combine(date.fromisoformat(session), time(23, 59, 59), ZONE)


@dataclass(frozen=True)
class InputPermit:
    path: str
    start: str
    end: str
    source: str
    version: str
    sha256: str
    instruments: tuple[str, ...]
    certifications: dict
    is_fixture: bool = False


def preflight(permit):
    blockers = []
    if permit is None:
        blockers = ["safe_input_allowlist", *CERTIFICATES]
    else:
        if permit.is_fixture:
            blockers.append("synthetic_is_not_official_evidence")
        if not permit.source or not permit.version or not permit.instruments or len(permit.sha256) != 64:
            blockers.append("safe_input_allowlist")
        # Do not read any referenced certificate or source payload automatically.
        for key in CERTIFICATES:
            record = permit.certifications.get(key, {})
            if not all(record.get(field) for field in ("issuer", "evidence_reference", "version")):
                blockers.append(key)
        if not (date.fromisoformat(permit.start) <= date.fromisoformat(permit.end) < date(2025, 1, 1)):
            blockers.append("pre_2025_boundary")
    return {"status": "BLOCKED_BY_DATA_OR_PROVENANCE" if blockers else "CERTIFICATE_METADATA_PRESENT",
            "blockers": blockers, "data_opened": False,
            "note": "Metadata presence alone is not certification verification or official readiness."}


def load_authorized(path, *, permit, start, end, source):
    """Reject path, source, interval or uncertified real snapshot BEFORE opening it.

    Phase 1 supports synthetic files only. A real-data adapter needs independently
    verified custodian certificates; arbitrary self-asserted JSON cannot unlock it.
    """
    resolved = Path(path).resolve()
    interval_valid = (date.fromisoformat(permit.start) <= date.fromisoformat(start)
                      <= date.fromisoformat(end) <= date.fromisoformat(permit.end) < date(2025, 1, 1))
    if (resolved != Path(permit.path).resolve() or source != permit.source or not interval_valid
            or not permit.version or not permit.instruments):
        raise PermissionError("Unauthorized path/source/date scope; input not opened")
    if not permit.is_fixture:
        raise PermissionError("Real D2 certificates not independently verified; input not opened")
    content = resolved.read_bytes()
    if sha256(content).hexdigest() != permit.sha256:
        raise ValueError("Snapshot checksum mismatch")
    payload = json.loads(content)
    if payload.get("is_fixture") is not True or payload["provenance"]["source"] != source:
        raise ValueError("Fixture/source provenance mismatch")
    if payload["provenance"]["version"] != permit.version:
        raise ValueError("Source version mismatch")
    for row in payload["bars"]:
        if not permit.start <= row["session"] <= permit.end or row["ticker"] not in permit.instruments:
            raise ValueError("Payload violates certified snapshot scope")
    return payload


def visible_bar(row, cutoff):
    """Audited time overrides daily assumption, including known late publication."""
    if row["session"] > cutoff.date().isoformat():
        return None
    audited = row.get("available_at")
    if audited:
        at = datetime.fromisoformat(audited)
        if at.utcoffset() is None or at < datetime.combine(date.fromisoformat(row["session"]), time(), ZONE):
            raise ValueError("Invalid audited availability")
        assurance, basis = "AUDITED", "published"
    elif row.get("availability_basis") == "end_of_day_assumption":
        at, assurance, basis = eod(row["session"]), "ASSUMED", "EOD_AVAILABILITY_ASSUMPTION"
    else:
        return None
    if at > cutoff:
        return None
    return {**row, "available_at": at.isoformat(), "audited_available_at": audited,
            "assumed_available_at": eod(row["session"]).isoformat() if assurance == "ASSUMED" else None,
            "timestamp_assurance": assurance, "availability_basis": basis,
            "availability_policy": "d2-eod-availability-v1"}
