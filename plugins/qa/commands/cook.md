---
description: Produce test artifacts from a plan or a request — auto-detects mode → AUTOMATION writes test code (Playwright/Appium, routes by platform) or MANUAL generates test cases to xlsx + Google/Lark Sheet
argument-hint: <path/to/plan.md | request or feature + spec/Figma link> [web|android|ios] [--auto|--manual]
allowed-tools: Read, Glob, Grep, Edit, Write, Bash, Agent
---

# /cook — Write tests (mode router)

Input: **$ARGUMENTS**

## Step 0 — Detect mode
Run **skill `detect-mode`** → `automation` | `manual`. Read ONLY the matching section below.

---

# Mode: automation — write test code

## Classify input
- Path to a `.md` in `plans/` → read & execute that plan.
- Direct description → infer the task; large task → summarize the steps before coding; no plan but a large task → suggest `/plan-tests` first.

## Step A0 — Lock platform (routing — do NOT read extra skills)
Run **skill `detect-platform`** (argument/auto-detect/ask). If the plan states a platform → follow the plan. Result = **one** `platform` (web · android · ios; android+ios merge into `app` at the code-writing layer).

## Step A1 — Read the CORRECT platform skill + rules (only 1 branch)
> Read only the branch matching `platform`. Do NOT read the other branch (save tokens).

- **web** → skill **`cook-web`** + rules `rules/web/design-pattern.md` · `coding-rules.md` · `design-system.md`.
- **android | ios** → skill **`cook-app`** + rules `rules/app/design-pattern.md` · `coding-rules.md` · `design-system.md`.

The platform skill wraps the full flow: element 3-layer lookup → declare Screen/Page Object (skill `declare-screen`, no-assert) → Test (assert) → smoke/regression compose → (app) TestNG XML with a `GoToHomeTest` block first. A `failCap`/red-log message caused by the app gets the `[APP-BUG]` label ([failure-triage.md §3b](../rules/failure-triage.md)). Locators that need discovery → open the screen via `navigate-web`/`navigate-app` + `find-elements-<platform>` (spawn agent `source-inspector` for app); elements missing id/testid → **skill `missing-ids`** (RECORD).

## After coding (all platforms)
- **skill `build-verify`** (compile/build green — `mvn clean compile test-compile` for Java). On error → **skill `fix-by-layer`** until green. **A red test on a trial run ≠ always fix the test**: triage first ([failure-triage.md](../rules/failure-triage.md)) — `[APP-BUG]` means write a defect, hand it to dev, and keep the test honest, do NOT loosen the assertion; only `[FRAMEWORK]`/`[ENV]`/`[DATA]` may be fixed.
- **skill `update-sitemap`** for every Screen created/edited. **Missing ID Report** (skill `missing-ids`) if any element lacks an id.
- List files created/edited + the test run command (print the platform used). Do **NOT** commit/push unless asked (use `/push-code`).

