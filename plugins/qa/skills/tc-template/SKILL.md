---
name: tc-template
description: Output contract for the test case spreadsheet — 15-column layout (Testcase ID, Description, Pre-Condition, Steps to Perform, Steps Expected Result, Status Build STG/PRD, Bug ID, Time Est, isAuto, Build devices, Notes), header rows 1-7 with COUNTIF formula, TC_ID reset per sheet, freeze row 8, upload priority Lark Drive > Google Sheets > local xlsx. Code uses the helper module configs/tc_template (no inline Python). Used by the cook command and skill gen-testcases.
---

# Skill: tc-template

A reusable capability to **build the test case spreadsheet file** per the project's standard contract. Input: data rows from skill `gen-testcases`. Naming/upload convention: [output-format.md](../../rules/output-format.md).

> **LANGUAGE — RULE #1**: Content follows the **configured output language** (`.plugin.env` `LANGUAGE`, **default Vietnamese**) — see [output-language.md](../../rules/output-language.md). When Vietnamese, ALL strings (including string literals in code/formula) **MUST have diacritics**: `&" phút / "` NOT `&" phut / "`. Missing diacritics = WRONG.
>
> **CODE — no inline**: every `create_*.py` script MUST `import` from the helper module **`configs/tc_template`** (e.g. `save_xlsx_local`, `create_tc_spreadsheet`, `create_multi_sheet_tc_spreadsheet`, `sanitize_text`, `sanitize_tc`, `TOTAL_COLS`, `TIME_EST_FORMULA`). Do NOT copy/redefine these functions/constants inline — this is the #1 cause of losing Vietnamese diacritics. (The helper module is the project's own Python config file; call it by NAME, do not re-inline its contents.)

## Procedure

1. **Prepare data rows**: receive a list of TC dicts from skill `gen-testcases` (each dict: `id`, `desc`, `precond`, `steps`, `expected`, `time_est`, `merge_with_prev` for multi-result). Sanitize text before writing (`sanitize_text`/`sanitize_tc` from the helper).
2. **15-column layout (A-O)** — header rows 7-8:

   | Col | Header (row 7) | Sub (row 8) |
   |-----|----------------|-------------|
   | A | Testcase ID | |
   | B | Testcase Description | |
   | C | Pre-Condition | |
   | D | Test Procedures (merge D-E) | Steps to Perform |
   | E | | Steps Expected Result |
   | F | Status (merge F-G) | Build STG |
   | G | | Build PRD |
   | H | Bug ID | |
   | I | Time Est | |
   | J | isAuto | |
   | K-M | Build #1 / devices | Device #1 / #2 / #3 |
   | N | Status #1 | |
   | O | Notes | |

3. **Header rows 1-7** (each sheet has its own header):
   - Row 1: `Link DOC:` | (link) ... `Passed` | `=COUNTIF(F-range, D1)`
   - Row 2: `Link Figma:` | (link) ... `Failed` | `=COUNTIF(F-range, D2)`
   - Row 3: `Create by` | (name/set via config) ... `Not start` | `=COUNTIF(F-range, D3)`
   - Row 4: `Create Date` | {YYYY-MM-DD} ... `Cancel` | `=COUNTIF(F-range, D4)`
   - Row 5: total `=SUM(E1:E4)` (Testcases)
   - Row 6: `Time Est (1 round):` | (auto-formula converting minutes => hours+minutes)
   - Row 7: Story Point (if the project enables it) — `{SP} points ({role})`
   - COUNTIF references the Status column **within that same sheet**, `valueInputOption = USER_ENTERED` so Google Sheets evaluates the formula.
4. **Status column**: data validation dropdown — `PASSED`, `FAILED`, `NOT START`, `CANCEL`; default `NOT START`; center-aligned.
5. **Multi-result merge**: for a group of TCs with the same description, merge cells in column B (Description) and C (Pre-Condition) across the rows (`merge_with_prev=True` from the 2nd row onward).
6. **Formatting**: header rows 7-8 bg `#CCFFFF` bold center; data columns C-O wrap + align top; **freeze row 8** (`A9`); thin border `#D0D0D0` across the whole data area; **do not fix row height** (auto-resize); Time Est column I is minutes/TC (used to compute the B6 total).
7. **TC_ID RESET per sheet**: each sheet restarts from `TC_001`. Multi-module => one sheet per module (`create_multi_sheet_tc_spreadsheet`), each sheet with its own header + COUNTIF.
8. **Save locally first**: `save_xlsx_local(...)` => `.xlsx` file in `results/<feature-name>/` (hard backup). Name it per [output-format §2](../../rules/output-format.md): `{prefix}-phase-N.xlsx`, merged => `{prefix}-final.xlsx`.
9. **Upload via the priority chain** ([output-format §4](../../rules/output-format.md)): `LARK_DRIVE_FOLDER_ID` (Lark Sheet) > `GOOGLE_DRIVE_FOLDER_ID` (Google Sheets) > local-only. Read the folder ID from config (placeholder), do not hardcode. Lark fails => try Google; both fail => confirm local is OK.
10. **Return**: both the local path **and** the Drive URL (a single URL after merging all phases). Do NOT push each phase separately.

> This skill builds the **file/format/upload**. TC content is produced by skill `gen-testcases`. Phase-splitting is by skill `plan-testcases`.
