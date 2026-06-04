---
description: Introduce & guide usage of the qa plugin — which commands, which skills, the automation/manual workflows, and the mode + platform routers
argument-hint: [command name / topic to dig into — empty = overview]
allowed-tools: Read, Glob, Grep
---

# /help — QA Plugin Guide

Topic: **$ARGUMENTS** (empty → full overview).

## Steps
Run **skill `help-info`**:
1. Dynamically scan the plugin (`Glob` `commands/*.md` + `skills/*/SKILL.md` in the plugin directory) → list **only the commands/skills that actually exist** (do not invent).
2. Empty `$ARGUMENTS` → print **overview**: one prefix-free `qa` plugin, the mode router (automation vs manual via `detect-mode`) + platform router (web/android/ios reads only the matching skill), and the standard flows (exploratory → plan-tests → cook → run → fix → review → push-code → merge-request for automation; analyze → plan-tests → cook → log-bug for manual).
3. With `$ARGUMENTS` (e.g. `cook`, `exploratory`, "mode routing", "platform routing") → read that exact command/skill and explain it in depth: purpose, arguments, the skill it calls, usage example.

## Principles
- Read & guide only, do NOT modify anything.
- Print concisely, with real command examples. All commands are **prefix-free** (`/cook`, `/run`, `/log-bug`). Note that the dual-purpose commands (`cook`/`plan-tests`/`analyze`/`count-cases`) auto-detect automation vs manual mode, overridable with `--auto`/`--manual`.
