#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

for candidate in "$HOME/.local/bin" "$HOME/.cargo/bin"; do
  if [ -x "$candidate/uv" ]; then
    export PATH="$candidate:$PATH"
  fi
done

echo "==> [1/3] Syncing environment (including PyInstaller dev group)..."
uv sync --group dev

echo "==> [2/3] Building standalone --onedir application into dist/tixcraft_bot..."
uv run pyinstaller --noconfirm --clean tixcraft_bot.spec

echo "==> [3/3] Cleaning intermediate build/ & generating default settings.json..."
rm -rf build
uv run python - <<'PY'
import json, os, settings
dist_dir = os.path.join("dist", "tixcraft_bot")
os.makedirs(os.path.join(dist_dir, "webdriver"), exist_ok=True)
cfg_path = os.path.join(dist_dir, "settings.json")
with open(cfg_path, "w", encoding="utf-8") as f:
    json.dump(settings.get_default_config(), f, indent=2, ensure_ascii=False)
print("Wrote default config:", cfg_path)
PY

echo ""
echo "Build complete! Standalone app folder: dist/tixcraft_bot/"
echo "  - Launch GUI : ./dist/tixcraft_bot/settings"
echo "  - Launch Bot : ./dist/tixcraft_bot/chrome_tixcraft"
