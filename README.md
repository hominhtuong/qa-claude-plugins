# qa-claude-plugins

> **Bộ plugin Claude Code mã nguồn mở cho mọi kỹ sư QA/QC dùng AI.** Tự động hoá kiểm thử web & mobile, sinh test case từ tài liệu, exploratory testing, review code — biến Claude Code thành một "QA engineer" thực thụ ngay trong terminal/IDE của bạn.

Miễn phí & mở cho **bất kỳ ai** — không gắn với công ty hay framework cụ thể nào. Cài một lần, dùng cho mọi project; **sửa 1 nơi → mọi project update theo**, không copy `.claude/` thủ công, không xung đột với cấu hình sẵn có của project.

- **Marketplace**: `qa-claude`.
- **3 plugin**: `core` (dùng chung) · `auto` (automation đa nền tảng Web+App) · `qa-manual` (sinh test case thủ công).
- **Triết lý lõi**: command **tự rẽ nền tảng** (web / android / ios) rồi **chỉ đọc skill đúng nền tảng** → không tốn token thừa.
- **Tích hợp tuỳ chọn**: thông báo kết quả (Lark / Slack / Teams / Telegram) & chia sẻ report (Cloudflare R2 / S3) — dùng tài khoản của chính bạn, bật-tắt tự do.

---

## 1. Vì sao là plugin (không phải submodule / npm)

| | Submodule | npm/library | **Plugin marketplace** ✅ |
|---|---|---|---|
| Sửa 1 nơi → all update | `git submodule update` từng repo | postinstall copy file | `/plugin marketplace update qa-claude` |
| Không xung đột project | ❌ đổ thẳng vào `.claude` | ❌ | ✅ **namespaced** `/auto:cook` |
| Project override được | khó | khó | ✅ command/skill **local thắng** plugin trùng tên |
| Claude load native | ✓ | ❌ không load skill từ `node_modules` | ✅ |

---

## 2. Kiến trúc — router theo nền tảng (điểm cốt lõi)

Dự án automation chạy **nhiều nền tảng**: **Web** (Playwright Java), **App iOS + Android** (Appium Java). Mỗi nền tảng tìm element / viết code / chạy test **khác nhau**. Nếu nhồi hết vào 1 skill → Claude đọc cả phần Android lẫn iOS lẫn Web cho mọi việc → **tốn token, nhiễu**.

**Giải pháp**: skill **tách nhỏ theo nền tảng**, command là **router** — Bước 0 chốt nền tảng, sau đó chỉ đọc **đúng 1 skill**:

```
/find-elements <màn> [web|android|ios]
        │
        ▼  Bước 0 — skill detect-platform (đối số? → auto-detect dự án? → hỏi)
   ┌────┴─────────────┬──────────────────┐
  web              android               ios
   │                  │                   │
find-elements-web  find-elements-android  find-elements-ios   ← chỉ đọc 1 skill
(getByRole>testid) (id>accessibility>     (accessibility>
                    uiautomator>xpath)     -ios predicate>class chain)
```

Mọi command `auto` theo đúng khuôn này (`/exploratory`, `/cook`, `/run`, `/fix`, …). Bản đồ định tuyến đầy đủ: [`plugins/auto/rules/platform-detect.md`](plugins/auto/rules/platform-detect.md).

| Việc | web | android | ios |
|---|---|---|---|
| Điều hướng | `navigate-web` | `navigate-app` | `navigate-app` |
| Trích locator | `find-elements-web` | `find-elements-android` | `find-elements-ios` |
| Viết code | `cook-web` | `cook-app` | `cook-app` |
| Chạy suite | `run-web` | `run-app` | `run-app` |
| Rule design/coding | `rules/web/*` | `rules/app/*` | `rules/app/*` |

Skill **không phụ thuộc nền tảng** (đọc bất kể platform): `detect-platform`, `exploratory-method`, `plan-method`, `fix-by-layer`, `review-audit` (platform-aware theo từng file), `design-conformance`, `update-sitemap`.

---

## 3. Cấu trúc repo

