# Failure Triage — Phân định "lỗi APP" vs "lỗi FRAMEWORK" (BẮT BUỘC)

> **Bối cảnh dự án**: **SBH Flutter là app MỚI**, viết lại theo logic **SBH Reactive** bằng Flutter — **KHÔNG phải app chuẩn (golden)**. App có thể đang lỗi/chưa hoàn thiện. Vì vậy mục tiêu của exploratory + chạy test **không phải** giả định app đúng, mà là **phát hiện tính năng nào đang lỗi**, và phân định **rạch ròi** nguyên nhân.
>
> Quy tắc này áp dụng cho mọi command/skill có thể gặp failure: `exploratory`, `run`/`run-tests`, `fix`/`fix-by-layer`, `plan`, `cook`, `review-*`. Mọi FAIL / element-not-found **MUST** được phân loại theo taxonomy dưới đây, KHÔNG để FAIL "trôi" mà không gán nhãn.

---

## 1. Taxonomy nguyên nhân gốc (gán cho mọi FAIL)

| Nhãn | Nghĩa | Ví dụ điển hình | Hành động |
|------|-------|-----------------|-----------|
| `[APP-BUG]` | **Lỗi ứng dụng** — app hành xử sai so với kỳ vọng (logic SBH Reactive / spec). | Crash, exception hiện trên màn (vd `SqliteException(2067)`), data sai, tính năng thiếu/"coming soon", validation không chặn, điều hướng sai, nút bấm không phản hồi. | **KHÔNG sửa test cho pass.** Ghi nhận **Defect** → report dev. Test giữ nguyên kỳ vọng đúng (đỏ = lỗi thật) hoặc mark known-defect kèm ticket. |
| `[FRAMEWORK]` | **Lỗi dự án/automation** — app ĐÚNG nhưng test sai: locator sai/stale, bắt element sai strategy, thiếu wait, sai màn giả định, assertion kỳ vọng sai. | Element có thật (page source xác nhận) nhưng query nhầm; làm tay thì OK nhưng test đỏ. | **Sửa** qua skill `fix-by-layer` (Screen locator / Test / wait). KHÔNG đụng app. |
| `[ENV]` | **Môi trường** — device/emulator, Appium server, quyền, mạng. | `adb` mất device, Appium down, popup quyền chặn, Appium port. | Sửa env/preflight; không đụng app/test logic. |
| `[DATA]` | **Dữ liệu/precondition** — account test thiếu data để cover (list rỗng…). | List Nhập/Xuất kho rỗng → không có item để mở chi tiết. | Seed data / chỉnh precondition; không kết luận app/test sai. |
| `[NEEDS-TRIAGE]` | **Chưa phân định** — chưa đủ bằng chứng. | Mới thấy đỏ, chưa kiểm tra lại trên app thật. | **Bắt buộc** kiểm chứng lại (MCP/làm tay) rồi đổi sang nhãn ở trên. KHÔNG để nguyên. |

> Nhãn nguyên nhân **độc lập** với mức độ nghiêm trọng (Critical/Warning/Info). Một FAIL luôn có **1 nhãn nguyên nhân** + **1 mức độ**.

---

## 2. Thủ tục phân định (App-bug hay Framework-bug?)

**Nguyên tắc vàng: tái hiện trên APP THẬT trước khi kết luận.** (qua Appium MCP — skill `mcp-navigate` — hoặc thao tác tay.)

```
FAIL / element-not-found
   │
   ├─ Tái hiện thủ công trên app thật (MCP/tay)
   │
   ├─ Tính năng làm tay CHẠY ĐÚNG?
   │     ├─ CÓ  → lỗi KHÔNG ở app:
   │     │        ├─ element có trong page_source nhưng test bắt sai → [FRAMEWORK] (locator/strategy/wait)
   │     │        ├─ thiếu data/precondition                         → [DATA]
   │     │        └─ device/Appium/quyền/mạng                        → [ENV]
   │     └─ KHÔNG (làm tay cũng sai/crash/thiếu) → [APP-BUG]
   │
   └─ Element-not-found đặc thù:
         ├─ page_source KHÔNG có element (thật sự vắng / "coming soon" / màn khác) → [APP-BUG] (tính năng thiếu/đổi) 
         └─ page_source CÓ element, chỉ là locator/strategy ta sai             → [FRAMEWORK]
```

