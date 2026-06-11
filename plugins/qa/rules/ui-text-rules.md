# Rule: text conformance — static labels vs dynamic values

Used by /qa:exploratory-ui's text layer (`ui_compare.py --design-text`, skill `ui-text-compare`).
The local engine EXTRACTS the text (Figma tokens for the design + OCR for the app) and matches it by
position; THIS rule is how the AI decides which mismatches are real bugs. The core distinction:

- **Static label** = UI copy that is fixed by the design: it should read EXACTLY what Figma says.
  A difference here is a **bug** (typo, wrong word, wrong language, truncation, missing label).
  *Examples:* screen/section titles ("Products", "Hóa đơn"), button text ("Lưu", "Thanh toán"),
  field labels ("Tên khách hàng", "Tổng tiền:"), tab/menu names, table headers, empty-state copy,
  fixed hints/placeholders.
- **Dynamic value** = content that comes from DATA and legitimately differs from the Figma sample:
  do **NOT** flag a content difference. *Examples:* list/row items, customer names, prices, amounts,
  dates/times, quantities, statuses, IDs/codes, search results, user-entered text, counts/badges.

> The Figma frame shows *sample* data. So "Products" (a header) must match, but the items under it
> ("item 1", "item 2" in the design vs "sản phẩm nháp", "sản phẩm thật" in the app) are data — ignore
> the content difference. **Catch `Products` ≠ `Product`; ignore the item list.**

## What the engine gives you (per matched text)
Each `text.mismatch` / `text.missing` finding carries: `design_text`, `app_text`, `similarity`
(0–1), `likely_dynamic` (heuristic), plus the design tokens (`design_color`, `design_font`,
`design_weight`, `design_size`) and a `where` region. The engine's first-pass heuristic:
- `likely_dynamic = true` when the text has digits / currency / %, or similarity is low (< 0.55) →
  it pre-marks the finding `warn` (probably data).
- `likely_dynamic = false` with high similarity → pre-marked `fail` (a static label that changed).

## How the AI decides (override the heuristic with judgement)
1. **Is this a label or a value?** Use the design context: the Figma node's role/position (a header,
   a button, a fixed label) ⇒ static; a repeated row, a number, a name ⇒ dynamic. The
   `figma-reader` summary + the screen's purpose tell you which.
2. **Static label mismatch ⇒ `[APP-BUG]`.** Report it: `design_text` vs `app_text`. Typical bugs:
   wrong word ("Products"→"Product"), missing diacritics ("Đăng nhập"→"Dang nhap"), wrong copy,
   truncated/clipped text, wrong language, label swapped.
3. **Dynamic value mismatch ⇒ ignore the CONTENT.** Don't file a bug for different data. You MAY
   still note *format/state* problems that are design-governed even on dynamic text — e.g. a price
   shown without the currency unit, a date in the wrong format, text overflowing its box, the wrong
   color/weight on the value — but those come from the color/typography/layout findings, not the
   content diff.
4. **`text.missing`** (design has a label, app shows nothing there): could be a genuinely missing
   label (bug) OR an empty/different state/data (not a bug). Decide from context; if unsure mark
   `[NEEDS-TRIAGE]` and confirm on the screenshot — don't assert.
5. **OCR noise guard:** OCR can misread (especially low-contrast or tiny text, or Vietnamese
   diacritics without the `vie` pack). Before calling a 1–2 character difference a bug, sanity-check
   against the heatmap/screenshot. A whole-word change ("Products"→"Product") is reliable; a single
   wrong accent might be OCR — verify.

## Output
For each confirmed static-label mismatch, a plain-language bug line (see
[ui-conformance-report-template.md](ui-conformance-report-template.md)) citing design vs actual text.
Dynamic values never appear as bugs. When OCR is unavailable (no backend), say so — text comparison
was skipped, only color/font/layout were checked.
