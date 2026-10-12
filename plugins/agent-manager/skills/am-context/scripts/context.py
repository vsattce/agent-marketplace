"""Collect a bounded, read-only inventory of context sources."""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import re
import sys
import threading
import tomllib
from pathlib import Path
from typing import Any, Callable, TextIO


MODES = {"summary", "all", "skills", "tools", "rules"}
MAX_SCAN_ENTRIES = 2_000
MAX_SKILL_FILES = 400
MAX_FILE_BYTES = 512 * 1024
MAX_SESSION_BYTES = 8 * 1024 * 1024
MAX_SESSION_FILES = 1_000
MAX_TOKENIZER_CACHE_BYTES = 64 * 1024 * 1024
THREAD_ID_RE = re.compile(r"^[A-Za-z0-9-]{1,128}$")
SKILL_NAME_RE = re.compile(r"(?m)^name:\s*[\"']?([^\"'\r\n#]+)")
_TOKENIZER_CACHE_LOCK = threading.RLock()


def _read_existing_tokenizer_cache(
    blobpath: str,
    expected_hash: str | None = None,
    env: dict[str, str] | None = None,
) -> bytes:
    """Read a tiktoken cache entry without fetching or creating cache files."""
    environment = os.environ if env is None else env
    if "TIKTOKEN_CACHE_DIR" in environment:
        cache_dir = environment["TIKTOKEN_CACHE_DIR"]
    elif "DATA_GYM_CACHE_DIR" in environment:
        cache_dir = environment["DATA_GYM_CACHE_DIR"]
    else:
        temp_root = next((environment.get(name) for name in ("TMPDIR", "TEMP", "TMP")
                          if environment.get(name) and Path(os.path.expanduser(environment[name])).is_dir()), None)
        if temp_root is None:
            raise FileNotFoundError("no existing local tiktoken cache directory can be confirmed read-only")
        cache_dir = str(Path(os.path.expanduser(temp_root)) / "data-gym-cache")
    if not cache_dir:
        raise FileNotFoundError("tiktoken cache is disabled")

    cache_path = Path(os.path.expanduser(cache_dir)) / hashlib.sha1(blobpath.encode("utf-8")).hexdigest()
    if cache_path.is_symlink():
        raise OSError("tiktoken cache entry must not be a symbolic link")
    with cache_path.open("rb") as source:
        contents = source.read(MAX_TOKENIZER_CACHE_BYTES + 1)
    if len(contents) > MAX_TOKENIZER_CACHE_BYTES:
        raise ValueError("tiktoken cache entry exceeds the read limit")
    if expected_hash is not None and hashlib.sha256(contents).hexdigest() != expected_hash:
        raise ValueError("tiktoken cache entry hash does not match")
    return contents


def _estimate_with_tiktoken(content: bytes) -> int:
    """Use an installed encoder only when its BPE data is already cached locally."""
    text = content.decode("utf-8")
    tiktoken = importlib.import_module("tiktoken")
    tiktoken_load = importlib.import_module("tiktoken.load")

    with _TOKENIZER_CACHE_LOCK:
        read_file_cached = tiktoken_load.read_file_cached
        tiktoken_load.read_file_cached = _read_existing_tokenizer_cache
        try:
            encoding = tiktoken.get_encoding("o200k_base")
            return len(encoding.encode(text, disallowed_special=()))
        finally:
            tiktoken_load.read_file_cached = read_file_cached


def estimate_bytes(content: bytes) -> dict[str, Any]:
    """Estimate size with local o200k data when available, otherwise use bytes."""
    try:
        tokens = _estimate_with_tiktoken(content)
    except Exception:
        tokens = None
    if tokens is not None:
        algorithm = "tiktoken o200k_base (estimate; active model unknown)"
    else:
        tokens = len(content)
        algorithm = "UTF-8 bytes (size proxy, not a tokenizer count; tiktoken or verified local cache unavailable)"
    return {
        "status": "ESTIMATED",
        "bytes": len(content),
        "tokens": tokens,
        "algorithm": algorithm,
        "loaded": "UNKNOWN",
        "completeness": "COMPLETE",
    }


def _unknown_estimate(*, read_status: str = "UNAVAILABLE") -> dict[str, Any]:
    return {
        "status": "UNKNOWN",
        "bytes": None,
        "tokens": None,
        "algorithm": "UNAVAILABLE",
        "loaded": "UNKNOWN",
        "completeness": "PARTIAL",
        "read_status": read_status,
    }


def _estimate_read_content(content: bytes, truncated: bool, read_status: str) -> dict[str, Any]:
    if read_status != "READ":
        return _unknown_estimate(read_status=read_status)
    estimate = estimate_bytes(content)
    if truncated:
        estimate["completeness"] = "PARTIAL"
    return estimate


def _read_bytes(path: Path, limit: int = MAX_FILE_BYTES) -> tuple[bytes, bool, str]:
    try:
        with path.open("rb") as source:
            content = source.read(limit + 1)
        truncated = len(content) > limit
        return content[:limit], truncated, "READ"
    except (OSError, ValueError):
        return b"", False, "UNAVAILABLE"


