---
name: log-bug
description: Reusable logic to log a bug to a Lark Bitable board — gather required fields (Dev PIC, Sprint, Version, Feature), score Severity/Priority via severity-priority.md, read-only board guard (block create on a production view), daily multi-board confirmation, Python-first Lark API (do NOT print token). Board ID read from .env/config (placeholder), not hardcoded. Used by the log-bug command.
---

# Skill: log-bug

A reusable capability to **create a bug record** on Lark Bitable per the team template. Scoring rules: [severity-priority.md](../../rules/severity-priority.md).

> **LANGUAGE — RULE #1**: Generate the Vietnamese content (Name, Steps, Actual, Expected) in Vietnamese (with diacritics). Steps must be clear and reproducible (same quality standard as test cases).
>
> **CREATE ONLY — never modify/delete an existing record**.

## Procedure

1. **Load config (placeholder, not hardcoded)**:
   - The active board is read from `.env`/config: `LARK_BUG_BASE_ID`, `LARK_BUG_TABLE_ID` (+ `LARK_BUG_BASE_NAME` for display/confirm). If not set => ask the user for the Lark Bitable URL, extract the ID from the pattern `.../base/<BASE_ID>?table=<TABLE_ID>`. If the user pastes a board URL in the prompt => use it directly.
   - Field cache (if the project has one): resolve Dev PIC / Sprint / Feature / Version from the cache FIRST; only call `list_fields` on a cache miss or when the data changes.
2. **Read-only guard (CHECK BEFORE every create)**: the board is read-only if ANY source reports:
   - `.env` flag `LARK_BUG_READ_ONLY` = `true`/`1`/`yes`.
   - State file board (e.g. `.board-state.json`) key `read_only` = true.
   - Board registry note marked `READ-ONLY` / production view.
   => If read-only: **STOP, do NOT create**, tell the user (production board), instruct to swap to the STG board or temporarily bypass (`LARK_BUG_READ_ONLY=false`). Do NOT bypass on your own, do NOT change the board on your own.
3. **Multi-board daily confirmation**: if the registry has >= 2 boards => at the start of each day, the FIRST bug must confirm with the user that it points to the correct board (compare `last_confirm_date`/`confirmed_alias` in the state file against today + the active board). Mismatch => show a confirmation, wait for the user. Only 1 board => skip. User pastes a new board URL in the prompt => skip confirmation that time.
4. **Gather required fields** (ASK if missing from both the prompt and `.env` defaults):
   - **Dev PIC** (lookup cache => open_id; no match => ask).
   - **Sprint** (cache => `DEFAULT_SPRINT` from `.env` => ask). Skip per platform if applicable.
   - **Version** (cache => `DEFAULT_VERSION` from `.env` => ask). Skip per platform if applicable.
   - **Feature / Tính năng** (match cache; ambiguous => ask).
   > Platform-based skip: Admin Portal doesn't attach Sprint/Version; Web doesn't attach Version (depends on the board schema — read the field list when unsure).
5. **Auto-fill the remaining fields** (no need to ask): Name (`[Tính năng/màn hình] Mô tả bug`), Platform (detect from context, default `App`), Type (UI/UX vs Function vs Performance), Source/Status (per board schema, new bug = `New`).
6. **Score Severity/Priority** per [severity-priority.md](../../rules/severity-priority.md): user provides => validate (large mismatch with evidence => ask to confirm); not provided => auto-estimate + write a short rationale. If the board has no Severity field => use Priority only.
7. **Attachment** (if any): image/video => read & ANALYZE the content to understand the bug (which screen, steps, actual vs expected) before filling. User has a short description => prioritize the description, with media adding detail. Upload via the Lark helper (Python), get the `file_token`. Upload fails => create the bug without attachment, tell the user to add it manually.
8. **Lark API — Python-first**: use the project's Python helper (e.g. `configs/lark_api.py`: `create_record`, `search_records`, `list_fields`, `update_record`) for ALL Bitable operations. Do NOT use `mcp__lark*` (often fails token expired). **NEVER print a token/secret** to output.
9. **Body template** for the `Input data / Action` field:
   ```
   Preconditions (nếu có):
   - ...
   Steps:
   1. ...
   Actual:
   - ...
   Notes (nếu có):
   - ...
   ```
   `Expected result` field: `Expected:` + content.
10. **Create + return link**: full info => create directly (run a duplicate-check first if the project enables it); missing required fields => show a draft + ask. After create => build a direct link to the record from config (`get_lark_record_url`/base URL). Multiple bugs in one prompt => create sequentially, return a summary table.

> This skill creates the bug record. Detailed scoring => rule `severity-priority.md`.
