# Design System Conformance (UI của app) — đối chiếu Figma (BẮT BUỘC cho exploratory)

> Phân biệt: file này nói về **design system của APP đang test** (UI: màu/typography/component, thường theo Material 3). KHÁC với [design-system.md](design-system.md) vốn nói về design system của **codebase test** (POM/naming/locator). Cả hai cùng tồn tại.

Nguồn mốc: một thư mục design-system **trích từ Figma** của dự án bạn — quy ước trỏ qua biến `DESIGN_SYSTEM_DIR` (mặc định `design-system/` ở gốc repo, hoặc cấu hình trong CLAUDE.md). Thư mục này chứa `tokens.json` (màu/typography/shape/elevation), `components/*.json`, `manifest.json`. Brand color / hệ design (vd Material 3) lấy từ chính tokens đó — **không hardcode trong plugin**.

> Chưa có thư mục design-system? Tính năng đối chiếu design **tự bỏ qua** (ghi `[NEEDS-TRIAGE]`), exploratory vẫn chạy phần chức năng bình thường.

## Khi nào áp dụng
- `/exploratory`: ngoài phát hiện lỗi chức năng, **thêm 1 pass đối chiếu design** cho mỗi màn/đối tượng UI gặp được (chỉ khi có `DESIGN_SYSTEM_DIR`).
- `/review-change`, `/review-codebase`: tham chiếu khi đánh giá ảnh/spec (không bắt buộc).

## Cách check (multimodal-first — app Flutter/native không cho đọc màu/font qua element)
1. Mở màn qua Appium MCP (skill `navigate-app`) → **chụp screenshot**.
2. Nạp `<DESIGN_SYSTEM_DIR>/tokens.json` + file component liên quan trong `<DESIGN_SYSTEM_DIR>/components/` (vd popup → `dialog.json`, dải nút chọn → `button-group.json`).
3. **Nhìn ảnh, đối chiếu** từng mục trong `conformanceChecklist` của component: màu nền/chữ vs token, bo góc, cỡ chữ theo typography scale, state-layer khi nhấn.
4. **Structural check rẻ** qua element bounds: vùng chạm nút ≥48px, segment cùng chiều cao, dialog không tràn mép.

## Phân loại lệch (BẮT BUỘC theo failure-triage)
Mọi sai khác design phải gắn nhãn — xem [failure-triage.md](failure-triage.md):
- App vẽ sai so với Figma (nút primary sai màu, dialog bo góc vuông, sai cỡ chữ, thiếu state-layer) → **`[APP-BUG]`** *design deviation* — báo dev, KHÔNG sửa test để né.
- Ta đối chiếu nhầm component/sai spec → **`[FRAMEWORK]`** (sửa spec trong `<DESIGN_SYSTEM_DIR>/`).
- Spec chưa trích / thiếu node → **`[NEEDS-TRIAGE]`** (bổ sung component theo README §Quy trình bổ sung).

Trong report exploratory, mục **🐛 App defects** thêm dòng design deviation; HTML run report dùng `Utils.failCap(..., "[APP-BUG] <màn> lệch design: <chi tiết> (kỳ vọng <token/spec>)")`.

## Giới hạn (trung thực, không phóng đại)
- Màu/typography **chỉ kiểm bằng mắt trên ảnh** — không trích chính xác từ element Flutter/native. Kết luận lệch màu phải dựa trên ảnh rõ, không suy đoán.
- Một số số đo px trong spec theo M3 default (đánh dấu `_*Note`/`dataProvenance`) — đừng coi là mốc cứng cho tới khi verify bằng `get_design_context`.
- Coverage component thường chưa đủ — xem `<DESIGN_SYSTEM_DIR>/manifest.json`. Component pending → chưa đối chiếu được, ghi `[NEEDS-TRIAGE]`.
