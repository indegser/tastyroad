#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("run_regular_source_automation.py")
SPEC = importlib.util.spec_from_file_location("run_regular_source_automation", SCRIPT_PATH)
assert SPEC and SPEC.loader
RUNNER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RUNNER
SPEC.loader.exec_module(RUNNER)


class RegularSourceAutomationTests(unittest.TestCase):
    def test_scope_report_preserves_release_video_ids(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / "report.json"
            report_path.write_text(
                json.dumps(
                    {
                        "release_scope_video_ids": ["video-b", "video-a", "video-b"],
                        "new_videos": [{"video_id": "ignored-fallback"}],
                    }
                ),
                encoding="utf-8",
            )

            self.assertEqual(
                RUNNER.load_scope_video_ids(report_path),
                ["video-a", "video-b"],
            )

    def test_scope_report_supports_legacy_new_video_shape(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / "report.json"
            report_path.write_text(
                json.dumps({"new_videos": [{"video_id": "video-a"}, {"video_id": "video-b"}]}),
                encoding="utf-8",
            )

            self.assertEqual(
                RUNNER.load_scope_video_ids(report_path),
                ["video-a", "video-b"],
            )

    def test_work_queues_route_owned_findings(self) -> None:
        queues = RUNNER.work_queues(
            {
                "blockers": [{"type": "mapping", "video_id": "map-video"}],
                "warnings": [
                    {"type": "transcript", "video_id": "transcript-video"},
                    {"type": "must_taste", "video_id": "taste-video"},
                ],
            }
        )

        self.assertEqual([item["video_id"] for item in queues["map_verification"]], ["map-video"])
        self.assertEqual([item["video_id"] for item in queues["transcript_ingest"]], ["transcript-video"])
        self.assertEqual([item["video_id"] for item in queues["must_taste_validation"]], ["taste-video"])

    def test_release_restaurant_ids_are_limited_to_verified_scoped_videos(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            sqlite_path = Path(directory) / "test.sqlite"
            with sqlite3.connect(sqlite_path) as connection:
                connection.executescript(
                    """
                    create table youtube_videos (id integer primary key, video_id text);
                    create table restaurants (id integer primary key, naver_map_id text);
                    create table youtube_video_restaurants (
                      restaurant_id integer,
                      youtube_video_id integer,
                      status text
                    );
                    insert into youtube_videos values (1, 'scoped'), (2, 'legacy');
                    insert into restaurants values (10, '123'), (11, '456'), (12, '');
                    insert into youtube_video_restaurants values
                      (10, 1, 'verified'),
                      (11, 2, 'verified'),
                      (12, 1, 'verified');
                    """
                )

            self.assertEqual(
                RUNNER.select_release_restaurant_ids(sqlite_path, ["scoped"]),
                [10],
            )


if __name__ == "__main__":
    unittest.main()
