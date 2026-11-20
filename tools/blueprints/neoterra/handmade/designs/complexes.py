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


def rail_openings(d, rail, levels):
    """Guard every opening in a walkable floor (stair wells, deck holes over outside stairs, lofts): any open cell
    next to a reachable standing cell with a drop of 2+ below it, under a roof/ceiling, gets a railing. Over a
    flight the railing sits high enough to keep 3 blocks of headroom above the steps; the top steps (a drop of
    0-1, the stair's own entry) stay open. `levels` = the walking levels of the floors/decks/lofts to guard.
    Repeats until nothing changes. Returns the cells railed."""
    import walkcheck
    done = []
    for _ in range(4):
        n = len(done)
        _rail_pass(d, rail, levels, walkcheck.analyse(d.bp, True)[2], done)
        if len(done) == n:
            break
    return done


def _rail_pass(d, rail, levels, seen, done):
    for (x, y, z) in sorted(seen):
        if y not in levels:
            continue
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, nz = x + dx, z + dz
            if not d.bp.inside(nx, y + 1, nz) or (nx, y, nz) in seen:
                continue
            if not (d.air(nx, y, nz) and d.air(nx, y + 1, nz) and d.air(nx, y - 1, nz) and y >= 2
                    and d.air(nx, y - 2, nz)):
                continue
            if not any(not d.air(nx, yy, nz) for yy in range(y + 2, min(d.sy, y + 9))):
                continue                                     # open sky: not an indoor/deck opening
            b = y - 3
            while b > 0 and d.air(nx, b, nz):
                b -= 1
            yr = max(y, b + 4) if "stairs" in d.get(nx, b, nz) else y
            if yr <= y + 1 and d.air(nx, yr, nz):
                d.set(nx, yr, nz, rail)
                done.append((nx, yr, nz))


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
            d.chair(x, y, 2, "south", "birch")
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
        for x in range(1, 11, 2):
            for z in range(1, 11, 3):
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
    ridge = d.gable(X1, Z1, X2, Z2, 10, "z", "dark_prismarine_stairs", "dark_prismarine_slab", "calcite")
    for z in (Z1, Z2):
        for y in range(10, ridge):
            if d.get(7, y, z) == "minecraft:calcite":
                d.set(7, y, z, log("dark_oak_log", "y"))
    # cart doors, loft door + hoist beam with pulley and a load
    d.clear(6, 2, Z1, 8, 4, Z1)
    for x in (6, 7, 8):
        d.set(x, 5, Z1, log("dark_oak_log", "x"))
    d.door(7, 7, Z1, "north", "dark_oak")
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

WALL_SEQ = {
    "lounge": ["sofa", "sofa", "plant", "shelf", "books", "sofa", "sofa", "lamp"],
    "library": ["books2", "books2", "chisel", "books2", "books2", "plant"],
    "office": ["crate", "chisel", "plant", "carto", "shelf", "chest", "lectern"],
    "gym": ["weights", "bench", "plant", "target", "weights", "shelf"],
    "store": ["crate2", "chest", "sack", "crate2", "shelf", "sack2"],
    "workshop": ["smith", "grind", "cutter", "crate", "anvil", "shelf", "loom", "crate2"],
    "dining": ["shelf", "plant", "chest", "shelf", "books", "lamp"],
    "kitchen": ["furnace", "smoker", "sink", "counter", "crate", "counter"],
    "drawing": ["carto", "lectern", "chisel", "crate", "plant", "shelf"],
    "bar": ["crate", "shelf", "crate", "plant", "shelf", "books"],
    "spa": ["plant", "bench", "shelf", "plant", "bench"],
    "hall": ["plant", "sofa", "sofa", "shelf", "plant", "books"],
}
CENTER = {"lounge": "groups", "library": "desks", "office": "desks", "gym": "mats", "store": "aisles",
          "workshop": "benches", "dining": "tables", "kitchen": "island", "drawing": "desks", "bar": "groups",
          "spa": "pool", "hall": "groups"}


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


def _inward(x, z, x1, z1, x2, z2):
    if z == z1:
        return "south"
    if z == z2:
        return "north"
    if x == x1:
        return "east"
    return "west"


