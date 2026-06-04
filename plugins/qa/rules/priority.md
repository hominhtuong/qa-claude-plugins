# Priority Framework

A shared framework for assessing **Priority** (the urgency of handling) for a bug/ticket.
**Read when**: command `log-bug` and skill `log-bug`; when the user asks to assess handling priority.

> Severity is **not used** — log only Priority. If the user does not provide a Priority, the AI auto-estimates it from the evidence (do not block on it).

---

## 1. Priority levels

| Level | Meaning | Main criteria |
|-----|---------|----------------|
| `Critical` | Drop everything | Crash, data loss/corruption, security breach, blocks a core flow with no workaround, large incorrect financial figures |
| `High` | Handle now/soon | Main flow severely broken with no reliable workaround; wide production impact; financial/legal/security risk; close to release |
| `Medium` | Per plan | Functional bug with a workaround, or affecting only a small group; schedule within the sprint |
| `Low` | Backlog | UI/copy/layout/cosmetic, no business-logic impact, experience improvement, not blocking |

> Some boards use a 3-level scale (`High/Medium/Low`). In that case fold `Critical` into `High`. Always match the board's actual option list (read the field options when unsure).

---

## 2. How to score (4 axes, prioritized top-down)
1. **Business impact**: Is there incorrect financial/order/closing-number data? → pushes toward Critical/High.
2. **User impact scope**: How many users/tenants/roles are affected? Wider → higher.
3. **Functional impact**: Does it block a core flow with no workaround? → higher.
4. **Timing**: Close to a release/go-live, SLA/VIP commitment, or risk of a wide-scale incident? → higher.

Missing info → tentatively assign `Medium`, clearly note what needs verifying.

---

## 3. Synonym mapping (normalize input labels)

| Input label | Normalized |
|-------------|-----------|
| Critical, Blocker, Urgent, P0, S1 | Critical (or High if the board has no Critical) |
| High, Major, P1, S2 | High |
| Medium, Normal, Moderate, P2, S3 | Medium |
| Low, Minor, Trivial, Cosmetic, P3, S4 | Low |

---

## 4. Output contract for `/log-bug`
- User provided a Priority → validate against the framework. Large mismatch with the evidence → ask to confirm before creating the record. **Do not override** the user's level without explanation.
- User did NOT provide a Priority → **auto-estimate** from the evidence + write a short one-line rationale. Do not ask the user just for priority.
- Unsure → choose the safe level (`Medium`) + note what needs verifying.
- Financial/security data → review the evidence carefully before lowering the level.
