import copy
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from repair_must_taste_display_copy import repair_copy, row_fingerprint


class DisplayCopyRepairTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "test.sqlite"
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TABLE video_must_taste_items (id INTEGER PRIMARY KEY, rank INTEGER, reason TEXT, repaired_reason TEXT, evidence_json TEXT)")
            db.executemany("INSERT INTO video_must_taste_items VALUES (?, 1, ?, ?, ?)", [
                (1, "정말 맛있어", "맛있다고 했습니다.", '{"repaired_reason":"맛있다고 했습니다.","evidence":{"text":"정말 맛있어"}}'),
                (2, "훌륭했습니다", "훌륭했습니다.", '{"evidence":{"text":"훌륭했습니다"}}'),
            ])
        self.before = self.rows()
        self.fix = {"id": 1, "before": self.before[0]["repaired_reason"], "after": "정말 맛있어.", "row_sha256": row_fingerprint(self.before[0]), "source_quote": "정말 맛있어", "review": {"verdict": "pass"}}

    def rows(self):
        with sqlite3.connect(self.path) as db:
            db.row_factory = sqlite3.Row
            return [dict(row) for row in db.execute("SELECT * FROM video_must_taste_items ORDER BY id")]

    def test_dry_run_does_not_write(self):
        original = self.path.read_bytes()
        self.assertEqual(repair_copy(self.path, {"fixes": [self.fix]})["rows"], 1)
        self.assertEqual(self.path.read_bytes(), original)

    def test_only_display_and_mirror_change(self):
        repair_copy(self.path, {"fixes": [self.fix]}, apply=True)
        after = self.rows()
        self.assertEqual(after[1], self.before[1])
        for key in ("id", "rank", "reason"):
            self.assertEqual(after[0][key], self.before[0][key])
        doc = json.loads(self.before[0]["evidence_json"])
        doc["repaired_reason"] = self.fix["after"]
        self.assertEqual(json.loads(after[0]["evidence_json"]), doc)

    def test_stale_row_rejects_entire_batch(self):
        bad = copy.deepcopy(self.fix)
        bad.update(id=2, row_sha256="stale")
        with self.assertRaisesRegex(ValueError, "Stale"):
            repair_copy(self.path, {"fixes": [self.fix, bad]}, apply=True)
        self.assertEqual(self.rows(), self.before)

    def test_unreviewed_duplicate_and_invalid_copy_rejected(self):
        for change in ({"review": {}}, {"after": "a\nb"}, {"after": "a" * 281}, {"before": "wrong"}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                repair_copy(self.path, {"fixes": [dict(self.fix, **change)]}, apply=True)
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            repair_copy(self.path, {"fixes": [self.fix, self.fix]}, apply=True)
        self.assertEqual(self.rows(), self.before)


if __name__ == "__main__":
    unittest.main()
