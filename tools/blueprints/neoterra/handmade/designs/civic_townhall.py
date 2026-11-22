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


def plan(d, y, x0, z0, rows, leg, w=None):
    """Stamp a hand-drawn floor plan: rows run north->south from z0, characters west->east from x0.
    ' ' and '.' leave the cell alone (walkway); every other character is looked up in `leg`: a block state
    string, or a function f(d, x, y, z) for counted pieces (chairs, beds, work blocks, shelves)."""
    for dz, row in enumerate(rows):
        if w is not None and len(row) != w:
            raise PlanError(f"plan row {dz} at ({x0},{y},{z0}) has {len(row)} cells, expected {w}: {row!r}")
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
def CH(back, wood=None, sit=True, arms=False):
    def f(d, x, y, z):
        if d.get(x, y, z) != AIR:
            raise PlanError(f"chair at ({x},{y},{z}) blocked by {d.get(x, y, z)}")
        d.chair(x, y, z, back, wood or d.S["wood"], sit=sit, arms=arms)
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
        stairs(d, 22, 21, Y0, 7, "east", rails=[(22, 21), (23, 20), (24, 20), (25, 20)])
        link(d, 20, 7, 18, "east")
        link(d, 32, 7, 18, "east")
    if L >= 4:
        r = shell(d, 20, 22, 32, 35, 2, "gable", "z", mat="bricks", up="calcite", ties=(25, 29))
        link(d, 26, Y0, 22, "south")
        stairs(d, 31, 24, Y0, 7, "south", rails=[(31, 24), (30, 25), (30, 26), (30, 27)])
        chim(d, 32, 30, Y0, r["ridge"] + 1)
        edoor(d, 26, Y0, 35, "north")
    if L >= 5:
        shell(d, 8, 24, 18, 34, 2, "gable", "z", mat="stone_bricks", up="stone_bricks", gable_end="stone_bricks")
        edoor(d, 13, Y0, 24, "south")
        stairs(d, 9, 26, Y0, 7, "south", rails=[(9, 26), (10, 27), (10, 28), (10, 29)])
        shell(d, 34, 24, 44, 34, 2, "gable", "z", mat="bricks", up="calcite")
        edoor(d, 39, Y0, 24, "south")
        stairs(d, 43, 27, Y0, 7, "south", rails=[(43, 27), (42, 28), (42, 29), (42, 30)])
        mx1, mz1, mx2, mz2 = 46, 24, 54, 36                         # market house: open arcade below
        shell(d, mx1, mz1, mx2, mz2, 2, "gable", "z", mat="stone_bricks", up="calcite")
        for x in range(mx1, mx2 + 1):
            for z in range(mz1, mz2 + 1):
                if (x in (mx1, mx2) or z in (mz1, mz2)) and not ((x in (mx1, mx2) and (z - mz1) % 3 == 0) or
                                                                 (z in (mz1, mz2) and (x - mx1) % 4 == 0)):
                    for y in range(Y0, 6):
                        d.set(x, y, z, AIR)
                    d.set(x, 5, z, "stone_brick_slab[type=top,waterlogged=false]")
        stairs(d, 53, 34, Y0, 7, "north", rails=[(53, 34), (52, 33), (52, 32), (52, 31)])
    hw_rooms(d, L)
    return d


def base_leg(d, wood=None, chest="south", barrel="south", plant=None):
    """Legend shared by the hand-drawn plans of one pack (chairs: the arrow points at the backrest side)."""
    wood = wood or d.S["wood"]
    top = {"Hearthwood": "dark_oak_planks", "Cascadia": "stripped_spruce_wood[axis=y]", "Neoterra": "smooth_quartz"}[d.pack]
    sl = slab("smooth_quartz_slab", "top") if d.pack == "Neoterra" else slab(f"{wood}_slab", "top")
    return {
        "^": CH("north", wood), "v": CH("south", wood), "<": CH("west", wood), ">": CH("east", wood),
        "T": top, "_": sl, "B": BK(3), "b": BK(2), "1": BK(1), "K": BAR(barrel),
        "c": f"chest[facing={chest},type=single,waterlogged=false]", "L": LANT(),
        "p": plant or d.P["plant"], "r": "red_carpet", "y": "yellow_carpet", "g": "green_carpet",
        "u": "blue_carpet", "k": "brown_carpet", "a": "cyan_carpet", "i": "light_gray_carpet",
        "q": "white_carpet", "o": "orange_carpet", "m": "lime_carpet",
    }


def hw_rooms(d, L):
    two = L >= 3
    W = "dark_oak"
    leg = base_leg(d, W, plant="potted_red_tulip")
    # ---------------------------------------------------------------- vestibule in the clock tower
    plan(d, Y0, 25, 10, [
        ">r<",  # benches either side of the runner
        ".r.",
        ".r.",
        "prp",
    ], leg | {">": CH("west", W, sit=False), "<": CH("east", W, sit=False)})
    d.sign(25, 4, 11, "east", ["Notices", "", "Market day:", "Saturday"], W)
    d.sign(27, 4, 11, "west", ["Mind the", "step"], W)
    hang(d, Y0, [(26, 12)])
    # ---------------------------------------------------------------- guildhall (core ground floor)
    lg = leg | {"C": IT("crafting_table"), "F": IT("furnace", "east"), "K": BAR("west"),
                "Z": BED("east"), "c": "chest[facing=west,type=single,waterlogged=false]"}
    south = "..vv......Z" if L <= 2 else ("." + "     " + "...cp")
    plan(d, Y0, 21, 15, [
        " ._..r...KK",          # clerk's desk beside the hut, record barrels in the NE corner
        "C.v..r.^^..",          # workbench on the west wall, council table east of the aisle
        "_....r.TT>.",
        ".....r.TT>.",
        "F....r.vv..",          # stove pair on the west wall
        "F....r...." + ("_" if L <= 2 else "."),
        south,                  # L1-2: settle and the caretaker's cot; L3+: the stair to the council floor
    ], lg)
    pts(d, Y0 + 1, [(23, 15)], CAN(2))
    pts(d, Y0 + 1, [(21, 17), (29, 18)], "flower_pot")
    pts(d, Y0 + 1, [(28, 17)], CAN(3))
    if L <= 2:
        pts(d, Y0 + 1, [(31, 20)], CAN(1))
    if L >= 4:
        pts(d, Y0, [(26, 21)], "red_carpet")
    wbanner(d, 21, 4, 17, "east", "red")
    wbanner(d, 31, 4, 17, "west", "yellow")
    hang(d, Y0, [(22, 18), (26, 16), (30, 18)])
    # ---------------------------------------------------------------- forecourt (street side)
    for x in range(14, 39):
        for z in range(1, 9):
            d.set(x, 1, z, "polished_andesite" if 25 <= x <= 27 or z in (1, 8) else "stone_bricks")
    for x, z in ((21, 7), (31, 7)):                                    # lamp posts either side of the walk
        lamppost_hw(d, x, z)
    for x0 in (20, 29):                                              # flower borders under the front windows
        d.fill(x0, 1, 12, x0 + 3, 1, 13, "grass_block[snowy=false]")
        plan(d, Y0, x0, 12, ["fdfa", "afdf"], {"f": "red_tulip", "d": "oxeye_daisy", "a": "allium"})
    wtorch(d, 25, 4, 8, "north")
    wtorch(d, 27, 4, 8, "north")
    d.sign(26, 5, 8, "north", ["TOWN", "HALL"], W)
    d.banner(25, 6, 8, "north", "red")
    d.banner(27, 6, 8, "north", "red")
    if L >= 2:
        hw_wings(d, L, leg)
    if two:
        hw_upper(d, L, leg)
    if L >= 4:
        hw_rear(d, L, leg)
    if L >= 5:
        hw_square(d, L, leg)
    if L >= 2:
        hw_eaves(d, L)


def hw_eaves(d, L):
    """The one-block strip under the wing eaves, dressed by hand: flower borders under the street windows,
    benches against the back walls, firewood at the chimney, water butts, crates at the store's loading door
    and wall torches beside the side doors."""
    W = "dark_oak"
    for x0, row in ((9, "fdaf"), (15, "afdf"), (34, "fdaf"), (40, "afdf")):      # street front of both wings
        d.fill(x0, 1, 13, x0 + 3, 1, 13, "grass_block[snowy=false]")
        plan(d, Y0, x0, 13, [row], {"f": "red_tulip", "d": "oxeye_daisy", "a": "allium"})
    for z in (14, 15):                                                # log stack against the workshop chimney
        pts(d, Y0, [(7, z)], log("dark_oak_log", "x"))
        pts(d, Y0 + 1, [(7, z)], log("dark_oak_log", "x"))
    pts(d, Y0, [(7, 21)], "water_cauldron[level=3]")
    pts(d, Y0, [(45, 15), (45, 16)], "barrel[facing=up,open=false]")      # crates by the loading door
    pts(d, Y0, [(45, 21)], "chest[facing=west,type=single,waterlogged=false]")
    wtorch(d, 45, 4, 17, "east")
    wtorch(d, 45, 4, 20, "east")
    for xs in ((9, 10), (41, 42)):                                    # benches on the garden side (clear of L5 doors)
        plan(d, Y0, xs[0], 23, ["vv"], {"v": OUTSEAT("north", W)})
        pts(d, Y0, [(xs[0] - 1, 23), (xs[1] + 1, 23)], "potted_red_tulip")
    pts(d, Y0, [(16, 23)], "water_cauldron[level=3]")
    pts(d, Y0, [(36, 23)], "composter[level=0]")
    if L <= 3:                                                        # behind the core before the rear hall
        wtorch(d, 24, 4, 23, "south")
        wtorch(d, 28, 4, 23, "south")
        pts(d, Y0, [(26, 23)], "potted_cornflower")
    if L >= 4:                                                        # along the rear hall's side walls
        wtorch(d, 19, 4, 26, "west")
        wtorch(d, 19, 4, 33, "west")
        wtorch(d, 33, 4, 26, "east")
        wtorch(d, 33, 4, 33, "east")
        for z in (31, 32):                                            # firewood for the banquet-hall hearth
            pts(d, Y0, [(33, z)], log("dark_oak_log", "z"))
            pts(d, Y0 + 1, [(33, z)], log("dark_oak_log", "z"))
    if L == 4:                                                        # still open yard on both sides
        plan(d, Y0, 19, 28, ["v", "v"], {"v": OUTSEAT("east", W)})
        pts(d, Y0, [(19, 27), (19, 30)], "potted_azure_bluet")
        plan(d, Y0, 33, 27, ["v", "v"], {"v": OUTSEAT("west", W)})


