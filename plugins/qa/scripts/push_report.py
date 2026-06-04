#!/usr/bin/env python3
"""Push a test report (HTML + screenshots/videos) to Cloudflare R2 via wrangler.

Cross-platform (Windows/macOS/Linux) — a python replacement for a bash push script,
with a per-date upload log + dedup. Shares file-collection/log with push_s3.py via _upload.py.

Requires the `wrangler` CLI (auto-installed by the `setup`/`doctor` skill:
`npm install -g wrangler`). Falls back to `npx wrangler` if not on PATH.

Config from .claude/qa-claude/.plugin.env (see `setup` skill):
    ENABLE_CF_PUSH   true|false   (gate; false => no-op, exit 0)
    CF_ACCOUNT_ID    Cloudflare account id        (required)
    CF_API_TOKEN     R2-edit API token            (required)
    CF_R2_BUCKET     bucket name                  (required)
    CF_R2_DOMAIN     public custom domain         (optional, builds URLs)
    CF_R2_PREFIX     key prefix / folder          (optional)

Usage:
    python3 push_report.py <report_html_file> [session_manifest]

Prints a final machine-readable line `REPORT_URL=<url>` (empty if no domain) so the
caller can feed it to lark_notify.py / notify_webhook.py --report-url.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

from _env import env_bool, env_str, load_env, project_root
from _upload import UploadLog, content_type, report_targets


def log(msg):
    print(f"[R2] {msg}")


def resolve_wrangler():
    if shutil.which("wrangler"):
        return ["wrangler"]
    if shutil.which("npx"):
        return ["npx", "wrangler"]
    return None


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    load_env()

    if not env_bool("ENABLE_CF_PUSH", False):
        log("Push disabled (ENABLE_CF_PUSH != true)")
        print("REPORT_URL=")
        return 0

    missing = [k for k in ("CF_ACCOUNT_ID", "CF_API_TOKEN", "CF_R2_BUCKET") if not env_str(k)]
    if missing:
        log(f"ERROR: missing config: {', '.join(missing)}")
        return 1

    if not argv:
        log("ERROR: missing report file path\nUsage: push_report.py <report_html_file> [manifest]")
        return 1
    report_file = Path(argv[0])
    if not report_file.is_file():
        log(f"ERROR: report file not found: {report_file}")
        return 1
    manifest = Path(argv[1]) if len(argv) > 1 and argv[1] else None

    wrangler = resolve_wrangler()
    if wrangler is None:
        log("ERROR: wrangler not found. Install: npm install -g wrangler (run the `setup` skill)")
        return 1

    os.environ["CLOUDFLARE_ACCOUNT_ID"] = env_str("CF_ACCOUNT_ID")
    os.environ["CLOUDFLARE_API_TOKEN"] = env_str("CF_API_TOKEN")

    bucket = env_str("CF_R2_BUCKET")
    domain = env_str("CF_R2_DOMAIN")
    prefix = env_str("CF_R2_PREFIX")
    date_folder = report_file.parent.name
    log_dir = Path(env_str("CF_LOG_DIR") or (project_root() / "results" / "tests" / ".upload-logs"))
    ulog = UploadLog(log_dir / f"{date_folder}.log")

    log("━" * 34)
    log(f"Report: {report_file.name} | Bucket: {bucket} | Log: {ulog.path}")
    log("━" * 34)

    report_url = ""
    total = skipped = 0
    for path, base_key in report_targets(report_file, manifest):
        key = f"{prefix}/{base_key}" if prefix else base_key
        url = f"{domain}/{key}" if domain else ""
        total += 1
        existing = ulog.lookup(key)
        if existing is not None:
            log(f"  SKIP (already uploaded): {path.name}")
            skipped += 1
        else:
            cmd = wrangler + ["r2", "object", "put", f"{bucket}/{key}",
                              f"--file={path}", f"--content-type={content_type(path)}", "--remote"]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode == 0:
                ulog.write(key, url, "OK")
                log(f"  OK: {path.name}")
            else:
                ulog.write(key, url, "FAIL")
                tail = proc.stderr.strip().splitlines()[-1] if proc.stderr.strip() else "unknown"
                log(f"  FAIL: {path.name} :: {tail}")
                url = ""
        if path == report_file:
            report_url = url

    log("━" * 34)
    log(f"Total: {total} files ({skipped} skipped)")
    if report_url:
        log(f"URL: {report_url}")
    log("Done!")
    print(f"REPORT_URL={report_url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
