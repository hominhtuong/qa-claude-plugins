# Review Checklist — WEB (Playwright Java) — used by `/review-code`

Check each item. Levels: 🔴 Blocker (must fix) · 🟡 Should fix · 🟢 Suggestion. Any 🔴 ⇒ conclusion **NEEDS FIX**.

## A. Layering (design-pattern)
- [ ] 🔴 Screen contains **no** assertion (`assert*`, `assertThat`).
- [ ] 🔴 Assertions live **only** in `tests/`.
- [ ] 🔴 `<Feature>Tests` has **NO** `@Test` (only smoke/regression have `@Test`).
- [ ] 🔴 `smoke/` and `regressions/` **only call back** functions in `tests/`, no embedded logic/locator.
- [ ] 🔴 Files are in the correct feature package; no out-of-scope changes spilling into other features.
- [ ] 🟡 Smoke is a critical-path subset; Regression covers everything.

## A2. GoToHome / base / sitemap
- [ ] 🔴 Feature flow: regression `extends BaseRegressionTest`, smoke `extends BaseSmokeTest`; auth (login; forgot/sign-out) + GoToHome test `extends BaseTest`.
- [ ] 🔴 Do not re-implement login/back-to-Home logic in a feature test — use `GoToHome.ensure`/the `home` field.
- [ ] 🟡 Each screen created/edited has its corresponding `sitemap/screens/<id>.json` node updated.
- [ ] 🟡 Account/credential/URL come from `ConfigManager`/`TestData`, not hard-coded.

## A3. Browser lifecycle — ONE window per run (anti-flicker, design-pattern §7)
- [ ] 🔴 Browser is launched **once** in `BaseTest` `@BeforeSuite(alwaysRun=true)` (lazy-singleton `PlaywrightFactory.getPage()`) and closed **once** in `@AfterSuite(alwaysRun=true)` (flush report → `PlaywrightFactory.closeAll()`).
- [ ] 🔴 **No** browser/context/page launch or close in `@BeforeMethod`/`@AfterMethod`/`@BeforeClass`/`@AfterClass`; no `page.close()`/`context.close()`/`browser.close()` between tests; no `new` Playwright/Browser/Context/Page per test/class/Screen (these flicker the window open/close each case).
- [ ] 🔴 `@BeforeMethod` in `BaseRegressionTest`/`BaseSmokeTest` does **only** `GoToHome.ensure(page)` (navigate the same window) — it does not (re)create a browser.
- [ ] 🟡 Suite runs serial/single-window (`*-serial.xml`, `thread-count=1`, no parallel) so one browser serves every test; the Retry listener reuses the same page (no relaunch).

## B. Page Object Model
- [ ] 🔴 Screen `extends BaseScreen` and implements `screenKeyLocator()` with a sensible key element (language-proof).
- [ ] 🔴 Screen has `isDisplayed()` (derived from `screenKeyLocator()`, via `BaseScreen`, never throws).
- [ ] 🔴 No `page.locator(...)` / `page.getByRole(...)` in the test layer — locators are declared as fields in a Screen.
- [ ] 🟡 Action methods are verbs, returning `this` or the next Screen; navigating to a new screen returns a new Screen.
- [ ] 🟡 Queries (`isXxx`) return a boolean, never throw.

## C. Locator & stability (design-system)
- [ ] 🔴 No `Thread.sleep` for waiting on UI (use `WaitUtils`/auto-wait).
- [ ] 🔴 No `page.locator()` xpath-with-index or fragile `.nth(n)`.
- [ ] 🟡 Locator priority `getByRole > getByTestId > getByLabel/Placeholder/[name=] > getByText/heading > semantic CSS`; avoid auto-gen classes (`.css-*`, Tailwind util, `.rs-*`).
- [ ] 🟡 Keycloak realm elements anchored by a stable id (`#username`/`#password`/`#kc-login`/href broker), NOT by text.
- [ ] 🟡 No arbitrary timeout bumps; timeouts come from `config`.
- [ ] 🟡 **Missing test-id**: an element that can't be anchored by `data-testid`/`id` (using text/role-name/css/xpath/nth) has a `status:"missing"` entry in `missing-test-ids/screens/<id>.json` (via skill `missing-ids`; design-system §3b). Keycloak realm → `external-sso`.

## D. Configuration & secrets (coding-rules)
- [ ] 🔴 No hard-coded URL/credential in a test → use `ConfigManager`/`TestData`.
- [ ] 🔴 No committed secrets; **no logging passwords**.
- [ ] 🟡 New config keys are in `configs/<env>.properties` (+ `.env.example` if secret).

## E. Naming & style
- [ ] 🟡 Screen/field/method/test names follow [design-system.md](design-system.md).
- [ ] 🟡 Explicit imports, no unused field/variable/import.
- [ ] 🟢 Comments explain "why", at a reasonable density.

## F. Build & evidence
- [ ] 🔴 `mvn -q -B test-compile` green (via skill `build-verify`).
- [ ] 🟡 Related tests have been run (or a reason given why they couldn't run).
- [ ] 🟡 **Mandatory evidence**: each smoke/regression test, on completion, has a **screenshot attached to ExtentReport — on pass AND fail** + records the **URL** at the end (the reader can verify the automation actually ran). Do not disable unless there is a reason.

## H. Test depth (NOT just "the screen is displayed")
> Displaying the right screen is only a necessary condition. A test that only asserts `isDisplayed()` is **too shallow** — flag 🟡 (🔴 if the screen has important numbers/navigation that are completely skipped).
- [ ] 🔴 **Numbers must be cross-checked**: figures on the screen (metric/total/count) verified against their source — open/navigate to the corresponding feature to compare, or cross-check internally. Wrong numbers = the worst kind of bug, must not be skipped.
- [ ] 🟡 **Clickable block → opens the correct sub-screen**: each clickable block/button/menu/"Xem tất cả" has a click test + asserts **URL change / new heading**, not just that the button exists.
- [ ] 🟡 **"Xem thêm"/expander must reveal more data**: assert the row count grows by the promised amount (e.g. "Xem thêm (7)" → +7), "Xem tất cả" opens the full screen.
- [ ] 🟡 **Badge/count/notification must match state**: work pending ⟺ positive badge; cleared ⟺ all-clear/0; count matches the list.
- [ ] 🟡 Tests read values **dynamically** & tolerate empty-state; do NOT hard-code live numbers.

---
**Finding format:** `path:line` — level — rule violated — **actual code** that's wrong + **fix code**. Order Blockers first. Conclusion: PASS / NEEDS FIX + count by level + an aggregated Missing ID Report. Failure triage (if related to run results): [failure-triage.md](../failure-triage.md).
</content>
