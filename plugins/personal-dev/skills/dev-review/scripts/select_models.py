"""Require reviewer only, using the shared two-role validator."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


SIBLING_HELPER_PATH = (
    Path(__file__).resolve().parents[2] / "dev-delegate/scripts/select_models.py"
)
USAGE = "reviewer=<model>:<effort>"


def select_models(payload: object) -> dict:
    try:
        spec = importlib.util.spec_from_file_location(
            "personal_dev_shared_select_models", SIBLING_HELPER_PATH,
        )
        if spec is None or spec.loader is None:
            raise ImportError("shared validator is unavailable")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except (OSError, ImportError, SyntaxError):
        return {"status": "BLOCKED", "reasons": ["shared model validator is unavailable"], "usage": USAGE}
    return module.select_models(payload, required_roles=("reviewer",))


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, UnicodeError):
        result = {"status": "BLOCKED", "reasons": ["stdin must contain valid JSON"], "usage": USAGE}
    else:
        result = select_models(payload)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "READY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
