#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline_schema import ensure_pipeline_schema


DEFAULT_SQLITE = Path("data/tastyroad.sqlite")
DEFAULT_INPUT = Path("data/verified_places/sungsikyung_mukeultende_places.json")
DEFAULT_INPUT_DIR = Path("data/verified_places")
NAVER_PLACE_ID_RE = re.compile(r"(?:/entry/place/|/place/)(\d+)")


def ensure_schema(connection: sqlite3.Connection) -> None:
    ensure_pipeline_schema(connection)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def get_youtube_video_id(connection: sqlite3.Connection, video_id: str) -> int:
    row = connection.execute(
        "select id from youtube_videos where video_id = ?",
        (video_id,),
    ).fetchone()
    if row is None:
        raise RuntimeError(f"No YouTube video found for video_id={video_id}")
    return int(row[0])


def extract_naver_map_id(url: str) -> str:
    match = NAVER_PLACE_ID_RE.search(url)
    return match.group(1) if match else ""


def resolve_naver_map_url(url: str) -> str:
    if not url.startswith("https://naver.me/"):
        return url
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=15) as response:
        return response.geturl()


def resolve_naver_map_details(item: dict[str, Any]) -> tuple[str, str]:
    if item.get("map_provider") != "naver_map":
        return "", str(item.get("map_url") or "")

    map_url = str(item.get("map_url") or "")
    explicit_id = str(item.get("naver_map_id") or "").strip()
    if explicit_id:
        return explicit_id, map_url or f"https://map.naver.com/p/entry/place/{explicit_id}?placePath=%2Fhome"

    naver_map_id = extract_naver_map_id(map_url)
    if naver_map_id:
        return naver_map_id, map_url

    try:
        resolved_url = resolve_naver_map_url(map_url)
    except Exception as error:  # noqa: BLE001 - naver.me redirects can fail transiently.
        print(f"warning: failed to resolve Naver map URL {map_url}: {error}", file=sys.stderr)
        return "", map_url

    return extract_naver_map_id(resolved_url), resolved_url


def upsert_restaurant(
    connection: sqlite3.Connection,
    item: dict[str, Any],
    now: str,
    naver_map_id: str,
) -> int:
    existing = connection.execute(
        "select id from restaurants where naver_map_id = ?",
        (naver_map_id,),
    ).fetchone()
    if existing is None:
        existing = connection.execute(
            """
            select id from restaurants
            where country_code = ? and address = ? and canonical_name = ?
            """,
            (item["country_code"], item["address"], item["resolved_name"]),
        ).fetchone()

    if existing is not None:
        restaurant_id = int(existing[0])
        connection.execute(
            """
            update restaurants
            set
              naver_map_id = ?,
              display_name = ?,
              local_name = ?,
              region = ?,
              phone = ?,
              category = ?,
              updated_at = ?
            where id = ?
            """,
            (
                naver_map_id,
                item["display_name"],
                item.get("local_name"),
                item["region"],
                item.get("phone"),
                item.get("category"),
                now,
                restaurant_id,
            ),
        )
        return restaurant_id

    connection.execute(
        """
        insert into restaurants (
          naver_map_id,
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
        values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            naver_map_id,
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
        select id from restaurants where naver_map_id = ?
        """,
        (naver_map_id,),
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


def upsert_video_restaurant(
    connection: sqlite3.Connection,
    restaurant_id: int,
    youtube_video_id: int,
    item: dict[str, Any],
    verified_at: str,
) -> None:
    connection.execute(
        """
        insert into youtube_video_restaurants (
          restaurant_id,
          youtube_video_id,
          confidence,
          status,
          verified_at
        )
        values (?, ?, ?, ?, ?)
        on conflict(restaurant_id, youtube_video_id) do update set
          confidence = excluded.confidence,
          status = excluded.status,
          verified_at = excluded.verified_at
        """,
        (restaurant_id, youtube_video_id, item["confidence"], item["status"], verified_at),
    )
    connection.execute(
        "update youtube_videos set status = ? where id = ?",
        (item["status"], youtube_video_id),
    )


def upsert_place_resolution_candidate(
    connection: sqlite3.Connection,
    youtube_video_id: int,
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
          youtube_video_id,
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
        on conflict(youtube_video_id, search_provider, query, result_url) do update set
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
            youtube_video_id,
            item["map_provider"],
            query,
            item.get("display_name") or item["resolved_name"],
            item["address"],
            item.get("phone"),
            item.get("category"),
            item["map_url"],
            int(item.get("result_rank", 1)),
            float(item["confidence"]),
            str(item.get("resolution_status") or "selected"),
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
        count = 0
        for item in payload["items"]:
            youtube_video_id = get_youtube_video_id(connection, item["video_id"])
            naver_map_id, resolved_map_url = resolve_naver_map_details(item)
            resolved_item = {
                **item,
                "map_url": resolved_map_url,
                "resolution_status": "selected" if naver_map_id else "needs_review",
            }
            upsert_place_resolution_candidate(connection, youtube_video_id, resolved_item, payload["verified_at"])
            if not naver_map_id:
                print(
                    f"warning: skipped restaurant without Naver map ID: "
                    f"{item.get('display_name') or item.get('resolved_name')} ({item.get('map_url')})",
                    file=sys.stderr,
                )
                continue
            restaurant_id = upsert_restaurant(connection, resolved_item, now, naver_map_id)
            upsert_place_link(connection, restaurant_id, resolved_item, payload["verified_at"])
            upsert_video_restaurant(connection, restaurant_id, youtube_video_id, resolved_item, payload["verified_at"])
            count += 1
        ensure_pipeline_schema(connection)

    return count


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
