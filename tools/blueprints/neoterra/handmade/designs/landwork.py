"""
Land-work huts: farmer, fisherman, plantation, miner, nether worker.

Miner
  Hearthwood  "Wheal Hearth": Cornish engine house. Rubble-stone house with a tall brick-topped stack built into the
              west gable (forge hearth inside), the shaft head-frame (cluster) framed in dark-oak lattice against
              the east gable. L2 ore track to an ore heap, L3 the engine house rises to two storeys with the beam
              engine upstairs, L4 boiler lean-to, L5 fenced ore yard.
  Cascadia    "Timberline Mine": spruce-log head-frame with braces around the shaft, a log hoist house with the
              winding drum (gable to the street, porch), L2 a track to the ore cart siding, L3 a tipple / ore bin on
              stilts over the rails, L4 powder lean-to, L5 rock dump and lamp shed.
  Neoterra    "Shaft 01": enclosed concrete winding tower over the shaft attached to a white flat-roofed mining
              station (lamp room, ore sorting). L3 glazed control floor upstairs, L4 conveyor gallery to the tower,
              L5 ore yard canopy with tracks.
"""
from hm import Design, design, AIR, D4, OPP, CW


# ------------------------------------------------------------------------------------------------- helpers
def stair(b, facing, half="bottom", shape="straight"):
    b = b if b.endswith("_stairs") else b + "_stairs"
    return f"{b}[facing={facing},half={half},shape={shape},waterlogged=false]"


def slab(b, t="bottom"):
    b = b if b.endswith("_slab") else b + "_slab"
    return f"{b}[type={t},waterlogged=false]"


def logb(b, axis="y"):
    return f"{b}[axis={axis}]"


def trap(b, facing, half="top", open_=False):
    return f"{b}_trapdoor[facing={facing},half={half},open={'true' if open_ else 'false'},powered=false,waterlogged=false]"


def rail(shape):
    return f"rail[shape={shape},waterlogged=false]"


CHAIN = "chain[axis=y,waterlogged=false]"
HOPPER = "hopper[enabled=true,facing=down]"


def walls(d, x1, z1, x2, z2, y1, y2, mat):
    for y in range(y1, y2 + 1):
        for x in range(x1, x2 + 1):
            d.set(x, y, z1, mat)
            d.set(x, y, z2, mat)
        for z in range(z1, z2 + 1):
            d.set(x1, y, z, mat)
            d.set(x2, y, z, mat)


def posts(d, pts, y1, y2, mat):
    for x, z in pts:
        for y in range(y1, y2 + 1):
            d.set(x, y, z, mat)


def ladder(d, x, z, y1, y2, facing):
    for y in range(y1, y2 + 1):
        d.set(x, y, z, f"ladder[facing={facing},waterlogged=false]")


def track(d, pts, y):
    """Rails through a list of cells (orthogonal neighbours); shapes worked out from the neighbours."""
    for i, (x, z) in enumerate(pts):
        nb = []
        for j in (i - 1, i + 1):
            if 0 <= j < len(pts):
                nb.append((pts[j][0] - x, pts[j][1] - z))
        dirs = {(0, -1): "n", (0, 1): "s", (1, 0): "e", (-1, 0): "w"}
        ds = sorted(dirs[v] for v in nb)
        if len(ds) == 2 and ds[0] != ds[1] and {"n", "s"} != set(ds) and {"e", "w"} != set(ds):
            m = {frozenset("se"): "south_east", frozenset("sw"): "south_west", frozenset("ne"): "north_east",
                 frozenset("nw"): "north_west"}
            shape = m[frozenset(ds)]
        elif ds and ds[0] in "ew":
            shape = "east_west"
        else:
            shape = "north_south"
        d.set(x, y, z, rail(shape))


def ore_heap(d, x, y, z, kinds=("raw_iron_block", "coal_block", "gravel")):
    """Small 2x2 heap of mined material with a slab cap."""
    d.set(x, y, z, kinds[0])
    d.set(x + 1, y, z, kinds[1 % len(kinds)])
    d.set(x, y, z + 1, kinds[2 % len(kinds)])
    d.set(x + 1, y, z + 1, "gravel")
    d.set(x, y + 1, z, slab("cobblestone"))


def racks(d, cells, n, facing="north"):
    for x, y, z in cells[:n]:
        d.rack(x, y, z, facing)


def lattice(d, x1, z1, x2, z2, y1, y2, post, beam, step=4, skip=()):
    """Timber/steel frame around a rectangle: corner posts y1..y2, ring beams every `step` and at y2."""
    posts(d, [(x1, z1), (x2, z1), (x1, z2), (x2, z2)], y1, y2, post)
    for y in list(range(y1 + step, y2, step)) + [y2]:
        for x in range(x1 + 1, x2):
            for z in (z1, z2):
                if (x, z) not in skip:
                    d.set(x, y, z, logb(beam, "x") if "log" in beam or "wood" in beam else beam)
        for z in range(z1 + 1, z2):
            for x in (x1, x2):
                if (x, z) not in skip:
                    d.set(x, y, z, logb(beam, "z") if "log" in beam or "wood" in beam else beam)


def mtop(L):
    """Height of the miner cluster's head-frame platform (ground 1)."""
    return 10 + 3 * (L - 1)


