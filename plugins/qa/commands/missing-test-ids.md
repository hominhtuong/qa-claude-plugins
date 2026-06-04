---
description: Manage "test-id debt" — EXPORT the list of elements missing an id to send to dev, RECORD a new element, or RESOLVE once dev has added the id
argument-hint: [export (default) | record <screen> <element> | resolve <screen> <element>]
allowed-tools: Read, Glob, Grep, Edit, Write, Bash
---

# /qa:missing-test-ids — Manage "test-id debt"

Input: **$ARGUMENTS** (empty → default `export`).

Thin wrapper for **skill `missing-ids`** (`${CLAUDE_PLUGIN_ROOT}/skills/missing-ids`). For the locator priority standard + Missing ID Report: see the `coding-rules.md` of the enabled plugin domain (e.g. `appium`) — locator priority `id > accessibility > uiautomator > xpath`.

## Routing by `$ARGUMENTS`

| Argument | Skill capability | Action |
|---|---|---|
| `export` *(default)* | EXPORT | `python3 scripts/export_missing_ids.py` → scan `screens/<group>/*.java` + `elements.json`, collect non-id elements, print summary + path to the output sent to dev. |
| `record <screen> <element>` | RECORD | Add the element missing an id to that Screen's Missing ID Report (temporary locator + description). |
| `resolve <screen> <element>` | RESOLVE | After dev adds the id: switch the locator field to `@MobileFindBy(id=...)` + update `elements.json` → re-run EXPORT so the list shrinks; verify the compile is green (skill `build-verify`). |

## Output
- **export**: number of screens scanned, total elements missing an id (broken down by locator type: accessibility/uiautomator/xpath/text), path to the output file.
- **record/resolve**: the Screen/elements.json files touched + the new status.

> Elements missing an `id` anchored by text/xpath break easily on UI changes / i18n — this is the document for QA to ask dev to add a `resource-id`/`accessibilityId`.
