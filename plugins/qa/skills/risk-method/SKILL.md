---
name: risk-method
description: Reusable logic to assess quality risk for a feature/release from a QA-Lead perspective and emit a Risk Matrix + mitigation plan. Scores each risk factor (Technical / Process / Business) on Likelihood × Impact (1–25), classifies Low/Medium/High/Critical per product-ops.md, defines prevention/detection/response/owner for every Medium+ risk, and recommends a risk-based test strategy (coverage focus, exploratory areas, regression scope, staged rollout, monitoring). Writes results/<context>/risk-assessment-<feature>.md. Reusable core behind the risk command. For QA Lead / Manager.
---

# Skill: risk-method

Reusable capability: turn a feature/release into a **prioritized risk picture** — what could go wrong, how likely, how bad, and exactly what to do about each one. Drives a risk-based test strategy, not a generic checklist.

> 🎯 **Audience = QA Lead / Manager.** Every risk must be specific ("API timeout on third-party payment", not "technical risk"), scored with a stated reason, and paired with a concrete mitigation + owner.

## Inputs (any one)
1. **Feature description + specs/Figma** — read the docs (spawn the `lark-reader`/`figma-reader` agents like `/qa:analyze-spec` does) → scope, complexity, dependencies.
2. **Plan path** — `plans/<feature>/plan.md` → scope, modules, known risks.
3. **Release scope** — the user describes features/changes/timeline → assess the whole release.
4. **Sitemap (optional)** — `sitemap/sitemap.json` for dependency/impact + historical bug hot-spots.

## Procedure
1. **Read** `../../rules/product-ops.md` (§5 Risk Matrix, §8 honesty) + the input source. Resolve the context name (feature/sprint → name, else `ops-<YYYY-MM-DD>`).
2. **Identify risk factors** across three categories — only those that actually apply to this feature:
   - **Technical**: code complexity, integration points, data migration, new tech, platform scope, performance.
   - **Process**: specs completeness, timeline pressure, team familiarity, dependency on other teams, historical bug density.
   - **Business**: user impact, revenue/payment, compliance, data sensitivity (PII), rollback difficulty.
3. **Score** each: Likelihood (1–5) × Impact (1–5) = Risk Score (1–25) → Level (Low 1–4 / Medium 5–9 / High 10–15 / Critical 16–25). State **why** each score.
4. **Mitigate** every Medium+ risk: Prevention (before) · Detection (signal it's materializing) · Response (if it happens) · **Owner** (a role).
5. **Recommend a risk-based test strategy**: highest-coverage areas, exploratory focus, regression scope, staged rollout phases (if applicable), post-release monitoring.
6. **Write** `results/<context>/risk-assessment-<feature>.md` per the structure below.
7. **Conclude**: print the overall risk level, the top 3 risks, the file path, and a go/no-proceed recommendation.

## Report structure
1. **Header** — feature/release, date, sources used.
2. **Risk overview** — count by Level + % + **Overall Risk Level**.
3. **Risk matrix** — `| # | Risk factor | Likelihood | Impact | Score | Level | Mitigation |`.
4. **Risk detail** — per Medium+ risk: category, likelihood reason, impact reason, score/level, mitigation (prevention/detection/response/owner).
5. **Risk-based test strategy** — coverage focus · exploratory focus · regression scope · staged rollout · monitoring.
6. **Sitemap impact** (if available) — dependencies, cross-feature impacts, known historical bugs.
7. **Summary & recommendation** — overall assessment + actions before proceeding + go/no-go (if applicable).

## Rules
- **Specific risks only** — never list generic risks not tied to this feature; differentiate scores (no all-same).
- Every Medium+ risk needs a concrete mitigation **with an owner**. Never skip business risks — they often carry the highest impact.
- Explain the WHY behind each likelihood/impact score.
- **LANGUAGE**: write the report in the configured output language (default Vietnamese with diacritics; technical terms in English) — see `../../rules/output-language.md`.
- Read-only on source docs; this skill produces an assessment, it does not modify specs/tests.
