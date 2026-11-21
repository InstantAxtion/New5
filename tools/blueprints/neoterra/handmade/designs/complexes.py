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
    """Neoterra flat, 15 x 9: main bedroom (NW), kids' room / study (SW), open-plan living room with kitchen run,
    island, dining table and a sofa group facing the balcony (east). Corridor door at x7 on the south wall,
    balcony door at x11 on the north glass."""
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
    for x, z in cells(6, 3, 14, 8):                      # kitchen / dining zone floored in pale stone
        d.set(x, 0, z, "smooth_stone")
    # ---- main bedroom: bed head against the window wall, dresser, wardrobe, reading chair
    d.bed(1, y, 0, "north", "cyan")
    if L >= 2:
        d.bed(2, y, 0, "north", "cyan")
        nightstand(d, 3, y, 0, "birch", endrod("up"))
    else:
        d.set(2, y, 0, "potted_bamboo")
    nightstand(d, 0, y, 0, "birch", endrod("up"))
    wardrobe(d, 4, y, 0, "south", "white_concrete")
    d.set(4, y, 1, "white_concrete")
    d.set(4, y + 1, 1, "white_concrete")
    d.set(0, y, 3, slab("birch", "top"))                 # dresser with a mirror-glass above
    d.set(0, y + 1, 3, "potted_white_tulip")
    d.set(0, y + 2, 3, "light_gray_stained_glass_pane")
    d.chair(0, y, 2, "west", "birch", sit=False)         # reading chair by the side glass
    rugc(d, 1, 2, 2, 3, y, "light_gray" if L < 3 else "cyan")
    d.set(2, 4, 2, endrod("down"))
    # ---- kids' room (L3+) / study (L1-2)
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
        d.set(4, y, 8, "barrel[facing=up,open=false]")   # toy / file box
        d.set(3, y, 8, "potted_bamboo")
    if nk == 0:                                          # study: second desk, shelving and a lounge chair
        d.set(0, y, 5, slab("birch", "top"))
        d.set(0, y + 1, 5, "potted_azure_bluet")
        d.set(0, y, 6, "chiseled_bookshelf[facing=east,slot_0_occupied=true,slot_1_occupied=false,"
                       "slot_2_occupied=true,slot_3_occupied=true,slot_4_occupied=false,slot_5_occupied=true]")
        rugc(d, 2, 6, 3, 7, y, "gray")
        d.chair(3, y, 6, "north", "birch", sit=False)
    elif nk < 3:
        d.set(0, y, 7, "chest[facing=east,type=single,waterlogged=false]")
    d.set(4, y, 5, "white_concrete" if nk < 3 else "chest[facing=west,type=single,waterlogged=false]")
    d.set(4, y + 1, 5, "white_concrete" if nk < 3 else "potted_dandelion")
    rugc(d, 2, 6, 3, 7, y, ("lime", "yellow", "light_blue")[L % 3])
    d.set(2, 4, 6, endrod("down"))
    # ---- kitchen run on the back wall, upper cabinets above
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
    d.set(10, y + 3, 8, "light_gray_concrete")           # extractor hood
    d.hut(*G["HUT"])
    d.set(6, y + 1, 8, endrod("up"))
    d.set(8, y, 8, slab("birch", "top"))                 # hall console by the front door
    d.set(8, y + 1, 8, "potted_white_tulip")
    for x in (9, 10, 11):                                # island with stools
        d.set(x, y, 6, "smooth_quartz")
    d.set(11, y + 1, 6, "potted_white_tulip")
    d.set(9, y + 1, 6, "decorated_pot[cracked=false,facing=north,waterlogged=false]")
    d.chair(9, y, 5, "north", "smooth_quartz")
    d.chair(10, y, 5, "north", "smooth_quartz")
    # dining table by the east glass
    d.set(13, y, 5, slab("birch", "top"))
    d.set(13, y + 1, 5, "candle[candles=3,lit=false,waterlogged=false]")
    d.chair(12, y, 5, "west", "birch")
    d.chair(14, y, 5, "east", "birch")
    if L >= 2:
        d.set(13, y, 4, slab("birch", "top"))
        d.set(13, y + 1, 4, "potted_azure_bluet")
        d.chair(12, y, 4, "west", "birch")
        d.chair(14, y, 4, "east", "birch")
    # ---- lounge: sofa facing the balcony view, coffee table, armchair, media shelf
    rugc(d, 7, 0, 10, 1, y, ("light_gray", "cyan", "white", "gray", "light_blue")[L - 1])
    n_sofa = 2 if L < 2 else 3
    for x in range(8, 8 + n_sofa):
        d.chair(x, y, 2, "south", "birch", sit=False)
    d.set(7, y, 2, trap("birch", "west", "bottom", True))
    d.set(8 + n_sofa, y, 2, trap("birch", "east", "bottom", True))
    d.set(9, y, 1, slab("smooth_quartz", "top"))
    d.set(9, y + 1, 1, "potted_azure_bluet")
    d.chair(7, y, 0, "west", "birch", sit=False)         # armchair by the media wall
    d.set(6, y, 0, "potted_bamboo")
    d.set(6, y, 1, slab("birch", "top"))                 # media shelf on the bedroom wall
    d.set(6, y + 1, 1, "note_block[instrument=harp,note=0,powered=false]")
    d.set(6, y, 2, endrod("up"))
    if L >= 3:
        d.set(6, y + 2, 1, "black_stained_glass_pane")   # wall screen
    if L >= 4:
        d.item(14, y, 0, "jukebox")
    else:
        d.set(14, y, 0, "smooth_quartz")
    d.set(14, y + 1, 0, "potted_cactus")
    d.set(14, y, 1, slab("birch", "top"))
    d.set(14, y + 1, 1, "lantern[hanging=false,waterlogged=false]")
    d.set(14, y, 2, "potted_bamboo")
    if L >= 5:
        d.item(12, y, 0, "ender_chest", "south")
    else:
        d.set(12, y, 0, "potted_white_tulip")
    for x, z in ((9, 3), (11, 7), (13, 2), (13, 5), (8, 6)):
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
    # round 5: parlour settee + bookcases, kitchen dresser, bedroom dressing table, children's desk
    d.set(4, y, 1, "bookshelf")
    d.set(4, y + 1, 1, "bookshelf")
    d.set(4, y, 2, "bookshelf")
    d.set(4, y + 1, 2, "potted_fern")
    d.set(2, y, 2, slab("dark_oak", "top"))              # tea table on the rug
    d.set(2, y + 1, 2, "flower_pot")
    d.chair(2, y, 3, "south", "dark_oak", sit=False)
    d.chair(3, y, 3, "south", "dark_oak", sit=False)
    if L < 2:
        d.chair(0, y, 1, "west", "dark_oak", sit=False)
    d.set(6, y, 3, "potted_fern")
    d.set(6, y, 6, slab("dark_oak", "top"))              # dressing table
    d.set(6, y + 1, 6, "potted_allium")
    d.set(6, y + 2, 6, "glass_pane")
    d.chair(6, y, 7, "west", "dark_oak", sit=False)
    d.set(10, y, 10, "potted_red_tulip")
    d.set(3, y, 6, "chest[facing=south,type=single,waterlogged=false]")   # toy chest
    rugc(d, 2, 7, 3, 8, y, ("light_blue", "lime", "yellow", "pink", "purple")[L - 1])
    if nk < 2:
        d.set(1, y, 9, slab("oak", "top"))
        d.set(1, y + 1, 9, "potted_dandelion")
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
    # round 5: bedroom chair and chest, bunk-room desk, great-room fireside bench and wood store
    d.chair(4, y, 2, "east", "spruce", sit=False)
    d.set(0, y, 3, "chest[facing=east,type=single,waterlogged=false]")
    d.set(4, y, 7, "chest[facing=west,type=single,waterlogged=false]")
    d.set(3, y, 9, slab("spruce", "top"))
    d.set(3, y + 1, 9, lantern(False))
    rugc(d, 2, 7, 3, 8, y, ("green", "orange", "light_gray", "brown", "red")[L - 1])
    d.chair(10, y, 2, "east", "spruce", sit=False)
    d.chair(10, y, 3, "east", "spruce", sit=False)
    d.set(10, y, 4, slab("spruce", "top"))
    d.set(10, y + 1, 4, "potted_fern")
    d.set(6, y, 4, log("spruce_log", "x"))               # firewood box
    d.set(6, y + 1, 4, log("spruce_log", "x"))
    d.set(10, y, 6, "potted_spruce_sapling")
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
    # each landing has its own corner (east end of the stair hall, x13-18): bench / parcel lockers / book swap /
    # planter seat; and its own doormat colour
    for f, s in enumerate(S):
        Y = s + 1
        rugc(d, 11, 15, 12, 15, Y, ("light_blue", "gray", "lime", "orange")[f])
        if f == 0:
            d.chair(15, Y, 17, "south", "birch", sit=False)
            d.chair(16, Y, 17, "south", "birch", sit=False)
            d.set(17, Y, 17, "potted_bamboo")
            d.set(18, Y, 17, slab("birch", "top"))
            d.set(18, Y + 1, 17, "potted_white_tulip")
            d.set(18, Y, 15, "potted_bamboo")
        elif f == 1:
            for z in (15, 16, 17):
                d.set(18, Y, z, "barrel[facing=west,open=false]")
                d.set(18, Y + 1, z, "barrel[facing=west,open=false]")
            d.set(14, Y, 17, "potted_cactus")
            d.set(17, Y + 2, 16, endrod("west"))
        elif f == 2:
            d.set(18, Y, 16, "bookshelf")
            d.set(18, Y + 1, 16, "bookshelf")
            d.set(18, Y, 17, "bookshelf")
            d.set(18, Y + 1, 17, "potted_fern")
            d.chair(17, Y, 15, "east", "birch", sit=False)
            d.chair(16, Y, 17, "south", "birch", sit=False)
            d.set(17, Y, 17, slab("birch", "top"))
            d.set(17, Y + 1, 17, lantern(False))
        else:
            for x in (16, 17, 18):
                d.set(x, Y, 17, "moss_block")
                d.set(x, Y + 1, 17, ("azalea", "fern", "flowering_azalea")[x - 16])
            d.chair(14, Y, 17, "south", "birch", sit=False)
            d.chair(15, Y, 17, "south", "birch", sit=False)
            d.set(18, Y, 16, "potted_bamboo")
    flight(d, 6, 16, 2, 6, "east", "smooth_quartz")
    flight_rails(d, 6, 16, 2, 6, "east", "glass_pane")
    for f, s in enumerate(S):
        Y = s + 1
        if f % 2 == 0:
            flight(d, 11, 17, Y, 5, "west", "smooth_quartz")
            flight_rails(d, 11, 17, Y, 5, "west", "glass_pane")
        else:
            flight(d, 7, 16, Y, 5, "east", "smooth_quartz")
            flight_rails(d, 7, 16, Y, 5, "east", "glass_pane")
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
    for x in (5, 9, 13, 17):                              # canopy downlights over the entrance
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
    for x in (9, 10, 11):                                # residents' lounge: sofa and coffee table (all levels)
        d.chair(x, 2, 11, "south", "birch")
    seats += 3
    for x in (9, 10, 11):
        d.set(x, 2, 10, slab("smooth_quartz", "top"))
    d.set(9, 3, 10, "potted_azure_bluet")
    d.set(11, 3, 10, "candle[candles=3,lit=false,waterlogged=false]")
    d.set(12, 2, 11, slab("smooth_quartz", "top"))       # side table with a lamp
    d.set(12, 3, 11, lantern(False))
    d.set(12, 2, 8, "potted_bamboo")
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
    for x in range(px1 + 1, 13):                         # bedside carpet run in front of the beds
        if PZ + 3 <= 14:
            d.set(x, Y, PZ + 3, "light_gray_carpet")
    d.set(14, Y, 15, slab("birch", "top"))               # dining table by the kitchenette
    d.set(15, Y, 15, slab("birch", "top"))
    d.set(14, Y + 1, 15, "potted_white_tulip")
    d.set(15, Y + 1, 15, "candle[candles=3,lit=false,waterlogged=false]")
    d.chair(14, Y, 14, "north", "birch", sit=False)
    d.chair(15, Y, 14, "north", "birch", sit=False)
    d.set(5, Y, 17, slab("birch", "top"))                # study desk in the back corner
    d.set(5, Y + 1, 17, endrod("up"))
    d.chair(6, Y, 17, "east", "birch", sit=False)
    d.set(5, Y, 16, "bookshelf")
    d.set(5, Y + 1, 16, "potted_bamboo")
    bx = [6, 5, 9, 11, 13]
    nb = L
    for i in range(nb):
        x = bx[i]
        d.bed(x, Y, PZ + 1, "north", ("cyan", "light_blue", "white", "lime", "light_gray")[i])
        d.set(x, Y + 3, PZ + 2, endrod("down"))          # reading light over each bed
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
    for x in (6, 9, 12, 15, 18):                          # planters along the roof parapet
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

        for x, z in ((6, PZ + 2), (8, 16), (14, PZ + 2), (16, 16), (6, 16), (15, 12)):
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
def win_hw(d, x, y, z, h=2, lintel="calcite", out=None):
    """Sash window with a lintel; with `out` a flower box (trapdoor + flowers) on the sill outside."""
    for k in range(h):
        d.set(x, y + k, z, "glass_pane")
    d.set(x, y + h, z, lintel)
    if out:
        ox, oz = x + D4[out][0], z + D4[out][1]
        if d.bp.inside(ox, y, oz) and d.air(ox, y, oz) and d.air(ox, y - 1, oz) and y > 3:
            d.set(ox, y - 1, oz, trap("dark_oak", out, "top"))
            d.set(ox, y, oz, ("potted_red_tulip", "potted_blue_orchid", "potted_allium")[(x + y + z) % 3])


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
            win_hw(d, x, ya + 1, Z1, out="north")
        for x in (3, 10, 19, 26):
            win_hw(d, x, ya + 1, Z2, out="south")
        for z in (7, 14):
            win_hw(d, X1, ya + 1, z, out="west")
            win_hw(d, X2, ya + 1, z, out="east")
        if ya > 2:
            for x in (14, 15, 16):
                win_hw(d, x, ya + 1, Z1)
    # ---- stair hall
    for x, z in cells(14, 6, 16, 16):
        d.set(x, 1, z, "polished_blackstone" if (x + z) % 2 else "calcite")
    for fl in ((14, 11, 2, "south"), (16, 15, 7, "north"), (14, 15, 12, "north")):
        flight(d, fl[0], fl[1], fl[2], 5, fl[3], "dark_oak")
        flight_rails(d, fl[0], fl[1], fl[2], 5, fl[3], "dark_oak_fence")
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
    # ---- rear garden (L3+), roof lantern (L5)
    if L >= 3:
        for x, z in cells(0, 18, 30, 24):
            if (x in (0, 30) or z == 24) and not (z == 24 and 14 <= x <= 16):
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
    flight_rails(d, 5, 9, 2, 5, "south", "spruce_fence")
    flight_rails(d, 5, 20, 7, 5, "north", "spruce_fence")
    for y in (7, 12):                                    # railings across the open ends of the gallery decks
        for x in (5, 6, 7):
            for z in (3, 27):
                if d.air(x, y, z):
                    d.set(x, y, z, "spruce_fence")
    for z in range(Z1 - 1, Z2 + 2):
        for x, y in ((3, 12), (4, 13), (5, 14), (6, 15), (7, 16)):
            d.set(x, y, z, stair("dark_oak", "east"))
    for s in S:
        for fz in G["FZS"]:
            d.door(X1, s + 1, fz + 5, "west", "spruce")
            d.door(X2, s + 1, fz + 4, "east", "spruce", "right")
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
    # covered ground under the west gallery: log store, boot bench, kegs and lanterns under the deck
    for z in ((5, 6, 22, 23) if L >= 2 else (5, 6)):
        d.set(7, 2, z, log("spruce_log", "z"))
        d.set(7, 3, z, log("spruce_log", "z"))
    d.chair(7, 2, 17, "east", "spruce", sit=False)
    d.chair(7, 2, 18, "east", "spruce", sit=False)
    d.keg(7, 2, 19, "west")
    d.set(7, 3, 19, lantern(False))
    if L >= 2:
        d.set(7, 2, 16, "barrel[facing=up,open=false]")
        d.set(6, 2, 25, "stripped_spruce_log[axis=y]")  # chopping block
        d.set(6, 2, 24, "potted_fern")
    for z in (7, 17, 24):
        d.set(6, 5, z, lantern())
    # under the east balconies: firewood, a bench and a lantern each
    for fz in G["FZS"]:
        for z in (fz + 2, fz + 3):
            d.set(21, 2, z, log("spruce_log", "z"))
            d.set(21, 3, z, log("spruce_log", "z"))
        d.chair(21, 2, fz + 5, "west", "spruce", sit=False)
        d.keg(21, 2, fz + 6, "north")
        d.set(22, 5, fz + 4, lantern())
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
            d.set(x, 6, 28, slab("dark_oak", "top"))
            d.set(x, 6, 29, slab("dark_oak", "top"))
            d.set(x, 6, 30, slab("dark_oak", "top"))
        for x in range(18, 23):
            for y in range(2, 5):
                d.set(x, y, 30, log("spruce_log", "x") if (x + y) % 3 else log("stripped_spruce_log", "x"))
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


# ============================================================================================ TWIN BUILDER
# Annex (child) box: world x AX.., z AZ.., local y=0 = parent ground (y=1); HUT = local hut cell.
TB_NT = dict(AX=19, AZ=4, AW=12, AD=12, AH=9, HUT=(10, 1, 1))
TB_HW = dict(AX=17, AZ=11, AW=13, AD=15, AH=12, HUT=(2, 1, 4))
TB_CA = dict(AX=20, AZ=15, AW=12, AD=14, AH=10, HUT=(2, 1, 2))


def rack_unit(d, x, z, along, n, y, filled, post, shelf, face, pallet=None):
    """Shelving bay: n cells along `along` from (x,z), posts at both ends 3 high, shelf boards on top (y+3).
    Racks fill bottom-up, level by level, up to `filled`; empty bottom cells get a pallet. Returns racks placed."""
    dx, dz = D4[along]
    run_ = [(x + dx * i, z + dz * i) for i in range(n)]
    ends = [(x - dx, z - dz), (x + dx * n, z + dz * n)]
    for ex, ez in ends:
        for k in range(3):
            d.set(ex, y + k, ez, post)
    for cx, cz in [ends[0]] + run_ + [ends[1]]:
        d.set(cx, y + 3, cz, shelf)
    k = 0
    for lvl in range(3):
        for cx, cz in run_:
            if k < filled:
                d.rack(cx, y + lvl, cz, face)
                k += 1
            elif lvl == 0 and pallet:
                d.set(cx, y, cz, pallet)
    return k


def racks_in(d, units, y, need, post, shelf, pallet):
    """Fill shelving units [(x, z, along, n, face)] in order until `need` racks are placed."""
    left = need
    for (x, z, along, n, face) in units:
        left -= rack_unit(d, x, z, along, n, y, min(left, 3 * n), post, shelf, face, pallet)
    return left


def pallet_stack(d, x, z, y, block, h=2, base="spruce_slab[type=bottom,waterlogged=false]"):
    d.set(x, y, z, base)
    for k in range(1, h):
        d.set(x, y + k, z, block)


# ---------------------------------------------------------------------------------------------- Neoterra
def nt_shed(d, x1, z1, x2, z2, y, door_x, roll=(None, None), wall="light_gray_concrete"):
    """Prefab steel shed: concrete base walls, glass clerestory, white band, flat roof with parapet."""
    for x, z in cells(x1, z1, x2, z2):
        d.set(x, y - 1, z, "smooth_stone")
    for yy in range(y, y + 5):
        for x, z in cells(x1, z1, x2, z2):
            if x in (x1, x2) or z in (z1, z2):
                corner = x in (x1, x2) and z in (z1, z2)
                b = "white_concrete" if corner or yy == y + 4 else (wall if yy < y + 3 else
                                                                      "light_blue_stained_glass_pane")
                d.set(x, yy, z, b)
            else:
                d.set(x, yy, z, AIR)
    for x, z in cells(x1, z1, x2, z2):
        d.set(x, y + 5, z, "smooth_stone")
        if x in (x1, x2) or z in (z1, z2):
            d.set(x, y + 6, z, "white_concrete")
            d.set(x, y + 7, z, slab("smooth_quartz"))
    for x in range(x1 + 2, x2 - 1, 3):
        for z in range(z1 + 2, z2 - 1, 3):
            d.set(x, y + 5, z, "sea_lantern")
    a, b = roll                                                  # roller-door opening with safety stripes
    if a is not None:
        d.clear(a, y, z1, b, y + 2, z1)
        for k, yy in enumerate(range(y, y + 4)):
            stripe = "yellow_concrete" if k % 2 == 0 else "black_concrete"
            d.set(a - 1, yy, z1, stripe)
            d.set(b + 1, yy, z1, stripe)
        for k, x in enumerate(range(a - 1, b + 2)):
            d.set(x, y + 3, z1, "yellow_concrete" if k % 2 == 0 else "black_concrete")
        for x in range(a, b + 1):
            d.set(x, y + 2, z1 + 1, trap("iron", "north", "top"))
    d.door(door_x, y, z1, "north", "birch")


def annex_nt(rel, L):
    G = TB_NT
    d = Design("Neoterra", rel, (G["AW"], G["AH"] + 1, G["AD"]), gy=0, paving="smooth_stone")
    nt_shed(d, 0, 0, 11, 11, 1, 9, (4, 6))
    d.hut(*G["HUT"])
    # one long steel rack aisle across the shed
    units = [(3, 5, "east", 2, "north"), (7, 5, "east", 2, "south")]
    racks_in(d, units, 1, d.req["racks"], "gray_concrete", slab("smooth_stone", "top"),
             "spruce_slab[type=bottom,waterlogged=false]")
    # workbench line on the back wall
    d.item(2, 1, 10, "crafting_table")
    for x in (3, 4):
        d.set(x, 1, 10, slab("smooth_stone", "top"))
    d.set(5, 1, 10, "stonecutter[facing=north]")
    d.set(6, 1, 10, "grindstone[face=floor,facing=north]")
    d.set(7, 1, 10, "smithing_table")
    d.set(4, 2, 10, "lantern[hanging=false,waterlogged=false]")
    for x in range(2, 8):
        d.set(x, 3, 10, slab("smooth_stone", "top"))
    # materials by the door
    pallet_stack(d, 1, 8, 1, "bricks")
    pallet_stack(d, 1, 9, 1, "white_concrete")
    pallet_stack(d, 10, 8, 1, "glass", 2)
    pallet_stack(d, 10, 9, 1, "smooth_stone", 3 if L >= 3 else 2)
    if L >= 2:
        d.set(10, 1, 5, "cartography_table")
    if L >= 4:
        for x, z in ((1, 1), (3, 1), (5, 1), (7, 1), (9, 1), (1, 4), (3, 4), (5, 4), (7, 4), (9, 4)):
            d.set(x, 7, z, "daylight_detector[inverted=false,power=0]")
    if L >= 5:
        for x in range(1, 11):
            d.set(x, 4, 0, "cyan_terracotta")
    return d


