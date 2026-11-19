"""
Neoterra Bunker: a four-deck, self-sustaining underground settlement with a player base (L1-5).

The bunker is a residence hut (dorm, 1-5 beds) that contains four child huts, each upgraded on
its own (same mechanism as the official barracks towers):

  bunkerkitchen1-5 (blockhutcook)      canteen       1 furnace per level, seats, `work` spots
  bunkerschool1-5  (blockhutschool)    classroom     10 seats + teacher spot, bookshelves
  bunkerclinic1-5  (blockhuthospital)  clinic        2 beds per level, furnace, brewing (L3)
  bunkerfarm1-5    (blockhutfarmer)    farm office   racks, composter; works the farm fields

Decks (5 blocks each, a glass atrium through all of them under a surface skylight):
  A  y16  living      dorm | canteen | classroom | clinic | commons lounge | stores & laundry
  B  y11  PLAYER BASE workshop (smelting array + stations) | enchanting library (30 shelves) |
                      storage vault (~200 barrels) | player suite (beds, brewing) | armory | map room
  C  y6   farm        farm hall with a scarecrow field | farm office | compost store | reservoir
  D  y1   engineering second field | generator room | water tanks | emergency stores | atrium garden

Levels: L1 decks A+B, L2 adds the farm deck, L3 the engineering deck, L4 premium palette +
skylight dome + ender chest, L5 glowing atrium + reactor core.
The ground around (and decks not built yet) is `structurize:blocksolidsubstitution`;
child rooms are `structurize:blocksubstitution` in the bunker blueprint.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

from nbtlib import tag as NBT

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit import Kit, SUBST, edge, put, rack, tree, planter, bed, street_lamp  # noqa: E402
from common import Blueprint, Style, hut_te, connect_panes  # noqa: E402

SX, SY, SZ = 41, 32, 41
X1, X2, Z1, Z2 = 2, 38, 2, 38
DECKS = {"D": 1, "C": 6, "B": 11, "A": 16}       # deck floor heights
A_TOP, SURFACE = 21, 24
C = 20                                            # atrium centre (x and z)
SOLID = "structurize:blocksolidsubstitution"

# room interiors (x1, x2, z1, z2) and their door cell in the room's wall (facing the corridors)
ROOMS_XZ = {"NW": (3, 17, 3, 13), "NE": (26, 37, 3, 13), "SW": (3, 17, 27, 37), "SE": (26, 37, 27, 37),
            "W": (3, 13, 16, 24), "E": (27, 37, 16, 24)}
DOORS = {"NW": (18, 8), "NE": (25, 6), "SW": (18, 32), "SE": (25, 32), "W": (14, 20), "E": (26, 20)}

# child huts: name -> (block, deck, room, hut local xz)
CHILDREN = {
    "bunkerkitchen": ("blockhutcook", "A", "NE", (11, 9)),
    "bunkerschool": ("blockhutschool", "A", "SW", (14, 1)),
    "bunkerclinic": ("blockhuthospital", "A", "SE", (5, 0)),
    "bunkerfarm": ("blockhutfarmer", "C", "NE", (0, 9)),
}


def decks_for(L):
    return ["A", "B"] + (["C"] if L >= 2 else []) + (["D"] if L >= 3 else [])


# ---------------------------------------------------------------------------- child rooms
def furnish(name, bp, L, ox, oy, oz, tags):
    """Furnish a child room in local coordinates; (ox, oy, oz) = world pos of local (0, 0, 0).
    Door cells kept free: kitchen/farm (0, 3), school (14, 5), clinic (0, 5)."""
    st = Style(L)

    def at(lx, lz, s, dy=0):
        put(bp, ox + lx, oy + dy, oz + lz, s)

    def tag(lx, lz, n):
        tags.setdefault((ox + lx, oy, oz + lz), []).append(n)

    def seat(lx, lz, back):
        at(lx, lz, f"{st.SEAT}[facing={back},half=bottom,shape=straight,waterlogged=false]")
        tag(lx, lz, "sit")

    if name == "bunkerkitchen":                      # 12 x 11
        for i in range(L):
            at(1 + i, 0, "furnace[facing=south,lit=false]")
            tag(1 + i, 1, "work")
        at(8, 0, "smoker[facing=south,lit=false]")
        at(9, 0, "crafting_table")
        rack(bp, ox + 0, oy, oz + 0, "south")
        for tx, tz in ((3, 5), (8, 5)) + (((3, 8),) if L >= 3 else ()):
            at(tx, tz, st.counter)
            seat(tx - 1, tz, "west")
            seat(tx + 1, tz, "east")
    elif name == "bunkerschool":                     # 15 x 11
        for lx in range(2, 13):
            at(lx, 10, "black_concrete", 1)
        tag(7, 9, "work")
        for lz in (4, 6):
            for lx in (2, 4, 9, 11, 13):
                at(lx, lz + 1, st.counter)
                seat(lx, lz, "north")                 # backrest north: faces the board
        for i in range(2 * L):
            at(0, 1 + i % 8, "bookshelf", i // 8)
    elif name == "bunkerclinic":                     # 12 x 11
        spots = [(x, 3, "north") for x in (1, 3, 7, 9, 11)] + [(x, 7, "south") for x in (1, 3, 7, 9, 11)]
        for lx, lz, f in spots[: 2 * L]:
            bed(bp, ox + lx, oy, oz + lz, f, "red")
        at(11, 5, "furnace[facing=west,lit=false]")
        at(10, 10, "barrel[facing=north,open=false]")
        if L >= 3:
            at(11, 10, "brewing_stand[has_bottle_0=false,has_bottle_1=false,has_bottle_2=false]")
    elif name == "bunkerfarm":                       # 12 x 11
        for i in range(L):
            rack(bp, ox + 1 + i, oy, oz, "south")
        at(11, 1, "composter[level=0]")
        at(11, 2, "barrel[facing=west,open=false]")
        at(8, 5, st.counter)
        seat(8, 6, "south")
    for lx, lz in ((2, 2), (9, 7)):
        if bp.get(ox + lx, oy + 3, oz + lz) == "minecraft:air":
            bp.set(ox + lx, oy + 3, oz + lz, "lantern[hanging=true,waterlogged=false]")


def room_size(room):
    x1, x2, z1, z2 = ROOMS_XZ[room]
    return x2 - x1 + 1, z2 - z1 + 1


def build_room(name, L):
    block, deck, room, (hx, hz) = CHILDREN[name]
    sx, sz = room_size(room)
    bp = Blueprint(sx, 4, sz, f"{name}{L}.blueprint")
    tags = {}
    furnish(name, bp, L, 0, 0, 0, tags)
    hut = (hx, 0, hz)
    tags.setdefault(hut, []).append("invisible")
    path = f"fundamentals/{name}{L}.blueprint"
    bp.set(*hut, f"minecolonies:{block}[facing=north]", hut_te(path, (sx, 4, sz), hut, tags))
    bp.primary_offset = hut
    bp.architects = ["Neoterra"]
    return bp


# ---------------------------------------------------------------------------- bunker
def build_bunker(L, preview_rooms=0):
    k = Kit("bunker", "fundamentals", L, (SX, SY, SZ))
    bp, W, G = k.bp, k.W, k.G
    st = k.st
    concrete = "gray_concrete" if st.early else "polished_deepslate"
    decks = decks_for(L)
    seat = k.seat

    bp.fill(0, 0, 0, SX - 1, SURFACE - 1, SZ - 1, SOLID)
    for x in range(SX):
        for z in range(SZ):
            bp.set(x, SURFACE, z, "grass_block[snowy=false]")

    def near_atrium(x, z, r):
        return math.hypot(x - C, z - C) <= r

    # ---------------------------------------------------------------- deck shells, rooms, stair core walls
    for d in decks:
        F = DECKS[d]
        for x in range(X1, X2 + 1):
            for z in range(Z1, Z2 + 1):
                e = edge(x, z, X1, X2, Z1, Z2)
                bp.set(x, F, z, concrete if e else st.floor(x, z))
                bp.set(x, F + 5, z, concrete if e else W)
                for y in range(F + 1, F + 5):
                    bp.set(x, y, z, concrete if e else "air")
        farm_deck = d in ("C", "D")
        for room, (x1, x2, z1, z2) in ROOMS_XZ.items():
            if farm_deck and room in ("NW", "W", "SW"):
                continue                                                 # west half = farm hall
            for x in range(x1 - 1, x2 + 2):
                for z in range(z1 - 1, z2 + 2):
                    if edge(x, z, x1 - 1, x2 + 1, z1 - 1, z2 + 1) and not edge(x, z, X1, X2, Z1, Z2):
                        for y in range(F + 1, F + 5):
                            bp.set(x, y, z, W if y < F + 3 else G)
            dx, dz = DOORS[room]
            for y in (F + 1, F + 2):
                bp.set(dx, y, dz, "air")
        if farm_deck:  # farm hall wall along x18 with two doors
            for z in range(Z1 + 1, Z2):
                for y in range(F + 1, F + 5):
                    bp.set(18, y, z, W if y < F + 3 else G)
            for z in (8, 32):
                for y in (F + 1, F + 2):
                    bp.set(18, y, z, "air")
        for y in range(F + 1, F + 5):                                    # stair core x23-24, z10-16
            for z in range(9, 18):
                bp.set(22, y, z, W)
                bp.set(25, y, z, W)
            for x in (23, 24):
                bp.set(x, y, 9, W)
                bp.set(x, y, 17, W)
        for z in (10, 16):
            for y in (F + 1, F + 2):
                bp.set(22, y, z, "air")
        for x in range(4, 38, 5):                                        # corridor / plaza lights
            if not near_atrium(x, 20, 3.5):
                st.ceiling_light(bp, x, F + 5, 20)
        for z in range(15, 38, 5):
            if not near_atrium(20, z, 3.5):
                st.ceiling_light(bp, 20, F + 5, z)

    # ---------------------------------------------------------------- atrium through the decks + skylight
    bottom = DECKS[decks[-1]]
    for d in decks:
        F = DECKS[d]
        if F == bottom:
            continue
        for x in range(C - 4, C + 5):
            for z in range(C - 4, C + 5):
                dist = math.hypot(x - C, z - C)
                if dist <= 2.4:
                    bp.set(x, F, z, "air")
                elif dist < 3.5:
                    put(bp, x, F + 1, z, st.railing)
    for x in range(C - 3, C + 4):
        for z in range(C - 3, C + 4):
            dist = math.hypot(x - C, z - C)
            if dist <= 2.4:
                for y in range(A_TOP, SURFACE):
                    bp.set(x, y, z, "air")
                bp.set(x, SURFACE, z, "glass")
            elif dist < 3.5:
                bp.set(x, SURFACE, z, W)
    tree(bp, C, bottom + 1, C, h=3)                                      # atrium garden
    for i, a in enumerate(range(0, 360, 60)):
        x, z = round(C + 3 * math.cos(math.radians(a))), round(C + 3 * math.sin(math.radians(a)))
        if bp.get(x, bottom + 1, z) == "minecraft:air":
            if i % 2:
                planter(bp, x, bottom + 1, z)
            else:
                seat(x, bottom + 1, z, "north")
    if L >= 4:  # glass skylight dome
        for x in range(C - 4, C + 5):
            for z in range(C - 4, C + 5):
                dist = math.hypot(x - C, z - C)
                if 2.5 <= dist < 3.5:
                    bp.set(x, SURFACE + 1, z, "glass")
                elif dist < 2.5:
                    bp.set(x, SURFACE + 2, z, "glass")
    if L >= 5:  # glowing ring around the atrium on every deck
        for d in decks:
            F = DECKS[d]
            for x in range(C - 4, C + 5):
                for z in range(C - 4, C + 5):
                    if 3.5 <= math.hypot(x - C, z - C) < 4.5 and (x + z) % 2 == 0:
                        bp.set(x, F, z, "sea_lantern")

    # ---------------------------------------------------------------- stair core: alternating runs
    order = ["D", "C", "B", "A"]
    for i, d in enumerate(order[:-1]):
        if d not in decks or order[i + 1] not in decks:
            continue
        F = DECKS[d]
        if i % 2 == 0:
            col, zs, facing = 24, list(range(11, 16)), "south"
        else:
            col, zs, facing = 23, list(range(15, 10, -1)), "north"
        for z in zs[:4]:
            bp.set(col, F + 5, z, "air")
        for j, z in enumerate(zs):
            bp.set(col, F + 1 + j, z, f"{st.SEAT}[facing={facing},half=bottom,shape=straight,waterlogged=false]")

    # ---------------------------------------------------------------- surface entrance (x20, rising north)
    FA = DECKS["A"]
    for i in range(8):
        z, y = 12 - i, FA + 1 + i
        for yy in range(FA + 1, y):
            bp.set(20, yy, z, W)
        bp.set(20, y, z, f"{st.SEAT}[facing=north,half=bottom,shape=straight,waterlogged=false]")
        for yy in range(y + 1, min(y + 4, SURFACE + 1)):
            bp.set(20, yy, z, "air")
    PX1, PX2, PZ1, PZ2, PTOP = 17, 23, 1, 9, SURFACE + 5
    for x in range(PX1, PX2 + 1):
        for z in range(PZ1, PZ2 + 1):
            e = edge(x, z, PX1, PX2, PZ1, PZ2)
            if not (x == 20 and 5 <= z <= 8):
                bp.set(x, SURFACE, z, concrete if e else st.floor(x, z))
            bp.set(x, PTOP, z, k.band if e else W)
            if e:
                for y in range(SURFACE + 1, PTOP):
                    corner = x in (PX1, PX2) and z in (PZ1, PZ2)
                    bp.set(x, y, z, (k.glow or W) if corner else (G if y < PTOP - 1 else W))
    for y in (SURFACE + 1, SURFACE + 2):
        bp.set(20, y, PZ1, "air")
    k.door(20, SURFACE + 1, PZ1, "south")
    for z in range(5, 9):
        put(bp, 19, SURFACE + 1, z, st.railing)
        put(bp, 21, SURFACE + 1, z, st.railing)
    put(bp, 20, SURFACE + 1, 9, st.railing)
    st.ceiling_light(bp, 20, PTOP, 3)
    for z in range(0, PZ1):
        for x in (19, 20, 21):
            bp.set(x, SURFACE, z, W if x != 20 else "smooth_stone")
    for x, z in ((8, 30), (32, 30), (32, 12), (8, 12)):                 # air vents
        bp.set(x, SURFACE + 1, z, "iron_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]")
        for y in range(A_TOP, SURFACE + 1):
            bp.set(x, y, z, "iron_bars[east=false,north=false,south=false,waterlogged=false,west=false]")

    # ---------------------------------------------------------------- deck A: living
    y = DECKS["A"] + 1
    for x in (4, 5, 6, 14, 15)[:L]:                                      # dorm (NW): bunker residents
        bed(bp, x, y, 12, "south")
    for x in (4, 5):
        bp.set(x, y, 3, "barrel[facing=south,open=false]")
    hut = (8, y, 4)
    for x in (4, 7, 10):                                                 # commons lounge (W)
        seat(x, y, 17, "north")
    put(bp, 7, y, 21, st.counter)
    seat(6, y, 21, "west")
    seat(8, y, 21, "east")
    bp.set(4, y, 24, "jukebox[has_record=false]")
    for z in range(17, 25):                                              # stores & laundry (E)
        bp.set(37, y, z, "barrel[facing=west,open=false]")
        if L >= 2:
            bp.set(37, y + 1, z, "barrel[facing=west,open=false]")
    bp.set(29, y, 16, "water_cauldron[level=3]")
    bp.set(30, y, 16, "crafting_table")

    # ---------------------------------------------------------------- deck B: player base
    y = DECKS["B"] + 1
    smelt = ["furnace"] * 4 + ["blast_furnace"] * 2 + ["smoker"] * 2
    for i, s in enumerate(smelt[: min(3 + L, 8)]):                       # workshop (NW)
        bp.set(4 + i, y, 3, f"{s}[facing=south,lit=false]")
    for z, s in ((5, "crafting_table"), (6, "smithing_table"), (7, "stonecutter[facing=east]"),
                 (8, "loom[facing=east]"), (9, "cartography_table"), (10, "fletching_table")):
        bp.set(3, y, z, s)
    for x in range(11, 15):
        put(bp, x, y, 7, st.counter)
    for x in range(29, 34):                                              # enchanting library (NE)
        for z in range(5, 10):
            ring = x in (29, 33) or z in (5, 9)
            for yy in (y, y + 1):
                bp.set(x, yy, z, "bookshelf" if ring else "air")
    for yy in (y, y + 1):
        bp.set(31, yy, 9, "air")
    bp.set(31, y, 7, "enchanting_table")
    bp.set(27, y, 12, "anvil[facing=north]")
    bp.set(28, y, 12, "grindstone[face=floor,facing=north]")
    bp.set(36, y, 12, "lectern[facing=west,has_book=false,powered=false]")
    for yy in (y, y + 1, y + 2):                                         # storage vault (SW)
        for x in range(4, 17):                                           # (corners stay free)
            bp.set(x, yy, 37, "barrel[facing=north,open=false]")
        for z in range(28, 37):
            bp.set(3, yy, z, "barrel[facing=east,open=false]")
            if not 30 <= z <= 34:
                bp.set(17, yy, z, "barrel[facing=west,open=false]")
        for z in range(29, 36):
            for x in (6, 7, 11, 12):
                bp.set(x, yy, z, "barrel[facing=up,open=false]")
    bed(bp, 35, y, 35, "south")                                          # player suite (SE)
    bed(bp, 33, y, 35, "south")
    bp.set(37, y, 28, "brewing_stand[has_bottle_0=false,has_bottle_1=false,has_bottle_2=false]")
    bp.set(37, y, 29, "brewing_stand[has_bottle_0=false,has_bottle_1=false,has_bottle_2=false]")
    bp.set(37, y, 30, "water_cauldron[level=3]")
    bp.set(37, y, 31, "barrel[facing=west,open=false]")
    put(bp, 29, y, 30, st.counter)
    seat(28, y, 30, "west")
    seat(30, y, 30, "east")
    if L >= 4:
        bp.set(36, y, 37, "ender_chest[facing=north,waterlogged=false]")
    bp.set(29, y, 37, "jukebox[has_record=false]")
    for z, s in ((17, "anvil[facing=east]"), (18, "smithing_table"), (19, "grindstone[face=floor,facing=east]"),
                 (23, "barrel[facing=east,open=false]"), (24, "barrel[facing=east,open=false]")):
        bp.set(3, y, z, s)                                               # armory (W)
    for x in range(5, 12, 2):
        bp.set(x, y, 24, "barrel[facing=north,open=false]")
    bp.set(37, y, 18, "cartography_table")                              # map room (E)
    bp.set(37, y, 19, "lectern[facing=west,has_book=false,powered=false]")
    bp.set(37, y, 21, "crafting_table")
    for z in range(22, 25):
        bp.set(37, y, z, "bookshelf")
        bp.set(37, y + 1, z, "bookshelf")
    put(bp, 32, y, 20, st.counter)
    put(bp, 33, y, 20, st.counter)

    # ---------------------------------------------------------------- farm decks
    def field(F):
        for x in range(3, 18):
            for z in range(3, 38):
                if (x, z) == (10, 20):
                    continue
                bp.set(x, F, z, "water[level=0]" if x % 4 == 1 else "farmland[moisture=7]")
        bp.set(10, F, 20, st.floor(10, 20))
        bp.set(10, F + 1, 20, "minecolonies:blockhutfield[facing=north,half=lower]",
               NBT.Compound({"id": NBT.String("minecolonies:scarecrow"), "Item": NBT.String("")}))
        bp.set(10, F + 2, 20, "minecolonies:blockhutfield[facing=north,half=upper]")
        for x in range(4, 18, 4):
            for z in range(5, 38, 5):
                # hanging lights (a light in the ceiling would replace the farmland of the deck above)
                bp.set(x, F + 4, z, "lantern[hanging=true,waterlogged=false]")

    if "C" in decks:
        F = DECKS["C"]
        field(F)
        y = F + 1
        for z in range(17, 25):                                          # compost store (E)
            bp.set(37, y, z, "barrel[facing=west,open=false]")
        for x in (29, 31, 33):
            bp.set(x, y, 24, "composter[level=0]")
        for x in range(28, 38):                                          # reservoir (SE)
            for z in range(29, 38):
                wall = x in (28, 37) or z in (29, 37)
                for yy in (y, y + 1):
                    bp.set(x, yy, z, "glass" if wall else ("water[level=0]" if yy == y else "air"))

    if "D" in decks:
        F = DECKS["D"]
        field(F)
        y = F + 1
        k.fill(30, y, 7, 32, y + 2, 9, "redstone_block")                 # generator room (NE)
        bp.set(31, y + 3, 8, "sea_lantern" if L >= 5 else "redstone_block")
        for x, z in ((28, 5), (34, 5), (28, 11), (34, 11)):
            k.fill(x, y, z, x, y + 2, z, "waxed_copper_block" if not st.early else "iron_block")
            bp.set(x, y + 3, z, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        for cx, cz in ((30, 31), (34, 34)):                              # water tanks (SE)
            for x in range(cx - 1, cx + 2):
                for z in range(cz - 1, cz + 2):
                    for yy in (y, y + 1, y + 2):
                        bp.set(x, yy, z, "glass" if (x, z) != (cx, cz) else "water[level=0]")
        for z in range(17, 25):                                          # emergency stores (E)
            for yy in (y, y + 1):
                bp.set(37, yy, z, "barrel[facing=west,open=false]")

    # ---------------------------------------------------------------- child rooms
    for name, (block, deck, room, (hx, hz)) in CHILDREN.items():
        if deck not in decks:
            continue
        x1, x2, z1, z2 = ROOMS_XZ[room]
        F = DECKS[deck]
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                for yy in range(F + 1, F + 5):
                    bp.set(x, yy, z, SUBST)
        if preview_rooms:
            for x in range(x1, x2 + 1):
                for z in range(z1, z2 + 1):
                    for yy in range(F + 1, F + 5):
                        bp.set(x, yy, z, "minecraft:air")
            furnish(name, bp, preview_rooms, x1, F + 1, z1, {})
        k.child((x1 + hx, F + 1, z1 + hz), block, f"fundamentals/{name}0.blueprint")

    # ---------------------------------------------------------------- surface landscaping
    if L >= 2:
        for x, z in ((5, 5), (35, 5), (5, 35), (35, 35), (28, 28)):
            tree(bp, x, SURFACE + 1, z, h=3)
    if L >= 3:
        for x, z in ((12, 20), (28, 20), (20, 30)):
            planter(bp, x, SURFACE + 1, z)
    if L >= 4:
        for x in (16, 24):
            street_lamp(bp, x, SURFACE + 1, 0, premium=True)
    if L >= 5:
        for x, z in ((PX1, PZ1), (PX2, PZ1), (PX1, PZ2), (PX2, PZ2)):
            k.fill(x, SURFACE + 1, z, x, PTOP - 1, z, "sea_lantern")

    connect_panes(bp)
    tags = {hut: ["neoterra"], (0, SURFACE, 0): ["groundlevel"]}
    for p, names in k.tags.items():
        tags.setdefault(p, []).extend(names)
    path = f"fundamentals/bunker{L}.blueprint"
    bp.set(*hut, "minecolonies:blockhutcitizen[facing=north]", hut_te(path, (SX, SY, SZ), hut, tags))
    bp.primary_offset = hut
    bp.architects = ["Neoterra"]
    return bp


if __name__ == "__main__":
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    for lvl in range(1, 6):
        build_bunker(lvl).save(out / f"bunker{lvl}.blueprint")
        for name in CHILDREN:
            build_room(name, lvl).save(out / f"{name}{lvl}.blueprint")
    print("bunker (4 decks) + 4 child room types x 5 levels")
    if len(sys.argv) > 2:
        prev = Path(sys.argv[2])
        prev.mkdir(parents=True, exist_ok=True)
        for lvl in range(1, 6):
            b = build_bunker(lvl, preview_rooms=lvl)
            b.save(prev / f"bunker{lvl}_furnished.blueprint")
            for y in range(b.sy):                       # cutaway copy for the preview images
                for z in range(b.sz):
                    for x in range(b.sx):
                        g = b.grid[y][z][x]
                        if g == SOLID or (y == SURFACE and g.startswith("minecraft:grass")):
                            b.grid[y][z][x] = "minecraft:air"
                        if y == A_TOP and X1 < x < X2 and Z1 < z < Z2:
                            b.grid[y][z][x] = "minecraft:air"
            b.save(prev / f"bunker{lvl}_cutaway.preview")
