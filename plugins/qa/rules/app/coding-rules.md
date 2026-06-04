# Coding Rules — Java code conventions (MANDATORY)

Code standard for every Java file in the project. Overall architecture: [design-pattern.md](design-pattern.md). Naming standard & locator strategy: [design-system.md](design-system.md).

## Language & style
- Java 16+, UTF-8 encoding. Follow the existing style; mirror the reference file.
- One responsibility per class. Short methods, clear names. Comments explain "why", keep the density of the surrounding code (English or Vietnamese).
- Explicit `import`, no `import *`. Remove unused imports/fields/variables.
- Prefer editing existing files over creating new ones; keep code simple, avoid over-engineering.

## Element declaration — `@MobileFindBy`
- **Always** use `@MobileFindBy` (NOT separate `@AndroidFindBy` + `@iOSXCUITFindBy`). Use `@MobileFindBys` only when each platform needs a different locator.
- **Locator priority (in order):**
  1. `id` — **best**, cross-platform (resourceId Android / accessibilityId iOS).
  2. `accessibility` — cross-platform (content-description / accessibilityIdentifier).
  3. `uiautomator` — Android-only when there is no id/accessibility.
  4. `xpath` — **last resort**, MUST comment the reason no better locator exists.
- **NEVER** call `driver.findElements()` directly in a Screen — always declare a `List<WebElement>` with `@MobileFindBy`.

```java
// Priority 1: id (BEST — cross-platform)
@MobileFindBy(id = "btn_back")
public WebElement backButton;

// Priority 2: accessibility
@MobileFindBy(accessibility = "Nhập số điện thoại")
public WebElement screenTitle;

// Priority 3: uiautomator
@MobileFindBy(uiautomator = "new UiSelector().description(\"Tôi đồng ý với \")")
public WebElement termsText;

// Priority 4: xpath (LAST RESORT — comment why)
// xpath used because element has no id, accessibility, or unique uiautomator selector
@MobileFindBy(xpath = "//android.widget.TextView[@text='Submit']")
public WebElement submitButton;

// List: same annotation, declare as List<WebElement>
@MobileFindBy(uiautomator = "new UiSelector().resourceIdMatches(\".*contact_item_.*\")")
public List<WebElement> contactItems;

// Platform-specific: Android first, iOS second
@MobileFindBys({
    @MobileFindBy(uiautomator = "new UiSelector().className(\"android.widget.ScrollView\")"),
    @MobileFindBy(className = "XCUIElementTypeOther")
})
public WebElement scrollView;
```

### Fast probe (back-loop / reset polling)
`@MobileFindBy` polls 5s by default — too slow for back-loop/reset. Use `probe = true` (returns immediately ~50-100ms):
```java
@MobileFindBy(id = "home_screen") public WebElement homeScreenImage;          // normal — isDisplayed() waits 5s
@MobileFindBy(id = "home_screen", probe = true) public List<WebElement> homeScreenProbe;  // fast — no wait
public boolean isDisplayedFast() { return !homeScreenProbe.isEmpty(); }
```
**Rules**: declare probe fields as `List<WebElement>` (no try/catch needed — the list is empty when absent). **Never** use `probe=true` for assertions (assertions need a wait timeout). **Never** call `driver.findElements()` — always go through a `probe=true` field.

## Missing ID Report (MANDATORY)
When you declare an element **without an `id`** (using `accessibility`/`uiautomator`/`xpath`/text…), you **MUST** emit a "Missing ID Report" table so QA can ask devs to add an id. Applies in `/plan-tests`, `/cook`, `/fix`, `/review-*`. Skill-ized logic: skill `missing-ids`.
```
⚠️ **Missing ID Report** — Elements without an ID, dev needs to add one:

| Element name | Location / Screen | Current locator | Description |
|-------------|-------------------|-------------------|-------|
| termsText   | Onboarding        | uiautomator: `new UiSelector().description("Tôi đồng ý với ")` | Terms agreement checkbox |
```
Only report elements that do NOT use `id`. Skip elements that have an `id`.

## Page Object (Screen) — summary
- extends `BaseScreen`, package `com.example.screens.<group>`, constructor takes `AppiumDriver` and calls `super(driver)`.
- Elements are `public WebElement` + `@MobileFindBy`. Interaction methods (verbs) live in the Screen, **NOT** in the Test. **MUST** have `isDisplayed()` (try-catch, return false on exception).
- NO asserts, NO TestNG imports in a Screen. Contract details: [design-pattern.md §3](design-pattern.md).

## Test class — summary
- extends `BaseTest` (atomic) or `BaseRegression` (aggregate flow). Init Screens in `@BeforeClass(alwaysRun=true)` via `requireDriver()`; `ExtentTest` via `extentReport.getExtentTest("Screen Name")`.
- `@Test(priority=n)` (n from 1). Each step: `report.createNode("Step")` + screenshot `Utils.infoCap/passCap/failCap(driver, node, msg)`.
- `DataProvider` for test data (`@Test(dataProvider="users", dataProviderClass=TestDataProvider.class)`). Do NOT look up elements / call `driver.findElement()` in a Test.

## Waiting & stability (anti-flaky)
- ❌ **`Thread.sleep()` is banned** for waiting on UI. `MobileFindFieldDecorator` already provides 5-10s polling; use `WebDriverWait` for specific conditions.
- `Utils.delay(ms)` ONLY for animation/transition. Do not bump timeouts blindly to "make the test pass" — timeouts are centrally configured, no magic numbers scattered around.
- `isDisplayed()` and queries do not throw — they return a boolean.

## Import order
```java
// 1. Project   import com.example.screens.base.BaseScreen; com.example.utils.MobileFindBy; ...
// 2. Appium    import io.appium.java_client.AppiumDriver;
// 3. Selenium  import org.openqa.selenium.WebElement; ...support.ui.WebDriverWait;
// 4. TestNG    import org.testng.annotations.*; org.testng.Assert;   (Test only)
// 5. Extent    import com.aventstack.extentreports.ExtentTest;        (Test only)
// 6. Java SDK  import java.time.Duration; java.util.List;
```

## Configuration & secrets
- Do not hard-code path/URL/credential/timeout — go through `PropertyReader` + `configurations/*.properties` (load order `configurations/` → `classpath:constants/`).
- Do not commit secrets; do not log passwords. Test account/OTP come from config / `TestDataProvider`, not hard-coded in the Test.

## Reference templates (read before creating a new class)
- **Screen**: `src/main/java/com/example/screens/auth/LoginScreen.java`
- **Test**: `src/test/java/com/example/tests/auth/GoToHomeTest.java`
- **HTML report**: `${CLAUDE_PLUGIN_ROOT}/rules/report-template.html` — replace `{{placeholder}}`, output `docs/<module>-testcase-report.html`.

## Before finishing
- `mvn clean compile test-compile` must be **green** (skill `build-verify`). Red → fix via skill `fix-by-layer` until green.
- Self-check against [review-checklist.md](review-checklist.md). Changing the directory structure → update `CLAUDE.md`, `README.md`, `README-vi.md`, the TestNG XML, and re-sync `.codex` (`bash scripts/sync-codex-from-claude.sh`).
- Do NOT commit/push unless asked.
</content>
</invoke>
