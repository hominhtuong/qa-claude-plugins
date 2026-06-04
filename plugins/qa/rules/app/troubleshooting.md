# Troubleshooting Guide

Common errors and how to handle them.

---

## Appium & Driver

### 1. `SessionNotCreatedException` — App does not start
**Cause**: Wrong app path, wrong package/activity, or device not ready
**Fix**:
- Check `appPath` in `android-capabilities.properties` — does the APK file exist?
- Check that `appPackage`, `appActivity` are correct
- `adb devices` — is the device connected?
- Try `adb install <apk>` manually first

### 2. `WebDriverException: Connection refused`
**Cause**: Appium server not running or wrong port
**Fix**:
- `curl http://127.0.0.1:4723/status` — check the server
- `./scripts/start-appium.sh` — start the server
- `./scripts/kill-appium.sh` then restart if the port is taken

### 3. `NoSuchElementException` — Element not found
**Cause**: Element not rendered yet, wrong locator, or wrong screen
**Fix**:
- Check the current screen is correct (`isDisplayed()`)
- Check the locator in elements.json or use source-inspector
- Increase the timeout if needed: MobileFindFieldDecorator currently polls 5s
- Check the animation hasn't finished → add `Utils.delay()`

### 4. `StaleElementReferenceException`
**Cause**: The element was removed/recreated in the DOM after being found
**Fix**:
- Find the element again (call the getter again)
- Use `WebDriverWait` instead of accessing the element immediately
- Check whether an animation or transition is occurring

---

## Build & Compile

### 5. `mvn compile` fails — Cannot find symbol
**Cause**: A class/method was deleted or an import is wrong
**Fix**:
- Check the import statements
- `mvn clean compile test-compile` (clean build)
- `Cmd+Shift+P → Java: Clean Java Language Server Workspace` in VSCode

### 6. `Test classes not found` when running mvn test
**Cause**: The TestNG XML references a wrong class name
**Fix**:
- Check `testng-*.xml` — does the class name match the actual package + class name?
- Run `mvn clean compile test-compile` before testing

---

## Device & Emulator

### 7. Emulator does not start
**Cause**: AVD not created, or a resource conflict
**Fix**:
- `emulator -list-avds` — check the AVD exists
- Does `avdName` in `android-capabilities.properties` match?
- Kill the old emulator: `adb emu kill`
- `./scripts/start-emulator.sh` — auto-start

### 8. iOS device not recognized
**Cause**: Wrong UDID, device not trusted, or WebDriverAgent not built
**Fix**:
- `xcrun xctrace list devices` — is the device in the list?
- Check `udid` in `ios-capabilities.properties`
- Open Xcode → trust the device
- Build WebDriverAgent: `xcodebuild -project WebDriverAgent.xcodeproj -scheme WebDriverAgentRunner`

---

## Reporting

### 9. Report does not upload to Cloudflare R2
**Cause**: Wrong config or wrangler not installed
**Fix**:
- Check `configurations/cloudflare.properties` — `ENABLE_CF_PUSH=true`?
- `which wrangler` — is wrangler installed?
- `npm install -g wrangler` if not present
- Check `reports/upload-logs/` for error logs

### 10. Lark notification not sent
**Cause**: Wrong webhook URL or wrong secret
**Fix**:
- Check `configurations/lark.properties` — `ENABLE_LARK_NOTIFY=true`?
- Verify the webhook URL is still active in the Lark bot settings
- Check network connectivity

---

## MCP

### 11. MCP Appium does not connect
**Cause**: Appium server not running on port 4723
**Fix**:
- `./scripts/start-appium.sh` — start on port 4723
- Check `.mcp.json` — `APPIUM_PORT=4723`
- The device must be connected AND the app must be open

> **Note — 2 independent Appium servers**: MCP uses a **fixed port 4723** (`.mcp.json` + `start-appium.sh`). Test runtime (`/run`) uses `AppiumServer.usingAnyFreePort()` → **any free port**, does NOT need start-appium.sh. To make `/run` reuse the MCP server → `export APPIUM_SERVER_URL=http://127.0.0.1:4723`.

### 11b. MCP `appium_start_session` reports "Either provide 'app' option… or set noReset true"
**Cause**: The MCP tool does NOT map the `app_path` parameter to the `app` capability for install.
**Fix**: install the app FIRST with `adb install -r -g <appPath>` (check `pm list packages | grep <pkg>`), then `appium_start_session` only passes `app_package` + `app_activity` (app preinstalled). Verify the package matches the APK: `aapt dump badging <apk>` (`package: name=...`, `launchable-activity: name=...`). `appActivity` (example) = `com.example.app.MainActivity`.

### 11c. MCP login → blocked by notification permission popup
**Cause**: Android 13+ shows the `POST_NOTIFICATIONS` dialog after reaching Home.
**Fix**: tap `id com.android.permissioncontroller:id/permission_deny_button` (or `permission_allow_button`). The phone/password input fields are `android.widget.EditText` (no id) — find them by `class_name`. Test account: `configurations/test-users.json`.

### 12. MCP Lark returns "Access denied"
**Cause**: Wrong token mode or missing scope
**Fix**:
- Wiki/docx content → `useUAT: true`
- Comments → do NOT use `useUAT` (tenant token)
- Image download → `useUAT: true`
- Check `.mcp.json` scopes
- Read `${CLAUDE_PLUGIN_ROOT}/rules/lark-mcp-guide.md`

### 13. Inline image download returns an empty array
**Cause**: Using a tenant token instead of a user token
**Fix**: `batchGetTmpDownloadUrl` MUST use `useUAT: true`
</content>
