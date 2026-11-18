#!/usr/bin/env bash
# Rebuilds the Neoterra pack: blueprints, sanity checks, previews and icons.
# Requires: python3, pip install nbtlib pillow
set -euo pipefail
cd "$(dirname "$0")/../../.."
PACK=stylepacks/Neoterra
PREV=docs/previews/neoterra
T=tools/blueprints
mkdir -p "$PREV"

python3 $T/neoterra/townhall.py "$PACK/fundamentals"
python3 $T/neoterra/check_townhall.py
python3 $T/neoterra/builder.py "$PACK/fundamentals"
python3 $T/neoterra/deliveryman.py "$PACK/craftsmanship/storage"
python3 $T/neoterra/warehouse.py "$PACK/craftsmanship/storage"

for l in 1 2 3 4 5; do
  python3 $T/render.py "$PACK/fundamentals/townhall$l.blueprint" "$PREV/townhall$l" >/dev/null
  python3 $T/render.py "$PACK/craftsmanship/storage/deliveryman$l.blueprint" "$PREV/deliveryman$l" >/dev/null
  python3 $T/render.py "$PACK/craftsmanship/storage/warehouse$l.blueprint" "$PREV/warehouse$l" >/dev/null
  python3 $T/render.py "$PACK/fundamentals/builder$l.blueprint" "$PREV/builder$l" >/dev/null
done
python3 $T/neoterra/make_images.py "$PACK" "$PREV"
echo "built $PACK"
