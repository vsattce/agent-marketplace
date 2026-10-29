"""Desktop synchronization, isolated from the daily DSH profile and model calls."""

import importlib.util
import json
import os
from pathlib import Path
from unittest import mock
import unittest

import yaml

from temp_paths import temporary_test_directory


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".agents/skills/sync-dsh/scripts/sync.py"
SPEC = importlib.util.spec_from_file_location("dsh_sync", SCRIPT)
sync = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sync)


class DesktopSyncTests(unittest.TestCase):
    def setUp(self):
        temporary = temporary_test_directory("dsh-sync")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.repository = self.directory / "repo"
        self.home = self.directory / "dsh-home"
        self.profile = self.home / "profiles/desktop"
        self.profile.mkdir(parents=True)
        (self.profile / "package.json").write_text('{"name":"dsh-profile-desktop"}', encoding="utf-8")
        self.patch = self.profile / "cordis.patch.yml"
        self.original = "# My settings\r\n- id: locale\r\n  config:\r\n    preference: zh\r\n"
        self.patch.write_bytes(self.original.encode())
        self.desktop = self.directory / "DeepSeek Harness.exe"
        self.desktop.write_bytes(b"fixture")
        (self.repository / ".agents/plugins").mkdir(parents=True)
        catalog = {"name": "agent-marketplace", "plugins": [
            {"name": "example", "source": {"source": "local", "path": "./plugins/example"}},
        ]}
        (self.repository / ".agents/plugins/marketplace.json").write_text(json.dumps(catalog), encoding="utf-8")
        self.skill = self.repository / "plugins/example/skills/example/SKILL.md"
        self.skill.parent.mkdir(parents=True)
        self.skill.write_text("---\nname: example\ndescription: 示例\ndisable-model-invocation: true\n---\n"
                              "Read [contract](../../references/contract.md).\n", encoding="utf-8")
        resource = self.repository / "plugins/example/references/contract.md"
        resource.parent.mkdir()
        resource.write_text("Contract", encoding="utf-8")
        codex = self.repository / "plugins/example/codex-skills/am-context/SKILL.md"
        codex.parent.mkdir(parents=True)
        codex.write_text("Codex only", encoding="utf-8")
        self.inspector = mock.patch.object(sync, "inspect", side_effect=self.fake_inspect)
        self.inspector.start()
        self.addCleanup(self.inspector.stop)

    def fake_inspect(self, desktop, roots, home, *, defaults=False):
        entries = []
        for root in [*roots, *([home / "skills"] if defaults else [])]:
            for path in sorted(root.glob("*/SKILL.md")):
                metadata = yaml.safe_load(path.read_text("utf-8").split("---", 2)[1])
                entries.append({"name": metadata["name"], "path": str(path), "invocation": {
                    "modelInvocable": not metadata.get("disable-model-invocation", False),
                    "userInvocable": metadata.get("user-invocable", True),
                }})
        return {"version": "0.2.1-rc.2", "skills": entries}

    def run_sync(self, **options):
        return sync.synchronize(self.repository, self.desktop, self.home, **options)

    def test_check_only_does_not_create_installation_or_change_settings(self):
        result = self.run_sync(check_only=True)
        self.assertEqual((result["plugins"], result["skills"]), (1, 1))
        self.assertEqual(self.patch.read_bytes(), self.original.encode())
        self.assertFalse((self.home / "marketplaces").exists())

    def test_sync_keeps_shared_resources_and_original_settings_and_is_idempotent(self):
        first = self.run_sync()
        release = Path(first["release"])
        installed = release / "plugins/example/skills/example/SKILL.md"
        self.assertEqual(installed.read_bytes(), self.skill.read_bytes())
        self.assertEqual((installed.parent / "../../references/contract.md").resolve().read_text(), "Contract")
        self.assertFalse((release / "plugins/example/codex-skills").exists())
        patch = self.patch.read_bytes()
        self.assertTrue(patch.startswith(self.original.encode()))
        self.assertEqual(patch.count(sync.BEGIN.encode()), 1)
        modified = self.patch.stat().st_mtime_ns
        self.assertEqual(self.run_sync()["release"], first["release"])
        self.assertEqual(self.patch.read_bytes(), patch)
        self.assertEqual(self.patch.stat().st_mtime_ns, modified)

    def test_refresh_uses_new_snapshot_and_keeps_prior_snapshot(self):
        first = self.run_sync()
        self.skill.write_text(self.skill.read_text("utf-8") + "New instruction.\n", encoding="utf-8")
        second = self.run_sync()
        self.assertNotEqual(first["release"], second["release"])
        self.assertTrue(Path(first["release"]).is_dir())
        self.assertIn(Path(second["release"]).as_posix(), self.patch.read_text("utf-8"))
        self.assertNotIn(Path(first["release"]).as_posix(), self.patch.read_text("utf-8"))

    def test_disabled_provider_remains_disabled(self):
        self.run_sync()
        self.patch.write_text(self.patch.read_text().replace("disabled: false", "disabled: true"), encoding="utf-8")
        self.assertFalse(self.run_sync()["enabled"])
        self.assertIn("disabled: true", self.patch.read_text())

    def test_plugin_merge_refreshes_provider_roots_and_preserves_previous_snapshot(self):
        catalog_path = self.repository / ".agents/plugins/marketplace.json"
        catalog = json.loads(catalog_path.read_text("utf-8"))
        catalog["plugins"].append({"name": "testing-automation", "source": {
            "source": "local", "path": "./plugins/testing-automation",
        }})
        catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
        browser = self.repository / "plugins/testing-automation/skills/playwright-cli/SKILL.md"
        browser.parent.mkdir(parents=True)
        browser.write_text("---\nname: playwright-cli\ndescription: Browser automation\n---\nBrowser.\n", encoding="utf-8")
        original = browser.read_bytes()
        first = self.run_sync()
        browser.parent.rename(self.repository / "plugins/example/skills/playwright-cli")
        catalog["plugins"].pop()
        catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
        second = self.run_sync()
        self.assertEqual((first["plugins"], second["plugins"], second["skills"]), (2, 1, 2))
        self.assertNotIn("testing-automation", self.patch.read_text("utf-8"))
        self.assertEqual((Path(first["release"]) / "plugins/testing-automation/skills/playwright-cli/SKILL.md").read_bytes(), original)
        self.assertEqual((Path(second["release"]) / "plugins/example/skills/playwright-cli/SKILL.md").read_bytes(), original)

    def test_user_skill_name_collision_blocks_all_installation(self):
        user_skill = self.home / "skills/example/SKILL.md"
        user_skill.parent.mkdir(parents=True)
        user_skill.write_bytes(self.skill.read_bytes())
        with self.assertRaisesRegex(sync.SyncError, "conflict"):
            self.run_sync()
        self.assertEqual(self.patch.read_bytes(), self.original.encode())
        self.assertFalse((self.home / "marketplaces").exists())

    def test_snapshot_user_edit_is_preserved_and_blocks_refresh(self):
        result = self.run_sync()
        resource = Path(result["release"]) / "plugins/example/references/contract.md"
        resource.write_text("User edit", encoding="utf-8")
        before = self.patch.read_bytes()
        with self.assertRaisesRegex(sync.SyncError, "edited or is incomplete"):
            self.run_sync()
        self.assertEqual(resource.read_text(), "User edit")
        self.assertEqual(self.patch.read_bytes(), before)

    def test_check_only_rejects_modified_snapshot_without_changing_it(self):
        result = self.run_sync()
        resource = Path(result["release"]) / "plugins/example/references/contract.md"
        resource.write_text("User edit", encoding="utf-8")
        before = self.patch.read_bytes()
        with self.assertRaisesRegex(sync.SyncError, "edited or is incomplete"):
            self.run_sync(check_only=True)
        self.assertEqual(resource.read_text(), "User edit")
        self.assertEqual(self.patch.read_bytes(), before)

    def test_interrupted_copy_does_not_publish_partial_snapshot_and_can_retry(self):
        release = Path(self.run_sync(check_only=True)["release"])
        write_bytes = Path.write_bytes

        def interrupted_write(path, content):
            if "releases" in path.parts and path.name == "contract.md":
                raise OSError("simulated copy interruption")
            return write_bytes(path, content)

        with mock.patch.object(Path, "write_bytes", interrupted_write):
            with self.assertRaisesRegex(sync.SyncError, "staging.*retained"):
                self.run_sync()
        self.assertFalse(release.exists())
        self.assertEqual(self.patch.read_bytes(), self.original.encode())
        self.assertTrue(list(release.parent.glob(".stage-*")))
        self.assertEqual(self.run_sync()["release"], str(release))

    def test_nested_user_group_in_managed_block_is_preserved(self):
        result = self.run_sync()
        entries = sync.parse_patch(self.patch.read_text())[1]["insert"]
        group = [{"insert": [{"id": "user-group", "name": "cordis:group", "group": True,
                              "disabled": True, "config": entries}]}]
        changed = sync.BEGIN + "\n" + yaml.safe_dump(group) + sync.END + "\n"
        self.patch.write_text(changed, encoding="utf-8")
        with self.assertRaises(sync.SyncError):
            self.run_sync()
        self.assertEqual(self.patch.read_text(), changed)
        self.assertTrue(Path(result["release"]).exists())

    def test_check_only_rejects_existing_lock_without_removing_it(self):
        destination = self.home / "marketplaces/agent-marketplace"
        destination.mkdir(parents=True)
        lock = destination / ".sync.lock"
        lock.write_text("Other run", encoding="utf-8")
        with self.assertRaisesRegex(sync.SyncError, "Another synchronization"):
            self.run_sync(check_only=True)
        self.assertEqual(lock.read_text(), "Other run")
        self.assertFalse((destination / "releases").exists())

    def test_concurrent_settings_edit_is_preserved(self):
        def change_settings(desktop, roots, home, **options):
            if roots and "releases" in roots[0].parts:
                self.patch.write_text("- id: user-change\n", encoding="utf-8")
            return self.fake_inspect(desktop, roots, home, **options)
        with mock.patch.object(sync, "inspect", side_effect=change_settings):
            with self.assertRaisesRegex(sync.SyncError, "changed during"):
                self.run_sync()
        self.assertEqual(self.patch.read_text(), "- id: user-change\n")

    def test_native_policy_mismatch_blocks_before_writes(self):
        def wrong_policy(desktop, roots, home, **options):
            result = self.fake_inspect(desktop, roots, home, **options)
            for entry in result["skills"]:
                entry["invocation"]["modelInvocable"] = True
            return result
        with mock.patch.object(sync, "inspect", side_effect=wrong_policy):
            with self.assertRaisesRegex(sync.SyncError, "invocation policy"):
                self.run_sync()
        self.assertFalse((self.home / "marketplaces").exists())

    def test_user_entries_inside_managed_block_are_preserved(self):
        self.run_sync()
        changed = self.patch.read_text().replace(sync.END, "- id: my-extra-provider\n" + sync.END)
        self.patch.write_text(changed, encoding="utf-8")
        with self.assertRaisesRegex(sync.SyncError, "contains user entries"):
            self.run_sync()
        self.assertEqual(self.patch.read_text(), changed)

    def test_user_edited_managed_roots_are_preserved(self):
        result = self.run_sync()
        changed = self.patch.read_text().replace(Path(result["release"]).as_posix(), self.home.as_posix())
        self.patch.write_text(changed, encoding="utf-8")
        with self.assertRaisesRegex(sync.SyncError, "roots were edited"):
            self.run_sync()
        self.assertEqual(self.patch.read_text(), changed)

    def test_sync_lock_does_not_remove_other_runs_lock(self):
        destination = self.home / "marketplaces/agent-marketplace"
        destination.mkdir(parents=True)
        lock = destination / ".sync.lock"
        lock.write_text("Other run", encoding="utf-8")
        with self.assertRaisesRegex(sync.SyncError, "Another synchronization"):
            self.run_sync()
        self.assertEqual(lock.read_text(), "Other run")
        self.assertFalse((destination / "releases").exists())

    def test_project_tooling_and_codex_only_skill_are_not_exported(self):
        files, skills = sync.products(ROOT)
        self.assertEqual(len(skills), 30)
        self.assertEqual(len({entry["plugin"] for entry in skills.values()}), 6)
        self.assertEqual(skills["playwright-cli"]["plugin"], "engineering-tools")
        self.assertNotIn("disable-model-invocation", skills["playwright-cli"]["metadata"])
        self.assertIn("plugins/engineering-tools/licenses/playwright-cli/LICENSE", files)
        self.assertIn("plugins/engineering-tools/skills/playwright-cli/references/running-code.md", files)
        self.assertIn("plugins/matt/licenses/setup-matt-pocock-skills/LICENSE", files)
        self.assertIn("plugins/matt/skills/setup-matt-pocock-skills/domain.md", files)
        self.assertFalse(any(name.startswith("plugins/testing-automation/") for name in files))
        self.assertNotIn("am-context", skills)
        self.assertFalse(any(".agents/" in name or "/codex-skills/" in name for name in files))
        for name in ("am-config", "dev-review", "handoff", "grill-with-docs", "improve-codebase-architecture", "setup-matt-pocock-skills"):
            self.assertIs(skills[name]["metadata"]["disable-model-invocation"], True)
        for name in ("grilling", "domain-modeling"):
            self.assertNotIn("disable-model-invocation", skills[name]["metadata"])

    def test_redirected_path_is_rejected(self):
        with mock.patch.object(Path, "is_junction", return_value=True):
            with self.assertRaisesRegex(sync.SyncError, "Redirected"):
                self.run_sync()
        self.assertEqual(self.patch.read_bytes(), self.original.encode())


