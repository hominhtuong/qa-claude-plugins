---
description: Introduce & guide usage of the QA plugin suite (core + auto + qa-manual) — which commands, which skills, the workflow, and how to call namespaced
argument-hint: [command name / topic to dig into — empty = overview]
allowed-tools: Read, Glob, Grep
---

# /help — QA Plugin Suite Guide

Topic: **$ARGUMENTS** (empty → full overview).

## Steps
Run **skill `help-info`**:
1. Dynamically scan installed plugins (`Glob` `*/commands/*.md` + `*/skills/*/SKILL.md` in the plugin directory) → list **only the commands/skills that actually exist** (do not invent).
2. Empty `$ARGUMENTS` → print **overview**: the 3 plugins (core/auto/qa-manual), the platform-router philosophy (web/android/ios reads only the skill for the matching platform), the standard flow (exploratory → plan-tests → cook → run → fix → review → push-code → merge-request), and how to call namespaced.
3. With `$ARGUMENTS` (e.g. `cook`, `exploratory`, "platform routing", "qa-manual") → read that exact command/skill and explain it in depth: purpose, arguments, the skill it calls, usage example.

## Principles
- Read & guide only, do NOT modify anything.
- Print concisely, with real command examples. Remind to type **namespaced** (`/auto:cook` vs `/qa-manual:cook`) when there are commands with the same name.
