---
description: Review the current git change (diff) against the design system & coding rules, output findings with code + how to fix
argument-hint: [path/file/feature | empty = uncommitted diff]
allowed-tools: Read, Glob, Grep, Bash
---

# /review-change — Review git changes

Scope: **$ARGUMENTS** (empty → uncommitted changes).

Thin wrapper. All rule-inspection logic lives in **skill `review-audit`** (`${CLAUDE_PLUGIN_ROOT}/skills/review-audit`).

## Execution
1. Run **skill `review-audit`** with scope = `$ARGUMENTS` (or the current diff if empty): `git diff HEAD` + `git diff --cached` + new files. The skill is **platform-aware**: it identifies each file's platform (web Playwright vs app Appium) → reads the correct rule set `rules/web/*` or `rules/app/*` (nothing extra), classifies files → checklist section, checks each item, build-checks, outputs findings by severity.
2. **Review only, don't fix.** Each finding: clickable `path:line` + actual code + fix code. Order Critical → Warning → Info.
3. User wants to fix → suggest `/fix` (skill `fix-by-layer`).

## Output
Report in the skill `review-audit` format: summary (files, critical/warning issues), file reviews (PASS/FAIL/SKIP check table), issues with fixes, **Missing ID Report** consolidated, Documentation Sync (CLAUDE.md/README/TestNG need updating?). Conclusion CLEAN/WARNINGS/ISSUES FOUND. Clean → say so briefly, don't pad.
