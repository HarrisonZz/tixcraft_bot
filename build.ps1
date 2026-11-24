$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

foreach ($candidate in @("$HOME\.local\bin", "$HOME\.cargo\bin")) {
    if ((Test-Path (Join-Path $candidate "uv.exe")) -and ($env:Path -notlike "*$candidate*")) {
        $env:Path = "$candidate;$env:Path"
    }
}

Write-Host "==> [1/3] Syncing environment (including PyInstaller dev group)..." -ForegroundColor Cyan
uv sync --group dev
if ($LASTEXITCODE -ne 0) {
    throw "uv sync --group dev failed (exit code $LASTEXITCODE)."
}

Write-Host "==> [2/3] Building standalone --onedir application into dist\tixcraft_bot..." -ForegroundColor Cyan
uv run pyinstaller --noconfirm --clean tixcraft_bot.spec
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed (exit code $LASTEXITCODE)."
}

Write-Host "==> [3/3] Cleaning intermediate build\ & generating default settings.json..." -ForegroundColor Cyan
if (Test-Path (Join-Path $PSScriptRoot "build")) {
    Remove-Item -Recurse -Force (Join-Path $PSScriptRoot "build")
}
@'
import json, os, settings
dist_dir = os.path.join("dist", "tixcraft_bot")
os.makedirs(os.path.join(dist_dir, "webdriver"), exist_ok=True)
cfg_path = os.path.join(dist_dir, "settings.json")
with open(cfg_path, "w", encoding="utf-8") as f:
    json.dump(settings.get_default_config(), f, indent=2, ensure_ascii=False)
print("Wrote default config:", cfg_path)
'@ | uv run python -
if ($LASTEXITCODE -ne 0) {
    throw "Post-build asset setup failed (exit code $LASTEXITCODE)."
}

Write-Host ""
Write-Host "Build complete! Standalone app folder: dist\tixcraft_bot\" -ForegroundColor Green
Write-Host "  - Launch GUI : .\dist\tixcraft_bot\settings.exe"
Write-Host "  - Launch Bot : .\dist\tixcraft_bot\chrome_tixcraft.exe"
