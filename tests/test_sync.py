"""Focused checks for snapshot updates and preserving files on failure."""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import yaml

SPEC = importlib.util.spec_from_file_location("skill_sync", Path(__file__).parents[1] / "scripts" / "sync.py")
skill_sync = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(skill_sync)


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "marketplace"
        self.root.mkdir()
        plugin = self.root / "plugins" / "common-workflow"
        plugin.mkdir(parents=True)
        (plugin / "plugin.json").write_text('{"name":"common-workflow"}', encoding="utf-8")
        self.upstream = Path(self.temporary.name) / "upstream"
        self.upstream.mkdir()
        (self.upstream / "LICENSE").write_text("upstream license\n", encoding="utf-8")
        self.write_skill("alpha")
        self.sources = [{"name": "alpha", "repo": "example/skills", "path": "skills/alpha", "ref": "main"}]
        self.write_sources()
        self.commit = "a" * 40
        self.fetch = patch.object(skill_sync, "fetch", side_effect=lambda *args: (self.upstream, self.commit))
        self.mock_fetch = self.fetch.start()
        self.addCleanup(self.fetch.stop)

    def write_sources(self):
        document = {"groups": {"common-workflow": {"displayName": "通用工作流", "skills": self.sources}}}
        (self.root / "sources.yaml").write_text(yaml.safe_dump(document, allow_unicode=True), encoding="utf-8")

    def write_skill(self, name):
        path = self.upstream / "skills" / name
        path.mkdir(parents=True, exist_ok=True)
        (path / "SKILL.md").write_text(f"---\nname: {name}\ndescription: Test skill\n---\nInstructions\n", encoding="utf-8", newline="\n")
        return path

    def run_sync(self):
        with contextlib.redirect_stdout(io.StringIO()):
            skill_sync.sync(self.root)

    def snapshot(self):
        return {path.relative_to(self.root).as_posix(): path.read_bytes() for path in self.root.rglob("*") if path.is_file()}

    def test_updates_latest_content_and_preserves_licenses(self):
        asset = self.upstream / "skills" / "alpha" / "old.txt"
        asset.write_text("old", encoding="utf-8")
        self.run_sync()
        asset.unlink()
        entry = self.upstream / "skills" / "alpha" / "SKILL.md"
        entry.write_text(entry.read_text(encoding="utf-8") + "New instructions\n", encoding="utf-8")
        self.commit = "b" * 40
        self.run_sync()
        target = self.root / "plugins" / "common-workflow" / "skills" / "alpha"
        self.assertFalse((target / "old.txt").exists())
        self.assertEqual((target / "SKILL.md").read_bytes(), entry.read_bytes())
        self.assertEqual((self.root / "plugins/common-workflow/licenses/alpha/LICENSE").read_bytes(), (self.upstream / "LICENSE").read_bytes())
        self.assertEqual(json.loads((self.root / "sources.lock.json").read_text())["skills"]["alpha"]["commit"], self.commit)

    def test_engineering_tools_updates_idempotently_and_restores_failed_publish(self):
        plugin = self.root / "plugins" / "engineering-tools"
        plugin.mkdir(parents=True)
        (plugin / "plugin.json").write_text('{"name":"engineering-tools"}', encoding="utf-8")
        self.write_skill("docker-build-strategies")
        asset = self.upstream / "skills" / "docker-build-strategies" / "references" / "build.bin"
        asset.parent.mkdir(parents=True)
        asset.write_bytes(b"\x00\xff\r\n")
        notice = self.upstream / "NOTICE"
        notice.write_bytes(b"Copyright\r\n\x00")
        document = {
            "groups": {
                "common-workflow": {"displayName": "通用工作流", "skills": self.sources},
                "engineering-tools": {
                    "displayName": "工程工具",
                    "skills": [{
                        "name": "docker-build-strategies",
                        "repo": "docker/skills",
                        "path": "skills/docker-build-strategies",
                        "ref": "main",
                    }],
                },
            },
        }
        (self.root / "sources.yaml").write_text(yaml.safe_dump(document, allow_unicode=True), encoding="utf-8")

        self.run_sync()
        skill_target = plugin / "skills" / "docker-build-strategies"
        license_target = plugin / "licenses" / "docker-build-strategies"
        self.assertEqual((skill_target / "references/build.bin").read_bytes(), asset.read_bytes())
        self.assertEqual((license_target / "LICENSE").read_bytes(), (self.upstream / "LICENSE").read_bytes())
        self.assertEqual((license_target / "NOTICE").read_bytes(), notice.read_bytes())
        lock_before = json.loads((self.root / "sources.lock.json").read_text(encoding="utf-8"))
        self.assertEqual(lock_before["skills"]["docker-build-strategies"]["group"], "engineering-tools")
        before = self.snapshot()
        self.run_sync()
        self.assertEqual(before, self.snapshot())

        entry = self.upstream / "skills" / "docker-build-strategies" / "SKILL.md"
        entry.write_bytes(entry.read_bytes() + b"Updated upstream\n")
        self.commit = "b" * 40
        original_replace = Path.replace

        def fail_lock_replace(path, target):
            if path.name == "sources.lock.json" and path.parent.name.startswith(".skill-sync-"):
                raise OSError("simulated write failure")
            return original_replace(path, target)

        with patch.object(Path, "replace", fail_lock_replace), self.assertRaises(OSError):
            self.run_sync()
        self.assertEqual(before, self.snapshot())

        self.run_sync()
        self.assertEqual((skill_target / "SKILL.md").read_bytes(), entry.read_bytes())
        updated_lock = json.loads((self.root / "sources.lock.json").read_text(encoding="utf-8"))
        self.assertEqual(updated_lock["skills"]["docker-build-strategies"]["commit"], self.commit)

    def test_sync_does_not_generate_kimi_installable_manifests(self):
        self.run_sync()
        self.assertTrue((self.root / "plugins/common-workflow/skills/alpha/SKILL.md").is_file())
        for relative in (
            "kimi.plugin.json",
            ".agents/plugins/marketplace.json",
            ".claude-plugin/marketplace.json",
            "plugins/common-workflow/kimi.plugin.json",
        ):
            self.assertFalse((self.root / relative).exists(), relative)

    def test_same_commit_is_idempotent_and_repairs_local_snapshot(self):
        self.run_sync()
        before = self.snapshot()
        self.run_sync()
        self.assertEqual(before, self.snapshot())
        target = self.root / "plugins/common-workflow/skills/alpha/SKILL.md"
        target.write_text("local edit", encoding="utf-8")
        self.run_sync()
        self.assertEqual(target.read_bytes(), (self.upstream / "skills/alpha/SKILL.md").read_bytes())

    def test_all_sources_validated_before_writes(self):
        self.run_sync()
        self.sources.append({"name": "missing", "repo": "example/skills", "path": "skills/missing", "ref": "main"})
        self.write_sources()
        before = self.snapshot()
        self.commit = "b" * 40
        with self.assertRaises(skill_sync.SyncError):
            self.run_sync()
        self.assertEqual(before, self.snapshot())

    def test_fetch_failure_preserves_snapshots_and_lock(self):
        self.run_sync()
        before = self.snapshot()
        self.mock_fetch.side_effect = skill_sync.SyncError("network unavailable")
        with self.assertRaises(skill_sync.SyncError):
            self.run_sync()
        self.assertEqual(before, self.snapshot())

    def test_unlisted_skills_are_not_deleted(self):
        self.sources.append({"name": "beta", "repo": "example/skills", "path": "skills/beta", "ref": "main"})
        self.write_skill("beta")
        self.write_sources()
        self.run_sync()
        self.assertEqual(self.mock_fetch.call_count, 1)
        self.sources.pop()
        self.write_sources()
        self.run_sync()
        self.assertTrue((self.root / "plugins/common-workflow/skills/beta/SKILL.md").exists())
        self.assertIn("beta", json.loads((self.root / "sources.lock.json").read_text())["skills"])

    def test_invalid_sources_fail_before_fetch(self):
        for field, value in [("path", "../outside"), ("path", "/outside"), ("repo", "https://github.com/example/skills"), ("ref", "--upload-pack=anything")]:
            with self.subTest(field=field):
                original = self.sources[0][field]
                self.sources[0][field] = value
                self.write_sources()
                with self.assertRaises(skill_sync.SyncError):
                    self.run_sync()
                self.sources[0][field] = original
        self.assertEqual(self.mock_fetch.call_count, 0)

    def test_duplicate_source_mapping_keys_fail_before_fetch_or_publish(self):
        cases = {
            "repeated group": """groups:
  common-workflow:
    displayName: First
    skills:
      - name: alpha
        repo: owner/repo
        path: skills/alpha
        ref: main
  common-workflow:
    displayName: Second
    skills:
      - name: alpha
        repo: owner/repo
        path: skills/alpha
        ref: main
""",
            "nested source key": """groups:
  common-workflow:
    displayName: Test
    skills:
      - name: alpha
        repo: private-source-value/repo
        repo: owner/repo
        path: skills/alpha
        ref: main
""",
        }
        for label, text in cases.items():
            with self.subTest(label=label):
                (self.root / "sources.yaml").write_text(text, encoding="utf-8")
                before = self.snapshot()
                with patch.object(skill_sync, "publish", wraps=skill_sync.publish) as publish:
                    with self.assertRaises(skill_sync.SyncError) as caught:
                        self.run_sync()
                self.assertNotIn("private-source-value", str(caught.exception))
                self.assertEqual(self.mock_fetch.call_count, 0)
                publish.assert_not_called()
                self.assertEqual(before, self.snapshot())

    def test_yaml_merge_override_remains_valid(self):
        (self.root / "sources.yaml").write_text("""groups:
  common-workflow:
    <<: &defaults
      displayName: &default_name Default name
      skills:
        - name: beta
          repo: owner/repo
          path: skills/beta
          ref: main
    displayName: *default_name
    skills:
      - name: alpha
        repo: example/skills
        path: skills/alpha
        ref: main
""", encoding="utf-8")
        self.run_sync()
        self.assertTrue((self.root / "plugins/common-workflow/skills/alpha/SKILL.md").is_file())
        self.assertFalse((self.root / "plugins/common-workflow/skills/beta").exists())
        self.assertEqual(self.mock_fetch.call_count, 1)

    def test_yaml_merge_sequence_keeps_first_mapping_precedence(self):
        self.write_skill("beta")
        (self.root / "sources.yaml").write_text("""groups:
  common-workflow:
    <<: [
      {displayName: Selected, skills: [{name: beta, repo: owner/repo, path: skills/beta, ref: main}]},
      {displayName: '', skills: [{name: alpha, repo: owner/repo, path: skills/alpha, ref: main}]}
    ]
""", encoding="utf-8")
        self.run_sync()
        self.assertTrue((self.root / "plugins/common-workflow/skills/beta/SKILL.md").is_file())
        self.assertFalse((self.root / "plugins/common-workflow/skills/alpha").exists())

    def test_duplicate_keys_inside_merge_source_fail_before_fetch_or_publish(self):
        cases = {
            "duplicate key in merge source": """groups:
  common-workflow:
    <<: {displayName: First, displayName: private-source-value}
    skills:
      - name: alpha
        repo: owner/repo
        path: skills/alpha
        ref: main
""",
            "repeated merge key": """groups:
  common-workflow:
    <<: {displayName: First, skills: [{name: alpha, repo: owner/repo, path: skills/alpha, ref: main}]}
    <<: {displayName: Second, skills: [{name: alpha, repo: owner/repo, path: skills/alpha, ref: main}]}
""",
        }
        for label, text in cases.items():
            with self.subTest(label=label):
                self.mock_fetch.reset_mock()
                (self.root / "sources.yaml").write_text(text, encoding="utf-8")
                before = self.snapshot()
                with patch.object(skill_sync, "publish", wraps=skill_sync.publish) as publish:
                    with self.assertRaises(skill_sync.SyncError) as caught:
                        self.run_sync()
                self.assertNotIn("private-source-value", str(caught.exception))
                self.assertEqual(self.mock_fetch.call_count, 0)
                publish.assert_not_called()
                self.assertEqual(before, self.snapshot())

    def test_duplicate_lock_object_keys_fail_before_fetch_or_publish(self):
        cases = {
            "nested record key": '{"skills":{"alpha":{"group":"private-lock-value","group":"common-workflow"}}}',
            "skill identity key": '{"skills":{"alpha":{"group":"common-workflow"},"alpha":{"group":"common-workflow"}}}',
        }
        for label, text in cases.items():
            with self.subTest(label=label):
                self.mock_fetch.reset_mock()
                (self.root / "sources.lock.json").write_text(text, encoding="utf-8")
                before = self.snapshot()
                with patch.object(skill_sync, "publish", wraps=skill_sync.publish) as publish:
                    with self.assertRaises(skill_sync.SyncError) as caught:
                        self.run_sync()
                self.assertNotIn("private-lock-value", str(caught.exception))
                self.assertEqual(self.mock_fetch.call_count, 0)
                publish.assert_not_called()
                self.assertEqual(before, self.snapshot())

    def test_duplicate_skill_is_rejected(self):
        self.sources.append(dict(self.sources[0]))
        self.write_sources()
        with self.assertRaises(skill_sync.SyncError):
            self.run_sync()
        self.assertEqual(self.mock_fetch.call_count, 0)

    def test_publish_failure_restores_snapshot_and_lock(self):
        self.run_sync()
        before = self.snapshot()
        self.commit = "b" * 40
        entry = self.upstream / "skills/alpha/SKILL.md"
        entry.write_text(entry.read_text(encoding="utf-8") + "Changed\n", encoding="utf-8")
        original_replace = Path.replace

        def replace(path, target):
            if path.name == "sources.lock.json" and path.parent.name.startswith(".skill-sync-"):
                raise OSError("simulated write failure")
            return original_replace(path, target)

        with patch.object(Path, "replace", replace), self.assertRaises(OSError):
            self.run_sync()
        self.assertEqual(before, self.snapshot())

    def test_owned_plugin_survives_repeated_sync_and_failure(self):
        owned = self.root / "plugins/agent-manager/skills/am-conflict"
        owned.mkdir(parents=True)
        (owned / "SKILL.md").write_text("owned source", encoding="utf-8")
        configure = self.root / "plugins/agent-manager/skills/am-config"
        configure.mkdir(parents=True)
        (configure / "SKILL.md").write_text("owned project configuration source", encoding="utf-8")
        self.run_sync()
        before = skill_sync.fingerprints(self.root / "plugins/agent-manager")
        snapshot = self.snapshot()
        self.run_sync()
        self.assertEqual(snapshot, self.snapshot())
        self.mock_fetch.side_effect = skill_sync.SyncError("network unavailable")
        with self.assertRaises(skill_sync.SyncError):
            self.run_sync()
        self.assertEqual(before, skill_sync.fingerprints(self.root / "plugins/agent-manager"))

    def test_sources_cannot_grant_owned_plugin_write_access(self):
        (self.root / "plugins/agent-manager").mkdir()
        (self.root / "plugins/agent-manager/plugin.json").write_text('{}', encoding="utf-8")
        document = {"groups": {"agent-manager": {"displayName": "Owned", "skills": self.sources}}}
        (self.root / "sources.yaml").write_text(yaml.safe_dump(document), encoding="utf-8")
        before = self.snapshot()
        with self.assertRaises(skill_sync.SyncError):
            self.run_sync()
        self.assertEqual(before, self.snapshot())
        self.assertEqual(self.mock_fetch.call_count, 0)

    def test_publisher_rejects_owned_manifest_and_snapshot_targets(self):
        with tempfile.TemporaryDirectory(dir=self.root) as staging:
            staged = Path(staging) / "replacement"
            staged.mkdir()
            for relative in ("plugins/agent-manager/skills/am-conflict", "plugins/common-workflow/plugin.json", "plugins/common-workflow/skills", "plugins/common-workflow/.claude-plugin/plugin.json", "plugins/common-workflow/kimi.plugin.json", "plugins/engineering-tools/plugin.json", "kimi.plugin.json", ".claude-plugin/marketplace.json"):
                with self.subTest(target=relative), self.assertRaises(skill_sync.SyncError):
                    skill_sync.publish([(staged, self.root / relative)], Path(staging), self.root)
            self.assertTrue(staged.exists())

    def test_owned_lock_item_is_rejected_before_fetch(self):
        (self.root / "sources.lock.json").write_text(json.dumps({"skills": {"owned": {"group": "agent-manager"}}}), encoding="utf-8")
        with self.assertRaises(skill_sync.SyncError):
            self.run_sync()
        self.assertEqual(self.mock_fetch.call_count, 0)

    def test_managed_directory_cannot_redirect_into_owned(self):
        owned = self.root / "plugins/agent-manager"
        owned.mkdir()
        target = self.root / "plugins/common-workflow/skills"
        try:
            target.symlink_to(owned, target_is_directory=True)
        except OSError:
            self.skipTest("Host does not permit symlink creation")
        before = self.snapshot()
        with self.assertRaises(skill_sync.SyncError):
            self.run_sync()
        self.assertEqual(before, self.snapshot())


if __name__ == "__main__":
    unittest.main()
