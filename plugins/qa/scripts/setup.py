#!/usr/bin/env python3
"""One-shot project setup for the qa plugin — cross-platform (Windows/macOS/Linux).

All plugin config lives in ONE folder, separate from the project's own ./.env:

    <project>/.claude/qa-claude/
      .plugin.env              # 🔒 secrets (Lark/R2/S3/notify) — ONE sectioned file.  SCAFFOLD (never overwritten)
      .plugin.env.example      # reference for .plugin.env keys.                        OVERWRITE (refreshed on update)
      log-bug.config.yml       # 🧩 board ids + dev-pic/field mappings (user-filled).   SCAFFOLD (never overwritten)
      log-bug.config.example.yml # reference for the config schema.                     OVERWRITE
      release-gate.config.yml  # 🚦 Go/No-Go criteria for /qa:release-gate (user-filled).SCAFFOLD (never overwritten)
      release-gate.config.example.yml # reference for the gate schema.                   OVERWRITE
      testcase-template.md     # 📄 test-case format (plugin-owned).                    OVERWRITE
      README.md                # 📖 usage guide — full command list (auto-generated).   OVERWRITE

SCAFFOLD = create only if missing (protects your secrets / board config).
OVERWRITE = always refreshed from the plugin (so an update brings the latest schema/format).

Usage:
    python3 setup.py            # scaffold + refresh .claude/qa-claude + doctor (auto-install wrangler + truststore)
    python3 setup.py --update   # alias — same behaviour (refresh the OVERWRITE files)
    python3 setup.py --no-fix   # skip auto-install (wrangler/truststore), report only
"""
import shutil
import sys
from pathlib import Path

import doctor
import gen_guide
from _env import project_root

PLUGIN_ROOT = Path(__file__).resolve().parent.parent      # scripts/ -> plugin root
ENV_TEMPLATE = PLUGIN_ROOT / "templates" / ".plugin.env.example"
MANAGED_SRC = PLUGIN_ROOT / "templates" / "qa-claude"     # testcase-template.md, log-bug.config.yml
MANAGED_DIR = ".claude/qa-claude"
GITIGNORE_LINES = [".claude/qa-claude/.plugin.env", ".qa-venv/", "results/tests/",
                   ".claude/qa-claude/ui-engine/", ".claude/qa-claude/ui-engine.config.json"]


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

    # 0) migrate a pre-0.0.5 .env -> .plugin.env (keep the user's secrets, drop the old name)
    legacy = dst_dir / ".env"
    if legacy.is_file() and not (dst_dir / ".plugin.env").is_file():
        legacy.rename(dst_dir / ".plugin.env")
        print("[setup]   move   .env -> .plugin.env  (migrated your secrets to the new name)")
    if (dst_dir / ".env.example").is_file():
        (dst_dir / ".env.example").unlink()   # superseded by .plugin.env.example

    # 1) secrets: .plugin.env (scaffold) + .plugin.env.example (overwrite reference)
    if ENV_TEMPLATE.is_file():
        _copy(ENV_TEMPLATE, dst_dir / ".plugin.env.example", overwrite=True)
        _copy(ENV_TEMPLATE, dst_dir / ".plugin.env", overwrite=False)

    # 2) user-edited config: .yml (scaffold, kept) + .example.yml (overwrite reference)
    for name in ("log-bug.config.yml", "release-gate.config.yml"):
        cfg = MANAGED_SRC / name
        if cfg.is_file():
            example = name.replace(".yml", ".example.yml")
            _copy(cfg, dst_dir / example, overwrite=True)
            _copy(cfg, dst_dir / name, overwrite=False)

    # 3) pure plugin-owned templates: always overwrite
    for name in ("testcase-template.md",):
        src = MANAGED_SRC / name
        if src.is_file():
            _copy(src, dst_dir / name, overwrite=True)

    # 4) usage guide: README.md listing every command (OVERWRITE — regenerated each run)
    guide = gen_guide.install(dst_dir)
    print(f"[setup]   write  {guide.name}  (usage guide — full command list, auto-generated)")

    print("[setup] (edit .plugin.env + log-bug.config.yml — these are yours and never overwritten)")


def patch_gitignore(root: Path):
    gi = root / ".gitignore"
    existing = gi.read_text(encoding="utf-8").splitlines() if gi.exists() else []
    present = set(line.strip() for line in existing)
    to_add = [ln for ln in GITIGNORE_LINES if ln not in present]
    if not to_add:
        print("[setup] .gitignore already covers the plugin's secret .plugin.env / caches")
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
