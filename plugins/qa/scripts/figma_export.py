#!/usr/bin/env python3
"""Export Figma frames to PNG files — cross-platform, stdlib-only (urllib + the plugin's TLS ctx).

WHY: /qa:exploratory-ui needs each design screen as a real PNG FILE on disk so the local CV engine
(ui_compare.py) can diff it against the app screenshot. The Figma MCP `get_screenshot` returns an
image into the AI's context (good for the AI to LOOK at) but not a file the CV math can open. The
Figma REST "images" endpoint renders any node to a PNG URL we then download — scriptable, no MCP,
works headless. Needs a Figma personal access token (Figma → Settings → Security → personal access
tokens) in .plugin.env as FIGMA_TOKEN (FIGMA_ACCESS_TOKEN / FIGMA_PERSONAL_TOKEN also accepted).

Subcommands:
    list   --url <figmaUrl> [--json]                 list the frames under the node (id, name, type)
    export --url <figmaUrl> --out <dir> [--scale 2] [--ids id1,id2] [--json]
                                                     render frames to <dir>/fm_<idx>-<slug>.png + manifest.json

Reads no secret from the CLI — FIGMA_TOKEN comes from .claude/qa-claude/.plugin.env (git-ignored).
Output JSON: { ok, file_key, node_id, frames:[{node_id,name,type,file?}], manifest? }
Exit codes: 0 ok · 2 missing/invalid token · 3 Figma API/HTTP error · 4 bad input.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _env import (ensure_utf8_io, load_env, make_ssl_context,  # noqa: E402
                  is_ssl_cert_error, ssl_help_text)

ensure_utf8_io()
load_env()

import os  # noqa: E402

API = "https://api.figma.com/v1"
FRAME_TYPES = {"FRAME", "COMPONENT", "COMPONENT_SET", "INSTANCE"}
CONTAINER_TYPES = {"CANVAS", "SECTION", "GROUP", "DOCUMENT"}


def _token() -> str:
    for key in ("FIGMA_TOKEN", "FIGMA_ACCESS_TOKEN", "FIGMA_PERSONAL_TOKEN"):
        v = (os.environ.get(key) or "").strip()
        if v and not v.lower().startswith(("your_", "figd_xxx")):
            return v
    return ""


def parse_url(url: str) -> tuple[str, str]:
    """Extract (file_key, node_id) from a Figma URL. node_id is returned API-form (':' not '-')."""
    m = re.search(r"figma\.com/(?:design|file|board)/([A-Za-z0-9]+)", url)
    file_key = m.group(1) if m else ""
    # A branch URL nests the real key after /branch/<branchKey>/
    mb = re.search(r"/branch/([A-Za-z0-9]+)", url)
    if mb:
        file_key = mb.group(1)
    node_id = ""
    q = urllib.parse.urlparse(url).query
    params = urllib.parse.parse_qs(q)
    if "node-id" in params:
        node_id = params["node-id"][0].replace("-", ":")
    return file_key, node_id


def _get(path: str, token: str, ctx) -> dict:
    req = urllib.request.Request(API + path, headers={"X-Figma-Token": token})
    with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
        return json.loads(r.read().decode("utf-8"))


def _slug(name: str, idx: int) -> str:
    """Stable ASCII kebab filename, transliterating Vietnamese diacritics (Hóa đơn → hoa-don)
    so the rendered PNG keeps a recognizable name (file/folder names stay diacritic-free)."""
    import unicodedata
    s = (name or "").replace("đ", "d").replace("Đ", "D")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))  # drop accents, keep base letters
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    s = s[:40] or "frame"
    return f"fm_{idx:03d}-{s}"


def resolve_frames(file_key: str, node_id: str, token: str, ctx) -> tuple[list[dict], str]:
    """Return the list of frames to export ([{node_id,name,type}]) + the resolved root node id.

    If the URL points at a single FRAME/COMPONENT → export just it. If it points at a PAGE/SECTION
    (a container) → export its direct frame children. If no node-id → use the file's first page.
    """
    if node_id:
        data = _get(f"/files/{file_key}/nodes?ids={urllib.parse.quote(node_id)}", token, ctx)
        node = (data.get("nodes", {}).get(node_id) or {}).get("document")
        if not node:
            return [], node_id
        ntype = node.get("type", "")
        if ntype in FRAME_TYPES:
            return [{"node_id": node_id, "name": node.get("name", ""), "type": ntype}], node_id
        # container → direct frame children
        frames = [{"node_id": c["id"], "name": c.get("name", ""), "type": c.get("type", "")}
                  for c in node.get("children", []) if c.get("type") in FRAME_TYPES]
        if frames:
            return frames, node_id
        return [{"node_id": node_id, "name": node.get("name", ""), "type": ntype}], node_id
    # No node-id: take the first canvas of the file and its frame children.
    data = _get(f"/files/{file_key}", token, ctx)
    doc = data.get("document", {})
    for canvas in doc.get("children", []):
        frames = [{"node_id": c["id"], "name": c.get("name", ""), "type": c.get("type", "")}
                  for c in canvas.get("children", []) if c.get("type") in FRAME_TYPES]
        if frames:
            return frames, canvas.get("id", "")
    return [], ""


def render_urls(file_key: str, ids: list[str], scale: float, token: str, ctx) -> dict:
    """Ask Figma to render the given node ids to PNG; returns {node_id: image_url}."""
    out: dict[str, str] = {}
    # The images endpoint accepts many ids per call; chunk to stay well under URL limits.
    for i in range(0, len(ids), 20):
        chunk = ids[i:i + 20]
        q = urllib.parse.urlencode({"ids": ",".join(chunk), "format": "png", "scale": scale})
        data = _get(f"/images/{file_key}?{q}", token, ctx)
        if data.get("err"):
            raise RuntimeError(f"Figma images error: {data['err']}")
        out.update({k: v for k, v in (data.get("images") or {}).items() if v})
    return out


def _hex_from_fills(fills) -> str:
    """First visible SOLID fill → #RRGGBB. '' if none (e.g. image/gradient text)."""
    for f in (fills or []):
        if f.get("type") == "SOLID" and f.get("visible", True):
            c = f.get("color", {})
            r, g, b = (int(round(c.get(k, 0) * 255)) for k in ("r", "g", "b"))
            return "#%02X%02X%02X" % (r, g, b)
    return ""


