from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT_PATH = (
    Path(__file__).parents[1] / "scripts" / "sync_naver_map_list.py"
)
SPEC = importlib.util.spec_from_file_location("sync_naver_map_list", SCRIPT_PATH)
assert SPEC and SPEC.loader
sync = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = sync
SPEC.loader.exec_module(sync)


class SyncNaverMapListTests(unittest.TestCase):
    def test_list_name_pattern_does_not_confuse_numbered_lists(self) -> None:
        tastyroad = sync.list_name_pattern("Tastyroad")
        tastyroad_two = sync.list_name_pattern("Tastyroad 2")

        self.assertIsNotNone(
            tastyroad.fullmatch("폴더명 Tastyroad 장소수 1,000 선택해제됨")
        )
        self.assertIsNotNone(
            tastyroad.fullmatch("비공개 폴더명 Tastyroad 장소수 1,000 선택됨")
        )
        self.assertIsNone(
            tastyroad.fullmatch("폴더명 Tastyroad 2 장소수 635 선택해제됨")
        )
        self.assertIsNotNone(
            tastyroad_two.fullmatch("폴더명 Tastyroad 2 장소수 635 선택됨")
        )

    def test_parse_list_count_supports_thousands_separator(self) -> None:
        self.assertEqual(
            sync.parse_list_count("폴더명 Tastyroad 장소수 1,000 선택해제됨"),
            1000,
        )

    def test_place_name_matching_ignores_spacing_and_punctuation(self) -> None:
        self.assertTrue(
            sync.place_name_matches(
                "K55 송탄 부대찌개 여의도본점",
                "K55송탄부대찌개 여의도 본점 한식",
            )
        )
        self.assertFalse(sync.place_name_matches("함반", "전혀 다른 식당"))

    def test_parse_browser_refs_reads_agent_browser_snapshot(self) -> None:
        snapshot = """
        - button "저장" [ref=e1]
        - checkbox "비공개 폴더명 Tastyroad 2 장소수 635 선택해제됨" [ref=e2]
        - button "저장" [ref=e3]
        """

        refs = sync.parse_browser_refs(snapshot)

        self.assertEqual([ref.ref for ref in refs], ["e1", "e2", "e3"])
        self.assertEqual(refs[1].role, "checkbox")
        self.assertEqual(refs[1].name, "비공개 폴더명 Tastyroad 2 장소수 635 선택해제됨")

    def test_target_list_checkbox_from_snapshot_uses_exact_list(self) -> None:
        snapshot = """
        - checkbox "폴더명 Tastyroad 장소수 1,000 선택해제됨" [ref=e1]
        - checkbox "비공개 폴더명 Tastyroad 2 장소수 635 선택됨" [ref=e2]
        """

        target = sync.target_list_checkbox_from_snapshot(snapshot, "Tastyroad 2")

        self.assertIsNotNone(target)
        assert target is not None
        checkbox, state, count = target
        self.assertEqual(checkbox.ref, "e2")
        self.assertEqual(state, "selected")
        self.assertEqual(count, 635)

    def test_agent_browser_base_command_uses_persistent_session(self) -> None:
        config = sync.AgentBrowserConfig(
            session="sync-session",
            session_name="Sync Session",
            profile=Path("/tmp/naver-profile"),
            provider="chromium",
            headed=True,
            max_output=1234,
        )

        self.assertEqual(
            sync.agent_browser_base_command(config),
            [
                "agent-browser",
                "--session",
                "sync-session",
                "--session-name",
                "Sync Session",
                "--max-output",
                "1234",
                "--profile",
                "/tmp/naver-profile",
                "--provider",
                "chromium",
                "--headed",
            ],
        )

    def test_success_clears_a_previous_failure(self) -> None:
        place = sync.Place(10, "테스트", "https://map.naver.com/p/entry/place/10")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "failures.json"
            sync.record_failure(path, place, RuntimeError("temporary"), 3, None)
            self.assertEqual(sync.load_failure_ids(path), {10})

            sync.record_failure(
                path,
                place,
                sync.PlacePageNotFound("not found"),
                1,
                None,
            )
            failures = sync.load_failures(path)
            self.assertEqual(len(failures), 1)
            self.assertTrue(failures[0]["permanent"])

            sync.clear_failure(path, 10)
            self.assertEqual(sync.load_failure_ids(path), set())

    def test_load_places_limits_results_to_requested_restaurant_ids(self) -> None:
        connection = mock.MagicMock()
        connection.__enter__.return_value = connection
        connection.execute.return_value.fetchall.return_value = [
            (10, "대상", "https://map.naver.com/p/entry/place/10"),
            (11, "과거", "https://map.naver.com/p/entry/place/11"),
        ]
        with mock.patch.object(sync.sqlite3, "connect", return_value=connection):
            places = sync.load_places(set(), restaurant_ids={10})

        self.assertEqual([place.id for place in places], [10])

    def test_load_places_returns_empty_when_requested_id_is_already_synced(self) -> None:
        connection = mock.MagicMock()
        connection.__enter__.return_value = connection
        connection.execute.return_value.fetchall.return_value = [
            (10, "대상", "https://map.naver.com/p/entry/place/10"),
        ]
        with mock.patch.object(sync.sqlite3, "connect", return_value=connection):
            places = sync.load_places({10}, restaurant_ids={10})

        self.assertEqual(places, [])


if __name__ == "__main__":
    unittest.main()
