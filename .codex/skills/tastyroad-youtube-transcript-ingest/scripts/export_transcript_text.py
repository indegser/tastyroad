#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

from transcript_schema import DEFAULT_SQLITE, ensure_transcript_schema


def export_text(sqlite_path: Path, video_id: str, output: Path | None) -> None:
    with sqlite3.connect(sqlite_path) as connection:
        connection.row_factory = sqlite3.Row
        ensure_transcript_schema(connection)
        row = connection.execute(
            """
            select video_id, source_name, language_code, transcript_text
            from preferred_youtube_transcripts
            where video_id = ?
            """,
            (video_id,),
        ).fetchone()

    if row is None:
        raise SystemExit(f"No preferred transcript found for {video_id}")

    text = str(row["transcript_text"])
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + "\n", encoding="utf-8")
        print(f"Wrote {output}")
    else:
        sys.stdout.write(text + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export the preferred transcript text for one video.")
    parser.add_argument("--sqlite", type=Path, default=DEFAULT_SQLITE)
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    export_text(args.sqlite, args.video_id, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
