---
name: fix-by-layer
description: Reusable logic to fix an issue (compile fail, test fail, flaky, rule violation, Critical finding) at the RIGHT layer of the test architecture, applying the minimal fix at the root cause without workarounds that mask bugs. Used by the fix command (core), push-code/merge-request (auto-fix clear Critical), cook (on compile/run errors). Verify with the build-verify skill.
---

# Skill: fix-by-layer

Reusable capability: locate the right layer to fix, don't patch the wrong place. Standards: [design-pattern.md](../../rules/app/design-pattern.md), [coding-rules.md](../../rules/app/coding-rules.md).

## Procedure
0. **Triage before fixing** ([failure-triage.md](../../rules/failure-triage.md)) — **MANDATORY**: classify the FAIL as `[APP-BUG]` vs `[FRAMEWORK]`/`[ENV]`/`[DATA]`. If **`[APP-BUG]`** (app is wrong — reproducible on the real app): **STOP, do NOT fix the test to make it green.** Record the defect (expected vs actual + evidence) to report to dev; keep the test honest (genuinely red, or mark as known-defect with a ticket). This skill ONLY fixes when the root cause is `[FRAMEWORK]`/`[ENV]`/`[DATA]` (app is correct, automation/environment/data is wrong).
1. **Scope it**: read the compile error / stack trace / log, or rerun the failing class `mvn test -Dtest=<Class>`. Selector/UI changed → reopen the app with the **`navigate-app` skill** + the **`find-elements-*` skill (per platform)** to get the correct locator. Confirm the element/behavior actually exists on the app (distinguish from `[APP-BUG]`).
2. **Find the right layer** (don't patch the wrong place):
   - Selector / element changed → **Screen** (`@MobileFindBy`).
   - Wrong expectation / assertion / reporting → **Test** (`tests/<group>`).
   - Wrong compose flow / missing GoToHome / wrong recovery → **regression/smoke** (extends `BaseRegression`).
   - Infrastructure (timeout, capabilities, account, device) → **configurations/** + `utils`/`base`, NOT hard-coded in the Test.
   - Element missing an id (locator broke due to text/xpath) → switch to a more stable locator + record via the `missing-ids` skill.
3. **Minimal fix, at the root cause** — NO workarounds: no random `Thread.sleep`, no indiscriminate timeout bumps, no `try/catch` swallowing errors, no disabling assertions, **no loosening an assertion to dodge an `[APP-BUG]`** (masking an app bug = forbidden). Reference template: `LoginScreen.java` / `GoToHomeTest.java`.
4. **Verify**: `build-verify` skill (`mvn clean compile test-compile` green) → rerun the just-fixed test until green.
5. **Report**: root cause, file/layer fixed, how it was verified. Flaky → state the source of nondeterminism + the remedy (wait for a real condition instead of sleeping). Any non-id element touched → Missing ID Report.

> Distinct from the `review-audit` skill (audit only). This is the **fix** skill. To fix a **plan** (a file under `plans/`) do NOT use this skill — update the plan file directly, keeping the standard format.
