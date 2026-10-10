"""Manual-only packaging and recorded-upstream comparisons."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/agent-manager"


def load_module(name, relative):
    spec = importlib.util.spec_from_file_location(name, PLUGIN / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


updates = load_module("check_sources", "skills/check-updates/scripts/check_sources.py")


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
        self.assertEqual({skill.name for skill in skills}, {"resolve-conflicts", "check-updates", "configure-project"})
        for skill in skills:
            policy = yaml.safe_load((skill / "agents/openai.yaml").read_text(encoding="utf-8"))
            self.assertIs(policy["policy"]["allow_implicit_invocation"], False)
            text = (skill / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("Only use when explicitly invoked by the user.", text)
        sources = yaml.safe_load((ROOT / "sources.yaml").read_text(encoding="utf-8"))
        self.assertNotIn("agent-manager", sources["groups"])
        lock = json.loads((ROOT / "sources.lock.json").read_text(encoding="utf-8"))
        self.assertNotIn("agent-manager", {item["group"] for item in lock["skills"].values()})
        self.assertNotIn("configure-project", lock["skills"])
        self.assertNotIn("configure-project", {item["name"] for group in sources["groups"].values() for item in group["skills"]})


if __name__ == "__main__":
    unittest.main()
