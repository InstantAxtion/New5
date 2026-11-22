"""Civic: university (hand-designed, all packs).

Round 4: every room, yard and exterior detail is placed by hand. Shells (walls, floors, window openings, roofs)
come from the local shell() (a copy of _civic_common.bldg without any decoration or light passes); furniture is
drawn from per-room ASCII plans (plan()) or single-piece calls at concrete coordinates. Nothing scans the grid
or decides by itself where a piece goes.
"""
from designs._civic_common import (Y0, st, slab, log, flight, framing, clockface, bell, need, keep, new, put,  # noqa: F401
                                   wallblock, link, arch, chimney, plant_tree, post_lamp, park_bench, fountain,
                                   cart, common_materials)
from hm import design, AIR, D4, OPP, CW  # noqa: E402,F401


# ============================================================================================ shell & openings
def shell(d, x1, z1, x2, z2, nf=1, roof="gable", axis="x", win="nesw", ws=3, mat=None, up=None, wh=4,
          gable_end=None, ties=(), glassy=False, parapet=True):
    """Building shell only: floor, walls per storey with storey bands, plinth, corner quoins/posts, window
    openings, roof. `ties` = explicit positions (along the ridge axis) of the tie beams under a gable roof.
    Returns dict(ys, top, ridge, x1, z1, x2, z2). No furniture, lights or window dressing."""
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
    for x in range(x1, x2 + 1):                                       # plinth
        for z in range(z1, z2 + 1):
            if x in (x1, x2) or z in (z1, z2):
                d.set(x, Y0, z, S["base"] if not (d.pack == "Cascadia" and (x * 7 + z) % 5 == 0) else "mossy_cobblestone")
    if d.pack == "Hearthwood":
        for f, y in enumerate(ys):
            m = mat if f == 0 else up
            if m in ("calcite", "yellow_terracotta", "white_terracotta"):
                framing(d, x1, z1, x2, z2, y, y + wh - 1, S["post"], every=3)
    for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):             # corner quoins / posts
        for y in range(Y0, top + 1):
            if d.pack == "Hearthwood":
                d.set(x, y, z, ("smooth_stone" if y % 2 else "chiseled_stone_bricks") if mat == "stone_bricks" else
                      ("smooth_stone" if y % 2 else "stone_bricks"))
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
        ends = ((x1, (z1 + z2) // 2), (x2, (z1 + z2) // 2)) if axis == "x" else \
            (((x1 + x2) // 2, z1), ((x1 + x2) // 2, z2))
        for ex, ez in ends:                                           # king post / gable window
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
        for x in range(x1, x2 + 1):                                   # cantilevered roof edge
            for z in (z1 - 1, z2 + 1):
                put(d, x, top + 1, z, edge)
        for z in range(z1, z2 + 1):
            for x in (x1 - 1, x2 + 1):
                put(d, x, top + 1, z, edge)
        ridge = top + 1
    return dict(ys=ys, top=top, ridge=ridge, x1=x1, z1=z1, x2=x2, z2=z2)


def entrance(d, x, y, z, facing, wood=None, double=False, along="x", step=None):
    """Exterior door in a wall (facing = into the building); clears and reserves the cells before and behind it
    and lays one step stone outside. No lamps – those are placed by hand."""
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


def stairs(d, x, z, y0, yU, rise, rails=(), block=None, rail=None):
    """Straight flight between storeys; `rails` = explicit (x, y, z) cells for the balustrade round the hole."""
    block = block or (f"{d.S['wood']}_stairs" if d.pack != "Neoterra" else "smooth_quartz_stairs")
    dx, dz = D4[rise]
    n = yU - y0
    keep(d, x - dx, y0, z - dz, 3)
    lx, lz = flight(d, x, z, y0, yU, rise, block, under=d.S["floor"] if d.pack != "Neoterra" else "smooth_quartz")
    keep(d, lx, yU, lz, 3)
    for i in range(n):
        keep(d, x + dx * i, y0 + i + 1, z + dz * i, 3)
    rail = rail or (f"{d.S['wood']}_fence" if d.pack != "Neoterra" else "glass_pane")
    for (rx, ry, rz) in rails:
        d.set(rx, ry, rz, rail)
    return lx, lz


def lawn(d, x1, z1, x2, z2, mat="grass_block[snowy=false]"):
    """Ground rectangle (y = 1) – draw lawns before buildings and paths."""
    d.fill(x1, 1, z1, x2, 1, z2, mat)


def pave(d, x1, z1, x2, z2, mat):
    d.fill(x1, 1, z1, x2, 1, z2, mat)


def bed_of(d, x1, z1, x2, z2, flowers):
    """Flower bed over the rectangle I give, flowers in the order listed (row by row)."""
    i = 0
    for z in range(min(z1, z2), max(z1, z2) + 1):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            d.set(x, 1, z, "grass_block[snowy=false]")
            d.set(x, 2, z, flowers[i % len(flowers)])
            i += 1


def hedge_line(d, x1, z1, x2, z2, leaves="oak_leaves"):
    for x in range(min(x1, x2), max(x1, x2) + 1):
        for z in range(min(z1, z2), max(z1, z2) + 1):
            d.set(x, 2, z, f"{leaves}[distance=1,persistent=true,waterlogged=false]")


def flower_box(d, x, y, z, out, flower, trap=None):
    """One window box under a window: trapdoor front at (x,y,z) outside the wall, pot in it is not possible, so
    the box is a top trapdoor ledge with a potted flower standing on the ledge cell above."""
    trap = trap or f"{d.S['wood']}_trapdoor"
    d.set(x, y, z, f"{trap}[facing={out},half=top,open=false,powered=false,waterlogged=false]")
    d.set(x, y + 1, z, f"potted_{flower}")


# ============================================================================================ room plans
def _chair(back, sit=True):
    return lambda d, x, y, z: d.chair(x, y, z, back, d.S["wood"] if d.pack != "Neoterra" else "birch", sit=sit)


def _it(name, facing=None):
    def f(d, x, y, z):
        if name == "water_cauldron":
            d.item(x, y, z, "water_cauldron[level=3]")
        else:
            d.item(x, y, z, name, facing)
    return f


def _rack(facing):
    return lambda d, x, y, z: d.rack(x, y, z, facing)


def _hut(facing="north"):
    return lambda d, x, y, z: d.hut(x, y, z, facing)


def _bed(facing, color=None):
    return lambda d, x, y, z: d.bed(x, y, z, facing, color)


def _spot(name):
    def f(d, x, y, z):
        d.spot(x, y, z, name)
        keep(d, x, y, z)
    return f


def _shelf(d, x, y, z):
    d.bookshelf(x, y, z)


def chest(facing, typ="single"):
    return f"chest[facing={facing},type={typ},waterlogged=false]"


def trap(wood, facing, half="top", open_=False):
    return f"{wood}_trapdoor[facing={facing},half={half},open={'true' if open_ else 'false'},powered=false,waterlogged=false]"


def legend(dd, **over):
    """Shared plan characters (per pack materials). Room plans add their own characters with `over`."""
    neo = dd.pack == "Neoterra"
    W = dd.S["wood"] if not neo else "birch"
    g = {
        "B": _shelf,
        "n": _chair("north"), "s": _chair("south"), "e": _chair("east"), "w": _chair("west"),
        "N": _chair("north", False), "S": _chair("south", False), "E": _chair("east", False), "W": _chair("west", False),
        "T": "smooth_quartz" if neo else f"{W}_planks",
        "t": slab("smooth_quartz_slab" if neo else f"{W}_slab", "top"),
        "c": "candle[candles=3,lit=false,waterlogged=false]",
        "k": "candle[candles=1,lit=false,waterlogged=false]",
        "o": "flower_pot",
        "p": {"Neoterra": "potted_bamboo", "Hearthwood": "potted_red_tulip", "Cascadia": "potted_fern"}[dd.pack],
        "L": "lantern[hanging=true,waterlogged=false]",
        "l": "lantern[hanging=false,waterlogged=false]",
        "*": "sea_lantern",
        "=": {"Neoterra": "cyan_carpet", "Hearthwood": "red_carpet", "Cascadia": "brown_carpet"}[dd.pack],
        "-": {"Neoterra": "light_gray_carpet", "Hearthwood": "orange_carpet", "Cascadia": "green_carpet"}[dd.pack],
        "X": "barrel[facing=up,open=false]",
        "f": f"{W}_fence",
        "#": f"{W}_planks",
        ".": AIR,
    }
    g.update(over)
    return g


def plan(d, x0, z0, y, layers, lg):
    """Stamp a hand-drawn room plan. layers[k] (rows north->south, chars west->east) is drawn at y + k.
    ' ' leaves a cell alone; other chars come from `lg` (block state or callable(d, x, y, z)). Refuses to put
    anything into cells reserved for door approaches / stair landings / work-block fronts."""
    for k, rows in enumerate(layers):
        yy = y + k
        for dz, row in enumerate(rows):
            for dx, ch in enumerate(row):
                if ch == " ":
                    continue
                x, z = x0 + dx, z0 + dz
                v = lg[ch]
                if (x, yy, z) in d.res and v != AIR:
                    raise ValueError(f"{d.pack} {d.rel}: plan puts '{ch}' on reserved cell {(x, yy, z)}")
                if callable(v):
                    v(d, x, yy, z)
                else:
                    d.set(x, yy, z, v)


# ============================================================================================ Hearthwood
def uni_hearthwood(rel, L):
    """Oxford college growing into a full quadrangle: Old Schools (L1) -> gate tower & laboratory (L2) ->
    great hall & quad (L3) -> upper storeys & library range with cloister (L4) -> chapel, master's garden and
    the New Building residence (L5)."""
    d = new("Hearthwood", rel, (49, 30, 57))
    SB = "stone_bricks"
    lg = legend(d, h=_bed("north"), H=_bed("south"), u="cauldron", q="cake[bites=0]",
                m="potted_red_mushroom", C=chest("south"), d="decorated_pot[cracked=false,facing=north,waterlogged=false]",
                v="brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]")
    two = L >= 4

    # ---------------------------------------------------------------- Old Schools (L1 core; upper storey L4)
    b = shell(d, 8, 8, 20, 15, 2 if two else 1, "gable", "x", mat=SB, up=SB, gable_end=SB, ties=(11, 16))
    entrance(d, 14, Y0, 8, "south")
    d.sign(14, 5, 7, "north", ["OLD SCHOOLS", "", "Collegium"], "dark_oak")
    d.wall_torch(13, 4, 7, "north")
    d.wall_torch(15, 4, 7, "north")
    d.hearth(9, Y0, 12, "east", b["ridge"] + 2, "bricks", "campfire")
    chimney(d, 8, 12, Y0, b["ridge"] + 1)
    keep(d, 18, Y0, 9)                                                # hut, rack, lectern fronts
    keep(d, 18, Y0, 11)
    keep(d, 18, Y0, 13)
    keep(d, 10, Y0, 9)                                                # furnace front
    lg.update(F=_it("furnace", "east"), R=_rack("west"), Q=_it("lectern", "west"), Y=_hut())
    if two:
        stairs(d, 13, 14, Y0, 7, "east", rails=[(13, 7, 14), (14, 7, 13), (15, 7, 13), (16, 7, 13)])
        south = "pBB.     Bp"
    else:
        south = "pBBBBBBBBBp"
    # the study: fireside armchairs (W), tutorial table (centre), lectern + rack on the east wall, books south
    plan(d, 9, 9, Y0, [
        ["F..t...tp.Y",
         "......nnn..",
         " =e...TTT.R",
         " =t...sss..",
         " =e.......Q",
         south],
        ["   o   c   ",
         "           ",
         "       c   ",
         "  k        ",
         "           ",
         " BB      B " if two else " BBBBBBBBB "],
        ["           ",
         "           ",
         "           ",
         "           ",
         "           ",
         " BB      B " if two else (" BBBBBBBBB " if L >= 2 else "           ")],
        ["           ",
         "           ",
         "  L    L   "]], lg)
    d.banner(11, 4, 9, "south", "blue")
    d.banner(17, 4, 9, "south", "blue")
    for x in (10, 13, 16):                                            # window boxes on the street front
        flower_box(d, x, Y0, 7, "north", ("red_tulip", "oxeye_daisy", "cornflower")[(x - 10) // 3])
    if two:                                                           # upper storey: two scholars' sets
        plan(d, 9, 9, 7, [
            ["thC.BttBCht",
             ". ..BssB. .",
             ".=.......=.",
             " .t.....t..",
             "..s..   s..",
             "BBX.      p"],
            ["k   BcoB  k",
             "    B  B   ",
             "           ",
             "  k     k  ",
             "           ",
             "BB         "],
            [],
            ["           ",
             "           ",
             "  L    L   "]], lg)
        for x in (10, 13, 16):
            flower_box(d, x, 7, 7, "north", ("allium", "red_tulip", "oxeye_daisy")[(x - 10) // 3])
    # forecourt: gravel walk with stone kerbs, two cottage beds, a lamp at each bed
    pave(d, 12, 0, 12, 6, SB)
    pave(d, 16, 0, 16, 6, SB)
    pave(d, 13, 0, 15, 6, "gravel")
    bed_of(d, 9, 4, 11, 6, ("red_tulip", "oxeye_daisy", "cornflower", "allium"))
    bed_of(d, 17, 4, 19, 6, ("allium", "cornflower", "oxeye_daisy", "red_tulip"))
    post_lamp(d, 11, 3)
    post_lamp(d, 17, 3)

    # ---------------------------------------------------------------- L2: gate tower + laboratory range
    if L >= 2:
        g = shell(d, 21, 7, 25, 15, 3, "flat", mat=SB, up=SB, win="nesw", ws=2)
        d.clear(22, Y0, 7, 24, 5, 15)                                 # gate passage
        d.fill(22, 1, 7, 24, 1, 15, SB)
        for z in (7, 15):
            d.set(22, 5, z, st("stone_brick_stairs", "west", "top"))
            d.set(24, 5, z, st("stone_brick_stairs", "east", "top"))
            d.set(23, 5, z, "chiseled_stone_bricks")
        for x, z in ((21, 7), (25, 7), (21, 15), (25, 15)):           # corner turrets
            for y in range(g["top"] + 2, g["top"] + 5):
                d.set(x, y, z, SB if y < g["top"] + 4 else "stone_brick_wall")
        d.banner(22, 9, 6, "north", "blue")
        d.banner(24, 9, 6, "north", "blue")
        clockface(d, 23, 13, 7, "north", "smooth_quartz")
        for y in range(Y0, 13):                                       # ladder up the east wall of the tower
            d.set(24, y, 10, "ladder[facing=west,waterlogged=false]")
        for z in (8, 14):                                             # lanterns under the gate arches
            d.set(23, 5, z, "lantern[hanging=true,waterlogged=false]")
        # muniment room (archive) on the first floor
        plan(d, 22, 8, 7, [
            ["BCB", "X..", "X. ", "C..", "C..", "X.t", "BBB"],
            ["B B", "   ", "   ", "   ", "   ", "  l", "BBB"],
            [],
            ["   ", "   ", "   ", " L "]], legend(d, C=chest("east")))
        # the Master's study on the top floor
        plan(d, 22, 8, 12, [
            ["BtB", ".s.", ".. ", "...", "w=e", "...", "pBp"],
            ["BcB", "   ", "   ", "   ", "   ", "   ", " B "],
            [],
            ["   ", "   ", "   ", " L "]], lg)
        # laboratory range
        lab2 = L >= 4
        b2 = shell(d, 26, 8, 38, 15, 2 if lab2 else 1, "gable", "x", mat=SB, up=SB, gable_end=SB, ties=(29, 34))
        entrance(d, 32, Y0, 8, "south")
        d.wall_torch(31, 4, 7, "north")
        d.wall_torch(33, 4, 7, "north")
        chimney(d, 38, 13, Y0, b2["ridge"] + 1)
        d.sign(32, 5, 7, "north", ["LABORATORY"], "dark_oak")
        for x, z in ((37, 10), (37, 11), (37, 12), (37, 13)):
            keep(d, x - 1, Y0, z)
        keep(d, 36, Y0, 13)
        hot = need(d, "furnace") > 1
        ll = dict(lg, V=_it("brewing_stand"), U=_it("water_cauldron"), K=_it("crafting_table"),
                  F=_it("furnace", "west"), G=_it("furnace", "north"), C=chest("north"))
        if lab2:
            stairs(d, 28, 14, Y0, 7, "east", rails=[(28, 7, 14), (29, 7, 13), (30, 7, 13), (31, 7, 13)])
            south, south2 = ".     BBX" + ("G" if hot else "X") + "p", "      BB   "
        else:
            south, south2 = "BBBBBBB.X" + ("G" if hot else "X") + "p", "BBBBBBB    "
        plan(d, 27, 9, Y0, [
            ["utu...BBB.p",
             "..........V",
             "...ttttt..U",
             "...s.s.s..K",
             ".........." + ("F" if hot else "p"),
             south],
            [" m    oco  ",
             "           ",
             "   ovdco   ",
             "           ",
             "           ",
             south2],
            [],
            ["           ",
             "           ",
             "  L    L   "]], ll)
        if lab2:                                                      # graduate reading room upstairs
            plan(d, 27, 9, 7, [
                [".t..t..t..B",
                 ".s..s..s..B",
                 "p..wTTe...B",
                 "..........B",
                 "..   .....B",
                 "X      .CXp"],
                [" c  o  c  B",
                 "          B",
                 "    oc    B",
                 "          B",
                 "          B"],
                [],
                ["           ",
                 "           ",
                 "  L    L   "]], ll)
        pave(d, 30, 0, 30, 6, SB)
        pave(d, 34, 0, 34, 6, SB)
        pave(d, 31, 0, 33, 6, "gravel")
        bed_of(d, 27, 5, 29, 6, ("cornflower", "allium", "oxeye_daisy"))
        bed_of(d, 35, 5, 37, 6, ("oxeye_daisy", "red_tulip", "cornflower"))
        post_lamp(d, 29, 3)
        post_lamp(d, 35, 3)

    # ---------------------------------------------------------------- L3: great hall + quad
    if L >= 3:
        # quad first (ground), buildings over it
        lawn(d, 15, 16, 31, 31)
        pave(d, 22, 16, 24, 31, "gravel")
        pave(d, 15, 23, 31, 24, "gravel")
        for x, z in ((20, 23), (26, 23), (23, 19), (23, 28), (18, 24), (28, 24), (23, 17), (23, 30)):
            d.spot(x, Y0, z, "leisure")
            keep(d, x, Y0, z)
        for x, z in ((19, 19), (28, 19), (19, 28), (28, 28)):
            plant_tree(d, x, z)
        park_bench(d, 20, 21, "x", "north")
        park_bench(d, 26, 26, "x", "south")
        hedge_line(d, 17, 31, 21, 31)
        hedge_line(d, 25, 31, 29, 31)
        h = shell(d, 8, 32, 38, 40, 1, "gable", "x", mat=SB, up=SB, gable_end=SB, wh=6, ties=(12, 17, 29, 34))
        for x in (22, 23, 24):                                        # louvre on the ridge
            for z in (35, 36, 37):
                d.set(x, h["ridge"], z, "dark_oak_planks")
        for x, z in ((22, 35), (24, 35), (22, 37), (24, 37)):
            d.set(x, h["ridge"] + 1, z, "dark_oak_fence")
        d.hip(22, 35, 24, 37, h["ridge"] + 2, "deepslate_tile_stairs", "deepslate_tile_slab", overhang=0)
        for x in (10, 14, 18, 28, 32, 36):                            # buttresses (none at the doors)
            for z, f in ((31, "south"), (41, "north")):
                for y in range(Y0, 6):
                    d.set(x, y, z, SB)
                d.set(x, 6, z, st("stone_brick_stairs", f))
        link(d, 23, Y0, 32, "south")
        d.hearth(37, Y0, 36, "west", 8, "bricks", "campfire")
        chimney(d, 38, 36, Y0, h["ridge"] + 1)
        tables = "TTTTTTTT...TTTTTTTTT"
        plan(d, 9, 33, Y0, [
            ["===..nnnnnnnn...nnnnnnnnn...p",
             "wT=.." + tables + "....",
             "wT=..ssssssss...sssssssss... ",
             "wT=" + "=" * 25 + " ",
             "wT=..nnnnnnnn...nnnnnnnnn... ",
             "wT=.." + tables + "....",
             "===..ssssssss...sssssssss...p"],
            ["",
             " c    c  c  c     c  c  c   ",
             "",
             " o",
             "",
             " c    c  c  c     c  c  c   "],
            [], [], [],
            ["",
             "",
             "",
             "   L    L           L    L  "]], lg)
        for x in (16, 20, 27, 31):                                    # portraits along the south wall
            d.banner(x, 5, 39, "north", "red" if x < 23 else "blue")
        d.banner(9, 5, 35, "east", "blue")
        d.banner(9, 5, 37, "east", "blue")

    # ---------------------------------------------------------------- L4: library range + cloister
    if L >= 4:
        shell(d, 8, 16, 14, 31, 2, "gable", "z", mat=SB, up=SB, gable_end=SB, ws=2, ties=(19, 23, 27))
        link(d, 14, Y0, 23, "west")
        stairs(d, 13, 29, Y0, 7, "north", rails=[(12, 7, 26), (12, 7, 27), (12, 7, 28), (13, 7, 29)])
        press = "BB..."
        desk_ = "te..."
        plan(d, 9, 17, Y0, [
            ["BB..p", desk_, desk_, press, desk_, desk_, press, desk_, desk_, "BB.. ", "te.. ", "te.. ", "BB.. ",
             "BBB.."],
            ["BB   ", "k    ", "o    ", "BB   ", "k    ", "o    ", "BB   ", "k    ", "o    ", "BB   ", "k    ",
             "o    ", "BB   ", "BBB  "],
            ["BB   ", "", "", "BB   ", "", "", "BB   ", "", "", "BB   ", "", "", "BB   "],
            ["", "   L ", "", "", "", "   L ", "", "", "", "", "  L  "]], lg)
        plan(d, 9, 17, 7, [
            ["BBp..", "BwTe.", "BwTe.", "BwTe.", "BwTe.", "BwTe.", "B....", "B....", "B... ", "B..  ", "B..  ",
             "B..  ", "B... ", "BBXp."],
            ["BB   ", "B c  ", "B o  ", "B c  ", "B o  ", "B c  ", "B    ", "B    ", "B    ", "B    ", "B    ",
             "B    ", "B    ", "BB   "],
            [],
            ["", "", "  L  ", "", "", "", "  L  ", "", "", "", "  L  "]], lg)
        for z in range(16, 32):                                       # cloister arcade along the quad
            if z % 2:
                for y in range(Y0, 5):
                    d.set(16, y, z, "stone_brick_wall")
            d.set(16, 5, z, SB)
            d.set(15, 5, z, slab("stone_brick_slab", "top"))

    # ---------------------------------------------------------------- L5: chapel, garden, New Building
    if L >= 5:
        c = shell(d, 32, 16, 38, 31, 1, "gable", "z", mat=SB, up=SB, gable_end=SB, wh=7, ws=2, ties=(20, 24, 28))
        link(d, 32, Y0, 23, "east")
        pew = "nn=nn"
        gap = "..=.."
        plan(d, 33, 17, Y0, [
            ["p.=.u", gap, pew, gap, pew, gap, "..=nn", gap, pew, gap, pew, gap, gap, "pfTfp"],
            ["", "", "", "", "", "", "", "", "", "", "", "", "", " ccc "],
            [], [], [], [],
            ["", "", "", "  L  ", "", "", "", "  L  ", "", "", "", "  L  "]], lg)
        d.window(35, 4, 31, 35, 7, 31, "purple_stained_glass_pane")
        for x in (34, 36):                                            # bell-cote on the north gable
            d.set(x, c["ridge"] + 1, 16, "stone_brick_wall")
            d.set(x, c["ridge"] + 2, 16, "stone_brick_slab[type=bottom,waterlogged=false]")
        d.set(35, c["ridge"] + 2, 16, "stone_bricks")
        bell(d, 35, c["ridge"] + 1, 16)
        fountain(d, 23, 24, 2)
        # master's garden west of the ranges: gravel walk, beds, trees, two benches, a lamp, fence
        lawn(d, 1, 16, 6, 44)
        pave(d, 3, 16, 3, 44, "gravel")
        for z in (18, 22, 26, 30, 34, 38, 42):
            bed_of(d, 1, z, 2, z + 1, ("red_tulip", "allium", "oxeye_daisy", "cornflower"))
        for z in (20, 28, 36):
            plant_tree(d, 5, z)
        park_bench(d, 4, 24, "z", "east")
        park_bench(d, 4, 32, "z", "east")
        post_lamp(d, 4, 40)
        for z in range(16, 45):
            d.set(0, 2, z, "dark_oak_fence")
        # carriage stand on the street
        pave(d, 39, 0, 47, 3, "gravel")
        for x in (40, 43, 46):
            cart(d, x, 2)
        # the New Building: three-storey residence south of the hall, garden between
        nb = shell(d, 10, 45, 36, 52, 3, "gable", "x", mat=SB, up=SB, gable_end=SB, ties=(14, 20, 26, 32))
        arch(d, 23, Y0, 40, "south")
        lawn(d, 8, 41, 38, 44)
        pave(d, 23, 41, 24, 44, "gravel")
        bed_of(d, 9, 42, 20, 43, ("red_tulip", "oxeye_daisy", "cornflower", "allium", "oxeye_daisy", "red_tulip"))
        bed_of(d, 27, 42, 37, 43, ("allium", "cornflower", "oxeye_daisy", "red_tulip", "cornflower"))
        entrance(d, 23, Y0, 45, "south", double=True, step="gravel")
        d.wall_torch(22, 4, 44, "north")
        d.wall_torch(25, 4, 44, "north")
        d.hearth(11, Y0, 48, "east", nb["ridge"] + 2, "bricks", "campfire")
        chimney(d, 10, 48, Y0, nb["ridge"] + 1)
        chimney(d, 36, 48, Y0 + 1, nb["ridge"] + 1)
        stairs(d, 12, 51, Y0, 7, "east", rails=[(12, 7, 51), (13, 7, 50), (14, 7, 50), (15, 7, 50)])
        stairs(d, 33, 51, 7, 12, "west", rails=[(33, 12, 51), (30, 12, 50), (31, 12, 50), (32, 12, 50)])
        nl = dict(lg, Z="smoker[facing=west,lit=true]")
        # ground: junior common room (fire, sofa, games table) and the dining room with a kitchen range
        plan(d, 11, 46, Y0, [
            ["p..t....BB.p..p...tttt..X",
             " ==e...n........nnnnnnn.t",
             " ==e..wTe......wTTTTTTT.Z",
             " ==e...s........sssssss.t",
             "...t....................u",
             ".     ..BBp....BB.......X"],
            ["   l    BB        oqco   ",
             "                        k",
             "       k          c c c  ",
             "                        k",
             "   l                     ",
             "        BB     BB        "],
            [],
            ["",
             "",
             "     L     L       L     "]], nl)
        # first floor: eight study-bedrooms along the north wall, desks under the south windows
        plan(d, 11, 46, 7, [
            ["p" + "htC" * 8,
             "." + " .." * 8,
             " " + "-" * 24,
             "." * 25,
             "..   ...n..n..n..........",
             ".      .t..t..t.X.      p"],
            [" " + " k " * 8,
             "", "", "", "",
             "        o  k  o          "],
            [],
            ["", "", "      L           L      "]], nl)
        # second floor: four rooms with beds on the south wall, a desk row, the fellows' bookcases
        plan(d, 11, 46, 12, [
            ["BB..t..t..t..t..t...BBBBp",
             "....s..s..s..s..s........",
             " ." + "=" * 15 + "." * 8,
             "." * 25,
             ". ... ... ... .....   ...",
             "CHtC.HtC.HtC.HtX.      .p"],
            ["BB  c  o  c  o  c   BBBB ",
             "", "", "", "",
             "  k   k   k   k          "],
            [],
            ["", "", "   L     L     L     L   "]], dict(nl, C=chest("north")))
    return d


# ============================================================================================ Neoterra
def _ceiling(d, y, pts):
    """Recessed ceiling panels at the listed (x, z) points of the ceiling layer y."""
    for x, z in pts:
        d.set(x, y, z, "sea_lantern")


def uni_neoterra(rel, L):
    """Research campus: institute pavilion (L1) -> glass bridge & lab block (L2) -> lecture theatre and the
    green quad (L3) -> extra storeys, student union (L4) -> residence tower and sports court (L5)."""
    d = new("Neoterra", rel, (53, 40, 55), paving="smooth_stone")
    Q = "smooth_quartz"
    lg = legend(d, M="black_stained_glass_pane", g="light_gray_stained_glass", q="cake[bites=0]",
                v="brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]", u="cauldron",
                d="decorated_pot[cracked=false,facing=north,waterlogged=false]", U="water_cauldron[level=3]",
                Z="smoker[facing=south,lit=true]", O="furnace[facing=south,lit=false]",
                C=chest("east"), A="flowering_azalea", m="moss_block")
    lg[">"] = _bed("east")

    def roof_plants(y, pts, kind="A"):
        for x, z in pts:
            d.set(x, y, z, lg[kind])

    # ---------------------------------------------------------------- institute pavilion (3 storeys at L4)
    tall = L >= 4
    p = shell(d, 6, 6, 18, 14, 3 if tall else 1, "flat", glassy=True, win="nsw")
    entrance(d, 11, Y0, 6, "south", double=True)
    d.sign(12, 6, 5, "north", ["INSTITUTE OF", "SCIENCE"], "birch", glow=True, color="cyan")
    d.fill(9, 6, 3, 15, 6, 5, slab("smooth_quartz_slab", "top"))   # entrance canopy
    for x in (9, 15):
        for y in range(Y0, 6):
            d.set(x, y, 3, "quartz_pillar[axis=y]" if L >= 4 else "white_concrete")
    keep(d, 8, Y0, 7)
    keep(d, 16, Y0, 7)
    keep(d, 7, Y0, 12)
    keep(d, 16, Y0, 13)
    lg.update(Y=_hut(), Q=_it("lectern", "west"), R=_rack("north"), F=_it("furnace", "west"))
    if tall:
        stairs(d, 9, 13, Y0, 7, "east", rails=[(9, 7, 13), (10, 7, 12), (11, 7, 12), (12, 7, 12)])
        stairs(d, 16, 7, 7, 12, "west", rails=[(16, 12, 7), (13, 12, 8), (14, 12, 8), (15, 12, 8)])
        south = "R.     .B.F"
    else:
        south = "R.BBBBBBB.F"
    # reception & seminar room: seminar table for ten, hut / lectern / rack / kiln in the four corners
    plan(d, 7, 7, Y0, [
        ["Y.p.....p.Q",
         "...........",
         "...nnnnn...",
         "...TTTTT...",
         "...sssss...",
         "...........",
         south],
        ["", "", "", "    o c    ", "", "", "  o  o     " if not tall else ""]], lg)
    _ceiling(d, 6, [(9, 10), (15, 10)])
    if tall:
        # first floor: café & faculty lounge
        plan(d, 7, 7, 7, [
            ["p....     .",
             "...........",
             "w.e........",
             "wte.wTe.wTe",
             "w.e........",
             "...   .....",
             "X.      ttX"],
            ["", "", "", " o    k   k", "", "", "        oo "]], lg)
        _ceiling(d, 11, [(9, 10), (15, 10)])
        # second floor: open-plan research office
        plan(d, 7, 7, 12, [
            ["....      .",
             "......   ..",
             "...........",
             ".tt....tt..",
             ".ss....ss..",
             "...........",
             "BBp.....pBB"],
            ["", "", "", " MM    MM  ", "", "", "BB       BB"]], lg)
        _ceiling(d, 16, [(9, 10), (15, 10)])
        ry = p["top"] + 2                                             # roof garden
        for x in range(7, 18):
            d.set(x, ry, 7, "moss_block")
            d.set(x, ry, 13, "moss_block")
        roof_plants(ry + 1, [(7, 7), (12, 7), (17, 7), (7, 13), (12, 13), (17, 13)])
        roof_plants(ry, [(10, 10), (14, 10)], "p")
        d.set(16, ry, 9, "smooth_stone")
        d.set(16, ry + 1, 9, "iron_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
    pave(d, 10, 0, 13, 5, "smooth_stone")
    post_lamp(d, 4, 4)
    post_lamp(d, 20, 4)

    # ---------------------------------------------------------------- L2: glass bridge + lab block
    if L >= 2:
        nf = {2: 1, 3: 1, 4: 2, 5: 3}[L]
        b2 = shell(d, 26, 6, 40, 14, nf, "flat", glassy=True, win="nse")
        d.box(18, Y0, 8, 26, 5, 12, "glass", floor="polished_diorite")
        d.fill(18, 6, 8, 26, 6, 12, Q)
        d.clear(19, Y0, 9, 25, 5, 11)
        for x in (18, 26):
            arch(d, x, Y0, 10, "east")
        for x in (19, 21, 23, 25):
            d.set(x, Y0, 9, "potted_bamboo")
            d.set(x, Y0, 11, "potted_bamboo") if x in (21, 23) else None
            d.set(x, 6, 10, "sea_lantern")
        entrance(d, 33, Y0, 6, "south", double=True)
        d.sign(33, 6, 5, "north", ["LABS"], "birch", glow=True, color="cyan")
        for z in range(8, 13):
            keep(d, 38, Y0, z)
        hot = need(d, "furnace") > 1
        ll = dict(lg, V=_it("brewing_stand"), K=_it("crafting_table"), F=_it("furnace", "west"))
        ll["U"] = _it("water_cauldron")
        if nf >= 2:
            stairs(d, 28, 13, Y0, 7, "east", rails=[(28, 7, 13), (29, 7, 12), (30, 7, 12), (31, 7, 12)])
            south = ".     BBB...p"
        else:
            south = "BBBBBBBBB...p"
        # wet lab: fume bench on the north wall, island with stools, required stations on the east wall
        plan(d, 27, 7, Y0, [
            ["ttttt...BBB.p",
             "............V",
             "............U",
             "...tttttt...K",
             "...s.s.s...." + ("F" if hot else "."),
             "............" + ("F" if hot else "p"),
             south],
            ["vdoco   BBB  ",
             "", "",
             "    o v c    "]], ll)
        _ceiling(d, 6, [(30, 10), (36, 10)])
        if nf >= 2:                                                   # seminar room with a board
            for z in range(8, 13):
                d.set(39, 8, z, "gray_concrete")
                d.set(39, 9, z, "gray_concrete")
                d.set(39, 7, z, trap("birch", "west"))
            plan(d, 27, 7, 7, [
                ["p...........p",
                 "..wt..wt.... ",
                 "..wt..wt.... ",
                 "..wt..wt..te ",
                 "..wt..wt.... ",
                 "..   ....... ",
                 "p      " + ("     ." if nf >= 3 else ".....X")],
                ["", "   k   k     ", "   o   o     ", "   k   k  k  ", "   o   o     "]], lg)
            _ceiling(d, 11, [(30, 10), (35, 10)])
        if nf >= 3:                                                   # two glass-walled offices
            stairs(d, 38, 13, 7, 12, "west", rails=[(35, 12, 12), (36, 12, 12), (37, 12, 12), (38, 12, 13)])
            plan(d, 27, 7, 12, [
                ["BBtt.pgp.tt.B",
                 "..s...g..s..B",
                 "......g.....B",
                 "wte...g.wte..",
                 "......g......",
                 "........   ..",
                 "pX....      p"],
                ["BBMM..g..MM.B", "      g     B", "      g     B", " o    g   o  ", "      g      "],
                ["      g", "      g", "      g", "      g", "      g"],
                ["      g", "      g", "      g", "      g", "      g"]], lg)
            _ceiling(d, 16, [(30, 10), (36, 10)])
        if nf >= 2:                                                   # solar array on the lab roof
            ry = b2["top"] + 2
            for z in (8, 9, 11, 12):
                for x in range(28, 39):
                    d.set(x, ry, z, "daylight_detector[inverted=false,power=0]")
            d.set(39, ry, 7, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        plant_tree(d, 22, 3)
        if L < 5:
            plant_tree(d, 44, 3)

    # ---------------------------------------------------------------- L3: green quad + lecture theatre
    if L >= 3:
        lawn(d, 6, 16, 46, 36)
        pave(d, 25, 15, 27, 37, "smooth_stone")
        pave(d, 6, 26, 46, 26, "smooth_stone")
        for x in (24, 28):                                            # andesite kerbs along the main walk
            pave(d, x, 16, x, 25, "polished_andesite")
            pave(d, x, 27, x, 36, "polished_andesite")
        for x, z in ((17, 26), (21, 26), (31, 26), (35, 26), (26, 19), (26, 22), (26, 30), (26, 34)):
            d.spot(x, Y0, z, "leisure")
            keep(d, x, Y0, z)
        trees = [(18, 20), (34, 32), (21, 32), (31, 20)]
        if L < 4:
            trees += [(10, 20), (10, 32)]
        if L < 5:
            trees += [(42, 20), (42, 32)]
        for x, z in trees:
            plant_tree(d, x, z)
        park_bench(d, 19, 24, "x", "north")
        park_bench(d, 32, 24, "x", "north")
        park_bench(d, 19, 28, "x", "south")
        park_bench(d, 32, 28, "x", "south")
        if L >= 4:
            fountain(d, 26, 26, 2)
        X1, X2, Z1, Z2 = 14, 38, 38, 47
        shell(d, X1, Z1, X2, Z2, 1, "flat", wh=8, win="s", ws=4)
        for x in range(X1, X2 + 1):
            d.set(x, 9, Z1, "cyan_terracotta")
        entrance(d, 26, Y0, Z1, "north", double=True)
        for k in range(3):                                            # raked tiers rising south
            zs = Z1 + 4 + 2 * k
            for z in (zs, zs + 1):
                for x in range(X1 + 1, X2):
                    for y in range(Y0, Y0 + k):
                        d.set(x, y, z, Q)
            for x in range(17, 36):                                   # one row of 16 seats, aisles at 20/26/32
                if x not in (20, 26, 32):
                    d.chair(x, Y0 + k, zs, "south", "birch")
        for x in range(18, 35):                                       # projection screen
            d.set(x, 6, Z1 + 1, "black_concrete")
            d.set(x, 7, Z1 + 1, "black_concrete")
        d.set(26, 8, Z1 + 1, "sea_lantern")
        d.set(22, Y0, 40, Q)                                          # speaker's desk with a lamp
        d.set(23, Y0, 40, Q)
        d.set(22, Y0 + 1, 40, "lantern[hanging=false,waterlogged=false]")
        for x in (15, 37):                                            # book walls flanking the stage
            for z in range(39, 44):
                for y in range(Y0, Y0 + 3):
                    d.bookshelf(x, y, z)
        _ceiling(d, 10, [(20, 43), (26, 43), (32, 43)])

    # ---------------------------------------------------------------- L4: student union
    if L >= 4:
        un = shell(d, 6, 17, 14, 34, 2, "flat", glassy=True, win="nsew")
        entrance(d, 14, Y0, 25, "west", double=True, along="z")
        d.sign(14, 6, 21, "east", ["STUDENT", "UNION"], "birch", glow=True, color="cyan")
        stairs(d, 8, 33, Y0, 7, "east", rails=[(8, 7, 33), (9, 7, 32), (10, 7, 32), (11, 7, 32)])
        table = "..wTe.."
        plan(d, 7, 18, Y0, [
            ["ZtUtOtX", ".......", "..TTT..", ".......", "tttt...", "......."] + [table] * 8 +
            ["p.....p", ".     ."],
            [" o k  o", "", "  qoc  ", "", "o  k", "", "  c", "", "  o", "", "  c", "", "  o", ""]], lg)
        _ceiling(d, 6, [(10, 20), (10, 25), (10, 30)])
        plan(d, 7, 18, 7, [
            ["BBp.pBB", "..ttt..", ".sssss.", ".......", ".......", ".......", ".wTTe..", ".wTTe..",
             ".......", ".......", ".wTTe..", ".wTTe..", ".......", "p.....p", "..   ..", "X      "],
            ["BB   BB", "  o k  ", "", "", "", "", "  ck", "  oc", "", "", "  ck", "  oc"]], lg)
        _ceiling(d, 11, [(10, 20), (10, 26), (10, 31)])
        ry = un["top"] + 2
        for z in range(18, 34):
            d.set(7, ry, z, "moss_block")
            d.set(13, ry, z, "moss_block")
        roof_plants(ry + 1, [(7, 18), (13, 18), (7, 25), (13, 25), (7, 33), (13, 33)])
        roof_plants(ry, [(10, 21), (10, 25), (10, 29)], "p")

    # ---------------------------------------------------------------- L5: residence tower + sports court
    if L >= 5:
        dt = shell(d, 38, 17, 46, 34, 6, "flat", glassy=True, win="nsew")
        entrance(d, 38, Y0, 25, "east")
        d.sign(38, 6, 24, "west", ["RESIDENCE"], "birch", glow=True, color="cyan")
        for k in range(5):
            y0 = Y0 + 5 * k
            if k % 2 == 0:
                stairs(d, 39, 19, y0, y0 + 5, "south",
                       rails=[(39, y0 + 5, 19), (40, y0 + 5, 20), (40, y0 + 5, 21), (40, y0 + 5, 22)])
            else:
                stairs(d, 45, 32, y0, y0 + 5, "north",
                       rails=[(45, y0 + 5, 32), (44, y0 + 5, 29), (44, y0 + 5, 30), (44, y0 + 5, 31)])
        plan(d, 39, 18, Y0, [                                         # lobby with sofas and a porter's desk
            [".......", " ......", " .nnn.p", " ..t...", " .sss..", " ......", ".......", ".......",
             ".......", ".ttt...", "..s....", "XXX..BB", "......B", ".....pB", ".......", "p.....p"],
            ["", "", "", "   o", "", "", "", "", "", " Mko", "", "     BB", "      B"]], lg)
        # five upper storeys, each its own use (stairs alternate west / east, so holes differ per floor)
        tw = dict(lg, H=_bed("south", "yellow"), h=_bed("west", "lime"), I="white_stained_glass_pane",
                  G="gray_concrete")
        plan(d, 39, 18, 7, [                                          # 1st: quiet study library
            ["pBBBBBp", " ......", "  .wTe.", "  .....", "  .wTe.", " ......", ".......", "BB...BB",
             "p.nnn.B", "..TTT.B", "..sss. ", "B..... ", "Bw=t=e ", "B.===. ", "B..... ", "BBp...."],
            [" BBBBB ", "", "    l", "", "    l", "", "", "BB   BB", "      B", "  coc B", "", "B", "B  k",
             "B", "B", "BB"],
            [" BBBBB ", "", "", "", "", "", "", "BB   BB", "      B", "      B", "", "B", "B", "B", "B", "BB"]],
            tw)
        _ceiling(d, 11, [(42, 21), (42, 27), (42, 31)])
        plan(d, 39, 18, 12, [                                         # 2nd: student flat – kitchen & dorm
            [".tZtU.p", " .....t", " ..nn.t", " .wTTe.", " ..ss..", " ......", ".......", "t....XC",
             "h .....", "t.==...", "h ==.  ", "t.==.  ", "h ...  ", "t....  ", "h .... ", "t..BBX."],
            [" o d", "      o", "", "   co", "", "", "", "k", "", "k", "", "k", "", "k", "", "k  BB"]], tw)
        _ceiling(d, 16, [(42, 20), (42, 25), (42, 30)])
        plan(d, 39, 18, 17, [                                         # 3rd: computer lab & seminar table
            ["ptttttp", " .ssss.", "  .....", "  ....B", "  ....B", " .....B", ".......", ".nnnnn.",
             "wTTTTTe", "wTTTTTe", ".sssss ", "...... ", "B..... ", "B..XX. ", "p..... ", "BBBp..."],
            [" MMMMM ", "", "", "      B", "      B", "      B", "", "", " c o c", " o c o", "", "", "B",
             "B", "", "BBB"],
            ["", "", "", "      B", "      B", "      B", "", "", "", "", "", "", "B", "B", "", "BBB"]], tw)
        _ceiling(d, 21, [(42, 19), (42, 26), (42, 31)])
        plan(d, 39, 18, 22, [                                         # 4th: graduate flat – lounge & 2 rooms
            [".pBBBp.", " ......", " .nnn..", " .=t=..", " .sss..", " ......", ".......", "III.III",
             "C.....X", "C......", "te.... ", "....=  ", "te..=  ", ".....  ", ".  .   ", "tHHtHHt"],
            ["  BBB", "", "", "   o", "", "", "", "III III", "", "", "l", "", "l", "", "", "k  k  k"],
            ["", "", "", "", "", "", "", "III III"], ["", "", "", "", "", "", "", "III III"]], tw)
        _ceiling(d, 26, [(42, 21), (41, 29), (44, 29)])
        plan(d, 39, 18, 27, [                                         # 5th: sky lounge with a bar
            ["XtttttX", " .sss..", "  .....", "  ....A", "  .....", " ......", ".......", "A.nnn.A",
             "w.=t=.e", "w.===.e", "..sss..", ".......", ".......", ".wTe..A", ".......", "AB.p.BA"],
            [" oqdo", "", "", "", "", "", "", "", "   o", "", "", "", "", "  l", "", " B   B"]], tw)
        _ceiling(d, 31, [(42, 21), (42, 27), (42, 32)])
        _ceiling(d, 6, [(42, 22), (42, 29)])
        ry = dt["top"] + 2
        for z in (19, 20, 22, 23, 25, 26, 28, 29, 31, 32):
            for x in range(40, 45):
                d.set(x, ry, z, "daylight_detector[inverted=false,power=0]")
        d.set(39, ry, 18, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        for x in range(42, 52):                                       # sports court beside the street
            for z in range(1, 15):
                edge = x in (42, 51) or z in (1, 14) or z == 8
                d.set(x, 1, z, "white_concrete" if edge else "light_blue_terracotta")
        for z in (2, 13):
            d.set(46, 2, z, "iron_bars")
            d.set(46, 3, z, "iron_bars")
            d.set(46, 4, z, "white_stained_glass")
            d.set(47, 2, z, "iron_bars")
            d.set(47, 3, z, "iron_bars")
            d.set(47, 4, z, "white_stained_glass")
        for x in (43, 50):
            d.set(x, 2, 8, "birch_fence")
            d.set(x, 3, 8, "white_banner[rotation=0]")
    return d



# ============================================================================================ Cascadia
def uni_cascadia(rel, L):
    """Timber college: study lodge with a porch (L1) -> chemistry cabin & covered boardwalk (L2) -> lecture
    lodge and the campfire quad (L3) -> reading lodge, bunkhouse, lodge loft (L4) -> mess hall, fire lookout,
    faculty lodge and a boardwalk round the whole quad (L5)."""
    d = new("Cascadia", rel, (53, 30, 55), paving="coarse_dirt")
    lg = legend(d, h=_bed("north"), u="cauldron", q="cake[bites=0]", m="potted_red_mushroom",
                d="decorated_pot[cracked=false,facing=north,waterlogged=false]", U="water_cauldron[level=3]",
                v="brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]",
                Z="smoker[facing=south,lit=true]", O="furnace[facing=south,lit=false]", C=chest("south"),
                P="cartography_table")
    lg["<"] = _bed("west")
    LOGY = log("spruce_log")

    # ---------------------------------------------------------------- study lodge with porch (loft at L4)
    loft = L >= 4
    b = shell(d, 6, 6, 18, 14, 2 if loft else 1, "gable", "x", ties=(10, 14))
    entrance(d, 12, Y0, 6, "south")
    d.fill(5, 1, 2, 19, 1, 5, "spruce_planks")                       # porch deck, posts, lean-to roof
    for x in (5, 9, 15, 19):
        for y in range(Y0, 6):
            d.set(x, y, 2, LOGY)
    for x in range(4, 21):
        d.set(x, 6, 1, st("spruce_stairs", "south"))
        for z in range(2, 6):
            d.set(x, 6, z, slab("spruce_slab"))
    for x in (6, 7, 8, 16, 17, 18):                                   # porch rail between the posts
        d.set(x, Y0, 2, "spruce_fence")
    d.set(12, 5, 4, "lantern[hanging=true,waterlogged=false]")
    d.set(7, 5, 4, "lantern[hanging=true,waterlogged=false]")
    d.set(17, 5, 4, "lantern[hanging=true,waterlogged=false]")
    d.chair(14, Y0, 5, "north", "spruce", sit=False)                  # porch bench by the door
    d.chair(15, Y0, 5, "north", "spruce", sit=False)
    d.set(16, Y0, 5, "barrel[facing=up,open=false]")
    d.set(8, Y0, 5, "potted_fern")
    d.sign(12, 5, 5, "north", ["TIMBERLINE", "COLLEGE"], "spruce")
    d.hearth(12, Y0, 13, "north", b["ridge"] + 1, "cobblestone", "campfire")
    chimney(d, 12, 14, Y0, b["ridge"] + 1)
    keep(d, 8, Y0, 7)
    keep(d, 16, Y0, 7)
    keep(d, 7, Y0, 12)
    keep(d, 16, Y0, 13)
    lg.update(Y=_hut(), Q=_it("lectern", "west"), R=_rack("north"), F=_it("furnace", "west"))
    if loft:
        stairs(d, 16, 8, Y0, 7, "south", rails=[(16, 7, 8), (15, 7, 9), (15, 7, 10), (15, 7, 11),
                                                 (17, 7, 9), (17, 7, 10), (17, 7, 11)])
    sc = " " if loft else "."
    west = "B" if L >= 2 else "."
    # common room: long study table, two chairs at the fire, lectern, rack, stove and books
    plan(d, 7, 7, Y0, [
        ["Y.p.....p.Q",
         west + ".nnn.nnn" + sc + ".",
         west + ".TTTTTTT" + sc + ".",
         west + ".sssssss" + sc + ".",
         west + "...n.n.." + sc + ".",
         "...=====" + "." + sc + ".",
         "R.BB   BB.F"],
        ["",
         "",
         "   c   c",
         "",
         "",
         "",
         "  BB   BB  " if L >= 2 else ""],
        [],
        ["", "", "", "   L   L"]], lg)
    if loft:                                                          # sleeping loft for first-years
        plan(d, 7, 7, 7, [
            ["hthChthC...",
             " . . . .. .",
             "........   ",
             ".=====..   ",
             "........   ",
             "te....... .",
             "XBB.. .BB p"],
            [" k   k", "", "", "", "", "o", " BB   BB"],
            [], [],
            ["", "", "", "   L   L"]], lg)
    bed_of(d, 1, 3, 3, 5, ("fern", "blue_orchid", "fern", "lily_of_the_valley"))
    post_lamp(d, 21, 4)

    # ---------------------------------------------------------------- L2: chemistry cabin + boardwalk
    if L >= 2:
        b2 = shell(d, 30, 6, 42, 14, 1, "gable", "x", ties=(34, 38))
        entrance(d, 36, Y0, 6, "south")
        d.sign(36, 5, 5, "north", ["CHEMISTRY"], "spruce")
        chimney(d, 42, 10, Y0, b2["ridge"] + 1)
        for z in range(8, 13):
            keep(d, 40, Y0, z)
        hot = need(d, "furnace") > 1
        cl = dict(lg, V=_it("brewing_stand"), K=_it("crafting_table"), F=_it("furnace", "west"))
        cl["U"] = _it("water_cauldron")
        plan(d, 31, 7, Y0, [
            ["utu...BBB.p",
             "..........V",
             "..........U",
             "..TTTTT...K",
             "..s.s.s..." + ("F" if hot else "."),
             ".........." + ("F" if hot else "p"),
             "BBBBBBB...p"],
            [" m    oko  ",
             "", "",
             "  vdcko",
             "", "",
             "BBBBBBB"],
            [],
            ["", "", "", "   L   L"]], cl)
        # covered boardwalk between the two cabins
        for x in range(19, 30):
            for z in range(8, 13):
                d.set(x, 1, z, "spruce_planks")
                d.set(x, 6, z, slab("spruce_slab"))
        for x in range(19, 30):
            for z in (8, 12):
                d.set(x, Y0, z, "spruce_fence")
        for x in (19, 22, 25, 28):
            for z in (8, 12):
                for y in range(Y0, 6):
                    d.set(x, y, z, LOGY)
        for z in (8, 12):                                             # side openings onto the yard
            d.set(24, Y0, z, AIR)
        link(d, 18, Y0, 10, "east")
        link(d, 30, Y0, 10, "west")
        for x in (21, 24, 27):
            d.set(x, 5, 10, "lantern[hanging=true,waterlogged=false]")
        trees = [(22, 3), (27, 3)] + ([(46, 4)] if L < 5 else [])
        for x, z in trees:
            plant_tree(d, x, z)

    # ---------------------------------------------------------------- L3: lecture lodge + campfire quad
    if L >= 3:
        lawn(d, 6, 16, 46, 36)
        for x, z in ((8, 18), (9, 18), (12, 31), (13, 31), (30, 19), (31, 19), (31, 20), (40, 33), (41, 33),
                     (36, 21), (44, 29), (19, 34), (20, 34)):
            d.set(x, 1, z, "moss_block")
        pave(d, 24, 15, 26, 37, "spruce_planks")
        cx, cz = 19, 26                                               # campfire ring with log seats
        d.fill(cx - 1, 1, cz - 1, cx + 1, 1, cz + 1, "gravel")
        d.set(cx, 1, cz, "cobblestone")
        d.set(cx, Y0, cz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        for (x, z, ax) in ((cx - 3, cz, "z"), (cx + 3, cz, "z"), (cx, cz - 3, "x"), (cx, cz + 3, "x"),
                           (cx - 3, cz - 1, "z"), (cx + 3, cz + 1, "z")):
            d.set(x, Y0, z, log("stripped_spruce_log", ax))
        for x, z in ((17, 24), (21, 24), (17, 28), (21, 28), (32, 22), (36, 28), (25, 20), (25, 32)):
            d.spot(x, Y0, z, "leisure")
            keep(d, x, Y0, z)
        trees = [(34, 18), (20, 18)]
        if L < 4:
            trees += [(9, 33), (42, 24)]
        if L < 5:
            trees += [(30, 33)]
        for x, z in trees:
            plant_tree(d, x, z)
        lec = shell(d, 12, 38, 38, 46, 1, "gable", "x", wh=5, ties=(17, 23, 29, 35))
        entrance(d, 25, Y0, 38, "south", double=True)
        d.hearth(37, Y0, 42, "west", 7, "cobblestone", "campfire")
        chimney(d, 38, 42, Y0, lec["ridge"] + 1)
        for z in range(40, 45):                                       # chalkboard on the west wall
            d.set(13, Y0 + 1, z, "black_concrete")
            d.set(13, Y0 + 2, z, "black_concrete")
            d.set(13, Y0, z, trap("spruce", "east"))
        cols = "e.e.e.e...e.e.e.e.e"
        plan(d, 13, 39, Y0, [
            ["p...." + cols + "B",
             " ...." + cols + "B",
             " ...." + cols + " ",
             " .T.." + "." * 19 + " ",
             " ...." + cols + " ",
             " ...." + cols + "B",
             "p...." + cols + "B"],
            ["                        B", "                        B", "", "  l", "", "                        B",
             "                        B"],
            ["                        B", "                        B", "", "", "", "                        B",
             "                        B"],
            [],
            ["", "", "", "    L     L     L     L"]], lg)

    # ---------------------------------------------------------------- L4: reading lodge + bunkhouse
    if L >= 4:
        shell(d, 6, 17, 13, 34, 2, "gable", "z", ties=(20, 25, 30))
        entrance(d, 13, Y0, 25, "west")
        stairs(d, 8, 22, Y0, 7, "south", rails=[(8, 7, 22), (7, 7, 23), (7, 7, 24), (7, 7, 25),
                                                 (9, 7, 23), (9, 7, 24), (9, 7, 25)])
        plan(d, 7, 18, Y0, [
            ["B....p", "B...wt", "B.....", "B...wt", "B ....", "B ..wt", "B ....", "B ....", "B ....",
             "B.....", "BwTewt", "BwTe..", "BwTewt", "BwTe..", "B...wt", "BB..pX"],
            ["B", "B    k", "B", "B    o", "B", "B    k", "B", "B", "B", "B", "B c  o", "B", "B o  k", "B c",
             "B    k", "BB"],
            ["B", "B", "B", "B", "B", "B", "B", "B", "B", "B", "B", "B", "B", "B", "B", "B"],
            ["", "", "   L", "", "", "", "", "", "   L", "", "", "", "", "   L"]], lg)
        plan(d, 7, 18, 7, [
            ["BB..BB", "...P..", "...s..", "......", ". ....", "   ...", "   ...", "   ...", ". ....",
             ". ....", "...wTe", "...wTe", "...wTe", "...wTe", "...wTe", "BB.pBB"],
            ["BB  BB", "", "", "", "", "", "", "", "", "", "    c", "    o", "    c", "    o", "    c",
             "BB  BB"],
            [],
            ["", "", "   L", "", "", "", "", "   L", "", "", "", "", "   L"]], lg)
        bunk2 = L >= 5
        bk = shell(d, 38, 17, 46, 34, 2 if bunk2 else 1, "gable", "z", ties=(21, 29))
        entrance(d, 38, Y0, 25, "east")
        d.hearth(45, Y0, 30, "west", bk["ridge"] + 1, "cobblestone", "campfire")
        chimney(d, 46, 30, Y0, bk["ridge"] + 1)
        if bunk2:
            stairs(d, 45, 19, Y0, 7, "south", rails=[(45, 7, 19), (44, 7, 20), (44, 7, 21), (44, 7, 22)])
            east = [".", " ", " ", " ", " ", " "]
        else:
            east = ["C", "C", "C", "X", "C", "p"]
        rows = ["t....." + east[0], "< ...." + east[1], "t....." + east[2], "< ...." + east[3],
                "t....." + east[4], "< ...." + east[5], "t......", ".......", "C.....X", "< .....",
                "t......", "< ..w. ", "t...w. ", "< ..w. ", "t......", "< ...XX"]
        bl = dict(lg, C=chest("east"))
        plan(d, 39, 18, Y0, [rows,
                             ["k", "", "k", "", "k", "", "k", "", "", "", "k", "", "k", "", "k"],
                             [],
                             ["", "", "", "   L", "", "", "", "", "", "", "", "   L"]], bl)
        if bunk2:
            plan(d, 39, 18, 7, [
                ["B.t.t..", "B.s.s. ", "B....  ", "p....  ", "B....  ", "B..... ", "...... ", ".......",
                 "< ....C", "t......", "< .....", "t......", "< .... ", "t......", "< .....", "t...XXC"],
                ["B k o", "", "B", "", "B", "B", "", "", "", "k", "", "k", "", "k", "", "k"],
                [],
                ["", "", "", "   L", "", "", "", "", "", "", "", "   L"]], bl)

    # ---------------------------------------------------------------- L5: mess hall, lookout, faculty lodge
    if L >= 5:
        mh = shell(d, 44, 4, 52, 15, 1, "gable", "z", ties=(8, 12))
        entrance(d, 48, Y0, 4, "south")
        d.sign(48, 5, 3, "north", ["MESS HALL"], "spruce")
        d.hearth(48, Y0, 14, "north", mh["ridge"] + 1, "cobblestone", "campfire")
        chimney(d, 48, 15, Y0, mh["ridge"] + 1)
        plan(d, 45, 5, Y0, [
            ["ZtU.tOX", ".......", ".TT....", ".......", ".......", "wTe.wTe", "wTe.wTe", "wTe.wTe",
             "wTe.wTe", "p.   .p"],
            [" o  k", "", " qo", "", "", " c   o", " o   c", " c   o", " o   c"],
            [],
            ["", "", "", "   L", "", "", "", "   L"]], lg)
        tx1, tz1 = 31, 30                                             # fire-lookout tower at the quad corner
        for x, z in ((tx1, tz1), (tx1 + 4, tz1), (tx1, tz1 + 4), (tx1 + 4, tz1 + 4)):
            for y in range(Y0, 16):
                d.set(x, y, z, LOGY)
        for y in (7, 12):
            for a in range(1, 4):
                for (x, z, ax) in ((tx1 + a, tz1, "x"), (tx1 + a, tz1 + 4, "x"), (tx1, tz1 + a, "z"),
                                   (tx1 + 4, tz1 + a, "z")):
                    d.set(x, y, z, log("spruce_log", ax))
        d.fill(tx1, 15, tz1, tx1 + 4, 15, tz1 + 4, "spruce_planks")
        for x in range(tx1, tx1 + 5):
            for z in (tz1, tz1 + 4):
                d.set(x, 16, z, "spruce_fence")
        for z in range(tz1 + 1, tz1 + 4):
            for x in (tx1, tx1 + 4):
                d.set(x, 16, z, "spruce_fence")
        d.hip(tx1, tz1, tx1 + 4, tz1 + 4, 19, "dark_oak_stairs", "dark_oak_slab", overhang=1)
        for x, z in ((tx1, tz1), (tx1 + 4, tz1), (tx1, tz1 + 4), (tx1 + 4, tz1 + 4)):
            for y in range(16, 19):
                d.set(x, y, z, LOGY)
        d.set(tx1 + 2, 19, tz1 + 2, "spruce_planks")
        bell(d, tx1 + 2, 18, tz1 + 2)
        d.set(tx1 + 2, Y0, tz1 + 2, "hay_block[axis=y]")              # water barrel & hay at its foot
        d.set(tx1 + 1, Y0, tz1 + 1, "barrel[facing=up,open=false]")
        # faculty lodge: two studies either side of a board wall, common room with a fire, bedrooms above
        fl = shell(d, 40, 39, 52, 51, 2, "gable", "x", ties=(44, 48))
        entrance(d, 48, Y0, 39, "south")
        d.hearth(51, Y0, 48, "west", fl["ridge"] + 2, "cobblestone", "campfire")
        chimney(d, 52, 48, Y0, fl["ridge"] + 1)
        stairs(d, 42, 50, Y0, 7, "east", rails=[(42, 7, 50), (43, 7, 49), (44, 7, 49), (45, 7, 49)])
        arch(d, 46, Y0, 42, "east")
        fw = dict(lg, **{"#": "spruce_planks"})
        plan(d, 41, 40, Y0, [
            ["BttBp#p..tB", ".s...#...sB", "..........B", "wte..#.....", ".....#.....", "p...X#C...p",
             "...........", "...nnnnn.. ", "...TTTTT.. ", "...sssss.. ", ".     .BBpX"],
            ["BkoB #   kB", "     #    B", "          B", " o   #", "     #", "     #", "", "", "    c c",
             "", "       BB"],
            ["     #", "     #", "", "     #", "     #", "     #"],
            ["     #", "     #", "     #", "  L  #  L", "     #", "     #", "", "     L"]], fw)
        plan(d, 41, 40, 7, [
            ["Cht.ht.ht.h", ". .. .. .. ", "...........", ".=========.", "...........", "...........",
             "te.........", "te.........", ".......... ", "X.   ......", "X      .BBp"],
            ["  k  k  k", "", "", "", "", "", "o", "k", "", "", "        BB"],
            [],
            ["", "", "", "", "", "   L   L"]], fw)
        # covered boardwalk round the quad
        for x in range(14, 38):
            for z in (15, 37):
                d.set(x, 1, z, "spruce_planks")
                d.set(x, 6, z, slab("spruce_slab"))
        for z in range(15, 38):
            for x in (14, 37):
                d.set(x, 1, z, "spruce_planks")
                d.set(x, 6, z, slab("spruce_slab"))
        for x in (14, 18, 22, 30, 34, 37):
            for z in (15, 37):
                for y in range(Y0, 6):
                    d.set(x, y, z, LOGY)
        for z in (19, 23, 27, 31):
            for x in (14, 37):
                for y in range(Y0, 6):
                    d.set(x, y, z, LOGY)
        for x in (16, 20, 28, 32):
            d.set(x, 5, 15, "lantern[hanging=true,waterlogged=false]")
            d.set(x, 5, 37, "lantern[hanging=true,waterlogged=false]")
        for z in (21, 29):
            d.set(14, 5, z, "lantern[hanging=true,waterlogged=false]")
            d.set(37, 5, z, "lantern[hanging=true,waterlogged=false]")
    return d


@design("university")
def university_v2(pack, rel, L):
    return common_materials({"Hearthwood": uni_hearthwood, "Cascadia": uni_cascadia, "Neoterra": uni_neoterra}[pack](rel, L))
