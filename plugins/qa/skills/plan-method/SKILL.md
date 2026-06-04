---
name: plan-method
description: Reusable logic to design the test plan file plans/<feature>/plan.md after passing the exploratory GATE (no [APP-BUG]). Platform-agnostic — the command passes the platform (web/app) so the right rules are read. Structure Objective / Analysis / Steps / Screens / Test cases / TestNG XML / Missing ID Report / Notes. Do NOT write code at the plan step. Reusable core behind the plan-tests command.
---

# Skill: plan-method

Reusable capability: from a feature **that passed a clean exploratory pass** → a **firm plan (.md)** describing how to build the tests, for `/qa:cook` to execute. **Do NOT write code** at this step. Platform-agnostic: the command passes `<platform>` (web/app) → read the right rules `../../rules/<platform>/design-pattern.md`.

> 🚦 **Mandatory GATE — exploratory first, plan second**: only plan a feature/sub-feature **with no `[APP-BUG]`** (the `exploratory-method` skill). A feature that's broken → NO test plan, the deliverable is a bug report sent to dev. Large feature → gate per sub-feature.

## Procedure
1. **Read the platform rules**: `../../rules/<platform>/design-pattern.md` (+ the corresponding coding-rules, design-system) — the command states clearly whether the platform is `web` or `app`. Read `sitemap/sitemap.md` + `screens/<group>/test-hints.json`.
2. **Survey for reuse**: Glob the feature's existing Screen/Test → reuse `base`/`utils`/`actions`/`models`, no duplication. Element source: Screen.java → elements.json → (if missing) note "needs MCP/DOM discovery" for `/qa:cook` to run.
3. **Write the file** `plans/<feature>/plan.md` (folder lowercase-hyphen; if it exists → update it) per the structure:
   - **Objective** — the feature's test goal.
   - **Analysis** — related files · reuse vs new files · element source (Screen/JSON/discovery).
   - **Steps** — each step: file path + create/edit + details.
   - **Screens** — table `| Screen | File | Key element (isDisplayed) | Main locator | Action methods |`.
   - **Test cases** — table `| Test | Scenario | Assertion |`; list ALL functions, **1 function = 1 scenario + assertion**.
   - **TestNG XML** — (app ONLY) `GoToHomeTest` is the first `<test>` block, then the feature tests.
   - **Missing ID Report** — `| element | screen | current locator | description |` (omit if everything has an id).
   - **Notes** — risks / open questions.
4. **Layering principle** (write into the plan): `screens` (no-assert) → `tests` (assert) → `regression/smoke` (compose). Each Screen described via the `declare-screen` skill (key element, action = verb). Element expected to lack an id → note it for `/qa:cook` to RECORD via the `missing-ids` skill.
5. **Correct expectations**: the plan records the **canonical expectation** (per spec/original app) for each test so `/qa:cook` keeps the test honest. The sitemap only **lists** screens to create/update — `/qa:cook` is what actually writes them.
6. **Conclude**: print the plan path + a 3-5 line summary for the user to review before `/qa:cook`.

> Don't write code at the plan step. Cooking mobile code is the `cook-app` skill, web is the `cook-web` skill. Detailed gate logic: the `exploratory-method` skill.
