---
description: Compile rồi chạy test với device preflight (real/emulator auto-detect) và tóm tắt report
argument-hint: [android (mặc định) | ios | all | tên test/feature cụ thể]
allowed-tools: Read, Glob, Grep, Bash
---

# /run — Compile & chạy test

Input: **$ARGUMENTS** (platform/suite/test cụ thể; trống = android).

Wrapper mỏng cho **skill `run-tests`** (`${CLAUDE_PLUGIN_ROOT}/skills/run-tests`).

## Thực hiện
1. Chạy **skill `run-tests`**: xác định scope → **compile trước** (`mvn clean compile test-compile`, đỏ thì dừng) → device preflight (đọc `deviceName` từ capabilities: `emulator-*` = emulator auto-start; ngược lại = real device phải có trong `adb devices`/`xcrun`) → chạy `./scripts/run-android.sh` / `run-ios.sh` / `run-all.sh` (hoặc `mvn test -DsuiteXmlFile=<suite>` cho suite tuỳ chỉnh).
2. Báo kết quả: exit code, report mới nhất `reports/<date>/`, passed/failed/skipped/duration.
3. **Triage fail** ([failure-triage.md](../rules/failure-triage.md)): phân định mỗi FAIL là `[APP-BUG]` (app sai → liệt kê defect chuyển dev, KHÔNG sửa test) vs `[FRAMEWORK]`/`[ENV]`/`[DATA]` (→ gợi ý `/fix`). Tóm tắt fail theo nhãn để rõ "app lỗi hay test lỗi".

## Nguyên tắc
- Luôn compile trước khi chạy. Ưu tiên scripts (tự check device). KHÔNG sửa test code — chỉ chạy.
- TestNG XML phải có `GoToHomeTest` là `<test>` block đầu tiên.