def _read_toml(path: Path) -> tuple[dict[str, Any], bool]:
    if not path.is_file():
        return {}, False
    raw, truncated, status = _read_bytes(path)
    if status != "READ" or truncated:
        return {}, True
    try:
        parsed = tomllib.loads(raw.decode("utf-8"))
        return parsed, False
    except (UnicodeDecodeError, tomllib.TOMLDecodeError):
        return {}, True


def _read_json(path: Path) -> tuple[dict[str, Any], bool]:
    if not path.is_file():
        return {}, False
    raw, truncated, status = _read_bytes(path)
    if status != "READ" or truncated:
        return {}, True
    try:
        parsed = json.loads(raw.decode("utf-8"))
        return (parsed if isinstance(parsed, dict) else {}), False
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}, True


def _display_path(path: Path, project: Path, label: str) -> str:
    try:
        return path.resolve().relative_to(project.resolve()).as_posix()
    except (OSError, ValueError):
        try:
            return str(path.resolve())
        except OSError:
            return str(path.absolute())


def _project_root(project: Path) -> Path:
    current = project.resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return current


def _project_chain(root: Path, current: Path) -> list[Path]:
    root = root.resolve()
    current = current.resolve()
    try:
        relative = current.relative_to(root)
    except ValueError:
        return [current]
    chain = [root]
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        chain.append(cursor)
    return chain


def _walk_files(root: Path, *, max_depth: int = 5, suffixes: set[str] | None = None):
    """Walk a small tree without following links or visiting unbounded entries."""
    try:
        if not root.exists():
            return [], False
        if not root.is_dir():
            return [], True
    except OSError:
        return [], True
    files: list[Path] = []
    stack = [(root, 0)]
    visited = 0
    partial = False
    while stack:
        directory, depth = stack.pop()
        try:
            with os.scandir(directory) as iterator:
                entries = []
                for entry in iterator:
                    visited += 1
                    if visited > MAX_SCAN_ENTRIES:
                        partial = True
                        stack.clear()
                        break
                    entries.append(entry)
        except OSError:
            partial = True
            continue
        for entry in sorted(entries, key=lambda item: item.name.casefold(), reverse=True):
            try:
                if entry.is_symlink():
                    continue
                if entry.is_file(follow_symlinks=False):
                    path = Path(entry.path)
                    if suffixes is None or path.suffix.lower() in suffixes:
                        files.append(path)
                elif entry.is_dir(follow_symlinks=False) and depth < max_depth:
                    stack.append((Path(entry.path), depth + 1))
            except OSError:
                partial = True
        if len(files) > MAX_SKILL_FILES:
            files = files[:MAX_SKILL_FILES]
            partial = True
            break
    return files, partial


def _skill_segments(raw: bytes) -> tuple[bytes, bytes, str | None]:
    """Split optional YAML frontmatter while preserving an exact byte partition."""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return b"", raw, None
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return b"", raw, None
    closing = next((index for index in range(1, len(lines)) if lines[index].strip() == "---"), None)
    if closing is None:
        return b"", raw, None
    metadata_text = "".join(lines[:closing + 1])
    body_text = "".join(lines[closing + 1:])
    match = SKILL_NAME_RE.search(metadata_text)
    name = match.group(1).strip() if match else None
    return metadata_text.encode("utf-8"), body_text.encode("utf-8"), name


def _skill_item(path: Path, root: Path, source_kind: str, source_label: str) -> dict[str, Any]:
    raw, truncated, read_status = _read_bytes(path)
    metadata, body, frontmatter_name = _skill_segments(raw)
    metadata_estimate = _estimate_read_content(metadata, truncated, read_status)
    body_estimate = _estimate_read_content(body, truncated, read_status)
    item = {
        "name": frontmatter_name or path.parent.name,
        "path": _display_path(path, root, source_label),
        "source": source_label,
        "source_kind": source_kind,
        "metadata": metadata_estimate,
        "body": body_estimate,
        "loaded": "UNKNOWN",
        "content_status": "PARTIAL" if truncated else read_status,
    }
    return item


