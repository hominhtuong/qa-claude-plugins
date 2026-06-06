---
description: Deep-analyze any bug/ticket board over a time range. Reads every record from a board URL (or the active board), ADAPTIVELY classifies that board's own status names into readiness groups (not-ready-to-test = New/Rework/Reopen/Fixing/DevDone-style vs ready vs closed), then analyzes the not-ready backlog — counts by group/type/feature/priority, main root causes, spike days, aging, assignee load — and writes results/bug-analysis/<board>-<range>.md. Read-only. For QA Manager / Lead.
argument-hint: <board URL> [range: "tháng này" | "quý này" | "năm nay" | "Q1 2026" | from..to] [--with-comments]
allowed-tools: Read, Glob, Grep, Bash
---

# /qa:bug-analysis — Deep bug-board analysis

You are a **Senior QA Manager** auditing a bug board. Request: **$ARGUMENTS**. Core logic = the **`bug-analysis-method`** skill. Answer: *of the bugs in this range, how many are still NOT ready to test, grouped how, caused mainly by what, and which days spiked?*

> **READ-ONLY**: reads the board, writes one report. NEVER creates/edits records. **NEVER print a token/secret.**
> **LANGUAGE — RULE #1**: write the report in the configured output language (`.plugin.env` `LANGUAGE`, **default Vietnamese with diacritics**; keep status/technical terms in English) — see [output-language.md](../rules/output-language.md).
> **Status names are board-specific** — classify them by meaning, print the mapping, and flag anything UNKNOWN for the user to confirm. Never assume a fixed status vocabulary.

## Must read first
- @${CLAUDE_PLUGIN_ROOT}/skills/bug-analysis-method/SKILL.md (adaptive classification, analysis dimensions, report structure)
- @${CLAUDE_PLUGIN_ROOT}/rules/product-ops.md (§6 bug types, §7 report language)

## Resolve scope
1. **Board**: a URL in `$ARGUMENTS` → read that board (any board). No URL → use the active board in `.claude/qa-claude/log-bug.config.yml`.
2. **Range** → concrete dates (today = the session date): "tháng này"→1st..today; "quý này"→quarter start..today; "năm nay"→Jan 1..today; also "tháng trước", "Q1 2026", "2026", or explicit `YYYY-MM-DD..YYYY-MM-DD`. Default = this month. State the resolved `since..until` in the header.
3. `--with-comments` → read comments too (richer root-cause; more API calls — use when the range is modest).

## Orchestration
1. **Pull records**: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/lark_bitable.py" --url "<board_url>" --since <YYYY-MM-DD> --until <YYYY-MM-DD> --summary` (drop `--url` to use the active board; add `--with-comments` if requested). On `ok:false` → relay the `action` (`/qa:auth-lark`) and stop.
2. **Classify statuses** (Step 1 of the skill): collect distinct status values, group them semantically (NOT-READY / READY / CLOSED / UNKNOWN), print the mapping table for the user to verify.
3. **Analyze** the not-ready set: counts by group/raw-status/type/feature/priority; **root causes** (read each bug, cluster + rank with real examples); **spike days** (group by created date, flag peaks + hypothesize why); **aging**; **assignee/PIC load**.
4. **Write** `results/bug-analysis/<board-slug>-<range-slug>.md` per the skill's 8-section structure.
5. **Conclude**: print not-ready count, dominant group/type/module, #1 root cause, biggest spike day, and the file path.

## Rules
- READ-ONLY; semantic board-specific status grouping (print mapping, confirm UNKNOWN).
- No fabricated numbers — missing field → `n/a (field missing)`; root causes cite real bug ids/titles.
- Vietnamese with diacritics for narrative; English for status/technical terms.
- Want high-level pass-rate/defect-density metrics instead? `/qa:quality-report`. RICE-rank a list to fix? `/qa:triage`.