# ================================================================================================== MINER
def miner_hearthwood(rel, L):
    d = Design("Hearthwood", rel, (23, 29, 19), gy=1)
    stone, brick = "stone_bricks", "bricks"
    x1, z1, x2, z2 = 2, 5, 12, 11
    tall = L >= 3
    top = 10 if tall else 5
    # rubble-stone walls with a brick quoin course
    for y in range(2, top + 1):
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                if x in (x1, x2) or z in (z1, z2):
                    r = (x * 7 + y * 3 + z * 5) % 9
                    d.set(x, y, z, "mossy_stone_bricks" if r == 0 else ("cobblestone" if r == 4 else stone))
                else:
                    d.set(x, y, z, AIR)
    d.fill(x1, 1, z1, x2, 1, z2, "spruce_planks")
    for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        for y in range(2, top + 1):
            d.set(x, y, z, brick if y % 2 else stone)
    if tall:
        d.fill(x1 + 1, 6, z1 + 1, x2 - 1, 6, z2 - 1, "spruce_planks")
        for x in range(x1, x2 + 1):
            d.set(x, 6, z1, brick)
            d.set(x, 6, z2, brick)
    ridge = d.gable(x1, z1, x2, z2, top + 1, "x", "deepslate_tile_stairs", "deepslate_tile_slab", stone,
                    overhang=1)
    # the east gable is the bob wall against the head-frame: no overhang there
    for y in range(top + 1, ridge + 1):
        for z in range(z1 - 1, z2 + 2):
            d.set(x2 + 1, y, z, AIR)
    # windows: tall arched slits, brick heads
    for x in (4, 10):
        d.window(x, 3, z1, x, 4, z1)
        d.set(x, 5, z1, brick)
        d.window(x, 3, z2, x, 4, z2)
    if tall:
        for x in (4, 7, 10):
            for z in (z1, z2):
                d.window(x, 8, z, x, 9, z)
                d.set(x, 10, z, brick)
    d.door(7, 2, z1, "south", "dark_oak")
    d.set(7, 4, z1, brick)
    d.sign(6, 4, z1 - 1, "north", ["WHEAL", "HEARTH", "est. mine"], "dark_oak")
    # stack built into the west gable: forge hearth inside
    sx1, sz1 = 0, 7
    stack_top = 18 if tall else 12
    for y in range(1, stack_top + 1):
        for x in range(sx1, sx1 + 3):
            for z in range(sz1, sz1 + 3):
                if (x, z) == (sx1 + 1, sz1 + 1) and y > 3:
                    d.set(x, y, z, AIR)                                   # flue
                else:
                    d.set(x, y, z, brick if y > stack_top - 4 or y == 1 else
                          ("cobblestone" if (x + y + z) % 5 == 0 else stone))
    for x in range(sx1, sx1 + 3):
        for z in range(sz1, sz1 + 3):
            if (x, z) != (sx1 + 1, sz1 + 1):
                d.set(x, stack_top + 1, z, slab("brick"))
    d.set(x1, 2, 8, "campfire[facing=east,lit=true,signal_fire=false,waterlogged=false]")
    d.set(x1, 3, 8, brick)
    d.set(sx1 + 1, 3, sz1 + 1, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    d.set(sx1 + 1, 2, sz1 + 1, brick)
    # ---- ground floor: miners' workshop ----
    d.hut(3, 2, 6)
    d.item(3, 2, 10, "furnace", "east")
    if L >= 2:
        d.item(3, 3, 10, "hopper")                                       # ore chute feeding the furnace
    d.item(5, 2, 10, "crafting_table")
    d.set(4, 2, 10, "grindstone[face=floor,facing=north]")              # pick sharpening
    racks(d, [(x, 2, 10) for x in range(6, 12)], d.req["racks"])
    d.set(3, 2, 7, "anvil[facing=north]")
    d.set(3, 2, 9, "water_cauldron[level=3]")                           # quench
    d.set(9, 2, 6, "barrel[facing=up,open=false]")
    d.set(10, 2, 6, "barrel[facing=up,open=false]")
    d.set(8, 2, 8, "dark_oak_fence")                                    # tally table
    d.set(8, 3, 8, "dark_oak_pressure_plate[powered=false]")
    d.chair(8, 2, 7, "north", "dark_oak", sit=False)
    d.lamp(5, top if not tall else 5, 8)
    d.lamp(9, top if not tall else 5, 8)
    if tall:
        ladder(d, 11, 6, 2, 6, "west")
        d.set(11, 6, 6, "ladder[facing=west,waterlogged=false]")
        # engine floor: beam engine cylinder under the rocking beam
        d.fill(7, 7, 8, 8, 9, 9, "polished_deepslate")
        d.set(7, 9, 8, "iron_block")
        for x in range(5, 11):
            d.set(x, 10, 8, logb("dark_oak_log", "x"))
        d.set(5, 9, 8, CHAIN)
        d.set(5, 8, 8, CHAIN)
        d.set(5, 7, 8, "cauldron")
        d.set(9, 7, 9, "lever[face=floor,facing=east,powered=false]")
        d.set(3, 7, 10, "blast_furnace[facing=east,lit=true]")         # boiler fire
        d.set(3, 7, 9, "water_cauldron[level=3]")
        d.set(4, 7, 10, "coal_block")
        d.chair(3, 7, 6, "west", "dark_oak", sit=False)
        d.lamp(5, 11, 8)
        d.lamp(9, 11, 9)
        for x in range(x1 + 1, x2):
            if x not in (10, 11):
                d.set(x, 7, z1 + 1, "air")
        d.set(10, 7, 6, "dark_oak_fence")
        d.set(10, 7, 7, "dark_oak_fence")
    # ---- head-frame lattice around the shaft (cluster at 13..16, 7..9) ----
    yt = mtop(L)
    lattice(d, 12, 6, 17, 10, 2, yt, "dark_oak_log[axis=y]", "stripped_dark_oak_log", step=4,
            skip=[(12, z) for z in range(6, 11)] if not tall else [])
    for x in (12,):
        for z in (6, 10):
            for y in range(top + 1, yt + 1):
                d.set(x, y, z, "dark_oak_log[axis=y]")
    for z in range(6, 11):                                              # top deck
        for x in range(12, 18):
            if x in (12, 17) or z in (6, 10):
                d.set(x, yt, z, "dark_oak_planks")
                d.set(x, yt + 1, z, "dark_oak_fence")
    d.cluster(13, 7)
    d.set(18, 2, 6, "lantern[hanging=false,waterlogged=false]")
    d.set(18, 1, 6, "dark_oak_planks")
    # ---- L2+: ore track from the shaft to the ore heap ----
    if L >= 2:
        pts = [(14, z) for z in range(5, 2, -1)] + [(x, 3) for x in range(15, 20)]
        track(d, pts, 2)
        ore_heap(d, 20, 2, 2)
        d.set(20, 2, 4, "barrel[facing=up,open=false]")
        d.set(21, 2, 4, "chest[facing=west,type=single,waterlogged=false]")
    # ---- L4: boiler lean-to behind ----
    if L >= 4:
        lx1, lx2, lz2 = 4, 10, 15
        walls(d, lx1, z2, lx2, lz2, 2, 4, stone)
        d.fill(lx1 + 1, 1, z2 + 1, lx2 - 1, 1, lz2 - 1, "spruce_planks")
        for i, z in enumerate(range(lz2 + 1, z2, -1)):
            yy = 4 + i
            for x in range(lx1 - 1, lx2 + 2):
                d.set(x, yy, z, stair("deepslate_tile", "north"))
            for x in (lx1, lx2):
                for y in range(5, yy):
                    if z <= lz2:
                        d.set(x, y, z, stone)
        d.door(lx2, 2, 13, "east", "dark_oak")
        d.set(5, 2, 12, "blast_furnace[facing=east,lit=true]")
        d.set(5, 2, 13, "water_cauldron[level=3]")
        d.set(5, 2, 14, "coal_block")
        d.set(9, 2, 14, "barrel[facing=up,open=false]")
        d.set(9, 3, 14, "barrel[facing=up,open=false]")
        d.window(lx1, 3, 13, lx1, 3, 13)
        d.lamp(7, 4, 13)
    # ---- L5: fenced ore yard with a spoil heap ----
    if L >= 5:
        for x in range(14, 23):
            d.set(x, 2, 16, "dark_oak_fence")
        for z in range(12, 17):
            d.set(22, 2, z, "dark_oak_fence")
        d.set(18, 2, 16, "dark_oak_fence_gate[facing=south,in_wall=false,open=false,powered=false]")
        track(d, [(15, z) for z in range(11, 15)] + [(x, 14) for x in range(16, 20)], 2)
        ore_heap(d, 20, 2, 12, ("raw_copper_block", "raw_iron_block", "coal_block"))
        d.fill(13, 2, 13, 13, 2, 15, "gravel")
        d.set(13, 3, 14, "gravel")
        d.set(21, 3, 15, "lantern[hanging=false,waterlogged=false]")
        d.set(21, 2, 15, "dark_oak_fence")
    return d


def miner_cascadia(rel, L):
    d = Design("Cascadia", rel, (25, 29, 21), gy=1, paving="coarse_dirt")
    yt = mtop(L)
    # ---- head-frame: spruce logs with braces around the shaft (cluster at 4..7, 10..12) ----
    lattice(d, 3, 9, 8, 13, 2, yt, "spruce_log[axis=y]", "stripped_spruce_log", step=3)
    for y in range(5, yt, 3):                                         # knee braces under each ring
        for x, z, f in ((3, 10, "south"), (3, 12, "north"), (8, 10, "south"), (8, 12, "north")):
            d.set(x, y - 1, z, stair("spruce", f, "top"))
    for z in range(9, 14):
        for x in range(3, 9):
            if x in (3, 8) or z in (9, 13):
                d.set(x, yt, z, "spruce_planks")
                d.set(x, yt + 1, z, "spruce_fence")
    # back legs: a raking strut from the frame top down toward the hoist house
    d.cluster(4, 10)
    legs = []
    for k in range(1, 12):
        y = yt - 2 * k
        if y < 2:
            break
        legs.append((8 + k, y))
    return_legs = legs
    # ---- hoist house: log walls on river rock, gable to the street ----
    x1, z1, x2, z2 = 11, 7, 19, 15
    d.fill(x1, 1, z1, x2, 1, z2, "cobblestone")
    d.fill(x1 + 1, 1, z1 + 1, x2 - 1, 1, z2 - 1, "spruce_planks")
    for y in range(2, 6):
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                if x in (x1, x2) or z in (z1, z2):
                    ax = "x" if z in (z1, z2) else "z"
                    d.set(x, y, z, logb("spruce_log", ax))
                else:
                    d.set(x, y, z, AIR)
    for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        posts(d, [(x, z)], 2, 5, "stripped_spruce_log[axis=y]")
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if x in (x1, x2) or z in (z1, z2):
                d.set(x, 2, z, "mossy_cobblestone" if (x + z) % 3 == 0 else "cobblestone")
    ridge = d.gable(x1, z1, x2, z2, 6, "z", "dark_oak_stairs", "dark_oak_slab", "spruce_planks", overhang=1)
    for x in range(x1 + 1, x2):                                       # board-and-batten gable ends
        for z in (z1, z2):
            for y in range(6, ridge):
                if d.get(x, y, z) == "minecraft:spruce_planks" and x % 2 == 0:
                    d.set(x, y, z, "stripped_spruce_log[axis=y]")
    mid = (x1 + x2) // 2
    d.door(mid, 2, z1, "south", "spruce")
    for x in (x1 + 2, x2 - 2):
        d.window(x, 3, z1, x, 4, z1)
    for z in range(z1 + 2, z2 - 1, 3):
        d.window(x2, 3, z, x2, 4, z)
    d.window(mid, 7, z1, mid, 8, z1)
    d.door(x1, 2, 11, "west", "spruce")                               # side door toward the shaft
    d.set(x1 - 1, 1, 11, "spruce_planks")
    d.sign(mid, 6, z1 - 1, "north", ["TIMBERLINE", "MINE", "No. 1"], "spruce")
    # porch on the street side
    pz = z1 - 3
    d.fill(x1, 1, pz, x2, 1, z1 - 1, "spruce_planks")
    for x in (x1, x2):
        posts(d, [(x, pz)], 2, 5, "spruce_log[axis=y]")
    for x in range(x1 - 1, x2 + 2):
        d.set(x, 6, pz - 1, stair("spruce", "south"))
        for z in range(pz, z1):
            d.set(x, 6, z, slab("spruce"))
    for x in range(x1 + 1, x2):
        if x != mid:
            d.set(x, 2, pz, "spruce_fence")
    d.chair(x1 + 1, 2, z1 - 1, "south", "spruce", sit=False)
    d.set(x2 - 1, 2, z1 - 1, "barrel[facing=up,open=false]")
    d.lamp(mid - 2, 5, z1 - 2)
    d.lamp(mid + 2, 5, z1 - 2)
    # ---- interior: hoist drum, workbench, racks ----
    d.hut(x1 + 1, 2, z1 + 1)
    for z in range(z1 + 3, z1 + 6):                                   # winding drum on its frame
        d.set(x1 + 2, 3, z, logb("stripped_spruce_log", "z"))
    d.set(x1 + 2, 2, z1 + 2, "spruce_fence")
    d.set(x1 + 2, 3, z1 + 2, "spruce_fence")
    d.set(x1 + 2, 2, z1 + 6, "spruce_fence")
    d.set(x1 + 2, 3, z1 + 6, "spruce_fence")
    d.set(x1 + 3, 2, z1 + 4, "lever[face=floor,facing=east,powered=false]")
    d.item(x2 - 1, 2, z1 + 2, "crafting_table")
    d.item(x2 - 1, 2, z1 + 3, "furnace", "west")
    racks(d, [(x, 2, z2 - 1) for x in range(x2 - 1, x1, -1)], d.req["racks"])
    d.set(x2 - 1, 2, z1 + 5, "barrel[facing=up,open=false]")
    d.set(mid, 2, z1 + 4, "spruce_fence")
    d.set(mid, 3, z1 + 4, "lantern[hanging=false,waterlogged=false]")
    for z in (z1 + 2, z2 - 3):
        d.lamp(mid, 5, z)
    # stone chimney with stove on the east side
    d.set(x2 - 1, 2, z1 + 6, "smoker[facing=west,lit=true]")
    for y in range(2, ridge + 1):
        d.set(x2 + 1, y, z1 + 6, "mossy_cobblestone" if y % 3 == 0 else "cobblestone")
    for x, y in return_legs:                                         # raking back legs onto the roof
        stop = False
        for z in (9, 13):
            for yy in (y + 1, y):
                if d.air(x, yy, z) or "stairs" in d.get(x, yy, z) or "slab" in d.get(x, yy, z):
                    d.set(x, yy, z, logb("spruce_log", "x"))
                else:
                    stop = True
        if stop:
            break
    # ---- L2+: track from the shaft to the cart siding / tipple ----
    if L >= 2:
        pts = [(6, z) for z in range(8, 1, -1)]
        track(d, pts, 2)
        d.set(6, 2, 1, "spruce_fence")
        d.set(5, 2, 1, "spruce_fence")
        d.set(7, 2, 1, "spruce_fence")
        # ore chute: hopper fed from the bin above / a timber chute frame
        posts(d, [(4, 3), (8, 3), (4, 6), (8, 6)], 2, 5 if L >= 3 else 4, "spruce_log[axis=y]")
        if L < 3:
            for x in range(4, 9):
                for z in range(3, 7):
                    if x in (4, 8) or z in (3, 6):
                        d.set(x, 5, z, "spruce_slab[type=bottom,waterlogged=false]")
            d.item(6, 4, 4, "hopper")
            d.set(6, 5, 4, "spruce_planks")
    if L >= 3:                                                         # tipple: ore bin raised on stilts
        d.fill(4, 6, 3, 8, 6, 6, "spruce_planks")
        walls(d, 4, 3, 8, 6, 7, 8, "spruce_planks")
        for x, z in ((4, 3), (8, 3), (4, 6), (8, 6)):
            posts(d, [(x, z)], 6, 9, "spruce_log[axis=y]")
        d.fill(5, 7, 4, 7, 7, 5, "raw_iron_block")
        d.set(6, 8, 4, "coal_block")
        d.item(6, 5, 4, "hopper")
        d.set(6, 5, 5, "spruce_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
        d.gable(4, 3, 8, 6, 9, "z", "spruce_stairs", "spruce_slab", "spruce_planks", overhang=1)
        for y in range(2, 6):                                          # access ladder to the bin
            d.set(3, y, 5, "ladder[facing=west,waterlogged=false]")
        d.set(3, 6, 5, "ladder[facing=west,waterlogged=false]")
        d.set(3, 7, 5, "ladder[facing=west,waterlogged=false]")
        d.set(4, 7, 5, AIR)
        d.set(4, 8, 5, AIR)
    # ---- L4: powder & tool lean-to on the east ----
    if L >= 4:
        lx1, lx2 = x2, x2 + 4
        walls(d, lx1, 10, lx2, 14, 2, 4, "spruce_planks")
        d.fill(lx1 + 1, 1, 11, lx2 - 1, 1, 13, "spruce_planks")
        for z in range(9, 16):
            for x in range(lx1 + 1, lx2 + 2):
                d.set(x, 5, z, slab("spruce"))
        d.set(lx1, 2, 11, AIR)
        d.set(lx1, 3, 11, AIR)
        d.set(lx2 - 1, 2, 11, "barrel[facing=up,open=false]")
        d.set(lx2 - 1, 2, 13, "tnt[unstable=false]")
        d.set(lx2 - 1, 3, 13, "spruce_slab[type=bottom,waterlogged=false]")
        d.set(lx2 - 1, 2, 12, "barrel[facing=up,open=false]")
        d.lamp(lx1 + 2, 4, 12)
        d.window(lx2, 3, 12, lx2, 3, 12)
    # ---- L5: rock dump, fences and lamp posts ----
    if L >= 5:
        d.fill(1, 2, 16, 4, 2, 19, "gravel")
        d.fill(1, 3, 17, 3, 3, 18, "gravel")
        d.set(2, 4, 17, "cobblestone")
        d.set(4, 2, 17, "mossy_cobblestone")
        track(d, [(6, z) for z in range(14, 19)] + [(x, 18) for x in range(7, 11)], 2)
        ore_heap(d, 11, 2, 17, ("raw_gold_block", "raw_iron_block", "coal_block"))
        for x in range(13, 24):
            d.set(x, 2, 19, "spruce_fence")
        for x, z in ((9, 3), (22, 6)):
            d.set(x, 2, z, "spruce_fence")
            d.set(x, 3, z, "spruce_fence")
            d.set(x, 4, z, "lantern[hanging=false,waterlogged=false]")
    return d


def miner_neoterra(rel, L):
    d = Design("Neoterra", rel, (21, 29, 17), gy=1, paving="smooth_stone")
    yt = mtop(L)
    # ---- enclosed winding tower around the shaft (cluster at 4..7, 6..8) ----
    for y in range(2, yt):
        for x in range(3, 9):
            for z in range(5, 10):
                if x in (3, 8) or z in (5, 9):
                    corner = x in (3, 8) and z in (5, 9)
                    d.set(x, y, z, "white_concrete" if corner else "light_gray_concrete")
    for y in range(3, yt - 1):                                       # glazed strips
        for x in (5, 6):
            d.set(x, y, 5, "gray_stained_glass_pane")
            d.set(x, y, 9, "gray_stained_glass_pane")
        d.set(3, y, 7, "gray_stained_glass_pane")
    for y in range(4, yt, 4):
        d.set(8, y, 6, "sea_lantern")
        d.set(8, y, 8, "sea_lantern")
    for x in range(3, 9):
        for z in range(5, 10):
            if x in (3, 8) or z in (5, 9):
                d.set(x, yt, z, "smooth_quartz")
                d.set(x, yt + 1, z, "iron_bars")
    d.fill(3, yt - 1, 5, 8, yt - 1, 5, "cyan_terracotta")
    d.fill(3, yt - 1, 9, 8, yt - 1, 9, "cyan_terracotta")
    d.sign(5, yt - 2, 4, "north", ["SHAFT", "01"], "birch", glow=True, color="cyan")
    d.door(8, 2, 7, "west", "iron")
    d.cluster(4, 6)
    # ---- mining station ----
    X2 = 15 if L == 1 else 19
    x1, z1, z2 = 9, 4, 11
    tall = L >= 3
    top = 5
    d.box(x1, 2, z1, X2, top, z2, "white_concrete", floor="polished_andesite")
    d.fill(x1, 6, z1, X2, 6, z2, "smooth_quartz")
    d.set(x1, 2, 7, AIR)
    d.set(x1, 3, 7, AIR)
    for x in range(x1 + 1, X2):
        if x != 12:
            d.window(x, 3, z1, x, 4, z1)
    for z in range(z1 + 2, z2 - 1, 2):
        d.window(X2, 3, z, X2, 4, z)
    d.fill(x1, 5, z1, X2, 5, z1, "cyan_terracotta")
    d.door(12, 2, z1, "south", "birch")
    for x in range(11, 15):                                           # entrance canopy
        d.set(x, 5, z1 - 1, slab("smooth_quartz", "top"))
        d.set(x, 5, z1 - 2, slab("smooth_quartz", "top"))
    d.hut(14, 2, 5)
    d.item(10, 2, 10, "crafting_table")
    d.item(11, 2, 10, "furnace", "north")
    if L >= 2:
        d.item(11, 3, 10, "hopper")
    racks(d, [(12, 2, 10), (13, 2, 10), (14, 2, 10), (16, 2, 10), (17, 2, 10), (18, 2, 10)], d.req["racks"])
    # lamp room: helmet lockers (iron trapdoors) and charging lamps
    for z in (5, 6):
        d.set(10, 2, z, "iron_block")
        d.set(10, 3, z, "iron_trapdoor[facing=east,half=bottom,open=true,powered=false,waterlogged=false]")
    d.set(10, 2, 8, "smooth_quartz_slab[type=top,waterlogged=false]")
    d.set(10, 3, 8, "lantern[hanging=false,waterlogged=false]")
    for x in range(11, X2, 3):
        d.set(x, 5, 7, "sea_lantern")
    if L >= 2:                                                        # ore sorting bench in the extension
        for x in range(15, 17):
            d.set(x, 2, 7, "smooth_quartz_slab[type=top,waterlogged=false]")
        d.set(15, 2, 5, "barrel[facing=up,open=false]")
        d.set(16, 2, 5, "barrel[facing=up,open=false]")
        d.set(17, 2, 8, "stonecutter[facing=west]") if L < 3 else d.set(16, 2, 8, "stonecutter[facing=north]")
    if tall:                                                          # glazed control floor
        d.box(x1, 7, z1, X2, 10, z2, "white_concrete")
        for x in range(x1 + 1, X2):
            d.window(x, 8, z1, x, 9, z1, "light_blue_stained_glass_pane")
            d.window(x, 8, z2, x, 9, z2, "light_blue_stained_glass_pane")
        d.flat(x1, z1, X2, z2, 11, "smooth_quartz", "white_concrete", "smooth_quartz_slab")
        for i in range(4):                                            # stair along the east wall, rising south
            d.set(X2 - 1, 2 + i, 5 + i, stair("smooth_quartz", "south"))
            d.set(X2 - 1, 6, 5 + i, AIR)
            d.set(X2 - 2, 7, 5 + i, "iron_bars")
        # control desk facing the tower
        for z in range(5, 10):
            d.set(x1 + 1, 7, z, "smooth_quartz_slab[type=top,waterlogged=false]" if z != 7 else "observer[facing=up,powered=false]")
        d.chair(x1 + 2, 7, 6, "east", "birch", sit=False)
        d.chair(x1 + 2, 7, 8, "east", "birch", sit=False)
        d.set(x1, 8, 7, "light_blue_stained_glass_pane")
        d.set(x1, 9, 7, "light_blue_stained_glass_pane")
        d.set(13, 7, 9, "potted_bamboo")
        for x in range(11, X2, 4):
            d.set(x, 10, 7, "sea_lantern")
    else:
        d.flat(x1, z1, X2, z2, 6, "smooth_quartz", "white_concrete", "smooth_quartz_slab")
    if L >= 4:                                                        # conveyor gallery tower -> station roof
        for x in range(9, 13):
            d.set(x, 12, 6, "light_gray_concrete")
            d.set(x, 12, 8, "light_gray_concrete")
            d.set(x, 12, 7, "smooth_quartz")
            d.set(x, 13, 6, "gray_stained_glass_pane")
            d.set(x, 13, 8, "gray_stained_glass_pane")
            d.set(x, 14, 7, "smooth_quartz_slab[type=bottom,waterlogged=false]")
            d.set(x, 14, 6, "smooth_quartz_slab[type=bottom,waterlogged=false]")
            d.set(x, 14, 8, "smooth_quartz_slab[type=bottom,waterlogged=false]")
        for x in (14, 17):                                            # solar panels on the roof
            for z in range(6, 10):
                d.set(x, 12, z, "daylight_detector[inverted=false,power=0]")
    if L >= 5:                                                        # ore yard canopy with tracks
        for x in range(10, 20):
            for z in range(13, 16):
                d.set(x, 6, z, "smooth_quartz_slab[type=bottom,waterlogged=false]")
        posts(d, [(10, 15), (19, 15)], 2, 5, "light_gray_concrete")
        track(d, [(5, z) for z in range(10, 15)] + [(x, 14) for x in range(6, 17)], 2)
        ore_heap(d, 17, 2, 13, ("raw_iron_block", "raw_copper_block", "coal_block"))
        d.set(13, 5, 13, "lantern[hanging=true,waterlogged=false]")
    return d


@design("miner")
def miner(pack, rel, L):
    return {"Hearthwood": miner_hearthwood, "Cascadia": miner_cascadia, "Neoterra": miner_neoterra}[pack](rel, L)


# ============================================================================================ NETHER WORKER
NW_STYLE = {
    "Neoterra": dict(size=(25, 16, 19), X=2, Z=3, wall="white_concrete", base="polished_blackstone_bricks",
                     floor="polished_blackstone", trim="cyan_terracotta", wood="crimson", glass="gray_stained_glass_pane",
                     light="sea_lantern", fire="soul_campfire", paving="smooth_stone"),
    "Hearthwood": dict(size=(27, 24, 19), X=3, Z=3, wall="stone_bricks", base="polished_blackstone_bricks",
                       floor="deepslate_tiles", trim="chiseled_stone_bricks", wood="dark_oak",
                       glass="red_stained_glass_pane", light="lantern", fire="campfire", paving=None),
    "Cascadia": dict(size=(25, 22, 21), X=4, Z=5, wall="spruce_log", base="blackstone",
                     floor="spruce_planks", trim="stripped_spruce_log", wood="spruce", glass="glass_pane",
                     light="lantern", fire="campfire", paving="coarse_dirt"),
}


def nw_wall(d, pack, x, y, z, st, along):
    """One wall cell in the pack's wall material (Cascadia: horizontal logs)."""
    if pack == "Cascadia":
        d.set(x, y, z, logb("spruce_log", along) if y > 2 else ("blackstone" if (x + z) % 3 else "basalt[axis=y]"))
    elif pack == "Hearthwood":
        r = (x * 5 + y * 7 + z * 3) % 11
        d.set(x, y, z, "polished_blackstone_bricks" if y == 2 else
              ("andesite" if r == 0 else ("mossy_stone_bricks" if r == 5 else "stone_bricks")))
    else:
        d.set(x, y, z, st["base"] if y == 2 else st["wall"])


def netherworker_design(pack, rel, L):
    st = NW_STYLE[pack]
    d = Design(pack, rel, st["size"], gy=1, paving=st["paving"])
    X, Z = st["X"], st["Z"]
    big = L >= 3
    if big:
        x1, x2, z1, z2 = X, X + 16, Z + 3, Z + 12
    else:
        x1, x2, z1, z2 = X + 1, X + 14, Z + 4, Z + 12
    skin = big and pack != "Neoterra"
    zf = Z - 1 if skin else (Z if big else z1)                        # street face of the building
    # ---- hall shell: walls y2..9, ceiling/eave course y10 ----
    d.fill(x1, 1, zf, x2, 1, z2, st["floor"])
    for y in range(2, 11):
        for x in range(x1, x2 + 1):
            for z in range(zf, z2 + 1):
                edge = x in (x1, x2) or z in (zf, z2)
                if big and Z <= z <= Z + 2 and not (skin and z == zf):
                    continue                                          # the cluster's gallery
                if edge:
                    nw_wall(d, pack, x, y, z, st, "x" if z in (zf, z2) else "z")
                else:
                    d.set(x, y, z, AIR)
    for x in range(x1, x2 + 1):
        for z in range(zf, z2 + 1):
            if not (big and Z <= z <= Z + 2 and not (skin and z == zf)):
                d.set(x, 10, z, st["trim"] if pack != "Cascadia" else "spruce_planks")
    if pack == "Cascadia":
        for x, z in ((x1, zf), (x2, zf), (x1, z2), (x2, z2)):
            posts(d, [(x, z)], 2, 10, "stripped_spruce_log[axis=y]")
    if pack == "Hearthwood":                                          # buttresses
        for z in range(zf + 2, z2, 3):
            for x, f in ((x1 - 1, "east"), (x2 + 1, "west")):
                for y in range(2, 7):
                    d.set(x, y, z, "stone_bricks")
                d.set(x, 7, z, stair("stone_brick", f))
    # ---- roof ----
    if pack == "Neoterra":
        d.flat(x1, zf, x2, z2, 10, "smooth_quartz", "white_concrete", "smooth_quartz_slab")
        for x in range(x1, x2 + 1):
            d.set(x, 9, z2, st["trim"])
            if not big:
                d.set(x, 9, zf, st["trim"])
        if big:                                                       # keep the gallery's own roof edge
            for x in range(x1, x2 + 1):
                for z in range(Z, Z + 3):
                    for y in (11, 12):
                        d.set(x, y, z, AIR)
            for z in range(Z, Z + 3):
                for x in (x1, x2):
                    d.set(x, 11, z, "white_concrete")
        ridge = 11
    elif pack == "Hearthwood":
        ridge = d.gable(x1, zf, x2, z2, 11, "z", "deepslate_tile_stairs", "deepslate_tile_slab", "stone_bricks",
                        overhang=1)
        # bell-cote on the street gable
        mx = (x1 + x2) // 2
        for y in range(ridge - 2, ridge + 3):
            d.set(mx - 1, y, zf, "stone_bricks")
            d.set(mx + 1, y, zf, "stone_bricks")
        d.set(mx, ridge + 2, zf, "stone_bricks")
        d.set(mx, ridge + 3, zf, slab("stone_brick"))
        d.set(mx - 1, ridge + 3, zf, stair("stone_brick", "east"))
        d.set(mx + 1, ridge + 3, zf, stair("stone_brick", "west"))
        d.set(mx, ridge, zf, AIR)
        d.set(mx, ridge + 1, zf, "bell[attachment=ceiling,facing=north,powered=false]")
        # rose window
        for y in (12, 13):
            for x in (mx - 1, mx, mx + 1):
                d.set(x, y, zf, st["glass"])
    else:
        ridge = d.gable(x1, zf, x2, z2, 11, "x", "dark_oak_stairs", "dark_oak_slab", "spruce_planks", overhang=1)
        for x in (x1, x2):                                            # carved ridge posts (crossed gable ends)
            d.set(x, ridge + 1, (zf + z2) // 2, "stripped_spruce_log[axis=y]")
            d.set(x, ridge + 2, (zf + z2) // 2, "spruce_fence")
    # ---- openings ----
    mx = (x1 + x2) // 2
    if not big:
        d.door(X + 7, 2, z1, "south", st["wood"] if pack != "Neoterra" else "iron")
        d.door(X + 8, 2, z1, "south", st["wood"] if pack != "Neoterra" else "iron", "right")
        wins = [X + 3, X + 12]
    else:
        if skin:
            d.door(X + 8, 2, zf, "south", st["wood"])
            d.set(X + 8, 4, zf, st["trim"] if pack == "Hearthwood" else "stripped_spruce_log[axis=x]")
        wins = [X + 3, X + 13]
    for x in wins:
        if not big or skin:
            d.window(x, 4, zf, x, 7, zf, st["glass"])
    for z in range(z1 + 1, z2, 3):                                    # tall side windows
        for x in (x1, x2):
            d.window(x, 4, z, x, 7, z, st["glass"])
    if pack == "Hearthwood":
        for z in range(z1 + 1, z2, 3):
            for x in (x1, x2):
                d.set(x, 8, z, "chiseled_stone_bricks")
    # name sign
    names = {"Neoterra": ["PORTAL", "LAB"], "Hearthwood": ["Shrine of the", "Ember Gate"],
             "Cascadia": ["EMBER", "LODGE"]}
    if pack == "Neoterra":
        d.sign(X + 7 if not big else X + 6, 9 if not big else 9, zf - 1 if not big else Z - 1, "north", names[pack],
               "crimson", glow=True, color="red")
    else:
        d.sign(X + 6, 4, zf - 1, "north", names[pack], st["wood"])
    # ---- the functional cluster (portal chamber; from L3 with the glazed gallery) ----
    if big:
        d.cluster(X, Z)
    else:
        d.cluster(X + 5, Z + 8)
    if skin:                                                          # clad the gallery's glazed side ends
        for z in range(Z, Z + 3):
            for x in (x1 - 1, x2 + 1):
                for y in range(2, 11):
                    nw_wall(d, pack, x, y, z, st, "z")
                d.set(x, 1, z, st["floor"])
    if pack == "Neoterra":                                            # roof lantern over the portal chamber
        for x in range(X + 4, X + 12):
            for z in range(Z + 7, Z + 13):
                edge = x in (X + 4, X + 11) or z in (Z + 7, Z + 12)
                d.set(x, 11, z, "polished_blackstone_bricks" if edge else "tinted_glass")
        for x, z in ((X + 4, Z + 7), (X + 11, Z + 7), (X + 4, Z + 12), (X + 11, Z + 12)):
            d.set(x, 12, z, "end_rod[facing=up]")
    # ---- furnishing ----
    d.hut(X + 3, 2, Z + 9)
    if big:
        d.item(X + 2, 2, Z + 11, "blast_furnace", "east")
        d.item(X + 14, 2, Z + 11, "crafting_table")
        d.item(X + 13, 2, Z + 11, "crafting_table")
        rk = [(X + 15, 2, z) for z in range(Z + 4, Z + 10)] + [(X + 1, 2, z) for z in range(Z + 4, Z + 7)]
        racks(d, rk, d.req["racks"], "west")
        # braziers flanking the portal approach and benches facing it
        for x in (X + 5, X + 10):
            d.set(x, 2, Z + 6, f"{st['fire']}[facing=south,lit=true,signal_fire=false,waterlogged=false]")
        for x in range(X + 6, X + 10):
            d.set(x, 2, Z + 5, stair(st["wood"], "north"))
        d.rug(X + 6, Z + 6, X + 9, Z + 7, 2, ("red_carpet",), "plain")
        d.set(X + 2, 2, Z + 4, "lectern[facing=east,has_book=true,powered=false]")
        d.set(X + 12, 2, Z + 11, "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]")
        d.set(X + 14, 2, Z + 10, "cauldron")
        d.set(X + 2, 2, Z + 10, "magma_block")
        for x in range(X + 2, X + 15, 4):
            d.lamp(x, 9, Z + 6, "soul_lantern" if pack == "Neoterra" else "lantern")
    else:
        d.item(X + 2, 2, Z + 11, "furnace", "east")
        d.item(X + 13, 2, Z + 11, "crafting_table")
        rk = [(X + 13, 2, z) for z in range(Z + 5, Z + 9)]
        racks(d, rk, d.req["racks"], "west")
        for x in (X + 5, X + 10):
            d.set(x, 2, Z + 6, f"{st['fire']}[facing=south,lit=true,signal_fire=false,waterlogged=false]")
        d.set(X + 2, 2, Z + 5, "lectern[facing=east,has_book=true,powered=false]")
        d.set(X + 12, 2, Z + 11, "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]")
        d.rug(X + 6, Z + 5, X + 9, Z + 7, 2, ("red_carpet",), "plain")
        for x in (X + 3, X + 12):
            d.lamp(x, 9, Z + 7, "soul_lantern" if pack == "Neoterra" else "lantern")
    # candles on the portal sill corners
    d.set(X + 4 if not big else X + 4, 2, Z + 10, "polished_blackstone_bricks")
    d.candle(X + 4, 3, Z + 10, 3, "red")
    d.set(X + 11, 2, Z + 10, "polished_blackstone_bricks")
    d.candle(X + 11, 3, Z + 10, 3, "red")
    # ---- pack extras ----
    if pack == "Neoterra":
        if L >= 4:                                                    # east annex: sample lab
            ax1, ax2 = x2, x2 + 5
            d.box(ax1, 2, Z + 5, ax2, 5, Z + 12, "white_concrete", floor="polished_blackstone")
            d.flat(ax1, Z + 5, ax2, Z + 12, 6, "smooth_quartz", "white_concrete", "smooth_quartz_slab")
            for z in range(Z + 6, Z + 12, 2):
                d.window(ax2, 3, z, ax2, 4, z, "gray_stained_glass_pane")
            d.set(ax1, 2, Z + 10, AIR)
            d.set(ax1, 3, Z + 10, AIR)
            for z in range(Z + 6, Z + 12):
                d.set(ax2 - 1, 2, z, "smooth_quartz_slab[type=top,waterlogged=false]" if z % 2 else "crying_obsidian")
            d.set(ax2 - 1, 3, Z + 7, "brewing_stand[has_bottle_0=true,has_bottle_1=true,has_bottle_2=false]")
            d.set(ax1 + 2, 5, Z + 8, "sea_lantern")
        if L >= 5:                                                    # roof terrace with soul lights
            for x in range(x1 + 2, x2 - 1, 3):
                d.set(x, 11, Z + 4, "soul_lantern[hanging=false,waterlogged=false]")
                d.set(x + 1, 11, Z + 4, "potted_crimson_fungus")
            for x in (x1 + 1, x2 - 1):
                for z in range(Z + 7, z2):
                    d.set(x, 11, z, "polished_blackstone_slab[type=bottom,waterlogged=false]")
    if pack == "Hearthwood":
        if L >= 4:                                                    # sacristy lean-to on the east
            ax1, ax2 = x2 + 1, x2 + 5
            walls(d, ax1, z2 - 6, ax2, z2, 2, 5, "stone_bricks")
            d.fill(ax1 + 1, 1, z2 - 5, ax2 - 1, 1, z2 - 1, "deepslate_tiles")
            for i, x in enumerate(range(ax2 + 1, ax1 - 1, -1)):
                for z in range(z2 - 7, z2 + 2):
                    d.set(x, 6 + i, z, stair("deepslate_tile", "west"))
                if x <= ax2:
                    for z in (z2 - 6, z2):
                        for y in range(6, 6 + i):
                            d.set(x, y, z, "stone_bricks")
            d.set(x2, 2, z2 - 3, AIR)
            d.set(x2, 3, z2 - 3, AIR)
            d.set(x2 + 1, 2, z2 - 3, AIR)
            d.set(x2 + 1, 3, z2 - 3, AIR)
            for z in (z2 - 5, z2 - 1):
                d.set(ax2 - 1, 2, z, "chiseled_bookshelf[facing=west,slot_0_occupied=true,slot_1_occupied=true,"
                                     "slot_2_occupied=false,slot_3_occupied=true,slot_4_occupied=false,slot_5_occupied=true]")
            d.set(ax2 - 1, 2, z2 - 3, "dark_oak_stairs[facing=east,half=bottom,shape=straight,waterlogged=false]")
            d.window(ax2, 3, z2 - 3, ax2, 4, z2 - 3, "red_stained_glass_pane")
            d.lamp(ax1 + 2, 5, z2 - 3)
        if L >= 5:                                                    # walled herb garden with lanterns
            for z in range(zf, z2 + 1):
                if z % 3 == 0:
                    d.set(x1 - 2, 2, z, "stone_brick_wall")
                    d.set(x1 - 2, 3, z, "lantern[hanging=false,waterlogged=false]")
            d.set(x2 + 2, 2, zf, "stone_brick_wall")
            d.set(x2 + 2, 3, zf, "lantern[hanging=false,waterlogged=false]")
            d.set(x1 - 1, 2, zf - 1, "potted_crimson_roots")
    if pack == "Cascadia":
        if big:                                                       # deep porch across the front
            pz = zf - 3
            d.fill(x1, 1, pz, x2, 1, zf - 1, "spruce_planks")
            for x in (x1, X + 5, X + 11, x2):
                posts(d, [(x, pz)], 2, 6, "spruce_log[axis=y]")
            for x in range(x1 - 1, x2 + 2):
                d.set(x, 7, pz - 1, stair("dark_oak", "south"))
                for z in range(pz, zf):
                    d.set(x, 7, z, slab("dark_oak"))
            for x in range(x1 + 1, x2):
                if x not in (X + 5, X + 11, X + 8):
                    d.set(x, 2, pz, "spruce_fence")
            d.set(X + 2, 2, zf - 1, stair("spruce", "north"))
            d.set(X + 14, 2, zf - 1, "barrel[facing=up,open=false]")
            d.lamp(X + 8, 6, zf - 2)
        if L >= 4:                                                    # wood & coal lean-to on the west
            for z in range(z1 + 2, z2 + 1):
                for y in range(2, 5):
                    if z in (z1 + 2, z2):
                        d.set(x1 - 4, y, z, "spruce_log[axis=y]")
                d.set(x1 - 4, 5, z, slab("spruce"))
                for x in range(x1 - 3, x1):
                    d.set(x, 6 if x == x1 - 1 else 5, z, slab("spruce"))
                    if z % 2:
                        d.set(x, 2, z, "spruce_log[axis=x]" if x != x1 - 1 else "coal_block")
            d.set(x1 - 2, 3, z1 + 3, "spruce_log[axis=x]")
        if L >= 5:                                                    # fire pit ring out front
            fx, fz = x2 + 2, z1 + 2
            for dx, dz in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                d.set(fx + dx, 2, fz + dz, "mossy_cobblestone_slab[type=bottom,waterlogged=false]")
            d.set(fx, 2, fz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    return d


@design("netherworker")
def netherworker(pack, rel, L):
    return netherworker_design(pack, rel, L)


# ================================================================================================ FISHERMAN
def fish_items(d, smoker, craft, barrel, rack_cells, rack_facing="east"):
    d.item(*smoker[:3], "smoker", smoker[3])
    d.item(*craft, "crafting_table")
    d.item(*barrel, "barrel")
    racks(d, rack_cells, d.req["racks"], rack_facing)


def fisherman_neoterra(rel, L):
    d = Design("Neoterra", rel, (27, 14, 19), gy=1, paving="smooth_stone")
    cx, cz = 13, 1                                                    # pond 13..25 x 1..17, pier rows 8..9
    x1, x2, z1, z2 = 4, 12, 4, 13
    d.box(x1, 2, z1, x2, 5, z2, "white_concrete", floor="polished_diorite")
    d.fill(x1, 2, z1, x2, 2, z1, "light_gray_concrete")
    for z in range(z1 + 1, z2):                                       # glass wall to the water
        if z not in (8, 9):
            d.window(x2, 2, z, x2, 4, z, "glass_pane")
    for x in range(x1 + 1, x2):
        if x != 8:
            d.window(x, 3, z1, x, 4, z1)
    for z in range(z1 + 2, z2, 3):
        d.window(x1, 3, z, x1, 4, z)
    d.fill(x1, 5, z1, x2, 5, z1, "cyan_terracotta")
    d.fill(x2, 5, z1, x2, 5, z2, "cyan_terracotta")
    d.door(x2, 2, 8, "west", "birch")
    d.door(x2, 2, 9, "west", "birch", "right")
    d.door(8, 2, z1, "south", "birch")
    d.flat(x1, z1, x2, z2, 6, "smooth_quartz", "white_concrete", "smooth_quartz_slab")
    for z in range(6, 12):                                            # canopy over the pier door
        d.set(x2 + 0, 6, z, "smooth_quartz")
    d.sign(8, 5, z1 - 1, "north", ["HARBOUR", "MASTER"], "birch", glow=True, color="cyan")
    # ---- interior: tackle shop / fish prep ----
    d.hut(x1 + 1, 2, z1 + 1)
    fish_items(d, (6, 2, z2 - 1, "north"), (5, 2, z2 - 1), (7, 2, z2 - 1),
               [(x1 + 1, 2, z) for z in range(z1 + 3, z1 + 8)])
    d.set(8, 2, z2 - 1, "smooth_quartz_slab[type=top,waterlogged=false]")   # filleting counter
    d.set(9, 2, z2 - 1, "water_cauldron[level=3]")
    d.set(10, 2, z2 - 1, "smooth_quartz_slab[type=top,waterlogged=false]")
    d.set(10, 3, z2 - 1, "dried_kelp_block") if L >= 2 else None
    d.set(9, 2, z1 + 1, "barrel[facing=up,open=false]")              # bait barrels
    d.set(10, 2, z1 + 1, "barrel[facing=up,open=false]")
    d.set(8, 2, 7, "smooth_quartz_slab[type=top,waterlogged=false]")      # chart table
    d.chair(8, 2, 6, "north", "birch", sit=False)
    for x in (6, 9):
        d.set(x, 5, 8, "sea_lantern")
    d.plant(x2 - 1, 2, z1 + 1, "potted_bamboo")
    # ---- L2: south deck with benches and bollards ----
    if L >= 2:
        d.fill(x1, 1, z2 + 1, x2, 1, z2 + 4, "mangrove_planks")
        for x in range(x1, x2 + 1):
            d.set(x, 2, z2 + 4, "white_stained_glass_pane")
        for x in (x1 + 1, x1 + 4):
            d.chair(x, 2, z2 + 2, "west", "birch", sit=False)
            d.table(x + 1, 2, z2 + 2, "birch", "slab", "smooth_quartz_slab")
            d.chair(x + 2, 2, z2 + 2, "east", "birch", sit=False)
    # ---- L3: roof pavilion and terrace, reached by an outdoor stair ----
    if L >= 3:
        for i in range(5):
            d.set(x1 + 1 + i, 2 + i, z2 + 1, stair("smooth_quartz", "east"))
            for y in range(2, 2 + i):
                d.set(x1 + 1 + i, y, z2 + 1, "smooth_quartz")
        d.set(x1 + 6, 6, z2 + 1, "smooth_quartz")
        d.set(x1 + 6, 6, z2, "smooth_quartz")
        d.set(x1 + 6, 7, z2, AIR)
        d.set(x1 + 6, 8, z2, AIR)
        for x in range(x1, x2 + 1):                                   # glass railing instead of parapet
            for z in (z1, z2):
                d.set(x, 7, z, "white_stained_glass_pane")
                d.set(x, 8, z, AIR)
        for z in range(z1, z2 + 1):
            for x in (x1, x2):
                d.set(x, 7, z, "white_stained_glass_pane")
                d.set(x, 8, z, AIR)
        d.set(x1 + 6, 7, z2, AIR)
        px2, pz2 = x1 + 5, z1 + 5
        d.box(x1, 7, z1, px2, 9, pz2, "light_gray_stained_glass")
        for x, z in ((x1, z1), (px2, z1), (x1, pz2), (px2, pz2)):
            posts(d, [(x, z)], 7, 9, "white_concrete")
        d.flat(x1 - 1, z1 - 1, px2 + 1, pz2 + 1, 10, "smooth_quartz")
        d.door(x1 + 3, 7, pz2, "north", "birch")
        d.chair(x1 + 1, 7, z1 + 1, "north", "birch", sit=False)
        d.chair(x1 + 2, 7, z1 + 1, "north", "birch", sit=False)
        d.set(x1 + 4, 7, z1 + 1, "smooth_quartz_slab[type=top,waterlogged=false]")
        d.set(x1 + 4, 8, z1 + 1, "lantern[hanging=false,waterlogged=false]")
        d.plant(x1 + 1, 7, pz2 - 1, "potted_bamboo")
        for x in range(x1 + 1, px2, 2):
            d.set(x, 9, z1 + 2, "sea_lantern")
        for x in (8, 10):                                             # terrace loungers
            d.chair(x, 7, z1 + 8, "west", "birch", sit=False)
        d.set(x2 - 1, 7, z1 + 1, "azalea")
        d.set(x2 - 1, 7, z2 - 1, "azalea")
    if L >= 4:                                                        # street fish stall with awning
        for x in range(x1, x1 + 4):
            d.set(x, 2, z1 - 2, "smooth_quartz_slab[type=top,waterlogged=false]")
            d.set(x, 5, z1 - 2, "cyan_concrete" if x % 2 else "white_concrete")
            d.set(x, 5, z1 - 1, "cyan_concrete" if x % 2 else "white_concrete")
        posts(d, [(x1 - 1, z1 - 2)], 2, 5, "birch_fence")
        d.set(x1 + 1, 2, z1 - 3, "barrel[facing=up,open=false]")
        d.set(x1 + 2, 2, z1 - 3, "packed_ice")
    if L >= 5:                                                        # beacon mast at the deck corner
        posts(d, [(x2, z2 + 4)], 2, 9, "white_concrete")
        d.set(x2, 10, z2 + 4, "sea_lantern")
        d.set(x2, 11, z2 + 4, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        d.banner(x2, 8, z2 + 5, "south", "cyan")
    d.cluster(cx, cz)
    return d


def fisherman_hearthwood(rel, L):
    d = Design("Hearthwood", rel, (28, 20, 21), gy=1)
    cx, cz = 14, 2                                                    # pond 14..26 x 2..18, pier rows 9..10
    x1, x2, z1, z2 = 3, 13, 5, 14
    tall = L >= 3
    top = 9 if tall else 5
    beam = "stripped_dark_oak_log"
    d.box(x1, 2, z1, x2, top, z2, "calcite", floor="spruce_planks")
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if x in (x1, x2) or z in (z1, z2):
                d.set(x, 2, z, "bricks")
    for x in range(x1, x2 + 1, 2):                                    # timber framing
        for z in (z1, z2):
            for y in range(3, top + 1):
                d.set(x, y, z, logb(beam, "y"))
    for z in range(z1, z2 + 1, 3):
        for x in (x1, x2):
            for y in range(3, top + 1):
                d.set(x, y, z, logb(beam, "y"))
    for x in range(x1, x2 + 1):
        for z in (z1, z2):
            d.set(x, top, z, logb(beam, "x"))
            if tall:
                d.set(x, 6, z, logb(beam, "x"))
    for z in range(z1, z2 + 1):
        for x in (x1, x2):
            d.set(x, top, z, logb(beam, "z"))
            if tall:
                d.set(x, 6, z, logb(beam, "z"))
    if tall:
        d.fill(x1 + 1, 6, z1 + 1, x2 - 1, 6, z2 - 1, "spruce_planks")
    ridge = d.gable(x1, z1, x2, z2, top + 1, "z", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite",
                    overhang=1)
    # windows (leaded panes between studs) and doors
    for x in (x1 + 1, x2 - 1, x1 + 5):
        d.window(x, 3, z1, x, 4, z1)
    for z in (z1 + 2, z1 + 7):
        d.window(x2, 3, z, x2, 4, z)
        d.window(x1, 3, z, x1, 4, z)
    if tall:
        for x in (x1 + 3, x2 - 3):
            d.window(x, 7, z1, x, 8, z1)
            d.window(x, 7, z2, x, 8, z2)
    d.window((x1 + x2) // 2, top + 2, z1, (x1 + x2) // 2, top + 3, z1)
    d.door(x1 + 3, 2, z1, "south", "dark_oak")
    d.door(x2, 2, 9, "west", "dark_oak")
    d.door(x2, 2, 10, "west", "dark_oak", "right")
    for x in range(x1 + 1, x2, 4):                                    # flower boxes under the windows
        if d.get(x, 3, z1).endswith("glass_pane"):
            d.set(x, 2, z1 - 1, "dark_oak_trapdoor[facing=north,half=top,open=true,powered=false,waterlogged=false]")
    d.sign(x1 + 5, 5 if not tall else 6, z1 - 1, "north", ["The Silver", "Herring"], "dark_oak", hanging=False)
    # brick chimney on the west wall with the cooking hearth
    d.hearth(x1 + 1, 2, 11, "east", ridge + 1, "bricks", "campfire")
    for y in range(2, ridge + 2):
        d.set(x1 - 1, y, 11, "bricks")
        if y > top:
            d.set(x1, y, 11, "bricks")
    # ---- interior: fishmonger's kitchen ----
    d.hut(x1 + 1, 2, z1 + 1)
    fish_items(d, (x1 + 1, 2, z2 - 1, "east"), (x1 + 2, 2, z2 - 1), (x1 + 3, 2, z2 - 1),
               [(x, 2, z2 - 1) for x in range(x1 + 4, x1 + 9)], "north")
    for x in range(x1 + 4, x2 - 1):                                   # fish counter facing the door
        if x != x1 + 6:
            d.counter(x, z1 + 3, x, z1 + 3, 2, "dark_oak_slab")
    d.set(x1 + 6, 2, z1 + 3, "dark_oak_fence_gate[facing=east,in_wall=false,open=false,powered=false]")
    d.set(x2 - 1, 2, z1 + 1, "water_cauldron[level=3]")
    d.set(x2 - 1, 2, z1 + 2, "barrel[facing=up,open=false]")
    d.lamp(x1 + 5, top, z1 + 5)
    d.lamp(x1 + 5, top, z2 - 3) if not tall else d.lamp(x1 + 5, 5, z2 - 3)
    if tall:
        ladder(d, x2 - 1, z2 - 2, 2, 6, "west")
        d.set(x2 - 1, 6, z2 - 2, "ladder[facing=west,waterlogged=false]")
        # net loft upstairs
        for x in range(x1 + 1, x1 + 5):
            d.set(x, 7, z1 + 1, "cobweb")
        d.set(x1 + 2, 7, z2 - 1, "chest[facing=north,type=single,waterlogged=false]")
        d.set(x1 + 3, 7, z2 - 1, "barrel[facing=up,open=false]")
        d.set(x1 + 5, 7, z2 - 1, "dark_oak_slab[type=top,waterlogged=false]")
        d.candle(x1 + 5, 8, z2 - 1, 2)
        d.lamp(x1 + 5, 10, (z1 + z2) // 2)
        d.lamp(x1 + 5, 5, z1 + 5)
    # ---- L2: smokehouse behind ----
    if L >= 2:
        sx1, sx2, sz1, sz2 = 4, 8, 16, 19
        d.box(sx1, 2, sz1, sx2, 7, sz2, "bricks", floor="bricks")
        d.hip(sx1, sz1, sx2, sz2, 8, "deepslate_tile_stairs", "deepslate_tile_slab", overhang=1)
        for y in range(8, 12):
            d.set(6, y, 17, "bricks") if y > 9 else None
        d.door(6, 2, sz1, "south", "dark_oak")
        d.set(6, 2, z2, AIR)
        d.set(6, 3, z2, AIR)
        d.set(6, 2, z2 + 1, AIR)
        d.set(5, 2, 18, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        d.set(7, 2, 18, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        for x in (5, 6, 7):
            for z in (17, 18):
                d.set(x, 6, z, CHAIN)
                d.set(x, 5, z, "dried_kelp_block")
        d.set(6, 2, 18, "bricks")
    # ---- L4: net-drying frames along the street ----
    if L >= 4:
        for x in range(9, 14):
            d.set(x, 2, 2, "dark_oak_fence")
            d.set(x, 5, 2, "dark_oak_fence")
            if x in (9, 13):
                d.set(x, 3, 2, "dark_oak_fence")
                d.set(x, 4, 2, "dark_oak_fence")
            else:
                d.set(x, 3, 2, "cobweb")
                d.set(x, 4, 2, "cobweb")
    # ---- L5: fish stall with striped awning in front ----
    if L >= 5:
        for x in range(3, 7):
            d.set(x, 2, 2, "dark_oak_slab[type=top,waterlogged=false]")
            d.set(x, 5, 2, "red_wool" if x % 2 else "white_wool")
            d.set(x, 5, 1, "red_wool" if x % 2 else "white_wool")
        posts(d, [(3, 1), (6, 1)], 2, 4, "dark_oak_fence")
        d.set(4, 3, 2, "packed_ice")
        d.set(5, 3, 2, "barrel[facing=north,open=false]")
        d.set(7, 2, 2, "barrel[facing=up,open=false]")
        d.plant(2, 2, 4, "potted_red_tulip")
    d.cluster(cx, cz)
    return d


def fisherman_cascadia(rel, L):
    d = Design("Cascadia", rel, (30, 20, 22), gy=1, paving="coarse_dirt")
    cx, cz = 16, 3                                                    # pond 16..28 x 3..19, pier rows 10..11
    X1 = 6 if L < 3 else 2
    x1, x2, z1, z2 = X1, 15, 6, 15
    d.fill(x1, 1, z1, x2, 1, z2, "spruce_planks")
    for y in range(2, 6):
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                if x in (x1, x2) or z in (z1, z2):
                    if y == 2:
                        d.set(x, y, z, "mossy_cobblestone" if (x + z) % 3 == 0 else "cobblestone")
                    else:
                        d.set(x, y, z, logb("spruce_log", "x" if z in (z1, z2) else "z"))
                else:
                    d.set(x, y, z, AIR)
    for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        posts(d, [(x, z)], 2, 5, "stripped_spruce_log[axis=y]")
    ridge = d.gable(x1, z1, x2, z2, 6, "x", "spruce_stairs", "spruce_slab", "spruce_planks", overhang=1)
    for z in range(z1 + 1, z2):                                       # board-and-batten gables
        for x in (x1, x2):
            for y in range(6, ridge):
                if d.get(x, y, z) == "minecraft:spruce_planks" and z % 2 == 0:
                    d.set(x, y, z, "stripped_spruce_log[axis=y]")
    # big boat doors on the water gable
    for z in (10, 11):
        for y in (2, 3, 4):
            d.set(x2, y, z, AIR)
    d.set(x2, 5, 10, "stripped_spruce_log[axis=z]")
    d.set(x2, 5, 11, "stripped_spruce_log[axis=z]")
    for z in (9, 12):
        d.set(x2, 2, z, "stripped_spruce_log[axis=y]")
    d.window(x2, 7, 10, x2, 8, 11)
    d.door(x1 + 3, 2, z1, "south", "spruce")
    for x in range(x1 + 6, x2 - 1, 3):
        d.window(x, 3, z1, x, 4, z1)
        d.window(x, 3, z2, x, 4, z2)
    d.window(x1, 3, 9, x1, 4, 9)
    d.sign(x1 + 4, 5, z1 - 1, "north", ["SALMON", "RUN", "Fish Camp"], "spruce")
    # ---- interior: boat bay and tackle room ----
    d.hut(7, 2, z1 + 1)
    fish_items(d, (14, 2, z1 + 1, "west"), (13, 2, z1 + 1), (12, 2, z1 + 1),
               [(x, 2, z2 - 1) for x in range(14, 9, -1)], "north")
    # upturned canoe on trestles in the bay
    d.set(9, 2, 9, "spruce_fence")
    d.set(12, 2, 9, "spruce_fence")
    for x in range(9, 13):
        d.set(x, 3, 9, "spruce_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
    d.set(8, 2, z1 + 1, "barrel[facing=up,open=false]")
    d.set(9, 2, z1 + 1, "spruce_slab[type=top,waterlogged=false]")
    d.set(10, 2, z1 + 1, "water_cauldron[level=3]")
    for x in (8, 12):
        d.lamp(x, 5, 10)
    # stone chimney on the north wall with stove
    for y in range(2, ridge + 1):
        d.set(x1 + 1, y, z2 + 1, "mossy_cobblestone" if y % 3 == 0 else "cobblestone")
    d.set(x1 + 1, 2, z2, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    d.set(x1 + 1, 3, z2, "cobblestone")
    # ---- L2: porch along the street side ----
    if L >= 2:
        pz = z1 - 3
        d.fill(x1, 1, pz, x2, 1, z1 - 1, "spruce_planks")
        for x in (x1, x2, (x1 + x2) // 2):
            posts(d, [(x, pz)], 2, 5, "spruce_log[axis=y]")
        for x in range(x1 - 1, x2 + 2):
            d.set(x, 6, pz - 1, stair("spruce", "south"))
            for z in range(pz, z1):
                d.set(x, 6, z, slab("spruce"))
        for x in range(x1 + 1, x2):
            if x not in (x1 + 3, (x1 + x2) // 2):
                d.set(x, 2, pz, "spruce_fence")
        d.chair(x2 - 2, 2, z1 - 1, "south", "spruce", sit=False)
        d.chair(x2 - 3, 2, z1 - 1, "south", "spruce", sit=False)
        d.lamp(x1 + 3, 5, z1 - 2)
    # ---- L3: west end becomes the net loft / gear room ----
    if L >= 3:
        for z in range(z1 + 1, z2):
            d.set(6, 5, z, "spruce_planks")
        for x in range(x1 + 1, 6):
            for z in (z1 + 1, z1 + 2):
                d.set(x, 4, z, "cobweb")
        d.set(x1 + 1, 2, z2 - 1, "barrel[facing=up,open=false]")
        d.set(x1 + 2, 2, z2 - 1, "chest[facing=north,type=single,waterlogged=false]")
        d.set(x1 + 1, 2, 10, "spruce_slab[type=top,waterlogged=false]")
        d.set(x1 + 1, 3, 10, "lantern[hanging=false,waterlogged=false]")
    # ---- L4: smoke shack behind ----
    if L >= 4:
        sx1, sx2, sz1, sz2 = 3, 7, 17, 20
        d.box(sx1, 2, sz1, sx2, 4, sz2, "spruce_planks", floor="cobblestone")
        d.gable(sx1, sz1, sx2, sz2, 5, "z", "dark_oak_stairs", "dark_oak_slab", "spruce_planks", overhang=1)
        d.door(5, 2, sz1, "south", "spruce")
        d.set(5, 2, 19, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        for x in (4, 6):
            d.set(x, 4, 19, "dried_kelp_block")
            d.set(x, 4, 18, "dried_kelp_block")
    # ---- L5: drying racks and a canoe rack by the water ----
    if L >= 5:
        for x in range(9, 15):
            d.set(x, 2, 18, "spruce_fence")
            d.set(x, 4, 18, "spruce_fence")
            if x in (9, 14):
                d.set(x, 3, 18, "spruce_fence")
            else:
                d.set(x, 3, 18, "dried_kelp_block" if x % 2 else "cobweb")
        for x in range(9, 15):
            d.set(x, 2, 20, "stripped_spruce_log[axis=x]") if x in (9, 14) else None
        d.set(13, 2, 1, "spruce_fence")
        d.set(13, 3, 1, "lantern[hanging=false,waterlogged=false]")
    d.cluster(cx, cz)
    return d


@design("fisherman")
def fisherman(pack, rel, L):
    return {"Hearthwood": fisherman_hearthwood, "Cascadia": fisherman_cascadia,
            "Neoterra": fisherman_neoterra}[pack](rel, L)


# =============================================================================================== PLANTATION
def gambrel(d, x1, z1, x2, z2, y0, stairs, block, end, overhang=1):
    """Barn roof (ridge along z): steep lower slope, gentle upper slope. Wall tops at y0-1. Returns ridge y."""
    a1, a2 = x1 - overhang, x2 + overhang
    n = a2 - a1 + 1
    half = n // 2
    prof = [0, 2, 4, 5, 6, 7, 7, 8, 8, 9][:half]
    for i in range(half):
        for side in (0, 1):
            x = a1 + i if side == 0 else a2 - i
            face = "east" if side == 0 else "west"
            h = y0 + prof[i] - overhang
            top_cell = (i == half - 1 and n % 2 == 0)
            for z in range(z1 - overhang, z2 + overhang + 1):
                if top_cell:
                    d.set(x, h, z, block)
                else:
                    d.set(x, h, z, stair(stairs, face))
                lo = y0 + prof[i - 1] - overhang + 1 if i > 0 else h
                for y in range(lo, h):
                    d.set(x, y, z, block)
            # gable ends
            if x1 <= x <= x2:
                for z in (z1, z2):
                    for y in range(y0, h):
                        if d.air(x, y, z):
                            d.set(x, y, z, end)
    if n % 2 == 1:
        x = a1 + half
        h = y0 + prof[half - 1] - overhang + 1
        for z in range(z1 - overhang, z2 + overhang + 1):
            d.set(x, h, z, slab(stairs))
        for z in (z1, z2):
            for y in range(y0, h):
                if d.air(x, y, z):
                    d.set(x, y, z, end)
    return y0 + prof[half - 1] - overhang


def planter_row(d, x1, x2, z, y, crops=("wheat[age=7]", "carrots[age=7]", "potatoes[age=7]", "beetroots[age=3]")):
    for i, x in enumerate(range(x1, x2 + 1)):
        d.set(x, y - 1, z, "farmland[moisture=7]")
        d.set(x, y, z, crops[(i // 2) % len(crops)])


def plantation_neoterra(rel, L):
    d = Design("Neoterra", rel, (33, 14, 31), gy=1, paving="smooth_stone")
    d.cluster(0, 4)                                                   # beds 0..26 x 4..30
    x1, x2, z1, z2 = 22, 31, 1, 9
    d.box(x1, 2, z1, x2, 5, z2, "white_concrete", floor="polished_diorite")
    for x in range(x1 + 1, x2):                                       # glass curtain wall to the street
        if x not in (26, 27):
            d.window(x, 2, z1, x, 4, z1, "glass_pane")
    for z in range(z1 + 1, z2):
        d.window(x1, 3, z, x1, 4, z, "glass_pane")
    d.fill(x1, 5, z1, x2, 5, z1, "lime_terracotta")
    d.double_door(26, 2, z1, "x", "south", "birch")
    d.flat(x1, z1, x2, z2, 6, "smooth_quartz", "white_concrete", "smooth_quartz_slab")
    for x in range(25, 29):
        d.set(x, 5, z1 - 1, "smooth_quartz_slab[type=top,waterlogged=false]")
    d.sign(24, 4, z1 - 1, "north", ["AGRI", "LAB"], "birch", glow=True, color="lime")
    # office: seed bank and sample bench
    d.hut(x1 + 1, 2, z1 + 1)
    racks(d, [(x2 - 1, 2, z) for z in range(z1 + 2, z2)], d.req["racks"], "west")
    for x in range(x1 + 1, x1 + 5):
        d.set(x, 2, z2 - 1, "smooth_quartz_slab[type=top,waterlogged=false]")
    d.set(x1 + 1, 3, z2 - 1, "potted_cactus")
    d.set(x1 + 2, 3, z2 - 1, "potted_bamboo")
    d.set(x1 + 3, 3, z2 - 1, "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]")
    d.chair(x1 + 2, 2, z2 - 2, "north", "birch", sit=False)
    d.set(x1 + 1, 2, z1 + 4, "barrel[facing=up,open=false]")
    d.set(x1 + 1, 2, z1 + 5, "barrel[facing=up,open=false]")
    d.set(x1 + 5, 2, z1 + 4, "smooth_quartz_slab[type=top,waterlogged=false]")
    d.set(x1 + 5, 2, z1 + 5, "smooth_quartz_slab[type=top,waterlogged=false]")
    d.chair(x1 + 4, 2, z1 + 4, "west", "birch", sit=False)
    for x in (x1 + 3, x1 + 7):
        d.set(x, 5, z1 + 4, "sea_lantern")
    # side door toward the beds
    d.door(x1, 2, z2 - 1, "east", "birch")
    if L >= 2:                                                        # planters along the street front
        for x in range(x1, x2 + 1):
            if x not in (25, 26, 27, 28):
                d.set(x, 1, z1 - 1, "moss_block")
                d.set(x, 2, z1 - 1, "azalea" if x % 3 == 0 else "fern")
    if L >= 3:                                                        # hydroponic greenhouse wing
        gz2 = 14
        for y in range(2, 6):
            for x in range(x1, x2 + 1):
                for z in range(z2, gz2 + 1):
                    edge = x in (x1, x2) or z in (z2, gz2)
                    if z == z2:
                        continue
                    if edge:
                        corner = x in (x1, x2) and z == gz2
                        d.set(x, y, z, "white_concrete" if corner or y == 2 else "glass")
                    else:
                        d.set(x, y, z, AIR)
        d.fill(x1 + 1, 6, z2 + 1, x2 - 1, 6, gz2 - 1, "light_blue_stained_glass")
        for x in range(x1, x2 + 1):
            d.set(x, 6, gz2, "white_concrete")
        for z in range(z2, gz2 + 1):
            d.set(x1, 6, z, "white_concrete")
            d.set(x2, 6, z, "white_concrete")
        d.fill(x1 + 1, 1, z2 + 1, x2 - 1, 1, gz2 - 1, "polished_diorite")
        for z in (z2 + 1, z2 + 3):
            planter_row(d, x1 + 2, x2 - 2, z, 2, ("carrots[age=7]", "beetroots[age=3]"))
        d.set(x1 + 1, 2, z2 + 1, "composter[level=4]")
        d.set(x2 - 1, 2, gz2 - 1, "water_cauldron[level=3]")
        d.door(27, 2, z2, "south", "birch")
        d.set(27, 1, z2 + 1, "polished_diorite")
        d.set(27, 2, z2 + 1, AIR)
        d.set(27, 1, z2 + 3, "polished_diorite")
        d.set(27, 2, z2 + 3, AIR)
        for x in range(x1 + 2, x2 - 1, 3):
            d.set(x, 5, z2 + 2, "end_rod[facing=down]")
    if L >= 4:                                                        # solar array on the office roof
        for x in range(x1 + 1, x2, 2):
            for z in range(z1 + 2, z2 - 1):
                d.set(x, 7, z, "daylight_detector[inverted=false,power=0]")
    if L >= 5:                                                        # seed vault & packing annex on the east
        ax1, ax2, az1, az2 = 27, 32, 16, 23
        d.box(ax1, 2, az1, ax2, 5, az2, "white_concrete", floor="polished_diorite")
        d.flat(ax1, az1, ax2, az2, 6, "smooth_quartz", "white_concrete", "smooth_quartz_slab")
        d.fill(ax1, 5, az1, ax2, 5, az1, "lime_terracotta")
        d.door(29, 2, az1, "south", "birch")
        for z in range(az1 + 2, az2, 2):
            d.window(ax1, 3, z, ax1, 4, z, "glass_pane")
        d.set(ax2 - 1, 2, az2 - 1, "bamboo_block[axis=y]")
        d.set(ax2 - 1, 3, az2 - 1, "bamboo_block[axis=y]")
        d.set(ax2 - 2, 2, az2 - 1, "bamboo_block[axis=y]")
        d.set(ax2 - 1, 2, az2 - 2, "barrel[facing=up,open=false]")
        d.set(ax1 + 1, 2, az2 - 1, "potted_cactus")
        d.set(29, 5, az1 + 3, "sea_lantern")
        for z in range(15, 16):
            d.set(29, 1, z, "smooth_stone")
    return d


def lean_glass(d, xa, xb, za, zb, ends=(True, True)):
    """Victorian lean-to glasshouse along x: brick back wall at za (street), glass slope down to a low brick wall at
    zb (south, toward the beds). Inside: a staging bench along the back wall and an aisle."""
    depth = zb - za                                                   # rows za+1..zb
    top = 4 + depth                                                   # back wall height
    for x in range(xa, xb + 1):
        for y in range(2, top + 1):
            d.set(x, y, za, "bricks")
        d.set(x, top + 1, za, slab("brick"))
        for i, z in enumerate(range(zb, za, -1)):
            ry = 5 + i
            d.set(x, ry, z, "glass" if x % 3 else stair("dark_oak", "north"))
            for y in range(2, ry):
                if z == zb:
                    d.set(x, y, z, "bricks" if y == 2 else "glass_pane")
                else:
                    d.set(x, y, z, AIR)
    for x, on in ((xa, ends[0]), (xb, ends[1])):
        if not on:
            continue
        for i, z in enumerate(range(zb, za, -1)):
            for y in range(2, 5 + i):
                d.set(x, y, z, "bricks")
    d.fill(xa, 1, za + 1, xb, 1, zb - 1, "bricks")
    for x in range(xa + 1, xb):                                      # staging bench with seedlings
        if d.air(x, 2, za + 1):
            d.set(x, 2, za + 1, "dark_oak_slab[type=top,waterlogged=false]")
            d.set(x, 3, za + 1, ("potted_cactus", "potted_fern", "potted_bamboo", "potted_red_tulip")[x % 4])
    d.fill(xa, 2 + 0, za, xb, 2, za, "bricks")


def plantation_hearthwood(rel, L):
    d = Design("Hearthwood", rel, (31, 18, 33), gy=1)
    d.cluster(2, 6)                                                   # beds 2..28 x 6..32
    beam = "stripped_dark_oak_log"
    x1, x2, z1, z2 = 11, 16, 1, 12
    # potting shed: brick plinth, plaster and dark-oak frame, gable to the street
    d.box(x1, 2, z1, x2, 5, z2, "calcite", floor="spruce_planks")
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if x in (x1, x2) or z in (z1, z2):
                d.set(x, 2, z, "bricks")
    for z in range(z1, z2 + 1, 3):
        for x in (x1, x2):
            posts(d, [(x, z)], 3, 5, logb(beam, "y"))
    for x in (x1, x2):
        for z in (z1, z2):
            posts(d, [(x, z)], 3, 5, logb(beam, "y"))
    for z in range(z1, z2 + 1):
        d.set(x1, 5, z, logb(beam, "z"))
        d.set(x2, 5, z, logb(beam, "z"))
    ridge = d.gable(x1, z1, x2, z2, 6, "z", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite", overhang=1)
    for z in (z1, z2):
        for x in range(x1, x2 + 1):
            d.set(x, 5, z, logb(beam, "x"))
        for y in range(6, ridge):
            d.set((x1 + x2) // 2, y, z, logb(beam, "y")) if d.get((x1 + x2) // 2, y, z) == "minecraft:calcite" else None
    d.door(13, 2, z1, "south", "dark_oak")
    d.window(15, 3, z1, 15, 4, z1)
    d.window(13, 6, z1, 14, 6, z1)
    for z in (4, 7, 10):
        d.window(x1, 3, z - 1, x1, 4, z - 1) if z != 4 else None
    d.window(x2, 3, 8, x2, 4, 8)
    d.window(x2, 3, 10, x2, 4, 10)
    d.door(13, 2, z2, "north", "dark_oak")
    d.sign(12, 4, z1 - 1, "north", ["Kitchen", "Garden"], "dark_oak")
    d.set(15, 2, z1 - 1, "potted_red_tulip")
    # inside: potting bench, seed drawers, racks, sink
    d.hut(x1 + 1, 2, z1 + 1)
    racks(d, [(x1 + 1, 2, z) for z in range(z1 + 4, z1 + 9)], d.req["racks"], "east")
    for z in range(z1 + 4, z1 + 9):
        d.set(x2 - 1, 2, z, "dark_oak_slab[type=top,waterlogged=false]" if z != z1 + 6 else "water_cauldron[level=3]")
        if z in (z1 + 4, z1 + 8):
            d.set(x2 - 1, 3, z, "flower_pot")
        if z == z1 + 5:
            d.set(x2 - 1, 3, z, "potted_cactus")
    d.set(x2 - 1, 2, z2 - 1, "barrel[facing=up,open=false]")
    d.set(x2 - 2, 2, z2 - 1, "barrel[facing=up,open=false]")
    d.set(x1 + 1, 2, z2 - 1, "composter[level=6]")
    d.lamp(13, 5, 4)
    d.lamp(13, 5, 9)
    if L >= 2:                                                        # glasshouse east of the shed
        xb = 22 if L == 2 else 28
        lean_glass(d, x2, xb, z1, 5, ends=(False, True))
        d.door(x2, 2, 3, "east", "dark_oak")
        racks_extra = []
    if L >= 4:                                                        # glasshouse west of the shed
        lean_glass(d, 2, x1, z1, 5, ends=(True, False))
        d.door(x1, 2, 3, "west", "dark_oak")
    if L >= 5:                                                        # espaliered fruit on the back walls, gate
        for x in list(range(4, 10, 2)) + list(range(18, 28, 3)):
            d.set(x, 4, 0, "oak_leaves[distance=7,persistent=true,waterlogged=false]")
            d.set(x, 5, 0, "oak_leaves[distance=7,persistent=true,waterlogged=false]")
            d.set(x - 1, 4, 0, "oak_leaves[distance=7,persistent=true,waterlogged=false]")
            d.set(x + 1, 4, 0, "oak_leaves[distance=7,persistent=true,waterlogged=false]")
        for x in (12, 15):
            posts(d, [(x, 0)], 2, 3, "bricks")
            d.set(x, 4, 0, "lantern[hanging=false,waterlogged=false]")
    return d


def plantation_cascadia(rel, L):
    d = Design("Cascadia", rel, (33, 20, 33), gy=1, paving="coarse_dirt")
    d.cluster(0, 6)                                                   # beds 0..26 x 6..32
    x1, x2, z1 = 22, 31, 3
    big = L >= 3
    z2 = 14 if big else 9
    d.fill(x1, 1, z1, x2, 1, z2, "spruce_planks")
    for y in range(2, 7):
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                if x in (x1, x2) or z in (z1, z2):
                    if y == 2:
                        d.set(x, y, z, "cobblestone" if (x + z) % 4 else "mossy_cobblestone")
                    else:
                        d.set(x, y, z, "spruce_planks" if (x if z in (z1, z2) else z) % 2 else "stripped_spruce_log[axis=y]")
                else:
                    d.set(x, y, z, AIR)
    for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        posts(d, [(x, z)], 2, 6, "spruce_log[axis=y]")
    if big:
        d.fill(x1 + 1, 7, z1 + 4, x2 - 1, 7, z2 - 1, "spruce_planks")         # hay loft
        ridge = gambrel(d, x1, z1, x2, z2, 7, "dark_oak", "dark_oak_planks", "spruce_planks")
        # loft door and hay hood on the street gable
        d.set(26, 9, z1, AIR)
        d.set(27, 9, z1, AIR)
        d.set(26, 10, z1, AIR)
        d.set(27, 10, z1, AIR)
        d.set(26, 9, z1, "spruce_trapdoor[facing=north,half=bottom,open=true,powered=false,waterlogged=false]")
        d.set(27, 9, z1, "spruce_trapdoor[facing=north,half=bottom,open=true,powered=false,waterlogged=false]")
    else:
        ridge = d.gable(x1, z1, x2, z2, 7, "z", "dark_oak_stairs", "dark_oak_slab", "spruce_planks", overhang=1)
    # sliding barn doors (open) and windows
    for x in (26, 27):
        for y in (2, 3, 4):
            d.set(x, y, z1, AIR)
    d.set(25, 5, z1, "stripped_spruce_log[axis=x]")
    d.set(28, 5, z1, "stripped_spruce_log[axis=x]")
    for x in (25, 28):
        for y in (2, 3, 4):
            d.set(x, y, z1, "spruce_planks")
    for z in range(z1 + 2, z2, 3):
        d.window(x2, 3, z, x2, 4, z)
    d.door(x1, 2, z1 + 3, "east", "spruce")
    # farm stand on the street: produce crates under a shed roof
    sz = z1 - 3
    for x in range(x1 - 1, x2 + 2):
        d.set(x, 6, sz - 1 if sz - 1 >= 0 else sz, stair("spruce", "south")) if sz - 1 >= 0 else None
    for x in range(x1, x2 + 1):
        for z in range(max(sz, 0), z1):
            d.set(x, 6, z, slab("spruce"))
    posts(d, [(x1, 0), (x2, 0)], 2, 5, "spruce_log[axis=y]")
    for x, b in ((x1 + 1, "melon"), (x1 + 2, "pumpkin"), (x2 - 2, "hay_block[axis=y]"), (x2 - 1, "melon")):
        d.set(x, 2, 1, "spruce_slab[type=top,waterlogged=false]")
        d.set(x, 2, 0, b)
    d.set(x1 + 3, 2, 1, "barrel[facing=up,open=false]")
    d.set(x2 - 3, 2, 1, "barrel[facing=up,open=false]")
    d.sign(24, 5, z1 - 1, "north", ["CEDAR CREEK", "FARM STAND"], "spruce")
    d.lamp(26, 5, 1)
    # interior: bundles of cane & bamboo, racks, tool corner
    d.hut(x1 + 1, 2, z1 + 1)
    racks(d, [(x2 - 1, 2, z) for z in range(z1 + 1, z1 + 6)], d.req["racks"], "west")
    for z in (z1 + 4, z1 + 5):
        d.set(x1 + 1, 2, z, "bamboo_block[axis=y]")
        d.set(x1 + 1, 3, z, "bamboo_block[axis=y]")
    d.set(x1 + 2, 2, z1 + 5, "bamboo_block[axis=x]")
    d.set(x1 + 1, 2, z1 + 2, "barrel[facing=up,open=false]")
    d.set(28, 2, z1 + 4, "spruce_fence")
    d.set(28, 3, z1 + 4, "spruce_pressure_plate[powered=false]")
    d.lamp(26, 6, z1 + 3)
    if big:
        for z in range(z1 + 8, z2):
            d.set(x1 + 1, 2, z, "hay_block[axis=z]")
            d.set(x1 + 1, 3, z, "hay_block[axis=z]") if z % 2 else None
        for x in range(x1 + 1, x2):
            for z in (z2 - 1,):
                d.set(x, 8, z, "hay_block[axis=x]")
        ladder(d, x2 - 1, z2 - 1, 2, 7, "west")
        d.lamp(26, 6, z2 - 3)
        d.set(26, 2, z2 - 2, "grindstone[face=floor,facing=north]")
        d.set(27, 2, z2 - 1, "crafting_table")
    if L >= 4:                                                        # lean-to cane drying shed on the east band
        for z in range(z1 + 2, z2 + 1, 3):
            posts(d, [(32, z)], 2, 4, "spruce_log[axis=y]")
        for z in range(z1 + 1, z2 + 1):
            d.set(32, 5, z, slab("spruce"))
            if z % 3 != (z1 + 2) % 3:
                d.set(32, 2, z, "bamboo_block[axis=z]" if z % 2 else "hay_block[axis=y]")
    if L >= 5:                                                        # water tower by the beds
        tx, tz = 17, 1
        posts(d, [(tx, tz), (tx + 3, tz), (tx, tz + 3), (tx + 3, tz + 3)], 2, 8, "spruce_log[axis=y]")
        for x in range(tx, tx + 4):
            for z in range(tz, tz + 4):
                d.set(x, 9, z, "spruce_planks")
                corner = x in (tx, tx + 3) and z in (tz, tz + 3)
                for y in (10, 11, 12):
                    if not corner and (x in (tx, tx + 3) or z in (tz, tz + 3)):
                        d.set(x, y, z, "stripped_spruce_log[axis=y]" if y != 11 else "spruce_planks")
                    elif not corner:
                        d.set(x, y, z, "water")
        d.hip(tx, tz, tx + 3, tz + 3, 13, "dark_oak_stairs", "dark_oak_slab", overhang=0)
        for x in (tx + 1, tx + 2):
            d.set(x, 5, tz, "spruce_fence")
    return d


@design("plantation")
def plantation(pack, rel, L):
    return {"Hearthwood": plantation_hearthwood, "Cascadia": plantation_cascadia,
            "Neoterra": plantation_neoterra}[pack](rel, L)


# ================================================================================================== FARMER
def compost_bay(d, x, y, z, along="x"):
    """Three composters side by side (the hut's work blocks)."""
    dx, dz = (1, 0) if along == "x" else (0, 1)
    for i in range(3):
        d.item(x + dx * i, y, z + dz * i, "composter")


def farmer_hearthwood(rel, L):
    d = Design("Hearthwood", rel, (25, 17, 23), gy=1)
    beam = "stripped_dark_oak_log"
    x1, x2, z1, z2 = 2, 11, 3, 9
    tall = L >= 4
    top = 9 if tall else 5
    d.box(x1, 2, z1, x2, top, z2, "calcite", floor="oak_planks")
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if x in (x1, x2) or z in (z1, z2):
                d.set(x, 2, z, "stone_bricks")
    # lower storey brick, upper timber framing when two storeys
    if tall:
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                if x in (x1, x2) or z in (z1, z2):
                    for y in range(3, 6):
                        d.set(x, y, z, "bricks")
        d.fill(x1 + 1, 6, z1 + 1, x2 - 1, 6, z2 - 1, "oak_planks")
    for x in range(x1, x2 + 1, 3):
        for z in (z1, z2):
            for y in range(6 if tall else 3, top + 1):
                d.set(x, y, z, logb(beam, "y"))
    for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        posts(d, [(x, z)], 3, top, logb(beam, "y"))
    for x in range(x1, x2 + 1):
        for z in (z1, z2):
            d.set(x, top, z, logb(beam, "x"))
    ridge = d.gable(x1, z1, x2, z2, top + 1, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite",
                    overhang=1)
    for z in range(z1, z2 + 1):
        for x in (x1, x2):
            d.set(x, top, z, logb(beam, "z"))
    d.door(6, 2, z1, "south", "dark_oak")
    for x in (4, 9):
        d.window(x, 3, z1, x, 4, z1)
        d.window(x, 3, z2, x, 4, z2)
    if tall:
        for x in (3, 5, 8, 10):
            d.window(x, 7, z1, x, 8, z1)
        d.window(x1, 7, 6, x1, 8, 6)
    d.window(x1, 3, 6, x1, 4, 6)
    for x in (4, 9):                                                  # flower boxes
        d.set(x, 2, z1 - 1, "potted_red_tulip" if x == 4 else "potted_oxeye_daisy")
    # brick chimney + farmhouse range on the east gable
    d.hearth(x2 - 1, 2, 6, "west", ridge + 2, "bricks", "campfire")
    for y in range(2, ridge + 3):
        d.set(x2 + 1, y, 6, "bricks")
        if y > top:
            d.set(x2, y, 6, "bricks")
    d.set(x2 - 1, 3, 6, "bricks")
    d.sign(5, 4, z1 - 1, "north", ["Meadowbrook", "Farm"], "dark_oak")
    # ---- farmhouse kitchen ----
    d.hut(x1 + 1, 2, z1 + 1)
    d.item(x1 + 1, 2, z2 - 1, "crafting_table")
    d.set(x1 + 2, 2, z2 - 1, "oak_slab[type=top,waterlogged=false]")
    d.set(x1 + 3, 2, z2 - 1, "water_cauldron[level=3]")
    d.dining(5, 2, 6, 2, "x", "oak", chairs=("n", "s"), sit=False)
    rk = [(x1 + 1, 2, z) for z in (z1 + 3, z1 + 4)] + [(x, 2, z1 + 1) for x in (8, 9, 10)]
    racks(d, rk, min(d.req["racks"], 2 if L < 2 else 2))
    d.lamp(6, top if not tall else 5, 6)
    if tall:
        ladder(d, x2 - 1, z1 + 1, 2, 6, "west")
        # bedroom-free loft: seed store and spinning corner
        d.set(x1 + 1, 7, z1 + 1, "barrel[facing=up,open=false]")
        d.set(x1 + 1, 7, z1 + 2, "barrel[facing=up,open=false]")
        d.set(x1 + 1, 7, z2 - 1, "loom[facing=east]")
        d.chair(x1 + 2, 7, z2 - 1, "south", "oak", sit=False)
        d.set(5, 7, z2 - 1, "hay_block[axis=x]")
        d.set(6, 7, z2 - 1, "hay_block[axis=x]")
        d.lamp(6, 10, 6)
    # ---- yard behind: compost bay and kitchen garden ----
    compost_bay(d, 3, 2, 12)
    for x in range(2, 12):
        d.set(x, 2, 18, "oak_fence")
    for z in range(13, 19):
        d.set(2, 2, z, "oak_fence")
        d.set(11, 2, z, "oak_fence")
    for x in range(3, 11):
        for z in range(14, 18):
            if x == 6:
                d.set(x, 1, z, "water") if z == 15 else d.set(x, 1, z, "gravel")
                continue
            d.set(x, 1, z, "farmland[moisture=7]")
            d.set(x, 2, z, ("carrots[age=7]", "potatoes[age=7]", "wheat[age=7]")[x % 3])
    d.door(6, 2, z2, "north", "dark_oak")
    d.set(8, 2, 12, "oak_fence")
    d.set(8, 3, 12, "lantern[hanging=false,waterlogged=false]")
    # ---- L2: tool shed ----
    if L >= 2:
        sx1, sx2, sz1, sz2 = 13, 17, 3, 7
        d.box(sx1, 2, sz1, sx2, 4, sz2, "dark_oak_planks", floor="oak_planks")
        for x, z in ((sx1, sz1), (sx2, sz1), (sx1, sz2), (sx2, sz2)):
            posts(d, [(x, z)], 2, 4, logb(beam, "y"))
        d.gable(sx1, sz1, sx2, sz2, 5, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "dark_oak_planks")
        d.door(15, 2, sz1, "south", "dark_oak")
        d.window(sx2, 3, 5, sx2, 3, 5)
        d.set(sx1 + 1, 2, sz2 - 1, "grindstone[face=floor,facing=north]")
        rk2 = [(x, 2, sz2 - 1) for x in (sx1 + 2, sx1 + 3)] + [(sx1 + 1, 2, sz1 + 1)]
        racks(d, rk2, d.req["racks"] - 2)
        d.set(sx2 - 1, 2, sz1 + 1, "barrel[facing=up,open=false]")
        d.set(sx2 - 1, 3, sz1 + 1, "lantern[hanging=false,waterlogged=false]")
    # ---- L3: barn with grain barrels ----
    if L >= 3:
        bx1, bx2, bz1, bz2 = 13, 22, 10, 20
        d.box(bx1, 2, bz1, bx2, 6, bz2, "dark_oak_planks", floor="spruce_planks")
        for x in range(bx1, bx2 + 1):
            for z in range(bz1, bz2 + 1):
                if x in (bx1, bx2) or z in (bz1, bz2):
                    d.set(x, 2, z, "stone_bricks")
                    if (x in (bx1, bx2) and z % 3 == 1) or (z in (bz1, bz2) and x % 3 == 1):
                        for y in range(3, 7):
                            d.set(x, y, z, logb("dark_oak_log", "y"))
        rb = d.gable(bx1, bz1, bx2, bz2, 7, "z", "deepslate_tile_stairs", "deepslate_tile_slab", "dark_oak_planks",
                     overhang=1)
        for x in (17, 18):                                            # cart doors facing the yard
            for y in (2, 3, 4):
                d.set(x, y, bz1, AIR)
        d.set(16, 2, bz1 - 1, "dark_oak_fence_gate[facing=west,in_wall=false,open=true,powered=false]")
        d.set(19, 2, bz1 - 1, "dark_oak_fence_gate[facing=east,in_wall=false,open=true,powered=false]")
        d.window(17, 8, bz1, 18, 9, bz1)
        for i, z in enumerate((bz1 + 2, bz1 + 3, bz1 + 4, bz1 + 5)):
            d.item(bx2 - 1, 2, z, "barrel")
        for z in range(bz1 + 2, bz2 - 1):
            d.set(bx1 + 1, 2, z, "hay_block[axis=z]")
            if z % 2:
                d.set(bx1 + 1, 3, z, "hay_block[axis=z]")
        d.set(17, 2, bz2 - 2, "spruce_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
        d.set(18, 2, bz2 - 2, "spruce_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
        d.set(16, 2, bz2 - 2, "spruce_fence")
        d.set(19, 2, bz2 - 2, "spruce_fence")                         # hay wain
        d.set(17, 3, bz2 - 2, "hay_block[axis=x]")
        racks(d, [(bx2 - 1, 2, z) for z in range(bz1 + 7, bz2)], max(0, d.req["racks"] - 5))
        for z in (bz1 + 3, bz2 - 3):
            d.lamp(17, 6, z)
    # ---- L5: well and duck pond ----
    if L >= 5:
        wx, wz = 20, 4
        for dx in range(3):
            for dz in range(3):
                d.set(wx + dx, 2, wz + dz, "cobblestone" if (dx, dz) != (1, 1) else "water")
        d.set(wx + 1, 1, wz + 1, "water")
        posts(d, [(wx, wz + 1), (wx + 2, wz + 1)], 3, 4, "dark_oak_fence")
        for dx in range(3):
            d.set(wx + dx, 5, wz + 1, slab("deepslate_tile"))
        d.set(wx + 1, 4, wz + 1, CHAIN)
    return d


def farmer_cascadia(rel, L):
    d = Design("Cascadia", rel, (27, 20, 25), gy=1, paving="coarse_dirt")
    x1, x2, z1, z2 = 3, 11, 5, 12
    d.fill(x1, 1, z1, x2, 1, z2, "spruce_planks")
    for y in range(2, 6):
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                if x in (x1, x2) or z in (z1, z2):
                    if y == 2:
                        d.set(x, y, z, "cobblestone" if (x + z) % 3 else "mossy_cobblestone")
                    else:
                        d.set(x, y, z, logb("spruce_log", "x" if z in (z1, z2) else "z"))
                else:
                    d.set(x, y, z, AIR)
    for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        posts(d, [(x, z)], 2, 5, "stripped_spruce_log[axis=y]")
    ridge = d.gable(x1, z1, x2, z2, 6, "z", "spruce_stairs", "spruce_slab", "stripped_spruce_log[axis=y]", overhang=1)
    mid = (x1 + x2) // 2
    d.door(mid, 2, z1, "south", "spruce")
    for x in (x1 + 2, x2 - 2):
        d.window(x, 3, z1, x, 4, z1)
    d.window(mid, 7, z1, mid, 8, z1)
    for z in (z1 + 2, z2 - 2):
        d.window(x1, 3, z, x1, 4, z)
    d.window(x2, 3, z2 - 2, x2, 4, z2 - 2)
    # porch
    pz = z1 - 3
    d.fill(x1, 1, pz, x2, 1, z1 - 1, "spruce_planks")
    for x in (x1, x2):
        posts(d, [(x, pz)], 2, 5, "spruce_log[axis=y]")
    for x in range(x1 - 1, x2 + 2):
        d.set(x, 6, pz - 1, stair("spruce", "south"))
        for z in range(pz, z1):
            d.set(x, 6, z, slab("spruce"))
    for x in range(x1 + 1, x2):
        if x != mid:
            d.set(x, 2, pz, "spruce_fence")
    d.chair(x1 + 1, 2, z1 - 1, "south", "spruce", sit=False)
    d.chair(x2 - 1, 2, z1 - 1, "south", "spruce", sit=False)
    d.lamp(mid, 5, z1 - 2)
    d.sign(mid - 2, 4, z1 - 1, "north", ["Elk Ridge", "Homestead"], "spruce")
    # stone chimney on the west wall
    for y in range(2, ridge + 2):
        d.set(x1 - 1, y, 9, "mossy_cobblestone" if y % 3 == 0 else "cobblestone")
    d.hearth(x1 + 1, 2, 9, "east", 4, "cobblestone", "campfire")
    # ---- cabin interior ----
    d.hut(x2 - 1, 2, z1 + 1)
    d.item(x2 - 1, 2, z2 - 1, "crafting_table")
    d.set(x2 - 2, 2, z2 - 1, "spruce_slab[type=top,waterlogged=false]")
    d.set(x2 - 3, 2, z2 - 1, "smoker[facing=north,lit=false]")
    d.dining(6, 2, 7, 2, "z", "spruce", chairs=("e", "w"), sit=False)
    racks(d, [(x2 - 1, 2, z) for z in (z1 + 3, z1 + 4)], 2)
    d.rug(5, 6 + 0, 8, 10, 2, ("brown_carpet",), "plain")
    d.lamp(mid, 6, z1 + 3)
    d.lamp(mid, 6, z2 - 2)
    # ---- compost & garden beside the cabin ----
    compost_bay(d, x1, 2, 15)
    for x in range(x1, x2 + 1):
        d.set(x, 2, 22, "spruce_fence")
    for z in range(16, 23):
        d.set(x1 - 1, 2, z, "spruce_fence")
        d.set(x2 + 1, 2, z, "spruce_fence")
    for x in range(x1, x2 + 1):
        for z in range(17, 22):
            d.set(x, 1, z, "farmland[moisture=7]" if x != mid else ("water" if z == 19 else "coarse_dirt"))
            if x != mid:
                d.set(x, 2, z, ("potatoes[age=7]", "carrots[age=7]", "beetroots[age=3]")[(x // 2) % 3])
    d.door(mid, 2, z2, "north", "spruce")
    # ---- L2: tool lean-to on the east side ----
    if L >= 2:
        lx2 = x2 + 4
        walls(d, x2, z1 + 1, lx2, z2 - 1, 2, 4, "spruce_planks")
        d.fill(x2 + 1, 1, z1 + 2, lx2 - 1, 1, z2 - 2, "spruce_planks")
        for z in range(z1, z2 + 1):
            for x in range(x2 + 1, lx2 + 2):
                d.set(x, 5, z, slab("spruce"))
        d.door(lx2 - 1, 2, z1 + 1, "south", "spruce")
        d.set(lx2 - 1, 2, z2 - 2, "grindstone[face=floor,facing=north]")
        racks(d, [(x2 + 1, 2, z2 - 2), (x2 + 2, 2, z2 - 2), (x2 + 1, 2, z1 + 2)], d.req["racks"] - 2)
        d.set(lx2, 3, z1 + 3, "glass_pane")
    # ---- L3: gambrel barn ----
    if L >= 3:
        bx1, bx2, bz1, bz2 = 16, 25, 9, 22
        d.fill(bx1, 1, bz1, bx2, 1, bz2, "spruce_planks")
        for y in range(2, 7):
            for x in range(bx1, bx2 + 1):
                for z in range(bz1, bz2 + 1):
                    if x in (bx1, bx2) or z in (bz1, bz2):
                        d.set(x, y, z, "cobblestone" if y == 2 else
                              ("stripped_spruce_log[axis=y]" if (x + z) % 2 == 0 else "dark_oak_planks"))
                    else:
                        d.set(x, y, z, AIR)
        d.fill(bx1 + 1, 7, bz1 + 5, bx2 - 1, 7, bz2 - 1, "spruce_planks")
        gambrel(d, bx1, bz1, bx2, bz2, 7, "dark_oak", "dark_oak_planks", "dark_oak_planks")
        for x in (20, 21):
            for y in (2, 3, 4):
                d.set(x, y, bz1, AIR)
        d.set(20, 5, bz1, "stripped_spruce_log[axis=x]")
        d.set(21, 5, bz1, "stripped_spruce_log[axis=x]")
        d.set(20, 9, bz1, "spruce_trapdoor[facing=north,half=bottom,open=true,powered=false,waterlogged=false]")
        d.set(21, 9, bz1, "spruce_trapdoor[facing=north,half=bottom,open=true,powered=false,waterlogged=false]")
        for z in range(bz1 + 2, bz1 + 6):
            d.item(bx1 + 1, 2, z, "barrel")
        for z in range(bz1 + 7, bz2):                                 # stalls
            d.set(bx2 - 3, 2, z, "spruce_fence") if z % 3 else None
            d.set(bx2 - 1, 2, z, "hay_block[axis=y]") if z % 3 == 0 else None
        for x in range(bx1 + 1, bx2):
            d.set(x, 8, bz2 - 1, "hay_block[axis=x]")
            d.set(x, 8, bz2 - 2, "hay_block[axis=x]") if x % 2 else None
        ladder(d, bx1 + 1, bz2 - 1, 2, 7, "east")
        racks(d, [(bx1 + 1, 2, z) for z in range(bz1 + 7, bz1 + 10)], max(0, d.req["racks"] - 5))
        d.lamp(20, 6, bz1 + 3)
        d.lamp(20, 6, bz2 - 3)
        for z in range(bz1 + 2, bz2 - 1, 4):
            d.window(bx2, 3, z, bx2, 4, z)
    # ---- L4: corral ----
    if L >= 4:
        for x in range(16, 21):
            d.set(x, 2, 1, "spruce_fence")
            d.set(x, 2, 7, "spruce_fence")
        for z in range(1, 8):
            d.set(16, 2, z, "spruce_fence")
            d.set(20, 2, z, "spruce_fence")
        d.set(18, 2, 7, "spruce_fence_gate[facing=north,in_wall=false,open=false,powered=false]")
        d.set(19, 2, 2, "water_cauldron[level=3]")
        d.set(17, 2, 2, "hay_block[axis=y]")
    # ---- L5: wooden stave silo with a dome ----
    if L >= 5:
        sx, sz = 21, 1
        ring = [(1, 0), (2, 0), (0, 1), (3, 1), (0, 2), (3, 2), (1, 3), (2, 3)]
        for y in range(1, 14):
            for dx, dz in ring:
                d.set(sx + dx, y, sz + dz, "cobblestone" if y <= 2 else
                      ("stripped_dark_oak_log[axis=y]" if y % 4 == 0 else "spruce_planks"))
            for dx in (1, 2):
                for dz in (1, 2):
                    d.set(sx + dx, y, sz + dz, "hay_block[axis=y]" if y < 12 else AIR)
        for dx, dz, f in ((1, 0, "south"), (2, 0, "south"), (0, 1, "east"), (3, 1, "west"), (0, 2, "east"),
                          (3, 2, "west"), (1, 3, "north"), (2, 3, "north")):
            d.set(sx + dx, 14, sz + dz, stair("dark_oak", f))
        for dx in (1, 2):
            for dz in (1, 2):
                d.set(sx + dx, 14, sz + dz, "dark_oak_planks")
                d.set(sx + dx, 15, sz + dz, slab("dark_oak"))
        d.set(sx + 1, 16, sz + 1, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        for y in range(3, 13):
            d.set(sx - 1, y, sz + 1, "ladder[facing=west,waterlogged=false]")
    return d


def farmer_neoterra(rel, L):
    d = Design("Neoterra", rel, (25, 14, 21), gy=1, paving="smooth_stone")
    x1, x2, z1, z2 = 2, 10, 3, 10
    d.box(x1, 2, z1, x2, 5, z2, "white_concrete", floor="polished_diorite")
    for x in range(x1 + 1, x2):
        if x != 6:
            d.window(x, 2, z1, x, 4, z1, "glass_pane")
    for z in range(z1 + 2, z2, 3):
        d.window(x1, 3, z, x1, 4, z)
    d.fill(x1, 5, z1, x2, 5, z1, "lime_terracotta")
    d.door(6, 2, z1, "south", "birch")
    d.flat(x1, z1, x2, z2, 6, "smooth_quartz", "white_concrete", "smooth_quartz_slab")
    for x in range(5, 8):
        d.set(x, 5, z1 - 1, "smooth_quartz_slab[type=top,waterlogged=false]")
    d.sign(4, 4, z1 - 1, "north", ["AGRI", "HUB"], "birch", glow=True, color="lime")
    # ---- office / farm kitchen ----
    d.hut(x1 + 1, 2, z1 + 1)
    d.item(x2 - 1, 2, z2 - 1, "crafting_table")
    d.set(x2 - 2, 2, z2 - 1, "smooth_quartz_slab[type=top,waterlogged=false]")
    d.set(x2 - 3, 2, z2 - 1, "water_cauldron[level=3]")
    racks(d, [(x1 + 1, 2, z) for z in range(z1 + 3, z1 + 6)], 2, "east")
    d.set(6, 2, 7, "smooth_quartz_slab[type=top,waterlogged=false]")
    d.chair(5, 2, 7, "west", "birch", sit=False)
    d.chair(7, 2, 7, "east", "birch", sit=False)
    d.plant(x2 - 1, 2, z1 + 1, "potted_bamboo")
    for x in (4, 8):
        d.set(x, 5, 6, "sea_lantern")
    d.door(x2, 2, 6, "west", "birch")
    # ---- compost station with a canopy ----
    for z in range(z2 + 2, z2 + 6):
        for x in range(x1, x1 + 5):
            d.set(x, 5, z, "smooth_quartz_slab[type=bottom,waterlogged=false]")
    posts(d, [(x1, z2 + 5), (x1 + 4, z2 + 5)], 2, 4, "light_gray_concrete")
    compost_bay(d, x1 + 1, 2, z2 + 3)
    # raised kitchen-garden beds (quartz rims, irrigation channel)
    for x in range(1, 11):
        for z in range(16, 21):
            rim = x in (1, 10) or z in (16, 20)
            d.set(x, 2, z, "smooth_quartz_slab[type=bottom,waterlogged=false]" if rim else AIR)
            if not rim:
                if z == 18:
                    d.set(x, 1, z, "water")
                else:
                    d.set(x, 1, z, "farmland[moisture=7]")
                    d.set(x, 2, z, ("wheat[age=7]", "carrots[age=7]", "beetroots[age=3]")[x % 3])
    # ---- L2: tool garage ----
    if L >= 2:
        gx1, gx2, gz1, gz2 = 12, 17, 3, 8
        d.box(gx1, 2, gz1, gx2, 4, gz2, "light_gray_concrete", floor="smooth_stone")
        d.flat(gx1, gz1, gx2, gz2, 5, "smooth_quartz", "white_concrete", "smooth_quartz_slab")
        for x in range(gx1 + 1, gx2):
            for y in (2, 3, 4):
                d.set(x, y, gz1, AIR)
        for x in range(gx1 + 1, gx2):
            d.set(x, 4, gz1, "iron_bars")
        d.set(gx1 + 1, 2, gz2 - 1, "grindstone[face=floor,facing=north]")
        racks(d, [(x, 2, gz2 - 1) for x in range(gx1 + 2, gx2)], d.req["racks"] - 2, "north")
        d.set(gx1 + 2, 4, gz1 + 2, "end_rod[facing=down]")
    # ---- L3: hydroponic greenhouse with the grain barrels ----
    if L >= 3:
        hx1, hx2, hz1, hz2 = 12, 22, 10, 18
        for y in range(2, 7):
            for x in range(hx1, hx2 + 1):
                for z in range(hz1, hz2 + 1):
                    if x in (hx1, hx2) or z in (hz1, hz2):
                        corner = x in (hx1, hx2) and z in (hz1, hz2)
                        d.set(x, y, z, "white_concrete" if corner or y in (2, 6) else "glass")
                    else:
                        d.set(x, y, z, AIR)
        d.fill(hx1 + 1, 7, hz1 + 1, hx2 - 1, 7, hz2 - 1, "light_blue_stained_glass")
        walls(d, hx1, hz1, hx2, hz2, 7, 7, "white_concrete")
        d.fill(hx1 + 1, 1, hz1 + 1, hx2 - 1, 1, hz2 - 1, "polished_diorite")
        for z in (hz1 + 2, hz1 + 4, hz1 + 6):
            planter_row(d, hx1 + 3, hx2 - 2, z, 2)
            for x in range(hx1 + 3, hx2 - 1):
                d.set(x, 5, z, "end_rod[facing=down]") if x % 2 else None
        d.door(16, 2, hz1, "south", "birch")
        for z in range(hz1 + 1, hz1 + 5):
            d.item(hx1 + 1, 2, z, "barrel")
        racks(d, [(hx1 + 1, 2, z) for z in range(hz1 + 5, hz2)], max(0, d.req["racks"] - 5), "east")
    # ---- L4: solar on the office roof; L5: green roof terrace ----
    if L >= 4:
        for x in range(x1 + 1, x2, 2):
            for z in range(z1 + 1, z2):
                d.set(x, 7, z, "daylight_detector[inverted=false,power=0]")
    if L >= 5:
        for x in range(13, 17):
            for z in range(4, 8):
                d.set(x, 6, z, "moss_block")
                d.set(x, 7, z, "azalea" if (x + z) % 3 == 0 else ("fern" if (x + z) % 3 == 1 else "air"))
        for x in range(18, 23):
            d.set(x, 2, 2, "birch_fence")
    return d


@design("farmer")
def farmer(pack, rel, L):
    return {"Hearthwood": farmer_hearthwood, "Cascadia": farmer_cascadia, "Neoterra": farmer_neoterra}[pack](rel, L)
