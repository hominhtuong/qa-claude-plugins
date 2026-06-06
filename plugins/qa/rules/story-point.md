# Story Point Estimation Rules (shared)

Rules for estimating Story Points from the **QC perspective** (effort to write TCs + execute +
log bugs + retest — NOT dev effort).
**Read when**: `/qa:est-sp`, and when `/qa:plan-tests` / `/qa:plan-gen-testcases` add an SP section.

> Output language follows [output-language.md](output-language.md).

---

## 1. Scale (Fibonacci)
Use **1, 2, 3, 5, 8, 13, 21**.

| SP | Description | Examples |
|----|-------------|----------|
| **1** | very simple, near-zero risk | change a label, fix a typo, verify 1 field |
| **2** | simple, low risk, 1–2 screens | toggle on/off, verify a simple list |
| **3** | light-medium, clear logic | simple form (3–5 fields), basic CRUD for 1 entity |
| **5** | medium, validation + business logic | complex form, filter/sort/pagination, 2–3 step flow |
| **8** | complex, many scenarios, API integration | full CRUD module, multi-step flow, payment integration |
| **13** | very complex, cross-module, many edge cases | third-party integration, complex workflow, multi-platform |
| **21** | epic — should be split | an entire large module → split into multiple stories |

## 2. Assessment factors (QC view)

### 2.1 Test-case count
| TC count | Base SP (before role adjustment) |
|----------|----------------------------------|
| 1–10 | 1–2 |
| 11–25 | 3–5 |
| 26–50 | 5–8 |
| 51–80 | 8–13 |
| 80+ | 13–21 (should split) |

### 2.2 Technical complexity
Low (UI display, static, simple nav) · Medium (validation, CRUD, filter/sort, state) ·
High (API integration, real-time, cross-platform, multi-step) · Very High (third-party, payment, security, concurrency).

### 2.3 Impact scope
1 screen → low · 2–3 related screens → medium · cross-module / many flows → high.

### 2.4 Risk & uncertainty
Clear logic + complete specs → low · incomplete specs / ambiguity → medium · third-party dependency / no API docs → high.

## 3. Role multiplier (IMPORTANT)
SP is adjusted by the executor's role, read from **`.plugin.env` `USER_ROLE`** (default `senior`).
Override per call if the user says e.g. "role: junior".

| Role | Multiplier | Why |
|------|-----------|-----|
| **junior** | ×1.5 (round up to nearest Fibonacci) | extra time for context, more detailed TCs, more reviews |
| **mid** | ×1.2 (round up) | experienced but may need guidance on complex parts |
| **senior** | ×1.0 (baseline) | quick understanding, efficient TC writing |
| **lead** | ×1.0 (baseline) | as senior for execution, plus review responsibility |

**Calculation**: base SP (from §2) → × role multiplier → round **up** to the nearest Fibonacci number.
Example: base 5 → junior 5×1.5=7.5 → **8**; mid 5×1.2=6 → **8**; senior/lead → **5**.

Read the role via the env helper:
```bash
python3 -c "import sys; sys.path.insert(0,'${CLAUDE_PLUGIN_ROOT}/scripts'); from _env import load_env, env_str; load_env(); print(env_str('USER_ROLE','senior'))"
```

## 4. Output format for `/qa:est-sp` (MANDATORY table)
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
- ALWAYS this markdown table — no other format. Bold the selected SP in the Fibonacci row.
- If multiplier ≠ 1.0, add a row after Base SP: `| Role multiplier | x{m} ({role}) → {Y}×{m}={r} → Fibonacci = {X} |`.

## 5. Special rules
- SP is an estimate — always explain the reasoning.
- SP > 13 → recommend splitting into smaller stories.
- Plan mode: when a plan already has an SP section, show it and ask before recalculating.
- SP applies to **QC effort**, not dev effort.
