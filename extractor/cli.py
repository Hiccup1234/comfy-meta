from __future__ import annotations

import argparse
import json
import sys
import tempfile
import webbrowser
from datetime import datetime
from pathlib import Path

from extractor import __version__
from extractor.batch import process_batch
from extractor.report_html import write_report_html
from extractor.serialization import utc_now_iso8601

SUPPORTED_FORMATS = ["png", "jpg", "jpeg", "webp"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="comfy-meta",
        description="Extract EXIF and ComfyUI metadata from images.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"comfy-meta {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    extract_cmd = subparsers.add_parser("extract", help="Extract metadata from file/folder")
    extract_cmd.add_argument("--input", required=True, help="Input file or directory")
    extract_cmd.add_argument("--output", required=True, help="Output JSON path")
    extract_cmd.add_argument(
        "--recursive",
        action="store_true",
        help="Recursively process files when input is a directory",
    )
    extract_cmd.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output",
    )
    extract_cmd.add_argument(
        "--relative-paths",
        action="store_true",
        help="Write file paths as relative to the input path when possible",
    )

    return parser


def _build_payload(
    input_info: dict,
    results: list[dict],
    errors: list[dict],
    discovered: int,
    processed_ok: int,
    failed: int,
    skipped_unsupported: int,
) -> dict:
    return {
        "tool_version": __version__,
        "run_at": utc_now_iso8601(),
        "input": input_info,
        "totals": {
            "discovered": discovered,
            "processed_ok": processed_ok,
            "failed": failed,
            "skipped_unsupported": skipped_unsupported,
        },
        "results": results,
        "errors": errors,
    }


def _print_summary(discovered: int, processed_ok: int, failed: int, skipped_unsupported: int) -> None:
    print(
        "Summary: discovered={discovered} processed_ok={ok} failed={failed} skipped_unsupported={skipped}".format(
            discovered=discovered,
            ok=processed_ok,
            failed=failed,
            skipped=skipped_unsupported,
        )
    )


def _maybe_relativize_paths(payload: dict, input_path: Path) -> None:
    if input_path.is_file():
        return

    base = input_path.resolve()

    for item in payload.get("results", []):
        path = Path(item["file_path"])  # absolute from extraction step
        try:
            item["file_path"] = str(path.resolve().relative_to(base))
        except Exception:
            continue

    for item in payload.get("errors", []):
        path = Path(item["file_path"])
        try:
            item["file_path"] = str(path.resolve().relative_to(base))
        except Exception:
            continue


def run_extract(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    output_path = Path(args.output)

    try:
        results, errors, totals = process_batch(input_path=input_path, recursive=args.recursive)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Unexpected runtime error: {exc}", file=sys.stderr)
        return 1

    payload = _build_payload(
        input_info={
            "path": str(input_path),
            "recursive": bool(args.recursive),
            "formats": SUPPORTED_FORMATS,
        },
        results=results,
        errors=errors,
        discovered=totals.discovered,
        processed_ok=totals.processed_ok,
        failed=totals.failed,
        skipped_unsupported=totals.skipped_unsupported,
    )

    if args.relative_paths:
        _maybe_relativize_paths(payload, input_path=input_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2 if args.pretty else None, ensure_ascii=False)

    print("Extraction complete")
    print(f"Output: {output_path}")
    _print_summary(
        discovered=totals.discovered,
        processed_ok=totals.processed_ok,
        failed=totals.failed,
        skipped_unsupported=totals.skipped_unsupported,
    )

    if totals.processed_ok == 0:
        return 2
    return 0


def _run_dragdrop_mode(paths: list[str]) -> int:
    merged_results: list[dict] = []
    merged_errors: list[dict] = []
    discovered = 0
    processed_ok = 0
    failed = 0
    skipped_unsupported = 0

    for raw_path in paths:
        input_path = Path(raw_path)
        try:
            results, errors, totals = process_batch(input_path=input_path, recursive=False)
            merged_results.extend(results)
            merged_errors.extend(errors)
            discovered += totals.discovered
            processed_ok += totals.processed_ok
            failed += totals.failed
            skipped_unsupported += totals.skipped_unsupported
        except Exception as exc:
            failed += 1
            merged_errors.append(
                {
                    "file_path": str(input_path),
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                }
            )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_base = f"comfy_meta_dragdrop_{timestamp}"
    output_name = f"{output_base}.json"
    output_dir_candidates: list[Path] = []

    first_input = Path(paths[0]).expanduser()
    if first_input.exists():
        if first_input.is_file():
            output_dir_candidates.append(first_input.parent)
        else:
            output_dir_candidates.append(first_input)
    output_dir_candidates.append(Path.cwd())
    output_dir_candidates.append(Path(tempfile.gettempdir()))

    output_path: Path | None = None
    for candidate in output_dir_candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".comfy_meta_write_test"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            output_path = candidate / output_name
            break
        except Exception:
            continue

    if output_path is None:
        print("Error: no writable output directory found for drag-and-drop mode.", file=sys.stderr)
        return 1
    payload = _build_payload(
        input_info={
            "paths": paths,
            "recursive": False,
            "formats": SUPPORTED_FORMATS,
        },
        results=merged_results,
        errors=merged_errors,
        discovered=discovered,
        processed_ok=processed_ok,
        failed=failed,
        skipped_unsupported=skipped_unsupported,
    )

    try:
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
    except Exception as exc:
        print(f"Error: failed to write output JSON: {exc}", file=sys.stderr)
        return 1

    html_path = output_path.with_suffix(".html")
    try:
        write_report_html(payload, html_path)
    except Exception as exc:
        print(f"Warning: failed to write HTML report: {exc}", file=sys.stderr)
        html_path = None

    print("Drag-and-drop extraction complete")
    print(f"JSON Output: {output_path}")
    if html_path is not None:
        print(f"HTML Output: {html_path}")
    _print_summary(
        discovered=discovered,
        processed_ok=processed_ok,
        failed=failed,
        skipped_unsupported=skipped_unsupported,
    )
    if html_path is not None:
        try:
            webbrowser.open(html_path.resolve().as_uri())
        except Exception:
            pass

    if processed_ok == 0:
        return 2
    return 0


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    # Windows drag-and-drop onto the .exe passes paths as positional args.
    if argv and argv[0] not in {"extract", "-h", "--help"} and not argv[0].startswith("-"):
        return _run_dragdrop_mode(argv)

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "extract":
        return run_extract(args)

    print("Unknown command", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
