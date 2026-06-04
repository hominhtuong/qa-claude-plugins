---
name: commit-push
description: Reusable logic to commit & push safely — never push directly to main/master (auto-creates a feat/<slug> branch), commit per Conventional Commits with a Co-Authored-By trailer, push -u without force. Used by push-code and merge-request after the code is clean + build is green. Runs only when the user requests it.
---

# Skill: commit-push

Reusable capability: get clean changes onto origin safely. Runs **only after** `review-audit` is clean of Critical and `build-verify` is green, and **only when the user requests it**.

## Procedure
1. **Determine the branch**: `git branch --show-current`.
   - On the **default branch** (`main`/`master`) → **do NOT push directly**. Create a feature branch `feat/<slug>` (inferred from the diff, or ask for a name if unclear) → `git switch -c <branch>`.
   - Any other branch → keep it.
2. **Stage**: `git add` the in-scope files; avoid adding junk/secret files (cross-check `.gitignore` — do not add `reports/`, tokens, `.properties` containing secrets).
3. **Commit message**: use the parameter if provided; empty → auto-generate a short Conventional Commit from the diff (e.g. `test(order): them smoke flow tao don`). End with the line:
   `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`
4. **Push**: `git push -u origin <branch>`. Remote rejects (branch behind remote) → `git fetch` + notify the user, do **NOT** force-push.
5. **Report**: committed files, branch name, push result (branch URL if the remote prints it).

> Only commit/push when the user requests it (via command `/push-code` or `/merge-request`). Do not act on your own.
