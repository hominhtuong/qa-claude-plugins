#!/usr/bin/env python3
"""Toolchain doctor for the `auto` plugin — cross-platform (Windows/macOS/Linux).

Detects required/optional tools, prints per-OS install commands for anything missing,
and with --fix auto-installs what can be safely automated (currently: wrangler via npm).

System toolchains (python, node, java) cannot be auto-installed by a python script
(you can't bootstrap python with python), so those are reported with the exact command
for the detected OS.

Usage:
    python3 doctor.py            # report only
    python3 doctor.py --fix      # also: npm install -g wrangler if npm present
"""
import platform
import shutil
import subprocess
import sys

OS = platform.system()  # 'Darwin', 'Windows', 'Linux'


def _install_hint(mac, win, linux):
    return {"Darwin": mac, "Windows": win, "Linux": linux}.get(OS, linux)


# name -> (probe cmd list, required?, install hints per OS)
CHECKS = [
    ("python3", [sys.executable, "--version"], True,
     _install_hint("brew install python", "winget install Python.Python.3",
                   "sudo apt install python3")),
    ("node", ["node", "--version"], True,
     _install_hint("brew install node", "winget install OpenJS.NodeJS",
                   "sudo apt install nodejs npm")),
    ("npm", ["npm", "--version"], True,
     _install_hint("brew install node", "winget install OpenJS.NodeJS",
                   "sudo apt install npm")),
    ("wrangler", ["wrangler", "--version"], True, "npm install -g wrangler"),
    ("java", ["java", "-version"], True,
     _install_hint("brew install openjdk@17", "winget install EclipseAdoptium.Temurin.17.JDK",
                   "sudo apt install openjdk-17-jdk")),
    ("mvn", ["mvn", "-v"], True,
     _install_hint("brew install maven", "winget install Apache.Maven",
                   "sudo apt install maven")),
    ("aws", ["aws", "--version"], False,
     _install_hint("brew install awscli", "winget install Amazon.AWSCLI",
                   "sudo apt install awscli") + "  (only for S3-compatible upload)"),
    ("adb", ["adb", "version"], False, "Android SDK Platform Tools (optional, Android only)"),
    ("appium", ["appium", "--version"], False, "npm install -g appium (optional, mobile only)"),
]


def _probe(name, cmd):
    exe = cmd[0]
    if name != "python3" and shutil.which(exe) is None:
        return False, ""
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        out = (proc.stdout or "") + (proc.stderr or "")
        return True, out.strip().splitlines()[0] if out.strip() else "ok"
    except Exception:
        return False, ""


def run(fix: bool = False) -> int:
    print(f"== auto-plugin doctor ({OS}) ==")
    missing_required = []
    can_autofix = []
    for name, cmd, required, hint in CHECKS:
        ok, version = _probe(name, cmd)
        tag = "  " if required else "· "
        if ok:
            print(f"{tag}[ok]   {name:<9} {version}")
        else:
            label = "MISSING" if required else "absent "
            print(f"{tag}[{label}] {name:<9} -> {hint}")
            if required:
                missing_required.append((name, hint))
            if name == "wrangler":
                can_autofix.append(name)

    if fix and "wrangler" in can_autofix and shutil.which("npm"):
        print("\n[fix] installing wrangler globally (npm install -g wrangler)...")
        proc = subprocess.run(["npm", "install", "-g", "wrangler"])
        if proc.returncode == 0:
            print("[fix] wrangler installed.")
            missing_required = [m for m in missing_required if m[0] != "wrangler"]
        else:
            print("[fix] wrangler install failed — install manually: npm install -g wrangler")

    _check_tls(fix=fix)

    if missing_required:
        print("\nMissing required tools — install them, then re-run the doctor:")
        for name, hint in missing_required:
            print(f"  - {name}: {hint}")
        return 1
    print("\nAll required tools present ✅")
    return 0


def _have_truststore() -> bool:
    """True if `truststore` (OS trust-store TLS) can be imported in this interpreter."""
    try:
        import truststore  # noqa: F401
        return True
    except Exception:  # noqa: BLE001
        return False


