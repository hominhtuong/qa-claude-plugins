---
name: exploratory-ui-method
description: A design-conformance exploratory method for /qa:exploratory-ui — pair each Figma frame (fm_*) with its app screenshot (ss_*), drive the local CV engine over every pair via the ui-visual-compare skill (color Delta-E / SSIM / palette / hash run LOCALLY → tiny JSON verdicts), aggregate per-screen PASS/WARN/FAIL into a UI-conformance report, triage FAILs as [APP-BUG] design deviation, write the model-efficiency log summary, and make the GATE decision — all while keeping the AI's token cost near-zero (it reads verdict JSON, not raw pixels). The reusable core behind the exploratory-ui command.
---

# Skill: exploratory-ui-method

Reusable capability: run a **design-conformance sweep** of a feature — does the built app screen
look like its Figma design (color first, then layout/structure)? — by orchestrating the **local CV
engine** over every screen pair and synthesizing the results into a dev-facing report. The design
goal is **maximum local processing, minimum AI tokens**: the model (opencv/scikit-image) reduces
each screen pair to a small JSON verdict; the AI only reasons over those verdicts and looks at an
image **only** for the screens the engine flagged. Metric/threshold reference:
[ui-visual-compare.md](../../rules/ui-visual-compare.md). Triage standard:
[failure-triage.md](../../rules/failure-triage.md).

> Relationship to siblings: this is the **multi-screen orchestrator + reporter**.
> [ui-visual-compare](../ui-visual-compare/SKILL.md) does ONE pair; [ui-engine-check](../ui-engine-check/SKILL.md)
> resolves the engine; [design-conformance](../design-conformance/SKILL.md) is the token-token/spec
> check used by plain /qa:exploratory. exploratory-ui adds the **pixel-level local CV** layer on top.

## Inputs (from the command)
- `feature` (folder slug, no diacritics), `platform` (web/android/ios), resolved output `language`.
- Engine `venv_python` + `config_path` + `ocr_backend` (from `ui-engine-check`, state READY).
- Figma frames on disk: `results/<feature>/ui-compare/figma/fm_*.png` + `figma/manifest.json` +
  **`figma/text-styles.json`** (the exact design TEXT oracle) (from `scripts/figma_export.py`), and
  the `figma-reader` summary for human screen names/specs.
- App screenshots on disk: `results/<feature>/ui-compare/app/ss_*.png` (captured by the command via
  the platform MCP, optionally after the `ui-seed-data` `--seed` step).

## Procedure

