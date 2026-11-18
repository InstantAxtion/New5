"""
Neoterra Builder's Hut ("Construction Yard"), levels 1-5 (minecolonies:blockhutbuilder).

Style: realistic near-future construction company yard: a white concrete + glass site office,
an open timber workshop shed, a fenced materials yard with racks, and a yellow tower crane
you can climb (ladder up the mast to the cab and jib).

Levels 1-3 use the cheap palette, level 4+ the premium one (see common.CHEAP_UNTIL).

  L1  Site Office      ground-floor office with the hut, crafting & cartography tables;
                       fenced yard with 4 racks.
  L2  Workshop         timber workshop shed (stonecutter, grindstone, anvil, smithing table,
                       crafting table), 8 racks, material pallets, tower crane (14 high).
  L3  Drawing Office   upper floor drafting room (stairs, bookshelves, lectern, cartography),
                       16 racks under a canopy, crane 18 high.
  L4  Premium upgrade  tinted glass/DO trim, roof terrace with solar, architect's cutter,
                       24 racks, bed, crane 22 high, trees & lamps, concrete site hoarding.
  L5  Landmark         crane 26 high with lit cab and hook load, timber louvres, 32 racks,
                       ender chest, roof planters.

Same 25 x 34 x 21 footprint every level. Front = north (z 0). y 0 foundation, y 1 ground.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    Blueprint, Style, put, hut_te, connect_panes, tree, planter, street_lamp, solar_panels,
    do_slab, rack,
)

SX, SY, SZ = 25, 34, 21
OX1, OX2, OZ1, OZ2 = 2, 11, 4, 12      # site office
SHED_Z1, SHED_Z2 = 13, 18              # workshop shed behind the office
YX1, YX2, YZ1, YZ2 = 13, 23, 3, 19     # materials yard (fence line on the outer edge)
MAST = (20, 8)                         # crane mast centre (x, z); 3x3 mast
CRANE_TOP = {1: None, 2: 14, 3: 18, 4: 22, 5: 26}
RACKS = {1: [(18, 1, range(14, 18))], 2: [(18, 1, range(14, 22))], 3: [(18, 2, range(14, 22))],
         4: [(18, 2, range(14, 22)), (16, 1, range(14, 22))],
         5: [(18, 2, range(14, 22)), (16, 2, range(14, 22))]}   # (z, height, x range)


def build(level: int) -> Blueprint:
    L = level
    st = Style(L)
    bp = Blueprint(SX, SY, SZ, f"builder{L}.blueprint")
    W, G, T, WOOD, DECK = st.WHITE, st.GLASS, st.TRIM, st.WOOD, st.DECK
    mullion = W if st.early else WOOD
    band = T if st.early else DECK
    YELLOW = "yellow_concrete"

    # ------------------------------------------------------------ ground
    bp.fill(0, 0, 0, SX - 1, 0, SZ - 1, "structurize:blocksolidsubstitution")
    for x in range(SX):
        for z in range(SZ):
            if YX1 <= x <= YX2 and YZ1 <= z <= YZ2:
                s = "polished_andesite" if (x + z) % 3 else "smooth_stone"        # yard slab
            elif OX1 <= x <= OX2 and OZ1 <= z <= SHED_Z2:
                s = st.floor(x, z)
            elif z <= 3:
                s = "smooth_stone" if (x + z) % 2 else "polished_andesite"
            else:
                s = "grass_block[snowy=false]"
            bp.set(x, 1, z, s)

    # ------------------------------------------------------------ site office (ground floor)
    upper = L >= 3
    top1 = 7                                  # slab over the ground floor
    for x in range(OX1, OX2 + 1):
        for z in range(OZ1, OZ2 + 1):
            if not (x in (OX1, OX2) or z in (OZ1, OZ2)):
                continue
            for y in range(2, top1):
                if z == OZ1 and x in (6, 7) and y <= 4:
                    s = "air"                                         # entrance
                elif y == 6:
                    s = band
                elif z == OZ1:
                    s = mullion if x in (OX1, OX2) or (x - OX1) % 3 == 0 else G
                elif x == OX2 and z == 11 and y <= 4:
                    s = "air"                                         # side door to the yard
                elif x in (OX1, OX2) and 3 <= y <= 5 and (z - OZ1) % 3:
                    s = G
                elif z == OZ2 and x in (4, 5) and y <= 4 and L >= 2:
                    s = "air"                                         # back door to the workshop
                else:
                    s = W
                bp.set(x, y, z, s)
    for x in range(OX1, OX2 + 1):
        for z in range(OZ1, OZ2 + 1):
            edge = x in (OX1, OX2) or z in (OZ1, OZ2)
            bp.set(x, top1, z, W if edge else (st.floor(x, z) if upper else "smooth_stone"))
    for x, z in ((4, 6), (8, 6), (4, 10), (8, 10)):
        st.ceiling_light(bp, x, top1, z)

    # ------------------------------------------------------------ L3: drawing office upstairs
    top2 = 13
    if upper:
        for x in range(OX1, OX2 + 1):
            for z in range(OZ1, OZ2 + 1):
                if not (x in (OX1, OX2) or z in (OZ1, OZ2)):
                    continue
                for y in range(top1 + 1, top2):
                    if y == top2 - 1:
                        s = W
                    elif z == OZ1:
                        s = mullion if x in (OX1, OX2) or (x - OX1) % 3 == 0 else G
                    elif x in (OX1, OX2) and y in (9, 10, 11) and (z - OZ1) % 3:
                        s = G
                    else:
                        s = W
                    bp.set(x, y, z, s)
        for x in range(OX1, OX2 + 1):
            for z in range(OZ1, OZ2 + 1):
                edge = x in (OX1, OX2) or z in (OZ1, OZ2)
                bp.set(x, top2, z, W if edge else "smooth_stone")
        for x, z in ((4, 7), (8, 7), (5, 10)):
            st.ceiling_light(bp, x, top2, z)
        # staircase along the east wall, rising south (z5 y2 -> z10 y7)
        for i in range(6):
            z, y = 5 + i, 2 + i
            if y > 2:
                bp.fill(10, 2, z, 10, y - 1, z, W)
            bp.set(10, y, z, "spruce_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]")
        for z in range(5, 10):
            bp.set(10, top1, z, "air")
            put(bp, 9, top1 + 1, z, st.railing)
        # drafting room
        y = top1 + 1
        for x in range(3, 9):
            bp.set(x, y, 11, "bookshelf")
        bp.set(3, y, 5, "cartography_table")
        bp.set(4, y, 5, "lectern[facing=south,has_book=false,powered=false]")
        for x in (5, 6, 7):
            put(bp, x, y, 8, st.counter if st.early else do_slab(T, "top"))   # drawing tables
            bp.set(x, y, 9, "spruce_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]")

    # ------------------------------------------------------------ L2: workshop shed
    if L >= 2:
        roof_y = 6
        for x in range(OX1, OX2 + 1):
            for z in range(SHED_Z1, SHED_Z2 + 1):
                bp.set(x, roof_y, z, W if z == SHED_Z2 or x in (OX1, OX2) else DECK)
        for x, z in ((OX1, SHED_Z2), (OX2, SHED_Z2), (OX1, SHED_Z1), (OX2, SHED_Z1), (6, SHED_Z2)):
            bp.fill(x, 2, z, x, roof_y - 1, z, T)
        for x in range(OX1 + 1, OX2):                 # back wall of the shed (timber slats)
            bp.fill(x, 2, SHED_Z2, x, roof_y - 1, SHED_Z2, WOOD if x % 2 else DECK)
        ws = [((3, 17), "stonecutter[facing=north]"), ((4, 17), "grindstone[face=floor,facing=north]"),
              ((5, 17), "anvil[facing=east]"), ((7, 17), "smithing_table"), ((8, 17), "crafting_table"),
              ((9, 17), "barrel[facing=up,open=false]"), ((10, 17), "barrel[facing=up,open=false]")]
        for (x, z), s in ws:
            bp.set(x, 2, z, s)
        for x in (4, 8):
            st.ceiling_light(bp, x, roof_y, 15)
        # material pallets in the yard
        for x, z, mat in ((14, 5, "stripped_spruce_log[axis=x]"), (14, 11, "bricks")):
            bp.fill(x, 2, z, x + 1, 3, z + 1, mat)

    # ------------------------------------------------------------ yard: fence / hoarding, racks, canopy
    gate = range(15, 22)
    for x in range(YX1, YX2 + 1):
        for z in range(YZ1, YZ2 + 1):
            on_line = (x == YX2 or z in (YZ1, YZ2)) and not (z == YZ1 and x in gate)
            if not on_line:
                continue
            if st.early:
                bp.set(x, 2, z, "spruce_fence[east=false,north=false,south=false,waterlogged=false,west=false]")
            else:
                bp.set(x, 2, z, W)
                put(bp, x, 3, z, st.railing)
    for z_row, height, xs in RACKS[L]:
        for x in xs:
            for y in range(2, 2 + height):
                rack(bp, x, y, z_row, "north")
    if L >= 3:  # canopy over the racks
        for x in range(YX1, YX2):
            for z in range(14, YZ2 + 1):
                bp.set(x, 6, z, W if z == 14 or x == YX1 else DECK)
        for x in (YX1, YX2 - 1):
            bp.fill(x, 2, 14, x, 5, 14, T)
        for x in (15, 19):
            st.ceiling_light(bp, x, 6, 16)

    # ------------------------------------------------------------ tower crane
    ct = CRANE_TOP[L]
    if ct:
        mx, mz = MAST
        for y in range(2, ct + 1):
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    corner = abs(dx) == 1 and abs(dz) == 1
                    brace = (y - 2) % 4 == 0 and not (dx == 0 and dz == 1)
                    if (dx, dz) == (0, 0) or corner or brace:
                        bp.set(mx + dx, y, mz + dz, YELLOW)
            bp.set(mx, y, mz + 1, "ladder[facing=south,waterlogged=false]")   # climb inside the mast
        bp.fill(mx - 1, 1, mz - 1, mx + 1, 1, mz + 1, "smooth_stone")        # concrete base
        # slewing platform, cab, jib and counter-jib
        bp.fill(mx - 1, ct + 1, mz - 1, mx + 1, ct + 1, mz + 1, YELLOW)
        bp.set(mx, ct + 1, mz + 1, "ladder[facing=south,waterlogged=false]")
        for x in range(4, mx - 1):                                            # jib (west)
            bp.set(x, ct + 1, mz, YELLOW)
            bp.set(x, ct + 2, mz, "iron_bars[east=false,north=false,south=false,waterlogged=false,west=false]" if x % 2 else YELLOW)
        for x in range(mx + 2, SX):                                           # counter-jib (east)
            bp.set(x, ct + 1, mz, YELLOW)
        bp.fill(SX - 2, ct + 2, mz, SX - 1, ct + 3, mz, "gray_concrete")      # counterweight
        for y in range(ct + 2, ct + 6):                                       # apex
            bp.set(mx, y, mz, YELLOW)
        bp.set(mx, ct + 6, mz, "lantern[hanging=false,waterlogged=false]")    # aircraft warning light
        # cab on the south side of the platform: glass with a seat
        for y in (ct + 2, ct + 3):
            bp.set(mx - 1, y, mz + 1, G)
            bp.set(mx + 1, y, mz + 1, G)
        bp.fill(mx - 1, ct + 1, mz + 2, mx + 1, ct + 1, mz + 2, YELLOW)     # cab floor
        bp.fill(mx - 1, ct + 2, mz + 2, mx + 1, ct + 3, mz + 2, G)          # cab windscreen
        bp.fill(mx - 1, ct + 4, mz + 1, mx + 1, ct + 4, mz + 2, YELLOW)     # cab roof
        # hook over the yard
        hook_x = 15
        for y in range(9 if L >= 5 else ct - 3, ct + 1):
            bp.set(hook_x, y, mz, "chain[axis=y,waterlogged=false]")
        if L >= 5:
            bp.fill(hook_x - 1, 7, mz - 1, hook_x + 1, 8, mz + 1, "stripped_spruce_log[axis=x]")  # load
            bp.set(mx, ct + 2, mz - 1, "sea_lantern")                              # cab light

    # ------------------------------------------------------------ L4: roof terrace, cutter, bed, trees
    if L >= 4:
        for x in range(OX1, OX2 + 1):
            for z in range(OZ1, OZ2 + 1):
                if x in (OX1, OX2) or z in (OZ1, OZ2):
                    put(bp, x, top2 + 1, z, st.railing)
        solar_panels(bp, 3, top2 + 1, 9, 10, 11)
        for y in range(top1 + 1, top2 + 1):
            bp.set(3, y, 6, "ladder[facing=east,waterlogged=false]")            # roof ladder
        bp.set(6, 2, 17, "domum_ornamentum:architectscutter[facing=north]")
        bp.set(3, top1 + 1, 8, "light_gray_bed[facing=south,occupied=false,part=foot]")
        bp.set(3, top1 + 1, 9, "light_gray_bed[facing=south,occupied=false,part=head]")
        tree(bp, 1, 2, 1, h=3)
        street_lamp(bp, 12, 2, 1)
        street_lamp(bp, 23, 2, 1)

    # ------------------------------------------------------------ L5: louvres, planters, ender chest
    if L >= 5:
        for z in range(OZ1 + 1, OZ2 + 1, 2):
            bp.fill(OX1 - 1, 2, z, OX1 - 1, top2 - 1, z, WOOD)
        for x in (5, 8):
            planter(bp, x, top2 + 1, 6)
        bp.set(9, top1 + 1, 11, "ender_chest[facing=north,waterlogged=false]")

    # ------------------------------------------------------------ hut, reception, function
    sit = []
    hut = (4, 2, 8)
    for z in (7, 8, 9):
        put(bp, 5, 2, z, st.counter)
    bp.set(3, 2, 11, "crafting_table")
    bp.set(7, 2, 11, "cartography_table")
    bp.set(8, 2, 11, "barrel[facing=up,open=false]")
    bp.set(9, 2, 11, "barrel[facing=up,open=false]")
    if L >= 2:
        bp.set(6, 2, 11, "lectern[facing=north,has_book=false,powered=false]")
        for x in (8, 9):
            bp.set(x, 2, 5, "spruce_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]")
            sit.append((x, 2, 5))

    connect_panes(bp)
    tags = {hut: ["neoterra"], (0, 1, 0): ["groundlevel"]}
    for p in sit:
        tags.setdefault(p, []).append("sit")
    path = f"fundamentals/builder{L}.blueprint"
    bp.set(*hut, "minecolonies:blockhutbuilder[facing=east]", hut_te(path, (SX, SY, SZ), hut, tags))
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
