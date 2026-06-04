---
name: update-board
description: Reusable logic to manage the Lark bug board registry in .claude/qa-claude/log-bug.config.yml — add a board from its URL (extract base/table/view/wiki ids), switch the active board by alias, and refresh field/option/dev-pic mappings from the live board. Used by the update-board command and when /log-bug needs to point at a different board.
---

# Skill: update-board

Edit the bug board registry so `/log-bug` writes to the right place. Target file: `.claude/qa-claude/log-bug.config.yml` (created by skill `setup`). **NEVER print tokens/secrets.**

## Procedure
1. **Locate config**: `.claude/qa-claude/log-bug.config.yml`. Missing → tell the user to run skill `setup` first.
2. **Parse the input** (`$ARGUMENTS`):
   - **Board URL** → extract ids:
     - `https://<domain>.larksuite.com/base/<base_id>?table=<table_id>&view=<view_id>` → `base_id`, `table_id`, `view_id`.
     - `https://<domain>.larksuite.com/wiki/<wiki_token>?table=<table_id>&view=<view_id>` → `wiki_token`, `table_id`, `view_id` (resolve `base_id` via the Lark helper/MCP if needed).
   - **Existing alias** (no URL) → just switch `active_board` to it.
3. **Add / update the board** under `boards:`:
   - Ask the user for a short `alias` (map key) + whether it is `read_only` (production = true).
   - Write `name`, `base_id`, `table_id`, `view_id`, `wiki_token`, `read_only`. Confirm before overwriting an existing alias.
   - Set `active_board` to this alias if `--active` is passed or it's the only board.
4. **Refresh mappings** (optional — ask the user): read the live fields (project `list_fields`, or Lark MCP `bitable appTableField_list`) and update:
   - `fields:` — logical name → actual board field name.
   - `options:` — `priority`/`type`/`platform` option lists + `status_new`.
   - `dev_pic:` — resolve open_ids for any developer names the user provides.
5. **Write back** the YAML (preserve comments/structure where possible) and print: the new `active_board`, its `read_only` state, and a 3-line summary of what changed.

## Rules
- Edit ONLY `.claude/qa-claude/log-bug.config.yml`. Never touch `.claude/qa-claude/.env` secrets, never print tokens.
- This file is the user's own copy — `setup` does NOT overwrite it (only the `.example.yml` reference is refreshed).
- After a switch, note that `/log-bug` now targets the new board and enforces its `read_only` guard.
