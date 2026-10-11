"""Manual-only packaging and recorded-upstream comparisons."""

import importlib.util
import json
from pathlib import Path
import tempfile
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


updates = load_module("check_sources", "skills/am-update/scripts/check_sources.py")


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

    def test_duplicate_source_mapping_keys_block_before_query(self):
        cases = {
            "repeated group": """groups:
  common-workflow:
    skills:
      - name: alpha
        repo: owner/repo
        path: skills/alpha
        ref: main
  common-workflow:
    skills:
      - name: alpha
        repo: owner/repo
        path: skills/alpha
        ref: main
""",
            "nested source key": """groups:
  common-workflow:
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
                before = {path.name: path.read_bytes() for path in self.root.iterdir()}
                self.calls.clear()
                with self.assertRaises(updates.Unknown) as caught:
                    updates.check_sources(self.root, self.query)
                self.assertNotIn("private-source-value", str(caught.exception))
                self.assertEqual(self.calls, [])
                self.assertEqual(before, {path.name: path.read_bytes() for path in self.root.iterdir()})

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
        repo: owner/repo
        path: skills/alpha
        ref: main
""", encoding="utf-8")
        rows = updates.check_sources(self.root, self.query)
        self.assertEqual([row["Name"] for row in rows], ["alpha"])
        self.assertEqual(len(self.calls), 2)

    def test_yaml_merge_sequence_keeps_first_mapping_precedence(self):
        (self.root / "sources.yaml").write_text("""groups:
  common-workflow:
    <<: [
      {displayName: Selected, skills: [{name: beta, repo: owner/repo, path: skills/beta, ref: main}]},
      {displayName: '', skills: [{name: alpha, repo: owner/repo, path: skills/alpha, ref: main}]}
    ]
""", encoding="utf-8")
        rows = updates.check_sources(self.root, self.query)
        self.assertEqual([row["Name"] for row in rows], ["beta"])

    def test_duplicate_keys_inside_merge_source_block_before_query(self):
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
                (self.root / "sources.yaml").write_text(text, encoding="utf-8")
                before = {path.name: path.read_bytes() for path in self.root.iterdir()}
                self.calls.clear()
                with self.assertRaises(updates.Unknown) as caught:
                    updates.check_sources(self.root, self.query)
                self.assertNotIn("private-source-value", str(caught.exception))
                self.assertEqual(self.calls, [])
                self.assertEqual(before, {path.name: path.read_bytes() for path in self.root.iterdir()})

    def test_duplicate_lock_object_keys_block_before_query(self):
        cases = {
            "nested record key": '{"skills":{"alpha":{"group":"private-lock-value","group":"common-workflow"}}}',
            "skill identity key": '{"skills":{"alpha":{},"alpha":{}}}',
        }
        for label, text in cases.items():
            with self.subTest(label=label):
                (self.root / "sources.lock.json").write_text(text, encoding="utf-8")
                before = {path.name: path.read_bytes() for path in self.root.iterdir()}
                self.calls.clear()
                with self.assertRaises(updates.Unknown) as caught:
                    updates.check_sources(self.root, self.query)
                self.assertNotIn("private-lock-value", str(caught.exception))
                self.assertEqual(self.calls, [])
                self.assertEqual(before, {path.name: path.read_bytes() for path in self.root.iterdir()})


class PackagingTests(unittest.TestCase):
    def test_kimi_installable_entries_are_removed(self):
        catalog = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
        claude = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual({entry["name"] for entry in catalog["plugins"]}, {entry["name"] for entry in claude["plugins"]})
        self.assertFalse((ROOT / "kimi.plugin.json").exists())
        for plugin in (ROOT / "plugins").iterdir():
            self.assertFalse((plugin / "kimi.plugin.json").exists(), plugin.name)
        self.assertFalse((PLUGIN / "references/kimi.md").exists())
        self.assertFalse((ROOT / "plugins/agent-manager/references/agent-sources.md").exists())
        self.assertFalse((ROOT / "tests/kimi_loader.cjs").exists())

    def test_manual_only_metadata_and_marketplace_registration(self):
        catalog = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
        entries = [entry for entry in catalog["plugins"] if entry["name"] == "agent-manager"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["source"]["path"], "./plugins/agent-manager")
        manifest = json.loads((PLUGIN / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["version"], "0.6.1")
        skills = list((PLUGIN / "skills").iterdir())
        self.assertEqual({skill.name for skill in skills}, {"am-conflict", "am-update", "am-config"})
        for skill in skills:
            policy = yaml.safe_load((skill / "agents/openai.yaml").read_text(encoding="utf-8"))
            self.assertIs(policy["policy"]["allow_implicit_invocation"], False)
            text = (skill / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("Only use when explicitly invoked by the user.", text)
            frontmatter = yaml.safe_load(text.split("---", 2)[1])
            self.assertIs(frontmatter["disable-model-invocation"], True)
        sources = yaml.safe_load((ROOT / "sources.yaml").read_text(encoding="utf-8"))
        self.assertNotIn("agent-manager", sources["groups"])
        lock = json.loads((ROOT / "sources.lock.json").read_text(encoding="utf-8"))
        self.assertNotIn("agent-manager", {item["group"] for item in lock["skills"].values()})
        self.assertNotIn("am-config", lock["skills"])
        self.assertNotIn("am-config", {item["name"] for group in sources["groups"].values() for item in group["skills"]})

    def test_claude_catalog_uses_same_plugin_roots_and_unpinned_versions(self):
        codex = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
        claude = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(claude["name"], codex["name"])
        self.assertEqual({entry["name"] for entry in claude["plugins"]}, {entry["name"] for entry in codex["plugins"]})
        count = 0
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
        self.assertEqual(count, 20)
        handoff = (ROOT / "plugins/common-workflow/skills/handoff/SKILL.md").read_text(encoding="utf-8")
        self.assertIs(yaml.safe_load(handoff.split("---", 2)[1])["disable-model-invocation"], True)


if __name__ == "__main__":
    unittest.main()
