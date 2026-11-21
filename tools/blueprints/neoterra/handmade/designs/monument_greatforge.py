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
    WT = 4 if L <= 2 else 8                               # wall top
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
    if L >= 3:                                            # string course between the storeys
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
    if L <= 2:
        put(d, [(8, 1, 4, "coal_block"), (8, 2, 4, "black_carpet"), (8, 1, 5, "barrel[facing=up,open=false]")])
    lamp(d, 3, 4 if L >= 3 else 3, 6)
    lamp(d, 7, 4 if L >= 3 else 3, 6)
    # sign over the door
    d.sign(5, WT + 2 if L <= 2 else 6, 1, "north", ["", "FORGE", "", ""], "dark_oak")
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
        put(d, [(3, 1, 3, "stone_bricks"), (3, 2, 3, "anvil[facing=north]")] if L == 2 else [])
    if L >= 3:
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
    if L >= 4:
        # pentice roof over the door on brackets, lamps beside it, corbelled chimney cap
        for x in range(3, 8):
            d.set(x, 4 if L < 3 else 4, 1, stair("deepslate_tile_stairs", "south"))
        d.set(3, 3, 1, "dark_oak_fence")
        d.set(7, 3, 1, "dark_oak_fence")
        for x in range(3, 8):
            for z in range(9, 14):
                pass
        for x in range(3, 8):
            for z in (9, 13):
                if 0 <= z <= 12:
                    d.set(x, CH, z, stair("brick_stairs", "south" if z == 9 else "north", "top"))
        for z in range(10, 13):
            d.set(3, CH, z, stair("brick_stairs", "east", "top"))
            d.set(7, CH, z, stair("brick_stairs", "west", "top"))
        for x in (4, 6):
            d.set(x, CH + 1, 10, "terracotta")
            d.set(x, CH + 1, 12, "terracotta")
        put(d, [(1, 2, 1, "stone_bricks"), (1, 3, 1, "lantern[hanging=false,waterlogged=false]"),
                (9, 2, 1, "stone_bricks"), (9, 3, 1, "lantern[hanging=false,waterlogged=false]")])
    if L >= 5:
        # cast-iron cresting on the ridge, weather vane, window boxes, horseshoe arch banner
        top = RY + 4
        for z in range(3, 10):
            if z in (5, 6):
                continue
            d.set(5, top + 1, z, "iron_bars")
        d.set(5, top + 1, 2, "stone_bricks")
        d.set(5, top + 2, 2, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        for x, z, f in ((0, 5, "west"), (0, 8, "west"), (10, 5, "east"), (10, 8, "east")):
            d.set(x, 1, z, trap("dark_oak_trapdoor", f, "top"))
            d.set(x, 2, z, "potted_red_tulip" if z == 5 else "potted_cornflower")
        d.banner(5, 3, 1, "north", "black")
    connect_walls(d)
    return d


