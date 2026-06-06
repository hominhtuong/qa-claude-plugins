---
name: setup
description: Standard setup for a project using the qa plugin — install all plugin config into <project>/.claude/qa-claude/ (separate from the project's own ./.env): scaffold .plugin.env (secrets) + log-bug.config.yml (board/mappings) without overwriting, refresh the .example references + testcase-template.md, patch .gitignore, run doctor (auto-installs wrangler). Cross-platform (Windows/macOS/Linux). Use when first adding the plugin to a project, or after updating the plugin.
---

# Skill: setup

Prepare a project to use this plugin's config + optional integrations. All plugin config lives in **`<project>/.claude/qa-claude/`** — kept SEPARATE from the project's own `./.env`. The logic is in `scripts/setup.py` (cross-platform, stdlib-only) — this skill runs it and interprets the result.

## Procedure
1. **Run setup** (pick the python command per OS):
   - macOS/Linux: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/setup.py`
   - Windows: `python ${CLAUDE_PLUGIN_ROOT}/scripts/setup.py`

   It installs into `.claude/qa-claude/`:

   | File | Policy |
   |---|---|
   | `.plugin.env` | 🔒 secrets (ONE sectioned file) — **SCAFFOLD** (created if missing, never overwritten) |
   | `log-bug.config.yml` | 🧩 board ids + dev-pic/field mappings — **SCAFFOLD** (your copy, never overwritten) |
   | `.plugin.env.example` · `log-bug.config.example.yml` | references — **OVERWRITE** (refreshed each run / on update) |
   | `testcase-template.md` | 📄 test-case format (plugin-owned) — **OVERWRITE** |
   | `README.md` | 📖 usage guide — full command list, auto-generated from the live commands — **OVERWRITE** |

   Then it adds `.claude/qa-claude/.plugin.env`, `.qa-venv/`, `results/tests/.upload-logs/` to `.gitignore`, and runs **doctor** (`--no-fix` to skip auto-installing `wrangler`).

2. **Read the doctor output**: a required tool still missing (python/node/java/mvn) → the script prints the **correct install command per OS**; hand it to the user, then re-run. Do NOT auto-install system toolchains.

3. **Prompt the user to fill their files** (both git-ignored / theirs, never overwritten):
   - `.claude/qa-claude/.plugin.env` — Lark/R2/S3/notify secrets (only the channel they enable via `ENABLE_*`), plus behavior toggles: `HEADLESS` (web driver) and **`LANGUAGE`** (output language for reports/test cases/deliverables — default `Vietnamese`, set `English` for English output; see `rules/output-language.md`).
     - **Lark app**: to read docs / use Bitable, set `ENABLE_LARK_APP=true` AND real `LARK_APP_ID`/`LARK_APP_SECRET` (the `cli_xxx`/`your_app_secret` placeholders are rejected with a clear message), then run `/qa:auth-lark` — it now **tests read scopes for real** (a missing `wiki:wiki`/`docx:document:readonly` shows up immediately).
     - **Behind a corporate proxy?** If Lark calls fail with `CERTIFICATE_VERIFY_FAILED`, set `SSL_CERT_FILE` to a CA bundle (the error prints the exact command) or `pip install truststore`. `/qa:doctor` flags this too.
   - `.claude/qa-claude/log-bug.config.yml` — Lark bug board ids + `dev_pic` open_ids + defaults (for `/qa:log-bug`).

## Principles
- **Secrets + user config live in `.claude/qa-claude/`** (`.plugin.env` git-ignored) — NEVER in the plugin, NEVER in the project's root `./.env`.
- **SCAFFOLD vs OVERWRITE**: your `.plugin.env` and `log-bug.config.yml` are never clobbered; the `.example` references + `testcase-template.md` are refreshed so a plugin update brings the latest schema/format (diff the `.example` against your file after updating). A pre-0.0.5 `.env` is auto-migrated to `.plugin.env` on the next run (secrets preserved).
- Idempotent: safe to re-run; does not duplicate `.gitignore` lines.
- After setup, `/qa:run` auto-pushes the report + sends Lark if the flags are enabled (see skills `run-app`/`run-web`); `/qa:log-bug` reads the board config.
