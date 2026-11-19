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
rm -f "$PACK/decorations/housing/playerhouse.blueprint"
python3 $T/neoterra/playerhouse.py "$PACK/decorations/housing"
python3 $T/neoterra/workhuts.py "$PACK"
python3 $T/neoterra/education.py "$PACK"
python3 $T/neoterra/military.py "$PACK" "$FURN"
python3 $T/neoterra/bunker.py "$PACK/fundamentals" "$FURN"
python3 $T/neoterra/unique.py "$PACK"
python3 $T/neoterra/update1.py "$PACK"
python3 $T/neoterra/update2.py "$PACK"
python3 $T/neoterra/update3.py "$PACK"
python3 $T/neoterra/deliveryman.py "$PACK/craftsmanship/storage"
python3 $T/neoterra/warehouse.py "$PACK/craftsmanship/storage"
# detail pass: richer materials, facades, roofs, gardens and interiors (level-scaled, walk-checked)
# massing pass: towers, wings, colonnades and plazas that make each level bigger (walk-checked)
python3 $T/neoterra/massing.py "$PACK" > /dev/null
python3 $T/neoterra/detail.py "$PACK" "$FURN" > /dev/null

for l in 1 2 3 4 5; do
  for f in fundamentals/townhall fundamentals/builder fundamentals/cottage fundamentals/house \
           fundamentals/apartment fundamentals/quadplex fundamentals/cook fundamentals/lumberjack \
           craftsmanship/storage/deliveryman craftsmanship/storage/warehouse \
           craftsmanship/carpentry/sawmill craftsmanship/masonry/stonemason craftsmanship/metallurgy/mechanic \
           education/school education/library education/university \
           military/guardtower military/archery military/combatacademy military/stable \
           decorations/housing/playerhouse fundamentals/miner fundamentals/hospital \
           agriculture/horticulture/farmer agriculture/husbandry/fisherman \
           craftsmanship/metallurgy/smeltery craftsmanship/metallurgy/blacksmith craftsmanship/luxury/baker \
           craftsmanship/carpentry/fletcher craftsmanship/luxury/cookery craftsmanship/luxury/alchemist \
           craftsmanship/luxury/dyer craftsmanship/luxury/glassblower craftsmanship/luxury/concretemixer \
           craftsmanship/masonry/crusher craftsmanship/masonry/sifter craftsmanship/masonry/stonesmeltery \
           agriculture/horticulture/florist agriculture/horticulture/plantation agriculture/horticulture/composter \
           agriculture/husbandry/beekeeper agriculture/husbandry/chickenherder agriculture/husbandry/cowboy \
           agriculture/husbandry/shepherd agriculture/husbandry/swineherder agriculture/husbandry/rabbithutch \
           mystic/enchanter mystic/graveyard mystic/mysticalsite mystic/netherworker \
           military/wallguardtower education/communitycollege; do
    python3 $T/render.py "$PACK/$f$l.blueprint" "$PREV/$(basename $f)$l" >/dev/null
  done
  python3 $T/render.py "$FURN/skytower${l}_furnished.blueprint" "$PREV/skytower$l" >/dev/null
  python3 $T/render.py "$FURN/barracks${l}_furnished.blueprint" "$PREV/barracks$l" >/dev/null
  python3 $T/render.py "$FURN/bunker${l}_cutaway.preview" "$PREV/bunker$l" >/dev/null
done
for l in 1 2 3; do
  python3 $T/render.py "$PACK/fundamentals/tavern$l.blueprint" "$PREV/tavern$l" >/dev/null
  python3 $T/render.py "$PACK/military/gatehouse$l.blueprint" "$PREV/gatehouse$l" >/dev/null
  python3 $T/render.py "$PACK/walls/watchtower$l.blueprint" "$PREV/watchtower$l" >/dev/null
done
for f in $(find "$PACK/walls" "$PACK/decorations/parks" "$PACK/infrastructure" -name "*.blueprint" \
           | grep -vE "/mineshafts/(miner|.*shaft)|watchtower[0-9]"); do
  python3 $T/render.py "$f" "$PREV/$(basename "$f" .blueprint)" >/dev/null
done
for f in decorations/supplies/supplycamp decorations/supplies/supplyship decorations/fields/neofield \
         agriculture/fields/neobamboo agriculture/fields/neocactus agriculture/fields/neosugar agriculture/fields/neokelp; do
  python3 $T/render.py "$PACK/$f.blueprint" "$PREV/$(basename $f)" >/dev/null
done
python3 $T/neoterra/make_images.py "$PACK" "$PREV"
# buildings with child huts (Skytower, barracks, bunker) are checked as assembled copies
python3 $T/walkcheck.py $(find "$PACK" -name "*.blueprint" | grep -vE "/(skytower|barracks|bunker)[a-z]*[0-9]|/mineshafts/miner|shaft1\.blueprint|ship\.blueprint") \
  "$FURN"/*_furnished.blueprint >/dev/null \
  && echo "walkcheck: everything reachable"
echo "built $PACK"
