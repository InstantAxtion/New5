"""
Compound residences and yards – sky tower (+ flats) and twin builder (+ annex).

SKY TOWER (parent: lobby, café, concierge, penthouse/caretaker; 4 child flats on every level)
  Neoterra    "Skyline Residences": 17 x 15 glass high-rise, one flat per storey. Double-height glass lobby with a
              café bar and concierge desk, cantilevered balconies on the street face (the first one doubles as the
              entrance canopy), stair core with a glazed stairwell at the back. Glass penthouse on the roof that
              grows from a studio (L1) to a full-width suite with hot tub, roof garden (L4) and glowing corner
              fins + spire (L5).
  Hearthwood  "Albion Mansions": Edwardian red-brick mansion block, 27 wide, two flats per floor either side of a
              central stair hall, three-storey bay windows, stone portico, steep tiled roof with end chimneys.
              Porter's lodge and residents' parlour on the ground floor; garret rooms with dormers in the attic
              (L3+), front railings and garden (L2+), rear garden (L4+), roof lantern (L5).
  Cascadia    "Ridgeback Lodge": timber-and-stone mountain lodge, gable to the street. River-rock ground storey
              (great room with stone fireplace, keeper's bunks, kitchen), two log storeys with two flats each,
              opened from a covered west gallery with an outside stair, deck balconies on the east. Porch (L2+),
              hot-tub deck (L3+), log woodshed (L4+), lookout cupola (L5).
  Flats (child): each a furnished apartment – living room, kitchen run (furnace, smoker, sink, crafting table,
  barrel), main bedroom (double bed from L2) and a children's room that fills with beds from L3, bookshelves +
  jukebox (L4), ender chest (L5).

TWIN BUILDER (parent = first builder's workshop + the shared yard; annex = the second builder's workshop)
  Neoterra    Construction depot: two flat-roofed prefab sheds with glass clerestories and safety-striped door
              frames, steel rack aisles inside, shared canopy over the drive-through, tower crane in the rear yard
              (L3+), scaffold tower, concrete-mixer bay, stacked materials.
  Hearthwood  Master builder's yard: brick-and-timber workshop with a gable to the street, a timber hoist beam with
              pulley over the loft doors, a walled yard with arched gateway, timber stacks and a sawpit; the annex
              is an open-fronted masons' lodge (oak posts, tiled roof) with rack bays.
  Cascadia    Timber-framing yard: big log barn with a long gable along the street and wide doors, log A-frame
              derrick over the yard, lumber stacks and sawhorses; the annex is a log workshop with a lean-to
              rack shed.
"""
from hm import Design, design, AIR, D4

OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}
CW = {"north": "east", "east": "south", "south": "west", "west": "north"}
FLAT = "fundamentals/skytowerflat0.blueprint"
ANNEX = "fundamentals/twinbuilderannex0.blueprint"


# ============================================================================================ small helpers
def stair(b, facing, half="bottom", shape="straight"):
    b = b if b.endswith("stairs") else b + "_stairs"
    return f"{b}[facing={facing},half={half},shape={shape},waterlogged=false]"


def slab(b, t="bottom"):
    b = b if b.endswith("slab") else b + "_slab"
    return f"{b}[type={t},waterlogged=false]"


def trap(wood, facing, half="top", open_=False):
    return f"{wood}_trapdoor[facing={facing},half={half},open={'true' if open_ else 'false'},powered=false," \
           f"waterlogged=false]"


def fence(wood):
    return f"{wood}_fence[east=false,north=false,south=false,waterlogged=false,west=false]"


def gate(wood, facing):
    return f"{wood}_fence_gate[facing={facing},in_wall=false,open=false,powered=false]"


def log(b, axis="y"):
    return f"{b}[axis={axis}]"


def lantern(hanging=True, soul=False):
    return f"{'soul_' if soul else ''}lantern[hanging={'true' if hanging else 'false'},waterlogged=false]"


def endrod(facing="down"):
    return f"end_rod[facing={facing}]"


def chain():
    return "chain[axis=y,waterlogged=false]"


def cells(x1, z1, x2, z2):
    for z in range(min(z1, z2), max(z1, z2) + 1):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            yield x, z


def flight(d, x, z, y, n, direction, block, support=None):
    """Straight flight of n stairs from (x,z) on walking level y climbing toward `direction`; clears 3 above each
    step. Returns the landing cell."""
    dx, dz = D4[direction]
    for i in range(n):
        cx, cz, h = x + dx * i, z + dz * i, y + i
        d.set(cx, h, cz, stair(block, direction))
        for k in (1, 2, 3):
            if d.bp.inside(cx, h + k, cz):
                d.set(cx, h + k, cz, AIR)
        if support:
            for yy in range(y, h):
                d.set(cx, yy, cz, support)
    return x + dx * n, z + dz * n, y + n


def nightstand(d, x, y, z, wood, light="candle"):
    d.set(x, y, z, slab(wood, "top"))
    if light == "candle":
        d.candle(x, y + 1, z, 1)
    elif light == "lantern":
        d.set(x, y + 1, z, lantern(False))
    elif light:
        d.set(x, y + 1, z, light)


def wardrobe(d, x, y, z, facing, top):
    d.set(x, y, z, f"chest[facing={facing},type=single,waterlogged=false]")
    d.set(x, y + 1, z, top)


def rugc(d, x1, z1, x2, z2, y, color):
    for x, z in cells(x1, z1, x2, z2):
        if d.air(x, y, z):
            d.set(x, y, z, f"{color}_carpet")


def planter(d, x1, z1, x2, z2, y, plants=("azalea", "flowering_azalea", "fern")):
    for i, (x, z) in enumerate(cells(x1, z1, x2, z2)):
        d.set(x, y, z, "moss_block" if i % 3 else "grass_block[snowy=false]")
        if d.air(x, y + 1, z):
            d.set(x, y + 1, z, plants[i % len(plants)])


def ring(d, x1, z1, x2, z2, y1, y2, block):
    for y in range(y1, y2 + 1):
        for x, z in cells(x1, z1, x2, z2):
            if x in (x1, x2) or z in (z1, z2):
                d.set(x, y, z, block)


def chiseled(facing):
    return (f"chiseled_bookshelf[facing={facing},slot_0_occupied=true,slot_1_occupied=true,slot_2_occupied=false,"
            f"slot_3_occupied=true,slot_4_occupied=false,slot_5_occupied=true]")


def tree(d, x, z, y, logb="birch_log", leaves="azalea_leaves", h=4):
    for k in range(h):
        d.set(x, y + k, z, log(logb))
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            for k in (h - 1, h):
                if (dx, dz) != (0, 0) or k == h:
                    if d.air(x + dx, y + k, z + dz):
                        d.set(x + dx, y + k, z + dz, f"{leaves}[distance=1,persistent=true,waterlogged=false]")
    d.set(x, y + h + 1, z, f"{leaves}[distance=1,persistent=true,waterlogged=false]")


def add_child(d, x0, y0, z0, w, h, dpt, hut, path):
    """Reserve the child's box (x0..x0+w-1, y0..y0+h-1, z0..) and place its hut at local hut=(hx, hy, hz)."""
    d.reserve(x0, y0, z0, x0 + w - 1, y0 + h - 1, z0 + dpt - 1)
    hx, hy, hz = hut
    d.child_hut(x0 + hx, y0 + hy - 1, z0 + hz, path)


# ============================================================================================ SKY TOWER
# Flat (child) boxes: local origin = NW interior corner of the flat on its floor slab (y=0 is the slab, walking
# y=1..4, the parent's next slab above). FW x FD footprint; HUT = local hut cell (y = 1).
NT = dict(X1=3, X2=19, Z1=4, Z2=18, SLABS=(7, 12, 17, 22), ROOF=27, FX=4, FZ=5, FW=15, FD=9, HUT=(6, 1, 8))
HW = dict(X1=1, X2=29, Z1=5, Z2=17, SLABS=(6, 11), ROOF=16, FXS=(2, 18), FZ=6, FW=11, FD=11, HUT=(5, 1, 3))
CA = dict(X1=8, X2=20, Z1=4, Z2=26, SLABS=(6, 11), ROOF=16, FX=9, FZS=(5, 16), FW=11, FD=10, HUT=(4, 1, 4))


