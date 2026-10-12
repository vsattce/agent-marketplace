"""Runtime-context boundaries for the am-context inspector."""

import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins/agent-manager/skills/am-context/scripts/context.py"


def load_context_module():
    spec = importlib.util.spec_from_file_location("agent_manager_context", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError("Unable to load the am-context implementation")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def usage_counts(input_tokens: int, output_tokens: int = 7) -> dict:
    return {
        "input_tokens": input_tokens,
        "cached_input_tokens": 0,
        "cache_write_input_tokens": 0,
        "output_tokens": output_tokens,
        "reasoning_output_tokens": 2,
        "total_tokens": input_tokens + output_tokens,
    }


def token_usage_record(
    input_tokens: int,
    *,
    output_tokens: int = 7,
    thread_id: str = "019c-runtime-current",
    turn_id: str = "turn-current",
    timestamp: str = "2026-10-12T08:00:00Z",
) -> dict:
    return {
        "type": "token_usage_record",
        "timestamp": timestamp,
        "payload": {
            "thread_id": thread_id,
            "turn_id": turn_id,
            "session_id": "session-current",
            "root_turn_id": "turn-root",
            "response_id": "response-current",
            "usage": usage_counts(input_tokens, output_tokens),
            "turn_token_usage": usage_counts(9000),
            "thread_token_usage": usage_counts(18000),
        },
    }


def task_started(turn_id: str = "turn-current", window: int = 258400) -> dict:
    return {
        "type": "event_msg",
        "payload": {
            "type": "task_started",
            "turn_id": turn_id,
            "model_context_window": window,
        },
    }


def token_event(input_tokens: int | None, *, timestamp: str = "2026-10-12T08:00:00Z", window: int = 1000) -> dict:
    usage = usage_counts(input_tokens) if input_tokens is not None else None
    return {
        "type": "event_msg",
        "timestamp": timestamp,
        "payload": {
            "type": "token_count",
            "info": {
                "total_token_usage": usage_counts(9000),
                "last_token_usage": usage,
                "model_context_window": window,
            },
        },
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


class ContextCliTests(unittest.TestCase):
    def test_default_and_supported_modes_call_runtime_inspector_once(self):
        context = load_context_module()
        calls = []

        def inspector(**kwargs):
            calls.append(kwargs)
            return {"mode": kwargs["mode"]}

        for mode in ("summary", "all", "skills", "tools", "rules"):
            with self.subTest(mode=mode):
                output = io.StringIO()
                self.assertEqual(context.main(["--mode", mode], stdout=output, scanner=inspector), 0)
                self.assertEqual(json.loads(output.getvalue()), {"mode": mode})
        output = io.StringIO()
        self.assertEqual(context.main([], stdout=output, scanner=inspector), 0)
        self.assertEqual(json.loads(output.getvalue()), {"mode": "summary"})
        self.assertEqual([call["mode"] for call in calls], ["summary", "all", "skills", "tools", "rules", "summary"])

    def test_help_and_invalid_modes_do_not_inspect_runtime(self):
        context = load_context_module()
        calls = []
        output = io.StringIO()

        self.assertEqual(context.main(["--mode", "help"], stdout=output, scanner=lambda **kw: calls.append(kw)), 0)
        self.assertIn("all|skills|tools|rules|help", output.getvalue())
        self.assertEqual(context.main(["--mode", "ALL"], stdout=io.StringIO(), scanner=lambda **kw: calls.append(kw)), 2)
        self.assertEqual(calls, [])


class RuntimeContextTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="agent-manager-runtime-context-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.project = self.root / "project"
        self.project.mkdir()
        (self.project / ".git").mkdir()
        self.home = self.root / "codex-home"
        self.home.mkdir()
        self.thread_id = "019c-runtime-current"
        self.env = {"CODEX_HOME": str(self.home), "CODEX_THREAD_ID": self.thread_id}
        self.context = load_context_module()

    def collect(self, mode="summary", harness="codex"):
        return self.context.collect_context(
            mode=mode,
            harness=harness,
            project=str(self.project),
            env=self.env,
        )

    def test_summary_reads_only_exact_session_and_never_scans_project_sources(self):
        (self.project / "AGENTS.md").write_text("UNLOADED_RULE_SECRET_MARKER", encoding="utf-8")
        unloaded = self.project / ".agents/skills/unloaded/SKILL.md"
        unloaded.parent.mkdir(parents=True)
        unloaded.write_text("UNLOADED_SKILL_SECRET_MARKER", encoding="utf-8")
        write_codex_session(self.home, self.project, self.thread_id, [token_usage_record(120), token_event(120)])

        opened_project_files = []
        original_open = Path.open

        def tracked_open(path, *args, **kwargs):
            if path.is_file() and self.project in path.resolve().parents:
                opened_project_files.append(path)
            return original_open(path, *args, **kwargs)

        with patch.object(Path, "open", tracked_open):
            result = self.collect()

        serialized = json.dumps(result, ensure_ascii=False)
        self.assertEqual(opened_project_files, [])
        self.assertNotIn("UNLOADED_RULE_SECRET_MARKER", serialized)
        self.assertNotIn("UNLOADED_SKILL_SECRET_MARKER", serialized)
        self.assertNotIn("known_breakdown", result)
        self.assertNotIn("active_skill", result)
        self.assertEqual(result["context_token_usage"]["status"], "MEASURED")
        self.assertEqual(result["context_token_usage"]["input_tokens"], 120)
        self.assertEqual(result["runtime_context"]["status"], "UNKNOWN")
        self.assertEqual(result["runtime_context"]["basis"], "No complete latest-request input snapshot is exposed by this runtime.")
        self.assertNotIn("categories", result["runtime_context"], "summary should explain the limit without an UNKNOWN table")

    def test_latest_per_response_report_in_log_order_is_used_without_summing(self):
        write_codex_session(
            self.home,
            self.project,
            self.thread_id,
            [task_started(), token_usage_record(146345, output_tokens=900), token_event(145059, window=258400)],
        )

        usage = self.collect()["context_token_usage"]

        self.assertEqual(usage["status"], "MEASURED")
        self.assertEqual(usage["input_tokens"], 145059)
        self.assertEqual(usage["source"], "event_msg.token_count.last_token_usage.input_tokens")
        self.assertEqual(usage["window_tokens"], 258400)
        self.assertEqual(usage["window_source"], "event_msg.token_count.info.model_context_window")
        self.assertEqual(usage["remaining_approx"], 113341)
        self.assertEqual(usage["usage_percent_approx"], 56.1)

    def test_later_usage_record_is_used_after_earlier_token_count(self):
        write_codex_session(
            self.home,
            self.project,
            self.thread_id,
            [task_started(), token_event(145059, window=258400), token_usage_record(146345, output_tokens=900)],
        )

        usage = self.collect()["context_token_usage"]

        self.assertEqual(usage["input_tokens"], 146345)
        self.assertEqual(usage["source"], "token_usage_record.payload.usage.input_tokens")
        self.assertEqual(usage["window_source"], "event_msg.task_started.model_context_window (matching turn_id)")

    def test_token_count_reports_latest_input_and_only_its_reported_window(self):
        write_codex_session(self.home, self.project, self.thread_id, [token_event(120, window=1000)])

        usage = self.collect()["context_token_usage"]

        self.assertEqual(usage["status"], "MEASURED")
        self.assertEqual(usage["input_tokens"], 120)
        self.assertEqual(usage["window_tokens"], 1000)
        self.assertEqual(usage["remaining_approx"], 880)
        self.assertEqual(usage["usage_percent_approx"], 12.0)
        self.assertEqual(usage["source"], "event_msg.token_count.last_token_usage.input_tokens")

    def test_window_from_another_turn_is_not_used(self):
        write_codex_session(
            self.home,
            self.project,
            self.thread_id,
            [task_started(turn_id="turn-old"), token_usage_record(146345, turn_id="turn-current")],
        )

        usage = self.collect()["context_token_usage"]

        self.assertEqual(usage["input_tokens"], 146345)
        self.assertIsNone(usage["window_tokens"])
        self.assertIsNone(usage["remaining_approx"])

    def test_task_started_after_usage_record_cannot_supply_its_window(self):
        write_codex_session(
            self.home,
            self.project,
            self.thread_id,
            [token_usage_record(146345), task_started(window=258400)],
        )

        usage = self.collect()["context_token_usage"]

        self.assertEqual(usage["input_tokens"], 146345)
        self.assertIsNone(usage["window_tokens"])

    def test_ambiguous_repeated_task_started_window_is_unknown(self):
        write_codex_session(
            self.home,
            self.project,
            self.thread_id,
            [task_started(window=258400), task_started(window=200000), token_usage_record(146345)],
        )

        usage = self.collect()["context_token_usage"]

        self.assertEqual(usage["input_tokens"], 146345)
        self.assertIsNone(usage["window_tokens"])

    def test_duplicate_task_started_after_usage_invalidates_cached_window(self):
        write_codex_session(
            self.home,
            self.project,
            self.thread_id,
            [
                task_started(turn_id="turn-current", window=1000),
                token_usage_record(120, turn_id="turn-current"),
                task_started(turn_id="turn-current", window=2000),
            ],
        )

        usage = self.collect()["context_token_usage"]

        self.assertEqual(usage["status"], "MEASURED")
        self.assertEqual(usage["input_tokens"], 120)
        self.assertIsNone(usage["window_tokens"])
        self.assertIsNone(usage["remaining_approx"])
        self.assertIsNone(usage["usage_percent_approx"])

    def test_mirrored_token_count_and_usage_record_are_never_accumulated(self):
        write_codex_session(
            self.home,
            self.project,
            self.thread_id,
            [token_usage_record(120), token_event(120)],
        )

        usage = self.collect()["context_token_usage"]

        self.assertEqual(usage["input_tokens"], 120)

    def test_rate_limit_token_count_without_info_does_not_replace_latest_usage(self):
        rate_limit = {"type": "event_msg", "payload": {"type": "token_count", "info": None}}
        write_codex_session(self.home, self.project, self.thread_id, [token_usage_record(120), rate_limit])

        usage = self.collect()["context_token_usage"]

        self.assertEqual(usage["status"], "MEASURED")
        self.assertEqual(usage["input_tokens"], 120)

    def test_invalid_newer_usage_does_not_fall_back_to_older_measurement(self):
        write_codex_session(
            self.home,
            self.project,
            self.thread_id,
            [token_usage_record(120), token_usage_record(-1, timestamp="2026-10-12T08:01:00Z")],
        )

        usage = self.collect()["context_token_usage"]

        self.assertEqual(usage["status"], "UNKNOWN")
        self.assertIsNone(usage["input_tokens"])

    def test_malformed_newer_usage_payload_does_not_fall_back_to_older_measurement(self):
        malformed = {"type": "token_usage_record", "payload": None}
        write_codex_session(self.home, self.project, self.thread_id, [token_usage_record(120), malformed])

        usage = self.collect()["context_token_usage"]

        self.assertEqual(usage["status"], "UNKNOWN")
        self.assertIsNone(usage["input_tokens"])

    def test_non_object_jsonl_record_marks_measurement_unavailable(self):
        for malformed in (None, []):
            with self.subTest(record=malformed):
                write_codex_session(self.home, self.project, self.thread_id, [token_usage_record(120), malformed])

                usage = self.collect()["context_token_usage"]

                self.assertEqual(usage["status"], "UNKNOWN")
                self.assertEqual(usage["availability"], "PARTIAL")
                self.assertIsNone(usage["input_tokens"])

    def test_malformed_event_shape_does_not_leave_stale_measurement(self):
        malformed_events = (
            {"type": "event_msg", "payload": {"type": []}},
            {"type": "event_msg", "payload": {"type": {}}},
            {"type": "event_msg", "payload": {}},
            {"type": "event_msg", "payload": []},
            {"type": "event_msg", "payload": {"type": "token_count"}},
        )
        for malformed in malformed_events:
            with self.subTest(event=malformed):
                write_codex_session(self.home, self.project, self.thread_id, [token_usage_record(120), malformed])

                usage = self.collect()["context_token_usage"]

                self.assertEqual(usage["status"], "UNKNOWN")
                self.assertEqual(usage["availability"], "PARTIAL")
                self.assertIsNone(usage["input_tokens"])

    def test_invalid_newer_legacy_token_count_does_not_fall_back(self):
        write_codex_session(self.home, self.project, self.thread_id, [token_event(120), token_event(None)])

        usage = self.collect()["context_token_usage"]

        self.assertEqual(usage["status"], "UNKNOWN")
        self.assertIsNone(usage["input_tokens"])

    def test_invalid_newer_token_count_does_not_fall_back_to_usage_record(self):
        write_codex_session(self.home, self.project, self.thread_id, [token_usage_record(120), token_event(None)])

        usage = self.collect()["context_token_usage"]

        self.assertEqual(usage["status"], "UNKNOWN")
        self.assertIsNone(usage["input_tokens"])

    def test_compaction_invalidates_older_usage_until_a_new_measurement(self):
        compacted = {"type": "compacted", "timestamp": "2026-10-12T08:01:00Z"}
        write_codex_session(self.home, self.project, self.thread_id, [token_usage_record(120), compacted])
        self.assertEqual(self.collect()["context_token_usage"]["status"], "UNKNOWN")

        write_codex_session(
            self.home,
            self.project,
            self.thread_id,
            [token_usage_record(120), compacted, token_usage_record(240, timestamp="2026-10-12T08:02:00Z")],
        )
        self.assertEqual(self.collect()["context_token_usage"]["input_tokens"], 240)

    def test_session_metadata_must_match_exact_thread_and_cwd(self):
        wrong = {"type": "session_meta", "payload": {"id": "another-thread", "cwd": str(self.project)}}
        path = self.home / "sessions/2026/10/12" / f"rollout-{self.thread_id}.jsonl"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(wrong) + "\n{UNREAD_OTHER_SESSION_BODY\n", encoding="utf-8")

        usage = self.collect()["context_token_usage"]

        self.assertEqual(usage["status"], "UNKNOWN")
        self.assertEqual(usage["availability"], "UNKNOWN")
        self.assertIsNone(usage["input_tokens"])

    def test_usage_record_thread_id_must_match_the_session_thread(self):
        write_codex_session(
            self.home,
            self.project,
            self.thread_id,
            [token_usage_record(900, thread_id="another-thread")],
        )

        usage = self.collect()["context_token_usage"]

        self.assertEqual(usage["status"], "UNKNOWN")
        self.assertIsNone(usage["input_tokens"])

    def test_unmatched_session_is_never_used_as_a_fallback(self):
        write_codex_session(self.home, self.project, "another-thread", [token_usage_record(900, thread_id="another-thread")])

        opened_sessions = []
        original_open = Path.open

        def tracked_open(path, *args, **kwargs):
            if path.suffix == ".jsonl":
                opened_sessions.append(path)
            return original_open(path, *args, **kwargs)

        with patch.object(Path, "open", tracked_open):
            usage = self.collect()["context_token_usage"]

        self.assertEqual(opened_sessions, [])
        self.assertEqual(usage["status"], "UNKNOWN")
        self.assertIsNone(usage["input_tokens"])

    def test_oversized_exact_session_is_unknown_without_fallback(self):
        write_codex_session(self.home, self.project, self.thread_id, [token_usage_record(120)])
        with patch.object(self.context, "MAX_SESSION_BYTES", 100):
            usage = self.collect()["context_token_usage"]

        self.assertEqual(usage["status"], "UNKNOWN")
        self.assertEqual(usage["availability"], "PARTIAL")
        self.assertIsNone(usage["input_tokens"])

    def test_incomplete_session_tail_does_not_fall_back_to_previous_usage(self):
        path = write_codex_session(self.home, self.project, self.thread_id, [token_usage_record(120)])
        with path.open("ab") as destination:
            destination.write(b'{"type":"token_usage_record"')

        usage = self.collect()["context_token_usage"]

        self.assertEqual(usage["status"], "UNKNOWN")
        self.assertEqual(usage["availability"], "PARTIAL")
        self.assertIsNone(usage["input_tokens"])

    def test_logged_roles_and_content_kinds_do_not_prove_latest_request_membership(self):
        user_item = {
            "type": "response_item",
            "payload": {
                "type": "message",
                "role": "user",
                "turn_id": "turn-current",
                "content": [{"type": "text", "text": "CURRENT_USER_SECRET"}],
                "internal_chat_message_metadata_passthrough": {"content_item_kinds": ["user.text"]},
            },
        }
        assistant_item = {
            "type": "response_item",
            "payload": {
                "type": "message",
                "role": "assistant",
                "turn_id": "turn-current",
                "content": [{"type": "text", "text": "RESPONSE_OUTPUT_SECRET"}],
                "internal_chat_message_metadata_passthrough": {"content_item_kinds": ["generic.developer_instructions"]},
            },
        }
        write_codex_session(
            self.home,
            self.project,
            self.thread_id,
            [user_item, token_usage_record(120), assistant_item],
        )

        result = self.collect("all")
        serialized = json.dumps(result, ensure_ascii=False)
        categories = result["runtime_context"]["categories"]

        self.assertNotIn("CURRENT_USER_SECRET", serialized)
        self.assertNotIn("RESPONSE_OUTPUT_SECRET", serialized)
        self.assertEqual(categories["current_user_message"]["status"], "UNKNOWN")
        self.assertEqual(categories["activated_skill_instructions"]["status"], "UNKNOWN")
        self.assertEqual(result["runtime_context"]["total"]["status"], "UNKNOWN")

    def test_modes_show_only_unknown_runtime_visibility_for_the_requested_area(self):
        write_codex_session(self.home, self.project, self.thread_id, [token_event(120)])
        expected = {
            "skills": {"skill_discovery_metadata", "activated_skill_instructions"},
            "tools": {"tools_mcp_definitions", "tool_results"},
            "rules": {"system_harness_instructions", "project_developer_instructions", "rules"},
        }

        for mode, wanted in expected.items():
            with self.subTest(mode=mode):
                categories = self.collect(mode)["runtime_context"]["categories"]
                self.assertEqual(set(categories), wanted)
                self.assertTrue(all(item["status"] == "UNKNOWN" for item in categories.values()))

    def test_claude_reports_runtime_request_data_as_unknown(self):
        result = self.collect(harness="claude")

        self.assertEqual(result["context_token_usage"]["status"], "UNKNOWN")
        self.assertEqual(result["runtime_context"]["status"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
