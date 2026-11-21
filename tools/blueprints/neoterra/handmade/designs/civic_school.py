"""Civic: school (hand-designed, all packs).

Round 4: no automatic placement. The building shells (walls, floors, window openings, roofs) come from the local
shell() below (a copy of _civic_common.bldg without any of its dressing passes); every piece of furniture, every
light, every flower box, shutter, lamp post, tree and yard fixture is an explicit placement at a coordinate chosen
for that room – mostly drawn as small ASCII plans (plan()) per room and level.
"""
from designs import _civic_common as _c
globals().update({k: v for k, v in vars(_c).items() if not k.startswith("__")})
from hm import design  # noqa: E402,F401


# ----------------------------------------------------------------------------------------------- local helpers
def shell(d, x1, z1, x2, z2, nf=1, roof="gable", axis="x", win="nesw", ws=3, mat=None, up=None, wh=4,
          gable_end=None, glassy=False, parapet=True, beams=(), edge=True):
    """Bare building shell: floor, walls per storey with floor slabs and storey bands, plinth, corner posts,
    window openings (structural, regular spacing), roof. `beams` = explicit tie-beam positions (x for an x-axis
    gable, z for a z-axis gable) – no lights, sills, shutters or brackets: those are placed by hand."""
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
    for x in range(x1, x2 + 1):                                       # plinth course
        for z in range(z1, z2 + 1):
            if x in (x1, x2) or z in (z1, z2):
                d.set(x, Y0, z, S["base"] if not (d.pack == "Cascadia" and (x * 7 + z) % 5 == 0) else "mossy_cobblestone")
    if d.pack == "Hearthwood":                                        # timber framing on plastered storeys
        for f, y in enumerate(ys):
            m = mat if f == 0 else up
            if m in ("calcite", "yellow_terracotta", "white_terracotta"):
                framing(d, x1, z1, x2, z2, y, y + wh - 1, S["post"], every=3)
    for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):             # corner posts / quoins
        for y in range(Y0, top + 1):
            if d.pack == "Hearthwood":
                if mat == up or y < ys[0] + wh:
                    d.set(x, y, z, "smooth_stone" if y % 2 else "stone_bricks")
                else:
                    d.set(x, y, z, log(S["post"]))
            elif d.pack == "Cascadia":
                d.set(x, y, z, log(S["post"]))
            else:
                d.set(x, y, z, "light_gray_concrete")
    sides = {"n": (z1, "x"), "s": (z2, "x"), "w": (x1, "z"), "e": (x2, "z")}
    for f, y in enumerate(ys):                                        # window openings
        for sd in win:
            line, along = sides[sd]
            a1, a2 = (x1, x2) if along == "x" else (z1, z2)
            if a2 - a1 - 3 < 1:
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
                    d.set(x, yy, z, S["glass"] if d.pack != "Neoterra" or f == 0 else
                          "light_gray_stained_glass_pane" if glassy else S["glass"])
    ridge = top
    if roof == "gable":
        ridge = d.gable(x1, z1, x2, z2, top + 1, axis, f"{S['roof']}_stairs", f"{S['roof']}_slab",
                        gable_end or (up if d.pack != "Cascadia" else "spruce_planks"), overhang=1)
        ends = ((x1, (z1 + z2) // 2), (x2, (z1 + z2) // 2)) if axis == "x" else (((x1 + x2) // 2, z1), ((x1 + x2) // 2, z2))
        for ex, ez in ends:
            for yy in range(top + 1, ridge):
                if d.pack == "Hearthwood" and "stairs" not in d.get(ex, yy, ez):
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
        for b in beams:
            if axis == "x":
                for z in range(z1 + 1, z2):
                    d.set(b, top + 1, z, log(S["post"], "z"))
            else:
                for x in range(x1 + 1, x2):
                    d.set(x, top + 1, b, log(S["post"], "x"))
    elif roof == "hip":
        ridge = d.hip(x1, z1, x2, z2, top + 1, f"{S['roof']}_stairs", f"{S['roof']}_slab", overhang=1)
    else:
        d.fill(x1, top + 1, z1, x2, top + 1, z2, "smooth_quartz" if d.pack == "Neoterra" else S["band"])
        if parapet:
            for x in range(x1, x2 + 1):
                for z in range(z1, z2 + 1):
                    if x in (x1, x2) or z in (z1, z2):
                        d.set(x, top + 2, z, "white_concrete" if d.pack == "Neoterra" else S["base"])
                        d.set(x, top + 3, z, slab("smooth_quartz_slab") if d.pack == "Neoterra" else
                              ("stone_brick_slab[type=bottom,waterlogged=false]" if (x + z) % 2 else "stone_bricks"))
        if edge:
            eb = slab("smooth_quartz_slab", "top") if d.pack == "Neoterra" else slab("stone_brick_slab", "top")
            for x in range(x1 - 1, x2 + 2):                                # cantilevered roof edge
                for z in (z1 - 1, z2 + 1):
                    put(d, x, top + 1, z, eb)
            for z in range(z1, z2 + 1):
                for x in (x1 - 1, x2 + 1):
                    put(d, x, top + 1, z, eb)
        ridge = top + 1
    return dict(ys=ys, top=top, ridge=ridge, x1=x1, z1=z1, x2=x2, z2=z2)


def entry(d, x, y, z, facing, wood=None, double=False, along="x", step=None):
    """Exterior door in a wall (facing = into the room), approach cells cleared and a threshold block outside.
    No automatic lamps – door lights are placed by hand."""
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
        d.set(cx + ox, 1, cz + oz, step or (d.S["base"] if d.pack != "Cascadia" else "spruce_planks"))


def stairs(d, x, z, y0, yU, rise, block=None):
    """Straight flight between storeys (approach and landing reserved). Railings are placed by hand (rails())."""
    block = block or (f"{d.S['wood']}_stairs" if d.pack != "Neoterra" else "smooth_quartz_stairs")
    dx, dz = D4[rise]
    n = yU - y0
    keep(d, x - dx, y0, z - dz, 3)
    lx, lz = flight(d, x, z, y0, yU, rise, block, under=d.S["floor"] if d.pack != "Neoterra" else "smooth_quartz")
    keep(d, lx, yU, lz, 3)
    for i in range(n):
        keep(d, x + dx * i, y0 + i + 1, z + dz * i, 3)
    return lx, lz


def rails(d, y, cells, block=None):
    """Explicit railing / balustrade cells (x, z) at height y."""
    block = block or (f"{d.S['wood']}_fence" if d.pack != "Neoterra" else "glass_pane")
    for x, z in cells:
        d.set(x, y, z, block)


CH = {"n": "north", "s": "south", "e": "east", "w": "west"}


def plan(d, y, x0, z0, rows, legend):
    """Stamp a hand-drawn furniture plan: rows run north->south, characters west->east starting at (x0, z0).
    ' ' and '.' leave the cell as it is. A legend value is a block state or a callable f(d, x, y, z)."""
    for dz, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch in " .":
                continue
            v = legend[ch]
            x, z = x0 + dx, z0 + dz
            if callable(v):
                v(d, x, y, z)
            else:
                d.set(x, y, z, v)


# legend pieces (each draws ONE thing at the given cell)
def seat(back, wood=None):
    return lambda d, x, y, z: d.chair(x, y, z, back, wood or d.S["wood"])


def stool(back, wood=None):
    return lambda d, x, y, z: d.chair(x, y, z, back, wood or d.S["wood"], sit=False)


def shelf(d, x, y, z):
    d.bookshelf(x, y, z)


def work(d, x, y, z):
    d.spot(x, y, z, "work")


def itm(block, facing=None):
    return lambda d, x, y, z: d.item(x, y, z, block, facing)


def tslab(block):
    return slab(block, "top")


def trap(wood, facing, half="top", open_=False):
    return f"{wood}_trapdoor[facing={facing},half={half},open={'true' if open_ else 'false'},powered=false,waterlogged=false]"


def stair(block, facing, half="bottom"):
    return st(block, facing, half)


LANT = "lantern[hanging=true,waterlogged=false]"
LANT_S = "lantern[hanging=false,waterlogged=false]"
CANDLE = "candle[candles=2,lit=false,waterlogged=false]"


def candle(n=1, color=""):
    return f"{color + '_' if color else ''}candle[candles={n},lit=false,waterlogged=false]"


def wbanner(color, facing):
    return f"{color}_wall_banner[facing={facing}]"


def board(d, cells, y, facing, blk="black_concrete", ledge="oak"):
    """Chalkboard on the listed wall-face cells (2 high from y) with a chalk-ledge trapdoor under it."""
    for x, z in cells:
        d.set(x, y, z, blk)
        d.set(x, y + 1, z, blk)
        if ledge:
            d.set(x, y - 1, z, trap(ledge, facing))


def shutters(d, x, y, z, out, wood):
    """Open shutters either side of ONE window (x, y..y+1, z) on the wall facing `out`."""
    ox, oz = D4[out]
    lx, lz = D4[CW[out]]
    for s in (1, -1):
        for yy in (y, y + 1):
            d.set(x + lx * s + ox, yy, z + lz * s + oz, trap(wood, out, "bottom", True))


def window_box(d, x, y, z, out, flower, wood="dark_oak"):
    """Flower box under ONE window: trapdoor sill at y-1 outside the wall, potted flower above it is replaced by a
    little planter of moss + flower (two blocks) hanging on the wall."""
    ox, oz = D4[out]
    d.set(x + ox, y - 1, z + oz, trap(wood, out, "top"))
    d.set(x + ox, y, z + oz, "potted_" + flower)


def ground(d, x1, z1, x2, z2, mat):
    d.fill(x1, 1, z1, x2, 1, z2, mat)


def lamp_post(d, x, z, h=3, base=None, pole=None, top=LANT_S):
    base = base or {"Hearthwood": "stone_brick_wall", "Cascadia": "spruce_log[axis=y]", "Neoterra": "birch_fence"}[d.pack]
    pole = pole or {"Hearthwood": "dark_oak_fence", "Cascadia": "spruce_fence", "Neoterra": "birch_fence"}[d.pack]
    d.set(x, 2, z, base)
    for k in range(1, h):
        d.set(x, 2 + k, z, pole)
    d.set(x, 2 + h, z, top)


def flowers(d, cells, kinds):
    """Explicit flower cells [(x, z), ...] (planted on grass) with the matching flower from `kinds`."""
    for (x, z), f in zip(cells, kinds):
        d.set(x, 1, z, "grass_block[snowy=false]")
        d.set(x, 2, z, f)


def leaves(kind):
    return f"{kind}_leaves[distance=1,persistent=true,waterlogged=false]"
