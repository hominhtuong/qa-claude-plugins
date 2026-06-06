# QA Claude Plugins

🌐 [Tiếng Việt](README.md) · **English**

> **An open-source Claude Code plugin for QA/QC engineers, QA Managers and Product Ops using AI.** Automate web & mobile testing, generate test cases from documents, run exploratory testing, review code — and roll it all up into quality dashboards, Go/No-Go release gates, traceability matrices and release notes. Turns Claude Code into a real "QA engineer" *and* a "quality manager" right inside your terminal/IDE.

Free & open to **everyone**. Install once, use across every project that has Claude. All commands are called as **`/qa:<name>`** (e.g. `/qa:exploratory`).

## Table of contents

- [Features](#features)
- [Installation](#installation)
- [Quickstart workflow](#quickstart-workflow--from-zero-to-your-first-project)
- [Updating](#updating)
- [Command list](#command-list)
  - [Shared](#shared)
  - [Automation](#automation)
  - [Manual QA](#manual-qa)
  - [Quality management & reporting](#quality-management--reporting-qa-manager--product-ops)
- [How it works](#how-it-works)
- [Optional integrations](#optional-integrations)
- [Contributing](#contributing)

## Features

- **Multi-platform automation** — Web (Playwright) + App (Appium iOS/Android): explore & hunt bugs, write Page Objects + tests, run & triage failures, fix the right layer, review → push → open a PR/MR.
- **Manual QA** — analyze specs/PRDs, plan test cases, generate test cases to **xlsx / Google / Lark Sheet**, log bugs to **Lark Bitable**.
- **Quality management & reporting** (QA Manager / Product Ops) — roll up the bug board + test results into a **metrics dashboard**, an auditable **Go/No-Go release gate**, a **requirement traceability matrix**, and **release notes** (internal changelog + user-facing). Read-only.
- **Auto-routing by platform** (web / android / ios) → reads only the matching platform skill → no wasted tokens.
- **Optional integrations** — result notifications (Lark / Slack / Teams / Telegram) & report sharing (Cloudflare R2 / S3), using **your own** accounts, toggle freely.
- **Cross-platform** — Windows + macOS.

## Installation

```bash
/plugin marketplace add hominhtuong/qa-claude-plugins
/plugin install qa@qa-claude
/reload-plugins
/qa:setup        # ← run once right after install: scaffolds .claude/qa-claude/ + checks the toolchain
```

> **After installing (or reloading) the plugin, run `/qa:setup` once per project.** It creates `.claude/qa-claude/` (config + `.plugin.env`), patches `.gitignore`, and checks the toolchain — no terminal needed. Then open `.claude/qa-claude/.plugin.env` to enable what you want. Details in [Optional integrations](#optional-integrations).

Or declare it in the project (so anyone who clones it is prompted to install) — `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "qa-claude": { "source": { "source": "github", "repo": "hominhtuong/qa-claude-plugins" } }
  },
  "enabledPlugins": { "qa@qa-claude": true }
}
```

> You can still add your own commands in the project's `.claude/commands/` (invoked **without a prefix**, e.g. `/mycmd`) — they run independently alongside the plugin's `/qa:…` commands.

## Quickstart workflow — from zero to your first project

New here? This is the whole path, in order. You type commands in Claude Code — **no terminal, no framework knowledge needed.**

1. **Open the project in VS Code** and install Claude Code, then install this plugin (the two `/plugin …` lines above) and run `/reload-plugins`.
2. **Create the test project skeleton** — `/qa:scaffold`. Pick **app** or **web**; it generates a standard Page Object Model framework (folders, `pom.xml`, `Makefile`, suites, an example *login* test) that already compiles. *You now have a real project — the structure shows you where things go.*
3. **Set up the plugin** — `/qa:setup` (creates `.claude/qa-claude/`, checks the toolchain).
4. **Fill your account** — open `.env` and put in the test login (and the app/web URL if asked).
5. **Try the example** — `/qa:run` (or `make smoke`): one browser/app session opens, runs the login case start-to-finish, then closes and produces an HTML report under `results/`.
6. **Add your own feature** — `/qa:plan-tests <feature>` → `/qa:cook` → `/qa:run`. Repeat per feature. (Prefer manual test cases instead of code? `/qa:analyze-spec` → `/qa:plan-gen-testcases` → `/qa:gen-testcases`.)
7. **Hunt bugs / log them** — `/qa:exploratory <feature>` finds bugs; `/qa:log-bug` records them to your board.

> That's it: **scaffold → setup → fill `.env` → run → plan-tests/cook.** A few cases later you have a working test project. For team leads, see [Quality management & reporting](#quality-management--reporting-qa-manager--product-ops).

## Updating

When a new version is out:

```text
/plugin marketplace update qa-claude
/reload-plugins
```

Run `/qa:setup --update` to refresh the `.example`/template files in `.claude/qa-claude/` (your `.env` and `log-bug.config.yml` are **never overwritten**).

## MCP servers (auto-registered when the plugin is enabled)

The plugin **bundles** the MCP servers automation needs — enabling the plugin is enough, **no manual `.mcp.json`**:

| Server | Used for | Config |
|---|---|---|
| **figma** | read design (exploratory, design-conformance) | built-in (http) — just sign in to Figma when prompted |
| **playwright** | web driver | built-in (`npx @playwright/mcp`) |
| **appium** | iOS/Android driver (port 4723) | built-in (`npx appium-mcp`) — still run the Appium server via `start-appium.sh` |
| **Lark** | read docs/Bitable | ❌ **not** via MCP — uses Python `lark_read.py` reading `.plugin.env` (dual tenant/user mode, avoids token errors). To use the MCP, add `@larksuiteoapi/lark-mcp` to your project `.mcp.json` (see [lark-mcp-guide](plugins/qa/rules/lark-mcp-guide.md)). |

> If your project **already** configures its own figma/appium/playwright MCP, yours takes precedence; the plugin locates the right tools via ToolSearch, no conflict.

## Command list

> **How to call**: every plugin command is invoked as **`/qa:<name>`** (e.g. `/qa:exploratory`). This is Claude Code's mandatory namespace for plugins — it can't be dropped. The `*-method` / `*-app` / `*-web`… entries in the menu are **internal skills**; you **don't call them directly** — just call the commands.

### Shared

| Command | What it does |
|---|---|
| `/qa:scaffold [--app\|--web]` | **Create a standard automation project** from scratch (POM framework: folders + pom/Makefile/suites/configs + an example login test that compiles). Run once on an empty repo; then just `/qa:plan-tests`. Never overwrites existing code. |
| `/qa:setup` | **Set up the plugin in a project** (once): Claude runs the script to create `.claude/qa-claude/` + check the toolchain. No terminal needed. |
| `/qa:help [topic]` | Introduce & guide usage of the plugin, list commands/skills. |
| `/qa:status` | Quick overview of the project state (git, devices, Appium, coverage). |
| `/qa:ask <question>` | Q&A about the codebase / architecture / config / testing approach (answer only). |
| `/qa:missing-test-ids` | Manage "test-id debt" to send to dev (export / record / resolve). |
| `/qa:feedback <feedback/bug>` | Send feedback / report a problem → opens a pre-filled GitHub issue (with version/OS); just click Submit. |

> **Automation and Manual use distinct names**, no ambiguity: `cook` (write code) ↔ `gen-testcases` (generate test cases) · `plan-tests` ↔ `plan-gen-testcases` · `analyze` ↔ `analyze-spec` · `count-cases` ↔ `count-testcases`.

### Automation

| Command | What it does |
|---|---|
| `/qa:sitemap [feature] [platform]` | **Crawl & build the sitemap**: walk the whole app/web (or just one feature, e.g. `/qa:sitemap home`), declare **each screen's elements** (name + stable locator) and update the navigation map under `sitemap/`. **Mapping only — NO tests, NO bug hunting, NO Page Object code.** Re-running *extends* nodes (merge by element name), never duplicates. |
| `/qa:exploratory <feature> [platform] [--spec <file\|url\|figma>]` | Explore the **whole** screen like a senior QA, **hunt bugs to the end** — finding a bug does **not** stop the run; log + triage it and keep going through the entire feature; compare against **spec/Figma** when provided → *spec-mismatch* bugs; capture evidence. **Only then conclude (GATE):** any `[APP-BUG]` → emit a **bug report** for dev (🚦 don't write tests for the broken part); **clean** → declare elements/Screen → ready for `/qa:plan-tests`. |
| `/qa:plan-tests <feature>` | Design an automation test plan (only when exploratory is clean). |
| `/qa:find-elements <screen>` | Extract durable locators (auto-routes web/android/ios). |
| `/qa:cook <plan\|request>` | Write Page Object + test code following the design pattern. |
| `/qa:run [platform]` | Compile + run tests + **triage failures** (`[APP-BUG]` vs `[FRAMEWORK]`/`[ENV]`/`[DATA]`). |
| `/qa:fix <bug>` | Fix a bug (compile/test fail, flaky, rule violation) at the **correct layer**. |
| `/qa:analyze <code\|result>` | Analyze the codebase / test results / structure (read-only, no edits). |
| `/qa:count-cases <feature>` | Count existing automation testcases (`@Test`) + estimate the total per sub-feature. |
| `/qa:review-change` | Review the current git diff against the design system & coding rules. |
| `/qa:review-codebase` | Review the **whole** codebase against the rules + cross-file consistency. |
| `/qa:push-code` | Review → auto-fix Blockers → green build → commit & push the branch. |
| `/qa:merge-request` | Review → safely merge the target → push → open a PR/MR (auto-detects GitHub `gh` / GitLab `glab`). |
| `/qa:kill-appium` | Kill all running Appium servers. |

### Manual QA

| Command | What it does |
|---|---|
| `/qa:analyze-spec <spec>` | Analyze a doc/PRD from a QA perspective (testable, ambiguity, risk, questions for the PO) → md file. |
| `/qa:plan-gen-testcases <feature>` | Build a multi-phase test-case plan (scope, screens, TC_ID range). |
| `/qa:gen-testcases <plan>` | Generate test cases to **xlsx / Google / Lark Sheet** (localized output supported). |
| `/qa:count-testcases <file\|sheet>` | Count test cases in a sheet/plan + report coverage per section. |
| `/qa:est-sp <plan\|feature>` | Estimate **Story Points** for QC effort (TCs + execute + retest), factored by role (`USER_ROLE`); outputs the SP table, updates the plan in plan mode. |
| `/qa:explain-bug <Bug ID\|text\|link>` | "Translate" a messy bug into a clear summary (repro/actual/expected + Severity/Priority sanity check); reads the record + comments by Bug ID or full Lark link. |
| `/qa:check-duplicate-bug <description>` | Check the board for a duplicate **before** logging (keyword search, drops closed + false positives) — decision only, never creates. |
| `/qa:log-bug <description>` | Log a bug to Lark Bitable (with image/video, scores Priority). |
| `/qa:update-board <url\|alias>` | Add/switch the active Lark board + refresh mappings. |
| `/qa:auth-lark` | Authenticate your Lark app + probe which scopes/read-mode it has (run once before the Lark doc/board commands). |

### Quality management & reporting (QA Manager / Product Ops)

> **Read-only** — these commands aggregate artifacts QA already produced (`results/` + the Lark bug board) into decision-grade documents for leads, managers and product ops. They never create/edit bugs or tests.

| Command | What it does |
|---|---|
| `/qa:quality-report [from..to\|tag]` | **QA dashboard** for managers: pass rate + trend, open bugs by priority with aging, defect density / hot-spot modules, created-vs-resolved trend, coverage per feature → `results/quality-report/` (md, optional HTML/notify). |
| `/qa:bug-analysis <board url> [range]` | **Deep board analysis** of any board over a range: adaptively classifies that board's own status names into not-ready-to-test / ready / closed, then breaks down the not-ready backlog by group/type/feature/priority + **root causes** + **spike days** + aging → `results/bug-analysis/`. |
| `/qa:release-gate <release>` | **Go / No-Go** verdict against an auditable checklist (`release-gate.config.yml`): hard gates → NO-GO, soft gates → CONDITIONAL (ship with sign-off). Writes verdict + per-gate table + blockers + sign-off block. |
| `/qa:traceability <feature\|all>` | **Requirement Traceability Matrix**: link each requirement (from `/qa:analyze-spec`) → test cases → bugs, flag Gap / No-test / Partial / Covered. Closes the spec↔test↔bug loop. |
| `/qa:release-notes <release>` | **Release notes for two audiences**: an internal technical changelog (Conventional-Commit grouped + fixed-bug table) + a user-facing notes doc (plain language, benefit-led) from git history + fixed bugs. |
| `/qa:risk <feature\|release>` | **Risk assessment**: a Risk Matrix (Likelihood × Impact, 1–25) classified Low/Medium/High/Critical, with prevention/detection/response/owner mitigation per Medium+ risk and a risk-based test strategy. |
| `/qa:triage <bug list>` | **Bug triage**: classify Severity + Type, score by **RICE** for an objective processing order, derive SLA deadlines + regression scope, emit an action plan. Reads a sheet/file/list or the board. |
| `/qa:sla <ticket data>` | **SLA compliance** report: compliance rate (overall + per priority), MTTR-Response/Resolution with P50/P90/P95, breach analysis, trend, assignee performance. |
| `/qa:postmortem <incident>` | **Blameless postmortem**: timeline + root-cause (5 Whys + technical/process factors) + impact + action items (Prevent/Detect/Mitigate, owner role, due). Grounds the timeline in related board records. |

> Shared frameworks for these: [product-ops.md](plugins/qa/rules/product-ops.md) (SLA / health / release gates / RICE / risk matrix), [severity-priority-framework.md](plugins/qa/rules/severity-priority-framework.md), [story-point.md](plugins/qa/rules/story-point.md).

### Output

All output is gathered under the **`results/`** folder in the project:

| Type | Location |
|---|---|
| Exploratory (spec analysis + figma-tracking + bug report + screenshots) | `results/<feature-name>/` (shared register: `results/bug-summary.md`) |
| Each test run (HTML report + screenshots/videos) | `results/tests/<ddMMMyyyy>/…` |
| Test cases (xlsx) + analysis + html testcase report | `results/<feature-name>/` |
| Quality & ops reports (dashboard / release gate / traceability / release notes / risk / triage / SLA / bug analysis) | `results/quality-report/`, `results/release-gate/<release>/`, `results/release-notes/<release>/`, `results/bug-analysis/`, `results/<context>/` (risk/triage/sla/traceability) |

`results/tests/` (per-run artifacts) is automatically added to `.gitignore` when you run `setup`.

## How it works

Each automation command has **Step 0: lock the platform** (from the argument `web|android|ios`, else auto-detect the project, else ask), then **reads only 1 skill** for that platform → saves tokens, never runs the wrong runtime:

| Task | web | android | ios |
|---|---|---|---|
| Navigation | `navigate-web` | `navigate-app` | `navigate-app` |
| Extract locators | `find-elements-web` | `find-elements-android` | `find-elements-ios` |
| Write code | `cook-web` | `cook-app` | `cook-app` |
| Run suite | `run-web` | `run-app` | `run-app` |

## Optional integrations

> **No configuration needed by default** — reports are always written in the project (locally). Notifications (Lark/Slack/…) and report upload (R2/S3) are optional, toggled independently.

Everyone uses **their own** account. All plugin config lives in `<project>/.claude/qa-claude/` (kept separate, **never touches the app's own `./.env`**):

| File | Role | On re-running `setup` |
|---|---|---|
| `.env` | 🔒 secrets (one sectioned file: Lark/R2/S3/notify) | kept (yours) |
| `log-bug.config.yml` | 🧩 Lark board + dev/field mappings | kept (yours) |
| `.env.example` · `log-bug.config.example.yml` | latest schema reference | refreshed |
| `testcase-template.md` | 📄 test-case format | refreshed |

**Set up once / project** — just type:

```text
/qa:setup
```

Claude runs the script (auto-detects macOS/Windows), creates `.claude/qa-claude/`, patches `.gitignore`, and checks the toolchain (auto-installs `wrangler` if `npm` is present; otherwise prints the OS-specific install command). You **don't need a terminal**. Then open `.claude/qa-claude/.env` to enable what you want (and `log-bug.config.yml` for `/qa:log-bug`).

### Choose a channel (at most 1 per group)

| Need | Default | Channel A | Channel B |
|---|---|---|---|
| **View report** | ✅ local HTML | - | - |
| **Notification** | summarized in the Claude session | **Lark** (`ENABLE_LARK_NOTIFY` + `LARK_*`) | **Webhook** Slack/Teams/Telegram/Discord (`ENABLE_NOTIFY_WEBHOOK` + `NOTIFY_*`) |
| **Share report URL** | open the local file | **Cloudflare R2** (`ENABLE_CF_PUSH` + `CF_*`, needs `wrangler`) | **S3** AWS/MinIO/… (`ENABLE_S3_PUSH` + `S3_*`/`AWS_*`, needs `aws` CLI) |

Lark: group → Settings → Bots → **Custom Bot** → copy the webhook. R2: Cloudflare → API Tokens → **R2 Token (Edit)**. S3: leave `S3_ENDPOINT` empty for AWS, set the endpoint for MinIO/others. Enable a channel and fill in that key group.

### Log bug to Lark

`/qa:log-bug` reads `.claude/qa-claude/log-bug.config.yml` (board id, Dev PIC → user id mapping, options, defaults). Fill in your board there (or use `/qa:update-board <url>`). It scores **Priority** only (AI auto-estimates if you leave it blank); a production board sets `read_only: true` to block accidental logging.

## Contributing

Open source — contributions welcome. For plugin-extension conventions (structure, skill/command naming, technical invariants) see [CONTRIBUTING.md](CONTRIBUTING.md).

**Feedback / bug reports**: do it right while using the plugin — type **`/qa:feedback <description>`**, and the plugin opens a pre-filled GitHub issue (version + OS already filled) for you to click Submit.
