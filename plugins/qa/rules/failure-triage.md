# Failure Triage — Distinguishing "APP bug" vs "FRAMEWORK bug" (MANDATORY)

> **Project context**: the app under test (AUT) is **NOT a golden/reference app** — it may be buggy/unfinished, especially when it's new or being rewritten. So the goal of exploratory + running tests is **not** to assume the app is correct, but to **find which features are broken** (against spec/PRD/design), and to **clearly** attribute the root cause.
>
> This rule applies to every command/skill that can hit a failure: `exploratory`, `run`/`run-app`/`run-web`, `fix`/`fix-by-layer`, `plan-tests`, `cook`, `review-*`. Every FAIL / element-not-found **MUST** be classified per the taxonomy below; do NOT let a FAIL "drift" unlabeled.

---

## 1. Root-cause taxonomy (assign to every FAIL)

| Label | Meaning | Typical example | Action |
|------|-------|-----------------|--------|
| `[APP-BUG]` | **Application bug** — the app behaves wrong vs expectation (spec / PRD / design). | Crash, on-screen exception (e.g. `SqliteException(2067)`), wrong data, missing/"coming soon" feature, validation that doesn't block, wrong navigation, unresponsive button. | **Do NOT fix the test to pass.** Record a **Defect** → report to dev. Keep the test's correct expectation (red = real bug) or mark known-defect with a ticket. |
| `[FRAMEWORK]` | **Project/automation bug** — the app is CORRECT but the test is wrong: bad/stale locator, wrong element-finding strategy, missing wait, wrong assumed screen, wrong assertion expectation. | The element really exists (page source confirms) but the query is off; manual works but the test is red. | **Fix** via skill `fix-by-layer` (Screen locator / Test / wait). Do NOT touch the app. |
| `[ENV]` | **Environment** — device/emulator, Appium server, permissions, network. | `adb` loses the device, Appium down, permission popup blocks, Appium port. | Fix env/preflight; don't touch app/test logic. |
| `[DATA]` | **Data/precondition** — the test account lacks data to cover (empty list…). | Empty Inbound/Outbound stock list → no item to open detail. | Seed data / adjust precondition; don't conclude app/test is wrong. |
| `[NEEDS-TRIAGE]` | **Not yet attributed** — insufficient evidence. | Just saw red, haven't re-checked on the real app. | **Mandatory** re-verify (MCP/manual) then change to a label above. Do NOT leave as-is. |

> The cause label is **independent** of severity (Critical/Warning/Info). A FAIL always has **one cause label** + **one severity**.

---

## 2. Attribution procedure (App-bug or Framework-bug?)

**Golden rule: reproduce on the REAL APP before concluding.** (via Appium MCP — skill `navigate-app` — or manually.)

```
FAIL / element-not-found
   │
   ├─ Reproduce manually on the real app (MCP/by hand)
   │
   ├─ Does the feature WORK CORRECTLY by hand?
   │     ├─ YES → the bug is NOT in the app:
   │     │        ├─ element is in page_source but the test queries wrong → [FRAMEWORK] (locator/strategy/wait)
   │     │        ├─ missing data/precondition                              → [DATA]
   │     │        └─ device/Appium/permission/network                       → [ENV]
   │     └─ NO (manual also fails/crashes/missing) → [APP-BUG]
   │
   └─ Element-not-found specifics:
         ├─ page_source does NOT have the element (truly absent / "coming soon" / different screen) → [APP-BUG] (missing/changed feature)
         └─ page_source HAS the element, only our locator/strategy is wrong                          → [FRAMEWORK]
```

**Mandatory evidence attached to the label:**
- `[APP-BUG]`: screenshot of the wrong behavior + reproduction steps + expected (per spec/PRD/design) vs actual.
- `[FRAMEWORK]`: a page-source excerpt proving the element/behavior is correct + the wrong locator currently used.
- `[ENV]`/`[DATA]`: description of the missing condition.

> Watch for a common pitfall (see [troubleshooting.md](troubleshooting.md)): MCP `find_element` strategy `id` sometimes doesn't match Flutter's bare resource-id → **that's a quirk of the MCP TOOL, NOT an app-bug and NOT a runtime framework-bug** (because `@MobileFindBy(id=...)` matches correctly at runtime). Don't mistake it for an app bug.

---

## 3. How to report — clear attribution in BOTH reports

### 3a. Exploratory report (`results/<feature-name>/dev-bug-report-<ddMMMyyyy>.md`)
Split into **2 separate sections**, do not mix:
- **🐛 App defects (`[APP-BUG]`)** — table: `# | Màn | Kỳ vọng | Thực tế | Mức độ | Bằng chứng (screenshot) | Bước tái hiện`.
- **🧰 Framework / locator issues (`[FRAMEWORK]`/`[ENV]`/`[DATA]`)** — table: `# | Vấn đề | Nguyên nhân | Cách xử lý`.
- The overall observation table has an extra **"Triage" column** carrying exactly one label per FAIL/⚠️ row.

### 3b. HTML run report (ExtentReports, each `/run`)
- **Mandatory** convention: the `Utils.failCap/infoCap` message **starts with the label** so it shows inline in the HTML:
  ```java
  Utils.failCap(driver, node, "[APP-BUG] Tab 'Đã phát hành' crash SqliteException(2067) khi load");
  Utils.failCap(driver, node, "[FRAMEWORK] btn_filter_status đổi locator — cần cập nhật Screen");
  Utils.infoCap(driver, node, "[DATA] List nhập kho rỗng — skip mở chi tiết");
  ```
- When summarizing `/run` results: group FAILs by label (how many APP-BUG vs FRAMEWORK vs ENV/DATA) → the reader instantly knows whether it's "app broken" or "test broken".

### 3c. HTML test-case report (`report-template.html` → `results/<module>/<module>-testcase-report.html`)
- Use a **Result/Triage** column/legend (`Pass` · `App-bug` · `Framework` · `Env/Data` · `Needs-triage`) + a **Defect summary** section listing `[APP-BUG]` to hand off to dev.

---

## 4. Implications when building tests (MANDATORY to remember)

- **Do NOT hide app bugs to "go green".** Don't relax assertions, don't `try/catch` swallow errors, don't `Thread.sleep` to dodge an app-bug. If the app is wrong → the test must reflect that wrongness (genuinely red, or known-defect with a ticket), not a fake pass.
- **A red test ≠ always fix the test.** Before `fix`, attribute: red because of `[FRAMEWORK]` (fix the test) or because of `[APP-BUG]` (report to dev, keep the test honest).
- Each `[APP-BUG]` found in `/cook` or `/run` → record it in the corresponding report + mention it in the summary so QA can hand it to dev.
</content>
