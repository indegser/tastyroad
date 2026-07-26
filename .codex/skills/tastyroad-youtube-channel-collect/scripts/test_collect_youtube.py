from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("collect_youtube.py")
SPEC = importlib.util.spec_from_file_location("collect_youtube", SCRIPT_PATH)
assert SPEC and SPEC.loader
collect = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = collect
SPEC.loader.exec_module(collect)


class CollectYoutubeTests(unittest.TestCase):
    def test_reused_candidate_preserves_original_collected_at(self) -> None:
        existing = collect.YoutubeVideo(
            source_key="source",
            source="Source",
            channel_id="channel",
            video_id="video",
            title="Existing title",
            url="https://youtube.com/watch?v=video",
            thumbnail_url="thumbnail",
            published_at="2026-07-01T00:00:00Z",
            updated_at="",
            description="Existing description",
            duration_seconds=60,
            tags=[],
            chapters=[],
            restaurant_name_candidates=[],
            collected_at="2026-07-01T01:00:00Z",
        )
        candidate = collect.YoutubeVideo(
            source_key="source",
            source="Source",
            channel_id="channel",
            video_id="video",
            title="Existing title",
            url="https://youtube.com/watch?v=video",
            thumbnail_url="thumbnail",
            published_at="2026-07-01T00:00:00Z",
            updated_at="",
            description="Existing description",
            duration_seconds=None,
            tags=[],
            chapters=[],
            restaurant_name_candidates=[],
            collected_at="2026-07-26T00:00:00Z",
        )

        merged = collect.merge_candidate_with_existing(
            candidate,
            existing,
            "2026-07-26T00:00:00Z",
        )

        self.assertEqual(merged.collected_at, existing.collected_at)


if __name__ == "__main__":
    unittest.main()
