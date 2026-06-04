# qa-claude-plugins

> **Bộ plugin Claude Code mã nguồn mở cho mọi kỹ sư QA/QC dùng AI.** Tự động hoá kiểm thử web & mobile, sinh test case từ tài liệu, exploratory testing, review code — biến Claude Code thành một "QA engineer" thực thụ ngay trong terminal/IDE của bạn.

Miễn phí & mở cho **tất cả mọi người**. Cài một lần, dùng cho mọi project có sử dụng Claude, không xung đột với cấu hình sẵn có của project.

- **Marketplace**: `qa-claude` · **1 plugin duy nhất**: `qa`.
- **Mọi command gọi TRỰC TIẾP, không prefix**: `/cook`, `/run`, `/fix`, `/merge-request`, `/log-bug`, `/status`…
- **2 router thông minh**: command **tự rẽ chế độ** (automation ⟷ manual) và **tự rẽ nền tảng** (web / android / ios) → chỉ đọc đúng skill cần → không tốn token thừa.
- **Tích hợp tuỳ chọn**: thông báo kết quả (Lark / Slack / Teams / Telegram) & chia sẻ report (Cloudflare R2 / S3) — dùng tài khoản của chính bạn, bật-tắt tự do.

---

## 1. Vì sao là plugin (không phải submodule / npm)

| | Submodule | npm/library | **Plugin marketplace** ✅ |
|---|---|---|---|
| Sửa 1 nơi → all update | `git submodule update` từng repo | postinstall copy file | `/plugin marketplace update qa-claude` |
| Không xung đột project | ❌ đổ thẳng vào `.claude` | ❌ | ✅ command/skill **local thắng** plugin trùng tên |
| Gọi command | — | — | ✅ **trực tiếp** `/cook` (không prefix) |
| Claude load native | ✓ | ❌ không load skill từ `node_modules` | ✅ |

---

## 2. Kiến trúc — 2 router (điểm cốt lõi)

Một command như `/cook` phục vụ **nhiều thế giới**: viết code automation (Web Playwright / App Appium iOS+Android) HOẶC sinh test case thủ công. Mỗi nhánh đọc/viết khác nhau. Nếu nhồi hết vào 1 skill → Claude đọc thừa → **tốn token, nhiễu**.

**Giải pháp**: skill **tách nhỏ**, command là **router** — Bước 0 chốt hướng đi, sau đó chỉ đọc **đúng 1 skill**.

### Router 1 — chế độ (`detect-mode`): automation ⟷ manual
4 command "đa năng" (`cook`, `plan-tests`, `analyze`, `count-cases`) tự nhận diện:

```
/cook <plan|yêu cầu> [--auto|--manual]
        │
        ▼  Bước 0 — skill detect-mode (cờ? → repo có test framework? → nội dung? → hỏi)
   ┌────┴───────────────────┐
automation                manual
(viết code test)          (sinh test case → xlsx/Sheet)
 → detect-platform         → gen-testcases / tc-template
```

### Router 2 — nền tảng (`detect-platform`): web / android / ios
Nhánh automation chốt tiếp nền tảng → chỉ đọc 1 skill:

| Việc | web | android | ios |
|---|---|---|---|
| Điều hướng | `navigate-web` | `navigate-app` | `navigate-app` |
| Trích locator | `find-elements-web` | `find-elements-android` | `find-elements-ios` |
| Viết code | `cook-web` | `cook-app` | `cook-app` |
| Chạy suite | `run-web` | `run-app` | `run-app` |
| Rule design/coding | `rules/web/*` | `rules/app/*` | `rules/app/*` |

Bản đồ định tuyến đầy đủ: [`plugins/qa/rules/platform-detect.md`](plugins/qa/rules/platform-detect.md). Skill **agnostic** (đọc bất kể mode/platform): `detect-mode`, `detect-platform`, `exploratory-method`, `plan-method`, `fix-by-layer`, `review-audit`, `design-conformance`, `update-sitemap`.

---

## 3. Cấu trúc repo

