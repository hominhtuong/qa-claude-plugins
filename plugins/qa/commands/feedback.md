---
description: Send feedback or report a problem about the qa plugin — opens a pre-filled GitHub issue (plugin version, OS, and what you were doing auto-filled) so the maintainer can collect & fix it. No login needed to view the link; uses `gh` to file it directly if installed.
argument-hint: <your feedback / the problem you hit>
allowed-tools: Bash, Read
---

# /qa:feedback — Send feedback / report a problem

The user's message: **$ARGUMENTS**

Turn it into a GitHub issue on the plugin repo so the maintainer can collect & fix it. **Privacy**: send ONLY what the user typed + plugin version + OS — nothing silent, no secrets/tokens/file contents. This runs only because the user invoked it.

## Steps
1. **Clarify briefly if vague**: `$ARGUMENTS` empty/unclear → ask ONE short question (what happened? what did you expect?). If they hit an error, capture the key error line + the command they ran this session as the `context`.
2. **Pick the type**: `bug` (something broke), `idea` (feature/improvement), or `question`. Default `bug` for a failure.
3. **Build the issue link** (cross-platform Python):
   ```bash
   PY="$(command -v python3 || command -v python)"
   "$PY" "${CLAUDE_PLUGIN_ROOT}/scripts/feedback.py" "<message>" --type <bug|idea|question> --context "<what they were doing / error, if any>"
   ```
   It prints `FEEDBACK_URL=<pre-filled GitHub new-issue link>` (and a `gh issue create …` command if `gh` is installed).
4. **Hand the user the link**: present `FEEDBACK_URL` as a clickable markdown link — *"Bấm vào đây để gửi (đã điền sẵn, chỉ cần bấm Submit)."* The link needs no login to view/fill; submitting needs a free GitHub account.
5. **Offer the direct path**: if the script printed a `gh issue create` command (gh is installed), offer to run it to file the issue immediately — **ask the user first**, then run it and return the created issue URL.

## Principles
- Opt-in only; never auto-send. Never include `.env` values, tokens, or file contents — just the user's words + version + OS.
- Keep the message faithful to what the user said; don't editorialize.
- Logic lives in `scripts/feedback.py` (stdlib, cross-platform).
