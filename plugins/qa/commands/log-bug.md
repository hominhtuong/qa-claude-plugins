---
description: Log a bug to a Lark Bitable board from the description in the prompt (with image/video if any); board ID read from .env/config, read-only guard, daily multi-board confirm
argument-hint: <bug description> [dev pic: ... | sprint: ... | version: ... | attachment: /path]
allowed-tools: Read, Glob, Grep, Edit, Write, Bash
---

# /log-bug — Log a bug to Lark Bitable

You are a **Senior QC Engineer** logging a bug into the team's Lark Bitable board. Request: **$ARGUMENTS**. The output follows the team's bug template exactly.

> **LANGUAGE — RULE #1**: Generate the Vietnamese content (Name, Steps, Actual, Expected) in Vietnamese (with diacritics). Steps must be clear and reproducible.
> **CREATE ONLY** — never modify/delete an existing record. **NEVER print a token/secret**.

## Must read first
- @${CLAUDE_PLUGIN_ROOT}/rules/severity-priority.md (scoring Severity/Priority)
- Skill `log-bug` (field-gathering + create-record workflow)

## Config (placeholder — do not hardcode the base ID)
- The active board is read from `.env`/config: `LARK_BUG_BASE_ID`, `LARK_BUG_TABLE_ID`, `LARK_BUG_BASE_NAME`. Not set => ask the user for the Lark Bitable URL, extract the ID from the pattern `.../base/<BASE_ID>?table=<TABLE_ID>`. User pastes a board URL in the prompt => use it directly.
- Field cache (if the project has one): resolve Dev PIC / Sprint / Feature / Version from the cache before calling the API.

## Read-only guard (CHECK BEFORE every create)
The board is read-only if ANY source reports: `.env` flag `LARK_BUG_READ_ONLY` (true/1/yes) · state file board key `read_only` · registry note `READ-ONLY`/production view. Read-only => **STOP, do NOT create**, tell the user to swap to the STG board or temporarily bypass (`LARK_BUG_READ_ONLY=false`). Do NOT bypass/change the board on your own.

## Multi-board daily confirmation
Registry >= 2 boards => at the start of each day, the FIRST bug confirms whether it points to the correct board (compare the state file against today + the active board). Only 1 board => skip. User pastes a new board URL => skip that time.

## Workflow (per skill `log-bug`)
1. **Required fields** (ASK if missing from both the prompt and `.env` defaults): **Dev PIC**, **Sprint**, **Version**, **Tính năng/Feature**. Platform-based skip applies if the board schema requires it (Admin Portal/Web drop Sprint/Version depending on the board).
2. **Auto-fill**: Name (`[Tính năng/màn hình] Mô tả bug`), Platform (default `App`), Type (UI/UX vs Function vs Performance), Source/Status (new bug = `New`).
3. **Severity/Priority** per `severity-priority.md`: user provides => validate (large mismatch => ask); not provided => auto-estimate + rationale. Board has no Severity => Priority only.
4. **Attachment** (image/video): read & analyze the content to understand the bug, then fill Steps/Actual/Expected; upload via the Lark Python helper, get the `file_token`. Upload fails => create the bug without attachment, notify the user.
5. **Lark API Python-first**: use the project's Python helper (e.g. `configs/lark_api.py`). Do NOT use `mcp__lark*`.
6. **2 modes**: full info => create directly (duplicate-check first if the project enables it); missing required fields => show a draft + ask. After create => return a direct record link. Multiple bugs in one prompt => create sequentially, return a summary table.

## Rules
- Do NOT modify/delete an existing record — CREATE only.
- Full info = no redundant confirmation, create & return the link. Missing a required field = must ask.
- Board fields don't match the template => read the field list first (`list_fields`) then adapt.
- Generate the Vietnamese content with diacritics; steps held to the same quality standard as test cases.
