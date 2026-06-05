---
description: Add/switch the active Lark bug board and refresh field/option/dev-pic mappings in .claude/qa-claude/log-bug.config.yml from a board URL or alias (so /qa:log-bug knows where to write)
argument-hint: <Lark board URL | alias to switch to> [--active]
allowed-tools: Read, Glob, Grep, Edit, Write, Bash
---

# /qa:update-board — Manage the bug board registry

Input: **$ARGUMENTS** (a Lark board URL to add, or an existing `alias` to switch to).

Run **skill `update-board`**. It edits `.claude/qa-claude/log-bug.config.yml` (created by skill `setup`). **NEVER print tokens/secrets.**

## What it does
1. **No config yet** → tell the user to run `/qa:setup` first (it creates `.claude/qa-claude/log-bug.config.yml`).
2. **Given a board URL** → extract `base_id` / `table_id` / `view_id` / `wiki_token` from the URL pattern (`.../base/<base_id>?table=<table_id>&view=<view_id>` or `.../wiki/<wiki_token>?table=...`). Add or update a board entry under `boards:` (ask the user for a short `alias` + whether it's `read_only`). With `--active` (or if it's the only board) → set `active_board` to it.
3. **Given an existing alias** → set `active_board` to that alias (switch).
4. **Refresh mappings** (optional, ask): read the live board fields (project Lark helper `list_fields`, or Lark MCP `bitable...appTableField_list`) → update `fields:` (field names), `options:` (priority/type/platform/status), and resolve any new `dev_pic:` open_ids the user names. Write back to the config.

## Rules
- Only edit `.claude/qa-claude/log-bug.config.yml` — do not touch `.claude/qa-claude/.plugin.env` secrets.
- Confirm before overwriting an existing board entry. Print the resulting active board + a 3-line summary.
- After switching, remind the user that `/qa:log-bug` will write to the new active board (and respects its `read_only`).
