#!/usr/bin/env python3
"""Lark app authentication + capability/permission check — cross-platform, stdlib-only.

What it does (the flow QAButler / F2KB use, distilled):
  1. Read LARK_APP_ID + LARK_APP_SECRET (+ LARK_DOMAIN) from the plugin env
     (.claude/qa-claude/.plugin.env).
  2. AUTHENTICATE: exchange them for a tenant_access_token (proves the credentials
     are valid) and cache the token + expiry to .claude/qa-claude/lark-auth.state.json.
  3. REFRESH CAPABILITIES: probe what the app id can actually do (read Drive, read the
     configured Bitable board, ...) and write the resolved capability set back to the
     state file + a LARK_APP_CAPABILITIES summary line in the plugin env.
  4. CHECK vs COMMAND: compare the app's capabilities against what a command needs
     (`--command log-bug`); if a required capability is DENIED, report the conflict +
     the exact scope to grant in the Lark Developer Console. Default request = `full`.

Usage:
    python3 lark_auth.py                       # auth + probe + print capability table
    python3 lark_auth.py --command log-bug     # also fail (exit 3) if a required cap is denied
    python3 lark_auth.py --request full         # request/verify every capability (default)
    python3 lark_auth.py --request bitable.read,bitable.write
    python3 lark_auth.py --json                 # machine-readable result
    python3 lark_auth.py --no-write             # don't touch state file / plugin env

Exit codes: 0 ok · 2 missing/invalid credentials · 3 capability conflict for --command.
NEVER prints the app secret or the access token.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from _env import env_str, find_env_file, load_env, project_root

DEFAULT_DOMAIN = "https://open.larksuite.com"   # Feishu (CN): https://open.feishu.cn
STATE_NAME = "lark-auth.state.json"

# Status values a capability can resolve to.
GRANTED, DENIED, UNKNOWN, SKIPPED, DECLARED = "granted", "denied", "unknown", "skipped", "declared"

# Capability registry: key -> (Lark scope, human title, probe kind | None).
# Probe kind None = cannot be verified non-destructively (e.g. a write would create a
# record); it is reported as DECLARED — trusted from the granted-scope list, not tested.
CAPABILITIES = {
    "bitable.read":  ("bitable:app:readonly", "Read Bitable (fields/records)",   "bitable_read"),
    "bitable.write": ("bitable:app",          "Create/update Bitable records",   None),
    "drive.read":    ("drive:drive:readonly", "Read Drive files / documents",    "drive_read"),
    "drive.upload":  ("drive:drive",          "Upload attachments to Drive",     None),
    "docx.read":     ("docx:document:readonly", "Read Docx documents",           None),
    "wiki.read":     ("wiki:wiki:readonly",   "Read Wiki nodes",                 None),
}

# Which capabilities each Lark-touching command needs.
COMMAND_REQS = {
    "log-bug":      ["bitable.read", "bitable.write", "drive.upload"],
    "update-board": ["bitable.read"],
    "plan-tests":   ["wiki.read", "docx.read", "drive.read"],
    "exploratory":  ["wiki.read", "docx.read", "drive.read"],  # reads a Lark spec into the oracle
    "analyze-spec": ["wiki.read", "docx.read", "drive.read"],
}

# Lark error codes / signals that mean "the app lacks this permission" (best-effort;
# codes vary across endpoints, so we also treat HTTP 403 + permission-ish messages as denial).
_DENY_CODES = {99991679, 99991668, 99991663, 1254302, 1254040, 131006, 131005, 91403, 234001}
_DENY_WORDS = ("permission", "no access", "access denied", "forbidden", "scope", "unauthorized")


def _api(method: str, url: str, token: str | None = None, body: dict | None = None) -> tuple[int, dict]:
    """Call a Lark endpoint. Returns (http_status, json_body). Never raises."""
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8", "replace") or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8", "replace") or "{}")
        except Exception:  # noqa: BLE001
            return e.code, {}
    except Exception as e:  # noqa: BLE001 — network/DNS; treat as unknown, never crash
        return 0, {"_error": str(e)}


def authenticate(domain: str, app_id: str, app_secret: str) -> tuple[str, int, str]:
    """Exchange app id/secret for a tenant_access_token.

    Returns (token, expire_epoch, error_msg). On failure token == "" and error_msg is set.
    """
    url = f"{domain}/open-apis/auth/v3/tenant_access_token/internal"
    status, jb = _api("POST", url, body={"app_id": app_id, "app_secret": app_secret})
    if jb.get("code") == 0 and jb.get("tenant_access_token"):
        return jb["tenant_access_token"], int(time.time()) + int(jb.get("expire", 0)), ""
    msg = jb.get("msg") or jb.get("_error") or f"HTTP {status}"
    return "", 0, f"{msg} (code={jb.get('code')})"


def _classify(status: int, jb: dict) -> str:
    """Map an API response to GRANTED / DENIED / UNKNOWN for a probe."""
    code = jb.get("code")
    if code == 0:
        return GRANTED
    msg = str(jb.get("msg", "")).lower()
    if status == 403 or code in _DENY_CODES or any(w in msg for w in _DENY_WORDS):
        return DENIED
    return UNKNOWN  # e.g. resource-not-found / bad id — the scope itself may be fine


def _read_board_ids(root: Path) -> tuple[str, str]:
    """Best-effort (base_id, table_id) of the active board from log-bug.config.yml.

    Minimal line parse (no PyYAML dep): find `active_board:` then that board's first
    non-empty base_id / table_id. Returns ("","") if unavailable.
    """
    cfg = root / ".claude" / "qa-claude" / "log-bug.config.yml"
    if not cfg.is_file():
        return "", ""

    def _val(s: str) -> str:
        return s.split(":", 1)[1].strip().strip('"').strip("'")

    active, cur, base, table = "", "", "", ""
    for raw in cfg.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        s = line.strip()
        if s.startswith("active_board:"):
            active = _val(s)
        # a board alias is a key nested exactly one level under `boards:` (2-space indent).
        elif line.startswith("  ") and not line.startswith("    ") and s.endswith(":"):
            cur = s[:-1].strip()
        elif active and cur == active:  # deeper lines belong to the active board
            if s.startswith("base_id:") and not base:
                base = _val(s)
            elif s.startswith("table_id:") and not table:
                table = _val(s)
    return base, table


def probe(cap: str, domain: str, token: str, root: Path) -> str:
    """Non-destructively probe one capability. Returns a status constant."""
    kind = CAPABILITIES[cap][2]
    if kind is None:
        return DECLARED
    if kind == "drive_read":
        st, jb = _api("GET", f"{domain}/open-apis/drive/v1/files?page_size=1", token)
        return _classify(st, jb)
    if kind == "bitable_read":
        base, table = _read_board_ids(root)
        if not base:
            return SKIPPED  # no board configured yet — nothing to probe against
        url = f"{domain}/open-apis/bitable/v1/apps/{base}"
        if table:
            url = f"{domain}/open-apis/bitable/v1/apps/{base}/tables/{table}/fields?page_size=1"
        st, jb = _api("GET", url, token)
        return _classify(st, jb)
    return SKIPPED


def _upsert_env_key(env_path: Path, key: str, value: str) -> None:
    """Set KEY=value in the plugin env file (add the line if absent). Leaves the rest intact."""
    lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.is_file() else []
    out, done = [], False
    for ln in lines:
        if ln.strip().split("=", 1)[0].strip() == key and not ln.strip().startswith("#"):
            out.append(f"{key}={value}")
            done = True
        else:
            out.append(ln)
    if not done:
        if out and out[-1].strip():
            out.append("")
        out.append(f"# auto-managed by /qa:auth-lark — do not hand-edit")
        out.append(f"{key}={value}")
    env_path.write_text("\n".join(out) + "\n", encoding="utf-8")


def run(requested: list[str], command: str | None, write: bool) -> tuple[int, dict]:
    load_env()
    domain = env_str("LARK_DOMAIN", DEFAULT_DOMAIN).rstrip("/")
    app_id = env_str("LARK_APP_ID")
    app_secret = env_str("LARK_APP_SECRET")
    root = project_root()

    if not app_id or not app_secret:
        return 2, {"ok": False, "error": "LARK_APP_ID / LARK_APP_SECRET not set in "
                   ".claude/qa-claude/.plugin.env — run /qa:setup-plugin and fill the LARK APP section"}

    token, expire, err = authenticate(domain, app_id, app_secret)
    if not token:
        return 2, {"ok": False, "app_id": app_id, "error": f"authentication failed: {err}"}

    caps = {}
    for cap in requested:
        scope, title, _ = CAPABILITIES[cap]
        caps[cap] = {"scope": scope, "title": title, "status": probe(cap, domain, token, root)}

    # Refresh permissions: persist token (for reuse) + resolved capabilities.
    if write:
        state = {"app_id": app_id, "domain": domain, "token_expire": expire,
                 "checked_at": int(time.time()),
                 "capabilities": {k: v["status"] for k, v in caps.items()}}
        (root / ".claude" / "qa-claude" / STATE_NAME).write_text(
            json.dumps(state, indent=2) + "\n", encoding="utf-8")
        env_path = find_env_file()
        if env_path:
            usable = [k for k, v in caps.items() if v["status"] in (GRANTED, DECLARED)]
            _upsert_env_key(env_path, "LARK_APP_CAPABILITIES", ",".join(usable))

    result = {"ok": True, "app_id": app_id, "domain": domain, "capabilities": caps}

    # Compare against the command's requirements.
    if command:
        reqs = COMMAND_REQS.get(command)
        if reqs is None:
            result["command"] = {"name": command, "note": "command needs no Lark capability"}
        else:
            conflicts = [{"capability": c, "scope": CAPABILITIES[c][0]}
                         for c in reqs if caps.get(c, {}).get("status") == DENIED]
            result["command"] = {"name": command, "required": reqs, "conflicts": conflicts}
            if conflicts:
                return 3, result
    return 0, result


def _print_human(res: dict) -> None:
    if not res.get("ok"):
        print(f"❌ {res.get('error')}", file=sys.stderr)
        return
    print(f"✅ Authenticated  app_id={res['app_id']}  domain={res['domain']}")
    icon = {GRANTED: "✅", DENIED: "❌", DECLARED: "📜", UNKNOWN: "❔", SKIPPED: "➖"}
    print("\nCapabilities:")
    for cap, v in res["capabilities"].items():
        print(f"  {icon.get(v['status'], '?')} {v['status']:8} {cap:14} {v['scope']:24} {v['title']}")
    cmd = res.get("command")
    if cmd:
        if cmd.get("conflicts"):
            print(f"\n⚠️  /{cmd['name']} CONFLICT — the app id is missing these permissions:")
            for c in cmd["conflicts"]:
                print(f"     • {c['capability']}  → grant scope `{c['scope']}` in the Lark Developer Console")
            print("   Add the scope(s), re-publish the app version, then re-run /qa:auth-lark.")
        elif "required" in cmd:
            print(f"\n✅ /{cmd['name']} — all required capabilities available "
                  f"({', '.join(cmd['required'])}).")
        else:
            print(f"\nℹ️  {cmd.get('note')}")
    print("\nLegend: ✅granted ❌denied 📜declared(not tested—write/upload) ❔unknown ➖skipped(no resource)")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Lark app auth + capability/permission check")
    ap.add_argument("--request", default="full",
                    help="'full' (default) or comma-list of capability keys to verify")
    ap.add_argument("--command", default=None,
                    help="check the app's capabilities against this command's needs "
                         f"({', '.join(COMMAND_REQS)})")
    ap.add_argument("--no-write", action="store_true",
                    help="do not update the state file / plugin env")
    ap.add_argument("--json", action="store_true", help="print machine-readable JSON")
    args = ap.parse_args(argv)

    if args.request.strip().lower() == "full":
        requested = list(CAPABILITIES)
    else:
        requested = [c.strip() for c in args.request.split(",") if c.strip()]
        bad = [c for c in requested if c not in CAPABILITIES]
        if bad:
            print(f"unknown capability: {', '.join(bad)}; valid: {', '.join(CAPABILITIES)}",
                  file=sys.stderr)
            return 2

    code, res = run(requested, args.command, write=not args.no_write)
    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        _print_human(res)
    return code


if __name__ == "__main__":
    sys.exit(main())
