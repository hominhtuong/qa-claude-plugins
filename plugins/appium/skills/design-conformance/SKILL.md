---
name: design-conformance
description: Logic tái dùng để đối chiếu UI app SBH với design system (Figma → sbh-app-design-system/) — kiểm màu/typography/bo góc/state theo Material 3 brand #16993B. Dùng bởi command exploratory (Bước 2b) và tham chiếu bởi review-*. App Flutter không cho Appium đọc màu/font qua element nên check chủ yếu multimodal (so screenshot app vs token/spec). Lệch design = [APP-BUG] design deviation theo failure-triage.
---

# Skill: design-conformance

Năng lực tái dùng: cho một màn / một loại UI đang mở trên app thật → **đối chiếu design system app SBH** và xuất finding lệch design. Mốc đối chiếu ở thư mục [`sbh-app-design-system/`](../../../sbh-app-design-system/). Luật đầy đủ: [design-system-figma.md](../../rules/design-system-figma.md). Phân loại lệch: [failure-triage.md](../../rules/failure-triage.md).

> Phân biệt: skill này check **design system của APP** (UI: màu/typo/component M3). KHÁC với [design-system.md](../../rules/design-system.md) — chuẩn của codebase test (POM/naming).

## Vì sao multimodal-first
App SBH là **Flutter** → Appium thấy cây phẳng, **KHÔNG đọc được màu hex / font-weight / pixel** qua thuộc tính element. Vì vậy:
- **Kiểm bằng ảnh** (chính): chụp screenshot màn app rồi Claude nhìn, so với token + `referenceScreenshot` của component.
- **Structural (phụ, rẻ)**: dùng element bounds để kiểm cái đo được — vùng chạm nút ≥48px, segment cùng chiều cao, dialog không tràn mép.

## Thủ tục
1. **Nhận diện loại UI** trên màn (nút, popup/dialog, dải nút chọn, text field, card…). Map sang component trong [`sbh-app-design-system/manifest.json`](../../../sbh-app-design-system/manifest.json).
   - status `done` → có spec, đối chiếu được.
   - status `pending` (chưa trích) → **KHÔNG kết luận**, gắn `[NEEDS-TRIAGE]` + (tuỳ chọn) bổ sung spec theo `sbh-app-design-system/README.md` (cần URL/node-id Figma; figma MCP chỉ chạy từ main agent).
2. **Nạp mốc**: [`tokens.json`](../../../sbh-app-design-system/tokens.json) (màu/typography/shape/elevation) + `components/<loại>.json` (variant, `conformanceChecklist`, `referenceScreenshot`).
3. **Chụp app**: `mcp__appium__appium_take_screenshot` → JPG vào `sitemap/screenshots/<name>.jpg` (KHÔNG ra Desktop, KHÔNG PNG).
4. **Đối chiếu** từng mục `conformanceChecklist`: màu nền/chữ vs token (brand primary `#16993B`, secondary `#005DF9`), bo góc, cỡ chữ theo typography scale, có state-layer khi nhấn không. So trực quan với `referenceScreenshot`.
5. **Phân loại & ghi** mỗi lệch (theo failure-triage):
   - App vẽ sai vs Figma → `[APP-BUG]` *design deviation* (kèm screenshot + kỳ vọng token/spec + thực tế). Báo dev, KHÔNG sửa test né.
   - Ta map nhầm component / spec sai → `[FRAMEWORK]` (sửa spec trong `sbh-app-design-system/`).
   - Chưa có spec → `[NEEDS-TRIAGE]`.

## Đầu ra
Danh sách finding design: `loại UI | mục checklist | kỳ vọng (token/spec) | thực tế | triage | screenshot`. Đưa `[APP-BUG]` vào mục **🐛 App defects** của exploratory report; trong HTML run report dùng `Utils.failCap(driver, node, "[APP-BUG] <màn> lệch design: <chi tiết> (kỳ vọng <token>)")`.

## Giới hạn (trung thực)
- Kết luận lệch màu/typography phải dựa trên ảnh rõ — KHÔNG suy đoán từ thuộc tính element.
- Số đo px trong spec đánh dấu `_*Note`/`dataProvenance` (theo M3 default) chưa là mốc cứng tới khi verify `get_design_context`.
- Coverage component còn thiếu (xem `manifest.json`) — chỉ đối chiếu component `done`.
