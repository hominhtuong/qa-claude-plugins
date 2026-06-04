---
name: find-elements-web
description: Reusable logic to extract durable elements from the currently open web page (via Playwright MCP browser_snapshot / DOM) and pick stable locators following the web priority getByRole > getByTestId > getByLabel/Placeholder/[name=] > getByText/heading > semantic CSS. Used by the exploratory command (getting elements to declare a Screen) and fix (getting the correct locator when the UI/selector changes). Flags elements missing a data-testid for the missing-ids skill. Serves as input for the cook-web skill.
---

# Skill: find-elements-web

Reusable capability: from the currently open page (after the `navigate-web` skill) → a list of elements + stable Playwright locators, feeding `cook-web`. Locator strategy: [design-system.md §locator](../../rules/web/design-system.md). This skill is the locator-PICKING + catalog-writing part; DOM discovery from the real app runs via Playwright MCP.

## Procedure
1. **Get a snapshot of the current screen**: `mcp__plugin_playwright_playwright__browser_snapshot` (accessibility tree: role + name + ref) — the primary source for choosing `getByRole`. Need raw attributes (`data-testid`, `id`, `name`, `placeholder`, `aria-*`) → `mcp__plugin_playwright_playwright__browser_evaluate` to read the element's DOM.
2. **Pick the locator** by web priority for each important element (top-down preference):
   - `page.getByRole(AriaRole.X, name("..."))` — **best**, closest to the user, survives refactors.
   - `page.getByTestId("...")` — `data-testid` (only when the attribute has been confirmed via `setTestIdAttribute`).
   - `getByLabel` / `getByPlaceholder` / `[name="..."]` — form fields with a stable label/name.
   - `getByText(...)` / `getByRole(HEADING, name)` — static title/label (usable as a key element).
   - **Semantic** CSS — last resort, with a reason comment.
   - ❌ **BANNED**: xpath-with-index, brittle `.nth(n)`, auto-generated classes (`.css-1ab2c3`, Tailwind utilities, `.rs-*`). Multi-language app (EN/VI) ⇒ prefer id/role over text.
3. **Element that can't be anchored by `data-testid`/`id`** (must use text/role-name/css) → mark it so the **`missing-ids` skill** RECORDs it (`status: "missing"`, with `suggestedTestId`). Elements on the Keycloak realm (`#username`/`#password`/`#kc-login`) → `status: "external-sso"`, NOT included in the export.
4. **Choose `screenKeyLocator()`**: 1 element that always appears & is unique when the screen is shown (heading/marker app-shell), language-proof — prefer `data-testid` or role-heading.
5. **Return**: a table `element (role) | chosen locator | raw attributes | missing testid?` for the Screen declaration step.

> This skill only EXTRACTS + picks locators; writing them into Java fields is the `cook-web` skill. Capture evidence → `mcp__plugin_playwright_playwright__browser_take_screenshot`, saved to `.playwright-mcp/`, NOT to Desktop.
