---
description: Thực thi một plan (path file plan) hoặc một yêu cầu trực tiếp để code test theo đúng design pattern dự án
argument-hint: <path/tới/plan.md | mô tả trực tiếp việc cần làm>
allowed-tools: Read, Glob, Grep, Edit, Write, Bash, Agent
---

# /cook — Thực thi plan / yêu cầu

Input: **$ARGUMENTS**

## Phân loại input
- Path tới file `.md` trong `plans/` → đọc & thực thi đúng plan.
- Mô tả trực tiếp → tự suy ra việc cần làm & thực thi (việc lớn → tóm tắt bước trước khi code). Không có plan mà việc lớn → đề xuất `/plan` trước.

## Bắt buộc đọc trước khi code
- @${CLAUDE_PLUGIN_ROOT}/rules/design-pattern.md
- @${CLAUDE_PLUGIN_ROOT}/rules/coding-rules.md
- @${CLAUDE_PLUGIN_ROOT}/rules/design-system.md
- `sitemap/sitemap.md` + `screens/<group>/test-hints.json` (khi viết test)

## Quy trình chuẩn (LÀM ĐÚNG THỨ TỰ)

1. **Element lookup (3-layer)** ([design-pattern §2](../rules/design-pattern.md)) — resolve mọi element trước khi code:
   - **Layer 1** `screens/<group>/<Name>Screen.java` → field `@MobileFindBy` có sẵn? dùng luôn.
   - **Layer 2** `screens/<group>/elements.json` → có trong catalog? thêm vào Screen.
   - **Layer 3** MCP discovery (chỉ khi 1&2 miss): device preflight + start session qua **skill `mcp-navigate`** → spawn agent `source-inspector` → **skill `capture-elements`** chọn locator → **BẮT BUỘC** lưu `elements.json`.
2. **Khai báo Screen** — **skill `declare-screen`** (extends `BaseScreen`, locator priority `id>accessibility>uiautomator>xpath`, `isDisplayed()`, action = verb, **không assert**). Element thiếu `id` → **skill `missing-ids`** (RECORD).
3. **Models/TestData**: thêm record `models/` + provider `TestDataProvider` nếu cần.
4. **Test class**: viết FULL trong `tests/<group>/<Name>Test.java` (atomic → extends `BaseTest`; flow tổng hợp → `tests/regression|smoke/<group>/` extends `BaseRegression`). Init Screen trong `@BeforeClass(alwaysRun=true)` qua `requireDriver()`; `@Test(priority=n)`; mỗi step `report.createNode()` + `Utils.infoCap/passCap/failCap`. **Message `failCap` mở đầu bằng nhãn triage** khi đỏ do app (vd `Utils.failCap(driver, node, "[APP-BUG] ...")`) — xem [failure-triage.md §3b](../rules/failure-triage.md).
5. **TestNG XML**: `GoToHomeTest` là `<test>` block ĐẦU TIÊN; mỗi class cần ordering = 1 `<test>` block riêng; listener `TestResultCollector`.

## Sau khi code
- **skill `build-verify`**: `mvn clean compile test-compile` xanh (+ optional chạy nhanh feature). Lỗi → **skill `fix-by-layer`** tới khi xanh. **Test đỏ khi chạy thử ≠ luôn sửa test**: triage trước ([failure-triage.md](../rules/failure-triage.md)) — nếu là `[APP-BUG]` thì ghi defect chuyển dev + giữ test trung thực, KHÔNG nới assertion cho xanh; chỉ `[FRAMEWORK]`/`[ENV]`/`[DATA]` mới sửa.
- **skill `update-sitemap`**: với mỗi Screen tạo/sửa → cập nhật `elements.json` + `test-hints.json` + `sitemap/sitemap.md` + regenerate.
- **Missing ID Report** (skill `missing-ids`): in bảng element chưa có id (bỏ nếu tất cả có id).
- Liệt kê file đã tạo/sửa + lệnh chạy test. KHÔNG commit/push trừ khi được yêu cầu.

## Nguyên tắc
- Tái dùng `base`/`utils`/`actions`/`models` — không lặp code. Mỗi feature gói trong group riêng.
- Reference template: `LoginScreen.java` / `GoToHomeTest.java` (đọc trước khi tạo class mới).
- Plan tham chiếu element chưa có thật → dừng, đề xuất MCP discovery (Layer 3) hoặc `/exploratory` trước.