```
qa-claude-plugins/
├── .claude-plugin/marketplace.json          # catalog (1 plugin: qa)
└── plugins/qa/                               # plugin DUY NHẤT — mọi command gọi trực tiếp
    ├── .claude-plugin/plugin.json
    ├── commands/  cook · plan-tests · analyze · count-cases   (đa năng — tự rẽ mode)
    │              exploratory · find-elements · run · fix · review-change ·
    │              review-codebase · push-code · merge-request · kill-appium ·
    │              log-bug · help · status · ask · missing-test-ids
    ├── skills/    detect-mode · detect-platform │ find-elements-{web,android,ios} │
    │              navigate-{web,app} │ cook-{web,app} │ run-{web,app} │
    │              exploratory-method · plan-method · fix-by-layer · review-audit ·
    │              design-conformance · declare-screen · update-sitemap │
    │              gen-testcases · plan-testcases · tc-template · log-bug │
    │              commit-push · build-verify · missing-ids · help-info │ setup · doctor
    ├── scripts/   setup · doctor · lark_notify · notify_webhook · push_report · push_s3 · _env · _upload  (python3, cross-platform)
    ├── templates/ .env.example  (config Lark/R2/S3 — copy sang ./.env trong project)
    ├── rules/     platform-detect · failure-triage · exploratory-bug-report-template ·
    │              lark-mcp-guide · git-conventions · test-quality · severity-priority · output-format │
    │              web/{design-pattern,coding-rules,design-system,review-checklist} │
    │              app/{design-pattern,coding-rules,design-system,design-system-figma,review-checklist,troubleshooting}
    └── agents/    source-inspector · figma-reader · lark-reader
```

**Nguyên tắc**: chỉ 1 plugin → mọi file đọc qua `${CLAUDE_PLUGIN_ROOT}/...` (per-plugin), gọi skill khác **theo tên** (vd `commit-push`, `gen-testcases`) — Claude tự resolve trong plugin.

---

## 4. Command catalog & luồng làm việc (gọi trực tiếp, không prefix)

### Automation (luồng chuẩn)
1. **`/exploratory <feature> [platform]`** — khám phá như QA senior, **săn bug**, chụp bằng chứng → `reports/exploratory/<feature>/`, xuất **bug report gửi dev**. 🚦 **GATE**: có `[APP-BUG]` → báo dev, **dừng** (không viết test cho app sai).
2. **`/plan-tests <feature>`** — thiết kế plan test (chỉ khi exploratory sạch).
3. **`/find-elements <màn>`** — trích locator bền vững (router 3 nền tảng).
4. **`/cook <plan|yêu cầu>`** — viết Page Object + test (web→`cook-web`, app→`cook-app`).
5. **`/run [platform]`** — compile + chạy + **triage fail** (`[APP-BUG]` vs `[FRAMEWORK]`/`[ENV]`/`[DATA]`).
6. **`/fix <bug>`** — sửa **đúng layer**, không sửa test để né `[APP-BUG]`.
7. **`/review-change`** · **`/review-codebase`** → **`/push-code`** → **`/merge-request`** (tự nhận GitHub `gh` / GitLab `glab` từ remote).

### Manual QA (test case thủ công)
`/analyze <spec>` → `/plan-tests <feature>` → `/cook <plan>` (sinh test case ra **Sheet/xlsx**, tiếng Việt có dấu, chuẩn `test-quality`) → `/log-bug <mô tả>` (Lark Bitable).

### Dùng chung
`/help` · `/status` · `/ask` · `/missing-test-ids` · `/count-cases` · `/kill-appium`.

> **4 command đa năng** (`cook`, `plan-tests`, `analyze`, `count-cases`) **tự nhận diện** automation hay manual theo cờ `--auto`/`--manual`, loại repo, và nội dung yêu cầu. Nhập nhằng → nó hỏi 1 lần.

---

## 5. Cài & bật cho mỗi project

```bash
# Cài marketplace + plugin (1 lần/máy)
/plugin marketplace add hominhtuong/qa-claude-plugins      # hoặc git URL GitLab/self-host
/plugin install qa@qa-claude
```

Hoặc commit vào project (ai clone cũng được hỏi cài) — `.claude/settings.json`:
```json
{
  "extraKnownMarketplaces": {
    "qa-claude": { "source": { "source": "github", "repo": "hominhtuong/qa-claude-plugins" } }
  },
  "enabledPlugins": { "qa@qa-claude": true }
}
```

**Override trong project**: gõ `/cook` → nếu project có command **local** cùng tên thì bản local **thắng** plugin. Project có thể đặt skill cùng tên trong `.claude/skills/` để **đè** skill plugin — tuỳ biến mà không sửa plugin.

---

## 5b. Lark notify & report upload — **đều TÙY CHỌN**

> **Mặc định: không cần cấu hình gì.** Report luôn được sinh **trong local project** (`reports/…` cho app · `results/reports/…` cho web). Thông báo (Lark/Slack/…) và upload report (R2/S3) là **tính năng độc lập, bật-tắt riêng**. Không bật → `/run` vẫn chạy bình thường, bỏ qua êm.

**Mỗi user dùng tài khoản của CHÍNH MÌNH** — toàn bộ webhook/secret/key do user tự điền vào `./.env` của project (git-ignored). Plugin **không chứa** và **không dùng chung** account của ai.

