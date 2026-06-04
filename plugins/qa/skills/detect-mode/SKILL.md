---
name: detect-mode
description: Decide whether a QA task is AUTOMATION (write/run test code) or MANUAL (generate test cases / analyze specs into spreadsheets) and route the shared commands to the right skills. Used by the dual-purpose commands cook/plan-tests/analyze/count-cases, analogous to detect-platform for web/android/ios.
---

# Skill: detect-mode

Determine the working mode for a dual-purpose command → **`automation`** or **`manual`**. The calling command then reads ONLY the matching branch (save tokens).

- **automation** = produce/operate test CODE (Page Objects, test classes, run suites) in an automation framework (Appium/Playwright Java).
- **manual** = produce QA artifacts as DOCUMENTS (test cases in xlsx/Sheet, requirement analysis, manual test plans).

## Decision order (first match wins)
1. **Explicit override** in `$ARGUMENTS`: `mode:auto`/`mode:manual`, `--auto`/`--manual`, or unambiguous intent in the request ("write test code", "Page Object", "run the suite" → automation; "generate test cases", "test case spreadsheet", "analyze the spec", "TC_ID" → manual).
2. **The artifact in the argument**:
   - A spec/PRD/Figma link or a doc with no code to produce → **manual**.
   - A request to write/edit Page Objects / test classes, or to run/compile a suite → **automation**.
   - A `plans/<feature>/*.md` plan → open it: a manual test-case plan (TC_ID ranges, sections, Test Case Matrix) → **manual**; an automation plan (Screens/POM/Steps to code, TestNG XML) → **automation**.
3. **Project signal** (detect the repo type):
   - **automation** if the repo is a test-automation codebase — `pom.xml`/`build.gradle` with Appium/Playwright/TestNG, `src/test/java/**`, `playwright.config.*`, `testng*.xml`, or existing Page Objects/Screens.
   - **manual** if it's a docs/spec repo with no test framework (or the task only references docs/sheets).
4. **Ambiguous** → ask the user once: *"Automation (write/run test code) or Manual (generate test cases / analyze specs)?"*

## Output
A single `mode` = `automation` | `manual`. Hand it back to the calling command, which reads only that mode's section. For `automation`, the command additionally runs `detect-platform` (web/android/ios) inside its branch.
