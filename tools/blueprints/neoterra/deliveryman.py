"""
Neoterra Courier's Hut ("Logistics Hub"), levels 1-5
(MineColonies hut: minecolonies:blockhutdeliveryman; files deliveryman1-5 like the official packs).

Style: realistic near-future parcel depot: white concrete and glass hall with a wide loading
door, timber mullions and louvres, charcoal trim, green roof, solar panels, rooftop drone pad.

Same 23 x 22 x 21 footprint every level:

  L1  Depot Hall        ground-floor hall with a 7-wide loading door: hut + reception counter,
                        parcel lockers (barrels), crafting & cartography tables, roof railing.
  L2  Loading Canopy    timber canopy on charcoal columns over the forecourt, loading-bay
                        markings, green roof with solar panels, lockers grow to 21 + 10 barrels,
                        lectern, waiting bench.
  L3  Dispatch Office   upper floor (tinted glass, timber mullions) reached by a staircase
                        through a double-height void; front roof terrace with planters.
                        Office: desks, bookshelves, lectern, cartography, more lockers.
  L4  Drone Port        roof drone pad, solar array, roof railing + ladder, street trees and
                        lamps, bed (respawn) in the office.
  L5  Landmark          full-height timber louvres on the side and back facades, terrace
                        trees, antenna mast, ender chest.

Coordinates: x 0..22, z 0..20 (front = north = z 0), y 0 foundation, y 1 ground.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    Blueprint, Style, put, hut_te, connect_panes, tree, planter, street_lamp, solar_panels,
    do_slab,
)

SX, SY, SZ = 23, 22, 21
HX1, HX2, HZ1, HZ2 = 2, 20, 5, 18       # hall footprint
UZ1 = 11                                # upper floor starts here (front terrace is z5..10)
GROUND_TOP = 8                          # slab between ground floor and upper floor/terrace
UPPER_TOP = 14                          # roof of the upper floor
BARREL = "barrel[facing=east,open=false]"


def build(level: int) -> Blueprint:
    L = level
    st = Style(L)
    bp = Blueprint(SX, SY, SZ, f"deliveryman{L}.blueprint")
    W, G, T, WOOD, DECK = st.WHITE, st.GLASS, st.TRIM, st.WOOD, st.DECK
    mullion = W if st.early else WOOD
    band = T if st.early else DECK

    # ------------------------------------------------------------ ground
    bp.fill(0, 0, 0, SX - 1, 0, SZ - 1, "structurize:blocksolidsubstitution")
    for x in range(SX):
        for z in range(SZ):
            outside_hall = not (HX1 <= x <= HX2 and HZ1 <= z <= HZ2)
            if z <= 4:                                          # forecourt
                if L >= 2 and 7 <= x <= 15:
                    bp.set(x, 1, z, W if x in (7, 15) else st.LIGHTGRAY)   # loading bay
                else:
                    bp.set(x, 1, z, "smooth_stone" if (x + z) % 2 else "polished_andesite")
            elif outside_hall:
                bp.set(x, 1, z, "grass_block[snowy=false]")
            else:
                bp.set(x, 1, z, st.floor(x, z))

    # ------------------------------------------------------------ ground-floor walls
    for x in range(HX1, HX2 + 1):
        for y in range(2, GROUND_TOP):
            # front facade (z5): loading door + pedestrian entrance
            if 8 <= x <= 14 and y <= 5:
                s = "air"
            elif x in (4, 5) and y <= 4:
                s = "air"
            elif y == 7:
                s = band
            elif 7 <= x <= 15 and y == 6:
                s = T                                            # door lintel
            elif x in (HX1, HX2) or (x - HX1) % 3 == 0:
                s = mullion
            else:
                s = G
            bp.set(x, y, HZ1, s)
            # back facade (z18): solid with a window strip
            if st.early:
                back = G if (y in (4, 5) and 3 < x < 19 and (x - HX1) % 3) else W
            else:
                back = band if y == 7 else (W if y == 2 or x in (HX1, HX2) else (WOOD if (x - HX1) % 3 == 0 else G))
            bp.set(x, y, HZ2, back)
    for z in range(HZ1 + 1, HZ2):
        for x in (HX1, HX2):
            for y in range(2, GROUND_TOP):
                if y == 7:
                    s = band
                elif y == 2:
                    s = W
                elif (z - HZ1) % 3 == 0:
                    s = mullion
                else:
                    s = G if 3 <= y <= 6 else W
                bp.set(x, y, z, s)

    # ------------------------------------------------------------ slab / roof at y8
    for x in range(HX1, HX2 + 1):
        for z in range(HZ1, HZ2 + 1):
            edge = x in (HX1, HX2) or z in (HZ1, HZ2)
            if edge:
                s = W
            elif L >= 3 and z < UZ1:
                s = DECK                                         # roof terrace decking
            elif L >= 3:
                s = st.floor(x, z)                               # upper-floor floor
            elif L == 2 and 4 <= x <= 18 and 7 <= z <= 16:
                s = "grass_block[snowy=false]"                   # green roof
            else:
                s = "smooth_stone"
            bp.set(x, GROUND_TOP, z, s)
    for x in range(5, 18, 4):                                    # ground-floor ceiling lights
        for z in (7, 11, 15):
            st.ceiling_light(bp, x, GROUND_TOP, z)

    if L <= 2:  # roof railing (flat roof, no upper floor yet)
        for x in range(HX1, HX2 + 1):
            for z in range(HZ1, HZ2 + 1):
                if x in (HX1, HX2) or z in (HZ1, HZ2):
                    put(bp, x, GROUND_TOP + 1, z, st.railing)
    if L == 2:
        solar_panels(bp, 12, GROUND_TOP + 1, 12, 17, 16)
        bp.fill(12, GROUND_TOP, 12, 17, GROUND_TOP, 16, "smooth_stone")
        for x in range(4, 11, 2):
            for z in range(8, 16, 3):
                bp.set(x, GROUND_TOP + 1, z, "short_grass")

    # ------------------------------------------------------------ L2: loading canopy
    if L >= 2:
        for x in range(6, 17):
            for z in range(1, HZ1):
                bp.set(x, GROUND_TOP, z, W if z == 1 or x in (6, 16) else DECK)
        for x in (6, 16):
            bp.fill(x, 2, 1, x, GROUND_TOP - 1, 1, T)
        for x in (9, 13):
            st.ceiling_light(bp, x, GROUND_TOP, 3)

    # ------------------------------------------------------------ L3: upper floor + stairs
    if L >= 3:
        for x in range(HX1, HX2 + 1):
            for z in range(UZ1, HZ2 + 1):
                if not (x in (HX1, HX2) or z in (UZ1, HZ2)):
                    continue
                for y in range(GROUND_TOP + 1, UPPER_TOP):
                    if z == UZ1 and 10 <= x <= 12 and y <= 11:
                        s = "air"                                 # door to the terrace
                    elif y == UPPER_TOP - 1:
                        s = W
                    elif z == HZ2 and x in (HX1, HX2):
                        s = W
                    elif (x - HX1) % 3 == 0 if z in (UZ1, HZ2) else (z - UZ1) % 3 == 0:
                        s = WOOD
                    else:
                        s = G
                    bp.set(x, y, z, s)
        for x in range(HX1, HX2 + 1):
            for z in range(UZ1, HZ2 + 1):
                edge = x in (HX1, HX2) or z in (UZ1, HZ2)
                bp.set(x, UPPER_TOP, z, W if edge else "smooth_stone")
        for x in (5, 10, 15):
            for z in (13, 16):
                st.ceiling_light(bp, x, UPPER_TOP, z)
        # terrace railing along the open edges
        for x in range(HX1, HX2 + 1):
            put(bp, x, GROUND_TOP + 1, HZ1, st.railing)
        for z in range(HZ1, UZ1):
            put(bp, HX1, GROUND_TOP + 1, z, st.railing)
            put(bp, HX2, GROUND_TOP + 1, z, st.railing)
        # staircase (2 wide) along the east side through a double-height void
        for i in range(7):
            z, y = 8 + i, 2 + i
            for x in (18, 19):
                if y > 2:
                    bp.fill(x, 2, z, x, y - 1, z, W)
                bp.set(x, y, z, "spruce_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]")
        for x in (18, 19):
            for z in range(7, 14):
                bp.set(x, GROUND_TOP, z, "air")
        for z in range(7, 14):
            if z != UZ1:
                put(bp, 17, GROUND_TOP + 1, z, st.railing)        # guard rail around the void
        for x in (18, 19):
            put(bp, x, GROUND_TOP + 1, 6, st.railing)
        # terrace planters + benches
        for x in (4, 8, 14):
            planter(bp, x, GROUND_TOP + 1, HZ1 + 1)
        for x in (5, 6, 7):
            bp.set(x, GROUND_TOP + 1, 9, "spruce_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]")

    # ------------------------------------------------------------ L4: drone port
    if L >= 4:
        top = UPPER_TOP
        for x in range(HX1, HX2 + 1):
            for z in range(UZ1, HZ2 + 1):
                if x in (HX1, HX2) or z in (UZ1, HZ2):
                    put(bp, x, top + 1, z, st.railing)
        # drone pad with an H marking
        for x in range(12, 19):
            for z in range(12, 18):
                h = (x in (13, 17) and 13 <= z <= 16) or (z == 14 and 13 <= x <= 17)
                bp.set(x, top, z, W if h else T)
        for x, z in ((12, 12), (18, 12), (12, 17), (18, 17)):
            bp.set(x, top, z, "sea_lantern")
        solar_panels(bp, 4, top + 1, 12, 9, 15)
        # ladder to the roof
        for y in range(GROUND_TOP + 1, top + 1):
            bp.set(3, y, 17, "ladder[facing=east,waterlogged=false]")
        # street trees + lamps on the forecourt
        tree(bp, 1, 2, 1, h=3)
        tree(bp, 21, 2, 1, h=3)
        street_lamp(bp, 1, 2, 4)
        street_lamp(bp, 21, 2, 4)

    # ------------------------------------------------------------ L5: louvres, mast, terrace trees
    if L >= 5:
        for z in range(HZ1 + 1, HZ2 + 1, 2):
            for x in (HX1 - 1, HX2 + 1):
                bp.fill(x, 2, z, x, UPPER_TOP - 1, z, WOOD)
        for x in range(HX1 + 1, HX2, 2):
            bp.fill(x, 2, HZ2 + 1, x, UPPER_TOP - 1, HZ2 + 1, WOOD)
        bp.set(19, UPPER_TOP + 1, 17, T)
        for y in range(UPPER_TOP + 2, SY - 1):
            bp.set(19, y, 17, "chain[axis=y,waterlogged=false]")
        bp.set(19, SY - 1, 17, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        for x in (4, 14):
            bp.set(x, GROUND_TOP + 2, HZ1 + 1, "air")
            tree(bp, x, GROUND_TOP + 2, HZ1 + 1, h=2)

    # ------------------------------------------------------------ interior & function
    sit = []
    hut = (6, 2, 10)
    for x in range(4, 9):
        put(bp, x, 2, 9, st.counter)                             # reception counter
    put(bp, 4, 2, 10, st.counter)
    put(bp, 8, 2, 10, st.counter)
    lockers_z = range(14, 18) if L == 1 else range(11, 18)
    lockers_y = (2, 3) if L == 1 else (2, 3, 4)
    for z in lockers_z:                                          # parcel lockers on the west wall
        for y in lockers_y:
            bp.set(3, y, z, BARREL)
    bp.set(9, 2, 17, "crafting_table")
    bp.set(10, 2, 17, "cartography_table")
    if L >= 2:
        bp.set(11, 2, 17, "lectern[facing=north,has_book=false,powered=false]")
        for x in range(12, 17):
            for y in (2, 3):
                bp.set(x, y, 17, "barrel[facing=north,open=false]")
        for x in (14, 15, 16):
            bp.set(x, 2, 6, "spruce_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]")
            sit.append((x, 2, 6))
    if L >= 3:  # dispatch office upstairs
        y = GROUND_TOP + 1
        for x in range(5, 10):
            put(bp, x, y, 14, st.counter if st.early else do_slab(T, "top"))                 # desks
        for x in (5, 7, 9):
            bp.set(x, y, 13, "spruce_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]")
            sit.append((x, y, 13))
        for x in range(4, 10):
            bp.set(x, y, 17, "bookshelf")
            bp.set(x, y + 1, 17, "bookshelf")
        bp.set(11, y, 17, "lectern[facing=north,has_book=false,powered=false]")
        bp.set(12, y, 17, "cartography_table")
        for z in range(12, 17):
            for yy in (y, y + 1):
                bp.set(3, yy, z, BARREL)
    if L >= 4:
        bp.set(14, GROUND_TOP + 1, 17, "light_gray_bed[facing=east,occupied=false,part=foot]")
        bp.set(15, GROUND_TOP + 1, 17, "light_gray_bed[facing=east,occupied=false,part=head]")
    if L >= 5:
        bp.set(13, GROUND_TOP + 1, 17, "ender_chest[facing=north,waterlogged=false]")

    connect_panes(bp)

    # ------------------------------------------------------------ hut block
    tags = {hut: ["neoterra"], (0, 1, 0): ["groundlevel"]}
    for p in sit:
        tags.setdefault(p, []).append("sit")
    path = f"craftsmanship/storage/deliveryman{L}.blueprint"
    bp.set(*hut, "minecolonies:blockhutdeliveryman[facing=north]", hut_te(path, (SX, SY, SZ), hut, tags))
    bp.primary_offset = hut
    bp.architects = ["Neoterra"]
    return bp


if __name__ == "__main__":
    out_dir = Path(sys.argv[1])
    out_dir.mkdir(parents=True, exist_ok=True)
    for lvl in range(1, 6):
        b = build(lvl)
        b.save(out_dir / f"deliveryman{lvl}.blueprint")
        n = sum(1 for *_, s in b.blocks() if s not in ("minecraft:air", "structurize:blocksolidsubstitution"))
        print(f"deliveryman{lvl}: {n} blocks")
