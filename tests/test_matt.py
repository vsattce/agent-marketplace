"""Selected Matt package, runtime closure and upstream resource contracts."""

import json
from pathlib import Path
import re
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/matt"
SELECTED = {
    "setup-matt-pocock-skills", "grill-with-docs", "grilling", "domain-modeling",
    "to-spec", "to-tickets", "implement", "implement-spec", "tdd", "codebase-design",
    "code-review", "handoff", "diagnosing-bugs", "research",
    "improve-codebase-architecture", "writing-for-agents", "retro",
}
CALLS = {
    "grill-with-docs": {"grilling", "domain-modeling"},
    "implement": {"tdd", "code-review"},
    "implement-spec": {"tdd", "code-review"},
    "tdd": {"codebase-design"},
    "improve-codebase-architecture": {"codebase-design", "grilling", "domain-modeling"},
    "retro": {"writing-for-agents"},
}
RESOURCES = {
    "setup-matt-pocock-skills": {
        "domain.md", "issue-tracker-github.md", "issue-tracker-gitlab.md",
        "issue-tracker-local.md", "triage-labels.md",
    },
    "tdd": {"tests.md", "mocking.md"},
    "codebase-design": {"DEEPENING.md", "DESIGN-IT-TWICE.md"},
    "domain-modeling": {"ADR-FORMAT.md", "GLOSSARY-FORMAT.md"},
    "improve-codebase-architecture": {"HTML-REPORT.md"},
    "writing-for-agents": {"SKILL-MECHANICS.md"},
    "diagnosing-bugs": {"scripts/hitl-loop.template.sh"},
}


def prose(text):
    """Example code links describe generated projects, not bundled files."""
    lines = []
    fence = None
    for line in text.splitlines():
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            if fence is None:
                fence = marker[1][0]
            elif marker[1][0] == fence:
                fence = None
        elif fence is None:
            lines.append(line)
    return "\n".join(lines)


class MattPackagingTests(unittest.TestCase):
    def test_only_selected_skills_and_matching_provenance(self):
        groups = yaml.safe_load((ROOT / "sources.yaml").read_text("utf-8"))["groups"]
        sources = groups["matt"]["skills"]
        lock = json.loads((ROOT / "sources.lock.json").read_text("utf-8"))["skills"]
        self.assertEqual({item["name"] for item in sources}, SELECTED)
        self.assertEqual({path.parent.name for path in (PLUGIN / "skills").glob("*/SKILL.md")}, SELECTED)
        self.assertEqual({item["name"] for item in groups["common-workflow"]["skills"]}, {"find-skills"})
        self.assertEqual({path.name for path in (ROOT / "plugins/common-workflow/skills").iterdir()}, {"find-skills"})
        self.assertEqual(set(lock), {item["name"] for group in groups.values() for item in group["skills"]})
        for source in sources:
            name = source["name"]
            with self.subTest(skill=name):
                category = "productivity" if name in {"grilling", "handoff", "writing-for-agents"} else "engineering"
                self.assertEqual(source, {"name": name, "repo": "mattpocock/skills", "path": f"skills/{category}/{name}", "ref": "main"})
                self.assertEqual({key: lock[name][key] for key in source}, source)
                self.assertEqual(lock[name]["group"], "matt")
                self.assertRegex(lock[name]["commit"], r"^[0-9a-f]{40}$")
                self.assertTrue((PLUGIN / "licenses" / name / "LICENSE").is_file())
        self.assertEqual(len({lock[name]["commit"] for name in SELECTED}), 1)

    def test_runtime_skill_calls_are_available(self):
        for name, dependencies in CALLS.items():
            entry = (PLUGIN / "skills" / name / "SKILL.md").read_text("utf-8")
            for dependency in dependencies:
                with self.subTest(skill=name, dependency=dependency):
                    self.assertIn(dependency, entry)
                    self.assertIn(dependency, SELECTED)
                    metadata = yaml.safe_load((PLUGIN / "skills" / dependency / "SKILL.md").read_text("utf-8").split("---", 2)[1])
                    self.assertFalse(metadata.get("disable-model-invocation", False))
        for name in ("to-spec", "to-tickets", "code-review", "implement-spec"):
            entry = (PLUGIN / "skills" / name / "SKILL.md").read_text("utf-8")
            self.assertIn("/setup-matt-pocock-skills", entry)

    def test_bundled_resources_and_real_relative_links(self):
        for name in SELECTED:
            directory = PLUGIN / "skills" / name
            for relative in {"SKILL.md", "agents/openai.yaml"} | RESOURCES.get(name, set()):
                self.assertTrue((directory / relative).is_file(), (name, relative))
            for document in directory.rglob("*.md"):
                text = prose(document.read_text("utf-8"))
                for target in re.findall(r"\]\(([^)\s]+)\)", text):
                    if "://" in target or target.startswith("#"):
                        continue
                    with self.subTest(document=document.relative_to(PLUGIN), target=target):
                        self.assertTrue((document.parent / target.split("#", 1)[0]).is_file())

    def test_registration_and_default_workflow(self):
        codex = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text("utf-8"))
        claude = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text("utf-8"))
        manifest = json.loads((PLUGIN / "plugin.json").read_text("utf-8"))
        entry = next(item for item in codex["plugins"] if item["name"] == "matt")
        self.assertEqual(entry["source"]["path"], "./plugins/matt")
        self.assertEqual(entry["interface"], manifest["extensions"]["com.openai"]["interface"])
        self.assertEqual(next(item for item in claude["plugins"] if item["name"] == "matt")["source"], "./plugins/matt")
        self.assertTrue((PLUGIN / ".claude-plugin/plugin.json").is_file())
        self.assertFalse((PLUGIN / "references").exists())
        self.assertFalse((PLUGIN / "scripts").exists())
        docs = (ROOT / "docs/usage.md").read_text("utf-8")
        self.assertIn("普通开发（默认） | `$matt:implement`", docs)
        self.assertIn("不作为普通开发默认入口", docs)
        self.assertIn("`retro` 仅手动触发", docs)
        for name in ("retro", "implement", "implement-spec"):
            directory = PLUGIN / "skills" / name
            meta = yaml.safe_load((directory / "SKILL.md").read_text("utf-8").split("---", 2)[1])
            policy = yaml.safe_load((directory / "agents/openai.yaml").read_text("utf-8"))
            self.assertIs(meta["disable-model-invocation"], True)
            self.assertIs(policy["policy"]["allow_implicit_invocation"], False)


if __name__ == "__main__":
    unittest.main()
