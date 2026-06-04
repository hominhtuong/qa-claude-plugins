---
name: navigate-app
description: Reusable logic to use Appium MCP to launch the app, ensure it is at Home (manual GoToHome), then navigate to a feature screen per the sitemap. Used by the exploratory command (open a screen to explore/capture elements) and fix (reopen the real UI when a selector changes to get the correct locator). Includes device preflight + the correct way to install the app for MCP.
---

# Skill: navigate-app

Reusable capability: from a blank state → standing on the correct feature screen on a real device/emulator (Appium MCP), ready for `find-elements-android`/`-ios`. This is exactly the `GoToHomeTest` flow done manually via MCP.

## ⚠️ Two independent Appium servers — don't confuse them
- **MCP (this skill uses)**: server on a **fixed port 4723** per `.mcp.json` (`APPIUM_PORT=4723`). Start it with `./scripts/start-appium.sh` (kills the old port + starts + waits for ready). The MCP `appium_*` tools connect here.
- **Test runtime (`/qa:run`, NOT this skill)**: `AppiumServer.java` calls `usingAnyFreePort()` → any free port (or `APPIUM_SERVER_URL` if set). Does not touch 4723. → Don't run start-appium.sh for `/qa:run`.

## Procedure
1. **Device preflight**: `adb devices` (Android) / `xcrun simctl list devices` (iOS). Emulator needed but not running → `./scripts/start-emulator.sh` (poll until ready).
2. **MCP Appium ready**: `curl -s http://127.0.0.1:4723/status` — not ready → `./scripts/start-appium.sh`.
3. **Install the app BEFORE starting the session** (important):
   - MCP `appium_start_session` **CANNOT** use the `app_path` parameter to install (errors *"Either provide 'app' option… or set noReset true"*). → **Install manually**: `adb install -r -g <appPath>` then check `adb shell pm list packages | grep <appPackage>`.
   - `appPackage`/`appActivity` must match the actual APK — verify with `aapt dump badging <apk>` (`package: name=...`, `launchable-activity: name=...`). Wrong package → session starts but launch fails.
4. **Start the session** with the **already-installed** app: `appium_start_session(platform=Android, device_name=<udid>, app_package=<pkg>, app_activity=<activity>)` — do NOT pass app_path. Default automationName = UiAutomator2 (reads Flutter semantics well via content-desc).
5. **Check the sitemap first** (don't grope around): read `sitemap/sitemap.json` for the navigation path from Home to the feature screen, and the screen's characteristic element.
6. **Ensure you are at Home** (example illustrating a typical Flutter login flow — swap labels/elements for your app):
   - Welcome → tap `accessibility "Bắt đầu ngay"` → phone-number entry screen.
   - Enter the phone number into `class_name android.widget.EditText` (input field has NO id) → tap `accessibility "Tiếp tục"`.
   - Enter the password into `EditText` → tap `accessibility "Tiếp tục"` → Home.
   - **Account/OTP** comes from `configurations/test-users.json` (`phone`/`password`/`otp`) — **do NOT print the password** to the log.
   - Log in with **password** (not OTP for an existing account). Landing in a different state (OTP/onboarding) → handle as in `GoToHomeTest`.
7. **Dismiss the post-login popup**: the app often pops the Android notification-permission dialog → tap `id com.android.permissioncontroller:id/permission_deny_button` (or `permission_allow_button`). In-app popup/dialog → close per the whitelist like `Utils.recoverToHome` Stage A.
8. **Go to the feature screen**: from Home follow the sitemap path (tap tile/tab — element anchored by `accessibility=<VN label>`). `appium_get_page_source` to confirm the right screen.
9. Done → `appium_quit_session` (or let the command close it in its final step).

> Reference flow: `src/test/java/com/example/tests/auth/GoToHomeTest.java` (once built). Discovered elements are saved to `elements.json` via the `find-elements-*`/`declare-screen` skills.
