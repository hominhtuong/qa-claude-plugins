---
name: cook-app
description: Engine that writes mobile test code (Appium Java + TestNG + POM), used by the cook command when the platform is android/ios. Covers 3-layer element lookup, Screen declaration (via the declare-screen skill), writing atomic/flow Tests, TestNG XML (GoToHomeTest first), Utils.passCap/failCap with the [APP-BUG] triage label, build verification, sitemap updates, and recording elements missing an id. Keeps the cook command a thin router.
---

# Skill: cook-app

Reusable capability: from `plans/<feature>/plan.md` → standards-compliant POM Appium Java code that compiles green. The `/cook` command routes to this skill when the platform is **android/ios** (web → `cook-web` skill). Source standards (read BEFORE writing): [design-pattern.md](../../rules/app/design-pattern.md), [coding-rules.md](../../rules/app/coding-rules.md), [design-system.md](../../rules/app/design-system.md).

## Procedure
1. **GATE app-correct**: only cook features/sub-features that passed exploratory cleanly (no `[APP-BUG]`). Parts currently broken → do NOT write tests; leave the bug report for the dev.
2. **Element 3-layer lookup** ([design-pattern §lookup](../../rules/app/design-pattern.md)): **Screen.java** (field already exists?) → **`screens/<group>/elements.json`** (catalog?) → if missing, **MCP discovery**: open the screen via the `navigate-app` skill, spawn the `source-inspector` agent, pick the locator via the `find-elements-android` skill (android) or `find-elements-ios` skill (ios). Do NOT probe blindly when a catalog already exists.
3. **Declare Screen** — delegate to the **`declare-screen` skill**: `BaseScreen`, `@MobileFindBy` fields following the platform's locator priority, `isDisplayed()` (try-catch on 1 element), action = verb, **NO assert**. Elements missing an id → flag for step 7.
4. **Write Test class**:
   - Atomic test (1 behavior) → `extends BaseTest`, package `tests/<group>`, 1 method = 1 scenario + assertion.
   - Flow/regression (composing multiple steps) → `extends BaseRegression`; recover back to Home between steps.
   - Interact via Screen actions; assert ONLY in the Test. NO `driver.findElement()` in the Test, NO arbitrary `Thread.sleep`.
5. **TestNG XML** (`testng/<group>.xml`): `GoToHomeTest` is the **first** `<test>` block, then the feature tests in dependency order.
6. **Reporting + triage**: use `Utils.passCap(driver, test, msg)` / `Utils.failCap(driver, test, msg)` (screenshot + ExtentReport). FAIL suspected to be an app fault → attach the **`[APP-BUG]`** label ([failure-triage.md](../../rules/failure-triage.md)): reproduce on the real app → if the app is genuinely broken, keep the test honest (truly red / mark known-defect with a ticket); do NOT loosen the assertion to hide the bug.
7. **Post-processing**: **`build-verify` skill** (`mvn clean compile test-compile` green) → **`update-sitemap` skill** (sitemap + elements.json + test-hints.json) → non-id elements recorded via the **`missing-ids` skill** (RECORD + EXPORT).

> This skill ONLY writes mobile code; compile/runtime errors that arise → fix via the `fix-by-layer` skill. Planning is the `plan-method` skill. Commit when the user requests → `commit-push` skill.
