# Troubleshooting Guide

Các lỗi thường gặp và cách xử lý.

---

## Appium & Driver

### 1. `SessionNotCreatedException` — App không khởi động
**Nguyên nhân**: App path sai, package/activity sai, hoặc device chưa sẵn sàng
**Fix**:
- Kiểm tra `appPath` trong `android-capabilities.properties` — file APK có tồn tại?
- Kiểm tra `appPackage`, `appActivity` đúng chưa
- `adb devices` — device có connected?
- Thử `adb install <apk>` manual trước

### 2. `WebDriverException: Connection refused`
**Nguyên nhân**: Appium server chưa chạy hoặc port sai
**Fix**:
- `curl http://127.0.0.1:4723/status` — check server
- `./scripts/start-appium.sh` — start server
- `./scripts/kill-appium.sh` rồi start lại nếu port bị chiếm

### 3. `NoSuchElementException` — Element không tìm thấy
**Nguyên nhân**: Element chưa render, locator sai, hoặc screen chưa đúng
**Fix**:
- Check screen hiện tại có đúng không (`isDisplayed()`)
- Check locator trong elements.json hoặc dùng source-inspector
- Tăng timeout nếu cần: hiện MobileFindFieldDecorator poll 5s
- Check animation chưa xong → thêm `Utils.delay()`

### 4. `StaleElementReferenceException`
**Nguyên nhân**: Element đã bị DOM remove/recreate sau khi tìm thấy
**Fix**:
- Tìm lại element (call getter lại)
- Dùng `WebDriverWait` thay vì access element ngay
- Check xem có animation hay transition đang xảy ra

---

## Build & Compile

### 5. `mvn compile` fails — Cannot find symbol
**Nguyên nhân**: Class/method bị xóa hoặc import sai
**Fix**:
- Check import statements
- `mvn clean compile test-compile` (clean build)
- `Cmd+Shift+P → Java: Clean Java Language Server Workspace` trong VSCode

### 6. `Test classes not found` khi chạy mvn test
**Nguyên nhân**: TestNG XML reference sai class name
**Fix**:
- Check `testng-*.xml` — class name match với actual package + class name?
- Chạy `mvn clean compile test-compile` trước khi test

---

## Device & Emulator

### 7. Emulator không khởi động
**Nguyên nhân**: AVD chưa tạo, hoặc resource conflict
**Fix**:
- `emulator -list-avds` — check AVD tồn tại
- `avdName` trong `android-capabilities.properties` match?
- Kill emulator cũ: `adb emu kill`
- `./scripts/start-emulator.sh` — auto-start

### 8. iOS device không nhận
**Nguyên nhân**: UDID sai, device chưa trust, hoặc WebDriverAgent chưa build
**Fix**:
- `xcrun xctrace list devices` — device có trong list?
- Check `udid` trong `ios-capabilities.properties`
- Mở Xcode → trust device
- Build WebDriverAgent: `xcodebuild -project WebDriverAgent.xcodeproj -scheme WebDriverAgentRunner`

---

## Reporting

### 9. Report không upload lên Cloudflare R2
**Nguyên nhân**: Config sai hoặc wrangler chưa install
**Fix**:
- Check `configurations/cloudflare.properties` — `ENABLE_CF_PUSH=true`?
- `which wrangler` — wrangler installed?
- `npm install -g wrangler` nếu chưa có
- Check `reports/upload-logs/` cho error logs

### 10. Lark notification không gửi
**Nguyên nhân**: Webhook URL sai hoặc secret sai
**Fix**:
- Check `configurations/lark.properties` — `ENABLE_LARK_NOTIFY=true`?
- Verify webhook URL vẫn active trên Lark bot settings
- Check network connectivity

---

## MCP

### 11. MCP Appium không kết nối
**Nguyên nhân**: Appium server chưa chạy trên port 4723
**Fix**:
- `./scripts/start-appium.sh` — start trên port 4723
- Check `.mcp.json` — `APPIUM_PORT=4723`
- Device phải connected VÀ app phải đang mở

> **Lưu ý — 2 Appium server độc lập**: MCP dùng **port cố định 4723** (`.mcp.json` + `start-appium.sh`). Test runtime (`/run`) dùng `AppiumServer.usingAnyFreePort()` → **port trống bất kỳ**, KHÔNG cần start-appium.sh. Muốn `/run` dùng lại server MCP → `export APPIUM_SERVER_URL=http://127.0.0.1:4723`.

### 11b. MCP `appium_start_session` báo "Either provide 'app' option… or set noReset true"
**Nguyên nhân**: MCP tool KHÔNG map tham số `app_path` thành capability `app` để install.
**Fix**: cài app TRƯỚC bằng `adb install -r -g <appPath>` (check `pm list packages | grep <pkg>`), rồi `appium_start_session` chỉ truyền `app_package` + `app_activity` (app preinstalled). Verify package khớp APK: `aapt dump badging <apk>` (`package: name=...`, `launchable-activity: name=...`). `appActivity` SBH = `com.example.merchant_app.MainActivity`.

### 11c. Login MCP → vướng popup quyền thông báo
**Nguyên nhân**: Android 13+ bật dialog `POST_NOTIFICATIONS` sau khi vào Home.
**Fix**: tap `id com.android.permissioncontroller:id/permission_deny_button` (hoặc `permission_allow_button`). Ô input SĐT/mật khẩu là `android.widget.EditText` (không id) — tìm bằng `class_name`. Account test: `configurations/test-users.json`.

### 12. MCP Lark trả lỗi "Access denied"
**Nguyên nhân**: Sai token mode hoặc thiếu scope
**Fix**:
- Wiki/docx content → `useUAT: true`
- Comments → KHÔNG dùng `useUAT` (tenant token)
- Image download → `useUAT: true`
- Check `.mcp.json` scopes
- Đọc `${CLAUDE_PLUGIN_ROOT}/rules/lark-mcp-guide.md`

### 13. Inline image download trả về mảng rỗng
**Nguyên nhân**: Dùng tenant token thay vì user token
**Fix**: `batchGetTmpDownloadUrl` PHẢI dùng `useUAT: true`
