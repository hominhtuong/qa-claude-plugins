---
name: help-info
description: Skill that introduces & guides usage of the open-source qa plugin — lists the commands (invoked as /qa:<name>), explains the platform router (web/android/ios reads only the matching skill), and the two distinct workflows (AUTOMATION exploratory → plan-tests → cook → run → fix → review → push-code → merge-request; MANUAL analyze-spec → plan-gen-testcases → gen-testcases → log-bug). Used by the /qa:help command, or when the user asks "how do I use this plugin / what commands are there / what skills are there".
---

# Skill: help-info

Reusable capability: answer "what's in this QA plugin and how do I use it". When the caller (command `/qa:help` or a user question) needs an overview → print the map below, then (if the user asks something specific) dig into the matching command/skill. Dynamically scan `${CLAUDE_PLUGIN_ROOT}/commands/*.md` + `skills/*/SKILL.md` to list **only what is actually installed** (don't invent non-existent commands).

## One plugin, namespaced `/qa:` commands
Everything lives in a single `qa` plugin. Plugin commands are invoked as **`/qa:<name>`** (e.g. `/qa:exploratory`, `/qa:run`, `/qa:gen-testcases`, `/qa:log-bug`) — the `qa:` namespace is required by Claude Code and cannot be removed. The `*-method`/`*-app`/`*-web` entries in the menu are **internal skills**; guide users to the commands, not the skills. It covers two worlds with **distinct command names** (no ambiguity):
- **Automation** — Web (Playwright) + App (Appium iOS/Android): `cook`, `plan-tests`, `analyze`, `count-cases`, plus exploratory/find-elements/run/fix/review/push-code/merge-request. These **auto-route by platform**.
- **Manual QA** — test cases as documents: `gen-testcases`, `plan-gen-testcases`, `analyze-spec`, `count-testcases`, `log-bug`, `update-board`.

## Platform router (automation Step 0 — `detect-platform`)
Take the platform from the argument (`web|android|ios`), else auto-detect (playwright.config / android-capabilities / ios-capabilities), else ask. Then **read only 1 platform skill** (save tokens):
- `find-elements` → `find-elements-web` | `-android` | `-ios`
- `cook` → `cook-web` | `cook-app` · `run` → `run-web` | `run-app` · `navigate` → `navigate-web` | `navigate-app`
- design/coding rules → `rules/web/*` | `rules/app/*`

## Standard workflow — automation
1. `/qa:exploratory <feature> [platform]` — explore like a senior QA, hunt bugs, capture evidence, output a bug report. **GATE**: any `[APP-BUG]` → report to dev, stop (do not write tests).
2. `/qa:plan-tests <feature>` — design the automation test plan (only when exploratory is clean).
3. `/qa:find-elements <screen>` — extract locators if needed.
4. `/qa:cook <plan|requirement>` — write Page Object + test code.
5. `/qa:run [platform]` — run + triage failures (`[APP-BUG]` vs `[FRAMEWORK]`).
6. `/qa:fix <bug>` — fix the right layer (do not edit the test to dodge an `[APP-BUG]`).
7. `/qa:review-change` · `/qa:review-codebase` → `/qa:push-code` → `/qa:merge-request`.

## Standard workflow — manual QA
`/qa:analyze-spec <spec>` → `/qa:plan-gen-testcases <feature>` → `/qa:gen-testcases <plan>` (test cases into Sheet/xlsx) → `/qa:log-bug <description>` (set the board with `/qa:update-board`).

## Shared / utility commands
`/qa:setup-plugin` (one-click project setup — Claude runs the script, no terminal) · `/qa:help` (this overview) · `/qa:status` · `/qa:ask` · `/qa:missing-test-ids` · `/qa:count-cases` · `/qa:count-testcases` · `/qa:kill-appium`. `/qa:setup-plugin` creates `.claude/qa-claude/` (`.env` + `log-bug.config.yml` + templates) and checks the toolchain (skill `setup`/`doctor`); enables optional Lark/Slack/Teams/Telegram notify + Cloudflare R2 / S3 report upload.

> A project can add its own commands in `.claude/commands/` (invoked WITHOUT a prefix, e.g. `/mycmd`); they run independently alongside the plugin's `/qa:` commands (different namespaces, no clash). Install / update: `/plugin marketplace update qa-claude` → `/reload-plugins`.
