# SECTION 1 SPEC — Data & Analytics Foundation

## 0. Mục tiêu của Section 1

Biến project từ **Day 0 scaffold** thành một vertical slice có dữ liệu tài chính thật chạy end-to-end.

Sau Section 1, user phải có thể:

1. Chọn hoặc nhập một ticker hợp lệ trong phạm vi hệ thống.
2. Backend lấy dữ liệu thật qua `vnstock`.
3. Dữ liệu được normalize về schema nội bộ của project.
4. Backend tính một số market/fundamental analytics bằng code deterministic.
5. Frontend hiển thị được dữ liệu thật của ticker.
6. Hệ thống vẫn giữ thiết kế **dynamic ticker**, không hard-code 3 mã demo.
7. Có tests đủ để chứng minh provider, analytics và API hoạt động ổn định.

Section này **chưa có Materiality Engine, AI Agent, LLM explanation, thesis, RAG, portfolio, email**.

Mục tiêu duy nhất:

> **Ticker → Real Data → Normalized Data → Analytics → API → Explore UI**

---

# 1. Nguyên tắc bắt buộc

## 1.1 Dynamic ticker

Không được viết logic kiểu:

```python
if ticker == "FPT":
    ...
elif ticker == "MBB":
    ...
```

Ticker phải là data/entity động.

3 mã như FPT/MBB/HPG chỉ được dùng làm:

- seed/demo data;
- fixtures;
- integration smoke tests;
- evaluation examples sau này.

Không được dùng chúng làm giới hạn kiến trúc.

---

## 1.2 `vnstock` là primary provider

Không dùng SSI FastConnect.

Primary provider cho Section 1:

```text
vnstock
```

Nhưng toàn bộ app không được phụ thuộc trực tiếp vào API/schema của `vnstock`.

Phải giữ abstraction:

```text
Application
    ↓
MarketDataProvider / FundamentalsProvider / NewsProvider
    ↓
VnstockProvider
    ↓
vnstock
```

Nếu Day 0 đã có provider abstraction thì **reuse**, không tạo hierarchy trùng lặp.

---

## 1.3 Normalize trước khi dùng

Không được để:

```text
vnstock DataFrame
→ frontend trực tiếp
```

Phải đi qua schema nội bộ.

Ví dụ:

```text
vnstock
↓
provider adapter
↓
normalized project schema
↓
service / analytics
↓
API
↓
frontend
```

Mục tiêu:

- dễ đổi provider sau này;
- analytics không phụ thuộc package ngoài;
- tests dễ mock;
- frontend nhận contract ổn định.

---

## 1.4 Deterministic analytics

Các metric số phải được tính bằng Python/code.

LLM tuyệt đối chưa tham gia Section 1.

Ví dụ:

```text
OHLCV
↓
Python
↓
MA20
RSI14
20D return
Relative volume
```

Không dùng AI để:

- tính chỉ số;
- suy luận số liệu;
- điền dữ liệu thiếu;
- tạo giá trị giả.

---

# 2. Phạm vi dữ liệu

Section 1 chỉ cần đủ dữ liệu phục vụ Section 2 — Materiality Engine.

Không cố xây terminal chứng khoán hoàn chỉnh.

---

# 3. Market Data

## 3.1 Required raw fields

Normalized daily OHLCV:

```text
ticker
date
open
high
low
close
volume
source
```

Optional nếu provider có sẵn và đáng tin:

```text
adjusted_close
exchange
```

Không bắt buộc realtime.

Daily data là đủ cho MVP.

---

## 3.2 Required analytics

Tính bằng `pandas` / `numpy`.

Bắt buộc:

```text
daily_return
return_5d
return_20d
ma20
ma50
rsi14
avg_volume_20d
relative_volume_20d
volatility_20d
drawdown_from_20d_high
```

Không thêm hàng chục indicator khác.

Nếu indicator cần warm-up period, API phải trả `null` thay vì fake value.

---

## 3.3 Market analytics principles

Functions phải:

- pure/deterministic khi có thể;
- không gọi network;
- nhận normalized data;
- trả output có schema rõ;
- unit test được.

Logical boundary:

```text
provider fetch
↓
normalized OHLCV
↓
analytics module
↓
MarketSnapshot
```

---

# 4. Fundamental Data

## 4.1 Required normalized fields

Không cần full financial statements.

Bắt đầu với:

```text
ticker
period
revenue
net_profit
gross_margin
net_margin
roe
source
```

Nếu một field không tồn tại hoặc không reliable:

```text
null
```

Không suy đoán.

---

## 4.2 Required derived metrics

Nếu đủ dữ liệu:

```text
revenue_growth_yoy
net_profit_growth_yoy
gross_margin_change
net_margin_change
roe_change
```

