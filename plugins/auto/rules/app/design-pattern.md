# Design Pattern — Test architecture (MANDATORY)

Framework: **Appium Java Client + TestNG + Page Object Model (POM)**, multi-platform **Android · iOS · Flutter** (the Sổ Bán Hàng app is written in Flutter). Organized **package-by-feature** (`screens/<group>` ↔ `tests/<group>`) so each member can work independently with fewer merge conflicts.

> Golden rule: **Screen** (locators `@MobileFindBy` + actions, NO assert) → **tests/** (test flow + assertion + reporting) → **regression/smoke** (aggregate flow extending `BaseRegression`). Each Screen has `isDisplayed()` based on one characteristic element. Locators live only in the Screen. No hard-coding/secret/`Thread.sleep`. Every test starts from **Home**.

## 1. Layers and responsibilities

```
src/main/java/com/example/
├── appium/    AppiumServer                         — Appium server lifecycle
├── actions/   MobileActions                        — swipe, tap, OTP… (shared interaction helpers)
├── models/    Capabilities, Environment, UserInfo  — pure DATA, no assert
├── utils/     PropertyReader, Utils, MobileFindBy,  — pure helpers; Utils.recoverToHome(),
│              MobileFindFieldDecorator, ExtentReport,  takeScreenshot, FLog
│              FLog
└── screens/
    ├── base/      BaseScreen                        — shared contract + decorator timeout
    └── <group>/   <Name>Screen.java                 — Page Object: @MobileFindBy + actions, NO assert
                   elements.json                      — element catalog (MCP-managed, persisted)
                   test-hints.json                    — field metadata + business rules (for /plan-tests, /cook)

src/test/java/com/example/tests/
├── base/         BaseTest         — driver lifecycle, ExtentReport, @AfterMethod screenshot
│                 BaseRegression   — extends BaseTest + auto recoverToHome before/after each @Test
│                 TestDataProvider
├── auth/         GoToHomeTest · OnboardingTest · LoginTest   — extends BaseTest (PATH back to Home)
├── <feature>/    <Name>Test.java  — ATOMIC test, extends BaseTest (single purpose)
├── regression/<feature>/  <Name>Test.java — aggregate flow, extends BaseRegression
└── smoke/<feature>/       <Name>Test.java — critical-path subset, extends BaseRegression
```

**Golden rules — never violate:**
- A **Screen** only knows "what the screen has" and "what it can do" → declares `@MobileFindBy` + action methods (verbs). **Absolutely no assert** in a Screen, no TestNG imports.
- **tests/** is the ONLY place holding assertions + ExtentReport + screenshots. Each Test class extends `BaseTest` (atomic) or `BaseRegression` (aggregate flow), initializing Screens in `@BeforeClass(alwaysRun=true)` via `requireDriver()`.
- **models/** is just data; **utils/actions/appium** are shared across all features and rarely change.

## 2. Element Lookup Chain (3-layer) — MANDATORY before writing code

```
Screen.java  →  elements.json  →  Appium MCP (source-inspector agent)
```
1. **Layer 1 — Screen.java**: is a `@MobileFindBy` field already declared? → use it directly.
2. **Layer 2 — elements.json**: is it in the catalog `screens/<group>/elements.json`? → add it to the Screen then use it.
3. **Layer 3 — MCP discovery**: not there yet → check device → spawn the **agent `source-inspector`** to discover from the real app → you **MUST** save it to `elements.json` for reuse.

Skill-ized detail: skill `find-elements-android`/`-ios` (pick a stable locator) + skill `declare-screen` (write the Screen). After Layer 3 you must run skill `update-sitemap`.

## 3. Screen contract: `isDisplayed()`

Each Screen extends `BaseScreen`, constructor `public <Name>Screen(AppiumDriver driver){ super(driver); }`. It **MUST** have:
```java
public boolean isDisplayed() {
    try { return primaryElement.isDisplayed(); }
    catch (Exception ignored) { return false; }
}
```
`primaryElement` = the most characteristic element, always visible when the screen is active. `isDisplayed()` never throws. Tests use `screen.isDisplayed()` to check navigation.

**Fast probe** for back-loop/reset (false-negative acceptable): declare a `probe = true` field as `List<WebElement>` (skips the 5s polling, returns immediately ~50ms), used by `isDisplayedFast()`. Do NOT use `probe` for assertions. Detail: [coding-rules.md](coding-rules.md).

## 4. Home Prerequisite & recovery (MANDATORY)

- **Every test starts from Home.** The TestNG XML always has `com.example.tests.auth.GoToHomeTest` as the **first `<test>` block** (it handles Onboarding + Login if needed).
- **`Utils.recoverToHome(driver)`** (`src/main/java/com/example/utils/Utils.java`) — a 2-stage cross-platform safety net:
  - **Stage A — whitelist scan**: hide keyboard → dismiss popup/dialog (close/cancel/confirm ids + VN labels) → iOS `nav_tab_management`/`back_button` → `navigate().back()` (loop until `home_screen` appears).
  - **Stage B — restart app** (when A fails): `terminateApp` + `activateApp` + wait for `RUNNING_IN_FOREGROUND` + tap-through Splash (`btn_login`) & DataSync (`btn_skip_sync`).
- **Automatic via `BaseRegression`**: `@BeforeMethod ensureOnHomeBeforeTest` + an after-test hook calls `recoverToHome` before/after each `@Test` (after PASS/FAIL screenshots are taken). **Skipped for `tests/auth.*`** (those ARE the path back to Home). No-op (~50ms) when already at Home.
- **Implication when writing new regression/smoke**: extend `BaseRegression` (not `BaseTest`). ❌ Do NOT write your own `@BeforeMethod ensureOnHome` per class. ❌ Do NOT wrap `navigateBackToHome()` in try/catch at the end of each test — the hook handles it. ✅ Only write the test body.
- **Atomic** tests in `tests/<feature>/` extend `BaseTest` directly → NO recovery hook (call `Utils.recoverToHome` manually if a hard reset is needed).
- Reference: `src/test/java/com/example/tests/recovery/RecoverToHomeTest.java` · suite `testng/testng-recover-to-home.xml`.

## 5. Sitemap (for AI navigation) — read BEFORE every task

```
sitemap/sitemap.md          → ALWAYS READ: navigation index, screen lookup, entry points
sitemap/test-playbook.md    → READ WHEN PLANNING: test patterns + cross-screen journeys
screens/<group>/test-hints.json → READ WHEN IMPLEMENTING: field metadata + business rules
screens/<group>/elements.json   → READ WHEN CODING: element locators (MCP-managed)
sitemap/screenshots/        → multimodal reference (JPG/screen)
```
**Auto-update** after MCP discovery / element change (skill `update-sitemap`): update `elements.json`, `test-hints.json`, `sitemap/sitemap.md`, then regenerate with `python3 sitemap/scripts/gen_sitemap_v2.py` + `gen_test_hints.py`. Detail: `sitemap/README.md`.

## 6. Package-by-feature (conflict avoidance)

Each feature = one **group** (`auth`, `home`, `product`, `order`…). A member owns the whole of `screens/<group>` + `tests/<group>`. Group names **lowercase**; Screen/Test **PascalCase**. Shared code (`base`, `utils`, `actions`, `models`) rarely changes — edit minimally, extend without breaking the API.

## 7. Running tests

- Scripts (recommended, self-check device): `./scripts/run-android.sh` · `./scripts/run-ios.sh` · `./scripts/run-all.sh`.
- Maven: `mvn test -DsuiteXmlFile=testng/testng-android.xml` (or `-ios`/`-all`).
- Compile: `mvn clean compile test-compile` (always run before finishing — skill `build-verify`).

> Naming standard & locator: [design-system.md](design-system.md). Java code rules: [coding-rules.md](coding-rules.md). Review checklist: [review-checklist.md](review-checklist.md). Common issues: [troubleshooting.md](troubleshooting.md).
</content>
