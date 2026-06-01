#!/usr/bin/env python3

from __future__ import annotations

import sqlite3


def ensure_pipeline_schema(connection: sqlite3.Connection) -> None:
    connection.execute("pragma foreign_keys = on")
    ensure_review_schema(connection)
    ensure_mapping_schema(connection)
    ensure_pipeline_views(connection)


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


def ensure_mapping_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        create table if not exists restaurants (
          id integer primary key autoincrement,
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

        create table if not exists mentions (
          id integer primary key autoincrement,
          restaurant_id integer not null references restaurants(id),
          mention_candidate_id integer not null references mention_candidates(id),
          confidence real not null,
          status text not null,
          verified_at text not null,
          unique(restaurant_id, mention_candidate_id)
        );

        create table if not exists place_resolution_candidates (
          id integer primary key autoincrement,
          mention_candidate_id integer not null references mention_candidates(id),
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
          unique(mention_candidate_id, search_provider, query, result_url)
        );
        """
    )


def ensure_pipeline_views(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        drop view if exists video_pipeline_status;
        create view video_pipeline_status as
        with mapped as (
          select
            mention_candidate_id,
            count(distinct restaurant_id) as mapped_restaurant_count,
            max(verified_at) as last_mapped_at
          from mentions
          group by mention_candidate_id
        ),
        search_counts as (
          select
            mention_candidate_id,
            count(*) as search_candidate_count,
            max(searched_at) as last_search_at
          from place_resolution_candidates
          group by mention_candidate_id
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
          c.id as mention_candidate_id,
          c.external_id as video_id,
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
        from mention_candidates c
        join sources s on s.id = c.source_id
        left join reviewed r on r.external_id = c.external_id
        left join mapped m on m.mention_candidate_id = c.id
        left join search_counts sc on sc.mention_candidate_id = c.id;

        drop view if exists unreviewed_videos;
        create view unreviewed_videos as
        select *
        from video_pipeline_status
        where review_status = 'unreviewed';

        drop view if exists mapping_backlog;
        create view mapping_backlog as
        select *
        from video_pipeline_status
        where mapping_status in ('mapping_pending', 'mapping_partial');
        """
    )
