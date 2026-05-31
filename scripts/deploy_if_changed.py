#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import shlex
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SITE_OUTPUT = ROOT / "public" / "index.html"
DEFAULT_VERIFIED_DIR = ROOT / "data" / "verified_places"
DEFAULT_DEPLOY_COMMAND = "pnpm dlx vercel@latest --prod --yes --scope jaekwon-hans-projects"


def digest(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command: list[str]) -> None:
    print("+", " ".join(shlex.quote(part) for part in command))
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Collect data, promote verified places, render the static page, and deploy only if output changed."
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_SITE_OUTPUT)
    parser.add_argument("--verified-dir", type=Path, default=DEFAULT_VERIFIED_DIR)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--deploy-command",
        default=DEFAULT_DEPLOY_COMMAND,
        help="Command to run when rendered output changed.",
    )
    args = parser.parse_args()

    before = digest(args.output)
    run(
        [
            sys.executable,
            "scripts/build_site.py",
            "--output",
            str(args.output),
            "--verified-dir",
            str(args.verified_dir),
        ]
    )
    after = digest(args.output)

    if before == after:
        print("No rendered site changes; skipping Vercel deploy.")
        return 0

    print("Rendered site changed.")
    if args.dry_run:
        print("Dry run enabled; skipping Vercel deploy.")
        return 0

    run(shlex.split(args.deploy_command))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
