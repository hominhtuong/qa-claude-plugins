# Changelog

All notable changes to the `qa` plugin. Versions follow the plugin manifest
(`plugins/qa/.claude-plugin/plugin.json`).

## 0.0.20 — `/qa:scaffold`: a standard project from scratch + non-tech quickstart

- **`/qa:scaffold`** — turn an empty repo into a ready, **compiling** Page Object Model project so
  the next step is just `/qa:plan-tests`. `--app` (Appium Java) / `--web` (Playwright Java) / `--both`
  (default: ask, recommend app). It runs `scripts/scaffold.py` to lay the canonical tree + static,
  token-substituted boilerplate (`pom.xml`, `Makefile`, TestNG suites, `configs/*.properties.example`,
  `.env.example`, `.gitignore`, shared `sitemap/SCHEMA.md`), then **generates the framework classes +
  one example `auth/login` + `GoToHome`** following the platform design-pattern, and gates on
  `build-verify` (`mvn test-compile`). **Never overwrites existing code** (refuses a non-empty repo
  without `--force`). Web scaffolds encode the §7 one-browser-per-run lifecycle out of the box.
- **`scripts/scaffold.py`** + **`templates/scaffold/{web,app}/`** — the deterministic skeleton:
  package/group/name/URL tokens (`__PKG__`, `__GROUP__`, `__BASE_URL__`, …) substituted into every
  file; builds the full `src/main`+`src/test` package tree; copies the shared sitemap schema; seeds
  `sitemap/sitemap.json`.
- **README — "Quickstart workflow: from zero to your first project"** (both languages, added to the
  table of contents): a non-technical, 7-step path — install → `/qa:scaffold` → `/qa:setup` → fill
  `.env` → `/qa:run` the example → `/qa:plan-tests`/`/qa:cook` per feature. `/qa:scaffold` is also
  listed in the Shared command table and the auto-generated project guide (under "Bắt đầu").

## 0.0.19 — Web: one browser per run (no flicker on smoke/regression)

Fixes the reported symptom of the browser opening/closing after every case during a
smoke/regression run. The design already intended "one shared window for the whole run",
but the rules never pinned the **TestNG lifecycle scope**, so cooked `BaseTest` code could
launch/close the browser at *method* scope → flicker. Now made explicit & enforced:

- **design-pattern.md §7 (new, MANDATORY)** — `PlaywrightFactory` is a lazy singleton
  (`getPage()` creates once, reuses; `closeAll()` is the only close). `BaseTest` launches the
  browser **once** in `@BeforeSuite(alwaysRun=true)` and closes it **once** in
  `@AfterSuite(alwaysRun=true)` (flush report → close → upload/notify) — so the window stays
  open from the first case to the last, and the report is sent when the run finishes, not per
  case. `BaseRegressionTest`/`BaseSmokeTest` `@BeforeMethod` does **only** `GoToHome.ensure(page)`.
- **Banned anti-patterns** (the actual flicker causes): launching/closing browser/context/page
  in `@BeforeMethod`/`@AfterMethod`/`@BeforeClass`/`@AfterClass`; `page/context/browser.close()`
  between tests; `new` Playwright/Browser/Context/Page per test/class/Screen; a retry that
  relaunches the browser; splitting the run into many JVMs / parallel workers.
- Reinforced across the web pipeline: **coding-rules.md** (Shared state & lifecycle), **cook-web**
  (generate BaseTest at suite scope), **run-web** (flicker = `[FRAMEWORK]` → `/qa:fix`; prefer
  `make smoke`/`regression`, keep `thread-count=1`), **review-checklist.md** (new §A3 — 🔴 items so
  `/qa:review-*` catches per-method lifecycle), and **plan-method** (call out run-scoped lifecycle
  when the plan creates base/core).

## 0.0.18 — Blameless postmortem + release-gate/data-source correctness

- **`/qa:postmortem`** — produce a **blameless incident postmortem**: an evidence-based timeline,
  root-cause analysis (5 Whys + technical/process contributing factors, trigger vs root cause),
  impact (incl. SLA target vs actual), resolution/recovery, what-went-well/wrong/lucky, and a tracked
  action-item table typed **Prevent / Detect / Mitigate** with a role owner + due. Grounds the timeline
  in optional related board records (by Bug ID / link / board+range, `--with-comments`). Blameless
  (roles, not names) and evidence-based (missing facts → open questions, never invented) →
  `results/postmortem/<incident>.md`.
