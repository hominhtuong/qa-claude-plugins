# Exploratory Bug Report — Template (standard format to send to dev)

> **Mandatory** output format for `/exploratory` (and for the exploratory-gate of `/plan-tests`). Output lives in the PROJECT under `reports/exploratory/` (created at run time).
>
> **Output language**: the report body is written in **Vietnamese (with diacritics)** — it is a deliverable sent to the Vietnamese dev team. The instructions below are in English; the template field labels are kept in Vietnamese as they are part of the deliverable.
>
> - **Output file**: `reports/exploratory/<group>/dev-bug-report-<ddMMMyyyy>.md` (e.g. `dev-bug-report-03Jun2026.md`). If running multiple groups on the same day → one file/day grouping all groups, or one file per group.
> - **Screenshot evidence**: saved in `reports/exploratory/<group>/screenshots/`, **named by BUG-ID** (`02-APP01-published-tab-sqlite-crash.png`). Each `[APP-BUG]` MUST have at least one screenshot.
> - Each bug is also **appended to the defect register** `reports/exploratory/bug-summary.md` (assign an APP-ID, update the count table + severity distribution).
> - Assign labels per [failure-triage.md](failure-triage.md). **Only `[APP-BUG]` blocks test writing** (see `/plan-tests`).

---

## File structure (copy this skeleton)

The report body below is the Vietnamese-language deliverable; keep the Vietnamese field labels and fill them in in Vietnamese.

```markdown
# 🐛 Bug Report gửi Dev — <App> (exploratory <ddMMMyyyy>)

> App `<package>` · build `<ver>` · <platform> · device `<id>` · account `<sđt>`.
> Defect register đầy đủ: bug-summary.md. Bản này gom **N lỗi** ưu tiên gửi dev.

---

## 🔴 BUG-1 (Critical) — <module>: <tiêu đề lỗi ngắn gọn, có giá trị>

- **Màn**: <đường điều hướng từ Home → … → màn lỗi>.
- **Hiện tượng**: <mô tả khách quan>. Trích **nguyên văn** thông báo lỗi / SQL / text sai trong ``` code block ``` nếu có.
- **Root cause (nếu suy ra được từ thông báo)**: <phân tích ngắn — vd conflict target SQL sai, sai công thức>.
- **Tác động**: <ảnh hưởng người dùng / nghiệp vụ — vd lộ schema, sai chứng từ pháp lý>.
- **Kỳ vọng**: <hành vi đúng theo spec/PRD>.
- **Bằng chứng**: `reports/exploratory/<group>/screenshots/<file>.png`.
- *(Defect ID register: **APP-NN**.)*

## 🔴 BUG-2 (Critical) — …
## 🟡 BUG-3 (Warning) — …
## ℹ️ BUG-k (Info) — …

---

## ✅ Đã kiểm tra — KHÔNG lỗi (app hoạt động đúng)
- <màn A> (mô tả ngắn cái đã verify) — OK.
- <màn B> — OK.

## ❓ Cần dev xác nhận (low-confidence, NEEDS-TRIAGE)
- <quan sát chưa đủ bằng chứng kết luận bug> — cần dev xác nhận hành vi mong muốn.

## Ghi chú môi trường
- <điều kiện env/data ảnh hưởng test — vd device không sạc, account thiếu data>.
```

---

## Content conventions (quality > quantity)

1. **Valuable bug title**: state the core symptom precisely (e.g. "tab Đã phát hành crash + lộ raw SQL"), not generic ("error on screen X").
2. **Objective evidence**: quote the error/SQL/wrong number verbatim; give **clear reproduction steps** (path from Home); record the **number of reproductions** (e.g. 2/2).
3. **Root cause when visible**: if the error message reveals the cause (SQL conflict, formula), give a short analysis — it helps dev fix faster. Do NOT make it up if unsure.
4. **Severity** by impact: 🔴 Critical (crash / wrong legal document / loss of a core function / security exposure) · 🟡 Warning (partly wrong / UX stuck / missing feature vs spec) · ℹ️ Info (id-convention deviation, small localization).
5. **The "Verified — no bug" section is mandatory** — it tells dev the covered scope (so "not tested" ≠ "no bug").
6. **Be honest**: the app is a port that may have bugs — do NOT hide bugs, do NOT conclude `[APP-BUG]` before reproducing on the real app (uncertain → `NEEDS-TRIAGE`).
</content>
