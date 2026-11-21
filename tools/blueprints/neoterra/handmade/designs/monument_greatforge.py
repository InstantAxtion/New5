"""
Grand project: the GREAT FORGE (+ greatforgewing child huts, each with a smithing table).

Hearthwood  "Coalbrookdale Ironworks": a Victorian brick ironworks. L1 the Old Furnace house – a brick hall with
            a tall tapering furnace stack rising through its tiled roof, tapping arch with the blast furnace and
            the pig bed in front; two brick FORGE HALLS (the wings) with big chimneys flank the yard. L2 the arched
            casting house in front (cupola, jib crane, pig beds) and a charging loft. L3 the charging bank with
            its ore/coke/limestone vaults and the charging bridge, the river with the cast-iron arch bridge. L4
            the New Furnace with its blowing-engine house and great chimney, the bridge toll house. L5 the Great
            Warehouse with its clock tower, works gate and yard dressing.
Cascadia    "Cascadia Smelter & Stamp Mill": a mountain smelter on a hillside (see the Cascadia section).
Neoterra    "Neoterra Steelworks": a modern steelworks landmark (see the Neoterra section).

Every furnishing is placed by hand at explicit coordinates; loops only draw structure (walls, floors, roofs,
rails along lines given here) or rows whose start / spacing / count are written for that specific room.
Wings are pasted without rotation at both positions, so they are drawn symmetric about their own centre line
(the hut block sits beside the door).
"""
from hm import Design, design, AIR

WING = "monuments/greatforgewing0.blueprint"
WATER = "water[level=0]"


# ----------------------------------------------------------------------------------------------- helpers
def stair(b, f, half="bottom", shape="straight"):
    return f"{b}[facing={f},half={half},shape={shape},waterlogged=false]"


def slab(b, t="bottom"):
    return f"{b}[type={t},waterlogged=false]"


def lantern(hang=True):
    return f"lantern[hanging={'true' if hang else 'false'},waterlogged=false]"


def logb(b, axis="y"):
    return f"{b}[axis={axis}]"


def trap(b, f, half="bottom", open_=False):
    return f"{b}[facing={f},half={half},open={'true' if open_ else 'false'},powered=false,waterlogged=false]"


def plate(kind="heavy_weighted"):
    return f"{kind}_pressure_plate[power=0]" if "weighted" in kind else f"{kind}_pressure_plate[powered=false]"


SOLIDISH_NO = ("air", "stairs", "slab", "lantern", "torch", "door", "carpet", "flower", "pot", "rail", "chain",
               "bed", "sign", "banner", "button", "plate", "rod", "water", "trapdoor", "leaves", "sapling", "grass",
               "fern", "bush", "lily", "cane", "vine", "candle", "bell", "azalea", "substitution", "head", "campfire",
               "lava", "cauldron", "anvil", "hopper")


def connect_walls(d):
    """Set the side connections of every *_wall block (the toolkit only connects panes and fences)."""
    bp = d.bp
    dirs = {"north": (0, -1), "south": (0, 1), "west": (-1, 0), "east": (1, 0)}
    for x, y, z, s in list(bp.blocks()):
        name = s.split("[")[0]
        if not name.endswith("_wall") or "sign" in name or "banner" in name or "torch" in name:
            continue
        sides = {}
        for k, (dx, dz) in dirs.items():
            if not bp.inside(x + dx, y, z + dz):
                sides[k] = "none"
                continue
            n = bp.get(x + dx, y, z + dz).split("[")[0].split(":")[-1]
            conn = n.endswith("_wall") or n.endswith("fence") or n.endswith("pane") or n.endswith("bars") or \
                not any(t in n for t in SOLIDISH_NO)
            sides[k] = "low" if conn else "none"
        above = bp.get(x, y + 1, z) if bp.inside(x, y + 1, z) else AIR
        straight = (sides["north"] == sides["south"] == "low" and sides["east"] == sides["west"] == "none") or \
                   (sides["east"] == sides["west"] == "low" and sides["north"] == sides["south"] == "none")
        up = "false" if straight and above == AIR else "true"
        if above != AIR and above.split("[")[0].endswith("_wall"):
            for k in sides:
                if sides[k] == "low":
                    sides[k] = "tall"
            up = "true" if not straight else "false"
        bp.grid[y][z][x] = (f"{name}[east={sides['east']},north={sides['north']},south={sides['south']},"
                            f"up={up},waterlogged=false,west={sides['west']}]")


def lamp(d, x, y, z, kind="lantern"):
    """ONE hanging lamp at (x, y, z) on a chain up to the next block above."""
    yy = y + 1
    while d.bp.inside(x, yy, z) and d.air(x, yy, z) and yy < y + 12:
        yy += 1
    for k in range(y + 1, yy):
        d.set(x, k, z, "chain[axis=y,waterlogged=false]")
    d.set(x, y, z, f"{kind}[hanging=true,waterlogged=false]")


def put(d, items):
    """Hand-written list of single blocks: (x, y, z, state)."""
    for x, y, z, st in items:
        d.set(x, y, z, st)


def rect(d, x1, z1, x2, z2, y, block):
    d.fill(x1, y, z1, x2, y, z2, block)


