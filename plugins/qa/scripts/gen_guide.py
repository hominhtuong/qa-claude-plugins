#!/usr/bin/env python3
"""Generate the user-facing usage guide for the qa plugin — cross-platform, stdlib-only.

After `setup`, the user has `.plugin.env` but may not know how to use the commands.
So next to it we drop a human-readable `README.md` that lists EVERY command that
actually ships in the plugin, grouped by workflow, with its description + argument hint.

The guide is generated from the live `commands/*.md` frontmatter, so it never drifts:
add/rename a command and the next `setup` (or `setup --update`) refreshes this file.
It is an OVERWRITE artifact (regenerated each run) — users should not hand-edit it.
"""
from __future__ import annotations

import json
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent      # scripts/ -> plugin root
GUIDE_NAME = "README.md"                                   # lives in .claude/qa-claude/

# Ordered command groups (Vietnamese headings). Commands are emitted in this order;
# any command found on disk but not listed here is appended under "Khác" so nothing
# is ever silently dropped.
GROUPS = [
    ("🚀 Bắt đầu & trợ giúp", [
        "scaffold", "setup", "help", "ask", "status", "feedback",
    ]),
    ("🤖 Kiểm thử tự động — Automation (Playwright Web / Appium iOS·Android)", [
        "exploratory", "plan-tests", "find-elements", "cook", "run", "fix",
        "analyze", "count-cases", "missing-test-ids", "kill-appium",
    ]),
    ("✍️ Kiểm thử thủ công — Manual QA (test case + bug board)", [
        "analyze-spec", "plan-gen-testcases", "gen-testcases", "count-testcases",
        "est-sp", "explain-bug", "check-duplicate-bug", "log-bug", "update-board",
    ]),
    ("📊 Quản lý chất lượng & báo cáo — QA Manager / Product Ops", [
        "quality-report", "bug-analysis", "release-gate", "traceability", "release-notes",
        "risk", "triage", "sla", "postmortem",
    ]),
    ("🔍 Review & tích hợp code", [
        "review-change", "review-codebase", "push-code", "merge-request",
    ]),
    ("🔗 Lark / Feishu", [
        "auth-lark",
    ]),
]


def _frontmatter(md: str) -> dict:
    """Pull the simple `key: value` frontmatter block from a command .md (stdlib only)."""
    out: dict = {}
    lines = md.splitlines()
    if not lines or lines[0].strip() != "---":
        return out
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" in line:
            key, _, val = line.partition(":")
            out[key.strip()] = val.strip()
    return out


