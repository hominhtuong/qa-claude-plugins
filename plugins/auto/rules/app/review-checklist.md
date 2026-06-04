# Review Checklist

Checklist for `/review-change` and `/review-codebase`. Each item is marked PASS/FAIL/SKIP.

---

## Severity & Status

| Symbol | Meaning |
|--------|---------|
| ✅ | **PASS** — Meets the standard |
| ❌ | **FAIL** — Violation, must fix before merge |
| ⚠️ | **WARNING** — Should consider fixing |
| ⏭️ | **SKIP** — Not applicable to this file |

| Severity | When |
|----------|------|
| 🔴 **Critical** | Must fix. Security, architecture breakage, runtime error |
| 🟡 **Warning** | Should fix. Anti-pattern, missing validation, wrong convention |
| ℹ️ **Info** | Suggestion for improvement, not mandatory |

| Risk Level | Condition |
|------------|-----------|
| 🔴 **High** | Has >=1 Critical OR changes to core framework (BaseScreen, BaseTest) |
| 🟡 **Medium** | Has Warning but no Critical. Or new Screen/Test is incomplete |
| 🟢 **Low** | Only Info or no issues |

---

## A. Structure & Placement

- [ ] **A1**: Screen class located in `src/main/java/com/example/screens/<group>/`
- [ ] **A2**: Test class located in `src/test/java/com/example/tests/<group>/`
- [ ] **A3**: Screen group name matches between screens/ and tests/ (e.g., `screens/auth/` <-> `tests/auth/`)
- [ ] **A4**: elements.json located in the same folder as Screen class
- [ ] **A5**: Config files located in `configurations/`
- [ ] **A6**: Scripts located in `scripts/`, have `chmod +x`, have shebang (`#!/bin/bash`)
- [ ] **A7**: TestNG XML located in `testng/`

## B. Naming Convention

- [ ] **B1**: Screen class: `<Name>Screen.java` (PascalCase)
- [ ] **B2**: Test class: `<Name>Test.java` (PascalCase)
- [ ] **B3**: Element fields: camelCase + suffix by type (Button, Textfield, Label, ...)
- [ ] **B4**: Test methods: verb + noun, describe behavior (checkUI, testLogin)
- [ ] **B5**: Package: `com.example.screens.<group>` / `com.example.tests.<group>` (group = lowercase)
- [ ] **B6**: Plan folders: lowercase-hyphen (`login-flow`, `onboarding`)
- [ ] **B7**: Methods/variables: camelCase. Classes: PascalCase. Consistent throughout file

## C. Screen Class

- [ ] **C1**: Extends `BaseScreen`
- [ ] **C2**: Constructor: `public <Name>Screen(AppiumDriver driver) { super(driver); }`
- [ ] **C3**: Elements declared as `public WebElement` with `@MobileFindBy`
- [ ] **C4**: Has `isDisplayed()` method
- [ ] **C5**: `isDisplayed()` uses try-catch, returns false on exception
- [ ] **C7**: NO assertions, NO Assert/TestNG imports
- [ ] **C8**: NO direct `driver.findElement()` / `driver.findElements()` calls (use @MobileFindBy)
- [ ] **C9**: Appropriate return types: `void` for actions, `String` for getters, `boolean` for checks
- [ ] **C10**: Method names describe UI actions (e.g., `tapLoginButton()`, `getErrorMessage()`)

## D. Test Class

- [ ] **D1**: Extends `BaseTest`
- [ ] **D2**: `@BeforeClass(alwaysRun = true)` initializes Screen + ExtentTest
- [ ] **D3**: Uses `requireDriver()` (no direct `driver` access during init)
- [ ] **D4**: `@Test(priority = n)` for each test method
- [ ] **D6**: Screenshot at each important step (`Utils.passCap/failCap/infoCap`)
- [ ] **D7**: DataProvider for test data. NO hardcoded test data
- [ ] **D8**: NO direct `driver.findElement()` / `driver.findElements()` calls in Test (use Screen elements)
- [ ] **D10**: Assertions must have descriptive message (e.g., `Assert.assertTrue(result, "Login should succeed")`)
- [ ] **D11**: Each test runs independently, no dependency on other test execution order