# ---------------------------------------------------------------------------------------------- flats
def flat_nt(rel, L):
    G = NT
    d = Design("Neoterra", rel, (G["FW"], 5, G["FD"]), gy=0, paving="birch_planks")
    y = 1
    wall = "white_concrete"
    d.fill(5, 1, 0, 5, 4, 8, wall)                       # bedrooms | living
    d.fill(0, 1, 4, 4, 4, 4, wall)                       # main bedroom | kids' room
    d.door(5, y, 3, "east", "birch")
    d.door(5, y, 6, "east", "birch", "right")
    for x, z in cells(0, 0, 4, 3):
        d.set(x, 0, z, "light_gray_wool")
    for x, z in cells(0, 5, 4, 8):
        d.set(x, 0, z, "light_blue_wool" if L >= 3 else "light_gray_wool")
    # main bedroom: bed head against the window wall
    d.bed(1, y, 0, "north", "cyan")
    if L >= 2:
        d.bed(2, y, 0, "north", "cyan")
        nightstand(d, 3, y, 0, "birch", endrod("up"))
    nightstand(d, 0, y, 0, "birch", endrod("up"))
    if L < 2:
        d.set(2, y, 0, "potted_bamboo")
    wardrobe(d, 4, y, 0, "south", "white_concrete")
    d.set(4, y, 1, "white_concrete")
    d.set(4, y + 1, 1, "white_concrete")
    # kids' room: beds with their heads on the side glass
    nk = max(0, L - 2)
    for i in range(nk):
        d.bed(0, y, 5 + i, "west", ("light_blue", "lime", "yellow")[i])
    d.set(0, y, 8, slab("birch", "top"))                 # desk
    d.set(0, y + 1, 8, endrod("up"))
    d.chair(1, y, 8, "east", "birch", sit=False)
    if L >= 4:
        d.bookshelf(4, y, 8)
        d.bookshelf(3, y, 8)
        d.set(4, y + 1, 8, "potted_cactus")
    else:
        d.set(4, y, 8, "potted_bamboo")
    # living / kitchen
    run = [(9, "furnace"), (10, "smoker"), (11, "sink"), (12, "crafting_table"), (13, "barrel"), (14, "fridge")]
    for x, k in run:
        if k == "sink":
            d.set(x, y, 8, "water_cauldron[level=3]")
        elif k == "fridge":
            d.set(x, y, 8, "iron_block")
            d.set(x, y + 1, 8, "iron_block")
        elif k == "barrel":
            d.item(x, y, 8, "barrel", "north")
        else:
            d.item(x, y, 8, k, "north" if k != "crafting_table" else None)
        if k != "fridge":
            d.set(x, y + 2, 8, slab("smooth_quartz", "top"))
    d.hut(*G["HUT"])
    d.set(6, y + 1, 8, endrod("up"))
    for x in (10, 11, 12):                               # island with stools
        d.set(x, y, 6, "smooth_quartz")
    d.set(12, y + 1, 6, "potted_white_tulip")
    d.chair(10, y, 5, "north", "smooth_quartz")
    d.chair(11, y, 5, "north", "smooth_quartz")
    if L >= 2:                                           # sofa facing the balcony view
        rugc(d, 7, 0, 10, 1, y, "light_gray")
        for x in (8, 9, 10):
            d.chair(x, y, 2, "south", "white_wool" if False else "birch")
        d.set(7, y, 2, trap("birch", "west", "bottom", True))
        d.set(9, y, 1, slab("smooth_quartz", "top"))
        d.set(9, y + 1, 1, "potted_azure_bluet")
    d.set(6, y, 0, "potted_bamboo")
    d.set(14, y, 2, "potted_bamboo")
    if L >= 4:
        d.item(14, y, 0, "jukebox")
    else:
        d.set(14, y, 0, "smooth_quartz")
    if L >= 5:
        d.item(14, y, 4, "ender_chest", "west")
    for x, z in ((2, 2), (2, 6), (9, 3), (11, 7), (13, 2)):
        d.set(x, 4, z, endrod("down"))
    return d


def flat_hw(rel, L):
    G = HW
    d = Design("Hearthwood", rel, (G["FW"], 5, G["FD"]), gy=0, paving="oak_planks")
    y = 1
    wall = "white_terracotta"
    # cross hall z=4 (doors from the stair hall at either end); bedrooms behind a wall at z=5
    d.fill(0, 1, 5, 10, 4, 5, wall)
    d.fill(5, 1, 6, 5, 4, 10, wall)
    d.fill(5, 1, 0, 5, 4, 2, wall)                       # parlour | kitchen stub wall
    d.door(2, y, 5, "south", "dark_oak")
    d.door(8, y, 5, "south", "dark_oak", "right")
    for x in range(0, 11):
        d.set(x, 0, 4, "dark_oak_planks")                # hall runner boards
    rugc(d, 1, 4, 9, 4, y, "red")
    # parlour (north-west, bay window in front)
    d.set(0, 0, 0, "oak_planks")
    if L >= 2:
        d.chair(0, y, 1, "west", "dark_oak")
        d.chair(0, y, 2, "west", "dark_oak", sit=False)
        d.set(0, y, 3, trap("dark_oak", "south", "bottom", True))
        d.set(1, y, 1, slab("dark_oak", "top"))
        d.set(1, y + 1, 1, "potted_red_tulip")
    rugc(d, 1, 2, 3, 3, y, "red")
    if L >= 4:
        d.item(4, y, 0, "jukebox")
        d.set(4, y + 1, 0, "potted_lily_of_the_valley")
    else:
        d.set(4, y, 0, slab("dark_oak", "top"))
        d.set(4, y + 1, 0, "potted_azure_bluet")
    d.set(0, y, 0, "potted_fern")
    # kitchen / dining (north-east): range against the east wall, table by the bay
    run = [(0, "furnace"), (1, "smoker"), (2, "sink"), (3, "crafting_table")]
    for z, k in run:
        if k == "sink":
            d.set(10, y, z, "water_cauldron[level=3]")
        else:
            d.item(10, y, z, k, "west" if k != "crafting_table" else None)
        d.set(10, y + 2, z, slab("dark_oak", "top"))
    d.set(10, y + 3, 1, "bricks")                        # range hood
    d.item(8, y, 0, "barrel", "south")
    d.set(8, y + 2, 0, slab("dark_oak", "top"))
    d.set(8, y + 3, 0, "decorated_pot[cracked=false,facing=south,waterlogged=false]")
    d.table(7, y, 1, "dark_oak")
    d.table(7, y, 2, "dark_oak") if L >= 2 else None
    d.chair(6, y, 1, "west", "dark_oak")
    d.chair(8, y, 1, "east", "dark_oak")
    if L >= 2:
        d.chair(6, y, 2, "west", "dark_oak")
        d.chair(8, y, 2, "east", "dark_oak")
    d.hut(*G["HUT"])
    if L >= 5:
        d.item(6, y, 0, "ender_chest", "south")
    else:
        d.set(6, y, 0, "potted_red_tulip")
    # main bedroom (south-east): double bed from L2, head against the back wall
    d.bed(7, y, 10, "south", "red")
    if L >= 2:
        d.bed(8, y, 10, "south", "red")
        nightstand(d, 9, y, 10, "dark_oak")
    nightstand(d, 6, y, 10, "dark_oak")
    wardrobe(d, 10, y, 7, "west", "dark_oak_planks")
    rugc(d, 6, 7, 9, 8, y, "orange")
    # children's room (south-west)
    nk = max(0, L - 2)
    for i in range(nk):
        d.bed(i * 2 if i < 2 else 4, y, 10, "south", ("blue", "green", "yellow")[i])
    if nk < 3:
        d.set(4, y, 10, slab("oak", "top"))
        d.candle(4, y + 1, 10, 1)
        d.chair(4, y, 9, "south", "oak", sit=False)
    if L >= 4:
        d.bookshelf(0, y, 6)
        d.bookshelf(0, y, 7)
        d.set(1, y, 6, "potted_dandelion")
    else:
        d.set(0, y, 6, f"chest[facing=east,type=single,waterlogged=false]")
    d.set(1, y, 10 if nk == 0 else 8, "potted_oxeye_daisy") if nk == 0 else None
    for x, z in ((2, 1), (8, 2), (3, 8), (8, 8), (5, 4)):
        d.set(x, 4, z, lantern())
    return d


