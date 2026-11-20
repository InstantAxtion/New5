"""
Civic & education landmarks: townhall, hospital, library, school, university, communitycollege.

See the per-type docstrings for what each pack's building is.
"""
from hm import Design, design, AIR, D4, OPP, CW

Y0 = 2   # first walkable layer


# ============================================================================================ helpers
def st(block, facing, half="bottom", shape="straight"):
    return f"{block}[facing={facing},half={half},shape={shape},waterlogged=false]"


def slab(block, typ="bottom"):
    return f"{block}[type={typ},waterlogged=false]"


def log(block, axis="y"):
    return f"{block}[axis={axis}]"


def flight(d, x, z, y0, yU, rise, block, under=None, width=1, side="east"):
    """Straight stair flight: first step at (x, y0, z), rising toward `rise` until the top step sits in the floor
    layer yU-1 (you step off onto the floor at yU). Headroom (3 blocks, for the jump) is cleared above every step.
    `width` extends the flight toward `side`. Returns the landing cell (x, z) on the upper floor."""
    dx, dz = D4[rise]
    sx, sz = D4[side]
    n = yU - y0
    for w in range(width):
        for i in range(n):
            cx, cz = x + dx * i + sx * w, z + dz * i + sz * w
            y = y0 + i
            d.set(cx, y, cz, st(block, rise))
            if under:
                for yy in range(y0, y):
                    d.set(cx, yy, cz, under)
            for yy in range(y + 1, y + 4):
                if d.bp.inside(cx, yy, cz):
                    d.set(cx, yy, cz, AIR)
    return x + dx * n, z + dz * n


def shelves(d, x1, z1, x2, z2, y, h=1):
    """Run of bookshelves (h high) on every free cell of the line/rectangle."""
    for x in range(min(x1, x2), max(x1, x2) + 1):
        for z in range(min(z1, z2), max(z1, z2) + 1):
            for k in range(h):
                if d.air(x, y + k, z):
                    d.bookshelf(x, y + k, z)


def rail(d, x1, z1, x2, z2, y, fence):
    for x in range(min(x1, x2), max(x1, x2) + 1):
        for z in range(min(z1, z2), max(z1, z2) + 1):
            if d.air(x, y, z):
                d.set(x, y, z, fence)


def beams(d, x1, x2, z1, z2, y, blk, every=4, axis="z"):
    """Exposed tie beams across a room (axis = direction the beam runs)."""
    if axis == "z":
        for x in range(x1, x2 + 1, every):
            for z in range(z1, z2 + 1):
                d.set(x, y, z, log(blk, "z"))
    else:
        for z in range(z1, z2 + 1, every):
            for x in range(x1, x2 + 1):
                d.set(x, y, z, log(blk, "x"))


def framing(d, x1, z1, x2, z2, y1, y2, post, every=2, sill=True):
    """Tudor framing on a calcite wall rectangle: posts every `every`, sill and head beams."""
    for x in range(x1, x2 + 1):
        for z in (z1, z2):
            if (x - x1) % every == 0 or x == x2:
                for y in range(y1, y2 + 1):
                    if not d.get(x, y, z).endswith("pane") and "door" not in d.get(x, y, z):
                        d.set(x, y, z, log(post, "y"))
            d.set(x, y2, z, log(post, "x"))
            if sill:
                d.set(x, y1, z, log(post, "x"))
    for z in range(z1, z2 + 1):
        for x in (x1, x2):
            if (z - z1) % every == 0 or z == z2:
                for y in range(y1, y2 + 1):
                    if not d.get(x, y, z).endswith("pane") and "door" not in d.get(x, y, z):
                        d.set(x, y, z, log(post, "y"))
            d.set(x, y2, z, log(post, "z"))
            if sill:
                d.set(x, y1, z, log(post, "z"))


def clockface(d, x, y, z, facing, face="quartz_block", frame=None, hand="black_concrete"):
    """3x3 clock face centred at (x,y,z) in a wall facing `facing` (hands at three o'clock)."""
    ax = (1, 0) if facing in ("north", "south") else (0, 1)
    for a in (-1, 0, 1):
        for b in (-1, 0, 1):
            d.set(x + ax[0] * a, y + b, z + ax[1] * a, face)
    right = {"north": -1, "south": 1, "east": -1, "west": 1}[facing]   # viewer's right
    d.set(x, y, z, hand)
    d.set(x, y + 1, z, hand)
    d.set(x + ax[0] * right, y, z + ax[1] * right, hand)
    if frame:
        fx, fz = D4[facing]
        for a in (-1, 1):
            d.set(x + ax[0] * a * 2, y, z + ax[1] * a * 2, frame)


