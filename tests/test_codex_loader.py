"""Opt-in real Codex loader tests with isolated config and no model inference.

Set AGENT_MANAGER_CODEX_TESTS=1 to run. A localhost provider captures the actual
request context then stops the CLI; no model, external API, or Skill body executes.
"""

import http.server
import json
import os
from pathlib import Path
import queue
import subprocess
import threading
import time
import unittest
from temp_paths import temporary_test_directory

ROOT = Path(__file__).resolve().parents[1]


def skill_body(plugin: str, skill: str) -> str:
    text = (ROOT / "plugins" / plugin / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) != 3:
        raise AssertionError(f"Invalid Skill frontmatter: {plugin}:{skill}")
    return parts[2].strip()


def contains_text(value, expected: str) -> bool:
    values = text_values(value)
    return any(expected in item for item in values) or any(
        expected in separator.join(values) for separator in ("", "\n")
    )


def text_entries(value, path="$") -> list[tuple[str, str]]:
    if isinstance(value, str):
        return [(path, value)]
    if isinstance(value, dict):
        return [entry for key, child in value.items() for entry in text_entries(child, f"{path}.{key}")]
    if isinstance(value, list):
        return [entry for index, child in enumerate(value) for entry in text_entries(child, f"{path}[{index}]")]
    return []


def captured_skill_source(value, name: str) -> tuple[str, str] | None:
    for path, content in text_entries(value):
        if f"<name>{name}</name>" not in content:
            continue
        path_end = content.find("</path>", content.find("<path>"))
        content_end = content.rfind("\n</skill>")
        if path_end >= 0 and content_end >= 0:
            return path, content[path_end + len("</path>\n"):content_end]
    return None


def text_values(value) -> list[str]:
    return [value for _, value in text_entries(value)]


class ProbeBlocked(ValueError):
    """Development-only loader evidence could not be obtained."""


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


