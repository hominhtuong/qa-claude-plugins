---
name: missing-ids
description: Reusable logic to manage "test-id debt" — elements in a Screen that cannot yet be anchored by id (temporarily using accessibility/uiautomator/xpath/text). Three capabilities: RECORD (collect elements missing an id into the Missing ID Report), EXPORT (run scripts/export_missing_ids.py to collect across the whole project to send to dev), RESOLVE (when dev has added the id). Used by cook/fix/exploratory/review-* or run standalone via the missing-test-ids command.
---

# Skill: missing-ids

> **Output language**: any prose in the Missing ID Report meant for the dev (descriptions, notes) follows the **configured language** (`.plugin.env` `LANGUAGE`, default Vietnamese with diacritics) — see [output-language.md](../../rules/output-language.md). Element names, locators, screen ids, and the `suggestedTestId` stay English/technical.

Reusable capability: record/list/export elements missing an `id` so QA can ask dev to add it. Why it exists: the most durable anchor is `resource-id`/`accessibilityId`; locators by text/xpath/uiautomator break easily on UI changes / i18n. Standard (static rule): coding-rules §Missing ID Report ([app](../../rules/app/coding-rules.md) · [web](../../rules/web/coding-rules.md)), the matching checklist item in review-checklist ([app](../../rules/app/review-checklist.md) · [web](../../rules/web/review-checklist.md)).

## Capability 1 — RECORD (caller invokes when declaring an element)
When `declare-screen`/`cook`/`fix` declares an element for a Screen that **cannot** be anchored by `id`:
1. Temporarily use the most stable locator (priority `accessibility` > `uiautomator` > `xpath`).
2. Collect it into the **Missing ID Report** (the output table at the end of the task) — do NOT report elements that already have an `id`:
```
⚠️ **Missing ID Report** — Elements without an ID, dev needs to add them:

| Element name | Location / Screen | Current locator | Description |
|-------------|-------------------|-------------------|-------|
| termsText   | Onboarding        | uiautomator: `new UiSelector().description("Tôi đồng ý với ")` | Terms checkbox |
```

## Capability 2 — EXPORT (run standalone or at the end of exploratory/cook)
1. Run `python3 scripts/export_missing_ids.py` — scan all `screens/<group>/*.java` + `elements.json`, collect elements using non-id locators.
2. Print summary: number of screens scanned, total elements missing an id (broken down by locator type), path to the output file.
3. This is the document sent to dev to add `resource-id`/`accessibilityId`.

## Capability 3 — RESOLVE (after dev adds the id)
Dev adds the id → switch the locator field to `@MobileFindBy(id = "...")` in the Screen + update `elements.json` → re-run EXPORT so the list shrinks. Verify the compile is green via skill `build-verify`.

> This skill references rules, it does not duplicate them. Callers: skill `declare-screen`, commands `/qa:cook` `/qa:fix` `/qa:exploratory` `/review-*` `/qa:missing-test-ids`.
