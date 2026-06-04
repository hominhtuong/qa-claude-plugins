# Design Pattern — Kiến trúc test (BẮT BUỘC)

Framework: **Appium Java Client + TestNG + Page Object Model (POM)**, đa nền tảng **Android · iOS · Flutter** (app Sổ Bán Hàng viết bằng Flutter). Tổ chức **package-by-feature** (`screens/<group>` ↔ `tests/<group>`) để mỗi thành viên phát triển độc lập, ít conflict khi merge.

> Luật vàng: **Screen** (locator `@MobileFindBy` + action, KHÔNG assert) → **tests/** (test flow + assertion + reporting) → **regression/smoke** (flow tổng hợp extends `BaseRegression`). Mỗi Screen có `isDisplayed()` dựa trên 1 element đặc trưng. Locator chỉ ở Screen. Không hard-code/secret/`Thread.sleep`. Mọi test bắt đầu từ **Home**.

## 1. Phân lớp (layers) và trách nhiệm

```
src/main/java/com/sbh/
├── appium/    AppiumServer                         — vòng đời Appium server
├── actions/   MobileActions                        — swipe, tap, OTP… (helper tương tác chung)
├── models/    Capabilities, Environment, UserInfo  — DỮ LIỆU thuần, không assert
├── utils/     PropertyReader, Utils, MobileFindBy,  — helper thuần; Utils.recoverToHome(),
│              MobileFindFieldDecorator, ExtentReport,  takeScreenshot, FLog
│              FLog
└── screens/
    ├── base/      BaseScreen                        — hợp đồng chung + decorator timeout
    └── <group>/   <Name>Screen.java                 — Page Object: @MobileFindBy + action, KHÔNG assert
                   elements.json                      — element catalog (MCP-managed, persist)
                   test-hints.json                    — field metadata + business rules (cho /plan, /cook)

src/test/java/com/sbh/tests/
├── base/         BaseTest         — lifecycle driver, ExtentReport, @AfterMethod screenshot
│                 BaseRegression   — extends BaseTest + auto recoverToHome trước/sau mỗi @Test
│                 TestDataProvider
├── auth/         GoToHomeTest · OnboardingTest · LoginTest   — extends BaseTest (ĐƯỜNG về Home)
├── <feature>/    <Name>Test.java  — test ATOMIC, extends BaseTest (1 mục đích)
├── regression/<feature>/  <Name>Test.java — flow tổng hợp, extends BaseRegression
└── smoke/<feature>/       <Name>Test.java — subset critical-path, extends BaseRegression
```

**Luật vàng — không vi phạm:**
- **Screen** chỉ biết "màn có gì" và "làm được gì" → khai báo `@MobileFindBy` + action method (verb). **Tuyệt đối không assert** trong Screen, không import TestNG.
- **tests/** là nơi DUY NHẤT chứa assertion + ExtentReport + screenshot. Mỗi Test class extends `BaseTest` (atomic) hoặc `BaseRegression` (flow tổng hợp), khởi tạo Screen trong `@BeforeClass(alwaysRun=true)` qua `requireDriver()`.
- **models/** chỉ là dữ liệu; **utils/actions/appium** dùng chung cho mọi feature, ít thay đổi.

## 2. Element Lookup Chain (3-layer) — BẮT BUỘC trước khi viết code

```
Screen.java  →  elements.json  →  Appium MCP (source-inspector agent)
```
1. **Layer 1 — Screen.java**: field `@MobileFindBy` đã khai báo? → dùng luôn.
2. **Layer 2 — elements.json**: có trong catalog `screens/<group>/elements.json`? → thêm vào Screen rồi dùng.
3. **Layer 3 — MCP discovery**: chưa có → check device → spawn **agent `source-inspector`** discover từ app thật → **BẮT BUỘC** lưu vào `elements.json` để tái dùng.

Chi tiết skill hoá: skill `capture-elements` (chọn locator ổn định) + skill `declare-screen` (viết Screen). Sau Layer 3 phải chạy skill `update-sitemap`.

## 3. Hợp đồng Screen: `isDisplayed()`

Mỗi Screen extends `BaseScreen`, constructor `public <Name>Screen(AppiumDriver driver){ super(driver); }`. **MUST** có:
```java
public boolean isDisplayed() {
    try { return primaryElement.isDisplayed(); }
    catch (Exception ignored) { return false; }
}
```
`primaryElement` = element đặc trưng nhất, luôn hiển thị khi màn active. `isDisplayed()` không bao giờ ném exception. Test dùng `screen.isDisplayed()` để kiểm điều hướng.

**Fast probe** cho back-loop/reset (false-negative chấp nhận được): khai báo field `probe = true` dạng `List<WebElement>` (bỏ polling 5s, trả ngay ~50ms), dùng cho `isDisplayedFast()`. KHÔNG dùng `probe` cho assertion. Chi tiết: [coding-rules.md](coding-rules.md).

## 4. Home Prerequisite & recovery (BẮT BUỘC)

- **Mọi test bắt đầu từ Home.** TestNG XML luôn có `com.sbh.tests.auth.GoToHomeTest` là **`<test>` block đầu tiên** (tự xử lý Onboarding + Login nếu cần).
- **`Utils.recoverToHome(driver)`** (`src/main/java/com/sbh/utils/Utils.java`) — safety net 2 tầng, cross-platform:
  - **Stage A — whitelist scan**: hide keyboard → dismiss popup/dialog (close/cancel/confirm ids + nhãn VN) → iOS `nav_tab_management`/`back_button` → `navigate().back()` (lặp tới khi thấy `home_screen`).
  - **Stage B — restart app** (khi A thất bại): `terminateApp` + `activateApp` + chờ `RUNNING_IN_FOREGROUND` + tap-through Splash (`btn_login`) & DataSync (`btn_skip_sync`).
- **Tự động qua `BaseRegression`**: `@BeforeMethod ensureOnHomeBeforeTest` + after-test hook gọi `recoverToHome` trước/sau mỗi `@Test` (sau khi đã chụp ảnh PASS/FAIL). **Bỏ qua cho `tests/auth.*`** (chúng LÀ đường về Home). No-op (~50ms) khi đã ở Home.
- **Hệ quả khi viết regression/smoke mới**: extends `BaseRegression` (không phải `BaseTest`). ❌ KHÔNG tự viết `@BeforeMethod ensureOnHome` mỗi class. ❌ KHÔNG wrap `navigateBackToHome()` trong try/catch cuối mỗi test — hook lo hết. ✅ Chỉ viết thân test.
- Test **atomic** trong `tests/<feature>/` extends `BaseTest` trực tiếp → KHÔNG có recovery hook (gọi `Utils.recoverToHome` thủ công nếu cần reset cứng).
- Reference: `src/test/java/com/sbh/tests/recovery/RecoverToHomeTest.java` · suite `testng/testng-recover-to-home.xml`.

## 5. Sitemap (cho AI điều hướng) — đọc TRƯỚC mọi task

```
sitemap/sitemap.md          → ALWAYS READ: navigation index, screen lookup, entry points
sitemap/test-playbook.md    → READ WHEN PLANNING: test patterns + cross-screen journeys
screens/<group>/test-hints.json → READ WHEN IMPLEMENTING: field metadata + business rules
screens/<group>/elements.json   → READ WHEN CODING: element locators (MCP-managed)
sitemap/screenshots/        → multimodal reference (JPG/screen)
```
**Auto-update** sau MCP discovery / đổi element (skill `update-sitemap`): cập nhật `elements.json`, `test-hints.json`, `sitemap/sitemap.md`, rồi regenerate bằng `python3 sitemap/scripts/gen_sitemap_v2.py` + `gen_test_hints.py`. Chi tiết: `sitemap/README.md`.

## 6. Package-by-feature (chống conflict)

Mỗi tính năng = 1 **group** (`auth`, `home`, `product`, `order`…). Thành viên sở hữu trọn `screens/<group>` + `tests/<group>`. Group name **lowercase**; Screen/Test **PascalCase**. Code dùng chung (`base`, `utils`, `actions`, `models`) ít thay đổi — sửa phải tối thiểu, mở rộng không phá API.

## 7. Chạy test

- Scripts (khuyến nghị, tự check device): `./scripts/run-android.sh` · `./scripts/run-ios.sh` · `./scripts/run-all.sh`.
- Maven: `mvn test -DsuiteXmlFile=testng/testng-android.xml` (hoặc `-ios`/`-all`).
- Compile: `mvn clean compile test-compile` (luôn chạy trước khi xong — skill `build-verify`).

> Chuẩn đặt tên & locator: [design-system.md](design-system.md). Quy tắc code Java: [coding-rules.md](coding-rules.md). Checklist review: [review-checklist.md](review-checklist.md). Sự cố hay gặp: [troubleshooting.md](troubleshooting.md).
