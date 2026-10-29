"""Product catalogs, manifests and shared upstream packaging."""

import json
from pathlib import Path
import re
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]


class PackagingTests(unittest.TestCase):
    def test_retired_plugins_are_absent_from_products_and_sources(self):
        retired = {"personal-dev", "agent-manager"}
        expected = {"common-workflow", "matt", "software-dev", "engineering-tools"}
        self.assertEqual({path.name for path in (ROOT / "plugins").iterdir()}, expected)
        for relative in (".agents/plugins/marketplace.json", ".claude-plugin/marketplace.json"):
            catalog = json.loads((ROOT / relative).read_text(encoding="utf-8"))
            self.assertEqual({item["name"] for item in catalog["plugins"]}, expected)
        sources = yaml.safe_load((ROOT / "sources.yaml").read_text(encoding="utf-8"))["groups"]
        lock = json.loads((ROOT / "sources.lock.json").read_text(encoding="utf-8"))["skills"]
        self.assertFalse(retired & set(sources))
        self.assertFalse(retired & {item["group"] for item in lock.values()})
        for plugin in (ROOT / "plugins").iterdir():
            for document in plugin.rglob("*.md"):
                text = document.read_text(encoding="utf-8")
                for name in retired:
                    self.assertNotIn(f"plugins/{name}/", text, str(document))

    def test_maintenance_resources_resolve_outside_removed_plugins(self):
        contract = ROOT / "docs/agents/execution-resources.md"
        self.assertTrue(contract.is_file())
        for name in ("upgrade", "sync-agy", "sync-dsh", "claude-plugin-dev"):
            document = ROOT / ".agents/skills" / name / "SKILL.md"
            for target in re.findall(r"\]\(([^)\s]+)\)", document.read_text(encoding="utf-8")):
                if "://" in target or target.startswith("#"):
                    continue
                with self.subTest(document=document.relative_to(ROOT), target=target):
                    self.assertTrue((document.parent / target.split("#", 1)[0]).is_file())
        self.assertIn("../../AGENTS.md#任务产物目录", contract.read_text(encoding="utf-8"))

    def test_kimi_installable_entries_are_removed(self):
        catalog = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
        claude = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual({entry["name"] for entry in catalog["plugins"]}, {entry["name"] for entry in claude["plugins"]})
        self.assertFalse((ROOT / "kimi.plugin.json").exists())
        for plugin in (ROOT / "plugins").iterdir():
            self.assertFalse((plugin / "kimi.plugin.json").exists(), plugin.name)
        self.assertFalse((ROOT / "tests/kimi_loader.cjs").exists())


    def test_claude_catalog_uses_same_plugin_roots_and_unpinned_versions(self):
        codex = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
        claude = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(claude["name"], codex["name"])
        self.assertEqual({entry["name"] for entry in claude["plugins"]}, {entry["name"] for entry in codex["plugins"]})
        self.assertEqual(len(claude["plugins"]), 4)
        self.assertEqual({entry["name"] for entry in claude["plugins"]}, {
            "common-workflow", "matt", "software-dev", "engineering-tools",
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
        self.assertEqual(count, 26)
        self.assertEqual(codex_count, 26)
        software = next(entry for entry in claude["plugins"] if entry["name"] == "software-dev")
        software_manifest = json.loads((ROOT / "plugins/software-dev/.claude-plugin/plugin.json").read_text(encoding="utf-8"))
        codex_software = next(entry for entry in codex["plugins"] if entry["name"] == "software-dev")
        codex_manifest = json.loads((ROOT / "plugins/software-dev/plugin.json").read_text(encoding="utf-8"))
        self.assertIn("第三方上游", software["description"])
        self.assertIn("许可证", software_manifest["description"])
        self.assertEqual(codex_manifest["extensions"]["com.openai"]["interface"]["displayName"], "软件开发")
        self.assertIn("第三方上游", codex_software["description"])
        self.assertEqual(
            {path.parent.name for path in (ROOT / "plugins/software-dev/skills").glob("*/SKILL.md")},
            {"frontend-design", "web-design-guidelines", "vue", "fastapi", "java-springboot"},
        )
        for obsolete in ("frontend-dev", "backend-dev", "testing-automation"):
            obsolete_root = ROOT / "plugins" / obsolete
            self.assertFalse((obsolete_root / "plugin.json").exists())
            self.assertEqual(list(obsolete_root.rglob("SKILL.md")), [])
        handoff = (ROOT / "plugins/matt/skills/handoff/SKILL.md").read_text(encoding="utf-8")
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
        for plugin, skill in (("testing-automation", "webapp-testing"), ("software-dev", "java-spring-boot")):
            self.assertFalse((ROOT / "plugins" / plugin / "skills" / skill).exists())
            self.assertFalse((ROOT / "plugins" / plugin / "licenses" / skill).exists())
        for plugin, skill in (("engineering-tools", "docker-compose-patterns"), ("engineering-tools", "playwright-cli"), ("software-dev", "java-springboot")):
            manifest = json.loads((ROOT / "plugins" / plugin / "plugin.json").read_text(encoding="utf-8"))
            catalog = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
            registered = next(item for item in catalog["plugins"] if item["name"] == plugin)
            self.assertEqual(manifest["extensions"]["com.openai"]["interface"], registered["interface"])
            self.assertIn(skill, registered["interface"]["longDescription"])

    def test_playwright_belongs_to_engineering_tools_with_upstream_source_and_policy(self):
        plugin = ROOT / "plugins/engineering-tools"
        directory = plugin / "skills/playwright-cli"
        metadata = yaml.safe_load((directory / "SKILL.md").read_text("utf-8").split("---", 2)[1])
        self.assertEqual(metadata["name"], "playwright-cli")
        self.assertNotIn("disable-model-invocation", metadata)
        self.assertIn("Bash(playwright-cli:*)", metadata["allowed-tools"])
        self.assertTrue((directory / "references/running-code.md").is_file())
        self.assertTrue((plugin / "licenses/playwright-cli/LICENSE").is_file())
        sources = yaml.safe_load((ROOT / "sources.yaml").read_text("utf-8"))["groups"]
        source, = [item for item in sources["engineering-tools"]["skills"] if item["name"] == "playwright-cli"]
        self.assertEqual(source, {"name": "playwright-cli", "repo": "microsoft/playwright-cli",
                                  "path": "skills/playwright-cli", "ref": "main"})
        lock = json.loads((ROOT / "sources.lock.json").read_text("utf-8"))["skills"]["playwright-cli"]
        self.assertEqual({key: lock[key] for key in source}, source)
        self.assertEqual(lock["group"], "engineering-tools")
        self.assertRegex(lock["commit"], r"^[0-9a-f]{40}$")
        self.assertFalse((ROOT / "plugins/testing-automation").exists())



if __name__ == "__main__":
    unittest.main()