def _weight_name(w) -> str:
    """Figma fontWeight number → a human name designers use (Regular/Medium/Bold/…)."""
    try:
        w = int(w)
    except Exception:  # noqa: BLE001
        return ""
    table = [(100, "Thin"), (200, "ExtraLight"), (300, "Light"), (400, "Regular"),
             (500, "Medium"), (600, "SemiBold"), (700, "Bold"), (800, "ExtraBold"), (900, "Black")]
    return min(table, key=lambda t: abs(t[0] - w))[1]


def _walk_text_nodes(node: dict, origin, acc: list):
    """Collect every TEXT descendant with its design tokens, bbox relative to the frame origin."""
    if node.get("type") == "TEXT" and node.get("characters"):
        st = node.get("style", {})
        bb = node.get("absoluteBoundingBox") or {}
        rel = None
        if bb and origin:
            rel = [round(bb.get("x", 0) - origin[0], 1), round(bb.get("y", 0) - origin[1], 1),
                   round(bb.get("width", 0), 1), round(bb.get("height", 0), 1)]
        acc.append({
            "text": node.get("characters", ""),
            "color": _hex_from_fills(node.get("fills")),
            "fontFamily": st.get("fontFamily", ""),
            "fontWeight": _weight_name(st.get("fontWeight")),
            "fontSize": st.get("fontSize"),
            "bbox": rel,  # [x,y,w,h] in Figma px, relative to the frame's top-left
        })
    for ch in node.get("children", []) or []:
        _walk_text_nodes(ch, origin, acc)


