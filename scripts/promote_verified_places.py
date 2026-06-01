#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline_schema import ensure_pipeline_schema


DEFAULT_SQLITE = Path("data/tastyroad.sqlite")
DEFAULT_INPUT = Path("data/verified_places/sungsikyung_mukeultende_places.json")
DEFAULT_INPUT_DIR = Path("data/verified_places")


def ensure_schema(connection: sqlite3.Connection) -> None:
    ensure_pipeline_schema(connection)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def get_candidate_id(connection: sqlite3.Connection, video_id: str) -> int:
    row = connection.execute(
        "select id from mention_candidates where external_id = ?",
        (video_id,),
    ).fetchone()
    if row is None:
        raise RuntimeError(f"No mention candidate found for video_id={video_id}")
    return int(row[0])


def upsert_restaurant(connection: sqlite3.Connection, item: dict[str, Any], now: str) -> int:
    connection.execute(
        """
        insert into restaurants (
          canonical_name,
          display_name,
          local_name,
          country_code,
          region,
          address,
          phone,
          category,
          created_at,
          updated_at
        )
        values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        on conflict(country_code, address, canonical_name) do update set
          display_name = excluded.display_name,
          local_name = excluded.local_name,
          region = excluded.region,
          phone = excluded.phone,
          category = excluded.category,
          updated_at = excluded.updated_at
        """,
        (
            item["resolved_name"],
            item["display_name"],
            item.get("local_name"),
            item["country_code"],
            item["region"],
            item["address"],
            item.get("phone"),
            item.get("category"),
            now,
            now,
        ),
    )
    row = connection.execute(
        """
        select id from restaurants
        where country_code = ? and address = ? and canonical_name = ?
        """,
        (item["country_code"], item["address"], item["resolved_name"]),
    ).fetchone()
    if row is None:
        raise RuntimeError(f"Failed to load restaurant id for {item['resolved_name']}")
    return int(row[0])


def upsert_place_link(connection: sqlite3.Connection, restaurant_id: int, item: dict[str, Any], verified_at: str) -> None:
    connection.execute(
        """
        insert into place_links (
          restaurant_id,
          provider,
          url,
          evidence_url,
          confidence,
          status,
          notes,
          verified_at
        )
        values (?, ?, ?, ?, ?, ?, ?, ?)
        on conflict(restaurant_id, provider, url) do update set
          evidence_url = excluded.evidence_url,
          confidence = excluded.confidence,
          status = excluded.status,
          notes = excluded.notes,
          verified_at = excluded.verified_at
        """,
        (
            restaurant_id,
            item["map_provider"],
            item["map_url"],
            item.get("evidence_url"),
            item["confidence"],
            item["status"],
            item.get("notes"),
            verified_at,
        ),
    )


def upsert_mention(
    connection: sqlite3.Connection,
    restaurant_id: int,
    mention_candidate_id: int,
    item: dict[str, Any],
    verified_at: str,
) -> None:
    connection.execute(
        """
        insert into mentions (
          restaurant_id,
          mention_candidate_id,
          confidence,
          status,
          verified_at
        )
        values (?, ?, ?, ?, ?)
        on conflict(restaurant_id, mention_candidate_id) do update set
          confidence = excluded.confidence,
          status = excluded.status,
          verified_at = excluded.verified_at
        """,
        (restaurant_id, mention_candidate_id, item["confidence"], item["status"], verified_at),
    )
    connection.execute(
        "update mention_candidates set status = ? where id = ?",
        (item["status"], mention_candidate_id),
    )


def upsert_place_resolution_candidate(
    connection: sqlite3.Connection,
    mention_candidate_id: int,
    item: dict[str, Any],
    searched_at: str,
) -> None:
    query = str(
        item.get("map_query")
        or f"{item.get('region', '')} {item.get('display_name') or item.get('resolved_name')}"
    ).strip()
    connection.execute(
        """
        insert into place_resolution_candidates (
          mention_candidate_id,
          search_provider,
          query,
          result_name,
          result_address,
          result_phone,
          result_category,
          result_url,
          result_rank,
          confidence,
          status,
          evidence_json,
          searched_at
        )
        values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        on conflict(mention_candidate_id, search_provider, query, result_url) do update set
          result_name = excluded.result_name,
          result_address = excluded.result_address,
          result_phone = excluded.result_phone,
          result_category = excluded.result_category,
          result_rank = excluded.result_rank,
          confidence = excluded.confidence,
          status = excluded.status,
          evidence_json = excluded.evidence_json,
          searched_at = excluded.searched_at
        """,
        (
            mention_candidate_id,
            item["map_provider"],
            query,
            item.get("display_name") or item["resolved_name"],
            item["address"],
            item.get("phone"),
            item.get("category"),
            item["map_url"],
            int(item.get("result_rank", 1)),
            float(item["confidence"]),
            "selected",
            json.dumps(
                {
                    "evidence_url": item.get("evidence_url"),
                    "notes": item.get("notes"),
                    "country_code": item.get("country_code"),
                },
                ensure_ascii=False,
            ),
            searched_at,
        ),
    )


def promote(sqlite_path: Path, input_path: Path) -> int:
    payload = load_json(input_path)
    now = datetime.now(timezone.utc).isoformat()

    with sqlite3.connect(sqlite_path) as connection:
        ensure_schema(connection)
        for item in payload["items"]:
            mention_candidate_id = get_candidate_id(connection, item["video_id"])
            restaurant_id = upsert_restaurant(connection, item, now)
            upsert_place_resolution_candidate(connection, mention_candidate_id, item, payload["verified_at"])
            upsert_place_link(connection, restaurant_id, item, payload["verified_at"])
            upsert_mention(connection, restaurant_id, mention_candidate_id, item, payload["verified_at"])
        ensure_pipeline_schema(connection)

    return len(payload["items"])


def discover_inputs(input_dir: Path) -> list[Path]:
    return sorted(path for path in input_dir.glob("*.json") if path.is_file())


def promote_many(sqlite_path: Path, input_paths: list[Path]) -> int:
    total = 0
    for input_path in input_paths:
        count = promote(sqlite_path, input_path)
        total += count
        print(f"Promoted {count} verified places from {input_path}")
    return total


def main() -> int:
    parser = argparse.ArgumentParser(description="Promote verified place matches into normalized tables.")
    parser.add_argument("--sqlite", type=Path, default=DEFAULT_SQLITE)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument(
        "--input-dir",
        type=Path,
        help="Promote every JSON file in this directory. Overrides --input.",
    )
    args = parser.parse_args()

    if args.input_dir:
        input_paths = discover_inputs(args.input_dir)
        if not input_paths:
            raise RuntimeError(f"No verified place JSON files found in {args.input_dir}")
        count = promote_many(args.sqlite, input_paths)
    else:
        count = promote(args.sqlite, args.input)
        print(f"Promoted {count} verified places")

    print(f"Updated {args.sqlite}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
