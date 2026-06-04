---
description: Exploratory gate first, then design an AUTOMATION test plan (plans/<feature>/plan.md) ONLY when the app is clean; if the app is buggy, produce a bug report. Auto-routes by platform to read the correct design-pattern rules
argument-hint: <feature-name> [web|android|ios] [requirement description / Lark link / Figma]
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, WebSearch, Agent
---

# /qa:plan-tests — Exploratory gate → Design an automation test plan (platform router)

User request: **$ARGUMENTS**

> Want to plan MANUAL TEST CASES (not automation code) instead? Use **`/qa:plan-gen-testcases`**.

Goal: create a **solid plan (.md file)** describing how to implement the tests. `/qa:cook` executes it afterward. **Do NOT write code** at this step. (The name `/qa:plan-tests` distinguishes it from plan-release/plan-sprint.)

> 🚦 **GATE — exploratory first, plan after**: *Automation only works when the app is correct.* A feature with `[APP-BUG]` → **do NOT make a test plan**, the deliverable is a bug report for dev. Only a **clean** exploratory leads to a plan.

## Step 0 — Lock platform (routing)
Run **skill `detect-platform`** → one `platform`. It decides which design-pattern rules to read in Step 2.

## Step 1 — EXPLORATORY GATE (before anything)
1. Is there a recent bug report yet? `results/exploratory/<group>/dev-bug-report-*.md` + `bug-summary.md`. None/stale/changed → run **`/qa:exploratory <feature-name> <platform>`**.
2. Read the result:
   - 🔴 **Has `[APP-BUG]`** → **STOP planning** for that part; print "Feature NOT complete — N app bugs, see `dev-bug-report-*.md`". Do NOT create `plans/<feature>/plan.md`.
   - 🟢 **No `[APP-BUG]`** → app correct → continue to Step 2. Elements extracted during exploratory are used for Layer 1/2.
3. Large feature → **gate per sub-feature** (plan the clean parts, report bugs for the broken parts).

## Step 2 — Design the plan — skill `plan-method` (agnostic) + platform rules
Read **skill `plan-method`** (plan structure + layering principles + element 3-layer lookup) and the **design-pattern rules per `platform`** (only 1 branch):
- **web** → `rules/web/design-pattern.md` · `coding-rules.md` · `design-system.md`.
- **android | ios** → `rules/app/design-pattern.md` · `coding-rules.md` · `design-system.md`.

Also read the project's `@CLAUDE.md` + sitemap/test-hints if present. If the request has a Lark/Figma link → spawn a reader agent (`agent-lark-reader`/`agent-figma-reader`, 1 agent/URL, max 5/batch, append to `plans/<feature>/tracking.md`; details in [lark-mcp-guide.md](../rules/lark-mcp-guide.md)).

## Step 3 — Write the plan to `plans/<feature>/plan.md` (lowercase-hyphen; update if it exists)
Structure (per `plan-method`):
```markdown
## Objective
## Analysis   (related files · reuse · new files · element source: Screen/JSON/discovery)
## Steps      (each step: file path + create/edit + details)
## Screens    (| Screen | File | Key element (isDisplayed) | Main locator | Action methods |)
## Test cases (| Test | Scenario | Assertion |)  — FULL test functions, one scenario per function, NO shallow isDisplayed
## TestNG XML (GoToHomeTest is the first <test> block — app only)
## Missing ID Report  (| element | screen | current locator | description | — omit if everything has an id)
## Notes / risks / open questions
```

## Principles
- Layering: `screens` (no-assert) → `tests` (assert) → `regression/smoke` (compose). Feature starts from Home.
- The plan **lists** the sitemap screens/nodes to create — only `/qa:cook` writes them for real. The plan records the **correct expectation** (per spec) so `/qa:cook` keeps the test honest.
- After writing the file → print the plan path + platform + a 3-5 line summary for review before `/qa:cook`.