def wall_item(d, S, k, x, y, z, inward, h):
    w = S["wood"]
    if k == "sofa":
        d.chair(x, y, z, OPP[inward], w, sit=False)
    elif k == "plant":
        d.set(x, y, z, S["plants"][(x + z) % len(S["plants"])])
    elif k == "shelf":
        d.set(x, y, z, slab(S["top"], "top"))
        d.set(x, y + 1, z, ("decorated_pot[cracked=false,facing=north,waterlogged=false]", S["plants"][1],
                            "candle[candles=3,lit=false,waterlogged=false]")[(x * 3 + z) % 3])
    elif k == "books":
        d.set(x, y, z, "bookshelf")
    elif k == "books2":
        d.set(x, y, z, "bookshelf")
        if h >= 3:
            d.set(x, y + 1, z, "bookshelf")
    elif k == "chisel":
        d.set(x, y, z, chiseled(inward))
        if h >= 3:
            d.set(x, y + 1, z, chiseled(inward))
    elif k == "crate":
        d.set(x, y, z, "barrel[facing=up,open=false]")
    elif k == "crate2":
        d.set(x, y, z, "barrel[facing=up,open=false]")
        d.set(x, y + 1, z, f"barrel[facing={inward},open=false]")
    elif k == "chest":
        d.set(x, y, z, f"chest[facing={inward},type=single,waterlogged=false]")
    elif k == "sack":
        d.set(x, y, z, "white_wool")
    elif k == "sack2":
        d.set(x, y, z, "brown_wool")
        d.set(x, y + 1, z, "white_wool")
    elif k == "carto":
        d.set(x, y, z, "cartography_table")
    elif k == "lectern":
        d.set(x, y, z, f"lectern[facing={inward},has_book=false,powered=false]")
    elif k == "smith":
        d.set(x, y, z, "smithing_table")
    elif k == "grind":
        d.set(x, y, z, f"grindstone[face=floor,facing={inward}]")
    elif k == "cutter":
        d.set(x, y, z, f"stonecutter[facing={inward}]")
    elif k == "anvil":
        d.set(x, y, z, f"anvil[facing={CW[inward]}]")
    elif k == "loom":
        d.set(x, y, z, f"loom[facing={inward}]")
    elif k == "weights":
        d.set(x, y, z, "iron_block")
        d.set(x, y + 1, z, "heavy_weighted_pressure_plate[power=0]")
    elif k == "bench":
        d.set(x, y, z, slab(S["top"], "top"))
    elif k == "target":
        d.set(x, y, z, "target[power=0]")
    elif k == "lamp":
        if S["wood"] == "birch":
            d.set(x, y, z, slab("smooth_quartz", "top"))
            d.set(x, y + 1, z, endrod("up"))
        else:
            d.set(x, y, z, fence(S["wood"]))
            d.set(x, y + 1, z, lantern(False))
    elif k in ("furnace", "smoker"):
        d.set(x, y, z, f"{k}[facing={inward},lit=false]")
    elif k == "sink":
        d.set(x, y, z, "water_cauldron[level=3]")
    elif k == "counter":
        d.set(x, y, z, slab(S["top"], "top"))
        d.set(x, y + 1, z, S["plants"][0])


