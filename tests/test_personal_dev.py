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
    / "dev-delegate"
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


def payload_for_final_review(effort: str = "high") -> dict:
    return payload_with(
        model("gpt-6-luna", "high", "xhigh"),
        model("gpt-6.1-sol", "none", "minimal", "low", "medium", "high", "xhigh", "max", "ultra"),
    ) | {
        "final_review_required": True,
        "primary_effort": effort,
        "primary_effort_source": "current-turn",
    }


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
                model("gpt-6.2-luna", "high", "xhigh"),
                model("gpt-6.10-luna", "high", "xhigh"),
            )
        )

        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["coding"], {"model": "gpt-6.10-luna", "effort": "high"})
        self.assertEqual(result["review"], {"model": "gpt-6.10-luna", "effort": "xhigh"})
        self.assertEqual(
            result["display"],
            [
                "编码模型：gpt-6.10-luna｜思考强度：high",
                "验收模型：gpt-6.10-luna｜思考强度：xhigh",
            ],
        )

    def test_selects_major_only_model_for_minor_primary(self) -> None:
        result = select_models(payload_with(model("gpt-6-luna", "high", "xhigh")))

        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["coding"]["model"], "gpt-6-luna")

    def test_rejects_models_from_an_older_major(self) -> None:
        self.assert_blocked(payload_with(model("gpt-6.10-luna", "high", "xhigh")) | {"primary_model": "gpt-7-sol"})

    def test_rejects_unknown_primary_and_unapproved_coding_series(self) -> None:
        unknown_primary = payload_with(model("gpt-6.2-luna", "high", "xhigh"))
        unknown_primary["primary_model"] = "codex-next-sol"
        self.assert_blocked(unknown_primary)

        self.assert_blocked(payload_with(model("gpt-6.2-foo", "high", "xhigh")))

    def test_rejects_distinct_ids_with_the_same_numeric_version(self) -> None:
        self.assert_blocked(
            payload_with(
                model("gpt-6-luna", "high", "xhigh"),
                model("gpt-6.0-luna", "high", "xhigh"),
            )
        )

    def test_rejects_duplicate_model_ids(self) -> None:
        self.assert_blocked(
            payload_with(
                model("gpt-6.2-luna", "high", "xhigh"),
                model("gpt-6.2-luna", "high", "xhigh"),
            )
        )

    def test_rejects_malformed_inventory_and_effort_fields(self) -> None:
        self.assert_blocked(payload_with({"id": "gpt-6.2-luna", "efforts": "high,xhigh"}))
        self.assert_blocked(payload_with({"id": 62, "efforts": ["high", "xhigh"]}))

    def test_rejects_non_string_source_fields(self) -> None:
        payload = payload_with(model("gpt-6.2-luna", "high", "xhigh"))
        payload["primary_model_source"] = ["current-turn"]

        self.assert_blocked(payload)

    def test_rejects_malformed_effort_and_override_types_without_raising(self) -> None:
        invalid_payloads = [
            payload_with({"id": "gpt-6.2-luna", "efforts": None}),
            payload_with({"id": "gpt-6.2-luna", "efforts": ["xhigh", None]}),
        ]

        invalid_override = payload_with(model("codex-custom-preview", "high", "xhigh"))
        invalid_override.update(model_override=["codex-custom-preview"], override_confirmed=True)
        invalid_payloads.append(invalid_override)

        invalid_confirmation = payload_with(model("codex-custom-preview", "high", "xhigh"))
        invalid_confirmation.update(model_override="codex-custom-preview", override_confirmed="yes")
        invalid_payloads.append(invalid_confirmation)

        invalid_effort = payload_with(model("gpt-6.2-luna", "high", "xhigh"))
        invalid_effort["coding_effort"] = ["xhigh"]
        invalid_payloads.append(invalid_effort)

        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                self.assert_blocked(payload)

    def test_rejects_missing_required_effort(self) -> None:
        for efforts in (("xhigh",), ("high",)):
            with self.subTest(efforts=efforts):
                self.assert_blocked(payload_with(model("gpt-6.2-luna", *efforts)))

    def test_does_not_fall_back_when_highest_model_lacks_effort(self) -> None:
        for supported_effort in ("high", "xhigh"):
            with self.subTest(supported_effort=supported_effort):
                self.assert_blocked(
                    payload_with(
                        model("gpt-6.2-luna", "high", "xhigh"),
                        model("gpt-6.10-luna", supported_effort),
                    )
                )

    def test_confirmed_exact_override_can_use_a_renamed_model_series(self) -> None:
        payload = payload_with(model("codex-custom-preview", "high", "xhigh"))
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
        payload = payload_with(model("codex-custom-preview", "high", "xhigh"))
        payload.update(model_override="codex-custom-preview", override_confirmed=False)

        self.assert_blocked(payload)

    def test_confirmed_override_still_requires_a_reliable_primary_source(self) -> None:
        payload = payload_with(model("codex-custom-preview", "high", "xhigh"))
        payload.update(
            primary_model="codex-new-generation",
            primary_model_source="global-default",
            model_override="codex-custom-preview",
            override_confirmed=True,
        )

        self.assert_blocked(payload)

    def test_confirmed_override_still_requires_primary_model_identity(self) -> None:
        payload = payload_with(model("codex-custom-preview", "high", "xhigh"))
        payload.update(
            primary_model="",
            model_override="codex-custom-preview",
            override_confirmed=True,
        )

        self.assert_blocked(payload)

    def test_uses_explicit_effort_overrides_and_checks_them(self) -> None:
        for coding_effort, review_effort in (("low", "high"), ("xhigh", "max")):
            with self.subTest(coding_effort=coding_effort, review_effort=review_effort):
                payload = payload_with(model("gpt-6.2-luna", coding_effort, review_effort))
                payload.update(coding_effort=coding_effort, review_effort=review_effort)

                result = select_models(payload)

                self.assertEqual(result["status"], "READY")
                self.assertEqual(result["coding"]["effort"], coding_effort)
                self.assertEqual(result["review"]["effort"], review_effort)

    def test_single_role_override_preserves_other_role_default(self) -> None:
        for overrides, coding_effort, review_effort in (
            ({"coding_effort": "low"}, "low", "xhigh"),
            ({"review_effort": "low"}, "high", "low"),
        ):
            with self.subTest(overrides=overrides):
                payload = payload_with(model("gpt-6.2-luna", "low", "high", "xhigh", "max"))
                payload.update(overrides)

                result = select_models(payload)

                self.assertEqual(result["status"], "READY")
                self.assertEqual(result["coding"]["effort"], coding_effort)
                self.assertEqual(result["review"]["effort"], review_effort)

    def test_unsupported_user_effort_does_not_fall_back_to_default(self) -> None:
        for field in ("coding_effort", "review_effort"):
            with self.subTest(field=field):
                payload = payload_with(model("gpt-6.2-luna", "high", "xhigh"))
                payload[field] = "medium"

                self.assert_blocked(payload)

    def test_does_not_mutate_input_payload(self) -> None:
        payload = payload_with(model("gpt-6.2-luna", "high", "xhigh"))
        original = copy.deepcopy(payload)

        select_models(payload)

        self.assertEqual(payload, original)

    def test_final_review_defaults_one_level_below_current_session(self) -> None:
        for session, expected in (
            ("ultra", "max"), ("max", "xhigh"), ("xhigh", "high"),
            ("high", "medium"), ("medium", "low"), ("low", "minimal"),
            ("minimal", "none"), ("none", "none"),
        ):
            with self.subTest(session=session):
                result = select_models(payload_for_final_review(session))
                self.assertEqual(result["status"], "READY")
                self.assertEqual(result["final_review"], {"model": "gpt-6.1-sol", "effort": expected})
                self.assertEqual(result["coding"], {"model": "gpt-6-luna", "effort": "high"})
                self.assertEqual(result["review"], {"model": "gpt-6-luna", "effort": "xhigh"})
                self.assertIn(f"会话上限：{session}", result["display"][2])

    def test_difficult_final_review_escalates_to_session_limit(self) -> None:
        for effort in ("high", "xhigh", "max", "ultra"):
            with self.subTest(effort=effort):
                payload = payload_for_final_review(effort) | {"final_review_escalated": True}
                result = select_models(payload)
                self.assertEqual(result["status"], "READY")
                self.assertEqual(result["final_review"], {"model": "gpt-6.1-sol", "effort": effort})

    def test_final_review_missing_adjacent_level_only_moves_lower(self) -> None:
        payload = payload_for_final_review("xhigh")
        payload["models"][1]["efforts"] = ["medium", "xhigh", "ultra"]
        self.assertEqual(select_models(payload)["final_review"]["effort"], "medium")
        payload["models"][1]["efforts"] = ["xhigh", "ultra"]
        self.assert_blocked(payload)

    def test_final_review_blocks_unavailable_session_model(self) -> None:
        payload = payload_for_final_review()
        payload["models"] = [model("gpt-6-luna", "high", "xhigh")]
        self.assert_blocked(payload)

    def test_final_review_escalation_requires_the_exact_supported_limit(self) -> None:
        payload = payload_for_final_review() | {"final_review_escalated": True}
        payload["models"][1]["efforts"] = ["medium", "xhigh", "ultra"]
        self.assert_blocked(payload)
        self.assert_blocked(payload_for_final_review("none") | {"final_review_escalated": True})

    def test_final_review_requires_verified_effort_and_source(self) -> None:
        for field, value in (
            ("primary_effort", None), ("primary_effort", []),
            ("primary_effort", "private-marker"), ("primary_effort_source", None),
            ("primary_effort_source", []), ("primary_effort_source", "global-default"),
        ):
            with self.subTest(field=field, value=value):
                result = self.assert_blocked(payload_for_final_review() | {field: value})
                self.assertNotIn("private-marker", json.dumps(result))
        for field in ("primary_effort", "primary_effort_source"):
            payload = payload_for_final_review()
            payload.pop(field)
            self.assert_blocked(payload)
        self.assertEqual(
            select_models(payload_for_final_review() | {"primary_effort_source": "user"})["status"],
            "READY",
        )

    def test_final_review_validates_flags_and_rejects_unused_metadata(self) -> None:
        for field in ("final_review_required", "final_review_escalated"):
            for value in (None, 1, "false", []):
                with self.subTest(field=field, value=value):
                    self.assert_blocked(payload_for_final_review() | {field: value})
        self.assert_blocked(payload_for_final_review() | {"final_review_required": False})

    def test_final_review_cannot_switch_to_a_different_model(self) -> None:
        self.assert_blocked(payload_for_final_review() | {"final_review_model": "gpt-6-astra"})
        payload = payload_for_final_review() | {
            "model_override": "gpt-6-luna", "override_confirmed": True,
        }
        self.assertEqual(select_models(payload)["final_review"]["model"], payload["primary_model"])

    def test_optional_final_review_preserves_existing_contract_and_input(self) -> None:
        payload = payload_with(model("gpt-6-luna", "high", "xhigh"))
        baseline = select_models(payload)
        self.assertEqual(select_models(payload | {"final_review_required": False}), baseline)
        self.assertNotIn("final_review", baseline)
        payload = payload_for_final_review()
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
        payload = payload_with(model("gpt-6.2-luna", "high", "xhigh"))

        process = self.run_cli(json.dumps(payload))

        self.assertEqual(process.returncode, 0)
        self.assertEqual(process.stderr, "")
        self.assertEqual(self.parse_single_json_line(process.stdout)["status"], "READY")

    def test_final_review_cli_reports_actual_effort_and_session_limit(self) -> None:
        process = self.run_cli(json.dumps(payload_for_final_review("high")))
        self.assertEqual(process.returncode, 0)
        self.assertEqual(process.stderr, "")
        result = self.parse_single_json_line(process.stdout)
        self.assertEqual(result["final_review"], {"model": "gpt-6.1-sol", "effort": "medium"})
        self.assertIn("会话上限：high", result["display"][2])

    def test_blocked_cli_prints_json_and_exits_two(self) -> None:
        payload = payload_with(model("gpt-6.2-luna", "xhigh"))

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
