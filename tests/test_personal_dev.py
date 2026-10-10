import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path


SCRIPT_DIR = (
    Path(__file__).resolve().parents[1]
    / "plugins"
    / "personal-dev"
    / "skills"
    / "delegated-development"
    / "scripts"
)
sys.path.insert(0, str(SCRIPT_DIR))

from select_models import select_models


SCRIPT_PATH = SCRIPT_DIR / "select_models.py"


def payload_with(*models: dict) -> dict:
    return {
        "primary_model": "gpt-6.1-sol",
        "primary_model_source": "current-turn",
        "inventory_source": "current-spawn-tool",
        "models": list(models),
    }


def model(model_id: str, *efforts: str) -> dict:
    return {"id": model_id, "efforts": list(efforts)}


class SelectModelsTests(unittest.TestCase):
    def assert_blocked(self, payload: dict) -> dict:
        result = select_models(payload)
        self.assertEqual(result.get("status"), "BLOCKED")
        self.assertIsInstance(result.get("reasons"), list)
        self.assertTrue(all(isinstance(reason, str) and reason for reason in result["reasons"]))
        return result

    def test_selects_highest_numeric_same_major_model(self) -> None:
        result = select_models(
            payload_with(
                model("gpt-6.2-luna", "xhigh", "max"),
                model("gpt-6.10-luna", "xhigh", "max"),
            )
        )

        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["coding"], {"model": "gpt-6.10-luna", "effort": "xhigh"})
        self.assertEqual(result["review"], {"model": "gpt-6.10-luna", "effort": "max"})
        self.assertEqual(
            result["display"],
            [
                "编码模型：gpt-6.10-luna｜思考强度：xhigh",
                "验收模型：gpt-6.10-luna｜思考强度：max",
            ],
        )

    def test_selects_major_only_model_for_minor_primary(self) -> None:
        result = select_models(payload_with(model("gpt-6-luna", "xhigh", "max")))

        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["coding"]["model"], "gpt-6-luna")

    def test_rejects_models_from_an_older_major(self) -> None:
        self.assert_blocked(payload_with(model("gpt-6.10-luna", "xhigh", "max")) | {"primary_model": "gpt-7-sol"})

    def test_rejects_unknown_primary_and_unapproved_coding_series(self) -> None:
        unknown_primary = payload_with(model("gpt-6.2-luna", "xhigh", "max"))
        unknown_primary["primary_model"] = "codex-next-sol"
        self.assert_blocked(unknown_primary)

        self.assert_blocked(payload_with(model("gpt-6.2-foo", "xhigh", "max")))

    def test_rejects_distinct_ids_with_the_same_numeric_version(self) -> None:
        self.assert_blocked(
            payload_with(
                model("gpt-6-luna", "xhigh", "max"),
                model("gpt-6.0-luna", "xhigh", "max"),
            )
        )

    def test_rejects_duplicate_model_ids(self) -> None:
        self.assert_blocked(
            payload_with(
                model("gpt-6.2-luna", "xhigh", "max"),
                model("gpt-6.2-luna", "xhigh", "max"),
            )
        )

    def test_rejects_malformed_inventory_and_effort_fields(self) -> None:
        self.assert_blocked(payload_with({"id": "gpt-6.2-luna", "efforts": "xhigh,max"}))
        self.assert_blocked(payload_with({"id": 62, "efforts": ["xhigh", "max"]}))

    def test_rejects_non_string_source_fields(self) -> None:
        payload = payload_with(model("gpt-6.2-luna", "xhigh", "max"))
        payload["primary_model_source"] = ["current-turn"]

        self.assert_blocked(payload)

    def test_rejects_malformed_effort_and_override_types_without_raising(self) -> None:
        invalid_payloads = [
            payload_with({"id": "gpt-6.2-luna", "efforts": None}),
            payload_with({"id": "gpt-6.2-luna", "efforts": ["xhigh", None]}),
        ]

        invalid_override = payload_with(model("codex-custom-preview", "xhigh", "max"))
        invalid_override.update(model_override=["codex-custom-preview"], override_confirmed=True)
        invalid_payloads.append(invalid_override)

        invalid_confirmation = payload_with(model("codex-custom-preview", "xhigh", "max"))
        invalid_confirmation.update(model_override="codex-custom-preview", override_confirmed="yes")
        invalid_payloads.append(invalid_confirmation)

        invalid_effort = payload_with(model("gpt-6.2-luna", "xhigh", "max"))
        invalid_effort["coding_effort"] = ["xhigh"]
        invalid_payloads.append(invalid_effort)

        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                self.assert_blocked(payload)

    def test_rejects_missing_required_effort(self) -> None:
        self.assert_blocked(payload_with(model("gpt-6.2-luna", "max")))

    def test_does_not_fall_back_when_highest_model_lacks_effort(self) -> None:
        self.assert_blocked(
            payload_with(
                model("gpt-6.2-luna", "xhigh", "max"),
                model("gpt-6.10-luna", "max"),
            )
        )

    def test_confirmed_exact_override_can_use_a_renamed_model_series(self) -> None:
        payload = payload_with(model("codex-custom-preview", "xhigh", "max"))
        payload.update(
            primary_model="codex-new-generation",
            model_override="codex-custom-preview",
            override_confirmed=True,
        )

        result = select_models(payload)

        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["coding"]["model"], "codex-custom-preview")
        self.assertEqual(result["review"]["model"], "codex-custom-preview")

    def test_unconfirmed_override_is_blocked(self) -> None:
        payload = payload_with(model("codex-custom-preview", "xhigh", "max"))
        payload.update(model_override="codex-custom-preview", override_confirmed=False)

        self.assert_blocked(payload)

    def test_confirmed_override_still_requires_a_reliable_primary_source(self) -> None:
        payload = payload_with(model("codex-custom-preview", "xhigh", "max"))
        payload.update(
            primary_model="codex-new-generation",
            primary_model_source="global-default",
            model_override="codex-custom-preview",
            override_confirmed=True,
        )

        self.assert_blocked(payload)

    def test_confirmed_override_still_requires_primary_model_identity(self) -> None:
        payload = payload_with(model("codex-custom-preview", "xhigh", "max"))
        payload.update(
            primary_model="",
            model_override="codex-custom-preview",
            override_confirmed=True,
        )

        self.assert_blocked(payload)

    def test_uses_explicit_effort_overrides_and_checks_them(self) -> None:
        payload = payload_with(model("gpt-6.2-luna", "low", "high"))
        payload.update(coding_effort="low", review_effort="high")

        result = select_models(payload)

        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["coding"]["effort"], "low")
        self.assertEqual(result["review"]["effort"], "high")

    def test_does_not_mutate_input_payload(self) -> None:
        payload = payload_with(model("gpt-6.2-luna", "xhigh", "max"))
        original = copy.deepcopy(payload)

        select_models(payload)

        self.assertEqual(payload, original)


