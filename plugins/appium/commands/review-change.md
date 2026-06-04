---
description: Review thay đổi git hiện tại (diff) so với design system & coding rules, xuất finding kèm code + cách fix
argument-hint: [path/file/feature | để trống = diff chưa commit]
allowed-tools: Read, Glob, Grep, Bash
---

# /review-change — Review thay đổi git

Phạm vi: **$ARGUMENTS** (để trống → thay đổi chưa commit).

Wrapper mỏng. Toàn bộ logic soi rule nằm ở **skill `review-audit`** (`${CLAUDE_PLUGIN_ROOT}/skills/review-audit`).

## Thực hiện
1. Chạy **skill `review-audit`** với phạm vi = `$ARGUMENTS` (hoặc diff hiện tại nếu trống): `git diff HEAD` + `git diff --cached` + file mới. Nó đọc 4 rule (@${CLAUDE_PLUGIN_ROOT}/rules/design-pattern.md, coding-rules.md, design-system.md, review-checklist.md), phân loại file → section checklist, đối chiếu từng mục, build-check, xuất finding theo mức độ.
2. **Chỉ review, không tự sửa.** Mỗi finding: clickable `path:line` + code thực tế + code fix. Sắp Critical → Warning → Info.
3. Người dùng muốn sửa → gợi ý `/fix` (skill `fix-by-layer`).

## Đầu ra
Report theo định dạng skill `review-audit`: summary (files, issues critical/warning), file reviews (bảng check PASS/FAIL/SKIP), issues kèm fix, **Missing ID Report** tổng hợp, Documentation Sync (CLAUDE.md/README/TestNG cần update?). Kết luận CLEAN/WARNINGS/ISSUES FOUND. Sạch → nói ngắn gọn, đừng pad.
