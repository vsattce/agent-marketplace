"""Read-only context inventory and current Codex usage parsing."""

import importlib.util
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins/agent-manager/skills/am-context/scripts/context.py"


def load_context_module():
    if not SCRIPT.is_file():
        raise AssertionError(f"Context inventory implementation is missing: {SCRIPT}")
    spec = importlib.util.spec_from_file_location("agent_manager_context", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError("Unable to load context inventory implementation")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def usage_counts(input_tokens: int) -> dict:
    return {
        "input_tokens": input_tokens,
        "cached_input_tokens": 0,
        "cache_write_input_tokens": 0,
        "output_tokens": 7,
        "reasoning_output_tokens": 2,
        "total_tokens": input_tokens + 7,
    }


def write_codex_session(home: Path, project: Path, thread_id: str, events: list[dict]) -> Path:
    path = home / "sessions/2026/10/12" / f"rollout-2026-10-12-{thread_id}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    records = [{
        "type": "session_meta",
        "payload": {"id": thread_id, "cwd": str(project)},
    }, *events]
    path.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")
    return path


def token_event(input_tokens: int, *, timestamp: str = "2026-10-12T08:00:00Z", window: int = 1000) -> dict:
    return {
        "type": "event_msg",
        "timestamp": timestamp,
        "payload": {
            "type": "token_count",
            "info": {
                "total_token_usage": usage_counts(9000),
                "last_token_usage": usage_counts(input_tokens),
                "model_context_window": window,
            },
        },
    }


class FakeTokenizer:
    BLOB_URL = "https://example.invalid/o200k_base.tiktoken"
    CACHE_CONTENTS = b"local tokenizer fixture"
    EXPECTED_HASH = hashlib.sha256(CACHE_CONTENTS).hexdigest()

    def __init__(self):
        self.unsafe_reads = 0
        self.encoding_names = []
        self.load_module = types.ModuleType("tiktoken.load")

        def unsafe_read_file_cached(blobpath, expected_hash=None):
            self.unsafe_reads += 1
            raise AssertionError("network-capable cache loader must not run")

        self.original_read_file_cached = unsafe_read_file_cached
        self.load_module.read_file_cached = self.original_read_file_cached

        self.module = types.ModuleType("tiktoken")
        self.module.__path__ = []
        self.module.get_encoding = self.get_encoding
        self.modules = {"tiktoken": self.module, "tiktoken.load": self.load_module}

    @property
    def cache_contents(self):
        return self.CACHE_CONTENTS

    def cache_path(self, cache_dir):
        key = hashlib.sha1(self.BLOB_URL.encode("utf-8")).hexdigest()
        return cache_dir / key

    def write_cache(self, cache_dir, contents):
        self.cache_path(cache_dir).write_bytes(contents)

    def get_encoding(self, name):
        self.encoding_names.append(name)
        if name != "o200k_base":
            raise AssertionError(f"Unexpected encoding requested: {name}")
        cached_data = self.load_module.read_file_cached(self.BLOB_URL, self.EXPECTED_HASH)
        if cached_data != self.CACHE_CONTENTS:
            raise ValueError("Unexpected tokenizer data")

        class Encoder:
            @staticmethod
            def encode(text, disallowed_special=()):
                return text.split()

        return Encoder()


class ContextCliTests(unittest.TestCase):
    def test_modes_and_invalid_input_are_decided_before_scanning(self):
        context = load_context_module()
        calls = []

        def scanner(**kwargs):
            calls.append(kwargs)
            return {"mode": kwargs["mode"]}

        for mode in ("summary", "all", "skills", "tools", "rules"):
            with self.subTest(mode=mode):
                output = io.StringIO()
                result = context.main(
                    ["--mode", mode, "--harness", "codex", "--project", "unused"],
                    stdout=output,
                    scanner=scanner,
                )
                self.assertEqual(result, 0)
                self.assertEqual(json.loads(output.getvalue()), {"mode": mode})
        output = io.StringIO()
        self.assertEqual(context.main([], stdout=output, scanner=scanner), 0)
        self.assertEqual(json.loads(output.getvalue()), {"mode": "summary"})
        self.assertEqual(len(output.getvalue().splitlines()), 1, "default summary output should be compact")
        self.assertEqual([call["mode"] for call in calls], ["summary", "all", "skills", "tools", "rules", "summary"])

        for mode in ("help", "default", "ALL", "skills tools", "rules extra"):
            with self.subTest(mode=mode):
                output = io.StringIO()
                result = context.main(["--mode", mode], stdout=output, scanner=scanner)
                self.assertEqual(result, 0 if mode == "help" else 2)
                self.assertTrue(output.getvalue().strip())
                if mode != "help":
                    self.assertIn(f"Unknown mode: {mode}", output.getvalue())
                else:
                    self.assertIn("all|skills|tools|rules|help", output.getvalue())
                    self.assertNotIn("--mode summary", output.getvalue())
        self.assertEqual(len(calls), 6, "help and invalid modes must not scan")


class ContextInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="agent-manager-context-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.project = self.root / "project"
        self.project.mkdir()
        (self.project / ".git").mkdir()
        self.home = self.root / "codex-home"
        self.home.mkdir()
        self.thread_id = "019c-example-current"
        self.env = {"CODEX_HOME": str(self.home), "CODEX_THREAD_ID": self.thread_id}
        self.context = load_context_module()

    def collect(self, mode="all"):
        return self.context.collect_context(
            mode=mode,
            harness="codex",
            project=str(self.project),
            env=self.env,
            active_skill="am-context",
        )

    def test_collectors_run_only_for_requested_source_mode(self):
        results = {
            "rules": {"status": "COMPLETE", "items": [], "loaded": "UNKNOWN"},
            "skills": {"status": "COMPLETE", "items": [], "loaded": "UNKNOWN"},
            "plugins": {"status": "COMPLETE", "items": [{"name": "plugin", "source": "manifest"}], "files": [], "loaded": "UNKNOWN"},
            "tools": {"status": "COMPLETE", "items": [], "session_tools": "UNKNOWN"},
            "usage": {"status": "UNKNOWN", "availability": "UNAVAILABLE"},
        }
        expected = {
            "summary": {"rules", "skills", "plugins", "tools", "usage"},
            "all": {"rules", "skills", "plugins", "tools", "usage"},
            "rules": {"rules", "usage"},
            "skills": {"skills", "usage"},
            "tools": {"plugins", "tools", "usage"},
        }
        collector_specs = {
            "rules": ("_codex_rules", (self.project, self.project, self.home, [self.project])),
            "skills": ("_discover_skills", (self.project, self.project, "codex", self.env)),
            "plugins": ("_collect_plugins", (self.project, "codex", self.home)),
            "tools": ("_collect_tools", (self.project, self.project, "codex", self.home)),
            "usage": ("_collect_token_usage", ("codex", self.project, self.home, self.env)),
        }

        for mode, wanted in expected.items():
            with self.subTest(mode=mode):
                calls = {}
                with patch.multiple(
                    self.context,
                    **{
                        name: Mock(side_effect=lambda *args, _key=key, **kwargs: calls.setdefault(_key, results[_key]))
                        for key, (name, _) in collector_specs.items()
                    },
                ):
                    result = self.collect(mode)
                self.assertEqual(set(calls), wanted)
                if mode == "tools":
                    self.assertEqual(result["plugins"]["items"][0]["name"], "plugin")

    def test_successful_collectors_report_complete_not_unknown_loading(self):
        inventory = self.collect()
        for section in ("rules", "skills", "plugins", "tools"):
            self.assertEqual(inventory[section]["status"], "COMPLETE")
        self.assertEqual(inventory["skills"]["loaded"], "UNKNOWN")

    def test_rule_size_estimate_is_unknown_after_read_failure(self):
        path = self.project / "AGENTS.md"
        with patch.object(self.context, "_read_bytes", return_value=(b"", False, "UNAVAILABLE")):
            item = self.context._rule_item(path, self.project, "project", "project")
        self.assertEqual(item["estimate"]["status"], "UNKNOWN")
        self.assertIsNone(item["estimate"]["tokens"])
        self.assertIsNone(item["estimate"]["bytes"])

    def test_truncated_rule_estimate_keeps_estimated_type_and_partial_completeness(self):
        path = self.project / "AGENTS.md"
        path.write_bytes(b"long rule text")
        item = self.context._rule_item(path, self.project, "project", "project", limit=4)
        self.assertEqual(item["estimate"]["status"], "ESTIMATED")
        self.assertEqual(item["estimate"]["completeness"], "PARTIAL")
        self.assertEqual(item["estimate"]["bytes"], 4)

    def test_collector_status_is_partial_on_scan_limit_and_read_failure(self):
        skill = self.project / ".agents/skills/sample/SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text("# skill", encoding="utf-8")
        with patch.object(self.context, "MAX_SCAN_ENTRIES", 0):
            skills = self.context._discover_skills(self.project, self.project, "codex", self.env)
        self.assertEqual(skills["status"], "PARTIAL")

        rule = self.project / "AGENTS.md"
        rule.write_text("# rule", encoding="utf-8")
        with patch.object(self.context, "_read_bytes", side_effect=[
            (b"# rule", False, "READ"), (b"", False, "UNAVAILABLE")
        ]):
            rules = self.context._codex_rules(self.project, self.project, self.home, [self.project])
        self.assertEqual(rules["status"], "PARTIAL")
        self.assertEqual(rules["items"][0]["estimate"]["status"], "UNKNOWN")

    def test_known_breakdown_counts_source_files_once_and_separates_actual_usage(self):
        rule = self.project / "AGENTS.md"
        rule.write_bytes(b"rule")
        skill = self.project / ".agents/skills/shared/SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_bytes(b"---\nname: shared\n---\nskill body")
        catalog = self.project / ".agents/plugins/marketplace.json"
        catalog.parent.mkdir(parents=True)
        catalog.write_text('{"plugins":[{"name":"shared"},{"name":"shared"}]}', encoding="utf-8")
        manifest = self.project / "plugins/shared/plugin.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text('{"name":"shared"}', encoding="utf-8")
        config = self.project / ".codex/config.toml"
        config.parent.mkdir(parents=True)
        config.write_text("[plugins.shared]\nenabled = true\n", encoding="utf-8")

        with patch.dict(sys.modules, {"tiktoken": None, "tiktoken.load": None}):
            summary = self.collect("summary")
            tools = self.collect("tools")
            all_result = self.collect("all")

        breakdown = summary["known_breakdown"]
        categories = breakdown["categories"]
        self.assertEqual(categories["plugin_metadata"]["files"], 2)
        self.assertEqual(categories["known_project_config"]["files"], 1)
        self.assertEqual(categories["plugin_metadata"]["bytes"], len(catalog.read_bytes()) + len(manifest.read_bytes()))
        self.assertEqual(breakdown["loaded"], "UNKNOWN")
        self.assertIn("not actual current context contribution", breakdown["basis"])
        self.assertEqual(breakdown["other_context"]["status"], "UNKNOWN")
        self.assertEqual(summary["plugins"]["count"], 1)
        self.assertEqual(summary["plugins"]["source_count"], 3)
        self.assertIn("files", tools["plugins"])
        self.assertEqual(len([item for item in tools["plugins"]["files"] if item["kind"] == "plugin_metadata"]), 2)
        self.assertIn("known_breakdown", all_result)
        self.assertEqual(all_result["known_breakdown"]["total"]["tokens"], breakdown["total"]["tokens"])

    def test_summary_uses_distinct_names_and_compact_inventory_notice(self):
        catalog = self.project / ".agents/plugins/marketplace.json"
        catalog.parent.mkdir(parents=True)
        catalog.write_text('{"plugins":[{"name":"same"},{"name":"same"}]}', encoding="utf-8")
        summary = self.collect("summary")
        self.assertEqual(summary["plugins"]["count"], 1)
        self.assertEqual(summary["plugins"]["source_count"], 1)
        self.assertEqual(summary["inventory_loaded"], "UNKNOWN")
        self.assertEqual(summary["known_breakdown"]["loaded"], "UNKNOWN")
        self.assertEqual(summary["known_breakdown"]["other_context"]["status"], "UNKNOWN")
        self.assertNotIn("root", summary["project"])

    def test_usage_missing_number_is_unknown_with_separate_availability(self):
        result = self.collect()["context_token_usage"]
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertEqual(result["availability"], "UNAVAILABLE")
        self.assertIsNone(result["input_tokens"])

    def test_usage_derived_fields_name_latest_reported_request_and_approximation(self):
        write_codex_session(self.home, self.project, self.thread_id, [token_event(120, window=1000)])
        result = self.collect()["context_token_usage"]
        self.assertEqual(result["availability"], "AVAILABLE")
        self.assertEqual(result["remaining_approx_status"], "DERIVED / APPROX")
        self.assertEqual(result["usage_percent_approx_status"], "DERIVED / APPROX")
        self.assertIn("latest reported request", result["basis"])

    def test_codex_global_override_precedes_agents_and_external_path_is_absolute(self):
        global_override = self.home / "AGENTS.override.md"
        global_agents = self.home / "AGENTS.md"
        global_override.write_text("override", encoding="utf-8")
        global_agents.write_text("fallback", encoding="utf-8")
        project_override = self.project / "AGENTS.override.md"
        project_agents = self.project / "AGENTS.md"
        project_override.write_text("project override", encoding="utf-8")
        project_agents.write_text("project fallback", encoding="utf-8")

        rules = self.context._codex_rules(self.project, self.project, self.home, [self.project])
        paths = {item["path"] for item in rules["items"]}
        self.assertIn(str(global_override.resolve()), paths)
        self.assertNotIn(str(global_agents.resolve()), paths)
        self.assertIn("AGENTS.override.md", paths)
        self.assertIn("first non-empty", rules["selection"])
        self.assertEqual(rules["loaded"], "UNKNOWN")

    def test_latest_input_not_session_cumulative_total_drives_usage(self):
        write_codex_session(self.home, self.project, self.thread_id, [token_event(120, window=1000)])
        result = self.collect()["context_token_usage"]
        self.assertEqual(result["status"], "MEASURED")
        self.assertEqual(result["input_tokens"], 120)
        self.assertNotEqual(result["input_tokens"], 9000)
        self.assertEqual(result["window_tokens"], 1000)
        self.assertEqual(result["remaining_approx"], 880)
        self.assertEqual(result["usage_percent_approx"], 12.0)
        self.assertEqual(result["timestamp"], "2026-10-12T08:00:00Z")

    def test_compaction_after_last_usage_invalidates_old_measurement(self):
        compact = {"type": "event_msg", "timestamp": "2026-10-12T08:01:00Z",
                   "payload": {"type": "context_compacted"}}
        write_codex_session(self.home, self.project, self.thread_id, [token_event(120), compact])
        result = self.collect()["context_token_usage"]
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertIsNone(result["input_tokens"])

    def test_top_level_compacted_marker_invalidates_usage_until_new_count(self):
        compacted = {"type": "compacted", "timestamp": "2026-10-12T08:01:00Z"}
        write_codex_session(self.home, self.project, self.thread_id, [token_event(120), compacted])
        result = self.collect()["context_token_usage"]
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertIsNone(result["input_tokens"])

        write_codex_session(
            self.home,
            self.project,
            self.thread_id,
            [token_event(120), compacted, token_event(240, timestamp="2026-10-12T08:02:00Z")],
        )
        result = self.collect()["context_token_usage"]
        self.assertEqual(result["status"], "MEASURED")
        self.assertEqual(result["input_tokens"], 240)

    def test_current_thread_and_cwd_must_match_session_metadata(self):
        other = {"type": "session_meta", "payload": {"id": "different-session", "cwd": str(self.project)}}
        path = self.home / "sessions/2026/10/12" / f"rollout-{self.thread_id}.jsonl"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(other) + "\n" + json.dumps(token_event(20)) + "\n", encoding="utf-8")
        result = self.collect()["context_token_usage"]
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertIsNone(result["input_tokens"])

    def test_missing_or_invalid_newest_usage_never_falls_back_to_stale_counts(self):
        invalid = token_event(20)
        invalid["payload"]["info"]["last_token_usage"]["input_tokens"] = -1
        write_codex_session(self.home, self.project, self.thread_id, [token_event(100), invalid])
        result = self.collect()["context_token_usage"]
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertIsNone(result["input_tokens"])

        (self.home / "sessions").rename(self.home / "sessions-old")
        result = self.collect()["context_token_usage"]
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertIsNone(result["input_tokens"])

    def test_unmatched_session_is_not_replaced_with_another_session(self):
        write_codex_session(self.home, self.project, "different-session", [token_event(900)])
        result = self.collect()["context_token_usage"]
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertIsNone(result["input_tokens"])

    def test_body_and_metadata_estimates_are_non_overlapping_and_not_loaded_by_presence(self):
        skill = self.project / ".agents/skills/sample/SKILL.md"
        skill.parent.mkdir(parents=True)
        body = "---\nname: sample\ndescription: example\n---\n# Body\nactual content\n"
        skill.write_text(body, encoding="utf-8")
        (self.project / "AGENTS.md").write_text("Project rule\n", encoding="utf-8")
        inventory = self.collect()
        item = next(skill for skill in inventory["skills"]["items"] if skill["name"] == "sample")
        self.assertEqual(item["source_kind"], "standalone")
        self.assertEqual(item["metadata"]["status"], "ESTIMATED")
        self.assertEqual(item["body"]["status"], "ESTIMATED")
        self.assertEqual(item["metadata"]["bytes"] + item["body"]["bytes"], len(skill.read_bytes()))
        self.assertEqual(item["body"]["loaded"], "UNKNOWN")
        rule = next(rule for rule in inventory["rules"]["items"] if rule["path"] == "AGENTS.md")
        self.assertEqual(rule["loaded"], "UNKNOWN")

    def test_read_only_utf8_estimator_does_not_need_tokenizer_or_create_cache(self):
        candidate = self.project / "AGENTS.md"
        candidate.write_text("规则文本", encoding="utf-8")
        before = {path.relative_to(self.root) for path in self.root.rglob("*")}
        with patch.dict(sys.modules, {"tiktoken": None, "tiktoken.load": None}):
            estimate = self.context.estimate_bytes(candidate.read_bytes())
            inventory = self.collect()
        after = {path.relative_to(self.root) for path in self.root.rglob("*")}
        self.assertEqual(estimate["status"], "ESTIMATED")
        self.assertEqual(estimate["tokens"], len("规则文本".encode("utf-8")))
        self.assertIn("UTF-8 bytes", estimate["algorithm"])
        self.assertEqual(after, before)
        self.assertFalse(any("tokenizer" in path.as_posix().lower() for path in after))

    def test_tiktoken_uses_only_an_existing_verified_cache(self):
        cache_dir = self.root / "tokenizer-cache"
        cache_dir.mkdir()
        tokenizer = FakeTokenizer()
        tokenizer.write_cache(cache_dir, tokenizer.cache_contents)
        with patch.dict(sys.modules, tokenizer.modules), patch.dict(
            "os.environ", {"TIKTOKEN_CACHE_DIR": str(cache_dir)}
        ):
            estimate = self.context.estimate_bytes(b"two words")

        self.assertEqual(estimate["status"], "ESTIMATED")
        self.assertEqual(estimate["bytes"], len(b"two words"))
        self.assertEqual(estimate["tokens"], 2)
        self.assertIn("tiktoken o200k_base", estimate["algorithm"])
        self.assertEqual(tokenizer.encoding_names, ["o200k_base"])
        self.assertEqual(tokenizer.unsafe_reads, 0)
        self.assertIs(tokenizer.load_module.read_file_cached, tokenizer.original_read_file_cached)
        self.assertEqual(list(cache_dir.iterdir()), [tokenizer.cache_path(cache_dir)])

    def test_missing_or_cold_tokenizer_cache_falls_back_without_writing(self):
        cache_dir = self.root / "empty-tokenizer-cache"
        cache_dir.mkdir()
        tokenizer = FakeTokenizer()
        with patch.dict(sys.modules, tokenizer.modules), patch.dict(
            "os.environ", {"TIKTOKEN_CACHE_DIR": str(cache_dir)}
        ):
            estimate = self.context.estimate_bytes(b"two words")

        self.assertEqual(estimate["tokens"], len(b"two words"))
        self.assertIn("UTF-8 bytes", estimate["algorithm"])
        self.assertEqual(list(cache_dir.iterdir()), [])
        self.assertEqual(tokenizer.unsafe_reads, 0)
        self.assertIs(tokenizer.load_module.read_file_cached, tokenizer.original_read_file_cached)

    def test_tokenizer_cache_fallback_never_probes_or_creates_system_temp(self):
        with patch.dict("os.environ", {}, clear=True), patch(
            "tempfile.gettempdir", side_effect=AssertionError("must not probe the system temp directory")
        ):
            with self.assertRaises(FileNotFoundError):
                self.context._read_existing_tokenizer_cache(FakeTokenizer.BLOB_URL, env={})

    def test_damaged_tokenizer_cache_falls_back_and_preserves_cache_bytes(self):
        cache_dir = self.root / "damaged-tokenizer-cache"
        cache_dir.mkdir()
        tokenizer = FakeTokenizer()
        damaged = b"damaged local tokenizer data"
        tokenizer.write_cache(cache_dir, damaged)
        with patch.dict(sys.modules, tokenizer.modules), patch.dict(
            "os.environ", {"TIKTOKEN_CACHE_DIR": str(cache_dir)}
        ):
            estimate = self.context.estimate_bytes(b"two words")

        self.assertEqual(estimate["tokens"], len(b"two words"))
        self.assertIn("UTF-8 bytes", estimate["algorithm"])
        self.assertEqual(tokenizer.cache_path(cache_dir).read_bytes(), damaged)
        self.assertEqual(tokenizer.unsafe_reads, 0)
        self.assertIs(tokenizer.load_module.read_file_cached, tokenizer.original_read_file_cached)

    def test_declared_mcp_names_are_reported_without_config_values(self):
        settings = self.project / ".codex/config.toml"
        settings.parent.mkdir()
        settings.write_text(
            '[mcp_servers."safe-name"]\ncommand = "private-command-marker"\n'
            'api_token = "private-token-marker"\n', encoding="utf-8"
        )
        output = json.dumps(self.collect(), ensure_ascii=False)
        self.assertIn("safe-name", output)
        self.assertNotIn("private-command-marker", output)
        self.assertNotIn("private-token-marker", output)

    def test_codex_plugin_enablement_only_reports_boolean_values(self):
        config = self.project / ".codex/config.toml"
        config.parent.mkdir()
        config.write_text(
            '[plugins.enabled-true]\nenabled = true\n'
            '[plugins.enabled-false]\nenabled = false\n'
            '[plugins.missing-field]\n'
            '[plugins.string-value]\nenabled = "private-string-marker"\n'
            '[plugins.object-value]\nenabled = { marker = "private-object-marker" }\n'
            '[plugins.list-value]\nenabled = ["private-list-marker"]\n'
            '[plugins.integer-value]\nenabled = 7\n',
            encoding="utf-8",
        )

        result = self.collect("tools")
        output = json.dumps(result, ensure_ascii=False)
        items = {item["name"]: item for item in result["plugins"]["items"]}
        self.assertNotIn("private-string-marker", output)
        self.assertNotIn("private-object-marker", output)
        self.assertNotIn("private-list-marker", output)
        self.assertNotIn("7", items["integer-value"]["evidence"])
        self.assertEqual(items["enabled-true"]["evidence"], "configured enabled=true")
        self.assertEqual(items["enabled-false"]["evidence"], "configured enabled=false")
        self.assertEqual(items["missing-field"]["evidence"], "configured")
        for name in ("string-value", "object-value", "list-value", "integer-value"):
            self.assertEqual(items[name]["evidence"], "configured enabled=UNKNOWN")
        self.assertEqual(result["plugins"]["status"], "PARTIAL")
        self.assertTrue(all(item["loaded"] == "UNKNOWN" for item in items.values()))

        config.write_text("[plugins.missing-field]\n", encoding="utf-8")
        missing_only = self.collect("tools")["plugins"]
        self.assertEqual(missing_only["status"], "COMPLETE")
        self.assertEqual(missing_only["items"][0]["evidence"], "configured")

    def test_claude_plugin_enablement_redacts_non_boolean_values(self):
        settings = self.home / "settings.json"
        settings.write_text(json.dumps({
            "enabledPlugins": {
                "enabled-true": True,
                "enabled-false": False,
                "string-value": "private-string-marker",
                "object-value": {"marker": "private-object-marker"},
                "list-value": ["private-list-marker"],
                "integer-value": 7,
                "null-value": None,
            },
        }), encoding="utf-8")

        result = self.context.collect_context(
            mode="tools",
            harness="claude",
            project=str(self.project),
            env={"CLAUDE_CONFIG_DIR": str(self.home)},
            active_skill="am-context",
        )
        output = json.dumps(result, ensure_ascii=False)
        items = {item["name"]: item for item in result["plugins"]["items"]}
        self.assertNotIn("private-string-marker", output)
        self.assertNotIn("private-object-marker", output)
        self.assertNotIn("private-list-marker", output)
        self.assertNotIn("7", items["integer-value"]["evidence"])
        self.assertEqual(items["enabled-true"]["evidence"], "configured enabled=true")
        self.assertEqual(items["enabled-false"]["evidence"], "configured enabled=false")
        for name in ("string-value", "object-value", "list-value", "integer-value", "null-value"):
            self.assertEqual(items[name]["evidence"], "configured enabled=UNKNOWN")
        self.assertTrue(all(item["loaded"] == "UNKNOWN" for item in items.values()))
        self.assertEqual(result["plugins"]["status"], "PARTIAL")


if __name__ == "__main__":
    unittest.main()
