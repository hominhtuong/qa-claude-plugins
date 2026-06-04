#!/usr/bin/env python3
"""Push a test report to any S3-compatible storage (AWS S3 / CMC Cloud / MinIO) via the `aws` CLI.

Alternative to push_report.py (Cloudflare R2) for teams not on Cloudflare.
Cross-platform; shares file-collection/log with push_report.py via _upload.py.
Uses the standard S3 endpoint + access-key/secret convention (works with AWS/CMC/MinIO).

Requires the AWS CLI (`aws`). Install: macOS `brew install awscli` · Windows
`winget install Amazon.AWSCLI` · Linux `sudo apt install awscli`. (doctor reports it.)

Config from .claude/qa-claude/.env (see `setup` skill):
    ENABLE_S3_PUSH       true|false   (gate; false => no-op, exit 0)
    AWS_ACCESS_KEY_ID    access key                    (required)
    AWS_SECRET_ACCESS_KEY secret key                   (required)
    S3_BUCKET            bucket name                   (required)
    S3_REGION            region (e.g. ap-southeast-1, hcm-1)   (optional)
    S3_ENDPOINT          custom endpoint url           (optional; blank => AWS default)
    S3_PREFIX            key prefix / folder           (optional)
    S3_PUBLIC_BASE       base url to build shareable links  (optional)

Usage:
    python3 push_s3.py <report_html_file> [session_manifest]

Prints `REPORT_URL=<url>` (empty if no S3_PUBLIC_BASE) for the notifier scripts.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

from _env import env_bool, env_str, load_env, project_root
from _upload import UploadLog, content_type, report_targets


def log(msg):
    print(f"[S3] {msg}")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    load_env()

    if not env_bool("ENABLE_S3_PUSH", False):
        log("Push disabled (ENABLE_S3_PUSH != true)")
        print("REPORT_URL=")
        return 0

    missing = [k for k in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "S3_BUCKET") if not env_str(k)]
    if missing:
        log(f"ERROR: missing config: {', '.join(missing)}")
        return 1

    if not argv:
        log("ERROR: missing report file path\nUsage: push_s3.py <report_html_file> [manifest]")
        return 1
    report_file = Path(argv[0])
    if not report_file.is_file():
        log(f"ERROR: report file not found: {report_file}")
        return 1
    manifest = Path(argv[1]) if len(argv) > 1 and argv[1] else None

    if shutil.which("aws") is None:
        log("ERROR: aws CLI not found. Install: brew/winget/apt install awscli (run the `doctor` skill)")
        return 1

    # aws CLI reads creds/region from env
    os.environ["AWS_ACCESS_KEY_ID"] = env_str("AWS_ACCESS_KEY_ID")
    os.environ["AWS_SECRET_ACCESS_KEY"] = env_str("AWS_SECRET_ACCESS_KEY")
    region = env_str("S3_REGION")
    if region:
        os.environ["AWS_DEFAULT_REGION"] = region

    bucket = env_str("S3_BUCKET")
    endpoint = env_str("S3_ENDPOINT")
    prefix = env_str("S3_PREFIX")
    public_base = env_str("S3_PUBLIC_BASE").rstrip("/")
    date_folder = report_file.parent.name
    log_dir = Path(env_str("S3_LOG_DIR") or (project_root() / "reports" / "upload-logs"))
    ulog = UploadLog(log_dir / f"{date_folder}.s3.log")

    log("━" * 34)
    log(f"Report: {report_file.name} | Bucket: {bucket} | Endpoint: {endpoint or 'aws-default'}")
    log("━" * 34)

    report_url = ""
    total = skipped = 0
    for path, base_key in report_targets(report_file, manifest):
        key = f"{prefix}/{base_key}" if prefix else base_key
        url = f"{public_base}/{key}" if public_base else ""
        total += 1
        existing = ulog.lookup(key)
        if existing is not None:
            log(f"  SKIP (already uploaded): {path.name}")
            skipped += 1
        else:
            cmd = ["aws", "s3", "cp", str(path), f"s3://{bucket}/{key}",
                   "--content-type", content_type(path)]
            if endpoint:
                cmd += ["--endpoint-url", endpoint]
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
