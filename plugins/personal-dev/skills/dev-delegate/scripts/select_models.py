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
_SETTING_RE = re.compile(r"([A-Za-z0-9][A-Za-z0-9._/-]*)(?:\s*:\s*|\s+)([A-Za-z]+)")
_ARGUMENT_RE = re.compile(rf"\s*([A-Za-z]+)(?:\s*[=:]\s*|\s+)({_SETTING_RE.pattern})(?=\s|$)")
_EFFORT_ALIASES = {"h": "high", "m": "medium"}


def _normalize_model(model_id: str) -> str:
    model_id = model_id.lower()
    match = re.fullmatch(r"(?:gpt-?)?([0-9]+(?:\.[0-9]+)*)-?([a-z][a-z0-9]*(?:-[a-z0-9]+)*)", model_id)
    if match:
        return f"gpt-{match[1]}-{match[2]}"
    return model_id


def _blocked(reason: str, usage: str = USAGE) -> dict:
    return {"status": "BLOCKED", "reasons": [reason], "usage": usage}


def parse_arguments(arguments: str, *, required_roles: tuple = _ROLES) -> dict:
    """Parse model arguments extracted separately from the Skill task text."""
    usage = " ".join(f"{role}=<model>:<effort>" for role in required_roles)
    if not isinstance(arguments, str):
        raise ValueError(f"model arguments must be text; use {usage}")
    arguments = arguments.strip()
    roles = {}
    position = 0
    while position < len(arguments):
        match = _ARGUMENT_RE.match(arguments, position)
        if match is None or match[1].lower() not in _ROLE_ALIASES:
            raise ValueError(f"unsupported model argument; separate role and value with =, : or whitespace; use {usage}")
        key = match[1].lower()
        position = match.end()
        key = _ROLE_ALIASES[key]
        if key in roles:
            raise ValueError(f"duplicate {key} parameter; use {usage}")
        roles[key] = f"{match[3]}:{match[4]}"
    missing = [role for role in required_roles if role not in roles]
    if missing:
        raise ValueError(f"missing required parameter(s): {', '.join(missing)}; use {usage}")
    return roles


def select_models(payload: dict, *, required_roles: tuple = _ROLES) -> dict:
    """Validate required and explicitly supplied roles, with no model defaults."""
    usage = " ".join(f"{role}=<model>:<effort>" for role in required_roles)

    def blocked(reason: str) -> dict:
        return _blocked(reason, usage)

    if not isinstance(payload, dict):
        return blocked("input must be a JSON object")
    roles = {}
    for key, value in payload.items():
        if key in _ROLE_ALIASES:
            role = _ROLE_ALIASES[key]
            if role in roles:
                return blocked(f"duplicate {role} parameter (including aliases)")
            roles[role] = value
    missing = [role for role in required_roles if role not in roles]
    if missing:
        return blocked(f"missing required parameter(s): {', '.join(missing)}")
    if set(payload) - _INPUT_FIELDS:
        return blocked("input contains unsupported fields; legacy model roles are not accepted")
    requested = {}
    for role in _ROLES:
        if role not in roles:
            continue
        value = roles[role]
        match = _SETTING_RE.fullmatch(value.strip()) if isinstance(value, str) else None
        if match is None:
            return blocked(f"{role} must provide model and effort; use <model>:<effort> or <model> <effort>")
        model_id, effort = match.groups()
        effort = effort.lower()
        requested[role] = (_normalize_model(model_id), _EFFORT_ALIASES.get(effort, effort))
    if payload.get("inventory_source") != "current-spawn-tool":
        return blocked("inventory_source must be current-spawn-tool")
    models = payload.get("models")
    if not isinstance(models, list) or not models:
        return blocked("models must be a non-empty list from the current Harness")
    models_by_id = {}
    for item in models:
        if not isinstance(item, dict) or set(item) != {"id", "efforts"}:
            return blocked("each model must contain only id and efforts fields")
        model_id, efforts = item["id"], item["efforts"]
        if not isinstance(model_id, str) or not model_id.strip():
            return blocked("model id must be a non-empty string")
        if model_id in models_by_id:
            return blocked("model inventory contains duplicate ids")
        if not isinstance(efforts, list) or any(
            not isinstance(effort, str) or not effort.strip() for effort in efforts
        ):
            return blocked("model efforts must be a list of non-empty strings")
        if len(set(efforts)) != len(efforts):
            return blocked("model efforts contain duplicates")
        models_by_id[model_id] = efforts

    result = {"status": "READY"}
    for role, (model_id, effort) in requested.items():
        # Normalize format on both sides, preserving the full version and family.
        # Resolve collisions before checking effort so it cannot choose a model.
        candidates = [candidate for candidate in models_by_id
                      if _normalize_model(candidate) == model_id]
        if len(candidates) != 1:
            return blocked(f"{role} model is unavailable or ambiguous in the current Harness")
        actual_id = candidates[0]
        actual_efforts = [supported for supported in models_by_id[actual_id]
                          if supported.lower() == effort]
        if len(actual_efforts) != 1:
            return blocked(f"{role} effort is unsupported or ambiguous for the requested model in the current Harness")
        result[role] = {"model": actual_id, "effort": actual_efforts[0]}
    result["display"] = [
        f"{role} 模型：{result[role]['model']}｜思考强度：{result[role]['effort']}"
        for role in requested
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
