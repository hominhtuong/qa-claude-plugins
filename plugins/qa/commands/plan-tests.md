---
description: Design a test plan — auto-detects mode → AUTOMATION runs an exploratory gate then writes plans/<feature>/plan.md to implement tests (routes by platform), or MANUAL builds a multi-phase test-case plan for /cook
argument-hint: <feature-name> [web|android|ios] [spec/PRD/Figma link | requirement] [--auto|--manual]
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, WebSearch, Agent
---

# /plan-tests — Test planning (mode router)

User request: **$ARGUMENTS**

## Step 0 — Detect mode
Run **skill `detect-mode`** → `automation` | `manual`. Read ONLY the matching section below. (The name `/plan-tests` distinguishes it from plan-release/plan-sprint.)

---

# Mode: automation — plan to implement tests

Goal: create a **solid plan (.md file)** describing how to implement the tests. `/cook` executes it afterward. **Do NOT write code** at this step.

> 🚦 **GATE — exploratory first, plan after**: *Automation only works when the app is correct.* A feature with `[APP-BUG]` → **do NOT make a test plan**, the deliverable is a bug report for dev. Only a **clean** exploratory leads to a plan.

## Step A0 — Lock platform (routing)
Run **skill `detect-platform`** → one `platform`. It decides which design-pattern rules to read in Step A2.

## Step A1 — EXPLORATORY GATE (before anything)
1. Is there a recent bug report yet? `reports/exploratory/<group>/dev-bug-report-*.md` + `bug-summary.md`. None/stale/changed → run **`/exploratory <feature-name> <platform>`**.
2. Read the result:
   - 🔴 **Has `[APP-BUG]`** → **STOP planning** for that part; print "Feature NOT complete — N app bugs, see `dev-bug-report-*.md`". Do NOT create `plans/<feature>/plan.md`.
   - 🟢 **No `[APP-BUG]`** → app correct → continue to Step A2. Elements extracted during exploratory are used for Layer 1/2.
3. Large feature → **gate per sub-feature** (plan the clean parts, report bugs for the broken parts).

## Step A2 — Design the plan — skill `plan-method` (agnostic) + platform rules
Read **skill `plan-method`** (plan structure + layering principles + element 3-layer lookup) and the **design-pattern rules per `platform`** (only 1 branch):
- **web** → `rules/web/design-pattern.md` · `coding-rules.md` · `design-system.md`.
- **android | ios** → `rules/app/design-pattern.md` · `coding-rules.md` · `design-system.md`.

Also read the project's `@CLAUDE.md` + sitemap/test-hints if present. If the request has a Lark/Figma link → spawn a reader agent (`agent-lark-reader`/`agent-figma-reader`, 1 agent/URL, max 5/batch, append to `plans/<feature>/tracking.md`; details in [lark-mcp-guide.md](../rules/lark-mcp-guide.md)).

## Step A3 — Write the plan to `plans/<feature>/plan.md` (lowercase-hyphen; update if it exists)
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

## Principles (automation)
- Layering: `screens` (no-assert) → `tests` (assert) → `regression/smoke` (compose). Feature starts from Home.
- The plan **lists** the sitemap screens/nodes to create — only `/cook` writes them for real. The plan records the **correct expectation** (per spec) so `/cook` keeps the test honest.
- After writing the file → print the plan path + platform + a 3-5 line summary for review before `/cook`.

---

# Mode: manual — build a multi-phase test-case plan

You are a **Senior QA Lead**. Goal: create a detailed test plan that any QC can use as direct input for `/cook` (manual mode) without asking further questions.

> **LANGUAGE — RULE #1**: Generate the plan content in Vietnamese (with diacritics). Keep technical terms in English. When spawning a sub-agent, the agent prompt MUST repeat this rule.

## Must read first
- Skill `plan-testcases` (phase-splitting / estimation engine)
- @${CLAUDE_PLUGIN_ROOT}/rules/output-format.md (time estimation, naming)

## Gathering information (MUST ask sequentially if missing)
1. Feature / module / sprint to test?
2. Spec/PRD/BRD/ticket link (Google Docs / Lark wiki / Notion / Jira...)?
3. Figma link (if there's UI)?
4. Platform: iOS / Android / Web / All?
5. What is OUT OF SCOPE?
6. Deadline / timeline?
7. Dependency / integration with other modules?

Determine the **output folder + prefix**: `plans/<feature-name>/` (kebab-case, lowercase, no diacritics); prefix = feature abbreviation.

## Orchestration — gather data + build the plan
1. **Check existing summary** (`{output}/{prefix}-docs-summary.md`, `{prefix}-figma-summary-*.md`): if present (same day) → ask the user to reuse or re-read.
2. **Determine agents + Figma batch**: has a doc → 1 Docs reader agent. Has Figma → `get_metadata` to count screens, each agent ≤ 7 screens (8-14 → 2 agents, 15-21 → 3 agents). **Total ≤ 5 agents**. User pastes text directly → skip orchestration.
3. **Launch agents in PARALLEL** (same response, max 5). Every sub-agent prompt MUST include the line: "CRITICAL: All Vietnamese content MUST have diacritics. Output without diacritics is WRONG."
4. **WAIT** for all agents to finish (MANDATORY SYNC) → read all summaries + the analysis from `/analyze` (manual mode, if any) + existing plans in `plans/` (avoid duplication).

## Test Plan structure (use skill `plan-testcases`)
The plan MUST contain all of these sections:
1. **General Info**: feature name, DOC link, Figma link, platform, creation date, specs version.
2. **Test Scope**: in-scope (detail each function/screen/flow), out-of-scope (explicit), assumptions.
3. **Feature Breakdown**: split into modules/sections, each section noting function, business rule, UI component, validation rule, state, integration point.
4. **Test Strategy**: test level, test type (functional/UI-UX/API/performance/security/compatibility as applicable), approach (manual/auto/hybrid).
5. **Phase Division** (MANDATORY if > 1 phase): each phase = a group of **FULLY INDEPENDENT** features (no shared data, no overlap). Table: Phase | Module | TC_ID Range | Est. TCs | Sheet Name. Small feature (≤ 40 TCs) → 1 phase.
6. **Test Case Matrix**: table Section | Phase | Positive | Negative | Boundary | Edge | Total | Priority + describe the main scenario of each section.
7. **Test Data Requirements**: account, sample data, config, shared precondition, environment.
8. **Risk Assessment**: bug-prone areas (real reasons, not generic), integration risk, mitigation, areas needing focus.
9. **Time Estimation**: expected TC count, time to write TCs + execute 1 round + regression (formula [output-format §5](${CLAUDE_PLUGIN_ROOT}/rules/output-format.md)).
10. **Story Point**: Fibonacci (1·2·3·5·8·13·21) + role if the project configures it.
11. **Entry / Exit Criteria**.
12. **Deliverables**: checklist (this plan, TC sheet from `/cook`, bug report, execution report).

## Output (manual)
- File `plans/<feature-name>/<prefix>.md` (overall) + per-phase file/section + a `<!-- PLAN STATUS -->` block at the top (PENDING/IN_PROGRESS/COMPLETED marker + TC_ID range per phase) for `/cook` (manual mode) to read.
- Directory lowercase-hyphen, auto-create if missing.
- After writing the file → print the path + a 3-5 line summary for the user to review before `/cook`. If the session is already long/has many docs → suggest `/clear` or `/compact` before `/cook`.
