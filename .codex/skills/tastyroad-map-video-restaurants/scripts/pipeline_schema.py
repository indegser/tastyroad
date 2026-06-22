#!/usr/bin/env python3

from __future__ import annotations

import re
import sqlite3


NAVER_PLACE_ID_RE = re.compile(r"(?:/entry/place/|/place/)(\d+)")


def ensure_pipeline_schema(connection: sqlite3.Connection) -> None:
    connection.execute("pragma foreign_keys = on")
    drop_pipeline_views(connection)
    migrate_legacy_video_schema(connection)
    ensure_source_schema(connection)
    ensure_youtube_video_schema(connection)
    ensure_review_schema(connection)
    ensure_story_review_schema(connection)
    ensure_mapping_schema(connection)
    ensure_pipeline_views(connection)


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


def drop_pipeline_views(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        drop view if exists mapping_backlog;
        drop view if exists unreviewed_videos;
        drop view if exists video_pipeline_status;
        """
    )


def migrate_legacy_video_schema(connection: sqlite3.Connection) -> None:
    if table_exists(connection, "mention_candidates") and not table_exists(connection, "youtube_videos"):
        connection.execute("alter table mention_candidates rename to youtube_videos")

    youtube_video_columns = column_names(connection, "youtube_videos")
    if "external_id" in youtube_video_columns and "video_id" not in youtube_video_columns:
        connection.execute("alter table youtube_videos rename column external_id to video_id")

    if table_exists(connection, "mentions") and not table_exists(connection, "youtube_video_restaurants"):
        connection.execute("alter table mentions rename to youtube_video_restaurants")

    video_restaurant_columns = column_names(connection, "youtube_video_restaurants")
    if (
        "mention_candidate_id" in video_restaurant_columns
        and "youtube_video_id" not in video_restaurant_columns
    ):
        connection.execute(
            "alter table youtube_video_restaurants rename column mention_candidate_id to youtube_video_id"
        )

    resolution_columns = column_names(connection, "place_resolution_candidates")
    if "mention_candidate_id" in resolution_columns and "youtube_video_id" not in resolution_columns:
        connection.execute(
            "alter table place_resolution_candidates rename column mention_candidate_id to youtube_video_id"
        )


def ensure_source_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        create table if not exists sources (
          id integer primary key autoincrement,
          name text not null unique,
          type text not null,
          trust_tier text not null,
          official_url text not null,
          created_at text not null
        )
        """
    )


def ensure_youtube_video_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        create table if not exists youtube_videos (
          id integer primary key autoincrement,
          source_id integer not null references sources(id),
          video_id text not null,
          title text not null,
          url text not null,
          thumbnail_url text not null default '',
          published_at text not null,
          updated_at text not null,
          description text not null default '',
          duration_seconds integer,
          tags text not null default '[]',
          chapters text not null default '[]',
          raw_restaurant_name_candidates text not null,
          collected_at text not null,
          status text not null default 'pending',
          unique(source_id, video_id)
        )
        """
    )
    columns = column_names(connection, "youtube_videos")
    if "thumbnail_url" not in columns:
        connection.execute("alter table youtube_videos add column thumbnail_url text not null default ''")
    if "description" not in columns:
        connection.execute("alter table youtube_videos add column description text not null default ''")
    if "duration_seconds" not in columns:
        connection.execute("alter table youtube_videos add column duration_seconds integer")
    if "tags" not in columns:
        connection.execute("alter table youtube_videos add column tags text not null default '[]'")
    if "chapters" not in columns:
        connection.execute("alter table youtube_videos add column chapters text not null default '[]'")


def ensure_review_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        create table if not exists agent_video_reviews (
          external_id text primary key,
          decision text not null,
          confidence real not null default 0,
          restaurant_names text not null default '[]',
          detected_restaurant_count integer not null default 0,
          reason text not null default '',
          reviewer text not null default 'codex',
          reviewed_at text not null
        )
        """
    )
    columns = {
        row[1]
        for row in connection.execute("pragma table_info(agent_video_reviews)").fetchall()
    }
    if "detected_restaurant_count" not in columns:
        connection.execute(
            "alter table agent_video_reviews add column detected_restaurant_count integer not null default 0"
        )


