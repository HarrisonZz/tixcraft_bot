#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "==> [1/3] Checking uv installation..."
if ! command -v uv >/dev/null 2>&1; then
  for candidate in "$HOME/.local/bin" "$HOME/.cargo/bin"; do
    if [ -x "$candidate/uv" ]; then
      export PATH="$candidate:$PATH"
      break
    fi
  done
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found. Installing uv via official Astral installer..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi

uv --version

echo "==> [2/3] Syncing Python 3.12 virtual environment (.venv) from uv.lock..."
if [ -f "$SCRIPT_DIR/uv.lock" ]; then
  uv sync --locked
else
  uv sync
fi

echo "==> [3/3] Verifying runtime & dependencies..."
uv run python - <<'PY'
import sys, tkinter, selenium, PIL, importlib.metadata as m
import ddddocr
print(
    "Python", sys.version.split()[0],
    "| selenium", selenium.__version__,
    "| Pillow", PIL.__version__,
    "| ddddocr", m.version("ddddocr"),
    "| tkinter OK"
)
PY

echo ""
echo "Environment setup complete!"
echo "  - Open settings GUI : uv run settings.py"
echo "  - Run bot directly  : uv run chrome_tixcraft.py"
echo "  - Run test suite    : uv run python -m unittest discover -s tests -v"
