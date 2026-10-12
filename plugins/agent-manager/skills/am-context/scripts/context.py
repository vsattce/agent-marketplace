"""Inspect the latest reported request usage for the current Codex thread."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Callable, TextIO


MODES = {"summary", "all", "skills", "tools", "rules"}
MAX_SESSION_BYTES = 64 * 1024 * 1024
MAX_SESSION_FILES = 1_000
THREAD_ID_RE = re.compile(r"^[A-Za-z0-9-]{1,128}$")

_CATEGORY_REASONS = {
    "conversation_history": "The persisted history does not identify the complete subset sent in this request.",
    "current_user_message": "A user message record alone does not prove membership in the latest request.",
    "system_harness_instructions": "The complete system and Harness request payload is not exposed.",
    "project_developer_instructions": "The complete developer instruction payload is not exposed.",
    "rules": "A rule file on disk does not prove that its contents entered this request.",
    "skill_discovery_metadata": "Available Skill listings do not prove which metadata entered this request.",
    "activated_skill_instructions": "A Skill invocation or file does not prove that its full instructions entered this request.",
    "tools_mcp_definitions": "The complete tool and MCP definitions sent in this request are not exposed.",
    "tool_results": "Tool results may be absent or truncated in persisted history and cannot be counted as complete input.",
    "compaction_summary": "Compaction records do not expose a complete latest-request input snapshot.",
    "other_runtime_content": "Other runtime framing and hidden content are not exposed as request members.",
}

_MODE_CATEGORIES = {
    "all": tuple(_CATEGORY_REASONS),
    "skills": ("skill_discovery_metadata", "activated_skill_instructions"),
    "tools": ("tools_mcp_definitions", "tool_results"),
    "rules": ("system_harness_instructions", "project_developer_instructions", "rules"),
}


def _normalize_path(path: str) -> str | None:
    value = os.path.expanduser(path.strip())
    if value.startswith("\\\\?\\UNC\\"):
        value = "\\\\" + value[8:]
    elif value.startswith("\\\\?\\"):
        value = value[4:]
    try:
        return os.path.normcase(os.path.normpath(os.path.abspath(value)))
    except (OSError, ValueError):
        return None


def _session_files(home: Path, thread_id: str) -> tuple[list[Path], bool]:
    """Locate filenames for one exact thread without opening other session files."""
    sessions = home / "sessions"
    if not sessions.is_dir():
        return [], False
    matches: list[Path] = []
    visited = 0
    partial = False
    stack = [(sessions, 0)]
    while stack:
        directory, depth = stack.pop()
        try:
            with os.scandir(directory) as iterator:
                entries = list(iterator)
        except OSError:
            partial = True
            continue
        for entry in entries:
            visited += 1
            if visited > MAX_SESSION_FILES:
                return matches, True
            try:
                if entry.is_symlink():
                    continue
                if entry.is_dir(follow_symlinks=False) and depth < 3:
                    stack.append((Path(entry.path), depth + 1))
                elif entry.is_file(follow_symlinks=False) and entry.name.endswith(".jsonl"):
                    stem = entry.name[:-6]
                    if stem == thread_id or stem.endswith("-" + thread_id):
                        matches.append(Path(entry.path))
            except OSError:
                partial = True
    return matches, partial


def _unknown_usage(
    reason: str = "No usable measurement is available for the latest reported request.",
    availability: str = "UNAVAILABLE",
) -> dict[str, Any]:
    return {
        "status": "UNKNOWN",
        "availability": availability,
        "input_tokens": None,
        "window_tokens": None,
        "remaining_approx": None,
        "remaining_approx_status": "UNKNOWN",
        "usage_percent_approx": None,
        "usage_percent_approx_status": "UNKNOWN",
        "timestamp": None,
        "source": None,
        "basis": "Only per-response input usage is treated as a measured request total; no cumulative total is substituted.",
        "reason": reason,
    }


def _valid_count(value: Any, *, allow_zero: bool = True) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and (value >= 0 if allow_zero else value > 0)
    )


def _session_record_fields(record: dict[str, Any], thread_id: str) -> tuple[str, Any, Any, Any, Any]:
    """Extract only session identity, compaction markers, and per-response input usage."""
    record_type = record.get("type")
    if record_type == "session_meta":
        payload = record.get("payload")
        if isinstance(payload, dict):
            thread = payload.get("id")
            cwd = payload.get("cwd")
            return "metadata", thread if isinstance(thread, str) else None, cwd if isinstance(cwd, str) else None, None, None
        return "metadata", None, None, None, None
    if record_type == "compacted":
        return "compaction", None, None, None, None
    if record_type == "token_usage_record":
        payload = record.get("payload")
        if not isinstance(payload, dict):
            return "invalid_record", None, None, None, None
        record_thread_id = payload.get("thread_id")
        usage = payload.get("usage")
        input_tokens = usage.get("input_tokens") if isinstance(usage, dict) else None
        turn_id = payload.get("turn_id")
        timestamp = record.get("timestamp") if isinstance(record.get("timestamp"), str) else None
        if record_thread_id is not None and record_thread_id != thread_id:
            return "invalid_record", None, None, timestamp, None
        if not _valid_count(input_tokens):
            return "invalid_record", None, turn_id, timestamp, None
        return "usage_record", input_tokens, turn_id if isinstance(turn_id, str) else None, timestamp, "token_usage_record.payload.usage.input_tokens"
    if record_type != "event_msg":
        return "other", None, None, None, None
    payload = record.get("payload")
    if not isinstance(payload, dict):
        return "invalid_event", None, None, None, None
    event_type = payload.get("type")
    if not isinstance(event_type, str):
        return "invalid_event", None, None, None, None
    if event_type in {"context_compacted", "context_compaction", "context_compaction_started"}:
        return "compaction", None, None, None, None
    if event_type == "task_started":
        turn_id = payload.get("turn_id")
        window = payload.get("model_context_window")
        if not isinstance(turn_id, str) or not turn_id:
            return "task_started", None, None, None, None
        if not _valid_count(window, allow_zero=False):
            window = None
        return "task_started", turn_id, window, None, None
    if event_type != "token_count":
        return "other", None, None, None, None
    if "info" not in payload:
        return "invalid_event", None, None, None, None
    info = payload.get("info")
    # Rate-limit token_count events use info=null and do not describe a new request.
    if info is None:
        return "other", None, None, None, None
    if not isinstance(info, dict):
        return "invalid_event", None, None, None, None
    usage = info.get("last_token_usage")
    input_tokens = usage.get("input_tokens") if isinstance(usage, dict) else None
    timestamp = record.get("timestamp") if isinstance(record.get("timestamp"), str) else None
    if not _valid_count(input_tokens):
        return "invalid_event", None, None, timestamp, None
    window = info.get("model_context_window")
    if not _valid_count(window, allow_zero=False):
        window = None
    return "usage_event", input_tokens, window, timestamp, "event_msg.token_count.last_token_usage.input_tokens"


def _read_current_codex_usage(project: Path, home: Path, env: dict[str, str]) -> dict[str, Any]:
    thread_id = env.get("CODEX_THREAD_ID", "").strip()
    if not thread_id or not THREAD_ID_RE.fullmatch(thread_id):
        return _unknown_usage("CODEX_THREAD_ID is not available")
    matches, scan_partial = _session_files(home, thread_id)
    if scan_partial:
        return _unknown_usage("Current-session filename search was bounded or incomplete", "PARTIAL")
    if len(matches) != 1:
        return _unknown_usage("No unique session file matched CODEX_THREAD_ID")

    session_file = matches[0]
    try:
        if session_file.stat().st_size > MAX_SESSION_BYTES:
            return _unknown_usage("Current-session file exceeds the read limit", "PARTIAL")
        with session_file.open("rb") as source:
            total = 0
            first_line = source.readline()
            total += len(first_line)
            try:
                first_record = json.loads(first_line)
            except (UnicodeDecodeError, json.JSONDecodeError, RecursionError):
                return _unknown_usage("Current-session metadata could not be read", "PARTIAL")
            if not isinstance(first_record, dict):
                return _unknown_usage("Current-session metadata could not be read", "PARTIAL")
            record_kind, metadata_id, metadata_cwd, _, _ = _session_record_fields(first_record, thread_id)
            del first_record
            if record_kind != "metadata" or metadata_id != thread_id:
                return _unknown_usage("Session metadata did not confirm the exact current thread", "UNKNOWN")
            if not isinstance(metadata_cwd, str) or _normalize_path(metadata_cwd) != _normalize_path(str(project)):
                return _unknown_usage("Session cwd did not match the current project", "UNKNOWN")

            metadata_count = 1
            turn_windows: dict[str, int | None] = {}
            seen_task_started: set[str] = set()
            latest_usage: tuple[int, str, str | None, int | None, str | None, str] | None = None
            saw_usage_report = False
            latest_invalid_availability: str | None = None
            for line in source:
                total += len(line)
                if total > MAX_SESSION_BYTES:
                    return _unknown_usage("Current-session file exceeds the read limit", "PARTIAL")
                try:
                    record = json.loads(line)
                except (UnicodeDecodeError, json.JSONDecodeError, RecursionError):
                    return _unknown_usage("Current-session file contains an unreadable event", "PARTIAL")
                if not isinstance(record, dict):
                    return _unknown_usage("Current-session event has an invalid record shape", "PARTIAL")
                record_kind, first, second, third, fourth = _session_record_fields(record, thread_id)
                del record
                if record_kind == "metadata":
                    metadata_count += 1
                elif record_kind == "compaction":
                    turn_windows.clear()
                    seen_task_started.clear()
                    latest_usage = None
                    saw_usage_report = False
                    latest_invalid_availability = None
                elif record_kind == "task_started" and isinstance(first, str):
                    if first in seen_task_started:
                        # Repeated starts can mean reroute or a changed runtime window.
                        turn_windows[first] = None
                        if latest_usage is not None and latest_usage[1] == "record" and latest_usage[2] == first:
                            input_tokens, report_kind, turn_id, _, timestamp, source_name = latest_usage
                            latest_usage = (input_tokens, report_kind, turn_id, None, timestamp, source_name)
                    else:
                        seen_task_started.add(first)
                        turn_windows[first] = second
                elif record_kind == "usage_record":
                    saw_usage_report = True
                    window = turn_windows.get(second) if isinstance(second, str) else None
                    latest_usage = (first, "record", second, window, third, fourth)
                    latest_invalid_availability = None
                elif record_kind == "invalid_record":
                    saw_usage_report = True
                    latest_usage = None
                    latest_invalid_availability = "AVAILABLE"
                elif record_kind == "usage_event":
                    saw_usage_report = True
                    latest_usage = (first, "event", None, second, third, fourth)
                    latest_invalid_availability = None
                elif record_kind == "invalid_event":
                    saw_usage_report = True
                    latest_usage = None
                    latest_invalid_availability = "PARTIAL"
    except OSError:
        return _unknown_usage("Current-session file could not be read")

    if metadata_count != 1:
        return _unknown_usage("Session metadata was duplicated", "UNKNOWN")
    if latest_usage is None:
        reason = "No usable per-response input usage remains after compaction or invalidation checks" if saw_usage_report else "Current session has no per-response input usage event"
        return _unknown_usage(reason, latest_invalid_availability or "AVAILABLE")

    input_tokens, report_kind, turn_id, window, timestamp, source = latest_usage
    remaining = max(window - input_tokens, 0) if window is not None else None
    percentage = round(input_tokens / window * 100, 1) if window is not None else None
    return {
        "status": "MEASURED",
        "availability": "AVAILABLE",
        "input_tokens": input_tokens,
        "window_tokens": window,
        "remaining_approx": remaining,
        "remaining_approx_status": "DERIVED / APPROX" if remaining is not None else "UNKNOWN",
        "usage_percent_approx": percentage,
        "usage_percent_approx_status": "DERIVED / APPROX" if percentage is not None else "UNKNOWN",
        "timestamp": timestamp,
        "source": source,
        "window_source": "event_msg.task_started.model_context_window (matching turn_id)" if report_kind == "record" and window is not None else (
            "event_msg.token_count.info.model_context_window" if report_kind == "event" and window is not None else None
        ),
        "basis": "Input usage is the latest per-response report in session-log order; reports are not accumulated. A token_usage_record window is shown only from a task_started event with the same turn_id; remaining and percentage are derived approximations.",
    }


def _collect_token_usage(harness: str, project: Path, codex_home: Path, env: dict[str, str]) -> dict[str, Any]:
    if harness == "codex":
        return _read_current_codex_usage(project, codex_home, env)
    if harness == "claude":
        return _unknown_usage("Claude Code does not expose a confirmed latest-request usage record here")
    return _unknown_usage("Harness is not confirmed")


def _runtime_context(mode: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "status": "UNKNOWN",
        "basis": "No complete latest-request input snapshot is exposed by this runtime.",
    }
    if mode != "summary":
        names = _MODE_CATEGORIES.get(mode, _MODE_CATEGORIES["all"])
        result["categories"] = {
            name: {"status": "UNKNOWN", "tokens": None, "reason": _CATEGORY_REASONS[name]}
            for name in names
        }
        result["total"] = {"status": "UNKNOWN", "tokens": None}
    return result


def collect_context(
    mode: str,
    harness: str,
    project: str,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Read one exact current Codex session and report only confirmed request usage."""
    environment = dict(os.environ if env is None else env)
    current = Path(project).expanduser().resolve()
    codex_home = Path(environment.get("CODEX_HOME") or (Path.home() / ".codex")).expanduser()
    supported = harness in {"codex", "claude"}
    token_usage = _collect_token_usage(harness, current, codex_home, environment)
    return {
        "mode": mode,
        "harness": {"status": "FACT" if supported else "UNKNOWN", "name": harness if supported else "UNKNOWN"},
        "project": {"status": "FACT" if current.is_dir() else "UNAVAILABLE", "cwd_scope": "current"},
        "context_token_usage": token_usage,
        "runtime_context": _runtime_context(mode),
    }


