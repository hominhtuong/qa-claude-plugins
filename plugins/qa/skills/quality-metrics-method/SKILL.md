---
name: quality-metrics-method
description: Reusable logic to aggregate QA quality metrics into a manager-facing report. Pulls test-run results from results/tests/, the shared bug register results/bug-summary.md, and live bug records from the Lark Bitable board (scripts/lark_bitable.py) → computes pass rate + trend, open bugs by severity/priority with aging, defect density, created-vs-resolved trend, coverage per feature → writes results/quality-report/<date>/report.md (+ optional HTML/notify/share). Read-only: never creates bugs or tests. Reusable core behind the quality-report command, also consumed by release-gate-method.
---

# Skill: quality-metrics-method

Reusable capability: turn the artifacts QA already produced (test runs + bug board) into a **QA-Manager dashboard** — a single report that answers "is quality trending up or down, and where are the hot spots?". **Read-only**: this skill aggregates, it never creates/edits bugs or tests.

> 🎯 **Audience = QA Manager / Lead**, not the IC running one suite. The output is decision-grade: trends, ratios, hot-spot modules — not a raw dump.

## Inputs (best-effort — degrade gracefully, never invent)
1. **Test runs** — `results/tests/<ddMMMyyyy>/…` HTML/JSON reports across dates → per-run pass/fail/skip counts + trend. Missing → report "no automation runs found in range" and continue with bug metrics only.
2. **Shared bug register** — `results/bug-summary.md` (the exploratory register) → bugs found this period not yet on the board.
3. **Live board** — `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/lark_bitable.py" --summary [--since <YYYY-MM-DD>] [--until <YYYY-MM-DD>]` → all records mapped to logical fields + `summary` tallies (by_status / by_priority / by_type / by_platform). On `ok:false` relay the `action` verbatim (run `/qa:auth-lark`) and continue with file-only metrics — clearly flag the board section as unavailable.
4. **Test cases** — feature xlsx + `results/<feature>/` analysis (from gen-testcases) → total designed vs executed for coverage.

## Metrics to compute
- **Pass rate** per run + **trend** across the date range (▲/▼ vs previous run); flakiness flag if a test flips fail↔pass.
- **Open bugs by Priority** (Critical/High/Medium/Low) + **aging** = days since `created_time` for still-open records (status not in the closed set). Call out any Critical/High aging beyond a threshold (default 7 days).
- **Defect density** = bugs per feature/module (group by the `feature` field); rank to surface **hot-spot modules**.
- **Created vs Resolved trend** over the period (inflow vs outflow) — is the backlog growing?
- **Bug type / platform split** (UI/UX vs Function vs Performance; App/Web/…).
- **Coverage per feature** = executed test cases / designed (when xlsx available); flag features with 0 automation.
- **Escape rate** — ONLY if the board distinguishes environment/found-stage (e.g. a "found in" field). If the board lacks that field, **omit escape rate** and note it as "not measurable with current board schema" — do NOT fake it.

> **Health thresholds**: classify each metric Healthy / Warning / Critical using the table in `../../rules/product-ops.md` §2 (escape rate, regression, open-critical, coverage, pass rate, hotfix rate). Cite the band in the report so the verdict is auditable.

## Procedure
1. **Resolve range**: from `$ARGUMENTS` (`from..to` dates or a release tag → its date window) else default to the last 30 days. State the resolved window in the report header.
2. **Gather in parallel**: spawn the `lark-reader`-style board read via `lark_bitable.py` AND read `results/tests/` + `results/bug-summary.md` concurrently. Read the board JSON; do NOT print tokens.
3. **Compute** the metrics above from the gathered data. Every number must trace to a source; if a metric's source is missing, mark it `n/a (source missing)` rather than guessing.
4. **Write** `results/quality-report/<date>/report.md` per the structure below (folder date = `ddMMMyyyy`). Render an HTML twin from `../../rules/report-template.html` if the user wants a shareable file.
5. **Optional delivery**: if the project enables it, notify (Lark/webhook via `lark_notify.py`/`notify_webhook.py`) and/or upload (`push_report.py`/`push_s3.py`) — same toggles as the rest of the plugin. Default = local file only.
6. **Conclude**: print the report path + a 5-line executive summary (overall health verdict, top hot-spot, biggest risk, trend direction).

## Report structure (`report.md`)
1. **Header** — period window, board name, generated date, data sources used (✅/⚠️ missing).
2. **Executive summary** — 4-6 bullets: health verdict, pass-rate trend, open-Critical count, top hot-spot module, backlog direction.
3. **Test execution** — table per run: `| Date | Total | Pass | Fail | Skip | Pass% | Δ |` + trend note.
4. **Defects — current state** — open by Priority (table) + aging callouts (oldest open Critical/High).
5. **Defects — trend** — created vs resolved per sub-period; backlog delta.
6. **Hot-spot modules** — `| Feature | Open bugs | Density | Note |` ranked.
7. **Coverage** — `| Feature | Designed TC | Executed | Coverage% | Automated? |` (omit if no testcase data).
8. **Risks & recommendations** — 3-5 concrete actions for the lead (where to focus next sprint).

## Rules
- **READ-ONLY** — never create/edit bug records or tests. Never print tokens/secrets.
- **No fabricated numbers** — a missing source → `n/a (source missing)`, not a guess. Escape rate omitted unless the board schema supports it.
- **LANGUAGE**: write the report in the configured output language (`.plugin.env` `LANGUAGE`, default Vietnamese with diacritics; keep metric/technical terms in English) — see `../../rules/output-language.md`.
- Closed-status set is configurable; default treat `Done/Closed/Resolved/Verified/Rejected` as closed, everything else as open.
- This skill's metrics output (the JSON-able numbers) is reused by `release-gate-method` — keep the open-bug-by-priority + pass-rate computation consistent.
