# Design System

Design system cho ShinhanAppium project. File này là nguồn quy chuẩn cho `/review-change` và `/review-codebase`.

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

- **Screen**: chứa elements + interaction methods
- **Test**: chứa test flow + assertions + reporting
- **Tuyệt đối KHÔNG** đặt logic tìm element / tương tác element trong Test class
- **Tuyệt đối KHÔNG** đặt assertions trong Screen class

### Package Structure
```
com.sbh.screens.<group>.<Name>Screen    → Page Object
com.sbh.tests.<group>.<Name>Test        → Test Class
com.sbh.screens.<group>/elements.json   → Element catalog
```

Group names: `auth`, `home`, `splash`, `settings`, `product`, `order`, ...
- Screen và Test cùng group phải dùng cùng group name
- Mỗi group tương ứng 1 luồng chức năng trong app

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

Mọi Screen class PHẢI đáp ứng:

- [ ] `extends BaseScreen`
- [ ] Constructor: `public <Name>Screen(AppiumDriver driver) { super(driver); }`
- [ ] Package: `com.sbh.screens.<group>`
- [ ] Import: `com.sbh.screens.base.BaseScreen`, `com.sbh.utils.MobileFindBy`, `io.appium.java_client.AppiumDriver`, `org.openqa.selenium.WebElement`
- [ ] Elements: `public WebElement` with `@MobileFindBy`
- [ ] **MUST** have `public boolean isDisplayed()` method
- [ ] `isDisplayed()` dùng try-catch, return false nếu exception
- [ ] Interaction methods (click, enter, scroll) nằm trong Screen class
- [ ] KHÔNG có assertions, KHÔNG import TestNG/Assert

### isDisplayed() Pattern
```java
public boolean isDisplayed() {
    try {
        return <primaryElement>.isDisplayed();
    } catch (Exception ignored) { return false; }
}
```
- `primaryElement`: element đặc trưng nhất, luôn hiển thị khi screen đó active
- KHÔNG dùng nhiều element check (1 element là đủ)

---

## 4. Test Class Checklist

Mọi Test class PHẢI đáp ứng:

- [ ] `extends BaseTest`
- [ ] Package: `com.sbh.tests.<group>`
- [ ] `@BeforeClass(alwaysRun = true)` method:
  - Initialize ALL Screen instances via `new <Name>Screen(requireDriver())`
  - Create `ExtentTest` via `extentReport.getExtentTest("Screen Name")`
- [ ] Test methods dùng `@Test(priority = n)` — n bắt đầu từ 1, tăng dần
- [ ] Mỗi step quan trọng tạo `report.createNode("Step Name")`
- [ ] Screenshot tại mỗi step: `Utils.infoCap()`, `Utils.passCap()`, `Utils.failCap()`
- [ ] DataProvider nếu cần test data: `@Test(dataProvider="users", dataProviderClass=TestDataProvider.class)`
- [ ] KHÔNG có logic tìm element, KHÔNG gọi `driver.findElement()` trực tiếp

### Test Method Naming
- `checkUI` — verify giao diện
- `testLogin`, `testSearch` — test hành vi chính
- `passingData` — nhận data từ DataProvider
- Dùng động từ + danh từ, mô tả hành vi

---

## 5. Element Declaration Rules

### Locator Priority (bắt buộc theo thứ tự)
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
- Suffix theo loại element:

| Element Type | Suffix | Example |
|-------------|--------|---------|
| Button | `Button` | `loginButton`, `backButton` |
| Text field | `Textfield` hoặc `Input` | `phoneInputTextfield`, `emailInput` |
| Label / Text | `Label` hoặc `Text` | `titleLabel`, `errorText` |
| Checkbox | `Checkbox` | `termsCheckbox` |
| Toggle / Switch | `Toggle` hoặc `Switch` | `notificationToggle` |
| Image | `Image` hoặc `Icon` | `avatarImage`, `searchIcon` |
| ScrollView | `ScrollView` | `mainScrollView` |
| Container / View | `View` hoặc `Container` | `headerView`, `listContainer` |
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
Khi mỗi platform cần locator khác nhau:
```java
@MobileFindBys({
    @MobileFindBy(uiautomator = "new UiSelector().className(\"android.widget.ScrollView\")"),
    @MobileFindBy(className = "XCUIElementTypeOther")
})
public WebElement scrollView;
```
- Annotation đầu: Android locator
- Annotation sau: iOS locator
- `MobileFindFieldDecorator` tự chọn theo platform

