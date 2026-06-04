---
description: Authenticate Lark (Feishu) in BOTH token modes and verify permissions — tenant (app token from LARK_APP_ID/LARK_APP_SECRET) and/or user (UAT via OAuth login). Probes what each mode can do (Bitable / Drive / Docs), resolves the effective read mode (preference auto|tenant|user; auto picks the mode with more granted read scopes, tie→tenant), writes structured lark info to lark-auth.state.json + env, and reports any conflict with what a command needs. You (Claude) run scripts/lark_auth.py yourself; the user runs no terminal command.
argument-hint: [--command plan-tests|exploratory|log-bug|update-board] [--mode auto|tenant|user] [--login [--code <CODE>]] [--request full|<caps>] [--json]
allowed-tools: Bash, Read, Edit
---

# /qa:auth-lark — Lark dual-mode authentication + permission check

Authenticate the project's Lark access and check it has the permissions the QA commands need. **Two token modes, both optional & combinable:** *tenant* (app token — the doc must be shared with the app; default, zero extra setup) and *user* (UAT — the doc must be visible to you; needs a one-time OAuth login). **Run the script YOURSELF via Bash — do NOT print a command for the user to run.** The script NEVER prints the secret, token, or refresh token.

## Step 1 — Run the auth script (auto-detect Python)
Pass `$ARGUMENTS` straight through (default = no args = probe every configured mode + request FULL capability). One Bash call:

```bash
PY="$(command -v python3 || command -v python)"
"$PY" "${CLAUDE_PLUGIN_ROOT}/scripts/lark_auth.py" $ARGUMENTS
```

What it does:
1. **Authenticate each configured mode** — tenant: `LARK_APP_ID`+`LARK_APP_SECRET`→`tenant_access_token`; user: refresh the stored `LARK_USER_REFRESH_TOKEN`→`user_access_token` (rotated refresh token re-persisted).
2. **Probe capabilities per mode** — what each token can actually do (read Drive, read the active Bitable board from `log-bug.config.yml`, …).
3. **Resolve the read mode** — by preference `LARK_TOKEN_MODE` (`auto` picks whichever mode has MORE granted read caps, tie→tenant; or an explicit `tenant`/`user`). Writes structured lark info → `lark-auth.state.json` (per-mode caps + `read_mode`) + `LARK_READ_MODE` / `LARK_APP_CAPABILITIES` / `LARK_USER_CAPABILITIES` lines in `.plugin.env`, so commands/skills (and `lark_read.py`) know which token to use.
4. **Check vs command** — with `--command <name>`, compares the BEST capability across modes against that command's needs.

## Step 1b — Enable user (UAT) mode (only if the user wants it)
If docs are shared with people (not the app), or the user asks for user-token mode:
1. Run `lark_auth.py --login` → it prints a **consent URL** + the `redirect_uri` (must match the app console's Redirect URL). Give the URL to the user.
2. The user opens it, approves, and copies the `code` from the redirected URL.
3. Run `lark_auth.py --login --code <CODE>` → stores `LARK_USER_REFRESH_TOKEN`.
4. Re-run `/qa:auth-lark` to probe user-mode caps and resolve `read_mode`.

Set the default mode with `--mode auto|tenant|user` (persisted). `auto` (recommended) auto-selects the stronger mode and `lark_read.py` still **falls back** to the other mode for any doc the chosen one is denied.

## Step 2 — Interpret the exit code & report
- **exit 0** → authenticated; print the per-mode capability table + the resolved `read_mode`. If `--command` was given and all required caps are available, say it's ready.
- **exit 2** → no/invalid credentials in ANY mode. Tell the user to open **`.claude/qa-claude/.plugin.env`**, set `ENABLE_LARK_APP=true` + `LARK_APP_ID`/`LARK_APP_SECRET` (tenant), and/or run `/qa:auth-lark --login` (user), then re-run.
- **exit 3** → permission conflict: missing a scope in ALL modes. Relay each missing capability + the **exact scope to grant** — tenant: Developer Console → Permissions & Scopes → re-publish; user: add to `LARK_USER_SCOPE` → re-login. Then re-run.

## Capabilities & how they map to commands
- `bitable.read` (`bitable:app:readonly`) · `bitable.write` (`bitable:app`) → **/qa:log-bug**, **/qa:update-board**
- `drive.read` (`drive:drive:readonly`) · `drive.upload` (`drive:drive`) → log-bug attachment + doc readers
- `docx.read` (`docx:document:readonly`) · `wiki.read` (`wiki:wiki:readonly`) → **/qa:plan-tests**, **/qa:exploratory**, **/qa:analyze-spec** Lark doc reading

Status legend the script prints: ✅granted ❌denied 📜declared (write/upload — can't be probed non-destructively, trusted from the scope grant) ❔unknown ➖skipped (no resource to probe, e.g. board id not filled yet).

## Principles
- **Default = request FULL** — verify every capability unless `--request` narrows it.
- **Default mode = auto** — both modes are first-class; the project's tenant flow wins ties. Never force user mode unless asked or tenant can't read the docs.
- Run BEFORE relying on `/qa:log-bug` or Lark doc reads so a missing scope surfaces here, not mid-task.
- Secrets (incl. the user refresh token) stay in `.claude/qa-claude/.plugin.env` (git-ignored). NEVER print them. Logic lives in `scripts/lark_auth.py`; this command just drives it.
