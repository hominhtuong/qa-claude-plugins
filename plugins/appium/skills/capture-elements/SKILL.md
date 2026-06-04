---
name: capture-elements
description: Logic tái dùng để trích xuất element bền vững từ màn đang mở trên app thật (qua Appium MCP / page source) và chọn locator ổn định theo priority id > accessibility > uiautomator > xpath. Dùng bởi command exploratory (lấy element để khai báo Screen) và fix (lấy locator đúng khi UI/selector đổi). Đánh dấu element thiếu id cho skill missing-ids. Là đầu vào cho skill declare-screen.
---

# Skill: capture-elements

Năng lực tái dùng: từ màn đang mở (sau `mcp-navigate`) → danh sách element + locator ổn định, nuôi cho `declare-screen`. Chiến lược locator: [design-system §5](../../rules/design-system.md). Việc discovery nặng từ app thật do **agent `source-inspector`** (`${CLAUDE_PLUGIN_ROOT}/agents/agent-source.md`) thực thi qua Appium MCP; skill này là phần CHỌN locator + ghi catalog.

## Thủ tục
1. **Lấy page source** màn hiện tại: `mcp__appium__appium_get_page_source` (hoặc dump từ source-inspector). Nắm cấu trúc cây element + thuộc tính (`resource-id`, `content-desc`, `text`, `class`, `accessibility id`).
2. **Chọn locator** theo priority cho mỗi element quan trọng:
   - `id` (resource-id Android / accessibilityId iOS) — **tốt nhất**.
   - `accessibility` (content-desc) — cross-platform thay thế.
   - `uiautomator` (`new UiSelector()...`) — Android-only khi không có id/accessibility.
   - `xpath` — **last resort**, kèm comment lý do. Tránh xpath cứng & index mong manh.
3. **Element không có `id`** (phải dùng accessibility/uiautomator/xpath/text) → đánh dấu để **skill `missing-ids`** RECORD khi `declare-screen` ghi Screen.
4. **Ghi catalog**: lưu element + locator đã chọn vào `screens/<group>/elements.json` (persist cho 3-layer lookup). Form field mới → cập nhật `test-hints.json` (field metadata + business rules).
5. **Trả về**: bảng `element (vai trò) | locator chọn | thuộc tính thô | thiếu id?` cho bước khai báo Screen.

> Skill này chỉ TRÍCH XUẤT + chọn locator; viết thành field Java là skill `declare-screen`. [MCP Screenshot Rule] khi chụp qua MCP: dùng JPG, lưu `sitemap/screenshots/<name>.jpg`, KHÔNG để ra Desktop.
