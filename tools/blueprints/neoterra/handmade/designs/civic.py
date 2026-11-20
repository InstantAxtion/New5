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


def townhall_neoterra(rel, L):
    d = Design("Neoterra", rel, (29, 34, 27), gy=1, paving="smooth_stone")
    W, G, Q = "white_concrete", "light_gray_concrete", "smooth_quartz"
    two = L >= 3
    X1, X2 = (8, 18) if L == 1 else (3, 23)
    Z1, Z2 = 8, 20
    top = 10 if two else 5
    d.box(X1, Y0, Z1, X2, top, Z2, W, floor="polished_diorite")
    if two:
        d.fill(X1, 6, Z1, X2, 6, Z2, G)
    # curtain walls: concrete columns every 4, glass between (street side full height, sides ribbon windows)
    for x in range(X1 + 1, X2):
        if (x - X1) % 4:
            d.window(x, Y0, Z1, x, 5, Z1, "glass_pane")
            if two:
                d.window(x, 7, Z1, x, 10, Z1, "light_gray_stained_glass_pane")
            d.window(x, 3, Z2, x, 4, Z2, "glass_pane")
    for z in range(Z1 + 2, Z2 - 1):
        if z % 4:
            d.window(X1, 3, z, X1, 4, z, "glass_pane")
            d.window(X2, 3, z, X2, 4, z, "glass_pane")
            if two:
                d.window(X2, 8, z, X2, 9, z, "glass_pane")
    for x in range(X1, X2 + 1):                                     # cyan floor band
        d.set(x, 6, Z1, "cyan_terracotta")
    d.flat(X1, Z1, X2, Z2, top + 1, Q, W, "smooth_quartz_slab")
    if L >= 2:
        for x in (8, 18):
            d.fill(x, Y0, Z1 + 1, x, 5, Z2 - 1, G)
            d.door(x, Y0, 14, "east" if x == 8 else "west", "birch")
    # entrance: double glass doors under a cantilevered canopy
    d.double_door(12, Y0, Z1, "x", "south", "birch")
    d.double_door(14, Y0, Z1, "x", "south", "birch") if False else None
    for x in range(10, 17):
        for z in range(Z1 - 3, Z1):
            d.set(x, 6, z, slab("smooth_quartz_slab", "top"))
    for x in (10, 16):
        d.set(x, 6, Z1 - 3, "sea_lantern")
    d.sign(13, 7, Z1 - 1, "north", ["CIVIC", "CENTRE"], "birch", glow=True, color="cyan") if two else \
        d.sign(13, 5, Z1 - 4, "north", ["CIVIC", "CENTRE"], "birch", glow=True, color="cyan")
    # ---- clock fin + bell frame (east end, in front)
    fx1, fx2, fz1, fz2 = 24, 26, 7, 9
    ft = {1: 12, 2: 16}.get(L, 24)
    if L == 1:
        fx1, fx2 = 20, 22
    for x in range(fx1, fx2 + 1):
        for z in range(fz1, fz2 + 1):
            for y in range(Y0, ft + 1):
                d.set(x, y, z, W)
    for y in range(Y0 + 1, ft - 3):
        d.set(fx1 + 1, y, fz1, "cyan_stained_glass")
    clockface(d, fx1 + 1, ft - 1, fz1, "north", "black_concrete", hand="sea_lantern")
    clockface(d, fx1, ft - 1, fz1 + 1, "west", "black_concrete", hand="sea_lantern")
    # open bell frame on top: corner posts, slab roof
    for x, z in ((fx1, fz1), (fx2, fz1), (fx1, fz2), (fx2, fz2)):
        for y in range(ft + 1, ft + 4):
            d.set(x, y, z, "quartz_pillar[axis=y]")
    d.fill(fx1, ft + 4, fz1, fx2, ft + 4, fz2, Q)
    bell(d, fx1 + 1, ft + 3, fz1 + 1)
    d.set(fx1 + 1, ft + 5, fz1 + 1, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    # ---- plaza with fountain
    d.fill(1, 1, 1, 27, 1, Z1 - 1, "polished_diorite") if L >= 2 else d.fill(7, 1, 1, 19, 1, Z1 - 1, "polished_diorite")
    fxc, fzc = 6, 3
    if L >= 2:
        for x in range(fxc - 2, fxc + 3):
            for z in range(fzc - 1, fzc + 2):
                edge = x in (fxc - 2, fxc + 2) or z in (fzc - 1, fzc + 1)
                d.set(x, Y0, z, slab("smooth_quartz_slab") if edge else "water[level=0]")
                if not edge:
                    d.set(x, 1, z, "light_blue_concrete")
        d.set(fxc, Y0, fzc, Q)
        d.set(fxc, Y0 + 1, fzc, "water[level=0]")
        d.set(fxc, 1, fzc, Q)
    # ---- lobby / council (centre)
    d.hut(10, Y0, 9)
    d.counter(9, 11, 11, 11, Y0, body=Q)                          # reception desk
    d.chair(10, Y0, 12, "south", "birch", sit=False)
    for x, z in ((12, 13), (13, 13), (12, 14), (13, 14)):           # round council table, 8 chairs
        d.table(x, Y0, z, "birch", "block", "smooth_quartz")
    for x in (12, 13):
        d.chair(x, Y0, 12, "north", "birch")
        d.chair(x, Y0, 15, "south", "birch")
    for z in (13, 14):
        d.chair(11, Y0, z, "west", "birch")
        d.chair(14, Y0, z, "east", "birch")
    d.rug(11, 12, 14, 15, Y0, ("cyan_carpet",), "plain")
    d.item(9, Y0, 16, "crafting_table")
    d.item(9, Y0, 17, "furnace", "east")
    d.item(9, Y0, 18, "furnace", "east")
    for z in (9, 10):
        for y in (Y0, Y0 + 1):
            d.item(17, y, z, "barrel", "west")
    d.bed(17, Y0, 19, "south", "cyan")
    d.plant(16, Y0, 19, "potted_bamboo")
    d.plant(16, Y0, 9, "potted_bamboo")
    for x in (10, 13, 16):
        d.set(x, 5, 14, "sea_lantern")
    # ---- maker space (west)
    if L >= 2:
        col = ["furnace", "blast_furnace", "smoker", "water_cauldron", "brewing_stand", "anvil", "grindstone",
               "anvil" if need(d, "anvil") > 1 else None, "grindstone" if need(d, "grindstone") > 1 else None,
               "stonecutter", "smithing_table"]
        for i, it in enumerate(col):
            z = 9 + i
            if it == "water_cauldron":
                d.item(4, Y0, z, "water_cauldron[level=3]")
            elif it:
                d.item(4, Y0, z, it, "east")
            else:
                d.set(4, Y0, z, slab("smooth_quartz_slab", "top"))
        for z, it in zip((9, 10, 11, 12, 16, 17, 18), ("crafting_table", "crafting_table", "fletching_table",
                                                       "loom", "cartography_table", None, None)):
            if it:
                d.item(7, Y0, z, it, "west")
            else:
                d.set(7, Y0, z, slab("smooth_quartz_slab", "top"))
        for z in (10, 14, 18):
            d.set(5, 5, z, "sea_lantern")
            d.set(6, 5, z, "sea_lantern")
    # ---- stores (east) with loading door
    if L >= 2:
        for z in range(9, 20):
            if z in (14, 15):
                continue
            for y in (Y0, Y0 + 1):
                d.item(22, y, z, "barrel", "west")
        for z in (9, 10):
            for y in (Y0, Y0 + 1):
                d.item(19, y, z, "barrel", "east")
        d.double_door(X2, Y0, 14, "z", "east", "mangrove")
        d.fill(24, 1, 13, 27, 1, 16, "polished_andesite")
        for z in (12, 16):
            d.set(21, 5, z, "sea_lantern")
    # ---- upper floor (L3+)
    if two:
        flight(d, 10, 19, Y0, 7, "east", "smooth_quartz_stairs", under=Q)
        rail(d, 11, 18, 14, 18, 7, "glass_pane")
        for x in (9, 17):
            d.fill(x, 7, Z1 + 1, x, 10, Z2 - 1, G)
            d.door(x, 7, 17, "east" if x == 9 else "west", "birch")
        # council chamber: horseshoe table facing the speaker's lectern
        for x in range(11, 16):
            d.table(x, 7, 15, "birch", "block", "smooth_quartz")
            d.chair(x, 7, 16, "south", "mangrove")
        for z in (12, 13, 14):
            d.table(11, 7, z, "birch", "block", "smooth_quartz")
            d.table(15, 7, z, "birch", "block", "smooth_quartz")
            d.chair(10, 7, z, "west", "mangrove")
            d.chair(16, 7, z, "east", "mangrove")
        d.item(13, 7, 10, "lectern", "south")
        d.banner(13, 9, 9, "south", "cyan")
        d.rug(12, 11, 14, 14, 7, ("light_gray_carpet",), "plain")
        if L >= 4:
            d.item(16, 7, 10, "jukebox")
        for x in (11, 13, 15):
            d.set(x, 10, 13, "sea_lantern")
        # archive (west): full-height shelving
        shelves(d, 4, 9, 4, 19, 7, 3)
        shelves(d, 5, 19, 8, 19, 7, 3)
        d.item(6, 7, 13, "enchanting_table")
        d.set(6, 7, 15, slab("smooth_quartz_slab", "top"))
        d.chair(6, 7, 16, "south", "birch", sit=False)
        d.rug(5, 12, 7, 14, 7, ("cyan_carpet",), "plain")
        for z in (11, 16):
            d.set(6, 10, z, "sea_lantern")
        # quarters (east): capsule rooms
        for z in (9, 11, 13, 15, 17):
            d.bed(22, 7, z, "east", "cyan")
            d.set(22, 7, z + 1, W)
            d.set(21, 7, z + 1, "light_gray_stained_glass_pane")
        if L >= 4:
            d.item(18, 7, 19, "ender_chest", "east")
        for z in (11, 16):
            d.set(19, 10, z, "sea_lantern")
    # ---- roof garden (L4+): planters, solar panels; L5 pergola + rooftop access by ladder
    if L >= 4:
        ry = top + 2
        for x in range(X1 + 1, X2):
            for z in (Z1 + 1, Z2 - 1):
                d.set(x, ry, z, "moss_block" if x % 3 else "azalea")
        for x in range(X1 + 2, X2 - 1, 2):
            for z in range(Z1 + 4, Z1 + 8):
                d.set(x, ry, z, "daylight_detector[inverted=false,power=0]")
        for x in range(5, 22, 4):
            d.set(x, ry, Z2 - 3, "flowering_azalea")
    if L >= 5:
        for x in (1, 27):
            for z in (2, 6):
                lamppost(d, x, Y0, z, "end_rod[facing=up]", "sea_lantern", 2) if False else None
        for x in (2, 11, 17, 26):
            d.set(x, Y0, 1, "birch_fence")
            d.set(x, Y0 + 1, 1, "end_rod[facing=up]")
        bench(d, 10, 3, 12, 3, Y0, "north", "birch", tag=None)
        bench(d, 15, 3, 17, 3, Y0, "north", "birch", tag=None)
        for x in (9, 18):                                          # planters
            d.set(x, Y0, 3, "moss_block")
            d.set(x, Y0 + 1, 3, "flowering_azalea")
    return d


def townhall_cascadia(rel, L):
    d = Design("Cascadia", rel, (27, 30, 33), gy=1, paving="coarse_dirt")
    lg = "spruce_log"
    X1, X2 = 5, 19
    Z1, Z2 = 8, (18 if L == 1 else 28)
    loft = L >= 3
    # log walls on a river-rock footing, gable turned to the street
    d.box(X1, Y0, Z1, X2, 6, Z2, log(lg, "z"), floor="spruce_planks")
    for x in range(X1, X2 + 1):
        for y in range(Y0, 7):
            d.set(x, y, Z1, log(lg, "x"))
            d.set(x, y, Z2, log(lg, "x"))
    for x in range(X1, X2 + 1):
        for z in range(Z1, Z2 + 1):
            if x in (X1, X2) or z in (Z1, Z2):
                d.set(x, Y0, z, "mossy_cobblestone" if (x * 3 + z) % 4 == 0 else "cobblestone")
    for x, z in ((X1, Z1), (X2, Z1), (X1, Z2), (X2, Z2)):
        for y in range(Y0, 7):
            d.set(x, y, z, log("stripped_spruce_log"))
    if L >= 2:
        for y in range(Y0, 7):
            d.set(X1, y, 18, log("stripped_spruce_log"))
            d.set(X2, y, 18, log("stripped_spruce_log"))
    ridge = d.gable(X1, Z1, X2, Z2, 7, "z", "deepslate_tile_stairs", "deepslate_tile_slab", "stripped_spruce_log[axis=y]",
                    overhang=1)
    for y in range(7, ridge):                                       # board-and-batten gable ends
        for x in range(X1, X2 + 1):
            for z in (Z1, Z2):
                if d.get(x, y, z).startswith("minecraft:stripped_spruce_log"):
                    d.set(x, y, z, "spruce_planks" if x % 2 else log("stripped_spruce_log"))
    mid = (X1 + X2) // 2
    d.window(mid - 1, 9, Z1, mid + 1, 10, Z1)                        # gable window
    d.set(mid, 9, Z1, log("spruce_log"))
    if loft:
        d.fill(X1 + 1, 7, Z1 + 1, X2 - 1, 7, Z2 - 1, "spruce_planks")
    else:
        beams(d, X1 + 1, X2 - 1, Z1 + 2, Z2 - 2, 7, "stripped_spruce_log", every=4, axis="x")
    # windows
    for z in range(Z1 + 3, Z2 - 1, 4):
        for x in (X1, X2):
            d.window(x, 3, z, x, 4, z)
    for x in (X1 + 3, X2 - 3):
        d.window(x, 3, Z1, x, 4, Z1)
    # entrance and the deep porch with log posts
    d.double_door(mid, Y0, Z1, "x", "south", "spruce") if False else d.door(mid, Y0, Z1, "south", "spruce")
    d.set(mid - 1, Y0, Z1, log(lg, "x"))
    pz = Z1 - 4
    d.fill(X1 - 1, 1, pz, X2 + 1, 1, Z1 - 1, "spruce_planks")
    for x in (X1 - 1, mid - 3, mid + 3, X2 + 1):
        for y in range(Y0, 6):
            d.set(x, y, pz, log(lg))
    for x in range(X1 - 2, X2 + 3):
        d.set(x, 6, pz - 1, st("spruce_stairs", "south"))
        for z in range(pz, Z1):
            d.set(x, 6, z, slab("spruce_slab"))
    for x in range(X1 - 1, X2 + 2):
        if abs(x - mid) > 1 and x not in (X1 - 1, mid - 3, mid + 3, X2 + 1):
            d.set(x, Y0, pz, "spruce_fence")
    d.sign(mid, 5, Z1 - 1, "north", ["GRANGE", "HALL"], "spruce")
    d.set(mid - 2, 5, Z1 - 2, "lantern[hanging=true,waterlogged=false]")
    d.set(mid + 2, 5, Z1 - 2, "lantern[hanging=true,waterlogged=false]")
    d.chair(X1 + 1, Y0, Z1 - 2, "south", "spruce", sit=False)
    d.chair(X1 + 2, Y0, Z1 - 2, "south", "spruce", sit=False)
    # river-rock chimney + fireplace on the west wall of the hall
    fz = 13
    d.hearth(X1 + 1, Y0, fz, "east", 7, "cobblestone", "campfire")
    for z in (fz - 1, fz, fz + 1):
        for y in range(Y0, ridge - 1):
            d.set(X1 - 1, y, z, "mossy_cobblestone" if (y + z) % 3 == 0 else "cobblestone")
        d.set(X1, 1, z, "cobblestone")
    for y in range(Y0 + 2, ridge - 1):
        d.set(X1, y, fz, "cobblestone")
    d.set(X1 + 1, Y0 + 2, fz, AIR)
    d.set(X1 + 1, Y0 + 3, fz, AIR)
    d.fill(X1 - 1, Y0, fz, X1, ridge - 1, fz, "cobblestone")
    d.set(X1 - 1, ridge - 1, fz, "cobblestone_wall")
    d.set(X1 + 1, Y0, fz, "campfire[facing=east,lit=true,signal_fire=false,waterlogged=false]")
    # ---- council hall (front part)
    d.hut(mid + 1, Y0, Z1 + 1)
    for z in range(11, 16):
        d.table(mid + 1, Y0, z, "spruce", "block", "stripped_spruce_wood[axis=y]")
        d.chair(mid, Y0, z, "west", "spruce")
        d.chair(mid + 2, Y0, z, "east", "spruce")
    d.chair(mid + 1, Y0, 16, "south", "spruce")
    d.rug(X1 + 2, 12, X1 + 3, 14, Y0, ("brown_carpet",), "plain")
    d.item(X2 - 1, Y0, Z1 + 1, "crafting_table")
    d.item(X2 - 1, Y0, Z1 + 2, "furnace", "west")
    d.item(X2 - 1, Y0, Z1 + 3, "furnace", "west")
    for z in (16, 17) if L == 1 else (12, 13):
        for y in (Y0, Y0 + 1):
            d.item(X2 - 1, y, z, "barrel", "west")
    d.bed(X1 + 1, Y0, 17 if L == 1 else 16, "west")
    if L == 1:
        d.set(X1 + 1, Y0, 16, slab("spruce_slab", "top"))
    for z in (10, 14) if L == 1 else (10, 14):
        d.lamp(mid + 1, 6 if loft else 6, z)
    # ---- workshop & stores (rear, L2+)
    if L >= 2:
        d.fill(X1 + 1, Y0, 18, X2 - 1, 6, 18, log(lg, "x"))
        d.door(X1 + 3, Y0, 18, "south", "spruce")
        col = ["furnace", "blast_furnace", "smoker", "water_cauldron", "brewing_stand", "anvil", "grindstone"]
        if need(d, "anvil") > 1:                                    # second anvil free-standing mid-floor
            d.item(mid, Y0, 23, "anvil", "east")
        for i, it in enumerate(col):
            z = 20 + i
            if it == "water_cauldron":
                d.item(X1 + 1, Y0, z, "water_cauldron[level=3]")
            elif it:
                d.item(X1 + 1, Y0, z, it, "east")
        for i, it in enumerate(["crafting_table", "smithing_table", "fletching_table", "stonecutter", "loom",
                                "cartography_table", "grindstone" if need(d, "grindstone") > 1 else None]):
            if it:
                d.item(X2 - 1, Y0, 20 + i, it, "west")
        # stores: barrel shelving against the back wall either side of the back door
        for x in range(X1 + 1, X2):
            if abs(x - mid) <= 1:
                continue
            for y in (Y0, Y0 + 1):
                d.item(x, y, Z2 - 1, "barrel", "north")
        d.double_door(mid, Y0, Z2, "x", "north", "spruce") if False else d.door(mid, Y0, Z2, "north", "spruce")
        d.set(mid, Y0, Z2 - 1, AIR)
        d.lamp(mid, 6, 22)
        d.lamp(mid, 6, 25)
        d.set(mid - 2, Y0, Z2 + 1, "chopping" if False else log("stripped_spruce_log"))
        d.set(mid - 2, Y0 + 1, Z2 + 1, "iron_axe" if False else AIR)
        for x in range(X1, X1 + 4):                                 # woodpile under the eave
            d.set(x, Y0, Z2 + 1, log("spruce_log", "x"))
    # ---- loft (L3+): archive at the front, bunk quarters at the back
    if loft:
        lx = flight(d, X1 + 6, 18 if False else 17, Y0, 8, "east", "spruce_stairs", under="spruce_planks")
        rail(d, X1 + 7, 16, X1 + 11, 16, 8, "spruce_fence")
        for z in range(Z1 + 1, 17):                                 # bookshelves under both slopes
            d.bookshelf(X1 + 2, 8, z, 1)
            d.bookshelf(X1 + 3, 8, z, 2)
            if z != Z1 + 1:
                d.bookshelf(X2 - 2, 8, z, 1)
                d.bookshelf(X2 - 3, 8, z, 2)
        d.item(mid, 8, 12, "enchanting_table")
        d.item(mid, 8, 15, "lectern", "north")
        d.chair(mid - 1, 8, 12, "east", "spruce", sit=False)
        d.rug(mid - 1, 11, mid + 1, 13, 8, ("green_carpet",), "plain")
        for z in (19, 21, 23, 25, 27):
            d.bed(X1 + 4, 8, z, "west")
            if z < 27:
                d.set(X1 + 4, 8, z + 1, slab("spruce_slab", "top"))
        if L >= 4:
            d.item(X2 - 4, 8, 20, "ender_chest", "west")
            d.item(X1 + 2, Y0, 9, "jukebox")
        for z in (11, 20, 25):
            d.lamp(mid, 13, z)
        d.set(mid, 14, 11, "spruce_planks") if False else None
        # dormers on both slopes for light
        for z in (12, 22):
            for x, f in ((X1 + 2, "west"), (X2 - 2, "east")):
                d.window(x, 9, z, x, 9, z)
    # ---- fire-lookout bell tower (L3+); L1-2 a bell frame on the porch
    if L >= 3:
        tx1, tx2, tz1, tz2 = 21, 25, 9, 13
        for x, z in ((tx1, tz1), (tx2, tz1), (tx1, tz2), (tx2, tz2)):
            for y in range(Y0, 16):
                d.set(x, y, z, log(lg))
            d.set(x, 1, z, "cobblestone")
        for y in (7, 12):
            for x in range(tx1 + 1, tx2):
                d.set(x, y, tz1, log(lg, "x"))
                d.set(x, y, tz2, log(lg, "x"))
            for z in range(tz1 + 1, tz2):
                d.set(tx1, y, z, log(lg, "z"))
                d.set(tx2, y, z, log(lg, "z"))
        d.fill(tx1, 15, tz1, tx2, 15, tz2, "spruce_planks")
        d.box(tx1, 16, tz1, tx2, 18, tz2, "spruce_planks")
        for x in range(tx1 + 1, tx2):
            d.window(x, 16, tz1, x, 17, tz1)
            d.window(x, 16, tz2, x, 17, tz2)
        for z in range(tz1 + 1, tz2):
            d.window(tx1, 16, z, tx1, 17, z)
            d.window(tx2, 16, z, tx2, 17, z)
        rt = d.hip(tx1, tz1, tx2, tz2, 19, "dark_oak_stairs", "dark_oak_slab", overhang=1)
        d.fill(23, 19, 11, 23, rt - 1, 11, log(lg))
        bell(d, 23, 18, 11)
        for y in range(Y0, 15):
            d.set(22, y, tz1 + 1, "ladder[facing=south,waterlogged=false]") if False else None
    else:
        bx = X2 + 3
        for y in range(Y0, 6):
            d.set(bx, y, 6, log(lg))
            d.set(bx + 2, y, 6, log(lg))
        d.fill(bx, 6, 6, bx + 2, 6, 6, log(lg, "x"))
        bell(d, bx + 1, 5, 6)
    if L >= 5:                                                       # flagpole & rail fence yard
        for y in range(Y0, 12):
            d.set(2, y, 3, "spruce_fence")
        d.banner(2, 11, 4, "south", "green") if False else d.set(2, 12, 3, "green_wool")
        for z in range(10, 30, 1):
            d.set(1, Y0, z, "spruce_fence")
        d.set(3, Y0, 30, "hay_block[axis=y]")
        d.set(4, Y0, 30, "barrel[facing=up,open=false]")
    return d


@design("townhall")
def townhall(pack, rel, L):
    return {"Hearthwood": townhall_hearthwood, "Cascadia": townhall_cascadia,
            "Neoterra": townhall_neoterra}[pack](rel, L)


# ============================================================================================ HOSPITAL
"""
Hospital.
  Hearthwood  Victorian cottage hospital: brick, tall cross-gabled admin block with an entrance porch, Nightingale
              ward wings (beds in two rows, heads to the walls under tall windows, white curtains between). Admin:
              waiting bench, nurses' station, dispensary (brewing stand, sterilising furnace, wash basin, supply
              rack, barrels). East ward from L1, west ward from L4, walled garden at L5.
  Neoterra    medical centre: white glass box with a glowing cross, reception desk, dispensary; ground-floor bay
              ward behind a glass partition, upstairs ward from L3, ambulance bay from L4, rooftop helipad at L5.
  Cascadia    ranger infirmary: log clinic cabin (gable to the street, porch, stone chimney) with a long log ward
              wing; screened sleeping porch on the ward from L4, herb garden at L5.
"""


def hospital_hearthwood(rel, L):
    d = Design("Hearthwood", rel, (29, 20, 23), gy=1)
    B, SB = "bricks", "stone_bricks"
    nb = d.req["beds"]

    def wing(x1, x2):
        d.box(x1, Y0, 6, x2, 6, 14, B, floor="oak_planks")
        for x in range(x1, x2 + 1):
            for z in (6, 14):
                d.set(x, Y0, z, SB)
        for z in range(6, 15):
            for x in (x1, x2):
                d.set(x, Y0, z, SB)
        d.gable(x1, 6, x2, 14, 7, "x", "deepslate_tile_stairs", "deepslate_tile_slab", B, overhang=1)
    E2 = 20 if L <= 2 else 22
    wing(16, E2)
    if L >= 4:
        wing(4, 10)
    # admin block (taller, cross gable to the street)
    d.box(10, Y0, 4, 16, 8, 16, B, floor="oak_planks")
    for x in range(10, 17):
        for z in (4, 16):
            d.set(x, Y0, z, SB)
    for z in range(4, 17):
        for x in (10, 16):
            d.set(x, Y0, z, SB)
    rg = d.gable(10, 4, 16, 16, 9, "z", "deepslate_tile_stairs", "deepslate_tile_slab", B, overhang=1)
    d.clear(11, Y0, 5, 15, 6, 15)
    d.fill(11, 7, 5, 15, 7, 15, "oak_planks")                      # ceiling
    for x0 in (16, 10):
        if x0 == 10 and L < 4:
            continue
        d.clear(x0, Y0, 9, x0, 4, 11)
        d.door(x0, Y0, 10, "east", "oak", "left")
        d.set(x0, Y0, 9, SB)
        d.set(x0, Y0 + 1, 9, B)
        d.set(x0, Y0, 11, SB)
        d.set(x0, Y0 + 1, 11, B)
        d.set(x0, 4, 9, B)
        d.set(x0, 4, 11, B)
        d.set(x0, 4, 10, B)
    d.clear(17, Y0, 7, E2 - 1, 6, 13)
    if L >= 4:
        d.clear(5, Y0, 7, 9, 6, 13)
    # gable windows of the admin block, tall lancets
    d.window(13, 9, 4, 13, 10, 4)
    for x in (11, 15):
        d.window(x, 3, 4, x, 5, 4)
    d.window(13, 3, 16, 13, 5, 16)
    # chimney
    for y in range(Y0, rg + 3):
        d.set(15, y, 16, B)
    d.set(15, rg + 3, 16, "brick_wall") if False else d.set(15, rg + 3, 16, "flower_pot")
    # entrance porch with its own little gable
    d.door(13, Y0, 4, "south", "oak")
    for x in (12, 14):
        for y in range(Y0, 5):
            d.set(x, y, 2, "oak_fence" if y < 4 else "dark_oak_planks")
    d.fill(12, 5, 2, 14, 5, 3, "dark_oak_planks")
    d.gable(12, 2, 14, 3, 6, "z", "deepslate_tile_stairs", "deepslate_tile_slab", "dark_oak_planks", overhang=0)
    d.fill(12, 1, 1, 14, 1, 3, SB)
    d.sign(13, 6, 1, "north", ["Cottage", "Hospital"], "dark_oak") if False else \
        d.sign(13, 6, 3, "north", ["Cottage", "Hospital"], "dark_oak")
    d.set(13, 4, 3, "lantern[hanging=true,waterlogged=false]")
    # ---- admin interior
    d.hut(11, Y0, 5)
    if d.req["seats"]:
        d.chair(15, Y0, 6, "east", "oak")
        d.chair(15, Y0, 7, "east", "oak")
    d.set(15, Y0, 5, "potted_red_tulip")
    for x in (12, 13, 14):                                          # nurses' station
        d.set(x, Y0, 12, slab("dark_oak_slab", "top"))
    d.chair(13, Y0, 13, "south", "oak", sit=False)
    d.set(12, Y0 + 1, 12, "candle[candles=1,lit=false,waterlogged=false]")
    d.item(11, Y0, 14, "brewing_stand")
    d.item(11, Y0, 15, "water_cauldron[level=3]")
    d.item(15, Y0, 15, "furnace", "west")
    if d.req["racks"]:
        d.rack(15, Y0, 14, "west")
    nbar = need(d, "barrel")
    for x in (12, 13, 14)[:nbar]:
        d.item(x, Y0, 15, "barrel", "north")
    shelves(d, 12, 16, 14, 16, 3, 0)
    d.set(13, 6, 7, "lantern[hanging=true,waterlogged=false]")
    d.set(13, 6, 13, "lantern[hanging=true,waterlogged=false]")
    d.rug(11, 9, 15, 11, Y0, ("white_carpet",), "plain")
    # ---- wards: heads to the long walls, curtains between, tall window over each bed
    placed = 0
    for (x1, x2) in ((17, E2 - 1), (5, 9)):
        if x1 == 5 and L < 4:
            continue
        for zh, head in ((7, "north"), (13, "south")):
            k = ward_row(d, x1, x2, zh, Y0, head, "white", nb - placed)
            for x in range(x1, x1 + 2 * k, 2):
                d.window(x, 4, 6 if head == "north" else 14, x, 5, 6 if head == "north" else 14)
                d.set(x, Y0, zh + (1 if head == "north" else -1) * 2, AIR) if False else None
            placed += k
        for x in range(x1, x2 + 1, 2):
            d.set(x, 7, 10, log("stripped_dark_oak_log", "x")) if False else None
        beams(d, x1 + 1, x2, 7, 13, 7, "stripped_dark_oak_log", every=4, axis="z")
        for x in range(x1 + 1, x2 + 1, 4):
            d.set(x, 6, 10, "lantern[hanging=true,waterlogged=false]")
    # end windows of the wards
    d.window(E2, 3, 9, E2, 5, 11)
    if L >= 4:
        d.window(4, 3, 9, 4, 5, 11)
    # spare floor in the L1-2 ward: visitors' table
    if nb <= 4:
        d.dining(19, Y0, 10 if nb <= 2 else 10, 1, "x", "oak", ("e", "w"), sit=False) if nb <= 2 else None
    # ---- garden (L5): fenced lawn behind with benches and flower borders
    if L >= 5:
        for x in range(3, 26):
            for z in range(17, 22):
                d.set(x, 1, z, "grass_block[snowy=false]")
                if x in (3, 25) or z == 21:
                    d.set(x, Y0, z, "oak_fence")
        for x in range(5, 24, 3):
            d.set(x, Y0, 20, ("rose_bush[half=lower]", "peony[half=lower]", "lilac[half=lower]")[x % 3])
            d.set(x, Y0 + 1, 20, ("rose_bush[half=upper]", "peony[half=upper]", "lilac[half=upper]")[x % 3])
        bench(d, 7, 18, 9, 18, Y0, "south", "oak", tag=None)
        bench(d, 18, 18, 20, 18, Y0, "south", "oak", tag=None)
        d.door(13, Y0, 16, "north", "oak") if False else None
    for x in (11, 15):
        d.set(x, Y0, 3, "potted_red_tulip") if False else d.flowerbox(x, 3, x, 3, Y0)
    return d


def hospital_neoterra(rel, L):
    d = Design("Neoterra", rel, (25, 22, 25), gy=1, paving="smooth_stone")
    W, G = "white_concrete", "light_gray_concrete"
    nb = d.req["beds"]
    X1, X2, Z1, Z2 = 3, 15, 6, 18
    two = L >= 3
    top = 10 if two else 5
    d.box(X1, Y0, Z1, X2, top, Z2, W, floor="polished_diorite")
    if two:
        d.fill(X1, 6, Z1, X2, 6, Z2, G)
    for x in range(X1 + 1, X2):
        if (x - X1) % 3:
            d.window(x, Y0, Z1, x, 5, Z1, "glass_pane")
            if two:
                d.window(x, 8, Z1, x, 9, Z1, "glass_pane")
                d.window(x, 8, Z2, x, 9, Z2, "glass_pane")
            d.window(x, 3, Z2, x, 4, Z2, "glass_pane")
    for z in range(Z1 + 2, Z2 - 1, 3):
        d.window(X1, 3, z, X1, 4, z + 1, "glass_pane")
        if two:
            d.window(X1, 8, z, X1, 9, z + 1, "glass_pane")
    d.flat(X1, Z1, X2, Z2, top + 1, "smooth_quartz", W, "smooth_quartz_slab")
    for x in range(X1, X2 + 1):
        d.set(x, 6, Z1, "cyan_terracotta")
    d.double_door(8, Y0, Z1, "x", "south", "birch")
    # glowing cross on the facade + sign
    cx, cy = 12, (8 if two else 3)
    cz = Z1 - 1
    if two:
        for k in (-1, 0, 1):
            d.set(cx + k, cy + 1, cz, "sea_lantern")
            d.set(cx, cy + 1 + k, cz, "sea_lantern")
        for k in (-2, 2):
            d.set(cx + k, cy + 1, cz, "red_concrete")
            d.set(cx, cy + 1 + k, cz, "red_concrete")
    else:                                                           # rooftop cross sign on the single storey
        for k in (-1, 0, 1):
            d.set(cx + k, 8, Z1 + 1, "red_concrete")
            d.set(cx, 8 + k, Z1 + 1, "red_concrete")
        d.set(cx, 8, Z1 + 1, "sea_lantern")
        d.set(cx, 7, Z1 + 1, "red_concrete")
    d.sign(8, 6 if not two else 7, cz, "north", ["MEDICAL", "CENTRE"], "birch", glow=True, color="cyan")
    for x in range(6, 12):
        for z in range(Z1 - 3, Z1):
            d.set(x, 6 if not two else 6, z, slab("smooth_quartz_slab", "top"))
    # ---- ground floor: reception & dispensary (north), bay ward (south) behind glass
    d.hut(4, Y0, 7)
    for x in range(6, 11):
        d.set(x, Y0, 10, "smooth_quartz" if x != 8 else "white_concrete")
    d.set(10, Y0, 9, "smooth_quartz")
    d.chair(7, Y0, 11, "south", "birch", sit=False)
    d.set(9, Y0 + 1, 10, "daylight_detector[inverted=false,power=0]")
    d.item(4, Y0, 9, "brewing_stand")
    d.item(4, Y0, 10, "water_cauldron[level=3]")
    d.item(4, Y0, 11, "furnace", "east")
    if d.req["racks"]:
        d.rack(4, Y0, 8, "east")
    for z in range(need(d, "barrel")):
        d.item(11 + z, Y0, 11, "barrel", "north")
    if d.req["seats"]:
        d.chair(11, Y0, 7, "north", "birch", arms=False)
        d.chair(12, Y0, 7, "north", "birch")
        d.plant(13, Y0, 7, "potted_bamboo")
    # glass partition z12, door
    for x in range(X1 + 1, X2):
        d.set(x, Y0, 12, "white_stained_glass_pane")
        d.set(x, Y0 + 1, 12, "white_stained_glass_pane")
        d.set(x, Y0 + 2, 12, "white_concrete")
    d.door(8, Y0, 12, "south", "birch")
    d.set(8, 4, 12, "white_concrete")
    placed = ward_row(d, 5, 13, 17, Y0, "south", "cyan", nb)
    d.rug(4, 13, 14, 14, Y0, ("light_gray_carpet",), "plain")
    for x in (6, 10, 14):
        d.set(x, 5, 9, "sea_lantern")
        d.set(x, 5, 14, "sea_lantern")
    # ---- upper ward (L3+): stairs along the east wall
    if two:
        for z in range(7, 12):
            if not d.air(14, Y0, z):
                d.set(14, Y0, z, AIR)
        for z in range(7, 7 + need(d, "barrel")):
            pass
        flight(d, 14, 7, Y0, 7, "south", "smooth_quartz_stairs", under="smooth_quartz")
        rail(d, 13, 8, 13, 11, 7, "glass_pane")
        placed += ward_row(d, 5, 11, 7, 7, "north", "cyan", nb - placed)
        placed += ward_row(d, 5, 13, 17, 7, "south", "cyan", nb - placed)
        d.set(9, 7, 12, "smooth_quartz")                         # nurses' desk
        d.set(10, 7, 12, "smooth_quartz")
        d.chair(9, 7, 13, "south", "birch", sit=False)
        for x in (6, 10, 13):
            d.set(x, 10, 12, "sea_lantern")
    # barrels moved off the stair line on L3+
    # ---- ambulance bay (L4+)
    if L >= 4:
        d.box(X2, Y0, 9, 21, 5, Z2, W, floor="polished_andesite")
        d.flat(X2, 9, 21, Z2, 6, "smooth_quartz", W, "smooth_quartz_slab")
        d.clear(17, Y0, 9, 20, 4, 9)
        for x in range(17, 21):
            d.set(x, 5, 9, "red_concrete")
        d.door(X2, Y0, 14, "east", "birch")
        d.set(18, Y0, 13, "minecart[shape=north_south]") if False else d.set(18, 1, 13, "yellow_concrete")
        for z in range(10, 18):
            d.set(16, 1, z, "yellow_concrete") if z % 2 else None
        for x in range(16, 22):
            for z in range(3, 9):
                if z in (3,) or x in (16, 21):
                    pass
            d.set(x, 6, 8, slab("smooth_quartz_slab", "top"))
        d.rack(20, Y0, 17, "north") if False else d.set(20, Y0, 17, "white_concrete")
        d.set(19, Y0, 17, "white_concrete")
        d.set(18, 5, 13, "sea_lantern")
    # ---- helipad (L5)
    if L >= 5:
        ry = top + 1
        for x in range(X1 + 1, X2):
            for z in range(Z1 + 1, Z2):
                d.set(x, ry, z, "gray_concrete")
        H = ["#...#", "#...#", "#####", "#...#", "#...#"]
        for i, row in enumerate(H):
            for j, ch in enumerate(row):
                if ch == "#":
                    d.set(7 + j, ry, 10 + i, "white_concrete")
        for x, z in ((X1 + 1, Z1 + 1), (X2 - 1, Z1 + 1), (X1 + 1, Z2 - 1), (X2 - 1, Z2 - 1)):
            d.set(x, ry + 1, z, "end_rod[facing=up]")
    return d


def hospital_cascadia(rel, L):
    d = Design("Cascadia", rel, (27, 20, 27), gy=1, paving="coarse_dirt")
    lg = "spruce_log"
    nb = d.req["beds"]

    def logbox(x1, z1, x2, z2, ytop, along):
        d.box(x1, Y0, z1, x2, ytop, z2, log("stripped_spruce_log", "z"), floor="spruce_planks")
        for x in range(x1, x2 + 1):
            for y in range(Y0, ytop + 1):
                d.set(x, y, z1, log("stripped_spruce_log", "x"))
                d.set(x, y, z2, log("stripped_spruce_log", "x"))
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                if x in (x1, x2) or z in (z1, z2):
                    d.set(x, Y0, z, "mossy_cobblestone" if (x + 2 * z) % 5 == 0 else "cobblestone")
        for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
            for y in range(Y0, ytop + 1):
                d.set(x, y, z, log("dark_oak_log"))
        for x in range(x1, x2 + 1):
            d.set(x, ytop, z1, log("dark_oak_log", "x"))
            d.set(x, ytop, z2, log("dark_oak_log", "x"))
    WX2 = 17 if L <= 2 else 23
    # ward wing (gable along x)
    logbox(11, 7, WX2, 15, 5, "x")
    d.gable(11, 7, WX2, 15, 6, "x", "dark_oak_stairs", "dark_oak_slab", "spruce_planks", overhang=1)
    # clinic cabin (gable to the street)
    logbox(3, 5, 11, 15, 5, "z")
    rg = d.gable(3, 5, 11, 15, 6, "z", "dark_oak_stairs", "dark_oak_slab", "stripped_spruce_log[axis=y]", overhang=1)
    d.clear(4, Y0, 6, 10, 5, 14)
    d.clear(12, Y0, 8, WX2 - 1, 5, 14)
    d.clear(11, Y0, 10, 11, 3, 12)
    d.door(11, Y0, 11, "east", "spruce")
    d.set(11, Y0, 10, log(lg, "z"))
    d.set(11, Y0 + 1, 10, log(lg, "z"))
    d.set(11, Y0, 12, log(lg, "z"))
    d.set(11, Y0 + 1, 12, log(lg, "z"))
    # porch on the street
    d.door(7, Y0, 5, "south", "spruce")
    d.fill(2, 1, 1, 12, 1, 4, "spruce_planks")
    for x in (2, 12):
        for y in range(Y0, 5):
            d.set(x, y, 1, log(lg))
    for x in range(1, 14):
        d.set(x, 5, 0, st("spruce_stairs", "south"))
        for z in range(1, 5):
            d.set(x, 5, z, slab("spruce_slab"))
    for x in range(3, 12):
        if x not in (6, 7, 8):
            d.set(x, Y0, 1, "spruce_fence")
    d.sign(7, 4, 4, "north", ["INFIRMARY", "+"], "spruce")
    d.set(5, 4, 3, "lantern[hanging=true,waterlogged=false]")
    d.set(9, 4, 3, "lantern[hanging=true,waterlogged=false]")
    if d.req["seats"]:
        d.chair(3, Y0, 2, "west", "spruce")
        d.chair(11, Y0, 2, "east", "spruce")
    # windows
    for x in (5, 9):
        d.window(x, 3, 5, x, 4, 5)
    d.window(3, 3, 9, 3, 4, 10)
    d.window(7, 7, 5, 7, 8, 5)
    # stone chimney with a stove (the furnace) on the west wall
    for y in range(Y0, rg + 2):
        d.set(2, y, 12, "cobblestone" if y % 3 else "mossy_cobblestone")
        d.set(2, y, 13, "cobblestone")
    for y in range(Y0, rg + 2):
        d.set(3, y, 12, "cobblestone")
    d.item(4, Y0, 12, "furnace", "east")
    d.set(4, Y0 + 1, 12, "cobblestone")
    # ---- clinic interior
    d.hut(4, Y0, 6)
    for x in (6, 7, 8):
        d.set(x, Y0, 9, slab("spruce_slab", "top"))
    d.chair(7, Y0, 10, "south", "spruce", sit=False)
    d.set(8, Y0 + 1, 9, "candle[candles=2,lit=false,waterlogged=false]")
    d.item(4, Y0, 14, "brewing_stand")
    d.item(5, Y0, 14, "water_cauldron[level=3]")
    if d.req["racks"]:
        d.rack(10, Y0, 6, "west")
    for i in range(need(d, "barrel")):
        d.item(10, Y0, 14 - i, "barrel", "west")
    d.rug(6, 12, 8, 13, Y0, ("green_carpet",), "plain")
    d.set(7, 5, 8, "lantern[hanging=true,waterlogged=false]")
    d.set(7, 5, 12, "lantern[hanging=true,waterlogged=false]")
    beams(d, 4, 10, 8, 12, 6, "stripped_spruce_log", every=4, axis="x")
    # ---- ward
    placed = ward_row(d, 13, WX2 - 1, 8, Y0, "north", "white", nb, curtain="white_wool")
    placed += ward_row(d, 13, WX2 - 1, 14, Y0, "south", "white", nb - placed, curtain="white_wool")
    for x in range(13, WX2, 2):
        d.window(x, 4, 7, x, 4, 7)
        d.window(x, 4, 15, x, 4, 15)
    beams(d, 12, WX2 - 1, 8, 14, 6, "stripped_spruce_log", every=4, axis="z")
    for x in range(12, WX2, 4):
        d.set(x, 5, 11, "lantern[hanging=true,waterlogged=false]")
    d.window(WX2, 3, 10, WX2, 4, 12)
    # ---- sleeping porch (L4+): screened deck along the ward's south side
    if L >= 4:
        d.fill(11, 1, 16, WX2 + 1, 1, 20, "spruce_planks")
        for x in range(11, WX2 + 2):
            d.set(x, 5, 21, st("spruce_stairs", "north"))
            for z in range(16, 21):
                d.set(x, 5, z, slab("spruce_slab"))
            d.set(x, Y0, 20, "spruce_fence" if x % 4 else log(lg))
            if x % 4 == 0:
                for y in range(Y0 + 1, 5):
                    d.set(x, y, 20, log(lg))
        d.door(15, Y0, 15, "south", "spruce")
        for x in (13, 17, 19):
            d.chair(x, Y0, 18, "north", "spruce", sit=False)
        d.set(21, Y0, 18, "spruce_slab[type=top,waterlogged=false]")
    if L >= 5:                                                       # herb garden
        for x in range(1, 10):
            for z in range(17, 25):
                d.set(x, 1, z, "farmland[moisture=7]" if (z % 2) else "coarse_dirt")
                if z % 2:
                    d.set(x, Y0, z, ("fern", "sweet_berry_bush[age=2]", "short_grass")[x % 3])
                if x in (1, 9) or z == 24:
                    d.set(x, Y0, z, "spruce_fence")
        d.set(5, Y0, 16, "spruce_fence_gate[facing=south,in_wall=false,open=false,powered=false]") if False else None
    return d


@design("hospital")
def hospital(pack, rel, L):
    return {"Hearthwood": hospital_hearthwood, "Cascadia": hospital_cascadia,
            "Neoterra": hospital_neoterra}[pack](rel, L)


# ============================================================================================ LIBRARY
"""
Library.
  Hearthwood  Oxford college library: tall stone hall with lancet windows, buttresses, steep tiled roof and a
              rose window over the door. Inside, the "stall system": bookcases run out from both long walls
              between the windows, each window bay has a reading desk; carpet runner down the middle, librarian's
              lectern on a dais at the far end. Grows longer every level; L4+ enchanting alcove, L5 knot garden.
  Neoterra    glass-cube library: double-height glazed reading atrium on the street, freestanding stack rows behind,
              a mezzanine of stacks from L4, roof reading terrace at L5.
  Cascadia    A-frame reading lodge: the roof comes down to the ground, bookshelves fill the low eaves on both sides,
              fully glazed log-framed gable to the street, stone hearth at the back; grows deeper, L5 front deck.
"""


def shelf_runs(d, runs, target):
    """Place whole bookshelf runs (x1, z1, x2, z2, y, h) in order until `target` shelves are placed."""
    for r in runs:
        if d.placed["bookshelves"] >= target:
            break
        shelves(d, *r)


def library_hearthwood(rel, L):
    d = Design("Hearthwood", rel, (23, 26, 31), gy=1)
    S = "stone_bricks"
    Z1, Z2 = 6, {1: 15, 2: 19, 3: 23, 4: 27, 5: 27}[L]
    X1, X2 = 4, 18
    d.box(X1, Y0, Z1, X2, 9, Z2, S, floor="spruce_planks")
    for x in range(X1, X2 + 1):
        for z in range(Z1, Z2 + 1):
            if x in (X1, X2) or z in (Z1, Z2):
                d.set(x, Y0, z, "polished_andesite")
                d.set(x, 9, z, "chiseled_stone_bricks" if (x + z) % 4 == 0 else S)
    ridge = d.gable(X1, Z1, X2, Z2, 10, "z", "deepslate_tile_stairs", "deepslate_tile_slab", S, overhang=1)
    beams(d, X1 + 1, X2 - 1, Z1 + 2, Z2 - 2, 10, "stripped_dark_oak_log", every=4, axis="x")
    for z in range(Z1 + 2, Z2 - 1, 4):
        d.set(11, 9, z, "chain[axis=y,waterlogged=false]")
        d.set(11, 8, z, "lantern[hanging=true,waterlogged=false]")
    # stalls between lancet windows, buttresses outside
    stall_z = list(range(Z1 + 2, Z2 - 2, 4))
    h = 3 if L <= 3 else 4
    seats = 0
    for z in stall_z:
        for x in (X1 - 1, X2 + 1):
            for y in range(Y0, 7):
                d.set(x, y, z, S)
            d.set(x, 7, z, st("stone_brick_stairs", "east" if x < X1 else "west"))
        bay = [zz for zz in (z + 1, z + 2, z + 3) if zz < Z2 - 1]
        if len(bay) == 3:
            for x in (X1, X2):
                d.window(x, 4, z + 1, x, 7, z + 3)
                for zz in (z + 1, z + 3):
                    d.set(x, 4, zz, S)
                    d.set(x, 7, zz, S)
                d.set(x, 8, z + 2, "glass_pane")
            for x, cx, back in ((X1 + 1, X1 + 2, "east"), (X2 - 1, X2 - 2, "west")):
                for zz in bay:
                    d.set(x, Y0, zz, slab("dark_oak_slab", "top"))
                    d.chair(cx, Y0, zz, back, "dark_oak")
                    seats += 1
                d.set(x, Y0 + 1, z + 2, "candle[candles=3,lit=false,waterlogged=false]")
    runs = []
    for z in stall_z:
        runs.append((X1 + 1, z, X1 + 3, z, Y0, h))
        runs.append((X2 - 3, z, X2 - 1, z, Y0, h))
    runs.append((X1 + 1, Z2 - 1, 9, Z2 - 1, Y0, 4))
    runs.append((13, Z2 - 1, X2 - 1, Z2 - 1, Y0, 4))
    shelf_runs(d, runs, d.req["bookshelves"])
    # entrance with pointed arch and rose window
    d.double_door(10, Y0, Z1, "x", "south", "dark_oak") if False else d.door(11, Y0, Z1, "south", "dark_oak")
    d.set(10, 4, Z1, st("stone_brick_stairs", "west", "top"))
    d.set(12, 4, Z1, st("stone_brick_stairs", "east", "top"))
    for x, y in ((11, 11), (10, 12), (11, 12), (12, 12), (9, 13), (11, 13), (13, 13), (10, 14), (11, 14),
                 (12, 14), (11, 15), (10, 13), (12, 13)):
        d.set(x, y, Z1, "glass_pane" if (x, y) != (11, 13) else "light_blue_stained_glass")
    d.window(8, 4, Z1, 8, 7, Z1)
    d.window(14, 4, Z1, 14, 7, Z1)
    d.sign(11, 5, Z1 - 1, "north", ["LIBRARY", "", "Sapere aude"], "dark_oak")
    d.hut(9, Y0, Z1 + 1)
    d.fill(10, 1, 0, 12, 1, Z1 - 1, "stone_bricks")
    # nave: carpet runner, central reading table
    d.rug(10, Z1 + 1, 12, Z2 - 3, Y0, ("red_carpet",), "plain")
    for z in range(Z1 + 3, Z2 - 3, 2):
        pass
    if d.req["seats"] > seats:
        for z in range(Z1 + 3, Z1 + 3 + (d.req["seats"] - seats + 1) // 2):
            d.table(11, Y0, z, "dark_oak", "block", "dark_oak_planks")
            d.chair(10, Y0, z, "west", "dark_oak")
            d.chair(12, Y0, z, "east", "dark_oak")
    # dais with the librarian's lectern; enchanting alcove from L4
    for x in range(10, 13):
        d.set(x, Y0, Z2 - 2, slab("dark_oak_slab", "top") if x != 11 else "dark_oak_planks")
    d.item(11, Y0, Z2 - 2, "lectern", "north")
    d.set(11, Y0, Z2 - 1, AIR)
    if L >= 4:
        d.item(11, Y0, Z2 - 1, "enchanting_table")
        d.set(11, Y0, Z2 - 2, AIR)
        d.item(11, Y0, Z2 - 3, "lectern", "south") if False else None
        d.placed["items"]["minecraft:lectern"] -= 1
        d.set(10, Y0, Z2 - 2, AIR)
        d.set(12, Y0, Z2 - 2, AIR)
        d.item(10, Y0, Z2 - 3, "lectern", "north") if False else d.item(12, Y0, Z2 - 2, "lectern", "west")
        d.window(11, 4, Z2, 11, 8, Z2, "purple_stained_glass_pane")
    else:
        d.window(11, 4, Z2, 11, 8, Z2, "glass_pane")
    # L5: knot garden in front
    if L >= 5:
        for x in range(1, 22):
            for z in range(1, 5):
                if x in range(10, 13):
                    continue
                d.set(x, 1, z, "grass_block[snowy=false]")
                if x in (1, 9, 13, 21) or z in (1, 4):
                    d.set(x, Y0, z, "oak_leaves[distance=1,persistent=true,waterlogged=false]")
                elif (x + z) % 3 == 0:
                    d.set(x, Y0, z, "rose_bush[half=lower]")
                    d.set(x, Y0 + 1, z, "rose_bush[half=upper]")
        for x in (10, 12):
            d.set(x, Y0, 1, "stone_brick_wall")
            d.set(x, Y0 + 1, 1, "lantern[hanging=false,waterlogged=false]")
    return d


def library_neoterra(rel, L):
    d = Design("Neoterra", rel, (25, 22, 25), gy=1, paving="smooth_stone")
    W, G = "white_concrete", "light_gray_concrete"
    big = L >= 3
    X1, X2, Z1, Z2 = (3, 21, 4, 20) if big else (3, 13, 4, 14)
    top = 10
    d.box(X1, Y0, Z1, X2, top, Z2, W, floor="polished_diorite")
    d.flat(X1, Z1, X2, Z2, top + 1, "smooth_quartz", W, "smooth_quartz_slab")
    # full-height glazed street front and east side of the atrium, ribbon windows elsewhere
    for x in range(X1 + 1, X2):
        if (x - X1) % 4:
            d.window(x, Y0, Z1, x, top - 1, Z1, "glass_pane")
    for z in range(Z1 + 1, Z2):
        if (z - Z1) % 4:
            d.window(X2, Y0, z, X2, top - 1, z, "glass_pane")
            d.window(X1, Y0 + 1, z, X1, top - 1, z, "glass_pane")
    for x in range(X1 - 1, X2 + 2):                                 # cantilevered roof edge
        for z in (Z1 - 1, Z2 + 1):
            d.set(x, top, z, slab("smooth_quartz_slab", "top"))
    for z in range(Z1, Z2 + 1):
        for x in (X1 - 1, X2 + 1):
            d.set(x, top, z, slab("smooth_quartz_slab", "top"))
    for x in range(X1, X2 + 1):
        d.set(x, top, Z1, "cyan_terracotta")
    for z in range(Z1, Z2 + 1):
        d.set(X1, top, z, "cyan_terracotta")
        d.set(X2, top, z, "cyan_terracotta")
    mid = 8
    d.double_door(mid, Y0, Z1, "x", "south", "birch")
    d.sign(mid, top - 1 if False else 6, Z1 - 1, "north", ["PUBLIC", "LIBRARY"], "birch", glow=True, color="cyan")
    d.sign(mid + 1, 6, Z1 - 1, "north", ["", "open late"], "birch", glow=True, color="cyan")
    for x in range(mid - 2, mid + 4):
        for z in (Z1 - 1, Z1 - 2):
            d.set(x, 5, z, slab("smooth_quartz_slab", "top"))
    d.hut(X1 + 1, Y0, Z1 + 1)
    # circulation desk + lectern
    for x in range(mid + 2, mid + 5):
        d.set(x, Y0, Z1 + 4, "smooth_quartz")
    d.item(mid + 3, Y0, Z1 + 5, "lectern", "north") if False else d.item(mid + 2, Y0, Z1 + 3, "lectern", "north")
    d.chair(mid + 3, Y0, Z1 + 5, "south", "mangrove", sit=False)
    # reading tables in the atrium (north)
    seats = 0
    need_s = d.req["seats"]
    for tx in (X1 + 2, X1 + 3):
        pass
    for tz in (Z1 + 3,):
        for tx in range(X1 + 2, X1 + 2 + 2):
            d.table(tx, Y0, tz, "birch", "block", "smooth_quartz")
        for tx in range(X1 + 2, X1 + 4):
            d.chair(tx, Y0, tz - 1, "north", "mangrove")
            d.chair(tx, Y0, tz + 1, "south", "mangrove")
            seats += 2
        d.chair(X1 + 4, Y0, tz, "east", "mangrove")
        d.chair(X1 + 1, Y0, tz, "west", "mangrove")
        seats += 2
    d.plant(X1 + 1, Y0, Z1 + 5, "potted_bamboo")
    # stacks: rows along x behind the atrium (3 high), aisles 2 wide
    if big:
        g = [(X1 + 2, z, X2 - 3, z, Y0, 3) for z in (11, 12, 15, 16)]
        if L >= 4:
            m = [(X1 + 1, z, X2 - 4, z, 7, 2) for z in (13, 14, 17, 18)]
            runs = [g[0], m[0], m[1], g[1], m[2], m[3], g[2], g[3]]
        else:
            runs = g
        runs.append((X1 + 1, Z2 - 1, X2 - 3, Z2 - 1, Y0, 3))
        # more reading tables along the glass on the east side
        for tz in (Z1 + 2, Z1 + 5):
            if seats >= need_s:
                break
            for tx in (X2 - 4, X2 - 3):
                d.table(tx, Y0, tz, "birch", "block", "smooth_quartz")
                d.chair(tx, Y0, tz - 1, "north", "mangrove")
                d.chair(tx, Y0, tz + 1, "south", "mangrove")
                seats += 2
    else:
        runs = [(X1 + 1, Z2 - 1, X2 - 1, Z2 - 1, Y0, 3), (X2 - 1, Z1 + 7, X2 - 1, Z2 - 2, Y0, 3),
                (X1 + 1, Z1 + 8, X2 - 4, Z1 + 8, Y0, 3)]
    for x in range(X1 + 2, X2 - 1, 3):
        d.set(x, top, Z1 + 3, "sea_lantern")
    # mezzanine (L4+): floor over the stacks, glass balustrade, stairs along the east wall
    if L >= 4:
        d.fill(X1 + 1, 6, 10, X2 - 1, 6, Z2 - 1, G)
        rail(d, X1 + 1, 10, X2 - 2, 10, 7, "glass_pane")
        for z in range(10, Z2):
            for y in range(Y0, 6):
                if (X2 - 1, y, z) and d.get(X2 - 1, y, z).endswith("bookshelf"):
                    d.set(X2 - 1, y, z, AIR)
        flight(d, X2 - 1, Z2 - 1, Y0, 7, "north", "smooth_quartz_stairs", under="smooth_quartz")
        rail(d, X2 - 2, Z2 - 5, X2 - 2, Z2 - 2, 7, "glass_pane")
        d.item(X1 + 3, 7, Z2 - 1, "enchanting_table")
        d.chair(X1 + 3, 7, Z2 - 2, "north", "mangrove", sit=False) if False else None
        for x in range(X1 + 2, X2 - 1, 4):
            d.set(x, 5, 13, "sea_lantern")
            d.set(x, 10, 15, "sea_lantern")
    shelf_runs(d, runs, d.req["bookshelves"])
    if L >= 4:
        # reading lounge on the mezzanine front edge
        for x in range(X1 + 2, X1 + 2 + max(0, need_s - seats)):
            d.chair(x, 7, 11, "south", "mangrove")
            seats += 1
    # roof terrace (L5): planters and benches reached by a ladder
    if L >= 5:
        ry = top + 2
        for x in range(X1 + 1, X2):
            for z in (Z1 + 1, Z2 - 1):
                d.set(x, ry, z, "moss_block" if x % 3 else "flowering_azalea")
        for z in range(Z1 + 3, Z2 - 2, 3):
            bench(d, X1 + 4, z, X1 + 7, z, ry, "north", "birch", tag=None)
        for y in range(7, ry):
            d.set(X1 + 1, y, Z2 - 2, "ladder[facing=east,waterlogged=false]")
        d.set(X1 + 1, top + 1, Z2 - 2, "ladder[facing=east,waterlogged=false]")
    return d


def library_cascadia(rel, L):
    d = Design("Cascadia", rel, (25, 16, 31), gy=1, paving="coarse_dirt")
    X1, X2 = 3, 21
    Z1, Z2 = 5, {1: 13, 2: 17, 3: 21, 4: 25, 5: 25}[L]
    d.fill(X1, 1, Z1, X2, 1, Z2, "spruce_planks")
    ridge = d.gable(X1, Z1, X2, Z2, Y0, "z", "dark_oak_stairs", "dark_oak_slab", "spruce_planks", overhang=1)
    # glazed street gable with a log frame and the door
    for x in range(X1 + 1, X2):
        for y in range(Y0, ridge):
            if d.get(x, y, Z1) == "minecraft:spruce_planks":
                d.set(x, y, Z1, "glass_pane" if x % 3 else log("spruce_log"))
    for x in range(X1 + 1, X2):
        if d.get(x, 6, Z1) in ("minecraft:glass_pane", "minecraft:spruce_log[axis=y]"):
            d.set(x, 6, Z1, log("spruce_log", "x"))
    d.double_door(11, Y0, Z1, "x", "south", "spruce")
    d.set(12, Y0 + 2, Z1, log("spruce_log", "x"))
    d.set(11, Y0 + 2, Z1, log("spruce_log", "x"))
    d.sign(12, 4, Z1 - 1, "north", ["READING", "LODGE"], "spruce") if False else \
        d.sign(12, 7, Z1 - 1, "north", ["READING", "LODGE"], "spruce")
    # back gable: planks with the river-rock chimney
    for y in range(Y0, ridge + 2):
        for x in (11, 12, 13):
            if y < ridge - 1 or x == 12:
                d.set(x, y, Z2, "cobblestone" if (x + y) % 3 else "mossy_cobblestone")
    d.hearth(12, Y0, Z2 - 1, "north", ridge + 1, "cobblestone", "campfire")
    d.set(12, Y0 + 1, Z2 - 1, AIR)
    d.set(12, Y0 + 2, Z2 - 1, "cobblestone")
    d.rug(11, Z2 - 4, 13, Z2 - 2, Y0, ("brown_carpet",), "plain")
    # stacks in the low eaves: 1/2/3 high wedges on both sides
    runs = []
    for z in range(Z1 + 1, Z2):
        runs.append((X1 + 1, z, X1 + 1, z, Y0, 1))
        runs.append((X1 + 2, z, X1 + 2, z, Y0, 2))
        runs.append((X1 + 3, z, X1 + 3, z, Y0, 3))
        runs.append((X2 - 1, z, X2 - 1, z, Y0, 1))
        runs.append((X2 - 2, z, X2 - 2, z, Y0, 2))
        runs.append((X2 - 3, z, X2 - 3, z, Y0, 3))
    d.hut(X1 + 4, Y0, Z1 + 1)
    d.item(X2 - 4, Y0, Z1 + 1, "lectern", "west")
    shelf_runs(d, runs, d.req["bookshelves"])
    # reading tables down the middle
    seats = 0
    z = Z1 + 3
    while seats < d.req["seats"] and z <= Z2 - 3:
        for tx in (9, 15):
            d.table(tx, Y0, z, "spruce", "post", "spruce_pressure_plate[powered=false]")
            d.chair(tx - 1, Y0, z, "west", "spruce")
            d.chair(tx + 1, Y0, z, "east", "spruce")
            seats += 2
        z += 2
    if L >= 4:
        d.item(12, Y0, Z2 - 5, "enchanting_table")
    # lights hanging from the collar ties
    for zz in range(Z1 + 2, Z2 - 1, 4):
        for x in range(X1 + 7, X2 - 6):
            d.set(x, 9, zz, log("stripped_spruce_log", "x"))
        d.set(12, 8, zz, "lantern[hanging=true,waterlogged=false]")
    # skylight dormers from L3
    if L >= 3:
        for zz in range(Z1 + 4, Z2 - 2, 6):
            for x in (X1 + 4, X2 - 4):
                d.set(x, 7 if False else 7, zz, "glass")
    # front deck (L5) with benches
    if L >= 5:
        d.fill(X1, 1, 0, X2, 1, Z1 - 1, "spruce_planks")
        for x in range(X1, X2 + 1):
            d.set(x, Y0, 0, "spruce_fence" if x not in (11, 12) else AIR)
        for z in range(1, Z1):
            d.set(X1, Y0, z, "spruce_fence")
            d.set(X2, Y0, z, "spruce_fence")
        bench(d, X1 + 2, 2, X1 + 5, 2, Y0, "south", "spruce", tag=None)
        bench(d, X2 - 5, 2, X2 - 2, 2, Y0, "south", "spruce", tag=None)
        for x in (X1, X2):
            d.set(x, Y0 + 1, 0, "lantern[hanging=false,waterlogged=false]")
    return d


@design("library")
def library(pack, rel, L):
    return {"Hearthwood": library_hearthwood, "Cascadia": library_cascadia, "Neoterra": library_neoterra}[pack](rel, L)


# ============================================================================================ SCHOOL
"""
School.
  Hearthwood  Cotswold village school: honey sandstone schoolroom with a steep tiled gable, tall windows, gabled
              entrance porch and a bell-cote on the west gable. Desks in rows facing the blackboard, teacher's
              desk in front, bookcase at the back. L3 art room wing (loom, map table, easels), L4 walled
              playground with hopscotch, L5 school garden.
  Neoterra    modern primary school: long single-storey pavilion, white with coloured fins and big windows, flat
              overhanging roof. Classroom first, art studio from L3, covered play court from L4, roof solar at L5.
  Cascadia    one-room log schoolhouse: gable to the street, porch, little belfry on the front ridge, stone
              chimney; craft-room lean-to from L3, swing set from L4, garden at L5.
"""


def school_hearthwood(rel, L):
    d = Design("Hearthwood", rel, (25, 20, 25), gy=1)
    SS, CS = "smooth_sandstone", "cut_sandstone"
    X1, X2, Z1, Z2 = 4, 18, 7, 15
    d.box(X1, Y0, Z1, X2, 6, Z2, SS, floor="oak_planks")
    for x in range(X1, X2 + 1):
        for z in range(Z1, Z2 + 1):
            if x in (X1, X2) or z in (Z1, Z2):
                d.set(x, Y0, z, CS)
    for x, z in ((X1, Z1), (X2, Z1), (X1, Z2), (X2, Z2)):
        for y in range(Y0, 7):
            d.set(x, y, z, CS)
    ridge = d.gable(X1, Z1, X2, Z2, 7, "x", "deepslate_tile_stairs", "deepslate_tile_slab", SS, overhang=1)
    beams(d, X1 + 2, X2 - 2, Z1 + 1, Z2 - 1, 7, "stripped_dark_oak_log", every=4)
    # tall windows (north & south), gable window east
    for x in (7, 10, 13):
        for z in (Z1, Z2):
            d.window(x, 3, z, x, 5, z)
            d.set(x, 6, z, CS)
    d.window(X2, 4, 10, X2, 5, 12)
    # bell-cote on the west gable
    d.set(X1, ridge + 1, 10, "sandstone_wall")
    d.set(X1, ridge + 1, 12, "sandstone_wall")
    d.set(X1, ridge + 1, 11, AIR)
    d.fill(X1, ridge + 2, 10, X1, ridge + 2, 12, slab("sandstone_slab"))
    d.set(X1, ridge + 2, 11, CS)
    bell(d, X1, ridge + 1, 11, "east")
    # entrance porch
    d.door(16, Y0, Z1, "south", "oak")
    for x in (15, 17):
        for y in range(Y0, 5):
            d.set(x, y, 4, "oak_fence" if y < 4 else "dark_oak_planks")
        for z in (5, 6):
            d.set(x, Y0, z, SS)
    d.fill(15, 5, 4, 17, 5, 6, "dark_oak_planks")
    d.gable(15, 4, 17, 6, 6, "z", "deepslate_tile_stairs", "deepslate_tile_slab", SS, overhang=0)
    d.fill(15, 1, 2, 17, 1, 6, CS)
    d.sign(16, 6, 3, "north", ["VILLAGE", "SCHOOL", "est. 1872"], "dark_oak")
    d.set(16, 4, 5, "lantern[hanging=true,waterlogged=false]")
    # ---- schoolroom
    d.hut(17, Y0, 8)
    blackboard(d, X1 + 1, 9, X1 + 1, 13, 3, "east")
    d.set(X1 + 3, Y0, 11, slab("dark_oak_slab", "top"))           # teacher's desk
    d.set(X1 + 3, Y0, 12, slab("dark_oak_slab", "top"))
    d.set(X1 + 3, Y0 + 1, 12, "candle[candles=1,lit=false,waterlogged=false]")
    d.spot(X1 + 2, Y0, 11, "work")
    d.chair(X1 + 2, Y0, 12, "west", "dark_oak", sit=False)
    d.set(X1 + 1, Y0, 9, "potted_red_tulip") if False else None
    desk_rows(d, 9, 14, Z1 + 1, Z2 - 1, Y0, "west", "oak", "oak_slab", every_x=3, need=d.req["seats"])
    shelf_runs(d, [(X2 - 1, 10, X2 - 1, 14, Y0, 1), (X2 - 1, 10, X2 - 1, 14, Y0 + 1, 1)], d.req["bookshelves"])
    for x in (7, 11, 15):
        d.set(x, 6, 11, "lantern[hanging=true,waterlogged=false]")
    for z in (8, 9):                                                 # coat pegs by the door
        pass
    # ---- art room wing (L3+)
    if L >= 3:
        d.box(10, Y0, Z2, 16, 6, 21, SS, floor="oak_planks")
        d.gable(10, Z2 + 1, 16, 21, 7, "z", "deepslate_tile_stairs", "deepslate_tile_slab", SS, overhang=1)
        d.clear(11, Y0, Z2 + 1, 15, 6, 20)
        d.door(13, Y0, Z2, "south", "oak")
        for x in (13,):
            d.window(x, 3, 21, x, 5, 21)
        d.window(16, 3, 17, 16, 4, 19)
        d.item(11, Y0, 17, "loom", "east")
        d.item(11, Y0, 19, "cartography_table")
        for x in (14, 15):                                          # easels
            d.set(x, Y0, 20, "spruce_fence")
            d.set(x, Y0 + 1, 20, "spruce_trapdoor[facing=north,half=bottom,open=true,powered=false,waterlogged=false]")
        d.table(14, Y0, 17, "oak", "slab")
        d.chair(15, Y0, 17, "east", "oak", sit=False)
        d.set(13, 6, 18, "lantern[hanging=true,waterlogged=false]")
        d.set(12, Y0, 20, "white_banner[rotation=0]") if False else None
    # ---- playground (L4+): low wall, hopscotch, tree; L5 school garden
    if L >= 4:
        for x in range(X2 + 1, 24):
            for z in range(3, 21):
                if x == 23 or z in (3, 20):
                    d.set(x, Y0, z, "sandstone_wall")
        hop = [(21, 6), (21, 7), (20, 8), (22, 8), (21, 9), (20, 10), (22, 10), (21, 11)]
        for x, z in hop:
            d.set(x, 1, z, "white_concrete" if (x + z) % 2 else "yellow_terracotta")
        d.set(21, 1, 16, "grass_block[snowy=false]")
        tree(d, 21, Y0, 16, "oak_log", "oak_leaves", 4, 2)
        d.set(X2, Y0, 11, AIR)
        d.door(X2, Y0, 9, "west", "oak") if False else None
    if L >= 5:
        for x in range(2, 10):
            for z in range(17, 23):
                if x in (2, 9) or z in (17, 22):
                    d.set(x, Y0, z, "oak_fence")
                else:
                    d.set(x, 1, z, "farmland[moisture=7]")
                    d.set(x, Y0, z, ("carrots[age=7]", "potatoes[age=7]", "beetroots[age=3]")[z % 3])
        d.set(5, Y0, 17, "oak_fence_gate[facing=north,in_wall=false,open=false,powered=false]")
        d.set(3, Y0, 16, "composter[level=4]")
    return d


def school_neoterra(rel, L):
    d = Design("Neoterra", rel, (29, 16, 23), gy=1, paving="smooth_stone")
    W = "white_concrete"
    fins = ("yellow_concrete", "lime_concrete", "cyan_concrete")
    X1, X2, Z1, Z2 = 3, 14, 5, 15
    EX2 = 22 if L >= 3 else X2

    def pavilion(x1, x2):
        d.box(x1, Y0, Z1, x2, 6, Z2, W, floor="polished_diorite")
        for x in range(x1 + 1, x2):
            if (x - x1) % 3:
                d.window(x, 3, Z1, x, 5, Z1, "glass_pane")
                d.window(x, 3, Z2, x, 5, Z2, "glass_pane")
            else:
                for y in range(Y0, 7):
                    d.set(x, y, Z1 - 1, fins[(x // 3) % 3])
        d.fill(x1 - 1, 7, Z1 - 2, x2 + 1, 7, Z2 + 1, "smooth_quartz")
        for x in range(x1 - 1, x2 + 2):
            d.set(x, 8, Z1 - 2, slab("smooth_quartz_slab"))
            d.set(x, 8, Z2 + 1, slab("smooth_quartz_slab"))
    pavilion(X1, X2)
    if L >= 3:
        pavilion(X2, EX2)
        d.clear(X2, Y0, 9, X2, 4, 10)
        d.set(X2, Y0, 9, AIR)
    d.double_door(9, Y0, Z1, "x", "south", "birch")
    d.sign(7, 7, Z1 - 3, "north", ["SUNRISE", "SCHOOL"], "birch", glow=True, color="yellow") if False else \
        d.sign(8, 6, Z1 - 2, "north", ["SUNRISE", "SCHOOL"], "birch", glow=True, color="yellow")
    for z in range(Z1 + 2, Z2 - 1, 3):
        d.window(X1, 3, z, X1, 5, z + 1, "glass_pane")
    # ---- classroom: board on the south wall, desks facing it
    d.hut(X1 + 1, Y0, Z1 + 1)
    blackboard(d, 6, Z2 - 1, 11, Z2 - 1, 3, "north", "gray_concrete", "birch")
    d.set(8, Y0, Z2 - 3, "smooth_quartz")
    d.set(9, Y0, Z2 - 3, "smooth_quartz")
    d.spot(8, Y0, Z2 - 2, "work")
    d.chair(9, Y0, Z2 - 2, "south", "birch", sit=False)
    desk_rows(d, X1 + 2, X2 - 2, Z1 + 1, Z2 - 4, Y0, "south", "birch", "smooth_quartz_slab", every_x=3,
              need=d.req["seats"])
    shelf_runs(d, [(X1 + 1, 9, X1 + 1, 13, Y0, 1), (X1 + 1, 9, X1 + 1, 13, Y0 + 1, 1)], d.req["bookshelves"])
    for x in (6, 10):
        for z in (8, 12):
            d.set(x, 6, z, "sea_lantern")
    # ---- art studio (L3+)
    if L >= 3:
        d.item(EX2 - 1, Y0, Z1 + 2, "loom", "west")
        d.item(EX2 - 1, Y0, Z1 + 4, "cartography_table")
        for x in (17, 19):
            d.set(x, Y0, Z2 - 1, "birch_fence")
            d.set(x, Y0 + 1, Z2 - 1, "birch_trapdoor[facing=north,half=bottom,open=true,powered=false,waterlogged=false]")
        for x in (17, 18, 19):
            d.set(x, Y0, 9, slab("smooth_quartz_slab", "top"))
            d.chair(x, Y0, 10, "south", "birch", sit=False)
        d.plant(EX2 - 1, Y0, Z2 - 1, "potted_bamboo")
        for x in (17, 20):
            d.set(x, 6, 10, "sea_lantern")
        d.set(EX2 - 1, Y0 + 1, 10, "light_blue_wall_banner[facing=west]")
    # ---- covered play court (L4+)
    if L >= 4:
        for x in range(X1, EX2 + 1):
            for z in range(Z2 + 2, 22):
                d.set(x, 1, z, "gray_concrete" if not (x in (X1, EX2) or z in (Z2 + 2, 21) or x == 12)
                      else "white_concrete")
        for x in (X1, EX2):
            for y in range(Y0, 7):
                d.set(x, y, 21, "light_gray_concrete")
        for x in range(X1, EX2 + 1):
            d.set(x, 7, 21, "smooth_quartz")
            for z in range(Z2 + 2, 21):
                d.set(x, 7, z, slab("smooth_quartz_slab", "top")) if (x + z) % 2 == 0 or True else None
        for x in (X1 + 1, EX2 - 1):                                 # hoops
            d.set(x, Y0, 18, "iron_bars")
            d.set(x, Y0 + 1, 18, "iron_bars")
            d.set(x, Y0 + 2, 18, "white_stained_glass")
            d.set(x + (1 if x == X1 + 1 else -1), Y0 + 2, 18, "orange_stained_glass_pane") if False else None
        d.door(9, Y0, Z2, "north", "birch")
    if L >= 5:
        for x in range(X1 + 1, EX2, 2):
            for z in range(Z1 + 1, Z2 - 1):
                d.set(x, 8, z, "daylight_detector[inverted=false,power=0]")
        for z in range(Z1, Z2 + 1, 3):
            d.set(26, 1, z, "grass_block[snowy=false]")
            d.set(26, Y0, z, "flowering_azalea")
    return d


def school_cascadia(rel, L):
    d = Design("Cascadia", rel, (25, 22, 27), gy=1, paving="coarse_dirt")
    lg = "spruce_log"
    X1, X2, Z1, Z2 = 6, 16, 7, 19
    d.box(X1, Y0, Z1, X2, 6, Z2, log("stripped_spruce_log", "z"), floor="spruce_planks")
    for x in range(X1, X2 + 1):
        for y in range(Y0, 7):
            d.set(x, y, Z1, log("stripped_spruce_log", "x"))
            d.set(x, y, Z2, log("stripped_spruce_log", "x"))
    for x in range(X1, X2 + 1):
        for z in range(Z1, Z2 + 1):
            if x in (X1, X2) or z in (Z1, Z2):
                d.set(x, Y0, z, "cobblestone" if (x + z) % 3 else "mossy_cobblestone")
    for x, z in ((X1, Z1), (X2, Z1), (X1, Z2), (X2, Z2)):
        for y in range(Y0, 7):
            d.set(x, y, z, log(lg))
    ridge = d.gable(X1, Z1, X2, Z2, 7, "z", "dark_oak_stairs", "dark_oak_slab", "spruce_planks", overhang=1)
    beams(d, X1 + 1, X2 - 1, Z1 + 2, Z2 - 2, 7, "spruce_log", every=4, axis="x")
    mid = 11
    # belfry on the front ridge
    for x in range(mid - 1, mid + 2):
        for z in range(Z1, Z1 + 3):
            d.set(x, ridge, z, "spruce_planks")
    for x, z in ((mid - 1, Z1), (mid + 1, Z1), (mid - 1, Z1 + 2), (mid + 1, Z1 + 2)):
        for y in range(ridge + 1, ridge + 3):
            d.set(x, y, z, "spruce_fence")
    d.hip(mid - 1, Z1, mid + 1, Z1 + 2, ridge + 3, "spruce_stairs", "spruce_slab", overhang=1)
    d.set(mid, ridge + 3, Z1 + 1, "spruce_planks")
    bell(d, mid, ridge + 2, Z1 + 1)
    # porch
    d.door(mid, Y0, Z1, "south", "spruce")
    d.fill(X1, 1, Z1 - 3, X2, 1, Z1 - 1, "spruce_planks")
    for x in (X1, X2):
        for y in range(Y0, 6):
            d.set(x, y, Z1 - 3, log(lg))
    for x in range(X1 - 1, X2 + 2):
        d.set(x, 6, Z1 - 4, st("spruce_stairs", "south"))
        for z in range(Z1 - 3, Z1):
            d.set(x, 6, z, slab("spruce_slab"))
    for x in range(X1 + 1, X2):
        if abs(x - mid) > 1:
            d.set(x, Y0, Z1 - 3, "spruce_fence")
    d.sign(mid, 5, Z1 - 1, "north", ["SCHOOL", "DIST. No. 7"], "spruce")
    for x in (8, 14):
        d.window(x, 3, Z1, x, 4, Z1)
    for z in (10, 13, 16):
        d.window(X1, 3, z, X1, 5, z)
        d.window(X2, 3, z, X2, 5, z)
    # stone chimney on the back gable with a stove
    for y in range(Y0, ridge):
        d.set(mid, y, Z2 + 1, "cobblestone" if y % 3 else "mossy_cobblestone")
    d.set(mid, ridge, Z2 + 1, "cobblestone_wall")
    # ---- schoolroom: board on the back wall
    d.hut(X1 + 1, Y0, Z1 + 1)
    blackboard(d, 9, Z2 - 1, 13, Z2 - 1, 3, "north", "black_concrete", "spruce")
    d.set(10, Y0, Z2 - 3, slab("spruce_slab", "top"))
    d.set(11, Y0, Z2 - 3, slab("spruce_slab", "top"))
    d.set(10, Y0 + 1, Z2 - 3, "candle[candles=1,lit=false,waterlogged=false]")
    d.spot(11, Y0, Z2 - 2, "work")
    d.chair(10, Y0, Z2 - 2, "south", "spruce", sit=False)
    desk_rows(d, X1 + 2, X2 - 2, Z1 + 2, Z2 - 4, Y0, "south", "spruce", "spruce_slab", every_x=3,
              need=d.req["seats"])
    shelf_runs(d, [(X1 + 1, Z2 - 4, X1 + 1, Z2 - 1, Y0, 1), (X1 + 1, Z2 - 4, X1 + 1, Z2 - 1, Y0 + 1, 1)],
               d.req["bookshelves"])
    for x in (X2 - 1,):
        for z in (Z1 + 1, Z1 + 2):
            d.set(x, Y0 + 1, z, "spruce_fence")                    # coat pegs
    d.set(X2 - 1, Y0, Z2 - 1, "water_cauldron[level=3]") if False else d.set(X2 - 1, Y0, Z2 - 1, "barrel[facing=up,open=false]") if False else None
    for z in (11, 15):
        d.set(mid, 6, z, "lantern[hanging=true,waterlogged=false]")
    # ---- craft lean-to (L3+)
    if L >= 3:
        d.box(X2, Y0, 10, 21, 5, 16, log("stripped_spruce_log", "z"), floor="spruce_planks")
        for x in range(X2, 22):
            for y in range(Y0, 6):
                d.set(x, y, 10, log("stripped_spruce_log", "x"))
                d.set(x, y, 16, log("stripped_spruce_log", "x"))
        for z in range(9, 18):
            for x in range(X2 + 1, 23):
                d.set(x, 6, z, slab("spruce_slab"))
        d.clear(X2, Y0, 12, X2, Y0 + 1, 12)
        d.set(X2, Y0, 12, AIR)
        d.door(X2, Y0, 12, "east", "spruce")
        d.item(20, Y0, 11, "loom", "west")
        d.item(20, Y0, 15, "cartography_table")
        d.set(20, Y0, 13, "crafting_table") if False else d.set(20, Y0, 13, slab("spruce_slab", "top"))
        d.window(21, 3, 12, 21, 4, 14)
        d.set(18, 5, 13, "lantern[hanging=true,waterlogged=false]")
        d.set(18, Y0, 15, "spruce_fence")
        d.set(18, Y0 + 1, 15, "spruce_trapdoor[facing=north,half=bottom,open=true,powered=false,waterlogged=false]")
    # ---- swing set (L4+), garden (L5)
    if L >= 4:
        for z in (22, 25):
            for y in range(Y0, 6):
                d.set(4, y, z, log(lg))
        for z in range(22, 26):
            d.set(4, 6, z, log(lg, "z"))
        for z in (23, 24):
            for y in (4, 5):
                d.set(4, y, z, "chain[axis=y,waterlogged=false]")
            d.set(4, 3, z, slab("spruce_slab", "top"))
        d.set(8, 1, 23, "sand")
        d.set(9, 1, 23, "sand")
        d.set(8, 1, 24, "sand")
        d.set(9, 1, 24, "sand")
    if L >= 5:
        for x in range(13, 23):
            for z in range(20, 26):
                if x in (13, 22) or z in (20, 25):
                    d.set(x, Y0, z, "spruce_fence")
                else:
                    d.set(x, 1, z, "farmland[moisture=7]")
                    d.set(x, Y0, z, ("carrots[age=7]", "potatoes[age=7]", "wheat[age=7]")[x % 3])
        d.set(17, Y0, 20, "spruce_fence_gate[facing=north,in_wall=false,open=false,powered=false]")
        for x in range(1, 4):
            for y in (Y0, Y0 + 1):
                d.set(x, y, 9, log("spruce_log", "z"))                  # woodpile
    return d


@design("school")
def school(pack, rel, L):
    return {"Hearthwood": school_hearthwood, "Cascadia": school_cascadia, "Neoterra": school_neoterra}[pack](rel, L)


# ============================================================================================ UNIVERSITY
"""
University.
  Hearthwood  Oxford college: battlemented stone ranges round a grass quad, entered through a gate tower.
              L1 gate tower + senior common room (study: lectern, shelves, fireplace, supply rack); L2 the
              alchemy laboratory on the other side of the gate; L3 the lecture hall closes the quad (benches facing
              the lectern) with cloister walks and the quad lawn for strolling (leisure spots); L4 the college
              library range; L5 fountain and fellows' garden details.
  Neoterra    research campus: faculty pavilion + glass bridge + lab block on the street, a raked lecture
              theatre at the back from L3 and a green quad with trees and benches between.
  Cascadia    timber college: log lodges round a quad joined by covered boardwalks, a campfire ring in the quad,
              lecture lodge with benches, chemistry cabin, reading cabin.
"""


def crenel(d, x1, z1, x2, z2, ytop, wall="stone_bricks", floor="oak_planks", merlon="stone_bricks"):
    d.box(x1, Y0, z1, x2, ytop, z2, wall, floor=floor)
    d.fill(x1, ytop + 1, z1, x2, ytop + 1, z2, wall)
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if x in (x1, x2) or z in (z1, z2):
                d.set(x, ytop + 2, z, merlon if (x + z) % 2 == 0 else slab("stone_brick_slab"))
                d.set(x, Y0, z, "polished_andesite")


def university_hearthwood(rel, L):
    d = Design("Hearthwood", rel, (31, 24, 31), gy=1)
    S = "stone_bricks"
    # ---- north range: west half (L1+), east half (L2+), gate tower
    crenel(d, 4, 4, 13, 10, 6)
    if L >= 2:
        crenel(d, 17, 4, 26, 10, 6)
    crenel(d, 13, 3, 17, 11, 11, floor="stone_bricks")
    d.clear(14, Y0, 3, 16, 5, 11)                                   # gate passage
    d.fill(14, 1, 0, 16, 1, 11, "stone_bricks")
    for z in (3, 11):
        d.set(14, 5, z, st("stone_brick_stairs", "west", "top"))
        d.set(16, 5, z, st("stone_brick_stairs", "east", "top"))
    d.fill(14, 6, 4, 16, 6, 10, S)
    for x, z in ((13, 3), (17, 3)):                                 # corner turrets
        for y in range(12, 16):
            d.set(x, y, z, S if y < 15 else "stone_brick_wall")
    d.window(15, 8, 3, 15, 9, 3)
    d.sign(15, 7, 2, "north", ["COLLEGIUM", "", "MDCCXII"], "dark_oak")
    d.banner(14, 9, 2, "north", "blue")
    d.banner(16, 9, 2, "north", "blue")
    d.door(13, Y0, 7, "west", "dark_oak")
    for x in range(6, 13, 3):
        d.window(x, 3, 4, x, 5, 4)
        d.window(x, 3, 10, x, 5, 10)
    # ---- senior common room / study (west): fireplace, shelves, lectern, rack
    d.hut(12, Y0, 5)
    d.hearth(8, Y0, 9, "north", 9, "bricks", "campfire")
    if L == 1:
        d.chair(7, Y0, 7, "north", "dark_oak", arms=True)
        d.chair(9, Y0, 7, "north", "dark_oak", arms=True)
    d.rug(7, 6, 9, 8, Y0, ("red_carpet",), "plain") if False else None
    d.item(12, Y0, 9, "lectern", "west")
    d.rack(12, Y0, 8, "west")
    d.item(5, Y0, 5, "furnace", "east") if L == 1 else d.set(5, Y0, 5, "dark_oak_slab[type=top,waterlogged=false]")
    runs = [(5, 6, 5, 8, Y0, 3), (6, 9, 6, 9, Y0, 3), (10, 9, 11, 9, Y0, 3)]
    # ---- laboratory (east, L2+)
    if L >= 2:
        d.door(17, Y0, 7, "east", "dark_oak")
        for x in range(19, 26, 3):
            d.window(x, 3, 4, x, 5, 4)
            d.window(x, 3, 10, x, 5, 10)
        d.item(25, Y0, 5, "brewing_stand")
        d.item(25, Y0, 6, "water_cauldron[level=3]")
        d.item(25, Y0, 7, "crafting_table")
        for i in range(max(1, need(d, "furnace"))):
            d.item(25, Y0, 8 + i, "furnace", "west") if i < 2 else d.item(24, Y0, 9, "furnace", "north")
        for x in (20, 21, 22):                                      # lab bench with flasks
            d.set(x, Y0, 7, slab("stone_brick_slab", "top"))
        d.set(20, Y0 + 1, 7, "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]")
        d.set(22, Y0 + 1, 7, "flower_pot")
        d.chair(21, Y0, 8, "south", "dark_oak", sit=False)
        d.set(18, Y0, 9, "cauldron")
        d.set(21, 6, 6, "lantern[hanging=true,waterlogged=false]")
        # study table in the common room for the L2 seats
        d.dining(7, Y0, 6, 4, "x", "dark_oak", ("n", "s", "e", "w"))
        runs.append((19, 5, 23, 5, Y0, 3))
    d.set(8, 6, 7, "lantern[hanging=true,waterlogged=false]")
    # ---- quad, cloisters, lecture hall (L3+)
    if L >= 3:
        d.box(4, Y0, 20, 26, 7, 26, S, floor="oak_planks")       # great hall: steep roof with a louvre
        for x in range(4, 27):
            for z in (20, 26):
                d.set(x, Y0, z, "polished_andesite")
        hr = d.gable(4, 20, 26, 26, 8, "x", "deepslate_tile_stairs", "deepslate_tile_slab", S, overhang=1)
        for x in (14, 15, 16):
            for z in (22, 23, 24):
                d.set(x, hr, z, "dark_oak_planks")
        for x, z in ((14, 22), (16, 22), (14, 24), (16, 24)):
            d.set(x, hr + 1, z, "dark_oak_fence")
        d.hip(14, 22, 16, 24, hr + 2, "deepslate_tile_stairs", "deepslate_tile_slab", overhang=0)
        d.set(15, hr + 1, 23, "lantern[hanging=false,waterlogged=false]")
        for x in range(6, 26, 3):
            d.window(x, 3, 26, x, 6, 26)
        for x in range(6, 26, 4):
            if x != 14:
                d.window(x, 3, 20, x, 6, 20)
        d.double_door(15, Y0, 20, "x", "north", "dark_oak")
        # lecture hall: lectern at the west end, benches facing it
        d.item(6, Y0, 23, "lectern", "east") if need(d, "lectern") > 1 else d.set(6, Y0, 23, "dark_oak_planks")
        d.set(6, Y0, 22, slab("dark_oak_slab", "top"))
        d.set(6, Y0, 24, slab("dark_oak_slab", "top"))
        d.spot(5, Y0, 23, "work") if False else None
        for x in range(9, 22, 2):
            for z in (21, 22, 24, 25):
                if d.placed["seats"] < d.req["seats"] + 2:
                    d.chair(x, Y0, z, "east", "dark_oak")
        blackboard(d, 5, 22, 5, 24, 3, "east")
        for x in range(9, 25, 5):
            d.set(x, 7, 23, "lantern[hanging=true,waterlogged=false]")
        runs.append((25, 21, 25, 25, Y0, 3))
        runs.append((23, 21, 24, 21, Y0, 3))
        runs.append((23, 25, 24, 25, Y0, 3))
        # cloister walks on the quad's west and east sides
        for x0, xin in ((10, 11), (20, 19)):
            d.fill(min(x0, xin) - 1 if x0 == 10 else x0, 1, 11, max(x0, xin) + 1 if x0 == 20 else x0, 1, 19,
                   "stone_bricks") if False else None
            for z in range(11, 20):
                d.set(x0, 1, z, "stone_bricks")
                d.set(x0 + (-1 if x0 == 10 else 1), 1, z, "stone_bricks")
                if z % 2 == 1:
                    for y in range(Y0, 6):
                        d.set(xin, y, z, "stone_brick_wall" if y < 5 else S)
                else:
                    d.set(xin, 5, z, st("stone_brick_stairs", "north", "top"))
                d.set(xin, 6, z, slab("deepslate_tile_slab"))
                d.set(x0, 6, z, slab("deepslate_tile_slab"))
                d.set(x0 + (-1 if x0 == 10 else 1), 6, z, slab("deepslate_tile_slab"))
                d.set(x0 + (-2 if x0 == 10 else 2), 6, z, slab("deepslate_tile_slab"))
        # the quad lawn with cross paths; leisure spots where students stroll
        for x in range(12, 19):
            for z in range(11, 20):
                d.set(x, 1, z, "grass_block[snowy=false]")
        for x in range(12, 19):
            d.set(x, 1, 15, "gravel")
        for z in range(11, 20):
            d.set(15, 1, z, "gravel")
        for x, z in ((13, 15), (17, 15), (15, 12), (15, 18), (12, 15), (18, 15), (15, 11), (15, 19)):
            d.spot(x, Y0, z, "leisure")
        for x, z in ((12, 12), (18, 12), (12, 18), (18, 18)):
            d.set(x, Y0, z, "potted_azure_bluet") if False else d.set(x, Y0, z, "rose_bush[half=lower]")
            d.set(x, Y0 + 1, z, "rose_bush[half=upper]")
    # ---- library range (L4+) on the west side of the quad
    if L >= 4:
        crenel(d, 4, 10, 9, 19, 6)
        d.set(9, Y0, 15, AIR)
        d.door(9, Y0, 15, "east", "dark_oak")
        d.set(9, 4, 15, S)
        runs += [(5, 11, 5, 18, Y0, 3), (6, 11, 8, 11, Y0, 3), (6, 18, 8, 18, Y0, 3)]
        d.set(7, 6, 15, "lantern[hanging=true,waterlogged=false]")
        d.set(7, Y0, 15, "dark_oak_slab[type=top,waterlogged=false]")
        d.set(7, Y0 + 1, 15, "candle[candles=3,lit=false,waterlogged=false]")
        for z in (13, 17):
            d.window(4, 3, z, 4, 5, z)
    if L >= 5:                                                       # fountain in the quad + east range
        d.set(15, Y0, 15, "stone_brick_wall")
        d.set(15, Y0 + 1, 15, "water[level=0]") if False else d.set(15, Y0 + 1, 15, "lantern[hanging=false,waterlogged=false]")
        for x, z in ((14, 14), (16, 14), (14, 16), (16, 16)):
            d.set(x, Y0, z, "water[level=0]") if False else d.set(x, 1, z, "water[level=0]")
        crenel(d, 21, 10, 26, 19, 6)
        d.set(21, Y0, 15, AIR)
        d.door(21, Y0, 15, "west", "dark_oak")
        d.set(21, 4, 15, S)
        for z in (12, 14, 16, 18):
            d.bed(25, Y0, z, "east", "blue") if False else None
        d.set(24, 6, 15, "lantern[hanging=true,waterlogged=false]")
        for z in range(11, 19, 2):
            d.chair(25, Y0, z, "east", "dark_oak", sit=False)
            d.set(24, Y0, z, slab("dark_oak_slab", "top"))
    shelf_runs(d, runs, d.req["bookshelves"])
    return d


def university_neoterra(rel, L):
    d = Design("Neoterra", rel, (31, 22, 31), gy=1, paving="smooth_stone")
    W, G, Q = "white_concrete", "light_gray_concrete", "smooth_quartz"

    def block(x1, z1, x2, z2, top, glass_side=True):
        d.box(x1, Y0, z1, x2, top, z2, W, floor="polished_diorite")
        d.flat(x1, z1, x2, z2, top + 1, Q, W, "smooth_quartz_slab")
        for x in range(x1 + 1, x2):
            if (x - x1) % 3:
                d.window(x, 3, z1, x, top - 1, z1, "glass_pane")
                d.window(x, 3, z2, x, top - 1, z2, "glass_pane")
        for x in range(x1, x2 + 1):
            d.set(x, top, z1, "cyan_terracotta")
    # ---- faculty pavilion (west)
    block(3, 3, 12, 11, 6)
    d.double_door(7, Y0, 3, "x", "south", "birch")
    d.sign(7, 7, 2, "north", ["INSTITUTE OF", "SCIENCE"], "birch", glow=True, color="cyan") if False else \
        d.sign(7, 6, 2, "north", ["INSTITUTE OF", "SCIENCE"], "birch", glow=True, color="cyan")
    d.hut(4, Y0, 4)
    d.item(11, Y0, 4, "lectern", "west")
    d.rack(4, Y0, 10, "north")
    d.item(4, Y0, 9, "furnace", "east") if L == 1 else d.set(4, Y0, 9, "smooth_quartz")
    d.chair(8, Y0, 9, "south", "mangrove")
    d.chair(9, Y0, 9, "south", "mangrove")
    d.set(8, Y0, 8, slab("smooth_quartz_slab", "top"))
    d.set(9, Y0, 8, slab("smooth_quartz_slab", "top"))
    runs = [(11, 9, 11, 10, Y0, 3), (5, 10, 10, 10, Y0, 3), (11, 5, 11, 5, Y0, 3)]
    for x in (5, 9):
        d.set(x, 6, 7, "sea_lantern")
    # ---- glass bridge + lab block (east, L2+)
    if L >= 2:
        block(18, 3, 27, 11, 6)
        d.box(12, Y0, 5, 18, 5, 9, "glass", floor="polished_diorite")
        d.fill(12, 6, 5, 18, 6, 9, Q)
        d.clear(13, Y0, 6, 17, 5, 8)
        for x in (12, 18):
            d.clear(x, Y0, 7, x, 3, 7)
        d.door(12, Y0, 7, "east", "birch") if False else None
        d.set(13, Y0, 6, "potted_bamboo")
        # lab: brewing, cauldron, crafting, furnaces
        d.item(26, Y0, 4, "brewing_stand")
        d.item(26, Y0, 5, "water_cauldron[level=3]")
        d.item(26, Y0, 6, "crafting_table")
        for i in range(max(1, need(d, "furnace"))):
            d.item(26, Y0, 8 + i, "furnace", "west")
        for x in range(20, 24):
            d.set(x, Y0, 7, "smooth_quartz")
        d.set(21, Y0 + 1, 7, "brewing_stand[has_bottle_0=true,has_bottle_1=true,has_bottle_2=false]")
        d.set(23, Y0 + 1, 7, "end_rod[facing=up]")
        d.chair(21, Y0, 8, "south", "birch", sit=False)
        d.chair(22, Y0, 8, "south", "birch", sit=False)
        for x in (20, 24):
            d.set(x, 6, 7, "sea_lantern")
        # seminar table in the pavilion
        for x in range(6, 10):
            d.table(x, Y0, 6, "birch", "block", Q)
            d.chair(x, Y0, 5, "north", "mangrove")
            d.chair(x, Y0, 7, "south", "mangrove")
    # ---- lecture theatre (L3+) and the quad
    if L >= 3:
        X1, X2, Z1, Z2 = 3, 27, 19, 29
        d.box(X1, Y0, Z1, X2, 8, Z2, W, floor="polished_diorite")
        d.flat(X1, Z1, X2, Z2, 9, Q, W, "smooth_quartz_slab")
        for x in range(X1, X2 + 1):
            d.set(x, 8, Z1, "cyan_terracotta")
        for x in range(X1 + 2, X2 - 1, 4):
            d.window(x, 4, Z1, x + 1, 6, Z1, "light_gray_stained_glass_pane")
        d.double_door(14, Y0, Z1, "x", "north", "birch")
        # stage along the north wall, lectern, screen
        d.item(10, Y0, Z1 + 1, "lectern", "south") if need(d, "lectern") > 1 else d.set(10, Y0, Z1 + 1, Q)
        for x in range(6, 25):
            d.set(x, 5, Z1 + 1, "black_concrete")
            d.set(x, 6, Z1 + 1, "black_concrete")
        d.set(15, 6, Z1 + 1, "sea_lantern")
        # raked seating: tiers rising south
        for k in range(4):
            zs = Z1 + 3 + 2 * k
            for z in (zs, zs + 1):
                for x in range(X1 + 1, X2):
                    for y in range(Y0, Y0 + k):
                        d.set(x, y, z, Q)
            for x in range(X1 + 3, X2 - 2):
                if x == 15:
                    continue
                d.chair(x, Y0 + k, zs, "south", "birch")
        for x in range(6, 25, 6):
            d.set(x, 8, 24, "sea_lantern")
        runs.append((X1 + 1, Z2 - 1, X2 - 1, Z2 - 1, Y0 + 4, 2))
        # quad: lawn, trees, benches, paths; leisure spots
        for x in range(3, 28):
            for z in range(12, 19):
                d.set(x, 1, z, "grass_block[snowy=false]")
        for x in range(3, 28):
            d.set(x, 1, 15, "smooth_stone")
        for z in range(12, 19):
            d.set(15, 1, z, "smooth_stone")
        for x in (6, 24):
            tree(d, x, Y0, 13, "birch_log", "birch_leaves", 4, 1)
        bench(d, 9, 13, 11, 13, Y0, "north", "birch", tag=None)
        bench(d, 19, 17, 21, 17, Y0, "south", "birch", tag=None)
        for x, z in ((8, 15), (11, 15), (13, 15), (17, 15), (20, 15), (22, 15), (15, 13), (15, 17)):
            d.spot(x, Y0, z, "leisure")
    if L >= 4:
        runs.append((13, 6, 17, 6, Y0, 3)) if False else None
        for x in range(4, 12):
            d.set(x, 1, 12, "smooth_stone")
    if L >= 5:
        for x in range(4, 12):
            for z in (4, 10):
                d.set(x, 8, z, "moss_block") if False else None
        for x in range(19, 27, 2):
            for z in range(5, 10):
                d.set(x, 8, z, "daylight_detector[inverted=false,power=0]")
        for x in range(4, 12):
            d.set(x, 8, 6, "flowering_azalea") if x % 2 else None
    shelf_runs(d, runs, d.req["bookshelves"])
    return d


def university_cascadia(rel, L):
    d = Design("Cascadia", rel, (31, 20, 31), gy=1, paving="coarse_dirt")
    lg = "spruce_log"

    def lodge(x1, z1, x2, z2, axis, top=5, roof="dark_oak"):
        d.box(x1, Y0, z1, x2, top, z2, log("stripped_spruce_log", "z" if axis == "z" else "x"), floor="spruce_planks")
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                if x in (x1, x2) or z in (z1, z2):
                    d.set(x, Y0, z, "cobblestone" if (x + z) % 3 else "mossy_cobblestone")
                    if (x in (x1, x2)) != (z in (z1, z2)):
                        for y in range(Y0 + 1, top + 1):
                            d.set(x, y, z, log("stripped_spruce_log", "x" if z in (z1, z2) else "z"))
        for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
            for y in range(Y0, top + 1):
                d.set(x, y, z, log(lg))
        return d.gable(x1, z1, x2, z2, top + 1, axis, f"{roof}_stairs", f"{roof}_slab", "spruce_planks", overhang=1)
    # ---- hall lodge (north-west): study
    lodge(3, 3, 13, 11, "x")
    d.door(8, Y0, 3, "south", "spruce")
    d.sign(8, 5, 2, "north", ["TIMBERLINE", "COLLEGE"], "spruce")
    for x in (5, 11):
        d.window(x, 3, 3, x, 4, 3)
    d.hut(4, Y0, 4)
    d.item(12, Y0, 4, "lectern", "west")
    d.rack(4, Y0, 10, "north")
    for y in range(Y0, 10):
        d.set(8, y, 12, "cobblestone" if y % 3 else "mossy_cobblestone")
    d.hearth(8, Y0, 10, "north", 6, "cobblestone", "campfire")
    d.chair(7, Y0, 8, "south", "spruce", arms=True)
    d.chair(9, Y0, 8, "south", "spruce", arms=True)
    d.item(12, Y0, 10, "furnace", "west") if L == 1 else d.set(12, Y0, 10, "barrel[facing=up,open=false]") if False else None
    if L == 1:
        d.item(12, Y0, 10, "furnace", "west")
    runs = [(4, 6, 4, 8, Y0, 3), (12, 6, 12, 8, Y0, 3)]
    d.set(8, 5, 6, "lantern[hanging=true,waterlogged=false]")
    # ---- chemistry cabin (north-east, L2+)
    if L >= 2:
        lodge(17, 3, 27, 11, "x", roof="spruce")
        d.door(22, Y0, 3, "south", "spruce")
        for x in (19, 25):
            d.window(x, 3, 3, x, 4, 3)
        d.item(26, Y0, 5, "brewing_stand")
        d.item(26, Y0, 6, "water_cauldron[level=3]")
        d.item(26, Y0, 7, "crafting_table")
        for i in range(max(1, need(d, "furnace"))):
            d.item(18, Y0, 5 + i, "furnace", "east")
        for x in (21, 22, 23):
            d.set(x, Y0, 8, slab("spruce_slab", "top"))
            d.chair(x, Y0, 9, "south", "spruce", sit=False)
        d.set(22, 5, 7, "lantern[hanging=true,waterlogged=false]")
        # study table in the hall lodge for 10 seats
        for x in (6, 7, 8, 9, 10):
            d.table(x, Y0, 6, "spruce", "block", "stripped_spruce_wood[axis=y]")
            d.chair(x, Y0, 5, "north", "spruce")
        d.chair(5, Y0, 6, "west", "spruce")
        d.chair(11, Y0, 6, "east", "spruce")
        d.chair(5, Y0, 5, "west", "spruce") if False else d.chair(11, Y0, 5, "east", "spruce")
        runs += [(18, 9, 18, 10, Y0, 3), (26, 9, 26, 10, Y0, 3)]
        # boardwalk between the two lodges with a roof
        for x in range(14, 17):
            for z in range(5, 10):
                d.set(x, 1, z, "spruce_planks")
            d.set(x, 6, 4, slab("spruce_slab"))
            d.set(x, 6, 10, slab("spruce_slab"))
            for z in range(5, 10):
                d.set(x, 6, z, slab("spruce_slab"))
        for x in (14, 16):
            for z in (4, 10):
                for y in range(Y0, 6):
                    d.set(x, y, z, "spruce_fence")
        for x0 in (13, 17):
            d.clear(x0, Y0, 7, x0, Y0 + 1, 7)
            d.door(x0, Y0, 7, "east" if x0 == 13 else "west", "spruce")
    # ---- lecture lodge (south, L3+) + quad with campfire ring and boardwalks
    if L >= 3:
        lodge(3, 20, 27, 28, "x", top=6)
        d.double_door(15, Y0, 20, "x", "north", "spruce")
        for x in range(5, 27, 4):
            d.window(x, 3, 28, x, 5, 28)
            if x not in (13, 17):
                d.window(x, 3, 20, x, 5, 20)
        d.item(5, Y0, 24, "lectern", "east") if need(d, "lectern") > 1 else d.set(5, Y0, 24, "spruce_planks")
        blackboard(d, 4, 23, 4, 25, 3, "east", "black_concrete", "spruce")
        for x in range(8, 24, 2):
            for z in (21, 22, 23, 25, 26, 27):
                if d.placed["seats"] < d.req["seats"] + 4:
                    d.chair(x, Y0, z, "east", "spruce")
        runs.append((26, 21, 26, 27, Y0, 3))
        for x in range(8, 25, 5):
            d.set(x, 6, 24, "lantern[hanging=true,waterlogged=false]")
        beams(d, 6, 25, 21, 27, 7, "stripped_spruce_log", every=5)
        # quad
        for x in range(3, 28):
            for z in range(12, 20):
                d.set(x, 1, z, "grass_block[snowy=false]" if (x * 7 + z) % 5 else "moss_block")
        for z in range(12, 20):
            d.set(15, 1, z, "spruce_planks")
            d.set(16, 1, z, "spruce_planks")
        d.set(15, 1, 12, "spruce_planks")
        cx, cz = 9, 16                                               # campfire ring
        d.set(cx, Y0, cz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        d.set(cx, 1, cz, "cobblestone")
        for (x, z, ax) in ((cx - 2, cz, "z"), (cx + 2, cz, "z"), (cx, cz - 2, "x"), (cx, cz + 2, "x")):
            d.set(x, Y0, z, log("stripped_spruce_log", ax))
        for x, z in ((cx - 2, cz - 1), (cx + 2, cz - 1), (cx - 1, cz - 2), (cx + 1, cz + 2), (cx - 2, cz + 2),
                     (cx + 2, cz + 2), (22, 15), (20, 17)):
            d.spot(x, Y0, z, "leisure")
        tree(d, 22, Y0, 13, "spruce_log", "spruce_leaves", 5, 2)
        for z in (12, 19):
            for x in (14, 17):
                d.set(x, Y0, z, "lantern[hanging=false,waterlogged=false]") if False else None
        d.set(14, Y0, 13, "spruce_fence")
        d.set(14, Y0 + 1, 13, "lantern[hanging=false,waterlogged=false]")
        d.set(17, Y0, 18, "spruce_fence")
        d.set(17, Y0 + 1, 18, "lantern[hanging=false,waterlogged=false]")
    # ---- reading cabin (L4+) west of the quad... built as shelves wall + porch in the hall lodge loft
    if L >= 4:
        runs += [(5, 10, 7, 10, Y0, 3), (9, 10, 11, 10, Y0, 3), (4, 9, 4, 9, Y0, 3), (12, 9, 12, 9, Y0, 3)]
        for x in range(0, 3):
            pass
    if L >= 5:
        for y in range(Y0, 14):
            d.set(29, y, 15, "spruce_fence")
        d.set(29, 14, 15, "green_wool")
        d.set(29, 13, 15, "green_wool")
        for z in range(12, 20):
            d.set(1, Y0, z, "spruce_fence")
            d.set(29, Y0, z, "spruce_fence") if z != 15 else None
    shelf_runs(d, runs, d.req["bookshelves"])
    return d


@design("university")
def university(pack, rel, L):
    return {"Hearthwood": university_hearthwood, "Cascadia": university_cascadia,
            "Neoterra": university_neoterra}[pack](rel, L)


# ============================================================================================ COMMUNITY COLLEGE
"""
Community college (smaller campus building with an outdoor teaching spot).
  Hearthwood  Mechanics' Institute: red-brick hall with stone quoins, pedimented gable to the street, stone
              porch; lecture room with benches facing the lecturer's lectern and wall shelves; reading room on a
              new upper floor from L4. Walled front garden with a speaker's plinth and benches.
  Neoterra    learning pavilion: glass-fronted flat-roofed classroom behind an open-air amphitheatre (tiered
              seats facing a stage with the outdoor lecturer's spot and lectern); green roof at L5.
  Cascadia    grange-style timber hall broadside to the street with a deep porch, outdoor fire circle with log
              benches and a speaker's stump; reading lean-to from L4.
"""


def sit_out(d, x, y, z, back, wood):
    d.chair(x, y, z, back, wood, sit=False)
    d.tag(x, y, z, "sit_out")


def college_hearthwood(rel, L):
    d = Design("Hearthwood", rel, (23, 24, 27), gy=1)
    B, Q = "bricks", "stone_bricks"
    X1, X2, Z1, Z2 = 4, 18, 9, 21
    two = L >= 4
    top = 11 if two else 6
    d.box(X1, Y0, Z1, X2, top, Z2, B, floor="oak_planks")
    for x in range(X1, X2 + 1):
        for z in range(Z1, Z2 + 1):
            if x in (X1, X2) or z in (Z1, Z2):
                d.set(x, Y0, z, Q)
    for x, z in ((X1, Z1), (X2, Z1), (X1, Z2), (X2, Z2)):           # quoins
        for y in range(Y0, top + 1):
            d.set(x, y, z, Q if y % 2 else "polished_andesite")
    if two:
        d.fill(X1 + 1, 7, Z1 + 1, X2 - 1, 7, Z2 - 1, "oak_planks")
        for x in range(X1, X2 + 1):
            d.set(x, 7, Z1, Q)
            d.set(x, 7, Z2, Q)
        for z in range(Z1, Z2 + 1):
            d.set(X1, 7, z, Q)
            d.set(X2, 7, z, Q)
    ridge = d.gable(X1, Z1, X2, Z2, top + 1, "z", "deepslate_tile_stairs", "deepslate_tile_slab", B, overhang=1)
    if not two:
        beams(d, X1 + 1, X2 - 1, Z1 + 2, Z2 - 2, 7, "stripped_dark_oak_log", every=4, axis="x")
    # pediment: stone string course across the street gable, oculus, name
    for x in range(X1 - 1, X2 + 2):
        d.set(x, top + 1, Z1 - 1, st("stone_brick_stairs", "south", "top")) if False else None
    for x in range(X1, X2 + 1):
        d.set(x, top + 1, Z1, Q) if d.get(x, top + 1, Z1) == "minecraft:bricks" else None
    d.set(11, top + 3, Z1, "glass_pane")
    d.set(11, top + 4, Z1, "glass_pane")
    d.sign(11, top + 2, Z1 - 1, "north", ["MECHANICS'", "INSTITUTE"], "dark_oak")
    # windows: tall sashes with stone heads
    for x in (6, 8, 14, 16):
        d.window(x, 3, Z1, x, 5, Z1)
        d.set(x, 6, Z1, Q)
        if two:
            d.window(x, 8, Z1, x, 10, Z1)
    for z in range(Z1 + 2, Z2 - 1, 3):
        d.window(X1, 4, z, X1, 5, z)
        d.window(X2, 4, z, X2, 5, z)
        if two:
            d.window(X1, 9, z, X1, 10, z)
            d.window(X2, 9, z, X2, 10, z)
    # porch: two columns and a small pediment, steps
    d.double_door(11, Y0, Z1, "x", "south", "dark_oak") if False else d.door(11, Y0, Z1, "south", "dark_oak")
    for x in (9, 13):
        for y in range(Y0, 6):
            d.set(x, y, Z1 - 2, "quartz_pillar[axis=y]" if L >= 3 else Q)
    d.fill(9, 6, Z1 - 2, 13, 6, Z1 - 1, Q)
    for x in range(9, 14):
        d.set(x, 7, Z1 - 2, st("stone_brick_stairs", "south") if x != 11 else Q)
    d.fill(9, 1, Z1 - 2, 13, 1, Z1 - 1, "polished_andesite")
    # ---- lecture room
    d.hut(X1 + 2, Y0, Z1 + 1)
    d.item(11, Y0, Z2 - 2, "lectern", "north")
    blackboard(d, 9, Z2 - 1, 13, Z2 - 1, 3, "north")
    if need(d, "lectern") > 1:
        d.item(15, Y0, Z2 - 2, "lectern", "north")                 # demonstrator's stand
    n = 0
    for z in (Z1 + 3, Z1 + 5):
        for x in list(range(7, 11)) + list(range(12, 16)):
            if d.placed["seats"] < d.req["seats"]:
                d.chair(x, Y0, z, "north", "dark_oak")
    shelf_runs(d, [(X2 - 1, Z1 + 1, X2 - 1, Z1 + 5, Y0, 2), (X2 - 1, Z1 + 6, X2 - 1, Z2 - 1, Y0, 1),
                   (X2 - 1, Z1 + 6, X2 - 1, Z2 - 1, Y0 + 1, 1), (X2 - 1, Z1 + 1, X2 - 1, Z2 - 1, Y0 + 2, 1)],
               min(d.req["bookshelves"], 18))
    for z in (Z1 + 4, Z2 - 4):
        d.set(11, 6, z, "lantern[hanging=true,waterlogged=false]")
    # ---- reading room upstairs (L4+)
    if two:
        flight(d, X1 + 1, Z1 + 2, Y0, 8, "south", "oak_stairs", under="oak_planks")
        rail(d, X1 + 2, Z1 + 3, X1 + 2, Z1 + 7, 8, "dark_oak_fence")
        shelf_runs(d, [(X2 - 1, Z1 + 1, X2 - 1, Z2 - 1, 8, 3), (X1 + 2, Z2 - 1, X2 - 2, Z2 - 1, 8, 3),
                       (X1 + 1, Z2 - 3, X1 + 1, Z2 - 1, 8, 3)], d.req["bookshelves"])
        for x in (9, 12):
            d.dining(x, 8, 15, 1, "x", "dark_oak", ("n", "s"), sit=False)
        for z in (12, 17):
            d.set(11, 11, z, "lantern[hanging=true,waterlogged=false]") if False else d.lamp(11, 11, z)
    # ---- walled front garden: speaker's plinth + benches (outdoor class)
    for x in range(2, 21):
        for z in range(1, Z1 - 2):
            d.set(x, 1, z, "grass_block[snowy=false]")
    for z in range(1, Z1 - 2):
        for x in (10, 11, 12):
            d.set(x, 1, z, "gravel")
    for x in range(2, 21):
        if x not in (10, 11, 12):
            d.set(x, Y0, 0, "brick_wall")
    for z in range(0, Z1 - 1):
        d.set(2, Y0, z, "brick_wall")
        d.set(20, Y0, z, "brick_wall")
    d.set(5, 1, 3, Q)
    d.set(5, Y0, 3, slab("stone_brick_slab"))
    d.spot(5, Y0 + 1, 3, "stand_out") if False else d.tag(5, Y0, 3, "stand_out")
    d.placed["spots"]["stand_out"] = 1
    for x in (4, 6, 7):
        pass
    for x in (3, 4, 6, 7):
        sit_out(d, x, Y0, 5, "south", "dark_oak")
    sit_out(d, 8, Y0, 4, "east", "dark_oak")
    sit_out(d, 8, Y0, 3, "east", "dark_oak")
    for x in (14, 17):
        d.set(x, Y0, 3, "rose_bush[half=lower]")
        d.set(x, Y0 + 1, 3, "rose_bush[half=upper]")
    if L >= 5:
        tree(d, 16, Y0, 4, "oak_log", "oak_leaves", 4, 2)
        for x in (10, 12):
            d.set(x, Y0, 1, "brick_wall")
            d.set(x, Y0 + 1, 1, "lantern[hanging=false,waterlogged=false]")
    return d


def college_neoterra(rel, L):
    d = Design("Neoterra", rel, (25, 16, 29), gy=1, paving="smooth_stone")
    W, Q = "white_concrete", "smooth_quartz"
    X1, X2, Z1, Z2 = 4, 20, 15, 26
    d.box(X1, Y0, Z1, X2, 6, Z2, W, floor="polished_diorite")
    d.fill(X1 - 1, 7, Z1 - 2, X2 + 1, 7, Z2 + 1, Q)
    for x in range(X1 - 1, X2 + 2):
        d.set(x, 8, Z1 - 2, slab("smooth_quartz_slab"))
    for x in range(X1 + 1, X2):
        d.window(x, Y0, Z1, x, 6, Z1, "glass_pane")
    for x in range(X1, X2 + 1, 4):
        for y in range(Y0, 7):
            d.set(x, y, Z1, "cyan_terracotta")
    for z in range(Z1 + 2, Z2 - 1, 3):
        d.window(X1, 3, z, X1, 5, z, "glass_pane")
    d.double_door(11, Y0, Z1, "x", "south", "birch")
    d.set(11, Y0, Z1, AIR) if False else None
    d.sign(12, 7, Z1 - 3, "north", ["LEARNING", "PAVILION"], "birch", glow=True, color="cyan") if False else \
        d.sign(11, 6, Z1 - 1, "north", ["LEARNING", "PAVILION"], "birch", glow=True, color="cyan")
    # ---- classroom: screen + lectern on the east wall, seats facing it
    d.hut(X1 + 1, Y0, Z1 + 1)
    d.item(X2 - 2, Y0, 20, "lectern", "west")
    for z in range(18, 23):
        d.set(X2 - 1, 4, z, "black_concrete")
        d.set(X2 - 1, 5, z, "black_concrete")
    for x in (9, 11, 13, 15):
        for z in (18, 19, 21, 22):
            if d.placed["seats"] < d.req["seats"]:
                d.chair(x, Y0, z, "west", "birch")
                d.table(x + 1, Y0, z, "birch", "slab", "smooth_quartz_slab") if False else None
    runs = [(X1 + 1, Z2 - 1, X1 + 5, Z2 - 1, Y0, 2), (X1 + 6, Z2 - 1, X1 + 10, Z2 - 1, Y0, 2),
            (X1 + 11, Z2 - 1, X2 - 1, Z2 - 1, Y0, 2), (X1 + 1, Z2 - 1, X2 - 1, Z2 - 1, Y0 + 2, 1),
            (X1 + 1, Z1 + 4, X1 + 1, Z2 - 2, Y0, 3), (X1 + 2, Z1 + 4, X1 + 3, Z1 + 4, Y0, 2)]
    shelf_runs(d, runs, d.req["bookshelves"])
    for x in (8, 12, 16):
        d.set(x, 6, 20, "sea_lantern")
    # ---- amphitheatre: stage by the pavilion, tiers rising to the street
    for x in range(6, 19):
        for z in (11, 12):
            d.set(x, 1, z, "polished_andesite")
    d.spot(12, Y0, 12, "stand_out")
    if need(d, "lectern") > 1:
        d.item(14, Y0, 12, "lectern", "north")
    for k, z in enumerate((9, 7, 5, 3)):
        for zz in (z, z - 1):
            for x in range(5, 20):
                for y in range(Y0, Y0 + k):
                    d.set(x, y, zz, Q)
        for x in range(6, 19):
            if x == 12:
                continue
            if k < 2 or L >= 3:
                sit_out(d, x, Y0 + k, z, "north", "birch") if k < 3 else None
    for y in range(Y0, Y0 + 3):                                     # aisle steps
        pass
    for x in (5, 19):
        for z in range(3, 12):
            d.set(x, Y0 + 3, z, "birch_fence") if False else None
    if L >= 2:
        for x in (4, 20):
            d.set(x, Y0, 11, "birch_fence")
            d.set(x, Y0 + 1, 11, "end_rod[facing=up]")
    if L >= 3:                                                       # shade canopy over the stage
        for x in (6, 18):
            for y in range(Y0, 7):
                d.set(x, y, 10, "white_concrete")
        for x in range(6, 19):
            d.set(x, 7, 10, Q)
            d.set(x, 7, 11, slab("smooth_quartz_slab", "top"))
            d.set(x, 7, 12, slab("smooth_quartz_slab", "top"))
            d.set(x, 7, 13, slab("smooth_quartz_slab", "top"))
        for x in range(8, 18, 3):
            d.set(x, 6, 10, "sea_lantern") if False else None
    if L >= 5:                                                       # green roof
        for x in range(X1, X2 + 1):
            for z in range(Z1 - 1, Z2 + 1):
                if x not in (X1 - 1, X2 + 1):
                    d.set(x, 8, z, "moss_carpet")
        for x in range(X1 + 1, X2, 4):
            d.set(x, 8, Z2, "flowering_azalea")
    return d


def college_cascadia(rel, L):
    d = Design("Cascadia", rel, (25, 18, 29), gy=1, paving="coarse_dirt")
    lg = "spruce_log"
    X1, X2, Z1, Z2 = 3, 19, 15, 25
    d.box(X1, Y0, Z1, X2, 6, Z2, log("stripped_spruce_log", "x"), floor="spruce_planks")
    for z in range(Z1, Z2 + 1):
        for y in range(Y0, 7):
            d.set(X1, y, z, log("stripped_spruce_log", "z"))
            d.set(X2, y, z, log("stripped_spruce_log", "z"))
    for x in range(X1, X2 + 1):
        for z in range(Z1, Z2 + 1):
            if x in (X1, X2) or z in (Z1, Z2):
                d.set(x, Y0, z, "cobblestone" if (x + z) % 3 else "mossy_cobblestone")
    for x in range(X1, X2 + 1, 4):
        for z in (Z1, Z2):
            for y in range(Y0 + 1, 7):
                d.set(x, y, z, log(lg))
    ridge = d.gable(X1, Z1, X2, Z2, 7, "x", "dark_oak_stairs", "dark_oak_slab", "spruce_planks", overhang=1)
    beams(d, X1 + 2, X2 - 2, Z1 + 1, Z2 - 1, 7, "spruce_log", every=4)
    for x in (5, 9, 13, 17):
        d.window(x + 1, 3, Z1, x + 2, 4, Z1) if x + 2 < X2 else None
    for x in (6, 10, 14):
        d.window(x, 3, Z2, x + 1, 4, Z2)
    d.double_door(11, Y0, Z1, "x", "south", "spruce") if False else d.door(11, Y0, Z1, "south", "spruce")
    d.set(10, Y0, Z1, log("stripped_spruce_log", "x"))
    d.set(10, Y0 + 1, Z1, log("stripped_spruce_log", "x"))
    # deep porch along the street side
    d.fill(X1, 1, Z1 - 3, X2, 1, Z1 - 1, "spruce_planks")
    for x in (X1, 7, 15, X2):
        for y in range(Y0, 6):
            d.set(x, y, Z1 - 3, log(lg))
    for x in range(X1 - 1, X2 + 2):
        d.set(x, 6, Z1 - 4, st("spruce_stairs", "south"))
        for z in range(Z1 - 3, Z1):
            d.set(x, 6, z, slab("spruce_slab"))
    d.sign(11, 5, Z1 - 1, "north", ["VALLEY", "COLLEGE"], "spruce")
    for x in (8, 14):
        d.set(x, 5, Z1 - 2, "lantern[hanging=true,waterlogged=false]")
    # stone chimney on the west end
    for y in range(Y0, ridge + 1):
        d.set(X1 - 1, y, 20, "cobblestone" if y % 3 else "mossy_cobblestone")
    d.hearth(X1 + 1, Y0, 20, "east", 7, "cobblestone", "campfire")
    for y in range(Y0 + 2, 7):
        d.set(X1, y, 20, "cobblestone")
    # ---- classroom: lectern on the east end, benches facing it
    d.hut(X1 + 2, Y0, Z1 + 1)
    d.item(X2 - 2, Y0, 20, "lectern", "west")
    blackboard(d, X2 - 1, 18, X2 - 1, 22, 3, "west", "black_concrete", "spruce")
    for x in (8, 10, 12, 14):
        for z in (17, 18, 19, 21, 22, 23):
            if d.placed["seats"] < d.req["seats"]:
                d.chair(x, Y0, z, "west", "spruce")
    runs = [(X1 + 1, Z2 - 1, X1 + 5, Z2 - 1, Y0, 2), (X1 + 1, Z1 + 1, X1 + 1, Z1 + 3, Y0, 2),
            (X1 + 6, Z2 - 1, X1 + 9, Z2 - 1, Y0, 2)]
    for x in (9, 13):
        d.set(x, 6, 20, "lantern[hanging=true,waterlogged=false]")
    # ---- reading lean-to (L4+) on the east end
    if L >= 4:
        d.box(X2, Y0, 16, 23, 5, 24, log("stripped_spruce_log", "z"), floor="spruce_planks")
        for z in range(15, 26):
            for x in range(X2 + 1, 25):
                d.set(x, 6, z, slab("spruce_slab"))
        d.clear(X2, Y0, 24 - 4, X2, Y0 + 1, 20)
        d.set(X2 - 1, 3, 20, AIR) if False else None
        d.set(X2, Y0, 20, AIR)
        d.set(X2, Y0 + 1, 20, AIR)
        d.door(X2, Y0, 23, "east", "spruce") if False else None
        d.item(X2 - 2, Y0, 20, "lectern", "west") if False else None
        runs += [(21, 17, 21, 19, Y0, 3), (21, 21, 21, 23, Y0, 3), (22, 17, 22, 23, Y0, 3),
                 (20, 17, 20, 17, Y0, 3), (20, 23, 20, 23, Y0, 3)]
        d.window(23, 3, 19, 23, 4, 21) if False else None
        d.set(21, 5, 20, "lantern[hanging=true,waterlogged=false]")
        # the classroom lectern moves off the doorway
        d.set(X2 - 2, Y0, 20, AIR)
        d.placed["items"]["minecraft:lectern"] -= 1
        d.item(X2 - 2, Y0, 19, "lectern", "west")
        for z in range(18, 23):
            d.set(X2 - 1, 3, z, AIR)
            d.set(X2 - 1, 4, z, AIR)
            d.set(X2 - 1, Y0, z, AIR)
        blackboard(d, X2 - 1, 17, X2 - 1, 18, 3, "west", "black_concrete", "spruce")
        blackboard(d, X2 - 1, 22, X2 - 1, 23, 3, "west", "black_concrete", "spruce")
    shelf_runs(d, runs, d.req["bookshelves"])
    # ---- fire circle with log benches and the speaker's stump
    cx, cz = 11, 6
    for x in range(cx - 4, cx + 5):
        for z in range(cz - 4, cz + 5):
            if abs(x - cx) + abs(z - cz) <= 6:
                d.set(x, 1, z, "gravel" if abs(x - cx) + abs(z - cz) <= 2 else "coarse_dirt")
    d.set(cx, 1, cz, "cobblestone")
    d.set(cx, Y0, cz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for x in (cx - 1, cx, cx + 1):
        sit_out(d, x, Y0, cz - 3, "north", "spruce")
    for z in (cz - 1, cz, cz + 1):
        sit_out(d, cx - 3, Y0, z, "west", "spruce")
        sit_out(d, cx + 3, Y0, z, "east", "spruce")
    d.set(cx, 1, cz + 3, log("stripped_spruce_log"))
    d.spot(cx, Y0, cz + 3, "stand_out")
    if need(d, "lectern") > 1 and L < 4:
        d.item(cx + 1, Y0, cz + 3, "lectern", "north")
    elif need(d, "lectern") > 1:
        d.item(cx + 1, Y0, cz + 3, "lectern", "north")
    for x, z in ((cx - 4, cz - 3), (cx + 4, cz - 3)):
        d.set(x, Y0, z, "spruce_fence")
        d.set(x, Y0 + 1, z, "lantern[hanging=false,waterlogged=false]")
    if L >= 5:                                                       # woodpile and chopping stumps
        for x in range(19, 23):
            for y in (Y0, Y0 + 1):
                d.set(x, y, 2, log("spruce_log", "x"))
        d.set(2, Y0, 4, log("stripped_spruce_log"))
        d.set(2, Y0, 7, log("stripped_spruce_log"))
        for z in range(1, 12):
            d.set(0, Y0, z, "spruce_fence")
            d.set(24, Y0, z, "spruce_fence")
    return d


@design("communitycollege")
def communitycollege(pack, rel, L):
    return {"Hearthwood": college_hearthwood, "Cascadia": college_cascadia, "Neoterra": college_neoterra}[pack](rel, L)


# ############################################################################################################
#  ROUND 2: modular complexes – every level adds real buildings / storeys, all rooms furnished and decorated
# ############################################################################################################
STY = {
    "Hearthwood": dict(wall="bricks", up="calcite", base="stone_bricks", post="stripped_dark_oak_log",
                       band="dark_oak_planks", floor="oak_planks", wood="dark_oak", wood2="oak",
                       roof="deepslate_tile", glass="glass_pane", shutter="spruce_trapdoor", sill="dark_oak_trapdoor",
                       lamp="lantern", rug=("red_carpet", "orange_carpet"), bed="red", path="gravel",
                       border="stone_brick_wall", flowers=("red_tulip", "oxeye_daisy", "cornflower", "allium")),
    "Cascadia": dict(wall="stripped_spruce_log", up="stripped_spruce_log", base="cobblestone", post="spruce_log",
                     band="spruce_log", floor="spruce_planks", wood="spruce", wood2="dark_oak",
                     roof="dark_oak", glass="glass_pane", shutter="spruce_trapdoor", sill="spruce_trapdoor",
                     lamp="lantern", rug=("brown_carpet", "green_carpet"), bed="brown", path="coarse_dirt",
                     border="cobblestone_wall", flowers=("fern", "blue_orchid", "lily_of_the_valley", "dandelion")),
    "Neoterra": dict(wall="white_concrete", up="white_concrete", base="light_gray_concrete", post="light_gray_concrete",
                     band="cyan_terracotta", floor="polished_diorite", wood="birch", wood2="mangrove",
                     roof="smooth_quartz", glass="glass_pane", shutter=None, sill="smooth_quartz_slab",
                     lamp="sea_lantern", rug=("cyan_carpet", "light_gray_carpet"), bed="cyan", path="smooth_stone",
                     border="smooth_quartz_slab", flowers=("bamboo", "azure_bluet", "white_tulip", "cactus")),
}
OUT = {"n": "north", "s": "south", "e": "east", "w": "west"}


# per-type palettes inside each pack (roof / walls / trim / accent differ between building types)
THEMES = {
    ("Hearthwood", "townhall"): dict(roof="deepslate_tile", wall="stone_bricks", up="calcite", post="stripped_dark_oak_log",
                                     shutter="mangrove_trapdoor", band="dark_oak_planks"),
    ("Hearthwood", "hospital"): dict(roof="dark_oak", wall="bricks", up="calcite", post="stripped_oak_log",
                                     shutter="warped_trapdoor", band="oak_planks", wood="oak", sill="oak_trapdoor"),
    ("Hearthwood", "library"): dict(roof="mud_brick", wall="smooth_sandstone", up="smooth_sandstone",
                                    shutter="dark_oak_trapdoor", base="sandstone"),
    ("Hearthwood", "school"): dict(roof="brick", wall="yellow_terracotta", up="yellow_terracotta",
                                   post="stripped_oak_log", shutter="warped_trapdoor", wood="oak", band="oak_planks"),
    ("Hearthwood", "university"): dict(roof="dark_prismarine", wall="stone_bricks", up="stone_bricks",
                                       shutter="spruce_trapdoor"),
    ("Hearthwood", "communitycollege"): dict(roof="granite", wall="white_terracotta", up="white_terracotta",
                                             shutter="bamboo_trapdoor", post="stripped_dark_oak_log"),
    ("Cascadia", "townhall"): dict(roof="dark_oak", wall="stripped_spruce_log", shutter="mangrove_trapdoor"),
    ("Cascadia", "hospital"): dict(roof="dark_prismarine", wall="birch_planks", up="birch_planks",
                                   post="stripped_birch_log", band="spruce_log", shutter="mangrove_trapdoor"),
    ("Cascadia", "library"): dict(roof="mangrove", wall="stripped_dark_oak_log", up="stripped_dark_oak_log",
                                  post="spruce_log", shutter="warped_trapdoor", base="tuff"),
    ("Cascadia", "school"): dict(roof="spruce", wall="mangrove_planks", up="mangrove_planks", post="stripped_birch_log",
                                 shutter="birch_trapdoor", band="stripped_birch_log"),
    ("Cascadia", "university"): dict(roof="deepslate_tile", wall="stripped_spruce_log", shutter="warped_trapdoor",
                                     base="andesite"),
    ("Cascadia", "communitycollege"): dict(roof="warped", wall="spruce_planks", up="spruce_planks",
                                           post="stripped_spruce_log", shutter="bamboo_trapdoor"),
    ("Neoterra", "townhall"): dict(band="cyan_terracotta", wall="white_concrete"),
    ("Neoterra", "hospital"): dict(band="lime_terracotta", wall="white_concrete", base="light_gray_concrete"),
    ("Neoterra", "library"): dict(band="orange_terracotta", wall="white_terracotta", up="birch_planks",
                                  base="polished_deepslate"),
    ("Neoterra", "school"): dict(band="yellow_concrete", wall="light_gray_concrete", up="light_gray_concrete"),
    ("Neoterra", "university"): dict(band="magenta_terracotta", wall="light_gray_concrete", up="white_concrete",
                                     base="polished_blackstone"),
    ("Neoterra", "communitycollege"): dict(band="orange_concrete", wall="white_concrete", up="mangrove_planks",
                                           base="gray_concrete"),
}


def new(pack, rel, size, **kw):
    d = Design(pack, rel, size, gy=1, **kw)
    d.res = set()
    d.S = dict(STY[pack])
    d.S.update(THEMES.get((pack, d.req["base"]), {}))
    return d


def put(d, x, y, z, b, te=None):
    if not d.bp.inside(x, y, z) or not d.air(x, y, z) or (x, y, z) in d.res:
        return False
    d.set(x, y, z, b, te)
    return True


def keep(d, x, y, z, h=2):
    for k in range(h):
        d.res.add((x, y + k, z))


def wallblock(d, mat, side):
    if mat.endswith("_log") or mat.endswith("_wood"):
        return log(mat, "x" if side in ("n", "s") else "z")
    return mat


def bldg(d, x1, z1, x2, z2, nf=1, roof="gable", axis="x", win="nesw", ws=3, mat=None, up=None, wh=4,
         gable_end=None, beams_on=True, deco=True, glassy=False, parapet=True):
    """A building shell: plinth, walls per storey (wh high + floor slab), corner posts, storey bands, windows with
    sills/shutters, roof (gable/hip/flat) with eave brackets, tie beams and lights. Returns dict(ys, top, ridge)."""
    S = d.S
    mat = mat or S["wall"]
    up = up or S["up"]
    fh = wh + 1
    ys = [Y0 + fh * f for f in range(nf)]
    top = ys[-1] + wh - 1
    d.fill(x1, 1, z1, x2, 1, z2, S["floor"] if d.pack != "Neoterra" else "polished_diorite")
    for f, y in enumerate(ys):
        m = mat if f == 0 else up
        for yy in range(y, y + (wh if f == nf - 1 else fh)):
            for x in range(x1, x2 + 1):
                d.set(x, yy, z1, wallblock(d, m, "n"))
                d.set(x, yy, z2, wallblock(d, m, "s"))
            for z in range(z1 + 1, z2):
                d.set(x1, yy, z, wallblock(d, m, "w"))
                d.set(x2, yy, z, wallblock(d, m, "e"))
            if yy < y + wh:
                d.clear(x1 + 1, yy, z1 + 1, x2 - 1, yy, z2 - 1)
        if f < nf - 1:
            yb = y + wh
            d.fill(x1 + 1, yb, z1 + 1, x2 - 1, yb, z2 - 1, S["floor"] if d.pack != "Neoterra" else "smooth_stone")
            for x in range(x1, x2 + 1):
                for z in (z1, z2):
                    d.set(x, yb, z, wallblock(d, S["band"], "n" if z == z1 else "s"))
            for z in range(z1, z2 + 1):
                for x in (x1, x2):
                    d.set(x, yb, z, wallblock(d, S["band"], "w"))
    # plinth
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if x in (x1, x2) or z in (z1, z2):
                d.set(x, Y0, z, S["base"] if not (d.pack == "Cascadia" and (x * 7 + z) % 5 == 0) else "mossy_cobblestone")
    # timber framing on Hearthwood upper storeys
    if d.pack == "Hearthwood":
        for f, y in enumerate(ys):
            m = mat if f == 0 else up
            if m in ("calcite", "yellow_terracotta", "white_terracotta", "pink_terracotta", "light_blue_terracotta"):
                framing(d, x1, z1, x2, z2, y, y + wh - 1, S["post"], every=3)
    # corner posts / quoins
    for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        for y in range(Y0, top + 1):
            if d.pack == "Hearthwood":
                if mat == up or y < ys[0] + wh:
                    d.set(x, y, z, ("smooth_stone" if y % 2 else "chiseled_stone_bricks") if mat == "stone_bricks" else
                          ("cut_sandstone" if y % 2 else "chiseled_sandstone") if mat == "smooth_sandstone" else
                          ("smooth_stone" if y % 2 else "stone_bricks"))
                else:
                    d.set(x, y, z, log(S["post"]))
            elif d.pack == "Cascadia":
                d.set(x, y, z, log(S["post"]))
            else:
                d.set(x, y, z, "light_gray_concrete")
    # windows
    sides = {"n": (z1, "x"), "s": (z2, "x"), "w": (x1, "z"), "e": (x2, "z")}
    for f, y in enumerate(ys):
        for sd in win:
            line, along = sides[sd]
            a1, a2 = (x1, x2) if along == "x" else (z1, z2)
            n = a2 - a1 - 3
            if n < 1:
                continue
            for a in range(a1 + 2, a2 - 1):
                if glassy:
                    if (a - a1) % 4 == 0:
                        continue
                elif (a - a1 - 2) % ws != 0:
                    continue
                x, z = (a, line) if along == "x" else (line, a)
                h2 = wh - 1 if glassy or d.pack == "Neoterra" else 2
                for yy in range(y + 1, y + 1 + h2):
                    d.set(x, yy, z, S["glass"] if d.pack != "Neoterra" or f == 0 else "light_gray_stained_glass_pane"
                          if glassy else S["glass"])
                if not deco:
                    continue
                ox, oz = D4[OUT[sd]]
                if d.pack == "Neoterra":
                    if not glassy:
                        put(d, x + ox, y + wh - 1 + 1, z + oz, slab("smooth_quartz_slab", "top")) if False else None
                    continue
                if f == 0:                                          # ground floor: hood moulding only (keeps the
                    put(d, x + ox, y + 3, z + oz, st(f"{S['wood']}_stairs" if d.pack == "Cascadia" else  # pavement free)
                                                    "stone_brick_stairs", OPP[OUT[sd]], "top"))
                    continue
                put(d, x + ox, y, z + oz, f"{S['sill']}[facing={OUT[sd]},half=top,open=false,powered=false,waterlogged=false]")
                if d.pack == "Hearthwood":
                    put(d, x + ox, y + 1, z + oz, "potted_" + S["flowers"][(x + z) % 4])
                lx, lz = D4[CW[OUT[sd]]]
                for s in (1, -1):
                    for yy in range(y + 1, y + 3):
                        put(d, x + lx * s + ox, yy, z + lz * s + oz,
                            f"{S['shutter']}[facing={OUT[sd]},half=bottom,open=true,powered=false,waterlogged=false]")
    # roof
    ridge = top
    if roof == "gable":
        ridge = d.gable(x1, z1, x2, z2, top + 1, axis, f"{S['roof']}_stairs",
                        f"{S['roof']}_slab", gable_end or (up if d.pack != "Cascadia" else "spruce_planks"), overhang=1)
        # gable-end detail: king post (HW) / board and batten (CS), small window
        ends = ((x1, (z1 + z2) // 2), (x2, (z1 + z2) // 2)) if axis == "x" else (((x1 + x2) // 2, z1), ((x1 + x2) // 2, z2))
        for ex, ez in ends:
            for yy in range(top + 1, ridge):
                if d.pack == "Hearthwood" and not d.get(ex, yy, ez).endswith("stairs]") and "stairs" not in d.get(ex, yy, ez):
                    d.set(ex, yy, ez, log(S["post"]))
            if ridge - top >= 4:
                d.set(ex, top + 2, ez, S["glass"])
        if d.pack == "Cascadia":
            for yy in range(top + 1, ridge):
                for a in range((x1 if axis == "z" else z1), (x2 if axis == "z" else z2) + 1):
                    for e in ((z1, z2) if axis == "z" else (x1, x2)):
                        x, z = (a, e) if axis == "z" else (e, a)
                        if d.get(x, yy, z) == "minecraft:spruce_planks" and a % 2 == 0:
                            d.set(x, yy, z, log("stripped_spruce_log"))
        # eave brackets under the overhang on the long sides
        if deco:
            if axis == "x":
                for x in range(x1, x2 + 1, 2):
                    put(d, x, top, z1 - 1, st(f"{S['wood']}_stairs", "south", "top"))
                    put(d, x, top, z2 + 1, st(f"{S['wood']}_stairs", "north", "top"))
            else:
                for z in range(z1, z2 + 1, 2):
                    put(d, x1 - 1, top, z, st(f"{S['wood']}_stairs", "east", "top"))
                    put(d, x2 + 1, top, z, st(f"{S['wood']}_stairs", "west", "top"))
        if beams_on:
            beams(d, x1 + 1, x2 - 1, z1 + 1, z2 - 1, top + 1, S["post"] if d.pack != "Neoterra" else "smooth_quartz",
                  every=4, axis="z" if axis == "x" else "x") if False else None
            if axis == "x":
                for x in range(x1 + 2, x2 - 1, 4):
                    for z in range(z1 + 1, z2):
                        d.set(x, top + 1, z, log(S["post"], "z"))
                    d.set(x, top, (z1 + z2) // 2, "lantern[hanging=true,waterlogged=false]")
            else:
                for z in range(z1 + 2, z2 - 1, 4):
                    for x in range(x1 + 1, x2):
                        d.set(x, top + 1, z, log(S["post"], "x"))
                    d.set((x1 + x2) // 2, top, z, "lantern[hanging=true,waterlogged=false]")
    elif roof == "hip":
        ridge = d.hip(x1, z1, x2, z2, top + 1, f"{S['roof']}_stairs", f"{S['roof']}_slab", overhang=1)
        for x in range(x1 + 2, x2 - 1, 4):
            for z in range(z1 + 2, z2 - 1, 4):
                d.set(x, top + 1, z, d.S["band"] if d.pack != "Cascadia" else "spruce_planks")
                d.set(x, top, z, "lantern[hanging=true,waterlogged=false]")
    else:
        d.fill(x1, top + 1, z1, x2, top + 1, z2, "smooth_quartz" if d.pack == "Neoterra" else S["band"])
        if parapet:
            for x in range(x1, x2 + 1):
                for z in range(z1, z2 + 1):
                    if x in (x1, x2) or z in (z1, z2):
                        d.set(x, top + 2, z, "white_concrete" if d.pack == "Neoterra" else S["base"])
                        d.set(x, top + 3, z, slab("smooth_quartz_slab") if d.pack == "Neoterra" else
                              ("stone_brick_slab[type=bottom,waterlogged=false]" if (x + z) % 2 else "stone_bricks"))
        for x in range(x1, x2 + 1):                                 # cantilevered roof edge
            for z in (z1 - 1, z2 + 1):
                put(d, x, top + 1, z, slab("smooth_quartz_slab", "top") if d.pack == "Neoterra" else slab("stone_brick_slab", "top"))
        for z in range(z1, z2 + 1):
            for x in (x1 - 1, x2 + 1):
                put(d, x, top + 1, z, slab("smooth_quartz_slab", "top") if d.pack == "Neoterra" else slab("stone_brick_slab", "top"))
        for x in range(x1 + 2, x2 - 1, 4):
            for z in range(z1 + 2, z2 - 1, 4):
                d.set(x, top + 1, z, "sea_lantern" if d.pack == "Neoterra" else "glowstone")
        ridge = top + 1
    # lights on lower floors
    for f, y in enumerate(ys[:-1]):
        for x in range(x1 + 2, x2 - 1, 4):
            for z in range(z1 + 2, z2 - 1, 4):
                if d.pack == "Neoterra":
                    d.set(x, y + wh, z, "sea_lantern")
                else:
                    d.set(x, y + wh - 1, z, "lantern[hanging=true,waterlogged=false]")
    return dict(ys=ys, top=top, ridge=ridge, x1=x1, z1=z1, x2=x2, z2=z2)


def ext_door(d, x, y, z, facing, wood=None, double=False, along="x", step=True, lamp=True):
    """Exterior door in a wall; facing = the inside direction (doors face into the room as in hm)."""
    wood = wood or d.S["wood"]
    if double:
        d.double_door(x, y, z, along, facing, wood)
    else:
        d.door(x, y, z, facing, wood)
    ox, oz = D4[OPP[facing]]
    cells = [(x, z)] + ([(x + (1 if along == "x" else 0), z + (1 if along == "z" else 0))] if double else [])
    for cx, cz in cells:
        for k in range(3):
            for sgn in (1, -1):
                if d.bp.inside(cx + ox * sgn, y + k, cz + oz * sgn):
                    d.set(cx + ox * sgn, y + k, cz + oz * sgn, AIR)
        keep(d, cx + ox, y, cz + oz, 3)
        keep(d, cx - ox, y, cz - oz, 3)
        d.set(cx + ox, 1, cz + oz, d.S["base"] if d.pack != "Cascadia" else "spruce_planks")
    if lamp:
        lx, lz = D4[CW[facing]]
        far = cells[-1]
        put(d, x - lx + ox, y + 2, z - lz + oz, "lantern[hanging=false,waterlogged=false]") if False else None
        wt = OPP[facing]
        for (cx, cz), s in ((cells[0], -1), (far, 1)):
            px, pz = cx + lx * s, cz + lz * s
            if d.get(px, y + 2, pz) not in (AIR,) and not d.get(px, y + 2, pz).endswith("pane"):
                put(d, px + ox, y + 2, pz + oz, f"wall_torch[facing={wt}]" if d.pack != "Neoterra" else
                    f"end_rod[facing={wt}]")


def link(d, x, y, z, facing, wood=None):
    """Interior door through a wall cell (facing = direction of travel into the next room)."""
    wood = wood or d.S["wood"]
    d.set(x, y, z, AIR)
    d.set(x, y + 1, z, AIR)
    d.door(x, y, z, facing, wood)
    ox, oz = D4[facing]
    for k in range(3):
        for sgn in (1, -1):
            d.set(x + ox * sgn, y + k, z + oz * sgn, AIR)
    keep(d, x + ox, y, z + oz, 3)
    keep(d, x - ox, y, z - oz, 3)
    keep(d, x, y, z, 2)


def arch(d, x, y, z, facing, h=3):
    """Open archway (no door) through a wall cell."""
    for k in range(h):
        d.set(x, y + k, z, AIR)
    ox, oz = D4[facing]
    keep(d, x + ox, y, z + oz, 3)
    keep(d, x - ox, y, z - oz, 3)
    keep(d, x, y, z, 3)


def stair_up(d, x, z, y0, yU, rise, block=None, rails=True):
    """Flight between storeys, reserving the approach and landing; railings on the upper floor along the hole."""
    block = block or (f"{d.S['wood']}_stairs" if d.pack != "Neoterra" else "smooth_quartz_stairs")
    dx, dz = D4[rise]
    n = yU - y0
    keep(d, x - dx, y0, z - dz, 3)
    lx, lz = flight(d, x, z, y0, yU, rise, block, under=d.S["floor"] if d.pack != "Neoterra" else "smooth_quartz")
    keep(d, lx, yU, lz, 3)
    for i in range(n):
        keep(d, x + dx * i, y0 + i + 1, z + dz * i, 3)
    for i in range(max(0, n - 4), n):
        keep(d, x + dx * i, yU, z + dz * i, 2)
    if rails:
        sx, sz = D4[CW[rise]]
        fence = f"{d.S['wood']}_fence" if d.pack != "Neoterra" else "glass_pane"
        for i in range(max(0, n - 4), n):
            for s in (1, -1):
                cx, cz = x + dx * i + sx * s, z + dz * i + sz * s
                if d.bp.inside(cx, yU - 1, cz) and d.get(cx, yU - 1, cz) != AIR and d.air(cx, yU, cz):
                    put(d, cx, yU, cz, fence)
    return lx, lz


# ------------------------------------------------------------------------------------------------ furnishers
def R(x1, z1, x2, z2):
    return (x1, z1, x2, z2)


def wall_cells(r, side, inset=0):
    x1, z1, x2, z2 = r
    if side == "n":
        return [(x, z1 + inset) for x in range(x1, x2 + 1)]
    if side == "s":
        return [(x, z2 - inset) for x in range(x1, x2 + 1)]
    if side == "w":
        return [(x1 + inset, z) for z in range(z1, z2 + 1)]
    return [(x2 - inset, z) for z in range(z1, z2 + 1)]


def lights(d, r, y, h=4, every=4):
    x1, z1, x2, z2 = r
    for x in range(x1 + 1, x2, every):
        for z in range(z1 + 1, z2, every):
            if d.pack == "Neoterra":
                if d.get(x, y + h, z) not in (AIR,):
                    d.set(x, y + h, z, "sea_lantern")
            elif d.get(x, y + h, z) != AIR:
                put(d, x, y + h - 1, z, "lantern[hanging=true,waterlogged=false]")


def rug_in(d, r, y, colors=None, inset=1, pattern="border"):
    x1, z1, x2, z2 = r
    c = colors or d.S["rug"]
    for x in range(x1 + inset, x2 - inset + 1):
        for z in range(z1 + inset, z2 - inset + 1):
            k = 0 if pattern == "plain" else (0 if x in (x1 + inset, x2 - inset) or z in (z1 + inset, z2 - inset) else 1)
            put(d, x, y, z, c[k % len(c)])


def wall_art(d, r, y, sides="nesw", colors=("red", "blue")):
    """Banners / framed signs on solid wall cells at eye height (skip windows)."""
    x1, z1, x2, z2 = r
    i = 0
    for sd in sides:
        face = OPP[OUT[sd]]
        ox, oz = D4[OUT[sd]]
        cells = wall_cells(r, sd)
        for k, (x, z) in enumerate(cells[1:-1]):
            if k % 4 != 1:
                continue
            behind = d.get(x + ox, y + 2, z + oz)
            if behind == AIR or "pane" in behind or "door" in behind or "glass" in behind:
                continue
            if i % 2 == 0:
                put(d, x, y + 2, z, f"{colors[i // 2 % len(colors)]}_wall_banner[facing={face}]")
            else:
                put(d, x, y + 2, z, f"{d.S['wood']}_trapdoor[facing={face},half=bottom,open=true,powered=false,waterlogged=false]")
            i += 1


def corners(d, r, y, blocks=None):
    x1, z1, x2, z2 = r
    blocks = blocks or ["potted_" + f for f in d.S["flowers"]]
    for i, (x, z) in enumerate(((x1, z1), (x2, z1), (x1, z2), (x2, z2))):
        put(d, x, y, z, blocks[i % len(blocks)] if not blocks[i % len(blocks)].startswith("potted_cactus")
            else "potted_cactus")


def shelf_wall(d, r, side, y, h=3, chisel=True, skip=()):
    """Book wall: bookshelves (counted), chiseled bookshelves every 4th column for variety."""
    x1, z1, x2, z2 = r
    face = OPP[OUT[side]]
    for k, (x, z) in enumerate(wall_cells(r, side)):
        if (x, z) in skip:
            continue
        for yy in range(y, y + h):
            if (x, yy, z) in d.res or not d.air(x, yy, z):
                continue
            if chisel and k % 4 == 3 and yy == y + 1:
                d.set(x, yy, z, f"chiseled_bookshelf[facing={face},slot_0_occupied=true,slot_1_occupied=true,"
                                f"slot_2_occupied=false,slot_3_occupied=true,slot_4_occupied=false,slot_5_occupied=true]")
            else:
                d.bookshelf(x, yy, z)


def desk(d, x, y, z, chair_side, wood=None, sit=True, deco="candle"):
    wood = wood or d.S["wood"]
    if not put(d, x, y, z, slab(f"{wood}_slab", "top") if d.pack != "Neoterra" else slab("smooth_quartz_slab", "top")):
        return
    ox, oz = D4[chair_side]
    if d.air(x + ox, y, z + oz) and (x + ox, y, z + oz) not in d.res:
        d.chair(x + ox, y, z + oz, chair_side, wood, sit=sit)
    if deco == "candle":
        put(d, x, y + 1, z, "candle[candles=2,lit=false,waterlogged=false]")
    elif deco:
        put(d, x, y + 1, z, deco)


def office(d, r, y, h=4, desk_side="n"):
    x1, z1, x2, z2 = r
    cx = (x1 + x2) // 2
    if desk_side == "n":
        desk(d, cx, y, z1 + 1, "south", deco="candle")
        desk(d, cx + 1, y, z1 + 1, "south", deco="potted_" + d.S["flowers"][0] if d.S["flowers"][0] != "bamboo" else "potted_bamboo")
        shelf_wall(d, r, "s", y, 2)
    else:
        desk(d, cx, y, z2 - 1, "north")
        desk(d, cx + 1, y, z2 - 1, "north", deco="flower_pot")
        shelf_wall(d, r, "n", y, 2)
    corners(d, r, y)
    wall_art(d, r, y)
    rug_in(d, r, y)
    lights(d, r, y, h)


def dorm(d, r, y, n, h=4, head="w", color=None, desks=True):
    """Beds with heads against one long wall and nightstands between; wardrobe chests opposite."""
    x1, z1, x2, z2 = r
    color = color or d.S["bed"]
    placed = 0
    if head in ("w", "e"):
        hx = x1 if head == "w" else x2
        for z in range(z1, z2 + 1, 2):
            if placed >= n:
                break
            if not (d.air(hx, y, z) and d.air(hx + (1 if head == "w" else -1), y, z)) or (hx, y, z) in d.res:
                continue
            d.bed(hx, y, z, OUT[head], color)
            placed += 1
            if z + 1 <= z2:
                put(d, hx, y, z + 1, slab(f"{d.S['wood']}_slab", "top") if d.pack != "Neoterra" else "white_concrete")
                put(d, hx, y + 1, z + 1, "candle[candles=1,lit=false,waterlogged=false]" if d.pack != "Neoterra" else "end_rod[facing=up]")
        ox = x2 if head == "w" else x1
        for z in range(z1, z2 + 1, 3):
            put(d, ox, y, z, f"chest[facing={'west' if head == 'w' else 'east'},type=single,waterlogged=false]")
            if desks:
                desk(d, ox, y, z + 1, "west" if head == "w" else "east", sit=False, deco="flower_pot")
    else:
        hz = z1 if head == "n" else z2
        for x in range(x1, x2 + 1, 2):
            if placed >= n:
                break
            if not (d.air(x, y, hz) and d.air(x, y, hz + (1 if head == "n" else -1))) or (x, y, hz) in d.res:
                continue
            d.bed(x, y, hz, OUT[head], color)
            placed += 1
            if x + 1 <= x2:
                put(d, x + 1, y, hz, slab(f"{d.S['wood']}_slab", "top") if d.pack != "Neoterra" else "white_concrete")
                put(d, x + 1, y + 1, hz, "candle[candles=1,lit=false,waterlogged=false]" if d.pack != "Neoterra" else "end_rod[facing=up]")
        oz = z2 if head == "n" else z1
        for x in range(x1, x2 + 1, 3):
            put(d, x, y, oz, f"chest[facing={'north' if head == 'n' else 'south'},type=single,waterlogged=false]")
            if desks:
                desk(d, x + 1, y, oz, "north" if head == "n" else "south", sit=False, deco="flower_pot")
    rug_in(d, r, y, inset=1 if (x2 - x1 > 3 and z2 - z1 > 3) else 0, pattern="plain")
    wall_art(d, r, y)
    lights(d, r, y, h)
    return placed


def tables(d, r, y, kind="dining", step=4, wood=None, sit=True, top=None):
    """Grid of 4-seat tables (or long tables) filling a room with aisles."""
    x1, z1, x2, z2 = r
    wood = wood or d.S["wood"]
    n = 0
    for tz in range(z1 + 1, z2, step):
        for tx in range(x1 + 1, x2, step):
            cells = [(tx + a, tz + b) for a in (-1, 0, 1) for b in (-1, 0, 1)]
            if not all(x1 <= cx <= x2 and z1 <= cz <= z2 and d.air(cx, y, cz) and (cx, y, cz) not in d.res
                       and d.air(cx, y + 1, cz) for cx, cz in cells):
                continue
            if top:
                d.table(tx, y, tz, wood, "block", top)
            else:
                d.table(tx, y, tz, wood, "post")
            for side, (dx, dz) in D4.items():
                d.chair(tx + dx, y, tz + dz, side, wood, sit=sit)
                n += 1
    return n


def long_table(d, x1, z, x2, y, wood=None, sit=True, top=None, ends=True, deco=True):
    wood = wood or d.S["wood"]
    n = 0
    for x in range(x1, x2 + 1):
        d.table(x, y, z, wood, "block", top or f"{d.S['wood']}_planks" if d.pack != "Neoterra" else top or "smooth_quartz")
        for dz, back in ((-1, "north"), (1, "south")):
            if d.air(x, y, z + dz) and (x, y, z + dz) not in d.res:
                d.chair(x, y, z + dz, back, wood, sit=sit)
                n += 1
        if deco and x % 2 == 0:
            put(d, x, y + 1, z, "candle[candles=3,lit=false,waterlogged=false]" if x % 4 == 0 else "flower_pot")
    if ends:
        for x, back in ((x1 - 1, "west"), (x2 + 1, "east")):
            if d.air(x, y, z) and (x, y, z) not in d.res:
                d.chair(x, y, z, back, wood, sit=sit)
                n += 1
    return n


def long_table_z(d, x, z1, z2, y, wood=None, sit=True, top=None):
    wood = wood or d.S["wood"]
    n = 0
    for z in range(z1, z2 + 1):
        d.table(x, y, z, wood, "block", top or (f"{wood}_planks" if d.pack != "Neoterra" else "smooth_quartz"))
        for dx, back in ((-1, "west"), (1, "east")):
            if d.air(x + dx, y, z) and (x + dx, y, z) not in d.res:
                d.chair(x + dx, y, z, back, wood, sit=sit)
                n += 1
        if z % 3 == 0:
            put(d, x, y + 1, z, "candle[candles=3,lit=false,waterlogged=false]")
    return n


def classroom(d, r, y, board="n", need=None, wood=None, teacher_spot=False, h=4):
    """Board on one wall, teacher's desk in front, rows of desk+chair facing it, shelves at the back."""
    x1, z1, x2, z2 = r
    wood = wood or d.S["wood"]
    bb = "black_concrete" if d.pack != "Neoterra" else "gray_concrete"
    top = f"{wood}_slab" if d.pack != "Neoterra" else "smooth_quartz_slab"
    n = 0
    if board in ("n", "s"):
        bz = z1 if board == "n" else z2
        cx = (x1 + x2) // 2
        blackboard(d, cx - 2, bz, cx + 2, bz, y + 1, OPP[OUT[board]], bb, wood if d.pack != "Neoterra" else "birch")
        tz = bz + (2 if board == "n" else -2)
        put(d, cx, y, tz, slab(top, "top"))
        put(d, cx + 1, y, tz, slab(top, "top"))
        put(d, cx + 1, y + 1, tz, "candle[candles=1,lit=false,waterlogged=false]")
        sz = bz + (1 if board == "n" else -1)
        if teacher_spot:
            d.spot(cx, y, sz, "work")
            keep(d, cx, y, sz)
        d.chair(cx + 1, y, sz, OUT[board], wood, sit=False)
        n += desk_rows(d, x1 + 1, x2 - 1, (tz + 2) if board == "n" else z1 + 1, z2 - 1 if board == "n" else tz - 2,
                       y, OUT[board], wood, top, every_x=3, need=need)
        shelf_wall(d, (x1, z1, x2, z2), "s" if board == "n" else "n", y, 1, chisel=False)
    else:
        bx = x1 if board == "w" else x2
        cz = (z1 + z2) // 2
        blackboard(d, bx, cz - 2, bx, cz + 2, y + 1, OPP[OUT[board]], bb, wood if d.pack != "Neoterra" else "birch")
        tx = bx + (2 if board == "w" else -2)
        put(d, tx, y, cz, slab(top, "top"))
        put(d, tx, y, cz + 1, slab(top, "top"))
        put(d, tx, y + 1, cz + 1, "candle[candles=1,lit=false,waterlogged=false]")
        sx = bx + (1 if board == "w" else -1)
        if teacher_spot:
            d.spot(sx, y, cz, "work")
            keep(d, sx, y, cz)
        d.chair(sx, y, cz + 1, OUT[board], wood, sit=False)
        n += desk_rows(d, (tx + 2) if board == "w" else x1 + 1, x2 - 1 if board == "w" else tx - 2, z1 + 1, z2 - 1,
                       y, OUT[board], wood, top, every_x=3, need=need)
        shelf_wall(d, (x1, z1, x2, z2), "e" if board == "w" else "w", y, 1, chisel=False)
    corners(d, r, y)
    wall_art(d, r, y, colors=("yellow", "lime", "light_blue"))
    lights(d, r, y, h)
    return n


def lab(d, r, y, h=4, req=()):
    """Laboratory: required work blocks along one wall, a central bench with flasks, cauldrons, shelves."""
    x1, z1, x2, z2 = r
    for i, (it, x, z, f) in enumerate(req):
        if it == "water_cauldron":
            d.item(x, y, z, "water_cauldron[level=3]")
        else:
            d.item(x, y, z, it, f)
    bench_top = "smooth_stone_slab" if d.pack != "Neoterra" else "smooth_quartz_slab"
    cz = (z1 + z2) // 2
    for x in range(x1 + 2, x2 - 1):
        if put(d, x, y, cz, slab(bench_top, "top")):
            put(d, x, y + 1, cz, ("brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]",
                                  "flower_pot", "candle[candles=3,lit=false,waterlogged=false]", "decorated_pot[cracked=false,facing=north,waterlogged=false]")[x % 4])
    for x in range(x1 + 2, x2 - 1, 2):
        if d.get(x, y, cz).startswith("minecraft:" + bench_top):
            if d.air(x, y, cz + 1) and (x, y, cz + 1) not in d.res:
                d.chair(x, y, cz + 1, "south", d.S["wood"], sit=False)
    for (x, z) in wall_cells(r, "n")[1:-1]:
        if (x, y, z) not in d.res and d.air(x, y, z):
            if x % 3 == 0:
                d.set(x, y, z, "cauldron")
            elif x % 3 == 1:
                d.set(x, y, z, slab(bench_top, "top"))
                put(d, x, y + 1, z, "potted_" + ("red_mushroom" if x % 2 else "brown_mushroom"))
    corners(d, r, y, ["potted_fern", "potted_dead_bush"])
    lights(d, r, y, h)


def lecture(d, r, y, front="w", need=None, h=4, lectern=False):
    """Lecture hall: benches in rows facing the front wall with a lectern platform and a board."""
    x1, z1, x2, z2 = r
    wood = d.S["wood"]
    bb = "black_concrete" if d.pack != "Neoterra" else "gray_concrete"
    n = 0
    if front in ("w", "e"):
        fx = x1 if front == "w" else x2
        cz = (z1 + z2) // 2
        blackboard(d, fx, cz - 2, fx, cz + 2, y + 1, OPP[OUT[front]], bb, wood if d.pack != "Neoterra" else "birch")
        lx = fx + (2 if front == "w" else -2)
        if lectern:
            d.item(lx, y, cz, "lectern", OPP[OUT[front]] if False else OUT[OPP[front[0]]] if False else
                   ("east" if front == "w" else "west"))
            keep(d, lx + (1 if front == "w" else -1), y, cz)
        else:
            put(d, lx, y, cz, f"{wood}_planks" if d.pack != "Neoterra" else "smooth_quartz")
        rng = range(lx + 3, x2, 2) if front == "w" else range(lx - 3, x1, -2)
        for x in rng:
            for z in range(z1, z2 + 1):
                if z == cz:
                    continue
                if need is not None and n >= need:
                    break
                if d.air(x, y, z) and (x, y, z) not in d.res:
                    d.chair(x, y, z, OUT[OPP[front][0]] if False else ("east" if front == "w" else "west"), wood)
                    n += 1
    else:
        fz = z1 if front == "n" else z2
        cx = (x1 + x2) // 2
        blackboard(d, cx - 2, fz, cx + 2, fz, y + 1, OPP[OUT[front]], bb, wood if d.pack != "Neoterra" else "birch")
        lz = fz + (2 if front == "n" else -2)
        if lectern:
            d.item(cx, y, lz, "lectern", "south" if front == "n" else "north")
            keep(d, cx, y, lz + (1 if front == "n" else -1))
        else:
            put(d, cx, y, lz, f"{wood}_planks" if d.pack != "Neoterra" else "smooth_quartz")
        rng = range(lz + 3, z2, 2) if front == "n" else range(lz - 3, z1, -2)
        for z in rng:
            for x in range(x1, x2 + 1):
                if x == cx:
                    continue
                if need is not None and n >= need:
                    break
                if d.air(x, y, z) and (x, y, z) not in d.res:
                    d.chair(x, y, z, "south" if front == "n" else "north", wood)
                    n += 1
    wall_art(d, r, y, colors=("blue", "white"))
    lights(d, r, y, h)
    return n


def store(d, r, y, h=2, aisle="z"):
    """Store room: barrel shelving two high along the long walls, crates (barrels) and sacks."""
    x1, z1, x2, z2 = r
    sides = ("w", "e") if aisle == "z" else ("n", "s")
    for sd in sides:
        face = OPP[OUT[sd]]
        for (x, z) in wall_cells(r, sd):
            for k in range(h):
                if (x, y + k, z) not in d.res and d.air(x, y + k, z) and (k == 0 or not d.air(x, y, z)):
                    d.set(x, y + k, z, f"barrel[facing={face},open=false]")
    for (x, z) in wall_cells(r, "n" if aisle == "z" else "w")[1:-1:2]:
        put(d, x, y, z, "white_wool" if (x + z) % 2 else "brown_wool")
    lights(d, r, y, 4)


def workshop(d, r, y, h=4):
    x1, z1, x2, z2 = r
    cycle = ["crafting_table", "smithing_table", "stonecutter[facing=north]" if False else "fletching_table",
             "loom[facing=north]", "grindstone[face=floor,facing=north]"]
    for i, (x, z) in enumerate(wall_cells(r, "n")[1:-1]):
        if i % 2 == 0 and (x, y, z) not in d.res and d.air(x, y, z) and (x, y, z + 1) not in d.res:
            d.set(x, y, z, cycle[(i // 2) % len(cycle)])
            keep(d, x, y, z + 1)
    cz = (z1 + z2) // 2
    for x in range(x1 + 2, x2 - 1):
        if put(d, x, y, cz, slab(f"{d.S['wood']}_slab", "top") if d.pack != "Neoterra" else slab("smooth_quartz_slab", "top")):
            put(d, x, y + 1, cz, ("flower_pot", "candle[candles=2,lit=false,waterlogged=false]", AIR)[x % 3]) if x % 3 < 2 else None
    lights(d, r, y, h)


def kitchen(d, r, y, h=4):
    x1, z1, x2, z2 = r
    top = "smooth_stone_slab" if d.pack != "Neoterra" else "smooth_quartz_slab"
    for i, (x, z) in enumerate(wall_cells(r, "n")[1:-1]):
        if (x, y, z) in d.res or not d.air(x, y, z):
            continue
        b = ("smoker[facing=south,lit=true]", slab(top, "top"), "water_cauldron[level=3]", slab(top, "top"),
             "furnace[facing=south,lit=false]", slab(top, "top"))[i % 6]
        d.set(x, y, z, b)
        keep(d, x, y, z + 1)
        if b.startswith(slab(top, "top")[:20]) and "slab" in b:
            put(d, x, y + 1, z, ("flower_pot", "candle[candles=1,lit=false,waterlogged=false]")[i % 2])
    cx, cz = (x1 + x2) // 2, (z1 + z2) // 2 + 1
    for x in range(cx - 1, cx + 2):
        put(d, x, y, cz, f"{d.S['wood']}_planks" if d.pack != "Neoterra" else "smooth_quartz")
        put(d, x, y + 1, cz, ("cake[bites=0]", "flower_pot", "candle[candles=2,lit=false,waterlogged=false]")[x % 3])
    lights(d, r, y, h)


def ward(d, r, y, n, head=("n", "s"), h=4, color="white"):
    x1, z1, x2, z2 = r
    placed = 0
    for hd in head:
        if placed >= n:
            break
        if hd in ("n", "s"):
            placed += ward_row(d, x1, x2, z1 if hd == "n" else z2, y, OUT[hd], color, n - placed)
        else:
            placed += ward_col(d, x1 if hd == "w" else x2, z1, z2, y, OUT[hd], color, n - placed)
    rug_in(d, r, y, ("white_carpet",) if d.pack != "Cascadia" else ("green_carpet",), inset=2, pattern="plain")
    lights(d, r, y, h)
    return placed


def lounge(d, r, y, h=4):
    """Waiting room / common room: sofas (stairs) round a low table, plants, rug, art."""
    x1, z1, x2, z2 = r
    wood = d.S["wood"]
    cx, cz = (x1 + x2) // 2, (z1 + z2) // 2
    for x in range(cx - 1, cx + 2):
        if d.air(x, y, cz - 1) and (x, y, cz - 1) not in d.res:
            d.chair(x, y, cz - 1, "north", wood)
        if d.air(x, y, cz + 1) and (x, y, cz + 1) not in d.res:
            d.chair(x, y, cz + 1, "south", wood)
    put(d, cx, y, cz, f"{wood}_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
    put(d, cx, y + 1, cz, "potted_" + d.S["flowers"][1])
    rug_in(d, (cx - 2, cz - 2, cx + 2, cz + 2), y, inset=0)
    corners(d, r, y)
    wall_art(d, r, y)
    lights(d, r, y, h)


# ------------------------------------------------------------------------------------------------ outdoors
def lawn(d, x1, z1, x2, z2, mat="grass_block[snowy=false]"):
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if d.get(x, 1, z) != AIR and d.air(x, 2, z):
                d.set(x, 1, z, mat)


def path(d, x1, z1, x2, z2, mat=None, border=True):
    mat = mat or d.S["path"]
    for x in range(min(x1, x2), max(x1, x2) + 1):
        for z in range(min(z1, z2), max(z1, z2) + 1):
            d.set(x, 1, z, mat)
    if border:
        b = {"Hearthwood": "stone_bricks", "Cascadia": "cobblestone", "Neoterra": "polished_andesite"}[d.pack]
        if x1 == x2 or z1 == z2 or True:
            for x in range(min(x1, x2) - 1, max(x1, x2) + 2):
                for z in range(min(z1, z2) - 1, max(z1, z2) + 2):
                    if (x < min(x1, x2) or x > max(x1, x2) or z < min(z1, z2) or z > max(z1, z2)) and \
                            d.bp.inside(x, 1, z) and d.get(x, 1, z).startswith("minecraft:grass_block"):
                        d.set(x, 1, z, b)


def flowerbed(d, x1, z1, x2, z2, flowers=None):
    flowers = flowers or ("poppy", "dandelion", "azure_bluet", "oxeye_daisy", "cornflower", "allium")
    for x in range(min(x1, x2), max(x1, x2) + 1):
        for z in range(min(z1, z2), max(z1, z2) + 1):
            if d.air(x, 2, z) and (x, 2, z) not in d.res:
                d.set(x, 1, z, "grass_block[snowy=false]")
                d.set(x, 2, z, flowers[(x * 3 + z) % len(flowers)])


def hedge(d, x1, z1, x2, z2, leaves="oak_leaves"):
    for x in range(min(x1, x2), max(x1, x2) + 1):
        for z in range(min(z1, z2), max(z1, z2) + 1):
            put(d, x, 2, z, f"{leaves}[distance=1,persistent=true,waterlogged=false]")


def post_lamp(d, x, z, kind=None):
    if d.pack == "Neoterra":
        put(d, x, 2, z, "light_gray_concrete_powder") if False else None
        for k, b in enumerate(("birch_fence", "birch_fence", "birch_fence", "sea_lantern")):
            put(d, x, 2 + k, z, b)
    elif d.pack == "Hearthwood":
        for k, b in enumerate(("stone_brick_wall", "dark_oak_fence", "dark_oak_fence", "lantern[hanging=false,waterlogged=false]")):
            put(d, x, 2 + k, z, b)
    else:
        for k, b in enumerate(("spruce_log[axis=y]", "spruce_fence", "spruce_fence", "lantern[hanging=false,waterlogged=false]")):
            put(d, x, 2 + k, z, b)


def park_bench(d, x, z, along, back, tag=None):
    wood = d.S["wood"]
    dx, dz = (1, 0) if along == "x" else (0, 1)
    for k in range(2):
        cx, cz = x + dx * k, z + dz * k
        if d.air(cx, 2, cz) and (cx, 2, cz) not in d.res:
            d.chair(cx, 2, cz, back, wood, sit=(tag == "sit"))
            if tag and tag != "sit":
                d.tag(cx, 2, cz, tag)
    for s in (-1, 2):
        put(d, x + dx * s, 2, z + dz * s, f"{wood}_trapdoor[facing={back},half=bottom,open=true,powered=false,waterlogged=false]") if False else None


def plant_tree(d, x, z, kind=None):
    kind = kind or {"Hearthwood": "oak", "Cascadia": "spruce", "Neoterra": "birch"}[d.pack]
    if not d.air(x, 2, z):
        return
    d.set(x, 1, z, "grass_block[snowy=false]")
    if kind == "spruce":
        h = 6
        for k in range(h):
            d.set(x, 2 + k, z, log("spruce_log"))
        for y, r in ((4, 2), (5, 1), (6, 2), (7, 1), (8, 0)):
            for a in range(-r, r + 1):
                for b in range(-r, r + 1):
                    if abs(a) + abs(b) <= r + (1 if r == 2 else 0) and d.air(x + a, y, z + b):
                        put(d, x + a, y, z + b, "spruce_leaves[distance=1,persistent=true,waterlogged=false]")
        put(d, x, 8, z, "spruce_leaves[distance=1,persistent=true,waterlogged=false]")
    else:
        tree(d, x, 2, z, f"{kind}_log", f"{kind}_leaves", 4 if kind == "birch" else 5, 2)


def fountain(d, cx, cz, r=2):
    rim = {"Hearthwood": "stone_brick_wall", "Cascadia": "mossy_cobblestone_wall", "Neoterra": "smooth_quartz_slab[type=bottom,waterlogged=false]"}[d.pack]
    for x in range(cx - r, cx + r + 1):
        for z in range(cz - r, cz + r + 1):
            if x in (cx - r, cx + r) or z in (cz - r, cz + r):
                d.set(x, 2, z, rim)
                d.set(x, 1, z, {"Hearthwood": "stone_bricks", "Cascadia": "cobblestone", "Neoterra": "smooth_quartz"}[d.pack])
            else:
                d.set(x, 1, z, "stone_bricks" if d.pack != "Neoterra" else "light_blue_concrete")
                d.set(x, 2, z, "water[level=0]")
    d.set(cx, 2, cz, {"Hearthwood": "stone_bricks", "Cascadia": "mossy_cobblestone", "Neoterra": "smooth_quartz"}[d.pack])
    d.set(cx, 3, cz, {"Hearthwood": "stone_brick_wall", "Cascadia": "mossy_cobblestone_wall", "Neoterra": "end_rod[facing=up]"}[d.pack])
    d.set(cx, 4, cz, "water[level=0]" if d.pack != "Neoterra" else "sea_lantern") if d.pack == "Neoterra" else \
        d.set(cx, 4, cz, "lantern[hanging=false,waterlogged=false]")


def chimney(d, x, z, y1, y2, mat=None):
    mat = mat or {"Hearthwood": "bricks", "Cascadia": "cobblestone", "Neoterra": "light_gray_concrete"}[d.pack]
    for y in range(y1, y2 + 1):
        d.set(x, y, z, mat if not (d.pack == "Cascadia" and y % 3 == 0) else "mossy_cobblestone")
    d.set(x, y2 + 1, z, {"Hearthwood": "brick_wall", "Cascadia": "cobblestone_wall", "Neoterra": "iron_bars"}[d.pack])
    d.set(x, y2 + 2, z, "campfire[facing=north,lit=false,signal_fire=false,waterlogged=false]") if False else None


def cart(d, x, z, along="x"):
    """Hand cart: two wheels (dark trapdoors), bed of slabs, a sack."""
    wood = d.S["wood"] if d.pack != "Neoterra" else "spruce"
    dx, dz = (1, 0) if along == "x" else (0, 1)
    put(d, x, 2, z, slab(f"{wood}_slab", "top"))
    put(d, x + dx, 2, z + dz, slab(f"{wood}_slab", "top"))
    put(d, x, 3, z, "brown_wool") if False else put(d, x + dx, 3, z + dz, "hay_block[axis=y]") if False else None
    put(d, x - dx, 2, z - dz, f"{wood}_fence")
    put(d, x + dx, 3, z + dz, "barrel[facing=up,open=false]") if False else None


def roof_garden(d, b, kind="garden"):
    """Neoterra roof: planters round the edge, solar panels, a vent unit and an antenna."""
    x1, z1, x2, z2, top = b["x1"], b["z1"], b["x2"], b["z2"], b["top"]
    ry = top + 2
    for x in range(x1 + 1, x2):
        for z in (z1 + 1, z2 - 1):
            put(d, x, ry, z, "moss_block" if (x % 4) else "flowering_azalea")
    if kind == "solar":
        for x in range(x1 + 2, x2 - 1):
            for z in range(z1 + 3, z2 - 2):
                if (z - z1) % 3 != 2:
                    put(d, x, ry, z, "daylight_detector[inverted=false,power=0]")
    else:
        for x in range(x1 + 2, x2 - 1, 3):
            for z in range(z1 + 3, z2 - 2, 3):
                put(d, x, ry, z, "potted_bamboo" if (x + z) % 2 else "flowering_azalea")
    put(d, x2 - 2, ry, z1 + 2, "smooth_stone")
    put(d, x2 - 2, ry + 1, z1 + 2, "iron_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
    put(d, x1 + 2, ry, z2 - 2, "lightning_rod[facing=up,powered=false,waterlogged=false]")


# ============================================================================================ UNIVERSITY v2
def uni_hearthwood(rel, L):
    """Oxford college growing into a full quadrangle campus."""
    d = new("Hearthwood", rel, (49, 30, 57))
    SB = "stone_bricks"
    # ---- L1: Old Schools – the study (common room) with fireplace, study table, lectern, rack
    os_nf = 2 if L >= 4 else 1
    b = bldg(d, 8, 8, 20, 15, os_nf, "gable", "x", mat=SB, up=SB, gable_end=SB)
    ext_door(d, 14, Y0, 8, "south", double=False)
    d.sign(14, 5, 7, "north", ["OLD SCHOOLS", "", "Collegium"], "dark_oak")
    d.hut(19, Y0, 9)
    keep(d, 18, Y0, 9)
    d.hearth(9, Y0, 12, "east", b["ridge"] + 2, "bricks", "campfire")
    chimney(d, 8, 12, Y0, b["ridge"] + 1)
    d.chair(11, Y0, 11, "west", "dark_oak", arms=False)
    d.chair(11, Y0, 13, "west", "dark_oak", arms=False)
    d.item(19, Y0, 13, "lectern", "west")
    keep(d, 18, Y0, 13)
    d.rack(19, Y0, 11, "west")
    keep(d, 18, Y0, 11)
    d.item(9, Y0, 9, "furnace", "east")
    keep(d, 10, Y0, 9)
    if os_nf == 2:
        stair_up(d, 13, 14, Y0, 7, "east")
    long_table(d, 14, 12, 16, Y0, "dark_oak")
    shelf_wall(d, (9, 9, 19, 14), "s", Y0, 3, skip=[(9, 14), (19, 14)])
    rug_in(d, (9, 9, 19, 14), Y0, ("red_carpet", "brown_carpet"))
    corners(d, (9, 9, 19, 14), Y0)
    wall_art(d, (9, 9, 19, 14), Y0, "n", ("blue", "white"))
    if os_nf == 2:                                                  # upper storey: student sets
        dorm(d, (9, 9, 19, 13), 7, 5, head="n")
    # forecourt
    path(d, 13, 0, 15, 7)
    for x in (11, 17):
        post_lamp(d, x, 5)
    flowerbed(d, 9, 5, 11, 6)
    flowerbed(d, 17, 5, 19, 6)
    # ---- L2: gate tower + laboratory range
    if L >= 2:
        g = bldg(d, 21, 7, 25, 15, 3, "flat", mat=SB, up=SB, win="nesw", ws=2)
        d.clear(22, Y0, 7, 24, 5, 15)                              # gate passage
        for x in range(22, 25):
            for z in range(7, 16):
                d.set(x, 1, z, "stone_bricks")
        for z in (7, 15):
            d.set(22, 5, z, st("stone_brick_stairs", "west", "top"))
            d.set(24, 5, z, st("stone_brick_stairs", "east", "top"))
            d.set(23, 5, z, "chiseled_stone_bricks")
        for x, z in ((21, 7), (25, 7), (21, 15), (25, 15)):        # corner turrets
            for y in range(g["top"] + 2, g["top"] + 5):
                d.set(x, y, z, SB if y < g["top"] + 4 else "stone_brick_wall")
        d.banner(22, 9, 6, "north", "blue")
        d.banner(24, 9, 6, "north", "blue")
        clockface(d, 23, 13, 7, "north", "smooth_quartz")
        for y in range(Y0, g["top"] + 1):                          # ladder up the tower
            d.set(25 - 1, y, 14, "ladder[facing=north,waterlogged=false]") if y >= 6 else None
        office(d, (22, 8, 24, 14), 7)
        shelf_wall(d, (22, 8, 24, 14), "w", 12, 3)
        d.set(23, 12, 11, "dark_oak_slab[type=top,waterlogged=false]")
        # laboratory
        lb_nf = 2 if L >= 4 else 1
        b2 = bldg(d, 26, 8, 38, 15, lb_nf, "gable", "x", mat=SB, up=SB, gable_end=SB)
        ext_door(d, 32, Y0, 8, "south")
        chimney(d, 38, 13, Y0, b2["ridge"] + 1)
        fur = max(0, need(d, "furnace") - 1)
        reqs = [("brewing_stand", 37, 10, None), ("water_cauldron", 37, 11, None), ("crafting_table", 37, 12, None)]
        reqs += [("furnace", 37, 13 + i, "west") if i < 1 else ("furnace", 36, 14, "north") for i in range(fur)]
        for it, x, z, f in reqs:
            keep(d, x - 1, Y0, z) if x == 37 else keep(d, x, Y0, z - 1)
        lab(d, (27, 9, 37, 14), Y0, req=reqs)
        d.sign(32, 5, 7, "north", ["LABORATORY"], "dark_oak")
        if lb_nf == 2:
            stair_up(d, 28, 14, Y0, 7, "east")
            dorm(d, (27, 9, 37, 13), 7, 5, head="n")
        path(d, 31, 0, 33, 7)
        flowerbed(d, 27, 5, 29, 6)
        flowerbed(d, 35, 5, 37, 6)
        post_lamp(d, 30, 5)
        post_lamp(d, 34, 5)
    # ---- L3: great hall (lecture) closes the quad; quad lawn with paths and strollers
    if L >= 3:
        h = bldg(d, 8, 32, 38, 40, 1, "gable", "x", mat=SB, up=SB, gable_end=SB, wh=6)
        for x in (22, 23, 24):                                      # louvre on the ridge
            for z in (35, 36, 37):
                d.set(x, h["ridge"], z, "dark_oak_planks")
        for x, z in ((22, 35), (24, 35), (22, 37), (24, 37)):
            d.set(x, h["ridge"] + 1, z, "dark_oak_fence")
        d.hip(22, 35, 24, 37, h["ridge"] + 2, "deepslate_tile_stairs", "deepslate_tile_slab", overhang=0)
        for x in range(10, 38, 4):                                  # buttresses
            for z, f in ((31, "south"), (41, "north")):
                for y in range(Y0, 6):
                    put(d, x, y, z, SB)
                put(d, x, 6, z, st("stone_brick_stairs", f))
        link(d, 23, Y0, 32, "south")
        lecture(d, (9, 33, 37, 39), Y0, "w", need=None, h=6)
        d.set(10, Y0, 35, "dark_oak_planks") if False else None
        for x in (11,):
            for z in range(33, 40):
                put(d, x, Y0, z, "red_carpet")
        shelf_wall(d, (9, 33, 37, 39), "e", Y0, 3)
        # quad
        lawn(d, 15, 16, 31, 31)
        path(d, 22, 16, 24, 31)
        path(d, 15, 23, 31, 24)
        for x, z in ((20, 23), (26, 23), (23, 19), (23, 28), (18, 24), (28, 24), (23, 17), (23, 30)):
            d.spot(x, Y0, z, "leisure")
            keep(d, x, Y0, z)
        for x, z in ((17, 18), (29, 18), (17, 29), (29, 29)):
            plant_tree(d, x, z)
        for x, z in ((20, 20), (26, 27)):
            park_bench(d, x, z, "x", "north" if z < 24 else "south")
        hedge(d, 15, 31, 21, 31)
        hedge(d, 25, 31, 31, 31)
    # ---- L4: library range (west of the quad), two storeys
    if L >= 4:
        lb = bldg(d, 8, 16, 14, 31, 2, "gable", "z", mat=SB, up=SB, gable_end=SB, ws=2)
        link(d, 14, Y0, 23, "west")
        r1 = (9, 17, 13, 30)
        shelf_wall(d, r1, "w", Y0, 3)
        for z in range(19, 29, 3):
            for x in (11, 12):
                d.bookshelf(x, Y0, z, 2)
        for z in (18, 21, 24, 27):
            desk(d, 13, Y0, z, "west", sit=True)
        stair_up(d, 10, 29, Y0, 7, "north") if False else stair_up(d, 9, 29, Y0, 7, "north") if False else None
        stair_up(d, 13, 30, Y0, 7, "north")
        shelf_wall(d, r1, "w", 7, 3)
        long_table_z(d, 11, 19, 24, 7)
        lights(d, r1, 7)
        rug_in(d, r1, Y0, ("green_carpet",), pattern="plain")
        # cloister arcade along the quad side of the library
        for z in range(16, 32):
            if z % 2:
                for y in range(Y0, 5):
                    put(d, 16, y, z, "stone_brick_wall")
            put(d, 16, 5, z, SB)
            put(d, 15, 5, z, slab("deepslate_tile_slab", "top")) if False else d.set(15, 5, z, slab("stone_brick_slab", "top"))
            d.set(16, 5, z, SB)
    # ---- L5: chapel with bell-cote (east of the quad), kitchen, master's garden, fountain
    if L >= 5:
        c = bldg(d, 32, 16, 38, 31, 1, "gable", "z", mat=SB, up=SB, gable_end=SB, wh=7, ws=2)
        link(d, 32, Y0, 23, "east")
        for z in range(18, 29, 2):                                  # pews
            for x in (34, 36, 37):
                if d.air(x, Y0, z):
                    d.chair(x, Y0, z, "south", "dark_oak")
        d.set(35, Y0, 30, "dark_oak_planks")
        put(d, 35, Y0 + 1, 30, "candle[candles=4,lit=false,waterlogged=false]")
        put(d, 34, Y0, 30, "candle[candles=3,lit=false,waterlogged=false]")
        put(d, 36, Y0, 30, "candle[candles=3,lit=false,waterlogged=false]")
        d.window(35, 4, 31, 35, 7, 31, "purple_stained_glass_pane")
        d.set(35, c["ridge"] + 1, 16, "stone_brick_wall")
        d.set(35, c["ridge"] + 2, 16, "stone_bricks")
        bell(d, 35, c["ridge"] + 1, 17) if False else None
        for x in (34, 36):
            d.set(x, c["ridge"] + 1, 16, "stone_brick_wall")
            d.set(x, c["ridge"] + 2, 16, "stone_brick_slab[type=bottom,waterlogged=false]")
        d.set(35, c["ridge"] + 1, 16, AIR)
        bell(d, 35, c["ridge"] + 1, 16)
        for z in range(18, 30):
            put(d, 35, Y0, z, "red_carpet")
        lights(d, (33, 17, 37, 30), Y0, 7)
        fountain(d, 23, 24, 2)
        for x, z in ((23, 21), (23, 27)):
            pass
        # master's garden west of the Old Schools
        lawn(d, 1, 16, 6, 44)
        for z in range(18, 44, 4):
            flowerbed(d, 2, z, 3, z + 1)
            plant_tree(d, 5, z + 2) if z % 8 == 2 else None
        for z in range(16, 45):
            put(d, 0, 2, z, "dark_oak_fence")
        path(d, 39, 0, 47, 3, border=False)
        for x in range(40, 47, 3):
            cart(d, x, 2)
        # the New Building: three-storey student residence south of the hall, garden between
        nb = bldg(d, 10, 45, 36, 52, 3, "gable", "x", mat=SB, up=SB, gable_end=SB)
        ext_door(d, 23, Y0, 45, "south", double=True)
        arch(d, 23, Y0, 40, "south")
        path(d, 23, 41, 24, 44)
        lawn(d, 8, 41, 38, 44)
        flowerbed(d, 9, 42, 20, 43)
        flowerbed(d, 27, 42, 37, 43)
        stair_up(d, 12, 51, Y0, 7, "east")
        stair_up(d, 33, 51, 7, 12, "west")
        lounge(d, (11, 46, 22, 50), Y0)
        tables(d, (25, 46, 35, 50), Y0, sit=True)
        dorm(d, (11, 46, 35, 50), 7, 10, head="n")
        dorm(d, (11, 46, 35, 50), 12, 10, head="n")
        for x in (14, 32):
            chimney(d, x, 52, Y0 + 1, nb["ridge"] + 1)
    shelf_runs(d, [], 0)
    return d


def uni_neoterra(rel, L):
    """Research campus: pavilion -> lab block & bridge -> lecture theatre & quad -> extra storeys -> dorm tower,
    student union, sports court."""
    d = new("Neoterra", rel, (53, 40, 55), paving="smooth_stone")
    Q = "smooth_quartz"
    pv_nf = 3 if L >= 4 else 1
    p = bldg(d, 6, 6, 18, 14, pv_nf, "flat", glassy=True, win="nsw")
    ext_door(d, 11, Y0, 6, "south", double=True)
    d.sign(12, 6, 5, "north", ["INSTITUTE OF", "SCIENCE"], "birch", glow=True, color="cyan")
    for x in range(9, 16):
        for z in (3, 4, 5):
            put(d, x, 6, z, slab("smooth_quartz_slab", "top"))
    d.hut(7, Y0, 7)
    keep(d, 8, Y0, 7)
    d.item(17, Y0, 7, "lectern", "west")
    keep(d, 16, Y0, 7)
    d.rack(7, Y0, 13, "north")
    keep(d, 7, Y0, 12)
    d.item(17, Y0, 13, "furnace", "west")
    keep(d, 16, Y0, 13)
    if pv_nf > 1:
        stair_up(d, 8, 9, Y0, 7, "south")
        stair_up(d, 16, 12, 7, 12, "north")
    for x in range(10, 15):
        d.table(x, Y0, 10, "birch", "block", Q)
    for x in range(10, 15):
        d.chair(x, Y0, 9, "north", "mangrove")
        d.chair(x, Y0, 11, "south", "mangrove")
    shelf_wall(d, (7, 7, 17, 13), "s", Y0, 3)
    rug_in(d, (9, 8, 15, 12), Y0, ("cyan_carpet",), inset=0, pattern="plain")
    corners(d, (7, 7, 17, 13), Y0, ["potted_bamboo"])
    if pv_nf > 1:
        r2 = (7, 7, 17, 13)
        tables(d, r2, 7, step=4, sit=True)
        lights(d, r2, 7)
        office(d, (7, 7, 11, 13), 12)
        office(d, (13, 7, 17, 13), 12, desk_side="s")
        d.fill(12, 12, 7, 12, 15, 13, "light_gray_stained_glass")
        link(d, 12, 12, 10, "east") if False else arch(d, 12, 12, 10, "east")
        roof_garden(d, p, "garden")
    path(d, 10, 0, 13, 5, "smooth_stone")
    for x in (4, 20):
        post_lamp(d, x, 4)
    if L >= 2:
        lb_nf = {2: 1, 3: 1, 4: 2, 5: 3}[L]
        b2 = bldg(d, 26, 6, 40, 14, lb_nf, "flat", glassy=True, win="nse")
        d.box(18, Y0, 8, 26, 5, 12, "glass", floor="polished_diorite")
        d.fill(18, 6, 8, 26, 6, 12, Q)
        d.clear(19, Y0, 9, 25, 5, 11)
        for x in (18, 26):
            arch(d, x, Y0, 10, "east")
        for x in range(19, 26, 2):
            put(d, x, Y0, 9, "potted_bamboo")
            put(d, x, 5, 10, "sea_lantern") if False else d.set(x, 6, 10, "sea_lantern")
        ext_door(d, 33, Y0, 6, "south", double=True)
        d.sign(33, 6, 5, "north", ["LABS"], "birch", glow=True, color="cyan")
        fur = max(0, need(d, "furnace") - 1)
        reqs = [("brewing_stand", 39, 8, None), ("water_cauldron", 39, 9, None), ("crafting_table", 39, 10, None)]
        reqs += [("furnace", 39, 11 + i, "west") for i in range(fur)]
        for it, x, z, f in reqs:
            keep(d, x - 1, Y0, z)
        lab(d, (27, 7, 39, 13), Y0, req=reqs)
        if lb_nf > 1:
            stair_up(d, 28, 13, Y0, 7, "east")
            classroom(d, (27, 7, 39, 12), 7, board="e")
            roof_garden(d, b2, "solar")
        if lb_nf > 2:
            stair_up(d, 38, 13, 7, 12, "west")
            office(d, (27, 7, 32, 13), 12)
            office(d, (34, 7, 39, 13), 12, desk_side="s")
            d.fill(33, 12, 7, 33, 15, 13, "light_gray_stained_glass")
            arch(d, 33, 12, 10, "east")
        for x in (22, 44):
            plant_tree(d, x, 3)
    if L >= 3:
        X1, X2, Z1, Z2 = 14, 38, 38, 47
        bldg(d, X1, Z1, X2, Z2, 1, "flat", wh=8, win="s", ws=4)
        shelf_wall(d, (X1 + 1, Z1 + 1, X2 - 1, Z2 - 1), "w", Y0, 3)
        shelf_wall(d, (X1 + 1, Z1 + 1, X2 - 1, Z2 - 1), "e", Y0, 3)
        for x in range(X1, X2 + 1):
            d.set(x, 9, Z1, "cyan_terracotta")
        ext_door(d, 26, Y0, Z1, "north", double=True)
        for x in range(18, 35):
            d.set(x, 6, Z1 + 1, "black_concrete")
            d.set(x, 7, Z1 + 1, "black_concrete")
        d.set(26, 7, Z1 + 1, "sea_lantern")
        put(d, 20, Y0, Z1 + 2, Q)
        for k in range(3):                                          # raked tiers rising south
            zs = Z1 + 4 + 2 * k
            for z in (zs, zs + 1):
                for x in range(X1 + 1, X2):
                    for y in range(Y0, Y0 + k):
                        d.set(x, y, z, Q)
            for x in range(X1 + 3, X2 - 2):
                if x in (20, 26, 32):
                    continue
                d.chair(x, Y0 + k, zs, "south", "birch")
        lights(d, (X1 + 1, Z1 + 1, X2 - 1, Z2 - 1), Y0, 8)
        lawn(d, 6, 16, 46, 36)
        path(d, 25, 15, 27, 37)
        path(d, 6, 26, 46, 26)
        for x, z in ((12, 26), (18, 26), (34, 26), (40, 26), (26, 19), (26, 23), (26, 30), (26, 34)):
            d.spot(x, Y0, z, "leisure")
            keep(d, x, Y0, z)
        for x, z in ((10, 20), (42, 20), (10, 32), (42, 32), (18, 20), (34, 32)):
            plant_tree(d, x, z)
        for x, z in ((20, 24), (30, 24)):
            park_bench(d, x, z, "x", "north")
        for x, z in ((20, 28), (30, 28)):
            park_bench(d, x, z, "x", "south")
        fountain(d, 26, 26, 2) if L >= 4 else None
    if L >= 4:
        un = bldg(d, 6, 17, 14, 34, 2, "flat", glassy=True, win="nsew")
        ext_door(d, 14, Y0, 25, "west", double=True, along="z")
        kitchen(d, (7, 18, 13, 21), Y0)
        tables(d, (7, 23, 13, 33), Y0, step=4)
        stair_up(d, 7, 33, Y0, 7, "north")
        lounge(d, (7, 18, 13, 26), 7)
        tables(d, (7, 27, 13, 33), 7)
        roof_garden(d, un, "garden")
        d.sign(14, 6, 21, "east", ["STUDENT", "UNION"], "birch", glow=True, color="cyan")
    if L >= 5:
        dt = bldg(d, 38, 17, 46, 34, 6, "flat", glassy=True, win="nsew")
        ext_door(d, 38, Y0, 25, "east")
        for k in range(5):
            stair_up(d, 39 + (k % 2) * 6, 18 if k % 2 == 0 else 33, Y0 + 5 * k, Y0 + 5 * k + 5,
                     "south" if k % 2 == 0 else "north")
        for k in range(6):
            y = Y0 + 5 * k
            if k == 0:
                lounge(d, (39, 19, 45, 32), y)
            else:
                dorm(d, (39, 20, 45, 31), y, 6, head="e")
        roof_garden(d, dt, "solar")
        # sports court beside the street
        for x in range(42, 52):
            for z in range(1, 15):
                edge = x in (42, 51) or z in (1, 14) or z == 8
                d.set(x, 1, z, "white_concrete" if edge else "light_blue_terracotta")
        for z in (2, 13):
            put(d, 46, 2, z, "iron_bars")
            put(d, 46, 3, z, "iron_bars")
            put(d, 46, 4, z, "white_stained_glass")
    return d


def uni_cascadia(rel, L):
    """Timber college: lodges round a quad joined by covered boardwalks."""
    d = new("Cascadia", rel, (53, 30, 55), paving="coarse_dirt")
    st_nf = 2 if L >= 4 else 1
    b = bldg(d, 6, 6, 18, 14, st_nf, "gable", "x")
    ext_door(d, 12, Y0, 6, "south")
    d.fill(5, 1, 2, 19, 1, 5, "spruce_planks")                     # porch
    for x in (5, 19, 9, 15):
        for y in range(Y0, 6):
            put(d, x, y, 2, log("spruce_log"))
    for x in range(4, 21):
        d.set(x, 6, 1, st("spruce_stairs", "south"))
        for z in range(2, 6):
            d.set(x, 6, z, slab("spruce_slab"))
    d.sign(12, 5, 5, "north", ["TIMBERLINE", "COLLEGE"], "spruce")
    d.hut(7, Y0, 7)
    keep(d, 8, Y0, 7)
    d.item(17, Y0, 7, "lectern", "west")
    keep(d, 16, Y0, 7)
    d.rack(7, Y0, 13, "north")
    keep(d, 7, Y0, 12)
    d.item(17, Y0, 13, "furnace", "west")
    keep(d, 16, Y0, 13)
    d.hearth(12, Y0, 13, "north", b["ridge"] + 1, "cobblestone", "campfire")
    chimney(d, 12, 14, Y0, b["ridge"] + 1)
    if st_nf > 1:
        stair_up(d, 16, 8, Y0, 7, "south")
    for x in range(10, 15):
        d.table(x, Y0, 9, "spruce", "block", "stripped_spruce_wood[axis=y]")
        d.chair(x, Y0, 8, "north", "spruce")
        d.chair(x, Y0, 10, "south", "spruce")
    d.chair(11, Y0, 11, "south", "spruce", arms=True) if False else None
    shelf_wall(d, (7, 7, 17, 13), "w", Y0, 3, skip=[(7, 7), (7, 13)])
    shelf_wall(d, (7, 7, 17, 13), "e", Y0, 2, skip=[(17, 7), (17, 13)])
    rug_in(d, (9, 11, 15, 12), Y0, ("brown_carpet",), inset=0, pattern="plain")
    if st_nf > 1:
        dorm(d, (7, 7, 17, 13), 7, 4, head="n")
    if L >= 2:
        c_nf = 1
        b2 = bldg(d, 30, 6, 42, 14, c_nf, "gable", "x")
        ext_door(d, 36, Y0, 6, "south")
        d.sign(36, 5, 5, "north", ["CHEMISTRY"], "spruce")
        chimney(d, 42, 10, Y0, b2["ridge"] + 1)
        fur = max(0, need(d, "furnace") - 1)
        reqs = [("brewing_stand", 41, 8, None), ("water_cauldron", 41, 9, None), ("crafting_table", 41, 10, None)]
        reqs += [("furnace", 41, 11 + i, "west") for i in range(fur)]
        for it, x, z, f in reqs:
            keep(d, x - 1, Y0, z)
        lab(d, (31, 7, 41, 13), Y0, req=reqs)
        shelf_wall(d, (31, 7, 41, 13), "s", Y0, 2, skip=[(31, 13), (41, 13)])
        # covered boardwalk
        for x in range(19, 30):
            for z in range(8, 13):
                d.set(x, 1, z, "spruce_planks")
                d.set(x, 6, z, slab("spruce_slab"))
            for z in (8, 12):
                if x % 3 == 1:
                    for y in range(Y0, 6):
                        d.set(x, y, z, log("spruce_log"))
                else:
                    d.set(x, Y0, z, "spruce_fence")
        for x0 in (18, 30):
            link(d, x0, Y0, 10, "east" if x0 == 18 else "west")
        for x in range(20, 30, 4):
            d.set(x, 5, 10, "lantern[hanging=true,waterlogged=false]")
        for x in (24,):
            d.set(x, Y0, 8, AIR)
            d.set(x, Y0, 12, AIR)
        for x, z in ((22, 3), (27, 3), (46, 4)):
            plant_tree(d, x, z)
    if L >= 3:
        lec = bldg(d, 12, 38, 38, 46, 1, "gable", "x", wh=5)
        ext_door(d, 25, Y0, 38, "north", double=True)
        lecture(d, (13, 39, 37, 45), Y0, "w", h=5)
        shelf_wall(d, (13, 39, 37, 45), "e", Y0, 3)
        chimney(d, 12, 42, Y0, lec["ridge"] + 1)
        lawn(d, 6, 16, 46, 36, "grass_block[snowy=false]")
        for x in range(6, 47):
            for z in range(16, 37):
                if (x * 7 + z * 3) % 11 == 0:
                    d.set(x, 1, z, "moss_block")
        path(d, 24, 15, 26, 37, "spruce_planks", border=False)
        cx, cz = 15, 26
        d.set(cx, 1, cz, "cobblestone")
        d.set(cx, Y0, cz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        for x in range(cx - 1, cx + 2):
            for z in range(cz - 1, cz + 2):
                if (x, z) != (cx, cz):
                    d.set(x, 1, z, "gravel")
        for (x, z, ax) in ((cx - 3, cz, "z"), (cx + 3, cz, "z"), (cx, cz - 3, "x"), (cx, cz + 3, "x"),
                           (cx - 3, cz - 1, "z"), (cx + 3, cz + 1, "z")):
            d.set(x, Y0, z, log("stripped_spruce_log", ax))
        for x, z in ((cx - 2, cz - 2), (cx + 2, cz - 2), (cx - 2, cz + 2), (cx + 2, cz + 2), (32, 22), (36, 28),
                     (25, 20), (25, 32)):
            d.spot(x, Y0, z, "leisure")
            keep(d, x, Y0, z)
        for x, z in ((34, 18), (42, 24), (30, 33), (9, 33), (20, 18)):
            plant_tree(d, x, z)
    if L >= 4:
        rl = bldg(d, 6, 17, 13, 34, 2, "gable", "z")
        ext_door(d, 13, Y0, 25, "west")
        r1 = (7, 18, 12, 33)
        stair_up(d, 12, 33, Y0, 7, "north") if False else stair_up(d, 8, 22, Y0, 7, "south")
        shelf_wall(d, r1, "w", Y0, 3)
        for z in range(19, 33, 4):
            desk(d, 11, Y0, z, "west")
        shelf_wall(d, r1, "w", 7, 2)
        shelf_wall(d, r1, "e", 7, 1)
        lights(d, r1, Y0)
        rug_in(d, r1, Y0, ("green_carpet",), pattern="plain")
        tables(d, (8, 19, 11, 32), 7, sit=True)
    if L >= 4:
        bk_nf = 2 if L >= 5 else 1
        bk = bldg(d, 38, 17, 46, 34, bk_nf, "gable", "z")
        ext_door(d, 38, Y0, 25, "east")
        if bk_nf > 1:
            stair_up(d, 45, 19, Y0, 7, "south")
            dorm(d, (39, 18, 45, 33), 7, 7, head="e")
        dorm(d, (39, 18, 45, 33), Y0, 7, head="e")
        chimney(d, 46, 30, Y0, bk["ridge"] + 1)
    if L >= 5:
        # mess hall lodge on the street, east of the chemistry cabin
        mh = bldg(d, 44, 4, 52, 15, 1, "gable", "z")
        ext_door(d, 48, Y0, 4, "south")
        kitchen(d, (45, 5, 51, 8), Y0)
        tables(d, (45, 9, 51, 14), Y0)
        chimney(d, 52, 12, Y0, mh["ridge"] + 1)
        # fire-lookout tower at the quad corner
        tx1, tz1 = 31, 30
        for x, z in ((tx1, tz1), (tx1 + 4, tz1), (tx1, tz1 + 4), (tx1 + 4, tz1 + 4)):
            for y in range(Y0, 16):
                d.set(x, y, z, log("spruce_log"))
        for y in (7, 12):
            for a in range(1, 4):
                for (x, z, ax) in ((tx1 + a, tz1, "x"), (tx1 + a, tz1 + 4, "x"), (tx1, tz1 + a, "z"), (tx1 + 4, tz1 + a, "z")):
                    d.set(x, y, z, log("spruce_log", ax))
        d.fill(tx1, 15, tz1, tx1 + 4, 15, tz1 + 4, "spruce_planks")
        for x in range(tx1, tx1 + 5):
            for z in range(tz1, tz1 + 5):
                if x in (tx1, tx1 + 4) or z in (tz1, tz1 + 4):
                    d.set(x, 16, z, "spruce_fence")
        d.hip(tx1, tz1, tx1 + 4, tz1 + 4, 19, "dark_oak_stairs", "dark_oak_slab", overhang=1)
        for x, z in ((tx1, tz1), (tx1 + 4, tz1), (tx1, tz1 + 4), (tx1 + 4, tz1 + 4)):
            for y in range(16, 19):
                d.set(x, y, z, log("spruce_log"))
        d.set(tx1 + 2, 19, tz1 + 2, "spruce_planks")
        bell(d, tx1 + 2, 18, tz1 + 2)
        # faculty lodge (two storeys) in the south-east corner
        fl = bldg(d, 40, 39, 52, 51, 2, "gable", "x")
        ext_door(d, 48, Y0, 39, "south")
        stair_up(d, 42, 50, Y0, 7, "east")
        office(d, (41, 40, 45, 45), Y0)
        office(d, (47, 40, 51, 45), Y0, desk_side="s")
        lounge(d, (41, 46, 51, 50), Y0) if False else tables(d, (46, 46, 51, 50), Y0)
        d.fill(46, Y0, 40, 46, 5, 45, "spruce_planks")
        arch(d, 46, Y0, 42, "east")
        dorm(d, (41, 40, 51, 50), 7, 8, head="n")
        chimney(d, 52, 45, Y0, fl["ridge"] + 1)
        # covered boardwalk round the quad (posts, rail, slab roof)
        for x in range(14, 38):
            for z in (15, 37):
                d.set(x, 1, z, "spruce_planks")
                d.set(x, 6, z, slab("spruce_slab"))
                if x % 4 == 2:
                    for y in range(Y0, 6):
                        d.set(x, y, z, log("spruce_log"))
                    d.set(x, 5, z + (1 if z == 15 else -1), "lantern[hanging=false,waterlogged=false]") if False else None
        for z in range(15, 38):
            for x in (14, 37):
                d.set(x, 1, z, "spruce_planks")
                d.set(x, 6, z, slab("spruce_slab"))
                if z % 4 == 3:
                    for y in range(Y0, 6):
                        d.set(x, y, z, log("spruce_log"))
        for x in range(16, 37, 4):
            d.set(x, 5, 15, "lantern[hanging=true,waterlogged=false]")
            d.set(x, 5, 37, "lantern[hanging=true,waterlogged=false]")
    return d


@design("university")
def university_v2(pack, rel, L):
    return {"Hearthwood": uni_hearthwood, "Cascadia": uni_cascadia, "Neoterra": uni_neoterra}[pack](rel, L)


def line_items(d, x, z, along, y, face, items, step=1):
    """Required work blocks in a row starting at (x,z) along +x ('x') or +z ('z'); the cell in front (direction
    `face`) is kept free. None leaves a gap. Returns next free position."""
    dx, dz = (1, 0) if along == "x" else (0, 1)
    fx, fz = D4[face]
    for i, it in enumerate(items):
        cx, cz = x + dx * i * step, z + dz * i * step
        if it is None:
            continue
        if it == "water_cauldron":
            d.item(cx, y, cz, "water_cauldron[level=3]")
        elif it == "rack":
            d.rack(cx, y, cz, face)
        else:
            d.item(cx, y, cz, it, face if it not in ("barrel",) else "up")
        keep(d, cx + fx, y, cz + fz)
        keep(d, cx, y, cz, 1)
    return x + dx * len(items) * step, z + dz * len(items) * step


def barrels(d, x, z, along, y, n, face, h=2):
    """Barrel shelving n cells long, h high (required barrels), aisle kept in front."""
    dx, dz = (1, 0) if along == "x" else (0, 1)
    fx, fz = D4[face]
    k = 0
    for i in range(n):
        cx, cz = x + dx * i, z + dz * i
        for j in range(h):
            d.item(cx, y + j, cz, "barrel", face)
            k += 1
        keep(d, cx + fx, y, cz + fz)
    return k


def work_items(d, L):
    """The town hall's work blocks for this level (barrels handled separately)."""
    out = []
    for k, n in sorted(d.req["items"].items()):
        k = k.split(":")[1]
        if k in ("barrel", "enchanting_table", "lectern", "ender_chest", "jukebox"):
            continue
        out += [k] * n
    return out


def market_stall(d, x, z, color, goods=("melon", "pumpkin[]", "hay_block[axis=y]")):
    """Market stall: counter, posts, striped wool awning, goods."""
    wood = d.S["wood"] if d.pack != "Neoterra" else "birch"
    for dx in (0, 2):
        for y in (2, 3, 4):
            put(d, x + dx, y, z, f"{wood}_fence")
            put(d, x + dx, y, z + 2, f"{wood}_fence")
    for dx in range(3):
        for dz in range(3):
            put(d, x + dx, 5, z + dz, f"{color if (dx % 2 == 0) else 'white'}_wool" if d.pack != "Neoterra" else
                f"{color}_concrete" if dx % 2 == 0 else "white_concrete")
    put(d, x + 1, 2, z, slab(f"{wood}_slab", "top"))
    put(d, x + 1, 3, z, ("melon", "pumpkin", "hay_block[axis=y]", "red_mushroom_block[down=true,east=true,north=true,south=true,up=true,west=true]")[(x + z) % 4])
    put(d, x + 1, 2, z + 2, "barrel[facing=up,open=false]") if False else put(d, x + 1, 2, z + 2, "composter[level=8]")


# ============================================================================================ TOWN HALL v2
def th_hearthwood(rel, L):
    d = new("Hearthwood", rel, (55, 36, 53))
    two = L >= 3
    nf = 2 if two else 1
    # ---- core guildhall (L1+): public hall
    c = bldg(d, 20, 14, 32, 22, nf, "gable", "x", win="nesw")
    d.hut(21, Y0, 15)
    keep(d, 22, Y0, 15)
    d.set(23, Y0, 15, slab("dark_oak_slab", "top"))
    put(d, 23, Y0 + 1, 15, "candle[candles=2,lit=false,waterlogged=false]")
    d.chair(23, Y0, 16, "south", "dark_oak", sit=False)
    long_table(d, 25, 18, 27, Y0, "dark_oak")
    line_items(d, 21, 17, "z", Y0, "east", ["crafting_table", "furnace", "furnace"])
    barrels(d, 31, 15, "z", Y0, 2, "west")
    d.bed(31, Y0, 21, "east")
    put(d, 31, Y0, 20, slab("dark_oak_slab", "top"))
    put(d, 31, Y0 + 1, 20, "candle[candles=1,lit=false,waterlogged=false]")
    rug_in(d, (21, 15, 31, 21), Y0, ("red_carpet", "yellow_carpet"))
    wall_art(d, (21, 15, 31, 21), Y0, "s", ("red", "yellow"))
    # entrance tower over the door (stub L1-2, clock & belfry L3+)
    tt = {1: 9, 2: 14}.get(L, 25)
    t = bldg(d, 24, 9, 28, 14, 1, "flat", wh=tt - 1, mat="stone_bricks", up="stone_bricks", win="", deco=False,
             parapet=False)
    d.clear(25, Y0, 14, 27, 4, 14)
    ext_door(d, 26, Y0, 9, "south")
    d.sign(26, 5, 8, "north", ["TOWN", "HALL"], "dark_oak")
    d.banner(25, 6, 8, "north", "red")
    d.banner(27, 6, 8, "north", "red")
    d.fill(25, 6, 10, 27, 6, 13, "dark_oak_planks")
    by = tt - 3
    d.fill(25, by, 10, 27, by, 13, "dark_oak_planks")
    for y in range(by + 1, tt):
        for x in range(25, 28):
            d.set(x, y, 9, AIR)
            d.set(x, y, 14, AIR)
        for z in range(10, 14):
            d.set(24, y, z, AIR)
            d.set(28, y, z, AIR)
    bell(d, 26, tt - 1, 11)
    d.fill(24, tt, 9, 28, tt, 14, "stone_bricks")
    rt = d.hip(24, 9, 28, 14, tt + 1, f"{d.S['roof']}_stairs", f"{d.S['roof']}_slab", overhang=1)
    d.set(26, rt + 1, 11, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    if two:
        clockface(d, 26, by - 3, 9, "north", "white_concrete")
        clockface(d, 24, by - 3, 11, "west", "white_concrete")
        clockface(d, 28, by - 3, 11, "east", "white_concrete")
        for x in range(24, 29):
            put(d, x, by - 6, 8, st("stone_brick_stairs", "south", "top"))
    # forecourt: patterned paving, lamp posts, flower beds
    for x in range(14, 39):
        for z in range(1, 9):
            d.set(x, 1, z, "stone_bricks" if (x + z) % 3 else "polished_andesite")
    for x in (21, 31):
        post_lamp(d, x, 7)
    flowerbed(d, 20, 12, 23, 13)
    flowerbed(d, 29, 12, 32, 13)
    # ---- L2: workshop wing (west) + stores wing (east)
    if L >= 2:
        w = bldg(d, 8, 14, 20, 22, nf, "gable", "x", mat="bricks", up="calcite")
        link(d, 20, Y0, 18, "west")
        items = work_items(d, L)
        a, b = items[:11], items[11:]
        line_items(d, 9, 15, "x", Y0, "south", a[:11])
        line_items(d, 9, 21, "x", Y0, "north", b + [None] * 0)
        d.hearth(13, Y0, 18, "north", 6, "bricks", "campfire") if False else None
        for x in range(11, 18):
            if x % 2:
                put(d, x, Y0, 18, slab("dark_oak_slab", "top"))
                put(d, x, Y0 + 1, 18, ("flower_pot", "candle[candles=2,lit=false,waterlogged=false]")[x % 4 == 1])
        lights(d, (9, 15, 19, 21), Y0)
        chimney(d, 8, 16, Y0, w["ridge"] + 1)
        d.sign(14, 5, 13, "north", ["Guild", "Workshop"], "dark_oak")
        ext_door(d, 8, Y0, 18, "east")
        s_ = bldg(d, 32, 14, 44, 22, nf, "gable", "x", mat="bricks", up="calcite")
        link(d, 32, Y0, 18, "east")
        nb = need(d, "barrel") - 4
        barrels(d, 33, 15, "x", Y0, min(11, (nb + 1) // 2), "south")
        if nb > 22:
            pass
        rest = nb - 2 * min(11, (nb + 1) // 2)
        if rest > 0:
            barrels(d, 33, 21, "x", Y0, (rest + 1) // 2, "north")
        ext_door(d, 44, Y0, 18, "west", double=True, along="z")
        store(d, (33, 17, 43, 20), Y0)
        cart(d, 47, 16, "z")
        put(d, 47, 2, 21, "hay_block[axis=y]")
        path(d, 45, 18, 52, 19, border=False)
    # ---- L3: upper floor: archive (W), council chamber (centre), quarters (E)
    if two:
        stair_up(d, 22, 21, Y0, 7, "east")
        link(d, 20, 7, 18, "east")
        link(d, 32, 7, 18, "east")
        for x in range(23, 30):
            pass
        long_table(d, 24, 17, 29, 7, "dark_oak", top="dark_oak_planks")
        d.item(30, 7, 15, "lectern", "west")
        keep(d, 29, 7, 15)
        if L >= 4:
            d.item(21, 7, 15, "jukebox")
            keep(d, 22, 7, 15)
        wall_art(d, (21, 15, 31, 21), 7, "n", ("red", "yellow"))
        rug_in(d, (21, 15, 31, 20), 7, ("red_carpet",), inset=1, pattern="plain")
        shelf_wall(d, (9, 15, 19, 21), "n", 7, 3)
        shelf_wall(d, (9, 15, 19, 21), "w", 7, 3)
        d.item(14, 7, 19, "enchanting_table")
        keep(d, 14, 7, 20)
        tables(d, (15, 16, 19, 21), 7, sit=False)
        dorm(d, (33, 15, 43, 21), 7, 5, head="n")
        if L >= 4:
            d.item(43, 7, 21, "ender_chest", "west")
            keep(d, 42, 7, 21)
    # ---- L4: rear wing – banquet hall & kitchen below, mayor's apartment above
    if L >= 4:
        r = bldg(d, 20, 22, 32, 35, 2, "gable", "z", mat="bricks", up="calcite")
        link(d, 26, Y0, 22, "south")
        long_table_z(d, 26, 25, 31, Y0, "dark_oak")
        kitchen(d, (21, 31, 31, 34), Y0)
        wall_art(d, (21, 23, 31, 33), Y0, "ew", ("red", "yellow"))
        stair_up(d, 31, 24, Y0, 7, "south")
        office(d, (21, 23, 30, 27), 7)
        dorm(d, (21, 29, 31, 34), 7, 2, head="s")
        lounge(d, (21, 28, 31, 34), 7)
        chimney(d, 32, 30, Y0, r["ridge"] + 1)
        # walled garden behind with a bandstand
        lawn(d, 8, 36, 46, 51)
        for x in range(8, 47):
            put(d, x, 2, 51, "brick_wall")
        for z in range(36, 52):
            put(d, 8, 2, z, "brick_wall")
            put(d, 46, 2, z, "brick_wall")
        path(d, 25, 35, 27, 50)
        bx, bz = 26, 43
        for x in range(bx - 3, bx + 4):
            for z in range(bz - 3, bz + 4):
                if abs(x - bx) + abs(z - bz) <= 4:
                    d.set(x, 1, z, "stone_bricks")
        for x, z in ((bx - 2, bz - 2), (bx + 2, bz - 2), (bx - 2, bz + 2), (bx + 2, bz + 2)):
            for y in range(Y0, 6):
                d.set(x, y, z, "dark_oak_fence")
        d.hip(bx - 2, bz - 2, bx + 2, bz + 2, 6, "deepslate_tile_stairs", "deepslate_tile_slab", overhang=1)
        for x, z in ((12, 40), (40, 40), (12, 48), (40, 48)):
            plant_tree(d, x, z)
        flowerbed(d, 15, 37, 22, 38)
        flowerbed(d, 30, 37, 37, 38)
        for x, z in ((18, 44), (33, 44)):
            park_bench(d, x, z, "x", "south")
    # ---- L5: market square with stalls & fountain; courthouse (W) and guard house (E) round the garden
    if L >= 5:
        fountain(d, 26, 4, 2)
        for x, col in ((15, "red"), (35, "blue")):
            market_stall(d, x, 2, col)
        for x, col in ((10, "yellow"), (40, "green")):
            market_stall(d, x, 5, col)
        ch = bldg(d, 8, 24, 18, 34, 2, "gable", "z", mat="stone_bricks", up="stone_bricks", gable_end="stone_bricks")
        ext_door(d, 13, Y0, 24, "south")
        for x in range(9, 18):
            pass
        d.item(13, Y0, 32, "lectern", "north") if False else put(d, 13, Y0, 32, "dark_oak_planks")
        lecture(d, (9, 25, 17, 33), Y0, "s")
        stair_up(d, 9, 26, Y0, 7, "south")
        office(d, (9, 25, 17, 33), 7)
        shelf_wall(d, (9, 25, 17, 33), "e", 7, 3)
        d.sign(13, 5, 23, "north", ["COURT", "HOUSE"], "dark_oak")
        gh = bldg(d, 34, 24, 44, 34, 2, "gable", "z", mat="bricks", up="calcite")
        ext_door(d, 39, Y0, 24, "south")
        d.sign(39, 5, 23, "north", ["WATCH", "HOUSE"], "dark_oak")
        tables(d, (35, 25, 43, 29), Y0)
        for x in range(36, 43, 2):                                 # cells
            d.fill(x, Y0, 31, x, 4, 33, "iron_bars")
        stair_up(d, 43, 27, Y0, 7, "south")
        dorm(d, (35, 25, 42, 33), 7, 6, head="w")
        # covered market house: open arcade below, corn exchange above
        mx1, mz1, mx2, mz2 = 46, 24, 54, 36
        m = bldg(d, mx1, mz1, mx2, mz2, 2, "gable", "z", mat="stone_bricks", up="calcite")
        for x in range(mx1, mx2 + 1):
            for z in range(mz1, mz2 + 1):
                if (x in (mx1, mx2) or z in (mz1, mz2)) and not ((x in (mx1, mx2) and (z - mz1) % 3 == 0) or
                                                                 (z in (mz1, mz2) and (x - mx1) % 4 == 0)):
                    for y in range(Y0, 6):
                        d.set(x, y, z, AIR)
                    d.set(x, 5, z, "stone_brick_slab[type=top,waterlogged=false]")
        for x, z, col in ((48, 27, "red"), (51, 27, "yellow"), (48, 31, "green"), (51, 31, "blue")):
            put(d, x, Y0, z, slab("dark_oak_slab", "top"))
            put(d, x + 1, Y0, z, f"{col}_wool")
            put(d, x, Y0 + 1, z, ("melon", "pumpkin", "hay_block[axis=y]", "carved_pumpkin[facing=north]")[x % 4])
        stair_up(d, 47, 35, Y0, 7, "north") if False else stair_up(d, 53, 34, Y0, 7, "north")
        tables(d, (47, 25, 52, 35), 7)
        d.sign(50, 6, 23, "north", ["MARKET", "HOUSE"], "dark_oak")
        for z in (26, 30):
            put(d, 33, 4, z, "lantern[hanging=false,waterlogged=false]") if False else None
    return d


def th_neoterra(rel, L):
    d = new("Neoterra", rel, (53, 45, 49), paving="smooth_stone")
    Q = "smooth_quartz"
    two = L >= 3
    nf = 2 if two else 1
    c = bldg(d, 18, 12, 32, 22, nf, "flat", glassy=True, win="nesw")
    ext_door(d, 24, Y0, 12, "south", double=True)
    d.hut(19, Y0, 13)
    keep(d, 20, Y0, 13)
    for x in range(21, 24):
        d.set(x, Y0, 15, Q)
    d.chair(22, Y0, 16, "south", "mangrove", sit=False)
    for x, z in ((25, 17), (26, 17), (25, 18), (26, 18)):
        d.table(x, Y0, z, "birch", "block", Q)
    for x in (25, 26):
        d.chair(x, Y0, 16, "north", "birch")
        d.chair(x, Y0, 19, "south", "birch")
    for z in (17, 18):
        d.chair(24, Y0, z, "west", "birch")
        d.chair(27, Y0, z, "east", "birch")
    line_items(d, 19, 17, "z", Y0, "east", ["crafting_table", "furnace", "furnace"])
    barrels(d, 31, 13, "z", Y0, 2, "west")
    d.bed(31, Y0, 21, "east", "cyan")
    put(d, 31, Y0, 20, "white_concrete")
    put(d, 31, Y0 + 1, 20, "end_rod[facing=up]")
    corners(d, (19, 13, 31, 21), Y0, ["potted_bamboo"])
    for x in range(20, 31):
        for z in (12, 11, 10, 9):
            pass
    for x in range(21, 30):                                         # entrance canopy
        for z in range(8, 12):
            put(d, x, 6 if not two else 6, z, slab("smooth_quartz_slab", "top"))
    d.sign(25, 7 if two else 7, 11, "north", ["CIVIC", "CENTRE"], "birch", glow=True, color="cyan") if False else \
        d.sign(25, 6 if not two else 7, 11 if two else 7, "north", ["CIVIC", "CENTRE"], "birch", glow=True, color="cyan")
    # plaza paving pattern
    for x in range(10, 41):
        for z in range(1, 12):
            if d.get(x, 1, z) == "minecraft:smooth_stone":
                d.set(x, 1, z, "polished_diorite" if (x // 2 + z // 2) % 2 else "smooth_stone")
    for x in (20, 30):
        post_lamp(d, x, 4)
    for x in (16, 34):
        put(d, x, 2, 9, "moss_block")
        put(d, x, 3, 9, "flowering_azalea")
    if L >= 2:
        w = bldg(d, 6, 12, 18, 22, nf, "flat", glassy=True, win="nsw")
        link(d, 18, Y0, 17, "west")
        items = work_items(d, L)
        line_items(d, 7, 13, "x", Y0, "south", items[:11])
        line_items(d, 7, 21, "x", Y0, "north", items[11:])
        for x in range(9, 16):
            put(d, x, Y0, 17, slab("smooth_quartz_slab", "top"))
            put(d, x, Y0 + 1, 17, ("flower_pot", "end_rod[facing=up]", AIR)[x % 3]) if x % 3 < 2 else None
        ext_door(d, 6, Y0, 17, "east")
        d.sign(12, 6, 11, "north", ["MAKER", "SPACE"], "birch", glow=True, color="orange")
        s_ = bldg(d, 32, 12, 44, 22, nf, "flat", glassy=False, win="ns")
        link(d, 32, Y0, 17, "east")
        nb = need(d, "barrel") - 4
        barrels(d, 33, 13, "x", Y0, min(11, (nb + 1) // 2), "south")
        rest = nb - 2 * min(11, (nb + 1) // 2)
        if rest > 0:
            barrels(d, 33, 21, "x", Y0, (rest + 1) // 2, "north")
        ext_door(d, 44, Y0, 17, "west", double=True, along="z")
        store(d, (33, 15, 43, 19), Y0)
        # clock fin with bell frame
        ft = 17 if L == 2 else 28
        for x in range(46, 49):
            for z in range(7, 10):
                for y in range(Y0, ft + 1):
                    d.set(x, y, z, "white_concrete")
        for y in range(Y0 + 1, ft - 3):
            d.set(47, y, 7, "cyan_stained_glass")
        clockface(d, 47, ft - 1, 7, "north", "black_concrete", hand="sea_lantern")
        for x, z in ((46, 7), (48, 7), (46, 9), (48, 9)):
            for y in range(ft + 1, ft + 4):
                d.set(x, y, z, "quartz_pillar[axis=y]")
        d.fill(46, ft + 4, 7, 48, ft + 4, 9, Q)
        bell(d, 47, ft + 3, 8)
        d.set(47, ft + 5, 8, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    if two:
        stair_up(d, 20, 21, Y0, 7, "east")
        link(d, 18, 7, 17, "east")
        link(d, 32, 7, 17, "east")
        for x in range(22, 29):                                     # horseshoe council table
            d.table(x, 7, 19, "birch", "block", Q)
            d.chair(x, 7, 20, "south", "mangrove")
        for z in (15, 16, 17, 18):
            for x, back in ((22, "west"), (28, "east")):
                d.table(x, 7, z, "birch", "block", Q)
                d.chair(x + (-1 if back == "west" else 1), 7, z, back, "mangrove")
        d.item(25, 7, 13, "lectern", "south")
        keep(d, 25, 7, 14)
        d.banner(25, 9, 13, "south", "cyan") if False else None
        if L >= 4:
            d.item(30, 7, 13, "jukebox")
            keep(d, 30, 7, 14)
        shelf_wall(d, (7, 13, 17, 21), "w", 7, 3)
        shelf_wall(d, (7, 13, 17, 21), "s", 7, 3)
        d.item(12, 7, 16, "enchanting_table")
        keep(d, 12, 7, 17)
        tables(d, (8, 13, 16, 15), 7, sit=False)
        dorm(d, (33, 13, 43, 21), 7, 5, head="n")
        if L >= 4:
            d.item(43, 7, 21, "ender_chest", "west")
            keep(d, 42, 7, 21)
        for b in (w, s_):
            roof_garden(d, b, "garden" if b is w else "solar")
    if L >= 4:
        r = bldg(d, 18, 22, 32, 34, 3, "flat", glassy=True, win="esw")
        link(d, 25, Y0, 22, "south")
        long_table(d, 21, 27, 29, Y0, "birch", top=Q)
        long_table(d, 21, 30, 29, Y0, "birch", top=Q)
        kitchen(d, (19, 33, 31, 33), Y0) if False else None
        corners(d, (19, 23, 31, 33), Y0, ["potted_bamboo"])
        stair_up(d, 31, 24, Y0, 7, "south")
        office(d, (19, 23, 25, 33), 7)
        lounge(d, (26, 23, 30, 33), 7)
        stair_up(d, 19, 32, 7, 12, "north")
        tables(d, (20, 23, 31, 33), 12, sit=False)
        roof_garden(d, r, "garden")
        fountain(d, 25, 4, 2)
        for x, z in ((12, 3), (38, 3), (12, 8), (38, 8)):
            plant_tree(d, x, z)
        for x in (15, 33):
            park_bench(d, x, 5, "x", "north")
    if L >= 5:
        tw = bldg(d, 34, 24, 46, 40, 6, "flat", glassy=True, win="nsew")
        ext_door(d, 40, Y0, 40, "north", double=True)
        link(d, 34, Y0, 30, "east") if False else None
        for k in range(5):
            stair_up(d, 35 if k % 2 == 0 else 45, 25 if k % 2 == 0 else 39, Y0 + 5 * k, Y0 + 5 * k + 5,
                     "south" if k % 2 == 0 else "north")
        lounge(d, (36, 26, 44, 38), Y0)
        for k in range(1, 6):
            y = Y0 + 5 * k
            office(d, (36, 25, 44, 31), y)
            tables(d, (36, 33, 44, 38), y, sit=False)
        roof_garden(d, tw, "solar")
        for i, b in enumerate((c,)):
            roof_garden(d, b, "garden")
        for x, col in ((8, "orange"), (42, "lime")):
            market_stall(d, x, 4, col)
        d.sign(40, 6, 41, "south", ["CITY", "OFFICES"], "birch", glow=True, color="cyan")
    return d


def th_cascadia(rel, L):
    d = new("Cascadia", rel, (55, 34, 55), paving="coarse_dirt")
    loft = L >= 3
    c = bldg(d, 14, 10, 28, 22, 2 if loft else 1, "gable", "z")
    ext_door(d, 21, Y0, 10, "south")
    d.fill(13, 1, 5, 29, 1, 9, "spruce_planks")                   # porch
    for x in (13, 17, 25, 29):
        for y in range(Y0, 6):
            put(d, x, y, 5, log("spruce_log"))
    for x in range(12, 31):
        d.set(x, 6, 4, st("spruce_stairs", "south"))
        for z in range(5, 10):
            d.set(x, 6, z, slab("spruce_slab"))
    for x in range(14, 29):
        if x not in (13, 17, 25, 29) and abs(x - 21) > 1:
            put(d, x, Y0, 5, "spruce_fence")
    d.sign(21, 5, 9, "north", ["GRANGE", "HALL"], "spruce")
    for x in (15, 27):
        d.chair(x, Y0, 7, "south", "spruce", sit=False)
    d.hut(15, Y0, 11)
    keep(d, 16, Y0, 11)
    for z in range(13, 18):
        d.table(21, Y0, z, "spruce", "block", "stripped_spruce_wood[axis=y]")
        d.chair(20, Y0, z, "west", "spruce")
        d.chair(22, Y0, z, "east", "spruce")
    d.chair(21, Y0, 18, "south", "spruce")
    line_items(d, 27, 11, "z", Y0, "west", ["crafting_table", "furnace", "furnace"])
    barrels(d, 27, 15, "z", Y0, 2, "west")
    d.bed(15, Y0, 19, "west")
    put(d, 15, Y0, 20, slab("spruce_slab", "top"))
    d.hearth(15, Y0, 16, "east", c["ridge"] + 2, "cobblestone", "campfire")
    chimney(d, 13, 16, Y0, c["ridge"] + 1)
    rug_in(d, (16, 12, 26, 20), Y0, ("brown_carpet", "green_carpet"))
    if L >= 2:
        w = bldg(d, 14, 22, 28, 32, 1, "gable", "z")
        link(d, 21, Y0, 22, "south")
        items = work_items(d, L)
        line_items(d, 15, 23, "z", Y0, "east", items[:9])
        line_items(d, 27, 23, "z", Y0, "west", items[9:])
        workshop(d, (17, 24, 25, 31), Y0)
        ext_door(d, 21, Y0, 32, "north", double=True)
        chimney(d, 28, 27, Y0, w["ridge"] + 1)
        # barrel shed lean-to
        nb = need(d, "barrel") - 4
        sh = bldg(d, 29, 12, 35, 22, 1, "gable", "z", win="e")
        link(d, 29, Y0 if False else Y0, 19, "east") if False else None
        ext_door(d, 32, Y0, 12, "south", double=False)
        barrels(d, 34, 13, "z", Y0, min(9, (nb + 1) // 2), "west")
        rest = nb - 2 * min(9, (nb + 1) // 2)
        if rest > 0:
            barrels(d, 30, 14, "z", Y0, (rest + 1) // 2, "east")
        for x, z in ((38, 14), (39, 14)):
            for y in (2, 3):
                put(d, x, y, z, log("spruce_log", "z"))
        cart(d, 37, 18, "z")
    if loft:
        stair_up(d, 17, 21, Y0, 7, "east")
        shelf_wall(d, (16, 11, 26, 15), "w", 7, 3)
        shelf_wall(d, (16, 11, 26, 15), "n", 7, 3)
        shelf_wall(d, (16, 11, 26, 15), "e", 7, 2)
        d.item(21, 7, 13, "enchanting_table")
        d.item(18, 7, 16, "lectern", "south")
        keep(d, 18, 7, 17)
        keep(d, 21, 7, 14)
        if L >= 4:
            d.item(15, 7, 19, "ender_chest", "east")
            keep(d, 16, 7, 19)
        dorm(d, (15, 17, 25, 21), 7, 5, head="n")
        # fire-lookout bell tower
        tx1, tz1 = 40, 4
        for x, z in ((tx1, tz1), (tx1 + 4, tz1), (tx1, tz1 + 4), (tx1 + 4, tz1 + 4)):
            for y in range(Y0, 18):
                d.set(x, y, z, log("spruce_log"))
        for y in (7, 12):
            for a in range(1, 4):
                for (x, z, ax) in ((tx1 + a, tz1, "x"), (tx1 + a, tz1 + 4, "x"), (tx1, tz1 + a, "z"),
                                   (tx1 + 4, tz1 + a, "z")):
                    d.set(x, y, z, log("spruce_log", ax))
        d.fill(tx1, 17, tz1, tx1 + 4, 17, tz1 + 4, "spruce_planks")
        for x in range(tx1, tx1 + 5):
            for z in range(tz1, tz1 + 5):
                if x in (tx1, tx1 + 4) or z in (tz1, tz1 + 4):
                    d.set(x, 18, z, "spruce_fence")
        for x, z in ((tx1, tz1), (tx1 + 4, tz1), (tx1, tz1 + 4), (tx1 + 4, tz1 + 4)):
            for y in range(18, 21):
                d.set(x, y, z, log("spruce_log"))
        d.hip(tx1, tz1, tx1 + 4, tz1 + 4, 21, "dark_oak_stairs", "dark_oak_slab", overhang=1)
        d.set(tx1 + 2, 21, tz1 + 2, "spruce_planks")
        bell(d, tx1 + 2, 20, tz1 + 2)
    else:
        for y in range(Y0, 6):
            d.set(32, y, 6, log("spruce_log"))
            d.set(34, y, 6, log("spruce_log"))
        d.fill(32, 6, 6, 34, 6, 6, log("spruce_log", "x"))
        bell(d, 33, 5, 6)
    if L >= 4:
        m = bldg(d, 2, 10, 12, 24, 2, "gable", "z")
        ext_door(d, 7, Y0, 10, "south")
        d.sign(7, 5, 9, "north", ["MAYOR"], "spruce")
        stair_up(d, 11, 12, Y0, 7, "south")
        lounge(d, (3, 11, 10, 16), Y0)
        kitchen(d, (3, 17, 10, 21), Y0)
        tables(d, (4, 17, 9, 21), Y0)
        office(d, (3, 11, 11, 16), 7)
        d.item(3, 7, 21, "jukebox")
        keep(d, 4, 7, 21)
        dorm(d, (3, 17, 11, 21), 7, 2, head="w")
        chimney(d, 2, 16, Y0, m["ridge"] + 1)
        for x in range(1, 13):
            put(d, x, 2, 6, "spruce_fence")
        flowerbed(d, 2, 7, 5, 8, ("fern", "blue_orchid", "allium", "lily_of_the_valley"))
        flowerbed(d, 9, 7, 12, 8, ("fern", "blue_orchid", "allium", "lily_of_the_valley"))
        plant_tree(d, 4, 3)
        plant_tree(d, 10, 3)
    if L >= 5:
        f = bldg(d, 36, 14, 48, 28, 2, "gable", "z", mat="mangrove_planks", up="mangrove_planks")
        d.double_door(41, Y0, 14, "x", "south", "spruce")
        for x in (40, 43):
            d.set(x, Y0, 14, AIR)
            d.set(x, Y0 + 1, 14, AIR)
            d.set(x, Y0 + 2, 14, AIR)
        d.sign(42, 6, 13, "north", ["FIRE", "HALL"], "spruce")
        for z in range(16, 26):                                      # engine bay: cart, hoses
            put(d, 42, Y0, z, "red_wool" if z % 3 else "barrel[facing=up,open=false]") if z in (18, 19, 20) else None
        cart(d, 41, 18, "z")
        kitchen(d, (37, 15, 40, 27), Y0)
        tables(d, (37, 20, 40, 27), Y0)
        for z in range(16, 26, 2):
            put(d, 47, Y0 + 1, z, "lantern[hanging=false,waterlogged=false]") if False else None
        stair_up(d, 47, 22, Y0, 7, "south")
        dorm(d, (37, 15, 45, 26), 7, 6, head="w", desks=False)
        for y in range(Y0, 24):                                      # hose-drying tower
            for x, z in ((50, 22), (52, 22), (50, 24), (52, 24)):
                d.set(x, y, z, log("spruce_log"))
            if y % 5 == 0:
                for x in (50, 51, 52):
                    d.set(x, y, 22, log("spruce_log", "x"))
                    d.set(x, y, 24, log("spruce_log", "x"))
        d.hip(50, 22, 52, 24, 24, "dark_oak_stairs", "dark_oak_slab", overhang=1)
        jl = bldg(d, 36, 34, 46, 42, 1, "gable", "x", mat="cobblestone", up="cobblestone", gable_end="cobblestone")
        ext_door(d, 41, Y0, 34, "south")
        d.sign(41, 5, 33, "north", ["JAIL"], "spruce")
        for x in range(38, 45, 2):
            d.fill(x, Y0, 39, x, 4, 41, "iron_bars")
        tables(d, (37, 35, 45, 37), Y0)
        lv = bldg(d, 2, 28, 12, 42, 1, "gable", "z", mat="stripped_spruce_log")
        ext_door(d, 7, Y0, 28, "south", double=True)
        for z in range(30, 42, 3):                                  # stalls with hay
            for x in (3, 11):
                put(d, x, Y0, z, "hay_block[axis=y]")
            d.fill(4, Y0, z + 2, 4, Y0 + 1, z + 2, "spruce_fence")
            d.fill(10, Y0, z + 2, 10, Y0 + 1, z + 2, "spruce_fence")
        d.sign(7, 5, 27, "north", ["LIVERY"], "spruce")
        # boardwalk main street with hitching rails and lamps
        for x in range(0, 55):
            for z in range(0, 3):
                d.set(x, 1, z, "spruce_planks")
        for x in range(2, 53, 6):
            put(d, x, 2, 3, "spruce_fence")
            put(d, x, 3, 3, "lantern[hanging=false,waterlogged=false]")
    return d


@design("townhall")
def townhall_v2(pack, rel, L):
    return {"Hearthwood": th_hearthwood, "Cascadia": th_cascadia, "Neoterra": th_neoterra}[pack](rel, L)


