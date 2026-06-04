# Design System Conformance (UI app SBH) — đối chiếu Figma (BẮT BUỘC cho exploratory)

> Phân biệt: file này nói về **design system của APP SBH** (UI: màu/typography/component theo Material 3). KHÁC với [design-system.md](design-system.md) vốn nói về design system của **codebase test** (POM/naming/locator). Cả hai cùng tồn tại.

Nguồn mốc: thư mục [`sbh-app-design-system/`](../../sbh-app-design-system/) trích từ Figma *[Flutter] Design System* (`fileKey OCS34gMIjBAxWAFBaua1wX`). Brand primary = **`#16993B`** (xanh SBH), secondary `#005DF9`. Hệ Material 3.

## Khi nào áp dụng
- `/exploratory`: ngoài phát hiện lỗi chức năng, **thêm 1 pass đối chiếu design** cho mỗi màn/đối tượng UI gặp được.
- `/review-change`, `/review-codebase`: tham chiếu khi đánh giá ảnh/spec (không bắt buộc).

## Cách check (multimodal-first — app Flutter không cho đọc màu/font qua element)
1. Mở màn qua Appium MCP (skill `mcp-navigate`) → **chụp screenshot**.
2. Nạp [`sbh-app-design-system/tokens.json`](../../sbh-app-design-system/tokens.json) + file component liên quan trong [`sbh-app-design-system/components/`](../../sbh-app-design-system/components/) (vd popup → `dialog.json`, dải nút chọn → `button-group.json`).
3. **Nhìn ảnh, đối chiếu** từng mục trong `conformanceChecklist` của component: màu nền/chữ vs token, bo góc, cỡ chữ theo typography scale, state-layer khi nhấn.
4. **Structural check rẻ** qua element bounds: vùng chạm nút ≥48px, segment cùng chiều cao, dialog không tràn mép.

## Phân loại lệch (BẮT BUỘC theo failure-triage)
Mọi sai khác design phải gắn nhãn — xem [failure-triage.md](failure-triage.md):
- App vẽ sai so với Figma (nút primary sai màu, dialog bo góc vuông, sai cỡ chữ, thiếu state-layer) → **`[APP-BUG]`** *design deviation* — báo dev, KHÔNG sửa test để né.
- Ta đối chiếu nhầm component/sai spec → **`[FRAMEWORK]`** (sửa spec trong `sbh-app-design-system/`).
- Spec chưa trích / thiếu node → **`[NEEDS-TRIAGE]`** (bổ sung component theo README §Quy trình bổ sung).

Trong report exploratory, mục **🐛 App defects** thêm dòng design deviation; HTML run report dùng `Utils.failCap(..., "[APP-BUG] <màn> lệch design: <chi tiết> (kỳ vọng <token/spec>)")`.

## Giới hạn (trung thực, không phóng đại)
- Màu/typography **chỉ kiểm bằng mắt trên ảnh** — không trích chính xác từ element Flutter. Kết luận lệch màu phải dựa trên ảnh rõ, không suy đoán.
- Một số số đo px trong spec theo M3 default (đánh dấu `_*Note`/`dataProvenance`) — đừng coi là mốc cứng cho tới khi verify bằng `get_design_context`.
- Mới có scheme **light**; chưa cover dark mode.
- Coverage component: mới 3/35 + tokens — xem [`sbh-app-design-system/manifest.json`](../../sbh-app-design-system/manifest.json). Component pending → chưa đối chiếu được, ghi `[NEEDS-TRIAGE]`.
