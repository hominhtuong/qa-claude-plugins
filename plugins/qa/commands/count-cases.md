---
description: Count test cases & coverage — auto-detects mode → AUTOMATION counts @Test methods in the regression code + estimates total by sub-feature, or MANUAL counts TC_ID rows in a created sheet/plan-tests and reports coverage by section
argument-hint: <feature name> OR <xlsx/plan path | Google/Lark Sheet link> [--auto|--manual]
allowed-tools: Read, Glob, Grep, Bash
---

# /count-cases — Test case statistics (mode router)

Request: **$ARGUMENTS**

## Step 0 — Detect mode
Run **skill `detect-mode`** → `automation` | `manual`. Read ONLY the matching section below.

---

# Mode: automation — count @Test in the codebase

You are a QA Testcase Statistics Reporter. Your task is to count regression testcases for a specific feature and estimate total possible cases.

## Input
- Feature name from user: $ARGUMENTS
- Examples: `Inventory`, `Quản lý bàn`, `Cashbook`, `Sales`, `Khuyến mại`

## Terminology (MUST follow)
- **1 testcase = 1 method annotated `@Test`** (do NOT count `@BeforeClass` / `@BeforeMethod` / `@AfterClass` / `@AfterMethod`)
- Don't call it a "test", call it a "testcase"
- Setup/teardown methods (`initScreen`, `cleanupBackToHome`, `restoreHomeState`, `resetTo*`, `passingData`) → do NOT count as business testcases
- Test class alias (extends another class, no own `@Test`) → count by the parent class's `@Test`

## Process

### Step 1: Resolve feature → folder mapping
- Read `sitemap/sitemap.md` to find the feature group(s)
- Map Vietnamese name → English folder if needed:
  - "Quản lý bàn" → `table` / `table-management`
  - "Sổ quỹ" → `cashbook`
  - "Khách hàng" → `customer`
  - "Sản phẩm" → `product`
  - "Khuyến mại" → `promotion`
  - "Báo cáo" → `report`
  - "Bán hàng" → `sales`
  - "Kho" / "Quản lý kho" → `inventory`
  - "Cài đặt" → `settings`
  - "Đơn hàng" → `orders`
- If the folder does not exist in `src/test/java/com/example/tests/regression/` → state clearly "No regression file yet for {feature}, est from scratch"

### Step 2: Count current testcases (EXACT, no estimation)

```bash
# Count @Test annotations accurately
find src/test/java/com/example/tests/regression/<folder> -name "*.java" -exec grep -cE "^\s*@Test(\(|$|\s)" {} +

# List @Test methods with their names
grep -B1 "public void" src/test/java/com/example/tests/regression/<folder>/*.java | grep -E "(@Test|public void)"
```

- For alias classes (`extends com.example.tests.X.YTest`) → also count parent's `@Test` methods
- Verify by reading file structure if grep result is suspicious

### Step 3: Identify sub-features

For a feature with multiple sub-screens (see `sitemap/sitemap.md`), BREAK IT DOWN by each sub-feature.

**Inventory example** → Nhập kho / Xuất kho / Kiểm kho / Danh sách kho / Mã vạch
**Customer example** → Danh sách / Tạo mới / Chi tiết / Nhóm khách hàng / Công nợ
**Cashbook example** → Danh sách / Tạo thu / Tạo chi / Filter / Search / Sync

Classify existing testcases into each sub-feature based on the method name (prefix / keyword).

### Step 4: Estimate total possible cases (est cases)

Estimation basis (in priority order):
1. **Sitemap**: number of screens / sub-screens of the feature in `sitemap/sitemap.md`
2. **Test-hints**: read `src/main/java/com/example/screens/<group>/test-hints.json` → number of fields, validation rules, business rules
3. **Test-playbook patterns** (`sitemap/test-playbook.md`):
   - UI check: 1 case / screen
   - Search: 3-4 cases (exact / partial match / not exist / clear)
   - Filter: 1 case / filter chip
   - CRUD: create valid + validation per required field + edit + delete + duplicate
   - Sync with related module: 1-2 cases
   - Empty / loading state: 1-2 cases
   - Status tabs: 1 case / tab
4. **Edge cases**: amount overflow, network error, permission, role-based access

STATE the estimation basis for each sub-feature. This is an estimate — do NOT claim it as an exact number.

### Step 5: Output report (MUST follow this format)

