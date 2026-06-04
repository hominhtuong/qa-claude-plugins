#!/usr/bin/env python3
"""Build a pre-filled GitHub "new issue" URL for user feedback on the qa plugin.

Cross-platform, stdlib-only. Reads the plugin version, detects the OS, and prints a
ready-to-click GitHub issue link (pre-filled, no login needed to view/fill — a free
GitHub account is needed only to actually submit). If the `gh` CLI is installed, also
prints a `gh issue create` command to file it directly.

Privacy: only includes the message the user typed + plugin version + OS. Nothing else,
nothing silent — this runs only when the user invokes /qa:feedback.

Usage:
    python3 feedback.py "<message>" [--type bug|idea|question] [--context "<what you were doing / error>"]
"""
import argparse
import json
import platform
import shlex
import shutil
import sys
import urllib.parse
from pathlib import Path

REPO = "hominhtuong/qa-claude-plugins"        # upstream plugin repo — feedback lands here
PLUGIN_ROOT = Path(__file__).resolve().parent.parent


def plugin_version() -> str:
    try:
        data = json.loads((PLUGIN_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        return data.get("version", "unknown")
    except Exception:
        return "unknown"


def build(message: str, typ: str, context: str):
    ver = plugin_version()
    osname = f"{platform.system()} {platform.release()}"
    emoji = {"bug": "🐛", "idea": "💡", "question": "❓", "feedback": "📝"}.get(typ, "📝")
    title = f"[{typ}] " + (message.strip().splitlines()[0][:70] if message.strip() else "feedback")
    body = (
        f"### {emoji} {typ.capitalize()}\n{message.strip() or '(no description)'}\n\n"
        f"### What were you doing / error (if any)\n{context.strip() or '(not provided)'}\n\n"
        f"---\n- Plugin: `qa` v{ver}\n- OS: {osname}\n- Submitted via `/qa:feedback`\n"
    )
    query = urllib.parse.urlencode({"title": title, "body": body, "labels": "feedback"})
    url = f"https://github.com/{REPO}/issues/new?{query}"
    return url, title, body


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build a GitHub feedback issue link")
    ap.add_argument("message")
    ap.add_argument("--type", default="bug", choices=["bug", "idea", "question", "feedback"])
    ap.add_argument("--context", default="")
    args = ap.parse_args(argv)

    url, title, body = build(args.message, args.type, args.context)
    print("FEEDBACK_URL=" + url)
    if shutil.which("gh"):
        print("\n# gh is installed — you can file it directly with:")
        # no --label (gh errors if the label doesn't exist on the repo; the web URL is lenient)
        print(f"gh issue create --repo {REPO} "
              f"--title {shlex.quote(title)} --body {shlex.quote(body)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
