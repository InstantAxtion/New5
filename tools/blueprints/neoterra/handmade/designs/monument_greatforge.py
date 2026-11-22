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
HW_SIZE = (57, 40, 59)
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
    if L == 1:
        # open-sided forge shed: dwarf walls with oak posts and a wall plate, the front open between posts
        for z in range(3, 11):
            for x in (1, 9):
                d.set(x, 3, z, logb("stripped_dark_oak_log") if z in (6, 7) else AIR)
                d.set(x, 4, z, logb("stripped_dark_oak_log", "z"))
        for x in range(2, 9):
            for y in (1, 2, 3):
                d.set(x, y, 2, logb("stripped_dark_oak_log") if x in (3, 7) else AIR)
            d.set(x, 4, 2, logb("stripped_dark_oak_log", "x"))
        d.window(2, 2, 11, 2, 3, 11)
        d.window(8, 2, 11, 8, 3, 11)
    else:
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
    # behind the hall under the eaves: water butt, barrels of charcoal, wall lamps
    put(d, [(23, 2, 28, "barrel[facing=up,open=false]"), (24, 2, 28, "barrel[facing=up,open=false]"),
            (24, 3, 28, "barrel[facing=south,open=false]"), (33, 2, 28, "water_cauldron[level=3]"),
            (34, 2, 28, "composter[level=3]"), (X1 - 1, 2, 24, "barrel[facing=up,open=false]"),
            (X1 - 1, 4, 22, "wall_torch[facing=west]"), (X2 + 1, 4, 22, "wall_torch[facing=east]"),
            (X2 + 1, 2, 25, "grindstone[face=floor,facing=north]")])
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
        hw_lodges(d, L)
    if L >= 5:
        hw_warehouse(d, L)
        hw_ironmaster(d, L)
        hw_south_bank(d, L)
    place_wings(d, HW_WX, HW_WZ, HW_WSIZE, HW_WHUT)
    connect_walls(d)
    return d




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
        for z in (47, 48):
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


def hw_lodges(d, L):
    """L4 works gate between two brick lodges: the Pattern Shop (west) and the Works Office (east)."""
    for X1, X2, door_x, face in ((13, 19, 19, "east"), (37, 43, 37, "west")):
        Z1, Z2 = 3, 12
        rect(d, X1, Z1, X2, Z2, 1, "stone_bricks")
        hw_brick_walls(d, X1, Z1, X2, Z2, 2, 9)
        ring(d, X1, Z1, X2, Z2, 6, "stone_bricks")
        for x in range(X1 + 1, X2):
            for z in range(Z1 + 1, Z2):
                d.set(x, 6, z, "spruce_planks")
        d.gable(X1, Z1, X2, Z2, 10, "z", "deepslate_tile_stairs", "deepslate_tile_slab", "bricks", overhang=1)
        d.door(door_x, 2, 8, face, "dark_oak")
        d.set(door_x, 4, 8, "stone_bricks")
        for x in (X1 + 2, X2 - 2):
            hw_window(d, x, Z1, 3, 2)
            hw_window(d, x, Z1, 7, 2)
            hw_window(d, x, Z2, 3, 2)
        d.window(X1 + 3, 11, Z1, X1 + 3, 12, Z1)
        for z in (5, 10):
            hw_window(d, X1 if face == "east" else X2, z, 3, 2)
            hw_window(d, X1, z, 7, 2)
            hw_window(d, X2, z, 7, 2)
        hw_window(d, door_x, 5, 3, 2)
        # chimney on the outer gable wall
        cx = X1 + 3
        for y in range(2, 16):
            d.set(cx, y, Z2 + 1, "bricks")
        d.set(cx, 16, Z2 + 1, "terracotta")
    # ---- Pattern Shop (x 14..18, z 4..11): ground floor joinery, pattern store above
    put(d, [(14, 2, 4, "crafting_table"), (15, 2, 4, slab("spruce_slab", "top")), (16, 2, 4, slab("spruce_slab", "top")),
            (15, 3, 4, cand(2)), (15, 2, 5, stair("spruce_stairs", "north")),
            (18, 2, 4, "stonecutter[facing=west]"), (18, 2, 5, "grindstone[face=floor,facing=west]"),
            (14, 2, 7, "spruce_log[axis=z]"), (14, 2, 8, "spruce_log[axis=z]"), (14, 3, 7, "spruce_log[axis=z]"),
            (14, 2, 10, "barrel[facing=up,open=false]"), (14, 2, 11, "barrel[facing=up,open=false]"),
            (14, 3, 11, "barrel[facing=north,open=false]"), (16, 2, 11, shelf("north")), (17, 2, 11, shelf("north")),
            (16, 2, 8, "spruce_fence"), (16, 3, 8, plate("spruce")), (16, 2, 9, stair("spruce_stairs", "south"))])
    for y in range(2, 7):
        d.set(18, y, 10, "ladder[facing=west,waterlogged=false]")
    lamp(d, 16, 5, 6)
    lamp(d, 16, 5, 10)
    put(d, [(14, 7, 4, shelf("east")), (14, 8, 4, shelf("east")), (14, 7, 5, shelf("east")), (14, 8, 5, shelf("east")),
            (14, 7, 6, shelf("east")), (14, 7, 9, shelf("east")), (14, 8, 9, shelf("east")),
            (17, 7, 4, "chest[facing=south,type=single,waterlogged=false]"), (18, 7, 4, "chest[facing=south,type=single,waterlogged=false]"),
            (16, 7, 7, slab("spruce_slab", "top")), (17, 7, 7, slab("spruce_slab", "top")), (16, 8, 7, pot("north")),
            (16, 7, 6, stair("spruce_stairs", "south")), (14, 7, 11, "barrel[facing=up,open=false]"),
            (16, 7, 9, "light_gray_carpet"), (16, 7, 10, "light_gray_carpet"), (15, 7, 10, "light_gray_carpet")])
    lamp(d, 16, 9, 8)
    # ---- Works Office (x 38..42, z 4..11): counting house below, manager's office above
    put(d, [(38, 2, 4, "lectern[facing=south,has_book=true,powered=false]"), (38, 2, 5, stair("dark_oak_stairs", "north")),
            (40, 2, 4, "lectern[facing=south,has_book=true,powered=false]"), (40, 2, 5, stair("dark_oak_stairs", "north")),
            (42, 2, 4, "cartography_table"), (42, 2, 6, "chest[facing=west,type=single,waterlogged=false]"),
            (42, 2, 7, "iron_bars"), (42, 3, 6, "lantern[hanging=false,waterlogged=false]"),
            (42, 2, 11, "furnace[facing=north,lit=true]"), (41, 2, 11, "bricks"),
            (39, 2, 9, "dark_oak_fence"), (39, 3, 9, plate("dark_oak")), (39, 2, 10, stair("dark_oak_stairs", "south")),
            (40, 2, 9, stair("dark_oak_stairs", "east")),
            (40, 2, 7, "green_carpet"), (41, 2, 7, "green_carpet"), (40, 2, 8, "green_carpet"), (41, 2, 8, "green_carpet")])
    for y in range(2, 7):
        d.set(38, y, 11, "ladder[facing=east,waterlogged=false]")
    lamp(d, 40, 5, 6)
    lamp(d, 40, 5, 10)
    put(d, [(40, 7, 5, slab("dark_oak_slab", "top")), (41, 7, 5, slab("dark_oak_slab", "top")), (40, 8, 5, cand(3)),
            (41, 8, 5, "potted_fern"), (40, 7, 6, stair("dark_oak_stairs", "south")),
            (38, 7, 4, "bookshelf"), (38, 8, 4, "bookshelf"), (38, 7, 5, "bookshelf"), (38, 8, 5, "bookshelf"),
            (42, 7, 9, stair("dark_oak_stairs", "west")), (42, 7, 10, stair("dark_oak_stairs", "west")),
            (41, 7, 9, "red_carpet"), (40, 7, 9, "red_carpet"), (41, 7, 10, "red_carpet"), (40, 7, 10, "red_carpet"),
            (40, 7, 8, "dark_oak_fence"), (40, 8, 8, plate("dark_oak")), (42, 7, 4, "potted_azalea_bush"),
            (42, 7, 11, "chest[facing=north,type=single,waterlogged=false]")])
    d.set(40, 7, 9, "dark_oak_fence")
    d.set(40, 8, 9, "dark_oak_pressure_plate[powered=false]")
    d.set(40, 7, 8, "red_carpet")
    lamp(d, 40, 9, 7)
    # ---- the gate: dwarf wall with railings, piers with lamps, iron overthrow with the company name
    for x in list(range(20, 26)) + list(range(31, 37)):
        d.set(x, 2, 0, "bricks")
        d.set(x, 3, 0, "iron_bars")
    for x in (26, 30):
        for y in range(2, 6):
            d.set(x, y, 0, "stone_bricks")
        d.set(x, 6, 0, "lantern[hanging=false,waterlogged=false]")
    for x in range(27, 30):
        d.set(x, 6, 0, "iron_bars")
    d.set(28, 7, 0, "iron_bars")
    d.sign(28, 5, 1, "south", ["", "THE COMPANY", "", ""], "dark_oak")


