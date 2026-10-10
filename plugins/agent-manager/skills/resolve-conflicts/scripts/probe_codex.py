# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Test project-only exact Skill filtering in a disposable Codex environment.

No real project/user config is edited. No model turn or Skill body is executed.
Run only after identifying Codex and verifying current official RPC/CLI support.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import tempfile
import threading
import tomllib


class ProbeBlocked(ValueError):
    """The isolated loader check cannot establish support."""


def stop_process(process: subprocess.Popen) -> None:
    """Stop only our probe and its children, including inherited pipe owners."""
    if process.poll() is None:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                           capture_output=True, timeout=10)
        else:
            process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)


def run(command: list[str], env: dict[str, str], cwd: Path) -> str:
    result = subprocess.run(command, env=env, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=40)
    if result.returncode:
        raise ProbeBlocked(f"{command[1]} failed (exit {result.returncode}); probe aborted")
    return result.stdout


def rpc_skills(cwd: Path, env: dict[str, str], selector: str | None = None) -> tuple[list[dict], bool]:
    process = subprocess.Popen(["codex", "app-server", "--stdio"], cwd=cwd, env=env,
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, text=True, encoding="utf-8")
    responses = queue.Queue()

    def reader():
        for line in process.stdout:
            try:
                responses.put(json.loads(line))
            except ValueError:
                continue
        responses.put(None)

    worker = threading.Thread(target=reader, daemon=True)
    worker.start()

    def request(identifier, method, params):
        process.stdin.write(json.dumps({"id": identifier, "method": method, "params": params}) + "\n")
        process.stdin.flush()
        while True:
            message = responses.get(timeout=40)
            if message is None:
                raise ProbeBlocked("Codex app-server stopped before responding")
            if message.get("id") == identifier:
                if "error" in message:
                    raise ProbeBlocked(f"Codex {method} rejected the probe request")
                return message["result"]

    try:
        request(1, "initialize", {"clientInfo": {"name": "agent-manager-probe", "version": "0.1.0"}, "capabilities": {"experimentalApi": True}})
        process.stdin.write('{"method":"initialized"}\n')
        process.stdin.flush()
        payload = request(2, "skills/list", {"cwds": [str(cwd)], "forceReload": True})
        data = payload.get("data", [])
        if len(data) != 1 or data[0].get("errors"):
            raise ProbeBlocked("Codex Skill discovery returned incomplete inventory")
        loaded = request(3, "config/read", {"cwd": str(cwd), "includeLayers": False})
        entries = (loaded.get("config", {}).get("skills") or {}).get("config") or []
        visible = any(item.get("path") == selector and item.get("enabled") is False for item in entries)
        return data[0]["skills"], visible
    except queue.Empty as error:
        raise ProbeBlocked("Codex Skill discovery timed out") from error
    finally:
        stop_process(process)
        process.stdin.close()
        worker.join(timeout=5)
        if not worker.is_alive():
            process.stdout.close()


def tree_hash(root: Path) -> dict[str, str]:
    return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in root.rglob("*") if path.is_file()}


