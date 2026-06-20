#!/usr/bin/env python3

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".codex/skills/tastyroad-data-pipeline/scripts"))

from collect_youtube import DEFAULT_CONFIG, DEFAULT_OUTPUT_DIR, DEFAULT_SQLITE, collect_sources
from promote_verified_places import DEFAULT_INPUT, promote


def verify(sqlite_path: Path) -> list[tuple[str, str, str, float, str]]:
    with sqlite3.connect(sqlite_path) as connection:
        rows = connection.execute(
            """
            select
              r.display_name,
              r.address,
              p.provider,
              m.confidence,
              m.status
            from restaurants r
            join youtube_video_restaurants m on m.restaurant_id = r.id
            join place_links p on p.restaurant_id = r.id
            order by m.confidence desc
            """
        ).fetchall()

    if len(rows) < 3:
        raise RuntimeError(f"Expected at least 3 promoted restaurants, got {len(rows)}")

    return [(str(name), str(address), str(provider), float(confidence), str(status)) for name, address, provider, confidence, status in rows]


def main() -> int:
    counts = collect_sources(
        config_path=DEFAULT_CONFIG,
        output_dir=DEFAULT_OUTPUT_DIR,
        sqlite_path=DEFAULT_SQLITE,
        only_keys={"sungsikyung_mukeultende"},
    )

    promoted_count = promote(DEFAULT_SQLITE, DEFAULT_INPUT)
    rows = verify(DEFAULT_SQLITE)

    print(f"Collected candidates: {sum(counts.values())}")
    print(f"Promoted places: {promoted_count}")
    for name, address, provider, confidence, status in rows:
        print(f"- {name} | {address} | {provider} | {confidence:.2f} | {status}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
