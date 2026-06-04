---
description: Review code (review-audit) → tự fix Blocker rõ ràng → build xanh → commit & push branch hiện tại lên origin
argument-hint: [commit message tuỳ chọn — trống = tự sinh từ diff]
allowed-tools: Read, Glob, Grep, Edit, Write, Bash
---

# /push-code — Review → fix → build → push

Input (commit message tuỳ chọn): **$ARGUMENTS**

Mục tiêu: chỉ push code **đã sạch rule + biên dịch xanh**. Command compose 4 skill theo thứ tự, chèn chính sách xử-lý-finding của push.

## Quy trình (làm đúng thứ tự)

### 1. Review — skill `review-audit`
Soi thay đổi chưa commit theo `review-checklist` → finding theo mức độ.

### 2. Xử lý finding (chính sách push) — skill `fix-by-layer`
- **🔴 Critical nguyên nhân gốc rõ ràng** (assert trong Screen, `driver.findElement()` trong Test, hard-code secret, `Thread.sleep`, thiếu `isDisplayed()`…) → **tự fix** qua skill `fix-by-layer`. Fix xong → chạy lại `review-audit` cho phần vừa sửa.
- **🔴 Critical mơ hồ / cần quyết định nghiệp vụ** → **DỪNG, không push**, báo người dùng + đề xuất.
- **🟡** tự fix nếu nhỏ & an toàn, không thì ghi báo cáo (không chặn). **ℹ️** chỉ ghi.

### 3. Build xanh — skill `build-verify`
`mvn clean compile test-compile` xanh (cổng bắt buộc). Không xanh → DỪNG, không push.

### 4. Commit & push — skill `commit-push`
Xác định branch (không push thẳng `main`/`master` → tạo `feat/<slug>`), stage tránh secret, commit Conventional + trailer Co-Authored-By (message: `$ARGUMENTS` nếu có), `git push -u origin` no-force.

## Báo cáo cuối
Tóm tắt review (finding theo mức độ, cái nào đã fix / còn lại), file đã commit, tên branch, kết quả push. Dừng giữa chừng → nêu rõ lý do + việc người dùng cần quyết định. **Missing ID Report** nếu có element non-id.
