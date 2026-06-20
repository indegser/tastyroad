#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path
from urllib.request import urlopen


DEFAULT_SQLITE = Path("data/tastyroad.sqlite")
DEFAULT_HTML = Path(".next/server/app/index.html")
DEFAULT_DYNAMIC_ROUTE = Path(".next/server/app/page.js")
MIN_STORY_INTRO_CHARS = 240
MIN_TASTING_FLOW_CHARS = 180
DEFAULT_PAGE_SIZE = 20


def active_search_link_count(sqlite_path: Path) -> int:
    with sqlite3.connect(sqlite_path) as connection:
        return int(
            connection.execute(
                """
                select count(*)
                from place_links
                where provider = 'naver_map'
                  and status in ('verified', 'metadata_verified')
                  and url like '%/p/search/%'
                """
            ).fetchone()[0]
        )


def expected_public_count(sqlite_path: Path) -> int:
    with sqlite3.connect(sqlite_path) as connection:
        return int(
            connection.execute(
                """
                select count(distinct r.id)
                from restaurants r
                join youtube_video_restaurants m on m.restaurant_id = r.id
                join youtube_videos c on c.id = m.youtube_video_id
                join agent_video_reviews review on review.external_id = c.video_id
                join video_story_reviews story on story.external_id = c.video_id
                where review.decision = 'restaurant_intro'
                  and trim(r.naver_map_id) != ''
                  and (trim(story.story_hook) != '' or trim(story.story_intro) != '')
                  and length(trim(story.story_intro)) >= ?
                  and length(trim(story.tasting_flow)) >= ?
                """
                ,
                (MIN_STORY_INTRO_CHARS, MIN_TASTING_FLOW_CHARS),
            ).fetchone()[0]
        )


def public_missing_map_count(sqlite_path: Path) -> int:
    with sqlite3.connect(sqlite_path) as connection:
        return int(
            connection.execute(
                """
                with ranked_mentions as (
                  select
                    r.id,
                    row_number() over (
                      partition by r.id
                      order by c.published_at desc, c.id desc
                    ) as mention_rank
                  from restaurants r
                  join youtube_video_restaurants m on m.restaurant_id = r.id
                  join youtube_videos c on c.id = m.youtube_video_id
                  join agent_video_reviews review on review.external_id = c.video_id
                  join video_story_reviews story on story.external_id = c.video_id
                  where review.decision = 'restaurant_intro'
                    and trim(r.naver_map_id) != ''
                    and (trim(story.story_hook) != '' or trim(story.story_intro) != '')
                    and length(trim(story.story_intro)) >= ?
                    and length(trim(story.tasting_flow)) >= ?
                ),
                ranked_links as (
                  select
                    restaurant_id,
                    url,
                    row_number() over (
                      partition by restaurant_id
                      order by
                        case provider
                          when 'naver_map' then 0
                          when 'google_maps' then 1
                          else 2
                        end,
                        confidence desc,
                        verified_at desc
                    ) as link_rank
                  from place_links
                  where status in ('verified', 'metadata_verified')
                    and url not like '%/p/search/%'
                )
                select count(*)
                from ranked_mentions
                left join ranked_links on ranked_links.restaurant_id = ranked_mentions.id
                  and ranked_links.link_rank = 1
                where ranked_mentions.mention_rank = 1
                  and ranked_links.url is null
                """,
                (MIN_STORY_INTRO_CHARS, MIN_TASTING_FLOW_CHARS),
            ).fetchone()[0]
        )


def read_html(html_path: Path | None, url: str | None) -> str:
    if url:
        with urlopen(url, timeout=20) as response:
            return response.read().decode("utf-8")
    if html_path is None:
        raise ValueError("html_path is required when url is not provided")
    return html_path.read_text(encoding="utf-8")


def verify(sqlite_path: Path, html_path: Path | None, url: str | None) -> None:
    expected_count = expected_public_count(sqlite_path)
    expected_page_count = min(expected_count, DEFAULT_PAGE_SIZE)
    search_link_count = active_search_link_count(sqlite_path)
    missing_map_count = public_missing_map_count(sqlite_path)

    if search_link_count:
        raise RuntimeError(
            "Public listing contract failed: "
            f"{search_link_count} active Naver map links are search URLs, "
            "not verified place entries."
        )
    if missing_map_count:
        raise RuntimeError(
            "Public listing contract failed: "
            f"{missing_map_count} public restaurants do not have a verified map link."
        )

    if not url and html_path and not html_path.exists():
        if not DEFAULT_DYNAMIC_ROUTE.exists():
            raise RuntimeError(
                "Public listing contract failed: no static HTML or dynamic "
                "home route artifact was found."
            )
        if expected_count < expected_page_count:
            raise RuntimeError(
                "Public listing contract failed: SQLite public restaurant "
                f"count is invalid ({expected_count})."
            )
        print(
            "Public listing contract ok: "
            f"{expected_count} public restaurants, dynamic route={DEFAULT_DYNAMIC_ROUTE}"
        )
        return

    html = read_html(html_path, url)
    card_count = html.count('class="video-card"')
    story_count = html.count('class="story-section"')

    if "/p/search/" in html:
        raise RuntimeError(
            "Public listing contract failed: rendered HTML contains a "
            "Naver search URL instead of a verified place entry."
        )

    if card_count != expected_page_count:
        raise RuntimeError(
            "Public listing contract failed: "
            f"rendered {card_count} cards, but expected {expected_page_count} "
            f"cards on the first page from {expected_count} public restaurants."
        )
    if story_count != card_count:
        raise RuntimeError(
            "Public listing contract failed: "
            f"rendered {card_count} cards but only {story_count} story blocks. "
            "Every public card must have a story."
        )

    source = url or str(html_path)
    print(
        "Public listing contract ok: "
        f"{card_count} cards, {story_count} stories, "
        f"{expected_count} public restaurants, source={source}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Verify that the public web listing contains only items with both "
            "story reviews and verified map mappings."
        )
    )
    parser.add_argument("--sqlite", type=Path, default=DEFAULT_SQLITE)
    parser.add_argument("--html", type=Path, default=DEFAULT_HTML)
    parser.add_argument("--url", help="Verify a deployed URL instead of a local HTML file.")
    args = parser.parse_args()

    try:
        verify(args.sqlite, None if args.url else args.html, args.url)
    except Exception as exc:  # noqa: BLE001 - CLI should print concise failures.
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
