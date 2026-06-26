#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
from pathlib import Path
from typing import Any

from must_taste_schema import DEFAULT_SQLITE


DEFAULT_DONE_GLOB = "*_done.json"
APPLY_SCRIPT = Path(__file__).resolve().with_name("apply_must_taste_result.py")


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be >= 1")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Collect must-taste worker completion files, let retry files override earlier "
            "insufficient results, dry-run validate every selected artifact, and optionally "
            "apply the validated results sequentially to SQLite."
        )
    )
    parser.add_argument("--sqlite", type=Path, default=DEFAULT_SQLITE)
    parser.add_argument("--done-dir", type=Path, required=True)
    parser.add_argument("--done-glob", default=DEFAULT_DONE_GLOB)
    parser.add_argument("--expected-count", type=positive_int)
    parser.add_argument("--source-name")
    parser.add_argument("--reviewer", default="codex-worker")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually write rows to SQLite after dry-run validation. Omit for validation only.",
    )
    parser.add_argument(
        "--require-zero-missing",
        action="store_true",
        help="After --apply, fail unless source scoped map+transcript pairs without taste is zero.",
    )
    return parser.parse_args()


def load_done_rows(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    if isinstance(data, dict):
        if isinstance(data.get("results"), list):
            return [row for row in data["results"] if isinstance(row, dict)]
        return [data]
    return []


def dry_run_passed(row: dict[str, Any]) -> bool:
    dry_run = row.get("dry_run")
    return (
        row.get("dry_run_passed") is True
        or (isinstance(dry_run, dict) and (dry_run.get("passed") is True or dry_run.get("status") == "passed"))
        or str(dry_run).lower() in {"passed", "true"}
    )


def row_item_count(row: dict[str, Any]) -> int:
    if row.get("item_count") is not None:
        return int(row["item_count"])
    items = row.get("items")
    if isinstance(items, list):
        return len(items)
    return 0


def success_like(row: dict[str, Any]) -> bool:
    return (row.get("status") or "").lower() == "success" or (
        dry_run_passed(row) and row_item_count(row) > 0
    )


def row_key(row: dict[str, Any]) -> tuple[str, int]:
    video_id = str(row.get("video_id") or "")
    restaurant_id = int(row.get("restaurant_id") or 0)
    if not video_id or restaurant_id <= 0:
        raise ValueError(f"Completion row is missing video_id/restaurant_id: {row}")
    return video_id, restaurant_id


def completion_sort_key(path: Path) -> tuple[int, str]:
    name = path.name
    is_retry = 1 if name.startswith("retry_") else 0
    return is_retry, name


def collect_selected_rows(done_dir: Path, done_glob: str) -> tuple[dict[tuple[str, int], dict[str, Any]], dict[tuple[str, int], str]]:
    selected: dict[tuple[str, int], dict[str, Any]] = {}
    selected_source: dict[tuple[str, int], str] = {}
    for path in sorted(done_dir.glob(done_glob), key=completion_sort_key):
        for row in load_done_rows(path):
            key = row_key(row)
            selected[key] = row
            selected_source[key] = path.name
    return selected, selected_source


def artifact_paths(video_id: str, restaurant_id: int) -> tuple[Path, Path]:
    base = Path("data/work/must_taste") / video_id / str(restaurant_id)
    return base / "context.json", base / "result.json"


def validate_selected_rows(
    selected: dict[tuple[str, int], dict[str, Any]],
    selected_source: dict[tuple[str, int], str],
    expected_count: int | None,
) -> list[tuple[str, int, Path, Path, str]]:
    if expected_count is not None and len(selected) != expected_count:
        raise SystemExit(f"expected {expected_count} selected pairs, got {len(selected)}")

    not_success = [
        (key, selected_source[key], row)
        for key, row in sorted(selected.items())
        if not success_like(row)
    ]
    if not_success:
        preview = "\n".join(
            f"{source}: {key[0]}/{key[1]} status={row.get('status')!r} items={row_item_count(row)}"
            for key, source, row in not_success[:20]
        )
        raise SystemExit(f"selected rows still include non-success entries:\n{preview}")

    artifact_rows = []
    for (video_id, restaurant_id), row in sorted(selected.items()):
        context_path, result_path = artifact_paths(video_id, restaurant_id)
        if not context_path.exists() or not result_path.exists():
            raise SystemExit(
                f"missing artifacts for {video_id}/{restaurant_id}: "
                f"context={context_path.exists()} result={result_path.exists()}"
            )
        result = json.loads(result_path.read_text(encoding="utf-8"))
        if not isinstance(result.get("items"), list) or not result["items"]:
            raise SystemExit(f"selected success row has no final items: {video_id}/{restaurant_id}")
        artifact_rows.append(
            (video_id, restaurant_id, context_path, result_path, selected_source[(video_id, restaurant_id)])
        )
    return artifact_rows


def run_apply(
    sqlite_path: Path,
    context_path: Path,
    result_path: Path,
    reviewer: str,
    apply: bool,
) -> None:
    command = [
        "python3",
        str(APPLY_SCRIPT),
        "--sqlite",
        str(sqlite_path),
        "--context",
        str(context_path),
        "--result",
        str(result_path),
    ]
    if apply:
        command.extend(["--reviewer", reviewer])
    else:
        command.append("--dry-run")
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, text=True)


