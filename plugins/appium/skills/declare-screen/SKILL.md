---
name: declare-screen
description: Logic tái dùng để viết/cập nhật một Page Object "Screen" đúng chuẩn POM của dự án (Appium Java, đa nền tảng Android/iOS/Flutter). Dùng khi một command (cook, exploratory) cần khai báo màn hình thành class Screen — field @MobileFindBy theo locator priority, isDisplayed(), action method kiểu verb, KHÔNG assert. Bao gồm chiến lược chọn locator ổn định và móc nối skill missing-ids cho element thiếu id.
---

# Skill: declare-screen

Năng lực tái dùng: biến một màn hình (vừa khám phá hoặc theo plan) thành **Page Object** đúng chuẩn. Command gọi skill này thay vì tự viết lại quy tắc POM. Chuẩn gốc: [design-pattern §3](../../rules/design-pattern.md), [coding-rules.md](../../rules/coding-rules.md), [design-system.md](../../rules/design-system.md).

## Thủ tục
1. **File & vị trí**: `src/main/java/com/sbh/screens/<group>/<Name>Screen.java`, extends `BaseScreen`, constructor `public <Name>Screen(AppiumDriver driver){ super(driver); }`. Một màn con = một Screen riêng (đừng nhồi nhiều màn). Group lowercase, class PascalCase.
2. **Reference template trước**: đọc `src/main/java/com/sbh/screens/auth/LoginScreen.java` để bám đúng cấu trúc, import order, pattern `isDisplayed()`.
3. **Element fields** (`public WebElement` + `@MobileFindBy`, camelCase theo vai trò UI + suffix loại: `loginButton`, `phoneInputTextfield`, `titleLabel`). **Locator priority**: `id` > `accessibility` > `uiautomator` > `xpath` (xpath BẮT BUỘC comment lý do). Nhiều element → `List<WebElement>`, KHÔNG `driver.findElements()`. Mỗi platform khác locator → `@MobileFindBys` (Android trước, iOS sau).
4. **`isDisplayed()`** (MUST): try-catch quanh 1 element đặc trưng nhất, return `false` on exception — không bao giờ ném. Back-loop/reset cần nhanh → thêm field `probe = true` dạng `List<WebElement>` + `isDisplayedFast()`.
5. **Action methods** = động từ (`enterPhone`, `tapLogin`, `scrollToBottom`); tương tác qua `MobileActions`/element field. **TUYỆT ĐỐI không assert**, không import TestNG trong Screen.
6. **Element thiếu id**: mỗi element KHÔNG neo được bằng `id` (đang dùng accessibility/uiautomator/xpath/text) → gọi **skill `missing-ids`** (RECORD) để gom vào Missing ID Report.
7. **Persist elements.json**: element mới discover → lưu vào `screens/<group>/elements.json` để tái dùng (Layer 2 của 3-layer lookup).

> Sau khi khai báo: compile xanh qua **skill `build-verify`**; cập nhật bản đồ qua **skill `update-sitemap`**.
