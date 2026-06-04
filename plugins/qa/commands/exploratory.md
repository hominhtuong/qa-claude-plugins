---
description: Navigate to a feature screen (web/android/ios), read & analyze any spec provided (local file / URL / Figma / pasted prompt) into an expected-behavior oracle, then explore & hunt bugs like a senior QA against that oracle, capture evidence + produce a bug report; GATE for writing tests. Auto-route by platform, reading only the matching platform skill.
argument-hint: <feature-name> [web|android|ios] [nav path] [--spec <file|url|figma|"text">]...
allowed-tools: Read, Glob, Grep, Edit, Write, Bash, Agent, WebFetch
---

# /qa:exploratory — Explore & find bugs in a feature (spec-driven, platform router)

Feature to explore: **$ARGUMENTS**

**Goal #1 — FIND BUGS**: probe the feature screen like a **senior exploratory QA** to surface app defects → produce a **bug report for dev** following [exploratory-bug-report-template.md](../rules/exploratory-bug-report-template.md).
**Goal #2 — Prepare tests (ONLY when clean)**: feature with **no `[APP-BUG]`** → extract elements → ready for `/qa:plan-tests`/`/qa:cook`.

> ⚠️ **GATE**: *Automation only works when the app is correct.* A feature with `[APP-BUG]` → **do NOT write tests** for that part, the deliverable is a **bug report**. Only a **clean** feature proceeds to `/qa:plan-tests`.
> ⚠️ **Suspect the app by default**: every wrong/red observation **MUST** be triaged per [failure-triage.md](../rules/failure-triage.md): `[APP-BUG]` (app wrong — blocks tests) vs `[FRAMEWORK]` (our element capture/automation is wrong) vs `[ENV]`/`[DATA]`. Do NOT assume the app is correct.

## Step 0 — Lock platform (routing)
Run **skill `detect-platform`** (argument/auto-detect/ask) → one `platform`. Determine the **group** (lowercase, e.g. `quản lý đơn` → `order`); read `sitemap/sitemap.json` (if it exists) to learn the path from Home.

## Step 0.5 — Read & analyze the spec → expected-behavior ORACLE (when any spec is provided)
> **Why**: a spec turns blind clicking into **oracle-based** testing — you compare what the app *does* against what it *should* do, so deviations become real `[APP-BUG] spec-mismatch` instead of guesses. **Do the full read + analysis FIRST; only hunt bugs once the docs are read and the analysis is clear.** No spec given → skip to Step 1 and explore heuristically (still valid, just lower bug-catch power).

**0.5a — Collect spec sources** from `$ARGUMENTS` (any mix, repeatable via `--spec`, or just pasted in the prompt):
- **Lark URL** (`larksuite.com` / `feishu.cn` / `lark.com`)
- **Figma URL** (`figma.com`)
- **Generic web URL** (any other `http(s)://`)
- **Local file path** (no `http` — `.md`/`.pdf`/`.docx`/`.xlsx`/`.png`/…)
- **Pasted text** — the user describes the expected behavior inline

**0.5b — Fan out reader sub-agents in parallel** (one level of orchestration; each writes into `results/exploratory/<group>/spec/`). Every sub-agent prompt MUST include: *"CRITICAL: tất cả nội dung tiếng Việt PHẢI có dấu. Output không dấu là SAI."*
- **Lark URL** → agent **`lark-reader`** (`output_file: results/exploratory/<group>/spec/spec-summary.md`, `doc_index`). It reads via the Python helper (app token, auto-auth); if it reports an auth/permission error, run `/qa:auth-lark --command exploratory` to fix scopes, then retry.
- **Figma URL** → agent **`figma-reader`** (`output_file: .../spec/figma-summary.md`, `tracking_file: .../spec/figma-tracking.md`, `max_screens`, `batch`). If it returns PENDING screens → spawn the next `batch` until none remain.
- **Generic URL / local file / pasted text** → agent **`spec-reader`** (`source`, `output_file: .../spec/spec-summary.md`, `doc_index`, `feature_name`).
- Reader returns **embedded links** (Lark/Figma/external) → fan out the matching reader once more (max depth 1). Don't recurse further.

**0.5c — WAIT** for all readers → read their summaries (`spec/spec-summary.md`, `spec/figma-summary.md`).

**0.5d — Consolidate into the oracle** `results/exploratory/<group>/spec/spec-analysis.md` (Vietnamese, with diacritics). This is the **probe checklist** the bug-hunt runs against:
- **Functional requirements** to exercise (each → one probe).
- **Business rules / formulas** (expected values to verify against on-screen figures).
- **Validation rules** per field (valid/invalid/boundary inputs to try + expected error message).
- **UI/UX states** expected (loading/empty/error/success/disabled) + design points (feed Step 2b).
- **Edge cases** to hit.
- **Open questions / gaps** in the spec → carry to the report's `❓ NEEDS-TRIAGE` + questions for PO.

