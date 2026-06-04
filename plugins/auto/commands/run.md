---
description: Compile then run tests + summarize the report; auto-route by platform (web Playwright / app Appium), reading only the matching platform skill
argument-hint: [web | android (default for app) | ios | all | specific test/feature name]
allowed-tools: Read, Glob, Grep, Bash
---

# /run — Compile & run tests (platform router)

Input: **$ARGUMENTS** (specific platform/suite/test).

## Step 0 — Lock platform (routing)
Run **skill `detect-platform`**: argument `web|android|ios|all` → use it directly; empty → auto-detect the project. App-only repo with empty input → default **android** (print clearly "defaulting to android, pass `ios`/`web` to change"). `all` = run each detected platform in turn.

## Step 1 — Run the CORRECT platform skill (only 1)
> Read only the skill matching `platform`.

- **web** → skill **`run-web`**: compile → `make smoke|regression` or `mvn test -Dtest=<Class#method>` → ExtentReports report `results/reports/<date>/`.
- **android | ios** → skill **`run-app`**: compile (`mvn clean compile test-compile`) → device preflight (`emulator-*` auto-start; a real device must be in `adb devices`/`xcrun`) → `./scripts/run-android.sh` / `run-ios.sh` / `run-all.sh` (or `mvn test -DsuiteXmlFile=<suite>`). The TestNG XML must have `GoToHomeTest` as the first `<test>` block.

## Step 2 — Report results & triage
- Exit code, latest report, passed/failed/skipped/duration.
- **Triage every FAIL** ([failure-triage.md](../rules/failure-triage.md)): `[APP-BUG]` (app wrong → list the defect, hand to dev, do NOT fix the test) vs `[FRAMEWORK]`/`[ENV]`/`[DATA]` (→ suggest `/fix`). Summarize fails by label ("3 fail: 1 [APP-BUG], 2 [FRAMEWORK]").

## Step 3 — Push report + Lark notify (automatic, if enabled)

The platform skill handles the **final step**: if the project has `./.env` with `ENABLE_CF_PUSH=true` → push the report to Cloudflare R2 (`scripts/push_report.py`); `ENABLE_LARK_NOTIFY=true` → send a result card to Lark (`scripts/lark_notify.py`). Flags off → skip silently. Project has no `.env` yet → run skill `setup` once (cross-platform Win/Mac, auto-installs `wrangler`).

## Principles
- Always compile before running. Prefer scripts (they self-check the device). Do **NOT** edit test code — just run. Print the platform run clearly.
