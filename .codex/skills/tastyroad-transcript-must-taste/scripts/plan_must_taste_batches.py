#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any

from must_taste_schema import DEFAULT_SQLITE


DEFAULT_OUTPUT_DIR = Path("/tmp/tastyroad_must_taste_batches")


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be >= 1")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Plan transcript must-taste backfill work into worker-sized JSON files. "
            "This script only reads SQLite and writes planning artifacts."
        )
    )
    parser.add_argument("--sqlite", type=Path, default=DEFAULT_SQLITE)
    parser.add_argument("--source-name", required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--batch-size", type=positive_int, default=3)
    parser.add_argument(
        "--exclude-pairs-file",
        type=Path,
        action="append",
        default=[],
        help="Prior pairs.json whose video_id/restaurant_id pairs should not be planned again. Repeatable.",
    )
    parser.add_argument(
        "--include-existing",
        action="store_true",
        help="Plan every scoped pair instead of only pairs without must-taste rows.",
    )
    parser.add_argument(
        "--group-by-video",
        action="store_true",
        help=(
            "Write video-grouped batch inputs so workers can scout each transcript once "
            "and then split restaurant-specific result artifacts."
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow writing into an existing non-empty output directory.",
    )
    return parser.parse_args()


def fetch_pairs(
    connection: sqlite3.Connection,
    source_name: str,
    include_existing: bool,
) -> list[dict[str, Any]]:
    where_missing = ""
    if not include_existing:
        where_missing = """
          and not exists (
            select 1
            from video_must_taste_items v
            where v.youtube_video_id = yv.id
              and v.restaurant_id = r.id
          )
        """
    rows = connection.execute(
        f"""
        select
          yv.id as youtube_pk,
          yv.video_id,
          yv.title,
          yv.published_at,
          r.id as restaurant_id,
          r.display_name,
          pt.id as transcript_track_id,
          pt.language_code,
          pt.language,
          pt.segment_count
        from youtube_video_restaurants yvr
        join youtube_videos yv on yv.id = yvr.youtube_video_id
        join sources s on s.id = yv.source_id
        join restaurants r on r.id = yvr.restaurant_id
        join preferred_youtube_transcripts pt on pt.youtube_video_id = yv.id
        where s.name = ?
          and coalesce(r.naver_map_id, '') != ''
          {where_missing}
        order by yv.published_at desc, yv.id desc, r.id
        """,
        (source_name,),
    ).fetchall()
    return [
        {
            "youtube_pk": row["youtube_pk"],
            "video_id": row["video_id"],
            "title": row["title"],
            "published_at": row["published_at"],
            "restaurant_id": row["restaurant_id"],
            "display_name": row["display_name"],
            "transcript_track_id": row["transcript_track_id"],
            "language_code": row["language_code"],
            "language": row["language"],
            "segment_count": row["segment_count"],
        }
        for row in rows
    ]


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def group_pairs_by_video(pairs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[int, dict[str, Any]] = {}
    for pair in pairs:
        youtube_pk = int(pair["youtube_pk"])
        entry = grouped.setdefault(
            youtube_pk,
            {
                "youtube_pk": youtube_pk,
                "video_id": pair["video_id"],
                "title": pair["title"],
                "published_at": pair["published_at"],
                "transcript_track_id": pair["transcript_track_id"],
                "language_code": pair["language_code"],
                "language": pair["language"],
                "segment_count": pair["segment_count"],
                "restaurants": [],
            },
        )
        entry["restaurants"].append(
            {
                "restaurant_id": pair["restaurant_id"],
                "display_name": pair["display_name"],
            }
        )
    return list(grouped.values())


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir
    if output_dir.exists() and any(output_dir.iterdir()) and not args.force:
        raise SystemExit(f"{output_dir} is not empty; pass --force to write planning files.")
    output_dir.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(args.sqlite)
    connection.row_factory = sqlite3.Row
    pairs = fetch_pairs(connection, args.source_name, args.include_existing)
    excluded_pair_count = 0
    if args.exclude_pairs_file:
        excluded_rows = [
            row
            for path in args.exclude_pairs_file
            for row in json.loads(path.read_text(encoding="utf-8"))
        ]
        excluded_keys = {
            (str(row["video_id"]), int(row["restaurant_id"]))
            for row in excluded_rows
        }
        before_count = len(pairs)
        pairs = [
            pair
            for pair in pairs
            if (str(pair["video_id"]), int(pair["restaurant_id"])) not in excluded_keys
        ]
        excluded_pair_count = before_count - len(pairs)

    mode = "all_scoped" if args.include_existing else "missing_only"
    write_json(output_dir / "pairs.json", pairs)
    plan_units: list[dict[str, Any]]
    unit_name: str
    if args.group_by_video:
        plan_units = group_pairs_by_video(pairs)
        unit_name = "videos"
        write_json(output_dir / "videos.json", plan_units)
    else:
        plan_units = pairs
        unit_name = "pairs"
    batches = []
    for index in range(0, len(plan_units), args.batch_size):
        batch_number = len(batches) + 1
        batch_items = plan_units[index : index + args.batch_size]
        batch_path = output_dir / f"batch_{batch_number:03}.json"
        write_json(batch_path, batch_items)
        batches.append(
            {
                "batch_number": batch_number,
                "path": str(batch_path),
                "unit": unit_name,
                "unit_count": len(batch_items),
                "pair_count": sum(
                    len(item.get("restaurants", [item]))
                    for item in batch_items
                ),
                "done_path": str(output_dir / f"batch_{batch_number:03}_done.json"),
            }
        )

    manifest = {
        "source_name": args.source_name,
        "mode": mode,
        "grouping": "video" if args.group_by_video else "pair",
        "sqlite": str(args.sqlite),
        "output_dir": str(output_dir),
        "batch_size": args.batch_size,
        "pair_count": len(pairs),
        "unit_count": len(plan_units),
        "batch_count": len(batches),
        "excluded_pair_count": excluded_pair_count,
        "exclude_pairs_files": [str(path) for path in args.exclude_pairs_file],
        "pairs_path": str(output_dir / "pairs.json"),
        "videos_path": str(output_dir / "videos.json") if args.group_by_video else None,
        "batches": batches,
    }
    write_json(output_dir / "manifest.json", manifest)

    print(f"source_name={args.source_name}")
    print(f"mode={mode}")
    print(f"grouping={manifest['grouping']}")
    print(f"pair_count={len(pairs)}")
    print(f"unit_count={len(plan_units)}")
    print(f"batch_count={len(batches)}")
    print(f"excluded_pair_count={excluded_pair_count}")
    print(f"output_dir={output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
