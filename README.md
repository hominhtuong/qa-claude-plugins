# qa-claude-plugins

> **Bộ plugin Claude Code mã nguồn mở cho mọi kỹ sư QA/QC dùng AI.** Tự động hoá kiểm thử web & mobile, sinh test case từ tài liệu, exploratory testing, review code — biến Claude Code thành một "QA engineer" thực thụ ngay trong terminal/IDE của bạn.

Miễn phí & mở cho **tất cả mọi người**. Cài một lần, dùng cho mọi project có Claude — mọi command gọi **trực tiếp, không prefix**, không xung đột với cấu hình sẵn có của project.

---

## ✨ Tính năng

- **Automation đa nền tảng** — Web (Playwright) + App (Appium iOS/Android): khám phá săn bug, viết Page Object + test, chạy & phân loại lỗi, fix đúng layer, review → push → tạo PR/MR.
- **Manual QA** — phân tích spec/PRD, lập kế hoạch test case, sinh test case ra **xlsx / Google / Lark Sheet**, log bug lên **Lark Bitable**.
- **Tự rẽ nền tảng** (web / android / ios) → chỉ đọc đúng skill nền tảng → không tốn token thừa.
- **Tích hợp tuỳ chọn** — thông báo kết quả (Lark / Slack / Teams / Telegram) & chia sẻ report (Cloudflare R2 / S3), dùng tài khoản của **chính bạn**, bật-tắt tự do.
- **Cross-platform** — Windows + macOS.

---

## 🚀 Cài đặt

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

> Project có command/skill **local** cùng tên sẽ **thắng** plugin → bạn tuỳ biến được mà không cần sửa plugin.

---

## 🧭 Command (gọi trực tiếp, không prefix)

### Automation

| Command | Việc |
|---|---|
| `/exploratory <feature> [platform]` | Khám phá như QA senior, **săn bug**, chụp bằng chứng, xuất bug report gửi dev. 🚦 Có `[APP-BUG]` → dừng, không viết test cho app sai. |
| `/plan-tests <feature>` | Thiết kế kế hoạch test (chỉ khi exploratory sạch). |
| `/find-elements <màn>` | Trích locator bền vững (web/android/ios). |
| `/cook <plan\|yêu cầu>` | Viết Page Object + test code. |
| `/run [platform]` | Compile + chạy + **phân loại lỗi** (`[APP-BUG]` vs `[FRAMEWORK]`/`[ENV]`/`[DATA]`). |
| `/fix <bug>` | Sửa **đúng layer**, không sửa test để né lỗi app. |
| `/review-change` · `/review-codebase` | Soi rule trước khi push. |
| `/push-code` · `/merge-request` | Push + tạo PR/MR (tự nhận GitHub `gh` / GitLab `glab` từ remote). |

### Manual QA

| Command | Việc |
|---|---|
| `/analyze-spec <spec>` | Phân tích tài liệu/PRD theo góc QA (testable, rủi ro, câu hỏi cho PO). |
| `/plan-gen-testcases <feature>` | Lập kế hoạch test case nhiều phase. |
| `/gen-testcases <plan>` | Sinh test case ra **xlsx / Google / Lark Sheet** (tiếng Việt có dấu). |
| `/log-bug <mô tả>` | Log bug lên Lark Bitable (kèm ảnh/video). |
| `/update-board <url\|alias>` | Thêm/đổi board Lark + cập nhật mapping. |

### Dùng chung
`/help` · `/status` · `/ask` · `/missing-test-ids` · `/count-cases` (đếm `@Test`) · `/count-testcases` (đếm TC trong sheet) · `/kill-appium`.

> **Automation và Manual dùng tên riêng**, không nhập nhằng: `/cook` (viết code) ↔ `/gen-testcases` (sinh test case) · `/plan-tests` ↔ `/plan-gen-testcases` · `/analyze` ↔ `/analyze-spec` · `/count-cases` ↔ `/count-testcases`.

---

## ⚙️ Cách hoạt động — platform router

Command automation có **Bước 0: chốt nền tảng** (lấy từ đối số `web|android|ios`, không có thì tự nhận diện project, nhập nhằng thì hỏi) rồi **chỉ đọc đúng 1 skill** cho nền tảng đó → tiết kiệm token, không chạy nhầm runtime:

| Việc | web | android | ios |
|---|---|---|---|
| Điều hướng | `navigate-web` | `navigate-app` | `navigate-app` |
| Trích locator | `find-elements-web` | `find-elements-android` | `find-elements-ios` |
| Viết code | `cook-web` | `cook-app` | `cook-app` |
| Chạy suite | `run-web` | `run-app` | `run-app` |

---

## 🔌 Tích hợp tuỳ chọn — Lark notify & report upload

> **Mặc định không cần cấu hình gì** — report luôn được sinh trong project (local). Thông báo (Lark/Slack/…) và upload report (R2/S3) là tuỳ chọn, bật-tắt riêng. Không bật → mọi thứ chạy bình thường.

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

Script tự tạo `.claude/qa-claude/`, vá `.gitignore`, và chạy **doctor** kiểm tra toolchain (tự cài `wrangler` nếu có `npm`; thiếu công cụ thì in lệnh cài đúng theo OS). Sau đó mở `.claude/qa-claude/.env` để bật tính năng cần dùng.

### Chọn kênh (mỗi nhóm tối đa 1)

| Nhu cầu | Mặc định | Kênh A | Kênh B |
|---|---|---|---|
| **Xem report** | ✅ HTML local | — | — |
| **Thông báo** | tóm tắt trong phiên Claude | **Lark** (`ENABLE_LARK_NOTIFY` + `LARK_*`) | **Webhook** Slack/Teams/Telegram/Discord (`ENABLE_NOTIFY_WEBHOOK` + `NOTIFY_*`) |
| **Chia sẻ report URL** | mở file local | **Cloudflare R2** (`ENABLE_CF_PUSH` + `CF_*`, cần `wrangler`) | **S3** AWS/MinIO/… (`ENABLE_S3_PUSH` + `S3_*`/`AWS_*`, cần `aws` CLI) |

Lark: group → Settings → Bots → **Custom Bot** → copy webhook. R2: Cloudflare → API Tokens → **R2 Token (Edit)**. S3: để trống `S3_ENDPOINT` cho AWS, điền endpoint cho MinIO/khác. Bật kênh nào điền cụm key đó.

### Log bug lên Lark

`/log-bug` đọc `.claude/qa-claude/log-bug.config.yml` (board id, mapping Dev PIC → user id, options, defaults). Điền board của bạn vào đó (hoặc dùng `/update-board <url>`). Chỉ chấm **Priority** (AI tự đánh giá nếu bạn không điền); board production gắn `read_only: true` để chặn log nhầm.

---

## 🔄 Cập nhật

Khi có bản mới:

```text
/plugin marketplace update qa-claude
/reload-plugins
```

Chạy lại skill `setup` để làm mới các file `.example`/template trong `.claude/qa-claude/` (file `.env` và `log-bug.config.yml` của bạn **không bị ghi đè**).

---

## 🤝 Đóng góp

Mã nguồn mở — chào mừng đóng góp. Quy ước mở rộng plugin (cấu trúc, đặt tên skill/command, ràng buộc kỹ thuật) xem [CONTRIBUTING.md](CONTRIBUTING.md).
