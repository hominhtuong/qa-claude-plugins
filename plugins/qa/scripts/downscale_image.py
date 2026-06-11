#!/usr/bin/env python3
"""Downscale a screenshot so it is safe to Read into an LLM context — cross-platform.

WHY: long screenshot-heavy runs (e.g. /qa:exploratory) hit a cumulative many-image budget.
The first trigger is per-image DIMENSION: the API rejects any image whose longer side exceeds
~2000px ("image dimensions exceed max allowed size for many-image requests: 2000 pixels").
A phone screencap is often 1220×2712 — already over the limit. This helper shrinks the longer
side to <=`--max` (default 1300) so each Read succeeds and the many-image budget stretches.

It NEVER needs a specific tool preinstalled — it tries backends in order and uses whichever
exists: Pillow (python) -> sips (macOS) -> ImageMagick (magick/convert) -> ffmpeg. If NONE is
available it still parses the image header with the stdlib and reports the real dimensions +
an install hint, so the caller can decide NOT to Read an oversized image (and drive blind
instead) rather than tripping the cap.

Usage:
    python3 downscale_image.py shot.png                     # -> shot.small.png (<=1300 long side)
    python3 downscale_image.py shot.png --out small.png
    python3 downscale_image.py shot.png --max 1000 --json
    python3 downscale_image.py shot.png --probe-only --json # just measure, never resize

Output JSON: { ok, src, out, backend, original:[w,h], result:[w,h], downscaled, needs_resize,
               within_cap, action }
Exit codes: 0 ok (resized OR already small) · 1 oversized but no backend to resize · 2 bad input.
"""
from __future__ import annotations

import argparse
import json
import shutil
import struct
import subprocess
import sys
from pathlib import Path

CAP_PX = 2000          # hard per-image dimension cap for many-image requests
DEFAULT_MAX = 1300     # recommended longer-side target (comfortably under the cap)


# ── stdlib dimension probe (no third-party dep) ────────────────────────────────

def image_size(path: Path) -> tuple[int, int] | None:
    """Return (width, height) for PNG/JPEG/GIF/BMP using only the stdlib. None if unknown."""
    try:
        with open(path, "rb") as f:
            head = f.read(26)
            if len(head) < 24:
                return None
            # PNG: 8-byte sig, then IHDR (width,height big-endian uint32 at offset 16).
            if head[:8] == b"\x89PNG\r\n\x1a\n":
                w, h = struct.unpack(">II", head[16:24])
                return int(w), int(h)
            # GIF: logical screen descriptor (little-endian uint16 at offset 6).
            if head[:6] in (b"GIF87a", b"GIF89a"):
                w, h = struct.unpack("<HH", head[6:10])
                return int(w), int(h)
            # BMP: DIB header width/height (little-endian int32 at offset 18).
            if head[:2] == b"BM":
                w, h = struct.unpack("<ii", head[18:26])
                return int(abs(w)), int(abs(h))
            # JPEG: scan SOF markers for the frame dimensions.
            if head[:2] == b"\xff\xd8":
                return _jpeg_size(path)
    except Exception:  # noqa: BLE001
        return None
    return None


def _jpeg_size(path: Path) -> tuple[int, int] | None:
    with open(path, "rb") as f:
        f.read(2)  # SOI
        while True:
            b = f.read(1)
            if not b:
                return None
            if b != b"\xff":
                continue
            marker = f.read(1)
            while marker == b"\xff":
                marker = f.read(1)
            if not marker:
                return None
            m = marker[0]
            if 0xC0 <= m <= 0xCF and m not in (0xC4, 0xC8, 0xCC):  # SOF0..SOF15 (frame)
                f.read(3)  # segment length(2) + precision(1)
                h, w = struct.unpack(">HH", f.read(4))
                return int(w), int(h)
            seg = f.read(2)
            if len(seg) < 2:
                return None
            length = struct.unpack(">H", seg)[0]
            f.seek(length - 2, 1)


# ── resize backends (use whichever is present) ─────────────────────────────────

def _try_pillow(src: Path, out: Path, max_side: int) -> bool:
    try:
        from PIL import Image  # type: ignore
    except Exception:  # noqa: BLE001
        return False
    try:
        with Image.open(src) as im:
            im = im.convert("RGB") if im.mode in ("RGBA", "P", "LA") and out.suffix.lower() in (".jpg", ".jpeg") else im
            im.thumbnail((max_side, max_side))  # in-place, preserves aspect ratio
            im.save(out)
        return out.is_file()
    except Exception:  # noqa: BLE001
        return False


def _run(cmd: list[str]) -> bool:
    try:
        return subprocess.run(cmd, capture_output=True, timeout=60).returncode == 0
    except Exception:  # noqa: BLE001
        return False


def _try_sips(src: Path, out: Path, max_side: int) -> bool:  # macOS
    if not shutil.which("sips"):
        return False
    # -Z N resizes so the LONGER side becomes N, preserving aspect ratio.
    return _run(["sips", "-Z", str(max_side), str(src), "--out", str(out)]) and out.is_file()


