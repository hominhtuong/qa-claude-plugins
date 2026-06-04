#!/usr/bin/env python3
"""One-shot project setup for the qa plugin — cross-platform (Windows/macOS/Linux).

Does NOT put any secret in the plugin. It:
  1. Scaffolds ./.env in the PROJECT from templates/.env.example (NEVER overwrites — holds secrets).
  2. Installs editable resources into ./.claude/qa-claude/ from templates/qa-claude/
     (testcase-template.md, log-bug.config.yml, ...). These are plugin-MANAGED:
     re-running setup (or `--update`) OVERWRITES them so a plugin update refreshes them.
  3. Patches the project's .gitignore so .env / upload-logs are never committed.
  4. Runs the toolchain doctor (with --fix to auto-install wrangler when npm is present).

Usage:
    python3 setup.py            # scaffold .env (if missing) + (re)install .claude/qa-claude + doctor
    python3 setup.py --update   # same; explicit alias — re-installs managed resources
    python3 setup.py --no-fix   # skip wrangler auto-install, report only
"""
import shutil
import sys
from pathlib import Path

import doctor
from _env import project_root

PLUGIN_ROOT = Path(__file__).resolve().parent.parent  # scripts/ -> plugin root
ENV_TEMPLATE = PLUGIN_ROOT / "templates" / ".env.example"
MANAGED_SRC = PLUGIN_ROOT / "templates" / "qa-claude"   # editable resources to install
MANAGED_DIR = ".claude/qa-claude"                       # destination inside the project
GITIGNORE_LINES = [".env", ".qa-venv/", "reports/upload-logs/"]


def scaffold_env(root: Path):
    """Create ./.env from the template if missing. NEVER overwrite (it holds secrets)."""
    dst = root / ".env"
    if dst.exists():
        print(f"[setup] .env already exists at {dst} — left untouched (secrets)")
        return
    if not ENV_TEMPLATE.is_file():
        print(f"[setup] WARN: env template not found: {ENV_TEMPLATE}")
        return
    dst.write_text(ENV_TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"[setup] created {dst} — fill in real values (Lark/R2/S3...)")


def install_managed(root: Path):
    """Copy templates/qa-claude/* into <project>/.claude/qa-claude/ — ALWAYS OVERWRITE.

    These are plugin-managed defaults the user can tweak between updates; a plugin
    update + re-run refreshes them. The destination folder name (.claude/qa-claude)
    signals it is overwrite-managed.
    """
    if not MANAGED_SRC.is_dir():
        print(f"[setup] no managed resources at {MANAGED_SRC} — skip")
        return
    dst_dir = root / MANAGED_DIR
    dst_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for src in sorted(MANAGED_SRC.rglob("*")):
        if src.is_file():
            rel = src.relative_to(MANAGED_SRC)
            dst = dst_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)   # overwrite
            count += 1
    print(f"[setup] installed {count} file(s) into {dst_dir}/ (overwritten — edit to customize)")


def patch_gitignore(root: Path):
    gi = root / ".gitignore"
    existing = gi.read_text(encoding="utf-8").splitlines() if gi.exists() else []
    present = set(line.strip() for line in existing)
    to_add = [ln for ln in GITIGNORE_LINES if ln not in present]
    if not to_add:
        print("[setup] .gitignore already covers .env / upload-logs")
        return
    block = (["", "# qa-claude plugin"] if existing else ["# qa-claude plugin"]) + to_add
    with gi.open("a", encoding="utf-8") as f:
        f.write(("\n" if existing and existing[-1].strip() else "") + "\n".join(block) + "\n")
    print(f"[setup] added to .gitignore: {', '.join(to_add)}")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    root = project_root()
    print(f"== qa-plugin setup (project: {root}) ==")
    scaffold_env(root)
    install_managed(root)
    patch_gitignore(root)
    print()
    return doctor.run(fix="--no-fix" not in argv)


if __name__ == "__main__":
    sys.exit(main())