def _discover_skills(project: Path, root: Path, harness: str, env: dict[str, str]) -> dict[str, Any]:
    candidates: list[tuple[Path, str, str]] = []
    roots: list[tuple[Path, str, str]] = []
    for directory in _project_chain(root, project):
        roots.append((directory / ".agents" / "skills", "standalone", "project"))
        if harness == "claude":
            roots.append((directory / ".claude" / "skills", "standalone", "project"))
    if harness == "claude":
        claude_home = Path(env.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude"))
        roots.append((claude_home / "skills", "standalone", "claude-user"))
    elif harness == "codex":
        roots.append((Path(env.get("CODEX_HOME") or (Path.home() / ".codex")) / "skills", "standalone", "codex-user"))
        roots.append((Path.home() / ".agents" / "skills", "standalone", "user"))

    partial = False
    for skills_root, source_kind, label in roots:
        files, tree_partial = _walk_files(skills_root, max_depth=3, suffixes={".md"})
        partial = partial or tree_partial
        for path in files:
            if path.name.lower() == "skill.md":
                candidates.append((path, source_kind, label))

    # Project plugin Skills are reported as plugin-provided sources, not as standalone installs.
    plugins_root = root / "plugins"
    if plugins_root.is_dir():
        try:
            plugin_dirs = sorted((path for path in plugins_root.iterdir() if path.is_dir() and not path.is_symlink()), key=lambda path: path.name.casefold())
        except OSError:
            plugin_dirs = []
            partial = True
        if len(plugin_dirs) > 100:
            partial = True
        for plugin_dir in plugin_dirs[:100]:
            skill_files, tree_partial = _walk_files(plugin_dir / "skills", max_depth=4, suffixes={".md"})
            partial = partial or tree_partial
            candidates.extend((path, "plugin", f"plugin:{plugin_dir.name}") for path in skill_files if path.name.lower() == "skill.md")

    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path, source_kind, label in candidates[:MAX_SKILL_FILES]:
        key = os.path.normcase(str(path.resolve()))
        if key in seen:
            continue
        seen.add(key)
        item = _skill_item(path, root, source_kind, label)
        partial = partial or item["content_status"] != "READ"
        items.append(item)
    if len(candidates) > MAX_SKILL_FILES:
        partial = True
    return {"status": "PARTIAL" if partial else "COMPLETE", "items": items, "loaded": "UNKNOWN"}


def _rule_item(path: Path, project: Path, source: str, scope: str, limit: int = MAX_FILE_BYTES) -> dict[str, Any]:
    raw, truncated, read_status = _read_bytes(path, limit)
    estimate = _estimate_read_content(raw, truncated, read_status)
    return {
        "path": _display_path(path, project, source),
        "source": source,
        "scope": scope,
        "content_status": "PARTIAL" if truncated else read_status,
        "bytes": len(raw) if read_status == "READ" else None,
        "estimate": estimate,
        "loaded": "UNKNOWN",
    }


def _nonempty_file(path: Path, limit: int) -> tuple[bool, bool]:
    raw, truncated, status = _read_bytes(path, limit)
    if status != "READ":
        return False, True
    if truncated:
        # Do not select a lower-priority file when the preferred file cannot be fully checked.
        return True, True
    return bool(raw.strip()), truncated


def _codex_rules(project: Path, root: Path, home: Path, chain: list[Path]) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    partial = False
    global_selected: Path | None = None
    for name in ("AGENTS.override.md", "AGENTS.md"):
        candidate = home / name
        if not candidate.is_file():
            continue
        nonempty, issue = _nonempty_file(candidate, MAX_FILE_BYTES)
        partial = partial or issue
        if nonempty or issue:
            global_selected = candidate
            break
    if global_selected is not None:
        item = _rule_item(global_selected, root, "codex-user", "global")
        partial = partial or item["content_status"] != "READ"
        items.append(item)

    config, config_partial = _read_toml(home / "config.toml")
    partial = partial or config_partial
    fallback = config.get("project_doc_fallback_filenames", [])
    if not isinstance(fallback, list) or not all(isinstance(value, str) for value in fallback):
        fallback = []
        partial = True
    max_bytes = config.get("project_doc_max_bytes", MAX_FILE_BYTES)
    if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes < 1:
        max_bytes = MAX_FILE_BYTES
    max_bytes = min(max_bytes, MAX_FILE_BYTES)

    for directory in chain:
        selected: Path | None = None
        for name in ["AGENTS.override.md", "AGENTS.md", *fallback]:
            candidate = directory / name
            if not candidate.is_file():
                continue
            nonempty, issue = _nonempty_file(candidate, max_bytes)
            partial = partial or issue
            if nonempty or issue:
                selected = candidate
                break
        if selected is not None:
            item = _rule_item(selected, root, "codex-project", "project", max_bytes)
            partial = partial or item["content_status"] != "READ"
            items.append(item)
    return {
        "status": "PARTIAL" if partial else "COMPLETE",
        "items": items,
        "selection": "Codex lists the first non-empty file at each project level: AGENTS.override.md, AGENTS.md, then configured fallback names; global priority is AGENTS.override.md then AGENTS.md.",
        "loaded": "UNKNOWN",
    }


def _claude_rules(project: Path, root: Path, home: Path, chain: list[Path]) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    partial = False
    global_main = home / "CLAUDE.md"
    if global_main.is_file():
        item = _rule_item(global_main, root, "claude-user", "global")
        partial = partial or item["content_status"] != "READ"
        items.append(item)
    global_rules, walk_partial = _walk_files(home / "rules", max_depth=3, suffixes={".md"})
    partial = partial or walk_partial
    for path in global_rules:
        item = _rule_item(path, root, "claude-user", "global rule")
        partial = partial or item["content_status"] != "READ"
        items.append(item)

    for directory in chain:
        for candidate in (directory / "CLAUDE.md", directory / "CLAUDE.local.md", directory / ".claude" / "CLAUDE.md"):
            if candidate.is_file():
                item = _rule_item(candidate, root, "claude-project", "project / inherited")
                partial = partial or item["content_status"] != "READ"
                items.append(item)
        rules_root = directory / ".claude" / "rules"
        rule_files, tree_partial = _walk_files(rules_root, max_depth=3, suffixes={".md"})
        partial = partial or tree_partial
        for path in rule_files:
            item = _rule_item(path, root, "claude-project", "conditional scope may apply")
            partial = partial or item["content_status"] != "READ"
            items.append(item)

    # AGENTS.md support depends on the installed Claude Code version and effective settings.
    for directory in chain:
        candidate = directory / "AGENTS.md"
        if candidate.is_file():
            item = _rule_item(candidate, root, "claude-compatible-candidate", "version / settings dependent")
            partial = partial or item["content_status"] != "READ"
            items.append(item)
    return {
        "status": "PARTIAL" if partial else "COMPLETE",
        "items": items,
        "selection": "Claude sources are listed by scope; conditional rules and AGENTS.md compatibility depend on client version and settings.",
        "loaded": "UNKNOWN",
    }


def _codex_configs(project: Path, home: Path) -> list[tuple[Path, str, dict[str, Any]]]:
    configs = []
    for path, source in ((home / "config.toml", "codex-user"), (project / ".codex" / "config.toml", "codex-project")):
        if path.is_file():
            parsed, partial = _read_toml(path)
            configs.append((path, source, {"_parse_partial": partial, **parsed}))
    return configs


def _claude_settings(project: Path, home: Path) -> list[tuple[Path, str, dict[str, Any]]]:
    paths = (
        (home / "settings.json", "claude-user"),
        (project / ".claude" / "settings.json", "claude-project"),
        (project / ".claude" / "settings.local.json", "claude-project-local"),
    )
    settings = []
    for path, source in paths:
        if path.is_file():
            parsed, partial = _read_json(path)
            settings.append((path, source, {"_parse_partial": partial, **parsed}))
    return settings


def _source_file_item(
    path: Path,
    project: Path,
    source: str,
    kind: str,
    *,
    parse_partial: bool = False,
) -> dict[str, Any]:
    raw, truncated, read_status = _read_bytes(path)
    estimate = _estimate_read_content(raw, truncated, read_status)
    partial = parse_partial or truncated or read_status != "READ"
    return {
        "path": _display_path(path, project, source),
        "source": source,
        "kind": kind,
        "status": "PARTIAL" if partial else "COMPLETE",
        "content_status": "PARTIAL" if truncated else read_status,
        "estimate": estimate,
        "loaded": "UNKNOWN",
    }


def _collect_plugins(root: Path, harness: str, home: Path) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    files: list[dict[str, Any]] = []
    seen_files: set[str] = set()
    partial = False

    def add_file(path: Path, source: str, kind: str, parse_partial: bool = False) -> None:
        nonlocal partial
        key = os.path.normcase(str(path.resolve()))
        if key in seen_files:
            return
        seen_files.add(key)
        file_item = _source_file_item(path, root, source, kind, parse_partial=parse_partial)
        files.append(file_item)
        partial = partial or file_item["status"] != "COMPLETE"

    catalog_paths = [root / ".agents" / "plugins" / "marketplace.json", root / ".claude-plugin" / "marketplace.json"]
    for catalog in catalog_paths:
        if not catalog.is_file():
            continue
        parsed, parse_partial = _read_json(catalog)
        partial = partial or parse_partial
        add_file(catalog, "project", "plugin_metadata", parse_partial)
        for plugin in parsed.get("plugins", []) if isinstance(parsed.get("plugins"), list) else []:
            if isinstance(plugin, dict) and isinstance(plugin.get("name"), str):
                items.append({"name": plugin["name"], "source": _display_path(catalog, root, "project"), "evidence": "catalog entry", "loaded": "UNKNOWN"})

    plugins_root = root / "plugins"
    if plugins_root.is_dir():
        try:
            plugin_dirs = sorted((path for path in plugins_root.iterdir() if path.is_dir() and not path.is_symlink()), key=lambda path: path.name.casefold())
        except OSError:
            plugin_dirs = []
            partial = True
        if len(plugin_dirs) > 100:
            partial = True
        for plugin_dir in plugin_dirs[:100]:
            manifests = (plugin_dir / "plugin.json", plugin_dir / ".claude-plugin" / "plugin.json")
            for manifest in manifests:
                if not manifest.is_file():
                    continue
                parsed, parse_partial = _read_json(manifest)
                partial = partial or parse_partial
                add_file(manifest, "project", "plugin_metadata", parse_partial)
                name = parsed.get("name") if isinstance(parsed.get("name"), str) else plugin_dir.name
                items.append({"name": name, "source": _display_path(manifest, root, "project"), "evidence": "source manifest", "loaded": "UNKNOWN"})

    settings = _codex_configs(root, home) if harness == "codex" else _claude_settings(root, home)
    for path, source, config in settings:
        partial = partial or bool(config.get("_parse_partial"))
        add_file(path, source, "known_project_config", bool(config.get("_parse_partial")))
        if harness == "codex":
            plugins = config.get("plugins", {})
            if isinstance(plugins, dict):
                for name, value in plugins.items():
                    if not isinstance(value, dict):
                        partial = True
                        evidence = "configured enabled=UNKNOWN"
                    elif "enabled" not in value:
                        evidence = "configured"
                    elif type(value["enabled"]) is bool:
                        evidence = f"configured enabled={str(value['enabled']).lower()}"
                    else:
                        partial = True
                        evidence = "configured enabled=UNKNOWN"
                    items.append({"name": str(name), "source": _display_path(path, root, source), "evidence": evidence, "loaded": "UNKNOWN"})
            elif "plugins" in config:
                partial = True
        else:
            plugins = config.get("enabledPlugins", {})
            if isinstance(plugins, dict):
                for name, enabled in plugins.items():
                    if type(enabled) is bool:
                        evidence = f"configured enabled={str(enabled).lower()}"
                    else:
                        partial = True
                        evidence = "configured enabled=UNKNOWN"
                    items.append({"name": str(name), "source": _display_path(path, root, source), "evidence": evidence, "loaded": "UNKNOWN"})
            elif "enabledPlugins" in config:
                partial = True

    if harness == "claude":
        mcp_config = root / ".mcp.json"
        if mcp_config.is_file():
            _, parse_partial = _read_json(mcp_config)
            partial = partial or parse_partial
            add_file(mcp_config, "claude-project-mcp", "known_project_config", parse_partial)

    deduplicated = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        key = (item["name"], item["source"])
        if key not in seen:
            seen.add(key)
            deduplicated.append(item)
    return {
        "status": "PARTIAL" if partial else "COMPLETE",
        "items": deduplicated,
        "files": files,
        "loaded": "UNKNOWN",
    }


def _mcp_names_from_json(config: dict[str, Any]) -> list[str]:
    servers = config.get("mcpServers", {})
    return [name for name in servers if isinstance(name, str)] if isinstance(servers, dict) else []


def _collect_tools(project: Path, root: Path, harness: str, home: Path) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    partial = False
    if harness == "codex":
        sources = _codex_configs(project, home)
        for path, source, config in sources:
            partial = partial or bool(config.get("_parse_partial"))
            servers = config.get("mcp_servers", {})
            if isinstance(servers, dict):
                items.extend({"name": name, "kind": "MCP", "source": _display_path(path, root, source), "configured": "FACT", "available": "UNKNOWN"}
                             for name in servers if isinstance(name, str))
    elif harness == "claude":
        config_roots = _claude_settings(project, home)
        mcp_json = project / ".mcp.json"
        if mcp_json.is_file():
            parsed, parse_partial = _read_json(mcp_json)
            config_roots.append((mcp_json, "claude-project-mcp", {"_parse_partial": parse_partial, **parsed}))
        for path, source, config in config_roots:
            partial = partial or bool(config.get("_parse_partial"))
            items.extend({"name": name, "kind": "MCP", "source": _display_path(path, root, source), "configured": "FACT", "available": "UNKNOWN"}
                         for name in _mcp_names_from_json(config))
    unique: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        key = (item["name"], item["source"])
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return {
        "status": "PARTIAL" if partial else "COMPLETE",
        "items": unique,
        "session_tools": "UNKNOWN",
        "available": "UNKNOWN",
    }


def _normalize_path(path: str) -> str | None:
    value = os.path.expanduser(path.strip())
    # pathlib on Windows may render local long paths with this prefix.
    if value.startswith("\\\\?\\UNC\\"):
        value = "\\\\" + value[8:]
    elif value.startswith("\\\\?\\"):
        value = value[4:]
    try:
        return os.path.normcase(os.path.normpath(os.path.abspath(value)))
    except (OSError, ValueError):
        return None


def _session_files(home: Path, thread_id: str) -> tuple[list[Path], bool]:
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
    reason: str = "Current-session measurement is unavailable",
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
        "basis": "No usable token measurement is available for the latest reported request.",
        "reason": reason,
    }


