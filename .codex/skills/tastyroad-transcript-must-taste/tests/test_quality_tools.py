from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from compare_must_taste_quality import (  # noqa: E402
    best_item_assignment,
    evidence_comparison,
    menu_similarity,
)
from measure_must_taste_tokens import read_rollout  # noqa: E402
from prepare_must_taste_video_context import write_review_prompt  # noqa: E402


class QualityComparisonTests(unittest.TestCase):
    def test_menu_similarity_tolerates_spacing_and_suffixes(self) -> None:
        self.assertEqual(menu_similarity("감자 튀김", "감자튀김"), 1.0)
        self.assertGreaterEqual(menu_similarity("칠리 쉬림프 버거", "칠리쉬림프"), 0.72)

    def test_assignment_is_set_based_not_rank_locked(self) -> None:
        baseline = [
            {"rank": 1, "menu_item": "족발", "segment_index": 10, "evidence": {}},
            {"rank": 2, "menu_item": "막국수", "segment_index": 20, "evidence": {}},
        ]
        candidate = [
            {
                "rank": 1,
                "menu_item": "막국수",
                "evidence": {"segment_index": 20},
                "supporting_evidence": [],
            },
            {
                "rank": 2,
                "menu_item": "족발",
                "evidence": {"segment_index": 10},
                "supporting_evidence": [],
            },
        ]
        matches = best_item_assignment(baseline, candidate)
        self.assertTrue(all(match["menu_match"] for match in matches))
        self.assertEqual(matches[0]["candidate_menu_item"], "족발")
        self.assertEqual(matches[1]["candidate_menu_item"], "막국수")

    def test_supporting_evidence_can_recover_nearby_baseline(self) -> None:
        baseline = {
            "segment_index": 100,
            "evidence": {"supporting_evidence": [{"segment_index": 103}]},
        }
        candidate = {
            "evidence": {"segment_index": 80},
            "supporting_evidence": [{"segment_index": 103}],
        }
        comparison = evidence_comparison(baseline, candidate)
        self.assertTrue(comparison["exact"])
        self.assertEqual(comparison["distance"], 0)


class TokenMeasurementTests(unittest.TestCase):
    def test_rollout_uses_final_cumulative_usage(self) -> None:
        rows = [
            {
                "type": "event_msg",
                "payload": {
                    "type": "token_count",
                    "info": {
                        "total_token_usage": {
                            "input_tokens": 100,
                            "cached_input_tokens": 60,
                            "output_tokens": 10,
                            "reasoning_output_tokens": 2,
                            "total_tokens": 110,
                        }
                    },
                },
            },
            {
                "type": "response_item",
                "payload": {"type": "function_call", "name": "exec_command"},
            },
            {
                "type": "event_msg",
                "payload": {
                    "type": "token_count",
                    "info": {
                        "total_token_usage": {
                            "input_tokens": 250,
                            "cached_input_tokens": 200,
                            "output_tokens": 25,
                            "reasoning_output_tokens": 5,
                            "total_tokens": 275,
                        }
                    },
                },
            },
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rollout.jsonl"
            path.write_text(
                "".join(json.dumps(row) + "\n" for row in rows),
                encoding="utf-8",
            )
            report = read_rollout(path)
        self.assertEqual(report["usage"]["input_tokens"], 250)
        self.assertEqual(report["usage"]["uncached_input_tokens"], 50)
        self.assertEqual(report["model_response_count"], 2)
        self.assertEqual(report["tool_call_count"], 1)


class VideoReviewPromptTests(unittest.TestCase):
    def test_prompt_rejects_overlap_and_weak_third_slot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "review.md"
            write_review_prompt(path)
            prompt = path.read_text(encoding="utf-8")

        self.assertIn("never fill the second or third slot", prompt)
        self.assertIn("broad course/set candidate", prompt)
        self.assertIn("A third item needs the same strong standard as rank 1", prompt)
        self.assertIn("rejected_candidates", prompt)


if __name__ == "__main__":
    unittest.main()
