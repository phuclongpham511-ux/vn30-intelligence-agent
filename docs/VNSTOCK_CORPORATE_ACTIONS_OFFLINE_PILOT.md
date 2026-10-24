# Vnstock corporate actions — offline integration pilot

Ngày: **24/10/2026**. Nhánh `feature/financial-data-intelligence`; baseline `6f757cd7f9a645f154bb7337e7cdc6c772df855c`. Đây là phần triển khai nhỏ theo mission “WOOFI VNSTOCK CORPORATE ACTIONS OFFLINE INTEGRATION PILOT”, không phải V5.14 hoặc activation nguồn dữ liệu mới.

## Spec và ranh giới kiểm thử

Mục tiêu: nhận tối đa20 source fixture records dạng SDK event và trả `CorporateActionNotice` hiện có, chứng minh repository và `StockActions` hiện có nhận được mà không tạo storage/route/frontend mới.

Seams được xác định từ các yêu cầu1,8,9 của mission:

1. Pure adapter → `CorporateActionNotice`: kiểu sự kiện, tiền/tỷ lệ, ngày, ownership và nguyên trạng raw evidence.
2. `CorporateActionRepository.ingest/get_actions_for_symbol` → idempotency, immutable revisions, as-of và omission không phải cancellation.
3. Existing `GET /stocks/{symbol}/corporate-actions` response → current StockActions presentation/renderer EN/VI, giữ trust gates và fixture disclosure.

Không thay existing schemas, repository, financial journal, SSI/OHLC, routers, production configuration hoặc component UI. Không import/call live vnstock SDK. Chỉ dùng fixtures tổng hợp, không dùng private capture/PDF/credentials. Bảng vocab dưới đây là **hợp đồng pilot**, không phải sự xác nhận vocab provider thực tế.

## MAPPING_CONTRACT

Version: **`vnstock-vci-events-offline-v1`**.

Implementation: `src/providers/vnstock/corporate_actions.py`, public seam:

```python
normalize_event(row, requested_symbol=..., semantics_reference=...,
                amount_unit=None, ratio_basis=None)
```

Pure function: không đọc file, gọi mạng/SDK, ghi DB, tìm bản mới nhất hoặc reconcile một source response. Nó trả schema có sẵn; caller kiểm thử mới chuyển notice sang repository trong SQLite in-memory.

Input là một dict JSON finite, keys dạng string, raw JSON tối đa4000 ký tự. `semantics_reference` bắt buộc, ghi nguồn khai báo ý nghĩa cho fixture; không được hiểu thành upstream verification. Mapped evidence phải vừa giới hạn6000 ký tự hiện có. Không chấp nhận timestamp/epoch rồi âm thầm chuyển thành ngày, không tự sanitize NaN thành0.

