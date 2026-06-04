---
name: detect-platform
description: Reusable logic (routing brain) to lock in EXACTLY ONE platform web/android/ios for a command in this cross-platform automation project, then point to the skills/rules to read for that platform — so the command does NOT read superfluous skills for other platforms (saving tokens). Every auto command calls this skill at Step 0 before reading any heavy skill. The decision standard lives in the platform-detect.md rule.
---

# Skill: detect-platform

Reusable capability: return **one** platform token (`web` | `android` | `ios`, or the group `app`=android/ios when only code-writing is needed) + the list of skills/rules to load. This is the routing step: it runs EXTREMELY CHEAP (Glob, no reading large files) so the command loads only the correct platform skills. Full standard: [platform-detect.md](../../rules/platform-detect.md).

## Procedure
1. **Explicit argument** first: does `$ARGUMENTS` contain `web`/`android`/`ios` (or `--platform=`)? → lock it in immediately, go to step 4.
2. **Path context** (if the arg points to a file/screen): Playwright (`getByRole`, `import com.microsoft.playwright`) → `web`; `@MobileFindBy`/`AppiumDriver` → `app`.
3. **Auto-detect the project** with Glob (per the signal table in [platform-detect.md](../../rules/platform-detect.md)): `playwright.config.*`/`Makefile`/`base.url` → web · `android-capabilities.properties`/`testng-android.xml` → android · `ios-capabilities.properties`/`testng-ios.xml` → ios.
4. **Disambiguate**: if >1 candidate remains and the command needs exactly 1 platform → use the command's **default** (state clearly "using `<x>` (default), pass another platform to change") or **ASK the user**. Do NOT guess, do NOT run all three.
5. **Return** to the command: the locked-in `platform` + the skill map (see table below). The command **reads only the skill on the matching row**.

| platform | navigate | find-elements | cook | run | rules |
|---|---|---|---|---|---|
| web | `navigate-web` | `find-elements-web` | `cook-web` | `run-web` | `rules/web/*` |
| android | `navigate-app` | `find-elements-android` | `cook-app` | `run-app` | `rules/app/*` |
| ios | `navigate-app` | `find-elements-ios` | `cook-app` | `run-app` | `rules/app/*` |

> This skill ONLY routes — it does not open a device or extract elements. After getting `platform`, the command loads the correct platform skills + the agnostic skills (`exploratory-method`, `plan-method`, `fix-by-layer`, `review-audit`, `update-sitemap`). Multiple platforms at once (e.g. reviewing the whole repo) → iterate over each detected platform.
