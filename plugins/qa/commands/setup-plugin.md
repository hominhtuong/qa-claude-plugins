---
description: One-click setup of the qa plugin in THIS project — you (Claude) auto-detect the OS and run scripts/setup.py yourself; it creates .claude/qa-claude/ (config + .plugin.env), patches .gitignore, and checks the toolchain. The user does NOT run any terminal command.
argument-hint: [--update (refresh templates) | --no-fix (don't auto-install wrangler)]
allowed-tools: Bash, Read, Edit, Write, Glob, Grep
---

# /qa:setup-plugin — One-click project setup

Set this project up to use the plugin. **Run the script YOURSELF via Bash — do NOT print a command and ask the user to run it.** This is the friendly entry point for non-technical users: they type `/qa:setup-plugin`, you do the rest.

## Step 1 — Run the setup script (auto-detect Python)
Use the available Python interpreter (cross-platform: macOS/Linux usually `python3`, Windows usually `python`). Run in ONE Bash call, passing through `$ARGUMENTS` (e.g. `--update`, `--no-fix`):

```bash
PY="$(command -v python3 || command -v python)"
"$PY" "${CLAUDE_PLUGIN_ROOT}/scripts/setup.py" $ARGUMENTS
```

- If that fails because no Python is found → tell the user to install **Python 3.9+** and give the OS-specific command (macOS `brew install python` · Windows `winget install Python.Python.3` · Linux `sudo apt install python3`), then stop.
- If `${CLAUDE_PLUGIN_ROOT}` doesn't expand in the shell, resolve the plugin path from this command file's location and call `<plugin>/scripts/setup.py`.

## Step 2 — Interpret the output (per skill `setup`)
The script installs into `.claude/qa-claude/`: `.plugin.env` + `log-bug.config.yml` (yours, never overwritten) and `.plugin.env.example` / `log-bug.config.example.yml` / `testcase-template.md` (refreshed), patches `.gitignore`, and runs the toolchain **doctor**. A pre-0.0.5 `.env` is auto-migrated to `.plugin.env` (your secrets are kept).

- If the doctor reports a missing required tool (node/java/mvn/wrangler), relay the **exact install command it printed** for this OS. Don't auto-install system toolchains.

## Step 3 — Tell the user what to do next (plain language)
- To turn on notifications / report sharing: open **`.claude/qa-claude/.plugin.env`**, flip the `ENABLE_*` flag you want and fill that section (Lark / Slack / R2 / S3). All optional — skip to use nothing.
- To use `/qa:log-bug`: open **`.claude/qa-claude/.plugin.env`** and fill the **LARK APP** section (`LARK_APP_ID` / `LARK_APP_SECRET`), then run **`/qa:auth-lark`** to authenticate + verify the app id has the permissions `/qa:log-bug` needs. Fill the board id + dev mapping in **`.claude/qa-claude/log-bug.config.yml`** (or `/qa:update-board <board-url>`).
- Both files are yours and survive future `setup` runs.

## Principles
- The user never touches a terminal — you run the script and summarize.
- Re-running is safe (idempotent): your `.plugin.env`/`log-bug.config.yml` are never overwritten; only the `.example`/template references refresh.
- Logic lives in `scripts/setup.py` + skill `setup`; this command just drives it.
