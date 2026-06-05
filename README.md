# QA Claude Plugins

🌐 **Tiếng Việt** · [English](README-en.md)

> **Bộ plugin Claude Code mã nguồn mở cho mọi kỹ sư QA/QC dùng AI.** Tự động hoá kiểm thử web & mobile, sinh test case từ tài liệu, exploratory testing, review code - biến Claude Code thành một "QA engineer" thực thụ ngay trong terminal/IDE của bạn.

Miễn phí & mở cho **tất cả mọi người**, cài một lần, dùng cho mọi project có Claude. Mọi command gọi dạng **`/qa:<tên>`** (ví dụ `/qa:exploratory`).

## Mục lục

- [Tính năng](#tính-năng)
- [Cài đặt](#cài-đặt)
- [Cập nhật](#cập-nhật)
- [Danh sách command](#danh-sách-command)
  - [Dùng chung](#dùng-chung)
  - [Automation](#automation)
  - [Manual QA](#manual-qa)
- [Cách hoạt động](#cách-hoạt-động)
- [Tích hợp tuỳ chọn](#tích-hợp-tuỳ-chọn)
- [Đóng góp](#đóng-góp)

## Tính năng

- **Automation đa nền tảng** - Web (Playwright) + App (Appium iOS/Android): khám phá săn bug, viết Page Object + test, chạy & phân loại lỗi, fix đúng layer, review → push → tạo PR/MR.
- **Manual QA** - phân tích spec/PRD, lập kế hoạch test case, sinh test case ra **xlsx / Google / Lark Sheet**, log bug lên **Lark Bitable**.
- **Tự rẽ nền tảng** (web / android / ios) → chỉ đọc đúng skill nền tảng → không tốn token thừa.
- **Tích hợp tuỳ chọn** - thông báo kết quả (Lark / Slack / Teams / Telegram) & chia sẻ report (Cloudflare R2 / S3), dùng tài khoản của **chính bạn**, bật-tắt tự do.
- **Cross-platform** - Windows + macOS.

## Cài đặt

```bash
/plugin marketplace add hominhtuong/qa-claude-plugins
/plugin install qa@qa-claude
```

Hoặc khai báo sẵn trong project (ai clone về cũng được hỏi cài) - `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "qa-claude": { "source": { "source": "github", "repo": "hominhtuong/qa-claude-plugins" } }
  },
  "enabledPlugins": { "qa@qa-claude": true }
}
```

> Bạn vẫn có thể thêm command riêng vào `.claude/commands/` của project (gọi **không prefix**, vd `/mycmd`) - chạy song song, độc lập với command plugin (`/qa:…`).

## Cập nhật

Khi có bản mới:

```text
/plugin marketplace update qa-claude
/reload-plugins
```

Chạy `/qa:setup-plugin --update` để làm mới các file `.example`/template trong `.claude/qa-claude/` (file `.env` và `log-bug.config.yml` của bạn **không bị ghi đè**).

## MCP servers (tự động khi bật plugin)

Plugin **tự đính kèm** các MCP server cần cho automation — bật plugin là có, **không cần cấu hình `.mcp.json` thủ công**:

| Server | Dùng cho | Cấu hình |
|---|---|---|
| **figma** | đọc design (exploratory, design-conformance) | sẵn (http) — chỉ cần đăng nhập Figma khi được hỏi |
| **playwright** | driver web | sẵn (`npx @playwright/mcp`) |
| **appium** | driver iOS/Android (port 4723) | sẵn (`npx appium-mcp`) — vẫn cần chạy Appium server qua `start-appium.sh` |
| **Lark** | đọc doc/Bitable | ❌ **không** qua MCP — dùng Python `lark_read.py` đọc `.plugin.env` (dual-mode tenant/user, tránh lỗi token). Ai muốn MCP thì tự thêm `@larksuiteoapi/lark-mcp` vào `.mcp.json` project (xem [lark-mcp-guide](plugins/qa/rules/lark-mcp-guide.md)). |

> Nếu project của bạn **đã có** figma/appium/playwright MCP riêng → bản của bạn được ưu tiên; plugin tự nhận đúng tool qua ToolSearch, không xung đột.

## Danh sách command

> **Cách gọi**: tất cả command của plugin gọi dạng **`/qa:<tên>`** (ví dụ `/qa:exploratory`). Đây là quy ước namespace bắt buộc của Claude Code cho plugin - không bỏ được. Những mục `*-method` / `*-app` / `*-web`… hiện trong menu là **skill nội bộ**, bạn **không cần gọi trực tiếp** - cứ gọi command.

### Dùng chung

| Command | Việc |
|---|---|
| `/qa:setup-plugin` | **Cài plugin vào project** (1 lần): Claude tự chạy script tạo `.claude/qa-claude/` + check toolchain. Không cần terminal. |
| `/qa:help [chủ đề]` | Giới thiệu & hướng dẫn dùng plugin, liệt kê command/skill. |
| `/qa:status` | Tóm tắt nhanh trạng thái project (git, device, Appium, coverage). |
| `/qa:ask <câu hỏi>` | Hỏi đáp về codebase / kiến trúc / cấu hình / cách test (chỉ trả lời). |
| `/qa:missing-test-ids` | Quản lý "nợ test-id" gửi dev (export / record / resolve). |
| `/qa:feedback <góp ý/lỗi>` | Góp ý / báo lỗi plugin → mở sẵn 1 GitHub issue (kèm version/OS), bấm Submit là xong. |

### Automation

| Command | Việc |
|---|---|
| `/qa:exploratory <feature> [platform] [--spec <file\|url\|figma>]` | Khám phá **toàn bộ** màn hình như QA senior, **săn bug đến cùng** — gặp bug **không dừng**, ghi nhận + triage rồi đi tiếp đến hết feature; đối chiếu **spec/Figma** nếu có → bug *spec-mismatch*; chụp bằng chứng. **Xong mới kết luận (GATE):** có `[APP-BUG]` → xuất **bug report** gửi dev (🚦 không viết test cho phần app sai); **sạch** → khai báo elements/Screen → sẵn cho `/qa:plan-tests`. |
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

### Kết quả (output)

Mọi output gom về thư mục **`results/`** trong project:

| Loại | Vị trí |
|---|---|
| Exploratory (phân tích spec + figma-tracking + bug report + screenshot) | `results/<feature-name>/` (register chung: `results/bug-summary.md`) |
| Mỗi lần chạy test (HTML report + screenshot/video) | `results/tests/<ddMMMyyyy>/…` |
| Test case (xlsx) + analysis + html testcase report | `results/<feature-name>/` |

`results/tests/` (artifact mỗi lần chạy) được tự thêm vào `.gitignore` khi chạy `setup`.

## Cách hoạt động

Command automation có **Bước 0: chốt nền tảng** (lấy từ đối số `web|android|ios`, không có thì tự nhận diện project, nhập nhằng thì hỏi) rồi **chỉ đọc đúng 1 skill** cho nền tảng đó → tiết kiệm token, không chạy nhầm runtime:

| Việc | web | android | ios |
|---|---|---|---|
| Điều hướng | `navigate-web` | `navigate-app` | `navigate-app` |
| Trích locator | `find-elements-web` | `find-elements-android` | `find-elements-ios` |
| Viết code | `cook-web` | `cook-app` | `cook-app` |
| Chạy suite | `run-web` | `run-app` | `run-app` |

## Tích hợp tuỳ chọn

> **Mặc định không cần cấu hình gì** - report luôn được sinh trong project (local). Thông báo (Lark/Slack/…) và upload report (R2/S3) là tuỳ chọn, bật-tắt riêng.

Mỗi user dùng **tài khoản của chính mình**. Toàn bộ config plugin nằm gọn trong `<project>/.claude/qa-claude/` (tách riêng, **không đụng `./.env` của app**):

**Cài 1 lần / project** - chỉ cần gõ:

```text
/qa:setup-plugin
```

Claude tự chạy script (tự nhận macOS/Windows), tạo `.claude/qa-claude/`, vá `.gitignore`, kiểm tra toolchain (tự cài `wrangler` nếu có `npm`; thiếu gì thì chỉ lệnh cài đúng theo OS). Bạn **không cần mở terminal**. Sau đó mở `.claude/qa-claude/.env` để bật tính năng cần dùng (và `log-bug.config.yml` cho `/qa:log-bug`).

### Chọn kênh (mỗi nhóm tối đa 1)

| Nhu cầu | Mặc định | Kênh A | Kênh B |
|---|---|---|---|
| **Xem report** | ✅ HTML local | - | - |
| **Thông báo** | tóm tắt trong phiên Claude | **Lark** (`ENABLE_LARK_NOTIFY` + `LARK_*`) | **Webhook** Slack/Teams/Telegram/Discord (`ENABLE_NOTIFY_WEBHOOK` + `NOTIFY_*`) |
| **Chia sẻ report URL** | mở file local | **Cloudflare R2** (`ENABLE_CF_PUSH` + `CF_*`, cần `wrangler`) | **S3** AWS/MinIO/… (`ENABLE_S3_PUSH` + `S3_*`/`AWS_*`, cần `aws` CLI) |

Lark: group → Settings → Bots → **Custom Bot** → copy webhook. R2: Cloudflare → API Tokens → **R2 Token (Edit)**. S3: để trống `S3_ENDPOINT` cho AWS, điền endpoint cho MinIO/khác. Bật kênh nào điền cụm key đó.

### Log bug lên Lark

`/qa:log-bug` đọc `.claude/qa-claude/log-bug.config.yml` (board id, mapping Dev PIC → user id, options, defaults). Điền board của bạn vào đó (hoặc dùng `/qa:update-board <url>`). Chỉ chấm **Priority** (AI tự đánh giá nếu bạn không điền); board production gắn `read_only: true` để chặn log nhầm.


## Đóng góp

Mã nguồn mở - chào mừng đóng góp. Quy ước mở rộng plugin (cấu trúc, đặt tên skill/command, ràng buộc kỹ thuật) xem [CONTRIBUTING.md](CONTRIBUTING.md).

**Góp ý / báo lỗi**: dùng ngay trong lúc xài - gõ **`/qa:feedback <mô tả>`**, plugin mở sẵn 1 GitHub issue (đã điền version + OS) để bạn bấm Submit.
