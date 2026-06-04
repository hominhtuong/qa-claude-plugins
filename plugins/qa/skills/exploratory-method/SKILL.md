---
name: exploratory-method
description: A senior-QA-style exploratory testing method to hunt app bugs, independent of the platform driver (the command supplies the driver skill navigate-web for web / navigate-app for app; element extraction via find-elements-web/-android/-ios). Covers probing the main interactions, critically reading figures/messages, on-the-spot triage, capturing evidence, writing a bug report for the dev, syncing the register, and the GATE DECISION. The reusable core behind the exploratory command.
---

# Skill: exploratory-method

Reusable capability: probe a feature → **find app bugs** → bug report for the dev + gate decision. Platform-agnostic: the command supplies the driver (web → `navigate-web` skill, app → `navigate-app` skill) and the element extractor (`find-elements-web`/`-android`/`-ios`). Standards: [failure-triage.md](../../rules/failure-triage.md), [exploratory-bug-report-template.md](../../rules/exploratory-bug-report-template.md).

> ⚠️ **The app may be broken** (a port/incomplete build) → do NOT assume the app is correct by default. Every wrong observation **MUST** be triaged with a label, not skipped, not guessed.

## Procedure
1. **Stand on the right feature screen**: use the driver skill the command supplies (`navigate-app`/`navigate-web`) to open the app, go to Home, and navigate to the feature screen — read `sitemap/sitemap.json` first if it exists (it may already know the path).
2. **Record the navigation map** (skill `update-sitemap`) — **for EVERY screen you pass through** (Home → … → feature, and any sub-screens you open): write/update `sitemap/screens/<id>.json` with the `reach` steps (web: route + clicks · app: the tap actions), `parentId` (where you came from), `keyElement`, `route` (web) / `null` (app), and `notes`. **Do this even if the feature is buggy** — the navigation map is the value later cases use to reach the feature. Regenerate `sitemap.json` at the end (`scripts/gen_sitemap.py`).
3. **Probe the main interactions**: open/close, filter, create/edit, **open an item's detail**, validate **empty/boundary** input (negative values, max length, odd characters). Note what's correct/wrong, crashes, UI bugs, edge cases.
4. **Read figures/messages CRITICALLY**: wrong totals, nonsensical negative numbers, English text leaking through, raw SQL/exception/stacktrace exposed in the UI, context-wrong messages. Extract **verbatim** (via page source) to paste into the report.
5. **On-the-spot triage** ([failure-triage.md](../../rules/failure-triage.md)): each wrong behavior → reproduce manually on the app right away to decide **`[APP-BUG]`** (app is wrong — reproducible) vs `[FRAMEWORK]` (we grabbed the wrong element/automation) vs `[ENV]`/`[DATA]`. Only `[APP-BUG]` goes into the bug section.
6. **Capture evidence** → **always pass the FULL relative path as the screenshot tool's `filename`**, never a bare file name (a bare name lands in the MCP output dir / project root, not here). Web = `browser_take_screenshot` with `filename: "results/exploratory/<feature>/screenshots/<BUG-ID>.png"`; app = `appium_take_screenshot` saved to the same path. **Named by BUG-ID** (e.g. `results/exploratory/<feature>/screenshots/02-APP01-published-tab-crash.png`). Each `[APP-BUG]` ≥1 image; also save a few OK-screen images (`..-ok.png`) as proof of "checked".
7. **Bug report for the dev**: write `results/exploratory/<feature>/dev-bug-report-<ddMMMyyyy>.md` in the **exact format** of [exploratory-bug-report-template.md](../../rules/exploratory-bug-report-template.md) — each bug: Screen · Symptom (verbatim) · Root cause (if found) · Impact · Expectation · Evidence · Defect ID. Include a **✅ Checked — NO bug** section + **❓ NEEDS-TRIAGE** + environment notes. Write the report in Vietnamese.
8. **Sync the register**: append each `[APP-BUG]` into `results/exploratory/bug-summary.md` (assign APP-ID, update the per-function count table + severity distribution).

## GATE decision
- 🔴 **Has `[APP-BUG]`** → the feature is NOT done. **Deliverable = bug report** for the dev. Do **NOT** proceed to `/qa:plan-tests`/`/qa:cook` for the broken part (only cleanly separable clean parts move on).
- 🟢 **No `[APP-BUG]`** (only possibly FW/ENV/DATA) → app is correct → extract clean elements → ready for **`/qa:plan-tests`**.

> *Automation runs only when the app is already correct.* Planning is the `plan-method` skill; automation errors (FW) are fixed via the `fix-by-layer` skill, NOT recorded in the app bug section.
