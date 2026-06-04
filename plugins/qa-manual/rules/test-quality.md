# Test Quality Rules

Test case quality standards: steps, expected result, multi-result, negative coverage.
**Read when**: command `cook`, `plan-tests`, `analyze` and skill `gen-testcases`.

> **Language — RULE #1**: Generate all test case content in Vietnamese (with diacritics) (description, precondition, steps, expected, section title). "Đăng nhập" is NOT "Dang nhap"; "Mật khẩu" is NOT "Mat khau". Keep technical terms in English (API, token, session, database). Content without diacritics is WRONG and must be fixed. This rule applies to sub-agents too.

---

## 1. Steps Quality

- **Steps describe ONLY actions** (action) — what the tester does. Do NOT write a step that looks like an expected result / a verification statement.
- Each step must have all of: **action + data + UI location**. Detailed enough that the reader can execute it immediately.
- GOOD (step is an action):
  ```
  1. Mở app > Vào màn hình Đăng nhập
  2. Nhập "test@gmail.com" vào ô Email
  3. Nhập "123456" vào ô Mật khẩu
  4. Nhấn nút "Đăng nhập"
  ```
- BAD — step looks like an expected result (MUST NOT DO):
  ```
  1. Xác nhận bảng hiển thị đủ 5 cột dữ liệu
  2. Kiểm tra dòng thứ 2 có ngày tạo cũ hơn dòng thứ 1
  ```
  These are verification statements, NOT steps. A step must be an action: "Quan sát bảng danh sách", "Cuộn xuống dòng tiếp theo"...
- BAD — too generic (MUST NOT DO):
  ```
  1. Đăng nhập với tài khoản hợp lệ
  ```

## 2. One Test Objective Per TC

- Each test case verifies **EXACTLY 1 objective**. Do NOT combine multiple scenarios into 1 TC.
- A TC must be **independent** — not dependent on the result of another TC.
- A precondition can be reused (define a shared setup).

## 3. Multi-Result TC Format (MANDATORY)

When 1 test description has **multiple expected results to verify** → use this format:

- **Number of TC_IDs = number of expected results**. Each expected result gets 1 row, its own TC_ID.
- **Test Description**: merged across all rows in the same group (identical).
- **Pre-Condition**: merged across all rows in the same group (identical).
- **1 step = 1 expected result**. Each row has exactly 1 step + 1 corresponding expected result.
- The step describes the **action** to perform; the expected result describes **what to verify**.

**Example**: Description "Kiểm tra hiển thị bảng danh sách sổ" has 3 points to verify:

| TC_ID | Test Description | Pre-Condition | Steps to Perform | Steps Expected Result |
|-------|-----------------|---------------|-------------------|----------------------|
| TC_001 | Kiểm tra hiển thị bảng danh sách sổ | Đã đăng nhập, truy cập màn hình danh sách sổ | Quan sát các cột trong bảng danh sách | Bảng hiển thị đủ 5 cột: Mã sổ, Tên sổ, Ngày tạo, Người tạo, Trạng thái |
| TC_002 | Kiểm tra hiển thị bảng danh sách sổ | Đã đăng nhập, truy cập màn hình danh sách sổ | Quan sát cuối mỗi dòng trong bảng | Mỗi dòng có icon 3 chấm (more options) ở cuối dòng |
| TC_003 | Kiểm tra hiển thị bảng danh sách sổ | Đã đăng nhập, truy cập màn hình danh sách sổ | Quan sát thứ tự sắp xếp các dòng | Danh sách sắp xếp theo ngày tạo giảm dần (mới nhất đầu tiên) |

**Key rules**:
- Description & Precondition are **identical** across rows in the same group (the xlsx will merge cells).
- Each step is a **concrete action** (observe, tap, scroll, enter...), NOT a verification statement.
- Each expected result is **clear, self-explanatory** — no confusing references like "(BR16)" without context.
- Do NOT combine multiple verifications into 1 step/expected pair.

## 4. Negative Test Coverage (MANDATORY)

- For EACH positive test case, always consider the corresponding negative scenario.
- Example: Positive "Đăng nhập thành công" => Negative: wrong password, empty email, invalid email format, locked account...
- Negative coverage is **mandatory**, not optional — a feature missing negative cases has not met coverage.

## 5. Expected Result Rules

- Do NOT write obvious/redundant expected results:
  - "App không bị crash" — WRONG
  - "Không giật/lag" — WRONG
  - "Không lỗi" — WRONG
  - "App mở thành công" — WRONG
  - "Hệ thống hoạt động bình thường" — WRONG