def desk_rows(d, x1, x2, z1, z2, y, board, wood, top, every_x=3, need=None):
    """Classroom: rows of desk + chair pairs facing the board side (`board` = north/south/east/west).
    Desks are in pairs across, aisles between. Returns the number of seats placed."""
    n = 0
    bx, bz = D4[board]
    back = OPP[board]
    if board in ("north", "south"):
        rows = range(z1, z2, 2) if board == "north" else range(z2, z1, -2)
        for r in rows:
            for x in range(x1, x2 + 1):
                if every_x and (x - x1) % every_x == every_x - 1:
                    continue
                if need is not None and n >= need:
                    return n
                d.table(x, y, r, wood, "slab", top)
                d.chair(x, y, r - bz, back, wood)
                n += 1
    else:
        cols = range(x1, x2, 2) if board == "west" else range(x2, x1, -2)
        for c in cols:
            for z in range(z1, z2 + 1):
                if every_x and (z - z1) % every_x == every_x - 1:
                    continue
                if need is not None and n >= need:
                    return n
                d.table(c, y, z, wood, "slab", top)
                d.chair(c - bx, y, z, back, wood)
                n += 1
    return n


def blackboard(d, x1, z1, x2, z2, y, facing, blk="black_concrete", frame="dark_oak"):
    """Chalkboard hung on a wall face (cells just inside the wall), 2 high from y, chalk ledge below."""
    for x in range(min(x1, x2), max(x1, x2) + 1):
        for z in range(min(z1, z2), max(z1, z2) + 1):
            d.set(x, y, z, blk)
            d.set(x, y + 1, z, blk)
            d.set(x, y - 1, z, f"{frame}_trapdoor[facing={facing},half=top,open=false,powered=false,waterlogged=false]")


def ward_row(d, x1, x2, z, y, head, color, n, curtain="white_stained_glass_pane", step=2):
    """Row of hospital beds along x from x1, heads at row z pointing `head` (north/south), curtains between.
    Returns beds placed."""
    k = 0
    fz = D4[OPP[head]][1]
    for x in range(x1, x2 + 1, step):
        if k >= n:
            break
        d.bed(x, y, z, head, color)
        k += 1
        if x + 1 <= x2 and k < n:
            for zz in (z, z + fz):
                d.set(x + 1, y, zz, curtain)
                d.set(x + 1, y + 1, zz, curtain)
    return k


def ward_col(d, x, z1, z2, y, head, color, n, curtain="white_stained_glass_pane", step=2):
    k = 0
    fx = D4[OPP[head]][0]
    for z in range(z1, z2 + 1, step):
        if k >= n:
            break
        d.bed(x, y, z, head, color)
        k += 1
        if z + 1 <= z2 and k < n:
            for xx in (x, x + fx):
                d.set(xx, y, z + 1, curtain)
                d.set(xx, y + 1, z + 1, curtain)
    return k


def bench(d, x1, z1, x2, z2, y, back, wood, tag="sit"):
    """Bench / pew of stairs; every cell is a seat tagged `tag` ("sit", "sit_out" or None for decoration)."""
    for x in range(min(x1, x2), max(x1, x2) + 1):
        for z in range(min(z1, z2), max(z1, z2) + 1):
            d.chair(x, y, z, back, wood, sit=(tag == "sit"))
            if tag and tag != "sit":
                d.tag(x, y, z, tag)
                d.placed.setdefault("tagged", {}).setdefault(tag, 0)
                d.placed["tagged"][tag] += 1


def tree(d, x, y, z, logb="oak_log", leaves="oak_leaves", h=4, r=2):
    for k in range(h):
        d.set(x, y + k, z, log(logb))
    for dy in range(h - 2, h + 2):
        rr = r if dy < h else r - 1
        for a in range(-rr, rr + 1):
            for b in range(-rr, rr + 1):
                if abs(a) + abs(b) <= rr + (1 if dy == h - 1 else 0) and d.air(x + a, y + dy, z + b):
                    d.set(x + a, y + dy, z + b, f"{leaves}[distance=1,persistent=true,waterlogged=false]")


