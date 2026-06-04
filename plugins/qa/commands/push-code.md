---
description: Review code (review-audit) → auto-fix clear Blockers → green build → commit & push the current branch to origin
argument-hint: [optional commit message — empty = auto-generate from the diff]
allowed-tools: Read, Glob, Grep, Edit, Write, Bash
---

# /qa:push-code — Review → fix → build → push

Input (optional commit message): **$ARGUMENTS**

Goal: only push code that is **rule-clean and compiles green**. The command composes 4 skills in order, applying push-specific finding-handling policy. Works with any remote host (GitHub / GitLab / Bitbucket / self-hosted) — it only does `git push`.

## Procedure (follow the order)

### 1. Review — skill `review-audit`
Audit uncommitted changes against `review-checklist` → findings by severity.

### 2. Handle findings (push policy) — skill `fix-by-layer`
- **🔴 Critical with a clear root cause** (assertion inside a Screen, `driver.findElement()` inside a Test, hard-coded secret, `Thread.sleep`, missing `isDisplayed()`…) → **auto-fix** via skill `fix-by-layer`. After fixing → re-run `review-audit` on the changed part.
- **🔴 Critical that is ambiguous / needs a business decision** → **STOP, do not push**, report to the user with a proposal.
- **🟡** auto-fix if small & safe, otherwise record in the report (non-blocking). **ℹ️** record only.

### 3. Green build — skill `build-verify`
`mvn clean compile test-compile` green (mandatory gate). Not green → STOP, do not push.

### 4. Commit & push — skill `commit-push`
Determine the branch (never push straight to `main`/`master` → create `feat/<slug>`), stage while avoiding secrets, commit Conventional + Co-Authored-By trailer (message: `$ARGUMENTS` if provided), `git push -u origin` without force.

## Final report
Summarize the review (findings by severity, which were fixed / which remain), committed files, branch name, push result. If stopped midway → state the reason + the decision the user needs to make. Include a **Missing ID Report** if there are non-id elements.