def ring(d, x1, z1, x2, z2, y, block):
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if x in (x1, x2) or z in (z1, z2):
                d.set(x, y, z, block)


def stair_run(d, cells, facing, block, fill=None):
    """A flight of stairs on the hand-listed cells [(x, y, z), ...]; `fill` = stringer block under each step."""
    for x, y, z in cells:
        d.set(x, y, z, stair(block, facing))
        if fill:
            for yy in range(2, y):
                d.set(x, yy, z, fill)


def chair(d, x, y, z, back, wood):
    d.set(x, y, z, stair(f"{wood}_stairs", back))


def table(d, x, y, z, wood, top=None):
    d.set(x, y, z, f"{wood}_fence")
    d.set(x, y + 1, z, top or f"{wood}_pressure_plate[powered=false]")


def bed(d, x, y, z, facing, color):
    """Head at (x, y, z), foot one cell opposite to `facing`."""
    dx, dz = {"north": (0, 1), "south": (0, -1), "east": (-1, 0), "west": (1, 0)}[facing]
    d.set(x, y, z, f"{color}_bed[facing={facing},occupied=false,part=head]")
    d.set(x + dx, y, z + dz, f"{color}_bed[facing={facing},occupied=false,part=foot]")


def shelf(face):
    occ = ["true", "false", "true", "true", "false", "true"]
    return f"chiseled_bookshelf[facing={face}," + ",".join(f"slot_{i}_occupied={o}" for i, o in enumerate(occ)) + "]"


def pot(face="north"):
    return f"decorated_pot[cracked=false,facing={face},waterlogged=false]"


def cand(n=2, color=""):
    c = f"{color}_candle" if color else "candle"
    return f"{c}[candles={n},lit=false,waterlogged=false]"


def place_wings(d, xs, z0, wsize, whut):
    wx, wy, wz = wsize
    hx, hy, hz = whut
    for ox in xs:
        d.reserve(ox, 1, z0, ox + wx - 1, d.sy - 1, z0 + wz - 1)
        d.child_hut(ox + hx, hy + 1, z0 + hz, WING)


def water_strip(d, x1, z1, x2, z2, weir="mossy_stone_bricks"):
    """River / leat in the ground layer between x1..x2, z1..z2; riverbed below."""
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            d.set(x, 0, z, "structurize:blocksolidsubstitution")
            d.set(x, 1, z, WATER)


# =============================================================================================================
#                                     HEARTHWOOD – Coalbrookdale ironworks
# =============================================================================================================
HW_SIZE = (57, 40, 49)
HW_WX, HW_WZ, HW_WSIZE, HW_WHUT = (1, 45), 1, (11, 26, 13), (2, 1, 4)
HW_STACK = {1: 21, 2: 24, 3: 26, 4: 28, 5: 31}

