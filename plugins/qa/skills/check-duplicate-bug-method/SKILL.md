---
name: check-duplicate-bug-method
description: Reusable logic to check for a duplicate bug on the Lark Bitable board before logging a new one. Parses free text or a structured payload (name/feature/platform/keywords...), extracts 2–3 meaningful keywords, searches the board via scripts/lark_bitable.py --search, drops closed records + keyword-only false positives, assesses true duplicates by same feature/screen + similar wrong behavior, and returns a decision (create new / potential duplicate → user picks). Never creates a record. Reusable core behind the check-duplicate-bug command; also callable by log-bug before creating.
---

# Skill: check-duplicate-bug-method

Reusable capability: before a bug is logged, find whether the board already has it — so the team doesn't pile up duplicates. **This skill never creates a record**; it only returns a decision.

> 🎯 Prefer **fewer false positives** over flooding results. A shared keyword alone is not a duplicate — the wrong behavior must match.

## Input modes
1. **Free text** (standalone use) — e.g. "Lỗi thanh toán không áp dụng chiết khấu ở màn hình Bán hàng".
2. **Structured payload** (when `log-bug` calls it):
   ```
   name: [Bán hàng] Không áp dụng chiết khấu khi thanh toán
   feature: Bán hàng
   platform: App
   keywords: chiết khấu, thanh toán
   ```

## Procedure
1. **Parse** the input. Title = `name` (or the free text). Pull `feature/platform/priority/sprint/version/keywords` if present (improves filtering).
2. **Build keywords** — 2–3 meaningful tokens from the title: drop a `[Feature]` prefix, prefer the behavior/error phrase. If the user passed `keywords`, use them (sanitized).
3. **Search the board**:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/lark_bitable.py" --search "<kw1>,<kw2>,<kw3>"
   ```
   No board config / `ok:false` → relay the `action` (run `/qa:setup` or `/qa:update-board` / `/qa:auth-lark`) and STOP (don't guess).
4. **Filter**: drop closed records (`Closed/Done/Rejected/Reject/Cancel`); drop keyword-only false positives (same word, different defect).
5. **Assess** a true duplicate = same `feature`/main screen context AND similar wrong behavior (not just one shared word). Unsure → keep it, label `Cần xác nhận`.
6. **Return the decision** (no record created):
   - **No relevant duplicate** → conclusion: safe to create a new bug.
   - **Potential duplicate(s)** → show the similar-bug table + ask the user: (a) create anyway / (b) skip as duplicate.
   - **Search API/network error** → warn; recommend the caller (`/qa:log-bug`) continue creating, do NOT block.

## Output format
```
--- Kết quả kiểm tra Duplicate Bug ---
Bug đang kiểm tra: Name · Feature · Keywords
Kết luận: <Không phát hiện bug trùng / Phát hiện bug tương tự>

| # | Bug ID | Name | Status | Priority | Sprint | Link |
|---|--------|------|--------|----------|--------|------|

Đề xuất hành động: <tiếp tục tạo bug mới / cần user xác nhận>
```
No results → print a short empty table + the reason.

## Rules
- **Never create/edit/delete** a record in this skill.
- Missing board config → report clearly and stop. Search error → warn, don't assert a firm conclusion.
- Prefer reducing false positives over returning noisy matches.
- **LANGUAGE**: output in the configured output language (default Vietnamese with diacritics; technical terms in English) — see `../../rules/output-language.md`.
- **Integration**: when `/qa:log-bug`'s `check_duplicate: true`, call this before creating a record.
