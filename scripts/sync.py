# /// script
# requires-python = ">=3.12"
# dependencies = ["PyYAML>=6.0.2,<7"]
# ///
"""Copy the selected upstream directories; never change sources or commit Git."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

try:
    import yaml
except ImportError:
    sys.exit("Missing PyYAML. Run: uv run --script scripts/sync.py")


class SyncError(Exception):
    """A source or snapshot cannot be synchronized safely."""


# Only these explicitly generated Plugins belong to the third-party pipeline.
# Adding an owned Plugin or a sources.yaml group never grants write access.
MANAGED_PLUGINS = frozenset({"common-workflow", "software-dev", "engineering-tools"})


class UniqueKeyLoader(yaml.SafeLoader):
    """Reject duplicate YAML keys while preserving SafeLoader merge behavior."""

    def flatten_mapping(self, node):
        if isinstance(node, yaml.nodes.MappingNode):
            checked = getattr(self, "_checked_mapping_nodes", None)
            if checked is None:
                checked = self._checked_mapping_nodes = set()
            if id(node) not in checked:
                checked.add(id(node))
                seen = set()
                merge_seen = False
                for key_node, _ in node.value:
                    if key_node.tag == "tag:yaml.org,2002:merge":
                        if merge_seen:
                            raise yaml.constructor.ConstructorError(
                                "while constructing a mapping", node.start_mark,
                                "duplicate key", key_node.start_mark,
                            )
                        merge_seen = True
                        continue
                    key = self.construct_object(key_node, deep=True)
                    try:
                        duplicate = key in seen
                        seen.add(key)
                    except TypeError as error:
                        raise yaml.constructor.ConstructorError(
                            "while constructing a mapping", node.start_mark,
                            "unhashable key", key_node.start_mark,
                        ) from error
                    if duplicate:
                        raise yaml.constructor.ConstructorError(
                            "while constructing a mapping", node.start_mark,
                            "duplicate key", key_node.start_mark,
                        )
        return super().flatten_mapping(node)


def unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise SyncError("Invalid sources.lock.json: duplicate object key")
        result[key] = value
    return result


def managed_target(path: Path, root: Path) -> None:
    """Enforce the write boundary independently of sources and the lock."""
    contained(path, root)
    relative = path.relative_to(root)
    if relative.as_posix() == "sources.lock.json":
        return
    parts = relative.parts
    if len(parts) != 4 or parts[0] != "plugins" or parts[1] not in MANAGED_PLUGINS or parts[2] not in {"skills", "licenses"} or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", parts[3]):
        raise SyncError(f"Not a managed snapshot target: {relative}")
    if path.resolve() != path.absolute():
        raise SyncError(f"Managed target is redirected: {relative}")
    # Snapshot targets are directories: plugins/<group>/<kind>/<skill>.


def read_sources(root: Path) -> list[dict[str, str]]:
    try:
        document = yaml.load((root / "sources.yaml").read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
    except yaml.YAMLError as error:
        raise SyncError("Invalid sources.yaml: malformed or duplicate mapping key") from error
    if not isinstance(document, dict) or set(document) != {"groups"}:
        raise SyncError("sources.yaml must contain only a groups mapping")
    groups = document["groups"]
    if not isinstance(groups, dict) or not groups:
        raise SyncError("groups must be a non-empty mapping")
    sources = []
    names = set()
    for group, settings in groups.items():
        if not isinstance(group, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", group):
            raise SyncError(f"Invalid group: {group!r}")
        if group not in MANAGED_PLUGINS:
            raise SyncError(f"Not a managed/generated Plugin: {group!r}")
        plugin = root / "plugins" / group
        contained(plugin, root / "plugins")
        if plugin.resolve() != plugin.absolute():
            raise SyncError(f"Managed Plugin redirects outside its declared directory: {group}")
        if not (plugin / "plugin.json").is_file():
            raise SyncError(f"Missing plugins/{group}/plugin.json; create the Plugin explicitly")
        if not isinstance(settings, dict) or set(settings) != {"displayName", "skills"}:
            raise SyncError(f"{group}: expected displayName and skills")
        if not isinstance(settings["displayName"], str) or not settings["displayName"].strip():
            raise SyncError(f"{group}: displayName must be non-empty")
        if not isinstance(settings["skills"], list) or not settings["skills"]:
            raise SyncError(f"{group}: skills must be a non-empty list")
        for source in settings["skills"]:
            if not isinstance(source, dict) or set(source) != {"name", "repo", "path", "ref"}:
                raise SyncError(f"{group}: each Skill needs name, repo, path, ref")
            if any(not isinstance(value, str) or not value.strip() for value in source.values()):
                raise SyncError(f"{group}: source fields must be non-empty strings")
            name = source["name"]
            if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or name.casefold() in names:
                raise SyncError(f"Invalid or duplicate Skill name: {name}")
            if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", source["repo"]):
                raise SyncError(f"{name}: repo must be owner/repo")
            path = PurePosixPath(source["path"])
            if path.is_absolute() or any(part in {".", ".."} for part in source["path"].split("/")) or "\\" in source["path"] or ":" in source["path"]:
                raise SyncError(f"{name}: path must stay inside the upstream repository")
            if source["ref"].startswith("-") or any(character.isspace() for character in source["ref"]):
                raise SyncError(f"{name}: invalid ref")
            names.add(name.casefold())
            sources.append({**source, "group": group})
    return sources


def contained(path: Path, parent: Path) -> None:
    """Check resolved targets before moving or replacing anything."""
    if path.is_symlink() or not path.resolve().is_relative_to(parent.resolve()) or path.resolve() == parent.resolve():
        raise SyncError(f"Path escapes its target directory: {path}")


def sync_temporary_parent(root: Path) -> Path:
    """Create and validate the in-repository parent for one sync run."""
    root = root.absolute()
    if root.resolve() != root:
        raise SyncError("Marketplace root is redirected")

    temporary_root = root / ".agent-tmp"
    sync_root = temporary_root / "sync"
    for directory in (temporary_root, sync_root):
        if directory.is_symlink() or directory.is_junction() or directory.resolve() != directory.absolute():
            raise SyncError(f"Synchronization temporary directory is redirected: {directory.name}")
        if directory.exists() and not directory.is_dir():
            raise SyncError(f"Synchronization temporary path is not a directory: {directory.name}")
        try:
            directory.mkdir(exist_ok=True)
        except OSError as error:
            raise SyncError(f"Cannot prepare synchronization temporary directory: {directory.name}") from error
        if directory.is_symlink() or directory.is_junction() or directory.resolve() != directory.absolute():
            raise SyncError(f"Synchronization temporary directory is redirected: {directory.name}")
    return sync_root


def git(repository: Path, *arguments: str) -> str:
    command = ["git", "-C", str(repository), *arguments]
    try:
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180, env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
    except subprocess.TimeoutExpired as error:
        raise SyncError(f"Git {arguments[0]} timed out after 180 seconds") from error
    if result.returncode:
        # Sources accept public owner/repo only; no credential-bearing URLs.
        raise SyncError(f"Git {arguments[0]} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def fetch(source: dict[str, str], destination: Path) -> tuple[Path, str]:
    destination.mkdir()
    git(destination, "init", "--quiet")
    git(destination, "remote", "add", "origin", f"https://github.com/{source['repo']}.git")
    git(destination, "fetch", "--quiet", "--depth=1", "origin", source["ref"])
    commit = git(destination, "rev-parse", "FETCH_HEAD")
    # Checkout leaves blobs byte-for-byte intact, including upstream LF endings.
    git(destination, "-c", "core.autocrlf=false", "-c", "core.symlinks=true", "checkout", "--quiet", "--detach", commit)
    return destination, commit


def validate_skill(directory: Path, name: str) -> None:
    if not directory.is_dir():
        raise SyncError(f"{name}: upstream directory does not exist")
    for path in [directory, *directory.rglob("*")]:
        if path.is_symlink() or path.is_junction():
            raise SyncError(f"{name}: symlink is not supported: {path.name}")
    entry = directory / "SKILL.md"
    if not entry.is_file():
        raise SyncError(f"{name}: missing SKILL.md")
    text = entry.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    if not lines or lines[0] != "---" or "---" not in lines[1:]:
        raise SyncError(f"{name}: missing YAML frontmatter")
    metadata = yaml.safe_load("\n".join(lines[1:lines.index("---", 1)]))
    if not isinstance(metadata, dict) or metadata.get("name") != name or not isinstance(metadata.get("description"), str) or not metadata["description"].strip():
        raise SyncError(f"{name}: SKILL.md needs the matching name and a description")


def fingerprints(directory: Path) -> dict[str, str]:
    if not directory.exists():
        return {}
    result = {}
    for path in directory.rglob("*"):
        if path.is_symlink() or path.is_junction():
            raise SyncError(f"Refusing to replace a symlink: {path}")
        if path.is_file():
            result[path.relative_to(directory).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def change_summary(before: dict[str, str], after: dict[str, str]) -> str:
    added = len(after.keys() - before.keys())
    removed = len(before.keys() - after.keys())
    changed = sum(before[path] != after[path] for path in before.keys() & after.keys())
    return f"+{added} ~{changed} -{removed} files"


def copy_licenses(repository: Path, directory: Path) -> None:
    directory.mkdir()
    for path in repository.iterdir():
        if path.is_file() and not path.is_symlink() and re.match(r"^(licen[cs]e|copying|notice)([.-]|$)", path.name, re.IGNORECASE):
            shutil.copy2(path, directory / path.name)


def publish(replacements: list[tuple[Path, Path]], workspace: Path, root: Path) -> None:
    """Restore existing snapshots if a filesystem replacement fails."""
    for _, target in replacements:
        managed_target(target, root)
    applied = []
    try:
        for index, (staged, target) in enumerate(replacements):
            managed_target(target, root)
            target.parent.mkdir(parents=True, exist_ok=True)
            backup = workspace / f"backup-{index}" if target.exists() else None
            if backup is not None:
                target.replace(backup)
            applied.append((target, backup))
            staged.replace(target)
    except (OSError, SyncError):
        for target, backup in reversed(applied):
            managed_target(target, root)
            if target.is_dir():
                shutil.rmtree(target)
            elif target.exists():
                target.unlink()
            if backup is not None:
                backup.replace(target)
        raise


def sync(root: Path) -> None:
    sources = read_sources(root)
    lock_path = root / "sources.lock.json"
    contained(lock_path, root)
    try:
        previous = json.loads(lock_path.read_text(encoding="utf-8"), object_pairs_hook=unique_json_object) if lock_path.exists() else {"skills": {}}
    except json.JSONDecodeError as error:
        raise SyncError("Invalid sources.lock.json: malformed JSON") from error
    if not isinstance(previous, dict) or not isinstance(previous.get("skills"), dict):
        raise SyncError("Invalid sources.lock.json: expected a skills mapping")
    records = dict(previous["skills"])
    for name, record in records.items():
        if not isinstance(record, dict) or record.get("group") not in MANAGED_PLUGINS:
            raise SyncError(f"Lock contains a non-generated or invalid item: {name}")
    replacements = []
    summaries = []
    # Stage and validate every source before changing any tracked snapshot.
    temporary_parent = sync_temporary_parent(root)
    with tempfile.TemporaryDirectory(prefix="run-", dir=temporary_parent) as temporary:
        workspace = Path(temporary)
        repositories = {}
        for source in sources:
            name, group = source["name"], source["group"]
            key = (source["repo"], source["ref"])
            if key not in repositories:
                print(f"Fetch {source['repo']} @ {source['ref']}", flush=True)
                repositories[key] = fetch(source, workspace / f"repo-{len(repositories)}")
            repository, commit = repositories[key]
            upstream = repository / source["path"]
            contained(upstream, repository)
            validate_skill(upstream, name)
            target = root / "plugins" / group / "skills" / name
            contained(target, root / "plugins" / group)
            managed_target(target, root)
            staged = workspace / f"skill-{name}"
            shutil.copytree(upstream, staged)
            before, after = fingerprints(target), fingerprints(staged)
            changed = before != after
            if changed:
                replacements.append((staged, target))
            licenses = workspace / f"licenses-{name}"
            copy_licenses(repository, licenses)
            license_target = root / "plugins" / group / "licenses" / name
            contained(license_target, root / "plugins" / group)
            managed_target(license_target, root)
            if fingerprints(license_target) != fingerprints(licenses):
                replacements.append((licenses, license_target))
            record = {**source, "commit": commit}
            old = records.get(name, {})
            if isinstance(old, dict) and all(old.get(field) == value for field, value in record.items()) and not changed and old.get("syncedAt"):
                record["syncedAt"] = old["syncedAt"]
            else:
                record["syncedAt"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            records[name] = record
            previous_commit = old.get("commit", "none") if isinstance(old, dict) else "none"
            summaries.append(f"{group}/{name}: {previous_commit} -> {commit}; {change_summary(before, after)}")
        lock_text = json.dumps({"skills": records}, ensure_ascii=False, indent=2) + "\n"
        if not lock_path.exists() or lock_path.read_text(encoding="utf-8") != lock_text:
            staged_lock = workspace / "sources.lock.json"
            staged_lock.write_text(lock_text, encoding="utf-8", newline="\n")
            replacements.append((staged_lock, lock_path))
        publish(replacements, workspace, root)
    for summary in summaries:
        print(summary)
    unlisted = records.keys() - {source["name"] for source in sources}
    if unlisted:
        print(f"Unlisted snapshots kept (no automatic deletion): {', '.join(sorted(unlisted))}")
    print(f"Synchronized {len(sources)} Skills; {len(replacements)} snapshot/record paths changed.")
    print("Review: git diff --stat; git diff -- sources.lock.json; git status --short")


def main() -> int:
    try:
        sync(Path(__file__).resolve().parents[1])
    except (SyncError, OSError, ValueError, yaml.YAMLError) as error:
        print(f"Sync failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
