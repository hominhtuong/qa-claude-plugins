---
description: Quản lý "nợ test-id" — EXPORT danh sách element thiếu id gửi dev, RECORD element mới, hoặc RESOLVE khi dev đã gắn id
argument-hint: [export (mặc định) | record <screen> <element> | resolve <screen> <element>]
allowed-tools: Read, Glob, Grep, Edit, Write, Bash
---

# /missing-test-ids — Quản lý "nợ test-id"

Input: **$ARGUMENTS** (trống → mặc định `export`).

Wrapper mỏng cho **skill `missing-ids`** (`${CLAUDE_PLUGIN_ROOT}/skills/missing-ids`). Chuẩn locator priority + Missing ID Report: xem rule `coding-rules.md` của plugin domain đang bật (vd `appium`) — locator priority `id > accessibility > uiautomator > xpath`.

## Định tuyến theo `$ARGUMENTS`

| Đối số | Năng lực skill | Việc làm |
|---|---|---|
| `export` *(mặc định)* | EXPORT | `python3 scripts/export_missing_ids.py` → quét `screens/<group>/*.java` + `elements.json`, gom element non-id, in summary + đường dẫn output gửi dev. |
| `record <screen> <element>` | RECORD | Thêm element thiếu id vào Missing ID Report của Screen đó (locator tạm + mô tả). |
| `resolve <screen> <element>` | RESOLVE | Sau khi dev gắn id: đổi locator field sang `@MobileFindBy(id=...)` + cập nhật `elements.json` → chạy lại EXPORT để danh sách co lại; verify compile xanh (skill `build-verify`). |

## Đầu ra
- **export**: số màn quét, tổng element thiếu id (phân theo loại locator: accessibility/uiautomator/xpath/text), đường dẫn file output.
- **record/resolve**: file Screen/elements.json đã đụng + trạng thái mới.

> Element thiếu `id` neo bằng text/xpath dễ vỡ khi đổi UI/đa ngôn ngữ — đây là tài liệu để QA yêu cầu dev bổ sung `resource-id`/`accessibilityId`.
