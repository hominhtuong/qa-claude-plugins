---
name: cook-web
description: Reusable logic to write/maintain a Playwright Java Page Object (Screen) + <Feature>Tests class + smoke/regression runner following the 3-layer POM, with correct locator priority and isDisplayed(), and NO assert in the Screen. Used by the cook/plan-tests command (creating a new feature or extending one). Hooks the missing-ids skill for elements lacking data-testid; verifies via the build-verify skill.
---

# Skill: cook-web

Reusable capability: from the element catalog (`find-elements-web` skill) + plan → code following the 3-layer POM correctly. Standards: [design-pattern.md](../../rules/web/design-pattern.md), [coding-rules.md](../../rules/web/coding-rules.md), [design-system.md](../../rules/web/design-system.md).

## Procedure
1. **Identify the feature** (`<feature>` slug → camel package) + the list of screens. One sub-screen = **one separate Screen**.
2. **Screen** (`src/main/java/.../screens/<feature>/<Name>Screen.java`):
   - `extends BaseScreen`; constructor takes `Page` via `super(page)`.
   - Declare locators as **fields** by role (camelCase: `submitButton`, `amountInput`), chosen by priority `getByRole > getByTestId > getByLabel/Placeholder/[name=] > getByText/heading > semantic CSS`. NO xpath-index, `.nth()`, auto-generated classes.
   - Set `screenKeyLocator()` = 1 key element (heading/marker, language-proof).
   - Action methods are **verbs**, return `this` (fluent) or the next Screen; navigation → return the new Screen.
   - Queries (`isXxx`) return a boolean, never throw an exception; wait with `WaitUtils.isVisibleWithin(..., config.elementTimeout())`, **NO `Thread.sleep`**.
   - **ZERO assertions** in the Screen.
3. **Element missing `data-testid`/`id`** → temporarily use the best available locator + RECORD via the `missing-ids` skill (`status:"missing"` + `suggestedTestId`). Keycloak realm → `external-sso`.
4. **`<Feature>Tests`** (`src/test/java/.../tests/<feature>/<Feature>Tests.java`): `extends BaseTests`, takes `Page` via `super(page)`, **NO `@Test`**. Each method = 1 scenario, calls `screen(Class)` + contains **ALL assertions** (`org.testng.Assert`) with a message clearly stating the expectation + the actual value. Tests must be **DEEP** (design-pattern §2b): cross-checked figures match the source, click-through asserts a URL/heading change, expander reveals more data — not just `isDisplayed()`.
5. **Runner**: `smoke/<feature>/<Feature>SmokeTest.java` (`extends BaseSmokeTest`) + `regressions/<feature>/<Feature>RegressionTest.java` (`extends BaseRegressionTest`) — only `@Test(groups=...)` methods that call back into the functions in `Tests` (auth feature → `extends BaseTest`). Register into the suite `configs/suites/*.xml`.
   - **Browser lifecycle — ONE window per run (anti-flicker, MANDATORY):** if you create/touch `core/PlaywrightFactory` or `base/BaseTest`, the browser MUST launch **once** in `BaseTest` `@BeforeSuite(alwaysRun=true)` (lazy-singleton `PlaywrightFactory.getPage()`) and close **once** in `@AfterSuite(alwaysRun=true)` (flush report → `PlaywrightFactory.closeAll()`). `BaseRegressionTest`/`BaseSmokeTest` `@BeforeMethod` does **only** `GoToHome.ensure(page)`. **NEVER** launch/close a browser/context/page in `@BeforeMethod`/`@AfterMethod`/`@BeforeClass`/`@AfterClass`, and never `new`/`close` a Browser per test/class/Screen — that flickers the window open/close each case. Full spec: [design-pattern.md](../../rules/web/design-pattern.md) §7.
6. **Update the sitemap** node `sitemap/screens/<id>.json` for the screen just built.
7. **Verify**: `build-verify` skill (`mvn -q -B test-compile` green) → re-run the class just written until green.

> This skill WRITES code; checking conformance is the `review-audit` skill, fixing errors is the `fix-by-layer` skill. Reference templates: `LoginScreen.java` / `LoginTests.java` / `LoginRegressionTest.java`.