def flat_ca(rel, L):
    G = CA
    d = Design("Cascadia", rel, (G["FW"], 5, G["FD"]), gy=0, paving="spruce_planks")
    y = 1
    wall = "stripped_spruce_log[axis=y]"
    board = "spruce_planks"
    d.fill(0, 1, 4, 4, 4, 4, board)
    d.fill(0, 1, 6, 4, 4, 6, board)
    d.fill(5, 1, 0, 5, 4, 9, wall)
    d.set(5, y, 5, AIR)
    d.set(5, y + 1, 5, AIR)
    d.set(5, y + 2, 5, log("stripped_spruce_log", "z"))
    d.door(2, y, 4, "north", "spruce")
    d.door(2, y, 6, "south", "spruce", "right")
    rugc(d, 0, 5, 4, 5, y, "brown")
    # main bedroom (north-west)
    d.bed(1, y, 0, "north", "brown")
    if L >= 2:
        d.bed(2, y, 0, "north", "brown")
        nightstand(d, 3, y, 0, "spruce", "lantern")
    nightstand(d, 0, y, 0, "spruce", "lantern")
    wardrobe(d, 4, y, 0, "south", "spruce_planks")
    rugc(d, 1, 2, 3, 3, y, "green")
    # bunk room (south-west)
    nk = max(0, L - 2)
    for i in range(nk):
        d.bed(0, y, 7 + i, "west", ("green", "orange", "light_gray")[i])
    if L >= 4:
        d.bookshelf(4, y, 9)
        d.bookshelf(4, y, 8)
    else:
        d.keg(4, y, 9, "north")
    if nk < 3:
        d.set(0, y, 9, "chest[facing=east,type=single,waterlogged=false]")
    d.hut(*G["HUT"])
    # great room: kitchen on the back wall, table, rocker by the balcony
    run = [(6, "furnace"), (7, "smoker"), (8, "sink"), (9, "crafting_table"), (10, "barrel")]
    for x, k in run:
        if k == "sink":
            d.set(x, y, 9, "water_cauldron[level=3]")
        elif k == "barrel":
            d.item(x, y, 9, "barrel", "north")
        else:
            d.item(x, y, 9, k, "north" if k != "crafting_table" else None)
        d.set(x, y + 2, 9, slab("spruce", "top"))
    d.set(7, y + 3, 9, "cobblestone")
    d.table(8, y, 6, "spruce")
    d.chair(7, y, 6, "west", "spruce")
    d.chair(9, y, 6, "east", "spruce")
    if L >= 2:
        d.chair(8, y, 7, "south", "spruce")
        d.chair(8, y, 5, "north", "spruce")
        d.chair(6, y, 1, "west", "dark_oak")
        d.chair(6, y, 2, "west", "dark_oak", sit=False)
        d.set(7, y, 1, slab("spruce", "top"))
        d.set(7, y + 1, 1, "potted_fern")
        rugc(d, 7, 2, 9, 3, y, "brown")
    if L >= 4:
        d.item(10, y, 0, "jukebox")
    else:
        d.keg(10, y, 0, "west")
    if L >= 5:
        d.item(9, y, 0, "ender_chest", "south")
    else:
        d.set(9, y, 0, "potted_spruce_sapling")
    d.set(6, y, 9 - 1, "potted_fern")
    for x, z in ((2, 2), (2, 8), (8, 2), (8, 7), (2, 5)):
        d.set(x, 4, z, lantern())
    return d


@design("skytowerflat")
def skytowerflat(pack, rel, L):
    return {"Neoterra": flat_nt, "Hearthwood": flat_hw, "Cascadia": flat_ca}[pack](rel, L)


