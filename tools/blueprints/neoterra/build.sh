#!/usr/bin/env bash
# Rebuilds the Neoterra pack: blueprints, sanity checks, previews and icons.
# Requires: python3, pip install nbtlib pillow
set -euo pipefail
cd "$(dirname "$0")/../../.."
PACK=stylepacks/Neoterra
PREV=docs/previews/neoterra
T=tools/blueprints
mkdir -p "$PREV"
# files that later steps regenerate from scratch must not run through the early passes
rm -f "$PACK"/fundamentals/twinbuilder*.blueprint
find "$PACK" -path "*/wonders/*.blueprint" -delete 2>/dev/null || true

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
# raw generator output: the other packs run their own shape passes from here
RAW=$(mktemp -d)
cp -r "$PACK/." "$RAW/"
# detail pass: richer materials, facades, roofs, gardens and interiors (level-scaled, walk-checked)
# reshape pass: each level re-forms the main building (roofs, storeys, crowns; walk-checked)
python3 $T/neoterra/reshape.py "$PACK" > /dev/null
# massing pass: towers, wings, colonnades and plazas that make each level bigger (walk-checked)
python3 $T/neoterra/massing.py "$PACK" > /dev/null
python3 $T/neoterra/detail.py "$PACK" "$FURN" > /dev/null
# plot pass: no landscaping outside, crop to the building + 1-block paved apron (walk-checked)
python3 $T/neoterra/plot.py "$PACK" > /dev/null
# support pass: nothing floats (posts down to the ground, or stray bits removed; walk-checked)
python3 $T/neoterra/support.py "$PACK" Neoterra > /dev/null
# barracks fort, gatehouse, wall guard tower and sky tower facade in real-world forms
python3 $T/neoterra/military_styles.py "$PACK" Neoterra
python3 $T/neoterra/skyskin.py "$PACK" Neoterra > /dev/null
# every regular hut as its real-world building type (typology.py), in Neoterra's modern style
python3 $T/neoterra/archgen.py "$RAW" "$PACK" Neoterra > /dev/null
python3 $T/neoterra/support.py "$PACK" Neoterra > /dev/null
# Twin Builders' Yard: one building, two builder huts (parent + child annex)
python3 $T/neoterra/twinbuilder.py "$PACK" Neoterra
# Grand Projects (wonders) with wing child huts
python3 $T/neoterra/wonders.py "$PACK" Neoterra
# Domum Ornamentum: Neoterra's own set (framed lights, quartz pillars), more at higher levels
# hand-made huts (designs/*.py) replace the generated ones; vanilla blocks only
python3 $T/neoterra/handmade/handmade.py "$PACK" Neoterra
python3 $T/neoterra/vanillaize.py "$PACK"
# level 1 already reserves the plot of level 5
python3 $T/neoterra/plotmax.py "$PACK"

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
python3 $T/walkcheck.py $(find "$PACK" -name "*.blueprint" | grep -vE "/(skytower|barracks|bunker)[a-z]*[0-9]|twinbuilder[a-z]*[0-9]|/mineshafts/miner|shaft1\.blueprint|ship\.blueprint|/wonders/") \
  "$FURN"/*_furnished.blueprint >/dev/null \
  && echo "walkcheck: everything reachable"
# Hearthwood (cozy modern) and Cascadia (Oregon / Pacific Northwest): their own shape passes (roof forms,
# crowns, landmark modules) from the raw buildings, then their own materials
for STY in Hearthwood Cascadia; do
  OUT=stylepacks/$STY
  SP=docs/previews/$(echo $STY | tr 'A-Z' 'a-z')
  rm -rf "$OUT"
  cp -r "$RAW" "$OUT"
  rm -f "$OUT/pack.json" "$OUT/neoterra.png"
  NEOTERRA_STYLE=$STY python3 $T/neoterra/reshape.py "$OUT" > /dev/null
  NEOTERRA_STYLE=$STY python3 $T/neoterra/massing.py "$OUT" > /dev/null
  NEOTERRA_STYLE=$STY python3 $T/neoterra/detail.py "$OUT" > /dev/null
  NEOTERRA_STYLE=$STY python3 $T/neoterra/plot.py "$OUT" > /dev/null
  NEOTERRA_STYLE=$STY python3 $T/neoterra/support.py "$OUT" $STY > /dev/null
  python3 $T/neoterra/restyle.py "$OUT" "$OUT" $STY
  # every regular hut: its real-world building type (typology.py) in the pack's own architecture
  python3 $T/neoterra/archgen.py "$RAW" "$OUT" $STY > /dev/null
  # Cascadia university: hand-designed campus hall (clock tower, portico, wings, library)
  if [ "$STY" = Cascadia ]; then python3 $T/neoterra/university_cascadia.py "$OUT"; fi
  python3 $T/neoterra/support.py "$OUT" $STY > /dev/null
  python3 $T/neoterra/military_styles.py "$OUT" $STY
  # own sky tower (with flats) and own bunker (with rooms) per pack
  python3 $T/neoterra/skytower_styles.py "$OUT" $STY
  python3 $T/neoterra/bunker_styles.py "$OUT" $STY
  # walls, roads, rails, canals, bridges, subway, boardwalk, cliff climb and parks in the pack's own design
  python3 $T/neoterra/styleinfra.py "$OUT" $STY
  python3 $T/neoterra/twinbuilder.py "$OUT" $STY
  python3 $T/neoterra/wonders.py "$OUT" $STY
  # Domum Ornamentum: the pack's own set (shutters / timber frames / shingles / pillars), more at higher levels
  # furniture in the pack's own style, then its Domum set
  python3 $T/neoterra/handmade/handmade.py "$OUT" $STY
  python3 $T/neoterra/vanillaize.py "$OUT"
  python3 $T/neoterra/fields_styles.py "$OUT" $STY
  python3 $T/neoterra/plotmax.py "$OUT"
  mkdir -p "$SP"
  for f in fundamentals/townhall5 craftsmanship/storage/deliveryman5 decorations/housing/playerhouse5 \
           education/university5 military/barracks5 agriculture/horticulture/farmer5 fundamentals/miner5 \
           mystic/enchanter5 walls/watchtower3 fundamentals/apartment5 craftsmanship/metallurgy/smeltery3 \
           education/library5 craftsmanship/luxury/baker5 agriculture/horticulture/florist5; do
    python3 $T/render.py "$OUT/$f.blueprint" "$SP/$(basename $f)" >/dev/null
  done
  for b in fundamentals/house fundamentals/cottage craftsmanship/luxury/cookery; do
    for l in 1 2 3 4 5; do python3 $T/render.py "$OUT/$b$l.blueprint" "$SP/$(basename $b)$l" >/dev/null; done
  done
  python3 $T/neoterra/make_images.py "$OUT" "$SP" "$(echo $STY | tr 'A-Z' 'a-z').png"
  python3 $T/walkcheck.py $(find "$OUT" -name "*.blueprint" | grep -vE "/(skytower|barracks|bunker)[a-z]*[0-9]|twinbuilder[a-z]*[0-9]|/mineshafts/miner|shaft1\.blueprint|ship\.blueprint|/wonders/") >/dev/null \
    && echo "$STY walkcheck: everything reachable"
done
# Farmworks: automatic mob and food farms + Trade Post / Supply Depot huts
FW=stylepacks/Farmworks
FP=docs/previews/farmworks
rm -rf "$FW"
python3 $T/neoterra/farms.py "$FW"
python3 $T/neoterra/tradepost.py "$FW"
python3 $T/neoterra/plotmax.py "$FW"
mkdir -p "$FP"
for f in $(find "$FW" -name "*.blueprint"); do
  python3 $T/render.py "$f" "$FP/$(basename "$f" .blueprint)" >/dev/null
done
python3 - "$FW" "$FP" <<'PY'
import sys
from pathlib import Path
from PIL import Image, ImageOps
pack, prev = Path(sys.argv[1]), Path(sys.argv[2])
def square(im, bg):
    side = max(im.size); out = Image.new("RGBA", (side, side), bg)
    out.paste(im, ((side - im.width) // 2, (side - im.height) // 2), im); return out
im = Image.open(prev / "mobtower_front.png").convert("RGBA")
square(im, (236, 240, 244, 255)).resize((128, 128), Image.LANCZOS).save(pack / "farmworks.png")
icon = square(im, (0, 0, 0, 0)).resize((20, 20), Image.LANCZOS)
for cat in ("decorations", "trade"):
    icon.save(pack / cat / "icon.png")
    g = ImageOps.grayscale(icon.convert("RGB")).convert("RGBA"); g.putalpha(icon.getchannel("A"))
    g.save(pack / cat / "icon_disabled.png")
PY
echo "built $PACK, stylepacks/Hearthwood, stylepacks/Cascadia and stylepacks/Farmworks"
