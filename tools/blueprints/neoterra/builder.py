"""
Neoterra Builder's Hut ("Fabrication Hub"), levels 1-5 (minecolonies:blockhutbuilder).

Style: near-future construction company. A glass lobby with chamfered corners carries a floating
upper box (cantilevered on slim pilotis, ribbon window all round). Next to it, a fabrication
yard with a big 3D-printing gantry over a print bed, where a printed concrete pod grows every
level. Racks sit in a covered materials store at the back of the yard.

Levels 1-3 use the cheap palette; level 4+ the premium one with glowing light strips
(see common.CHEAP_UNTIL).

  L1  Lobby            glass lobby with the hut behind a counter; crafting & cartography
                       tables, barrels; fenced yard with 8 racks.
  L2  Floating Studio  cantilevered upper box (design studio, stairs), workshop corner
                       (stonecutter, grindstone, anvil, smithing table), 3D-printing gantry
                       with a first printed ring, covered racks (11).
  L3  Roof Deck        roof deck + ladder, taller printed pod, 22 racks.
  L4  Premium upgrade  tinted glass, light strips (box soffit, bands, gantry), glowing print
                       nozzle, Architect's Cutter, bed, solar, trees + light columns, 33 racks.
  L5  Landmark         printed pod finished with a glass oculus, glowing box edges, roof garden,
                       antenna spire, ender chest, 44 racks.

Same 29 x 28 x 25 footprint every level. Front = north (z 0). y 0 foundation, y 1 ground.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    Blueprint, Style, put, hut_te, connect_panes, tree, planter, street_lamp, solar_panels,
    do_slab, rack,
)

SX, SY, SZ = 29, 28, 25
LX1, LX2, LZ1, LZ2 = 3, 12, 6, 18      # glass lobby (ground floor)
BX1, BX2, BZ1, BZ2 = 2, 13, 3, 20      # floating upper box
SLAB, BOX_ROOF = 7, 14
BED = (21, 12)                          # print bed centre (x, z)
GANTRY_X = (16, 26)
GANTRY_Z = (7, 17)
GANTRY_TOP = 13
RACK_ROWS = {  # level -> list of (z, facing, height, x range)
    1: [(20, "north", 1, range(16, 24))],
    2: [(20, "north", 1, range(16, 27))],
    3: [(20, "north", 2, range(16, 27))],
    4: [(20, "north", 2, range(16, 27)), (22, "south", 1, range(16, 27))],
    5: [(20, "north", 2, range(16, 27)), (22, "south", 2, range(16, 27))],
}
PRINT_HEIGHT = {1: 0, 2: 2, 3: 4, 4: 6, 5: 7}


def chamfer(x, z, x1, x2, z1, z2):
    return x in (x1, x2) and z in (z1, z2)


def build(level: int) -> Blueprint:
    L = level
    st = Style(L)
    bp = Blueprint(SX, SY, SZ, f"builder{L}.blueprint")
    W, G, T, WOOD, DECK = st.WHITE, st.GLASS, st.TRIM, st.WOOD, st.DECK
    glow = st.GLOW                        # None on cheap levels
    band = st.band
    sit = []

    # ------------------------------------------------------------ ground
    bp.fill(0, 0, 0, SX - 1, 0, SZ - 1, "structurize:blocksolidsubstitution")
    for x in range(SX):
        for z in range(SZ):
            bx, bz = BED
            if LX1 <= x <= LX2 and LZ1 <= z <= LZ2:
                s = st.floor(x, z)
            elif abs(x - bx) <= 4 and abs(z - bz) <= 4:
                edge = abs(x - bx) == 4 or abs(z - bz) == 4
                s = (glow if glow and edge else "smooth_stone")                 # print bed
            elif 15 <= x <= 27 and 3 <= z <= 23:
                s = "polished_andesite" if (x + z) % 2 else "smooth_stone"      # yard
            elif z <= 2:
                s = "smooth_stone" if (x // 2 + z) % 2 else "polished_andesite"
            else:
                s = "grass_block[snowy=false]"
            bp.set(x, 1, z, s)

    # ------------------------------------------------------------ glass lobby
    for x in range(LX1, LX2 + 1):
        for z in range(LZ1, LZ2 + 1):
            if not (x in (LX1, LX2) or z in (LZ1, LZ2)):
                continue
            for y in range(2, SLAB):
                if chamfer(x, z, LX1, LX2, LZ1, LZ2):
                    s = "air"
                elif y == 6:
                    s = band
                elif z == LZ1 and x in (7, 8) and y <= 4:
                    s = "air"                                          # main entrance
                elif x == LX2 and z == 11 and y <= 4:
                    s = "air"                                          # door to the yard
                elif z == LZ2 and L == 1:
                    s = W
                elif (x + z) % 3 == 0:
                    s = T                                              # slim mullions
                else:
                    s = G
                bp.set(x, y, z, s)
    for x, z in ((LX1 + 1, LZ1 + 1), (LX2 - 1, LZ1 + 1), (LX1 + 1, LZ2 - 1), (LX2 - 1, LZ2 - 1)):
        for y in range(2, SLAB):
            bp.set(x, y, z, band if y == 6 else G)

    # ------------------------------------------------------------ slab / L1 roof
    if L == 1:
        for x in range(LX1, LX2 + 1):
            for z in range(LZ1, LZ2 + 1):
                if chamfer(x, z, LX1, LX2, LZ1, LZ2):
                    continue
                edge = x in (LX1, LX2) or z in (LZ1, LZ2)
                bp.set(x, SLAB, z, W if edge else "smooth_stone")
        for x in range(LX1, LX2 + 1):
            for z in range(LZ1, LZ2 + 1):
                if (x in (LX1, LX2) or z in (LZ1, LZ2)) and not chamfer(x, z, LX1, LX2, LZ1, LZ2):
                    put(bp, x, SLAB + 1, z, st.railing)
    else:
        # ------------------------------------------------ L2+: floating box on pilotis
        for x in range(BX1, BX2 + 1):
            for z in range(BZ1, BZ2 + 1):
                if chamfer(x, z, BX1, BX2, BZ1, BZ2):
                    continue
                edge = x in (BX1, BX2) or z in (BZ1, BZ2)
                bp.set(x, SLAB, z, (glow or W) if edge else st.floor(x, z))       # glowing soffit edge
                bp.set(x, BOX_ROOF, z, W if edge else ("smooth_stone" if L < 3 else DECK))
                if not edge:
                    continue
                for y in range(SLAB + 1, BOX_ROOF):
                    if y in (SLAB + 1, BOX_ROOF - 2):
                        s = W
                    elif y == BOX_ROOF - 1:
                        s = band
                    else:
                        s = G                                          # ribbon window
                    bp.set(x, y, z, s)
        for x, z in ((BX1 + 1, BZ1 + 1), (BX2 - 1, BZ1 + 1), (BX1 + 1, BZ2 - 1), (BX2 - 1, BZ2 - 1)):
            for y in range(SLAB + 1, BOX_ROOF):
                bp.set(x, y, z, W if y in (SLAB + 1, BOX_ROOF - 2) else (band if y == BOX_ROOF - 1 else G))
        for x, z in ((4, 4), (11, 4), (4, 19), (11, 19)):
            bp.fill(x, 2, z, x, SLAB - 1, z, T)                        # slim pilotis
        for x, z in ((5, 9), (9, 9), (6, 14), (10, 15)):
            st.ceiling_light(bp, x, BOX_ROOF, z)
        # stairs from the lobby up into the box (x4, rising south z12 -> z17)
        for i in range(6):
            z, y = 12 + i, 2 + i
            if y > 2:
                bp.fill(4, 2, z, 4, y - 1, z, W)
            bp.set(4, y, z, "spruce_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]")
        for z in range(12, 17):
            bp.set(4, SLAB, z, "air")
            put(bp, 5, SLAB + 1, z, st.railing)
        put(bp, 4, SLAB + 1, 11, st.railing)
        # design studio
        y = SLAB + 1
        for z in range(5, 11):
            bp.set(3, y, z, "bookshelf")
            bp.set(3, y + 1, z, "bookshelf")
        for x in range(7, 11):
            put(bp, x, y, 6, st.counter if st.early else do_slab(T, "top"))        # drawing tables
        for x in (7, 9):
            bp.set(x, y, 7, "spruce_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]")
        bp.set(11, y, 5, "lectern[facing=south,has_book=false,powered=false]")
        bp.set(12, y, 5, "cartography_table")
        bp.set(12, y, 6, "crafting_table")

    for x, z in ((6, 9), (9, 13), (6, 16)):                           # lobby ceiling lights
        st.ceiling_light(bp, x, SLAB, z)

    # ------------------------------------------------------------ L3: roof deck
    if L >= 3:
        for x in range(BX1, BX2 + 1):
            for z in range(BZ1, BZ2 + 1):
                if (x in (BX1, BX2) or z in (BZ1, BZ2)) and not chamfer(x, z, BX1, BX2, BZ1, BZ2):
                    put(bp, x, BOX_ROOF + 1, z, st.railing)
        for y in range(SLAB + 1, BOX_ROOF + 1):
            bp.set(12, y, 19, "ladder[facing=west,waterlogged=false]")
        for z in (13, 17):
            planter(bp, 3, BOX_ROOF + 1, z)

    # ------------------------------------------------------------ yard fence
    for x in range(14, SX):
        for z in range(2, SZ):
            on_line = (x == SX - 1 or z in (2, SZ - 1)) and not (z == 2 and 18 <= x <= 24)
            if on_line:
                put(bp, x, 2, z, st.railing)

    # ------------------------------------------------------------ 3D-printing gantry + printed pod
    if L >= 2:
        gx1, gx2 = GANTRY_X
        gz1, gz2 = GANTRY_Z
        top = GANTRY_TOP
        leg = W
        for x in (gx1, gx2):
            for z in (gz1, gz2):
                bp.set(x, 1, z, T)                                         # base plate
                for y in range(2, top):
                    bp.set(x, y, z, glow if glow and y % 4 == 0 else leg)
            for z in range(gz1, gz2 + 1):                                  # rails
                bp.set(x, top, z, T)
        bx, bz = BED
        for x in range(gx1, gx2 + 1):                                      # bridge
            bp.set(x, top, bz, T)
            bp.set(x, top + 1, bz, W)
            if glow and gx1 < x < gx2:
                bp.set(x, top - 1, bz, "end_rod[facing=down]" if x % 2 == 0 else "air")
        # print head carriage + nozzle
        bp.fill(bx - 1, top - 1, bz - 1, bx + 1, top - 1, bz + 1, T)
        bp.set(bx, top - 1, bz, W)
        bp.set(bx, top - 2, bz, "end_rod[facing=down]" if glow else "hopper[enabled=true,facing=down]")
        # printed pod: layered ring that grows and tapers into a dome
        h = PRINT_HEIGHT[L]
        for k in range(h):
            y = 2 + k
            r = 3.5 - max(0, k - 3) * 0.75
            mat = (W if k % 2 else st.LIGHTGRAY) if not st.early else ("smooth_stone" if k % 2 else st.LIGHTGRAY)
            for x in range(bx - 4, bx + 5):
                for z in range(bz - 4, bz + 5):
                    d = math.hypot(x - bx, z - bz)
                    if r - 1 <= d < r and not (z > bz and x == bx and k < 2):   # doorway on the south
                        bp.set(x, y, z, mat)
        if L >= 5:
            bp.set(bx, 2 + h, bz, "glass")                                 # oculus
            for x, z in ((bx - 1, bz), (bx + 1, bz), (bx, bz - 1), (bx, bz + 1)):
                bp.set(x, 2 + h, z, W)
            bp.set(bx, 1, bz, "sea_lantern")

    # ------------------------------------------------------------ materials store (racks)
    for z_row, facing, height, xs in RACK_ROWS[L]:
        for x in xs:
            for y in range(2, 2 + height):
                rack(bp, x, y, z_row, facing)
    if L >= 2:
        for x in range(15, 28):
            for z in range(19, 24):
                bp.set(x, 6, z, (glow or W) if z == 19 else DECK)
        for x, z in ((15, 19), (27, 19), (15, 23), (27, 23)):
            bp.fill(x, 2, z, x, 5, z, T)
        for x in (18, 24):
            st.ceiling_light(bp, x, 6, 21)

    # ------------------------------------------------------------ L4: sky box + premium extras
    SKX1, SKX2, SKZ1, SKZ2, SK_TOP = 6, 13, 1, 11, 20
    if L >= 4:
        # second glass box stacked on the roof, cantilevered 2 blocks further over the entrance
        for x in range(SKX1, SKX2 + 1):
            for z in range(SKZ1, SKZ2 + 1):
                if chamfer(x, z, SKX1, SKX2, SKZ1, SKZ2):
                    continue
                edge = x in (SKX1, SKX2) or z in (SKZ1, SKZ2)
                if z < BZ1:
                    bp.set(x, BOX_ROOF, z, glow if edge else W)               # cantilevered floor
                elif not edge:
                    bp.set(x, BOX_ROOF, z, DECK)
                bp.set(x, SK_TOP, z, W if edge else "smooth_stone")
                for y in range(BOX_ROOF + 1, SK_TOP):
                    if not edge:
                        bp.set(x, y, z, "air")
                    elif y == SK_TOP - 1:
                        bp.set(x, y, z, band)
                    elif z == SKZ1:
                        bp.set(x, y, z, T if x in (SKX1 + 2, SKX2 - 2) else G)  # full-height glass front
                    elif z == SKZ2 and x in (9, 10) and y <= BOX_ROOF + 2:
                        bp.set(x, y, z, "air")                                 # door from the roof deck
                    else:
                        bp.set(x, y, z, W if y == BOX_ROOF + 1 else G)
        for x, z in ((SKX1 + 1, SKZ1 + 1), (SKX2 - 1, SKZ1 + 1), (SKX1 + 1, SKZ2 - 1), (SKX2 - 1, SKZ2 - 1)):
            for y in range(BOX_ROOF + 1, SK_TOP):
                bp.set(x, y, z, band if y == SK_TOP - 1 else G)
        for x, z in ((8, 4), (11, 4), (9, 8)):
            st.ceiling_light(bp, x, SK_TOP, z)
        # sky lounge: bed (respawn), jukebox, seats
        y = BOX_ROOF + 1
        bp.set(8, y, 9, "light_gray_bed[facing=west,occupied=false,part=foot]")
        bp.set(7, y, 9, "light_gray_bed[facing=west,occupied=false,part=head]")
        bp.set(12, y, 9, "jukebox[has_record=false]")
        for x in (8, 9, 10, 11):
            bp.set(x, y, 3, "spruce_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]")
            sit.append((x, y, 3))
        solar_panels(bp, 8, BOX_ROOF + 1, 13, 11, 18)
        bp.set(9, 2, 17, "domum_ornamentum:architectscutter[facing=north]")
        tree(bp, 1, 2, 1, h=3)
        street_lamp(bp, 14, 2, 1, premium=True)
        street_lamp(bp, 27, 2, 1, premium=True)

    # ------------------------------------------------------------ L5: landmark
    if L >= 5:
        for x, z in ((BX1, BZ1 + 1), (BX2, BZ1 + 1), (BX1, BZ2 - 1), (BX2, BZ2 - 1),
                     (BX1 + 1, BZ1), (BX2 - 1, BZ1), (BX1 + 1, BZ2), (BX2 - 1, BZ2)):
            for y in range(SLAB + 1, BOX_ROOF):
                bp.set(x, y, z, "sea_lantern")                             # glowing box edges
        for x, z in ((SKX1, SKZ1 + 1), (SKX2, SKZ1 + 1), (SKX1 + 1, SKZ1), (SKX2 - 1, SKZ1)):
            for y in range(BOX_ROOF + 1, SK_TOP):
                bp.set(x, y, z, "sea_lantern")
        for x, z in ((5, 15), (5, 17)):
            planter(bp, x, BOX_ROOF + 1, z)
        bp.set(10, SK_TOP + 1, 6, T)
        for y in range(SK_TOP + 2, SY - 2):
            bp.set(10, y, 6, "end_rod[facing=up]" if y % 2 else "chain[axis=y,waterlogged=false]")
        bp.set(10, SY - 2, 6, "sea_lantern")
        bp.set(10, SY - 1, 6, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        bp.set(11, BOX_ROOF + 1, 9, "ender_chest[facing=north,waterlogged=false]")

    # ------------------------------------------------------------ lobby: hut, counter, workshop
    hut = (10, 2, 10)
    for x, z in ((9, 9), (10, 9), (11, 9), (9, 10)):
        put(bp, x, 2, z, st.counter)
    bp.set(6, 2, 17, "crafting_table")
    bp.set(7, 2, 17, "cartography_table")
    bp.set(10, 2, 17, "barrel[facing=up,open=false]")
    bp.set(10, 3, 17, "barrel[facing=up,open=false]")
    for x in (5, 6):
        bp.set(x, 2, 8, "spruce_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]")
        sit.append((x, 2, 8))
    if L >= 2:
        for (x, z), s in (((11, 13), "stonecutter[facing=west]"), ((11, 14), "grindstone[face=floor,facing=west]"),
                          ((11, 15), "anvil[facing=north]"), ((8, 17), "smithing_table")):
            bp.set(x, 2, z, s)
        for x in (7, 9):
            sit.append((x, SLAB + 1, 7))

    connect_panes(bp)
    tags = {hut: ["neoterra"], (0, 1, 0): ["groundlevel"]}
    for p in sit:
        tags.setdefault(p, []).append("sit")
    path = f"fundamentals/builder{L}.blueprint"
    bp.set(*hut, "minecolonies:blockhutbuilder[facing=north]", hut_te(path, (SX, SY, SZ), hut, tags))
    bp.primary_offset = hut
    bp.architects = ["Neoterra"]
    return bp


if __name__ == "__main__":
    out_dir = Path(sys.argv[1])
    out_dir.mkdir(parents=True, exist_ok=True)
    for lvl in range(1, 6):
        b = build(lvl)
        b.save(out_dir / f"builder{lvl}.blueprint")
        racks = sum(1 for *_, s in b.blocks() if "rack" in s)
        n = sum(1 for *_, s in b.blocks() if s not in ("minecraft:air", "structurize:blocksolidsubstitution"))
        print(f"builder{lvl}: {n} blocks, {racks} racks")
