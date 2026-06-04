---
description: Mở màn của một tính năng bằng Appium MCP, test thăm dò, trích element vào screens/<group> và xuất report
argument-hint: <ten-tinh-nang> [navigation path nếu biết]
allowed-tools: Read, Glob, Grep, Edit, Write, Bash, Agent
---

# /exploratory — Khám phá & tìm bug một tính năng (GATE cho việc viết test)

Tính năng cần khám phá: **$ARGUMENTS**

**Mục tiêu #1 — TÌM BUG**: thăm dò màn tính năng để **phát hiện lỗi app** và xuất **bug report gửi dev** đúng định dạng [exploratory-bug-report-template.md](../rules/exploratory-bug-report-template.md) (mẫu anh duyệt: `reports/exploratory/dev-bug-report-03Jun2026.md`).

**Mục tiêu #2 — Chuẩn bị cho test (CHỈ khi sạch)**: nếu tính năng **không có `[APP-BUG]`**, trích element → khai báo `screens/<group>` để `/plan`/`/cook` dựng test.

> ⚠️ **Luật cổng (GATE)**: *Automation chỉ hoạt động khi app đã đúng.* → **Tính năng có `[APP-BUG]` thì KHÔNG viết test** cho phần đó. exploratory phát hiện app lỗi/chưa hoàn thiện → **deliverable là bug report** (báo dev), KHÔNG tiến hành `/plan`/`/cook`. Chỉ feature **sạch** mới đi tiếp sang `/plan`.

> ⚠️ **App là bản port (SBH Flutter ← SBH Reactive), KHÔNG phải app chuẩn** → giả định mặc định là **app có thể đang lỗi**. Mọi quan sát sai/đỏ **MUST** phân định nhãn theo [failure-triage.md](../rules/failure-triage.md): `[APP-BUG]` (app sai — chặn test) vs `[FRAMEWORK]` (ta bắt element/automation sai) vs `[ENV]`/`[DATA]`. KHÔNG mặc định app đúng.

## Bước 0 — Chuẩn bị
- Xác định **group** (lowercase, vd `quản lý đơn` → `order`). Đọc `sitemap/sitemap.md` để biết navigation path từ Home.

## Bước 1 — Mở app & điều hướng (Appium MCP) — skill `mcp-navigate`
- **MCP Appium = port cố định 4723** (`.mcp.json`); chưa ready → `./scripts/start-appium.sh`. (Khác với `/run` — test runtime tự free-port qua `AppiumServer`.)
- Device preflight (`adb devices` / start emulator nếu cần).
- **Install app TRƯỚC** (MCP không install qua `app_path`): `adb install -r -g <appPath>` → check `pm list packages`. Verify `appPackage`/`appActivity` khớp APK (`aapt dump badging`).
- `appium_start_session(platform, device_name, app_package, app_activity)` — app đã cài, KHÔNG truyền app_path. UiAutomator2 đọc tốt semantics Flutter.
- **Về Home** (SBH): Welcome `accessibility "Bắt đầu ngay"` → nhập SĐT vào `class_name EditText` → `"Tiếp tục"` → nhập mật khẩu → `"Tiếp tục"` → Home. Account từ `configurations/test-users.json`, **không in mật khẩu**.
- **Dismiss popup** quyền thông báo: `id com.android.permissioncontroller:id/permission_deny_button`.
- Đi theo path sitemap tới màn feature → `appium_get_page_source` xác nhận đúng màn.

## Bước 2 — Khám phá & săn bug (exploratory testing)
Thử tương tác chính (mở/đóng, filter, tạo/sửa, **mở chi tiết item**, validate input rỗng/biên), **đọc kỹ số liệu/thông báo** (sai số, số âm, text tiếng Anh lọt, raw SQL/exception lộ ra UI). Ghi nhận: hành vi đúng/sai, crash, lỗi UI, edge case.
- **Screenshot bằng chứng bug** → `reports/exploratory/<group>/screenshots/`, **đặt tên theo BUG-ID** (vd `02-APP01-published-tab-sqlite-crash.png`). Mỗi `[APP-BUG]` ≥1 ảnh. Cũng lưu vài ảnh **màn OK** (đặt `..-ok.png`) làm bằng chứng "đã kiểm".
- Lỗi lộ text/SQL → trích **nguyên văn** (qua page source) để dán vào report.
- **[ENV] device**: máy thật không cắm sạc dễ doze tắt màn → gửi `KEYCODE_WAKEUP` trước mỗi thao tác, hoặc cắm sạc + bật Developer "Stay awake" (xem memory `device-doze-keyguard-env`).

**Triage tại chỗ** ([failure-triage.md](../rules/failure-triage.md)): mỗi khi thấy hành vi sai / màn lỗi / element không thấy → tái hiện thủ công ngay trên app để phân định: app thật sự lỗi (`[APP-BUG]` — chụp bằng chứng + bước tái hiện) hay chỉ là ta bắt element sai (`[FRAMEWORK]` — page source xác nhận element vẫn đúng) hay thiếu data/env (`[DATA]`/`[ENV]`). KHÔNG bỏ qua, KHÔNG đoán.

