"""Opt-in real Claude Code installation and loader checks, with no real model.

MARKETPLACE_CLAUDE_TESTS=1 enables isolated CLAUDE_CONFIG_DIR fixtures.
A localhost API rejects inference after capturing the actual request context.
"""
import http.server
import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import threading
import unittest

from temp_paths import temporary_test_directory

ROOT = Path(__file__).resolve().parents[1]


def skill_body(plugin, skill):
    text = (ROOT / "plugins" / plugin / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) != 3:
        raise AssertionError(f"Invalid Skill frontmatter: {plugin}:{skill}")
    return parts[2].strip()


def contains_text(value, expected):
    if isinstance(value, str):
        # Claude preserves CRLF from local Skills; read_text normalizes it to LF.
        return expected.replace("\r\n", "\n") in value.replace("\r\n", "\n")
    if isinstance(value, dict):
        return any(contains_text(child, expected) for child in value.values())
    if isinstance(value, list):
        return any(contains_text(child, expected) for child in value)
    return False


def run(command, env, cwd):
    result = subprocess.run(command, env=env, cwd=cwd, capture_output=True,
                            text=True, encoding="utf-8", errors="replace", timeout=45)
    if result.returncode:
        raise AssertionError(f"Claude fixture command failed ({command[1:3]}): {result.stdout} {result.stderr}")
    return result.stdout


@unittest.skipUnless(os.environ.get("MARKETPLACE_CLAUDE_TESTS") == "1", "Opt-in isolated Claude loader validation")
class ClaudeLoaderTests(unittest.TestCase):
    def setUp(self):
        self.temporary = temporary_test_directory("claude-loader")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()
        self.project = self.base / "project"
        self.project.mkdir()
        self.home = self.base / "user"
        self.home.mkdir()
        self.env = {key: value for key, value in os.environ.items()
                    if not key.startswith(("ANTHROPIC_", "CLAUDE_"))}
        self.env.update({"CLAUDE_CONFIG_DIR": str(self.home), "ANTHROPIC_API_KEY": "isolated-fixture",
                         "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1", "DISABLE_AUTOUPDATER": "1",
                         "CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY": "1"})
        subprocess.run(["git", "init", "--quiet", str(self.project)], check=True, capture_output=True)
        self.claude_version = run(["claude", "--version"], self.env, self.project).strip()
        run(["claude", "plugin", "marketplace", "add", str(ROOT)], self.env, self.project)

    def install(self, name):
        run(["claude", "plugin", "install", f"{name}@agent-marketplace"], self.env, self.project)

    def context(self, prompt="fixture", tools="Skill"):
        requests = queue.Queue()

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                payload = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
                if "messages" in payload:
                    requests.put(payload)
                response = json.dumps({"type": "error", "error": {"type": "invalid_request_error", "message": "Fixture capture complete"}}).encode()
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(response)))
                self.end_headers()
                self.wfile.write(response)

            def log_message(self, *args):
                pass

        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        env = {**self.env, "ANTHROPIC_BASE_URL": f"http://127.0.0.1:{server.server_port}"}
        try:
            result = subprocess.run(["claude", "-p", prompt, "--verbose", "--output-format", "stream-json",
                                     "--no-session-persistence", "--model", "claude-sonnet-4-6",
                                     "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}', "--tools", tools],
                                    env=env, cwd=self.project, capture_output=True, text=True, encoding="utf-8",
                                    errors="replace", timeout=45)
            init = next((json.loads(line) for line in result.stdout.splitlines()
                         if line.startswith('{') and json.loads(line).get("subtype") == "init"), None)
            self.assertIsNotNone(init, f"Claude fixture failed: {result.stdout[-1200:]} {result.stderr[-1200:]}")
            self.assertFalse(requests.empty(), "Claude did not send context to the fixture API")
            payloads = []
            while not requests.empty():
                payloads.append(requests.get_nowait())
            return init, json.dumps(payloads, ensure_ascii=False)
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=5)

    def test_all_plugins_install_discover_and_preserve_manual_only(self):
        catalog = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
        for entry in catalog["plugins"]:
            self.install(entry["name"])
            details = run(["claude", "plugin", "details", entry["name"]], self.env, self.project)
            for skill_entry in (ROOT / entry["source"] / "skills").glob("*/SKILL.md"):
                self.assertIn(skill_entry.parent.name, details)
        init, context = self.context()
        commands = init.get("slash_commands", [])
        for entry in catalog["plugins"]:
            for skill_entry in (ROOT / entry["source"] / "skills").glob("*/SKILL.md"):
                self.assertIn(f'{entry["name"]}:{skill_entry.parent.name}', commands)
        self.assertIn("software-dev:vue", commands)
        for obsolete in ("software-dev:java-spring-boot", "testing-automation:webapp-testing", "testing-automation:playwright-cli"):
            self.assertNotIn(obsolete, commands)
        self.assertEqual(
            {name for name in commands if name.startswith("software-dev:")},
            {f"software-dev:{name}" for name in (
                "frontend-design", "web-design-guidelines", "vue", "fastapi", "java-springboot",
            )},
        )
        self.assertIn("software-dev:vue", context)
        for plugin, skill in (("software-dev", "fastapi"),
                              ("software-dev", "java-springboot"),
                              ("software-dev", "vue"),
                              ("engineering-tools", "docker-build-strategies"),
                              ("engineering-tools", "docker-compose-patterns"),
                              ("engineering-tools", "playwright-cli")):
            with self.subTest(invocation=f"{plugin}:{skill}"):
                _, explicit = self.context(
                    f"/{plugin}:{skill} 仅验证完整 Skill 正文已加载，不执行正文、不修改文件。"
                )
                self.assertTrue(contains_text(json.loads(explicit), skill_body(plugin, skill)))
        self.assertNotIn("matt:handoff", context)

    def test_project_upgrade_entry_and_shared_rules_load(self):
        for directory in (".claude/skills/upgrade", ".agents/skills/upgrade"):
            shutil.copytree(ROOT / directory, self.project / directory)
        for filename in ("AGENTS.md", "CLAUDE.md"):
            shutil.copyfile(ROOT / filename, self.project / filename)
        init, context = self.context()
        self.assertEqual(init["slash_commands"].count("upgrade"), 1)
        self.assertIn("当前仅支持 Claude Code 和 Codex", context)
        _, explicit = self.context("/upgrade 仅验证入口加载，不同步、不修改文件。")
        self.assertIn("../../../.agents/skills/upgrade/SKILL.md", explicit)



if __name__ == "__main__":
    unittest.main()
