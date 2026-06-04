# Contributing

Thanks for helping improve **qa-claude-plugins**. This repo is a single Claude Code plugin (`qa`) published through the `qa-claude` marketplace. Keep these conventions so the plugin stays prefix-free, token-efficient, and consistent.

## Repo layout

```
qa-claude-plugins/
├── .claude-plugin/marketplace.json     # catalog (one plugin: qa)
└── plugins/qa/
    ├── .claude-plugin/plugin.json
    ├── commands/   one .md per slash command
    ├── skills/     <name>/SKILL.md       (reusable capabilities, called by name)
    ├── rules/      static reference docs read by commands/skills
    ├── agents/     sub-agent definitions
    ├── scripts/    python3 helpers (cross-platform, stdlib-first)
    └── templates/  .env.example  +  qa-claude/ (installed into a project's .claude/qa-claude/)
```

## Invariants

1. **One plugin, prefix-free commands.** Every command is invoked bare (`/cook`, `/run`). Do not create commands that collide in name with different behaviour — give each a distinct, self-explanatory name (e.g. `cook` for automation vs `gen-testcases` for manual test cases).
2. **`${CLAUDE_PLUGIN_ROOT}` is per-plugin.** A file that a command/skill *reads* must live in this plugin; call other skills **by name** (e.g. `commit-push`, `gen-testcases`). Never reference `.claude/rules|skills|agents/` from inside a plugin file.
3. **Automation commands route by platform.** They run `detect-platform` (web/android/ios) first, then read only the matching skill/rules (`rules/web/*` vs `rules/app/*`). Adding a platform = add a `*-<platform>` skill + one router line, not a giant shared skill.
4. **Project-side config goes in `.claude/qa-claude/`** (installed by `setup`): secrets in `.env`, user data in `log-bug.config.yml` (both never overwritten); `.example` references + `testcase-template.md` are refreshed on update. Never put secrets in the plugin; keep the plugin's `.env` separate from the project's own `./.env`.
5. **Frontmatter.** Commands keep `description`, `argument-hint`, `allowed-tools`. A skill is a folder `<name>/SKILL.md` with `name` (== folder name) + `description`. Write descriptions in **English** so the model triggers them reliably; if the *output* should be localized (e.g. Vietnamese test cases), say so explicitly in the instructions.

## Before opening a PR

```bash
# valid JSON
python3 -m json.tool .claude-plugin/marketplace.json
python3 -m json.tool plugins/qa/.claude-plugin/plugin.json

# no cross-plugin .claude/ references
grep -rn '\.claude/\(rules\|skills\|agents\)/' plugins/

# every skill's `name:` matches its folder; referenced skill names exist
# python scripts compile
python3 -m py_compile plugins/qa/scripts/*.py
```

Bump `version` in `plugin.json` + `marketplace.json` for a release. Keep Java package examples on the neutral placeholder `com.example.*` (real projects set their own base package via their `CLAUDE.md`).
