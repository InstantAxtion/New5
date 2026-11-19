"""
Sky tower facades: a regular high-rise elevation per pack (storey bands, corner piers, even wall cladding),
paved forecourt instead of lawn and trees. Only blocks facing the outside are changed; flats, lobby, beds,
balconies, glass and everything functional stay as they are.

  Neoterra    white concrete with light-grey storey bands and grey piers
  Hearthwood  red-brick mansion block: brick walls, white stone bands, dark corner piers, brick base
  Cascadia    timber tower: spruce cladding, dark-oak bands and piers, river-rock base

usage: python skyskin.py <pack dir> <style>
"""
from __future__ import annotations

import sys
from collections import deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from blueprint import load, AIR  # noqa: E402

SKIN = {
    "Neoterra": dict(wall="white_concrete", band="light_gray_concrete", pier="gray_concrete", base="smooth_stone",
                     pave="smooth_stone"),
    "Hearthwood": dict(wall="bricks", band="white_terracotta", pier="stripped_dark_oak_log[axis=y]", base="stone_bricks",
                       pave="stone_bricks"),
    "Cascadia": dict(wall="spruce_planks", band="dark_oak_planks", pier="dark_oak_log[axis=y]", base="cobblestone",
                     pave="cobblestone"),
}
KEEP = ("glass", "door", "ladder", "bed", "blockhut", "barrel", "furnace", "crafting", "chest", "lantern", "torch",
        "substitution", "rack", "stairs", "slab", "fence", "pane", "carpet", "trapdoor", "bars", "button", "sign",
        "flower", "pot", "campfire", "rod", "chain", "candle", "table", "lectern", "bell", "leaves", "grass_block",
        "end_rod", "sea_lantern", "glowstone", "shroomlight")
NATURE = ("leaves", "_log", "short_grass", "tall_grass", "fern", "flower", "bush", "azalea", "poppy", "dandelion",
          "tulip", "daisy", "cornflower", "allium", "orchid", "lily")


def name(s):
    return s.split("[")[0].split(":")[-1]


def skin(path: Path, style: str):
    bp = load(path)
    k = SKIN[style]
    sx, sy, sz = bp.sx, bp.sy, bp.sz
    # building footprint: columns with glass anywhere above the ground floor
    cols = {(x, z) for x, y, z, s in bp.blocks() if y >= 3 and "glass" in s}
    if not cols:
        return 0
    x1, x2 = min(c[0] for c in cols), max(c[0] for c in cols)
    z1, z2 = min(c[1] for c in cols), max(c[1] for c in cols)
    # 1) nature outside the footprint: trees, plants, lawn
    for x in range(sx):
        for z in range(sz):
            inside = x1 <= x <= x2 and z1 <= z <= z2
            for y in range(1, sy):
                n = name(bp.get(x, y, z))
                if not inside and any(t in n for t in NATURE) and not n.startswith("stripped") and y >= 2:
                    bp.set(x, y, z, AIR)
            n = name(bp.get(x, 1, z))
            if n in ("grass_block", "dirt", "coarse_dirt", "podzol", "moss_block", "rooted_dirt"):
                bp.set(x, 1, z, "minecraft:" + k["pave"])
    # 2) outside air (flood fill from the boundary)
    out = set()
    q = deque()
    for x in range(sx):
        for z in range(sz):
            for y in range(sy):
                if (x in (0, sx - 1) or z in (0, sz - 1) or y == sy - 1) and bp.get(x, y, z) == AIR:
                    out.add((x, y, z))
                    q.append((x, y, z))
    while q:
        x, y, z = q.popleft()
        for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            n = (x + dx, y + dy, z + dz)
            if n in out or not bp.inside(*n) or bp.get(*n) != AIR:
                continue
            out.add(n)
            q.append(n)
    # 3) recolour outward-facing cladding in a regular pattern
    changed = 0
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            for y in range(2, sy):
                s = bp.get(x, y, z)
                n = name(s)
                if s == AIR or any(t in n for t in KEEP):
                    continue
                if not any((x + dx, y, z + dz) in out for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    continue
                corner = x in (x1, x2) and z in (z1, z2)
                if y <= 3:
                    m = k["base"]
                elif corner:
                    m = k["pier"]
                elif y % 5 == 1:
                    m = k["band"]
                else:
                    m = k["wall"]
                bp.set(x, y, z, "minecraft:" + m)
                changed += 1
    bp.save(path)
    return changed


def main():
    root, style = Path(sys.argv[1]), sys.argv[2]
    for L in range(1, 6):
        p = root / "fundamentals" / f"skytower{L}.blueprint"
        print(f"skytower{L}: {skin(p, style)} facade blocks")


if __name__ == "__main__":
    main()
