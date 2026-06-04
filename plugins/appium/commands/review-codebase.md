---
description: Review TOÀN BỘ codebase so với design system, coding rules và cross-file consistency
argument-hint: [để trống = quét toàn dự án]
allowed-tools: Read, Glob, Grep, Bash
---

# /review-codebase — Review toàn dự án

Wrapper mỏng. Toàn bộ logic soi rule nằm ở **skill `review-audit`** (`${CLAUDE_PLUGIN_ROOT}/skills/review-audit`), chạy ở chế độ **toàn codebase**.

## Thực hiện
1. Chạy **skill `review-audit`** scope = toàn bộ: Glob `src/main/java/com/sbh/screens/**/*.java`, `src/test/java/com/sbh/tests/**/*.java`, `screens/**/elements.json`, `testng/**/*.xml`, `configurations/*.properties`, `scripts/*.sh`. Đọc EVERY file, không lấy mẫu.
2. Đối chiếu 4 rule (@${CLAUDE_PLUGIN_ROOT}/rules/...) + review-checklist; phân loại file → section.
3. **Cross-file consistency**: Screen↔Test mapping (mỗi Screen có ≥1 Test) · package alignment `screens/<group>` ↔ `tests/<group>` · TestNG coverage (mọi Test class có trong XML) · elements.json ↔ @MobileFindBy sync · GoToHomeTest là `<test>` đầu mọi XML · import thừa/thiếu.
4. **Risk assessment**: High (secret hard-code, thiếu `isDisplayed()`) · Medium (`Thread.sleep`, `driver.findElement()` trong Test, naming lệch) · Low (style/comment).

## Đầu ra
Codebase Review Report: summary + Health Matrix (bảng % theo category) + Critical/Warning/Suggestions (mỗi issue kèm `path:line` + code + fix) + Cross-file Analysis + **Missing ID Report** tổng hợp + Risk Summary + Recommendations. Codebase sạch → thừa nhận, đừng bịa lỗi.