## E. Element Locators

- [ ] **E1**: Uses `@MobileFindBy` (NOT `@AndroidFindBy`/`@iOSXCUITFindBy`)
- [ ] **E2**: Locator priority: id -> accessibility -> uiautomator -> text -> className -> xpath
- [ ] **E3**: `xpath` must have a comment explaining the reason
- [ ] **E4**: Platform-specific uses `@MobileFindBys` container
- [ ] **E5**: Elements without `id` must be reported in Missing ID Report
- [ ] **E7**: Variable names clearly describe the UI element (e.g., `loginButton`, NOT `el1`, `btn`)

## F. Wait Strategy

- [ ] **F1**: NO direct `Thread.sleep()` usage
- [ ] **F2**: Use `Utils.delay()` when waiting for animations
- [ ] **F3**: Use `WebDriverWait` for explicit waits
- [ ] **F4**: NO hardcoded timeout values (use config or constants)

## G. TestNG XML

- [ ] **G1**: `GoToHomeTest` is the first `<test>` block
- [ ] **G2**: `preserve-order="true"` on `<suite>` and `<test>`
- [ ] **G3**: `TestResultCollector` listener is declared
- [ ] **G5**: Platform parameter: `<parameter name="platform" value="android|ios"/>`
- [ ] **G7**: Suite name and test name are descriptive (NOT `Suite1`, `Test`)

## H. Configuration

- [ ] **H1**: NO hardcoded paths/URLs/credentials in code
- [ ] **H2**: Config uses PropertyReader, NO direct file reading
- [ ] **H3**: Secrets only in .properties files (NOT committed to repo)
- [ ] **H4**: Required capabilities are complete (platformVersion, deviceName, ...)
- [ ] **H5**: Timeout values are reasonable — not too short or too long

## I. Reporting

- [ ] **I1**: ExtentTest created via `extentReport.getExtentTest()`
- [ ] **I2**: Child nodes via `report.createNode()`
- [ ] **I3**: Screenshots use `Utils.takeScreenshot()` — relative path
- [ ] **I4**: Status helpers: `passCap`, `failCap`, `infoCap`

## J. Code Quality

- [ ] **J1**: No unused imports
- [ ] **J2**: No unused variables
- [ ] **J3**: No duplicate code (extract to Screen method if used multiple times)
- [ ] **J4**: Comments in English or Vietnamese
- [ ] **J5**: No over-engineering (simple > complex)
- [ ] **J6**: Clean compilation (mvn compile test-compile)
- [ ] **J7**: No large commented-out code blocks (>5 lines) — delete instead of commenting
- [ ] **J8**: NO `System.out.println()` — use Logger/FLog
- [ ] **J9**: TODO/FIXME must include a ticket number
- [ ] **J10**: No wildcard imports (`import java.util.*;`)

## K. Documentation Sync

- [ ] **K1**: Structure changes -> update CLAUDE.md
- [ ] **K2**: Structure changes -> update README.md + README-vi.md
- [ ] **K3**: TestNG class changes -> update testng-*.xml
- [ ] **K4**: New elements via MCP -> update sitemap.xml
- [ ] **K5**: Complex logic has explanatory comments

---

## File -> Checklist Mapping

| File type | Checklist groups |
|-----------|-----------------|
| Screen class (`screens/**/*.java`) | **A, B, C, E, F, I, J** |
| Test class (`tests/**/*.java`) | **A, B, D, F, I, J** |
| elements.json | **A4, E** |
| TestNG XML (`testng-*.xml`) | **G** |
| Config (`.properties`) | **H** |
| Script (`.sh`) | **A6** |
| Documentation (`.md`) | **K** |
| Other files | **J** |


