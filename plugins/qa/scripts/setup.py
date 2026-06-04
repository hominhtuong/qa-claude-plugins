#!/usr/bin/env python3
"""One-shot project setup for the qa plugin — cross-platform (Windows/macOS/Linux).

All plugin config lives in ONE folder, separate from the project's own ./.env:

    <project>/.claude/qa-claude/
      .env                     # 🔒 secrets (Lark/R2/S3/notify) — ONE sectioned file.  SCAFFOLD (never overwritten)
      .env.example             # reference for .env keys.                               OVERWRITE (refreshed on update)
      log-bug.config.yml       # 🧩 board ids + dev-pic/field mappings (user-filled).   SCAFFOLD (never overwritten)
      log-bug.config.example.yml # reference for the config schema.                     OVERWRITE
      testcase-template.md     # 📄 test-case format (plugin-owned).                    OVERWRITE

SCAFFOLD = create only if missing (protects your secrets / board config).
OVERWRITE = always refreshed from the plugin (so an update brings the latest schema/format).

Usage:
    python3 setup.py            # scaffold + refresh .claude/qa-claude + doctor (auto-install wrangler)
    python3 setup.py --update   # alias — same behaviour (refresh the OVERWRITE files)
    python3 setup.py --no-fix   # skip wrangler auto-install, report only
"""
import shutil
import sys
from pathlib import Path

import doctor
from _env import project_root

PLUGIN_ROOT = Path(__file__).resolve().parent.parent      # scripts/ -> plugin root
ENV_TEMPLATE = PLUGIN_ROOT / "templates" / ".env.example"
MANAGED_SRC = PLUGIN_ROOT / "templates" / "qa-claude"     # testcase-template.md, log-bug.config.yml
MANAGED_DIR = ".claude/qa-claude"
GITIGNORE_LINES = [".claude/qa-claude/.env", ".qa-venv/", "results/tests/"]


def _copy(src: Path, dst: Path, overwrite: bool):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and not overwrite:
        print(f"[setup]   keep   {dst.name}  (already exists — left untouched)")
        return
    shutil.copyfile(src, dst)
    print(f"[setup]   {'write ' if overwrite else 'create'} {dst.name}")


def install_managed(root: Path):
    """Install all plugin config into <project>/.claude/qa-claude/.

    For each user-config file: refresh a `<name>.example` (OVERWRITE) + scaffold the
    real file (SCAFFOLD). Pure templates are OVERWRITE.
    """
    dst_dir = root / MANAGED_DIR
    dst_dir.mkdir(parents=True, exist_ok=True)
    print(f"[setup] {dst_dir}/")

    # 1) secrets: .env (scaffold) + .env.example (overwrite reference)
    if ENV_TEMPLATE.is_file():
        _copy(ENV_TEMPLATE, dst_dir / ".env.example", overwrite=True)
        _copy(ENV_TEMPLATE, dst_dir / ".env", overwrite=False)

    # 2) log-bug config: .yml (scaffold) + .example.yml (overwrite reference)
    cfg = MANAGED_SRC / "log-bug.config.yml"
    if cfg.is_file():
        _copy(cfg, dst_dir / "log-bug.config.example.yml", overwrite=True)
        _copy(cfg, dst_dir / "log-bug.config.yml", overwrite=False)

    # 3) pure plugin-owned templates: always overwrite
    for name in ("testcase-template.md",):
        src = MANAGED_SRC / name
        if src.is_file():
            _copy(src, dst_dir / name, overwrite=True)

    print("[setup] (edit .env + log-bug.config.yml — these are yours and never overwritten)")


def patch_gitignore(root: Path):
    gi = root / ".gitignore"
    existing = gi.read_text(encoding="utf-8").splitlines() if gi.exists() else []
    present = set(line.strip() for line in existing)
    to_add = [ln for ln in GITIGNORE_LINES if ln not in present]
    if not to_add:
        print("[setup] .gitignore already covers the plugin's secret .env / caches")
        return
    block = (["", "# qa-claude plugin"] if existing else ["# qa-claude plugin"]) + to_add
    with gi.open("a", encoding="utf-8") as f:
        f.write(("\n" if existing and existing[-1].strip() else "") + "\n".join(block) + "\n")
    print(f"[setup] added to .gitignore: {', '.join(to_add)}")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    root = project_root()
    print(f"== qa-plugin setup (project: {root}) ==")
    install_managed(root)
    patch_gitignore(root)
    print()
    return doctor.run(fix="--no-fix" not in argv)


if __name__ == "__main__":
    sys.exit(main())
