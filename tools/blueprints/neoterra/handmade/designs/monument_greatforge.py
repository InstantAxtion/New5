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
HW_SIZE = (57, 40, 51)
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
        hw_tollhouse(d, L)
        hw_chimney(d, L)
    if L >= 4:
        hw_new_furnace(d, L)
        hw_engine_house(d, L)
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
    """L3 river along the back of the works and the cast-iron arch bridge (Ironbridge) at x 46..52."""
    water_strip(d, 0, 41, d.sx - 1, 45)
    for x in range(d.sx):
        d.set(x, 1, 40, "stone_bricks")
        d.set(x, 1, 46, "stone_bricks")
        if not 46 <= x <= 52:
            d.set(x, 2, 40, "stone_brick_wall")
            d.set(x, 2, 46, "stone_brick_wall")
    for z in range(41, 46):                                # weirs at the plot edges keep the water in
        d.set(0, 1, z, "mossy_stone_bricks")
        d.set(d.sx - 1, 1, z, "mossy_stone_bricks")
    for x in range(d.sx):
        for z in (47, 48, 49, 50):
            d.set(x, 1, z, "coarse_dirt" if z == 48 else "grass_block[snowy=false]")
    # bridge: deck x 47..51, rails on x 46 and 52, semicircular cast-iron ribs on x 46 / 48 / 50 / 52
    iron, irst, irsl = "polished_deepslate", "polished_deepslate_stairs", "polished_deepslate_slab"
    prof = {37: (2, "s"), 38: (3, "s"), 39: (4, "s"), 40: (5, "s"), 41: (6, "s"), 42: (6, "b"), 43: (6, "b"),
            44: (6, "b"), 45: (6, "n"), 46: (5, "n"), 47: (4, "n"), 48: (3, "n"), 49: (2, "n")}
    for z, (y, k) in prof.items():
        for x in range(46, 53):
            if z <= 40 or z >= 46:                         # masonry abutments under the ramps
                for yy in range(2, y):
                    d.set(x, yy, z, "stone_bricks")
            if k == "b" or x in (46, 52):
                d.set(x, y, z, iron if x in (46, 52) else "spruce_planks")
            else:
                d.set(x, y, z, stair("stone_brick_stairs" if z <= 40 or z >= 46 else irst,
                                     "south" if k == "s" else "north"))
        if 38 <= z <= 48:
            for x in (46, 52):
                d.set(x, y + 1, z, "iron_bars")
    for x in (46, 48, 50, 52):                             # the arch rib
        put(d, [(x, 4, 41, stair(irst, "north", "top")), (x, 5, 42, stair(irst, "north", "top")),
                (x, 5, 43, slab(irsl, "top")), (x, 5, 44, stair(irst, "south", "top")),
                (x, 4, 45, stair(irst, "south", "top")), (x, 2, 41, iron), (x, 3, 41, iron),
                (x, 2, 45, iron), (x, 3, 45, iron)])
    for x in (46, 52):                                     # spandrel rings between rib and deck
        d.set(x, 5, 41, "iron_bars")
        d.set(x, 5, 45, "iron_bars")
    for x in (47, 49, 51):                                 # cross girders under the deck
        d.set(x, 5, 43, slab(irsl, "top"))
    for x, z in ((46, 37), (52, 37), (46, 49), (52, 49)):  # lamp standards at the ends
        d.set(x, 3, z, iron)
        d.set(x, 4, z, "polished_deepslate_wall")
        d.set(x, 5, z, "lantern[hanging=false,waterlogged=false]")
    for z in range(35, 37):
        for x in range(47, 52):
            d.set(x, 1, z, "gravel")


