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

    if missing_required:
        print("\nMissing required tools — install them, then re-run the doctor:")
        for name, hint in missing_required:
            print(f"  - {name}: {hint}")
        return 1
    print("\nAll required tools present ✅")
    return 0


if __name__ == "__main__":
    sys.exit(run(fix="--fix" in sys.argv[1:]))
