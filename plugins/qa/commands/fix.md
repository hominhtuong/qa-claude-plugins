---
description: Fix a bug (compile/test fail, flaky, rule violation) at the correct layer, or update an existing plan. Auto-route by platform to get locators/read the correct platform rules
argument-hint: <bug description / test failure / path to plan to fix> [web|android|ios]
allowed-tools: Read, Glob, Grep, Edit, Write, Bash, Agent
---

# /qa:fix — Fix a bug or fix a plan (platform router)

Input: **$ARGUMENTS**

## Classify
1. **Fix a plan**: input points to a file in `plans/` or says "fix plan" → update that plan file (keep the standard `/qa:plan-tests` format). Do NOT use skill fix-by-layer.
2. **Fix a bug** (default): compile/build fail / test fail / flaky / rule violation → continue below.

## Step 0 — Lock platform (routing)
Run **skill `detect-platform`** (argument/failing file path context/auto-detect) → one `platform`.

## Execution (fix a bug)
- Read the rules per `platform`: **web** → `rules/web/coding-rules.md` + `design-pattern.md`; **android/ios** → `rules/app/coding-rules.md` + `design-pattern.md`.
- **skill `fix-by-layer`** (agnostic): triage first ([failure-triage.md](../rules/failure-triage.md)) — `[APP-BUG]` means **STOP, write a defect, hand it to dev, do NOT fix the test to make it green**; only `[FRAMEWORK]`/`[ENV]`/`[DATA]` may be fixed. Isolate the correct layer (Screen locator / Test assertion / regression-smoke compose / configurations) → apply the minimal fix addressing the root cause, do NOT work around (no stray `Thread.sleep`, no swallowing errors).
- Failure caused by a **changed selector/UI** → get the correct locator before fixing the Screen: open the screen via `navigate-web`/`navigate-app` + `find-elements-<platform>`.
- Verify via **skill `build-verify`** (compile/build green + re-run the just-fixed test until green).
- Non-id element touched → Missing ID Report (skill `missing-ids`). Do NOT commit/push unless asked.

## Report
Platform · root cause · file/layer fixed · how it was verified. Flaky → source of nondeterminism + the remedy (wait for a real condition instead of sleeping).
