#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
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


if __name__ == "__main__":
    unittest.main()
