"""
Neoterra Warehouse ("Distribution Centre"), levels 1-5
(MineColonies hut: minecolonies:blockhutwarehouse, block entity minecolonies:warehouse).

Style: realistic near-future logistics hall: tall white concrete shell with a clerestory glass
band, timber band and louvres, two loading docks under a timber canopy, rooftop solar,
skylights and a green roof.

The warehouse's capacity comes from MineColonies racks (single racks, 3 high max so couriers can
reach them). Racks grow every level:

  L1  36 racks   one double row, 1 high.        Hut counter, crafting table.
  L2  72 racks   same row, 2 high.              Dock canopy, bay markings, rooftop solar.
  L3  144 racks  two double rows, 2 high.       Office mezzanine (stairs), skylights, tinted glass.
  L4  216 racks  three double rows, 2 high.     Roof access, railing, green roof, trees & lamps.
  L5  324 racks  three double rows, 3 high.     Timber louvres, roof garden, mast, ender chest.

Same 31 x 20 x 25 footprint every level. Front = north (z 0). y 0 foundation, y 1 ground.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    Blueprint, Style, put, hut_te, connect_panes, tree, planter, street_lamp, solar_panels,
    do_slab, rack,
)

SX, SY, SZ = 31, 20, 25
X1, X2, Z1, Z2 = 2, 28, 5, 22          # hall shell
ROOF = 11
MEZZ = 7                               # office mezzanine floor (x3..12, z6..8), L3+
DOCKS = ((6, 10), (20, 24))            # loading door x-ranges (5 wide, 5 tall)
ROWS = ((9, 10), (13, 14), (17, 18))   # back-to-back rack rows (z)
RACK_X = list(range(5, 14)) + list(range(17, 26))   # cross aisle x14..16 stays clear


def rack_plan(level):
    """(number of double rows, rack height) per level."""
    return {1: (1, 1), 2: (1, 2), 3: (2, 2), 4: (3, 2), 5: (3, 3)}[level]


def build(level: int) -> Blueprint:
    L = level
    st = Style(L)
    bp = Blueprint(SX, SY, SZ, f"warehouse{L}.blueprint")
    W, G, T, WOOD, DECK = st.WHITE, st.GLASS, st.TRIM, st.WOOD, st.DECK
    mullion = W if st.early else WOOD
    band = T if st.early else DECK

    # ------------------------------------------------------------ ground
    bp.fill(0, 0, 0, SX - 1, 0, SZ - 1, "structurize:blocksolidsubstitution")
    for x in range(SX):
        for z in range(SZ):
            inside = X1 <= x <= X2 and Z1 <= z <= Z2
            if inside:
                s = st.floor(x, z)
                if not st.early and 14 <= x <= 16:
                    s = "smooth_stone"                             # cross aisle
            elif z <= 4:
                in_bay = any(a - 1 <= x <= b + 1 for a, b in DOCKS)
                if L >= 2 and in_bay:
                    s = W if any(x in (a - 1, b + 1) for a, b in DOCKS) else st.LIGHTGRAY
                else:
                    s = "smooth_stone" if (x + z) % 2 else "polished_andesite"
            else:
                s = "grass_block[snowy=false]"
            bp.set(x, 1, z, s)

    # ------------------------------------------------------------ shell
    def facade(u, y, length_pos, front=False, x=None):
        if y == ROOF - 1:
            return W
        if y in (8, 9):
            return mullion if length_pos % 3 == 0 else G         # clerestory band
        if y == 7:
            return band
        if front:
            if any(a <= x <= b for a, b in DOCKS) and y <= 6:
                return "air"
            if 14 <= x <= 16 and y <= 4:
                return "air"
            if (12 <= x <= 18) and y <= 6:
                return G if x not in (12, 18) else mullion       # glazed entrance bay
        return W
    for x in range(X1, X2 + 1):
        for y in range(2, ROOF):
            bp.set(x, y, Z1, facade(x, y, x - X1, front=True, x=x))
            bp.set(x, y, Z2, facade(x, y, x - X1))
    for z in range(Z1 + 1, Z2):
        for y in range(2, ROOF):
            bp.set(X1, y, z, facade(z, y, z - Z1))
            bp.set(X2, y, z, facade(z, y, z - Z1))

    # roof: skylights (L3+) over the aisles, recessed lights elsewhere
    for x in range(X1, X2 + 1):
        for z in range(Z1, Z2 + 1):
            edge = x in (X1, X2) or z in (Z1, Z2)
            skylight = L >= 3 and z in (12, 16, 20) and 5 <= x <= 25
            bp.set(x, ROOF, z, W if edge else ("glass" if skylight else "smooth_stone"))
    for x in (6, 11, 19, 24):
        for z in (7, 11, 15, 19):
            st.ceiling_light(bp, x, ROOF, z)

    # ------------------------------------------------------------ racks
    rows, height = rack_plan(L)
    for zf, zb in ROWS[:rows]:
        for x in RACK_X:
            for y in range(2, 2 + height):
                rack(bp, x, y, zf, "north")
                rack(bp, x, y, zb, "south")
        if height < 3:  # end cap: a timber post at the east end of each row
            for x in (26,):
                for z in (zf, zb):
                    bp.fill(x, 2, z, x, 1 + height, z, WOOD)

    # ------------------------------------------------------------ L2: canopy, solar
    if L >= 2:
        for x in range(4, 27):
            for z in range(1, Z1):
                bp.set(x, 8, z, W if z == 1 or x in (4, 26) else DECK)
        for x in (4, 15, 26):
            bp.fill(x, 2, 1, x, 7, 1, T)
        for x in (8, 22):
            st.ceiling_light(bp, x, 8, 3)
        solar_panels(bp, 4, ROOF + 1, 7, 26, 10)
        if L == 2:
            solar_panels(bp, 4, ROOF + 1, 13, 26, 20)

    # ------------------------------------------------------------ L3: mezzanine office
    if L >= 3:
        for x in range(3, 13):
            for z in range(6, 9):
                bp.set(x, MEZZ, z, DECK)
        for x in range(3, 13):
            put(bp, x, MEZZ + 1, 9, st.railing)
        for z in range(6, 9):
            put(bp, 13, MEZZ + 1, z, st.railing)
        # stairs up the west side aisle (2 wide), rising north
        for i in range(6):
            z, y = 14 - i, 2 + i
            for x in (3, 4):
                if y > 2:
                    bp.fill(x, 2, z, x, y - 1, z, W)
                bp.set(x, y, z, "spruce_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]")
        for x in (3, 4):
            put(bp, x, MEZZ + 1, 9, "air")                        # top of the stairs
        # office furniture
        y = MEZZ + 1
        for x in range(6, 10):
            put(bp, x, y, 7, do_slab(T, "top"))                   # desk facing the hall
        for x in (6, 8):
            bp.set(x, y, 8, "spruce_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]")
        bp.set(3, y, 6, "crafting_table")
        bp.set(4, y, 6, "cartography_table")
        bp.set(5, y, 6, "lectern[facing=south,has_book=false,powered=false]")
        for x in (10, 11, 12):
            bp.set(x, y, 6, "barrel[facing=south,open=false]")
        bp.set(12, y, 7, "barrel[facing=west,open=false]")

    # ------------------------------------------------------------ L4: roof access, green roof, trees
    if L >= 4:
        for x in range(X1, X2 + 1):
            for z in range(Z1, Z2 + 1):
                if x in (X1, X2) or z in (Z1, Z2):
                    put(bp, x, ROOF + 1, z, st.railing)
        for y in range(2, ROOF + 1):
            bp.set(27, y, 21, "ladder[facing=west,waterlogged=false]")
        for x in range(4, 27):
            for z in (14, 18):
                bp.set(x, ROOF, z, "grass_block[snowy=false]")
                if x % 3 == 0:
                    bp.set(x, ROOF + 1, z, "short_grass" if x % 2 else "flowering_azalea")
        solar_panels(bp, 4, ROOF + 1, 21, 24, 21)
        tree(bp, 1, 2, 1, h=4)
        tree(bp, 29, 2, 1, h=4)
        street_lamp(bp, 1, 2, 4)
        street_lamp(bp, 29, 2, 4)

    # ------------------------------------------------------------ L5: louvres, roof garden, mast
    if L >= 5:
        for z in range(Z1 + 1, Z2 + 1, 2):
            for x in (X1 - 1, X2 + 1):
                bp.fill(x, 2, z, x, ROOF - 1, z, WOOD)
        for x in range(X1 + 1, X2, 2):
            bp.fill(x, 2, Z2 + 1, x, ROOF - 1, Z2 + 1, WOOD)
        for x in (8, 22):
            planter(bp, x, ROOF + 1, 17, "moss_carpet")
            tree(bp, x, ROOF + 2, 17, h=2)
        bp.set(26, ROOF + 1, 19, T)
        for y in range(ROOF + 2, SY - 1):
            bp.set(26, y, 19, "chain[axis=y,waterlogged=false]")
        bp.set(26, SY - 1, 19, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        bp.set(11, MEZZ + 1, 7, "ender_chest[facing=north,waterlogged=false]")

    # ------------------------------------------------------------ hut & counter
    sit = []
    hut = (17, 2, 7)
    for x in range(17, 20):
        put(bp, x, 2, 6, st.counter)
    put(bp, 19, 2, 7, st.counter)
    bp.set(20, 2, 7, "crafting_table")
    if L >= 3:
        for x in (6, 8):
            sit.append((x, MEZZ + 1, 8))

    connect_panes(bp)
    tags = {hut: ["neoterra"], (0, 1, 0): ["groundlevel"]}
    for p in sit:
        tags.setdefault(p, []).append("sit")
    path = f"craftsmanship/storage/warehouse{L}.blueprint"
    bp.set(*hut, "minecolonies:blockhutwarehouse[facing=north]",
           hut_te(path, (SX, SY, SZ), hut, tags, te_id="minecolonies:warehouse"))
    bp.primary_offset = hut
    bp.architects = ["Neoterra"]
    return bp


if __name__ == "__main__":
    out_dir = Path(sys.argv[1])
    out_dir.mkdir(parents=True, exist_ok=True)
    for lvl in range(1, 6):
        b = build(lvl)
        b.save(out_dir / f"warehouse{lvl}.blueprint")
        racks = sum(1 for *_, s in b.blocks() if "rack" in s)
        n = sum(1 for *_, s in b.blocks() if s not in ("minecraft:air", "structurize:blocksolidsubstitution"))
        print(f"warehouse{lvl}: {n} blocks, {racks} racks")
