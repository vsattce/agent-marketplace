# /// script
# requires-python = ">=3.12"
# dependencies = ["tomlkit>=0.13.3,<0.14", "PyYAML>=6.0.2,<7"]
# ///
"""Read-only preflight; never start a potentially mutating Codex subprocess.

A disposable CODEX_HOME alone does not confine logs, caches or child processes.
Without verified project-only confinement, runtime filtering tests are BLOCKED.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from project_config import Blocked, config_path, project_root


def probe(global_plugin: Path, skill_name: str, project_skill: Path | None = None) -> dict:
    root = project_root(Path.cwd())
    config_path(root)
    global_plugin = global_plugin.resolve(strict=True)
    manifest = json.loads((global_plugin / "plugin.json").read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or not isinstance(manifest.get("name"), str):
        raise Blocked("Cannot safely read Plugin identity")
    candidates = []
    for entry in (global_plugin / "skills").glob("*/SKILL.md"):
        lines = entry.read_text(encoding="utf-8-sig").splitlines()
        if not lines or lines[0] != "---" or "---" not in lines[1:]:
            raise Blocked("Cannot safely read Plugin Skill metadata")
        metadata = yaml.safe_load("\n".join(lines[1:lines.index("---", 1)]))
        if not isinstance(metadata, dict):
            raise Blocked("Cannot safely read Plugin Skill metadata")
        if metadata.get("name") == skill_name:
            candidates.append(str(entry.resolve()))
    if len(candidates) != 1:
        raise Blocked("Cannot identify exactly one global Skill file; use official loaded inventory")
    if project_skill is not None:
        project_skill = project_skill.resolve(strict=True)
        if not project_skill.is_relative_to(root):
            raise Blocked("Project Skill is outside current project root")
    return {
        "Status": "BLOCKED",
        "Project": str(root),
        "Plugin": manifest.get("name"),
        "Skill": skill_name,
        "GlobalSkillFile": candidates[0],
        "ProjectSkill": str(project_skill) if project_skill else "UNKNOWN",
        "Version": "UNKNOWN (obtain from current Harness metadata)",
        "ReadOnlyPreflight": True,
        "Reason": "Cannot verify runtime project-level Skill filtering without verified "
                  "project-only process confinement. No config, cache, installation or "
                  "temporary directory was written. Global fallback is forbidden.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--global-plugin-root", type=Path, required=True)
    parser.add_argument("--skill", required=True)
    parser.add_argument("--project-skill", type=Path)
    args = parser.parse_args()
    try:
        result = probe(args.global_plugin_root, args.skill, args.project_skill)
    except (Blocked, OSError, ValueError, yaml.YAMLError) as error:
        result = {"Status": "BLOCKED", "Reason": str(error)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
