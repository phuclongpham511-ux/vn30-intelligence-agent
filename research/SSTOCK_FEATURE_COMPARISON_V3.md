# SStock feature comparison — V3

Status describes the delivered bounded financial experience, including data and
acceptance limits. COMPLETE requires usable supported data, correct behavior and
end-to-end acceptance for the stated scope; a component/endpoint is insufficient.
Runtime/browser/mobile acceptance is PENDING, so no feature is labelled COMPLETE.
All real data below is in explicitly enabled private research mode.

| SStock Feature | Woofi Implementation | Data Source | Functional Status | Coverage | Remaining Gap |
|---|---|---|---|---|---|
| Financial Overview | Period-labelled financial highlights, revenue/profit first, balance/cash/quality disclosures; shared controls | Existing VCI; selected HPG/TCB/VCB originals; CafeF | PARTIAL | Nine saved issuers, three with original-qualified annual inputs | Runtime/mobile acceptance; broader qualified histories |
| Revenue & Earnings | Existing combined amount/rate charts and detailed performance table | HPG annual originals; bank-specific TCB/VCB income; VCI; partial CafeF | PARTIAL | HPG/TCB/VCB 2024–25 qualified, original provider 2018–25 amount histories | CafeF net revenue unresolved; source-specific revision comparability |
| Growth Analysis | YoY trends, exact-prior-year changes, metric definitions; no unknown-scope promotion | Same original reports / canonical Python engine | PARTIAL | HPG revenue/PAT; TCB/VCB bank income, PAT, loans/deposits growth | Qualified quarterly/QoQ/TTM and longer ratio histories |
| Balance Sheet | Dedicated composition/amount view and selected source statement table | Original reports; VCI; VHM CafeF | PARTIAL | HPG 2025; TCB/VCB 2024–25; eight-year original provider amounts | HPG qualified prior closing balance; more component fields |
| Cash Flow Analysis | Dedicated operating/investing/financing/FCF history, signs and exact source rows | HPG, TCB, VCB originals; VCI | PARTIAL | Three original-report issuers over two annual periods; HPG FCF | More years, qualified quarterly flows, complete note coverage |
| Profitability Ratios | Dedicated margins/ROE/ROA, backend formulas and explanations | HPG margins; TCB/VCB average-balance returns | PARTIAL | 2024–25 margins; 2025 bank ROE/ROA | HPG opening balances, extra bank years, NIM |
| Financial Health | Liquidity/leverage; separate bank funding and deposit/credit-quality panel | HPG original; TCB original statements/notes; VCB common statements | PARTIAL | HPG 2025 ratios; TCB/VCB loans/deposits; TCB two-year note ratios | CAR/NIM, specialist peer notes; accounting definitions differ from vendor/regulatory ratios |
| Valuation | No fabricated P/E/P/B chart; reported EPS remains separately labelled | Original bank EPS / existing provider amounts | UNAVAILABLE | Reported EPS is useful per-share disclosure, not valuation | Matched dated price, weighted shares, parent equity and adjustments |
| Detailed Financial Statements | Original label/period/unit tables, source evidence, selected notes and expandable metric definitions | Three selected original reports; VCI; VHM CafeF | PARTIAL | 113 qualified canonical reported cells plus two FX reconciliation cells; partial original provider tables | Full statement/note coverage and more periods, rather than merely selected fields |
| Dividends and Corporate Actions | Existing timeline with financial-analysis shortcut, original links/terms/dates | Three saved official VSDC FPT notices | PARTIAL | FPT three cash notices; all other histories explicitly incomplete | More issuer/action coverage, qualified ex-dates and dividend yield |
| Industry Analysis | Observed directory, per-metric coverage, missing members, covered median/min/max | 406 SSI observed pairs; saved financial sources | PARTIAL | 61 categories, eight with financial observations; bank median on 15 metrics | Wider qualified cohort; specialist securities/property fields; historical totals disabled |
| Peer Comparisons | Company-context navigation, table, competition rank/percentile, covered distribution | TCB/VCB originals + matching observed SSI bank category | PARTIAL | Two of 22 banks, 15 FY2025 metrics | More original-report peers; comparable specialist ratios outside TCB; browser acceptance |

The current SStock revisit reconfirmed company context, shared period controls,
business-picture/growth/valuation/statement/document navigation and model-specific
chart groups. Its narrow integrated-browser layout showed dense two-column
issuer facts and vertically arranged financial groups. Woofi implements its own
responsive two-column/three-column highlights and existing chart/table system.
SStock's displayed financial values, scores, taxonomy and data provider are not
inputs to Woofi. The existing [research catalogue](sstock/DASHBOARD_CATALOG.md)
remains the broader interaction reference.
