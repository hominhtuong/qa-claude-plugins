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
import re
import ssl
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from _env import (env_bool, env_str, find_env_file, is_ssl_cert_error, load_env,
                  make_ssl_context, project_root, ssl_help_text)

DEFAULT_DOMAIN = "https://open.larksuite.com"   # Feishu (CN): https://open.feishu.cn
STATE_NAME = "lark-auth.state.json"

# Throwaway document tokens used to probe a READ scope when no real doc is supplied: a
# missing scope returns a permission error regardless of the token; a present scope returns
# a harmless "not found", which we read as "the scope works". See _classify_read_scope.
_DUMMY_WIKI = "QAclaudeScopeProbeWikiToken0"
_DUMMY_DOCX = "QAclaudeScopeProbeDocxToken0"

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
    "docx.read":     ("docx:document:readonly", "Read Docx documents",           "docx_read"),
    "wiki.read":     ("wiki:wiki:readonly",   "Read Wiki nodes",                 "wiki_read"),
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

# Signals that specifically mean "this TOKEN lacks the required SCOPE" (vs. "this resource
# is gone / id is malformed", which means the scope itself is fine). Kept narrow on purpose
# so a throwaway-token probe of a read scope does not mis-report a not-found as denied.
_SCOPE_DENY_CODES = {99991672, 99991663, 99991679, 91403}
_SCOPE_DENY_WORDS = ("following scopes is required", "following scope is required",
                     "permission denied", "access denied", "no permission",
                     "unauthorized", "forbidden", "not authorized")


def creds_are_placeholder(app_id: str | None = None, secret: str | None = None) -> bool:
    """True when LARK_APP_ID/SECRET are empty or still the template placeholders.

    Catches the default `cli_xxxxxxxxxxxxxxxx` / `your_app_secret` so we fail with a clear
    "fill your credentials" message instead of letting Lark return an opaque 10003.
    """
    app_id = env_str("LARK_APP_ID") if app_id is None else (app_id or "")
    secret = env_str("LARK_APP_SECRET") if secret is None else (secret or "")
    app_id, secret = app_id.strip(), secret.strip()
    if not app_id or not secret:
        return True
    if secret.lower() in ("your_app_secret", "your_secret", "app_secret", "changeme"):
        return True
    if re.match(r"^cli_x{6,}$", app_id, re.I) or app_id.lower().startswith("cli_xxxx"):
        return True
    return False


def diagnose_error(text: str) -> tuple[str, str]:
    """Map a raw Lark/transport error string to (error_code, one-line actionable fix).

    Stable error_codes let skills/agents propose the exact next step instead of guessing:
      SSL_CERT · REDIRECT_MISMATCH · INVALID_PARAM · SCOPE_DENIED · DOC_DENIED · UNKNOWN
    """
    t = (text or "").lower()
    if is_ssl_cert_error(text):
        return ("SSL_CERT", "Chạy /qa:doctor --fix để tự cài truststore (dùng trust store của "
                "hệ điều hành — xong ngay). Nếu không cài được mới cần đặt SSL_CERT_FILE trong "
                ".plugin.env trỏ tới CA bundle (xem hướng dẫn SSL bên dưới).")
    if "20029" in t or "redirect" in t:
        return ("REDIRECT_MISMATCH", "Đặt LARK_REDIRECT_URI khớp ĐÚNG Redirect URL đã đăng "
                "ký trong app console rồi chạy lại /qa:auth-lark --login.")
    if "10003" in t or "invalid param" in t:
        return ("INVALID_PARAM", "Kiểm tra LARK_APP_ID/LARK_APP_SECRET (còn placeholder?) — "
                "đặt giá trị thật từ Developer Console → Credentials & Basic Info.")
    if any(w in t for w in ("following scopes is required", "following scope is required")) \
            or "scope" in t:
        return ("SCOPE_DENIED", "Cấp scope còn thiếu (Developer Console → Permissions & "
                "Scopes → publish; user mode: thêm vào LARK_USER_SCOPE + login lại).")
    if any(w in t for w in ("access denied", "permission", "forbidden", "no access")):
        return ("DOC_DENIED", "Chia sẻ tài liệu cho app (tenant mode) hoặc cho chính bạn "
                "(user mode), hoặc chạy /qa:auth-lark --login để dùng user token.")
    return ("UNKNOWN", "Chạy /qa:auth-lark để kiểm tra credential & quyền.")


_SSL_CTX = None  # built once; honours SSL_CERT_FILE / truststore from make_ssl_context()


def _ssl_context():
    global _SSL_CTX
    if _SSL_CTX is None:
        _SSL_CTX = make_ssl_context()
    return _SSL_CTX


