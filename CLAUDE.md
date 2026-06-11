# QAClaudePlugins — project rules

This repo ships the **qa** Claude Code plugin (`plugins/qa`). The rules below are authoritative
for any work that touches Lark (Feishu) — they hold both inside this repo and when the plugin is
imported into another main project.

## Lark login & authentication policy (MANDATORY)

Any operation that needs Lark login / auth (`/qa:auth-lark`, `/qa:log-bug`, `/qa:update-board`,
Lark doc readers, the bug-board reporting commands) MUST comply with all three rules:

1. **Request FULL capability in one consent.** Auth always asks for the maximum read **and**
   write scopes at once (`bitable:app`, `drive:drive`, `docx:document`, `wiki:wiki` + their
   `:readonly` forms, plus `offline_access`) so we never re-grant piecemeal. Lark grants
   whatever the app actually has enabled; extra scopes are ignored, not fatal. Source of truth:
   `DEFAULT_USER_SCOPE` in `plugins/qa/scripts/lark_auth.py`. Narrow only via `--request` /
   `LARK_USER_SCOPE`.

2. **Default OAuth redirect = port 3000** (`http://localhost:3000/callback`) — the port most
   Lark apps register, NOT 8080/8000. Source of truth: `DEFAULT_REDIRECT_URI` in `lark_auth.py`.
   Override per project with `LARK_REDIRECT_URI` only if the app console registered a different
   URL/port (a mismatch → Lark error 20029).

3. **Prefer user mode; writes/updates are MANDATORY user (`mode: user`).** The default token
   mode is `user` (`LARK_TOKEN_MODE=user`) so reads prefer the real person. Every CREATE/UPDATE
   on Lark (a `/qa:log-bug` record, a record update) MUST use the **user token**
   (`useUAT: true` on the MCP, or `get_write_token()` in Python) so the record is attributable —
   we can always trace WHO did it. NEVER write with the tenant/app token (it logs the change as
   the bot). If no user token is configured, STOP and run `/qa:auth-lark --login`; do not fall
   back to the app token for a write. Reads still fall back tenant↔user for any doc the chosen
   token can't see.

Setup: run `/qa:auth-lark --login` once (consent asks for full scopes on port 3000), then
`/qa:auth-lark` to probe & resolve. Secrets live in `.claude/qa-claude/.plugin.env` (git-ignored)
— never print or hardcode tokens.

Full details: [plugins/qa/rules/lark-mcp-guide.md](plugins/qa/rules/lark-mcp-guide.md) and the
[/qa:auth-lark command](plugins/qa/commands/auth-lark.md).
