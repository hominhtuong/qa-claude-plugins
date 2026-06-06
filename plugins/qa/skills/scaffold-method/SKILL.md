---
name: scaffold-method
description: Reusable logic to scaffold a brand-new standard QA automation project (Playwright-Web or Appium-App, Page Object Model) from scratch — so a fresh repo gets the canonical structure + a compiling, runnable skeleton, and users only call /qa:plan-tests to add features. Runs scripts/scaffold.py to lay the directory tree + static boilerplate (pom/Makefile/suites/configs/.env/.gitignore/sitemap), then GENERATES the framework Java classes + ONE example feature (auth/login + GoToHome) following the platform design-pattern, then gates on build-verify (mvn test-compile). Safe: never overwrites existing code. Reusable core behind the scaffold command.
---

# Skill: scaffold-method

Reusable capability: turn an **empty repo** into a ready, compiling automation framework that follows this plugin's architecture exactly — so the next step for anyone (even non-technical) is just `/qa:plan-tests <feature>` → `/qa:cook`. The structure itself teaches the user what goes where.

> 🎯 Output a project that **compiles and can run** (`make smoke` reaches Login), not just empty folders. Static config is copied deterministically; the Java framework is generated from the platform design-pattern; `build-verify` is the gate.

## Inputs
- **platform**: `web` (Playwright Java) or `app` (Appium Java). The command resolves this (flag `--web`/`--app`, else ask).
- **package**: base Java package (e.g. `com.<org>.app`). Ask if not given; derive `group`/`artifact`/`name` from it + the repo name.
- **base URL** (web) / **app id+activity or bundle** (app): ask or take from the prompt; safe placeholders are fine (the user edits `.env`/configs later).

## Procedure
1. **Guard**: if `pom.xml` or `src/` already exists → this is NOT an empty repo. Do NOT scaffold over it; tell the user to use `/qa:cook`/`/qa:plan-tests` to extend, or pass `--force` only if they truly want to add the skeleton alongside.
2. **Lay the skeleton** (deterministic) — run the script (cross-platform: `python3` macOS/Linux, `python` Windows):
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scaffold.py" --platform <web|app> \
     --package <pkg> --name "<Project Name>" --base-url "<url>" [--id-url ...] [--home-path ...]
   ```
   It creates the canonical dir tree (`src/main/java/<pkg>/{config|core|flows|utils|models|sitemap|report|screens/...}` + `src/test/java/<pkg>/{base|tests|smoke|regressions}` for web; the Appium layout for app), copies + token-substitutes the boilerplate (`pom.xml`, `Makefile`, suites/testng XML, `configs/*.properties.example`, `.env.example`, `.gitignore`, `sitemap/SCHEMA.md`), and prints what it wrote. It **never deletes** files.
3. **Read the platform architecture** — `../../rules/<platform>/design-pattern.md` (+ `coding-rules.md`, `design-system.md`). This is the exact contract the generated classes must follow (web: §7 browser lifecycle — one window per run).
4. **Generate the framework layer** (the `.gitkeep` dirs the script made) — write the shared infra classes per the design-pattern, mirroring the reference structure:
   - **web**: `config/ConfigManager`+`Environment`, `core/PlaywrightFactory`(idempotent `getOrStartPage`/`closeAll`)+`RunContext`+`AppState`+`AppStateDetector`, `flows/GoToHome`, `utils/Log`+`WaitUtils`+`DataGenerator`, `models/User`, `sitemap/SitemapNode`+`SitemapManager`, `report/ExtentManager`+`ReportConfig`+`TestRunResult`, `screens/base/BaseScreen`; test side `base/BaseTest`(@BeforeSuite/lazy `getOrStartPage` + **@AfterSuite `closeAll`** — never close per method)+`BaseTests`+`BaseRegressionTest`+`BaseSmokeTest`+`RetryAnalyzer`+`RetryListener`+`ReportListener`+`SitemapListener`+`TestData`.
   - **app**: `appium/AppiumServer`, `actions/MobileActions`, `models/Capabilities`+`Environment`+`UserInfo`, `utils/PropertyReader`+`Utils`(`recoverToHome`)+`MobileFindBy`+`ExtentReport`+`FLog`, `screens/base/BaseScreen`; test side `base/BaseTest`(driver lifecycle)+`BaseRegression`(auto `recoverToHome`)+`RetryListener`+`TestDataProvider`.
5. **Generate ONE example feature end-to-end** so the skeleton compiles and demonstrates the pattern: `auth/Login` (Screen + `<Feature>Tests` + smoke + regression runner) and the **GoToHome** precondition test. Keep it generic (no business-specific screens). This is the worked example users copy via `/qa:plan-tests`/`/qa:cook`.
6. **Seed the sitemap**: write `sitemap/screens/login.json` (+ `home.json`) per `sitemap/SCHEMA.md`, then `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/gen_sitemap.py"`.
7. **build-verify gate** (the `build-verify` skill): `mvn -q -B test-compile` MUST be green before finishing. Fix generation errors until it compiles (`fix-by-layer` if needed).
8. **Conclude**: print the tree summary + the exact next commands: edit `.env` + `configs/<env>.properties`, then `/qa:setup` (plugin config), then `make smoke` (or `/qa:run`), then `/qa:plan-tests <feature>` → `/qa:cook` to add real features.

## Rules
- **Never overwrite the user's code** — the script keeps existing files; only add the skeleton. Refuse on a non-empty project unless `--force`.
- **Follow the platform design-pattern exactly** — the generated framework is the same architecture `/qa:cook` expects, so later features drop in cleanly. Web: enforce the §7 one-browser-per-run lifecycle (launch via idempotent factory, close ONLY in `@AfterSuite`).
- **Must compile** — finish only after `build-verify` is green; ship a runnable skeleton, not stubs that don't build.
- **Generic example only** — `auth/login` + `GoToHome`; no business screens. Keep names/URLs from the user's inputs (placeholders OK).
- **LANGUAGE**: code/identifiers/paths stay English; the closing summary + any prose follow the configured output language (`../../rules/output-language.md`).
- After scaffolding, real features are added by `/qa:plan-tests` → `/qa:cook` (per feature). This skill only lays the foundation once.
