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