Nếu provider đã trả metric nhưng project có thể tính lại từ raw inputs, ưu tiên deterministic calculation nội bộ để giữ logic kiểm soát được.

---

## 4.3 Sector-specific metrics

**Chưa implement sâu ở Section 1.**

Chỉ chuẩn bị architecture để sau này thêm:

```text
Bank:
NIM
NPL
CASA
...

Retail:
inventory
store growth
...
```

Không thêm lúc này trừ khi code hiện tại đã support rất tự nhiên.

---

# 5. News Data

## 5.1 Goal

Section 1 chưa cần news intelligence.

Chỉ cần normalized news ingestion đủ để Section 2 sau này classify Material / Potentially Relevant / Noise.

---

## 5.2 Required normalized fields

```text
id
ticker
published_at
title
summary_or_content
source
url
```

Nếu nguồn không có full article:

- lưu title;
- lưu snippet/summary nếu hợp pháp;
- không fabricate body.

---

## 5.3 Source rule

Ưu tiên:

1. `vnstock` nếu có nguồn news phù hợp;
2. public source ổn định mà project được phép dùng;
3. local fixture/sample dataset nếu live news source chưa ổn.

Không dành nhiều thời gian viết crawler phức tạp.

Không scrape trái điều khoản sử dụng.

Nếu live news chưa ổn định, Section 1 vẫn có thể PASS với:

```text
normalized news fixtures + provider interface
```

miễn market/fundamental data thật đã chạy.

---

# 6. Internal Schemas

Codex phải kiểm tra model/schema Day 0 trước.

Không tạo duplicate nếu đã tồn tại.

Nếu chưa có equivalent, cần logical schemas tương đương:

## 6.1 Stock

```text
id
ticker
name
exchange
sector
is_active
created_at
updated_at
```

Ticker unique.

---

## 6.2 MarketBar

```text
ticker
date
open
high
low
close
volume
source
```

Unique logical key:

```text
ticker + date + source
```

---

## 6.3 MarketSnapshot

API-facing object:

```json
{
  "ticker": "FPT",
  "as_of": "YYYY-MM-DD",
  "close": 0,
  "daily_return": 0,
  "return_5d": 0,
  "return_20d": 0,
  "ma20": 0,
  "ma50": 0,
  "rsi14": 0,
  "avg_volume_20d": 0,
  "relative_volume_20d": 0,
  "volatility_20d": 0,
  "drawdown_from_20d_high": 0,
  "source": "vnstock"
}
```

Actual values phụ thuộc data thật.

---

## 6.4 FundamentalSnapshot

```json
{
  "ticker": "FPT",
  "period": "FY/Q",
  "revenue": null,
  "net_profit": null,
  "revenue_growth_yoy": null,
  "net_profit_growth_yoy": null,
  "gross_margin": null,
  "gross_margin_change": null,
  "net_margin": null,
  "net_margin_change": null,
  "roe": null,
  "roe_change": null,
  "source": "..."
}
```

Không bắt buộc tất cả field non-null.

---

## 6.5 NewsItem

```json
{
  "id": "...",
  "ticker": "FPT",
  "published_at": "...",
  "title": "...",
  "summary_or_content": "...",
  "source": "...",
  "url": "..."
}
```

---

# 7. Provider Contracts

Không khóa vào exact function name nếu Day 0 đã có interface khác.

Codex phải map requirement này vào architecture hiện tại.

Logical capabilities:

```text
MarketDataProvider
- get_history(ticker, start, end)
- get_latest(ticker)

FundamentalsProvider
- get_fundamentals(ticker)

NewsProvider
- get_news(ticker, limit)
```

Nếu Day 0 đang có một unified provider thì giữ unified provider.

Không refactor chỉ để khớp tên trong spec.

---

# 8. Ticker Management

## 8.1 Không hard-code universe

Phải có cơ chế để thêm stock mới.

Có thể:

```text
POST /stocks
```

hoặc reuse endpoint Day 0.

Input tối thiểu:

```text
ticker
```

Optional:

```text
name
exchange
sector
```

Nếu có thể xác minh ticker thông qua provider:

- validate;
- normalize uppercase;
- reject invalid ticker cleanly.

Nếu provider không hỗ trợ reliable validation:

- vẫn cho add ticker;
- first data fetch quyết định ticker usable hay không;
- trả lỗi rõ ràng.

---

## 8.2 Ticker rules

```text
fpt → FPT
 FPT  → FPT
```

Ticker unique case-insensitive.

Không duplicate seed khi chạy lại.

---

# 9. API Contracts

Reuse router structure Day 0 nếu phù hợp.

Recommended capabilities:

