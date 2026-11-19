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
python3 $T/neoterra/residences.py "$PACK/fundamentals"
FURN=$(mktemp -d)
python3 $T/neoterra/skytower.py "$PACK/fundamentals" "$FURN"
python3 $T/neoterra/playerhouse.py "$PACK/decorations/housing/playerhouse.blueprint"
python3 $T/neoterra/deliveryman.py "$PACK/craftsmanship/storage"
python3 $T/neoterra/warehouse.py "$PACK/craftsmanship/storage"

for l in 1 2 3 4 5; do
  python3 $T/render.py "$PACK/fundamentals/townhall$l.blueprint" "$PREV/townhall$l" >/dev/null
  python3 $T/render.py "$PACK/craftsmanship/storage/deliveryman$l.blueprint" "$PREV/deliveryman$l" >/dev/null
  python3 $T/render.py "$PACK/craftsmanship/storage/warehouse$l.blueprint" "$PREV/warehouse$l" >/dev/null
  python3 $T/render.py "$PACK/fundamentals/builder$l.blueprint" "$PREV/builder$l" >/dev/null
  python3 $T/render.py "$FURN/skytower${l}_furnished.blueprint" "$PREV/skytower$l" >/dev/null
  for r in cottage house apartment quadplex; do
    python3 $T/render.py "$PACK/fundamentals/$r$l.blueprint" "$PREV/$r$l" >/dev/null
  done
done
python3 $T/render.py "$PACK/decorations/housing/playerhouse.blueprint" "$PREV/playerhouse" >/dev/null
python3 $T/neoterra/make_images.py "$PACK" "$PREV"
# the Skytower's apartments are separate child huts, so check the furnished copies instead
python3 $T/walkcheck.py $(ls "$PACK"/fundamentals/*.blueprint | grep -v "/skytower") \
  "$FURN"/*.blueprint "$PACK"/decorations/housing/*.blueprint "$PACK"/craftsmanship/storage/*.blueprint >/dev/null \
  && echo "walkcheck: everything reachable"
echo "built $PACK"