def lamppost_hw(d, x, z):
    pts(d, Y0, [(x, z)], "stone_brick_wall")
    pts(d, Y0 + 1, [(x, z)], "dark_oak_fence")
    pts(d, Y0 + 2, [(x, z)], "dark_oak_fence")
    pts(d, Y0 + 3, [(x, z)], LANT())


def hw_wings(d, L, leg):
    W = "dark_oak"
    # ---------------------------------------------------------------- guild workshop (west wing)
    lg = leg | {"S": IT("blast_furnace", "south"), "M": IT("smithing_table"), "C": IT("crafting_table"),
                "O": IT("stonecutter", "south"), "X": IT("fletching_table"), "P": IT("cartography_table"),
                "N": IT("loom", "south"), "A": IT("anvil", "south"), "G": IT("grindstone", "east"),
                "H": IT("smoker", "north"), "F": IT("furnace", "north"), "R": IT("brewing_stand"),
                "Q": IT("water_cauldron[level=3]"), "h": "hay_block[axis=y]", "w": "white_wool"}
    plan(d, Y0, 9, 15, [
        "SM.COX.PN..",          # smith's corner by the chimney, then the bench row under the north windows
        "A..........",
        ("A" if L >= 3 else ".") + "..____....",   # carpenters' bench island
        "...........",          # through aisle door to door
        "G..........",
        ("G" if L >= 3 else ".") + ".......hh",
        ".HF.RQ...ww",          # cook & apothecary side, wool bales for the loom
    ], lg)
    pts(d, Y0 + 1, [(12, 17)], CAN(2))
    pts(d, Y0 + 1, [(14, 17)], "flower_pot")
    pts(d, Y0 + 1, [(18, 20)], "hay_block[axis=y]")
    hang(d, Y0, [(11, 18), (15, 18)])
    d.sign(14, 5, 13, "north", ["Guild", "Workshop"], W)
    wtorch(d, 7, 4, 17, "west")
    # ---------------------------------------------------------------- stores (east wing)
    nb = need(d, "barrel") - 4
    stacks = (nb + 1) // 2
    north = {5: ".KKKKK.hhc.", 9: ".KKKKKKKKK."}[stacks]           # barrel shelving on the north wall
    lg = leg | {"K": BAR("south"), "h": "hay_block[axis=y]", "e": "barrel[facing=north,open=false]",
                "c": "chest[facing=south,type=single,waterlogged=false]", "s": "chest[facing=north,type=single,waterlogged=false]",
                "C": "composter[level=8]", "w": "brown_wool", "<": CH("west", W, sit=False)}
    plan(d, Y0, 33, 15, [
        north,
        "...........",
        "...........",
        "...........",
        "...........",
        "...........",
        "ssee.hww.C.",
    ], lg)
    plan(d, Y0, 42, 16, ["<_"], leg | {"<": CH("west", W)})          # store clerk at the door
    pts(d, Y0 + 1, [(43, 16)], CAN(1))
    pts(d, Y0 + 1, [(38, 21)], "brown_wool")
    hang(d, Y0, [(37, 18), (41, 18)])
    d.sign(38, 5, 13, "north", ["Town", "Stores"], W)
    d.fill(45, 1, 18, 52, 1, 19, "gravel")                              # cart track to the loading doors
    plan(d, Y0, 47, 15, ["f", "_", "_"], {"f": "dark_oak_fence", "_": slab("spruce_slab", "top")})
    pts(d, Y0 + 1, [(47, 17)], "hay_block[axis=y]")
    pts(d, Y0, [(47, 21)], "hay_block[axis=y]")
    pts(d, Y0, [(46, 21)], "barrel[facing=up,open=false]")


def hw_upper(d, L, leg):
    W = "dark_oak"
    y = 7
    # ---------------------------------------------------------------- archive (west upper)
    plan(d, y, 9, 15, [
        "B1BB1BB1BBB",
        "B..........",
        "B.^^^...E..",
        "B.TTT...ggg",
        "1.vvv......",
        "B...^..^...",
        "B..._.._...",
    ], leg | {"E": IT("enchanting_table")})
    pts(d, y + 1, [(10 + 2, 18)], CAN(3))
    pts(d, y + 1, [(13, 21), (16, 21)], CAN(1))
    hang(d, y, [(11, 18), (15, 18)])
    # ---------------------------------------------------------------- council chamber (core upper)
    plan(d, y, 21, 15, [
        "p.........I",
        "..^^^^^^...",
        "..TTTTTT<..",
        "..vvvvvv...",
        ".rrrrrrrrr.",
        "  .   .....",
        " .......c..",
    ], leg | {"I": IT("lectern", "west"), "<": CH("east", W, arms=True)})
    pts(d, y + 1, [(24, 17), (27, 17)], CAN(3))
    pts(d, y + 1, [(26, 17)], "flower_pot")
    wbanner(d, 24, 9, 15, "south", "red")
    wbanner(d, 27, 9, 15, "south", "yellow")
    hang(d, y, [(26, 17), (22, 19), (30, 19)])
    # ---------------------------------------------------------------- officials' quarters (east upper)
    plan(d, y, 33, 15, [
        ".H_H_H_H_H.",
        "...........",
        "...........",
        "...rrrrr...",
        "...........",
        ".....^.....",
        "c.u.._...uc",
    ], leg | {"H": BED("north"), "c": "chest[facing=north,type=single,waterlogged=false]",
              "u": "cauldron", "E": IT("ender_chest", "west")})
    pts(d, y + 1, [(38, 21)], CAN(2))
    for x in (35, 37, 39, 41):
        pts(d, y + 1, [(x, 15)], CAN(1))
    hang(d, y, [(37, 18), (41, 18)])
    # front window boxes on the upper storey
    for x in (22, 10, 16, 34, 40):
        pts(d, y, [(x, 13)], TD("north", "dark_oak"))
        pts(d, y + 1, [(x, 13)], "potted_red_tulip" if x % 4 else "potted_cornflower")


