---
description: Check for a duplicate bug on the Lark Bitable board BEFORE logging a new one. Parses free text or a structured payload, extracts 2–3 keywords, searches the board (read-only), drops closed records + keyword-only false positives, and returns a decision (safe to create / potential duplicate → you pick). Never creates a record. Prefers fewer false positives. For QA/QC.
argument-hint: <bug description> | name: ... feature: ... keywords: ...   [--board <alias>]
allowed-tools: Read, Glob, Grep, Bash
---

# /qa:check-duplicate-bug — Duplicate check before logging

You are a **Senior QC Engineer** screening for duplicate bugs before a new one is logged. Request: **$ARGUMENTS**. Core logic = the **`check-duplicate-bug-method`** skill. This command **never creates a record** — it only returns a decision.

> **LANGUAGE — RULE #1**: output in the configured output language (`.plugin.env` `LANGUAGE`, **default Vietnamese with diacritics**; keep technical terms in English) — see [output-language.md](../rules/output-language.md).
> **Read-only**: never creates/edits/deletes a record. **NEVER print a token/secret.**
> No input → show usage and ask for a bug description.

## Must read first
- @${CLAUDE_PLUGIN_ROOT}/skills/check-duplicate-bug-method/SKILL.md (parse, keywords, search, decision)

## Orchestration
1. **Parse** `$ARGUMENTS`: free text → title; structured payload → pull name/feature/platform/keywords.
2. **Keywords**: 2–3 meaningful tokens (drop a `[Feature]` prefix; prefer the behavior/error phrase; honor a `keywords:` list).
3. **Search**: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/lark_bitable.py" --search "<kw1>,<kw2>,<kw3>"` (`--board <alias>` overrides). No config / `ok:false` → relay the `action` (`/qa:setup`, `/qa:update-board`, or `/qa:auth-lark`) and stop.
4. **Filter** closed records + keyword-only false positives; assess true duplicates (same feature/screen + similar wrong behavior; unsure → `Cần xác nhận`).
5. **Return the decision** per the skill's output format (no record created). Search error → warn and recommend `/qa:log-bug` continue, don't block.

## Usage guide (when no input)
```
--- /qa:check-duplicate-bug ---
Kiểm tra bug trùng trước khi tạo bug mới (không tạo record).
  1) Text tự do:  /qa:check-duplicate-bug Lỗi thanh toán không áp dụng chiết khấu ở màn Bán hàng
  2) Structured:  /qa:check-duplicate-bug
                  name: [Bán hàng] Không áp dụng chiết khấu khi thanh toán
                  feature: Bán hàng
                  keywords: chiết khấu, thanh toán
```

## Rules
- Never create/edit a record here. Missing board config → report and stop; search error → warn, no firm conclusion.
- Prefer fewer false positives over noisy matches.
- Vietnamese with diacritics; technical terms in English.
- Ready to log after checking? `/qa:log-bug` (it can also run this automatically when `check_duplicate: true`).