## Principles (automation)
- Reuse `base`/`utils`/`actions`/`models` — no duplicated code. Each feature wrapped in its own group. Read the reference template (the platform's `LoginScreen`) before creating a new class.
- Plan references an element that does not actually exist → stop, suggest `/find-elements` or `/exploratory` first.

---

# Mode: manual — generate test cases

You are a **Senior QC Engineer**. The output must be production quality — detailed, accurate, immediately executable without further explanation.

> **LANGUAGE — RULE #1 (MANDATORY)**: Generate all test case content in Vietnamese (with diacritics) — description, precondition, steps, expected, section title. "Đăng nhập" is NOT "Dang nhap". When spawning a sub-agent, the agent prompt MUST repeat this rule verbatim. Only use English when the user requests `language: English`.

## Must read first
- @${CLAUDE_PLUGIN_ROOT}/rules/test-quality.md
- @${CLAUDE_PLUGIN_ROOT}/rules/output-format.md
- Skill `gen-testcases` (TC-writing engine) + skill `tc-template` (spreadsheet contract)

## Gathering information (MUST ask if missing)
1. Spec/PRD/ticket link (Google Docs / Lark wiki / Notion...)?
2. Figma link (if there's UI)?
3. Is there already a test plan from `/plan-tests` (manual mode)? If so → read that plan as the main input.
4. Determine the **output folder + prefix**: `results/<feature-name>/` (kebab-case, lowercase, no diacritics); prefix = feature abbreviation (e.g. `wir` for "Warehouse Inventory Report").

## Classifying the input
- **Path to a plan `.md`** (from `/plan-tests` manual mode) → MODE A (multi-phase).
- **Direct description + link** → MODE B (gather data + execute).

## MODE A — Has a plan → parallel multi-phase
1. Read the `<!-- PLAN STATUS -->` block at the top of the plan file: identify every phase + status (COMPLETED/PENDING/IN_PROGRESS) + TC_ID range.
2. Read rules `test-quality.md`, `output-format.md` + skills `gen-testcases`, `tc-template`.
3. **Spawn N parallel agents for N PENDING phases** — **max 5 concurrent agents**. >5 phases → run 5 first, spawn more as agents finish. Each agent (description "Cook Phase X"):
   ```
   You are a Senior QC Engineer. Write test cases for Phase X of the plan.
   CRITICAL: All Vietnamese content MUST have diacritics. "Đăng nhập" is NOT "Dang nhap",
   "Mật khẩu" is NOT "Mat khau". Output without diacritics is WRONG and must be fixed.
   Context: plan file {path} · Phase {N} · Scope {description from plan} · TC_ID range {TC_XXX-TC_YYY}
            · Output file {output}/{prefix}-phase-{N}.xlsx
   Read rules test-quality.md + output-format.md, use skills gen-testcases + tc-template.
   Read the Phase X section in the plan + summary files if any.
   Create the xlsx FOR THIS phase only. Do NOT upload to Drive (save locally only).
   ```
4. **WAIT** for all agents to finish (results may arrive out of order → record immediately, update the PLAN STATUS marker).
5. **Merge & Upload** (ONLY when ALL phases are DONE): combine all `{prefix}-phase-*.xlsx` → 1 master workbook (each module/feature = its own sheet, sheet name = module name, **TC_ID reset per sheet**, each sheet has its own header + COUNTIF). Save `{prefix}-final.xlsx`. Upload **once** via the priority chain → return a single URL.

## MODE B — No plan → gather + execute
1. Has a Figma link → `get_metadata` to count screens → spawn N Figma reader agents (each agent ≤ 7 screens). Has a doc link → spawn 1 Docs reader agent. **Total ≤ 5 agents**, launch in the same response.
2. **WAIT** for all agents to finish → read the summaries + rules + skills (MANDATORY SYNC, do not start writing TCs before every agent finishes).
3. Estimate the TC count: if > 50 TCs or > 5 modules → split into independent phases (use skill `plan-testcases`), spawn parallel agents (max 5) like MODE A. Smaller → write directly as a single phase.
4. Merge & Upload (like MODE A step 5).

## Handling Specs vs Figma conflicts
On detecting a contradiction → **STOP, ask the user** (follow Docs / follow Figma / case by case), mark `[Resolved: ...]` in the Precondition. See [test-quality §6.3](${CLAUDE_PLUGIN_ROOT}/rules/test-quality.md).

## Principles (manual)
- Write TCs per skill `gen-testcases`: 1 objective/TC, steps are actions only, expected separated out, **MANDATORY negative coverage**, no redundant expected & no color-code checks, correct multi-result format.
- Build the file per skill `tc-template`: 15 columns, header rows 1-7, freeze row 8, COUNTIF per sheet, import code from `configs/tc_template` (not inline).
- **DO NOT push each phase separately** — push only after merging. Return both the local path + Drive URL.
- If there's no plan and the work is large (>50 TCs, many modules) → suggest `/plan-tests` (manual mode) first.
