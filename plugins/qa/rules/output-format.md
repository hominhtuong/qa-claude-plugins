# Output Format Rules

File naming, multi-sheet, time estimation, and upload priority conventions for test case output.
**Read when**: command `cook`, skill `tc-template`.

---

## 1. Output Workflow

- **Test case / Checklist**: **MUST** create the local `.xlsx` file first, then upload to Drive.
- Workflow:
  1. Create the `.xlsx` in `results/<feature-name>/` (kebab-case, lowercase, no diacritics).
  2. Upload to Drive via the **Upload Priority** (see section 4).
  3. Return to the user **both** the local file path **and** the Drive URL.
- **Reason**: the local `.xlsx` is a hard backup — if the Drive upload fails, the local copy still exists.
- `.md` files are only used for: test plan, bug analysis report, descriptive documentation.
- Spreadsheet-creation code: reference the helper module `configs/tc_template` (see skill `tc-template`). Do NOT copy/redefine the template functions inline (`sanitize_text`, `sanitize_tc`, `TIME_EST_FORMULA`...) — this is the #1 cause of losing Vietnamese diacritics ("phút" => "phut").

---

## 2. File Naming

- **Per-phase** (multi-phase output): `{prefix}-phase-{N}.xlsx` (e.g. `wir-phase-1.xlsx`).
- **Final merged** (MANDATORY for multi-phase): after merging all phases => save `{prefix}-final.xlsx` containing every sheet.
- **Single-phase**: `{prefix}.xlsx`.
- **prefix** = feature name abbreviation (e.g. `wir` for "Warehouse Inventory Report").
- **Output dir**: `results/<feature-name>/`, lowercase, spaces => hyphens, no diacritics. Auto-create if missing.

---

## 3. Multi-Sheet Rules

- **Each independent feature/module => its own sheet** in the workbook. Sheet name = module name (short).
- **TC_ID RESET per sheet**: each sheet restarts from `TC_001`. Do NOT number continuously across sheets (TC_051 on sheet 2 is WRONG).
- **Each sheet has its own header** (rows 1-7) with COUNTIF formulas referencing data **within that same sheet**, not another sheet. Each sheet has its own Time Est, Create Date, link.
- **When to combine into 1 sheet**: phases/sections belonging to the same feature => sequential TC_ID, divided by section header rows.
- **When to split into multiple sheets**: clearly independent modules/tasks => one sheet per module, TC_ID reset, own header.

---

## 4. Upload Priority Chain

The upload target is determined by config (`.env`), checked in order:

```
1. LARK_DRIVE_FOLDER_ID != null => import to Lark Drive as an editable Lark Sheet
   - Success => return the Lark Sheet URL, DONE
   - Fail (token expired) => auto re-auth => retry
   - Fail (other error) => fall through to step 2

2. GOOGLE_DRIVE_FOLDER_ID != null => upload to Google Sheets
   - Success => return the Google Sheets URL, DONE
   - Fail => report the error, confirm the local .xlsx is still OK

3. Both null => skip upload, return only the local .xlsx path
```

**Key rules**:
- Lark fails => **keep trying Google** (don't stop). Both fail => still confirm the local file is OK, report both errors.
- **DO NOT push each phase separately** — push once AFTER merging all phases => return a single URL.
- Read the folder ID from config (placeholder), do not hardcode the base/folder ID in code.

---

## 5. Time Estimation

- **MUST** add a "Time Est (1 round):" line in the header (column B). Format: `~Xh (Y TCs x avg Z min/TC)`.
- Count the actual TC count accurately (do NOT count section header rows).
- Formula:
  - Simple (UI check, display, toggle): **2 min/TC**
  - Medium (form input, validation, CRUD): **3 min/TC**
  - Complex (API integration, cross-platform, multi-step flow): **4-5 min/TC**
  - Mixed => default **3 min/TC**
  - Buffer **+20%** for setup, navigation, bug logging.

---

## 6. Sanitize Text (MANDATORY)

Replace incorrectly AI-generated characters **BEFORE** writing the file:
- `—` (em dash) / `–` (en dash) => `-`
- `->` => `=>`
- Smart quotes => straight quotes

Apply to ALL: description, precondition, steps, expected, section title. Use `sanitize_text()` / `sanitize_tc()` from `configs/tc_template` (do NOT redefine inline).