def _try_imagemagick(src: Path, out: Path, max_side: int) -> bool:
    exe = shutil.which("magick") or shutil.which("convert")
    if not exe:
        return False
    base = [exe] + (["convert"] if Path(exe).name == "magick" else [])
    # ">" only shrinks if larger; NxN with no gravity fits within the box, aspect preserved.
    return _run(base + [str(src), "-resize", f"{max_side}x{max_side}>", str(out)]) and out.is_file()


def _try_ffmpeg(src: Path, out: Path, max_side: int) -> bool:
    if not shutil.which("ffmpeg"):
        return False
    # Scale the longer side to max_side, keep aspect, force even dims; only downscale.
    vf = (f"scale='if(gt(iw,ih),min({max_side},iw),-2)':"
          f"'if(gt(iw,ih),-2,min({max_side},ih))'")
    return _run(["ffmpeg", "-y", "-i", str(src), "-vf", vf, str(out)]) and out.is_file()


BACKENDS = [("pillow", _try_pillow), ("sips", _try_sips),
            ("imagemagick", _try_imagemagick), ("ffmpeg", _try_ffmpeg)]


def available_backend() -> str:
    """Name of the first usable resize backend, or '' if none (for /qa:doctor)."""
    try:
        import PIL  # type: ignore  # noqa: F401
        return "pillow"
    except Exception:  # noqa: BLE001
        pass
    if shutil.which("sips"):
        return "sips"
    if shutil.which("magick") or shutil.which("convert"):
        return "imagemagick"
    if shutil.which("ffmpeg"):
        return "ffmpeg"
    return ""


INSTALL_HINT = ("install ONE downscale backend: `pip install Pillow` (any OS), or macOS `sips` "
                "(built-in), or ImageMagick (`brew/apt install imagemagick`), or ffmpeg. Until "
                "then, do NOT Read screenshots whose longer side > 2000px — drive blind via page "
                "source / accessibility-id instead.")


def downscale(src: Path, out: Path, max_side: int) -> dict:
    """Downscale src->out if its longer side exceeds max_side. Returns a result dict."""
    if not src.is_file():
        return {"ok": False, "src": str(src), "error": "source not found"}
    orig = image_size(src)
    needs = bool(orig and max(orig) > max_side)
    res = {"ok": True, "src": str(src), "out": str(src), "backend": "",
           "original": list(orig) if orig else None, "result": list(orig) if orig else None,
           "downscaled": False,
           "needs_resize": needs,
           "within_cap": bool(orig and max(orig) <= CAP_PX)}
    if not needs:
        res["action"] = "already small enough — safe to Read directly."
        return res
    for name, fn in BACKENDS:
        if fn(src, out, max_side):
            res.update(ok=True, out=str(out), backend=name, downscaled=True,
                       result=list(image_size(out) or []),
                       within_cap=(max(image_size(out) or [0]) <= CAP_PX),
                       action=f"Read the downscaled copy: {out}")
            return res
    # No backend — keep the original but flag it as unsafe to Read if over the hard cap.
    res["ok"] = bool(orig and max(orig) <= CAP_PX)
    res["action"] = (f"NO downscale backend found and the image is {orig[0]}x{orig[1]} "
                     f"(> {CAP_PX}px). {INSTALL_HINT}") if orig else \
                    f"could not measure the image and no backend to resize. {INSTALL_HINT}"
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Downscale a screenshot to be safe to Read into an LLM context")
    ap.add_argument("src", help="path to the source image")
    ap.add_argument("--out", default=None, help="output path (default: <src>.small<ext>)")
    ap.add_argument("--max", type=int, default=DEFAULT_MAX, help=f"longer-side target px (default {DEFAULT_MAX})")
    ap.add_argument("--probe-only", action="store_true", help="only measure dimensions, never resize")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args(argv)

    src = Path(args.src)
    if args.probe_only:
        size = image_size(src)
        res = {"ok": src.is_file(), "src": str(src), "original": list(size) if size else None,
               "within_cap": bool(size and max(size) <= CAP_PX),
               "needs_resize": bool(size and max(size) > args.max),
               "backend_available": available_backend()}
    else:
        out = Path(args.out) if args.out else src.with_suffix(f".small{src.suffix or '.png'}")
        res = downscale(src, out, args.max)

    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        if not res.get("ok") and not res.get("original"):
            print(f"❌ {res.get('error') or res.get('action')}", file=sys.stderr)
        elif res.get("downscaled"):
            print(f"✅ {res['original'][0]}x{res['original'][1]} → {res['result'][0]}x{res['result'][1]}"
                  f"  ({res['backend']})  {res['out']}")
        elif res.get("needs_resize"):
            print(f"⚠️  {res.get('action')}", file=sys.stderr)
        else:
            print(f"✅ {res.get('action', 'ok')}  {res.get('out', src)}")
    return 0 if res.get("ok") else (1 if res.get("original") else 2)


if __name__ == "__main__":
    sys.exit(main())
