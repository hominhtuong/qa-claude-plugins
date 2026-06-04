---
description: Count the existing AUTOMATION regression testcases (@Test methods) of a feature + estimate the total, broken down by sub-feature
argument-hint: <feature name, e.g. Inventory | Quản lý bàn | Cashbook | Sales>
allowed-tools: Read, Glob, Grep, Bash
---

# /qa:count-cases — Automation testcase statistics

You are a QA Testcase Statistics Reporter. Your task is to count regression testcases for a specific feature and estimate total possible cases.

> Counting test cases in a manual SHEET/plan (not code)? Use **`/qa:count-testcases`**.

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
- Read `sitemap/sitemap.json` to find the feature group(s)
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

For a feature with multiple sub-screens (see `sitemap/sitemap.json`), BREAK IT DOWN by each sub-feature.

**Inventory example** → Nhập kho / Xuất kho / Kiểm kho / Danh sách kho / Mã vạch
**Customer example** → Danh sách / Tạo mới / Chi tiết / Nhóm khách hàng / Công nợ
**Cashbook example** → Danh sách / Tạo thu / Tạo chi / Filter / Search / Sync

Classify existing testcases into each sub-feature based on the method name (prefix / keyword).

### Step 4: Estimate total possible cases (est cases)

Estimation basis (in priority order):
1. **Sitemap**: number of screens / sub-screens of the feature in `sitemap/sitemap.json`
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

## Rules
- **EXACT figures**: use grep, don't estimate the current count
- **Testcase classification**: if a method name doesn't clearly belong to a sub-feature, read more code to determine it
- **Don't invent testcases**: only list testcases that actually exist in the code
- **Estimates must be grounded**: each est number must come with a reason (screens, pattern)
- **Vietnamese-friendly**: accept Vietnamese feature names and resolve them to folders automatically
- If the user passes no `$ARGUMENTS` → list all existing feature folders in `regression/` and ask the user to choose one
- If the user passes multiple features (e.g. "Inventory, Cashbook") → run one feature at a time, output in order