def hw_warehouse(d, L):
    """L5 Great Warehouse with its clock tower: dispatch hall, cast-iron showroom, pattern & drawing loft."""
    X1, X2, Z1, Z2 = 39, 55, 15, 27
    rect(d, X1, Z1, X2, Z2, 1, "stone_bricks")
    hw_brick_walls(d, X1, Z1, X2, Z2, 2, 14)
    for y in (7, 11):
        ring(d, X1, Z1, X2, Z2, y, "stone_bricks")
        for x in range(X1 + 1, X2):
            for z in range(Z1 + 1, Z2):
                d.set(x, y, z, "spruce_planks")
    d.gable(X1, Z1, X2, Z2, 15, "x", "brick_stairs", "brick_slab", "bricks", overhang=1)
    for x in (41, 44, 50, 53):
        for y0 in (3, 8, 12):
            d.window(x, y0, Z1, x, y0 + 1, Z1)
            d.window(x, y0, Z2, x, y0 + 1, Z2)
    for z in (18, 24):
        for y0 in (3, 8, 12):
            d.window(X1, y0, z, X1, y0 + 1, z)
    for y0 in (8, 12):
        d.window(X2, y0, 18, X2, y0 + 1, 18)
    # loading doors on the east end with a hoist beam
    d.double_door(X2, 2, 21, "z", "east", "spruce")
    for y in (8, 12):
        d.fill(X2, y, 21, X2, y + 1, 22, AIR)
        d.set(X2 + 1, y - 1, 21, trap("spruce_trapdoor", "east", "top"))
    for x in (X2, X2 + 1):
        d.set(x, 15, 21, logb("stripped_dark_oak_log", "x"))
    d.set(X2 + 1, 14, 21, "chain[axis=y,waterlogged=false]")
    d.set(X2 + 1, 13, 21, "chain[axis=y,waterlogged=false]")
    # clock tower over the main door (x 45..49, z 14..18)
    TX1, TX2, TZ1, TZ2 = 45, 49, 13, 17
    for y in range(2, 29):
        for x in range(TX1, TX2 + 1):
            for z in range(TZ1, TZ2 + 1):
                edge = x in (TX1, TX2) or z in (TZ1, TZ2)
                if y <= 14 and z >= Z1:
                    continue                               # inside the warehouse below the roof
                if edge:
                    d.set(x, y, z, "stone_bricks" if (x in (TX1, TX2) and z in (TZ1, TZ2)) or y in (15, 22, 28) else "bricks")
                elif y >= 15:
                    d.set(x, y, z, AIR)
    for x in range(TX1 + 1, TX2):
        for z in range(TZ1 + 1, Z1):
            d.set(x, 1, z, "stone_bricks")
            for y in range(2, 15):
                d.set(x, y, z, AIR)
    for x in range(TX1 + 1, TX2):
        d.set(x, 15, Z1, "stone_bricks")
        for y in (2, 3):
            d.set(x, y, TZ1, AIR)
            d.set(x, y, Z1, AIR)
    d.set(47, 4, TZ1, AIR)
    d.set(46, 4, TZ1, stair("brick_stairs", "west", "top"))
    d.set(48, 4, TZ1, stair("brick_stairs", "east", "top"))
    d.set(47, 5, TZ1, "chiseled_stone_bricks")
    d.door(47, 2, Z1, "north", "dark_oak")
    d.set(46, 2, Z1, "bricks"), d.set(48, 2, Z1, "bricks"), d.set(46, 3, Z1, "bricks"), d.set(48, 3, Z1, "bricks")
    lamp(d, 47, 6, 14)
    for face_z, fx in ((TZ1, None),):
        for x in range(46, 49):
            for y in range(23, 26):
                d.set(x, y, TZ1, "calcite")
        d.set(47, 24, TZ1, "black_concrete")
        d.set(47, 25, TZ1, "black_concrete")
        d.set(48, 24, TZ1, "black_concrete")
    for x in (TX1, TX2):
        for z in range(TZ1 + 1, TZ2):
            for y in range(23, 26):
                d.set(x, y, z, "calcite")
        d.set(x, 24, 15, "black_concrete")
        d.set(x, 25, 15, "black_concrete")
    for x in range(46, 49):                                # belfry openings and the bell
        d.set(x, 26, TZ1, AIR) if x == 47 else None
        d.set(x, 27, TZ1, AIR) if x == 47 else None
    for z in (15,):
        d.set(TX1, 26, z, AIR), d.set(TX1, 27, z, AIR), d.set(TX2, 26, z, AIR), d.set(TX2, 27, z, AIR)
    d.set(47, 26, TZ2, AIR), d.set(47, 27, TZ2, AIR)
    d.fill(TX1 + 1, 25, TZ1 + 1, TX2 - 1, 25, TZ2 - 1, "spruce_planks")
    d.set(47, 27, 15, "bell[attachment=ceiling,facing=north,powered=false]")
    d.fill(TX1 + 1, 28, TZ1 + 1, TX2 - 1, 28, TZ2 - 1, "bricks")
    top = d.hip(TX1, TZ1, TX2, TZ2, 29, "deepslate_tile_stairs", "deepslate_tile_slab", overhang=1)
    d.set(47, top + 1, 15, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    d.sign(47, 7, TZ1 - 1, "north", ["GREAT", "WAREHOUSE", "1838", ""], "dark_oak")
    # ---- ground floor: dispatch hall (stair up the west wall)
    stair_run(d, [(40, 2, 16), (40, 3, 17), (40, 4, 18), (40, 5, 19), (40, 6, 20)], "south", "spruce_stairs",
              fill="spruce_planks")
    for z in (18, 19, 20):
        d.set(40, 7, z, AIR)
    for z in (18, 19, 20):
        d.set(41, 8, z, "spruce_fence")
    rows = []
    for x in (43, 44, 45, 50, 51, 52):                     # two aisles of crated castings, two high
        for z in (19, 20):
            rows += [(x, 2, z, "barrel[facing=up,open=false]"), (x, 3, z, "barrel[facing=north,open=false]")]
    put(d, rows)
    put(d, [(43, 2, 24, slab("spruce_slab", "top")), (44, 2, 24, slab("spruce_slab", "top")),
            (43, 3, 24, pot("north")), (44, 3, 24, pot("east")), (45, 2, 24, "cauldron"), (45, 2, 25, "cauldron"),
            (48, 2, 24, "spruce_fence"), (48, 3, 24, plate()), (48, 2, 25, "polished_deepslate"),
            (53, 2, 25, "lectern[facing=north,has_book=true,powered=false]"), (54, 2, 25, "chest[facing=north,type=single,waterlogged=false]"),
            (54, 2, 16, "anvil[facing=east]"), (53, 2, 16, "anvil[facing=east]"), (50, 2, 16, "iron_bars"),
            (51, 2, 16, "iron_bars"), (41, 2, 26, "barrel[facing=up,open=false]"), (42, 2, 26, "barrel[facing=up,open=false]")])
    for x, z in ((44, 17), (51, 17), (44, 22), (51, 22), (48, 26)):
        lamp(d, x, 6, z)
    # ---- first floor: showroom of cast-iron goods
    show = []
    for x, z, item in ((43, 17, "anvil[facing=north]"), (45, 17, "cauldron"), (51, 17, "bell[attachment=floor,facing=north,powered=false]"),
                       (53, 17, "lantern[hanging=false,waterlogged=false]"), (43, 25, "smoker[facing=north,lit=false]"),
                       (45, 25, "furnace[facing=north,lit=false]"), (51, 25, "anvil[facing=east]"), (53, 25, "cauldron")):
        show += [(x, 8, z, "polished_andesite"), (x, 9, z, item)]
    put(d, show)
    put(d, [(47, 8, 20, "iron_bars"), (48, 8, 20, "iron_bars"), (49, 8, 20, "iron_bars"), (47, 9, 20, "iron_bars"),
            (49, 9, 20, "iron_bars"), (48, 9, 20, "iron_bars"),
            (47, 8, 22, stair("dark_oak_stairs", "south")), (48, 8, 22, stair("dark_oak_stairs", "south")),
            (49, 8, 22, stair("dark_oak_stairs", "south")),
            (53, 8, 21, slab("dark_oak_slab", "top")), (53, 9, 21, cand(2)), (52, 8, 21, stair("dark_oak_stairs", "west"))])
    for x in range(43, 54):
        if x in (47, 48, 49):
            continue
        d.set(x, 8, 21, "red_carpet")
    for x in (47, 48, 49):
        d.set(x, 8, 23, "red_carpet")
        d.set(x, 8, 24, "red_carpet")
    for x, z in ((44, 19), (52, 19), (44, 23), (52, 23)):
        lamp(d, x, 10, z)
    for y in range(8, 12):
        d.set(54, y, 26, "ladder[facing=west,waterlogged=false]")
    # ---- second floor: pattern store and drawing office
    loft = []
    for x in (42, 43, 44):                                 # pattern shelving, aisles between
        for z in (17, 18, 19):
            if (x, z) != (43, 18):
                pass
    for z in range(17, 21):
        loft += [(42, 12, z, shelf("east")), (42, 13, z, shelf("east")), (45, 12, z, shelf("west")), (45, 13, z, shelf("west"))]
    for z in range(23, 26):
        loft += [(42, 12, z, shelf("east")), (45, 12, z, shelf("west"))]
    put(d, loft)
    put(d, [(49, 12, 17, "cartography_table"), (50, 12, 17, "cartography_table"), (49, 12, 18, stair("spruce_stairs", "south")),
            (50, 12, 18, stair("spruce_stairs", "south")), (52, 12, 17, "cartography_table"), (52, 12, 18, stair("spruce_stairs", "south")),
            (54, 12, 17, "lectern[facing=west,has_book=true,powered=false]"),
            (49, 12, 24, "crafting_table"), (50, 12, 24, slab("spruce_slab", "top")), (50, 13, 24, pot("north")),
            (51, 12, 24, slab("spruce_slab", "top")), (51, 13, 24, cand(3)), (50, 12, 23, stair("spruce_stairs", "north")),
            (54, 12, 22, "chest[facing=west,type=single,waterlogged=false]"), (54, 12, 23, "chest[facing=west,type=single,waterlogged=false]"),
            (48, 12, 20, "light_gray_carpet"), (49, 12, 20, "light_gray_carpet"), (50, 12, 20, "light_gray_carpet"),
            (51, 12, 20, "light_gray_carpet"), (52, 12, 20, "light_gray_carpet")])
    for x, z in ((43, 22), (48, 19), (52, 21), (48, 25)):
        lamp(d, x, 14, z)
    # under the back eaves: a dray with crates waiting, the porter's barrow, lamps
    put(d, [(49, 2, 28, trap("spruce_trapdoor", "south", "top")), (50, 2, 28, trap("spruce_trapdoor", "south", "top")),
            (51, 2, 28, trap("spruce_trapdoor", "south", "top")), (49, 3, 28, "barrel[facing=up,open=false]"),
            (50, 3, 28, "barrel[facing=east,open=false]"), (48, 2, 28, "spruce_fence"),
            (53, 2, 28, "barrel[facing=up,open=false]"), (54, 2, 28, "cauldron"),
            (47, 5, 28, "wall_torch[facing=south]"), (53, 5, 28, "wall_torch[facing=south]")])


def hw_ironmaster(d, L):
    """L5 the ironmaster's house across the bridge: Georgian brick, hipped roof, porch, parlour and study."""
    X1, X2, Z1, Z2 = 43, 55, 51, 57
    rect(d, X1, Z1, X2, Z2, 1, "stone_bricks")
    hw_brick_walls(d, X1, Z1, X2, Z2, 2, 10, plinth="stone_bricks", quoin="stone_bricks")
    ring(d, X1, Z1, X2, Z2, 6, "stone_bricks")
    for x in range(X1 + 1, X2):
        for z in range(Z1 + 1, Z2):
            d.set(x, 6, z, "oak_planks")
    for z in range(Z1 + 1, Z2):                            # partitions: hall between parlour and dining room
        for y in range(2, 6):
            d.set(47, y, z, "calcite")
            d.set(51, y, z, "calcite")
    d.set(47, 2, 54, AIR), d.set(47, 3, 54, AIR), d.set(51, 2, 55, AIR), d.set(51, 3, 55, AIR)
    for z in range(Z1 + 1, Z2):
        for y in range(7, 11):
            d.set(49, y, z, "calcite")
    d.set(49, 7, 53, AIR), d.set(49, 8, 53, AIR)
    ring(d, X1, Z1, X2, Z2, 11, "stone_bricks")
    d.hip(X1, Z1, X2, Z2, 12, "deepslate_tile_stairs", "deepslate_tile_slab", overhang=1)
    d.door(49, 2, Z1, "north", "dark_oak")
    for x in (45, 53):
        hw_window(d, x, Z1, 3, 2)
        hw_window(d, x, Z2, 3, 2)
    for x in (45, 49, 53):
        hw_window(d, x, Z1, 8, 2)
        hw_window(d, x, Z2, 8, 2)
    for z in (54,):
        hw_window(d, X1, z, 3, 2)
        hw_window(d, X2, z, 3, 2)
    for x in (44, 54):                                     # chimneys on the end walls
        for y in range(2, 17):
            d.set(x, y, 54 if False else Z2 + 1, "bricks")
    # porch on columns
    for x in (48, 50):
        for y in range(2, 5):
            d.set(x, y, Z1 - 1, "stone_brick_wall")
    for x in range(47, 52):
        d.set(x, 5, Z1 - 1, slab("stone_brick_slab"))
    d.set(48, 5, Z1 - 1, "stone_bricks"), d.set(50, 5, Z1 - 1, "stone_bricks")
    d.set(49, 6, Z1 - 1, stair("stone_brick_stairs", "south"))
    # garden: gravel path from the bridge, box hedges, railings
    for z in range(47, Z1 - 1):
        for x in (48, 49, 50):
            d.set(x, 1, z, "gravel")
    for x in list(range(43, 47)) + list(range(52, 56)):
        d.set(x, 2, 48, "oak_leaves[distance=1,persistent=true,waterlogged=false]")
    for x, f in ((44, "poppy"), (45, "oxeye_daisy"), (53, "cornflower"), (54, "allium")):
        d.set(x, 2, 49, f)
    # ---- ground floor: parlour (west), hall with stair ladder, dining room (east)
    put(d, [(44, 2, 56, "bricks"), (45, 2, 56, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]"),
            (46, 2, 56, "bricks"), (44, 3, 56, "bricks"), (45, 3, 56, "bricks"), (46, 3, 56, "bricks"),
            (44, 2, 53, stair("dark_oak_stairs", "west")), (44, 2, 54, stair("dark_oak_stairs", "west")),
            (46, 2, 53, stair("dark_oak_stairs", "north")), (45, 2, 53, "red_carpet"), (45, 2, 54, "red_carpet"),
            (45, 2, 55, "red_carpet"), (44, 2, 52, "bookshelf"), (44, 3, 52, "bookshelf"), (46, 2, 52, "potted_fern"),
            (52, 2, 53, "dark_oak_fence"), (53, 2, 53, "dark_oak_fence"), (52, 3, 53, plate("dark_oak")),
            (53, 3, 53, cand(3)), (52, 2, 52, stair("dark_oak_stairs", "north")), (53, 2, 52, stair("dark_oak_stairs", "north")),
            (52, 2, 54, stair("dark_oak_stairs", "south")), (53, 2, 54, stair("dark_oak_stairs", "south")),
            (54, 2, 56, "smoker[facing=west,lit=false]"), (53, 2, 56, slab("dark_oak_slab", "top")),
            (52, 2, 56, "barrel[facing=up,open=false]"), (54, 2, 52, "chest[facing=west,type=single,waterlogged=false]"),
            (49, 2, 52, "red_carpet"), (49, 2, 53, "red_carpet"), (48, 2, 56, "potted_azalea_bush")])
    for y in range(2, 7):
        d.set(50, y, 56, "ladder[facing=north,waterlogged=false]")
    lamp(d, 45, 5, 54)
    lamp(d, 53, 5, 54)
    lamp(d, 49, 5, 54)
    # ---- upper floor: master bedroom (west) and the ironmaster's study (east)
    bed(d, 45, 7, 56, "south", "blue")
    put(d, [(44, 7, 56, slab("dark_oak_slab", "top")), (44, 8, 56, cand(1)), (46, 7, 56, slab("dark_oak_slab", "top")),
            (44, 7, 52, "chest[facing=east,type=single,waterlogged=false]"), (48, 7, 52, "barrel[facing=up,open=false]"),
            (45, 7, 53, "blue_carpet"), (46, 7, 53, "blue_carpet"), (45, 7, 54, "blue_carpet"), (46, 7, 54, "blue_carpet"),
            (48, 7, 56, "water_cauldron[level=3]"),
            (52, 7, 52, "bookshelf"), (53, 7, 52, "bookshelf"), (54, 7, 52, "bookshelf"), (52, 8, 52, "bookshelf"),
            (53, 8, 52, "bookshelf"), (54, 8, 52, "bookshelf"),
            (53, 7, 55, slab("dark_oak_slab", "top")), (52, 7, 55, slab("dark_oak_slab", "top")), (53, 8, 55, cand(2)),
            (52, 8, 55, "potted_fern"), (53, 7, 54, stair("dark_oak_stairs", "north")),
            (54, 7, 56, "lectern[facing=north,has_book=true,powered=false]"), (50, 7, 52, "cartography_table"),
            (52, 7, 54, "green_carpet"), (51, 7, 54, "green_carpet")])
    lamp(d, 46, 10, 54)
    lamp(d, 52, 10, 54)


def hw_south_bank(d, L):
    """L5 across the river: the erecting shop (long brick shed with a roof lantern) and the coach house."""
    # ---- erecting shop x 2..26, z 50..57
    X1, X2, Z1, Z2 = 2, 26, 50, 57
    rect(d, X1, Z1, X2, Z2, 1, "stone_bricks")
    hw_brick_walls(d, X1, Z1, X2, Z2, 2, 8)
    ring(d, X1, Z1, X2, Z2, 5, "stone_bricks")
    d.gable(X1, Z1, X2, Z2, 9, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "bricks", overhang=1)
    for x in range(X1 + 2, X2 - 1):                        # glazed roof lantern along the ridge
        d.set(x, 13, 53, "glass")
        d.set(x, 13, 54, "glass")
    for x in (4, 8, 12, 16, 20, 24):
        if x != 12:
            hw_window(d, x, Z1, 3, 3)
        hw_window(d, x, Z2, 3, 3)
    hw_arch(d, 11, 2, Z1, "x", 3, 3)
    d.sign(12, 7, Z1 - 1, "north", ["ERECTING", "SHOP", "", ""], "dark_oak")
    for z in (53, 54):
        hw_window(d, X1, z, 3, 3)
        hw_window(d, X2, z, 3, 3)
    # overhead travelling crane on brackets, its hook over the engine being erected
    for x in range(X1 + 1, X2):
        d.set(x, 8, 52, "polished_deepslate_slab[type=top,waterlogged=false]")
        d.set(x, 8, 55, "polished_deepslate_slab[type=top,waterlogged=false]")
    for z in (53, 54):
        d.set(16, 8, z, "polished_deepslate_slab[type=top,waterlogged=false]")
    for y in (5, 6, 7):
        d.set(16, y, 53, "chain[axis=y,waterlogged=false]")
    # an engine under construction: frame, cylinder, flywheel; lathes and benches along the walls
    put(d, [(14, 2, 53, "polished_deepslate"), (15, 2, 53, "polished_deepslate"), (16, 2, 53, "polished_deepslate"),
            (17, 2, 53, "polished_deepslate"), (14, 2, 54, "polished_deepslate"), (17, 2, 54, "polished_deepslate"),
            (16, 3, 53, "cauldron"), (16, 4, 53, "iron_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]"),
            (15, 3, 53, "grindstone[face=floor,facing=east]"),
            (19, 2, 54, "iron_bars"), (19, 3, 54, "iron_bars"), (19, 4, 54, "iron_bars"), (19, 2, 53, "iron_bars"),
            (19, 2, 55, "iron_bars"), (19, 3, 53, "iron_bars"), (19, 3, 55, "iron_bars"),
            (3, 2, 56, "crafting_table"), (4, 2, 56, slab("spruce_slab", "top")), (5, 2, 56, slab("spruce_slab", "top")),
            (4, 3, 56, cand(2)), (5, 3, 56, "lantern[hanging=false,waterlogged=false]"), (4, 2, 55, stair("spruce_stairs", "north")),
            (7, 2, 56, "grindstone[face=floor,facing=north]"), (8, 2, 56, "grindstone[face=floor,facing=north]"),
            (10, 2, 56, "stonecutter[facing=north]"), (12, 2, 56, "anvil[facing=east]"),
            (22, 2, 56, "chest[facing=north,type=single,waterlogged=false]"), (23, 2, 56, "barrel[facing=up,open=false]"),
            (24, 2, 56, "barrel[facing=up,open=false]"), (25, 2, 56, "barrel[facing=up,open=false]"),
            (25, 3, 56, "barrel[facing=west,open=false]"), (25, 2, 51, "smithing_table"),
            (3, 2, 51, "barrel[facing=up,open=false]"), (4, 2, 51, "iron_bars"), (5, 2, 51, "iron_bars"),
            (22, 2, 51, "lectern[facing=south,has_book=true,powered=false]"),
            (8, 2, 53, "yellow_carpet"), (9, 2, 53, "yellow_carpet"), (8, 2, 54, "yellow_carpet"), (9, 2, 54, "yellow_carpet")])
    for x in (5, 10, 21, 24):
        lamp(d, x, 5, 54 if x % 2 else 53)
    # ---- coach house x 30..40, z 51..57: two stalls, carriage bay, tack room, hay loft
    X1, X2, Z1, Z2 = 30, 40, 51, 57
    rect(d, X1, Z1, X2, Z2, 1, "stone_bricks")
    hw_brick_walls(d, X1, Z1, X2, Z2, 2, 8)
    for x in range(X1 + 1, X2):
        for z in range(Z1 + 1, Z2):
            d.set(x, 6, z, "spruce_planks")
    d.gable(X1, Z1, X2, Z2, 9, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "bricks", overhang=1)
    hw_arch(d, 34, 2, Z1, "x", 3, 3)
    for x in (32, 38):
        hw_window(d, x, Z1, 3, 2)
        hw_window(d, x, Z2, 3, 2)
    d.set(35, 7, Z1, AIR), d.set(35, 8, Z1, AIR)          # hay door
    for y in range(9, 13):                                 # cupola on the ridge
        pass
    d.set(35, 13, 54, "dark_oak_fence")
    d.set(35, 14, 54, slab("deepslate_tile_slab"))
    for z in range(52, 57):
        d.set(33, 2, z, "dark_oak_fence") if z != 52 else None
        d.set(37, 2, z, "dark_oak_fence") if z != 52 else None
    put(d, [(31, 2, 56, "hay_block[axis=y]"), (31, 2, 55, "water_cauldron[level=3]"), (32, 2, 56, "hay_block[axis=x]"),
            (31, 2, 53, "barrel[facing=up,open=false]"), (32, 3, 56, "hay_block[axis=y]"),
            (34, 2, 55, trap("spruce_trapdoor", "north", "top")), (35, 2, 55, trap("spruce_trapdoor", "north", "top")),
            (36, 2, 55, trap("spruce_trapdoor", "north", "top")), (35, 2, 56, "spruce_fence"),
            (34, 2, 54, "dark_oak_trapdoor[facing=west,half=bottom,open=true,powered=false,waterlogged=false]"),
            (36, 2, 54, "dark_oak_trapdoor[facing=east,half=bottom,open=true,powered=false,waterlogged=false]"),
            (39, 2, 56, "chest[facing=north,type=single,waterlogged=false]"), (38, 2, 56, "barrel[facing=up,open=false]"),
            (39, 2, 54, "leather_horse_armor" if False else "lectern[facing=west,has_book=false,powered=false]"),
            (39, 3, 53, trap("spruce_trapdoor", "west", open_=True)), (38, 2, 53, "brown_carpet"), (39, 2, 53, "brown_carpet")])
    for y in range(2, 7):
        d.set(39, y, 52, "ladder[facing=west,waterlogged=false]")
    lamp(d, 32, 5, 54)
    lamp(d, 35, 5, 53)
    lamp(d, 38, 5, 55)
    put(d, [(31, 7, 56, "hay_block[axis=x]"), (32, 7, 56, "hay_block[axis=x]"), (33, 7, 56, "hay_block[axis=x]"),
            (31, 7, 55, "hay_block[axis=x]"), (31, 8, 56, "hay_block[axis=x]"), (32, 7, 55, "hay_block[axis=y]"),
            (37, 7, 56, "white_wool"), (38, 7, 56, "white_wool"), (38, 8, 56, "white_carpet"), (37, 7, 52, "barrel[facing=up,open=false]"),
            (31, 7, 52, "hay_block[axis=z]"), (33, 7, 53, "composter[level=5]")])
    lamp(d, 35, 8, 55)
    # paths along the south bank to both doors
    for x in range(2, 46):
        d.set(x, 1, 48, "coarse_dirt")
    for z in range(48, 51):
        d.set(12, 1, z, "gravel"), d.set(35, 1, z, "gravel")


# =============================================================================================================
#                              CASCADIA – mountain smelter and stamp mill
# =============================================================================================================
# The smelter (L1) stands at the foot of a hill; the stamp mill climbs the hill in tiers to the west (L2 tiers 1-2,
# L3 tier 3 + the ore trestle to the furnace top, L4 the ore-bin tier and the timber headframe), the camp grows to
# the east (L3 assay office with its false front, L4 bunk & cook house, L5 water tower + flume, boiler house).
CA_SIZE = (49, 44, 58)
CA_WX, CA_WZ, CA_WSIZE, CA_WHUT = (2, 36), 1, (11, 28, 13), (2, 1, 3)
CA_ROCK = ("cobblestone", "mossy_cobblestone", "andesite", "cobblestone", "tuff", "cobblestone")


def rock(x, y, z):
    return CA_ROCK[(x * 7 + y * 3 + z * 5) % len(CA_ROCK)]


def caw(rel, L):
    """Cascadia wing: a rubble-stone FURNACE TOWER with a timber forge shed in front (symmetric about x = 5)."""
    d = Design("Cascadia", rel, CA_WSIZE, gy=0, paving="coarse_dirt")
    CH = {1: 13, 2: 15, 3: 17, 4: 19, 5: 21}[L]
    rect(d, 2, 2, 8, 6, 0, "spruce_planks")
    # forge shed x 1..9, z 1..7: log posts, plank walls (half walls at L1), gable roof running into the stack
    WT = 3
    for x in range(1, 10):
        for z in range(1, 8):
            if not (x in (1, 9) or z in (1, 7)):
                continue
            for y in range(1, WT + 1):
                post = (x in (1, 9) and z in (1, 4, 7)) or (z == 1 and x in (3, 7))
                if post:
                    st = logb("spruce_log")
                elif L == 1 and y == 3:
                    st = AIR
                else:
                    st = "spruce_planks" if y < 3 else "stripped_spruce_log[axis=x]" if z in (1, 7) else "stripped_spruce_log[axis=z]"
                d.set(x, y, z, st)
    for x in range(1, 10):
        d.set(x, 4, 1, logb("spruce_log", "x"))
        d.set(x, 4, 7, logb("spruce_log", "x"))
    for z in range(1, 8):
        d.set(1, 4, z, logb("spruce_log", "z"))
        d.set(9, 4, z, logb("spruce_log", "z"))
    d.gable(1, 1, 9, 7, 5, "z", "spruce_stairs", "spruce_slab", "spruce_planks", overhang=1)
    d.door(5, 1, 1, "north", "spruce")
    if L >= 2:
        for x, z in ((1, 3), (1, 6), (9, 3), (9, 6)):
            d.window(x, 2, z, x, 3, z)
        d.window(2, 2, 1, 2, 3, 1)
        d.window(8, 2, 1, 8, 3, 1)
    # the furnace tower x 3..7, z 7..11: battered rubble stack, sealed core, arch with the fire
    for y in range(1, 10):
        for x in range(3, 8):
            for z in range(7, 12):
                if 4 <= x <= 6 and 8 <= z <= 10 and y >= 3:
                    d.set(x, y, z, AIR)
                elif y == 9 and (x in (3, 7) or z in (7, 11)):
                    f = "south" if z == 7 else "north" if z == 11 else "east" if x == 3 else "west"
                    d.set(x, y, z, stair("cobblestone_stairs", f))
                else:
                    d.set(x, y, z, rock(x, y, z))
    for y in range(9, CH + 1):
        for x in range(4, 7):
            for z in range(8, 11):
                d.set(x, y, z, AIR if (x, z) == (5, 9) else ("stone_bricks" if y == CH else rock(x, y, z)))
    put(d, [(5, 1, 7, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]"), (5, 2, 7, AIR),
            (4, 2, 7, stair("cobblestone_stairs", "west", "top")), (6, 2, 7, stair("cobblestone_stairs", "east", "top")),
            (5, 3, 7, logb("stripped_spruce_log", "x")), (5, 1, 8, "magma_block"), (5, 2, 8, AIR)])
    d.hut(*CA_WHUT, facing="east")
    # the smithy
    d.item(3, 1, 6, "smithing_table")
    put(d, [(4, 1, 7, "piston[extended=false,facing=east]"), (5, 1, 5, "anvil[facing=east]"),
            (7, 1, 6, "water_cauldron[level=3]"), (8, 1, 4, "grindstone[face=floor,facing=west]"),
            (8, 1, 2, "barrel[facing=up,open=false]"), (8, 1, 3, "coal_block"), (8, 2, 3, "black_carpet"),
            (2, 2, 5, trap("spruce_trapdoor", "east", open_=True)), (2, 2, 6, trap("spruce_trapdoor", "east", open_=True)),
            (2, 1, 5, "chest[facing=east,type=single,waterlogged=false]")])
    lamp(d, 5, 3, 3)
    lamp(d, 5, 3, 6) if L >= 3 else None
    d.sign(5, 3, 0, "north", ["", "SMITHY", "", ""], "spruce")
    if L >= 2:
        # woodpile and ore heap beside the shed, quench barrel at the door
        put(d, [(0, 1, 2, logb("spruce_log", "z")), (0, 1, 3, logb("spruce_log", "z")), (0, 2, 2, logb("spruce_log", "z")),
                (10, 1, 2, "iron_ore"), (10, 1, 3, "gravel"), (10, 2, 2, "iron_ore"),
                (7, 1, 0, "barrel[facing=up,open=false]"), (3, 1, 0, "water_cauldron[level=3]")])
    if L >= 3:
        # charging gallery around the chimney on the tower top, ladder up the back
        for x in range(2, 9):
            for z in range(6, 13):
                if 4 <= x <= 6 and 8 <= z <= 10:
                    continue
                d.set(x, 9, z, "spruce_planks")
                if (x in (2, 8) or z in (6, 12)) and (x, z) != (5, 12):
                    d.set(x, 10, z, "spruce_fence")
        for x, z in ((2, 6), (8, 6), (2, 12), (8, 12)):
            for y in range(2, 9):
                if d.get(x, y, z) == AIR:
                    d.set(x, y, z, logb("spruce_log"))
        for y in range(1, 10):
            d.set(5, y, 12, "ladder[facing=south,waterlogged=false]")
        d.set(5, 10, 12, AIR)
        put(d, [(2, 11, 6, "lantern[hanging=false,waterlogged=false]"), (8, 11, 6, "lantern[hanging=false,waterlogged=false]"),
                (7, 10, 11, "barrel[facing=up,open=false]"), (3, 10, 11, "iron_ore"), (3, 10, 10, "coal_block")])
    if L >= 4:
        # charging house roof on posts over the gallery
        for x, z in ((3, 7), (7, 7), (3, 11), (7, 11)):
            for y in range(10, 13):
                d.set(x, y, z, logb("spruce_log"))
        d.gable(3, 7, 7, 11, 13, "x", "spruce_stairs", "spruce_slab", "spruce_planks", overhang=1)
        for y in range(13, CH + 1):
            for x in range(4, 7):
                for z in range(8, 11):
                    d.set(x, y, z, AIR if (x, z) == (5, 9) else ("stone_bricks" if y == CH else rock(x, y, z)))
        lamp(d, 2, 4, 0)
        lamp(d, 8, 4, 0)
    if L >= 5:
        put(d, [(5, CH + 1, 8, "lightning_rod[facing=up,powered=false,waterlogged=false]"),
                (0, 1, 5, "hay_block[axis=y]"), (10, 1, 5, "composter[level=6]")])
        d.banner(5, 4, 0, "north", "orange")
    connect_walls(d)
    return d


def ca_logwall(d, x1, z1, x2, z2, y1, y2, base=None):
    """Log-cabin walls: horizontal spruce logs, stripped corner posts, optional rubble footing course."""
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if not (x in (x1, x2) or z in (z1, z2)):
                continue
            for y in range(y1, y2 + 1):
                if x in (x1, x2) and z in (z1, z2):
                    st = logb("stripped_spruce_log")
                elif base and y == y1:
                    st = rock(x, y, z)
                else:
                    st = logb("spruce_log", "x" if z in (z1, z2) else "z")
                d.set(x, y, z, st)


def ca_hill(d, x1, z1, x2, z2, ytop):
    """Terrace of the hillside: rubble retaining faces, earth inside, up to ytop (inclusive)."""
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            face = x in (x1, x2) or z in (z1, z2)
            for y in range(2, ytop + 1):
                d.set(x, y, z, rock(x, y, z) if face else ("dirt" if (x + z + y) % 3 else "coarse_dirt"))


def ca_smelter(d, L):
    """L1 the smelter: battered rubble blast-furnace stack with its hearth chamber, timber casting shed in front."""
    # ---- casting shed x 17..31, z 13..23
    SX1, SX2, SZ1, SZ2 = 17, 31, 13, 23
    for x in range(SX1, SX2 + 1):
        for z in range(SZ1, SZ2 + 1):
            d.set(x, 1, z, "sand" if 22 <= x <= 26 else "packed_mud")
    for x in range(SX1, SX2 + 1):
        for z in range(SZ1, SZ2 + 1):
            if not (x in (SX1, SX2) or z in (SZ1, SZ2)):
                continue
            post = (x in (SX1, SX2) and z in (SZ1, 18, SZ2)) or (z in (SZ1, SZ2) and x in (21, 27))
            for y in range(2, 6):
                if post:
                    d.set(x, y, z, logb("spruce_log"))
                elif z == SZ2:
                    continue                                # open to the furnace
                elif y <= 3 and not (z == SZ1 and 22 <= x <= 26):
                    d.set(x, y, z, "spruce_planks" if y == 2 else "stripped_spruce_log[axis=%s]" % ("x" if z == SZ1 else "z"))
    for x in range(SX1, SX2 + 1):
        d.set(x, 6, SZ1, logb("spruce_log", "x"))
        d.set(x, 6, SZ2, logb("spruce_log", "x"))
    for z in range(SZ1, SZ2 + 1):
        d.set(SX1, 6, z, logb("spruce_log", "z"))
        d.set(SX2, 6, z, logb("spruce_log", "z"))
    d.gable(SX1, SZ1, SX2, SZ2, 7, "x", "spruce_stairs", "spruce_slab", "spruce_planks", overhang=1)
    d.sign(24, 9, SZ1 - 1, "north", ["CASCADIA", "SMELTING CO.", "", ""], "spruce")
    # ---- the stack: 9x9 base with the hearth chamber, 7x7 then 5x5 shaft, battered with stair courses
    T = {1: 18, 2: 21, 3: 23, 4: 25, 5: 27}[L]
    for y in range(2, 8):
        for x in range(20, 29):
            for z in range(24, 33):
                d.set(x, y, z, rock(x, y, z) if x in (20, 28) or z in (24, 32) else AIR)
    for x in range(20, 29):
        for z in range(24, 33):
            edge = x in (20, 28) or z in (24, 32)
            if 23 <= x <= 25 and 27 <= z <= 29:
                continue
            if edge:
                f = "south" if z == 24 else "north" if z == 32 else "east" if x == 20 else "west"
                d.set(x, 8, z, stair("cobblestone_stairs", f))
                d.set(x, 7, z, "stone_bricks")
            else:
                d.set(x, 8, z, rock(x, 8, z))
    for y in range(9, T + 1):
        r = 3 if y <= 13 else 2
        for x in range(24 - r, 25 + r):
            for z in range(28 - r, 29 + r):
                if 23 <= x <= 25 and 27 <= z <= 29:
                    continue
                edge = x in (24 - r, 24 + r) or z in (28 - r, 28 + r)
                if y == 13 and edge:
                    f = "south" if z == 28 - r else "north" if z == 28 + r else "east" if x == 24 - r else "west"
                    d.set(x, y, z, stair("cobblestone_stairs", f))
                else:
                    d.set(x, y, z, "stone_bricks" if y == T else rock(x, y, z))
    for x in range(22, 27):
        for z in range(26, 31):
            if x in (22, 26) or z in (26, 30):
                if (x in (22, 26)) and (z in (26, 30)):
                    d.set(x, T + 1, z, "cobblestone_wall")
    # casting arch (north) into the hearth chamber
    for x in range(23, 26):
        for y in range(2, 5):
            d.set(x, y, 24, AIR)
    put(d, [(23, 5, 24, stair("stone_brick_stairs", "west", "top")), (25, 5, 24, stair("stone_brick_stairs", "east", "top")),
            (24, 5, 24, AIR), (24, 6, 24, "chiseled_stone_bricks")])
    # hearth chamber x 21..27, z 25..31: crucible under the shaft, blast furnace no. 1, tuyeres and bellows
    for x in range(21, 28):
        for z in range(25, 32):
            d.set(x, 1, z, "stone_bricks")
    for x in range(23, 26):
        for z in range(27, 30):
            d.set(x, 2, z, "smooth_basalt" if (x, z) != (24, 28) else "lava_cauldron")
    d.item(24, 2, 26, "blast_furnace", "north")
    put(d, [(22, 3, 28, "iron_bars"), (26, 3, 28, "iron_bars"),
            (21, 2, 28, "piston[extended=false,facing=east]"), (21, 2, 27, "brown_wool"), (21, 2, 29, "brown_wool"),
            (27, 2, 28, "piston[extended=false,facing=west]"), (27, 2, 27, "brown_wool"), (27, 2, 29, "brown_wool"),
            (21, 2, 31, "coal_block"), (22, 2, 31, "coal_block"), (21, 3, 31, "black_carpet"),
            (27, 2, 31, "barrel[facing=up,open=false]"), (26, 2, 31, "iron_ore"), (27, 3, 31, "barrel[facing=north,open=false]"),
            (21, 2, 25, "grindstone[face=floor,facing=east]"), (27, 2, 25, "cauldron")])
    lamp(d, 22, 7, 26)
    lamp(d, 26, 7, 26)
    lamp(d, 22, 7, 30)
    lamp(d, 26, 7, 30)
    # ---- in the shed: hut, sow channel and pig bed, the anvil and quench, iron pigs stacked, tools
    d.hut(18, 2, 15, "east")
    for z in range(15, 24):
        d.set(24, 2, z, plate())
    for z in (17, 19, 21):
        for x in (22, 23, 25, 26):
            d.set(x, 2, z, plate())
    d.item(29, 2, 16, "anvil", "east")
    put(d, [(30, 2, 16, "water_cauldron[level=3]"), (30, 2, 15, "grindstone[face=floor,facing=west]"),
            (30, 3, 18, trap("spruce_trapdoor", "west", open_=True)), (30, 3, 19, trap("spruce_trapdoor", "west", open_=True)),
            (29, 2, 20, trap("iron_trapdoor", "north")), (30, 2, 20, trap("iron_trapdoor", "north")),
            (29, 2, 21, trap("iron_trapdoor", "north")), (30, 2, 21, trap("iron_trapdoor", "north")),
            (30, 2, 22, "chest[facing=west,type=single,waterlogged=false]"),
            (18, 2, 19, "coal_block"), (18, 2, 20, "coal_block"), (19, 2, 20, "coal_block"), (18, 3, 20, "black_carpet"),
            (18, 2, 22, "barrel[facing=up,open=false]"), (19, 2, 22, "barrel[facing=up,open=false]"),
            (18, 3, 22, "barrel[facing=east,open=false]"), (18, 2, 17, "crafting_table"), (19, 2, 14, "barrel[facing=up,open=false]")])
    for x, z in ((19, 17), (29, 18), (24, 14), (20, 21), (28, 22), (22, 18), (26, 18), (24, 21)):
        lamp(d, x, 5, z)
    if L >= 2:
        # second tap on the west face of the stack: blast furnace no. 2 with its own pig bed outside
        d.item(20, 2, 28, "blast_furnace", "west")
        put(d, [(20, 3, 28, stair("stone_brick_stairs", "west", "top")), (21, 2, 28, "magma_block")])
        for x in (16, 17, 18, 19):
            d.set(x, 1, 28, "sand")
            d.set(x, 2, 28, plate())
        for x in (17, 18):
            for z in (27, 29):
                d.set(x, 1, z, "sand")
                d.set(x, 2, z, plate())


def ca_east_tap(d, L):
    """L4 third tap on the east face of the stack: blast furnace no. 4, pig bed, cooling yard under a lean-to."""
    d.item(28, 2, 28, "blast_furnace", "east")
    put(d, [(28, 3, 28, stair("stone_brick_stairs", "east", "top")), (27, 2, 28, "magma_block")])
    for x in (29, 30, 31, 32):
        d.set(x, 1, 28, "sand")
        d.set(x, 2, 28, plate())
    for x in (30, 31):
        for z in (27, 29):
            d.set(x, 1, z, "sand")
            d.set(x, 2, z, plate())
    # lean-to roof on posts over the east casting bed
    for x, z in ((33, 25), (33, 31)):
        for y in range(2, 7):
            d.set(x, y, z, logb("spruce_log"))
    for z in range(24, 33):
        d.set(33, 7, z, logb("spruce_log", "z"))
        for x in range(29, 35):
            d.set(x, 8 - (1 if x >= 33 else 0) if False else (8 if x < 32 else 7), z, stair("spruce_stairs", "west")) if False else None
    for z in range(24, 33):
        for x, y in ((29, 9), (30, 9), (31, 8), (32, 8), (33, 8), (34, 7)):
            d.set(x, y, z, stair("spruce_stairs", "west"))
    put(d, [(32, 2, 25, "barrel[facing=up,open=false]"), (32, 2, 31, "water_cauldron[level=3]"),
            (29, 2, 31, trap("iron_trapdoor", "north")), (30, 2, 31, trap("iron_trapdoor", "north")),
            (29, 2, 25, "anvil[facing=north]"), (31, 2, 25, "grindstone[face=floor,facing=north]")])
    lamp(d, 31, 6, 28)


def ca_yard(d, L):
    for x in range(14, 35):
        for z in range(0, 13):
            d.set(x, 1, z, "coarse_dirt" if (x * 3 + z) % 5 else "gravel")
    for z in range(0, 13):
        for x in (23, 25):
            d.set(x, 1, z, "gravel")
    if L >= 2:
        for x in range(15, 20):                            # slag tip beside the smelter
            for z in range(33, 36):
                d.set(x, 2, z, "blackstone" if L >= 4 else "basalt[axis=y]")
        d.set(17, 3, 34, "basalt[axis=y]")


def ca_tier(d, x1, z1, x2, z2, yf, wt, roof_y):
    """One tier of the stamp mill: plank floor at yf, log walls from yf up to wt, gable roof (ridge along x)."""
    ca_logwall(d, x1, z1, x2, z2, yf, wt)
    for x in range(x1 + 1, x2):
        for z in range(z1 + 1, z2):
            d.set(x, yf, z, "spruce_planks")
            for y in range(yf + 1, wt + 6):
                d.set(x, y, z, AIR)
    return d.gable(x1, z1, x2, z2, roof_y, "x", "spruce_stairs", "spruce_slab", "spruce_planks", overhang=1)


def ca_mill(d, L):
    """The stamp mill climbing the hill on the west: tier 1 concentrators (L2), tier 2 stamp battery (L2),
    tier 3 crushers (L3), tier 4 ore bin under the headframe (L4)."""
    X1, X2 = 2, 14
    # ---- tier 1 (z 18..26, floor y2): concentrating tables, settling tanks
    for x in range(X1, X2 + 1):
        for z in range(18, 27):
            d.set(x, 1, z, "spruce_planks")
    ca_tier(d, X1, 18, X2, 26, 1, 7, 8)
    d.double_door(7, 2, 18, "x", "north", "spruce")
    for x in (4, 11):
        d.window(x, 4, 18, x + 1, 5, 18)
    for z in (21, 24):
        d.window(X1, 4, z, X1, 5, z)
    # tier 2 hill and building (z 26..34, floor y6)
    ca_hill(d, X1, 27, X2, 34, 5)
    ca_tier(d, X1, 26, X2, 34, 6, 11, 12)
    for x in range(X1 + 1, X2):                           # shared wall between tier 1 and tier 2
        for y in range(2, 6):
            d.set(x, y, 26, logb("spruce_log", "x"))
    # stair from tier 1 up to tier 2 along the east wall
    stair_run(d, [(13, 2, 21), (13, 3, 22), (13, 4, 23), (13, 5, 24), (13, 6, 25)], "south", "spruce_stairs",
              fill="spruce_planks")
    d.set(13, 7, 26, AIR), d.set(13, 8, 26, AIR)
    d.set(13, 6, 26, "spruce_planks")
    # tier 1 furnishing: three concentrating tables with their launders, settling tanks, concentrate barrels
    for x0 in (4, 7, 10):
        put(d, [(x0, 2, 21, slab("smooth_stone_slab", "top")), (x0 + 1, 2, 21, slab("smooth_stone_slab", "top")),
                (x0, 3, 21, "light_blue_carpet"), (x0 + 1, 3, 21, "light_blue_carpet"),
                (x0, 2, 20, trap("spruce_trapdoor", "south", "top"))])
    put(d, [(3, 2, 25, "water_cauldron[level=3]"), (4, 2, 25, "water_cauldron[level=3]"), (5, 2, 25, "cauldron"),
            (3, 2, 19, "barrel[facing=up,open=false]"), (3, 3, 19, "barrel[facing=north,open=false]"),
            (3, 2, 22, "white_wool"), (3, 2, 23, "white_wool"), (3, 3, 22, "white_carpet"),
            (8, 2, 25, "spruce_fence"), (8, 3, 25, plate()), (9, 2, 25, "lectern[facing=north,has_book=true,powered=false]"),
            (11, 2, 25, "chest[facing=north,type=single,waterlogged=false]"), (12, 2, 19, "composter[level=2]")])
    for x, z in ((5, 23), (10, 23), (7, 19)):
        lamp(d, x, 6, z)
    # tier 2 furnishing: the five-stamp battery (mortar, stems, cam shaft), feeder, amalgam plates, belt pulley
    for x in range(4, 13):
        d.set(x, 7, 31, "polished_andesite")
        d.set(x, 7, 32, "polished_andesite")
    for x in (5, 7, 9, 11):
        for y in (8, 9, 10):
            d.set(x, y, 31, "iron_bars" if y < 10 else "polished_andesite")
    for x in range(3, 14):
        d.set(x, 11, 31, logb("stripped_spruce_log", "x"))
    for x in (4, 6, 8, 10, 12):
        d.set(x, 8, 32, "hopper[enabled=true,facing=down]")
    put(d, [(4, 7, 29, slab("smooth_stone_slab", "top")), (5, 7, 29, slab("smooth_stone_slab", "top")),
            (6, 7, 29, slab("smooth_stone_slab", "top")), (10, 7, 29, slab("smooth_stone_slab", "top")),
            (11, 7, 29, slab("smooth_stone_slab", "top")), (12, 7, 29, slab("smooth_stone_slab", "top")),
            (13, 10, 31, "stripped_spruce_wood[axis=x]"),
            (12, 7, 28, "iron_ore"), (13, 7, 28, "iron_ore"), (13, 8, 28, "gravel"), (12, 7, 33, "barrel[facing=up,open=false]"),
            (12, 8, 33, "barrel[facing=west,open=false]"), (8, 7, 27, "spruce_fence"), (8, 8, 27, "lantern[hanging=false,waterlogged=false]")])
    for x, z in ((4, 28), (11, 28), (8, 30)):
        lamp(d, x, 10, z)
    if L == 2:
        # under the back eaves of tier 2 (built over by tier 3 later): woodpile, water butt, barrels
        put(d, [(1, 2, 31, "barrel[facing=up,open=false]"), (1, 2, 33, "composter[level=3]"), (1, 3, 31, "barrel[facing=up,open=false]"),
                (5, 2, 35, "barrel[facing=up,open=false]"), (9, 2, 35, "water_cauldron[level=3]"),
                (12, 2, 35, "hay_block[axis=y]"), (7, 2, 35, "chest[facing=north,type=single,waterlogged=false]")])
    for x in (4, 11):
        d.window(x, 8, 26, x + 1, 9, 26)
    for z in (28, 32):
        d.window(X1, 8, z, X1, 9, z)
        d.window(X2, 8, z, X2, 9, z)


def ca_main(rel, L):
    d = Design("Cascadia", rel, CA_SIZE, gy=1, paving="grass_block[snowy=false]")
    ca_yard(d, L)
    ca_smelter(d, L)
    if L >= 2:
        ca_mill(d, L)
    if L >= 3:
        ca_mill_upper(d, L)
        ca_trestle(d, L)
        ca_assay(d, L)
    if L >= 4:
        ca_east_tap(d, L)
    if L >= 5:
        ca_camp(d, L)
        ca_hillside(d, L)
        ca_storefronts(d, L)
    place_wings(d, CA_WX, CA_WZ, CA_WSIZE, CA_WHUT)
    connect_walls(d)
    return d


NT_AT = dict(stacks=2, ironrow=3, coalrow=4, tower=3, galleries=3, rolling=4, gantry=5, battery=4, stoves=5,
             hq=5, power=5, monitor=5)


def nt_main(rel, L):
    d = Design("Neoterra", rel, NT_SIZE, gy=1, paving="smooth_stone")
    for x in range(26, 35):                                # entrance plaza
        for z in range(0, 10):
            d.set(x, 1, z, "polished_diorite" if (x + z) % 2 else "polished_andesite")
    at = NT_AT
    nt_hall(d, L)
    if L >= at["stacks"]:
        nt_stacks(d, L)
    if L >= at["ironrow"]:
        nt_stockyard(d, L)
    if L >= at["tower"]:
        nt_control_tower(d, L)
    if L >= at["galleries"]:
        nt_galleries(d, L)
    if L >= at["rolling"]:
        nt_rolling_mill(d, L)
    if L >= at["gantry"]:
        nt_gantry(d, L)
    if L >= at["stoves"]:
        nt_stoves(d, L)
    if L >= at["hq"]:
        nt_hq(d, L)
    if L >= at["power"]:
        nt_power(d, L)
    if L >= at["monitor"]:
        nt_monitor(d, L)
        nt_plaza(d, L)
    place_wings(d, NT_WX, NT_WZ, NT_WSIZE, NT_WHUT)
    connect_walls(d)
    return d


# =============================================================================================================
@design("greatforge")
def greatforge(pack, rel, L):
    return {"Hearthwood": hw_main, "Cascadia": ca_main, "Neoterra": nt_main}[pack](rel, L)


@design("greatforgewing")
def greatforgewing(pack, rel, L):
    return {"Hearthwood": hww, "Cascadia": caw, "Neoterra": ntw}[pack](rel, L)


def ca_mill_upper(d, L):
    """Tier 3 (L3): the crusher floor; tier 4 (L4): the ore bin under the headframe on the hilltop."""
    X1, X2 = 2, 14
    ca_hill(d, X1, 35, X2, 42, 9)
    ca_tier(d, X1, 34, X2, 42, 10, 15, 16)
    for x in range(X1 + 1, X2):
        for y in range(6, 10):
            d.set(x, y, 34, logb("spruce_log", "x"))
    stair_run(d, [(3, 7, 30), (3, 8, 31), (3, 9, 32), (3, 10, 33)], "south", "spruce_stairs", fill=None)
    for z, y in ((30, 7), (31, 8), (32, 9), (33, 10)):
        for yy in range(7, y):
            d.set(3, yy, z, "spruce_planks")
    d.set(3, 11, 34, AIR), d.set(3, 12, 34, AIR), d.set(3, 10, 34, "spruce_planks")
    for z in (37, 40):
        d.window(X1, 12, z, X1, 13, z)
    d.window(7, 12, 34, 9, 13, 34)
    # crusher floor: jaw crusher on its plinth, grizzly over the chute, picking table, ore feeders to the stamps
    put(d, [(6, 11, 39, "polished_andesite"), (7, 11, 39, "polished_andesite"), (8, 11, 39, "polished_andesite"),
            (6, 12, 39, "grindstone[face=floor,facing=north]"), (8, 12, 39, "grindstone[face=floor,facing=north]"),
            (7, 12, 39, "stonecutter[facing=north]"), (7, 13, 39, logb("stripped_spruce_log", "x")),
            (6, 11, 41, "iron_bars"), (7, 11, 41, "iron_bars"), (8, 11, 41, "iron_bars"),
            (10, 11, 37, slab("spruce_slab", "top")), (11, 11, 37, slab("spruce_slab", "top")), (12, 11, 37, slab("spruce_slab", "top")),
            (10, 12, 37, "iron_ore"), (12, 12, 37, "gravel"), (11, 12, 37, "brown_carpet"),
            (10, 11, 36, stair("spruce_stairs", "north")), (12, 11, 36, stair("spruce_stairs", "north")),
            (5, 11, 36, "hopper[enabled=true,facing=down]"), (6, 11, 36, "hopper[enabled=true,facing=down]"),
            (13, 11, 41, "barrel[facing=up,open=false]"), (13, 11, 40, "barrel[facing=up,open=false]"),
            (13, 12, 41, "barrel[facing=west,open=false]"), (3, 11, 41, "chest[facing=east,type=single,waterlogged=false]"),
            (13, 11, 35, "water_cauldron[level=3]")])
    for x, z in ((5, 38), (11, 39), (8, 36)):
        lamp(d, x, 14, z)
    # door out to the ore trestle (east wall)
    d.set(X2, 11, 38, AIR), d.set(X2, 12, 38, AIR)
    if L >= 4:
        ca_hill(d, X1, 43, X2, 56, 13)
        ca_tier(d, X1, 42, X2, 50, 14, 19, 20)
        for x in range(X1 + 1, X2):
            for y in range(10, 14):
                d.set(x, y, 42, logb("spruce_log", "x"))
        stair_run(d, [(3, 11, 37), (3, 12, 38), (3, 13, 39), (3, 14, 40)], "south", "spruce_stairs")
        for z, y in ((37, 11), (38, 12), (39, 13), (40, 14)):
            for yy in range(11, y):
                d.set(3, yy, z, "spruce_planks")
        d.set(3, 14, 41, "spruce_planks"), d.set(3, 14, 42, "spruce_planks")
        d.set(3, 15, 42, AIR), d.set(3, 16, 42, AIR)
        d.set(3, 11, 41, AIR)
        d.set(4, 11, 41, "chest[facing=east,type=single,waterlogged=false]")
        # the ore bin: a sloping timber bin full of ore, the skip chute from the headframe, the bin gate
        for x in range(4, 13):
            for z in range(46, 50):
                h = 14 + (z - 45)
                for y in range(15, h + 1):
                    d.set(x, y, z, "iron_ore" if (x + y + z) % 3 else "gravel")
                d.set(x, h + 1, z, "brown_carpet" if (x + z) % 2 else "gravel")
        for x in range(4, 13):
            d.set(x, 15, 45, trap("spruce_trapdoor", "north", "top"))
            d.set(x, 16, 45, "spruce_fence")
        put(d, [(8, 15, 44, "hopper[enabled=true,facing=down]"), (4, 15, 43, "barrel[facing=up,open=false]"),
                (5, 15, 43, "lectern[facing=north,has_book=true,powered=false]"), (11, 15, 43, "chest[facing=north,type=single,waterlogged=false]"),
                (3, 15, 44, "lever[face=floor,facing=east,powered=false]")])
        for x in (5, 9, 12):
            lamp(d, x, 18, 44)
        for x in (5, 10):
            d.window(x, 16, 42, x + 1, 17, 42)
        # the headframe on the hilltop (x 5..11, z 51..55), sheave wheel, backstays, the hoist house behind
        for x, z in ((5, 51), (11, 51), (5, 55), (11, 55)):
            for y in range(14, 27):
                d.set(x, y, z, logb("spruce_log"))
        for y in (18, 22, 26):
            for x in range(5, 12):
                d.set(x, y, 51, logb("stripped_spruce_log", "x"))
                d.set(x, y, 55, logb("stripped_spruce_log", "x"))
            for z in range(51, 56):
                d.set(5, y, z, logb("stripped_spruce_log", "z"))
                d.set(11, y, z, logb("stripped_spruce_log", "z"))
        for x in range(5, 12):
            for z in range(51, 56):
                d.set(x, 27, z, "spruce_planks" if not (6 <= x <= 10 and 52 <= z <= 54) else d.get(x, 27, z))
        wheel = [(8, 30), (7, 30), (9, 30), (6, 29), (10, 29), (6, 28), (10, 28), (7, 27), (9, 27), (8, 27)]
        for x, y in wheel:
            d.set(x, y + 1, 53, "dark_oak_planks" if (x + y) % 2 else "spruce_planks")
        d.set(8, 29, 53, logb("spruce_log", "z"))
        for y in range(15, 28):
            d.set(8, y, 53, "chain[axis=y,waterlogged=false]")
        for x in range(6, 11):                             # shaft collar
            for z in range(52, 55):
                if (x, z) != (8, 53):
                    d.set(x, 14, z, "spruce_planks" if x in (6, 10) or z in (52, 54) else "spruce_planks")
        d.set(8, 14, 53, AIR), d.set(8, 13, 53, AIR), d.set(8, 12, 53, AIR)
        put(d, [(7, 15, 52, "spruce_fence"), (9, 15, 52, "spruce_fence"), (7, 15, 54, "spruce_fence"), (9, 15, 54, "spruce_fence"),
                (6, 15, 53, "barrel[facing=up,open=false]")])
        d.set(13, 15, 50, AIR), d.set(13, 16, 50, AIR)    # back door of the bin house onto the hilltop
        for x in range(5, 12):                             # skip chute down to the ore bin
            pass
        for z, y in ((50, 21), (49, 21)):
            d.set(8, y, z, slab("spruce_slab"))
        ca_logwall(d, 3, 56, 13, 57, 14, 17) if False else None
        lamp(d, 8, 25, 53) if False else None


def ca_trestle(d, L):
    """L3 ore trestle: plank deck with rails on log bents from the crusher floor to the furnace top."""
    Y = 13
    # landing and steps from the tier-3 door up to the deck
    put(d, [(15, 10, 38, "spruce_planks"), (15, 9, 38, logb("spruce_log")),
            (16, 11, 38, stair("spruce_stairs", "east")), (17, 12, 38, stair("spruce_stairs", "east")),
            (18, 13, 38, stair("spruce_stairs", "east"))])
    for y in range(2, 9):
        d.set(15, y, 38, logb("spruce_log"))
    for x in (16, 17, 18):
        for y in range(2, 11 + (x - 16)):
            d.set(x, y, 38, logb("spruce_log") if x == 16 else "spruce_planks") if x in (16, 18) else None
    # east leg along z 37..39 (x 19..25), north leg along x 23..25 (z 31..36)
    cells = [(x, z) for x in range(19, 26) for z in (37, 38, 39)] + [(x, z) for x in (23, 24, 25) for z in range(31, 37)]
    for x, z in cells:
        d.set(x, Y, z, "spruce_planks")
    for x in range(19, 26):
        d.set(x, Y + 1, 39, "spruce_fence")
        d.set(x, Y + 1, 37, "spruce_fence") if x < 23 else None
    for z in range(32, 40):
        d.set(26, Y + 1, z, "spruce_fence")
        d.set(22, Y + 1, z, "spruce_fence") if z < 37 else None
    for x in range(19, 24):
        d.set(x, Y + 1, 38, "rail[shape=east_west,waterlogged=false]")
    d.set(24, Y + 1, 38, "rail[shape=north_west,waterlogged=false]")
    for z in range(31, 38):
        d.set(24, Y + 1, z, "rail[shape=north_south,waterlogged=false]")
    d.set(24, Y + 1, 30, AIR)                             # charging door into the shaft
    # log bents: two posts and a cap beam with knee braces
    for x in (20, 24):
        for z in (37, 39):
            for y in range(2, Y):
                d.set(x, y, z, logb("spruce_log"))
        d.set(x, 8, 38, logb("stripped_spruce_log", "z"))
    for z in (34,):
        for x in (23, 25):
            for y in range(9, Y):
                d.set(x, y, z, logb("spruce_log"))
            for y in range(2, 9):
                d.set(x, y, z, logb("spruce_log"))
        d.set(24, 8, z, logb("stripped_spruce_log", "x"))
    for x, z in ((20, 37), (24, 37), (20, 39), (24, 39)):
        d.set(x, Y - 1, z, logb("stripped_spruce_log"))
    put(d, [(19, Y + 1, 37, "lantern[hanging=false,waterlogged=false]"), (25, Y + 1, 32, "lantern[hanging=false,waterlogged=false]")])
    # under the trestle: ore-car repair stand, barrels of grease, water for the mules, torches on the bents
    put(d, [(21, 2, 38, "barrel[facing=up,open=false]"), (22, 2, 38, "barrel[facing=up,open=false]"),
            (22, 3, 38, "barrel[facing=north,open=false]"), (25, 2, 35, "water_cauldron[level=3]"),
            (24, 2, 36, "hay_block[axis=y]"), (23, 2, 33, "composter[level=4]"), (19, 2, 38, "chest[facing=east,type=single,waterlogged=false]"),
            (21, 4, 37, "wall_torch[facing=east]"), (21, 4, 39, "wall_torch[facing=east]"), (24, 4, 35, "wall_torch[facing=south]"),
            (22, 2, 34, "spruce_fence"), (22, 3, 34, "lantern[hanging=false,waterlogged=false]")])


def ca_assay(d, L):
    """L3 assay office: rubble ground floor, board-and-batten upper storey, tall false front with the name."""
    X1, X2, Z1, Z2 = 35, 45, 17, 26
    rect(d, X1, Z1, X2, Z2, 1, "spruce_planks")
    for x in range(X1, X2 + 1):
        for z in range(Z1, Z2 + 1):
            if not (x in (X1, X2) or z in (Z1, Z2)):
                d.set(x, 6, z, "spruce_planks")
                continue
            for y in range(2, 6):
                d.set(x, y, z, rock(x, y, z))
            d.set(x, 6, z, logb("spruce_log", "x" if z in (Z1, Z2) else "z"))
            for y in range(7, 10):
                d.set(x, y, z, logb("stripped_spruce_log") if (x + z) % 2 == 0 or (x in (X1, X2) and z in (Z1, Z2)) else "spruce_planks")
    d.gable(X1, Z1, X2, Z2, 10, "z", "spruce_stairs", "spruce_slab", "spruce_planks", overhang=1)
    # false front
    for x in range(X1, X2 + 1):
        for y in range(10, 17):
            d.set(x, y, Z1, "spruce_planks" if y < 16 else stair("spruce_stairs", "south", "top"))
    for x in (X1, X2):
        d.set(x, 17, Z1, "spruce_planks")
    d.set(40, 17, Z1, "spruce_planks"), d.set(40, 18, Z1, "spruce_slab[type=bottom,waterlogged=false]")
    d.sign(40, 13, Z1 - 1, "north", ["ASSAY", "OFFICE", "Gold Silver", "Iron Copper"], "spruce")
    d.sign(39, 13, Z1 - 1, "north", ["", "", "", ""], "spruce") if False else None
    # boardwalk porch with a lean-to roof
    for x in range(X1 - 1, X2 + 2):
        for z in (15, 16):
            d.set(x, 1, z, "spruce_planks")
        d.set(x, 6, 15, stair("spruce_stairs", "south"))
        d.set(x, 6, 16, stair("spruce_stairs", "south")) if False else None
    for x in (X1, 40, X2):
        for y in range(2, 6):
            d.set(x, y, 15, logb("stripped_spruce_log"))
    d.door(40, 2, Z1, "north", "spruce")
    for x in (37, 43):
        d.window(x, 3, Z1, x + 1, 4, Z1)
        d.window(x, 7, Z1, x + 1, 8, Z1)
    for z in (20, 23):
        d.window(X1, 3, z, X1, 4, z)
        d.window(X2, 7, z, X2, 8, z)
        d.window(X1, 7, z, X1, 8, z)
    # ---- ground floor: the assay laboratory
    d.item(44, 2, 25, "blast_furnace", "west")
    put(d, [(44, 3, 25, "bricks"), (44, 4, 25, "bricks"), (43, 2, 25, slab("smooth_stone_slab", "top")),
            (43, 3, 25, "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]"),
            (44, 2, 23, "cauldron"), (44, 2, 22, "lava_cauldron"),
            (36, 2, 18, "glass"), (36, 3, 18, "spruce_fence"), (36, 4, 18, plate()) if False else (36, 2, 18, slab("spruce_slab", "top")),
            (36, 3, 18, "glass_pane"), (37, 2, 18, slab("spruce_slab", "top")), (37, 3, 18, "heavy_weighted_pressure_plate[power=0]"),
            (36, 2, 21, slab("spruce_slab", "top")), (36, 2, 22, slab("spruce_slab", "top")), (36, 2, 23, slab("spruce_slab", "top")),
            (36, 3, 21, "brewing_stand[has_bottle_0=false,has_bottle_1=true,has_bottle_2=false]"), (36, 3, 22, "flower_pot"),
            (36, 3, 23, "brewing_stand[has_bottle_0=true,has_bottle_1=true,has_bottle_2=false]"),
            (37, 2, 22, stair("spruce_stairs", "east")),
            (40, 2, 25, "barrel[facing=up,open=false]"), (39, 2, 25, "barrel[facing=up,open=false]"),
            (40, 3, 25, "iron_ore"), (39, 3, 25, "gold_ore") if False else (39, 3, 25, "raw_copper_block" if False else "copper_ore"),
            (41, 2, 21, "spruce_fence"), (41, 3, 21, plate("spruce")), (42, 2, 21, stair("spruce_stairs", "east")),
            (44, 2, 18, "lectern[facing=west,has_book=true,powered=false]"), (44, 2, 19, "chest[facing=west,type=single,waterlogged=false]")])
    for y in range(2, 7):
        d.set(36, y, 25, "ladder[facing=east,waterlogged=false]")
    for x, z in ((38, 20), (42, 23), (40, 19)):
        lamp(d, x, 5, z)
    # ---- upper floor: the superintendent's office and records room
    put(d, [(40, 7, 18, slab("dark_oak_slab", "top")), (41, 7, 18, slab("dark_oak_slab", "top")), (40, 8, 18, cand(3)),
            (41, 8, 18, "potted_fern"), (40, 7, 19, stair("dark_oak_stairs", "south")),
            (44, 7, 18, "chest[facing=west,type=single,waterlogged=false]"), (44, 8, 18, "iron_bars"),
            (36, 7, 18, "bookshelf"), (36, 8, 18, "bookshelf"), (37, 7, 18, "bookshelf"), (37, 8, 18, "bookshelf"),
            (38, 7, 22, "cartography_table"), (39, 7, 22, stair("spruce_stairs", "west")),
            (43, 7, 22, stair("spruce_stairs", "west")), (43, 7, 23, stair("spruce_stairs", "west")),
            (42, 7, 22, "green_carpet"), (41, 7, 22, "green_carpet"), (42, 7, 23, "green_carpet"), (41, 7, 23, "green_carpet"),
            (44, 7, 25, "barrel[facing=up,open=false]"), (43, 7, 25, "barrel[facing=up,open=false]"),
            (40, 7, 25, "white_bed[facing=east,occupied=false,part=foot]"), (41, 7, 25, "white_bed[facing=east,occupied=false,part=head]"),
            (42, 7, 25, slab("spruce_slab", "top")), (42, 8, 25, cand(1))])
    lamp(d, 40, 9, 21)
    lamp(d, 42, 9, 24)
    if L >= 5:
        # second muffle furnace (blast furnace no. 5) beside the first
        d.item(44, 2, 21, "blast_furnace", "west")
        d.set(44, 3, 21, "bricks")
        d.set(44, 4, 21, "bricks")


def ca_camp(d, L):
    """L5 the camp: bunk & cook house, boiler house with its iron smokestack, water tower and the flume."""
    # ---- bunk & cook house x 34..46, z 29..40: log, two storeys, porch on the north
    X1, X2, Z1, Z2 = 34, 46, 29, 40
    rect(d, X1, Z1, X2, Z2, 1, "spruce_planks")
    ca_logwall(d, X1, Z1, X2, Z2, 2, 10, base=True)
    for x in range(X1 + 1, X2):
        for z in range(Z1 + 1, Z2):
            d.set(x, 6, z, "spruce_planks")
    d.gable(X1, Z1, X2, Z2, 11, "z", "spruce_stairs", "spruce_slab", "spruce_planks", overhang=1)
    for z in range(Z1 + 1, Z2):                            # partition: cook house (west) / bunk room (east) below
        for y in range(2, 6):
            d.set(40, y, z, logb("stripped_spruce_log"))
    d.set(40, 2, 35, AIR), d.set(40, 3, 35, AIR)
    d.door(37, 2, Z1, "north", "spruce")
    d.door(43, 2, Z1, "north", "spruce")
    for x in (36, 39, 42, 45):
        d.window(x, 3, Z2, x, 4, Z2)
        d.window(x, 7, Z1, x, 8, Z1)
        d.window(x, 7, Z2, x, 8, Z2)
    for z in (32, 37):
        d.window(X1, 3, z, X1, 4, z)
        d.window(X2, 3, z, X2, 4, z)
    for x in range(X1, X2 + 1):                           # porch
        d.set(x, 1, 28, "spruce_planks")
        d.set(x, 5, 28, stair("spruce_stairs", "south"))
    for x in (X1, 40, X2):
        for y in range(2, 5):
            d.set(x, y, 28, logb("stripped_spruce_log"))
    for y in range(2, 13):                                 # stone chimney of the cook stove
        d.set(X1 - 1, y, 38, rock(X1 - 1, y, 38))
    d.sign(40, 5, Z1 - 1, "north", ["BUNK HOUSE", "& COOK HOUSE", "", ""], "spruce") if False else None
    d.sign(37, 4, 27, "north", ["COOK HOUSE", "", "", ""], "spruce") if False else None
    # cook house: range, sink, larder, two long tables with benches
    put(d, [(35, 2, 38, "smoker[facing=east,lit=true]"), (35, 2, 37, "furnace[facing=east,lit=false]"),
            (35, 2, 39, slab("spruce_slab", "top")), (35, 3, 39, "barrel[facing=up,open=false]"),
            (35, 2, 36, "water_cauldron[level=3]"), (35, 2, 35, slab("spruce_slab", "top")), (35, 3, 35, pot("east")),
            (39, 2, 39, "barrel[facing=up,open=false]"), (38, 2, 39, "barrel[facing=up,open=false]"),
            (39, 3, 39, "barrel[facing=north,open=false]"), (35, 2, 30, "chest[facing=east,type=single,waterlogged=false]")])
    for z in (31, 32, 33):
        put(d, [(37, 2, z, "spruce_fence"), (37, 3, z, plate("spruce")),
                (36, 2, z, stair("spruce_stairs", "west")), (38, 2, z, stair("spruce_stairs", "east"))])
    lamp(d, 37, 5, 32)
    lamp(d, 37, 5, 36)
    # bunk room: three bunks along the back wall, foot lockers, stove, wash stand, ladder to the loft
    for x in (41, 43, 45):
        bed(d, x, 2, 39, "south", "brown")
        d.set(x, 2, 37, "chest[facing=north,type=single,waterlogged=false]")
    put(d, [(45, 2, 30, "furnace[facing=west,lit=true]"), (44, 2, 30, "water_cauldron[level=3]"),
            (42, 2, 33, "spruce_fence"), (42, 3, 33, cand(2)), (41, 2, 33, stair("spruce_stairs", "west")),
            (43, 2, 33, stair("spruce_stairs", "east")), (42, 2, 35, "brown_carpet"), (43, 2, 35, "brown_carpet")])
    for y in range(2, 7):
        d.set(41, y, 30, "ladder[facing=south,waterlogged=false]")
    lamp(d, 43, 5, 32)
    lamp(d, 43, 5, 37)
    # loft: more bunks under the roof, a card table, lockers
    for x, z in ((36, 39), (38, 39), (44, 39)):
        bed(d, x, 7, z, "south", "green")
    for x, z in ((36, 30), (39, 30)):
        bed(d, x, 7, z, "north", "green")
    put(d, [(42, 7, 34, "spruce_fence"), (42, 8, 34, plate("spruce")), (41, 7, 34, stair("spruce_stairs", "west")),
            (43, 7, 34, stair("spruce_stairs", "east")), (42, 7, 33, stair("spruce_stairs", "north")),
            (45, 7, 36, "chest[facing=west,type=single,waterlogged=false]"), (45, 7, 35, "barrel[facing=up,open=false]"),
            (37, 7, 35, "red_carpet"), (38, 7, 35, "red_carpet"), (37, 7, 34, "red_carpet"), (38, 7, 34, "red_carpet")])
    lamp(d, 40, 10, 34)
    # ---- boiler house x 34..42, z 44..53 with the smokestack and the hoist-house belt line
    X1, X2, Z1, Z2 = 34, 42, 44, 53
    rect(d, X1, Z1, X2, Z2, 1, "cobblestone")
    for x in range(X1, X2 + 1):
        for z in range(Z1, Z2 + 1):
            if x in (X1, X2) or z in (Z1, Z2):
                for y in range(2, 8):
                    d.set(x, y, z, rock(x, y, z) if y <= 3 else ("spruce_planks" if (x + z) % 3 else logb("stripped_spruce_log")))
    d.gable(X1, Z1, X2, Z2, 8, "z", "spruce_stairs", "spruce_slab", "spruce_planks", overhang=1)
    d.double_door(37, 2, Z1, "x", "north", "spruce")
    for z in (47, 50):
        d.window(X1, 4, z, X1, 5, z)
        d.window(X2, 4, z, X2, 5, z)
    # two fire-tube boilers bricked in, fire doors, water feed, coal pile
    for x0 in (35, 39):
        for x in range(x0, x0 + 3):
            for z in range(47, 52):
                for y in (2, 3):
                    d.set(x, y, z, "bricks")
        d.set(x0 + 1, 3, 47, "iron_bars")
        d.set(x0 + 1, 2, 47, "furnace[facing=north,lit=true]")
        for z in range(48, 52):
            d.set(x0 + 1, 4, z, "polished_andesite")
    put(d, [(35, 2, 45, "coal_block"), (36, 2, 45, "coal_block"), (35, 3, 45, "black_carpet"),
            (41, 2, 45, "water_cauldron[level=3]"), (41, 2, 46, "barrel[facing=up,open=false]"),
            (38, 2, 52, "lever[face=floor,facing=north,powered=false]"), (38, 2, 49, "chain[axis=y,waterlogged=false]") if False else (38, 2, 50, "chest[facing=north,type=single,waterlogged=false]")])
    lamp(d, 38, 6, 46)
    lamp(d, 38, 6, 50)
    # the iron smokestack (x 43..45, z 50..52)
    for y in range(2, 37):
        for x in range(43, 46):
            for z in range(50, 53):
                if (x, z) == (44, 51):
                    continue
                d.set(x, y, z, rock(x, y, z) if y <= 6 else ("polished_deepslate" if y % 8 == 0 else "deepslate_tiles"))
    for x, z in ((43, 50), (45, 50), (43, 52), (45, 52)):
        d.set(x, 37, z, "deepslate_tile_wall")
    d.set(43, 2, 51, "cobblestone"), d.set(42, 3, 51, "iron_bars")
    # ---- water tower x 44..47, z 42..46 on log legs, flume on trestle west to the mill
    for x, z in ((44, 43), (47, 43), (44, 46), (47, 46)):
        for y in range(2, 14):
            d.set(x, y, z, logb("spruce_log"))
    for x in range(43, 49):
        for z in range(42, 48):
            if not d.bp.inside(x, 14, z):
                continue
            d.set(x, 14, z, "spruce_planks")
            if x in (43, 48) or z in (42, 47):
                for y in range(15, 19):
                    d.set(x, y, z, logb("stripped_spruce_log") if (x + z) % 2 else "spruce_planks")
            else:
                d.set(x, 15, z, WATER)
                d.set(x, 16, z, WATER)
                d.set(x, 17, z, WATER)
                d.set(x, 18, z, WATER)
    d.hip(43, 42, 48, 47, 19, "spruce_stairs", "spruce_slab", overhang=0)
    for x in range(43, 49):
        for z in range(42, 48):
            if d.get(x, 19, z) == AIR:
                d.set(x, 19, z, "spruce_planks")
    # flume: plank trough at y 16 along z 41 from the tower to the ore-bin tier
    for x in range(15, 43):
        d.set(x, 15, 41, "spruce_planks")
        d.set(x, 16, 41, WATER if x > 15 else "spruce_planks")
        d.set(x, 16, 40, "spruce_planks")
        d.set(x, 16, 42, "spruce_planks")
    d.set(43, 16, 41, "spruce_planks")
    for x in (18, 24, 30, 36):
        for y in range(2, 15):
            if d.get(x, y, 41) == AIR:
                d.set(x, y, 41, logb("spruce_log"))
    # tailings dump behind the smelter
    for x in range(16, 33):
        for z in range(44, 57):
            h = 2 + min(x - 15, 33 - x, z - 43, 57 - z) // 2
            for y in range(2, h + 1):
                if d.get(x, y, z) == AIR:
                    d.set(x, y, z, "gravel" if (x + z) % 4 else "coarse_dirt")


def ca_hillside(d, L):
    """L5 the hillside the mill is cut into: earth and rock slope falling east of the upper tiers, a mine adit with
    its ore-car track, the charging house on the furnace top and the aerial tramway tower."""
    for x in range(15, 34):
        for z in range(35, 58):
            h = int(13 - (x - 14) * 0.75 - max(0, 44 - z) * 1.2 + (0.5 if (x * 3 + z) % 4 == 0 else 0))
            for y in range(2, h + 1):
                if d.get(x, y, z) == AIR:
                    d.set(x, y, z, rock(x, y, z) if (x * 5 + y + z * 3) % 7 == 0 else
                          ("grass_block[snowy=false]" if y == h else "dirt"))
    for x, z, kind in ((17, 52, "spruce"), (20, 47, "spruce"), (24, 55, "spruce"), (28, 54, "birch")):
        y0 = 2
        while d.get(x, y0, z) != AIR:
            y0 += 1
        for k in range(4):
            d.set(x, y0 + k, z, logb(f"{kind}_log"))
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for yy in (y0 + 3, y0 + 4):
                    if d.bp.inside(x + dx, yy, z + dz) and d.air(x + dx, yy, z + dz):
                        d.set(x + dx, yy, z + dz, f"{kind}_leaves[distance=1,persistent=true,waterlogged=false]")
        d.set(x, y0 + 5, z, f"{kind}_leaves[distance=1,persistent=true,waterlogged=false]")
    # charging house on the furnace top: a timber hood around the throat on the 7x7 ledge
    for x, z in ((21, 25), (27, 25), (21, 31), (27, 31)):
        for y in range(13, 18):
            d.set(x, y, z, logb("spruce_log"))
    d.gable(21, 25, 27, 31, 18, "x", "spruce_stairs", "spruce_slab", "spruce_planks", overhang=1)
    for x in range(22, 27):
        for z in range(26, 31):
            if 22 <= x <= 26 and 26 <= z <= 30 and (x in (22, 26) or z in (26, 30)):
                for y in range(14, 26):
                    pass
    T = 27
    for y in range(18, T + 1):
        for x in range(22, 27):
            for z in range(26, 31):
                if x in (22, 26) or z in (26, 30):
                    d.set(x, y, z, "stone_bricks" if y == T else rock(x, y, z))
                else:
                    d.set(x, y, z, AIR)
    for x in range(21, 28):                               # plank charging floor on the ledge round the throat
        for z in range(25, 32):
            if x in (21, 27) or z in (25, 31):
                if "stairs" in d.get(x, 13, z):
                    d.set(x, 13, z, "spruce_planks")
    for z in (31,):
        d.set(22, 14, z, AIR), d.set(26, 14, z, AIR)
    put(d, [(22, 14, 31, "barrel[facing=up,open=false]"), (26, 14, 31, "barrel[facing=up,open=false]"),
            (26, 15, 31, "barrel[facing=north,open=false]"), (23, 14, 25, "iron_ore"), (25, 14, 25, "iron_ore"),
            (21, 14, 29, "coal_block"), (21, 15, 29, "black_carpet"), (27, 14, 28, "coal_block")])
    # aerial tramway: a log tower on the hilltop and cable down to a terminal above the smelter yard
    for y in range(14, 24):
        d.set(3, y, 55, logb("spruce_log"))
        d.set(3, y, 57, logb("spruce_log")) if d.bp.inside(3, y, 57) else None
    for z in range(54, 58):
        d.set(3, 24, z, logb("stripped_spruce_log", "z"))
    for x in range(4, 14):
        d.set(x, 23, 56, "chain[axis=x,waterlogged=false]")
    for x in (6, 10):
        d.set(x, 22, 56, "cauldron")


def ca_storefronts(d, L):
    """L5 two false-front buildings flanking the smelter yard: the company store and the post & telegraph."""
    for X1, X2, name in ((14, 20, ("COMPANY", "STORE")), (28, 34, ("POST &", "TELEGRAPH"))):
        Z1, Z2 = 2, 11
        rect(d, X1, Z1, X2, Z2, 1, "spruce_planks")
        for x in range(X1, X2 + 1):
            for z in range(Z1, Z2 + 1):
                if x in (X1, X2) or z in (Z1, Z2):
                    for y in range(2, 8):
                        d.set(x, y, z, rock(x, y, z) if y == 2 else (logb("stripped_spruce_log") if (x + z) % 2 == 0 or
                              (x in (X1, X2) and z in (Z1, Z2)) else "spruce_planks"))
        d.gable(X1, Z1, X2, Z2, 8, "z", "spruce_stairs", "spruce_slab", "spruce_planks", overhang=1)
        for x in range(X1, X2 + 1):                        # false front
            for y in range(8, 14):
                d.set(x, y, Z1, "spruce_planks" if y < 13 else stair("spruce_stairs", "south", "top"))
        d.set((X1 + X2) // 2, 14, Z1, "spruce_planks")
        d.sign((X1 + X2) // 2, 10, Z1 - 1, "north", ["", name[0], name[1], ""], "spruce")
        d.door((X1 + X2) // 2, 2, Z1, "north", "spruce")
        d.window(X1 + 1, 3, Z1, X1 + 2, 5, Z1)
        d.window(X2 - 2, 3, Z1, X2 - 1, 5, Z1)
        for z in (5, 8):
            d.window(X1, 4, z, X1, 5, z)
            d.window(X2, 4, z, X2, 5, z)
        for x in range(X1, X2 + 1):                        # boardwalk and awning
            d.set(x, 1, 1, "spruce_planks")
            d.set(x, 1, 0, "spruce_planks")
            d.set(x, 6, 1, stair("spruce_stairs", "south"))
        for x in (X1, X2):
            for y in range(2, 6):
                d.set(x, y, 1, logb("stripped_spruce_log"))
    # company store: counter across the room, shelves of goods behind, sacks and barrels, scale, stove
    for x in range(15, 20):
        if x != 17:
            d.set(x, 2, 6, slab("spruce_slab", "top"))
    put(d, [(16, 3, 6, "heavy_weighted_pressure_plate[power=0]"), (18, 3, 6, cand(2)), (15, 3, 6, pot("north")),
            (15, 2, 10, "barrel[facing=up,open=false]"), (16, 2, 10, "barrel[facing=up,open=false]"),
            (15, 3, 10, "barrel[facing=east,open=false]"), (19, 2, 10, shelf("north")), (18, 2, 10, shelf("north")),
            (19, 3, 10, shelf("north")), (18, 3, 10, shelf("north")), (19, 2, 8, "white_wool"), (19, 2, 7, "white_wool"),
            (19, 3, 8, "white_carpet"), (15, 2, 3, "barrel[facing=up,open=false]"), (19, 2, 3, "furnace[facing=west,lit=true]"),
            (16, 2, 4, stair("spruce_stairs", "west")), (17, 2, 8, "chest[facing=north,type=single,waterlogged=false]")])
    lamp(d, 17, 6, 4)
    lamp(d, 17, 6, 8)
    # post & telegraph: counter with mail pigeonholes, telegraph desk, safe, waiting bench
    for x in range(29, 34):
        if x != 31:
            d.set(x, 2, 6, slab("spruce_slab", "top"))
    put(d, [(29, 2, 10, shelf("north")), (30, 2, 10, shelf("north")), (29, 3, 10, shelf("north")), (30, 3, 10, shelf("north")),
            (33, 2, 9, slab("dark_oak_slab", "top")), (33, 3, 9, "note_block[instrument=harp,note=0,powered=false]"),
            (32, 2, 9, stair("dark_oak_stairs", "east")), (33, 2, 10, "chest[facing=west,type=single,waterlogged=false]"),
            (33, 2, 7, "lectern[facing=north,has_book=true,powered=false]"),
            (29, 2, 3, stair("spruce_stairs", "west")), (29, 2, 4, stair("spruce_stairs", "west")),
            (33, 2, 3, "potted_fern"), (30, 3, 6, "lantern[hanging=false,waterlogged=false]"), (32, 3, 6, "paper" if False else cand(1)),
            (31, 2, 8, "brown_carpet"), (31, 2, 9, "brown_carpet")])
    lamp(d, 31, 6, 4)
    lamp(d, 31, 6, 9)


# =============================================================================================================
#                                     NEOTERRA – the Neoterra Steelworks
# =============================================================================================================
# L1 the melt shop (tall ribbed steel hall with a glazed front, converter no. 1, overhead crane) between two
# cylindrical blast-furnace towers (the wings). L2 the red-and-white twin stacks and the ore stockyard, L3 the
# glass control tower and the conveyor bridges to the furnace tops, L4 the rolling mill and the stockyard gantry
# crane (premium materials from here: quartz, sea lanterns, copper), L5 the visitor pavilion with its roof garden,
# the observation crown on the control tower and the rail siding. Converters 2..5 are added along the hall.
NT_SIZE = (61, 48, 50)
NT_WX, NT_WZ, NT_WSIZE, NT_WHUT = (3, 47), 9, (11, 44, 11), (3, 1, 3)
NT_H = {1: 11, 2: 15, 3: 20, 4: 25, 5: 32}


def disc(r, cx, cz):
    return {(x, z) for x in range(int(cx - r - 1), int(cx + r + 2)) for z in range(int(cz - r - 1), int(cz + r + 2))
            if (x - cx) ** 2 + (z - cz) ** 2 <= r * r + 0.3}


def ring_of(cells):
    return {(x, z) for (x, z) in cells if any((x + a, z + b) not in cells for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))}


def ntw(rel, L):
    """Neoterra wing: a cylindrical BLAST-FURNACE TOWER, cast house with the smithing table at its foot."""
    d = Design("Neoterra", rel, NT_WSIZE, gy=0, paving="smooth_stone")
    H = NT_H[L]
    prem = L >= 4
    band = "cyan_concrete" if not prem else "cyan_terracotta"
    body, shell = disc(4.2, 5, 5), None
    shell = ring_of(body)
    inner = disc(3.2, 5, 5)
    for x, z in body:
        d.set(x, 0, z, "polished_andesite")
    for y in range(1, H + 1):
        for x, z in shell:
            if y <= 5:
                st = "light_gray_concrete"
            elif y % 4 == 2:
                st = band
            else:
                st = "gray_concrete"
            d.set(x, y, z, st)
    for x, z in body - shell:                              # cast-house ceiling = the glowing hearth above
        d.set(x, 6, z, "magma_block")
    for x, z in inner - disc(2.2, 5, 5):
        d.set(x, 7, z, "gray_concrete")
    # door and cast-house windows
    d.set(5, 1, 1, AIR), d.set(5, 2, 1, AIR)
    d.door(5, 1, 1, "north", "birch") if False else None
    d.set(5, 3, 1, "white_concrete")
    for x, z in ((1, 5), (9, 5)):
        d.window(x, 2, z, x, 3, z, "light_gray_stained_glass_pane" if not prem else "light_blue_stained_glass_pane")
    d.set(5, 0, 0, "polished_andesite"), d.set(4, 0, 0, "polished_andesite"), d.set(6, 0, 0, "polished_andesite")
    d.hut(*NT_WHUT, facing="east")
    # the cast house: tap-hole trough, smithing table, sample lab bench, lockers, lamps
    d.item(7, 1, 3, "smithing_table")
    put(d, [(5, 1, 8, "lava_cauldron"), (4, 1, 8, "polished_andesite"), (6, 1, 8, "polished_andesite"),
            (5, 2, 8, "iron_bars"), (5, 1, 7, plate()), (5, 1, 6, plate()),
            (8, 1, 5, slab("smooth_stone_slab", "top")), (8, 1, 6, slab("smooth_stone_slab", "top")),
            (8, 2, 5, "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=false]"),
            (2, 1, 5, "barrel[facing=east,open=false]"), (2, 1, 6, "barrel[facing=east,open=false]"),
            (2, 2, 5, "barrel[facing=east,open=false]"), (3, 1, 7, "anvil[facing=north]"),
            (7, 1, 7, "water_cauldron[level=3]"), (4, 1, 4, "yellow_carpet"), (5, 1, 4, "yellow_carpet"), (5, 1, 5, "yellow_carpet")])
    d.set(5, 5, 5, lantern(True)) if not prem else d.set(5, 5, 5, "sea_lantern")
    d.set(3, 5, 6, lantern(True))
    d.set(7, 5, 6, lantern(True))
    d.sign(5, 3, 0, "north", ["", "FURNACE", "", ""], "birch", glow=True, color="cyan")
    # top: open throat ring with a catwalk rail
    for x, z in shell:
        d.set(x, H + 1, z, "iron_bars")
    if L >= 2:
        # bustle main round the tuyere level and four uptakes over the top
        for x, z in ring_of(disc(5.2, 5, 5)):
            if d.bp.inside(x, 5, z) and (x, z) not in body:
                d.set(x, 5, z, "gray_concrete")
        for x, z in ((2, 2), (8, 2), (2, 8), (8, 8)):
            for y in range(H + 1, H + 4):
                d.set(x, y, z, "light_gray_concrete")
        for x in range(2, 9):
            d.set(x, H + 4, 2, "light_gray_concrete")
            d.set(x, H + 4, 8, "light_gray_concrete")
        for z in range(3, 8):
            d.set(5, H + 4, z, "light_gray_concrete")
        for y in range(H + 4, H + 7):
            d.set(5, y, 5, "gray_concrete")
    if L >= 3:
        # catwalk ring below the top and the access ladder on the south side
        yc = H - 3
        for x, z in ring_of(disc(5.2, 5, 5)):
            if d.bp.inside(x, yc, z) and (x, z) not in body:
                d.set(x, yc, z, slab("smooth_stone_slab", "top"))
                d.set(x, yc + 1, z, "iron_bars")
        for y in range(1, yc + 2):
            d.set(5, y, 10, "ladder[facing=south,waterlogged=false]")
        d.set(5, yc, 10, "ladder[facing=south,waterlogged=false]")
        d.set(5, yc + 1, 10, "ladder[facing=south,waterlogged=false]")
        for x, z in ((0, 5), (10, 5)):
            d.set(x, yc + 2, z, lantern(False))
    if L >= 4:
        # premium skin: quartz bands, sea-lantern ring, copper uptake caps
        for x, z in shell:
            for y in (H - 6, H - 1):
                d.set(x, y, z, "smooth_quartz")
            d.set(x, 4, z, "sea_lantern" if (x + z) % 3 == 0 else "smooth_quartz")
        for x, z in ((2, 2), (8, 2), (2, 8), (8, 8)):
            d.set(x, H + 4, z, "cut_copper")
    if L >= 5:
        # the crown: end-rod beams and a glowing cap on the downcomer
        for x, z in ((1, 5), (9, 5), (5, 1), (5, 9)):
            d.set(x, H + 2, z, "end_rod[facing=up]")
        d.set(5, H + 7, 5, "sea_lantern")
        d.set(5, H + 8, 5, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    connect_walls(d)
    return d


def nt_mat(L):
    prem = L >= 4
    return dict(rib="gray_concrete", panel="light_gray_concrete", band="cyan_concrete",
                glass="light_blue_stained_glass_pane" if prem else "light_gray_stained_glass_pane",
                roof="smooth_quartz" if prem else "smooth_stone", top="smooth_quartz" if prem else "white_concrete",
                light="sea_lantern" if prem else "glowstone", prem=prem)


def nt_lamp(d, x, y, z, M):
    """Ceiling light: a lantern hanging under the roof on L1-3, a sea lantern set into it from L4."""
    if M["prem"]:
        d.set(x, y + 1, z, "sea_lantern")
    else:
        d.set(x, y, z, lantern(True))


def nt_hall(d, L):
    """The melt shop: ribbed steel hall 21 x 15, glazed front, converters along the back, overhead crane."""
    M = nt_mat(L)
    X1, X2, Z1, Z2 = 20, 40, 10, 24
    rect(d, X1, Z1, X2, Z2, 1, "polished_andesite")
    ribs_x, ribs_z = (20, 24, 28, 32, 36, 40), (10, 14, 18, 24)
    for x in range(X1, X2 + 1):
        for z in range(Z1, Z2 + 1):
            if not (x in (X1, X2) or z in (Z1, Z2)):
                continue
            rib = (z in (Z1, Z2) and x in ribs_x) or (x in (X1, X2) and z in ribs_z)
            for y in range(2, 14):
                if rib:
                    st = M["rib"]
                elif y == 8:
                    st = M["band"]
                elif 9 <= y <= 11:
                    st = M["glass"]
                elif y >= 12:
                    st = M["top"]
                else:
                    st = M["panel"]
                d.set(x, y, z, st)
    rect(d, X1, Z1, X2, Z2, 14, M["roof"])
    ring(d, X1, Z1, X2, Z2, 15, M["top"])
    for x in range(23, 38):                                # skylight strips
        if x % 4 != 0:
            d.set(x, 14, 13, "glass")
            d.set(x, 14, 21, "glass")
    # glazed entrance front x 26..34 with doors, canopy and the name
    for x in range(26, 35):
        for y in range(2, 12):
            d.set(x, y, Z1, M["glass"] if x not in (26, 34) else M["rib"])
    for x in (29, 30, 31):
        d.door(x, 2, Z1, "north", "birch", "left" if x != 31 else "right")
    for x in range(25, 36):
        for z in (7, 8, 9):
            d.set(x, 7, z, slab(M["roof"] + "_slab" if M["prem"] else "smooth_stone_slab", "top"))
        d.set(x, 6, 7, "cyan_concrete") if False else None
    for x in (25, 35):
        d.set(x, 7, 7, M["top"])
    d.sign(30, 13, Z1 - 1, "north", ["NEOTERRA", "STEELWORKS", "", ""], "birch", glow=True, color="cyan")
    for x in (28, 32):
        d.set(x, 6, 8, lantern(True)) if not M["prem"] else d.set(x, 7, 8, "sea_lantern")
    # ---- converters along the back (one per level), each with its blast furnace at the tap, hood and duct
    for k, cx in enumerate((30, 26, 34, 22, 38)[:L]):
        for x in range(cx - 1, cx + 2):
            for z in (21, 22):
                d.set(x, 2, z, "polished_andesite")
                for y in (3, 4, 5):
                    d.set(x, y, z, "gray_concrete" if x != cx or z != 21 else "black_concrete")
                d.set(x, 9, z, "light_gray_concrete")
            d.set(x, 6, 22, slab("smooth_stone_slab"))
        d.set(cx, 6, 21, "magma_block")
        for y in range(10, 14):
            d.set(cx, y, 22, "light_gray_concrete")
        d.item(cx, 2, 20, "blast_furnace", "north")
        for tx in (cx - 2, cx + 2):
            if X1 < tx < X2:
                d.set(tx, 4, 21, "iron_bars")
                d.set(tx, 2, 21, "polished_andesite")
                d.set(tx, 3, 21, "iron_bars")
        d.set(cx, 3, 20, "iron_bars") if False else None
        d.sign(cx, 7, 21, "north", [f"CONVERTER {k + 1}", "", "", ""], "birch", glow=True, color="cyan") if False else None
    # ---- maintenance corner (west of the entrance): the anvil, grindstone, lockers, bench
    d.hut(25, 2, 11, "north")
    d.item(22, 2, 12, "anvil", "east")
    put(d, [(21, 2, 11, "barrel[facing=east,open=false]"), (21, 3, 11, "barrel[facing=east,open=false]"),
            (21, 2, 12, "barrel[facing=east,open=false]"), (23, 2, 11, "grindstone[face=floor,facing=north]"),
            (21, 2, 14, slab("smooth_stone_slab", "top")), (21, 2, 15, slab("smooth_stone_slab", "top")),
            (21, 3, 14, "crafting_table") if False else (21, 3, 15, pot("east")), (22, 2, 15, stair("polished_andesite_stairs", "west")),
            (21, 2, 17, "water_cauldron[level=3]")])
    # ---- control pulpit (north-east corner): glass booth with the operator's desk
    for x in range(36, 40):
        for z in range(11, 15):
            if x == 36 or z == 14:
                for y in (2, 3, 4):
                    d.set(x, y, z, "glass_pane" if (x, z) != (36, 13) or y == 4 else AIR)
            d.set(x, 5, z, slab("smooth_stone_slab", "top"))
    put(d, [(38, 2, 11, slab("smooth_stone_slab", "top")), (39, 2, 11, slab("smooth_stone_slab", "top")),
            (38, 3, 11, "daylight_detector[inverted=false,power=0]"), (39, 3, 11, "lever[face=floor,facing=south,powered=false]"),
            (38, 2, 12, stair("polished_andesite_stairs", "north")), (39, 2, 13, "lectern[facing=west,has_book=true,powered=false]"),
            (37, 2, 11, "potted_bamboo")])
    # ---- ladle transfer track, the ladle car, safety walkways, the overhead crane
    for x in range(21, 40):
        d.set(x, 2, 17, "rail[shape=east_west,waterlogged=false]")
    put(d, [(33, 2, 17, "lava_cauldron"), (27, 2, 17, "cauldron")])
    for x in range(23, 40):
        if x not in (29, 30, 31):
            d.set(x, 2, 15, "yellow_carpet")
        if d.get(x, 2, 19) == AIR:
            d.set(x, 2, 19, "yellow_carpet")
    for x in range(21, 40):
        d.set(x, 11, 11, slab("smooth_stone_slab", "top"))
        d.set(x, 11, 23, slab("smooth_stone_slab", "top"))
    for z in range(11, 24):
        d.set(26, 12, z, "yellow_concrete")
    for y in (9, 10, 11):
        d.set(26, y, 16, "chain[axis=y,waterlogged=false]")
    d.set(26, 12, 16, "gray_concrete")
    d.set(26, 8, 16, "cauldron")
    for x, z in ((23, 13), (30, 13), (37, 17), (23, 19), (30, 19) , (34, 13)):
        nt_lamp(d, x, 13, z, M)


def nt_stacks(d, L):
    """L2 twin red-and-white stacks behind the hall, flue ducts from the converter hoods."""
    top = {2: 34, 3: 38, 4: 42, 5: 45}[L]
    for cx in (16, 44):
        for x in range(cx - 2, cx + 3):
            for z in range(26, 31):
                for y in (2, 3):
                    d.set(x, y, z, "gray_concrete" if y == 2 else "light_gray_concrete")
        for y in range(4, top + 1):
            for x in range(cx - 1, cx + 2):
                for z in range(27, 30):
                    if (x, z) == (cx, 28):
                        continue
                    d.set(x, y, z, ("red_concrete" if (y // 3) % 2 else "white_concrete") if y >= 20 else "light_gray_concrete")
        d.set(cx, top + 1, 27, "lantern[hanging=false,waterlogged=false]" if L < 4 else "redstone_lamp[lit=true]")
        for x in range(cx - 1, cx + 2):
            for z in (26, 30):
                d.set(x, top, z, stair("polished_andesite_stairs" if L < 4 else "smooth_quartz_stairs", "north" if z == 26 else "south", "top"))
        # access ladder and a platform half way up
        for y in range(4, 22):
            d.set(cx, y, 26, "ladder[facing=north,waterlogged=false]")
        for x in range(cx - 2, cx + 3):
            for z in range(25, 32):
                if (x in (cx - 2, cx + 2) or z in (25, 31)) and d.get(x, 22, z) == AIR:
                    d.set(x, 22, z, slab("smooth_stone_slab", "top"))
                    d.set(x, 23, z, "iron_bars")
        d.set(cx, 22, 25, slab("smooth_stone_slab", "top"))
        d.set(cx, 23, 25, AIR)
        for x in range(cx - 1, cx + 2):
            if d.get(x, 22, 26) == AIR:
                d.set(x, 22, 26, slab("smooth_stone_slab", "top"))
    # flue ducts at y 16: riser from the hall roof, then over to the stack
    for (rx, sx) in ((22, 16), (38, 44)):
        d.set(rx, 15, 23, "light_gray_concrete")
        d.set(rx, 16, 23, "light_gray_concrete")
        for x in range(min(rx, sx), max(rx, sx) + 1):
            d.set(x, 16, 23, "light_gray_concrete")
        for z in range(23, 27):
            d.set(sx, 16, z, "light_gray_concrete")
        for x in range(min(rx, sx) + 1, max(rx, sx)):
            if x in (18, 19, 41, 42) and d.get(x, 15, 23) == AIR:
                for y in range(2, 16):
                    if d.get(x, y, 23) == AIR:
                        d.set(x, y, 23, "gray_concrete_powder" if False else "light_gray_concrete") if x in (18, 42) else None


def nt_windrow(d, z0, x1, x2, mats):
    """A stockpile windrow: 5-wide triangular cross-section centred on z0, ends tapered."""
    prof = {-2: 1, -1: 2, 0: 3, 1: 2, 2: 1}
    for x in range(x1, x2 + 1):
        taper = min(x - x1, x2 - x) + 1
        for dz, h in prof.items():
            for y in range(2, 2 + min(h, taper)):
                d.set(x, y, z0 + dz, mats[(x * 3 + y + dz * 5) % len(mats)])


def nt_stockyard(d, L):
    """L2 iron-ore windrow, L3 coal windrow, L4 coke-oven battery with its quench tower; stacker rails."""
    for x in range(10, 51):
        d.set(x, 1, 34, "gray_concrete")
    nt_windrow(d, 37, 12, 48, ("iron_ore", "red_sand", "gravel", "red_sand", "iron_ore", "coarse_dirt"))
    for x in range(10, 51):
        d.set(x, 2, 34, "rail[shape=east_west,waterlogged=false]")
    # the stacker: a boom on a rail car over the windrow
    sx = 22
    put(d, [(sx, 3, 34, "light_gray_concrete"), (sx + 1, 3, 34, "light_gray_concrete"), (sx, 4, 34, "yellow_concrete"),
            (sx, 5, 34, "yellow_concrete"), (sx, 6, 34, "yellow_concrete")])
    for z in range(35, 40):
        d.set(sx, 7 - (z - 35) // 2, z, slab("smooth_stone_slab", "top"))
        d.set(sx, 8 - (z - 35) // 2, z, "iron_bars") if z < 38 else None
    if L >= NT_AT["coalrow"]:
        nt_windrow(d, 42, 12, 48, ("coal_block", "black_concrete_powder", "coal_block", "gray_concrete_powder"))
    if L >= NT_AT["battery"]:
        # coke-oven battery z 45..48: brick oven block in a concrete frame, chargers' rail on top, quench tower
        for x in range(12, 49):
            for z in range(45, 49):
                for y in range(2, 8):
                    edge = x in (12, 48) or (x - 12) % 6 == 0
                    d.set(x, y, z, "gray_concrete" if edge or y == 7 else ("bricks" if z in (45, 48) else "bricks"))
                if z in (45, 48) and (x - 12) % 2 == 1 and not (x - 12) % 6 == 0:
                    d.set(x, 4, z, "iron_trapdoor[facing=%s,half=bottom,open=true,powered=false,waterlogged=false]" % ("north" if z == 45 else "south"))
            d.set(x, 8, 46, "rail[shape=east_west,waterlogged=false]")
            if x % 3 == 0:
                d.set(x, 8, 47, "iron_bars")
        for y in range(2, 18):                             # quench tower at the east end
            for x in range(50, 54):
                for z in range(44, 49):
                    if x in (50, 53) or z in (44, 48):
                        d.set(x, y, z, "light_gray_concrete" if y < 14 else "gray_concrete")
        for x in range(51, 53):
            for z in range(45, 48):
                d.set(x, 18, z, "iron_bars")
        d.set(51, 2, 44, AIR), d.set(51, 3, 44, AIR)


def nt_control_tower(d, L):
    """L3 the glass control tower at the gate (x 41..46, z 2..7): lobby, control room, shift office, meeting
    room; L4 laboratory and engineering floors; L5 the observation lounge crown and its spire."""
    M = nt_mat(L)
    X1, X2, Z1, Z2 = 41, 46, 2, 7
    top = {3: 18, 4: 26, 5: 26}[L]
    rect(d, X1, Z1, X2, Z2, 1, "polished_diorite")
    for y in range(2, top + 1):
        for x in range(X1, X2 + 1):
            for z in range(Z1, Z2 + 1):
                if not (x in (X1, X2) or z in (Z1, Z2)):
                    continue
                corner = x in (X1, X2) and z in (Z1, Z2)
                slabline = (y - 2) % 4 == 0 and y > 2
                d.set(x, y, z, M["top"] if corner else ("cyan_concrete" if slabline else M["glass"]))
    for yf in range(5, top + 1, 4):                        # floor slabs (y 5, 9, 13, 17, 21, 25)
        for x in range(X1 + 1, X2):
            for z in range(Z1 + 1, Z2):
                d.set(x, yf + 1, z, M["roof"]) if False else None
    floors = [y for y in (6, 10, 14, 18, 22) if y < top]
    for yf in floors:
        for x in range(X1 + 1, X2):
            for z in range(Z1 + 1, Z2):
                d.set(x, yf, z, "polished_diorite")
    rect(d, X1, Z1, X2, Z2, top, M["roof"])
    for x in range(X1, X2 + 1):
        for z in range(Z1, Z2 + 1):
            if x in (X1, X2) or z in (Z1, Z2):
                d.set(x, top + 1, z, "glass_pane")
    # ladder shaft in the south-east corner
    for y in range(2, top):
        d.set(45, y, 6, "ladder[facing=west,waterlogged=false]")
    d.set(43, 2, Z1, AIR), d.set(43, 3, Z1, AIR)
    d.door(43, 2, Z1, "north", "birch")
    d.sign(42, 4, Z1 - 1, "north", ["CONTROL", "TOWER", "", ""], "birch", glow=True, color="cyan")
    # lobby: reception desk, waiting bench, plants
    put(d, [(42, 2, 5, slab("smooth_stone_slab", "top")), (43, 2, 5, slab("smooth_stone_slab", "top")),
            (42, 3, 5, "potted_bamboo"), (43, 3, 5, "lantern[hanging=false,waterlogged=false]"),
            (42, 2, 6, stair("birch_stairs", "north")), (44, 2, 4, stair("polished_andesite_stairs", "east")),
            (44, 2, 3, "potted_azalea_bush"), (42, 2, 3, "cyan_carpet"), (43, 2, 4, "cyan_carpet")])
    nt_lamp(d, 43, 5, 4, M)
    # control room: consoles on top slabs with screens, operators' chairs
    put(d, [(42, 7, 3, slab("smooth_stone_slab", "top")), (43, 7, 3, slab("smooth_stone_slab", "top")),
            (44, 7, 3, slab("smooth_stone_slab", "top")), (42, 8, 3, "daylight_detector[inverted=false,power=0]"),
            (43, 8, 3, "daylight_detector[inverted=false,power=0]"), (44, 8, 3, "lever[face=floor,facing=south,powered=false]"),
            (42, 7, 4, stair("birch_stairs", "north")), (44, 7, 4, stair("birch_stairs", "north")),
            (42, 7, 6, "barrel[facing=up,open=false]"), (43, 7, 6, "light_gray_carpet"), (44, 7, 5, "light_gray_carpet")])
    nt_lamp(d, 43, 9, 5, M)
    # shift office: desk, files, plant
    put(d, [(42, 11, 5, slab("birch_slab", "top")), (42, 11, 4, slab("birch_slab", "top")), (42, 12, 4, cand(2, "white")),
            (43, 11, 5, stair("birch_stairs", "west")), (44, 11, 3, "barrel[facing=up,open=false]"),
            (43, 11, 3, "barrel[facing=up,open=false]"), (42, 11, 6, "potted_bamboo"), (44, 11, 5, "blue_carpet")])
    nt_lamp(d, 43, 13, 4, M)
    # meeting room: round table and chairs
    put(d, [(43, 15, 4, "birch_fence"), (43, 16, 4, plate("birch")), (42, 15, 4, stair("birch_stairs", "west")),
            (44, 15, 4, stair("birch_stairs", "east")), (43, 15, 3, stair("birch_stairs", "north")),
            (43, 15, 5, stair("birch_stairs", "south")), (42, 15, 6, "potted_fern"), (44, 15, 6, "white_carpet")])
    nt_lamp(d, 42, 17, 3, M)
    if L >= 4:
        put(d, [(42, 19, 3, slab("smooth_quartz_slab", "top")), (43, 19, 3, slab("smooth_quartz_slab", "top")),
                (42, 20, 3, "brewing_stand[has_bottle_0=true,has_bottle_1=true,has_bottle_2=false]"),
                (43, 20, 3, "flower_pot"), (44, 19, 3, "water_cauldron[level=3]"), (42, 19, 5, "lectern[facing=east,has_book=true,powered=false]"),
                (44, 19, 5, stair("birch_stairs", "east")), (43, 19, 6, "white_carpet")])
        nt_lamp(d, 43, 21, 4, M)
        put(d, [(42, 23, 3, "cartography_table"), (43, 23, 3, "cartography_table"), (42, 23, 4, stair("birch_stairs", "north")),
                (43, 23, 4, stair("birch_stairs", "north")), (42, 23, 6, shelf("east")), (42, 24, 6, shelf("east")),
                (44, 23, 3, "potted_bamboo"), (44, 23, 5, "cyan_carpet")])
        nt_lamp(d, 44, 25, 4, M)
    if L >= 5:
        # observation lounge crown on the roof: glass walls, quartz cap, sofas, telescope, spire with end rods
        for y in range(27, 31):
            for x in range(X1, X2 + 1):
                for z in range(Z1, Z2 + 1):
                    if x in (X1, X2) or z in (Z1, Z2):
                        d.set(x, y, z, M["top"] if (x in (X1, X2) and z in (Z1, Z2)) else "light_blue_stained_glass")
        rect(d, X1, Z1, X2, Z2, 31, "smooth_quartz")
        ring(d, X1 - 1, Z1 - 1, X2 + 1, Z2 + 1, 31, slab("smooth_quartz_slab"))
        for y in range(26, 31):
            d.set(45, y, 6, "ladder[facing=west,waterlogged=false]")
        put(d, [(42, 27, 3, stair("quartz_stairs", "north")), (43, 27, 3, stair("quartz_stairs", "north")),
                (42, 27, 4, stair("quartz_stairs", "west")), (44, 27, 3, "potted_bamboo"),
                (45, 27, 3, "iron_bars"), (45, 28, 3, "lightning_rod[facing=north,powered=false,waterlogged=false]"),
                (43, 27, 5, "cyan_carpet"), (43, 27, 4, "cyan_carpet"), (42, 27, 6, "potted_azalea_bush")])
        d.set(44, 30, 5, "sea_lantern")
        for y in range(32, 41):
            d.set(43, y, 4, "end_rod[facing=up]" if y > 35 else "smooth_quartz")


def nt_galleries(d, L):
    """L3 conveyor bridges: from transfer towers in the stockyard up to the furnace tops (x 7..9 and 51..53)."""
    Y = 16
    for cx in (8, 52):
        # transfer tower x cx-2..cx+2, z 31..35: open steel frame, deck with the head house, chute to the reclaimer
        for x, z in ((cx - 2, 31), (cx + 2, 31), (cx - 2, 35), (cx + 2, 35)):
            for y in range(2, Y + 5):
                d.set(x, y, z, "gray_concrete")
        for x in range(cx - 2, cx + 3):
            for z in range(31, 36):
                d.set(x, Y, z, "smooth_stone")
                if x in (cx - 2, cx + 2) or z in (31, 35):
                    d.set(x, Y + 4, z, "light_gray_concrete")
                    if not (x in (cx - 2, cx + 2) and z in (31, 35)):
                        d.set(x, Y + 1, z, "iron_bars")
            for z in (31, 35):
                d.set(x, 9, z, "light_gray_concrete")
        for z in range(31, 36):
            d.set(cx - 2, 9, z, "light_gray_concrete")
            d.set(cx + 2, 9, z, "light_gray_concrete")
        for x in range(cx - 1, cx + 2):                    # head house: glazed box over the transfer chute
            for z in range(32, 35):
                for y in (Y + 1, Y + 2, Y + 3):
                    if x != cx or z != 33:
                        d.set(x, y, z, "light_gray_stained_glass_pane" if (x != cx and z != 33) or y == Y + 3 else AIR)
                d.set(x, Y + 4, z, "smooth_stone")
        for y in range(2, Y):
            d.set(cx, y, 33, "light_gray_concrete")
        put(d, [(cx, Y + 1, 33, "hopper[enabled=true,facing=down]"), (cx + 1, Y + 1, 32, AIR), (cx + 1, Y + 2, 32, AIR),
                (cx + 2, Y + 3, 33, lantern(False)) if False else (cx - 2, Y + 2, 33, AIR)])
        # the covered gallery z 20..30: deck, belt, glazed sides, roof, two trestle columns
        for z in range(20, 31):
            for x in (cx - 1, cx, cx + 1):
                d.set(x, Y, z, "smooth_stone" if x != cx else "black_concrete")
                d.set(x, Y + 3, z, slab("smooth_stone_slab"))
            for x in (cx - 1, cx + 1):
                d.set(x, Y + 1, z, "light_gray_stained_glass_pane")
                d.set(x, Y + 2, z, "light_gray_stained_glass_pane")
            d.set(cx, Y + 1, z, "rail[shape=north_south,waterlogged=false]")
        for z in (25,):
            for x in (cx - 1, cx + 1):
                for y in range(2, Y):
                    d.set(x, y, z, "light_gray_concrete")
            d.set(cx, Y - 1, z, "light_gray_concrete")
        for x in (cx - 1, cx + 1):
            for y in range(2, Y):
                d.set(x, y, 30, "light_gray_concrete")


def nt_rolling_mill(d, L):
    """L4 the rolling mill x 19..41, z 26..32: sawtooth-roofed hall, roll stands, cooling bed, coil store."""
    M = nt_mat(L)
    X1, X2, Z1, Z2 = 19, 41, 26, 32
    rect(d, X1, Z1, X2, Z2, 1, "polished_andesite")
    for x in range(X1, X2 + 1):
        for z in range(Z1, Z2 + 1):
            if x in (X1, X2) or z in (Z1, Z2):
                for y in range(2, 9):
                    rib = (x - X1) % 4 == 0 and z in (Z1, Z2) or (x in (X1, X2) and z in (Z1, Z2))
                    d.set(x, y, z, M["rib"] if rib else ("white_concrete" if y < 6 else M["glass"] if y < 8 else M["top"]))
    for x in range(X1, X2 + 1):                           # sawtooth roof: north-facing glazing
        for z in range(Z1, Z2 + 1):
            k = (z - Z1) % 3
            d.set(x, 9, z, "smooth_stone" if k != 0 else "smooth_stone")
            if k == 2 and z < Z2:
                d.set(x, 10, z, stair("smooth_quartz_stairs", "north"))
            if k == 0 and Z1 < z < Z2:
                d.set(x, 10, z, "glass")
    d.double_door(29, 2, Z2, "x", "south", "birch")
    d.sign(30, 7, Z1 - 1, "north", ["ROLLING", "MILL", "", ""], "birch", glow=True, color="cyan") if False else None
    # roll stands along the centre line, the run-out table, cooling bed, coil store, crane runway
    for x in (24, 28, 32):
        put(d, [(x, 2, 28, "polished_andesite"), (x, 3, 28, "iron_block"), (x, 4, 28, "polished_andesite"),
                (x, 2, 30, "polished_andesite"), (x, 3, 30, "iron_block"), (x, 4, 30, "polished_andesite"),
                (x, 4, 29, "polished_andesite"), (x, 2, 29, "iron_bars")])
    for x in range(21, 39):
        if x not in (24, 28, 32):
            d.set(x, 2, 29, "rail[shape=east_west,waterlogged=false]")
    for x in range(34, 41):
        for z in (27, 31):
            d.set(x, 2, z, trap("iron_trapdoor", "north"))
    put(d, [(20, 2, 27, "barrel[facing=up,open=false]"), (20, 2, 31, "lectern[facing=east,has_book=true,powered=false]"),
            (21, 2, 31, slab("smooth_stone_slab", "top")), (21, 3, 31, "daylight_detector[inverted=false,power=0]"),
            (22, 2, 27, "light_gray_carpet"), (23, 2, 27, "yellow_carpet"), (26, 2, 27, "yellow_carpet"),
            (27, 2, 27, "yellow_carpet"), (30, 2, 27, "yellow_carpet"), (31, 2, 27, "yellow_carpet"),
            (26, 2, 31, "yellow_carpet"), (27, 2, 31, "yellow_carpet"), (30, 2, 31, "yellow_carpet"), (31, 2, 31, "yellow_carpet"),
            (22, 2, 31, "water_cauldron[level=3]")])
    for x, z in ((22, 29), (26, 29), (30, 29), (34, 29), (38, 29)):
        d.set(x, 9, z, "sea_lantern")


def nt_gantry(d, L):
    """L4 stockyard gantry crane on rails along z 33 and z 49."""
    for x in range(0, d.sx):
        d.set(x, 1, 49, "gray_concrete")
        d.set(x, 2, 49, "rail[shape=east_west,waterlogged=false]")
    gx = 36
    for z in (33, 49):
        for x in (gx, gx + 2):
            for y in range(2, 14):
                d.set(x, y, z, "yellow_concrete" if y > 2 else "gray_concrete")
    for z in range(33, 50):
        d.set(gx, 14, z, "yellow_concrete")
        d.set(gx + 2, 14, z, "yellow_concrete")
        d.set(gx + 1, 14, z, slab("smooth_stone_slab", "top"))
    put(d, [(gx + 1, 15, 40, "light_gray_concrete"), (gx + 1, 15, 41, "light_gray_concrete"),
            (gx + 1, 13, 41, "chain[axis=y,waterlogged=false]"), (gx + 1, 12, 41, "chain[axis=y,waterlogged=false]"),
            (gx + 1, 11, 41, "chain[axis=y,waterlogged=false]"), (gx + 1, 10, 41, "hopper[enabled=true,facing=down]")])
    for x in range(gx, gx + 3):                            # operator's cab under the girder
        d.set(x, 13, 47, "light_blue_stained_glass")
    d.set(gx + 1, 13, 47, "light_blue_stained_glass")


def nt_stoves(d, L):
    """L5 hot-blast stoves: two tall domed cylinders beside each furnace tower."""
    for cx in (4, 12, 48, 56):
        cells = disc(1.8, cx, 23)
        rim = ring_of(cells)
        for y in range(2, 22):
            for x, z in rim:
                d.set(x, y, z, "smooth_quartz" if y % 5 == 0 else "light_gray_concrete")
        for x, z in cells - rim:
            for y in range(2, 22):
                d.set(x, y, z, "gray_concrete")
        for x, z in cells:
            d.set(x, 22, z, "smooth_quartz_slab[type=bottom,waterlogged=false]" if (x, z) in rim else "smooth_quartz")
        d.set(cx, 23, 23, "smooth_quartz_slab[type=bottom,waterlogged=false]")
        for y in range(10, 13):                            # hot-blast main to the tower
            d.set(cx + (1 if cx in (4, 48) else -1) * 0, y, 21, "light_gray_concrete") if False else None
    for x in range(4, 13):
        d.set(x, 18, 21, "light_gray_concrete")
    for x in range(48, 57):
        d.set(x, 18, 21, "light_gray_concrete")
    for x in (8, 52):
        d.set(x, 18, 20, "light_gray_concrete")


def nt_hq(d, L):
    """L5 the headquarters tower west of the entrance (x 14..24, z 1..7), twin of the control tower in spirit:
    exhibition, cafe, open-plan office, boardroom, design studio, executive floor, roof garden."""
    X1, X2, Z1, Z2 = 14, 24, 1, 7
    top = 26
    rect(d, X1, Z1, X2, Z2, 1, "polished_diorite")
    floors = (6, 10, 14, 18, 22)
    for y in range(2, top + 1):
        for x in range(X1, X2 + 1):
            for z in range(Z1, Z2 + 1):
                if x in (X1, X2) or z in (Z1, Z2):
                    post = (x in (X1, X2) and z in (Z1, Z2)) or (z in (Z1, Z2) and x == 19)
                    d.set(x, y, z, "smooth_quartz" if post else ("cyan_terracotta" if y in floors else "light_blue_stained_glass_pane"))
    for yf in floors:
        rect(d, X1 + 1, Z1 + 1, X2 - 1, Z2 - 1, yf, "polished_diorite")
    rect(d, X1, Z1, X2, Z2, top, "smooth_quartz")
    ring(d, X1, Z1, X2, Z2, top + 1, "glass_pane")
    for y in range(2, top + 1):
        d.set(23, y, 6, "ladder[facing=west,waterlogged=false]")
    d.door(19, 2, Z1, "north", "birch")
    d.set(19, 4, Z1, "smooth_quartz")
    d.sign(19, 5, Z1 - 1, "north", ["NEOTERRA", "STEEL HQ", "Visitors", "welcome"], "birch", glow=True, color="cyan")
    # G: exhibition – a cast ingot, a model ladle, an anvil and a gold casting on plinths, info lecterns, benches
    put(d, [(16, 2, 3, "polished_andesite"), (16, 3, 3, "iron_block"), (16, 2, 5, "polished_andesite"), (16, 3, 5, "lava_cauldron"),
            (22, 2, 3, "polished_andesite"), (22, 3, 3, "anvil[facing=east]"), (22, 2, 5, "polished_andesite"),
            (22, 3, 5, "gold_block"), (17, 2, 4, "lectern[facing=west,has_book=true,powered=false]"),
            (21, 2, 4, "lectern[facing=east,has_book=true,powered=false]"), (18, 2, 6, stair("quartz_stairs", "south")),
            (20, 2, 6, stair("quartz_stairs", "south")), (19, 2, 3, "cyan_carpet"), (19, 2, 4, "cyan_carpet"),
            (19, 2, 5, "cyan_carpet"), (15, 2, 6, "potted_bamboo"), (15, 2, 2, "potted_bamboo")])
    for x in (16, 22):
        d.set(x, 5, 4, "sea_lantern")
    # F1 (y 7): cafe – counter with the coffee machine, two tables, plants
    put(d, [(15, 7, 2, slab("smooth_quartz_slab", "top")), (16, 7, 2, slab("smooth_quartz_slab", "top")),
            (17, 7, 2, slab("smooth_quartz_slab", "top")), (15, 8, 2, "brewing_stand[has_bottle_0=true,has_bottle_1=true,has_bottle_2=true]"),
            (16, 8, 2, "cake[bites=2]"), (15, 7, 3, "barrel[facing=up,open=false]"),
            (20, 7, 2, "potted_azalea_bush"), (21, 7, 2, "potted_fern"), (19, 7, 4, "light_blue_carpet"), (20, 7, 4, "light_blue_carpet")])
    for tx in (17, 21):
        put(d, [(tx, 7, 5, "birch_fence"), (tx, 8, 5, plate("birch")), (tx - 1, 7, 5, stair("birch_stairs", "west")),
                (tx + 1, 7, 5, stair("birch_stairs", "east"))])
    for x in (16, 21):
        d.set(x, 9, 4, "sea_lantern")
    # F2 (y 11): open-plan office – two desk rows with screens and chairs, printer, water cooler
    for x in (15, 16, 17, 19, 20, 21):
        put(d, [(x, 11, 3, slab("birch_slab", "top")), (x, 12, 3, "daylight_detector[inverted=false,power=0]" if x % 2 else "potted_bamboo"),
                (x, 11, 4, stair("birch_stairs", "north"))])
    put(d, [(15, 11, 6, "dispenser[facing=north,triggered=false]"), (17, 11, 6, "water_cauldron[level=3]"),
            (21, 11, 6, "barrel[facing=up,open=false]"), (19, 11, 6, "light_gray_carpet"), (20, 11, 5, "light_gray_carpet")])
    for x in (16, 20):
        d.set(x, 13, 4, "sea_lantern")
    # F3 (y 15): boardroom – long table with chairs, screen wall
    for x in (17, 18, 19, 20, 21):
        put(d, [(x, 15, 4, "birch_fence"), (x, 16, 4, plate("birch")), (x, 15, 3, stair("birch_stairs", "north")),
                (x, 15, 5, stair("birch_stairs", "south"))])
    put(d, [(16, 15, 4, stair("quartz_stairs", "west")), (15, 15, 4, "black_concrete"), (15, 16, 4, "black_stained_glass"),
            (22, 15, 2, "potted_bamboo"), (22, 15, 6, "potted_bamboo"), (15, 15, 2, "lectern[facing=east,has_book=true,powered=false]")])
    d.set(19, 17, 4, "sea_lantern")
    # F4 (y 19): design studio – drafting tables, model shelves, a smithing bench for prototypes
    put(d, [(15, 19, 2, "cartography_table"), (16, 19, 2, "cartography_table"), (15, 19, 3, stair("birch_stairs", "north")),
            (16, 19, 3, stair("birch_stairs", "north")), (19, 19, 2, shelf("south")), (20, 19, 2, shelf("south")),
            (19, 20, 2, shelf("south")), (20, 20, 2, shelf("south")), (22, 19, 4, "crafting_table"),
            (22, 19, 5, slab("smooth_quartz_slab", "top")), (22, 20, 5, pot("west")), (17, 19, 5, "white_carpet"),
            (18, 19, 5, "white_carpet"), (17, 19, 4, "white_carpet")])
    for x in (16, 21):
        d.set(x, 21, 4, "sea_lantern")
    # F5 (y 23): executive floor – desk, book wall, lounge sofa round a rug, view over the works
    put(d, [(16, 23, 3, slab("dark_oak_slab", "top")), (17, 23, 3, slab("dark_oak_slab", "top")), (16, 24, 3, cand(3, "white")),
            (16, 23, 4, stair("dark_oak_stairs", "north")), (15, 23, 2, "bookshelf"), (15, 24, 2, "bookshelf"),
            (16, 23, 2, "bookshelf"), (16, 24, 2, "bookshelf"),
            (20, 23, 5, stair("quartz_stairs", "south")), (21, 23, 5, stair("quartz_stairs", "south")),
            (22, 23, 4, stair("quartz_stairs", "east")), (20, 23, 4, "red_carpet"), (21, 23, 4, "red_carpet"),
            (20, 23, 3, "red_carpet"), (21, 23, 3, "red_carpet"), (22, 23, 2, "potted_azalea_bush")])
    for x in (17, 21):
        d.set(x, 25, 4, "sea_lantern")
    # roof garden
    for x in range(X1 + 1, X2):
        for z in range(Z1 + 1, Z2):
            if (x + z) % 3 == 0:
                d.set(x, top + 1, z, "moss_carpet")
    put(d, [(16, 27, 3, "azalea_leaves[distance=1,persistent=true,waterlogged=false]"),
            (21, 27, 5, "flowering_azalea_leaves[distance=1,persistent=true,waterlogged=false]"),
            (18, 27, 5, stair("birch_stairs", "south")), (19, 27, 5, stair("birch_stairs", "south"))])


def nt_plaza(d, L):
    """L5 entrance plaza: the giant-ladle sculpture on its plinth, flag masts, planters with trees, ore wagons
    on the siding."""
    for x in range(28, 33):
        for z in range(1, 5):
            d.set(x, 2, z, "polished_andesite" if x in (28, 32) or z in (1, 4) else "smooth_quartz")
    for x in range(29, 32):                                # the ladle: a tilted bowl pouring a glowing stream
        for z in (2, 3):
            for y in (3, 4, 5):
                d.set(x, y, z, "gray_concrete" if y < 5 or x != 30 else "magma_block")
    put(d, [(29, 6, 2, "gray_concrete"), (31, 6, 3, "gray_concrete"), (32, 5, 3, "orange_stained_glass"),
            (32, 4, 3, "orange_stained_glass"), (32, 3, 3, "shroomlight")])
    for x in (26, 34):
        for y in range(2, 12):
            d.set(x, y, 0, "iron_bars" if y < 11 else "light_gray_concrete")
        d.set(x, 9, 1, "cyan_wall_banner[facing=south]")
    for x, z in ((14, 9), (24, 9), (36, 9), (46, 9)):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if d.bp.inside(x + dx, 2, z + dz) and d.air(x + dx, 2, z + dz):
                    d.set(x + dx, 2, z + dz, "smooth_quartz_slab[type=bottom,waterlogged=false]")
        d.set(x, 2, z, "moss_block")
        for y in range(3, 6):
            d.set(x, y, z, logb("birch_log"))
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for y in (6, 7):
                    if d.bp.inside(x + dx, y, z + dz) and d.air(x + dx, y, z + dz):
                        d.set(x + dx, y, z + dz, "azalea_leaves[distance=1,persistent=true,waterlogged=false]")
    for x0 in (14, 22, 30, 40):                            # ore wagons on the siding
        for x in range(x0, x0 + 3):
            d.set(x, 3, 49, "hopper[enabled=true,facing=down]" if x == x0 + 1 else "gray_concrete")


def nt_monitor(d, L):
    """L5 roof monitor on the melt shop: a glazed clerestory lantern along the ridge, roof vents."""
    for x in range(22, 39):
        for z in range(15, 20):
            edge = x in (22, 38) or z in (15, 19)
            for y in (15, 16, 17):
                if edge:
                    d.set(x, y, z, "light_blue_stained_glass" if y < 17 and (x - 22) % 4 else "smooth_quartz")
            d.set(x, 18, z, "smooth_quartz_slab[type=bottom,waterlogged=false]")
    for x in (24, 28, 32, 36):
        d.set(x, 15, 12, "cut_copper")
        d.set(x, 16, 12, "cut_copper_slab[type=bottom,waterlogged=false]")


def nt_power(d, L):
    """L5 the works power station: hyperbolic cooling tower (west end of the stockyard) and the turbine house
    with its switch room (east end)."""
    # cooling tower centred (5, 43): radius pinches from 5 to 3.6 at two thirds of the height, flares to the lip
    for y in range(2, 28):
        t = (y - 2) / 25
        r = 5.2 - 2.4 * (1 - (1 - t / 0.7) ** 2) if t < 0.7 else 2.8 + 1.4 * ((t - 0.7) / 0.3)
        cells = ring_of(disc(r, 5, 43))
        for x, z in cells:
            if d.bp.inside(x, y, z):
                d.set(x, y, z, "white_concrete" if y % 6 else "light_gray_concrete")
    for x, z in ring_of(disc(5.2, 5, 43)):                 # open legs at the foot
        if (x + z) % 3 == 0:
            d.set(x, 2, z, AIR)
    for x, z in disc(4.2, 5, 43):
        d.set(x, 1, z, WATER)
        d.set(x, 0, z, "structurize:blocksolidsubstitution")

    # turbine house x 54..60, z 36..48: glass clerestory, turbine sets, switch gallery
    X1, X2, Z1, Z2 = 54, 60, 36, 48
    rect(d, X1, Z1, X2, Z2, 1, "polished_andesite")
    for x in range(X1, X2 + 1):
        for z in range(Z1, Z2 + 1):
            if x in (X1, X2) or z in (Z1, Z2):
                for y in range(2, 12):
                    rib = z in (Z1, Z2) and x in (X1, X2) or (x in (X1, X2) and (z - Z1) % 4 == 0)
                    d.set(x, y, z, "gray_concrete" if rib else ("white_concrete" if y < 8 else
                                                                 "light_blue_stained_glass_pane" if y < 11 else "smooth_quartz"))
    rect(d, X1, Z1, X2, Z2, 12, "smooth_quartz")
    ring(d, X1, Z1, X2, Z2, 13, "white_concrete")
    d.double_door(X1, 2, 41, "z", "west", "birch")
    d.sign(X1 - 1, 9, 42, "west", ["POWER", "STATION", "", ""], "birch", glow=True, color="cyan")
    for z0 in (38, 44):                                    # two turbine-generator sets
        for z in range(z0, z0 + 3):
            put(d, [(56, 2, z, "polished_andesite"), (57, 2, z, "polished_andesite"), (58, 2, z, "polished_andesite"),
                    (57, 3, z, "smooth_quartz" if z != z0 + 1 else "cyan_terracotta")])
        put(d, [(56, 3, z0 + 1, "iron_bars"), (58, 3, z0 + 1, "iron_bars"), (57, 4, z0 + 1, "lightning_rod[facing=up,powered=false,waterlogged=false]")])
    put(d, [(59, 2, 42, slab("smooth_quartz_slab", "top")), (59, 2, 41, slab("smooth_quartz_slab", "top")),
            (59, 3, 42, "daylight_detector[inverted=false,power=0]"), (59, 3, 41, "lever[face=floor,facing=west,powered=false]"),
            (58, 2, 42, stair("birch_stairs", "east")), (55, 2, 37, "barrel[facing=up,open=false]"),
            (55, 2, 47, "barrel[facing=up,open=false]"), (59, 2, 37, "water_cauldron[level=3]"),
            (55, 2, 43, "yellow_carpet"), (56, 2, 43, "yellow_carpet"), (57, 2, 43, "yellow_carpet"), (58, 2, 43, "yellow_carpet"),
            (55, 2, 42, "yellow_carpet"), (55, 2, 39, "yellow_carpet"), (55, 2, 40, "yellow_carpet"), (59, 2, 47, "chest[facing=west,type=single,waterlogged=false]")])
    for z in (39, 42, 45):
        d.set(57, 11, z, "sea_lantern")
    for x in range(54, 61):                                # cable gantry towards the works
        pass
