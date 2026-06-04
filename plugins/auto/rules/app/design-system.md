# Design System

Design system for the ShinhanAppium project. This file is the standard source for `/review-change` and `/review-codebase`.

---

## 1. Architecture Pattern

### Page Object Model (POM)
```
Screen (Page Object) ←→ Test (Test Class)
       ↓                      ↓
   BaseScreen              BaseTest
       ↓                      ↓
   MobileFindFieldDecorator   AppiumDriver (static, shared)
```

- **Screen**: holds elements + interaction methods
- **Test**: holds test flow + assertions + reporting
- **Absolutely DO NOT** put element-finding / element-interaction logic in a Test class
- **Absolutely DO NOT** put assertions in a Screen class

### Package Structure
```
com.example.screens.<group>.<Name>Screen    → Page Object
com.example.tests.<group>.<Name>Test        → Test Class
com.example.screens.<group>/elements.json   → Element catalog
```

Group names: `auth`, `home`, `splash`, `settings`, `product`, `order`, ...
- Screen and Test in the same group must use the same group name
- Each group corresponds to one functional flow in the app

---

## 2. File Naming Convention

| Type | Pattern | Example | Location |
|------|---------|---------|----------|
| Screen class | `<Name>Screen.java` | `LoginScreen.java` | `screens/<group>/` |
| Test class | `<Name>Test.java` | `LoginTest.java` | `tests/<group>/` |
| Element catalog | `elements.json` | `elements.json` | `screens/<group>/` |
| Plan | `plan.md` | `plan.md` | `plans/<feature>/` |
| Tracking | `tracking.md` | `tracking.md` | `plans/<feature>/` |
| Config | `<name>.properties` | `android-capabilities.properties` | `configurations/` |
| Script | `<action>.sh` | `run-android.sh` | `scripts/` |
| TestNG XML | `testng-<scope>.xml` | `testng-android.xml` | `testng/` |

### Name must be PascalCase
- Screen: `LoginScreen`, `ForgotPasswordScreen`, `LeftSideBarScreen`
- Test: `LoginTest`, `GoToHomeTest`, `SignOutTest`

### Group name must be lowercase
- `auth`, `home`, `splash` — NOT `Auth`, `Home`

---

## 3. Screen Class Checklist

Every Screen class MUST satisfy:

- [ ] `extends BaseScreen`
- [ ] Constructor: `public <Name>Screen(AppiumDriver driver) { super(driver); }`
- [ ] Package: `com.example.screens.<group>`
- [ ] Import: `com.example.screens.base.BaseScreen`, `com.example.utils.MobileFindBy`, `io.appium.java_client.AppiumDriver`, `org.openqa.selenium.WebElement`
- [ ] Elements: `public WebElement` with `@MobileFindBy`
- [ ] **MUST** have a `public boolean isDisplayed()` method
- [ ] `isDisplayed()` uses try-catch, returns false on exception
- [ ] Interaction methods (click, enter, scroll) live in the Screen class
- [ ] NO assertions, NO TestNG/Assert imports

### isDisplayed() Pattern
```java
public boolean isDisplayed() {
    try {
        return <primaryElement>.isDisplayed();
    } catch (Exception ignored) { return false; }
}
```
- `primaryElement`: the most characteristic element, always visible when that screen is active
- Do NOT check multiple elements (one element is enough)

---

## 4. Test Class Checklist

Every Test class MUST satisfy:

- [ ] `extends BaseTest`
- [ ] Package: `com.example.tests.<group>`
- [ ] `@BeforeClass(alwaysRun = true)` method:
  - Initialize ALL Screen instances via `new <Name>Screen(requireDriver())`
  - Create `ExtentTest` via `extentReport.getExtentTest("Screen Name")`
