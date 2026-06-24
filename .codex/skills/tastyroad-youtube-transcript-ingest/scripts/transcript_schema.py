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


def ensure_column(
    connection: sqlite3.Connection,
    table_name: str,
    column_name: str,
    column_definition: str,
) -> None:
    if column_name in column_names(connection, table_name):
        return
    connection.execute(f"alter table {table_name} add column {column_name} {column_definition}")


def ensure_transcript_schema(connection: sqlite3.Connection) -> None:
    connection.execute("pragma foreign_keys = on")
    connection.executescript(
        """
        create table if not exists youtube_transcript_jobs (
          id integer primary key autoincrement,
          scope_type text not null,
          scope_value text not null default '',
          requested_languages text not null default '[]',
          status text not null,
          started_at text not null,
          finished_at text,
          stats_json text not null default '{}'
        );

        create table if not exists youtube_transcript_tracks (
          id integer primary key autoincrement,
          youtube_video_id integer not null references youtube_videos(id) on delete cascade,
          video_id text not null,
          source_name text not null default '',
          language_code text not null,
          language text not null default '',
          is_generated integer not null default 0,
          provider text not null default 'youtube_transcript_api',
          provider_track_id text not null default '',
          raw_json text not null default '[]',
          transcript_text text not null default '',
          content_hash text not null,
          segment_count integer not null default 0,
          storage_provider text not null default 'sqlite',
          raw_blob_path text not null default '',
          raw_blob_size integer not null default 0,
          segments_blob_path text not null default '',
          segments_blob_size integer not null default 0,
          blob_uploaded_at text not null default '',
          blob_metadata_json text not null default '{}',
          fetched_at text not null,
          unique(youtube_video_id, language_code, is_generated, provider)
        );

        create table if not exists youtube_transcript_segments (
          id integer primary key autoincrement,
          track_id integer not null references youtube_transcript_tracks(id) on delete cascade,
          segment_index integer not null,
          start_seconds real not null default 0,
          duration_seconds real not null default 0,
          end_seconds real not null default 0,
          text text not null,
          raw_json text not null default '{}',
          unique(track_id, segment_index)
        );

        create table if not exists youtube_transcript_fetch_attempts (
          id integer primary key autoincrement,
          job_id integer references youtube_transcript_jobs(id) on delete set null,
          youtube_video_id integer references youtube_videos(id) on delete cascade,
          video_id text not null,
          provider text not null default 'youtube_transcript_api',
          requested_languages text not null default '[]',
          status text not null,
          error_type text not null default '',
          error_message text not null default '',
          attempted_at text not null,
          metadata_json text not null default '{}'
        );

        create index if not exists youtube_transcript_tracks_video_id_idx
        on youtube_transcript_tracks(video_id);

        create index if not exists youtube_transcript_segments_track_start_idx
        on youtube_transcript_segments(track_id, start_seconds);

        create index if not exists youtube_transcript_fetch_attempts_video_idx
        on youtube_transcript_fetch_attempts(video_id, attempted_at);
        """
    )
    ensure_transcript_columns(connection)
    ensure_transcript_views(connection)


def ensure_transcript_columns(connection: sqlite3.Connection) -> None:
    ensure_column(
        connection,
        "youtube_transcript_tracks",
        "storage_provider",
        "text not null default 'sqlite'",
    )
    ensure_column(
        connection,
        "youtube_transcript_tracks",
        "raw_blob_path",
        "text not null default ''",
    )
    ensure_column(
        connection,
        "youtube_transcript_tracks",
        "raw_blob_size",
        "integer not null default 0",
    )
    ensure_column(
        connection,
        "youtube_transcript_tracks",
        "segments_blob_path",
        "text not null default ''",
    )
    ensure_column(
        connection,
        "youtube_transcript_tracks",
        "segments_blob_size",
        "integer not null default 0",
    )
    ensure_column(
        connection,
        "youtube_transcript_tracks",
        "blob_uploaded_at",
        "text not null default ''",
    )
    ensure_column(
        connection,
        "youtube_transcript_tracks",
        "blob_metadata_json",
        "text not null default '{}'",
    )


def ensure_transcript_views(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        drop view if exists preferred_youtube_transcripts;
        drop view if exists youtube_transcript_status;

        create view preferred_youtube_transcripts as
        with ranked as (
          select
            t.*,
            row_number() over (
              partition by t.youtube_video_id
              order by
                case
                  when t.language_code = 'ko' and t.is_generated = 0 then 0
                  when t.language_code = 'ko' and t.is_generated = 1 then 1
                  when t.language_code = 'en' and t.is_generated = 0 then 2
                  when t.language_code = 'en' and t.is_generated = 1 then 3
                  when t.is_generated = 0 then 4
                  else 5
                end,
                t.fetched_at desc,
                t.id desc
            ) as transcript_rank
          from youtube_transcript_tracks t
        )
        select
          id,
          youtube_video_id,
          video_id,
          source_name,
          language_code,
          language,
          is_generated,
          provider,
          provider_track_id,
          raw_json,
          transcript_text,
          content_hash,
          segment_count,
          storage_provider,
          raw_blob_path,
          raw_blob_size,
          segments_blob_path,
          segments_blob_size,
          blob_uploaded_at,
          blob_metadata_json,
          fetched_at
        from ranked
        where transcript_rank = 1;

        create view youtube_transcript_status as
        with preferred as (
          select *
          from preferred_youtube_transcripts
        ),
        last_attempt as (
          select
            a.*,
            row_number() over (
              partition by a.youtube_video_id
              order by a.attempted_at desc, a.id desc
            ) as attempt_rank
          from youtube_transcript_fetch_attempts a
        )
        select
          y.id as youtube_video_id,
          y.video_id,
          s.name as source,
          y.title,
          y.published_at,
          case
            when p.id is not null then 'has_transcript'
            when la.id is not null and la.status = 'failed' then 'fetch_failed'
            else 'missing_transcript'
          end as transcript_status,
          p.id as preferred_track_id,
          p.language_code,
          p.language,
          p.is_generated,
          p.segment_count,
          p.storage_provider,
          p.raw_blob_path,
          p.raw_blob_size,
          p.segments_blob_path,
          p.segments_blob_size,
          p.blob_uploaded_at,
          p.fetched_at,
          la.status as last_attempt_status,
          la.error_type as last_error_type,
          la.error_message as last_error_message,
          la.attempted_at as last_attempted_at
        from youtube_videos y
        join sources s on s.id = y.source_id
        left join preferred p on p.youtube_video_id = y.id
        left join last_attempt la on la.youtube_video_id = y.id
          and la.attempt_rank = 1;
        """
    )


def main() -> int:
    with sqlite3.connect(DEFAULT_SQLITE) as connection:
        ensure_transcript_schema(connection)
    print(f"Ensured transcript schema in {DEFAULT_SQLITE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
