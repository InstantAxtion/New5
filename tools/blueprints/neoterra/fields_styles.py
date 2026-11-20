"""
Fields for Hearthwood and Cascadia: own names (no more neo* leftovers from Neoterra) and own borders.

The working part of each field (farmland, water, plant spots, the plantation / scarecrow block and its tags) is kept
exactly, so the farmer and the plantation still use them; the names (file, path, name, schematic name) and the
border change per pack:

  Hearthwood  low brick garden wall with dark-oak railings and lanterns on the corner posts
              cottagegarden, cottagegardenlarge, bamboogrove, cactushouse, kelppond, canebed
  Cascadia    split-rail spruce fence on mossy stone footings, log corner posts
              homesteadfield, homesteadfieldlarge, bamboostand, cactuspatch, kelpslough, canemarsh

usage: python fields_styles.py <pack dir> <Hearthwood|Cascadia>
"""
from __future__ import annotations

import sys
from pathlib import Path

from nbtlib import tag as NBT

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from blueprint import load, AIR  # noqa: E402

NAMES = {
    "Hearthwood": {"neofield": "cottagegarden", "neofieldlarge": "cottagegardenlarge", "neobamboo": "bamboogrove",
                   "neocactus": "cactushouse", "neokelp": "kelppond", "neosugar": "canebed"},
    "Cascadia": {"neofield": "homesteadfield", "neofieldlarge": "homesteadfieldlarge", "neobamboo": "bamboostand",
                 "neocactus": "cactuspatch", "neokelp": "kelpslough", "neosugar": "canemarsh"},
}
KEEP = ("farmland", "water", "blockhut", "substitution", "bamboo", "cactus", "sugar_cane", "kelp", "sand", "dirt",
        "glass", "glowstone", "sea_lantern")


def border(style, x, y, z, corner, gy):
    if style == "Hearthwood":
        if y == gy + 1:
            return "minecraft:bricks"
        if y == gy + 2:
            return "minecraft:stripped_dark_oak_log[axis=y]" if corner else \
                "minecraft:dark_oak_fence[east=false,north=false,south=false,waterlogged=false,west=false]"
        if y == gy + 3 and corner:
            return "minecraft:lantern[hanging=false,waterlogged=false]"
    else:
        if y == gy + 1:
            return "minecraft:spruce_log[axis=y]" if corner else ("minecraft:mossy_cobblestone" if (x + z) % 3 == 0 else
                                                                 "minecraft:spruce_fence[east=false,north=false,south=false,waterlogged=false,west=false]")
        if y == gy + 2:
            return "minecraft:spruce_log[axis=y]" if corner else \
                "minecraft:spruce_fence[east=false,north=false,south=false,waterlogged=false,west=false]"
    return None


def process(path: Path, style: str):
    old = path.stem
    new = NAMES[style].get(old)
    if not new:
        return None
    bp = load(path)
    hx, hy, hz = bp.primary_offset
    gy = hy - 1 if hy >= 1 else 1
    sx, sz = bp.sx, bp.sz
    for x in range(sx):
        for z in range(sz):
            if not (x in (0, sx - 1) or z in (0, sz - 1)):
                continue
            corner = x in (0, sx - 1) and z in (0, sz - 1)
            gap = (z in (0, sz - 1) and abs(x - sx // 2) <= 1) or (x in (0, sx - 1) and abs(z - sz // 2) <= 1) \
                or (abs(x - hx) <= 1 and abs(z - hz) <= 1)
            for y in range(gy + 1, bp.sy):
                s = bp.get(x, y, z)
                if (x, y, z) in bp.tile_entities and "blockhut" in s:
                    continue
                if any(k in s for k in KEEP) and "glass" not in s:
                    continue
                if s == AIR and y > gy + 3:
                    continue
                b = None if gap else border(style, x, y, z, corner, gy)
                if gap and y <= gy + 3 and (x, y, z) != (hx, hy, hz) and s != AIR \
                        and any(k in s for k in ("fence", "bricks", "log", "lantern", "cobblestone")):
                    bp.tile_entities.pop((x, y, z), None)
                    bp.set(x, y, z, AIR)
                    continue
                if b is not None:
                    if (x, y, z) == (hx, hy, hz):
                        continue
                    bp.tile_entities.pop((x, y, z), None)
                    bp.set(x, y, z, b)
                elif s != AIR and y > gy + 2 and "kelp" not in path.name:
                    bp.tile_entities.pop((x, y, z), None)
                    bp.set(x, y, z, AIR)
    te = bp.tile_entities.get((hx, hy, hz))
    rel = path.relative_to(path.parents[2]).as_posix().replace(old, new)
    if te is not None:
        if "path" in te:
            te["path"] = NBT.String(rel)
        if "name" in te:
            te["name"] = NBT.String(new)
        bdp = te.get("blueprintDataProvider")
        if bdp is not None:
            bdp["path"] = NBT.String(rel)
            bdp["schematicName"] = NBT.String(new)
            if "pack" in bdp:
                bdp["pack"] = NBT.String(style)
    bp.name = f"{new}.blueprint"
    target = path.with_name(f"{new}.blueprint")
    bp.save(target)
    path.unlink()
    return f"{old} -> {new}"


def main():
    root, style = Path(sys.argv[1]), sys.argv[2]
    done = [r for f in sorted(root.rglob("neo*.blueprint")) if (r := process(f, style))]
    print(f"{style}: fields renamed and re-bordered: {', '.join(done)}")


if __name__ == "__main__":
    main()
