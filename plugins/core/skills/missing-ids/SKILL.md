---
name: missing-ids
description: Logic tái dùng để quản lý "nợ test-id" — element trong Screen chưa neo được bằng id (đang tạm dùng accessibility/uiautomator/xpath/text). Ba năng lực: RECORD (gom element thiếu id vào Missing ID Report), EXPORT (chạy scripts/export_missing_ids.py gom toàn dự án gửi dev), RESOLVE (khi dev đã gắn id). Dùng bởi cook/fix/exploratory/review-* hoặc chạy độc lập qua command missing-test-ids.
---

# Skill: missing-ids

Năng lực tái dùng: ghi/liệt kê/export element thiếu `id` để QA yêu cầu dev bổ sung. Vì sao tồn tại: neo bền nhất là `resource-id`/`accessibilityId`; locator theo text/xpath/uiautomator dễ vỡ khi đổi UI/đa ngôn ngữ. Chuẩn (rule tĩnh): [coding-rules.md §Missing ID Report](../../rules/coding-rules.md), checklist mục tương ứng [review-checklist.md](../../rules/review-checklist.md).

## Năng lực 1 — RECORD (caller gọi khi khai báo element)
Khi `declare-screen`/`cook`/`fix` khai báo cho Screen một element **không** neo được bằng `id`:
1. Tạm dùng locator ổn nhất (priority `accessibility` > `uiautomator` > `xpath`).
2. Gom vào **Missing ID Report** (bảng output cuối task) — KHÔNG report element đã có `id`:
```
⚠️ **Missing ID Report** — Các element chưa có ID, cần yêu cầu dev bổ sung:

| Tên element | Vị trí / Màn hình | Locator hiện tại | Mô tả |
|-------------|-------------------|-------------------|-------|
| termsText   | Onboarding        | uiautomator: `new UiSelector().description("Tôi đồng ý với ")` | Checkbox điều khoản |
```

## Năng lực 2 — EXPORT (chạy độc lập hoặc cuối exploratory/cook)
1. Chạy `python3 scripts/export_missing_ids.py` — quét toàn bộ `screens/<group>/*.java` + `elements.json`, gom element dùng locator non-id.
2. In summary: số màn quét, tổng element thiếu id (phân theo loại locator), đường dẫn file output.
3. Đây là tài liệu gửi dev để gắn `resource-id`/`accessibilityId`.

## Năng lực 3 — RESOLVE (sau khi dev gắn id)
Dev gắn id → đổi locator field sang `@MobileFindBy(id = "...")` trong Screen + cập nhật `elements.json` → chạy lại EXPORT để danh sách co lại. Verify compile xanh qua skill `build-verify`.

> Skill này tham chiếu rule, không nhân bản. Caller: skill `declare-screen`, command `/cook` `/fix` `/exploratory` `/review-*` `/missing-test-ids`.
