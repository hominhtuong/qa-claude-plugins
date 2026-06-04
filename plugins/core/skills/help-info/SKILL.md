---
name: help-info
description: Skill that introduces & guides usage of the open-source qa-claude QA plugin suite (core + auto + qa-manual) — lists commands per plugin, explains the platform-router philosophy (web/android/ios reads only the skill for the matching platform), the standard workflow (exploratory → plan-tests → cook → run → fix → review → push-code → merge-request) and how to call commands namespaced. Used by the /help command, or when the user asks "how do I use this plugin / what commands are there / what skills are there".
---

# Skill: help-info

Reusable capability: answer "what's in this QA plugin suite and how do I use it". When the caller (command `/help` or a user question) needs an overview → print the map below, then (if the user asks something specific) dig into the matching command/skill. Dynamically scan `${CLAUDE_PLUGIN_ROOT}/../*/commands/*.md` + `*/skills/*/SKILL.md` to list **only what is actually installed** (don't invent non-existent commands).

## The 3 plugins
- **core** — shared across every project (domain-agnostic): `/help` `/status` `/ask` `/missing-test-ids` + skills `commit-push` `build-verify` `missing-ids` `help-info`.
- **auto** — multi-platform automation **Web (Playwright) + App (Appium iOS/Android)**. Every command **auto-routes by platform** (router) then reads only the skill for the matching platform → no wasted tokens.
- **qa-manual** — manual QA: generate test cases into Sheet/xlsx, plan tests, log bugs to Lark, analyze requirements.

## Platform-router philosophy (auto)
Every auto command has a **Step 0 — `detect-platform`**: take the platform from the argument (`web|android|ios`), if empty auto-detect the project (playwright.config / android-capabilities / ios-capabilities), if ambiguous ask. Then **read only 1 platform skill**:
- `find-elements` → `find-elements-web` | `-android` | `-ios`
- `cook` → `cook-web` | `cook-app` · `run` → `run-web` | `run-app` · `navigate` → `navigate-web` | `navigate-app`
- design/coding rules → `rules/web/*` | `rules/app/*`

## Standard workflow (automation)
1. `/exploratory <feature> [platform]` — explore like a senior QA, hunt bugs, capture evidence, output a bug report. **GATE**: any `[APP-BUG]` → report to dev, stop (do not write tests).
2. `/plan-tests <feature>` — design the test plan (only when exploratory is clean).
3. `/find-elements <screen>` — extract locators if needed.
4. `/cook <plan|requirement>` — write Page Object + test code.
5. `/run [platform]` — run + triage failures (`[APP-BUG]` vs `[FRAMEWORK]`).
6. `/fix <bug>` — fix the right layer (do not edit the test to dodge an `[APP-BUG]`).
7. `/review-change` · `/review-codebase` — check against rules. → `/push-code` → `/merge-request`.

## Manual QA workflow (qa-manual)
`/qa-manual:analyze <spec>` → `/qa-manual:plan-tests <feature>` → `/qa-manual:cook <plan>` (generate test cases into Sheet/xlsx) → `/qa-manual:log-bug <description>`.

## How to call
- Typing **bare** `/cook` → the project's **local** command wins (if any). For the plugin version → type **namespaced**: `/auto:cook`, `/qa-manual:cook`, `/core:status`.
- Two plugins have same-named commands (`cook`, `plan-tests`) → **always namespaced** to be clear: `/auto:cook` (write code) vs `/qa-manual:cook` (generate test cases).

> Plugins **override by priority**: a project's local command/skill (if same name) beats the plugin → projects can override without editing the plugin. Install / update: `/plugin marketplace update qa-claude` → `/reload-plugins`.
