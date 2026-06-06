---
description: Build a Requirement Traceability Matrix (RTM) — link each requirement to its test cases and bugs, then surface coverage gaps (Gap / No-test / Partial / Covered). Reads the analyze-spec output (requirements), the feature xlsx / plan (test cases), and the Lark board (bugs) — read-only. Writes results/<feature>/traceability.md. Closes the spec↔test↔bug loop. For QA + QA Manager.
argument-hint: <feature name | all> [--board <alias>]
allowed-tools: Read, Glob, Grep, Bash, Agent
---

# /qa:traceability — Requirement Traceability Matrix

You are a **Senior QA** closing the loop between spec, tests, and bugs. Request: **$ARGUMENTS**. Core logic = the **`traceability-method`** skill. The deliverable is a matrix whose value is the **No-test** and **Gap** rows it exposes.

> **READ-ONLY**: reads analysis + test cases + the bug board, writes a matrix. NEVER creates/edits bugs or tests. **NEVER print a token/secret.**
> **LANGUAGE — RULE #1**: write the matrix in the configured output language (`.plugin.env` `LANGUAGE`, **default Vietnamese with diacritics**; keep ids/technical terms in English) — see [output-language.md](../rules/output-language.md).
> **Honest links only**: an uncertain TC↔requirement mapping stays unlinked (shown as a Gap) — never invent a link to look complete.

## Must read first
- @${CLAUDE_PLUGIN_ROOT}/skills/traceability-method/SKILL.md (extraction, linking, coverage classes, structure)

## Resolve scope
1. **Feature** = `$ARGUMENTS`: a name → one RTM under `results/<feature>/`; `all` → combined matrix under `results/traceability/`.
2. **Requirements source** = the analyze-spec output `results/<feature>/*-docs-summary.md` (+ the Functional Requirements / Business Rules sections). Missing → tell the user to run `/qa:analyze-spec <feature>` first, then stop. Do NOT fabricate requirements.
3. **Board**: `--board <alias>` overrides `active_board`.

## Orchestration
1. **Extract requirements** from the analysis → numbered `REQ-NN` rows (reuse existing numbering if present).
2. **Gather in parallel**:
   - **Test cases** — Glob `results/<feature>/*.xlsx` + `plans/<feature>/plan.md` → TC_IDs.
   - **Bugs** — `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/lark_bitable.py" [--board <alias>]` filtered to the feature field. On `ok:false` → relay the `action` (`/qa:auth-lark`), continue without the bug column (flag ⚠️).
3. **Link** each requirement → TC_IDs + Bug_IDs (explicit reference → title/keyword match → leave unlinked).
4. **Classify** each requirement Covered / Partial / Gap / No-test.
5. **Write** `results/<feature>/traceability.md` (or `results/traceability/matrix.md` for `all`) per the skill's structure (summary, matrix, untested list, orphans, notes).
6. **Conclude**: print the matrix path + coverage stats (X/Y covered, N no-test, M partial) + the top untested requirements.

## Rules
- READ-ONLY; honest links only (uncertain ⇒ Gap, never invented).
- Always surface No-test rows prominently — never bury a zero-coverage requirement.
- Vietnamese with diacritics for narrative; English for ids/technical terms.
- Requirements come from `/qa:analyze-spec`; this command consumes that output, it does not re-analyze the spec.
