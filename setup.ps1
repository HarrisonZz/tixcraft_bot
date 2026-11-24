$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Host "==> [1/3] Checking uv installation..." -ForegroundColor Cyan
$uvCmd = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uvCmd) {
    foreach ($candidate in @("$HOME\.local\bin", "$HOME\.cargo\bin")) {
        if (Test-Path (Join-Path $candidate "uv.exe")) {
            $env:Path = "$candidate;$env:Path"
            $uvCmd = Get-Command uv -ErrorAction SilentlyContinue
            break
        }
    }
}

if (-not $uvCmd) {
    Write-Host "uv not found. Installing uv via official Astral installer..." -ForegroundColor Yellow
    Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
    $env:Path = "$HOME\.local\bin;$HOME\.cargo\bin;$env:Path"
}

uv --version

Write-Host "==> [2/3] Syncing Python 3.12 virtual environment (.venv) from uv.lock..." -ForegroundColor Cyan
if (Test-Path (Join-Path $PSScriptRoot "uv.lock")) {
    uv sync --locked
} else {
    uv sync
}
if ($LASTEXITCODE -ne 0) {
    throw "uv sync failed (exit code $LASTEXITCODE)."
}

Write-Host "==> [3/3] Verifying runtime & dependencies..." -ForegroundColor Cyan
@'
import sys, tkinter, selenium, PIL, importlib.metadata as m
import ddddocr
print(
    "Python", sys.version.split()[0],
    "| selenium", selenium.__version__,
    "| Pillow", PIL.__version__,
    "| ddddocr", m.version("ddddocr"),
    "| tkinter OK"
)
'@ | uv run python -
if ($LASTEXITCODE -ne 0) {
    throw "Environment verification failed (exit code $LASTEXITCODE)."
}

Write-Host ""
Write-Host "Environment setup complete!" -ForegroundColor Green
Write-Host "  - Open settings GUI : uv run settings.py"
Write-Host "  - Run bot directly  : uv run chrome_tixcraft.py"
Write-Host "  - Run test suite    : uv run python -m unittest discover -s tests -v"