### Cài 1 lần / project (tạo `.env` + check toolchain)

Chạy skill `setup` (hoặc bảo Claude *"chạy skill setup"*):

```bash
# macOS/Linux
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/setup.py
# Windows
python  %CLAUDE_PLUGIN_ROOT%\scripts\setup.py
```

Script tự: tạo `./.env` từ template · vá `.gitignore` · chạy **doctor** (in lệnh cài thiếu theo OS, tự cài `wrangler` nếu có npm). Sau đó mở `./.env` bật tính năng cần dùng.

### Phương án (mỗi nhóm chọn tối đa 1 kênh)

| Nhu cầu | Mặc định (zero-config) | Kênh A | Kênh B (thay thế) |
| --- | --- | --- | --- |
| **Xem report** | ✅ HTML ngay trong local project | — | — |
| **Thông báo kết quả** | tóm tắt ngay trong phiên Claude | **Lark** (`ENABLE_LARK_NOTIFY` + `LARK_*`, không cần cài gì) | **Generic webhook** Slack/Teams/Telegram/Discord (`ENABLE_NOTIFY_WEBHOOK` + `NOTIFY_*`) |
| **Chia sẻ report qua URL** | mở file local / gửi tay | **Cloudflare R2** (`ENABLE_CF_PUSH` + `CF_*`, cần `wrangler`) | **S3-compatible** AWS/CMC/MinIO (`ENABLE_S3_PUSH` + `S3_*`/`AWS_*`, cần `aws` CLI) |

Lark: group → Settings → Bots → **Custom Bot** → copy webhook (+ secret nếu bật sign). Generic webhook: `NOTIFY_PROVIDER=slack\|discord\|teams\|generic` + `NOTIFY_WEBHOOK_URL`, hoặc `telegram` + `NOTIFY_TELEGRAM_TOKEN`/`NOTIFY_TELEGRAM_CHAT_ID`. R2: token Cloudflare → My Profile → API Tokens → **R2 Token** (Edit). S3: để trống `S3_ENDPOINT` cho AWS thật, điền endpoint cho CMC/MinIO. Chọn kênh nào điền cụm key đó; kênh không dùng để `ENABLE_*=false`.

> **Secret sống trong project** (`./.env`, git-ignored) — TUYỆT ĐỐI không vào repo plugin. Script là python3 thuần (Lark) + `wrangler`/`aws` cho upload; không cần pip.

---

## 6. Update một nơi → mọi project

1. Sửa file trong `plugins/qa/...`, **bump `version`** trong `plugin.json` + `marketplace.json`, commit & push.
2. Mỗi máy: `/plugin marketplace update qa-claude` → `/reload-plugins` (hoặc mở session mới).

---

## 7. Luật bất biến khi mở rộng (nói AI tuân thủ)

1. **1 plugin duy nhất (`qa`)** — mọi command gọi trực tiếp, không prefix. Đừng tạo plugin trùng tên command với nhau (sẽ buộc prefix lại).
2. **`${CLAUDE_PLUGIN_ROOT}` là per-plugin** — file một command/skill *đọc* phải cùng plugin; gọi skill khác **theo tên** (vd `commit-push`, `gen-testcases`). **Không** dùng `.claude/rules|skills|agents/` trong file plugin.
3. **Command đa năng** (`cook`/`plan-tests`/`analyze`/`count-cases`) luôn có **Bước 0 `detect-mode`** → 2 nhánh `# Mode: automation` / `# Mode: manual`. Nhánh automation có thêm **`detect-platform`** → chỉ đọc skill/rule đúng nền tảng (web `rules/web/*` · app `rules/app/*`).
4. Command frontmatter giữ format (`description`, `argument-hint`, `allowed-tools`). Skill = thư mục `<name>/SKILL.md`, frontmatter `name` (== tên thư mục) + `description`. **Description bằng tiếng Anh** (AI trigger nhanh hơn); nội dung output tiếng Việt thì ghi rõ trong instruction.
5. Sau khi sửa: `python3 -m json.tool` mọi JSON; `grep -rn '\.claude/\(rules\|skills\|agents\)/' plugins/` phải rỗng; tên skill tham chiếu phải tồn tại; tên skill `name:` == tên thư mục.

### Backlog gợi ý
- Package Java ví dụ dùng placeholder `com.example.*`; project thật nên đặt base package của mình (cấu hình trong CLAUDE.md) — rule chỉ minh hoạ cấu trúc `screens/tests/utils/base`.
- Thêm nền tảng Flutter integration_test (Dart) như nhánh thứ 4 của platform router nếu chuyển từ Appium sang `appium_flutter_server`.