USAGE = "Usage: context.py [--mode summary|all|skills|tools|rules|help] [--harness codex|claude] [--project PATH]"


def main(
    argv: list[str] | None = None,
    stdout: TextIO | None = None,
    scanner: Callable[..., dict[str, Any]] | None = None,
) -> int:
    """Parse exact modes and avoid runtime inspection for help or invalid input."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    output = stdout or sys.stdout
    values: dict[str, str] = {
        "mode": "summary",
        "harness": "unknown",
        "project": str(Path.cwd()),
    }
    allowed = {"--mode": "mode", "--harness": "harness", "--project": "project"}
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        if argument in {"-h", "--help"}:
            print(USAGE, file=output)
            return 0
        key = allowed.get(argument)
        if key is None or index + 1 >= len(arguments):
            print(USAGE, file=output)
            return 2
        values[key] = arguments[index + 1]
        index += 2

    mode = values["mode"]
    if mode == "help":
        print(USAGE, file=output)
        return 0
    if mode not in MODES:
        print(f"Unknown mode: {mode}\n{USAGE}", file=output)
        return 2
    inspect = scanner or collect_context
    result = inspect(
        mode=mode,
        harness=values["harness"],
        project=values["project"],
        env=dict(os.environ),
    )
    serialized = json.dumps(
        result,
        ensure_ascii=False,
        indent=None if mode == "summary" else 2,
        separators=(",", ":") if mode == "summary" else None,
    )
    print(serialized, file=output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
