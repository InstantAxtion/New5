#!/usr/bin/env bash
# Rebuilds the Neoterra pack: blueprints, sanity checks, previews and icons.
# Requires: python3, pip install nbtlib pillow
set -euo pipefail
cd "$(dirname "$0")/../../.."
PACK=stylepacks/Neoterra
PREV=docs/previews/neoterra
mkdir -p "$PACK/fundamentals" "$PREV"

python3 tools/blueprints/neoterra/townhall.py "$PACK/fundamentals"
python3 tools/blueprints/neoterra/check_townhall.py

for l in 1 2 3 4 5; do
  python3 tools/blueprints/render.py "$PACK/fundamentals/townhall$l.blueprint" "$PREV/townhall$l" >/dev/null
done
python3 tools/blueprints/neoterra/make_images.py "$PACK" "$PREV"
echo "built $PACK"
