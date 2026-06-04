---
name: run-tests
description: Logic tái dùng để compile rồi chạy test với device preflight (real/emulator auto-detect) và tóm tắt report. Dùng bởi command run. Luôn compile trước; dùng scripts/run-*.sh (tự check device) thay vì gọi Maven thô khi có thể.
---

# Skill: run-tests

Năng lực tái dùng: chạy suite an toàn — compile trước, check device, chạy script phù hợp, tóm tắt kết quả.

## Thủ tục
1. **Xác định scope**: platform (android mặc định / ios / all) + suite (`testng/testng-android.xml` · `-ios` · `-all`) hoặc test/feature cụ thể.
2. **Compile trước** (cổng): `mvn clean compile test-compile`. Đỏ → báo lỗi, **KHÔNG** chạy tiếp (gợi ý skill `fix-by-layer`).
3. **Device preflight** (script tự lo, nhưng nắm cơ chế): đọc `deviceName` từ capabilities — `emulator-*` = emulator (chưa chạy → `./scripts/start-emulator.sh`, poll 5s, timeout 60s); ngược lại = real device (phải có trong `adb devices` / `xcrun xctrace list devices`, không thì abort).
4. **Chạy**: `./scripts/run-android.sh` · `./scripts/run-ios.sh` · `./scripts/run-all.sh` (khuyến nghị). Suite tuỳ chỉnh → `mvn test -DsuiteXmlFile=<suite>`.
5. **Báo kết quả**: exit code, report mới nhất trong `reports/<date>/`, tóm tắt passed/failed/skipped/duration.
6. **Triage mỗi FAIL** ([failure-triage.md](../../rules/failure-triage.md)) — **trước khi gợi ý `/fix`**: với mỗi test đỏ, phân định nguyên nhân gốc `[APP-BUG]` (app sai — báo dev, KHÔNG sửa test cho xanh) vs `[FRAMEWORK]` (locator/automation sai — `/fix`) vs `[ENV]`/`[DATA]`. Đối chiếu stack trace + screenshot trong ExtentReport (message đã mở đầu bằng nhãn). **Tóm tắt fail theo nhãn** (vd "3 fail: 1 [APP-BUG], 2 [FRAMEWORK]") để biết "app lỗi" hay "test lỗi". Chỉ FAIL nhãn `[FRAMEWORK]`/`[ENV]`/`[DATA]` mới gợi ý `/fix`; `[APP-BUG]` → liệt kê defect chuyển dev.

## Appium server — KHÔNG cần start thủ công cho `/run`
Test runtime dùng `AppiumServer.shared()` tự `usingAnyFreePort()` → start Appium trên **port trống bất kỳ**, không phụ thuộc port đang chạy. Vì vậy `/run` **không** gọi `start-appium.sh`. Muốn point sang server có sẵn (vd MCP 4723) → `export APPIUM_SERVER_URL=http://127.0.0.1:4723` trước khi chạy. (Server cố định 4723 + `start-appium.sh` chỉ dành cho **MCP exploratory**, xem skill `mcp-navigate`.)

> KHÔNG sửa test code — chỉ chạy. TestNG XML phải có `GoToHomeTest` là `<test>` block đầu tiên.
