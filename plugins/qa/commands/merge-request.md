---
description: Review → fix → integrate latest target via a temp branch (safe merge) → push → open a Pull/Merge Request (auto-detects GitHub gh / GitLab glab from the remote)
argument-hint: [optional PR/MR title] [--target <target branch, default main>]
allowed-tools: Read, Glob, Grep, Edit, Write, Bash
---

# /merge-request — Open a clean PR/MR (no conflicts, no lost code)

Input: **$ARGUMENTS** (optional PR/MR title; target defaults to `main`).

Works with **any host** — GitHub, GitLab (gitlab.com or self-hosted/company), Bitbucket. Host & project are **derived from `git remote get-url origin`** of the current repo (never hard-coded). Goal: open a PR/MR for the current branch that has **no conflict with the target and loses no line of code** — by integrating the latest target through a **temp branch** before pushing.

## Step 0 — Detect the host (routing)
Read `git remote get-url origin` and pick the tool:
- host contains `github.com` (or `gh` is configured for it) → **GitHub**, use `gh pr create`.
- host contains `gitlab` (gitlab.com or any self-hosted GitLab) → **GitLab**, use `glab mr create`.
- otherwise → push the branch and print the compare URL for the user to open the PR/MR manually.

## Procedure (follow the order)

### 1. Quality gate — skills `review-audit` + `fix-by-layer` + `build-verify`
Same as steps 1–3 of `/push-code`: `review-audit` → auto-fix clear Criticals via `fix-by-layer` / STOP if a decision is needed → `build-verify` green. Not clean + green → do **not** open the PR/MR.

### 2. Settle branch & commit — skill `commit-push` (branch + commit only)
Determine `FEATURE` (on `main` → create `feat/<slug>`, never PR/MR main→main). Commit all pending changes (message `$ARGUMENTS` if provided + Co-Authored-By trailer). **Do not push yet.** Determine `TARGET` (default `main` or `--target`).

### 3. Fetch the latest target
`git fetch origin --prune`. Reference `origin/<TARGET>`.

### 4. Integrate via a temp branch (safe)
1. `git switch -c tmp/mr-<FEATURE> origin/<TARGET>` → `git merge --no-ff FEATURE`.
2. Conflict → resolve per the **Smart-merge rules** below. After resolving: no markers left (`grep` check) **and** `build-verify` green.

### 5. Bring the result back to FEATURE (fast-forward, no lost code)
- `git switch FEATURE` → `git merge --ff-only tmp/mr-<FEATURE>` → `git branch -D tmp/mr-<FEATURE>`.
- If (4)/(5) can't be rescued safely → `git merge --abort`, delete the temp branch, **STOP** + report the list of conflicting files needing a decision. Never drop code.

### 6. Push & open the PR/MR
- `git push -u origin FEATURE` (no force).
- **GitHub** (`gh` auto-detects the host from `origin`; if not logged in: `gh auth login`):
  ```bash
  gh pr create --base <TARGET> --head FEATURE --title "<title>" --body "<description>"
  ```
- **GitLab** (`glab` auto-detects the host from `origin`; if not logged in: `glab auth login --hostname <host of origin>`):
  ```bash
  glab mr create --source-branch FEATURE --target-branch <TARGET> \
    --title "<title>" --description "<description>" --remove-source-branch=false --yes
  ```
- CLI not authed → fallback to the host API: derive **host** + **project path** from `git remote get-url origin` (URL-encode the project for GitLab, e.g. `group/repo` → `group%2Frepo`), token from env (`GH_TOKEN`/`GITHUB_TOKEN` for GitHub, `GITLAB_TOKEN`/`GITLAB_PAT` for GitLab). NEVER print the token. Title = `$ARGUMENTS` or generated from the diff; description = change summary + review result + "integrated `origin/<TARGET>`, build green".
- After creating: confirm the PR/MR is **mergeable** (`gh pr view` / `glab mr view <iid>` or API `has_conflicts`). If the target moved → repeat steps 3–5.

## Smart-merge rules (on conflict)
Principle: **lose no code, never guess.**
1. NO global `-X ours`/`-X theirs`. Resolve hunk by hunk after understanding both sides.
2. Additive changes at different positions (method/field/import/config key) → **KEEP BOTH** (most conflicts in a *package-by-feature* repo are this kind).
3. `configurations/*.properties` → union keys from both sides. Member-owned `elements.json`/`test-hints.json`/`sitemap` → union nodes/fields.
4. Semantic conflict (same method/logic changed differently) → **do NOT decide alone**: record the file + both sides, `git merge --abort`, STOP, ask the user.
5. Shared files (`base`/`utils`/`actions`) → prefer keeping both; a real API conflict → treat as (4).
6. After each resolution: empty marker grep **and** green `build-verify` before continuing.

## Final report
Summarize the review (findings & fixes), the target-integration result (which files conflicted, how resolved), source/target branch, PR/MR link, mergeable status. If stopped → reason + the decision the user must make.
