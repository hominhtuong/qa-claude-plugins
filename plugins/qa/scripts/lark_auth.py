#!/usr/bin/env python3
"""Lark authentication + capability check — DUAL TOKEN MODE, cross-platform, stdlib-only.

Two ways to reach a Lark document, both supported and configurable in the plugin env:
  • TENANT mode (app token) — LARK_APP_ID + LARK_APP_SECRET → tenant_access_token. The
    DOCUMENT must be shared with the APP. This is the project default flow.
  • USER mode (user_access_token / UAT) — obtained once via OAuth (`--login`) and then
    auto-refreshed from a stored refresh token. The DOCUMENT must be visible to the USER.

What it does:
  1. Read credentials from .claude/qa-claude/.plugin.env.
  2. AUTHENTICATE every mode that is configured (tenant: always if app id/secret present;
     user: if a refresh token is stored).
  3. PROBE each mode's real capabilities (read Drive, read the configured Bitable board…).
  4. RESOLVE the effective read mode by preference LARK_TOKEN_MODE (auto|tenant|user):
     `auto` picks whichever mode has MORE granted read capabilities (tie → tenant); an
     explicit tenant/user is honoured if that mode is available.
  5. WRITE structured "lark info" both modes + resolved read_mode → lark-auth.state.json,
     plus LARK_READ_MODE / LARK_APP_CAPABILITIES / LARK_USER_CAPABILITIES env lines so
     commands & skills (and lark_read.py) know which token to use.
  6. CHECK vs COMMAND (`--command log-bug`): conflict if a required cap is denied in the
     resolved/best mode → report the exact scope to grant.

Usage:
    python3 lark_auth.py                        # auth all modes + probe + resolve + table
    python3 lark_auth.py --command plan-tests   # also fail (exit 3) if a required cap is denied
    python3 lark_auth.py --mode user            # set preference to user (auto|tenant|user)
    python3 lark_auth.py --login                # print the OAuth URL to grant a user token
    python3 lark_auth.py --login --code <CODE>  # exchange the OAuth code → store user refresh token
    python3 lark_auth.py --request bitable.read,bitable.write
    python3 lark_auth.py --json                 # machine-readable result
    python3 lark_auth.py --no-write             # don't touch state file / plugin env

Exit codes: 0 ok · 2 missing/invalid credentials · 3 capability conflict for --command.
NEVER prints the app secret, the access token, or the refresh token.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from _env import env_str, find_env_file, load_env, project_root

DEFAULT_DOMAIN = "https://open.larksuite.com"   # Feishu (CN): https://open.feishu.cn
STATE_NAME = "lark-auth.state.json"

# OAuth 2.0 (user token) endpoints + defaults. Override the redirect URI / scope via env
# (LARK_REDIRECT_URI / LARK_USER_SCOPE) to match what the app registered in its console.
OAUTH_TOKEN_PATH = "/open-apis/authen/v2/oauth/token"
OAUTH_AUTHORIZE_PATH = "/open-apis/authen/v1/authorize"
DEFAULT_REDIRECT_URI = "http://localhost:8080/callback"
DEFAULT_USER_SCOPE = ("offline_access docx:document:readonly wiki:wiki:readonly "
                      "drive:drive:readonly bitable:app:readonly")

# Read modes + the capabilities that matter for "which mode reads docs better".
TENANT, USER, AUTO = "tenant", "user", "auto"
READ_CAPS = ("wiki.read", "docx.read", "drive.read")

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


# ── USER mode (OAuth 2.0 user_access_token) ───────────────────────────────────────

def oauth_authorize_url(domain: str, app_id: str, redirect_uri: str, scope: str,
                        state: str = "qa-claude") -> str:
    """Build the consent URL the user opens once to grant a user token."""
    from urllib.parse import urlencode
    q = urlencode({"client_id": app_id, "redirect_uri": redirect_uri, "scope": scope,
                   "state": state, "response_type": "code"})
    return f"{domain}{OAUTH_AUTHORIZE_PATH}?{q}"


def oauth_exchange_code(domain: str, app_id: str, app_secret: str, code: str,
                        redirect_uri: str) -> tuple[str, str, int, str]:
    """Exchange an authorization code for (access_token, refresh_token, expire_epoch, err)."""
    body = {"grant_type": "authorization_code", "client_id": app_id,
            "client_secret": app_secret, "code": code, "redirect_uri": redirect_uri}
    st, jb = _api("POST", f"{domain}{OAUTH_TOKEN_PATH}", body=body)
    if jb.get("access_token"):
        return (jb["access_token"], jb.get("refresh_token", ""),
                int(time.time()) + int(jb.get("expires_in", 0)), "")
    return "", "", 0, f"{jb.get('error_description') or jb.get('msg') or st} (code={jb.get('code') or jb.get('error')})"


def user_token_from_refresh(domain: str, app_id: str, app_secret: str,
                            refresh_token: str) -> tuple[str, str, int, str]:
    """Refresh a user_access_token. Returns (access, new_refresh, expire_epoch, err).

    Lark may rotate the refresh token — the caller MUST persist new_refresh when set.
    """
    body = {"grant_type": "refresh_token", "client_id": app_id,
            "client_secret": app_secret, "refresh_token": refresh_token}
    st, jb = _api("POST", f"{domain}{OAUTH_TOKEN_PATH}", body=body)
    if jb.get("access_token"):
        return (jb["access_token"], jb.get("refresh_token", refresh_token),
                int(time.time()) + int(jb.get("expires_in", 0)), "")
    return "", "", 0, f"{jb.get('error_description') or jb.get('msg') or st} (code={jb.get('code') or jb.get('error')})"


def available_modes() -> dict:
    """Which token modes are configured (from env). Tenant: app id+secret. User: refresh token."""
    return {
        TENANT: bool(env_str("LARK_APP_ID") and env_str("LARK_APP_SECRET")),
        USER: bool(env_str("LARK_USER_REFRESH_TOKEN")),
    }


def get_tenant_token(domain: str) -> tuple[str, int, str]:
    """Tenant token from env credentials."""
    return authenticate(domain, env_str("LARK_APP_ID"), env_str("LARK_APP_SECRET"))


def get_user_token(domain: str, persist: bool = True) -> tuple[str, int, str]:
    """User token by refreshing the stored refresh token; persist a rotated refresh token."""
    app_id, secret = env_str("LARK_APP_ID"), env_str("LARK_APP_SECRET")
    refresh = env_str("LARK_USER_REFRESH_TOKEN")
    if not refresh:
        return "", 0, "no LARK_USER_REFRESH_TOKEN — run /qa:auth-lark --login first"
    if not (app_id and secret):
        return "", 0, "LARK_APP_ID / LARK_APP_SECRET required to refresh the user token"
    access, new_refresh, expire, err = user_token_from_refresh(domain, app_id, secret, refresh)
    if access and persist and new_refresh and new_refresh != refresh:
        env_path = find_env_file()
        if env_path:
            _upsert_env_key(env_path, "LARK_USER_REFRESH_TOKEN", new_refresh)
        os.environ["LARK_USER_REFRESH_TOKEN"] = new_refresh
    return access, expire, err


def resolve_read_mode(pref: str, caps_tenant: dict, caps_user: dict, avail: dict) -> tuple[str, str]:
    """Resolve the effective read mode. Returns (mode, reason)."""
    pref = (pref or AUTO).strip().lower()
    if pref in (TENANT, USER):
        if avail.get(pref):
            return pref, f"preference LARK_TOKEN_MODE={pref}"
        other = USER if pref == TENANT else TENANT
        if avail.get(other):
            return other, f"preferred {pref} not configured → fell back to {other}"
        return pref, f"preference {pref} (no mode configured)"
    # auto: pick the mode with more granted read caps; tie → tenant (project default)
    def score(caps):
        return sum(1 for c in READ_CAPS if caps.get(c) == GRANTED)
    st, su = score(caps_tenant), score(caps_user)
    if avail.get(USER) and not avail.get(TENANT):
        return USER, "auto: only user mode configured"
    if avail.get(TENANT) and not avail.get(USER):
        return TENANT, "auto: only tenant mode configured"
    if su > st:
        return USER, f"auto: user mode has more granted read caps ({su} > {st})"
    return TENANT, f"auto: tenant ≥ user read caps ({st} ≥ {su}) — project default"


def get_read_token(domain: str, mode_arg: str | None = None) -> tuple[str, str, str]:
    """For lark_read.py: return (token, mode_used, err) for the requested/resolved mode.

    Resolution: explicit mode_arg → state read_mode → env LARK_TOKEN_MODE → tenant.
    """
    avail = available_modes()
    mode = (mode_arg or "").strip().lower()
    if mode not in (TENANT, USER):
        mode = _state_read_mode() or env_str("LARK_TOKEN_MODE", AUTO).strip().lower()
    if mode not in (TENANT, USER):
        # unresolved 'auto' without a cached decision → prefer an available mode, tenant first
        mode = TENANT if avail.get(TENANT) else (USER if avail.get(USER) else TENANT)
    token, _exp, err = (get_user_token(domain) if mode == USER else get_tenant_token(domain))
    return token, mode, err


def other_mode(mode: str) -> str:
    return USER if mode == TENANT else TENANT


def _state_read_mode() -> str:
    """Read the cached resolved read_mode from the state file (best-effort)."""
    try:
        p = project_root() / ".claude" / "qa-claude" / STATE_NAME
        return json.loads(p.read_text(encoding="utf-8")).get("read_mode", "")
    except Exception:  # noqa: BLE001
        return ""


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


def _probe_mode(token: str, requested: list[str], domain: str, root: Path) -> dict:
    """Probe every requested capability with one mode's token."""
    caps = {}
    for cap in requested:
        scope, title, _ = CAPABILITIES[cap]
        caps[cap] = {"scope": scope, "title": title, "status": probe(cap, domain, token, root)}
    return caps


