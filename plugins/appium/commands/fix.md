---
description: Fix một bug (compile/test fail, flaky, rule violation) đúng layer, hoặc cập nhật/sửa một plan đã có
argument-hint: <mô tả bug / lỗi test / path plan cần sửa>
allowed-tools: Read, Glob, Grep, Edit, Write, Bash, Agent
---

# /fix — Sửa bug hoặc sửa plan

Input: **$ARGUMENTS**

## Phân loại
1. **Sửa plan**: input trỏ file trong `plans/` hoặc nói "sửa plan" → cập nhật file plan đó (giữ format chuẩn của `/plan`). KHÔNG dùng skill fix-by-layer.
2. **Sửa bug** (mặc định): compile fail / test fail / flaky / rule violation → dùng skill bên dưới.

## Thực hiện (sửa bug)
- Đọc @${CLAUDE_PLUGIN_ROOT}/rules/coding-rules.md + @${CLAUDE_PLUGIN_ROOT}/rules/design-pattern.md.
- **skill `fix-by-layer`**: khoanh vùng → tìm đúng layer (Screen `@MobileFindBy` / Test assertion / regression-smoke compose / configurations) → sửa tối thiểu đúng nguyên nhân gốc, KHÔNG workaround (không `Thread.sleep` bừa, không nuốt lỗi).
- Lỗi do **selector/UI đổi** → lấy locator đúng qua **skill `mcp-navigate`** + **skill `capture-elements`** trước khi sửa Screen.
- Verify qua **skill `build-verify`** (compile xanh + chạy lại test vừa fix tới khi xanh).
- Element non-id đụng tới → Missing ID Report (skill `missing-ids`). KHÔNG commit/push trừ khi được yêu cầu.

## Báo cáo
Nguyên nhân gốc · file/layer đã sửa · cách verify. Flaky → nguồn bất định + biện pháp (chờ điều kiện thật thay vì sleep).
