---
name: fix-by-layer
description: Logic tái dùng để sửa một vấn đề (compile fail, test fail, flaky, rule violation, finding Critical) ĐÚNG layer trong kiến trúc test, sửa tối thiểu theo nguyên nhân gốc, không workaround che lỗi. Dùng bởi command fix (lõi), push-code/merge-request (tự fix Critical rõ ràng), cook (khi lỗi biên dịch/chạy). Verify bằng skill build-verify.
---

# Skill: fix-by-layer

Năng lực tái dùng: định vị đúng tầng để sửa, không vá nhầm chỗ. Chuẩn: [design-pattern.md](../../rules/design-pattern.md), [coding-rules.md](../../rules/coding-rules.md).

## Thủ tục
0. **Triage trước khi sửa** ([failure-triage.md](../../rules/failure-triage.md)) — **BẮT BUỘC**: phân định FAIL là `[APP-BUG]` hay `[FRAMEWORK]`/`[ENV]`/`[DATA]`. Nếu **`[APP-BUG]`** (app sai — tái hiện được trên app thật): **DỪNG, KHÔNG sửa test cho xanh.** Ghi nhận defect (kỳ vọng vs thực tế + bằng chứng) để báo dev; giữ test trung thực (đỏ thật hoặc mark known-defect kèm ticket). Skill này CHỈ sửa khi nguyên nhân là `[FRAMEWORK]`/`[ENV]`/`[DATA]` (app đúng, automation/môi trường/data sai).
1. **Khoanh vùng**: đọc compile error / stack trace / log, hoặc chạy lại class fail `mvn test -Dtest=<Class>`. Selector/UI đổi → mở lại app bằng **skill `mcp-navigate`** + **skill `capture-elements`** để lấy locator đúng. Xác nhận element/hành vi có thật trên app (phân biệt với `[APP-BUG]`).
2. **Tìm đúng layer** (đừng vá nhầm):
   - Selector / element đổi → **Screen** (`@MobileFindBy`).
   - Sai kỳ vọng / assertion / reporting → **Test** (`tests/<group>`).
   - Sai compose flow / thiếu GoToHome / sai recovery → **regression/smoke** (extends `BaseRegression`).
   - Hạ tầng (timeout, capabilities, account, device) → **configurations/** + `utils`/`base`, KHÔNG hard-code trong Test.
   - Element thiếu id (locator vỡ vì text/xpath) → đổi sang locator ổn hơn + ghi qua skill `missing-ids`.
3. **Sửa tối thiểu, đúng nguyên nhân gốc** — KHÔNG workaround: không `Thread.sleep` bừa, không tăng timeout vô tội vạ, không `try/catch` nuốt lỗi, không tắt assertion, **không nới assertion để né một `[APP-BUG]`** (che lỗi app = cấm). Reference template: `LoginScreen.java` / `GoToHomeTest.java`.
4. **Verify**: skill `build-verify` (`mvn clean compile test-compile` xanh) → chạy lại test vừa fix tới khi xanh.
5. **Báo**: nguyên nhân gốc, file/layer đã sửa, cách verify. Flaky → nêu nguồn bất định + biện pháp (chờ điều kiện thật thay vì sleep). Element non-id đụng tới → Missing ID Report.

> Phân biệt với skill `review-audit` (chỉ soi). Đây là skill **sửa**. Sửa **plan** (file trong `plans/`) thì KHÔNG dùng skill này — cập nhật trực tiếp file plan giữ format chuẩn.
