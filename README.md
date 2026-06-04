# qa-claude-plugins

> **Bộ plugin Claude Code mã nguồn mở cho mọi kỹ sư QA/QC dùng AI.** Tự động hoá kiểm thử web & mobile, sinh test case từ tài liệu, exploratory testing, review code — biến Claude Code thành một "QA engineer" thực thụ ngay trong terminal/IDE của bạn.

Miễn phí & mở cho **tất cả mọi người**. Cài một lần, dùng cho mọi project có Claude. Mọi command gọi dạng **`/qa:<tên>`** (ví dụ `/qa:exploratory`).

## Mục lục

- [Tính năng](#tính-năng)
- [Cài đặt](#cài-đặt)
- [Danh sách command](#danh-sách-command)
  - [Automation](#automation)
  - [Manual QA](#manual-qa)
  - [Dùng chung](#dùng-chung)
- [Cách hoạt động](#cách-hoạt-động)
- [Tích hợp tuỳ chọn](#tích-hợp-tuỳ-chọn)
- [Cập nhật](#cập-nhật)
- [Đóng góp](#đóng-góp)

## Tính năng

- **Automation đa nền tảng** — Web (Playwright) + App (Appium iOS/Android): khám phá săn bug, viết Page Object + test, chạy & phân loại lỗi, fix đúng layer, review → push → tạo PR/MR.
- **Manual QA** — phân tích spec/PRD, lập kế hoạch test case, sinh test case ra **xlsx / Google / Lark Sheet**, log bug lên **Lark Bitable**.
- **Tự rẽ nền tảng** (web / android / ios) → chỉ đọc đúng skill nền tảng → không tốn token thừa.
- **Tích hợp tuỳ chọn** — thông báo kết quả (Lark / Slack / Teams / Telegram) & chia sẻ report (Cloudflare R2 / S3), dùng tài khoản của **chính bạn**, bật-tắt tự do.
- **Cross-platform** — Windows + macOS.

## Cài đặt

```bash
/plugin marketplace add hominhtuong/qa-claude-plugins
/plugin install qa@qa-claude
```

Hoặc khai báo sẵn trong project (ai clone về cũng được hỏi cài) — `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "qa-claude": { "source": { "source": "github", "repo": "hominhtuong/qa-claude-plugins" } }
  },
  "enabledPlugins": { "qa@qa-claude": true }
}
```

> Bạn vẫn có thể thêm command riêng vào `.claude/commands/` của project (gọi **không prefix**, vd `/mycmd`) — chạy song song, độc lập với command plugin (`/qa:…`).

## Danh sách command

> **Cách gọi**: tất cả command của plugin gọi dạng **`/qa:<tên>`** (ví dụ `/qa:exploratory`). Đây là quy ước namespace bắt buộc của Claude Code cho plugin — không bỏ được. Những mục `*-method` / `*-app` / `*-web`… hiện trong menu là **skill nội bộ**, bạn **không cần gọi trực tiếp** — cứ gọi command.

### Automation

| Command | Việc |
|---|---|
| `/qa:exploratory <feature> [platform]` | Khám phá màn hình như QA senior, **săn bug**, chụp bằng chứng, xuất bug report gửi dev. 🚦 Có `[APP-BUG]` → dừng, không viết test cho app sai. |
| `/qa:plan-tests <feature>` | Thiết kế kế hoạch test automation (chỉ khi exploratory sạch). |
| `/qa:find-elements <màn>` | Trích locator bền vững (tự rẽ web/android/ios). |
| `/qa:cook <plan\|yêu cầu>` | Viết Page Object + test code theo design pattern. |
| `/qa:run [platform]` | Compile + chạy test + **phân loại lỗi** (`[APP-BUG]` vs `[FRAMEWORK]`/`[ENV]`/`[DATA]`). |
| `/qa:fix <bug>` | Sửa lỗi (compile/test fail, flaky, vi phạm rule) **đúng layer**. |
| `/qa:analyze <code\|kết quả>` | Phân tích codebase / kết quả test / cấu trúc (chỉ đọc, không sửa). |
| `/qa:count-cases <feature>` | Đếm testcase automation (`@Test`) hiện có + ước lượng tổng theo sub-feature. |
| `/qa:review-change` | Soi git diff hiện tại theo design system & coding rules. |
| `/qa:review-codebase` | Soi **toàn bộ** codebase theo rule + nhất quán cross-file. |
| `/qa:push-code` | Review → tự fix Blocker → build xanh → commit & push branch. |
| `/qa:merge-request` | Review → merge target an toàn → push → mở PR/MR (tự nhận GitHub `gh` / GitLab `glab`). |
| `/qa:kill-appium` | Tắt mọi Appium server đang chạy. |

### Manual QA

| Command | Việc |
|---|---|
| `/qa:analyze-spec <spec>` | Phân tích tài liệu/PRD theo góc QA (testable, mơ hồ, rủi ro, câu hỏi cho PO) → file md. |
| `/qa:plan-gen-testcases <feature>` | Lập kế hoạch test case nhiều phase (scope, màn, TC_ID range). |
| `/qa:gen-testcases <plan>` | Sinh test case ra **xlsx / Google / Lark Sheet** (tiếng Việt có dấu). |
| `/qa:count-testcases <file\|sheet>` | Đếm test case trong sheet/plan + báo coverage theo section. |
| `/qa:log-bug <mô tả>` | Log bug lên Lark Bitable (kèm ảnh/video, chấm Priority). |
| `/qa:update-board <url\|alias>` | Thêm/đổi board Lark active + cập nhật mapping. |

### Dùng chung

| Command | Việc |
|---|---|
| `/qa:help [chủ đề]` | Giới thiệu & hướng dẫn dùng plugin, liệt kê command/skill. |
| `/qa:status` | Tóm tắt nhanh trạng thái project (git, device, Appium, coverage). |
| `/qa:ask <câu hỏi>` | Hỏi đáp về codebase / kiến trúc / cấu hình / cách test (chỉ trả lời). |
| `/qa:missing-test-ids` | Quản lý "nợ test-id" gửi dev (export / record / resolve). |

> **Automation và Manual dùng tên riêng**, không nhập nhằng: `cook` (viết code) ↔ `gen-testcases` (sinh test case) · `plan-tests` ↔ `plan-gen-testcases` · `analyze` ↔ `analyze-spec` · `count-cases` ↔ `count-testcases`.

## Cách hoạt động

Command automation có **Bước 0: chốt nền tảng** (lấy từ đối số `web|android|ios`, không có thì tự nhận diện project, nhập nhằng thì hỏi) rồi **chỉ đọc đúng 1 skill** cho nền tảng đó → tiết kiệm token, không chạy nhầm runtime:

| Việc | web | android | ios |
|---|---|---|---|
| Điều hướng | `navigate-web` | `navigate-app` | `navigate-app` |
| Trích locator | `find-elements-web` | `find-elements-android` | `find-elements-ios` |
| Viết code | `cook-web` | `cook-app` | `cook-app` |
| Chạy suite | `run-web` | `run-app` | `run-app` |

## Tích hợp tuỳ chọn

> **Mặc định không cần cấu hình gì** — report luôn được sinh trong project (local). Thông báo (Lark/Slack/…) và upload report (R2/S3) là tuỳ chọn, bật-tắt riêng.

Mỗi user dùng **tài khoản của chính mình**. Toàn bộ config plugin nằm gọn trong `<project>/.claude/qa-claude/` (tách riêng, **không đụng `./.env` của app**):

| File | Vai trò | Khi `setup` chạy lại |
|---|---|---|
| `.env` | 🔒 secret (1 file chia section: Lark/R2/S3/notify) | giữ nguyên (của bạn) |
| `log-bug.config.yml` | 🧩 board Lark + mapping dev/field | giữ nguyên (của bạn) |
| `.env.example` · `log-bug.config.example.yml` | bản tham chiếu schema mới nhất | làm mới |
| `testcase-template.md` | 📄 format test case | làm mới |

**Cài 1 lần / project** — chạy skill `setup` (hoặc bảo Claude *"chạy skill setup"*):

```bash
# macOS/Linux
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/setup.py
# Windows
python  %CLAUDE_PLUGIN_ROOT%\scripts\setup.py
```

Script tự tạo `.claude/qa-claude/`, vá `.gitignore`, chạy **doctor** kiểm tra toolchain (tự cài `wrangler` nếu có `npm`; thiếu công cụ thì in lệnh cài đúng theo OS). Sau đó mở `.claude/qa-claude/.env` để bật tính năng cần dùng.

### Chọn kênh (mỗi nhóm tối đa 1)

| Nhu cầu | Mặc định | Kênh A | Kênh B |
|---|---|---|---|
| **Xem report** | ✅ HTML local | — | — |
| **Thông báo** | tóm tắt trong phiên Claude | **Lark** (`ENABLE_LARK_NOTIFY` + `LARK_*`) | **Webhook** Slack/Teams/Telegram/Discord (`ENABLE_NOTIFY_WEBHOOK` + `NOTIFY_*`) |
| **Chia sẻ report URL** | mở file local | **Cloudflare R2** (`ENABLE_CF_PUSH` + `CF_*`, cần `wrangler`) | **S3** AWS/MinIO/… (`ENABLE_S3_PUSH` + `S3_*`/`AWS_*`, cần `aws` CLI) |

Lark: group → Settings → Bots → **Custom Bot** → copy webhook. R2: Cloudflare → API Tokens → **R2 Token (Edit)**. S3: để trống `S3_ENDPOINT` cho AWS, điền endpoint cho MinIO/khác. Bật kênh nào điền cụm key đó.

### Log bug lên Lark

`/qa:log-bug` đọc `.claude/qa-claude/log-bug.config.yml` (board id, mapping Dev PIC → user id, options, defaults). Điền board của bạn vào đó (hoặc dùng `/qa:update-board <url>`). Chỉ chấm **Priority** (AI tự đánh giá nếu bạn không điền); board production gắn `read_only: true` để chặn log nhầm.

## Cập nhật

Khi có bản mới:

```text
/plugin marketplace update qa-claude
/reload-plugins
```

Chạy lại skill `setup` để làm mới các file `.example`/template trong `.claude/qa-claude/` (file `.env` và `log-bug.config.yml` của bạn **không bị ghi đè**).

## Đóng góp

Mã nguồn mở — chào mừng đóng góp. Quy ước mở rộng plugin (cấu trúc, đặt tên skill/command, ràng buộc kỹ thuật) xem [CONTRIBUTING.md](CONTRIBUTING.md).
