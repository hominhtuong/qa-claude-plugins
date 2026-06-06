---
name: traceability-method
description: Reusable logic to build a Requirement Traceability Matrix (RTM) — link each requirement to its test cases and bugs, and surface coverage gaps. Reads the requirement checklist from the analyze-spec output (results/<feature>/*-docs-summary.md + the Functional Requirements section), the designed test cases (the feature xlsx / gen-testcases plan), and bugs from the Lark Bitable board (scripts/lark_bitable.py) → writes results/<feature>/traceability.md with a Requirement → TC_IDs → Bug_IDs → coverage-status table that flags Gap / No-test / Partial. Read-only. Closes the spec↔test↔bug loop. Reusable core behind the traceability command. For QA + QA Manager.
---

# Skill: traceability-method

Reusable capability: close the loop between **what was specified**, **what was tested**, and **what broke** — a Requirement Traceability Matrix that makes coverage gaps impossible to hide. Answers "which requirement has no test?" and "which requirement keeps producing bugs?".

> 🔗 **The matrix is the deliverable**: one row per requirement, columns Requirement → Test cases → Bugs → Coverage status. The value is the **Gap** and **No-test** rows it surfaces.

## Inputs (degrade gracefully — name what's missing, never invent links)
1. **Requirements** — the analyze-spec output for the feature: `results/<feature>/*-docs-summary.md` + the **Functional Requirements** checklist (section 3.1) and Business Rules (3.2). Each becomes a requirement row with a stable id (`REQ-01…`; reuse existing ids if the analysis already numbered them). No analysis present → tell the user to run `/qa:analyze-spec <feature>` first; do not fabricate requirements.
2. **Test cases** — the feature's `results/<feature>/*.xlsx` (gen-testcases output) and/or the plan (`plans/<feature>/plan.md`). Map each TC_ID to the requirement it exercises (by feature/section reference, then by title match).
3. **Bugs** — `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/lark_bitable.py" [--board <alias>]` filtered to the feature (the `feature` logical field). Map each bug to the requirement it violates. On board `ok:false` relay the `action` and continue without the bug column (flag it ⚠️).

## Procedure
1. **Scope**: `$ARGUMENTS` = a feature name (one RTM under `results/<feature>/`) or `all` (Glob every `results/*/` with an analysis → one combined matrix under `results/traceability/`).
2. **Extract requirements** from the analysis → numbered rows. **Extract test cases** → TC_IDs. **Extract bugs** for the feature.
3. **Link**: for each requirement, collect its TC_IDs and Bug_IDs. Matching order: explicit section/requirement reference in the TC/bug → title/keyword match → leave unlinked (better an honest Gap than a wrong link).
4. **Classify coverage** per requirement:
   - **Covered** — ≥1 test case, all passing / no open bug.
   - **Partial** — has test cases but also an open bug, or only some sub-conditions covered.
   - **Gap** — test cases exist but failing/insufficient, or open bug with weak coverage.
   - **No-test** — zero test cases mapped (the headline risk).
5. **Write** `results/<feature>/traceability.md` (or `results/traceability/matrix.md` for `all`) per the structure below. Bold/emoji the **No-test** and **Gap** rows.
6. **Conclude**: print the matrix path + coverage stats (X/Y requirements covered, N no-test, M partial) and the top untested requirements.

## Output structure (`traceability.md`)
1. **Header** — feature, sources used (analysis file, xlsx, board), generated date.
2. **Coverage summary** — counts: total requirements · Covered · Partial · Gap · No-test · coverage %.
3. **Matrix** — `| REQ ID | Requirement | Test cases (TC_ID) | Bugs | Coverage |` — one row per requirement, 🔴 No-test / 🟡 Partial|Gap / 🟢 Covered.
4. **Untested requirements** — the No-test rows pulled out as an action list for the QA owner.
5. **Orphans** — test cases or bugs that map to no requirement (possible spec gap or stale test).
6. **Notes** — ambiguous links + any unread source.

## Rules
- **READ-ONLY** — never create bugs/tests; never print tokens.
- **Honest links only** — an uncertain mapping stays unlinked and shows as a Gap; never invent a TC↔REQ link to look complete.
- **No-test rows are the point** — always surface them prominently; never bury a zero-coverage requirement.
- **LANGUAGE**: write the matrix in the configured output language (`.plugin.env` `LANGUAGE`, default Vietnamese with diacritics; keep ids/technical terms in English) — see `../../rules/output-language.md`.
- Requirement source = the `analyze-spec` output; this skill consumes it, it does not re-analyze the spec.
