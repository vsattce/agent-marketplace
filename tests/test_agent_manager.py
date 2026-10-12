"""Manual-only owned Plugin packaging and bundled references."""

import json
from pathlib import Path
import re
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/agent-manager"


class PackagingTests(unittest.TestCase):
    def test_kimi_installable_entries_are_removed(self):
        catalog = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
        claude = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual({entry["name"] for entry in catalog["plugins"]}, {entry["name"] for entry in claude["plugins"]})
        self.assertFalse((ROOT / "kimi.plugin.json").exists())
        for plugin in (ROOT / "plugins").iterdir():
            self.assertFalse((plugin / "kimi.plugin.json").exists(), plugin.name)
        self.assertFalse((PLUGIN / "references/kimi.md").exists())
        self.assertFalse((ROOT / "plugins/agent-manager/references/agent-sources.md").exists())
        self.assertFalse((ROOT / "tests/kimi_loader.cjs").exists())

    def test_manual_only_metadata_and_marketplace_registration(self):
        catalog = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
        entries = [entry for entry in catalog["plugins"] if entry["name"] == "agent-manager"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["source"]["path"], "./plugins/agent-manager")
        manifest = json.loads((PLUGIN / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["version"], "0.8.1")
        self.assertEqual(entries[0]["description"], manifest["description"])
        self.assertEqual(entries[0]["interface"], manifest["extensions"]["com.openai"]["interface"])
        claude = json.loads((PLUGIN / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
        claude_catalog = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
        claude_entry = next(entry for entry in claude_catalog["plugins"] if entry["name"] == "agent-manager")
        self.assertEqual(claude["description"], manifest["description"])
        self.assertEqual(claude_entry["description"], manifest["description"])
        skill_entries = list((PLUGIN / "skills").glob("*/SKILL.md"))
        self.assertEqual({skill.parent.name for skill in skill_entries}, {"am-config", "am-context"})
        for entry in skill_entries:
            skill_name = entry.parent.name
            policy = yaml.safe_load((entry.parent / "agents/openai.yaml").read_text(encoding="utf-8"))
            self.assertIs(policy["policy"]["allow_implicit_invocation"], False)
            text = entry.read_text(encoding="utf-8")
            frontmatter = yaml.safe_load(text.split("---", 2)[1])
            self.assertEqual(frontmatter["name"], skill_name)
            self.assertIs(frontmatter["disable-model-invocation"], True)
            self.assertIn(f"$agent-manager:{skill_name}", policy["interface"]["default_prompt"])
        sources = yaml.safe_load((ROOT / "sources.yaml").read_text(encoding="utf-8"))
        self.assertNotIn("agent-manager", sources["groups"])
        lock = json.loads((ROOT / "sources.lock.json").read_text(encoding="utf-8"))
        self.assertNotIn("agent-manager", {item["group"] for item in lock["skills"].values()})
        self.assertNotIn("am-config", lock["skills"])
        self.assertNotIn("am-config", {item["name"] for group in sources["groups"].values() for item in group["skills"]})

    def test_claude_catalog_uses_same_plugin_roots_and_unpinned_versions(self):
        codex = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
        claude = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(claude["name"], codex["name"])
        self.assertEqual({entry["name"] for entry in claude["plugins"]}, {entry["name"] for entry in codex["plugins"]})
        self.assertEqual(len(claude["plugins"]), 6)
        self.assertEqual({entry["name"] for entry in claude["plugins"]}, {
            "common-workflow", "software-dev", "engineering-tools", "testing-automation", "agent-manager", "personal-dev",
        })
        count = 0
        for entry in claude["plugins"]:
            counterpart = next(item for item in codex["plugins"] if item["name"] == entry["name"])
            self.assertEqual(entry["source"], counterpart["source"]["path"])
            root = ROOT / entry["source"]
            manifest = json.loads((root / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["name"], entry["name"])
            self.assertNotIn("version", manifest)
            self.assertNotIn("version", entry)
            self.assertNotIn("skills", manifest)  # Default directory discovery, one shared copy.
            count += len(list((root / "skills").glob("*/SKILL.md")))
        self.assertEqual(count, 21)
        software = next(entry for entry in claude["plugins"] if entry["name"] == "software-dev")
        software_manifest = json.loads((ROOT / "plugins/software-dev/.claude-plugin/plugin.json").read_text(encoding="utf-8"))
        codex_software = next(entry for entry in codex["plugins"] if entry["name"] == "software-dev")
        codex_manifest = json.loads((ROOT / "plugins/software-dev/plugin.json").read_text(encoding="utf-8"))
        self.assertIn("第三方上游", software["description"])
        self.assertIn("许可证", software_manifest["description"])
        self.assertEqual(codex_manifest["extensions"]["com.openai"]["interface"]["displayName"], "软件开发")
        self.assertIn("第三方上游", codex_software["description"])
        self.assertIn("OWNED Plugin", codex_manifest["extensions"]["com.openai"]["interface"]["longDescription"])
        self.assertEqual(
            {path.parent.name for path in (ROOT / "plugins/software-dev/skills").glob("*/SKILL.md")},
            {"frontend-design", "web-design-guidelines", "vue-best-practices", "fastapi", "java-spring-boot"},
        )
        for obsolete in ("frontend-dev", "backend-dev"):
            obsolete_root = ROOT / "plugins" / obsolete
            self.assertFalse((obsolete_root / "plugin.json").exists())
            self.assertEqual(list(obsolete_root.rglob("SKILL.md")), [])
        handoff = (ROOT / "plugins/common-workflow/skills/handoff/SKILL.md").read_text(encoding="utf-8")
        self.assertIs(yaml.safe_load(handoff.split("---", 2)[1])["disable-model-invocation"], True)

    def test_bundled_local_references_resolve(self):
        for document in PLUGIN.rglob("*.md"):
            for target in re.findall(r"\]\(([^)\s]+)\)", document.read_text(encoding="utf-8")):
                if "://" in target or target.startswith("#"):
                    continue
                with self.subTest(document=document.relative_to(PLUGIN), target=target):
                    path = (document.parent / target.split("#", 1)[0]).resolve()
                    self.assertTrue(path.is_file(), f"Missing bundled reference: {target}")


if __name__ == "__main__":
    unittest.main()