- **Review fixes to the quality-management group** (correctness pass over the 8 ops commands):
  - **release-gate** no longer auto-NO-GO's a manual-only team: a gate whose source is **unreadable**
    (auth/API error) stays UNKNOWN ⇒ NO-GO (fail-safe), but a gate whose source **genuinely doesn't
    exist** (e.g. `min_pass_rate` with no automation suite) is now **N/A → skipped** (not a blocker)
    with a note to set it `null`; confidence = PASS / (total − N/A).
  - **triage / sla** data-source wording corrected: the reliable path is the Lark Bitable board
    (`lark_bitable.py`, incl. `--url`); a **Google Sheet** is read only if the `google-sheets` MCP is
    configured; a **Lark Sheet** has no reader → export to `.xlsx/.csv` or use the board.

## 0.0.17 — Deep bug-board analysis + run setup right after install

- **`/qa:bug-analysis`** — point at **any** board by URL + a time range ("tháng này" / "quý này" /
  "năm nay" / `from..to`) and get a detailed analysis of the **not-ready-to-test backlog**. Because
  every board names its statuses differently, the command **adaptively classifies the board's own
  status values** into NOT-READY (New/Rework/Reopen/Fixing/DevDone-style) / READY / CLOSED / UNKNOWN
  (prints the mapping for the user to confirm), then breaks the backlog down by group/type/feature/
  priority, clusters **root causes** with real examples, detects **spike days** (abnormal creation
  peaks + likely reason), and reports aging + assignee load → `results/bug-analysis/<board>-<range>.md`.
- **Data layer** — `lark_bitable.py` gained `--url` to read an arbitrary board (parses
  `…/base/<id>?table=…`, and resolves `…/wiki/<token>?table=…` to its base app token), so the
  analysis works on any board without touching the configured one.
- **README** — `/qa:setup` is now shown directly in the Installation steps (run it once right
  after install/reload) in both languages, so first-time users don't miss it.

## 0.0.16 — Product-Ops & manager toolkit: risk, triage, SLA, est-sp, explain/dedup bug

Ports the battle-tested Product-Ops / QA-Lead commands from the QAButler project into the
plugin, restructured to the plugin's design (one command + one `*-method` skill each,
`${CLAUDE_PLUGIN_ROOT}` paths, English skill descriptions, `results/` output, Lark via Python,
output language via `output-language.md`). All read-only — they aggregate/interpret, never mutate.

- **Three shared frameworks (`rules/`)** distilled from QAButler: `product-ops.md` (SLA targets,
  health thresholds, release gates G1–G8, RICE, risk matrix, bug types, report-language guidance),
  `severity-priority-framework.md` (Severity-vs-Priority decision matrix + synonym normalization),
  `story-point.md` (Fibonacci scale + role multiplier).
- **`/qa:risk`** — risk assessment: Risk Matrix (Likelihood × Impact, 1–25) → Low/Medium/High/Critical,
  prevention/detection/response/owner per Medium+ risk, and a risk-based test strategy.
- **`/qa:triage`** — classify Severity + Type, score by **RICE** for an objective order, derive SLA
  deadlines + regression scope, emit an action plan. Reads a sheet/file/list or the board.
- **`/qa:sla`** — SLA compliance: rate (overall + per priority), MTTR-Response/Resolution with
  P50/P90/P95 percentiles, breach analysis, trend, assignee performance.
- **`/qa:est-sp`** — QC-effort Story Points factored by `USER_ROLE` (.plugin.env): junior ×1.5 /
  mid ×1.2 / senior·lead ×1.0; outputs the mandatory SP table, updates the plan in plan mode.
- **`/qa:explain-bug`** — "translate" a messy bug (text / no-diacritics / screenshot / Bug ID /
  full Lark link) into a clear summary plus a Severity/Priority reasonableness check; reads the record,
  its comments and history from the board.
- **`/qa:check-duplicate-bug`** — board duplicate check before logging (keyword search, drops closed
  records + false positives) — decision only; `/qa:log-bug` calls it when `check_duplicate: true`.
- **Data layer** — `lark_bitable.py` gained `--search` / `--bug-id` / `--record-id` / `--with-comments`
  (powers triage/explain-bug/check-duplicate-bug). New `USER_ROLE` key in `.plugin.env.example`.
- **Wiring** — release-gate references product-ops §3 gate defaults; quality-report references the
  §2 health thresholds; log-bug references the severity framework + the dedup skill. The project
  guide groups the new commands under Manual QA / "Quản lý chất lượng & báo cáo".
- **Not ported** (and why): `health` (overlaps quality-report), `qa-kpi`/`report-task` (coupled to
  QAButler sub-projects), `release-check` (= our release-gate), `search-doc` (needs a wiki-search backend).

