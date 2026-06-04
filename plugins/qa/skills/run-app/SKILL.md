---
name: run-app
description: Reusable logic to compile then run tests with device preflight (real/emulator auto-detect) and a report summary. Used by the run command. Always compile first; use scripts/run-*.sh (which check the device) instead of calling raw Maven where possible.
---

# Skill: run-app

Reusable capability: run the suite safely — compile first, check the device, run the right script, summarize the result.

## Procedure
1. **Determine scope**: platform (android default / ios / all) + suite (`testng/testng-android.xml` · `-ios` · `-all`) or a specific test/feature.
2. **Compile first** (gate): `mvn clean compile test-compile`. Red → report the error, do **NOT** continue (suggest the `fix-by-layer` skill).
3. **Device preflight** (the script handles it, but understand the mechanism): read `deviceName` from capabilities — `emulator-*` = emulator (not running → `./scripts/start-emulator.sh`, poll 5s, timeout 60s); otherwise = real device (must be in `adb devices` / `xcrun xctrace list devices`, else abort).
4. **Run**: `./scripts/run-android.sh` · `./scripts/run-ios.sh` · `./scripts/run-all.sh` (recommended). Custom suite → `mvn test -DsuiteXmlFile=<suite>`.
5. **Report the result**: exit code, the latest report under `results/tests/<ddMMMyyyy>/`, summary of passed/failed/skipped/duration.
6. **Triage every FAIL** ([failure-triage.md](../../rules/failure-triage.md)) — **before suggesting `/qa:fix`**: for each red test, classify the root cause as `[APP-BUG]` (app is wrong — report to dev, do NOT fix the test to make it green) vs `[FRAMEWORK]` (locator/automation wrong — `/qa:fix`) vs `[ENV]`/`[DATA]`. Cross-check the stack trace + screenshot in the ExtentReport (the message starts with the label). **Summarize fails by label** (e.g. "3 fail: 1 [APP-BUG], 2 [FRAMEWORK]") so it's clear whether the "app is broken" or the "test is broken". Only `[FRAMEWORK]`/`[ENV]`/`[DATA]` fails warrant a `/qa:fix` suggestion; `[APP-BUG]` → list the defect to hand to dev.

## Final step — Upload report + Notify (optional, if enabled)
Only runs when the project has a `.claude/qa-claude/.plugin.env` (created by the `setup` skill). Every flag defaults to `false` → silently skipped. The scripts read `.plugin.env` from the project, **cross-platform** (`python3` macOS/Linux, `python` Windows). Each group picks **at most 1** channel:

1. **Upload report** (share via URL) — run whichever channel is enabled:
   - R2 (`ENABLE_CF_PUSH`): `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/push_report.py results/tests/<ddMMMyyyy>/<report>.html [manifest]`
   - or S3-compatible (`ENABLE_S3_PUSH`): `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/push_s3.py results/tests/<ddMMMyyyy>/<report>.html [manifest]`
   - Both print a final line `REPORT_URL=<url>` — capture that URL for the notify step.
2. **Notify the result** — run whichever channel is enabled (same set of flags `--passed/--failed/--skipped/--duration-ms/--report-url/--git-name/--git-email` + per fail `--failed-test "<name>|<message>"`):
   - Lark (`ENABLE_LARK_NOTIFY`): `${CLAUDE_PLUGIN_ROOT}/scripts/lark_notify.py`
   - or generic webhook (`ENABLE_NOTIFY_WEBHOOK`, Slack/Teams/Telegram/Discord): `${CLAUDE_PLUGIN_ROOT}/scripts/notify_webhook.py`

Every script **no-ops itself** when its flag is off / config is missing → never breaks the run. Missing `wrangler`/`aws`/`python` → run the `doctor` skill.

## Appium server — NO need to start it manually for `/qa:run`
The test runtime uses `AppiumServer.shared()` which calls `usingAnyFreePort()` → starts Appium on **any free port**, independent of whatever port is running. So `/qa:run` does **not** call `start-appium.sh`. To point at an existing server (e.g. MCP 4723) → `export APPIUM_SERVER_URL=http://127.0.0.1:4723` before running. (The fixed port 4723 + `start-appium.sh` are only for **MCP exploratory**, see the `navigate-app` skill.)

> Do NOT fix test code — just run. The TestNG XML must have `GoToHomeTest` as the first `<test>` block.
