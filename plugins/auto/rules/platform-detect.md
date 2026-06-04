# Platform detection (web / android / ios)

A static rule shared by every command of the `auto` plugin. This is a multi-platform automation project (Web Playwright + App Appium iOS/Android) → each command must **lock onto exactly one platform** then only read that platform's skills. Goal: **don't read extra skills** (save tokens), don't run the wrong runtime.

## Decision order (stop at the first step that yields a result)

1. **Explicit argument** — `$ARGUMENTS` contains a token `web` | `android` | `ios` (or `--platform=<x>`, `app` = ask android/ios). → use it directly.
2. **Path context** — the arg points to a specific file/screen:
   - path contains Playwright Java (`getByRole`, `import com.microsoft.playwright`) → **web**.
   - path contains `@MobileFindBy` / `AppiumDriver` → **app** (android/ios) → proceed to step 4 to pick the OS.
3. **Auto-detect project type** (Glob, cheap — don't read large file contents):

   | Signal | Platform |
   |---|---|
   | `playwright.config.*`, `pom.xml` with `playwright`, `Makefile` with a `smoke`/`regression` target, `configs/*.properties` with `base.url`, `src/**/screens/**` using `Locator` | **web** |
   | `configurations/android-capabilities.properties`, `appPackage`/`appActivity`, `testng/testng-android.xml`, `scripts/run-android.sh`, `@MobileFindBy(uiautomator=...)` | **android** |
   | `configurations/ios-capabilities.properties`, `bundleId`/`udid`/`xcodeSigningId`, `testng/testng-ios.xml`, `scripts/run-ios.sh` | **ios** |
   | `pubspec.yaml` + `integration_test/` (Flutter target via Appium) | **app** (android/ios per capabilities) |

4. **Still multiple candidates** (e.g. repo has both android + ios, or both web + app) and the command **requires one platform** (find-elements / exploratory / run / cook):
   - There is a safe **default** for that command (e.g. `/run` defaults to android) → use the default, **print clearly** "running `<platform>` (default) — pass `web|ios` to change".
   - No clear default → **ASK the user** to choose a platform. Do NOT guess blindly, do NOT run all three.

## The `app` group

`cook` / `declare-screen` / `fix` write a **shared Appium Java codebase** for both Android & iOS (the `@MobileFindBy`/`@MobileFindBys` annotations handle locator differences). → these commands treat android+ios as **`app`** at the code-writing level, but **locator selection** still splits: `find-elements-android` vs `find-elements-ios`. Web is always separate (Playwright Java, a different codebase).

## Skill map by platform (a command reads EXACTLY one column)

| Task | web | android | ios |
|---|---|---|---|
| Open screen / navigate | `navigate-web` | `navigate-app` | `navigate-app` |
| Extract locators | `find-elements-web` | `find-elements-android` | `find-elements-ios` |
| Write test code | `cook-web` | `cook-app` | `cook-app` |
| Run suite | `run-web` | `run-app` | `run-app` |
| Design/coding rules | `rules/web/*` | `rules/app/*` | `rules/app/*` |

**Platform-independent** skills (read regardless of platform): `exploratory-method`, `plan-method`, `fix-by-layer`, `review-audit`, `design-conformance`, `update-sitemap`, and the shared rules `failure-triage.md` / `exploratory-bug-report-template.md` / `lark-mcp-guide.md`.
</content>
