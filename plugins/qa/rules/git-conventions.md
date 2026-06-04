# Git Conventions (shared)

Git conventions shared across every automation project. Skill `commit-push` enforces most of these rules.

## Branch
- Do **NOT** commit/push directly to `main`/`master`. Always create a feature branch `feat/<slug>` (or `fix/<slug>`, `chore/<slug>`).
- One PR/MR = one feature. Infer the branch slug from the diff content.

## Commit message (Conventional Commits)
- Format: `<type>(<scope>): <short description>` — type ∈ `feat|fix|test|chore|refactor|docs|ci`.
- Examples: `test(order): them smoke flow tao don`, `fix(auth): sua locator nut dang nhap`.
- End the commit message with the trailer:
  ```
  Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
  ```

## Push
- `git push -u origin <branch>` — **no** `--force`.
- Only commit/push **when the user requests it**.
- Do not add junk/secret files: skip `results/tests/` run artifacts, `.claude/qa-claude/.env`, tokens, files containing secrets (cross-check `.gitignore`).

## Gate before committing
1. `review-audit` clean of Critical/Blocker.
2. `build-verify` green (`mvn clean compile test-compile`).
3. Only then proceed to `commit-push`.
