"""Opt-in real Codex loader tests with isolated config and no model inference.

Set AGENT_MANAGER_CODEX_TESTS=1 to run. A localhost provider captures the actual
request context then stops the CLI; no model, external API, or Skill body executes.
"""

import http.server
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("codex_probe", ROOT / "plugins/agent-manager/skills/resolve-conflicts/scripts/probe_codex.py")
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)


@unittest.skipUnless(os.environ.get("AGENT_MANAGER_CODEX_TESTS") == "1", "Opt-in isolated Codex loader validation")
class CodexLoaderTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="agent-manager-loader-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.project = self.root / "project"
        self.project.mkdir()
        self.agent_home = self.root / "codex-home"
        self.agent_home.mkdir()
        self.env = {**os.environ, "CODEX_HOME": str(self.agent_home), "GIT_TERMINAL_PROMPT": "0"}
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
            '[model_providers.loader-probe]\nname = "Local loader capture"\n'
            f'base_url = "http://127.0.0.1:{self.server.server_port}/v1"\n'
            'wire_api = "responses"\nrequires_openai_auth = false\n'
            f'[projects.{json.dumps(str(self.project))}]\ntrust_level = "trusted"\n'
        )
        (self.agent_home / "config.toml").write_text(config, encoding="utf-8")
        probe.run(["git", "init", "--quiet"], self.env, self.project)
        probe.run(["codex", "plugin", "marketplace", "add", str(ROOT), "--json"], self.env, self.project)
        probe.run(["codex", "plugin", "add", "agent-manager@agent-marketplace", "--json"], self.env, self.project)

    def capture(self, prompt):
        self.requests.clear()
        self.request_received.clear()
        self.release_response.clear()
        self.handler_done.clear()
        process = subprocess.Popen(["codex", "exec", "--ephemeral", "--json", "--color", "never", prompt],
                                   cwd=self.project, env=self.env, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        captured = False
        try:
            captured = self.request_received.wait(timeout=40)
        finally:
            probe.stop_process(process)
            self.release_response.set()
            if captured:
                self.handler_done.wait(timeout=10)
        self.assertTrue(captured and self.requests, f"No loader request captured; exit {process.returncode}")
        return json.dumps(self.requests[0], ensure_ascii=False)

    def test_discovery_and_manual_only_context(self):
        inventory, _ = probe.rpc_skills(self.project, self.env)
        owned = [item for item in inventory if item["name"].startswith("agent-manager:")]
        self.assertEqual({item["name"] for item in owned}, {"agent-manager:resolve-conflicts", "agent-manager:check-updates"})
        self.assertTrue(all(item.get("enabled", True) for item in owned))
        ordinary = self.capture("请讨论当前项目的 Plugin / Skill 冲突和版本更新检查。")
        for marker in ("# 整理当前项目的 Agent 冲突", "# 只读检查 Agent 更新", "Only use when explicitly invoked by the user."):
            self.assertNotIn(marker, ordinary)
        for name, marker in (("resolve-conflicts", "# 整理当前项目的 Agent 冲突"), ("check-updates", "# 只读检查 Agent 更新")):
            with self.subTest(invocation=name):
                context = self.capture(f"${name} 仅验证 Skill 加载，本轮无需执行任何操作。")
                print(f"\nBare ${name} injected: {marker in context}", flush=True)
            with self.subTest(invocation=f"agent-manager:{name}"):
                context = self.capture(f"$agent-manager:{name} 仅验证 Skill 加载，本轮无需执行任何操作。")
                self.assertTrue(marker in context, "Namespaced explicit invocation did not inject Skill instructions")

    def test_project_skill_disable_runtime_probe(self):
        result = probe.probe(ROOT / "plugins/common-workflow", "handoff")
        checks = result["Checks"]
        self.assertTrue(checks["project_same_name_enabled"])
        self.assertTrue(checks["other_plugin_skills_enabled"])
        self.assertTrue(checks["user_config_unchanged"])
        self.assertTrue(checks["no_plugin_disable_rule"])
        self.assertTrue(checks["project_rule_loaded"])
        if result["Status"] == "BLOCKED":
            self.assertFalse(checks["global_target_disabled"])
            self.assertTrue(result["IsolatedUserLayerControlWorks"])
        else:
            self.assertTrue(checks["global_target_disabled"])


if __name__ == "__main__":
    unittest.main()
