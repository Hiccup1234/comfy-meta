from __future__ import annotations

import base64
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from typing import Any


def utc_now_iso8601() -> str:
    return datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat()


def make_json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, bytes):
        encoded = base64.b64encode(value).decode("ascii")
        return {"_type": "bytes_base64", "value": encoded}
    if isinstance(value, (list, tuple, set)):
        return [make_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(k): make_json_safe(v) for k, v in value.items()}
    if is_dataclass(value):
        return make_json_safe(asdict(value))
    return {"_type": type(value).__name__, "value": str(value)}
