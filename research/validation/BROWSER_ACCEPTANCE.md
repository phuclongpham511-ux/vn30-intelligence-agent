# Browser acceptance — actual integrated browser

Permitted Codex Integrated Browser was exposed and used; no personal external browser or automation framework was launched. SStock initially redirected to sign-in and later became accessible in the current session; eighteen issuer checks and industry interactions were completed. WiData HPG/TCB/SSI/VHM, statement interactions and methodology were inspected directly.

Woofi preview: http://127.0.0.1:3546/demo/financial-intelligence with NEXT_PUBLIC_WOOFI_VALIDATION=replay. Actual React components and Recharts rendered, not generated HTML screenshots. Checked non-financial annual cash-flow/profitability/liquidity, banking model selection, quarterly switching, VI language and light theme. Synthetic DEMO labels remain visible. Screenshots are under screenshots/.

Desktop and an observed approximately 377px-wide integrated pane were inspected. The narrow view kept charts readable and allowed horizontal table scrolling; screenshots/04-industry-narrow.png records the peer section. The exposed controls did not include viewport sizing, so no controlled device matrix is claimed. Real data display/industry coverage is not approved by fixture rendering. Dedicated local preview never accesses production services; BACKEND_URL points at the unused isolated port 8546.

The shared app shell attempted its normal ingestion-refresh requests against the unused isolated backend port and received 502. No production service or ingestion worker was contacted. API behavior was validated separately with FastAPI fixture integration tests. The local preview was stopped before the final normal production build.

The final production build passed. Its generated demo HTML contains the not-found
result and no synthetic heading/taxonomy content. A final preview restart was
rejected by automatic approval review as “blocked by policy”; no alternate launcher
was used. Post-build runtime recheck remains pending. The screenshots above record
the successful actual browser pass before that restart attempt.