def twin_nt(rel, L):
    G = TB_NT
    d = Design("Neoterra", rel, (33, 30, 27), paving="smooth_stone")
    for x, z in cells(0, 0, 32, 26):
        d.set(x, 1, z, "smooth_stone" if (x // 3 + z // 3) % 2 else "light_gray_concrete")
    for x in range(14, 19):                                    # drive-through lane with markings
        for z in range(0, 16):
            d.set(x, 1, z, "gray_concrete" if x != 16 or z % 3 == 0 else "yellow_concrete")
    nt_shed(d, 2, 4, 13, 15, 2, 4, (7, 9))
    d.hut(3, 2, 5)
    units = [(6, 8, "south", 2, "west"), (6, 12, "south", 2, "east")]
    racks_in(d, units, 2, d.req["racks"], "gray_concrete", slab("smooth_stone", "top"),
             "spruce_slab[type=bottom,waterlogged=false]")
    # workbench wall (west)
    d.item(3, 2, 12, "crafting_table")
    d.set(3, 2, 11, slab("smooth_stone", "top"))
    d.set(3, 2, 10, "stonecutter[facing=east]")
    d.set(3, 2, 13, "grindstone[face=floor,facing=east]")
    d.set(3, 3, 11, "lantern[hanging=false,waterlogged=false]")
    for z in range(10, 14):
        d.set(3, 4, z, slab("smooth_stone", "top"))
    # site office corner (glass box) with the plans table
    for x, z in cells(9, 5, 12, 7):
        if x == 9 or z == 7:
            d.set(x, 2, z, "white_concrete")
            d.set(x, 3, z, "light_gray_stained_glass_pane")
    d.door(10, 2, 7, "south", "birch")
    d.set(11, 2, 5, "cartography_table")
    d.chair(12, 2, 5, "east", "birch", sit=False)
    d.set(12, 2, 6, "lectern[facing=west,has_book=false,powered=false]")
    pallet_stack(d, 11, 13, 2, "bricks")
    pallet_stack(d, 12, 13, 2, "bricks", 3)
    pallet_stack(d, 11, 11, 2, "glass")
    d.sign(8, 6, 3, "north", ["BUILD DEPOT"], "birch", glow=True, color="cyan")
    for x, z in ((3, 9), (12, 9)):                       # safety banners and planters by the doors
        d.set(x, 4, z, "yellow_wall_banner[facing=east]" if x == 3 else "yellow_wall_banner[facing=west]")
    for x in (2, 13):
        d.set(x, 2, 3, "moss_block")
        d.set(x, 3, 3, "azalea")
    d.set(5, 2, 3, "potted_bamboo")
    # annex (second builder)
    add_child(d, G["AX"], 2, G["AZ"], G["AW"], G["AH"], G["AD"], G["HUT"], ANNEX)
    # ---- rear yard: chain-link fence, materials, scaffold tower, mixer
    for x in range(0, 33):
        d.set(x, 2, 26, "iron_bars")
        d.set(x, 3, 26, "iron_bars")
    for z in range(17, 26):
        for x in (0, 32):
            d.set(x, 2, z, "iron_bars")
            d.set(x, 3, z, "iron_bars")
    for z in (16,):
        for x in list(range(0, 2)) + list(range(31, 33)):
            d.set(x, 2, z, "iron_bars")
    for x in range(2, 6):                                     # stacked logs
        for y in (2, 3):
            d.set(x, y, 18, log("stripped_birch_log", "x"))
            d.set(x, y, 19, log("stripped_birch_log", "x"))
    for x, z in cells(2, 22, 4, 23):
        pallet_stack(d, x, z, 2, "bricks", 3 if (x + z) % 2 else 2)
    for x, z in cells(8, 22, 9, 24):
        pallet_stack(d, x, z, 2, "white_concrete", 2)
    for x, z in cells(27, 18, 28, 19):                        # scaffold tower
        for y in range(2, 8 + (2 if L >= 3 else 0)):
            d.set(x, y, z, "scaffolding[bottom=false,distance=0,waterlogged=false]")
    d.set(24, 2, 21, "cauldron")                              # concrete mixer
    d.set(24, 3, 21, "hopper[enabled=true,facing=down]")
    d.set(25, 2, 21, "gray_concrete_powder")
    d.set(25, 2, 22, "light_gray_concrete_powder")
    d.set(23, 2, 21, "iron_trapdoor[facing=east,half=bottom,open=true,powered=false,waterlogged=false]")
    # ---- L2: canopy over the drive-through
    if L >= 2:
        for z in (4, 9, 15):
            for y in range(2, 8):
                d.set(18, y, z, "light_gray_concrete")
        for x, z in cells(14, 3, 18, 15):
            d.set(x, 8, z, "light_gray_stained_glass" if (x + z) % 2 else "white_concrete")
        for x in range(14, 19):
            d.set(x, 8, 3, "cyan_terracotta")
        d.set(16, 7, 8, endrod("down"))
        d.set(16, 7, 12, endrod("down"))
    # ---- L3+: tower crane
    if L >= 3:
        top = 19 if L < 5 else 21
        for x, z in cells(14, 20, 17, 23):
            d.set(x, 1, z, "gray_concrete")
        for y in range(2, top):
            for x, z in cells(15, 21, 16, 22):
                d.set(x, y, z, "yellow_concrete" if y % 3 == 2 else "iron_bars")
        for x, z in cells(14, 20, 17, 23):
            d.set(x, top, z, "yellow_concrete")
        for x, z in cells(15, 20, 16, 20):
            d.set(x, top + 1, z, "light_gray_stained_glass")
        d.set(15, top + 1, 21, "yellow_concrete")
        d.set(16, top + 1, 21, "yellow_concrete")
        for x in range(8, 31):                               # jib (east) + counter-jib (west)
            d.set(x, top + 2, 21, "yellow_concrete")
            if x % 2 == 0:
                d.set(x, top + 3, 21, "iron_bars")
        for x in (8, 9, 10):
            d.set(x, top + 1, 21, "gray_concrete")
            d.set(x, top, 21, "gray_concrete")
        for y in range(top + 3, top + 6):
            d.set(15, y, 21, "yellow_concrete")
        d.set(15, top + 6, 21, "red_concrete")
        hx = 26
        d.set(hx, top + 1, 21, "iron_block")
        for y in range(top - 6, top + 1):
            d.set(hx, y, 21, chain())
        d.set(hx, top - 7, 21, "iron_bars")
        for x in (hx - 1, hx, hx + 1):
            d.set(x, top - 8, 21, "stone_bricks")
    # ---- L4: site cabin; L5: floodlights
    if L >= 4:
        for x, z in cells(19, 17, 22, 24):
            for y in (2, 3, 4):
                d.set(x, y, z, "cyan_concrete" if x in (19, 22) or z in (17, 24) else AIR)
            d.set(x, 5, z, "white_concrete")
        d.door(20, 2, 17, "north", "birch")
        d.set(22, 3, 20, "glass_pane")
        d.set(22, 3, 21, "glass_pane")
        d.set(21, 2, 22, "cartography_table")
        d.chair(21, 2, 21, "north", "birch", sit=False)
        d.set(20, 2, 23, "barrel[facing=up,open=false]")
        d.set(20, 4, 20, lantern())
        d.sign(21, 4, 16, "north", ["SITE", "OFFICE"], "birch", glow=True, color="cyan")
    if L >= 5:
        for x, z in ((1, 17), (31, 17), (1, 25), (31, 25)):
            for y in range(2, 7):
                d.set(x, y, z, "light_gray_concrete")
            d.set(x, 7, z, "sea_lantern")
            d.set(x, 8, z, slab("smooth_stone"))
    return d


# ---------------------------------------------------------------------------------------------- Hearthwood
def annex_hw(rel, L):
    G = TB_HW
    d = Design("Hearthwood", rel, (G["AW"], G["AH"] + 1, G["AD"]), gy=0, paving="gravel")
    x1, z1, x2, z2 = 1, 3, 11, 13
    for x, z in cells(x1, z1, x2, z2):
        d.set(x, 0, z, "stone_bricks" if x in (x1, x2) or z in (z1, z2) else "oak_planks")
    # brick back and side walls, open oak-post front (north)
    for y in range(1, 6):
        for x, z in cells(x1, z1, x2, z2):
            if z == z2 or x in (x1, x2):
                if z != z1:
                    d.set(x, y, z, "bricks")
        for x in (x1, 6, x2):
            d.set(x, y, z1, log("dark_oak_log", "y"))
    for x in range(x1, x2 + 1):
        d.set(x, 5, z1, log("dark_oak_log", "x"))
    for z in (6, 10):
        d.set(x1, 2, z, "glass_pane")
        d.set(x1, 3, z, "glass_pane")
    d.gable(x1, z1, x2, z2, 6, "x", "brick_stairs", "brick_slab", "bricks")
    d.hut(*G["HUT"])
    units = [(3, 12, "east", 2, "north"), (7, 12, "east", 2, "north")]
    racks_in(d, units, 1, d.req["racks"], fence("dark_oak"), slab("oak", "top"),
             "oak_slab[type=bottom,waterlogged=false]")
    # banker benches (masons' work stones) and the crafting table
    for x in (3, 4, 5):
        d.set(x, 1, 8, "stone_bricks")
        d.set(x, 2, 8, slab("smooth_stone"))
    d.item(8, 1, 8, "crafting_table")
    d.set(9, 1, 8, "stonecutter[facing=north]")
    d.set(10, 1, 8, "grindstone[face=floor,facing=west]")
    pallet_stack(d, 10, 5, 1, "stone_bricks", 2, "oak_slab[type=bottom,waterlogged=false]")
    pallet_stack(d, 10, 6, 1, "chiseled_stone_bricks", 2, "oak_slab[type=bottom,waterlogged=false]")
    d.set(2, 1, 10, "barrel[facing=up,open=false]")
    d.set(2, 1, 11, "water_cauldron[level=3]")
    for x, z in ((4, 6), (8, 6), (6, 10)):
        d.set(x, 5, z, lantern())
    if L >= 3:
        for x in (2, 3):
            d.set(x, 1, 1, "stone_bricks")
            d.set(x, 2, 1, slab("stone_brick"))
    if L >= 5:
        d.sign(6, 4, z1 - 1, "north", ["MASONS'", "LODGE"], "dark_oak")
    return d


def twin_hw(rel, L):
    G = TB_HW
    d = Design("Hearthwood", rel, (31, 24, 29), paving="grass_block[snowy=false]")
    X1, X2, Z1, Z2 = 2, 12, 3, 18
    for x, z in cells(13, 0, 30, 10):
        d.set(x, 1, z, "gravel" if (x + z) % 4 else "coarse_dirt")
    for x, z in cells(6, 0, 8, 2):
        d.set(x, 1, z, "gravel")
    # ---- workshop: brick ground storey, jettied-look timber loft, steep tiled gable to the street
    d.fill(X1, 1, Z1, X2, 1, Z2, "stone_bricks")
    d.fill(X1 + 1, 1, Z1 + 1, X2 - 1, 1, Z2 - 1, "oak_planks")
    ring(d, X1, Z1, X2, Z2, 2, 5, "bricks")
    d.clear(X1 + 1, 2, Z1 + 1, X2 - 1, 9, Z2 - 1)
    ring(d, X1, Z1, X2, Z2, 2, 2, "stone_bricks")
    d.fill(X1, 6, Z1, X2, 6, Z2, "dark_oak_planks")
    d.fill(X1 + 1, 6, Z1 + 1, X2 - 1, 6, Z2 - 1, "spruce_planks")
    ring(d, X1, Z1, X2, Z2, 7, 9, "calcite")
    for x, z in cells(X1, Z1, X2, Z2):
        if (x in (X1, X2) and (z - Z1) % 3 == 0) or (z in (Z1, Z2) and (x - X1) % 2 == 0):
            for y in (7, 8):
                d.set(x, y, z, log("dark_oak_log", "y"))
        if x in (X1, X2) or z in (Z1, Z2):
            d.set(x, 9, z, log("dark_oak_log", "x" if z in (Z1, Z2) else "z"))
    ridge = d.gable(X1, Z1, X2, Z2, 10, "z", "dark_oak_stairs", "dark_oak_slab", "calcite")
    for z in (Z1, Z2):
        for y in range(10, ridge):
            if d.get(7, y, z) == "minecraft:calcite":
                d.set(7, y, z, log("dark_oak_log", "y"))
    # cart doors, loft door + hoist beam with pulley and a load
    d.clear(6, 2, Z1, 8, 4, Z1)
    for x in (6, 7, 8):
        d.set(x, 5, Z1, log("dark_oak_log", "x"))
    d.door(7, 7, Z1, "north", "dark_oak")
    d.set(7, 7, Z1 - 1, "dark_oak_fence")                  # bar across the hoist door
    for z in range(Z1 - 3, Z1 + 1):
        d.set(7, 11, z, log("dark_oak_log", "z"))
    for y in range(6, 11):
        d.set(7, y, Z1 - 3, chain())
    d.set(7, 5, Z1 - 3, "hay_block[axis=y]")
    # windows
    for z in (6, 10, 14):
        win_hw(d, X1, 3, z, 2, "bricks")
        win_hw(d, X2, 3, z, 2, "bricks")
        for xx, f_ in ((X1 - 1, "west"), (X2 + 1, "east")):     # shutters on the workshop windows
            for zz in (z - 1, z + 1):
                for yy in (3, 4):
                    if d.air(xx, yy, zz):
                        d.set(xx, yy, zz, trap("dark_oak", f_, "bottom", True))
    for z in (8, 13):
        d.set(X1, 8, z, "glass_pane")
        d.set(X2, 8, z, "glass_pane")
    d.door(4, 2, Z1, "north", "dark_oak")
    d.hut(3, 2, 4)
    d.sign(4, 5, Z1 - 1, "north", ["J. MASON", "& SONS", "Builders"], "dark_oak")
    # ---- inside: two rack aisles, joiner's bench, ladder to the timber loft
    units = [(5, 10, "south", 2, "east"), (9, 10, "south", 2, "west")]
    racks_in(d, units, 2, d.req["racks"], fence("dark_oak"), slab("oak", "top"),
             "oak_slab[type=bottom,waterlogged=false]")
    d.item(3, 2, 16, "crafting_table")
    for x in (4, 5, 6):
        d.set(x, 2, 17, slab("dark_oak", "top"))
    d.set(5, 3, 17, "lantern[hanging=false,waterlogged=false]")
    d.set(7, 2, 17, "stonecutter[facing=north]")
    d.set(8, 2, 17, "grindstone[face=floor,facing=north]")
    for x in (4, 5, 6, 7, 8):
        d.set(x, 4, 17, slab("dark_oak", "top"))
    for y in range(2, 8):
        d.set(11, y, 17, "ladder[facing=north,waterlogged=false]")
    d.set(11, 6, 17, "ladder[facing=north,waterlogged=false]")
    for x, z in ((4, 8), (7, 7), (7, 14)):
        d.set(x, 5, z, lantern())
    for x in range(3, 11):                                    # loft: seasoning timber
        for z in (5, 6, 13, 14):
            if x != 7:
                d.set(x, 7, z, log("stripped_oak_log", "x"))
    # ---- annex (masons' lodge) and the yard
    add_child(d, G["AX"], 2, G["AZ"], G["AW"], G["AH"], G["AD"], G["HUT"], ANNEX)
    for x in range(14, 17):                                    # timber stack
        for y in (2, 3):
            for z in (5, 6, 7):
                d.set(x, y, z, log("oak_log", "z"))
    for x, z in cells(22, 4, 24, 5):
        pallet_stack(d, x, z, 2, "stone_bricks", 2 if (x + z) % 2 else 3, "oak_slab[type=bottom,waterlogged=false]")
    d.set(27, 2, 6, "sand")
    d.set(28, 2, 6, slab("sandstone"))
    d.set(27, 2, 7, slab("sandstone"))
    d.set(28, 2, 7, "barrel[facing=up,open=false]")
    if L >= 2:                                                # walled yard with an arched gateway
        for x in range(13, 31):
            for y in (2, 3):
                d.set(x, y, 0, "bricks")
            d.set(x, 4, 0, slab("stone_brick"))
        for z in range(0, 11):
            for y in (2, 3):
                d.set(30, y, z, "bricks")
            d.set(30, 4, z, slab("stone_brick"))
        d.clear(18, 2, 0, 20, 4, 0)
        for x in (17, 21):
            for y in range(2, 6):
                d.set(x, y, 0, "bricks")
        d.set(18, 5, 0, "bricks")
        d.set(19, 5, 0, "bricks")
        d.set(20, 5, 0, "bricks")
        d.set(18, 4, 0, stair("brick", "east", "top"))
        d.set(20, 4, 0, stair("brick", "west", "top"))
        d.set(19, 6, 0, slab("stone_brick"))
        d.set(17, 6, 0, lantern(False))
        d.set(21, 6, 0, lantern(False))
    if L >= 3:                                                # sawpit with a log on the trestles
        for x in range(14, 19):
            d.set(x, 1, 9, AIR)
            d.set(x, 0, 9, "dirt")
        for x in (14, 18):
            d.set(x, 1, 9, "oak_planks")
        for x in range(14, 19):
            d.set(x, 2, 9, log("oak_log", "x"))
    if L >= 4:                                                # lime kiln
        for x, z in cells(25, 8, 27, 10):
            for y in (2, 3, 4):
                if (x, z) != (26, 9):
                    d.set(x, y, z, "stone_bricks" if y < 4 else "bricks")
        d.set(26, 2, 9, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        d.set(26, 2, 8, AIR)
        d.set(26, 3, 8, "stone_bricks")
        for x, z in cells(25, 8, 27, 10):
            d.set(x, 5, z, "bricks" if (x, z) != (26, 9) else AIR)
    if L >= 5:                                                # handcart + flower tubs by the gate
        d.set(15, 2, 2, slab("spruce", "top"))
        d.set(16, 2, 2, slab("spruce", "top"))
        d.set(15, 1, 2, "gravel")
        d.set(14, 2, 2, fence("spruce"))
        d.set(16, 3, 2, "bricks")
        for x in (17, 21):
            d.set(x, 2, 1, "potted_red_tulip")
    return d


# ---------------------------------------------------------------------------------------------- Cascadia
def ca_logwalls(d, x1, z1, x2, z2, y1, y2):
    for y in range(y1, y2 + 1):
        for x in range(x1, x2 + 1):
            d.set(x, y, z1, log("stripped_spruce_log", "x"))
            d.set(x, y, z2, log("stripped_spruce_log", "x"))
        for z in range(z1, z2 + 1):
            d.set(x1, y, z, log("stripped_spruce_log", "z"))
            d.set(x2, y, z, log("stripped_spruce_log", "z"))
        for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
            d.set(x, y, z, log("spruce_log", "y"))
    for x, z in cells(x1, z1, x2, z2):
        if x in (x1, x2) or z in (z1, z2):
            d.set(x, y1 - 1, z, stone(x, y1 - 1, z))
            d.set(x, y1, z, stone(x, y1, z))


def annex_ca(rel, L):
    G = TB_CA
    d = Design("Cascadia", rel, (G["AW"], G["AH"] + 1, G["AD"]), gy=0, paving="coarse_dirt")
    x1, z1, x2, z2 = 1, 1, 10, 8
    for x, z in cells(x1 + 1, z1 + 1, x2 - 1, z2 - 1):
        d.set(x, 0, z, "spruce_planks")
    ca_logwalls(d, x1, z1, x2, z2, 1, 5)
    d.clear(x1 + 1, 1, z1 + 1, x2 - 1, 5, z2 - 1)
    d.gable(x1, z1, x2, z2, 6, "x", "spruce_stairs", "spruce_slab", "spruce_planks")
    d.double_door(5, 1, z1, "x", "north", "spruce")
    d.door(5, 1, z2, "south", "spruce")
    win_ca(d, 2, 2, z1, "north")
    win_ca(d, 8, 2, z1, "north")
    win_ca(d, x2, 2, 4, "east")
    d.hut(*G["HUT"])
    d.item(2, 1, 6, "crafting_table")
    d.set(2, 1, 5, slab("spruce", "top"))
    d.set(2, 1, 4, slab("spruce", "top"))
    d.set(2, 2, 5, "lantern[hanging=false,waterlogged=false]")
    d.set(9, 1, 6, "stonecutter[facing=west]")
    d.set(9, 1, 5, "grindstone[face=floor,facing=west]")
    d.set(9, 1, 3, "chest[facing=west,type=single,waterlogged=false]")
    d.set(5, 5, 4, lantern())
    d.set(6, 1, 4, log("stripped_spruce_log", "x"))           # timber on trestles
    d.set(7, 1, 4, log("stripped_spruce_log", "x"))
    # lean-to rack shed on the south side
    for x in (1, 5, 10):
        for y in range(1, 5):
            d.set(x, y, 13, log("spruce_log", "y"))
    for x, z in cells(0, 9, 11, 13):
        d.set(x, 5, z, slab("dark_oak"))
    for x, z in cells(1, 9, 10, 13):
        d.set(x, 0, z, "spruce_planks")
    units = [(2, 11, "east", 2, "north"), (7, 11, "east", 2, "south")]
    racks_in(d, units, 1, d.req["racks"], log("spruce_log", "y"), slab("spruce", "top"),
             "spruce_slab[type=bottom,waterlogged=false]")
    d.set(5, 4, 11, lantern())
    if L >= 3:
        for x in (0, 11):
            d.set(x, 1, 0, "barrel[facing=up,open=false]")
    if L >= 5:
        d.sign(5, 4, 0, "north", ["SHOP NO. 2"], "spruce")
    return d


def a_frame(d, x, z, y, h):
    """Log A-frame derrick standing across z at x..x+6: two raking legs, cross beam, pulley chain and load."""
    legs = [(x, x + 6), (x + 1, x + 5), (x + 2, x + 4)]
    seg = max(2, h // 3)
    for i, (a, b) in enumerate(legs):
        for k in range(seg):
            yy = y + i * seg + k
            d.set(a, yy, z, log("spruce_log", "y"))
            d.set(b, yy, z, log("spruce_log", "y"))
    top = y + 3 * seg
    for xx in range(x + 1, x + 6):
        d.set(xx, top, z, log("stripped_spruce_log", "x"))
    d.set(x + 3, top + 1, z, slab("dark_oak"))
    for yy in range(y + 3, top):
        d.set(x + 3, yy, z, chain())
    d.set(x + 3, y + 2, z, log("stripped_spruce_log", "z"))
    for zz in (z - 1, z + 1):                                 # back stays
        d.set(x + 3, y, zz + (zz - z) * 2, fence("spruce"))
    d.set(x + 7, y, z, log("stripped_spruce_log", "x"))      # windlass
    d.set(x + 8, y, z, fence("spruce"))
    return top


def twin_ca(rel, L):
    G = TB_CA
    d = Design("Cascadia", rel, (33, 22, 31), paving="coarse_dirt")
    for x, z in cells(0, 0, 32, 30):
        yard = (2 <= x <= 19 and 14 <= z <= 29) or (8 <= x <= 12 and z <= 3) or (20 <= x <= 31 and 13 <= z <= 14)
        if not yard:
            d.set(x, 1, z, "grass_block[snowy=false]" if (x * 5 + z * 3) % 7 else "moss_block")
        elif (x + z) % 5 == 0:
            d.set(x, 1, z, "gravel")
    X1, X2, Z1, Z2 = 2, 18, 3, 13
    # ---- big log barn, long gable along the street
    for x, z in cells(X1 + 1, Z1 + 1, X2 - 1, Z2 - 1):
        d.set(x, 1, z, "spruce_planks")
    ca_logwalls(d, X1, Z1, X2, Z2, 2, 7)
    d.clear(X1 + 1, 2, Z1 + 1, X2 - 1, 7, Z2 - 1)
    for z in (Z1, Z2):
        for y in range(2, 8):
            d.set(10, y, z, log("spruce_log", "y"))
    ridge = d.gable(X1, Z1, X2, Z2, 8, "x", "mangrove_stairs", "mangrove_slab", "spruce_planks")
    for x in (X1, X2):
        for y in range(8, ridge):
            if d.get(x, y, 8) == "minecraft:spruce_planks":
                d.set(x, y, 8, log("spruce_log", "y"))
    # barn doors (wide opening with a heavy lintel), side door, windows
    d.clear(8, 2, Z1, 12, 5, Z1)
    for x in range(7, 14):
        d.set(x, 6, Z1, log("spruce_log", "x"))
    for x in (8, 12):
        d.set(x, 2, Z1 - 1, AIR)
    for x in (5, 6, 7, 13, 14, 15):                           # slid-open barn door leaves, X-braced look
        for y in range(2, 6):
            d.set(x, y, Z1 - 1, trap("dark_oak" if (x + y) % 2 else "spruce", "north", "bottom", True))
    for x in range(4, 17):
        d.set(x, 6, Z1 - 1, fence("dark_oak"))                # door track
    d.door(4, 2, Z1, "north", "spruce")
    d.hut(3, 2, 4)
    for x in (6, 15):
        win_ca(d, x, 3, Z1, "north")
    for x in (5, 9, 14):
        win_ca(d, x, 3, Z2, "south")
    for z in (8,):
        win_ca(d, X1, 3, z, "west")
        win_ca(d, X2, 3, z, "east")
    d.sign(10, 7, Z1 - 1, "north", ["TIMBERLINE", "FRAMERS"], "spruce")
    for x, z in ((3, 12), (17, 12), (16, 4)):            # hay and feed sacks in the barn corners
        d.set(x, 2, z, "hay_block[axis=y]")
    d.set(3, 2, 11, "brown_wool")
    d.set(3, 5, 7, "green_wall_banner[facing=east]")
    d.set(17, 5, 7, "green_wall_banner[facing=west]")
    for x in (1, 19):
        d.set(x, 2, 2, "barrel[facing=up,open=false]" if x == 1 else "spruce_log[axis=y]")
        d.set(x, 3, 2, lantern(False))
    # inside: rack aisles, framing bench, tools
    units = [(5, 8, "east", 2, "north"), (13, 8, "east", 2, "south")]
    racks_in(d, units, 2, d.req["racks"], log("spruce_log", "y"), slab("spruce", "top"),
             "spruce_slab[type=bottom,waterlogged=false]")
    d.item(17, 2, 11, "crafting_table")
    for x in (14, 15, 16):
        d.set(x, 2, 12, slab("spruce", "top"))
    d.set(15, 3, 12, "lantern[hanging=false,waterlogged=false]")
    d.set(17, 2, 10, "grindstone[face=floor,facing=west]")
    d.set(17, 2, 9, "stonecutter[facing=west]")
    for x in (8, 9, 10, 11):                                  # a beam being cut on sawhorses
        d.set(x, 3, 11, log("stripped_spruce_log", "x"))
    for x in (8, 11):
        d.set(x, 2, 11, fence("spruce"))
    for x, z in ((5, 6), (10, 8), (15, 6)):
        d.set(x, 7, z, lantern())
    # ---- annex (second framer's shop) and the yard
    add_child(d, G["AX"], 2, G["AZ"], G["AW"], G["AH"], G["AD"], G["HUT"], ANNEX)
    for x in range(3, 8):                                     # log deck
        for z in (16, 17, 18):
            d.set(x, 2, z, log("spruce_log", "x"))
        for z in (16, 17):
            d.set(x, 3, z, log("spruce_log", "x"))
    d.set(10, 2, 16, log("stripped_spruce_log", "y"))         # chopping block
    if L >= 2:                                                # lumber stacks with stickers
        for z in range(21, 29):
            for x, y in ((2, 2), (3, 2), (2, 3), (3, 3), (2, 4)):
                d.set(x, y, z, "stripped_spruce_wood[axis=z]" if (y + z) % 2 else log("stripped_spruce_log", "z"))
        for x, z in ((6, 21), (6, 24)):
            d.set(x, 2, z, fence("spruce"))
            d.set(x + 1, 2, z, fence("spruce"))
            d.set(x, 3, z, slab("spruce"))
            d.set(x + 1, 3, z, slab("spruce"))
    if L >= 3:
        a_frame(d, 9, 21, 2, 9)
    if L >= 4:                                                # timber frame being raised
        for z in (26, 29):
            for x in (10, 16):
                for y in range(2, 7):
                    d.set(x, y, z, log("spruce_log", "y"))
            for x in range(10, 17):
                d.set(x, 7, z, log("stripped_spruce_log", "x"))
            for k, (x1_, x2_) in enumerate(((10, 16), (11, 15), (12, 14))):
                d.set(x1_, 8 + k, z, stair("spruce", "east"))
                d.set(x2_, 8 + k, z, stair("spruce", "west"))
            d.set(13, 10, z, "spruce_planks")
        for z in (27, 28):
            d.set(10, 7, z, log("stripped_spruce_log", "z"))
            d.set(16, 7, z, log("stripped_spruce_log", "z"))
    if L >= 5:
        for x in (1, 19):
            for y in range(2, 5):
                d.set(x, y, 14, fence("spruce"))
            d.set(x, 5, 14, lantern(False))
        d.set(26, 1, 29, "gravel")
    return d


# ============================================================================================ GROWTH KIT
# Later levels grow the complexes with real wings: multi-storey blocks in the pack's style (stairs, windows,
# roofs, chimneys), every floor furnished for its use, plus gardens and yard furniture.
import hm as _hm                                                     # noqa: E402
from blueprint import Blueprint as _BP                              # noqa: E402

STY = {
    "Neoterra": dict(wood="birch", plank="birch_planks", top="smooth_quartz", rug=("light_gray", "cyan"),
                     plants=("potted_bamboo", "potted_white_tulip", "potted_azure_bluet"), stairb="smooth_quartz",
                     floor="polished_diorite", banner="cyan", rail="glass_pane", bush="azalea"),
    "Hearthwood": dict(wood="dark_oak", plank="dark_oak_planks", top="dark_oak", rug=("red", "orange"),
                       plants=("potted_red_tulip", "potted_fern", "potted_allium"), stairb="dark_oak",
                       floor="oak_planks", banner="red", rail="dark_oak_fence", bush="flowering_azalea"),
    "Cascadia": dict(wood="spruce", plank="spruce_planks", top="spruce", rug=("brown", "green"),
                     plants=("potted_fern", "potted_spruce_sapling", "potted_red_mushroom"), stairb="spruce",
                     floor="spruce_planks", banner="green", rail="spruce_fence", bush="sweet_berry_bush[age=3]"),
}

def regrid(d, sx, sz, ox, oz, sy=None):
    """Move everything drawn so far by (ox, oz) into a bigger plot sx x sz (keeps hut, tags, children)."""
    old = d.bp
    nb = _BP(sx, sy or old.sy, sz, old.name)
    for y in range(min(d.gy, nb.sy)):
        for z in range(sz):
            for x in range(sx):
                nb.grid[y][z][x] = _hm._mc(_hm.SOLID)
    pave = _hm._mc(d.P["path"])
    for z in range(sz):
        for x in range(sx):
            nb.grid[d.gy][z][x] = pave
    for y in range(old.sy):
        for z in range(old.sz):
            for x in range(old.sx):
                if y <= d.gy and y < d.gy:
                    continue
                nb.grid[y][z + oz][x + ox] = old.grid[y][z][x]
    nb.tile_entities = {(x + ox, y, z + oz): t for (x, y, z), t in old.tile_entities.items()}
    d.bp = nb
    d.tags = {(x + ox, y, z + oz): t for (x, y, z), t in d.tags.items()}
    if d.hut_pos:
        x, y, z = d.hut_pos
        d.hut_pos = (x + ox, y, z + oz)
    d.child_positions = [(x + ox, y, z + oz, p) for (x, y, z, p) in d.child_positions]
    return d


# ---- hand placement: a tiny plan language. Every line puts ONE piece at a local coordinate I chose
# (lx east, lz south, from the room's north-west interior corner on its walking level).
#   C x z back            chair (stair seat), backrest on `back` (n/e/s/w)
#   T x z [deco]          table (top slab) with something standing on it
#   K x z [h]             bookcase, h high (default 2)
#   Q x z facing [h]      chiseled bookshelf
#   P x z [potted_x]      potted plant
#   S x z item            wall shelf (top slab) with an item on it
#   X x z code [dy]       any block (codes below or a full block state), dy above the floor
#   R x1 z1 x2 z2 colour  rug (carpet) over the free floor of that rectangle
#   L x z                 hanging lamp under the ceiling
#   W x1 z1 x2 z2 [block] partition wall, floor to ceiling
#   D x z facing          door (in a partition)
#   F x z facing          fireplace: fire, jambs either side, flue to the ceiling
#   G x z facing          wall banner (2 above the floor)
DIR = {"n": "north", "e": "east", "s": "south", "w": "west"}


def _code(code, tt, pack):
    if ":" in code and "[" not in code:
        name, f = code.split(":")
        f = DIR.get(f, f)
        return {"barrel": f"barrel[facing={f},open=false]",
                "chest": f"chest[facing={f},type=single,waterlogged=false]",
                "furnace": f"furnace[facing={f},lit=false]", "smoker": f"smoker[facing={f},lit=false]",
                "blast": f"blast_furnace[facing={f},lit=false]",
                "lectern": f"lectern[facing={f},has_book=false,powered=false]",
                "grind": f"grindstone[face=floor,facing={f}]", "cutter": f"stonecutter[facing={f}]",
                "loom": f"loom[facing={f}]", "anvil": f"anvil[facing={f}]",
                "trap": f"{tt}_trapdoor[facing={f},half=top,open=false,powered=false,waterlogged=false]",
                "skull": "skeleton_skull[powered=false,rotation=0]"}[name]
    table = {
        "barrel": "barrel[facing=up,open=false]", "counter": slab(tt, "top"), "slab": slab(tt, "top"),
        "pot": "decorated_pot[cracked=false,facing=north,waterlogged=false]",
        "candle": "candle[candles=3,lit=false,waterlogged=false]", "lamp": lantern(False),
        "brew": "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]",
        "note": "note_block[instrument=harp,note=0,powered=false]", "sink": "water_cauldron[level=3]",
        "water": "water[level=0]", "wool": "white_wool", "bwool": "brown_wool", "hay": "hay_block[axis=y]",
        "andesite": "polished_andesite", "plate": "heavy_weighted_pressure_plate[power=0]",
        "target": "target[power=0]", "chain": chain(), "carto": "cartography_table", "smith": "smithing_table",
        "craft": "crafting_table", "fletch": "fletching_table", "jukebox": "jukebox[has_record=false]",
        "bell": "bell[attachment=floor,facing=north,powered=false]", "cauldron": "cauldron",
        "fence": fence(tt), "planks": f"{tt}_planks", "stone": "smooth_stone",
        "sslab": slab("smooth_stone", "top"), "log": log(f"stripped_{tt}_log" if tt not in ("smooth_quartz",
                                                                                          "smooth_stone") else
                                                       "stripped_birch_log", "x"),
        "glow": "glowstone", "pumpkin": "carved_pumpkin[facing=north]", "melon": "melon",
        "composter": "composter[level=0]",
    }
    return table.get(code, code)


FRAME = {"Neoterra": "polished_andesite", "Hearthwood": "bricks", "Cascadia": "cobblestone"}


class PlanError(RuntimeError):
    pass


def fit(d, pack, ox, y, oz, H, plan, wd, tt, forbid=frozenset(), part=None):
    """Lay out a room/floor from a hand-written plan (see the plan language above)."""
    ceil = y + H - 1
    part = part or {"Neoterra": "light_gray_concrete", "Hearthwood": "calcite", "Cascadia": "spruce_planks"}[pack]
    rugs = []

    def put(lx, lz, st, dy=0):
        x, z = ox + lx, oz + lz
        if dy == 0 and (lx, lz) in forbid:
            raise PlanError(f"{d.rel} [{d.pack}] plan piece in a kept cell ({lx},{lz}) y={y}")
        if not d.air(x, y + dy, z):
            raise PlanError(f"{d.rel} [{d.pack}] ({lx},{lz}) dy={dy} at y={y} already holds {d.get(x, y + dy, z)}")
        d.set(x, y + dy, z, st)

    for raw in plan.strip().splitlines():
        a = raw.split("#")[0].split()
        if not a:
            continue
        op, v = a[0], a[1:]
        if op == "R":
            rugs.append(v)
            continue
        if op == "W":
            x1, z1, x2, z2 = map(int, v[:4])
            blk = v[4] if len(v) > 4 else part
            for lx, lz in cells(x1, z1, x2, z2):
                for yy in range(y, ceil):
                    d.set(ox + lx, yy, oz + lz, blk)
            continue
        lx, lz = int(v[0]), int(v[1])
        if op == "C":
            put(lx, lz, stair(wd, DIR[v[2]]))
        elif op == "T":
            put(lx, lz, slab(tt, "top"))
            if len(v) > 2:
                put(lx, lz, _code(v[2], tt, pack), 1)
        elif op == "K":
            for k in range(int(v[2]) if len(v) > 2 else 2):
                put(lx, lz, "bookshelf", k)
        elif op == "Q":
            for k in range(int(v[3]) if len(v) > 3 else 1):
                put(lx, lz, chiseled(DIR[v[2]]), k)
        elif op == "P":
            put(lx, lz, v[2] if len(v) > 2 else STY[pack]["plants"][0])
        elif op == "S":
            put(lx, lz, slab(tt, "top"))
            put(lx, lz, _code(v[2], tt, pack), 1)
        elif op == "X":
            put(lx, lz, _code(v[2], tt, pack), int(v[3]) if len(v) > 3 else 0)
        elif op == "L":
            x, z = ox + lx, oz + lz
            if d.air(x, ceil - 1, z):
                d.set(x, ceil - 1, z, lantern())
        elif op == "D":
            d.door(ox + lx, y, oz + lz, DIR[v[2]], wd)
        elif op == "G":
            put(lx, lz, f"{STY[pack]['banner']}_wall_banner[facing={DIR[v[2]]}]", 2)
        elif op == "F":
            f = DIR[v[2]]
            sx, sz = D4[CW[f]]
            put(lx, lz, f"campfire[facing={f},lit=true,signal_fire=false,waterlogged=false]")
            for k in (-1, 1):
                put(lx + sx * k, lz + sz * k, FRAME[pack])
                put(lx + sx * k, lz + sz * k, FRAME[pack], 1)
            for yy in range(1, H - 1):
                put(lx, lz, FRAME[pack], yy)
        else:
            raise PlanError(f"unknown plan op {op}")
    for v in rugs:
        x1, z1, x2, z2 = map(int, v[:4])
        for lx, lz in cells(x1, z1, x2, z2):
            x, z = ox + lx, oz + lz
            if d.air(x, y, z) and (lx, lz) not in forbid:
                d.set(x, y, z, f"{v[4]}_carpet")


def flight_rails(d, x, z, y, n, direction, rail):
    """Guard rail for one flight I placed: over the steps whose opening in the floor above is a 2+ drop, a rail
    sits in the opening at walking height (or one higher where the climbers below need the headroom)."""
    dx, dz = D4[direction]
    for i in range(max(1, n - 4), n - 2):
        cx, cz = x + dx * i, z + dz * i
        yr = max(y + n, y + i + 4)
        if d.air(cx, yr, cz) and d.air(cx, y + n - 1, cz):
            d.set(cx, yr, cz, rail)


DEF_ST = {
    "Neoterra": dict(trim="light_gray_concrete", fin="white_concrete", glass="light_blue_stained_glass_pane",
                     clad=None, band=("white_concrete", "cyan_terracotta"), edge="smooth_quartz",
                     parapet="white_concrete", coping="smooth_quartz", door="birch", green=False),
    "Hearthwood": dict(wall0="bricks", wall="bricks", plinth="stone_bricks", quoin="calcite", frame=None,
                       lintel="calcite", band="stone_bricks", roof="deepslate_tile", gable="bricks",
                       door="dark_oak", box="dark_oak", chimney="bricks"),
    "Cascadia": dict(wall0=None, wall="stripped_spruce_log", trim="spruce_log", band="dark_oak_planks",
                     roof="dark_oak", gable="spruce_planks", shutter="spruce", door="spruce"),
}


def _st(pack, st):
    out = dict(DEF_ST[pack])
    out.update(st or {})
    return out


def _wall_cell(d, pack, x, yy, z, x1, z1, x2, z2, Y, H, f, st):
    corner = x in (x1, x2) and z in (z1, z2)
    pos = (x - x1) if z in (z1, z2) else (z - z1)
    if pack == "Neoterra":
        if corner:
            return st["trim"]
        if pos % 4 == 0:
            return st["fin"]
        if st["clad"] and yy == Y + H - 2:
            return st["clad"]
        return st["glass"]
    if pack == "Hearthwood":
        wall = st["wall0"] if f == 0 else st["wall"]
        if corner:
            return st["quoin"] if yy % 2 == 0 else wall
        if f == 0 and yy == Y:
            return st["plinth"]
        if pos % 3 == 1 and Y + 1 <= yy <= Y + 2:
            return "glass_pane"
        if pos % 3 == 1 and yy == Y + 3:
            return st["lintel"]
        if st["frame"] and f > 0 and (pos % 3 == 0 or yy == Y + H - 2):
            return log(st["frame"], "y" if pos % 3 == 0 else ("x" if z in (z1, z2) else "z"))
        return wall
    # Cascadia
    if f == 0:
        if pos % 4 == 2 and Y + 1 <= yy <= Y + 2 and not corner:
            return "glass_pane"
        return st["wall0"] or stone(x, yy, z)
    if corner:
        return log(st["trim"], "y") if st["trim"].endswith(("_log", "_wood")) else st["trim"]
    if pos % 4 == 2 and Y + 1 <= yy <= Y + 2:
        return "glass_pane"
    w = st["wall"]
    return log(w, "x" if z in (z1, z2) else "z") if w.endswith(("_log", "_wood")) else w


def shell(d, pack, x1, z1, x2, z2, y0, n, H=5, roof="flat", axis="x", doors=(), stair=True, chimneys=True,
          st=None):
    """A multi-storey block (walls, floors, windows, switch-back stair with rails, doors, roof) in this building's
    own materials. It furnishes nothing: each building's rooms are laid out by hand with fit(). Returns
    (walking levels, interior origin x, origin z, forbidden-cells-by-floor function)."""
    S = STY[pack]
    st = _st(pack, st)
    levels = []
    A, B, zs = x2 - 1, x2 - 2, z1 + 2
    for f in range(n):
        Y = y0 + H * f
        levels.append(Y)
        for x, z in cells(x1, z1, x2, z2):
            per = x in (x1, x2) or z in (z1, z2)
            if pack == "Neoterra":
                b = st["band"][f % 2] if per else S["floor"]
            else:
                b = st["band"] if per else S["floor"]
            d.set(x, Y - 1, z, b)
        for yy in range(Y, Y + H - 1):
            for x, z in cells(x1, z1, x2, z2):
                if x in (x1, x2) or z in (z1, z2):
                    d.set(x, yy, z, _wall_cell(d, pack, x, yy, z, x1, z1, x2, z2, Y, H, f, st))
                else:
                    d.set(x, yy, z, AIR)
    top = y0 + H * n - 1
    for x, z in cells(x1, z1, x2, z2):
        d.set(x, top, z, (st["edge"] if pack == "Neoterra" else st["band"])
              if (x in (x1, x2) or z in (z1, z2)) else S["floor"])
    rail = S["rail"]
    if stair and n > 1:
        for f in range(n - 1):
            Y = y0 + H * f
            if f % 2 == 0:
                flight(d, A, zs, Y, H, "south", S["stairb"])
                flight_rails(d, A, zs, Y, H, "south", rail)
            else:
                flight(d, B, zs + H - 1, Y, H, "north", S["stairb"])
                flight_rails(d, B, zs + H - 1, Y, H, "north", rail)
    for (x, z, fc) in doors:
        d.door(x, y0, z, fc, st["door"])
        if pack == "Neoterra":
            d.set(x, y0 + 2, z, st["glass"])
    W = x2 - x1 - 1
    zone = set()
    if stair and n > 1:
        zone = {(lx, lz) for lx in (W - 3, W - 2, W - 1) for lz in range(0, H + 2)}
    door_keep = set()
    for (x, z, fc) in doors:
        ix, iz = x + D4[OPP[fc]][0] - (x1 + 1), z + D4[OPP[fc]][1] - (z1 + 1)
        door_keep |= {(ix + a, iz + b) for a in (-1, 0, 1) for b in (-1, 0, 1)}

    def forbid(f):
        return zone | (door_keep if f == 0 else set())
    # roof
    if roof == "flat":
        for x, z in cells(x1, z1, x2, z2):
            if x in (x1, x2) or z in (z1, z2):
                d.set(x, top + 1, z, st["parapet"])
                d.set(x, top + 2, z, slab(st["coping"]))
        if st["green"]:
            for x, z in cells(x1 + 1, z1 + 1, x2 - 1, z2 - 1):
                d.set(x, top, z, "moss_block")
    elif roof in ("gable", "hip"):
        rs, rsl = st["roof"] + "_stairs", st["roof"] + "_slab"
        if roof == "gable":
            ridge = d.gable(x1, z1, x2, z2, top + 1, axis, rs, rsl, st["gable"])
        else:
            ridge = d.hip(x1, z1, x2, z2, top + 1, rs, rsl)
        if chimneys:
            ends = ((x1, (z1 + z2) // 2), (x2, (z1 + z2) // 2)) if axis == "x" else \
                (((x1 + x2) // 2, z1), ((x1 + x2) // 2, z2))
            for i_, (cx, cz) in enumerate(ends):
                if pack == "Cascadia" and i_ == 1:
                    continue
                for yy in range(top + 1, ridge + 3):
                    d.set(cx, yy, cz, st["chimney"] if pack == "Hearthwood" else stone(cx, yy, cz))
                d.set(cx, ridge + 3, cz, "flower_pot" if pack == "Hearthwood" else
                      "cobblestone_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
        if pack == "Cascadia" and roof == "gable":                # king post in each gable end
            ends = (z1, z2) if axis == "z" else (x1, x2)
            mid = (x1 + x2) // 2 if axis == "z" else (z1 + z2) // 2
            for e in ends:
                for yy in range(top + 1, ridge):
                    p_ = (mid, yy, e) if axis == "z" else (e, yy, mid)
                    d.set(*p_, log("spruce_log", "y"))
    return levels, (x1 + 1, z1 + 1), forbid


def fit_floors(d, pack, levels, origin, forbid, H, plans, floors, wd, tt, extra=()):
    """Apply the hand-written plan named floors[f] to floor f (extra = cells kept clear on every floor)."""
    ox, oz = origin
    for f, Y in enumerate(levels):
        fit(d, pack, ox, Y, oz, H, plans[floors[f]], wd, tt, forbid(f) | set(extra))


def lamp_post(d, x, z, y, pack, h=3):
    for k in range(h):
        d.set(x, y + k, z, {"Neoterra": "iron_bars",
                            "Hearthwood": "dark_oak_fence", "Cascadia": "spruce_fence"}[pack])
    if pack == "Neoterra":
        d.set(x, y + h, z, "sea_lantern")
        d.set(x, y + h + 1, z, slab("smooth_stone"))
    else:
        d.set(x, y + h, z, lantern(False))


def bench(d, x, z, y, pack, facing_back, n=2):
    S = STY[pack]
    dx, dz = D4[CW[facing_back]]
    for i in range(n):
        d.chair(x + dx * i, y, z + dz * i, facing_back, S["wood"], sit=False)
    for side in (-1, n):
        cx, cz = x + dx * side, z + dz * side
        if d.air(cx, y, cz):
            d.set(cx, y, cz, S["plants"][0] if pack != "Neoterra" else "potted_bamboo")


def flowerbed(d, x1, z1, x2, z2, y, pack, border=True):
    fl = {"Neoterra": ("allium", "white_tulip", "azure_bluet"),
          "Hearthwood": ("poppy", "cornflower", "oxeye_daisy", "allium", "red_tulip"),
          "Cascadia": ("fern", "lily_of_the_valley", "blue_orchid", "short_grass")}[pack]
    for x, z in cells(x1, z1, x2, z2):
        d.set(x, y - 1, z, "grass_block[snowy=false]" if pack != "Neoterra" else "moss_block")
        if d.air(x, y, z):
            d.set(x, y, z, fl[(x * 3 + z) % len(fl)])
    if border:
        bb = {"Neoterra": "smooth_quartz_slab[type=bottom,waterlogged=false]",
              "Hearthwood": "stone_brick_slab[type=bottom,waterlogged=false]",
              "Cascadia": "cobblestone_slab[type=bottom,waterlogged=false]"}[pack]
        for x, z in cells(x1 - 1, z1 - 1, x2 + 1, z2 + 1):
            if (x in (x1 - 1, x2 + 1) or z in (z1 - 1, z2 + 1)) and d.bp.inside(x, y, z) and d.air(x, y, z):
                d.set(x, y, z, bb)


def path_line(d, pts, y, block):
    for x, z in pts:
        if d.bp.inside(x, y, z):
            d.set(x, y, z, block)



# Each building of each complex has its own material set (the pack's family, never one palette for all).
NT_CLUB = dict(trim="gray_concrete", fin="mangrove_planks", glass="glass_pane", clad="orange_terracotta",
               band=("gray_concrete", "orange_terracotta"), edge="smooth_stone", parapet="gray_concrete",
               coping="smooth_stone", door="mangrove", green=True)
NT_TOWER_B = dict(trim="polished_deepslate", fin="cyan_concrete", glass="gray_stained_glass_pane",
                  clad="polished_deepslate", band=("polished_deepslate", "cyan_concrete"), edge="polished_deepslate",
                  parapet="polished_deepslate", coping="polished_deepslate", door="dark_oak")
NT_TOWER_C = dict(trim="white_terracotta", fin="lime_concrete", glass="light_gray_stained_glass_pane",
                  clad="white_terracotta", band=("white_terracotta", "lime_terracotta"), edge="smooth_quartz",
                  parapet="white_terracotta", coping="cut_copper", door="cherry", green=True)
HW_WEST = dict(wall0="sandstone", wall="smooth_sandstone", plinth="cut_sandstone", quoin="chiseled_sandstone",
               lintel="cut_sandstone", band="cut_sandstone", roof="brick", gable="smooth_sandstone", door="oak",
               box="oak", chimney="sandstone")
HW_EAST = dict(wall0="bricks", wall="white_terracotta", frame="dark_oak_log", plinth="stone_bricks", quoin="bricks",
               lintel="dark_oak_planks", band="dark_oak_planks", roof="dark_prismarine", gable="white_terracotta",
               door="spruce", box="spruce", chimney="bricks")
HW_SOUTH = dict(wall0="stone_bricks", wall="yellow_terracotta", frame="oak_log", plinth="mossy_stone_bricks",
                quoin="stone_bricks", lintel="oak_planks", band="stone_bricks", roof="granite", gable="yellow_terracotta",
                door="oak", box="oak", chimney="stone_bricks")
HW_LINK = dict(wall0="mud_bricks", wall="mud_bricks", plinth="stone_bricks", quoin="packed_mud", lintel="packed_mud",
               band="packed_mud", roof="mud_brick", gable="mud_bricks", door="cherry", box="jungle")
CA_HALL = dict(wall="mangrove_planks", trim="dark_oak_log", band="red_terracotta", roof="cobbled_deepslate",
               gable="mangrove_planks", shutter="dark_oak", door="mangrove")
CA_EAST = dict(wall="birch_planks", trim="spruce_log", band="green_terracotta", roof="spruce", gable="birch_planks",
               shutter="dark_oak", door="birch")
CA_TOWER = dict(wall0="tuff", wall="dark_oak_planks", trim="stripped_spruce_log", band="yellow_terracotta",
                roof="dark_prismarine", gable="dark_oak_planks", shutter="spruce", door="dark_oak")
CA_BATH = dict(wall="spruce_planks", trim="spruce_log", band="dark_oak_planks", roof="mangrove",
               gable="stripped_spruce_wood[axis=y]", shutter="mangrove", door="spruce")
CA_BARN = dict(wall="red_terracotta", trim="white_terracotta", band="white_terracotta", roof="spruce",
               gable="red_terracotta", shutter="birch", door="spruce")
CA_SOUTH = dict(wall="spruce_log", trim="stripped_spruce_log", band="dark_oak_planks", roof="deepslate_tile",
                gable="spruce_planks", shutter="mangrove", door="dark_oak")

# ---------------------------------------------------------------------------------------------- hand-made plans
def _row(op, pts, rest=""):
    """Lines for pieces I list one by one (pts = explicit (x, z) pairs)."""
    return "\n".join(f"{op} {x} {z} {rest}".rstrip() for x, z in pts)


# Neoterra sky tower – west residents' club (9 x 13 rooms, stair on the east side lx 6-8 / lz 0-6, door lx 4 lz 0)
NT_CLUB_PLANS = {
    "gym": """
        X 0 1 andesite
        X 0 1 plate 1
        X 0 2 andesite
        X 0 2 plate 1
        X 0 3 sslab
        X 0 5 sslab
        X 0 6 sslab
        R 2 4 4 6 lime
        X 3 9 target 1
        X 3 9 chain 2
        X 3 9 chain 3
        X 0 9 chest:e
        X 0 10 chest:e
        X 0 11 chest:e
        S 0 12 wool
        X 1 12 black_carpet
        X 2 12 black_carpet
        X 3 12 black_carpet
        X 6 12 sink
        S 7 12 wool
        P 8 12 potted_bamboo
        P 0 0 potted_bamboo
        P 2 0 potted_bamboo
        G 0 7 e
        L 2 3
        L 2 9
        L 7 10
    """,
    "lounge": """
        F 0 5 e
        K 0 3
        K 0 7
        T 2 5 potted_bamboo
        C 3 4 e
        C 3 5 e
        C 3 6 e
        C 2 3 n
        C 2 7 s
        R 1 4 3 6 cyan
        P 0 0 potted_bamboo
        P 0 12 potted_white_tulip
        T 5 11 lamp
        C 4 12 s
        C 6 9 n
        C 7 9 n
        T 7 11 potted_azure_bluet
        X 8 12 jukebox
        G 0 9 e
        L 2 5
        L 5 10
        L 7 10
    """,
    "library": """
        %s
        %s
        T 3 5 lamp
        T 3 6 candle
        C 2 5 w
        C 2 6 w
        C 4 5 e
        C 4 6 e
        X 5 1 lectern:w
        C 7 11 e
        T 8 11 candle
        P 6 12 potted_bamboo
        R 2 4 4 7 light_gray
        L 3 3
        L 3 9
        L 7 10
    """ % (_row("K", [(0, z) for z in range(1, 12)]), _row("K", [(x, 12) for x in range(1, 6)])),
    "bar": """
        %s
        %s
        %s
        X 0 10 mangrove_planks
        X 1 10 mangrove_planks
        X 2 10 mangrove_planks
        X 3 10 mangrove_planks
        C 0 9 n
        C 1 9 n
        C 2 9 n
        C 3 9 n
        C 0 2 n
        T 0 3 candle
        C 0 4 s
        C 0 5 n
        T 0 6 candle
        C 0 7 s
        X 8 12 jukebox
        P 6 12 potted_bamboo
        P 5 0 potted_bamboo
        L 2 4
        L 2 11
        L 7 10
    """ % (_row("X", [(x, 12) for x in range(0, 5)], "barrel:n"), _row("X", [(x, 12) for x in range(0, 5)], "counter 1"),
           _row("X", [(x, 12) for x in range(0, 5)], "brew 2")),
    "office": """
        Q 0 1 e 2
        Q 0 2 e 2
        X 0 3 barrel:e
        X 0 4 chest:e
        T 2 5 lamp
        T 3 5
        C 2 4 n
        C 3 6 s
        T 2 9
        T 3 9 lamp
        C 2 8 n
        C 3 10 s
        X 0 12 carto
        X 1 12 lectern:n
        P 5 12 potted_bamboo
        T 7 11 candle
        C 6 11 w
        C 8 11 e
        P 0 0 potted_bamboo
        L 2 3
        L 2 9
        L 7 10
    """,
    "cinema": """
        X 0 4 white_wool 1
        X 0 5 white_wool 1
        X 0 6 white_wool 1
        X 0 4 white_wool 2
        X 0 5 white_wool 2
        X 0 6 white_wool 2
        %s
        %s
        X 0 12 jukebox
        S 1 12 pot
        X 2 12 smoker:n
        P 5 12 potted_bamboo
        P 8 12 potted_bamboo
        C 7 10 n
        C 8 10 n
        L 4 10
        L 7 11
    """ % (_row("C", [(3, z) for z in range(3, 9)], "e"), _row("C", [(5, z) for z in range(3, 9)], "e")),
}
NT_CLUB_FLOORS = ["gym", "lounge", "library", "bar", "office", "cinema", "lounge"]

# Neoterra sky tower – east club tower B (9 x 13, same frame as the club but its own rooms)
NT_B_PLANS = {
    "restaurant": """
        C 0 3 w
        T 1 3 candle
        C 2 3 e
        C 0 6 w
        T 1 6 candle
        C 2 6 e
        C 0 9 w
        T 1 9 candle
        C 2 9 e
        T 4 5 candle
        C 4 4 n
        C 4 6 s
        T 4 9
        C 4 8 n
        C 4 10 s
        X 1 1 lectern:s
        %s
        X 6 12 barrel:n
        T 7 10 candle
        C 6 10 w
        C 8 10 e
        P 8 12 potted_bamboo
        P 0 0 potted_bamboo
        R 3 3 5 11 cyan
        L 1 4
        L 1 9
        L 4 7
        L 7 10
    """ % _row("X", [(x, 12) for x in range(0, 6)], "counter"),
    "kitchen": """
        X 0 1 furnace:e
        X 0 2 smoker:e
        X 0 3 furnace:e
        X 0 4 sink
        S 0 5 pot
        S 0 6 pot
        X 2 8 counter
        X 3 8 counter
        X 4 8 counter
        X 2 8 pot 1
        X 0 9 barrel:e
        X 0 10 barrel:e
        X 0 11 chest:e
        X 0 12 bwool
        X 5 12 cauldron
        T 7 11 candle
        C 6 11 w
        C 8 11 e
        L 2 3
        L 3 9
        L 7 10
    """,
    "office": """
        Q 0 2 e 2
        Q 0 3 e 2
        X 0 4 barrel:e
        X 0 5 chest:e
        T 3 3 lamp
        C 3 2 n
        T 3 7
        T 3 8 lamp
        C 2 7 w
        C 2 8 w
        C 4 7 e
        C 4 8 e
        X 0 12 carto
        X 1 12 lectern:n
        S 2 12 pot
        P 5 12 potted_bamboo
        C 7 10 n
        C 8 10 n
        T 7 12 potted_white_tulip
        L 3 3
        L 3 8
        L 7 11
    """,
    "cowork": """
        %s
        %s
        %s
        P 0 2 potted_bamboo
        S 0 10 pot
        S 0 11 candle
        X 0 12 barrel:e
        T 4 10
        T 5 10 lamp
        C 4 9 n
        C 5 9 n
        C 4 11 s
        C 5 11 s
        X 7 12 carto
        P 8 12 potted_bamboo
        L 1 6
        L 4 10
        L 7 10
    """ % (_row("T", [(1, z) for z in range(4, 9)]), _row("C", [(0, z) for z in range(4, 9)], "w"),
           _row("C", [(2, z) for z in range(4, 9)], "e")),
    "sky": """
        F 0 6 e
        T 2 6 potted_bamboo
        C 3 5 e
        C 3 6 e
        C 3 7 e
        C 2 4 n
        C 2 8 s
        R 1 5 3 7 gray
        P 0 2 potted_bamboo
        P 0 10 potted_bamboo
        T 5 11 lamp
        C 6 12 s
        C 7 12 s
        C 8 12 s
        T 7 10 potted_white_tulip
        L 2 6
        L 7 10
    """,
    "bar": """
        X 2 6 counter
        X 3 6 counter
        X 4 6 counter
        C 2 5 n
        C 3 5 n
        C 4 5 n
        C 2 7 s
        C 3 7 s
        C 4 7 s
        %s
        %s
        C 6 10 w
        T 7 10 candle
        C 8 10 e
        C 6 12 w
        T 7 12
        C 8 12 e
        P 0 12 potted_bamboo
        P 5 12 potted_bamboo
        X 0 1 jukebox
        L 3 3
        L 3 9
        L 7 11
    """ % (_row("X", [(0, z) for z in range(4, 9)], "barrel:e"), _row("X", [(0, z) for z in range(4, 9)], "brew 1")),
}


# Neoterra sky tower – south garden-pavilion tower C (11 x 13, stair lx 8-10 / lz 0-6, door lx 5 lz 0)
NT_C_PLANS = {
    "cafe": """
        X 0 2 counter
        X 0 2 brew 1
        X 0 3 counter
        X 0 4 counter
        X 0 4 pot 1
        X 0 5 smoker:e
        X 0 6 barrel:e
        C 1 3 e
        C 1 4 e
        T 4 4 candle
        C 3 4 w
        C 5 4 e
        T 4 8 candle
        C 3 8 w
        C 5 8 e
        T 2 10
        C 1 10 w
        C 3 10 e
        T 9 9
        C 8 9 w
        C 10 9 e
        T 9 12 potted_white_tulip
        C 8 12 w
        C 10 12 e
        P 0 12 potted_bamboo
        P 7 0 potted_bamboo
        P 0 0 potted_bamboo
        L 1 4
        L 4 6
        L 4 10
        L 9 10
    """,
    "studio": """
        X 0 2 loom:e
        X 0 4 carto
        X 2 3 lectern:s
        C 2 4 s
        X 2 7 lectern:s
        C 2 8 s
        X 5 5 white_wool
        X 5 5 pot 1
        S 0 10 pot
        S 0 11 candle
        X 0 12 chest:e
        R 4 9 6 11 magenta
        X 9 12 barrel
        P 10 12 potted_bamboo
        T 9 9 candle
        C 9 8 n
        L 2 5
        L 5 10
        L 9 10
    """,
    "library": """
        %s
        %s
        T 3 4 lamp
        T 4 4
        C 3 3 n
        C 4 3 n
        C 3 5 s
        C 4 5 s
        T 3 8
        T 4 8 lamp
        C 3 7 n
        C 4 7 n
        C 3 9 s
        C 4 9 s
        C 9 11 s
        T 10 11 lamp
        P 10 12 potted_bamboo
        P 8 12 potted_bamboo
        X 7 1 lectern:w
        L 3 4
        L 3 8
        L 9 10
    """ % (_row("K", [(0, z) for z in range(1, 13)]), _row("K", [(x, 12) for x in range(1, 7)])),
    "yoga": """
        R 1 2 6 5 lime
        R 1 7 6 10 lime
        X 0 12 chest:e
        S 1 12 wool
        S 2 12 wool
        X 3 12 sink
        P 0 0 potted_bamboo
        P 0 6 potted_bamboo
        P 7 0 potted_bamboo
        P 7 12 potted_bamboo
        P 10 12 potted_bamboo
        X 9 9 bell
        C 9 11 s
        C 10 11 s
        L 3 3
        L 3 9
        L 9 10
    """,
    "lounge": """
        F 0 6 e
        K 0 4
        K 0 8
        T 2 6 pot
        C 3 5 e
        C 3 6 e
        C 3 7 e
        C 2 4 n
        C 2 8 s
        R 1 5 3 7 white
        T 6 10 lamp
        C 5 10 w
        C 7 10 e
        C 9 8 n
        C 10 8 n
        T 9 10 potted_white_tulip
        C 9 12 s
        C 10 12 s
        X 0 12 jukebox
        P 0 0 potted_bamboo
        P 7 0 potted_bamboo
        L 2 6
        L 6 10
        L 9 10
    """,
    "bar": """
        %s
        %s
        X 2 2 counter
        X 2 3 counter
        X 2 4 counter
        X 2 5 counter
        C 3 2 e
        C 3 3 e
        C 3 4 e
        C 3 5 e
        T 6 9 candle
        C 5 9 w
        C 7 9 e
        T 9 10 candle
        C 8 10 w
        C 10 10 e
        T 6 12
        C 5 12 w
        C 7 12 e
        P 0 12 potted_bamboo
        P 7 0 potted_bamboo
        L 2 4
        L 6 10
        L 9 10
    """ % (_row("X", [(0, z) for z in range(1, 7)], "barrel:e"), _row("X", [(0, z) for z in range(1, 7)], "brew 1")),
}


# ---- round 5: the tall towers' middle storeys are composed from hand-made half-floor rooms. Every storey pairs a
# north room (beside the stair) with a south room behind a glass partition; the pairings and rug colours are listed
# by hand below so no two storeys are alike.
# Tower B (9 x 13; stair lx 6-8 / lz 0-6): north rooms use lx 0-5 / lz 0-6 (lx 5 lz 6 kept free), partition lz 7
# lx 0-4, south rooms lx 0-8 / lz 8-12 (lx 5 lz 8 kept free).
NT_B_NORTH = {
    "reception": """
        X 1 2 counter
        X 2 2 counter
        X 3 2 counter
        X 3 2 lamp 1
        C 2 1 n
        P 0 0 potted_bamboo
        P 5 0 potted_white_tulip
        C 0 4 w
        C 0 5 w
        T 1 5 potted_azure_bluet
        R 1 4 3 5 {rug}
        L 2 2
        L 2 5
    """,
    "meeting": """
        T 1 3
        T 2 3 lamp
        T 3 3
        C 1 2 n
        C 2 2 n
        C 3 2 n
        C 1 4 s
        C 2 4 s
        C 3 4 s
        X 0 3 black_concrete 1
        K 0 0 3
        P 5 0 potted_bamboo
        X 0 6 barrel:e
        L 2 3
    """,
    "print": """
        X 0 1 carto
        X 0 2 barrel:e
        X 0 3 barrel:e
        X 0 4 chest:e
        X 0 5 chest:e
        S 2 0 pot
        S 3 0 candle
        X 4 0 loom:s
        C 2 3 w
        T 3 3 lamp
        R 2 4 3 5 {rug}
        P 0 6 potted_bamboo
        L 2 3
    """,
    "kitchenette": """
        X 0 0 sink
        X 1 0 smoker:s
        X 2 0 counter
        X 2 0 pot 1
        X 3 0 iron_block
        X 3 0 iron_block 1
        T 2 3 potted_white_tulip
        T 2 4
        C 1 3 w
        C 3 3 e
        C 1 4 w
        C 3 4 e
        X 0 6 barrel:e
        L 2 3
    """,
    "manager": """
        T 1 2 lamp
        T 2 2
        C 1 1 n
        C 1 3 s
        C 2 3 s
        K 0 6 3
        K 1 6 3
        Q 2 6 n 2
        X 4 0 barrel:s
        P 5 0 potted_bamboo
        R 1 4 3 5 {rug}
        L 2 2
        L 2 5
    """,
    "lounge": """
        C 0 2 w
        T 0 3 potted_azure_bluet
        C 0 4 w
        C 1 6 s
        C 2 6 s
        C 3 6 s
        T 2 5 candle
        K 3 0 3
        K 4 0 3
        P 5 0 potted_bamboo
        R 1 2 3 4 {rug}
        L 2 3
        L 2 5
    """,
    "quiet": """
        K 0 0 3
        K 0 1 3
        K 0 2 3
        K 1 0 3
        K 2 0 3
        T 2 4 lamp
        C 1 4 w
        C 3 4 e
        X 4 0 lectern:s
        P 0 6 potted_white_tulip
        R 1 5 3 5 {rug}
        L 2 3
    """,
}
NT_B_SOUTH = {
    "openplan": """
        T 0 9
        T 1 9 lamp
        C 0 10 s
        C 1 10 s
        T 3 9
        T 4 9 lamp
        C 3 10 s
        C 4 10 s
        T 7 9
        T 7 10 lamp
        C 8 9 e
        C 8 10 e
        X 0 12 barrel:n
        X 1 12 chest:n
        P 4 12 potted_bamboo
        P 8 12 potted_bamboo
        L 1 10
        L 4 10
        L 7 11
    """,
    "board": """
        T 2 10
        T 3 10 lamp
        T 4 10
        T 5 10 potted_white_tulip
        T 6 10
        C 2 9 n
        C 3 9 n
        C 4 9 n
        C 6 9 n
        C 2 11 s
        C 3 11 s
        C 4 11 s
        C 5 11 s
        C 6 11 s
        C 1 10 w
        C 7 10 e
        X 4 12 note
        P 0 12 potted_bamboo
        P 8 12 potted_bamboo
        L 3 10
        L 6 10
    """,
    "studio": """
        X 0 9 loom:e
        X 0 10 carto
        X 0 11 lectern:e
        X 0 12 chest:e
        T 3 10
        T 4 10 lamp
        C 3 11 s
        C 4 11 s
        X 7 12 barrel:n
        S 8 12 pot
        X 8 9 white_wool
        X 8 9 pot 1
        R 2 9 4 9 {rug}
        L 2 10
        L 6 10
    """,
    "games": """
        T 1 10 candle
        C 0 10 w
        C 2 10 e
        C 1 9 n
        C 1 11 s
        T 5 10
        C 4 10 w
        C 6 10 e
        X 8 12 jukebox
        X 7 12 note
        X 0 12 barrel:n
        P 8 8 potted_bamboo
        R 4 11 6 12 {rug}
        L 1 10
        L 5 10
    """,
    "gym": """
        X 0 9 andesite
        X 0 9 plate 1
        X 0 10 andesite
        X 0 10 plate 1
        X 1 12 target
        X 2 12 chest:n
        X 3 12 chest:n
        S 4 12 wool
        X 7 12 sink
        P 8 12 potted_bamboo
        X 8 9 target
        X 8 9 chain 1
        R 3 9 6 11 {rug}
        L 2 10
        L 6 10
    """,
    "library": """
        K 0 12 3
        K 1 12 3
        K 2 12 3
        K 3 12 3
        K 0 11 3
        K 0 10 3
        T 4 10 lamp
        T 5 10
        C 4 9 n
        C 5 9 n
        C 4 11 s
        C 5 11 s
        C 8 11 e
        T 8 12 candle
        P 8 9 potted_bamboo
        L 4 10
        L 7 11
    """,
    "fireside": """
        F 8 10 w
        C 6 9 w
        C 6 10 w
        C 6 11 w
        T 3 10 potted_azure_bluet
        C 2 10 w
        C 3 9 n
        K 0 12 3
        K 1 12 3
        P 0 8 potted_bamboo
        X 4 12 jukebox
        R 4 9 5 11 {rug}
        L 5 10
        L 2 10
    """,
}
NT_B_MID = [("reception", "openplan", "cyan"), ("meeting", "board", "gray"), ("print", "studio", "yellow"),
            ("kitchenette", "games", "orange"), ("manager", "gym", "lime"), ("lounge", "library", "brown"),
            ("quiet", "fireside", "red"), ("reception", "games", "light_blue"), ("meeting", "gym", "purple"),
            ("print", "library", "green"), ("kitchenette", "fireside", "pink"), ("manager", "openplan", "blue"),
            ("lounge", "board", "magenta"), ("quiet", "studio", "white")]

# Tower C (11 x 13; stair lx 8-10 / lz 0-6): north rooms lx 0-7 / lz 0-6 (lx 7 lz 6 kept free), partition lz 7
# lx 0-6, south rooms lx 0-10 / lz 8-12 (lx 7 lz 8 kept free).
NT_C_NORTH = {
    "pottery": """
        X 0 1 furnace:e
        X 0 2 blast:e
        X 0 3 cauldron
        T 2 3 pot
        T 3 3 pot
        C 2 2 n
        C 3 4 s
        X 6 0 barrel:s
        S 5 0 pot
        P 0 6 potted_bamboo
        R 2 5 4 5 {rug}
        L 2 3
    """,
    "florist": """
        X 0 0 composter
        X 0 1 barrel:e
        X 2 2 moss_block
        X 3 2 moss_block
        X 4 2 moss_block
        X 2 2 flowering_azalea 1
        X 3 2 fern 1
        X 4 2 azalea 1
        T 2 5
        T 3 5 potted_red_tulip
        C 4 5 e
        X 6 0 sink
        P 7 0 potted_white_tulip
        L 3 3
    """,
    "music": """
        X 1 1 note
        X 2 1 note
        X 3 1 jukebox
        C 1 2 s
        C 2 2 s
        C 1 5 n
        C 2 5 n
        C 3 5 n
        K 0 6 2
        X 6 0 note
        R 1 3 3 4 {rug}
        L 2 3
    """,
    "nook": """
        K 0 0 3
        K 0 1 3
        K 0 2 3
        K 1 0 3
        T 3 3 lamp
        C 2 3 w
        C 4 3 e
        C 3 5 s
        P 6 0 potted_bamboo
        X 6 6 lectern:n
        R 2 4 4 4 {rug}
        L 3 3
    """,
    "playroom": """
        R 1 1 4 4 {rug}
        X 1 1 red_wool
        X 4 1 yellow_wool
        X 4 1 blue_wool 1
        X 0 6 chest:e
        X 1 6 chest:n
        T 2 4 cake
        C 2 5 s
        P 6 0 potted_white_tulip
        L 2 3
    """,
    "tearoom": """
        T 2 2 candle
        C 1 2 w
        C 3 2 e
        T 2 5 potted_azure_bluet
        C 1 5 w
        C 3 5 e
        X 6 0 counter
        X 6 0 brew 1
        X 5 0 smoker:s
        P 0 0 potted_bamboo
        L 2 3
        L 2 5
    """,
    "artstudio": """
        X 2 2 lectern:s
        C 2 3 s
        X 5 2 lectern:s
        C 5 3 s
        X 0 0 loom:e
        X 0 1 carto
        X 0 6 chest:e
        R 1 4 5 5 {rug}
        P 7 0 potted_bamboo
        L 3 3
    """,
    "tailor": """
        X 0 1 loom:e
        X 0 2 loom:e
        X 0 3 chest:e
        T 3 2
        T 4 2
        X 3 2 white_carpet 1
        C 3 3 s
        C 4 3 s
        X 6 0 barrel:s
        P 7 0 potted_white_tulip
        R 2 5 4 5 {rug}
        L 3 3
    """,
}
NT_C_SOUTH = {
    "yoga": """
        R 1 9 1 11 {rug}
        R 3 9 3 11 {rug}
        R 5 9 5 11 {rug}
        X 0 12 chest:e
        S 1 12 wool
        S 2 12 wool
        X 3 12 sink
        P 10 12 potted_bamboo
        P 0 8 potted_bamboo
        X 10 8 bell
        P 9 12 potted_white_tulip
        L 3 10
        L 8 10
    """,
    "cafe": """
        T 2 10 candle
        C 1 10 w
        C 3 10 e
        T 6 10
        C 5 10 w
        C 7 10 e
        X 0 12 counter
        X 1 12 counter
        X 0 12 brew 1
        X 2 12 smoker:n
        X 3 12 barrel:n
        T 9 11 potted_white_tulip
        C 9 10 n
        C 10 11 e
        L 2 10
        L 6 10
        L 9 11
    """,
    "library": """
        K 0 12 3
        K 1 12 3
        K 2 12 3
        K 3 12 3
        K 4 12 3
        K 0 10 3
        K 0 11 3
        T 3 10 lamp
        T 4 10
        C 3 9 n
        C 4 9 n
        C 3 11 s
        C 4 11 s
        Q 10 12 w 2
        T 8 10 candle
        C 9 10 e
        L 3 10
        L 9 10
    """,
    "cards": """
        T 2 10 candle
        C 1 10 w
        C 3 10 e
        C 2 9 n
        C 2 11 s
        T 6 11
        C 5 11 w
        C 7 11 e
        C 6 12 s
        X 10 12 jukebox
        X 9 12 note
        P 10 8 potted_bamboo
        L 2 10
        L 6 11
    """,
    "gallery": """
        G 0 10 e
        G 0 12 e
        G 10 10 w
        X 3 10 sslab
        X 3 10 pot 1
        X 6 10 sslab
        X 6 10 potted_flowering_azalea_bush 1
        C 4 12 s
        C 5 12 s
        X 9 12 lectern:n
        P 10 8 potted_bamboo
        R 3 9 6 9 {rug}
        L 3 10
        L 6 10
        L 9 11
    """,
    "lounge": """
        F 0 10 e
        C 2 9 e
        C 2 10 e
        C 2 11 e
        T 4 10 potted_azure_bluet
        K 0 12 2
        X 10 12 jukebox
        T 9 10
        C 9 11 s
        C 10 10 e
        R 3 9 5 11 {rug}
        L 2 10
        L 9 10
    """,
    "workshop": """
        X 0 10 craft
        X 0 11 smith
        X 0 12 fletch
        X 1 12 grind:n
        X 2 12 chest:n
        T 4 10
        T 5 10 lamp
        C 4 11 s
        C 5 11 s
        X 10 12 barrel:n
        X 10 11 barrel:w
        P 10 8 potted_bamboo
        L 3 10
        L 8 10
    """,
    "cinema": """
        X 0 9 white_wool 1
        X 0 10 white_wool 1
        X 0 11 white_wool 1
        X 0 9 white_wool 2
        X 0 10 white_wool 2
        X 0 11 white_wool 2
        C 3 9 e
        C 3 10 e
        C 3 11 e
        C 5 9 e
        C 5 10 e
        C 5 11 e
        X 10 12 jukebox
        S 9 12 pot
        L 4 10
        L 8 11
    """,
}
NT_C_MID = [("pottery", "yoga", "lime"), ("florist", "cafe", "white"), ("music", "library", "red"),
            ("nook", "cards", "green"), ("playroom", "gallery", "yellow"), ("tearoom", "lounge", "pink"),
            ("artstudio", "workshop", "orange"), ("tailor", "cinema", "purple"), ("pottery", "cards", "light_blue"),
            ("florist", "gallery", "cyan"), ("music", "lounge", "brown"), ("nook", "workshop", "gray"),
            ("playroom", "cinema", "magenta"), ("tearoom", "yoga", "blue"), ("artstudio", "cafe", "light_gray"),
            ("tailor", "library", "black")]


def _compose(plans, north, south, mid, wall):
    names = []
    for i, (a, b, rug) in enumerate(mid):
        key = f"{a}+{b}#{i}"
        plans[key] = wall + north[a].replace("{rug}", rug) + south[b].replace("{rug}", rug)
        names.append(key)
    return names


NT_B_MIDNAMES = _compose(NT_B_PLANS, NT_B_NORTH, NT_B_SOUTH, NT_B_MID, "W 0 7 4 7 light_gray_stained_glass\n")
NT_C_MIDNAMES = _compose(NT_C_PLANS, NT_C_NORTH, NT_C_SOUTH, NT_C_MID, "W 0 7 6 7 white_stained_glass\n")


def nt_b_floors(n):
    return (["restaurant", "kitchen"] + NT_B_MIDNAMES[:max(0, n - 4)] + ["sky", "bar"])[:n] if n >= 4 else \
        ["restaurant", "kitchen", "sky"][:n]


def nt_c_floors(n):
    return (["cafe"] + NT_C_MIDNAMES[:max(0, n - 2)] + ["bar"])[:n]



# Hearthwood sky tower – west wing "Albion Club" (11 x 23, stair lx 8-10 / lz 0-6, door lx 5 lz 0, a partition at
# lz 11 makes two rooms per floor; lz 21-22 at lx 4-6 stays free for the door into the link range)
HW_W_PLANS = {
    "dining": """
        W 0 11 10 11
        D 3 11 s
        R 5 2 5 10 red
        X 0 1 barrel:e
        C 0 3 w
        T 0 5 lamp
        C 0 7 w
        X 0 9 fence
        X 0 9 lamp 1
        K 7 3
        K 7 4
        P 7 9 potted_fern
        P 0 10 potted_red_tulip
        G 0 5 e
        L 5 4
        L 5 8
        %s
        %s
        %s
        C 3 14 n
        C 3 20 s
        X 0 13 chest:e
        S 0 15 pot
        S 0 16 candle
        S 0 17 pot
        X 0 21 chest:e
        F 10 17 w
        C 8 15 w
        C 8 19 w
        P 10 22 potted_fern
        P 10 12 potted_allium
        R 2 14 4 20 red
        L 3 14
        L 3 20
        L 8 17
    """ % (_row("T", [(3, z) for z in range(15, 20)], "candle"), _row("C", [(2, z) for z in range(15, 20)], "w"),
           _row("C", [(4, z) for z in range(15, 20)], "e")),
    "library": """
        W 0 11 10 11
        D 3 11 s
        %s
        T 3 4 lamp
        T 4 4
        C 3 3 n
        C 4 5 s
        X 7 9 lectern:w
        P 7 10 potted_fern
        P 0 10 potted_fern
        L 3 5
        %s
        K 1 22
        K 2 22
        K 3 22
        K 7 22
        K 8 22
        K 9 22
        K 10 22
        F 10 16 w
        T 8 16 candle
        C 8 15 w
        C 8 17 w
        T 3 17 lamp
        T 4 17
        C 3 16 n
        C 4 16 n
        C 3 18 s
        C 4 18 s
        R 7 14 9 18 orange
        L 3 17
        L 8 13
        L 8 20
    """ % (_row("K", [(0, z) for z in range(1, 10)]), _row("K", [(0, z) for z in range(12, 23)])),
    "lounge": """
        W 0 11 10 11
        D 3 11 s
        F 0 5 e
        K 0 3
        K 0 7
        T 2 5 potted_red_tulip
        C 3 4 e
        C 3 5 e
        C 3 6 e
        C 2 3 n
        C 2 7 s
        R 1 4 3 6 red
        T 6 9 lamp
        C 5 9 w
        C 7 9 e
        P 0 10 potted_fern
        P 7 1 potted_allium
        L 2 5
        L 6 8
        X 1 14 note
        X 2 14 note
        X 3 14 note
        C 2 15 s
        C 5 18 s
        C 6 18 s
        C 7 18 s
        C 5 20 s
        C 6 20 s
        C 7 20 s
        X 0 22 jukebox
        P 10 12 potted_fern
        P 10 22 potted_fern
        S 0 12 candle
        G 0 17 e
        L 3 15
        L 6 19
    """,
    "cards": """
        W 0 11 10 11
        D 3 11 s
        T 2 4 candle
        C 1 4 w
        C 3 4 e
        C 2 3 n
        C 2 5 s
        T 2 8
        C 1 8 w
        C 3 8 e
        C 2 7 n
        C 2 9 s
        T 6 8 candle
        C 5 8 w
        C 7 8 e
        S 0 1 pot
        X 0 10 chest:e
        P 7 1 potted_red_tulip
        L 2 6
        L 6 8
        F 0 17 e
        C 2 16 e
        C 2 18 e
        K 0 13
        K 0 21
        T 8 15 lamp
        C 8 14 n
        C 8 16 s
        T 8 20 candle
        C 7 20 w
        C 9 20 e
        X 3 22 barrel:n
        P 10 22 potted_fern
        G 0 15 e
        L 3 17
        L 8 17
    """,
    "guest": """
        W 0 11 10 11
        D 3 11 s
        T 0 3 lamp
        C 1 3 e
        T 0 7 candle
        C 1 7 e
        X 0 1 chest:e
        X 0 9 lectern:e
        K 7 1
        K 7 2
        P 7 10 potted_allium
        L 2 5
        C 1 14 n
        C 2 14 n
        C 3 14 n
        T 2 16 potted_allium
        C 1 18 s
        C 2 18 s
        C 3 18 s
        P 0 12 potted_fern
        P 0 22 potted_fern
        P 10 22 potted_red_tulip
        P 10 12 potted_fern
        T 8 17 lamp
        C 8 16 n
        C 8 18 s
        R 1 15 3 17 orange
        L 2 16
        L 8 17
    """,
}
HW_W_FLOORS = ["dining", "library", "lounge", "cards", "guest"]

# Hearthwood sky tower – east wing (billiards, smoking & map rooms, reading rooms, trophy room, tea room)
HW_E_PLANS = {
    "billiard": """
        W 0 12 10 12
        D 2 12 s
        X 2 4 green_wool
        X 3 4 green_wool
        X 2 5 green_wool
        X 3 5 green_wool
        X 2 6 green_wool
        X 3 6 green_wool
        X 2 7 green_wool
        X 3 7 green_wool
        X 0 3 fence
        X 0 4 fence
        C 0 7 w
        C 0 8 w
        S 0 10 candle
        X 7 1 barrel
        P 7 11 potted_fern
        L 2 5
        L 3 7
        %s
        %s
        %s
        %s
        P 10 13 potted_fern
        T 8 20 candle
        C 7 20 w
        C 9 20 e
        X 2 22 jukebox
        L 2 16
        L 8 19
    """ % (_row("X", [(0, z) for z in range(14, 19)], "barrel:e"), _row("X", [(0, z) for z in range(14, 19)], "brew 1"),
           _row("X", [(2, z) for z in range(14, 19)], "planks"), _row("C", [(3, z) for z in range(14, 19)], "e")),
    "smoking": """
        W 0 12 10 12
        D 2 12 s
        F 0 6 e
        C 2 5 e
        C 2 7 e
        R 1 5 2 7 orange
        K 0 2
        K 0 3
        K 0 9
        K 0 10
        T 6 9 lamp
        C 6 8 n
        C 6 10 s
        P 7 1 potted_fern
        L 2 6
        L 6 9
        X 2 16 carto
        X 3 16 carto
        C 2 15 n
        C 3 17 s
        X 0 14 lectern:e
        X 0 20 chest:e
        X 0 21 chest:e
        G 0 17 e
        K 10 14
        K 10 15
        K 10 18
        K 10 19
        P 10 22 potted_allium
        T 8 21 candle
        L 3 16
        L 8 18
    """,
    "reading": """
        W 0 12 10 12
        D 2 12 s
        %s
        T 4 4 lamp
        C 4 3 n
        C 4 5 s
        T 4 8 lamp
        C 4 7 n
        C 4 9 s
        X 7 1 lectern:w
        P 7 11 potted_fern
        L 4 6
        X 0 14 lectern:e
        X 0 16 lectern:e
        X 0 18 lectern:e
        C 3 15 e
        C 3 17 e
        T 7 17 candle
        C 6 17 w
        C 8 17 e
        C 7 16 n
        C 7 18 s
        P 10 13 potted_fern
        P 0 22 potted_red_tulip
        K 10 20
        K 10 21
        K 10 22
        L 3 16
        L 7 17
    """ % _row("K", [(0, z) for z in range(1, 12)]),
    "trophy": """
        W 0 12 10 12
        D 2 12 s
        G 0 2 e
        G 0 5 e
        G 0 8 e
        S 0 4 pot
        S 0 7 candle
        S 7 1 skull:n
        C 3 5 n
        C 4 5 n
        T 3 7
        T 4 7 candle
        C 3 9 s
        C 4 9 s
        L 3 7
        X 0 14 barrel:e
        X 0 15 barrel:e
        X 0 16 chest:e
        X 0 18 fence
        X 0 19 fence
        X 0 20 fence
        T 5 17 lamp
        C 5 16 n
        C 5 18 s
        P 10 13 potted_fern
        P 10 22 potted_fern
        G 10 17 w
        L 3 17
        L 8 17
    """,
    "tea": """
        W 0 12 10 12
        D 2 12 s
        T 3 5 candle
        T 4 5
        C 3 4 n
        C 4 4 n
        C 3 6 s
        C 4 6 s
        C 2 5 w
        C 5 5 e
        S 0 1 pot
        S 0 9 candle
        P 7 1 potted_red_tulip
        P 0 11 potted_fern
        L 3 5
        T 2 16 candle
        C 1 16 w
        C 3 16 e
        T 2 20
        C 1 20 w
        C 3 20 e
        T 7 18 potted_allium
        C 6 18 w
        C 8 18 e
        X 0 13 furnace:e
        X 0 14 sink
        S 0 15 pot
        P 10 13 potted_fern
        P 10 22 potted_fern
        L 2 18
        L 7 18
    """,
}
HW_E_FLOORS = ["billiard", "smoking", "reading", "trophy", "tea"]

# Hearthwood sky tower – south range (57 x 11 per floor, partitions at lx 18 and 38 make three rooms; stair on
# the east end lx 54-56 / lz 0-6; ground doors at lx 9, 28, 47)
_HW_S_PART = """
        W 18 0 18 10
        D 18 5 e
        W 38 0 38 10
        D 38 5 e
"""
HW_S_PLANS = {
    "ground": _HW_S_PART + """
        R 9 2 9 10 red
        T 13 4 candle
        C 12 4 w
        C 14 4 e
        C 13 3 n
        C 13 5 s
        R 12 3 14 5 orange
        X 17 3 dark_oak_planks
        X 17 3 dark_oak_planks 1
        X 17 3 lamp 2
        T 5 7 potted_allium
        C 4 7 w
        C 6 7 e
        C 0 3 w
        C 0 4 w
        T 0 5 lamp
        C 0 6 w
        C 0 7 w
        X 0 1 barrel:e
        X 17 1 fence
        X 17 1 lamp 1
        T 13 9 lamp
        P 12 10 potted_fern
        P 14 10 potted_fern
        K 17 8
        K 17 9
        G 0 9 e
        P 5 10 potted_allium
        P 0 10 potted_red_tulip
        L 5 5
        L 13 5
        %s
        %s
        %s
        C 22 5 w
        C 34 5 e
        F 28 10 n
        X 19 1 chest:s
        S 20 10 pot
        S 21 10 candle
        S 35 10 pot
        S 36 10 candle
        P 19 10 potted_fern
        P 37 10 potted_fern
        P 37 1 potted_fern
        G 19 8 e
        G 37 8 w
        L 23 5
        L 28 5
        L 33 5
        X 39 10 furnace:n
        X 40 10 smoker:n
        X 41 10 furnace:n
        X 42 10 sink
        S 43 10 pot
        S 44 10 pot
        X 45 10 barrel:n
        S 46 10 pot
        X 42 5 counter
        X 43 5 counter
        X 44 5 counter
        X 42 5 pot 1
        X 39 1 barrel:e
        X 39 2 barrel:e
        X 39 3 chest:e
        X 39 7 bwool
        X 39 8 wool
        T 50 8
        C 49 8 w
        C 51 8 e
        P 56 10 potted_fern
        P 53 1 potted_allium
        L 42 3
        L 44 7
        L 50 8
    """ % (_row("T", [(x, 5) for x in range(23, 34)], "candle"), _row("C", [(x, 4) for x in range(23, 34)], "n"),
           _row("C", [(x, 6) for x in range(23, 34)], "s")),
    "first": _HW_S_PART + """
        %s
        %s
        T 6 5 lamp
        T 7 5
        T 8 5 candle
        C 6 4 n
        C 7 4 n
        C 8 4 n
        C 6 6 s
        C 7 6 s
        C 8 6 s
        T 13 8 lamp
        C 12 8 w
        C 14 8 e
        X 17 1 lectern:w
        L 7 5
        L 13 8
        %s
        %s
        X 26 0 note
        X 27 0 note
        X 29 0 note
        X 30 0 note
        C 28 1 s
        G 19 5 e
        G 37 5 w
        R 24 4 26 6 orange
        R 30 4 32 6 orange
        L 23 5
        L 28 5
        L 33 5
        X 40 2 note
        X 41 2 note
        X 42 2 note
        C 41 3 s
        C 44 6 s
        C 45 6 s
        C 46 6 s
        C 44 8 s
        C 45 8 s
        C 46 8 s
        X 39 10 jukebox
        S 40 10 candle
        P 53 10 potted_fern
        P 50 1 potted_fern
        L 42 4
        L 45 7
    """ % (_row("K", [(0, z) for z in range(1, 10)]), _row("K", [(x, 10) for x in range(1, 18)]),
           _row("C", [(19, z) for z in range(1, 10) if z != 5], "w"),
           _row("C", [(37, z) for z in range(1, 10) if z != 5], "e")),
    "second": _HW_S_PART + """
        Q 0 1 e 2
        Q 0 2 e 2
        X 0 3 chest:e
        X 0 4 chest:e
        T 5 5 lamp
        T 6 5
        C 5 4 n
        C 6 6 s
        X 1 10 carto
        X 2 10 lectern:n
        T 12 6 candle
        T 13 6
        C 12 5 n
        C 13 5 n
        C 12 7 s
        C 13 7 s
        P 17 1 potted_fern
        P 17 10 potted_fern
        L 5 5
        L 12 6
        X 28 1 lectern:s
        X 27 0 candle
        X 29 0 candle
        %s
        %s
        R 28 2 28 10 red
        G 19 3 e
        G 37 3 w
        L 24 5
        L 32 5
        %s
        X 39 10 cauldron
        X 40 10 sink
        S 41 10 wool
        S 42 10 wool
        X 45 4 fence
        X 46 4 fence
        X 47 4 fence
        X 48 4 fence
        P 53 10 potted_fern
        L 43 5
        L 50 8
    """ % (_row("C", [(x, z) for z in (4, 6, 8) for x in (22, 23, 24, 25)], "s"),
           _row("C", [(x, z) for z in (4, 6, 8) for x in (31, 32, 33, 34)], "s"),
           _row("X", [(39, z) for z in (1, 2, 3, 7, 8, 9)], "chest:e")),
    "third": _HW_S_PART + """
        R 3 3 5 6 light_blue
        X 1 1 chest:e
        X 0 3 hay
        X 0 4 note
        T 5 4 candle
        C 4 4 w
        C 6 4 e
        X 12 10 bell
        P 0 10 potted_allium
        P 17 1 potted_red_tulip
        X 15 6 carved_pumpkin[facing=west]
        L 5 5
        L 13 5
        %s
        %s
        X 28 3 white_wool
        X 28 3 pot 1
        X 28 7 white_wool
        X 28 7 skull:n 1
        C 24 5 n
        C 32 5 n
        L 23 5
        L 33 5
        T 43 4 candle
        C 42 4 w
        C 44 4 e
        C 43 3 n
        C 43 5 s
        T 47 8
        C 46 8 w
        C 48 8 e
        X 39 1 barrel:e
        S 39 10 pot
        P 53 10 potted_fern
        L 43 5
        L 48 8
    """ % (_row("G", [(19, z) for z in (2, 4, 7, 9)], "e"), _row("G", [(37, z) for z in (2, 4, 7, 9)], "w")),
    "fourth": _HW_S_PART + """
        X 0 1 barrel:e
        X 0 2 barrel:e
        X 0 3 chest:e
        X 0 7 chest:e
        X 0 8 barrel:e
        X 0 9 barrel:e
        X 4 10 hay
        X 5 10 bwool
        X 6 10 wool
        X 12 3 chest:s
        X 13 3 chest:s
        X 12 7 barrel
        X 13 7 barrel
        L 6 5
        L 13 5
        X 28 5 lectern:n
        C 27 7 s
        C 28 7 s
        C 29 7 s
        T 23 4 candle
        C 22 4 w
        C 24 4 e
        T 33 4 lamp
        C 32 4 w
        C 34 4 e
        P 19 10 potted_fern
        P 37 10 potted_fern
        L 28 5
        X 39 10 craft
        X 40 10 smith
        X 41 10 anvil:e
        X 42 10 grind:n
        X 43 10 barrel:n
        X 39 2 fence
        X 39 3 fence
        T 46 6 lamp
        T 47 6
        P 53 10 potted_fern
        L 43 5
        L 49 8
    """,
}
HW_S_PLANS["attic"] = _HW_S_PART + """
        X 0 1 chest:e
        X 0 2 chest:e
        X 0 3 barrel:e
        T 4 6 candle
        C 4 5 n
        C 4 7 s
        X 1 10 loom:n
        C 1 9 s
        X 12 10 hay
        X 13 10 hay
        X 17 1 barrel:w
        L 5 5
        L 13 5
        X 20 1 jukebox
        C 22 3 n
        C 23 3 n
        C 24 3 n
        T 23 5 lamp
        C 31 7 s
        C 32 7 s
        T 31 9 candle
        S 36 10 pot
        P 19 10 potted_fern
        L 23 5
        L 32 7
        X 39 10 chest:n
        X 40 10 chest:n
        X 41 10 barrel:n
        X 39 1 bwool
        X 39 2 wool
        T 45 6
        C 45 7 s
        P 53 10 potted_fern
        L 43 5
        L 49 8
"""
HW_S_FLOORS = ["ground", "first", "second", "third", "fourth", "attic"]

# Hearthwood sky tower – the two link ranges (11 x 6, no stair; reached through the wings; door lx 5 lz 0)
HW_LW_PLANS = {
    "tack": """
        X 0 0 fence
        X 0 1 fence
        X 0 2 fence
        X 1 5 hay
        X 2 5 hay
        X 3 5 chest:n
        X 7 5 barrel:n
        X 8 5 barrel:n
        P 0 5 potted_fern
        L 3 2
        L 8 2
    """,
    "laundry": """
        X 0 1 sink
        X 0 2 sink
        X 0 3 cauldron
        S 0 5 wool
        S 1 5 wool
        X 2 5 chest:n
        X 8 5 barrel:n
        T 7 2
        T 8 2 lamp
        L 3 3
        L 8 3
    """,
    "linen": """
        X 0 1 chest:e
        X 0 2 chest:e
        X 0 3 chest:e
        X 0 4 chest:e
        S 2 5 wool
        S 3 5 wool
        S 7 5 wool
        X 9 5 barrel:n
        X 10 5 barrel:n
        L 3 3
        L 8 3
    """,
    "box": """
        X 0 1 chest:e
        X 0 4 chest:e
        X 1 5 barrel:n
        X 2 5 barrel:n
        T 8 2 candle
        C 8 3 s
        X 10 5 bell
        L 3 3
        L 8 3
    """,
    "lumber": """
        X 0 1 barrel:e
        X 0 2 barrel:e
        X 0 3 chest:e
        X 2 5 hay
        X 3 5 hay
        X 8 5 log
        X 9 5 log
        X 10 5 log
        L 3 3
        L 8 3
    """,
}

HW_LE_PLANS = {
    "boots": """
        X 2 0 fence
        C 3 1 n
        X 0 5 chest:n
        X 1 5 barrel:n
        S 2 5 pot
        X 9 1 fence
        X 10 1 fence
        X 10 2 fence
        P 10 5 potted_fern
        L 3 3
        L 8 3
    """,
    "ironing": """
        T 2 3
        T 3 3
        X 0 1 sink
        X 0 4 chest:e
        S 0 5 wool
        S 1 5 wool
        X 9 5 barrel:n
        C 8 2 n
        L 3 3
        L 8 3
    """,
    "servants": """
        T 2 3 candle
        T 3 3
        T 4 3 candle
        C 2 2 n
        C 3 2 n
        C 2 4 s
        C 3 4 s
        C 4 4 s
        F 10 3 w
        X 0 5 chest:n
        S 8 5 pot
        L 3 3
        L 8 3
    """,
    "sewing": """
        X 0 1 loom:e
        X 0 3 loom:e
        C 1 2 e
        T 3 5 candle
        X 8 5 chest:n
        S 9 5 wool
        S 10 5 wool
        C 8 2 n
        L 3 3
        L 8 3
    """,
    "storage": """
        X 0 1 barrel:e
        X 0 2 barrel:e
        X 0 3 barrel:e
        X 0 4 chest:e
        X 2 5 hay
        X 8 5 chest:n
        X 9 5 chest:n
        X 10 5 barrel:n
        L 3 3
        L 8 3
    """,
}
HW_LW_FLOORS = ["tack", "laundry", "linen", "box", "lumber"]
HW_LE_FLOORS = ["boots", "ironing", "servants", "sewing", "storage"]

# round 5: more furniture where the south range, the wings and the link ranges were still thin (hand-placed)
HW_S_PLANS["first"] += """
        T 49 4 candle
        C 48 4 w
        C 50 4 e
        K 56 9 2
        K 56 10 2
        X 39 2 barrel:e
        T 50 9 lamp
        C 49 9 w
        C 51 9 e
        G 39 7 e
        L 40 8
        L 49 4
"""
HW_S_PLANS["second"] += """
        K 17 2 3
        K 17 3 3
        T 9 2 candle
        C 8 2 w
        C 10 2 e
        X 9 10 barrel:n
        P 0 10 potted_red_tulip
        R 4 8 7 9 blue
        L 9 2
        L 3 8
        T 44 8
        T 45 8 lamp
        C 44 9 s
        C 45 9 s
        X 50 10 loom:n
        X 51 10 chest:n
        S 52 10 candle
        K 56 8 2
        K 56 9 2
        X 47 1 hay
        X 48 1 hay
        L 45 8
        L 51 9
"""
HW_S_PLANS["third"] += """
        K 17 2 3
        T 9 8 candle
        C 8 8 w
        C 10 8 e
        X 3 10 chest:n
        L 9 8
        X 23 2 white_wool
        X 23 2 pot 1
        X 33 2 white_wool
        X 33 2 skull:n 1
        X 23 8 white_wool
        X 23 8 pot 1
        X 33 8 white_wool
        X 33 8 lamp 1
        X 25 9 white_wool
        X 25 9 pot 1
        X 31 9 white_wool
        X 31 9 pot 1
        X 25 1 white_wool
        X 25 1 lamp 1
        X 31 1 white_wool
        X 31 1 skull:n 1
        C 27 5 n
        C 28 5 n
        C 29 5 n
        P 20 1 potted_fern
        P 36 1 potted_fern
        P 20 9 potted_allium
        P 36 9 potted_allium
        L 28 3
        L 28 7
        T 51 9 lamp
        C 50 9 w
        C 52 9 e
        K 56 7 2
        K 56 8 2
        X 39 3 chest:e
        X 39 7 chest:e
        G 39 8 e
        L 51 9
        L 40 6
"""
HW_S_PLANS["fourth"] += """
        X 5 3 barrel
        X 5 4 barrel
        X 5 6 barrel
        X 5 7 barrel
        X 9 3 hay
        X 9 3 hay 1
        X 9 7 hay
        T 15 9 candle
        C 14 9 w
        X 17 1 chest:w
        X 17 2 chest:w
        X 17 8 barrel:w
        X 17 9 barrel:w
        L 3 5
        L 9 5
        C 24 8 s
        C 25 8 s
        C 26 8 s
        C 30 8 s
        C 31 8 s
        C 32 8 s
        K 19 1 2
        K 19 2 2
        K 37 1 2
        K 37 2 2
        G 19 6 e
        G 37 6 w
        L 25 8
        L 31 8
        X 44 10 chest:n
        X 45 10 chest:n
        X 56 8 barrel:w
        X 56 9 barrel:w
        C 46 5 n
        C 47 5 n
        X 39 8 lectern:e
        L 40 8
        L 47 6
"""
HW_S_PLANS["attic"] += """
        T 9 3 candle
        C 8 3 w
        C 10 3 e
        X 17 8 chest:w
        X 17 9 chest:w
        K 0 7 2
        K 0 8 2
        R 7 7 10 8 red
        L 9 3
        L 4 9
        K 19 6 2
        K 19 7 2
        K 19 8 2
        T 27 3 candle
        C 27 2 n
        C 27 4 s
        T 34 4
        C 33 4 w
        C 35 4 e
        X 37 9 chest:w
        X 37 10 chest:w
        R 22 7 25 9 gray
        L 27 3
        L 34 4
        K 56 8 2
        K 56 9 2
        X 44 10 barrel:n
        X 45 10 barrel:n
        T 49 3 candle
        C 48 3 w
        C 50 3 e
        X 39 3 chest:e
        X 39 7 chest:e
        L 49 3
        L 40 8
"""
HW_E_PLANS["billiard"] += """
        T 6 9 candle
        C 5 9 w
        C 7 9 e
        G 0 6 e
        K 10 9 2
        K 10 10 2
        X 1 0 jukebox
        L 6 9
"""
HW_E_PLANS["trophy"] += """
        X 2 21 white_wool
        X 2 21 skull:n 1
        X 8 21 white_wool
        X 8 21 pot 1
        G 0 22 e
        K 10 19 2
        K 10 20 2
"""
HW_E_PLANS["tea"] += """
        X 0 3 counter
        X 0 3 pot 1
        X 0 7 counter
        X 0 7 brew 1
        T 7 9 potted_red_tulip
        L 7 9
"""
HW_W_PLANS["guest"] += """
        T 4 1 candle
        C 3 1 w
        C 5 1 e
        X 0 5 chest:e
"""
HW_LW_PLANS["lumber"] += """
        X 8 1 log
        X 9 1 log
        X 10 1 log
        X 8 1 log 1
        X 9 1 log 1
        X 10 2 craft
        L 5 4
"""
HW_LE_PLANS["ironing"] += """
        X 10 1 chest:w
        X 10 2 chest:w
        P 0 0 potted_fern
"""



# Cascadia sky tower – great hall chalet (13 x 17, stair lx 10-12 / lz 0-6, door lx 6 lz 0)
CA_HALL_PLANS = {
    "dining": """
        F 6 16 n
        K 4 16 1
        K 8 16 1
        %s
        %s
        %s
        %s
        %s
        %s
        X 0 1 barrel:e
        X 0 2 barrel:e
        S 0 15 pot
        S 0 16 candle
        X 12 16 chest:w
        P 0 0 potted_fern
        P 12 10 potted_fern
        G 0 8 e
        G 12 12 w
        R 5 14 7 15 brown
        L 2 8
        L 9 8
        L 6 13
    """ % (_row("T", [(2, z) for z in range(5, 13)], "candle"), _row("C", [(1, z) for z in range(5, 13)], "w"),
           _row("C", [(3, z) for z in range(5, 13)], "e"), _row("T", [(8, z) for z in range(8, 13)], "candle"),
           _row("C", [(7, z) for z in range(8, 13)], "w"), _row("C", [(9, z) for z in range(8, 13)], "e")),
    "loft": """
        F 0 8 e
        C 2 7 e
        C 2 9 e
        R 1 7 2 9 green
        K 0 5
        K 0 11
        C 5 2 n
        C 6 2 n
        T 5 4 potted_fern
        C 5 6 s
        C 6 6 s
        X 0 16 jukebox
        X 1 16 note
        C 6 14 w
        T 7 14 candle
        C 8 14 e
        T 11 12 lamp
        C 11 11 n
        P 12 16 potted_spruce_sapling
        P 0 0 potted_fern
        L 2 8
        L 6 4
        L 7 13
    """,
    "gallery": """
        %s
        T 5 8 lamp
        T 6 8
        C 5 7 n
        C 6 7 n
        C 5 9 s
        C 6 9 s
        X 12 14 lectern:w
        C 10 14 e
        P 12 10 potted_fern
        P 0 16 potted_fern
        L 3 8
        L 9 12
    """ % _row("K", [(0, z) for z in range(1, 16)]),
}
CA_HALL_FLOORS = ["dining", "loft", "gallery"]

# Cascadia sky tower – east wing (11 x 23; doors lx 5 lz 0 and lx 0 lz 11; a partition at lz 14)
CA_E_PLANS = {
    "games": """
        W 0 14 10 14
        D 3 14 s
        X 2 3 green_wool
        X 3 3 green_wool
        X 2 4 green_wool
        X 3 4 green_wool
        X 2 5 green_wool
        X 3 5 green_wool
        X 0 2 fence
        X 0 3 fence
        T 6 9 candle
        C 5 9 w
        C 7 9 e
        C 6 8 n
        C 6 10 s
        X 0 7 barrel:e
        P 7 1 potted_fern
        P 0 13 potted_fern
        L 3 4
        L 6 9
        F 10 18 w
        C 8 17 w
        C 8 19 w
        R 7 17 9 19 brown
        T 3 18 candle
        C 2 18 w
        C 4 18 e
        X 0 22 jukebox
        S 0 16 pot
        P 10 22 potted_fern
        L 3 18
        L 8 18
    """,
    "library": """
        W 0 14 10 14
        D 3 14 s
        %s
        T 4 5 lamp
        C 4 4 n
        C 4 6 s
        X 7 1 lectern:w
        T 6 10
        C 5 10 w
        C 7 10 e
        L 4 6
        %s
        T 5 19 lamp
        T 6 19
        C 5 18 n
        C 6 18 n
        C 5 20 s
        C 6 20 s
        F 10 17 w
        P 10 22 potted_fern
        L 5 19
        L 8 17
    """ % (_row("K", [(0, z) for z in range(1, 14)]), _row("K", [(x, 22) for x in range(0, 9)])),
    "lounge": """
        W 0 14 10 14
        D 3 14 s
        F 0 7 e
        C 2 6 e
        C 2 8 e
        T 4 7 potted_fern
        C 5 6 n
        C 5 8 s
        R 1 6 3 8 green
        K 0 3
        K 0 11
        P 7 1 potted_spruce_sapling
        L 3 7
        X 0 16 bwool
        X 0 17 bwool
        C 2 19 n
        C 3 19 n
        T 2 21 candle
        C 7 18 w
        T 8 18 lamp
        C 9 18 e
        X 10 22 chest:w
        P 0 22 potted_fern
        L 3 19
        L 8 19
    """,
    "attic": """
        W 0 14 10 14
        D 3 14 s
        X 0 1 chest:e
        X 0 2 chest:e
        X 0 3 barrel:e
        X 4 7 hay
        T 6 10 candle
        C 6 9 n
        P 7 1 potted_fern
        L 4 6
        X 0 16 barrel:e
        X 0 17 barrel:e
        X 0 18 chest:e
        X 8 22 hay
        X 9 22 hay
        T 5 19
        C 5 20 s
        L 4 18
    """,
}
CA_E_FLOORS = ["games", "library", "lounge", "attic"]

# Cascadia sky tower – lookout tower (7 x 9; stair lx 4-6 / lz 0-6, door lx 3 lz 0)
CA_T_PLANS = {
    "ski": """
        X 0 1 fence
        X 0 2 fence
        X 0 3 fence
        X 0 5 chest:e
        C 1 6 w
        X 3 8 barrel:n
        X 4 8 bwool
        P 6 8 potted_fern
        L 2 4
        L 5 8
    """,
    "map": """
        X 0 1 carto
        C 1 1 e
        X 0 3 lectern:e
        Q 0 5 e 2
        T 2 7 candle
        C 3 7 e
        P 6 8 potted_fern
        L 2 4
        L 5 8
    """,
    "tea": """
        T 1 3 candle
        C 1 2 n
        C 1 4 s
        C 0 3 w
        X 0 7 furnace:e
        S 0 8 pot
        C 4 8 s
        P 6 8 potted_spruce_sapling
        L 2 4
        L 5 8
    """,
    "lookout": """
        X 0 2 lectern:e
        C 1 4 w
        C 1 5 w
        T 2 7 lamp
        X 0 8 chest:e
        C 5 8 s
        P 6 7 potted_fern
        L 2 4
        L 5 8
    """,
    "store": """
        X 0 1 barrel:e
        X 0 2 barrel:e
        X 0 3 chest:e
        X 0 7 hay
        X 1 8 barrel:n
        P 6 8 potted_fern
        L 2 4
        L 5 8
    """,
}


CA_T_PLANS.update({
    "radio": """
        X 0 1 note
        X 0 2 lectern:e
        C 1 2 e
        X 0 3 jukebox
        T 2 7 lamp
        C 1 7 w
        X 0 8 chest:e
        P 6 8 potted_fern
        L 2 4
        L 5 8
    """,
    "aid": """
        X 0 1 brew
        X 0 2 cauldron
        X 0 3 chest:e
        X 0 4 chest:e
        X 2 8 white_wool
        X 3 8 white_wool
        C 1 6 w
        P 6 8 potted_spruce_sapling
        L 2 4
        L 5 8
    """,
    "workshop": """
        X 0 1 craft
        X 0 2 grind:e
        X 0 3 smith
        X 0 7 barrel:e
        X 0 8 chest:e
        T 2 4 lamp
        C 2 5 s
        P 6 8 potted_fern
        L 2 3
        L 5 8
    """,
    "pantry": """
        X 0 1 smoker:e
        X 0 2 barrel:e
        X 0 3 barrel:e
        X 0 6 barrel:e
        X 0 7 barrel:e
        X 1 8 hay
        X 2 8 hay
        X 3 8 melon
        L 2 4
        L 5 8
    """,
    "reading": """
        K 0 1 3
        K 0 2 3
        K 0 3 3
        K 0 4 3
        T 2 7 candle
        C 1 7 w
        C 3 7 e
        P 6 8 potted_fern
        L 2 4
        L 5 8
    """,
    "drying": """
        X 0 1 fence
        X 0 2 fence
        X 0 3 fence
        X 0 1 brown_carpet 1
        X 0 2 white_carpet 1
        X 0 3 green_carpet 1
        X 0 7 barrel:e
        X 0 8 chest:e
        C 3 8 s
        L 2 4
        L 5 8
    """,
    "chapel": """
        X 0 4 lectern:e
        C 2 3 s
        C 3 3 s
        C 2 5 s
        C 3 5 s
        X 0 8 candle
        P 6 8 potted_fern
        G 0 6 e
        L 2 4
        L 5 8
    """,
    "gear": """
        X 0 1 chest:e
        X 0 2 chest:e
        X 0 3 barrel:e
        X 0 6 fence
        X 0 7 fence
        X 0 8 fence
        T 3 8 candle
        C 2 8 s
        L 2 4
        L 5 8
    """,
})


def ca_t_floors(n):
    mid = ["map", "tea", "store", "radio", "aid", "workshop", "pantry", "reading", "drying", "gear", "chapel"]
    return (["ski"] + mid[:max(0, n - 2)] + ["lookout"])[:n]


# Cascadia sky tower – bathhouse (13 x 13; stair lx 10-12; door lx 6 lz 0)
CA_B_PLANS = {
    "pool": """
        %s
        %s
        C 0 3 w
        C 0 5 w
        C 0 7 w
        S 0 11 wool
        S 0 12 wool
        X 1 12 chest:n
        P 12 12 potted_fern
        P 9 12 potted_fern
        L 6 5
        L 6 9
        L 4 4
        L 8 4
        L 4 9
        L 8 9
        L 6 7
        X 3 3 potted_fern 1
        X 9 3 potted_fern 1
        X 3 10 potted_fern 1
        X 9 10 potted_fern 1
    """ % (_row("X", [(x, z) for x in range(3, 10) for z in range(3, 11) if x in (3, 9) or z in (3, 10)],
                "cobblestone_slab[type=top,waterlogged=false]"),
           _row("X", [(x, z) for x in range(4, 9) for z in range(4, 10)], "water")),
    "sauna": """
        W 0 6 6 6 spruce_planks
        D 3 6 s
        %s
        %s
        X 3 2 campfire[facing=south,lit=true,signal_fire=false,waterlogged=false]
        X 3 1 cobblestone
        C 1 10 n
        C 2 10 n
        T 1 12 candle
        S 7 12 wool
        S 8 12 wool
        X 12 12 chest:w
        P 9 9 potted_fern
        L 3 3
        L 4 10
        L 9 11
    """ % (_row("X", [(0, z) for z in range(0, 6)], "spruce_slab[type=bottom,waterlogged=false]"),
           _row("X", [(6, z) for z in range(0, 6)], "spruce_slab[type=bottom,waterlogged=false]")),
}

# Cascadia sky tower – red barn (13 x 11; stair lx 10-12; door lx 6 lz 0)
CA_N_PLANS = {
    "stable": """
        X 3 7 fence
        X 3 8 fence
        X 3 9 fence
        X 3 10 fence
        X 6 7 fence
        X 6 8 fence
        X 6 9 fence
        X 6 10 fence
        X 1 10 hay
        X 4 10 hay
        X 7 10 hay
        X 1 9 composter
        X 4 9 sink
        X 0 1 fence
        X 0 2 fence
        X 0 4 chest:e
        X 9 10 barrel:n
        X 12 10 hay
        L 2 8
        L 5 8
        L 9 8
    """,
    "hayloft": """
        %s
        %s
        X 0 9 chest:e
        X 6 6 barrel
        X 8 9 hay
        L 3 5
        L 8 8
    """ % (_row("X", [(x, z) for x in (0, 1, 2) for z in (1, 2, 3, 4)], "hay"),
           _row("X", [(x, 10) for x in range(0, 6)], "hay")),
}

# Cascadia sky tower – south chalet wing (19 x 15; stair lx 16-18; door lx 9 lz 0; partition lx 7)
CA_S_PLANS = {
    "dining": """
        W 7 0 7 14
        D 7 8 e
        F 0 7 e
        C 2 6 e
        C 2 8 e
        K 0 4
        K 0 10
        T 4 3 candle
        C 4 2 n
        T 4 12 candle
        C 4 13 s
        P 0 0 potted_fern
        P 0 14 potted_fern
        L 3 7
        %s
        %s
        %s
        X 15 14 chest:n
        S 8 14 pot
        S 9 14 candle
        P 15 10 potted_fern
        L 11 7
        L 11 12
    """ % (_row("T", [(11, z) for z in range(4, 13)], "candle"), _row("C", [(10, z) for z in range(4, 13)], "w"),
           _row("C", [(12, z) for z in range(4, 13)], "e")),
    "lounge": """
        W 7 0 7 14
        D 7 8 e
        T 3 7 lamp
        C 2 6 n
        C 3 6 n
        C 4 6 n
        C 2 8 s
        C 3 8 s
        C 4 8 s
        X 0 1 jukebox
        P 0 14 potted_fern
        L 3 7
        F 15 12 w
        C 13 11 w
        C 13 13 w
        R 12 11 14 13 brown
        T 10 4 candle
        C 9 4 w
        C 11 4 e
        S 8 14 pot
        L 11 9
    """,
    "library": """
        W 7 0 7 14
        D 7 8 e
        %s
        T 3 7 lamp
        C 3 6 n
        C 3 8 s
        L 3 7
        %s
        T 11 10 lamp
        T 12 10
        C 11 9 n
        C 12 9 n
        C 11 11 s
        C 12 11 s
        X 15 8 lectern:w
        L 11 10
    """ % (_row("K", [(0, z) for z in range(0, 15)]), _row("K", [(x, 14) for x in range(8, 16)])),
    "bar": """
        W 7 0 7 14
        D 7 8 e
        %s
        %s
        T 4 4 candle
        C 4 3 n
        C 4 5 s
        T 4 10 candle
        C 4 9 n
        C 4 11 s
        L 3 7
        X 9 13 barrel:n
        X 10 13 barrel:n
        X 11 13 barrel:n
        X 12 13 barrel:n
        X 9 11 planks
        X 10 11 planks
        X 11 11 planks
        X 12 11 planks
        C 9 10 n
        C 10 10 n
        C 11 10 n
        C 12 10 n
        P 15 14 potted_fern
        L 11 9
    """ % (_row("X", [(0, z) for z in range(2, 13)], "barrel:e"), _row("X", [(0, z) for z in range(2, 13)], "pot 1")),
    "hall": """
        W 7 0 7 14
        D 7 8 e
        X 0 2 chest:e
        X 0 3 chest:e
        X 0 4 barrel:e
        X 0 10 hay
        X 0 11 bwool
        T 3 7 candle
        C 3 8 s
        L 3 7
        X 9 14 bell
        C 10 9 s
        C 11 9 s
        C 12 9 s
        C 10 11 s
        C 11 11 s
        C 12 11 s
        X 11 6 lectern:s
        L 11 9
    """,
}
CA_S_FLOORS = ["dining", "lounge", "library", "bar", "hall"]

# round 5: hand-placed extras where the east wing and the south chalet were still thin
CA_E_PLANS["games"] += """
        K 10 9 2
        K 10 10 2
        K 10 11 2
        X 0 5 barrel:e
        S 0 6 lamp
        T 3 9 lamp
        C 3 10 s
        G 0 4 e
        L 3 10
"""
CA_E_PLANS["lounge"] += """
        K 10 16 2
        K 10 17 2
        T 5 16 candle
        C 6 16 e
        P 9 22 potted_fern
        L 6 16
"""
CA_E_PLANS["attic"] += """
        X 0 4 chest:e
        X 0 5 chest:e
        X 0 10 barrel:e
        X 0 11 barrel:e
        X 4 7 hay 1
        X 5 7 hay
        T 5 3 lamp
        C 4 3 w
        C 6 3 e
        X 10 10 chest:w
        X 10 11 chest:w
        K 10 12 2
        L 5 3
        L 9 11
        X 0 19 chest:e
        X 0 20 barrel:e
        X 10 16 hay
        X 10 17 hay
        L 8 20
"""
CA_S_PLANS["lounge"] += """
        K 0 3 2
        K 0 4 2
        K 6 12 2
        K 6 13 2
        T 2 12 candle
        C 1 12 w
        C 3 12 e
        L 3 12
"""
CA_S_PLANS["bar"] += """
        T 14 9 candle
        C 13 9 w
        C 15 9 e
        T 10 6 candle
        C 9 6 w
        C 11 6 e
        G 18 10 w
        L 14 9
        L 10 6
"""
CA_S_PLANS["hall"] += """
        T 3 3 lamp
        C 2 3 w
        C 4 3 e
        X 6 1 chest:w
        X 6 2 chest:w
        X 0 13 barrel:e
        X 0 14 barrel:e
        L 3 3
        L 3 12
        C 14 9 s
        C 15 9 s
        C 14 11 s
        C 15 11 s
        G 8 3 e
        G 8 12 e
        G 18 10 w
        X 10 6 candle
        P 18 14 potted_fern
        P 8 14 potted_fern
        L 14 10
        L 11 4
        L 16 12
"""
CA_S_PLANS["music"] = """
        W 7 0 7 14
        D 7 8 e
        X 0 1 note
        X 0 2 note
        X 0 3 jukebox
        C 1 2 w
        C 4 5 n
        C 5 5 n
        C 4 7 n
        C 5 7 n
        K 0 10 2
        K 0 11 2
        P 0 14 potted_fern
        T 3 12 candle
        C 2 12 w
        C 4 12 e
        L 3 5
        L 3 12
        T 10 3 candle
        C 9 3 w
        C 11 3 e
        T 10 10 lamp
        C 9 10 w
        C 11 10 e
        C 10 9 n
        C 10 11 s
        X 18 8 barrel:w
        X 18 9 barrel:w
        K 18 12 2
        K 18 13 2
        P 8 14 potted_fern
        P 18 14 potted_fern
        G 8 3 e
        L 10 3
        L 10 10
        L 14 12
"""
CA_S_PLANS["study"] = """
        W 7 0 7 14
        D 7 8 e
        Q 0 2 e 2
        Q 0 3 e 2
        T 3 3 lamp
        T 3 4
        C 4 3 e
        C 4 4 e
        X 0 8 carto
        X 0 9 lectern:e
        T 3 11 candle
        C 2 11 w
        C 4 11 e
        X 6 13 chest:w
        X 6 14 chest:w
        P 0 0 potted_fern
        L 3 4
        L 3 11
        T 9 3
        T 10 3 lamp
        C 9 4 s
        C 10 4 s
        T 13 3
        T 14 3 lamp
        C 13 4 s
        C 14 4 s
        T 9 9
        T 10 9 candle
        C 9 10 s
        C 10 10 s
        T 13 9 lamp
        T 14 9
        C 13 10 s
        C 14 10 s
        K 8 14 2
        K 9 14 2
        K 10 14 2
        P 18 14 potted_fern
        L 10 4
        L 14 4
        L 10 10
        L 14 10
"""
CA_S_FLOORS = CA_S_FLOORS + ["music", "study"]



# Neoterra twin builder – materials store (13 x 11, 6 high, no stair; door lx 6, roller doors lx 2-3 and 10-11)
NT_STORE_PLAN = """
        %s
        %s
        %s
        %s
        X 0 9 chest:e
        X 0 10 chest:e
        X 12 9 chest:w
        X 12 10 chest:w
        X 6 10 hay
        X 7 10 white_wool
        X 5 10 white_wool
        X 3 10 smooth_stone
        X 9 10 bricks
        L 3 6
        L 9 6
"""
NT_STORE_PLAN = NT_STORE_PLAN % (
    _row("X", [(x, 4) for x in (1, 2, 3, 4, 8, 9, 10, 11)], "barrel"),
    _row("X", [(x, 4) for x in (1, 2, 3, 4, 8, 9, 10, 11)], "barrel 1"),
    _row("X", [(x, 7) for x in (1, 2, 3, 4, 8, 9, 10, 11)], "chest:n"),
    _row("X", [(x, 7) for x in (1, 2, 3, 4, 8, 9, 10, 11)], "barrel 1"))

# Neoterra twin builder – site management offices (13 x 9; stair lx 10-12; door lx 6)
NT_OFFICE_PLANS = {
    "reception": """
        X 2 4 counter
        X 3 4 counter
        X 4 4 counter
        C 3 5 s
        X 0 1 chest:e
        Q 0 2 e 2
        C 1 7 w
        C 2 7 w
        T 3 7 potted_bamboo
        P 0 8 potted_bamboo
        X 10 8 carto
        C 9 8 w
        G 0 5 e
        L 3 4
        L 10 8
    """,
    "plans": """
        X 0 1 carto
        C 1 1 e
        X 0 3 carto
        C 1 3 e
        X 0 5 carto
        C 1 5 e
        T 4 4 pot
        T 5 4
        T 6 4 candle
        C 5 5 s
        X 0 8 chest:e
        X 1 8 chest:n
        Q 2 8 n
        X 11 8 lectern:w
        L 2 3
        L 5 4
        L 10 8
    """,
    "meeting": """
        %s
        %s
        %s
        C 2 4 w
        C 8 4 e
        X 0 8 jukebox
        S 1 8 pot
        P 10 8 potted_bamboo
        P 0 0 potted_bamboo
        L 3 4
        L 7 4
    """ % (_row("T", [(x, 4) for x in range(3, 8)]), _row("C", [(x, 3) for x in range(3, 8)], "n"),
           _row("C", [(x, 5) for x in range(3, 8)], "s")),
}

# Neoterra twin builder – precast works hall (27 x 14, 6 high; stair lx 24-26 / lz 0-7; doors lx 13 lz 0, lx 0 lz 6)
NT_HALL_PLANS = {
    "casting": """
        %s
        %s
        X 20 11 cauldron
        X 21 11 gray_concrete_powder
        X 22 11 light_gray_concrete_powder
        X 20 12 hopper[enabled=true,facing=down]
        %s
        X 0 1 chest:e
        X 0 2 barrel:e
        X 0 10 craft
        X 0 11 smith
        X 0 12 anvil:e
        X 26 13 barrel:w
        L 5 7
        L 13 7
        L 20 9
    """ % (_row("X", [(x, z) for x in range(3, 11) for z in (3, 4)], "smooth_stone_slab[type=bottom,waterlogged=false]"),
           _row("X", [(x, z) for x in range(3, 11) for z in (8, 9)], "smooth_stone_slab[type=bottom,waterlogged=false]"),
           _row("X", [(x, 13) for x in range(4, 16)], "white_concrete")),
    "finishing": """
        %s
        X 4 6 grind:n
        X 6 6 cutter:n
        X 8 6 grind:n
        C 4 7 s
        C 8 7 s
        X 0 1 chest:e
        X 0 2 chest:e
        Q 0 4 e 2
        %s
        X 20 12 lectern:n
        T 15 4 candle
        T 16 4
        C 15 3 n
        C 16 5 s
        P 26 13 potted_bamboo
        L 5 4
        L 15 4
        L 12 11
    """ % (_row("X", [(x, 5) for x in range(3, 11)], "counter"), _row("X", [(x, 13) for x in range(2, 18)], "barrel:n")),
}

# Neoterra twin builder – workers' canteen block (14 x 17; stair lx 11-13; door lx 6)
NT_CANTEEN_PLANS = {
    "canteen": """
        %s
        %s
        %s
        %s
        %s
        %s
        %s
        X 0 1 counter
        X 0 2 counter
        X 0 3 counter
        X 0 1 pot 1
        P 13 16 potted_bamboo
        P 0 16 potted_bamboo
        L 3 6
        L 3 12
        L 9 12
    """ % (_row("T", [(3, z) for z in range(5, 13)]), _row("C", [(2, z) for z in range(5, 13)], "w"),
           _row("C", [(4, z) for z in range(5, 13)], "e"), _row("T", [(9, z) for z in range(8, 15)]),
           _row("C", [(8, z) for z in range(8, 15)], "w"), _row("C", [(10, z) for z in range(8, 15)], "e"),
           _row("X", [(x, 16) for x in range(2, 8)], "counter")),
    "kitchen": """
        X 0 1 furnace:e
        X 0 2 smoker:e
        X 0 3 furnace:e
        X 0 4 sink
        S 0 5 pot
        X 0 6 barrel:e
        X 0 7 barrel:e
        X 4 4 counter
        X 5 4 counter
        X 6 4 counter
        X 4 8 counter
        X 5 8 counter
        X 6 8 counter
        %s
        X 13 16 chest:w
        T 9 12 candle
        C 8 12 w
        C 10 12 e
        L 3 4
        L 5 10
        L 10 12
    """ % _row("X", [(x, 16) for x in range(0, 10)], "barrel:n"),
    "lockers": """
        %s
        %s
        C 4 5 w
        C 4 6 w
        C 4 7 w
        C 4 10 w
        C 4 11 w
        C 4 12 w
        X 0 16 sink
        X 1 16 sink
        S 2 16 wool
        X 12 12 lectern:w
        P 13 16 potted_bamboo
        L 3 6
        L 3 12
        L 10 12
    """ % (_row("X", [(0, z) for z in range(2, 15)], "chest:e"), _row("X", [(0, z) for z in range(2, 15)], "chest:e 1")),
    "gym": """
        X 0 1 andesite
        X 0 1 plate 1
        X 0 2 andesite
        X 0 2 plate 1
        X 0 3 sslab
        R 3 3 6 6 lime
        X 3 10 target 1
        X 3 10 chain 2
        X 3 10 chain 3
        X 8 10 target 1
        X 8 10 chain 2
        X 8 10 chain 3
        X 0 16 sink
        S 1 16 wool
        X 3 16 black_carpet
        X 4 16 black_carpet
        X 5 16 black_carpet
        P 13 16 potted_bamboo
        L 4 4
        L 5 10
        L 10 13
    """,
    "training": """
        X 5 1 lectern:s
        X 4 0 white_wool 1
        X 5 0 white_wool 1
        X 6 0 white_wool 1
        %s
        X 0 16 chest:e
        Q 0 15 e 2
        X 13 16 carto
        P 0 8 potted_bamboo
        L 4 6
        L 4 12
        L 10 12
    """ % _row("C", [(x, z) for z in (4, 6, 8, 10, 12) for x in (2, 3, 4, 5, 6, 7)], "s"),
}
NT_CANTEEN_FLOORS = ["canteen", "kitchen", "lockers", "gym", "training"]

# Hearthwood twin builder – timber seasoning barn (9 x 13; stair lx 6-8; door lx 4)
HW_BARN_PLANS = {
    "timber": """
        %s
        %s
        X 0 12 chest:e
        X 1 12 barrel:n
        X 5 12 hay
        L 2 5
        L 4 10
    """ % (_row("X", [(0, z) for z in range(1, 11)], "log"), _row("X", [(0, z) for z in range(1, 11)], "log 1")),
    "loft": """
        %s
        X 3 10 barrel
        X 3 11 barrel
        X 7 12 chest:w
        L 3 5
        L 5 10
    """ % _row("X", [(x, z) for x in (0, 1) for z in range(2, 12)], "hay"),
}

# Hearthwood twin builder – clerk of works (11 x 9; stair lx 8-10; door on the south side lx 5 lz 8)
HW_CLERK_PLANS = {
    "clerk": """
        T 1 2 lamp
        T 2 2
        C 1 1 n
        C 2 3 s
        Q 0 4 e 2
        X 0 5 chest:e
        X 0 7 barrel:e
        P 7 0 potted_red_tulip
        C 3 6 w
        G 0 2 e
        L 2 3
        L 6 6
    """,
    "drawing": """
        X 0 1 carto
        C 1 1 e
        X 0 3 carto
        C 1 3 e
        X 0 5 carto
        C 1 5 e
        T 4 3 pot
        T 5 3 candle
        C 4 2 n
        X 0 8 chest:e
        X 1 8 chest:n
        X 7 8 lectern:n
        L 3 3
        L 6 7
    """,
    "archive": """
        %s
        %s
        T 4 4 lamp
        C 4 5 s
        P 7 0 potted_fern
        L 3 4
        L 7 7
    """ % (_row("Q", [(0, z) for z in range(0, 9)], "e 2"), _row("K", [(x, 8) for x in range(1, 8)])),
}

# Hearthwood twin builder – joinery (19 x 13; stair lx 16-18; doors lx 9 lz 0 and lx 0 lz 6)
HW_JOIN_PLANS = {
    "bench": """
        %s
        X 2 12 grind:n
        X 4 12 cutter:n
        X 6 12 smith
        X 8 12 anvil:e
        X 10 12 craft
        %s
        X 5 6 lamp 1
        %s
        X 15 12 barrel:n
        X 14 12 chest:n
        L 4 6
        L 9 9
        L 14 9
    """ % (_row("X", [(x, 6) for x in range(3, 8)], "counter"),
           _row("X", [(x, 8) for x in (12, 13, 14)], "counter"),
           _row("X", [(0, z) for z in (1, 2, 3, 9, 10, 11)], "log")),
    "store": """
        %s
        %s
        %s
        X 15 12 chest:n
        L 4 6
        L 12 8
    """ % (_row("X", [(x, z) for z in (2, 5, 8, 11) for x in range(1, 13) if x != 7], "log"),
           _row("X", [(x, z) for z in (2, 5, 8, 11) for x in range(1, 13) if x != 7], "log 1"),
           _row("X", [(0, z) for z in (3, 4, 6, 7, 9, 10)], "barrel:e")),
}

# Hearthwood twin builder – masons' hall (27 x 11; stair lx 24-26; doors lx 13 lz 0 and lx 26 lz 8)
HW_MASON_PLANS = {
    "banker": """
        %s
        %s
        X 0 1 chest:e
        X 0 2 barrel:e
        X 0 9 cutter:e
        X 0 10 grind:e
        %s
        X 20 10 craft
        X 21 10 anvil:e
        L 5 5
        L 13 5
        L 20 7
    """ % (_row("X", [(x, 4) for x in (3, 6, 9, 16, 19)], "stone_bricks"),
           _row("X", [(x, 4) for x in (3, 6, 9, 16, 19)], "chiseled_stone_bricks 1"),
           _row("X", [(x, 10) for x in range(3, 18)], "stone_bricks")),
    "mess": """
        %s
        %s
        %s
        F 0 5 e
        X 0 1 furnace:e
        X 0 2 sink
        X 0 9 barrel:e
        X 0 10 chest:e
        P 20 10 potted_fern
        L 8 5
        L 16 5
    """ % (_row("T", [(x, 5) for x in range(5, 20)], "candle"), _row("C", [(x, 4) for x in range(5, 20)], "n"),
           _row("C", [(x, 6) for x in range(5, 20)], "s")),
    "tracing": """
        %s
        X 6 6 carto
        X 8 6 carto
        X 10 6 carto
        C 6 7 s
        C 8 7 s
        C 10 7 s
        X 0 1 chest:e
        X 0 2 chest:e
        Q 0 4 e 2
        X 20 10 lectern:n
        L 8 5
        L 18 6
    """ % _row("X", [(x, 1) for x in range(4, 16)], "white_wool 1"),
}

# Hearthwood twin builder – tool shed (5 x 5, door lx 2) and cart shed / wheelwright (10 x 7, door lx 4)
HW_TOOL_PLAN = """
        X 0 1 fence
        X 0 2 fence
        X 0 3 barrel:e
        X 4 1 chest:w
        X 4 2 grind:w
        X 4 3 fence
        X 2 4 barrel:n
        L 2 2
"""
HW_CART_PLAN = """
        X 1 3 spruce_slab[type=top,waterlogged=false]
        X 2 3 spruce_slab[type=top,waterlogged=false]
        X 3 3 spruce_slab[type=top,waterlogged=false]
        X 0 3 fence
        X 1 6 anvil:e
        X 3 6 grind:n
        X 5 6 craft
        X 7 6 barrel:n
        X 9 1 log
        X 9 2 log
        X 9 1 log 1
        L 2 3
        L 7 3
"""

# Cascadia twin builder – lumber drying shed (15 x 9; doors lx 7 lz 0 and lz 8)
CA_SHED_PLAN = """
        %s
        %s
        %s
        %s
        X 14 4 chest:w
        X 0 4 barrel:e
        L 3 4
        L 11 4
"""
CA_SHED_PLAN = CA_SHED_PLAN % (
    _row("X", [(x, z) for x in range(1, 6) for z in (2, 6)], "log"),
    _row("X", [(x, z) for x in range(1, 6) for z in (2, 6)], "log 1"),
    _row("X", [(x, z) for x in range(9, 14) for z in (2, 6)], "log"),
    _row("X", [(x, z) for x in range(9, 14) for z in (2, 6)], "log 1"))

# Cascadia twin builder – framers' bunkhouse office (11 x 10; stair lx 8-10; door lx 5)
CA_BUNK_PLANS = {
    "office": """
        T 1 3 lamp
        T 2 3
        C 1 2 n
        C 2 4 s
        X 0 6 carto
        C 1 6 e
        Q 0 8 e 2
        X 0 9 chest:e
        X 7 9 barrel:n
        X 8 9 barrel:n
        P 3 9 potted_fern
        G 0 1 e
        L 2 3
        L 6 8
    """,
    "mess": """
        F 0 5 e
        C 2 4 e
        C 2 6 e
        T 5 8 candle
        T 6 8
        C 5 7 n
        C 6 7 n
        C 5 9 s
        C 6 9 s
        X 0 9 chest:e
        X 0 1 barrel:e
        X 10 9 bwool
        L 3 5
        L 6 8
    """,
}

# Cascadia twin builder – sawmill (21 x 13; stair lx 18-20; doors lx 10 lz 0 and lx 20 lz 10)
CA_MILL_PLANS = {
    "saw": """
        %s
        X 8 6 cutter:n
        X 12 6 cutter:n
        %s
        X 0 1 grind:e
        X 0 2 anvil:e
        X 0 3 chest:e
        %s
        X 17 12 barrel:n
        L 5 6
        L 10 6
        L 15 9
    """ % (_row("X", [(x, 6) for x in range(2, 8)], "log"), _row("X", [(x, 6) for x in range(13, 18)], "log"),
           _row("X", [(x, 12) for x in range(2, 12)], "spruce_planks")),
    "filing": """
        X 2 11 grind:n
        X 4 11 grind:n
        X 6 11 anvil:e
        C 2 10 s
        C 4 10 s
        %s
        %s
        X 0 1 chest:e
        X 0 2 barrel:e
        T 12 5 lamp
        C 12 4 n
        L 4 8
        L 12 6
        L 15 10
    """ % (_row("X", [(x, z) for x in (9, 10, 11) for z in (9, 10, 11)], "planks"),
           _row("X", [(x, 12) for x in range(9, 17)], "barrel:n")),
}

# Cascadia twin builder – cookhouse (19 x 13; stair lx 16-18; door lx 9)
CA_COOK_PLANS = {
    "dining": """
        %s
        %s
        %s
        %s
        %s
        %s
        F 0 6 e
        S 15 12 pot
        P 0 12 potted_fern
        L 4 6
        L 12 6
        L 8 10
    """ % (_row("T", [(x, 4) for x in range(3, 15)], "candle"), _row("C", [(x, 3) for x in range(3, 15)], "n"),
           _row("C", [(x, 5) for x in range(3, 15)], "s"), _row("T", [(x, 9) for x in range(3, 15)], "candle"),
           _row("C", [(x, 8) for x in range(3, 15)], "n"), _row("C", [(x, 10) for x in range(3, 15)], "s")),
    "kitchen": """
        X 0 1 furnace:e
        X 0 2 smoker:e
        X 0 3 furnace:e
        X 0 4 sink
        S 0 5 pot
        %s
        X 5 6 counter
        X 6 6 counter
        X 7 6 counter
        X 5 6 pot 1
        X 15 12 chest:n
        T 12 9 candle
        C 11 9 w
        C 13 9 e
        L 3 4
        L 7 8
        L 12 9
    """ % _row("X", [(x, 12) for x in range(0, 12)], "barrel:n"),
    "lounge": """
        F 0 6 e
        C 2 5 e
        C 2 7 e
        R 1 5 2 7 brown
        T 7 4 candle
        C 6 4 w
        C 8 4 e
        T 7 9 candle
        C 6 9 w
        C 8 9 e
        X 15 12 jukebox
        X 0 12 bwool
        X 1 12 bwool
        P 15 8 potted_fern
        L 3 6
        L 8 6
        L 13 10
    """,
}


def raise_building(d, pack, rect, y0, n, plans, floors, wd, tt, H=5, extra=(), **kw):
    """Shell of one add-on building plus its own hand-written floor plans."""
    levels, origin, forbid = shell(d, pack, *rect, y0, n, H=H, **kw)
    fit_floors(d, pack, levels, origin, forbid, H, plans, floors, wd, tt, extra)
    return levels


# ---------------------------------------------------------------------------------------------- sky tower growth
def _door_through(d, x, y, z, facing, wood, clear_in=None):
    """Door in an existing wall; clears the cell (and 2 above) on the inner side `clear_in` (dx, dz)."""
    d.door(x, y, z, facing, wood)
    if clear_in:
        cx, cz = x + clear_in[0], z + clear_in[1]
        for k in (0, 1, 2):
            d.set(cx, y + k, cz, AIR)


def grow_sky_nt(d, L):
    P = "Neoterra"
    regrid(d, 51, 47, 14, 4, 104)
    lv = [8, 13, 18, 23, 28]
    # plaza in front of all buildings: avenue trees, lamps, benches
    for x in range(0, 51):
        d.set(x, 1, 0, "polished_andesite")
        d.set(x, 1, 1, "smooth_stone" if x % 4 else "light_gray_concrete")
    for x in (2, 8, 14, 32, 38, 44):
        lamp_post(d, x, 2, 2, P, 4)
    for x in (4, 10, 40, 46):
        flowerbed(d, x, 4, x + 2, 5, 2, P)
    bench(d, 8, 3, 2, P, "south")
    bench(d, 41, 3, 2, P, "south")
    if L >= 2:                                        # west residents' club: gym, lounge, library (+ bar)
        lv += raise_building(d, P, (2, 8, 12, 22), 2, {2: 5, 3: 5, 4: 6, 5: 7}[L], NT_CLUB_PLANS, NT_CLUB_FLOORS,
                             "mangrove", "mangrove", doors=[(7, 8, "north")], st=NT_CLUB)
        for x in range(5, 10):                         # mangrove canopy over the club entrance
            d.set(x, 6, 7, slab("mangrove", "top"))
            d.set(x, 6, 6, slab("mangrove", "top"))
        for x in (5, 9):
            for y in range(2, 6):
                d.set(x, y, 6, "mangrove_fence")
        d.sign(7, 5, 7, "north", ["RESIDENTS", "CLUB"], "birch", glow=True, color="cyan")
        for x in (3, 11):
            tree(d, x, 25, 2, h=5)
    if L >= 3:                                        # east tower B: restaurant, offices, lounges, sky bar
        nB = {3: 8, 4: 13, 5: 18}[L]
        lv += raise_building(d, P, (39, 8, 49, 22), 3, nB, NT_B_PLANS, nt_b_floors(nB), "dark_oak",
                             "polished_andesite", doors=[(44, 8, "north")], st=NT_TOWER_B)
        d.set(44, 2, 7, stair("smooth_quartz", "south"))
        d.sign(44, 7, 7, "north", ["SKYLINE", "CLUB"], "birch", glow=True, color="cyan")
        # pool garden behind the towers
        for x, z in cells(3, 27, 14, 35):
            edge = x in (3, 14) or z in (27, 35)
            d.set(x, 1, z, "smooth_quartz" if edge else "water[level=0]")
            if not edge:
                d.set(x, 0, z, "prismarine_bricks" if (x + z) % 4 else "sea_lantern")
        for x in range(4, 14, 2):
            d.chair(x, 2, 37, "south", "birch", sit=False)
        for x, z in ((2, 26), (15, 26), (2, 36), (15, 36)):
            tree(d, x, z, 2, h=4)
        for x, z in cells(17, 26, 49, 27):
            d.set(x, 1, z, "smooth_stone")
        flowerbed(d, 34, 24, 37, 25, 2, P)
    if L >= 4:                                        # sky bridge A<->B, south tower C
        for x in range(34, 39):
            for z in (18, 19, 20):
                d.set(x, 22, z, "white_concrete" if z != 19 else "polished_diorite")
                d.set(x, 27, z, "white_concrete")
            for y in range(23, 27):
                d.set(x, y, 18, "light_blue_stained_glass_pane")
                d.set(x, y, 20, "light_blue_stained_glass_pane")
                d.set(x, y, 19, AIR)
        for x in (34, 36, 38):
            d.set(x, 26, 19, endrod("down"))
        _door_through(d, 33, 23, 19, "east", "birch", (-1, 0))
        _door_through(d, 39, 23, 19, "west", "birch", (1, 0))
        d.set(32, 23, 19, AIR)
        nC = {4: 6, 5: 18}[L]
        lv += raise_building(d, P, (20, 29, 32, 43), 2, nC, NT_C_PLANS, nt_c_floors(nC), "cherry", "cherry",
                             doors=[(26, 29, "north")], st=NT_TOWER_C)
        d.sign(26, 6, 28, "north", ["GARDEN", "PAVILION"], "birch", glow=True, color="cyan")
        for x in range(25, 28):
            for z in range(23, 29):
                d.set(x, 1, z, "polished_andesite")
        for x, z in ((36, 30), (44, 30), (36, 40), (44, 40)):
            tree(d, x, z, 2, h=5)
        for x, z in cells(38, 33, 42, 37):
            if x in (38, 42) or z in (33, 37):
                d.set(x, 2, z, slab("smooth_quartz"))
        d.set(40, 2, 35, "water[level=0]")
        d.set(40, 1, 35, "sea_lantern")
    if L >= 5:                                        # crown on tower B, west club roof pavilion
        top = 3 + 5 * 18 - 1
        for x, z in ((39, 8), (49, 8), (39, 22), (49, 22)):
            for y in range(top + 1, top + 6):
                d.set(x, y, z, "sea_lantern" if y % 2 else "white_concrete")
            d.set(x, top + 6, z, endrod("up"))
        for y in range(top + 1, top + 4):
            d.set(44, y, 15, "iron_bars")
        d.set(44, top + 4, 15, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    return d


def grow_sky_hw(d, L):
    P = "Hearthwood"
    regrid(d, 63, 53, 16, 0, 48)
    lv = [7, 12, 17]
    for x in range(0, 63):                            # street pavement with lamps
        d.set(x, 1, 0, "stone_bricks")
    for x in (3, 11, 19, 43, 51, 59):
        lamp_post(d, x, 1, 2, P, 3)
    if L >= 2:                                        # west wing: residents' dining hall, library, guest lounge
        lv += raise_building(d, P, (2, 5, 14, 29), 2, {2: 3, 3: 4, 4: 4, 5: 5}[L], HW_W_PLANS, HW_W_FLOORS, "oak",
                             "oak", extra=[(x, z) for x in (4, 5, 6) for z in (21, 22)], roof="gable", axis="z", doors=[(8, 5, "north")], st=HW_WEST)
        d.sign(8, 5, 4, "north", ["Albion", "Club"], "dark_oak") if d.air(8, 5, 4) else None
        flowerbed(d, 3, 1, 6, 3, 2, P)
        flowerbed(d, 10, 1, 13, 3, 2, P)
    if L >= 3:                                        # east wing: billiard room, smoking room, reading room
        lv += raise_building(d, P, (48, 5, 60, 29), 2, {3: 4, 4: 4, 5: 5}[L], HW_E_PLANS, HW_E_FLOORS, "dark_oak",
                             "dark_oak", extra=[(x, z) for x in (4, 5, 6) for z in (21, 22)], roof="gable", axis="z", doors=[(54, 5, "north")],
                   st=HW_EAST if L >= 4 else dict(HW_EAST, roof="deepslate_tile"))
        flowerbed(d, 49, 1, 52, 3, 2, P)
        flowerbed(d, 56, 1, 59, 3, 2, P)
    if L >= 4:                                        # south range closing a garden court
        lv += raise_building(d, P, (2, 38, 60, 50), 2, {4: 3, 5: 6}[L], HW_S_PLANS, HW_S_FLOORS, "spruce", "spruce",
                             roof="gable", axis="x", doors=[(31, 38, "north"), (12, 38, "north"), (50, 38, "north")],
                             st=HW_SOUTH)
        for x, z in cells(16, 26, 46, 36):
            d.set(x, 1, z, "grass_block[snowy=false]")
        path_line(d, [(31, z) for z in range(25, 38)], 1, "gravel")
        path_line(d, [(x, 28) for x in range(16, 47)], 1, "gravel")
        for x, z in cells(29, 26, 33, 30):                 # fountain
            if x in (29, 33) or z in (26, 30):
                d.set(x, 2, z, slab("stone_brick"))
            else:
                d.set(x, 1, z, "water[level=0]")
        d.set(31, 2, 28, "stone_brick_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
        for x, z in ((18, 27), (44, 27), (18, 35), (44, 35)):
            tree(d, x, z, 2, "oak_log", "oak_leaves", 5)
        for x, z in ((24, 28), (38, 28), (24, 34), (38, 34)):
            flowerbed(d, x, z, x + 1, z + 1, 2, P)
        bench(d, 26, 31, 2, P, "west")
        bench(d, 36, 31, 2, P, "east")
    if L >= 5:                                        # link ranges (coach houses) closing the court corners
        lv += raise_building(d, P, (2, 30, 14, 37), 2, 5, HW_LW_PLANS, HW_LW_FLOORS, "jungle", "jungle", extra=[(x, z) for x in (4, 5, 6) for z in (0, 1)],
                             roof="gable", axis="z", doors=[(14, 33, "east")], stair=False, chimneys=False, st=HW_LINK)
        lv += raise_building(d, P, (48, 30, 60, 37), 2, 5, HW_LE_PLANS, HW_LE_FLOORS, "jungle", "jungle", extra=[(x, z) for x in (4, 5, 6) for z in (0, 1)],
                             roof="gable", axis="z", doors=[(48, 33, "west")], stair=False, chimneys=False, st=HW_LINK)
        for Y in (2, 7, 12, 17, 22):                  # through-doors from the wings into the link ranges
            for xx in (8, 54):
                for zz, fc in ((29, "south"), (30, "south")):
                    d.door(xx, Y, zz, fc, "dark_oak")
                for zz in (28, 31):
                    for k in (0, 1, 2):
                        d.set(xx, Y + k, zz, AIR)
    if L >= 5:                                        # glass orangery in the court
        for x, z in cells(17, 32, 23, 36):
            d.set(x, 1, z, "stone_bricks")
            for y in (2, 3, 4):
                if x in (17, 23) or z in (32, 36):
                    corner = x in (17, 23) and z in (32, 36)
                    d.set(x, y, z, "white_terracotta" if corner or y == 2 else "glass_pane")
            d.set(x, 5, z, "glass" if not (x in (17, 23) or z in (32, 36)) else "white_terracotta")
        d.door(20, 2, 32, "north", "oak")
        for x, z in ((18, 34), (19, 35), (22, 34), (21, 35)):
            d.set(x, 2, z, ("potted_orange_tulip", "flowering_azalea", "potted_fern",
                            "azalea")[(x + z) % 4])
        d.set(20, 4, 34, lantern())
    if L >= 5:                                        # bandstand and lamps in the court
        for x, z in cells(38, 31, 42, 35):
            d.set(x, 1, z, "stone_bricks")
            if x in (38, 42) and z in (31, 35):
                for y in range(2, 5):
                    d.set(x, y, z, "oak_fence")
            elif (x in (38, 42) or z in (31, 35)) and not (x == 40 and z == 31):
                d.set(x, 2, z, "oak_fence")
        d.hip(38, 31, 42, 35, 5, "granite_stairs", "granite_slab")
        d.set(40, 4, 33, lantern())
        d.chair(40, 2, 34, "south", "oak", sit=False)
        for x, z in ((20, 26), (42, 26), (20, 36), (24, 31)):
            lamp_post(d, x, z, 2, P, 3)
    if L >= 5:                                        # clock tower over the south range gate
        tx1, tz1 = 28, 33
        for y in range(2, 33):
            for x, z in cells(tx1, tz1, tx1 + 6, tz1 + 4):
                if x in (tx1, tx1 + 6) or z in (tz1, tz1 + 4):
                    if not (2 <= y <= 5 and z in (tz1, tz1 + 4) and tx1 + 2 <= x <= tx1 + 4):
                        d.set(x, y, z, "calcite" if (x in (tx1, tx1 + 6) and z in (tz1, tz1 + 4) and y % 2)
                              else "bricks")
        for x in range(tx1 + 1, tx1 + 6):
            for y in (27, 28):
                d.set(x, y, tz1, "glass_pane" if x == tx1 + 3 else "bricks")
        d.hip(tx1, tz1, tx1 + 6, tz1 + 4, 33, "deepslate_tile_stairs", "deepslate_tile_slab")
        d.set(tx1 + 3, 37, tz1 + 2, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        d.set(tx1 + 3, 25, tz1 - 1, "white_wall_banner[facing=north]")
    return d


def grow_sky_ca(d, L):
    P = "Cascadia"
    regrid(d, 64, 64, 16, 0, 80)
    lv = [7, 12]
    grass = [(x, z) for x, z in cells(0, 0, 63, 63) if d.get(x, 1, z) == "minecraft:coarse_dirt"]
    path_line(d, [(x, 0) for x in range(0, 64)], 1, "gravel")
    for x in (4, 12, 48, 56):
        lamp_post(d, x, 2, 2, P, 3)
    if L >= 2:                                        # great hall chalet (restaurant + loft lounge)
        lv += raise_building(d, P, (2, 6, 16, 24), 2, 2 if L < 5 else 3, CA_HALL_PLANS, CA_HALL_FLOORS, "mangrove",
                             "spruce", roof="gable", axis="z", doors=[(9, 6, "north")], st=CA_HALL)
        for x in range(2, 17):                         # covered porch
            d.set(x, 6, 3, slab("dark_oak"))
            d.set(x, 6, 4, slab("dark_oak"))
            d.set(x, 6, 5, slab("dark_oak"))
        for x in (2, 9, 16):
            for y in range(2, 6):
                d.set(x, y, 3, log("spruce_log", "y"))
        for x, z in cells(2, 3, 16, 5):
            d.set(x, 1, z, "spruce_planks")
        d.sign(9, 5, 2, "north", ["GREAT", "HALL"], "spruce")
        for x in (5, 6, 7, 13, 14, 15):                 # firewood stacked against the porch rail
            d.set(x, 2, 2, log("spruce_log", "z"))
            d.set(x, 3, 2, log("spruce_log", "z"))
        for x in (4, 14):
            tree(d, x, 28, 2, "spruce_log", "spruce_leaves", 6)
        # fire circle between the hall and the lodge: stone ring, log benches, wood stack
        for x, z in cells(19, 29, 23, 33):
            if x in (19, 23) or z in (29, 33):
                d.set(x, 1, z, "cobblestone")
        d.set(21, 1, 31, "cobblestone")
        d.set(21, 2, 31, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        for x in (20, 21, 22):
            d.set(x, 2, 29, log("stripped_spruce_log", "x"))
            d.set(x, 2, 33, log("stripped_spruce_log", "x"))
        for z in (30, 31, 32):
            d.set(19, 2, z, log("stripped_spruce_log", "z"))
        for z in (30, 31, 32):
            for y in (2, 3, 4):
                d.set(25, y, z, log("spruce_log", "x"))
            d.set(25, 5, z, slab("spruce"))
        lamp_post(d, 23, 35, 2, P, 3)
    if L >= 3:                                        # east wing: game room, library, guest lounge
        lv += raise_building(d, P, (46, 4, 58, 28), 2, {3: 4, 4: 4, 5: 4}[L], CA_E_PLANS, CA_E_FLOORS, "birch", "birch",
                             roof="gable", axis="z", doors=[(52, 4, "north"), (46, 16, "west")], st=CA_EAST)
        for x in range(41, 46):                        # covered walkway to the lodge
            for z in (15, 16, 17):
                d.set(x, 1, z, "spruce_planks")
                d.set(x, 6, z, slab("dark_oak"))
            for z in (15, 17):
                if x % 2:
                    for y in range(2, 6):
                        d.set(x, y, z, fence("spruce"))
        for x, z in ((50, 34), (56, 34), (42, 2), (61, 32), (61, 8)):
            tree(d, x, z, 2, "spruce_log", "spruce_leaves", 6)
        for x in (47, 57):
            lamp_post(d, x, 2, 2, P, 3)
        bench(d, 49, 2, 2, P, "south", 3)
        flowerbed(d, 54, 1, 57, 2, 2, P)
        for z in (8, 14, 20, 26):                      # firewood stacked along the wing's east wall
            for y in (2, 3, 4):
                d.set(59, y, z, log("spruce_log", "x"))
                d.set(59, y, z + 1, log("spruce_log", "x"))
            d.set(59, 5, z, slab("spruce"))
            d.set(59, 5, z + 1, slab("spruce"))
    if L >= 4:                                        # lookout tower and the bathhouse
        nT = {4: 9, 5: 13}[L]
        lv += raise_building(d, P, (22, 40, 30, 50), 2, nT, CA_T_PLANS, ca_t_floors(nT), "dark_oak", "dark_oak",
                             roof="hip", doors=[(26, 40, "north")], st=CA_TOWER)
        lv += raise_building(d, P, (2, 32, 16, 46), 2, 2, CA_B_PLANS, ["pool", "sauna"], "spruce", "spruce",
                             roof="gable", axis="x", doors=[(9, 32, "north")], st=CA_BATH)
        lv += raise_building(d, P, (2, 50, 16, 62), 2, 2, CA_N_PLANS, ["stable", "hayloft"], "spruce", "spruce",
                             roof="gable", axis="x", doors=[(9, 50, "north")], st=CA_BARN)
        path_line(d, [(9, z) for z in range(47, 50)], 1, "gravel")
        # under the eaves of the bathhouse and the barn: rain barrels, benches, log piles, hay
        for x, z, b in ((3, 31, "barrel[facing=up,open=false]"), (12, 31, log("spruce_log", "x")),
                        (13, 31, log("spruce_log", "x")), (15, 31, "potted_fern"), (7, 31, "potted_fern"),
                        (3, 47, "barrel[facing=up,open=false]"), (4, 47, log("spruce_log", "x")),
                        (5, 47, log("spruce_log", "x")), (6, 47, log("spruce_log", "x")), (15, 47, "potted_fern"),
                        (3, 49, "water_cauldron[level=3]"), (4, 49, "hay_block[axis=y]"), (5, 49, "hay_block[axis=y]"),
                        (13, 49, "barrel[facing=up,open=false]"), (15, 49, "hay_block[axis=y]"),
                        (3, 63, log("spruce_log", "x")), (4, 63, log("spruce_log", "x")), (5, 63, log("spruce_log", "x")),
                        (10, 63, "hay_block[axis=y]"), (11, 63, "hay_block[axis=y]"), (13, 63, "barrel[facing=up,open=false]")):
            d.set(x, 2, z, b)
            if "log" in b or (x == 15 and "hay" in b):
                d.set(x, 3, z, b)
        d.chair(4, 2, 31, "south", "spruce", sit=False)
        d.chair(5, 2, 31, "south", "spruce", sit=False)
        d.chair(12, 2, 47, "north", "spruce", sit=False)
        d.chair(13, 2, 47, "north", "spruce", sit=False)
        path_line(d, [(26, z) for z in range(31, 40)], 1, "gravel")
        path_line(d, [(9, z) for z in range(25, 32)], 1, "gravel")
    if L >= 5:                                        # south chalet wing: dining room, suites lounge, library
        lv += raise_building(d, P, (38, 36, 58, 52), 2, 7, CA_S_PLANS, CA_S_FLOORS, "spruce", "dark_oak",
                             roof="gable", axis="x", doors=[(48, 36, "north")], st=CA_SOUTH)
        for x, z in ((34, 56), (20, 56), (44, 58), (58, 58)):
            tree(d, x, z, 2, "spruce_log", "spruce_leaves", 7)
    for x, z in grass:                               # meadow; trodden ground under eaves, decks and porches
        if d.get(x, 1, z) != "minecraft:coarse_dirt":
            continue
        if any(not d.air(x, yy, z) and "leaves" not in d.get(x, yy, z) for yy in range(2, 16)):
            d.set(x, 1, z, "packed_mud" if (x + z) % 3 else "coarse_dirt")
        else:
            d.set(x, 1, z, "grass_block[snowy=false]" if (x * 7 + z * 3) % 6 else "moss_block")
    return d


# Early levels build with common materials; from L4 the complexes may show off quartz & co.
CHEAP_NT = {"smooth_quartz_stairs": "polished_diorite_stairs", "smooth_quartz_slab": "smooth_stone_slab",
            "smooth_quartz": "white_concrete", "quartz_block": "white_concrete", "quartz_pillar": "white_concrete",
            "quartz_slab": "smooth_stone_slab", "quartz_stairs": "polished_diorite_stairs",
            "cut_copper_slab": "smooth_stone_slab", "cut_copper": "white_concrete"}


def economise(d, L, table=CHEAP_NT):
    """L1-3: swap the premium bulk materials for common ones (props kept where the new block has them)."""
    if L > 3:
        return d
    from blueprint import parse_state, format_state
    bp = d.bp
    for y in range(bp.sy):
        for z in range(bp.sz):
            row = bp.grid[y][z]
            for x in range(bp.sx):
                st = row[x]
                if "quartz" not in st and "copper" not in st:
                    continue
                name, props = parse_state(st)
                new = table.get(name.split(":")[1])
                if not new:
                    continue
                if not (new.endswith("_stairs") or new.endswith("_slab")):
                    props = {}
                row[x] = format_state("minecraft:" + new, props)
    return d


@design("skytower")
def skytower(pack, rel, L):
    core = {"Neoterra": skytower_nt, "Hearthwood": skytower_hw, "Cascadia": skytower_ca}[pack](rel, L)
    d = {"Neoterra": grow_sky_nt, "Hearthwood": grow_sky_hw, "Cascadia": grow_sky_ca}[pack](core, L)
    return economise(d, L) if pack == "Neoterra" else d


# ---------------------------------------------------------------------------------------------- twin builder growth
NT_DEPOT_STORE = dict(trim="gray_concrete", fin="yellow_concrete", glass="gray_stained_glass_pane", clad="gray_concrete",
                      band=("yellow_concrete", "black_concrete"), edge="gray_concrete", parapet="gray_concrete",
                      coping="smooth_stone", door="spruce")
NT_DEPOT_OFFICE = dict(trim="orange_terracotta", fin="birch_planks", glass="glass_pane", clad="orange_terracotta",
                       band=("white_concrete", "orange_terracotta"), edge="smooth_quartz", parapet="white_concrete",
                       coping="smooth_quartz", door="birch", green=True)
NT_DEPOT_HALL = dict(trim="polished_blackstone", fin="brown_terracotta", glass="light_gray_stained_glass_pane",
                     clad="brown_terracotta", band=("polished_blackstone", "yellow_terracotta"),
                     edge="polished_blackstone", parapet="polished_blackstone", coping="polished_blackstone",
                     door="dark_oak", roof="deepslate_tile", gable="brown_terracotta")
NT_DEPOT_CANTEEN = dict(trim="white_concrete", fin="magenta_concrete", glass="light_blue_stained_glass_pane",
                        clad="white_terracotta", band=("white_concrete", "magenta_terracotta"), edge="smooth_quartz",
                        parapet="white_concrete", coping="cut_copper", door="cherry", green=True)
HW_YARD_BARN = dict(wall0="stone_bricks", wall="spruce_planks", frame="spruce_log", plinth="cobblestone",
                    quoin="stone_bricks", lintel="spruce_planks", band="spruce_planks", roof="spruce",
                    gable="spruce_planks", door="spruce", box="spruce")
HW_YARD_OFFICE = dict(wall0="bricks", wall="pink_terracotta", frame="oak_log", plinth="stone_bricks", quoin="bricks",
                      lintel="oak_planks", band="oak_planks", roof="mud_brick", gable="pink_terracotta", door="oak",
                      box="oak", chimney="bricks")
HW_YARD_JOINERY = dict(wall0="stone_bricks", wall="white_terracotta", frame="dark_oak_log", plinth="mossy_stone_bricks",
                       quoin="stone_bricks", lintel="dark_oak_planks", band="dark_oak_planks", roof="deepslate_tile",
                       gable="white_terracotta", door="dark_oak", box="dark_oak", chimney="stone_bricks")
HW_YARD_MASONS = dict(wall0="sandstone", wall="smooth_sandstone", plinth="cut_sandstone", quoin="chiseled_sandstone",
                      lintel="cut_sandstone", band="cut_sandstone", roof="granite", gable="smooth_sandstone",
                      door="jungle", box="jungle", chimney="sandstone")
CA_YARD_SHED = dict(wall="birch_planks", trim="spruce_log", band="dark_oak_planks", roof="cobbled_deepslate",
                    gable="birch_planks", shutter="spruce", door="birch")
CA_YARD_BUNK = dict(wall="mangrove_planks", trim="dark_oak_log", band="yellow_terracotta", roof="spruce",
                    gable="mangrove_planks", shutter="dark_oak", door="mangrove")
CA_YARD_MILL = dict(wall0="tuff", wall="dark_oak_planks", trim="stripped_spruce_log", band="red_terracotta",
                    roof="dark_prismarine", gable="dark_oak_planks", shutter="spruce", door="dark_oak")
CA_YARD_COOK = dict(wall="spruce_log", trim="stripped_spruce_log", band="green_terracotta", roof="deepslate_tile",
                    gable="spruce_planks", shutter="mangrove", door="spruce")


def loading_dock(d, x1, x2, z, y, pack):
    """Raised dock apron with bollards and pallets in front of a store door row."""
    for x in range(x1, x2 + 1):
        d.set(x, y - 1, z, "smooth_stone" if pack == "Neoterra" else "stone_bricks")
    for x in (x1, x2):
        d.set(x, y, z, "yellow_concrete" if pack == "Neoterra" else "barrel[facing=up,open=false]")


def grow_twin_nt(d, L):
    P = "Neoterra"
    regrid(d, 52, 56, 0, 0, 44)
    lv = [2]
    for x, z in cells(33, 0, 51, 55):
        d.set(x, 1, z, "smooth_stone" if (x // 3 + z // 3) % 2 else "light_gray_concrete")
    for x in (0, 7, 21, 28, 35, 42, 49):
        lamp_post(d, x, 0, 2, P, 4)
    if L >= 2:                                        # materials store hall with roller doors and a dock
        lv += raise_building(d, P, (34, 4, 48, 16), 2, 1, {"store": NT_STORE_PLAN}, ["store"], "spruce", "smooth_stone",
                             H=6, extra=[(x, z) for x in (1, 2, 3, 4, 9, 10, 11, 12) for z in (0, 1)],
                             doors=[(41, 4, "north")], st=NT_DEPOT_STORE)
        for x in (37, 45):
            d.clear(x, 2, 4, x + 1, 4, 4)
            for xx in (x - 1, x + 2):
                for y in range(2, 6):
                    d.set(xx, y, 4, "yellow_concrete" if y % 2 else "black_concrete")
        loading_dock(d, 35, 47, 3, 2, P)
        d.sign(41, 6, 3, "north", ["MATERIALS", "STORE"], "birch", glow=True, color="yellow")
        for x, z in cells(35, 18, 38, 18):
            pallet_stack(d, x, z, 2, ("bricks", "white_concrete", "glass", "smooth_stone")[x % 4], 2)
    if L >= 3:                                        # site management offices (plans room, offices, lounge)
        lv += raise_building(d, P, (34, 21, 48, 31), 2, 3, NT_OFFICE_PLANS, ["reception", "plans", "meeting"], "birch",
                             "birch", doors=[(41, 21, "north")], st=NT_DEPOT_OFFICE)
        d.sign(41, 6, 20, "north", ["SITE", "MANAGEMENT"], "birch", glow=True, color="cyan")
        for x in (36, 46):
            tree(d, x, 19, 2, h=4)
    if L >= 4:                                        # precast production hall behind the yard
        for x in range(14, 19):
            d.set(x, 2, 26, AIR)
            d.set(x, 3, 26, AIR)
        lv += raise_building(d, P, (2, 29, 30, 44), 2, 2, NT_HALL_PLANS, ["casting", "finishing"], "dark_oak",
                             "polished_andesite", H=6, roof="gable", axis="x", chimneys=False,
                             doors=[(16, 29, "north"), (2, 36, "west")], st=NT_DEPOT_HALL)
        for x in (8, 13, 18, 23):                      # gantry rail along the hall front
            for y in range(2, 9):
                d.set(x, y, 27, "yellow_concrete" if y % 3 == 2 else "iron_bars")
        for x in range(7, 27):
            d.set(x, 9, 27, "yellow_concrete")
        d.sign(16, 8, 28, "north", ["PRECAST", "WORKS"], "birch", glow=True, color="yellow")
    if L >= 5:                                        # workers' canteen, lockers and gym; second crane
        lv += raise_building(d, P, (34, 35, 49, 53), 2, 5, NT_CANTEEN_PLANS, NT_CANTEEN_FLOORS, "cherry", "birch",
                             doors=[(41, 35, "north")], st=NT_DEPOT_CANTEEN)
        d.sign(41, 6, 34, "north", ["CANTEEN"], "birch", glow=True, color="magenta")
        for x, z in cells(2, 47, 30, 54):
            d.set(x, 1, z, "gray_concrete")
        for x in (4, 10, 16, 22, 28):                  # plant yard: excavator stand-ins and skips
            for z in (49, 52):
                d.set(x, 2, z, "yellow_concrete")
                d.set(x + 1, 2, z, "yellow_concrete")
                d.set(x, 3, z, "black_concrete")
                d.set(x + 1, 3, z, "glass")
        for y in range(2, 26):
            d.set(16, y, 46, "yellow_concrete" if y % 3 == 2 else "iron_bars")
        for x in range(6, 32):
            d.set(x, 26, 46, "yellow_concrete")
        d.set(16, 27, 46, "yellow_concrete")
        d.set(16, 28, 46, "red_concrete")
        for y in range(16, 26):
            d.set(28, y, 46, chain())
        d.set(28, 15, 46, "white_concrete")
    return d


def grow_twin_hw(d, L):
    P = "Hearthwood"
    regrid(d, 56, 54, 0, 0, 34)
    lv = [2, 7]
    path_line(d, [(x, 0) for x in range(0, 56)], 1, "gravel")
    for x in (1, 10, 19, 28, 37, 46, 55):
        lamp_post(d, x, 0, 2, P, 3)
    if L >= 2:                                        # timber seasoning barn behind the workshop
        lv += raise_building(d, P, (2, 21, 12, 35), 2, 2, HW_BARN_PLANS, ["timber", "loft"], "spruce", "oak",
                             roof="gable", axis="z", chimneys=False, doors=[(7, 21, "north")], st=HW_YARD_BARN)
        for z in (36, 37):                             # log pile outside the barn
            for x in range(3, 11):
                d.set(x, 2, z, log("oak_log", "x"))
                d.set(x, 3, z, log("oak_log", "x"))
    if L >= 3:                                        # clerk of works' office and drawing room
        lv += raise_building(d, P, (33, 2, 45, 12), 2, 3, HW_CLERK_PLANS, ["clerk", "drawing", "archive"], "oak", "oak",
                             roof="gable", axis="x", doors=[(39, 12, "south")], st=HW_YARD_OFFICE)
        flowerbed(d, 34, 14, 37, 15, 2, P)
        flowerbed(d, 41, 14, 44, 15, 2, P)
        d.sign(39, 5, 13, "south", ["Clerk of", "Works"], "dark_oak")
    if L >= 4:                                        # joinery shop with timber store above
        lv += raise_building(d, P, (33, 17, 53, 31), 2, 2, HW_JOIN_PLANS, ["bench", "store"], "dark_oak", "oak",
                             roof="gable", axis="x", doors=[(43, 17, "north"), (33, 24, "west")], st=HW_YARD_JOINERY)
        d.sign(43, 5, 16, "north", ["Joinery"], "dark_oak")
        for x in range(35, 52, 2):                     # seasoned boards stacked on bearers by the shop
            pallet_stack(d, x, 33, 2, "oak_planks" if x % 4 == 1 else "spruce_planks", 5,
                         "oak_slab[type=bottom,waterlogged=false]")
        lamp_post(d, 33, 33, 2, P, 3)
        lv += raise_building(d, P, (47, 34, 53, 40), 2, 1, {"tools": HW_TOOL_PLAN}, ["tools"], "oak", "oak",
                             roof="gable", axis="z", stair=False, chimneys=False, doors=[(50, 34, "north")], st=dict(HW_YARD_BARN, roof="dark_oak"))
        for x in range(36, 46, 3):                     # sawhorses with a plank across
            d.set(x, 2, 35, fence("oak"))
            d.set(x + 1, 2, 35, fence("oak"))
            d.set(x, 3, 35, slab("oak"))
            d.set(x + 1, 3, 35, slab("oak"))
        for x in range(31, 33):
            for z in range(14, 33):
                d.set(x, 1, z, "gravel")
    if L >= 5:                                        # masons' hall with the workers' mess upstairs
        lv += raise_building(d, P, (2, 39, 30, 51), 2, 3, HW_MASON_PLANS, ["banker", "mess", "tracing"], "jungle", "spruce",
                             roof="gable", axis="x", doors=[(16, 39, "north"), (30, 48, "east")], st=HW_YARD_MASONS)
        lv += raise_building(d, P, (34, 43, 45, 51), 2, 1, {"cart": HW_CART_PLAN}, ["cart"], "spruce", "spruce",
                             roof="gable", axis="x", stair=False, chimneys=False, doors=[(39, 43, "north")], st=HW_YARD_OFFICE)
        for i, (x, z) in enumerate(((47, 42), (49, 42), (51, 42), (47, 46), (49, 46), (51, 46), (47, 50), (49, 50),
                                    (51, 50))):           # dressed stone waiting on pallets
            pallet_stack(d, x, z, 2, ("stone_bricks", "bricks", "cobblestone")[i % 3], 2,
                         "oak_slab[type=bottom,waterlogged=false]")
        for x in (14, 18):
            for y in range(2, 9):
                d.set(x, y, 36, log("dark_oak_log", "y"))
        for x in range(13, 20):
            d.set(x, 9, 36, log("dark_oak_log", "x"))
        for y in range(5, 9):
            d.set(16, y, 36, chain())
        d.set(16, 4, 36, "stone_bricks")
    return d


def grow_twin_ca(d, L):
    P = "Cascadia"
    regrid(d, 56, 54, 0, 0, 34)
    lv = [2]
    for x, z in cells(33, 0, 55, 53):
        d.set(x, 1, z, "grass_block[snowy=false]" if (x * 5 + z * 3) % 7 else "moss_block")
    for x, z in cells(0, 31, 32, 53):
        d.set(x, 1, z, "coarse_dirt" if (x + z) % 5 else "gravel")
    if L >= 2:                                        # open-sided lumber drying shed (birch board ends)
        lv += raise_building(d, P, (34, 3, 50, 13), 2, 1, {"drying": CA_SHED_PLAN}, ["drying"], "spruce", "spruce",
                             roof="gable", axis="x", chimneys=False, doors=[(42, 13, "south"), (42, 3, "north")], st=CA_YARD_SHED)
        for x in list(range(35, 40)) + list(range(45, 50)):    # stickered lumber outside
            for y in (2, 3):
                d.set(x, y, 15, log("stripped_spruce_log", "x"))
    if L >= 3:                                        # framers' bunkhouse and office
        lv += raise_building(d, P, (36, 18, 48, 29), 2, 2, CA_BUNK_PLANS, ["office", "mess"], "mangrove", "spruce",
                             roof="gable", axis="x", doors=[(42, 18, "north")], st=CA_YARD_BUNK)
        for x in range(36, 49):                         # porch
            d.set(x, 6, 16, slab("spruce"))
            d.set(x, 6, 17, slab("spruce"))
        for x in (36, 48):
            for y in range(2, 6):
                d.set(x, y, 16, log("spruce_log", "y"))
        d.chair(38, 2, 17, "west", "spruce", sit=False)
        d.chair(46, 2, 17, "east", "spruce", sit=False)
    if L >= 4:                                        # sawmill hall with log deck and chute
        lv += raise_building(d, P, (2, 33, 24, 47), 2, 2, CA_MILL_PLANS, ["saw", "filing"], "dark_oak", "spruce",
                             roof="gable", axis="x", doors=[(13, 33, "north"), (24, 44, "east")], st=CA_YARD_MILL)
        for x in range(4, 22):
            for y in (2, 3):
                d.set(x, y, 50, log("spruce_log", "x"))
            d.set(x, 4, 50, log("spruce_log", "x")) if x % 2 else None
        d.sign(13, 6, 32, "north", ["SAWMILL"], "spruce")
    if L >= 5:                                        # cookhouse with dining hall and a log water tower
        lv += raise_building(d, P, (30, 34, 50, 48), 2, 3, CA_COOK_PLANS, ["dining", "kitchen", "lounge"], "spruce", "spruce",
                             roof="gable", axis="x", doors=[(40, 34, "north")], st=CA_YARD_COOK)
        for x, z in ((52, 36), (54, 36), (52, 38), (54, 38)):
            for y in range(2, 10):
                d.set(x, y, z, log("spruce_log", "y"))
        for x, z in cells(51, 35, 55, 39):
            d.set(x, 10, z, "spruce_planks")
        for y in (11, 12, 13):
            for x, z in cells(52, 36, 54, 38):
                d.set(x, y, z, "barrel[facing=up,open=false]" if (x, z) == (53, 37) and False else
                      log("stripped_spruce_log", "y"))
        for x, z in cells(51, 35, 55, 39):
            d.set(x, 14, z, slab("dark_oak"))
    return d


@design("twinbuilder")
def twinbuilder(pack, rel, L):
    core = {"Neoterra": twin_nt, "Hearthwood": twin_hw, "Cascadia": twin_ca}[pack](rel, L)
    d = {"Neoterra": grow_twin_nt, "Hearthwood": grow_twin_hw, "Cascadia": grow_twin_ca}[pack](core, L)
    return economise(d, L) if pack == "Neoterra" else d


@design("twinbuilderannex")
def twinbuilderannex(pack, rel, L):
    return {"Neoterra": annex_nt, "Hearthwood": annex_hw, "Cascadia": annex_ca}[pack](rel, L)
