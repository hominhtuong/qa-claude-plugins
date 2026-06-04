# Exploratory Bug Report — Template (định dạng chuẩn gửi dev)

> Định dạng output **bắt buộc** cho `/exploratory` (và cho exploratory-gate của `/plan`). Mẫu gốc anh duyệt: [`reports/exploratory/dev-bug-report-03Jun2026.md`](../../reports/exploratory/dev-bug-report-03Jun2026.md).
>
> - **Output file**: `reports/exploratory/<group>/dev-bug-report-<ddMMMyyyy>.md` (vd `dev-bug-report-03Jun2026.md`). Nếu chạy nhiều group cùng ngày → 1 file/ngày gom các group, hoặc 1 file/group.
> - **Screenshot bằng chứng**: lưu `reports/exploratory/<group>/screenshots/`, **đặt tên theo BUG-ID** (`02-APP01-published-tab-sqlite-crash.png`). Mỗi `[APP-BUG]` PHẢI có ít nhất 1 screenshot.
> - Mỗi bug đồng thời **append vào defect register** [`reports/exploratory/bug-summary.md`](../../reports/exploratory/bug-summary.md) (cấp APP-ID, cập nhật bảng đếm + phân bố mức độ).
> - Phân định nhãn theo [failure-triage.md](failure-triage.md). **Chỉ `[APP-BUG]` mới chặn việc viết test** (xem `/plan`).

---

## Cấu trúc file (copy khung này)

```markdown
# 🐛 Bug Report gửi Dev — SBH Flutter (exploratory <ddMMMyyyy>)

> App `<package>` · build `<ver>` · <platform> · device `<id>` · account `<sđt>`.
> Defect register đầy đủ: bug-summary.md. Bản này gom **N lỗi** ưu tiên gửi dev.

---

## 🔴 BUG-1 (Critical) — <module>: <tiêu đề lỗi ngắn gọn, có giá trị>

- **Màn**: <đường điều hướng từ Home → … → màn lỗi>.
- **Hiện tượng**: <mô tả khách quan>. Trích **nguyên văn** thông báo lỗi / SQL / text sai trong ``` code block ``` nếu có.
- **Root cause (nếu suy ra được từ thông báo)**: <phân tích ngắn — vd conflict target SQL sai, sai công thức>.
- **Tác động**: <ảnh hưởng người dùng / nghiệp vụ — vd lộ schema, sai chứng từ pháp lý>.
- **Kỳ vọng**: <hành vi đúng theo spec/SBH Reactive>.
- **Bằng chứng**: `reports/exploratory/<group>/screenshots/<file>.png`.
- *(Defect ID register: **APP-NN**.)*

## 🔴 BUG-2 (Critical) — …
## 🟡 BUG-3 (Warning) — …
## ℹ️ BUG-k (Info) — …

---

## ✅ Đã kiểm tra — KHÔNG lỗi (app hoạt động đúng)
- <màn A> (mô tả ngắn cái đã verify) — OK.
- <màn B> — OK.

## ❓ Cần dev xác nhận (low-confidence, NEEDS-TRIAGE)
- <quan sát chưa đủ bằng chứng kết luận bug> — cần dev xác nhận hành vi mong muốn.

## Ghi chú môi trường
- <điều kiện env/data ảnh hưởng test — vd device không sạc, account thiếu data>.
```

---

## Quy ước nội dung (chất lượng > số lượng)

1. **Tiêu đề bug có giá trị**: nêu đúng triệu chứng cốt lõi (vd "tab Đã phát hành crash + lộ raw SQL"), không chung chung ("lỗi màn X").
2. **Bằng chứng khách quan**: trích nguyên văn lỗi/SQL/số liệu sai; **bước tái hiện** rõ ràng (path từ Home); ghi **số lần tái hiện** (vd 2/2).
3. **Root cause khi nhìn thấy được**: nếu thông báo lỗi lộ nguyên nhân (SQL conflict, công thức), phân tích ngắn — giúp dev fix nhanh. KHÔNG bịa nếu không chắc.
4. **Mức độ** theo tác động: 🔴 Critical (crash / sai chứng từ pháp lý / mất chức năng chính / lộ bảo mật) · 🟡 Warning (sai một phần / UX kẹt / thiếu tính năng so spec) · ℹ️ Info (lệch chuẩn id, localization nhỏ).
5. **Mục "Đã kiểm KHÔNG lỗi" là bắt buộc** — cho dev biết phạm vi đã cover (không phải "chưa test" = "không lỗi").
6. **Trung thực**: app là bản port có thể lỗi — KHÔNG che lỗi, KHÔNG kết luận `[APP-BUG]` khi chưa tái hiện trên app thật (chưa chắc → `NEEDS-TRIAGE`).
