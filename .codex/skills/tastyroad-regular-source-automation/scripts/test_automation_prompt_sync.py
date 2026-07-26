from __future__ import annotations

import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL_PATH = SKILL_DIR / "SKILL.md"
RUNBOOK_PATH = SKILL_DIR / "scripts" / "automation_prompt.md"


class AutomationPromptSyncTests(unittest.TestCase):
    def test_runbook_requires_current_origin_main_and_fresh_skill_reads(self) -> None:
        runbook = RUNBOOK_PATH.read_text(encoding="utf-8")

        self.assertIn("current `origin/main`", runbook)
        self.assertIn("reread `AGENTS.md`", runbook)
        self.assertIn("every owning skill", runbook)
        self.assertIn("source of truth", runbook)
        self.assertIn("Do not duplicate this full runbook", runbook)

    def test_skill_defines_a_thin_bootstrap_prompt(self) -> None:
        skill = SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn("thin bootstrap prompt", skill)
        self.assertIn("current origin/main", skill)
        self.assertIn("automation_prompt.md", skill)
        self.assertIn("supersede details cached", skill)
        self.assertIn("Do not copy the full current runbook", skill)


if __name__ == "__main__":
    unittest.main()
