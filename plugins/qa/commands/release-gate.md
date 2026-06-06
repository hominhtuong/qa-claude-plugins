---
description: Score a release GO / NO-GO / CONDITIONAL against an auditable checklist — open bugs by priority + aging, pass rate, coverage vs the team's gate criteria in release-gate.config.yml. Hard gate fail => NO-GO; soft gate fail => CONDITIONAL (ship with sign-off). Reads the bug board + results/ (read-only), writes results/release-gate/<release>/gate.md with verdict, per-gate table, blockers, sign-off. For QA Manager / Product Ops.
argument-hint: <release name or tag> [--board <alias>] [--notify]
allowed-tools: Read, Glob, Grep, Bash, Agent
---

# /qa:release-gate — Go / No-Go quality gate

You are a **QA Manager / Release captain** producing an auditable ship decision. Request: **$ARGUMENTS**. Core logic = the **`release-gate-method`** skill. The deliverable is a verdict with the evidence behind every gate — not an opinion.

> **READ-ONLY**: reads the bug board + results, writes a gate report. NEVER creates/edits bugs or tests.
> **FAIL-SAFE**: a gate whose data is **UNREADABLE** (auth/API error) is **UNKNOWN** → a hard UNKNOWN ⇒ **NO-GO** (never pass optimistically). But a gate whose source **genuinely doesn't exist** (e.g. a manual-only team with no automation suite for `min_pass_rate`) is **N/A → skipped**, not a blocker — note it and suggest setting that threshold to `null`.
> **LANGUAGE — RULE #1**: write the report in the configured output language (`.plugin.env` `LANGUAGE`, **default Vietnamese with diacritics**; keep gate/metric terms in English) — see [output-language.md](../rules/output-language.md).
> **NEVER print a token/secret.**

## Must read first
- @${CLAUDE_PLUGIN_ROOT}/skills/release-gate-method/SKILL.md (gate evaluation + report structure)
- The gate criteria: `.claude/qa-claude/release-gate.config.yml`. Missing → tell the user to run `/qa:setup` (it scaffolds the file), then stop. Do NOT invent thresholds.

## Resolve scope
1. **Release** = `$ARGUMENTS` (name or git tag). Required — if absent, ask. Defines the metric window + the output folder `results/release-gate/<release>/`.
2. **Board**: `--board <alias>` overrides `active_board`.
3. `--notify` (or `notify_on_verdict: true` in config) → send the verdict on the configured channel.

## Orchestration
1. **Load criteria** from `release-gate.config.yml` (`hard:`/`soft:` thresholds, `closed_statuses`, `sign_off`).
2. **Gather metrics** (reuse the `quality-metrics-method` logic): prefer today's `results/quality-report/<date>/report.md` if present; else run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/lark_bitable.py" --summary` + read `results/tests/`. Compute open-by-priority + Critical aging + latest pass rate + coverage. On board `ok:false` → relay the `action` (`/qa:auth-lark`); mark dependent gates UNKNOWN.
3. **Evaluate** each hard + soft gate (PASS / FAIL / UNKNOWN with actual vs threshold) → derive the verdict (hard fail/unknown ⇒ NO-GO; soft fail ⇒ CONDITIONAL; else GO).
4. **Write** `results/release-gate/<release>/gate.md` per the skill's 7-section structure (verdict banner, gate checklist, blockers, conditional risks, open Critical/High list, sign-off, notes).
5. **Deliver** (optional): with `--notify`, send the verdict line + blocker count.
6. **Conclude**: print the 🟢/🟡/🔴 verdict, the blocker list, and the gate file path.

## Rules
- READ-ONLY; thresholds come ONLY from the config; never guess a policy.
- Unreadable data behind a hard gate = NO-GO (never optimistic).
- Vietnamese with diacritics for narrative; English for gate/metric labels.
- Need the underlying dashboard? Run `/qa:quality-report` first; this command reuses it when fresh.