```text
GET /stocks
POST /stocks
GET /stocks/{ticker}

GET /stocks/{ticker}/market
GET /stocks/{ticker}/history
GET /stocks/{ticker}/fundamentals
GET /stocks/{ticker}/news
GET /stocks/{ticker}/overview
```

`/overview` có thể aggregate:

```text
stock
latest market snapshot
latest fundamentals
latest news
```

Không có AI insight.

---

# 10. API Error Behavior

Ticker không tồn tại:

```text
404
```

Provider unavailable:

```text
502 hoặc handled service error
```

Insufficient history:

```text
200
```

với indicator chưa đủ dữ liệu là:

```text
null
```

Không dùng fake fallback number.

Network/provider exception không được leak raw traceback ra client.

---

# 11. Explore Frontend

Section 1 chỉ cần **functional UI**.

Không dành thời gian polish.

User cần có thể:

```text
select/search ticker
↓
open stock Explore page
```

Page hiển thị tối thiểu:

## Header

```text
Ticker
Company name nếu có
Latest close
Daily return
```

## Market

Basic chart:

```text
close price history
```

Nếu Day 0 frontend đã có chart dependency thì reuse.

Không cần candlestick đẹp nếu mất nhiều thời gian.

## Technical / Market Metrics

```text
20D return
MA20
MA50
RSI14
Relative volume
Volatility
```

## Fundamentals

```text
Revenue
Revenue growth
Net profit
Profit growth
Margins
ROE
```

Chỉ hiển thị fields có data.

## News

Simple list:

```text
published_at
title
source
```

Không AI summary.

---

# 12. Database / Persistence

Day 0 chưa verify PostgreSQL thật.

Section 1 phải xác nhận ít nhất một path persistence thực tế.

Nếu PostgreSQL config đã có:

- chạy migration/create schema;
- seed;
- save/retrieve stock records;
- verify one real persistence flow nếu architecture Day 0 đã dự kiến persistence.

Không bắt buộc persist toàn bộ historical OHLCV nếu điều đó làm phức tạp Section 1 quá mức.

Minimum acceptable:

```text
PostgreSQL stores stocks / app entities
```

Market/fundamental fetch có thể on-demand + cache/service layer.

Không thêm Redis.

---

# 13. Docker

Docker **không block Section 1**.

Nếu Docker Engine đang chạy và setup dễ:

- verify backend container;
- verify frontend nếu đã config.

Nếu Docker tiếp tục gây environment issue:

- ghi rõ trong Section 1 report;
- không trì hoãn data vertical slice.

Docker end-to-end sẽ được gate ở release section.

---

# 14. Tests

## 14.1 Existing tests

Không làm regress 17 tests Day 0.

Tất cả existing tests phải tiếp tục pass.

---

## 14.2 Unit tests — analytics

Bắt buộc deterministic.

Không gọi internet.

Fixtures synthetic/local.

Test ít nhất:

```text
daily_return
return_20d
ma20
ma50
rsi14
relative_volume_20d
volatility_20d
drawdown_from_20d_high
```

Test:

- normal case;
- insufficient history;
- missing/invalid rows nếu relevant;
- zero/empty volume edge case nếu cần.

---

## 14.3 Provider unit tests

Mock `vnstock`.

Validate:

```text
external output
↓
normalized internal schema
```

Không test internals của vnstock.

---

## 14.4 API tests

Test ít nhất:

```text
valid ticker
invalid ticker
market endpoint
fundamental endpoint
news endpoint
overview endpoint nếu implement
```

Network/provider calls mock trong default test suite.

---

## 14.5 Integration / smoke test

Tạo integration test hoặc script riêng, KHÔNG chạy mặc định trong unit test suite nếu cần internet.

Ví dụ:

```bash
python scripts/smoke_vnstock.py FPT
```

Phải:

1. gọi vnstock thật;
2. fetch market history;
3. normalize;
4. calculate analytics;
5. print concise success summary;
6. exit non-zero nếu fail.

Có thể test thêm 1–2 ticker.

---

# 15. Data Freshness / Provenance

Mọi output quan trọng phải có:

```text
source
as_of / period
```

Không cần full provenance system.

Nhưng không được trả metric mà không biết nó thuộc kỳ nào/ngày nào.

---

# 16. Logging

Provider failures phải log đủ để debug:

```text
ticker
provider
operation
error type
```

Không log:

- secret;
- API key;
- `.env`;
- sensitive config.

---

# 17. Performance

Không optimize sớm.

Frontend chỉ gọi backend.

Nếu `/overview` tạo quá nhiều provider calls thì để simple trước, optimize sau khi đo.

Không thêm queue/background worker.

---

# 18. Không làm trong Section 1

Tuyệt đối chưa implement:

