---
name: review-audit
description: Logic tái dùng để soi một tập thay đổi (diff) hoặc toàn codebase theo review-checklist của dự án và xuất finding theo mức độ (Critical/Warning/Info). Dùng bởi command review-change (diff), review-codebase (toàn bộ), và push-code/merge-request (cổng chất lượng trước commit). CHỈ soi & báo, KHÔNG tự sửa (việc sửa là skill fix-by-layer).
---

# Skill: review-audit

Năng lực tái dùng: kiểm tra tuân thủ rule & design pattern → danh sách finding. Chuẩn đối chiếu: [design-pattern.md](../../rules/design-pattern.md), [coding-rules.md](../../rules/coding-rules.md), [design-system.md](../../rules/design-system.md), [review-checklist.md](../../rules/review-checklist.md).

## Thủ tục
1. **Xác định phạm vi**:
   - Có path/feature → review file/feature đó.
   - Trống (review-change) → thay đổi chưa commit: `git diff HEAD` + `git diff --cached` + file mới (`git status --porcelain`). Không có thay đổi → review commit gần nhất `git diff HEAD~1..HEAD`.
   - Toàn bộ (review-codebase) → Glob `src/main/java/com/sbh/screens/**/*.java`, `src/test/java/com/sbh/tests/**/*.java`, `elements.json`, `testng/**/*.xml`, `configurations/*.properties`, `scripts/*.sh`.
2. **Phân loại file → section checklist**: Screen → A,B,C,E,F,J · Test → A,B,D,F,I,J · TestNG XML → G · Config → H · Script → A6 · Doc → K.
3. **Đối chiếu TỪNG mục** `review-checklist.md`. Trọng tâm bắt buộc:
   - Tách lớp: Screen không assert · assert chỉ ở Test · interaction ở Screen không ở Test.
   - POM: `@MobileFindBy` (không `driver.findElement()` trong Test); Screen có `isDisplayed()` (try-catch, 1 element).
   - Locator priority `id > accessibility > uiautomator > xpath` (xpath phải comment); cờ đỏ `Thread.sleep`, hard-code secret.
   - Naming/package đúng group; GoToHomeTest là `<test>` đầu trong TestNG XML.
   - **Missing ID**: element non-id đã vào Missing ID Report chưa (skill `missing-ids`).
4. **Build check** nếu liên quan: `mvn clean compile test-compile` (qua skill `build-verify`).
5. **Cross-file** (review-codebase): Screen↔Test mapping, package alignment, TestNG coverage, elements.json ↔ @MobileFindBy sync, import thừa/thiếu.
6. **Finding format** (BẮT BUỘC mỗi finding): clickable `path:line` link + **code thực tế** đang lỗi + **code fix**. Sắp Critical → Warning → Info.
7. **Kết luận**: CLEAN / WARNINGS / ISSUES FOUND + đếm theo mức độ + Missing ID Report tổng hợp.

> Skill này **chỉ soi, không sửa**. Caller muốn sửa → skill `fix-by-layer`. Codebase sạch → nói ngắn gọn, đừng bịa lỗi.
