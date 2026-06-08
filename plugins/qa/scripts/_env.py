"""Shared .plugin.env loader for the `qa` plugin scripts (cross-platform, stdlib-only).

Secrets live in the project's .claude/qa-claude/.plugin.env (git-ignored), never in the
plugin. Named `.plugin.env` so it never collides with the project's own ./.env. This
module finds that file (walking up from cwd) and loads it into os.environ.

Key names follow a stable convention (see templates/.plugin.env.example):
    ENABLE_LARK_NOTIFY, LARK_WEBHOOK_URL, LARK_WEBHOOK_SECRET, LARK_PLATFORM, LARK_USER
    ENABLE_CF_PUSH, CF_ACCOUNT_ID, CF_API_TOKEN, CF_R2_BUCKET, CF_R2_DOMAIN, CF_R2_PREFIX
"""
from __future__ import annotations  # allow `Path | None` on Python 3.8/3.9

import os
import sys
from pathlib import Path


def ensure_utf8_io() -> None:
    """Force UTF-8 on stdout/stderr so emoji + Vietnamese diacritics never crash the run.

    On a legacy Windows console (cp1252) `print()` of non-ASCII raises UnicodeEncodeError,
    which would abort scripts whose stdout is a contract (e.g. lark_read.py's JSON). Safe +
    idempotent on macOS/Linux. Runs once at import so every plugin script is covered.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # Python 3.7+
        except Exception:  # noqa: BLE001 — older Python / non-reconfigurable stream
            pass


ensure_utf8_io()


def project_root() -> Path:
    """Best-effort project root: $CLAUDE_PROJECT_DIR, else current working dir."""
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())


def find_env_file() -> Path | None:
    """Locate the plugin's .plugin.env (kept separate from the project's own ./.env).

    Order: $QA_ENV_FILE → walking up from cwd (and $CLAUDE_PROJECT_DIR), preferring
    `.claude/qa-claude/.plugin.env`, then the legacy `.claude/qa-claude/.env` (pre-0.0.5),
    then a bare `./.env` (last-resort fallback).
    """
    override = os.environ.get("QA_ENV_FILE")
    if override:
        p = Path(override)
        return p if p.is_file() else None
    here = Path(os.getcwd()).resolve()
    roots = [here, *here.parents]
    proj = os.environ.get("CLAUDE_PROJECT_DIR")
    if proj:
        roots = [Path(proj).resolve(), *roots]
    for d in roots:
        for candidate in (d / ".claude" / "qa-claude" / ".plugin.env",
                          d / ".claude" / "qa-claude" / ".env",
                          d / ".env"):
            if candidate.is_file():
                return candidate
    return None


def strip_inline_comment(value: str) -> str:
    """Drop a trailing ` # comment` from an env value WITHOUT touching a `#` that is part
    of the value (no whitespace before it — e.g. a secret `ab#cd`, a colour `#FF0000`, or
    a URL fragment). The `#` only starts a comment when preceded by a space or tab, and
    never inside a quoted span.

    Examples:
        "https://open.larksuite.com   # Feishu" -> "https://open.larksuite.com"
        "ab#cd"                                  -> "ab#cd"   (no space before #)
        "#FF0000"                                -> "#FF0000" (# at start = literal)
        '"a # b"  # tail'                        -> '"a # b"'  (# inside quotes kept)
    """
    out = []
    quote = ""
    for i, ch in enumerate(value):
        if quote:
            out.append(ch)
            if ch == quote:
                quote = ""
            continue
        if ch in ('"', "'"):
            quote = ch
            out.append(ch)
            continue
        if ch == "#" and i > 0 and value[i - 1] in (" ", "\t"):
            break
        out.append(ch)
    return "".join(out).rstrip()


def parse_env_line(raw: str):
    """Parse ONE `.plugin.env` line into (key, value), or None for blank/comment lines.

    The single source of truth for env parsing across every plugin script: supports
    `KEY=value` / `KEY = value`, ignores blank lines and whole-line `#` comments, cuts a
    safe trailing inline comment (see strip_inline_comment), and strips one layer of
    surrounding quotes. Returns None when the line carries no assignment.
    """
    line = raw.strip()
    if not line or line.startswith("#") or "=" not in line:
        return None
    key, value = line.split("=", 1)
    key = key.strip()
    if not key:
        return None
    value = strip_inline_comment(value.strip())
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        value = value[1:-1]  # paired surrounding quotes — keep the literal inside
    else:
        value = value.strip('"').strip("'")
    return key, value


def load_env(verbose: bool = False) -> dict:
    """Parse the plugin's .plugin.env into os.environ (without overriding real env vars).

    Returns the parsed key->value dict (may be empty if none). Uses parse_env_line for
    every line, so inline comments are cut safely and a `#` inside a value is preserved.
    Keys whose name contains SSL_CERT (SSL_CERT_FILE/SSL_CERT_DIR) are also set early so
    the TLS context that scripts build later picks up a corporate CA bundle.
    """
    parsed: dict = {}
    path = find_env_file()
    if path is None:
        if verbose:
            print("[env] no .plugin.env found — run the `setup` skill to create one")
        return parsed
    for raw in path.read_text(encoding="utf-8").splitlines():
        kv = parse_env_line(raw)
        if kv is None:
            continue
        key, value = kv
        parsed[key] = value
        os.environ.setdefault(key, value)
    if verbose:
        print(f"[env] loaded {len(parsed)} keys from {path}")
    return parsed


def make_ssl_context():
    """Build a TLS context for urllib that works behind a corporate self-signed proxy.

    Preference order, all stdlib-friendly:
      1. `truststore` (if installed) → verify against the OS trust store, which on macOS /
         Windows includes the corporate root CA injected by the proxy.
      2. `ssl.create_default_context()` → honours `SSL_CERT_FILE` / `SSL_CERT_DIR` (which
         load_env has already pushed into os.environ) so a hand-pointed CA bundle works.
    Never raises; returns a usable context regardless.
    """
    import ssl
    try:
        import truststore  # optional dependency — only used if the user installed it
        return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    except Exception:  # noqa: BLE001 — not installed / unsupported → fall back
        try:
            return ssl.create_default_context()
        except Exception:  # noqa: BLE001 — extremely defensive
            return None


def is_ssl_cert_error(text: str) -> bool:
    """True when an error string looks like a TLS trust failure (self-signed / corp proxy)."""
    t = (text or "").upper()
    return ("CERTIFICATE_VERIFY_FAILED" in t
            or "SELF-SIGNED CERTIFICATE" in t
            or "SELF SIGNED CERTIFICATE" in t
            or "UNABLE TO GET LOCAL ISSUER" in t)


def ssl_help_text() -> str:
    """One actionable block telling the user how to point SSL_CERT_FILE at a CA bundle."""
    import sys as _sys
    plat = _sys.platform
    if plat == "darwin":
        export = ('python3 -m pip install certifi  # once\n'
                  '     CERT="$(python3 -m certifi)"\n'
                  '     security find-certificate -a -p '
                  '/System/Library/Keychains/SystemRootCertificates.keychain >> "$CERT"\n'
                  '     security find-certificate -a -p '
                  '/Library/Keychains/System.keychain >> "$CERT"\n'
                  '     # then set in .plugin.env:  SSL_CERT_FILE=$CERT')
    elif plat.startswith("win"):
        export = ('pip install certifi python-certifi-win32  # picks up the Windows store\n'
                  '     # or export your corp root CA (.pem) and set SSL_CERT_FILE to it')
    else:
        export = ('pip install certifi  # then append your corp root CA:\n'
                  '     cat /etc/ssl/certs/ca-certificates.crt your-corp-root.pem > '
                  '~/qa-ca-bundle.pem\n'
                  '     # then set in .plugin.env:  SSL_CERT_FILE=~/qa-ca-bundle.pem')
    return ("🔒 SSL CERTIFICATE_VERIFY_FAILED — máy đang sau corporate proxy (root CA "
            "không có trong bundle của Python).\n"
            "   ✅ Cách nhanh nhất: chạy /qa:doctor --fix — nó tự cài `truststore` để dùng "
            "trust store của hệ điều hành (đã có sẵn root CA công ty), không cần config gì.\n"
            "   Nếu pip không cài được (offline / Python < 3.10), khắc phục thủ công bằng cách "
            "tạo CA bundle rồi đặt SSL_CERT_FILE trong .claude/qa-claude/.plugin.env:\n     " + export)


def env_bool(key: str, default: bool = False) -> bool:
    return str(os.environ.get(key, str(default))).strip().lower() == "true"


def env_str(key: str, default: str = "") -> str:
    v = os.environ.get(key)
    return v.strip() if v is not None else default
