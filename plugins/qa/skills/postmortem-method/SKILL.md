---
name: postmortem-method
description: Reusable logic to produce a blameless incident postmortem from an incident description (+ optional related bug records on the Lark board, logs, links). Builds a chronological timeline, a root-cause analysis (5 Whys + contributing technical/process factors), impact assessment, resolution/recovery notes, what-went-well/wrong/lucky, and a tracked action-item table (prevent/detect/mitigate, owner role, priority, due). Writes results/postmortem/<incident-slug>.md. Blameless (roles not names), evidence-based (asks for missing facts, never invents the timeline). Reusable core behind the postmortem command. For Product Ops / QA Lead.
---

# Skill: postmortem-method

Reusable capability: turn an incident into a **blameless postmortem** that explains what happened, why, and what concrete changes prevent a repeat. The value is an honest timeline + real root cause + tracked action items — not a blame log.

> 🧭 **Blameless**: describe systems and decisions, attribute owners by **role** ("Dev Team", "PS Lead"), never blame an individual. **Evidence-based**: build the timeline only from facts the user/records provide; where a fact is missing, list it as an open question — never invent timestamps or causes.

## Inputs
1. **Incident description** (required) — what happened, when detected, when resolved, who/what was affected. If thin, ask targeted questions (see below) before concluding.
2. **Related bug/ticket records** (optional) — pull from the Lark board to ground the timeline:
   - by Bug ID: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/lark_bitable.py" --bug-id <n> --with-comments`
   - by record link: `... --record-id recXXX --with-comments`
   - or a whole board/range: `... [--url "<board_url>"] --since <YYYY-MM-DD> --until <YYYY-MM-DD>`
   On `ok:false` relay the `action` (`/qa:auth-lark`); continue with the user-described facts and flag the board section ⚠️ unavailable.
3. **Logs / links / screenshots** (optional) — read and fold into the timeline + evidence.

## Severity & classification
Score incident severity per `../../rules/severity-priority-framework.md` (P1–P4) and the SLA targets / bug types in `../../rules/product-ops.md` (§1, §6). State response/resolution time vs the SLA target.

## Procedure
1. **Gather** the description + any board records/logs. Resolve the incident slug (short kebab-case) and the dates.
2. **Reconstruct the timeline** strictly from evidence: detection → triage/diagnosis → mitigation/workaround → resolution → verification, each with a timestamp where known (mark unknowns `?`).
3. **Root-cause analysis**: apply **5 Whys** to reach the underlying cause; separate the **trigger** from the **root cause**; list contributing factors split into **technical** and **process** (e.g. missing test coverage, no alert, gap in review).
4. **Impact**: users/tenants affected, scope, duration, and any financial/data/security/SLA consequence.
5. **Action items**: each is concrete + assigned to a **role** + typed **Prevent / Detect / Mitigate** + a priority + a due target. Cover all three types (preventing recurrence, detecting faster, limiting blast radius next time).
6. **Write** `results/postmortem/<incident-slug>.md` per the structure below.
7. **Conclude**: print severity, duration, the one-line root cause, the count of action items by type, and the file path. List any open questions that block a firm conclusion.

## Report structure
1. **Summary** — 1–2 lines: what happened, when, severity, duration, headline impact.
2. **Metadata** — detected-at · resolved-at · duration · severity (P1–P4) · status · affected area · owner roles · related bug ids/links.
3. **Impact** — users/scope/duration + financial/data/security/SLA effect (SLA target vs actual).
4. **Timeline** — `| Time | Event | Source |` chronological (detection → resolution → verification).
5. **Root-cause analysis** — trigger vs root cause; the 5-Whys chain; contributing factors (Technical / Process).
6. **Resolution & recovery** — what fixed it, any workaround, how recovery was verified.
7. **What went well / what went wrong / where we got lucky** — three short lists.
8. **Action items** — `| # | Action | Type (Prevent/Detect/Mitigate) | Owner (role) | Priority | Due |`.
9. **Lessons learned & open questions** — takeaways + facts still needed to close the analysis.

## Rules
- **Blameless** — systems/decisions/roles, never individual blame.
- **Evidence-based** — no invented timestamps or causes; missing facts → open questions.
- **Every action item** has a role owner + type + due; cover Prevent **and** Detect **and** Mitigate.
- **READ-ONLY** on the board — never create/edit records. Never print tokens/secrets.
- **LANGUAGE**: write the report in the configured output language (`.plugin.env` `LANGUAGE`, default Vietnamese with diacritics; keep severity/technical terms in English) — see `../../rules/output-language.md`; use the term/verdict guidance in `../../rules/product-ops.md` §7.
- This analyzes ONE incident → postmortem. Analyzing the whole board backlog over a range is `/qa:bug-analysis`; ranking a bug list is `/qa:triage`.
