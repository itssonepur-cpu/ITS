# Build a single-file EXE using PyInstaller
$ErrorActionPreference = 'Stop'

if (!(Test-Path -Path 'venv')) {
  python -m venv venv
}

./venv/Scripts/pip install --upgrade pip
./venv/Scripts/pip install -r requirements.txt

./venv/Scripts/pyinstaller --noconfirm --onefile --name WhatsAppPack `
  --add-data "config.example.json;." `
  --add-data "data;data" `
  --add-data "src;src" `
  main.py

Write-Host "Build complete. See dist/WhatsAppPack.exe"
