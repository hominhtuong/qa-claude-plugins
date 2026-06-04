# QA Claude Plugins

🌐 [Tiếng Việt](README.md) · **English**

> **An open-source Claude Code plugin for every QA/QC engineer using AI.** Automate web & mobile testing, generate test cases from documents, run exploratory testing, review code — turning Claude Code into a real "QA engineer" right inside your terminal/IDE.

Free & open to **everyone**. Install once, use across every project that has Claude. All commands are called as **`/qa:<name>`** (e.g. `/qa:exploratory`).

## Table of contents

- [Features](#features)
- [Installation](#installation)
- [Updating](#updating)
- [Command list](#command-list)
  - [Shared](#shared)
  - [Automation](#automation)
  - [Manual QA](#manual-qa)
- [How it works](#how-it-works)
- [Optional integrations](#optional-integrations)
- [Contributing](#contributing)

## Features

- **Multi-platform automation** — Web (Playwright) + App (Appium iOS/Android): explore & hunt bugs, write Page Objects + tests, run & triage failures, fix the right layer, review → push → open a PR/MR.
- **Manual QA** — analyze specs/PRDs, plan test cases, generate test cases to **xlsx / Google / Lark Sheet**, log bugs to **Lark Bitable**.
- **Auto-routing by platform** (web / android / ios) → reads only the matching platform skill → no wasted tokens.
- **Optional integrations** — result notifications (Lark / Slack / Teams / Telegram) & report sharing (Cloudflare R2 / S3), using **your own** accounts, toggle freely.
- **Cross-platform** — Windows + macOS.

## Installation

```bash
/plugin marketplace add hominhtuong/qa-claude-plugins
/plugin install qa@qa-claude
```

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

## Updating

When a new version is out:

```text
/plugin marketplace update qa-claude
/reload-plugins
```

Run `/qa:setup-plugin --update` to refresh the `.example`/template files in `.claude/qa-claude/` (your `.env` and `log-bug.config.yml` are **never overwritten**).

## Command list

> **How to call**: every plugin command is invoked as **`/qa:<name>`** (e.g. `/qa:exploratory`). This is Claude Code's mandatory namespace for plugins — it can't be dropped. The `*-method` / `*-app` / `*-web`… entries in the menu are **internal skills**; you **don't call them directly** — just call the commands.

### Shared

| Command | What it does |
|---|---|
| `/qa:setup-plugin` | **Set up the plugin in a project** (once): Claude runs the script to create `.claude/qa-claude/` + check the toolchain. No terminal needed. |
| `/qa:help [topic]` | Introduce & guide usage of the plugin, list commands/skills. |
| `/qa:status` | Quick overview of the project state (git, devices, Appium, coverage). |
| `/qa:ask <question>` | Q&A about the codebase / architecture / config / testing approach (answer only). |
| `/qa:missing-test-ids` | Manage "test-id debt" to send to dev (export / record / resolve). |
| `/qa:feedback <feedback/bug>` | Send feedback / report a problem → opens a pre-filled GitHub issue (with version/OS); just click Submit. |

> **Automation and Manual use distinct names**, no ambiguity: `cook` (write code) ↔ `gen-testcases` (generate test cases) · `plan-tests` ↔ `plan-gen-testcases` · `analyze` ↔ `analyze-spec` · `count-cases` ↔ `count-testcases`.

### Automation

| Command | What it does |
|---|---|
| `/qa:exploratory <feature> [platform]` | Explore a screen like a senior QA, **hunt bugs**, capture evidence, output a dev bug report. 🚦 Any `[APP-BUG]` → stop, don't write tests for a broken app. |
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
| `/qa:log-bug <description>` | Log a bug to Lark Bitable (with image/video, scores Priority). |
| `/qa:update-board <url\|alias>` | Add/switch the active Lark board + refresh mappings. |

### Output

All output is gathered under the **`results/`** folder in the project:

| Type | Location |
|---|---|
| Exploratory (spec analysis + figma-tracking + bug report + screenshots) | `results/<feature-name>/` (shared register: `results/bug-summary.md`) |
| Each test run (HTML report + screenshots/videos) | `results/tests/<ddMMMyyyy>/…` |
| Test cases (xlsx) + analysis + html testcase report | `results/<feature-name>/` |

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
/qa:setup-plugin
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
