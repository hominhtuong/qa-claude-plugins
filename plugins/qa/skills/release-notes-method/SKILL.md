---
name: release-notes-method
description: Reusable logic to generate stakeholder + end-user release notes for a release. Reads git commits since the previous tag (categorized via Conventional Commits — git-conventions.md), the fixed bugs in this release from the Lark Bitable board (scripts/lark_bitable.py), and shipped features from results/, then writes TWO audiences under results/release-notes/<release>/: internal-changelog.md (technical, grouped by type) + release-notes.md (user-facing, plain language, grouped by feature/highlight). Read-only on the board; localized output. Reusable core behind the release-notes command. For Product Ops.
---

# Skill: release-notes-method

Reusable capability: turn raw commits + fixed bugs into **two release documents** for two audiences — an internal technical changelog and a user/stakeholder-facing notes doc written in plain language. This is the Product-Ops bridge from "what engineering did" to "what we tell people".

> 📣 **Two outputs, two voices**: `internal-changelog.md` = precise, grouped by Conventional-Commit type, links commits/bugs. `release-notes.md` = benefit-led, no jargon, grouped by feature/highlight, safe to paste into a changelog page or announcement.

## Inputs
1. **Commits** — `git log <prev-tag>..<release-or-HEAD>` parsed by Conventional Commits (`feat|fix|test|chore|refactor|docs|ci`) per `../../rules/git-conventions.md`. Resolve the previous tag with `git describe --tags --abbrev=0 <release>^` (or `git tag --sort=-creatordate`); if there is no prior tag, use the repo's first commit. State the resolved range.
2. **Fixed bugs** — `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/lark_bitable.py" --status <closed-set> --version <release>` (or `--sprint`) → the defects resolved in this release, with priority + feature. On board `ok:false` relay the `action` (`/qa:auth-lark`) and continue with commit-only notes, flagging the bug section ⚠️ unavailable.
3. **Shipped features** — `results/<feature>/` analysis/plans referenced by the commits, to name features in human terms (not just commit subjects).

## Procedure
1. **Resolve the range** (prev-tag → release/HEAD) and the bug filter (version/sprint). Print the resolved range in both docs' headers.
2. **Gather** commits (Bash git) + fixed bugs (`lark_bitable.py`) — concurrently. Do NOT print tokens.
3. **Categorize commits**: `feat` → Features/Improvements; `fix` → Bug fixes; `refactor|chore|ci|docs|test` → Internal/Maintenance (folded or omitted in the user-facing doc). Drop noise (merge commits, version bumps) from the user-facing doc.
4. **Write `internal-changelog.md`** — grouped by type, each line `<scope>: <subject>` + short hash; a Fixed-bugs table mapping bug → priority → feature.
5. **Write `release-notes.md`** — user-facing: a 1-2 line intro, **Highlights** (top 3-5 user-visible changes as benefits), **Improvements**, **Fixes** (plain language — "Fixed an issue where…", not the commit subject), optional **Known issues** (open Critical/High from the board). No internal scopes, no hashes, no jargon.
6. **Optional delivery**: notify/share via the plugin's configured channel if requested.
7. **Conclude**: print both file paths + a 3-line summary (feature count, fix count, highlight headline).

## Output structure
`results/release-notes/<release>/`
- **internal-changelog.md** — Header (range, date) · Features (`feat`) · Fixes (`fix`) · Internal (`refactor/chore/ci/docs/test`) · Fixed bugs table (`| Bug | Priority | Feature | Status |`) · Contributors (optional, from git authors).
- **release-notes.md** — Header (release, date) · Intro · ✨ Highlights · 🔧 Improvements · 🐞 Fixes (plain language) · ⚠️ Known issues (optional).

## Rules
- **READ-ONLY** on the board; never create/edit bugs. Never print tokens.
- **User-facing doc has NO jargon** — translate commit subjects into benefits; never leak internal scope names, hashes, or ticket ids into `release-notes.md` (those live only in the internal changelog).
- **Don't invent** — a release with no `feat` commits has an empty Highlights section, not a fabricated one.
- **LANGUAGE**: write both docs in the configured output language (`.plugin.env` `LANGUAGE`, default Vietnamese with diacritics; keep product/technical terms in English) — see `../../rules/output-language.md`.
- Conventional-Commit parsing follows `../../rules/git-conventions.md`.
