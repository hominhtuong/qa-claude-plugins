---
name: mcp-navigate
description: Logic tái dùng để dùng Appium MCP khởi động app, đảm bảo về Home (GoToHome thủ công), rồi điều hướng tới một màn feature theo sitemap. Dùng bởi command exploratory (mở màn để khám phá/bắt element) và fix (mở lại UI thật khi selector đổi để lấy locator đúng). Bao gồm device preflight + cách install app đúng cho MCP.
---

# Skill: mcp-navigate

Năng lực tái dùng: từ trạng thái trắng → đứng đúng màn feature trên thiết bị thật/emulator (Appium MCP), sẵn sàng cho `capture-elements`. Đây chính là luồng `GoToHomeTest` làm thủ công qua MCP.

## ⚠️ Hai Appium server độc lập — đừng nhầm
- **MCP (skill này dùng)**: server **cố định port 4723** theo `.mcp.json` (`APPIUM_PORT=4723`). Khởi động bằng `./scripts/start-appium.sh` (tự kill port cũ + start + chờ ready). MCP tool `appium_*` kết nối vào đây.
- **Test runtime (`/run`, KHÔNG phải skill này)**: `AppiumServer.java` tự `usingAnyFreePort()` → port trống bất kỳ (hoặc `APPIUM_SERVER_URL` nếu set). Không đụng 4723. → Đừng start-appium.sh cho `/run`.

## Thủ tục
1. **Device preflight**: `adb devices` (Android) / `xcrun simctl list devices` (iOS). Emulator cần mà chưa chạy → `./scripts/start-emulator.sh` (poll tới khi sẵn sàng).
2. **MCP Appium ready**: `curl -s http://127.0.0.1:4723/status` — chưa ready → `./scripts/start-appium.sh`.
3. **Install app TRƯỚC khi start session** (quan trọng):
   - MCP `appium_start_session` **KHÔNG** dùng được tham số `app_path` để install (báo lỗi *"Either provide 'app' option… or set noReset true"*). → **Cài thủ công**: `adb install -r -g <appPath>` rồi check `adb shell pm list packages | grep <appPackage>`.
   - `appPackage`/`appActivity` phải khớp APK thật — verify bằng `aapt dump badging <apk>` (`package: name=...`, `launchable-activity: name=...`). Sai package → session start nhưng launch fail.
4. **Start session** với app **đã cài sẵn**: `appium_start_session(platform=Android, device_name=<udid>, app_package=<pkg>, app_activity=<activity>)` — KHÔNG truyền app_path. Default automationName = UiAutomator2 (đọc tốt semantics Flutter qua content-desc).
5. **Tra sitemap trước** (không dò mò): đọc `sitemap/sitemap.md` để biết navigation path từ Home tới màn feature, element đặc trưng.
6. **Đảm bảo về Home** (flow đã verify cho SBH Flutter):
   - Welcome → tap `accessibility "Bắt đầu ngay"` → màn nhập SĐT.
   - Nhập SĐT vào `class_name android.widget.EditText` (ô input KHÔNG có id) → tap `accessibility "Tiếp tục"`.
   - Nhập mật khẩu vào `EditText` → tap `accessibility "Tiếp tục"` → Home.
   - **Account/OTP** lấy từ `configurations/test-users.json` (`phone`/`password`/`otp`) — **KHÔNG in mật khẩu** ra log.
   - Login bằng **password** (không OTP cho account sẵn có). Lạc state khác (OTP/onboarding) → xử lý như `GoToHomeTest`.
7. **Dismiss popup sau login**: app hay bật dialog quyền thông báo Android → tap `id com.android.permissioncontroller:id/permission_deny_button` (hoặc `permission_allow_button`). Popup/dialog in-app → đóng theo whitelist như `Utils.recoverToHome` Stage A.
8. **Đi tới màn feature**: từ Home theo path sitemap (tap tile/tab — element neo bằng `accessibility=<nhãn VN>`). `appium_get_page_source` xác nhận đúng màn.
9. Xong việc → `appium_quit_session` (hoặc để command đóng ở bước cuối).

> Reference luồng: `src/test/java/com/sbh/tests/auth/GoToHomeTest.java` (khi đã dựng). Element discover lưu `elements.json` qua skill `capture-elements`/`declare-screen`.
