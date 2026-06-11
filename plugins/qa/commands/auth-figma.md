---
description: Optional Figma token setup for /qa:exploratory-ui — most users DON'T need it (exploratory-ui reads Figma through the bundled Figma MCP, just log in when asked). A FIGMA_TOKEN is only a fallback for headless/no-MCP runs or to fetch the exact design text+font oracle. When needed, you (Claude) open the Figma token page in the user's browser, they paste a token back, and you validate + write it into .plugin.env for them — they never edit a file.
argument-hint: [open | set <token> | check]
allowed-tools: Bash, Read
---

# /qa:auth-figma — set up a Figma token (only if needed; MCP is the default)

> **Most users can skip this.** `/qa:exploratory-ui` renders the Figma design through the bundled
> **Figma MCP** — just log in to Figma when prompted, no token. A `FIGMA_TOKEN` (personal access
> token) is only needed when MCP isn't available (headless/cron) OR to pull the **exact** design
> text + font-name oracle via Figma's REST API (a fidelity upgrade over reading it from the render).

## Step 0 — Decide if a token is even needed
Run a status check first:
```bash
PY="$(command -v python3 || command -v python)"
"$PY" "${CLAUDE_PLUGIN_ROOT}/scripts/figma_auth.py" check --json
```
- `state: no-token` and the user is running interactively with the Figma MCP → **tell them they
  likely don't need a token**; only proceed if they specifically want the REST fallback / exact text.
- `state: valid` → already set up, nothing to do.
- `state: invalid` → the saved token is bad; re-run the set flow below.

## Step 1 — Open the token page in their browser
```bash
"$PY" "${CLAUDE_PLUGIN_ROOT}/scripts/figma_auth.py" open
```
This opens `https://www.figma.com/settings` (and prints the URL as a fallback). Tell the user:
**Settings → Security → Personal access tokens → Generate new token**, set **scope "File content" =
Read**, copy the token (starts with `figd_`), and paste it back to you here.

## Step 2 — Validate + save it for them
When the user pastes the token, run (substitute the pasted value):
```bash
"$PY" "${CLAUDE_PLUGIN_ROOT}/scripts/figma_auth.py" set --token "<pasted-token>"
```
The script calls Figma's `/v1/me` to **validate**, then writes `FIGMA_TOKEN` into
`.claude/qa-claude/.plugin.env` (via the safe upsert — it never clobbers other keys). It only ever
prints a **masked** token. On success, confirm to the user (configured language) that
`/qa:exploratory-ui` can now use the REST fallback + exact text/font oracle.

**If validation fails:** `HTTP 401/403` → the token is wrong/expired or missing the *File content*
scope — have them regenerate it. TLS error → `/qa:doctor --fix` (corporate proxy), then retry.

## Notes
- The token is a **secret** — it lives only in `.claude/qa-claude/.plugin.env` (git-ignored). Never
  echo the full token back to the user or into the report.
- This is the same assisted pattern as `/qa:auth-lark` (you run the script; the user just pastes).
- To remove it, delete the `FIGMA_TOKEN=` line from `.plugin.env`.