Nguồn thiết kế: AGENTS/CONTEXT/DESIGN; §8 của nghiên cứu ecosystem; schema/repository hiện có; source đã cài `vnstock==4.0.2` trong `.venv/Lib/site-packages/vnstock/explorer/vci/company.py:637–716`; [official Reference events contract đã đọc trong nghiên cứu](https://vnstocks.com/docs/vnstock/tham-chieu-reference).

SDK4 gọi default page0,size50, request khoảng10 năm nhưng không loop pages; public events bỏ symbol và chuyển một số trường ngày. Vì vậy pilot nhận requested-symbol context tường minh và không suy history completeness từ khoảng request. Không gọi private `_fetch_events`.

## SUPPORTED_EVENT_TYPES

| Code + explicit action type | Woofi type | Terms được phép |
|---|---|---|
| DIV + Cash dividend / Cổ tức bằng tiền | cash_dividend | value_per_share khi declared VND/share |
| DIV + Stock dividend / Cổ tức bằng cổ phiếu | stock_dividend | exercise_ratio với basis đã khai báo |
| ISS + Bonus shares / Cổ phiếu thưởng | bonus_shares | exercise_ratio với basis đã khai báo |
| ISS + Rights offering / Quyền mua cổ phiếu | rights_offering | ratio; subscription price vẫn missing |

So khớp vocab sau trim/casefold; mọi label được cung cấp phải thuộc whitelist và thống nhất với nhau/code. Không parse title, generic event name, tỷ lệ ghi trong prose hoặc ticker-specific conditions để đoán loại. Unknown type, conflicting labels/code bị reject. Các label synthetic này chưa được kiểm chứng bằng response live.

Tất cả output bị khóa **`is_fixture=True`, `verified=False`, `withdrawn=False`**. Thành công normalize không nâng quyền công khai hoặc cấp source verification. Adapter không có option bật verified/live.

## UNSUPPORTED_FIELDS

- Subscription price của rights: không coi `value_per_share` là giá đăng ký khi semantics chưa được xác nhận; giữ raw field, `subscription_price_vnd=None`.
- Non-cash `payout_date`: giữ raw, chưa map sang payment/listing/credit date của cổ phiếu.
- Display/issue/start/end/listing dates, generic category/event-name và mọi extra fields: giữ trong raw evidence và liệt kê `unmapped_fields`; không dùng chúng lấp các ngày trống.
- Source URL, provider update timestamp, original publication timestamp, explicit cancellation và correction linkage chưa có contract đủ: không tự tạo URL/timestamp/trạng thái.
- Các loại additional issuance/other, ratio string như10:1, unknown ratio basis, timestamp/epoch/date mơ hồ: không tự diễn giải; loại/term/date liên quan bị reject theo reason code.
- Không tuyên bố hỗ trợ trực tiếp DataFrame chứa NumPy scalars/NaN; boundary hiện là dict JSON sạch được khai báo, chưa có acquisition/DataFrame converter.

Unsupported field còn nguyên trong `evidence_text`, không có nghĩa raw financial fact đã được hiểu hay đủ điều kiện hiển thị. Raw event title VI/EN vẫn được giữ, không dịch source evidence.

## SOURCE_IDENTITY

- `source = vnstock:VCI:events`.
- `source_id = <requested_symbol>:<vendor_id>`; row id bắt buộc, không bịa từ ngày/title.
- `component_id = event`, để đính chính classification không tự tạo action khác.
- Nếu raw có symbol thì phải bằng normalized requested symbol; thiếu raw symbol được ghi nhận bằng raw record và request context, không coi context là xác minh owner độc lập.
- Evidence envelope dùng existing `evidence_text`: mapping version, static SDK reference, exact raw fields, canonical raw-record SHA-256, requested symbol, declared amount/ratio basis và semantics reference.
- `source_revision` là hash của envelope, không bao gồm receipt time. Đây là hash canonical JSON, **không phải hash bytes PDF/HTTP capture gốc**. Không tạo capture store hoặc thay schema để chứa evidence.

`source_url=None`, `source_updated_at=None` khi không có evidence đủ; không dùng documentation URL làm original-event URL. UI hiện có chấp nhận missing URL.

## REVISION_BEHAVIOR

Existing repository tự tính action/observation identities và lưu append-only. Pilot không thay luật repository:

1. Cùng raw + declarations/version, receipt time mới → `duplicate`, cùng observation id.
2. Cùng source identity, amount/payment date thay đổi → `revision`; bản cũ vẫn đọc được theo as-of.
3. Classification correction cùng id → vẫn một action identity, một revision mới; ngày/terms của revision cũ không chảy sang bản sửa.
4. Mapping/declaration/raw evidence thay đổi được coi là content revision có thể inspect; đổi receipt time riêng không đổi content.
5. Response capped/partial hoặc một lần không trả lại event cũ không gây delete/withdraw. Adapter không có API reconcile/cancel; test nhận một event khác và xác nhận event cũ còn `withdrawn=False`.

Explicit source cancellation/correction-link semantics của provider thực tế vẫn là blocker; không giả lập nó thành tính năng live đã có.

## DATE_SEMANTICS

| Input | Existing notice field | Quy tắc |
|---|---|---|
| exright_date | effective_date | ISO calendar date trực tiếp; không tính từ record date |
| record_date | record_date | Không dùng display date thay thế |
| payout_date, cash only | payment_date | Là ngày nguồn ghi/kế hoạch, không chứng minh đã thanh toán |
| public_date | announced_on | Giữ date precision; announced_at không được tạo midnight |
| Các field thiếu/null/empty date | None | Không fabricated dates hoặc forward fill |

Reject ngày lịch sai, date strings không đúng YYYY-MM-DD, timestamp/epoch chưa biết quy ước, ex-date sau record date hoặc cash payment trước record date. Không áp quy tắc calendar/trading-day offset. Receipt/knowledge time do repository nhận riêng.

## UNIT_AND_RATIO_VALIDATION

Cash numeric amount chỉ được map khi caller khai báo `VND/share` và có semantics reference. Không suy đơn vị từ giá trị, tên mã, mệnh giá hoặc phần trăm. Unknown/missing required unit bị reject; source thiếu amount vẫn giữ None. Cash0 thật được giữ0, không lẫn với missing.

Share ratio chỉ map khi có một trong hai declaration:

- `fraction_new_per_old`:0.2 nghĩa là0.2 cổ phiếu mới/cũ trong fixture.
- `percent_new_per_old`:10 được chuyển thành0.1; nguồn và declaration vẫn nằm trong envelope.

Không nhận ratio string/old:new chưa rõ chiều. Reject bool, nonnumeric, nonfinite, negative/out-of-exact-frontend-range numbers và share ratio≤0. Thiếu ratio được giữ None, không suy từ title hoặc cash value. Không scale `value_per_share` sang cash cho stock/bonus/rights.

Các declaration trên là bằng chứng của **fixture contract**, không chứng minh original provider unit. Đây là lý do output không được verified.

## FRONTEND_CONTRACT_COMPATIBILITY

Không đổi frontend production. Backend tests dùng client/DB memory hiện có; frontend test chạy Python adapter → existing repository memory → existing GET reader và FastAPI JSON encoding → actual StockActionsView cùng `actionDate/actionTerm/trustedAction`.

Kiểm tra cả EN/VI: đúng ticker/shape/coverage, đủ bốn loại, raw evidence và DEMO còn inspectable; source amount/ratio/date chưa qua trust gate không trở thành confirmed facts. UI compatibility không phải chứng nhận public redistribution hoặc browser visual acceptance. Không mở browser/server trong task.

## Fixtures và TEST_RESULTS

File `tests/fixtures/vnstock_corporate_actions_v1.json` có **đúng20 synthetic input records**, không có amount/record thật. Chín records normalize được (có partial và corrections),11 records phải reject. Lặp test/bridge tái dùng đúng bundle này; không acquire records mới. Các regression fixtures của repo không bị thay đổi.

Coverage: cash/stock/bonus/rights; original và corrected amount/payment/type; explicit0 và missing amount/ratio/dates; unit/basis declarations; conflict/unknown type; bad date/order/precision; missing id; owner mismatch; numeric bool; textual ratio. Tests bổ sung thay declaration trên cùng record để kiểm tra foreign unit/unsupported basis/missing semantic reference.

TDD: cash test ban đầu fail vì chưa có module → green; share-type slice fail do mapper mới hỗ trợ cash → bổ sung tối thiểu → green. Sau đó kiểm định existing repository/GET/renderer seams mà không sửa chúng. Frontend bridge đã sửa encoding UTF-8 của subprocess Windows và JSON serialization trong harness; không đổi ứng dụng để làm tests pass.

Commands chỉ chạy offline, không migration/acquisition:

```powershell
.\.venv\Scripts\python.exe -B -m pytest tests/test_vnstock_corporate_actions_offline.py -q -p no:cacheprovider
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider
cd frontend
node --test tests/*.test.mjs
```

- Focused backend corporate-action/free-source/SSI regressions: **143 passed**, gồm21 pilot tests.
- Focused StockActions/presentation/bridge: **22 passed**, gồm2 bridge tests.
- Full frontend regression: **340 passed,1 existing skip**,0 failed.
- Full backend regression: **1.748 passed +32 subtests passed**,0 failed (288,30 giây).
- Bridge sau khi thêm network-denial guard: **2 passed**; subprocess cấm socket connections và xác nhận external `vnstock` SDK không được import.
- Existing Starlette/httpx deprecation warning không được xử lý bằng dependency upgrade trong pilot.

Test DB chỉ là SQLite in-memory/temporary fixtures; main financial SQLite không được mở ghi. Không thay SSI adjusted OHLC hoặc công thức engine.

## INTEGRATION_BLOCKERS và LIVE_PILOT_PREREQUISITES

Trước một nhiệm vụ live được duyệt riêng cần:

1. Provider sample hợp lệ xác nhận exact labels/code, stable id scope, response fields và completeness/page cap; không dùng private endpoint/paging workaround.
2. Units/basis thật cho cash/share/rights, source dates/timezone, payment semantics; xác nhận cách nhận explicit corrections/cancellations và source link/update timestamp.
3. Quyền sử dụng phần mềm/dữ liệu, cache/display/redistribution được xác nhận phù hợp use case; không suy từ sponsor hoặc normalized output.
4. Request budget/serial pacing, error handling và owner-approved phạm vi; không tự bật acquisition/public API wiring.
5. New mapping version nếu thay nghĩa/vocab; idempotency/revision/contract regression trước khi nhập nguồn thật. Fixture-only adapter hiện tại không có nút bật live/verified.

Giá trị chứng minh: **existing contracts chứa được bốn nhóm sự kiện với evidence, missingness và revisions**, không cần thêm storage system. Những gì chưa chứng minh: coverage/freshness/semantic correctness của VCI live, public data rights hoặc operational rollout.

## Delivery và bảo toàn

CODE_CHANGED: YES — chỉ thêm pure adapter và tests/fixtures; không đổi code production hiện có.

DATABASE_CHANGED: NO — persistent production/private journals giữ nguyên; ephemeral test DB là phạm vi kiểm thử.

COMMIT_HASH: xem delivery message/git log; commit riêng các file pilot sau tests/review, không đưa nghiên cứu/tooltip/private files không liên quan vào commit.

PUSH_STATUS: NOT PUSHED. Không merge, đổi branch, upgrade SDK hoặc bắt đầu V5.14.

Protected baseline gồm financial DB, pin/lock, CONTEXT, hai tooltip files, next-env và bốn báo cáo/note chưa commit; được so SHA-256 trước/sau. Các báo cáo nghiên cứu hiện có được giữ nguyên.

## Standards

**0 findings.** Review độc lập xác nhận reuse schema/terms/repository, raw evidence và fixture flags, missingness, dynamic symbols và phạm vi không sửa production. Không có baseline smell đáng đưa thêm abstraction/refactor vào pilot. Căn cứ: AGENTS, CONTEXT, frontend/AGENTS và DESIGN.

## Spec

**0 actionable findings.** Review độc lập xác nhận đủ20 synthetic records/bốn loại, explicit units/ratios, rejection, dates, idempotency/revisions/as-of, omission không là cancellation và actual EN/VI StockActions bridge. Các giới hạn live vocab, identity, completeness, correction/cancellation và rights được ghi rõ, không bị trình bày thành kết quả đã kiểm chứng.

Hai review chỉ đọc diff kể từ baseline, không chạy lại app/tests/network, đọc private captures hoặc sửa worktree. Source/tests đã qua review không đổi; chỉ bổ sung kết quả review vào tài liệu bàn giao.

Review summary: Standards0, worst issue none; Spec0, worst issue none.
