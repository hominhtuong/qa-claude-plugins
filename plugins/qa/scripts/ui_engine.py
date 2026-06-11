#!/usr/bin/env python3
"""Local UI-vision engine manager for /qa:exploratory-ui — cross-platform (Windows/macOS/Linux).

WHY: /qa:exploratory-ui compares an app screenshot against its Figma design *locally* (color
Delta-E, SSIM, histogram, perceptual-hash) so the heavy image work runs on the machine and only
a tiny JSON verdict is handed to the AI — saving tokens. That comparison needs a small Python CV
stack (opencv + scikit-image + pillow + imagehash + numpy). To avoid clashing with the system
Python or the project's own deps, the stack lives in a DEDICATED venv:

    <project>/.claude/qa-claude/ui-engine/venv/

and a config records the interpreter path + thresholds:

    <project>/.claude/qa-claude/ui-engine.config.json

This script is the lifecycle manager behind the `ui-engine-check` skill and the
`/qa:ui-engine-install` command. It NEVER prints secrets and writes only under .claude/qa-claude/.

Subcommands:
    check    [--json]            report engine state (READY / NEEDS-SETUP / NEEDS-DEPS / NOT-INSTALLED)
    install  [--json] [--force]  create the venv, pip-install the CV stack, write the config
    info     [--json]            print the resolved config + interpreter + package versions
    python   [--json]            print ONLY the venv interpreter path (for callers to exec ui_compare.py)

Exit codes: 0 ok / engine READY · 2 not installed or deps missing · 3 install failed · 4 bad input.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _env import ensure_utf8_io, project_root  # noqa: E402

ensure_utf8_io()

OS = platform.system()  # 'Darwin', 'Windows', 'Linux'

# The CV stack. opencv-python-HEADLESS (no GUI libs) installs cleanly on servers/CI and on both
# macOS (incl. Apple Silicon) and Windows from prebuilt wheels — no compiler needed. scikit-image
# pulls scipy+numpy; imagehash pulls Pillow. Pin nothing hard so fresh wheels resolve per-platform.
PACKAGES = ["numpy", "opencv-python-headless", "scikit-image", "Pillow", "imagehash"]
# Modules to import-probe (pip name -> import name differs for several of these).
PROBE_IMPORTS = ["numpy", "cv2", "skimage", "PIL", "imagehash"]

DEFAULT_THRESHOLDS = {
    # ── GLOBAL color/structure ────────────────────────────────────────────────
    # Delta-E CIEDE2000 — perceptual color distance (0=identical). <1 imperceptible, 2-3 noticeable
    # on a close look, >5 clearly a different color. Mean over the frame + the 95th percentile region.
    "deltaE_mean_warn": 3.0,
    "deltaE_mean_fail": 6.0,
    "deltaE_p95_fail": 12.0,
    # SSIM — structural similarity (1=identical layout). Layout/spacing/shape drift drops this.
    "ssim_warn": 0.90,
    "ssim_fail": 0.80,
    # Perceptual hash Hamming distance (0=identical). >10 = visibly different composition.
    "phash_fail": 12,
    # Color-histogram correlation (1=identical distribution). Catches global tint/theme drift.
    "hist_corr_warn": 0.92,
    "hist_corr_fail": 0.85,
    # ── PER-REGION color (background vs text separated, via 2-means per grid cell) ──
    "bg_deltaE_warn": 3.0, "bg_deltaE_fail": 6.0,       # background/fill color
    "text_deltaE_warn": 4.0, "text_deltaE_fail": 8.0,   # text/foreground color
    # ── PER-REGION typography (measured on the text mask) ─────────────────────
    "stroke_ratio_warn": 0.15, "stroke_ratio_fail": 0.25,  # font weight (đậm/nhạt): |Δstroke|/ref
    "size_ratio_warn": 0.10, "size_ratio_fail": 0.18,      # font size: |Δtext-height|/ref
    "shape_dist_warn": 0.07, "shape_dist_fail": 0.11,      # font family (LOW confidence): edge-orientation distance
    # ── PER-REGION layout ─────────────────────────────────────────────────────
    "cell_ssim_warn": 0.82, "cell_ssim_fail": 0.62,        # local structure/alignment drift
    # ── region grid (rows × cols the frame is split into for the per-region sweep) ──
    "grid_rows": 6, "grid_cols": 4,
}


def engine_root() -> Path:
    return project_root() / ".claude" / "qa-claude" / "ui-engine"


def venv_dir() -> Path:
    return engine_root() / "venv"


def venv_python(vdir: Path | None = None) -> Path:
    """Path to the venv's interpreter — Windows puts it in Scripts\\, POSIX in bin/."""
    vdir = vdir or venv_dir()
    if OS == "Windows":
        return vdir / "Scripts" / "python.exe"
    return vdir / "bin" / "python"