def furnish(d, pack, kind, x1, z1, x2, z2, y, ceil, keep=()):
    """Furnish the interior x1..x2 / z1..z2 (walking level y, ceiling block at `ceil`): furniture along the walls,
    a layout for the room's use in the middle, rugs and ceiling lights. `keep` cells (and their neighbours) stay
    clear for doors and stairs."""
    S = STY[pack]
    h = ceil - y
    block = set()
    for kx, kz in keep:
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                block.add((kx + dx, kz + dz))

    def free(x, z):
        return (x, z) not in block and d.air(x, y, z) and d.air(x, y + 1, z) and not d.air(x, y - 1, z)
    seq = WALL_SEQ[kind]
    i = 0
    per = [(x, z) for x, z in cells(x1, z1, x2, z2) if x in (x1, x2) or z in (z1, z2)]
    for x, z in per:
        if not free(x, z):
            continue
        inward = _inward(x, z, x1, z1, x2, z2)
        if x in (x1, x2) and z in (z1, z2):                  # corners: a plant, never a work block
            d.set(x, y, z, S["plants"][(x + z) % 3])
            continue
        k = seq[i % len(seq)]
        i += 1
        wall_item(d, S, k, x, y, z, inward, h)
        if h >= 4 and i % 4 == 0 and d.air(x, y + 2, z) and k in ("sofa", "plant", "crate", "chest", "bench",
                                                                   "carto", "smith", "sink", "counter"):
            d.set(x, y + 2, z, f"{S['banner']}_wall_banner[facing={inward}]")
    # middle
    cx1, cz1, cx2, cz2 = x1 + 2, z1 + 2, x2 - 2, z2 - 2
    mode = CENTER[kind]
    w = S["wood"]

    def ok(cs):
        return all(cx1 <= a <= cx2 and cz1 <= b <= cz2 and free(a, b) for a, b in cs)
    if mode in ("groups",):
        for tz in range(cz1 + 1, cz2, 4):
            for tx in range(cx1 + 1, cx2, 5):
                cs = [(tx + a, tz + b) for a in (-1, 0, 1) for b in (-1, 0, 1)]
                if ok(cs):
                    rugc(d, tx - 1, tz - 1, tx + 1, tz + 1, y, S["rug"][(tx + tz) % 2])
                    d.set(tx, y, tz, slab(S["top"], "top"))
                    d.set(tx, y + 1, tz, S["plants"][tx % 3])
                    d.chair(tx - 1, y, tz, "west", w, sit=False)
                    d.chair(tx + 1, y, tz, "east", w, sit=False)
    elif mode in ("desks", "tables"):
        step = 4 if mode == "desks" else 5
        for tz in range(cz1 + 1, cz2, 4):
            for tx in range(cx1, cx2 - 1, step):
                L_ = 2 if mode == "desks" else 3
                cs = [(tx + a, tz + b) for a in range(L_) for b in (-1, 0, 1)]
                if ok(cs):
                    for a in range(L_):
                        d.set(tx + a, y, tz, slab(S["top"], "top") if mode == "desks" else d.P["wood"] + "_planks"
                              if False else slab(S["top"], "top"))
                        d.chair(tx + a, y, tz - 1, "north", w, sit=False)
                        d.chair(tx + a, y, tz + 1, "south", w, sit=False)
                    d.set(tx, y + 1, tz, "candle[candles=2,lit=false,waterlogged=false]" if mode == "tables"
                          else ("lantern[hanging=false,waterlogged=false]" if w != "birch" else endrod("up")))
                    d.set(tx + L_ - 1, y + 1, tz, S["plants"][(tx + tz) % 3])
    elif mode == "aisles":
        for tz in range(cz1, cz2 + 1, 3):
            for tx in range(cx1, cx2 + 1):
                if tx == (cx1 + cx2) // 2:
                    continue
                if ok([(tx, tz)]):
                    d.set(tx, y, tz, "barrel[facing=up,open=false]" if (tx + tz) % 3 else "chest[facing=north,"
                          "type=single,waterlogged=false]")
                    if h >= 3 and (tx + tz) % 2:
                        d.set(tx, y + 1, tz, ("white_wool", "hay_block[axis=y]", "barrel[facing=up,open=false]")[tx % 3])
    elif mode == "benches":
        for tz in range(cz1 + 1, cz2, 3):
            for tx in range(cx1, cx2 - 1, 5):
                cs = [(tx + a, tz) for a in range(3)] + [(tx + a, tz + b) for a in range(3) for b in (-1, 1)]
                if ok(cs):
                    for a in range(3):
                        d.set(tx + a, y, tz, slab(S["top"], "top"))
                    d.set(tx, y + 1, tz, "lantern[hanging=false,waterlogged=false]")
                    d.set(tx + 2, y + 1, tz, "decorated_pot[cracked=false,facing=north,waterlogged=false]")
    elif mode == "mats":
        for tz in range(cz1 + 1, cz2, 4):
            for tx in range(cx1, cx2 - 1, 4):
                cs = [(tx + a, tz + b) for a in range(2) for b in range(2)]
                if ok(cs):
                    rugc(d, tx, tz, tx + 1, tz + 1, y, S["rug"][1])
    elif mode == "island":
        for tz in range(cz1 + 1, cz2, 4):
            cs = [(tx, tz) for tx in range(cx1 + 1, cx2)]
            if len(cs) >= 2 and ok(cs):
                for tx, _ in cs:
                    d.set(tx, y, tz, slab(S["top"], "top"))
                d.set(cs[0][0], y + 1, tz, "decorated_pot[cracked=false,facing=north,waterlogged=false]")
    elif mode == "pool":
        if cx2 - cx1 >= 3 and cz2 - cz1 >= 2 and ok(list(cells(cx1, cz1, cx2, cz2))):
            for x, z in cells(cx1, cz1, cx2, cz2):
                edge = x in (cx1, cx2) or z in (cz1, cz2)
                d.set(x, y, z, slab(S["top"], "top") if edge else "water[level=0]")
                if not edge:
                    d.set(x, y - 1, z, "prismarine_bricks" if (x + z) % 5 else "sea_lantern")
    # ceiling lights
    for lx in range(x1 + 1, x2, 4):
        for lz in range(z1 + 1, z2, 4):
            if d.air(lx, ceil - 1, lz) and not d.air(lx, ceil, lz):
                if w == "birch":
                    d.set(lx, ceil - 1, lz, endrod("down"))
                elif h >= 5 and d.air(lx, ceil - 2, lz):
                    d.set(lx, ceil - 1, lz, chain())
                    d.set(lx, ceil - 2, lz, lantern())
                else:
                    d.set(lx, ceil - 1, lz, lantern())


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