- [ ] Test methods use `@Test(priority = n)` — n starts at 1, increasing
- [ ] Each important step creates `report.createNode("Step Name")`
- [ ] Screenshot at each step: `Utils.infoCap()`, `Utils.passCap()`, `Utils.failCap()`
- [ ] DataProvider if test data is needed: `@Test(dataProvider="users", dataProviderClass=TestDataProvider.class)`
- [ ] NO element-finding logic, NO direct `driver.findElement()` calls

### Test Method Naming
- `checkUI` — verify the UI
- `testLogin`, `testSearch` — test the main behavior
- `passingData` — receive data from a DataProvider
- Use verb + noun, describing the behavior

---

## 5. Element Declaration Rules

### Locator Priority (mandatory, in order)
```
1. id          → @MobileFindBy(id = "btn_login")
2. accessibility → @MobileFindBy(accessibility = "Login button")
3. uiautomator → @MobileFindBy(uiautomator = "new UiSelector()...")
4. text        → @MobileFindBy(text = "Đăng nhập")
5. className   → @MobileFindBy(className = "android.widget.Button")
6. xpath       → @MobileFindBy(xpath = "//...") // MUST comment why
```

### Element Naming Convention
- camelCase, descriptive
- Suffix by element type:

| Element Type | Suffix | Example |
|-------------|--------|---------|
| Button | `Button` | `loginButton`, `backButton` |
| Text field | `Textfield` or `Input` | `phoneInputTextfield`, `emailInput` |
| Label / Text | `Label` or `Text` | `titleLabel`, `errorText` |
| Checkbox | `Checkbox` | `termsCheckbox` |
| Toggle / Switch | `Toggle` or `Switch` | `notificationToggle` |
| Image | `Image` or `Icon` | `avatarImage`, `searchIcon` |
| ScrollView | `ScrollView` | `mainScrollView` |
| Container / View | `View` or `Container` | `headerView`, `listContainer` |
| Link | `Link` | `forgotPasswordLink` |
| Tab | `Tab` | `homeTab`, `settingsTab` |

### List of Elements Declaration
When you need to find **multiple elements** (e.g., list items, child views), use `List<WebElement>`:
```java
// Find all matching elements by className
@MobileFindBy(className = "android.view.View")
public List<WebElement> viewItems;

// Find all matching elements by uiautomator pattern
@MobileFindBy(uiautomator = "new UiSelector().resourceIdMatches(\".*contact_item_.*\")")
public List<WebElement> contactItems;

// Find all matching elements by accessibility
@MobileFindBy(accessibility = "product_card")
public List<WebElement> productCards;
```
- Same `@MobileFindBy` annotation, just declare field as `List<WebElement>` instead of `WebElement`
- `MobileFindFieldDecorator` auto-detects and uses `findElements()` internally
- **NEVER** use `driver.findElements()` directly — always declare via `@MobileFindBy`
- Includes timeout retry (polls until list is non-empty or timeout)

### Platform-specific Declaration
When each platform needs a different locator:
```java
@MobileFindBys({
    @MobileFindBy(uiautomator = "new UiSelector().className(\"android.widget.ScrollView\")"),
    @MobileFindBy(className = "XCUIElementTypeOther")
})
public WebElement scrollView;
```
- First annotation: Android locator
- Second annotation: iOS locator
- `MobileFindFieldDecorator` picks automatically by platform

---

## 6. Import Order

```java
// 1. Project imports
import com.example.screens.base.BaseScreen;
import com.example.utils.MobileFindBy;
import com.example.utils.MobileFindBys;
import com.example.utils.Utils;

// 2. Appium imports
import io.appium.java_client.AppiumDriver;

// 3. Selenium imports
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.WebDriverWait;

// 4. TestNG imports (Test class only)
import org.testng.annotations.*;
import org.testng.Assert;

// 5. ExtentReports imports (Test class only)
import com.aventstack.extentreports.ExtentTest;

// 6. Java SDK imports
import java.time.Duration;
```

---

## 7. TestNG XML Structure

