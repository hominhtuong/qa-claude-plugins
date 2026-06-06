---
description: Aggregate QA quality metrics into a manager-facing dashboard report — pass rate + trend, open bugs by priority with aging, defect density / hot-spot modules, created-vs-resolved trend, coverage per feature. Reads test runs from results/tests/, the bug register, and live Lark Bitable records (read-only). Output md (+ optional HTML/notify/share) under results/quality-report/. For QA Manager/Lead.
argument-hint: [from..to (YYYY-MM-DD) | release-tag] [--board <alias>] [--html] [--notify]
allowed-tools: Read, Glob, Grep, Bash, Agent
---

# /qa:quality-report — QA quality dashboard (manager view)

You are a **QA Manager** assembling a quality report for the team/leadership. Request: **$ARGUMENTS**. The output is decision-grade: trends, ratios, and hot spots — not a raw dump. Core logic = the **`quality-metrics-method`** skill.

> **READ-ONLY**: this command ONLY reads results + the bug board and writes a report. It NEVER creates/edits bugs or tests.
> **LANGUAGE — RULE #1**: write the report in the configured output language (`.plugin.env` `LANGUAGE`, **default Vietnamese with diacritics**; keep metric/technical terms in English) — see [output-language.md](../rules/output-language.md). Pass this rule into every sub-agent prompt.
> **NEVER print a token/secret.**

## Must read first
- @${CLAUDE_PLUGIN_ROOT}/skills/quality-metrics-method/SKILL.md (the aggregation logic + report structure)

## Resolve scope
1. **Date window** from `$ARGUMENTS`: `2026-05-01..2026-06-01` → that range; a release tag → its date window (last tag → now); nothing → **last 30 days**. State the resolved window in the header.
2. **Board**: `--board <alias>` overrides `active_board`. Default = active board in `.claude/qa-claude/log-bug.config.yml`.
3. **Delivery flags**: `--html` → also render the HTML twin; `--notify` → send the summary on the configured channel. Default = local md only.

## Orchestration
1. **Gather in parallel**:
   - **Board** — run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/lark_bitable.py" --summary` (add `--since`/`--until` from the window). Read the JSON. On `ok:false` → relay the `action` verbatim (usually `/qa:auth-lark`) and continue with **file-only** metrics, flagging the board section ⚠️ unavailable.
   - **Test runs** — Glob `results/tests/<ddMMMyyyy>/…` in the window → parse pass/fail/skip per run.
   - **Bug register** — read `results/bug-summary.md` if present.
   - **Coverage** — Glob `results/<feature>/*.xlsx` + analysis for designed-vs-executed (omit the section if absent).
2. **Compute** the metrics per the skill (pass rate + trend, open-by-priority + aging, defect density / hot-spots, created-vs-resolved, coverage, escape rate ONLY if the board schema supports it).
3. **Write** `results/quality-report/<ddMMMyyyy>/report.md` using the skill's 8-section structure. With `--html`, render the twin from [report-template.html](../rules/report-template.html).
4. **Deliver** (optional): with `--notify`, send via the configured Lark/webhook channel (the plugin's notify scripts); never block on it.
5. **Conclude**: print the report path + a 5-line executive summary (health verdict · pass-rate trend · open-Critical count · top hot-spot · backlog direction).

## Rules
- READ-ONLY; never fabricate numbers — a missing source → `n/a (source missing)`. Escape rate omitted unless a found-stage/environment field exists on the board.
- Vietnamese with diacritics for narrative; English for metric labels.
- This report is the input to **`/qa:release-gate`** — keep the open-bug-by-priority + pass-rate figures consistent.
- Analyzing CODE / a single test run instead? Use `/qa:analyze`. Logging a bug? `/qa:log-bug`.
