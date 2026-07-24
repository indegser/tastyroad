#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any


def clean(value: Any) -> str:
    return str(value or "").strip()


def removal_rows(paths: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows.extend(
            {**item, "audit_path": str(path)}
            for item in payload.get("items", [])
            if item.get("verdict") == "remove_mapping"
        )
    return rows


def parse_names(value: str) -> list[str]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    return [clean(item) for item in parsed if clean(item)] if isinstance(parsed, list) else []


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Remove transcript-disproved video/restaurant mappings from reviewed audit artifacts."
    )
    parser.add_argument("--sqlite", type=Path, default=Path("data/tastyroad.sqlite"))
    parser.add_argument("--audit", type=Path, action="append", required=True)
    args = parser.parse_args()

    rows = removal_rows(args.audit)
    removed = 0
    with sqlite3.connect(args.sqlite) as connection:
        for row in rows:
            video_id = clean(row.get("video_id"))
            restaurant_id = int(row.get("restaurant_id") or 0)
            video = connection.execute(
                "select id from youtube_videos where video_id = ?",
                (video_id,),
            ).fetchone()
            restaurant = connection.execute(
                "select display_name, naver_map_id from restaurants where id = ?",
                (restaurant_id,),
            ).fetchone()
            if video is None or restaurant is None:
                raise RuntimeError(f"Unknown audited pair: {video_id}/{restaurant_id}")
            youtube_video_id = int(video[0])
            mapped = connection.execute(
                """
                select 1 from youtube_video_restaurants
                where youtube_video_id = ? and restaurant_id = ?
                """,
                (youtube_video_id, restaurant_id),
            ).fetchone()
            if mapped is None:
                continue

            evidence = row.get("mapping_evidence") or row.get("existing_mapping_evidence") or {}
            expected_naver_id = clean(evidence.get("naver_map_id"))
            if expected_naver_id and expected_naver_id != clean(restaurant[1]):
                raise RuntimeError(
                    f"Naver ID changed for audited pair {video_id}/{restaurant_id}: "
                    f"expected={expected_naver_id} actual={restaurant[1]}"
                )

            connection.execute(
                "delete from video_must_taste_items where youtube_video_id = ? and restaurant_id = ?",
                (youtube_video_id, restaurant_id),
            )
            connection.execute(
                "delete from youtube_video_restaurants where youtube_video_id = ? and restaurant_id = ?",
                (youtube_video_id, restaurant_id),
            )

            review = connection.execute(
                "select restaurant_names from agent_video_reviews where external_id = ?",
                (video_id,),
            ).fetchone()
            if review is not None:
                remaining_names = [
                    name for name in parse_names(clean(review[0])) if name != clean(restaurant[0])
                ]
                connection.execute(
                    """
                    update agent_video_reviews
                    set decision = ?,
                        restaurant_names = ?,
                        detected_restaurant_count = ?,
                        reason = ?
                    where external_id = ?
                    """,
                    (
                        "restaurant_intro" if remaining_names else "reviewed_uncertain",
                        json.dumps(remaining_names, ensure_ascii=False),
                        len(remaining_names),
                        f"Removed transcript-disproved mapping via {row['audit_path']}.",
                        video_id,
                    ),
                )

            remaining_mapping = connection.execute(
                "select 1 from youtube_video_restaurants where youtube_video_id = ? limit 1",
                (youtube_video_id,),
            ).fetchone()
            connection.execute(
                "update youtube_videos set status = ? where id = ?",
                ("metadata_verified" if remaining_mapping else "reviewed_uncertain", youtube_video_id),
            )
            removed += 1

    print(f"Removed {removed} audited video/restaurant mappings")
    print(f"Updated {args.sqlite}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
