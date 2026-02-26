from __future__ import annotations

import json
from typing import Any

KNOWN_COMFY_KEYS = {"prompt", "workflow", "parameters"}


def _attempt_json_parse(value: Any) -> tuple[Any, bool]:
    if not isinstance(value, str):
        return value, False
    text = value.strip()
    if not text:
        return value, False
    if text[0] not in "[{\"":
        return value, False

    try:
        return json.loads(text), True
    except json.JSONDecodeError:
        return value, False


def parse_comfyui_metadata(raw_metadata: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    comfyui: dict[str, Any] = {}
    extra_keys: dict[str, Any] = {}
    warnings: list[str] = []

    for key, value in raw_metadata.items():
        lower_key = key.lower()
        parsed_value, was_parsed = _attempt_json_parse(value)

        if lower_key in KNOWN_COMFY_KEYS:
            comfyui[lower_key] = parsed_value
            if not was_parsed and isinstance(value, str) and value.strip().startswith(("{", "[")):
                warnings.append(f"Failed to parse JSON for key '{key}'")
        else:
            extra_keys[key] = parsed_value

    if extra_keys:
        comfyui["extra_keys"] = extra_keys

    return comfyui, warnings
