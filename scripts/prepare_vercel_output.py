#!/usr/bin/env python3

from __future__ import annotations

import shutil
from pathlib import Path


SQLITE_PATH = Path("data/tastyroad.sqlite")
VERCEL_FUNCTIONS_DIR = Path(".vercel/output/functions")


def main() -> int:
    if not SQLITE_PATH.exists():
        raise FileNotFoundError(f"SQLite database not found: {SQLITE_PATH}")
    if not VERCEL_FUNCTIONS_DIR.exists():
        raise FileNotFoundError(f"Vercel functions directory not found: {VERCEL_FUNCTIONS_DIR}")

    copied = 0
    for function_dir in VERCEL_FUNCTIONS_DIR.rglob("*.func"):
        target = function_dir / "data" / SQLITE_PATH.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SQLITE_PATH, target)
        copied += 1

    if copied == 0:
        raise RuntimeError("No Vercel serverless function directories were found.")

    print(f"Copied {SQLITE_PATH} into {copied} Vercel function bundle(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
