#!/usr/bin/env python3
"""Send a test-result message to a generic chat webhook (Slack/Discord/Teams/Telegram/generic).

Alternative to lark_notify.py for teams not on Lark. Cross-platform, stdlib-only.
Builds one plain-text summary and shapes the payload per provider.

Config from the PROJECT's ./.env (see `setup` skill):
    ENABLE_NOTIFY_WEBHOOK   true|false   (gate; false => no-op, exit 0)
    NOTIFY_PROVIDER         slack|discord|teams|telegram|generic   (default slack)
    NOTIFY_WEBHOOK_URL      incoming webhook url (slack/discord/teams/generic)
    NOTIFY_TELEGRAM_TOKEN   bot token            (telegram only)
    NOTIFY_TELEGRAM_CHAT_ID chat/channel id      (telegram only)
    NOTIFY_PLATFORM         display label (default "QA")
    NOTIFY_USER             triggered-by label (default "QA")

Usage: same flags as lark_notify.py
    python3 notify_webhook.py --passed 10 --failed 2 --skipped 1 --duration-ms 123000 \\
        --report-url https://... --failed-test "loginTest|NoSuchElement"

Exit codes: 0 = sent or intentionally skipped; 1 = real send error.
"""
import argparse
import json
import sys
import urllib.request

from _env import env_bool, env_str, load_env


def _truncate(s: str, n: int = 200) -> str:
    return s if len(s) <= n else s[:n] + "…"


def build_text(platform, passed, failed, skipped, duration_ms, report_url,
               user, git_name, git_email, failed_tests):
    total = passed + failed + skipped
    status = "FAILED" if failed > 0 else "PASSED"
    emoji = "❌" if failed > 0 else "✅"
    secs = duration_ms // 1000
    mins, rem = divmod(secs, 60)
    duration = f"{mins}m {rem}s" if mins > 0 else f"{rem}s"

    lines = [f"{emoji} {platform} Test Report — {status}",
             f"Total: {total} | ✅ {passed} | ❌ {failed} | ⏭ {skipped} | ⏱ {duration}"]
    who = []
    if user:
        who.append(f"Triggered by: {user}")
    if git_name:
        who.append(f"Author: {git_name}" + (f" <{git_email}>" if git_email else ""))
    if who:
        lines.append(" | ".join(who))
    if failed_tests:
        lines.append(f"Failed tests ({len(failed_tests)}):")
        for name, message in failed_tests:
            lines.append(f"🔴 {name}" + (f" — {_truncate(message)}" if message else ""))
    if report_url:
        lines.append(f"Report: {report_url}")
    return "\n".join(lines)


def build_payload(provider, text, failed):
    if provider == "discord":
        return {"content": text}
    if provider == "teams":
        return {"@type": "MessageCard", "@context": "http://schema.org/extensions",
                "themeColor": "E01E5A" if failed else "2EB67D",
                "text": text.replace("\n", "  \n")}
    if provider == "telegram":
        return {"text": text}  # chat_id added by caller
    # slack & generic both accept {"text": ...}
    return {"text": text}


def post(url, payload):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.status, resp.read().decode("utf-8", "replace")


def _parse_failed(values):
    out = []
    for v in values or []:
        name, _, message = v.partition("|")
        out.append((name.strip(), message.strip()))
    return out


def main(argv=None):
    load_env()
    ap = argparse.ArgumentParser(description="Send test-report to a generic chat webhook")
    ap.add_argument("--passed", type=int, default=0)
    ap.add_argument("--failed", type=int, default=0)
    ap.add_argument("--skipped", type=int, default=0)
    ap.add_argument("--duration-ms", type=int, default=0)
    ap.add_argument("--report-url", default="")
    ap.add_argument("--platform", default=None, help="override NOTIFY_PLATFORM")
    ap.add_argument("--user", default=None, help="override NOTIFY_USER")
    ap.add_argument("--git-name", default="")
    ap.add_argument("--git-email", default="")
    ap.add_argument("--failed-test", action="append", dest="failed_tests",
                    help='repeatable; format "name|message"')
    args = ap.parse_args(argv)

    if not env_bool("ENABLE_NOTIFY_WEBHOOK", False):
        print("[notify] disabled (ENABLE_NOTIFY_WEBHOOK != true) — skip")
        return 0

    provider = (env_str("NOTIFY_PROVIDER", "slack") or "slack").lower()
    platform = args.platform or env_str("NOTIFY_PLATFORM", "QA")
    user = args.user or env_str("NOTIFY_USER", "QA")
    text = build_text(platform, args.passed, args.failed, args.skipped, args.duration_ms,
                      args.report_url, user, args.git_name, args.git_email,
                      _parse_failed(args.failed_tests))

    try:
        if provider == "telegram":
            token = env_str("NOTIFY_TELEGRAM_TOKEN")
            chat_id = env_str("NOTIFY_TELEGRAM_CHAT_ID")
            if not token or not chat_id:
                print("[notify] telegram needs NOTIFY_TELEGRAM_TOKEN + NOTIFY_TELEGRAM_CHAT_ID — skip",
                      file=sys.stderr)
                return 0
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {"chat_id": chat_id, "text": text}
        else:
            url = env_str("NOTIFY_WEBHOOK_URL")
            if not url:
                print("[notify] NOTIFY_WEBHOOK_URL empty — skip", file=sys.stderr)
                return 0
            payload = build_payload(provider, text, args.failed > 0)

        status, body = post(url, payload)
        print(f"[notify:{provider}] response: {status} - {body[:200]}")
        return 0
    except Exception as e:  # noqa: BLE001 — notification must never break the run
        print(f"[notify:{provider}] send error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