def hww(rel, L):
    """Hearthwood wing: a brick FORGE HALL with a big back chimney (symmetric about x = 5, door north)."""
    d = Design("Hearthwood", rel, HW_WSIZE, gy=0, paving="gravel")
    WT = 4 if L == 1 else 8                               # wall top
    RY = WT + 1                                           # eave course of the roof
    CH = {1: 11, 2: 13, 3: 16, 4: 18, 5: 20}[L]           # chimney top
    # floor and apron
    rect(d, 2, 3, 8, 10, 0, "bricks")
    rect(d, 3, 0, 7, 1, 0, "cobblestone")
    # walls: stone-brick plinth, brick body, stone quoins
    for x in range(1, 10):
        for z in range(2, 12):
            if not (x in (1, 9) or z in (2, 11)):
                continue
            for y in range(1, WT + 1):
                st = "bricks"
                if y == 1:
                    st = "stone_bricks"
                elif x in (1, 9) and z in (2, 11):
                    st = "stone_bricks" if y % 2 == 0 else "bricks"
                d.set(x, y, z, st)
    if L >= 2:                                            # string course between the storeys
        ring(d, 1, 2, 9, 11, 5, "stone_bricks")
    d.gable(1, 2, 9, 11, RY, "z", "deepslate_tile_stairs", "deepslate_tile_slab", "bricks", overhang=1)
    # arched forge doorway in the front gable
    d.fill(4, 1, 2, 6, 2, 2, AIR)
    d.set(5, 3, 2, AIR)
    d.set(4, 3, 2, stair("brick_stairs", "west", "top"))
    d.set(6, 3, 2, stair("brick_stairs", "east", "top"))
    d.set(5, 4, 2, "chiseled_stone_bricks")
    # windows (hand-placed)
    for x, z in ((1, 5), (1, 8), (9, 5), (9, 8)):
        d.window(x, 2, z, x, 3, z)
    d.window(8, 2, 2, 8, 3, 2)
    d.window(2, 2, 11, 2, 3, 11)
    d.window(8, 2, 11, 8, 3, 11)
    # chimney stack behind the hearth (x 4..6, z 10..12) with a flue
    for y in range(3, CH + 1):
        for x in range(4, 7):
            for z in range(10, 13):
                d.set(x, y, z, AIR if (x, z) == (5, 11) else "bricks")
    for x in range(4, 7):
        for z in range(11, 13):
            d.set(x, 1, z, "bricks")
            d.set(x, 2, z, "bricks")
    # the forge: raised hearth, fire, cheeks, hood
    put(d, [(4, 1, 10, "bricks"), (5, 1, 10, "bricks"), (6, 1, 10, "bricks"),
            (5, 2, 10, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]"),
            (4, 2, 10, "brick_wall"), (6, 2, 10, "brick_wall"),
            (5, 3, 10, stair("brick_stairs", "south", "top"))])
    d.hut(*HW_WHUT, facing="east")
    # ground floor furnishing (the smithy)
    d.item(3, 1, 9, "smithing_table")
    put(d, [(7, 1, 10, "piston[extended=false,facing=west]"), (8, 1, 10, "brown_wool"),
            (5, 1, 7, "anvil[facing=east]"), (7, 1, 8, "water_cauldron[level=3]"),
            (8, 1, 7, "grindstone[face=floor,facing=north]"),
            (2, 1, 7, "barrel[facing=up,open=false]"), (2, 1, 8, "chest[facing=east,type=single,waterlogged=false]"),
            (2, 2, 7, trap("spruce_trapdoor", "east", open_=True)), (2, 2, 8, trap("spruce_trapdoor", "east", open_=True))])
    if L == 1:
        put(d, [(8, 1, 4, "coal_block"), (8, 2, 4, "black_carpet"), (8, 1, 5, "barrel[facing=up,open=false]")])
    lamp(d, 3, 4 if L >= 2 else 3, 6)
    lamp(d, 7, 4 if L >= 2 else 3, 6)
    # sign over the door
    d.sign(5, WT + 2 if L == 1 else 6, 1, "north", ["", "FORGE", "", ""], "dark_oak")
    if L >= 2:
        # buttresses on the long sides, a ridge louvre for the forge heat, quench barrel and anvil block outside
        for x, f in ((0, "east"), (10, "west")):
            for z in (4, 9):
                for y in range(1, 3):
                    d.set(x, y, z, "stone_bricks")
                d.set(x, 3, z, stair("stone_brick_stairs", f))
        ridge = RY + 4
        for z in (5, 6):
            d.set(5, ridge, z, "deepslate_tiles")
            d.set(5, ridge + 1, z, "dark_oak_fence")
            d.set(5, ridge + 2, z, slab("deepslate_tile_slab"))
        put(d, [(2, 1, 1, "water_cauldron[level=3]"), (8, 1, 1, "barrel[facing=up,open=false]"),
                (8, 2, 1, "lantern[hanging=false,waterlogged=false]")])
    if L >= 2:
        # pattern loft: floor at y5, ladder in the north-east corner
        for x in range(2, 9):
            for z in range(3, 11):
                if 4 <= x <= 6 and z == 10:
                    continue
                d.set(x, 5, z, "spruce_planks")
        d.set(8, 5, 3, AIR)
        for y in range(1, 6):
            d.set(8, y, 3, "ladder[facing=west,waterlogged=false]")
        for x, z in ((1, 6), (9, 6)):
            d.window(x, 6, z, x, 7, z)
        d.window(5, 7, 2, 5, 8, 2)
        put(d, [(8, 1, 5, "coal_block"), (8, 1, 6, "barrel[facing=up,open=false]"), (8, 2, 5, "black_carpet")])
        # the loft: pattern shelves, bench, lectern with the order book, barrels of moulding sand
        put(d, [(2, 6, 4, shelf("east")), (2, 7, 4, shelf("east")), (2, 6, 5, shelf("east")),
                (2, 6, 8, "crafting_table"), (2, 6, 9, slab("spruce_slab", "top")), (2, 7, 9, cand(3)),
                (3, 6, 9, stair("spruce_stairs", "north")),
                (8, 6, 7, "lectern[facing=west,has_book=true,powered=false]"),
                (8, 6, 9, "barrel[facing=up,open=false]"), (7, 6, 9, "barrel[facing=up,open=false]"),
                (8, 7, 9, "barrel[facing=west,open=false]"),
                (5, 6, 5, "white_carpet"), (6, 6, 5, "white_carpet"), (5, 6, 6, "white_carpet"),
                (6, 6, 6, "white_carpet"), (5, 6, 4, pot("north"))])
        lamp(d, 4, 8, 7)
        lamp(d, 6, 8, 4)
    if L >= 3:
        # pentice roof over the door on brackets, lamps beside it, corbelled chimney cap
        for x in range(3, 8):
            d.set(x, 4, 1, stair("deepslate_tile_stairs", "south"))
        d.set(3, 3, 1, "dark_oak_fence")
        d.set(7, 3, 1, "dark_oak_fence")
        put(d, [(1, 2, 1, "stone_bricks"), (1, 3, 1, "lantern[hanging=false,waterlogged=false]"),
                (9, 2, 1, "stone_bricks"), (9, 3, 1, "lantern[hanging=false,waterlogged=false]")])
    if L >= 4:
        # corbelled chimney cap with pots, window boxes under the side windows
        for x in range(3, 8):
            d.set(x, CH, 9, stair("brick_stairs", "south", "top"))
        for z in range(10, 13):
            d.set(3, CH, z, stair("brick_stairs", "east", "top"))
            d.set(7, CH, z, stair("brick_stairs", "west", "top"))
        for x in (4, 6):
            d.set(x, CH + 1, 10, "terracotta")
            d.set(x, CH + 1, 12, "terracotta")
        for x, z, f in ((0, 5, "west"), (0, 8, "west"), (10, 5, "east"), (10, 8, "east")):
            d.set(x, 1, z, trap("dark_oak_trapdoor", f, "top"))
            d.set(x, 2, z, "potted_red_tulip" if z == 5 else "potted_cornflower")
    if L >= 5:
        # cast-iron cresting on the ridge, weather vane, window boxes, horseshoe arch banner
        top = RY + 4
        for z in range(3, 10):
            if z in (5, 6):
                continue
            d.set(5, top + 1, z, "iron_bars")
        d.set(5, top + 1, 2, "stone_bricks")
        d.set(5, top + 2, 2, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        d.banner(5, 3, 1, "north", "black")
    connect_walls(d)
    return d


def hw_brick_walls(d, x1, z1, x2, z2, y1, y2, body="bricks", plinth="stone_bricks", quoin="stone_bricks"):
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if not (x in (x1, x2) or z in (z1, z2)):
                continue
            for y in range(y1, y2 + 1):
                st = body
                if y == y1:
                    st = plinth
                elif x in (x1, x2) and z in (z1, z2) and y % 2 == 0:
                    st = quoin
                d.set(x, y, z, st)


def hw_arch(d, x, y, z, axis="x", w=3, h=3, body="bricks"):
    """Round-headed opening w wide (odd), h tall to the springing, at (x..x+w-1 along axis, y.., z)."""
    dx, dz = (1, 0) if axis == "x" else (0, 1)
    lo, hi = ("west", "east") if axis == "x" else ("north", "south")
    for i in range(w):
        for yy in range(y, y + h):
            d.set(x + dx * i, yy, z + dz * i, AIR)
    d.set(x, y + h, z, stair("brick_stairs", lo, "top"))
    d.set(x + dx * (w - 1), y + h, z + dz * (w - 1), stair("brick_stairs", hi, "top"))
    for i in range(1, w - 1):
        d.set(x + dx * i, y + h, z + dz * i, AIR)
    d.set(x + dx * (w // 2), y + h + 1, z + dz * (w // 2), "chiseled_stone_bricks")


def hw_window(d, x, z, y=4, h=2):
    d.window(x, y, z, x, y + h - 1, z)
    d.set(x, y + h, z, "stone_bricks")
    d.set(x, y - 1, z, "stone_bricks")


def hw_furnace_house(d, L):
    """The Old Furnace: brick hall 15 x 13 around the furnace stack; charging loft from L2."""
    X1, X2, Z1, Z2 = 21, 35, 15, 27
    rect(d, X1, Z1, X2, Z2, 1, "packed_mud")
    hw_brick_walls(d, X1, Z1, X2, Z2, 2, 9)
    ring(d, X1, Z1, X2, Z2, 6, "stone_bricks")          # string course
    d.gable(X1, Z1, X2, Z2, 10, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "bricks", overhang=1)
    # north casting arch (open into the yard / casting house) and windows
    hw_arch(d, 27, 2, Z1, "x", 3, 3)
    for x in (23, 33):
        hw_window(d, x, Z1)
    for z in (18, 24):
        hw_window(d, X1, z)
        hw_window(d, X2, z)
    for x in (23, 33):
        hw_window(d, x, Z2)
    # gable oculi
    d.set(X1, 12, 21, "glass_pane")
    d.set(X2, 12, 21, "glass_pane")
    # furnace stack 5 x 5 through the hall, then 3 x 3 with a flue up to its corbelled top
    T = HW_STACK[L]
    for y in range(2, 13):
        for x in range(26, 31):
            for z in range(19, 24):
                d.set(x, y, z, "stone_bricks" if y == 2 or (x in (26, 30) and z in (19, 23) and y % 2 == 0) else "bricks")
    for y in range(5, 13):                               # sealed hollow core of the stack
        for x in range(27, 30):
            for z in range(20, 23):
                d.set(x, y, z, AIR)
    for y in range(13, T + 1):
        for x in range(27, 30):
            for z in range(20, 23):
                d.set(x, y, z, AIR if (x, z) == (28, 21) else "bricks")
    for x in range(26, 31):
        for z in range(19, 24):
            if x in (26, 30) or z in (19, 23):
                f = "north" if z == 19 else "south" if z == 23 else "west" if x == 26 else "east"
                d.set(x, T, z, stair("brick_stairs", f, "top"))
    for x, z in ((26, 19), (30, 19), (26, 23), (30, 23)):
        d.set(x, T, z, "bricks")
    for x in range(27, 30):
        for z in range(20, 23):
            if (x, z) != (28, 21):
                d.set(x, T + 1, z, slab("stone_brick_slab"))
    # tapping arch with blast furnace no. 1, the pig bed in front, blowing arch with bellows on the west
    d.item(28, 2, 19, "blast_furnace", "north")
    put(d, [(28, 3, 19, AIR), (27, 3, 19, stair("brick_stairs", "west", "top")),
            (29, 3, 19, stair("brick_stairs", "east", "top")), (28, 4, 19, "chiseled_stone_bricks")])
    rect(d, 26, 16, 30, 18, 1, "sand")
    for x, z in ((28, 16), (28, 17), (28, 18), (26, 17), (27, 17), (29, 17), (30, 17)):
        d.set(x, 2, z, plate())
    put(d, [(26, 2, 21, "iron_bars"), (25, 2, 21, "piston[extended=false,facing=east]"),
            (25, 2, 20, "brown_wool"), (25, 2, 22, "brown_wool"), (25, 3, 21, "brown_carpet")])
    d.hut(25, 2, 16, "east")
    # the great anvil with quench and grindstone (east of the arch)
    d.item(32, 2, 17, "anvil", "east")
    put(d, [(33, 2, 16, "water_cauldron[level=3]"), (34, 2, 17, "grindstone[face=floor,facing=north]"),
            (34, 2, 16, "barrel[facing=up,open=false]"), (31, 2, 16, "stone_bricks"),
            (31, 3, 16, "lantern[hanging=false,waterlogged=false]")])
    # coke heap (west bay), ore and limestone (east bay)
    put(d, [(22, 2, 23, "coal_block"), (23, 2, 23, "coal_block"), (22, 2, 22, "coal_block"),
            (22, 3, 23, "black_carpet"), (23, 3, 23, "black_carpet"), (22, 3, 22, "black_carpet"),
            (34, 2, 20, "iron_ore"), (34, 2, 21, "iron_ore"), (33, 2, 21, "iron_ore"), (34, 3, 21, "brown_carpet"),
            (34, 2, 23, "barrel[facing=up,open=false]"), (33, 2, 23, "barrel[facing=up,open=false]"),
            (34, 3, 23, "barrel[facing=west,open=false]")])
    # moulding bench along the back wall: patterns, flasks, ladles
    put(d, [(23, 2, 26, "crafting_table"), (24, 2, 26, slab("spruce_slab", "top")), (25, 2, 26, slab("spruce_slab", "top")),
            (24, 3, 26, pot("north")), (25, 2, 25, stair("spruce_stairs", "north")),
            (31, 2, 26, "lava_cauldron"), (32, 2, 26, "cauldron"), (33, 2, 26, slab("smooth_stone_slab", "top")),
            (34, 2, 26, "chest[facing=north,type=single,waterlogged=false]")])
    for x, z in ((23, 17), (33, 19), (23, 21), (33, 24), (28, 25)):
        lamp(d, x, 6 if z != 25 else 5, z)
    if L >= 2:
        # charging loft (U around the stack) at y7, staircase up the west wall
        for x in range(22, 35):
            for z in range(19, 27):
                if 26 <= x <= 30 and z <= 23:
                    continue
                if 26 <= x <= 30 and z >= 24 or x <= 25 or x >= 31:
                    d.set(x, 7, z, "spruce_planks")
        for z in range(19, 22):
            d.set(22, 7, z, AIR)
        stair_run(d, [(22, 2, 17), (22, 3, 18), (22, 4, 19), (22, 5, 20), (22, 6, 21)], "south", "spruce_stairs",
                  fill="spruce_planks")
        for x in (23, 24, 25, 31, 32, 33, 34):
            d.set(x, 8, 19, "spruce_fence")
        for z in (20, 21):
            d.set(23, 8, z, "spruce_fence")
        # the loft: ore, coke and limestone ready for charging, the weigh beam, the clerk's desk
        put(d, [(26, 8, 21, trap("spruce_trapdoor", "west", open_=True)), (30, 8, 21, trap("spruce_trapdoor", "east", open_=True)),
                (24, 8, 23, "iron_ore"), (25, 8, 23, "iron_ore"), (24, 9, 23, "brown_carpet"),
                (23, 8, 23, "coal_block"), (23, 9, 23, "black_carpet"), (22, 8, 23, "coal_block"),
                (22, 8, 26, "barrel[facing=up,open=false]"), (22, 9, 26, "barrel[facing=east,open=false]"),
                (23, 8, 26, "barrel[facing=up,open=false]"),
                (24, 8, 26, "spruce_fence"), (24, 9, 26, plate()),
                (34, 8, 19, "calcite"), (34, 8, 20, "calcite"), (33, 8, 19, "barrel[facing=up,open=false]"),
                (31, 8, 26, "lectern[facing=north,has_book=true,powered=false]"),
                (33, 8, 26, slab("spruce_slab", "top")), (33, 9, 26, cand(2)), (33, 8, 25, stair("spruce_stairs", "north")),
                (34, 8, 26, "chest[facing=north,type=single,waterlogged=false]"),
                (34, 8, 23, "barrel[facing=up,open=false]"), (34, 9, 23, "white_carpet")])
        lamp(d, 24, 10, 21)
        lamp(d, 32, 10, 22)
        lamp(d, 28, 10, 25)
    if L >= 3:
        # charging door to the bridge; tramway rails from the bridge to the stack's charging door
        d.fill(27, 8, Z2, 29, 9, Z2, AIR)
        d.set(28, 8, 23, trap("spruce_trapdoor", "south", open_=True))
        for z in (24, 25, 26, 27):
            d.set(28, 8, z, "rail[shape=north_south,waterlogged=false]")


def hw_casting_house(d, L):
    """Arched casting house in front of the furnace (L2): pig beds, cupolas, jib crane, ladles."""
    X1, X2, Z1, Z2 = 21, 35, 5, 15
    rect(d, X1, Z1, X2, Z2 - 1, 1, "sand")
    for x in range(X1, X2 + 1):
        for z in range(Z1, Z2):
            if x in (X1, X2) or z == Z1:
                for y in range(2, 9):
                    st = "bricks"
                    if y == 2:
                        st = "stone_bricks"
                    elif x in (X1, X2) and z == Z1 and y % 2 == 0:
                        st = "stone_bricks"
                    d.set(x, y, z, st)
    ring(d, X1, Z1, X2, Z2, 9, "bricks")
    for x in range(X1 + 1, X2):
        d.set(x, 9, Z2, AIR)
    d.gable(X1, Z1, X2, Z2 - 1, 9, "z", "deepslate_tile_stairs", "deepslate_tile_slab", "bricks", overhang=1)
    for x0 in (23, 27, 31):
        hw_arch(d, x0, 2, Z1, "x", 3, 3)
    for z0 in (7, 11):
        hw_arch(d, X1, 2, z0, "z", 3, 3)
        hw_arch(d, X2, 2, z0, "z", 3, 3)
    d.set(28, 12, Z1, "glass_pane")
    d.sign(28, 10, Z1 - 1, "north", ["COALBROOKDALE", "IRON WORKS", "est. 1709", ""], "dark_oak")
    # sow channel from the furnace arch and three rows of pigs each side
    for z in range(6, 15):
        d.set(28, 2, z, plate())
    for z in (8, 10, 12):
        for x in (24, 25, 26, 27, 29, 30, 31, 32):
            d.set(x, 2, z, plate())
    # cupola no. 2 (north-west corner): blast furnace at the foot of a brick shaft through the roof
    d.item(23, 2, 14, "blast_furnace", "east")
    for y in range(3, 17):
        d.set(23, y, 14, "bricks")
    d.set(22, 2, 14, "stone_bricks")
    d.set(22, 3, 14, stair("brick_stairs", "east", "top"))
    # jib crane with a ladle on its chain
    for y in range(2, 8):
        d.set(22, y, 7, logb("stripped_dark_oak_log"))
    for x in range(23, 26):
        d.set(x, 7, 7, logb("stripped_dark_oak_log", "x"))
    put(d, [(25, 6, 7, "chain[axis=y,waterlogged=false]"), (25, 5, 7, "chain[axis=y,waterlogged=false]"),
            (25, 4, 7, "cauldron"), (23, 6, 7, stair("dark_oak_stairs", "west", "top"))])
    # ladles and the founder's corner
    put(d, [(34, 2, 6, "lava_cauldron"), (33, 2, 6, "cauldron"), (34, 2, 7, "cauldron"),
            (34, 2, 14, "barrel[facing=up,open=false]"), (34, 3, 14, "barrel[facing=west,open=false]"),
            (34, 2, 12, "grindstone[face=floor,facing=west]")])
    if L >= 3:
        # cupola no. 3 (north-east corner)
        d.item(33, 2, 14, "blast_furnace", "west")
        for y in range(3, 17):
            d.set(33, y, 14, "bricks")
        d.set(33, 3, 13, stair("brick_stairs", "south", "top"))
    for x, z in ((25, 10), (31, 10), (28, 7), (28, 13)):
        lamp(d, x, 6, z)


def hw_yard(d, L):
    """Works yard: gravel from the street to the furnace, cobbled cart track, the two forge forecourts."""
    for x in range(12, 45):
        for z in range(0, 30):
            d.set(x, 1, z, "gravel")
    for z in range(0, 15):
        for x in (27, 29):
            d.set(x, 1, z, "cobblestone")
        d.set(28, 1, z, "coarse_dirt")
    if L == 1:
        # pig bed outside the arch at L1 (the casting house covers it from L2)
        for z in range(9, 15):
            d.set(28, 1, z, "sand")
            d.set(28, 2, z, plate())
        for x in (26, 27, 29, 30):
            for z in (10, 12):
                d.set(x, 1, z, "sand")
                d.set(x, 2, z, plate())
        put(d, [(24, 2, 13, "cauldron"), (32, 2, 13, "lava_cauldron"), (33, 2, 13, "barrel[facing=up,open=false]")])


def hw_main(rel, L):
    d = Design("Hearthwood", rel, HW_SIZE, gy=1, paving="grass_block[snowy=false]")
    hw_yard(d, L)
    hw_furnace_house(d, L)
    if L >= 2:
        hw_casting_house(d, L)
    if L >= 3:
        hw_bank(d, L)
        hw_river(d, L)
    place_wings(d, HW_WX, HW_WZ, HW_WSIZE, HW_WHUT)
    connect_walls(d)
    return d


@design("greatforge")
def greatforge(pack, rel, L):
    return {"Hearthwood": hw_main}[pack](rel, L)


@design("greatforgewing")
def greatforgewing(pack, rel, L):
    return {"Hearthwood": hww}[pack](rel, L)


def hw_bank(d, L):
    """L3 charging bank: three stone vaults (ore, coke, limestone) under a charging deck, bridge to the loft."""
    X1, X2, Z1, Z2 = 19, 37, 30, 38
    for x in range(X1, X2 + 1):
        for z in range(Z1, Z2 + 1):
            d.set(x, 1, z, "cobblestone")
            if x in (X1, X2) or z in (Z1, Z2) or x in (25, 31):
                for y in range(2, 7):
                    d.set(x, y, z, "mossy_stone_bricks" if (x * 3 + y + z * 5) % 7 == 0 else "stone_bricks")
            d.set(x, 7, z, "cobblestone" if not (x in (X1, X2) or z in (Z1, Z2)) else "stone_bricks")
    for x0 in (21, 27, 33):
        d.fill(x0, 2, Z1, x0 + 2, 3, Z1, AIR)
        d.set(x0 + 1, 4, Z1, AIR)
        d.set(x0, 4, Z1, stair("stone_brick_stairs", "west", "top"))
        d.set(x0 + 2, 4, Z1, stair("stone_brick_stairs", "east", "top"))
        d.set(x0 + 1, 5, Z1, "chiseled_stone_bricks")
    # buttresses on the back
    for x in (19, 25, 31, 37):
        for y in range(2, 6):
            d.set(x, y, Z2 + 1, "stone_bricks")
        d.set(x, 6, Z2 + 1, stair("stone_brick_stairs", "north"))
    # ---- vault 1: iron ore
    put(d, [(20, 2, 37, "iron_ore"), (21, 2, 37, "iron_ore"), (22, 2, 37, "iron_ore"), (23, 2, 37, "iron_ore"),
            (24, 2, 37, "iron_ore"), (20, 3, 37, "iron_ore"), (21, 3, 37, "iron_ore"), (20, 2, 36, "iron_ore"),
            (22, 3, 37, "brown_carpet"), (23, 3, 37, "brown_carpet"), (21, 3, 36, "brown_carpet"),
            (20, 2, 32, "barrel[facing=up,open=false]"), (20, 2, 33, "barrel[facing=up,open=false]"),
            (20, 3, 32, "barrel[facing=east,open=false]"), (24, 2, 32, "lectern[facing=west,has_book=false,powered=false]"),
            (24, 2, 35, trap("spruce_trapdoor", "west", "top")), (23, 2, 35, "composter[level=4]")])
    lamp(d, 22, 5, 33)
    lamp(d, 22, 5, 35)
    # ---- vault 2: coke
    put(d, [(26, 2, 37, "coal_block"), (27, 2, 37, "coal_block"), (28, 2, 37, "coal_block"), (29, 2, 37, "coal_block"),
            (30, 2, 37, "coal_block"), (26, 2, 36, "coal_block"), (30, 2, 36, "coal_block"), (26, 3, 37, "coal_block"),
            (27, 3, 37, "black_carpet"), (28, 3, 37, "black_carpet"), (29, 3, 37, "black_carpet"),
            (26, 3, 36, "black_carpet"), (30, 3, 36, "black_carpet"),
            (26, 2, 32, "water_cauldron[level=3]"), (30, 2, 32, "barrel[facing=up,open=false]"),
            (30, 2, 33, "scaffolding[bottom=false,distance=0,waterlogged=false]"),
            (26, 2, 34, "spruce_fence"), (26, 3, 34, plate("spruce"))])
    lamp(d, 28, 5, 33)
    lamp(d, 28, 5, 35)
    # ---- vault 3: limestone flux
    put(d, [(32, 2, 37, "calcite"), (33, 2, 37, "calcite"), (34, 2, 37, "calcite"), (35, 2, 37, "calcite"),
            (36, 2, 37, "calcite"), (36, 2, 36, "calcite"), (35, 3, 37, "calcite"),
            (32, 3, 37, "white_carpet"), (33, 3, 37, "white_carpet"), (34, 3, 37, "white_carpet"),
            (36, 3, 36, "white_carpet"),
            (32, 2, 33, "grindstone[face=floor,facing=east]"), (36, 2, 32, "barrel[facing=up,open=false]"),
            (36, 2, 33, "barrel[facing=up,open=false]"), (36, 3, 32, "barrel[facing=west,open=false]"),
            (32, 2, 35, "stonecutter[facing=east]")])
    lamp(d, 34, 5, 33)
    lamp(d, 34, 5, 35)
    # ---- the charging deck: parapet, rails to the bridge, ore and coke heaps waiting, a hoist
    for x in range(X1, X2 + 1):
        for z in range(Z1, Z2 + 1):
            if (x in (X1, X2) or z in (Z1, Z2)) and not (27 <= x <= 29 and z == Z1) and (x, z) != (X2, 33):
                d.set(x, 8, z, "stone_brick_wall")
    for z in range(30, 36):
        d.set(28, 8, z, "rail[shape=north_south,waterlogged=false]")
    put(d, [(21, 8, 35, "iron_ore"), (22, 8, 35, "iron_ore"), (21, 8, 36, "iron_ore"), (22, 8, 36, "iron_ore"),
            (21, 9, 36, "iron_ore"), (21, 9, 35, "brown_carpet"),
            (34, 8, 35, "coal_block"), (35, 8, 35, "coal_block"), (34, 8, 36, "coal_block"), (35, 8, 36, "coal_block"),
            (35, 9, 36, "coal_block"), (34, 9, 36, "black_carpet"),
            (31, 8, 33, "calcite"), (31, 8, 34, "calcite"), (31, 9, 34, "white_carpet")])
    for y in range(8, 13):
        d.set(24, y, 32, logb("stripped_dark_oak_log"))
    for x in (25, 26):
        d.set(x, 12, 32, logb("stripped_dark_oak_log", "x"))
    put(d, [(26, 11, 32, "chain[axis=y,waterlogged=false]"), (26, 10, 32, "barrel[facing=up,open=false]"),
            (23, 8, 32, "barrel[facing=up,open=false]")])
    for x, z in ((20, 31), (36, 31), (20, 37), (36, 37)):
        d.set(x, 8, z, "stone_bricks")
        d.set(x, 9, z, "lantern[hanging=false,waterlogged=false]")
    # outside stair up the east end
    stair_run(d, [(38, 2, 37), (38, 3, 36), (38, 4, 35), (38, 5, 34), (38, 6, 33)], "north", "stone_brick_stairs",
              fill="stone_bricks")
    d.set(38, 7, 32, "stone_bricks")
    d.set(38, 7, 33, AIR)
    for z in range(33, 38):
        d.set(39, 3 + (37 - z), z, "stone_brick_wall")
    # charging bridge to the furnace loft (cast-iron girders, plank deck, iron rails)
    for z in (28, 29):
        for x in range(26, 31):
            d.set(x, 7, z, "polished_deepslate" if x in (26, 30) else "spruce_planks")
        d.set(26, 8, z, "iron_bars")
        d.set(30, 8, z, "iron_bars")
        d.set(28, 8, z, "rail[shape=north_south,waterlogged=false]")
        d.set(26, 6, z, stair("polished_deepslate_stairs", "west" if False else "north", "top"))
        d.set(30, 6, z, stair("polished_deepslate_stairs", "north", "top"))


def hw_river(d, L):
    """L3 river along the back of the works and the cast-iron arch bridge (Ironbridge) at x 47..51."""
    water_strip(d, 0, 41, d.sx - 1, 44)
    for x in range(d.sx):
        d.set(x, 1, 40, "stone_bricks")
        d.set(x, 1, 45, "stone_bricks")
        if not 47 <= x <= 51:
            d.set(x, 2, 40, "stone_brick_wall")
    d.set(0, 1, 41, "mossy_stone_bricks")                  # weirs at the plot edges keep the water in
    for z in range(41, 45):
        d.set(0, 1, z, "mossy_stone_bricks")
        d.set(d.sx - 1, 1, z, "mossy_stone_bricks")
    for x in range(d.sx):
        for z in (46, 47, 48):
            if not 47 <= x <= 51:
                d.set(x, 1, z, "coarse_dirt" if z == 47 else "grass_block[snowy=false]")
    # bridge: deck x 48..50, rails on x 47 and 51, ribs on 47 / 49 / 51
    iron, irst = "polished_deepslate", "polished_deepslate_stairs"
    prof = {38: (2, "s"), 39: (3, "s"), 40: (4, "s"), 41: (4, "b"), 42: (4, "b"), 43: (4, "b"), 44: (4, "b"),
            45: (4, "n"), 46: (3, "n"), 47: (2, "n")}
    for z, (y, k) in prof.items():
        for x in range(47, 52):
            for yy in range(2, y):
                if z in (41, 42, 43, 44):
                    continue
                d.set(x, yy, z, "stone_bricks" if x in (47, 51) or z in (39, 40, 45, 46) else "stone_bricks")
            if k == "b":
                d.set(x, y, z, iron if x in (47, 51) else "spruce_planks")
            else:
                d.set(x, y, z, stair("stone_brick_stairs", "south" if k == "s" else "north")
                      if 48 <= x <= 50 else "stone_bricks")
        if 39 <= z <= 46:
            for x in (47, 51):
                d.set(x, y + 1, z, "iron_bars")
    for x in (47, 49, 51):                                 # the arch rib with its haunches
        d.set(x, 3, 41, stair(irst, "north", "top"))
        d.set(x, 3, 44, stair(irst, "south", "top"))
        d.set(x, 2, 41, iron)
        d.set(x, 2, 44, iron)
    for x in (47, 51):                                     # lamp standards at the ends
        d.set(x, 5, 39, iron)
        d.set(x, 6, 39, "lantern[hanging=false,waterlogged=false]")
        d.set(x, 5, 46, iron)
        d.set(x, 6, 46, "lantern[hanging=false,waterlogged=false]")
    d.set(49, 5, 38, AIR)
    for z in range(46, 49):
        for x in range(48, 51):
            d.set(x, 1, z, "gravel")


