"""Shared registration and manual invocation of the owned development plugin."""

import json
from pathlib import Path
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/personal-dev"
SKILL = PLUGIN / "skills/dev-delegate"
REVIEW = PLUGIN / "skills/dev-review"


class PersonalDevPackagingTests(unittest.TestCase):
    def test_registered_in_codex_and_claude_with_bundled_resources(self):
        codex = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
        entries = [entry for entry in codex["plugins"] if entry["name"] == "personal-dev"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["source"], {"source": "local", "path": "./plugins/personal-dev"})
        self.assertEqual(entries[0]["skills"], "./skills/")
        manifest = json.loads((PLUGIN / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(
            {path.name for path in (PLUGIN / "skills").iterdir()},
            {"dev-delegate", "dev-review", "dev-yagni", "dev-simplify"},
        )
        self.assertEqual(manifest["name"], entries[0]["name"])
        self.assertEqual(manifest["version"], "0.5.0")
        self.assertEqual(manifest["extensions"]["com.openai"]["interface"], entries[0]["interface"])
        self.assertTrue((SKILL / "scripts/select_models.py").is_file())
        self.assertTrue((SKILL / "references/roles.md").is_file())
        self.assertTrue((REVIEW / "scripts/select_models.py").is_file())
        self.assertTrue((REVIEW / "references/review-contract.md").is_file())
        self.assertTrue((REVIEW / "references/report-template.md").is_file())

        review_frontmatter = yaml.safe_load((REVIEW / "SKILL.md").read_text(encoding="utf-8").split("---", 2)[1])
        review_metadata = yaml.safe_load((REVIEW / "agents/openai.yaml").read_text(encoding="utf-8"))
        self.assertEqual(review_frontmatter["name"], "dev-review")
        self.assertIs(review_frontmatter["disable-model-invocation"], True)
        self.assertIs(review_metadata["policy"]["allow_implicit_invocation"], False)
        self.assertIn("$personal-dev:dev-review", review_metadata["interface"]["default_prompt"])

        for skill_name in ("dev-yagni", "dev-simplify"):
            skill_dir = PLUGIN / "skills" / skill_name
            frontmatter = yaml.safe_load((skill_dir / "SKILL.md").read_text(encoding="utf-8").split("---", 2)[1])
            metadata = yaml.safe_load((skill_dir / "agents/openai.yaml").read_text(encoding="utf-8"))
            self.assertEqual(frontmatter["name"], skill_name)
            self.assertIs(frontmatter["disable-model-invocation"], True)
            self.assertIs(metadata["policy"]["allow_implicit_invocation"], False)
            self.assertIn(f"$personal-dev:{skill_name}", metadata["interface"]["default_prompt"])
            self.assertEqual(
                {path.relative_to(skill_dir).as_posix() for path in skill_dir.rglob("*") if path.is_file()},
                {"SKILL.md", "agents/openai.yaml"},
            )

        claude = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
        claude_entry = next(entry for entry in claude["plugins"] if entry["name"] == "personal-dev")
        self.assertEqual(claude_entry["source"], "./plugins/personal-dev")
        claude_manifest = json.loads((PLUGIN / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(claude_manifest["name"], "personal-dev")
        self.assertNotIn("version", claude_manifest)
        self.assertTrue((PLUGIN / "references/codex.md").is_file())
        self.assertTrue((PLUGIN / "references/claude.md").is_file())

    def test_manual_only_policy_and_owned_source_boundary(self):
        frontmatter = yaml.safe_load((SKILL / "SKILL.md").read_text(encoding="utf-8").split("---", 2)[1])
        metadata = yaml.safe_load((SKILL / "agents/openai.yaml").read_text(encoding="utf-8"))
        self.assertEqual(frontmatter["name"], "dev-delegate")
        self.assertIs(frontmatter["disable-model-invocation"], True)
        self.assertIs(metadata["policy"]["allow_implicit_invocation"], False)
        self.assertIn("$personal-dev:dev-delegate", metadata["interface"]["default_prompt"])
        sources = yaml.safe_load((ROOT / "sources.yaml").read_text(encoding="utf-8"))
        lock = json.loads((ROOT / "sources.lock.json").read_text(encoding="utf-8"))
        self.assertNotIn("personal-dev", sources["groups"])
        self.assertNotIn("personal-dev", {entry["group"] for entry in lock["skills"].values()})


if __name__ == "__main__":
    unittest.main()