def hw_tollhouse(d, L):
    """L3 bridge toll house: brick ground storey, timber-framed upper storey, hipped roof, toll board."""
    X1, X2, Z1, Z2 = 40, 45, 29, 35
    rect(d, X1, Z1, X2, Z2, 1, "stone_bricks")
    hw_brick_walls(d, X1, Z1, X2, Z2, 2, 5)
    ring(d, X1, Z1, X2, Z2, 6, "dark_oak_planks")
    for x in range(X1, X2 + 1):
        for z in range(Z1, Z2 + 1):
            if x in (X1, X2) or z in (Z1, Z2):
                for y in range(7, 10):
                    post = (x in (X1, X2) and z in (Z1, Z2)) or (x in (X1, X2) and z == 32) or (z in (Z1, Z2) and x == 42)
                    d.set(x, y, z, logb("stripped_dark_oak_log") if post else "calcite")
            else:
                d.set(x, 6, z, "spruce_planks")
    ring(d, X1, Z1, X2, Z2, 10, "dark_oak_planks")
    d.hip(X1, Z1, X2, Z2, 11, "deepslate_tile_stairs", "deepslate_tile_slab", overhang=1)
    d.door(X2, 2, 32, "east", "dark_oak")
    for z in (30, 34):
        d.window(X2, 3, z, X2, 4, z)
    d.window(X1, 3, 30, X1, 4, 30)
    d.window(42, 3, Z1, 43, 4, Z1)
    d.window(42, 3, Z2, 43, 4, Z2)
    for x, z in ((X2, 31), (X2, 33), (X1, 33), (43, Z1), (44, Z2)):
        d.window(x, 7, z, x, 8, z)
    d.sign(X2 + 1, 4, 31, "east", ["IRON BRIDGE", "TOLLS", "Coach 2s 6d", "Foot 1/2d"], "dark_oak")
    put(d, [(X2 + 1, 4, 33, "lantern[hanging=false,waterlogged=false]"), (X2 + 1, 3, 33, "stone_brick_wall")])
    for y in range(2, 15):                                 # chimney stack on the west wall
        d.set(X1 - 1, y, 34, "bricks")
    d.set(X1 - 1, 15, 34, "terracotta")
    # ground floor: the toll office
    put(d, [(44, 2, 30, slab("dark_oak_slab", "top")), (44, 3, 30, cand(3)), (43, 2, 30, stair("dark_oak_stairs", "west")),
            (44, 2, 34, slab("dark_oak_slab", "top")), (44, 3, 34, "chest[facing=west,type=single,waterlogged=false]"),
            (41, 2, 34, "furnace[facing=east,lit=true]"), (41, 3, 34, "bricks"),
            (42, 2, 33, "dark_oak_fence"), (42, 3, 33, plate("dark_oak")), (43, 2, 33, stair("dark_oak_stairs", "east")),
            (41, 2, 30, "barrel[facing=up,open=false]"), (41, 3, 30, "potted_red_tulip"),
            (42, 2, 31, "red_carpet"), (43, 2, 31, "red_carpet"), (42, 2, 32, "red_carpet"), (43, 2, 32, "red_carpet")])
    for y in range(2, 7):
        d.set(41, y, 31, "ladder[facing=east,waterlogged=false]")
    lamp(d, 43, 5, 32)
    # upper floor: the toll keeper's bedroom
    bed(d, 43, 7, 34, "south", "red")
    put(d, [(44, 7, 34, slab("spruce_slab", "top")), (44, 8, 34, cand(1)),
            (42, 7, 34, "chest[facing=north,type=single,waterlogged=false]"),
            (41, 7, 34, "barrel[facing=up,open=false]"), (41, 8, 34, "barrel[facing=east,open=false]"),
            (44, 7, 30, "water_cauldron[level=3]"), (42, 7, 30, "dark_oak_fence"), (42, 8, 30, plate("dark_oak")),
            (43, 7, 30, stair("dark_oak_stairs", "east")),
            (42, 7, 32, "white_carpet"), (43, 7, 32, "white_carpet"), (44, 7, 32, "white_carpet"),
            (43, 7, 31, "white_carpet")])
    lamp(d, 43, 9, 32)


def hw_chimney(d, L):
    """The great chimney (L3, raised at L4/L5): square brick shaft with stone bands, corbelled cap, flue duct."""
    top = {3: 29, 4: 34, 5: 37}[L]
    X1, Z1 = 1, 31
    for y in range(2, top + 1):
        for x in range(X1, X1 + 3):
            for z in range(Z1, Z1 + 3):
                if (x, z) == (X1 + 1, Z1 + 1) and y >= 3:
                    continue
                band = y in (2, 12, 20, 28) or (y == top)
                d.set(x, y, z, "stone_bricks" if band else "bricks")
    for x in range(X1 - 1, X1 + 4):                       # corbel ring
        for z in range(Z1 - 1, Z1 + 4):
            if x in (X1 - 1, X1 + 3) or z in (Z1 - 1, Z1 + 3):
                if not d.bp.inside(x, top, z):
                    continue
                f = "north" if z == Z1 - 1 else "south" if z == Z1 + 3 else "west" if x == X1 - 1 else "east"
                d.set(x, top, z, stair("stone_brick_stairs", f, "top"))
    for x, z in ((X1, Z1), (X1 + 2, Z1), (X1, Z1 + 2), (X1 + 2, Z1 + 2)):
        d.set(x, top + 1, z, "bricks")
    # plinth with a stoke-hole arch and the flue duct to the engine house boiler
    put(d, [(X1 + 1, 2, Z1, "iron_bars"), (X1 + 1, 2, Z1 - 1, "stone_brick_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]")])
    for x in range(X1 + 3, 6):
        d.set(x, 2, Z1 + 1, "bricks")
        d.set(x, 3, Z1 + 1, stair("brick_stairs", "north"))


