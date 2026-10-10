# /// script
# requires-python = ">=3.12"
# dependencies = ["tomlkit>=0.13.3,<0.14", "PyYAML>=6.0.2,<7"]
# ///
"""Project detection and lossless project-only edits after adapter verification.

The CLI only preflights. edit_config is called by the explicitly invoked Skill
after scope, trust, official capabilities and collateral effects are verified.
"""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import tomllib

import tomlkit
import yaml


class Blocked(ValueError):
    """Cannot safely identify or edit this project's configuration."""


PROJECT_MARKERS = (
    "package.json", "pyproject.toml", "pom.xml", "build.gradle", "build.gradle.kts",
    "Cargo.toml", "go.mod", "CMakeLists.txt", "Makefile", "composer.json",
    ".agents/plugins/marketplace.json", ".codex/config.toml", "AGENTS.md",
)


def user_config() -> Path:
    return Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "config.toml"


def project_root(cwd: Path) -> Path:
    cwd = cwd.resolve(strict=True)
    if not cwd.is_dir():
        raise Blocked("该 Skill 只能在项目目录中执行。")
    try:
        result = subprocess.run(
            ["git", "-C", str(cwd), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, encoding="utf-8", timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        result = None
    if result is not None and result.returncode == 0:
        candidate = Path(result.stdout.strip()).resolve()
    else:
        candidate = next((directory for directory in (cwd, *cwd.parents)
                          if any((directory / marker).is_file() for marker in PROJECT_MARKERS)
                          or any(directory.glob("*.sln")) or any(directory.glob("*.csproj"))), None)
    if candidate is None or candidate in {Path.home().resolve(), user_config().parent.resolve()}:
        raise Blocked("该 Skill 只能在项目目录中执行。")
    return candidate


def config_path(project: Path) -> Path:
    project = project.resolve(strict=True)
    if project_root(project) != project:
        raise Blocked("Expected a recognized project root")
    target = project / ".codex" / "config.toml"
    if target.resolve() != target.absolute() or target.resolve() == user_config().resolve():
        raise Blocked("Project config is redirected or points to user/global config")
    if target.exists() and not target.is_file():
        raise Blocked("Project config is not a regular file")
    return target


def read_document(content: bytes):
    try:
        text = content.decode("utf-8")
        return tomlkit.parse(text), tomllib.loads(text)
    except (UnicodeError, ValueError, tomlkit.exceptions.ParseError) as error:
        raise Blocked("Project TOML cannot be safely parsed") from error


def plugin_disable_update(plugin_id: str, plugin_root: Path, losing_skills: set[str]) -> dict[str, bool]:
    """Reject whole-Plugin disable when other capabilities would be lost."""
    plugin_root = plugin_root.resolve(strict=True)
    manifest = json.loads((plugin_root / "plugin.json").read_text(encoding="utf-8"))
    if manifest.get("name") != plugin_id.split("@", 1)[0]:
        raise Blocked("Plugin identity differs from the scanned source")
    extension = manifest.get("extensions", {}).get("com.openai", {})
    if any(key in extension or key in manifest for key in ("hooks", "apps", "mcpServers", "skills")) or any(
        (plugin_root / path).exists() for path in ("mcp.json", ".mcp.json", ".app.json", "hooks", ".codex-plugin")
    ):
        raise Blocked("Plugin has additional or custom capabilities; cannot safely disable it")
    names = []
    for entry in (plugin_root / "skills").glob("*/SKILL.md"):
        text = entry.read_text(encoding="utf-8-sig").splitlines()
        if not text or text[0] != "---" or "---" not in text[1:]:
            raise Blocked("Malformed Skill entry")
        metadata = yaml.safe_load("\n".join(text[1:text.index("---", 1)]))
        if not isinstance(metadata, dict) or not isinstance(metadata.get("name"), str):
            raise Blocked("Missing Skill name")
        names.append(metadata["name"])
    if not names or len(names) != len(set(names)) or set(names) != losing_skills:
        raise Blocked(f"Plugin-level disable would lose unrelated Skills: {', '.join(sorted(set(names) - losing_skills)) or 'incomplete inventory'}")
    return {plugin_id: False}


def edit_config(project: Path, *, plugin_updates: dict[str, bool] | None = None,
                skill_updates: dict[str, bool] | None = None) -> bool:
    """Incrementally edit verified targets; preserve every unrelated TOML value.

    This low-level editor does not infer winners or grant trust. The Skill must
    verify the installed Harness accepts these overrides before calling it.
    """
    target = config_path(project)
    original = target.read_bytes() if target.exists() else b""
    existed = target.exists()
    global_path = user_config()
    global_before = global_path.read_bytes() if global_path.exists() else None
    document, before = read_document(original)
    expected = copy.deepcopy(before)
    for plugin_id, enabled in (plugin_updates or {}).items():
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*@[a-zA-Z0-9][a-zA-Z0-9_.-]*", plugin_id) or type(enabled) is not bool:
            raise Blocked("Invalid Plugin identity or enabled value")
        if "plugins" not in document:
            document["plugins"] = tomlkit.table()
        plugins = document["plugins"]
        if not isinstance(plugins, tomlkit.items.Table):
            raise Blocked("Unsupported inline/dotted Plugin structure")
        if plugin_id not in plugins:
            plugins[plugin_id] = tomlkit.table()
        if not isinstance(plugins[plugin_id], tomlkit.items.Table):
            raise Blocked("Unsupported inline Plugin entry")
        plugins[plugin_id]["enabled"] = enabled
        expected.setdefault("plugins", {}).setdefault(plugin_id, {})["enabled"] = enabled
    for skill_path, enabled in (skill_updates or {}).items():
        if not Path(skill_path).is_absolute() or not Path(skill_path).exists() or type(enabled) is not bool:
            raise Blocked("Skill override needs an existing absolute loader path and a boolean")
        if "skills" not in document:
            document["skills"] = tomlkit.table()
        skills = document["skills"]
        if not isinstance(skills, tomlkit.items.Table):
            raise Blocked("Unsupported skills structure")
        if "config" not in skills:
            skills["config"] = tomlkit.aot()
        entries = skills["config"]
        if not isinstance(entries, tomlkit.items.AoT):
            raise Blocked("Unsupported inline skills.config structure")
        matches = [entry for entry in entries if entry.get("path") == skill_path]
        if len(matches) > 1:
            raise Blocked("Ambiguous duplicate skills.config path")
        if not matches:
            entry = tomlkit.table()
            entry["path"] = skill_path
            entries.append(entry)
        else:
            entry = matches[0]
        entry["enabled"] = enabled
        expected_entries = expected.setdefault("skills", {}).setdefault("config", [])
        expected_matches = [item for item in expected_entries if item.get("path") == skill_path]
        if expected_matches:
            expected_matches[0]["enabled"] = enabled
        else:
            expected_entries.append({"path": skill_path, "enabled": enabled})
    updated = tomlkit.dumps(document).encode("utf-8")
    if read_document(updated)[1] != expected:
        raise Blocked("Unexpected unrelated configuration change")
    if updated == original:
        return False
    # Recheck redirects and concurrent edits immediately before publishing.
    config_path(project)
    if target.exists() != existed or (target.read_bytes() if existed else b"") != original:
        raise Blocked("Project config changed during planning")
    if (global_path.read_bytes() if global_path.exists() else None) != global_before:
        raise Blocked("User config changed during planning; rescan effective state")
    target.parent.mkdir(exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, prefix=".agent-config-", delete=False) as output:
            temporary = Path(output.name)
            output.write(updated)
            output.flush()
            os.fsync(output.fileno())
        if existed:
            os.chmod(temporary, target.stat().st_mode)
        config_path(project)
        if target.exists() != existed or (target.read_bytes() if existed else b"") != original:
            raise Blocked("Concurrent project config edit; no changes applied")
        os.replace(temporary, target)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    if target.read_bytes() != updated or read_document(target.read_bytes())[1] != expected:
        raise Blocked("Post-write verification failed; inspect project config before continuing")
    if (global_path.read_bytes() if global_path.exists() else None) != global_before:
        raise Blocked("User config changed externally; effective state must be rechecked")
    return True


if __name__ == "__main__":
    try:
        root = project_root(Path.cwd())
        target = config_path(root)
        read_document(target.read_bytes() if target.exists() else b"")
        print(f"Project: {root}\nConfig: {target}\nPreflight: OK (read-only)")
    except (Blocked, OSError) as error:
        raise SystemExit(f"BLOCKED\nReason: {error}")
