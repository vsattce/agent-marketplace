"""Project-only Claude plugin-dev reference snapshot and Codex Skill loading."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import test_codex_loader as codex_loader


rpc_skills = codex_loader.rpc_skills
run = codex_loader.run


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / ".agents" / "plugin-dev" / "upstream"
WRAPPER = ROOT / ".agents" / "skills" / "claude-plugin-dev" / "SKILL.md"
EXPECTED_SNAPSHOT_SHA256 = "7c9386a468deb9cf8280ab5883346a2c1b714b5e72ede798f1613ad6611ceefc"
EXPECTED_EXECUTABLES = (
    "skills/agent-development/scripts/validate-agent.sh",
    "skills/hook-development/examples/load-context.sh",
    "skills/hook-development/examples/validate-bash.sh",
    "skills/hook-development/examples/validate-write.sh",
    "skills/hook-development/scripts/hook-linter.sh",
    "skills/hook-development/scripts/test-hook.sh",
    "skills/hook-development/scripts/validate-hook-schema.sh",
    "skills/plugin-settings/examples/read-settings-hook.sh",
    "skills/plugin-settings/scripts/parse-frontmatter.sh",
    "skills/plugin-settings/scripts/validate-settings.sh",
)


def snapshot_digest(root: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    files = sorted(path for path in root.rglob("*") if path.is_file())
    for path in files:
        relative_path = path.relative_to(root).as_posix()
        digest.update(relative_path.encode("utf-8") + b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return len(files), digest.hexdigest()


class PluginDevSnapshotTests(unittest.TestCase):
    def test_pinned_snapshot_is_complete_and_wrapper_paths_resolve(self):
        source = json.loads((ROOT / ".agents" / "plugin-dev" / "source.json").read_text(encoding="utf-8"))
        self.assertEqual(source, {
            "repository": "https://github.com/anthropics/claude-plugins-official",
            "commit": "a9fd21643fc10eb9c8c8b581902f6259937fa1a4",
            "path": "plugins/plugin-dev",
            "scope": "project-development-tooling",
        })
        self.assertEqual(snapshot_digest(SNAPSHOT), (60, EXPECTED_SNAPSHOT_SHA256))
        self.assertTrue((SNAPSHOT / "LICENSE").is_file())

        references = (
            "skills/plugin-structure/SKILL.md",
            "skills/plugin-structure/references/manifest-reference.md",
            "skills/plugin-structure/README.md",
            ".claude-plugin/plugin.json",
            "commands/create-plugin.md",
            "skills/command-development/SKILL.md",
            "skills/agent-development/SKILL.md",
            "agents/agent-creator.md",
            "agents/plugin-validator.md",
            "agents/skill-reviewer.md",
            "skills/hook-development/SKILL.md",
            "skills/mcp-integration/SKILL.md",
            "skills/plugin-settings/SKILL.md",
            "skills/skill-development/SKILL.md",
        )
        for reference in references:
            with self.subTest(reference=reference):
                self.assertTrue((SNAPSHOT / reference).is_file(), reference)
        for line in WRAPPER.read_text(encoding="utf-8").splitlines():
            if "`" not in line:
                continue
            for candidate in line.split("`")[1::2]:
                if candidate.startswith(("skills/", "commands/", "agents/", ".claude-plugin/")):
                    candidate_path = SNAPSHOT / candidate.rstrip("/")
                    self.assertTrue(candidate_path.exists(), candidate)

    def test_upstream_executable_modes_are_preserved_in_git_index(self):
        paths = [f".agents/plugin-dev/upstream/{relative_path}" for relative_path in EXPECTED_EXECUTABLES]
        result = subprocess.run(
            ["git", "ls-files", "--stage", "--", *paths],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        modes = {}
        for line in result.stdout.splitlines():
            metadata, path = line.split("\t", 1)
            mode, _blob, stage = metadata.split()
            self.assertEqual(stage, "0", path)
            modes[path] = mode
        self.assertEqual(modes, {path: "100755" for path in paths})

    def test_repository_development_tooling_stays_outside_marketplace_sources(self):
        for manifest in (".agents/plugins/marketplace.json", ".claude-plugin/marketplace.json", "kimi.plugin.json"):
            with self.subTest(manifest=manifest):
                self.assertNotIn("claude-plugin-dev", (ROOT / manifest).read_text(encoding="utf-8"))
                self.assertNotIn(".agents/plugin-dev", (ROOT / manifest).read_text(encoding="utf-8"))
        for source_file in ("sources.yaml", "sources.lock.json"):
            with self.subTest(source_file=source_file):
                self.assertNotIn("plugin-dev", (ROOT / source_file).read_text(encoding="utf-8").lower())
        self.assertIn(".agents/plugin-dev/upstream/** -text", (ROOT / ".gitattributes").read_text(encoding="utf-8"))


@unittest.skipUnless(os.environ.get("AGENT_MANAGER_CODEX_TESTS") == "1", "Opt-in isolated Codex loader validation")
class CodexPluginDevLoaderTests(unittest.TestCase):
    def setUp(self):
        # Reuse the repository's existing local API capture fixture and its isolated CODEX_HOME.
        codex_loader.CodexLoaderTests.setUp(self)
        self.external = tempfile.TemporaryDirectory(prefix="codex-plugin-dev-loader-")
        self.addCleanup(self.external.cleanup)
        self.external_root = Path(self.external.name)
        self.project = self.external_root / "project"
        self.project.mkdir()
        self.outside_project = self.external_root / "outside-project"
        self.outside_project.mkdir()
        config_path = self.agent_home / "config.toml"
        config_text = config_path.read_text(encoding="utf-8")
        for project_path in (self.project, self.outside_project):
            config_text += f'\n[projects.{json.dumps(str(project_path))}]\ntrust_level = "trusted"\n'
            run(["git", "init", "--quiet"], self.env, project_path)
        config_path.write_text(config_text, encoding="utf-8")

        project_agents = self.project / ".agents"
        plugin_dev = project_agents / "plugin-dev" / "upstream"
        plugin_dev.parent.mkdir(parents=True)
        shutil.copytree(SNAPSHOT, plugin_dev)
        self.wrapper_dir = project_agents / "skills" / "claude-plugin-dev"

    def test_snapshot_is_not_discovered_but_explicit_project_skill_loads(self):
        snapshot_only, _ = rpc_skills(self.project, self.env)
        self.assertNotIn("claude-plugin-dev", {item.get("name") for item in snapshot_only})

        self.wrapper_dir.mkdir(parents=True)
        shutil.copy2(WRAPPER, self.wrapper_dir / "SKILL.md")
        inventory, _ = rpc_skills(self.project, self.env)
        wrapper_skills = [item for item in inventory if item.get("name") == "claude-plugin-dev"]
        self.assertEqual(len(wrapper_skills), 1)
        loaded_path = wrapper_skills[0].get("path") or wrapper_skills[0].get("filePath")
        self.assertTrue(loaded_path, f"Codex did not report the loaded Skill path: {wrapper_skills[0]}")
        self.assertEqual(Path(loaded_path).resolve(), (self.wrapper_dir / "SKILL.md").resolve())

        outside_inventory, _ = rpc_skills(self.outside_project, self.env)
        self.assertNotIn("claude-plugin-dev", {item.get("name") for item in outside_inventory})

        ordinary_context = codex_loader.CodexLoaderTests.capture(self, "请解释 Vue 中 ref 和 reactive 的区别，不调用任何 Skill。")
        self.assertNotIn("Do not apply generic development workflow Skills automatically.", ordinary_context)
        explicit_context = codex_loader.CodexLoaderTests.capture(self, "$claude-plugin-dev 仅验证项目 Skill 指令注入，本轮不修改文件。")
        self.assertIn("Do not apply generic development workflow Skills automatically.", explicit_context)


if __name__ == "__main__":
    unittest.main()
