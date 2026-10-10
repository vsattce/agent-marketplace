"""Management safety boundaries and recorded-upstream comparisons."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/agent-manager"


def load_module(name, relative):
    spec = importlib.util.spec_from_file_location(name, PLUGIN / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


config = load_module("project_config", "skills/resolve-conflicts/scripts/project_config.py")
with patch.dict(sys.modules, {"project_config": config}):
    probe = load_module("safe_probe", "skills/resolve-conflicts/scripts/probe_codex.py")
updates = load_module("check_sources", "skills/check-updates/scripts/check_sources.py")


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "project"
        self.root.mkdir()
        (self.root / "package.json").write_text('{}', encoding="utf-8")
        # The editor must bind to the invocation cwd, not trust a passed root.
        self.cwd = patch.object(Path, "cwd", return_value=self.root)
        self.cwd.start()
        self.addCleanup(self.cwd.stop)
        self.agent_home = Path(self.temporary.name) / "agent-home"
        self.agent_home.mkdir()
        (self.agent_home / "config.toml").write_text('model = "preserve-global"\n', encoding="utf-8")
        self.environment = patch.dict(os.environ, {"CODEX_HOME": str(self.agent_home)})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.target = self.root / ".codex/config.toml"

    def write_config(self, text):
        self.target.parent.mkdir(exist_ok=True)
        self.target.write_bytes(text.encode("utf-8"))

    def test_incremental_plugin_and_skill_override_preserve_unrelated_values(self):
        original = ('# Keep this comment\r\nmodel = "original"\r\n'
                    'approval_policy = "never"\r\nsandbox_mode = "workspace-write"\r\n'
                    '[profiles.work]\r\nmodel = "profile-model"\r\n'
                    '[mcp_servers.docs]\r\ncommand = "unchanged"\r\n'
                    '[plugins."other@market"]\r\nenabled = true # Keep inline comment\r\n')
        self.write_config(original)
        global_before = (self.agent_home / "config.toml").read_bytes()
        skill = self.root / "skill/SKILL.md"
        skill.parent.mkdir()
        skill.write_text("test", encoding="utf-8")
        self.assertTrue(config.edit_config(self.root, plugin_updates={"loser@market": False}, skill_updates={str(skill): False}))
        after = self.target.read_bytes()
        self.assertTrue(after.startswith(original.encode("utf-8")))
        parsed = tomllib.loads(after.decode("utf-8"))
        self.assertFalse(parsed["plugins"]["loser@market"]["enabled"])
        self.assertEqual(parsed["skills"]["config"], [{"path": str(skill), "enabled": False}])
        self.assertEqual(global_before, (self.agent_home / "config.toml").read_bytes())
        self.assertFalse(config.edit_config(self.root, plugin_updates={"loser@market": False}, skill_updates={str(skill): False}))

    def test_existing_override_keeps_comments_and_metadata(self):
        self.write_config('[plugins."loser@market"]\nenabled = true # why\n[plugins."loser@market".mcp_servers.docs]\nenabled = false\n')
        config.edit_config(self.root, plugin_updates={"loser@market": False})
        self.assertIn('enabled = false # why', self.target.read_text(encoding="utf-8"))
        self.assertFalse(tomllib.loads(self.target.read_text())["plugins"]["loser@market"]["mcp_servers"]["docs"]["enabled"])

    def test_project_internal_directory_is_supported(self):
        nested = self.root / "src/feature"
        nested.mkdir(parents=True)
        self.assertEqual(config.project_root(nested), self.root.resolve())

    def test_non_project_and_user_global_rejected(self):
        empty = Path(self.temporary.name) / "empty"
        empty.mkdir()
        for path in (empty, self.agent_home):
            with self.subTest(path=path), self.assertRaises(config.Blocked):
                config.project_root(path)
        with self.assertRaises(config.Blocked):
            config.edit_config(self.agent_home, plugin_updates={"loser@market": False})

    def test_invalid_toml_is_not_modified(self):
        self.write_config('model = [invalid')
        before = self.target.read_bytes()
        with self.assertRaises(config.Blocked):
            config.edit_config(self.root, plugin_updates={"loser@market": False})
        self.assertEqual(before, self.target.read_bytes())

    def test_symlink_config_rejected(self):
        self.target.parent.mkdir()
        try:
            self.target.symlink_to(self.agent_home / "config.toml")
        except OSError:
            self.skipTest("Host does not permit symlink creation")
        with self.assertRaises(config.Blocked):
            config.edit_config(self.root, plugin_updates={"loser@market": False})

    def test_external_write_targets_are_rejected(self):
        other = Path(self.temporary.name) / "project-other"
        other.mkdir()
        subprocess.run(["git", "init", "--quiet", str(other)], check=True,
                       capture_output=True, timeout=10)
        home = Path.home()
        targets = [
            home / ".codex/config.toml", home / ".codex/skills",
            home / ".agents/skills", home / ".claude/config.json",
            home / ".config/agent", self.agent_home / "plugins/cache/example",
            other / ".codex/config.toml", self.root / "../project-other/config.toml",
        ]
        for target in targets:
            with self.subTest(target=target), self.assertRaisesRegex(config.Blocked, "outside project root"):
                config.write_path(self.root, target)
        with self.assertRaisesRegex(config.Blocked, "outside project root"):
            config.edit_config(other, plugin_updates={"loser@market": False})
        self.assertFalse((other / ".codex").exists())

    def test_external_selector_is_read_only_and_preserves_plugin_siblings(self):
        plugin = self.agent_home / "plugins/cache/example"
        for name in ("handoff", "research", "diagnostics"):
            skill = plugin / "skills" / name / "SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text(f"---\nname: {name}\ndescription: fixture\n---\n", encoding="utf-8")
        selector = plugin / "skills/handoff/SKILL.md"
        before = {str(path): path.read_bytes() for path in self.agent_home.rglob("*") if path.is_file()}
        self.assertTrue(config.edit_config(self.root, skill_updates={str(selector): False}))
        parsed = tomllib.loads(self.target.read_text(encoding="utf-8"))
        self.assertEqual(parsed["skills"]["config"], [{"path": str(selector), "enabled": False}])
        self.assertNotIn("plugins", parsed)
        self.assertEqual(before, {str(path): path.read_bytes() for path in self.agent_home.rglob("*") if path.is_file()})

    def test_redirected_directory_cannot_write_or_clean_external_config(self):
        before = (self.agent_home / "config.toml").read_bytes()
        if os.name == "nt":
            subprocess.run(["cmd", "/c", "mklink", "/J", str(self.target.parent), str(self.agent_home)],
                           check=True, capture_output=True, timeout=10)
        else:
            self.target.parent.symlink_to(self.agent_home, target_is_directory=True)
        with self.assertRaisesRegex(config.Blocked, "outside project root"):
            config.edit_config(self.root, plugin_updates={"loser@market": False})
        self.assertEqual(before, (self.agent_home / "config.toml").read_bytes())
        self.assertEqual({path.name for path in self.agent_home.iterdir()}, {"config.toml"})

    def test_hardlinked_config_is_rejected(self):
        self.target.parent.mkdir()
        os.link(self.agent_home / "config.toml", self.target)
        before = self.target.read_bytes()
        with self.assertRaisesRegex(config.Blocked, "hardlinked"):
            config.edit_config(self.root, plugin_updates={"loser@market": False})
        self.assertEqual(before, self.target.read_bytes())
        self.assertEqual(before, (self.agent_home / "config.toml").read_bytes())

    def test_windows_case_and_drive_boundaries(self):
        if os.name != "nt":
            self.skipTest("Windows path semantics")
        target = Path(str(self.root).swapcase()) / ".codex/config.toml"
        self.assertEqual(config.write_path(self.root, target), target)
        drive = "Z:" if self.root.drive.upper() != "Z:" else "Y:"
        with self.assertRaisesRegex(config.Blocked, "outside project root"):
            config.write_path(self.root, Path(drive + "/external/config.toml"))

    def test_global_directory_cannot_become_project_via_markers(self):
        skill = self.agent_home / "skills/example"
        skill.mkdir(parents=True)
        (skill / "package.json").write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(config.Blocked, "can only run inside a project"):
            config.project_root(skill)

    def test_unconfined_runtime_probe_is_blocked_without_writes(self):
        before = {str(path): path.read_bytes() for path in self.agent_home.rglob("*") if path.is_file()}
        # Global metadata is readable; verification must not install/copy/delete
        # anything or start Codex, even under a disposable CODEX_HOME.
        with (patch("subprocess.Popen", side_effect=AssertionError("Unexpected process")),
              patch("tempfile.TemporaryDirectory", side_effect=AssertionError("Unexpected temporary directory")),
              patch.object(Path, "write_text", side_effect=AssertionError("Unexpected write")),
              patch.object(Path, "unlink", side_effect=AssertionError("Unexpected cleanup")),
              patch.object(config.subprocess, "run", return_value=None)):
            result = probe.probe(ROOT / "plugins/common-workflow", "handoff")
        self.assertEqual(result["Status"], "BLOCKED")
        self.assertTrue(result["ReadOnlyPreflight"])
        self.assertIn("project-only process confinement", result["Reason"])
        self.assertFalse(self.target.parent.exists())
        self.assertEqual(before, {str(path): path.read_bytes() for path in self.agent_home.rglob("*") if path.is_file()})

    def test_non_project_probe_does_not_create_configuration(self):
        empty = Path(self.temporary.name) / "empty"
        empty.mkdir()
        with patch.object(Path, "cwd", return_value=empty), self.assertRaisesRegex(config.Blocked, "can only run inside a project"):
            probe.probe(ROOT / "plugins/common-workflow", "handoff")
        self.assertEqual(list(empty.iterdir()), [])

    def test_partial_plugin_conflict_is_blocked(self):
        # Real common-workflow exposes five capabilities; handoff alone cannot
        # justify disabling the whole Plugin.
        with self.assertRaisesRegex(config.Blocked, "unrelated Skills"):
            config.plugin_disable_update("common-workflow@agent-marketplace", ROOT / "plugins/common-workflow", {"handoff"})

    def test_single_skill_plugin_can_be_disabled(self):
        update = config.plugin_disable_update("backend-dev@agent-marketplace", ROOT / "plugins/backend-dev", {"java-spring-boot"})
        self.assertEqual(update, {"backend-dev@agent-marketplace": False})

    def test_extra_capabilities_block_plugin_disable(self):
        plugin = self.root / "plugin"
        skill = plugin / "skills/handoff"
        skill.mkdir(parents=True)
        (plugin / "plugin.json").write_text('{"name":"example"}', encoding="utf-8")
        (skill / "SKILL.md").write_text('---\nname: handoff\ndescription: test\n---\n', encoding="utf-8")
        (plugin / "mcp.json").write_text('{}', encoding="utf-8")
        with self.assertRaisesRegex(config.Blocked, "additional"):
            config.plugin_disable_update("example@market", plugin, {"handoff"})


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.current = "a" * 40
        self.remote = "b" * 40
        self.sources = [{"name": name, "repo": "owner/repo", "path": f"skills/{name}", "ref": "main"} for name in ("alpha", "beta")]
        self.records = {source["name"]: {**source, "group": "common-workflow", "commit": self.current} for source in self.sources}
        self.write_files()
        self.calls = []

    def write_files(self):
        (self.root / "sources.yaml").write_text(yaml.safe_dump({"groups": {"common-workflow": {"skills": self.sources}}}), encoding="utf-8")
        (self.root / "sources.lock.json").write_text(json.dumps({"skills": self.records}), encoding="utf-8")

    def query(self, url):
        self.calls.append(url)
        return {"sha": self.remote} if "/commits/" in url else [{"name": "SKILL.md", "type": "file"}]

    def test_comparison_is_read_only_and_deduplicates_ref(self):
        before = {path.name: path.read_bytes() for path in self.root.iterdir()}
        rows = updates.check_sources(self.root, self.query)
        self.assertEqual([row["Status"] for row in rows], ["UPDATE AVAILABLE"] * 2)
        self.assertEqual(len([url for url in self.calls if "/commits/" in url]), 1)
        self.assertEqual(before, {path.name: path.read_bytes() for path in self.root.iterdir()})
        self.remote = self.current
        self.assertTrue(all(row["Status"] == "LATEST" for row in updates.check_sources(self.root, self.query)))

    def test_fixed_sha_does_not_follow_main(self):
        self.sources[0]["ref"] = self.current
        self.records["alpha"]["ref"] = self.current
        self.write_files()
        def query(url):
            self.calls.append(url)
            return {"sha": self.current if url.endswith(self.current) else self.remote} if "/commits/" in url else [{"name": "SKILL.md", "type": "file"}]
        rows = updates.check_sources(self.root, query)
        self.assertEqual(rows[0]["Status"], "LATEST")
        self.assertEqual(rows[1]["Status"], "UPDATE AVAILABLE")

    def test_missing_path_and_network_failure_are_distinct(self):
        def query(url):
            if "/contents/skills/alpha?" in url:
                raise updates.Unknown("GitHub HTTP 404")
            if "/contents/" in url:
                raise updates.Unknown("GitHub HTTP 403")
            return {"sha": self.remote}
        rows = updates.check_sources(self.root, query)
        self.assertEqual([row["Status"] for row in rows], ["UPSTREAM PATH MISSING", "UNKNOWN"])

    def test_repo_or_ref_not_found_is_unknown(self):
        def query(url):
            raise updates.Unknown("GitHub HTTP 404")
        self.assertTrue(all(row["Status"] == "UNKNOWN" for row in updates.check_sources(self.root, query)))

    def test_source_change_cannot_be_compared_with_old_lock(self):
        self.records["alpha"]["repo"] = "old/source"
        self.write_files()
        rows = updates.check_sources(self.root, self.query)
        self.assertEqual(rows[0]["Status"], "UNKNOWN")
        self.assertIn("identity", rows[0]["Reason"])


class PackagingTests(unittest.TestCase):
    def test_manual_only_metadata_and_marketplace_registration(self):
        catalog = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
        entries = [entry for entry in catalog["plugins"] if entry["name"] == "agent-manager"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["source"]["path"], "./plugins/agent-manager")
        skills = list((PLUGIN / "skills").iterdir())
        self.assertEqual({skill.name for skill in skills}, {"resolve-conflicts", "check-updates"})
        for skill in skills:
            policy = yaml.safe_load((skill / "agents/openai.yaml").read_text(encoding="utf-8"))
            self.assertIs(policy["policy"]["allow_implicit_invocation"], False)
            text = (skill / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("Only use when explicitly invoked by the user.", text)
        sources = yaml.safe_load((ROOT / "sources.yaml").read_text(encoding="utf-8"))
        self.assertNotIn("agent-manager", sources["groups"])
        lock = json.loads((ROOT / "sources.lock.json").read_text(encoding="utf-8"))
        self.assertNotIn("agent-manager", {item["group"] for item in lock["skills"].values()})


if __name__ == "__main__":
    unittest.main()