def config_path() -> Path:
    return project_root() / ".claude" / "qa-claude" / "ui-engine.config.json"


def load_config() -> dict:
    p = config_path()
    if p.is_file():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return {}
    return {}


def _probe_packages(py: Path) -> tuple[bool, dict]:
    """Import every required module inside the venv; return (all_ok, {module: version|None})."""
    code = (
        "import json\n"
        "mods = " + repr(PROBE_IMPORTS) + "\n"
        "out = {}\n"
        "for m in mods:\n"
        "    try:\n"
        "        mod = __import__(m)\n"
        "        out[m] = getattr(mod, '__version__', 'ok')\n"
        "    except Exception as e:\n"
        "        out[m] = None\n"
        "print(json.dumps(out))\n"
    )
    try:
        proc = subprocess.run([str(py), "-c", code], capture_output=True, text=True, timeout=120)
        data = json.loads((proc.stdout or "").strip() or "{}")
    except Exception:  # noqa: BLE001
        return False, {m: None for m in PROBE_IMPORTS}
    all_ok = all(data.get(m) for m in PROBE_IMPORTS)
    return all_ok, data


def detect_state() -> dict:
    """Resolve the engine state without changing anything. The single source of truth for the
    ui-engine-check skill. State ∈ {READY, NEEDS-SETUP, NEEDS-DEPS, NOT-INSTALLED}."""
    py = venv_python()
    cfg = load_config()
    res = {
        "os": OS,
        "engine_root": str(engine_root()),
        "venv_python": str(py),
        "venv_exists": py.is_file(),
        "config_path": str(config_path()),
        "config_exists": config_path().is_file(),
        "packages": {m: None for m in PROBE_IMPORTS},
        "thresholds": cfg.get("thresholds", DEFAULT_THRESHOLDS),
    }
    if not py.is_file():
        res["state"] = "NOT-INSTALLED"
        res["hint"] = "Run /qa:ui-engine-install to create the venv and install the CV stack."
        return res
    ok, pkgs = _probe_packages(py)
    res["packages"] = pkgs
    if not ok:
        res["state"] = "NEEDS-DEPS"
        res["hint"] = "venv exists but the CV stack is incomplete — run /qa:ui-engine-install to repair."
        res["missing"] = [m for m in PROBE_IMPORTS if not pkgs.get(m)]
        return res
    if not config_path().is_file():
        res["state"] = "NEEDS-SETUP"
        res["hint"] = "CV stack is present but the config is missing — run /qa:ui-engine-install (it only writes the config)."
        return res
    res["state"] = "READY"
    res["hint"] = "Engine ready — ui_compare.py can run."
    return res


