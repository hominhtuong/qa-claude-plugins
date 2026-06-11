---
name: ui-text-compare
description: Reusable logic for the TEXT layer of /qa:exploratory-ui — compare the words the app renders against the design's exact text (Figma text-styles.json) so a changed STATIC label (design "Products" → app "Product") is caught while DYNAMIC values (list data, numbers, names) are ignored. The local engine extracts text (Figma tokens + OCR of the app screenshot via ui_ocr.py) and matches by position; this skill applies the static-vs-dynamic rule and turns confirmed mismatches into plain-language bug lines. Extraction = local model/script; the static/dynamic call = AI.
---

# Skill: ui-text-compare

Reusable capability: answer *"does the app's text match the design?"* — beyond color/font/layout.
The split is deliberate: **EXTRACTION is the local model's job** (exact design text from Figma +
OCR of the app screenshot), **CLASSIFICATION (static label vs dynamic value) is the AI's job**, per
[ui-text-rules.md](../../rules/ui-text-rules.md). This is how /qa:exploratory-ui catches a typo'd or
changed label without false-flagging data that legitimately differs from the Figma sample.

## Prerequisites
- Engine `READY` with an **OCR backend** (skill [ui-engine-check](../ui-engine-check/SKILL.md) →
  `ocr_backend` ∈ {tesseract, rapidocr}). If `none`, text comparison is skipped — say so in the
  report (only color/font/layout were checked) and suggest installing Tesseract `vie` via
  `/qa:ui-engine-install`.
- The **design text oracle**: `results/<feature>/ui-compare/figma/text-styles.json` (exact text +
  color + font + size + bbox per Figma TEXT node), written by `scripts/figma_export.py export`
  (or `text-styles`). Keyed by the same `fm_<idx>-<slug>` as the rendered PNGs.

## Procedure (per pair — runs inside the per-pair compare)

1. The text layer is built into `ui_compare.py`: pass `--design-text <…/figma/text-styles.json>
   --design-slug fm_<idx>-<slug> --ocr-langs vie+eng` alongside the normal compare args
   (skill [ui-visual-compare](../ui-visual-compare/SKILL.md)). It OCRs the app screenshot, maps each
   Figma TEXT node's bbox into the app's pixel space, finds the nearest app text line, and emits:
   - `text.mismatch` — design text ≠ app text. Carries `design_text`, `app_text`, `similarity`,
     `likely_dynamic`, and the design tokens (`design_color/font/weight/size`).
   - `text.missing` — design has a label but the app shows no text there.
   - `layout.align` — a matched label whose left edge moved a lot (canh lề lệch).

2. **Apply the static-vs-dynamic rule** ([ui-text-rules.md](../../rules/ui-text-rules.md)) to each
   `text.mismatch` — override the engine's `likely_dynamic` heuristic with judgement from context
   (Figma node role/position, screen purpose, the `figma-reader` summary):
   - **Static label** (title, button, field label, header, fixed copy) that differs → `[APP-BUG]`:
     typo, wrong word, missing diacritics, truncation, wrong language. (e.g. *Products → Product*).
   - **Dynamic value** (row data, number, price, date, name, status, id) → **ignore the content**.
   - `text.missing` → decide from context; if unsure `[NEEDS-TRIAGE]` and confirm on the screenshot.

3. **OCR-noise guard**: before calling a 1–2 character/accent difference a bug, sanity-check against
   the heatmap/screenshot — whole-word changes are reliable, a single wrong accent may be OCR (worse
   without the Tesseract `vie` pack). Never assert a text bug you can't see.

## Output
Confirmed static-label mismatches → plain-language bug lines per
[ui-conformance-report-template.md](../../rules/ui-conformance-report-template.md) (*design "X" → app
"Y"*), with the design tokens as the expected value and the heatmap as evidence. Dynamic values never
become bugs. Feeds the aggregate report in [exploratory-ui-method](../exploratory-ui-method/SKILL.md).
