---
name: ui-engine-check
description: Reusable logic to resolve the state of the local UI-vision CV engine (the opencv + scikit-image venv that powers /qa:exploratory-ui's screenshot-vs-Figma comparison) — is it READY (link the config), present-but-NEEDS-SETUP/NEEDS-DEPS (repair), or NOT-INSTALLED (suggest /qa:ui-engine-install)? Runs scripts/ui_engine.py check, never installs on its own without consent. The gate every exploratory-ui run passes before it can compare. Cross-platform (macOS/Windows/Linux).
---

# Skill: ui-engine-check

Reusable capability: before /qa:exploratory-ui can diff an app screenshot against its Figma design,
the **local CV engine** must exist. That engine is a dedicated Python venv
(`.claude/qa-claude/ui-engine/venv/`) holding `opencv-python-headless + scikit-image + Pillow +
imagehash + numpy`, plus a config (`.claude/qa-claude/ui-engine.config.json`) recording the
interpreter path + comparison thresholds. This skill **resolves the engine state** and tells the
caller exactly what to do next — it does NOT install anything without the user's consent.

> Why a separate engine: the heavy image math runs LOCALLY (color Delta-E, SSIM, hashes) so only a
> tiny JSON verdict reaches the AI — saving tokens. The venv keeps that CV stack off the system
> Python and off the project's own deps. See [ui-visual-compare.md](../../rules/ui-visual-compare.md).

## Procedure

1. **Probe the engine** (read-only, fast):
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ui_engine.py check --json
   ```
   The JSON has a `state` field — branch on it:

   | `state` | Meaning | What this skill returns to the caller |
   |---|---|---|
   | `READY` | venv + all CV packages + config present | **Use it.** Return `venv_python` + `config_path` (the thresholds source). No action needed. |
   | `NEEDS-SETUP` | CV stack present but config missing | Self-heal: run `ui_engine.py install` (it only (re)writes the config — no re-download). Re-check → READY. |
   | `NEEDS-DEPS` | venv exists but a package is missing/broken | Tell the caller it needs repair → route to **install-helper** `/qa:ui-engine-install` (repairs in place). |
   | `NOT-INSTALLED` | no venv yet | **STOP and ASK.** The engine is required to compare. Suggest the user run **install-helper** `/qa:ui-engine-install` (one-time, ~30–60s, downloads ~100–200MB of prebuilt wheels). Only on the user's "yes" does the install run. |

2. **READY path** — load the config and hand it to `ui-visual-compare`:
   - `venv_python`: the interpreter that must run `ui_compare.py`.
   - `config_path`: pass as `--thresholds` so the user's tuned thresholds (if any) apply.
   - Confirm to the user in one line: *"UI engine sẵn sàng (opencv {ver}, scikit-image {ver})"* (configured language).

3. **NOT-INSTALLED path** — **never auto-install silently**. Present the choice:
   - Explain: the local model/engine is not installed yet; without it the screenshot-vs-design
     color check can't run. Installing creates an isolated venv and downloads the CV stack once.
   - If the user agrees → invoke the install-helper (the `/qa:ui-engine-install` command, or run
     `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ui_engine.py install --json` directly), then re-run
     step 1 to confirm `READY`.
   - If the user declines → the exploratory-ui run cannot do the visual comparison; offer to
     continue with a **non-CV** path (the AI eyeballs the Figma screenshot vs the app screenshot
     directly — higher token cost, less precise) or stop.

4. **NEEDS-DEPS / repair** — route to the install-helper with the user's consent; it reuses the
   existing venv and reinstalls only what's missing (`ui_engine.py install` is idempotent;
   `--force` recreates from scratch if the venv is corrupt).

## Output

Return to the caller a small status object: `{ state, venv_python, config_path, thresholds, hint }`.
On READY this is everything `ui-visual-compare` needs. On any non-READY state, the caller must
resolve it (install/repair with consent) before comparing — do NOT fabricate comparison results
without a working engine.

## Notes
- Cross-platform: the script resolves `venv/bin/python` (macOS/Linux) vs `venv\Scripts\python.exe`
  (Windows) for you — never hardcode the interpreter path; always read `venv_python` from the JSON.
- The engine lives under the PROJECT (`$CLAUDE_PROJECT_DIR/.claude/qa-claude/`), so each project has
  its own copy and its own tunable thresholds; it is git-ignored along with the rest of `qa-claude/`.
- This skill is read-only by default. The only state change it may trigger is an install/repair, and
  only after the user agrees (or, for `NEEDS-SETUP`, the no-download config rewrite).
