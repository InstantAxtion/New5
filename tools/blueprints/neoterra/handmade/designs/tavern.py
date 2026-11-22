"""
Tavern – reference design for the hand-made set.

  Hearthwood  "The Crown & Hearth": English coaching inn. Brick ground floor, jettied timber-framed plaster upper
              floor with guest rooms, steep tiled gable, big brick chimney, hanging pub sign. Taproom with a bar
              and kegs along the back wall, inglenook fireplace, tables. L2 longer, L3 adds a rear brewhouse wing
              with a jukebox snug and a fenced beer garden.
  Cascadia    "Timberline Roadhouse": logging-town saloon. Log walls on a river-rock footing, gable turned to the
              street behind a tall false front, full-width covered porch with rocking chairs, stone chimney.
              Bunk loft upstairs. L2 adds a side lean-to, L3 a back deck with tables.
  Neoterra    "Skyline Lounge": modern bar. White concrete box with a full-height glass street front, bar island,
              booth seating, capsule rooms upstairs, flat roof. L3 adds a roof terrace bar with planters.

Requirements (all levels 8 beds, 3 barrels; seats 8 / 18 / 22; L3 jukebox).
"""
from hm import Design, design, AIR, D4

NAMES = {"Hearthwood": ["The Crown", "& Hearth"], "Cascadia": ["Timberline", "Roadhouse"],
         "Neoterra": ["SKYLINE", "LOUNGE"]}


def bar_back(d, x1, x2, z, y, facing):
    """Back bar against a wall: kegs below, a shelf of bottles (brewing stands / pots) above; the hut's three
    work barrels stand at the start."""
    for i, x in enumerate(range(x1, x2 + 1)):
        if i < 3:
            d.item(x, y, z, "barrel", "up")
        else:
            d.keg(x, y, z, "east" if i % 2 else "west")
        d.set(x, y + 1, z, f"{d.P['wood']}_slab[type=top,waterlogged=false]")
        if i % 2 == 0:
            d.set(x, y + 2, z, "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]")
        else:
            d.set(x, y + 2, z, "decorated_pot[cracked=false,facing=north,waterlogged=false]")


def bar(d, x1, x2, z, y, top, stools_side, wood=None):
    """Counter along x from x1 to x2 at row z, stools on `stools_side` (north/south). Returns seats."""
    n = 0
    for x in range(x1, x2 + 1):
        d.set(x, y, z, top)
        dz = D4[stools_side][1]
        d.chair(x, y, z + dz, stools_side, wood)
        n += 1
    return n


