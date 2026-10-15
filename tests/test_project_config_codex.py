"""Opt-in native Codex project capability regression. No real user writes."""
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch
import tomlkit

from test_codex_loader import rpc_skills, run
from test_configure_project import editor
from temp_paths import temporary_test_directory

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.environ.get("AGENT_MANAGER_CODEX_TESTS") == "1", "Opt-in isolated Codex loader validation")
class ProjectConfigurationCodexTests(unittest.TestCase):
    def setUp(self):
        self.temporary = temporary_test_directory("codex-project-config")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()
        self.project = self.base / "project"
        self.home = self.base / "codex-home"
        self.skill = self.project / ".agents/skills/probe/SKILL.md"
        self.skill.parent.mkdir(parents=True)
        self.home.mkdir()
        self.skill.write_text("---\nname: probe\ndescription: Native capability fixture\n---\nFixture", encoding="utf-8")
        self.env = {**os.environ, "CODEX_HOME": str(self.home), "GIT_TERMINAL_PROMPT": "0"}
        self.trust = f'[projects.{json.dumps(str(self.project))}]\ntrust_level = "trusted"\n'
        self.user_config = self.home / "config.toml"
        self.user_config.write_text(self.trust, encoding="utf-8")
        run(["git", "init", "--quiet"], self.env, self.project)
        run(["codex", "plugin", "marketplace", "add", str(ROOT), "--json"], self.env, self.project)
        run(["codex", "plugin", "add", "agent-manager@agent-marketplace", "--json"], self.env, self.project)
        self.user_base = self.user_config.read_text(encoding="utf-8")
        self.config = self.project / ".codex/config.toml"
        self.config.parent.mkdir()
        self.assertEqual(run(["codex", "--version"], self.env, self.project).strip(), editor.VERIFIED_CODEX)
        inventory, _ = rpc_skills(self.project, self.env)
        self.plugin_skill = next(item for item in inventory if item["name"] == "agent-manager:am-config")
        plugin_root = Path(self.plugin_skill["path"]).parents[2]
        self.payload = {"agent": "codex", "explicit_invocation": True, "scope": "project",
                        "requests": [{"kind": "plugin", "target": "agent-manager@agent-marketplace", "enabled": False}],
                        "inventory": {"complete": True, "codex_version": editor.VERIFIED_CODEX,
                                      "project_root": str(self.project), "project_config_active": True,
                                      "project_overrides_effective": True,
                                      "targets": [{"kind": "plugin", "id": "agent-manager@agent-marketplace",
                                                   "name": "agent-manager", "path": str(plugin_root),
                                                   "installed": True, "configuration": "local-marketplace"}]}}

    def write_user(self, plugin_enabled=True, skill_path=None, trusted=True):
        # Preserve the fixture's installation/marketplace registration. Replacing
        # those tables would test an unregistered plugin rather than filtering.
        document = tomlkit.parse(self.user_base)
        document["plugins"]["agent-manager@agent-marketplace"]["enabled"] = plugin_enabled
        document["projects"][str(self.project)]["trust_level"] = "trusted" if trusted else "untrusted"
        if skill_path is not None:
            document.add("skills", {"config": [{"path": skill_path, "enabled": False}]})
        self.user_config.write_text(document.as_string(), encoding="utf-8")

    def test_plugin_editor_overrides_user_both_directions_and_reloads(self):
        for enabled in (False, True):
            with self.subTest(enabled=enabled):
                self.write_user(plugin_enabled=not enabled)
                before = self.user_config.read_bytes()
                self.payload["requests"][0]["enabled"] = enabled
                with patch.dict(os.environ, {"CODEX_HOME": str(self.home)}):
                    report = editor.configure(self.payload, self.project)
                self.assertEqual(report["Status"], "SUCCESS")
                inventory, _ = rpc_skills(self.project, self.env)
                present = [item for item in inventory if item["name"].startswith("agent-manager:")]
                self.assertEqual(bool(present), enabled)
                if enabled:
                    self.assertEqual({item["name"] for item in present}, {
                        "agent-manager:am-config", "agent-manager:am-context"})
                self.assertEqual(self.user_config.read_bytes(), before)

    def test_skill_project_fields_are_loaded_but_ignored_and_cannot_override_user(self):
        for path, name in ((str(self.skill), "probe"),
                           (str(self.skill.parent), "probe"),
                           (self.plugin_skill["path"], self.plugin_skill["name"]),
                           (str(Path(self.plugin_skill["path"]).parent), self.plugin_skill["name"])):
            with self.subTest(path=path):
                self.config.write_text(f'[[skills.config]]\npath = {json.dumps(path)}\nenabled = false\n', encoding="utf-8")
                inventory, visible = rpc_skills(self.project, self.env, path)
                self.assertTrue(visible, "Project field is parseable, but this does not prove filtering")
                selected = next(item for item in inventory if item["name"] == name)
                self.assertTrue(selected["enabled"], "Capability changed: audit support gate before proceeding")
        for path, name in ((str(self.skill), "probe"), (self.plugin_skill["path"], self.plugin_skill["name"])):
            with self.subTest(user_disabled=path):
                self.write_user(skill_path=path)
                self.config.write_text(f'[[skills.config]]\npath = {json.dumps(path)}\nenabled = true\n', encoding="utf-8")
                inventory, _ = rpc_skills(self.project, self.env)
                self.assertFalse(next(item for item in inventory if item["name"] == name)["enabled"])

    def test_untrusted_project_plugin_config_not_applied(self):
        self.write_user(trusted=False)
        self.config.write_text('[plugins."agent-manager@agent-marketplace"]\nenabled = false\n', encoding="utf-8")
        inventory, _ = rpc_skills(self.project, self.env)
        self.assertTrue(any(item["name"].startswith("agent-manager:") for item in inventory))


