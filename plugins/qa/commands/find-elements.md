---
description: Extract durable locators for a screen — auto-route by platform (web Playwright / android / ios), reading only the matching platform skill, nothing extra
argument-hint: <screen-name / feature> [web|android|ios] [navigation path if known]
allowed-tools: Read, Glob, Grep, Edit, Write, Bash, Agent
---

# /qa:find-elements — Extract locators for a screen (platform router)

Input: **$ARGUMENTS**

## Step 0 — Lock platform (routing — do NOT read extra skills)
Run **skill `detect-platform`** (spec: `${CLAUDE_PLUGIN_ROOT}/rules/platform-detect.md`): explicit argument `web|android|ios` → use it directly; if empty, auto-detect from the project; still ambiguous → ask the user. Result = **one** `platform`.

## Step 1 — Open the correct screen (only the locked platform skill)
- **web** → skill `navigate-web` (Playwright MCP: navigate + login + back to Home → feature screen).
- **android | ios** → skill `navigate-app` (Appium MCP: device preflight + install + session + GoToHome → screen).

## Step 2 — Extract locators (READ EXACTLY 1 SKILL — this is the token-saving point)
> Read only the skill matching `platform`. Do **NOT** read the other 2 platform skills.

| platform | skill to read | locator priority |
|---|---|---|
| **web** | `find-elements-web` | `getByRole` > `getByTestId` (data-testid) > label/placeholder/name > text/heading > semantic CSS |
| **android** | `find-elements-android` | `id` (resource-id) > `accessibility` (content-desc) > `uiautomator` > `xpath` |
| **ios** | `find-elements-ios` | `accessibility`/`id` > `-ios predicate string` > `-ios class chain` > `xpath` |

## Step 3 — Record catalog & test-id debt
- Save the element + chosen locator into the project's catalog (`screens/<group>/elements.json` app · `missing-test-ids/`/page-object web) to reuse on the next lookup.
- Element **that can't be anchored by id/testid** → **skill `missing-ids`** (RECORD) collects it into the Missing ID Report for dev.

## Output
A table `element (role) | chosen locator | raw attributes | missing id?` for the locked `platform`, ready for `/qa:cook` (declare Screen/Page Object). Print the platform used clearly. When done → close the session (`appium_quit_session` / `browser_close`) if the navigate skill opened one.

> This is the template router for the whole plugin: **detect-platform → read exactly 1 platform skill → agnostic skill**. Every other command (`/qa:exploratory`, `/qa:cook`, `/qa:run`, `/qa:fix`) follows this same shape.