# ----------------------------------------------------------------------------------------------- Hearthwood
def hearthwood(rel, L):
    d = Design("Hearthwood", rel, (40, 42, 43), gy=1)
    P = d.P
    X2 = 15 if L == 1 else 19
    x1, z1, z2 = 3, 4, 12
    y0, y1 = 2, 6                     # ground storey air y2..5, first floor deck y6, upper y7..10
    beam = "stripped_dark_oak_log"
    # ground storey: brick with stone base course
    d.box(x1, y0, z1, X2, 5, z2, "bricks", floor="oak_planks")
    d.fill(x1, y0, z1, X2, y0, z1, "stone_bricks")
    for x in range(x1, X2 + 1):
        d.set(x, y0, z2, "stone_bricks")
    for z in range(z1, z2 + 1):
        d.set(x1, y0, z, "stone_bricks")
        d.set(X2, y0, z, "stone_bricks")
    # jetty: upper storey sticks out one block over the street side from L2
    uz1 = z1 - 1 if L >= 2 else z1
    d.fill(x1, y1, uz1, X2, y1, z2, "dark_oak_planks")
    d.box(x1, y1 + 1, uz1, X2, 10, z2, "calcite")
    for x in range(x1, X2 + 1, 2):                                  # close-studded timber framing
        for z in (uz1, z2):
            for y in range(y1 + 1, 11):
                d.set(x, y, z, f"{beam}[axis=y]")
    for z in range(uz1, z2 + 1, 2):
        for x in (x1, X2):
            for y in range(y1 + 1, 11):
                d.set(x, y, z, f"{beam}[axis=y]")
    for x in range(x1, X2 + 1):
        d.set(x, 10, uz1, f"{beam}[axis=x]")
        d.set(x, 10, z2, f"{beam}[axis=x]")
        if uz1 < z1 and x % 2:                                       # jetty brackets
            d.set(x, 5, uz1, "dark_oak_stairs[facing=south,half=top,shape=straight,waterlogged=false]")
    # ground-floor windows (leaded) and the door
    door_x = 9
    for x in range(x1 + 2, X2 - 1):
        if abs(x - door_x) <= 1 or (x - x1) % 4 == 0:
            continue
        d.window(x, 3, z1, x, 4, z1)
    for x in range(x1 + 2, X2 - 1, 3):
        d.window(x, 3, z2, x, 4, z2)
    d.double_door(door_x, y0, z1, "x", "south", "dark_oak")
    # upper windows between the studs
    for x in range(x1 + 1, X2, 2):
        if x % 4 == 0:
            for z in (uz1, z2):
                d.window(x, 8, z, x, 9, z)
    # roof: steep tiled gable along x, calcite gable ends with framing
    ridge = d.gable(x1, uz1, X2, z2, 11, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite", overhang=1)
    for yy in range(11, ridge):
        for x in (x1, X2):
            zc = (uz1 + z2) // 2
            if d.get(x, yy, zc) == "minecraft:calcite":
                d.set(x, yy, zc, f"{beam}[axis=y]")
    # ---- taproom ----
    # bar along the back wall with kegs behind it
    bx1, bx2 = 8, X2 - 2
    bar_back(d, bx1, bx2, z2 - 1, y0, "north")
    seats = bar(d, bx1, bx2 - 1, z2 - 3, y0, "dark_oak_planks", "north")
    d.set(bx2, y0, z2 - 3, "dark_oak_fence_gate[facing=east,in_wall=false,open=false,powered=false]")
    for x in range(bx1, bx2):
        if (x - bx1) % 3 == 1:
            d.set(x, 5, z2 - 3, "lantern[hanging=true,waterlogged=false]")
    # inglenook fireplace on the west wall, chimney through the roof
    d.hearth(x1 + 1, y0, 8, "east", ridge + 3, "bricks", "campfire")
    d.set(x1 + 1, y0 + 1, 8, "bricks")
    d.rug(x1 + 2, 7, x1 + 3, 9, y0, ("red_carpet",), "plain")
    d.chair(x1 + 3, y0, 6, "north", "dark_oak", True, arms=False)
    d.chair(x1 + 3, y0, 10, "south", "dark_oak", True, arms=False)
    seats += 2
    # staircase up along the east wall (rising south)
    sx = X2 - 1
    for i, y in enumerate(range(y0, y1)):
        d.set(sx, y, z1 + 1 + i, "dark_oak_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]")
        if y > y0:
            d.fill(sx, y0, z1 + 1 + i, sx, y - 1, z1 + 1 + i, "dark_oak_planks")
    for i in range(4):
        d.set(sx, y1, z1 + 1 + i, AIR)
    # tables in the remaining floor
    hx, hz = x1 + 2, z1 + 1                                          # hut by the entrance, same on every level
    d.hut(hx, y0, hz)
    need = {1: 8, 2: 18, 3: 22}[L]
    if L == 3:
        d.item(x1 + 1, y0, z1 + 1, "jukebox")
    sets = {1: [(10, 6, "we")], 2: [(9, 6, "nsew"), (12, 6, "nse")]}.get(L, [(9, 6, "nsew"), (12, 6, "nsew"),
                                                                           (15, 6, "nse")])
    if L == 1:                                                       # settle under the front window
        d.chair(7, y0, 5, "north", "dark_oak", True)
        d.chair(8, y0, 5, "north", "dark_oak", True)
        seats += 2
    for tx, tz, sides in sets:                                       # taproom tables
        d.dining(tx, y0, tz, 1, "x", "dark_oak", tuple(sides))
        seats += len(sides)
    for x in range(x1 + 3, X2 - 1, 4):
        d.lamp(x, 5, 6)
    # ---- guest rooms upstairs: 8 beds, rooms off a central corridor ----
    yb = y1 + 1
    bx = list(range(x1 + 2, x1 + 2 + 4 * 2, 2))
    bc = {1: "red", 2: "blue", 3: "green"}[L]
    for x in bx:
        d.bed(x, yb, uz1 + 1, "north", bc)
        d.bed(x, yb, z2 - 1, "south", bc)
    for x in bx:
        d.set(x + 1, yb, uz1 + 1, f"dark_oak_slab[type=top,waterlogged=false]")
        d.candle(x + 1, yb + 1, uz1 + 1, 2)
        d.set(x + 1, yb, z2 - 1, f"dark_oak_slab[type=top,waterlogged=false]")
        d.candle(x + 1, yb + 1, z2 - 1, 1)
    d.rug(x1 + 1, (uz1 + z2) // 2, x1 + 9, (uz1 + z2) // 2, yb, ("red_carpet",), "plain")   # runner, 9 cells
    d.keg(x1 + 1, yb, (uz1 + z2) // 2 - 1, "east")                    # luggage cask and a fern at the west end
    d.plant(x1 + 1, yb + 1, (uz1 + z2) // 2 - 1, "potted_fern")
    if L == 1:                                                       # wash stand and trunk by the stairs
        d.set(X2 - 2, yb, z2 - 1, "water_cauldron[level=3]")
        d.keg(X2 - 1, yb, z2 - 1, "west")
    else:                                                            # east end: landlord's parlour / card corner
        d.rug(X2 - 5, z2 - 4, X2 - 3, z2 - 2, yb, ({2: "brown_carpet"}.get(L, "green_carpet"),), "plain")
        d.table(X2 - 4, yb, z2 - 3, "dark_oak")
        d.chair(X2 - 5, yb, z2 - 3, "west", "dark_oak", True, arms=False)
        d.chair(X2 - 3, yb, z2 - 3, "east", "dark_oak", True, arms=False)
        d.chair(X2 - 4, yb, z2 - 2, "south", "dark_oak", True, arms=False)
        if L == 3:
            d.chair(X2 - 4, yb, z2 - 4, "north", "dark_oak", True, arms=False)
            d.set(X2 - 6, yb, z2 - 1, "lectern[facing=north,has_book=true,powered=false]")
        else:
            d.set(X2 - 6, yb, z2 - 1, "water_cauldron[level=3]")
            d.plant(X2 - 6, yb, uz1 + 1, "potted_red_tulip")
    for x in range(x1 + 2, X2 - 2, 4):
        d.lamp(x, 10, (uz1 + z2) // 2)
    # railing round the stair well
    for z in range(z1 + 1, z1 + 4):
        d.set(sx - 1, y1 + 1, z, "dark_oak_fence")
    if L >= 2:                                                       # wardrobe and bookcase at the far end
        d.set(X2 - 2, yb, z2 - 1, "chiseled_bookshelf[facing=west,slot_0_occupied=true,slot_1_occupied=false,"
                                  "slot_2_occupied=true,slot_3_occupied=false,slot_4_occupied=true,slot_5_occupied=false]")
    # ---- street front ----
    d.sign(door_x - 2, 5, z1 - 1 if L == 1 else z1 - 2, "east", NAMES["Hearthwood"], "dark_oak", hanging=True)
    if L >= 2:
        d.set(door_x - 2, 5, z1 - 1, "dark_oak_fence")
        d.set(door_x - 2, 5, z1 - 1, "dark_oak_planks")
    for x in range(x1 + 1, X2):                                      # flower boxes under the upper windows
        if x % 4 == 0:
            d.set(x, 7, uz1 - 1, "dark_oak_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
    d.chair(door_x + 3, y0, z1 - 2, "south", "dark_oak", sit=False)
    d.chair(door_x + 4, y0, z1 - 2, "south", "dark_oak", sit=False)
    d.keg(door_x - 1, y0, z1 - 1, "west")
    d.keg(door_x - 1, y0 + 1, z1 - 1, "north")
    d.set(door_x + 2, y0 + 2, z1 - 1, "wall_torch[facing=north]")
    # ---- L3: brewhouse wing behind and a beer garden ----
    if L == 3:
        wx1, wx2, wz1, wz2 = 12, 19, z2, 19
        d.box(wx1, y0, wz1, wx2, 5, wz2, "bricks", floor="oak_planks")
        for x in range(wx1 + 2, wx2 - 1):
            d.set(x, 3, wz2, "glass_pane")
        for z in range(wz1 + 2, wz2 - 1, 2):
            d.set(wx2, 3, z, "glass_pane")
        d.gable(wx1, wz1 + 1, wx2, wz2, 6, "z", "deepslate_tile_stairs", "deepslate_tile_slab", "bricks")
        d.door(X2 - 1, y0, z2, "south", "dark_oak")                 # door from behind the bar
        for x in range(wx1 + 1, wx2):                                # brewing vats
            d.set(x, y0, wz2 - 1, "water_cauldron[level=3]" if x % 2 else "barrel[facing=up,open=false]")
        d.set(wx1 + 1, y0, wz1 + 2, "furnace[facing=east,lit=false]")
        d.set(wx1 + 1, y0, wz1 + 3, "smoker[facing=east,lit=false]")
        d.lamp(wx1 + 3, 5, wz1 + 3)
        d.set(wx1 + 3, y0, wz1 + 3, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        d.set(wx1 + 3, y0 + 1, wz1 + 3, "water_cauldron[level=3]")     # brew kettle over the fire
        d.set(wx1 + 4, y0, wz1 + 1, "hay_block[axis=y]")                # malt sacks by the door
        d.set(wx1 + 5, y0, wz1 + 1, "hay_block[axis=x]")
        d.set(wx1 + 4, y0 + 1, wz1 + 1, "hay_block[axis=x]")
        d.keg(wx2 - 1, y0, wz1 + 4, "west")                             # finished casks
        d.keg(wx2 - 1, y0, wz1 + 5, "west")
        d.keg(wx2 - 1, y0 + 1, wz1 + 4, "west")
        d.set(wx1 + 1, y0, wz1 + 4, "crafting_table")
        # beer garden
        gx1, gx2, gz1, gz2 = 3, 10, 14, 21
        d.fill(gx1, 1, gz1, gx2, 1, gz2, "grass_block[snowy=false]")
        for x in range(gx1, gx2 + 1):
            for z in range(gz1, gz2 + 1):
                if x in (gx1, gx2) or z in (gz1, gz2):
                    d.set(x, y0, z, "dark_oak_fence")
        d.set(6, y0, gz1, "dark_oak_fence_gate[facing=north,in_wall=false,open=false,powered=false]")
        d.set(7, y0, gz1, "dark_oak_fence_gate[facing=north,in_wall=false,open=false,powered=false]")
        d.fill(6, 1, z2 + 1, 7, 1, gz1, "gravel")
        for tx, tz in ((5, 17), (8, 19)):                           # beer garden tables
            d.dining(tx, y0, tz, 1, "x", "oak", ("n", "s", "e", "w"))
            seats += 4
        for x, z in ((gx1, gz1), (gx2, gz1), (gx1, gz2), (gx2, gz2)):
            d.set(x, y0 + 1, z, "lantern[hanging=false,waterlogged=false]")
        d.set(gx1 + 1, y0, gz2 - 1, "flowering_azalea")
        d.set(gx2 - 1, y0, gz2 - 1, "flowering_azalea")
    return d


# ----------------------------------------------------------------------------------------------- Cascadia
def cascadia(rel, L):
    W = {1: 11, 2: 13, 3: 13}[L]
    d = Design("Cascadia", rel, (48, 42, 38), gy=1, paving="coarse_dirt")
    x1, z1 = 4, 7
    x2, z2 = x1 + W - 1, z1 + 14
    y0 = 2
    log = "spruce_log"
    # river-rock footing, log walls (horizontal logs, corner posts), board floor
    d.box(x1, y0, z1, x2, 6, z2, f"{log}[axis=z]", floor="spruce_planks")
    for x in range(x1, x2 + 1):
        for y in range(y0, 7):
            d.set(x, y, z1, f"{log}[axis=x]")
            d.set(x, y, z2, f"{log}[axis=x]")
    for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        for y in range(y0, 7):
            d.set(x, y, z, "stripped_spruce_log[axis=y]")
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if x in (x1, x2) or z in (z1, z2):
                d.set(x, 1, z, "mossy_cobblestone" if (x + z) % 3 == 0 else "cobblestone")
    # loft floor and walls up to the eaves
    d.fill(x1 + 1, 7, z1 + 1, x2 - 1, 7, z2 - 1, "spruce_planks")
    # steep gable, ridge running back from the street (gable to the street)
    ridge = d.gable(x1, z1, x2, z2, 7, "z", "spruce_stairs", "spruce_slab", "spruce_planks", overhang=1)
    # false front: tall flat board facade on the street gable with the saloon name
    for x in range(x1 - 1, x2 + 2):
        for y in range(y0, ridge + 2):
            if y >= 7 or x in (x1 - 1, x2 + 1):
                d.set(x, y, z1 - 1, "stripped_spruce_log[axis=y]" if x in (x1 - 1, x2 + 1) else "spruce_planks")
        d.set(x, ridge + 2, z1 - 1, "spruce_slab[type=bottom,waterlogged=false]")
    mid = (x1 + x2) // 2
    d.sign(mid, ridge - 1, z1 - 2, "north", NAMES["Cascadia"], "spruce")
    d.sign(mid - 1, ridge - 1, z1 - 2, "north", ["~~~~", "EST. 1889"], "spruce")
    d.sign(mid + 1, ridge - 1, z1 - 2, "north", ["~~~~", "ROOMS"], "spruce")
    # porch: full width, posts, shed roof, rocking chairs
    pz = z1 - 4
    d.fill(x1 - 1, 1, pz, x2 + 1, 1, z1 - 2, "spruce_planks")
    for x in range(x1 - 1, x2 + 2):
        for z in range(pz, z1 - 1):
            d.set(x, y0 - 1, z, "spruce_planks")
    for x in (x1 - 1, mid - 3, mid + 3, x2 + 1):
        for y in range(y0, 6):
            d.set(x, y, pz, f"{log}[axis=y]")
    for x in range(x1 - 2, x2 + 3):
        d.set(x, 6, pz - 1, "spruce_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]")
        for z in range(pz, z1 - 1):
            d.set(x, 6, z, "spruce_slab[type=bottom,waterlogged=false]")
    for x in range(x1, x2 + 1):
        if abs(x - mid) > 1 and x not in (mid - 3, mid + 3):
            d.set(x, y0, pz, "spruce_fence")
    d.chair(x1 + 1, y0, z1 - 2, "south", "spruce", sit=False)
    d.chair(x2 - 1, y0, z1 - 2, "south", "spruce", sit=False)
    d.keg(x1, y0, z1 - 3, "north")
    d.set(mid - 2, 5, z1 - 2, "lantern[hanging=true,waterlogged=false]")
    d.set(mid + 2, 5, z1 - 2, "lantern[hanging=true,waterlogged=false]")
    # swinging doors + windows
    d.double_door(mid, y0, z1, "x", "south", "spruce") if W % 2 == 0 else d.door(mid, y0, z1, "south", "spruce")
    for x in (x1 + 2, x2 - 2):
        d.window(x, 3, z1, x, 4, z1)
    for z in range(z1 + 3, z2 - 1, 4):
        d.window(x1, 3, z, x1, 4, z)
        d.window(x2, 3, z, x2, 4, z)
    # ---- saloon floor ----
    # long bar along the east wall, back bar against the wall
    bz1, bz2 = z1 + 3, z2 - 4
    for z in range(bz1, bz2 + 1):
        d.set(x2 - 1, y0, z, "barrel[facing=up,open=false]" if z - bz1 < 3 else f"barrel[facing=west,open=false]")
        if z - bz1 < 3:
            d.placed["items"]["minecraft:barrel"] = d.placed["items"].get("minecraft:barrel", 0) + 1
        d.set(x2 - 1, y0 + 1, z, "spruce_slab[type=top,waterlogged=false]")
        d.set(x2 - 1, y0 + 2, z, "potted_dead_bush" if z % 2 else "decorated_pot[cracked=false,facing=west,waterlogged=false]")
        d.set(x2 - 3, y0, z, "stripped_spruce_wood[axis=y]")
        d.chair(x2 - 4, y0, z, "west", "spruce")
    seats = bz2 - bz1 + 1
    d.set(x2 - 3, y0, bz2 + 1, "spruce_fence_gate[facing=south,in_wall=false,open=false,powered=false]")
    d.hut(x1 + 1, y0, z1 + 1)
    # stone chimney + fireplace on the west wall at the back
    fz = z2 - 3
    d.hearth(x1 + 1, y0, fz, "east", ridge + 2, "cobblestone", "campfire")
    for y in range(y0, ridge + 2):
        d.set(x1, y, fz, "mossy_cobblestone" if y % 3 == 0 else "cobblestone")
    d.rug(x1 + 2, fz - 1, x1 + 3, fz + 1, y0, ("brown_carpet",), "plain")
    # ladder to the bunk loft (north-west corner)
    for y in range(y0, 8):
        d.set(mid, y, z2 - 1, "ladder[facing=north,waterlogged=false]")
    need = {1: 8, 2: 18, 3: 22}[L]
    sets = {1: [(7, 11, "nsew"), (7, 14, "ew")], 2: [(6, 11, "nsew"), (9, 11, "nsew"), (6, 14, "ns")]}.get(
        L, [(6, 11, "nsew"), (9, 11, "nsew"), (6, 14, "nsew"), (9, 14, "ns")])
    for tx, tz, sides in sets:                                       # saloon tables
        d.dining(tx, y0, tz, 1, "x", "spruce", tuple(sides))
        seats += len(sides)
    if L == 3:
        d.item(x1 + 1, y0, z1 + 3, "jukebox")
    for z in range(z1 + 3, z2 - 1, 4):
        d.lamp(mid, 6, z)
    # loft: 8 bunks under the roof slope
    yl = 8
    bc = {1: "brown", 2: "green", 3: "red"}[L]
    for i, z in enumerate(range(z1 + 2, z1 + 2 + 2 * 4, 2)):
        d.bed(x1 + 2, yl, z, "west", bc)
        d.bed(x2 - 2, yl, z, "east", bc)
    # back of the loft: footlockers, a rug by the ladder hatch, lanterns on chains from the ridge
    d.keg(x1 + 3, yl, z1 + 10, "east")
    d.keg(x1 + 3, yl, z1 + 11, "east")
    d.plant(x1 + 3, yl + 1, z1 + 10, "potted_fern")
    d.rug(mid - 1, z1 + 9, mid + 1, z1 + 11, yl, ({1: "green_carpet", 2: "brown_carpet"}.get(L, "red_carpet"),), "plain")
    for z in (z1 + 3, z1 + 10):
        for y in range(yl + 3, ridge):
            d.set(mid, y, z, "chain[axis=y,waterlogged=false]")
        d.set(mid, yl + 2, z, "lantern[hanging=true,waterlogged=false]")
    if L >= 2:                                                       # a table for cards in the gable end
        d.table(x2 - 4, yl, z1 + 10, "spruce")
        d.chair(x2 - 4, yl, z1 + 9, "north", "spruce", True)
        d.chair(x2 - 4, yl, z1 + 11, "south", "spruce", True)
    if L == 3:
        d.set(x2 - 4, yl, z1 + 12, "water_cauldron[level=3]")         # wash stand
        d.keg(x2 - 2, yl, z1 + 10, "west")
        d.keg(x2 - 2, yl, z1 + 11, "west")
    # ---- L2: side lean-to (store room); L3: back deck with tables ----
    if L >= 2:
        lx1, lx2 = x2, x2 + 5
        d.box(lx1, y0, z1 + 4, lx2, 5, z1 + 13, "spruce_planks", floor="spruce_planks")
        for z in range(z1 + 4, z1 + 14):
            d.set(lx2, 1, z, "cobblestone")
            d.set(lx2, 6, z, "spruce_slab[type=bottom,waterlogged=false]")
            for x in range(lx1 + 1, lx2):
                d.set(x, 6, z, "spruce_slab[type=bottom,waterlogged=false]")
        for z in range(z1 + 5, z1 + 13, 2):
            d.set(lx2, 3, z, "glass_pane")
        d.door(x2, y0, z1 + 12, "east", "spruce")                    # door from the saloon, past the back bar
        d.set(lx2, 3, z1 + 8, "target[power=0]")                       # dartboard on the end wall
        # back room: card tables
        d.dining(lx1 + 2, y0, z1 + 7, 1, "x", "dark_oak", ("n", "s", "e", "w"))   # card table
        seats += 4
        d.lamp(lx1 + 2, 5, z1 + 7)
        d.lamp(lx1 + 2, 5, z1 + 11)
        if L == 2:
            d.keg(lx2 - 1, y0, z1 + 12, "north")
            d.keg(lx2 - 1, y0, z1 + 11, "north")
            d.keg(lx2 - 1, y0 + 1, z1 + 12, "north")
        else:                                                        # a settle along the back wall
            d.chair(lx2 - 2, y0, z1 + 12, "south", "spruce", True)
            d.chair(lx2 - 1, y0, z1 + 12, "south", "spruce", True)
            seats += 2
            d.keg(lx2 - 1, y0, z1 + 5, "west")
    if L == 3:
        dz1 = z2 + 1
        d.fill(x1 - 1, 1, dz1, x2 + 1, 1, dz1 + 6, "spruce_planks")
        for x in range(x1 - 1, x2 + 2):
            for z in range(dz1, dz1 + 7):
                if x in (x1 - 1, x2 + 1) or z == dz1 + 6:
                    d.set(x, y0, z, "spruce_fence")
        d.door(mid + 2, y0, z2, "north", "spruce")
        for tx in (x1 + 3, x1 + 8):                                 # deck tables
            d.dining(tx, y0, dz1 + 2, 1, "x", "spruce", ("n", "s", "e", "w"))
            seats += 4
        for x, z in ((x1 - 1, dz1 + 6), (x2 + 1, dz1 + 6)):
            d.set(x, y0 + 1, z, "lantern[hanging=false,waterlogged=false]")
    return d


# ----------------------------------------------------------------------------------------------- Neoterra
def neoterra(rel, L):
    d = Design("Neoterra", rel, (40, 42, 36), gy=1, paving="smooth_stone")
    W = {1: 13, 2: 17, 3: 17}[L]
    x1, z1 = 3, 4
    x2, z2 = x1 + W - 1, z1 + 11
    y0 = 2
    # two storeys, 4-high each, concrete box with a cantilevered upper floor and full-height glass front
    d.box(x1, y0, z1, x2, 6, z2, "white_concrete", floor="polished_diorite")
    d.fill(x1, 7, z1 - 1, x2, 7, z2, "light_gray_concrete")
    d.box(x1, 8, z1 - 1, x2, 11, z2, "white_concrete")
    d.flat(x1, z1 - 1, x2, z2, 12, "smooth_quartz", "white_concrete", "smooth_quartz_slab")
    for x in range(x1 + 1, x2):                                     # glass street front
        d.window(x, y0, z1, x, 6, z1, "glass_pane")
        d.window(x, 9, z1 - 1, x, 10, z1 - 1, "light_gray_stained_glass_pane")
    for x in (x1, x2):
        for y in range(y0, 12):
            d.set(x, y, z1 if y < 7 else z1 - 1, "light_gray_concrete")
    for z in range(z1 + 2, z2 - 1, 3):
        d.window(x1, 3, z, x1, 5, z)
        d.window(x2, 9, z, x2, 10, z)
    d.fill(x1, 7, z1 - 1, x2, 7, z1 - 1, "cyan_terracotta")         # cyan band
    mid = (x1 + x2) // 2
    d.double_door(mid, y0, z1, "x", "south", "birch")
    d.sign(mid - 1, 7, z1 - 2, "north", NAMES["Neoterra"], "birch", glow=True, color="cyan")
    # entrance canopy
    for x in range(mid - 2, mid + 4):
        for z in (z1 - 1, z1 - 2):
            d.set(x, 6, z, "smooth_quartz_slab[type=top,waterlogged=false]")
    # ---- lounge ----
    # bar island in the middle-back with a mirrored back bar
    bx1, bx2 = x1 + 3, x2 - 3
    for x in range(bx1, bx2 + 1):
        d.set(x, y0, z2 - 1, "barrel[facing=up,open=false]" if x - bx1 < 3 else "smooth_quartz")
        if x - bx1 < 3:
            d.placed["items"]["minecraft:barrel"] = d.placed["items"].get("minecraft:barrel", 0) + 1
        d.set(x, y0 + 1, z2 - 1, "light_blue_stained_glass")
        d.set(x, y0 + 2, z2 - 1, "sea_lantern" if x % 3 == 0 else "light_blue_stained_glass")
    seats = 0
    for x in range(bx1, bx2):
        d.set(x, y0, z2 - 3, "quartz_block")
        d.chair(x, y0, z2 - 4, "north", "birch")
        seats += 1
    d.set(bx2, y0, z2 - 3, "birch_fence_gate[facing=east,in_wall=false,open=false,powered=false]")
    # booths along the west wall: bench backs to the wall, table between
    for z in range(z1 + 2, z2 - 5, 3):
        d.chair(x1 + 1, y0, z, "west", "birch")
        d.table(x1 + 2, y0, z, "birch", "slab", "smooth_quartz_slab")
        d.chair(x1 + 3, y0, z, "east", "birch")
        seats += 2
    d.hut(x2 - 1, y0, z1 + 1)
    need = {1: 8, 2: 18, 3: 22}[L]
    if L == 3:
        d.item(x2 - 1, y0, z1 + 2, "jukebox")
    for tx, tz in {1: [(10, 7)], 2: [(9, 6)]}.get(L, [(9, 6), (13, 6)]):     # lounge tables on rugs
        d.rug(tx - 1, tz - 1, tx + 1, tz + 1, y0, ({1: "cyan_carpet", 2: "light_blue_carpet"}.get(L, "cyan_carpet"),),
              "plain")
        d.dining(tx, y0, tz, 1, "x", "birch", ("n", "s", "e", "w"))
        seats += 4
    for x in range(x1 + 2, x2 - 1, 3):
        d.set(x, 6, z1 + 6, "sea_lantern")
    d.plant(x1 + 1, y0, z2 - 1, "potted_bamboo")
    d.plant(x1 + 1, y0, z1 + 1, "potted_bamboo")                      # plants either side of the entrance
    if L >= 2:
        d.plant(mid + 3, y0, z1 + 1, "potted_azalea_bush")
    # drinks on the bar top
    d.set(bx1 + 1, y0 + 1, z2 - 3, "brewing_stand[has_bottle_0=true,has_bottle_1=true,has_bottle_2=false]")
    d.candle(bx1 + 3, y0 + 1, z2 - 3, 3, "white")
    d.set(bx2 - 2, y0 + 1, z2 - 3, "brewing_stand[has_bottle_0=false,has_bottle_1=true,has_bottle_2=true]")
    # stair core in the south-east corner (straight flight along x)
    for i in range(6):
        x = x2 - 6 + i
        d.set(x, y0 + i, z2 - 2, "smooth_quartz_stairs[facing=east,half=bottom,shape=straight,waterlogged=false]")
    for x in range(x2 - 4, x2 - 1):
        d.set(x, 7, z2 - 2, AIR)
    # upper floor: capsule rooms (8 beds), heads against the walls, glass partition to the stair landing
    yb = 8
    bed_c = {1: "cyan", 2: "light_gray", 3: "blue"}[L]
    for x in range(x1 + 1, x1 + 9, 2):
        d.bed(x, yb, z1, "north", bed_c)                              # north capsules (cantilevered front)
        d.set(x + 1, yb, z1, "white_concrete")
        d.set(x + 1, yb + 1, z1, "white_concrete")
        d.bed(x, yb, z2 - 4, "south", bed_c)                          # south capsules with a bedside shelf
        d.set(x + 1, yb, z2 - 4, "birch_slab[type=top,waterlogged=false]")
        d.candle(x + 1, yb + 1, z2 - 4, 1, "light_gray")
    for x in range(x1 + 1, x1 + 10):
        d.set(x, yb, z2 - 3, "light_gray_concrete")
        d.set(x, yb + 1, z2 - 3, "light_gray_stained_glass_pane")
    d.set(x1 + 9, yb, z2 - 3, "birch_door[facing=south,half=lower,hinge=left,open=false,powered=false]")
    d.set(x1 + 9, yb + 1, z2 - 3, "birch_door[facing=south,half=upper,hinge=left,open=false,powered=false]")
    for x in range(x1 + 2, x2 - 1, 4):
        d.set(x, 11, z1 + 5, "sea_lantern")
    d.rug(x1 + 2, z1 + 3, x1 + 7, z1 + 4, yb, ({1: "cyan_carpet", 2: "gray_carpet"}.get(L, "light_blue_carpet"),),
          "plain")                                                     # runner, 12 cells
    d.plant(x1 + 1, yb, z1 + 3, "potted_bamboo")
    # landing strip behind the glass: wash basins and lockers, lit
    d.set(x1 + 1, yb, z2 - 1, "water_cauldron[level=3]")
    d.set(x1 + 2, yb, z2 - 1, "water_cauldron[level=3]")
    d.set(x1 + 1, yb + 2, z2 - 1, "light_gray_stained_glass")          # mirror strip over the basins
    d.set(x1 + 2, yb + 2, z2 - 1, "light_gray_stained_glass")
    d.keg(x1 + 4, yb, z2 - 1, "north")
    d.keg(x1 + 5, yb, z2 - 1, "north")
    d.set(x1 + 3, 11, z2 - 2, "sea_lantern")
    if L >= 2:
        # guest lounge at the east end of the upper floor
        d.chair(x1 + 11, yb, z1, "north", "birch")
        d.chair(x1 + 12, yb, z1, "north", "birch")
        d.chair(x1 + 13, yb, z1, "north", "birch")
        d.table(x1 + 12, yb, z1 + 2, "birch", "slab", "smooth_quartz_slab")
        d.chair(x1 + 12, yb, z1 + 4, "south", "birch")
        d.rug(x1 + 11, z1 + 1, x1 + 13, z1 + 3, yb, ({2: "orange_carpet"}.get(L, "cyan_carpet"),), "plain")
        d.plant(x1 + 10, yb, z1, "potted_azalea_bush")
        d.plant(x1 + 14, yb, z1, "potted_bamboo")
        if L == 2:
            for z in range(z1 + 5, z1 + 8):
                d.set(x2 - 1, yb, z, "bookshelf")
            d.set(x2 - 1, yb + 1, z1 + 6, "potted_fern")
        else:
            for z in (z1 + 5, z1 + 6):
                d.set(x2 - 1, yb, z, "bookshelf")
            d.keg(x2 - 1, yb, z1 + 7, "west")                       # bar cart
            d.set(x2 - 1, yb + 1, z1 + 7, "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]")
    if L == 3:                                                      # roof terrace bar
        for x in range(x1 + 1, x2):
            for z in range(z1, z2):
                d.set(x, 13, z, AIR)
        for x in range(x1 + 1, x2, 4):
            d.set(x, 13, z2 - 1, "azalea")
        for y in range(8, 13):
            d.set(x2 - 1, y, z1 + 2, "ladder[facing=west,waterlogged=false]")
        d.set(x2 - 1, 12, z1 + 2, "ladder[facing=west,waterlogged=false]")
        for tx in (x1 + 4, x1 + 9):                                 # roof terrace tables
            d.dining(tx, 13, z1 + 5, 1, "x", "birch", ("n", "s", "e", "w"))
            seats += 4
    return d


# ----------------------------------------------------------------------------------------------- site dressing
# Runs after the add-on buildings (designs/shops.py growth) are drawn: hand-placed dressing for the covered strips
# behind them, the ballroom dance floor, and trees moved in from the plot edge so the yard stays inside the
# buildings' footprint. Coordinates are fixed per pack and level.
def site(d, L):
    from designs.shops import tree, spruce_tree
    S = "south"
    if d.pack == "Hearthwood":
        if L >= 2:                                   # yard behind the coach house, under its eaves
            d.set(25, 2, 12, "water_cauldron[level=3]")                 # rain butt
            d.set(26, 2, 12, "barrel[facing=up,open=false]")
            for x in (29, 30, 31):                                       # log pile
                d.set(x, 2, 12, "oak_log[axis=x]")
            d.set(30, 3, 12, "oak_log[axis=x]")
            d.chair(34, 2, 12, "north", "dark_oak", sit=False)          # bench against the back wall
            d.chair(35, 2, 12, "north", "dark_oak", sit=False)
            d.wall_torch(27, 4, 12, S)
            d.wall_torch(33, 4, 12, S)
        if L == 3:                                   # stable yard behind the stables
            d.set(3, 2, 36, "hay_block[axis=y]")
            d.set(4, 2, 36, "hay_block[axis=x]")
            d.set(3, 3, 36, "hay_block[axis=x]")
            d.set(7, 2, 36, "water_cauldron[level=3]")                  # horse trough
            d.set(8, 2, 36, "water_cauldron[level=3]")
            d.set(11, 2, 36, "composter[level=7]")                      # muck heap
            d.set(15, 2, 36, "barrel[facing=up,open=false]")
            d.set(16, 2, 36, "barrel[facing=up,open=false]")
            d.wall_torch(5, 4, 36, S)
            d.wall_torch(14, 4, 36, S)
            d.clear(21, 2, 37, 34, d.sy - 1, 42)                        # lone lamp, bench and tree at the plot edge
            d.clear(34, 2, 28, 38, d.sy - 1, 32)                        # yard tree one step in from the edge
            tree(d, 35, 30)
    elif d.pack == "Cascadia":
        if L >= 2:                                   # wood yard behind the bunk house
            for x in (26, 27, 28):
                d.set(x, 2, 12, "spruce_log[axis=x]")
            d.set(27, 3, 12, "spruce_log[axis=x]")
            d.set(30, 2, 12, "stripped_spruce_log[axis=y]")             # chopping block
            d.set(32, 2, 12, "water_cauldron[level=3]")                 # wash basin
            d.set(33, 2, 12, "barrel[facing=up,open=false]")
            d.chair(35, 2, 12, "north", "spruce", sit=False)
            d.chair(36, 2, 12, "north", "spruce", sit=False)
            d.wall_torch(29, 4, 12, S)
            d.wall_torch(35, 4, 12, S)
        if L == 3:                                   # livery yard behind the livery barn
            d.set(26, 2, 26, "hay_block[axis=y]")
            d.set(27, 2, 26, "hay_block[axis=x]")
            d.set(26, 3, 26, "hay_block[axis=x]")
            d.set(30, 2, 26, "water_cauldron[level=3]")
            d.set(31, 2, 26, "water_cauldron[level=3]")
            d.set(34, 2, 26, "composter[level=7]")
            d.set(38, 2, 26, "barrel[facing=up,open=false]")
            d.set(39, 2, 26, "barrel[facing=up,open=false]")
            d.wall_torch(29, 4, 26, S)
            d.wall_torch(41, 4, 26, S)
            d.clear(43, 2, 6, 47, d.sy - 1, 10)                         # tree at the plot edge moves in
            spruce_tree(d, 41, 8)
    else:
        if L == 3:
            for x in range(6, 19):                   # ballroom: checkered dance floor instead of a 52-cell rug
                for z in range(22, 26):
                    if "carpet" in d.get(x, 2, z):
                        d.set(x, 2, z, AIR)
                    d.set(x, 1, z, "light_gray_concrete" if (x + z) % 2 else "white_concrete")
            d.clear(24, 2, 30, 28, d.sy - 1, 34)                        # tree at the plot edge moves in
            tree(d, 27, 27, "birch")


@design("tavern")
def tavern(pack, rel, L):
    from designs.shops import grow
    d = {"Hearthwood": hearthwood, "Cascadia": cascadia, "Neoterra": neoterra}[pack](rel, L)
    grow(d, L, "tavern")
    site(d, L)
    return d