### Rules
- Each test class that must run in order → place in its own `<test>` block
- `preserve-order="true"` on both `<suite>` and `<test>`
- `GoToHomeTest` is **ALWAYS** the first `<test>` block
- The `TestResultCollector` listener is always declared

### Template
```xml
<suite name="Regression Suite" verbose="1" preserve-order="true">
    <parameter name="platform" value="android"/>
    <listeners>
        <listener class-name="com.example.utils.TestResultCollector"/>
    </listeners>

    <test name="GoToHome" preserve-order="true">
        <classes>
            <class name="com.example.tests.auth.GoToHomeTest"/>
        </classes>
    </test>

    <test name="TargetTest" preserve-order="true">
        <classes>
            <class name="com.example.tests.<group>.<Name>Test"/>
        </classes>
    </test>
</suite>
```

---

## 8. Wait Strategy

| Type | Usage | When |
|------|-----------|---------|
| **Implicit** | `MobileFindFieldDecorator` (5s polling, 500ms interval) | Every element lookup, automatic |
| **Explicit** | `new WebDriverWait(driver, Duration.ofSeconds(n))` | Wait for a specific condition |
| **Animation** | `Utils.delay(ms)` | Wait for an animation to finish |
| **BANNED** | `Thread.sleep()` | NEVER use directly |

---

## 9. Reporting Pattern

### Screenshot at each step
```java
ExtentTest node = report.createNode("Step Name");
// ... do action ...
Utils.passCap(driver, node, "Action succeeded");  // pass + screenshot
Utils.failCap(driver, node, "Action failed");     // fail + screenshot
Utils.infoCap(driver, node, "Current state");      // info + screenshot
```

### Naming for ExtentTest
- `extentReport.getExtentTest("Screen Name")` — top-level test
- `report.createNode("Step: Action Description")` — child step

---

## 10. Configuration Rules

| File | Location | Purpose |
|------|---------|---------|
| `android-capabilities.properties` | `configurations/` | Android capabilities |
| `ios-capabilities.properties` | `configurations/` | iOS capabilities |
| `flutter-capabilities.properties` | `configurations/` | Flutter capabilities |
| `configuration.properties` | `configurations/` | General settings |
| `cloudflare.properties` | `configurations/` | R2 upload config |
| `lark.properties` | `configurations/` | Lark notification config |

- Do NOT hardcode paths, URLs, credentials in code
- PropertyReader load order: `configurations/` → `classpath:constants/` → `classpath:`
- Secrets (API tokens, webhook URLs) only live in .properties files

---

## 11. Error Handling Pattern

### Screen class
```java
public boolean isDisplayed() {
    try { return element.isDisplayed(); }
    catch (Exception ignored) { return false; }
}
```

### Test class
```java
if (screen.isDisplayed()) {
    Utils.passCap(driver, node, "Screen verified");
} else {
    Utils.failCap(driver, node, "Screen not found");
    Assert.fail("Expected screen not displayed");
}
```

- Do NOT throw raw exceptions from a Screen class
- The Test class decides pass/fail via Assert
- Always screenshot before failing

---

## 12. Anti-patterns (DO NOT do)

| Anti-pattern | Correct way |
|-------------|-----------|
| `driver.findElement()` in a Test class | Use a Screen class element |
| `Thread.sleep(5000)` | `Utils.delay()` or `WebDriverWait` |
| `@AndroidFindBy` / `@iOSXCUITFindBy` | `@MobileFindBy` |
| Hardcode phone/password in a Test | Use `DataProvider` + `UserInfo` |
| Assert in a Screen class | Assert only in a Test class |
| Multiple classes in one `<test>` block (when ordering is needed) | One `<test>` block per class |
| `xpath` without a comment | Must comment the reason |
| Screen class without `isDisplayed()` | MUST have it |
| Static imports for an element | Instance field via `@MobileFindBy` |
| Hardcode file paths | Use `configuration.properties` |
</content>