def probe(global_plugin: Path, skill_name: str, project_skill: Path | None = None) -> dict:
    global_plugin = global_plugin.resolve(strict=True)
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", skill_name):
        raise ProbeBlocked("Invalid Skill name")
    manifest = json.loads((global_plugin / "plugin.json").read_text(encoding="utf-8"))
    plugin_name = manifest.get("name")
    extension = manifest.get("extensions", {}).get("com.openai", {})
    if not isinstance(plugin_name, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", plugin_name):
        raise ProbeBlocked("Unrecognized Plugin manifest")
    if any(key in extension or key in manifest for key in ("hooks", "apps", "mcpServers", "skills")) or any((global_plugin / path).exists() for path in ("mcp.json", ".mcp.json", ".app.json", "hooks", ".codex-plugin")):
        raise ProbeBlocked("Probe only supports standard skills-only Plugins; extra components could have side effects")
    for path in (global_plugin, *global_plugin.rglob("*")):
        if path.is_symlink() or path.is_junction():
            raise ProbeBlocked("Cannot safely copy redirected Plugin paths")
    original = tree_hash(global_plugin)
    user_root = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    real_config = user_root / "config.toml"
    user_before = real_config.read_bytes() if real_config.exists() else None
    with tempfile.TemporaryDirectory(prefix="agent-manager-probe-") as temporary:
        root = Path(temporary)
        agent_home = root / "codex-home"
        agent_home.mkdir()
        project = root / "project"
        project.mkdir()
        env = {**os.environ, "CODEX_HOME": str(agent_home), "GIT_TERMINAL_PROMPT": "0"}
        version = run(["codex", "--version"], env, project).strip()
        run(["git", "init", "--quiet", str(project)], env, project)
        (agent_home / "config.toml").write_text(f'[projects.{json.dumps(str(project))}]\ntrust_level = "trusted"\n', encoding="utf-8")
        marketplace = root / "marketplace"
        copied_plugin = marketplace / "plugins" / plugin_name
        shutil.copytree(global_plugin, copied_plugin)
        catalog_path = marketplace / ".agents/plugins/marketplace.json"
        catalog_path.parent.mkdir(parents=True)
        catalog = {"name": "conflict-probe", "plugins": [{"name": plugin_name, "source": {"source": "local", "path": f"./plugins/{plugin_name}"}, "skills": "./skills/", "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}}]}
        catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
        run(["codex", "plugin", "marketplace", "add", str(marketplace), "--json"], env, project)
        run(["codex", "plugin", "add", f"{plugin_name}@conflict-probe", "--json"], env, project)
        local_skill = project / ".agents/skills" / skill_name
        if project_skill is not None:
            project_skill = project_skill.resolve(strict=True)
            if any(path.is_symlink() or path.is_junction() for path in (project_skill, *project_skill.rglob("*"))):
                raise ProbeBlocked("Project Skill has redirected paths")
            shutil.copytree(project_skill, local_skill)
        else:
            local_skill.mkdir(parents=True)
            (local_skill / "SKILL.md").write_text(f"---\nname: {skill_name}\ndescription: Isolated project Skill probe; do not execute.\n---\nLoader fixture only.\n", encoding="utf-8")
        baseline, _ = rpc_skills(project, env)
        cache = agent_home / "plugins/cache"
        global_skills = [item for item in baseline if Path(item["path"]).resolve().is_relative_to(cache.resolve())]
        target = [item for item in global_skills if item["name"].split(":")[-1] == skill_name and item.get("enabled", True)]
        project_before = [item for item in baseline if Path(item["path"]).resolve().is_relative_to(local_skill.resolve()) and item.get("enabled", True)]
        if len(target) != 1 or len(project_before) != 1:
            raise ProbeBlocked("Probe did not discover exactly one global and one project copy")
        target_path = target[0]["path"]
        other_paths = {item["path"] for item in global_skills if item["path"] != target_path and item.get("enabled", True)}
        isolated_user_before = (agent_home / "config.toml").read_bytes()
        project_config = project / ".codex/config.toml"
        project_config.parent.mkdir()
        project_config.write_text(f"[[skills.config]]\npath = {json.dumps(target_path)}\nenabled = false\n", encoding="utf-8")
        after, loaded = rpc_skills(project, env, target_path)
        available_paths = {item["path"] for item in after if item.get("enabled", True)}
        checks = {
            "global_target_disabled": target_path not in available_paths,
            "project_same_name_enabled": project_before[0]["path"] in available_paths,
            "other_plugin_skills_enabled": other_paths <= available_paths,
            "user_config_unchanged": (agent_home / "config.toml").read_bytes() == isolated_user_before,
            "no_plugin_disable_rule": "plugins" not in tomllib.loads(project_config.read_text(encoding="utf-8")),
            "project_rule_loaded": loaded,
        }
        # Reference docs differ on folder vs SKILL.md; test the alternate exact
        # selector and a disposable user-layer control before diagnosing failure.
        folder_selector = str(Path(target_path).parent)
        project_config.write_text(f"[[skills.config]]\npath = {json.dumps(folder_selector)}\nenabled = false\n", encoding="utf-8")
        folder_after, folder_loaded = rpc_skills(project, env, folder_selector)
        folder_available = {item["path"] for item in folder_after if item.get("enabled", True)}
        folder_works = target_path not in folder_available and project_before[0]["path"] in folder_available and other_paths <= folder_available and folder_loaded
        if folder_works:
            checks["global_target_disabled"] = True
            checks["project_rule_loaded"] = True
            checks["project_same_name_enabled"] = True
            checks["other_plugin_skills_enabled"] = True
        # Only the isolated test home is changed for this control; never real home.
        project_config.unlink()
        (agent_home / "config.toml").write_bytes(isolated_user_before + f"\n[[skills.config]]\npath = {json.dumps(target_path)}\nenabled = false\n".encode("utf-8"))
        user_after, _ = rpc_skills(project, env, target_path)
        user_control_works = target_path not in {item["path"] for item in user_after if item.get("enabled", True)}
        result = {"Status": "SUPPORTED" if all(checks.values()) else "BLOCKED", "Version": version,
                  "Checks": checks, "GlobalSelector": "Exact Skill folder" if folder_works else "Exact skills/list SKILL.md path",
                  "FolderSelectorWorks": folder_works, "IsolatedUserLayerControlWorks": user_control_works,
                  "OtherPluginSkills": sorted(item["name"] for item in global_skills if item["path"] in other_paths),
                  "Reason": "" if all(checks.values()) else (
                      "当前 Codex 版本虽然支持 skill-level disable，但项目级 .codex/config.toml 中的 skills.config 当前不会生效。"
                      if user_control_works and loaded else "Cannot establish safe project-only filtering; inspect Checks before editing.")}
    if tree_hash(global_plugin) != original or (real_config.read_bytes() if real_config.exists() else None) != user_before:
        raise ProbeBlocked("Real input/config changed externally during probe; rescan before proceeding")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--global-plugin-root", type=Path, required=True)
    parser.add_argument("--skill", required=True)
    parser.add_argument("--project-skill", type=Path)
    args = parser.parse_args()
    try:
        result = probe(args.global_plugin_root, args.skill, args.project_skill)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["Status"] == "SUPPORTED" else 1
    except (ProbeBlocked, OSError, ValueError, subprocess.TimeoutExpired) as error:
        print(json.dumps({"Status": "BLOCKED", "Reason": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