**Bằng chứng bắt buộc kèm theo nhãn:**
- `[APP-BUG]`: screenshot hành vi sai + bước tái hiện + kỳ vọng (theo SBH Reactive/spec) vs thực tế.
- `[FRAMEWORK]`: trích đoạn page source chứng minh element/hành vi đúng + locator sai đang dùng.
- `[ENV]`/`[DATA]`: mô tả điều kiện thiếu.

> Lưu ý cạm bẫy hay gặp (xem [troubleshooting.md](troubleshooting.md)): MCP `find_element` strategy `id` đôi khi không match resource-id trần của Flutter → **đó là quirk của TOOL MCP, KHÔNG phải app-bug và cũng không phải framework-bug của runtime** (vì `@MobileFindBy(id=...)` runtime match đúng). Đừng nhầm thành lỗi app.

---

## 3. Cách báo cáo — phân định rõ trong CẢ HAI report

### 3a. Exploratory report (`reports/exploratory/<group>/report.md`)
Tách **2 mục riêng**, không trộn:
- **🐛 App defects (`[APP-BUG]`)** — bảng: `# | Màn | Kỳ vọng | Thực tế | Mức độ | Bằng chứng (screenshot) | Bước tái hiện`.
- **🧰 Framework / locator issues (`[FRAMEWORK]`/`[ENV]`/`[DATA]`)** — bảng: `# | Vấn đề | Nguyên nhân | Cách xử lý`.
- Bảng quan sát tổng có thêm **cột "Triage"** mang đúng 1 nhãn cho mỗi dòng FAIL/⚠️.

### 3b. HTML run report (ExtentReports, mỗi lần `/run`)
- Quy ước **bắt buộc**: message của `Utils.failCap/infoCap` **mở đầu bằng nhãn** để hiện inline trong HTML:
  ```java
  Utils.failCap(driver, node, "[APP-BUG] Tab 'Đã phát hành' crash SqliteException(2067) khi load");
  Utils.failCap(driver, node, "[FRAMEWORK] btn_filter_status đổi locator — cần cập nhật Screen");
  Utils.infoCap(driver, node, "[DATA] List nhập kho rỗng — skip mở chi tiết");
  ```
- Khi tóm tắt kết quả `/run`: nhóm các FAIL theo nhãn (bao nhiêu APP-BUG vs FRAMEWORK vs ENV/DATA) → người đọc biết ngay "app lỗi" hay "test lỗi".

### 3c. HTML test-case report (`report-template.html` → `docs/<module>-testcase-report.html`)
- Dùng cột/legend **Result/Triage** (`Pass` · `App-bug` · `Framework` · `Env/Data` · `Needs-triage`) + mục **Defect summary** liệt kê `[APP-BUG]` để chuyển dev.

---

## 4. Hệ quả khi build test (BẮT BUỘC nhớ)

- **KHÔNG che lỗi app để "cho xanh".** Không nới assertion, không `try/catch` nuốt lỗi, không `Thread.sleep` để né một app-bug. Nếu app sai → test phải phản ánh sai đó (đỏ thật hoặc known-defect có ticket), không làm cho pass giả.
- **Test đỏ ≠ luôn phải sửa test.** Trước khi `fix`, phân định: đỏ vì `[FRAMEWORK]` (sửa test) hay vì `[APP-BUG]` (báo dev, giữ test trung thực).
- Mỗi `[APP-BUG]` phát hiện trong `/cook` hoặc `/run` → ghi vào report tương ứng + nêu trong phần tổng kết để QA chuyển dev.