def fetch_text_styles(file_key: str, frames: list, token: str, ctx) -> dict:
    """For each frame, return its exact TEXT nodes (content + color + font + size + bbox).

    This is the DESIGN ORACLE for text: exact, no OCR error. The app side is OCR'd and compared
    against this so a changed static label (Products → Product) is caught while dynamic values pass.
    """
    ids = [f["node_id"] for f in frames]
    out: dict = {}
    for i in range(0, len(ids), 10):
        chunk = ids[i:i + 10]
        data = _get(f"/files/{file_key}/nodes?ids={urllib.parse.quote(','.join(chunk))}", token, ctx)
        for nid in chunk:
            doc = (data.get("nodes", {}).get(nid) or {}).get("document")
            if not doc:
                continue
            bb = doc.get("absoluteBoundingBox") or {}
            origin = [bb.get("x", 0), bb.get("y", 0)] if bb else None
            acc: list = []
            _walk_text_nodes(doc, origin, acc)
            out[nid] = {"frame": doc.get("name", ""), "frame_size": [bb.get("width"), bb.get("height")] if bb else None,
                        "texts": acc}
    return out


def _download(url: str, dest: Path, ctx) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=120, context=ctx) as r:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(r.read())
        return dest.is_file() and dest.stat().st_size > 0
    except Exception:  # noqa: BLE001
        return False


