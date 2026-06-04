---
description: Build a multi-phase MANUAL TEST-CASE plan (scope, screens, phases, TC_ID range) → plans/<feature>/<prefix>.md + per-phase files, detailed enough for /qa:gen-testcases to run
argument-hint: <feature-name> [spec/PRD/Figma link | requirement description]
allowed-tools: Read, Glob, Grep, Edit, Write, Bash, Agent
---

# /qa:plan-gen-testcases — Test-case planning (manual)

You are a **Senior QA Lead**. Request: **$ARGUMENTS**. Goal: create a detailed test plan that any QC can use as direct input for `/qa:gen-testcases` without asking further questions.

> Planning AUTOMATION tests (write code) instead? Use **`/qa:plan-tests`**.

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
4. **WAIT** for all agents to finish (MANDATORY SYNC) → read all summaries + the analysis from `/qa:analyze-spec` (if any) + existing plans in `plans/` (avoid duplication).

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
12. **Deliverables**: checklist (this plan, TC sheet from `/qa:gen-testcases`, bug report, execution report).

## Output
- File `plans/<feature-name>/<prefix>.md` (overall) + per-phase file/section + a `<!-- PLAN STATUS -->` block at the top (PENDING/IN_PROGRESS/COMPLETED marker + TC_ID range per phase) for `/qa:gen-testcases` to read.
- Directory lowercase-hyphen, auto-create if missing.
- After writing the file → print the path + a 3-5 line summary for the user to review before `/qa:gen-testcases`. If the session is already long/has many docs → suggest `/clear` or `/compact` before `/qa:gen-testcases`.
