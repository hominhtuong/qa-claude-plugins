---
name: bug-report-import
description: Import bugs from an exploratory report (results/<feature>/dev-bug-report-*.md, produced by /qa:exploratory) into Lark Bitable. Resolve & parse the report into structured bug drafts, map report fields → board fields (title→Name, Màn→Feature, Hiện tượng+steps+Actual→Input/Action, Kỳ vọng→Expected, severity 🔴/🟡/ℹ️→Priority, screenshot→Attachment), exclude NEEDS-TRIAGE by default, show a selection table for the user to pick which bugs to push, collect the missing fields (Dev PIC, Sprint, Version) ONCE for the batch, then hand each selected draft to skill log-bug to create it. Used by /qa:log-bug when the prompt is `from <feature|report.md>`.
---

# Skill: bug-report-import

Bridge **`/qa:exploratory` → Lark board**: an exploratory run already wrote a full bug report; this skill turns those bugs into board records **without re-typing them**. It does the *parse + map + pick + fill-the-gaps* work, then delegates the actual create to skill **[log-bug](../log-bug/SKILL.md)** (board config, read-only guard, duplicate check, upload, record link — all reused, never duplicated here).

> **LANGUAGE — RULE #1**: keep the source report's language as-is (default Vietnamese with diacritics — see [output-language.md](../../rules/output-language.md)). Don't translate or strip diacritics. Don't paraphrase a symptom/verbatim error; copy it.
> **CREATE ONLY — never modify/delete a record. NEVER print a token/secret.**

## Procedure

### 1. Resolve the report file
From the prompt after `from`/`import` (or a path the user pasted):
- **`from <feature-name>`** → newest `results/<feature-name>/dev-bug-report-*.md` (sort by the `<ddMMMyyyy>` in the name; Glob `results/<feature-name>/dev-bug-report-*.md`). Folder uses kebab-case, no diacritics (e.g. `quan-ly-don`).
- **`from <path>.md`** → use that file directly.
- **Bare feature name / nothing resolvable** → Glob `results/*/dev-bug-report-*.md`; 1 match → use it; several → list them and ASK which.
- **None found** → tell the user to run `/qa:exploratory <feature>` first (that's what produces the report), then stop.

Also read `results/<feature>/analysis.md` (the oracle) if present — it can sharpen the **Expected** wording when a bug's "Kỳ vọng" cites a spec rule.

### 2. Parse each bug section
The report follows [exploratory-bug-report-template.md](../../rules/exploratory-bug-report-template.md). Each bug is a heading like `## 🔴 BUG-1 (Critical) — <module>: <title>` followed by bullets. Extract per bug:

| From the report | → maps to logical field |
|---|---|
| heading severity emoji `🔴`/`🟡`/`ℹ️` (or `(Critical/Warning/Info)`) | **Priority** (see step 3) |
| `<module>: <title>` in the heading | **Name** (`[<module>] <title>`) |
| **Màn** (nav path) | **Feature / Tính năng** (the module/screen) + prepend to steps |
| **Hiện tượng** (+ any verbatim error/SQL/number block) | **Input/Action** body → `Actual` + the verbatim quote |
| reproduction steps / "Màn" path / `số lần lặp` | **Input/Action** body → `Steps` (path from Home) |
| **Root cause** (if present) | **Input/Action** body → `Notes` (helps dev) |
| **Tác động** | **Input/Action** body → `Notes` (impact) |
| **Kỳ vọng** | **Expected result** |
| **Bằng chứng** (`results/<feature>/screenshots/<file>.png`) | **Attachment** (upload in step 6) |
| `Defect ID: APP-NN` | keep in `Notes` for traceability (board has no such field) |

**Exclude by default**: the `❓ Cần dev xác nhận (NEEDS-TRIAGE)` and `✅ Đã kiểm tra — KHÔNG lỗi` sections — those are not confirmed bugs. (Mention how many NEEDS-TRIAGE items were skipped, so the user can opt them in explicitly.)

### 3. Map severity → Priority
Severity emoji in the report → an option in config `options.priority` (apply [priority.md](../../rules/priority.md) if the board uses different buckets):
- 🔴 Critical → `Critical` (or the top bucket)
- 🟡 Warning → `High`/`Medium` — pick per impact text, lean `Medium`
- ℹ️ Info → `Low`

The user can override per bug in the selection step. Keep a one-line rationale per bug (from the impact text) so the mapping is auditable.

### 4. Show the selection table — USER PICKS
Print one row per parsed `[APP-BUG]` (default: all selected) and ask the user which to push. Keep it scannable:

```
#  Sel  Pri       Màn / module            Tiêu đề lỗi                         Ảnh
1  [x]  Critical  Đã phát hành             tab crash + lộ raw SQL              ✓
2  [x]  High      Tạo đơn                  sai tổng tiền khi áp voucher        ✓
3  [ ]  Low       Cài đặt                  lệch padding nút Lưu                 ✗
   (+2 mục NEEDS-TRIAGE bị bỏ qua — nói "thêm cả triage" nếu muốn đẩy)
```
User replies with which numbers to push (default = all that are pre-selected; allow "all", "1,2", "chỉ critical"). Don't create anything yet.

### 5. Collect the missing fields ONCE for the batch
The report does **not** contain these — gather them a single time and apply to every selected bug (per-bug override allowed):
- **Dev PIC** — ASK (resolve via config `dev_pic:` → open_id). One owner for the batch, but let the user say e.g. "bug 2 → Hùng".
- **Sprint** — prompt → config `defaults.sprint` → ASK. (Skip if platform ∈ `skip.no_sprint`.)
- **Version** — prompt → try the report's "Ghi chú môi trường" (`build <ver>`) → config `defaults.version` → ASK. (Skip if platform ∈ `skip.no_version`.)
- **Platform / Type** — auto: platform from the report header / `defaults.platform`; Type (UI/UX vs Function vs Performance) inferred per bug from its symptom.

### 6. Create each selected bug — via skill `log-bug`
Hand each completed draft to the **[log-bug](../log-bug/SKILL.md)** create flow (do NOT reimplement it): it loads board config, runs the **read-only guard** + **daily multi-board confirm** (once for the batch), maps fields/options, **uploads the screenshot** from `Bằng chứng` and attaches the file token (upload fails → create without it, note which), runs the **duplicate check** if `check_duplicate: true`, creates the record, and returns a direct link.

Use the `Input data / Action` body template from the log-bug skill:
```
Preconditions (nếu có):
- ...
Steps:
1. ...
Actual:
- ... (kèm trích nguyên văn lỗi/SQL nếu có)
Notes (nếu có):
- Root cause: ...
- Tác động: ...
- Defect ID (exploratory): APP-NN
Account test: <defaults.test_account or from the report, if any>
```

### 7. Summary
Create sequentially; print a result table: `BUG-ID · Priority · Tiêu đề · record link · ảnh đính kèm?`. Note any skipped (deselected / NEEDS-TRIAGE / read-only board / duplicate found) and any screenshot that failed to upload (so the user attaches it manually).

## Principles
- **Reuse, don't fork**: this skill only parses + maps + picks + fills gaps. All board logic (config, guards, create, upload, links) stays in skill `log-bug`.
- **Don't invent data**: only the report's content + the 3 user-supplied fields (Dev PIC/Sprint/Version). A field absent in both → ASK, never fabricate.
- **NEEDS-TRIAGE is opt-in** — never auto-create a record for an unconfirmed observation.
- **Keep Vietnamese + verbatim quotes** exactly as the report wrote them.
- Idempotent intent: rely on `check_duplicate` so re-running `from <feature>` doesn't double-log.
