"""Validate explicit worker/reviewer settings against the current spawn tool."""

from __future__ import annotations

import json
import re
import sys


USAGE = "worker=<model>:<effort> reviewer=<model>:<effort>"
_ROLES = ("worker", "reviewer")
_ROLE_ALIASES = {
    "worker": "worker", "work": "worker", "w": "worker", "code": "worker",
    "reviewer": "reviewer", "review": "reviewer", "r": "reviewer", "check": "reviewer",
}
_INPUT_FIELDS = {*_ROLE_ALIASES, "inventory_source", "models"}
_SETTING_RE = re.compile(r"([A-Za-z0-9][A-Za-z0-9._/-]*):([a-z]+)")


def _blocked(reason: str) -> dict:
    return {"status": "BLOCKED", "reasons": [reason], "usage": USAGE}


def parse_arguments(arguments: str) -> dict:
    """Parse model arguments extracted separately from the Skill task text."""
    if not isinstance(arguments, str):
        raise ValueError(f"model arguments must be text; use {USAGE}")
    roles = {}
    for token in arguments.split():
        key, separator, value = token.partition("=")
        if not separator or key not in _ROLE_ALIASES:
            raise ValueError(f"unsupported model argument; use {USAGE}")
        key = _ROLE_ALIASES[key]
        if key in roles:
            raise ValueError(f"duplicate {key} parameter; use {USAGE}")
        if _SETTING_RE.fullmatch(value) is None:
            raise ValueError(f"{key} must use <model>:<effort>; use {USAGE}")
        roles[key] = value
    missing = [role for role in _ROLES if role not in roles]
    if missing:
        raise ValueError(f"missing required parameter(s): {', '.join(missing)}; use {USAGE}")
    return roles


def select_models(payload: dict) -> dict:
    """Return exactly two user-chosen configurations, with no model defaults."""
    if not isinstance(payload, dict):
        return _blocked("input must be a JSON object")
    roles = {}
    for key, value in payload.items():
        if key in _ROLE_ALIASES:
            role = _ROLE_ALIASES[key]
            if role in roles:
                return _blocked(f"duplicate {role} parameter (including aliases)")
            roles[role] = value
    missing = [role for role in _ROLES if role not in roles]
    if missing:
        return _blocked(f"missing required parameter(s): {', '.join(missing)}")
    if set(payload) - _INPUT_FIELDS:
        return _blocked("input contains unsupported fields; legacy model roles are not accepted")
    requested = {}
    for role in _ROLES:
        value = roles[role]
        match = _SETTING_RE.fullmatch(value) if isinstance(value, str) else None
        if match is None:
            return _blocked(f"{role} must use <model>:<effort>")
        requested[role] = match.groups()
    if payload.get("inventory_source") != "current-spawn-tool":
        return _blocked("inventory_source must be current-spawn-tool")
    models = payload.get("models")
    if not isinstance(models, list) or not models:
        return _blocked("models must be a non-empty list from the current Harness")
    models_by_id = {}
    for item in models:
        if not isinstance(item, dict) or set(item) != {"id", "efforts"}:
            return _blocked("each model must contain only id and efforts fields")
        model_id, efforts = item["id"], item["efforts"]
        if not isinstance(model_id, str) or not model_id.strip():
            return _blocked("model id must be a non-empty string")
        if model_id in models_by_id:
            return _blocked("model inventory contains duplicate ids")
        if not isinstance(efforts, list) or any(
            not isinstance(effort, str) or not effort.strip() for effort in efforts
        ):
            return _blocked("model efforts must be a list of non-empty strings")
        if len(set(efforts)) != len(efforts):
            return _blocked("model efforts contain duplicates")
        models_by_id[model_id] = efforts

    result = {"status": "READY"}
    for role, (model_id, effort) in requested.items():
        # The sole shorthand omits the literal gpt- prefix and must match one
        # exact current-tool ID. No family or latest-version selection occurs.
        candidates = [candidate for candidate in models_by_id
                      if candidate == model_id or candidate == f"gpt-{model_id}"]
        if len(candidates) != 1:
            return _blocked(f"{role} model is unavailable or ambiguous in the current Harness")
        actual_id = candidates[0]
        if effort not in models_by_id[actual_id]:
            return _blocked(f"{role} effort is not supported by the requested model in the current Harness")
        result[role] = {"model": actual_id, "effort": effort}
    result["display"] = [
        f"{role} 模型：{result[role]['model']}｜思考强度：{result[role]['effort']}"
        for role in _ROLES
    ]
    return result


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
