"""Transactional project editing, with real Windows path and rollback checks."""
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import tomllib
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins/agent-manager/skills/am-config/scripts/configure_project.py"
spec = importlib.util.spec_from_file_location("configure_project", SCRIPT)
editor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(editor)


class ConfigureProjectTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix=".skill-sync-config-", dir=ROOT)
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()
        self.project = self.base / "project"
        self.project.mkdir()
        subprocess.run(["git", "init", "--quiet", str(self.project)], check=True, capture_output=True)
        self.config = self.project / ".codex/config.toml"
        self.global_home = self.base / "user/.codex"
        self.global_home.mkdir(parents=True)
        (self.global_home / "config.toml").write_text('model = "global fixture"\n', encoding="utf-8")
        self.global_before = (self.global_home / "config.toml").read_bytes()
        self.addCleanup(self.assert_global_unchanged)
        self.version = patch.object(editor, "codex_version", return_value=editor.VERIFIED_CODEX)
        self.version.start()
        self.addCleanup(self.version.stop)
        self.protected = patch.object(editor, "protected_roots", return_value=[self.global_home])
        self.protected.start()
        self.addCleanup(self.protected.stop)
        targets = []
        for name in ("alpha", "beta"):
            plugin = self.global_home / f"plugins/{name}"
            plugin.mkdir(parents=True)
            (plugin / "plugin.json").write_text(json.dumps({"name": name}), encoding="utf-8")
            targets.append({"kind": "plugin", "id": f"{name}@fixture", "name": name,
                            "path": str(plugin), "installed": True, "configuration": "local-marketplace"})
        self.skill = self.project / ".agents/skills/vue/SKILL.md"
        self.skill.parent.mkdir(parents=True)
        self.skill.write_text("---\nname: vue\ndescription: fixture\n---\n", encoding="utf-8")
        targets.append({"kind": "skill", "id": str(self.skill), "name": "vue", "path": str(self.skill)})
        self.payload = {"agent": "codex", "explicit_invocation": True, "scope": "project",
                        "requests": [{"kind": "plugin", "target": "alpha", "enabled": True}],
                        "inventory": {"complete": True, "codex_version": editor.VERIFIED_CODEX,
                                      "project_root": str(self.project), "project_config_active": True,
                                      "project_overrides_effective": True, "targets": targets}}

    def assert_global_unchanged(self):
        self.assertEqual((self.global_home / "config.toml").read_bytes(), self.global_before)

    def write(self, text):
        self.config.parent.mkdir(exist_ok=True)
        self.config.write_bytes(text.encode("utf-8"))

    def run_editor(self):
        return editor.configure(self.payload, self.project)

    def blocked(self, reason):
        before = self.config.read_bytes() if self.config.exists() else None
        directories = sorted(str(path.relative_to(self.project)) for path in self.project.rglob("*") if ".git" not in path.parts)
        with self.assertRaises(editor.Blocked) as caught:
            self.run_editor()
        self.assertIn(reason, caught.exception.reason)
        self.assertEqual(self.config.read_bytes() if self.config.exists() else None, before)
        self.assertEqual(sorted(str(path.relative_to(self.project)) for path in self.project.rglob("*") if ".git" not in path.parts), directories)
        return caught.exception

    def test_minimal_new_config_and_enable_plugin(self):
        report = self.run_editor()
        self.assertEqual(report["Status"], "SUCCESS")
        self.assertEqual(tomllib.loads(self.config.read_text()), {"plugins": {"alpha@fixture": {"enabled": True}}})
        self.assertEqual(list(self.config.parent.iterdir()), [self.config])

    def test_current_and_previously_verified_codex_versions(self):
        for version in ("codex-cli 0.162.0-alpha.2", "codex-cli 0.162.0-alpha.17.2"):
            with self.subTest(version=version), patch.object(editor, "codex_version", return_value=version):
                self.payload["inventory"]["codex_version"] = version
                self.assertEqual(self.run_editor()["Status"], "SUCCESS")

    def test_verified_but_mismatched_codex_version_blocks(self):
        self.payload["inventory"]["codex_version"] = "codex-cli 0.162.0-alpha.2"
        with patch.object(editor, "codex_version", return_value="codex-cli 0.162.0-alpha.17.2"):
            self.blocked("CODEX PROJECT-LEVEL CONFIGURATION NOT SUPPORTED")

    def test_kimi_project_switch_blocks_entire_batch_without_writing(self):
        self.payload["agent"] = "kimi"
        self.payload["requests"].append({"kind": "skill", "target": "vue", "enabled": False})
        self.blocked("KIMI PROJECT-LEVEL CONFIGURATION NOT SUPPORTED")

    def test_disable_plugin_and_idempotence(self):
        self.write('[plugins."alpha@fixture"]\nenabled = true # preserve\n')
        self.payload["requests"][0]["enabled"] = False
        self.run_editor()
        self.assertEqual(self.config.read_bytes(), b'[plugins."alpha@fixture"]\nenabled = false # preserve\n')
        before = self.config.stat().st_mtime_ns
        report = self.run_editor()
        self.assertEqual(report["Changed"], [])
        self.assertEqual(self.config.stat().st_mtime_ns, before)

    def test_batch_enable_and_disable(self):
        self.payload["requests"].append({"kind": "plugin", "target": "beta@fixture", "enabled": False})
        self.run_editor()
        self.assertEqual(tomllib.loads(self.config.read_text())["plugins"],
                         {"alpha@fixture": {"enabled": True}, "beta@fixture": {"enabled": False}})

    def test_unrelated_bytes_comments_model_mcp_profiles_and_skills_preserved(self):
        prefix = '# keep header\r\nmodel = "fixture"\r\n\r\n[mcp_servers.demo]\r\ncommand = "fixture" # keep\r\n\r\n[profiles.special]\r\nmodel = "other"\r\n\r\n[[skills.config]]\r\npath = "/unrelated/SKILL.md"\r\nenabled = false\r\n\r\n'
        suffix = '\r\n[plugins."beta@fixture"]\r\nenabled = false # unrelated\r\n'
        self.write(prefix + '[plugins."alpha@fixture"]\r\nenabled = false # requested\r\n' + suffix)
        self.run_editor()
        self.assertEqual(self.config.read_bytes(), (prefix + '[plugins."alpha@fixture"]\r\nenabled = true # requested\r\n' + suffix).encode())

    def test_new_entry_preserves_unknown_fields_and_multiline_literals(self):
        original = '# header\nmodel = "fixture"\nunknown = """\n[plugins.fake]\nenabled = false\n"""\n[plugins."beta@fixture".mcp_servers.demo]\nenabled = false # retain\n'
        self.write(original)
        self.run_editor()
        current = self.config.read_text()
        self.assertTrue(current.startswith(original))
        self.assertFalse(tomllib.loads(current)["plugins"]["beta@fixture"]["mcp_servers"]["demo"]["enabled"])

    def test_inline_tables_are_incremental(self):
        self.write('model="fixture" # retain\nplugins = {"alpha@fixture" = {enabled = false, extra = 7}} # inline\n')
        self.run_editor()
        self.assertEqual(self.config.read_text(), 'model="fixture" # retain\nplugins = {"alpha@fixture" = {enabled = true, extra = 7}} # inline\n')

    def test_duplicate_short_name_blocks_and_exact_identity_disambiguates(self):
        other = deepcopy(self.payload["inventory"]["targets"][0])
        other["id"] = "alpha@other"
        self.payload["inventory"]["targets"].append(other)
        error = self.blocked("AMBIGUOUS TARGET")
        self.assertEqual(len(error.matches), 2)
        self.payload["requests"][0]["target"] = "alpha@fixture"
        self.run_editor()

    def test_duplicate_skill_sources_block_before_capability_check(self):
        self.payload["inventory"]["targets"].append({"kind": "skill", "id": "frontend:vue", "name": "vue", "path": str(self.global_home / "vue/SKILL.md")})
        self.payload["requests"] = [{"kind": "skill", "target": "vue", "enabled": False}]
        self.blocked("AMBIGUOUS TARGET")

    def test_missing_target_and_valid_plus_invalid_batch_zero_writes(self):
        for requests in ([{"kind": "plugin", "target": "missing", "enabled": True}],
                         self.payload["requests"] + [{"kind": "plugin", "target": "missing", "enabled": True}]):
            with self.subTest(requests=requests):
                self.payload["requests"] = requests
                self.blocked("TARGET NOT FOUND")

    def test_skill_enable_disable_and_mixed_batch_block_on_real_capability(self):
        for state in (True, False):
            for mixed in (False, True):
                with self.subTest(state=state, mixed=mixed):
                    self.payload["requests"] = [{"kind": "skill", "target": "vue", "enabled": state}]
                    if mixed:
                        self.payload["requests"].insert(0, {"kind": "plugin", "target": "alpha", "enabled": True})
                    self.blocked(editor.UNSUPPORTED_CONFIG)

    def test_unsupported_agents(self):
        for agent in ("antigravity", "other", ""):
            self.payload["agent"] = agent
            self.blocked("UNSUPPORTED AGENT")

    def test_explicit_project_scope_required(self):
        self.payload["explicit_invocation"] = False
        self.blocked("USER EXPLICIT REQUEST REQUIRED")
        self.payload["explicit_invocation"] = True
        self.payload["scope"] = "global"
        self.blocked("PROJECT-ONLY CONFIGURATION REQUIRED")
        self.payload["scope"] = "project"
        self.payload["config"] = str(self.global_home / "config.toml")
        self.blocked("PROJECT-ONLY CONFIGURATION REQUIRED")

    def test_not_a_project_no_guessing_or_git_init(self):
        # An internal Git directory is not a worktree/project. All fixtures stay
        # in this repository, so an ordinary child would inherit its Git root.
        outside = self.project / ".git"
        before = sorted(outside.iterdir())
        with self.assertRaisesRegex(editor.Blocked, "PROJECT ROOT NOT FOUND"):
            editor.configure(self.payload, outside)
        self.assertEqual(sorted(outside.iterdir()), before)

    def test_subdirectory_uses_git_root_and_no_git_environment_spoofing(self):
        child = self.project / "nested"
        child.mkdir()
        with patch.dict(os.environ, {"GIT_WORK_TREE": str(self.global_home), "GIT_DIR": str(self.project / ".git")}):
            report = editor.configure(self.payload, child)
        self.assertEqual(report["Project"], str(self.project))

    def test_dotdot_sibling_prefix_and_other_drive_escape(self):
        paths = [self.project / "../escape/config.toml", self.base / "project-sibling/config.toml"]
        if os.name == "nt":
            mounted_drives = {drive[:2].casefold() for drive in os.listdrives()}
            unmounted_drive = next(
                (letter for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if f"{letter}:".casefold() not in mounted_drives),
                None,
            )
            if unmounted_drive is None:
                self.skipTest("No unmounted drive is available for the cross-drive path check")
            paths.append(Path(f"{unmounted_drive}:/outside/config.toml"))
        else:
            paths.append(Path("/outside/config.toml"))
        for path in paths:
            with self.subTest(path=path), self.assertRaisesRegex(editor.Blocked, "PATH ESCAPES PROJECT ROOT"):
                editor.safe_path(path, self.project)

    def test_symlink_file_outside_and_inside_project_block(self):
        self.config.parent.mkdir()
        for target in (self.global_home / "config.toml", self.project / "local.toml"):
            if target.parent == self.project:
                target.write_text("# local", encoding="utf-8")
            try:
                self.config.symlink_to(target)
            except OSError as error:
                self.skipTest(f"Host cannot create symlinks: {error}")
            self.blocked("PATH ESCAPES PROJECT ROOT")
            self.config.unlink()

    @unittest.skipUnless(os.name == "nt", "Windows junction validation")
    def test_windows_junction_to_global_home_is_blocked(self):
        result = subprocess.run(["cmd", "/c", "mklink", "/J", str(self.config.parent), str(self.global_home)], capture_output=True)
        self.assertEqual(result.returncode, 0)
        try:
            self.blocked("PATH ESCAPES PROJECT ROOT")
        finally:
            self.config.parent.rmdir()

    @unittest.skipUnless(os.name == "nt", "Windows case normalization")
    def test_windows_case_normalized_containment(self):
        self.assertEqual(editor.safe_path(Path(str(self.config).upper()), self.project), Path(str(self.config).upper()).resolve())

    def test_hardlink_cannot_modify_an_outside_alias(self):
        self.config.parent.mkdir()
        os.link(self.global_home / "config.toml", self.config)
        self.blocked("CONFIG CANNOT BE SAFELY MODIFIED")

    def test_global_codex_stays_read_only_even_if_git_project(self):
        subprocess.run(["git", "init", "--quiet", str(self.global_home)], check=True, capture_output=True)
        payload = deepcopy(self.payload)
        payload["inventory"]["project_root"] = str(self.global_home)
        with self.assertRaisesRegex(editor.Blocked, "PATH ESCAPES PROJECT ROOT"):
            editor.configure(payload, self.global_home)

    def test_invalid_toml_and_invalid_switch_types_block(self):
        for text in ('model = [broken', '[plugins."alpha@fixture"]\nenabled = "false"', 'plugins = 7'):
            self.write(text)
            self.blocked("CONFIG CANNOT BE SAFELY MODIFIED")

    def test_unknown_version_untrusted_override_and_incomplete_inventory_block(self):
        for key, value in (("codex_version", "unknown"), ("project_config_active", False),
                           ("project_overrides_effective", False), ("complete", False)):
            with self.subTest(key=key):
                original = self.payload["inventory"][key]
                self.payload["inventory"][key] = value
                self.blocked("INCOMPLETE" if key == "complete" else editor.UNSUPPORTED_CONFIG)
                self.payload["inventory"][key] = original
        with patch.object(editor, "codex_version", return_value="codex-cli newer"):
            self.blocked(editor.UNSUPPORTED_CONFIG)

    def test_uninstalled_workspace_managed_and_missing_manifest_block(self):
        target = self.payload["inventory"]["targets"][0]
        target["installed"] = False
        self.blocked(editor.UNSUPPORTED_CONFIG)
        target["installed"] = True
        target["configuration"] = "workspace-managed"
        self.blocked(editor.UNSUPPORTED_CONFIG)
        target["configuration"] = "local-marketplace"
        (Path(target["path"]) / "plugin.json").unlink()
        self.blocked("TARGET NOT FOUND")

    def test_conflicting_requests_block_and_identical_requests_deduplicate(self):
        self.payload["requests"].append({"kind": "plugin", "target": "alpha@fixture", "enabled": False})
        self.blocked("CONFLICTING REQUESTS")
        self.payload["requests"][-1]["enabled"] = True
        report = self.run_editor()
        self.assertEqual(len(report["Changed"]), 1)

    def test_reread_after_write_and_idempotent_reread(self):
        with patch.object(editor, "verify_config", wraps=editor.verify_config) as verify:
            self.run_editor()
            self.assertEqual(verify.call_count, 1)
            self.run_editor()
            self.assertEqual(verify.call_count, 2)

    def test_verification_failure_restores_existing_or_removes_new_config(self):
        for original in (None, '# original\nmodel = "fixture"\n'):
            if original is not None:
                self.write(original)
            with patch.object(editor, "verify_config", side_effect=editor.Blocked("CONFIG VERIFICATION FAILED")):
                self.blocked("ORIGINAL RESTORED")
            self.assertEqual(self.config.read_text() if self.config.exists() else None, original)

    def test_replace_failure_leaves_no_partial_or_temp_config(self):
        with patch.object(editor.os, "replace", side_effect=OSError("fixture")):
            self.blocked("CONFIG WRITE FAILED")

    def test_existing_lock_is_not_deleted_or_overwritten(self):
        self.config.parent.mkdir()
        lock = self.config.parent / ".configure-project.lock"
        lock.write_text("other owner", encoding="utf-8")
        self.blocked("CONFIG WRITE FAILED")
        self.assertEqual(lock.read_text(), "other owner")

    def test_readonly_config_blocked_without_staging_or_permission_changes(self):
        self.write("# read-only\n")
        self.config.chmod(0o444)
        try:
            self.blocked("CONFIG CANNOT BE SAFELY MODIFIED")
        finally:
            self.config.chmod(0o600)

    @unittest.skipUnless(os.name == "nt", "Windows directory handles")
    def test_windows_directory_guard_prevents_parent_swap(self):
        self.config.parent.mkdir()
        with editor.hold_directories(self.config.parent):
            with self.assertRaises(OSError):
                self.config.parent.rename(self.project / "redirected")
        self.assertTrue(self.config.parent.is_dir())

    def test_cli_refuses_to_switch_to_another_project(self):
        result = subprocess.run([os.sys.executable, "-B", str(SCRIPT), "--cwd", str(self.project)],
                                input=json.dumps(self.payload), text=True, capture_output=True, timeout=15, cwd=ROOT)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["Reason"], "PATH ESCAPES PROJECT ROOT")
        self.assertFalse(self.config.exists())

    def test_post_write_concurrent_change_is_reported_honestly(self):
        def failed_verification(path, planned, expected):
            path.write_text("# concurrent writer\n", encoding="utf-8")
            raise editor.Blocked("CONFIG VERIFICATION FAILED")
        with patch.object(editor, "verify_config", side_effect=failed_verification):
            with self.assertRaises(editor.Blocked) as caught:
                self.run_editor()
        self.assertEqual(caught.exception.changes_applied, "UNKNOWN; CHECK PROJECT CONFIG")
        self.assertEqual(self.config.read_text(), "# concurrent writer\n")

    def test_backup_restore_failure_reports_unknown_state(self):
        self.write("# original\n")
        replace = editor.os.replace
        calls = []
        def fail_rollback(source, destination):
            calls.append(destination)
            if len(calls) == 2:
                raise OSError("fixture rollback failure")
            replace(source, destination)
        with patch.object(editor.os, "replace", side_effect=fail_rollback):
            with patch.object(editor, "verify_config", side_effect=editor.Blocked("CONFIG VERIFICATION FAILED")):
                with self.assertRaises(editor.Blocked) as caught:
                    self.run_editor()
        self.assertEqual(caught.exception.changes_applied, "UNKNOWN; CHECK PROJECT CONFIG")
        self.assertEqual(list(self.config.parent.iterdir()), [self.config])

    def test_optimistic_concurrency_prevents_lost_update(self):
        planned, expected = editor.CodexAdapter().plan(b"", [{**self.payload["inventory"]["targets"][0], "enabled": True}])
        self.write("# concurrent\n")
        with self.assertRaisesRegex(editor.Blocked, "CONFIG CHANGED CONCURRENTLY"):
            editor.publish(self.project, self.config, None, planned, expected)
        self.assertEqual(self.config.read_text(), "# concurrent\n")

    def test_cli_structured_blocked_report(self):
        result = subprocess.run([os.sys.executable, "-B", str(SCRIPT), "--cwd", str(self.project)],
                                input=json.dumps({**self.payload, "agent": "kimi"}),
                                text=True, capture_output=True, timeout=15, cwd=self.project)
        self.assertEqual(result.returncode, 2)
        report = json.loads(result.stdout)
        self.assertEqual(report["Reason"], "KIMI PROJECT-LEVEL CONFIGURATION NOT SUPPORTED")
        self.assertEqual(report["Changes applied"], "NONE")
        self.assertEqual(report["Global files modified"], "NONE")


if __name__ == "__main__":
    unittest.main()