def lamppost(d, x, y, z, post, lamp="lantern", h=3):
    for k in range(h):
        d.set(x, y + k, z, post)
    d.set(x, y + h, z, f"{lamp}[hanging=false,waterlogged=false]" if "lantern" in lamp else lamp)


def bell(d, x, y, z, facing="north"):
    d.set(x, y, z, f"bell[attachment=ceiling,facing={facing},powered=false]")


def count(d, key):
    return d.placed["items"].get("minecraft:" + key, 0)


def need(d, key):
    return d.req["items"].get("minecraft:" + key, 0)


# ============================================================================================ TOWN HALL
"""
Town hall.
  Hearthwood  Tudor guildhall: long stone-and-timber hall (stone ground floor, framed calcite upper floor from L3)
              with a square stone clock & bell tower over the entrance. Ground floor: public hall in the middle,
              guild workshop (west) and civic stores with a loading door (east). Upstairs (L3+): council chamber
              with a long table and speaker's lectern, archive lined with shelves, guest quarters.
  Neoterra    glass civic centre: white concrete & glass slab with a slender concrete clock fin and open bell
              frame, plaza with a fountain and canopy. Ground: lobby + council chamber; level 2: maker space and
              store; level 3: archive and quarters; roof garden.
  Cascadia    timber grange lodge: long log hall with its gable to the street, deep porch, river-rock chimney,
              rear workshop lean-to, and a free-standing log fire-lookout tower carrying the bell.
"""


