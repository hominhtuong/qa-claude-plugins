---
description: Navigate to a feature screen (web/android/ios), explore & hunt bugs like a senior QA, capture evidence + produce a bug report; GATE for writing tests. Auto-route by platform, reading only the matching platform skill
argument-hint: <feature-name> [web|android|ios] [navigation path if known]
allowed-tools: Read, Glob, Grep, Edit, Write, Bash, Agent
---

# /qa:exploratory — Explore & find bugs in a feature (platform router)

Feature to explore: **$ARGUMENTS**

**Goal #1 — FIND BUGS**: probe the feature screen like a **senior exploratory QA** to surface app defects → produce a **bug report for dev** following [exploratory-bug-report-template.md](../rules/exploratory-bug-report-template.md).
**Goal #2 — Prepare tests (ONLY when clean)**: feature with **no `[APP-BUG]`** → extract elements → ready for `/qa:plan-tests`/`/qa:cook`.

> ⚠️ **GATE**: *Automation only works when the app is correct.* A feature with `[APP-BUG]` → **do NOT write tests** for that part, the deliverable is a **bug report**. Only a **clean** feature proceeds to `/qa:plan-tests`.
> ⚠️ **Suspect the app by default**: every wrong/red observation **MUST** be triaged per [failure-triage.md](../rules/failure-triage.md): `[APP-BUG]` (app wrong — blocks tests) vs `[FRAMEWORK]` (our element capture/automation is wrong) vs `[ENV]`/`[DATA]`. Do NOT assume the app is correct.

## Step 0 — Lock platform (routing)
Run **skill `detect-platform`** (argument/auto-detect/ask) → one `platform`. Determine the **group** (lowercase, e.g. `quản lý đơn` → `order`); read the sitemap (if any) to learn the path from Home.

## Step 1 — Open the correct screen (only the locked platform skill)
- **web** → skill **`navigate-web`** (Playwright MCP: navigate URL + login + back to Home → feature screen).
- **android | ios** → skill **`navigate-app`** (Appium MCP: device preflight + install + session + GoToHome → feature screen).

## Step 2 — Explore, hunt bugs & triage — skill `exploratory-method` (agnostic, core)
The full bug-hunting method (try the main interactions + open item detail + validate boundaries, **read figures/messages carefully** to catch wrong numbers/negative numbers/leaked text/SQL exceptions exposed in the UI), **triage on the spot**, **screenshot evidence** → `reports/exploratory/<group>/screenshots/` named by BUG-ID (each `[APP-BUG]` ≥1 image + a few `-ok` images), quote the error verbatim — lives in **skill `exploratory-method`**. Elements that can't be anchored → record them in the bug report. Screenshot via MCP web = `browser_take_screenshot`, app = `appium_take_screenshot` (JPG, not to Desktop).

## Step 2b — Cross-check against the design system (if a spec exists) — skill `design-conformance`
Does the UI match the design system (color/typography/corner-radius/state tokens, touch target ≥48px). Deviation vs the design → `[APP-BUG]` *design deviation*. No component spec yet → `[NEEDS-TRIAGE]`, don't conclude. (Native apps make it hard to read color/font via element → check mainly via images.)

## Step 3 — Extract elements (ONLY when the feature is clean)
> Skip if the feature has a blocking `[APP-BUG]` (no test written yet means no Screen needed yet).

Open the correct find-elements skill per platform: **web** `find-elements-web` · **android** `find-elements-android` · **ios** `find-elements-ios` (app: spawn agent `source-inspector`). Elements missing id/testid → **skill `missing-ids`** (RECORD). Declare Screen/Page Object via skill `declare-screen` (no-assert) → **skill `build-verify`** green → **skill `update-sitemap`**.

## Step 4 — Bug Report for dev (MAIN DELIVERABLE)
Per `exploratory-method`: write `reports/exploratory/<group>/dev-bug-report-<ddMMMyyyy>.md` following the template (each bug: Screen · Verbatim symptom · Root cause if found · Impact · Expectation · Evidence · Defect ID) + a **✅ Checked — NO bug** section + **❓ NEEDS-TRIAGE** + environment notes. Append each `[APP-BUG]` to the register `reports/exploratory/bug-summary.md`.

## Step 5 — GATE DECISION + finish
- 🔴 **Has `[APP-BUG]`** → deliverable = bug report for dev. Do **NOT** `/qa:plan-tests`/`/qa:cook` for the broken part.
- 🟢 **No `[APP-BUG]`** → app correct → Screen/elements extracted → suggest **`/qa:plan-tests <feature-name>`**.

Close the session (`appium_quit_session` / `browser_close`). Print: platform, bug report path (+ register), list of `[APP-BUG]`, Screen/sitemap updated (if clean), **gate conclusion**.
