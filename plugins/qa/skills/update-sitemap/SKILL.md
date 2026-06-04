---
name: update-sitemap
description: Reusable logic to update the screen map (sitemap) + element catalog whenever a screen is touched. Used when a command (exploratory, cook) has just created/edited a Screen or discovered an element via MCP. Update elements.json + test-hints.json + sitemap.md then regenerate with the script. plan only lists the nodes to be touched.
---

# Skill: update-sitemap

Reusable capability: keep the navigation map in sync with the code, so the AI navigates correctly next time. Sitemap system: [design-pattern §5](../../rules/app/design-pattern.md). Details: `sitemap/README.md`.

## Procedure (Auto-Update Rule — after MCP discovery / element change)
1. **`screens/<group>/elements.json`** — add/update the locator of a newly discovered element (the source for the 3-layer Layer 2 lookup).
2. **`screens/<group>/test-hints.json`** — if a new form field is discovered: add the field metadata, validation, business rule (for `/plan-tests`, `/cook`).
3. **`sitemap/sitemap.md`** — add a new screen entry to the navigation index (screen name, path from Home, entry points, characteristic element). Existing screen with a new element → update it.
4. **Screenshot** (if captured via MCP): save to `sitemap/screenshots/<name>.jpg` (JPG, not PNG; don't leave it on the Desktop).
5. **Regenerate**: `python3 sitemap/scripts/gen_sitemap_v2.py` (sitemap.md) + `python3 sitemap/scripts/gen_test_hints.py` (test-hints.json).

> At `/plan-tests`: do NOT write files — only **list** the nodes/screens to create/update (path from Home, key element) in the plan for `/cook` to execute later.
