from __future__ import annotations

from pathlib import Path
from typing import Iterable

from extractor.core import extract_image_metadata
from extractor.models import RunTotals

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def discover_files(input_path: Path, recursive: bool) -> tuple[list[Path], int]:
    if input_path.is_file():
        if input_path.suffix.lower() in SUPPORTED_EXTENSIONS:
            return [input_path], 0
        return [], 1

    if not input_path.is_dir():
        raise FileNotFoundError(f"Input path does not exist: {input_path}")

    entries: Iterable[Path]
    if recursive:
        entries = input_path.rglob("*")
    else:
        entries = input_path.iterdir()

    all_files = [path for path in entries if path.is_file()]
    supported = [f for f in all_files if f.suffix.lower() in SUPPORTED_EXTENSIONS]
    skipped = len(all_files) - len(supported)
    return supported, skipped


def process_batch(input_path: Path, recursive: bool) -> tuple[list[dict], list[dict], RunTotals]:
    files, skipped = discover_files(input_path, recursive=recursive)
    totals = RunTotals(discovered=len(files), skipped_unsupported=skipped)

    results: list[dict] = []
    errors: list[dict] = []

    for file_path in files:
        try:
            result, warnings = extract_image_metadata(file_path)
            record = {
                "file_path": result.file_path,
                "format": result.format,
                "size_bytes": result.size_bytes,
                "dimensions": result.dimensions,
                "exif": result.exif,
                "comfyui": result.comfyui,
                "raw_metadata": result.raw_metadata,
            }
            if warnings:
                record["warnings"] = warnings

            results.append(record)
            totals.processed_ok += 1
        except Exception as exc:  # Keep running in batch mode.
            totals.failed += 1
            errors.append(
                {
                    "file_path": str(file_path),
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                }
            )

    return results, errors, totals
