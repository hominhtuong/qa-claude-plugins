---
name: review-audit
description: Reusable logic to audit a set of changes (diff) or the whole codebase against the project's review-checklist and emit findings by severity (Critical/Warning/Info). Used by the review-change command (diff), review-codebase (everything), and push-code/merge-request (quality gate before commit). Audits & reports ONLY, does NOT auto-fix (fixing is the fix-by-layer skill).
---

# Skill: review-audit

Reusable capability: check rule & design-pattern compliance → a list of findings. **Platform-aware**: load rules for the platform of the FILE being reviewed (don't read in the other platform's rules unnecessarily).
- Playwright Java file (web: `Locator`, `getByRole`, `com.microsoft.playwright`) → check against `rules/web/`: [design-pattern](../../rules/web/design-pattern.md) · [coding-rules](../../rules/web/coding-rules.md) · [design-system](../../rules/web/design-system.md) · [review-checklist](../../rules/web/review-checklist.md).
- Appium Java file (app: `@MobileFindBy`, `AppiumDriver`) → check against `rules/app/`: [design-pattern](../../rules/app/design-pattern.md) · [coding-rules](../../rules/app/coding-rules.md) · [design-system](../../rules/app/design-system.md) · [review-checklist](../../rules/app/review-checklist.md).
- Repo with both → review per platform, using the right rule set for each group of files.

## Procedure
1. **Determine scope & platform** (the `detect-platform` skill if needed):
   - Path/feature given → review that file/feature; identify the platform from the file content.
   - Empty (review-change) → uncommitted changes: `git diff HEAD` + `git diff --cached` + new files (`git status --porcelain`). No changes → review the latest commit `git diff HEAD~1..HEAD`.
   - Everything (review-codebase) → Glob sources per platform: web `src/**/screens/**/*.java` + `tests/**`; app `screens/**/*.java` + `tests/**` + `elements.json` + `testng/**/*.xml` + `configurations/*.properties` + `scripts/*.sh`.
2. **Classify files → checklist sections** (per the platform's review-checklist): Screen/Page Object · Test · (app) TestNG XML · Config · Script · Doc.
3. **Check EACH item** of the platform's review-checklist. Mandatory focus:
   - Layering: Screen does not assert · assertions only in Test · interaction in Screen not in Test.
   - POM locators: **web** `getByRole > getByTestId > label/text > css` (no xpath-index, no `.nth()`); **app** `@MobileFindBy` `id > accessibility > uiautomator > xpath` (no `driver.findElement()` in Test). Screen has `isDisplayed()`.
   - Red flags: `Thread.sleep`/`page.waitForTimeout`, hard-coded secret, auto-generated class locator.
   - Naming/package matches the group; (app) GoToHomeTest is the first `<test>` in the TestNG XML.
   - **Missing ID**: has each non-id/non-testid element gone into the Missing ID Report (the `missing-ids` skill)?
4. **Build check** if relevant: `mvn clean compile test-compile` (via the `build-verify` skill).
5. **Cross-file** (review-codebase): Screen↔Test mapping, package alignment, TestNG coverage, elements.json ↔ @MobileFindBy sync, unused/missing imports.
6. **Finding format** (MANDATORY per finding): clickable `path:line` link + the **actual code** that's wrong + the **fix code**. Order Critical → Warning → Info.
7. **Conclusion**: CLEAN / WARNINGS / ISSUES FOUND + count by severity + consolidated Missing ID Report.

> This skill **only audits, does not fix**. Caller wants a fix → the `fix-by-layer` skill. Clean codebase → say so briefly, don't invent issues.
