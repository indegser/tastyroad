#!/usr/bin/env python3

from __future__ import annotations

from collect_youtube import DEFAULT_CONFIG, DEFAULT_OUTPUT_DIR, DEFAULT_SQLITE, collect_sources


def main() -> int:
    counts = collect_sources(
        config_path=DEFAULT_CONFIG,
        output_dir=DEFAULT_OUTPUT_DIR,
        sqlite_path=DEFAULT_SQLITE,
        only_keys={"sungsikyung_mukeultende"},
        full_channel=True,
        workers=4,
        reuse_existing=True,
    )
    print(f"Updated {DEFAULT_SQLITE}")
    print(f"Total candidates collected: {sum(counts.values())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
