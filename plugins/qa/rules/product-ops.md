# Product Ops Rules (shared)

Shared framework for the **quality-management & product-ops** commands: SLA, health metrics,
release readiness, triage, risk assessment, KPI.
**Read when**: `/qa:sla`, `/qa:triage`, `/qa:risk`, `/qa:release-gate`, `/qa:quality-report`
(load on demand — the command states which sections it needs).

> Output language follows [output-language.md](output-language.md) (default Vietnamese with
> diacritics; keep technical terms in English). The term table in §7 is guidance for the
> Vietnamese case so manager-facing reports read cleanly.

---

## 1. SLA Defaults

### SLA Targets (default — the user/board can override)

| Priority | Response Time | Resolution Time |
|----------|--------------|-----------------|
| P1 - Critical | 15 min | 4 h |
| P2 - High | 1 h | 24 h |
| P3 - Medium | 4 h | 72 h |
| P4 - Low | 24 h | 1 week |

### Priority synonym mapping (normalize any input label → P1–P4)

| Input | Maps to |
|-------|---------|
| Critical, Blocker, Urgent, S1 | P1 |
| High, Major, S2 | P2 |
| Medium, Normal, Moderate, S3 | P3 |
| Low, Minor, Trivial, S4, Cosmetic | P4 |

Unmappable label → bucket `Unknown`, report the count, ask to normalize the source data.

---

## 2. Health Metrics Thresholds

### Quality
| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| Bug Escape Rate | <5% | 5–15% | >15% |
| Regression Rate | <3% | 3–8% | >8% |
| Open Critical (P1/P2) | 0 | 1–2 | >2 |

### Customer
| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| Customer-Reported Bug Ratio | <20% | 20–40% | >40% |
| Repeat Issue Rate | <5% | 5–10% | >10% |

### Testing
| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| Test Coverage Rate | >80% | 60–80% | <60% |
| Test Execution Rate | >95% | 80–95% | <80% |
| Test Pass Rate | >95% | 85–95% | <85% |

### Velocity
| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| Hotfix Rate | <10% | 10–25% | >25% |

---

## 3. Release Readiness Gates (defaults for `/qa:release-gate`)

These are sensible defaults; the team's `release-gate.config.yml` overrides them.

### Critical gates (FAIL ⇒ NO-GO)
- **G1 – Test Completion**: Execution rate ≥ 95%
- **G2 – Test Pass Rate**: Pass rate ≥ 95%
- **G3 – Critical Bugs**: 0 P1/P2 open

### Important gates (FAIL ⇒ CONDITIONAL GO possible)
- **G4 – High Bugs**: all P3 triaged (workaround or accepted)
- **G5 – Regression**: regression suite pass = 100%

### Advisory gates (FAIL ⇒ noted, not blocking)
- **G6 – Rollback Plan**: documented
- **G7 – Release Notes**: reviewed
- **G8 – Sign-off**: QA Lead + PM + Tech Lead approved

### Verdict logic
```
IF any G1/G2/G3 FAIL => NO-GO
ELIF confidence >= 70% AND no P1/P2 open => CONDITIONAL GO
ELSE => NO-GO
confidence = (PASS gates / (total - N/A)) x 100%
```

---

## 4. RICE Scoring Framework (for `/qa:triage`)

| Factor | Scale | Guidance |
|--------|-------|----------|
| **Reach** | # users affected (or % of base) | estimate from description / reports |
| **Impact** | 3=Massive · 2=High · 1=Medium · 0.5=Low | severity of effect on the user workflow |
| **Confidence** | 100%=High · 80%=Medium · 50%=Low | confidence in Reach + Impact |
| **Effort** | person-days to fix | complexity of the fix |

**Formula**: `RICE = (Reach × Impact × Confidence) / Effort`

---

## 5. Risk Matrix (for `/qa:risk`)

- **Likelihood**: 1 (Rare) · 2 (Unlikely) · 3 (Possible) · 4 (Likely) · 5 (Almost Certain)
- **Impact**: 1 (Negligible) · 2 (Minor) · 3 (Moderate) · 4 (Major) · 5 (Catastrophic)
- **Risk Score** = Likelihood × Impact

| Score | Level | Action |
|-------|-------|--------|
| 1–4 | Low | standard testing |
| 5–9 | Medium | additional coverage, peer review |
| 10–15 | High | exploratory testing, staged rollout, contingency plan |
| 16–25 | Critical | full regression, canary deploy, mandatory rollback plan |

---

## 6. Bug Classification

### Severity / Priority
Full decision matrix (Severity vs Priority, evidence checklist, synonym mapping) lives in
[severity-priority-framework.md](severity-priority-framework.md). Priority-only logging logic
for the bug board is in [priority.md](priority.md).

### Bug Types
| Type | Code | Description |
|------|------|-------------|
| Functional | `FUNC` | logic, flow, business rule |
| UI/UX | `UI` | display, layout, interaction |
| Performance | `PERF` | slow, timeout, memory |
| Data | `DATA` | loss, corruption, calculation |
| Security | `SEC` | auth, authorization, exposure |
| Integration | `INT` | API, third-party, cross-module |
| Regression | `REG` | a previously fixed bug reappeared |

---

## 7. Output Rules

- **Reports** → `results/<context-name>/` as `.md` (data tables optionally `.xlsx`). Sharing
  (when enabled) follows the plugin's channels: Lark / R2 / S3 — same toggles as the rest.
- **Context naming**: user-given feature/sprint name → use it; otherwise date-based
  `ops-<YYYY-MM-DD>`. Folder names lowercase-hyphen (e.g. `sprint-15`, `payment-module`).
- **No personal address** in formal reports (they go to leadership). The Owner column in an
  action table uses a **role**: "QA Lead", "Dev Team", "PS Lead"… not a personal name.

### Report language (when output is Vietnamese)
Manager-facing reports must read cleanly — avoid unnecessary English. Use Vietnamese verdicts:

| Vietnamese (USE) | English (avoid) | When |
| --- | --- | --- |
| **ĐẠT** | ON_TRACK / PASS | meets or beats target |
| **CÓ RỦI RO** | AT_RISK / NEAR | gap 0–1% |
| **TRƯỢT TARGET** | OFF_TRACK / FAIL | gap > 1% |
| **KHẢ THI** | REALISTIC | action/target achievable |
| **KHÔNG KHẢ THI** | UNREALISTIC | action/target unrealistic |

Common terms to translate: spike → tăng đột biến · blind spot → điểm mù · prioritize → ưu tiên ·
audit → rà soát · RCA → phân tích nguyên nhân gốc · stakeholder → bên liên quan · enforce → bắt buộc ·
momentum → đà cải tiến · backfill → bổ sung dữ liệu thiếu.

**Keep in English**: technical acronyms (API, token, OAuth, SLA, FRT, TTR, CRUD), standard test/release
terms (bug, ticket, regression, sprint, release, hotfix, P1/P2/P3/P4), product/feature names, units (%, ms, MB).
Does NOT apply to test-case docs, code, or config — those keep technical convention.

---

## 8. Honesty rules (all product-ops commands)

- **Base analysis on actual data** — never fabricate values not in the input/board.
- Missing source → mark `n/a (source missing)`, never guess.
- Differentiate (don't give every bug/risk the same score) — the scoring must rank.
- Every Medium+ risk and every action needs an **owner** and a concrete next step.