def hw_rear(d, L, leg):
    W = "dark_oak"
    # ---------------------------------------------------------------- banquet hall + kitchen (rear ground)
    lg = leg | {"J": IT("jukebox"), "F": "furnace[facing=east,lit=false]", "M": "smoker[facing=east,lit=false]",
                "Q": "water_cauldron[level=3]", "e": "barrel[facing=east,open=false]", "C": "composter[level=0]",
                "h": "hay_block[axis=y]", "x": "bricks"}
    plan(d, Y0, 21, 23, [
        "J......... ",
        "p..^...^.. ",          # head chairs
        "..<T>.<T>. ",          # two refectory tables either side of the aisle
        "..<T>.<T>. ",
        "..<T>.<T>. ",
        "..<T>.<T>. ",
        "..<T>.<T>.x",
        "...v...v...",          # fireplace on the east wall (x31)
        "F____.____x",          # serving counter between hall and kitchen
        "M..........",
        "Q..TT......",          # kitchen table
        "ec___.___Ch",
    ], lg)
    pts(d, Y0, [(31, 30)], "campfire[facing=west,lit=true,signal_fire=false,waterlogged=false]")
    pts(d, Y0 + 1, [(31, 29), (31, 30), (31, 31)], "bricks")
    for yy in (4, 5):
        pts(d, yy, [(31, 30)], "bricks")
    d.set(31, 6, 30, "bricks")
    pts(d, Y0 + 1, [(23, 31)], "cake[bites=0]")
    pts(d, Y0 + 1, [(28, 31), (24, 33)], "flower_pot")
    pts(d, Y0 + 1, [(24, 27), (28, 27)], CAN(3))
    pts(d, Y0 + 1, [(23, 34)], CAN(1))
    wbanner(d, 21, 4, 28, "east", "red")
    hang(d, Y0, [(24, 25), (28, 25), (24, 29), (28, 29), (26, 33)])
    # ---------------------------------------------------------------- mayor's apartment (rear upper)
    y = 7
    for x in range(21, 31):                                          # partition office | bedroom
        for yy in range(y, y + 4):
            d.set(x, yy, 28, "dark_oak_planks" if x in (21, 25, 27, 30) else "calcite")
    link(d, 26, y, 28, "south")
    plan(d, y, 21, 23, [
        "bbb.....  ",
        "....^.... ",
        "E..___...",
        "...v.v...",
        "pp.......",
    ], leg | {"E": IT("ender_chest", "east")})
    pts(d, y + 1, [(24, 25)], CAN(2))
    pts(d, y + 1, [(26, 25)], "flower_pot")
    plan(d, y, 21, 29, [
        "..........",
        "c........ ",
        "c...rrrr..",
        "..<T.rr...",
        "...r..r...",
        "u.._HH_..p",
    ], leg | {"c": "chest[facing=east,type=single,waterlogged=false]", "u": "cauldron",
              "H": BED("south"), "<": CH("west", W, sit=False)})
    pts(d, y + 1, [(24, 34), (27, 34)], CAN(1))
    pts(d, y + 1, [(24, 32)], "potted_azure_bluet")
    hang(d, y, [(25, 25), (23, 29), (28, 29)])
    # ---------------------------------------------------------------- walled garden with bandstand
    d.fill(8, 1, 36, 46, 1, 51, "grass_block[snowy=false]")
    d.fill(25, 1, 35, 27, 1, 50, "gravel")
    for x in range(8, 47):
        d.set(x, Y0, 51, "brick_wall")
    for z in range(36, 51):
        d.set(8, Y0, z, "brick_wall")
        d.set(46, Y0, z, "brick_wall")
    bx, bz = 26, 43
    for x in range(bx - 3, bx + 4):
        for z in range(bz - 3, bz + 4):
            if abs(x - bx) + abs(z - bz) <= 4:
                d.set(x, 1, z, "stone_bricks")
    for x, z in ((bx - 2, bz - 2), (bx + 2, bz - 2), (bx - 2, bz + 2), (bx + 2, bz + 2)):
        for yy in range(Y0, 6):
            d.set(x, yy, z, "dark_oak_fence")
    d.hip(bx - 2, bz - 2, bx + 2, bz + 2, 6, "deepslate_tile_stairs", "deepslate_tile_slab", overhang=1)
    plan(d, Y0, 25, 44, ["n.n"], {"n": "note_block[instrument=harp,note=0,powered=false]"})
    for x, z in ((12, 40), (40, 40), (12, 48), (40, 48)):
        oak(d, x, z)
    beds = {(15, 37): "ftdcfa", (31, 37): "adftcd", (10, 49): "fdcafdcfadcf", (30, 49): "cfadfdcafdcfadf"}
    for (x0, z0), row in beds.items():
        d.fill(x0, 1, z0, x0 + len(row) - 1, 1, z0 + 1, "grass_block[snowy=false]")
        plan(d, Y0, x0, z0, [row, row[::-1]], {"f": "red_tulip", "t": "oxeye_daisy", "d": "cornflower",
                                              "c": "allium", "a": "azure_bluet"})
    for x, z in ((24, 38), (28, 38), (24, 48), (28, 48)):
        lamppost_hw(d, x, z)
    plan(d, Y0, 18, 43, ["vv"], {"v": OUTSEAT("south", W)})
    plan(d, Y0, 33, 43, ["vv"], {"v": OUTSEAT("south", W)})
    wtorch(d, 24, 4, 36, "south")
    wtorch(d, 27, 4, 36, "south")


def oak(d, x, z, logb="oak_log", leaves="oak_leaves", h=5):
    """One hand-placed tree (trunk + crown) at (x, z)."""
    d.set(x, 1, z, "grass_block[snowy=false]")
    for k in range(h):
        d.set(x, Y0 + k, z, log(logb))
    lv = f"{leaves}[distance=1,persistent=true,waterlogged=false]"
    for dy, r in ((h - 2, 2), (h - 1, 2), (h, 1), (h + 1, 0)):
        for a in range(-r, r + 1):
            for b in range(-r, r + 1):
                if abs(a) + abs(b) <= r + 1 - (dy == h + 1) and d.air(x + a, Y0 + dy, z + b):
                    d.set(x + a, Y0 + dy, z + b, lv)


def stall_hw(d, x, z, color, goods):
    """Market stall: fence posts, striped awning, counter with goods, a crate behind."""
    for dx in (0, 2):
        for yy in (2, 3, 4):
            _put(d, x + dx, yy, z, "dark_oak_fence")
            _put(d, x + dx, yy, z + 2, "dark_oak_fence")
    for dx in range(3):
        for dz in range(3):
            _put(d, x + dx, 5, z + dz, f"{color}_wool" if dx != 1 else "white_wool")
    _put(d, x + 1, 2, z, slab("dark_oak_slab", "top"))
    _put(d, x + 1, 3, z, goods)
    _put(d, x + 1, 2, z + 2, "barrel[facing=up,open=false]")


def hw_square(d, L, leg):
    W = "dark_oak"
    # ---------------------------------------------------------------- market square: fountain and stalls
    for x in range(24, 29):
        for z in range(2, 7):
            ring = x in (24, 28) or z in (2, 6)
            d.set(x, 1, z, "stone_bricks")
            d.set(x, Y0, z, "stone_brick_wall" if ring else "water[level=0]")
    d.set(26, Y0, 4, "chiseled_stone_bricks")
    d.set(26, Y0 + 1, 4, "stone_brick_wall")
    d.set(26, Y0 + 2, 4, LANT())
    stall_hw(d, 15, 2, "red", "melon")
    stall_hw(d, 35, 2, "blue", "pumpkin")
    stall_hw(d, 10, 5, "yellow", "hay_block[axis=y]")
    stall_hw(d, 40, 5, "green", "carved_pumpkin[facing=north]")
    # ---------------------------------------------------------------- court house
    plan(d, Y0, 9, 25, [
        ".....p...",
        " ........",
        " .^^.^^.>",          # public benches, jury box on the east wall
        " ........",
        " .^^.^^.>",
        " .......>",
        "...___..>",          # judge's bench
        "....v....",
        "..r...r..",
    ], leg)
    pts(d, Y0 + 1, [(12, 31)], CAN(2))
    pts(d, Y0 + 1, [(14, 31)], "flower_pot")
    wbanner(d, 11, 4, 33, "north", "red")
    wbanner(d, 15, 4, 33, "north", "red")
    hang(d, Y0, [(13, 27), (13, 30)])
    plan(d, 7, 9, 25, [
        "......bbb",          # judges' chambers and law library
        " .......b",
        " ...T...b",
        " ..<T>..b",
        " ...T...b",
        "........b",
        ".c......",
        "...^....",
        "...__..p",
    ], leg | {"c": "chest[facing=east,type=single,waterlogged=false]"})
    pts(d, 8, [(12, 33)], CAN(2))
    pts(d, 8, [(13, 28)], CAN(3))
    hang(d, 7, [(13, 28), (14, 32)], h=4)
    d.sign(13, 5, 23, "north", ["COURT", "HOUSE"], W)
    wtorch(d, 12, 4, 23, "north")
    wtorch(d, 14, 4, 23, "north")
    # ---------------------------------------------------------------- watch house: guard room and two cells
    plan(d, Y0, 35, 25, [
        "c.p......",
        "..^^.....",
        ".<TT>....",
        "..vv.....",
        "........ ",
        "bbIbbbIb ",          # cell front: iron bars and iron doors
        "h..u.h.u ",
        "........ ",
        ".........",
    ], leg | {"b": "iron_bars", "I": "iron_door[facing=south,half=lower,hinge=left,open=false,powered=false]",
              "h": "hay_block[axis=y]", "u": "cauldron", "c": "chest[facing=south,type=single,waterlogged=false]"})
    for x in (37, 41):
        d.set(x, Y0 + 1, 30, "iron_door[facing=south,half=upper,hinge=left,open=false,powered=false]")
    for x in range(35, 43):
        if x not in (37, 41):
            for yy in (Y0 + 1, Y0 + 2):
                d.set(x, yy, 30, "iron_bars")
    for z in range(31, 34):                                           # partition between the cells
        for yy in (Y0, Y0 + 1, Y0 + 2):
            d.set(39, yy, z, "iron_bars")
    pts(d, Y0 + 1, [(37, 27)], CAN(2))
    hang(d, Y0, [(37, 27), (39, 31)])
    plan(d, 7, 35, 25, [
        "HcHcHcH..",          # barrack room: bunks along the north wall
        ".........",
        "........ ",
        "...^.... ",
        "..<T>... ",
        "...v.... ",
        "........ ",
        ".........",
        ".c.c..p..",
    ], leg | {"H": BED("north"), "c": "chest[facing=north,type=single,waterlogged=false]"})
    hang(d, 7, [(38, 29)])
    d.sign(39, 5, 23, "north", ["WATCH", "HOUSE"], W)
    wtorch(d, 38, 4, 23, "north")
    wtorch(d, 40, 4, 23, "north")
    # ---------------------------------------------------------------- market house: open arcade + corn exchange
    for x, z, col, good in ((48, 27, "red", "melon"), (51, 27, "yellow", "pumpkin"),
                            (48, 31, "green", "hay_block[axis=y]"), (51, 31, "blue", "carved_pumpkin[facing=north]")):
        _put(d, x, Y0, z, slab("dark_oak_slab", "top"))
        _put(d, x + 1, Y0, z, f"{col}_wool")
        _put(d, x, Y0 + 1, z, good)
    hang(d, Y0, [(50, 29), (50, 33)])
    plan(d, 7, 47, 25, [
        "hh.....",
        "h......",
        "..^^^..",
        ".<TTT>.",
        "..vvv..",
        ".......",
        "e......",
        "e.... ",
        "c.... ",
        "...... ",
        "u..... ",
    ], leg | {"h": "hay_block[axis=y]", "e": "barrel[facing=east,open=false]", "u": "cauldron",
              "c": "chest[facing=east,type=single,waterlogged=false]"})
    pts(d, 8, [(49, 28)], CAN(3))
    hang(d, 7, [(50, 28), (50, 32)])
    d.sign(50, 6, 23, "north", ["MARKET", "HOUSE"], W)


