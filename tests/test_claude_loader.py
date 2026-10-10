"""Opt-in real Claude Code installation and loader checks, with no real model.

AGENT_MANAGER_CLAUDE_TESTS=1 enables isolated CLAUDE_CONFIG_DIR fixtures.
A localhost API rejects inference after capturing the actual request context.
"""
import http.server
import json
import os
from pathlib import Path
import queue
import subprocess
import tempfile
import threading
import unittest

from test_configure_project import editor

ROOT = Path(__file__).resolve().parents[1]


def run(command, env, cwd):
    result = subprocess.run(command, env=env, cwd=cwd, capture_output=True,
                            text=True, encoding="utf-8", errors="replace", timeout=45)
    if result.returncode:
        raise AssertionError(f"Claude fixture command failed ({command[1:3]}): {result.stdout} {result.stderr}")
    return result.stdout


@unittest.skipUnless(os.environ.get("AGENT_MANAGER_CLAUDE_TESTS") == "1", "Opt-in isolated Claude loader validation")
class ClaudeLoaderTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix=".skill-sync-claude-", dir=ROOT)
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
        self.assertEqual(run(["claude", "--version"], self.env, self.project).strip(), editor.VERIFIED_CLAUDE)
        run(["claude", "plugin", "marketplace", "add", str(ROOT)], self.env, self.project)

    def install(self, name):
        run(["claude", "plugin", "install", f"{name}@agent-marketplace"], self.env, self.project)

    def context(self):
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
            result = subprocess.run(["claude", "-p", "fixture", "--verbose", "--output-format", "stream-json",
                                     "--no-session-persistence", "--model", "claude-sonnet-4-6",
                                     "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}', "--tools", "Skill"],
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
            for skill in (ROOT / entry["source"] / "skills").iterdir():
                self.assertIn(skill.name, details)
        init, context = self.context()
        commands = init.get("slash_commands", [])
        for entry in catalog["plugins"]:
            for skill in (ROOT / entry["source"] / "skills").iterdir():
                self.assertIn(f'{entry["name"]}:{skill.name}', commands)
        self.assertIn("frontend-dev:vue", context)
        for name in ("common-workflow:handoff", "agent-manager:resolve-conflicts",
                     "agent-manager:check-updates", "agent-manager:configure-project"):
            self.assertNotIn(name, context)

    def test_project_switches_override_user_and_local_overrides_project(self):
        self.install("frontend-dev")
        config = self.project / ".claude/settings.json"
        config.parent.mkdir(exist_ok=True)
        installed = json.loads((self.home / "plugins/installed_plugins.json").read_text(encoding="utf-8"))
        record = installed["plugins"]["frontend-dev@agent-marketplace"][0]
        payload = {"agent": "claude", "explicit_invocation": True, "scope": "project",
                   "requests": [{"kind": "plugin", "target": "frontend-dev@agent-marketplace", "enabled": False}],
                   "inventory": {"complete": True, "claude_version": editor.VERIFIED_CLAUDE,
                                 "project_root": str(self.project), "project_config_active": True,
                                 "project_overrides_effective": True, "targets": [{"kind": "plugin",
                                 "id": "frontend-dev@agent-marketplace", "name": "frontend-dev",
                                 "path": record["installPath"], "installed": True, "configuration": "marketplace"}]}}
        user_config = self.home / "settings.json"
        before = user_config.read_bytes()
        editor.configure(payload, self.project)
        init, context = self.context()
        self.assertNotIn("frontend-dev:vue", init["slash_commands"])
        self.assertNotIn("frontend-dev:vue", context)
        self.assertEqual(user_config.read_bytes(), before)
        user = json.loads(before)
        user["enabledPlugins"]["frontend-dev@agent-marketplace"] = False
        user_config.write_text(json.dumps(user))
        payload["requests"][0]["enabled"] = True
        editor.configure(payload, self.project)
        init, context = self.context()
        self.assertIn("frontend-dev:vue", init["slash_commands"])
        self.assertIn("frontend-dev:vue", context)
        local = config.parent / "settings.local.json"
        local.write_text('{"enabledPlugins":{"frontend-dev@agent-marketplace":false}}')
        with self.assertRaisesRegex(editor.Blocked, "LOCAL SETTINGS OVERRIDE"):
            editor.configure(payload, self.project)
        init, context = self.context()
        self.assertNotIn("frontend-dev:vue", init["slash_commands"])
        self.assertNotIn("frontend-dev:vue", context)


if __name__ == "__main__":
    unittest.main()
