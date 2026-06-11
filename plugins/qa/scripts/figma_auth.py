#!/usr/bin/env python3
"""Assisted Figma token setup for /qa:exploratory-ui — cross-platform, stdlib-only.

MOST users don't need this: /qa:exploratory-ui reads Figma through the bundled **Figma MCP** (just
log in when asked) — no token. A FIGMA_TOKEN (personal access token) is only needed as a FALLBACK:
- headless / cron / no-MCP environments where MCP isn't available, or
- to fetch the EXACT design text + font names oracle via the REST API (a fidelity upgrade).

When a token IS needed, this makes it painless: you (Claude) run `--open` to launch the Figma token
page in the user's browser, the user creates a token (scope: File content read) and pastes it back,
then you run `--set <token>` — this script VALIDATES it (GET /v1/me) and writes FIGMA_TOKEN into
.claude/qa-claude/.plugin.env for them (via the shared upsert helper). The user never edits a file.

Subcommands:
    check            [--json]   report whether a token is set + valid, and that MCP is preferred
    open             [--json]   open the Figma personal-access-token page in the browser (+ print URL)
    set   --token T  [--json]   validate the pasted token, then persist FIGMA_TOKEN to .plugin.env

NEVER prints the full token (masked). Exit codes: 0 ok · 2 invalid/missing token · 3 network/TLS error.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _env import (ensure_utf8_io, load_env, find_env_file, project_root,  # noqa: E402
                  make_ssl_context, upsert_env_key, open_in_browser,
                  is_ssl_cert_error, ssl_help_text)

ensure_utf8_io()
load_env()

TOKEN_PAGE = "https://www.figma.com/settings"  # → Security → Personal access tokens → Create
ME_API = "https://api.figma.com/v1/me"
KEYS = ("FIGMA_TOKEN", "FIGMA_ACCESS_TOKEN", "FIGMA_PERSONAL_TOKEN")


def _mask(t: str) -> str:
    t = t or ""
    return (t[:6] + "…" + t[-4:]) if len(t) > 12 else "***"


def _current_token() -> str:
    for k in KEYS:
        v = (os.environ.get(k) or "").strip()
        if v and not v.lower().startswith(("your_", "figd_xxx")):
            return v
    return ""


def _validate(token: str):
    """GET /v1/me with the token. Returns (ok, info_or_error)."""
    ctx = make_ssl_context()
    req = urllib.request.Request(ME_API, headers={"X-Figma-Token": token})
    try:
        with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
            data = json.loads(r.read().decode("utf-8"))
        who = data.get("email") or data.get("handle") or "Figma user"
        return True, who
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            return False, f"token bị từ chối (HTTP {e.code}) — sai/hết hạn, hoặc thiếu scope 'File content'."
        return False, f"Figma API HTTP {e.code}"
    except Exception as e:  # noqa: BLE001
        msg = str(e)
        if is_ssl_cert_error(msg):
            return False, "TLS verify failed.\n" + ssl_help_text()
        return False, f"network error: {msg}"


def cmd_check(as_json: bool) -> int:
    tok = _current_token()
    out = {"mcp_preferred": True, "token_set": bool(tok)}
    if not tok:
        out["state"] = "no-token"
        out["hint"] = ("Không sao — /qa:exploratory-ui đọc Figma qua MCP (đăng nhập khi được hỏi), "
                       "không cần token. Chỉ cần token cho môi trường headless/no-MCP: chạy /qa:auth-figma.")
        print(json.dumps(out, ensure_ascii=False, indent=2) if as_json else f"ℹ️  {out['hint']}")
        return 0
    ok, info = _validate(tok)
    out["state"] = "valid" if ok else "invalid"
    out["token"] = _mask(tok)
    out["detail"] = info
    if as_json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print((f"✅ FIGMA_TOKEN hợp lệ ({_mask(tok)}) — {info}") if ok
              else f"❌ FIGMA_TOKEN ({_mask(tok)}) không hợp lệ: {info}")
    return 0 if ok else 2


def cmd_open(as_json: bool) -> int:
    opened = open_in_browser(TOKEN_PAGE)
    steps = ("1) Vào trang vừa mở → Settings → Security → 'Personal access tokens' → 'Generate new token'. "
             "2) Đặt scope 'File content' = Read. 3) Copy token (bắt đầu bằng figd_) rồi dán lại cho mình "
             "— mình sẽ kiểm tra và tự lưu (không cần sửa file).")
    out = {"opened": opened, "url": TOKEN_PAGE, "steps": steps}
    if as_json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(("🔗 Đã mở: " if opened else "🔗 Mở trang này: ") + TOKEN_PAGE)
        print("   " + steps)
    return 0


def cmd_set(token: str, as_json: bool) -> int:
    token = (token or "").strip()
    if not token:
        print(json.dumps({"ok": False, "error": "empty token"}, ensure_ascii=False) if as_json
              else "❌ Token rỗng.")
        return 2
    ok, info = _validate(token)
    if not ok:
        print(json.dumps({"ok": False, "error": info, "token": _mask(token)}, ensure_ascii=False, indent=2)
              if as_json else f"❌ Token không hợp lệ: {info}")
        return 2 if "HTTP" in info or "từ chối" in info else 3
    env_path = find_env_file() or (project_root() / ".claude" / "qa-claude" / ".plugin.env")
    upsert_env_key(env_path, "FIGMA_TOKEN", token, comment="auto-managed by /qa:auth-figma — do not hand-edit")
    out = {"ok": True, "token": _mask(token), "user": info, "env": str(env_path)}
    if as_json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(f"✅ Đã lưu FIGMA_TOKEN ({_mask(token)}) cho {info} → {env_path}")
        print("   /qa:exploratory-ui giờ có thể dùng REST fallback + oracle text chính xác.")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Assisted Figma token setup for /qa:exploratory-ui")
    sub = ap.add_subparsers(dest="cmd")
    for name in ("check", "open", "set"):
        sp = sub.add_parser(name)
        sp.add_argument("--json", action="store_true")
        if name == "set":
            sp.add_argument("--token", required=True, help="the personal access token pasted by the user")
    args = ap.parse_args(argv)
    if args.cmd == "check":
        return cmd_check(args.json)
    if args.cmd == "open":
        return cmd_open(args.json)
    if args.cmd == "set":
        return cmd_set(args.token, args.json)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