---

## 6. Import Order

```java
// 1. Project imports
import com.sbh.screens.base.BaseScreen;
import com.sbh.utils.MobileFindBy;
import com.sbh.utils.MobileFindBys;
import com.sbh.utils.Utils;

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

### Quy tắc
- Mỗi test class cần chạy theo thứ tự → đặt trong `<test>` block riêng
- `preserve-order="true"` trên cả `<suite>` và `<test>`
- `GoToHomeTest` **LUÔN** là `<test>` block đầu tiên
- `TestResultCollector` listener luôn được khai báo

### Template
```xml
<suite name="SBH Suite" verbose="1" preserve-order="true">
    <parameter name="platform" value="android"/>
    <listeners>
        <listener class-name="com.sbh.utils.TestResultCollector"/>
    </listeners>

    <test name="GoToHome" preserve-order="true">
        <classes>
            <class name="com.sbh.tests.auth.GoToHomeTest"/>
        </classes>
    </test>

    <test name="TargetTest" preserve-order="true">
        <classes>
            <class name="com.sbh.tests.<group>.<Name>Test"/>
        </classes>
    </test>
</suite>
```

---

## 8. Wait Strategy

| Loại | Cách dùng | Khi nào |
|------|-----------|---------|
| **Implicit** | `MobileFindFieldDecorator` (5s polling, 500ms interval) | Mọi element lookup tự động |
| **Explicit** | `new WebDriverWait(driver, Duration.ofSeconds(n))` | Chờ điều kiện cụ thể |
| **Animation** | `Utils.delay(ms)` | Chờ animation hoàn tất |
| **BANNED** | `Thread.sleep()` | NEVER dùng trực tiếp |

---

## 9. Reporting Pattern

### Screenshot tại mỗi step
```java
ExtentTest node = report.createNode("Step Name");
// ... do action ...
Utils.passCap(driver, node, "Action succeeded");  // pass + screenshot
Utils.failCap(driver, node, "Action failed");     // fail + screenshot
Utils.infoCap(driver, node, "Current state");      // info + screenshot
```

### Naming cho ExtentTest
- `extentReport.getExtentTest("Screen Name")` — top-level test
- `report.createNode("Step: Action Description")` — child step

---

## 10. Configuration Rules

| File | Nơi đặt | Mục đích |
|------|---------|----------|
| `android-capabilities.properties` | `configurations/` | Android capabilities |
| `ios-capabilities.properties` | `configurations/` | iOS capabilities |
| `flutter-capabilities.properties` | `configurations/` | Flutter capabilities |
| `configuration.properties` | `configurations/` | General settings |
| `cloudflare.properties` | `configurations/` | R2 upload config |
| `lark.properties` | `configurations/` | Lark notification config |

- KHÔNG hardcode paths, URLs, credentials trong code
- PropertyReader load order: `configurations/` → `classpath:constants/` → `classpath:`
- Secrets (API tokens, webhook URLs) chỉ nằm trong .properties files

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

- KHÔNG throw raw exceptions từ Screen class
- Test class quyết định pass/fail via Assert
- Luôn screenshot trước khi fail

---

## 12. Anti-patterns (KHÔNG được làm)

| Anti-pattern | Đúng cách |
|-------------|-----------|
| `driver.findElement()` trong Test class | Dùng Screen class element |
| `Thread.sleep(5000)` | `Utils.delay()` hoặc `WebDriverWait` |
| `@AndroidFindBy` / `@iOSXCUITFindBy` | `@MobileFindBy` |
| Hardcode phone/password trong Test | Dùng `DataProvider` + `UserInfo` |
| Assert trong Screen class | Assert chỉ trong Test class |
| Multiple classes trong 1 `<test>` block (khi cần ordering) | Mỗi class 1 `<test>` block |
| `xpath` không có comment | Phải comment lý do |
| Screen class không có `isDisplayed()` | MUST have |
| Static imports cho element | Instance field via `@MobileFindBy` |
| Hardcode file paths | Dùng `configuration.properties` |
