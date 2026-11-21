"""
Industry group: blacksmith, smeltery, stonesmeltery, mechanic, stonemason, crusher, sifter.

(design notes per type are in the docstring of each @design function)
"""
import math

from hm import Design, design, AIR, D4, OPP, CW


# ================================================================================================ helpers
def need(d, block):
    return d.req["items"].get("minecraft:" + block, 0)


def place(d, block, cells, n=None):
    """Place the required number of `block` work blocks at the first cells of (x, y, z, facing)."""
    n = need(d, block) if n is None else n
    if n > len(cells):
        raise RuntimeError(f"{d.pack} {d.rel}: only {len(cells)} cells for {n} {block}")
    for x, y, z, f in cells[:n]:
        d.item(x, y, z, block, f)
    return cells[n:]


def racks(d, cells):
    n = d.req["racks"]
    if n > len(cells):
        raise RuntimeError(f"{d.pack} {d.rel}: only {len(cells)} rack cells for {n}")
    for x, y, z, f in cells[:n]:
        d.rack(x, y, z, f)
    return cells[n:]


def perim(x1, z1, x2, z2):
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if x in (x1, x2) or z in (z1, z2):
                yield x, z


def col(d, x, z, y1, y2, block):
    for y in range(y1, y2 + 1):
        d.set(x, y, z, block)


def st(name, facing, half="bottom", shape="straight"):
    return f"{name}[facing={facing},half={half},shape={shape},waterlogged=false]"


def slab(name, t="bottom"):
    return f"{name}[type={t},waterlogged=false]"


def td(name, facing, half="bottom", open_=False):
    return f"{name}[facing={facing},half={half},open={'true' if open_ else 'false'},powered=false,waterlogged=false]"


def hang(d, x, y, z, kind="lantern", chain=True):
    """Hanging lantern at y with a chain up to the first solid block above."""
    d.set(x, y, z, f"{kind}[hanging=true,waterlogged=false]")
    if chain:
        yy = y + 1
        while yy < d.sy and d.air(x, yy, z):
            yy += 1
        if yy < d.sy:
            for k in range(y + 1, yy):
                d.set(x, k, z, "chain[axis=y,waterlogged=false]")


def hooks(d, cells, y, facing):
    """Tool wall: tripwire hooks with chains between them on a wall (cells are the air cells in front)."""
    for i, (x, z) in enumerate(cells):
        if d.air(x, y, z):
            d.set(x, y, z, f"tripwire_hook[attached=false,facing={facing},powered=false]")


def forge(d, x, z, facing, top, frame, y=2, chimney=True, fuel="magma_block"):
    """Smith's hearth against a wall: (x,z) = fire cell, `facing` = side it opens to. Glowing magma bed with a
    lit campfire on it, frame cheeks either side, hood over all three, flue rising from the back cell to `top`."""
    sx, sz = D4[CW[facing]]
    bx, bz = D4[OPP[facing]]
    for k in (-1, 0, 1):
        cx, cz = x + sx * k, z + sz * k
        if k == 0:
            d.set(cx, y, cz, fuel)
            d.set(cx, y + 1, cz, f"campfire[facing={facing},lit=true,signal_fire=false,waterlogged=false]")
        else:
            d.set(cx, y, cz, frame)
            d.set(cx, y + 1, cz, frame)
        d.set(cx, y + 2, cz, frame)
    if chimney:
        for yy in range(y, top):
            d.set(x + bx, yy, z + bz, frame)
        for yy in range(y + 3, top):
            d.set(x, yy, z, frame)


def trough(d, cells):
    for x, y, z in cells:
        d.set(x, y, z, "water_cauldron[level=3]")


def gable_posts(d, x, z1, z2, y, ridge, post, axis="x"):
    """Centre king post on a gable end (for timber framing)."""
    zc = (z1 + z2) // 2
    for yy in range(y, ridge):
        if axis == "x":
            if not d.air(x, yy, zc) and "stairs" not in d.get(x, yy, zc):
                d.set(x, yy, zc, post)


def shed_roof(d, x1, z1, x2, z2, y, low, stairs, overhang=1):
    """Single-pitch roof over x1..x2/z1..z2 sloping down toward side `low` (north/south/east/west); the highest row
    is at the side opposite `low`, at y + depth - 1."""
    o = overhang
    if low in ("north", "south"):
        rows = list(range(z1 - o, z2 + o + 1))
        if low == "south":
            rows = rows[::-1]
        for i, z in enumerate(rows):
            for x in range(x1 - o, x2 + o + 1):
                d.set(x, y + i - o, z, st(stairs, OPP[low]))
    else:
        rows = list(range(x1 - o, x2 + o + 1))
        if low == "east":
            rows = rows[::-1]
        for i, x in enumerate(rows):
            for z in range(z1 - o, z2 + o + 1):
                d.set(x, y + i - o, z, st(stairs, OPP[low]))


def stone_stack(d, cells, y, blocks=("stone_bricks", "polished_andesite", "chiseled_stone_bricks", "smooth_stone")):
    """Stacks of cut stone blocks in a yard: list of (x, z, height)."""
    for i, (x, z, h) in enumerate(cells):
        for k in range(h):
            d.set(x, y + k, z, blocks[(i + k) % len(blocks)])


# --------------------------------------------------------------------------------------- pack shells
def hw_house(d, x1, z1, x2, z2, top, axis="x", wall="calcite", base="stone_bricks", floor="spruce_planks",
             step=2, overhang=1, roof="deepslate_tile", brick_to=2, post="stripped_dark_oak_log"):
    """Timber-framed plaster walls on a stone/brick plinth with a steep tiled gable. Returns the ridge height."""
    y = 2
    d.box(x1, y, z1, x2, top, z2, wall, floor=floor)
    for x, z in perim(x1, z1, x2, z2):
        for yy in range(y, brick_to + 1):
            d.set(x, yy, z, base if yy == y else "bricks")
        on = (x in (x1, x2) and z in (z1, z2)) or (z in (z1, z2) and (x - x1) % step == 0) or \
             (x in (x1, x2) and (z - z1) % step == 0)
        if on:
            col(d, x, z, brick_to + 1, top, f"{post}[axis=y]")
    for x in range(x1, x2 + 1):
        d.set(x, top, z1, f"{post}[axis=x]")
        d.set(x, top, z2, f"{post}[axis=x]")
    for z in range(z1, z2 + 1):
        d.set(x1, top, z, f"{post}[axis=z]")
        d.set(x2, top, z, f"{post}[axis=z]")
    ridge = d.gable(x1, z1, x2, z2, top + 1, axis, f"{roof}_stairs", f"{roof}_slab", wall, overhang)
    # king posts on the gable ends
    if axis == "x":
        zc = (z1 + z2) // 2
        for xx in (x1, x2):
            for yy in range(top + 1, ridge):
                if d.get(xx, yy, zc) == "minecraft:" + wall:
                    d.set(xx, yy, zc, f"{post}[axis=y]")
    else:
        xc = (x1 + x2) // 2
        for zz in (z1, z2):
            for yy in range(top + 1, ridge):
                if d.get(xc, yy, zz) == "minecraft:" + wall:
                    d.set(xc, yy, zz, f"{post}[axis=y]")
    return ridge


def cas_house(d, x1, z1, x2, z2, top, axis="z", roof="dark_oak", floor="spruce_planks", overhang=1,
              log="stripped_spruce_log", corner="spruce_log", end="spruce_planks"):
    """Horizontal log walls on a river-rock footing, dark corner posts, steep dark gable. Returns ridge."""
    y = 2
    d.box(x1, y, z1, x2, top, z2, log, floor=floor)
    for x, z in perim(x1, z1, x2, z2):
        d.set(x, y, z, "mossy_cobblestone" if (x * 3 + z) % 4 == 0 else "cobblestone")
        ax = "x" if z in (z1, z2) else "z"
        for yy in range(y + 1, top + 1):
            d.set(x, yy, z, f"{log}[axis={ax}]")
    for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        col(d, x, z, y, top, f"{corner}[axis=y]")
    return d.gable(x1, z1, x2, z2, top + 1, axis, f"{roof}_stairs", f"{roof}_slab", end, overhang)


def neo_house(d, x1, z1, x2, z2, top, floor="polished_diorite", wall="white_concrete", pil="light_gray_concrete",
              parapet=True, roof="smooth_quartz"):
    """Concrete box with pilasters, flat roof (deck at top+1) with parapet and quartz coping."""
    y = 2
    d.box(x1, y, z1, x2, top, z2, wall, floor=floor)
    for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        col(d, x, z, y, top, pil)
    d.flat(x1, z1, x2, z2, top + 1, roof, wall if parapet else None, "smooth_quartz_slab" if parapet else None)
    return top + 1


def glass_front(d, x1, x2, z, y1, y2, glass="glass_pane", mullion="light_gray_concrete", every=3):
    for x in range(x1, x2 + 1):
        for y in range(y1, y2 + 1):
            d.set(x, y, z, mullion if (x - x1) % every == every - 1 and x != x2 else glass)


def glass_side(d, x, z1, z2, y1, y2, glass="glass_pane", mullion="light_gray_concrete", every=3):
    for z in range(z1, z2 + 1):
        for y in range(y1, y2 + 1):
            d.set(x, y, z, mullion if (z - z1) % every == every - 1 and z != z2 else glass)


def neo_sign(d, x, y, z, lines, facing="north"):
    d.sign(x, y, z, facing, lines, "birch", glow=True, color="cyan")


def solar(d, x1, z1, x2, z2, y):
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            d.set(x, y, z, "daylight_detector[inverted=false,power=0]")


def fill_up(d, x, z, y, block, limit=40):
    """Fill from y upward until the first non-air block (closes a gable under a roof)."""
    k = 0
    while k < limit and d.bp.inside(x, y, z) and d.air(x, y, z):
        d.set(x, y, z, block)
        y += 1
        k += 1


