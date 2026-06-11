# Rule: UI visual comparison — metrics, thresholds & how to read them

Stable reference for the local CV engine behind **/qa:exploratory-ui** (scripts `ui_compare.py` /
`ui_engine.py`, skills `ui-visual-compare` / `exploratory-ui-method`). It explains every number the
engine emits so the report cites the right cause and the thresholds can be tuned with intent.

## Why local CV (not an AI vision call) for "is the color right"
Color sameness is a **measurable, deterministic** question. A perceptual color metric answers it
exactly and for free, on-device — no model download, no per-image token cost. The AI is reserved for
**judgement** (is this flagged deviation a real design bug or just different data?), which it does by
reading a handful of numbers and, only for failures, one heatmap. That split is the whole point:
**model does the measuring, AI does the deciding.**

## The engine
A dedicated venv at `.claude/qa-claude/ui-engine/venv/` with `numpy · opencv-python-headless ·
scikit-image · Pillow · imagehash`. Installed/repaired by `/qa:ui-engine-install`
(`scripts/ui_engine.py install`); state resolved by `scripts/ui_engine.py check`. Config +
thresholds: `.claude/qa-claude/ui-engine.config.json` (per project, git-ignored, tunable).

## Inputs
One **pair** of PNG files: `fm_<id>.png` (Figma frame, rendered to a file by `figma_export.py`) and
`ss_<id>.png` (app screenshot captured via the platform MCP). The engine scales the reference to a
working canvas (`--work`, default 768px longer side) and resizes the actual onto the same canvas so
every metric lines up pixel-for-pixel.

## Metrics (what each one catches)
| Metric (key) | What it measures | Good | Bad |
|---|---|---|---|
| **Color Delta-E mean** (`deltaE_mean`) | CIEDE2000 perceptual color distance averaged over the frame. **The headline "is the color right" number.** | < 2 (imperceptible) | ≥ 6 (clearly wrong color somewhere) |
| **Color Delta-E p95** (`deltaE_p95`) | 95th-percentile Delta-E — a strong **local** miscolor (one region very wrong) even if the mean is okay. | low | ≥ 12 |
| **Perceptible area %** (`color_perceptible_pct`) | % of the frame where Delta-E > 5 (visibly off). | ~0% | large |
| **Palette Delta-E** (`palette_deltaE`) | Distance from each dominant design color to its nearest app color (k-means palettes). Coarse brand-color check. | low | high |
| **SSIM** (`ssim`) | Structural similarity over grayscale — layout/spacing/shape/edges. | ≥ 0.95 | ≤ 0.80 |
| **Histogram correlation** (`hist_corr`) | HSV color-distribution correlation — global tint/theme drift (e.g. dark vs light, wrong accent everywhere). | ≥ 0.95 | ≤ 0.85 |
| **pHash distance** (`phash_distance`) | Perceptual-hash Hamming distance — gross composition change (wrong screen, big content shift). | 0–6 | ≥ 12 |
| **Aspect delta** (`aspect_delta`) | How different the two frames' aspect ratios are — high = wrong device size or mis-paired frame (metrics then computed on a forced canvas, treat with care). | ~0 | ≥ 0.15 |
| **Color match %** (`color_match_pct`) | Friendly 0–100 reskin of `deltaE_mean` for the report (10 Delta-E → 0%). | ~100 | low |

## Verdict
`ui_compare.py` rolls the metrics into **PASS / WARN / FAIL** (see `_verdict`):
- **FAIL** if any: `deltaE_mean ≥ deltaE_mean_fail`, `deltaE_p95 ≥ deltaE_p95_fail`,
  `ssim ≤ ssim_fail`, `phash_distance ≥ phash_fail`, or `hist_corr ≤ hist_corr_fail`.
- **WARN** if borderline: `deltaE_mean ≥ deltaE_mean_warn`, `ssim ≤ ssim_warn`,
  `hist_corr ≤ hist_corr_warn`, or `aspect_delta ≥ 0.15`.
- **PASS** otherwise. Each verdict carries human `reasons[]` citing the exact number that fired.

### Default thresholds (`ui-engine.config.json` → `thresholds`)
```
deltaE_mean_warn 3.0 · deltaE_mean_fail 6.0 · deltaE_p95_fail 12.0
ssim_warn 0.90 · ssim_fail 0.80
phash_fail 12
hist_corr_warn 0.92 · hist_corr_fail 0.85
```
Tune per project by editing the config (no reinstall). Tighten Delta-E for brand-strict UIs; loosen
SSIM for content-heavy screens whose data legitimately varies.

## How to read a verdict (triage)
1. **PASS** → ✅ checked, no defect.
2. **WARN** → judge from the numbers; Read the **downscaled** images only if genuinely ambiguous.
3. **FAIL** → Read the **heatmap** (`diffs/<id>-heatmap.png`, JET overlay showing *where* it diverges)
   and triage per [failure-triage.md](failure-triage.md):
   - render differs from Figma → **`[APP-BUG]` design deviation** — cite the metric + expected token
     (cross-check the design system via [design-conformance](../skills/design-conformance/SKILL.md)).
   - difference is the app's **data/state**, not its design → `[DATA]` (use `--seed` to neutralize).
   - high `aspect_delta` / no design baseline / wrong pairing → `[NEEDS-TRIAGE]`, re-pair first.

## The model-efficiency log
Every comparison appends a line to `results/<feature>/ui-compare/model-log.jsonl`
(`ts, feature, pair_id, screen, verdict, metrics, thresholds, sizes`). It is a **first-class
output**: over many runs it shows how often each threshold fires and whether the engine's PASS/FAIL
calls match reality — the basis for re-tuning thresholds and for trusting the automation. The report's
"Hiệu quả model" section summarizes it (counts by verdict, mean Delta-E, which thresholds dominated).

## Honesty / limits
- A clean comparison needs a clean pair: same screen, same state, comparable canvas. Garbage pairing
  → garbage verdict. Resolve `aspect_delta`/mis-pairs before concluding a bug.
- The engine sees **pixels**, not intent. It can't tell a deliberate redesign from a regression — the
  Figma frame is the oracle; if the design itself changed, update the reference.
- Anti-aliasing/sub-pixel text rendering causes small SSIM/Delta-E noise — that's why thresholds
  aren't zero. Don't drive thresholds to perfection; calibrate against the model log.