def run(requested: list[str], command: str | None, write: bool,
        pref_override: str | None = None) -> tuple[int, dict]:
    load_env()
    domain = env_str("LARK_DOMAIN", DEFAULT_DOMAIN).rstrip("/")
    app_id = env_str("LARK_APP_ID")
    root = project_root()
    avail = available_modes()

    if not avail[TENANT] and not avail[USER]:
        return 2, {"ok": False, "error": "No Lark credentials in .claude/qa-claude/.plugin.env — "
                   "set ENABLE_LARK_APP=true + LARK_APP_ID/LARK_APP_SECRET (tenant mode), and/or "
                   "run /qa:auth-lark --login (user mode). See /qa:setup-plugin."}

    # Persist the preference if the caller set one.
    pref = (pref_override or env_str("LARK_TOKEN_MODE", AUTO)).strip().lower()
    if pref not in (AUTO, TENANT, USER):
        pref = AUTO

    modes: dict = {}
    errors: dict = {}
    expires: dict = {}
    # TENANT
    if avail[TENANT]:
        t_tok, t_exp, t_err = get_tenant_token(domain)
        if t_tok:
            modes[TENANT] = _probe_mode(t_tok, requested, domain, root)
            expires[TENANT] = t_exp
        else:
            errors[TENANT] = t_err
    # USER
    if avail[USER]:
        u_tok, u_exp, u_err = get_user_token(domain)
        if u_tok:
            modes[USER] = _probe_mode(u_tok, requested, domain, root)
            expires[USER] = u_exp
        else:
            errors[USER] = u_err

    if not modes:
        return 2, {"ok": False, "app_id": app_id, "domain": domain,
                   "error": "authentication failed for all configured modes", "mode_errors": errors}

    caps_t = {k: v["status"] for k, v in modes.get(TENANT, {}).items()}
    caps_u = {k: v["status"] for k, v in modes.get(USER, {}).items()}
    read_mode, reason = resolve_read_mode(pref, caps_t, caps_u,
                                          {TENANT: TENANT in modes, USER: USER in modes})

    if write:
        state = {"app_id": app_id, "domain": domain, "checked_at": int(time.time()),
                 "token_mode_pref": pref, "read_mode": read_mode, "read_mode_reason": reason,
                 "modes": {m: {"available": True, "token_expire": expires.get(m, 0),
                               "capabilities": {k: v["status"] for k, v in caps.items()}}
                           for m, caps in modes.items()},
                 "mode_errors": errors}
        (root / ".claude" / "qa-claude" / STATE_NAME).write_text(
            json.dumps(state, indent=2) + "\n", encoding="utf-8")
        env_path = find_env_file()
        if env_path:
            _upsert_env_key(env_path, "LARK_TOKEN_MODE", pref)
            _upsert_env_key(env_path, "LARK_READ_MODE", read_mode)
            if TENANT in modes:
                usable = [k for k, v in caps_t.items() if v in (GRANTED, DECLARED)]
                _upsert_env_key(env_path, "LARK_APP_CAPABILITIES", ",".join(usable))
            if USER in modes:
                usable = [k for k, v in caps_u.items() if v in (GRANTED, DECLARED)]
                _upsert_env_key(env_path, "LARK_USER_CAPABILITIES", ",".join(usable))

    result = {"ok": True, "app_id": app_id, "domain": domain, "pref": pref,
              "read_mode": read_mode, "read_mode_reason": reason,
              "modes": modes, "mode_errors": errors}

    # Compare against the command's requirements — judge against the BEST status across modes.
    if command:
        reqs = COMMAND_REQS.get(command)
        if reqs is None:
            result["command"] = {"name": command, "note": "command needs no Lark capability"}
        else:
            def best(cap):
                vals = [m.get(cap, {}).get("status") for m in modes.values()]
                if GRANTED in vals or DECLARED in vals:
                    return GRANTED
                return DENIED if DENIED in vals else UNKNOWN
            conflicts = [{"capability": c, "scope": CAPABILITIES[c][0]}
                         for c in reqs if best(c) == DENIED]
            result["command"] = {"name": command, "required": reqs, "conflicts": conflicts}
            if conflicts:
                return 3, result
    return 0, result