```
qa-claude-plugins/
├── .claude-plugin/marketplace.json          # catalog 3 plugin
└── plugins/
    ├── core/                                 # domain-agnostic, dùng chung
    │   ├── commands/  help · status · ask · missing-test-ids
    │   ├── skills/    help-info · commit-push · build-verify · missing-ids
    │   └── rules/     git-conventions
    │
    ├── auto/                                 # automation Web + App (router theo nền tảng)
    │   ├── commands/  find-elements · exploratory · plan-tests · cook · run · fix ·
    │   │              review-change · review-codebase · push-code · merge-request ·
    │   │              analyze · count-cases · kill-appium
    │   ├── skills/    detect-platform │ find-elements-{web,android,ios} │
    │   │              navigate-{web,app} │ cook-{web,app} │ run-{web,app} │
    │   │              exploratory-method · plan-method · fix-by-layer · review-audit ·
    │   │              design-conformance · declare-screen · update-sitemap · setup · doctor
    │   ├── scripts/   setup · doctor · lark_notify · notify_webhook · push_report · push_s3 · _env · _upload  (python3, cross-platform)
    │   ├── templates/ .env.example  (config Lark/R2 — copy sang ./.env trong project)
    │   ├── rules/     platform-detect · failure-triage · exploratory-bug-report-template ·
    │   │              lark-mcp-guide │ web/{design-pattern,coding-rules,design-system,review-checklist} │
    │   │              app/{design-pattern,coding-rules,design-system,design-system-figma,review-checklist,troubleshooting}
    │   └── agents/    source-inspector · figma-reader · lark-reader
    │
    └── qa-manual/                            # QA thủ công: test case → Sheet/xlsx
        ├── commands/  cook · plan-tests · analyze · log-bug · count-cases
        ├── skills/    gen-testcases · plan-testcases · tc-template · log-bug
        └── rules/     test-quality · severity-priority · output-format
```

**Nguyên tắc phân tầng**: file mà 1 command/skill **đọc** phải nằm **cùng plugin** (`${CLAUDE_PLUGIN_ROOT}` là per-plugin). Gọi **skill plugin khác** (vd `commit-push`/`build-verify` của `core`) thì **gọi theo tên** — Claude resolve theo plugin đang bật.

---

## 4. Command catalog & luồng làm việc

### `auto` — automation (luồng chuẩn)
1. **`/auto:exploratory <feature> [platform]`** — khám phá như QA senior, **săn bug**, chụp bằng chứng → `reports/exploratory/<feature>/`, xuất **bug report gửi dev**. 🚦 **GATE**: có `[APP-BUG]` → báo dev, **dừng** (không viết test cho app sai).
2. **`/auto:plan-tests <feature>`** — thiết kế plan test (chỉ khi exploratory sạch).
3. **`/auto:find-elements <màn>`** — trích locator bền vững (router 3 nền tảng).
4. **`/auto:cook <plan|yêu cầu>`** — viết Page Object + test (web→`cook-web`, app→`cook-app`).
5. **`/auto:run [platform]`** — compile + chạy + **triage fail** (`[APP-BUG]` vs `[FRAMEWORK]`/`[ENV]`/`[DATA]`).
6. **`/auto:fix <bug>`** — sửa **đúng layer**, không sửa test để né `[APP-BUG]`.
7. **`/auto:review-change`** · **`/auto:review-codebase`** → **`/auto:push-code`** → **`/auto:merge-request`**.

### `qa-manual` — test case thủ công
`/qa-manual:analyze <spec>` → `/qa-manual:plan-tests <feature>` → `/qa-manual:cook <plan>` (sinh test case ra **Sheet/xlsx**, tiếng Việt có dấu, chuẩn `test-quality`) → `/qa-manual:log-bug <mô tả>` (Lark Bitable).

### `core` — dùng chung
`/help` (giới thiệu + hướng dẫn — skill `help-info`) · `/status` · `/ask` · `/missing-test-ids` (quản lý nợ test-id gửi dev).

> **Lệnh trùng tên** (`cook`, `plan-tests` có ở cả `auto` và `qa-manual`) → **luôn gõ namespaced**: `/auto:cook` (viết code) vs `/qa-manual:cook` (sinh test case).