def _write_config(py: Path, versions: dict) -> Path:
    """Persist the engine config (interpreter + versions + thresholds). Preserves any thresholds
    the user already tuned in an existing config; only fills defaults for missing keys."""
    existing = load_config()
    thresholds = {**DEFAULT_THRESHOLDS, **(existing.get("thresholds") or {})}
    cfg = {
        "engine": "ui-vision-cv",
        "venv_python": str(py),
        "packages": versions,
        "thresholds": thresholds,
        "compare_script": str((Path(__file__).resolve().parent / "ui_compare.py")),
    }
    p = config_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def cmd_install(force: bool, as_json: bool) -> int:
    steps: list[str] = []
    vdir = venv_dir()
    py = venv_python(vdir)

    def emit(state: str, code: int, **extra) -> int:
        out = {"ok": code == 0, "state": state, "venv_python": str(py),
               "config_path": str(config_path()), "steps": steps, **extra}
        if as_json:
            print(json.dumps(out, ensure_ascii=False, indent=2))
        else:
            for s in steps:
                print(s)
            print(("✅ " if code == 0 else "❌ ") + state)
        return code

    if force and vdir.exists():
        import shutil
        steps.append(f"[install] --force: removing existing venv {vdir}")
        shutil.rmtree(vdir, ignore_errors=True)

    # 1) Create the venv if missing.
    if not py.is_file():
        engine_root().mkdir(parents=True, exist_ok=True)
        steps.append(f"[install] creating venv at {vdir} (base: {sys.executable})")
        proc = subprocess.run([sys.executable, "-m", "venv", str(vdir)],
                              capture_output=True, text=True)
        if proc.returncode != 0 or not py.is_file():
            steps.append("[install] venv creation FAILED:\n" + (proc.stderr or proc.stdout or "").strip())
            steps.append("  Ensure the `venv` module is available (Debian/Ubuntu: sudo apt install python3-venv).")
            return emit("INSTALL-FAILED", 3)
    else:
        steps.append(f"[install] reusing existing venv at {vdir}")

    # 2) Upgrade pip (best-effort) then install the CV stack.
    subprocess.run([str(py), "-m", "pip", "install", "--upgrade", "pip", "--quiet"],
                   capture_output=True, text=True)
    steps.append("[install] pip install " + " ".join(PACKAGES) + " (prebuilt wheels, ~30-60s)")
    proc = subprocess.run([str(py), "-m", "pip", "install", "--quiet", *PACKAGES],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "").strip()
        steps.append("[install] pip install FAILED:\n" + tail[-1500:])
        from _env import is_ssl_cert_error, ssl_help_text
        if is_ssl_cert_error(tail):
            steps.append(ssl_help_text())
        else:
            steps.append("  Retry when online, or check the proxy/index. Wheels come from PyPI.")
        return emit("INSTALL-FAILED", 3)

    # 3) Probe the imports and capture versions.
    ok, versions = _probe_packages(py)
    if not ok:
        missing = [m for m in PROBE_IMPORTS if not versions.get(m)]
        steps.append(f"[install] post-install import probe FAILED for: {', '.join(missing)}")
        return emit("INSTALL-FAILED", 3, missing=missing)
    steps.append("[install] import probe OK: " + ", ".join(f"{k}={v}" for k, v in versions.items()))

    # 4) Write the config.
    cfgp = _write_config(py, versions)
    steps.append(f"[install] wrote config {cfgp}")
    return emit("READY", 0, packages=versions)


def cmd_check(as_json: bool) -> int:
    res = detect_state()
    if as_json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(f"== ui-engine ({res['os']}) — {res['state']} ==")
        print(f"  venv python : {res['venv_python']}  ({'present' if res['venv_exists'] else 'MISSING'})")
        print(f"  config      : {res['config_path']}  ({'present' if res['config_exists'] else 'MISSING'})")
        for m, v in res["packages"].items():
            print(f"  {m:<10}: {v if v else 'MISSING'}")
        print(f"  → {res['hint']}")
    return 0 if res["state"] == "READY" else 2


def cmd_info(as_json: bool) -> int:
    cfg = load_config()
    if not cfg:
        msg = {"ok": False, "error": "no config — engine not installed yet"}
        print(json.dumps(msg, ensure_ascii=False, indent=2) if as_json else "No ui-engine config — run /qa:ui-engine-install.")
        return 2
    print(json.dumps(cfg, ensure_ascii=False, indent=2) if as_json else json.dumps(cfg, ensure_ascii=False, indent=2))
    return 0


def cmd_python(as_json: bool) -> int:
    py = venv_python()
    ok = py.is_file()
    if as_json:
        print(json.dumps({"ok": ok, "venv_python": str(py)}, ensure_ascii=False))
    else:
        print(str(py) if ok else "")
    return 0 if ok else 2


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Manage the local UI-vision CV engine for /qa:exploratory-ui")
    sub = ap.add_subparsers(dest="cmd")
    for name in ("check", "install", "info", "python"):
        sp = sub.add_parser(name)
        sp.add_argument("--json", action="store_true", help="machine-readable output")
        if name == "install":
            sp.add_argument("--force", action="store_true", help="recreate the venv from scratch")
    args = ap.parse_args(argv)

    if args.cmd == "install":
        return cmd_install(force=getattr(args, "force", False), as_json=args.json)
    if args.cmd == "check":
        return cmd_check(args.json)
    if args.cmd == "info":
        return cmd_info(args.json)
    if args.cmd == "python":
        return cmd_python(args.json)
    ap.print_help()
    return 4


if __name__ == "__main__":
    sys.exit(main())
