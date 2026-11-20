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
    d = Design("Hearthwood", rel, (44, 42, 40), gy=1)
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
    seats += d.seating(x1 + 5, z1 + 1, X2 - 3, z2 - 4, y0, max(0, need - seats), "dark_oak", "post",
                       rug=None, step=3 if L > 1 else 4)
    for x in range(x1 + 3, X2 - 1, 4):
        d.lamp(x, 5, 6)
    # ---- guest rooms upstairs: 8 beds, rooms off a central corridor ----
    yb = y1 + 1
    bx = list(range(x1 + 2, x1 + 2 + 4 * 2, 2))
    for x in bx:
        d.bed(x, yb, uz1 + 1, "north")
        d.bed(x, yb, z2 - 1, "south")
    for x in bx:
        d.set(x + 1, yb, uz1 + 1, f"dark_oak_slab[type=top,waterlogged=false]")
        d.candle(x + 1, yb + 1, uz1 + 1, 2)
        d.set(x + 1, yb, z2 - 1, f"dark_oak_slab[type=top,waterlogged=false]")
        d.candle(x + 1, yb + 1, z2 - 1, 1)
    d.rug(x1 + 1, (uz1 + z2) // 2 - 1 + 1, X2 - 3, (uz1 + z2) // 2 + 1 - 1, yb, ("red_carpet", "red_carpet"), "plain")
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
        seats += d.seating(gx1 + 1, gz1 + 1, gx2 - 1, gz2 - 1, y0, max(0, need - seats), "oak", "post")
        for x, z in ((gx1, gz1), (gx2, gz1), (gx1, gz2), (gx2, gz2)):
            d.set(x, y0 + 1, z, "lantern[hanging=false,waterlogged=false]")
        d.set(gx1 + 1, y0, gz2 - 1, "flowering_azalea")
        d.set(gx2 - 1, y0, gz2 - 1, "flowering_azalea")
    return d


# ----------------------------------------------------------------------------------------------- Cascadia
def cascadia(rel, L):
    W = {1: 11, 2: 13, 3: 13}[L]
    d = Design("Cascadia", rel, (46, 42, 42), gy=1, paving="coarse_dirt")
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
    seats += d.seating(x1 + 1, z1 + 3, x2 - 5, z2 - 2, y0, max(0, need - seats), "spruce", "post", step=3)
    if L == 3:
        d.item(x1 + 1, y0, z1 + 3, "jukebox")
    for z in range(z1 + 3, z2 - 1, 4):
        d.lamp(mid, 6, z)
    # loft: 8 bunks under the roof slope
    yl = 8
    for i, z in enumerate(range(z1 + 2, z1 + 2 + 2 * 4, 2)):
        d.bed(x1 + 2, yl, z, "west")
        d.bed(x2 - 2, yl, z, "east")
    # ---- L2: side lean-to (store room); L3: back deck with tables ----
    if L >= 2:
        lx1, lx2 = x2, x2 + 5
        d.box(lx1, y0, z1 + 4, lx2, 5, z1 + 11, "spruce_planks", floor="spruce_planks")
        for z in range(z1 + 4, z1 + 12):
            d.set(lx2, 1, z, "cobblestone")
            d.set(lx2, 6, z, "spruce_slab[type=bottom,waterlogged=false]")
            for x in range(lx1 + 1, lx2):
                d.set(x, 6, z, "spruce_slab[type=bottom,waterlogged=false]")
        for z in range(z1 + 5, z1 + 11, 2):
            d.set(lx2, 3, z, "glass_pane")
        for z in range(z1 + 6, z1 + 9):
            d.set(x2, y0, z, AIR)
            d.set(x2, y0 + 1, z, AIR)
        # back room: card tables
        seats += d.seating(lx1 + 1, z1 + 5, lx2 - 1, z1 + 10, y0, max(0, need - seats), "dark_oak", "post", step=3)
        d.lamp(lx1 + 2, 5, z1 + 7)
    if L == 3:
        dz1 = z2 + 1
        d.fill(x1 - 1, 1, dz1, x2 + 1, 1, dz1 + 6, "spruce_planks")
        for x in range(x1 - 1, x2 + 2):
            for z in range(dz1, dz1 + 7):
                if x in (x1 - 1, x2 + 1) or z == dz1 + 6:
                    d.set(x, y0, z, "spruce_fence")
        d.door(mid + 2, y0, z2, "north", "spruce")
        seats += d.seating(x1, dz1, x2, dz1 + 5, y0, max(0, need - seats), "spruce", "post", step=3)
        for x, z in ((x1 - 1, dz1 + 6), (x2 + 1, dz1 + 6)):
            d.set(x, y0 + 1, z, "lantern[hanging=false,waterlogged=false]")
    return d


# ----------------------------------------------------------------------------------------------- Neoterra
def neoterra(rel, L):
    d = Design("Neoterra", rel, (44, 42, 40), gy=1, paving="smooth_stone")
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
    seats += d.seating(x1 + 5, z1 + 1, x2 - 2, z2 - 6, y0, max(0, need - seats), "birch", "post",
                       rug=("cyan_carpet",), step=4)
    for x in range(x1 + 2, x2 - 1, 3):
        d.set(x, 6, z1 + 6, "sea_lantern")
    d.plant(x1 + 1, y0, z2 - 1, "potted_bamboo")
    # stair core in the south-east corner (straight flight along x)
    for i in range(6):
        x = x2 - 6 + i
        d.set(x, y0 + i, z2 - 2, "smooth_quartz_stairs[facing=east,half=bottom,shape=straight,waterlogged=false]")
    for x in range(x2 - 4, x2):
        d.set(x, 7, z2 - 2, AIR)
    # upper floor: capsule rooms (8 beds) along both long walls, glass corridor
    yb = 8
    for x in range(x1 + 1, x1 + 9, 2):
        d.bed(x, yb, z1 + 1, "north")
        d.bed(x, yb, z2 - 4, "south")
        d.set(x + 1, yb, z1 + 1, "white_concrete")
        d.set(x + 1, yb + 1, z1 + 1, "white_concrete")
    for x in range(x1 + 1, x1 + 10):
        d.set(x, yb, z2 - 3, "light_gray_concrete")
        d.set(x, yb + 1, z2 - 3, "light_gray_stained_glass_pane")
    d.set(x1 + 9, yb, z2 - 3, "birch_door[facing=south,half=lower,hinge=left,open=false,powered=false]")
    d.set(x1 + 9, yb + 1, z2 - 3, "birch_door[facing=south,half=upper,hinge=left,open=false,powered=false]")
    for x in range(x1 + 2, x2 - 1, 4):
        d.set(x, 11, z1 + 5, "sea_lantern")
    d.rug(x1 + 1, z1 + 3, x2 - 1, z1 + 4, yb, ("light_gray_carpet",), "plain")
    if L == 3:                                                      # roof terrace bar
        for x in range(x1 + 1, x2):
            for z in range(z1, z2):
                d.set(x, 13, z, AIR)
        for x in range(x1 + 1, x2, 4):
            d.set(x, 13, z2 - 1, "azalea")
        for y in range(8, 13):
            d.set(x2 - 1, y, z1 + 2, "ladder[facing=west,waterlogged=false]")
        d.set(x2 - 1, 12, z1 + 2, "ladder[facing=west,waterlogged=false]")
        seats += d.seating(x1 + 1, z1 + 3, x2 - 2, z2 - 2, 13, max(0, need - seats), "birch", "post", step=4)
    return d


@design("tavern")
def tavern(pack, rel, L):
    from designs.shops import grow
    d = {"Hearthwood": hearthwood, "Cascadia": cascadia, "Neoterra": neoterra}[pack](rel, L)
    grow(d, L, "tavern")
    return d
