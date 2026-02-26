from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ImageResult:
    file_path: str
    format: str
    size_bytes: int
    dimensions: dict[str, int]
    exif: dict[str, Any] = field(default_factory=dict)
    comfyui: dict[str, Any] = field(default_factory=dict)
    raw_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorItem:
    file_path: str
    error_type: str
    message: str


@dataclass
class RunTotals:
    discovered: int = 0
    processed_ok: int = 0
    failed: int = 0
    skipped_unsupported: int = 0
