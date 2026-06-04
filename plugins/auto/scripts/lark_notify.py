#!/usr/bin/env python3
"""Send a test-result interactive card to a Lark group via Custom Bot Webhook.

Cross-platform (Windows/macOS/Linux), stdlib-only — no pip install needed.
Ported 1:1 from F2WebAutomation `LarkNotifier.java` (HMAC-SHA256 sign + lark_md card).

Config is read from the PROJECT's ./.env (see `setup` skill):
    ENABLE_LARK_NOTIFY   true|false   (gate; false => no-op, exit 0)
    LARK_WEBHOOK_URL     https://open.larksuite.com/open-apis/bot/v2/hook/xxxx
    LARK_WEBHOOK_SECRET  sign secret (optional; enables HMAC sign)
    LARK_PLATFORM        display label (default "QA")
    LARK_USER            triggered-by label (default "QA")

Usage:
    python3 lark_notify.py --passed 10 --failed 2 --skipped 1 --duration-ms 123000 \\
        --report-url https://... --git-name "Minh" --git-email a@b.c \\
        --failed-test "loginTest|NoSuchElement: #submit" --failed-test "payTest|timeout"

Exit codes: 0 = sent or intentionally skipped; 1 = real send error.
"""
import argparse
import base64
import hashlib
import hmac
import json
import sys
import time
import urllib.request
from datetime import datetime

from _env import env_bool, env_str, load_env


def _truncate(s: str, n: int = 200) -> str:
    return s if len(s) <= n else s[:n] + "…"


def build_card(platform, passed, failed, skipped, duration_ms,
               report_url, user, git_name, git_email, failed_tests):
    total = passed + failed + skipped
    status = "FAILED" if failed > 0 else "PASSED"
    color = "red" if failed > 0 else "green"

    secs = duration_ms // 1000
    mins, rem = divmod(secs, 60)
    duration = f"{mins}m {rem}s" if mins > 0 else f"{rem}s"

    def field(content):
        return {"is_short": True, "text": {"tag": "lark_md", "content": content}}

    elements = [
        {"tag": "div", "fields": [field(f"**Platform:**\n{platform}"),
                                   field(f"**Duration:**\n{duration}")]},
    ]

    if user or git_name:
        row = []
        if user:
            row.append(field(f"**Triggered by:**\n{user}"))
        if git_name:
            git_info = git_name + (f"\n{git_email}" if git_email else "")
            row.append(field(f"**Author:**\n{git_info}"))
        elements.append({"tag": "div", "fields": row})

    elements += [
        {"tag": "hr"},
        {"tag": "div", "fields": [field(f"**Total:**\n{total}"),
                                  field(f"**Passed:** ✅\n{passed}")]},
        {"tag": "div", "fields": [field(f"**Failed:** ❌\n{failed}"),
                                  field(f"**Skipped:** ⏭\n{skipped}")]},
    ]

    if failed_tests:
        lines = []
        for name, message in failed_tests:
            entry = f"🔴 **{name}**"
            if message:
                entry += f"\n{_truncate(message)}"
            lines.append(entry)
        elements.append({"tag": "hr"})
        elements.append({"tag": "div", "text": {"tag": "lark_md",
                        "content": f"**Failed tests ({len(failed_tests)}):**\n" + "\n".join(lines)}})

    elements.append({"tag": "hr"})

    if report_url:
        elements.append({"tag": "action", "actions": [{
            "tag": "button",
            "text": {"tag": "plain_text", "content": "📊 View Full Report"},
            "url": report_url, "type": "primary"}]})

    elements.append({"tag": "note", "elements": [
        {"tag": "plain_text", "content": datetime.now().strftime("%d/%m/%Y %H:%M:%S")}]})

    return {
        "msg_type": "interactive",
        "card": {
            "header": {"template": color,
                       "title": {"tag": "plain_text",
                                 "content": f"{platform} Test Report - {status}"}},
            "elements": elements,
        },
    }


def _sign(secret: str, timestamp: int) -> str:
    string_to_sign = f"{timestamp}\n{secret}"
    digest = hmac.new(string_to_sign.encode("utf-8"), b"", hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")


def send(webhook_url: str, secret: str, card: dict) -> int:
    body = dict(card)
    if secret:
        ts = int(time.time())
        body = {"timestamp": str(ts), "sign": _sign(secret, ts), **card}
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(webhook_url, data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            print(f"[Lark] response: {resp.status} - {resp.read().decode('utf-8', 'replace')}")
        return 0
    except Exception as e:  # noqa: BLE001 — notification must never break the run
        print(f"[Lark] send error: {e}", file=sys.stderr)
        return 1


def _parse_failed(values):
    out = []
    for v in values or []:
        name, _, message = v.partition("|")
        out.append((name.strip(), message.strip()))
    return out


def main(argv=None):
    load_env()
    ap = argparse.ArgumentParser(description="Send Lark test-report card")
    ap.add_argument("--passed", type=int, default=0)
    ap.add_argument("--failed", type=int, default=0)
    ap.add_argument("--skipped", type=int, default=0)
    ap.add_argument("--duration-ms", type=int, default=0)
    ap.add_argument("--report-url", default="")
    ap.add_argument("--platform", default=None, help="override LARK_PLATFORM")
    ap.add_argument("--user", default=None, help="override LARK_USER")
    ap.add_argument("--git-name", default="")
    ap.add_argument("--git-email", default="")
    ap.add_argument("--failed-test", action="append", dest="failed_tests",
                    help='repeatable; format "name|message"')
    args = ap.parse_args(argv)

    if not env_bool("ENABLE_LARK_NOTIFY", False):
        print("[Lark] disabled (ENABLE_LARK_NOTIFY != true) — skip")
        return 0
    webhook = env_str("LARK_WEBHOOK_URL")
    if not webhook:
        print("[Lark] LARK_WEBHOOK_URL empty — skip", file=sys.stderr)
        return 0

    platform = args.platform or env_str("LARK_PLATFORM", "QA")
    user = args.user or env_str("LARK_USER", "QA")
    card = build_card(platform, args.passed, args.failed, args.skipped, args.duration_ms,
                      args.report_url, user, args.git_name, args.git_email,
                      _parse_failed(args.failed_tests))
    return send(webhook, env_str("LARK_WEBHOOK_SECRET"), card)


if __name__ == "__main__":
    sys.exit(main())