def _session_record_fields(record: dict[str, Any]) -> tuple[str, Any, Any, Any]:
    """Extract only metadata and token-use fields from one session record."""
    record_type = record.get("type")
    if record_type == "session_meta":
        payload = record.get("payload")
        if isinstance(payload, dict):
            thread_id = payload.get("id")
            cwd = payload.get("cwd")
            return "metadata", thread_id if isinstance(thread_id, str) else None, cwd if isinstance(cwd, str) else None, None
        return "metadata", None, None, None
    if record_type == "compacted":
        return "compaction", None, None, None
    if record_type != "event_msg":
        return "other", None, None, None
    payload = record.get("payload")
    if not isinstance(payload, dict):
        return "other", None, None, None
    event_type = payload.get("type")
    if event_type in {"context_compacted", "context_compaction", "context_compaction_started"}:
        return "compaction", None, None, None
    if event_type != "token_count":
        return "other", None, None, None
    info = payload.get("info")
    usage = info.get("last_token_usage") if isinstance(info, dict) else None
    input_tokens = usage.get("input_tokens") if isinstance(usage, dict) else None
    window = info.get("model_context_window") if isinstance(info, dict) else None
    timestamp = record.get("timestamp") if isinstance(record.get("timestamp"), str) else None
    if not isinstance(input_tokens, int) or isinstance(input_tokens, bool) or input_tokens < 0:
        input_tokens = None
    if not isinstance(window, int) or isinstance(window, bool) or window <= 0:
        window = None
    return "token_count", input_tokens, window, timestamp


