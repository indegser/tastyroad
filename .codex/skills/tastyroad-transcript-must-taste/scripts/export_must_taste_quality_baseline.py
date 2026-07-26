#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from must_taste_schema import DEFAULT_SQLITE


DEFAULT_OUTPUT = Path("data/work/must_taste_quality/baseline.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Freeze previously stored must-taste rows as a deterministic quality baseline. "
            "SQLite is opened read-only and is never modified."
        )
    )
    parser.add_argument("--sqlite", type=Path, default=DEFAULT_SQLITE)
    parser.add_argument("--source-name", default="성시경의 먹을텐데")
    parser.add_argument("--video-id", action="append", default=[])
    parser.add_argument(
        "--sample-size",
        type=int,
        default=30,
        help="Number of restaurant-video pairs. Use 0 for every eligible pair.",
    )
    parser.add_argument("--seed", default="must-taste-quality-v1")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def normalize_text(value: object) -> str:
    return " ".join(str(value or "").split())


def parse_evidence_json(value: object) -> dict[str, Any]:
    if not value:
        return {}
    try:
        parsed = json.loads(str(value))
    except json.JSONDecodeError:
        return {"parse_error": True, "raw": str(value)}
    return parsed if isinstance(parsed, dict) else {"raw": parsed}


def stable_pair_order(seed: str, pair: dict[str, Any]) -> str:
    key = f"{seed}:{pair['video_id']}:{pair['restaurant_id']}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def database_uri(path: Path) -> str:
    return f"file:{path.resolve()}?mode=ro"


def load_pairs(
    sqlite_path: Path,
    source_name: str,
    video_ids: list[str],
) -> list[dict[str, Any]]:
    query = """
        select
          i.restaurant_id,
          i.youtube_video_id,
          i.video_id,
          i.rank,
          i.item_name,
          i.reason,
          i.repaired_reason,
          i.segment_index,
          i.start_seconds,
          i.end_seconds,
          i.timestamp_label,
          i.evidence_text,
          i.transcript_track_id,
          i.generated_at,
          i.evidence_json,
          y.title,
          y.published_at,
          s.name as source_name,
          r.display_name as restaurant_name,
          pt.segment_count,
          (
            select count(*)
            from youtube_video_restaurants scoped
            where scoped.youtube_video_id = i.youtube_video_id
              and scoped.status in ('verified', 'metadata_verified')
          ) as restaurant_count
        from video_must_taste_items i
        join youtube_videos y on y.id = i.youtube_video_id
        join sources s on s.id = y.source_id
        join restaurants r on r.id = i.restaurant_id
        join preferred_youtube_transcripts pt on pt.youtube_video_id = y.id
        where s.name = ?
    """
    params: list[Any] = [source_name]
    if video_ids:
        placeholders = ",".join("?" for _ in video_ids)
        query += f" and i.video_id in ({placeholders})"
        params.extend(video_ids)
    query += " order by i.video_id, i.restaurant_id, i.rank"

    with sqlite3.connect(database_uri(sqlite_path), uri=True) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(query, params).fetchall()

    grouped: dict[tuple[str, int], list[sqlite3.Row]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["video_id"]), int(row["restaurant_id"]))].append(row)

    pairs = []
    for (_, _), pair_rows in grouped.items():
        first = pair_rows[0]
        pairs.append(
            {
                "video_id": str(first["video_id"]),
                "youtube_video_id": int(first["youtube_video_id"]),
                "video_title": str(first["title"]),
                "published_at": str(first["published_at"]),
                "source_name": str(first["source_name"]),
                "restaurant_id": int(first["restaurant_id"]),
                "restaurant_name": str(first["restaurant_name"]),
                "restaurant_count_in_video": int(first["restaurant_count"]),
                "transcript_track_id": int(first["transcript_track_id"]),
                "transcript_segment_count": int(first["segment_count"]),
                "items": [
                    {
                        "rank": int(row["rank"]),
                        "menu_item": str(row["item_name"]),
                        "reason": str(row["reason"]),
                        "repaired_reason": str(row["repaired_reason"]),
                        "segment_index": int(row["segment_index"]),
                        "start_seconds": float(row["start_seconds"]),
                        "end_seconds": float(row["end_seconds"]),
                        "timestamp": str(row["timestamp_label"]),
                        "evidence_text": str(row["evidence_text"]),
                        "generated_at": str(row["generated_at"]),
                        "evidence": parse_evidence_json(row["evidence_json"]),
                    }
                    for row in pair_rows
                ],
            }
        )
    return pairs


def baseline_hash(pairs: list[dict[str, Any]]) -> str:
    encoded = json.dumps(
        pairs,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def export(args: argparse.Namespace) -> dict[str, Any]:
    if args.sample_size < 0:
        raise ValueError("--sample-size must be 0 or greater.")
    pairs = load_pairs(args.sqlite, args.source_name, args.video_id)
    pairs.sort(key=lambda pair: stable_pair_order(args.seed, pair))
    if args.sample_size:
        pairs = pairs[: args.sample_size]
    if not pairs:
        raise ValueError("No stored must-taste pairs matched the requested baseline scope.")

    multi_restaurant_pairs = sum(
        1 for pair in pairs if int(pair["restaurant_count_in_video"]) > 1
    )
    return {
        "schema_version": 1,
        "kind": "must_taste_quality_baseline",
        "baseline_id": baseline_hash(pairs),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "sqlite_path": str(args.sqlite),
            "source_name": args.source_name,
            "video_ids": args.video_id,
            "sample_size": args.sample_size,
            "seed": args.seed,
        },
        "summary": {
            "pair_count": len(pairs),
            "video_count": len({pair["video_id"] for pair in pairs}),
            "item_count": sum(len(pair["items"]) for pair in pairs),
            "multi_restaurant_pair_count": multi_restaurant_pairs,
        },
        "pairs": pairs,
    }


def main() -> int:
    args = parse_args()
    baseline = export(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(baseline, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    summary = baseline["summary"]
    print(f"baseline_id={baseline['baseline_id']}")
    print(f"videos={summary['video_count']}")
    print(f"pairs={summary['pair_count']}")
    print(f"items={summary['item_count']}")
    print(f"output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
