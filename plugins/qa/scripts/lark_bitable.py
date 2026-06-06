#!/usr/bin/env python3
"""Read records from the active Lark Bitable board — for reporting commands, NOT the MCP.

Why Python instead of the Lark MCP: the same reason as lark_read.py — the MCP frequently
fails with token-expired (99991668); this helper re-authenticates the app on every run
(dual-mode tenant/user token via lark_auth, the SAME creds /qa:auth-lark verifies) so the
bug-board reads behind /qa:quality-report, /qa:release-gate, /qa:release-notes and
/qa:traceability are reliable in headless / cron contexts.

It reads the board id + field mapping from <project>/.claude/qa-claude/log-bug.config.yml
(active_board → base_id/table_id + the `fields:` logical→board-name map), lists every
record (paginated), maps each into the plugin's logical field names, and prints JSON.

Usage:
    python3 lark_bitable.py                       # all records of the active board
    python3 lark_bitable.py --board production     # a specific board alias
    python3 lark_bitable.py --status New,Open      # only these status values
    python3 lark_bitable.py --since 2026-05-01     # created on/after (created_time)
    python3 lark_bitable.py --until 2026-06-01     # created on/before
    python3 lark_bitable.py --sprint S12 --version 1.4.0
    python3 lark_bitable.py --summary             # add aggregate counts to the output

Output JSON: { ok, board:{alias,name,base_id,table_id,read_only}, total, returned,
               fields, records:[{record_id, url, fields:{<logical>:value,...}, created_time,
               last_modified_time}], summary?:{by_status,by_priority,by_type,by_platform} }

Exit codes: 0 ok · 2 missing/invalid credentials · 3 no/invalid board config · 4 read failed.
NEVER prints the app secret or the access token.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from _env import env_str, load_env, project_root, ssl_help_text
from lark_auth import (DEFAULT_DOMAIN, _api, available_modes, diagnose_error,
                       get_read_token, other_mode)

CONFIG_REL = ".claude/qa-claude/log-bug.config.yml"


# ── config parsing (no PyYAML dep — minimal indentation-aware parse) ───────────

def _strip_val(s: str) -> str:
    return s.split(":", 1)[1].strip().strip('"').strip("'") if ":" in s else ""


def read_config(root: Path, board_alias: str | None) -> dict:
    """Return the active board + field map from log-bug.config.yml.

    Mirrors the minimal-parse style of lark_auth._read_board_ids but also captures the
    full board entry (name/view_id/wiki_token/read_only) and the `fields:` mapping.
    """
    cfg = root / CONFIG_REL
    if not cfg.is_file():
        return {"ok": False, "error_code": "NO_CONFIG",
                "action": f"Missing {CONFIG_REL} — run /qa:setup, then fill the board ids."}

    active = ""
    boards: dict[str, dict] = {}
    fields: dict[str, str] = {}
    section = ""          # "boards" | "fields" | ""
    cur_board = ""
    for raw in cfg.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        s = line.strip()
        indent = len(line) - len(line.lstrip())
        if indent == 0:
            if s.startswith("active_board:"):
                active = _strip_val(s)
            elif s.startswith("boards:"):
                section, cur_board = "boards", ""
            elif s.startswith("fields:"):
                section = "fields"
            else:
                section = ""   # left boards/fields into another top-level key
            continue
        if section == "boards":
            if indent == 2 and s.endswith(":"):
                cur_board = s[:-1].strip()
                boards[cur_board] = {}
            elif cur_board and indent >= 4 and ":" in s:
                k = s.split(":", 1)[0].strip()
                boards[cur_board][k] = _strip_val(s)
        elif section == "fields" and indent == 2 and ":" in s:
            fields[s.split(":", 1)[0].strip()] = _strip_val(s)

    alias = board_alias or active
    if not alias or alias not in boards:
        return {"ok": False, "error_code": "NO_BOARD",
                "action": f"Board alias '{alias or '(empty active_board)'}' not found in {CONFIG_REL}."}
    b = boards[alias]
    if not b.get("base_id") or not b.get("table_id"):
        return {"ok": False, "error_code": "NO_BOARD_IDS",
                "action": f"Board '{alias}' is missing base_id/table_id in {CONFIG_REL}."}
    return {"ok": True, "alias": alias, "board": b,
            "fields": fields or _DEFAULT_FIELDS}


_URL_RE = re.compile(r"/(base|wiki|docx|sheets)/([A-Za-z0-9]+)")


def parse_board_url(url: str) -> dict:
    """Parse a Lark board URL → {kind, token, table_id, view_id}.

    Handles base URLs (…/base/<base_id>?table=…&view=…) and wiki-wrapped bases
    (…/wiki/<wiki_token>?table=…). The wiki token is resolved to the real base app
    token later (needs an auth token), see resolve_wiki_obj().
    """
    m = _URL_RE.search(urlparse(url).path if "://" in url else url)
    if not m:
        return {"kind": "", "token": "", "table_id": "", "view_id": ""}
    q = parse_qs(urlparse(url).query)
    return {"kind": m.group(1), "token": m.group(2),
            "table_id": (q.get("table") or [""])[0], "view_id": (q.get("view") or [""])[0]}


def resolve_wiki_obj(domain: str, token: str, wiki_token: str) -> str:
    """A wiki node wrapping a Bitable → the base app token (obj_token). '' on failure."""
    st, jb = _api("GET", f"{domain}/open-apis/wiki/v2/spaces/get_node?token={wiki_token}", token)
    if st == 200 and jb.get("code", 0) == 0:
        return jb.get("data", {}).get("node", {}).get("obj_token", "")
    return ""


# Fallback field map (matches templates/qa-claude/log-bug.config.yml) if `fields:` absent.
_DEFAULT_FIELDS = {
    "name": "Name of bug", "feature": "Tính năng", "platform": "Platform",
    "type": "Type", "priority": "Priority", "status": "Status",
    "dev_pic": "Dev PIC", "sprint": "Sprint", "version": "Version",
    "input_action": "Input data / Action", "expected": "Expected result",
    "attachment": "Attachment",
}


# ── bitable record listing ─────────────────────────────────────────────────────

def list_records(domain: str, token: str, base_id: str, table_id: str) -> tuple[bool, list, dict]:
    """List ALL records (paginated). Returns (ok, records, err_or_meta)."""
    out: list[dict] = []
    page_token = ""
    while True:
        url = (f"{domain}/open-apis/bitable/v1/apps/{base_id}/tables/{table_id}/records"
               f"?page_size=500")
        if page_token:
            url += f"&page_token={page_token}"
        st, jb = _api("GET", url, token)
        if st != 200 or jb.get("code", 0) != 0:
            return False, [], {"status": st, "body": jb}
        data = jb.get("data", {})
        out.extend(data.get("items", []) or [])
        if data.get("has_more") and data.get("page_token"):
            page_token = data["page_token"]
            continue
        return True, out, {}


def fetch_comments(domain: str, token: str, base_id: str, record_id: str) -> list:
    """Best-effort: list comments on one Bitable record. Returns [] on any failure."""
    url = (f"{domain}/open-apis/drive/v1/files/{base_id}/comments"
           f"?file_type=bitable&page_size=50&record_id={record_id}")
    st, jb = _api("GET", url, token)
    if st != 200 or jb.get("code", 0) != 0:
        return []
    out = []
    for c in (jb.get("data", {}).get("items", []) or []):
        replies = []
        for r in (c.get("reply_list", {}) or {}).get("replies", []) or []:
            content = r.get("content", {}) or {}
            txt = " ".join(e.get("text_run", {}).get("text", "")
                           for e in content.get("elements", []) or [])
            replies.append({"user_id": r.get("user_id", ""), "text": txt.strip()})
        out.append({"comment_id": c.get("comment_id", ""), "resolved": c.get("is_solved", False),
                    "replies": replies})
    return out


def _flatten(value):
    """Bitable cell values come in many shapes (str, list of text runs, person, link)."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return value
    if isinstance(value, dict):
        # text run / link / attachment-ish
        return value.get("text") or value.get("name") or value.get("link") or ""
    if isinstance(value, list):
        parts = [_flatten(v) for v in value]
        parts = [str(p) for p in parts if p not in ("", None)]
        return ", ".join(parts)
    return str(value)


