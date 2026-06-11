---
description: Design-conformance exploratory — open a feature screen (web/android/ios), capture screenshots, render the Figma design to PNGs, then compare each app screen vs its design using a LOCAL CV engine (color CIEDE2000 Delta-E / SSIM / palette / perceptual-hash) so heavy image work runs locally and only tiny JSON verdicts reach the AI. Aggregates PASS/WARN/FAIL into a UI-conformance report + [APP-BUG] design deviations, with a model-efficiency log. Auto-routes by platform. Optional --seed recreates Figma sample data first.
argument-hint: <feature-name>[: <figma-url>] [web|android|ios] [nav path] [--seed] [--figma <url>] [--scale 2]
allowed-tools: Read, Glob, Grep, Edit, Write, Bash, Agent, WebFetch, ToolSearch
---

# /qa:exploratory-ui — Check the built UI against the Figma design (local CV, low-token)

Feature + design to verify: **$ARGUMENTS**

**Goal — does the app screen match its design, and HOW does it differ?** The local CV engine
(opencv + scikit-image) analyzes per region and returns **typed findings**, not just "different":
**bố cục** (layout/alignment) · **màu sắc** tách riêng *nền* vs *chữ* (hex + ΔE) · **font** —
*family* (serif/sans), *độ đậm* (weight/stroke), *cỡ chữ* (size). The model does the heavy lifting;
the AI reads compact typed verdicts → near-zero vision tokens. Tolerances are perceptual + device-
tolerant (near-identical fonts pass; a difference the eye would catch fails). Deviations become
`[APP-BUG] design deviation` in a dev-facing report, grouped by attribute.

> ⚠️ **Local-first, token-thrifty**: the engine reduces each screen pair to a small JSON
> (`deltaE_mean/p95`, `ssim`, `hist_corr`, `phash`, verdict). Read **raw screenshots only for FAIL**
> screens (the diff heatmap), always downscaled. Never dump 30 screenshots into context.
> ⚠️ **Suspect a deviation, but triage it** per [failure-triage.md](../rules/failure-triage.md): a real
> render mismatch = `[APP-BUG] design deviation`; a difference caused by the app's *data/state* (not
> design) = `[DATA]` (use `--seed` to neutralize it); no design baseline / mis-pair = `[NEEDS-TRIAGE]`.
> **LANGUAGE — RULE #1**: the report + all user-facing prose follow `.plugin.env` `LANGUAGE` (default
> **Vietnamese with diacritics**) — see [output-language.md](../rules/output-language.md). Resolve once at Step 0.

## Step 0 — Lock platform, feature folder, args (routing)
Run **skill `detect-platform`** → one `platform` (web/android/ios). Resolve the output `language`.
Parse `$ARGUMENTS`:
- **`<feature-name>`** → the results folder slug (kebab-case, **no diacritics**, e.g. `Hóa đơn` →
  `hoa-don`). All outputs live under `results/<feature-name>/` (`ui-compare/` for this command).
- **Figma URL** — taken from `<feature>: <url>`, a `@<url>`, or `--figma <url>`. Required (the design
  baseline). If absent, ask for it (or fall back to the design-system tokens via `design-conformance`
  with no pixel diff).
- **`--seed`** → recreate Figma sample data before capture (skill `ui-seed-data`). Default OFF.
- **nav path / device / viewport** → how to reach the screen; which device (app) / viewport (web).

Create `results/<feature-name>/ui-compare/{figma,app,pairs,diffs}/`.

## Step 1 — Engine gate (the local model)
Run **skill `ui-engine-check`** → resolve `venv_python` + `config_path` + `ocr_backend`.
- `READY` → continue. Tell the user: *"UI engine sẵn sàng (opencv …, OCR <tesseract|rapidocr|tắt>)"*.
  If `ocr_backend` = `none`, **text comparison is OFF** — note it (only color/font/layout checked) and
  suggest installing Tesseract `vie` via `/qa:ui-engine-install` for the text-vs-design check.
- `NOT-INSTALLED` / `NEEDS-DEPS` → **ask the user** to install via the install-helper
  **`/qa:ui-engine-install`** (one-time, ~30–60s). On consent, run it, then re-check → `READY`.
  On decline → offer the non-CV fallback (AI eyeballs Figma vs app screenshots, higher token cost) or stop.
- `NEEDS-SETUP` → it self-heals (config rewrite, no download).

