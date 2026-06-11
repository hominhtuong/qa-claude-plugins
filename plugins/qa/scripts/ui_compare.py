#!/usr/bin/env python3
"""UI visual comparator — runs INSIDE the ui-engine venv (needs cv2/skimage/PIL/imagehash/numpy).

Given ONE pair — a Figma reference frame (fm_*.png) and an app screenshot (ss_*.png) — it does all
the heavy image analysis LOCALLY and emits a tiny JSON verdict (a dozen numbers + a PASS/WARN/FAIL
+ short reasons). The orchestrating AI reads only that JSON, never the raw pixels, so a whole
exploratory-ui run costs almost no vision tokens. Every comparison is also appended to a JSONL
"model log" so the team can track how well the engine flags real design deviations over time.

Metrics (all local, deterministic):
  • color   — CIEDE2000 Delta-E between Lab images (mean, p95, % perceptible area) → "is the color right"
  • palette — dominant-color (k-means) match between the two frames
  • struct  — SSIM (structural similarity) over grayscale → layout/spacing/shape drift
  • hash    — perceptual-hash (pHash) Hamming distance → gross composition change
  • hist    — color-histogram correlation → global tint/theme drift
A heatmap PNG (where they differ most) is written for evidence — the AI views it ONLY for FAIL pairs.

This script MUST be run with the venv interpreter (see ui_engine.py `python`):
    <venv-python> ui_compare.py --reference fm.png --actual ss.png --pair-id hd001 \
        --out results/<f>/ui-compare/pairs/hd001.json \
        --log results/<f>/ui-compare/model-log.jsonl \
        --diff results/<f>/ui-compare/diffs/hd001-heatmap.png \
        [--thresholds <config.json>] [--feature <name>] [--screen "<name>"] [--work 768]

Output JSON (also printed to stdout): { ok, pair_id, verdict, reasons[], metrics{...}, sizes{...} }
Exit codes: 0 verdict computed (any verdict) · 2 cannot read an image · 3 missing CV deps · 4 bad input.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import numpy as np
    import cv2
    from skimage.color import rgb2lab, deltaE_ciede2000
    from skimage.metrics import structural_similarity as ssim
    from PIL import Image
    import imagehash
except Exception as e:  # noqa: BLE001 — wrong interpreter (system python, not the venv)
    sys.stderr.write(
        "❌ CV stack not importable — run this with the ui-engine venv interpreter.\n"
        f"   import error: {e}\n"
        "   Get the path: python3 scripts/ui_engine.py python   (then exec that python ui_compare.py ...)\n")
    sys.exit(3)


DEFAULT_THRESHOLDS = {
    "deltaE_mean_warn": 3.0, "deltaE_mean_fail": 6.0, "deltaE_p95_fail": 12.0,
    "ssim_warn": 0.90, "ssim_fail": 0.80,
    "phash_fail": 12,
    "hist_corr_warn": 0.92, "hist_corr_fail": 0.85,
}


def _load_rgb(path: Path) -> "np.ndarray":
    """Read an image as RGB uint8 via OpenCV (handles PNG/JPG); raises on failure."""
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)  # BGR
    if img is None:
        raise FileNotFoundError(f"cannot read image: {path}")
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def _fit_work(ref: "np.ndarray", act: "np.ndarray", work: int):
    """Scale the reference so its longer side == `work`, then resize the actual to the SAME canvas.

    Forcing a common canvas lets every metric line up pixel-for-pixel. When the two frames have
    different aspect ratios (a Figma frame vs a phone screenshot), that's a real signal — we record
    aspect_delta so the report can flag "wrong canvas/ratio" rather than silently distorting.
    """
    rh, rw = ref.shape[:2]
    scale = work / max(rh, rw)
    tw, th = max(1, int(round(rw * scale))), max(1, int(round(rh * scale)))
    ref_r = cv2.resize(ref, (tw, th), interpolation=cv2.INTER_AREA)
    act_r = cv2.resize(act, (tw, th), interpolation=cv2.INTER_AREA)
    return ref_r, act_r


def _color_deltaE(ref: "np.ndarray", act: "np.ndarray"):
    """Per-pixel CIEDE2000 between the two frames in Lab. Returns (mean, p95, perceptible_pct, map)."""
    lab_r = rgb2lab(ref.astype(np.float32) / 255.0)
    lab_a = rgb2lab(act.astype(np.float32) / 255.0)
    de = deltaE_ciede2000(lab_r, lab_a)  # HxW float
    mean = float(np.mean(de))
    p95 = float(np.percentile(de, 95))
    perceptible = float(np.mean(de > 5.0) * 100.0)  # % of frame where color is clearly off
    return mean, p95, perceptible, de


def _dominant_palette(img: "np.ndarray", k: int = 5):
    """Top-k dominant colors via k-means (returns list of [r,g,b] + their weight fraction)."""
    data = img.reshape(-1, 3).astype(np.float32)
    if len(data) > 20000:  # subsample for speed; palette is stable under sampling
        idx = np.linspace(0, len(data) - 1, 20000).astype(int)
        data = data[idx]
    k = int(min(k, max(1, len(np.unique(data, axis=0)))))
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, labels, centers = cv2.kmeans(data, k, None, criteria, 3, cv2.KMEANS_PP_CENTERS)
    counts = np.bincount(labels.flatten(), minlength=k).astype(float)
    weights = counts / counts.sum()
    order = np.argsort(-weights)
    return [([int(c) for c in centers[i]], float(weights[i])) for i in order]


def _palette_match(ref: "np.ndarray", act: "np.ndarray") -> float:
    """Mean Delta-E from each dominant ref color to its nearest actual color (0 = palettes match)."""
    pr = _dominant_palette(ref)
    pa = _dominant_palette(act)
    ref_cols = np.array([c for c, _ in pr], dtype=np.float32).reshape(-1, 1, 3) / 255.0
    act_cols = np.array([c for c, _ in pa], dtype=np.float32).reshape(1, -1, 3) / 255.0
    lab_r = rgb2lab(ref_cols)  # (R,1,3)
    lab_a = rgb2lab(act_cols)  # (1,A,3)
    R, A = lab_r.shape[0], lab_a.shape[1]
    grid_r = np.repeat(lab_r, A, axis=1)            # (R,A,3)
    grid_a = np.repeat(lab_a, R, axis=0)            # (R,A,3)
    de = deltaE_ciede2000(grid_r, grid_a)           # (R,A)
    nearest = de.min(axis=1)                        # best match per ref color
    weights = np.array([w for _, w in pr], dtype=np.float32)
    return float(np.average(nearest, weights=weights))


def _hist_corr(ref: "np.ndarray", act: "np.ndarray") -> float:
    """Average HSV histogram correlation (1 = identical color distribution)."""
    hsv_r = cv2.cvtColor(ref, cv2.COLOR_RGB2HSV)
    hsv_a = cv2.cvtColor(act, cv2.COLOR_RGB2HSV)
    corrs = []
    for ch, bins, rng in ((0, 50, [0, 180]), (1, 60, [0, 256]), (2, 60, [0, 256])):
        h_r = cv2.calcHist([hsv_r], [ch], None, [bins], rng)
        h_a = cv2.calcHist([hsv_a], [ch], None, [bins], rng)
        cv2.normalize(h_r, h_r); cv2.normalize(h_a, h_a)
        corrs.append(cv2.compareHist(h_r, h_a, cv2.HISTCMP_CORREL))
    return float(np.mean(corrs))


def _phash_distance(ref_path: Path, act_path: Path) -> int:
    return int(imagehash.phash(Image.open(ref_path)) - imagehash.phash(Image.open(act_path)))


def _write_heatmap(act: "np.ndarray", de_map: "np.ndarray", out: Path) -> None:
    """Overlay the Delta-E map (JET colormap) on the actual frame so a human sees WHERE it diverges."""
    norm = np.clip(de_map / 15.0, 0, 1)  # 15 Delta-E ≈ saturated red
    heat = cv2.applyColorMap((norm * 255).astype(np.uint8), cv2.COLORMAP_JET)
    base = cv2.cvtColor(act, cv2.COLOR_RGB2BGR)
    blend = cv2.addWeighted(base, 0.55, heat, 0.45, 0)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), blend)


def _verdict(m: dict, th: dict):
    """Roll the metrics up into PASS / WARN / FAIL with human reasons. Color is the headline signal."""
    reasons: list[str] = []
    fail = False
    warn = False

    if m["deltaE_mean"] >= th["deltaE_mean_fail"]:
        fail = True; reasons.append(f"color off — mean Delta-E {m['deltaE_mean']:.1f} ≥ {th['deltaE_mean_fail']}")
    elif m["deltaE_mean"] >= th["deltaE_mean_warn"]:
        warn = True; reasons.append(f"color slightly off — mean Delta-E {m['deltaE_mean']:.1f}")
    if m["deltaE_p95"] >= th["deltaE_p95_fail"]:
        fail = True; reasons.append(f"a region is strongly miscolored — p95 Delta-E {m['deltaE_p95']:.1f} ≥ {th['deltaE_p95_fail']}")

    if m["ssim"] <= th["ssim_fail"]:
        fail = True; reasons.append(f"layout/structure differs — SSIM {m['ssim']:.2f} ≤ {th['ssim_fail']}")
    elif m["ssim"] <= th["ssim_warn"]:
        warn = True; reasons.append(f"minor structural drift — SSIM {m['ssim']:.2f}")

    if m["phash_distance"] >= th["phash_fail"]:
        fail = True; reasons.append(f"composition differs — pHash distance {m['phash_distance']} ≥ {th['phash_fail']}")

    if m["hist_corr"] <= th["hist_corr_fail"]:
        fail = True; reasons.append(f"global color distribution differs — hist corr {m['hist_corr']:.2f} ≤ {th['hist_corr_fail']}")
    elif m["hist_corr"] <= th["hist_corr_warn"]:
        warn = True; reasons.append(f"slight tint/theme drift — hist corr {m['hist_corr']:.2f}")

    if m["aspect_delta"] >= 0.15:
        warn = True; reasons.append(f"aspect ratio differs by {m['aspect_delta']*100:.0f}% (canvas/ratio mismatch — metrics computed on a forced common canvas)")

    verdict = "FAIL" if fail else ("WARN" if warn else "PASS")
    if not reasons:
        reasons.append("matches the design within tolerance")
    return verdict, reasons


def compare(ref_path: Path, act_path: Path, work: int, th: dict, diff: Path | None):
    ref = _load_rgb(ref_path)
    act = _load_rgb(act_path)
    rh, rw = ref.shape[:2]
    ah, aw = act.shape[:2]
    aspect_ref = rw / rh if rh else 0.0
    aspect_act = aw / ah if ah else 0.0
    aspect_delta = abs(aspect_ref - aspect_act) / max(aspect_ref, aspect_act, 1e-6)

    ref_r, act_r = _fit_work(ref, act, work)
    de_mean, de_p95, perceptible, de_map = _color_deltaE(ref_r, act_r)
    gray_r = cv2.cvtColor(ref_r, cv2.COLOR_RGB2GRAY)
    gray_a = cv2.cvtColor(act_r, cv2.COLOR_RGB2GRAY)
    ssim_val = float(ssim(gray_r, gray_a))
    hist = _hist_corr(ref_r, act_r)
    palette_de = _palette_match(ref_r, act_r)
    phash = _phash_distance(ref_path, act_path)

    metrics = {
        "deltaE_mean": round(de_mean, 2),
        "deltaE_p95": round(de_p95, 2),
        "color_perceptible_pct": round(perceptible, 1),
        "palette_deltaE": round(palette_de, 2),
        "ssim": round(ssim_val, 3),
        "hist_corr": round(hist, 3),
        "phash_distance": phash,
        "aspect_delta": round(aspect_delta, 3),
        "color_match_pct": round(max(0.0, 100.0 - de_mean / 0.1), 1),  # friendly 0-100 (10 Delta-E→0%)
    }
    verdict, reasons = _verdict(metrics, th)

    if diff is not None:
        try:
            _write_heatmap(act_r, de_map, diff)
        except Exception:  # noqa: BLE001 — heatmap is evidence-only, never fail the comparison
            diff = None

    return {
        "metrics": metrics,
        "verdict": verdict,
        "reasons": reasons,
        "sizes": {"reference": [rw, rh], "actual": [aw, ah], "work": list(ref_r.shape[1::-1])},
        "heatmap": str(diff) if diff else None,
    }


def _load_thresholds(arg: str | None) -> dict:
    """Thresholds come from the engine config (ui-engine.config.json) or an explicit JSON file."""
    if not arg:
        return dict(DEFAULT_THRESHOLDS)
    p = Path(arg)
    if not p.is_file():
        return dict(DEFAULT_THRESHOLDS)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        th = data.get("thresholds", data) if isinstance(data, dict) else {}
        return {**DEFAULT_THRESHOLDS, **(th or {})}
    except Exception:  # noqa: BLE001
        return dict(DEFAULT_THRESHOLDS)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Compare an app screenshot against a Figma reference (local CV).")
    ap.add_argument("--reference", required=True, help="Figma reference PNG (fm_*.png)")
    ap.add_argument("--actual", required=True, help="app screenshot PNG (ss_*.png)")
    ap.add_argument("--pair-id", default="", help="stable id for this screen pair (e.g. hd001)")
    ap.add_argument("--screen", default="", help="human screen name (for the log/report)")
    ap.add_argument("--feature", default="", help="feature name (for the log)")
    ap.add_argument("--out", default="", help="write the verdict JSON here")
    ap.add_argument("--log", default="", help="append one JSONL line here (model-efficiency tracking)")
    ap.add_argument("--diff", default="", help="write the difference heatmap PNG here")
    ap.add_argument("--thresholds", default="", help="path to ui-engine.config.json (or a thresholds json)")
    ap.add_argument("--work", type=int, default=768, help="working longer-side px for the math (default 768)")
    args = ap.parse_args(argv)

    ref_path, act_path = Path(args.reference), Path(args.actual)
    th = _load_thresholds(args.thresholds or None)
    diff = Path(args.diff) if args.diff else None

    try:
        result = compare(ref_path, act_path, args.work, th, diff)
    except FileNotFoundError as e:
        err = {"ok": False, "pair_id": args.pair_id, "error": str(e)}
        print(json.dumps(err, ensure_ascii=False))
        return 2
    except Exception as e:  # noqa: BLE001
        err = {"ok": False, "pair_id": args.pair_id, "error": f"{type(e).__name__}: {e}"}
        print(json.dumps(err, ensure_ascii=False))
        return 2

    out = {
        "ok": True,
        "pair_id": args.pair_id,
        "screen": args.screen,
        "feature": args.feature,
        "reference": str(ref_path),
        "actual": str(act_path),
        **result,
    }

    if args.out:
        op = Path(args.out)
        op.parent.mkdir(parents=True, exist_ok=True)
        op.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.log:
        lp = Path(args.log)
        lp.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "feature": args.feature, "pair_id": args.pair_id, "screen": args.screen,
            "verdict": out["verdict"], "metrics": out["metrics"],
            "thresholds": th, "sizes": out["sizes"],
        }
        with lp.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(json.dumps({k: out[k] for k in ("ok", "pair_id", "screen", "verdict", "reasons", "metrics", "heatmap")},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