1. **Pair the screens** (`fm_<id>` ↔ `ss_<id>`). Build a pairing table from `figma/manifest.json`
   (frame index/name/node-id) and the captured screenshots. Pair by the shared `<id>` the command
   assigned when it captured each screen (e.g. Figma frame "Hóa đơn" → `fm_001-…` ↔ app capture
   `ss_001-…`). Record any **unpaired** items:
   - Figma frame with no app screenshot → screen not reached/captured → `[NEEDS-TRIAGE]` (couldn't verify).
   - App screenshot with no Figma frame → extra/undesigned screen → note it; don't compare.

2. **Compare every pair** via skill [ui-visual-compare](../ui-visual-compare/SKILL.md) — one
   `ui_compare.py` run per pair. **When `ocr_backend` ≠ none, also pass the text layer**
   (`--design-text figma/text-styles.json --design-slug fm_<id>… --ocr-langs vie+eng`) so the same
   call does color/font/layout AND text-vs-design (skill [ui-text-compare](../ui-text-compare/SKILL.md)).
   Each produces `pairs/<id>.json` + a `model-log.jsonl` line + a heatmap. **Do not Read the
   screenshots** — collect the small verdict JSONs.

3. **Read the verdicts** (`pairs/*.json`) — for each screen lead with `summary_by_type` (which of
   `text.mismatch` / `color.background` / `color.text` / `typography.weight` / `typography.size` /
   `typography.family` / `layout.shift` / `layout.align` failed, in how many regions) then `findings[]`
   for the quotable specifics. Bucket each screen PASS / WARN / FAIL.
   - **Text findings**: apply rule [ui-text-rules.md](../../rules/ui-text-rules.md) — a `text.mismatch`
     with `likely_dynamic=false` on a STATIC label (title/button/field label) → `[APP-BUG]` (cite
     *design "Products" → app "Product"*); `likely_dynamic=true` (data/number/name) → **ignore the
     content**. Guard against OCR noise on 1–2 char/accent diffs (verify on the image).
   - For **FAIL** screens only: Read the **heatmap** (`diffs/<id>-heatmap.png`, downscale first if
     >2000px via `scripts/downscale_image.py`) to confirm + localize, and — when a design token
     baseline exists — cross-check the expected color/type against the design system per
     [design-conformance](../design-conformance/SKILL.md) (so the report cites *expected #2196F3 /
     Bold 16sp*, not just a number). For a `typography.family` finding (LOW confidence) ALWAYS
     eyeball the image before asserting it — it's a shape hint, not OCR.
   - For **WARN**: judge from the numbers; Read images only if genuinely ambiguous.

4. **Triage each FAIL/WARN** → `[APP-BUG] design deviation` vs `[DATA]`/state difference vs
   `[NEEDS-TRIAGE]` (no design baseline / mis-pair / wrong device size). A real deviation cites:
   screen · **which attribute** (nền/chữ-màu/đậm-nhạt/cỡ/font/bố cục) + region · the number (ΔE, stroke
   %, size %, SSIM) · expected (token/Figma) vs actual · heatmap path as evidence. Quote the finding's
   `detail` string directly — it's already phrased.

5. **Write the UI-conformance report** `results/<feature>/ui-conformance-report-<ddMMMyyyy>.md` —
   **PLAIN LANGUAGE, NOT technical**, following
   [ui-conformance-report-template.md](../../rules/ui-conformance-report-template.md), in the configured
   output language (default Vietnamese with diacritics — [output-language.md](../../rules/output-language.md)).
   > 🎯 **The bar:** anyone reading a bug must instantly get it and be able to log it. **Do NOT put raw
   > SSIM/ΔE/stroke numbers in the report** — translate them: *"Design: text 'Products', chữ #000000,
   > nền #FFFFFF, font Arial Regular; Thực tế: 'Product', chữ #909090, nền #393939, font giống Times."*
   > The technical numbers stay in `pairs/*.json` + `model-log.jsonl` (for tuning the engine).
   - **Tổng quan**: feature, platform, device/viewport, OCR backend, # screens, Đạt/Có-lỗi counts.
   - **Bảng tổng quan từng màn**: `Màn | Kết luận (🟢/🟡/🔴) | Vấn đề chính (ngắn)`.
   - **🐛 Lỗi cần sửa**: one `### Lỗi N` per issue with **Design:** (exact Figma tokens — text/màu/nền/
     font/cỡ) vs **Thực tế:** (app text + measured hex + font class) + **Sai:** (thuộc tính nào) + 📷
     heatmap path. Make each block `/qa:log-bug`-ready (see template + the bug-report-import mapping).
   - **✅ Đã kiểm tra — khớp** + **❓ Cần xác nhận (NEEDS-TRIAGE)** (unpaired screens, no baseline, OCR off,
     low-confidence font, seeding skipped).
   Append each confirmed `[APP-BUG]` to the cross-feature register `results/bug-summary.md`.

6. **GATE decision** (mirrors /qa:exploratory):
   - 🔴 **Has `[APP-BUG]` design deviation** → deliverable = this report for dev/designer. Suggest
     pushing to the board with **`/qa:log-bug from <feature>`** (imports the report).
   - 🟢 **All PASS (no deviation)** → UI matches design → the feature's visual layer is clean.

## Token discipline
- The AI Reads **only** FAIL heatmaps (and rare WARN images), always downscaled. Everything else is
  numeric. A 15-screen feature should cost a handful of images at most, not 30 raw screenshots.
- Keep per-screen prose short; the verdict table carries the detail.

## Output
`results/<feature>/ui-compare/` (figma/ app/ pairs/ diffs/ + `model-log.jsonl`) and the report
`ui-conformance-report-<ddMMMyyyy>.md`, the register update, and the gate conclusion. The model-log
persists across runs as the engine's effectiveness ledger.