# ---------------------------------------------------------------------------------------------- Neoterra tower
def skytower_nt(rel, L):
    G = NT
    d = Design("Neoterra", rel, (23, 44, 23), paving="smooth_stone")
    X1, X2, Z1, Z2 = G["X1"], G["X2"], G["Z1"], G["Z2"]
    S, R = G["SLABS"], G["ROOF"]
    col, glass, white = "light_gray_concrete", "light_blue_stained_glass_pane", "white_concrete"
    # ---- plaza
    for x, z in cells(0, 0, 22, 22):
        d.set(x, 1, z, "smooth_stone" if (x + z) % 2 else "polished_diorite")
    for x in range(9, 14):
        for z in range(0, Z1):
            d.set(x, 1, z, "polished_andesite")
    # ---- slabs and the shell
    d.fill(X1, 1, Z1, X2, 1, Z2, "polished_andesite")
    for s in S + (R,):
        d.fill(X1, s, Z1, X2, s, Z2, white)
    storeys = [(2, 6)] + [(s + 1, s + 4) for s in S]
    for (ya, yb) in storeys:
        ring(d, X1, Z1, X2, Z2, ya, yb, glass)
        d.clear(X1 + 1, ya, Z1 + 1, X2 - 1, yb, Z2 - 1)
        for z in range(14, Z2 + 1):                      # solid core flanks
            for x in (X1, X2):
                d.fill(x, ya, z, x, yb, z, white)
        d.fill(X1, ya, Z2, X2, yb, Z2, white)
        for x in range(6, 13):                           # glazed stairwell
            d.fill(x, ya, Z2, x, yb, Z2, "glass_pane")
        for x in (X1, 7, 11, 15, X2):                    # mullions
            d.fill(x, ya, Z1, x, yb, Z1, col)
        for z in (Z1, 9, 14):
            d.fill(X1, ya, z, X1, yb, z, col)
            d.fill(X2, ya, z, X2, yb, z, col)
        d.fill(X1, ya, Z2, X1, yb, Z2, col)
        d.fill(X2, ya, Z2, X2, yb, Z2, col)
    for s in S:                                          # cyan accent at slab edges, street side
        for x in range(X1, X2 + 1):
            d.set(x, s, Z1, "cyan_terracotta" if x in (X1, X2) else white)
    # ---- core: corridor wall z=14, stairs on rows 16/17
    for s in S:
        d.fill(X1 + 1, s + 1, 14, X2 - 1, s + 4, 14, white)
        d.door(11, s + 1, 14, "south", "birch")
        d.set(8, s + 4, 15, endrod("down"))
        d.set(16, s + 4, 15, endrod("down"))
        d.sign(12, s + 2, 15, "south", ["", f"FLAT {S.index(s) + 1}"], "birch", glow=True, color="cyan")
    flight(d, 6, 16, 2, 6, "east", "smooth_quartz")
    for f, s in enumerate(S):
        Y = s + 1
        if f % 2 == 0:
            flight(d, 11, 17, Y, 5, "west", "smooth_quartz")
        else:
            flight(d, 7, 16, Y, 5, "east", "smooth_quartz")
    # ---- balconies (street side); the first one is the entrance canopy
    for s in S:
        for x, z in cells(5, 2, 17, 3):
            d.set(x, s, z, "smooth_quartz")
        for x in range(5, 18):
            d.set(x, s + 1, 2, "glass_pane")
        d.set(5, s + 1, 3, "glass_pane")
        d.set(17, s + 1, 3, "glass_pane")
        d.door(15, s + 1, Z1, "north", "birch")
        d.set(6, s + 1, 3, "potted_bamboo")
        d.chair(13, s + 1, 3, "east", "birch", sit=False)
        d.set(12, s + 1, 3, slab("smooth_quartz", "top"))
        for x in range(5, 18):
            d.set(x, s - 1, 3, "light_gray_concrete") if s > 7 else None
    for x in range(5, 18, 4):
        d.set(x, 6, 3, endrod("down"))
    # ---- lobby (y 2..6)
    d.fill(X1 + 1, 1, Z1 + 1, X2 - 1, 1, 13, "polished_diorite")
    for x in range(X1 + 1, X2):
        d.set(x, 6, Z1, white)                            # transom band carrying the sign
    d.double_door(10, 2, Z1, "x", "north", "birch")
    d.set(10, 4, Z1, "glass_pane")
    d.set(11, 4, Z1, "glass_pane")
    d.sign(10, 6, Z1 - 1, "north", ["SKYLINE"], "birch", glow=True, color="cyan")
    d.sign(11, 6, Z1 - 1, "north", ["RESIDENCES"], "birch", glow=True, color="cyan")
    d.fill(X1 + 1, 2, 14, X2 - 1, 6, 14, white)          # core wall with a passage to the stairs
    d.clear(7, 2, 14, 8, 4, 14)
    d.sign(9, 4, 13, "north", ["STAIRS", "<--"], "birch", glow=True, color="white")
    # café: back bar of six barrels, counter with stools, kitchen line on the core wall
    for z in range(6, 12):
        d.item(4, 2, z, "barrel", "east")
        d.set(4, 3, z, slab("smooth_quartz", "top"))
        d.set(4, 4, z, "decorated_pot[cracked=false,facing=east,waterlogged=false]" if z % 2 else
              "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]")
    for z in range(7, 11):
        d.set(6, 2, z, "quartz_block")
        d.chair(7, 2, z, "east", "birch")
    d.set(6, 3, 7, "potted_white_tulip")
    d.item(4, 2, 13, "furnace", "north")
    d.item(5, 2, 13, "smoker", "north")
    d.item(6, 2, 13, "crafting_table")
    d.set(4, 2, 12, "water_cauldron[level=3]")
    d.sign(5, 5, Z1 + 1, "south", ["CAFE"], "birch", glow=True, color="cyan")
    # concierge
    d.hut(17, 2, 6)
    for x, z in ((15, 6), (15, 7), (15, 8), (16, 8)):
        d.set(x, 2, z, "smooth_quartz")
    d.set(15, 3, 6, "potted_bamboo")
    d.chair(16, 2, 7, "east", "birch")
    d.item(18, 2, 7, "ender_chest", "west")
    d.set(18, 2, 6, "iron_block")
    d.set(18, 3, 6, "iron_block")
    seats = 5
    # lounge
    d.chair(13, 2, 12, "south", "birch")
    d.set(12, 2, 12, slab("smooth_quartz", "top"))
    d.set(14, 2, 12, "potted_bamboo")
    seats += 1
    rugc(d, 9, 8, 12, 11, 2, "cyan")
    if L >= 2:
        for x in (9, 10, 11):
            d.chair(x, 2, 11, "south", "birch")
        seats += 3
        for x in (9, 10, 11):
            d.set(x, 2, 10, slab("smooth_quartz", "top"))
    if L >= 3:
        for x in (9, 10, 11):
            d.chair(x, 2, 9, "north", "birch")
        seats += 3
    d.item(18, 2, 12, "jukebox")
    d.set(18, 2, 11, "potted_bamboo")
    d.set(18, 2, 13, "potted_bamboo")
    for x, z in ((6, 9), (10, 7), (14, 9), (10, 12), (16, 11)):
        d.set(x, 6, z, chain())
        d.set(x, 5, z, lantern())
    # ---- flats (reserved boxes, child huts)
    for s in S:
        add_child(d, G["FX"], s + 1, G["FZ"], G["FW"], 4, G["FD"], G["HUT"], FLAT)
    # ---- roof: parapet glass, penthouse growing with the level
    Y = R + 1
    PZ = {1: 12, 2: 11, 3: 9, 4: 9, 5: 8}[L]
    for x, z in cells(X1, Z1, X2, Z2):
        if x in (X1, X2) or z in (Z1, Z2):
            d.set(x, Y, z, "glass_pane")
    px1, px2 = X1 + 1, X2 - 1
    ring(d, px1, PZ, px2, Z2, Y, Y + 3, "glass_pane")
    d.fill(px1, Y, Z2, px2, Y + 3, Z2, white)
    for x, z in ((px1, PZ), (px2, PZ), (px1, Z2), (px2, Z2)):
        d.fill(x, Y, z, x, Y + 3, z, col)
    for x, z in cells(px1, PZ, px2, Z2):
        d.set(x, Y + 4, z, "smooth_quartz")
        if x in (px1, px2) or z in (PZ, Z2):
            d.set(x, Y + 5, z, white)
    for x in range(px1, px2 + 1):
        d.set(x, Y + 4, PZ, "cyan_terracotta")
    d.door(15, Y, PZ, "north", "birch")
    for x in range(7, 12):                               # railing round the stair well
        d.set(x, Y, 15, "glass_pane")
    d.set(7, Y, 16, "glass_pane")
    rugc(d, px1 + 1, PZ + 1, px2 - 1, 14, Y, "light_gray")
    bx = [6, 5, 9, 11, 13]
    nb = L
    for i in range(nb):
        x = bx[i]
        d.bed(x, Y, PZ + 1, "north", "cyan")
    if L == 1:
        nightstand(d, 5, Y, PZ + 1, "birch", endrod("up"))
    else:
        nightstand(d, 7, Y, PZ + 1, "birch", endrod("up"))
    if L >= 3:
        d.fill(8, Y, PZ + 1, 8, Y + 2, PZ + 2, glass)
    if L >= 4:
        d.fill(12, Y, PZ + 1, 12, Y + 2, PZ + 2, glass)
    if L >= 5:
        d.fill(14, Y, PZ + 1, 14, Y + 2, PZ + 2, glass)
    # lounge corner and kitchenette in the penthouse
    d.chair(17, Y, 15, "east", "birch", sit=False)
    d.chair(17, Y, 14, "east", "birch", sit=False)
    d.set(16, Y, 14, slab("smooth_quartz", "top"))
    d.set(17, Y, 13, "potted_bamboo")
    for x in range(13, 17):
        d.set(x, Y, 17, "smooth_quartz" if x != 14 else "water_cauldron[level=3]")
    d.set(17, Y, 17, "iron_block")
    d.set(17, Y + 1, 17, "iron_block")
    if L >= 4:
        d.item(17, Y, 16, chiseled("west"))
    if L >= 5:
        d.item(17, Y + 1, 16, chiseled("west"))
    for x, z in ((6, 15), (14, 15), (10, PZ + 2)):
        d.set(x, Y + 3, z, endrod("down"))
    # roof terrace
    for x in range(X1 + 1, X2):
        if x % 3 == 0:
            d.set(x, Y, Z1 + 1, "moss_block")
            d.set(x, Y + 1, Z1 + 1, "azalea")
    if PZ >= 11:
        d.chair(6, Y, PZ - 2, "south", "birch", sit=False)
        d.chair(7, Y, PZ - 2, "south", "birch", sit=False)
    if L >= 3:                                          # hot tub and loungers
        for x, z in cells(5, 5, 8, 7):
            d.set(x, Y, z, "smooth_quartz" if x in (5, 8) or z in (5, 7) else "water[level=0]")
        d.set(6, Y - 1, 6, "sea_lantern")
        for x in (12, 14, 16):
            d.chair(x, Y, 6, "south", "birch", sit=False)
    if L >= 5:                                          # pergola
        for x, z in ((11, 5), (17, 5), (11, 7), (17, 7)):
            d.set(x, Y, z, "quartz_pillar[axis=y]")
            d.set(x, Y + 1, z, "quartz_pillar[axis=y]")
            d.set(x, Y + 2, z, "quartz_pillar[axis=y]")
        for x, z in cells(11, 5, 17, 7):
            if x % 2 == 1 or x in (11, 17):
                d.set(x, Y + 3, z, slab("smooth_quartz"))
    # roof of the penthouse: solar → garden → crown
    RY = Y + 5
    if L <= 3:
        for x in range(px1 + 1, px2, 2):
            for z in range(PZ + 1, Z2 - 1, 2):
                d.set(x, RY, z, "daylight_detector[inverted=false,power=0]")
    else:
        for x, z in cells(px1 + 1, PZ + 1, px2 - 1, Z2 - 1):
            d.set(x, RY - 1, z, "moss_block" if (x + z) % 4 else "grass_block[snowy=false]")
            if (x * 3 + z) % 5 == 0:
                d.set(x, RY, z, "azalea" if x % 2 else "flowering_azalea")
        tree(d, 11, 14, RY, h=3)
    if L >= 5:
        for x, z in ((X1, Z1), (X2, Z1), (X1, Z2), (X2, Z2)):
            for yy in range(Y, Y + 8):
                d.set(x, yy, z, "sea_lantern" if yy % 2 else "white_concrete")
            d.set(x, Y + 8, z, endrod("up"))
        for yy in range(RY, RY + 6):
            d.set(11, yy, Z2 - 1, "lightning_rod[facing=up,powered=false,waterlogged=false]" if yy == RY + 5
                  else "iron_bars")
    # ---- street furniture
    planter(d, 0, 5, 1, 16, 1)
    planter(d, 21, 5, 22, 16, 1)
    for x in (2, 20):
        d.chair(x, 2, 2, "west" if x == 2 else "east", "birch", sit=False)
        d.chair(x, 2, 1, "west" if x == 2 else "east", "birch", sit=False)
    if L >= 2:
        for x in (1, 21):
            tree(d, x, 19, 2)
    for x in (7, 15):
        d.set(x, 2, 1, "sea_lantern")
        d.set(x, 3, 1, endrod("up"))
    return d



