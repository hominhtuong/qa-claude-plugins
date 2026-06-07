---
name: plan-method
description: Reusable logic to design the test plan file plans/<feature>/plan.md after the exploratory GATE. By DEFAULT the plan is built even when bugs exist (declarable+actionable elements → KNOWN-BUG cases; the rest → Blocked cases); --stop-on-bug makes any [APP-BUG] stop at the bug report. Platform-agnostic — the command passes the platform (web/app) so the right rules are read. Structure Objective / Analysis / Steps / Screens / Test cases / TestNG XML / Missing ID Report / Known issues & Blocked cases / Notes. Do NOT write code at the plan step. Reusable core behind the plan-tests command.
---

# Skill: plan-method

Reusable capability: from a feature **after its exploratory pass** → a **firm plan (.md)** describing how to build the tests, for `/qa:cook` to execute. **Do NOT write code** at this step. Platform-agnostic: the command passes `<platform>` (web/app) → read the right rules `../../rules/<platform>/design-pattern.md`.

> 🚦 **GATE — two modes (the command sets the mode via `--stop-on-bug`)**:
> - **Default (plan-anyway)**: bugs do NOT block planning. For each `[APP-BUG]`, if the element is still **declarable** (locator findable) AND **actionable** (clickable/typeable) → put it in the plan as a `KNOWN-BUG: <APP-ID>` case that asserts the **canonical expectation** (so it fails honestly until dev fixes — intended; QA runs ahead of the fix). Only un-declarable / un-actionable parts (element absent, page crashes, no interaction possible) → **Blocked cases**. The bug report is still a deliverable alongside the plan.
> - **`--stop-on-bug`**: only plan a feature/sub-feature **with no `[APP-BUG]`**. A broken feature → NO test plan; deliverable is the bug report for dev.
> Large feature → apply the active mode per sub-feature.

## Procedure
1. **Read the platform rules**: `../../rules/<platform>/design-pattern.md` (+ the corresponding coding-rules, design-system) — the command states clearly whether the platform is `web` or `app`. Read `sitemap/sitemap.json` + `screens/<group>/test-hints.json`.
2. **Survey for reuse**: Glob the feature's existing Screen/Test → reuse `base`/`utils`/`actions`/`models`, no duplication. Element source: Screen.java → elements.json → (if missing) note "needs MCP/DOM discovery" for `/qa:cook` to run.
3. **Write the file** `plans/<feature>/plan.md` (folder lowercase-hyphen; if it exists → update it) per the structure:
   - **Objective** — the feature's test goal.
   - **Analysis** — related files · reuse vs new files · element source (Screen/JSON/discovery).
   - **Steps** — each step: file path + create/edit + details.
   - **Screens** — table `| Screen | File | Key element (isDisplayed) | Main locator | Action methods |`.
   - **Test cases** — table `| Test | Scenario | Assertion | Known-bug |`; list ALL functions, **1 function = 1 scenario + assertion**. The Known-bug column carries the `<APP-ID>` for cases that assert the canonical expectation and are expected to fail until dev fixes (default mode).
   - **TestNG XML** — (app ONLY) `GoToHomeTest` is the first `<test>` block, then the feature tests.
   - **Missing ID Report** — `| element | screen | current locator | description |` (omit if everything has an id).
   - **Known issues & Blocked cases** — (default mode) `| Case | APP-ID | Plannable? | Reason |`: for every `[APP-BUG]` from exploratory, record whether it was planned-with-KNOWN-BUG or excluded as blocked (and why). Omit when exploratory was clean / under `--stop-on-bug`.
   - **Notes** — risks / open questions.
4. **Layering principle** (write into the plan): `screens` (no-assert) → `tests` (assert) → `regression/smoke` (compose). Each Screen described via the `declare-screen` skill (key element, action = verb). Element expected to lack an id → note it for `/qa:cook` to RECORD via the `missing-ids` skill.
   - **Run-scoped lifecycle**: if the plan creates/changes base/core (`BaseTest`/`PlaywrightFactory`, or the app driver factory), state it explicitly — **one** browser/driver launched **once** at suite start (`@BeforeSuite`) and closed **once** at suite end (`@AfterSuite`), reused across every case (web: `../../rules/web/design-pattern.md` §7). Never open/close per test (causes browser flicker on regression).
5. **Correct expectations**: the plan records the **canonical expectation** (per spec/original app) for each test so `/qa:cook` keeps the test honest. The sitemap only **lists** screens to create/update — `/qa:cook` is what actually writes them.
6. **Conclude**: print the plan path + a 3-5 line summary for the user to review before `/qa:cook`.

> Don't write code at the plan step. Cooking mobile code is the `cook-app` skill, web is the `cook-web` skill. Detailed gate logic: the `exploratory-method` skill.
