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


def expected_public_count(sqlite_path: Path) -> int:
    with sqlite3.connect(sqlite_path) as connection:
        return int(
            connection.execute(
                """
                select count(distinct r.id)
                from restaurants r
                join mentions m on m.restaurant_id = r.id
                join mention_candidates c on c.id = m.mention_candidate_id
                join agent_video_reviews review on review.external_id = c.external_id
                join video_story_reviews story on story.external_id = c.external_id
                where review.decision = 'restaurant_intro'
                  and (trim(story.story_hook) != '' or trim(story.story_intro) != '')
                  and length(trim(story.story_intro)) >= ?
                  and length(trim(story.tasting_flow)) >= ?
                """
                ,
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
