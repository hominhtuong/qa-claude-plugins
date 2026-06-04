# Design System — WEB naming, structure & locator standard (MANDATORY)

The test suite's "design system": the set of conventions that make every file look like it was written by **one person**. Consistency = easier to review, maintain, and merge.

## 1. Directory map for a new feature (`<feature>` = kebab slug → camel package)

| Layer | Path | Class name |
|---|---|---|
| Screen | `src/main/java/<base.pkg>/screens/<feature>/` | `<Name>Screen` (e.g. `OrderListScreen`) |
| Model | `src/main/java/<base.pkg>/models/` | noun (`Order`, `Product`) — `record` |
| Test functions | `src/test/java/<base.pkg>/tests/<feature>/` | `<Feature>Tests` |
| Smoke | `src/test/java/<base.pkg>/smoke/<feature>/` | `<Feature>SmokeTest` |
| Regression | `src/test/java/<base.pkg>/regressions/<feature>/` | `<Feature>RegressionTest` |

> One sub-screen = one separate Screen (`OrderListScreen`, `OrderDetailScreen`) — don't cram multiple screens into one class. Maven splits `src/main`/`src/test`; the "feature folder" is expressed by the **same package name** across both trees.

## 2. Naming conventions

- **Package**: one word, by domain (`auth`, `orders`, `products`, `dashboard`).
- **Screen field (locator)**: camelCase by **UI role**, NOT by selector. ✅ `usernameInput`, `submitButton`, `overviewHeading`. ❌ `btn1`, `inputName`.
- **Action method**: present-tense verb. ✅ `enterUsername`, `submit`, `openOrder`. Boolean query: `isDisplayed`, `isSubmitEnabled`, `hasInvalidCredentialsError`.
- **Test function (tests/)**: describes the scenario, camelCase. ✅ `loginWithValidCredentials`, `rejectWrongPassword`, `submitNewOpensFormPicker`.
- **Smoke/regression method**: same name (or very close to) the test function it calls, for traceability.
- **Constants**: `UPPER_SNAKE`. **Config key**: dotted `base.url`; the corresponding env var `BASE_URL`.

## 3. Locator strategy (top-down priority)

1. `page.getByRole(AriaRole.X, name("..."))` — most stable, closest to the user.
2. `page.getByTestId("...")` — `data-testid` (`setTestIdAttribute("data-testid")` in `PlaywrightFactory`).
3. `getByLabel(...)` / `getByPlaceholder(...)` / `[name="..."]` — form fields.
4. `getByText(...)` / `getByRole(HEADING, name(...))` — static title/label (used as a key element).
5. Semantic CSS (meaningful) — last resort, with a comment.
6. ❌ **BAN**: xpath-with-index, fragile `.nth(n)`, auto-gen classes (`.css-1ab2c3`, Tailwind util, `.rs-*`).

A locator is declared **once** as a field in a Screen. Multi-language app (EN/VI) → prefer id/role so it doesn't break when the language changes. Keep accented text as Unicode when forced to use it (e.g. `"Đăng nhập"`).

## 3b. Test-id & "missing-test-ids" (MANDATORY)

The most durable anchor is a stable `data-testid`/`id`. **Why not rely on text/xpath**: the app is **multi-language** ⇒ text locators fail; fields **show/hide by tenant/plan/permission** ⇒ rigid xpath, `.nth()`, and auto-gen classes fail.

When you declare an element for a Screen that **cannot be anchored by `data-testid`/`id`**:
1. **Temporarily** use the most stable locator (per priority in section 3).
2. **MUST** add/update `missing-test-ids/screens/<id>.json` (`status:"missing"` + `current` + `suggestedTestId` + `priority`) via **skill `missing-ids`** (RECORD). `<id>` matches the sitemap id.
3. Dev adds the id + the test now uses `getByTestId(...)` → `status:"resolved"`.

**Statuses**: `missing` (dev needs to add — goes into export) · `pending` (id added on a branch, NOT yet deployed → keep the current locator, wait to verify on the real app before swapping; a blind swap makes the suite pass green while silently failing) · `resolved` (id LIVE + test migrated, verified) · `external-sso` (Keycloak realm elements `#username`/`#password`/`#kc-login` — impossible to inject, does NOT go into export). EXPORT (skill `missing-ids`) gathers the `missing` entries → `export.json` to send to dev.

## 4. How to choose `screenKeyLocator()`

- An element that **always appears & is unique** when the screen is shown: a heading/title or app-shell marker. Prefer `data-testid`/role-heading (language-proof). E.g. `LoginScreen` (Keycloak) → `#kc-login`; `HomeScreen` → app-shell marker (testid).
- Avoid elements that may be hidden by loading/empty-state or covered by an overlay (onboarding tour).

## 5. Data & configuration

- Do not hard-code URL/credential/timeout in a test → get them from `ConfigManager`/`TestData`.
- Secrets (username/password) in `.env` (git-ignored). Non-sensitive defaults in `configs/<env>.properties` (`base.url`/`login.url`/`home.path`/timeouts). Create data via `TestData` (factory) + `DataGenerator` (random).
- **Login = Keycloak SSO** (OIDC+PKCE): app → realm → Sign in form (`#username`/`#password`/`#kc-login`) → `/auth/callback` → app. To skip the login UI → bypass via API/storageState.

## 6. Sitemap (per-screen JSON)

Each screen = one file `sitemap/screens/<id>.json` (each member owns their own ⇒ fewer conflicts). `/exploratory`/`/plan-tests`/`/cook` create/update a node when they touch a screen (fields: `realName`, `testFeature`, `screenClass`, `route`, `parentId`, `childrenIds`, `keyElement`, `reach`, `notes`). The merged file `sitemap/sitemap.json` is regenerated by a listener on each run — do NOT edit by hand.

## 7. TestNG suites & reporting

- Suites in `configs/suites/*.xml`: `smoke.xml`/`regression.xml` (parallel) + `*-serial.xml` (serial — recommended, clean green report) + per-feature (`auth-regression.xml`). Adding a new feature → register the class in the matching suite.
- **Each run = one directory** `results/tests/<ddMMMyyyy>/<runTs>/`: ExtentReports Spark HTML + `screenshots/` (pass & fail) + `traces/` + `videos/`. Each test embeds a screenshot of both states + **the URL at the end**. Do NOT write artifacts to top-level `results/`. End of run: push R2/S3 + notify (enabled in `.claude/qa-claude/.env`).

> Overall architecture: [design-pattern.md](design-pattern.md). Code rules: [coding-rules.md](coding-rules.md). Review checklist: [review-checklist.md](review-checklist.md).
</content>