## 0.0.15 — Quality management & reporting: serve QA Managers and Product Ops

Extends the plugin beyond the QA/QC individual contributor to **QA Managers/Leads and
Product Ops**, with four read-only commands that roll up artifacts QA already produced
(`results/` + the Lark bug board) into decision-grade documents. No new audience config —
they reuse the same `.claude/qa-claude/` config and bug board.

- **New shared data layer — `scripts/lark_bitable.py`.** Reads records from the active
  Lark Bitable board via the same dual-mode (tenant/user) token as `lark_read.py`
  (re-auths every run, avoids `99991668`), maps each record to the plugin's logical field
  names from `log-bug.config.yml`, supports `--status/--sprint/--version/--since/--until`
  filters and `--summary` tallies. Never prints tokens.
- **`/qa:quality-report`** — QA-Manager dashboard: pass rate + trend, open bugs by priority
  with aging, defect density / hot-spot modules, created-vs-resolved trend, coverage per
  feature → `results/quality-report/<date>/` (md, optional HTML/notify). Escape rate only
  when the board schema supports it (never faked).
- **`/qa:release-gate`** — Go/No-Go verdict against an auditable checklist
  (`release-gate.config.yml`): hard gates ⇒ NO-GO, soft gates ⇒ CONDITIONAL. Fail-safe:
  unreadable data behind a hard gate = NO-GO, never an optimistic pass.
- **`/qa:traceability`** — Requirement Traceability Matrix linking requirements
  (`/qa:analyze-spec`) → test cases → bugs, flagging Gap / No-test / Partial / Covered.
- **`/qa:release-notes`** — two audiences: an internal Conventional-Commit changelog +
  fixed-bug table, and a jargon-free user-facing notes doc, from git history + the board.
- **Setup** now scaffolds `release-gate.config.yml` (kept on re-run) + refreshes its
  `.example`. The auto-generated project guide gains a "Quản lý chất lượng & báo cáo" group.

## 0.0.14 — Lark auth/doc-reading: handle every failure with one clear action

Hardens the Lark authentication + document-reading path so a new user reaches a
document without debugging six layers by hand. Every failure now maps to a stable
`error_code` plus a single next action.

- **#1 env parser — inline comments no longer break values.** `_env.py` gained a single
  `parse_env_line`/`strip_inline_comment` (used everywhere): a `# comment` is cut only when
  whitespace precedes it, so a `#` inside a value (secret `ab#cd`, colour `#FF0000`, URL
  fragment) is preserved. The `.plugin.env.example` no longer ships an inline comment on
  `LARK_DOMAIN=` (it was producing `URL can't contain control characters`).
- **#2 read scopes are tested for real, not assumed.** `wiki.read`/`docx.read`/`drive.read`
  now do a harmless GET and report `✅granted`/`❌denied` (only `bitable.write`/`drive.upload`
  stay `📜declared`). A missing `wiki:wiki` scope surfaces at `/qa:auth-lark`, not mid-read.
  New `--probe-doc <url>` / `LARK_PROBE_DOC` tests against the exact document you need.
- **#3 corporate self-signed SSL is actionable.** The TLS context honours `SSL_CERT_FILE`
  and auto-uses `truststore` (OS trust store) when installed; a `CERTIFICATE_VERIFY_FAILED`
  prints a one-step `SSL_CERT_FILE` fix instead of a stacktrace. `SSL_CERT_FILE` is now
  documented in `.plugin.env.example`, and `/qa:doctor` probes HTTPS to Lark.
- **#4 OAuth redirect (error 20029) is self-explaining.** `/qa:auth-lark --login` warns when
  it falls back to the default `:8080/callback`, the 20029 error maps to "set
  `LARK_REDIRECT_URI`", and a successful login persists the redirect that worked.
- **#5 placeholder/disabled credentials caught early.** `cli_xxxx…`/`your_app_secret` or
  `ENABLE_LARK_APP=false` now fail with a precise message instead of Lark's opaque
  `invalid param (code=10003)`.
- **#6 actionable errors everywhere.** Both `lark_auth.py` and `lark_read.py` emit
  `error_code` + `action` for env / SSL / scope / redirect / placeholder / doc-not-shared,
  so the `lark-reader` agent and `/qa:analyze-spec` propose the exact fix.
- Added stdlib unit tests (`plugins/qa/scripts/tests/test_lark.py`): env parsing,
  placeholder detection, read-scope classification, error diagnosis. No secret/token is ever
  printed on any branch.
