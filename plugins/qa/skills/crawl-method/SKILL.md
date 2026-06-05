---
name: crawl-method
description: Reusable, platform-agnostic logic to CRAWL an app/web target and build the navigation sitemap with a per-screen element catalog — BFS-walk every reachable screen (or only a given feature subtree), and for each screen declare its elements (name + stable locator only) into sitemap/screens/<id>.json. Discovery ONLY — it never writes tests, never hunts bugs, never triages, never generates Page Object code. Used by the /qa:sitemap command. Delegates per-screen element picking to find-elements-web/-android/-ios, node-writing to update-sitemap, and id-debt to missing-ids.
---

# Skill: crawl-method

Reusable capability: systematically **walk** a target app/site and record what's there — the screen graph (`reach`/`parentId`) **plus** a declaration-only **element catalog** per screen. This is the engine behind `/qa:sitemap`. It is **discovery, not testing**: the only outputs are `sitemap/screens/*.json` files (+ the regenerated `sitemap.json`).

## Hard boundaries (what this skill MUST NOT do)
- ❌ **No tests** — never write a Screen/Page Object class, test method, or `/qa:cook`/`/qa:plan-tests` output.
- ❌ **No bug hunting** — do not probe for defects, do not assert expected vs actual, do not produce a bug report or `[APP-BUG]`/triage tags. If something is obviously broken and blocks navigation, note it in the node's `notes` and move on.
- ❌ **No mutating actions** — navigate and read only. Do NOT submit forms, create/delete records, send messages, or change server state. To reveal a screen you may click navigation (menus, tabs, rows, "detail"/"view"), but avoid destructive/irreversible buttons (Delete, Pay, Send, Confirm). When a screen can only be reached by a write action, record the path in `reach` and skip entering it.
- ✅ **Only** declare elements (`name` + stable locator) and update the sitemap.

## Inputs (from the command)
- `platform` — locked by `detect-platform` (`web` | `android` | `ios`).
- `scope` — either **whole app** (no feature given) or a **feature subtree** (e.g. `home`, `invoice`): crawl only that screen and everything reachable *underneath* it.
- the existing `sitemap/sitemap.json` (if any) — so the crawl is **incremental**: known screens get refreshed/extended, not re-discovered from scratch.

## Procedure (BFS crawl)
1. **Seed the frontier.**
   - Whole-app scope → start at **Home** (`navigate-web` / `navigate-app` → `GoToHome`). Seed = Home + the top-level entry points visible from the app shell (sidebar/menu/tab-bar items, dashboard cards).
   - Feature scope → resolve the feature to its start screen via the existing sitemap's `reach` (or by matching `realName`/`id`), navigate straight there, and treat **that** screen as the BFS root (only descend into its children).
2. **Maintain a visited set** keyed by screen identity (route for web; key on-screen anchor/title for app) so you never crawl the same screen twice. Pre-load it with the ids already in `sitemap.json`.
3. **For each screen popped from the frontier:**
   a. **Confirm you're on it** — capture the screen (web: `browser_snapshot`; app: source/screenshot via the navigate skill) and pick the `keyElement` (the stable anchor that proves the screen is shown).
   b. **Declare elements** — run the matching platform skill (**web** `find-elements-web` · **android** `find-elements-android` · **ios** `find-elements-ios`) to get each meaningful element + its stable locator by that platform's priority. Convert each into an `elements[]` entry: `name` (camelCase, role+type suffix — the future POM field name), `type`, `label` (visible text, keep Vietnamese diacritics), `strategy`, `locator`, `missingId`. **Catalog only — no action methods, no assertions.** Skip purely decorative chrome; keep interactive controls, inputs, headings/labels that identify data, list/row containers, tabs, and navigation affordances.
   c. **Record id debt** — every element that can't be anchored by a stable id/testid → mark `missingId: true` and hand it to the **`missing-ids`** skill (RECORD) so dev gets a Missing ID Report. (Record-only; don't block the crawl.)
   d. **Write the node** via the **`update-sitemap`** skill: `id`/`realName`/`testFeature`/`platform`, `route` (web URL · app `null`), `parentId` (the screen you came FROM), `keyElement`, `reach` (web: route + clicks · app: tap steps from `GoToHome`), `home`, and the `elements[]` catalog from (b). **Merge, don't clobber**: if the node already exists, keep its data and union new elements by `name`; set `screenClass` only if it was already set (never invent one).
   e. **Discover children** — from the snapshot, enqueue every *navigable* child not in the visited set (menu items, tabs, list rows → detail, "view/detail" links, pagination into a sub-view). Respect `scope`: in feature scope, only enqueue children that belong under the feature root. Apply the mutating-action boundary above.
4. **Loop** until the frontier is empty (whole app) or the feature subtree is exhausted.
5. **Regenerate** the aggregate once at the end (or periodically for a big crawl): `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_sitemap.py` (Windows: `python`). It auto-links `childrenIds` and warns on dangling refs / id≠filename.

## Crawl hygiene
- **Idempotent**: re-running `/qa:sitemap` on an already-mapped target should mostly *refresh* nodes (add newly found elements, fix moved routes), not create duplicates. Reuse the existing `id` for a screen you recognize.
- **Bounded**: cap obvious infinite fan-out — for a long list, map the list screen + **one** representative row→detail, not every row. Note "list of N items; detail mapped from row 0" in `notes`. Don't paginate endlessly.
- **Loops/back-edges**: if a child links back to an ancestor, just set `parentId` to the first screen you reached it from; don't re-crawl.
- **Auth walls / dead ends**: a screen you can't enter without a write/irreversible action → record it as a child with `reach` describing the gate and `notes: "not entered — requires <action>"`. Don't force it.
- **Vietnamese**: all `realName`/`label`/`notes` in Vietnamese MUST keep diacritics — no-diacritic text is wrong.

## Output (back to the command)
A short summary: platform · scope (whole app / feature) · **count of screens mapped/updated** · total elements declared · count of `missingId` elements handed to `missing-ids` · path `sitemap/sitemap.json` + any generator warnings. No tests, no bug report — by design.

> Sibling to `exploratory-method`: same "walk the app" motion, opposite intent. `exploratory-method` *judges* the app (oracle, bugs, gate); `crawl-method` only *inventories* it (screens + elements). When in doubt, do less: record and move on.