# ============================================================================================ NEOTERRA
# Civic centre: glass-fronted council pavilion with a canopy on a paved plaza (L1), maker space and stores
# wings with a clock fin (L2), council chamber / archive / guest rooms upstairs and roof gardens (L3),
# a three-storey rear block with canteen, offices and study + fountain plaza (L4), and a six-storey city
# office tower with its own floors of hand-furnished rooms (L5).
def th_neoterra(rel, L):
    d = new("Neoterra", rel, (53, 45, 49), paving="smooth_stone")
    Q = "smooth_quartz"
    two = L >= 3
    nf = 2 if two else 1
    c = shell(d, 18, 12, 32, 22, nf, "flat", glassy=True, win="nesw")
    edoor(d, 24, Y0, 12, "south", double=True)
    d.hut(19, Y0, 13)
    keep(d, 20, Y0, 13)
    for x in range(21, 30):                                         # entrance canopy
        for z in range(8, 12):
            d.set(x, 6, z, slab("smooth_quartz_slab", "top"))
    for x in (21, 29):
        for yy in range(Y0, 6):
            d.set(x, yy, 8, "quartz_pillar[axis=y]" if L >= 4 else "white_concrete")
    d.sign(25, 7, 11, "north", ["CIVIC", "CENTRE"], "birch", glow=True, color="cyan") if two else \
        d.sign(25, 6, 7, "north", ["CIVIC", "CENTRE"], "birch", glow=True, color="cyan")
    ws = es = None
    if L >= 2:
        ws = shell(d, 6, 12, 18, 22, nf, "flat", glassy=True, win="nsw")
        link(d, 18, Y0, 17, "west")
        edoor(d, 6, Y0, 17, "east")
        d.sign(12, 6, 11, "north", ["MAKER", "SPACE"], "birch", glow=True, color="orange")
        es = shell(d, 32, 12, 44, 22, nf, "flat", glassy=False, win="ns")
        link(d, 32, Y0, 17, "east")
        edoor(d, 44, Y0, 17, "west", double=True, along="z")
        ft = 17 if L == 2 else 28                                   # clock fin with bell frame
        d.fill(46, Y0, 7, 48, ft, 9, "white_concrete")
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
        stairs(d, 20, 21, Y0, 7, "east", rails=[(20, 21), (21, 20), (22, 20), (23, 20)])
        link(d, 18, 7, 17, "east")
        link(d, 32, 7, 17, "east")
    r = tw = None
    if L >= 4:
        r = shell(d, 18, 22, 32, 34, 3, "flat", glassy=True, win="esw")
        link(d, 25, Y0, 22, "south")
        stairs(d, 31, 24, Y0, 7, "south", rails=[(31, 24), (30, 25), (30, 26), (30, 27)])
        stairs(d, 19, 32, 7, 12, "north", rails=[(19, 32), (20, 31), (20, 30), (20, 29)])
    if L >= 5:
        tw = shell(d, 34, 24, 46, 40, 6, "flat", glassy=True, win="nsew")
        edoor(d, 40, Y0, 40, "north", double=True)
        for k in range(5):
            y0 = Y0 + 5 * k
            if k % 2 == 0:
                stairs(d, 35, 25, y0, y0 + 5, "south", rails=[(35, 25), (36, 26), (36, 27), (36, 28)])
            else:
                stairs(d, 45, 39, y0, y0 + 5, "north", rails=[(45, 39), (44, 38), (44, 37), (44, 36)])
        d.sign(40, 6, 41, "south", ["CITY", "OFFICES"], "birch", glow=True, color="cyan")
    nt_rooms(d, L, dict(c=c, ws=ws, es=es, r=r, tw=tw))
    return d


def lamppost_nt(d, x, z):
    pts(d, Y0, [(x, z)], "light_gray_concrete")
    pts(d, Y0 + 1, [(x, z)], "birch_fence")
    pts(d, Y0 + 2, [(x, z)], "birch_fence")
    pts(d, Y0 + 3, [(x, z)], "sea_lantern")


def nt_rooms(d, L, B):
    W = "birch"
    leg = base_leg(d, W, plant="potted_bamboo") | {"G": STK(*(["light_gray_stained_glass_pane"] * 3)),
                                                  "s": "light_gray_shulker_box[facing=up]",
                                                  "u": "water_cauldron[level=3]", "z": "flowering_azalea",
                                                  "M": "moss_block", "S": "daylight_detector[inverted=false,power=0]",
                                                  "e": "end_rod[facing=up]"}
    sl = lambda y: y + 4                                             # noqa: E731
    # ---------------------------------------------------------------- lobby (core ground)
    lg = leg | {"K": BAR("east"), "C": IT("crafting_table"), "F": IT("furnace", "east"), "Z": BED("east", "cyan"),
                "N": "white_concrete"}
    plan(d, Y0, 19, 13, [
        " ._.........p",        # reception counter beside the hut block, staff seat behind it
        "p<_..........",
        "K._.....^^...",        # file barrels on the west wall; meeting table for four
        "K......<TT>..",
        ".......<TT>..",
        "C.......vv...",        # staff kitchenette: workbench + two ovens
        "F.._.........",        # coffee table in front of the waiting sofa
        "F.vvv.......N",
        ("p...........Z" if L <= 2 else "." + "     " + "......Z"),   # night porter's bed (SE)
    ], lg, w=13)
    pts(d, Y0 + 1, [(21, 13)], "end_rod[facing=up]")
    pts(d, Y0 + 1, [(22, 19), (28, 16)], "potted_bamboo")
    pts(d, Y0 + 1, [(31, 20)], LANT())
    hang(d, Y0, [(22, 15), (27, 16), (24, 19), (29, 20)], kind="glowstone" if L >= 3 else "sea_lantern")
    # ---------------------------------------------------------------- plaza
    for x in range(10, 41):
        for z in range(1, 11):
            d.set(x, 1, z, "polished_diorite" if z in (3, 7) or 24 <= x <= 25 else "smooth_stone")
    lamppost_nt(d, 20, 4)
    lamppost_nt(d, 30, 4)
    for x in (16, 34):
        pts(d, Y0, [(x, 9)], "moss_block")
        pts(d, Y0 + 1, [(x, 9)], "flowering_azalea")
    if L >= 2:
        nt_wings(d, L, leg)
    if L >= 3:
        nt_upper(d, L, leg)
    if L >= 4:
        nt_rear(d, L, leg)
    if L >= 5:
        nt_tower(d, L, leg)


