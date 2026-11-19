"""
Neoterra residences (MineColonies hut: minecolonies:blockhutcitizen), three variants with
levels 1-5. A residence of level N has N beds, like the official packs.

  cottage    single-family home with a cantilevered roof, glass front and garden.
             L1 house (1 bed) -> L2 bedroom wing -> L3 glass loft + roof terrace + hedges ->
             L4 pool, vegetable garden, premium upgrade -> L5 roof garden, glowing loft, trees.
  apartment  apartment block that grows one storey per level (one flat + bed per storey),
             stair core, balconies from L3, roof terrace / roof garden.
  house      regular two-storey family house with a sloping roof and a garage.
             L1 house (1 bed) -> L2 garage workshop, porch, 2nd bed -> L3 back deck, pergola,
             3rd bed -> L4 guest room, garage roof terrace, hot tub -> L5 attic loft bed.
  quadplex   row of four townhouses with cantilevered glass bay windows; one townhouse per
             level (L1-L4), and a glass penthouse on the roof at L5 (5th bed).

Levels 1-3 use the cheap palette, 4-5 the premium one (common.CHEAP_UNTIL).
Front = north (z 0). y 0 foundation, y 1 ground.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    Blueprint, Style, put, hut_te, connect_panes, tree, planter, street_lamp,
    do_slab, bed, door, chair,
)


def finish(bp, kind, level, hut, sit, size):
    connect_panes(bp)
    tags = {hut: ["neoterra"], (0, 1, 0): ["groundlevel"]}
    for p in sit:
        tags.setdefault(p, []).append("sit")
    path = f"fundamentals/{kind}{level}.blueprint"
    bp.set(*hut, "minecolonies:blockhutcitizen[facing=north]", hut_te(path, size, hut, tags))
    bp.primary_offset = hut
    bp.architects = ["Neoterra"]
    return bp


def ground(bp, fn):
    bp.fill(0, 0, 0, bp.sx - 1, 0, bp.sz - 1, "structurize:blocksolidsubstitution")
    for x in range(bp.sx):
        for z in range(bp.sz):
            bp.set(x, 1, z, fn(x, z))


def rect_edge(x, z, x1, x2, z1, z2):
    return x in (x1, x2) or z in (z1, z2)


# ============================================================================ cottage
def build_cottage(level: int) -> Blueprint:
    L, st = level, Style(level)
    SX, SY, SZ = 19, 16, 19
    bp = Blueprint(SX, SY, SZ, f"cottage{L}.blueprint")
    W, G, T, D = st.WHITE, st.GLASS, st.TRIM, st.DECK
    glow, band = st.GLOW, st.band
    sit = []
    MX1, MX2, MZ1, MZ2 = 4, 14, 5, 12        # main house
    ROOF = 6

    def gfn(x, z):
        if 8 <= x <= 10 and z <= MZ1:
            return W if x in (8, 10) else "smooth_stone"            # front path
        return "grass_block[snowy=false]"
    ground(bp, gfn)

    # main house walls
    for x in range(MX1, MX2 + 1):
        for z in range(MZ1, MZ2 + 1):
            if not rect_edge(x, z, MX1, MX2, MZ1, MZ2):
                bp.set(x, 1, z, st.floor(x, z))
                continue
            for y in range(2, ROOF):
                if y == ROOF - 1:
                    s = W
                elif z == MZ1 and MX1 < x < MX2:
                    s = G                                            # glass front
                elif x in (MX1, MX2) and 7 <= z <= 10 and y in (3, 4):
                    s = G
                elif z == MZ2 and 10 <= x <= 12 and y in (3, 4):
                    s = G
                else:
                    s = W
                bp.set(x, y, z, s)
    door(bp, 9, 2, MZ1, "south", "birch" if st.early else "waxed_copper")
    # cantilevered flat roof with an accent fascia
    for x in range(MX1 - 1, MX2 + 2):
        for z in range(MZ1 - 1, MZ2 + 2):
            edge = rect_edge(x, z, MX1 - 1, MX2 + 1, MZ1 - 1, MZ2 + 1)
            bp.set(x, ROOF, z, band if edge else ("smooth_stone" if L < 3 else st.floor(x, z)))
    for x, z in ((6, 7), (10, 9), (7, 10)):
        st.ceiling_light(bp, x, ROOF, z)

    # L1 interior: hut, kitchen, table, bed
    hut = (5, 2, 7)
    put(bp, 5, 2, 8, st.counter)
    bp.set(5, 2, 11, "crafting_table")
    bp.set(6, 2, 11, "furnace[facing=north,lit=false]")
    bp.set(8, 2, 11, "smoker[facing=north,lit=false]")      # x7 stays free: doorway to the wing
    bp.set(9, 2, 11, "barrel[facing=up,open=false]")
    put(bp, 9, 2, 8, st.counter)                                     # table
    chair(bp, 8, 2, 8, st.SEAT, "west", sit)
    chair(bp, 10, 2, 8, st.SEAT, "east", sit)
    bed(bp, 12, 2, 10, "south")

    # L2: bedroom wing behind the house
    WX1, WX2, WZ1, WZ2 = 4, 10, 12, 17
    if L >= 2:
        for x in range(WX1, WX2 + 1):
            for z in range(WZ1, WZ2 + 1):
                if not rect_edge(x, z, WX1, WX2, WZ1, WZ2):
                    bp.set(x, 1, z, st.floor(x, z))
                    continue
                if z == WZ1:
                    continue                                         # shared with the main house
                for y in range(2, ROOF):
                    s = G if (y in (3, 4) and (x == WX1 or z == WZ2) and (x + z) % 3) else W
                    bp.set(x, y, z, W if y == ROOF - 1 else s)
        for y in (2, 3):
            bp.set(7, y, MZ2, "air")                                  # doorway into the wing
        for x in range(WX1 - 1, WX2 + 2):
            for z in range(WZ1 + 1, WZ2 + 2):
                edge = x in (WX1 - 1, WX2 + 1) or z == WZ2 + 1
                bp.set(x, ROOF, z, band if edge else "smooth_stone")
        st.ceiling_light(bp, 7, ROOF, 15)
        bed(bp, 9, 2, 15, "south")
        bp.set(5, 2, 16, "barrel[facing=up,open=false]")

    # L3: glass loft on the roof, roof terrace, hedges
    LX1, LX2, LZ1, LZ2, LTOP = 6, 14, 5, 11, 11
    if L >= 3:
        for x in range(LX1, LX2 + 1):
            for z in range(LZ1, LZ2 + 1):
                if not rect_edge(x, z, LX1, LX2, LZ1, LZ2):
                    continue
                for y in range(ROOF + 1, LTOP):
                    if y == LTOP - 1:
                        s = band
                    elif z == LZ1 or (x == LX2 and y < LTOP - 1):
                        s = G
                    elif x == LX1 and z == 8 and y <= ROOF + 2:
                        s = "air"                                    # door to the terrace
                    else:
                        s = W if (x + z) % 4 else G
                    bp.set(x, y, z, s)
        for x in range(LX1, LX2 + 1):
            for z in range(LZ1, LZ2 + 1):
                bp.set(x, LTOP, z, (glow or W) if rect_edge(x, z, LX1, LX2, LZ1, LZ2) else "smooth_stone")
        st.ceiling_light(bp, 10, LTOP, 8)
        # stairs up (x13, rising south z6 -> z10)
        for i in range(5):
            z, y = 6 + i, 2 + i
            if y > 2:
                bp.fill(13, 2, z, 13, y - 1, z, W)
            bp.set(13, y, z, f"{st.SEAT}[facing=south,half=bottom,shape=straight,waterlogged=false]")
        for z in range(6, 10):
            bp.set(13, ROOF, z, "air")
            put(bp, 12, ROOF + 1, z, st.railing)
        bed(bp, 8, ROOF + 1, 9, "south")
        bp.set(7, ROOF + 1, 6, "bookshelf")
        bp.set(8, ROOF + 1, 6, "lectern[facing=south,has_book=false,powered=false]")
        # roof terrace railing (outside the loft) + hedges along the plot front
        for x in range(MX1 - 1, MX2 + 2):
            for z in range(MZ1 - 1, MZ2 + 2):
                if rect_edge(x, z, MX1 - 1, MX2 + 1, MZ1 - 1, MZ2 + 1) and not (LX1 <= x <= LX2 and LZ1 <= z <= LZ2):
                    put(bp, x, ROOF + 1, z, st.railing)
        for x in range(SX):
            if not 8 <= x <= 10:
                bp.set(x, 2, 0, st.LEAVES)

    # L4: pool, vegetable garden, 4th bed
    if L >= 4:
        for x in range(11, 18):
            for z in range(13, 18):
                edge = rect_edge(x, z, 11, 17, 13, 17)
                bp.set(x, 1, z, W if edge else "water[level=0]")
                if not edge:
                    bp.set(x, 0, z, "sea_lantern" if (x + z) % 3 == 0 else "smooth_stone")
        for x in range(12, 18):
            for z in range(1, 4):
                if (x, z) == (14, 2):
                    bp.set(x, 1, z, "water[level=0]")
                else:
                    bp.set(x, 1, z, "farmland[moisture=7]")
                    bp.set(x, 2, z, "carrots[age=7]" if x % 2 else "potatoes[age=7]")
        bed(bp, 11, ROOF + 1, 6, "south")                            # keeps the stair landing (x11-12, z10) clear
        street_lamp(bp, 7, 2, 1, premium=True)
        street_lamp(bp, 11, 2, 1, premium=True)

    # L5: 5th bed, roof garden on the wing, glowing loft frame, trees
    if L >= 5:
        bed(bp, 5, 2, 15, "south")
        for x in range(WX1, WX2 + 1):
            for z in range(WZ1 + 1, WZ2 + 1):
                bp.set(x, ROOF, z, "grass_block[snowy=false]")
                if (x + z) % 3 == 0:
                    bp.set(x, ROOF + 1, z, "flowering_azalea")
        for x, z in ((LX1, LZ1), (LX2, LZ1), (LX1, LZ2), (LX2, LZ2)):
            bp.fill(x, ROOF + 1, z, x, LTOP - 1, z, "sea_lantern")
        bp.set(12, ROOF + 1, 11, "jukebox[has_record=false]")
    if L >= 2:
        tree(bp, 2, 2, 3, h=3)
        tree(bp, 16, 2, 9, h=4)
    return finish(bp, "cottage", L, hut, sit, (SX, SY, SZ))


# ============================================================================ apartment
AX1, AX2, AZ1, AZ2 = 2, 14, 4, 15            # building shell
STOREY = 5


def build_apartment(level: int) -> Blueprint:
    L, st = level, Style(level)
    SX, SY, SZ = 17, 34, 19
    bp = Blueprint(SX, SY, SZ, f"apartment{L}.blueprint")
    W, G, T, D = st.WHITE, st.GLASS, st.TRIM, st.DECK
    glow, band = st.GLOW, st.band
    sit = []
    floors = [1 + STOREY * i for i in range(L)]
    roof = 1 + STOREY * L

    def gfn(x, z):
        if 9 <= x <= 11 and z < AZ1:
            return W if x in (9, 11) else "smooth_stone"
        return "grass_block[snowy=false]"
    ground(bp, gfn)

    for i, F in enumerate(floors):
        # slab (ground floor uses the plaza level)
        for x in range(AX1, AX2 + 1):
            for z in range(AZ1, AZ2 + 1):
                edge = rect_edge(x, z, AX1, AX2, AZ1, AZ2)
                if i == 0:
                    if not edge:
                        bp.set(x, 1, z, st.floor(x, z))
                else:
                    bp.set(x, F, z, band if edge else st.floor(x, z))
        # walls
        for x in range(AX1, AX2 + 1):
            for z in range(AZ1, AZ2 + 1):
                if not rect_edge(x, z, AX1, AX2, AZ1, AZ2):
                    continue
                for y in range(F + 1, F + STOREY):
                    corner = x in (AX1, AX2) and z in (AZ1, AZ2)
                    if corner:
                        s = W
                    elif z == AZ1:
                        s = st.WOOD if (x - AX1) % 3 == 0 else G       # glazed front
                    elif y in (F + 2, F + 3) and (z - AZ1) % 3 and z != AZ2:
                        s = G
                    elif z == AZ2 and y in (F + 2, F + 3) and 4 <= x <= 10 and x % 3:
                        s = G
                    else:
                        s = W
                    bp.set(x, y, z, s)
        # core partition (x11, z4..12 + z12) with two doorways per floor
        for y in range(F + 1, F + STOREY):
            for z in range(AZ1 + 1, 13):
                bp.set(11, y, z, W)
            for x in (12, 13):
                bp.set(x, y, 12, W)
        for z in (5, 11):
            for y in (F + 1, F + 2):
                bp.set(11, y, z, "air")
        # flat furniture
        y = F + 1
        bed(bp, 4, y, 13, "south")
        bp.set(6, y, 14, "furnace[facing=north,lit=false]")
        bp.set(7, y, 14, "smoker[facing=north,lit=false]")
        bp.set(8, y, 14, "crafting_table")
        bp.set(9, y, 14, "barrel[facing=up,open=false]")
        put(bp, 5, y, 10, st.counter)                                  # dining table
        chair(bp, 4, y, 10, st.SEAT, "west", sit)
        chair(bp, 6, y, 10, st.SEAT, "east", sit)
        for x in (7, 8):
            chair(bp, x, y, 7, st.SEAT, "south", sit)                  # sofa facing the window
        for x, z in ((5, 7), (8, 11), (5, 13)):
            st.ceiling_light(bp, x, F + STOREY, z)
        # balconies (L3+), the ground floor gets a patio instead
        if L >= 3:
            for x in range(4, 10):
                for z in range(1, AZ1):
                    edge = x in (4, 9) or z == 1
                    if i == 0:
                        bp.set(x, 1, z, D if not (9 <= x <= 11) else bp.get(x, 1, z))
                    else:
                        bp.set(x, F, z, (glow or W) if edge else D)
                        if edge:
                            put(bp, x, F + 1, z, st.railing)
            for x in (6, 7):
                for yy in (F + 1, F + 2):
                    bp.set(x, yy, AZ1, "air")                          # balcony door
    # entrance and hut
    door(bp, 10, 2, AZ1, "south", "birch" if st.early else "waxed_copper")
    hut = (10, 2, 6)
    put(bp, 9, 2, 6, st.counter)

    # roof
    for x in range(AX1, AX2 + 1):
        for z in range(AZ1, AZ2 + 1):
            edge = rect_edge(x, z, AX1, AX2, AZ1, AZ2)
            bp.set(x, roof, z, band if edge else ("smooth_stone" if L < 4 else D))
            if edge:
                put(bp, x, roof + 1, z, st.railing)
    # stair runs, one per storey, alternating between the two core columns; each run cuts
    # its own hole in the slab above (done after every slab exists)
    for i, F in enumerate(floors):
        if i % 2 == 0:
            col, zs, facing = 13, list(range(6, 11)), "south"
        else:
            col, zs, facing = 12, list(range(10, 5, -1)), "north"
        for z in zs[:4]:
            bp.set(col, F + STOREY, z, "air")
        for k, z in enumerate(zs):
            bp.set(col, F + 1 + k, z, f"{st.SEAT}[facing={facing},half=bottom,shape=straight,waterlogged=false]")
    # guard rails around the stair core on the roof (landings at z5 / z11 stay open)
    other = 12 if (L - 1) % 2 == 0 else 13
    for z in range(6, 11):
        put(bp, other, roof + 1, z, st.railing)
        put(bp, 11, roof + 1, z, st.railing)
    for x in (12, 13):
        put(bp, x, roof + 1, 12, st.railing)
    if L >= 4:  # roof garden
        for x in range(3, 10):
            for z in (13, 14):
                bp.set(x, roof, z, "grass_block[snowy=false]")
                if x % 2:
                    bp.set(x, roof + 1, z, "flowering_azalea")
        for x in (4, 8):
            chair(bp, x, roof + 1, 9, st.SEAT, "south", sit)
    if L >= 5:
        tree(bp, 5, roof + 1, 7, h=3)
        tree(bp, 9, roof + 1, 7, h=2)
        bp.set(13, roof + 1, 14, T)
        for y in range(roof + 2, SY - 1):
            bp.set(13, y, 14, "chain[axis=y,waterlogged=false]")
        bp.set(13, SY - 1, 14, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        bp.set(3, roof + 1, 14, "ender_chest[facing=north,waterlogged=false]")
    if L >= 2:
        tree(bp, 1, 2, 1, h=3)
        tree(bp, 15, 2, 1, h=3)
    if L >= 4:
        street_lamp(bp, 8, 2, 1, premium=True)
        street_lamp(bp, 12, 2, 1, premium=True)
    return finish(bp, "apartment", L, hut, sit, (SX, SY, SZ))


# ============================================================================ quadplex
QZ1, QZ2 = 4, 15                       # front / back walls
QROOF, QMID = 11, 6


def build_quadplex(level: int) -> Blueprint:
    L, st = level, Style(level)
    SX, SY, SZ = 27, 18, 21
    bp = Blueprint(SX, SY, SZ, f"quadplex{L}.blueprint")
    W, G, T, D = st.WHITE, st.GLASS, st.TRIM, st.DECK
    glow, band = st.GLOW, st.band
    sit = []
    units = min(L, 4)

    def gfn(x, z):
        for k in range(units):
            if x == 4 + 6 * k and z < QZ1:
                return "smooth_stone"                                   # path to each front door
        return "grass_block[snowy=false]"
    ground(bp, gfn)

    for k in range(units):
        x0, x1 = 1 + 6 * k, 7 + 6 * k
        xa = x0 + 1
        # walls
        for x in range(x0, x1 + 1):
            for z in range(QZ1, QZ2 + 1):
                if not rect_edge(x, z, x0, x1, QZ1, QZ2):
                    bp.set(x, 1, z, st.floor(x, z))
                    continue
                for y in range(2, QROOF):
                    if y in (QMID, QROOF - 1):
                        s = band if z == QZ1 or y == QROOF - 1 else W
                    elif z == QZ1 and x0 < x < x1:
                        s = G if y < QMID else ("air" if x0 + 2 <= x <= x0 + 4 else G)
                    elif z == QZ2 and x0 < x < x1 and y in (3, 4, 8, 9):
                        s = G
                    else:
                        s = W
                    bp.set(x, y, z, s)
        # upper floor slab + roof
        for x in range(x0, x1 + 1):
            for z in range(QZ1, QZ2 + 1):
                if not rect_edge(x, z, x0, x1, QZ1, QZ2):
                    bp.set(x, QMID, z, st.floor(x, z))
                bp.set(x, QROOF, z, band if z in (QZ1, QZ2) else ("smooth_stone" if L < 4 else W))
        door(bp, x0 + 3, 2, QZ1, "south", "birch" if st.early else "waxed_copper")
        # cantilevered glass bay window on the upper floor
        for x in range(x0 + 1, x1):
            for z in range(1, QZ1):
                edge = x in (x0 + 1, x1 - 1) or z == 1
                bp.set(x, QMID, z, (glow or W) if edge else D)
                bp.set(x, QROOF - 1, z, band if edge else W)
                if edge:
                    for y in range(QMID + 1, QROOF - 1):
                        bp.set(x, y, z, G if not (x in (x0 + 1, x1 - 1) and z == 1) else W)
        for x in range(x0 + 1, x1):
            for z in range(1, QZ1):
                bp.set(x, QROOF, z, W)
        chair(bp, x0 + 3, QMID + 1, 2, st.SEAT, "south", sit)           # window seat
        # stairs along the west party wall (rising south z8 -> z12)
        for i in range(5):
            z, y = 8 + i, 2 + i
            if y > 2:
                bp.fill(xa, 2, z, xa, y - 1, z, W)
            bp.set(xa, y, z, f"{st.SEAT}[facing=south,half=bottom,shape=straight,waterlogged=false]")
        for z in range(8, 12):
            bp.set(xa, QMID, z, "air")
            put(bp, xa + 1, QMID + 1, z, st.railing)
        # ground floor: kitchen + dining
        bp.set(x0 + 3, 2, 14, "furnace[facing=north,lit=false]")
        bp.set(x0 + 4, 2, 14, "smoker[facing=north,lit=false]")
        bp.set(x0 + 5, 2, 14, "crafting_table")
        bp.set(xa, 2, 14, "barrel[facing=up,open=false]")
        put(bp, x0 + 4, 2, 8, st.counter)
        chair(bp, x0 + 3, 2, 8, st.SEAT, "west", sit)
        chair(bp, x0 + 5, 2, 8, st.SEAT, "east", sit)
        # upper floor: bedroom
        bed(bp, x0 + 4, QMID + 1, 13, "south")
        bp.set(x0 + 5, QMID + 1, 14, "barrel[facing=up,open=false]")
        st.ceiling_light(bp, x0 + 4, QMID, 10)
        st.ceiling_light(bp, x0 + 4, QROOF, 8)
        # gardens: tree at the back, hedge dividers
        if L >= 2:
            tree(bp, x0 + 3, 2, 18, h=3)
        if L >= 3 and k > 0:
            for z in range(QZ2 + 1, SZ - 1):
                bp.set(x0, 2, z, st.LEAVES)
    hut = (6, 2, 6)

    # L5: glass penthouse on the roof (5th bed), roof terrace, ladder from unit 2
    if L >= 5:
        PX1, PX2, PZ1, PZ2, PTOP = 8, 18, 6, 12, 16
        for x in range(1, 26):
            for z in range(QZ1, QZ2 + 1):
                if rect_edge(x, z, 1, 25, QZ1, QZ2):
                    put(bp, x, QROOF + 1, z, st.railing)
                elif not (PX1 <= x <= PX2 and PZ1 <= z <= PZ2):
                    bp.set(x, QROOF, z, D)
        for x in range(PX1, PX2 + 1):
            for z in range(PZ1, PZ2 + 1):
                if rect_edge(x, z, PX1, PX2, PZ1, PZ2):
                    for y in range(QROOF + 1, PTOP):
                        corner = x in (PX1, PX2) and z in (PZ1, PZ2)
                        s = "sea_lantern" if corner else (band if y == PTOP - 1 else G)
                        bp.set(x, y, z, s)
                bp.set(x, PTOP, z, W if rect_edge(x, z, PX1, PX2, PZ1, PZ2) else "smooth_stone")
        for y in (QROOF + 1, QROOF + 2):
            bp.set(10, y, PZ2, "air")                                   # penthouse door
        st.ceiling_light(bp, 13, PTOP, 9)
        bed(bp, 16, QROOF + 1, 8, "north")
        bp.set(17, QROOF + 1, 11, "ender_chest[facing=west,waterlogged=false]")
        bp.set(9, QROOF + 1, 7, "jukebox[has_record=false]")
        for x in (12, 13, 14):
            chair(bp, x, QROOF + 1, 11, st.SEAT, "south", sit)
        for y in range(QMID + 1, QROOF + 1):
            bp.set(9, y, 14, "ladder[facing=north,waterlogged=false]")    # unit 2 upper floor -> roof
        for x in (3, 23):
            planter(bp, x, QROOF + 1, 13)
    if L >= 4:
        for k in range(units):
            street_lamp(bp, 6 + 6 * k, 2, 0, premium=True)
    return finish(bp, "quadplex", L, hut, sit, (SX, SY, SZ))


# ============================================================================ house
def build_house(level: int) -> Blueprint:
    """Regular two-storey family house with a sloping (mono-pitch) roof, garage and gardens.

    L1 house: kitchen, living, dining, master bedroom upstairs (1 bed)
    L2 garage workshop + driveway, porch canopy, 2nd bedroom, trees
    L3 back deck + pergola, hedges, 3rd bedroom
    L4 premium; guest room downstairs (4th bed), garage roof terrace, hot tub, lamp spires
    L5 attic loft bed under the high roof (5th bed), glowing corners, ender chest, jukebox
    """
    L, st = level, Style(level)
    SX, SY, SZ = 21, 19, 21
    bp = Blueprint(SX, SY, SZ, f"house{L}.blueprint")
    W, G, T, D = st.WHITE, st.GLASS, st.TRIM, st.DECK
    glow, band = st.GLOW, st.band
    sit = []
    HX1, HX2, HZ1, HZ2 = 3, 14, 5, 14        # house shell
    MID = 6                                  # upper floor slab

    def roof_y(z):
        k = z - (HZ1 - 1)
        return 11 + k // 2, ("bottom" if k % 2 == 0 else "top")

    def gfn(x, z):
        if 8 <= x <= 10 and z < HZ1:
            return W if x in (8, 10) else "smooth_stone"                # front path
        if L >= 2 and 15 <= x <= 19 and z < 7:
            return "smooth_stone" if x in (15, 19) else "polished_andesite"   # driveway
        return "grass_block[snowy=false]"
    ground(bp, gfn)

    # walls (ground + upper floor, gables up to the sloping roof)
    for x in range(HX1, HX2 + 1):
        for z in range(HZ1, HZ2 + 1):
            if not rect_edge(x, z, HX1, HX2, HZ1, HZ2):
                bp.set(x, 1, z, st.floor(x, z))
                bp.set(x, MID, z, st.floor(x, z))
                continue
            top = roof_y(z)[0] - 1 if x in (HX1, HX2) else (10 if z == HZ1 else roof_y(z)[0] - 1)
            for y in range(2, top + 1):
                corner = x in (HX1, HX2) and z in (HZ1, HZ2)
                if y == MID:
                    s = band
                elif corner:
                    s = W
                elif z == HZ1 and y in (3, 4, 8, 9) and x not in (9,):
                    s = G if x % 4 else st.WOOD                          # big front windows
                elif x in (HX1, HX2) and y >= 11 and not st.early:
                    s = G                                                # glazed gable (premium)
                elif x in (HX1, HX2) and y in (3, 4, 8, 9) and (z - HZ1) % 3:
                    s = G
                elif z == HZ2 and y in (3, 4, 12, 13) and (x - HX1) % 3:
                    s = G                                                # back windows + clerestory
                else:
                    s = W
                bp.set(x, y, z, s)
    door(bp, 9, 2, HZ1, "south", "birch" if st.early else "waxed_copper")
    # sloping roof (1 in 2) from front to back, with overhangs
    for x in range(HX1 - 1, HX2 + 2):
        for z in range(HZ1 - 1, HZ2 + 2):
            y, half = roof_y(z)
            if st.early:
                bp.set(x, y, z, f"smooth_stone_slab[type={half},waterlogged=false]")
            else:
                put(bp, x, y, z, do_slab(W, half))
    # lights
    for x, z in ((6, 8), (11, 8), (7, 12)):
        st.ceiling_light(bp, x, MID, z)
    for x, z in ((7, 9), (11, 11)):
        y, _ = roof_y(z)
        bp.set(x, y - 1, z, "lantern[hanging=true,waterlogged=false]")

    # stairs up along the west wall (x4, rising north z12 -> z8)
    for i in range(5):
        z, y = 12 - i, 2 + i
        if y > 2:
            bp.fill(4, 2, z, 4, y - 1, z, W)
        bp.set(4, y, z, f"{st.SEAT}[facing=north,half=bottom,shape=straight,waterlogged=false]")
    for z in range(9, 13):
        bp.set(4, MID, z, "air")
        put(bp, 5, MID + 1, z, st.railing)

    # ground floor: hut, living, dining, kitchen
    hut = (12, 2, 6)
    for x in (7, 8):
        chair(bp, x, 2, 7, st.SEAT, "north", sit)                       # sofa facing the room
    put(bp, 10, 2, 10, st.counter)                                       # dining table
    chair(bp, 9, 2, 10, st.SEAT, "west", sit)
    chair(bp, 11, 2, 10, st.SEAT, "east", sit)
    bp.set(6, 2, 13, "furnace[facing=north,lit=false]")
    bp.set(7, 2, 13, "smoker[facing=north,lit=false]")
    bp.set(8, 2, 13, "crafting_table")
    bp.set(9, 2, 13, "barrel[facing=up,open=false]")
    # upper floor: bedrooms along the back wall
    bed(bp, 7, MID + 1, 12, "south")
    if L >= 2:
        bed(bp, 9, MID + 1, 12, "south")
    if L >= 3:
        bed(bp, 11, MID + 1, 12, "south")
    bp.set(13, MID + 1, 13, "barrel[facing=up,open=false]")
    put(bp, 11, MID + 1, 6, st.counter)                                 # desk at the front window
    chair(bp, 11, MID + 1, 7, st.SEAT, "south", sit)

    # L2: garage workshop + porch canopy
    GX1, GX2, GZ1, GZ2 = 15, 19, 7, 14
    if L >= 2:
        for x in range(GX1, GX2 + 1):
            for z in range(GZ1, GZ2 + 1):
                edge = rect_edge(x, z, GX1, GX2, GZ1, GZ2)
                bp.set(x, 6, z, band if edge else ("smooth_stone" if L < 4 else D))
                if not edge:
                    bp.set(x, 1, z, "polished_andesite")
                    continue
                for y in range(2, 6):
                    if z == GZ1 and GX1 < x < GX2 and y <= 4:
                        s = "air"                                        # garage door opening
                    elif z == GZ1 and GX1 < x < GX2:
                        s = T
                    elif x == GX2 and y in (3, 4) and (z - GZ1) % 3:
                        s = G
                    else:
                        s = W
                    bp.set(x, y, z, s)
        for y in (2, 3):
            bp.set(HX2, y, 10, "air")                                    # house <-> garage door
        for (x, z), s in (((19 - 1, 13), "anvil[facing=west]"), ((18, 12), "smithing_table"),
                          ((18, 11), "grindstone[face=floor,facing=west]"), ((16, 13), "crafting_table"),
                          ((17, 13), "barrel[facing=up,open=false]")):
            bp.set(x, 2, z, s)
        st.ceiling_light(bp, 17, 6, 10)
        for x in range(7, 12):                                           # porch canopy
            for z in range(2, HZ1):
                bp.set(x, MID, z, (glow or band) if z == 2 or x in (7, 11) else D)
        tree(bp, 2, 2, 2, h=3)
        tree(bp, 3, 2, 18, h=4)

    # L3: back deck with pergola, hedges
    if L >= 3:
        for x in range(4, 14):
            for z in range(HZ2 + 1, 19):
                bp.set(x, 1, z, D)
        for x in (4, 13):
            bp.fill(x, 2, 18, x, 4, 18, st.WOOD)
        for x in range(4, 14):
            bp.set(x, 5, 18, st.WOOD if x % 2 else W)
        put(bp, 8, 2, 16, st.counter)                                    # outdoor table
        chair(bp, 7, 2, 16, st.SEAT, "west", sit)
        chair(bp, 9, 2, 16, st.SEAT, "east", sit)
        for x in range(SX):
            if not (8 <= x <= 10 or 15 <= x <= 19):
                bp.set(x, 2, 0, st.LEAVES)

    # L4: guest room downstairs, garage roof terrace, hot tub, lamps
    if L >= 4:
        bed(bp, 12, 2, 12, "south")
        for x in range(GX1, GX2 + 1):
            for z in range(GZ1, GZ2 + 1):
                if rect_edge(x, z, GX1, GX2, GZ1, GZ2):
                    put(bp, x, 7, z, st.railing)
        for y in (MID + 1, MID + 2):
            bp.set(HX2, y, 9, "air")                                     # upstairs door to the terrace
        for x, z in ((16, 9), (17, 9)):
            chair(bp, x, 7, z, st.SEAT, "west" if x == 16 else "east", sit)
        for x in range(15, 19):
            for z in range(16, 20):
                edge = rect_edge(x, z, 15, 18, 16, 19)
                bp.set(x, 1, z, W if edge else "water[level=0]")
                if not edge:
                    bp.set(x, 0, z, "sea_lantern")
        street_lamp(bp, 7, 2, 0, premium=True)
        street_lamp(bp, 14, 2, 0, premium=True)

    # L5: attic loft (5th bed) under the high back of the roof, glowing roof edge
    if L >= 5:
        for x in range(5, 13):
            for z in range(10, 14):
                bp.set(x, 11, z, D)
        for x in range(5, 13):
            put(bp, x, 12, 9, st.railing)
        for y in range(MID + 1, 12):
            bp.set(13, y, 11, "ladder[facing=west,waterlogged=false]")
        bed(bp, 8, 12, 12, "south")
        bp.set(11, 12, 13, "jukebox[has_record=false]")
        bp.set(6, 12, 13, "ender_chest[facing=north,waterlogged=false]")
        for x in (HX1, HX2):                                             # glowing corner strips
            for z in (HZ1, HZ2):
                bp.fill(x, MID + 1, z, x, 10, z, "sea_lantern")
    return finish(bp, "house", L, hut, sit, (SX, SY, SZ))


BUILDERS = {"cottage": build_cottage, "house": build_house, "apartment": build_apartment,
            "quadplex": build_quadplex}

if __name__ == "__main__":
    out_dir = Path(sys.argv[1])
    out_dir.mkdir(parents=True, exist_ok=True)
    for kind, fn in BUILDERS.items():
        for lvl in range(1, 6):
            b = fn(lvl)
            b.save(out_dir / f"{kind}{lvl}.blueprint")
            beds = sum(1 for *_, s in b.blocks() if s.endswith("part=head]") or "part=head" in s)
            n = sum(1 for *_, s in b.blocks() if s not in ("minecraft:air", "structurize:blocksolidsubstitution"))
            print(f"{kind}{lvl}: {n} blocks, {beds} beds")
