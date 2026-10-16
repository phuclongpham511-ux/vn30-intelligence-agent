# Daily attention: competitive research V1

Inspected 2026-10-16, public interfaces in the Codex browser and official help
pages. This is a workflow sample, not a usability study or premium-product audit.
No accounts created, alerts subscribed, private data submitted or assets copied.

## Evidence and comparison

| Product and exact public URL | Direct UI observations | Documentation / limits | Decision for Woofi |
| --- | --- | --- | --- |
| [SStock board](https://sstock.vn/bang-dien) | Index strip; sector groups with consistent ticker/price/change/volume columns. One click opens Quick News above the board: VN30/all controls, publisher/time, linked ticker chips with session tooltips, load more and full archive. | Existing empty personal portfolio visible; saved portfolio behavior and review/correction semantics not tested. DOM interaction timed out; accessible native menu interaction succeeded. | Keep a short contextual reading layer and direct research links, without copying strength scores or inferred issuer links. |
| [FireAnt](https://www.fireant.vn/) | Index/price sidebar, prominent app entry points, short videos and separate public discussions with author/time/ticker links. Notification invitation distinguishes watchlist articles, followed-member activity and interactions; dismissed without subscription. | [Watchlist guide](https://help.fireant.vn/fireant-web/dashboard/panel-ben-phai/watchlist/) documents list/articles/community/alerts within one watchlist. [Entry guide](https://help.fireant.vn/fireant-web/intro/) says saving Watchlists requires login. Personalized workspace not tested. | Reuse the existing Watchlist context. Keep discussion separate from reporting; do not promote social popularity as factual importance. |
| [VietstockFinance](https://finance.vietstock.vn/) | Dense market landing with section jump links, dated charts, consistent numerical tables, company links, timestamped news and docked Watchlist/news panels. Explicit units and source disclaimer; advertising competes with research. | Authenticated Watchlist and corporate-event calendar interaction not verified. No dedup/read-state claim is inferred from the public list. | Preserve compact attribution and disclosure; avoid a second wide dashboard or recommendation columns. |
| [TradingView](https://www.tradingview.com/) → [News Flow](https://www.tradingview.com/news-flow/) | Homepage separates market context, ideas and news. News Flow has Full feed/Watchlist/Instrument/Add filter controls; compact provider/time/headline rows and an inline article reader with instrument navigation. | Selecting Watchlist did not establish a saved personalized filter; its actual saved-list behavior remains NOT_VERIFIED. Official [filter guide](https://www.tradingview.com/support/solutions/43000732560-news-flow-s-filters-overview/) and [alerts guide](https://www.tradingview.com/support/solutions/43000762838-news-alerts/) describe filtering and notifications. Alerts were not created. | Aggregate followed-stock reporting before deep research, but retain original publisher access and explicit reviews. |
| [Koyfin](https://www.koyfin.com/) → [login](https://app.koyfin.com/login) | Public homepage describes watchlist dashboards and research; app presents email/password/SSO login. **Application unavailable without authentication.** | Official [release notes](https://www.koyfin.com/help/release-notes/) describe Watchlist News for news/filings/transcripts; [desktop alerts](https://www.koyfin.com/help/release-notes/v3-66-desktop-alerts/) describe document alerts and contextual navigation. These are DOCUMENTATION ONLY, not tested premium features. | Use one existing followed-stock projection, not configurable widgets or another alert service. |
| [Seeking Alpha](https://seekingalpha.com/) → [Wall Street Breakfast](https://seekingalpha.com/author/wall-street-breakfast) | Public homepage separates Latest News, Trending Analysis, Trending News, saved articles and portfolios; ratings visibly locked. WSB profile directly describes a concise daily briefing readable on mobile/email. | Briefing article content, subscribed digest and personal portfolio not tested. Official [portfolio alerts help](https://help.seekingalpha.com/how-do-i-set-up-real-time-alerts-for-my-seeking-alpha-portfolio) describes daily portfolio digests. | Adopt a finite reading budget; reject opinion/rating promotion, forced daily content and subscription infrastructure. |

The shared pattern is contextual compression: market overview → followed universe
→ a short reading list → original evidence/research. None of these public
observations establishes correction-aware explicit acknowledgment. That remains a
Woofi strength, not a claimed competitor deficiency. Dedup internals, stale-source
policies and cross-device review semantics were NOT_VERIFIED for all six.

## Effort, hierarchy and mobile

Observed SStock board → Quick News takes one interaction; TradingView homepage →
News Flow takes one link, followed by filter controls. Koyfin reaches an auth wall.
FireAnt separates general market/community from personal monitoring. Vietstock's
section jumps reduce navigation but still require scanning several dense regions.
These counts describe only the inspected public entry step, not end-to-end tasks.

Competitor mobile application behavior was not tested. Seeking Alpha's mobile
briefing claim is official descriptive copy, not mobile acceptance. Avoid copying
desktop information density into small screens. Woofi's implementation will use
wrapping metadata and vertically ordered reading rows, with browser width checks.
No screenshot artifact was saved during this research; direct AX/DOM observations
are recorded above. No proprietary screenshot is shipped as a product asset.

## Opportunity and scope decision

Woofi already has market context, story identities, exact issuer association,
per-ticker unread items, Community and explicit correction-aware receipts. The
verified code gap is **cross-ticker triage**: users must scan each stock and source
section and can encounter the same Story repeatedly across followed tickers.

Add a bounded “Read first” section inside Watchlist, using already loaded News and
Community. Deduplicate identities across stocks, show no more than three unread
items, disclose ordering and page bounds, preserve attribution/publication age,
and allow explicit acknowledgment of only the represented ticker-item pairs.
Technical remains in its existing assurance-aware section. No new Home dashboard,
AI summary, speculative importance score, automated review or acquisition worker.

Research informs a hypothesis of lower scanning effort; actual time saved is not
claimed as measured. Quiet/no-new-evidence and incomplete coverage are first-class.
