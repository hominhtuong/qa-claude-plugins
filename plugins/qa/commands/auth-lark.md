---
description: Authenticate a Lark (Feishu) custom app and verify its permissions — reads LARK_APP_ID/LARK_APP_SECRET from .claude/qa-claude/.plugin.env, exchanges them for a tenant access token, probes what the app id can do (Bitable / Drive / Docs), and reports any conflict with what a command needs. Default requests FULL capability. You (Claude) run scripts/lark_auth.py yourself; the user runs no terminal command.
argument-hint: [--command log-bug|update-board|plan-tests] [--request full|<caps>] [--json]
allowed-tools: Bash, Read, Edit
---

# /qa:auth-lark — Lark app authentication + permission check

Authenticate the project's Lark custom app and check the app id has the permissions the QA commands need. **Run the script YOURSELF via Bash — do NOT print a command for the user to run.** The script NEVER prints the secret or the token.

## Step 1 — Run the auth script (auto-detect Python)
Pass `$ARGUMENTS` straight through (default = no args = request FULL capability). One Bash call:

```bash
PY="$(command -v python3 || command -v python)"
"$PY" "${CLAUDE_PLUGIN_ROOT}/scripts/lark_auth.py" $ARGUMENTS
```

What it does (the QAButler / F2KB flow):
1. **Authenticate** — `LARK_APP_ID` + `LARK_APP_SECRET` (+ `LARK_DOMAIN`) → `tenant_access_token` (validates the credentials), cached to `.claude/qa-claude/lark-auth.state.json`.
2. **Refresh capabilities** — probes what the app id can actually do (read Drive, read the active Bitable board from `log-bug.config.yml`, …) and writes the resolved set back to the state file + a `LARK_APP_CAPABILITIES=` line in `.plugin.env`.
3. **Check vs command** — with `--command <name>`, compares the app's capabilities against that command's requirements and reports conflicts.

## Step 2 — Interpret the exit code & report
- **exit 0** → authenticated; print the capability table. If `--command` was given and all required caps are available, say it's ready.
- **exit 2** → missing/invalid credentials. Tell the user to open **`.claude/qa-claude/.plugin.env`**, set `ENABLE_LARK_APP=true` and fill `LARK_APP_ID` / `LARK_APP_SECRET` (Lark Developer Console → Credentials & Basic Info), then re-run `/qa:auth-lark`.
- **exit 3** → permission conflict: the app id is missing a scope a command needs. Relay each missing capability + the **exact scope to grant** (the script prints it), tell the user to add it in the Developer Console → Permissions & Scopes, **re-publish the app version**, then re-run `/qa:auth-lark`.

## Capabilities & how they map to commands
- `bitable.read` (`bitable:app:readonly`) · `bitable.write` (`bitable:app`) → **/qa:log-bug**, **/qa:update-board**
- `drive.read` (`drive:drive:readonly`) · `drive.upload` (`drive:drive`) → log-bug attachment + doc readers
- `docx.read` (`docx:document:readonly`) · `wiki.read` (`wiki:wiki:readonly`) → **/qa:plan-tests** Lark doc reading

Status legend the script prints: ✅granted ❌denied 📜declared (write/upload — can't be probed non-destructively, trusted from the scope grant) ❔unknown ➖skipped (no resource to probe, e.g. board id not filled yet).

## Principles
- **Default = request FULL** — verify every capability unless `--request` narrows it.
- Run BEFORE relying on `/qa:log-bug` so a missing scope surfaces here, not mid-bug-logging.
- Secrets stay in `.claude/qa-claude/.plugin.env` (git-ignored). NEVER print the secret/token. Logic lives in `scripts/lark_auth.py`; this command just drives it.
