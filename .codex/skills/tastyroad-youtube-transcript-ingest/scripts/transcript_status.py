#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

from transcript_schema import DEFAULT_SQLITE, ensure_transcript_schema

DEFAULT_CONFIG = Path("data/sources/youtube_sources.json")


def load_source_aliases(config_path: Path) -> dict[str, str]:
    if not config_path.exists():
        return {}
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    aliases: dict[str, str] = {}
    for item in payload.get("sources", []):
        key = str(item.get("key", "")).strip()
        name = str(item.get("name", "")).strip()
        if key and name:
            aliases[key] = name
            aliases[name] = name
    return aliases


def resolve_source_name(source: str | None, config_path: Path) -> str | None:
    if not source:
        return None
    aliases = load_source_aliases(config_path)
    return aliases.get(source, source)


def print_status(sqlite_path: Path, source: str | None, config_path: Path, limit: int) -> None:
    source_name = resolve_source_name(source, config_path)
    with sqlite3.connect(sqlite_path) as connection:
        connection.row_factory = sqlite3.Row
        ensure_transcript_schema(connection)
        params: list[str] = []
        source_clause = ""
        if source_name:
            source_clause = " where source = ?"
            params.append(source_name)

        rows = connection.execute(
            f"""
            select source, transcript_status, count(*) as count
            from youtube_transcript_status
            {source_clause}
            group by source, transcript_status
            order by source, transcript_status
            """,
            params,
        ).fetchall()
        missing_rows = connection.execute(
            f"""
            select published_at, source, video_id, transcript_status, title, last_error_type
            from youtube_transcript_status
            {source_clause}
              {"and" if source_clause else "where"} transcript_status != 'has_transcript'
            order by published_at desc, youtube_video_id desc
            limit ?
            """,
            [*params, limit],
        ).fetchall()

    print("Transcript status")
    for row in rows:
        print(f"- {row['source']}\t{row['transcript_status']}: {row['count']}")

    if missing_rows:
        print("\nMissing or failed transcripts")
        for row in missing_rows:
            error = f"\t{row['last_error_type']}" if row["last_error_type"] else ""
            print(
                f"- {row['published_at']}\t{row['source']}\t{row['video_id']}"
                f"\t{row['transcript_status']}{error}\t{row['title']}"
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Show Tastyroad YouTube transcript DB status.")
    parser.add_argument("--sqlite", type=Path, default=DEFAULT_SQLITE)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--source")
    parser.add_argument("--limit", type=int, default=20)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print_status(args.sqlite, args.source, args.config, args.limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
