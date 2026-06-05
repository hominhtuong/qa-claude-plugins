---
description: Discovery crawl — walk the whole app/web target (or just one feature), declare every screen's elements (name + stable locator only) and build/refresh the navigation sitemap under sitemap/. Pure mapping — NO tests, NO bug hunting, NO Page Object code. Auto-route by platform, reading only the matching skill.
argument-hint: [feature-name] [web|android|ios] [nav path if known]
allowed-tools: Read, Glob, Grep, Edit, Write, Bash, Agent
---

# /qa:sitemap — Crawl & map the app into the sitemap (elements + navigation)

Scope to map: **$ARGUMENTS** (empty → the **whole** app/web from Home).

**Goal**: produce/refresh the project's **sitemap** — the screen graph + a per-screen **element catalog** (each element's `name` + stable locator) — by walking the target. This is the input that lets `/qa:plan-tests`, `/qa:cook`, and the `navigate-*` skills know *how to reach* a screen and *what's on it*.

> ⚠️ **Discovery ONLY.** This command does **not** write tests, does **not** hunt bugs, does **not** triage, and does **not** generate Page Object classes. The only deliverable is `sitemap/screens/*.json` (+ the regenerated `sitemap/sitemap.json`). If a screen is visibly broken, jot it in the node's `notes` and keep crawling — no bug report.
> ⚠️ **Read-only navigation.** Click only to *reveal* screens (menus, tabs, rows, detail/view). Never trigger destructive/irreversible actions (Delete, Pay, Send, Confirm) just to map — record the gate in `reach`/`notes` and skip.

## Step 0 — Lock platform + scope (routing)
1. Run **skill `detect-platform`** (argument / auto-detect / ask) → one `platform`. Do NOT read the other platforms' skills.
2. Read `sitemap/sitemap.json` if it exists → load the already-mapped screens so this run is **incremental** (refresh/extend, don't duplicate). First run with no `sitemap/` folder → it will be created at the project **root** (`sitemap/` with `sitemap.json`, `SCHEMA.md`, and `screens/` holding one `<id>.json` per screen) by the `update-sitemap` skill + generator.
3. **Resolve scope** from `$ARGUMENTS`:
   - A feature name (e.g. `home`, `invoice`, `quản lý đơn` → `quan-ly-don`) → **feature scope**: crawl only that screen and everything reachable *underneath* it. Match it to a start screen via the existing sitemap's `reach`/`realName`/`id`.
   - No feature name → **whole-app scope**: crawl every screen reachable from Home.

## Step 1 — Open the start screen (only the locked platform skill)
- **web** → skill **`navigate-web`** (Playwright MCP: navigate + login → Home, or straight to the feature's start screen if scoped).
- **android | ios** → skill **`navigate-app`** (Appium MCP: device preflight + install + session + `GoToHome` → start screen).

## Step 2 — Crawl & declare — skill `crawl-method` (agnostic, core)
Run **skill `crawl-method`**: BFS-walk every reachable screen in scope. For **each** screen:
- pick the `keyElement` (stable anchor), then run the matching find-elements skill (**web** `find-elements-web` · **android** `find-elements-android` · **ios** `find-elements-ios`) to extract elements + stable locators;
- write each into the node's `elements[]` catalog (`name` camelCase / `type` / `label` with diacritics / `strategy` / `locator` / `missingId`) — **declaration only, no actions/asserts**;
- elements with no stable id/testid → **skill `missing-ids`** (RECORD) for the Missing ID Report (record-only, don't block);
- write/refresh the node via skill **`update-sitemap`** (`route`/`parentId`/`keyElement`/`reach`/`home` + `elements[]`), **merging** by element `name` for already-known screens (never duplicate, never invent a `screenClass`);
- enqueue navigable children (menus, tabs, rows→detail, view links) within scope; respect the read-only + bounded-fan-out rules (map a long list + one representative row→detail, not every row).

## Step 3 — Regenerate the aggregate
After the crawl, refresh `sitemap/sitemap.json`:
- macOS/Linux: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_sitemap.py`
- Windows: `python %CLAUDE_PLUGIN_ROOT%\scripts\gen_sitemap.py`

It auto-links `childrenIds` from `parentId`, ensures `SCHEMA.md`, and warns (non-fatal) on dangling refs / id≠filename / bad JSON.

## Step 4 — Finish
Close the session (`appium_quit_session` / `browser_close`). Print: **platform**, **scope** (whole app / feature `<name>`), **# screens mapped/updated**, **total elements declared**, **# `missingId` elements** sent to the Missing ID Report, the path `sitemap/sitemap.json` + any generator warnings, and the suggested next step (`/qa:plan-tests <feature>` to plan, or `/qa:cook` to turn the catalog into Page Objects). **No tests, no bug report — by design.**

> Difference vs `/qa:exploratory`: same "walk the app" motion, opposite intent. `exploratory` *judges* the app (spec oracle → bugs → GATE). `sitemap` only *inventories* it (screens + elements) — the cheap, safe first pass that fills the map every later command reads.
