---
name: declare-screen
description: Reusable logic to write/update a "Screen" Page Object following the project's POM standard (Appium Java, cross-platform Android/iOS/Flutter). Used when a command (cook, exploratory) needs to declare a screen as a Screen class — @MobileFindBy fields by locator priority, isDisplayed(), verb-style action methods, NO assert. Includes the strategy for choosing stable locators and hooks into the missing-ids skill for elements lacking an id.
---

# Skill: declare-screen

Reusable capability: turn a screen (just discovered or per the plan) into a standards-compliant **Page Object**. Commands call this skill instead of re-implementing the POM rules themselves. Source standards: [design-pattern §3](../../rules/app/design-pattern.md), [coding-rules.md](../../rules/app/coding-rules.md), [design-system.md](../../rules/app/design-system.md).

## Procedure
1. **File & location**: `src/main/java/com/example/screens/<group>/<Name>Screen.java`, extends `BaseScreen`, constructor `public <Name>Screen(AppiumDriver driver){ super(driver); }`. One sub-screen = one separate Screen (don't cram multiple screens together). Group lowercase, class PascalCase.
2. **Reference the template first**: read `src/main/java/com/example/screens/auth/LoginScreen.java` to follow the correct structure, import order, and `isDisplayed()` pattern.
3. **Element fields** (`public WebElement` + `@MobileFindBy`, camelCase by UI role + type suffix: `loginButton`, `phoneInputTextfield`, `titleLabel`). **Locator priority**: `id` > `accessibility` > `uiautomator` > `xpath` (xpath MUST have a reason comment). Multiple elements → `List<WebElement>`, NOT `driver.findElements()`. Per-platform differing locator → `@MobileFindBys` (Android first, iOS second).
4. **`isDisplayed()`** (MUST): try-catch around the single most distinctive element, return `false` on exception — never throw. Back-loop/reset that needs to be fast → add a `probe = true` field as `List<WebElement>` + `isDisplayedFast()`.
5. **Action methods** = verbs (`enterPhone`, `tapLogin`, `scrollToBottom`); interact via `MobileActions`/element fields. **ABSOLUTELY no assert**, no importing TestNG in the Screen.
6. **Elements missing an id**: every element that cannot be anchored by `id` (currently using accessibility/uiautomator/xpath/text) → call the **`missing-ids` skill** (RECORD) to collect into the Missing ID Report.
7. **Persist elements.json**: newly discovered elements → save into `screens/<group>/elements.json` for reuse (Layer 2 of the 3-layer lookup).

> After declaring: compile green via the **`build-verify` skill**; update the map via the **`update-sitemap` skill**.
