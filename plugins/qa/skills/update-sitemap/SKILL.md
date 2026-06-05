---
name: update-sitemap
description: Reusable logic to keep the project's navigation sitemap in sync — write/update sitemap/screens/<id>.json (source of truth: route + edges parent→child + keyElement + reach steps + optional elements[] catalog + notes) for any screen a command visits or builds, then regenerate sitemap/sitemap.json with the plugin's gen_sitemap.py. Used by sitemap (EVERY screen crawled, fills elements[]), exploratory (EVERY screen visited), and cook (every Screen built). Web stores route+clicks; app (Appium) stores tap steps. plan-tests only LISTS nodes, never writes.
---

# Skill: update-sitemap

Keep the navigation map current so the AI — and every later case — knows how to reach any screen. Schema: `sitemap/SCHEMA.md` (auto-created on first generate). Source of truth = `sitemap/screens/<id>.json` (one file per screen); the aggregate `sitemap/sitemap.json` is **generated**, never hand-edited.

## When to run
- **`/qa:sitemap`** → for **EVERY screen the crawl visits**, add/update its node **and** fill the `elements[]` catalog (declaration only — `name` + stable locator, no actions/asserts). **Merge** by element `name` on already-known screens; never duplicate, never invent a `screenClass`.
- **`/qa:exploratory`** → for **EVERY screen you visit**, add/update its node — even before a Screen class exists. The `reach` steps are the whole point (later cases navigate by them).
- **`/qa:cook`** → when a Screen/Page Object is created/edited, set/refresh `screenClass` + `keyElement`.
- **`/qa:plan-tests`** → do NOT write files; only **LIST** the nodes to create/update in the plan.

## Procedure
1. **Write/update `sitemap/screens/<id>.json`** (`<id>` = kebab-case screen/feature, **== the filename**). Fill per `sitemap/SCHEMA.md`:
   - `id`, `realName`, `testFeature`, `platform` (`web`|`android`|`ios`).
   - `route` — **web**: the URL/path. **app**: `null` (navigation is by tap → put it in `reach`).
   - `parentId` — the screen you came FROM (this is the edge; `null` for root). `keyElement` — the `isDisplayed()` anchor.
   - `reach` — step-by-step navigation to GET here. **web**: route + clicks (e.g. `"click sidebar 'Invoices'"`). **app**: tap actions (e.g. `"tap tab 'Kho'"`, `"tap row 0"`). Start from `GoToHome` unless pre-login.
   - `screenClass` (FQN once built, else `null`), `home` (bool), `notes` (selectors / status `verified <date>` / bugs / TODOs).
   - `elements` (optional, filled by `/qa:sitemap`) — the **declaration-only** catalog: array of `{name, type, label, strategy, locator, missingId}` per `sitemap/SCHEMA.md`. **No action methods, no assertions, no Page Object class.** When refreshing an existing node, **union by `name`** (add new, keep old) instead of overwriting.
   - One screen = one file → low merge conflict. Edit only the files for the feature you touched. `childrenIds` are auto-derived from `parentId` (you don't need to set them).
2. **(App POM, optional)** if you also captured locators, keep them in the element source per the app design-pattern (`screens/<group>/elements.json` / `test-hints.json`) — that's the POM element catalog, separate from this navigation sitemap.
3. **Regenerate the aggregate** (rebuilds `sitemap.json` + ensures `SCHEMA.md`):
   - macOS/Linux: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_sitemap.py`
   - Windows: `python ${CLAUDE_PLUGIN_ROOT}/scripts/gen_sitemap.py`
   It auto-links `childrenIds`, warns on dangling `parentId` / id≠filename / bad JSON (non-fatal).
4. **Screenshot** (optional, if captured via MCP): `sitemap/screenshots/<id>.jpg` (JPG, not PNG; not on the Desktop).

> The sitemap is a first-class output of `/qa:exploratory` — record it for every screen you walk through, even when the feature is buggy and no test gets written. The next command reads it to find the path to the feature.
