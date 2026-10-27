"""The review entry uses exactly the shared worker/reviewer protocol."""

import copy
from pathlib import Path
import unittest
from unittest.mock import patch

from test_personal_dev import (
    CliContract, ExplicitModelContract, ROOT, SELECTOR, load_selector, payload_with,
)


SCRIPT_PATH = ROOT / "plugins/personal-dev/skills/dev-review/scripts/select_models.py"
REVIEW_MODULE = load_selector(SCRIPT_PATH)


class ReviewModelAdapterTests(ExplicitModelContract, unittest.TestCase):
    selector = staticmethod(REVIEW_MODULE.select_models)

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


if __name__ == "__main__":
    unittest.main()
