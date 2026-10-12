"""Packaging boundary for the am-context Skill."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "plugins/agent-manager/skills/am-context"


class ContextPackagingTests(unittest.TestCase):
    def test_skill_does_not_ship_a_runtime_helper(self):
        script_files = [path for path in (SKILL / "scripts").rglob("*") if path.is_file()]
        self.assertEqual(script_files, [])


if __name__ == "__main__":
    unittest.main()