---

## 5. Cài & bật cho mỗi project

```bash
# Cài marketplace (1 lần/máy)
/plugin marketplace add hominhtuong/qa-claude-plugins      # hoặc git URL GitLab/self-host
/plugin install core@qa-claude
/plugin install auto@qa-claude            # project automation (web/app)
/plugin install qa-manual@qa-claude       # project QA tài liệu
```

Hoặc commit vào project (ai clone cũng được hỏi cài) — `.claude/settings.json`:
```json
{
  "extraKnownMarketplaces": {
    "qa-claude": { "source": { "source": "github", "repo": "hominhtuong/qa-claude-plugins" } }
  },
  "enabledPlugins": { "core@qa-claude": true, "auto@qa-claude": true }
}
```

**Override trong project**: gõ trần `/cook` → command **local** của project (nếu có) **thắng** plugin. Muốn bản plugin → gõ namespaced `/auto:cook`, hoặc xoá command local trùng để hết drift. Project có thể đặt skill cùng tên trong `.claude/skills/` để **đè** skill plugin.

---

## 5b. Lark notify & Cloudflare R2 push — **đều TÙY CHỌN**

> **Mặc định: không cần cấu hình gì.** Report luôn được sinh **trong local project** (`reports/…` cho app · `results/reports/…` cho web). Lark và R2 là **2 tính năng độc lập, bật-tắt riêng** — chỉ để **thông báo** (Lark) và **chia sẻ report qua URL** (R2). Không bật → `/auto:run` vẫn chạy bình thường, bỏ qua êm.

**Mỗi user dùng tài khoản của CHÍNH MÌNH** — toàn bộ webhook/secret/key do user tự điền vào `./.env` của project (git-ignored). Plugin **không chứa** và **không dùng chung** account của ai.

### Cài 1 lần / project (tạo `.env` + check toolchain)

Chạy skill `setup` (hoặc bảo Claude *"chạy skill setup của auto"*):

```bash
# macOS/Linux
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/setup.py
# Windows
python  %CLAUDE_PLUGIN_ROOT%\scripts\setup.py
```

Script tự: tạo `./.env` từ template · vá `.gitignore` · chạy **doctor** (in lệnh cài thiếu theo OS, tự cài `wrangler` nếu có npm). Sau đó mở `./.env` bật tính năng cần dùng:

### Tùy chọn A — Lark notify (card kết quả vào group Lark)

Bật `ENABLE_LARK_NOTIFY=true` rồi điền **cụm `LARK_*`** (lấy từ Custom Bot của group anh):

```ini
ENABLE_LARK_NOTIFY=true
LARK_WEBHOOK_URL=https://open.larksuite.com/open-apis/bot/v2/hook/<của-bạn>
LARK_WEBHOOK_SECRET=<sign secret của bot, để trống nếu bot không bật sign>
LARK_PLATFORM=Tên hiển thị trên card     # vd "MyApp - Android"
LARK_USER=Tên người/đội trigger
```

Yêu cầu thêm: **không có** (script Lark dùng python stdlib thuần). Lấy webhook: group Lark → Settings → Bots → **Custom Bot** → copy webhook (+ secret nếu bật "Signature verification").

### Tùy chọn B — Cloudflare R2 push (upload report lên cloud, share bằng URL)

Bật `ENABLE_CF_PUSH=true` rồi điền **cụm `CF_*`** (R2 của tài khoản Cloudflare của anh):

```ini
ENABLE_CF_PUSH=true
CF_ACCOUNT_ID=<account id Cloudflare>
CF_API_TOKEN=<API token quyền R2 Edit>
CF_R2_BUCKET=<tên bucket>
CF_R2_DOMAIN=https://<custom domain của bucket>   # optional: để build URL public
CF_R2_PREFIX=auto                                 # optional: thư mục con trong bucket
```

Yêu cầu thêm: **`wrangler` CLI** (`npm install -g wrangler` — skill `setup`/`doctor` tự cài nếu có npm). Tạo token: Cloudflare → My Profile → API Tokens → **R2 Token** (Edit).

