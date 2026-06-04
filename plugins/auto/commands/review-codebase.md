---
description: Review the ENTIRE codebase against the design system, coding rules and cross-file consistency
argument-hint: [empty = scan the whole project]
allowed-tools: Read, Glob, Grep, Bash
---

# /review-codebase — Review the whole project

Thin wrapper. All rule-inspection logic lives in **skill `review-audit`** (`${CLAUDE_PLUGIN_ROOT}/skills/review-audit`), run in **whole-codebase** mode.

## Execution
1. Run **skill `review-audit`** scope = everything: Glob `src/main/java/com/example/screens/**/*.java`, `src/test/java/com/example/tests/**/*.java`, `screens/**/elements.json`, `testng/**/*.xml`, `configurations/*.properties`, `scripts/*.sh`. Read EVERY file, no sampling.
2. Cross-check rules by each file group's platform (web → `rules/web/*`, app → `rules/app/*`) + review-checklist; classify files → section.
3. **Cross-file consistency**: Screen↔Test mapping (each Screen has ≥1 Test) · package alignment `screens/<group>` ↔ `tests/<group>` · TestNG coverage (every Test class is in an XML) · elements.json ↔ @MobileFindBy sync · GoToHomeTest is the first `<test>` in every XML · unused/missing imports.
4. **Risk assessment**: High (hard-coded secret, missing `isDisplayed()`) · Medium (`Thread.sleep`, `driver.findElement()` in a Test, naming drift) · Low (style/comment).

## Output
Codebase Review Report: summary + Health Matrix (% table by category) + Critical/Warning/Suggestions (each issue with `path:line` + code + fix) + Cross-file Analysis + **Missing ID Report** consolidated + Risk Summary + Recommendations. Clean codebase → acknowledge it, don't invent issues.
