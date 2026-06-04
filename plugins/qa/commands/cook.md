---
description: Write AUTOMATION test code from a plan or a request following the design pattern; auto-routes by platform (web Playwright / app Appium), reading only the matching platform skill
argument-hint: <path/to/plan.md | description of the task> [web|android|ios]
allowed-tools: Read, Glob, Grep, Edit, Write, Bash, Agent
---

# /qa:cook — Write test code (platform router)

Input: **$ARGUMENTS**

> Want to GENERATE TEST CASES (xlsx/Sheet) instead of writing automation code? Use **`/qa:gen-testcases`**.

## Classify input
- Path to a `.md` in `plans/` → read & execute that plan.
- Direct description → infer the task; large task → summarize the steps before coding; no plan but a large task → suggest `/qa:plan-tests` first.

## Step 0 — Lock platform (routing — do NOT read extra skills)
Run **skill `detect-platform`** (argument/auto-detect/ask). If the plan states a platform → follow the plan. Result = **one** `platform` (web · android · ios; android+ios merge into `app` at the code-writing layer).

## Step 1 — Read the CORRECT platform skill + rules (only 1 branch)
> Read only the branch matching `platform`. Do NOT read the other branch (save tokens).

- **web** → skill **`cook-web`** + rules `rules/web/design-pattern.md` · `coding-rules.md` · `design-system.md`.
- **android | ios** → skill **`cook-app`** + rules `rules/app/design-pattern.md` · `coding-rules.md` · `design-system.md`.

The platform skill wraps the full flow: element 3-layer lookup → declare Screen/Page Object (skill `declare-screen`, no-assert) → Test (assert) → smoke/regression compose → (app) TestNG XML with a `GoToHomeTest` block first. A `failCap`/red-log message caused by the app gets the `[APP-BUG]` label ([failure-triage.md §3b](../rules/failure-triage.md)). Locators that need discovery → open the screen via `navigate-web`/`navigate-app` + `find-elements-<platform>` (spawn agent `source-inspector` for app); elements missing id/testid → **skill `missing-ids`** (RECORD).

## After coding (all platforms)
- **skill `build-verify`** (compile/build green — `mvn clean compile test-compile` for Java). On error → **skill `fix-by-layer`** until green. **A red test on a trial run ≠ always fix the test**: triage first ([failure-triage.md](../rules/failure-triage.md)) — `[APP-BUG]` means write a defect, hand it to dev, and keep the test honest, do NOT loosen the assertion; only `[FRAMEWORK]`/`[ENV]`/`[DATA]` may be fixed.
- **skill `update-sitemap`** for every Screen created/edited. **Missing ID Report** (skill `missing-ids`) if any element lacks an id.
- List files created/edited + the test run command (print the platform used). Do **NOT** commit/push unless asked (use `/qa:push-code`).

## Principles
- Reuse `base`/`utils`/`actions`/`models` — no duplicated code. Each feature wrapped in its own group. Read the reference template (the platform's `LoginScreen`) before creating a new class.
- Plan references an element that does not actually exist → stop, suggest `/qa:find-elements` or `/qa:exploratory` first.
