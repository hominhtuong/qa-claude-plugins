"""Shared .env loader for the `auto` plugin scripts (cross-platform, stdlib-only).

Secrets live in the project's .claude/qa-claude/.env (git-ignored), never in the plugin.
This module finds that .env (walking up from cwd) and loads it into os.environ.

Key names follow a stable convention (see templates/.env.example):
    ENABLE_LARK_NOTIFY, LARK_WEBHOOK_URL, LARK_WEBHOOK_SECRET, LARK_PLATFORM, LARK_USER
    ENABLE_CF_PUSH, CF_ACCOUNT_ID, CF_API_TOKEN, CF_R2_BUCKET, CF_R2_DOMAIN, CF_R2_PREFIX
"""
from __future__ import annotations  # allow `Path | None` on Python 3.8/3.9

import os
from pathlib import Path


def project_root() -> Path:
    """Best-effort project root: $CLAUDE_PROJECT_DIR, else current working dir."""
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())


def find_env_file() -> Path | None:
    """Locate the plugin's .env (kept separate from the project's own ./.env).

    Order: $QA_ENV_FILE → walking up from cwd (and $CLAUDE_PROJECT_DIR), preferring
    `.claude/qa-claude/.env` over a bare `./.env` (the latter kept as a fallback).
    """
    override = os.environ.get("QA_ENV_FILE")
    if override:
        p = Path(override)
        return p if p.is_file() else None
    here = Path(os.getcwd()).resolve()
    roots = [here, *here.parents]
    proj = os.environ.get("CLAUDE_PROJECT_DIR")
    if proj:
        roots = [Path(proj).resolve(), *roots]
    for d in roots:
        for candidate in (d / ".claude" / "qa-claude" / ".env", d / ".env"):
            if candidate.is_file():
                return candidate
    return None


def load_env(verbose: bool = False) -> dict:
    """Parse the project's .env into os.environ (without overriding real env vars).

    Returns the parsed key->value dict (may be empty if no .env). Supports `KEY=value`
    and `KEY = value`, ignores blank lines and `#` comments, strips surrounding quotes.
    """
    parsed: dict = {}
    path = find_env_file()
    if path is None:
        if verbose:
            print("[env] no .env found — run the `setup` skill to create one")
        return parsed
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not key:
            continue
        parsed[key] = value
        os.environ.setdefault(key, value)
    if verbose:
        print(f"[env] loaded {len(parsed)} keys from {path}")
    return parsed


def env_bool(key: str, default: bool = False) -> bool:
    return str(os.environ.get(key, str(default))).strip().lower() == "true"


def env_str(key: str, default: str = "") -> str:
    v = os.environ.get(key)
    return v.strip() if v is not None else default
