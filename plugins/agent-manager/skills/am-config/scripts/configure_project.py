# /// script
# requires-python = ">=3.12"
# dependencies = ["tomlkit>=0.13.3,<1"]
# ///
"""Explicit, transactional project switches. Never launch an Agent harness.

The calling Skill supplies current read-only discovery evidence over stdin.
Only the current Agent's project configuration is a persistent write target.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from copy import deepcopy
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import tomllib


class Blocked(ValueError):
    def __init__(self, reason: str, target: str = "", matches: list[str] | None = None,
                 changes_applied: str = "NONE"):
        super().__init__(reason)
        self.reason = reason
        self.target = target
        self.matches = matches or []
        self.changes_applied = changes_applied


# Exact runtime validated in tests/test_project_config_codex.py. Unknown versions
# fail closed; a version change needs fresh isolated loader evidence, not a guess.
VERIFIED_CODEX = "codex-cli 0.162.0-alpha.17.2"
VERIFIED_CLAUDE = "2.1.291 (Claude Code)"
VERIFIED_CODEX_VERSIONS = {VERIFIED_CODEX, "codex-cli 0.162.0-alpha.2"}
VERIFIED_CLAUDE_VERSIONS = {VERIFIED_CLAUDE, "2.1.296 (Claude Code)"}
UNSUPPORTED_CONFIG = "CODEX PROJECT-LEVEL CONFIGURATION NOT SUPPORTED"
UNSUPPORTED_CLAUDE = "CLAUDE PROJECT-LEVEL CONFIGURATION NOT SUPPORTED"
WINDOWS_ONLY = "PLUGIN SWITCH CONFIGURATION REQUIRES WINDOWS"


def require_windows_configuration() -> None:
    if os.name != "nt":
        raise Blocked(WINDOWS_ONLY)


def project_root(cwd: Path) -> Path:
    env = {key: value for key, value in os.environ.items()
           if not key.startswith("GIT_")}
    try:
        result = subprocess.run(["git", "-C", str(cwd), "rev-parse", "--show-toplevel"],
                                env=env, capture_output=True, text=True, timeout=10)
        if result.returncode or not result.stdout.strip():
            raise Blocked("PROJECT ROOT NOT FOUND")
        root = Path(result.stdout.strip()).resolve(strict=True)
        if not cwd.resolve(strict=True).is_relative_to(root):
            raise Blocked("PROJECT ROOT NOT FOUND")
        return root
    except (OSError, subprocess.TimeoutExpired) as error:
        raise Blocked("PROJECT ROOT NOT FOUND") from error


def protected_roots() -> list[Path]:
    home = Path.home()
    return [path.resolve() for path in (
        home / ".codex", home / ".agents", home / ".claude", home / ".config",
        Path(os.environ.get("CODEX_HOME", home / ".codex")),
        Path(os.environ.get("CLAUDE_CONFIG_DIR", home / ".claude")),
    )]


def safe_path(path: Path, root: Path) -> Path:
    """Canonical ancestry, including existing symlinks/junctions and hardlinks."""
    try:
        if ".." in path.parts or not path.is_absolute():
            raise Blocked("PATH ESCAPES PROJECT ROOT")
        real = path.resolve()
        if real == root or not real.is_relative_to(root):
            raise Blocked("PATH ESCAPES PROJECT ROOT")
        if any(real == forbidden or real.is_relative_to(forbidden) for forbidden in protected_roots()):
            raise Blocked("PATH ESCAPES PROJECT ROOT")
        # Even in-project redirection is unnecessary for a configuration editor.
        for component in (path, *path.parents):
            if component == root:
                break
            if component.is_symlink() or component.is_junction():
                raise Blocked("PATH ESCAPES PROJECT ROOT")
            if component.exists():
                attributes = component.lstat()
                if getattr(attributes, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                    raise Blocked("PATH ESCAPES PROJECT ROOT")
                if component == path:
                    if not (stat.S_ISREG(attributes.st_mode) or stat.S_ISDIR(attributes.st_mode)):
                        raise Blocked("CONFIG CANNOT BE SAFELY MODIFIED")
                    if stat.S_ISREG(attributes.st_mode) and attributes.st_nlink != 1:
                        raise Blocked("CONFIG CANNOT BE SAFELY MODIFIED")
        return real
    except (OSError, RuntimeError, ValueError) as error:
        if isinstance(error, Blocked):
            raise
        raise Blocked("PATH ESCAPES PROJECT ROOT") from error


def codex_version() -> str:
    try:
        result = subprocess.run(["codex", "--version"], capture_output=True, text=True, timeout=10)
        if result.returncode:
            raise Blocked(UNSUPPORTED_CONFIG)
        return result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired) as error:
        raise Blocked(UNSUPPORTED_CONFIG) from error


def claude_version() -> str:
    try:
        result = subprocess.run(["claude", "--version"], capture_output=True, text=True, timeout=10)
        if result.returncode:
            raise Blocked(UNSUPPORTED_CLAUDE)
        return result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired) as error:
        raise Blocked(UNSUPPORTED_CLAUDE) from error


def read_json(text: str) -> dict:
    """Reject duplicate keys and non-JSON numbers instead of losing user data."""
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result

    def invalid_constant(value):
        raise ValueError("Invalid JSON constant")

    document = json.loads(text, object_pairs_hook=unique, parse_constant=invalid_constant)
    if not isinstance(document, dict):
        raise ValueError("JSON object required")
    return document


def json_members(text: str) -> dict[str, tuple[int, int]]:
    """Find value spans in an already validated JSON object with the stdlib decoder."""
    decoder = json.JSONDecoder()
    position = text.index("{") + 1
    members = {}
    while True:
        while text[position].isspace():
            position += 1
        if text[position] == "}":
            return members
        key, position = decoder.raw_decode(text, position)
        while text[position].isspace():
            position += 1
        position += 1  # colon, guaranteed by read_json
        while text[position].isspace():
            position += 1
        start = position
        _, position = decoder.raw_decode(text, position)
        members[key] = (start, position)
        while text[position].isspace():
            position += 1
        if text[position] == ",":
            position += 1


def set_json_members(text: str, values: dict) -> str:
    """Change requested scalar values; preserve all other bytes and key order."""
    spans = json_members(text)
    for key, (start, end) in sorted(spans.items(), key=lambda item: item[1][0], reverse=True):
        if key in values:
            text = text[:start] + json.dumps(values[key], ensure_ascii=False) + text[end:]
    missing = {key: value for key, value in values.items() if key not in spans}
    if missing:
        # Insert before the closing brace without touching existing members.
        closing = text.rfind("}")
        insertion = closing
        while insertion > 0 and text[insertion - 1].isspace():
            insertion -= 1
        newline = "\r\n" if "\r\n" in text else "\n"
        indent = "  "
        if "\n" in text:
            for line in text.splitlines():
                if line.lstrip().startswith('"'):
                    indent = line[:len(line) - len(line.lstrip())]
                    break
        additions = ("," + newline + indent).join(
            json.dumps(key, ensure_ascii=False) + ": " + json.dumps(value, ensure_ascii=False)
            for key, value in missing.items())
        text = text[:insertion] + ("," if spans else "") + newline + indent + additions + text[insertion:]
    return text


def resolve_requests(requests: list, inventory: dict) -> list[dict]:
    """Match exact identities; names never select a preferred source."""
    targets = inventory.get("targets")
    if inventory.get("complete") is not True or not isinstance(targets, list):
        raise Blocked("TARGET INVENTORY INCOMPLETE")
    if not requests or not isinstance(requests, list):
        raise Blocked("USER EXPLICIT REQUEST REQUIRED")
    for target in targets:
        if (not isinstance(target, dict) or target.get("kind") not in {"skill", "plugin"}
                or any(not isinstance(target.get(key), str) or not target[key] for key in ("id", "name", "path"))):
            raise Blocked("TARGET INVENTORY INCOMPLETE")
    resolved = {}
    for request in requests:
        if (not isinstance(request, dict) or set(request) != {"kind", "target", "enabled"}
                or request["kind"] not in {"skill", "plugin"}
                or not isinstance(request["target"], str) or not request["target"]
                or type(request["enabled"]) is not bool):
            raise Blocked("INVALID REQUEST")
        selector = request["target"]
        matches = [target for target in targets if target["kind"] == request["kind"]
                   and selector in {target["id"], target["name"], target["path"]}]
        if not matches:
            raise Blocked("TARGET NOT FOUND", selector)
        if len(matches) != 1:
            raise Blocked("AMBIGUOUS TARGET", selector, [f'{item["id"]} / {item["path"]}' for item in matches])
        target = matches[0]
        key = (target["kind"], target["id"])
        if key in resolved and resolved[key]["enabled"] != request["enabled"]:
            raise Blocked("CONFLICTING REQUESTS", selector)
        resolved[key] = {**target, "enabled": request["enabled"]}
    return list(resolved.values())


class CodexAdapter:
    """Current Codex supports project plugin switches, not skill filtering."""

    def validate(self, root: Path, inventory: dict, targets: list[dict]) -> None:
        actual_version = codex_version()
        if (actual_version not in VERIFIED_CODEX_VERSIONS or inventory.get("codex_version") != actual_version
                or inventory.get("project_config_active") is not True
                or inventory.get("project_overrides_effective") is not True
                or inventory.get("project_root") != str(root)):
            raise Blocked(UNSUPPORTED_CONFIG)
        for target in targets:
            if target["kind"] == "skill":
                # config/read sees this field, but skills/list proves it is ignored.
                raise Blocked(UNSUPPORTED_CONFIG, target["id"])
            if (target.get("installed") is not True
                    or target.get("configuration") != "local-marketplace"
                    or target["id"].count("@") != 1
                    or not all(target["id"].split("@"))):
                raise Blocked(UNSUPPORTED_CONFIG, target["id"])
            plugin_root = Path(target["path"])
            if not plugin_root.is_absolute() or not plugin_root.is_dir():
                raise Blocked("TARGET NOT FOUND", target["id"])
            manifests = [plugin_root / "plugin.json", plugin_root / ".codex-plugin/plugin.json"]
            manifest = next((path for path in manifests if path.is_file()), None)
            try:
                if manifest is None or json.loads(manifest.read_text(encoding="utf-8"))["name"] != target["id"].split("@")[0]:
                    raise Blocked("TARGET NOT FOUND", target["id"])
            except (OSError, ValueError, KeyError, TypeError) as error:
                if isinstance(error, Blocked):
                    raise
                raise Blocked("TARGET NOT FOUND", target["id"]) from error

    def plan(self, original: bytes, targets: list[dict]) -> tuple[bytes, dict]:
        try:
            import tomlkit
        except ImportError as error:
            raise Blocked("EDITOR DEPENDENCY UNAVAILABLE") from error
        try:
            text = original.decode("utf-8")
            baseline = tomllib.loads(text)
            document = tomlkit.parse(text)
            if document.as_string() != text:
                raise Blocked("CONFIG CANNOT BE SAFELY MODIFIED")
            expected = deepcopy(baseline)
            plugins = document.get("plugins")
            if plugins is None:
                document.add("plugins", tomlkit.table())
                plugins = document["plugins"]
            if not isinstance(expected.setdefault("plugins", {}), dict):
                raise Blocked("CONFIG CANNOT BE SAFELY MODIFIED")
            for target in targets:
                identifier = target["id"]
                if identifier not in plugins:
                    plugins.add(identifier, tomlkit.table())
                entry = plugins[identifier]
                expected_entry = expected["plugins"].setdefault(identifier, {})
                if not isinstance(expected_entry, dict):
                    raise Blocked("CONFIG CANNOT BE SAFELY MODIFIED")
                if "enabled" in expected_entry and type(expected_entry["enabled"]) is not bool:
                    raise Blocked("CONFIG CANNOT BE SAFELY MODIFIED")
                entry["enabled"] = target["enabled"]
                expected_entry["enabled"] = target["enabled"]
            planned = document.as_string().encode("utf-8")
            if tomllib.loads(planned.decode("utf-8")) != expected:
                raise Blocked("CONFIG CANNOT BE SAFELY MODIFIED")
            return planned, expected
        except (ValueError, TypeError, KeyError, AttributeError) as error:
            if isinstance(error, Blocked):
                raise
            raise Blocked("CONFIG CANNOT BE SAFELY MODIFIED") from error


class ClaudeAdapter:
    """Verified Claude Code enabledPlugins in shared project settings."""

    def validate(self, root: Path, inventory: dict, targets: list[dict]) -> None:
        actual_version = claude_version()
        if (actual_version not in VERIFIED_CLAUDE_VERSIONS or inventory.get("claude_version") != actual_version
                or inventory.get("project_config_active") is not True
                or inventory.get("project_overrides_effective") is not True
                or inventory.get("project_root") != str(root)):
            raise Blocked(UNSUPPORTED_CLAUDE)
        # This higher project layer must not silently override the edited value.
        local = root / ".claude/settings.local.json"
        safe_path(local, root)
        try:
            local_settings = read_json(local.read_text(encoding="utf-8")) if local.exists() else {}
            switches = local_settings.get("enabledPlugins", {})
            if not isinstance(switches, dict):
                raise ValueError("Invalid enabledPlugins")
            for target in targets:
                if (target["kind"] != "plugin" or target.get("installed") is not True
                        or target.get("configuration") != "marketplace"
                        or target["id"].count("@") != 1 or not all(target["id"].split("@"))):
                    raise Blocked(UNSUPPORTED_CLAUDE, target["id"])
                if target["id"] in switches and switches[target["id"]] is not target["enabled"]:
                    raise Blocked("CLAUDE LOCAL SETTINGS OVERRIDE PROJECT", target["id"])
                plugin_root = Path(target["path"])
                manifest = plugin_root / ".claude-plugin/plugin.json"
                if (not plugin_root.is_absolute() or not manifest.is_file()
                        or read_json(manifest.read_text(encoding="utf-8")).get("name") != target["id"].split("@")[0]):
                    raise Blocked("TARGET NOT FOUND", target["id"])
        except (OSError, ValueError, TypeError) as error:
            if isinstance(error, Blocked):
                raise
            raise Blocked("CONFIG CANNOT BE SAFELY MODIFIED") from error

    def plan(self, original: bytes, targets: list[dict]) -> tuple[bytes, dict]:
        try:
            text = original.decode("utf-8") if original else "{\n}\n"
            baseline = read_json(text)
            expected = deepcopy(baseline)
            switches = expected.setdefault("enabledPlugins", {})
            if not isinstance(switches, dict) or any(type(value) is not bool for value in switches.values()):
                raise ValueError("Invalid enabledPlugins")
            requested = {target["id"]: target["enabled"] for target in targets}
            switches.update(requested)
            spans = json_members(text)
            if "enabledPlugins" in spans:
                start, end = spans["enabledPlugins"]
                text = text[:start] + set_json_members(text[start:end], requested) + text[end:]
            else:
                text = set_json_members(text, {"enabledPlugins": requested})
            if read_json(text) != expected:
                raise ValueError("Unexpected configuration change")
            return text.encode("utf-8"), expected
        except (ValueError, TypeError, KeyError) as error:
            raise Blocked("CONFIG CANNOT BE SAFELY MODIFIED") from error


@contextmanager
def hold_directories(parent: Path):
    """On Windows deny ancestor rename/delete while validating and publishing."""
    handles = []
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        create = kernel.CreateFileW
        create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                           wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
        create.restype = wintypes.HANDLE
        close = kernel.CloseHandle
        close.argtypes = [wintypes.HANDLE]
        close.restype = wintypes.BOOL
        try:
            for directory in reversed((parent, *parent.parents)):
                # FILE_LIST_DIRECTORY participates in sharing checks; a
                # metadata-only (desired access 0) handle does not block rename.
                handle = create(str(directory), 1, 3, None, 3, 0x02000000, None)
                if handle == wintypes.HANDLE(-1).value:
                    raise Blocked("CONFIG CANNOT BE SAFELY MODIFIED")
                handles.append(handle)
            yield
        finally:
            for handle in reversed(handles):
                close(handle)
    else:
        require_windows_configuration()


def verify_config(path: Path, planned: bytes, expected: dict) -> None:
    actual = path.read_bytes()
    parsed = read_json(actual.decode("utf-8")) if path.suffix == ".json" else tomllib.loads(actual.decode("utf-8"))
    if actual != planned or parsed != expected:
        raise Blocked("CONFIG VERIFICATION FAILED")


def publish(root: Path, config: Path, original: bytes | None, planned: bytes, expected: dict) -> None:
    """One atomic replacement, optimistic concurrency check, and rollback."""
    safe_path(config, root)
    created_directory = not config.parent.exists()
    staging = None
    lock_fd = None
    # Keep the historical lock path so old and renamed Skill copies serialize together.
    lock = config.parent / ".configure-project.lock"
    replaced = False
    try:
        # Complete batch preflight already succeeded. Keep new-directory cleanup
        # separate from config rollback, so a failed operation leaves no template.
        with hold_directories(config.parent.parent):
            safe_path(config.parent, root)
            config.parent.mkdir(exist_ok=True)
            with hold_directories(config.parent):
                safe_path(config, root)
                safe_path(lock, root)
                lock_fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                current = config.read_bytes() if config.exists() else None
                if current != original:
                    raise Blocked("CONFIG CHANGED CONCURRENTLY")
                descriptor, name = tempfile.mkstemp(prefix=".am-config-", dir=config.parent)
                staging = Path(name)
                with os.fdopen(descriptor, "wb") as stream:
                    stream.write(planned)
                    stream.flush()
                    os.fsync(stream.fileno())
                if original is not None:
                    os.chmod(staging, stat.S_IMODE(config.stat().st_mode))
                safe_path(config, root)
                if (config.read_bytes() if config.exists() else None) != original:
                    raise Blocked("CONFIG CHANGED CONCURRENTLY")
                os.replace(staging, config)
                replaced = True
                try:
                    verify_config(config, planned, expected)
                except (OSError, ValueError) as error:
                    # Refuse to overwrite an unrelated concurrent writer.
                    safe_path(config, root)
                    if config.read_bytes() != planned:
                        raise Blocked("CONFIG VERIFICATION FAILED; ROLLBACK BLOCKED BY CONCURRENT CHANGE",
                                      changes_applied="UNKNOWN; CHECK PROJECT CONFIG") from error
                    if original is None:
                        config.unlink()
                    else:
                        descriptor, name = tempfile.mkstemp(prefix=".am-config-", dir=config.parent)
                        staging = Path(name)
                        with os.fdopen(descriptor, "wb") as stream:
                            stream.write(original)
                            stream.flush()
                            os.fsync(stream.fileno())
                        os.chmod(staging, stat.S_IMODE(config.stat().st_mode))
                        os.replace(staging, config)
                        if config.read_bytes() != original:
                            raise Blocked("ROLLBACK FAILED", changes_applied="UNKNOWN; CHECK PROJECT CONFIG") from error
                    replaced = False
                    raise Blocked("CONFIG VERIFICATION FAILED; ORIGINAL RESTORED") from error
    except OSError as error:
        raise Blocked("CONFIG WRITE FAILED" if not replaced else "CONFIG WRITE FAILED; CHECK PROJECT CONFIG",
                      changes_applied="UNKNOWN; CHECK PROJECT CONFIG" if replaced else "NONE") from error
    except Blocked as error:
        if replaced and error.changes_applied == "NONE":
            error.changes_applied = "UNKNOWN; CHECK PROJECT CONFIG"
        raise
    finally:
        active_error = sys.exception()
        cleanup_errors = []
        if lock_fd is not None:
            try:
                os.close(lock_fd)
            except OSError as error:
                cleanup_errors.append((lock, error))
        for temporary_path in (staging, lock if lock_fd is not None else None):
            try:
                if temporary_path is not None and temporary_path.exists():
                    safe_path(temporary_path, root)
                    temporary_path.unlink()
            except (OSError, Blocked) as error:
                cleanup_errors.append((temporary_path, error))
        try:
            if created_directory and config.parent.exists() and not any(config.parent.iterdir()):
                safe_path(config.parent, root)
                config.parent.rmdir()
        except (OSError, Blocked) as error:
            cleanup_errors.append((config.parent, error))
        if cleanup_errors:
            paths = "; ".join(dict.fromkeys(str(path) for path, _ in cleanup_errors))
            if isinstance(active_error, Blocked):
                active_error.reason += "; CLEANUP FAILED"
                active_error.target = paths
            else:
                raise Blocked("CONFIG CLEANUP FAILED; CHECK PROJECT CONFIG", target=paths,
                              changes_applied="UNKNOWN; CHECK PROJECT CONFIG" if replaced else "NONE") from cleanup_errors[0][1]


def configure(payload: dict, cwd: Path) -> dict:
    require_windows_configuration()
    if not isinstance(payload, dict) or payload.get("explicit_invocation") is not True:
        raise Blocked("USER EXPLICIT REQUEST REQUIRED")
    if payload.get("agent") not in {"codex", "claude"}:
        raise Blocked("UNSUPPORTED AGENT")
    if set(payload) != {"agent", "explicit_invocation", "scope", "requests", "inventory"} or payload["scope"] != "project":
        raise Blocked("PROJECT-ONLY CONFIGURATION REQUIRED")
    root = project_root(cwd)
    is_claude = payload["agent"] == "claude"
    config = root / (".claude/settings.json" if is_claude else ".codex/config.toml")
    safe_path(config, root)
    inventory = payload["inventory"]
    if not isinstance(inventory, dict):
        raise Blocked("TARGET INVENTORY INCOMPLETE")
    targets = resolve_requests(payload["requests"], inventory)
    adapter = ClaudeAdapter() if is_claude else CodexAdapter()
    adapter.validate(root, inventory, targets)
    try:
        if config.exists() and not config.stat().st_mode & stat.S_IWUSR:
            raise Blocked("CONFIG CANNOT BE SAFELY MODIFIED")
        original = config.read_bytes() if config.exists() else None
        if is_claude and original == b"":
            raise Blocked("CONFIG CANNOT BE SAFELY MODIFIED")
        planned, expected = adapter.plan(original or b"", targets)
        if planned != original:
            publish(root, config, original, planned, expected)
        else:
            verify_config(config, planned, expected)
    except OSError as error:
        raise Blocked("CONFIG CANNOT BE SAFELY MODIFIED") from error
    previous = (read_json((original or b"{}").decode("utf-8")).get("enabledPlugins", {}) if is_claude
                else tomllib.loads((original or b"").decode("utf-8")).get("plugins", {}))
    return {"Status": "SUCCESS", "Agent": "Claude Code" if is_claude else "Codex", "Project": str(root), "Config": str(config),
            "Changed": [f'{"ENABLE" if target["enabled"] else "DISABLE"} {target["id"]}' for target in targets
                        if (previous.get(target["id"]) if is_claude else previous.get(target["id"], {}).get("enabled")) != target["enabled"]],
            "Unchanged": "All unrequested states, comments and unrelated configuration preserved",
            "Global files modified": "NONE", "Verified": "Project configuration re-read; reload the trusted project to activate"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    args = parser.parse_args()
    try:
        require_windows_configuration()
        payload = json.load(sys.stdin)
        if project_root(args.cwd) != project_root(Path.cwd()):
            raise Blocked("PATH ESCAPES PROJECT ROOT")
        report = configure(payload, args.cwd)
    except (Blocked, ValueError, OSError, TypeError) as error:
        report = {"Status": "BLOCKED", "Reason": error.reason if isinstance(error, Blocked) else "INVALID INPUT",
                  "Changes applied": error.changes_applied if isinstance(error, Blocked) else "NONE",
                  "Global files modified": "NONE"}
        if isinstance(error, Blocked) and error.target:
            report["Target"] = error.target
        if isinstance(error, Blocked) and error.matches:
            report["Matches"] = error.matches
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["Status"] == "SUCCESS" else 2


if __name__ == "__main__":
    sys.exit(main())
