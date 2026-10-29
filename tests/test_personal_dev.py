"""Explicit worker/reviewer arguments, inventory validation and CLI failures."""

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "plugins/personal-dev/skills/dev-review/scripts/model_validation.py"


def load_selector(path):
    spec = importlib.util.spec_from_file_location("personal_dev_models", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SELECTOR = load_selector(SCRIPT_PATH)


def model(model_id, *efforts):
    return {"id": model_id, "efforts": list(efforts)}


def payload_with(*models):
    return {
        "worker": "6-luna:high",
        "reviewer": "6.1-terra:high",
        "inventory_source": "current-spawn-tool",
        "models": list(models) or [
            model("gpt-6-luna", "high", "low"),
            model("gpt-6.1-terra", "high", "max"),
        ],
    }


class ExplicitModelContract:
    """Both helpers share validation, with entry-specific required roles."""

    required_roles = ("worker", "reviewer")
    usage = SELECTOR.USAGE

    def assert_blocked(self, payload, reason=None):
        result = self.selector(payload)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue(result["reasons"])
        self.assertEqual(result["usage"], self.usage)
        self.assertFalse({"worker", "reviewer", "coding", "review", "final_review"} & result.keys())
        if reason:
            self.assertIn(reason, " ".join(result["reasons"]))
        self.assertNotIn("private-marker", json.dumps(result))
        return result

    def test_explicit_short_ids_and_distinct_roles(self):
        result = self.selector(payload_with())
        self.assertEqual(result, {
            "status": "READY",
            "worker": {"model": "gpt-6-luna", "effort": "high"},
            "reviewer": {"model": "gpt-6.1-terra", "effort": "high"},
            "display": [
                "worker 模型：gpt-6-luna｜思考强度：high",
                "reviewer 模型：gpt-6.1-terra｜思考强度：high",
            ],
        })

    def test_missing_each_or_both_roles_blocks_before_inventory(self):
        for missing in (("worker",), ("reviewer",), ("worker", "reviewer")):
            required_missing = set(missing) & set(self.required_roles)
            if not required_missing:
                continue
            payload = payload_with()
            for field in (*missing, "models"):
                payload.pop(field)
            with self.subTest(missing=missing):
                result = self.assert_blocked(payload, "missing required")
                for role in required_missing:
                    self.assertIn(role, result["reasons"][0])

    def test_empty_or_malformed_role_has_no_defaults(self):
        for role in ("worker", "reviewer"):
            for value in (None, [], {}, 1, "", "high", "6-luna", ":high",
                          "6-luna:", "6-luna:high:extra", "6luna high extra", "6luna :"):
                with self.subTest(role=role, value=value):
                    self.assert_blocked(payload_with() | {role: value}, role)

    def test_unsupported_model_or_effort_fails_for_either_role(self):
        for role in ("worker", "reviewer"):
            for value, reason in (("private-marker:high", "model"),
                                  ("gpt-6-luna:private-marker", "effort"),
                                  ("gpt-6-luna:max", "effort")):
                with self.subTest(role=role, value=value):
                    self.assert_blocked(payload_with() | {role: value}, reason)

    def test_does_not_choose_latest_or_use_another_model_for_effort(self):
        payload = payload_with(
            model("gpt-6-luna", "high"),
            model("gpt-6.99-luna", "high", "max"),
            model("gpt-6.1-terra", "high"),
        )
        self.assertEqual(self.selector(payload)["worker"]["model"], "gpt-6-luna")
        self.assert_blocked(payload | {"worker": "6-luna:max"}, "effort")
        self.assert_blocked(payload | {"worker": "6.2-luna:high"}, "model")
        self.assert_blocked(payload | {"reviewer": "gpt-6.1-terra:max"}, "effort")

    def test_full_ids_native_ids_and_same_model_are_allowed(self):
        payload = payload_with(
            model("native-model-v2", "medium", "high"),
            model("other-model", "low"),
        ) | {"worker": "native-model-v2:medium", "reviewer": "native-model-v2:high"}
        result = self.selector(payload)
        self.assertEqual(result["worker"], {"model": "native-model-v2", "effort": "medium"})
        self.assertEqual(result["reviewer"], {"model": "native-model-v2", "effort": "high"})
        result = self.selector(payload_with() | {"worker": "gpt-6-luna:low"})
        self.assertEqual(result["worker"]["effort"], "low")

    def test_common_model_and_effort_formats_use_exact_inventory_values(self):
        expected = self.selector(payload_with())
        for worker in ("6luna", "6-luna", "gpt6luna", "gpt-6-luna", "GPT6LUNA"):
            for reviewer in ("6.1terra", "6.1-terra", "gpt6.1terra", "gpt-6.1-terra", "GPT6.1TERRA"):
                for separator in (":", " ", " : "):
                    with self.subTest(worker=worker, reviewer=reviewer, separator=separator):
                        payload = payload_with() | {
                            "worker": f" {worker}{separator}HIGH ",
                            "reviewer": f"{reviewer}{separator}h",
                        }
                        self.assertEqual(self.selector(payload), expected)
        payload = payload_with(model("GPT-6-LUNA", "Medium"), model("gpt-6.1-terra", "high"))
        result = self.selector(payload | {"worker": "6luna:M"})
        self.assertEqual(result["worker"], {"model": "GPT-6-LUNA", "effort": "Medium"})

    def test_normalization_preserves_version_and_family_and_never_falls_back(self):
        payload = payload_with(
            model("gpt-6-luna", "high"), model("gpt-6.1-terra", "high"),
            model("gpt-6-terra", "high"), model("gpt-61-terra", "high"),
        )
        for value in ("terra:high", "gpt-terra:high", "6.2terra:high", "6.1ter:high", "6_luna:high"):
            with self.subTest(value=value):
                self.assert_blocked(payload | {"worker": value}, "model")
        result = self.selector(payload | {"reviewer": "61terra:HIGH"})
        self.assertEqual(result["reviewer"]["model"], "gpt-61-terra")
        for effort in ("max", "ultra", "hh", "med"):
            self.assert_blocked(payload | {"worker": f"6luna:{effort}"}, "effort")
        self.assert_blocked(payload | {"worker": "6.2luna:h"}, "model")
        self.assert_blocked(payload_with(model("gpt-6.1-terra", "high")), "model")
        for effort in ("h", "m"):
            self.assert_blocked(payload_with(
                model("gpt-6-luna", "low", "max"), model("gpt-6.1-terra", "high"),
            ) | {"worker": f"6luna:{effort}"}, "effort")

    def test_normalized_inventory_collisions_block_before_effort_selection(self):
        payload = payload_with(
            model("gpt-6-luna", "high"), model("gpt6luna", "low"),
            model("gpt-6.1-terra", "high"),
        )
        for requested in ("6luna:high", "gpt-6-luna:high"):
            self.assert_blocked(payload | {"worker": requested}, "ambiguous")
        payload = payload_with(model("gpt-6-luna", "high", "HIGH"), model("gpt-6.1-terra", "high"))
        self.assert_blocked(payload, "effort")

    def test_effort_is_only_checked_against_requested_model(self):
        payload = payload_with(model("opus", "native-effort"), model("sonnet", "high"))
        # A syntactically valid native effort need not belong to a Codex ranking.
        payload.update(worker="sonnet:high", reviewer="opus:adaptive")
        payload["models"][0]["efforts"] = ["adaptive"]
        self.assertEqual(self.selector(payload)["reviewer"]["effort"], "adaptive")

    def test_short_id_must_not_match_two_routes(self):
        payload = payload_with(
            model("6-luna", "high"), model("gpt-6-luna", "high"),
            model("gpt-6.1-terra", "high"),
        )
        self.assert_blocked(payload, "ambiguous")
        self.assert_blocked(payload | {"worker": "gpt-6-luna:high"}, "ambiguous")

    def test_inventory_must_be_current_and_nonempty(self):
        for updates in ({"inventory_source": None}, {"inventory_source": []},
                        {"inventory_source": "cache"}, {"models": []},
                        {"models": {}}, {"models": None}):
            with self.subTest(updates=updates):
                self.assert_blocked(payload_with() | updates)
        for field in ("models", "inventory_source"):
            payload = payload_with()
            payload.pop(field)
            self.assert_blocked(payload)

    def test_malformed_inventory_is_blocked_without_exceptions(self):
        invalid = [
            None, {}, {"id": "x", "efforts": [], "extra": True},
            model("", "high"), model(6, "high"),
            {"id": "x", "efforts": None}, {"id": "x", "efforts": "high"},
            {"id": "x", "efforts": [[]]}, model("x", "", "high"),
            model("x", "high", "high"),
        ]
        for item in invalid:
            with self.subTest(item=item):
                self.assert_blocked(payload_with(item))
        self.assert_blocked(payload_with(model("x", "high"), model("x", "low")), "duplicate")
        self.assert_blocked(payload_with(model("gpt-6-luna"), model("gpt-6.1-terra", "high")), "effort")

    def test_legacy_roles_and_automatic_selection_metadata_are_rejected(self):
        fields = ("plan", "final", "coding_effort", "review_effort",
                  "audit_effort", "verification_effort", "primary_model",
                  "primary_model_source", "primary_effort", "primary_effort_source",
                  "model_override", "override_confirmed", "final_review_required",
                  "final_review_escalated", "final_review_model", "final_review_effort",
                  "unexpected")
        for field in fields:
            with self.subTest(field=field):
                self.assert_blocked(payload_with() | {field: "private-marker"}, "unsupported")

    def test_no_input_mutation_and_no_partial_ready_config(self):
        for payload in (payload_with(), payload_with() | {"reviewer": "private-marker:high"}):
            original = copy.deepcopy(payload)
            self.selector(payload)
            self.assertEqual(payload, original)

    def test_all_fixed_alias_combinations_normalize_to_two_roles(self):
        expected = self.selector(payload_with())
        for worker in ("worker", "work", "w", "code"):
            for reviewer in ("reviewer", "review", "r", "check"):
                with self.subTest(worker=worker, reviewer=reviewer):
                    payload = payload_with()
                    payload[worker] = payload.pop("worker")
                    payload[reviewer] = payload.pop("reviewer")
                    original = copy.deepcopy(payload)
                    self.assertEqual(self.selector(payload), expected)
                    self.assertEqual(payload, original)

    def test_alias_duplicates_block_even_when_values_are_equal(self):
        for alias in ("work", "w", "code", "review", "r", "check"):
            role = "worker" if alias in ("work", "w", "code") else "reviewer"
            for value in (payload_with()[role], "private-marker:high"):
                with self.subTest(alias=alias, value=value):
                    self.assert_blocked(payload_with() | {alias: value}, f"duplicate {role}")

    def test_single_alias_does_not_supply_the_other_required_role(self):
        for alias in ("work", "w", "code", "review", "r", "check"):
            payload = payload_with()
            role = "worker" if alias in ("work", "w", "code") else "reviewer"
            missing = "reviewer" if role == "worker" else "worker"
            value = payload.pop(role)
            payload.pop(missing)
            payload[alias] = value
            if missing in self.required_roles:
                self.assert_blocked(payload, f"missing required parameter(s): {missing}")
            else:
                self.assertEqual(self.selector(payload)["status"], "READY")

    def test_non_object_inputs_are_blocked(self):
        for value in (None, [], "", 1, "private-marker"):
            self.assert_blocked(value)


class SelectModelsTests(ExplicitModelContract, unittest.TestCase):
    selector = staticmethod(SELECTOR.select_models)


class ModelArgumentsTests(unittest.TestCase):
    def test_requested_formats_parse_and_validate_to_exact_models(self):
        for text in (
            "w 6luna high r 6.1terra high",
            "w 6luna:high r 6.1terra:high",
            "w=6luna:high r=6.1terra:high",
            "w 6-luna:high r 6.1-terra:high",
            "worker 6-luna high reviewer 6.1-terra high",
            "worker gpt-6-luna high reviewer gpt-6.1-terra high",
            "W = GPT6LUNA : H R GPT6.1TERRA HIGH",
            "r 6.1terra : high\tw 6luna h",
        ):
            with self.subTest(text=text):
                parsed = SELECTOR.parse_arguments(text)
                self.assertEqual(SELECTOR.select_models(payload_with() | parsed),
                                 SELECTOR.select_models(payload_with()))

    def test_parse_both_parameters_in_either_order(self):
        for text in (
            "worker=6-luna:high reviewer=6.1-terra:high",
            " reviewer=6.1-terra:high\tworker=6-luna:high ",
        ):
            self.assertEqual(SELECTOR.parse_arguments(text), {
                "worker": "6-luna:high", "reviewer": "6.1-terra:high",
            })
            result = SELECTOR.select_models(payload_with() | SELECTOR.parse_arguments(text))
            self.assertEqual(result["status"], "READY")

    def test_parser_fails_for_missing_duplicate_legacy_or_malformed(self):
        for text in ("", "worker=6-luna:high", "reviewer=6.1-terra:high",
                     "worker=6-luna:high worker=6-luna:low reviewer=6.1-terra:high",
                     "plan=6-luna:high reviewer=6.1-terra:high",
                     "worker=6-luna reviewer=6.1-terra:high",
                     "worker=6-luna:high reviewer=:high",
                     "worker=6-luna:high reviewer=6.1-terra:high final=x:high",
                     None):
            with self.subTest(text=text):
                with self.assertRaisesRegex(ValueError, "worker=<model>:<effort> reviewer=<model>:<effort>"):
                    SELECTOR.parse_arguments(text)

    def test_all_alias_pairs_parse_and_reject_duplicate_normalized_roles(self):
        for worker in ("worker", "work", "w", "code"):
            for reviewer in ("reviewer", "review", "r", "check"):
                text = f"{worker}=6-luna:high {reviewer}=6.1-terra:high"
                self.assertEqual(SELECTOR.parse_arguments(text), {
                    "worker": "6-luna:high", "reviewer": "6.1-terra:high",
                })
                for duplicate in ("worker=6-luna:high", "reviewer=6.1-terra:high"):
                    with self.assertRaisesRegex(ValueError, "duplicate"):
                        SELECTOR.parse_arguments(f"{text} {duplicate}")

    def test_role_separators_accept_aliases_case_and_surrounding_whitespace(self):
        separators = ("=", ":", " ", " = ", " : ", "\t")
        for worker in ("worker", "work", "w", "code", "WORKER", "W"):
            for reviewer in ("reviewer", "review", "r", "check", "Reviewer", "R"):
                for worker_separator in separators:
                    for reviewer_separator in separators:
                        text = f" \t{reviewer}{reviewer_separator}6luna:high  {worker}{worker_separator}6luna:high\n"
                        with self.subTest(text=text):
                            self.assertEqual(SELECTOR.parse_arguments(text), {
                                "reviewer": "6luna:high", "worker": "6luna:high",
                            })

    def test_mixed_separators_still_reject_duplicate_normalized_roles(self):
        for duplicate in ("W:6-luna:high", "work 6-luna:high", "Reviewer : 6.1-terra:high", "R 6.1-terra:high"):
            with self.subTest(duplicate=duplicate), self.assertRaisesRegex(ValueError, "duplicate"):
                SELECTOR.parse_arguments(f"w=6-luna:high r:6.1-terra:high {duplicate}")

    def test_relaxed_separators_still_reject_missing_or_extra_values(self):
        invalid = ("w::6-luna:high", "w==6-luna:high", "w:=6-luna:high", "worker6-luna:high",
                   "w 6-luna", "w 6-luna:", "w 6-luna:high:extra", "w 6-luna high extra",
                   "w 6-luna:high,r:6.1-terra:high", "w 6luna h r 6.1terra",
                   "w 6-luna:high task", "plan 6-luna:high", "w", "w:", "w =")
        for text in invalid:
            with self.subTest(text=text), self.assertRaises(ValueError):
                SELECTOR.parse_arguments(f"{text} reviewer:6.1-terra:high")

    def test_semantic_errors_are_blocked_after_parsing(self):
        for text, reason in (
            ("w unknown high r 6.1terra high", "model"),
            ("w 6luna high r terra high", "model"),
            ("w 6luna imaginary r 6.1terra high", "effort"),
            ("w 6luna max r 6.1terra high", "effort"),
        ):
            with self.subTest(text=text):
                parsed = SELECTOR.parse_arguments(text)
                payload = payload_with()
                payload["models"].append(model("gpt-6-terra", "high"))
                result = SELECTOR.select_models(payload | parsed)
                self.assertEqual(result["status"], "BLOCKED")
                self.assertIn(reason, result["reasons"][0])

    def test_missing_diagnostic_names_each_missing_parameter(self):
        for text, role in (("worker=6-luna:high", "reviewer"),
                           ("reviewer=6.1-terra:high", "worker")):
            with self.assertRaisesRegex(ValueError, f"missing required parameter.*{role}"):
                SELECTOR.parse_arguments(text)


class CliContract:
    required_roles = ("worker", "reviewer")
    usage = SELECTOR.USAGE

    def run_cli(self, text):
        return subprocess.run(
            [sys.executable, "-B", str(self.script)], input=text, text=True,
            capture_output=True, check=False,
        )

    def test_ready_cli(self):
        process = self.run_cli(json.dumps(payload_with()))
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(process.stderr, "")
        self.assertEqual(len(process.stdout.splitlines()), 1)
        self.assertEqual(json.loads(process.stdout)["reviewer"],
                         {"model": "gpt-6.1-terra", "effort": "high"})

    def test_cli_normalizes_model_and_effort_formats(self):
        process = self.run_cli(json.dumps(payload_with() | {
            "worker": "GPT6LUNA H", "reviewer": "6.1terra:HIGH",
        }))
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(json.loads(process.stdout), SELECTOR.select_models(payload_with()))

    def test_cli_normalizes_aliases_and_blocks_duplicate_roles(self):
        payload = payload_with()
        payload["w"] = payload.pop("worker")
        payload["check"] = payload.pop("reviewer")
        process = self.run_cli(json.dumps(payload))
        self.assertEqual(process.returncode, 0, process.stderr)
        result = json.loads(process.stdout)
        self.assertEqual(set(result), {"status", "worker", "reviewer", "display"})
        self.assertEqual(result["worker"], {"model": "gpt-6-luna", "effort": "high"})
        self.assertEqual(result["reviewer"], {"model": "gpt-6.1-terra", "effort": "high"})
        payload["review"] = payload["check"]
        process = self.run_cli(json.dumps(payload))
        self.assertEqual(process.returncode, 2)
        self.assertIn("duplicate reviewer", json.loads(process.stdout)["reasons"][0])

    def test_missing_invalid_and_unsupported_cli_exit_two(self):
        missing_worker = payload_with()
        missing_worker.pop("worker")
        missing_reviewer = payload_with()
        missing_reviewer.pop("reviewer")
        missing_payloads = [missing_reviewer, {}]
        if "worker" in self.required_roles:
            missing_payloads.append(missing_worker)
        for payload in (*missing_payloads,
                        payload_with() | {"worker": "private-marker:high"},
                        payload_with() | {"reviewer": "6-luna:max"}):
            with self.subTest(payload=payload):
                process = self.run_cli(json.dumps(payload))
                self.assertEqual(process.returncode, 2, process.stderr)
                result = json.loads(process.stdout)
                self.assertEqual(result["status"], "BLOCKED")
                self.assertEqual(result["usage"], self.usage)
                self.assertEqual(process.stderr, "")
                self.assertNotIn("private-marker", process.stdout)

    def test_invalid_or_nonobject_json_hides_input(self):
        for text in ('{"private-marker":"secret"', '["private-marker"]', "null"):
            process = self.run_cli(text)
            self.assertEqual(process.returncode, 2)
            self.assertEqual(json.loads(process.stdout)["status"], "BLOCKED")
            self.assertNotIn("private-marker", process.stdout + process.stderr)


class SelectModelsCliTests(CliContract, unittest.TestCase):
    script = SCRIPT_PATH


if __name__ == "__main__":
    unittest.main()