def run_login(code: str | None, redirect_uri: str | None, scope: str | None,
              write: bool) -> tuple[int, dict]:
    """OAuth user-token flow: print the consent URL, or exchange a code for a refresh token."""
    load_env()
    domain = env_str("LARK_DOMAIN", DEFAULT_DOMAIN).rstrip("/")
    app_id, secret = env_str("LARK_APP_ID"), env_str("LARK_APP_SECRET")
    redirect_uri = redirect_uri or env_str("LARK_REDIRECT_URI", DEFAULT_REDIRECT_URI)
    scope = scope or env_str("LARK_USER_SCOPE", DEFAULT_USER_SCOPE)
    if not (app_id and secret):
        return 2, {"ok": False, "error": "LARK_APP_ID / LARK_APP_SECRET required for OAuth login"}

    if not code:
        url = oauth_authorize_url(domain, app_id, redirect_uri, scope)
        return 0, {"ok": True, "login_url": url, "redirect_uri": redirect_uri,
                   "next": "Open login_url, approve, copy the `code` from the redirected URL, "
                           "then re-run: /qa:auth-lark --login --code <CODE>"}

    access, refresh, _exp, err = oauth_exchange_code(domain, app_id, secret, code, redirect_uri)
    if not access or not refresh:
        return 2, {"ok": False, "error": f"OAuth code exchange failed: {err}",
                   "hint": "Check the code is fresh + redirect_uri matches the app console exactly"}
    if write:
        env_path = find_env_file()
        if env_path:
            _upsert_env_key(env_path, "LARK_USER_REFRESH_TOKEN", refresh)
            _upsert_env_key(env_path, "LARK_TOKEN_MODE", env_str("LARK_TOKEN_MODE", AUTO))
        os.environ["LARK_USER_REFRESH_TOKEN"] = refresh
    return 0, {"ok": True, "user_login": "stored a user refresh token",
               "next": "Re-run /qa:auth-lark to probe user-mode capabilities and resolve read_mode"}


