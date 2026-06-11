---
description: Authenticate Lark (Feishu) in BOTH token modes and verify permissions — tenant (app token from LARK_APP_ID/LARK_APP_SECRET) and/or user (UAT via OAuth login). Probes what each mode can do (Bitable / Drive / Docs), resolves the effective read mode (preference user(default)|auto|tenant; user prefers the real-person token so writes are traceable, auto picks the mode with more granted read scopes tie→tenant), writes structured lark info to lark-auth.state.json + env, and reports any conflict with what a command needs. You (Claude) run scripts/lark_auth.py yourself; the user runs no terminal command.
argument-hint: [--command plan-tests|exploratory|analyze-spec|log-bug|update-board] [--mode auto|tenant|user] [--login [--code <CODE>]] [--probe-doc <url>] [--request full|<caps>] [--json]
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

## Step 1b — Enable user (UAT) mode (DEFAULT — set this up early)
User mode is the **project default** (`LARK_TOKEN_MODE=user`): reads prefer the real person and **every CREATE/UPDATE is attributable to a human (audit trail)** — `/qa:log-bug` and `/qa:update-board` writes always use the user token, never the app/bot token. Set it up once:
1. Run `lark_auth.py --login` → it prints a **consent URL** (asking for FULL read+write scopes in one go) + the `redirect_uri`. The default redirect is `http://localhost:3000/callback` (port **3000** — what most Lark apps register). If the app console registered a different URL/port, set `LARK_REDIRECT_URI` first or pass `--redirect-uri`, else Lark returns error 20029. Give the URL to the user.
2. The user opens it, approves, and copies the `code` from the redirected URL.
3. Run `lark_auth.py --login --code <CODE>` → stores `LARK_USER_REFRESH_TOKEN` + the working redirect.
4. Re-run `/qa:auth-lark` to probe user-mode caps and resolve `read_mode`.

Change the preference with `--mode user|auto|tenant` (persisted). `user` (default) keeps writes traceable; `lark_read.py` still **falls back** to tenant for any doc the user token is denied. Only switch to `tenant`/`auto` if you deliberately want app-token writes (loses the who-did-it audit trail).

## Step 2 — Interpret the exit code & report
- **exit 0** → authenticated; print the per-mode capability table + the resolved `read_mode`. If `--command` was given and all required caps are available, say it's ready.
- **exit 2** → no/invalid credentials, OR a transport failure (SSL/network). The JSON/human output carries a stable **`error_code`** + a one-line **`action`** — relay that verbatim (see the table below). Common: `CREDS_PLACEHOLDER` (still `cli_xxx`/`your_app_secret`), `APP_DISABLED` (`ENABLE_LARK_APP=false`), `SSL_CERT` (corporate self-signed proxy — the output already prints the exact `SSL_CERT_FILE` fix), `REDIRECT_MISMATCH` (20029).
- **exit 3** → permission conflict: a required read scope is **denied** in ALL modes (now actually tested, not assumed). Relay each missing capability + the **exact scope to grant** — tenant: Developer Console → Permissions & Scopes → re-publish; user: add to `LARK_USER_SCOPE` → re-login. Then re-run.

### Error codes → single next action (relay these, don't re-derive)
| `error_code` | Meaning | One-step fix to relay |
|---|---|---|
| `CREDS_PLACEHOLDER` | App id/secret still the template placeholder | Fill real `LARK_APP_ID`/`LARK_APP_SECRET` + `ENABLE_LARK_APP=true` (Developer Console → Credentials) |
| `APP_DISABLED` | Creds look real but `ENABLE_LARK_APP=false` | Set `ENABLE_LARK_APP=true` |
| `SSL_CERT` | TLS trust failure (corporate self-signed CA) | Set `SSL_CERT_FILE` to a CA bundle (output prints the command) or `pip install truststore` |
| `REDIRECT_MISMATCH` | OAuth 20029 — redirect not registered | Set `LARK_REDIRECT_URI` to a URL registered in the app console |
| `INVALID_PARAM` | Lark 10003 (usually bad creds) | Re-check `LARK_APP_ID`/`LARK_APP_SECRET` |
| `SCOPE_DENIED` | Token lacks a required scope | Grant the scope (console → publish) or add to `LARK_USER_SCOPE` + re-login |
| `DOC_DENIED` | Doc not shared with app/user | Share the doc, or `--login` to use the user token |

### Verifying read scopes against a real doc (recommended)
Read scopes (`wiki.read`/`docx.read`/`drive.read`) are now **probed for real** — a missing scope shows as `❌ denied` immediately, never an optimistic "declared". To test against the exact document the user needs (cleanest signal), pass `--probe-doc <wiki_or_docx_url>` (or set `LARK_PROBE_DOC` in `.plugin.env`). Without it, a throwaway token still surfaces a missing scope.

## Capabilities & how they map to commands
- `bitable.read` (`bitable:app:readonly`) · `bitable.write` (`bitable:app`) → **/qa:log-bug**, **/qa:update-board**
- `drive.read` (`drive:drive:readonly`) · `drive.upload` (`drive:drive`) → log-bug attachment + doc readers
- `docx.read` (`docx:document:readonly`) · `wiki.read` (`wiki:wiki:readonly`) → **/qa:plan-tests**, **/qa:exploratory**, **/qa:analyze-spec** Lark doc reading

Status legend the script prints: ✅granted (read scopes are **actually tested** with a harmless GET) ❌denied 📜declared (only `bitable.write`/`drive.upload` — a write can't be probed non-destructively) ❔unknown ➖skipped (no resource to probe, e.g. board id not filled yet).

## Principles
- **Default = request FULL** — both modes ask for the maximum read **and write** scopes in one consent (`bitable:app`, `drive:drive`, `docx:document`, `wiki:wiki` + their readonly forms) so you never re-grant piecemeal. Lark grants whatever the app actually has enabled. Narrow only with `--request`.
- **Default mode = user** — reads prefer the real person and **writes/updates are MANDATORY user** (the app token would log records as the bot, losing the who-did-it audit trail). `lark_read.py` still falls back to tenant for any doc the user can't see. Switch to `tenant`/`auto` only if you deliberately accept app-token writes.
- **Default OAuth redirect = port 3000** (`http://localhost:3000/callback`) — the port most Lark apps register. Override via `LARK_REDIRECT_URI` if the app console differs.
- Run BEFORE relying on `/qa:log-bug` or Lark doc reads so a missing scope surfaces here, not mid-task. If user mode isn't set up yet, do Step 1b first — writes refuse to fall back to the app token.
- Secrets (incl. the user refresh token) stay in `.claude/qa-claude/.plugin.env` (git-ignored). NEVER print them. Logic lives in `scripts/lark_auth.py`; this command just drives it.
