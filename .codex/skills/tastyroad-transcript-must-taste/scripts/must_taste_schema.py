#!/usr/bin/env python3

from __future__ import annotations

import sqlite3
from pathlib import Path


DEFAULT_SQLITE = Path("data/tastyroad.sqlite")


def table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    return (
        connection.execute(
            "select 1 from sqlite_master where type = 'table' and name = ?",
            (table_name,),
        ).fetchone()
        is not None
    )


def column_names(connection: sqlite3.Connection, table_name: str) -> set[str]:
    if not table_exists(connection, table_name):
        return set()
    return {row[1] for row in connection.execute(f"pragma table_info({table_name})").fetchall()}


def ensure_must_taste_schema(connection: sqlite3.Connection) -> None:
    connection.execute("pragma foreign_keys = on")
    connection.execute("drop view if exists video_must_taste_top3")
    if (
        table_exists(connection, "video_must_taste_items")
        and "restaurant_id" not in column_names(connection, "video_must_taste_items")
    ):
        connection.execute("drop table video_must_taste_items")

    connection.executescript(
        """
        create table if not exists video_must_taste_items (
          id integer primary key autoincrement,
          restaurant_id integer not null references restaurants(id) on delete cascade,
          youtube_video_id integer not null references youtube_videos(id) on delete cascade,
          video_id text not null,
          rank integer not null check(rank between 1 and 3),
          item_name text not null check(trim(item_name) != ''),
          reason text not null check(trim(reason) != ''),
          repaired_reason text not null default '',
          segment_index integer not null,
          start_seconds real not null,
          end_seconds real not null,
          timestamp_label text not null,
          evidence_text text not null check(trim(evidence_text) != ''),
          transcript_track_id integer references youtube_transcript_tracks(id) on delete set null,
          reviewer text not null default 'codex',
          generated_at text not null,
          evidence_json text not null default '{}',
          unique(restaurant_id, youtube_video_id, rank)
        );

        create index if not exists video_must_taste_items_restaurant_idx
        on video_must_taste_items(restaurant_id, rank);

        create index if not exists video_must_taste_items_video_idx
        on video_must_taste_items(video_id, restaurant_id, rank);

        create view video_must_taste_top3 as
        select
          r.id as restaurant_id,
          r.display_name as restaurant_name,
          y.id as youtube_video_id,
          y.video_id,
          s.name as source,
          y.title,
          y.url,
          count(i.id) as item_count,
          max(i.generated_at) as generated_at
        from video_must_taste_items i
        join restaurants r on r.id = i.restaurant_id
        join youtube_videos y on y.id = i.youtube_video_id
        join sources s on s.id = y.source_id
        group by r.id, r.display_name, y.id, y.video_id, s.name, y.title, y.url;
        """
    )

    if "repaired_reason" not in column_names(connection, "video_must_taste_items"):
        connection.execute(
            "alter table video_must_taste_items "
            "add column repaired_reason text not null default ''"
        )


def main() -> int:
    with sqlite3.connect(DEFAULT_SQLITE) as connection:
        ensure_must_taste_schema(connection)
    print(f"Ensured must-taste schema in {DEFAULT_SQLITE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
