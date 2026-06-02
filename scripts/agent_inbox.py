#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


DEFAULT_WORK_DIR = Path("data/work")


@dataclass(frozen=True)
class InboxItem:
    status: str
    stage: str
    video_id: str
    title: str
    artifact_path: str
    claimed_by: str = ""


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def discover_inbox(work_dir: Path, stage: str | None = None) -> list[InboxItem]:
    videos_dir = work_dir / "videos"
    if not videos_dir.exists():
        return []

    items: list[InboxItem] = []
    for artifact_path in sorted(videos_dir.glob("*/*.json")):
        payload = load_json(artifact_path)
        if payload.get("status") not in {"needs_agent", "claimed"}:
            continue
        current_stage = str(payload.get("stage") or "")
        if stage and current_stage != stage:
            continue
        items.append(
            InboxItem(
                status=str(payload.get("status") or ""),
                stage=current_stage,
                video_id=str(payload.get("video_id") or ""),
                title=str(payload.get("title") or ""),
                artifact_path=str(artifact_path),
                claimed_by=str(payload.get("claimed_by") or ""),
            )
        )
    return items


def render_text(items: list[InboxItem]) -> str:
    if not items:
        return "No needs_agent or claimed artifacts found."
    return "\n".join(
        f"{item.status}\t{item.stage}\t{item.video_id}\t{item.artifact_path}\t{item.claimed_by}\t{item.title}"
        for item in items
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="List stage artifacts that need agent work.")
    parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK_DIR)
    parser.add_argument("--stage")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()

    items = discover_inbox(args.work_dir, stage=args.stage)
    if args.format == "json":
        print(json.dumps([asdict(item) for item in items], ensure_ascii=False, indent=2))
    else:
        print(render_text(items))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