```text
Materiality Engine
event scoring
Monitoring Baseline weighting
Watchlist intelligence
Attention Budget
OpenAI
Agents SDK
LLM explanation
Thesis
RAG
pgvector workflow
PDF upload
Portfolio
Email alerts
price prediction
BUY / SELL / HOLD
auto trading
multi-agent
Celery
Redis
Kafka
```

Nếu code Day 0 đã có scaffold cho một số phần thì giữ scaffold, nhưng không phát triển.

---

# 19. Section 1 Demo Flow

Demo cuối section phải chạy:

```text
1. User mở app
2. Search/select ticker
3. Nếu ticker chưa có → add
4. Backend fetch data thật qua vnstock
5. Explore page hiện:
   - price history
   - market metrics
   - fundamentals
   - news hoặc normalized news fixture
6. User đổi ticker
7. Cùng pipeline chạy mà không sửa code
```

Phải demo ít nhất:

```text
3 tickers khác nhau
```

nhưng architecture support ticker động.

---

# 20. Capability Gate — Definition of Done

Section 1 chỉ PASS nếu:

- [ ] Existing Day 0 tests vẫn pass
- [ ] `vnstock` market fetch thật hoạt động với ít nhất 3 ticker
- [ ] Ticker mới có thể thêm mà không sửa source code
- [ ] Không có ticker-specific branching trong business logic
- [ ] Dữ liệu vnstock được normalize về internal schemas
- [ ] Market analytics được tính deterministic bằng code
- [ ] Analytics có unit tests
- [ ] Fundamentals trả dữ liệu normalized hoặc `null` rõ ràng nếu thiếu
- [ ] News có normalized contract
- [ ] Explore page hiển thị data thật cho nhiều ticker
- [ ] Frontend không gọi vnstock trực tiếp
- [ ] Provider/network errors được xử lý sạch
- [ ] PostgreSQL path cơ bản được verify nếu local DB khả dụng
- [ ] Frontend build pass
- [ ] TypeScript pass
- [ ] Test suite pass
- [ ] Repo git clean sau commit

Nếu một item core data path fail, không sang Section 2.

---

# 21. Deliverables Codex phải tạo / cập nhật

Không tạo file dư thừa nếu repo đã có equivalent.

Bắt buộc cuối task:

```text
working code
tests
README update
docs/SECTION1_REPORT.md
```

`SECTION1_REPORT.md` phải ghi:

```text
1. What was implemented
2. Final architecture/data flow
3. Files changed
4. vnstock capabilities actually used
5. Supported normalized fields
6. Test results
7. Frontend build result
8. PostgreSQL verification status
9. Docker verification status
10. Known limitations
11. Commands to run locally
12. Example API requests
13. Next section readiness
```

---

# 22. Git Requirements

Sau khi toàn bộ acceptance criteria đạt:

```text
git status
```

phải clean.

Commit suggested:

```text
feat: add vnstock data and analytics foundation
```

Push lên:

```text
main
```

Chỉ push khi tests/build đã pass.

---

# 23. Instruction cho Codex

Trước khi code:

1. Đọc toàn bộ README hiện tại.
2. Đọc `docs/DAY0_REPORT.md`.
3. Inspect architecture Day 0.
4. Reuse models, routers, provider abstractions hiện có.
5. Không rewrite project structure nếu không có lý do kỹ thuật cụ thể.
6. Không tạo `app/main.py`.
7. Giữ duy nhất root `main.py` và một FastAPI app.
8. Kiểm tra API hiện tại trước khi tạo endpoint mới.
9. Không hard-code FPT/MBB/HPG trong logic.
10. Không implement bất kỳ feature Section 2 nào.

Trong quá trình implement:

- ưu tiên simplest working solution;
- giữ code readable;
- thêm type hints;
- không over-engineer;
- tests chạy offline mặc định;
- external provider calls nằm sau abstraction;
- document mọi assumption về vnstock.

Sau khi code:

1. Chạy backend tests.
2. Chạy frontend typecheck/build.
3. Chạy vnstock smoke test thật.
4. Verify dynamic ticker với nhiều mã.
5. Verify DB path nếu PostgreSQL khả dụng.
6. Viết `docs/SECTION1_REPORT.md`.
7. Commit.
8. Push.
9. Trả về concise report gồm:
   - commit hash;
   - tests;
   - build;
   - live vnstock result;
   - DB status;
   - limitations.

---

# 24. North Star của Section 1

Section 1 không nhằm chứng minh AI.

Nó nhằm chứng minh:

> **Hệ thống có một data foundation đáng tin cậy, dynamic và deterministic để Materiality Engine có thể được xây bên trên.**

Nếu một feature không giúp đạt mục tiêu đó, không làm trong Section này.
