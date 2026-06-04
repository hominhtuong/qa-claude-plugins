---
name: find-elements-android
description: Reusable logic to extract durable elements from the currently open Android screen (via Appium MCP page source / source-inspector agent) and pick stable locators following the Android priority id > accessibility > uiautomator > xpath. Used by the cook-app skill and the exploratory/fix command when the platform is android. Flags elements missing an id for the missing-ids skill. Serves as input for the declare-screen skill.
---

# Skill: find-elements-android

Reusable capability: from the currently open Android screen (after the `navigate-app` skill) → a list of elements + stable locators, feeding `declare-screen`/`cook-app`. Locator strategy: [design-system §locator](../../rules/app/design-system.md). Heavy discovery from the real app is done by the **`source-inspector` agent** (`${CLAUDE_PLUGIN_ROOT}/agents/agent-source-inspector.md`) running via Appium MCP (UiAutomator2); this skill is the locator-PICKING + catalog-writing part.

## Procedure
1. **Get the page source** of the current screen: `appium_get_page_source` (or a dump from `source-inspector`). Grasp the element tree + raw Android attributes: `resource-id`, `content-desc`, `text`, `class`, `bounds`, `clickable`.
2. **Pick the locator** by **Android priority** for each important element (top-down):
   - `id` (resource-id, e.g. `tab_inbound_all`) — **best**, the most stable anchor.
   - `accessibility` (content-desc, e.g. `"Tạo nhập hàng"`) — when there's no id (Flutter often sets content-desc to the VN label).
   - `uiautomator` (`new UiSelector()...`, **Android-only**) — when id/content-desc aren't enough. Real idioms:
     - `new UiSelector().resourceIdMatches(".*table_card.*")` — dynamic/repeated ids (lists).
     - `new UiSelector().descriptionContains("Tab 1 trong")` — content-desc by pattern.
     - `new UiSelector().className("android.widget.Button").instance(n)` — pick by type + order.
     - `new UiScrollable(new UiSelector().scrollable(true)).scrollIntoView(new UiSelector().text("..."))` — scroll to an off-screen element.
   - `xpath` — **last resort**, MUST have a reason comment (e.g. `(//android.widget.Button)[1]`). Avoid hardcoded xpath + brittle indices.
3. **Element without an `id`** (must use accessibility/uiautomator/xpath) → mark `hasId: false` so the **`missing-ids` skill** RECORDs it when the Screen is written.
4. **Write the catalog**: save the element + chosen locator into `screens/<group>/elements.json` (persist Layer 2 of the 3-layer lookup). Each entry: `{ strategy, locator, hasId, desc }`.
5. **Return**: a table `element (role) | chosen locator | raw attributes | missing id?` for the Screen declaration step.

> This skill ONLY extracts + picks Android locators; writing them into Java fields is the `declare-screen` skill. `@MobileFindBy(uiautomator=...)` is **Android-only** (iOS skips it). Cross-platform elements with differing locators between the two OSes → combine with `@MobileFindBys` (see `find-elements-ios` skill). [MCP Screenshot Rule] screenshots via MCP use JPG — **pass the full relative path as the `filename`**: `sitemap/screenshots/<name>.jpg` (a bare file name falls back to the MCP output dir / project root), NOT to Desktop.
