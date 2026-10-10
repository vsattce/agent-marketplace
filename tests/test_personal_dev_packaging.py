"""Codex-only registration and manual invocation of the owned development plugin."""

import json
from pathlib import Path
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/personal-dev"
SKILL = PLUGIN / "skills/delegated-development"
REVIEW = PLUGIN / "skills/review"


class PersonalDevPackagingTests(unittest.TestCase):
    def test_registered_only_in_codex_with_bundled_resources(self):
        codex = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
        entries = [entry for entry in codex["plugins"] if entry["name"] == "personal-dev"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["source"], {"source": "local", "path": "./plugins/personal-dev"})
        self.assertEqual(entries[0]["skills"], "./skills/")
        manifest = json.loads((PLUGIN / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], entries[0]["name"])
        self.assertEqual(manifest["version"], "0.2.0")
        self.assertEqual(manifest["extensions"]["com.openai"]["interface"], entries[0]["interface"])
        self.assertEqual(
            {path.name for path in (PLUGIN / "skills").iterdir()},
            {"delegated-development", "review"},
        )
        self.assertTrue((SKILL / "scripts/select_models.py").is_file())
        self.assertTrue((SKILL / "references/roles.md").is_file())
        self.assertTrue((REVIEW / "scripts/select_models.py").is_file())
        self.assertTrue((REVIEW / "references/review-contract.md").is_file())
        self.assertTrue((REVIEW / "references/report-template.md").is_file())

        review_frontmatter = yaml.safe_load((REVIEW / "SKILL.md").read_text(encoding="utf-8").split("---", 2)[1])
        review_metadata = yaml.safe_load((REVIEW / "agents/openai.yaml").read_text(encoding="utf-8"))
        self.assertEqual(review_frontmatter["name"], "review")
        self.assertIs(review_frontmatter["disable-model-invocation"], True)
        self.assertIs(review_metadata["policy"]["allow_implicit_invocation"], False)
        self.assertIn("$personal-dev:review", review_metadata["interface"]["default_prompt"])

        claude = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
        kimi = json.loads((ROOT / "kimi.plugin.json").read_text(encoding="utf-8"))
        self.assertNotIn("personal-dev", {entry["name"] for entry in claude["plugins"]})
        self.assertNotIn("./plugins/personal-dev/skills/", kimi["skills"])
        self.assertFalse((PLUGIN / ".claude-plugin").exists())
        self.assertFalse((PLUGIN / "kimi.plugin.json").exists())

    def test_manual_only_policy_and_owned_source_boundary(self):
        frontmatter = yaml.safe_load((SKILL / "SKILL.md").read_text(encoding="utf-8").split("---", 2)[1])
        metadata = yaml.safe_load((SKILL / "agents/openai.yaml").read_text(encoding="utf-8"))
        self.assertEqual(frontmatter["name"], "delegated-development")
        self.assertIs(frontmatter["disable-model-invocation"], True)
        self.assertIs(metadata["policy"]["allow_implicit_invocation"], False)
        self.assertIn("$personal-dev:delegated-development", metadata["interface"]["default_prompt"])
        sources = yaml.safe_load((ROOT / "sources.yaml").read_text(encoding="utf-8"))
        lock = json.loads((ROOT / "sources.lock.json").read_text(encoding="utf-8"))
        self.assertNotIn("personal-dev", sources["groups"])
        self.assertNotIn("personal-dev", {entry["group"] for entry in lock["skills"].values()})


if __name__ == "__main__":
    unittest.main()
