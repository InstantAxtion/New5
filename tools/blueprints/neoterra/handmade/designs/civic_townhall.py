"""Civic: town hall (hand-designed, all packs).

Round 4: no automatic placement. The building shells (walls, floors, window openings, roofs) come from the local
`shell()` (a copy of _civic_common.bldg without its decoration passes: no sills, shutters, eave brackets, tie-beam
lanterns or ceiling-light grids). Every room, yard and facade detail is drawn below by hand: furniture rooms are
ASCII floor plans stamped at fixed coordinates (`plan()`), lamps / signs / planters are explicit coordinate lists.
"""
from designs._civic_common import (Y0, st, slab, log, flight, framing, clockface, bell, need, keep, new,  # noqa: F401
                                   common_materials, link, wallblock, OUT)
from hm import design, AIR, D4, OPP, CW  # noqa: F401


# ============================================================================================ structural helpers
def shell(d, x1, z1, x2, z2, nf=1, roof="gable", axis="x", win="nesw", ws=3, mat=None, up=None, wh=4,
          gable_end=None, glassy=False, parapet=True, ties=()):
    """Building shell (structure only): plinth, walls per storey with floor slabs and storey bands, corner
    posts / quoins, window openings, roof. `ties` = explicit tie-beam positions (x for an x-ridge, z for a
    z-ridge) under a gable. Returns dict(ys, top, ridge, x1, z1, x2, z2)."""
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
            if m in ("calcite",):
                framing(d, x1, z1, x2, z2, y, y + wh - 1, S["post"], every=3)
    for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):            # corner posts / quoins
        for y in range(Y0, top + 1):
            if d.pack == "Hearthwood":
                if mat == up or y < ys[0] + wh:
                    d.set(x, y, z, ("smooth_stone" if y % 2 else "chiseled_stone_bricks") if mat == "stone_bricks" else
                          ("smooth_stone" if y % 2 else "stone_bricks"))
                else:
                    d.set(x, y, z, log(S["post"]))
            elif d.pack == "Cascadia":
                d.set(x, y, z, log(S["post"]))
            else:
                d.set(x, y, z, "light_gray_concrete")
    sides = {"n": (z1, "x"), "s": (z2, "x"), "w": (x1, "z"), "e": (x2, "z")}   # window openings
    for f, y in enumerate(ys):
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
                    d.set(x, yy, z, S["glass"] if d.pack != "Neoterra" or f == 0 else "light_gray_stained_glass_pane"
                          if glassy else S["glass"])
    ridge = top
    if roof == "gable":
        ridge = d.gable(x1, z1, x2, z2, top + 1, axis, f"{S['roof']}_stairs", f"{S['roof']}_slab",
                        gable_end or (up if d.pack != "Cascadia" else "spruce_planks"), overhang=1)
        ends = ((x1, (z1 + z2) // 2), (x2, (z1 + z2) // 2)) if axis == "x" else (((x1 + x2) // 2, z1), ((x1 + x2) // 2, z2))
        for ex, ez in ends:                                           # king post + gable window
            for yy in range(top + 1, ridge):
                if d.pack == "Hearthwood" and "stairs" not in d.get(ex, yy, ez):
                    d.set(ex, yy, ez, log(S["post"]))
            if ridge - top >= 4:
                d.set(ex, top + 2, ez, S["glass"])
        if d.pack == "Cascadia":                                      # board-and-batten gables
            for yy in range(top + 1, ridge):
                for a in range((x1 if axis == "z" else z1), (x2 if axis == "z" else z2) + 1):
                    for e in ((z1, z2) if axis == "z" else (x1, x2)):
                        x, z = (a, e) if axis == "z" else (e, a)
                        if d.get(x, yy, z) == "minecraft:spruce_planks" and a % 2 == 0:
                            d.set(x, yy, z, log("stripped_spruce_log"))
        for t in ties:                                                # tie beams at the given positions
            if axis == "x":
                for z in range(z1 + 1, z2):
                    d.set(t, top + 1, z, log(S["post"], "z"))
            else:
                for x in range(x1 + 1, x2):
                    d.set(x, top + 1, t, log(S["post"], "x"))
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
        edge = slab("smooth_quartz_slab", "top") if d.pack == "Neoterra" else slab("stone_brick_slab", "top")
        for x in range(x1 - 1, x2 + 2):                               # cantilevered roof edge
            for z in range(z1 - 1, z2 + 2):
                if (x in (x1 - 1, x2 + 1) or z in (z1 - 1, z2 + 1)) and d.air(x, top + 1, z):
                    d.set(x, top + 1, z, edge)
        ridge = top + 1
    return dict(ys=ys, top=top, ridge=ridge, x1=x1, z1=z1, x2=x2, z2=z2)


def edoor(d, x, y, z, facing, wood=None, double=False, along="x"):
    """Exterior door (facing = inside direction); clears the cells in front and behind, step outside.
    No automatic lamps: door lights are placed by hand."""
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


def stairs(d, x, z, y0, yU, rise, rails=(), block=None):
    """Straight flight between storeys; `rails` = the explicit cells (x, z) on the upper floor that get a
    balustrade along the stair hole."""
    block = block or (f"{d.S['wood']}_stairs" if d.pack != "Neoterra" else "smooth_quartz_stairs")
    dx, dz = D4[rise]
    n = yU - y0
    keep(d, x - dx, y0, z - dz, 3)
    lx, lz = flight(d, x, z, y0, yU, rise, block, under=d.S["floor"] if d.pack != "Neoterra" else "smooth_quartz")
    keep(d, lx, yU, lz, 3)
    for i in range(n):
        keep(d, x + dx * i, y0 + i + 1, z + dz * i, 3)
    fence = f"{d.S['wood']}_fence" if d.pack != "Neoterra" else "glass_pane"
    for rx, rz in rails:
        d.set(rx, yU, rz, fence)
    return lx, lz


def chim(d, x, z, y1, y2, mat=None, cap=None):
    """Chimney stack from y1 to y2 with a cap."""
    mat = mat or {"Hearthwood": "bricks", "Cascadia": "cobblestone", "Neoterra": "light_gray_concrete"}[d.pack]
    for y in range(y1, y2 + 1):
        d.set(x, y, z, mat if not (d.pack == "Cascadia" and y % 3 == 0) else "mossy_cobblestone")
    d.set(x, y2 + 1, z, cap or {"Hearthwood": "brick_wall", "Cascadia": "cobblestone_wall", "Neoterra": "iron_bars"}[d.pack])


# ============================================================================================ hand placement
class PlanError(RuntimeError):
    pass


def _put(d, x, y, z, block, te=None):
    """Hand placement into a free cell; raises when the cell is taken (catches plans drawn over walls, doors,
    stairs or door/stair approaches)."""
    here = d.get(x, y, z)
    if here != AIR or ((x, y, z) in d.res and not block.endswith("carpet")):
        raise PlanError(f"{d.pack} L{d.level}: cell ({x},{y},{z}) is not free ({here}) for {block}")
    d.set(x, y, z, block, te)


def plan(d, y, x0, z0, rows, leg):
    """Stamp a hand-drawn floor plan: rows run north->south from z0, characters west->east from x0.
    ' ' and '.' leave the cell alone (walkway); every other character is looked up in `leg`: a block state
    string, or a function f(d, x, y, z) for counted pieces (chairs, beds, work blocks, shelves)."""
    for dz, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch in " .":
                continue
            a = leg[ch]
            x, z = x0 + dx, z0 + dz
            if isinstance(a, str):
                _put(d, x, y, z, a)
            else:
                a(d, x, y, z)


def pts(d, y, cells, block):
    """The same block at an explicit list of (x, z) cells."""
    for x, z in cells:
        _put(d, x, y, z, block)


# legend pieces ------------------------------------------------------------------------------------------------
def CH(back, wood=None, sit=True):
    def f(d, x, y, z):
        if d.get(x, y, z) != AIR:
            raise PlanError(f"chair at ({x},{y},{z}) blocked by {d.get(x, y, z)}")
        d.chair(x, y, z, back, wood or d.S["wood"], sit=sit)
    return f


def OUTSEAT(back, wood=None):
    """Outdoor bench seat (decorative, no tag)."""
    return CH(back, wood, sit=False)


def IT(name, facing=None):
    def f(d, x, y, z):
        if d.get(x, y, z) != AIR:
            raise PlanError(f"{name} at ({x},{y},{z}) blocked by {d.get(x, y, z)}")
        d.item(x, y, z, name, facing)
    return f


def BAR(face, h=2):
    """Required barrels stacked h high (lids facing the aisle)."""
    def f(d, x, y, z):
        for k in range(h):
            if d.get(x, y + k, z) != AIR:
                raise PlanError(f"barrel at ({x},{y + k},{z}) blocked")
            d.item(x, y + k, z, "barrel", face)
    return f


def BK(h=3):
    def f(d, x, y, z):
        for k in range(h):
            if d.get(x, y + k, z) != AIR:
                raise PlanError(f"bookshelf at ({x},{y + k},{z}) blocked by {d.get(x, y + k, z)}")
        d.bookshelf(x, y, z, h)
    return f


def BED(facing, color=None):
    """Bed head cell (the foot goes one cell opposite to `facing`; draw that cell as '.')."""
    def f(d, x, y, z):
        fx, fz = D4[OPP[facing]]
        for cx, cz in ((x, z), (x + fx, z + fz)):
            if d.get(cx, y, cz) != AIR:
                raise PlanError(f"bed at ({cx},{y},{cz}) blocked by {d.get(cx, y, cz)}")
        d.bed(x, y, z, facing, color)
    return f


def STK(*blocks):
    """A stack of blocks from the floor up (cupboards, clocks, statues)."""
    def f(d, x, y, z):
        for k, b in enumerate(blocks):
            if b:
                _put(d, x, y + k, z, b)
    return f


def TD(facing, wood, half="top", open_=False):
    return f"{wood}_trapdoor[facing={facing},half={half},open={'true' if open_ else 'false'},powered=false,waterlogged=false]"


def LANT(hanging=False):
    return f"lantern[hanging={'true' if hanging else 'false'},waterlogged=false]"


def CAN(n=1, color=""):
    c = f"{color}_candle" if color else "candle"
    return f"{c}[candles={n},lit=false,waterlogged=false]"


def hang(d, y, cells, h=4, kind="lantern"):
    """Hanging lanterns under a ceiling at the given cells (y = floor walk layer, ceiling at y+h)."""
    for x, z in cells:
        if kind == "lantern":
            _put(d, x, y + h - 1, z, LANT(True))
        elif kind == "chain":
            _put(d, x, y + h - 1, z, "chain[axis=y,waterlogged=false]")
            _put(d, x, y + h - 2, z, LANT(True))
        else:                                                          # recessed panel in the ceiling
            d.set(x, y + h, z, kind)


def wbanner(d, x, y, z, facing, color):
    _put(d, x, y, z, f"{color}_wall_banner[facing={facing}]")


def wtorch(d, x, y, z, facing):
    _put(d, x, y, z, f"wall_torch[facing={facing}]")


# ============================================================================================ HEARTHWOOD
# Guildhall on a market square: stone ground floor with a clock tower over the door (L1), brick workshop and
# stores wings (L2), plastered & timber-framed upper floor (L3), rear banquet wing + walled garden (L4),
# court house, watch house and an open market house round the square (L5).
def th_hearthwood(rel, L):
    d = new("Hearthwood", rel, (55, 36, 53))
    two = L >= 3
    nf = 2 if two else 1
    shell(d, 20, 14, 32, 22, nf, "gable", "x", win="nesw", ties=(22, 26, 30))
    d.hut(21, Y0, 15)
    keep(d, 22, Y0, 15)
    # entrance / clock tower over the door (stub L1-2, clock & belfry L3+)
    tt = {1: 9, 2: 14}.get(L, 25)
    shell(d, 24, 9, 28, 14, 1, "flat", wh=tt - 1, mat="stone_bricks", up="stone_bricks", win="", parapet=False)
    d.clear(25, Y0, 14, 27, 4, 14)
    edoor(d, 26, Y0, 9, "south")
    d.fill(25, 6, 10, 27, 6, 13, "dark_oak_planks")
    by = tt - 3
    d.fill(25, by, 10, 27, by, 13, "dark_oak_planks")
    for y in range(by + 1, tt):                                     # belfry openings
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
        for x in range(24, 29):                                     # cornice under the clock stage
            d.set(x, by - 6, 8, st("stone_brick_stairs", "south", "top"))
    if L >= 2:
        shell(d, 8, 14, 20, 22, nf, "gable", "x", mat="bricks", up="calcite", ties=(11, 15))
        link(d, 20, Y0, 18, "west")
        chim(d, 8, 16, Y0, 12 if not two else 17)
        edoor(d, 8, Y0, 18, "east")
        shell(d, 32, 14, 44, 22, nf, "gable", "x", mat="bricks", up="calcite", ties=(37, 41))
        link(d, 32, Y0, 18, "east")
        edoor(d, 44, Y0, 18, "west", double=True, along="z")
    if two:
        stairs(d, 22, 21, Y0, 7, "east", rails=[(23, 20), (24, 20), (25, 20), (26, 20)])
        link(d, 20, 7, 18, "east")
        link(d, 32, 7, 18, "east")
    if L >= 4:
        r = shell(d, 20, 22, 32, 35, 2, "gable", "z", mat="bricks", up="calcite", ties=(25, 29))
        link(d, 26, Y0, 22, "south")
        stairs(d, 31, 24, Y0, 7, "south", rails=[(30, 25), (30, 26), (30, 27), (30, 28)])
        chim(d, 32, 30, Y0, r["ridge"] + 1)
        edoor(d, 26, Y0, 35, "north")
    if L >= 5:
        shell(d, 8, 24, 18, 34, 2, "gable", "z", mat="stone_bricks", up="stone_bricks", gable_end="stone_bricks")
        edoor(d, 13, Y0, 24, "south")
        stairs(d, 9, 26, Y0, 7, "south", rails=[(10, 27), (10, 28), (10, 29), (10, 30)])
        shell(d, 34, 24, 44, 34, 2, "gable", "z", mat="bricks", up="calcite")
        edoor(d, 39, Y0, 24, "south")
        stairs(d, 43, 27, Y0, 7, "south", rails=[(42, 28), (42, 29), (42, 30), (42, 31)])
        mx1, mz1, mx2, mz2 = 46, 24, 54, 36                         # market house: open arcade below
        shell(d, mx1, mz1, mx2, mz2, 2, "gable", "z", mat="stone_bricks", up="calcite")
        for x in range(mx1, mx2 + 1):
            for z in range(mz1, mz2 + 1):
                if (x in (mx1, mx2) or z in (mz1, mz2)) and not ((x in (mx1, mx2) and (z - mz1) % 3 == 0) or
                                                                 (z in (mz1, mz2) and (x - mx1) % 4 == 0)):
                    for y in range(Y0, 6):
                        d.set(x, y, z, AIR)
                    d.set(x, 5, z, "stone_brick_slab[type=top,waterlogged=false]")
        stairs(d, 53, 34, Y0, 7, "north", rails=[(52, 33), (52, 32), (52, 31), (52, 30)])
    hw_rooms(d, L)
    return d


def hw_rooms(d, L):
    pass


@design("townhall")
def townhall_v2(pack, rel, L):
    return common_materials({"Hearthwood": th_hearthwood}[pack](rel, L))
