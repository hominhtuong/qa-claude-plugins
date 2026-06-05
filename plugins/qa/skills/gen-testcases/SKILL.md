---
name: gen-testcases
description: Engine for writing production-quality manual test cases from a requirement/spec/Figma/plan. Applies the test-quality.md standard — steps describe actions only (action+data+UI location), expected result separated out, multi-result format (1 objective N expected => N TC_ID rows, merge description/precondition), 1 objective/TC, MANDATORY negative coverage, no redundant expected ("app doesn't crash", color-code checks). Output language follows .plugin.env LANGUAGE (default Vietnamese with diacritics). Used by the cook command (main phase/sub-agent) and fix.
---

# Skill: gen-testcases

A reusable capability to **write manual test cases** at the Senior QC standard — output immediately executable, no further explanation needed. Full reference standard: [test-quality.md](../../rules/test-quality.md). Spreadsheet output contract: skill `tc-template`.

> **LANGUAGE — RULE #1 (MANDATORY)**: Generate all test case content in the **configured output language** (`.plugin.env` `LANGUAGE`, **default Vietnamese with diacritics**) — description, precondition, steps, expected result, section title. By default "Đăng nhập" is NOT "Dang nhap"; "Mật khẩu" is NOT "Mat khau"; keep technical terms in English (API, token, session). Vietnamese content without diacritics is WRONG and must be fixed. Full policy: [output-language.md](../../rules/output-language.md). When a command spawns a sub-agent to call this skill, pass the resolved language and **repeat this rule verbatim**. (An explicit `language: English` in the request overrides the env setting.)

## Procedure

1. **Analyze the requirement**: read the specs/PRD/plan-tests/Figma summary carefully. List every testable scenario, business rule, validation rule, UI behavior, integration point (API/DB/third-party). When both Figma + PRD are present => use the Four-Part Coverage Framework ([test-quality §6.2](../../rules/test-quality.md)).
2. **Detect Specs vs Figma conflicts**: if contradictory => **STOP, ask the user** (follow Docs / follow Figma / case by case); do not decide on your own. Mark the result in the Precondition (`[Resolved: ...]`). See [test-quality §6.3](../../rules/test-quality.md).
3. **Design coverage** — group by section, each section a clear logical group. Ensure full:
   - **Positive** (happy path, valid input)
   - **Negative** (MANDATORY — wrong input, error handling, empty, permission denied, locked account...). Each positive must have a corresponding negative.
   - **Boundary** (min/max, character limits, extreme quantities)
   - **Edge** (empty/null, special characters, concurrent, network loss, multi-device)
4. **Write TCs by the core principles** ([test-quality §1-5](../../rules/test-quality.md)):
   - **1 objective / TC** — do not combine multiple scenarios; TCs independent.
   - **Steps = actions ONLY** (action + data + UI location). Do NOT write a step that looks like a verification ("Confirm the table has 5 columns" is an expected, not a step).
   - **Expected result separated out** — describe concretely how the UI/message/data/navigation/state changes. NO redundant expected: "app doesn't crash", "no error", "works normally". NO color-code/hex checks. NO confusing context-free references ("per BR16").
   - **Multi-result format** (when 1 description has N expected): create N rows, each row 1 TC_ID + 1 step + 1 expected; Description & Pre-Condition **identical** across rows (cells will be merged in the xlsx). See [test-quality §3](../../rules/test-quality.md).
5. **Complete precondition** for each TC: account state (logged in, role, permission), required existing data, environment/setting.
6. **Assign Priority** for each TC: Critical / High / Medium / Low ([test-quality §6.4](../../rules/test-quality.md)). Leave the Test Type & isAuto columns blank.
7. **TC_ID**: format `TC_001`, `TC_002`... ascending, **RESET per sheet** (each sheet restarts from TC_001). Checklist uses `CL_001`, Regression uses `RT_001`.
8. **Sanitize** before writing: `—`/`–` => `-`, `->` => `=>`, smart quotes => straight quotes. Use the helper from skill `tc-template`, do not redefine inline.
9. **Self-check** against the Quality Checklist [test-quality §7](../../rules/test-quality.md) BEFORE output: complete preconditions? steps are actions? no redundant expected? enough negative? multi-result correct? Vietnamese with diacritics? TC_ID reset per sheet?
10. **Hand off output** to skill `tc-template` to build the spreadsheet (15 columns, header rows 1-7, upload via the priority chain).

> This skill **only writes TC content**. Building the file/upload is skill `tc-template`. Phase-splitting/estimation is skill `plan-testcases`.
