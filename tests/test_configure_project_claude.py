"""Claude JSON edits reuse the project's transaction and path protections."""
from copy import deepcopy
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

import test_configure_project as common

editor = common.editor


class ClaudeConfigureTests(unittest.TestCase):
    write = common.ConfigureProjectTests.write
    run_editor = common.ConfigureProjectTests.run_editor
    blocked = common.ConfigureProjectTests.blocked
    assert_global_unchanged = common.ConfigureProjectTests.assert_global_unchanged

    def setUp(self):
        self.actual_protected_roots = editor.protected_roots
        common.ConfigureProjectTests.setUp(self)
        self.config = self.project / ".claude/settings.json"
        self.payload["agent"] = "claude"
        self.payload["inventory"]["claude_version"] = editor.VERIFIED_CLAUDE
        self.version_claude = patch.object(editor, "claude_version", return_value=editor.VERIFIED_CLAUDE)
        self.version_claude.start()
        self.addCleanup(self.version_claude.stop)
        for target in self.payload["inventory"]["targets"]:
            if target["kind"] == "plugin":
                target["configuration"] = "marketplace"
                manifest = Path(target["path"]) / ".claude-plugin/plugin.json"
                manifest.parent.mkdir()
                manifest.write_text(json.dumps({"name": target["name"]}), encoding="utf-8")

    def test_minimal_batch_and_idempotence(self):
        self.payload["requests"].append({"kind": "plugin", "target": "beta", "enabled": False})
        report = self.run_editor()
        self.assertEqual(report["Agent"], "Claude Code")
        self.assertEqual(json.loads(self.config.read_bytes()),
                         {"enabledPlugins": {"alpha@fixture": True, "beta@fixture": False}})
        before = self.config.stat().st_mtime_ns
        self.assertEqual(self.run_editor()["Changed"], [])
        self.assertEqual(self.config.stat().st_mtime_ns, before)
        self.assertEqual(list(self.config.parent.iterdir()), [self.config])

    def test_unrelated_bytes_and_switches_preserved(self):
        original = ('{\r\n\t"model" : "fixture",\r\n\t"env": {"text":"escaped \\\" brace }"},\r\n'
                    '\t"enabledPlugins": {"alpha@fixture" : false, "beta@fixture": false},\r\n'
                    '\t"permissions": {"allow":["Read"]}\r\n}\r\n')
        self.write(original)
        self.run_editor()
        self.assertEqual(self.config.read_bytes(), original.replace('"alpha@fixture" : false', '"alpha@fixture" : true').encode())

    def test_new_members_preserve_existing_bytes(self):
        for text in ('{}', '{\r\n  "model": "fixture"\r\n}\r\n',
                     '{"model":"fixture","enabledPlugins":{"beta@fixture":false}}'):
            self.write(text)
            self.run_editor()
            parsed = json.loads(self.config.read_bytes())
            self.assertTrue(parsed["enabledPlugins"]["alpha@fixture"])
            self.assertEqual({key: value for key, value in parsed.items() if key != "enabledPlugins"},
                             {key: value for key, value in json.loads(text).items() if key != "enabledPlugins"})
            if '"model":"fixture"' in text:
                self.assertIn('"model":"fixture"', self.config.read_text(encoding="utf-8"))

    def test_malformed_duplicate_nonfinite_and_invalid_types_block(self):
        for text in ('', '{broken', '[]', '{"enabledPlugins":null}',
                     '{"enabledPlugins":{"alpha@fixture":"false"}}',
                     '{"env": {"key":1,"key":2}}', '{"x":NaN}',
                     '{"enabledPlugins":{},"enabledPlugins":{}}'):
            with self.subTest(text=text):
                self.write(text)
                self.blocked("CONFIG CANNOT BE SAFELY MODIFIED")

    def test_project_local_conflict_blocks_without_modifying_either_file(self):
        self.config.parent.mkdir()
        local = self.config.parent / "settings.local.json"
        original = b'{"enabledPlugins":{"alpha@fixture":false},"model":"fixture"}'
        local.write_bytes(original)
        self.blocked("LOCAL SETTINGS OVERRIDE")
        self.assertEqual(local.read_bytes(), original)
        local.write_text('{"enabledPlugins":{"alpha@fixture":true}}')
        self.run_editor()

    def test_invalid_local_settings_block(self):
        self.config.parent.mkdir()
        (self.config.parent / "settings.local.json").write_text('{"enabledPlugins":7}')
        self.blocked("CONFIG CANNOT BE SAFELY MODIFIED")

    def test_mixed_skill_and_plugin_batch_blocks(self):
        self.payload["requests"].append({"kind": "skill", "target": "vue", "enabled": False})
        self.blocked(editor.UNSUPPORTED_CLAUDE)

    def test_unknown_runtime_and_inactive_layers_block(self):
        for key, value in (("claude_version", "newer"), ("project_config_active", False),
                           ("project_overrides_effective", False)):
            original = self.payload["inventory"][key]
            self.payload["inventory"][key] = value
            self.blocked(editor.UNSUPPORTED_CLAUDE)
            self.payload["inventory"][key] = original
        with patch.object(editor, "claude_version", return_value="newer"):
            self.blocked(editor.UNSUPPORTED_CLAUDE)

    def test_uninstalled_and_invalid_manifest_block(self):
        target = self.payload["inventory"]["targets"][0]
        target["installed"] = False
        self.blocked(editor.UNSUPPORTED_CLAUDE)
        target["installed"] = True
        manifest = Path(target["path"]) / ".claude-plugin/plugin.json"
        manifest.write_text('{"name":"other"}')
        self.blocked("TARGET NOT FOUND")

    def test_duplicate_identity_and_conflicting_requests(self):
        duplicate = deepcopy(self.payload["inventory"]["targets"][0])
        duplicate["id"] = "alpha@other"
        self.payload["inventory"]["targets"].append(duplicate)
        self.blocked("AMBIGUOUS TARGET")
        self.payload["requests"][0]["target"] = "alpha@fixture"
        self.run_editor()
        self.payload["requests"].append({"kind": "plugin", "target": "alpha@fixture", "enabled": False})
        self.blocked("CONFLICTING REQUESTS")

    test_explicit_project_scope_required = common.ConfigureProjectTests.test_explicit_project_scope_required
    test_subdirectory_uses_git_root_and_no_git_environment_spoofing = common.ConfigureProjectTests.test_subdirectory_uses_git_root_and_no_git_environment_spoofing
    test_hardlink_cannot_modify_an_outside_alias = common.ConfigureProjectTests.test_hardlink_cannot_modify_an_outside_alias
    test_symlink_file_outside_and_inside_project_block = common.ConfigureProjectTests.test_symlink_file_outside_and_inside_project_block
    test_windows_junction_to_global_home_is_blocked = common.ConfigureProjectTests.test_windows_junction_to_global_home_is_blocked
    test_replace_failure_leaves_no_partial_or_temp_config = common.ConfigureProjectTests.test_replace_failure_leaves_no_partial_or_temp_config
    test_existing_lock_is_not_deleted_or_overwritten = common.ConfigureProjectTests.test_existing_lock_is_not_deleted_or_overwritten
    test_optimistic_concurrency_prevents_lost_update = common.ConfigureProjectTests.test_optimistic_concurrency_prevents_lost_update
    test_readonly_config_blocked_without_staging_or_permission_changes = common.ConfigureProjectTests.test_readonly_config_blocked_without_staging_or_permission_changes
    test_windows_directory_guard_prevents_parent_swap = common.ConfigureProjectTests.test_windows_directory_guard_prevents_parent_swap

    def test_verification_failure_restores_existing_or_removes_new_json(self):
        for original in (None, '{"model":"original"}\n'):
            if original is not None:
                self.write(original)
            with patch.object(editor, "verify_config", side_effect=editor.Blocked("CONFIG VERIFICATION FAILED")):
                self.blocked("ORIGINAL RESTORED")
            self.assertEqual(self.config.read_text(encoding="utf-8") if self.config.exists() else None, original)

    def test_custom_claude_home_is_protected(self):
        with patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(self.project)}), patch.object(
                editor, "protected_roots", side_effect=self.actual_protected_roots):
            self.blocked("PATH ESCAPES PROJECT ROOT")

    def test_new_entry_keeps_existing_plugin_switch_bytes(self):
        original = '{\n  "enabledPlugins": {\n    "beta@fixture" : false\n  },\n  "model":"fixture"\n}\n'
        self.write(original)
        self.run_editor()
        current = self.config.read_text(encoding="utf-8")
        self.assertIn('"beta@fixture" : false', current)
        self.assertTrue(current.endswith('  },\n  "model":"fixture"\n}\n'))
        self.assertTrue(json.loads(current)["enabledPlugins"]["alpha@fixture"])

    def test_escaped_key_is_changed_without_rewriting_key(self):
        original = '{"enabledPlugins":{"alpha\\u0040fixture":false},"text":"中文"}'
        self.write(original)
        self.run_editor()
        self.assertEqual(self.config.read_text(encoding="utf-8"), original.replace(':false', ':true'))


if __name__ == "__main__":
    unittest.main()