- Only write expected results with **real test value**: describe concretely how the UI changes, what notification/message appears, where and to what value the data updates, which screen it navigates to, how the element state changes (enabled/disabled, visible/hidden).
- Do NOT check colors/hex codes in the expected result (e.g. "Header có màu nền #F2F3F4" — WRONG). Checking color codes has no test value, it belongs to pixel-perfect review (designer/dev verify it themselves).
- Do NOT use confusing context-free references (e.g. "Sắp xếp theo BR16" — WRONG). Write it clearly: "Sắp xếp theo ngày tạo giảm dần".
- GOOD:
  ```
  - Hiển thị message "Đăng nhập thành công"
  - Điều hướng sang màn hình Trang chủ
  - Avatar người dùng hiển thị ở góc trên phải header
  ```

---

## 6. Test Coverage

### 6.1 Coverage Types
- Includes: **Positive, Negative, Boundary, Edge case**.
- Group test cases by scenario/section.
- Assign priority: **Critical / High / Medium / Low**.
- **Test Type** column: leave blank (user fills it when needed).
- **isAuto** column: leave blank, do NOT auto-fill.

### 6.2 Four-Part Coverage Framework (when both Figma + PRD are present)

When writing TCs with both a Figma design and a PRD/specs, use the 4-part framework to ensure full coverage. This is a **section-splitting guide**, NOT a hard requirement to have exactly 4 parts — you may merge/split depending on the feature.

**Part 1 — UI Display Condition Checks**: when elements show/hide, conditional rendering by role/permission, loading/skeleton state, initial state, responsive (if any).

**Part 2 — UI Object / Data Type Checks**: elements match Figma (layout, spacing, typography), data type of each input field, field constraints (length, format, required/optional), placeholder, tooltip, icon.

**Part 3 — Data Display Checks**: fetch & render data correctly, format (date, number, currency), empty/no-data state, sorting/filtering/pagination, accuracy per business rule.

**Part 4 — Interaction & Validation Checks**: every element clickable/tappable, form submit & error handling, validation rules from the PRD, edge/boundary, business logic workflow, error/success message, API integration point (if any).

> The framework is a coverage-assurance tool — NOT a rigid template. A simple feature may not need all 4 parts.

> **Do NOT create TCs verifying color codes** (hex, RGB...): no test value, wastes execution time, belongs to pixel-perfect review.

### 6.3 Conflict Resolution: Specs vs Figma

When you detect a conflict between Specs/PRD and the Figma design:

- **`/cook`, `/plan-tests`**: **STOP**, show the list of conflicts, ask the user how to handle (follow Docs / follow Figma / pick each one). Do NOT decide on your own.
- **`/analyze`** (read-only): record the conflict in the output, clearly state what the Specs say, what the Figma shows, propose a resolution — no need to stop and ask.
- **Default fallback** (when there's only 1 source or you can't ask): prioritize **Specs/PRD** for business logic/validation/flow; prioritize **Figma** for UI/UX layout/visual/interaction.
- **Mark in output**: add a note in the Precondition — `[Resolved: Theo Figma]` / `[Resolved: Theo Docs]` / `[Resolved: Thỏa hiệp]` / `[Conflict: Specs vs Figma]`.
- **Exception**: a purely visual conflict (color, font size, spacing) not mentioned in the Specs => prioritize Figma, no need to ask.

### 6.4 Priority Assignment Guidelines

| Priority | When to use | Example |
|----------|------------|---------|
| **Critical** | Core functionality, blocks the whole feature, security | Login, payment, data loss |
| **High** | Main functionality, large UX impact | CRUD, main validation, navigation |
| **Medium** | Secondary feature, has a workaround | Filter, sort, display formatting |
| **Low** | Minor UI, nice-to-have | Tooltip, hover effect, animation |

---

## 7. Quality Checklist (self-check before output)

- [ ] Does each TC have a complete precondition?
- [ ] Are steps detailed enough, with concrete test data, and actions (not verifications)?
- [ ] NO obvious expected results ("app doesn't crash"...)?
- [ ] Covered Positive + Negative + Boundary + Edge?
- [ ] Multi-result format correct (description/precondition merged, 1 step = 1 expected)?
- [ ] NO TC checking color codes/hex?
- [ ] Vietnamese content WITH diacritics (unless the user requests English)?
- [ ] TC_ID reset per sheet (each sheet restarts from TC_001)?
- [ ] Priority assigned reasonably? Section grouping logical and clear?