def _read_current_codex_usage(project: Path, home: Path, env: dict[str, str]) -> dict[str, Any]:
    thread_id = env.get("CODEX_THREAD_ID", "").strip()
    if not thread_id or not THREAD_ID_RE.fullmatch(thread_id):
        return _unknown_usage("CODEX_THREAD_ID is not available")
    matches, scan_partial = _session_files(home, thread_id)
    if scan_partial:
        return _unknown_usage("Current-session file search was bounded or incomplete", "PARTIAL")
    if len(matches) != 1:
        return _unknown_usage("No unique session file matched CODEX_THREAD_ID", "UNAVAILABLE")
    session_file = matches[0]
    try:
        if session_file.stat().st_size > MAX_SESSION_BYTES:
            return _unknown_usage("Current-session file exceeds the read limit", "PARTIAL")
        metadata_count = 0
        metadata_id: Any = None
        metadata_cwd: Any = None
        latest_usage: tuple[int, int | None, str | None] | None = None
        saw_usage_event = False
        with session_file.open("rb") as source:
            total = 0
            for line in source:
                total += len(line)
                if total > MAX_SESSION_BYTES:
                    return _unknown_usage("Current-session file exceeds the read limit", "PARTIAL")
                try:
                    record = json.loads(line)
                except (UnicodeDecodeError, json.JSONDecodeError, RecursionError):
                    return _unknown_usage("Current-session file contains an unreadable event", "PARTIAL")
                if not isinstance(record, dict):
                    del record
                    continue
                record_kind, first, second, third = _session_record_fields(record)
                del record
                if record_kind == "metadata":
                    metadata_count += 1
                    metadata_id, metadata_cwd = first, second
                elif record_kind == "compaction":
                    latest_usage = None
                elif record_kind == "token_count":
                    saw_usage_event = True
                    input_tokens, window, timestamp = first, second, third
                    if isinstance(input_tokens, int) and not isinstance(input_tokens, bool) and input_tokens >= 0:
                        valid_window = window if isinstance(window, int) and not isinstance(window, bool) and window > 0 else None
                        latest_usage = (input_tokens, valid_window, timestamp)
                    else:
                        # A newer malformed usage event invalidates older measurements.
                        latest_usage = None
    except OSError:
        return _unknown_usage("Current-session file could not be read")

    if metadata_count != 1 or metadata_id != thread_id:
        return _unknown_usage("Session metadata did not confirm the exact current thread", "UNKNOWN")
    session_cwd = metadata_cwd
    if not isinstance(session_cwd, str) or _normalize_path(session_cwd) != _normalize_path(str(project)):
        return _unknown_usage("Session cwd did not match the current project", "UNKNOWN")

    if latest_usage is None:
        reason = "No usable token_count remains after compaction and invalidation checks" if saw_usage_event else "Current session has no token usage event"
        return _unknown_usage(reason, "AVAILABLE")
    input_tokens, window, timestamp = latest_usage
    remaining = max(window - input_tokens, 0) if window is not None else None
    percentage = round(input_tokens / window * 100, 1) if window is not None else None
    return {
        "status": "MEASURED",
        "availability": "AVAILABLE",
        "input_tokens": input_tokens,
        "window_tokens": window,
        "remaining_approx": remaining,
        "remaining_approx_status": "DERIVED / APPROX" if remaining is not None else "UNAVAILABLE",
        "usage_percent_approx": percentage,
        "usage_percent_approx_status": "DERIVED / APPROX" if percentage is not None else "UNAVAILABLE",
        "timestamp": timestamp,
        "source": "exact current Codex thread; last_token_usage.input_tokens",
        "basis": "Measured input_tokens are from the latest reported request; remaining and percentage are derived approximations from that request and its reported context window.",
    }