def _ensure_truststore(fix: bool) -> bool:
    """Make corporate-proxy TLS work out of the box by installing `truststore`.

    `truststore` routes Python's certificate verification through the OS trust store
    (macOS Keychain / Windows cert store / Linux ca-certificates) — which already holds
    the corporate root CA that IT installed. That is why we prefer it over making the user
    hand-build a PEM bundle and point SSL_CERT_FILE at it: zero config, and it survives the
    proxy rotating its CA. This is the auto-fix that lets `setup` "just work" behind a proxy.

    Returns True if truststore ends up importable. Needs Python 3.10+ (truststore's floor);
    on older interpreters we skip and the caller falls back to the SSL_CERT_FILE hint.
    """
    if _have_truststore():
        return True
    if not fix:
        return False
    if sys.version_info < (3, 10):
        print("· [info] TLS       truststore needs Python 3.10+ — skipping auto-install "
              f"(this is Python {sys.version_info.major}.{sys.version_info.minor}).")
        return False
    print("\n[fix] installing truststore (use the OS trust store for corporate-proxy TLS)...")
    base = [sys.executable, "-m", "pip", "install", "--quiet", "truststore"]
    # Plain install first; retry with --user for PEP-668 / externally-managed interpreters.
    for cmd in (base, base + ["--user"]):
        if subprocess.run(cmd).returncode == 0 and _have_truststore():
            print("[fix] truststore installed — Lark TLS will trust your OS/corporate CA.")
            return True
    print("[fix] truststore install failed (offline or restricted pip?) — "
          "will fall back to the SSL_CERT_FILE hint if Lark TLS is blocked.")
    return False


def _check_tls(fix: bool = False) -> None:
    """Probe HTTPS to Lark; auto-fix corporate-proxy trust, else point to the remedy.

    Non-fatal — only Lark features need it. With --fix this first installs `truststore`
    (see _ensure_truststore) so a proxy environment is handled at setup time with no user
    action. Only if that is unavailable AND TLS is still blocked do we print the manual
    SSL_CERT_FILE fix — so a fresh `setup` "just works" on the common case.
    """
    import os
    import ssl
    import urllib.error
    import urllib.request

    have_ts = _ensure_truststore(fix)
    host = "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal"
    try:
        if have_ts:
            import truststore  # use the OS trust store (includes the corporate root CA)
            ctx = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            via = " (via OS trust store)"
        else:
            ctx = ssl.create_default_context()  # honours SSL_CERT_FILE if the user set one
            via = ""
        req = urllib.request.Request(host, data=b"{}", method="POST",
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=15, context=ctx).read()
        print(f"· [ok]   TLS       can reach Lark over HTTPS{via}")
    except urllib.error.HTTPError:
        # Got an HTTP response (e.g. 400 to the empty body) → the TLS handshake succeeded.
        via = " (via OS trust store)" if have_ts else ""
        print(f"· [ok]   TLS       can reach Lark over HTTPS{via}")
    except Exception as e:  # noqa: BLE001
        msg = str(getattr(e, "reason", e))
        up = msg.upper()
        if ("CERTIFICATE_VERIFY_FAILED" in up or "SELF-SIGNED CERTIFICATE" in up
                or "SELF SIGNED CERTIFICATE" in up or "UNABLE TO GET LOCAL ISSUER" in up):
            # truststore would have fixed this; reaching here means it could not be installed.
            print("· [warn] TLS       corporate/self-signed CA blocks Lark, and truststore "
                  "could not be installed automatically.")
            print(f"           Manual fix: {sys.executable} -m pip install truststore "
                  "(retry when online), then re-run /qa:doctor.")
            have = "set" if os.environ.get("SSL_CERT_FILE") else "NOT set"
            print(f"           Or point SSL_CERT_FILE (currently {have}) at a CA bundle in "
                  ".claude/qa-claude/.plugin.env — macOS:")
            print("             pip install certifi; CERT=\"$(python3 -m certifi)\"; "
                  "security find-certificate -a -p /Library/Keychains/System.keychain >> \"$CERT\"; "
                  "set SSL_CERT_FILE=$CERT")
        # any other error (offline/DNS) is unrelated to the toolchain → stay quiet


if __name__ == "__main__":
    sys.exit(run(fix="--fix" in sys.argv[1:]))
