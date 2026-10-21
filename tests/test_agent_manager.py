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
        manifest = json.loads((PLUGIN / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["version"], "0.8.3")
        self.assertFalse((PLUGIN / "plugin.json").exists())
        self.assertEqual(manifest["skills"], ["./skills/", "./codex-skills/"])
        self.assertEqual(entries[0]["description"], manifest["description"])
        self.assertEqual(entries[0]["interface"], manifest["interface"])
        self.assertEqual(entries[0]["skills"], manifest["skills"])
        claude = json.loads((PLUGIN / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
        claude_catalog = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
        claude_entry = next(entry for entry in claude_catalog["plugins"] if entry["name"] == "agent-manager")
        self.assertEqual(claude_entry["description"], claude["description"])
        skill_entries = list((PLUGIN / "skills").glob("*/SKILL.md"))
        self.assertEqual({skill.parent.name for skill in skill_entries}, {"am-config"})
        for entry in skill_entries:
            skill_name = entry.parent.name
            policy = yaml.safe_load((entry.parent / "agents/openai.yaml").read_text(encoding="utf-8"))
            self.assertIs(policy["policy"]["allow_implicit_invocation"], False)
            text = entry.read_text(encoding="utf-8")
            frontmatter = yaml.safe_load(text.split("---", 2)[1])
            self.assertEqual(frontmatter["name"], skill_name)
            self.assertIs(frontmatter["disable-model-invocation"], True)
            self.assertIn(f"$agent-manager:{skill_name}", policy["interface"]["default_prompt"])
        codex_entries = list((PLUGIN / "codex-skills").glob("*/SKILL.md"))
        self.assertEqual({skill.parent.name for skill in codex_entries}, {"am-context"})
        policy = yaml.safe_load((PLUGIN / "codex-skills/am-context/agents/openai.yaml").read_text(encoding="utf-8"))
        self.assertIs(policy["policy"]["allow_implicit_invocation"], False)
        context_text = (PLUGIN / "codex-skills/am-context/SKILL.md").read_text(encoding="utf-8")
        context_frontmatter = yaml.safe_load(context_text.split("---", 2)[1])
        self.assertEqual(context_frontmatter["name"], "am-context")
        self.assertNotIn("disable-model-invocation", context_frontmatter)
        self.assertIn("$agent-manager:am-context", policy["interface"]["default_prompt"])
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
        codex_count = 0
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
            codex_count += len(list((root / "skills").glob("*/SKILL.md")))
            codex_count += len(list((root / "codex-skills").glob("*/SKILL.md")))
        self.assertEqual(count, 22)
        self.assertEqual(codex_count, 23)
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
            {"frontend-design", "web-design-guidelines", "vue", "fastapi", "java-springboot"},
        )
        for obsolete in ("frontend-dev", "backend-dev"):
            obsolete_root = ROOT / "plugins" / obsolete
            self.assertFalse((obsolete_root / "plugin.json").exists())
            self.assertEqual(list(obsolete_root.rglob("SKILL.md")), [])
        handoff = (ROOT / "plugins/common-workflow/skills/handoff/SKILL.md").read_text(encoding="utf-8")
        self.assertIs(yaml.safe_load(handoff.split("---", 2)[1])["disable-model-invocation"], True)

    def test_new_skills_are_bundled_and_removed_skills_are_not_discoverable(self):
        compose = ROOT / "plugins/engineering-tools/skills/docker-compose-patterns"
        entry = (compose / "SKILL.md").read_text(encoding="utf-8")
        self.assertEqual(yaml.safe_load(entry.split("---", 2)[1])["name"], "docker-compose-patterns")
        self.assertTrue((compose / "references/service-dependencies.md").is_file())
        self.assertTrue((compose / "scripts/verify-compose.sh").is_file())
        self.assertTrue((ROOT / "plugins/engineering-tools/licenses/docker-compose-patterns/LICENSE").is_file())
        sources = yaml.safe_load((ROOT / "sources.yaml").read_text(encoding="utf-8"))["groups"]
        source = next(item for item in sources["engineering-tools"]["skills"] if item["name"] == "docker-compose-patterns")
        self.assertEqual(source["repo"], "docker/skills")
        self.assertEqual(source["path"], "skills/docker-compose-patterns")
        java = ROOT / "plugins/software-dev/skills/java-springboot"
        java_entry = (java / "SKILL.md").read_text(encoding="utf-8")
        self.assertEqual(yaml.safe_load(java_entry.split("---", 2)[1])["name"], "java-springboot")
        self.assertTrue((ROOT / "plugins/software-dev/licenses/java-springboot/LICENSE").is_file())
        java_source = next(item for item in sources["software-dev"]["skills"] if item["name"] == "java-springboot")
        self.assertEqual(java_source["repo"], "github/awesome-copilot")
        self.assertEqual(java_source["path"], "skills/java-springboot")
        lock = json.loads((ROOT / "sources.lock.json").read_text(encoding="utf-8"))["skills"]
        self.assertEqual(lock["docker-compose-patterns"]["group"], "engineering-tools")
        self.assertEqual(lock["java-springboot"]["group"], "software-dev")
        self.assertNotIn("java-spring-boot", lock)
        self.assertNotIn("webapp-testing", lock)
        self.assertNotIn("webapp-testing", {item["name"] for group in sources.values() for item in group["skills"]})
        for plugin, skill in (("testing-automation", "webapp-testing"), ("personal-dev", "dev-yagni"), ("software-dev", "java-spring-boot")):
            self.assertFalse((ROOT / "plugins" / plugin / "skills" / skill).exists())
            self.assertFalse((ROOT / "plugins" / plugin / "licenses" / skill).exists())
        for plugin, skill in (("engineering-tools", "docker-compose-patterns"), ("testing-automation", "playwright-cli"), ("software-dev", "java-springboot")):
            manifest = json.loads((ROOT / "plugins" / plugin / "plugin.json").read_text(encoding="utf-8"))
            catalog = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
            registered = next(item for item in catalog["plugins"] if item["name"] == plugin)
            self.assertEqual(manifest["extensions"]["com.openai"]["interface"], registered["interface"])
            self.assertIn(skill, registered["interface"]["longDescription"])

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
