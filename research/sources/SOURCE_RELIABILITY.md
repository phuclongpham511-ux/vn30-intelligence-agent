# Reliability and provenance

VCI is retained because the actual pinned adapter, metadata guards and saved source receipts are inspectable. Known problems: absent consolidation/original-unit metadata; unqualified publication strings; financial-other model fields remain sparse; source labels can conflict; SDK DataFrame head/fill operations must not erase history/missingness. Existing packet transport avoids those transformations.

Receipt hashes and per-record hashes establish the saved input version, not the issuer's audit status or first-publication vintage. The journal never overwrites a prior revision and rejects a changed payload under the same revision identity. Same-time conflicting revisions are explicitly unavailable. As-of reads exclude unknown publication dates and records fetched after the cutoff; this does not establish certified historical membership or issuer vintages.

Observed sample completeness is documented, not extrapolated. Source endpoints can change or become unavailable. No provider uptime, SLAs or rate-limit ceiling was measured. No automatic provider replacement, live retry expansion, unrestricted endpoint loop or production collector was introduced.