# ---------------------------------------------------------------------------------------------- Hearthwood tower
def win_hw(d, x, y, z, h=2, lintel="calcite"):
    for k in range(h):
        d.set(x, y + k, z, "glass_pane")
    d.set(x, y + h, z, lintel)


def bay_hw(d, a, storeys, top):
    """Three-storey canted-look bay window in front of the facade (z=5): box x a..a+4, z 3..4."""
    for (ya, yb) in storeys:
        fl = ya - 1
        for x, z in cells(a, 3, a + 4, 4):
            d.set(x, fl, z, "calcite" if fl > 1 else "stone_bricks")
        for y in range(ya, yb + 1):
            for x, z in cells(a, 3, a + 4, 4):
                edge = x in (a, a + 4) or z == 3
                d.set(x, y, z, "bricks" if edge else AIR)
            d.set(a, y, 3, "calcite" if y % 2 == 0 else "bricks")
            d.set(a + 4, y, 3, "calcite" if y % 2 == 0 else "bricks")
        for x in range(a + 1, a + 4):
            d.set(x, ya, 3, "calcite")
            d.set(x, ya + 1, 3, "glass_pane")
            d.set(x, ya + 2, 3, "glass_pane")
            d.set(x, yb, 3, "calcite")
        d.set(a, ya + 1, 4, "glass_pane")
        d.set(a, ya + 2, 4, "glass_pane")
        d.set(a + 4, ya + 1, 4, "glass_pane")
        d.set(a + 4, ya + 2, 4, "glass_pane")
        d.clear(a + 1, ya, 5, a + 3, ya + 2, 5)
    for x, z in cells(a, 3, a + 4, 4):
        d.set(x, top, z, "calcite")
    for x in range(a - 1, a + 6):
        d.set(x, top + 1, 2, stair("deepslate_tile", "south"))
        d.set(x, top + 1, 3, "deepslate_tiles")
        d.set(x, top + 1, 4, "deepslate_tiles")
    for x in (a - 1, a + 5):
        d.set(x, top + 1, 3, stair("deepslate_tile", "south"))
        d.set(x, top + 1, 4, stair("deepslate_tile", "south"))


def dormer_hw(d, a, y=17):
    """Gabled dormer on the north roof slope (roof row z=6 at y18): window at z=6, x=a+1."""
    for yy in range(y, y + 3):
        d.set(a, yy, 6, "bricks")
        d.set(a + 2, yy, 6, "bricks")
    d.set(a + 1, y, 6, "glass_pane")
    d.set(a + 1, y + 1, 6, "glass_pane")
    d.set(a + 1, y + 2, 6, "calcite")
    for z in (7,):
        d.set(a + 1, y + 1, z, AIR)
        d.set(a + 1, y, z, AIR) if d.get(a + 1, y, z).endswith("stairs]") or "stairs" in d.get(a + 1, y, z) else None
    for z in range(5, 9):
        d.set(a, y + 3, z, stair("deepslate_tile", "east"))
        d.set(a + 1, y + 3, z, "deepslate_tiles")
        d.set(a + 2, y + 3, z, stair("deepslate_tile", "west"))
        d.set(a + 1, y + 4, z, slab("deepslate_tile"))
    d.set(a - 1, y + 2, 5, stair("deepslate_tile", "east"))
    d.set(a + 3, y + 2, 5, stair("deepslate_tile", "west"))


