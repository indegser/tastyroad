#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

from pipeline_schema import ensure_pipeline_schema


DEFAULT_SQLITE = Path("data/tastyroad.sqlite")
ALLOWED_DECISIONS = {"not_restaurant", "uncertain"}


def load_payload(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        raise ValueError("Input must be an object with an items array")
    if not str(payload.get("source") or "").strip():
        raise ValueError("Input must include source")
    if not str(payload.get("reviewed_at") or "").strip():
        raise ValueError("Input must include reviewed_at")
    return payload


def validate_item(connection: sqlite3.Connection, source: str, item: dict[str, Any]) -> None:
    video_id = str(item.get("video_id") or "").strip()
    decision = str(item.get("decision") or "").strip()
    reason = str(item.get("reason") or "").strip()
    confidence = float(item.get("confidence") or 0)
    if not video_id or decision not in ALLOWED_DECISIONS or not reason:
        raise ValueError(f"Invalid review item: {item}")
    if not 0 <= confidence <= 1:
        raise ValueError(f"confidence must be between 0 and 1 for {video_id}")

    row = connection.execute(
        """
        select v.id
        from youtube_videos v
        join sources s on s.id = v.source_id
        where v.video_id = ? and s.name = ?
        """,
        (video_id, source),
    ).fetchone()
    if row is None:
        raise ValueError(f"Video {video_id} does not belong to source {source}")

    mapping_count = int(
        connection.execute(
            """
            select count(*)
            from youtube_video_restaurants
            where youtube_video_id = ?
              and status in ('verified', 'metadata_verified')
            """,
            (int(row[0]),),
        ).fetchone()[0]
    )
    if mapping_count:
        raise ValueError(f"Refusing to apply {decision} to mapped video {video_id}")


def apply(sqlite_path: Path, input_path: Path, *, dry_run: bool) -> int:
    payload = load_payload(input_path)
    source = str(payload["source"]).strip()
    reviewed_at = str(payload["reviewed_at"]).strip()
    items = payload["items"]

    with sqlite3.connect(sqlite_path) as connection:
        for item in items:
            validate_item(connection, source, item)
        if dry_run:
            return len(items)

        for item in items:
            connection.execute(
                """
                insert into agent_video_reviews (
                  external_id, decision, confidence, restaurant_names,
                  detected_restaurant_count, reason, reviewer, reviewed_at
                )
                values (?, ?, ?, '[]', 0, ?, 'agent_review_decisions', ?)
                on conflict(external_id) do update set
                  decision = excluded.decision,
                  confidence = excluded.confidence,
                  restaurant_names = excluded.restaurant_names,
                  detected_restaurant_count = excluded.detected_restaurant_count,
                  reason = excluded.reason,
                  reviewer = excluded.reviewer,
                  reviewed_at = excluded.reviewed_at
                """,
                (
                    str(item["video_id"]).strip(),
                    str(item["decision"]).strip(),
                    float(item["confidence"]),
                    str(item["reason"]).strip(),
                    reviewed_at,
                ),
            )
        ensure_pipeline_schema(connection)
    return len(items)


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply reviewed non-mapping video decisions safely.")
    parser.add_argument("--sqlite", type=Path, default=DEFAULT_SQLITE)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    count = apply(args.sqlite, args.input, dry_run=args.dry_run)
    action = "Validated" if args.dry_run else "Applied"
    print(f"{action} {count} video review decisions")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"error: {error}", file=sys.stderr)
        raise
