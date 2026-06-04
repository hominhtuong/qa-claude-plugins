---
name: find-elements-ios
description: Reusable logic to extract durable elements from the currently open iOS screen (XCUITest) (via Appium MCP page source / source-inspector agent) and pick stable locators following the iOS priority accessibility/id > iosNsPredicate > iosClassChain > xpath. Used by the cook-app skill and the exploratory/fix command when the platform is ios. Flags elements missing an accessibility id for the missing-ids skill. Serves as input for the declare-screen skill.
---

# Skill: find-elements-ios

Reusable capability: from the currently open iOS screen (after the `navigate-app` skill) → a list of elements + stable XCUITest locators, feeding `declare-screen`/`cook-app`. Locator strategy: [design-system §locator](../../rules/app/design-system.md). Heavy discovery from the real app is done by the **`source-inspector` agent** (`${CLAUDE_PLUGIN_ROOT}/agents/agent-source-inspector.md`) running via Appium MCP (XCUITest); this skill is the locator-PICKING + catalog-writing part.

## Procedure
1. **Get the page source** of the current screen: `appium_get_page_source` (or a dump from `source-inspector`). Grasp the element tree + raw iOS attributes: `name`/`accessibilityIdentifier`, `label`, `value`, `type` (class), `visible`, `rect`. iOS classes look like `XCUIElementTypeButton`/`Other`/`StaticText`/`TextField`.
2. **Pick the locator** by **iOS priority** for each important element (top-down):
   - `accessibility`/`id` (accessibilityIdentifier — `id` maps to the same accessibility id on iOS) — **best**, the most stable anchor.
   - `iosNsPredicate` (`-ios predicate string`) — when there's no accessibility id. E.g.: `type == 'XCUIElementTypeButton' AND name == 'login'`, `label CONTAINS 'Tiếp tục' AND visible == true`.
   - `iosClassChain` (`-ios class chain`) — query by tree + index, more stable than xpath. E.g.: `**/XCUIElementTypeButton[`name == "login"`]`, `**/XCUIElementTypeCell[2]/XCUIElementTypeStaticText`.
   - `xpath` — **last resort**, MUST have a reason comment. Avoid hardcoded xpath + brittle indices.
3. **Element without an accessibility id** (must use predicate/classChain/xpath) → mark `hasId: false` so the **`missing-ids` skill** RECORDs it when the Screen is written.
4. **Write the catalog**: save the element + chosen locator into `screens/<group>/elements.json` (persist Layer 2 of the 3-layer lookup). Each entry: `{ strategy, locator, hasId, desc }`.
5. **Return**: a table `element (role) | chosen locator | raw attributes | missing id?` for the Screen declaration step.

> This skill ONLY extracts + picks iOS locators; writing them into Java fields is the `declare-screen` skill. `iosNsPredicate`/`iosClassChain` are **iOS-only** (Android skips them). Cross-platform elements with differing locators between the two OSes → combine with `@MobileFindBys({ @MobileFindBy(uiautomator=...), @MobileFindBy(iosClassChain=...) })` (Android entry first, iOS second). [MCP Screenshot Rule] screenshots via MCP use JPG — **pass the full relative path as the `filename`**: `sitemap/screenshots/<name>.jpg` (a bare file name falls back to the MCP output dir / project root), NOT to Desktop.
