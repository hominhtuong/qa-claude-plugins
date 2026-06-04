# Coding Rules — Quy tắc code Java (BẮT BUỘC)

Chuẩn code cho mọi file Java trong dự án. Kiến trúc tổng: [design-pattern.md](design-pattern.md). Chuẩn đặt tên & locator strategy: [design-system.md](design-system.md).

## Ngôn ngữ & style
- Java 16+, encoding UTF-8. Tuân theo style hiện có; bám file tham chiếu.
- Mỗi class một trách nhiệm. Method ngắn, tên rõ nghĩa. Comment giải thích "tại sao", giữ mật độ như code xung quanh (English hoặc Vietnamese).
- `import` tường minh, không `import *`. Bỏ import/field/biến thừa.
- Ưu tiên sửa file có sẵn hơn tạo file mới; giữ code đơn giản, tránh over-engineering.

## Khai báo element — `@MobileFindBy`
- **Luôn** dùng `@MobileFindBy` (KHÔNG `@AndroidFindBy` + `@iOSXCUITFindBy` riêng lẻ). `@MobileFindBys` chỉ khi mỗi platform cần locator khác nhau.
- **Locator priority (theo thứ tự):**
  1. `id` — **tốt nhất**, cross-platform (resourceId Android / accessibilityId iOS).
  2. `accessibility` — cross-platform (content-description / accessibilityIdentifier).
  3. `uiautomator` — Android-only khi không có id/accessibility.
  4. `xpath` — **last resort**, BẮT BUỘC comment lý do không có locator tốt hơn.
- **NEVER** `driver.findElements()` trực tiếp trong Screen — luôn khai báo `List<WebElement>` với `@MobileFindBy`.

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

// Platform-specific: Android trước, iOS sau
@MobileFindBys({
    @MobileFindBy(uiautomator = "new UiSelector().className(\"android.widget.ScrollView\")"),
    @MobileFindBy(className = "XCUIElementTypeOther")
})
public WebElement scrollView;
```

### Fast probe (back-loop / reset polling)
`@MobileFindBy` mặc định poll 5s — quá chậm cho back-loop/reset. Dùng `probe = true` (trả ngay ~50-100ms):
```java
@MobileFindBy(id = "home_screen") public WebElement homeScreenImage;          // normal — isDisplayed() chờ 5s
@MobileFindBy(id = "home_screen", probe = true) public List<WebElement> homeScreenProbe;  // fast — no wait
public boolean isDisplayedFast() { return !homeScreenProbe.isEmpty(); }
```
**Rules**: probe field khai báo `List<WebElement>` (không cần try/catch — list rỗng khi vắng). **Never** dùng `probe=true` cho assertion (assertion cần wait timeout). **Never** `driver.findElements()` — luôn qua field `probe=true`.

## Missing ID Report (BẮT BUỘC)
Khi khai báo element **không có `id`** (dùng `accessibility`/`uiautomator`/`xpath`/text…), **MUST** xuất bảng "Missing ID Report" để QA yêu cầu dev bổ sung id. Áp dụng trong `/plan`, `/cook`, `/fix`, `/review-*`. Logic skill hoá: skill `missing-ids`.
```
⚠️ **Missing ID Report** — Các element chưa có ID, cần yêu cầu dev bổ sung:

| Tên element | Vị trí / Màn hình | Locator hiện tại | Mô tả |
|-------------|-------------------|-------------------|-------|
| termsText   | Onboarding        | uiautomator: `new UiSelector().description("Tôi đồng ý với ")` | Checkbox đồng ý điều khoản |
```
Chỉ report element KHÔNG dùng `id`. Tất cả element có `id` → bỏ qua report.

## Page Object (Screen) — tóm tắt
- extends `BaseScreen`, package `com.sbh.screens.<group>`, constructor nhận `AppiumDriver` gọi `super(driver)`.
- Element `public WebElement` + `@MobileFindBy`. Interaction method (verb) ở Screen, **KHÔNG** ở Test. **MUST** có `isDisplayed()` (try-catch, return false on exception).
- KHÔNG assert, KHÔNG import TestNG trong Screen. Chi tiết hợp đồng: [design-pattern.md §3](design-pattern.md).

## Test class — tóm tắt
- extends `BaseTest` (atomic) hoặc `BaseRegression` (flow tổng hợp). Init Screen trong `@BeforeClass(alwaysRun=true)` qua `requireDriver()`; `ExtentTest` qua `extentReport.getExtentTest("Screen Name")`.
- `@Test(priority=n)` (n từ 1). Mỗi step: `report.createNode("Step")` + screenshot `Utils.infoCap/passCap/failCap(driver, node, msg)`.
- `DataProvider` cho test data (`@Test(dataProvider="users", dataProviderClass=TestDataProvider.class)`). KHÔNG tìm element / `driver.findElement()` trong Test.

## Chờ đợi & ổn định (chống flaky)
- ❌ **Cấm `Thread.sleep()`** chờ UI. `MobileFindFieldDecorator` đã cung cấp polling 5-10s; dùng `WebDriverWait` cho điều kiện cụ thể.
- `Utils.delay(ms)` CHỈ cho animation/transition. Không tăng timeout bừa để "qua test" — timeout cấu hình tập trung, không rải số ma.
- `isDisplayed()` và query không ném exception — trả boolean.

## Import order
```java
// 1. Project   import com.sbh.screens.base.BaseScreen; com.sbh.utils.MobileFindBy; ...
// 2. Appium    import io.appium.java_client.AppiumDriver;
// 3. Selenium  import org.openqa.selenium.WebElement; ...support.ui.WebDriverWait;
// 4. TestNG    import org.testng.annotations.*; org.testng.Assert;   (Test only)
// 5. Extent    import com.aventstack.extentreports.ExtentTest;        (Test only)
// 6. Java SDK  import java.time.Duration; java.util.List;
```

## Cấu hình & bí mật
- Không hard-code path/URL/credential/timeout — qua `PropertyReader` + `configurations/*.properties` (load order `configurations/` → `classpath:constants/`).
- Không commit secret; không log mật khẩu. Account/OTP test lấy từ config / `TestDataProvider`, không hard-code trong Test.

## Reference templates (đọc trước khi tạo class mới)
- **Screen**: `src/main/java/com/sbh/screens/auth/LoginScreen.java`
- **Test**: `src/test/java/com/sbh/tests/auth/GoToHomeTest.java`
- **HTML report**: `${CLAUDE_PLUGIN_ROOT}/rules/report-template.html` — thay `{{placeholder}}`, output `docs/<module>-testcase-report.html`.

## Trước khi xong
- `mvn clean compile test-compile` phải **xanh** (skill `build-verify`). Đỏ → sửa qua skill `fix-by-layer` tới khi xanh.
- Tự đối chiếu [review-checklist.md](review-checklist.md). Đổi cấu trúc thư mục → cập nhật `CLAUDE.md`, `README.md`, `README-vi.md`, TestNG XML, và re-sync `.codex` (`bash scripts/sync-codex-from-claude.sh`).
- KHÔNG commit/push trừ khi được yêu cầu.
