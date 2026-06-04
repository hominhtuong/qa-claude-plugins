# qa-claude-plugins

Marketplace plugin Claude Code **dùng chung** cho các project automation QA của Finan.
Mục tiêu: **sửa 1 nơi → mọi project update theo**, không còn copy `.claude/` thủ công từng repo, không xung đột với project.

- **Repo**: `hominhtuong/qa-claude-plugins` (local: `~/Documents/Shared/QAClaudePlugins`).
- **Marketplace name**: `qa-claude` (cái anh gõ sau dấu `@`).
- **Plugins**: `core` (dùng chung mọi project) · `appium` (mobile Appium/Flutter).
- Sẽ mở rộng: `web` (Playwright), `api` (REST/Postman) theo cùng khuôn.

---

## 1. Vì sao là plugin (không phải submodule / npm)

| | Submodule | npm/library | **Plugin marketplace** ✅ |
|---|---|---|---|
| Sửa 1 nơi → all update | `git submodule update` từng repo | postinstall copy file | `/plugin marketplace update qa-claude` (hoặc auto) |
| Mọi git host | ✓ | ✓ | ✓ (GitHub / git URL / self-host / npm / local) |
| Không xung đột project | ❌ đổ thẳng vào `.claude` | ❌ | ✅ **namespaced** `/appium:cook` |
| Claude load native | ✓ | ❌ không load skill từ `node_modules` | ✅ |
| Version pin | theo commit | semver | cả hai (`version` trong `plugin.json`) |

> **Codex**: plugin là cơ chế riêng của Claude Code — `.codex/` **không** đọc được. Project nào còn cần Codex thì giữ submodule song song chỉ cho mục đích đó.

---

## 2. Cấu trúc repo

```
qa-claude-plugins/
├── .claude-plugin/marketplace.json     # catalog liệt kê các plugin
└── plugins/
    ├── core/
    │   ├── .claude-plugin/plugin.json
    │   ├── commands/   status.md · ask.md · missing-test-ids.md
    │   ├── skills/     commit-push · build-verify · missing-ids
    │   └── rules/      git-conventions.md
    └── appium/
        ├── .claude-plugin/plugin.json
        ├── commands/   cook · plan · fix · exploratory · run · kill-appium · count-cases · analyze · review-change · review-codebase · push-code · merge-request
        ├── skills/     capture-elements · declare-screen · mcp-navigate · update-sitemap · run-tests · review-audit · fix-by-layer · design-conformance
        ├── agents/     source-inspector · figma-reader · lark-reader
        └── rules/      design-pattern · coding-rules · design-system · design-system-figma · failure-triage · troubleshooting · lark-mcp-guide · review-checklist · exploratory-bug-report-template · report-template.html
```

**Nguyên tắc phân tầng**: file mà một command/skill cần **đọc** phải nằm **cùng plugin** (vì `${CLAUDE_PLUGIN_ROOT}` là per-plugin, không trỏ chéo plugin được). Việc gọi **skill khác plugin** thì gọi **theo tên** (`commit-push`) — Claude resolve theo plugin đang bật, OK.

---

## 3. Cách dùng cho mỗi project

### Cài (1 lần / máy)
```bash
# GitHub
/plugin marketplace add hominhtuong/qa-claude-plugins
# hoặc git URL bất kỳ (GitLab/self-host)
/plugin marketplace add https://gitlab.com/finan/qa-claude-plugins.git

/plugin install core@qa-claude
/plugin install appium@qa-claude     # project mobile
```

### Hoặc khai báo trong project (commit vào repo → ai clone cũng tự được hỏi cài)
`.claude/settings.json`:
```json
{
  "extraKnownMarketplaces": {
    "qa-claude": { "source": { "source": "github", "repo": "hominhtuong/qa-claude-plugins" } }
  },
  "enabledPlugins": {
    "core@qa-claude": true,
    "appium@qa-claude": true
  }
}
```

### Gọi command (namespaced — không đụng command local)
```
/appium:cook <plan|yêu cầu>
/appium:exploratory <feature>
/core:push-code
```
> Gõ **trần** `/cook` → command **local** của project (nếu có) sẽ thắng. Muốn dùng bản plugin thì gõ namespaced `/appium:cook`, hoặc **xóa command trùng** khỏi project để hết drift.

---

## 4. Update một nơi → mọi project

1. Sửa file trong `plugins/...`, commit & push repo này.
2. Mỗi máy: `/plugin marketplace update qa-claude` rồi `/reload-plugins` (hoặc mở session mới).
3. **Versioning**: bump `version` trong `plugin.json` mỗi lần release để project nhảy có kiểm soát. (Bỏ `version` = auto theo mỗi commit.)

---

## 5. Tham chiếu rule trong plugin

