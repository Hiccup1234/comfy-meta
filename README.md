# comfy-meta

Extract EXIF and ComfyUI metadata from generated images.

## Features

- Supports single file and folder batch extraction
- Supports PNG, JPG/JPEG, and WebP
- Extracts EXIF + format metadata + ComfyUI keys (`prompt`, `workflow`, `parameters`)
- Keeps unknown metadata keys under `comfyui.extra_keys`
- Continues processing on errors and writes per-file error records
- Outputs JSON + console summary

## Install (dev)

```powershell
python -m pip install -r requirements.txt
```

## Run

```powershell
python -m extractor.cli extract --input "C:\\path\\to\\image_or_folder" --output ".\\result.json" --pretty
```

Optional flags:

- `--recursive`: recurse when input is a directory
- `--relative-paths`: convert result file paths to be relative to input folder

## Build Windows executable

```powershell
.\build_exe.ps1
```

Executable output:

- `dist\\comfy-meta\\comfy-meta.exe`

## Example

```powershell
.\dist\comfy-meta\comfy-meta.exe extract --input "C:\\ComfyUI\\output" --output ".\\metadata.json" --recursive --pretty
```

## Drag and Drop (Windows)

- You can drag one or more files/folders directly onto `comfy-meta.exe`.
- The app auto-runs extraction (non-recursive for dropped folders).
- It writes both:
  - `comfy_meta_dragdrop_YYYYMMDD_HHMMSS.json`
  - `comfy_meta_dragdrop_YYYYMMDD_HHMMSS.html`
- The HTML report includes per-image download buttons for:
  - `Workflow JSON`
  - `Prompt JSON`
- The HTML report is opened automatically in your default browser.
- Reports are written to a writable location (dropped file folder first, then fallback locations).
