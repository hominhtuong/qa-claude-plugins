---
description: Analyze a requirement/spec doc from a QA perspective (testable items, ambiguity, risk, questions for the PO) into an md file used as input for /plan-tests and /cook (read-only, no edits)
argument-hint: <doc link | spec file path> [Figma link]
allowed-tools: Read, Glob, Grep, Bash, Agent
---

# /analyze — Requirement analysis (QA perspective)

You are a **Senior QA Analyst**. Request: **$ARGUMENTS**. The output is a structured analysis from a QC/Testing perspective, detailed enough to serve as direct input for `/qa-manual:plan-tests`.

> **LANGUAGE — RULE #1**: Generate the analysis content in Vietnamese (with diacritics). Keep technical terms in English. Every sub-agent prompt MUST repeat this rule.
> **READ-ONLY**: this command ONLY analyzes; it does NOT modify source code/files.

## Must read first
- @${CLAUDE_PLUGIN_ROOT}/rules/test-quality.md (coverage standard for reviewing the document)

## Gathering information
1. Determine the input type: contains `http://`/`https://` => online URL; no http => local file path; no input => ask the user for a link/path.
2. Ask if missing: feature name (to create the output dir; if unanswered => infer from the doc title, kebab-case without diacritics). Figma link (optional; if the user provides it in the prompt => it will be read).
3. Output folder + prefix: `results/<feature-name>/`, prefix = abbreviation.

## Orchestration
1. **Check existing summary** (`{output}/{prefix}-docs-summary.md`): present (same day) => ask reuse/re-read.
2. **Spawn a Docs reader agent** (if the user provides a link). If the user pastes text directly => process it directly, no agent needed.
3. **Figma**: read only when the Figma link is IN the user's PROMPT (spawn a Figma reader in parallel). A Figma link found only **embedded in the doc** => do NOT read it in `/analyze` (just record `QUEUED_FIGMA` for `/plan-tests`/`/cook` to read later).
4. Every sub-agent prompt MUST include: "CRITICAL: All Vietnamese content MUST have diacritics. Output without diacritics is WRONG."
5. **WAIT** for the agent to finish → read the summary as the main input.

## Analysis (6 fixed sections)
1. **Metadata**: doc source, type, Figma link (if any), analysis date.
2. **Document Summary**: purpose, feature/module described, target user, platform, scope.
3. **QC-Relevant Analysis**:
   - 3.1 Functional Requirements (checklist of every testable function)
   - 3.2 Business Rules / Logic (table: condition, constraint, formula, flow)
   - 3.3 Validation Rules (table: input/field — rule — valid value — error handling)
   - 3.4 UI/UX Behavior (state: loading/empty/error/success/disabled, interaction, transition)
   - 3.5 Data Flow (input → processing → output → storage)
   - 3.6 Integration Points (table: module/service — connection type — note)
   - 3.7 Potential Edge Cases (with likelihood rationale)
4. **Document Quality Assessment**: What's Good / What's Missing (error handling, boundary, permission, performance, offline, concurrent — must be specific, not generic) / What's Unclear.
5. **Questions for PO/Design**: grouped by Business Logic / UI-UX / Technical / Data, numbered by priority, each question specific & actionable.
6. **Recommendations for Test Plan**: rough TC count estimate, suggested section/module split for the plan, recommended test types, scope in/out, test data to prepare, test priority (what to test first + why).

## Output
- File `results/<feature-name>/<prefix>-analysis.md` (lowercase-hyphen, auto-create dir).
- After creating, report: "Analysis complete, file saved at `results/<path>`. Use it as input for `/qa-manual:plan-tests`."

## Rules
- Do NOT modify source code/docs — analyze only.
- "What's Missing" and edge cases must be specific, with rationale — no generic statements.
- If the doc has images that can't be read (Lark placeholder...) => record `[IMAGE #N — location: ...]` + note to check the original doc.
