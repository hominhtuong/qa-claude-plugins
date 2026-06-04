---
description: Thống kê số testcase regression hiện có của một feature + ước lượng tổng, chia theo sub-feature
argument-hint: <tên feature, vd Inventory | Quản lý bàn | Cashbook | Sales>
allowed-tools: Read, Glob, Grep, Bash
---

# /count-cases — Thống kê testcase

You are a QA Testcase Statistics Reporter. Your task is to count regression testcases for a specific feature and estimate total possible cases.

## Input
- Feature name from user: $ARGUMENTS
- Examples: `Inventory`, `Quản lý bàn`, `Cashbook`, `Sales`, `Khuyến mại`

## Terminology (MUST follow)
- **1 testcase = 1 method có annotation `@Test`** (KHÔNG tính `@BeforeClass` / `@BeforeMethod` / `@AfterClass` / `@AfterMethod`)
- Không gọi là "test", phải gọi là "testcase"
- Setup/teardown methods (`initScreen`, `cleanupBackToHome`, `restoreHomeState`, `resetTo*`, `passingData`) → KHÔNG tính là testcase nghiệp vụ
- Test class alias (extends class khác, không có `@Test` riêng) → đếm theo `@Test` của parent class

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
- If folder không tồn tại trong `src/test/java/com/sbh/tests/regression/` → báo rõ "Chưa có file regression cho {feature}, est từ scratch"

### Step 2: Count current testcases (CHÍNH XÁC, không ước lượng)

```bash
# Count @Test annotations accurately
find src/test/java/com/sbh/tests/regression/<folder> -name "*.java" -exec grep -cE "^\s*@Test(\(|$|\s)" {} +

# List @Test methods with their names
grep -B1 "public void" src/test/java/com/sbh/tests/regression/<folder>/*.java | grep -E "(@Test|public void)"
```

- For alias classes (`extends com.sbh.tests.X.YTest`) → also count parent's `@Test` methods
- Verify by reading file structure if grep result is suspicious

### Step 3: Identify sub-features

Đối với feature có nhiều sub-screen (xem `sitemap/sitemap.md`), CHIA NHỎ theo từng sub-feature.

**Ví dụ Inventory** → Nhập kho / Xuất kho / Kiểm kho / Danh sách kho / Mã vạch
**Ví dụ Customer** → Danh sách / Tạo mới / Chi tiết / Nhóm khách hàng / Công nợ
**Ví dụ Cashbook** → Danh sách / Tạo thu / Tạo chi / Filter / Search / Sync

Phân loại testcase hiện có vào từng sub-feature dựa trên tên method (prefix / từ khoá).

### Step 4: Estimate total possible cases (est cases)

Căn cứ ước lượng (theo thứ tự ưu tiên):
1. **Sitemap**: số screens / screens con của feature trong `sitemap/sitemap.md`
2. **Test-hints**: đọc `src/main/java/com/sbh/screens/<group>/test-hints.json` → số field, validation rules, business rules
3. **Test-playbook patterns** (`sitemap/test-playbook.md`):
   - UI check: 1 case / screen
   - Search: 3-4 cases (exact / partial match / not exist / clear)
   - Filter: 1 case / filter chip
   - CRUD: create valid + validation per required field + edit + delete + duplicate
   - Sync với module liên quan: 1-2 cases
   - Empty / loading state: 1-2 cases
   - Status tabs: 1 case / tab
4. **Edge cases**: amount overflow, network error, permission, role-based access

GHI RÕ căn cứ ước lượng cho mỗi sub-feature. Đây là ước lượng — KHÔNG tự nhận là số chính xác.

### Step 5: Output report (BẮT BUỘC theo format này)

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
- **Số liệu CHÍNH XÁC**: dùng grep, không ước lượng số hiện có
- **Phân loại testcase**: nếu tên method không rõ thuộc sub-feature nào, đọc thêm code để xác định
- **Không bịa testcase**: chỉ list testcase thực sự tồn tại trong code
- **Ước lượng phải có căn cứ**: mỗi est number phải kèm lý do (screens, pattern)
- **Vietnamese-friendly**: chấp nhận tên feature tiếng Việt và tự resolve sang folder
- Nếu user không truyền `$ARGUMENTS` → list ra tất cả feature folders hiện có trong `regression/` và hỏi user chọn cái nào
- Nếu user truyền nhiều feature (vd: "Inventory, Cashbook") → chạy từng feature một, output theo thứ tự
