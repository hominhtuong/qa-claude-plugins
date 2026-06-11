# Template: UI-conformance report (plain language, ready to log-bug)

The report for /qa:exploratory-ui. **Golden rule: do the analysis with maximum technical depth, but
WRITE the report so anyone reads it and instantly gets the problem.** The local engine produces
precise numbers (SSIM, ΔE, stroke ratios) — those stay in `pairs/*.json` + `model-log.jsonl` for
tracking/tuning. They do **NOT** belong in the report body. Translate every finding into design
language a QC/designer/dev understands at a glance.

> ❌ Don't write: *"SSIM 0.667 + ΔE p95 30.5 → lệch layout, stroke ratio 0.42"*.
> ✅ Do write: *"Tiêu đề 'Products' đang hiển thị màu xám #909090 trên nền #393939, design là chữ đen
> #000000 trên nền trắng #FFFFFF; font đang là serif (giống Times) thay vì Arial."*

Translate the engine's typed findings → plain words:

| Engine finding | Say it as |
|---|---|
| `text.mismatch` (static) | *text khác: design "X" → app "Y"* |
| `color.background` | *màu nền sai: design #RRGGBB → app #RRGGBB* |
| `color.text` | *màu chữ sai: design #RRGGBB → app #RRGGBB* |
| `typography.weight` | *chữ đậm hơn / mảnh hơn design* |
| `typography.size` | *cỡ chữ lớn hơn / nhỏ hơn design* |
| `typography.family` | *font khác (vd design Arial → app trông giống serif/Times)* — nhớ là phỏng đoán, xác nhận bằng mắt |
| `layout.shift` / `layout.align` | *bố cục lệch / canh lề sai (lệch trái-phải) so với design* |

Use the design tokens the engine attaches (`design_color`, `design_font`, `design_weight`,
`design_size`) for the "Design:" side — they're the exact Figma truth. For the "Thực tế:" side use
the app's measured values (hex), and the app font as a CLASS (serif/sans + đậm/nhạt), naming a likely
font only as a guess.

---

## File: `results/<feature>/ui-conformance-report-<ddMMMyyyy>.md`

```markdown
# Báo cáo đối chiếu UI — <Feature> (<ddMMMyyyy>)

- **Nền tảng:** <web | android | ios> · thiết bị/màn hình: <device / viewport>
- **Design:** <Figma link> · **Số màn đối chiếu:** <n> · **Đạt:** <x> · **Có lỗi:** <y>
- **OCR (so text):** <tesseract vie+eng | rapidocr | tắt — không có backend>

## Tổng quan từng màn
| Màn | Kết luận | Vấn đề chính (ngắn) |
|-----|----------|---------------------|
| Hóa đơn | 🔴 Có lỗi | Tiêu đề sai chữ + sai màu nền; font khác |
| Danh sách | 🟢 Đạt | — |
| Chi tiết | 🟡 Cần xem lại | Canh lề nút lệch nhẹ |

## 🐛 Lỗi cần sửa
> Mỗi lỗi mô tả ở mức ĐỌC HIỂU, kèm ảnh bằng chứng. Đủ để tạo bug ngay.

### Lỗi 1 — Màn Hóa đơn · tiêu đề (vùng trên-trái)
- **Design:** text "Products", màu chữ #000000, nền #FFFFFF, font Arial Regular, cỡ 16.
- **Thực tế:** text "Product", màu chữ #909090, nền #393939, font giống serif (nghi Times), đậm hơn.
- **Sai:** nội dung chữ (Products → Product), màu chữ, màu nền, font.
- 📷 `results/<feature>/ui-compare/diffs/hd001-heatmap.png`

### Lỗi 2 — Màn Hóa đơn · nút Lưu (vùng dưới-giữa)
- **Design:** nền nút #2196F3 (xanh dương), chữ trắng #FFFFFF.
- **Thực tế:** nền nút #34A853 (xanh lá).
- **Sai:** màu nền nút.
- 📷 `results/<feature>/ui-compare/diffs/hd003-heatmap.png`

## ✅ Đã kiểm tra — khớp design
- Màn Danh sách, Màn Trống: màu/chữ/font/bố cục khớp.

## ❓ Cần xác nhận (NEEDS-TRIAGE)
- Màn Chi tiết: nghi khác font (low-confidence) — cần mắt người xác nhận trên ảnh.
- <Màn chưa chụp được / chưa có design baseline / OCR tắt nên chưa so được text>.

## Ghi chú
- Các giá trị động (tên KH, số tiền, ngày…) KHÔNG tính là lỗi nếu chỉ khác nội dung.
- Chi tiết số liệu kỹ thuật (để tinh chỉnh engine) nằm ở `ui-compare/model-log.jsonl`.
```

---

## Make it log-bug-ready
Structure each "Lỗi N" with the fields `/qa:log-bug` imports (the
[bug-report-import](../skills/bug-report-import/SKILL.md) maps them): **Màn** (→ Feature), the
symptom (Design vs Thực tế), **Kỳ vọng** = the design tokens, **Evidence** = the heatmap path,
severity (design deviation = 🟡 mặc định; sai chữ/màu rõ rệt có thể 🔴). After the report, suggest:
**`/qa:log-bug from <feature>`** — it parses these into the board, the user picks which to push.

## Severity hint (plain)
- 🔴 sai nội dung chữ tĩnh (sai label/typo), hoặc sai màu/độ tương phản rõ rệt (khó đọc).
- 🟡 lệch màu nhẹ, sai cỡ/độ đậm, canh lề lệch, nghi khác font.
- ℹ️ khác biệt nhỏ, có thể do thiết bị — ghi nhận để theo dõi.
