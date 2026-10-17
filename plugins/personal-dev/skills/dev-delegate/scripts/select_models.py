"""Choose an available coding model from a caller-supplied spawn-tool inventory."""

from __future__ import annotations

import json
import re
import sys


_PRIMARY_MODEL_RE = re.compile(r"gpt-(\d+(?:\.\d+)*)-(?:sol|astra|terra|luna)")
_LUNA_MODEL_RE = re.compile(r"gpt-(\d+(?:\.\d+)*)-luna")
_INPUT_FIELDS = {
    "primary_model",
    "primary_model_source",
    "inventory_source",
    "models",
    "model_override",
    "override_confirmed",
    "coding_effort",
    "review_effort",
    "final_review_required",
    "primary_effort",
    "primary_effort_source",
    "final_review_escalated",
    "final_review_model",
    "final_review_effort",
}
_EFFORT_LEVELS = ("none", "minimal", "low", "medium", "high", "xhigh", "max", "ultra")


def _blocked(reason: str) -> dict:
    return {"status": "BLOCKED", "reasons": [reason]}


def _with_final_review(result: dict, model_id: str, effort: str, note: str) -> dict:
    result["final_review"] = {"model": model_id, "effort": effort}
    result["display"].append(f"终审模型：{model_id}｜思考强度：{effort}｜{note}")
    return result


def _version_key(version: str) -> tuple[str, ...]:
    parts = [part.lstrip("0") or "0" for part in version.split(".")]
    while len(parts) > 1 and parts[-1] == "0":
        parts.pop()
    return tuple(parts)


def _version_order(version: tuple[str, ...]) -> tuple[tuple[int, str], ...]:
    return tuple((len(part), part) for part in version)


