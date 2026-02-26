from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import ExifTags, Image

from extractor.comfy_parser import parse_comfyui_metadata
from extractor.models import ImageResult
from extractor.serialization import make_json_safe

EXIF_TAGS = {tag_id: tag_name for tag_id, tag_name in ExifTags.TAGS.items()}


def _extract_exif(image: Image.Image) -> dict[str, Any]:
    exif_data: dict[str, Any] = {}

    try:
        exif = image.getexif()
        if exif:
            for tag_id, value in exif.items():
                key = EXIF_TAGS.get(tag_id, str(tag_id))
                exif_data[str(key)] = make_json_safe(value)
    except Exception:
        # Fall through to piexif fallback.
        pass

    if exif_data:
        return exif_data

    try:
        import piexif  # type: ignore

        raw_exif = image.info.get("exif")
        if not raw_exif:
            return exif_data

        loaded = piexif.load(raw_exif)
        for ifd_name, ifd_data in loaded.items():
            if not isinstance(ifd_data, dict):
                continue
            for tag_id, value in ifd_data.items():
                tag_name = f"{ifd_name}.{tag_id}"
                exif_data[tag_name] = make_json_safe(value)
    except Exception:
        return exif_data

    return exif_data


def _extract_raw_metadata(image: Image.Image) -> dict[str, Any]:
    raw: dict[str, Any] = {}

    for key, value in image.info.items():
        raw[str(key)] = make_json_safe(value)

    return raw


def extract_image_metadata(file_path: Path) -> tuple[ImageResult, list[str]]:
    with Image.open(file_path) as img:
        fmt = (img.format or "UNKNOWN").upper()
        width, height = img.size
        raw_metadata = _extract_raw_metadata(img)
        exif = _extract_exif(img)
        comfyui, warnings = parse_comfyui_metadata(raw_metadata)

    result = ImageResult(
        file_path=str(file_path),
        format=fmt,
        size_bytes=file_path.stat().st_size,
        dimensions={"width": width, "height": height},
        exif=exif,
        comfyui=comfyui,
        raw_metadata=raw_metadata,
    )

    return result, warnings
