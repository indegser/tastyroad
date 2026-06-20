#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

from collect_youtube import DEFAULT_SQLITE


def print_status(sqlite_path: Path, limit: int) -> None:
    with sqlite3.connect(f"file:{sqlite_path}?mode=ro", uri=True) as connection:
        review_rows = connection.execute(
            """
            select review_status, count(*)
            from video_pipeline_status
            group by review_status
            order by review_status
            """
        ).fetchall()
        mapping_rows = connection.execute(
            """
            select mapping_status, count(*)
            from video_pipeline_status
            group by mapping_status
            order by mapping_status
            """
        ).fetchall()
        backlog_rows = connection.execute(
            """
            select published_at, source, video_id, title, detected_restaurant_count, mapped_restaurant_count
            from mapping_backlog
            order by published_at desc, youtube_video_id desc
            limit ?
            """,
            (limit,),
        ).fetchall()

    print("Review status")
    for status, count in review_rows:
        print(f"- {status}: {count}")

    print("\nMapping status")
    for status, count in mapping_rows:
        print(f"- {status}: {count}")

    if backlog_rows:
        print("\nMapping backlog")
        for published_at, source, video_id, title, expected, mapped in backlog_rows:
            print(f"- {published_at}\t{source}\t{video_id}\t{mapped}/{expected}\t{title}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Show DB-backed collection/review/mapping pipeline status.")
    parser.add_argument("--sqlite", type=Path, default=DEFAULT_SQLITE)
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    print_status(args.sqlite, args.limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
