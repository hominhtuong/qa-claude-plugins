---
name: est-sp-method
description: Reusable logic to estimate Story Points for QC effort (write TCs + execute + log bugs + retest, NOT dev effort) from a plan or a feature description, factored by the executor's role. Reads rules/story-point.md, counts/estimates TCs, assesses complexity/scope/risk to a base SP on the Fibonacci scale, applies the role multiplier (USER_ROLE from .plugin.env: junior ×1.5 / mid ×1.2 / senior·lead ×1.0), rounds up to Fibonacci, and outputs the mandatory SP table. Reusable core behind the est-sp command.
---

# Skill: est-sp-method

Reusable capability: estimate the **QC effort** for a feature in Story Points, adjusted for who will do the work. Output is a fixed table so it's comparable across estimates.

> 📐 SP is an estimate — always explain the reasoning. SP > 13 → recommend splitting. SP measures **QC effort**, not dev effort.

## Inputs (any one)
1. **Plan path** — `plans/<feature>/plan.md`. If it already has an SP section → show it and ask before recalculating.
2. **Feature description + specs/Figma** — read the docs (spawn readers like `/qa:analyze-spec`), then estimate.
3. **Feature name** present in `results/`/`plans/` → use that material.

## Procedure
1. **Read** `../../rules/story-point.md`. **Resolve role** — precedence: (1) role stated in the prompt (e.g. "role: mid") → (2) `.plugin.env` `USER_ROLE` → (3) default `senior`:
   ```bash
   python3 -c "import sys; sys.path.insert(0,'${CLAUDE_PLUGIN_ROOT}/scripts'); from _env import load_env, env_str; load_env(); print(env_str('USER_ROLE','senior'))"
   ```
2. **Analyze**: count/estimate TCs (by modules/scenarios/coverage), assess technical complexity, scope (screens/modules), risk (specs completeness, third-party, uncertainty).
3. **Base SP** from the §2 factors on the Fibonacci scale.
4. **Role multiplier**: junior ×1.5 · mid ×1.2 · senior/lead ×1.0 → round **up** to the nearest Fibonacci.
5. **SP > 13** → recommend splitting into smaller stories.
6. **Output**:
   - **Plan mode** → add/replace the `### Story Point Estimation` section in `plans/<feature>/plan.md`, then print the table.
   - **Description mode** → print the table only (no file).

## Output (MANDATORY table — see story-point.md §4)
```
--- Story Point Estimation ---

| Item | Value |
|------|-------|
| Feature | {name} |
| Role | {role} (from .plugin.env) |
| Estimated SP | {X} points |
| Base SP | {Y} |
| Expected TCs | ~{N} TCs |
| Complexity | {description} |
| Scope | {description} |
| Risk | {description} |
| Fibonacci | 1 · 2 · 3 · **[X]** · 8 · 13 · 21 |
```
If multiplier ≠ 1.0, add after Base SP: `| Role multiplier | x{m} ({role}) → {Y}×{m}={r} → Fibonacci = {X} |`.

## Rules
- ALWAYS the markdown table above — no other format. Bold the selected SP in the Fibonacci row.
- Role from `.plugin.env` (or prompt override) — never hardcode.
- Reasoning must be concrete (TC count + complexity + scope + risk), not a bare number.
- **LANGUAGE**: localize the cell text per the configured output language (default Vietnamese with diacritics; keep SP/Fibonacci/technical terms in English) — see `../../rules/output-language.md`.
