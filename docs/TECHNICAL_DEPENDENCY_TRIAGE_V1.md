# Frontend dependency triage — 2026-10-10

Stock Detail checkpoint: 162d1de, after 854 backend and 73 frontend tests,
typecheck/build and diff/identity guards passed. Original worktree unchanged.

## Findings and product reachability

The initial npm audit flagged three packages as high severity. Reachability below
is an inference from the repository's routes, imports and configuration, not an
exploit test. Compatible patch releases were confirmed in the npm registry.

| Package | Advisory and affected version | Product impact | Fix and upgrade risk |
| --- | --- | --- | --- |
| next 16.3.6 | [GHSA-cjq9-62q9-8jv4](https://github.com/advisories/GHSA-cjq9-62q9-8jv4), high, remote image optimization SSRF | No remotePatterns or remote optimized Image imports; local mascot Images are unoptimized. The documented vulnerable remote-image path is not configured. | Pin 16.3.8: same minor release, no architecture migration. Regression/build/browser validation required. |
| sharp 0.35.4 | [GHSA-wq5f-xc86-pv6w](https://github.com/advisories/GHSA-wq5f-xc86-pv6w), high, upstream librsvg memory issue | No direct SVG decoding. Current host is Windows; advisory describes possible RCE under particular glibc Linux conditions. Future Linux image processing is relevant. | Lock 0.35.5 within Next's existing range. Native binary compatibility and build/rendering are the relevant risks. |
| source-map-js 1.2.1 | [GHSA-68fv-2mgg-jv7q](https://github.com/advisories/GHSA-68fv-2mgg-jv7q), high, indexed source-map offset denial of service | Transitive PostCSS/Tailwind build dependency. No user-supplied source-map ingestion was found. Primary exposure is processing untrusted build inputs. | Lock 1.2.2 within existing dependency ranges. No new direct dependency/override; CSS/build regression risk. |

Next also aggregates these advisories, all fixed by 16.3.8:

- [GHSA-3w37-wq28-93x7](https://github.com/advisories/GHSA-3w37-wq28-93x7),
  moderate: cache-component Draft Mode fill leak. Neither feature is configured.
- [GHSA-4jqv-mc3x-m676](https://github.com/advisories/GHSA-4jqv-mc3x-m676),
  moderate: Pages Router SSG/ISR cache poisoning. This project uses App Router.
- [GHSA-39w2-rjm5-chcv](https://github.com/advisories/GHSA-39w2-rjm5-chcv),
  low: development MCP information disclosure. Relevant to developer use of
  next dev; production next start does not expose that endpoint.
- [GHSA-f87g-xv8r-7p7x](https://github.com/advisories/GHSA-f87g-xv8r-7p7x),
  moderate: webpack metadata-image dynamicParams bypass. No such image routes;
  builds use Turbopack.
- [GHSA-mcj8-r9mp-w47p](https://github.com/advisories/GHSA-mcj8-r9mp-w47p),
  moderate: root catch-all page SSG/ISR cache poisoning. No root catch-all page;
  catch-all API proxies are not that page contract.

## Remediation and validation

Only the existing Next pin and compatible transitive lock entries were updated.
No major upgrade, npm audit fix --force, new direct transitive dependencies or
architecture change. The new npm audit reports **zero vulnerabilities**.
All 73 frontend tests, typecheck and optimized production build passed with
Next 16.3.8. Broader final integration validation is recorded in the supervised
EOD report. No push or deployment.
