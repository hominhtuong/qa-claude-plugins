#!/usr/bin/env python3
"""UI visual comparator — runs INSIDE the ui-engine venv (needs cv2/skimage/PIL/imagehash/numpy).

Given ONE pair — a Figma reference frame (fm_*.png) and an app screenshot (ss_*.png) — it does all
the heavy image analysis LOCALLY and emits a compact, *typed* verdict: not just "they differ" but
HOW they differ, per region — layout, background color, text color, font weight (đậm/nhạt), font
size, and a lower-confidence font-family signal. The orchestrating AI reads only that JSON, never
the raw pixels, so a whole exploratory-ui run costs almost no vision tokens. Every comparison is
appended to a JSONL "model log" so the team can track how reliably the engine flags real deviations.

Why this design: a global Delta-E says "a color is off somewhere"; it can't tell *background* from
*text*, nor a heavier font from a bigger one. So the engine works at two levels:
  • GLOBAL   — Delta-E (mean/p95), SSIM, histogram, pHash, palette  → fast overall signal.
  • PER-CELL — split the aligned frames into a grid; in each cell separate background vs foreground
               (text) color via 2-means, and on the text mask measure stroke width (weight), text
               row height (size) and an edge-orientation signature (family). Differences beyond a
               perceptual tolerance become typed FINDINGS the AI can turn into precise bug lines.
Tolerances are calibrated to human perception (CIEDE2000 for color; stroke/height *ratios* for type)
and stay device-tolerant — small rendering noise passes, but a difference the eye would catch fails.

Run with the venv interpreter (see ui_engine.py `python`):
    <venv-python> ui_compare.py --reference fm.png --actual ss.png --pair-id hd001 \
        --out results/<f>/ui-compare/pairs/hd001.json \
        --log results/<f>/ui-compare/model-log.jsonl \
        --diff results/<f>/ui-compare/diffs/hd001-heatmap.png \
        [--thresholds <config.json>] [--feature <name>] [--screen "<name>"] [--work 768] [--grid 6x4]

Output JSON: { ok, pair_id, verdict, reasons[], metrics{}, findings[], summary_by_type{}, sizes{} }
Exit codes: 0 verdict computed · 2 cannot read an image · 3 missing CV deps · 4 bad input.
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
    # ── global color / structure ──────────────────────────────────────────────
    "deltaE_mean_warn": 3.0, "deltaE_mean_fail": 6.0, "deltaE_p95_fail": 12.0,
    "ssim_warn": 0.90, "ssim_fail": 0.80,
    "phash_fail": 12,
    "hist_corr_warn": 0.92, "hist_corr_fail": 0.85,
    # ── per-region color (background vs text separated) ───────────────────────
    "bg_deltaE_warn": 3.0, "bg_deltaE_fail": 6.0,      # background fill color
    "text_deltaE_warn": 4.0, "text_deltaE_fail": 8.0,  # text/foreground color (smaller area → a touch looser)
    # ── per-region typography ─────────────────────────────────────────────────
    "stroke_ratio_warn": 0.15, "stroke_ratio_fail": 0.25,  # font weight (đậm/nhạt): |Δstroke|/ref
    "size_ratio_warn": 0.10, "size_ratio_fail": 0.18,      # font size: |Δtext-height|/ref
    "shape_dist_warn": 0.07, "shape_dist_fail": 0.11,      # font family (LOW confidence): edge-orientation distance
    # ── per-region layout ─────────────────────────────────────────────────────
    "cell_ssim_warn": 0.82, "cell_ssim_fail": 0.62,        # local structure/alignment drift
    # ── grid ──────────────────────────────────────────────────────────────────
    "grid_rows": 6, "grid_cols": 4,
}

# Keep the typed findings list compact for the AI (the global metrics + summary carry the rest).
MAX_FINDINGS = 14


# ── IO + alignment ─────────────────────────────────────────────────────────────

def _load_rgb(path: Path) -> "np.ndarray":
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)  # BGR
    if img is None:
        raise FileNotFoundError(f"cannot read image: {path}")
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def _fit_work(ref: "np.ndarray", act: "np.ndarray", work: int):
    """Scale the reference so its longer side == `work`, then resize the actual to the SAME canvas,
    so every metric and grid cell lines up. A different aspect ratio is itself a recorded signal."""
    rh, rw = ref.shape[:2]
    scale = work / max(rh, rw)
    tw, th = max(1, int(round(rw * scale))), max(1, int(round(rh * scale)))
    ref_r = cv2.resize(ref, (tw, th), interpolation=cv2.INTER_AREA)
    act_r = cv2.resize(act, (tw, th), interpolation=cv2.INTER_AREA)
    return ref_r, act_r


# ── color helpers ──────────────────────────────────────────────────────────────

def _deltaE_rgb(a, b) -> float:
    """CIEDE2000 distance between two RGB triplets (perceptual; 0 = identical)."""
    la = rgb2lab(np.array(a, dtype=np.float32).reshape(1, 1, 3) / 255.0)
    lb = rgb2lab(np.array(b, dtype=np.float32).reshape(1, 1, 3) / 255.0)
    return float(deltaE_ciede2000(la, lb)[0, 0])


def _color_deltaE_map(ref: "np.ndarray", act: "np.ndarray"):
    lab_r = rgb2lab(ref.astype(np.float32) / 255.0)
    lab_a = rgb2lab(act.astype(np.float32) / 255.0)
    de = deltaE_ciede2000(lab_r, lab_a)
    return float(np.mean(de)), float(np.percentile(de, 95)), float(np.mean(de > 5.0) * 100.0), de


def _two_color(cell: "np.ndarray"):
    """Separate a cell into (background_rgb, foreground_rgb, fg_weight) via 2-means.

    The larger cluster is the background fill; the smaller, sufficiently-contrasting cluster is the
    foreground (text/icon). Returns fg=None when the cell is effectively one color (no real text)."""
    data = cell.reshape(-1, 3).astype(np.float32)
    if len(data) > 6000:
        idx = np.linspace(0, len(data) - 1, 6000).astype(int)
        data = data[idx]
    if len(np.unique(data, axis=0)) < 2:
        return [int(c) for c in data[0]], None, 0.0
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 15, 1.0)
    _, labels, centers = cv2.kmeans(data, 2, None, criteria, 2, cv2.KMEANS_PP_CENTERS)
    counts = np.bincount(labels.flatten(), minlength=2).astype(float)
    w = counts / counts.sum()
    big, small = (0, 1) if w[0] >= w[1] else (1, 0)
    bg = [int(c) for c in centers[big]]
    fg = [int(c) for c in centers[small]]
    fg_weight = float(w[small])
    # Real foreground only if it occupies a text-like minority AND contrasts with the background.
    if fg_weight < 0.04 or _deltaE_rgb(bg, fg) < 8.0:
        return bg, None, fg_weight
    return bg, fg, fg_weight


# ── typography helpers (on the text mask) ──────────────────────────────────────

def _ink_mask(cell: "np.ndarray"):
    """Binarize a cell so text/foreground = 255. Returns (mask, ink_ratio)."""
    gray = cv2.cvtColor(cell, cv2.COLOR_RGB2GRAY)
    _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    if (mask > 0).mean() > 0.5:  # foreground should be the minority — invert if needed
        mask = cv2.bitwise_not(mask)
    return mask, float((mask > 0).mean())


def _stroke_width(mask: "np.ndarray") -> float:
    """Mean stroke thickness of the text in a binary mask (distance transform → 2×mean ridge).
    Proportional to font weight: bold strokes are thicker. Comparable as a ref/actual ratio."""
    if (mask > 0).sum() < 12:
        return 0.0
    dist = cv2.distanceTransform(mask, cv2.DIST_L2, 3)
    vals = dist[mask > 0]
    return float(2.0 * np.mean(vals)) if len(vals) else 0.0


def _text_height(mask: "np.ndarray") -> float:
    """Median glyph height via connected components. Proxy for font size — far more stable across
    fonts/leading than a projection profile (which merges or splits lines differently per family)."""
    if (mask > 0).sum() < 12:
        return 0.0
    n, _lab, stats, _cent = cv2.connectedComponentsWithStats(mask, 8)
    H = mask.shape[0]
    hs = []
    for i in range(1, n):
        h = int(stats[i, cv2.CC_STAT_HEIGHT]); a = int(stats[i, cv2.CC_STAT_AREA])
        if 3 <= h <= 0.9 * H and a >= 3:   # ignore specks and full-cell blobs
            hs.append(h)
    return float(np.median(hs)) if hs else 0.0


def _shape_sig(cell: "np.ndarray", mask: "np.ndarray") -> "np.ndarray":
    """Edge-orientation histogram over the text pixels (12 bins, magnitude-weighted, L1-normalized).
    Different font families bend strokes differently (serif vs sans, geometric vs humanist), so the
    orientation distribution shifts — serif feet add horizontal energy, modulated strokes spread the
    angles. A low-confidence family hint; thresholds are calibrated to flag serif-vs-sans-class
    differences while letting near-identical fonts (Arial≈Helvetica) and anti-aliasing noise pass."""
    gray = cv2.cvtColor(cell, cv2.COLOR_RGB2GRAY).astype(np.float32)
    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    mag = np.sqrt(gx * gx + gy * gy)
    ang = (np.arctan2(gy, gx) % np.pi)  # 0..pi (undirected)
    sel = mask > 0
    if sel.sum() < 24:
        return np.zeros(12, dtype=np.float32)
    hist, _ = np.histogram(ang[sel], bins=12, range=(0, np.pi), weights=mag[sel])
    s = hist.sum()
    return (hist / s).astype(np.float32) if s > 0 else np.zeros(12, dtype=np.float32)


def _sig_distance(a: "np.ndarray", b: "np.ndarray") -> float:
    """L1/2 distance between two normalized histograms (0 identical .. 1 disjoint)."""
    if a.sum() == 0 or b.sum() == 0:
        return 0.0
    return float(0.5 * np.abs(a - b).sum())


# ── global metrics ─────────────────────────────────────────────────────────────

def _hist_corr(ref, act) -> float:
    hsv_r = cv2.cvtColor(ref, cv2.COLOR_RGB2HSV)
    hsv_a = cv2.cvtColor(act, cv2.COLOR_RGB2HSV)
    corrs = []
    for ch, bins, rng in ((0, 50, [0, 180]), (1, 60, [0, 256]), (2, 60, [0, 256])):
        h_r = cv2.calcHist([hsv_r], [ch], None, [bins], rng)
        h_a = cv2.calcHist([hsv_a], [ch], None, [bins], rng)
        cv2.normalize(h_r, h_r); cv2.normalize(h_a, h_a)
        corrs.append(cv2.compareHist(h_r, h_a, cv2.HISTCMP_CORREL))
    return float(np.mean(corrs))


def _dominant_palette(img, k=5):
    data = img.reshape(-1, 3).astype(np.float32)
    if len(data) > 20000:
        data = data[np.linspace(0, len(data) - 1, 20000).astype(int)]
    k = int(min(k, max(1, len(np.unique(data, axis=0)))))
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, labels, centers = cv2.kmeans(data, k, None, crit, 3, cv2.KMEANS_PP_CENTERS)
    counts = np.bincount(labels.flatten(), minlength=k).astype(float)
    w = counts / counts.sum()
    order = np.argsort(-w)
    return [([int(c) for c in centers[i]], float(w[i])) for i in order]


def _palette_match(ref, act) -> float:
    pr, pa = _dominant_palette(ref), _dominant_palette(act)
    weights = np.array([w for _, w in pr], dtype=np.float32)
    nearest = []
    for c, _ in pr:
        nearest.append(min(_deltaE_rgb(c, c2) for c2, _ in pa))
    return float(np.average(nearest, weights=weights))


def _phash_distance(ref_path: Path, act_path: Path) -> int:
    return int(imagehash.phash(Image.open(ref_path)) - imagehash.phash(Image.open(act_path)))


# ── per-region sweep → typed findings ──────────────────────────────────────────

def _region_label(r, c, rows, cols):
    vb = ["trên", "giữa", "dưới"][min(2, int(r / rows * 3))]
    hb = ["trái", "giữa", "phải"][min(2, int(c / cols * 3))]
    return f"r{r+1}c{c+1}", f"{vb}-{hb}"


def _hex(rgb) -> str:
    return "#%02X%02X%02X" % (int(rgb[0]), int(rgb[1]), int(rgb[2]))


def _grade(value, warn, fail, higher_is_worse=True):
    if higher_is_worse:
        return "fail" if value >= fail else ("warn" if value >= warn else "pass")
    return "fail" if value <= fail else ("warn" if value <= warn else "pass")


def _scan_regions(ref, act, th):
    """Walk the grid; per cell emit typed findings for color(bg/text), typography(weight/size/family)
    and layout. Returns (findings, summary_by_type)."""
    rows, cols = int(th["grid_rows"]), int(th["grid_cols"])
    H, W = ref.shape[:2]
    findings = []
    for r in range(rows):
        for c in range(cols):
            y0, y1 = r * H // rows, (r + 1) * H // rows
            x0, x1 = c * W // cols, (c + 1) * W // cols
            cr, ca = ref[y0:y1, x0:x1], act[y0:y1, x0:x1]
            if cr.size == 0 or ca.size == 0:
                continue
            label, human = _region_label(r, c, rows, cols)
            base = {"region": label, "where": human}

            # local layout / structure
            g_r = cv2.cvtColor(cr, cv2.COLOR_RGB2GRAY)
            g_a = cv2.cvtColor(ca, cv2.COLOR_RGB2GRAY)
            try:
                cell_ssim = float(ssim(g_r, g_a))
            except Exception:  # noqa: BLE001 — tiny/edge cells
                cell_ssim = 1.0
            sev = _grade(cell_ssim, th["cell_ssim_warn"], th["cell_ssim_fail"], higher_is_worse=False)
            if sev != "pass":
                findings.append({**base, "type": "layout.shift", "severity": sev,
                                 "ssim": round(cell_ssim, 3),
                                 "detail": f"bố cục/căn chỉnh khác (SSIM {cell_ssim:.2f})"})

            # color: background vs text
            bg_r, fg_r, fgw_r = _two_color(cr)
            bg_a, fg_a, fgw_a = _two_color(ca)
            de_bg = _deltaE_rgb(bg_r, bg_a)
            sev = _grade(de_bg, th["bg_deltaE_warn"], th["bg_deltaE_fail"])
            if sev != "pass":
                findings.append({**base, "type": "color.background", "severity": sev,
                                 "deltaE": round(de_bg, 1), "ref": _hex(bg_r), "actual": _hex(bg_a),
                                 "detail": f"màu nền lệch ΔE {de_bg:.1f} (design {_hex(bg_r)} → app {_hex(bg_a)})"})
            if fg_r is not None and fg_a is not None:
                de_tx = _deltaE_rgb(fg_r, fg_a)
                sev = _grade(de_tx, th["text_deltaE_warn"], th["text_deltaE_fail"])
                if sev != "pass":
                    findings.append({**base, "type": "color.text", "severity": sev,
                                     "deltaE": round(de_tx, 1), "ref": _hex(fg_r), "actual": _hex(fg_a),
                                     "detail": f"màu chữ lệch ΔE {de_tx:.1f} (design {_hex(fg_r)} → app {_hex(fg_a)})"})
            elif fg_r is not None and fg_a is None:
                findings.append({**base, "type": "content.flat", "severity": "warn",
                                 "detail": "design có nội dung/chữ ở vùng này nhưng app gần như phẳng "
                                           "(thiếu text hoặc khác state/data?)"})

            # typography (only where both sides actually have text-like ink)
            m_r, ink_r = _ink_mask(cr)
            m_a, ink_a = _ink_mask(ca)
            text_like = (0.02 <= ink_r <= 0.55) and (0.02 <= ink_a <= 0.55)
            if text_like:
                weight_flagged = False
                sw_r, sw_a = _stroke_width(m_r), _stroke_width(m_a)
                if sw_r > 0.5 and sw_a > 0.5:
                    ratio = abs(sw_a - sw_r) / sw_r
                    sev = _grade(ratio, th["stroke_ratio_warn"], th["stroke_ratio_fail"])
                    if sev != "pass":
                        weight_flagged = True
                        heavier = "đậm hơn" if sw_a > sw_r else "nhạt/mảnh hơn"
                        findings.append({**base, "type": "typography.weight", "severity": sev,
                                         "ref_stroke": round(sw_r, 2), "actual_stroke": round(sw_a, 2),
                                         "ratio": round(ratio, 2),
                                         "detail": f"độ đậm chữ khác: app {heavier} ~{ratio*100:.0f}% "
                                                   f"(stroke {sw_r:.2f}→{sw_a:.2f})"})
                size_failed = False
                h_r, h_a = _text_height(m_r), _text_height(m_a)
                if h_r > 3 and h_a > 3:
                    ratio = abs(h_a - h_r) / h_r
                    sev = _grade(ratio, th["size_ratio_warn"], th["size_ratio_fail"])
                    if sev != "pass":
                        size_failed = (sev == "fail")
                        bigger = "lớn hơn" if h_a > h_r else "nhỏ hơn"
                        findings.append({**base, "type": "typography.size", "severity": sev,
                                         "ref_h": round(h_r, 1), "actual_h": round(h_a, 1),
                                         "ratio": round(ratio, 2),
                                         "detail": f"cỡ chữ khác: app {bigger} ~{ratio*100:.0f}% "
                                                   f"(cao {h_r:.0f}px→{h_a:.0f}px)"})
                # font family — LOW confidence. Suppress when this cell already shows a strong weight or
                # size change: both perturb the edge-orientation signature, so flagging family too would
                # just double-count the same visible difference (false "different font"). Family stays
                # the signal when color/weight/size are steady but the letterforms still differ (serif↔sans).
                if not weight_flagged and not size_failed:
                    dist = _sig_distance(_shape_sig(cr, m_r), _shape_sig(ca, m_a))
                    sev = _grade(dist, th["shape_dist_warn"], th["shape_dist_fail"])
                    if sev != "pass":
                        findings.append({**base, "type": "typography.family", "severity": sev,
                                         "confidence": "low", "shape_distance": round(dist, 3),
                                         "detail": f"dáng chữ/độ cong nét khác (có thể khác font family, "
                                                   f"vd serif vs sans) — shape-distance {dist:.2f}, mắt người xác nhận"})

    # rank: fail before warn, larger magnitude first; cap for token thrift
    order = {"fail": 0, "warn": 1}
    findings.sort(key=lambda f: (order.get(f["severity"], 2),
                                 -float(f.get("deltaE", f.get("ratio", f.get("shape_distance", 0)) or 0))))
    summary = {}
    for f in findings:
        s = summary.setdefault(f["type"], {"fail": 0, "warn": 0, "regions": []})
        s[f["severity"]] = s.get(f["severity"], 0) + 1
        if len(s["regions"]) < 6:
            s["regions"].append(f["region"])
    return findings[:MAX_FINDINGS], summary


# ── verdict ────────────────────────────────────────────────────────────────────

def _verdict(metrics, summary, th):
    reasons, fail, warn = [], False, False

    if metrics["deltaE_mean"] >= th["deltaE_mean_fail"]:
        fail = True; reasons.append(f"màu tổng thể lệch — mean ΔE {metrics['deltaE_mean']:.1f}")
    elif metrics["deltaE_mean"] >= th["deltaE_mean_warn"]:
        warn = True
    if metrics["deltaE_p95"] >= th["deltaE_p95_fail"]:
        fail = True; reasons.append(f"một vùng lệch màu mạnh — p95 ΔE {metrics['deltaE_p95']:.1f}")
    if metrics["ssim"] <= th["ssim_fail"]:
        fail = True; reasons.append(f"bố cục/cấu trúc khác — SSIM {metrics['ssim']:.2f}")
    elif metrics["ssim"] <= th["ssim_warn"]:
        warn = True
    if metrics["phash_distance"] >= th["phash_fail"]:
        fail = True; reasons.append(f"tổng thể khác — pHash {metrics['phash_distance']}")
    if metrics["hist_corr"] <= th["hist_corr_fail"]:
        fail = True; reasons.append(f"phân bố màu khác — hist {metrics['hist_corr']:.2f}")
    if metrics["aspect_delta"] >= 0.15:
        warn = True; reasons.append(f"tỉ lệ khung khác {metrics['aspect_delta']*100:.0f}% (sai device/khung?)")

    # typed region findings drive the precise reasons
    label = {"color.background": "màu nền", "color.text": "màu chữ",
             "typography.weight": "độ đậm chữ", "typography.size": "cỡ chữ",
             "typography.family": "font chữ", "layout.shift": "bố cục",
             "content.flat": "nội dung/state"}
    for t, s in summary.items():
        if s.get("fail"):
            fail = True; reasons.append(f"{label.get(t, t)} sai ở {s['fail']} vùng ({', '.join(s['regions'][:3])})")
        elif s.get("warn"):
            warn = True; reasons.append(f"{label.get(t, t)} cận ngưỡng ở {s['warn']} vùng")

    verdict = "FAIL" if fail else ("WARN" if warn else "PASS")
    if not reasons:
        reasons.append("khớp design trong dung sai (màu/bố cục/font)")
    return verdict, reasons


def _write_heatmap(act, de_map, out: Path):
    norm = np.clip(de_map / 15.0, 0, 1)
    heat = cv2.applyColorMap((norm * 255).astype(np.uint8), cv2.COLORMAP_JET)
    base = cv2.cvtColor(act, cv2.COLOR_RGB2BGR)
    blend = cv2.addWeighted(base, 0.55, heat, 0.45, 0)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), blend)


def compare(ref_path: Path, act_path: Path, work: int, th: dict, diff: Path | None):
    ref = _load_rgb(ref_path)
    act = _load_rgb(act_path)
    rh, rw = ref.shape[:2]
    ah, aw = act.shape[:2]
    aspect_ref = rw / rh if rh else 0.0
    aspect_act = aw / ah if ah else 0.0
    aspect_delta = abs(aspect_ref - aspect_act) / max(aspect_ref, aspect_act, 1e-6)

    ref_r, act_r = _fit_work(ref, act, work)
    de_mean, de_p95, perceptible, de_map = _color_deltaE_map(ref_r, act_r)
    gray_r = cv2.cvtColor(ref_r, cv2.COLOR_RGB2GRAY)
    gray_a = cv2.cvtColor(act_r, cv2.COLOR_RGB2GRAY)
    ssim_val = float(ssim(gray_r, gray_a))

    metrics = {
        "deltaE_mean": round(de_mean, 2),
        "deltaE_p95": round(de_p95, 2),
        "color_perceptible_pct": round(perceptible, 1),
        "palette_deltaE": round(_palette_match(ref_r, act_r), 2),
        "ssim": round(ssim_val, 3),
        "hist_corr": round(_hist_corr(ref_r, act_r), 3),
        "phash_distance": _phash_distance(ref_path, act_path),
        "aspect_delta": round(aspect_delta, 3),
        "color_match_pct": round(max(0.0, 100.0 - de_mean / 0.1), 1),
    }

    findings, summary = _scan_regions(ref_r, act_r, th)
    verdict, reasons = _verdict(metrics, summary, th)

    if diff is not None:
        try:
            _write_heatmap(act_r, de_map, diff)
        except Exception:  # noqa: BLE001 — evidence-only
            diff = None

    return {
        "verdict": verdict, "reasons": reasons, "metrics": metrics,
        "findings": findings, "summary_by_type": summary,
        "sizes": {"reference": [rw, rh], "actual": [aw, ah],
                  "work": list(ref_r.shape[1::-1]), "grid": [int(th["grid_rows"]), int(th["grid_cols"])]},
        "heatmap": str(diff) if diff else None,
    }


def _load_thresholds(arg: str | None) -> dict:
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


def _parse_grid(s: str):
    try:
        r, c = s.lower().split("x")
        return max(1, int(r)), max(1, int(c))
    except Exception:  # noqa: BLE001
        return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Compare an app screenshot against a Figma reference (local CV).")
    ap.add_argument("--reference", required=True)
    ap.add_argument("--actual", required=True)
    ap.add_argument("--pair-id", default="")
    ap.add_argument("--screen", default="")
    ap.add_argument("--feature", default="")
    ap.add_argument("--out", default="")
    ap.add_argument("--log", default="")
    ap.add_argument("--diff", default="")
    ap.add_argument("--thresholds", default="")
    ap.add_argument("--work", type=int, default=768, help="working longer-side px (default 768)")
    ap.add_argument("--grid", default="", help="region grid RxC (e.g. 6x4) — overrides config")
    args = ap.parse_args(argv)

    ref_path, act_path = Path(args.reference), Path(args.actual)
    th = _load_thresholds(args.thresholds or None)
    g = _parse_grid(args.grid) if args.grid else None
    if g:
        th["grid_rows"], th["grid_cols"] = g
    diff = Path(args.diff) if args.diff else None

    try:
        result = compare(ref_path, act_path, args.work, th, diff)
    except FileNotFoundError as e:
        print(json.dumps({"ok": False, "pair_id": args.pair_id, "error": str(e)}, ensure_ascii=False))
        return 2
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"ok": False, "pair_id": args.pair_id,
                          "error": f"{type(e).__name__}: {e}"}, ensure_ascii=False))
        return 2

    out = {"ok": True, "pair_id": args.pair_id, "screen": args.screen, "feature": args.feature,
           "reference": str(ref_path), "actual": str(act_path), **result}

    if args.out:
        op = Path(args.out); op.parent.mkdir(parents=True, exist_ok=True)
        op.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.log:
        lp = Path(args.log); lp.parent.mkdir(parents=True, exist_ok=True)
        entry = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 "feature": args.feature, "pair_id": args.pair_id, "screen": args.screen,
                 "verdict": out["verdict"], "metrics": out["metrics"],
                 "summary_by_type": out["summary_by_type"], "thresholds": th, "sizes": out["sizes"]}
        with lp.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(json.dumps({k: out[k] for k in ("ok", "pair_id", "screen", "verdict", "reasons",
                                          "metrics", "findings", "summary_by_type", "heatmap")},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
