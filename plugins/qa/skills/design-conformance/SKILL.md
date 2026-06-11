---
name: design-conformance
description: Reusable logic to check the UI of the app under test against the project's design system (Figma → DESIGN_SYSTEM_DIR folder) — checking color/typography/corner-radius/state against tokens (usually Material 3). Used by the exploratory command (Step 2b) and referenced by review-*. Flutter/native apps don't let Appium read color/font via elements, so checks are primarily multimodal (comparing app screenshots vs token/spec). A design deviation = [APP-BUG] design deviation per failure-triage.
---

# Skill: design-conformance

Reusable capability: for a screen / a type of UI currently open on the real app → **check against the app's design system** and produce design-deviation findings. The reference baseline lives in the project's design-system folder (`<DESIGN_SYSTEM_DIR>`, default `design-system/`). Full rules: [design-system-figma.md](../../rules/app/design-system-figma.md). Deviation classification: [failure-triage.md](../../rules/failure-triage.md).

> Distinction: this skill checks the **APP's design system** (UI: color/typo/M3 components). DIFFERENT from [design-system.md](../../rules/app/design-system.md) — the test codebase standard (POM/naming).

## Why multimodal-first
Flutter/native apps → Appium sees a flat tree and **CANNOT read hex color / font-weight / pixels** via element attributes. Therefore:
- **Check by image** (primary): take a screenshot of the app screen, then have Claude look at it and compare against the tokens + the component's `referenceScreenshot`.
- **Structural (secondary, cheap)**: use element bounds to check the measurable — button touch area ≥48px, segments of equal height, dialog not overflowing the edge.

## Procedure
1. **Identify the UI type** on the screen (button, popup/dialog, segmented button strip, text field, card…). Map to the component in `<DESIGN_SYSTEM_DIR>/manifest.json`.
   - status `done` → has a spec, can be checked.
   - status `pending` (not yet extracted) → do NOT conclude; attach `[NEEDS-TRIAGE]` + (optionally) add the spec per `<DESIGN_SYSTEM_DIR>/README.md` (needs the Figma URL/node-id; figma MCP only runs from the main agent).
2. **Load the baseline**: `<DESIGN_SYSTEM_DIR>/tokens.json` (color/typography/shape/elevation) + `components/<type>.json` (variant, `conformanceChecklist`, `referenceScreenshot`).
3. **Screenshot the app** (skill [capture-screenshot](../capture-screenshot/SKILL.md) / rule [screenshot-evidence.md](../../rules/screenshot-evidence.md) — this skill Reads many images, so the many-image cap is a real risk): take `mcp__plugin_qa_appium__appium_screenshot` with **`maxWidth: 720`** (locate via ToolSearch; downscaling to ~720px wide preserves color/typography fidelity for the comparison while keeping the image under the cap). For an archived full-res copy, capture to `sitemap/screenshots/<name>.png` via `adb -s <serial> exec-out screencap -p > <path>` / `xcrun simctl io <udid> screenshot <path>` and **downscale before Reading** (`scripts/downscale_image.py`). If the cap trips, you can no longer judge color visually — record the remaining items as `[NEEDS-TRIAGE]` and resume in a fresh run rather than guessing. NOT to Desktop.
4. **Check** each `conformanceChecklist` item: background/text color vs token (brand primary/secondary taken from `tokens.json`), corner radius, font size against the typography scale, presence of a state-layer when pressed. Compare visually against `referenceScreenshot`.
5. **Classify & record** each deviation (per failure-triage):
   - App renders wrong vs Figma → `[APP-BUG]` *design deviation* (with screenshot + expected token/spec + actual). Report to dev, do NOT patch the test to dodge it.
   - We mapped the wrong component / the spec is wrong → `[FRAMEWORK]` (fix the spec in `<DESIGN_SYSTEM_DIR>/`).
   - No spec yet → `[NEEDS-TRIAGE]`.

## Output
A list of design findings: `UI type | checklist item | expected (token/spec) | actual | triage | screenshot`. Put `[APP-BUG]` into the **🐛 App defects** section of the exploratory report; in the HTML run report use `Utils.failCap(driver, node, "[APP-BUG] <screen> design deviation: <details> (expected <token>)")`.

## Limits (honesty)
- Conclusions about color/typography deviation must be based on a clear image — do NOT infer from element attributes.
- Px measurements in the spec marked `_*Note`/`dataProvenance` (M3 default) are not a hard baseline until verified with `get_design_context`.
- Component coverage is still incomplete (see `manifest.json`) — only check `done` components.
