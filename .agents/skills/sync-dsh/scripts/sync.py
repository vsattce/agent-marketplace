# /// script
# requires-python = ">=3.12"
# dependencies = ["PyYAML>=6.0.2,<7"]
# ///
"""Synchronize catalog product skills using the installed DSH Desktop runtime."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

import yaml


ROOT = Path(__file__).resolve().parents[4]
BEGIN = "# BEGIN agent-marketplace sync-dsh"
END = "# END agent-marketplace sync-dsh"
PROVIDER_ID = "agent-marketplace-skills"
SUPPORTED_VERSIONS = {"0.2.1-rc.2"}
EXCLUDED = {"codex-skills", ".codex-plugin", ".claude-plugin", ".antigravity-plugin", "__pycache__"}


class SyncError(RuntimeError):
    pass


class PatchLoader(yaml.SafeLoader):
    """Accept existing Loader expressions as opaque values, without evaluating them."""


class Expression:
    pass


PatchLoader.add_constructor(None, lambda loader, node: Expression())


def plain_path(path: Path) -> Path:
    absolute = path.absolute()
    for component in (absolute, *absolute.parents):
        if component.is_symlink() or component.is_junction():
            raise SyncError(f"Redirected path is not supported: {component}")
    if absolute.resolve() != absolute:
        raise SyncError(f"Unexpected resolved path: {absolute}")
    return absolute


def digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def products(repository: Path) -> tuple[dict[str, bytes], dict[str, dict]]:
    catalog = json.loads((repository / ".agents/plugins/marketplace.json").read_text("utf-8"))
    if catalog.get("name") != "agent-marketplace":
        raise SyncError("Unexpected Marketplace identity")
    files, skills, names = {}, {}, set()
    for entry in catalog["plugins"]:
        name = entry["name"]
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or name in names:
            raise SyncError("Invalid or duplicate product name")
        names.add(name)
        if entry["source"] != {"source": "local", "path": f"./plugins/{name}"}:
            raise SyncError(f"Unexpected product source: {name}")
        source = plain_path(repository / "plugins" / name)
        count = 0
        for path in sorted(source.rglob("*")):
            plain_path(path)
            relative = path.relative_to(source)
            if any(part in EXCLUDED for part in relative.parts) or path.suffix == ".pyc":
                continue
            if not path.is_file():
                continue
            key = f"plugins/{name}/{relative.as_posix()}"
            files[key] = path.read_bytes()
            if len(relative.parts) == 3 and relative.parts[0] == "skills" and path.name == "SKILL.md":
                text = files[key].decode("utf-8")
                sections = text.split("---", 2)
                if len(sections) != 3 or sections[0].strip():
                    raise SyncError(f"Missing skill frontmatter: {key}")
                metadata = yaml.safe_load(sections[1])
                skill_name = relative.parts[1]
                if not isinstance(metadata, dict) or metadata.get("name") != skill_name or not metadata.get("description"):
                    raise SyncError(f"Invalid skill metadata: {key}")
                if skill_name in skills:
                    raise SyncError(f"Duplicate product skill: {skill_name}")
                skills[skill_name] = {"plugin": name, "path": key, "metadata": metadata}
                count += 1
        if not count:
            raise SyncError(f"No product skills: {name}")
    if not names:
        raise SyncError("No product plugins found")
    return files, skills


def parse_patch(text: str) -> list:
    try:
        rows = yaml.load(text, Loader=PatchLoader)
    except yaml.YAMLError as error:
        raise SyncError("Invalid Desktop patch YAML; no settings were changed") from error
    if rows is not None and (not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows)):
        raise SyncError("Desktop patch must be a YAML list of patch mappings")
    return rows or []


def all_rows(rows: list):
    for row in rows:
        yield row
        for field in ("insert", "config"):
            children = row.get(field)
            if isinstance(children, list):
                yield from all_rows([child for child in children if isinstance(child, dict)])


def managed_patch(text: str, roots: list[Path]) -> tuple[str, bool, list[str]]:
    rows = list(all_rows(parse_patch(text)))
    pattern = re.compile(r"(?ms)^" + re.escape(BEGIN) + r"\r?\n.*?^" + re.escape(END) + r"(?:\r?\n|$)")
    blocks = list(pattern.finditer(text))
    if text.count(BEGIN) != len(blocks) or text.count(END) != len(blocks) or len(blocks) > 1:
        raise SyncError("Ambiguous sync-dsh block; no settings were changed")
    managed = [row for row in rows if row.get("id") == PROVIDER_ID]
    disabled = False
    if blocks:
        if len(managed) != 1:
            raise SyncError("Managed provider is missing or duplicated")
        own_block = parse_patch(blocks[0].group().replace(BEGIN, "").replace(END, ""))
        if (len(own_block) != 1 or set(own_block[0]) != {"insert"}
                or not isinstance(own_block[0]["insert"], list) or len(own_block[0]["insert"]) != 1):
            raise SyncError("Managed block contains user entries; it was preserved")
        own_rows = list(all_rows(own_block))
        own = [row for row in own_rows if row.get("id") == PROVIDER_ID]
        if len(own) != 1 or own[0].get("name") != "@deepseek-ai/dsh-skill-filesystem":
            raise SyncError("Managed provider identity changed")
        if set(own[0]) - {"id", "name", "disabled", "config"}:
            raise SyncError("Managed provider contains user fields; it was preserved")
        disabled = own[0].get("disabled", False)
        if type(disabled) is not bool:
            raise SyncError("Managed provider disabled state must be a boolean")
        expected = {"providerName", "includeDefaultRoots", "customSkillDirs"}
        config = own[0].get("config", {})
        if set(config) != expected or config["providerName"] != "agent-marketplace" or config["includeDefaultRoots"] is not False:
            raise SyncError("Managed provider config was edited; preserve it and resolve the conflict first")
        prior_roots = config["customSkillDirs"]
        if not isinstance(prior_roots, list) or not prior_roots:
            raise SyncError("Managed skill roots were edited")
        for root in prior_roots:
            prior = Path(root) if isinstance(root, str) else Path()
            if (len(prior.parts) < 5 or prior.parts[-5] != "releases"
                    or not re.fullmatch(r"[0-9a-f]{64}", prior.parts[-4])
                    or prior.parts[-3] != "plugins" or prior.parts[-1] != "skills"
                    or (roots and prior.parents[3] != roots[0].parents[3])):
                raise SyncError("Managed skill roots were edited; they were preserved")
    elif managed:
        raise SyncError("Provider id is already used outside the managed block")
    extra_roots = []
    for row in rows:
        if row.get("id") != PROVIDER_ID and row.get("name") == "@deepseek-ai/dsh-skill-filesystem":
            config = row.get("config", {})
            if config.get("providerName") == "agent-marketplace":
                raise SyncError("Skill provider name is already used outside the managed block")
            for root in config.get("customSkillDirs", []):
                if not isinstance(root, str) or not Path(root).is_absolute():
                    raise SyncError("Cannot safely inspect existing custom skill roots")
                extra_roots.append(root)
    addition = [{"insert": [{"id": PROVIDER_ID, "name": "@deepseek-ai/dsh-skill-filesystem",
                           "disabled": disabled, "config": {"providerName": "agent-marketplace",
                           "includeDefaultRoots": False, "customSkillDirs": [path.as_posix() for path in roots]}}]}]
    newline = "\r\n" if "\r\n" in text else "\n"
    block = BEGIN + "\n" + yaml.safe_dump(addition, allow_unicode=True, sort_keys=False) + END + "\n"
    block = block.replace("\n", newline)
    if blocks:
        result = text[:blocks[0].start()] + block + text[blocks[0].end():]
    else:
        # An explicit empty YAML sequence cannot precede block-style list entries.
        base = re.sub(r"(?m)^\[\][ \t]*(?=\r?$)", "# Previously empty patch list", text)
        result = base + (newline if base and not base.endswith("\n") else "") + block
    parse_patch(result)
    return result, disabled, extra_roots


def inspect(desktop: Path, roots: list[Path], home: Path, *, defaults: bool = False) -> dict:
    environment = dict(os.environ, ELECTRON_RUN_AS_NODE="1")
    request = {"roots": [str(path) for path in roots], "dshHome": str(home), "includeDefaultRoots": defaults}
    result = subprocess.run(
        [str(desktop), "--expose-internals", "-e", "require(process.argv[1])",
         str(Path(__file__).with_name("inspect-desktop.cjs")), json.dumps(request)],
        capture_output=True, text=True, encoding="utf-8", env=environment, timeout=45,
    )
    payloads = [line.removeprefix("DSH_INSPECTION:") for line in result.stdout.splitlines() if line.startswith("DSH_INSPECTION:")]
    if result.returncode or len(payloads) != 1:
        detail = result.stderr.strip()[:1000] or "No inspection result returned"
        raise SyncError(f"Installed Desktop's isolated skill inspection failed: {detail}")
    payload = json.loads(payloads[0])
    if payload["version"] not in SUPPORTED_VERSIONS:
        raise SyncError(f"Desktop runtime {payload['version']} is not yet verified by this synchronizer")
    return payload


def verify_skills(observed: dict, expected: dict[str, dict], base: Path) -> None:
    entries = observed["skills"]
    if len(entries) != len(expected) or {entry["name"] for entry in entries} != set(expected):
        raise SyncError("Desktop's discovered skill inventory differs from the catalog products")
    for entry in entries:
        specification = expected[entry["name"]]
        if Path(entry["path"]).resolve() != (base / specification["path"]).resolve():
            raise SyncError(f"Unexpected Desktop skill path: {entry['name']}")
        policy = entry["invocation"]
        metadata = specification["metadata"]
        if (policy["modelInvocable"] != (not metadata.get("disable-model-invocation", False))
                or policy["userInvocable"] != metadata.get("user-invocable", True)):
            raise SyncError(f"Desktop invocation policy differs: {entry['name']}")


@contextmanager
def sync_lock(path: Path):
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as error:
        raise SyncError(f"Another synchronization owns {path}; no automatic lock removal") from error
    try:
        os.close(descriptor)
        yield
    finally:
        path.unlink()


def synchronize(repository: Path, desktop: Path, home: Path, *, check_only: bool = False) -> dict:
    repository, desktop, home = (plain_path(path) for path in (repository, desktop, home))
    if not desktop.is_file() or desktop.name != "DeepSeek Harness.exe":
        raise SyncError("Provide the installed DeepSeek Harness.exe with --desktop-path")
    profile = plain_path(home / "profiles/desktop")
    manifest = json.loads((profile / "package.json").read_text("utf-8"))
    if manifest.get("name") != "dsh-profile-desktop":
        raise SyncError("Desktop profile is not initialized")
    files, skills = products(repository)
    hashes = {relative: digest(content) for relative, content in files.items()}
    release_id = digest(json.dumps(hashes, sort_keys=True).encode("utf-8"))
    destination = plain_path(home / "marketplaces/agent-marketplace")
    release = plain_path(destination / "releases" / release_id)
    plugin_names = sorted({skill["plugin"] for skill in skills.values()})
    roots = [release / "plugins" / name / "skills" for name in plugin_names]
    patch = plain_path(profile / "cordis.patch.yml")
    original = patch.read_bytes() if patch.exists() else None
    text = original.decode("utf-8-sig") if original is not None else ""
    proposed, disabled, extra_roots = managed_patch(text, roots)
    encoded = (b"\xef\xbb\xbf" if original and original.startswith(b"\xef\xbb\xbf") else b"") + proposed.encode("utf-8")
    source_roots = [repository / "plugins" / name / "skills" for name in plugin_names]
    native = inspect(desktop, source_roots, home)
    verify_skills(native, skills, repository)
    existing = inspect(desktop, [Path(path) for path in extra_roots], home, defaults=True)
    conflicts = sorted(set(skills) & {entry["name"] for entry in existing["skills"]})
    if conflicts:
        raise SyncError("Existing user skill names conflict: " + ", ".join(conflicts))
    summary = {"desktopVersion": native["version"], "plugins": len(plugin_names), "skills": len(skills),
               "enabled": not disabled, "release": str(release), "checkOnly": check_only}
    if check_only:
        return summary
    destination.mkdir(parents=True, exist_ok=True)
    with sync_lock(destination / ".sync.lock"):
        if release.exists():
            actual = {path.relative_to(release).as_posix(): digest(path.read_bytes())
                      for path in release.rglob("*") if plain_path(path).is_file()}
            if actual != hashes:
                raise SyncError("Installed snapshot was edited or is incomplete; it was preserved")
        else:
            release.mkdir(parents=True)
            for relative, content in files.items():
                target = release / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
        for relative, expected_hash in hashes.items():
            if digest((release / relative).read_bytes()) != expected_hash:
                raise SyncError("Copied resource differs; Desktop settings were preserved")
        verify_skills(inspect(desktop, roots, home), skills, release)
        current_files, _ = products(repository)
        if current_files != files or (patch.read_bytes() if patch.exists() else None) != original:
            raise SyncError("Source or Desktop settings changed during synchronization; settings were preserved")
        if encoded != original:
            descriptor, temporary = tempfile.mkstemp(prefix=".sync-dsh-", dir=profile)
            temporary_path = Path(temporary)
            try:
                with os.fdopen(descriptor, "wb") as output:
                    output.write(encoded)
                os.replace(temporary_path, patch)
            finally:
                temporary_path.unlink(missing_ok=True)
        if patch.read_bytes() != encoded:
            raise SyncError("Desktop settings changed after publication; verify the managed block")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--desktop-path", required=True, type=Path)
    parser.add_argument("--dsh-home", type=Path, default=Path(os.environ.get("DSH_HOME", Path.home() / ".dsh")))
    parser.add_argument("--check-only", action="store_true")
    arguments = parser.parse_args()
    git = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True)
    if Path(git.stdout.strip()).resolve() != ROOT:
        raise SyncError("sync-dsh must run from its agent-marketplace Git checkout")
    print(json.dumps(synchronize(ROOT, arguments.desktop_path, arguments.dsh_home,
                                 check_only=arguments.check_only), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (SyncError, OSError, ValueError, subprocess.SubprocessError) as error:
        raise SystemExit(f"sync-dsh: {error}") from None
