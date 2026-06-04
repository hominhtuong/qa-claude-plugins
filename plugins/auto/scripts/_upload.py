"""Shared upload helpers for report-push scripts (push_report.py / push_s3.py).

Keeps the file-collection, content-type map and per-date dedup log identical across
upload providers (Cloudflare R2, S3-compatible) so they never drift.
"""
from __future__ import annotations

import time
from pathlib import Path

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8", ".css": "text/css",
    ".js": "application/javascript", ".json": "application/json",
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".gif": "image/gif", ".mp4": "video/mp4",
}


def content_type(path: Path) -> str:
    return CONTENT_TYPES.get(path.suffix.lower(), "application/octet-stream")


def report_targets(report_file: Path, manifest: Path | None):
    """Yield (local_path, object_key_without_prefix) for the HTML report + its media.

    object_key is rooted at the report's date folder, e.g. `16Mar2026/Android_report.html`,
    `16Mar2026/images/x.png`. The first yielded item is always the HTML report itself.
    """
    date_dir = report_file.parent
    date_folder = date_dir.name
    yield report_file, f"{date_folder}/{report_file.name}"

    if manifest and manifest.is_file():
        for raw in manifest.read_text(encoding="utf-8").splitlines():
            rel = raw.strip()
            if not rel or rel.startswith("#"):
                continue
            full = date_dir / rel
            if full.is_file():
                yield full, f"{date_folder}/{rel}"
    else:
        for sub in ("images", "videos"):
            d = date_dir / sub
            if d.is_dir():
                for p in sorted(d.rglob("*")):
                    if p.is_file():
                        yield p, f"{date_folder}/{sub}/{p.relative_to(d).as_posix()}"


class UploadLog:
    """Flat per-date log: <object_key>|<url>|<status>|<timestamp>. Dedup by first OK match."""

    def __init__(self, log_file: Path):
        self.path = log_file
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)

    def lookup(self, object_key: str):
        prefix = object_key + "|"
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.startswith(prefix):
                parts = line.split("|")
                if len(parts) >= 3 and parts[2] == "OK":
                    return parts[1]  # url
        return None

    def write(self, object_key: str, url: str, status: str):
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        with self.path.open("a", encoding="utf-8") as f:
            f.write(f"{object_key}|{url}|{status}|{ts}\n")
