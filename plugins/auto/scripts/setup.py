#!/usr/bin/env python3
"""One-shot project setup for the `auto` plugin — cross-platform (Windows/macOS/Linux).

Does NOT put any secret in the plugin. It:
  1. Scaffolds ./.env in the PROJECT from the plugin's templates/.env.example (never overwrites).
  2. Patches the project's .gitignore so .env / upload-logs are never committed.
  3. Runs the toolchain doctor (with --fix to auto-install wrangler when npm is present).

Usage:
    python3 setup.py            # scaffold + gitignore + doctor (auto-install wrangler)
    python3 setup.py --no-fix   # skip auto-install, report only
"""
import sys
from pathlib import Path

import doctor
from _env import project_root

PLUGIN_ROOT = Path(__file__).resolve().parent.parent  # scripts/ -> plugin root
TEMPLATE = PLUGIN_ROOT / "templates" / ".env.example"
GITIGNORE_LINES = [".env", ".qa-venv/", "reports/upload-logs/"]


def scaffold_env(root: Path) -> bool:
    dst = root / ".env"
    if dst.exists():
        print(f"[setup] .env already exists at {dst} — left untouched")
        return False
    if not TEMPLATE.is_file():
        print(f"[setup] ERROR: template not found: {TEMPLATE}")
        return False
    dst.write_text(TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"[setup] created {dst} from template — fill in real Lark/R2 values")
    return True


def patch_gitignore(root: Path):
    gi = root / ".gitignore"
    existing = gi.read_text(encoding="utf-8").splitlines() if gi.exists() else []
    present = set(line.strip() for line in existing)
    to_add = [ln for ln in GITIGNORE_LINES if ln not in present]
    if not to_add:
        print("[setup] .gitignore already covers .env / upload-logs")
        return
    block = (["", "# qa-claude auto plugin"] if existing else ["# qa-claude auto plugin"]) + to_add
    with gi.open("a", encoding="utf-8") as f:
        f.write(("\n" if existing and existing[-1].strip() else "") + "\n".join(block) + "\n")
    print(f"[setup] added to .gitignore: {', '.join(to_add)}")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    root = project_root()
    print(f"== auto-plugin setup (project: {root}) ==")
    scaffold_env(root)
    patch_gitignore(root)
    print()
    return doctor.run(fix="--no-fix" not in argv)


if __name__ == "__main__":
    sys.exit(main())