def _collect_token_usage(harness: str, project: Path, codex_home: Path, env: dict[str, str]) -> dict[str, Any]:
    if harness == "codex":
        return _read_current_codex_usage(project, codex_home, env)
    if harness == "claude":
        return _unknown_usage("Claude Code does not expose a confirmed current-context token count here")
    return _unknown_usage("Harness is not confirmed")


def _status_summary(section: dict[str, Any]) -> dict[str, Any]:
    items = section.get("items", [])
    if section.get("status") not in {"COMPLETE", "PARTIAL"}:
        return {"status": section.get("status", "UNKNOWN"), "count": None, "source_count": None}
    names = {
        item.get("name", item.get("path"))
        for item in items
        if isinstance(item, dict) and isinstance(item.get("name", item.get("path")), str)
    } if isinstance(items, list) else set()
    return {
        "status": section.get("status", "UNKNOWN"),
        "count": len(names),
        "source_count": len(items) if isinstance(items, list) else None,
    }


def _uncollected_section(*, tools: bool = False, plugins: bool = False) -> dict[str, Any]:
    section: dict[str, Any] = {
        "status": "UNKNOWN",
        "collection": "NOT_RUN",
        "items": [],
        "loaded": "UNKNOWN",
    }
    if tools:
        section["session_tools"] = "UNKNOWN"
        section["available"] = "UNKNOWN"
    if plugins:
        section["files"] = []
    return section


