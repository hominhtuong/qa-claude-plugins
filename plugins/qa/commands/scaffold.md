---
description: Scaffold a brand-new standard QA automation project from scratch (Playwright-Web or Appium-App, Page Object Model). Lays the canonical folder structure + static boilerplate (pom/Makefile/suites/configs/.env/.gitignore/sitemap), generates the framework + ONE example feature (auth/login + GoToHome), and verifies it compiles — so users only call /qa:plan-tests to add features. Default app; --web / --app / --both. Never overwrites existing code.
argument-hint: [--app | --web | --both] [package e.g. com.acme.app] [name] [base url]
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# /qa:scaffold — Create a standard automation project

You set up a **ready, compiling** Page Object Model project so the team (even non-technical) can immediately run it and then just `/qa:plan-tests` to add features. Request: **$ARGUMENTS**. Core logic = the **`scaffold-method`** skill.

> **Never overwrite the user's code.** If `pom.xml`/`src/` already exist, STOP and tell them to extend with `/qa:plan-tests`/`/qa:cook` (or pass `--force` to add the skeleton alongside).
> **Must end green:** finish only after `mvn -q -B test-compile` passes (the `build-verify` skill).
> **NEVER print a token/secret.**

## Must read first
- @${CLAUDE_PLUGIN_ROOT}/skills/scaffold-method/SKILL.md (steps, generated files, build-verify gate)

## Step 0 — resolve platform & inputs
1. **Platform**: `--web` (Playwright Java) or `--app` (Appium Java); `--both` scaffolds two separate trees. No flag → **ask** "web hay app?" (default/recommended: **app**).
2. **Package**: base Java package, e.g. `com.<org>.app`. Ask if not given. Derive `group`/`artifact`/`name` from it + the repo folder name (the script does this).
3. **URLs**: web → app base URL (+ identity/login origin + home path); app → app package/activity (Android) or bundle id (iOS). Placeholders are fine — the user fills `.env`/configs later. Ask briefly only for what's needed; don't block on optional values.

## Orchestration
1. **Lay the skeleton** (deterministic) — run cross-platform (`python3` macOS/Linux · `python` Windows):
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scaffold.py" --platform <web|app> --package <pkg> --name "<Name>" --base-url "<url>" [--id-url ... --home-path ...]
   ```
   It creates the canonical tree + token-substituted boilerplate and prints what it wrote (it never deletes files; refuses a non-empty project without `--force`).
2. **Read** `${CLAUDE_PLUGIN_ROOT}/rules/<platform>/design-pattern.md` (+ coding-rules, design-system) and **generate the framework Java classes + the example `auth/login` + `GoToHome`** per the skill — web MUST follow §7 (one browser per run: idempotent `getOrStartPage`, close ONLY in `@AfterSuite`).
3. **Seed the sitemap** (`sitemap/screens/login.json`, `home.json`) → `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/gen_sitemap.py"`.
4. **build-verify** — `mvn -q -B test-compile` until green (`fix-by-layer` if needed).
5. **Conclude** with the next steps: edit `.env` + `configs/<env>.properties` → `/qa:setup` (plugin config) → `make smoke` (or `/qa:run`) → `/qa:plan-tests <feature>` → `/qa:cook`.

## Rules
- Never overwrite code; refuse non-empty projects unless `--force`.
- Generated framework follows the platform design-pattern exactly (so `/qa:cook` features drop in cleanly). Web: enforce the one-browser-per-run lifecycle.
- Finish only when it compiles. Generic example only (auth/login + GoToHome), no business screens.
- Different from `/qa:setup` (which configures the *plugin* in a project): `/qa:scaffold` creates the *test framework* itself. Typical order: `/qa:scaffold` once → `/qa:setup` → `/qa:plan-tests`.