def _plugin_version() -> str:
    try:
        meta = json.loads((PLUGIN_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        return str(meta.get("version", "?"))
    except Exception:  # noqa: BLE001
        return "?"


def _scan_commands() -> dict:
    """name -> {description, argument-hint} for every commands/*.md in the plugin."""
    cmds: dict = {}
    cmd_dir = PLUGIN_ROOT / "commands"
    for md in sorted(cmd_dir.glob("*.md")):
        fm = _frontmatter(md.read_text(encoding="utf-8"))
        cmds[md.stem] = {
            "description": fm.get("description", "").strip(),
            "argument-hint": fm.get("argument-hint", "").strip(),
        }
    return cmds


def build() -> str:
    """Render the full guide markdown from the live command set."""
    cmds = _scan_commands()
    seen: set = set()
    lines: list = []

    lines.append("# Hướng dẫn sử dụng plugin QA")
    lines.append("")
    lines.append(f"> Plugin **qa** v{_plugin_version()} — file này được **tự sinh** sau khi chạy setup. ")
    lines.append("> Đừng sửa tay (sẽ bị ghi đè ở lần setup sau). Sửa secrets ở `.plugin.env` cùng thư mục này.")
    lines.append("")
    lines.append("Mọi lệnh đều gọi qua namespace **`/qa:<tên-lệnh>`** trong Claude Code "
                 "(ví dụ `/qa:exploratory`, `/qa:run`, `/qa:log-bug`).")
    lines.append("Plugin tự nhận diện nền tảng (web / android / ios) và chỉ nạp skill tương ứng — bạn không cần chỉ định thủ công.")
    lines.append("")

    lines.append("## ⚡ Bắt đầu nhanh")
    lines.append("")
    lines.append("1. **Cài đặt 1 lần:** `/qa:setup` — tạo `.claude/qa-claude/` (config + `.plugin.env`), vá `.gitignore`, kiểm tra toolchain.")
    lines.append("2. **Điền secrets (nếu dùng Lark/R2/notify):** mở `.claude/qa-claude/.plugin.env` và bật các `ENABLE_*` cần thiết.")
    lines.append("3. **Cần Lark bug board?** điền `.claude/qa-claude/log-bug.config.yml` rồi `/qa:auth-lark --login` để xác thực.")
    lines.append("4. **Chưa rõ lệnh nào?** gõ `/qa:help` (tổng quan) hoặc `/qa:help <tên-lệnh>` (đi sâu 1 lệnh).")
    lines.append("")
    lines.append("> **Chính sách đăng nhập Lark (bắt buộc):** xin **FULL quyền** (read+write) trong 1 lần consent; "
                 "redirect mặc định cổng **3000** (`http://localhost:3000/callback`); **mode mặc định = `user`** — "
                 "đọc ưu tiên user, còn **tạo/cập nhật bug board BẮT BUỘC dùng user token** (`useUAT: true`) để truy vết "
                 "ai thao tác (không ghi bằng app/tenant token). Chi tiết: `/qa:auth-lark` và `rules/lark-mcp-guide.md`.")
    lines.append("")

    lines.append("## 🔁 Hai luồng làm việc")
    lines.append("")
    lines.append("- **Automation (viết code test):** `exploratory` → `plan-tests` → `cook` → `run` → `fix` → `review-change` → `push-code` → `merge-request`")
    lines.append("- **Manual QA (viết test case):** `analyze-spec` → `plan-gen-testcases` → `gen-testcases` → `log-bug`")
    lines.append("- **Quản lý & báo cáo (QA Manager / Product Ops):** `traceability` (phủ spec↔test↔bug) · `quality-report` (dashboard metrics) · `risk` (ma trận rủi ro) · `triage` (RICE) · `sla` (compliance) → `release-gate` (Go/No-Go) → `release-notes` (changelog nội bộ + bản cho người dùng)")
    lines.append("")
    lines.append("> Lưu ý: hai luồng dùng **tên lệnh khác nhau** — `cook` (viết code) vs `gen-testcases` (viết test case); "
                 "`plan-tests` vs `plan-gen-testcases`; `analyze` vs `analyze-spec`; `count-cases` vs `count-testcases`.")
    lines.append("")

    lines.append("## 📋 Danh sách đầy đủ các lệnh")
    lines.append("")

    def emit(name: str):
        info = cmds.get(name)
        if not info:
            return
        seen.add(name)
        hint = info["argument-hint"]
        title = f"#### `/qa:{name}`"
        if hint:
            title += f"  `{hint}`"
        lines.append(title)
        lines.append("")
        lines.append(info["description"] or "_(chưa có mô tả)_")
        lines.append("")

    for heading, names in GROUPS:
        present = [n for n in names if n in cmds]
        if not present:
            continue
        lines.append(f"### {heading}")
        lines.append("")
        for n in present:
            emit(n)

    leftover = [n for n in cmds if n not in seen]
    if leftover:
        lines.append("### 🧩 Khác")
        lines.append("")
        for n in sorted(leftover):
            emit(n)

    lines.append("---")
    lines.append("")
    lines.append("Gặp lỗi hoặc muốn góp ý? chạy `/qa:feedback` để mở issue đã điền sẵn thông tin (version, OS).")
    lines.append("")
    return "\n".join(lines)


def install(managed_dir: Path) -> Path:
    """Write the guide into <project>/.claude/qa-claude/README.md (OVERWRITE). Returns the path."""
    managed_dir.mkdir(parents=True, exist_ok=True)
    dst = managed_dir / GUIDE_NAME
    dst.write_text(build(), encoding="utf-8")
    return dst


if __name__ == "__main__":  # allow standalone preview: python3 gen_guide.py
    print(build())
