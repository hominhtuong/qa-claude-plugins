---
name: bug-analysis-method
description: Reusable logic to deep-analyze a bug/ticket board (ANY board by URL) over a time range. Reads every record via scripts/lark_bitable.py --url (range-filtered by created_time), ADAPTIVELY classifies the board's own status names into readiness groups (not-ready-to-test = New/Rework/Reopen/Fixing/DevDone-style vs ready-to-test vs closed) since each board names them differently, then analyzes: count of not-ready bugs by group/type/feature/priority, main root causes, spike days (abnormal creation peaks), aging, and assignee load. Writes results/bug-analysis/<board>-<range>.md. Read-only. Reusable core behind the bug-analysis command.
---

# Skill: bug-analysis-method

Reusable capability: point at **any** bug board + a time range and get a detailed analysis of the **not-ready-to-test backlog** — how many, in which groups, why (root causes), and when they spiked. The hard part is that every board names its statuses differently, so the classification is **semantic, not hardcoded**.

> 🎯 The headline question: *"Of the bugs in this range, how many are still NOT ready to test, grouped how, caused mainly by what, and which days spiked?"*

## Inputs
1. **Board** — a URL (any board) → `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/lark_bitable.py" --url "<board_url>" --since <YYYY-MM-DD> --until <YYYY-MM-DD>`. No URL → fall back to the active board (omit `--url`). On `ok:false` relay the `action` (`/qa:auth-lark`) and stop.
2. **Range** — natural language → concrete dates (today = the session date): "tháng này"→1st..today of this month; "quý này"→quarter start..today; "năm nay"→Jan 1..today; "tháng trước"/"Q1"/"2026" similarly. State the resolved `since..until` in the report.

## Step 1 — Adaptive status classification (CRITICAL)
1. From the records, collect the **distinct values of the status field** (run with `--summary` to get `by_status`, or read the status-like field from the records — on a foreign board the field may not map to the logical `status` key, so inspect the actual field names/values).
2. **Classify each distinct status into a group by meaning**, not by a fixed list:
   - **NOT-READY-TO-TEST** — the bug is open and cannot be verified yet: e.g. `New`, `Open`, `Reopen/Reopened`, `Rework`, `Fixing/In Progress/Developing`, `DevDone` (fixed on the dev's machine, nobody has verified), `Waiting for fix`, `Backlog`, `Pending`.
   - **READY-TO-TEST / VERIFYING** — handed to QA: e.g. `Ready to test`, `R4Test`, `Testing`, `Retest`, `On stg/dev for test`.
   - **CLOSED / DONE** — resolved & no longer actionable: `Done`, `Closed`, `Resolved`, `Verified`, `Rejected`, `Won't fix`, `Cancel`.
   - **UNKNOWN** — anything you cannot confidently place → list it, ask the user to confirm its group; do NOT silently force it.
3. **Print the mapping table** in the report (board status → group) so the user can verify/correct it — board-specific naming means the user is the source of truth.

## Step 2 — Analyze the NOT-READY-TO-TEST set
Filter to the not-ready group within the range, then compute (as detailed as the data allows):
- **Totals**: total bugs/tickets in range; how many not-ready vs ready vs closed.
- **By status group** and by raw status (counts + %).
- **By bug type** (FUNC/UI/PERF/DATA/SEC/INT/REG — infer from type field or description) — which category dominates.
- **By feature/module** — hot-spot modules (ranked).
- **By priority/severity** — how many high/critical still not ready.
- **Root-cause analysis** — read each bug (name + description + comments when `--with-comments` is worth it) and cluster the **main causes** (e.g. validation gap, regression from release X, integration/API, data/migration, spec ambiguity). Rank causes by frequency; name concrete examples.
- **Spike days** — group by `created_time` date; flag days whose count is abnormally high (e.g. > mean + 1·σ, or clearly above the daily baseline) and hypothesize why (a release, a regression batch, a big feature).
- **Aging** — oldest not-ready bugs (days since created); flag stale high-priority ones.
- **Assignee/Dev PIC load** (if present) — who has the most not-ready bugs.

## Step 3 — Write the report
`results/bug-analysis/<board-slug>-<range-slug>.md` (slugs lowercase-hyphen; board-slug from the board name/alias or `board`). Structure:
1. **Header** — board, resolved range (`since..until`), generated date, totals, data caveats.
2. **Status → group mapping** — the adaptive classification table (for the user to verify).
3. **Executive summary** — 4–6 bullets: how many not-ready, the dominant group/type/module, the #1 root cause, the biggest spike day.
4. **Not-ready breakdown** — by group, by raw status, by type, by feature, by priority (tables).
5. **Root-cause analysis** — ranked causes with counts + concrete example bug ids/titles.
6. **Spike analysis** — table of dates with counts; call out the peaks + likely reason.
7. **Aging** — oldest not-ready (top N) `| Bug | Status | Age (d) | Priority | Feature | PIC |`.
8. **Recommendations** — concrete actions to drain the not-ready backlog (who, what).

## Rules
- **READ-ONLY** — never create/edit records. Never print tokens/secrets.
- **Semantic, board-specific status grouping** — never assume a fixed status vocabulary; print the mapping and flag UNKNOWN for the user to confirm.
- **No fabricated numbers** — missing field → `n/a (field missing)`. Root causes must cite real bugs, not invented ones.
- **LANGUAGE**: write the report in the configured output language (`.plugin.env` `LANGUAGE`, default Vietnamese with diacritics; keep status/technical terms in English) — see `../../rules/output-language.md`. Use the term/verdict guidance in `../../rules/product-ops.md` §7.
