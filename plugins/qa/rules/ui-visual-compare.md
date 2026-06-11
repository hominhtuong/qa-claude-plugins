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

The global numbers answer *"is something off?"* but can't tell **background from text**, nor a
**heavier** font from a **bigger** one. That's what the per-region layer is for.

## Typed findings (per region) — *HOW* it's wrong

The aligned frames are split into a grid (`grid_rows`×`grid_cols`, default 6×4). In each cell the
engine separates **background vs foreground (text)** colors (2-means) and, on the text mask, measures
weight/size/shape. Each difference beyond tolerance becomes a typed **finding** with a region label
(`r2c1`) + a human position (`giữa-trái`). The AI reads `findings[]` + the rolled-up
`summary_by_type{}` — it doesn't recompute anything. Finding types:

| `type` | Detects | Signal (local, per cell) | Default warn / fail |
|---|---|---|---|
| `color.background` | wrong **fill/background** color | CIEDE2000 between the two cells' dominant (background) colors; reports `ref`/`actual` hex | ΔE 3 / 6 |
| `color.text` | wrong **text/foreground** color | CIEDE2000 between the minority contrasting (text) colors; hex each side | ΔE 4 / 8 |
| `typography.weight` | **đậm/nhạt** (bold vs regular) | stroke width = 2×mean distance-transform of the text mask; compared as `abs(Δ)/ref` ratio | 15% / 25% |
| `typography.size` | **font size** | median glyph height via connected components; `abs(Δ)/ref` ratio (device-normalized on the common canvas) | 10% / 18% |
| `typography.family` | **different font family** (serif vs sans …) | edge-orientation histogram (12 bins) distance over text pixels. **LOW confidence** — flagged for the human to confirm; suppressed in a cell that already shows a weight change | dist 0.07 / 0.11 |
| `layout.shift` | **bố cục / căn chỉnh** drift | local SSIM of the cell (lower = more structural drift) | SSIM 0.82 / 0.62 |
| `content.flat` | design region has text but the app cell is ~flat | foreground present in ref, absent in actual (possible missing text or different state/data) | warn only |

Each finding carries a `detail` string already phrased in Vietnamese (e.g. *"màu nền lệch ΔE 50.9
(design #2196F3 → app #34A853)"*, *"độ đậm chữ khác: app đậm hơn ~46% (stroke 3.50→5.10)"*), so the
report can quote it directly. `summary_by_type` gives `{fail, warn, regions[]}` per type for a quick
roll-up. Findings are capped (top ~14 by severity) to stay token-cheap.

> **Device tolerance & honesty (the user's bar):** thresholds are perceptual, not zero — small
> anti-aliasing / DPI noise passes (an identical pair yields **no** findings). But a difference the
> eye would catch must fail: serif-vs-sans, a clearly bolder weight, a visibly different size or a
> wrong background/text color all trip a finding. `typography.family` is deliberately marked
> low-confidence (shape, not OCR) — surface it, but let the human/AI confirm via the heatmap/image.

## Verdict
`ui_compare.py` rolls the global metrics **and** the typed findings into **PASS / WARN / FAIL**
(see `_verdict`):

- **FAIL** if any global fail (`deltaE_mean ≥ deltaE_mean_fail`, `deltaE_p95 ≥ deltaE_p95_fail`,
  `ssim ≤ ssim_fail`, `phash_distance ≥ phash_fail`, `hist_corr ≤ hist_corr_fail`) **OR any region
  finding has severity `fail`** (a wrong background/text color, weight, size, family or layout in
  even one region).
- **WARN** if borderline global (`deltaE_mean ≥ deltaE_mean_warn`, `ssim ≤ ssim_warn`,
  `hist_corr ≤ hist_corr_warn`, `aspect_delta ≥ 0.15`) **OR any region finding is `warn`**.
- **PASS** otherwise. `reasons[]` cite the exact numbers + which attribute failed in which regions.

### Default thresholds (`ui-engine.config.json` → `thresholds`)
```
# global
deltaE_mean_warn 3.0 · deltaE_mean_fail 6.0 · deltaE_p95_fail 12.0
ssim_warn 0.90 · ssim_fail 0.80 · phash_fail 12 · hist_corr_warn 0.92 · hist_corr_fail 0.85
# per-region color (background vs text separated)
bg_deltaE_warn 3.0 · bg_deltaE_fail 6.0 · text_deltaE_warn 4.0 · text_deltaE_fail 8.0
# per-region typography
stroke_ratio_warn 0.15 · stroke_ratio_fail 0.25   (weight / đậm-nhạt)
size_ratio_warn 0.10 · size_ratio_fail 0.18       (font size)
shape_dist_warn 0.07 · shape_dist_fail 0.11       (font family — low confidence)
# per-region layout + grid
cell_ssim_warn 0.82 · cell_ssim_fail 0.62 · grid_rows 6 · grid_cols 4
```
Tune per project by editing the config (no reinstall). Tighten color/stroke for brand-strict UIs;
loosen `cell_ssim` / `size_ratio` for content-heavy screens whose data legitimately varies; raise
`grid_rows`×`grid_cols` for denser localization (more cells = finer regions, a little slower).

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