def wing(d, pack, x1, z1, x2, z2, y0, n, kinds, H=5, roof="flat", axis="x", doors=(), stair=True, chimneys=True,
         st=None):
    """A multi-storey block in the pack's family with an internal switch-back stair on its east side, every floor
    furnished (kinds[f]), and a roof. `st` picks this building's own materials (walls, trims, roof, accents) so
    the blocks of a complex do not share one palette. Returns the walking levels."""
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
    if stair and n > 1:
        for f in range(n - 1):
            Y = y0 + H * f
            if f % 2 == 0:
                flight(d, A, zs, Y, H, "south", S["stairb"])
            else:
                flight(d, B, zs + H - 1, Y, H, "north", S["stairb"])
    for (x, z, fc) in doors:
        d.door(x, y0, z, fc, st["door"])
        if pack == "Neoterra":
            d.set(x, y0 + 2, z, st["glass"])
    # outside: window boxes (Hearthwood), shutters (Cascadia) – never in front of a door
    door_out = {(x + D4[fc][0] + a, z + D4[fc][1] + b) for (x, z, fc) in doors for a in (-1, 0, 1) for b in (-1, 0, 1)}
    if pack in ("Hearthwood", "Cascadia"):
        for f in range(n):
            Y = y0 + H * f
            for x, z in cells(x1, z1, x2, z2):
                if not (x in (x1, x2) or z in (z1, z2)) or d.get(x, Y + 1, z) != "minecraft:glass_pane":
                    continue
                out = OPP[_inward(x, z, x1, z1, x2, z2)]
                ox, oz = x + D4[out][0], z + D4[out][1]
                if not d.bp.inside(ox, Y + 1, oz) or not d.air(ox, Y + 1, oz) or (f == 0 and (ox, oz) in door_out):
                    continue
                if pack == "Hearthwood":
                    if d.air(ox, Y, oz):
                        d.set(ox, Y, oz, trap(st["box"], out, "top"))
                        d.set(ox, Y + 1, oz, S["plants"][(x + z) % 3].replace("potted_fern", "potted_blue_orchid"))
                else:
                    sx, sz = D4[CW[out]]
                    for (cx, cz), side in (((ox - sx, oz - sz), OPP[CW[out]]), ((ox + sx, oz + sz), CW[out])):
                        for k in (1, 2):
                            if d.bp.inside(cx, Y + k, cz) and d.air(cx, Y + k, cz):
                                d.set(cx, Y + k, cz, trap(st["shutter"], side, "bottom", True))
    # furnish
    keep = [(x + D4[OPP[fc]][0], z + D4[OPP[fc]][1]) for (x, z, fc) in doors]
    fx2 = x2 - 3 if stair and n > 1 else x2 - 1
    for f in range(n):
        Y = y0 + H * f
        kk = keep if f == 0 else []
        kk = kk + [(fx2, zs - 1), (fx2, zs + H), (fx2 + 1, zs + H + 1)]
        furnish(d, pack, kinds[f % len(kinds)], x1 + 1, z1 + 1, fx2, z2 - 1, Y, Y + H - 1, kk)
    # roof
    if roof == "flat":
        for x, z in cells(x1, z1, x2, z2):
            if x in (x1, x2) or z in (z1, z2):
                d.set(x, top + 1, z, st["parapet"])
                d.set(x, top + 2, z, slab(st["coping"]))
        for x, z in cells(x1 + 1, z1 + 1, x2 - 1, z2 - 1):
            if st["green"]:
                d.set(x, top, z, "moss_block" if (x + z) % 3 else "grass_block[snowy=false]")
                if (x * 5 + z * 3) % 7 == 0:
                    d.set(x, top + 1, z, ("azalea", "flowering_azalea", "fern")[(x + z) % 3])
            elif x in (x1 + 1, x2 - 1) or z in (z1 + 1, z2 - 1):
                if (x + z) % 2 == 0:
                    d.set(x, top + 1, z, "moss_block")
                    d.set(x, top + 2, z, ("azalea", "flowering_azalea")[(x // 2 + z) % 2])
            elif (x - x1) % 3 == 0 and (z - z1) % 2 == 0 and x < x2 - 3:
                d.set(x, top + 1, z, "daylight_detector[inverted=false,power=0]")
        d.set(x2 - 2, top + 1, z2 - 2, "smooth_stone")
        d.set(x2 - 2, top + 2, z2 - 2, "iron_trapdoor[facing=north,half=bottom,open=false,powered=false,"
                                       "waterlogged=false]")
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
        if pack == "Cascadia" and roof == "gable":
            ends = (z1, z2) if axis == "z" else (x1, x2)
            mid = (x1 + x2) // 2 if axis == "z" else (z1 + z2) // 2
            for e in ends:
                for yy in range(top + 1, ridge):
                    p_ = (mid, yy, e) if axis == "z" else (e, yy, mid)
                    if d.get(*p_) == _hm._mc(st["gable"]):
                        d.set(*p_, log("spruce_log", "y"))
    return levels


def lamp_post(d, x, z, y, pack, h=3):
    for k in range(h):
        d.set(x, y + k, z, {"Neoterra": "light_gray_concrete_powder" if False else "iron_bars",
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
    for x in range(2, 50, 6):
        if not 21 <= x <= 29:
            lamp_post(d, x, 2, 2, P, 4)
    for x in (4, 10, 40, 46):
        flowerbed(d, x, 4, x + 2, 5, 2, P)
    bench(d, 8, 3, 2, P, "south")
    bench(d, 41, 3, 2, P, "south")
    if L >= 2:                                        # west residents' club: gym, lounge, library (+ bar)
        lv += wing(d, P, 2, 8, 12, 22, 2, {2: 5, 3: 5, 4: 6, 5: 7}[L], ["gym", "lounge", "library", "bar", "office"],
                   doors=[(7, 8, "north")], st=NT_CLUB)
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
        lv += wing(d, P, 39, 8, 49, 22, 3, nB, ["dining", "office", "lounge", "library", "gym", "bar", "office"],
                   doors=[(44, 8, "north")], st=NT_TOWER_B)
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
            d.set(x, 26, 19, endrod("down")) if x % 2 == 0 else None
        _door_through(d, 33, 23, 19, "east", "birch", (-1, 0))
        _door_through(d, 39, 23, 19, "west", "birch", (1, 0))
        d.set(32, 23, 19, AIR)
        nC = {4: 6, 5: 18}[L]
        lv += wing(d, P, 20, 29, 32, 43, 2, nC, ["dining", "lounge", "office", "library", "gym", "bar"],
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
    rail_openings(d, "glass_pane", tuple(sorted(set(lv))))
    return d


def grow_sky_hw(d, L):
    P = "Hearthwood"
    regrid(d, 63, 53, 16, 0, 48)
    lv = [7, 12, 17]
    for x in range(0, 63):                            # street pavement with lamps
        d.set(x, 1, 0, "stone_bricks")
    for x in range(3, 62, 8):
        if not 28 <= x <= 34:
            lamp_post(d, x, 1, 2, P, 3)
    if L >= 2:                                        # west wing: residents' dining hall, library, guest lounge
        lv += wing(d, P, 2, 5, 14, 29, 2, {2: 3, 3: 4, 4: 4, 5: 5}[L], ["dining", "library", "lounge", "hall"],
                   roof="gable", axis="z", doors=[(8, 5, "north")], st=HW_WEST)
        d.sign(8, 5, 4, "north", ["Albion", "Club"], "dark_oak") if d.air(8, 5, 4) else None
        flowerbed(d, 3, 1, 6, 3, 2, P)
        flowerbed(d, 10, 1, 13, 3, 2, P)
    if L >= 3:                                        # east wing: billiard room, smoking room, reading room
        lv += wing(d, P, 48, 5, 60, 29, 2, {3: 3, 4: 4, 5: 5}[L], ["bar", "lounge", "library", "hall"],
                   roof="gable", axis="z", doors=[(54, 5, "north")], st=HW_EAST)
        flowerbed(d, 49, 1, 52, 3, 2, P)
        flowerbed(d, 56, 1, 59, 3, 2, P)
    if L >= 4:                                        # south range closing a garden court
        lv += wing(d, P, 2, 38, 60, 50, 2, {4: 3, 5: 5}[L], ["dining", "lounge", "library", "office"],
                   roof="gable", axis="x", doors=[(31, 38, "north"), (12, 38, "north"), (50, 38, "north")], st=HW_SOUTH)
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
        d.set(31, 3, 31, "water[level=0]") if False else None
        for x, z in ((18, 27), (44, 27), (18, 35), (44, 35)):
            tree(d, x, z, 2, "oak_log", "oak_leaves", 5)
        for x, z in ((24, 28), (38, 28), (24, 34), (38, 34)):
            flowerbed(d, x, z, x + 1, z + 1, 2, P)
        bench(d, 26, 31, 2, P, "west")
        bench(d, 36, 31, 2, P, "east")
    if L >= 5:                                        # link ranges (coach houses) closing the court corners
        lv += wing(d, P, 2, 30, 14, 37, 2, 5, ["store", "office", "lounge", "library", "dining"], roof="gable", axis="z",
                   doors=[(14, 33, "east")], stair=False, chimneys=False, st=HW_LINK)
        lv += wing(d, P, 48, 30, 60, 37, 2, 5, ["store", "office", "lounge", "library", "dining"], roof="gable", axis="z",
                   doors=[(48, 33, "west")], stair=False, chimneys=False, st=HW_LINK)
        for Y in (2, 7, 12, 17, 22):                  # through-doors from the wings into the link ranges
            for xx in (8, 54):
                for zz, fc in ((29, "south"), (30, "south")):
                    d.door(xx, Y, zz, fc, "dark_oak")
                for zz in (28, 31):
                    for k in (0, 1, 2):
                        d.set(xx, Y + k, zz, AIR)
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
        d.set(tx1 + 3, 29, tz1, "white_concrete") if False else None
        d.hip(tx1, tz1, tx1 + 6, tz1 + 4, 33, "deepslate_tile_stairs", "deepslate_tile_slab")
        d.set(tx1 + 3, 37, tz1 + 2, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        d.set(tx1 + 3, 25, tz1 - 1, "white_wall_banner[facing=north]")
    rail_openings(d, "dark_oak_fence", tuple(sorted(set(lv))))
    return d


def grow_sky_ca(d, L):
    P = "Cascadia"
    regrid(d, 64, 64, 16, 0, 72)
    lv = [7, 12]
    for x, z in cells(0, 0, 63, 63):
        if d.get(x, 1, z) == "minecraft:coarse_dirt":
            d.set(x, 1, z, "grass_block[snowy=false]" if (x * 7 + z * 3) % 6 else "moss_block")
    path_line(d, [(x, 0) for x in range(0, 64)], 1, "gravel")
    for x in (4, 12, 48, 56):
        lamp_post(d, x, 2, 2, P, 3)
    if L >= 2:                                        # great hall chalet (restaurant + loft lounge)
        lv += wing(d, P, 2, 6, 16, 24, 2, 2 if L < 5 else 3, ["dining", "lounge", "library"], roof="gable", axis="z",
                   doors=[(9, 6, "north")], st=CA_HALL)
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
        for x in (4, 14):
            tree(d, x, 28, 2, "spruce_log", "spruce_leaves", 6)
    if L >= 3:                                        # east wing: game room, library, guest lounge
        lv += wing(d, P, 46, 4, 58, 28, 2, {3: 3, 4: 3, 5: 4}[L], ["bar", "library", "lounge", "hall"],
                   roof="gable", axis="z", doors=[(52, 4, "north"), (46, 16, "west")], st=CA_EAST)
        for x in range(41, 46):                        # covered walkway to the lodge
            for z in (15, 16, 17):
                d.set(x, 1, z, "spruce_planks")
                d.set(x, 6, z, slab("dark_oak"))
            for z in (15, 17):
                if x % 2:
                    for y in range(2, 6):
                        d.set(x, y, z, fence("spruce"))
        for x, z in ((50, 34), (56, 34), (42, 2)):
            tree(d, x, z, 2, "spruce_log", "spruce_leaves", 6)
    if L >= 4:                                        # lookout tower and the bathhouse
        lv += wing(d, P, 22, 40, 30, 50, 2, {4: 7, 5: 11}[L], ["store", "lounge", "library", "office", "bar"],
                   roof="hip", doors=[(26, 40, "north")], st=CA_TOWER)
        lv += wing(d, P, 2, 32, 16, 46, 2, 2, ["spa", "lounge"], roof="gable", axis="x", doors=[(9, 32, "north")],
                   st=CA_BATH)
        lv += wing(d, P, 2, 50, 16, 62, 2, 2, ["store", "store"], roof="gable", axis="x", doors=[(9, 50, "north")],
                   st=CA_BARN)
        path_line(d, [(9, z) for z in range(47, 50)], 1, "gravel")
        path_line(d, [(26, z) for z in range(31, 40)], 1, "gravel")
        path_line(d, [(9, z) for z in range(25, 32)], 1, "gravel")
    if L >= 5:                                        # south chalet wing: dining room, suites lounge, library
        lv += wing(d, P, 38, 36, 58, 52, 2, 5, ["dining", "lounge", "library", "bar", "hall"], roof="gable", axis="x",
                   doors=[(48, 36, "north")], st=CA_SOUTH)
        for x, z in ((34, 56), (20, 56), (44, 58), (58, 58)):
            tree(d, x, z, 2, "spruce_log", "spruce_leaves", 7)
    rail_openings(d, "spruce_fence", tuple(sorted(set(lv))))
    return d


@design("skytower")
def skytower(pack, rel, L):
    core = {"Neoterra": skytower_nt, "Hearthwood": skytower_hw, "Cascadia": skytower_ca}[pack](rel, L)
    return {"Neoterra": grow_sky_nt, "Hearthwood": grow_sky_hw, "Cascadia": grow_sky_ca}[pack](core, L)


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
    for x in range(0, 52, 7):
        lamp_post(d, x, 0, 2, P, 4) if not 14 <= x <= 18 else None
    if L >= 2:                                        # materials store hall with roller doors and a dock
        lv += wing(d, P, 34, 4, 48, 16, 2, 1, ["store"], H=6, doors=[(41, 4, "north")], st=NT_DEPOT_STORE)
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
        lv += wing(d, P, 34, 21, 48, 31, 2, 3, ["office", "drawing", "lounge"], doors=[(41, 21, "north")],
                   st=NT_DEPOT_OFFICE)
        d.sign(41, 6, 20, "north", ["SITE", "MANAGEMENT"], "birch", glow=True, color="cyan")
        for x in (36, 46):
            tree(d, x, 19, 2, h=4)
    if L >= 4:                                        # precast production hall behind the yard
        for x in range(14, 19):
            d.set(x, 2, 26, AIR)
            d.set(x, 3, 26, AIR)
        lv += wing(d, P, 2, 29, 30, 44, 2, 2, ["workshop", "store"], H=6, roof="gable", axis="x", chimneys=False,
                   doors=[(16, 29, "north"), (2, 36, "west")], st=NT_DEPOT_HALL)
        for x in range(8, 26, 5):                      # gantry rail along the hall front
            for y in range(2, 9):
                d.set(x, y, 27, "yellow_concrete" if y % 3 == 2 else "iron_bars")
        for x in range(7, 27):
            d.set(x, 9, 27, "yellow_concrete")
        for y in range(5, 9):
            d.set(18, y, 27, chain()) if False else None
        d.sign(16, 8, 28, "north", ["PRECAST", "WORKS"], "birch", glow=True, color="yellow")
    if L >= 5:                                        # workers' canteen, lockers and gym; second crane
        lv += wing(d, P, 34, 35, 49, 53, 2, 5, ["dining", "kitchen", "gym", "lounge", "office"], doors=[(41, 35, "north")],
                   st=NT_DEPOT_CANTEEN)
        d.sign(41, 6, 34, "north", ["CANTEEN"], "birch", glow=True, color="magenta")
        for x, z in cells(2, 47, 30, 54):
            d.set(x, 1, z, "gray_concrete")
        for x in range(4, 30, 6):                      # plant yard: excavator stand-ins and skips
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
    rail_openings(d, "iron_bars", tuple(sorted(set(lv))))
    return d


def grow_twin_hw(d, L):
    P = "Hearthwood"
    regrid(d, 56, 54, 0, 0, 34)
    lv = [2, 7]
    path_line(d, [(x, 0) for x in range(0, 56)], 1, "gravel")
    for x in range(1, 56, 9):
        lamp_post(d, x, 0, 2, P, 3) if d.air(x, 2, 0) else None
    if L >= 2:                                        # timber seasoning barn behind the workshop
        lv += wing(d, P, 2, 21, 12, 35, 2, 2, ["store", "store"], roof="gable", axis="z", chimneys=False,
                   doors=[(7, 21, "north")], st=HW_YARD_BARN)
        for z in range(37, 41):                        # log pile outside
            for x in range(3, 11):
                d.set(x, 2, z, log("oak_log", "x"))
                if z < 40:
                    d.set(x, 3, z, log("oak_log", "x"))
    if L >= 3:                                        # clerk of works' office and drawing room
        lv += wing(d, P, 33, 2, 45, 12, 2, 3, ["drawing", "office", "library"], roof="gable", axis="x",
                   doors=[(39, 12, "south")], st=HW_YARD_OFFICE)
        flowerbed(d, 34, 14, 37, 15, 2, P)
        flowerbed(d, 41, 14, 44, 15, 2, P)
        d.sign(39, 5, 13, "south", ["Clerk of", "Works"], "dark_oak")
    if L >= 4:                                        # joinery shop with timber store above
        lv += wing(d, P, 33, 17, 53, 31, 2, 2, ["workshop", "store"], roof="gable", axis="x",
                   doors=[(43, 17, "north"), (33, 24, "west")], st=HW_YARD_JOINERY)
        d.sign(43, 5, 16, "north", ["Joinery"], "dark_oak")
        for x in range(35, 52, 2):                     # seasoned boards stacked on bearers by the shop
            pallet_stack(d, x, 33, 2, "oak_planks" if x % 4 == 1 else "spruce_planks", 5,
                         "oak_slab[type=bottom,waterlogged=false]")
        lamp_post(d, 33, 33, 2, P, 3)
        for x in range(36, 52, 3):                     # sawhorses with a plank across
            d.set(x, 2, 35, fence("oak"))
            d.set(x + 1, 2, 35, fence("oak"))
            d.set(x, 3, 35, slab("oak"))
            d.set(x + 1, 3, 35, slab("oak"))
        for x in range(31, 33):
            for z in range(14, 33):
                d.set(x, 1, z, "gravel")
    if L >= 5:                                        # masons' hall with the workers' mess upstairs
        lv += wing(d, P, 2, 39, 30, 51, 2, 3, ["workshop", "dining", "lounge"], roof="gable", axis="x",
                   doors=[(16, 39, "north"), (30, 45, "east")], st=HW_YARD_MASONS)
        for z in range(37, 41):                        # move the log pile out of the way of the hall
            for x in range(3, 11):
                for y in (2, 3):
                    if d.get(x, y, z).startswith("minecraft:oak_log"):
                        d.set(x, y, z, AIR)
        for x, z in cells(34, 34, 52, 50):
            if (x + z) % 7 == 0 and d.air(x, 2, z):
                pallet_stack(d, x, z, 2, ("stone_bricks", "bricks", "cobblestone")[x % 3], 2,
                             "oak_slab[type=bottom,waterlogged=false]")
        for x in (14, 18):
            for y in range(2, 9):
                d.set(x, y, 36, log("dark_oak_log", "y"))
        for x in range(13, 20):
            d.set(x, 9, 36, log("dark_oak_log", "x"))
        for y in range(5, 9):
            d.set(16, y, 36, chain())
        d.set(16, 4, 36, "stone_bricks")
    rail_openings(d, "dark_oak_fence", tuple(sorted(set(lv))))
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
        lv += wing(d, P, 34, 3, 50, 13, 2, 1, ["store"], roof="gable", axis="x", chimneys=False,
                   doors=[(42, 13, "south"), (42, 3, "north")], st=CA_YARD_SHED)
        for x in list(range(35, 40)) + list(range(45, 50)):    # stickered lumber outside
            for y in (2, 3):
                d.set(x, y, 15, log("stripped_spruce_log", "x"))
    if L >= 3:                                        # framers' bunkhouse and office
        lv += wing(d, P, 36, 18, 48, 29, 2, 2, ["office", "lounge"], roof="gable", axis="x",
                   doors=[(42, 18, "north")], st=CA_YARD_BUNK)
        for x in range(36, 49):                         # porch
            d.set(x, 6, 16, slab("spruce"))
            d.set(x, 6, 17, slab("spruce"))
        for x in (36, 48):
            for y in range(2, 6):
                d.set(x, y, 16, log("spruce_log", "y"))
        d.chair(38, 2, 17, "west", "spruce", sit=False)
        d.chair(46, 2, 17, "east", "spruce", sit=False)
    if L >= 4:                                        # sawmill hall with log deck and chute
        lv += wing(d, P, 2, 33, 24, 47, 2, 2, ["workshop", "store"], roof="gable", axis="x",
                   doors=[(13, 33, "north"), (24, 40, "east")], st=CA_YARD_MILL)
        for x in range(4, 22):
            for y in (2, 3):
                d.set(x, y, 50, log("spruce_log", "x"))
            d.set(x, 4, 50, log("spruce_log", "x")) if x % 2 else None
        d.sign(13, 6, 32, "north", ["SAWMILL"], "spruce")
    if L >= 5:                                        # cookhouse with dining hall and a log water tower
        lv += wing(d, P, 30, 34, 50, 48, 2, 3, ["dining", "kitchen", "lounge"], roof="gable", axis="x",
                   doors=[(40, 34, "north")], st=CA_YARD_COOK)
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
    rail_openings(d, "spruce_fence", tuple(sorted(set(lv))))
    return d


@design("twinbuilder")
def twinbuilder(pack, rel, L):
    core = {"Neoterra": twin_nt, "Hearthwood": twin_hw, "Cascadia": twin_ca}[pack](rel, L)
    return {"Neoterra": grow_twin_nt, "Hearthwood": grow_twin_hw, "Cascadia": grow_twin_ca}[pack](core, L)


@design("twinbuilderannex")
def twinbuilderannex(pack, rel, L):
    return {"Neoterra": annex_nt, "Hearthwood": annex_hw, "Cascadia": annex_ca}[pack](rel, L)