def nt_wings(d, L, leg):
    # ---------------------------------------------------------------- maker space (west wing)
    lg = leg | {"S": IT("blast_furnace", "south"), "C": IT("crafting_table"), "O": IT("stonecutter", "south"),
                "X": IT("fletching_table"), "P": IT("cartography_table"), "N": IT("loom", "south"),
                "Y": IT("smithing_table"), "A": IT("anvil", "east"), "R": IT("grindstone", "east"),
                "H": IT("smoker", "north"), "F": IT("furnace", "north"), "V": IT("brewing_stand"),
                "Q": IT("water_cauldron[level=3]"), "w": "white_wool", "j": "cyan_wool"}
    plan(d, Y0, 7, 13, [
        "S.COX.PN..j",          # bench wall: cutter, fletching, plotter (cartography), loom
        "Y..........",
        "A..______..",          # assembly island
        ("A" if L >= 3 else ".") + "...v.v....",
        "...........",          # aisle door to door
        "R..........",
        ("R" if L >= 3 else ".") + "........ww",
        "...........",
        ".HF.VQ.....",          # lab / food side
    ], lg, w=11)
    pts(d, Y0 + 1, [(10, 15), (15, 15)], "end_rod[facing=up]")
    pts(d, Y0 + 1, [(12, 15)], "potted_bamboo")
    hang(d, Y0, [(9, 17), (15, 17)], kind="glowstone" if L >= 3 else "sea_lantern")
    # ---------------------------------------------------------------- stores (east wing)
    nb = need(d, "barrel") - 4
    north = {5: ".KKKKK.sss.", 9: ".KKKKKKKKK."}[(nb + 1) // 2]
    plan(d, Y0, 33, 13, [
        north,
        ".........<_",          # store clerk by the loading doors
        "...........",
        "...........",
        "...........",
        "...........",
        "...........",
        "...........",
        "ss.ss..ssj.",
    ], leg | {"K": BAR("south"), "j": "cyan_shulker_box[facing=up]"}, w=11)
    pts(d, Y0 + 1, [(43, 14)], "end_rod[facing=up]")
    pts(d, Y0 + 1, [(33, 21), (36, 21)], "light_gray_shulker_box[facing=up]")
    hang(d, Y0, [(36, 17), (40, 17)], kind="glowstone" if L >= 3 else "sea_lantern")


def nt_upper(d, L, leg):
    y = 7
    # ---------------------------------------------------------------- council chamber (core upper)
    plan(d, y, 19, 13, [
        "p.....I....." + ("J" if L >= 4 else "p"),
        ".............",
        "..<T.....T>..",          # horseshoe council table open toward the lectern
        "..<T.....T>..",
        "..<T.....T>..",
        "..<TTTTTTT>..",
        "...vvvvvvv...",
        "     ........",
        "      .......",
    ], leg | {"I": IT("lectern", "south"), "J": IT("jukebox")}, w=13)
    pts(d, y + 1, [(22, 15), (28, 15)], "potted_bamboo")
    pts(d, y + 1, [(25, 18)], "end_rod[facing=up]")
    pts(d, y + 1, [(22, 17), (28, 17)], "black_stained_glass_pane")     # clerks' screens at the table ends
    hang(d, y, [(25, 16), (25, 19)], kind="sea_lantern")
    # ---------------------------------------------------------------- archive (west upper)
    plan(d, y, 7, 13, [
        "B..p....p..",
        "B..........",
        "B.bbbbbb...",          # free-standing record stack
        "B..........",
        "B..........",
        "B...E......",
        "B..........",
        "B.^..^..^..",
        "B._.._.._..",          # study carrels under the south glazing
    ], leg | {"E": IT("enchanting_table")}, w=11)
    pts(d, y + 1, [(9, 21), (12, 21), (15, 21)], LANT())
    hang(d, y, [(10, 17), (14, 17)], kind="sea_lantern")
    # ---------------------------------------------------------------- guest rooms (east upper)
    plan(d, y, 33, 13, [
        "p.........p",
        "...........",
        "..vvv......",            # sofa facing the media wall
        "..._.......",
        "...........",
        "...........",
        "...........",
        "..N.N.N.N..",            # bed pods with low partitions (lamp on each)
        ".HNHNHNHNH.",
    ], leg | {"H": BED("south", "cyan"), "N": "white_concrete"}, w=11)
    pts(d, y + 1, [(35, 21), (37, 21), (39, 21), (41, 21)], LANT())
    hang(d, y, [(38, 16), (38, 19)], kind="sea_lantern")
    # ---------------------------------------------------------------- roof gardens on the wings
    ry = 12
    plan(d, ry, 7, 13, [
        "zM.......Mz",
        "M..p...p..M",
        "...........",
        ".zz.....zz.",
        "...........",
        "M..p...p..M",
        "zM.......Mz",
        "...........",
        ".V.......R.",
    ], leg | {"V": STK("smooth_stone", "iron_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]"),
              "R": "lightning_rod[facing=up,powered=false,waterlogged=false]"}, w=11)
    plan(d, ry, 33, 13, [
        "...........",
        ".SSSSSSSSS.",
        ".SSSSSSSSS.",
        "...........",
        ".SSSSSSSSS.",
        ".SSSSSSSSS.",
        "...........",
        ".SSSSSSSSS.",
        "V.........R",
    ], leg | {"V": STK("smooth_stone", "iron_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]"),
              "R": "lightning_rod[facing=up,powered=false,waterlogged=false]"}, w=11)


def nt_rear(d, L, leg):
    # ---------------------------------------------------------------- canteen (rear ground)
    plan(d, Y0, 19, 23, [
        ".....p.p.....",
        "............ ",
        "..^^^^^^^^.. ",
        ".<TTTTTTTT>. ",
        "..vvvvvvvv.. ",
        "............ ",
        "..^^^^^^^^...",
        ".<TTTTTTTT>..",
        "..vvvvvvvv...",
        ".............",
        "__H_u___j___c",          # servery along the south wall
    ], leg | {"H": "smoker[facing=north,lit=false]", "j": "cyan_shulker_box[facing=up]",
              "c": "chest[facing=north,type=single,waterlogged=false]"}, w=13)
    pts(d, Y0 + 1, [(22, 26), (27, 30)], "potted_bamboo")
    pts(d, Y0 + 1, [(25, 26), (24, 30)], LANT())
    pts(d, Y0 + 1, [(20, 33)], "cake[bites=0]")
    pts(d, Y0 + 1, [(21, 30), (28, 26)], CAN(3))
    hang(d, Y0, [(23, 26), (27, 26), (23, 30), (27, 30)], kind="glowstone")
    # ---------------------------------------------------------------- open-plan offices (rear floor 2)
    y = 7
    plan(d, y, 19, 23, [
        "p.........u..",
        "............ ",
        "..<__><__>.  ",          # four-desk pods
        "..<__><__>.  ",
        "..........   ",
        " ............",
        " .<__><__>...",
        " .<__><__>...",
        " ............",
        " ............",
        ".sss...p..._E",          # filing cabinets, the town safe (ender chest)
    ], leg | {"E": IT("ender_chest", "west")}, w=13)
    pts(d, y + 1, [(22, 25), (27, 26), (23, 30), (26, 29)], "potted_bamboo")
    pts(d, y + 1, [(30, 33)], "end_rod[facing=up]")
    hang(d, y, [(24, 26), (24, 30), (28, 31)], kind="glowstone")
    # ---------------------------------------------------------------- planning studio (rear floor 3)
    y = 12
    plan(d, y, 19, 23, [
        "p...bbbbbb..p",
        ".............",
        "...........<_",          # drafting desks on the east glazing
        "....^^^......",
        "...<TTT>.....",          # city model table
        "...<TTT>...<_",
        "  ..vvv......",
        "  ...........",
        "  .........<_",
        " ..._........",
        "..vvv....p..p",          # lounge sofa
    ], leg, w=13)
    pts(d, y + 1, [(23, 27), (25, 28)], "light_blue_carpet")
    pts(d, y + 1, [(24, 27), (23, 28)], "lime_carpet")
    pts(d, y + 1, [(31, 25), (31, 28), (31, 31)], "end_rod[facing=up]")
    pts(d, y + 1, [(22, 32)], "potted_bamboo")
    hang(d, y, [(24, 28), (29, 25), (25, 32)], kind="sea_lantern")
    # ---------------------------------------------------------------- sky garden on the rear block
    plan(d, 17, 19, 23, [
        "zMMM.....MMMz",
        "M...........M",
        "M..v.v.v.v..M",
        "...._._._....",
        "M...........M",
        "M.....e.....M",
        "M...........M",
        "....^.^.^....",
        "M...........M",
        "M...........M",
        "zMMMM...MMMMz",
    ], leg | {"v": OUTSEAT("south", "birch"), "^": OUTSEAT("north", "birch")}, w=13)
    # roof terrace on the council block
    plan(d, 12, 19, 13, [
        "MzM.......MzM",
        ".............",
        "..S.S.S.S.S..",
        "..S.S.S.S.S..",
        ".............",
        "..S.S.S.S.S..",
        "..S.S.S.S.S..",
        ".............",
        "MzM...V...MzM",
    ], leg | {"V": STK("smooth_stone", "iron_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")}, w=13)
    # ---------------------------------------------------------------- fountain plaza
    for x in range(23, 28):
        for z in range(2, 7):
            ring = x in (23, 27) or z in (2, 6)
            d.set(x, 1, z, "smooth_quartz" if ring else "light_blue_concrete")
            d.set(x, Y0, z, slab("smooth_quartz_slab") if ring else "water[level=0]")
    d.set(25, Y0, 4, "smooth_quartz")
    d.set(25, Y0 + 1, 4, "end_rod[facing=up]")
    d.set(25, Y0 + 2, 4, "sea_lantern")
    for x, z in ((12, 3), (38, 3), (12, 8), (38, 8)):
        oak(d, x, z, "birch_log", "birch_leaves", 4)
    plan(d, Y0, 15, 5, ["^^"], {"^": OUTSEAT("north", "birch")})
    plan(d, Y0, 33, 5, ["^^"], {"^": OUTSEAT("north", "birch")})


def stall_nt(d, x, z, color, goods):
    for dx in (0, 2):
        for yy in (2, 3, 4):
            _put(d, x + dx, yy, z, "birch_fence")
            _put(d, x + dx, yy, z + 2, "birch_fence")
    for dx in range(3):
        for dz in range(3):
            _put(d, x + dx, 5, z + dz, f"{color}_concrete" if dx != 1 else "white_concrete")
    _put(d, x + 1, 2, z, slab("smooth_quartz_slab", "top"))
    _put(d, x + 1, 3, z, goods)
    _put(d, x + 1, 2, z + 2, "composter[level=8]")


def nt_tower(d, L, leg):
    X = 35
    # F0 city lobby
    plan(d, Y0, X, 25, [
        " .p......p.",
        " ..........",
        " ..<TT>....",            # city model
        " ..<TT>....",
        " ..........",
        "...........",
        "...........",
        "...^.^.....",            # reception
        "..._____...",
        "...........",
        ".._....._..",
        ".vvv...vvv.",            # waiting sofas
        "...........",
        "p.........p",
        "...........",
    ], leg, w=11)
    pts(d, Y0 + 1, [(39, 27), (40, 28)], "light_blue_carpet")
    pts(d, Y0 + 1, [(40, 27), (39, 28)], "lime_carpet")
    pts(d, Y0 + 1, [(39, 33)], "end_rod[facing=up]")
    pts(d, Y0 + 1, [(41, 33), (37, 35), (43, 35)], "potted_bamboo")
    hang(d, Y0, [(38, 30), (42, 30), (40, 36), (40, 26)], kind="glowstone")
    # F1 planning office
    y = 7
    plan(d, y, X, 25, [
        " ..........",
        "  <__><__>.",
        "  <__><__>.",
        "  .........",
        " ..........",
        "...........",
        ".<__><__>..",
        ".<__><__>..",
        "...........",
        "c..........",
        ".......... ",
        "..^^^..... ",
        ".<TTT>.... ",            # breakout table
        "..vvv..... ",
        "p.......p. ",
    ], leg | {"c": "chest[facing=east,type=single,waterlogged=false]"}, w=11)
    pts(d, y + 1, [(38, 26), (43, 27), (37, 32), (42, 31)], "potted_bamboo")
    pts(d, y + 1, [(39, 37)], "end_rod[facing=up]")
    hang(d, y, [(40, 27), (40, 31), (39, 37)], kind="glowstone")
    # F2 records hall
    y = 12
    plan(d, y, X, 25, [
        " .BBBBBBBB.",
        " ..........",
        " .BBBBBBB..",
        " ..........",
        " .BBBBBBB..",
        "...........",
        "...........",
        ".^^^...^^^.",
        ".TTT...TTT.",
        ".vvv...vvv.",
        ".......... ",
        "B........  ",
        "B..I.....  ",
        "B........  ",
        "B.......p. ",
    ], leg | {"I": "lectern[facing=east,has_book=false,powered=false]"}, w=11)
    pts(d, y + 1, [(37, 33), (43, 33)], LANT())
    hang(d, y, [(40, 26), (40, 28), (40, 31)], kind="glowstone")
    # F3 meeting rooms
    y = 17
    plan(d, y, X, 25, [
        " ..........",
        "  .........",
        "  ..^^^^^..",
        "  .<TTTTT>.",
        "  .<TTTTT>.",
        "....vvvvv..",
        "...........",
        "GGGGG.GGGGG",            # glass partition
        "...........",
        "....^^^....",
        "...<TTT>.. ",
        "....vvv... ",
        ".......... ",
        "s......... ",
        ".......p.. ",
    ], leg, w=11)
    pts(d, y + 1, [(41, 28), (40, 35)], "potted_bamboo")
    pts(d, y + 1, [(39, 28)], "decorated_pot")                        # water jug and desk lamp on the table
    pts(d, y + 1, [(43, 29)], "end_rod[facing=up]")
    hang(d, y, [(41, 29), (40, 35)], kind="glowstone")
    # F4 staff canteen
    y = 22
    plan(d, y, X, 25, [
        " .M_u___c..",
        " ..........",
        " ..........",
        " .^^...^^..",
        " <TT><TT>..",
        " .vv...vv..",
        "...........",
        "..^^...^^..",
        ".<TT><TT>..",
        "..vv...vv..",
        ".......... ",
        "p........  ",
        ".........  ",
        "._.......  ",
        "vvv.....p. ",
    ], leg | {"M": "smoker[facing=south,lit=false]", "c": "chest[facing=south,type=single,waterlogged=false]"}, w=11)
    pts(d, y + 1, [(37, 29), (42, 33)], "potted_bamboo")
    pts(d, y + 1, [(38, 25)], "cake[bites=0]")
    hang(d, y, [(39, 29), (39, 33), (37, 37)], kind="glowstone")
    # F5 mayor's sky office and lounge
    y = 27
    plan(d, y, X, 25, [
        " .bb...bb..",
        "  .........",
        "  ...^.....",            # mayor's desk facing the door
        "  ..___....",
        " ...v.v....",
        "...........",
        "..aaaaaaa..",
        "...........",
        "...........",
        "p.........p",
        "...^^^.....",
        "..<___>....",            # lounge
        "...vvv.....",
        "^^^^^......",            # bar stools
        "_____....pp",
    ], leg, w=11)
    pts(d, y + 1, [(39, 28)], LANT())
    pts(d, y + 1, [(41, 28), (38, 39), (40, 36)], "potted_bamboo")
    pts(d, y + 1, [(36, 39)], "brewing_stand[has_bottle_0=false,has_bottle_1=false,has_bottle_2=false]")
    hang(d, y, [(40, 28), (40, 36), (37, 31)], kind="sea_lantern")
    # roof: helipad and solar field
    plan(d, 32, X, 25, [
        "SSSSS.SSSSS",
        "...........",
        "SSSSS.SSSSS",
        "...........",
        "..yyyyyyy..",
        "..y.....y..",
        "..y.w.w.y..",
        "..y.www.y..",
        "..y.w.w.y..",
        "..y.....y..",
        "..yyyyyyy..",
        "...........",
        "SSSSS.SSSSS",
        "...........",
        "MV.......RM",
    ], leg | {"V": STK("smooth_stone", "iron_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]"),
              "R": "lightning_rod[facing=up,powered=false,waterlogged=false]", "w": "white_carpet"}, w=11)
    # street side additions: market stalls on the plaza, door lights
    stall_nt(d, 5, 3, "orange", "melon")
    stall_nt(d, 42, 2, "lime", "pumpkin")


# ============================================================================================ CASCADIA
# Grange hall of a logging town: long log hall with a deep porch (L1), rear workshop and barrel shed (L2),
# loft library & bunk room plus a fire-lookout bell tower (L3), the mayor's house (L4), fire hall with hose
# tower, jail and livery stable on a boardwalk main street (L5).
def th_cascadia(rel, L):
    d = new("Cascadia", rel, (55, 34, 55), paving="coarse_dirt")
    loft = L >= 3
    c = shell(d, 14, 10, 28, 22, 2 if loft else 1, "gable", "z", ties=(13, 17))
    edoor(d, 21, Y0, 10, "south")
    d.fill(13, 1, 5, 29, 1, 9, "spruce_planks")                   # porch deck
    for x in (13, 17, 25, 29):
        for y in range(Y0, 6):
            d.set(x, y, 5, log("spruce_log"))
    for x in range(12, 31):
        d.set(x, 6, 4, st("spruce_stairs", "south"))
        for z in range(5, 10):
            d.set(x, 6, z, slab("spruce_slab"))
    for x in list(range(14, 17)) + list(range(18, 20)) + list(range(23, 25)) + list(range(26, 29)):
        d.set(x, Y0, 5, "spruce_fence")                              # porch rail, gap at the steps
    d.hut(15, Y0, 11)
    keep(d, 16, Y0, 11)
    d.hearth(15, Y0, 16, "east", c["ridge"] + 2, "cobblestone", "campfire")
    chim(d, 13, 16, Y0, c["ridge"] + 1)
    if L >= 2:
        shell(d, 14, 22, 28, 32, 1, "gable", "z", ties=(25, 29))
        link(d, 21, Y0, 22, "south")
        edoor(d, 21, Y0, 32, "north", double=True)
        chim(d, 28, 27, Y0, 11)
        shell(d, 29, 12, 35, 22, 1, "gable", "z", win="e", ties=(17,))
        edoor(d, 32, Y0, 12, "south")
    if loft:
        d.clear(15, 7, 21, 27, 10, 21)                              # rear roof overhang must not enter the loft
        stairs(d, 16, 21, Y0, 7, "east", rails=[(16, 21), (17, 20), (18, 20), (19, 20)])
        tx1, tz1 = 40, 4                                              # fire-lookout bell tower
        for x, z in ((tx1, tz1), (tx1 + 4, tz1), (tx1, tz1 + 4), (tx1 + 4, tz1 + 4)):
            for y in range(Y0, 21):
                d.set(x, y, z, log("spruce_log"))
        for y in (7, 12):
            for a in range(1, 4):
                for (x, z, ax) in ((tx1 + a, tz1, "x"), (tx1 + a, tz1 + 4, "x"), (tx1, tz1 + a, "z"),
                                   (tx1 + 4, tz1 + a, "z")):
                    d.set(x, y, z, log("spruce_log", ax))
        d.fill(tx1, 17, tz1, tx1 + 4, 17, tz1 + 4, "spruce_planks")
        for x in range(tx1, tx1 + 5):
            for z in range(tz1, tz1 + 5):
                if (x in (tx1, tx1 + 4) or z in (tz1, tz1 + 4)) and d.air(x, 18, z):
                    d.set(x, 18, z, "spruce_fence")
        d.hip(tx1, tz1, tx1 + 4, tz1 + 4, 21, "dark_oak_stairs", "dark_oak_slab", overhang=1)
        d.set(tx1 + 2, 21, tz1 + 2, "spruce_planks")
        bell(d, tx1 + 2, 20, tz1 + 2)
        d.fill(tx1 + 1, 1, tz1 + 1, tx1 + 3, 1, tz1 + 3, "cobblestone")
    else:
        for y in range(Y0, 6):
            d.set(32, y, 6, log("spruce_log"))
            d.set(34, y, 6, log("spruce_log"))
        d.fill(32, 6, 6, 34, 6, 6, log("spruce_log", "x"))
        bell(d, 33, 5, 6)
    if L >= 4:
        m = shell(d, 2, 10, 12, 24, 2, "gable", "z", ties=(13, 20))
        edoor(d, 7, Y0, 10, "south")
        stairs(d, 11, 12, Y0, 7, "south", rails=[(11, 12), (10, 13), (10, 14), (10, 15)])
        for x in (3, 11):                                            # porch posts and roof over the door
            for y in range(Y0, 5):
                d.set(x, y, 9, log("spruce_log"))
        for x in range(2, 13):
            for z in (8, 9):
                d.set(x, 5, z, slab("spruce_slab"))
        chim(d, 2, 16, Y0, m["ridge"] + 1)
    if L >= 5:
        shell(d, 36, 14, 48, 28, 2, "gable", "z", mat="mangrove_planks", up="mangrove_planks", ties=(18, 24))
        for x in range(40, 44):                                      # engine bay doors
            for y in range(Y0, Y0 + 3):
                d.set(x, y, 14, AIR)
        d.double_door(41, Y0, 14, "x", "south", "spruce")
        stairs(d, 47, 22, Y0, 7, "south", rails=[(47, 22), (46, 23), (46, 24), (46, 25)])
        for y in range(Y0, 24):                                      # hose-drying tower
            for x, z in ((50, 22), (52, 22), (50, 24), (52, 24)):
                d.set(x, y, z, log("spruce_log"))
        for y in (5, 10, 15, 20):
            for x in (50, 51, 52):
                d.set(x, y, 22, log("spruce_log", "x"))
                d.set(x, y, 24, log("spruce_log", "x"))
        d.hip(50, 22, 52, 24, 24, "dark_oak_stairs", "dark_oak_slab", overhang=1)
        shell(d, 36, 34, 46, 42, 1, "gable", "x", mat="cobblestone", up="cobblestone", gable_end="cobblestone",
              ties=(41,))
        edoor(d, 41, Y0, 34, "south")
        shell(d, 2, 28, 12, 42, 1, "gable", "z", mat="stripped_spruce_log", ties=(33, 37))
        edoor(d, 7, Y0, 28, "south", double=True)
    cs_rooms(d, L)
    return d


def lamppost_cs(d, x, z):
    pts(d, Y0, [(x, z)], "spruce_log[axis=y]")
    pts(d, Y0 + 1, [(x, z)], "spruce_fence")
    pts(d, Y0 + 2, [(x, z)], "spruce_fence")
    pts(d, Y0 + 3, [(x, z)], LANT())


def spruce(d, x, z, h=6):
    """One hand-placed spruce (trunk + layered cone) at (x, z)."""
    d.set(x, 1, z, "podzol[snowy=false]")
    for k in range(h):
        d.set(x, Y0 + k, z, log("spruce_log"))
    lv = "spruce_leaves[distance=1,persistent=true,waterlogged=false]"
    for y, r in ((4, 2), (5, 1), (6, 2), (7, 1), (8, 0)):
        for a in range(-r, r + 1):
            for b in range(-r, r + 1):
                if abs(a) + abs(b) <= r + (1 if r == 2 else 0) and d.air(x + a, y, z + b):
                    d.set(x + a, y, z + b, lv)
    if d.air(x, 8, z):
        d.set(x, 8, z, lv)


def cs_rooms(d, L):
    W = "spruce"
    loft = L >= 3
    leg = base_leg(d, W, plant="potted_fern") | {"h": "hay_block[axis=y]", "e": "barrel[facing=west,open=false]",
                                               "u": "water_cauldron[level=3]", "f": "spruce_fence"}
    # ---------------------------------------------------------------- grange hall (core ground)
    lg = leg | {"C": IT("crafting_table"), "F": IT("furnace", "west"), "K": BAR("west"), "Z": BED("west")}
    plan(d, Y0, 15, 11, [
        " ...........C",
        "p...........F",
        ".....<T>....F",          # long trestle table down the middle of the hall
        ".....<T>.....",
        " k>..<T>....K",          # fireside chairs at the hearth, barrels on the east wall
        " k...<T>....K",
        " k>..<T>.....",
        "......v......",
        "Z............",          # caretaker's bunk by the fire
        "_............",
        ("..vvv........" if L <= 2 else "." + "     " + "......."),
    ], lg, w=13)
    pts(d, Y0 + 1, [(21, 13)], "flower_pot")
    pts(d, Y0 + 1, [(21, 15), (15, 20)], LANT())
    pts(d, Y0 + 1, [(21, 17)], CAN(3))
    hang(d, Y0, [(18, 13), (24, 17)])
    # ---------------------------------------------------------------- porch, street front
    plan(d, Y0, 15, 7, ["v" + "." * 11 + "v"], {"v": OUTSEAT("south", W)})
    pts(d, Y0, [(16, 9), (26, 9)], "potted_fern")
    d.sign(21, 5, 9, "north", ["GRANGE", "HALL"], W)
    for x in (20, 22):
        _put(d, x, 5, 9, LANT(True))
    lamppost_cs(d, 11, 6) if L < 4 else None
    lamppost_cs(d, 31, 6)
    if L >= 2:
        cs_back(d, L, leg)
    if loft:
        cs_loft(d, L, leg)
    if L >= 4:
        cs_mayor(d, L, leg)
    if L >= 5:
        cs_street(d, L, leg)


def cs_back(d, L, leg):
    W = "spruce"
    # ---------------------------------------------------------------- workshop (rear wing)
    lg = leg | {"C": IT("crafting_table", None), "O": IT("stonecutter", "east"), "X": IT("fletching_table"),
                "P": IT("cartography_table"), "N": IT("loom", "east"), "G": IT("grindstone", "west"),
                "M": IT("smithing_table"), "A": IT("anvil", "east"), "S": IT("blast_furnace", "west"),
                "F": IT("furnace", "west"), "H": IT("smoker", "north"), "V": IT("brewing_stand"),
                "Q": IT("water_cauldron[level=3]"), "l": "stripped_spruce_log[axis=x]", "w": "white_wool",
                "c": "chest[facing=north,type=single,waterlogged=false]"}
    plan(d, Y0, 15, 23, [
        ".............",
        "C...........G",          # carpenter's benches on the west wall, forge on the east wall
        "O...........M",
        "X.........A..",
        "P..ll.......S",          # saw horse with a log
        "N........." + ("A" if L >= 3 else ".") + ".F",
        "............" + ("G" if L >= 3 else "."),
        "w............",
        "HVQ......c.ee",
    ], lg, w=13)
    pts(d, Y0 + 1, [(18, 27)], "stripped_spruce_log[axis=x]")
    hang(d, Y0, [(18, 25), (24, 29)])
    # ---------------------------------------------------------------- barrel shed
    nb = need(d, "barrel") - 4
    if nb <= 10:
        rows = [".....", "....h", "K...h", "K....", "K...c", "K....", "K...e", "....e", "l...l"]
    else:
        rows = [".....", "K...h", "K...h", "K....", "K...c", "K....", "K...e", "K....", "K...K"]
    plan(d, Y0, 30, 13, rows, leg | {"K": BAR("east"), "l": "spruce_log[axis=z]",
                                    "c": "chest[facing=west,type=single,waterlogged=false]"}, w=5)
    hang(d, Y0, [(32, 17)])
    if L <= 4:                                                         # log pile and hand cart by the shed
        for x in (38, 39):
            for y in (2, 3):
                _put(d, x, y, 14, log("spruce_log", "z"))
        plan(d, Y0, 37, 17, ["f", "_", "_"], {"f": "spruce_fence", "_": slab("spruce_slab", "top")})
        _put(d, 37, 3, 19, "hay_block[axis=y]")


def cs_loft(d, L, leg):
    W = "spruce"
    y = 7
    plan(d, y, 15, 11, [
        "B1BB1BB1BB1BB",          # book wall under the north windows
        "1............",
        "B..bb...<T>.I",          # record press, reading table, charter lectern
        "B....E..<T>..",
        "1............",
        " ............",
        "_...........H",          # bunk beds along both eaves walls
        "W...........c",
        "c...........H",
        "W.   .......c",
        ".     ......H",
    ], leg | {"I": IT("lectern", "west"), "E": IT("enchanting_table"), "H": BED("east"), "W": BED("west"),
              "c": "chest[facing=west,type=single,waterlogged=false]"}, w=13)
    pts(d, y + 1, [(24, 13)], LANT())
    pts(d, y + 1, [(15, 17)], CAN(1))
    hang(d, y, [(21, 13), (21, 17)])
    # covered back porch on the workshop: posts, shed roof, rail and a bench either side of the doors
    for x in (14, 18, 25, 28):
        for yy in range(Y0, 6):
            d.set(x, yy, 35, log("spruce_log"))
    for x in range(14, 29):
        d.set(x, 6, 36, st("spruce_stairs", "north"))
        for z in (33, 34, 35):
            d.set(x, 6, z, slab("spruce_slab"))
    for x in (15, 16, 17, 19, 24, 26, 27):
        _put(d, x, Y0, 35, "spruce_fence")
    plan(d, Y0, 16, 34, ["vv......vv"], {"v": OUTSEAT("south", W)})
    _put(d, 20, 5, 33, LANT(True))
    _put(d, 23, 5, 33, LANT(True))


def cs_mayor(d, L, leg):
    W = "spruce"
    d.hearth(3, Y0, 16, "east", 6, "cobblestone", "campfire")
    plan(d, Y0, 3, 11, [
        "p.c......",
        "........ ",
        "bb...... ",
        "...._... ",
        " kk>.... ",              # settle facing the parlour fire
        " kk>.... ",
        " kk>.....",
        ".........",
        "..^^^....",
        ".<TTT>...",              # family dining table
        "..vvv....",
        ".........",
        "FM_u__c.e",              # kitchen wall
    ], leg | {"F": "furnace[facing=north,lit=false]", "M": "smoker[facing=north,lit=false]",
              "c": "chest[facing=north,type=single,waterlogged=false]"}, w=9)
    pts(d, Y0 + 1, [(6, 14)], LANT())
    pts(d, Y0 + 1, [(6, 20)], CAN(3))
    pts(d, Y0 + 1, [(5, 23)], "flower_pot")
    hang(d, Y0, [(6, 13), (6, 20)])
    y = 7
    plan(d, y, 3, 11, [
        "JE..bbb..",              # mayor's office: record player, town safe, book cases
        "..^..... ",
        "..__...  ",
        "..v.v..  ",
        ".......  ",
        ".........",
        ".........",
        ".........",
        "_........",
        "W..kk...c",              # bedroom
        "W..kk...c",
        "_........",
        "p......u.",
    ], leg | {"J": IT("jukebox"), "E": IT("ender_chest", "south"), "W": BED("west"),
              "c": "chest[facing=west,type=single,waterlogged=false]"}, w=9)
    pts(d, y + 1, [(5, 13)], CAN(2))
    pts(d, y + 1, [(3, 19), (3, 22)], CAN(1))
    hang(d, y, [(6, 13), (6, 20)])
    d.sign(7, 5, 9, "north", ["MAYOR"], W)
    # front yard: rail fence, flower beds, two spruces
    for x in range(1, 13):
        if x not in (6, 7, 8):
            d.set(x, Y0, 6, "spruce_fence")
    for x0, row in ((2, "fbaf"), (9, "afbf")):
        d.fill(x0, 1, 7, x0 + 3, 1, 8, "grass_block[snowy=false]")
        plan(d, Y0, x0, 7, [row, row[::-1]], {"f": "fern", "b": "blue_orchid", "a": "allium"})
    spruce(d, 4, 3)
    spruce(d, 10, 3)
    d.fill(6, 1, 3, 8, 1, 9, "spruce_planks")
    # water tower on trestle legs east of the lookout
    for x, z in ((48, 4), (52, 4), (48, 8), (52, 8)):
        for yy in range(Y0, 14):
            d.set(x, yy, z, log("spruce_log"))
    for yy in (6, 10):
        for a in range(49, 52):
            d.set(a, yy, 4, log("spruce_log", "x"))
            d.set(a, yy, 8, log("spruce_log", "x"))
        for a in range(5, 8):
            d.set(48, yy, a, log("spruce_log", "z"))
            d.set(52, yy, a, log("spruce_log", "z"))
    d.fill(48, 13, 4, 52, 13, 8, "spruce_planks")
    for yy in range(14, 19):                                         # stave tank with iron hoops
        for x in range(48, 53):
            for z in range(4, 9):
                if x in (48, 52) or z in (4, 8):
                    if (x, z) in ((48, 4), (52, 4), (48, 8), (52, 8)):
                        continue
                    d.set(x, yy, z, log("stripped_spruce_log", "y") if yy not in (15, 17) else "spruce_planks")
    d.hip(48, 4, 52, 8, 19, "dark_oak_stairs", "dark_oak_slab", overhang=1)
    # under the tank: horse trough below the outlet, a hay bale, a feed barrel and a lantern on a leg
    pts(d, Y0, [(50, 6), (51, 6)], "water_cauldron[level=3]")
    pts(d, Y0, [(49, 5)], "hay_block[axis=y]")
    pts(d, Y0, [(49, 7)], "barrel[facing=up,open=false]")
    pts(d, 12, [(50, 6)], "chain[axis=y,waterlogged=false]")          # outlet pipe over the trough
    pts(d, 4, [(47, 6)], "wall_torch[facing=west]")


def cs_street(d, L, leg):
    W = "spruce"
    # ---------------------------------------------------------------- fire hall
    plan(d, Y0, 37, 15, [
        "c..p....p..",
        "c..........",
        "c..........",
        "c...ww.....",            # hose wagon
        "....ww....u",
        "....ww....u",
        "....ww.....",
        ".......... ",
        ".^^^...... ",
        "<TTT>..... ",            # crew mess table
        ".vvv...... ",
        ".......... ",
        "FM_u_...ee.",
    ], leg | {"w": "red_wool", "F": "furnace[facing=north,lit=false]", "M": "smoker[facing=north,lit=false]",
              "c": "chest[facing=east,type=single,waterlogged=false]"}, w=11)
    pts(d, Y0 + 1, [(41, 19), (42, 19)], "barrel[facing=north,open=false]")
    pts(d, Y0 + 1, [(39, 24)], LANT())
    hang(d, Y0, [(39, 20), (44, 20)])
    plan(d, 7, 37, 15, [
        "H..........",
        "c..........",
        "H......^^..",
        "c.....<TT>.",            # card table
        "H......vv..",
        "c..........",
        "H..........",
        "c......... ",
        "H........  ",
        "c........  ",
        "H........  ",
        "...........",
        "p.._.....p.",
    ], leg | {"H": BED("west"), "c": "chest[facing=east,type=single,waterlogged=false]"}, w=11)
    pts(d, 8, [(44, 18)], LANT())
    hang(d, 7, [(41, 18), (41, 24)])
    d.sign(42, 6, 13, "north", ["FIRE", "HALL"], W)
    # east side under the eaves: two ladders racked on the wall, fire buckets, hose barrels, a wall torch
    for z in (17, 18):
        for yy in (Y0, Y0 + 1, Y0 + 2):
            pts(d, yy, [(49, z)], "ladder[facing=east,waterlogged=false]")
    pts(d, Y0, [(49, 20), (49, 21)], "water_cauldron[level=3]")
    pts(d, Y0, [(49, 25), (49, 26)], "barrel[facing=up,open=false]")
    wtorch(d, 49, 4, 23, "east")
    # ---------------------------------------------------------------- jail
    plan(d, Y0, 37, 35, [
        "c.......p",
        ".^......>",
        ".__.....>",              # sheriff's desk, bench for visitors
        "bbIbbbIbb",              # cell front: bars and iron doors
        ".........",
        ".........",
        "h..u.h..u",
    ], leg | {"b": "iron_bars", "I": "iron_door[facing=south,half=lower,hinge=left,open=false,powered=false]",
              "u": "cauldron", "c": "chest[facing=south,type=single,waterlogged=false]"}, w=9)
    for x in (39, 43):
        d.set(x, Y0 + 1, 38, "iron_door[facing=south,half=upper,hinge=left,open=false,powered=false]")
    for x in range(37, 46):
        if x not in (39, 43):
            for yy in (Y0 + 1, Y0 + 2):
                d.set(x, yy, 38, "iron_bars")
    for z in range(39, 42):
        for yy in (Y0, Y0 + 1, Y0 + 2):
            d.set(41, yy, z, "iron_bars")
    pts(d, Y0 + 1, [(38, 37)], CAN(1))
    hang(d, Y0, [(41, 36)])
    d.sign(41, 5, 33, "north", ["JAIL"], W)
    # ---------------------------------------------------------------- livery stable
    plan(d, Y0, 3, 29, [
        "p.......p",
        "h.......h",              # hay feeders in each stall
        ".........",
        "ff.....ff",
        "h.......h",
        ".........",
        "ff.....ff",
        "h.......h",
        ".........",
        "ff.....ff",
        "h.......h",
        ".........",
        "uu.ccc.ee",              # water trough, tack chests, feed kegs
    ], leg | {"u": "water_cauldron[level=3]", "c": "chest[facing=north,type=single,waterlogged=false]",
              "e": "barrel[facing=north,open=false]"}, w=9)
    hang(d, Y0, [(7, 33), (7, 37)])
    d.sign(7, 5, 27, "north", ["LIVERY"], W)
    # ---------------------------------------------------------------- boardwalk main street
    for x in range(0, 55):
        for z in range(0, 3):
            d.set(x, 1, z, "spruce_planks")
    for x in (2, 8, 14, 20, 26, 32, 38, 44, 50):                    # hitching posts with lanterns
        _put(d, x, Y0, 3, "spruce_fence")
        _put(d, x, Y0 + 1, 3, LANT())


@design("townhall")
def townhall_v2(pack, rel, L):
    return common_materials({"Hearthwood": th_hearthwood, "Cascadia": th_cascadia, "Neoterra": th_neoterra}[pack](rel, L))
