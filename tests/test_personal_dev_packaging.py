"""Retained personal-dev entrypoints and their complete standalone resources."""

import json
from pathlib import Path
import re
import subprocess
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/personal-dev"
REVIEW = PLUGIN / "skills/dev-review"
RETAINED = {"dev-review", "dev-runtime-check", "dev-simplify"}
RETIRED = {"dev-prepare", "dev-delegate", "dev-auto"}


class PersonalDevPackagingTests(unittest.TestCase):
    def test_exact_retained_inventory_and_manual_policy(self):
        self.assertEqual({p.parent.name for p in (PLUGIN / "skills").glob("*/SKILL.md")}, RETAINED)
        for name in RETAINED:
            directory = PLUGIN / "skills" / name
            text = (directory / "SKILL.md").read_text("utf-8")
            metadata = yaml.safe_load(text.split("---", 2)[1])
            policy = yaml.safe_load((directory / "agents/openai.yaml").read_text("utf-8"))
            with self.subTest(skill=name):
                self.assertEqual(metadata["name"], name)
                self.assertIs(metadata["disable-model-invocation"], True)
                self.assertIs(policy["policy"]["allow_implicit_invocation"], False)
                self.assertIn(f"$personal-dev:{name}", policy["interface"]["default_prompt"])
                self.assertTrue(any("\u4e00" <= c <= "\u9fff" for c in metadata["description"]))
                self.assertLess(len(text.encode("utf-8")), 8000)
        for name in RETIRED:
            self.assertFalse((PLUGIN / "skills" / name).exists())
        self.assertFalse((PLUGIN / "references/preparation.md").exists())
        for path in PLUGIN.rglob("*"):
            if path.is_file():
                text = path.read_text("utf-8")
                for name in RETIRED:
                    self.assertNotIn(name, text, str(path))

    def test_registrations_and_owned_source_boundary(self):
        codex = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text("utf-8"))
        claude = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text("utf-8"))
        manifest = json.loads((PLUGIN / "plugin.json").read_text("utf-8"))
        entry = next(item for item in codex["plugins"] if item["name"] == "personal-dev")
        self.assertEqual(entry["source"], {"source": "local", "path": "./plugins/personal-dev"})
        self.assertEqual(entry["interface"], manifest["extensions"]["com.openai"]["interface"])
        self.assertEqual(entry["description"], manifest["description"])
        self.assertEqual(next(item for item in claude["plugins"] if item["name"] == "personal-dev")["source"], "./plugins/personal-dev")
        for name in RETAINED:
            self.assertIn(name, entry["interface"]["longDescription"])
        sources = yaml.safe_load((ROOT / "sources.yaml").read_text("utf-8"))["groups"]
        lock = json.loads((ROOT / "sources.lock.json").read_text("utf-8"))["skills"]
        self.assertNotIn("personal-dev", sources)
        self.assertNotIn("personal-dev", {item["group"] for item in lock.values()})

    def test_all_bundled_links_resolve(self):
        for document in PLUGIN.rglob("*.md"):
            for target in re.findall(r"\]\(([^)\s]+)\)", document.read_text("utf-8")):
                if "://" in target or target.startswith("#"):
                    continue
                with self.subTest(document=document.relative_to(PLUGIN), target=target):
                    self.assertTrue((document.parent / target.split("#", 1)[0]).is_file())
        for source in [PLUGIN / "skills" / name / "SKILL.md" for name in RETAINED]:
            self.assertIn("execution-resources.md", source.read_text("utf-8"))
        for name in ("upgrade", "sync-agy", "sync-dsh", "claude-plugin-dev"):
            self.assertTrue((PLUGIN / "references/execution-resources.md").is_file())
            entry = ROOT / ".agents/skills" / name / "SKILL.md"
            self.assertIn("execution-resources.md", entry.read_text("utf-8"))

    def test_review_preserves_scope_read_only_and_reporting(self):
        source = (REVIEW / "SKILL.md").read_text("utf-8")
        for value in ("reviewer → 主模型核验证据 → 输出报告", "不要求 worker",
                      "小范围或普通审查默认一个 reviewer", "普通审查不建 progress",
                      "P0–P3", "COMPLETE", "PARTIAL", "BLOCKED", "只读",
                      "报告默认在聊天中输出", "只有用户明确要求保存时"):
            self.assertIn(value, source)
        self.assertTrue((REVIEW / "scripts/model_validation.py").is_file())
        self.assertTrue((REVIEW / "scripts/select_models.py").is_file())
        for name, native in (("codex", "reasoning_effort"), ("claude", "Agent"),
                             ("agy", "invoke_subagent"), ("dsh", "subagent")):
            adapter = (PLUGIN / "references" / f"{name}.md").read_text("utf-8")
            with self.subTest(harness=name):
                self.assertIn("[子代理模型契约](subagent-models.md)", adapter)
                self.assertIn("dev-review 只要求 reviewer", adapter)
                self.assertIn(native, adapter)
                self.assertIn("BLOCKED", adapter)
                self.assertIn("execution-resources.md", adapter)
                self.assertNotIn("fresh coder", adapter)
                self.assertNotIn("Final Reviewer", adapter)

    def test_codex_example_validates_without_retired_package(self):
        from test_personal_dev_review import REVIEW_MODULE
        source = (PLUGIN / "references/codex.md").read_text("utf-8")
        example = re.search(r"```json\n(.*?)\n```", source, re.S)
        self.assertIsNotNone(example)
        result = REVIEW_MODULE.select_models(json.loads(example[1]))
        self.assertEqual(result["status"], "READY")
        self.assertEqual(set(result), {"status", "reviewer", "display"})
        self.assertEqual(result["reviewer"], {"model": "gpt-6.1-terra", "effort": "high"})

    def test_retained_temporary_paths_are_ignored(self):
        paths = [".personal-dev/tests/fixture/config.json", ".agent-manager/tests/fixture/config.json"]
        result = subprocess.run(["git", "check-ignore", "--", *paths], cwd=ROOT,
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), paths)
        for plugin in (PLUGIN, ROOT / "plugins/agent-manager"):
            for entry in plugin.rglob("SKILL.md"):
                self.assertNotIn(".agent-tmp", entry.read_text("utf-8"))


if __name__ == "__main__":
    unittest.main()
