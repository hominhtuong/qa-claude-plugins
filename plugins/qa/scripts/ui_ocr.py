#!/usr/bin/env python3
"""Local OCR text extraction for /qa:exploratory-ui — pluggable backend, runs in the ui-engine venv.

The visual engine (ui_compare.py) answers "is the color/font/layout right". This module answers the
other half the user asked for: "does the TEXT match the design?" — extract the words the app actually
renders (with positions) so the comparison can flag a changed STATIC label (Figma says "Products",
app shows "Product") while leaving DYNAMIC values (list data, numbers) alone. The static-vs-dynamic
call is the AI's job (rules/ui-text-rules.md); EXTRACTION is this local model's job.

Backends, tried in order (Auto):
  1. Tesseract  — `tesseract` binary + pytesseract, lang `vie+eng`. Best Vietnamese (with diacritics).
  2. RapidOCR   — `rapidocr_onnxruntime` (pip, ~ONNX, no torch). Self-contained fallback.
If neither is available, extraction returns backend="none" and the caller skips text comparison
(with a clear note) rather than guessing.

Output (line-level): { backend, lines: [ {text, bbox:[x,y,w,h], conf} ] } in PIXEL coords of the image.

CLI (standalone test):  <venv-python> ui_ocr.py <image.png> [--langs vie+eng] [--backend auto|tesseract|rapidocr] [--json]
Exit codes: 0 ok (even if 0 lines) · 2 image not found · 3 no OCR backend available.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


def _has_tesseract() -> bool:
    if shutil.which("tesseract") is None:
        return False
    try:
        import pytesseract  # noqa: F401
        return True
    except Exception:  # noqa: BLE001
        return False


def _has_rapidocr() -> bool:
    try:
        import rapidocr_onnxruntime  # noqa: F401
        return True
    except Exception:  # noqa: BLE001
        return False


def available_backend() -> str:
    """Name of the first usable OCR backend, or '' if none (for doctor / ui_engine check)."""
    if _has_tesseract():
        return "tesseract"
    if _has_rapidocr():
        return "rapidocr"
    return ""


# ── backends ───────────────────────────────────────────────────────────────────

def _extract_tesseract(path: Path, langs: str):
    """Word boxes from Tesseract, grouped into lines by (block, par, line)."""
    import pytesseract
    from PIL import Image
    data = pytesseract.image_to_data(Image.open(path), lang=langs,
                                     output_type=pytesseract.Output.DICT)
    groups: dict = {}
    n = len(data["text"])
    for i in range(n):
        txt = (data["text"][i] or "").strip()
        conf = float(data["conf"][i]) if str(data["conf"][i]).lstrip("-").isdigit() else -1.0
        if not txt or conf < 0:
            continue
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
        g = groups.setdefault(key, {"words": [], "x0": x, "y0": y, "x1": x + w, "y1": y + h, "confs": []})
        g["words"].append(txt)
        g["x0"] = min(g["x0"], x); g["y0"] = min(g["y0"], y)
        g["x1"] = max(g["x1"], x + w); g["y1"] = max(g["y1"], y + h)
        g["confs"].append(conf)
    lines = []
    for g in groups.values():
        lines.append({"text": " ".join(g["words"]),
                      "bbox": [int(g["x0"]), int(g["y0"]), int(g["x1"] - g["x0"]), int(g["y1"] - g["y0"])],
                      "conf": round(sum(g["confs"]) / len(g["confs"]) / 100.0, 3)})
    return lines


def _extract_rapidocr(path: Path):
    from rapidocr_onnxruntime import RapidOCR
    engine = RapidOCR()
    result, _ = engine(str(path))
    lines = []
    for item in (result or []):
        box, text, conf = item[0], item[1], item[2]
        xs = [p[0] for p in box]; ys = [p[1] for p in box]
        lines.append({"text": (text or "").strip(),
                      "bbox": [int(min(xs)), int(min(ys)), int(max(xs) - min(xs)), int(max(ys) - min(ys))],
                      "conf": round(float(conf), 3)})
    return [l for l in lines if l["text"]]


def extract(path: Path, langs: str = "vie+eng", backend: str = "auto") -> dict:
    """Extract line-level text + pixel bboxes. backend: auto|tesseract|rapidocr."""
    if not Path(path).is_file():
        return {"backend": "none", "error": f"image not found: {path}", "lines": []}
    chosen = backend
    if backend == "auto":
        chosen = available_backend() or "none"
    try:
        if chosen == "tesseract":
            return {"backend": "tesseract", "lines": _extract_tesseract(Path(path), langs)}
        if chosen == "rapidocr":
            return {"backend": "rapidocr", "lines": _extract_rapidocr(Path(path))}
    except Exception as e:  # noqa: BLE001 — backend present but failed (missing lang pack, etc.)
        return {"backend": chosen, "error": f"{type(e).__name__}: {e}", "lines": []}
    return {"backend": "none", "error": "no OCR backend available (install tesseract or rapidocr-onnxruntime)",
            "lines": []}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Extract text + boxes from an image (local OCR).")
    ap.add_argument("image")
    ap.add_argument("--langs", default="vie+eng")
    ap.add_argument("--backend", default="auto", choices=["auto", "tesseract", "rapidocr"])
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    p = Path(args.image)
    if not p.is_file():
        print(json.dumps({"ok": False, "error": f"image not found: {p}"}, ensure_ascii=False))
        return 2
    res = extract(p, args.langs, args.backend)
    if not res.get("lines") and res["backend"] == "none":
        print(json.dumps({"ok": False, **res}, ensure_ascii=False))
        return 3
    out = {"ok": True, **res}
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(f"backend={res['backend']}  lines={len(res['lines'])}")
        for l in res["lines"]:
            print(f"  [{l['conf']:.2f}] {l['bbox']}  {l['text']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
