# Actual data audit

Baseline b88f6f00250ea1a3ddc2a87ce7aabb95653d6573 has one FastAPI app, SQLModel application entities, SSI pricing, VCI packets through pinned vnstock 4.0.2, and a deterministic financial engine. Financial statements are fetched on demand and cached in process, not persisted as financial fact tables in the application schema. Existing private captures and reviewed filing manifests are separate saved evidence. No production database or credentials were inspected or modified.

The baseline already implements 49 financial outputs, including raw fields, ratios, growth and a balance residual diagnostic. Source mappings contain 25 canonical fields across income/balance/cash. The UI displays an approved subset; the full API/calculation evidence exposes more. The public projection requires qualified consolidation, source/field/receipt provenance and display permission. Personal research may show single source-reported amounts; it does not qualify unknown-basis derived comparisons.

The audit reads six hash-pinned captures and two new bounded existing-adapter captures. OBSERVED_SAMPLE.json and DATA_COVERAGE_MATRIX.csv contain exact denominators, tickers, frequencies, report kinds and period lists. These are sample percentages, not all-market or production-persistence coverage. A new dedicated offline journal stores normalized revisions; it is not the application database. Unknown facts are retained with null display values.

Classification: Stock.sector/industry exist as nullable unversioned fields. Security metadata does not supply a reviewed industry taxonomy. No real ticker-to-industry mapping is fabricated. The new schema requires versioned, effective-dated memberships and explicit references.
