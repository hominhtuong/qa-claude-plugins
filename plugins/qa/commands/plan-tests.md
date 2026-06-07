---
description: Exploratory gate first, then design an AUTOMATION test plan (plans/<feature>/plan.md). By DEFAULT, plan even when bugs are found (record them as known-issues/risks) as long as elements are declarable + actionable; pass --stop-on-bug to STOP at a bug report instead. Auto-routes by platform to read the correct design-pattern rules
argument-hint: <feature-name> [web|android|ios] [--stop-on-bug] [requirement description / Lark link / Figma]
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, WebSearch, Agent
---

# /qa:plan-tests — Exploratory gate → Design an automation test plan (platform router)

User request: **$ARGUMENTS**

> Want to plan MANUAL TEST CASES (not automation code) instead? Use **`/qa:plan-gen-testcases`**.

> **Output language**: write the plan/report prose in the **configured language** (`.plugin.env` `LANGUAGE`, default Vietnamese with diacritics) — see [output-language.md](../rules/output-language.md); code/identifiers stay English. Pass the resolved language into sub-agents.

Goal: create a **solid plan (.md file)** describing how to implement the tests. `/qa:cook` executes it afterward. **Do NOT write code** at this step. (The name `/qa:plan-tests` distinguishes it from plan-release/plan-sprint.)

> 🚦 **GATE — two modes (flag-controlled)**: exploratory always runs first and always writes a bug report when it finds `[APP-BUG]`. What happens *after* depends on the flag:
> - **Default (no flag) — plan anyway**: a bug does NOT block planning. Dev will fix the feature later; QA proceeds in parallel and accepts the risk. As long as each affected element is still **declarable** (locator findable) and **actionable** (clickable/typeable), it can go into the plan — the test records the **canonical expectation** (per spec) + a `KNOWN-BUG: <APP-ID>` note, so the case correctly FAILS until dev fixes. Only parts that are genuinely un-declarable / un-actionable (element absent, page crashes, cannot interact) are excluded as **Blocked cases**.
> - **`--stop-on-bug` — stop at the bug report**: any `[APP-BUG]` → **do NOT make a test plan**; the only deliverable is the bug report for dev. Use this when you want a clean app before investing in automation.

## Step 0 — Lock platform + parse flags (routing)
Run **skill `detect-platform`** → one `platform`. It decides which design-pattern rules to read in Step 2.
Parse `--stop-on-bug` from `$ARGUMENTS` (strip it before treating the rest as the requirement text). Default = **off** (plan-anyway mode).

## Step 1 — EXPLORATORY GATE (before anything)
1. Is there a recent bug report yet? `results/<feature-name>/dev-bug-report-*.md` + the register `results/bug-summary.md`. None/stale/changed → run **`/qa:exploratory <feature-name> <platform>`**.
   - 🔬 **Go DEEP, not a single lap.** This exploratory feeds the plan, so it must understand the feature in full, not "walk around once". Cover **cross-cutting/common contexts that affect the whole app** and **every variant of each entity** — see the `exploratory-method` skill's *"Depth & coverage for planning"* section (e.g. tax types each affecting product+sales, e-invoice settings, the "must have a unit to sell" rule; product = 3 kinds {normal · attributes/variants · conversion}, each with its own actions → open detail + copy for ALL three, etc.). A shallow sweep yields an incomplete plan with missing cases — that is the failure to avoid.
2. Read the exploratory result, then branch on the flag:
   - **`--stop-on-bug` ON**:
     - 🔴 **Has `[APP-BUG]`** → **STOP planning**; print "Feature NOT complete — N app bugs, see `dev-bug-report-*.md`". Do NOT create `plans/<feature>/plan.md`.
     - 🟢 **No `[APP-BUG]`** → continue to Step 2.
   - **Default (plan-anyway, no flag)** → **always continue to Step 2**, but carry the bug findings into the plan:
     - For each `[APP-BUG]`, decide **plannability**: is the affected element still **declarable** (locator findable) AND **actionable** (clickable/typeable)?
       - ✅ Yes → include it in the plan; the test case records the **canonical expectation** (per spec) + a `KNOWN-BUG: <APP-ID>` tag, so it fails honestly until dev fixes (this is intended — QA runs ahead of the fix).
       - ❌ No (element absent / page crashes / cannot interact at all) → exclude that case; list it under **Blocked cases** in the plan with the blocking `<APP-ID>`.
     - Always still produce the bug report + sync `results/bug-summary.md` (the exploratory does this). The plan and the bug report are BOTH deliverables.
   - Elements extracted during exploratory are used for Layer 1/2 in both modes.
3. Large feature → **gate per sub-feature** (each sub-feature follows the mode above independently).

## Step 2 — Design the plan — skill `plan-method` (agnostic) + platform rules
Read **skill `plan-method`** (plan structure + layering principles + element 3-layer lookup) and the **design-pattern rules per `platform`** (only 1 branch):
- **web** → `rules/web/design-pattern.md` · `coding-rules.md` · `design-system.md`.
- **android | ios** → `rules/app/design-pattern.md` · `coding-rules.md` · `design-system.md`.

Also read the project's `@CLAUDE.md` + sitemap/test-hints if present. If the request has a Lark/Figma link → spawn a reader agent (`agent-lark-reader`/`agent-figma-reader`, 1 agent/URL, max 5/batch, append to `plans/<feature>/tracking.md`; details in [lark-mcp-guide.md](../rules/lark-mcp-guide.md)).

## Step 3 — Write the plan to `plans/<feature>/plan.md` (lowercase-hyphen; update if it exists)
Structure (per `plan-method`):
```markdown
## Objective
## Analysis   (related files · reuse · new files · element source: Screen/JSON/discovery)
## Steps      (each step: file path + create/edit + details)
## Screens    (| Screen | File | Key element (isDisplayed) | Main locator | Action methods |)
## Test cases (| Test | Scenario | Assertion | Known-bug |)  — FULL test functions, one scenario per function, NO shallow isDisplayed; the Known-bug column carries the `<APP-ID>` for cases expected to fail until dev fixes
## TestNG XML (GoToHomeTest is the first <test> block — app only)
## Missing ID Report  (| element | screen | current locator | description | — omit if everything has an id)
## Known issues & Blocked cases  (default mode only; | Case | APP-ID | Plannable? | Reason | — list each `[APP-BUG]`: planned-with-KNOWN-BUG vs blocked; omit if exploratory was clean)
## Notes / risks / open questions
```

## Principles
- Layering: `screens` (no-assert) → `tests` (assert) → `regression/smoke` (compose). Feature starts from Home.
- The plan **lists** the sitemap screens/nodes to create — only `/qa:cook` writes them for real. The plan records the **correct expectation** (per spec) so `/qa:cook` keeps the test honest — including for `KNOWN-BUG` cases, which assert the canonical expectation and therefore fail until dev fixes (intended).
- After writing the file → print the plan path + platform + a 3-5 line summary for review before `/qa:cook`. In default mode, also print the count of planned `KNOWN-BUG` cases vs Blocked cases so the user sees what's running ahead of the fix.