def _fail(as_json: bool, code: int, msg: str, **extra) -> int:
    out = {"ok": False, "error": msg, **extra}
    print(json.dumps(out, ensure_ascii=False, indent=2) if as_json else f"❌ {msg}", file=sys.stderr)
    return code


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Export Figma frames to PNG files for /qa:exploratory-ui")
    sub = ap.add_subparsers(dest="cmd")
    for name in ("list", "export", "text-styles"):
        sp = sub.add_parser(name)
        sp.add_argument("--url", required=True, help="Figma design URL (with ?node-id=...)")
        sp.add_argument("--json", action="store_true", help="machine-readable output")
        if name in ("export", "text-styles"):
            sp.add_argument("--out", required=True, help="output directory for the PNGs + manifest.json")
        if name == "export":
            sp.add_argument("--scale", type=float, default=2.0, help="render scale (default 2x)")
            sp.add_argument("--ids", default="", help="comma-separated node ids to export (overrides auto-resolve)")
    args = ap.parse_args(argv)
    if not args.cmd:
        ap.print_help()
        return 4

    token = _token()
    if not token:
        return _fail(args.json, 2,
                     "No Figma token — set FIGMA_TOKEN in .claude/qa-claude/.plugin.env "
                     "(Figma → Settings → Security → personal access tokens, scope: File content read).")

    file_key, node_id = parse_url(args.url)
    if not file_key:
        return _fail(args.json, 4, f"could not parse a Figma file key from URL: {args.url}")

    ctx = make_ssl_context()
    try:
        frames, root = resolve_frames(file_key, node_id, token, ctx)
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8")[:300]
        except Exception:  # noqa: BLE001
            pass
        if e.code in (401, 403):
            return _fail(args.json, 2, f"Figma auth failed (HTTP {e.code}) — token invalid or lacks file access. {body}")
        return _fail(args.json, 3, f"Figma API HTTP {e.code}: {body}")
    except Exception as e:  # noqa: BLE001
        msg = str(e)
        if is_ssl_cert_error(msg):
            return _fail(args.json, 3, "TLS verify failed reaching Figma.\n" + ssl_help_text())
        return _fail(args.json, 3, f"Figma API error: {msg}")

    if not frames:
        return _fail(args.json, 3, f"no frames found under node {node_id or '(file root)'} in {file_key}")

    if args.cmd == "list":
        out = {"ok": True, "file_key": file_key, "node_id": node_id or root, "frames": frames}
        print(json.dumps(out, ensure_ascii=False, indent=2) if args.json
              else "\n".join(f"{i+1:>2}. {f['node_id']:<16} [{f['type']}] {f['name']}" for i, f in enumerate(frames)))
        return 0

    if args.cmd == "text-styles":
        try:
            styles = fetch_text_styles(file_key, frames, token, ctx)
        except Exception as e:  # noqa: BLE001
            return _fail(args.json, 3, f"Figma text-styles error: {e}")
        out_dir = Path(args.out); out_dir.mkdir(parents=True, exist_ok=True)
        per_slug = {}
        for idx, f in enumerate(frames, 1):
            per_slug[_slug(f["name"], idx)] = styles.get(f["node_id"], {"frame": f["name"], "texts": []})
        sp = out_dir / "text-styles.json"
        sp.write_text(json.dumps(per_slug, ensure_ascii=False, indent=2), encoding="utf-8")
        total = sum(len(v.get("texts", [])) for v in per_slug.values())
        out = {"ok": True, "file_key": file_key, "frames": len(per_slug), "text_nodes": total, "file": str(sp)}
        print(json.dumps(out, ensure_ascii=False, indent=2) if args.json
              else f"{total} text nodes across {len(per_slug)} frames → {sp}")
        return 0

    # export
    if args.ids:
        want = {i.strip().replace("-", ":") for i in args.ids.split(",") if i.strip()}
        frames = [f for f in frames if f["node_id"] in want] or [{"node_id": i, "name": "", "type": ""} for i in want]
    ids = [f["node_id"] for f in frames]
    try:
        urls = render_urls(file_key, ids, args.scale, token, ctx)
    except Exception as e:  # noqa: BLE001
        return _fail(args.json, 3, f"Figma render error: {e}")

    out_dir = Path(args.out)
    manifest = []
    for idx, f in enumerate(frames, 1):
        url = urls.get(f["node_id"])
        slug = _slug(f["name"], idx)
        dest = out_dir / f"{slug}.png"
        ok = bool(url) and _download(url, dest, ctx)
        manifest.append({"index": idx, "node_id": f["node_id"], "name": f["name"],
                         "type": f["type"], "file": str(dest) if ok else None,
                         "slug": slug, "exported": ok})

    man_path = out_dir / "manifest.json"
    out_dir.mkdir(parents=True, exist_ok=True)
    man_path.write_text(json.dumps({"file_key": file_key, "node_id": node_id or root,
                                    "scale": args.scale, "frames": manifest},
                                   ensure_ascii=False, indent=2), encoding="utf-8")

    # Also capture the exact design text oracle (best-effort — text comparison needs it, but a render
    # is still useful without it). Keyed by the same slug as the PNGs so the comparator can pair them.
    text_nodes = 0
    try:
        styles = fetch_text_styles(file_key, frames, token, ctx)
        per_slug = {m["slug"]: styles.get(m["node_id"], {"frame": m["name"], "texts": []}) for m in manifest}
        (out_dir / "text-styles.json").write_text(json.dumps(per_slug, ensure_ascii=False, indent=2), encoding="utf-8")
        text_nodes = sum(len(v.get("texts", [])) for v in per_slug.values())
    except Exception:  # noqa: BLE001 — never fail the export over the text oracle
        pass

    exported = [m for m in manifest if m["exported"]]
    out = {"ok": bool(exported), "file_key": file_key, "node_id": node_id or root,
           "exported_count": len(exported), "total": len(manifest),
           "manifest": str(man_path), "frames": manifest}
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        for m in manifest:
            print(("✅ " if m["exported"] else "❌ ") + f"{m['slug']:<32} {m['name']}")
        print(f"\n{len(exported)}/{len(manifest)} exported → {out_dir}  (manifest: {man_path})")
    return 0 if exported else 3


if __name__ == "__main__":
    sys.exit(main())