> **Analysis GATE**: if the spec is too thin to derive a probe checklist (no testable requirement at all), say so explicitly and either ask the user for more, or proceed heuristically and mark the run "no oracle". Do NOT pretend coverage you can't back with the spec.

## Step 1 — Open the correct screen (only the locked platform skill)
- **web** → skill **`navigate-web`** (Playwright MCP: navigate URL + login + back to Home → feature screen).
- **android | ios** → skill **`navigate-app`** (Appium MCP: device preflight + install + session + GoToHome → feature screen).

## Step 2 — Explore, hunt bugs & triage — skill `exploratory-method` (agnostic, core)
The full bug-hunting method lives in **skill `exploratory-method`**. **When a `spec-analysis.md` exists, drive the probe from it** (walk each requirement / business rule / validation / UI state, comparing actual vs expected → deviation = `[APP-BUG] spec-mismatch`); without it, fall back to heuristic probing (try the main interactions + open item detail + validate boundaries). Always **read figures/messages carefully** to catch wrong numbers/negative numbers/leaked text/SQL exceptions exposed in the UI, **triage on the spot**, **screenshot evidence** → `results/exploratory/<group>/screenshots/<BUG-ID>.png` (each `[APP-BUG]` ≥1 image + a few `-ok` images), quote the error verbatim. Elements that can't be anchored → record them in the bug report. Screenshot via MCP web = `browser_take_screenshot`, app = `appium_take_screenshot` — **always pass the full relative path as `filename`** (e.g. `results/exploratory/<group>/screenshots/<BUG-ID>.png`), never a bare file name, otherwise it lands in the MCP output dir / project root instead.

## Step 2b — Cross-check against the design (if a spec/Figma exists) — skill `design-conformance`
Does the UI match the design system + the Figma summary from Step 0.5 (color/typography/corner-radius/state tokens, layout, copy, touch target ≥48px). Deviation vs the design → `[APP-BUG]` *design deviation*. No component spec yet → `[NEEDS-TRIAGE]`, don't conclude. (Native apps make it hard to read color/font via element → check mainly via images.)

## Step 2c — Record the navigation map (ALWAYS, even if buggy) — skill `update-sitemap`
For **every screen you walked through** (Home → … → feature + sub-screens), write/update `sitemap/screens/<id>.json` with the `reach` steps (web: route + clicks · app: tap actions), `parentId`, `keyElement`, `route` (web) / `null` (app), `notes`. Then regenerate: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_sitemap.py`. This is a **first-class output** — it's how later cases find the path to the feature, so do it whether or not the feature is buggy.

## Step 3 — Extract elements & build the Screen (ONLY when the feature is clean)
> Skip if the feature has a blocking `[APP-BUG]` (no test written yet means no Screen needed yet — the sitemap node from Step 2c still stays).

Open the correct find-elements skill per platform: **web** `find-elements-web` · **android** `find-elements-android` · **ios** `find-elements-ios` (app: spawn agent `source-inspector`). Elements missing id/testid → **skill `missing-ids`** (RECORD). Declare Screen/Page Object via skill `declare-screen` (no-assert) → **skill `build-verify`** green → refresh the sitemap node's `screenClass` (skill `update-sitemap`).

## Step 4 — Bug Report for dev (MAIN DELIVERABLE)
Per `exploratory-method`: write `results/exploratory/<group>/dev-bug-report-<ddMMMyyyy>.md` following the template (each bug: Screen · Verbatim symptom · Root cause if found · Impact · **Expectation — cite the spec section/oracle when available** · Evidence · Defect ID) + a **✅ Checked — NO bug** section + **❓ NEEDS-TRIAGE** (include spec gaps/open questions from Step 0.5) + environment notes. Append each `[APP-BUG]` to the register `results/exploratory/bug-summary.md`.

## Step 5 — GATE DECISION + finish
- 🔴 **Has `[APP-BUG]`** → deliverable = bug report for dev. Do **NOT** `/qa:plan-tests`/`/qa:cook` for the broken part.
- 🟢 **No `[APP-BUG]`** → app correct → Screen/elements extracted → suggest **`/qa:plan-tests <feature-name>`**.

Close the session (`appium_quit_session` / `browser_close`). Print: platform, **spec sources read + oracle path** (`spec/spec-analysis.md`) or "no spec", bug report path (+ register), list of `[APP-BUG]`, **sitemap nodes updated (always)** + Screen built (if clean), **gate conclusion**.
