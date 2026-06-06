# Severity & Priority Framework (shared)

Shared framework for assessing **Severity** (how bad the impact is) and **Priority** (how urgent
the fix is) for a bug/ticket.
**Read when**: `/qa:triage`, `/qa:explain-bug`, `/qa:sla`, and whenever the user asks to assess
handling priority. (For Priority-only bug logging on the board, see [priority.md](priority.md).)

> Output language follows [output-language.md](output-language.md).

---

## 1. Goal
- Align how QA, Dev and Product Ops score severity vs urgency.
- Separate **Severity** (impact) from **Priority** (urgency) — avoid everything becoming `High/Critical`.

## 2. Definitions

### Severity (P1–P4)
| Level | Meaning | Main criteria |
|-------|---------|---------------|
| `P1 - Critical` | most severe | system down, large data loss/corruption, security breach, blocks a core flow with no workaround |
| `P2 - High` | high | main feature broken, large impact, no viable workaround |
| `P3 - Medium` | moderate | function impaired, workaround exists, local impact |
| `P4 - Low` | low | minor/cosmetic/typo, almost no business impact |

### Priority (P1–P4)
| Level | Meaning | Main criteria |
|-------|---------|---------------|
| `P1 - Immediate` | fix now | wide production impact, financial/legal/security risk, needs urgent hotfix |
| `P2 - Urgent` | fix soon | significant user/business impact, fix within 24h or this sprint |
| `P3 - Planned` | scheduled | has impact but a workaround exists; plan per sprint |
| `P4 - Backlog` | backlog | low impact, experience improvement, non-blocking |

## 3. Decision order
**A. Score Severity first** on 4 axes (top-down): business impact (wrong financial/order/settlement data?) →
user impact scope (how many users/tenants?) → functional impact (blocks a core flow?) →
workaround availability (acceptable alternative?).

**B. Then score Priority** — not necessarily equal to Severity. Add: proximity to release/go-live;
SLA/commitment (VIP customer, legal); escalation risk; cost of delay (does 1–3 days of delay sharply raise loss?).

## 4. Default mapping (when context data is thin)
| Severity | Suggested default Priority |
|----------|----------------------------|
| `P1 - Critical` | `P1 - Immediate` |
| `P2 - High` | `P2 - Urgent` |
| `P3 - Medium` | `P3 - Planned` |
| `P4 - Low` | `P4 - Backlog` |

Deviating is valid when: low severity but high priority (small bug on a critical demo/release flow,
big partner) — or, rarely, high severity but lower priority (stable workaround, very narrow scope,
risk clearly controlled). **If you deviate, record the reason.**

## 5. Quick heuristics
- `Critical`: crash, data loss, large wrong financial figures, security, cannot operate.
- `High`: main flow badly broken, no reliable workaround.
- `Medium`: functional bug with a workaround or affecting only a small group.
- `Low`: UI/copy/layout/cosmetic, no business-logic impact.

Missing info → tentatively assign `Medium` and state explicitly what must be verified.

## 6. Evidence checklist (before concluding)
1. Are Steps + Actual + Expected clear? 2. Which env — prod/stg/dev? 3. Real workaround or assumed?
4. How many users/roles/regions affected? 5. Any financial/data/security/legal angle?
6. Any upcoming release/SLA milestone? — State each missing item explicitly.

## 7. Output contract per command
- **`/qa:triage`** / **`/qa:sla`**: normalize all labels to `P1..P4`; unmappable → `Unknown` + report count.
- **`/qa:explain-bug`**: MUST include a block — *"Is the Severity/Priority assessment reasonable?"* with
  conclusion (Reasonable / Not reasonable / Insufficient data) + suggested Severity + suggested Priority + reason + next step.
- **`/qa:log-bug`**: validate a user-given level; on a large evidence mismatch, ask before creating. If omitted,
  auto-estimate with a short rationale (Priority-only per [priority.md](priority.md)).

## 8. Synonym normalization
| Input label | Normalized |
|-------------|-----------|
| Critical, Blocker, Urgent, S1 | P1 |
| High, Major, S2 | P2 |
| Medium, Normal, Moderate, S3 | P3 |
| Low, Minor, Trivial, Cosmetic, S4 | P4 |

## 9. Operating notes
- Never silently override a user-given level — explain. When unsure, pick the safe level (`Medium`) + ask.
- For financial/security cases: review evidence carefully before lowering a level.
