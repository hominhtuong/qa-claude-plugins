---
name: triage-method
description: Reusable logic to triage a list of bugs/incidents — classify Severity (P1–P4) + Type, score each by RICE for objective prioritization, derive SLA deadlines, analyze cross-feature impact + regression scope from the sitemap, and emit an ordered action plan. Reads bugs from a sheet/file/pasted text or the Lark Bitable board (scripts/lark_bitable.py), writes results/<context>/triage-report-<date>.md sorted by RICE. Reusable core behind the triage command. For QA/PS Lead / Manager.
---

# Skill: triage-method

Reusable capability: take a pile of bugs/incidents and produce a **defensible processing order** — severity + type classification, RICE-scored ranking, SLA deadlines, and the regression scope each fix implies.

> 🎯 **RICE drives the order.** Don't give every bug the same priority — the score must differentiate. Auto-classify severity but flag it for user confirmation; never silently override a user-given level.

## Inputs (any one)
1. **Lark Bitable board** (the reliable path) — `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/lark_bitable.py" [--status Open,...]` (add `--url "<board_url>"` for an arbitrary board). On `ok:false` relay the `action` (`/qa:auth-lark`).
2. **Google Sheet link** — only if the project has the `google-sheets` MCP configured (find `mcp__google-sheets__*` via ToolSearch); read the list, auto-detect columns. **Lark Sheet** has no Python reader in this plugin → ask the user to export it to `.xlsx/.csv`, or point at the Bitable board instead.
3. **Local file** (.xlsx/.csv) — read via the Read tool / python — or **pasted text** (single bug or batch).
4. **Sitemap (optional)** — `sitemap/sitemap.json` for impact + regression scope.
- Columns to auto-detect from any source: id, title, description, severity, status, reporter, date, affected users; ambiguous → ask.

## Procedure
1. **Read** `../../rules/product-ops.md` (§4 RICE, §1 SLA, §6 types) + `../../rules/severity-priority-framework.md` (normalize labels → P1–P4; unmappable → `Unknown` + count). Resolve context name (else `ops-<YYYY-MM-DD>`).
2. **Parse & classify** each bug: Severity (P1–P4 from description, flag for confirm) + Type (FUNC/UI/PERF/DATA/SEC/INT/REG).
3. **RICE** each: `(Reach × Impact × Confidence) / Effort`. State the four inputs per bug.
4. **Impact analysis** (from sitemap): which feature/page is hit → cross-feature impacts → regression scope (what to retest). Bugs hitting multiple features rank higher.
5. **SLA deadline** per severity (P1 15m/4h · P2 1h/24h · P3 4h/72h · P4 24h/1wk — or the board's override).
6. **Write** `results/<context>/triage-report-<date>.md` sorted by RICE, per the structure below.
7. **Conclude**: print the top-5 by RICE + counts by severity + the file path.

## Report structure
1. **Overview** — total + counts by P1/P2/P3/P4.
2. **Processing order (sorted by RICE)** — `| # | Bug ID | Title | Severity | RICE | Type | SLA | Impact scope |`.
3. **Per-bug detail** — severity, type, RICE breakdown (Reach/Impact/Confidence/Effort), affected feature, cross-feature impact, regression scope, SLA, recommendation.
4. **By type** — count + % per type.
5. **Impact map** — bugs per feature; cross-feature count.
6. **Action plan** — Immediate (P1) / 24h (P2) / this sprint (P3) / backlog (P4).

## Rules
- **RICE must differentiate** — never equal-priority everything.
- Don't change a user-given severity without explanation; auto-classified severity is flagged for confirmation.
- Never skip impact analysis or regression scope — a fix without its retest scope is incomplete.
- **LANGUAGE**: write the report in the configured output language (default Vietnamese with diacritics; technical terms in English) — see `../../rules/output-language.md`.
- Read-only — classifies and ranks; does not create/edit bug records. Logging is `/qa:log-bug`.
