# Screenshot & image-evidence rule (avoid the many-image cap)

Long, screenshot-heavy runs (especially `/qa:exploratory`, `/qa:sitemap`, design-conformance)
hit an **API image budget** that, once tripped, blocks viewing **every** further screenshot for
the rest of the session. This rule keeps that budget from running out. It is **platform-agnostic
policy**; the reusable procedure is the [capture-screenshot](../skills/capture-screenshot/SKILL.md) skill.

## The failure (know it so you avoid it)
- **Per-image dimension cap**: the API rejects any image whose **longer side > ~2000px** —
  `"At least one of the image dimensions exceed max allowed size for many-image requests: 2000 pixels"`.
  A phone screencap is commonly **1220×2712** (height > 2000), so a **raw** screenshot already fails.
- **Cumulative count**: it is *also* a per-session/turn many-image budget — every image you Read
  stays in context. Downscaling each one stretches the budget but does not make it infinite, so a
  run that Reads a screenshot at every step **will** eventually trip it. Capture freely to files;
  **View sparingly.**

## Rules (do these from the START of a run, not after it breaks)

1. **Capture SMALL — cap the longer side ≤ ~1300px (hard limit 2000).**
   - **App (Appium MCP)**: ALWAYS pass `maxWidth` to `appium_screenshot` — it resizes server-side,
     preserves aspect ratio, and is explicitly "for reducing token usage when sending screenshots
     to LLMs". Use **`maxWidth: 720`** (a 2.22∶1 portrait → ~720×1600, safely < 2000 in both
     orientations; drop to ~600 for the tightest budget). Never Read a raw, full-resolution capture.
   - **Web (Playwright MCP)**: prefer `browser_snapshot` (the accessibility tree — text, no image
     budget) for *reading* state; only `browser_take_screenshot` when a picture is truly needed, and
     keep the viewport modest (`browser_resize` ~ 1280×800) so the PNG stays under the cap.

2. **Always also capture full evidence to a FILE** (so the report has proof even after the budget is
   gone, and regardless of whether you can still *view*):
   - Android: `adb -s <serial> exec-out screencap -p > results/<feature>/screenshots/<BUG-ID>.png`
     (writes a file, returns nothing into context — costs **zero** image budget).
   - iOS: `xcrun simctl io <udid> screenshot results/<feature>/screenshots/<BUG-ID>.png`.
   - Web: `browser_take_screenshot` with the **full relative path** as `filename`
     (`results/<feature>/screenshots/<BUG-ID>.png`) — a bare name lands in the MCP output dir.
   - Name by **BUG-ID** (`02-APP01-...png`); also a few `..-ok.png` proofs of "checked".

3. **Before you Read a file-captured screenshot, downscale it.** Run the cross-platform helper and
   Read the small copy, never the original:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/downscale_image.py" <file.png> --json
   # → writes <file>.small.png (≤1300 long side) using Pillow / sips / ImageMagick / ffmpeg.
   #   If NO backend exists it reports the real dimensions + within_cap:false — then do NOT Read it.
   ```
   `--probe-only` just measures (stdlib header parse) without resizing — use it to decide if a Read
   is even safe.

4. **When the cap is hit, switch to driving BLIND — do not keep retrying Reads.** Once you see the
   "image dimensions exceed max allowed size for many-image requests" error, viewing is done for the
   run. Continue the exploration without images:
   - Read state from **page source / accessibility tree**, not pictures: app → `appium_get_page_source`
     or `appium_find_element` (accessibility-id = the on-screen label, e.g. a Vietnamese string) which
     returns element **text/UUID**, not an image; web → `browser_snapshot`.
   - **Verify a screen by querying for the labels you expect to be there** instead of looking.
   - Keep capturing full-res to files (rule 2) so the bug report still has evidence.

5. **Never trust `uiautomator dump` (or a stale semantic tree) as current-screen truth on Flutter
   apps** — it can report a previous screen's nodes while you are really on another. Use a fresh
   `appium_get_page_source` / a (downscaled) screenshot as the source of truth; treat the dump only
   as a hint.

## One-line summary
Capture small (`maxWidth`≈720 / file-capture), keep full evidence on disk, **downscale before any
Read**, view sparingly, and the moment the many-image error appears, finish the run **blind via page
source / accessibility-id** — full-res screenshots still saved to files for the report.
