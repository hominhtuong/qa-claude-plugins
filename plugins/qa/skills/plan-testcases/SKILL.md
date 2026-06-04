---
name: plan-testcases
description: Split 1 feature into independent PHASES for writing test cases in parallel. Assign a TC_ID range per phase, decide the output type (Test Case vs Checklist vs Regression), estimate time (~min/TC by complexity + 20% buffer) and story points (Fibonacci). Ensure phases don't overlap so merging is conflict-free. Used by the plan-tests command and cook (when the output is large and needs phasing).
---

# Skill: plan-testcases

A reusable capability to **plan tests** — split a feature into independent phases, assign TC_ID ranges, choose output types, estimate effort. The output is detailed enough for the `cook` command to execute immediately without re-asking.

> **LANGUAGE — RULE #1**: Generate the content in Vietnamese (with diacritics). Keep technical terms in English. Applies to sub-agents too.

## Procedure

1. **Aggregate input**: read all summaries (docs/Figma), analysis (if any from `/qa:analyze`), existing plans in `plans/` to avoid duplication. Determine the scope: in-scope (functions/screens/flows to test), out-of-scope (explicit), assumptions.
2. **Feature breakdown**: split the feature into small modules/sections. Each section notes: function description, business rule, main UI component, validation rule, state to verify, integration point.
3. **Split into independent PHASES** (core principle):
   - Each phase = a group of **FULLY INDEPENDENT** features — no shared data, no overlapping scope. Phase 1 is unrelated to Phase 2.
   - When merging results: no conflicts, nothing missing/duplicated.
   - Dependencies between features => put them in the SAME phase.
   - Small feature (<= 40 TCs) => may be a single phase.
4. **Assign TC_ID range + sheet name** per phase (table):

   | Phase | Module/Section | TC_ID Range | Est. TCs | Sheet Name |
   |-------|----------------|-------------|----------|------------|
   | 1 | [Module A, B] | TC_001-TC_025 | ~25 | [module-name] |
   | 2 | [Module C, D] | TC_026-TC_045 | ~20 | [module-name] |

   > Note: TC_ID **resets per sheet** on export (the range above is only for estimation, not a continuous count across independent sheets).
5. **Decide the output type** per part:
   - **Test Case** (`TC_xxx`): new/changed feature needing detailed per-scenario verification.
   - **Checklist** (`CL_xxx`): items to tick off quickly, few steps (smoke, sanity, UI quick check).
   - **Regression** (`RT_xxx`): aggregate flows re-run after each release to catch regressions.
6. **Test Case Matrix** — estimate the TC count per section by coverage type:

   | Section | Phase | Positive | Negative | Boundary | Edge | Total | Priority |
   |---------|-------|----------|----------|----------|------|-------|----------|

7. **Estimate time** (per [output-format §5](../../rules/output-format.md)): Simple 2 min/TC · Medium 3 min/TC · Complex 4-5 min/TC · Mixed default 3 min/TC; **+20% buffer**. Report: time to write TCs, execute 1 round, regression (if any).
8. **Estimate Story Points**: based on TC count, complexity, scope, risk. Round to the Fibonacci scale (1, 2, 3, 5, 8, 13, 21). Apply a role multiplier if the project configures USER_ROLE (junior x1.5, mid x1.2, senior/lead x1.0; default senior x1.0).
9. **Risk Assessment**: the most bug-prone area (analyze real reasons, not generic), integration risk, mitigation, areas needing test focus.
10. **Export the plan** to `plans/<feature>/<prefix>.md` (overall) + per-phase file/section + PLAN STATUS markers (`COMPLETED`/`PENDING`/`IN_PROGRESS`) for `cook` to read and run multi-phase.

> This skill **only plans**, it does not write TC content (that's skill `gen-testcases`) and does not build the file (skill `tc-template`).