class SelectModelsCliTests(unittest.TestCase):
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
        parsed = json.loads(output)
        self.assertIsInstance(parsed, dict)
        return parsed

    def test_ready_cli_prints_json_and_exits_zero(self) -> None:
        payload = payload_with(model("gpt-6.2-luna", "xhigh", "max"))

        process = self.run_cli(json.dumps(payload))

        self.assertEqual(process.returncode, 0)
        self.assertEqual(process.stderr, "")
        self.assertEqual(self.parse_single_json_line(process.stdout)["status"], "READY")

    def test_blocked_cli_prints_json_and_exits_two(self) -> None:
        payload = payload_with(model("gpt-6.2-luna", "max"))

        process = self.run_cli(json.dumps(payload))

        self.assertEqual(process.returncode, 2)
        self.assertEqual(process.stderr, "")
        self.assertEqual(self.parse_single_json_line(process.stdout)["status"], "BLOCKED")

    def test_invalid_json_is_blocked_without_echoing_input(self) -> None:
        input_text = '{"private-marker":"do-not-echo"'

        process = self.run_cli(input_text)

        self.assertEqual(process.returncode, 2)
        result = self.parse_single_json_line(process.stdout)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertNotIn("do-not-echo", process.stdout + process.stderr)

    def test_non_object_json_is_blocked_without_echoing_input(self) -> None:
        process = self.run_cli('["do-not-echo"]')

        self.assertEqual(process.returncode, 2)
        result = self.parse_single_json_line(process.stdout)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(process.stderr, "")
        self.assertNotIn("do-not-echo", process.stdout + process.stderr)


if __name__ == "__main__":
    unittest.main()
