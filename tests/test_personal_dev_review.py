"""Review adapter contract and safe CLI behavior."""

import copy
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "plugins/personal-dev/skills/dev-review/scripts/select_models.py"


def load_review_module():
    if not SCRIPT_PATH.is_file():
        return None
    spec = importlib.util.spec_from_file_location("personal_dev_review_select_models", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


REVIEW_MODULE = load_review_module()


def payload_with(*models: dict) -> dict:
    return {
        "primary_model": "gpt-6.1-sol",
        "primary_model_source": "current-turn",
        "inventory_source": "current-spawn-tool",
        "models": list(models),
    }


def model(model_id: str, *efforts: str) -> dict:
    return {"id": model_id, "efforts": list(efforts)}


class ReviewModelAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertIsNotNone(REVIEW_MODULE, "review model adapter is not implemented")

    def assert_blocked(self, payload: object) -> dict:
        result = REVIEW_MODULE.select_models(payload)
        self.assertEqual(result.get("status"), "BLOCKED")
        self.assertIsInstance(result.get("reasons"), list)
        self.assertTrue(all(isinstance(reason, str) and reason for reason in result["reasons"]))
        return result

    def test_maps_review_roles_to_shared_selector_and_displays_actual_models(self) -> None:
        result = REVIEW_MODULE.select_models(
            payload_with(
                model("gpt-6.2-luna", "xhigh", "max"),
                model("gpt-6.10-luna", "xhigh", "max"),
            )
        )

        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["audit"], {"model": "gpt-6.10-luna", "effort": "xhigh"})
        self.assertEqual(result["verification"], {"model": "gpt-6.10-luna", "effort": "max"})
        self.assertEqual(
            result["display"],
            [
                "审查模型：gpt-6.10-luna｜思考强度：xhigh",
                "复核模型：gpt-6.10-luna｜思考强度：max",
            ],
        )

    def test_uses_explicit_effort_overrides(self) -> None:
        payload = payload_with(model("gpt-6.2-luna", "low", "high"))
        payload.update(audit_effort="low", verification_effort="high")

        result = REVIEW_MODULE.select_models(payload)

        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["audit"]["effort"], "low")
        self.assertEqual(result["verification"]["effort"], "high")

    def test_confirmed_user_override_uses_shared_selector_rules(self) -> None:
        payload = payload_with(model("codex-custom-preview", "xhigh", "max"))
        payload.update(
            primary_model="gpt-6.1-sol",
            model_override="codex-custom-preview",
            override_confirmed=True,
        )

        result = REVIEW_MODULE.select_models(payload)

        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["audit"]["model"], "codex-custom-preview")
        self.assertEqual(result["verification"]["model"], "codex-custom-preview")

    def test_blocks_missing_identity_and_unsupported_effort(self) -> None:
        payload = payload_with(model("gpt-6.2-luna", "xhigh", "max"))
        payload["primary_model"] = ""
        self.assert_blocked(payload)

        unsupported = payload_with(model("gpt-6.2-luna", "xhigh"))
        self.assert_blocked(unsupported)

        newer_model_lacks_verification = payload_with(
            model("gpt-6.2-luna", "xhigh", "max"),
            model("gpt-6.10-luna", "xhigh"),
        )
        self.assert_blocked(newer_model_lacks_verification)

    def test_blocks_unknown_fields_and_mixed_legacy_role_fields_without_echo(self) -> None:
        for field in ("unexpected", "coding_effort", "review_effort"):
            payload = payload_with(model("gpt-6.2-luna", "xhigh", "max"))
            payload[field] = "private-marker"
            result = self.assert_blocked(payload)
            self.assertNotIn("private-marker", json.dumps(result, ensure_ascii=False))

    def test_blocks_helper_unavailable_without_exposing_its_path(self) -> None:
        with patch.object(REVIEW_MODULE, "SIBLING_HELPER_PATH", Path("private-helper-marker.py")):
            result = self.assert_blocked(payload_with(model("gpt-6.2-luna", "xhigh", "max")))

        self.assertNotIn("private-helper-marker", json.dumps(result, ensure_ascii=False))

    def test_does_not_mutate_input(self) -> None:
        payload = payload_with(model("gpt-6.2-luna", "xhigh", "max"))
        original = copy.deepcopy(payload)

        REVIEW_MODULE.select_models(payload)

        self.assertEqual(payload, original)


class ReviewModelAdapterCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(SCRIPT_PATH.is_file(), "review model adapter is not implemented")

    def run_cli(self, input_text: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            input=input_text,
            text=True,
            capture_output=True,
            check=False,
        )

    def parse_single_json_line(self, output: str) -> dict:
        self.assertEqual(len(output.splitlines()), 1)
        self.assertTrue(output.endswith("\n"))
        return json.loads(output)

    def test_ready_cli_prints_contract_and_exits_zero(self) -> None:
        process = self.run_cli(json.dumps(payload_with(model("gpt-6.2-luna", "xhigh", "max"))))

        self.assertEqual(process.returncode, 0)
        self.assertEqual(process.stderr, "")
        self.assertEqual(self.parse_single_json_line(process.stdout)["status"], "READY")

    def test_blocked_cli_hides_untrusted_effort_value_and_exits_two(self) -> None:
        payload = payload_with(model("gpt-6.2-luna", "xhigh", "max"))
        payload["audit_effort"] = "private-marker"

        process = self.run_cli(json.dumps(payload))

        self.assertEqual(process.returncode, 2)
        self.assertEqual(process.stderr, "")
        result = self.parse_single_json_line(process.stdout)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertNotIn("private-marker", process.stdout + process.stderr)

    def test_invalid_json_is_blocked_without_echoing_input(self) -> None:
        process = self.run_cli('{"private-marker":"do-not-echo"')

        self.assertEqual(process.returncode, 2)
        self.assertEqual(self.parse_single_json_line(process.stdout)["status"], "BLOCKED")
        self.assertNotIn("do-not-echo", process.stdout + process.stderr)


if __name__ == "__main__":
    unittest.main()
