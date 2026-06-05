# Output Language Rule

The language of everything the plugin **generates for the user** — bug reports, test cases,
test plans, analysis/summary docs, review findings, and the prose a command prints at the end —
is controlled by **one** setting. **Read when**: any command/skill that produces a report,
deliverable, or user-facing summary (`exploratory`, `gen-testcases`, `plan-tests`,
`plan-gen-testcases`, `analyze`, `analyze-spec`, `log-bug`, `count-*`, `review-*`, `sitemap`,
`status`, `find-elements`, `ask`, and their skills).

## The setting
- **Source**: `.claude/qa-claude/.plugin.env` → key **`LANGUAGE`**.
- **Values**: `Vietnamese` (default) · `English`. Case-insensitive.
- **Default = Vietnamese** when the key is missing, empty, the file doesn't exist, or the
  value is unrecognized. **Never block** on a missing value — silently fall back to Vietnamese.
- **How to read it**: before writing a deliverable, read that one line from the file (Read/Grep
  `LANGUAGE`; strip any inline `#` comment and surrounding whitespace). No script call needed.
  If a command spawns sub-agents to produce output, it MUST pass the resolved language into each
  sub-agent prompt (the sub-agent can't see the env file).

## What FOLLOWS the language (OUTPUT — user-facing)
Write these in the configured language (Vietnamese **with full diacritics** by default —
"Đăng nhập", not "Dang nhap"; keep technical terms like API/token/session in English):
- **Bug reports** (`/qa:exploratory`, `/qa:log-bug`) — body, titles, symptom / impact / expectation prose.
- **Test cases / checklists** (`/qa:gen-testcases`) — description, precondition, steps, expected, section titles.
- **Test plans & analysis** (`/qa:plan-tests`, `/qa:plan-gen-testcases`, `/qa:analyze`, `/qa:analyze-spec`).
- **Review findings, status summaries, counts**, and the final message a command prints to the user.
- Free-text `notes` / `realName` in sitemap nodes.

## What STAYS English / technical (regardless of `LANGUAGE`)
- All skill/command **definitions**, every `rules/*.md`, `SCHEMA.md`, and any **`CLAUDE.md`** — always English.
- **Code**: Page Objects, test methods, identifiers, element `name` + locators, file/folder names
  (kebab-case, no diacritics), sitemap `id` / `route` / `testFeature`, JSON keys.
- **Git** commit messages, branch names, PR/MR titles & bodies — English (engineering convention).
- **Verbatim evidence**: quote app strings / error text / SQL **exactly** as they appear — never translate a quote.

## Rule of thumb
Prose meant for a human reader → the configured language. Anything a machine parses or a dev
greps → English/technical. When `LANGUAGE=English`, emit the Vietnamese-labelled template fields
(e.g. the bug-report skeleton's `Màn` / `Hiện tượng` / `Kỳ vọng`) in English instead. When
`Vietnamese`, keep diacritics — undecorated Vietnamese output is **wrong**.
