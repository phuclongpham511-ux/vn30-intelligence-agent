# Explore + News Taxonomy + Search UX Correction V2

STATUS: PASS. Completed locally; no push authorized or performed.

GIT BASE: 32ec86c3a7e95706ccbaec10476b914d6a6a98ca on main.

## VN-Index and mascot

VN-Index now sits in the Explore hero upper right on desktop, beside the existing white wolf enlarged from 64 to 128 px. Mobile stacks the hero context and market data. Both themes use the same mascot assets. The hero has no provider/debug wording. Click opens /indices/VNINDEX with candle and volume charts, 3M/6M/1Y/2Y ranges, selected/latest OHLC and inspectable source evidence. Historical stock transport is reused without changing normalization or completed-session rules.

Actual SSI snapshot read on 07 Oct 2026: trading date 06 Oct 2026; level 1,759.08 points; Up +5.88 points (+0.34%); total volume 791,551,098 shares; total value 18,715,110,854,170 VND. Latest OHLC: 1,755.34 / 1,763.84 / 1,734.94 / 1,759.08. Browser 3M chart contained 61 completed sessions; changing to 6M loaded 122. Missing aggregates remain null/Unavailable.

## Hot Topics and News

Hot Topics appears only on Explore. Qualification requires at least two independent publisher groups and an eligible same-Story image. Ranking is publisher breadth, article activity capped at 20, then recency. Representative image is preferred; a deterministic eligible cluster member supplies fallback. Images use contain. Browser failures try other same-Story candidates, then remove the visual item if all fail; semantic archives retain no-image stories.

Live Hot Topics contained the SHB payment promotion and coffee export story, each with two independent publishers and working representative images. There was no live representative-missing fallback case; same-Story fallback and unrelated-image rejection were verified through backend public-seam and frontend render tests.

Navigation is exactly Industry -> Company -> Market Brief -> Community Pulse. No Hot Topics, Global Markets, Latest News or financial-only toggle remains on News. Semantic archives allow single-source stories with explicit counts and inspectable other reporting.

Classification uses deterministic headline subject framing. Broad market/macro framing, USD/VND and analyst-attributed index subjects take priority; primary sector framing comes next; Company requires primary-subject identity from active SSI ordinary-equity metadata. Unknown/private subsidiary extensions cannot inherit eligibility from a listed parent's bare brand, regardless of casing or Vietnamese accents. Sector/ticker mentions alone cannot grant Company. No ticker/headline exceptions or investment recommendation logic were added.

Foreign registry sources removed: bbc, guardian, fed, ecb, marketwatch. Ten Vietnamese publishers remain active: vnexpress, cafef, vneconomy, vietstock, vietnambiz, vietnamnet, tuoitre, thanhnien, dantri, vnbusiness. Foreign historical records remain stored; normal feeds, cluster disclosure, counts and images exclude them. Recognized overseas subjects require Vietnam context or a primary listed issuer. Live category verification examined 14 Company, 6 Industry and 90 Market Brief stories (limit 100) and found no foreign publisher in returned evidence.

## Real examples verified

| Category | Actual headline | Publisher | Why it qualifies |
| --- | --- | --- | --- |
| Company | SHB hoàn đến 200.000 đồng khi khách hàng thanh toán hóa đơn tự động | VnExpress | SHB issuer operation/promotion |
| Company | CEO FPT lần thứ 3 liên tiếp đắc cử Phó chủ tịch ASOCIO | Tuoi Tre | Listed issuer leadership |
| Company | VIB huy động 285 triệu USD, hướng tới 1 tỉ USD vốn quốc tế | Thanh Nien | Listed bank capital raising |
| Industry | Kim ngạch xuất khẩu cà phê giảm khi giá rớt 20% | VnExpress | Sector exports/pricing |
| Industry | Những yêu cầu mới về bao bì trong ngành thức uống dinh dưỡng chức năng | Thanh Nien | Industry-wide packaging requirements |
| Industry | Dự án hạ tầng metro, giao thông và logistics 'dắt tay' ngành cơ khí TP.HCM tăng trưởng | Tuoi Tre | Mechanical industry infrastructure impact |
| Market Brief | Thứ trưởng Bộ Tài chính: Sẽ trình Quốc hội sửa Luật Chứng khoán ngay kỳ họp tháng 10 | CafeF | Broad securities regulation |
| Market Brief | Lãi suất trái phiếu chính phủ Việt Nam neo cao | VnExpress | Domestic sovereign yields |
| Market Brief | VN-Index tăng nhẹ, thị trường kỳ vọng phục hồi quanh 1775 điểm | VnEconomy | Broad index movement |

The persisted MBS-attributed VN-Index forecast now appears in Market Brief rather than Company.

## Search and browser verification

Explore, header and Watchlist share an initially empty combobox. Empty focus shows valid recent history or nothing. Typed results search all 1,522 SSI equities and show at most six, with exact/prefix ticker matches before company substrings. Watchlist selects a ticker then exposes a separate Follow action; Explore opens stock research. Recent history is browser-local, most recent first, capped at eight. Every visible item has X; X removes only that item immediately without navigation. Clear history appears for multiple entries and closes the panel. Menus have bounded height and preserve keyboard navigation, Escape and outside dismissal.

Actual browser checks: desktop dark/light Explore hero and index chart; mobile 390 x 844 dark/light Explore, News and Watchlist; no horizontal overflow. Mobile VI search returned VIB, VIC, VID, VIE, VIF, VIG with six options in a 222 px list. News navigation order and absent Hot Topics were checked on rendered DOM and screenshots.

Watchlist flow completed: empty focus, PN partial search, PNJ selection, separate Follow PNJ, reload membership persistence, another VIB search, shared history, X removing VIB without navigating, reload preserving other entries, Clear history. The test-added PNJ membership was removed afterwards. Explore VC -> VCG with ArrowDown/Enter opened actual VCG research. Final VCG test-history removal preserved the Explore URL and closed the list.

Screenshots: C:/Users/PC/.codex/visualizations/2026/10/07/explore-v2/ (outside repository).

## Regression and review

- uv run pytest -q: 531 passed, 1 existing Starlette/httpx deprecation warning, 40.11 s.
- npm test: 43 passed, 0 failed.
- npm run typecheck: exit 0.
- npm run build: exit 0; 9 static pages generated, index research route included.
- git diff --check: passed.
- Standards review: no remaining substantive documented-standard violation.
- Spec review: no remaining blocker after casing/accent and analyst-attribution corrections; 11 focused correction tests passed.

SSI stock OHLC normalization, completed-session logic, Technical/Technical Materiality, Fundamentals, Community ingestion/Momentum and historical retention were not changed. The only SSI provider extension maps two existing index summary aggregate fields.

## Limitations and cleanup

Headline/canonical-name coverage is intentionally conservative; aliases and overseas relevance recognition remain partial. Historical daily index trading value is not supplied by the OHLC endpoint and is explicitly unavailable. News source status was stale (0/10 healthy) because the ingestion worker was stopped; HTTP refresh does not run ingestion. No worker was started for this correction. Live image fallback was covered by tests rather than a naturally missing representative image.

All repository local backend/frontend test servers, including the previously running frontend on port 3000, were stopped as requested. No repository ingestion worker remained running. Unrelated untracked files and the pre-existing generated frontend/next-env.d.ts dev-import change were preserved and excluded from this checkpoint.

NEXT: Review a small labelled sample of real publisher headlines to expand canonical issuer aliases and Vietnam relevance coverage safely.
