# Measured data coverage

Read research/data/OBSERVED_SAMPLE.json for exact per-ticker ranges and research/data/DATA_COVERAGE_MATRIX.csv for field-level numerators and denominators. Eight sample issuers, three statements each, 1,008 statement observations total: 756 reused and 252 newly captured through the existing adapter. This is not a production DB census or all-listed-equity coverage.

All 1,008 lack qualified consolidation/original-unit/publication metadata. The adapter's known transport unit convention is distinct from original metadata. Real public qualification is zero in this measured sample. The private revision journal contains 23,040 normalized period-metric versions across annual/quarterly/TTM projections (most recent 20 periods per frequency, eight annual where available). Its unavailable/blocked values remain null. These are metric-version records, not 23,040 verified financial facts.

No actual issuer-to-industry taxonomy was available in the baseline. Real industry coverage is unactivated. Synthetic tests/preview prove arithmetic, cohort exclusions, rank and missing coverage, not production market completeness. Official PNJ saved-text comparison is separate and does not qualify VCI consolidation or public rights.