def _aggregate_estimates(
    section: dict[str, Any],
    entries: list[dict[str, Any]],
    estimate_keys: tuple[str, ...] = ("estimate",),
) -> dict[str, Any]:
    if section.get("collection") == "NOT_RUN" or section.get("status") not in {"COMPLETE", "PARTIAL"}:
        return {
            "status": "UNKNOWN",
            "completeness": "UNAVAILABLE",
            "files": None,
            "estimated_files": None,
            "unavailable_files": None,
            "bytes": None,
            "tokens": None,
        }

    estimates: list[dict[str, Any]] = []
    for entry in entries:
        estimate: Any = entry
        for key in estimate_keys:
            estimate = estimate.get(key, {}) if isinstance(estimate, dict) else {}
        if isinstance(estimate, dict):
            estimates.append(estimate)
    estimated = [estimate for estimate in estimates if estimate.get("status") == "ESTIMATED"]
    unavailable_count = len(estimates) - len(estimated)
    partial = section.get("status") == "PARTIAL" or any(
        estimate.get("completeness") != "COMPLETE" for estimate in estimated
    )
    if unavailable_count:
        return {
            "status": "UNKNOWN",
            "completeness": "PARTIAL",
            "files": len(entries),
            "estimated_files": len(estimated),
            "unavailable_files": unavailable_count,
            "bytes": None,
            "tokens": None,
        }
    return {
        "status": "ESTIMATED",
        "completeness": "PARTIAL" if partial else "COMPLETE",
        "files": len(entries),
        "estimated_files": len(estimated),
        "unavailable_files": 0,
        "bytes": sum(estimate["bytes"] for estimate in estimated),
        "tokens": sum(estimate["tokens"] for estimate in estimated),
    }


def _known_breakdown(
    rules: dict[str, Any],
    skills: dict[str, Any],
    plugins: dict[str, Any],
) -> dict[str, Any]:
    plugin_files = plugins.get("files", [])
    if not isinstance(plugin_files, list):
        plugin_files = []
    categories = {
        "rules": _aggregate_estimates(rules, rules.get("items", [])),
        "skill_metadata": _aggregate_estimates(skills, skills.get("items", []), ("metadata",)),
        "skill_body": _aggregate_estimates(skills, skills.get("items", []), ("body",)),
        "plugin_metadata": _aggregate_estimates(
            plugins, [item for item in plugin_files if item.get("kind") == "plugin_metadata"]
        ),
        "known_project_config": _aggregate_estimates(
            plugins, [item for item in plugin_files if item.get("kind") == "known_project_config"]
        ),
    }
    all_collected = all(value["completeness"] != "UNAVAILABLE" for value in categories.values())
    all_known = all(value["tokens"] is not None for value in categories.values())
    total_complete = all_collected and all_known and all(
        value["completeness"] == "COMPLETE" for value in categories.values()
    )
    total = {
        "status": "ESTIMATED" if all_collected and all_known else "UNKNOWN",
        "completeness": "COMPLETE" if total_complete else "PARTIAL",
        "bytes": sum(value["bytes"] for value in categories.values()) if all_known else None,
        "tokens": sum(value["tokens"] for value in categories.values()) if all_known else None,
    }
    algorithm_set = {
        entry.get(key, {}).get("algorithm")
        for category, section, entries, key in (
            ("rules", rules, rules.get("items", []), "estimate"),
            ("skill_metadata", skills, skills.get("items", []), "metadata"),
            ("skill_body", skills, skills.get("items", []), "body"),
            ("plugin_metadata", plugins, [item for item in plugin_files if item.get("kind") == "plugin_metadata"], "estimate"),
            ("known_project_config", plugins, [item for item in plugin_files if item.get("kind") == "known_project_config"], "estimate"),
        )
        for entry in entries
        if isinstance(entry.get(key), dict) and entry[key].get("status") == "ESTIMATED"
    }
    algorithms = sorted(value for value in algorithm_set if isinstance(value, str))
    return {
        "status": total["status"],
        "completeness": total["completeness"],
        "basis": "Estimates of discovered local file contents; not actual current context contribution.",
        "categories": categories,
        "total": total,
        "algorithm": algorithms,
        "loaded": "UNKNOWN",
        "other_context": {
            "status": "UNKNOWN",
            "bytes": None,
            "tokens": None,
            "scope": "runtime, system/developer instructions, hidden tools/MCP, framing, and uncollected sources",
        },
    }


