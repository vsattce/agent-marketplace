"""Adapt review roles to the shared personal-dev model selector."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


SIBLING_HELPER_PATH = (
    Path(__file__).resolve().parents[2]
    / "delegated-development"
    / "scripts"
    / "select_models.py"
)
_INPUT_FIELDS = {
    "primary_model",
    "primary_model_source",
    "inventory_source",
    "models",
    "model_override",
    "override_confirmed",
    "audit_effort",
    "verification_effort",
}


def _blocked(reason: str) -> dict[str, Any]:
    return {"status": "BLOCKED", "reasons": [reason]}


def _load_sibling_selector():
    try:
        spec = importlib.util.spec_from_file_location(
            "personal_dev_shared_select_models",
            SIBLING_HELPER_PATH,
        )
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        selector = getattr(module, "select_models", None)
        return selector if callable(selector) else None
    except Exception:
        return None


def _safe_reason(reason: object) -> str:
    if not isinstance(reason, str):
        return "model selection could not be validated"

    # The shared helper includes the supplied effort in these two diagnostics.
    # Keep the useful role information without echoing untrusted input.
    if reason.startswith("selected model does not support coding effort "):
        return "selected model does not support requested audit effort"
    if reason.startswith("selected model does not support review effort "):
        return "selected model does not support requested verification effort"

    safe_reasons = {
        "input must be a JSON object",
        "input contains unsupported fields",
        "required input fields are missing",
        "primary_model must be a non-empty string",
        "primary_model_source must be current-turn or user",
        "inventory_source must be current-spawn-tool",
        "models must be a non-empty list",
        "each model must contain only id and efforts fields",
        "model id must be a non-empty string",
        "model inventory contains duplicate ids",
        "model efforts must be a list of non-empty strings",
        "model efforts contain duplicates",
        "coding_effort must be a non-empty string",
        "review_effort must be a non-empty string",
        "override_confirmed must be a boolean",
        "model_override must be a non-empty model id",
        "model_override requires explicit confirmation",
        "override_confirmed requires model_override",
        "confirmed model_override is not present in the tool inventory",
        "primary_model identity is not a recognized complete model id",
        "no approved Luna model matches the primary model major version",
        "different model ids have the same numeric version",
    }
    if reason in safe_reasons:
        return reason.replace("coding_effort", "audit_effort").replace(
            "review_effort", "verification_effort"
        )
    return "model selection could not be validated"


def select_models(payload: object) -> dict[str, Any]:
    """Resolve review and verification models through the existing shared rules."""
    if not isinstance(payload, dict):
        return _blocked("input must be a JSON object")
    if set(payload) - _INPUT_FIELDS:
        return _blocked("input contains unsupported fields")

    selector = _load_sibling_selector()
    if selector is None:
        return _blocked("shared model selector helper is unavailable")

    shared_payload = dict(payload)
    shared_payload["coding_effort"] = payload.get("audit_effort", "xhigh")
    shared_payload["review_effort"] = payload.get("verification_effort", "max")
    shared_payload.pop("audit_effort", None)
    shared_payload.pop("verification_effort", None)

    try:
        result = selector(shared_payload)
    except Exception:
        return _blocked("shared model selector could not complete")

    if not isinstance(result, dict):
        return _blocked("shared model selector returned an invalid result")
    if result.get("status") != "READY":
        raw_reasons = result.get("reasons", ["model selection could not be validated"])
        if not isinstance(raw_reasons, list) or not raw_reasons:
            raw_reasons = ["model selection could not be validated"]
        return {
            "status": "BLOCKED",
            "reasons": [_safe_reason(reason) for reason in raw_reasons],
        }

    coding = result.get("coding")
    review = result.get("review")
    if not isinstance(coding, dict) or not isinstance(review, dict):
        return _blocked("shared model selector returned an invalid result")
    model_id = coding.get("model")
    audit_effort = coding.get("effort")
    verification_model = review.get("model")
    verification_effort = review.get("effort")
    if not all(
        isinstance(value, str) and value
        for value in (model_id, audit_effort, verification_model, verification_effort)
    ):
        return _blocked("shared model selector returned an invalid result")

    return {
        "status": "READY",
        "audit": {"model": model_id, "effort": audit_effort},
        "verification": {"model": verification_model, "effort": verification_effort},
        "display": [
            f"审查模型：{model_id}｜思考强度：{audit_effort}",
            f"复核模型：{verification_model}｜思考强度：{verification_effort}",
        ],
    }


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, UnicodeError):
        result = _blocked("stdin must contain valid JSON")
    else:
        result = select_models(payload)

    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "READY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
