"""
Neoterra Bunker: a self-sustaining underground settlement (levels 1-5).

The bunker is a residence hut (its residents sleep in the dorm, 1-5 beds) that contains four
child huts, each upgraded on its own, exactly like the Skytower / barracks:

  bunkerkitchen1-5 (blockhutcook)      canteen: 1 furnace per level, seats, kitchen `work` spots.
  bunkerschool1-5  (blockhutschool)    classroom: 10 seats + teacher spot, bookshelves.
  bunkerclinic1-5  (blockhuthospital)  sick bay: 2 beds per level + furnace.
  bunkerfarm1-5    (blockhutfarmer)    farm office with racks; the farmer works the scarecrow
                                       field in the lit farm hall on the lower deck.

Layout (everything below the lawn at y 14):
  surface   glass entrance pavilion, lawn, air vents, trees, lamp spires (L4)
  deck A    y 7-10: dorm (bunker residents) | canteen | school  — corridor —
            clinic | storage + generator room | stair hall
  deck B    y 2-5:  farm hall with farmland, water channels and a scarecrow field, farm office

The child rooms are `structurize:blocksubstitution` in the bunker blueprint, the ground around
the shell is `structurize:blocksolidsubstitution`, so the builder only digs out what it needs.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit import Kit, SUBST, edge, put, rack, tree, planter, bed, door, street_lamp  # noqa: E402
from common import Blueprint, Style, hut_te, connect_panes  # noqa: E402
from nbtlib import tag as NBT  # noqa: E402

SX, SY, SZ = 33, 22, 31
X1, X2, Z1, Z2 = 2, 30, 2, 28            # shell
B_FLOOR, SLAB, A_TOP, SURFACE = 1, 6, 11, 14
SOLID = "structurize:blocksolidsubstitution"

# child rooms: name -> (block, x1, x2, z1, z2, floor_y, hut_xz)
ROOMS = {
    "bunkerkitchen": ("blockhutcook", 13, 19, 3, 12, SLAB, (13, 11)),
    "bunkerschool": ("blockhutschool", 21, 29, 3, 12, SLAB, (28, 4)),
    "bunkerclinic": ("blockhuthospital", 3, 11, 18, 27, SLAB, (4, 22)),
    "bunkerfarm": ("blockhutfarmer", 24, 29, 3, 9, B_FLOOR, (28, 8)),
}


# ---------------------------------------------------------------------------- child rooms
def furnish(name, bp, L, ox, oy, oz, tags):
    """Furnish a child room. (ox, oy, oz) = world pos of the room's interior corner at floor+1."""
    st = Style(L)
    block, x1, x2, z1, z2, fy, (hx, hz) = ROOMS[name]

    def P(x, z):
        return x - x1 + ox, z - z1 + oz

    def seat(x, z, back):
        wx, wz = P(x, z)
        bp.set(wx, oy, wz, f"{st.SEAT}[facing={back},half=bottom,shape=straight,waterlogged=false]")
        tags.setdefault((wx, oy, wz), []).append("sit")

    def put_at(x, z, s, y=0):
        wx, wz = P(x, z)
        put(bp, wx, oy + y, wz, s)

    if name == "bunkerkitchen":            # door from the corridor at (16, 12): keep it free
        for i in range(L):
            put_at(14 + i, 3, "furnace[facing=south,lit=false]")
            wx, wz = P(14 + i, 4)
            tags.setdefault((wx, oy, wz), []).append("work")
        put_at(19, 3, "smoker[facing=south,lit=false]")
        put_at(19, 4, "crafting_table")
        wx, wz = P(13, 3)
        rack(bp, wx, oy, wz, "south")
        for tx, tz in ((15, 6), (15, 9)):
            put_at(tx, tz, st.counter)
            seat(tx - 1, tz, "west")
            seat(tx + 1, tz, "east")
        if L >= 3:
            put_at(18, 7, st.counter)
            seat(18, 8, "south")
    elif name == "bunkerschool":           # door at (25, 12); board on the north wall
        for x in range(22, 29):
            put_at(x, 3, "black_concrete", 1)
        wx, wz = P(25, 4)
        tags.setdefault((wx, oy, wz), []).append("work")
        for z in (7, 9):
            for x in (22, 23, 24, 26, 27):
                put_at(x, z - 1, st.counter)
                seat(x, z, "south")                                      # backrest south: faces the board
        for i in range(2 * L):
            put_at(21, 4 + i % 5, "bookshelf", i // 5)
    elif name == "bunkerclinic":
        spots = [(x, 20, "north") for x in (3, 5, 7, 9, 11)] + [(x, 25, "south") for x in (3, 5, 7, 9, 11)]
        for x, z, f in spots[: 2 * L]:
            wx, wz = P(x, z)
            bed(bp, wx, oy, wz, f, "red")
        put_at(11, 22, "furnace[facing=west,lit=false]")
        put_at(11, 23, "barrel[facing=west,open=false]")
        if L >= 3:
            put_at(10, 22, "brewing_stand[has_bottle_0=false,has_bottle_1=false,has_bottle_2=false]")
    elif name == "bunkerfarm":
        for i in range(L):
            wx, wz = P(24 + i, 3)
            rack(bp, wx, oy, wz, "south")
        put_at(29, 5, "composter[level=0]")
        put_at(29, 4, "barrel[facing=west,open=false]")
        put_at(25, 8, st.counter)
        seat(25, 7, "north")
    # hanging lights
    for lx, lz in ((x1 + 2, z1 + 2), (x2 - 2, z2 - 2)):
        wx, wz = P(lx, lz)
        if bp.get(wx, oy + 3, wz) == "minecraft:air":
            bp.set(wx, oy + 3, wz, "lantern[hanging=true,waterlogged=false]")


def build_room(name, L):
    block, x1, x2, z1, z2, fy, (hx, hz) = ROOMS[name]
    sx, sz = x2 - x1 + 1, z2 - z1 + 1
    bp = Blueprint(sx, 4, sz, f"{name}{L}.blueprint")
    tags = {}
    furnish(name, bp, L, 0, 0, 0, tags)
    hut = (hx - x1, 0, hz - z1)
    tags.setdefault(hut, []).append("invisible")
    path = f"fundamentals/{name}{L}.blueprint"
    bp.set(*hut, f"minecolonies:{block}[facing=north]", hut_te(path, (sx, 4, sz), hut, tags))
    bp.primary_offset = hut
    bp.architects = ["Neoterra"]
    return bp


# ---------------------------------------------------------------------------- bunker
def build_bunker(L, preview_rooms=0):
    k = Kit("bunker", "fundamentals", L, (SX, SY, SZ))
    bp, W, G, T = k.bp, k.W, k.G, k.T
    concrete = "gray_concrete" if k.st.early else "polished_deepslate"

    # ground: solid substitution everywhere below the lawn, lawn on top, air above
    bp.fill(0, 0, 0, SX - 1, SURFACE - 1, SZ - 1, SOLID)
    for x in range(SX):
        for z in range(SZ):
            bp.set(x, SURFACE, z, "grass_block[snowy=false]")

    # shell: outer concrete box from y0 to the deck-A ceiling, hollow decks inside
    for x in range(X1, X2 + 1):
        for z in range(Z1, Z2 + 1):
            e = edge(x, z, X1, X2, Z1, Z2)
            bp.set(x, 0, z, concrete)
            bp.set(x, A_TOP, z, concrete if e else W)
            for y in range(1, A_TOP):
                bp.set(x, y, z, concrete if e else "air")
            if not e:
                bp.set(x, B_FLOOR, z, k.st.floor(x, z))
                bp.set(x, SLAB, z, k.st.floor(x, z))
    # deck A partitions: corridor z14-16 between walls z13 / z17; rooms split at x12 / x20
    for y in range(SLAB + 1, A_TOP):
        for x in range(X1 + 1, X2):
            bp.set(x, y, 13, W)
            bp.set(x, y, 17, W)
        for xp in (12, 20):
            for z in list(range(Z1 + 1, 13)) + list(range(18, Z2)):
                bp.set(xp, y, z, W)
    for x in (7, 16, 25):                                                # room doors off the corridor
        for z in (13, 17):
            k.opening(x, SLAB + 1, z, x, SLAB + 2, z)
    for x in range(4, 30, 4):                                            # corridor light strip
        k.st.ceiling_light(bp, x, A_TOP, 15)
    # deck B: farm office wall (x23 / z10) with a door
    for y in range(B_FLOOR + 1, SLAB):
        for z in range(Z1 + 1, 11):
            bp.set(23, y, z, W)
        for x in range(23, X2):
            bp.set(x, y, 10, W)
    k.opening(26, B_FLOOR + 1, 10, 26, B_FLOOR + 2, 10)

    # ------------------------------------------------ stairs: surface <-> deck A <-> deck B
    # run 1: deck A (walk 7) up to the pavilion (walk 15) along x28, rising south z19->z26
    for i in range(8):
        z, y = 19 + i, SLAB + 1 + i
        for yy in range(SLAB + 1, y):
            bp.set(28, yy, z, W)
        bp.set(28, y, z, f"{k.st.SEAT}[facing=south,half=bottom,shape=straight,waterlogged=false]")
        for yy in range(y + 1, min(y + 4, SURFACE + 1)):
            bp.set(28, yy, z, "air")                                      # 3 blocks of headroom through the cover
    bp.set(28, SURFACE + 1, 27, "air")
    bp.set(28, SURFACE, 27, W)
    # run 2: deck B (walk 2) up to deck A (walk 7) along x22, rising north z26->z22
    for i in range(5):
        z, y = 26 - i, B_FLOOR + 1 + i
        for yy in range(B_FLOOR + 1, y):
            bp.set(22, yy, z, W)
        bp.set(22, y, z, f"{k.st.SEAT}[facing=north,half=bottom,shape=straight,waterlogged=false]")
        if y < SLAB:
            bp.set(22, SLAB, z, "air")
    for z in range(23, 27):
        put(bp, 23, SLAB + 1, z, k.st.railing)
    put(bp, 22, SLAB + 1, 27, k.st.railing)

    # ------------------------------------------------ surface pavilion over the stair hall
    PX1, PX2, PZ1, PZ2, PTOP = 24, 30, 18, 28, SURFACE + 5
    for x in range(PX1, PX2 + 1):
        for z in range(PZ1, PZ2 + 1):
            e = edge(x, z, PX1, PX2, PZ1, PZ2)
            if not (x == 28 and 23 <= z <= 26):
                bp.set(x, SURFACE, z, k.st.floor(x, z) if not e else concrete)
            bp.set(x, PTOP, z, k.band if e else W)
            if e:
                for y in range(SURFACE + 1, PTOP):
                    bp.set(x, y, z, G if y < PTOP - 1 and not (x in (PX1, PX2) and z in (PZ1, PZ2)) else W)
    k.opening(26, SURFACE + 1, PZ1, 26, SURFACE + 2, PZ1)
    k.door(26, SURFACE + 1, PZ1, "south")
    k.st.ceiling_light(bp, 26, PTOP, 23)
    for z in range(23, 27):                                              # rails around the stairwell
        put(bp, 27, SURFACE + 1, z, k.st.railing)
        put(bp, 29, SURFACE + 1, z, k.st.railing)
    put(bp, 28, SURFACE + 1, 22, k.st.railing)
    # path, vents, trees
    for z in range(0, PZ1):
        for x in (25, 26, 27):
            bp.set(x, SURFACE, z, "smooth_stone" if x != 26 else W)
    for x, z in ((8, 8), (16, 8), (8, 22), (16, 22)):                     # air vents
        bp.set(x, SURFACE + 1, z, "stone_brick_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]"
               if k.st.early else "polished_deepslate_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
        bp.set(x, SURFACE + 2, z, "iron_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]")
        for y in range(A_TOP, SURFACE + 1):
            bp.set(x, y, z, "iron_bars[east=false,north=false,south=false,waterlogged=false,west=false]")

    # ------------------------------------------------ deck A parent rooms
    y = SLAB + 1
    # dorm (bunker residents)
    for i, x in enumerate((3, 4, 10, 11, 5)[:L]):                      # x6-8 stay free: dorm door at x7
        bed(bp, x, y, 11, "south")
    for x in (3, 4):
        bp.set(x, y, 3, "barrel[facing=south,open=false]")
    k.st.ceiling_light(bp, 7, A_TOP, 7)
    hut = (5, y, 4)
    # storage + generator room (x13-19, z18-27)
    for z in range(19, 24 if L >= 3 else 27):                          # (tank takes the back corner at L3+)
        bp.set(13, y, z, "barrel[facing=east,open=false]")
        if L >= 2:
            bp.set(13, y + 1, z, "barrel[facing=east,open=false]")
    bp.set(19, y, 26, "crafting_table")
    bp.set(19, y, 25, "furnace[facing=west,lit=false]")
    if L >= 3:  # generator + water reservoir (glass tank)
        k.fill(16, y, 20, 18, y + 1, 21, "redstone_block")
        bp.set(17, y + 2, 20, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        for x in range(14, 19):
            for z in range(24, 28):
                tank_wall = x in (14, 18) or z in (24, 27)
                for yy in (y, y + 1):
                    bp.set(x, yy, z, "glass" if tank_wall else ("water[level=0]" if yy == y else "air"))
    k.st.ceiling_light(bp, 16, A_TOP, 22)

    # ------------------------------------------------ deck B farm hall + field
    for x in range(4, 21):
        for z in range(4, 27):
            if (x, z) == (12, 15):
                bp.set(x, B_FLOOR, z, k.st.floor(x, z))
                continue
            if x % 4 == 0:
                bp.set(x, B_FLOOR, z, "water[level=0]")                     # irrigation
            else:
                bp.set(x, B_FLOOR, z, "farmland[moisture=7]")
    bp.set(12, B_FLOOR + 1, 15, "minecolonies:blockhutfield[facing=north,half=lower]",
           NBT.Compound({"id": NBT.String("minecolonies:scarecrow"), "Item": NBT.String("")}))
    bp.set(12, B_FLOOR + 2, 15, "minecolonies:blockhutfield[facing=north,half=upper]")
    for x in range(4, 21, 4):
        for z in range(5, 27, 4):
            bp.set(x, SLAB - 1, z, "lantern[hanging=true,waterlogged=false]" if k.st.early else "air")
            if not k.st.early:
                k.st.ceiling_light(bp, x, SLAB, z)
    for x in range(21, 23):
        for z in range(4, 27):
            bp.set(x, B_FLOOR, z, k.st.floor(x, z))                         # walkway beside the field

    # ------------------------------------------------ child rooms: substitution + level-0 huts
    for name, (block, x1, x2, z1, z2, fy, (hx, hz)) in ROOMS.items():
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                for yy in range(fy + 1, fy + 5):
                    bp.set(x, yy, z, SUBST)
        if preview_rooms:
            for x in range(x1, x2 + 1):
                for z in range(z1, z2 + 1):
                    for yy in range(fy + 1, fy + 5):
                        bp.set(x, yy, z, "minecraft:air")
            furnish(name, bp, preview_rooms, x1, fy + 1, z1, {})
        k.child((hx, fy + 1, hz), block, f"fundamentals/{name}0.blueprint")

    # ------------------------------------------------ surface landscaping
    if L >= 2:
        for x, z in ((4, 4), (20, 4), (4, 26), (20, 26)):
            tree(bp, x, SURFACE + 1, z, h=3)
    if L >= 3:
        for x, z in ((12, 15), (18, 15)):
            planter(bp, x, SURFACE + 1, z)
    if L >= 4:
        for x in (24, 28):
            street_lamp(bp, x, SURFACE + 1, 1, premium=True)
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
        for name in ROOMS:
            build_room(name, lvl).save(out / f"{name}{lvl}.blueprint")
    print("bunker + 4 room types x 5 levels")
    if len(sys.argv) > 2:
        prev = Path(sys.argv[2])
        prev.mkdir(parents=True, exist_ok=True)
        for lvl in range(1, 6):
            b = build_bunker(lvl, preview_rooms=lvl)
            b.save(prev / f"bunker{lvl}_furnished.blueprint")
            for y in range(b.sy):                       # cutaway copy for the preview images
                for z in range(b.sz):
                    for x in range(b.sx):
                        if b.grid[y][z][x] == SOLID or (y == SURFACE and b.grid[y][z][x].startswith("minecraft:grass")):
                            b.grid[y][z][x] = "minecraft:air"
                        if y == A_TOP and X1 < x < X2 and Z1 < z < Z2:
                            b.grid[y][z][x] = "minecraft:air"           # lift the roof off deck A
            b.save(prev / f"bunker{lvl}_cutaway.preview")
