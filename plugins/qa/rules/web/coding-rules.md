# Coding Rules — WEB code conventions (Playwright Java) — MANDATORY

## Language & style
- Java 21, UTF-8 encoding. Follow the existing style; 4-space format, no tabs.
- One responsibility per class. Short methods that read like prose. Clear names over abbreviations.
- Comments explain "why", not "what". Explicit `import`, no `import *`. Remove unused imports/fields/variables.

## Locator priority (web) — top-down priority
1. `page.getByRole(AriaRole.X, name("..."))` — **best**, stable, close to the user.
2. `page.getByTestId("...")` — `data-testid` (Playwright `setTestIdAttribute("data-testid")`). Always use `getByTestId(...)`, **do not** write `[data-testid=...]` yourself.
3. `getByLabel(...)` / `getByPlaceholder(...)` / `[name="..."]` — form fields with a stable label/name.
4. `getByText(...)` / `getByRole(HEADING, name(...))` — static title/label (can serve as a key element).
5. Semantic CSS (meaningful) — **last resort**, with a comment explaining why.

### ❌ BAN (red flags in review)
- **xpath-with-index** (`//div[3]`, `(//button)[2]`) and fragile `.nth(n)`.
- **Auto-gen classes**: `.css-1ab2c3` (CSS-in-JS), Tailwind utility classes, `.rs-*` (rsuite) — change every build.
- Locating by **text** for a multi-language app (EN/VI) when you can anchor by id/role — text breaks when the language changes.

> **Keycloak SSO**: the realm Sign in form does NOT have `data-testid` (Keycloak theme, outside the app dev's reach) → anchor by a **stable id that does NOT depend on text**: `#username`, `#password`, `#kc-login`, forgot `a[href*='reset-credentials']`, social `a[href*='/broker/<provider>/']`. This is the `external-sso` group, not test-id debt.

## Waiting & stability (anti-flaky)
- ❌ **`Thread.sleep` is banned** for waiting on UI. Use Playwright auto-wait or `WaitUtils.isVisibleWithin/waitForVisible/waitForHidden`.
- Do not bump timeouts blindly to "make the test pass". Timeouts are centrally configured in `config` (`config.elementTimeout()`/`navigationTimeout()`), no magic numbers scattered in code.
- `isDisplayed()` and every query (`isXxx`) **do not throw** — they return a boolean (try/catch swallows the error → false).

## Locator & interaction
- Locators are declared only as **fields in a Screen**. No `page.locator(...)`/`page.getByRole(...)` in the test layer.
- Action methods are **verbs**, returning `this` (fluent) or the next Screen. Navigating to a new screen → return the new Screen.

## Assertion
- Only in the `tests/` layer. Use `org.testng.Assert` or `PlaywrightAssertions.assertThat`.
- Each assert has a **clear message** stating the expectation + (if useful) the actual value.
- Do not swallow errors with `try/catch` and move on. No `assertTrue(true)`. **Do not relax an assertion to dodge an `[APP-BUG]`** (hiding app bugs = forbidden).

## Missing test-id convention (`data-testid`)
When you declare an element for a Screen that **cannot be anchored by `data-testid`/`id`** (must use text/role-name/css):
1. **Temporarily** use the most stable locator you can find (per the priority above).
2. **MUST** add/update an entry in `missing-test-ids/screens/<id>.json` (`status:"missing"`, with `current`, `suggestedTestId`, `priority`) via **skill `missing-ids`** (the RECORD capability). `<id>` matches the sitemap id.
3. Dev adds the id + the test now uses `getByTestId(...)` → set `status:"resolved"`. Id added on a branch but NOT yet deployed → `status:"pending"` (keep the current locator, wait to verify on the real app before swapping). Keycloak realm → `status:"external-sso"` (does NOT go into export).

## Configuration & secrets
- Do not commit secrets. **Do not print passwords** to logs/reports (`User.toString()` already masks them — keep it).
- Every environment value goes through `ConfigManager`. New key → update `configs/<env>.properties` (+ `.env.example` if secret). The `LOGIN_USERNAME`/`LOGIN_PASSWORD` account is in `.env` (git-ignored).

## Shared state & browser lifecycle (anti-flicker — MANDATORY)
- The Browser/Page is **one window SHARED for the whole run** (`PlaywrightFactory` lazy singleton, serial). A test must not assume naturally clean state — handle its own preconditions/data; feature tests start from Home (`GoToHome`). Auth tests log out themselves in `LoginScreen.open()`.
- **Launch ONCE, close ONCE.** The browser is launched in `BaseTest` `@BeforeSuite(alwaysRun=true)` and closed in `@AfterSuite(alwaysRun=true)` (report flushed, then `PlaywrightFactory.closeAll()`). Between tests, `@BeforeMethod` does **only** `GoToHome.ensure(page)` (navigate the SAME window) — it never opens/closes a browser.
- ❌ **BAN (causes the browser to open/close after each case — flicker):** launching or closing the browser/context/page in `@BeforeMethod`/`@AfterMethod`/`@BeforeClass`/`@AfterClass`; `page.close()`/`context.close()`/`browser.close()` between tests; `new` Playwright/Browser/Context/Page per test/class/Screen; a retry that relaunches the browser. Full spec: [design-pattern.md](design-pattern.md) §7.

## Before finishing
- `mvn -q -B test-compile` must be green (via skill `build-verify`). Re-run the related tests.
- Self-check against [review-checklist.md](review-checklist.md) before requesting a review.
</content>