def _api(method: str, url: str, token: str | None = None, body: dict | None = None) -> tuple[int, dict]:
    """Call a Lark endpoint. Returns (http_status, json_body). Never raises.

    On a TLS trust failure (corporate self-signed proxy) the body carries `_ssl_cert: True`
    so callers can surface the one-step SSL_CERT_FILE fix instead of a raw stacktrace.
    """
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20, context=_ssl_context()) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8", "replace") or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8", "replace") or "{}")
        except Exception:  # noqa: BLE001
            return e.code, {}
    except (ssl.SSLError, urllib.error.URLError) as e:  # TLS / network — flag SSL trust failures
        reason = getattr(e, "reason", e)
        msg = str(reason)
        out = {"_error": msg}
        if is_ssl_cert_error(msg):
            out["_ssl_cert"] = True
        return 0, out
    except Exception as e:  # noqa: BLE001 — anything else; treat as unknown, never crash
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
    """Which token modes are usable. Both need REAL (non-placeholder) app id+secret — the
    OAuth refresh of a user token also signs with the app credentials. Tenant additionally
    needs ENABLE_LARK_APP=true; user additionally needs a stored refresh token.
    """
    real = not creds_are_placeholder()
    return {
        TENANT: bool(real and env_bool("ENABLE_LARK_APP")),
        USER: bool(real and env_str("LARK_USER_REFRESH_TOKEN")),
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


def _classify_read_scope(status: int, jb: dict) -> str:
    """Classify a READ-scope probe: does the TOKEN actually hold the scope?

    A real read probe may hit a throwaway/non-existent document, so we must NOT treat a
    plain not-found as failure. Only a genuine permission/scope signal counts as DENIED;
    any other (non-network) API response means the scope itself works → GRANTED.
    """
    code = jb.get("code")
    if code == 0:
        return GRANTED
    if jb.get("_error"):  # network / DNS / TLS — can't conclude anything about the scope
        return UNKNOWN
    msg = str(jb.get("msg", "")).lower()
    if status == 403 or code in _SCOPE_DENY_CODES or any(w in msg for w in _SCOPE_DENY_WORDS):
        return DENIED
    return GRANTED  # got a non-permission API error (not-found / bad id) → scope is present


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


_DOC_TOKEN_RE = re.compile(r"/(wiki|docx|docs|sheets|base|file)/([A-Za-z0-9]+)")


def _parse_doc_token(url: str) -> tuple[str, str]:
    """Best-effort (kind, token) from a Lark URL or bare token (mirrors lark_read.parse_url)."""
    from urllib.parse import urlparse
    m = _DOC_TOKEN_RE.search(urlparse(url).path if "://" in url else url)
    if not m:
        bare = url.strip().strip("/").split("/")[-1].split("?")[0]
        return "wiki", bare
    kind = "docx" if m.group(1) in ("docx", "docs") else m.group(1)
    return kind, m.group(2)


def _probe_targets(domain: str, token: str, probe_doc: str) -> dict:
    """Resolve which wiki node / docx document the read probes should hit.

    With a real --probe-doc the read scopes are tested against a document the user can open
    (a clean GRANTED on success). Without one, throwaway tokens still surface a missing
    scope (permission error) while a present scope returns a harmless not-found.
    """
    targets = {"wiki": _DUMMY_WIKI, "docx": _DUMMY_DOCX}
    probe_doc = (probe_doc or "").strip()
    if not probe_doc:
        return targets
    kind, tok = _parse_doc_token(probe_doc)
    if kind == "wiki":
        targets["wiki"] = tok
        st, jb = _api("GET", f"{domain}/open-apis/wiki/v2/spaces/get_node?token={tok}", token)
        obj = ((jb.get("data") or {}).get("node") or {}).get("obj_token")
        if obj:
            targets["docx"] = obj
    elif kind in ("docx", "docs"):
        targets["docx"] = tok
    return targets


def probe(cap: str, domain: str, token: str, root: Path, targets: dict) -> str:
    """Non-destructively probe one capability. Returns a status constant.

    READ caps (wiki/docx/drive) do a real, harmless GET and are classified with
    _classify_read_scope so a missing scope shows as DENIED (never the old 'declared').
    WRITE/upload caps stay DECLARED — they can't be verified without creating data.
    """
    kind = CAPABILITIES[cap][2]
    if kind is None:
        return DECLARED
    if kind == "drive_read":
        st, jb = _api("GET", f"{domain}/open-apis/drive/v1/files?page_size=1", token)
        return _classify_read_scope(st, jb)
    if kind == "docx_read":
        doc = targets.get("docx") or _DUMMY_DOCX
        st, jb = _api("GET", f"{domain}/open-apis/docx/v1/documents/{doc}/raw_content", token)
        return _classify_read_scope(st, jb)
    if kind == "wiki_read":
        node = targets.get("wiki") or _DUMMY_WIKI
        st, jb = _api("GET", f"{domain}/open-apis/wiki/v2/spaces/get_node?token={node}", token)
        return _classify_read_scope(st, jb)
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


def _probe_mode(token: str, requested: list[str], domain: str, root: Path,
                probe_doc: str = "") -> dict:
    """Probe every requested capability with one mode's token."""
    targets = _probe_targets(domain, token, probe_doc)
    caps = {}
    for cap in requested:
        scope, title, _ = CAPABILITIES[cap]
        caps[cap] = {"scope": scope, "title": title,
                     "status": probe(cap, domain, token, root, targets)}
    return caps


def _no_creds_error() -> dict:
    """Tailored exit-2 payload distinguishing placeholder vs disabled vs empty credentials."""
    if creds_are_placeholder():
        return {"ok": False, "error_code": "CREDS_PLACEHOLDER",
                "error": "Chưa điền credential Lark thật. Mở .claude/qa-claude/.plugin.env, "
                "đặt ENABLE_LARK_APP=true + LARK_APP_ID/LARK_APP_SECRET (Developer Console → "
                "Credentials & Basic Info) — giá trị cli_xxx / your_app_secret là placeholder.",
                "action": "Điền LARK_APP_ID + LARK_APP_SECRET thật và ENABLE_LARK_APP=true."}
    if not env_bool("ENABLE_LARK_APP") and not env_str("LARK_USER_REFRESH_TOKEN"):
        return {"ok": False, "error_code": "APP_DISABLED",
                "error": "Credential có vẻ hợp lệ nhưng ENABLE_LARK_APP=false. Đặt "
                "ENABLE_LARK_APP=true trong .plugin.env (hoặc /qa:auth-lark --login cho user mode).",
                "action": "Đặt ENABLE_LARK_APP=true rồi chạy lại /qa:auth-lark."}
    return {"ok": False, "error_code": "ENV_NO_CREDS",
            "error": "No Lark credentials in .claude/qa-claude/.plugin.env — set "
            "ENABLE_LARK_APP=true + LARK_APP_ID/LARK_APP_SECRET (tenant), and/or run "
            "/qa:auth-lark --login (user). See /qa:setup.",
            "action": "Chạy /qa:setup rồi điền credential Lark."}


def run(requested: list[str], command: str | None, write: bool,
        pref_override: str | None = None, probe_doc: str = "") -> tuple[int, dict]:
    load_env()
    domain = env_str("LARK_DOMAIN", DEFAULT_DOMAIN).rstrip("/")
    app_id = env_str("LARK_APP_ID")
    root = project_root()
    avail = available_modes()
    probe_doc = probe_doc or env_str("LARK_PROBE_DOC")

    if not avail[TENANT] and not avail[USER]:
        return 2, _no_creds_error()

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
            modes[TENANT] = _probe_mode(t_tok, requested, domain, root, probe_doc)
            expires[TENANT] = t_exp
        else:
            errors[TENANT] = t_err
    # USER
    if avail[USER]:
        u_tok, u_exp, u_err = get_user_token(domain)
        if u_tok:
            modes[USER] = _probe_mode(u_tok, requested, domain, root, probe_doc)
            expires[USER] = u_exp
        else:
            errors[USER] = u_err

    if not modes:
        # All configured modes failed to even authenticate — classify the first error so the
        # message is actionable (SSL trust / invalid creds / redirect) rather than raw text.
        first_err = next(iter(errors.values()), "")
        ecode, action = diagnose_error(first_err)
        return 2, {"ok": False, "app_id": app_id, "domain": domain,
                   "error": "authentication failed for all configured modes",
                   "error_code": ecode, "action": action, "mode_errors": errors}

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
    # Did the redirect come from a real source (flag/env) or are we silently defaulting?
    redirect_explicit = bool(redirect_uri or env_str("LARK_REDIRECT_URI"))
    redirect_uri = redirect_uri or env_str("LARK_REDIRECT_URI", DEFAULT_REDIRECT_URI)
    scope = scope or env_str("LARK_USER_SCOPE", DEFAULT_USER_SCOPE)
    if creds_are_placeholder(app_id, secret):
        return 2, {"ok": False, "error_code": "CREDS_PLACEHOLDER",
                   "error": "OAuth login cần LARK_APP_ID/LARK_APP_SECRET thật (đang là "
                   "placeholder). Mở .plugin.env điền credential từ Developer Console.",
                   "action": "Điền LARK_APP_ID + LARK_APP_SECRET thật rồi chạy lại."}

    redirect_warning = None
    if not redirect_explicit:
        redirect_warning = (f"⚠️  Đang dùng redirect_uri mặc định {DEFAULT_REDIRECT_URI}. Giá trị "
                            "này PHẢI khớp ĐÚNG một Redirect URL đã đăng ký trong app console "
                            "(Security Settings → Redirect URLs). Nếu app bạn đăng ký URL khác "
                            "(vd :3000/callback), đặt LARK_REDIRECT_URI trong .plugin.env, nếu "
                            "không sẽ gặp lỗi 20029.")

    if not code:
        url = oauth_authorize_url(domain, app_id, redirect_uri, scope)
        return 0, {"ok": True, "login_url": url, "redirect_uri": redirect_uri,
                   "redirect_warning": redirect_warning,
                   "next": "Open login_url, approve, copy the `code` from the redirected URL, "
                           "then re-run: /qa:auth-lark --login --code <CODE>"}

    access, refresh, _exp, err = oauth_exchange_code(domain, app_id, secret, code, redirect_uri)
    if not access or not refresh:
        ecode, action = diagnose_error(err)
        hint = action if ecode in ("REDIRECT_MISMATCH", "SSL_CERT", "INVALID_PARAM") else \
            "Kiểm tra code còn mới + redirect_uri khớp ĐÚNG app console."
        return 2, {"ok": False, "error": f"OAuth code exchange failed: {err}",
                   "error_code": ecode, "action": action, "hint": hint,
                   "redirect_uri": redirect_uri}
    if write:
        env_path = find_env_file()
        if env_path:
            _upsert_env_key(env_path, "LARK_USER_REFRESH_TOKEN", refresh)
            _upsert_env_key(env_path, "LARK_TOKEN_MODE", env_str("LARK_TOKEN_MODE", AUTO))
            _upsert_env_key(env_path, "LARK_REDIRECT_URI", redirect_uri)  # remember what worked
        os.environ["LARK_USER_REFRESH_TOKEN"] = refresh
        os.environ["LARK_REDIRECT_URI"] = redirect_uri
    return 0, {"ok": True, "user_login": "stored a user refresh token",
               "redirect_uri": redirect_uri,
               "next": "Re-run /qa:auth-lark to probe user-mode capabilities and resolve read_mode"}


def _print_human(res: dict) -> None:
    if not res.get("ok"):
        print(f"❌ {res.get('error')}", file=sys.stderr)
        if res.get("error_code"):
            print(f"   [{res['error_code']}]", file=sys.stderr)
        if res.get("mode_errors"):
            for m, e in res["mode_errors"].items():
                print(f"   • {m}: {e}", file=sys.stderr)
        if res.get("action"):
            print(f"   → {res['action']}", file=sys.stderr)
        if res.get("hint"):
            print(f"   hint: {res['hint']}", file=sys.stderr)
        # Surface the full one-step SSL fix whenever a TLS trust failure is involved.
        if res.get("error_code") == "SSL_CERT" or any(
                is_ssl_cert_error(str(e)) for e in (res.get("mode_errors") or {}).values()):
            print("\n" + ssl_help_text(), file=sys.stderr)
        return

    # --login output
    if res.get("login_url"):
        print("🔗 Mở URL này để cấp quyền user token (đăng nhập + đồng ý):")
        print(f"   {res['login_url']}")
        print(f"\n   redirect_uri = {res['redirect_uri']} (phải khớp Redirect URL trong app console)")
        if res.get("redirect_warning"):
            print(f"\n{res['redirect_warning']}")
        print(f"\n➡️  {res['next']}")
        return
    if res.get("user_login"):
        print(f"✅ {res['user_login']}")
        if res.get("redirect_uri"):
            print(f"   redirect_uri đã lưu vào .plugin.env: {res['redirect_uri']}")
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
    print("\nLegend: ✅granted(tested) ❌denied 📜declared(write/upload—can't test non-destructively) "
          "❔unknown ➖skipped(no resource)")


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
    ap.add_argument("--probe-doc", default=None,
                    help="test docx/wiki read scopes against this real doc URL "
                         "(default LARK_PROBE_DOC; else a throwaway token still detects a missing scope)")
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

    code, res = run(requested, args.command, write=not args.no_write, pref_override=args.mode,
                    probe_doc=args.probe_doc or "")
    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        _print_human(res)
    return code


if __name__ == "__main__":
    sys.exit(main())