@unittest.skipUnless(os.environ.get("AGENT_MANAGER_CODEX_TESTS") == "1", "Opt-in isolated Codex loader validation")
class CodexLoaderTests(unittest.TestCase):
    def setUp(self):
        self.temporary = temporary_test_directory("codex-loader")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.project = self.root / "project"
        self.project.mkdir()
        self.agent_home = self.root / "codex-home"
        self.agent_home.mkdir()
        self.env = {**os.environ, "CODEX_HOME": str(self.agent_home), "GIT_TERMINAL_PROMPT": "0"}
        # A workstation HTTP proxy must not intercept the localhost fixture API.
        for key in ("NO_PROXY", "no_proxy"):
            self.env[key] = ",".join(filter(None, (self.env.get(key), "127.0.0.1", "localhost")))
        self.requests = []
        self.request_received = threading.Event()
        self.release_response = threading.Event()
        self.handler_done = threading.Event()
        requests = self.requests
        request_received = self.request_received
        release_response = self.release_response
        handler_done = self.handler_done

        class CaptureHandler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
                requests.append(json.loads(body))
                request_received.set()
                # Keep our CLI alive until its whole process tree is stopped;
                # returning an error first could orphan Git pipe owners on Windows.
                release_response.wait(timeout=10)
                handler_done.set()

            def log_message(self, *args):
                pass

        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), CaptureHandler)
        self.worker = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.worker.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        config = (
            'model = "loader-fixture"\nmodel_provider = "loader-probe"\n'
            'approval_policy = "never"\nsandbox_mode = "read-only"\n'
            '[features]\nremote_plugin = false\nsystem_proxy_fallback = false\n'
            '[model_providers.loader-probe]\nname = "Local loader capture"\n'
            f'base_url = "http://127.0.0.1:{self.server.server_port}/v1"\n'
            'wire_api = "responses"\nrequires_openai_auth = false\n'
            f'[projects.{json.dumps(str(self.project))}]\ntrust_level = "trusted"\n'
        )
        (self.agent_home / "config.toml").write_text(config, encoding="utf-8")
        run(["git", "init", "--quiet"], self.env, self.project)
        run(["codex", "plugin", "marketplace", "add", str(ROOT), "--json"], self.env, self.project)
        run(["codex", "plugin", "add", "agent-manager@agent-marketplace", "--json"], self.env, self.project)

    def capture(self, prompt):
        self.requests.clear()
        self.request_received.clear()
        self.release_response.clear()
        self.handler_done.clear()
        trace_path = self.root / "capture.log"
        with trace_path.open("wb") as trace:
            process = subprocess.Popen(["codex", "exec", "--ephemeral", "--json", "--color", "never", prompt],
                                       cwd=self.project, env=self.env, stdin=subprocess.DEVNULL,
                                       stdout=trace, stderr=subprocess.STDOUT)
            captured = False
            try:
                deadline = time.monotonic() + 40
                while process.poll() is None and time.monotonic() < deadline:
                    if self.request_received.wait(timeout=0.25):
                        captured = True
                        break
            finally:
                stop_process(process)
                self.release_response.set()
                if captured:
                    self.handler_done.wait(timeout=10)
        diagnostic = trace_path.read_text(encoding="utf-8", errors="replace")[-1600:]
        self.assertTrue(captured and self.requests, f"No loader request captured; exit {process.returncode}: {diagnostic}")
        return json.dumps(self.requests[0], ensure_ascii=False)

    def test_discovery_and_manual_only_context(self):
        inventory, _ = rpc_skills(self.project, self.env)
        owned = [item for item in inventory if item["name"].startswith("agent-manager:")]
        self.assertEqual({item["name"] for item in owned}, {"agent-manager:am-config"})
        self.assertTrue(all(item.get("enabled", True) for item in owned))
        ordinary = self.capture("请讨论当前项目的 Plugin / Skill 冲突、版本更新和项目开关配置，不调用任何 Skill。")
        for marker in ("# 编辑项目 Agent 指令 / Skill / Plugin", "Only use when explicitly invoked by the user."):
            self.assertNotIn(marker, ordinary)
        for name, marker in (("am-config", "# 编辑项目 Agent 指令 / Skill / Plugin"),):
            with self.subTest(invocation=name):
                context = self.capture(f"${name} 仅验证 Skill 加载，本轮无需执行任何操作。")
                print(f"\nBare ${name} injected: {marker in context}", flush=True)
            with self.subTest(invocation=f"agent-manager:{name}"):
                context = self.capture(f"$agent-manager:{name} 仅验证 Skill 加载，本轮无需执行任何操作。")
                self.assertTrue(marker in context, "Namespaced explicit invocation did not inject Skill instructions")

    def test_new_third_party_plugins_discover_and_inject_skills(self):
        run(["codex", "plugin", "add", "software-dev@agent-marketplace", "--json"], self.env, self.project)
        run(["codex", "plugin", "add", "engineering-tools@agent-marketplace", "--json"], self.env, self.project)
        inventory, _ = rpc_skills(self.project, self.env)
        by_name = {item["name"]: item for item in inventory}
        expected = (
            "software-dev:frontend-design",
            "software-dev:web-design-guidelines",
            "software-dev:vue-best-practices",
            "software-dev:fastapi",
            "software-dev:java-spring-boot",
            "engineering-tools:docker-build-strategies",
        )
        self.assertNotIn("software-dev:vue", by_name)
        for name in expected:
            with self.subTest(skill=name):
                entry = by_name.get(name)
                self.assertIsNotNone(entry, f"Codex did not discover {name}")
                self.assertTrue(entry.get("description"), f"Codex did not provide a description for {name}")

        ordinary = json.loads(self.capture("请用两句话说明当前目录用途，不调用任何 Skill，也不运行命令。"))
        for plugin, skill in (("software-dev", "frontend-design"),
                              ("software-dev", "web-design-guidelines"),
                              ("software-dev", "vue-best-practices"),
                              ("software-dev", "fastapi"),
                              ("software-dev", "java-spring-boot"),
                              ("engineering-tools", "docker-build-strategies")):
            name = f"{plugin}:{skill}"
            self.assertIsNone(captured_skill_source(ordinary, name),
                              f"Codex injected the namespaced Skill body without an explicit invocation: {name}")
            self.assertTrue(contains_text(ordinary, by_name[f"{plugin}:{skill}"].get("description", "")),
                            f"Codex automatic Skill context omitted the discovery description for {plugin}:{skill}")

        for plugin, skill in (("software-dev", "frontend-design"),
                              ("software-dev", "web-design-guidelines"),
                              ("software-dev", "vue-best-practices"),
                              ("software-dev", "fastapi"),
                              ("software-dev", "java-spring-boot"),
                              ("engineering-tools", "docker-build-strategies")):
            with self.subTest(invocation=f"{plugin}:{skill}"):
                name = f"{plugin}:{skill}"
                entry = by_name[name]
                installed_path = Path(entry["path"])
                skill_file = installed_path / "SKILL.md" if installed_path.is_dir() else installed_path
                source_file = ROOT / "plugins" / plugin / "skills" / skill / "SKILL.md"
                self.assertTrue(skill_file.is_file(), f"Codex discovery path does not resolve to SKILL.md: {entry['path']}")
                self.assertEqual(skill_file.read_bytes(), source_file.read_bytes(),
                                 f"Codex installed Skill differs from repository snapshot: {entry['path']}")

                source_text = source_file.read_text(encoding="utf-8")
                source_body = skill_body(plugin, skill)
                explicit = json.loads(self.capture(
                    f"${name} 仅验证完整 Skill 正文已加载，不执行正文、不修改文件。"
                ))
                text_fields = text_values(explicit)
                captured = captured_skill_source(explicit, name)
                self.assertIsNotNone(captured, f"Codex explicit invocation did not inject a Skill body for {name}")
                captured_path, injected_source = captured
                self.assertTrue(source_text.startswith(injected_source),
                                f"Codex injected content is not a prefix of the installed Skill file: {captured_path}")
                body_offset = injected_source.find(source_body[:40])
                self.assertGreaterEqual(body_offset, 0,
                                        f"Codex injected content has no Skill body marker for {name}")
                captured_body = injected_source[body_offset:]
                captured_body_content = captured_body.rstrip()
                self.assertTrue(captured_body_content.startswith(source_body[:128]),
                                f"Codex explicit invocation did not inject the Skill instructions for {name}")
                body_prefix_matches = source_body.startswith(captured_body_content)
                self.assertTrue(body_prefix_matches,
                                f"Codex injected body is neither a complete Skill nor its exact source prefix: {name}")
                complete = captured_body_content == source_body
                injected_bytes = injected_source.encode("utf-8")
                raw_source = source_file.read_bytes()
                byte_prefix = raw_source.startswith(injected_bytes)
                first_8000_bytes = injected_bytes == raw_source[:8000]
                self.assertTrue(complete or first_8000_bytes,
                                f"Codex injected an unexpected partial body length for {name}")
                truncation_markers = [marker for marker in ("[truncated]", "…", "TRUNCATED")
                                      if any(marker in item for item in text_fields)]
                print(
                    f"Codex CLI skill={name} path={entry['path']} request_count={len(self.requests)} "
                    f"installed_bytes={len(raw_source)} injected_bytes={len(injected_bytes)} "
                    f"byte_prefix={byte_prefix} first_8000_bytes={first_8000_bytes} "
                    f"injected_chars={len(injected_source)} body_chars={len(source_body)} "
                    f"injected_body_chars={len(captured_body_content)} "
                    f"injected_body_bytes={len(captured_body_content.encode('utf-8'))} complete={complete} "
                    f"first={source_body[:72]!r} injected_tail={captured_body_content[-72:]!r} "
                    f"source_next={source_body[len(captured_body_content):len(captured_body_content) + 72]!r} "
                    f"truncation_markers={truncation_markers!r}",
                    flush=True,
                )


if __name__ == "__main__":
    unittest.main()
