---
description: Introduce & guide usage of the qa plugin — which commands, which skills, the automation vs manual workflows, and the platform router
argument-hint: [command name / topic to dig into — empty = overview]
allowed-tools: Read, Glob, Grep
---

# /help — QA Plugin Guide

Topic: **$ARGUMENTS** (empty → full overview).

## Steps
Run **skill `help-info`**:
1. Dynamically scan the plugin (`Glob` `commands/*.md` + `skills/*/SKILL.md` in the plugin directory) → list **only the commands/skills that actually exist** (do not invent).
2. Empty `$ARGUMENTS` → print **overview**: one prefix-free `qa` plugin with the platform router (web/android/ios reads only the matching skill), and the two distinct flows (AUTOMATION: exploratory → plan-tests → cook → run → fix → review → push-code → merge-request; MANUAL: analyze-spec → plan-gen-testcases → gen-testcases → log-bug).
3. With `$ARGUMENTS` (e.g. `cook`, `gen-testcases`, "platform routing") → read that exact command/skill and explain it in depth: purpose, arguments, the skill it calls, usage example.

## Principles
- Read & guide only, do NOT modify anything.
- Print concisely, with real command examples. All commands are **prefix-free** (`/cook`, `/run`, `/log-bug`). Automation and manual-QA use **distinct command names** (e.g. `/cook` writes code vs `/gen-testcases` writes test cases; `/plan-tests` vs `/plan-gen-testcases`; `/analyze` vs `/analyze-spec`; `/count-cases` vs `/count-testcases`).
