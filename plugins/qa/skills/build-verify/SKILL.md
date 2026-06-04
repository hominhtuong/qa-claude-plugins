---
name: build-verify
description: Reusable logic acting as a "green gate" — clean compile/build (auto-detects the project's build system) and (optionally) a quick run of the just-touched feature's tests. Use before finishing cook/fix/exploratory and before committing in push-code/merge-request. Do not raise timeouts / add workarounds just to "pass the test".
---

# Skill: build-verify

Reusable capability: ensure the code is in a clean build state before moving on. Thin but a **blocking gate** (no patching to pass). Domain-agnostic — auto-detects the build system, not hard-wired to Maven.

## Procedure
1. **Detect the build system** (from the files present in the repo) then run the compile/build command, which must be **green**:
   - `pom.xml` (Maven — Appium Java / Playwright Java) → `mvn clean compile test-compile`.
   - `build.gradle` → `./gradlew compileTestJava` (or `assemble`).
   - `package.json` (Playwright/WDIO TS-JS) → `npm run build` if present, or `npx tsc --noEmit` / `npm run lint`.
   - `pubspec.yaml` (Flutter) → `flutter analyze`.
   Red → fix via skill `fix-by-layer` until green; still red → **STOP**, report the error, do **not** move on (no commit / no push).
2. **Optionally** do a quick run of the feature you just worked on (auto-check the device): script `./scripts/run-*.sh`, `mvn test -DsuiteXmlFile=testng/<suite>.xml`, `make smoke`, or `npx playwright test <spec>`. (App: the TestNG XML with `GoToHomeTest` is the first `<test>`.)
3. Do **not** bump timeouts arbitrarily, no `Thread.sleep`/`waitForTimeout`, do not loosen conditions just to "pass the test" — that hides bugs and violates coding-rules.

> Timeout/capabilities/credentials are taken centrally from config (`configurations/`, `configs/*.properties`, `.env`), not scattered as magic numbers / secrets in code.
