#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from collect_youtube import DEFAULT_CONFIG, DEFAULT_OUTPUT_DIR, DEFAULT_SQLITE, collect_sources
from promote_verified_places import DEFAULT_INPUT_DIR, discover_inputs, promote_many
from render_site import load_candidates, render_page


DEFAULT_SITE_OUTPUT = ROOT / "public" / "index.html"


@dataclass(frozen=True)
class BuildResult:
    collected_count: int
    promoted_count: int
    rendered_count: int
    thumbnail_count: int


def build_site(
    sqlite_path: Path = DEFAULT_SQLITE,
    output_path: Path = DEFAULT_SITE_OUTPUT,
    verified_dir: Path = DEFAULT_INPUT_DIR,
    limit: int = 80,
) -> BuildResult:
    counts = collect_sources(
        config_path=DEFAULT_CONFIG,
        output_dir=DEFAULT_OUTPUT_DIR,
        sqlite_path=sqlite_path,
        full_channel_keys={"sungsikyung_mukeultende"},
    )

    input_paths = discover_inputs(verified_dir)
    if not input_paths:
        raise RuntimeError(f"No verified place JSON files found in {verified_dir}")
    promoted_count = promote_many(sqlite_path, input_paths)

    candidates, _collected_at = load_candidates(sqlite_path, limit)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_page(candidates), encoding="utf-8")

    thumbnail_count = verify_build(sqlite_path, output_path, len(candidates))
    return BuildResult(
        collected_count=sum(counts.values()),
        promoted_count=promoted_count,
        rendered_count=len(candidates),
        thumbnail_count=thumbnail_count,
    )


def verify_build(sqlite_path: Path, output_path: Path, rendered_count: int) -> int:
    if rendered_count == 0:
        raise RuntimeError("Rendered site has no candidates")

    html = output_path.read_text(encoding="utf-8")
    required_fragments = [
        'class="thumbnail"',
        'class="video-card"',
        "업로드 ",
    ]
    for fragment in required_fragments:
        if fragment not in html:
            raise RuntimeError(f"Rendered site is missing expected fragment: {fragment}")

    with sqlite3.connect(sqlite_path) as connection:
        missing_visible_thumbnails = connection.execute(
            """
            select c.external_id
            from mentions m
            join mention_candidates c on c.id = m.mention_candidate_id
            where c.thumbnail_url = ''
            order by c.published_at desc
            limit 1
            """
        ).fetchone()
        thumbnail_count = connection.execute(
            """
            select count(*)
            from mention_candidates
            where thumbnail_url != ''
            """
        ).fetchone()[0]

    if missing_visible_thumbnails:
        raise RuntimeError(
            f"Promoted video is missing thumbnail_url: {missing_visible_thumbnails[0]}"
        )
    if int(thumbnail_count) == 0:
        raise RuntimeError("No collected YouTube candidates have thumbnail_url")

    return int(thumbnail_count)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Collect YouTube data, promote verified places, render the static page, and verify required UI data."
    )
    parser.add_argument("--sqlite", type=Path, default=DEFAULT_SQLITE)
    parser.add_argument("--output", type=Path, default=DEFAULT_SITE_OUTPUT)
    parser.add_argument("--verified-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--limit", type=int, default=80)
    args = parser.parse_args()

    result = build_site(
        sqlite_path=args.sqlite,
        output_path=args.output,
        verified_dir=args.verified_dir,
        limit=args.limit,
    )

    print(f"Collected candidates: {result.collected_count}")
    print(f"Promoted places: {result.promoted_count}")
    print(f"Rendered candidates: {result.rendered_count}")
    print(f"Candidates with thumbnails: {result.thumbnail_count}")
    print(f"Verified {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
