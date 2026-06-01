#!/usr/bin/env python3

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from apply_agent_reviews import DEFAULT_INPUT as DEFAULT_AGENT_REVIEWS, apply_reviews
from collect_youtube import DEFAULT_CONFIG, DEFAULT_OUTPUT_DIR, DEFAULT_SQLITE, collect_sources
from process_video_stories import DEFAULT_INPUT as DEFAULT_STORY_REVIEWS, process_stories
from promote_verified_places import DEFAULT_INPUT_DIR, discover_inputs, promote_many


@dataclass(frozen=True)
class UpdateResult:
    collected_count: int
    fetched_transcript_count: int
    story_review_count: int
    promoted_count: int


def update_pipeline(
    sqlite_path: Path = DEFAULT_SQLITE,
    verified_dir: Path = DEFAULT_INPUT_DIR,
) -> UpdateResult:
    counts = collect_sources(
        config_path=DEFAULT_CONFIG,
        output_dir=DEFAULT_OUTPUT_DIR,
        sqlite_path=sqlite_path,
        full_channel_keys={"sungsikyung_mukeultende"},
    )

    apply_reviews(sqlite_path, DEFAULT_AGENT_REVIEWS)

    story_result = process_stories(sqlite_path, input_path=DEFAULT_STORY_REVIEWS)

    input_paths = discover_inputs(verified_dir)
    if not input_paths:
        raise RuntimeError(f"No verified place JSON files found in {verified_dir}")
    promoted_count = promote_many(sqlite_path, input_paths)

    return UpdateResult(
        collected_count=sum(counts.values()),
        fetched_transcript_count=story_result.fetched_transcript_count,
        story_review_count=story_result.applied_review_count,
        promoted_count=promoted_count,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Refresh the local SQLite pipeline data without rendering or building the site."
    )
    parser.add_argument("--sqlite", type=Path, default=DEFAULT_SQLITE)
    parser.add_argument("--verified-dir", type=Path, default=DEFAULT_INPUT_DIR)
    args = parser.parse_args()

    result = update_pipeline(sqlite_path=args.sqlite, verified_dir=args.verified_dir)

    print(f"Collected candidates: {result.collected_count}")
    print(f"Fetched transcripts: {result.fetched_transcript_count}")
    print(f"Applied Codex story reviews: {result.story_review_count}")
    print(f"Promoted places: {result.promoted_count}")
    print(f"Updated SQLite DB: {args.sqlite}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
