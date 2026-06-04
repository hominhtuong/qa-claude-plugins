#!/usr/bin/env python3
"""Regenerate sitemap/sitemap.json from sitemap/screens/*.json (the source of truth).

Cross-platform, stdlib-only. This is the navigation-map generator the AI runs after
adding/updating any screen node. It:
  - reads every `sitemap/screens/<id>.json`,
  - auto-derives `childrenIds` from each node's `parentId` (so you only set parentId),
  - warns on dangling parentId / id≠filename / invalid JSON (non-fatal),
  - writes the aggregate `sitemap/sitemap.json`,
  - ensures `sitemap/SCHEMA.md` exists (copies the plugin's schema doc if missing).

Schema: see sitemap/SCHEMA.md. Used by skill `update-sitemap` (exploratory/cook).

Usage:  python3 gen_sitemap.py [--dir <project root>]
"""
import argparse
import json
import sys
from pathlib import Path

from _env import project_root

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_SRC = PLUGIN_ROOT / "templates" / "sitemap" / "SCHEMA.md"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Regenerate sitemap/sitemap.json")
    ap.add_argument("--dir", default=None, help="project root (default: $CLAUDE_PROJECT_DIR or cwd)")
    args = ap.parse_args(argv)

    root = Path(args.dir) if args.dir else project_root()
    sm = root / "sitemap"
    screens = sm / "screens"
    screens.mkdir(parents=True, exist_ok=True)

    # ensure SCHEMA.md
    schema = sm / "SCHEMA.md"
    if not schema.exists() and SCHEMA_SRC.is_file():
        schema.write_text(SCHEMA_SRC.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"[sitemap] wrote {schema}")

    nodes, warns = {}, []
    for f in sorted(screens.glob("*.json")):
        try:
            node = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            warns.append(f"{f.name}: invalid JSON ({e})")
            continue
        nid = node.get("id") or f.stem
        node.setdefault("id", nid)
        if nid != f.stem:
            warns.append(f"{f.name}: id '{nid}' != filename '{f.stem}'")
        if nid in nodes:
            warns.append(f"{f.name}: duplicate id '{nid}'")
        nodes[nid] = node

    # auto-derive childrenIds from parentId, merged with any explicit ones
    children = {}
    for nid, node in nodes.items():
        parent = node.get("parentId")
        if parent:
            children.setdefault(parent, []).append(nid)
    for nid, node in nodes.items():
        node["childrenIds"] = sorted(set(node.get("childrenIds") or []) | set(children.get(nid, [])))
        parent = node.get("parentId")
        if parent and parent not in nodes:
            warns.append(f"{nid}: parentId '{parent}' not found")

    out = {
        "source": "sitemap/screens/*.json (source of truth — edit those; this file is generated)",
        "count": len(nodes),
        "nodes": nodes,
    }
    (sm / "sitemap.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[sitemap] generated {sm / 'sitemap.json'} — {len(nodes)} screen(s)")
    for w in warns:
        print(f"[sitemap] WARN: {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