Rule sống cùng plugin, command/skill đọc qua biến `${CLAUDE_PLUGIN_ROOT}` (trỏ tới path cache thật ở mọi máy):
```
- @${CLAUDE_PLUGIN_ROOT}/rules/design-pattern.md
- @${CLAUDE_PLUGIN_ROOT}/rules/coding-rules.md
```
Project **không cần** sửa CLAUDE.md để nạp rule — command tự đọc.

---

## 6. Trạng thái & việc còn lại (pilot)

Đây là **bản scaffold lần 1**, gom 1:1 nội dung `.claude/` của **SBHAppium** làm bản mẫu chạy được.

- [x] Cấu trúc marketplace + 2 plugin + manifests.
- [x] Rewrite `.claude/{rules,skills,agents}/` → `${CLAUDE_PLUGIN_ROOT}/...` trong `appium`.
- [x] Tách `core` thật sự decoupled (3 skill + 3 command + git-conventions).
- [ ] **Verify khi pilot**: `@${CLAUDE_PLUGIN_ROOT}/rules/X.md` (auto-import có expand biến không) — nếu không, đổi thành câu lệnh "Read `${CLAUDE_PLUGIN_ROOT}/rules/X.md`".
- [ ] Rule `design-system-figma.md` còn trỏ `../../sbh-app-design-system/` (đặc thù SBH) — khi dùng cho project khác cần tổng quát hóa hoặc bỏ.
- [ ] **Open design**: `push-code`/`merge-request` (orchestrator) đang ở `appium` vì gọi `review-audit` (domain). Có thể nâng thành "core orchestrator gọi review-audit theo tên" khi thêm `web`/`api`.
- [ ] Tạo plugin `web` (từ F2WebAutomation) + `api` (từ SBH_API).

### Pilot khuyến nghị
Cài vào **ShinhanAppium** (đang trống skills/rules, rủi ro thấp nhất) → chạy `/appium:cook`, `/appium:run` xác nhận hoạt động trước khi rollout phần còn lại.

---

## 7. Tiếp tục bằng AI (dành cho phiên làm việc tại repo này)

Mở Claude Code **ngay tại thư mục repo này** (`~/Documents/Shared/QAClaudePlugins`) rồi giao việc theo các mạch dưới. Mỗi việc nêu rõ ràng buộc để AI không phá kiến trúc.

### Luật bất biến khi gen thêm (nói AI tuân thủ)
1. **`${CLAUDE_PLUGIN_ROOT}` là per-plugin** — file mà một command/skill *đọc* phải nằm **cùng plugin**; gọi skill khác plugin thì **gọi theo tên** (vd `commit-push`), không trỏ đường dẫn chéo plugin.
2. **Không** dùng `.claude/rules|skills|agents/` trong file plugin — luôn `${CLAUDE_PLUGIN_ROOT}/...` (hoặc link tương đối trong cùng plugin).
3. Mỗi plugin có `.claude-plugin/plugin.json` (`name`, `description`, `version`). Mỗi lần release → **bump `version`**.
4. Command frontmatter giữ nguyên format hiện có (`description`, `argument-hint`, `allowed-tools`). Skill là thư mục `<name>/SKILL.md` với frontmatter `name` + `description`.
5. Sau khi sửa: chạy `python3 -m json.tool` cho mọi JSON; grep `\.claude/(rules|skills|agents)/` phải rỗng trong `plugins/`.

### Backlog gợi ý (prompt mẫu cho AI)
- **Tạo plugin `web`**: "Tạo plugin `web` từ `~/Documents/Finan/F2WebAutomation/.claude` (Playwright Java + TestNG). Cùng khuôn `appium`: copy commands/skills/rules vào `plugins/web/`, rewrite path sang `${CLAUDE_PLUGIN_ROOT}`, thêm `plugin.json`, thêm entry vào `marketplace.json`. Các skill trùng tên với `core` (commit-push/build-verify/missing-ids) thì **bỏ**, gọi `core` theo tên."
- **Tạo plugin `api`**: tương tự từ `~/Documents/Finan/SBH_API/.claude`.
- **Nâng orchestrator lên core**: "Chuyển `push-code`/`merge-request` từ `appium` sang `core`, sửa để gọi `review-audit`/`fix-by-layer` **theo tên** (resolve theo plugin domain đang bật) thay vì trỏ file."
- **Tổng quát hóa rule SBH-specific**: bỏ/điều kiện hóa tham chiếu `../../sbh-app-design-system/` trong `appium/rules/design-system-figma.md`.
- **Verify auto-import**: kiểm dòng `@${CLAUDE_PLUGIN_ROOT}/rules/X.md` có expand không; nếu không → đổi sang câu lệnh "Read `${CLAUDE_PLUGIN_ROOT}/rules/X.md`" ở đầu mỗi command.

### Phát hành thay đổi
```bash
# sửa file trong plugins/... → bump version trong plugin.json
git add -A && git commit -m "feat(web): add web plugin"
git push
# mỗi máy dùng:  /plugin marketplace update qa-claude  →  /reload-plugins
```