def hw_new_furnace(d, L):
    """L4 New Furnace: second furnace hall (ridge north-south) with its own stack; blast furnaces 4 (+5 at L5)."""
    X1, X2, Z1, Z2 = 5, 17, 16, 26
    rect(d, X1, Z1, X2, Z2, 1, "packed_mud")
    hw_brick_walls(d, X1, Z1, X2, Z2, 2, 8)
    ring(d, X1, Z1, X2, Z2, 5, "stone_bricks")
    d.gable(X1, Z1, X2, Z2, 9, "z", "deepslate_tile_stairs", "deepslate_tile_slab", "bricks", overhang=1)
    hw_arch(d, 10, 2, Z1, "x", 3, 3)
    hw_arch(d, X2, 2, 22, "z", 3, 3)                       # side arch to the yard
    for x in (7, 15):
        hw_window(d, x, Z1, 4, 2)
        hw_window(d, x, Z2, 4, 2)
    for z in (18, 24):
        hw_window(d, X1, z, 4, 2)
    hw_window(d, X2, 18, 4, 2)
    d.window(11, 12, Z1, 11, 13, Z1)
    T = HW_STACK[L] - 2
    for y in range(2, 11):
        for x in range(9, 14):
            for z in range(19, 24):
                hollow = 10 <= x <= 12 and 20 <= z <= 22 and y >= 5
                d.set(x, y, z, AIR if hollow else ("stone_bricks" if y == 2 else "bricks"))
    for y in range(11, T + 1):
        for x in range(10, 13):
            for z in range(20, 23):
                d.set(x, y, z, AIR if (x, z) == (11, 21) else ("stone_bricks" if y % 6 == 0 else "bricks"))
    for x in range(9, 14):
        for z in range(19, 24):
            if x in (9, 13) or z in (19, 23):
                f = "north" if z == 19 else "south" if z == 23 else "west" if x == 9 else "east"
                d.set(x, T, z, stair("stone_brick_stairs", f, "top"))
    # tapping arch north: blast furnace no. 4 and its pig bed
    d.item(11, 2, 19, "blast_furnace", "north")
    put(d, [(10, 3, 19, stair("brick_stairs", "west", "top")), (12, 3, 19, stair("brick_stairs", "east", "top")),
            (11, 3, 19, AIR), (11, 4, 19, "chiseled_stone_bricks")])
    rect(d, 9, 17, 13, 18, 1, "sand")
    for x, z in ((11, 17), (11, 18), (9, 17), (10, 17), (12, 17), (13, 17)):
        d.set(x, 2, z, plate())
    # blast main from the blowing engine (iron pipe along the east bay into the stack)
    for z in range(21, 26):
        d.set(15, 4, z, "iron_bars")
    for x in (14,):
        d.set(x, 4, 21, "iron_bars")
    put(d, [(15, 2, 25, "polished_deepslate"), (15, 3, 25, "polished_deepslate"),
            (16, 2, 19, "anvil[facing=north]"), (16, 2, 17, "water_cauldron[level=3]"),
            (16, 2, 25, "barrel[facing=up,open=false]"), (16, 3, 25, "barrel[facing=west,open=false]"),
            (14, 2, 25, "chest[facing=north,type=single,waterlogged=false]"),
            (6, 2, 25, "coal_block"), (7, 2, 25, "coal_block"), (6, 2, 24, "coal_block"), (6, 3, 25, "black_carpet"),
            (7, 3, 25, "black_carpet"), (6, 3, 24, "black_carpet"),
            (6, 2, 17, "lava_cauldron"), (7, 2, 17, "cauldron"), (6, 2, 18, "grindstone[face=floor,facing=east]")])
    for x, z in ((7, 21), (15, 18), (11, 25), (7, 18)):
        lamp(d, x, 5, z)
    if L >= 5:
        # second tap on the west face: blast furnace no. 5, with its own sow channel
        d.item(9, 2, 21, "blast_furnace", "west")
        put(d, [(9, 3, 20, stair("brick_stairs", "north", "top")), (9, 3, 22, stair("brick_stairs", "south", "top")),
                (9, 3, 21, AIR), (9, 4, 21, "chiseled_stone_bricks")])
        for x in (6, 7, 8):
            d.set(x, 1, 21, "sand")
            d.set(x, 2, 21, plate())
        for z in (20, 22):
            d.set(7, 1, z, "sand")
            d.set(7, 2, z, plate())


