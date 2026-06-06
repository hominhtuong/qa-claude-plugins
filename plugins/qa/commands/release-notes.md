---
description: Generate release notes for TWO audiences from a release — an internal technical changelog (Conventional-Commit grouped, with fixed-bug table) + a user/stakeholder-facing notes doc (plain language, benefit-led, grouped by highlight). Reads git commits since the previous tag + fixed bugs from the Lark board (read-only). Writes results/release-notes/<release>/. Localized. For Product Ops.
argument-hint: <release name or tag> [--since <prev-tag>] [--board <alias>] [--notify]
allowed-tools: Read, Glob, Grep, Bash, Agent
---

# /qa:release-notes — Release notes (internal + user-facing)

You are a **Product Ops** lead turning engineering output into communication. Request: **$ARGUMENTS**. Core logic = the **`release-notes-method`** skill. You produce two docs in two voices: a precise internal changelog and a jargon-free user-facing notes doc.

> **READ-ONLY** on the bug board: never creates/edits bugs. **NEVER print a token/secret.**
> **LANGUAGE — RULE #1**: write both docs in the configured output language (`.plugin.env` `LANGUAGE`, **default Vietnamese with diacritics**; keep product/technical terms in English) — see [output-language.md](../rules/output-language.md).
> **User-facing doc = NO jargon**: no commit hashes, no internal scope names, no ticket ids — only benefits.

## Must read first
- @${CLAUDE_PLUGIN_ROOT}/skills/release-notes-method/SKILL.md (categorization + the two output structures)
- [git-conventions.md](../rules/git-conventions.md) (Conventional-Commit types for grouping)

## Resolve scope
1. **Release** = `$ARGUMENTS` (name or git tag). Required — if absent, ask.
2. **Range**: `--since <prev-tag>` overrides; else resolve the previous tag via `git describe --tags --abbrev=0 <release>^` (fallback: `git tag --sort=-creatordate`, else first commit). State the range in both headers.
3. **Board**: `--board <alias>` overrides `active_board`. `--notify` → announce on the configured channel.

## Orchestration
1. **Gather in parallel**:
   - **Commits** — `git log <prev>..<release|HEAD> --pretty=format:'%h %s (%an)'`; drop merge/version-bump noise.
   - **Fixed bugs** — `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/lark_bitable.py" --status <closed-set> --version <release>` (try `--sprint` if version is empty). On `ok:false` → relay the `action` (`/qa:auth-lark`), continue commit-only, flag the bug section ⚠️.
   - **Feature names** — Glob `results/<feature>/` to translate commit scopes into human feature names.
2. **Categorize** commits by Conventional-Commit type (`feat`→Features, `fix`→Fixes, rest→Internal).
3. **Write** `results/release-notes/<release>/internal-changelog.md` (technical, grouped + fixed-bug table) and `release-notes.md` (user-facing, plain language, ✨Highlights / 🔧Improvements / 🐞Fixes / ⚠️Known issues).
4. **Deliver** (optional): with `--notify`, send the highlight headline + counts.
5. **Conclude**: print both file paths + a 3-line summary (feature count, fix count, headline).

## Rules
- READ-ONLY on the board; never fabricate entries (no `feat` commits ⇒ empty Highlights, not invented).
- User-facing doc translates subjects into benefits; never leaks hashes/scopes/ticket ids.
- Vietnamese with diacritics for narrative; English for product/technical terms.
- This reads git history only — to actually commit/push/PR a release, use `/qa:push-code` / `/qa:merge-request`.