> Hai cụm hoàn toàn độc lập: bật A không cần B và ngược lại.

### Ai lo tầng nào

| Tầng | Ai lo | Ghi chú |
| --- | --- | --- |
| Toolchain (python/node/java/mvn/wrangler) | skill `doctor` | detect + in lệnh cài theo OS; tự cài được mỗi `wrangler` |
| Util code (Lark/R2) | `scripts/*.py` trong plugin | stdlib thuần (Lark) + `wrangler` (R2); không cần pip |
| Secret/config | `./.env` trong **project** | account của **chính user**, git-ignored, không bao giờ vào repo plugin |

### Phương án thay thế (mỗi nhóm chọn tối đa 1 kênh)

| Nhu cầu | Mặc định (zero-config) | Kênh A | Kênh B (thay thế) |
| --- | --- | --- | --- |
| **Xem report** | ✅ HTML ngay trong local project | — | — |
| **Thông báo kết quả** | tóm tắt ngay trong phiên Claude | **Lark** (`ENABLE_LARK_NOTIFY` + `LARK_*`) | **Generic webhook** Slack/Teams/Telegram/Discord (`ENABLE_NOTIFY_WEBHOOK` + `NOTIFY_*`) |
| **Chia sẻ report qua URL** | mở file local / gửi tay | **Cloudflare R2** (`ENABLE_CF_PUSH` + `CF_*`, cần `wrangler`) | **S3-compatible** AWS/CMC/MinIO (`ENABLE_S3_PUSH` + `S3_*`/`AWS_*`, cần `aws` CLI) |

Generic webhook: set `NOTIFY_PROVIDER=slack\|discord\|teams\|generic` + `NOTIFY_WEBHOOK_URL`, hoặc `telegram` + `NOTIFY_TELEGRAM_TOKEN`/`NOTIFY_TELEGRAM_CHAT_ID`. S3: để trống `S3_ENDPOINT` cho AWS thật, điền endpoint cho CMC/MinIO. Tất cả vẫn là cụm key trong `./.env` của user — chọn kênh nào điền cụm đó, kênh không dùng để `ENABLE_*=false`.

---

## 6. Update một nơi → mọi project

1. Sửa file trong `plugins/...`, **bump `version`** trong `plugin.json` liên quan, commit & push.
2. Mỗi máy: `/plugin marketplace update qa-claude` → `/reload-plugins` (hoặc mở session mới).

---

## 7. Luật bất biến khi mở rộng (nói AI tuân thủ)

1. **`${CLAUDE_PLUGIN_ROOT}` là per-plugin** — file một command/skill *đọc* phải **cùng plugin**; gọi skill plugin khác thì **gọi theo tên** (vd `commit-push`), không trỏ path chéo plugin.
2. **Không** dùng `.claude/rules|skills|agents/` trong file plugin — luôn `${CLAUDE_PLUGIN_ROOT}/...` hoặc link tương đối trong cùng plugin.
3. **Command `auto` luôn có Bước 0 `detect-platform`** rồi chỉ đọc skill/rule đúng nền tảng (web `rules/web/*` · app `rules/app/*`). Thêm nền tảng mới = thêm skill `*-<platform>` + 1 dòng trong router, KHÔNG nhồi vào skill chung.
4. Command frontmatter giữ format (`description`, `argument-hint`, `allowed-tools`). Skill = thư mục `<name>/SKILL.md`, frontmatter `name` (== tên thư mục) + `description`.
5. Sau khi sửa: `python3 -m json.tool` mọi JSON; `grep -rn '\.claude/\(rules\|skills\|agents\)/' plugins/` phải rỗng; tên skill tham chiếu phải tồn tại.

### Backlog gợi ý
- Tách riêng plugin `api` (REST/Postman) nếu cần — cùng khuôn router.
- Package Java ví dụ dùng placeholder `com.example.*`; project thật nên đặt base package của mình (cấu hình trong CLAUDE.md) — rule chỉ minh hoạ cấu trúc `screens/tests/utils/base`.
- Thêm nền tảng Flutter integration_test (Dart) như nhánh thứ 4 của router nếu chuyển từ Appium sang `appium_flutter_server`.
