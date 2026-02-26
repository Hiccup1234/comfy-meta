$ErrorActionPreference = "Stop"

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

python -m PyInstaller --noconfirm --clean --onedir --name comfy-meta extractor\cli.py

Write-Host "Build complete: dist\\comfy-meta\\comfy-meta.exe"
