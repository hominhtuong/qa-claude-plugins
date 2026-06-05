---
name: navigate-web
description: Reusable logic to use Playwright MCP to open the browser, log in via Keycloak SSO (#username/#password/#kc-login), ensure it is at Home (GoToHome.ensure equivalent), then navigate to a feature screen per the sitemap. Used by the exploratory command (open a screen to explore/capture elements) and fix (reopen the real UI when a selector changes to get the correct locator). Credentials come from .env/configs, do NOT print the password.
---

# Skill: navigate-web

Reusable capability: from a blank state → standing on the correct feature screen on the real app (Playwright MCP), ready for `find-elements-web`. This is exactly the `GoToHome.ensure(page)` flow done manually via MCP.

> The Playwright MCP is **bundled** by the plugin, so its tools are `mcp__plugin_qa_playwright__*` (the `browser_*` names below are shorthand). If your project configures its own Playwright MCP, the prefix may differ — locate the `browser_*` tools via ToolSearch and call the resolved names.

> **Headed vs headless**: the bundled server launches a **visible** browser by default (easier to watch + screenshot). To run without a window (CI/background), set `QA_HEADLESS=true` in the main project's `./.env` (or `.claude/qa-claude/.plugin.env`) — it is resolved at server startup by `scripts/mcp_playwright.py`. This is a launch-time setting: it cannot be toggled mid-session, so set it before the first `browser_navigate`.

## Procedure
1. **Get config & account**: `base.url`/`login.url`/`home.path` from `configs/<env>.properties`; `LOGIN_USERNAME`/`LOGIN_PASSWORD` from `.env`. **Do NOT print the password** to the log/report.
2. **Open the app**: `mcp__plugin_qa_playwright__browser_navigate` to `base.url` (or `base.url + home.path`). No session → the app redirects to the Keycloak realm (`login.url`).
3. **Identify the state** with `mcp__plugin_qa_playwright__browser_snapshot`:
   - **HOME** (already at the app origin, no longer at the realm) → done, go to step 6.
   - **LOGIN** (Keycloak Sign in form, has `#kc-login`) → step 4.
   - **UNKNOWN** (mid redirect/loading) → `browser_wait_for` then snapshot again.
4. **Log in to Keycloak** (stable ids, NOT by text — the realm is localized EN/VI):
   - `browser_type` into `#username` = username, into `#password` = password (mask, do not log the value).
   - `browser_click` `#kc-login` → realm redirects to `/auth/callback` → app. Landing in a new state (OTP/consent/password change) → snapshot + handle as an extended `GoToHome`, and record it to add to `AppStateDetector`.
5. **Confirm you are at Home**: snapshot again, verify the URL is back at the app origin + a key app-shell element is visible. Onboarding tour/modal blocking → close it (dialog Close) like `dismissOnboardingTourIfPresent`.
6. **Check the sitemap first** (don't grope around): read `sitemap/screens/<id>.json` for the route + navigation path from Home to the feature screen + key element.
7. **Go to the feature screen**: from Home follow the sitemap path (`browser_click` tile/tab/menu — anchored by role/testid). `browser_snapshot` to confirm the right screen (key element visible).
8. Done → let the command close it in its final step (`mcp__plugin_qa_playwright__browser_close`).

> Reference flow: `flows/GoToHome.java` + `screens/auth/LoginScreen.java`. Discovered elements are saved via the `find-elements-web` skill. To skip the login UI (when testing a feature) → bypass via API/storageState instead of driving the Keycloak form every time. For screenshots, always pass the **full relative path** as the tool's `filename` (e.g. `results/<feature-name>/screenshots/<BUG-ID>.png`) so the image lands where the command expects — a bare file name falls back to the MCP output dir / project root.
