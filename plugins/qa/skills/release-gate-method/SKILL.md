---
name: release-gate-method
description: Reusable logic to score a release GO / NO-GO / CONDITIONAL against an auditable checklist. Reads the gate criteria from .claude/qa-claude/release-gate.config.yml (hard gates = blockers, soft gates = conditional flags), pulls current quality metrics (reusing quality-metrics-method — open bugs by priority + aging, pass rate, coverage) from the bug board + results/, evaluates each criterion, and writes results/release-gate/<release>/gate.md with the verdict, per-criterion table, blocker list, and a sign-off block. Read-only: a decision artifact, never modifies bugs/tests. Reusable core behind the release-gate command.
---

# Skill: release-gate-method

Reusable capability: turn "are we ready to ship?" from a gut call into an **auditable verdict**. Evaluate the release against the team's written gate criteria and emit GO / NO-GO / CONDITIONAL with the evidence behind each decision.

> 🚦 **Verdict semantics**: any **hard** gate failing ⇒ **NO-GO** (must fix before ship). Only **soft** gates failing ⇒ **CONDITIONAL** (ship allowed with explicit sign-off + recorded risk). All gates pass ⇒ **GO**.

## Inputs
1. **Criteria** — `.claude/qa-claude/release-gate.config.yml` (`hard:`/`soft:` thresholds, `closed_statuses`, `sign_off` roster, `notify_on_verdict`). Missing → tell the user to run `/qa:setup` (it scaffolds the file) and stop; do NOT invent thresholds. The config's defaults mirror the **release gates G1–G8** in `../../rules/product-ops.md` §3 — read that for the rationale and the confidence-based CONDITIONAL-GO logic.
2. **Quality metrics** — reuse `quality-metrics-method`: prefer the latest `results/quality-report/<date>/report.md` if fresh (same day); else compute on the fly via `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/lark_bitable.py" --summary` + `results/tests/`. Need: open bugs by Priority, open-Critical aging, latest pass rate, coverage% (if available), created-vs-resolved this period.
3. **Release scope** — the release name/tag from `$ARGUMENTS` (defines the window + labels the output folder).

## Procedure
1. **Load criteria** from the config. Resolve `closed_statuses` → everything else is "open".
2. **Gather metrics** (reuse quality-metrics-method). On board `ok:false` relay the `action` (run `/qa:auth-lark`). Distinguish two cases for a gate whose data is missing — do NOT conflate them:
   - **UNREADABLE** (the source exists but failed: auth/API error, corrupt report) → **UNKNOWN** → a hard gate UNKNOWN ⇒ **NO-GO** (fail-safe — never optimistically pass).
   - **NOT APPLICABLE** (the source genuinely doesn't exist for this team — e.g. `min_pass_rate` but the project has **no automation suite / no `results/tests/` at all**) → mark the gate **N/A → skipped (not a blocker)** and note it; recommend the user set that threshold to `null` in the config. A manual-only team must never be auto-blocked just for lacking automation.
3. **Evaluate each gate**:
   - Hard: `max_open_critical`, `max_open_high`, `min_pass_rate`, `min_coverage` (skip any set to `null`).
   - Soft: `max_open_medium`, `max_critical_age_days`, `require_no_growing_backlog`.
   - Each → PASS / FAIL / UNKNOWN / N/A with the actual value vs threshold.
4. **Derive the verdict**: any hard FAIL or hard UNKNOWN ⇒ **NO-GO**; else any soft FAIL ⇒ **CONDITIONAL**; else **GO**. Gates marked **N/A (skipped)** do not count toward the verdict (confidence = PASS / (total − N/A), per product-ops §3).
5. **Write** `results/release-gate/<release>/gate.md` per the structure below.
6. **Optional notify**: if `notify_on_verdict: true`, send the verdict line + blocker count on the configured channel.
7. **Conclude**: print the verdict (with a clear 🟢/🟡/🔴), the blocker list, and the gate file path.

## Report structure (`gate.md`)
1. **Verdict banner** — 🟢 GO / 🟡 CONDITIONAL / 🔴 NO-GO + the release name + generated date + data-source freshness.
2. **Gate checklist** — `| Gate | Type | Threshold | Actual | Result |` (hard then soft).
3. **Blockers** — every hard FAIL/UNKNOWN with what must change to clear it (e.g. "close 2 open Critical: BUG-12, BUG-19").
4. **Conditional risks** — soft FAILs + the risk shipping anyway carries.
5. **Open Critical/High list** — `| Bug | Priority | Status | Age (d) | Dev PIC |` (the bugs gating the release).
6. **Sign-off** — the roster from config with empty checkboxes for each role to approve a CONDITIONAL/GO.
7. **Notes** — data caveats (any UNKNOWN gate + why).

## Rules
- **READ-ONLY** — produces a decision artifact; never edits bugs/tests. Never print tokens.
- **Fail-safe** — unreadable data behind a hard gate = UNKNOWN = NO-GO, never an optimistic pass.
- **Thresholds come ONLY from the config** — never hardcode/guess a policy.
- **LANGUAGE**: write the gate report in the configured output language (`.plugin.env` `LANGUAGE`, default Vietnamese with diacritics; keep gate/metric terms in English) — see `../../rules/output-language.md`.
- Consistent with `quality-metrics-method` (same open-bug + pass-rate definitions) so the gate and the dashboard never disagree.
