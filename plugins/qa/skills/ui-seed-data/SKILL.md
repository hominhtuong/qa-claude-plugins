---
name: ui-seed-data
description: Reusable logic for the --seed path of /qa:exploratory-ui — before capturing an app screenshot, read the SAMPLE values shown in the Figma frame (labels, numbers, list items, states) and recreate equivalent test data on the test account via the platform MCP (Appium type/tap for app, Playwright fill for web) so the app screen matches the design's content. This makes the screenshot-vs-Figma comparison fair (same content → differences are real color/layout deviations, not data noise). App-specific & best-effort; skipped without --seed.
---

# Skill: ui-seed-data

Reusable capability: a Figma frame usually shows **representative content** (a sample invoice, a
filled list, an error state). If the live app screen shows different data (empty list, other
numbers), a visual diff would flag that *content* difference as if it were a *design* bug. When the
user passes `--seed`, this skill **recreates Figma-equivalent data on the test account first**, so
the subsequent `ui-visual-compare` sees the same content and any remaining difference is a genuine
color/layout deviation.

> Default OFF. Without `--seed`, /qa:exploratory-ui compares the current state and the comparison
> is tolerant to data differences (focus on layout/color). With `--seed`, run this skill before the
> Step-3 capture. This is **best-effort and app-specific** — if a form can't be driven, fall back to
> tolerant compare and say so in the report.

## Procedure (only when `--seed`)

1. **Extract the sample content from the Figma frame** (already read by the `figma-reader` agent →
   `results/<feature>/figma-tracking/figma-summary.md`, and the rendered `fm_*.png`). For the target
   screen, list the concrete sample values the design displays:
   - field values (e.g. *Tên KH: "Nguyễn Văn A"*, *Tổng tiền: 1.250.000đ*),
   - list rows / counts (e.g. 3 line items),
   - the intended **state** (empty / filled / error / loading / success).
   Keep it to what's needed to make the screen look like the design — do NOT invent business data
   that violates validation.

2. **Locate the input path** to produce that state. Use the sitemap (`sitemap/screens/<id>.json`)
   and the platform navigation skill ([navigate-app](../navigate-app/SKILL.md) /
   [navigate-web](../navigate-web/SKILL.md)) to reach the create/edit form that feeds the target
   screen. If the design state is "list with N rows", that means creating N records.

3. **Seed via the platform MCP** (the command supplies the locked platform):
   - **app (Appium)** — `appium_find_element` (stable locator: id > accessibility > …) then
     `appium_set_value` / `appium_mobile_keyboard` to type, `appium_gesture` to tap Save. Confirm
     each save succeeded before moving on.
   - **web (Playwright)** — `browser_fill_form` / `browser_type` + `browser_click` to submit.
   Respect field validation (max length, format) — seed values that the app would actually accept.
   Never type secrets/credentials from the design; use safe placeholder data of the same shape.

4. **Reach the target screen in the seeded state** and hand control back to the command's Step-3
   capture (it screenshots `ss_<id>.png`). The screen should now mirror the Figma frame's content.

5. **Record what was seeded** in the run notes (`results/<feature>/ui-compare/seed-notes.md`):
   which screen, which values, created record ids (so they can be cleaned up later). This keeps the
   test account auditable and lets a re-run reproduce the same baseline.

## Guardrails
- **Test account only.** Never seed into a production/shared account. If unsure which account is
  active, STOP and ask — creating data is a side effect.
- **Best-effort.** If the form is unreachable, has unmapped elements, or validation blocks the
  Figma values, abort seeding for that screen, fall back to tolerant compare, and note it in the
  report (`seeding skipped: <reason>`) — never fake the screenshot.
- **Idempotence / cleanup.** Prefer reusing an existing matching record over creating duplicates.
  Log created ids so a later cleanup pass (or the user) can remove them.
- A design **error/empty/loading** state is produced by driving the app into that state (submit
  invalid input, clear the list), not by editing the screenshot.

## Output
A seeded test screen matching the Figma frame's content + `seed-notes.md` recording the values and
created record ids. On failure, a clear "seeding skipped" note so `ui-visual-compare` runs in
tolerant mode and the report explains why.
