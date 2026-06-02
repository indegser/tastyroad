#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path
from urllib.request import urlopen


DEFAULT_SQLITE = Path("data/tastyroad.sqlite")
DEFAULT_HTML = Path("out/index.html")


def expected_public_count(sqlite_path: Path) -> int:
    with sqlite3.connect(sqlite_path) as connection:
        return int(
            connection.execute(
                """
                with reviewed as (
                  select
                    external_id,
                    decision,
                    restaurant_names,
                    case
                      when detected_restaurant_count > 0 then detected_restaurant_count
                      when json_valid(restaurant_names) then json_array_length(restaurant_names)
                      else 0
                    end as detected_restaurant_count
                  from agent_video_reviews
                ),
                mapped as (
                  select
                    mention_candidate_id,
                    count(distinct restaurant_id) as mapped_restaurant_count
                  from mentions
                  group by mention_candidate_id
                )
                select count(*)
                from mention_candidates c
                join reviewed on reviewed.external_id = c.external_id
                join mapped on mapped.mention_candidate_id = c.id
                join video_story_reviews story on story.external_id = c.external_id
                where reviewed.decision = 'restaurant_intro'
                  and mapped.mapped_restaurant_count >= max(coalesce(reviewed.detected_restaurant_count, 1), 1)
                  and (trim(story.story_hook) != '' or trim(story.story_intro) != '')
                """
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
    html = read_html(html_path, url)
    card_count = html.count('class="video-card"')
    story_count = html.count('class="story"')

    if card_count != expected_count:
        raise RuntimeError(
            "Public listing contract failed: "
            f"rendered {card_count} cards, but SQLite has {expected_count} "
            "story-and-map-verified public items."
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
        f"{card_count} cards, {story_count} stories, source={source}"
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
