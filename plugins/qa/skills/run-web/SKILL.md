---
name: run-web
description: Reusable logic to compile then run the Playwright Java test suite (make smoke|regression or mvn test -Dtest=...), summarize the result from ExtentReports Spark, and triage every FAIL per failure-triage ([APP-BUG] vs [FRAMEWORK]/[ENV]/[DATA]). Used by the run command. Always compile first; prefer make targets.
---

# Skill: run-web

Reusable capability: run the suite safely — compile first, run the right target, summarize the report, triage fails.

## Procedure
1. **Determine scope**: suite (`make smoke` / `make regression`) or a specific class/method + env/browser if needed.
2. **Compile first** (gate): `mvn -q -B test-compile`. Red → report the error, do **NOT** continue (suggest the `fix-by-layer` skill).
3. **Run** (prefer the Makefile — it has wired the serial suite + env flags):
   - `make smoke` · `make regression` (SERIAL, clean green report — recommended).
   - 1 class: `make test CLASS=<Class>` (≈ `mvn test -Dtest=<Class>`). 1 method: `make method CLASS=<Class> METHOD=<method>` (≈ `mvn test -Dtest=<Class>#<method>`).
   - Watch it live (debug): `make regression HEADED=1` (force headed + slow), tune with `SLOWMO=<ms>` / `PAUSE=<ms>`.
   - Change env/browser: `make <target> ENV=staging BROWSER=chromium`.
4. **Report the result**: exit code + the latest report under `results/reports/<ddMMMyyyy>/<runTs>/` (ExtentReports Spark HTML + `screenshots/` + `traces/`). Summarize Total/Passed/Failed/Skipped + duration; each test has a screenshot (pass & fail) + the URL at the end embedded in the report.
5. **Triage every FAIL** ([failure-triage.md](../../rules/failure-triage.md)) — **before suggesting `/fix`**: for each red test, classify the root cause as `[APP-BUG]` (app is wrong — report to dev, do NOT fix the test to make it green) vs `[FRAMEWORK]` (locator/automation wrong — `/fix`) vs `[ENV]`/`[DATA]`. Cross-check the stack trace + screenshot + URL in the ExtentReport. **Summarize fails by label** (e.g. "3 fail: 1 [APP-BUG], 2 [FRAMEWORK]") so it's clear whether the "app is broken" or the "test is broken". Only `[FRAMEWORK]`/`[ENV]`/`[DATA]` fails warrant a `/fix` suggestion; `[APP-BUG]` → list the defect to hand to dev.

## Final step — Upload report + Notify (optional, if enabled)
Only runs when the project has a `./.env` (created by the `setup` skill). Every flag defaults to `false` → silently skipped. The scripts read `.env` from the project, **cross-platform** (`python3` macOS/Linux, `python` Windows). Each group picks **at most 1** channel:

1. **Upload report** (`<rpt>` = `results/reports/<date>/<runTs>/<report>.html`):
   - R2 (`ENABLE_CF_PUSH`): `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/push_report.py <rpt>`
   - or S3 (`ENABLE_S3_PUSH`): `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/push_s3.py <rpt>`
   - Capture the `REPORT_URL=<url>` line.
2. **Notify** (shared flags `--passed/--failed/--skipped/--duration-ms/--report-url/--git-name/--git-email` + per fail `--failed-test "<name>|<message>"`):
   - Lark (`ENABLE_LARK_NOTIFY`): `${CLAUDE_PLUGIN_ROOT}/scripts/lark_notify.py`
   - or generic webhook (`ENABLE_NOTIFY_WEBHOOK`): `${CLAUDE_PLUGIN_ROOT}/scripts/notify_webhook.py`

Every script **no-ops itself** when its flag is off / config is missing → does not break the run. Missing `wrangler`/`aws`/`python` → run the `doctor` skill.

> Do NOT fix test code — just run & triage. The browser is opened by `PlaywrightFactory` as **one shared window for the whole run** (serial); `make` already selects the `*-serial.xml` suite.