def townhall_hearthwood(rel, L):
    d = Design("Hearthwood", rel, (31, 36, 25), gy=1)
    S, beam = "stone_bricks", "stripped_dark_oak_log"
    two = L >= 3
    X1, X2 = (9, 21) if L == 1 else (3, 27)
    Z1, Z2 = 7, 17
    top = 10 if two else 5
    # ---- shell
    d.box(X1, Y0, Z1, X2, 5, Z2, S, floor="spruce_planks")
    d.fill(X1, 1, Z1, X2, 1, Z2, "spruce_planks")
    for x in range(X1, X2 + 1):
        for z in (Z1, Z2):
            d.set(x, Y0, z, "polished_andesite")
    for z in range(Z1, Z2 + 1):
        for x in (X1, X2):
            d.set(x, Y0, z, "polished_andesite")
    if L >= 2:
        for x in (9, 21):                                           # partitions
            d.fill(x, Y0, Z1 + 1, x, 5, Z2 - 1, S)
            d.door(x, Y0, 12, "east" if x == 9 else "west", "dark_oak")
    if two:
        d.fill(X1, 6, Z1, X2, 6, Z2, "dark_oak_planks")
        d.box(X1, 7, Z1, X2, top, Z2, "calcite")
        for x in (11, 21):                                          # upper partitions
            d.fill(x, 7, Z1 + 1, x, top, Z2 - 1, "dark_oak_planks")
            d.door(x, 7, 12, "east" if x == 11 else "west", "dark_oak")
    # windows: ground (leaded) between work blocks, upper between studs
    for x in range(X1 + 2, X2 - 1, 3):
        if 12 <= x <= 18:
            continue
        d.window(x, 3, Z1, x, 4, Z1)
        d.window(x, 3, Z2, x, 4, Z2)
    if two:
        for x in range(X1 + 1, X2, 4):
            if 12 <= x <= 18:
                continue
            d.window(x, 8, Z1, x + 1, 9, Z1)
        for x in range(13, 19, 2):
            d.window(x, 8, Z2, x, 9, Z2)
        framing(d, X1, Z1, X2, Z2, 7, top, beam, every=3)
        for x in range(X1, X2 + 1, 2):                              # jetty brackets under the upper floor
            d.set(x, 6, Z1 - 1, st("dark_oak_stairs", "south", "top"))
        for z in range(Z1, Z2 + 1):
            pass
    ridge = d.gable(X1, Z1, X2, Z2, top + 1, "x", "deepslate_tile_stairs", "deepslate_tile_slab",
                    "calcite" if two else S, overhang=1)
    for yy in range(top + 1, ridge):                                # king posts in the gable ends
        for x in (X1, X2):
            if d.get(x, yy, 12) == "minecraft:calcite":
                d.set(x, yy, 12, log(beam))
    if not two:
        beams(d, X1 + 2, X2 - 2, Z1 + 1, Z2 - 1, 6, beam, every=4)
    # big brick chimney on the west gable (workshop forge flue) from L2
    if L >= 2:
        for y in range(Y0, ridge + 3):
            d.set(X1, y, 12, "bricks")
            d.set(X1, y, 13, "bricks")
        d.set(X1, ridge + 3, 12, "brick_wall")
    # ---- tower over the entrance (x13..17, z3..7)
    tx1, tx2, tz1, tz2 = 13, 17, 3, 7
    tt = {1: 9, 2: 13}.get(L, 23)                                   # top of the shaft walls
    d.box(tx1, Y0, tz1, tx2, tt, tz2, S)
    d.fill(tx1 + 1, 1, tz1 + 1, tx2 - 1, 1, tz2 - 1, "polished_andesite")
    for y in range(Y0, tt + 1):                                     # quoins
        for x, z in ((tx1, tz1), (tx2, tz1), (tx1, tz2), (tx2, tz2)):
            d.set(x, y, z, "chiseled_stone_bricks" if y % 2 else "polished_andesite")
    d.clear(14, Y0, tz2, 16, 4, tz2)                                # arch into the hall
    d.set(14, 4, tz2, st("stone_brick_stairs", "west", "top"))
    d.set(16, 4, tz2, st("stone_brick_stairs", "east", "top"))
    d.double_door(15, Y0, tz1, "x", "south", "dark_oak") if False else d.door(15, Y0, tz1, "south", "dark_oak")
    d.set(14, 4, tz1, st("stone_brick_stairs", "west", "top"))
    d.set(16, 4, tz1, st("stone_brick_stairs", "east", "top"))
    d.set(15, 4, tz1, "chiseled_stone_bricks")
    d.sign(15, 5, tz1 - 1, "north", ["TOWN", "HALL"], "dark_oak")
    d.banner(14, 6, tz1 - 1, "north", "red")
    d.banner(16, 6, tz1 - 1, "north", "red")
    if two:
        d.fill(tx1 + 1, 6, tz1 + 1, tx2 - 1, 6, tz2 - 1, "dark_oak_planks")
        d.window(15, 7, tz1, 15, 9, tz1)                            # tall oriel-like window
        d.door(15, 7, tz2, "south", "dark_oak")                     # tower room off the council chamber
        d.set(15, 7, tz1 + 1, "red_carpet")
        d.set(14, 7, tz1 + 1, "dark_oak_stairs[facing=west,half=bottom,shape=straight,waterlogged=false]")
        d.set(16, 7, tz1 + 1, "dark_oak_stairs[facing=east,half=bottom,shape=straight,waterlogged=false]")
        d.lamp(15, 9, tz1 + 2)
        d.fill(tx1 + 1, 10, tz1 + 1, tx2 - 1, 10, tz2 - 1, "dark_oak_planks")
        # clock faces at y13 on three sides
        for y in (14, 18):                                          # string courses
            for x in range(tx1, tx2 + 1):
                d.set(x, y, tz1 - 1, st("stone_brick_stairs", "south", "top"))
        clockface(d, 15, 16, tz1, "north", "white_concrete")
        clockface(d, tx1, 16, 5, "west", "white_concrete")
        clockface(d, tx2, 16, 5, "east", "white_concrete")
    # belfry: open arches at the top of the shaft, bell hanging under the cap
    by = tt - 3                                                     # belfry floor below the arches
    d.fill(tx1 + 1, by, tz1 + 1, tx2 - 1, by, tz2 - 1, "dark_oak_planks")
    for y in range(by + 1, tt):
        for x in range(tx1 + 1, tx2):
            d.set(x, y, tz1, AIR)
            d.set(x, y, tz2, AIR)
        for z in range(tz1 + 1, tz2):
            d.set(tx1, y, z, AIR)
            d.set(tx2, y, z, AIR)
    for x in range(tx1 + 1, tx2):
        for z in (tz1, tz2):
            d.set(x, by + 1, z, "dark_oak_fence")
    for z in range(tz1 + 1, tz2):
        for x in (tx1, tx2):
            d.set(x, by + 1, z, "dark_oak_fence")
    d.fill(tx1, tt, tz1, tx2, tt, tz2, S)
    bell(d, 15, tt - 1, 5)
    rt = d.hip(tx1, tz1, tx2, tz2, tt + 1, "deepslate_tile_stairs", "deepslate_tile_slab", overhang=1)
    d.set(15, rt + 1, 5, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    # ---- central public hall (all levels)
    d.hut(11, Y0, 8)
    d.dining(14, Y0, 11, 3, "x", "dark_oak", ("n", "s"))
    d.rug(13, 10, 18, 12, Y0, ("red_carpet",), "plain")
    d.item(10, Y0, 14, "crafting_table")
    d.item(10, Y0, 15, "furnace", "east")
    d.item(10, Y0, 16, "furnace", "east")
    for z in (8, 9):
        for y in (Y0, Y0 + 1):
            d.item(20, y, z, "barrel", "west")
    d.bed(20, Y0, 16, "south")                                     # clerk's cot
    d.set(20, Y0, 14, "dark_oak_slab[type=top,waterlogged=false]")
    d.candle(20, Y0 + 1, 14, 2)
    d.set(10, Y0, 8, "potted_red_tulip")
    d.set(12, Y0, 8, "dark_oak_slab[type=top,waterlogged=false]")   # clerk's desk by the hut
    d.chair(12, Y0, 9, "south", "dark_oak", sit=False)
    for x in (12, 18):
        d.lamp(x, 5, 12)
    # ---- west wing: guild workshop
    if L >= 2:
        col = ["furnace", "furnace", "blast_furnace", "smoker", "water_cauldron", "anvil", "grindstone",
               "anvil" if need(d, "anvil") > 1 else None, "grindstone" if need(d, "grindstone") > 1 else None]
        for i, it in enumerate(col):
            z = 8 + i
            if it == "water_cauldron":
                d.item(4, Y0, z, "water_cauldron[level=3]")
            elif it:
                d.item(4, Y0, z, it, "east")
            else:
                d.set(4, Y0, z, "dark_oak_slab[type=top,waterlogged=false]")
        for z, it in zip(range(10, 15), ("crafting_table", "smithing_table", "fletching_table", "stonecutter",
                                         "crafting_table")):
            d.item(6, Y0, z, it, "east")
        d.item(8, Y0, 8, "loom", "west")
        d.item(8, Y0, 9, "cartography_table")
        d.item(8, Y0, 15, "brewing_stand")
        d.set(8, Y0, 16, "dark_oak_slab[type=top,waterlogged=false]")
        d.set(8, Y0 + 1, 16, "flower_pot")
        d.set(4, 4, 12, "wall_torch[facing=east]")
        for z in (9, 15):
            d.lamp(6, 5 if not two else 5, z)
        d.sign(9, 4, 12 - 2, "west", ["Guild", "Workshop"], "dark_oak") if False else None
    # ---- east wing: stores with loading door
    if L >= 2:
        for z in range(8, 16):
            if z in (12, 13):
                continue
            for y in (Y0, Y0 + 1):
                d.item(26, y, z, "barrel", "west")
        for x in (23, 24, 25):
            for y in (Y0, Y0 + 1):
                d.item(x, y, 16, "barrel", "north")
        d.double_door(27, Y0, 12, "z", "west", "spruce")
        d.clear(27, Y0, 12, 27, Y0 + 1, 13)
        d.double_door(X2, Y0, 12, "z", "east", "spruce")
        d.fill(28, 1, 11, 29, 1, 14, "gravel")
        d.set(22, Y0, 8, "minecraft:chest[facing=south,type=single,waterlogged=false]")
        d.set(23, Y0, 8, "minecraft:chest[facing=south,type=single,waterlogged=false]")
        d.lamp(24, 5, 12)
        d.set(28, Y0, 10, "hay_block[axis=y]")
        d.set(28, Y0, 15, "barrel[facing=up,open=false]")
    # ---- upper floor (L3+)
    if two:
        # stairs in the hall, along the back wall, rising east to a landing at x20
        flight(d, 15, 16, Y0, 7, "east", "dark_oak_stairs", under="dark_oak_planks")
        d.set(14, Y0, 16, AIR)
        rail(d, 15, 15, 19, 15, 7, "dark_oak_fence")
        # council chamber x12..20
        for x in range(13, 20):
            d.table(x, 7, 11, "dark_oak", "block", "dark_oak_planks")
            d.set(x, 8, 11, "red_carpet") if x % 2 else None
            d.chair(x, 7, 10, "north", "dark_oak")
            d.chair(x, 7, 12, "south", "dark_oak")
        d.chair(12, 7, 11, "west", "dark_oak", arms=False)          # mayor's chair at the head
        d.item(20, 7, 11, "lectern", "east")
        d.set(12, 9, 8, "red_wall_banner[facing=south]")
        d.rug(12, 9, 20, 13, 7, ("red_carpet",), "plain")
        for x in (13, 16, 19):
            d.lamp(x, 10, 11, "lantern")
        d.set(12, 10, 11, "dark_oak_planks")
        if L >= 4:
            d.item(20, 7, 8, "jukebox")
            d.set(12, 7, 14, "dark_oak_stairs[facing=west,half=bottom,shape=straight,waterlogged=false]")
            d.set(12, 7, 15, "dark_oak_stairs[facing=west,half=bottom,shape=straight,waterlogged=false]")
        # archive (west, x4..10)
        shelves(d, 4, 8, 4, 16, 7, 3)
        shelves(d, 5, 16, 10, 16, 7, 3)
        shelves(d, 5, 8, 5, 8, 7, 3)
        d.item(7, 7, 12, "enchanting_table")
        d.chair(7, 7, 13, "south", "dark_oak", sit=False)
        d.rug(6, 11, 8, 13, 7, ("green_carpet",), "plain")
        d.set(10, 7, 8, "cartography_table") if False else d.set(10, 7, 9, "dark_oak_slab[type=top,waterlogged=false]")
        d.candle(10, 8, 9, 3)
        d.lamp(7, 10, 10)
        d.lamp(7, 10, 14)
        # quarters (east, x22..26): 5 beds, heads to the east wall, nightstands between
        for i, z in enumerate((8, 10, 12, 14, 16)):
            d.bed(26, 7, z, "east")
            if z < 16:
                d.set(26, 7, z + 1, "spruce_slab[type=top,waterlogged=false]")
                d.candle(26, 8, z + 1, 1)
        d.rug(22, 9, 23, 15, 7, ("orange_carpet",), "plain")
        if L >= 4:
            d.item(22, 7, 8, "ender_chest", "south")
        d.lamp(24, 10, 10)
        d.lamp(24, 10, 14)
    # ---- forecourt
    d.fill(13, 1, 0, 17, 1, 2, "stone_bricks")
    if L >= 2:
        for x in (11, 19):
            lamppost(d, x, Y0, 2, "dark_oak_fence")
    if L >= 4:                                                     # flower beds along the facade
        for x in list(range(4, 12)) + list(range(19, 27)):
            d.set(x, 1, 5, "grass_block[snowy=false]")
            d.set(x, 1, 6, "grass_block[snowy=false]")
            d.set(x, Y0, 5, "dark_oak_fence" if x in (4, 11, 19, 26) else AIR)
            d.set(x, Y0, 6, ("poppy", "oxeye_daisy", "cornflower", "allium")[x % 4])
    if L == 5:                                                     # market cross on the green
        for x, z in ((7, 2), (23, 2)):
            d.set(x, Y0, z, "stone_brick_wall")
            d.set(x, Y0 + 1, z, "stone_brick_wall")
            d.set(x, Y0 + 2, z, "lantern[hanging=false,waterlogged=false]")
        bench(d, 4, 2, 5, 2, Y0, "north", "dark_oak", tag=None)
        bench(d, 25, 2, 26, 2, Y0, "north", "dark_oak", tag=None)
    return d


@design("townhall")
def townhall(pack, rel, L):
    return {"Hearthwood": townhall_hearthwood, "Cascadia": townhall_cascadia,
            "Neoterra": townhall_neoterra}[pack](rel, L)


def townhall_cascadia(rel, L):
    return townhall_hearthwood(rel, L)


def townhall_neoterra(rel, L):
    return townhall_hearthwood(rel, L)
