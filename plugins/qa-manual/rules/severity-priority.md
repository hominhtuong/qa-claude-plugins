# Severity & Priority Framework

A shared framework for assessing **Severity** (the seriousness of the impact) and **Priority** (the urgency of handling) for a bug/ticket.
**Read when**: command `log-bug` and skill `log-bug`; when the user asks to assess handling priority.

> Keep Severity and Priority separate to avoid every bug being tagged `High/Critical`.

---

## 1. Definitions

### Severity (seriousness of the impact)

| Level | Meaning | Main criteria |
|-----|---------|----------------|
| `High` | Serious | Crash, large data loss/corruption, security breach, blocks a core flow with no workaround |
| `Medium` | Moderate | Degraded function, workaround exists, localized impact on one group |
| `Low` | Low | Minor/cosmetic/typo, almost no business impact |

> Some boards use a 4-level scale (`Critical/High/Medium/Low`). In that case: `Critical` = crash/data loss/security; `High` = main flow broken with no workaround; the rest map accordingly.

### Priority (urgency of handling)

| Level | Meaning | Main criteria |
|-----|---------|----------------|
| `High` | Handle now/soon | Wide production impact, financial/legal/security risk, close to release |
| `Medium` | Per plan | Has impact but a workaround exists, schedule within the sprint |
| `Low` | Backlog | Low impact, experience improvement, not blocking |

---

## 2. Decision Matrix

### Step A — Score Severity first (4 axes, prioritized top-down)
1. **Business impact**: Is there incorrect financial/order/closing-number data?
2. **User impact scope**: How many users/tenants are affected?
3. **Functional impact**: Does it block a core flow?
4. **Workaround availability**: Is there an acceptable alternative way to operate?

### Step B — Score Priority next (Priority is NOT necessarily equal to Severity)
1. **Release timing**: Is it close to a release/go-live?
2. **SLA/Commitment**: Any SLA binding, VIP customer, or legal commitment?
3. **Spread potential**: Risk of escalating into a wide-scale incident?
4. **Cost of delay**: Does a 1-3 day delay sharply increase the damage?

---

## 3. Default Mapping (when context is missing)

| Severity | Default Priority |
|----------|-------------------|
| `High` | `High` |
| `Medium` | `Medium` |
| `Low` | `Low` |

### When a mapping mismatch is reasonable
- **Low Severity but high Priority**: a minor bug but in an important demo/release flow, affecting a major partner.
- **High Severity but low Priority** (rare): a stable workaround exists, extremely narrow scope, risk under control.

If the mapping deviates => **you must state the reason explicitly**.

---

## 4. Quick Heuristics

- `High/Critical`: crash, data loss, large incorrect financial figures, security, can't operate.
- `High`: main flow severely broken, no reliable workaround.
- `Medium`: functional bug with a workaround or affecting only a small group.
- `Low`: UI/copy/layout/cosmetic, no business-logic impact.

Missing info => tentatively assign `Medium`, clearly note what needs verifying.

---

## 5. Evidence Checklist Before Concluding

1. Are **Steps + Actual + Expected** clear yet?
2. Is the impact on **prod / stg / dev**?
3. Is there a real **workaround** or just an assumption?
4. How many **users / roles / regions** are affected?
5. Does it touch **finance, data, security, legal**?
6. Is any **release / SLA** milestone approaching?

For any item lacking data, note that item explicitly.

---

## 6. Synonym Mapping (normalize input labels)

| Input label | Normalized |
|-------------|-----------|
| Critical, Blocker, Urgent, S1 | High (or Critical if the board has it) |
| High, Major, S2 | High |
| Medium, Normal, Moderate, S3 | Medium |
| Low, Minor, Trivial, Cosmetic, S4 | Low |

---

## 7. Output Contract for `/log-bug`

- If the user already provided Severity/Priority => validate against the framework. If there's a large mismatch with the evidence => ask to confirm before creating the record.
- If the user did not provide it => auto-estimate + write a short rationale per the framework.
- **Do not override** the level the user provided without explanation.
- When unsure => choose the safe level (`Medium`) + ask for the missing info.
- For cases with financial/security data => review the evidence carefully before lowering the level.