def _to_epoch_ms(date_str: str, end_of_day: bool) -> int:
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    if end_of_day:
        dt = dt.replace(hour=23, minute=59, second=59)
    return int(dt.timestamp() * 1000)


# ── main ───────────────────────────────────────────────────────────────────────

def main(argv=None):
    ap = argparse.ArgumentParser(description="List records from the active Lark Bitable board")
    ap.add_argument("--board", default=None, help="board alias (default: active_board)")
    ap.add_argument("--mode", default=None, choices=["auto", "tenant", "user"],
                    help="force a token mode (default: resolved by /qa:auth-lark)")
    ap.add_argument("--status", default="", help="comma-separated status values to keep")
    ap.add_argument("--sprint", default="", help="keep only this sprint")
    ap.add_argument("--version", default="", help="keep only this version")
    ap.add_argument("--since", default="", help="created on/after YYYY-MM-DD")
    ap.add_argument("--until", default="", help="created on/before YYYY-MM-DD")
    ap.add_argument("--summary", action="store_true", help="add aggregate counts")
    ap.add_argument("--search", default="",
                    help="comma-separated keywords — keep records whose name/text contains ANY (case-insensitive)")
    ap.add_argument("--bug-id", default="", help="keep only the record whose bug-id field equals this number")
    ap.add_argument("--record-id", default="", help="keep only this record_id (recXXX)")
    ap.add_argument("--with-comments", action="store_true",
                    help="attach comments to each returned record (best-effort)")
    ap.add_argument("--url", default="",
                    help="read an ARBITRARY board by URL (…/base/<id>?table=… or …/wiki/<token>?table=…), bypassing config")
    args = ap.parse_args(argv)

    load_env()
    root = project_root()
    domain = env_str("LARK_DOMAIN", DEFAULT_DOMAIN).rstrip("/")

    avail = available_modes()
    if not avail["tenant"] and not avail["user"]:
        print(json.dumps({"ok": False, "error_code": "ENV_NO_CREDS",
                          "action": "No Lark credentials — run /qa:auth-lark."},
                         ensure_ascii=False, indent=2))
        return 2

    token, mode_used, err = get_read_token(domain, args.mode)
    if err:
        print(json.dumps({"ok": False, "error_code": "AUTH_FAILED", "action": err},
                         ensure_ascii=False, indent=2))
        return 2

    # Resolve the board — from --url (arbitrary) or from log-bug.config.yml (active/--board).
    if args.url:
        u = parse_board_url(args.url)
        if not u["kind"] or not u["table_id"]:
            print(json.dumps({"ok": False, "error_code": "BAD_URL",
                              "action": "URL must be a Lark board with a ?table=tbl… param (…/base/<id>?table=… or …/wiki/<token>?table=…)."},
                             ensure_ascii=False, indent=2))
            return 3
        if u["kind"] == "wiki":
            base_id = resolve_wiki_obj(domain, token, u["token"]) or \
                (resolve_wiki_obj(domain, get_read_token(domain, other_mode(mode_used))[0], u["token"])
                 if avail.get(other_mode(mode_used)) else "")
            wiki_token = u["token"]
        else:
            base_id, wiki_token = u["token"], ""
        table_id, view_id = u["table_id"], u["view_id"]
        if not base_id:
            print(json.dumps({"ok": False, "error_code": "WIKI_UNRESOLVED",
                              "action": "Could not resolve the wiki board to a base — share it with the app/user, then /qa:auth-lark, or pass a …/base/<id> URL."},
                             ensure_ascii=False, indent=2))
            return 4
        board = {"name": "(from url)", "base_id": base_id, "table_id": table_id,
                 "view_id": view_id, "wiki_token": wiki_token, "read_only": ""}
        cfg = {"alias": "(url)", "fields": _DEFAULT_FIELDS}
    else:
        cfg = read_config(root, args.board)
        if not cfg.get("ok"):
            print(json.dumps(cfg, ensure_ascii=False, indent=2))
            return 3
        board = cfg["board"]
        base_id, table_id = board["base_id"], board["table_id"]

    ok, items, meta = list_records(domain, token, base_id, table_id)
    if not ok and avail.get(other_mode(mode_used)):
        token2, _m, err2 = get_read_token(domain, other_mode(mode_used))
        if not err2:
            ok, items, meta = list_records(domain, token2, base_id, table_id)
    if not ok:
        ecode, action = diagnose_error(json.dumps(meta.get("body", {})))
        res = {"ok": False, "error_code": ecode, "action": action, "detail": meta.get("status")}
        if ecode == "SSL_CERT":
            res["ssl_help"] = ssl_help_text()
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 4

    fields_map = cfg["fields"]
    # invert: board-field-name → logical key
    inv = {v: k for k, v in fields_map.items() if v}

    status_keep = {s.strip() for s in args.status.split(",") if s.strip()}
    since_ms = _to_epoch_ms(args.since, False) if args.since else None
    until_ms = _to_epoch_ms(args.until, True) if args.until else None
    keywords = [k.strip().lower() for k in args.search.split(",") if k.strip()]
    bug_id = args.bug_id.strip().lstrip("#").lstrip("0") or args.bug_id.strip()  # tolerate BId-000427 → 427
    rec_keep = args.record_id.strip()

    view_id = board.get("view_id", "")
    wiki = board.get("wiki_token", "")

    def rec_url(rid: str) -> str:
        # best-effort deep link to the record
        if wiki:
            u = f"{domain}/wiki/{wiki}?table={table_id}"
        else:
            u = f"{domain}/base/{base_id}?table={table_id}"
        if view_id:
            u += f"&view={view_id}"
        if rid:
            u += f"&record={rid}"
        return u

    records = []
    for it in items:
        rid = it.get("record_id", "")
        raw_fields = it.get("fields", {}) or {}
        logical = {}
        for board_name, val in raw_fields.items():
            key = inv.get(board_name, board_name)
            logical[key] = _flatten(val)
        created = it.get("created_time") or 0
        modified = it.get("last_modified_time") or 0

        if rec_keep and rid != rec_keep:
            continue
        if status_keep and str(logical.get("status", "")) not in status_keep:
            continue
        if args.sprint and str(logical.get("sprint", "")) != args.sprint:
            continue
        if args.version and str(logical.get("version", "")) != args.version:
            continue
        if since_ms and created and created < since_ms:
            continue
        if until_ms and created and created > until_ms:
            continue
        if keywords:
            blob = " ".join(str(v) for v in logical.values()).lower()
            if not any(kw in blob for kw in keywords):
                continue
        if args.bug_id:
            # match any field that looks like a bug id / number, normalized (drop leading zeros + BId- prefix)
            cand = {str(v).lower().replace("bid-", "").lstrip("0") for v in logical.values()}
            if bug_id.lower() not in cand:
                continue

        rec = {
            "record_id": rid,
            "url": rec_url(rid),
            "fields": logical,
            "created_time": created,
            "last_modified_time": modified,
        }
        if args.with_comments and rid:
            rec["comments"] = fetch_comments(domain, token, base_id, rid)
        records.append(rec)

    out = {
        "ok": True,
        "board": {"alias": cfg["alias"], "name": board.get("name", ""),
                  "base_id": base_id, "table_id": table_id,
                  "read_only": str(board.get("read_only", "")).lower() in ("true", "1", "yes")},
        "mode_used": mode_used,
        "total": len(items),
        "returned": len(records),
        "fields": fields_map,
        "records": records,
    }

    if args.summary:
        def tally(key):
            agg: dict[str, int] = {}
            for r in records:
                v = str(r["fields"].get(key, "") or "—")
                agg[v] = agg.get(v, 0) + 1
            return dict(sorted(agg.items(), key=lambda kv: -kv[1]))
        out["summary"] = {
            "by_status": tally("status"),
            "by_priority": tally("priority"),
            "by_type": tally("type"),
            "by_platform": tally("platform"),
        }

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
