#!/usr/bin/env python3
"""Read a Lark/Feishu wiki or docx document via the app (tenant) token — no MCP.

Why Python instead of the Lark MCP: the MCP frequently fails with token-expired
(99991668) because it does not refresh; this helper re-authenticates the app on every
run (one call, cached token reused within its TTL) so reads are reliable in headless
and cron contexts. Credentials + scopes are the SAME ones /qa:auth-lark verifies
(wiki.read / docx.read / drive.read), read from .claude/qa-claude/.plugin.env.

Given a wiki/docx URL it resolves the object, pulls the plain text + the block tree
(to find images, tables, and embedded links), and the comments. Output is JSON the
lark-reader agent formats into a Vietnamese (with-diacritics) summary.

Usage:
    python3 lark_read.py "<wiki_or_docx_url>"            # JSON to stdout
    python3 lark_read.py "<url>" --no-comments           # skip comments
    python3 lark_read.py "<url>" --media-urls            # also resolve image tmp download URLs

Exit codes: 0 ok · 2 missing/invalid credentials · 4 could not read the document.
NEVER prints the app secret or the access token.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from urllib.parse import urlparse

from _env import env_str, load_env
from lark_auth import (DEFAULT_DOMAIN, _api, _classify, available_modes,
                       get_read_token, other_mode)

# --- token (dual-mode: tenant app token or user OAuth token, with fallback) ---
#
# The mode is resolved by lark_auth (--mode preference → cached read_mode → tenant).
# If the chosen mode is DENIED the document, read_document flags it and main() retries
# with the other configured mode — so a doc shared with only the user (or only the app)
# is still read whichever way works.


# --- URL parsing ---

_TOKEN_RE = re.compile(r"/(wiki|docx|docs|sheets|base|file)/([A-Za-z0-9]+)")


def parse_url(url: str) -> tuple[str, str]:
    """Return (kind, token) from a Lark URL. kind in wiki/docx/sheets/base/file."""
    m = _TOKEN_RE.search(urlparse(url).path if "://" in url else url)
    if not m:
        # bare token → assume wiki
        bare = url.strip().strip("/").split("/")[-1].split("?")[0]
        return "wiki", bare
    kind = "docx" if m.group(1) in ("docx", "docs") else m.group(1)
    return kind, m.group(2)


# --- API wrappers (tenant token) ---


def read_document(domain: str, token: str, kind: str, doc_token: str,
                  want_comments: bool, want_media: bool) -> tuple[int, dict]:
    """Resolve + read a wiki/docx doc. Returns (exit_code, result_dict)."""
    obj_token, obj_type, title = doc_token, kind, ""

    if kind == "wiki":
        st, jb = _api("GET", f"{domain}/open-apis/wiki/v2/spaces/get_node?token={doc_token}", token)
        node = (jb.get("data") or {}).get("node") or {}
        if not node:
            return 4, {"ok": False, "error": f"cannot resolve wiki node ({jb.get('msg') or st})",
                       "denied": _classify(st, jb) == "denied"}
        obj_token = node.get("obj_token", doc_token)
        obj_type = node.get("obj_type", "docx")
        title = node.get("title", "")

    if obj_type not in ("docx", "doc"):
        # non-docx (sheet/bitable/...) — return what we know, agent notes it
        return 0, {"ok": True, "title": title, "obj_type": obj_type, "obj_token": obj_token,
                   "text": "", "blocks": 0, "images": [], "links": [], "comments": [],
                   "note": f"obj_type={obj_type} không phải docx — chỉ trả metadata"}

    # plain text (reliable)
    st, jb = _api("GET", f"{domain}/open-apis/docx/v1/documents/{obj_token}/raw_content", token)
    if jb.get("code") not in (0, None) or st >= 400:
        return 4, {"ok": False, "error": f"raw_content failed: {jb.get('msg') or st} "
                   f"(code={jb.get('code')})", "denied": _classify(st, jb) == "denied"}
    text = (jb.get("data") or {}).get("content", "")
    if not title:
        title = (text.splitlines()[0].strip() if text.strip() else obj_token)

    images, links = _scan_blocks(domain, token, obj_token)
    comments = _read_comments(domain, token, obj_token) if want_comments else []
    if want_media and images:
        _attach_media_urls(domain, token, images)

    return 0, {"ok": True, "title": title, "obj_type": obj_type, "obj_token": obj_token,
               "text": text, "blocks_image_count": len(images), "images": images,
               "links": links, "comments": comments}


def _scan_blocks(domain: str, token: str, doc_id: str) -> tuple[list, list]:
    """Walk the block tree to collect image tokens + embedded links/mentions."""
    images: list[dict] = []
    links: list[dict] = []
    page_token = ""
    for _ in range(50):  # safety cap on pagination
        url = f"{domain}/open-apis/docx/v1/documents/{doc_id}/blocks?page_size=500"
        if page_token:
            url += f"&page_token={page_token}"
        st, jb = _api("GET", url, token)
        data = jb.get("data") or {}
        for b in data.get("items", []):
            img = b.get("image") or {}
            if img.get("token"):
                images.append({"token": img["token"], "width": img.get("width"),
                               "height": img.get("height")})
            for key in ("text", "heading1", "heading2", "heading3", "bullet", "ordered"):
                for el in (b.get(key) or {}).get("elements", []) or []:
                    md = el.get("mention_doc") or {}
                    if md.get("url") or md.get("token"):
                        links.append({"type": "mention_doc", "url": md.get("url", ""),
                                      "title": md.get("title", "")})
                    tr = el.get("text_run") or {}
                    link = (tr.get("text_element_style") or {}).get("link") or {}
                    if link.get("url"):
                        links.append({"type": "link", "url": link["url"]})
        if not data.get("has_more"):
            break
        page_token = data.get("page_token", "")
        if not page_token:
            break
    return images, links


def _read_comments(domain: str, token: str, file_token: str) -> list:
    out: list[dict] = []
    page_token = ""
    for _ in range(20):
        url = (f"{domain}/open-apis/drive/v1/files/{file_token}/comments"
               f"?file_type=docx&page_size=50")
        if page_token:
            url += f"&page_token={page_token}"
        st, jb = _api("GET", url, token)
        data = jb.get("data") or {}
        for c in data.get("items", []):
            replies = (c.get("reply_list") or {}).get("replies", []) or []
            text = " / ".join(
                "".join(p.get("text_run", {}).get("text", "")
                        for p in (r.get("content") or {}).get("elements", []) or [])
                for r in replies
            )
            out.append({"comment_id": c.get("comment_id"),
                        "resolved": bool(c.get("is_solved")),
                        "quote": c.get("quote", ""), "text": text,
                        "reply_count": len(replies)})
        if not data.get("has_more"):
            break
        page_token = data.get("page_token", "")
        if not page_token:
            break
    return out


def _attach_media_urls(domain: str, token: str, images: list) -> None:
    toks = [i["token"] for i in images]
    for i in range(0, len(toks), 5):
        chunk = toks[i:i + 5]
        q = "&".join(f"file_tokens={t}" for t in chunk)
        st, jb = _api("GET", f"{domain}/open-apis/drive/v1/medias/batch_get_tmp_download_url?{q}",
                      token)
        for item in ((jb.get("data") or {}).get("tmp_download_urls") or []):
            for img in images:
                if img["token"] == item.get("file_token"):
                    img["tmp_url"] = item.get("tmp_download_url", "")


def _read_with_mode(domain, mode, kind, doc_token, want_comments, want_media):
    token, mode_used, err = get_read_token(domain, mode)
    if not token:
        return 2, {"ok": False, "error": err, "mode": mode_used}, mode_used
    code, res = read_document(domain, token, kind, doc_token, want_comments, want_media)
    res["mode"] = mode_used
    return code, res, mode_used


def main(argv=None):
    ap = argparse.ArgumentParser(description="Read a Lark wiki/docx document (dual-mode token)")
    ap.add_argument("url", help="Lark wiki/docx URL (or bare token)")
    ap.add_argument("--mode", default=None, choices=["auto", "tenant", "user"],
                    help="force a token mode; default = resolved read_mode from /qa:auth-lark")
    ap.add_argument("--no-comments", action="store_true", help="skip reading comments")
    ap.add_argument("--media-urls", action="store_true",
                    help="resolve temporary download URLs for inline images")
    args = ap.parse_args(argv)

    load_env()
    domain = env_str("LARK_DOMAIN", DEFAULT_DOMAIN).rstrip("/")
    avail = available_modes()
    if not avail["tenant"] and not avail["user"]:
        print(json.dumps({"ok": False, "error": "No Lark credentials configured — run "
                          "/qa:setup then /qa:auth-lark (tenant) and/or "
                          "/qa:auth-lark --login (user)."}, ensure_ascii=False))
        return 2

    kind, doc_token = parse_url(args.url)
    code, res, mode_used = _read_with_mode(domain, args.mode, kind, doc_token,
                                           not args.no_comments, args.media_urls)

    # Fallback: chosen mode denied the doc → retry with the other configured mode.
    if not res.get("ok") and res.get("denied"):
        alt = other_mode(mode_used)
        if avail.get(alt):
            code2, res2, _ = _read_with_mode(domain, alt, kind, doc_token,
                                             not args.no_comments, args.media_urls)
            if res2.get("ok"):
                res2["fallback_from"] = mode_used
                code, res = code2, res2

    res.setdefault("source_url", args.url)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return code


if __name__ == "__main__":
    sys.exit(main())
