# V4 valuation evidence decisions

The existing Python financial engine remains numerical ground truth. No provider
valuation multiple is imported as a substitute for its inputs.

| Metric | Decision | Required evidence / implemented basis |
|---|---|---|
| Reported EPS | Available where individually source-supported | Keep source period, original VND/share scale and revision; do not sum quarterly EPS or treat it as a price multiple |
| Period-end book value per ordinary share | Activated for FPT FY2023/FY2024 | Ordinary-share capital and reserves from note 24 / actual circulating ordinary shares from note 23, same reporting date and binary; exclude non-controlling interests and budget funds |
| P/E | Unavailable | Matched dated SSI price / compatible annual or TTM ordinary EPS; price/EPS must share the same corporate-action basis, with financial publication evidence if historical PIT is claimed |
| P/B | Unavailable | Matched dated SSI price / compatible ordinary BVPS, including intervening share issuance, treasury shares and distributions |
| Earnings yield | Unavailable | Compatible ordinary EPS / the same dated price and action basis; no inverse of an unavailable P/E |
| Market capitalization | Unavailable | Dated price × actual shares outstanding on that price date; do not substitute weighted-average EPS shares or nominal capital |

FPT's book-value denominator is the actual circulation count at each reporting
date, not the weighted-average denominator used by EPS. The capital/reserve note
and share note are visually reviewed against the original public annual-report
PDF hosted by FPTS. The original comparative EPS in the 2023 report differs from
the later 2024 report's comparative presentation. Both originals remain pinned;
the explicit history selects the later 2023 comparative, without inventing a
universal adjustment factor. The book-value table is a reporting-date accounting
measure and never claims a historical price or historical availability date.

The adapter distinguishes `shares`, `VND` and `VND/share`; per-share values never
receive the million-VND statement multiplier. Positive integer share counts,
matching source/binary/scope/period and applicable balance checks are required.
Tests cover zero/negative shares, wrong units, mismatched owners and unpinned
history documents. Unsupported market multiples are still rejected by the
frontend contract. A valid private book value requires accounting/metadata
verification and the backend's same-period ordinary-equity/share inputs.

The installed SSI integration already normalizes dated trades/OHLC to VND and
preserves source times. It does not store a complete dated outstanding-share and
adjustment series in the financial evidence bundle. The private launcher clears
SSI credentials and performs no price acquisition. No credential, production
configuration, provider scope or paid subscription was changed.

Current official SSI documentation describes [masterData](https://developers.ssi.com.vn/docs/api-reference/data-masterData)
as dated ceiling/floor/reference-price data, and separately exposes
[corporateActions](https://developers.ssi.com.vn/docs/api-reference/data-corporateActions).
The latter needs its own authorized scope; event dates/ratios can be absent.
These schemas identify future evidence sources, not recovered Woofi records.
Older [v2 specifications](https://guide.ssi.com.vn/ssi-products/fastconnect-data/api-specs)
also distinguish adjusted and unadjusted closes; their fields must not be assumed
to exist in the installed v3 response. No documentation sample is ingested.

Publication time and public redistribution rights remain separate from current
accounting verification. Neither audited-report approval dates, URL dates nor
receipt times are promoted to qualified publication timestamps.
