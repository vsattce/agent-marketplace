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
}


def _blocked(reason: str) -> dict:
    return {"status": "BLOCKED", "reasons": [reason]}


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

    coding_effort = payload.get("coding_effort", "xhigh")
    review_effort = payload.get("review_effort", "max")
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

    return {
        "status": "READY",
        "coding": {"model": selected_model_id, "effort": coding_effort},
        "review": {"model": selected_model_id, "effort": review_effort},
        "display": [
            f"编码模型：{selected_model_id}｜思考强度：{coding_effort}",
            f"验收模型：{selected_model_id}｜思考强度：{review_effort}",
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
