---
name: setup
description: Standard setup for a project using the qa plugin — scaffold ./.env from the template, patch .gitignore, and run doctor (auto-installs wrangler). Cross-platform (Windows/macOS/Linux). Use when first adding the plugin to a project, or when you want to enable Lark notify / push reports to R2.
---

# Skill: setup

Prepare a project to use this plugin's optional integrations (Lark notifier + R2 report push). The logic lives entirely in `scripts/setup.py` (cross-platform, stdlib-only) — this skill just runs it and interprets the result.

## Procedure
1. **Run setup** (pick the python command per OS):
   - macOS/Linux: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/setup.py`
   - Windows: `python ${CLAUDE_PLUGIN_ROOT}/scripts/setup.py`

   The script will:
   - create `./.env` from `${CLAUDE_PLUGIN_ROOT}/templates/.env.example` (does NOT overwrite if it already exists);
   - add `.env`, `.qa-venv/`, `reports/upload-logs/` to the project's `.gitignore`;
   - run **doctor** and **auto-install `wrangler`** if the machine has `npm` (`--no-fix` to only report, not install).

2. **Read the doctor output**: if a required tool is still missing (python/node/java/mvn), the script prints the **correct install command per OS** — hand it to the user to run, then re-run. Do NOT auto-install system toolchains for the user.

3. **Prompt the user to fill `.env`**: open `./.env`, fill `LARK_WEBHOOK_URL`/`LARK_WEBHOOK_SECRET` (if enabling `ENABLE_LARK_NOTIFY=true`) and `CF_ACCOUNT_ID`/`CF_API_TOKEN`/`CF_R2_BUCKET` (if enabling `ENABLE_CF_PUSH=true`). Both flags default to `false` → nothing is enabled until the user fills them in and flips the flag.

## Principles
- **Secrets live in the project** (`./.env`, git-ignored) — NEVER write secrets into the plugin.
- Idempotent: safe to re-run (does not overwrite `.env`, does not duplicate `.gitignore` lines).
- After setup, `/run` will auto-push the report + send Lark if the two flags are enabled (see skills `run-app`/`run-web`).