def _print_human(res: dict) -> None:
    if not res.get("ok"):
        print(f"❌ {res.get('error')}", file=sys.stderr)
        if res.get("mode_errors"):
            for m, e in res["mode_errors"].items():
                print(f"   • {m}: {e}", file=sys.stderr)
        if res.get("hint"):
            print(f"   hint: {res['hint']}", file=sys.stderr)
        return

    # --login output
    if res.get("login_url"):
        print("🔗 Mở URL này để cấp quyền user token (đăng nhập + đồng ý):")
        print(f"   {res['login_url']}")
        print(f"\n   redirect_uri = {res['redirect_uri']} (phải khớp Redirect URL trong app console)")
        print(f"\n➡️  {res['next']}")
        return
    if res.get("user_login"):
        print(f"✅ {res['user_login']}")
        print(f"➡️  {res['next']}")
        return

    print(f"✅ Authenticated  app_id={res['app_id']}  domain={res['domain']}")
    print(f"🎯 Read mode = {res['read_mode']}  ({res.get('read_mode_reason','')})  · preference={res.get('pref')}")
    icon = {GRANTED: "✅", DENIED: "❌", DECLARED: "📜", UNKNOWN: "❔", SKIPPED: "➖"}
    for mode, caps in res["modes"].items():
        tag = "  ⭐ (read_mode)" if mode == res["read_mode"] else ""
        print(f"\n[{mode}] capabilities{tag}:")
        for cap, v in caps.items():
            print(f"  {icon.get(v['status'], '?')} {v['status']:8} {cap:14} {v['scope']:24} {v['title']}")
    for mode, err in (res.get("mode_errors") or {}).items():
        print(f"\n⚠️  [{mode}] not usable: {err}")
    cmd = res.get("command")
    if cmd:
        if cmd.get("conflicts"):
            print(f"\n⚠️  /{cmd['name']} CONFLICT — missing these permissions in ALL modes:")
            for c in cmd["conflicts"]:
                print(f"     • {c['capability']}  → grant scope `{c['scope']}` (tenant: app console; "
                      f"user: add to LARK_USER_SCOPE + re-login)")
            print("   Add the scope(s), re-publish / re-login, then re-run /qa:auth-lark.")
        elif "required" in cmd:
            print(f"\n✅ /{cmd['name']} — all required capabilities available "
                  f"({', '.join(cmd['required'])}).")
        else:
            print(f"\nℹ️  {cmd.get('note')}")
    print("\nLegend: ✅granted ❌denied 📜declared(not tested—write/upload) ❔unknown ➖skipped(no resource)")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Lark dual-mode auth + capability/permission check")
    ap.add_argument("--request", default="full",
                    help="'full' (default) or comma-list of capability keys to verify")
    ap.add_argument("--command", default=None,
                    help="check capabilities against this command's needs "
                         f"({', '.join(COMMAND_REQS)})")
    ap.add_argument("--mode", default=None, choices=[AUTO, TENANT, USER],
                    help="set the read-mode preference (auto|tenant|user); persisted to env")
    ap.add_argument("--login", action="store_true",
                    help="OAuth user-token flow: print the consent URL (or exchange with --code)")
    ap.add_argument("--code", default=None, help="OAuth authorization code (with --login)")
    ap.add_argument("--redirect-uri", default=None, help="OAuth redirect URI (must match app console)")
    ap.add_argument("--scope", default=None, help="OAuth user scope string (space-separated)")
    ap.add_argument("--no-write", action="store_true",
                    help="do not update the state file / plugin env")
    ap.add_argument("--json", action="store_true", help="print machine-readable JSON")
    args = ap.parse_args(argv)

    if args.login:
        code, res = run_login(args.code, args.redirect_uri, args.scope, write=not args.no_write)
        if args.json:
            print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            _print_human(res)
        return code

    if args.request.strip().lower() == "full":
        requested = list(CAPABILITIES)
    else:
        requested = [c.strip() for c in args.request.split(",") if c.strip()]
        bad = [c for c in requested if c not in CAPABILITIES]
        if bad:
            print(f"unknown capability: {', '.join(bad)}; valid: {', '.join(CAPABILITIES)}",
                  file=sys.stderr)
            return 2

    code, res = run(requested, args.command, write=not args.no_write, pref_override=args.mode)
    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        _print_human(res)
    return code


if __name__ == "__main__":
    sys.exit(main())
