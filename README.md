# QA Claude Plugins

🌐 **Tiếng Việt** · [English](README-en.md)

> **Bộ plugin Claude Code mã nguồn mở cho kỹ sư QA/QC, QA Manager và Product Ops dùng AI.** Tự động hoá kiểm thử web & mobile, sinh test case từ tài liệu, exploratory testing, review code - và tổng hợp tất cả thành dashboard chất lượng, cổng Go/No-Go release, ma trận truy vết và release notes. Biến Claude Code thành "QA engineer" *và* "quản lý chất lượng" thực thụ ngay trong terminal/IDE của bạn.

Miễn phí & mở cho **tất cả mọi người**, cài một lần, dùng cho mọi project có Claude. Mọi command gọi dạng **`/qa:<tên>`** (ví dụ `/qa:exploratory`).

## Mục lục

- [Tính năng](#tính-năng)
- [Cài đặt](#cài-đặt)
- [Workflow bắt đầu nhanh](#workflow-bắt-đầu-nhanh--từ-0-đến-project-đầu-tiên)
- [Cập nhật](#cập-nhật)
- [Danh sách command](#danh-sách-command)
  - [Dùng chung](#dùng-chung)
  - [Automation](#automation)
  - [Manual QA](#manual-qa)
  - [Quản lý chất lượng & báo cáo](#quản-lý-chất-lượng--báo-cáo-qa-manager--product-ops)
- [Cách hoạt động](#cách-hoạt-động)
- [Tích hợp tuỳ chọn](#tích-hợp-tuỳ-chọn)
- [Đóng góp](#đóng-góp)

## Tính năng

- **Automation đa nền tảng** - Web (Playwright) + App (Appium iOS/Android): khám phá săn bug, viết Page Object + test, chạy & phân loại lỗi, fix đúng layer, review → push → tạo PR/MR.
- **Manual QA** - phân tích spec/PRD, lập kế hoạch test case, sinh test case ra **xlsx / Google / Lark Sheet**, log bug lên **Lark Bitable**.
- **Quản lý chất lượng & báo cáo** (QA Manager / Product Ops) - gom bug board + kết quả test thành **dashboard metrics**, **cổng Go/No-Go release** có thể audit, **ma trận truy vết yêu cầu**, và **release notes** (changelog nội bộ + bản cho người dùng). Chỉ đọc.
- **Tự rẽ nền tảng** (web / android / ios) → chỉ đọc đúng skill nền tảng → không tốn token thừa.
- **Tích hợp tuỳ chọn** - thông báo kết quả (Lark / Slack / Teams / Telegram) & chia sẻ report (Cloudflare R2 / S3), dùng tài khoản của **chính bạn**, bật-tắt tự do.
- **Cross-platform** - Windows + macOS.

## Cài đặt

```bash
/plugin marketplace add hominhtuong/qa-claude-plugins
/plugin install qa@qa-claude
/reload-plugins
/qa:setup        # ← chạy ngay sau khi cài: tạo .claude/qa-claude/ + kiểm tra toolchain
```

> **Sau khi cài (hoặc reload) plugin, chạy `/qa:setup` một lần cho mỗi project.** Lệnh này tạo `.claude/qa-claude/` (config + `.plugin.env`), vá `.gitignore`, kiểm tra toolchain — không cần terminal. Sau đó mở `.claude/qa-claude/.plugin.env` để bật những gì cần. Chi tiết ở [Tích hợp tuỳ chọn](#tích-hợp-tuỳ-chọn).

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

## Workflow bắt đầu nhanh — từ 0 đến project đầu tiên

Mới dùng? Đây là toàn bộ lộ trình, theo thứ tự. Bạn chỉ **gõ lệnh trong Claude Code** — không cần terminal, không cần biết framework.

1. **Mở project trong VS Code**, cài Claude Code, cài plugin này (2 dòng `/plugin …` ở trên) rồi `/reload-plugins`.
2. **Tạo khung dự án test** — `/qa:scaffold`. Chọn **app** hay **web**; lệnh sinh sẵn bộ khung Page Object Model chuẩn (thư mục, `pom.xml`, `Makefile`, suites, 1 test *login* mẫu) đã biên dịch được. *Giờ bạn đã có 1 project thật — nhìn cấu trúc là hiểu để gì ở đâu.*
3. **Cấu hình plugin** — `/qa:setup` (tạo `.claude/qa-claude/`, kiểm tra toolchain).
4. **Điền tài khoản** — mở `.env`, nhập tài khoản test (và URL app/web nếu được hỏi).
5. **Chạy thử ví dụ** — `/qa:run` (hoặc `make smoke`): **1 browser/phiên app mở lên**, chạy case login từ đầu đến cuối rồi **đóng lại và xuất HTML report** trong `results/`.
6. **Thêm feature của bạn** — `/qa:plan-tests <feature>` → `/qa:cook` → `/qa:run`. Lặp lại theo từng feature. (Thích viết test case thủ công thay vì code? `/qa:analyze-spec` → `/qa:plan-gen-testcases` → `/qa:gen-testcases`.)
7. **Săn bug / log bug** — `/qa:exploratory <feature>` tìm bug; `/qa:log-bug` ghi lên board.

> Tóm lại: **scaffold → setup → điền `.env` → run → plan-tests/cook.** Vài case là có 1 project test chạy được. Dành cho team lead: xem [Quản lý chất lượng & báo cáo](#quản-lý-chất-lượng--báo-cáo-qa-manager--product-ops).

## Cập nhật

Khi có bản mới:

```text
/plugin marketplace update qa-claude
/reload-plugins
```

Chạy `/qa:setup --update` để làm mới các file `.example`/template trong `.claude/qa-claude/` (file `.env` và `log-bug.config.yml` của bạn **không bị ghi đè**).

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
| `/qa:scaffold [--app\|--web]` | **Tạo project automation chuẩn** từ đầu (khung POM: thư mục + pom/Makefile/suites/configs + 1 test login mẫu biên dịch được). Chạy 1 lần trên repo trống; sau đó chỉ cần `/qa:plan-tests`. Không ghi đè code có sẵn. |
| `/qa:setup` | **Cài plugin vào project** (1 lần): Claude tự chạy script tạo `.claude/qa-claude/` + check toolchain. Không cần terminal. |
| `/qa:help [chủ đề]` | Giới thiệu & hướng dẫn dùng plugin, liệt kê command/skill. |
| `/qa:status` | Tóm tắt nhanh trạng thái project (git, device, Appium, coverage). |
| `/qa:ask <câu hỏi>` | Hỏi đáp về codebase / kiến trúc / cấu hình / cách test (chỉ trả lời). |
| `/qa:missing-test-ids` | Quản lý "nợ test-id" gửi dev (export / record / resolve). |
| `/qa:feedback <góp ý/lỗi>` | Góp ý / báo lỗi plugin → mở sẵn 1 GitHub issue (kèm version/OS), bấm Submit là xong. |

### Automation

| Command | Việc |
|---|---|
| `/qa:sitemap [feature] [platform]` | **Khám phá & dựng sitemap**: đi hết app/web (hoặc chỉ 1 feature, ví dụ `/qa:sitemap home`), khai báo **element của từng màn** (tên + locator bền vững) và cập nhật bản đồ điều hướng vào thư mục `sitemap/`. **Chỉ map — KHÔNG viết test, KHÔNG bắt bug, KHÔNG sinh Page Object.** Chạy lại sẽ *bổ sung* (merge theo tên element), không tạo trùng. |
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
| `/qa:est-sp <plan\|feature>` | Ước lượng **Story Point** cho effort QC (viết TC + chạy + retest), điều chỉnh theo role (`USER_ROLE`); xuất bảng SP, cập nhật plan ở chế độ plan. |
| `/qa:explain-bug <Bug ID\|text\|link>` | "Dịch" bug lủng củng thành nội dung rõ ràng (repro/actual/expected + kiểm tra Severity/Priority hợp lý); đọc record + comment qua Bug ID hoặc link Lark đầy đủ. |
| `/qa:check-duplicate-bug <mô tả>` | Kiểm tra bug trùng trên board **trước khi** log (search keyword, loại bug đã đóng + false positive) — chỉ trả quyết định, không tạo record. |
| `/qa:log-bug <mô tả>` | Log bug lên Lark Bitable (kèm ảnh/video, chấm Priority). |
| `/qa:update-board <url\|alias>` | Thêm/đổi board Lark active + cập nhật mapping. |
| `/qa:auth-lark` | Xác thực Lark app + dò scope/read-mode mà app có (chạy 1 lần trước các lệnh đọc doc/board Lark). |

### Quản lý chất lượng & báo cáo (QA Manager / Product Ops)

> **Chỉ đọc (read-only)** — các lệnh này tổng hợp artifact mà QA đã tạo (`results/` + Lark bug board) thành tài liệu ra-quyết-định cho lead/manager/product ops. Không bao giờ tạo/sửa bug hay test.

| Command | Việc |
|---|---|
| `/qa:quality-report [from..to\|tag]` | **Dashboard QA** cho manager: pass rate + xu hướng, bug open theo priority kèm aging, defect density / module hot-spot, xu hướng created-vs-resolved, coverage theo feature → `results/quality-report/` (md, tuỳ chọn HTML/notify). |
| `/qa:bug-analysis <url board> [range]` | **Phân tích sâu** board bất kỳ theo range: tự phân loại tên status riêng của board thành nhóm chưa-sẵn-sàng-test / sẵn sàng / đã đóng, rồi bóc tách backlog chưa sẵn sàng theo nhóm/type/feature/priority + **nguyên nhân gốc** + **ngày bug đột biến** + aging → `results/bug-analysis/`. |
| `/qa:release-gate <release>` | Phán quyết **Go / No-Go** theo checklist có thể audit (`release-gate.config.yml`): hard gate → NO-GO, soft gate → CONDITIONAL (ship kèm sign-off). Xuất verdict + bảng từng gate + blocker + ô sign-off. |
| `/qa:traceability <feature\|all>` | **Ma trận truy vết yêu cầu (RTM)**: nối từng requirement (từ `/qa:analyze-spec`) → test case → bug, gắn cờ Gap / No-test / Partial / Covered. Khép vòng spec↔test↔bug. |
| `/qa:release-notes <release>` | **Release notes cho 2 đối tượng**: bản changelog kỹ thuật nội bộ (gom theo Conventional Commit + bảng bug đã fix) + bản cho người dùng (ngôn ngữ thường, theo lợi ích) từ git history + bug đã fix. |
| `/qa:risk <feature\|release>` | **Đánh giá rủi ro**: Risk Matrix (Likelihood × Impact, 1–25) phân loại Low/Medium/High/Critical, kèm mitigation (prevention/detection/response/owner) cho mỗi rủi ro Medium+ và test strategy theo rủi ro. |
| `/qa:triage <danh sách bug>` | **Triage bug**: phân loại Severity + Type, chấm **RICE** để xếp thứ tự xử lý khách quan, suy ra SLA deadline + regression scope, xuất action plan. Đọc từ sheet/file/list hoặc board. |
| `/qa:sla <dữ liệu ticket>` | Báo cáo **SLA compliance**: compliance rate (tổng + theo priority), MTTR-Response/Resolution kèm P50/P90/P95, phân tích breach, xu hướng, hiệu suất assignee. |
| `/qa:postmortem <sự cố>` | **Postmortem blameless**: timeline + nguyên nhân gốc (5 Whys + yếu tố kỹ thuật/quy trình) + impact + action item (Prevent/Detect/Mitigate, owner theo role, due). Ground timeline từ record liên quan trên board. |

> Framework dùng chung: [product-ops.md](plugins/qa/rules/product-ops.md) (SLA / health / release gate / RICE / risk matrix), [severity-priority-framework.md](plugins/qa/rules/severity-priority-framework.md), [story-point.md](plugins/qa/rules/story-point.md).

### Kết quả (output)

Mọi output gom về thư mục **`results/`** trong project:

| Loại | Vị trí |
|---|---|
| Exploratory (phân tích spec + figma-tracking + bug report + screenshot) | `results/<feature-name>/` (register chung: `results/bug-summary.md`) |
| Mỗi lần chạy test (HTML report + screenshot/video) | `results/tests/<ddMMMyyyy>/…` |
| Test case (xlsx) + analysis + html testcase report | `results/<feature-name>/` |
| Report quản lý & ops (dashboard / release gate / traceability / release notes / risk / triage / SLA / bug analysis) | `results/quality-report/`, `results/release-gate/<release>/`, `results/release-notes/<release>/`, `results/bug-analysis/`, `results/<context>/` (risk/triage/sla/traceability) |

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
/qa:setup
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
