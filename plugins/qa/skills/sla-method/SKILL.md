---
name: sla-method
description: Reusable logic to evaluate SLA compliance from ticket/bug data and emit a period report (sprint/month/quarter). Normalizes priority labels to P1–P4, computes SLA compliance rate (overall + per priority), MTTR-Response & MTTR-Resolution with P50/P90/P95 percentiles, breach analysis, trend vs previous period, and assignee performance. Reads a sheet/file/pasted data or the Lark Bitable board (scripts/lark_bitable.py), writes results/<context>/sla-report-<period>.md. Reusable core behind the sla command. For Product Ops.
---

# Skill: sla-method

Reusable capability: turn raw ticket/bug timestamps into an **SLA compliance report** — are we hitting response/resolution targets, where are we breaching, and is it getting better or worse?

> 🎯 **Audience = Product Ops.** Base every number on actual data; use percentiles (P50/P90/P95), not just averages; highlight critical (P1/P2) breaches. Never fabricate values.

## Inputs (any one)
1. **Lark Bitable board** (the reliable path) — `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/lark_bitable.py"` (add `--url "<board_url>"` for an arbitrary board) → records with created/modified timestamps + priority + status. On `ok:false` relay the `action`.
2. **Google Sheet link** — only if the project has the `google-sheets` MCP configured (`mcp__google-sheets__*` via ToolSearch); auto-detect columns by header. **Lark Sheet** has no Python reader here → ask the user to export to `.xlsx/.csv`, or use the Bitable board.
3. **Local file** (.xlsx/.csv/.json) — Read tool / python — or **pasted data**.

> Ticket timestamps are the key data: a board carries `created_time`/`last_modified_time` automatically; a sheet/file must include explicit created / first-response / resolved columns (resolution time can't be computed without them).

### Required vs optional columns
Required: **Ticket ID**, **Priority/Severity**, **Created date**. Optional (enrich when present):
First-response date, Resolved date, Status, Assignee. Missing/ambiguous required column → ask the user to map it.

## Procedure
1. **Read** `../../rules/product-ops.md` (§1 SLA targets + synonym mapping) + `../../rules/severity-priority-framework.md`. Resolve the period + context name (else `ops-<YYYY-MM-DD>`).
2. **Parse & normalize**: labels → P1–P4 (unmappable → `Unknown` + report count). Validate timestamps.
3. **Compute** (overall + per priority):
   - **SLA compliance rate** = resolved-within-SLA / total × 100% (target ≥ 95%).
   - **MTTR-Response** & **MTTR-Resolution** averages + **P50/P90/P95**.
   - **Breach analysis** — count + % breaching; top breaches (longest overdue).
   - **Trend** vs previous period (if historical data) — Improving / Stable / Degrading.
   - **Assignee performance** (if assignee present) — compliance + avg resolution per person.
4. **SLA targets** = defaults from product-ops §1 unless the user overrides.
5. **Write** `results/<context>/sla-report-<period>.md` per the structure below.
6. **Conclude**: print overall compliance rate, P1/P2 breach count, trend, and the file path.

## Report structure
1. **Overview** — total tickets, overall compliance %, MTTR-Response, MTTR-Resolution, breaches (count + %).
2. **Per priority** — `| Priority | Total | In SLA | Breached | Compliance | Avg Response | Avg Resolution |`.
3. **Percentiles** — `| Priority | P50/P90/P95 Response | P50/P90/P95 Resolution |`.
4. **Top breaches** — `| Ticket | Priority | Overdue by | Assignee | Note |`.
5. **Assignee performance** (if available).
6. **Trend** (if historical) — vs previous period + verdict.
7. **Recommendations** — concrete action items grounded in the data.

## Rules
- **Actual data only** — never fabricate or assume values not in the input.
- Use percentiles, not just averages; don't ignore outliers (they reveal systemic issues).
- Unmappable priority → `Unknown` bucket + report the count; ask to normalize the source.
- **LANGUAGE**: write the report in the configured output language (default Vietnamese with diacritics; technical terms in English) — see `../../rules/output-language.md`.
- Read-only — produces a report; does not modify tickets.