## Bước 2b — Đối chiếu design system (conformance) — skill `design-conformance`

Ngoài lỗi chức năng, kiểm tra UI có **đúng design system app** không (Material 3, brand `#16993B`) — mốc ở `sbh-app-design-system/`. Với mỗi loại UI gặp (nút, popup, dải nút chọn…): chụp screenshot → nạp `tokens.json` + `components/<loại>.json` liên quan → **nhìn ảnh đối chiếu** `referenceScreenshot` + `conformanceChecklist` (màu nền/chữ, bo góc, cỡ chữ, state-layer). App Flutter không cho đọc màu/font qua element → check **chủ yếu bằng ảnh** + structural (bounds: vùng chạm ≥48px). Lệch design → `[APP-BUG]` *design deviation* (theo [design-system-figma.md](../rules/design-system-figma.md)). Component chưa có spec (`manifest.json` = pending) → `[NEEDS-TRIAGE]`, không kết luận.

## Bước 3 — Trích element (CHỈ khi feature sạch) — skill `capture-elements`
> Bỏ qua/giảm tải bước này nếu feature có `[APP-BUG]` chặn (chưa viết test thì chưa cần Screen). Vẫn ghi nhận element nào không neo được (thiếu id) vào bug report.

Khi feature đủ sạch để dựng test: spawn agent `source-inspector` (`${CLAUDE_PLUGIN_ROOT}/agents/agent-source.md`) discover từ app thật → chọn locator ưu tiên `id > accessibility > uiautomator > xpath`. Đánh dấu element thiếu `id` cho Bước 4.

## Bước 4 — Khai báo Screen (CHỈ khi feature sạch) — skill `declare-screen`
Biến element thành Page Object (extends `BaseScreen`, `isDisplayed()`, action = verb, **không assert**). Element thiếu `id` → **skill `missing-ids`** (RECORD). Lưu `elements.json`. Cuối bước: **skill `build-verify`** (compile xanh).

## Bước 5 — Bug Report gửi dev (DELIVERABLE CHÍNH)
Ghi `reports/exploratory/<group>/dev-bug-report-<ddMMMyyyy>.md` **đúng định dạng** [exploratory-bug-report-template.md](../rules/exploratory-bug-report-template.md):
- Mỗi bug = 1 mục `## 🔴/🟡/ℹ️ BUG-N (<mức độ>) — <module>: <tiêu đề>` với: **Màn** (path từ Home) · **Hiện tượng** (trích nguyên văn lỗi/SQL/số liệu sai) · **Root cause** (nếu thấy được) · **Tác động** · **Kỳ vọng** · **Bằng chứng** (đường dẫn screenshot) · Defect ID.
- Mục **✅ Đã kiểm tra — KHÔNG lỗi** (bắt buộc — phạm vi đã cover).
- Mục **❓ NEEDS-TRIAGE** (quan sát chưa đủ bằng chứng) + **Ghi chú môi trường**.
- **Đồng bộ defect register**: append mỗi `[APP-BUG]` vào `reports/exploratory/bug-summary.md` (cấp APP-ID, cập nhật bảng đếm theo chức năng + phân bố mức độ).
- Chỉ `[APP-BUG]` mới lên mục bug; `[FRAMEWORK]`/`[ENV]`/`[DATA]` ghi ở register + ghi chú, KHÔNG coi là lỗi app.

## Bước 6 — Cập nhật sitemap (CHỈ khi feature sạch) — skill `update-sitemap`
Khi đã trích Screen/element: cập nhật `sitemap/sitemap.md` + `elements.json` + `test-hints.json` → regenerate. Chạy EXPORT của **skill `missing-ids`** (`scripts/export_missing_ids.py`).

## Bước 7 — QUYẾT ĐỊNH CỔNG (gate)
Dựa trên bug report, phân loại feature và in rõ kết luận:
- 🔴 **Có `[APP-BUG]`** → *feature CHƯA hoàn tất / đang lỗi*. **Deliverable = bug report** (`dev-bug-report-<ddMMMyyyy>.md`) + screenshots → **gửi dev**. **KHÔNG** chạy `/plan`/`/cook` cho phần lỗi (không viết test cho app sai). Nếu feature có phần sạch tách bạch → chỉ phần đó mới đi tiếp.
- 🟢 **KHÔNG `[APP-BUG]`** (chỉ có thể có FW/ENV/DATA) → *feature hoạt động đúng* → đã trích Screen/element ở Bước 3–6 → gợi ý **`/plan <ten-tinh-nang>`** để dựng bộ test.

## Kết thúc
`appium_quit_session`. In: đường dẫn **bug report** (+ register), danh sách `[APP-BUG]` (nếu có) cho dev, Screen/sitemap đã cập nhật (nếu sạch), và **kết luận gate** (gửi dev hay `/plan`).