```
═══════════════════════════════════════
📊 THỐNG KÊ TESTCASE — {Tên tính năng}
═══════════════════════════════════════

🎯 Tổng quan:
  • Est cases  : XX cases
  • Hiện có    : YY cases
  • Còn lại    : ZZ cases chưa làm (XX - YY)
  • Độ phủ     : NN%

📂 Chi tiết theo sub-feature:

| Sub-feature         | Est  | Hiện có | Còn lại | Độ phủ |
|---------------------|-----:|--------:|--------:|-------:|
| {sub-feature 1}     | XX   | YY      | ZZ      | NN%    |
| {sub-feature 2}     | XX   | YY      | ZZ      | NN%    |
| ...                 |      |         |         |        |
| **TỔNG**            | XX   | YY      | ZZ      | NN%    |

📝 Danh sách testcase hiện có (YY cases):

**Sub-feature {1}** ({N} cases):
  1. `testMethodName1` — mô tả ngắn
  2. `testMethodName2` — mô tả ngắn

**Sub-feature {2}** ({N} cases):
  ...

🔍 Căn cứ ước lượng est cases:
  • Sub-feature {1}: {N screens × M cases pattern} = XX
    - UI: 1, Search: 3, CRUD: 6, Validation: 4, ...
  • Sub-feature {2}: ...

⚠️ Gaps ưu tiên bổ sung (top 5):
  1. {sub-feature} — {testcase còn thiếu}, lý do priority: {business critical / regression risk / customer report}
  2. ...

📌 Ghi chú:
  - Số liệu "Hiện có" đếm chính xác bằng grep `^\s*@Test`
  - Số "Est" là ước lượng dựa trên sitemap + test-playbook patterns, không phải test plan chính thức
  - Nếu có manual test plan từ QC → cần map lại để chính xác hơn

═══════════════════════════════════════
```

## Rules (automation)
- **EXACT figures**: use grep, don't estimate the current count
- **Testcase classification**: if a method name doesn't clearly belong to a sub-feature, read more code to determine it
- **Don't invent testcases**: only list testcases that actually exist in the code
- **Estimates must be grounded**: each est number must come with a reason (screens, pattern)
- **Vietnamese-friendly**: accept Vietnamese feature names and resolve them to folders automatically
- If the user passes no `$ARGUMENTS` → list all existing feature folders in `regression/` and ask the user to choose one
- If the user passes multiple features (e.g. "Inventory, Cashbook") → run one feature at a time, output in order

---

# Mode: manual — count TC_ID rows in a sheet/plan

You are a **QA Testcase Statistics Reporter**. Task: accurately count the test cases present in a sheet/plan-tests and report coverage by feature/section.

> **LANGUAGE — RULE #1**: Generate the report in Vietnamese (with diacritics).

## Input
- Path to a created `.xlsx` file (e.g. `results/<feature>/<prefix>-final.xlsx`), OR
- A Google/Lark Sheet link, OR
- A plan `.md` file (`plans/<feature>/<prefix>.md`) — count by the Test Case Matrix, OR
- A feature name → find the corresponding file in `results/` and `plans/`.

## Terminology (MUST follow)
- **1 test case = 1 row with a TC_ID** (`TC_001`, `TC_002`...). Do NOT count **section header** rows (group-title rows without a TC_ID).
- **Multi-result**: each TC_ID row is its own test case (even if description/precondition is merged) — count by the **number of TC_ID rows**, not grouped by description.
- Checklist (`CL_xxx`) and Regression (`RT_xxx`) are counted similarly, reported separately per type.

## Process
1. **Resolve the source**:
   - xlsx → read with Python (openpyxl): for EACH sheet, count column A cells matching the pattern `TC_\d+` / `CL_\d+` / `RT_\d+`. Sheet name = feature/module.
   - Google/Lark Sheet link → read via the available API/MCP (`get_sheet_data` / `list_sheets`), count similarly per sheet.
   - Plan `.md` → parse the Test Case Matrix (Total column) per section.
2. **Count accurately** (do NOT estimate the existing count) — TC_ID resets per sheet, so count per sheet then sum.
3. **Classify coverage** for each section/sheet: estimate the Positive / Negative / Boundary / Edge ratio based on the content (if the plan has a Matrix → use those numbers). Flag any section **missing negative coverage** (negative = 0 is a red flag).
4. **Output report** (MUST follow the format):

```
═══════════════════════════════════════
📊 THỐNG KÊ TEST CASE — {Tên feature}
═══════════════════════════════════════

🎯 Tổng quan:
  • Tổng test case : NN (TC: .. | CL: .. | RT: ..)
  • Số sheet/module: MM

📂 Chi tiết theo sheet/section:

| Sheet / Section | Total TC | Positive | Negative | Boundary | Edge |
|-----------------|---------:|---------:|---------:|---------:|-----:|
| {sheet 1}       | XX       | ..       | ..       | ..       | ..   |
| ...             |          |          |          |          |      |
| **TỔNG**        | NN       |          |          |          |      |

⚠️ Cảnh báo coverage:
  • {section} — thiếu negative case (0) / chỉ có positive
  • ...

📌 Ghi chú:
  - Số "Tổng" đếm chính xác theo dòng TC_ID (không tính section header)
  - Multi-result: mỗi dòng TC_ID = 1 case
═══════════════════════════════════════
```

## Rules (manual)
- **ACCURATE figures**: count with code/grep, do not estimate the existing count.
- **Do NOT count section headers** as test cases.
- If no source is found for a feature → clearly report "Chưa có sheet/plan-tests cho {feature}".
- Multiple sources (multiple features) → run each one, output in order.
