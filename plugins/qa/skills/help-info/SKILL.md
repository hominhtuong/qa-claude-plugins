---
name: help-info
description: Skill that introduces & guides usage of the open-source qa plugin — lists the prefix-free commands, explains the platform router (web/android/ios reads only the matching skill), and the two distinct workflows (AUTOMATION exploratory → plan-tests → cook → run → fix → review → push-code → merge-request; MANUAL analyze-spec → plan-gen-testcases → gen-testcases → log-bug). Used by the /help command, or when the user asks "how do I use this plugin / what commands are there / what skills are there".
---

# Skill: help-info

Reusable capability: answer "what's in this QA plugin and how do I use it". When the caller (command `/help` or a user question) needs an overview → print the map below, then (if the user asks something specific) dig into the matching command/skill. Dynamically scan `${CLAUDE_PLUGIN_ROOT}/commands/*.md` + `skills/*/SKILL.md` to list **only what is actually installed** (don't invent non-existent commands).

## One plugin, prefix-free commands
Everything lives in a single `qa` plugin, so commands are called **bare** (no prefix): `/cook`, `/run`, `/gen-testcases`, `/log-bug`, `/status`. It covers two worlds with **distinct command names** (no ambiguity):
- **Automation** — Web (Playwright) + App (Appium iOS/Android): `cook`, `plan-tests`, `analyze`, `count-cases`, plus exploratory/find-elements/run/fix/review/push-code/merge-request. These **auto-route by platform**.
- **Manual QA** — test cases as documents: `gen-testcases`, `plan-gen-testcases`, `analyze-spec`, `count-testcases`, `log-bug`, `update-board`.

## Platform router (automation Step 0 — `detect-platform`)
Take the platform from the argument (`web|android|ios`), else auto-detect (playwright.config / android-capabilities / ios-capabilities), else ask. Then **read only 1 platform skill** (save tokens):
- `find-elements` → `find-elements-web` | `-android` | `-ios`
- `cook` → `cook-web` | `cook-app` · `run` → `run-web` | `run-app` · `navigate` → `navigate-web` | `navigate-app`
- design/coding rules → `rules/web/*` | `rules/app/*`

## Standard workflow — automation
1. `/exploratory <feature> [platform]` — explore like a senior QA, hunt bugs, capture evidence, output a bug report. **GATE**: any `[APP-BUG]` → report to dev, stop (do not write tests).
2. `/plan-tests <feature>` — design the automation test plan (only when exploratory is clean).
3. `/find-elements <screen>` — extract locators if needed.
4. `/cook <plan|requirement>` — write Page Object + test code.
5. `/run [platform]` — run + triage failures (`[APP-BUG]` vs `[FRAMEWORK]`).
6. `/fix <bug>` — fix the right layer (do not edit the test to dodge an `[APP-BUG]`).
7. `/review-change` · `/review-codebase` → `/push-code` → `/merge-request`.

## Standard workflow — manual QA
`/analyze-spec <spec>` → `/plan-gen-testcases <feature>` → `/gen-testcases <plan>` (test cases into Sheet/xlsx) → `/log-bug <description>` (set the board with `/update-board`).

## Shared / utility commands
`/help` (this overview) · `/status` · `/ask` · `/missing-test-ids` · `/count-cases` · `/count-testcases` · `/kill-appium`. Integrations setup: skills `setup`/`doctor` — scaffold `./.env` + editable resources in `./.claude/qa-claude/` (testcase template, log-bug board config), plus optional Lark/Slack/Teams/Telegram notify + Cloudflare R2 / S3 report upload.

> Project override: a project's **local** `.claude/commands/<name>.md` (if same name) beats the plugin's bare command → projects can override without editing the plugin. Install / update: `/plugin marketplace update qa-claude` → `/reload-plugins`.
