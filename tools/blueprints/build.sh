#!/usr/bin/env bash
# Regenerates every blueprint in the Modern Rail pack plus preview images.
# Requires: python3, pip install nbtlib pillow
set -euo pipefail
cd "$(dirname "$0")/../.."
python3 tools/blueprints/train_station.py stylepacks/ModernRail/transport/modern_train_station.blueprint
python3 tools/blueprints/render.py stylepacks/ModernRail/transport/modern_train_station.blueprint docs/previews/modern_train_station
python3 - <<'PY'
from PIL import Image
im = Image.open("docs/previews/modern_train_station_front.png").convert("RGBA")
side = max(im.size)
bg = Image.new("RGBA", (side, side), (236, 240, 244, 255))
bg.paste(im, ((side - im.width) // 2, (side - im.height) // 2), im)
bg.resize((128, 128), Image.LANCZOS).save("stylepacks/ModernRail/icon.png")
PY
echo "done"
