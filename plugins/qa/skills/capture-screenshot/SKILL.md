---
name: capture-screenshot
description: Reusable logic to capture and VIEW app/web screenshots without exhausting the API many-image budget that, once tripped, blocks viewing every further image in a run. Capture small (Appium maxWidth / Playwright snapshot), always save full-res evidence to a file, downscale before any Read via scripts/downscale_image.py (cross-platform Pillow/sips/ImageMagick/ffmpeg), view sparingly, and when the cap is hit finish the run blind via page source / accessibility-id. Used by exploratory-method (capture evidence), find-elements-android/-ios, navigate-app, design-conformance, crawl-method. Standard: rules/screenshot-evidence.md.
---

# Skill: capture-screenshot

Reusable capability: get the screenshot evidence + the views you need **without** running out of
the session image budget. Policy + the "why" live in [screenshot-evidence.md](../../rules/screenshot-evidence.md);
this skill is the concrete procedure callers run. It is **cross-platform** (the helper degrades to
whatever resize backend the user has) and platform-agnostic (app via Appium MCP, web via Playwright MCP).

> ⚠️ The budget is **cumulative per run**: every image you Read stays in context. Capture freely to
> files; **Read sparingly**. The first symptom is the API rejecting an image with
> *"image dimensions exceed max allowed size for many-image requests: 2000 pixels"* — after which
> you cannot view ANY new screenshot for the rest of the run.

## Procedure

1. **Capture for VIEWING — small from the start (longer side ≤ ~1300px, hard limit 2000):**
   - **App (Appium MCP)**: call `appium_screenshot` with **`maxWidth: 720`** (server-side resize,
     aspect ratio preserved — built "for reducing token usage when sending screenshots to LLMs").
     Drop to ~600 for the tightest budget. NEVER Read a raw full-resolution capture (a 1220×2712
     phone screencap is already over the cap).
   - **Web (Playwright MCP)**: for *reading* state prefer `browser_snapshot` (accessibility tree —
     text, costs no image budget). Only `browser_take_screenshot` when a picture is genuinely needed;
     keep the viewport modest (`browser_resize` ≈ 1280×800) so the PNG stays under the cap.

2. **Capture for EVIDENCE — always save full-res to a FILE** (so the report has proof even after the
   budget is gone). This costs **zero** image budget (nothing returns into context):
   - Android: `adb -s <serial> exec-out screencap -p > results/<feature>/screenshots/<BUG-ID>.png`
   - iOS: `xcrun simctl io <udid> screenshot results/<feature>/screenshots/<BUG-ID>.png`
   - Web: `browser_take_screenshot` with the **full relative path** as `filename`
     (`results/<feature>/screenshots/<BUG-ID>.png`) — a bare name lands in the MCP output dir / project root.
   - Name by **BUG-ID** (e.g. `02-APP01-published-tab-crash.png`); also save a few `..-ok.png` proofs.

3. **Before Reading any file-captured image, downscale it and Read the small copy:**
   - macOS/Linux: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/downscale_image.py <file.png> --json`
   - Windows: `python %CLAUDE_PLUGIN_ROOT%\scripts\downscale_image.py <file.png> --json`
   - It writes `<file>.small.png` (≤1300 longer side) using the first available backend
     (Pillow → sips → ImageMagick → ffmpeg) and prints `out`. **Read that `out` path, never the
     original.** Use `--max 1000` for an even smaller copy.
   - **No backend available?** The helper still reports the real `original` dimensions +
     `within_cap:false` (stdlib header parse). In that case **do NOT Read the image** — go straight
     to step 5 (blind), and tell the user to install a backend (`pip install Pillow` is the simplest,
     any OS). `/qa:doctor` flags this.

4. **View sparingly.** Don't Read a screenshot at every step. Read one when you must *judge a visual*
   (layout/wrong figure/crash). For "which screen am I on / did the value change", use page source or
   the accessibility tree (step 5) instead — it is cheaper and does not spend the budget.

5. **When the cap is hit (or no resize backend), drive BLIND — stop retrying Reads:**
   - App: read state via `appium_get_page_source`, or `appium_find_element` by **accessibility-id =
     the on-screen label** (e.g. a Vietnamese string) — it returns element **text/UUID**, not an image.
     Web: `browser_snapshot`.
   - **Verify a screen by querying for the labels you expect**, not by looking.
   - Keep capturing full-res to files (step 2) so the bug report still has evidence.
   - **Do not trust `uiautomator dump` / a stale semantic tree as current-screen truth on Flutter** —
     it can show a previous screen's nodes; a fresh page source (or a downscaled screenshot, if you
     still have budget) is the source of truth.

## One-line summary
`maxWidth`≈720 for app views · full-res to files for evidence · **downscale before any Read** · view
sparingly · the moment the many-image error appears, finish **blind via page source / accessibility-id**.