def _summary_usage(usage: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "status", "availability", "input_tokens", "window_tokens", "remaining_approx",
        "remaining_approx_status", "usage_percent_approx", "usage_percent_approx_status",
        "timestamp", "source", "basis", "reason",
    )
    return {key: usage[key] for key in keys if key in usage}


def collect_context(
    mode: str,
    harness: str,
    project: str,
    env: dict[str, str] | None = None,
    active_skill: str | None = None,
) -> dict[str, Any]:
    """Collect bounded filesystem evidence without claiming it is session-loaded."""
    environment = dict(os.environ if env is None else env)
    current = Path(project).expanduser().resolve()
    root = _project_root(current)
    chain = _project_chain(root, current)
    codex_home = Path(environment.get("CODEX_HOME") or (Path.home() / ".codex")).expanduser()
    claude_home = Path(environment.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude")).expanduser()
    supported = harness in {"codex", "claude"}
    collect_everything = mode in {"summary", "all"}
    collect_rules = collect_everything or mode == "rules"
    collect_skills = collect_everything or mode == "skills"
    collect_tools = collect_everything or mode == "tools"

    if collect_rules and supported:
        rules = _codex_rules(current, root, codex_home, chain) if harness == "codex" else _claude_rules(current, root, claude_home, chain)
    elif collect_rules:
        rules = {"status": "UNAVAILABLE", "items": [], "loaded": "UNKNOWN"}
    else:
        rules = _uncollected_section()
    skills = _discover_skills(current, root, harness, environment) if collect_skills and supported else (
        {"status": "UNAVAILABLE", "items": [], "loaded": "UNKNOWN"} if collect_skills else _uncollected_section()
    )
    source_home = codex_home if harness == "codex" else claude_home
    plugins = _collect_plugins(root, harness, source_home) if collect_tools and supported else (
        {"status": "UNAVAILABLE", "items": [], "files": [], "loaded": "UNKNOWN"} if collect_tools else _uncollected_section(plugins=True)
    )
    tools = _collect_tools(root, root, harness, source_home) if collect_tools and supported else (
        {"status": "UNAVAILABLE", "items": [], "session_tools": "UNKNOWN"} if collect_tools else _uncollected_section(tools=True)
    )
    token_usage = _collect_token_usage(harness, current, codex_home, environment)

    if active_skill:
        active_skill_evidence = {"name": active_skill, "invocation": "FACT", "loaded": "FACT"}
    else:
        active_skill_evidence = {"name": None, "invocation": "UNKNOWN", "loaded": "UNKNOWN"}
    project_info = {
        "status": "FACT" if current.is_dir() else "UNAVAILABLE",
        "path": str(current),
        "root": str(root),
        "cwd_scope": str(current),
    }
    if mode == "summary":
        project_info.pop("root")
    output: dict[str, Any] = {
        "mode": mode,
        "harness": {"status": "FACT" if supported else "UNKNOWN", "name": harness if supported else "UNKNOWN"},
        "project": project_info,
        "rules": rules,
        "skills": skills,
        "plugins": plugins,
        "tools": tools,
        "context_token_usage": token_usage,
        "active_skill": active_skill_evidence,
    }

    if mode == "summary":
        output["rules"] = _status_summary(rules)
        output["skills"] = _status_summary(skills)
        output["plugins"] = _status_summary(plugins)
        output["tools"] = _status_summary(tools)
        output["context_token_usage"] = _summary_usage(token_usage)
        output["inventory_loaded"] = "UNKNOWN"
        output["known_breakdown"] = _known_breakdown(rules, skills, plugins)
    elif mode == "all":
        output["known_breakdown"] = _known_breakdown(rules, skills, plugins)
    elif mode in {"skills", "tools", "rules"}:
        for key in ("rules", "skills", "plugins", "tools"):
            if key != mode and not (key == "plugins" and mode == "tools"):
                output[key] = _status_summary(output[key])
    return output


USAGE = "Usage: context.py [--mode all|skills|tools|rules|help] [--harness codex|claude] [--project PATH] [--active-skill NAME]"


def main(
    argv: list[str] | None = None,
    stdout: TextIO | None = None,
    scanner: Callable[..., dict[str, Any]] | None = None,
) -> int:
    """Parse a deliberately small CLI and avoid any scan on help or invalid input."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    output = stdout or sys.stdout
    values: dict[str, str] = {
        "mode": "summary",
        "harness": "unknown",
        "project": str(Path.cwd()),
        "active-skill": "",
    }
    allowed = {"--mode": "mode", "--harness": "harness", "--project": "project", "--active-skill": "active-skill"}
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
    collect = scanner or collect_context
    result = collect(
        mode=mode,
        harness=values["harness"],
        project=values["project"],
        env=dict(os.environ),
        active_skill=values["active-skill"] or None,
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
