#!/usr/bin/env python3
"""Launcher for the bundled Playwright MCP that honors a project headless preference.

Why a launcher instead of a hardcoded flag in .mcp.json: `--headless` is decided when
the MCP server starts, so it must be resolved BEFORE `@playwright/mcp` launches. This
thin wrapper reads the preference from the project, then execs the real server with (or
without) `--headless`. It writes NOTHING to stdout — stdout is the MCP stdio channel.

Headless resolution order (first hit wins):
  1. The main project's ./.env           — QA_HEADLESS / HEADLESS
  2. Shell env + the plugin's .plugin.env — QA_HEADLESS / HEADLESS  (loaded via _env)
  3. Default: headed (visible browser)    — matches Playwright's own default

Note: a project that configures its OWN `playwright` server in .mcp.json replaces this
bundle entirely (same-name override), so it controls headless on its own and this
launcher never runs — that is the intended ".mcp.json then default" layer.

Accepted truthy values for the env var: 1 / true / yes / on (case-insensitive).
Set QA_HEADLESS=false to force a visible browser explicitly.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

# _env.py lives next to this file; cwd is the project dir, not here.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _env import load_env, project_root  # noqa: E402

_HEADLESS_KEYS = ("QA_HEADLESS", "HEADLESS")


def _clean_value(value: str) -> str:
    """Normalize a raw .env value: strip an unquoted inline comment, then quotes/space.

    Handles real-world lines like `HEADLESS=true   # true | false` — the trailing
    `# ...` is a comment, not part of the value, so it must not reach the truthiness test.
    A value wrapped in quotes is taken verbatim (its `#` is data, not a comment).
    """
    v = value.strip()
    if v[:1] in ("'", '"'):
        return v.strip('"').strip("'")
    # unquoted: an inline comment starts at the first '#' preceded by whitespace
    for sep in (" #", "\t#"):
        if sep in v:
            v = v.split(sep, 1)[0]
    return v.strip()


def _truthy(value: str) -> bool:
    return _clean_value(str(value)).lower() in ("1", "true", "yes", "on")


def _read_dotenv_value(path: Path, *keys: str) -> str | None:
    """Return the first matching KEY=value from a .env-style file, or None."""
    if not path.is_file():
        return None
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            if k.strip() in keys:
                return _clean_value(v)
    except Exception:  # noqa: BLE001 — never let env parsing break server launch
        pass
    return None


def resolve_headless() -> bool:
    # 1. main project's ./.env wins (explicit project setup)
    raw = _read_dotenv_value(project_root() / ".env", *_HEADLESS_KEYS)
    if raw is not None:
        return _truthy(raw)
    # 2. shell env + .plugin.env (load_env uses setdefault, won't clobber shell)
    load_env()
    for key in _HEADLESS_KEYS:
        if key in os.environ:
            return _truthy(os.environ[key])
    # 3. default: headed
    return False


def main() -> int:
    headless = resolve_headless()
    npx = shutil.which("npx") or shutil.which("npx.cmd") or ("npx.cmd" if os.name == "nt" else "npx")
    cmd = [npx, "-y", "@playwright/mcp@latest"]
    if headless:
        cmd.append("--headless")
    # Pass through any extra args given in .mcp.json after the script path.
    cmd.extend(sys.argv[1:])
    print(f"[mcp-playwright] launching {'headless' if headless else 'headed'}", file=sys.stderr)
    # Inherit stdio so the MCP JSON-RPC stream flows straight through to the child.
    return subprocess.run(cmd).returncode


if __name__ == "__main__":
    sys.exit(main())
