---
description: Install-helper for the local UI-vision engine used by /qa:exploratory-ui — creates a dedicated Python venv under .claude/qa-claude/ui-engine/ and installs the CV stack (opencv-python-headless + scikit-image + Pillow + imagehash + numpy), then writes the engine config (interpreter path + comparison thresholds). One-time, cross-platform (macOS/Windows/Linux), idempotent; --force recreates the venv. You (Claude) run scripts/ui_engine.py yourself — the user runs no terminal command.
argument-hint: [--force] [--check]
allowed-tools: Read, Bash
---

# /qa:ui-engine-install — set up the local screenshot-vs-design engine

Install (or repair) the **local CV engine** that powers /qa:exploratory-ui's screenshot↔Figma color
comparison. The engine is an isolated Python venv so it never clashes with the system Python or the
project's own dependencies. Everything heavy runs locally; the AI later reads only small JSON
verdicts. **You run the script — the user does not touch a terminal.**

> What gets installed (≈100–200MB of prebuilt wheels, ~30–60s):
> `numpy · opencv-python-headless · scikit-image · Pillow · imagehash` (core CV) +
> `rapidocr-onnxruntime · pytesseract` (OCR for the text-vs-design layer — best-effort).
> Location: `<project>/.claude/qa-claude/ui-engine/venv/` · Config: `<project>/.claude/qa-claude/ui-engine.config.json`

> **OCR for text comparison (so it can catch a changed label like Products→Product):** the engine
> auto-uses the best available backend. `rapidocr-onnxruntime` (pip, self-contained) installs with the
> engine so text comparison works out of the box. For the **best Vietnamese (with diacritics)**, also
> install the **Tesseract** binary + the `vie` language pack — the engine prefers it automatically:
> - **macOS:** `brew install tesseract tesseract-lang`
> - **Windows:** `winget install UB-Mannheim.TesseractOCR` (pick Vietnamese during install, or add `vie.traineddata`)
> - **Linux:** `sudo apt install tesseract-ocr tesseract-ocr-vie`
> Tesseract is OPTIONAL — without it, rapidocr handles text (Vietnamese diacritics a bit weaker).

## Step 0 — Resolve intent
- `--check` (or no args and you just want status) → only report state, do not install.
- `--force` → recreate the venv from scratch (use when it's corrupt or deps won't import).

## Step 1 — Check current state first
Run:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ui_engine.py check --json
```
- `READY` → already installed. Print the engine versions + config path and stop (unless `--force`).
- `NEEDS-SETUP` → CV stack present, only the config is missing → the install below just rewrites it
  (no download).
- `NEEDS-DEPS` / `NOT-INSTALLED` → proceed to install.

## Step 2 — Install / repair
Run (add `--force` if requested):
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ui_engine.py install --json
```
This creates the venv (with the same Python that runs the script), pip-installs the CV stack,
import-probes every module, and writes `ui-engine.config.json` (interpreter path + default
thresholds — preserving any thresholds the user already tuned).

**If it fails:**
- `INSTALL-FAILED` with a TLS / `CERTIFICATE_VERIFY_FAILED` message → corporate proxy. Run
  `/qa:doctor --fix` (installs `truststore`) then retry, or follow the printed SSL_CERT_FILE hint.
- `venv` creation failed on Linux → `sudo apt install python3-venv`, then retry.
- pip offline / index blocked → retry when online; the wheels come from PyPI.

## Step 3 — Confirm
Re-run `ui_engine.py check --json` → expect `READY`. Report to the user (configured output language,
default Vietnamese): engine state, OpenCV + scikit-image versions, config path, and that
**/qa:exploratory-ui** can now run. Note the thresholds live in `ui-engine.config.json` and can be
tuned (color Delta-E / SSIM / hash) without reinstalling.

## Output
A `READY` local CV engine + its config. No secrets printed. Idempotent — safe to re-run; it reuses
the existing venv and only repairs what's missing (`--force` to rebuild).