def select_models(payload: dict) -> dict:
    """Resolve coding and review models using only the supplied tool inventory."""
    if not isinstance(payload, dict):
        return _blocked("input must be a JSON object")

    unknown_fields = set(payload) - _INPUT_FIELDS
    if unknown_fields:
        return _blocked("input contains unsupported fields")

    required_fields = {"primary_model", "primary_model_source", "inventory_source", "models"}
    if required_fields - set(payload):
        return _blocked("required input fields are missing")

    final_required = payload.get("final_review_required", False)
    if not isinstance(final_required, bool):
        return _blocked("final_review_required must be a boolean")
    final_fields = {"primary_effort", "primary_effort_source", "final_review_escalated",
                    "final_review_model", "final_review_effort"}
    if not final_required and final_fields.intersection(payload):
        return _blocked("final review fields require final_review_required")

    primary_model = payload["primary_model"]
    if not isinstance(primary_model, str) or not primary_model.strip():
        return _blocked("primary_model must be a non-empty string")
    primary_model_source = payload["primary_model_source"]
    if not isinstance(primary_model_source, str) or primary_model_source not in {"current-turn", "user"}:
        return _blocked("primary_model_source must be current-turn or user")
    if payload["inventory_source"] != "current-spawn-tool":
        return _blocked("inventory_source must be current-spawn-tool")

    raw_models = payload["models"]
    if not isinstance(raw_models, list) or not raw_models:
        return _blocked("models must be a non-empty list")

    models_by_id: dict[str, dict] = {}
    for item in raw_models:
        if not isinstance(item, dict) or set(item) != {"id", "efforts"}:
            return _blocked("each model must contain only id and efforts fields")
        model_id = item["id"]
        efforts = item["efforts"]
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
        models_by_id[model_id] = item

    coding_effort = payload.get("coding_effort", "high")
    review_effort = payload.get("review_effort", "xhigh")
    for field, effort in (("coding_effort", coding_effort), ("review_effort", review_effort)):
        if not isinstance(effort, str) or not effort.strip():
            return _blocked(f"{field} must be a non-empty string")

    has_override = "model_override" in payload
    override_confirmed = payload.get("override_confirmed", False)
    if not isinstance(override_confirmed, bool):
        return _blocked("override_confirmed must be a boolean")
    if has_override and (not isinstance(payload["model_override"], str) or not payload["model_override"].strip()):
        return _blocked("model_override must be a non-empty model id")
    if has_override and not override_confirmed:
        return _blocked("model_override requires explicit confirmation")
    if override_confirmed and not has_override:
        return _blocked("override_confirmed requires model_override")

    selected_model_id: str
    if has_override:
        selected_model_id = payload["model_override"]
        if selected_model_id not in models_by_id:
            return _blocked("confirmed model_override is not present in the tool inventory")
    else:
        primary_match = _PRIMARY_MODEL_RE.fullmatch(primary_model)
        if primary_match is None:
            return _blocked("primary_model identity is not a recognized complete model id")
        primary_major = _version_key(primary_match.group(1))[0]

        candidates: dict[tuple[str, ...], list[str]] = {}
        for model_id in models_by_id:
            match = _LUNA_MODEL_RE.fullmatch(model_id)
            if match is None:
                continue
            version = _version_key(match.group(1))
            if version[0] == primary_major:
                candidates.setdefault(version, []).append(model_id)

        if not candidates:
            return _blocked("no approved Luna model matches the primary model major version")
        if any(len(ids) > 1 for ids in candidates.values()):
            return _blocked("different model ids have the same numeric version")

        highest_version = max(candidates, key=_version_order)
        selected_model_id = candidates[highest_version][0]

    selected_efforts = set(models_by_id[selected_model_id]["efforts"])
    if coding_effort not in selected_efforts:
        return _blocked(f"selected model does not support coding effort {coding_effort}")
    if review_effort not in selected_efforts:
        return _blocked(f"selected model does not support review effort {review_effort}")

    result = {
        "status": "READY",
        "coding": {"model": selected_model_id, "effort": coding_effort},
        "review": {"model": selected_model_id, "effort": review_effort},
        "display": [
            f"编码模型：{selected_model_id}｜思考强度：{coding_effort}",
            f"验收模型：{selected_model_id}｜思考强度：{review_effort}",
        ],
    }
    if not final_required:
        return result

    escalated = payload.get("final_review_escalated", False)
    if not isinstance(escalated, bool):
        return _blocked("final_review_escalated must be a boolean")

    primary_effort = payload.get("primary_effort")
    has_session_effort = bool({"primary_effort", "primary_effort_source"}.intersection(payload))
    if has_session_effort:
        if not isinstance(primary_effort, str) or primary_effort not in _EFFORT_LEVELS:
            return _blocked("primary_effort must be a recognized current session effort")
        effort_source = payload.get("primary_effort_source")
        if not isinstance(effort_source, str) or effort_source not in {"current-turn", "user"}:
            return _blocked("primary_effort_source must be current-turn or user")

    # These role-specific values come from an explicit user request, not a new confirmation.
    if {"final_review_model", "final_review_effort"}.intersection(payload):
        final_model = payload.get("final_review_model", primary_model if primary_model in models_by_id else selected_model_id)
        if not isinstance(final_model, str) or final_model not in models_by_id:
            return _blocked("requested final review model is unavailable")
        supported = set(models_by_id[final_model]["efforts"])
        final_effort = payload.get("final_review_effort")
        if "final_review_effort" not in payload:
            if final_model == primary_model and has_session_effort:
                ceiling = _EFFORT_LEVELS.index(primary_effort)
                candidates = [effort for effort in _EFFORT_LEVELS[:max(ceiling, 1)] if effort in supported]
                final_effort = candidates[-1] if candidates else None
            elif review_effort in supported:
                final_effort = review_effort
            else:
                limit = _EFFORT_LEVELS.index(review_effort) if review_effort in _EFFORT_LEVELS else 0
                candidates = [effort for effort in _EFFORT_LEVELS[:limit + 1] if effort in supported]
                final_effort = candidates[-1] if candidates else None
        if not isinstance(final_effort, str) or final_effort not in supported:
            return _blocked("requested final review effort is unavailable")
        return _with_final_review(result, final_model, final_effort, "用户指定优先")

    # A hidden session effort or non-spawnable primary must not cause a configuration Q&A.
    if not has_session_effort or primary_model not in models_by_id:
        if escalated:
            return _blocked("final review escalation requires a verified available session limit")
        return _with_final_review(result, selected_model_id, review_effort, "沿用任务验收配置")

    supported = set(models_by_id[primary_model]["efforts"])
    ceiling = _EFFORT_LEVELS.index(primary_effort)
    if escalated:
        if ceiling == 0:
            return _blocked("final review has no higher effort within the session limit")
        if primary_effort not in supported:
            return _blocked("current session effort is unavailable for final review escalation")
        final_effort = primary_effort
    else:
        # Take one level down; missing levels can only lower the selection further.
        candidates = [
            effort for effort in _EFFORT_LEVELS[: max(ceiling, 1)] if effort in supported
        ]
        if not candidates:
            return _with_final_review(result, selected_model_id, review_effort, "沿用任务验收配置")
        final_effort = candidates[-1]

    return _with_final_review(result, primary_model, final_effort, f"会话上限：{primary_effort}")


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
