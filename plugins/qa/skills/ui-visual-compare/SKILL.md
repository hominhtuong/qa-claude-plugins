---
name: ui-visual-compare
description: Reusable logic to compare ONE screen pair — a Figma reference frame (fm_*.png) vs an app screenshot (ss_*.png) — using the local CV engine (scripts/ui_compare.py in the ui-engine venv). The heavy image math (color CIEDE2000 Delta-E, SSIM, palette, perceptual-hash, histogram) runs LOCALLY and returns a tiny JSON verdict (PASS/WARN/FAIL + a dozen numbers) plus a diff heatmap; appends every run to model-log.jsonl for model-efficiency tracking. The AI reads only the small JSON — never the raw pixels — so a whole run costs almost no vision tokens. Used by exploratory-ui-method per pair.
---

# Skill: ui-visual-compare

Reusable capability: given **one pair** of images already on disk — the Figma reference
`fm_*.png` and the app screenshot `ss_*.png` — run the **local CV engine** to decide whether the
app's color/layout matches the design, and emit a compact machine verdict the AI can reason over
cheaply. This is the token-saving core of /qa:exploratory-ui: **the model runs locally, the AI only
reads the result.** Metric meanings + thresholds: [ui-visual-compare.md](../../rules/ui-visual-compare.md).

> Prerequisite: the engine is `READY` (skill [ui-engine-check](../ui-engine-check/SKILL.md) resolved
> `venv_python` + `config_path`). Never run `ui_compare.py` with the system `python3` — it needs the
> venv's cv2/skimage.

## Procedure (per pair)

1. **Inputs** (provided by the caller / `exploratory-ui-method`):
   - `venv_python`, `config_path` — from `ui-engine-check`.
   - `reference` = `results/<feature>/ui-compare/figma/fm_<id>.png`
   - `actual` = `results/<feature>/ui-compare/app/ss_<id>.png`
   - `pair_id` (e.g. `hd001`), `screen` (human name), `feature`.

2. **Run the comparison** (heavy work, LOCAL — no image enters the AI context):
   ```bash
   <venv_python> ${CLAUDE_PLUGIN_ROOT}/scripts/ui_compare.py \
     --reference results/<feature>/ui-compare/figma/fm_<id>.png \
     --actual    results/<feature>/ui-compare/app/ss_<id>.png \
     --pair-id <id> --screen "<Screen name>" --feature <feature> \
     --out  results/<feature>/ui-compare/pairs/<id>.json \
     --log  results/<feature>/ui-compare/model-log.jsonl \
     --diff results/<feature>/ui-compare/diffs/<id>-heatmap.png \
     --thresholds <config_path>
   ```
   It prints (and writes to `--out`) a small JSON: `verdict`, `reasons[]`, and `metrics{}`
   (`deltaE_mean`, `deltaE_p95`, `color_perceptible_pct`, `palette_deltaE`, `ssim`, `hist_corr`,
   `phash_distance`, `aspect_delta`, `color_match_pct`). It also **appends one line to
   `model-log.jsonl`** (the model-efficiency tracking log) and writes a **diff heatmap** PNG.

3. **Read ONLY the small JSON** (`pairs/<id>.json` / stdout) — do NOT Read the source screenshots.
   Interpret the verdict:
   - **PASS** — color + structure within tolerance. Record as ✅ checked, no defect.
   - **WARN** — borderline (e.g. slight tint, minor structural drift). Note it; the AI MAY Read the
     **downscaled** actual + reference to judge whether it's a real issue (use `scripts/downscale_image.py`).
   - **FAIL** — clear deviation. **Now (and only now) it's worth a few vision tokens**: Read the
     **heatmap** (`diffs/<id>-heatmap.png`, downscaled if >2000px) to SEE where it diverges, confirm
     it's a real design deviation (not a data/state difference), and capture the specifics
     (expected token/color vs actual) for the report.

4. **Triage the FAIL** per [failure-triage.md](../../rules/failure-triage.md):
   - App renders a different color/layout than Figma → `[APP-BUG] design deviation` (cite the
     metric: *"header mean Delta-E 7.1, expected brand primary #2196F3, app shows greenish"*).
   - The mismatch is because the app's DATA/state differs from Figma's sample (different list,
     empty vs filled) → NOT a bug; note it and, if `--seed` is in play, re-seed + re-capture.
   - Aspect/canvas mismatch (`aspect_delta` high) → likely wrong frame paired or wrong device size →
     `[NEEDS-TRIAGE]`, re-pair before concluding.

## Output
Per pair: the verdict JSON (`pairs/<id>.json`), one `model-log.jsonl` line, and a heatmap PNG.
Hand the verdict + (for FAIL) the confirmed deviation details back to `exploratory-ui-method` for the
aggregate report. The model-log is a first-class output — it accumulates across runs so the team can
measure how reliably the engine flags real deviations and re-tune the thresholds in the config.

## Token discipline (the whole point)
- Default: the AI Reads **zero** screenshots — it reasons over the numeric verdict only.
- Read an image **only** for `FAIL` (the heatmap) and optionally `WARN`, and always **downscaled**.
- Never paste raw metric dumps for every pair into prose — summarize per screen in the report.