def source_coverage(connection: sqlite3.Connection, source_name: str) -> dict[str, int]:
    scoped_query = """
    select count(*)
    from youtube_video_restaurants yvr
    join youtube_videos yv on yv.id = yvr.youtube_video_id
    join sources s on s.id = yv.source_id
    join restaurants r on r.id = yvr.restaurant_id
    join preferred_youtube_transcripts pt on pt.youtube_video_id = yv.id
    where s.name = ?
      and coalesce(r.naver_map_id, '') != ''
    """
    pairs_with_items_query = """
    select count(distinct v.youtube_video_id || ':' || v.restaurant_id)
    from video_must_taste_items v
    join youtube_videos yv on yv.id = v.youtube_video_id
    join sources s on s.id = yv.source_id
    where s.name = ?
    """
    items_query = """
    select count(*)
    from video_must_taste_items v
    join youtube_videos yv on yv.id = v.youtube_video_id
    join sources s on s.id = yv.source_id
    where s.name = ?
    """
    remaining_query = """
    with scoped as (
      select yv.video_id, yvr.youtube_video_id, yvr.restaurant_id
      from youtube_video_restaurants yvr
      join youtube_videos yv on yv.id = yvr.youtube_video_id
      join sources s on s.id = yv.source_id
      join restaurants r on r.id = yvr.restaurant_id
      join preferred_youtube_transcripts pt on pt.youtube_video_id = yv.id
      where s.name = ?
        and coalesce(r.naver_map_id, '') != ''
    )
    select count(*)
    from scoped sc
    where not exists (
      select 1
      from video_must_taste_items v
      where v.youtube_video_id = sc.youtube_video_id
        and v.restaurant_id = sc.restaurant_id
    )
    """
    return {
        "scoped_pairs": connection.execute(scoped_query, (source_name,)).fetchone()[0],
        "pairs_with_items": connection.execute(pairs_with_items_query, (source_name,)).fetchone()[0],
        "items": connection.execute(items_query, (source_name,)).fetchone()[0],
        "remaining": connection.execute(remaining_query, (source_name,)).fetchone()[0],
    }


def main() -> int:
    args = parse_args()
    selected, selected_source = collect_selected_rows(args.done_dir, args.done_glob)
    artifact_rows = validate_selected_rows(selected, selected_source, args.expected_count)

    print(f"selected_pairs={len(artifact_rows)}")
    print("dry_run_start")
    for _, _, context_path, result_path, _ in artifact_rows:
        run_apply(args.sqlite, context_path, result_path, args.reviewer, apply=False)
    print(f"dry_run_ok={len(artifact_rows)}")

    if args.apply:
        print("apply_start")
        for _, _, context_path, result_path, _ in artifact_rows:
            run_apply(args.sqlite, context_path, result_path, args.reviewer, apply=True)
        print(f"applied_pairs={len(artifact_rows)}")
    else:
        print("apply_skipped=true")

    connection = sqlite3.connect(args.sqlite)
    print(f"integrity={connection.execute('pragma integrity_check').fetchone()[0]}")
    if args.source_name:
        coverage = source_coverage(connection, args.source_name)
        for key, value in coverage.items():
            print(f"{key}={value}")
        if args.require_zero_missing and coverage["remaining"] != 0:
            raise SystemExit(f"remaining must be 0, got {coverage['remaining']}")
    elif args.require_zero_missing:
        raise SystemExit("--require-zero-missing requires --source-name")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