# ================================================================================================ BLACKSMITH
def bs_hearthwood(rel, L):
    """Village smithy: long brick-plinth timber-framed forge with an open-sided street bay, big brick chimney on
    the west gable over a glowing hearth, anvil row, quench trough, tool wall. L4 a farrier's shoeing shed,
    L5 a paddock."""
    d = Design("Hearthwood", rel, PLOT["Hearthwood"])
    X2 = {1: 11, 2: 13}.get(L, 15)
    x1, z1, z2, top = 3, 5, 12, 5
    ridge = hw_house(d, x1, z1, X2, z2, top, "x", floor="cobblestone")
    # open work bay on the street side
    posts = [7, 11, X2] if X2 > 11 else [7, X2]
    for x in range(7, X2 + 1):
        for y in range(2, top):
            d.set(x, y, z1, AIR)
    for x in posts:
        col(d, x, z1, 2, top - 1, "dark_oak_log[axis=y]")
        for side in ("east", "west"):
            dx = D4[side][0]
            if 7 <= x + dx <= X2 and (x + dx) not in posts:
                d.set(x + dx, top - 1, z1, st("dark_oak_stairs", OPP[side], "top"))
    d.fill(7, 1, z1 - 1, X2, 1, z1 - 1, "cobblestone")
    d.window(4, 3, z1, 4, 4, z1)
    d.window(6, 3, z1, 6, 4, z1)
    for x in range(6, X2, 4):
        d.window(x, 3, z2, x, 4, z2)
    d.window(x1, 3, 10, x1, 4, 10)
    # hearth and chimney on the west gable
    forge(d, x1 + 1, 8, "east", ridge + 3, "bricks")
    d.set(x1, ridge + 3, 8, "brick_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
    d.hut(x1 + 1, 2, 6)
    d.item(x1 + 1, 2, 10, "furnace" if need(d, "furnace") else "blast_furnace", "east")
    d.set(x1 + 1, 2, 11, "coal_block")
    trough(d, [(5, 2, 11), (6, 2, 11)])
    place(d, "anvil", [(6, 2, 8, "north"), (8, 2, 8, "north"), (10, 2, 8, "north"), (12, 2, 8, "north")])
    d.item(7, 2, 11, "grindstone", "north")
    place(d, "smithing_table", [(8, 2, 11, None), (14, 2, 8, None)])
    racks(d, [(x, 2, 11, "north") for x in range(9, 15)])
    hooks(d, [(x, 11) for x in range(7, X2) if (x - 6) % 4], 4, "north")
    for x in range(6, X2, 4):
        hang(d, x, 5, 9)
    d.sign(5, 4, z1 - 1, "north", ["", "SMITHY", "~ farrier ~"], "dark_oak")
    d.keg(x1, 2, z1 - 1, "north")
    d.set(x1, 3, z1 - 1, "lantern[hanging=false,waterlogged=false]")
    if L >= 4:
        # farrier's shoeing shed: open posts, small gable, hay, hitching rail, trough
        sx1, sx2, sz1, sz2 = 18, 22, 5, 11
        d.fill(sx1, 1, sz1, sx2, 1, sz2, "packed_mud")
        for x, z in ((sx1, sz1), (sx2, sz1), (sx1, sz2), (sx2, sz2), (sx1, 8), (sx2, 8)):
            col(d, x, z, 2, 4, "dark_oak_log[axis=y]")
        for x in range(sx1, sx2 + 1):
            d.set(x, 5, sz1, "dark_oak_log[axis=x]")
            d.set(x, 5, sz2, "dark_oak_log[axis=x]")
        for z in range(sz1, sz2 + 1):
            d.set(sx1, 5, z, "dark_oak_log[axis=z]")
            d.set(sx2, 5, z, "dark_oak_log[axis=z]")
        d.gable(sx1, sz1, sx2, sz2, 6, "z", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite")
        for z in (sz1, sz2):
            for yy in range(6, 8):
                if d.get(20, yy, z) == "minecraft:calcite":
                    d.set(20, yy, z, "stripped_dark_oak_log[axis=y]")
        for z in range(sz1 + 1, sz2):
            if z != 8:
                d.set(sx2, 2, z, "dark_oak_fence")
        d.set(21, 2, 10, "hay_block[axis=y]")
        d.set(21, 3, 10, "hay_block[axis=x]")
        d.set(21, 2, 9, "hay_block[axis=z]")
        trough(d, [(19, 2, 10)])
        d.item(20, 2, 6, "anvil", "east")
        d.set(19, 2, 6, "smooth_stone")
        hang(d, 20, 4, 8)
    if L >= 5:
        px1, px2, pz1, pz2 = 15, 23, 14, 20
        d.fill(px1, 1, pz1, px2, 1, pz2, "grass_block[snowy=false]")
        for x, z in perim(px1, pz1, px2, pz2):
            d.set(x, 2, z, "dark_oak_fence")
        d.set(20, 2, pz1, "dark_oak_fence_gate[facing=north,in_wall=false,open=false,powered=false]")
        d.fill(20, 1, sz2 + 1, 20, 1, pz1 - 1, "gravel")
        trough(d, [(16, 2, 19), (17, 2, 19)])
        d.set(22, 2, 19, "hay_block[axis=y]")
        d.set(22, 2, 18, "hay_block[axis=x]")
        d.set(18, 2, 16, "oak_leaves[distance=1,persistent=true,waterlogged=false]")
        for x, z in ((px1, pz1), (px2, pz1), (px1, pz2), (px2, pz2)):
            d.set(x, 3, z, "lantern[hanging=false,waterlogged=false]")
    return d


def bs_cascadia(rel, L):
    """Logging-camp forge: steep dark A-frame turned to the street whose front third is an open forge bay on log
    posts (stone hearth wall and chimney, anvils, quench trough), log tool-room behind. L4 a coal & firewood
    lean-to, L5 a hitching rail and ore heap."""
    d = Design("Cascadia", rel, PLOT["Cascadia"], paving="coarse_dirt")
    x1, x2, z1 = 5, 13, 5
    Z2 = {1: 14, 2: 16}.get(L, 18)
    top, zw = 4, 9
    ridge = cas_house(d, x1, z1, x2, Z2, top, "z")
    # open bay at the front: remove walls z1..zw-1, keep corner posts, stone forge wall on the west side
    for z in range(z1, zw):
        for x in range(x1, x2 + 1):
            if x in (x1, x2) or z == z1:
                for y in range(2, top + 1):
                    d.set(x, y, z, AIR)
        for x in range(x1, x2 + 1):
            d.set(x, 1, z, "andesite" if (x + z) % 3 else "cobblestone")
    for x, z in ((x1, z1), (x2, z1), (x2, zw - 1)):
        col(d, x, z, 2, top, "spruce_log[axis=y]")
    for x in range(x1, x2 + 1):
        d.set(x, top, z1, "spruce_log[axis=x]")
    for z in range(z1, zw):
        d.set(x2, top, z, "spruce_log[axis=z]")
        d.set(x1, top, z, "cobblestone")
        for y in range(2, top):
            d.set(x1, y, z, "mossy_cobblestone" if (y + z) % 3 == 0 else "cobblestone")
    for x in (x1 + 1, x2 - 1):
        d.set(x, top - 1, z1, st("spruce_stairs", "east" if x == x1 + 1 else "west", "top"))
    # partition wall with door into the tool room, closed up to the roof
    for x in range(x1 + 1, x2):
        d.set(x, 2, zw, "cobblestone")
        for y in range(3, top + 1):
            d.set(x, y, zw, "stripped_spruce_log[axis=x]")
        fill_up(d, x, zw, top + 1, "spruce_planks")
    mid = (x1 + x2) // 2
    d.door(mid, 2, zw, "south", "spruce")
    # forge
    forge(d, x1 + 1, 7, "east", ridge + 3, "cobblestone")
    d.set(x1, ridge + 3, 7, "cobblestone_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
    trough(d, [(x1 + 1, 2, z1), (x1 + 2, 2, z1)])
    place(d, "anvil", [(8, 2, 7, "east"), (10, 2, 7, "east"), (8, 2, 5, "east"), (11, 2, 5, "east")])
    d.item(12, 2, 6, "grindstone", "west")
    d.hut(12, 2, 8)
    hang(d, 9, 4, 6)
    for z in range(z1 + 1, zw - 1):
        d.set(x2 + 0, 2, z, "spruce_fence") if z != 6 else None
    # sign on the gable
    d.sign(mid, ridge - 2, z1 - 1, "north", ["", "FORGE", "& IRONWORKS"], "spruce")
    # tool room
    d.item(x1 + 1, 2, zw + 1, "furnace" if need(d, "furnace") else "blast_furnace", "east")
    place(d, "smithing_table", [(x1 + 1, 2, zw + 2, None), (x2 - 1, 2, zw + 1, None)])
    d.set(x1 + 1, 2, Z2 - 1, "coal_block")
    racks(d, [(x, 2, Z2 - 1, "north") for x in range(x2 - 1, x1 + 1, -1)] + [(x2 - 1, 2, Z2 - 2, "west")])
    hooks(d, [(x, Z2 - 1) for x in range(x1 + 1, x2)], 3, "north")
    d.window(x1, 3, zw + 2, x1, 3, zw + 2)
    d.window(x2, 3, zw + 3, x2, 3, zw + 3)
    d.window(mid, 3, Z2, mid, 3, Z2)
    hang(d, mid, 4, zw + 3)
    if L >= 3:
        d.set(x2 - 1, 2, zw + 4, "chest[facing=west,type=single,waterlogged=false]")
        d.set(x2 - 1, 2, zw + 5, "iron_block")
        d.set(x2 - 1, 3, zw + 5, "spruce_pressure_plate[powered=false]")
    if L >= 4:
        # coal & firewood lean-to on the east side
        lx1, lx2, lz1, lz2 = x2 + 1, x2 + 5, zw + 1, Z2 - 1
        d.fill(lx1, 1, lz1, lx2, 1, lz2, "gravel")
        for x, z in ((lx2, lz1), (lx2, lz2), (lx2, (lz1 + lz2) // 2)):
            col(d, x, z, 2, 3, "spruce_log[axis=y]")
        for x in range(lx1, lx2 + 2):
            for z in range(lz1 - 1, lz2 + 2):
                d.set(x, 4, z, slab("dark_oak_slab"))
        for z in range(lz1 + 1, lz2):
            if z % 2:
                d.set(lx2, 2, z, "spruce_log[axis=x]")
                d.set(lx2, 3, z, "spruce_log[axis=x]")
        d.set(lx1 + 1, 2, lz2, "coal_block")
        d.set(lx1 + 2, 2, lz2, "coal_block")
        d.set(lx1 + 1, 3, lz2, "coal_block")
        d.set(lx1 + 3, 2, lz2, "raw_iron_block")
    if L >= 5:
        for z in range(10, 17):
            d.set(2, 2, z, "spruce_fence")
        trough(d, [(3, 2, 12), (3, 2, 13)])
        d.set(2, 3, 10, "lantern[hanging=false,waterlogged=false]")
        d.set(2, 3, 16, "lantern[hanging=false,waterlogged=false]")
    return d


def bs_neoterra(rel, L):
    """Metalworks studio: white concrete box with a full glass street front and cantilevered canopy, a blackstone
    forge with a steel flue through the flat roof, anvil line, quench basin and a quartz workbench wall. L3 wider
    with a reception counter, L4 solar roof, L5 an outdoor finishing yard."""
    d = Design("Neoterra", rel, PLOT["Neoterra"], paving="smooth_stone")
    X2 = {1: 12, 2: 14}.get(L, 17)
    x1, z1, z2, top = 3, 4, 13, 6
    roof = neo_house(d, x1, z1, X2, z2, top, floor="polished_andesite")
    glass_front(d, x1 + 1, X2 - 1, z1, 2, top - 1)
    d.fill(x1, top, z1, X2, top, z1, "cyan_terracotta")
    d.double_door(x1 + 6, 2, z1, "x", "south", "birch")
    for x in range(x1 - 1, X2 + 2):
        for z in (z1 - 1, z1 - 2):
            d.set(x, top, z, slab("smooth_quartz_slab", "top"))
    glass_side(d, X2, z1 + 1, z2 - 1, 3, top - 1)
    for z in range(z1 + 1, z2):
        d.set(x1, top - 1, z, "light_gray_stained_glass_pane")
    neo_sign(d, x1 + 3, top + 1, z1 - 1, ["", "METALWORKS"])
    # forge with steel flue
    forge(d, x1 + 1, 9, "east", roof + 5, "polished_blackstone_bricks")
    for yy in range(roof + 1, roof + 5):
        d.set(x1, yy, 9, "iron_block" if yy % 2 else "polished_blackstone_bricks")
        d.set(x1 + 1, yy, 9, "iron_block" if yy % 2 else "polished_blackstone_bricks")
    d.set(x1 + 1, roof + 5, 9, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    trough(d, [(x1 + 1, 2, 11), (x1 + 1, 2, 12)])
    d.item(x1 + 1, 2, 7, "furnace" if need(d, "furnace") else "blast_furnace", "east")
    d.set(x1 + 1, 2, 6, "polished_blackstone_bricks")
    d.set(x1 + 1, 2, 5, "polished_blackstone_bricks")
    place(d, "anvil", [(6, 2, 9, "north"), (8, 2, 9, "north"), (10, 2, 9, "north"), (12, 2, 9, "north")])
    d.item(6, 2, 12, "grindstone", "north")
    place(d, "smithing_table", [(7, 2, 12, None), (8, 2, 12, None)])
    racks(d, [(x, 2, 12, "north") for x in range(9, 15)])
    for x in range(6, X2):
        d.set(x, 4, 12, slab("smooth_quartz_slab", "top"))
    d.hut(X2 - 1, 2, z1 + 1)
    for x in range(x1 + 2, X2 - 1, 3):
        for z in (7, 11):
            d.set(x, roof, z, "sea_lantern")
    d.rug(5, 7, X2 - 2, 7, 2, ("yellow_carpet",), "plain")
    d.plant(x1 + 1, 2, z1 + 1, "potted_bamboo")
    if L >= 3:
        for x in range(13, 16):
            d.set(x, 2, 6, slab("smooth_quartz_slab", "top"))
        d.chair(14, 2, 7, "south", "birch", sit=False)
        d.set(15, 2, 11, "iron_block")
        d.set(15, 3, 11, "heavy_weighted_pressure_plate[power=0]")
    if L >= 4:
        solar(d, x1 + 2, z1 + 2, X2 - 2, z1 + 3, roof + 1)
        solar(d, x1 + 2, z2 - 3, X2 - 2, z2 - 2, roof + 1)
    if L >= 5:
        yx1 = X2 + 1
        d.fill(yx1, 1, z1 + 2, 21 - 1, 1, z2, "polished_andesite")
        for z in range(z1 + 2, z2 + 1):
            d.set(20, 2, z, "light_gray_concrete")
            d.set(20, 3, z, "light_gray_stained_glass_pane")
        d.door(X2, 2, 10, "east", "birch")
        d.set(19, 2, z1 + 3, "iron_block")
        d.set(19, 2, z2, "anvil[facing=east]")
        d.set(18, 2, z2, "moss_block")
        d.set(18, 3, z2, "azalea")
        d.set(20, 4, z1 + 2, "sea_lantern")
    return d


def blacksmith(pack, rel, L):
    return {"Hearthwood": bs_hearthwood, "Cascadia": bs_cascadia, "Neoterra": bs_neoterra}[pack](rel, L)


# ================================================================================================ SMELTERY
def sm_hearthwood(rel, L):
    """Victorian brick foundry: tall brick hall with stone quoins and a steep tiled roof, a square brick stack on
    the east gable, a furnace bench under a brick hood along the back wall. L3 an ore store lean-to with barrels,
    L4 a walled coal bunker, L5 a blast furnace."""
    d = Design("Hearthwood", rel, PLOT["Hearthwood"])
    x1, z1, z2, top = 7, 5, 12, 6
    X2 = {1: 13, 2: 15}.get(L, 17)
    d.box(x1, 2, z1, X2, top, z2, "bricks", floor="stone_bricks")
    for x, z in perim(x1, z1, X2, z2):
        d.set(x, 2, z, "stone_bricks")
    for x, z in ((x1, z1), (X2, z1), (x1, z2), (X2, z2)):
        for y in range(3, top + 1, 2):
            d.set(x, y, z, "stone_bricks")
    for x in range(x1, X2 + 1):
        d.set(x, top, z1, "stone_bricks")
        d.set(x, top, z2, "stone_bricks")
    ridge = d.gable(x1, z1, X2, z2, top + 1, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "bricks")
    # windows: tall, with a stone sill
    for x in [x for x in range(x1 + 2, X2 - 1, 2) if x not in (11, 12)]:
        d.window(x, 3, z1, x, 5, z1)
    for z in (7, 10):
        d.window(x1 if L < 3 else X2, 3, z, x1 if L < 3 else X2, 5, z)
        d.window(X2, 3, z, X2, 5, z)
    d.double_door(11, 2, z1, "x", "south", "spruce")
    d.set(11, 4, z1, "stone_bricks")
    d.set(12, 4, z1, "stone_bricks")
    d.sign(11, 5, z1 - 1, "north", ["", "FOUNDRY"], "dark_oak")
    d.sign(12, 5, z1 - 1, "north", ["", "& SMELTING"], "dark_oak")
    # stack on the east gable
    sx = X2 + 1
    for y in range(2, ridge + 8):
        for x in (sx, sx + 1):
            for z in (8, 9):
                d.set(x, y, z, "stone_bricks" if y in (2, ridge + 6) else "bricks")
    for x in (sx - 1, sx + 2):
        for z in (8, 9):
            d.set(x, ridge + 6, z, st("stone_brick_stairs", "west" if x < sx else "east", "top"))
    for x in (sx, sx + 1):
        for z in (7, 10):
            d.set(x, ridge + 6, z, st("stone_brick_stairs", "north" if z == 7 else "south", "top"))
        for z in (8, 9):
            d.set(x, ridge + 7, z, AIR)
    # furnace bench with hood along the back wall
    fur = [(x, 2, z2 - 1, "north") for x in range(9, 15)]
    nf = need(d, "furnace")
    place(d, "furnace", fur)
    nb = need(d, "blast_furnace")
    if nb:
        d.item(9 + nf, 2, z2 - 1, "blast_furnace", "north")
    for x in range(9, X2):
        if d.air(x, 2, z2 - 1):
            d.set(x, 2, z2 - 1, "bricks")
        d.set(x, 3, z2 - 1, "bricks")
        d.set(x, 4, z2 - 1, st("brick_stairs", "south"))
    d.item(x1 + 1, 2, z2 - 1, "crafting_table")
    d.set(x1 + 1, 2, z2 - 2, "coal_block")
    racks(d, [(X2 - 1, 2, z, "west") for z in range(7, 12)])
    d.hut(9, 2, 6)
    for x in range(9, X2, 3):
        hang(d, x, 5, 8)
    d.rug(9, 9, X2 - 2, 9, 2, ("gray_carpet",), "plain")
    if L >= 3:
        # ore store lean-to on the west with barrels of ore and charcoal
        lx1 = 2
        d.box(lx1, 2, z1 + 1, x1, 4, z2, "bricks", floor="stone_bricks")
        for x, z in perim(lx1, z1 + 1, x1, z2):
            d.set(x, 2, z, "stone_bricks")
        for z in range(z1, z2 + 2):
            d.set(lx1 - 1, 4, z, st("deepslate_tile_stairs", "east"))
            for x in range(lx1, x1):
                if d.air(x, 5, z):
                    d.set(x, 5, z, slab("deepslate_tile_slab"))
        for z in range(z1 + 2, z2):
            for y in (2, 3):
                d.set(x1, y, z, AIR) if z in (8, 9) else None
        place(d, "barrel", [(lx1 + 1, 2, z, "up") for z in range(z1 + 2, z2)] +
              [(lx1 + 2, 2, z2 - 1, "up"), (lx1 + 3, 2, z2 - 1, "up")])
        d.door(lx1 + 2, 2, z1 + 1, "south", "spruce")
        d.window(lx1, 3, 9, lx1, 3, 9)
        hang(d, lx1 + 3, 4, 9, chain=False) if d.air(lx1 + 3, 5, 9) is False else d.lamp(lx1 + 3, 4, 9)
    if L >= 4:
        # coal bunker in front
        for x, z in perim(2, 1, 6, 3):
            if z == 3 or x in (2, 6) or x == 2:
                d.set(x, 2, z, "stone_brick_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
        for x in range(3, 6):
            for z in (1, 2):
                d.set(x, 2, z, "coal_block")
            d.set(x, 1, 3, "stone_bricks")
        d.set(4, 3, 2, "coal_block")
    return d


def sm_cascadia(rel, L):
    """Mine smelter: river-rock furnace house under a steep dark roof, a tall square stone stack, a furnace bank
    along the stack wall. L3 an open log ore shed with barrels, L4 ore-cart rails and a charcoal pile, L5 a blast
    furnace."""
    d = Design("Cascadia", rel, PLOT["Cascadia"], paving="coarse_dirt")
    x1, x2, z1, z2, top = 10, 18, 6, 14, 5
    d.box(x1, 2, z1, x2, top, z2, "cobblestone", floor="stone")
    for x, z in perim(x1, z1, x2, z2):
        for y in range(2, top + 1):
            d.set(x, y, z, ("mossy_cobblestone" if (x + y * 2 + z) % 5 == 0 else
                            "andesite" if (x + y + z) % 4 == 0 else "cobblestone"))
    for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        col(d, x, z, 2, top, "spruce_log[axis=y]")
    for x in range(x1, x2 + 1):
        d.set(x, top, z1, "spruce_log[axis=x]")
        d.set(x, top, z2, "spruce_log[axis=x]")
    ridge = d.gable(x1, z1, x2, z2, top + 1, "z", "dark_oak_stairs", "dark_oak_slab", "spruce_planks")
    d.double_door(13, 2, z1, "x", "south", "spruce")
    for x in (11, 16):
        d.window(x, 3, z1, x, 4, z1)
    d.window(x1, 3, 10, x1, 4, 10)
    d.sign(14, ridge - 2, z1 - 1, "north", ["", "SMELTER", "assay office"], "spruce")
    # stack
    for y in range(2, ridge + 8):
        for x in range(x2 + 1, x2 + 4):
            for z in range(8, 11):
                if x == x2 + 2 and z == 9 and y > 3:
                    d.set(x, y, z, AIR)
                else:
                    d.set(x, y, z, "mossy_cobblestone" if (y % 4 == 0 and (x + z) % 2) else
                          "stone_bricks" if y >= ridge + 6 else "cobblestone")
    # furnace bank along the east wall
    fz = [(x2 - 1, 2, z, "west") for z in range(8, 13)]
    nf = need(d, "furnace")
    place(d, "furnace", fz)
    if need(d, "blast_furnace"):
        d.item(x2 - 1, 2, 8 + nf, "blast_furnace", "west")
    for z in range(7, z2):
        if d.air(x2 - 1, 2, z):
            d.set(x2 - 1, 2, z, "cobblestone")
        d.set(x2 - 1, 3, z, "cobblestone")
        d.set(x2 - 1, 4, z, st("cobblestone_stairs", "east"))
    d.item(x1 + 1, 2, z2 - 1, "crafting_table")
    d.set(x1 + 2, 2, z2 - 1, slab("spruce_slab", "top"))
    racks(d, [(x, 2, z2 - 1, "north") for x in range(x1 + 3, x2 - 1)] + [(x1 + 1, 2, z2 - 2, "east")])
    d.hut(x1 + 1, 2, z1 + 1)
    hang(d, 14, 4, 10)
    d.set(x1 + 1, 2, z1 + 3, "anvil[facing=north]")
    if L >= 2:
        for z in range(z1 + 1, z2):
            if z % 2 == 0:
                d.set(x2 + 1, 2, z, "spruce_log[axis=x]") if z < 8 or z > 10 else None
    if L >= 3:
        # open log ore shed with barrels, west of the house
        sx1, sx2, sz1, sz2 = 3, 7, 7, 14
        d.fill(sx1, 1, sz1, sx2, 1, sz2, "gravel")
        for z in range(sz1, sz2 + 1):
            d.set(sx1, 2, z, "cobblestone")
            for y in (3, 4):
                d.set(sx1, y, z, "stripped_spruce_log[axis=z]")
        for x in range(sx1, sx2 + 1):
            d.set(x, 2, sz2, "cobblestone")
            for y in (3, 4):
                d.set(x, y, sz2, "stripped_spruce_log[axis=x]")
        for x, z in ((sx1, sz1), (sx2, sz1), (sx2, sz2), (sx1, sz2), (sx2, 10)):
            col(d, x, z, 2, 4, "spruce_log[axis=y]")
        for x in range(sx1, sx2 + 1):
            d.set(x, 5, sz1, "spruce_log[axis=x]") if False else None
        d.gable(sx1, sz1, sx2, sz2, 5, "z", "dark_oak_stairs", "dark_oak_slab", "spruce_planks")
        place(d, "barrel", [(sx1 + 1, 2, z, "up") for z in range(sz1 + 1, sz2)])
        d.set(sx1 + 1, 3, sz1 + 1, "raw_iron_block")
        d.set(sx1 + 1, 3, sz1 + 3, "raw_copper_block")
        d.set(sx1 + 1, 3, sz1 + 5, "raw_gold_block")
        d.door(x1, 2, 12, "east", "spruce")
        d.fill(sx2 + 1, 1, 12, x1 - 1, 1, 12, "gravel")
        hang(d, 5, 4, 10)
    if L >= 4:
        for z in range(0, sz1 + 0):
            d.set(5, 2, z, "rail[shape=north_south,waterlogged=false]")
        for z in range(sz1, sz1 + 2):
            d.set(5, 2, z, "rail[shape=north_south,waterlogged=false]")
        d.set(5, 1, sz1 + 2, "cobblestone")
        # charcoal clamp
        for x, z in ((21, 15), (22, 15), (21, 16), (22, 16), (20, 16)):
            d.set(x, 2, z, "coal_block")
        d.set(21, 3, 16, "spruce_log[axis=x]")
    return d


def sm_neoterra(rel, L):
    """Smelting plant: tall light-grey concrete hall with a glass clerestory band, a round white stack with cyan
    rings linked by a flue duct, a blackstone furnace line under a hood. L3 ore barrels along the west wall and an
    overhead hoist, L4 rooftop solar, L5 a blast furnace."""
    d = Design("Neoterra", rel, PLOT["Neoterra"], paving="smooth_stone")
    x1, z1, z2, top = 3, 4, 13, 8
    X2 = {1: 10, 2: 12}.get(L, 14)
    roof = neo_house(d, x1, z1, X2, z2, top, floor="smooth_stone", wall="light_gray_concrete",
                     pil="white_concrete")
    for x, z in perim(x1, z1, X2, z2):
        if (x in (x1, X2) and z in (z1, z2)):
            continue
        d.set(x, 6, z, "light_gray_stained_glass_pane")
        d.set(x, 7, z, "light_gray_stained_glass_pane")
        d.set(x, 5, z, "cyan_terracotta")
    glass_front(d, x1 + 1, x1 + 4, z1, 2, 4)
    d.double_door(x1 + 2, 2, z1, "x", "south", "birch")
    for x in range(x1, x1 + 6):
        d.set(x, 5, z1 - 1, slab("smooth_quartz_slab", "top"))
    neo_sign(d, x1 + 6, 3, z1 - 1, ["SMELTING", "PLANT"])
    # round stack
    cx, cz = 18, 9
    for y in range(1, 26):
        for x in range(cx - 1, cx + 2):
            for z in range(cz - 1, cz + 2):
                if (x, z) == (cx, cz) and y > 2:
                    continue
                d.set(x, y, z, "cyan_terracotta" if y % 6 == 0 else "white_concrete")
        for x, z in ((cx - 2, cz), (cx + 2, cz), (cx, cz - 2), (cx, cz + 2)):
            if y <= 23:
                d.set(x, y, z, "cyan_terracotta" if y % 6 == 0 else "white_concrete")
    for x in range(cx - 1, cx + 2):
        for z in range(cz - 1, cz + 2):
            if (x, z) != (cx, cz):
                d.set(x, 26, z, "polished_blackstone_bricks")
    # flue duct from hall to stack
    for x in range(X2 + 1, cx - 2):
        d.set(x, 7, cz, "iron_block")
        d.set(x, 6, cz, "chain[axis=y,waterlogged=false]") if (x - X2) % 2 == 0 else None
    # furnace line with hood
    fur = [(x, 2, z2 - 1, "north") for x in range(x1 + 2, x1 + 8)]
    nf = need(d, "furnace")
    place(d, "furnace", fur)
    if need(d, "blast_furnace"):
        d.item(x1 + 2 + nf, 2, z2 - 1, "blast_furnace", "north")
    for x in range(x1 + 1, X2):
        if d.air(x, 2, z2 - 1):
            d.set(x, 2, z2 - 1, "polished_blackstone_bricks")
        d.set(x, 3, z2 - 1, "polished_blackstone_bricks")
        d.set(x, 4, z2 - 1, st("polished_blackstone_brick_stairs", "south"))
    d.item(X2 - 1, 2, z1 + 2, "crafting_table") if need(d, "crafting_table") else None
    racks(d, [(X2 - 1, 2, z, "west") for z in range(z1 + 3, z2 - 1)])
    d.hut(X2 - 1, 2, z1 + 1)
    d.rug(x1 + 2, z2 - 2, X2 - 2, z2 - 2, 2, ("yellow_carpet",), "plain")
    for x in range(x1 + 2, X2, 3):
        for z in (z1 + 3, z2 - 3):
            d.set(x, roof, z, "sea_lantern")
    if L >= 3:
        place(d, "barrel", [(x1 + 1, 2, z, "up") for z in range(z1 + 2, z2 - 1)])
        for z in range(z1 + 2, z2 - 1):
            d.set(x1 + 1, 4, z, slab("smooth_stone_slab", "top"))
        for y in range(5, roof):
            d.set(8, y, 8, "chain[axis=y,waterlogged=false]")
        d.set(8, 4, 8, "lantern[hanging=true,waterlogged=false]")
    if L >= 4:
        solar(d, x1 + 2, z1 + 2, X2 - 2, z1 + 3, roof + 1)
        solar(d, x1 + 2, z1 + 5, X2 - 2, z1 + 6, roof + 1)
    if L >= 5:
        for x in range(x1, X2 + 1, 2):
            d.plant(x, 2, z1 - 2, "potted_bamboo") if x != x1 + 2 and x != x1 + 3 else None
    return d


def smeltery(pack, rel, L):
    return {"Hearthwood": sm_hearthwood, "Cascadia": sm_cascadia, "Neoterra": sm_neoterra}[pack](rel, L)


# ================================================================================================ STONESMELTERY
def bottle_kiln(d, cx, cz, block="bricks", band="stone_bricks"):
    """Round brick bottle kiln (Staffordshire style) centred on (cx, cz): wide hovel tapering to a neck with a
    flared lip; hollow inside up to the open top. Returns the interior cells at floor level."""
    radius = {2: 3.6, 3: 3.6, 4: 3.6, 5: 3.6, 6: 3.4, 7: 3.0, 8: 2.6, 9: 2.2, 10: 1.7, 11: 1.6, 12: 1.6, 13: 1.6,
              14: 1.9}
    inner = []
    for y, r in radius.items():
        for x in range(cx - 4, cx + 5):
            for z in range(cz - 4, cz + 5):
                dd = math.hypot(x - cx, z - cz)
                if r - 1.05 < dd <= r:
                    d.set(x, y, z, band if y in (2, 14) else block)
                elif dd <= r - 1.05:
                    d.set(x, y, z, AIR)
                    if y == 2:
                        inner.append((x, z))
    for x, z in inner:
        d.set(x, 1, z, "bricks")
    return inner


def ss_hearthwood(rel, L):
    """Potter's kiln yard: a tall round brick bottle kiln (furnaces ring its firing chamber) beside a timber-framed
    potter's workshop with clay bins, a potter's wheel and pot shelves. L2 longer workshop, L3 a brick-walled
    kiln yard with pallets of fired bricks, L4 a drying lean-to, L5 a garden and hanging sign."""
    d = Design("Hearthwood", rel, PLOT["Hearthwood"])
    x1, z1, z2, top = 3, 4, 10, 5
    X2 = 9 if L == 1 else 12
    ridge = hw_house(d, x1, z1, X2, z2, top, "x", floor="spruce_planks")
    d.door(6, 2, z1, "south", "dark_oak")
    d.window(4, 3, z1, 4, 4, z1)
    d.window(8, 3, z1, 8, 4, z1)
    if X2 > 10:
        d.window(10, 3, z1, 10, 4, z1)
    d.window(x1, 3, 7, x1, 4, 7)
    d.door(X2, 2, 8, "east", "dark_oak")
    d.hut(4, 2, z1 + 1)
    # workshop: clay bin, wheel, shelves, workbench
    d.item(5, 2, z2 - 1, "crafting_table")
    d.set(4, 2, z2 - 1, "clay")
    d.set(4, 2, z2 - 2, "clay")
    d.set(4, 3, z2 - 1, "clay")
    d.set(x1 + 1, 2, 7, "spruce_fence")                                     # potter's wheel + stool
    d.set(x1 + 1, 3, 7, slab("smooth_stone_slab"))
    d.chair(x1 + 2, 2, 7, "east", "dark_oak", sit=False)
    racks(d, [(x, 2, z2 - 1, "north") for x in range(6, X2)])
    for x in range(5, X2):
        d.set(x, 4, z2 - 1, slab("dark_oak_slab", "top"))
        d.set(x, 5, z2 - 1, "decorated_pot[cracked=false,facing=north,waterlogged=false]" if x % 2 else
              "flower_pot")
    hang(d, 7, 4, 7)
    d.sign(6, 4, z1 - 1, "north", ["", "POTTERY", "& Kiln"], "dark_oak") if False else None
    d.sign(5, 4, z1 - 1, "north", ["", "POTTERY", "& KILN"], "dark_oak")
    # kiln
    cx, cz = 16, 15
    bottle_kiln(d, cx, cz)
    d.door(cx, 2, cz - 3, "south", "spruce")
    for y in (2, 3):
        d.set(cx, y, cz - 3, d.get(cx, y, cz - 3))
    d.set(cx, 4, cz - 3, "stone_bricks")
    fur = [(cx, 2, cz + 2, "north"), (cx - 2, 2, cz, "east"), (cx + 2, 2, cz, "west"),
           (cx - 1, 2, cz + 2, "north"), (cx + 1, 2, cz + 2, "north")]
    rest = place(d, "furnace", fur)
    for x, y, z, f in rest:
        d.set(x, y, z, "decorated_pot[cracked=false,facing=north,waterlogged=false]")
    for x, z in ((cx - 2, cz - 1), (cx + 2, cz - 1)):
        d.set(x, 2, z, "decorated_pot[cracked=false,facing=north,waterlogged=false]")
    d.set(cx, 2, cz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]") if False else None
    hang(d, cx, 5, cz)
    d.fill(cx, 1, z2 + 2, cx, 1, cz - 4, "gravel")
    d.fill(X2 + 1, 1, 8, cx, 1, 8, "gravel")
    d.fill(cx, 1, 8, cx, 1, z2 + 2, "gravel")
    if L >= 3:
        # brick yard wall round the kiln and pallets of fired bricks
        for x, z in perim(11, 12, 21, 20):
            if z == 12 and x in (cx - 1, cx, cx + 1):
                continue
            d.set(x, 2, z, "brick_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
        for x, z, h in ((12, 18, 2), (12, 19, 1), (20, 13, 2), (20, 14, 2), (13, 19, 1)):
            for k in range(h):
                d.set(x, 2 + k, z, "bricks" if (x + k) % 2 else "terracotta")
        for x, z in ((11, 12), (21, 12)):
            d.set(x, 3, z, "lantern[hanging=false,waterlogged=false]")
    if L >= 4:
        # drying lean-to on the workshop's south side: shelves of greenware
        for x in range(x1, X2 + 1):
            d.set(x, 4, z2 + 1, st("deepslate_tile_stairs", "north")) if False else None
        for x in range(x1 + 1, X2):
            d.set(x, 4, z2 + 2, st("dark_oak_stairs", "north"))
            d.set(x, 2, z2 + 2, slab("dark_oak_slab", "top")) if x % 2 else None
            d.set(x, 3, z2 + 2, "flower_pot") if x % 2 else None
        col(d, x1 + 1, z2 + 2, 2, 3, "dark_oak_fence")
        col(d, X2 - 1, z2 + 2, 2, 3, "dark_oak_fence")
    if L >= 5:
        d.fill(x1, 1, 1, x1 + 2, 1, 2, "grass_block[snowy=false]")
        for x in range(x1, x1 + 3):
            d.set(x, 2, 2, ["potted_red_tulip", "rose_bush[half=lower]", "peony[half=lower]"][x % 3]
                  if False else ["poppy", "oxeye_daisy", "cornflower"][x % 3])
        d.fill(8, 1, 1, 11, 1, 2, "grass_block[snowy=false]")
        for x in range(8, 12):
            d.set(x, 2, 2, ["poppy", "oxeye_daisy", "cornflower"][x % 3])
        d.set(x1, 2, z1 - 1, "lantern[hanging=false,waterlogged=false]")
    return d


def ss_cascadia(rel, L):
    """Lime kiln works: a massive river-rock kiln block with brick-lined draw arches (furnaces in the arches,
    unused ones glowing), smoke from the charging eye on top, and a log draw-shed built against its west face.
    L2 cordwood stacks, L3 a timber ramp up to the charging deck, L4 lime pallets, L5 lanterns and benches."""
    d = Design("Cascadia", rel, PLOT["Cascadia"], paving="coarse_dirt")
    # draw shed
    sx1, sx2, sz1, sz2 = 3, 11, 6, 14
    ridge = cas_house(d, sx1, sz1, sx2, sz2, 4, "z")
    d.door(7, 2, sz1, "south", "spruce")
    d.window(5, 3, sz1, 5, 3, sz1)
    d.window(9, 3, sz1, 9, 3, sz1)
    d.window(sx1, 3, 10, sx1, 3, 10)
    d.sign(7, ridge - 2, sz1 - 1, "north", ["", "LIME KILN", "~ co. ~"], "spruce")
    # kiln block
    kx1, kx2, kz1, kz2 = 12, 19, 7, 14
    for y in range(1, 7):
        for x in range(kx1, kx2 + 1):
            for z in range(kz1, kz2 + 1):
                d.set(x, y, z, "mossy_cobblestone" if (x * 7 + y * 3 + z * 5) % 6 == 0 else
                      "andesite" if (x + y * 2 + z) % 5 == 0 else "cobblestone")
    for x, z in perim(kx1, kz1, kx2, kz2):
        d.set(x, 7, z, "spruce_fence")
    for x in range(15, 17):
        for z in range(10, 12):
            d.set(x, 6, z, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    # draw arches: recess with brick lining, furnace at the back
    arches = [(kx1 + 1, 2, 10, "west"), (kx1 + 1, 2, 12, "west"), (13 + 1, 2, kz1 + 1, "north"),
              (16, 2, kz1 + 1, "north"), (18, 2, kz1 + 1, "north")]
    for x, y, z, f in arches:
        dx, dz = D4[f]
        rx, rz = x + dx, z + dz
        d.set(rx, 2, rz, AIR)
        d.set(rx, 3, rz, AIR)
        d.set(rx, 4, rz, st("brick_stairs", OPP[f], "top"))
        d.set(rx, 1, rz, "bricks")
        d.set(x, 3, z, "bricks")
    rest = place(d, "furnace", arches)
    for x, y, z, f in rest:
        d.set(x, y, z, "magma_block")
    for z in (10, 12):
        d.set(sx2, 2, z, AIR)
        d.set(sx2, 3, z, AIR)
        d.set(sx2, 4, z, "stripped_spruce_log[axis=z]")
    # shed interior
    d.hut(sx1 + 1, 2, sz1 + 1)
    d.item(sx1 + 1, 2, sz2 - 1, "crafting_table")
    racks(d, [(x, 2, sz2 - 1, "north") for x in range(sx1 + 2, sx2)])
    d.set(sx1 + 1, 2, sz2 - 4, "stone")
    d.set(sx1 + 1, 2, sz2 - 5, "smooth_stone")
    d.set(sx1 + 1, 3, sz2 - 4, "stone")
    hang(d, 7, 4, 10)
    hooks(d, [(x, sz2 - 1) for x in range(sx1 + 2, sx2)], 3, "north")
    if L >= 2:
        for z in range(2, 6):
            for y in (2, 3):
                d.set(21, y, z, "spruce_log[axis=x]")
    if L >= 3:
        # ramp up to the charging deck along the east face
        for i, z in enumerate(range(kz2 + 1 - 1, kz1 + 1, -1)):
            y = 2 + i
            if y > 6:
                break
            d.set(kx2 + 1, y, z, st("spruce_stairs", "north"))
            for yy in range(1, y):
                d.set(kx2 + 1, yy, z, "spruce_planks" if yy > 1 else "cobblestone")
            d.set(kx2 + 2, y, z, "spruce_fence")
        # landing and opening in the parapet
        top_z = kz2 - 4
        d.set(kx2, 7, top_z, AIR)
        d.set(kx2 + 1, 6, top_z, "spruce_planks")
        for yy in range(1, 6):
            d.set(kx2 + 1, yy, top_z, "spruce_log[axis=y]")
        d.set(kx2 + 2, 6, top_z, "spruce_fence")
        d.set(kx2 + 2, 7, top_z, "lantern[hanging=false,waterlogged=false]")
    if L >= 4:
        for x, z in ((14, 17), (15, 17), (14, 18), (17, 17)):
            d.set(x, 2, z, "spruce_slab[type=bottom,waterlogged=false]") if False else None
            d.set(x, 2, z, "white_concrete_powder")
        d.set(14, 3, 17, "white_concrete_powder")
    if L >= 5:
        d.set(sx1 - 1, 2, sz1 - 1, "spruce_fence")
        d.set(sx1 - 1, 3, sz1 - 1, "lantern[hanging=false,waterlogged=false]")
        d.set(kx1, 8, kz1, "lantern[hanging=false,waterlogged=false]")
    return d


def ss_neoterra(rel, L):
    """Kiln works: a long white workshop with a glazed sawtooth roof, a blackstone kiln wall with furnace ports
    and twin slender flues, a glass street showroom of terracotta and bricks. L2/L3 longer, L4 display plinths,
    L5 a planted forecourt."""
    d = Design("Neoterra", rel, PLOT["Neoterra"], paving="smooth_stone")
    x1, z1, z2, top = 2, 4, 13, 5
    X2 = {1: 10, 2: 13}.get(L, 17)
    d.box(x1, 2, z1, X2, top, z2, "white_concrete", floor="polished_diorite")
    for x, z in ((x1, z1), (X2, z1), (x1, z2), (X2, z2)):
        col(d, x, z, 2, top, "light_gray_concrete")
    glass_front(d, x1 + 1, X2 - 1, z1, 2, 4)
    d.fill(x1, top, z1, X2, top, z1, "cyan_terracotta")
    d.double_door(x1 + 2, 2, z1, "x", "south", "birch")
    # sawtooth roof: teeth face north (glass), slopes rise toward them
    for zt in (z1, z1 + 3, z1 + 6):
        for x in range(x1, X2 + 1):
            end = x in (x1, X2)
            for y in (6, 7):
                d.set(x, y, zt, "white_concrete" if end else "light_blue_stained_glass_pane")
            d.set(x, 8, zt, slab("smooth_quartz_slab"))
            d.set(x, 7, zt + 1, st("smooth_quartz_stairs", "north"))
            d.set(x, 6, zt + 2, st("smooth_quartz_stairs", "north"))
            if end:
                d.set(x, 6, zt + 1, "white_concrete")
    for x in range(x1, X2 + 1):
        d.set(x, 6, z2 - 1, slab("smooth_quartz_slab"))
        d.set(x, 6, z2, slab("smooth_quartz_slab"))
    # kiln wall along the back with furnace ports and flues
    nf = need(d, "furnace")
    ports = [(x, 2, z2 - 1, "north") for x in range(x1 + 2, x1 + 7)]
    place(d, "furnace", ports)
    for x in range(x1 + 1, x1 + 8):
        if d.air(x, 2, z2 - 1):
            d.set(x, 2, z2 - 1, "polished_blackstone_bricks")
        d.set(x, 3, z2 - 1, "polished_blackstone_bricks")
        d.set(x, 4, z2 - 1, "polished_blackstone_bricks")
        d.set(x, 5, z2 - 1, slab("polished_blackstone_brick_slab"))
    for fx in (x1 + 2, x1 + 6):
        for y in range(5, 12):
            d.set(fx, y, z2, "polished_blackstone_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]"
                  if y < 11 else "end_rod[facing=up]")
        d.set(fx, 5, z2 - 1, "polished_blackstone_bricks")
    # workshop
    d.hut(x1 + 1, 2, z1 + 1)
    d.item(x1 + 1, 2, z1 + 4, "crafting_table")
    racks(d, [(X2 - 1, 2, z, "west") for z in range(z1 + 4, z2)])
    d.rug(x1 + 2, z2 - 2, x1 + 6, z2 - 2, 2, ("orange_carpet",), "plain")
    for x in range(x1 + 2, X2 - 1, 3):
        d.set(x, 5, z1 + 5, "sea_lantern")
    # showroom shelves behind the glass
    for x in range(x1 + 5, X2 - 1):
        d.set(x, 2, z1 + 1, ["bricks", "white_glazed_terracotta", "smooth_stone", "cyan_glazed_terracotta"][x % 4])
    glass_side(d, X2, z1 + 1, z2 - 1, 3, 4)
    d.window(x1, 3, z1 + 3, x1, 4, z1 + 6, "glass_pane")
    neo_sign(d, x1 + 5, 5, z1 - 1, ["KILN", "WORKS"])
    if L >= 4:
        for x in range(x1 + 9, X2 - 2, 2):
            d.set(x, 2, z1 + 6, "smooth_quartz")
            d.set(x, 3, z1 + 6, ["terracotta", "bricks", "polished_deepslate"][x % 3])
    if L >= 5:
        for x in range(x1, X2 + 1, 3):
            if x not in (x1 + 2, x1 + 3):
                d.set(x, 2, z1 - 2, "moss_block")
                d.set(x, 3, z1 - 2, "azalea")
    return d


def stonesmeltery(pack, rel, L):
    return {"Hearthwood": ss_hearthwood, "Cascadia": ss_cascadia, "Neoterra": ss_neoterra}[pack](rel, L)


# ================================================================================================ MECHANIC
def stair_flight(d, cells, facing, block, y0=2, fill="spruce_planks"):
    """Straight flight: cells listed bottom-up, one step per cell; clears 2 blocks of headroom above each."""
    for i, (x, z) in enumerate(cells):
        y = y0 + i
        d.set(x, y, z, st(block, facing))
        for yy in range(y0, y):
            d.set(x, yy, z, fill)
        for k in (1, 2, 3):
            if i < len(cells) - 1 or k < 3:
                d.set(x, y + k, z, AIR)


def mc_hearthwood(rel, L):
    """Wheelwright & millwright's shop: timber-framed workshop with its gable to the street, wide carriage doors,
    a millstone 'gear' emblem in the gable, a pole lathe, wheel-dressing bench and timber stock inside. L3 rises to
    two storeys with a drafting room (lectern, cartography table) upstairs, L5 a lumber lean-to."""
    d = Design("Hearthwood", rel, PLOT["Hearthwood"])
    x1, x2, z1 = 4, 13, 5
    z2 = 11 if L <= 2 else 14
    two = L >= 3
    top = 10 if two else 5
    ridge = hw_house(d, x1, z1, x2, z2, top, "z", floor="spruce_planks")
    if two:
        # jetty band and first floor
        d.fill(x1 + 1, 6, z1 + 1, x2 - 1, 6, z2 - 1, "spruce_planks")
        for x in range(x1, x2 + 1):
            d.set(x, 6, z1, "dark_oak_log[axis=x]")
            d.set(x, 6, z2, "dark_oak_log[axis=x]")
        for z in range(z1, z2 + 1):
            d.set(x1, 6, z, "dark_oak_log[axis=z]")
            d.set(x2, 6, z, "dark_oak_log[axis=z]")
        for x in (6, 11):
            d.window(x, 8, z1, x, 9, z1)
        for z in (8, 11):
            d.window(x1, 8, z, x1, 9, z)
            d.window(x2, 8, z, x2, 9, z)
    # carriage doors with a heavy lintel
    d.double_door(8, 2, z1, "x", "south", "spruce")
    for x in range(7, 11):
        d.set(x, 4, z1, "dark_oak_log[axis=x]")
    d.window(6, 3, z1, 6, 3, z1)
    d.window(11, 3, z1, 11, 3, z1)
    d.window(x2, 3, 7, x2, 4, 7)
    d.window(x1, 3, 7, x1, 4, 7)
    # gear emblem in the street gable
    # cart-wheel emblem in the street gable: hub and rim set into the plaster
    for x in range(7, 11):
        for h in range(4):
            if x in (7, 10) and h in (0, 3):
                continue
            hub = x in (8, 9) and h in (1, 2)
            d.set(x, top + 1 + h, z1, "dark_oak_log[axis=z]" if hub else "stripped_spruce_log[axis=z]")
    d.sign(6, 4, z1 - 1, "west", ["WHEELWRIGHT", "& MILLWRIGHT"], "dark_oak", hanging=True)
    d.set(5, 4, z1 - 1, "dark_oak_fence")
    d.set(5, 4, z1 - 1, "dark_oak_planks")
    # ground floor: workshop
    d.hut(x1 + 1, 2, z1 + 1)
    d.item(x2 - 1, 2, z1 + 1, "crafting_table")
    d.item(x2 - 1, 2, z1 + 3, "anvil", "north")
    # pole lathe: grindstone chuck driven by a piston, bench in front
    d.set(x2 - 1, 2, z1 + 5, "grindstone[face=floor,facing=north]")
    d.set(x2 - 1, 2, z1 + 4, "piston[extended=false,facing=south]")
    d.set(x2 - 1, 4, z1 + 4, "grindstone[face=wall,facing=west]")
    # wheel bench in the middle: a wheel (grindstone) on a trestle
    d.set(8, 2, 8, slab("spruce_slab", "top"))
    d.set(9, 2, 8, slab("spruce_slab", "top"))
    d.set(8, 3, 8, "grindstone[face=floor,facing=east]")
    hang(d, 8, 5 if not two else 5, 7) if not two else d.lamp(9, 5, 9, hanging=True)
    if two:
        stair_flight(d, [(x1 + 1, z) for z in range(z1 + 3, z1 + 7)], "south", "spruce_stairs")
        for z in range(z1 + 3, z1 + 6):
            d.set(x1 + 2, 7, z, "spruce_fence")
        d.set(x1 + 1, 7, z1 + 2, "spruce_fence")
        d.set(x1 + 2, 7, z1 + 2, "spruce_fence")
    else:
        for z in range(z1 + 3, z2):
            d.set(x1 + 1, 2, z, "stripped_spruce_log[axis=z]")
        d.set(x1 + 1, 3, z1 + 3, "stripped_spruce_log[axis=z]")
        d.set(x1 + 1, 3, z1 + 4, "stripped_spruce_log[axis=z]")
    ground_racks = [(x, 2, z2 - 1, "north") for x in range(x1 + 3, x2)]
    up_racks = [(x, 7, z2 - 1, "north") for x in range(x1 + 3, x2)]
    racks(d, ground_racks[:3] + up_racks)
    hooks(d, [(x, z2 - 1) for x in range(x1 + 2, x2)], 4, "north")
    if two:
        d.item(x2 - 1, 7, z1 + 1, "lectern", "west")
        d.item(x2 - 1, 7, z1 + 3, "cartography_table")
        d.chair(x2 - 2, 7, z1 + 2, "west", "dark_oak", sit=False)
        d.bookshelf(x1 + 1, 7, z2 - 1, 2) if False else None
        d.set(x1 + 1, 7, z2 - 1, "bookshelf")
        d.set(x1 + 1, 8, z2 - 1, "bookshelf")
        d.rug(x1 + 3, z1 + 2, x2 - 3, z1 + 4, 7, ("red_carpet", "orange_carpet"))
        d.lamp(8, 10, 8)
        d.lamp(8, 5, 9)
    if L >= 5:
        # lumber lean-to on the east side
        for z in range(z1 + 1, z2):
            d.set(x2 + 4, 1, z, "stone_bricks")
            for x in range(x2 + 1, x2 + 5):
                d.set(x, 5, z, st("deepslate_tile_stairs", "west") if x == x2 + 4 else slab("deepslate_tile_slab"))
        for z in (z1 + 1, z2 - 1):
            col(d, x2 + 4, z, 2, 4, "dark_oak_log[axis=y]")
        for z in range(z1 + 2, z2 - 1):
            for y in (2, 3):
                d.set(x2 + 3, y, z, "stripped_oak_log[axis=z]")
        d.door(x2, 2, z1 + 6, "east", "spruce")
    return d


def mc_cascadia(rel, L):
    """Camp machine shop: long log shed with its eaves to the street and two wide roll-door bays, a rail spur
    running into a repair pit, a chain hoist with an engine block, workbenches; L3+ a drafting loft on a ladder,
    L4 a fuel store, L5 a longer track."""
    d = Design("Cascadia", rel, PLOT["Cascadia"], paving="coarse_dirt")
    x1, z1, z2, top = 3, 6, 13, 6
    X2 = {1: 13, 2: 16}.get(L, 19)
    ridge = cas_house(d, x1, z1, X2, z2, top, "x")
    # roll-door bays: openings with trapdoors rolled up under the lintel
    bays = [5, 9] + ([14] if X2 >= 16 else [])
    for bx in bays:
        for x in range(bx, bx + 3):
            for y in range(2, 5):
                d.set(x, y, z1, AIR)
            d.set(x, 5, z1, "spruce_log[axis=x]")
            d.set(x, 4, z1, td("spruce_trapdoor", "north", "top"))
        col(d, bx - 1, z1, 2, 4, "spruce_log[axis=y]")
        col(d, bx + 3, z1, 2, 4, "spruce_log[axis=y]")
    d.window(x1, 3, 9, x1, 4, 9)
    d.window(X2, 3, 9, X2, 4, 9)
    d.sign(x1 + 1, 5, z1 - 1, "north", ["MACHINE", "SHOP"], "spruce") if False else None
    # false-front sign board above the bays
    for x in range(5, 12):
        d.set(x, ridge - 1, z1 - 1, AIR) if False else None
    d.sign(7, 6, z1 - 2, "north", ["", "MACHINE", "SHOP"], "spruce") if False else None
    d.set(10, 6, z1 - 1, AIR) if False else None
    d.sign(8, 5, z1 - 1, "north", ["", "MACHINE SHOP"], "spruce") if False else None
    d.sign(9, 6, z1 - 1, "north", ["", "MACHINE", "SHOP"], "spruce") if not d.air(9, 6, z1) else None
    # rail spur into the first bay and a repair pit
    for z in range(0, z2 - 1):
        d.set(6, 2, z, "rail[shape=north_south,waterlogged=false]") if z < z1 + 4 or True else None
    for z in range(z1 + 1, z1 + 5):
        d.set(5, 1, z, "stone")
        d.set(7, 1, z, "stone")
    d.set(6, 2, z2 - 1, "spruce_planks")
    d.set(6, 3, z2 - 1, slab("spruce_slab"))
    for z in range(0, z2 - 1):
        d.set(6, 1, z, "gravel")
    # chain hoist over the second bay with an engine block on a stand
    for y in range(4, ridge):
        d.set(10, y, 9, "chain[axis=y,waterlogged=false]")
    d.set(10, 3, 9, "iron_block")
    d.set(10, 2, 9, "smooth_stone")
    d.set(9, 2, 9, "piston[extended=false,facing=up]")
    d.set(11, 2, 9, "observer[facing=west,powered=false]")
    # workbenches along the back wall
    d.hut(x1 + 1, 2, z1 + 1)
    d.item(8, 2, z2 - 1, "crafting_table")
    d.item(9, 2, z2 - 1, "anvil", "east")
    d.set(10, 2, z2 - 1, "grindstone[face=floor,facing=east]")
    d.set(11, 2, z2 - 1, slab("spruce_slab", "top"))
    hooks(d, [(x, z2 - 1) for x in range(7, X2)], 4, "north")
    loft = L >= 3
    gr = [(12, 2, z2 - 1, "north"), (X2 - 1, 2, z2 - 2, "west"), (X2 - 1, 2, z2 - 3, "west")]
    lr = [(x, 6, z2 - 1, "north") for x in range(x1 + 2, x1 + 6)]
    racks(d, gr + lr)
    for x in range(7, X2, 4):
        hang(d, x, 5, 10)
    if loft:
        d.fill(x1 + 1, 5, 9, x1 + 6, 5, z2 - 1, "spruce_planks")
        for x in range(x1 + 1, x1 + 7):
            d.set(x, 6, 9 - 1 + 1, AIR)
        for x in range(x1 + 1, x1 + 7):
            d.set(x, 6, 9, "spruce_fence") if x not in (x1 + 1,) else None
        for z in range(9, z2):
            d.set(x1 + 6, 6, z, "spruce_fence")
        d.set(x1 + 6, 6, z2 - 1, AIR)
        for y in range(2, 6):
            d.set(x1 + 7, y, z2 - 1, "ladder[facing=north,waterlogged=false]")
        d.set(x1 + 6, 6, z2 - 1, AIR)
        d.item(x1 + 1, 6, 10, "lectern", "east")
        d.item(x1 + 1, 6, 11, "cartography_table")
        d.set(x1 + 1, 6, 9, AIR)
        d.lamp(x1 + 3, 7, 11) if False else None
        # ladder cell's neighbour clears
        d.set(x1 + 6, 5, z2 - 1, "spruce_planks")
    if L >= 4:
        # fuel store: barrels-as-drums on a gravel pad by the east wall
        for z in (z1 + 1, z1 + 3):
            d.keg(X2 + 2, 2, z, "north")
        d.keg(X2 + 2, 2, z1 + 2, "east")
        d.set(X2 + 2, 3, z1 + 2, "barrel[facing=up,open=false]")
        d.fill(X2 + 1, 1, z1, X2 + 3, 1, z1 + 4, "gravel")
    if L >= 5:
        for z in range(0, z1):
            d.set(15, 2, z, "rail[shape=north_south,waterlogged=false]")
            d.set(15, 1, z, "gravel")
        d.set(15, 2, z1 + 1, "spruce_planks")
    return d


def mc_neoterra(rel, L):
    """Mech-lab: concrete box with a full-glass street front and a glazed service door, a machine test bay of
    pistons and observers behind glass, redstone-lamp ceiling; L3+ an upper storey design office with lectern and
    cartography table, L5 a roof terrace with a wind turbine mast."""
    d = Design("Neoterra", rel, PLOT["Neoterra"], paving="smooth_stone")
    x1, x2, z1, z2 = 3, 15, 4, 13
    two = L >= 3
    top = 10 if two else 5
    roof = neo_house(d, x1, z1, x2, z2, top, floor="polished_andesite")
    glass_front(d, x1 + 1, x2 - 1, z1, 2, 4)
    d.fill(x1, 5, z1, x2, 5, z1, "cyan_terracotta")
    d.double_door(x1 + 2, 2, z1, "x", "south", "birch")
    for x in range(x1 - 1, x1 + 6):
        d.set(x, 5, z1 - 1, slab("smooth_quartz_slab", "top"))
    neo_sign(d, x1 + 8, 5, z1 - 1, ["MECH", "LAB"])
    glass_side(d, x2, z1 + 1, z2 - 1, 3, 4)
    if two:
        d.fill(x1 + 1, 6, z1 + 1, x2 - 1, 6, z2 - 1, "smooth_stone")
        d.fill(x1, 6, z1, x2, 6, z2, "light_gray_concrete")
        d.fill(x1 + 1, 6, z1 + 1, x2 - 1, 6, z2 - 1, "smooth_stone")
        glass_front(d, x1 + 1, x2 - 1, z1, 7, 9, "light_gray_stained_glass_pane")
        glass_side(d, x1, z1 + 1, z2 - 1, 7, 9, "light_gray_stained_glass_pane")
        stair_flight(d, [(x, z2 - 1) for x in range(x2 - 1, x2 - 5, -1)], "west", "smooth_quartz_stairs",
                     fill="smooth_quartz")
        for x in range(x2 - 4, x2 - 2):
            d.set(x, 7, z2 - 2, "light_gray_stained_glass_pane")
    # test bay: a piston/observer rig in a glass booth
    for x, z in perim(x1 + 1, z2 - 4, x1 + 4, z2 - 1):
        if x == x1 + 4 or z == z2 - 4:
            d.set(x, 2, z, "light_gray_stained_glass_pane")
            d.set(x, 3, z, "light_gray_stained_glass_pane")
    d.set(x1 + 2, 2, z2 - 2, "piston[extended=false,facing=up]")
    d.set(x1 + 2, 3, z2 - 2, "observer[facing=east,powered=false]")
    d.set(x1 + 3, 2, z2 - 2, "sticky_piston[extended=false,facing=up]")
    d.set(x1 + 3, 3, z2 - 2, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    d.set(x1 + 1, 2, z2 - 1, "redstone_lamp[lit=true]")
    # workshop floor
    d.hut(x2 - 1, 2, z1 + 1)
    d.item(x1 + 5, 2, z2 - 1, "crafting_table")
    d.item(x1 + 6, 2, z2 - 1, "anvil", "east")
    d.set(x1 + 7, 2, z2 - 1, "grindstone[face=floor,facing=east]")
    for x in range(x1 + 5, x1 + 8):
        d.set(x, 4, z2 - 1, slab("smooth_quartz_slab", "top"))
    # central work island
    for x in range(x1 + 6, x1 + 9):
        d.set(x, 2, 8, slab("smooth_quartz_slab", "top"))
    d.set(x1 + 7, 3, 8, "observer[facing=north,powered=false]") if False else None
    d.set(x1 + 7, 3, 8, "heavy_weighted_pressure_plate[power=0]")
    gr = [(x2 - 1, 2, z, "west") for z in range(z1 + 3, z1 + 6)]
    ur = [(x, 7, z1 + 1, "north") for x in range(x1 + 1, x1 + 7)]
    racks(d, gr[:2] + gr[2:3] + ur)
    for x in range(x1 + 2, x2 - 1, 3):
        d.set(x, 6 if not two else 6, 8, "redstone_lamp[lit=true]") if not two else d.set(x, 6, 8, "redstone_lamp[lit=true]")
    if two:
        d.item(x1 + 1, 7, z2 - 2, "lectern", "east")
        d.item(x1 + 1, 7, z2 - 4, "cartography_table")
        d.chair(x1 + 3, 7, z2 - 3, "east", "birch", sit=False)
        d.set(x1 + 2, 7, z2 - 3, slab("smooth_quartz_slab", "top"))
        for x in range(x1 + 2, x2 - 1, 4):
            d.set(x, roof, 8, "sea_lantern")
        d.plant(x2 - 1, 7, z1 + 1, "potted_bamboo")
    if L >= 4:
        solar(d, x1 + 2, z1 + 2, x2 - 2, z1 + 4, roof + 1)
    if L >= 5:
        for y in range(roof + 1, roof + 7):
            d.set(x2 - 2, y, z2 - 2, "iron_bars" if y < roof + 6 else "observer[facing=up,powered=false]")
        for k in (-1, 1):
            d.set(x2 - 2 + k, roof + 6, z2 - 2, "end_rod[facing=east]" if k > 0 else "end_rod[facing=west]")
        d.set(x2 - 2, roof + 7, z2 - 2, "end_rod[facing=up]")
    return d


def mechanic(pack, rel, L):
    return {"Hearthwood": mc_hearthwood, "Cascadia": mc_cascadia, "Neoterra": mc_neoterra}[pack](rel, L)


# ================================================================================================ STONEMASON
def sn_hearthwood(rel, L):
    """Mason's lodge and banker shed: a small timber-framed lodge on the street, behind it a walled stone yard
    with pallets of dressed stone, and an open-fronted banker shed where the masons work at stonecutters set on
    stone bankers. L3+ the lodge gains a tracing office (lectern, bookshelves of patterns), L4 a grindstone."""
    d = Design("Hearthwood", rel, PLOT["Hearthwood"])
    x1, z1, z2, top = 3, 4, 10, 5
    X2 = 11 if L <= 2 else 16
    hw_house(d, x1, z1, X2, z2, top, "x", floor="spruce_planks")
    d.door(7, 2, z1, "south", "dark_oak")
    d.door(7, 2, z2, "north", "dark_oak")
    for x in (5, 9) + ((13, 15) if X2 > 11 else ()):
        d.window(x, 3, z1, x, 4, z1)
    d.sign(6, 4, z1 - 1, "north", ["", "MASON", "~ est. ~"], "dark_oak")
    d.hut(x1 + 1, 2, z1 + 1)
    d.item(x1 + 1, 2, z1 + 3, "crafting_table")
    racks(d, [(x, 2, z2 - 1, "north") for x in (5, 6, 8, 9, 10, 4)])
    hooks(d, [(x, z2 - 1) for x in (4, 5, 6, 8, 9, 10)], 4, "north")
    d.set(10, 2, z1 + 1, "chiseled_stone_bricks")
    d.set(9, 2, z1 + 1, slab("stone_brick_slab", "top"))
    hang(d, 7, 4, 7)
    if X2 > 11:
        # tracing office through a partition
        for z in range(z1 + 1, z2):
            for y in range(2, top + 1):
                d.set(11, y, z, "stripped_dark_oak_log[axis=y]" if z in (z1 + 1, z2 - 1) else "calcite")
            d.set(11, 2, z, "stone_bricks")
        d.door(11, 2, 7, "east", "dark_oak")
        for z in (z1 + 1, z1 + 2, z2 - 2, z2 - 1):
            d.bookshelf(X2 - 1, 2, z, 2 if z != z2 - 2 else 1)
        d.item(13, 2, z2 - 1, "lectern", "north")
        d.set(13, 2, z1 + 2, slab("dark_oak_slab", "top"))
        d.set(14, 2, z1 + 2, slab("dark_oak_slab", "top"))
        d.chair(13, 2, z1 + 1, "north", "dark_oak", sit=False)
        d.set(13, 3, z1 + 2, "white_carpet")
        d.rug(12, 6, 14, 8, 2, ("green_carpet", "lime_carpet"), "plain")
        d.lamp(13, 5, 7)
    # stone yard
    yz1, yz2 = z2 + 1, 19
    d.fill(x1, 1, yz1, 20, 1, yz2, "gravel")
    for x in range(x1 - 1, 22):
        d.set(x, 2, yz2 + 1, "cobblestone_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
    for z in range(z1, yz2 + 1):
        d.set(21, 2, z, "cobblestone_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
        if z > z2:
            d.set(x1 - 1, 2, z, "cobblestone_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
    for z in range(5, 8):
        d.set(21, 2, z, AIR)
    stone_stack(d, [(18, 5, 2), (19, 5, 2), (18, 7, 1), (19, 7, 2), (19, 9, 1), (18, 10, 2), (19, 10, 2)], 2)
    for x, z in ((18, 5), (19, 5)):
        d.set(x, 1, z, "spruce_planks")
    # banker shed along the back of the yard, open to the north
    n = need(d, "stonecutter")
    SX2 = 4 + 2 * (n - 1) + 1
    bz1, bz2 = 15, 19
    for x in range(x1, SX2 + 1):
        d.set(x, 2, bz2, "stone_bricks")
        for y in (3, 4):
            d.set(x, y, bz2, "calcite" if (x - x1) % 3 else "stripped_dark_oak_log[axis=y]")
    for z in range(bz1, bz2 + 1):
        for x in (x1, SX2):
            col(d, x, z, 2, 4, "calcite" if z != bz1 else "dark_oak_log[axis=y]")
            d.set(x, 2, z, "stone_bricks") if z != bz1 else None
    for x in range(x1, SX2 + 1, 3):
        col(d, x, bz1, 2, 4, "dark_oak_log[axis=y]")
    for x in range(x1, SX2 + 1):
        d.set(x, 5, bz1, "dark_oak_log[axis=x]")
    d.gable(x1, bz1, SX2, bz2, 6, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite")
    d.fill(x1 + 1, 1, bz1 + 1, SX2 - 1, 1, bz2 - 1, "stone_bricks")
    place(d, "stonecutter", [(4 + 2 * i, 2, 17, "north") for i in range(7)])
    for i in range(n - 1):
        d.set(5 + 2 * i, 2, 18, "smooth_stone") if 5 + 2 * i < SX2 else None
    if need(d, "grindstone"):
        d.item(SX2 - 1, 2, bz2 - 1, "grindstone", "north")
    for x in range(x1 + 2, SX2 - 1, 4):
        hang(d, x, 4, 17)
    return d


def sn_cascadia(rel, L):
    """Quarry stone shed: a long open pole barn (log posts, dark roof, no walls) over a line of stonecutter
    benches, a timber shear-legs derrick hoisting a block in the yard, rough-stone stacks; L3+ a log quarry office
    with plan shelves (bookshelves) and a lectern, L4 a grindstone, L5 a second stone stack and lamp posts."""
    d = Design("Cascadia", rel, PLOT["Cascadia"], paving="coarse_dirt")
    x1, x2, z1, z2 = 3, 17, 8, 15
    d.fill(x1, 1, z1, x2, 1, z2, "stone")
    for x in range(x1, x2 + 1, 2 if False else 1):
        pass
    for x in list(range(x1, x2 + 1, 7)) + [x2]:
        for z in (z1, z2):
            col(d, x, z, 2, 4, "spruce_log[axis=y]")
            d.set(x, 1, z, "cobblestone")
    for x in range(x1, x2 + 1):
        for z in (z1, z2):
            d.set(x, 5, z, "spruce_log[axis=x]")
    for z in range(z1, z2 + 1):
        for x in (x1, x2):
            d.set(x, 5, z, "spruce_log[axis=z]")
    ridge = d.gable(x1, z1, x2, z2, 6, "x", "dark_oak_stairs", "dark_oak_slab", "spruce_planks")
    # back wall boards to keep weather out
    for x in range(x1 + 1, x2):
        if d.air(x, 2, z2):
            for y in (2, 3, 4):
                d.set(x, y, z2, "spruce_planks" if y > 2 else "cobblestone")
    # stonecutter benches in two rows
    cells = [(x, 2, 11, "north") for x in range(5, 17, 2)] + [(6, 2, 13, "south"), (10, 2, 13, "south")]
    rest = place(d, "stonecutter", cells)
    d.hut(x1 + 1, 2, z1 + 1)
    racks(d, [(x, 2, z2 - 1, "north") for x in (12, 13, 14, 15, 16, 11)])
    if need(d, "grindstone"):
        d.item(x2 - 1, 2, 13, "grindstone", "west")
    for x in range(5, 17, 4):
        hang(d, x, 5, 12)
    d.item(x1 + 1, 2, z2 - 1, "crafting_table")
    # derrick in the yard: shear legs, boom, chain and a block
    mx, mz = 8, 3
    for y in range(2, 10):
        d.set(mx, y, mz, "spruce_log[axis=y]")
    for z in range(mz, mz + 4):
        d.set(mx, 9, z, "spruce_log[axis=z]") if False else None
    for x in range(mx, mx + 5):
        d.set(x, 9, mz, "stripped_spruce_log[axis=x]")
    for y in range(4, 9):
        d.set(mx + 4, y, mz, "chain[axis=y,waterlogged=false]")
    d.set(mx + 4, 3, mz, "stone")
    d.set(mx + 4, 2, mz, "cobblestone")
    d.set(mx - 1, 2, mz, "cobblestone_stairs[facing=east,half=bottom,shape=straight,waterlogged=false]")
    d.set(mx + 1, 2, mz, "cobblestone_stairs[facing=west,half=bottom,shape=straight,waterlogged=false]")
    stone_stack(d, [(14, 3, 2), (15, 3, 2), (14, 4, 1), (16, 4, 2), (15, 5, 1)], 2,
                ("cobblestone", "stone", "andesite", "stone_bricks"))
    d.sign(10, ridge - 1, z1 - 1, "north", ["", "QUARRY", "STONE CO."], "spruce") if False else None
    d.sign(10, 4, z1 - 1, "north", ["", "QUARRY", "STONE CO."], "spruce")
    d.set(10, 4, z1, "spruce_planks")
    if L >= 3:
        ox1, ox2, oz1, oz2 = 19, 24, 9, 15
        cas_house(d, ox1, oz1, ox2, oz2, 4, "z")
        d.door(21, 2, oz1, "south", "spruce")
        d.window(ox2, 3, 12, ox2, 3, 12)
        d.window(23, 3, oz1, 23, 3, oz1)
        for z in (oz1 + 2, oz1 + 3, oz1 + 4):
            d.bookshelf(ox2 - 1, 2, z, 2 if z != oz1 + 4 else 1)
        d.item(ox1 + 1, 2, oz2 - 1, "lectern", "east")
        d.set(ox1 + 2, 2, oz2 - 1, slab("spruce_slab", "top"))
        d.chair(ox1 + 3, 2, oz2 - 1, "east", "spruce", sit=False) if False else None
        d.lamp(21, 4, 12)
    if L >= 5:
        stone_stack(d, [(20, 4, 2), (21, 4, 1), (22, 4, 2)], 2, ("stone_bricks", "polished_andesite"))
        for x in (2, 18):
            d.set(x, 2, 6, "spruce_fence")
            d.set(x, 3, 6, "lantern[hanging=false,waterlogged=false]")
    return d


def sn_neoterra(rel, L):
    """Stone fabrication studio: glass showroom of polished stone samples on quartz plinths at the front, cutting
    hall behind with a line of stonecutters; L3+ a cantilevered upper materials library (bookshelves, lectern)
    with a terrace, L4 a grindstone polishing station."""
    d = Design("Neoterra", rel, PLOT["Neoterra"], paving="smooth_stone")
    x1, x2, z1, z2 = 3, 16, 4, 15
    two = L >= 3
    neo_house(d, x1, z1, x2, z2, 5, floor="polished_diorite", parapet=not two)
    glass_front(d, x1 + 1, x2 - 1, z1, 2, 4)
    d.fill(x1, 5, z1, x2, 5, z1, "cyan_terracotta")
    d.double_door(x1 + 3, 2, z1, "x", "south", "birch")
    neo_sign(d, x1 + 7, 5, z1 - 1, ["STONE", "STUDIO"])
    glass_side(d, x1, z1 + 1, z1 + 4, 2, 4)
    # showroom plinths with polished samples
    for i, x in enumerate(range(x1 + 6, x2 - 1, 2)):
        d.set(x, 2, z1 + 2, "smooth_quartz")
        d.set(x, 3, z1 + 2, ["polished_granite", "polished_diorite", "polished_andesite", "polished_deepslate",
                             "polished_tuff"][i % 5])
    d.hut(x1 + 1, 2, z1 + 1)
    d.item(x2 - 2, 2, z1 + 3, "crafting_table")
    # glass screen between showroom and cutting hall
    for x in range(x1 + 1, x2):
        if x not in (8, 9, 10):
            d.set(x, 2, 8, "light_gray_stained_glass_pane")
            d.set(x, 3, 8, "light_gray_stained_glass_pane")
    cells = [(x, 2, z2 - 2, "north") for x in range(x1 + 1, x1 + 12, 2)] + [(x1 + 1, 2, 10, "east")]
    place(d, "stonecutter", cells)
    for x in range(x1 + 1, x1 + 12):
        if d.air(x, 2, z2 - 1):
            d.set(x, 2, z2 - 1, ["smooth_stone", "polished_andesite"][x % 2])
    if need(d, "grindstone"):
        d.item(x2 - 1, 2, 10, "grindstone", "west")
    stair = [(x2 - 1, z) for z in range(z2 - 1, z2 - 5, -1)]
    gr = [(x2 - 1, 2, z, "west") for z in (z1 + 1, z1 + 2, z1 + 3)]
    for x in range(x1 + 2, x2 - 1, 3):
        d.set(x, 6, 11, "sea_lantern")
        d.set(x, 6, 6, "sea_lantern")
    if two:
        uz1 = 9
        d.fill(x1, 6, uz1, x2, 6, z2, "light_gray_concrete")
        d.box(x1, 7, uz1 - 1, x2, 10, z2, "white_concrete")
        d.fill(x1, 6, uz1 - 1, x2, 6, uz1 - 1, "light_gray_concrete")
        glass_front(d, x1 + 1, x2 - 1, uz1 - 1, 7, 9, "glass_pane")
        d.flat(x1, uz1 - 1, x2, z2, 11, "smooth_quartz", "white_concrete", "smooth_quartz_slab")
        for x in range(x1, x2 + 1):
            d.set(x, 7, z1, "white_concrete")
            d.set(x, 8, z1, "glass_pane")
        for z in range(z1, uz1 - 1):
            d.set(x1, 7, z, "white_concrete")
            d.set(x2, 7, z, "white_concrete")
        for x in range(x1 + 1, x2, 4):
            d.set(x, 7, z1 + 1, "moss_block")
            d.set(x, 8, z1 + 1, "azalea")
        d.door(x1 + 6, 7, uz1 - 1, "north", "birch")
        stair_flight(d, stair, "north", "smooth_quartz_stairs", fill="smooth_quartz")
        for z in range(z2 - 4, z2):
            d.set(x2 - 2, 7, z, "light_gray_stained_glass_pane") if z > z2 - 3 else None
        for z in (uz1 + 1, uz1 + 2, uz1 + 3):
            d.bookshelf(x1 + 1, 7, z, 2)
        d.item(x1 + 3, 7, z2 - 1, "lectern", "north")
        d.set(x1 + 4, 7, uz1 + 2, slab("smooth_quartz_slab", "top"))
        d.chair(x1 + 4, 7, uz1 + 3, "south", "birch", sit=False)
        for x in range(x1 + 2, x2 - 2, 4):
            d.set(x, 11, 12, "sea_lantern")
        racks(d, gr + [(x, 7, z2 - 1, "north") for x in range(x1 + 5, x1 + 9)])
    else:
        racks(d, gr)
    if L >= 4:
        solar(d, x1 + 2, uz1 + 1, x2 - 3, uz1 + 2, 12) if two else None
    return d


def stonemason(pack, rel, L):
    return {"Hearthwood": sn_hearthwood, "Cascadia": sn_cascadia, "Neoterra": sn_neoterra}[pack](rel, L)


# ================================================================================================ CRUSHER
def water_wheel(d, x, cy, cz, r=3, rim="dark_oak_planks", spoke="stripped_dark_oak_log"):
    """Vertical wheel in the y/z plane at column x, hub (cy, cz)."""
    for y in range(cy - r - 1, cy + r + 2):
        for z in range(cz - r - 1, cz + r + 2):
            dd = math.hypot(y - cy, z - cz)
            if r - 0.5 < dd <= r + 0.5:
                d.set(x, y, z, rim)
            elif dd <= r - 0.5 and (y == cy or z == cz):
                d.set(x, y, z, f"{spoke}[axis={'z' if y == cy else 'y'}]")
    d.set(x, cy, cz, "dark_oak_log[axis=x]")


def stamps(d, x1, x2, z, y0, frame="dark_oak_log", shaft="spruce_log", base="smooth_stone"):
    """Stamp battery: mortar box, iron stamp heads on chains, cam shaft along x, frame posts at both ends."""
    for x in range(x1, x2 + 1):
        d.set(x, y0, z, base)
        d.set(x, y0 + 5, z, f"{shaft}[axis=x]")
        if x1 < x < x2:
            d.set(x, y0 + 2, z, "iron_block")
            d.set(x, y0 + 3, z, "chain[axis=y,waterlogged=false]")
            d.set(x, y0 + 4, z, "chain[axis=y,waterlogged=false]")
    for x in (x1, x2):
        col(d, x, z, y0 + 1, y0 + 4, f"{frame}[axis=y]")


def bins(d, cells, y, wall, fills):
    """Material bins: (x1, z1, x2, z2) rectangles with a low wall on three sides and a heap inside."""
    for i, (x1, z1, x2, z2) in enumerate(cells):
        for x, z in perim(x1, z1, x2, z2):
            if z != z1 or x in (x1, x2):
                d.set(x, y, z, wall)
        for x in range(x1 + 1, x2):
            for z in range(z1, z2):
                d.set(x, y, z, fills[i % len(fills)])


def cr_hearthwood(rel, L):
    """Water-powered crushing mill: tall timber-framed mill house with a dark-oak water wheel turning in a stone
    mill race on its east side, a stamp battery and a millstone inside, gravel and sand bins out front; L3 a hoist
    loft door, L4 a sack store lean-to, L5 a footbridge over the race."""
    d = Design("Hearthwood", rel, PLOT["Hearthwood"])
    x1, x2, z1, z2, top = 4, 12, 5, 12, 8
    ridge = hw_house(d, x1, z1, x2, z2, top, "x", floor="stone_bricks", brick_to=3)
    d.door(7, 2, z1, "south", "dark_oak")
    for x in (5, 10):
        d.window(x, 4, z1, x, 5, z1)
    for x in (6, 10):
        d.window(x, 6, z2, x, 7, z2)
    d.window(x1, 5, 8, x1, 6, 9)
    # mill race and wheel
    for z in range(1, 20):
        d.set(14, 1, z, "water")
        d.set(15, 1, z, "water")
        d.set(13, 1, z, "stone_bricks")
        d.set(16, 1, z, "stone_bricks")
        d.set(13, 2, z, "stone_brick_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]") \
            if not 4 <= z <= 13 else None
        d.set(16, 2, z, "stone_brick_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]") \
            if not 4 <= z <= 13 else None
        d.set(14, 0, z, "stone_bricks")
        d.set(15, 0, z, "stone_bricks")
    water_wheel(d, 14, 5, 9, r=3)
    water_wheel(d, 15, 5, 9, r=3)
    d.set(13, 5, 9, "dark_oak_log[axis=x]")
    d.set(16, 2, 9, AIR)
    for y in range(2, 6):
        d.set(16, y, 8, "stone_bricks")
        d.set(16, y, 10, "stone_bricks")
    for y in (2, 3, 4):
        d.set(16, y, 9, "stone_bricks")
    d.set(16, 5, 9, "stone_bricks")
    # inside: line shaft from the wheel, stamp battery and millstone
    for x in range(x1 + 1, x2):
        d.set(x, 7, 9, "stripped_spruce_log[axis=x]")
    stamps(d, x1 + 3, x2 - 1, z2 - 1, 2)
    d.item(x1 + 1, 2, z2 - 1, "stonecutter", "north")
    d.item(8, 2, 8, "grindstone", "north")
    d.set(8, 4, 8, "hopper[enabled=true,facing=down]")
    d.set(8, 5, 8, "chain[axis=y,waterlogged=false]")
    d.set(8, 6, 8, "chain[axis=y,waterlogged=false]")
    d.hut(x1 + 1, 2, z1 + 1)
    d.item(x2 - 1, 2, z1 + 1, "crafting_table")
    racks(d, [(x1 + 1, 2, z, "east") for z in (z1 + 3, z1 + 4, z1 + 5)] + [(x2 - 1, 2, z1 + 3, "west"),
                                                                         (x2 - 1, 2, z1 + 4, "west")])
    hang(d, 6, 6, 8)
    hang(d, 10, 6, 8)
    d.sign(9, 4, z1 - 1, "north", ["", "CRUSHING", "MILL"], "dark_oak")
    # gravel / sand bins in front
    bins(d, [(2, 1, 4, 3), (8, 1, 10, 3)] if L < 2 else [(2, 1, 4, 3), (8, 1, 10, 3), (10, 1, 12, 3)], 2,
         "stone_brick_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]",
         ["gravel", "sand", "red_sand"])
    if L >= 3:
        # loft door with a hoist beam in the street gable side
        d.set(9, 6, z1, "dark_oak_door[facing=south,half=lower,hinge=left,open=false,powered=false]")
        d.set(9, 7, z1, "dark_oak_door[facing=south,half=upper,hinge=left,open=false,powered=false]")
        d.set(9, 8, z1 - 1, "dark_oak_log[axis=z]")
        d.set(9, 7, z1 - 1, "chain[axis=y,waterlogged=false]")
        d.fill(x1 + 1, 5, z1 + 1, x2 - 1, 5, z1 + 1, "spruce_slab[type=top,waterlogged=false]")
    if L >= 4:
        # sack store lean-to on the west
        for z in range(z1 + 1, z2):
            for x in range(1, x1):
                d.set(x, 1, z, "stone_bricks")
            d.set(1, 2, z, "stone_bricks")
            d.set(1, 3, z, "calcite")
            for x in range(1, x1):
                d.set(x, 4, z, slab("deepslate_tile_slab"))
        for z in (z1 + 1, z2 - 1):
            for x in range(1, x1):
                col(d, x, z, 2, 3, "calcite" if x > 1 else "stripped_dark_oak_log[axis=y]")
        d.door(x1, 2, 9, "west", "dark_oak")
        for z in (z1 + 2, z1 + 3):
            d.set(2, 2, z, "hay_block[axis=y]") if False else d.set(2, 2, z, "white_wool")
        d.set(2, 3, z1 + 2, "white_wool")
    if L >= 5:
        for z in (16, 17):
            for x in range(13, 17):
                d.set(x, 2, z, slab("dark_oak_slab", "top"))
        for x in range(13, 17):
            d.set(x, 3, 15, "dark_oak_fence")
            d.set(x, 3, 18, "dark_oak_fence")
        d.fill(13, 1, 16, 16, 1, 17, "water")
    return d


def cr_cascadia(rel, L):
    """Ore stamp mill: a tall log mill house over a stamp battery (iron stamps on a cam shaft), a low lean-to
    front room under a shallow slab roof, river-rock footings; L3 an ore tram running in, L4 a waste-rock dump,
    L5 a water tank on a log trestle."""
    d = Design("Cascadia", rel, PLOT["Cascadia"], paving="coarse_dirt")
    tx1, tx2, tz1, tz2 = 7, 15, 12, 19
    ridge = cas_house(d, tx1, tz1, tx2, tz2, 9, "x")
    for z in range(tz1 + 2, tz2 - 1, 3):
        d.window(tx1, 6, z, tx1, 7, z)
        d.window(tx2, 6, z, tx2, 7, z)
    for x in (9, 13):
        d.window(x, 7, tz1, x, 8, tz1)
    # front lean-to with a shallow slab roof
    lx1, lx2, lz1 = 5, 17, 5
    d.box(lx1, 2, lz1, lx2, 4, tz1, "stripped_spruce_log[axis=x]", floor="spruce_planks")
    for x, z in perim(lx1, lz1, lx2, tz1):
        if z == tz1:
            continue
        d.set(x, 2, z, "cobblestone" if (x + z) % 3 else "mossy_cobblestone")
        if z != lz1:
            for y in (3, 4):
                d.set(x, y, z, "stripped_spruce_log[axis=z]")
    for x, z in ((lx1, lz1), (lx2, lz1), (lx1, tz1), (lx2, tz1)):
        col(d, x, z, 2, 4, "spruce_log[axis=y]")
    for i, z in enumerate(range(lz1 - 1, tz1 + 1)):
        for x in range(lx1 - 1, lx2 + 2):
            if tx1 <= x <= tx2 and z >= tz1:
                continue
            d.set(x, 5 + i // 2, z, slab("dark_oak_slab", "bottom" if i % 2 == 0 else "top"))
    for z in range(lz1, tz1):
        for x in (lx1, lx2):
            fill_up(d, x, z, 5, "spruce_planks", limit=4)
    # opening into the stamp house
    for x in range(10, 13):
        for y in (2, 3, 4):
            d.set(x, y, tz1, AIR)
    d.double_door(10, 2, lz1, "x", "south", "spruce")
    for x in (7, 14):
        d.window(x, 3, lz1, x, 3, lz1)
    d.sign(12, 4, lz1 - 1, "north", ["", "STAMP MILL"], "spruce")
    # stamp battery in the tall house
    stamps(d, tx1 + 1, tx2 - 1, tz2 - 2, 2)
    d.fill(tx1 + 1, 6, tz2 - 1, tx2 - 1, 6, tz2 - 1, "spruce_planks")
    for x in range(tx1 + 2, tx2 - 1, 2):
        d.set(x, 7, tz2 - 1, "raw_iron_block" if x % 4 else "cobblestone")
    d.item(tx1 + 1, 2, tz1 + 2, "grindstone", "east")
    hang(d, 11, 7, 15)
    # front room
    d.hut(lx1 + 1, 2, lz1 + 1)
    d.item(lx2 - 1, 2, lz1 + 1, "crafting_table")
    d.item(lx2 - 1, 2, lz1 + 2, "stonecutter", "west")
    racks(d, [(lx1 + 1, 2, z, "east") for z in range(lz1 + 3, tz1)] + [(lx2 - 1, 2, lz1 + 4, "west")])
    d.lamp(11, 4, 8)
    bins(d, [(19, 6, 21, 8), (19, 10, 21, 12)], 2, "cobblestone_wall[east=none,north=none,south=none,up=true,"
         "waterlogged=false,west=none]", ["gravel", "sand"])
    if L >= 3:
        for z in range(0, lz1):
            d.set(11, 2, z, "rail[shape=north_south,waterlogged=false]") if False else None
        for x in range(tx2 + 1, 23):
            d.set(x, 2, 16, "rail[shape=east_west,waterlogged=false]")
            d.set(x, 1, 16, "gravel")
        d.door(tx2, 2, 16, "east", "spruce")
    if L >= 4:
        for x, z, h in ((2, 15, 2), (3, 15, 1), (2, 16, 3), (3, 16, 2), (2, 17, 2), (3, 17, 1), (4, 16, 1)):
            for k in range(h):
                d.set(x, 2 + k, z, "gravel" if k < h - 1 else "cobblestone")
    if L >= 5:
        for x, z in ((19, 20), (22, 20), (19, 23), (22, 23)):
            col(d, x, z, 2, 6, "spruce_log[axis=y]")
        d.fill(19, 7, 20, 22, 7, 23, "spruce_planks")
        for x, z in perim(19, 20, 22, 23):
            d.set(x, 8, z, "spruce_planks")
            d.set(x, 9, z, "spruce_planks")
        d.fill(20, 8, 21, 21, 9, 22, "water")
        d.fill(20, 10, 21, 21, 10, 22, "spruce_slab[type=bottom,waterlogged=false]")
    return d


def cr_neoterra(rel, L):
    """Aggregate plant: a glazed process hall with a jaw-crusher display (opposed pistons), round white storage
    silos on legs with cyan bands behind, and an inclined conveyor gantry feeding them; silos grow with level
    (1 / 2 / 3), L4 the conveyor, L5 rooftop solar and planters."""
    d = Design("Neoterra", rel, PLOT["Neoterra"], paving="smooth_stone")
    x1, x2, z1, z2, top = 3, 13, 3, 10, 5
    roof = neo_house(d, x1, z1, x2, z2, top, floor="polished_andesite")
    glass_front(d, x1 + 1, x2 - 1, z1, 2, 4)
    d.fill(x1, top, z1, x2, top, z1, "cyan_terracotta")
    d.double_door(x1 + 2, 2, z1, "x", "south", "birch")
    glass_side(d, x2, z1 + 1, z2 - 1, 3, 4)
    neo_sign(d, x1 + 6, top, z1 - 1, ["AGGREGATE", "PLANT"])
    # jaw crusher display
    d.set(7, 2, 7, "piston[extended=false,facing=east]")
    d.set(9, 2, 7, "sticky_piston[extended=false,facing=west]")
    d.set(8, 2, 7, "gravel")
    d.set(8, 3, 7, "hopper[enabled=true,facing=down]")
    for x in (7, 9):
        d.set(x, 3, 7, "iron_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]")
    d.hut(x1 + 1, 2, z1 + 1)
    d.item(x1 + 1, 2, z2 - 1, "crafting_table")
    d.item(x1 + 2, 2, z2 - 1, "stonecutter", "north")
    d.item(x1 + 3, 2, z2 - 1, "grindstone", "north")
    racks(d, [(x, 2, z2 - 1, "north") for x in range(x1 + 5, x2)])
    for x in range(x1 + 2, x2 - 1, 3):
        d.set(x, roof, 6, "sea_lantern")
    d.door(x1 + 4, 2, z2, "north", "birch")
    # silos
    nsil = {1: 1, 2: 2}.get(L, 3)
    for i in range(nsil):
        cx, cz = 5 + 6 * i, 15
        for x in range(cx - 2, cx + 3):
            for z in range(cz - 2, cz + 3):
                if abs(x - cx) == 2 and abs(z - cz) == 2:
                    continue
                for y in range(6, 15):
                    d.set(x, y, z, "cyan_terracotta" if y in (7, 12) else "white_concrete")
                d.set(x, 15, z, slab("smooth_quartz_slab"))
        d.set(cx, 15, cz, "smooth_quartz")
        d.set(cx, 16, cz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        for x, z in ((cx - 1, cz - 1), (cx + 1, cz - 1), (cx - 1, cz + 1), (cx + 1, cz + 1)):
            col(d, x, z, 2, 5, "iron_bars")
        d.set(cx, 5, cz, "hopper[enabled=true,facing=down]")
        d.set(cx, 1, cz, "gravel")
    d.fill(2, 1, 12, 20, 1, 18, "polished_andesite")
    if L >= 4:
        # inclined conveyor gantry from a ground hopper to the silo tops
        for i, z in enumerate(range(3, 13)):
            y = 2 + i
            d.set(20, y, z, st("smooth_stone_stairs" if False else "polished_andesite_stairs", "south"))
            if i % 3 == 0:
                for yy in range(2, y):
                    d.set(20, yy, z, "iron_bars")
        d.set(20, 2, 2, "hopper[enabled=true,facing=down]")
        for x in range(8, 21):
            d.set(x, 12, 13, slab("smooth_stone_slab", "top"))
        for z in (13,):
            for x in range(8, 21):
                d.set(x, 13, z, "iron_bars") if False else None
    if L >= 5:
        solar(d, x1 + 1, z1 + 1, x2 - 1, z1 + 3, roof + 1)
        for x in (x1 + 5, x1 + 8):
            d.set(x, 2, z1 - 2, "moss_block")
            d.set(x, 3, z1 - 2, "azalea")
    return d


def crusher(pack, rel, L):
    return {"Hearthwood": cr_hearthwood, "Cascadia": cr_cascadia, "Neoterra": cr_neoterra}[pack](rel, L)


# ================================================================================================ SIFTER
def sieve(d, x, y, z, wood="oak", tray=None):
    """Sieve on a stand: fence legs with a trapdoor screen laid on top."""
    d.set(x, y, z, f"{wood}_fence")
    d.set(x, y + 1, z, tray or td(f"{wood}_trapdoor", "north"))


def sf_hearthwood(rel, L):
    """Sieving shed: small open-fronted timber shed on a brick plinth with a steep tiled roof, sieve stands with
    oak screens and a wash tub, brick bins of gravel / sand / dirt; L3 longer with a second bay, L5 a cottage
    garden of sifted soil."""
    d = Design("Hearthwood", rel, PLOT["Hearthwood"])
    x1, z1, z2, top = 3, 5, 10, 4
    X2 = 10 if L <= 2 else 14
    hw_house(d, x1, z1, X2, z2, top, "x", floor="bricks")
    for x in range(x1 + 1, X2):
        for y in range(2, top):
            d.set(x, y, z1, AIR)
    for x in range(x1, X2 + 1, 4 if X2 == 14 else 7):
        col(d, x, z1, 2, top - 1, "dark_oak_log[axis=y]")
    col(d, X2, z1, 2, top - 1, "dark_oak_log[axis=y]")
    d.window(x1, 3, 8, x1, 3, 8)
    d.hut(x1 + 1, 2, z1 + 1)
    d.item(x1 + 1, 2, z2 - 1, "crafting_table")
    racks(d, [(x1 + 2, 2, z2 - 1, "north"), (x1 + 3, 2, z2 - 1, "north")])
    for x in range(x1 + 4, X2 - 1, 2):
        sieve(d, x, 2, z1 + 3)
    d.set(X2 - 1, 2, z2 - 1, "water_cauldron[level=3]")
    d.set(X2 - 1, 2, z2 - 2, "water_cauldron[level=2]")
    for x in range(x1 + 4, X2 - 1):
        d.set(x, 2, z2 - 1, ["gravel", "sand", "dirt", "clay"][x % 4]) if x % 2 == 0 else None
    hang(d, x1 + 4, top, 7)
    d.sign(x1 + 1, 3, z1 - 1, "north", ["", "SIFTER"], "dark_oak") if False else None
    d.sign(x1 + 2, top + 0, z1 - 1, "north", ["", "SIFTER"], "dark_oak")
    bins(d, [(X2 + 2, 6, X2 + 4, 8), (X2 + 2, 9, X2 + 4, 11)] if X2 + 4 < 19 else [],
         2, "brick_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]",
         ["gravel", "sand"])
    if L >= 2:
        bins(d, [(x1, 1, x1 + 2, 3)], 2,
             "brick_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]", ["dirt"])
    if L >= 5:
        d.fill(x1, 1, 12, X2, 1, 14, "grass_block[snowy=false]")
        for x in range(x1, X2 + 1):
            d.set(x, 2, 14, "dark_oak_fence")
        for x in range(x1 + 1, X2, 2):
            d.set(x, 2, 12, ["poppy", "oxeye_daisy", "cornflower", "allium"][x % 4])
    return d


def sf_cascadia(rel, L):
    """Sluice camp: a small log screen house with rocker sieves, and a long timber sluice box on trestles with
    water running down it; gravel heap at the head; L3 longer sluice and a second rocker, L5 a lantern rail."""
    d = Design("Cascadia", rel, PLOT["Cascadia"], paving="coarse_dirt")
    x1, x2, z1, z2 = 3, 9, 6, 12
    ridge = cas_house(d, x1, z1, x2, z2, 4, "z")
    d.door(6, 2, z1, "south", "spruce")
    d.window(x1, 3, 9, x1, 3, 9)
    d.window(x2, 3, 9, x2, 3, 9)
    d.sign(6, ridge - 2, z1 - 1, "north", ["", "SLUICE", "& SCREENS"], "spruce")
    d.hut(x1 + 1, 2, z1 + 1)
    d.item(x2 - 1, 2, z1 + 1, "crafting_table")
    racks(d, [(x1 + 1, 2, z2 - 1, "east"), (x1 + 1, 2, z2 - 2, "east")])
    sieve(d, x2 - 1, 2, z2 - 2, "spruce")
    d.set(x2 - 1, 2, z2 - 1, "water_cauldron[level=3]")
    hang(d, 6, 4, 9)
    # sluice box on trestles
    sx2 = 17 if L <= 2 else 20
    for x in range(x2 + 1, sx2 + 1):
        d.set(x, 3, 9, "spruce_planks")
        d.set(x, 4, 8, "spruce_planks")
        d.set(x, 4, 10, "spruce_planks")
        d.set(x, 4, 9, "water")
        if (x - x2) % 3 == 1:
            col(d, x, 8, 2, 3, "spruce_fence")
            col(d, x, 10, 2, 3, "spruce_fence")
    d.set(sx2 + 1, 4, 9, "spruce_planks")
    d.set(sx2 + 1, 3, 9, "spruce_planks")
    d.set(x2, 4, 9, "spruce_planks")
    # gravel head heap and output barrel
    for x, z, h in ((sx2 - 1, 12, 2), (sx2, 12, 1), (sx2 - 2, 12, 1), (sx2 - 1, 13, 1)):
        for k in range(h):
            d.set(x, 2 + k, z, "gravel")
    d.set(x2 + 2, 2, 12, "sand")
    d.set(x2 + 3, 2, 12, "sand")
    if L >= 3:
        sieve(d, 13, 2, 5, "spruce")
        sieve(d, 15, 2, 5, "spruce")
        d.set(14, 2, 5, "water_cauldron[level=3]")
        for x in (12, 16):
            col(d, x, 4, 2, 3, "spruce_log[axis=y]")
            col(d, x, 6, 2, 3, "spruce_log[axis=y]")
        for x in range(11, 18):
            for z in range(3, 8):
                d.set(x, 4, z, slab("dark_oak_slab"))
    if L >= 5:
        for x in range(x2 + 2, sx2, 4):
            d.set(x, 2, 7, "spruce_fence")
            d.set(x, 3, 7, "lantern[hanging=false,waterlogged=false]")
    return d


def sf_neoterra(rel, L):
    """Screening pavilion: a flat quartz canopy on slim concrete columns over vibrating screens (iron trapdoor decks
    on smooth-stone frames with hoppers below), a glass control kiosk; L3 a second screen line, L5 planted roof."""
    d = Design("Neoterra", rel, PLOT["Neoterra"], paving="smooth_stone")
    x1, x2, z1, z2 = 3, 13 if L <= 2 else 15, 4, 11
    d.fill(x1, 1, z1, x2, 1, z2, "polished_andesite")
    for x, z in perim(x1, z1, x2, z2):
        if (x - x1) % 4 == 0 and z in (z1, z2) or x in (x1, x2) and z in (z1, z2):
            col(d, x, z, 2, 5, "light_gray_concrete")
    d.fill(x1 - 1, 6, z1 - 1, x2 + 1, 6, z2 + 1, "smooth_quartz")
    for x in range(x1 - 1, x2 + 2):
        d.set(x, 6, z1 - 1, "cyan_terracotta")
    for x in range(x1 + 2, x2 - 1, 3):
        d.set(x, 6, 7, "sea_lantern")
    # back glass wall
    for x in range(x1 + 1, x2):
        if d.air(x, 2, z2):
            for y in range(2, 6):
                d.set(x, y, z2, "glass_pane")
    # control kiosk
    for x, z in perim(x1, z1, x1 + 4, z1 + 3):
        if (x, z) != (x1, z1):
            for y in (2, 3, 4):
                if d.air(x, y, z):
                    d.set(x, y, z, "light_gray_stained_glass_pane")
    d.door(x1 + 2, 2, z1 + 3, "south", "birch")
    d.hut(x1 + 1, 2, z1 + 1)
    d.item(x1 + 3, 2, z1 + 1, "crafting_table")
    racks(d, [(x1 + 1, 2, z1 + 2, "east"), (x1 + 3, 2, z1 + 2, "west")])
    # screen lines
    lines = [8] + ([10] if L >= 3 else [])
    for z in lines:
        for x in range(x1 + 5, x2 - 1):
            d.set(x, 2, z, "hopper[enabled=true,facing=down]" if x % 2 else "smooth_stone")
            d.set(x, 3, z, "iron_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]")
    d.set(x2 - 1, 2, 8, "gravel")
    d.set(x2 - 1, 3, 8, "gravel")
    neo_sign(d, x1 + 6, 5, z1 - 1, ["SCREENING"]) if False else None
    d.sign(x1 + 6, 6, z1 - 2, "north", ["SCREENING", "WORKS"], "birch", glow=True, color="cyan")
    d.set(x1 + 6, 6, z1 - 1, "cyan_terracotta")
    if L >= 5:
        for x in range(x1, x2 + 1, 2):
            d.set(x, 7, z2 + 1, "moss_block")
            d.set(x, 8, z2 + 1, "azalea")
    return d


def sifter(pack, rel, L):
    return {"Hearthwood": sf_hearthwood, "Cascadia": sf_cascadia, "Neoterra": sf_neoterra}[pack](rel, L)


# ================================================================================================ GROWTH
# Every hut grows into a works complex: the core building (drawn by the per-type functions above) plus one new,
# fully furnished building per level - a store at L2, a second workshop at L3, a two-storey sales room & office at
# L4 and a two-storey mess hall with stores above at L5 - laid out per pack (Hearthwood: a village yard of gabled
# timber buildings; Cascadia: long log sheds along a camp street; Neoterra: a campus of flat-roofed glass boxes).
PLOT = {"Hearthwood": (45, 40, 45), "Cascadia": (50, 40, 41), "Neoterra": (46, 40, 48)}
SLOTS = {
    "Hearthwood": [(27, 3, 37, 10, 1, "x"), (3, 26, 17, 33, 1, "x"), (28, 14, 38, 25, 2, "z"),
                   (19, 31, 41, 40, 3, "x")],
    "Cascadia": [(29, 4, 36, 15, 1, "z"), (39, 4, 47, 19, 1, "z"), (3, 27, 21, 35, 2, "x"),
                 (25, 23, 46, 36, 3, "x")],
    "Neoterra": [(27, 3, 38, 13, 1, None), (27, 17, 42, 28, 2, None), (3, 25, 19, 37, 2, None),
                 (22, 32, 44, 46, 3, None)],
}
WOOD = {"Hearthwood": "dark_oak", "Cascadia": "spruce", "Neoterra": "birch"}
RUGS = {"Hearthwood": ("red_carpet", "orange_carpet"), "Cascadia": ("green_carpet", "brown_carpet"),
        "Neoterra": ("cyan_carpet", "light_gray_carpet")}
TITLES = {
    "blacksmith": ["IRON STORE", "ARMOURY", "SMITHY SHOP", "SMITHS' HALL"],
    "smeltery": ["ORE STORE", "CASTING SHOP", "ASSAY OFFICE", "FOUNDRY HALL"],
    "stonesmeltery": ["CLAY STORE", "GLAZING SHOP", "BRICK SALES", "KILNMEN'S HALL"],
    "mechanic": ["PARTS STORE", "ASSEMBLY", "WORKS OFFICE", "FITTERS' HALL"],
    "stonemason": ["STONE STORE", "CARVING SHOP", "MASON'S OFFICE", "MASONS' HALL"],
    "crusher": ["SACK STORE", "GRADING SHOP", "MILL OFFICE", "MILLERS' HALL"],
    "sifter": ["SIEVE STORE", "WASH HOUSE", "SIFTER OFFICE", "WORKERS' HALL"],
}
TOOLS = {
    "blacksmith": ["anvil", "grindstone", "smithing_table"],
    "smeltery": ["furnace", "cauldron", "crafting_table"],
    "stonesmeltery": ["furnace", "crafting_table", "clay"],
    "mechanic": ["crafting_table", "piston", "anvil", "observer"],
    "stonemason": ["stonecutter", "grindstone", "smooth_stone"],
    "crusher": ["grindstone", "stonecutter", "gravel"],
    "sifter": ["sieve", "water_cauldron", "crafting_table"],
}
STOCK = {  # what sits on the shelves / in the bins of each trade
    "blacksmith": ["iron_block", "coal_block", "raw_iron_block", "chain"],
    "smeltery": ["raw_iron_block", "raw_copper_block", "raw_gold_block", "coal_block"],
    "stonesmeltery": ["clay", "bricks", "terracotta", "smooth_stone"],
    "mechanic": ["iron_block", "piston", "observer", "redstone_lamp"],
    "stonemason": ["stone_bricks", "chiseled_stone_bricks", "polished_andesite", "smooth_stone"],
    "crusher": ["gravel", "sand", "white_wool", "red_sand"],
    "sifter": ["sand", "gravel", "white_wool", "clay"],
}


def _state(name, facing):
    if name in ("anvil",):
        return f"anvil[facing={facing}]"
    if name in ("grindstone",):
        return f"grindstone[face=floor,facing={facing}]"
    if name in ("stonecutter",):
        return f"stonecutter[facing={facing}]"
    if name in ("furnace", "smoker", "blast_furnace"):
        return f"{name}[facing={facing},lit=false]"
    if name in ("piston", "observer"):
        return f"{name}[facing=up]" if name == "observer" else "piston[extended=false,facing=up]"
    if name == "observer":
        return "observer[facing=up,powered=false]"
    if name == "water_cauldron":
        return "water_cauldron[level=3]"
    if name == "chain":
        return "chain[axis=y,waterlogged=false]"
    if name == "redstone_lamp":
        return "redstone_lamp[lit=false]"
    return name


def _fix(st_):
    return st_.replace("observer[facing=up]", "observer[facing=up,powered=false]")


def lamp_post(d, x, z):
    P = d.pack
    if not (d.bp.inside(x, 6, z) and all(d.air(x, y, z) for y in range(2, 6))):
        return
    if P == "Hearthwood":
        col(d, x, z, 2, 3, "dark_oak_fence")
        d.set(x, 4, z, "lantern[hanging=false,waterlogged=false]")
    elif P == "Cascadia":
        col(d, x, z, 2, 3, "spruce_fence")
        d.set(x, 4, z, "lantern[hanging=false,waterlogged=false]")
    else:
        col(d, x, z, 2, 4, "light_gray_concrete_powder" if False else
            "andesite_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
        d.set(x, 5, z, "end_rod[facing=up]") if False else d.set(x, 5, z, "sea_lantern")


def tree(d, x, z):
    P = d.pack
    log, leaves = {"Hearthwood": ("oak_log", "oak_leaves"), "Cascadia": ("spruce_wood", "spruce_leaves"),
                   "Neoterra": ("birch_log", "birch_leaves")}[P]
    lv = f"{leaves}[distance=1,persistent=true,waterlogged=false]"
    if P == "Cascadia":
        h = 8
        for y in range(2, 2 + h):
            d.set(x, y, z, f"{log}[axis=y]")
        for y in range(4, 2 + h + 1):
            r = max(0, (2 + h - y) // 2)
            for a in range(-r, r + 1):
                for b in range(-r, r + 1):
                    if abs(a) + abs(b) <= r + (1 if r > 1 else 0) and (a, b) != (0, 0) and d.bp.inside(x + a, y, z + b) and d.air(x + a, y, z + b):
                        d.set(x + a, y, z + b, lv)
        d.set(x, 2 + h, z, lv)
    else:
        h = 5
        for y in range(2, 2 + h):
            d.set(x, y, z, f"{log}[axis=y]")
        for y in range(5, 9):
            r = 2 if y < 8 else 1
            for a in range(-r, r + 1):
                for b in range(-r, r + 1):
                    if abs(a) == r and abs(b) == r and (y == 7 or r == 1):
                        continue
                    if d.bp.inside(x + a, y, z + b) and d.air(x + a, y, z + b):
                        d.set(x + a, y, z + b, lv)
        if P == "Neoterra":
            for a, b in perim(x - 1, z - 1, x + 1, z + 1):
                d.set(a, 2, b, slab("smooth_stone_slab"))
            d.set(x, 1, z, "moss_block")


def bench(d, x, z, facing):
    P = d.pack
    w = WOOD[P]
    sx, sz = D4[CW[facing]]
    for k in (0, 1):
        d.set(x + sx * k, 2, z + sz * k, st(f"{w}_stairs", OPP[facing]))


def WALLST(name):
    return f"{name}[east=none,north=none,south=none,up=true,waterlogged=false,west=none]"


MAT = {
    "Hearthwood": dict(post="dark_oak_log[axis=y]", beam="dark_oak_log", board="calcite", stone="stone_bricks",
                       lowwall="stone_brick_wall", fence="dark_oak_fence", roof="deepslate_tile", yard="gravel",
                       floor="spruce_planks", deck="spruce_planks", stairs="dark_oak", sign="dark_oak"),
    "Cascadia": dict(post="spruce_log[axis=y]", beam="spruce_log", board="spruce_planks", stone="cobblestone",
                     lowwall="cobblestone_wall", fence="spruce_fence", roof="dark_oak", yard="gravel",
                     floor="spruce_planks", deck="spruce_planks", stairs="spruce", sign="spruce"),
    "Neoterra": dict(post="light_gray_concrete", beam="light_gray_concrete", board="white_concrete",
                     stone="polished_andesite", lowwall="andesite_wall", fence="birch_fence", roof="smooth_quartz",
                     yard="polished_andesite", floor="polished_diorite", deck="smooth_stone",
                     stairs="smooth_quartz", sign="birch"),
}


def roofset(d):
    r = MAT[d.pack]["roof"]
    if r == "smooth_quartz":
        return "smooth_quartz_stairs", "smooth_quartz_slab"
    return f"{r}_stairs", f"{r}_slab"


def hall(d, x1, z1, x2, z2, storeys=1, axis=None, title=None, sh=5, clerestory=False):
    """Pack-styled building shell with floors, windows, a street door (north), stairs and a sign.
    Returns dict(ridge, top, mx, rooms=[(fx1, fz1, fx2, fz2, y, reserved, keep)])."""
    P = d.pack
    M = MAT[P]
    wood = WOOD[P]
    want = storeys
    if storeys > 1 and (z2 - z1) < sh + 4 and (x2 - x1) < sh + 4:
        storeys = 1
    top = sh * storeys
    if P == "Hearthwood":
        ridge = hw_house(d, x1, z1, x2, z2, top, axis or "x", floor=M["floor"])
    elif P == "Cascadia":
        ridge = cas_house(d, x1, z1, x2, z2, top, axis or "z")
    else:
        ridge = neo_house(d, x1, z1, x2, z2, top, floor=M["floor"])
    mx = (x1 + x2) // 2
    for k in range(1, storeys):
        yd = 1 + sh * k
        d.fill(x1 + 1, yd, z1 + 1, x2 - 1, yd, z2 - 1, M["deck"])
        for x, z in perim(x1, z1, x2, z2):
            corner = x in (x1, x2) and z in (z1, z2)
            if P == "Neoterra":
                d.set(x, yd, z, "light_gray_concrete" if corner else "cyan_terracotta")
            else:
                d.set(x, yd, z, f"{M['beam']}[axis={'y' if corner else 'x' if z in (z1, z2) else 'z'}]")
    rows = [2 + sh * k for k in range(storeys)]
    for k, yb in enumerate(rows):
        hs = [(yb + 1, yb + 2)] + ([(yb + sh - 2, yb + sh - 2)] if clerestory and sh >= 7 else [])
        for ya, yb2 in hs:
            if P == "Neoterra":
                for x, z in perim(x1, z1, x2, z2):
                    if x in (x1, x2) and z in (z1, z2):
                        continue
                    along = (x - x1) if z in (z1, z2) else (z - z1)
                    if k == 0 and ya == yb + 1 and z == z1 and mx - 1 <= x <= mx + 2:
                        continue
                    for y in range(ya, yb2 + 1):
                        d.set(x, y, z, "light_gray_concrete" if along % 4 == 0 else "glass_pane")
            else:
                for x in range(x1 + 3, x2 - 1, 4):
                    for z in (z1, z2):
                        if k == 0 and z == z1 and abs(x - mx) <= 1:
                            continue
                        d.window(x, ya, z, x, yb2, z)
                for z in range(z1 + 3, z2 - 1, 4):
                    for x in (x1, x2):
                        d.window(x, ya, z, x, yb2, z)
    if P == "Neoterra":
        d.double_door(mx, 2, z1, "x", "south", "birch")
        for x in range(mx - 2, mx + 4):
            if d.air(x, 5, z1 - 1):
                d.set(x, 5, z1 - 1, slab("smooth_quartz_slab", "top"))
        keep = {(mx, z1 + 1), (mx + 1, z1 + 1)}
    else:
        d.door(mx, 2, z1, "south", wood)
        keep = {(mx, z1 + 1)}
    if title:
        if P == "Neoterra":
            d.sign(mx + 2, 4, z1 - 1, "north", ["", title], "birch", glow=True, color="cyan")
        else:
            d.sign(mx + 1, 4, z1 - 1, "north", ["", title], M["sign"])
    alongz = (z2 - z1) >= sh + 4
    rail = "light_gray_stained_glass_pane" if P == "Neoterra" else M["fence"]
    for k in range(1, storeys):
        if alongz:
            stair_flight(d, [(x1 + k, z) for z in range(z1 + 2, z1 + sh + 1)], "south", f"{M['stairs']}_stairs",
                         y0=2 + sh * (k - 1), fill=M["deck"])
            if k == storeys - 1:
                for z in range(z1 + 3, z1 + sh + 1):
                    d.set(x1 + k + 1, 2 + sh * k, z, rail)
        else:
            stair_flight(d, [(x, z2 - k) for x in range(x1 + 2, x1 + sh + 1)], "east", f"{M['stairs']}_stairs",
                         y0=2 + sh * (k - 1), fill=M["deck"])
            if k == storeys - 1:
                for x in range(x1 + 3, x1 + sh + 1):
                    d.set(x, 2 + sh * k, z2 - k - 1, rail)
    rooms = []
    for k in range(storeys):
        if storeys == 1:
            res = []
        elif alongz and k == 0:
            res = [(x1 + 1, z1 + 1, x1 + 2, z1 + sh + 1)]
        elif alongz:
            res = [(x1 + 1, z1 + 1, x1 + storeys + 1, z1 + sh + 2)]
        elif k == 0:
            res = [(x1 + 1, z2 - 2, x1 + sh + 1, z2 - 1)]
        else:
            res = [(x1 + 1, z2 - storeys - 1, x1 + sh + 2, z2 - 1)]
        rooms.append((x1 + 1, z1 + 1, x2 - 1, z2 - 1, 2 + sh * k, res, keep if k == 0 else set()))
    rooms += [None] * (want - storeys)
    door_path(d, mx, z1)
    return dict(ridge=ridge, top=top, mx=mx, rooms=rooms)


def door_path(d, mx, z1, n=4):
    P = d.pack
    path = {"Hearthwood": "dirt_path", "Cascadia": "spruce_planks", "Neoterra": "polished_andesite"}[P]
    for z in range(max(0, z1 - n), z1):
        for x in ((mx, mx + 1) if P == "Neoterra" else (mx,)):
            if d.air(x, 2, z):
                d.set(x, 1, z, path)


POTS = ["decorated_pot[cracked=false,facing=north,waterlogged=false]", "flower_pot", "potted_fern",
        "candle[candles=3,lit=false,waterlogged=false]"]


def token(d, tok, x, y, z, f, i, base):
    P = d.pack
    wood = WOOD[P]
    shelf = f"{wood}_slab[type=top,waterlogged=false]"
    stock = STOCK[base]
    if tok == "rack":
        d.rack(x, y, z, f)
    elif tok == "rack2":
        d.rack(x, y, z, f)
        d.rack(x, y + 1, z, f)
    elif tok == "keg":
        d.keg(x, y, z, f)
        d.set(x, y + 1, z, stock[i % len(stock)])
    elif tok == "barrel":
        d.set(x, y, z, "barrel[facing=up,open=false]")
        d.set(x, y + 1, z, POTS[0])
    elif tok == "pot":
        d.set(x, y, z, shelf)
        d.set(x, y + 1, z, POTS[i % len(POTS)])
    elif tok == "bench":
        d.set(x, y, z, shelf)
    elif tok == "book":
        d.set(x, y, z, f"chiseled_bookshelf[facing={f},slot_0_occupied=true,slot_1_occupied=true,"
                       "slot_2_occupied=false,slot_3_occupied=true,slot_4_occupied=false,slot_5_occupied=true]")
        d.set(x, y + 1, z, "bookshelf")
    elif tok == "lectern":
        d.set(x, y, z, f"lectern[facing={f},has_book=false,powered=false]")
    elif tok == "carto":
        d.set(x, y, z, "cartography_table")
    elif tok == "plant":
        d.plant(x, y, z, {"Hearthwood": "potted_red_tulip", "Cascadia": "potted_fern",
                          "Neoterra": "potted_bamboo"}[P])
    elif tok == "stock":
        d.set(x, y, z, stock[i % len(stock)])
        d.set(x, y + 1, z, stock[(i + 1) % len(stock)])
    elif tok == "hay":
        d.set(x, y, z, "hay_block[axis=y]")
    elif tok == "trough":
        d.set(x, y, z, "water_cauldron[level=3]")
    elif tok == "sieve":
        sieve(d, x, y, z, wood)
    elif tok == "wool":
        d.set(x, y, z, "white_wool")
        if i % 2:
            d.set(x, y + 1, z, "brown_wool")
    else:
        names = {"anvil": f"anvil[facing={CW[f]}]", "grind": f"grindstone[face=floor,facing={f}]",
                 "smith": "smithing_table", "cutter": f"stonecutter[facing={f}]",
                 "furnace": f"furnace[facing={f},lit=false]", "blast": f"blast_furnace[facing={f},lit=false]",
                 "smoker": f"smoker[facing={f},lit=false]", "craft": "crafting_table", "cauldron": "cauldron",
                 "piston": "piston[extended=false,facing=up]", "observer": f"observer[facing={f},powered=false]",
                 "dispenser": f"dispenser[facing={f},triggered=false]", "chest":
                     f"chest[facing={f},type=single,waterlogged=false]", "loom": f"loom[facing={f}]",
                 "lamp": "redstone_lamp[lit=false]"}
        d.set(x, y, z, names.get(tok, tok))


def fit(d, rm, items, base="blacksmith"):
    """Place a hand-written list of furniture in one room. Coordinates are offsets from the room's walls: x >= 0
    counts from the west wall, x < 0 from the east wall (-1 = against it); z likewise from the street side / back.
    Items: ("rack"/"rack2", x, z, facing), ("keg", x, z, facing, top), ("b", x, z, block, top), ("slab", x, z, top),
    ("chair", x, z, back), ("table", x, z), ("t", x, z, token, facing), ("bs", x, z) two-high bookcase,
    ("lamp", x, z) lantern on a chain, ("hook", x, z, facing), ("rug", x, z, w, h)."""
    if rm is None:
        return
    x1, z1, x2, z2, y, res, keep = rm
    keep = set(keep) | {(x, z + 1) for x, z in keep}
    wood = WOOD[d.pack]

    def X(v):
        return x1 + v if v >= 0 else x2 + 1 + v

    def Z(v):
        return z1 + v if v >= 0 else z2 + 1 + v

    def free(x, z):
        return (x1 <= x <= x2 and z1 <= z <= z2 and (x, z) not in keep
                and not any(a <= x <= b and c <= z <= e for a, c, b, e in res)
                and d.air(x, y, z) and d.air(x, y + 1, z) and not d.air(x, y - 1, z))

    for it in items:
        k, x, z, a = it[0], X(it[1]), Z(it[2]), it[3:]
        if k == "lamp":
            if x1 <= x <= x2 and z1 <= z <= z2 and d.air(x, y + 3, z) and d.air(x, y + 2, z):
                hang(d, x, y + 3, z)
            continue
        if k == "hook":
            if d.air(x, y + 2, z) and not d.air(x, y + 1, z):
                d.set(x, y + 2, z, f"tripwire_hook[attached=false,facing={a[0]},powered=false]")
            continue
        if k == "rug":
            c = RUGS[d.pack]
            for xx in range(x, x + a[0]):
                for zz in range(z, z + a[1]):
                    if free(xx, zz):
                        edge = xx in (x, x + a[0] - 1) or zz in (z, z + a[1] - 1)
                        d.set(xx, y, zz, c[0] if edge else c[1])
            continue
        if not free(x, z):
            continue
        if k == "rack":
            d.rack(x, y, z, a[0])
        elif k == "rack2":
            d.rack(x, y, z, a[0])
            d.rack(x, y + 1, z, a[0])
        elif k == "keg":
            d.keg(x, y, z, a[0])
            if len(a) > 1 and a[1]:
                d.set(x, y + 1, z, a[1])
        elif k == "b":
            d.set(x, y, z, a[0])
            if len(a) > 1 and a[1]:
                d.set(x, y + 1, z, a[1])
        elif k == "slab":
            d.set(x, y, z, f"{wood}_slab[type=top,waterlogged=false]")
            if a and a[0]:
                d.set(x, y + 1, z, a[0])
        elif k == "chair":
            d.chair(x, y, z, a[0], wood, sit=False)
        elif k == "table":
            d.table(x, y, z, wood)
        elif k == "desk":                            # table with its chair on the `back` side
            dx, dz = D4[a[0]]
            d.table(x, y, z, wood)
            if free(x + dx, z + dz):
                d.chair(x + dx, y, z + dz, a[0], wood, sit=False)
        elif k == "bs":
            d.set(x, y, z, "bookshelf")
            d.set(x, y + 1, z, "bookshelf")
        elif k == "t":
            token(d, a[0], x, y, z, a[1] if len(a) > 1 else "north", 0, base)


CANDLE = "candle[candles=3,lit=false,waterlogged=false]"
DPOT = "decorated_pot[cracked=false,facing=north,waterlogged=false]"
CHAIN = "chain[axis=y,waterlogged=false]"


def open_shed(d, x1, z1, x2, z2, h=4, axis="x", back=None, step=4, floor=None, sides=()):
    """Open-sided pole shed (posts, beams, pack roof) - optional closed back/sides. Returns roof top y."""
    P = d.pack
    M = MAT[P]
    if floor:
        d.fill(x1, 1, z1, x2, 1, z2, floor)
    for x, z in perim(x1, z1, x2, z2):
        along = (x - x1) if z in (z1, z2) else (z - z1)
        if (x in (x1, x2) and z in (z1, z2)) or along % step == 0:
            col(d, x, z, 2, h, M["post"])
    for x, z in perim(x1, z1, x2, z2):
        if P == "Neoterra":
            d.set(x, h + 1, z, M["beam"])
        else:
            d.set(x, h + 1, z, f"{M['beam']}[axis={'x' if z in (z1, z2) else 'z'}]")
    for side in ([back] if back else []) + list(sides):
        for x, z in perim(x1, z1, x2, z2):
            if {"north": z == z1, "south": z == z2, "west": x == x1, "east": x == x2}[side]:
                for y in range(2, h + 1):
                    if d.air(x, y, z):
                        d.set(x, y, z, M["board"] if y > 2 else M["stone"])
    if P == "Neoterra":
        d.fill(x1 - 1, h + 2, z1 - 1, x2 + 1, h + 2, z2 + 1, "smooth_quartz")
        for x, z in perim(x1 - 1, z1 - 1, x2 + 1, z2 + 1):
            d.set(x, h + 2, z, "cyan_terracotta" if z == z1 - 1 else "smooth_quartz")
        return h + 2
    s_, sl = roofset(d)
    return d.gable(x1, z1, x2, z2, h + 2, axis, s_, sl, M["board"])


def heap(d, cx, cz, r, blocks, y0=2):
    y = y0
    rr = r
    while rr >= 0.5:
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            for z in range(int(cz - r) - 1, int(cz + r) + 2):
                if math.hypot(x - cx, z - cz) <= rr and d.bp.inside(x, y, z) and d.air(x, y, z):
                    d.set(x, y, z, blocks[(x * 3 + z + y) % len(blocks)])
        rr -= 0.9
        y += 1


def pond(d, x1, z1, x2, z2, rim):
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            edge = x in (x1, x2) or z in (z1, z2)
            d.set(x, 1, z, rim if edge else "water")
            if not edge:
                d.set(x, 0, z, "clay")


def low_fence(d, x1, z1, x2, z2, gates=(), block=None):
    b = block or MAT[d.pack]["fence"]
    for x, z in perim(x1, z1, x2, z2):
        if (x, z) in gates:
            continue
        if d.air(x, 2, z):
            d.set(x, 2, z, WALLST(b) if b.endswith("_wall") else b)


def rails(d, cells, shape):
    for x, z in cells:
        if d.air(x, 2, z):
            d.set(x, 2, z, f"rail[shape={shape},waterlogged=false]")
            d.set(x, 1, z, "gravel")


def round_kiln(d, cx, cz, r, h, block, band=None, door=None):
    """Round kiln / silo shell of radius r and height h (from y2), hollow, optional door side."""
    for y in range(2, 2 + h):
        rr = r if y < 2 + h - 3 else max(1.2, r - (y - (2 + h - 3)) * 0.7)
        for x in range(cx - int(r) - 1, cx + int(r) + 2):
            for z in range(cz - int(r) - 1, cz + int(r) + 2):
                dd = math.hypot(x - cx, z - cz)
                if rr - 1.05 < dd <= rr:
                    d.set(x, y, z, band if band and y % 4 == 0 else block)
    if door:
        dx, dz = D4[door]
        rx, rz = cx + dx * int(r), cz + dz * int(r)
        d.set(rx, 2, rz, AIR)
        d.set(rx, 3, rz, AIR)


def post_sign(d, x, z, lines):
    if not all(d.air(x, y, z) for y in (2, 3)) or not d.air(x, 3, z - 1):
        return
    col(d, x, z, 2, 3, MAT[d.pack]["post"])
    if d.pack == "Neoterra":
        d.sign(x, 3, z - 1, "north", lines, "birch", glow=True, color="cyan")
    else:
        d.sign(x, 3, z - 1, "north", lines, MAT[d.pack]["sign"])


def stack_logs(d, x1, z1, x2, z2, h, axis="x", log="spruce_log"):
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            for y in range(2, 2 + h):
                d.set(x, y, z, f"{log}[axis={axis}]")


# ------------------------------------------------------------------------------------------------ blacksmith
def bs_coalshed(d, sl):
    """Coal & charcoal shed: open pole shed, walled bunkers of coal along the back, firewood and charcoal sacks."""
    x1, z1, x2, z2, s, ax = sl
    M = MAT[d.pack]
    open_shed(d, x1, z1, x2, z2, 4, "x", back="south", floor=M["yard"], sides=("east",))
    for x in range(x1 + 1, x2):                      # bunkers: a low wall every third cell along the back
        for z in (z2 - 1, z2 - 2):
            if (x - x1) % 3 == 0:
                d.set(x, 2, z, WALLST(M["lowwall"]))
                d.set(x, 3, z, WALLST(M["lowwall"]))
            else:
                d.set(x, 2, z, "coal_block")
                if z == z2 - 1:
                    d.set(x, 3, z, "coal_block")
    stack_logs(d, x1 + 1, z1 + 2, x1 + 1, z2 - 3, 3, "x", "oak_log")
    for x, b in ((x1 + 3, "black_wool"), (x1 + 4, "gray_wool"), (x1 + 5, "black_wool")):
        d.set(x, 2, z1 + 2, b)
    d.set(x1 + 4, 3, z1 + 2, "black_wool")
    d.rack(x2 - 1, 2, z1 + 1, "west")
    d.rack(x2 - 1, 2, z1 + 2, "west")
    d.set(x2 - 1, 2, z1 + 3, "cauldron")
    d.set(x2 - 2, 2, z1 + 1, "spruce_slab[type=top,waterlogged=false]")
    d.set(x2 - 2, 3, z1 + 1, "lantern[hanging=false,waterlogged=false]")
    hang(d, x1 + 3, 4, (z1 + z2) // 2)
    hang(d, x2 - 3, 4, (z1 + z2) // 2)
    post_sign(d, x1 + 2, z1 - 1, ["COAL", "& CHARCOAL"])
    rails(d, [(x, z1 - 2) for x in range(x1, x2 + 1)], "east_west")
    lamp_post(d, x2 + 1, z1 - 1)


def bs_stable(d, sl):
    """Farrier's stable: stalls (gates, hay racks, water troughs), a shoeing bay with anvil and tack wall, a hay
    loft door and a paddock."""
    x1, z1, x2, z2, s, ax = sl
    deep = (z2 - z1) >= 11
    hz2 = z2 - 5 if deep else z2
    info = hall(d, x1, z1, x2, hz2, 1, None, "FARRIER", sh=6)
    rm = info["rooms"][0]
    fx1, fz1, fx2, fz2, y = rm[:5]
    w = WOOD[d.pack]
    for x in range(info["mx"] + 2, fx2 + 1):        # stalls from the door eastwards, 2 wide with a fence between
        stall = (x - fx1) % 3
        if stall == 0:
            for z in range(fz2 - 2, fz2 + 1):
                d.set(x, y, z, f"{w}_fence")
        else:
            d.set(x, y, fz2, "hay_block[axis=y]" if stall == 1 else "water_cauldron[level=3]")
            d.set(x, y, fz2 - 2, f"{w}_fence_gate[facing=north,in_wall=false,open=false,powered=false]")
    fit(d, rm, [("t", 1, -2, "anvil", "north"), ("b", 0, -1, "water_cauldron[level=3]"),
                ("b", 2, -1, "hay_block[axis=x]"), ("rack", 0, 2, "east"), ("keg", 0, 3, "east"),
                ("hook", 0, 3, "east"), ("hook", 0, 4, "east"), ("b", 1, 0, "barrel[facing=up,open=false]", "lantern[hanging=false,waterlogged=false]"),
                ("lamp", 2, 2), ("lamp", -3, 1), ("lamp", -6, 1)], "blacksmith")
    lx = info["mx"] + 3
    d.set(lx, y + 4, z1, f"{w}_trapdoor[facing=north,half=bottom,open=true,powered=false,waterlogged=false]")
    pz1, pz2 = (z2 - 3, z2) if deep else (z2 + 2, z2 + 7)
    low_fence(d, x1, pz1, x2, pz2, gates={(x1, pz1 + 1), (x2, pz1 + 1)})
    d.set(x1 + 2, 2, pz2 - 1, "hay_block[axis=y]")
    trough(d, [(x2 - 2, 2, pz2 - 1), (x2 - 3, 2, pz2 - 1)])
    lamp_post(d, info["mx"] - 2, z1 - 2)


def awning(d, x1, x2, z1, y):
    """Striped awning over the street front (wool in the pack accent colours)."""
    cols = {"Hearthwood": ("red_wool", "white_wool"), "Cascadia": ("green_wool", "white_wool"),
            "Neoterra": ("cyan_wool", "white_wool")}[d.pack]
    for x in range(x1, x2 + 1):
        if d.air(x, y, z1 - 1):
            d.set(x, y, z1 - 1, cols[x % 2])


def bs_armourer(d, sl):
    """Armourer's shop: sales room with counter, armour on display and a customers' bench under the awning;
    plate-working shop upstairs with anvil, grindstone, smithing table and quench tub."""
    x1, z1, x2, z2, s, ax = sl
    info = hall(d, x1, z1, x2, z2, 2, ax, "ARMOURER")
    g, u = info["rooms"]
    fit(d, g, [("slab", -2, 3, CANDLE), ("slab", -3, 3), ("slab", -4, 3, DPOT), ("slab", -5, 3), ("slab", -6, 3, "flower_pot"),
               ("rack", -1, -1, "north"), ("b", -2, -1, "smooth_stone", "iron_block"), ("rack", -3, -1, "north"),
               ("b", -4, -1, "smooth_stone", CHAIN), ("t", -5, -1, "barrel"), ("rack", -6, -1, "north"),
               ("b", -4, -3, "smooth_stone", "iron_block"), ("keg", -1, 4, "west", "iron_block"),
               ("chair", -2, 0, "north"), ("chair", -3, 0, "north"), ("t", -1, 0, "plant"),
               ("rug", -7, 1, 6, 2), ("lamp", -3, 1), ("lamp", -4, -2)], "blacksmith")
    fit(d, u, [("t", -1, -1, "anvil", "north"), ("slab", -2, -1, CANDLE), ("t", -3, -1, "grind", "north"),
               ("t", -4, -1, "smith"), ("slab", -5, -1, "flower_pot"), ("b", -6, -1, "water_cauldron[level=3]"),
               ("rack2", -1, -3, "west"), ("keg", -1, -4, "west", CHAIN), ("t", -1, -5, "barrel"),
               ("hook", -1, -3, "west"), ("t", -4, 3, "anvil", "north"), ("chair", -5, 3, "east"),
               ("lamp", -3, 2), ("lamp", -3, -3)], "blacksmith")
    awning(d, x1, x2, z1, 5)
    lamp_post(d, x1, z1 - 2)


def bs_ironworks(d, sl):
    """Ironworks: four storeys - forge floor (a row of forges with their own chimneys, drop hammers, quench tanks),
    drawing office, bar store, pattern library."""
    x1, z1, x2, z2, s, ax = sl
    info = hall(d, x1, z1, x2, z2, 4, ax, "IRONWORKS")
    g, m, u, t = info["rooms"]
    fx1, fz1, fx2, fz2, y = g[:5]
    frame = {"Hearthwood": "bricks", "Cascadia": "cobblestone", "Neoterra": "polished_blackstone_bricks"}[d.pack]
    for fx in range(fx1 + 4, fx2 - 1, 5):           # forges every 5 cells along the back wall
        forge(d, fx, fz2, "north", info["ridge"] + 2, frame)
        d.set(fx, y, fz2 - 2, "anvil[facing=east]")
        d.set(fx, y + 3, fz2 - 2, "piston[extended=false,facing=down]")
        d.set(fx + 2, y, fz2 - 1, "water_cauldron[level=3]")
    fit(d, g, [("rack", -1, 1, "west"), ("rack", -1, 2, "west"), ("b", -1, 3, "coal_block", "coal_block"),
               ("t", -1, 4, "barrel"), ("slab", -3, 0, CANDLE), ("t", -4, 0, "grind", "south"), ("slab", -5, 0),
               ("t", -6, 0, "barrel"), ("rack", -7, 0, "south"), ("rack", -8, 0, "south"),
               ("rack", 2, 0, "south"), ("rack", 3, 0, "south"), ("slab", 4, 0, CANDLE), ("t", 5, 0, "smith"),
               ("slab", 6, 0, "flower_pot"), ("hook", 2, 0, "south"), ("hook", 3, 0, "south"),
               # finishing bench down the middle, a second anvil stand in deep halls
               ("t", -4, 3, "smith"), ("slab", -5, 3, CHAIN), ("slab", -6, 3), ("t", -7, 3, "grind", "south"),
               ("slab", -8, 3, DPOT), ("b", -11, -5, "iron_block"), ("b", -12, -5, "iron_block", "iron_block"),
               ("t", -13, -5, "anvil", "north"), ("hook", -1, 1, "west"), ("hook", -1, 2, "west"),
               ("lamp", -3, 3), ("lamp", -8, 3), ("lamp", -13, 3), ("lamp", 4, 3), ("lamp", -18, 3)], "blacksmith")
    # drawing office: drafting desks in two rows, plan chests under the street windows, bookcases at the back
    fit(d, m, [("slab", -3, 3, CANDLE), ("slab", -4, 3, "flower_pot"), ("chair", -3, 4, "south"), ("chair", -4, 2, "north"),
               ("slab", -8, 3, CANDLE), ("slab", -9, 3), ("chair", -8, 4, "south"), ("desk", -13, 3, "south"),
               ("bs", -1, -1), ("t", -2, -1, "book"), ("t", -3, -1, "lectern", "north"), ("bs", -4, -1),
               ("t", -5, -1, "carto"), ("bs", -6, -1), ("bs", -7, -1), ("t", -8, -1, "book"), ("bs", -9, -1),
               ("t", -2, 0, "chest", "south"), ("slab", -3, 0, "flower_pot"), ("t", -4, 0, "chest", "south"),
               ("slab", -5, 0, CANDLE), ("t", -6, 0, "chest", "south"), ("t", -1, 2, "lectern", "west"),
               ("t", -1, 0, "plant"), ("t", 6, -1, "plant"), ("desk", -5, -4, "north"), ("desk", -9, -4, "north"),
               ("rug", -5, 2, 3, 3), ("rug", -10, 2, 3, 3), ("lamp", -4, 2), ("lamp", -9, 2), ("lamp", -13, 2), ("lamp", -7, -4)], "blacksmith")
    # bar store: aisles of double-height racks with walkways, stock barrels at the west end
    fit(d, u, [("rack2", x, -1, "north") for x in range(-1, -10, -1)] +
        [("rack2", x, 3, "north") for x in range(-3, -10, -1)] + [("rack2", x, 4, "south") for x in range(-3, -10, -1)] +
        [("rack2", x, 7, "north") for x in range(-3, -10, -1)] + [("rack2", x, 8, "south") for x in range(-3, -10, -1)] +
        [("keg", -1, 1, "west", "iron_block"), ("keg", -1, 2, "west", CHAIN), ("t", -1, 0, "chest", "west"),
         ("keg", 6, -1, "north", "coal_block"), ("t", 7, -1, "barrel"), ("keg", 8, -1, "north", "raw_iron_block"),
         ("b", 6, 3, "iron_block", "iron_block"), ("b", 7, 3, "iron_block"), ("t", 8, 3, "chest", "east"),
         ("lamp", -6, 1), ("lamp", -6, -2), ("lamp", -6, 6), ("lamp", 7, 1)], "blacksmith")
    # pattern library: shelves along the back, reading tables, a reading nook in deep halls
    fit(d, t, [("bs", -1, -1), ("t", -2, -1, "book"), ("bs", -3, -1), ("t", -4, -1, "book"), ("bs", -5, -1),
               ("t", -6, -1, "book"), ("bs", -7, -1), ("bs", -8, -1), ("t", -9, -1, "book"), ("bs", -10, -1),
               ("table", -4, 3), ("table", -5, 3), ("table", -6, 3),
               ("chair", -4, 2, "north"), ("chair", -6, 4, "south"), ("chair", -5, 4, "south"), ("t", -1, 3, "lectern", "west"),
               ("desk", -10, 3, "south"), ("desk", -12, 3, "south"), ("t", -8, 0, "lectern", "south"),
               ("t", -2, 0, "plant"), ("slab", -3, 0, CANDLE), ("slab", -4, 0, "flower_pot"),
               ("table", -3, -4), ("chair", -3, -5, "north"), ("chair", -4, -4, "west"), ("t", 6, -1, "plant"),
               ("rug", -8, 2, 5, 3), ("t", -1, 0, "plant"), ("lamp", -5, 3), ("lamp", -11, 2), ("lamp", -3, -3)],
        "blacksmith")
    lamp_post(d, info["mx"] - 2, z1 - 2)
    lamp_post(d, info["mx"] + 2, z1 - 2)


# ------------------------------------------------------------------------------------------------ smeltery
def sm_oreyard(d, sl):
    """Ore yard: walled yard with ore heaps of raw iron / copper / gold under a bunker shed, a tram line and a
    weigh house with its scale book."""
    x1, z1, x2, z2, s, ax = sl
    M = MAT[d.pack]
    d.fill(x1, 1, z1, x2, 1, z2, M["yard"])
    low_fence(d, x1, z1, x2, z2, gates={(x1 + 2, z1), (x1 + 3, z1)}, block=M["lowwall"])
    ores = ["raw_iron_block", "raw_copper_block", "raw_gold_block"]
    for i, bx in enumerate((x1 + 1, x1 + 5)):
        heap(d, bx + 1.5, z2 - 2, 1.8, [ores[i], ores[i], "gravel"])
    rails(d, [(x1 + 2, z) for z in range(z1 - 3, z2 - 3)], "north_south")
    narrow = (x2 - x1) < 10
    wh = hall(d, x2 - (4 if narrow else 5), z1 + 2, x2, z1 + 7, 1, "x", "WEIGH HOUSE")
    fit(d, wh["rooms"][0], [("t", -1, -1, "lectern", "north"), ("b", 0, -1, "cauldron"), ("t", -1, 0, "barrel"),
                            ("slab", -2, -1, CANDLE), ("lamp", 1, 1)], "smeltery")
    open_shed(d, x1, z2 - 4, x2 - 7, z2, 4, "x", back="south")
    post_sign(d, x1 + 5, z1 - 1, ["ORE YARD"])
    bx = x1 if narrow else x1 + 1                    # tipping bin straddling the rails
    for x, z in ((bx, z1 + 1), (bx + 2, z1 + 1), (bx, z1 + 3), (bx + 2, z1 + 3)):
        col(d, x, z, 2, 4, M["post"])
    d.fill(bx, 5, z1 + 1, bx + 2, 5, z1 + 3, M["deck"])
    for x, z in perim(bx, z1 + 1, bx + 2, z1 + 3):
        d.set(x, 6, z, M["board"])
        d.set(x, 7, z, M["board"])
    d.set(bx + 1, 6, z1 + 2, "raw_iron_block")
    d.set(x1 + 2, 4, z1 + 2, "hopper[enabled=true,facing=down]")


def sm_casting(d, sl):
    """Casting hall: tall hall with a glazed roof monitor, furnaces along the back, a sand casting floor with
    ladles on chain hoists, moulding bench and racks of moulds."""
    x1, z1, x2, z2, s, ax = sl
    info = hall(d, x1, z1, x2, z2, 1, ax, "CASTING HALL", sh=8, clerestory=True)
    g = info["rooms"][0]
    fx1, fz1, fx2, fz2, y = g[:5]
    zc = (fz1 + fz2) // 2
    for x in range(fx1 + 2, fx2 - 1):               # sand bed down the middle, ladles every third cell
        d.set(x, 1, zc, "sand")
        d.set(x, 1, zc + 1, "sand")
    for x in range(fx1 + 2, fx2 - 1, 3):
        d.set(x, y, zc, "cauldron")
        for yy in range(y + 3, info["top"] + 1):
            if d.air(x, yy, zc):
                d.set(x, yy, zc, CHAIN)
    fit(d, g, [("t", -1, -1, "furnace", "north"), ("t", -2, -1, "furnace", "north"), ("slab", -3, -1, "flower_pot"),
               ("t", -4, -1, "furnace", "north"), ("t", -5, -1, "furnace", "north"), ("b", -6, -1, "coal_block"),
               ("rack", -1, 1, "west"), ("rack", -1, 2, "west"), ("slab", 1, -1, CANDLE), ("t", 2, -1, "craft"),
               ("b", 0, -2, "sand", "sand"), ("lamp", -3, 1), ("lamp", 3, 1)], "smeltery")
    if d.pack != "Neoterra":
        mz = (z1 + z2) // 2
        for x in range(x1 + 2, x2 - 1):
            d.set(x, info["ridge"] + 1, mz, "glass")
            d.set(x, info["ridge"] + 2, mz, slab(roofset(d)[1]))
    lamp_post(d, info["mx"] + 2, z1 - 2)


def sm_blast(d, sl):
    """Blast furnace: a tall tapering furnace tower with a charging trestle, a two-storey cast house at its foot
    (tapping floor with blast furnaces below, assay office above) and a slag heap."""
    x1, z1, x2, z2, s, ax = sl
    M = MAT[d.pack]
    tb = {"Hearthwood": "bricks", "Cascadia": "cobblestone", "Neoterra": "polished_blackstone_bricks"}[d.pack]
    wide = (x2 - x1) >= 15
    tx, tz = (x1 + 3, z2 - 3) if wide else (x2 - 3, z2 - 3)
    for y in range(2, 20):
        r = 3 if y < 10 else 2 if y < 16 else 1
        for x in range(tx - r, tx + r + 1):
            for z in range(tz - r, tz + r + 1):
                if max(abs(x - tx), abs(z - tz)) == r:
                    d.set(x, y, z, "stone_bricks" if y in (9, 15) else tb)
                elif y > 2:
                    d.set(x, y, z, AIR)
    d.set(tx, 2, tz, "magma_block")
    for y in (2, 3):
        d.set(tx, y, tz - 3, AIR)
    d.set(tx, 4, tz - 3, st("stone_brick_stairs", "south", "top"))
    ch = hall(d, x1 + 7, z1, x2, z2, 2, "z", "CAST HOUSE") if wide else \
        hall(d, x1, z1, x2, z2 - 7, 2, "x", "CAST HOUSE")
    fit(d, ch["rooms"][0], [("t", -1, -1, "blast", "west"), ("t", -1, -2, "blast", "west"), ("b", -2, -1, "cauldron"),
                            ("rack", -1, 0, "west"), ("slab", -3, -1, CANDLE), ("b", -4, -1, "sand"),
                            ("lamp", -2, 1)], "smeltery")
    fit(d, ch["rooms"][1], [("t", -1, -1, "lectern", "north"), ("slab", -2, -1, "brewing_stand[has_bottle_0=true,"
                            "has_bottle_1=false,has_bottle_2=false]"), ("slab", -3, -1, CANDLE), ("bs", -1, 1),
                            ("chair", -3, 0, "south"), ("t", -4, -1, "carto"), ("rug", -4, 0, 3, 1), ("lamp", -2, 0)],
        "smeltery")
    if wide:
        for z in range(z1, tz - 3):
            col(d, x1 + 3, z, 2, 9, M["post"]) if (z - z1) % 3 == 0 else None
            d.set(x1 + 3, 10, z, M["deck"])
            d.set(x1 + 2, 11, z, M["fence"])
            d.set(x1 + 4, 11, z, M["fence"])
        heap(d, x1 + 1.5, z1 + 2, 2.2, ["blackstone", "basalt[axis=y]", "gravel", "magma_block"])
    else:
        heap(d, x1 + 2, z2 - 2, 2.2, ["blackstone", "basalt[axis=y]", "gravel", "magma_block"])


def sm_foundry(d, sl):
    """Foundry: four storeys - moulding floor (furnaces, sand boxes, ladle), pattern shop, ingot store and the
    founder's office - with a tall stack at the corner."""
    x1, z1, x2, z2, s, ax = sl
    info = hall(d, x1, z1, x2, z2, 4, ax, "FOUNDRY")
    g, m, u, t = info["rooms"]
    # moulding floor: furnace bank on the back wall, sand moulding boxes in two rows, ladle cauldrons, coke store
    fit(d, g, [("t", -1, -1, "furnace", "north"), ("t", -2, -1, "furnace", "north"), ("t", -3, -1, "furnace", "north"),
               ("b", -4, -1, "coal_block", "coal_block"), ("t", -5, -1, "furnace", "north"), ("t", -6, -1, "furnace", "north"),
               ("b", -7, -1, "coal_block"), ("t", -8, -1, "blast", "north"), ("t", -9, -1, "blast", "north"),
               ("b", -4, 3, "sand"), ("b", -5, 3, "sand"), ("b", -6, 3, "cauldron"), ("b", -9, 3, "sand"),
               ("b", -10, 3, "sand"), ("b", -11, 3, "cauldron"), ("b", -4, -5, "sand"), ("b", -5, -5, "sand"),
               ("b", -6, -5, "cauldron"), ("b", -9, -5, "sand"), ("b", -10, -5, "sand"),
               ("rack", -1, 1, "west"), ("rack", -1, 2, "west"), ("t", -1, 3, "barrel"),
               ("t", 2, 0, "barrel"), ("t", 3, 0, "barrel"), ("keg", 4, 0, "south", "coal_block"), ("rack", 5, 0, "south"),
               ("slab", -3, 0, CANDLE), ("t", -4, 0, "craft"), ("slab", -5, 0, "flower_pot"), ("rack", -6, 0, "south"),
               ("rack", 6, 0, "south"), ("hook", 5, 0, "south"), ("hook", 6, 0, "south"),
               ("t", -1, -3, "barrel"), ("lamp", -5, 2), ("lamp", -10, 2), ("lamp", 4, 2), ("lamp", -8, -4), ("lamp", -3, -4)], "smeltery")
    # pattern shop: joiners' benches for wooden patterns, a pattern rack wall and the foreman's desk
    fit(d, m, [("t", -1, -1, "craft"), ("slab", -2, -1, CANDLE), ("slab", -3, -1, "flower_pot"), ("t", -4, -1, "craft"),
               ("slab", -5, -1), ("slab", -6, -1, DPOT), ("t", -7, -1, "loom", "north"), ("slab", -8, -1),
               ("slab", -4, 3), ("slab", -5, 3, CANDLE), ("chair", -4, 4, "south"), ("chair", -5, 2, "north"),
               ("slab", -9, 3), ("slab", -10, 3, "flower_pot"), ("chair", -9, 4, "south"), ("chair", -10, 2, "north"),
               ("rack", -1, 1, "west"), ("rack", -1, 2, "west"), ("rack", -1, 3, "west"),
               ("rack2", -3, 0, "south"), ("rack2", -4, 0, "south"), ("rack2", -5, 0, "south"), ("t", -6, 0, "chest", "south"),
               ("desk", -12, -4, "north"), ("t", 6, -1, "plant"), ("b", 7, -1, "oak_log[axis=x]"), ("b", 8, -1, "oak_log[axis=x]"),
               ("lamp", -4, 2), ("lamp", -9, 2), ("lamp", -12, -3)], "smeltery")
    # ingot store: shelving aisles of ingots, ore kegs and stacks of metal blocks
    fit(d, u, [("rack2", x, -1, "north") for x in range(-1, -10, -1)] +
        [("rack2", x, 3, "north") for x in range(-4, -10, -1)] + [("rack2", x, 4, "south") for x in range(-4, -10, -1)] +
        [("rack2", x, 7, "north") for x in range(-4, -10, -1)] +
        [("keg", -1, 1, "west", "raw_iron_block"), ("keg", -1, 2, "west", "raw_copper_block"),
         ("keg", -1, 3, "west", "raw_gold_block"), ("b", 6, -1, "iron_block"), ("b", 7, -1, "iron_block", "iron_block"),
         ("b", 8, -1, "gold_block"), ("t", 9, -1, "barrel"), ("t", 6, 3, "chest", "east"), ("t", 6, 4, "chest", "east"),
         ("lamp", -6, 1), ("lamp", -6, 6), ("lamp", 8, 2)], "smeltery")
    # founder's office: desk & visitors' chairs, an assay corner with a brewing stand, books and a map table
    fit(d, t, [("bs", -1, -1), ("t", -2, -1, "lectern", "north"), ("bs", -3, -1), ("t", -4, -1, "book"), ("bs", -5, -1),
               ("slab", -4, 3, CANDLE), ("slab", -5, 3, "flower_pot"), ("chair", -4, 4, "south"), ("chair", -5, 2, "north"),
               ("chair", -4, 2, "north"), ("t", -1, 3, "carto"), ("t", -1, 0, "plant"), ("rug", -7, 2, 5, 3),
               ("slab", -9, -1, "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]"),
               ("b", -10, -1, "cauldron"), ("slab", -11, -1, CANDLE), ("chair", -10, -2, "south"),
               ("t", -2, 0, "chest", "south"), ("t", -3, 0, "chest", "south"), ("t", -10, 0, "plant"),
               ("table", -10, 4), ("table", -11, 4), ("chair", -10, 3, "north"), ("chair", -11, 5, "south"),
               ("chair", -12, 4, "west"), ("t", 6, -1, "plant"),
               ("lamp", -4, 3), ("lamp", -10, -3), ("lamp", -11, 3)], "smeltery")
    tb = {"Hearthwood": "bricks", "Cascadia": "cobblestone", "Neoterra": "white_concrete"}[d.pack]
    for y in range(2, info["ridge"] + 8):
        for x in (x2 + 1, x2 + 2):
            for z in (z2 - 2, z2 - 1):
                if d.bp.inside(x, y, z):
                    d.set(x, y, z, "stone_bricks" if y % 6 == 0 else tb)
    lamp_post(d, info["mx"] - 2, z1 - 2)


# ------------------------------------------------------------------------------------------------ stonesmeltery
def ss_drying(d, sl):
    """Drying shed: open slatted shed with two-tier shelves of greenware (pots and bricks drying)."""
    x1, z1, x2, z2, s, ax = sl
    open_shed(d, x1, z1, x2, z2, 5, "x", floor=MAT[d.pack]["yard"], back="south")
    w = WOOD[d.pack]
    ware = ["flower_pot", "terracotta", DPOT, "bricks"]
    for z in range(z1 + 2, z2 - 1, 3):               # shelf rows every third row, two tiers
        for x in range(x1 + 2, x2 - 1):
            d.set(x, 2, z, f"{w}_slab[type=top,waterlogged=false]")
            d.set(x, 3, z, ware[(x + z) % 4])
            d.set(x, 4, z, f"{w}_slab[type=top,waterlogged=false]")
            d.set(x, 5, z, ware[(x + z + 1) % 4])
    for x in range(x1, x2 + 1):                      # slatted sides
        for z in (z2,):
            if d.air(x, 3, z):
                d.set(x, 3, z, f"{w}_fence")
    for z in range(z1 + 1, z2):
        for x in (x1, x2):
            if d.air(x, 3, z):
                d.set(x, 3, z, f"{w}_fence")
    d.rack(x1 + 1, 2, z1 + 1, "east")
    d.item(x2 - 1, 2, z1 + 1, "crafting_table")
    post_sign(d, x1 + 2, z1 - 1, ["DRYING", "SHED"])


def ss_kilnyard(d, sl):
    """Kiln yard: two more kilns with fire-mouths, a clay pit and pallets of clay and fired bricks."""
    x1, z1, x2, z2, s, ax = sl
    M = MAT[d.pack]
    d.fill(x1, 1, z1, x2, 1, z2, M["yard"])
    kb = {"Hearthwood": "bricks", "Cascadia": "cobblestone", "Neoterra": "white_concrete"}[d.pack]
    band = {"Hearthwood": "stone_bricks", "Cascadia": "mossy_cobblestone", "Neoterra": "orange_terracotta"}[d.pack]
    if x2 - x1 >= 13:
        ks = [(x1 + 3, (z1 + z2) // 2 + 1), (x2 - 3, (z1 + z2) // 2 + 1)]
    else:
        ks = [((x1 + x2) // 2, z1 + 6), ((x1 + x2) // 2, z2 - 3)]
    for cx, cz in ks:
        round_kiln(d, cx, cz, 3.2, 11, kb, band, door="north" if cz == ks[0][1] else "east")
        d.item(cx, 2, cz, "furnace", "north")
    if x2 - x1 >= 13:
        pond(d, (x1 + x2) // 2 - 1, z1, (x1 + x2) // 2 + 1, z1 + 2, M["stone"])
    else:
        pond(d, x1, z1, x1 + 2, z1 + 2, M["stone"])
    for x in ((x1 + x2) // 2 - 1, (x1 + x2) // 2 + 1):
        d.set(x, 2, z2, "clay")
        d.set(x, 2, z2 - 1, "bricks")


def ss_pughouse(d, sl):
    """Clay pug mill: three storeys (blunging tubs and clay bins, throwing wheels, ware store) with a horse-gin
    pug mill outside."""
    x1, z1, x2, z2, s, ax = sl
    wide = (x2 - x1) > (z2 - z1)
    info = hall(d, x1, z1, x2 - 7 if wide else x2, z2 if wide else z2 - 6, 3, ax, "PUG MILL")
    g, u, u2 = info["rooms"]
    fit(d, g, [("b", -1, -1, "water_cauldron[level=3]"), ("b", -2, -1, "water_cauldron[level=3]"),
               ("b", -3, -1, "clay", "clay"), ("b", -4, -1, "clay"), ("t", -1, 0, "craft"), ("rack", -1, 1, "west"),
               ("slab", -5, -1, "flower_pot"), ("lamp", -3, 1)], "stonesmeltery")
    fit(d, u, [("b", -2, 1, MAT[d.pack]["fence"], "smooth_stone_slab[type=bottom,waterlogged=false]"),
               ("chair", -2, 2, "south"), ("b", -5, 1, MAT[d.pack]["fence"], "smooth_stone_slab[type=bottom,waterlogged=false]"),
               ("chair", -5, 2, "south"), ("slab", -1, -1, DPOT), ("slab", -2, -1, "flower_pot"), ("rack", -3, -1, "north"),
               ("t", -1, 0, "plant"), ("lamp", -3, 1)], "stonesmeltery")
    fit(d, u2, [("rack2", -1, -1, "north"), ("rack2", -2, -1, "north"), ("keg", -3, -1, "north", "terracotta"),
                ("rack2", -4, -1, "north"), ("keg", -1, 1, "west", "bricks"), ("slab", -1, 0, DPOT), ("lamp", -3, 1)],
        "stonesmeltery")
    cx, cz = (x2 - 3, (z1 + z2) // 2) if wide else ((x1 + x2) // 2, z2 - 2)
    for x in range(cx - 3, cx + 4):                  # round track of the horse gin
        for z in range(cz - 2, cz + 3):
            if 1.5 < math.hypot(x - cx, (z - cz) * 1.4) <= 3.2 and d.bp.inside(x, 1, z):
                d.set(x, 1, z, "coarse_dirt")
    col(d, cx, cz, 2, 4, MAT[d.pack]["post"])
    for x in range(cx - 3, cx + 4):
        if x != cx:
            d.set(x, 4, cz, f"{MAT[d.pack]['beam']}[axis=x]" if d.pack != "Neoterra" else "iron_bars")


def ss_works(d, sl):
    """Pottery works: four storeys - throwing room, glaze room, ware store, manager's office - with a kiln chimney."""
    x1, z1, x2, z2, s, ax = sl
    info = hall(d, x1, z1, x2, z2, 4, ax, "POTTERY WORKS")
    g, m, u, t = info["rooms"]
    fen = MAT[d.pack]["fence"]
    wheel = "smooth_stone_slab[type=bottom,waterlogged=false]"
    # throwing room: a row of wheels with stools, clay bins and the pug bench on the back wall, ware boards
    fit(d, g, [("b", -3, 3, fen, wheel), ("chair", -3, 4, "south"), ("b", -6, 3, fen, wheel), ("chair", -6, 4, "south"),
               ("b", -9, 3, fen, wheel), ("chair", -9, 4, "south"), ("b", -12, 3, fen, wheel), ("chair", -12, 4, "south"),
               ("b", -1, -1, "clay", "clay"), ("b", -2, -1, "clay"),
               ("b", -3, -1, "water_cauldron[level=3]"), ("t", -4, -1, "furnace", "north"), ("t", -5, -1, "craft"),
               ("slab", -6, -1, "flower_pot"), ("slab", -7, -1, DPOT), ("slab", -8, -1, "flower_pot"), ("rack", -9, -1, "north"),
               ("rack", -1, 1, "west"), ("slab", -1, 2, "flower_pot"), ("slab", -1, 3, DPOT),
               ("slab", 2, 0, DPOT), ("slab", 3, 0, "flower_pot"), ("slab", 4, 0, DPOT), ("rack", 5, 0, "south"),
               ("slab", -3, 0, "flower_pot"), ("slab", -4, 0, DPOT), ("t", -5, 0, "barrel"),
               ("b", -5, -5, "clay"), ("b", -6, -5, "water_cauldron[level=3]"), ("b", -9, -5, fen, wheel),
               ("chair", -9, -4, "south"),
               ("lamp", -3, 2), ("lamp", -8, 2), ("lamp", -12, 2), ("lamp", 4, 2), ("lamp", -6, -4)], "stonesmeltery")
    # glaze room: glaze tubs, a dipping bench in the middle, glazed ware drying on boards
    fit(d, m, [("b", -1, -1, "water_cauldron[level=3]"), ("b", -2, -1, "water_cauldron[level=2]"),
               ("b", -3, -1, "cauldron"), ("slab", -4, -1, DPOT), ("slab", -5, -1, "flower_pot"),
               ("b", -6, -1, "white_glazed_terracotta"), ("b", -7, -1, "cyan_glazed_terracotta"), ("slab", -8, -1, DPOT),
               ("slab", -4, 3, DPOT), ("slab", -5, 3, "flower_pot"), ("slab", -6, 3, DPOT), ("chair", -5, 4, "south"),
               ("chair", -4, 4, "south"), ("slab", -9, 3, "flower_pot"), ("slab", -10, 3, DPOT), ("chair", -9, 4, "south"),
               ("rack", -1, 1, "west"), ("rack", -1, 2, "west"), ("t", -1, 3, "barrel"),
               ("slab", -3, 0, DPOT), ("slab", -4, 0, DPOT), ("slab", -5, 0, "flower_pot"), ("slab", -6, 0, DPOT),
               ("t", 6, -1, "furnace", "north"), ("t", 7, -1, "smoker", "north"), ("t", 8, -1, "craft"),
               ("lamp", -4, 2), ("lamp", -9, 2), ("lamp", 7, 2), ("lamp", -6, -4)], "stonesmeltery")
    # ware store: shelving aisles of finished pots and bricks
    fit(d, u, [("rack2", x, -1, "north") for x in range(-1, -9, -1)] +
        [("rack2", x, 3, "north") for x in range(-4, -10, -1)] + [("rack2", x, 4, "south") for x in range(-4, -10, -1)] +
        [("rack2", x, 7, "north") for x in range(-4, -10, -1)] +
        [("keg", -1, 1, "west", "terracotta"), ("keg", -1, 2, "west", "bricks"), ("slab", 6, -1, DPOT),
         ("slab", 7, -1, DPOT), ("b", 8, -1, "bricks", "bricks"), ("b", 9, -1, "terracotta"), ("t", 6, 3, "chest", "east"),
         ("lamp", -6, 1), ("lamp", -6, 6), ("lamp", 8, 2)], "stonesmeltery")
    # manager's office and sample room
    fit(d, t, [("bs", -1, -1), ("t", -2, -1, "lectern", "north"), ("bs", -3, -1), ("slab", -4, 3, CANDLE),
               ("slab", -5, 3, DPOT), ("chair", -4, 4, "south"), ("chair", -5, 2, "north"), ("chair", -4, 2, "north"),
               ("t", -1, 3, "carto"), ("t", -1, 0, "plant"),
               ("rug", -7, 2, 5, 3), ("slab", -8, -1, DPOT), ("slab", -9, -1, "flower_pot"), ("slab", -10, -1, DPOT),
               ("slab", -11, -1, DPOT), ("t", -2, 0, "chest", "south"), ("t", -3, 0, "chest", "south"),
               ("table", -10, 4), ("table", -11, 4), ("chair", -10, 3, "north"), ("chair", -11, 5, "south"),
               ("chair", -10, 5, "south"), ("t", 6, -1, "plant"), ("lamp", -4, 2), ("lamp", -10, 2), ("lamp", -8, -3)],
        "stonesmeltery")
    tb = {"Hearthwood": "bricks", "Cascadia": "cobblestone", "Neoterra": "white_concrete"}[d.pack]
    for y in range(2, info["ridge"] + 6):
        d.set(x2, y, (z1 + z2) // 2, tb)
        d.set(x2 + 1, y, (z1 + z2) // 2, tb)
    lamp_post(d, info["mx"] + 2, z1 - 2)


# ------------------------------------------------------------------------------------------------ mechanic
def mc_parts(d, sl):
    """Parts store: shelving bays of parts, a parts counter with the order book, crates of gears and springs."""
    x1, z1, x2, z2, s, ax = sl
    info = hall(d, x1, z1, x2, z2, 1, ax, "PARTS")
    fit(d, info["rooms"][0], [("rack2", x, -1, "north") for x in range(-1, -6, -1)] +
        [("keg", -1, 1, "west", "piston[extended=false,facing=up]"), ("keg", -1, 2, "west", "observer[facing=up,powered=false]"),
         ("t", -1, 3, "chest", "west"), ("slab", 1, 1, CANDLE), ("t", 2, 1, "lectern", "north"),
         ("rack2", -3, 3, "south"), ("rack2", -4, 3, "south"), ("lamp", -3, 1), ("lamp", 2, -2)], "mechanic")
    lamp_post(d, info["mx"] + 2, z1 - 2)


def mc_garage(d, sl):
    """Garage: three wide open bays with inspection pits, chain hoists over each bay and a rail spur; work
    benches and tool boards along the back."""
    x1, z1, x2, z2, s, ax = sl
    info = hall(d, x1, z1, x2, z2, 1, "x", "GARAGE", sh=6)
    bw = (x2 - x1 - 1) // 3
    for b in range(3):
        bx = x1 + 1 + b * bw
        for x in range(bx, bx + bw - 1):
            for y in range(2, 6):
                d.set(x, y, z1, AIR)
            d.set(x, 6, z1, f"{MAT[d.pack]['beam']}[axis=x]" if d.pack != "Neoterra" else "cyan_terracotta")
        cxp = bx + (bw - 1) // 2
        for z in range(z1 + 2, z2 - 2):
            d.set(cxp, 1, z, "polished_andesite" if z % 2 else "smooth_stone")
        for yy in range(5, info["top"] + 1):
            d.set(cxp, yy, (z1 + z2) // 2, CHAIN)
        d.set(cxp, 4, (z1 + z2) // 2, "iron_block")
    fit(d, info["rooms"][0], [("t", -1, -1, "craft"), ("slab", -2, -1, CANDLE), ("t", -3, -1, "anvil", "north"),
                              ("rack", -4, -1, "north"), ("t", -5, -1, "piston"), ("t", -6, -1, "observer", "north"),
                              ("hook", -2, -1, "north"), ("hook", -5, -1, "north"), ("t", 0, -1, "barrel")],
        "mechanic")
    rails(d, [(x1 + 2, z) for z in range(max(0, z1 - 4), z1 + 3)], "north_south")


def mc_engineshed(d, sl):
    """Engine shed: two tracks running in with an engine on the pit, a turntable stub, smoke vents in the roof;
    the foreman's office upstairs."""
    x1, z1, x2, z2, s, ax = sl
    info = hall(d, x1, z1, x2, z2, 2, ax, "ENGINE SHED")
    g, u = info["rooms"]
    fx1, fz1, fx2, fz2, y = g[:5]
    for tx in (fx1 + 5, fx2 - 2):
        for z in range(fz1, fz2):
            if d.air(tx, 2, z) and d.air(tx, 3, z):
                d.set(tx, 2, z, "rail[shape=north_south,waterlogged=false]")
    fit(d, g, [("t", -1, -1, "craft"), ("t", -1, -2, "dispenser", "west"), ("rack", -1, 1, "west"),
               ("b", -4, -1, "iron_block", "lever[face=floor,facing=north,powered=false]"), ("b", -5, -1, "furnace[facing=north,lit=false]"),
               ("t", -1, 0, "lamp"), ("lamp", -3, 2), ("lamp", 6, 2)], "mechanic")
    fit(d, u, [("slab", -3, 3, CANDLE), ("slab", -4, 3, "flower_pot"), ("chair", -3, 4, "south"), ("chair", -4, 2, "north"),
               ("bs", -1, -1), ("t", -2, -1, "lectern", "north"), ("t", -3, -1, "carto"), ("bs", -4, -1),
               ("t", -1, 0, "plant"), ("rack", -1, 2, "west"), ("rug", -5, 2, 4, 3), ("lamp", -3, 2)], "mechanic")
    for x in range(x1 + 3, x2 - 2, 4):               # smoke vents along the ridge
        col(d, x, (z1 + z2) // 2, info["ridge"] + 1, info["ridge"] + 2, "iron_bars")
    lamp_post(d, info["mx"] - 2, z1 - 2)


def mc_machinehall(d, sl):
    """Machine hall: erecting floor under an overhead crane girder, fitting shop, parts store and drawing office."""
    x1, z1, x2, z2, s, ax = sl
    info = hall(d, x1, z1, x2, z2, 4, ax, "MACHINE HALL")
    g, m, u, t = info["rooms"]
    fx1, fz1, fx2, fz2, y = g[:5]
    zc = (fz1 + fz2) // 2
    for x in range(fx1 + 4, fx2 + 1):                # crane girder across the hall
        if d.air(x, y + 3, zc):
            d.set(x, y + 3, zc, "iron_bars")
    # erecting floor: machines being built under the crane girder, benches and tool boards round the walls
    fit(d, g, [("b", -4, zc - fz1, "piston[extended=false,facing=up]", "observer[facing=up,powered=false]"),
               ("b", -5, zc - fz1, "smooth_stone", "dispenser[facing=up,triggered=false]"),
               ("b", -6, zc - fz1, "iron_block"),
               ("b", -9, zc - fz1, "iron_block", "lever[face=floor,facing=north,powered=false]"),
               ("b", -10, zc - fz1, "piston[extended=false,facing=up]"), ("b", -13, zc - fz1, "smooth_stone", "iron_block"),
               ("t", -1, -1, "craft"), ("t", -2, -1, "anvil", "north"), ("slab", -3, -1, CANDLE), ("rack", -4, -1, "north"),
               ("t", -5, -1, "craft"), ("slab", -6, -1, "redstone_lamp[lit=false]"), ("t", -7, -1, "grind", "north"),
               ("rack", -8, -1, "north"), ("hook", -4, -1, "north"), ("hook", -8, -1, "north"),
               ("rack", -1, 1, "west"), ("t", -1, 2, "barrel"), ("t", -1, 3, "barrel"),
               ("rack", 2, 0, "south"), ("rack", 3, 0, "south"), ("t", 4, 0, "craft"), ("slab", 5, 0, CANDLE),
               ("t", -3, 0, "chest", "south"), ("t", -4, 0, "chest", "south"), ("slab", -5, 0, "flower_pot"),
               ("lamp", -6, 1), ("lamp", -11, 1), ("lamp", 4, 2), ("lamp", -6, -3), ("lamp", -11, -3)], "mechanic")
    # fitting shop: fitters' benches in two rows with vices (anvils) and stools
    fit(d, m, [("t", -1, -1, "craft"), ("slab", -2, -1, "flower_pot"), ("t", -3, -1, "anvil", "north"),
               ("slab", -4, -1, CANDLE), ("t", -5, -1, "craft"), ("t", -6, -1, "anvil", "north"), ("slab", -7, -1),
               ("t", -8, -1, "grind", "north"),
               ("slab", -4, 3), ("slab", -5, 3, "redstone_lamp[lit=false]"), ("chair", -4, 4, "south"), ("chair", -5, 4, "south"),
               ("slab", -8, 3, CANDLE), ("t", -9, 3, "anvil", "north"), ("slab", -10, 3), ("chair", -8, 4, "south"),
               ("chair", -10, 4, "south"), ("rack", -1, 1, "west"), ("rack", -1, 2, "west"), ("t", -1, 3, "chest", "west"),
               ("hook", -1, 1, "west"), ("hook", -1, 2, "west"), ("t", 6, -1, "barrel"), ("t", 7, -1, "craft"),
               ("rack", -3, 0, "south"), ("rack", -4, 0, "south"), ("t", -5, 0, "barrel"),
               ("lamp", -5, 2), ("lamp", -9, 2), ("lamp", -6, -3), ("lamp", 7, 2)], "mechanic")
    # parts store: shelving aisles
    fit(d, u, [("rack2", x, -1, "north") for x in range(-1, -9, -1)] +
        [("rack2", x, 3, "north") for x in range(-4, -10, -1)] + [("rack2", x, 4, "south") for x in range(-4, -10, -1)] +
        [("keg", -1, 1, "west", "piston[extended=false,facing=up]"), ("keg", -1, 2, "west", "redstone_lamp[lit=false]"),
         ("t", 6, -1, "chest", "north"), ("t", 7, -1, "chest", "north"), ("keg", 8, -1, "north", "iron_block"),
         ("t", 6, 3, "barrel"), ("lamp", -5, 2), ("lamp", -6, 6), ("lamp", 7, 2)], "mechanic")
    # drawing office: drawing boards (cartography tables), plan chests, the chief engineer's desk
    fit(d, t, [("bs", -1, -1), ("t", -2, -1, "carto"), ("t", -3, -1, "lectern", "north"), ("bs", -4, -1),
               ("t", -5, -1, "carto"), ("bs", -6, -1),
               ("slab", -4, 3, CANDLE), ("slab", -5, 3, "flower_pot"), ("chair", -4, 4, "south"),
               ("slab", -8, 3, CANDLE), ("chair", -8, 4, "south"), ("t", -1, 0, "plant"), ("rug", -9, 2, 5, 3),
               ("t", -11, 3, "carto"), ("chair", -11, 4, "south"), ("t", -2, 0, "chest", "south"), ("t", -3, 0, "chest", "south"),
               ("slab", -4, 0, CANDLE), ("t", -5, 0, "chest", "south"), ("desk", -5, -4, "north"), ("desk", -9, -4, "north"),
               ("t", -1, 3, "plant"), ("t", 6, -1, "plant"), ("lamp", -5, 2), ("lamp", -11, 2), ("lamp", -7, -3)], "mechanic")
    lamp_post(d, info["mx"] + 2, z1 - 2)


# ------------------------------------------------------------------------------------------------ stonemason
def sn_cutshed(d, sl):
    """Cutting shed: open shed with a row of stone saws on bankers, blocks waiting on pallets and a gantry beam."""
    x1, z1, x2, z2, s, ax = sl
    open_shed(d, x1, z1, x2, z2, 4, "x", back="south", floor=MAT[d.pack]["stone"])
    zc = (z1 + z2) // 2
    for x in range(x1 + 2, x2 - 1, 2):               # saw row: one saw every second cell
        d.set(x, 2, zc, "stonecutter[facing=north]")
        d.set(x, 2, z2 - 1, ["stone_bricks", "polished_andesite", "smooth_stone", "chiseled_stone_bricks"][x % 4])
    d.rack(x1 + 1, 2, z2 - 1, "east")
    hang(d, x1 + 3, 4, zc - 1)
    hang(d, x2 - 3, 4, zc - 1)
    stone_stack(d, [(x1 + 1, z1 + 1, 2), (x1 + 3, z1 + 1, 1), (x1 + 5, z1 + 1, 2), (x2 - 1, z1 + 1, 2)], 2)
    for x in (x1 - 1, x2 + 1):
        col(d, x, zc, 2, 7, MAT[d.pack]["post"])
    for x in range(x1 - 1, x2 + 2):
        d.set(x, 8, zc, "iron_block" if d.pack == "Neoterra" else f"{MAT[d.pack]['beam']}[axis=x]")
    post_sign(d, x1 + 1, z1 - 1, ["CUTTING", "SHED"])


def sn_quarry(d, sl):
    """Quarry yard: a stepped quarry face of stone terraces with a derrick crane lifting a block, rubble heap,
    blocks waiting for the saws and the quarryman's hut."""
    x1, z1, x2, z2, s, ax = sl
    for z in range(z1 + 3, z2 + 1):
        h = min(7, (z - z1 - 2) + 1)
        for x in range(x1, x2 + 1):
            for y in range(2, 2 + h):
                d.set(x, y, z, "stone" if (x + y + z) % 5 else "andesite" if y % 2 else "cobblestone")
    mx = x1 + 3
    for y in range(2, 13):
        d.set(mx, y, z1 + 1, MAT[d.pack]["post"] if d.pack != "Neoterra" else "iron_block")
    for x in range(mx, mx + 7):
        d.set(x, 12, z1 + 1, f"{MAT[d.pack]['beam']}[axis=x]" if d.pack != "Neoterra" else "iron_block")
    for y in range(4, 12):
        d.set(mx + 6, y, z1 + 1, CHAIN)
    d.set(mx + 6, 3, z1 + 1, "stone")
    heap(d, x2 - 2, z1 + 1, 1.8, ["cobblestone", "gravel", "andesite"])
    stone_stack(d, [(x1 + 6, z1, 2), (x1 + 7, z1, 1), (x1 + 8, z1, 2)], 2)
    d.set(x1 + 1, 2, z1, "barrel[facing=up,open=false]")
    d.set(x1 + 1, 3, z1, "lantern[hanging=false,waterlogged=false]")
    d.set(x1, 2, z1 + 1, "grindstone[face=floor,facing=east]")


def sn_showroom(d, sl):
    """Monument showroom behind a columned portico: headstones, urns and obelisks on plinths, a sales desk, the
    carving studio upstairs and the drawings library at the top."""
    x1, z1, x2, z2, s, ax = sl
    pz = 2 if (z2 - z1) >= 11 else 1
    info = hall(d, x1, z1 + pz, x2, z2, 3, ax, "MONUMENTS")
    pil = {"Hearthwood": "quartz_pillar[axis=y]", "Cascadia": "polished_andesite",
           "Neoterra": "quartz_pillar[axis=y]"}[d.pack]
    for x in range(x1, x2 + 1, 3):
        if abs(x - info["mx"]) > 1:
            col(d, x, z1, 2, 5, pil)
    for x in range(x1, x2 + 1):
        d.set(x, 6, z1, "smooth_quartz_slab[type=bottom,waterlogged=false]")
        if pz == 2:
            d.set(x, 6, z1 + 1, "smooth_quartz_slab[type=bottom,waterlogged=false]")
    g, u, t = info["rooms"]
    wall = WALLST("stone_brick_wall")
    fit(d, g, [("b", -2, 3, "polished_andesite", DPOT), ("b", -4, 3, "polished_andesite", wall),
               ("b", -6, 3, "polished_andesite", "chiseled_stone_bricks"), ("b", -2, -1, "stone_bricks", wall),
               ("b", -3, -1, "stone_bricks", wall), ("b", -5, -1, "polished_andesite", DPOT),
               ("b", -6, -1, "chiseled_stone_bricks", "stone_brick_slab[type=bottom,waterlogged=false]"),
               ("slab", -1, 1, CANDLE), ("slab", -1, 2, "flower_pot"), ("chair", -2, 1, "west"),
               ("t", -1, 0, "plant"), ("lamp", -3, 2), ("lamp", -6, 2)], "stonemason")
    fit(d, u, [("t", -1, -1, "cutter", "north"), ("b", -2, -1, "polished_andesite"), ("t", -3, -1, "cutter", "north"),
               ("b", -4, 3, "stone", WALLST("stone_brick_wall")), ("b", -5, 3, "smooth_stone"), ("chair", -4, 4, "south"),
               ("rack", -1, 1, "west"), ("t", -1, 2, "grind", "west"), ("lamp", -3, 2)], "stonemason")
    fit(d, t, [("bs", -1, -1), ("t", -2, -1, "book"), ("t", -3, -1, "lectern", "north"), ("bs", -4, -1),
               ("t", -5, -1, "carto"), ("slab", -4, 3, CANDLE), ("chair", -4, 4, "south"), ("t", -1, 0, "plant"),
               ("rug", -6, 2, 4, 3), ("lamp", -3, 2)], "stonemason")
    for ox in (-3, 4):                               # obelisks either side of the entrance
        x = info["mx"] + ox
        if d.bp.inside(x, 2, z1 - 2) and all(d.air(x, y, z1 - 2) for y in range(2, 8)):
            d.set(x, 2, z1 - 2, "stone_bricks")
            col(d, x, z1 - 2, 3, 5, "polished_andesite")
            d.set(x, 6, z1 - 2, "chiseled_stone_bricks")
            d.set(x, 7, z1 - 2, slab("stone_brick_slab"))


def sn_lodge(d, sl):
    """Masons' lodge: carving hall, tracing floor (drawing boards), pattern library and the masters' room."""
    x1, z1, x2, z2, s, ax = sl
    info = hall(d, x1, z1, x2, z2, 4, ax, "MASONS' LODGE")
    g, m, u, t = info["rooms"]
    # carving hall: bankers (work stones) in a row with blocks being dressed, saws on the back wall
    fit(d, g, [("t", -1, -1, "cutter", "north"), ("b", -2, -1, "stone_bricks"), ("t", -3, -1, "cutter", "north"),
               ("t", -4, -1, "grind", "north"), ("b", -5, -1, "chiseled_stone_bricks", "stone_brick_slab[type=bottom,waterlogged=false]"),
               ("t", -6, -1, "cutter", "north"), ("rack", -7, -1, "north"),
               ("b", -4, 3, "stone", "stone"), ("b", -5, 3, "polished_andesite"), ("chair", -5, 4, "south"),
               ("b", -9, 3, "smooth_stone", DPOT), ("b", -10, 3, "stone", "stone_brick_slab[type=bottom,waterlogged=false]"),
               ("chair", -10, 4, "south"), ("b", -13, 3, "polished_andesite", WALLST("stone_brick_wall")),
               ("b", -5, -5, "stone_bricks", "chiseled_stone_bricks"), ("b", -9, -5, "smooth_stone", DPOT),
               ("rack", -1, 1, "west"), ("rack", -1, 2, "west"), ("hook", -1, 1, "west"), ("t", -1, 3, "barrel"),
               ("rack", 2, 0, "south"), ("slab", 3, 0, CANDLE), ("t", 4, 0, "grind", "south"), ("t", 5, 0, "barrel"),
               ("slab", -3, 0, "flower_pot"), ("t", -4, 0, "chest", "south"),
               ("t", -1, -3, "barrel"), ("t", -1, -4, "barrel"), ("b", 6, -1, "stone_bricks", "stone_bricks"),
               ("b", 7, -1, "polished_andesite"), ("t", 8, -1, "cutter", "north"),
               ("lamp", -4, 2), ("lamp", -9, 2), ("lamp", -13, 2), ("lamp", 4, 2), ("lamp", -7, -4)], "stonemason")
    # tracing floor: drawing boards in a row facing the windows, templates hung on the walls
    fit(d, m, [("t", -3, 3, "carto"), ("chair", -3, 4, "south"), ("t", -6, 3, "carto"), ("chair", -6, 4, "south"),
               ("t", -9, 3, "carto"), ("chair", -9, 4, "south"), ("t", -12, 3, "carto"), ("chair", -12, 4, "south"),
               ("slab", -1, -1, CANDLE), ("t", -2, -1, "lectern", "north"), ("slab", -3, -1, "flower_pot"),
               ("t", -4, -1, "chest", "north"), ("t", -5, -1, "chest", "north"), ("slab", -6, -1, DPOT),
               ("t", -7, -1, "lectern", "north"), ("t", -1, 0, "plant"), ("t", -1, 2, "chest", "west"),
               ("desk", -6, -4, "north"), ("desk", -10, -4, "north"), ("t", 6, -1, "plant"), ("slab", 7, -1, CANDLE),
               ("t", -1, -3, "plant"), ("bs", -9, -1), ("bs", -10, -1), ("t", 8, -1, "chest", "north"),
               ("lamp", -3, 2), ("lamp", -8, 2), ("lamp", -12, 2), ("lamp", -8, -3)], "stonemason")
    # pattern library: bookcases, reading tables
    fit(d, u, [("bs", x, -1) for x in range(-1, -9, -1)] +
        [("t", -1, 1, "book", "west"), ("t", -1, 2, "book", "west"), ("table", -4, 3), ("table", -5, 3),
         ("chair", -4, 2, "north"), ("chair", -5, 4, "south"), ("chair", -4, 4, "south"), ("rug", -7, 2, 5, 3),
         ("table", -10, 3), ("chair", -10, 4, "south"), ("chair", -10, 2, "north"), ("t", -12, 3, "lectern", "south"),
         ("bs", -3, 0), ("t", -4, 0, "book", "south"), ("bs", -5, 0), ("t", 6, -1, "plant"), ("t", 7, -1, "lectern", "north"),
         ("table", -5, -4), ("chair", -6, -4, "west"), ("chair", -4, -4, "east"),
         ("lamp", -5, 2), ("lamp", -10, 2), ("lamp", -5, -3)], "stonemason")
    # masters' room: the master's desk, a meeting table, the lodge chest and banners
    fit(d, t, [("bs", -1, -1), ("t", -2, -1, "lectern", "north"), ("bs", -3, -1), ("slab", -4, 3, CANDLE),
               ("slab", -5, 3, DPOT), ("chair", -4, 4, "south"), ("chair", -5, 2, "north"), ("chair", -4, 2, "north"),
               ("t", -1, 0, "plant"), ("rack", -1, 2, "west"), ("rug", -7, 2, 5, 3),
               ("table", -9, -4), ("table", -10, -4), ("table", -11, -4), ("chair", -9, -5, "north"), ("chair", -10, -5, "north"),
               ("chair", -11, -5, "north"), ("chair", -9, -3, "south"), ("chair", -11, -3, "south"), ("chair", -12, -4, "west"),
               ("t", -2, 0, "chest", "south"), ("slab", -3, 0, CANDLE), ("t", 6, -1, "plant"), ("t", -6, -1, "chest", "north"),
               ("lamp", -4, 2), ("lamp", -10, -4), ("lamp", -10, 2)], "stonemason")
    lamp_post(d, info["mx"] - 2, z1 - 2)
    lamp_post(d, info["mx"] + 2, z1 - 2)


# ------------------------------------------------------------------------------------------------ crusher
def cr_orebins(d, sl):
    """Ore bins: raised timber bins on posts with chutes over a tram line, a top trestle with its own rails, a
    ladder, and the bin-man's rack and lamp at the foot."""
    x1, z1, x2, z2, s, ax = sl
    M = MAT[d.pack]
    zb1, zb2 = z1 + 2, z1 + 5

    def bin_row(za, zb, fill):
        for x in range(x1, x2 + 1):
            for z in range(za, zb + 1):
                if (x - x1) % 3 == 0 and z in (za, zb):      # posts every third cell
                    col(d, x, z, 2, 5, M["post"])
                for y in range(6, 9):
                    edge = x in (x1, x2) or z in (za, zb) or (x - x1) % 3 == 0
                    d.set(x, y, z, M["board"] if edge else (fill[0] if y < 8 else fill[1]))
                d.set(x, 5, z, M["deck"])
    bin_row(zb1, zb2, ("gravel", "cobblestone"))
    for x in range(x1 + 2, x2 + 1, 3):
        d.set(x, 4, (zb1 + zb2) // 2, "hopper[enabled=true,facing=down]")
    rails(d, [(x, (zb1 + zb2) // 2) for x in range(max(0, x1 - 1), x2 + 2)], "east_west")
    for y in range(2, 9):
        d.set(x2 + 1, y, zb1, "ladder[facing=east,waterlogged=false]")
    if z2 - zb2 >= 6:
        bin_row(zb2 + 3, zb2 + 5, ("sand", "gravel"))
    if d.pack == "Neoterra":
        d.fill(x1 - 1, 9, zb1 - 1, x2 + 1, 9, zb2 + 1, "smooth_quartz")
    else:
        s_, sl_ = roofset(d)
        d.gable(x1, zb1, x2, zb2, 10, "x", s_, sl_, MAT[d.pack]["board"])
        for x in range(x1, x2 + 1):
            for z in (zb1, zb2):
                d.set(x, 9, z, MAT[d.pack]["board"])
    d.rack(x1 + 1, 2, z2, "north")
    d.set(x1 + 2, 2, z2, "barrel[facing=up,open=false]")
    lamp_post(d, x1 + 3, z2)
    post_sign(d, x1 + 1, z1, ["ORE BINS"])
    for x in range(x1, x2 + 1):                      # top trestle with the feed tramway
        d.set(x, 9, zb1 - 1, MAT[d.pack]["deck"])
        d.set(x, 10, zb1 - 2, MAT[d.pack]["fence"])
        d.set(x, 10, zb1 - 1, "rail[shape=east_west,waterlogged=false]")
        if (x - x1) % 3 == 0:
            col(d, x, zb1 - 1, 2, 8, MAT[d.pack]["post"])


def cr_tipple(d, sl):
    """Tipple: a tall headframe with an enclosed bin house on top, a cage on the chain, rails at the foot and the
    two-storey hoist house (winding engine below, weigh clerk above)."""
    x1, z1, x2, z2, s, ax = sl
    M = MAT[d.pack]
    tx1, tx2, tz1, tz2 = x1 + 1, x1 + 5, z1 + 1, z1 + 5
    wide = (x2 - x1) >= 14
    for x, z in ((tx1, tz1), (tx2, tz1), (tx1, tz2), (tx2, tz2)):
        col(d, x, z, 2, 16, M["post"])
    for y in (6, 11, 16):
        for x, z in perim(tx1, tz1, tx2, tz2):
            d.set(x, y, z, M["deck"] if d.pack != "Neoterra" else "iron_block")
    d.fill(tx1, 11, tz1, tx2, 11, tz2, M["deck"])
    d.fill(tx1 + 1, 12, tz1 + 1, tx2 - 1, 13, tz2 - 1, "gravel")
    for x in range(tx1, tx2 + 1):
        d.set(x, 17, (tz1 + tz2) // 2, f"{M['beam']}[axis=x]" if d.pack != "Neoterra" else "iron_block")
    for x, z in perim(tx1, tz1, tx2, tz2):
        for y in range(12, 16):
            if d.air(x, y, z):
                d.set(x, y, z, M["board"] if (x + y) % 4 else "glass_pane")
    d.fill(tx1 - 1, 16, tz1 - 1, tx2 + 1, 16, tz2 + 1, slab(roofset(d)[1]))
    for y in range(3, 11):
        d.set((tx1 + tx2) // 2, y, (tz1 + tz2) // 2, CHAIN)
    d.set((tx1 + tx2) // 2, 2, (tz1 + tz2) // 2, "iron_block")
    rails(d, [(x, tz2 + 1) for x in range(x1, x2 + 1)], "east_west")
    for y in range(2, 11):                           # ladder up the headframe leg
        d.set(tx1 - 1, y, tz1 + 1, "ladder[facing=west,waterlogged=false]")
    heap(d, tx2 + 2, tz1 + 1, 1.6, ["gravel", "cobblestone", "coal_block"])
    hh = hall(d, x1 + 8, z1 + 2, x2, z2, 2, "x", "HOIST HOUSE") if wide else \
        hall(d, x1, z1 + 8, x2, z2, 2, "z", "HOIST HOUSE")
    fit(d, hh["rooms"][0], [("t", -1, -1, "dispenser", "north"), ("b", -2, -1, "piston[extended=false,facing=up]", CHAIN),
                            ("slab", -1, 1, CANDLE), ("t", -3, -1, "craft"), ("rack", -1, 2, "west"), ("lamp", -2, 1)],
        "crusher")
    fit(d, hh["rooms"][1], [("t", -1, -1, "lectern", "north"), ("slab", -2, -1, CANDLE), ("chair", -2, -2, "south"),
                            ("bs", -3, -1), ("rack", -1, 1, "west"), ("rug", -3, 1, 2, 2), ("lamp", -2, 1)], "crusher")


def cr_screenhouse(d, sl):
    """Screening house: grinding floor, screen deck (iron screens over chutes), sack loft - and an inclined
    conveyor gallery climbing to the top."""
    x1, z1, x2, z2, s, ax = sl
    info = hall(d, x1 + 4, z1, x2, z2, 3, ax, "SCREEN HOUSE")
    g, u, u2 = info["rooms"]
    fit(d, g, [("t", -1, -1, "grind", "north"), ("slab", -2, -1, "flower_pot"), ("t", -3, -1, "cutter", "north"),
               ("b", -4, -1, "gravel", "gravel"), ("rack", -1, 1, "west"), ("keg", -1, 2, "west", "sand"),
               ("b", -3, 3, "hopper[enabled=true,facing=down]"), ("lamp", -2, 2)], "crusher")
    trap = "iron_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]"
    fit(d, u, [("b", x, 4, "hopper[enabled=true,facing=down]", trap) for x in (-2, -3, -4, -5)] +
        [("rack", -1, -1, "north"), ("b", -2, -1, "gravel"), ("b", -3, -1, "sand"), ("lamp", -3, 2)], "crusher")
    fit(d, u2, [("b", -1, -1, "white_wool", "brown_wool"), ("b", -2, -1, "white_wool"), ("rack2", -3, -1, "north"),
                ("keg", -1, 1, "west", "white_wool"), ("rack2", -4, -1, "north"), ("lamp", -3, 2)], "crusher")
    gx = x1 + 1
    for i, z in enumerate(range(z2, z1 + 1, -1)):   # conveyor gallery rising toward the street
        y = 2 + i // 2
        if y > 9:
            break
        d.set(gx, y, z, slab("smooth_stone_slab", "top" if i % 2 else "bottom"))
        d.set(gx - 1, y + 1, z, "iron_bars")
        d.set(gx + 1, y + 1, z, "iron_bars")
        if i % 3 == 0:
            for yy in range(2, y):
                d.set(gx, yy, z, MAT[d.pack]["post"])


HEAD_TOWER = {"Hearthwood": (41, 29, 43, 33), "Cascadia": (25, 27, 27, 31), "Neoterra": (21, 29, 25, 31)}


def cr_plant(d, sl):
    """Crushing plant: jaw-crusher floor, grading floor, bagging floor and sack store, with a head tower."""
    x1, z1, x2, z2, s, ax = sl
    info = hall(d, x1, z1, x2, z2, 4, ax, "CRUSHING PLANT")
    g, m, u, t = info["rooms"]
    jaw = [("b", -5, 3, "piston[extended=false,facing=east]"), ("b", -4, 3, "gravel", "hopper[enabled=true,facing=down]"),
           ("b", -3, 3, "sticky_piston[extended=false,facing=west]"),
           ("b", -10, 3, "piston[extended=false,facing=east]"), ("b", -9, 3, "gravel", "hopper[enabled=true,facing=down]"),
           ("b", -8, 3, "sticky_piston[extended=false,facing=west]")]
    # jaw-crusher floor: two jaw crushers (pistons either side of a hopper), feed bins and the crusherman's bench
    fit(d, g, jaw + [("t", -1, -1, "grind", "north"), ("t", -2, -1, "cutter", "north"), ("b", -3, -1, "gravel"),
                     ("b", -4, -1, "gravel", "gravel"), ("b", -5, -1, "cobblestone"), ("t", -6, -1, "grind", "north"),
                     ("rack", -7, -1, "north"), ("rack", -1, 1, "west"), ("t", -1, 0, "barrel"), ("t", -1, 2, "barrel"),
                     ("b", -5, -5, "piston[extended=false,facing=east]"), ("b", -4, -5, "gravel", "hopper[enabled=true,facing=down]"),
                     ("b", -3, -5, "sticky_piston[extended=false,facing=west]"),
                     ("rack", 2, 0, "south"), ("slab", 3, 0, CANDLE), ("t", 4, 0, "barrel"), ("t", 5, 0, "barrel"),
                     ("slab", -3, 0, "flower_pot"), ("t", -4, 0, "chest", "south"), ("hook", -7, -1, "north"),
                     ("lamp", -4, 1), ("lamp", -9, 1), ("lamp", 4, 2), ("lamp", -4, -4), ("lamp", -12, 1)], "crusher")
    # grading floor: screens (trapdoors over hoppers) in a row, graded sand and gravel in bins
    fit(d, m, [("t", -1, -1, "craft"), ("slab", -2, -1, CANDLE), ("b", -3, -1, "hopper[enabled=true,facing=down]"),
               ("b", -4, -1, "sand"), ("b", -5, -1, "red_sand"), ("b", -6, -1, "gravel"), ("t", -7, -1, "barrel"),
               ("b", -4, 3, "smooth_stone", "iron_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]"),
               ("b", -5, 3, "hopper[enabled=true,facing=down]", "iron_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]"),
               ("b", -6, 3, "hopper[enabled=true,facing=down]", "iron_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]"),
               ("b", -9, 3, "smooth_stone", "iron_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]"),
               ("b", -10, 3, "hopper[enabled=true,facing=down]", "iron_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]"),
               ("rack", -1, 1, "west"), ("keg", -1, 2, "west", "gravel"), ("keg", -1, 3, "west", "sand"),
               ("keg", -3, 0, "south", "sand"), ("keg", -4, 0, "south", "red_sand"), ("t", -5, 0, "barrel"),
               ("t", 6, -1, "chest", "north"), ("slab", 7, -1, "flower_pot"), ("desk", -10, -4, "north"),
               ("b", -5, 7, "hopper[enabled=true,facing=down]", "iron_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]"), ("b", -6, 7, "smooth_stone", "iron_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]"),
               ("chair", -5, 6, "north"), ("keg", -9, 7, "north", "gravel"), ("keg", -10, 7, "north", "sand"),
               ("t", 6, 3, "barrel"), ("t", -1, -3, "barrel"), ("t", -12, 3, "craft"),
               ("lamp", -4, 2), ("lamp", -9, 2), ("lamp", 7, 2), ("lamp", -6, -3), ("lamp", -10, 6)], "crusher")
    # bagging floor: sack filling bench with stools, stacked sacks
    fit(d, u, [("b", x, -1, "white_wool", "white_wool" if x % 2 else "brown_wool") for x in range(-1, -7, -1)] +
        [("rack2", -1, 1, "west"), ("rack2", -1, 2, "west"), ("slab", -4, 3, "flower_pot"), ("chair", -4, 4, "south"),
         ("b", -5, 3, "hopper[enabled=true,facing=down]"), ("slab", -6, 3, CANDLE), ("chair", -6, 4, "south"),
         ("b", -7, 3, "hopper[enabled=true,facing=down]"), ("slab", -8, 3), ("chair", -8, 4, "south"),
         ("t", -8, -1, "barrel"), ("t", -9, -1, "barrel"), ("rack", -10, -1, "north"),
         ("t", -3, 0, "barrel"), ("t", -4, 0, "barrel"), ("keg", -5, 0, "south", "white_wool"),
         ("b", 6, -1, "white_wool", "brown_wool"), ("b", 7, -1, "brown_wool"), ("t", 8, -1, "chest", "north"),
         ("b", -5, 7, "white_wool", "white_wool"), ("b", -6, 7, "brown_wool"), ("rack2", -7, 7, "north"),
         ("keg", -9, 7, "north", "white_wool"), ("t", -1, -3, "barrel"), ("t", 6, 3, "chest", "east"),
         ("lamp", -4, 2), ("lamp", -8, 2), ("lamp", -6, -3), ("lamp", 7, 2), ("lamp", -8, 6)], "crusher")
    # sack store: shelving aisles
    fit(d, t, [("rack2", x, -1, "north") for x in range(-1, -8, -1)] +
        [("rack2", x, 3, "north") for x in range(-4, -10, -1)] + [("rack2", x, 4, "south") for x in range(-4, -10, -1)] +
        [("keg", -1, 1, "west", "sand"), ("keg", -1, 2, "west", "gravel"), ("t", 6, -1, "barrel"), ("t", 7, -1, "barrel"),
         ("keg", 8, -1, "north", "white_wool"), ("lamp", -4, 2), ("lamp", -7, 6), ("lamp", 7, 2)], "crusher")
    M = MAT[d.pack]
    a, c, b, e = HEAD_TOWER[d.pack]
    h = info["top"] + 3
    for x, z in perim(a, c, b, e):
        for y in range(2, h + 1):
            d.set(x, y, z, M["board"] if (y % 4 or (x, z) in ((a, c), (b, c), (a, e), (b, e))) else "glass_pane")
    for x, z in ((a, c), (b, c), (a, e), (b, e)):
        col(d, x, z, 2, h, M["post"])
    d.fill(a - 1, h + 1, c - 1, b + 1, h + 1, e + 1, slab(roofset(d)[1]) if d.pack != "Neoterra" else "smooth_quartz")


# ------------------------------------------------------------------------------------------------ sifter
def sf_wash(d, sl):
    """Wash plant: a raised flume feeding a trommel drum (iron bars round a sand core) in an open shed, with tubs
    and chutes beneath and the washer's rack and stool."""
    x1, z1, x2, z2, s, ax = sl
    M = MAT[d.pack]
    open_shed(d, x1, z1, x2, z2, 5, "x", floor=M["stone"])
    zc = (z1 + z2) // 2
    for x in range(x1 + 2, x2 - 1):                  # the drum runs the length of the shed
        for y in (3, 4, 5):
            for z in (zc - 1, zc, zc + 1):
                if abs(y - 4) + abs(z - zc) == 1 or (y == 4 and z == zc):
                    d.set(x, y, z, "iron_bars" if (y, z) != (4, zc) else "sand")
        d.set(x, 2, zc, "hopper[enabled=true,facing=down]" if x % 2 else "water_cauldron[level=3]")
    for x in range(x1 - 1, x1 + 2):
        d.set(x, 6, zc, M["deck"])
        d.set(x, 7, zc, "water")
        d.set(x, 7, zc - 1, M["deck"])
        d.set(x, 7, zc + 1, M["deck"])
    d.rack(x2 - 1, 2, z1 + 1, "west")
    d.set(x2 - 2, 2, z1 + 1, f"{WOOD[d.pack]}_stairs[facing=east,half=bottom,shape=straight,waterlogged=false]")
    d.set(x2 - 1, 2, z2 - 1, "sand")
    d.set(x2 - 2, 2, z2 - 1, "gravel")
    hang(d, x1 + 2, 5, z1 + 1)
    post_sign(d, x1 + 2, z1 - 1, ["WASH PLANT"])


def sf_ponds(d, sl):
    """Settling ponds: three ponds with stone rims and a boardwalk, and a two-storey pump house (pump and tanks
    below, sample room above)."""
    x1, z1, x2, z2, s, ax = sl
    M = MAT[d.pack]
    w = (x2 - x1 - 9) // 3
    for i in range(3):
        px = x1 + i * (w + 1)
        pond(d, px, z1 + 1, px + w - 1, z2, M["stone"])
    for x in range(x1, x2 - 8):
        if d.air(x, 2, z1):
            d.set(x, 1, z1, M["deck"])
    ph = hall(d, x2 - 7, z1 + 1, x2, z2, 2, "x", "PUMP HOUSE")
    fit(d, ph["rooms"][0], [("b", -1, -1, "piston[extended=false,facing=up]", CHAIN), ("b", -2, -1, "water_cauldron[level=3]"),
                            ("t", -3, -1, "barrel"), ("rack", -1, 1, "west"), ("slab", -1, 2, CANDLE), ("lamp", -2, 1)],
        "sifter")
    fit(d, ph["rooms"][1], [("slab", -1, -1, "flower_pot"), ("slab", -2, -1, DPOT), ("t", -3, -1, "sieve"),
                            ("rack", -1, 1, "west"), ("b", -4, -1, "white_wool", "sand"), ("chair", -2, -2, "south"),
                            ("lamp", -2, 1)], "sifter")
    post_sign(d, x1 + 2, z1 - 1, ["SETTLING", "PONDS"])


def sf_drying(d, sl):
    """Sand drying house: drying trays on stands in rows, a sack corner and a sieve bench on both floors."""
    x1, z1, x2, z2, s, ax = sl
    info = hall(d, x1, z1, x2, z2, 2, ax, "DRYING HOUSE")
    g, u = info["rooms"]
    fen = MAT[d.pack]["fence"]
    tray = td(f"{WOOD[d.pack]}_trapdoor", "north")
    fit(d, g, [("b", x, 3, fen, tray) for x in (-3, -4, -5, -6)] +
        [("b", -1, -1, "white_wool", "white_wool"), ("b", -2, -1, "white_wool"), ("rack", -3, -1, "north"),
         ("t", -4, -1, "sieve"), ("keg", -1, 1, "west", "sand"), ("lamp", -4, 2)], "sifter")
    fit(d, u, [("b", x, 4, fen, tray) for x in (-2, -3, -4, -5, -6)] +
        [("b", -1, -1, "brown_wool"), ("rack", -2, -1, "north"), ("slab", -3, -1, DPOT), ("t", -1, 1, "sieve"),
         ("lamp", -4, 2)], "sifter")
    lamp_post(d, info["mx"] + 2, z1 - 2)


def sf_screen(d, sl):
    """Screening house: two screen decks, a bagging floor and a sample office with lectern and map table."""
    x1, z1, x2, z2, s, ax = sl
    info = hall(d, x1, z1, x2, z2, 4, ax, "SCREENING")
    g, m, u, t = info["rooms"]
    trap = "iron_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]"
    # lower screen deck: a long run of screens over hoppers, sieves and wash tubs
    deck1 = [("b", x, 3, "hopper[enabled=true,facing=down]", trap) for x in (-3, -4, -5, -6, -8, -9, -10, -11)]
    fit(d, g, deck1 + [("t", -1, -1, "sieve"), ("b", -2, -1, "water_cauldron[level=3]"), ("rack", -3, -1, "north"),
                       ("b", -4, -1, "sand", "sand"), ("t", -5, -1, "sieve"), ("b", -6, -1, "water_cauldron[level=3]"),
                       ("t", -7, -1, "barrel"), ("rack", -1, 1, "west"), ("t", -1, 2, "barrel"),
                       ("t", -5, -5, "sieve"), ("b", -6, -5, "water_cauldron[level=3]"), ("t", -9, -5, "sieve"),
                       ("rack", 2, 0, "south"), ("slab", 3, 0, CANDLE), ("t", 4, 0, "barrel"), ("t", -3, 0, "barrel"),
                       ("keg", -4, 0, "south", "sand"), ("lamp", -4, 1), ("lamp", -9, 1), ("lamp", 4, 2),
                       ("lamp", -7, -3)], "sifter")
    # upper screen deck: finer screens on a stone bench, sieving stools
    deck2 = [("b", x, 4, "smooth_stone", trap) for x in (-2, -3, -4, -5, -6, -7)]
    fit(d, m, deck2 + [("t", -1, -1, "sieve"), ("b", -2, -1, "white_wool", "white_wool"), ("rack", -3, -1, "north"),
                       ("t", -4, -1, "sieve"), ("chair", -4, -2, "south"), ("t", -6, -1, "sieve"), ("chair", -6, -2, "south"),
                       ("t", -8, -1, "barrel"), ("keg", -1, 1, "west", "gravel"), ("keg", -1, 2, "west", "sand"),
                       ("chair", -3, 3, "north"), ("chair", -6, 3, "north"), ("t", -9, 4, "sieve"),
                       ("t", -3, 0, "barrel"), ("t", -4, 0, "barrel"), ("t", 6, -1, "chest", "north"), ("t", 7, -1, "craft"),
                       ("t", -5, 7, "sieve"), ("chair", -5, 6, "north"), ("t", -8, 7, "sieve"), ("chair", -8, 6, "north"),
                       ("b", -11, 7, "water_cauldron[level=3]"), ("t", -12, 7, "sieve"), ("t", 6, 3, "barrel"),
                       ("keg", 7, 3, "east", "sand"), ("t", -1, -3, "barrel"),
                       ("lamp", -4, 2), ("lamp", -9, 2), ("lamp", 7, 2), ("lamp", -5, -4), ("lamp", -11, 6)], "sifter")
    # bagging floor
    fit(d, u, [("b", x, -1, "white_wool", "brown_wool" if x % 2 else None) for x in range(-1, -8, -1)] +
        [("rack2", -1, 1, "west"), ("rack2", -1, 2, "west"), ("slab", -4, 3, CANDLE), ("chair", -4, 4, "south"),
         ("slab", -5, 3), ("b", -6, 3, "hopper[enabled=true,facing=down]"), ("chair", -6, 4, "south"), ("slab", -7, 3, "flower_pot"),
         ("rack2", -9, 3, "north"), ("rack2", -10, 3, "north"), ("t", -3, 0, "barrel"), ("t", -4, 0, "barrel"),
         ("keg", -5, 0, "south", "white_wool"), ("t", 6, -1, "barrel"), ("t", 7, -1, "barrel"), ("t", 8, -1, "chest", "north"),
         ("b", -5, 7, "white_wool", "brown_wool"), ("b", -6, 7, "white_wool"), ("keg", -7, 7, "north", "sand"),
         ("rack2", -8, 7, "north"), ("t", -1, -3, "barrel"), ("t", -12, 3, "barrel"),
         ("lamp", -4, 2), ("lamp", -9, 1), ("lamp", -6, -3), ("lamp", 7, 2)], "sifter")
    # sample office
    fit(d, t, [("bs", -1, -1), ("t", -2, -1, "carto"), ("t", -3, -1, "lectern", "north"), ("bs", -4, -1),
               ("slab", -4, 3, "flower_pot"), ("slab", -5, 3, CANDLE), ("chair", -4, 4, "south"), ("chair", -5, 2, "north"),
               ("t", -1, 0, "plant"), ("rug", -7, 2, 5, 3),
               ("t", -6, -1, "sieve"), ("b", -7, -1, "water_cauldron[level=3]"), ("slab", -8, -1, "brewing_stand[has_bottle_0=true,"
               "has_bottle_1=true,has_bottle_2=false]"), ("chair", -7, -2, "south"), ("t", -2, 0, "chest", "south"),
               ("t", -3, 0, "chest", "south"), ("table", -10, 4), ("table", -11, 4), ("chair", -10, 3, "north"),
               ("chair", -11, 5, "south"), ("chair", -10, 5, "south"), ("t", 6, -1, "plant"), ("t", -1, 3, "plant"),
               ("lamp", -4, 2), ("lamp", -10, 2), ("lamp", -7, -3)], "sifter")
    lamp_post(d, info["mx"] - 2, z1 - 2)


PROJECTS = {
    "blacksmith": [bs_coalshed, bs_stable, bs_armourer, bs_ironworks],
    "smeltery": [sm_oreyard, sm_casting, sm_blast, sm_foundry],
    "stonesmeltery": [ss_drying, ss_kilnyard, ss_pughouse, ss_works],
    "mechanic": [mc_parts, mc_garage, mc_engineshed, mc_machinehall],
    "stonemason": [sn_cutshed, sn_quarry, sn_showroom, sn_lodge],
    "crusher": [cr_orebins, cr_tipple, cr_screenhouse, cr_plant],
    "sifter": [sf_wash, sf_ponds, sf_drying, sf_screen],
}


# ------------------------------------------------------------------------------------------------ palettes
TYPES = ["blacksmith", "smeltery", "stonesmeltery", "mechanic", "stonemason", "crusher", "sifter"]
FAM = {
    "slate": ("deepslate_tiles", "deepslate_tile_stairs", "deepslate_tile_slab"),
    "blueslate": ("dark_prismarine", "dark_prismarine_stairs", "dark_prismarine_slab"),
    "redtile": ("bricks", "brick_stairs", "brick_slab"),
    "browntile": ("mud_bricks", "mud_brick_stairs", "mud_brick_slab"),
    "rose": ("polished_granite", "polished_granite_stairs", "polished_granite_slab"),
    "spruce": ("spruce_planks", "spruce_stairs", "spruce_slab"),
    "darkoak": ("dark_oak_planks", "dark_oak_stairs", "dark_oak_slab"),
    "cobdeep": ("cobbled_deepslate", "cobbled_deepslate_stairs", "cobbled_deepslate_slab"),
    "mangrove": ("mangrove_planks", "mangrove_stairs", "mangrove_slab"),
}
PAL = {
    "Hearthwood": dict(
        roof=["slate", "blueslate", "browntile", "redtile", "rose", "spruce", "darkoak"],
        wall=["white_terracotta", "calcite", "smooth_sandstone", "yellow_terracotta", "stone_bricks", "mud_bricks",
              "pink_terracotta", "light_blue_terracotta", "bricks"],
        timber=[("stripped_dark_oak_log", "dark_oak_log"), ("stripped_spruce_log", "spruce_log"),
                ("stripped_oak_log", "oak_log")],
        plinth=["stone_bricks", "bricks", "mossy_stone_bricks", "cobblestone", "sandstone"],
        door=["crimson", "warped", "dark_oak", "acacia", "mangrove", "spruce", "bamboo"]),
    "Cascadia": dict(
        roof=["cobdeep", "blueslate", "mangrove", "slate", "spruce", "darkoak"],
        wall=[("stripped_spruce_log", "spruce_planks"), ("stripped_mangrove_log", "mangrove_planks"),
              ("stripped_birch_log", "birch_planks"), ("dark_oak_log", "dark_oak_planks"),
              ("spruce_log", "spruce_planks"), ("stripped_cherry_log", "cherry_planks"),
              ("stripped_oak_log", "oak_planks")],
        post=["dark_oak_log", "spruce_log", "stripped_spruce_log"],
        foot=["cobblestone", "tuff", "andesite", "mossy_cobblestone", "cobbled_deepslate"],
        door=["crimson", "spruce", "warped", "bamboo", "dark_oak", "mangrove", "jungle"]),
    "Neoterra": dict(
        wall=["light_gray_concrete", "gray_concrete", "white_terracotta", "white_concrete", "quartz_block",
              "light_gray_terracotta", "mangrove_planks", "cherry_planks", "polished_deepslate"],
        pil=["polished_blackstone", "white_concrete", "brown_terracotta", "gray_concrete", "polished_deepslate",
             "light_gray_concrete", "white_concrete"],
        acc=["orange_concrete", "yellow_concrete", "orange_terracotta", "lime_concrete", "cyan_terracotta",
             "yellow_terracotta", "magenta_concrete"],
        cop=["smooth_quartz_slab", "cut_copper_slab", "deepslate_tile_slab", "polished_blackstone_slab"],
        door=["mangrove", "dark_oak", "cherry", "warped", "birch", "oak", "crimson"]),
}


def palette_map(pack, t, k):
    """Block renames for type index t, building k (0 = core, 1..4 = add-ons): roof, walls, trim, accents."""
    p = PAL[pack]
    m = {}

    def fam(src, dst):
        for a, b in zip(FAM[src], FAM[dst]):
            if a != b:
                m["minecraft:" + a] = "minecraft:" + b
    if pack == "Hearthwood":
        fam("slate", p["roof"][(t + 2 * k) % len(p["roof"])])
        w = p["wall"][(t + 3 * k) % len(p["wall"])]
        if w != "calcite":
            m["minecraft:calcite"] = "minecraft:" + w
        tb = p["timber"][(t + k) % 3]
        m["minecraft:stripped_dark_oak_log"] = "minecraft:" + tb[0]
        m["minecraft:dark_oak_log"] = "minecraft:" + tb[1]
        pl = p["plinth"][(t + k) % 5]
        if pl != "stone_bricks":
            m["minecraft:stone_bricks"] = "minecraft:" + pl
        m["minecraft:dark_oak_door"] = f"minecraft:{p['door'][(t + k) % 7]}_door"
    elif pack == "Cascadia":
        fam("darkoak", p["roof"][(t + 2 * k) % len(p["roof"])])
        wl, wb = p["wall"][(t + 3 * k) % len(p["wall"])]
        post = p["post"][(t + k) % 3]
        if post == wl:
            post = "dark_oak_log" if wl != "dark_oak_log" else "stripped_spruce_log"
        m["minecraft:stripped_spruce_log"] = "minecraft:" + wl
        m["minecraft:spruce_log"] = "minecraft:" + post
        m["minecraft:spruce_planks"] = "minecraft:" + wb
        m["minecraft:cobblestone"] = "minecraft:" + p["foot"][(t + k) % 5]
        m["minecraft:spruce_door"] = f"minecraft:{p['door'][(t + k) % 7]}_door"
    else:
        w = p["wall"][(t + 2 * k) % len(p["wall"])]
        pil = p["pil"][(t + k) % len(p["pil"])]
        if pil == w:
            pil = "polished_blackstone" if w != "polished_blackstone" else "white_concrete"
        m["minecraft:white_concrete"] = "minecraft:" + w
        m["minecraft:light_gray_concrete"] = "minecraft:" + pil
        m["minecraft:cyan_terracotta"] = "minecraft:" + p["acc"][(t + k) % len(p["acc"])]
        m["minecraft:smooth_quartz_slab"] = "minecraft:" + p["cop"][(t + k) % len(p["cop"])]
        m["minecraft:birch_door"] = f"minecraft:{p['door'][(t + k) % 7]}_door"
    return {a: b for a, b in m.items() if a != b}


PROPS_OK = ("_stairs", "_slab", "_log", "_door", "_wood", "pillar")


def apply_palette(d, t, regions):
    bp = d.bp
    maps = {k: palette_map(d.pack, t, k) for k in range(5)}
    for y in range(bp.sy):
        layer = bp.grid[y]
        for z in range(bp.sz):
            row = layer[z]
            for x in range(bp.sx):
                s_ = row[x]
                if s_ == AIR:
                    continue
                k = 0
                for (a, c, b, e, kk) in regions:
                    if a <= x <= b and c <= z <= e:
                        k = kk
                        break
                name, _, props = s_.partition("[")
                new = maps[k].get(name)
                if new:
                    keep = props and new.endswith(PROPS_OK) and name.endswith(PROPS_OK)
                    row[x] = new + ("[" + props if keep else "")


def accent_wood(d, t):
    return PAL[d.pack]["door"][t % 7]


LAYOUTS = {
    "Hearthwood": [SLOTS["Hearthwood"],
                   [(3, 26, 13, 33, 1, "x"), (28, 3, 42, 10, 1, "x"), (30, 14, 40, 26, 2, "z"),
                    (16, 32, 38, 41, 3, "x")],
                   [(29, 15, 39, 22, 1, "x"), (27, 3, 41, 10, 1, "x"), (3, 27, 14, 38, 2, "z"),
                    (18, 29, 40, 38, 3, "x")]],
    "Cascadia": [SLOTS["Cascadia"],
                 [(40, 4, 47, 15, 1, "z"), (29, 4, 37, 19, 1, "z"), (28, 24, 46, 32, 2, "x"),
                  (3, 26, 24, 38, 3, "x")],
                 [(29, 24, 36, 35, 1, "z"), (39, 22, 47, 37, 1, "z"), (29, 3, 47, 11, 2, "x"),
                  (3, 27, 24, 38, 3, "x")]],
    "Neoterra": [SLOTS["Neoterra"],
                 [(3, 26, 14, 36, 1, None), (27, 3, 42, 14, 2, None), (27, 18, 43, 30, 2, None),
                  (18, 33, 40, 47, 3, None)],
                 [(30, 20, 41, 30, 1, None), (3, 26, 18, 37, 2, None), (27, 3, 43, 15, 2, None),
                  (21, 33, 44, 46, 3, None)]],
}


DOWNGRADE = {   # premium -> everyday material, used on levels 1-3 (L4-5 keep the premium finish)
    "smooth_quartz_stairs": "polished_diorite_stairs", "smooth_quartz_slab": "smooth_stone_slab",
    "smooth_quartz": "smooth_stone", "quartz_block": "calcite", "quartz_pillar": "calcite",
    "quartz_slab": "diorite_slab", "quartz_stairs": "diorite_stairs", "sea_lantern": "glowstone",
    "polished_blackstone_bricks": "deepslate_bricks", "polished_blackstone_brick_stairs": "deepslate_brick_stairs",
    "polished_blackstone_brick_slab": "deepslate_brick_slab", "polished_blackstone_brick_wall": "deepslate_brick_wall",
    "polished_blackstone_wall": "polished_deepslate_wall", "polished_blackstone_slab": "polished_deepslate_slab",
    "polished_blackstone": "polished_deepslate", "blackstone": "cobbled_deepslate",
    "dark_prismarine_stairs": "deepslate_tile_stairs", "dark_prismarine_slab": "deepslate_tile_slab",
    "dark_prismarine": "deepslate_tiles", "cut_copper_slab": "smooth_stone_slab",
}
DOWNGRADE2 = {"iron_block": "polished_andesite", "redstone_lamp": "glowstone", "end_rod": "lightning_rod",
              "white_glazed_terracotta": "white_terracotta", "cyan_glazed_terracotta": "cyan_terracotta"}


def remap(d, table):
    m = {"minecraft:" + a: "minecraft:" + b for a, b in table.items()}
    for layer in d.bp.grid:
        for row in layer:
            for x, s_ in enumerate(row):
                if s_ == AIR:
                    continue
                name, _, props = s_.partition("[")
                new = m.get(name)
                if new:
                    ok = props and new.endswith(PROPS_OK + ("_wall",)) and name.endswith(PROPS_OK + ("_wall",))
                    row[x] = new + ("[" + props if ok else "")


def premium_cap(d, L):
    import hm as _hm
    if L not in _hm.PREMIUM_CAP:
        return
    remap(d, DOWNGRADE)
    if _hm.premium_share(d.bp, d.gy) > _hm.PREMIUM_CAP[L] * 0.85:
        remap(d, DOWNGRADE2)


def complex_(base, fns):
    t = TYPES.index(base)

    def fn(pack, rel, L):
        d = fns[pack](rel, L)
        regions = []
        for i in range(4):
            if L >= i + 2:
                slot = LAYOUTS[pack][t % 3][i]
                PROJECTS[base][i](d, slot)
                x1, z1, x2, z2 = slot[:4]
                regions.append((x1 - 2, z1 - 2, x2 + 3, z2 + 3, i + 1))
        exterior(d, base, L)
        apply_palette(d, t, regions)
        premium_cap(d, L)
        return d
    return fn


for _b, _f in (("blacksmith", (bs_hearthwood, bs_cascadia, bs_neoterra)),
               ("smeltery", (sm_hearthwood, sm_cascadia, sm_neoterra)),
               ("stonesmeltery", (ss_hearthwood, ss_cascadia, ss_neoterra)),
               ("mechanic", (mc_hearthwood, mc_cascadia, mc_neoterra)),
               ("stonemason", (sn_hearthwood, sn_cascadia, sn_neoterra)),
               ("crusher", (cr_hearthwood, cr_cascadia, cr_neoterra)),
               ("sifter", (sf_hearthwood, sf_cascadia, sf_neoterra))):
    design(_b)(complex_(_b, dict(zip(("Hearthwood", "Cascadia", "Neoterra"), _f))))


# Hand-placed street furniture for each core building (absolute plot coordinates, chosen per type and pack):
#   ("post", x, z) lamp post, ("bench", x, z, facing), ("tree", x, z), ("bed", xa, xb, z) flower bed row,
#   ("shrub", x, z), ("shut", x, z, y, h, facing) a pair of shutters' one leaf, ("crate", x, z), ("cart", x, z)
#   a hand cart; an optional leading int is the first level it appears on.
EXT = {
    "blacksmith": {
        "Hearthwood": [("post", 2, 3), ("bench", 9, 2, "south"), ("bed", 11, 15, 1), ("tree", 21, 2),
                       ("shut", 3, 4, 3, 2, "north"), ("shut", 5, 4, 3, 2, "north"), ("shut", 7, 4, 3, 2, "north"),
                       ("crate", 16, 4), 3, ("tree", 2, 22), 4, ("bench", 6, 15, "south"), 5, ("tree", 13, 22)],
        "Cascadia": [("post", 4, 3), ("post", 14, 3), ("cart", 16, 6), ("tree", 2, 2), ("bed", 6, 8, 1),
                     ("crate", 15, 3), 3, ("tree", 20, 1), 4, ("bench", 8, 21, "north"), 5, ("tree", 2, 20)],
        "Neoterra": [("bed", 3, 8, 1), ("bed", 11, 16, 1), ("post", 2, 2), ("bench", 18, 3, "south"), ("tree", 21, 6),
                     3, ("tree", 21, 16), 4, ("post", 18, 15), 5, ("tree", 9, 20)],
    },
    "smeltery": {
        "Hearthwood": [("post", 9, 3), ("post", 14, 3), ("bed", 15, 19, 1), ("tree", 22, 3), ("crate", 18, 4),
                       3, ("tree", 21, 15), 4, ("bench", 9, 16, "north"), 5, ("tree", 3, 18)],
        "Cascadia": [("post", 12, 3), ("post", 16, 3), ("cart", 9, 3), ("tree", 22, 2), ("bed", 18, 21, 1),
                     3, ("tree", 3, 18), 4, ("bench", 12, 18, "north"), 5, ("tree", 22, 20)],
        "Neoterra": [("bed", 9, 13, 1), ("post", 2, 2), ("tree", 13, 20), ("bench", 9, 2, "south"),
                     3, ("tree", 3, 20), 4, ("post", 21, 3), 5, ("bed", 15, 20, 1)],
    },
    "stonesmeltery": {
        "Hearthwood": [("post", 13, 3), ("bed", 4, 6, 1), ("tree", 22, 4), ("crate", 14, 9), ("bench", 18, 10, "south"),
                       3, ("tree", 2, 16), 4, ("cart", 6, 13), 5, ("tree", 22, 12)],
        "Cascadia": [("post", 2, 4), ("post", 12, 4), ("tree", 22, 3), ("bed", 4, 6, 2), ("cart", 2, 12),
                     3, ("tree", 9, 18), 4, ("bench", 4, 17, "north"), 5, ("tree", 22, 16)],
        "Neoterra": [("bed", 6, 12, 1), ("post", 19, 3), ("bench", 19, 9, "east"), ("tree", 21, 13),
                     3, ("tree", 9, 18), 4, ("post", 2, 16), 5, ("tree", 16, 18)],
    },
    "mechanic": {
        "Hearthwood": [("post", 6, 3), ("post", 12, 3), ("cart", 15, 4), ("tree", 20, 2), ("bed", 1, 3, 1),
                       ("shut", 5, 4, 3, 1, "north"), ("shut", 7, 4, 3, 1, "north"), 3, ("tree", 2, 18),
                       4, ("bench", 7, 17, "north"), 5, ("tree", 15, 18)],
        "Cascadia": [("post", 2, 4), ("post", 21, 4), ("tree", 23, 1), ("crate", 22, 6), ("bed", 9, 12, 1),
                     3, ("tree", 2, 17), 4, ("bench", 8, 17, "north"), 5, ("tree", 16, 18)],
        "Neoterra": [("bed", 8, 14, 1), ("post", 2, 2), ("tree", 19, 3), ("bench", 17, 9, "east"),
                     3, ("tree", 9, 18), 4, ("post", 17, 14), 5, ("tree", 2, 17)],
    },
    "stonemason": {
        "Hearthwood": [("post", 2, 3), ("bed", 9, 12, 1), ("tree", 22, 2), ("bench", 13, 2, "south"),
                       ("shut", 4, 3, 3, 2, "north"), ("shut", 6, 3, 3, 2, "north"), 3, ("tree", 23, 22),
                       4, ("cart", 19, 13), 5, ("tree", 1, 22)],
        "Cascadia": [("post", 2, 6), ("tree", 23, 3), ("bed", 12, 16, 1), ("cart", 18, 7),
                     3, ("tree", 2, 20), 4, ("bench", 10, 19, "north"), 5, ("tree", 18, 20)],
        "Neoterra": [("bed", 10, 15, 1), ("post", 2, 2), ("tree", 19, 3), ("bench", 18, 9, "east"),
                     3, ("tree", 9, 20), 4, ("post", 18, 16), 5, ("tree", 2, 20)],
    },
    "crusher": {
        "Hearthwood": [("post", 6, 3), ("tree", 20, 3), ("bed", 18, 20, 1), ("cart", 1, 6), ("bench", 9, 15, "north"),
                       3, ("tree", 2, 16), 4, ("tree", 9, 21), 5, ("post", 18, 11)],
        "Cascadia": [("post", 4, 3), ("post", 18, 3), ("tree", 22, 1), ("cart", 2, 10), ("bed", 7, 9, 1),
                     3, ("tree", 2, 21), 4, ("bench", 13, 22, "north"), 5, ("tree", 23, 13)],
        "Neoterra": [("bed", 9, 13, 1), ("post", 2, 2), ("bench", 15, 4, "east"), ("tree", 22, 7),
                     3, ("tree", 3, 21), 4, ("post", 20, 18), 5, ("tree", 13, 21)],
    },
    "sifter": {
        "Hearthwood": [("post", 2, 3), ("bed", 7, 10, 1), ("tree", 18, 2), ("bench", 12, 2, "south"),
                       ("cart", 16, 12), 3, ("tree", 2, 18), 4, ("bench", 8, 17, "north"), 5, ("tree", 16, 18)],
        "Cascadia": [("post", 2, 4), ("post", 10, 4), ("tree", 20, 2), ("bed", 12, 15, 1), ("cart", 18, 11),
                     3, ("tree", 2, 17), 4, ("bench", 6, 16, "north"), 5, ("tree", 16, 18)],
        "Neoterra": [("bed", 8, 12, 1), ("post", 2, 2), ("tree", 19, 3), ("bench", 17, 9, "east"),
                     3, ("tree", 9, 17), 4, ("post", 2, 15), 5, ("tree", 16, 17)],
    },
}


def exterior(d, base, L):
    """Place the hand-picked street furniture of this type and pack (each piece only where its spot is open)."""
    P = d.pack
    pave = d.get(0, 1, 0)
    lvl = 1

    def open_at(x, z, h=3):
        return d.bp.inside(x, 2, z) and all(d.air(x, y, z) for y in range(2, 2 + h)) and \
            d.get(x, 1, z) in (pave, "minecraft:grass_block[snowy=false]")
    flowers = {"Hearthwood": ["poppy", "oxeye_daisy", "cornflower", "allium"], "Cascadia": ["fern", "lily_of_the_valley"],
               "Neoterra": ["azalea", "short_grass"]}[P]
    for it in EXT[base][P]:
        if isinstance(it, int):
            lvl = it
            continue
        if L < lvl:
            continue
        k = it[0]
        if k == "post" and open_at(it[1], it[2], 4):
            lamp_post(d, it[1], it[2])
        elif k == "tree" and open_at(it[1], it[2], 6):
            tree(d, it[1], it[2])
        elif k == "bench":
            sx, sz = D4[CW[it[3]]]
            if open_at(it[1], it[2]) and open_at(it[1] + sx, it[2] + sz):
                bench(d, it[1], it[2], it[3])
        elif k == "bed":
            for i, x in enumerate(range(it[1], it[2] + 1)):
                if open_at(x, it[3]):
                    d.set(x, 1, it[3], "moss_block" if P == "Neoterra" else "grass_block[snowy=false]")
                    d.set(x, 2, it[3], flowers[i % len(flowers)])
        elif k == "shrub" and open_at(it[1], it[2]):
            d.set(it[1], 2, it[2], "flowering_azalea" if P == "Hearthwood" else "azalea")
        elif k == "shut":
            x, z, y, h, f = it[1:]
            if all(d.air(x, y + i, z) for i in range(h)):
                for i in range(h):
                    d.set(x, y + i, z, td("spruce_trapdoor" if P == "Hearthwood" else "dark_oak_trapdoor", f, "bottom", True))
        elif k == "crate" and open_at(it[1], it[2]):
            d.set(it[1], 2, it[2], "barrel[facing=up,open=false]")
            d.set(it[1], 3, it[2], "barrel[facing=north,open=false]") if False else None
        elif k == "cart" and open_at(it[1], it[2]) and open_at(it[1] + 1, it[2]):
            w = WOOD[P]
            d.set(it[1], 2, it[2], f"{w}_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
            d.set(it[1] + 1, 2, it[2], f"{w}_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
            d.set(it[1] + 1, 3, it[2], "hay_block[axis=x]" if P != "Neoterra" else "barrel[facing=up,open=false]")