def skytower_hw(rel, L):
    G = HW
    d = Design("Hearthwood", rel, (31, 30, 25), paving="grass_block[snowy=false]")
    X1, X2, Z1, Z2 = G["X1"], G["X2"], G["Z1"], G["Z2"]
    storeys = [(2, 5), (7, 10), (12, 15)]
    # ---- shell: stone plinth, red brick, stone string courses, calcite quoins
    d.fill(X1, 1, Z1, X2, 1, Z2, "stone_bricks")
    d.fill(X1 + 1, 1, Z1 + 1, X2 - 1, 1, Z2 - 1, "oak_planks")
    for (ya, yb) in storeys:
        ring(d, X1, Z1, X2, Z2, ya, yb, "bricks")
        d.clear(X1 + 1, ya, Z1 + 1, X2 - 1, yb, Z2 - 1)
    ring(d, X1, Z1, X2, Z2, 2, 2, "stone_bricks")
    for s in G["SLABS"] + (G["ROOF"],):
        d.fill(X1 + 1, s, Z1 + 1, X2 - 1, s, Z2 - 1, "spruce_planks")
        ring(d, X1, Z1, X2, Z2, s, s, "stone_bricks" if s != G["ROOF"] else "bricks")
    for x, z in ((X1, Z1), (X2, Z1), (X1, Z2), (X2, Z2)):
        for y in range(2, 16):
            if y % 2 == 0:
                d.set(x, y, z, "calcite")
    # hall walls (plastered) on every storey
    for (ya, yb) in storeys:
        d.fill(13, ya, Z1 + 1, 13, yb, Z2 - 1, "calcite")
        d.fill(17, ya, Z1 + 1, 17, yb, Z2 - 1, "calcite")
    # ---- roof: steep tiled gable along the street, brick gable ends, end chimneys
    ridge = d.gable(X1, Z1, X2, Z2, 17, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "bricks")
    for x in (0, 30):
        for z in (10, 11, 12):
            for y in range(1, ridge + 2):
                d.set(x, y, z, "bricks")
        d.set(x, ridge + 2, 11, "bricks")
        for z in (10, 12):
            d.set(x, ridge + 2, z, "flower_pot")
    for x in (13, 17):                                   # party-wall stacks on the ridge
        for y in range(G["ROOF"] + 1, ridge + 3):
            for z in (11, 12):
                d.set(x, y, z, "bricks")
        d.set(x, ridge + 3, 11, "flower_pot")
        d.set(x, ridge + 3, 12, "flower_pot")
    # ---- bay windows (each flat and both ground-floor rooms), sash windows elsewhere
    for a in (3, 19):
        bay_hw(d, a, storeys, 16)
    for (ya, yb) in storeys:
        for x in (9, 11, 25, 27):
            win_hw(d, x, ya + 1, Z1)
        for x in (3, 10, 19, 26):
            win_hw(d, x, ya + 1, Z2)
        for z in (7, 14):
            win_hw(d, X1, ya + 1, z)
            win_hw(d, X2, ya + 1, z)
        if ya > 2:
            for x in (14, 15, 16):
                win_hw(d, x, ya + 1, Z1)
    # ---- stair hall
    for x, z in cells(14, 6, 16, 16):
        d.set(x, 1, z, "polished_blackstone" if (x + z) % 2 else "calcite")
    flight(d, 14, 11, 2, 5, "south", "dark_oak")
    flight(d, 16, 15, 7, 5, "north", "dark_oak")
    flight(d, 14, 15, 12, 5, "north", "dark_oak")
    n = 0
    for z, h in ((12, 1), (13, 2), (14, 3)):           # residents' lockers under the stairs
        for k in range(h):
            d.item(14, 2 + k, z, "barrel", "east")
            n += 1
    d.door(15, 2, Z1, "north", "dark_oak")
    d.set(15, 4, Z1, "glass_pane")
    d.door(13, 2, 8, "west", "dark_oak")
    d.door(17, 2, 8, "east", "dark_oak", "right")
    for s in G["SLABS"]:
        d.door(13, s + 1, 10, "west", "dark_oak")
        d.door(17, s + 1, 10, "east", "dark_oak", "right")
        d.set(15, s + 4, 12, lantern())
        d.set(15, s + 1, 6, "potted_fern")
        d.sign(15, s + 3, 6, "south", ["", f"Flats {1 + 2 * G['SLABS'].index(s)} & {2 + 2 * G['SLABS'].index(s)}"],
               "dark_oak")
    d.set(16, 2, 6, slab("dark_oak", "top"))
    d.set(16, 3, 6, "potted_red_tulip")
    d.set(15, 5, 9, lantern())
    d.set(15, 5, 14, lantern())
    # ---- residents' parlour (west): fireplace, sofa, card tables, gramophone
    d.set(1, 2, 11, "campfire[facing=east,lit=true,signal_fire=false,waterlogged=false]")
    d.set(1, 3, 11, "bricks")
    for z in (10, 11, 12):
        d.set(2, 4, z, slab("dark_oak", "top"))
    d.candle(2, 5, 10, 2)
    d.candle(2, 5, 12, 2)
    d.set(2, 2, 10, "bricks")
    d.set(2, 3, 10, "bricks")
    d.set(2, 2, 12, "bricks")
    d.set(2, 3, 12, "bricks")
    rugc(d, 3, 10, 3, 12, 2, "red")
    seats = 0
    for z in (10, 11, 12):
        d.chair(4, 2, z, "east", "dark_oak")
        seats += 1
    d.chair(3, 2, 9, "north", "dark_oak")
    d.chair(3, 2, 13, "south", "dark_oak")
    seats += 2
    d.item(12, 2, 16, "jukebox")
    d.set(11, 2, 16, slab("dark_oak", "top"))
    d.set(11, 3, 16, "potted_azure_bluet")
    if L >= 2:
        d.table(8, 2, 8, "dark_oak")
        d.chair(8, 2, 7, "north", "dark_oak")
        d.chair(8, 2, 9, "south", "dark_oak")
        d.chair(7, 2, 8, "west", "dark_oak")
        seats += 3
    if L >= 3:
        d.table(8, 2, 13, "dark_oak")
        d.chair(8, 2, 12, "north", "dark_oak")
        d.chair(8, 2, 14, "south", "dark_oak")
        d.chair(9, 2, 13, "east", "dark_oak")
        seats += 3
    d.bookshelf(2, 2, 16) if False else None
    for x in (3, 4):
        d.set(x, 2, 16, "bookshelf")
        d.set(x, 3, 16, "bookshelf")
    if L >= 4:
        d.item(6, 2, 16, chiseled("north"))
    if L >= 5:
        d.item(7, 2, 16, chiseled("north"))
    d.set(5, 2, 4, "potted_red_tulip")
    d.chair(4, 2, 4, "east", "oak", sit=False)
    d.chair(6, 2, 4, "west", "oak", sit=False)
    for x, z in ((5, 11), (9, 8), (9, 13)):
        d.set(x, 5, z, lantern())
    # ---- porter's lodge (east): desk, parcels, kitchen, bedroom
    d.hut(18, 2, 6)
    d.set(19, 2, 6, slab("dark_oak", "top"))
    d.item(20, 2, 6, "ender_chest", "south")
    d.chair(19, 2, 7, "south", "dark_oak")
    seats += 1
    for z, k in ((9, "furnace"), (10, "smoker"), (11, "sink"), (12, "crafting_table")):
        if k == "sink":
            d.set(28, 2, z, "water_cauldron[level=3]")
        else:
            d.item(28, 2, z, k, "west" if k != "crafting_table" else None)
        d.set(28, 4, z, slab("dark_oak", "top"))
    d.table(24, 2, 10, "dark_oak")
    d.chair(23, 2, 10, "west", "dark_oak")
    d.chair(25, 2, 10, "east", "dark_oak")
    seats += 2
    d.fill(18, 2, 13, 28, 5, 13, "calcite")
    d.door(21, 2, 13, "south", "dark_oak")
    d.bed(19, 2, 16, "south", "red")
    if L >= 2:
        d.bed(20, 2, 16, "south", "red")
        nightstand(d, 21, 2, 16, "dark_oak")
    nightstand(d, 18, 2, 16, "dark_oak")
    wardrobe(d, 28, 2, 15, "west", "dark_oak_planks")
    rugc(d, 19, 14, 22, 14, 2, "orange")
    d.set(21, 2, 4, "potted_fern")
    d.chair(20, 2, 4, "east", "oak", sit=False)
    for x, z in ((22, 8), (25, 11), (23, 15)):
        d.set(x, 5, z, lantern())
    # ---- flats
    for s in G["SLABS"]:
        for fx in G["FXS"]:
            add_child(d, fx, s + 1, G["FZ"], G["FW"], 4, G["FD"], G["HUT"], FLAT)
    # ---- attic: plastered partitions, garrets under dormers (L3+), box room before
    def roof_y(z):
        return 17 + min(z - 4, 18 - z) - 1
    for x in (13, 17):
        for z in range(Z1 + 1, Z2):
            for y in range(17, roof_y(z)):
                if d.air(x, y, z):
                    d.set(x, y, z, "calcite")
        d.door(x, 17, 9, "west" if x == 13 else "east", "dark_oak")
    d.set(15, 21, 11, lantern())
    nb = max(0, L - 2)
    if L >= 3:
        for a in (5, 9, 19, 23):
            dormer_hw(d, a)
    garrets = [5, 19, 9]
    for i, a in enumerate(garrets):
        if i < nb:
            d.bed(a + 1, 17, 7, "north", "red")
            d.set(a + 2, 17, 7, slab("oak", "top"))
            d.candle(a + 2, 18, 7, 1)
            d.set(a + 1, 17, 10, "chest[facing=north,type=single,waterlogged=false]")
            d.set(a + 1, 20, 9, lantern())
        else:
            d.keg(a + 1, 17, 9, "north")
            d.set(a + 2, 17, 9, "chest[facing=north,type=single,waterlogged=false]")
    # ---- front: portico, steps, railings and gardens
    for x in (13, 17):
        for y in (2, 3, 4):
            d.set(x, y, 2, "stone_brick_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
    for x, z in cells(13, 2, 17, 4):
        d.set(x, 5, z, "smooth_stone")
        d.set(x, 1, z, "stone_bricks")
        if x in (13, 17) or z == 2:
            d.set(x, 6, z, "stone_brick_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
    d.sign(15, 5, 1, "north", ["ALBION", "MANSIONS", "est. 1905"], "dark_oak")
    d.set(15, 4, 3, lantern())
    for x, z in cells(14, 0, 16, 1):
        d.set(x, 1, z, "gravel")
    if L >= 2:
        for x in range(0, 31):
            if x not in (14, 15, 16):
                d.set(x, 2, 1, "iron_bars")
        d.set(13, 2, 1, "bricks")
        d.set(17, 2, 1, "bricks")
        d.set(13, 3, 1, lantern(False))
        d.set(17, 3, 1, lantern(False))
        for x in range(8, 13):
            d.set(x, 2, 3, ("poppy", "allium", "oxeye_daisy")[x % 3])
        for x in range(24, 29):
            d.set(x, 2, 3, ("cornflower", "poppy", "azure_bluet")[x % 3])
    if L >= 3:
        for x in (1, 29):
            d.set(x, 2, 0, "stone_bricks")
            d.set(x, 3, 0, "dark_oak_fence")
            d.set(x, 4, 0, lantern(False))
    # ---- rear garden (L4+), roof lantern (L5)
    if L >= 4:
        for x, z in cells(0, 18, 30, 24):
            if x in (0, 30) or z == 24:
                d.set(x, 2, z, "oak_leaves[distance=1,persistent=true,waterlogged=false]")
        d.door(15, 2, Z2, "south", "dark_oak")
        for z in range(18, 23):
            d.set(15, 1, z, "gravel")
        for x in (6, 24):
            for z in (19, 22):
                d.chair(x, 2, z, "west" if x == 6 else "east", "dark_oak", sit=False)
            d.table(x + (1 if x == 6 else -1), 2, 20, "dark_oak")
        for x in range(2, 29, 3):
            if abs(x - 15) > 1:
                d.set(x, 2, 23, ("poppy", "allium", "cornflower")[x % 3])
                d.set(x, 2, 22, ("oxeye_daisy", "azure_bluet", "dandelion")[x % 3])
        d.set(15, 2, 21, "stone_brick_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
        d.set(15, 3, 21, "lantern[hanging=false,waterlogged=false]")
    if L >= 5:
        cy = ridge
        for x, z in cells(14, 10, 16, 12):
            d.set(x, cy, z, "calcite")
        for y in range(cy + 1, cy + 3):
            for x, z in cells(14, 10, 16, 12):
                if x in (14, 16) and z in (10, 12):
                    d.set(x, y, z, "dark_oak_log[axis=y]")
                elif x in (14, 16) or z in (10, 12):
                    d.set(x, y, z, "glass_pane")
                else:
                    d.set(x, y, z, AIR)
        d.set(15, cy + 2, 11, lantern())
        for x, z in cells(13, 9, 17, 13):
            d.set(x, cy + 3, z, "weathered_cut_copper_slab[type=bottom,waterlogged=false]")
        for x, z in cells(14, 10, 16, 12):
            d.set(x, cy + 3, z, "weathered_cut_copper")
        d.set(15, cy + 4, 11, "weathered_cut_copper")
        d.set(15, cy + 5, 11, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    return d


# ---------------------------------------------------------------------------------------------- Cascadia tower
def stone(x, y, z):
    v = (x * 7 + y * 13 + z * 5) % 9
    return "mossy_cobblestone" if v == 0 else ("andesite" if v in (3, 6) else "cobblestone")


def win_ca(d, x, y, z, out, h=2, w=1):
    sx, sz = D4[CW[out]]
    for i in range(w):
        for k in range(h):
            d.set(x + sx * i, y + k, z + sz * i, "glass_pane")
    ox, oz = D4[out]
    for (cx, cz), side in (((x - sx + ox, z - sz + oz), OPP[CW[out]]), ((x + sx * w + ox, z + sz * w + oz), CW[out])):
        for k in range(h):
            if d.bp.inside(cx, y + k, cz) and d.air(cx, y + k, cz):
                d.set(cx, y + k, cz, trap("spruce", side, "bottom", True))


def skytower_ca(rel, L):
    G = CA
    d = Design("Cascadia", rel, (29, 34, 31), paving="coarse_dirt")
    X1, X2, Z1, Z2 = G["X1"], G["X2"], G["Z1"], G["Z2"]
    S = G["SLABS"]
    for x, z in cells(0, 0, 28, 30):
        if not (10 <= x <= 18 and z <= 3):
            d.set(x, 1, z, "grass_block[snowy=false]" if (x * 3 + z * 7) % 5 else "moss_block")
    # ---- river-rock ground storey
    for x, z in cells(X1, Z1, X2, Z2):
        d.set(x, 1, z, stone(x, 1, z) if x in (X1, X2) or z in (Z1, Z2) else "spruce_planks")
    for y in range(2, 6):
        for x, z in cells(X1, Z1, X2, Z2):
            if x in (X1, X2) or z in (Z1, Z2):
                d.set(x, y, z, stone(x, y, z))
    # ---- log storeys
    for s in S + (G["ROOF"],):
        d.fill(X1 + 1, s, Z1 + 1, X2 - 1, s, Z2 - 1, "spruce_planks")
        for x in range(X1, X2 + 1):
            d.set(x, s, Z1, "dark_oak_planks")
            d.set(x, s, Z2, "dark_oak_planks")
        for z in range(Z1, Z2 + 1):
            d.set(X1, s, z, "dark_oak_planks")
            d.set(X2, s, z, "dark_oak_planks")
    for s in S:
        for y in range(s + 1, s + 5):
            for x in range(X1, X2 + 1):
                d.set(x, y, Z1, log("stripped_spruce_log", "x"))
                d.set(x, y, Z2, log("stripped_spruce_log", "x"))
            for z in range(Z1, Z2 + 1):
                d.set(X1, y, z, log("stripped_spruce_log", "z"))
                d.set(X2, y, z, log("stripped_spruce_log", "z"))
            for x, z in ((X1, Z1), (X2, Z1), (X1, Z2), (X2, Z2), (X1, 15), (X2, 15)):
                d.set(x, y, z, log("spruce_log", "y"))
            d.fill(X1 + 1, y, 15, X2 - 1, y, 15, "spruce_planks")
    # ---- roof: steep dark gable, gable to the street; catslide over the west gallery
    ridge = d.gable(X1, Z1, X2, Z2, 17, "z", "dark_oak_stairs", "dark_oak_slab", "spruce_planks")
    for z in (Z1, Z2):                                  # gable trusses
        for y in range(17, ridge):
            if d.get(14, y, z) == "minecraft:spruce_planks":
                d.set(14, y, z, log("stripped_spruce_log", "y"))
        for x in range(X1 + 1, X2):
            if d.get(x, 17, z) == "minecraft:spruce_planks":
                d.set(x, 17, z, log("stripped_spruce_log", "x"))
    for x, y in ((12, 18), (13, 18), (14, 18), (15, 18), (16, 18), (13, 19), (14, 19), (15, 19), (14, 20), (13, 20),
                 (15, 20)):
        d.set(x, y, Z1, "glass_pane")
    # ---- gallery (west): decks, posts, railings, outside stairs
    for s in S:
        for x, z in cells(5, Z1, 7, Z2):
            d.set(x, s, z, "dark_oak_planks")
        for z in range(Z1, Z2 + 1):
            d.set(4, s + 1, z, fence("dark_oak"))
            d.set(4, s, z, "dark_oak_planks")
    for z in (Z1, 9, 15, 21, Z2):
        for y in range(2, 13):
            d.set(4, y, z, log("spruce_log", "y"))
    flight(d, 5, 9, 2, 5, "south", "spruce")
    flight(d, 5, 20, 7, 5, "north", "spruce")
    for z in range(Z1 - 1, Z2 + 2):
        for x, y in ((3, 12), (4, 13), (5, 14), (6, 15), (7, 16)):
            d.set(x, y, z, stair("dark_oak", "east"))
    for s in S:
        for fz in G["FZS"]:
            d.door(X1, s + 1, fz + 5, "west", "spruce")
            d.door(X2, s + 1, fz + 4, "east", "spruce", "right")
            d.set(7, s + 3, fz + 3, lantern(False)) if False else None
            d.set(6, s + 4, fz + 3, lantern())
            d.sign(X1 - 1, s + 3, fz + 4, "west", ["", f"No. {(fz > 10) + 1 + 2 * S.index(s)}"], "spruce")
    # windows
    for s in S:
        Y = s + 2
        for fz in G["FZS"]:
            win_ca(d, X1, Y, fz + 1, "west")
            win_ca(d, X1, Y, fz + 8, "west")
            win_ca(d, X2, Y, fz + 1, "east", 2, 2)
            win_ca(d, X2, Y, fz + 6, "east", 2, 2)
        win_ca(d, 10, Y, Z1, "north", 2, 3)
        win_ca(d, 16, Y, Z1, "north", 2, 3)
        win_ca(d, 10, Y, Z2, "south", 2, 3)
        win_ca(d, 16, Y, Z2, "south", 2, 3)
    for x in (10, 18):
        win_ca(d, x, 3, Z1, "north")
    for z in (7, 11, 19, 23):
        win_ca(d, X1, 3, z, "west")
        win_ca(d, X2, 3, z, "east")
    # ---- east balconies on log brackets
    for fz in G["FZS"]:
        for s in S:
            for x, z in cells(21, fz + 1, 23, fz + 7):
                d.set(x, s, z, "dark_oak_planks")
                if x == 23 or z in (fz + 1, fz + 7):
                    d.set(x, s + 1, z, fence("dark_oak"))
            d.chair(22, s + 1, fz + 2, "south", "spruce", sit=False)
            d.set(22, s + 1, fz + 3, slab("spruce", "top"))
            d.set(22, s + 2, fz + 3, "potted_fern")
            d.chair(22, s + 1, fz + 6, "east", "spruce", sit=False)
        for z in (fz + 1, fz + 7):
            for y in range(2, 16):
                d.set(23, y, z, log("spruce_log", "y"))
        for x, z in cells(21, fz, 24, fz + 8):
            d.set(x, 16, z, slab("dark_oak"))
    # ---- ground floor: reception, keeper's bunks, kitchen, great room with stone fireplace
    d.fill(X1 + 1, 2, 15, X2 - 1, 5, 15, "spruce_planks")
    d.clear(13, 2, 15, 15, 4, 15)
    d.fill(12, 2, Z1 + 1, 12, 5, 14, "spruce_planks")
    d.fill(16, 2, Z1 + 1, 16, 5, 14, "spruce_planks")
    d.door(12, 2, 12, "west", "spruce")
    d.door(16, 2, 12, "east", "spruce", "right")
    d.door(14, 2, Z1, "north", "spruce")
    d.set(14, 4, Z1, "glass_pane")
    d.hut(13, 2, 6)
    d.set(13, 2, 7, slab("spruce", "top"))
    d.set(13, 3, 7, "lantern[hanging=false,waterlogged=false]")
    d.item(13, 2, 8, "ender_chest", "east")
    d.chair(15, 2, 9, "east", "spruce", sit=False)
    d.chair(15, 2, 10, "east", "spruce", sit=False)
    d.set(14, 5, 8, lantern())
    d.set(14, 5, 12, lantern())
    rugc(d, 14, 6, 14, 14, 2, "green")
    for i in range(L):                                   # keeper's bunk room
        d.bed(9, 2, 6 + i, "west", "brown")
    d.set(11, 2, 6, "chest[facing=west,type=single,waterlogged=false]")
    d.set(9, 2, 13, "chest[facing=east,type=single,waterlogged=false]")
    d.set(9, 2, 14, "potted_fern")
    d.set(10, 5, 9, lantern())
    for z, k in ((6, "furnace"), (7, "smoker"), (8, "crafting_table"), (9, "sink")):
        if k == "sink":
            d.set(19, 2, z, "water_cauldron[level=3]")
        else:
            d.item(19, 2, z, k, "west" if k != "crafting_table" else None)
        d.set(19, 4, z, slab("spruce", "top"))
    for z in (11, 12, 13):
        d.item(19, 2, z, "barrel", "west")
        d.item(19, 3, z, "barrel", "west")
    d.set(17, 2, 6, slab("spruce", "top"))
    d.set(17, 3, 6, "potted_fern")
    d.set(18, 5, 9, lantern())
    # great room
    d.set(14, 2, Z2, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for x in (13, 15):
        d.set(x, 2, Z2, "cobblestone")
        d.set(x, 3, Z2, "cobblestone")
    d.set(14, 3, Z2, "cobblestone")
    for x in (13, 14, 15):
        d.set(x, 1, 25, "cobblestone")
        d.set(x, 4, 25, slab("spruce", "top"))
    for x in range(12, 17):
        for y in range(1, 21):
            d.set(x, y, Z2 + 1, stone(x, y, Z2 + 1))
    for x in range(13, 16):
        for y in range(21, ridge + 2):
            d.set(x, y, Z2 + 1, stone(x, y, Z2 + 1))
    d.set(14, ridge + 2, Z2 + 1, stone(14, ridge + 2, Z2 + 1))
    d.set(14, ridge + 3, Z2 + 1, "cobblestone_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
    rugc(d, 12, 23, 16, 24, 2, "brown")
    for x in range(12, 17):
        d.chair(x, 2, 22, "north", "spruce")
    seats = 5
    d.chair(17, 2, 23, "east", "dark_oak")
    seats += 1
    d.item(9, 2, 25, "jukebox")
    d.set(10, 2, 25, "barrel[facing=up,open=false]")
    d.set(10, 3, 25, "potted_fern")
    if L >= 2:
        d.table(10, 2, 18, "spruce")
        d.chair(10, 2, 17, "north", "spruce")
        d.chair(10, 2, 19, "south", "spruce")
        d.chair(11, 2, 18, "east", "spruce")
        seats += 3
    if L >= 3:
        d.table(18, 2, 18, "spruce")
        d.chair(18, 2, 17, "north", "spruce")
        d.chair(18, 2, 19, "south", "spruce")
        d.chair(17, 2, 18, "west", "spruce")
        seats += 3
    if L >= 4:
        d.item(9, 2, 21, chiseled("east"))
    if L >= 5:
        d.item(9, 2, 22, chiseled("east"))
    for x, z in ((11, 21), (17, 21), (14, 18)):
        d.set(x, 5, z, lantern())
    # ---- flats
    for s in S:
        for fz in G["FZS"]:
            add_child(d, G["FX"], s + 1, fz, G["FW"], 4, G["FD"], G["HUT"], FLAT)
    # ---- outside: lanterns, firewood, porch (L2), hot tub (L3), woodshed (L4), lookout (L5)
    d.set(13, 4, Z1 - 1, "wall_torch[facing=north]") if False else None
    d.sign(14, 5, Z1 - 1, "north", ["RIDGEBACK", "LODGE"], "spruce")
    for x in (12, 16):
        d.set(x, 2, Z1 - 1, "barrel[facing=up,open=false]")
        d.set(x, 3, Z1 - 1, lantern(False))
    if L >= 2:
        for x, z in cells(10, 0, 18, 3):
            d.set(x, 1, z, "spruce_planks")
        for x in (10, 14, 18):
            if x != 14:
                for y in range(2, 6):
                    d.set(x, y, 0, log("spruce_log", "y"))
        for x in range(9, 20):
            for z in (1, 2, 3):
                d.set(x, 6, z, slab("dark_oak"))
            d.set(x, 5, 0, stair("dark_oak", "south"))
        d.set(11, 2, 1, stair("spruce", "south"))
        d.chair(11, 2, 2, "west", "spruce", sit=False)
        d.chair(17, 2, 2, "east", "spruce", sit=False)
        d.set(13, 5, 2, lantern())
        d.set(15, 5, 2, lantern())
    if L >= 3:
        for x, z in cells(22, 13, 27, 18):
            d.set(x, 1, z, "spruce_planks")
            if x in (22, 27) or z in (13, 18):
                if not (x == 22 and z in (14, 15)):
                    d.set(x, 2, z, fence("spruce"))
        for x, z in cells(24, 14, 26, 16):
            d.set(x, 1, z, "water[level=0]" if (x, z) != (25, 15) else "water[level=0]")
        for x, z in cells(23, 14, 27, 17):
            if not (24 <= x <= 26 and 14 <= z <= 16) and d.air(x, 2, z):
                pass
        d.set(25, 0, 15, "sea_lantern")
        d.chair(23, 2, 17, "west", "spruce", sit=False)
        d.chair(26, 2, 17, "east", "spruce", sit=False)
        d.set(27, 3, 13, lantern(False))
    if L >= 4:
        for x, z in cells(17, 28, 23, 30):
            d.set(x, 1, z, "spruce_planks")
        for x in (17, 23):
            for y in range(2, 6):
                d.set(x, y, 30, log("spruce_log", "y"))
                d.set(x, y, 28, log("spruce_log", "y"))
        for x in range(16, 25):
            d.set(x, 6, 28, stair("dark_oak", "south") if False else slab("dark_oak", "top"))
            d.set(x, 6, 29, slab("dark_oak", "top"))
            d.set(x, 6, 30, slab("dark_oak", "top"))
        for x in range(18, 23):
            for y in range(2, 5):
                d.set(x, y, 30, log("spruce_log", "x") if (x + y) % 3 else log("stripped_spruce_log", "x"))
        d.set(18, 2, 29, "chipped_anvil[facing=north]") if False else None
        d.set(20, 2, 28, "spruce_log[axis=y]")
        d.set(21, 2, 29, "spruce_log[axis=y]")
    if L >= 5:
        cy = ridge
        for x, z in cells(13, 13, 15, 17):
            d.set(x, cy, z, "spruce_planks")
        for y in range(cy + 1, cy + 3):
            for x, z in cells(13, 13, 15, 17):
                if x in (13, 15) and z in (13, 17):
                    d.set(x, y, z, log("stripped_spruce_log", "y"))
                elif x in (13, 15) or z in (13, 17):
                    d.set(x, y, z, "glass_pane")
                else:
                    d.set(x, y, z, AIR)
        for z in range(12, 19):
            d.set(12, cy + 3, z, stair("dark_oak", "east"))
            d.set(13, cy + 3, z, stair("dark_oak", "east"))
            d.set(14, cy + 3, z, "dark_oak_planks")
            d.set(15, cy + 3, z, stair("dark_oak", "west"))
            d.set(16, cy + 3, z, stair("dark_oak", "west"))
            d.set(14, cy + 4, z, slab("dark_oak"))
        d.set(14, cy + 2, 15, lantern())
        for y in range(cy + 5, cy + 8):
            d.set(14, y, 15, "spruce_fence")
        d.set(14, cy + 6, 16, "green_wall_banner[facing=south]")
    return d


@design("skytower")
def skytower(pack, rel, L):
    return {"Neoterra": skytower_nt, "Hearthwood": skytower_hw, "Cascadia": skytower_ca}[pack](rel, L)
