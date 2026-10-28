"""Review requires reviewer only and retains strict shared model validation."""

import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from test_personal_dev import (
    CliContract, ExplicitModelContract, ROOT, SELECTOR, load_selector, model, payload_with,
)


SCRIPT_PATH = ROOT / "plugins/personal-dev/skills/dev-review/scripts/select_models.py"
REVIEW_MODULE = load_selector(SCRIPT_PATH)


class ReviewModelAdapterTests(ExplicitModelContract, unittest.TestCase):
    selector = staticmethod(REVIEW_MODULE.select_models)
    required_roles = ("reviewer",)
    usage = REVIEW_MODULE.USAGE

    def test_reviewer_only_accepts_all_role_separators_without_worker(self):
        for alias in ("reviewer", "review", "r", "check", "REVIEWER", "R"):
            for separator in ("=", ":", " ", " = ", " : ", "\t"):
                with self.subTest(alias=alias, separator=separator):
                    parsed = SELECTOR.parse_arguments(f"{alias}{separator}6luna:high", required_roles=("reviewer",))
                    self.assertEqual(parsed, {"reviewer": "6luna:high"})
        for text in ("r:6luna:high REVIEWER 6luna:high", "r 6luna:HIGH", "r:6luna: high", "r:"):
            with self.subTest(text=text), self.assertRaisesRegex(ValueError, "reviewer=<model>:<effort>"):
                SELECTOR.parse_arguments(text, required_roles=("reviewer",))

    def test_reviewer_only_aliases_need_no_worker_inventory(self):
        for alias in ("reviewer", "review", "r", "check"):
            with self.subTest(alias=alias):
                payload = {
                    alias: "6.1-terra:high",
                    "inventory_source": "current-spawn-tool",
                    "models": [model("gpt-6.1-terra", "high")],
                }
                original = copy.deepcopy(payload)
                self.assertEqual(self.selector(payload), {
                    "status": "READY",
                    "reviewer": {"model": "gpt-6.1-terra", "effort": "high"},
                    "display": ["reviewer 模型：gpt-6.1-terra｜思考强度：high"],
                })
                self.assertEqual(payload, original)
                self.assertEqual(SELECTOR.parse_arguments(
                    f"{alias}=6.1-terra:high", required_roles=("reviewer",),
                ), {"reviewer": "6.1-terra:high"})

    def test_reviewer_only_rejects_duplicates_bad_config_and_missing_inventory(self):
        payload = payload_with()
        payload.pop("worker")
        for updates, reason in (({"r": payload["reviewer"]}, "duplicate reviewer"),
                                ({"reviewer": "private-marker:high"}, "model"),
                                ({"reviewer": "6.1-terra:low"}, "effort"),
                                ({"reviewer": ""}, "reviewer"),
                                ({"inventory_source": "cache"}, "inventory_source"),
                                ({"models": []}, "models"),
                                ({"final": "private-marker:high"}, "unsupported")):
            with self.subTest(updates=updates):
                self.assert_blocked(payload | updates, reason)
        for text in ("", "w=6-luna:high", "r=6.1-terra:high check=6.1-terra:high",
                     "reviewer=6.1-terra", "reviewer=6.1-terra:high final=x:high"):
            with self.subTest(text=text):
                with self.assertRaisesRegex(ValueError, "reviewer=<model>:<effort>"):
                    SELECTOR.parse_arguments(text, required_roles=("reviewer",))

    def test_review_adapter_preserves_both_role_configs_and_contract(self):
        payload = payload_with() | {"worker": "6-luna:low", "reviewer": "6.1-terra:max"}
        original = copy.deepcopy(payload)
        self.assertEqual(REVIEW_MODULE.select_models(payload), SELECTOR.select_models(payload))
        self.assertEqual(payload, original)
        result = REVIEW_MODULE.select_models(payload)
        self.assertEqual(set(result), {"status", "worker", "reviewer", "display"})

    def test_helper_unavailable_is_blocked_without_exposing_path(self):
        with patch.object(REVIEW_MODULE, "SIBLING_HELPER_PATH", Path("private-helper-marker.py")):
            result = self.assert_blocked(payload_with(), "unavailable")
        self.assertNotIn("private-helper-marker", str(result))


class ReviewModelAdapterCliTests(CliContract, unittest.TestCase):
    script = SCRIPT_PATH
    required_roles = ("reviewer",)
    usage = REVIEW_MODULE.USAGE

    def test_reviewer_only_cli_and_entry_specific_failure(self):
        for alias in ("reviewer", "review", "r", "check"):
            payload = payload_with()
            payload.pop("worker")
            payload[alias] = payload.pop("reviewer")
            process = self.run_cli(json.dumps(payload))
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertEqual(process.stderr, "")
            result = json.loads(process.stdout)
            self.assertEqual(set(result), {"status", "reviewer", "display"})
            self.assertEqual(len(result["display"]), 1)
        result = json.loads(self.run_cli('{}').stdout)
        self.assertEqual(result["usage"], "reviewer=<model>:<effort>")
        self.assertEqual(result["reasons"], ["missing required parameter(s): reviewer"])


if __name__ == "__main__":
    unittest.main()