class DesktopPatchTests(unittest.TestCase):
    def test_inspection_accepts_other_desktop_versions(self):
        payload = {"version": "future-version", "skills": []}
        result = mock.Mock(returncode=0, stdout="DSH_INSPECTION:" + json.dumps(payload), stderr="")
        with mock.patch.object(sync.subprocess, "run", return_value=result):
            self.assertEqual(sync.inspect(Path("desktop"), [], Path("home")), payload)

    def test_empty_sequence_and_expressions_remain_valid(self):
        for original in ("# empty\n[]\n", "- id: untouched\n  disabled: !!js process.platform\n"):
            with self.subTest(original=original):
                proposed, disabled, _ = sync.managed_patch(original, [ROOT / "plugins/software-dev/skills"])
                self.assertFalse(disabled)
                self.assertTrue(sync.parse_patch(proposed))
                if "!!js" in original:
                    self.assertTrue(proposed.startswith(original))

    def test_conflicting_ids_and_broken_markers_are_rejected(self):
        for original in (f"- id: {sync.PROVIDER_ID}\n", sync.BEGIN + "\n", sync.END + "\n"):
            with self.subTest(original=original), self.assertRaises(sync.SyncError):
                sync.managed_patch(original, [])

    def test_owned_entrypoints_reference_the_dsh_adapter(self):
        for source in ("plugins/personal-dev/skills/dev-review/SKILL.md",
                       "plugins/agent-manager/skills/am-config/SKILL.md"):
            self.assertIn("../../references/dsh.md", (ROOT / source).read_text("utf-8"))
        adapter = (ROOT / "plugins/personal-dev/references/dsh.md").read_text("utf-8")
        self.assertIn("spawn 干净上下文", adapter)
        self.assertIn("BLOCKED", adapter)


@unittest.skipUnless(os.environ.get("DSH_DESKTOP_TESTS"), "Set DSH_DESKTOP_TESTS to the installed Desktop executable")
class NativeDesktopTests(unittest.TestCase):
    def test_packaged_provider_loads_all_product_skills_without_host_or_llm(self):
        files, skills = sync.products(ROOT)
        self.assertTrue(files)
        names = sorted({entry["plugin"] for entry in skills.values()})
        with temporary_test_directory("dsh-native") as temporary:
            observed = sync.inspect(Path(os.environ["DSH_DESKTOP_TESTS"]),
                                    [ROOT / "plugins" / name / "skills" for name in names], Path(temporary))
            sync.verify_skills(observed, skills, ROOT)


if __name__ == "__main__":
    unittest.main()
