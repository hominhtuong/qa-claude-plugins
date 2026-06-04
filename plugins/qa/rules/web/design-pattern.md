# Design Pattern — WEB test architecture (Playwright Java) — MANDATORY

Framework: **Playwright Java + TestNG + Page Object Model (POM)**, Java 21 + Maven, organized **package-by-feature** so each member can work independently with fewer merge conflicts. One shared `Page` for the whole run (serial), managed by `PlaywrightFactory`; `setTestIdAttribute("data-testid")`.

## 1. Layers and responsibilities

```
src/main/java/<base.package>/
├── config/     ConfigManager, Environment        — read .env + configs/, account/base.url/login.url/home.path
├── core/       PlaywrightFactory                 — browser lifecycle: 1 SHARED Playwright/Browser/Context/Page for the whole run
│               AppState, AppStateDetector        — detect the screen (HOME/LOGIN/UNKNOWN) for GoToHome
├── flows/      GoToHome                          — precondition: guarantee back to Home from any state
├── utils/      Log, WaitUtils, DataGenerator     — pure helpers, no feature dependency
├── models/     User, ...                         — pure DATA (record), no Playwright, no assert
├── sitemap/    SitemapNode, SitemapManager       — read/write the screen map (per-screen JSON)
└── screens/
    ├── base/   BaseScreen                        — shared contract + isDisplayed()/isDisplayedNow()
    └── <feature>/ <Name>Screen.java              — Page Object: Locator fields + actions (verbs), NO assert

src/test/java/<base.package>/
├── base/         BaseTest          — browser lifecycle (sharedPage), used by ALL tests
│                 BaseRegressionTest — extends BaseTest + GoToHome.ensure before each test (feature regression)
│                 BaseSmokeTest      — extends BaseRegressionTest (smoke reuses the regression flow)
│                 TestData, listeners (Report/Sitemap/Retry)
├── tests/        BaseTests          — base for ALL <Feature>Tests: holds page/config, screen(Class), log/report
├── tests/<feature>/   <Feature>Tests.java        — extends BaseTests; a LIBRARY of test functions (with assertions), NO @Test
├── smoke/<feature>/   <Feature>SmokeTest.java    — @Test(groups="smoke"), CALLS BACK the critical-path functions
└── regressions/<feature>/ <Feature>RegressionTest.java — @Test(groups="regression"), CALLS BACK everything
```

**Golden rules — never violate:**
- A **Screen** only knows "what the screen has" + "what it can do" → declares `Locator` fields + action methods (verbs). **Absolutely no assert** in a Screen.
- **tests/** is the ONLY place holding assertions. Each `<Feature>Tests` **extends `BaseTests`** (sharing `page`/`config`/`screen(Class)`/log-report), receiving the `Page` via `super(page)`. Each method = 1 scenario. **NO `@Test`** in this class.
- **smoke/** and **regression/** contain NO logic/locator — only `@Test` calling back function names in `tests/`. Smoke = critical-path subset; Regression = full.
- **models/** is just data; **config/core/utils** are shared across all features.

## 2. GoToHome — mandatory precondition

- `flows/GoToHome.ensure(page)` GUARANTEES being at **Home** (the post-login app shell) from ANY state: `navigate(home.url)` → loop `detect AppState → handle` until reaching Home (screenshot as proof).
  - **HOME** → screenshot proof, return.
  - **LOGIN** (Keycloak Sign in form) → log in automatically (`#username`/`#password`/`#kc-login`) → realm redirect `/auth/callback` → app.
  - **UNKNOWN** (redirecting/loading) → settle + re-navigate Home.
- Owned by the **lead**; members treat Home as the starting point. `BaseRegressionTest`/`BaseSmokeTest` call `ensure(page)` before each test, using the `home` field. New Keycloak state detected (OTP/consent/password change) via `/exploratory` → extend the `switch` + `AppState`/`AppStateDetector`, do NOT patch in the test.
- **Auth feature** (login; forgot/sign-out) is a SEPARATE feature whose tests drive the flow themselves → `extends BaseTest` (NO GoToHome, to avoid recursion).

## 3. Screen contract: `isDisplayed()`

Each Screen `extends BaseScreen` and implements `screenKeyLocator()` — **one key element** proving the screen is displayed (heading/app-shell marker), language-proof (prefer `data-testid`/role-heading). `isDisplayed()` derives from it via `WaitUtils.isVisibleWithin`, and **never throws**. Tests use `screen.isDisplayed()` to check navigation.

## 4. Page Object Model

- Every `Locator` is declared as a **field in a Screen**. **Do not** scatter selectors (`page.locator(...)`, `page.getByRole(...)`) across the test layer.
- Action methods use **verbs** (`enterUsername`, `submit`, `openOrder`), returning `this` (fluent) or the next Screen. Navigating to a new screen → return a **new Screen** (e.g. `LoginScreen.submit()` returns `HomeScreen`).

## 5. Tests must be DEEP — not just "the screen is displayed" (MANDATORY)

`isDisplayed()` is only a necessary condition. For each screen/block you must verify real behavior & data:

- **Numbers = highest priority**: every figure (metric, total, count) must be **cross-checked against its source** — open/navigate to the corresponding feature to compare, or cross-check internally (e.g. the metric "Đơn hàng hôm nay" == the number of list rows after fully expanding). **Wrong numbers are the worst kind of bug.** Read the value **dynamically** via locator, do NOT hard-code live numbers.
- **Clickable block → opens the correct sub-screen**: click a block/button/"Xem tất cả"/menu then assert it OPENS THE CORRECT sub-screen/modal — **URL change and/or a new heading** — not just asserting the element exists.
- **"Xem thêm"/expander → reveals more data**: assert the row count grows by the promised amount (e.g. "Xem thêm (7)" → +7), "Xem tất cả" → opens the full screen.
- **Badge/notification/count → matches state**: work pending ⟺ positive badge; cleared ⟺ all-clear/0; count matches the list.
- Read dynamically, tolerate empty-state.

## 6. Package-by-feature (conflict avoidance)

A member **owns the whole** `screens/<feature>`, `tests/<feature>`, `smoke/<feature>`, `regressions/<feature>` (same package name across both the `src/main` and `src/test` trees). Shared code (`base`/`config`/`core`/`utils`) **rarely changes** — edit minimally, extend without breaking the API.

> Naming standard & locator: [design-system.md](design-system.md). Code rules: [coding-rules.md](coding-rules.md). Review checklist: [review-checklist.md](review-checklist.md). Failure triage: [failure-triage.md](../failure-triage.md).
</content>