## Step 2 — Read the Figma design → reference PNGs + summary
Two parallel reads of the SAME Figma URL:
1. **Render frames to files** (the CV reference images) — run:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/figma_export.py export --url "<figma-url>" \
     --out results/<feature-name>/ui-compare/figma --scale 2 --json
   ```
   It writes `figma/fm_<idx>-<slug>.png` per frame + `figma/manifest.json` (index · node-id · name)
   **and `figma/text-styles.json`** — the exact design TEXT oracle (each TEXT node's content + color +
   font + weight + size + bbox), keyed by the same slug. This is what the text layer compares the app's
   OCR'd text against (catch a changed static label, ignore dynamic values).
   Needs `FIGMA_TOKEN` in `.plugin.env` — if missing/invalid (exit 2), tell the user to add a Figma
   personal access token (Figma → Settings → Security), then retry. TLS error → `/qa:doctor --fix`.
2. **Structured summary + tracking** — spawn agent **`figma-reader`** (`figma_link`,
   `output_file: results/<feature-name>/figma-tracking/figma-summary.md`,
   `tracking_file: results/<feature-name>/figma-tracking/figma-tracking.md`). State the output
   language in the prompt (Vietnamese → *"tất cả tiếng Việt PHẢI có dấu"*). This gives human screen
   names + per-screen design notes (intended colors/states) for the report and for `--seed`.

Build the **screen list**: each Figma frame = one row `{idx, fm_file, node_id, name}` from the manifest.

## Step 3 — Open each screen on the app & capture (paired with the design)
Open the driver for the locked platform: **web** → skill `navigate-web` (Playwright MCP) · **android|ios**
→ skill `navigate-app` (Appium MCP: device preflight + install + GoToHome). Then **for each Figma
frame** in the screen list, in order:
1. Navigate to the matching app screen (per the nav path / sitemap).
2. **If `--seed`** → run skill **`ui-seed-data`** to recreate the frame's sample content/state first.
3. **Capture a full-res screenshot to a FILE** mirroring the frame's id —
   `results/<feature-name>/ui-compare/app/ss_<idx>-<slug>.png`:
   - **android**: `adb -s <serial> exec-out screencap -p > <path>`
   - **ios**: `xcrun simctl io <udid> screenshot <path>`
   - **web**: `browser_take_screenshot` with `filename` = the full relative path (full page).
   Use the **same `<idx>`** as the Figma frame so the pair is `fm_<idx>` ↔ `ss_<idx>`. Capture the
   screen in the SAME state the design shows (filled/empty/error). Skipped/unreachable screens →
   leave unpaired (the report marks them `[NEEDS-TRIAGE]`).

> Do NOT Read these screenshots into context here — they go to the local engine next. Viewing is only
> needed later for FAIL screens (downscale via `scripts/downscale_image.py` first).

## Step 4 — Compare every pair on the LOCAL engine — skill `exploratory-ui-method`
Hand `feature`, `platform`, `language`, `venv_python`, `config_path`, `ocr_backend`, and the paired
screen list to **skill `exploratory-ui-method`**. It drives **skill `ui-visual-compare`** once per
pair (`<venv_python> scripts/ui_compare.py …`). When `ocr_backend` ≠ none, ALSO pass the text layer
args so each call does color/font/layout **and** the text-vs-design check in one go:
`--design-text results/<feature-name>/ui-compare/figma/text-styles.json --design-slug fm_<idx>-<slug>
--ocr-langs vie+eng` (skill **`ui-text-compare`** + rule [ui-text-rules.md](../rules/ui-text-rules.md)).
Each pair emits `pairs/<idx>.json` (typed findings incl. `text.*`) + a `model-log.jsonl` line + a
`diffs/<idx>-heatmap.png`. The AI reads only the small JSONs (and the heatmap for FAIL screens) — all
CV/OCR math stays local.

## Step 5 — UI-conformance report + GATE — skill `exploratory-ui-method`
The same skill aggregates the verdicts into
`results/<feature-name>/ui-conformance-report-<ddMMMyyyy>.md` (configured language) **in PLAIN
LANGUAGE per [ui-conformance-report-template.md](../rules/ui-conformance-report-template.md)** —
each bug reads like *"Design: text 'Products', chữ #000000, nền #FFFFFF, font Arial Regular; Thực tế:
'Product', chữ #909090, nền #393939, font giống Times"*, NOT raw SSIM/ΔE numbers (those stay in
`pairs/*.json` + `model-log.jsonl`). Apply the static-vs-dynamic text rule. Structure: per-screen
overview table + **🐛 Lỗi cần sửa** (grouped, design vs thực tế, heatmap) + ✅ Đạt / ❓ NEEDS-TRIAGE.
Append each `[APP-BUG]` to `results/bug-summary.md`.
- 🔴 **Has deviation/label bug** → deliverable = report; suggest **`/qa:log-bug from <feature-name>`**.
- 🟢 **All PASS** → the UI matches the design.

## Step 6 — Finish
Close the session (`appium_quit_session` / `browser_close`). Print: platform + device/viewport,
engine versions, **feature folder** `results/<feature-name>/`, Figma frames rendered (count),
screens captured/paired (and any unpaired), report path, **model-log path**
`results/<feature-name>/ui-compare/model-log.jsonl`, list of `[APP-BUG]` design deviations, and the
**gate conclusion**.