def hw_engine_house(d, L):
    """L4 blowing-engine house: tall three-storey brick house, the beam rocking out of the bob wall."""
    X1, X2, Z1, Z2 = 6, 14, 28, 36
    rect(d, X1, Z1, X2, Z2, 1, "stone_bricks")
    hw_brick_walls(d, X1, Z1, X2, Z2, 2, 15)
    for y in (7, 11):
        ring(d, X1, Z1, X2, Z2, y, "stone_bricks")
        for x in range(X1 + 1, X2):
            for z in range(Z1 + 1, Z2):
                d.set(x, y, z, "spruce_planks")
    d.gable(X1, Z1, X2, Z2, 16, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "bricks", overhang=1)
    hw_arch(d, 9, 2, Z2, "x", 3, 3)                        # cylinder door (engine erected through it)
    d.door(10, 2, Z2, "south", "dark_oak")
    d.fill(9, 2, Z2, 9, 3, Z2, "dark_oak_planks")
    d.fill(11, 2, Z2, 11, 3, Z2, "dark_oak_planks")
    for z in (30, 34):
        for y0 in (3, 8, 12):
            d.window(X1, y0, z, X1, y0 + 1, z)
            d.window(X2, y0, z, X2, y0 + 1, z)
    # the beam (bob) rocking out over the bob wall
    for z in range(25, 35):
        d.set(10, 13, z, logb("stripped_dark_oak_log", "z"))
    d.set(10, 14, 32, "stone_bricks")
    for y in range(9, 13):
        d.set(10, y, 25, "chain[axis=y,waterlogged=false]")
    d.set(10, 13, 24, logb("stripped_dark_oak_log", "z"))
    # ground floor: blowing cylinder, boiler with fire door, coal, ladder
    for x in range(8, 11):
        for z in range(30, 33):
            for y in range(2, 5):
                d.set(x, y, z, "polished_deepslate" if (x, z) != (9, 31) or y < 4 else "iron_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
    for y in range(5, 7):
        d.set(9, y, 31, "chain[axis=y,waterlogged=false]")
    put(d, [(7, 2, 35, "furnace[facing=east,lit=true]"), (7, 2, 34, "furnace[facing=east,lit=true]"),
            (7, 3, 35, "bricks"), (7, 3, 34, "bricks"), (8, 2, 35, "water_cauldron[level=3]"),
            (13, 2, 35, "coal_block"), (13, 3, 35, "black_carpet"), (12, 2, 35, "coal_block"),
            (13, 2, 32, "barrel[facing=up,open=false]"), (13, 2, 33, "barrel[facing=up,open=false]"),
            (11, 2, 29, "lever[face=floor,facing=north,powered=false]"), (12, 2, 29, "grindstone[face=floor,facing=north]")])
    for y in range(2, 8):
        d.set(13, y, 29, "ladder[facing=west,waterlogged=false]")
    lamp(d, 11, 6, 34)
    lamp(d, 7, 6, 30)
    # middle floor: valve gear and the engineman's bench
    put(d, [(9, 8, 31, "chain[axis=y,waterlogged=false]"), (9, 9, 31, "chain[axis=y,waterlogged=false]"),
            (8, 8, 30, "lever[face=wall,facing=east,powered=false]"), (7, 8, 30, "polished_deepslate"),
            (7, 9, 30, "lever[face=wall,facing=east,powered=false]"),
            (7, 8, 33, "crafting_table"), (7, 8, 34, slab("spruce_slab", "top")), (7, 9, 34, cand(2)),
            (8, 8, 34, stair("spruce_stairs", "east")),
            (13, 8, 34, "chest[facing=west,type=single,waterlogged=false]"), (13, 8, 33, "barrel[facing=up,open=false]"),
            (12, 8, 35, "barrel[facing=up,open=false]"), (13, 9, 33, "candle[candles=3,lit=false,waterlogged=false]"),
            (11, 8, 31, "grindstone[face=floor,facing=east]"), (11, 8, 32, "grindstone[face=floor,facing=east]")])
    d.set(13, 7, 29, "ladder[facing=west,waterlogged=false]")
    for y in range(8, 12):
        d.set(7, y, 35, "ladder[facing=east,waterlogged=false]")
    lamp(d, 10, 10, 33)
    # beam floor: the bob's pivot on the bob wall, oil cans, the works bell
    put(d, [(10, 12, 32, "polished_deepslate"), (9, 12, 32, "polished_deepslate"), (11, 12, 32, "polished_deepslate"),
            (12, 12, 34, slab("spruce_slab", "top")), (12, 13, 34, cand(4)), (13, 12, 34, "barrel[facing=up,open=false]"),
            (13, 12, 35, "barrel[facing=up,open=false]"), (8, 12, 30, "chest[facing=east,type=single,waterlogged=false]"),
            (7, 12, 31, slab("spruce_slab", "top")), (7, 13, 31, "lantern[hanging=false,waterlogged=false]"),
            (12, 12, 30, "bell[attachment=floor,facing=north,powered=false]"),
            (9, 12, 34, "yellow_carpet"), (10, 12, 34, "yellow_carpet"), (9, 12, 35, "yellow_carpet"), (10, 12, 35, "yellow_carpet")])
    lamp(d, 11, 14, 34)
    d.sign(10, 5, Z2 + 1, "south", ["BLOWING", "ENGINE", "1776", ""], "dark_oak")
