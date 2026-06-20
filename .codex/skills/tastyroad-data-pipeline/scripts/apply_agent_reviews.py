#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline_schema import ensure_pipeline_schema


DEFAULT_SQLITE = Path("data/tastyroad.sqlite")
DEFAULT_INPUT = Path("data/agent_reviews/video_reviews.json")

ALLOWED_DECISIONS = {"restaurant_intro", "not_restaurant", "uncertain"}


@dataclass(frozen=True)
class ReviewCoverage:
    reviewed_count: int
    unreviewed_count: int
    examples: list[tuple[str, str, str, str]]


def ensure_schema(connection: sqlite3.Connection) -> None:
    ensure_pipeline_schema(connection)


def load_review_items(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        items = payload.get("reviews", [])
    else:
        items = payload

    if not isinstance(items, list):
        raise ValueError(f"{path} must contain a reviews list")
    return [item for item in items if isinstance(item, dict)]


def apply_reviews(sqlite_path: Path, input_path: Path) -> int:
    items = load_review_items(input_path)
    now = datetime.now(timezone.utc).isoformat()

    with sqlite3.connect(sqlite_path) as connection:
        ensure_schema(connection)
        count = 0
        for item in items:
            video_id = str(item.get("video_id") or item.get("external_id") or "").strip()
            if not video_id:
                raise ValueError(f"Review item is missing video_id: {item}")

            decision = str(item.get("decision") or "").strip()
            if decision not in ALLOWED_DECISIONS:
                raise ValueError(
                    f"Review {video_id} has invalid decision {decision!r}; "
                    f"expected one of {sorted(ALLOWED_DECISIONS)}"
                )

            restaurant_names = item.get("restaurant_names", [])
            if not isinstance(restaurant_names, list):
                raise ValueError(f"Review {video_id} restaurant_names must be a list")

            detected_restaurant_count = item.get("detected_restaurant_count")
            if detected_restaurant_count is None:
                detected_restaurant_count = len(restaurant_names)
            detected_restaurant_count = int(detected_restaurant_count)
            if detected_restaurant_count < 0:
                raise ValueError(f"Review {video_id} detected_restaurant_count must be >= 0")
            if decision == "restaurant_intro" and detected_restaurant_count == 0:
                detected_restaurant_count = max(1, len(restaurant_names))

            reviewed_at = str(item.get("reviewed_at") or now)
            connection.execute(
                """
                insert into agent_video_reviews (
                  external_id,
                  decision,
                  confidence,
                  restaurant_names,
                  detected_restaurant_count,
                  reason,
                  reviewer,
                  reviewed_at
                )
                values (?, ?, ?, ?, ?, ?, ?, ?)
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
                    video_id,
                    decision,
                    float(item.get("confidence", 0)),
                    json.dumps([str(name) for name in restaurant_names], ensure_ascii=False),
                    detected_restaurant_count,
                    str(item.get("reason") or ""),
                    str(item.get("reviewer") or "codex"),
                    reviewed_at,
                ),
            )
            count += 1

    return count


def list_unreviewed(sqlite_path: Path, limit: int) -> list[tuple[str, str, str, str]]:
    with sqlite3.connect(sqlite_path) as connection:
        ensure_schema(connection)
        rows = connection.execute(
            """
            select
              c.external_id,
              s.name,
              c.title,
              c.published_at
            from mention_candidates c
            join sources s on s.id = c.source_id
            left join agent_video_reviews r on r.external_id = c.external_id
            where r.external_id is null
            order by c.published_at desc, c.id desc
            limit ?
            """,
            (limit,),
        ).fetchall()

    return [(str(video_id), str(source), str(title), str(published_at)) for video_id, source, title, published_at in rows]


def review_coverage(sqlite_path: Path, limit: int = 10) -> ReviewCoverage:
    with sqlite3.connect(sqlite_path) as connection:
        ensure_schema(connection)
        reviewed_count = int(
            connection.execute(
                """
                select count(*)
                from mention_candidates c
                join agent_video_reviews r on r.external_id = c.external_id
                """
            ).fetchone()[0]
        )
        unreviewed_count = int(
            connection.execute(
                """
                select count(*)
                from mention_candidates c
                left join agent_video_reviews r on r.external_id = c.external_id
                where r.external_id is null
                """
            ).fetchone()[0]
        )

    return ReviewCoverage(
        reviewed_count=reviewed_count,
        unreviewed_count=unreviewed_count,
        examples=list_unreviewed(sqlite_path, limit) if unreviewed_count else [],
    )


def assert_all_candidates_reviewed(sqlite_path: Path, limit: int = 10) -> ReviewCoverage:
    coverage = review_coverage(sqlite_path, limit)
    if coverage.unreviewed_count:
        examples = "\n".join(
            f"- {published_at}\t{source}\t{video_id}\t{title}"
            for video_id, source, title, published_at in coverage.examples
        )
        raise RuntimeError(
            f"{coverage.unreviewed_count} collected videos have not gone through review. "
            "Run `python3 .codex/skills/tastyroad-data-pipeline/scripts/apply_agent_reviews.py --list-unreviewed` and add decisions "
            f"to data/agent_reviews/video_reviews.json before listing.\n{examples}"
        )
    return coverage


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply Codex-authored video review decisions.")
    parser.add_argument("--sqlite", type=Path, default=DEFAULT_SQLITE)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--list-unreviewed", action="store_true")
    parser.add_argument("--check-coverage", action="store_true")
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()

    if args.list_unreviewed:
        for video_id, source, title, published_at in list_unreviewed(args.sqlite, args.limit):
            print(f"{published_at}\t{source}\t{video_id}\t{title}")
        return 0

    if args.check_coverage:
        coverage = assert_all_candidates_reviewed(args.sqlite, args.limit)
        print(f"All collected videos reviewed ({coverage.reviewed_count}).")
        return 0

    count = apply_reviews(args.sqlite, args.input)
    print(f"Applied {count} agent reviews from {args.input}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