@unittest.skipUnless(os.environ.get("AGENT_MANAGER_CODEX_TESTS") == "1", "Opt-in isolated Codex loader validation")
class ProjectLocalPreparationCodexTests(unittest.TestCase):
    def test_saved_project_catalog_and_switch_do_not_prove_actual_loading(self):
        with temporary_test_directory("codex-project-preparation") as directory:
            base = Path(directory).resolve()
            project = base / "project"
            home = base / "codex-home"
            project.mkdir()
            home.mkdir()
            env = {**os.environ, "CODEX_HOME": str(home), "GIT_TERMINAL_PROMPT": "0",
                   "TMP": str(base), "TEMP": str(base)}
            self.assertEqual(run(["codex", "--version"], env, project).strip(), editor.VERIFIED_CODEX)
            user_config = home / "config.toml"
            user_config.write_text(
                '[features]\nremote_plugin = false\n'
                f'[projects.{json.dumps(str(project))}]\ntrust_level = "trusted"\n', encoding="utf-8")
            run(["git", "init", "--quiet"], env, project)
            plugin = project / "plugins/local-probe"
            (plugin / ".codex-plugin").mkdir(parents=True)
            (plugin / "skills/hello").mkdir(parents=True)
            (plugin / ".codex-plugin/plugin.json").write_text(json.dumps({
                "name": "local-probe", "version": "1.0.0", "skills": "./skills/", "hooks": {}}), encoding="utf-8")
            (plugin / "skills/hello/SKILL.md").write_text(
                "---\nname: hello\ndescription: Isolated project plugin fixture\n---\nFixture", encoding="utf-8")
            catalog = project / ".agents/plugins/marketplace.json"
            catalog.parent.mkdir(parents=True)
            catalog.write_text(json.dumps({"name": "local-probe-marketplace", "plugins": [{
                "name": "local-probe", "source": {"source": "local", "path": "./plugins/local-probe"},
                "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                "category": "Developer Tools"}]}), encoding="utf-8")
            config = project / ".codex/config.toml"
            config.parent.mkdir()
            config.write_text('[plugins."local-probe@local-probe-marketplace"]\nenabled = true\n', encoding="utf-8")
            before = user_config.read_bytes()
            inventory = json.loads(run(["codex", "plugin", "list", "--available", "--json"], env, project))
            listed = inventory["installed"] + inventory["available"]
            self.assertFalse(any(item["name"] == "local-probe" for item in listed),
                             "Discovery capability changed: update the project preparation evidence")
            skills, _ = rpc_skills(project, env)
            self.assertFalse(any(item["name"].startswith("local-probe:") for item in skills),
                             "Loading capability changed: update the project preparation evidence")
            self.assertEqual(user_config.read_bytes(), before)
            self.assertIs(tomlkit.parse(config.read_text(encoding="utf-8"))["plugins"][
                "local-probe@local-probe-marketplace"]["enabled"], True)


if __name__ == "__main__":
    unittest.main()
