# Sitemap — schema (for AI/commands, not end users)

A map of the app/site so an agent can answer *"to reach screen X, which route/screen class,
how do I navigate there, and what elements live on it?"* without re-scanning everything.
**Built up by `/qa:sitemap`** (a pure discovery crawl — walks every screen and declares its
elements, no tests/bugs) and **`/qa:exploratory`** (as it explores); read by `/qa:plan-tests`,
`/qa:cook`, and the `navigate-*` skills so later cases know how to get to a feature and what's on it.

## Files
- `sitemap/screens/<id>.json` — **source of truth**, one file per screen (member-owned ⇒ low merge conflict).
- `sitemap/sitemap.json` — **generated** aggregate (rebuilt by the plugin script; do NOT hand-edit).
- `sitemap/SCHEMA.md` — this file.
- `sitemap/screenshots/<id>.jpg` — optional multimodal reference.

## Regenerate the aggregate
After adding/editing any `screens/<id>.json`, run:

```bash
# macOS/Linux
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_sitemap.py
# Windows
python  %CLAUDE_PLUGIN_ROOT%\scripts\gen_sitemap.py
```

It reads every `screens/*.json`, auto-derives `childrenIds` from each node's `parentId`,
warns on dangling refs / id≠filename, and writes `sitemap/sitemap.json`.

## Node schema (`sitemap/screens/<id>.json`)
```json
{
  "id": "invoice",                 // kebab-case, == file name, stable
  "realName": "Hoá đơn điện tử",   // real product feature name (vi/en)
  "testFeature": "invoice",        // test slug / package
  "platform": "web",               // web | android | ios
  "screenClass": "com.example.screens.invoice.InvoiceListScreen", // FQN, or null if not built yet
  "route": "/invoices",            // WEB: the URL/path. APP: null (navigation is by tap → see `reach`)
  "parentId": "home",              // the screen you came FROM (the edge); null for root
  "childrenIds": ["invoice-detail"], // optional — auto-derived from children's parentId
  "keyElement": "heading 'Invoices'", // what isDisplayed() checks (stable anchor)
  "reach": ["GoToHome", "click sidebar 'Invoices'"], // HOW to get here, step by step
  "home": false,
  "elements": [                      // declared by /qa:sitemap — pure catalog, NO actions/asserts
    {
      "name": "createInvoiceButton", // camelCase: UI role + type suffix (the future POM field name)
      "type": "button",              // button|textfield|label|link|image|icon|tab|list|row|checkbox|radio|dropdown|toggle|...
      "label": "Tạo hoá đơn",        // visible text / name (vi keeps diacritics), or null
      "strategy": "role",            // WEB: role|testid|label|placeholder|text|css · APP: id|accessibility|uiautomator|xpath
      "locator": "getByRole('button', { name: 'Tạo hoá đơn' })", // platform-ready selector string
      "missingId": false             // true → no stable id/testid (candidate for the Missing ID Report)
    }
  ],
  "notes": "free-form: statuses (mapped <date>), TODOs"
}
```

> `elements` is a **declaration-only catalog** (the inventory `/qa:sitemap` produces): each entry names an
> element + its stable locator, nothing else — **no action methods, no assertions, no Page Object class**.
> `/qa:cook` later turns these into a real Screen/Page Object; `/qa:sitemap` never writes code.

## Web vs App — what to put in the edge (screen A → screen B)
- **Web**: set `route` (the URL/path) **and** `reach` (the click path, e.g. `"click sidebar 'Invoices'"`). The edge = route change + clicks.
- **App (Appium android/ios)**: `route` = `null`; the edge lives entirely in `reach` — the **tap actions** that move screen A → B (e.g. `"tap tab 'Kho'"`, `"tap row 0 in the list"`). `parentId`/`childrenIds` record which screen leads to which.

## Rules
- One screen ⇒ one file. Edit only the files for the feature you touched.
- `/qa:sitemap` and `/qa:exploratory` **MUST** add/update a node for **every screen they visit** — even before a Screen class exists. `reach` is the value: later cases navigate by it.
- `/qa:sitemap` additionally fills `elements` (the declaration-only catalog) for every screen it crawls; it **updates** existing nodes (merge new elements by `name`, never duplicate) and never writes tests, hunts bugs, or generates Page Object code.
- Keep `reach` short & imperative; start from `GoToHome` unless the screen is pre-login.
- After editing any node, run the generator to refresh `sitemap.json`.