def ensure_story_review_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        create table if not exists video_story_reviews (
          external_id text primary key,
          story_intro text not null,
          tasting_flow text not null,
          story_hook text not null default '',
          reviewer text not null default 'codex',
          evidence_json text not null default '{}',
          generated_at text not null
        );
        """
    )


def ensure_mapping_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        create table if not exists restaurants (
          id integer primary key autoincrement,
          naver_map_id text not null check(naver_map_id != ''),
          canonical_name text not null,
          display_name text not null,
          local_name text,
          country_code text not null,
          region text not null,
          address text not null,
          phone text,
          category text,
          status text not null default 'open',
          created_at text not null,
          updated_at text not null,
          unique(naver_map_id),
          unique(country_code, address, canonical_name)
        );

        create table if not exists place_links (
          id integer primary key autoincrement,
          restaurant_id integer not null references restaurants(id),
          provider text not null,
          url text not null,
          evidence_url text,
          confidence real not null,
          status text not null,
          notes text,
          verified_at text not null,
          unique(restaurant_id, provider, url)
        );

        create table if not exists youtube_video_restaurants (
          id integer primary key autoincrement,
          restaurant_id integer not null references restaurants(id),
          youtube_video_id integer not null references youtube_videos(id),
          confidence real not null,
          status text not null,
          verified_at text not null,
          unique(restaurant_id, youtube_video_id)
        );

        create table if not exists place_resolution_candidates (
          id integer primary key autoincrement,
          youtube_video_id integer not null references youtube_videos(id),
          search_provider text not null,
          query text not null,
          result_name text not null default '',
          result_address text not null default '',
          result_phone text,
          result_category text,
          result_url text,
          result_rank integer,
          confidence real not null default 0,
          status text not null default 'candidate',
          evidence_json text not null default '{}',
          searched_at text not null,
          unique(youtube_video_id, search_provider, query, result_url)
        );
        """
    )
    columns = column_names(connection, "restaurants")
    if "naver_map_id" not in columns:
        connection.execute("alter table restaurants add column naver_map_id text not null default ''")
    backfill_restaurant_naver_map_ids(connection)
    connection.execute(
        """
        create unique index if not exists restaurants_naver_map_id_unique
        on restaurants(naver_map_id)
        where naver_map_id != ''
        """
    )
    connection.executescript(
        """
        create trigger if not exists restaurants_require_naver_map_id_insert
        before insert on restaurants
        when trim(new.naver_map_id) = ''
        begin
          select raise(abort, 'restaurants.naver_map_id is required');
        end;

        create trigger if not exists restaurants_require_naver_map_id_update
        before update of naver_map_id on restaurants
        when trim(new.naver_map_id) = ''
        begin
          select raise(abort, 'restaurants.naver_map_id is required');
        end;
        """
    )


def extract_naver_map_id(url: str) -> str:
    match = NAVER_PLACE_ID_RE.search(url)
    return match.group(1) if match else ""


def backfill_restaurant_naver_map_ids(connection: sqlite3.Connection) -> None:
    if "naver_map_id" not in column_names(connection, "restaurants"):
        return

    rows = connection.execute(
        """
        select r.id, p.url
        from restaurants r
        join place_links p on p.restaurant_id = r.id
        where r.naver_map_id = ''
          and p.provider = 'naver_map'
          and p.status in ('verified', 'metadata_verified')
          and p.url not like '%/p/search/%'
        order by p.confidence desc, p.verified_at desc, p.id desc
        """
    ).fetchall()
    for restaurant_id, url in rows:
        naver_map_id = extract_naver_map_id(str(url or ""))
        if not naver_map_id:
            continue
        existing = connection.execute(
            "select 1 from restaurants where naver_map_id = ? and id != ?",
            (naver_map_id, restaurant_id),
        ).fetchone()
        if existing is not None:
            continue
        connection.execute(
            "update restaurants set naver_map_id = ? where id = ? and naver_map_id = ''",
            (naver_map_id, restaurant_id),
        )


def ensure_pipeline_views(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        create view video_pipeline_status as
        with mapped as (
          select
            youtube_video_id,
            count(distinct restaurant_id) as mapped_restaurant_count,
            max(verified_at) as last_mapped_at
          from youtube_video_restaurants
          group by youtube_video_id
        ),
        search_counts as (
          select
            youtube_video_id,
            count(*) as search_candidate_count,
            max(searched_at) as last_search_at
          from place_resolution_candidates
          group by youtube_video_id
        ),
        reviewed as (
          select
            external_id,
            decision,
            confidence,
            restaurant_names,
            case
              when detected_restaurant_count > 0 then detected_restaurant_count
              when json_valid(restaurant_names) then json_array_length(restaurant_names)
              else 0
            end as detected_restaurant_count,
            reason,
            reviewer,
            reviewed_at
          from agent_video_reviews
        )
        select
          c.id as youtube_video_id,
          c.video_id,
          s.name as source,
          c.title,
          c.url,
          c.published_at,
          c.collected_at,
          case
            when r.external_id is null then 'unreviewed'
            when r.decision = 'not_restaurant' then 'reviewed_not_restaurant'
            when r.decision = 'uncertain' then 'reviewed_uncertain'
            when r.decision = 'restaurant_intro' and r.detected_restaurant_count > 1 then 'reviewed_restaurant_multi'
            when r.decision = 'restaurant_intro' then 'reviewed_restaurant_single'
            else 'reviewed_other'
          end as review_status,
          r.decision as review_decision,
          coalesce(r.detected_restaurant_count, 0) as detected_restaurant_count,
          coalesce(r.restaurant_names, '[]') as reviewed_restaurant_names,
          r.confidence as review_confidence,
          r.reviewed_at,
          coalesce(sc.search_candidate_count, 0) as search_candidate_count,
          sc.last_search_at,
          coalesce(m.mapped_restaurant_count, 0) as mapped_restaurant_count,
          m.last_mapped_at,
          case
            when r.external_id is null then 'not_ready_for_mapping'
            when r.decision != 'restaurant_intro' then 'not_applicable'
            when coalesce(m.mapped_restaurant_count, 0) = 0 then 'mapping_pending'
            when coalesce(m.mapped_restaurant_count, 0) < max(coalesce(r.detected_restaurant_count, 1), 1) then 'mapping_partial'
            else 'mapping_verified'
          end as mapping_status
        from youtube_videos c
        join sources s on s.id = c.source_id
        left join reviewed r on r.external_id = c.video_id
        left join mapped m on m.youtube_video_id = c.id
        left join search_counts sc on sc.youtube_video_id = c.id;

        create view unreviewed_videos as
        select *
        from video_pipeline_status
        where review_status = 'unreviewed';

        create view mapping_backlog as
        select *
        from video_pipeline_status
        where mapping_status in ('mapping_pending', 'mapping_partial');
        """
    )
