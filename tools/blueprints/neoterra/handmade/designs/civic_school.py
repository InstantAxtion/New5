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


# ============================================================================================== HEARTHWOOD
# Victorian village school: brick-and-plaster schoolroom with bell-cote and gabled porch (L1), infants' room and
# walled playground (L2), art room with library loft (L3), the schoolmaster's house and the school hall (L4),
# junior school with music room, kitchen/canteen block, playing field and school garden (L5).
def sch_hearthwood(rel, L):
    d = new("Hearthwood", rel, (49, 28, 49))
    OAK = "oak"
    # ------------------------------------------------------------------ shells (all levels first)
    A = shell(d, 16, 8, 30, 16, 1, "gable", "x", win="nsw", ws=3, beams=(19, 23, 27))
    if L >= 2:
        shell(d, 30, 8, 38, 16, 1, "gable", "z", win="nse", beams=(10, 14))
    if L >= 3:
        shell(d, 18, 16, 26, 25, 2, "gable", "z", win="we", mat="bricks", up="yellow_terracotta", beams=(19, 23))
    if L >= 4:
        shell(d, 2, 6, 14, 18, 2, "gable", "z", win="nse", mat="bricks", up="yellow_terracotta", beams=(9, 15))
        shell(d, 14, 26, 30, 36, 1, "gable", "x", wh=6, beams=(18, 22, 26))
    if L >= 5:
        shell(d, 2, 22, 12, 36, 2, "gable", "z", mat="yellow_terracotta", up="yellow_terracotta", beams=(26, 32))
        shell(d, 30, 32, 40, 40, 2, "gable", "z", win="nse", mat="bricks", up="yellow_terracotta", beams=(35, 38))

    # ------------------------------------------------------------------ A: the schoolroom (L1+)
    entry(d, 27, Y0, 8, "south", step="stone_bricks")
    for x in (26, 28):                                                  # gabled entrance porch
        for y in (2, 3):
            d.set(x, y, 5, "oak_fence")
    d.fill(26, 4, 5, 28, 4, 5, log("stripped_oak_log", "x"))
    d.fill(26, 5, 5, 28, 5, 7, "oak_planks")
    d.gable(26, 5, 28, 7, 6, "z", "brick_stairs", "brick_slab", "yellow_terracotta", overhang=0)
    d.fill(26, 1, 5, 28, 1, 7, "stone_bricks")
    d.sign(27, 4, 4, "north", ["VILLAGE", "SCHOOL", "est. 1872"], "oak")
    d.set(27, 4, 7, LANT)                                               # porch lantern under the gable
    rg = A["ridge"]
    for z in (11, 13):                                                  # bell-cote on the west gable
        d.set(16, rg + 1, z, "brick_wall")
    d.fill(16, rg + 2, 11, 16, rg + 2, 13, slab("brick_slab"))
    d.set(16, rg + 2, 12, "bricks")
    bell(d, 16, rg + 1, 12, "east")
    d.hut(29, Y0, 9)
    keep(d, 28, Y0, 9)
    # schoolroom: board on the west wall, master's desk, two double columns of pupils' desks facing it,
    # bookcase and coal fire on the east gable wall, coat hooks by the door
    board(d, [(17, 11), (17, 12)], Y0 + 1, "east", ledge=OAK)
    plan(d, Y0, 17, 9, [
        # 17 .. 29
        ".............",   # z9  entry row (door at x27, hut at x29)
        "..t.De.De...B",   # z10
        "..t.De.De...B",   # z11
        ".ct.De.De....",   # z12
        "....De.De...X",   # z13
        "....De.De...F",   # z14
        "...........wX",   # z15
    ], {"t": tslab("oak_slab"), "c": seat("west", OAK), "D": tslab("spruce_slab"), "e": seat("east", OAK),
        "B": shelf, "X": "bricks", "F": "campfire[facing=west,lit=true,signal_fire=false,waterlogged=false]",
        "w": log("oak_log", "z")})
    d.spot(18, Y0, 11, "work")
    plan(d, Y0 + 1, 17, 10, [
        "..i.........B",   # z10: candle on the master's desk, bookcase 2nd shelf
        "..p.........B",   # z11
        "............X",   # z12 .. mantel
        "............X",
        "............X",
    ], {"i": candle(2), "p": "potted_red_tulip", "B": shelf, "X": "bricks"})
    d.set(29, Y0 + 2, 13, candle(1))
    d.set(29, Y0 + 2, 15, candle(1))
    for x in (22, 23, 25, 26):                                          # coat hooks on the north wall
        d.set(x, Y0 + 1, 9, "tripwire_hook[attached=false,facing=south,powered=false]")
    d.banner(20, 4, 15, "north", "yellow")
    d.banner(24, 4, 15, "north", "blue")
    for x in (19, 23, 27):                                              # lanterns hung from the tie beams
        d.set(x, 5, 12, LANT)
    # street front: shutters and flower boxes on the three schoolroom windows, a flower border, lamp posts
    for x, f in ((18, "red_tulip"), (21, "oxeye_daisy"), (24, "cornflower")):
        shutters(d, x, 3, 8, "north", "warped")
        window_box(d, x, 3, 8, "north", f)
    for z in (10, 13):
        shutters(d, 16, 3, z, "west", "warped")
    ground(d, 26, 0, 28, 4, "gravel")
    flowers(d, [(17, 6), (18, 6), (19, 6), (20, 6), (21, 6), (22, 6), (23, 6), (24, 6)],
            ["rose_bush[half=lower]", "red_tulip", "oxeye_daisy", "peony[half=lower]", "cornflower", "allium",
             "red_tulip", "azure_bluet"])
    for x in (17, 20):
        d.set(x, 3, 6, "rose_bush[half=upper]" if x == 17 else "peony[half=upper]")
    lamp_post(d, 25, 3)
    lamp_post(d, 29, 3)
    d.sign(25, 3, 2, "north", ["Headmaster", "Mr. Pryce"], "oak")

    # ------------------------------------------------------------------ B: infants' room + playground (L2+)
    if L >= 2:
        link(d, 30, Y0, 12, "east")
        entry(d, 34, Y0, 16, "north", step="stone_bricks")
        # two low tables with stools, a story corner with a rug and the teacher's chair, toy chest and xylophone
        plan(d, Y0, 31, 9, [
            # 31..37
            "p.n.~~~",     # z9
            ".wTe~~c",     # z10
            "..s.~~~",     # z11
            ".......",     # z12 (link door enters at x31)
            "..n...N",     # z13
            ".wTe..C",     # z14
            "..s...K",     # z15
        ], {"p": "potted_azure_bluet", "n": seat("north", OAK), "s": seat("south", OAK), "w": seat("west", OAK),
            "e": seat("east", OAK), "T": "oak_fence", "~": "light_blue_carpet", "c": seat("east", "spruce"),
            "N": "note_block[instrument=xylophone,note=0,powered=false]",
            "C": "chest[facing=west,type=single,waterlogged=false]", "K": "barrel[facing=up,open=false]"})
        d.set(33, Y0 + 1, 10, "oak_pressure_plate[powered=false]")
        d.set(33, Y0 + 1, 14, "oak_pressure_plate[powered=false]")
        d.set(37, Y0 + 1, 15, "potted_oxeye_daisy")
        d.banner(32, 4, 9, "south", "lime")
        d.banner(36, 4, 15, "north", "pink")
        d.set(34, 5, 10, LANT)
        d.set(34, 5, 14, LANT)
        d.sign(34, 5, 7, "north", ["INFANTS"], "oak")
        for x, f in ((32, "pink_tulip"), (35, "allium")):
            shutters(d, x, 3, 8, "north", "warped")
            window_box(d, x, 3, 8, "north", f)
        # walled playground: hopscotch, swings, sandpit, a bench along the wall, a shade tree, drinking trough
        for x in range(30, 47):
            if x != 34:
                d.set(x, 2, 18, "brick_wall")
            if x < 30 or x > 30:
                d.set(x, 2, 30, "brick_wall")
        for z in range(19, 30):
            d.set(46, 2, z, "brick_wall")
            if z < 26:
                d.set(30, 2, z, "brick_wall")
        d.set(30, 2, 30, "brick_wall")
        ground(d, 31, 19, 45, 29, "grass_block[snowy=false]")
        ground(d, 34, 17, 34, 25, "gravel")
        for k, (a, b) in enumerate(((1, 0), (1, 1), (0, 2), (2, 2), (1, 3), (0, 4), (2, 4), (1, 5))):
            d.set(36 + a, 1, 20 + b, "white_concrete" if k % 2 else "yellow_terracotta")
        for z in (20, 24):                                              # swing frame
            for y in range(2, 6):
                d.set(42, y, z, "oak_fence")
        d.fill(42, 6, 20, 42, 6, 24, log("stripped_oak_log", "z"))
        for z in (21, 23):
            d.set(42, 5, z, "chain[axis=y,waterlogged=false]")
            d.set(42, 4, z, "chain[axis=y,waterlogged=false]")
            d.set(42, 3, z, tslab("oak_slab"))
        ground(d, 31, 26, 33, 28, "sand")
        for z in (26, 27, 28):
            d.set(34, 1, z, "stone_bricks")
        d.set(32, 2, 27, "oak_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]")
        for z in (20, 21, 22):                                          # bench against the west wall
            sit_out(d, 31, Y0, z, "west", OAK)
        tree(d, 44, 2, 28, "oak_log", "oak_leaves", 5, 2)
        d.set(45, 2, 19, "water_cauldron[level=3]")
        lamp_post(d, 35, 19)

    # ------------------------------------------------------------------ C: art room + library loft (L3+)
    if L >= 3:
        link(d, 22, Y0, 16, "south")
        stairs(d, 25, 24, Y0, 7, "north")
        # art room: loom and map table, wash basin, paint table with stools, two easels, paint barrels
        plan(d, Y0, 19, 17, [
            # 19..25
            "L.....W",     # z17  loom, (door enters at x22), wash basin
            "......K",     # z18
            "..ttt..",     # z19  paint table
            "..sss..",     # z20  stools
            ".Ef....",     # z21  easel + painter's stool
            ".......",     # z22
            ".Ef....",     # z23
            "MM.....",     # z24  map table + paper stack
        ], {"L": itm("loom", "east"), "W": "water_cauldron[level=3]", "K": "barrel[facing=up,open=false]",
            "t": tslab("oak_slab"), "s": seat("south", OAK), "E": "oak_fence", "f": stool("east", "spruce"),
            "M": itm("cartography_table")})
        d.placed["items"]["minecraft:cartography_table"] -= 1             # second map table block is a paper stack
        d.set(20, Y0, 24, "chiseled_bookshelf[facing=north,slot_0_occupied=true,slot_1_occupied=true,"
                          "slot_2_occupied=true,slot_3_occupied=false,slot_4_occupied=true,slot_5_occupied=false]")
        for z in (21, 23):
            d.set(20, Y0 + 1, z, trap("birch", "east", "bottom", True))   # canvas on the easel
        plan(d, Y0 + 1, 21, 19, ["pir"], {"p": "flower_pot", "i": candle(3, "yellow"), "r": candle(2, "red")})
        d.banner(19, 4, 19, "east", "lime")
        d.banner(19, 4, 23, "east", "light_blue")
        d.banner(21, 4, 24, "north", "pink")
        d.set(22, 5, 18, LANT)
        d.set(22, 5, 22, LANT)
        # library loft: book presses on the north wall, reading table, lectern, window seats
        plan(d, 7, 19, 17, [
            # 19..25
            "BBBBBp.",     # z17
            ".......",     # z18
            "..nn...",     # z19
            "B.TT...",     # z20
            "..TT...",     # z21
            "B.ss...",     # z22
            "B......",     # z23
            "B.L....",     # z24
        ], {"B": shelf, "p": "potted_fern", "n": seat("north", OAK), "s": seat("south", OAK),
            "T": tslab("dark_oak_slab"), "L": "lectern[facing=north,has_book=false,powered=false]"})
        plan(d, 8, 19, 17, ["BBBBB"], {"B": shelf})
        d.set(21, 8, 20, candle(3))
        d.set(22, 8, 21, "flower_pot")
        rails(d, 7, [(24, 21), (24, 22), (24, 23), (25, 24)], "oak_fence")
        d.rug(20, 18, 23, 23, 7, ("red_carpet",), "plain")
        for z in (19, 23):
            d.set(22, 10, z, LANT)
        for z in (18, 21):
            window_box(d, 18, 8, z, "west", "red_tulip" if z == 18 else "allium")

    # ------------------------------------------------------------------ D: schoolmaster's house (L4+)
    if L >= 4:
        entry(d, 8, Y0, 6, "south", step="stone_bricks")
        for z in (8, 14):                                               # hand-set west windows (fire wall)
            for y in (3, 4, 8, 9):
                d.set(2, y, z, "glass_pane")
        for y in range(Y0, 6):                                          # ground-floor partition, door at x8
            d.fill(3, y, 12, 12, y, 12, "oak_planks")
        d.door(8, Y0, 12, "south", OAK)
        stairs(d, 13, 16, Y0, 7, "north")
        for y in range(7, 11):                                          # upstairs partition, door at x8
            d.fill(3, y, 12, 12, y, 12, "oak_planks")
        d.door(8, 7, 12, "south", OAK)
        # parlour: fireside chairs, side table, bookcase, hall table by the front door
        plan(d, Y0, 3, 7, [
            # 3..13
            "......t....",    # z7
            "...........",    # z8
            "X~e.....BB.",    # z9
            "F~T........",    # z10
            "X~e.....Dc.",    # z11
        ], {"X": "bricks", "F": "campfire[facing=east,lit=true,signal_fire=false,waterlogged=false]",
            "~": "red_carpet", "e": seat("east", OAK), "T": tslab("dark_oak_slab"), "t": tslab("dark_oak_slab"),
            "B": shelf, "D": tslab("dark_oak_slab"), "c": seat("east", OAK)})
        plan(d, Y0 + 1, 3, 7, ["......p....", "...........", "X.......BB.", "X.i........", "X.......f.."],
             {"X": "bricks", "p": "potted_red_tulip", "i": candle(2), "B": shelf, "f": "flower_pot"})
        d.set(7, 5, 9, LANT)
        # kitchen: range, sink and worktops on the south wall, kegs, scrubbed table with four chairs
        plan(d, Y0, 3, 13, [
            # 3..13
            "...........",    # z13
            "......n....",    # z14
            "K....wTe...",    # z15
            "K.....s....",    # z16
            "KSoCoF.....",    # z17
        ], {"K": "barrel[facing=east,open=false]", "S": "smoker[facing=north,lit=true]",
            "o": tslab("smooth_stone_slab"), "C": "water_cauldron[level=3]", "F": "furnace[facing=north,lit=false]",
            "n": seat("north", OAK), "s": seat("south", OAK), "w": seat("west", OAK), "e": seat("east", OAK),
            "T": "oak_planks"})
        d.set(3, 3, 17, "barrel[facing=up,open=false]")
        d.set(5, 3, 17, "flower_pot")
        d.set(7, 3, 17, candle(1))
        d.set(9, 3, 15, "cake[bites=0]")
        d.set(8, 5, 15, LANT)
        # study upstairs: book presses either side of the writing desk under the window, fireside chair
        plan(d, 7, 3, 7, [
            "..BB.BB....",    # z7  (desk at x7 under the window)
            "....s......",    # z8
            "X.e........",    # z9
            "F~~........",    # z10
            "X.p........",    # z11
        ], {"B": shelf, "s": seat("south", OAK), "X": "bricks",
            "F": "campfire[facing=east,lit=true,signal_fire=false,waterlogged=false]", "~": "brown_carpet",
            "e": seat("east", "spruce"), "p": "potted_fern"})
        plan(d, 8, 3, 7, ["..BB.BB....", "...........", "XXX........", "X..........", "X.........."],
             {"B": shelf, "X": "bricks"})
        d.set(5, 8, 9, AIR)
        d.set(4, 8, 9, AIR)
        d.set(7, 7, 7, tslab("dark_oak_slab"))
        d.set(7, 8, 7, candle(1))
        d.set(11, 7, 7, "spruce_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
        d.set(11, 8, 7, "potted_cornflower")
        rails(d, 7, [(12, 13), (12, 14), (12, 15), (13, 16)], "oak_fence")
        # bedroom upstairs: bed between nightstands, blanket chest, washstand, wardrobe
        plan(d, 7, 3, 13, [
            # 3..11
            "W........",      # z13
            "W.~~~....",      # z14
            "..~C~....",      # z15
            "...b.....",      # z16 (bed foot)
            "..nbn...V",      # z17 (bed head)
        ], {"W": "spruce_planks", "~": "white_carpet", "C": "chest[facing=north,type=single,waterlogged=false]",
            "n": tslab("oak_slab"), "V": "water_cauldron[level=3]", "b": "air"})
        d.set(3, 8, 13, "spruce_trapdoor[facing=east,half=top,open=false,powered=false,waterlogged=false]")
        d.set(3, 8, 14, "spruce_trapdoor[facing=east,half=top,open=false,powered=false,waterlogged=false]")
        d.bed(6, 7, 17, "south", "red")
        d.set(5, 8, 17, LANT_S)
        d.set(7, 8, 17, candle(1))
        d.set(11, 8, 17, "potted_lily_of_the_valley")
        for z in (9, 15):
            d.set(8, 10, z, LANT)
        chimney(d, 2, 10, Y0, 17)
        # garden: picket fence with a gate, two flower beds, flower boxes, door lamp, sign
        for x in range(1, 15):
            if x != 8:
                d.set(x, 2, 3, "oak_fence")
        ground(d, 8, 0, 8, 5, "gravel")
        ground(d, 3, 4, 6, 5, "grass_block[snowy=false]")
        ground(d, 10, 4, 13, 5, "grass_block[snowy=false]")
        flowers(d, [(3, 4), (4, 4), (5, 4), (6, 4), (3, 5), (5, 5), (10, 4), (11, 4), (12, 4), (13, 4), (11, 5),
                    (13, 5)], ["poppy", "lilac[half=lower]", "oxeye_daisy", "cornflower", "lavender" if False else
                               "allium", "red_tulip", "azure_bluet", "peony[half=lower]", "dandelion", "poppy",
                               "lily_of_the_valley", "oxeye_daisy"])
        d.set(4, 3, 4, "lilac[half=upper]")
        d.set(11, 3, 4, "peony[half=upper]")
        d.sign(8, 5, 5, "north", ["SCHOOL", "HOUSE"], "oak")
        d.wall_torch(9, 4, 5, "north")
        for x, f in ((4, "red_tulip"), (10, "cornflower")):
            shutters(d, x, 3, 6, "north", "warped")
            window_box(d, x, 3, 6, "north", f)
            shutters(d, x, 8, 6, "north", "warped")

        # -------------------------------------------------------------- E: school hall (L4+)
        entry(d, 27, Y0, 26, "south", double=True, step="stone_bricks")
        # stage at the west end with steps, lectern and piano; pews facing it; banners; chandeliers
        d.fill(15, 2, 27, 17, 2, 35, "oak_planks")
        for z in range(27, 36):
            d.set(18, 2, z, stair("oak_stairs", "west") if 30 <= z <= 32 else "oak_planks" if z in (27, 35) else
                  tslab("oak_slab"))
        d.set(18, 2, 27, "oak_planks")
        d.set(18, 2, 35, "oak_planks")
        d.set(16, 3, 31, "lectern[facing=east,has_book=false,powered=false]")
        d.set(15, 3, 28, "note_block[instrument=harp,note=0,powered=false]")
        d.set(15, 3, 29, "note_block[instrument=harp,note=0,powered=false]")
        d.set(15, 4, 28, tslab("dark_oak_slab"))
        d.set(15, 4, 29, tslab("dark_oak_slab"))
        d.chair(16, 3, 28, "east", "dark_oak", sit=False)
        for z in (27, 35):                                              # stage curtains
            for y in (3, 4, 5, 6):
                d.set(17, y, z, "red_wool")
        for x in (21, 23, 25, 27):                                      # pews, aisle down the middle (z31)
            bench(d, x, 28, x, 30, Y0, "east", OAK)
            bench(d, x, 32, x, 34, Y0, "east", OAK)
        for x in (20, 23):
            d.banner(x, 6, 27, "south", "yellow")
            d.banner(x, 6, 35, "north", "red")
        d.banner(15, 6, 31, "east", "red")
        for x in (18, 22, 26):
            d.set(x, 7, 31, "chain[axis=y,waterlogged=false]")
            d.set(x, 6, 31, LANT)
        d.sign(22, 6, 37, "south", ["SCHOOL", "HALL"], "oak")
        d.set(26, 4, 25, "wall_torch[facing=north]") if False else None
        d.wall_torch(29, 4, 25, "north")
        ground(d, 27, 17, 28, 25, "gravel")

    # ------------------------------------------------------------------ L5: junior school, canteen, grounds
    if L >= 5:
        entry(d, 7, Y0, 22, "south", step="stone_bricks")
        stairs(d, 11, 24, Y0, 7, "south")
        # junior classroom (ground): board on the south wall, two rows of double desks, master's desk
        board(d, [(5, 35), (6, 35), (7, 35), (8, 35)], Y0 + 1, "north", ledge=OAK)
        plan(d, Y0, 3, 23, [
            # 3..11
            "B........",      # z23
            "B........",      # z24
            ".nn.nn...",      # z25
            ".TT.TT...",      # z26
            ".........",      # z27
            ".nn.nn...",      # z28
            ".TT.TT...",      # z29
            ".........",      # z30
            ".nn.nn...",      # z31
            ".TT.TT...",      # z32
            ".........",      # z33
            "...MM.c..",      # z34  master's desk + chair
            ".........",      # z35
        ], {"B": shelf, "n": seat("north", OAK), "T": tslab("spruce_slab"), "M": tslab("oak_slab"),
            "c": seat("south", OAK)})
        d.set(3, 3, 23, "bookshelf")
        d.set(3, 3, 24, "potted_cactus")
        d.set(6, 3, 34, candle(1))
        d.banner(3, 4, 30, "east", "yellow") if False else None
        for z in (27, 31):
            d.set(7, 5, z, LANT)
        # music room (upstairs): choir risers facing the conductor's stand, piano, jukebox, drum
        rails(d, 7, [(10, 25), (10, 26), (10, 27), (11, 24)], "oak_fence")
        plan(d, 7, 3, 23, [
            # 3..11
            "Pp.......",      # z23 piano + stool
            "PP.......",      # z24
            ".........",      # z25
            ".........",      # z26
            ".........",      # z27
            "....L....",      # z28  conductor's stand
            ".........",      # z29
            "..sssss..",      # z30  front choir row
            "..RRRRR..",      # z31  riser
            "..RRRRR..",      # z32
            "..RRRRR..",      # z33
            ".J.....N.",      # z34
            ".........",      # z35
        ], {"P": "note_block[instrument=harp,note=0,powered=false]", "p": stool("east", "dark_oak"),
            "L": "lectern[facing=south,has_book=false,powered=false]", "s": seat("south", OAK),
            "R": "oak_planks", "J": "jukebox[has_record=false]", "N": "note_block[instrument=basedrum,note=0,powered=false]"})
        d.set(3, 8, 23, tslab("dark_oak_slab"))
        d.set(3, 8, 24, tslab("dark_oak_slab"))
        d.set(4, 8, 24, tslab("dark_oak_slab"))
        for x in range(5, 10):                                          # second and third choir rows on risers
            d.chair(x, 8, 32, "south", OAK)
            d.set(x, 8, 33, "oak_planks")
            d.chair(x, 9, 33, "south", OAK)
        d.set(5, 8, 31, stair("oak_stairs", "south")) if False else None
        for x in range(5, 10):
            d.set(x, 7, 31, stair("oak_stairs", "south"))
        d.banner(6, 9, 35, "north", "yellow") if False else None
        for z in (26, 32):
            d.set(7, 10, z, LANT)
        d.sign(7, 5, 21, "north", ["JUNIOR", "SCHOOL"], "oak")
        d.wall_torch(6, 4, 21, "north")
        for z, f in ((24, "red_tulip"), (30, "cornflower")):
            shutters(d, 2, 3, z, "west", "warped")
            window_box(d, 2, 3, z, "west", f)

        # G: canteen (kitchen + dining) with the staff room above
        link(d, 30, Y0, 34, "east")
        entry(d, 40, Y0, 38, "west", step="stone_bricks")
        stairs(d, 31, 39, Y0, 7, "north")
        plan(d, Y0, 32, 33, [
            # 32..39
            "....o..S",      # z33
            ".n..o..F",      # z34
            "wTe.....",      # z35  gap in the servery counter at x36
            ".s..o...",      # z36
            ".n..o..C",      # z37
            "wTe.o...",      # z38  (back door at z38)
            ".s..o..K",      # z39
        ], {"o": tslab("smooth_stone_slab"), "S": "smoker[facing=west,lit=true]",
            "F": "furnace[facing=west,lit=false]", "C": "water_cauldron[level=3]", "K": "barrel[facing=up,open=false]",
            "n": seat("north", OAK), "s": seat("south", OAK), "w": seat("west", OAK), "e": seat("east", OAK),
            "T": "oak_planks"})
        d.set(39, 2, 36, tslab("smooth_stone_slab"))
        plan(d, Y0 + 1, 33, 33, [".......", ".......", "i......", "...p...", ".......", "c......"],
             {"i": candle(3), "p": "cake[bites=0]", "c": "flower_pot"})
        d.set(36, 3, 33, "bread" if False else "flower_pot")
        for z in (34, 38):
            d.set(35, 5, z, LANT)
        # staff room: settle and armchairs round the fire, tea table, notice board, a sick-bay cot
        rails(d, 7, [(32, 36), (32, 37), (32, 38), (31, 39)], "oak_fence")
        plan(d, 7, 32, 33, [
            # 32..39
            "........",      # z33
            "........",      # z34  (landing at x31 z34)
            "...ccc.X",      # z35
            "...~T~.F",      # z36  fire on the east wall
            "...ccc.X",      # z37
            "........",      # z38
            ".V.bb...",      # z39
        ], {"c": "air", "~": "brown_carpet", "T": tslab("dark_oak_slab"), "X": "bricks",
            "F": "campfire[facing=west,lit=true,signal_fire=false,waterlogged=false]", "V": "water_cauldron[level=3]",
            "b": "air"})
        for x in (35, 36, 37):
            d.chair(x, 7, 35, "north", OAK)
            d.chair(x, 7, 37, "south", OAK)
        d.set(36, 8, 36, candle(2))
        d.set(39, 8, 35, "bricks")
        d.set(39, 8, 36, "bricks")
        d.set(39, 8, 37, "bricks")
        d.bed(35, 7, 39, "east", "white")
        d.set(36, 7, 39, AIR) if False else None
        d.set(33, 8, 39, "potted_oxeye_daisy") if False else None
        for z in (35, 38):
            d.set(35, 10, z, LANT)
        chimney(d, 40, 36, 7, 17)
        chimney(d, 40, 33, Y0, 17)
        d.sign(35, 5, 31, "north", ["CANTEEN"], "oak")
        # playing field with goals; school garden with beds, compost and a potting bench
        ground(d, 2, 40, 28, 48, "grass_block[snowy=false]")
        for x in range(2, 29):
            d.set(x, 1, 44, "white_concrete" if x == 15 else "grass_block[snowy=false]")
        for z in range(40, 49):
            d.set(15, 1, z, "white_concrete")
        for gx in (3, 27):                                              # goal frames
            for z in (42, 46):
                for y in (2, 3, 4):
                    d.set(gx, y, z, "white_concrete")
            d.fill(gx, 5, 42, gx, 5, 46, "white_concrete")
            for z in (43, 44, 45):
                d.set(gx + (1 if gx == 3 else -1) * 0, 4, z, "cobweb") if False else None
        for x in range(42, 48):
            for z in range(32, 47):
                if x in (42, 47) or z in (32, 46):
                    if not (x == 44 and z == 32):
                        d.set(x, 2, z, "oak_fence")
                elif z in (34, 35, 37, 38, 40, 41, 43, 44):
                    d.set(x, 1, z, "farmland[moisture=7]")
                    d.set(x, 2, z, {34: "carrots[age=7]", 35: "carrots[age=7]", 37: "potatoes[age=7]",
                                    38: "potatoes[age=7]", 40: "beetroots[age=3]", 41: "beetroots[age=3]",
                                    43: "wheat[age=7]", 44: "wheat[age=7]"}[z])
                else:
                    d.set(x, 1, z, "coarse_dirt")
        d.set(41, 2, 34, "composter[level=4]")
        d.set(41, 2, 35, "composter[level=7]")
        d.set(44, 1, 32, "gravel")
        lamp_post(d, 41, 31)
    return d


# ================================================================================================ NEOTERRA
# Modern primary school: glass classroom pavilion behind coloured fins (L1), glass bridge to a second pavilion
# (L2, art studio from L3), upper floor and fenced playground (L3), sports hall (L4), three-storey science and
# library block and a glazed canteen (L5).
def sch_neoterra(rel, L):
    d = new("Neoterra", rel, (53, 30, 51), paving="smooth_stone")
    B = "birch"
    Q = tslab("smooth_quartz_slab")
    SL = "sea_lantern"
    fins = {7: "yellow_concrete", 10: "lime_concrete", 16: "orange_concrete", 19: "yellow_concrete",
            25: "lime_concrete", 28: "orange_concrete", 31: "yellow_concrete", 34: "lime_concrete"}
    pnf = 2 if L >= 3 else 1
    # ------------------------------------------------------------------ shells
    A = shell(d, 6, 6, 20, 16, pnf, "flat", glassy=True, win="nsw")
    if L >= 2:
        Bb = shell(d, 24, 6, 36, 16, 1, "flat", glassy=True, win="nse")
        d.box(20, Y0, 9, 24, 5, 13, "glass", floor="polished_diorite")
        d.fill(20, 6, 9, 24, 6, 13, "smooth_quartz")
        d.clear(21, Y0, 10, 23, 5, 12)
        arch(d, 20, Y0, 11, "east")
        arch(d, 24, Y0, 11, "east")
    if L >= 4:
        shell(d, 6, 20, 34, 32, 1, "flat", wh=8, win="n", mat="light_gray_concrete")
    if L >= 5:
        S5 = shell(d, 38, 6, 50, 24, 3, "flat", glassy=True, win="nsew")
        C5 = shell(d, 6, 36, 30, 46, 1, "flat", glassy=True, win="nsw")

    # ------------------------------------------------------------------ A: classroom pavilion (L1+)
    for x, c in fins.items():
        if x < 20 or L >= 2:
            for y in range(Y0, 5 * (pnf if x < 20 else 1) + 2):
                d.set(x, y, 5, c)
    entry(d, 12, Y0, 6, "south", double=True, step="polished_andesite")
    d.fill(11, 5, 6, 14, 5, 6, "white_concrete")                       # lintel, canopy and glowing name sign
    d.fill(11, 6, 3, 14, 6, 5, Q)
    d.sign(12, 5, 5, "north", ["SUNRISE", "SCHOOL"], B, glow=True, color="yellow")
    d.sign(13, 5, 5, "north", ["primary", "& infants"], B, glow=True, color="cyan")
    d.hut(7, Y0, 7)
    keep(d, 8, Y0, 7)
    # classroom: board on the south wall, teacher's desk in front, three table islands of four, book wall west
    board(d, [(11, 15), (12, 15), (13, 15), (14, 15)], Y0 + 1, "north", "gray_concrete", ledge=B)
    plan(d, Y0, 7, 7, [
        # 7..19
        "............p",   # z7  (hut x7, entry x12-13)
        ".............",   # z8
        ".nn..nn..nn..",   # z9
        "BTT..TT..TT..",   # z10
        "Bss..ss..ss..",   # z11
        "B............",   # z12
        ".....MM......",   # z13
        ".....wc......",   # z14
        "p...........p",   # z15
    ], {"p": "potted_bamboo", "n": seat("north", B), "s": seat("south", B), "T": Q, "B": shelf, "M": Q,
        "w": work, "c": seat("south", B)})
    plan(d, Y0 + 1, 7, 10, ["B", "B", "B"], {"B": shelf})
    d.set(12, Y0 + 1, 13, "flower_pot")
    d.set(13, Y0 + 1, 13, candle(1, "lime"))
    d.set(8, Y0 + 1, 10, "potted_cactus") if False else None
    for x, z in ((9, 10), (13, 10), (17, 10), (12, 13)):                 # ceiling light panels
        d.set(x, 6, z, SL)
    for x in (8, 17):                                                   # street planters and lamps
        d.set(x, 2, 3, "moss_block")
        d.set(x, 3, 3, "flowering_azalea")
    d.set(10, 2, 3, "moss_block")
    d.set(15, 2, 3, "moss_block")
    d.set(10, 3, 3, "azalea")
    d.set(15, 3, 3, "azalea")
    lamp_post(d, 4, 4)
    lamp_post(d, 22, 4)
    ground(d, 12, 0, 13, 4, "polished_andesite")
    d.chair(5, Y0, 9, "west", B, sit=False) if False else None
    if pnf > 1:                                                         # upper floor: media and language room
        stairs(d, 14, 7, Y0, 7, "east")
        rails(d, 7, [(15, 8), (16, 8), (17, 8), (14, 7)])
        plan(d, 7, 7, 8, [
            # 7..19
            "B............",   # z8
            "B............",   # z9
            "B..~~~~~~....",   # z10
            "B..~nnn~~....",   # z11
            "...~QQQ~~....",   # z12
            "B..~sss~~....",   # z13
            "B............",   # z14
            ".............",   # z15 (study counter below)
        ], {"B": shelf, "~": "cyan_carpet", "n": seat("north", B), "s": seat("south", B), "Q": Q})
        for x in range(9, 20):                                          # study counter along the south glass
            if x != 14:
                d.set(x, 7, 15, Q)
                d.chair(x, 7, 14, "north", B) if x in (9, 11, 13, 16, 18) else None
        for x in (10, 12, 17):
            d.set(x, 8, 15, "flower_pot" if x == 12 else candle(1, "cyan"))
        d.set(11, 8, 12, "potted_azure_bluet")
        for x, z in ((10, 11), (15, 11), (12, 14)):
            d.set(x, 11, z, SL)
        # roof: two double rows of solar panels, planters on the corners, vent unit
        for z in (9, 10, 12, 13):
            for x in range(9, 18):
                d.set(x, 12, z, "daylight_detector[inverted=false,power=0]")
        for x, z in ((7, 7), (19, 7), (7, 15), (19, 15)):
            d.set(x, 12, z, "moss_block")
            d.set(x, 13, z, "flowering_azalea")
        d.set(18, 12, 14, "smooth_stone")
        d.set(18, 13, 14, "iron_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")

    # ------------------------------------------------------------------ B: second pavilion (L2 class, L3+ art)
    if L >= 2:
        entry(d, 30, Y0, 6, "south", step="polished_andesite")
        d.sign(30, 5, 5, "north", ["ART STUDIO" if L >= 3 else "CLASS 2"], B, glow=True, color="lime")
        d.set(30, 5, 6, "white_concrete")
        if L < 3:
            board(d, [(35, 10), (35, 11), (35, 12)], Y0 + 1, "west", "gray_concrete", ledge=B)
            plan(d, Y0, 25, 7, [
                # 25..35
                "..........p",   # z7
                "..wT.wT....",   # z8
                "..wT.wT....",   # z9
                "...........",   # z10
                "...........",   # z11  (bridge arrives at x25)
                "...........",   # z12
                "..wT.wT....",   # z13
                "..wT.wT....",   # z14
                "p.........p",   # z15
            ], {"p": "potted_bamboo", "w": seat("west", B), "T": Q})
            d.set(33, 2, 11, Q)
            d.chair(34, 2, 12, "east", B)
        else:
            plan(d, Y0, 25, 7, [
                # 25..35
                ".........L.",   # z7  loom
                ".E.E.....M.",   # z8  easels, map table
                ".f.f.......",   # z9  painters' stools
                "...........",   # z10
                "..ttt.ttt..",   # z11 work tables
                "..sss.sss..",   # z12
                "...........",   # z13
                ".WK.....RRR",   # z14 sink, kiln, paint racks
                "..........p",   # z15
            ], {"L": itm("loom", "west"), "M": itm("cartography_table"), "E": "birch_fence",
                "f": stool("north", B), "t": "white_concrete", "s": seat("south", B),
                "W": "water_cauldron[level=3]", "K": "blast_furnace[facing=north,lit=false]",
                "R": "barrel[facing=north,open=false]", "p": "potted_bamboo"})
            for x in (26, 28):
                d.set(x, Y0 + 1, 8, trap(B, "north", "bottom", True))
            plan(d, Y0 + 1, 27, 11, ["pir.rpi"], {"p": "flower_pot", "i": candle(3, "yellow"),
                                                   "r": candle(2, "magenta")})
            d.set(34, 3, 14, "barrel[facing=north,open=false]")
            d.banner(35, 4, 11, "west", "magenta")
            d.banner(35, 4, 13, "west", "lime")
        for x, z in ((28, 10), (32, 10), (30, 13)):
            d.set(x, 6, z, SL)
        d.set(22, 6, 11, SL)
        # roof garden on the second pavilion
        for x, z in ((26, 8), (27, 8), (33, 8), (34, 8), (26, 14), (27, 14), (33, 14), (34, 14)):
            d.set(x, 7, z, "moss_block")
            d.set(x, 8, z, "flowering_azalea" if (x + z) % 2 else "azalea")
        for x in range(28, 33):
            d.set(x, 7, 11, "moss_block")
            d.set(x, 8, 11, "potted_bamboo" if x % 2 else "fern")
        d.set(34, 7, 11, "smooth_stone")
        d.set(34, 8, 11, "iron_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")

    # ------------------------------------------------------------------ playground (L3+)
    if L >= 3:
        for x in range(38, 51):
            for z in (28, 44):
                if not (z == 28 and x in (43, 44)):
                    d.set(x, 2, z, "birch_fence")
        for z in range(29, 44):
            d.set(38, 2, z, "birch_fence")
            d.set(50, 2, z, "birch_fence")
        ground(d, 39, 29, 49, 43, "lime_concrete")
        ground(d, 43, 28, 44, 28, "smooth_stone")
        for z in range(30, 36):                                         # running track lines
            d.set(40, 1, z, "white_concrete")
        for k, (a, b) in enumerate(((1, 0), (1, 1), (0, 2), (2, 2), (1, 3), (0, 4), (2, 4), (1, 5))):
            d.set(41 + a, 1, 31 + b, "yellow_concrete" if k % 2 else "white_concrete")
        # climbing frame with slide
        for x, z in ((45, 31), (48, 31), (45, 34), (48, 34)):
            for y in range(2, 5):
                d.set(x, y, z, "yellow_concrete")
        d.fill(45, 5, 31, 48, 5, 34, "orange_concrete")
        for z in (32, 33):
            d.set(44, 2, z, "ladder[facing=west,waterlogged=false]") if False else None
        for k, z in enumerate((35, 36, 37)):
            d.set(46, 4 - k, z, stair("smooth_quartz_stairs", "north"))
        d.set(46, 1, 38, "white_concrete")
        # shade canopy over two benches
        for x in (40, 42):
            for y in range(2, 6):
                d.set(x, y, 40, "birch_fence")
        d.fill(39, 6, 39, 43, 6, 42, slab("smooth_quartz_slab", "bottom"))
        for x in (40, 41, 42):
            sit_out(d, x, Y0, 42, "south", B)
        d.set(48, 2, 42, "moss_block")
        d.set(48, 3, 42, "flowering_azalea")
        lamp_post(d, 49, 29)

    # ------------------------------------------------------------------ sports hall (L4+)
    if L >= 4:
        entry(d, 20, Y0, 20, "south", double=True, step="polished_andesite")
        for x in range(7, 34):                                          # court with lines
            for z in range(21, 32):
                d.set(x, 1, z, "white_concrete" if x in (7, 33, 20) or z in (21, 31) else "orange_terracotta")
        for x in (8, 32):                                               # basketball hoops at both ends
            for y in (4, 5, 6):
                d.set(x, y, 26, "white_stained_glass")
            d.set(x + (1 if x == 8 else -1), 5, 26, "iron_bars")
        for z in (22, 24, 28, 30):                                      # wall bars on the west wall
            for y in range(2, 8):
                d.set(7, y, z, "ladder[facing=east,waterlogged=false]")
        for x in range(10, 19):                                         # team benches by the entrance
            if x != 14:
                d.chair(x, Y0, 21, "north", B)
        for x in range(23, 32):
            if x != 27:
                d.chair(x, Y0, 21, "north", B)
        d.set(33, Y0, 31, "barrel[facing=up,open=false]")
        d.set(33, Y0, 30, "barrel[facing=up,open=false]")
        d.set(32, Y0, 31, "target[power=0]")
        for x in (10, 16, 24, 30):
            for z in (23, 29):
                d.set(x, 10, z, SL)
        d.sign(20, 7, 19, "north", ["SPORTS", "HALL"], B, glow=True, color="yellow")
        d.set(20, 7, 20, "light_gray_concrete")
        lamp_post(d, 17, 18)
        lamp_post(d, 24, 18)

    # ------------------------------------------------------------------ L5: science block + canteen
    if L >= 5:
        entry(d, 44, Y0, 6, "south", double=True, step="polished_andesite")
        d.fill(43, 6, 3, 46, 6, 5, Q)
        d.sign(44, 6, 5, "north", ["SCIENCE", "& LIBRARY"], B, glow=True, color="orange")
        d.set(44, 6, 6, "white_concrete")
        stairs(d, 39, 8, Y0, 7, "south")
        stairs(d, 49, 22, 7, 12, "north")
        # ground: laboratory with two benches, wash station, fish tank, specimen shelves
        plan(d, Y0, 40, 7, [
            # 40..49
            ".........W",   # z7
            ".........W",   # z8
            "..........",   # z9
            "..nnnnnn..",   # z10
            "..XXXXXX..",   # z11
            "..ssssss..",   # z12
            "..........",   # z13
            "..........",   # z14
            "..nnnnnn..",   # z15
            "..XXXXXX..",   # z16
            "..ssssss..",   # z17
            "..........",   # z18
            "..........",   # z19
            "..........",   # z20
            ".GGGGG...K",   # z21
            ".G...G...K",   # z22
            ".GGGGG...K",   # z23
        ], {"W": "water_cauldron[level=3]", "n": seat("north", B), "s": seat("south", B), "X": "white_concrete",
            "G": "glass", "K": "barrel[facing=west,open=false]"})
        for x in (42, 43, 44):
            for y in (2, 3):
                d.set(x, y, 22, "water")
        plan(d, Y0 + 1, 42, 11, ["b.p.b.", ".....", ".....", ".....", ".....", "pb..bi"],
             {"b": "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]", "p": "flower_pot",
              "i": candle(2, "lime")})
        d.set(41, 3, 21, "glass")
        for x in range(41, 46):
            d.set(x, 4, 21, "glass") if False else None
        d.set(49, 3, 21, "potted_cactus")
        for x, z in ((42, 11), (47, 11), (42, 16), (47, 16), (44, 21)):
            d.set(x, 6, z, SL)
        # first floor: library stacks, reading tables by the north glass
        rails(d, 7, [(40, 9), (40, 10), (40, 11), (39, 8)])
        rails(d, 12, [(48, 19), (48, 20), (48, 21), (49, 22)])
        for z in (14, 17, 20):
            for x in range(42, 47):
                d.bookshelf(x, 7, z)
                d.bookshelf(x, 8, z)
        plan(d, 7, 41, 8, [
            # 41..48
            "..nnn.nn",     # z8
            "..QQQ.QQ",     # z9
            "..sss.ss",     # z10
            "........",     # z11
        ], {"n": seat("north", B), "s": seat("south", B), "Q": Q})
        d.set(43, 8, 9, candle(1, "orange"))
        d.set(47, 8, 9, "potted_bamboo")
        d.set(48, 7, 14, "lectern[facing=west,has_book=false,powered=false]")
        d.set(41, 7, 23, "potted_bamboo")
        for x, z in ((44, 9), (44, 15), (44, 18), (44, 22)):
            d.set(x, 11, z, SL)
        # second floor: science classroom with board on the west wall and bench desks facing it
        board(d, [(39, 14), (39, 15), (39, 16)], 13, "east", "gray_concrete", ledge=B)
        plan(d, 12, 40, 8, [
            # 40..48
            ".........",    # z8
            "...TTT...",    # z9
            "...eee...",    # z10
            ".........",    # z11
            "...TT.TT.",    # z12
            "...ee.ee.",    # z13
            ".M.......",    # z14
            ".c.TT.TT.",    # z15
            "...ee.ee.",    # z16
            ".........",    # z17
            "...TT.TT.",    # z18
            "...ee.ee.",    # z19
        ], {"T": Q, "e": seat("south", B), "M": Q, "c": stool("west", B)})
        for x, z in ((44, 11), (44, 17), (44, 21)):
            d.set(x, 16, z, SL)
        # roof: telescope dome-less platform, solar rows, planters
        for z in (9, 10, 13, 14):
            for x in range(40, 48):
                d.set(x, 17, z, "daylight_detector[inverted=false,power=0]")
        d.set(46, 17, 20, "smooth_stone")
        d.set(46, 18, 20, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        d.set(41, 17, 20, "iron_block") if False else None
        for x, z in ((40, 22), (48, 22), (40, 17), (48, 17)):
            d.set(x, 17, z, "moss_block")
            d.set(x, 18, z, "flowering_azalea")
        # canteen: dining tables in the west part, servery counter, kitchen in the east part
        entry(d, 18, Y0, 36, "south", double=True, step="polished_andesite")
        d.sign(18, 5, 35, "north", ["CANTEEN"], B, glow=True, color="lime")
        d.set(18, 5, 36, "white_concrete")
        for z, back in ((38, "north"), (40, "south"), (42, "north"), (44, "south")):
            for x in range(8, 16):
                d.chair(x, Y0, z, back, B)
        for z in (39, 43):
            for x in range(8, 16):
                d.set(x, Y0, z, "white_concrete")
            for x in (9, 12, 15):
                d.set(x, Y0 + 1, z, "potted_bamboo" if x == 12 else "flower_pot")
        for z in range(37, 46):
            if z != 41:
                d.set(21, Y0, z, Q)
        for z in (38, 40, 43):
            d.set(21, Y0 + 1, z, "cake[bites=0]" if z == 40 else "flower_pot")
        plan(d, Y0, 22, 37, [
            # 22..29
            "......SF",     # z37
            ".......C",     # z38
            "...XX...",     # z39
            "...XX..K",     # z40
            "........",     # z41
            "...XX..K",     # z42
            "...XX...",     # z43
            ".......C",     # z44
            "......BB",     # z45
        ], {"S": "smoker[facing=west,lit=true]", "F": "furnace[facing=west,lit=false]",
            "C": "water_cauldron[level=3]", "X": "white_concrete", "K": "barrel[facing=west,open=false]",
            "B": "blast_furnace[facing=north,lit=false]"})
        for x, z in ((10, 41), (14, 41), (25, 41), (18, 39)):
            d.set(x, 6, z, SL)
        for z in (39, 41, 43):                                          # canteen roof solar rows
            for x in range(9, 28):
                d.set(x, 7, z, "daylight_detector[inverted=false,power=0]")
        for z in (37, 40, 43, 46):                                      # birch avenue beside the canteen
            plant_tree(d, 34, z, "birch")
        lamp_post(d, 32, 35)
    return d


# ================================================================================================ CASCADIA
# Mountain district school: one-room log schoolhouse with belfry and covered porch (L1), teacherage (L2), art
# lean-to and upper-grades schoolhouse (L3), timber gymnasium and log playground (L4), two-storey lunch hall with
# reading loft, school garden, woodshop and wagon shed (L5).
def sch_cascadia(rel, L):
    d = new("Cascadia", rel, (53, 28, 51), paving="coarse_dirt")
    S = "spruce"
    X1, X2, Z1, Z2, mid = 18, 28, 8, 20, 23
    FIRE_N = "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]"
    # ------------------------------------------------------------------ shells
    b = shell(d, X1, Z1, X2, Z2, 1, "gable", "z", wh=5, beams=(11, 15))
    if L >= 2:
        shell(d, 4, 8, 14, 16, 1, "gable", "z", win="nse", mat="stripped_spruce_log", up="stripped_spruce_log",
              beams=(12,))
    if L >= 3:
        shell(d, X2, 11, 33, 18, 1, "gable", "z", mat="mangrove_planks", up="mangrove_planks", win="e")
        c2 = shell(d, 36, 8, 46, 20, 1, "gable", "z", wh=5, beams=(11, 15))
    if L >= 4:
        shell(d, 10, 26, 40, 36, 1, "gable", "x", wh=7, mat="mangrove_planks", up="mangrove_planks",
              beams=(14, 20, 26, 32))
    if L >= 5:
        shell(d, 40, 26, 52, 38, 2, "gable", "z", mat="stripped_spruce_log", up="stripped_spruce_log", beams=(29, 34))
        shell(d, 44, 42, 52, 48, 1, "gable", "x", mat="stripped_spruce_log", win="", beams=(48,))
        shell(d, 2, 42, 10, 50, 1, "gable", "z", mat="mangrove_planks", up="mangrove_planks", wh=5, win="", beams=(46,))

    # ------------------------------------------------------------------ A: one-room schoolhouse (L1+)
    ridge = b["ridge"]
    for x in range(mid - 1, mid + 2):                                   # belfry on the front gable
        for z in range(Z1, Z1 + 3):
            d.set(x, ridge, z, "birch_planks")
    for x, z in ((mid - 1, Z1), (mid + 1, Z1), (mid - 1, Z1 + 2), (mid + 1, Z1 + 2)):
        for y in range(ridge + 1, ridge + 3):
            d.set(x, y, z, "birch_fence")
    d.hip(mid - 1, Z1, mid + 1, Z1 + 2, ridge + 3, "spruce_stairs", "spruce_slab", overhang=1)
    d.set(mid, ridge + 3, Z1 + 1, "spruce_planks")
    bell(d, mid, ridge + 2, Z1 + 1)
    entry(d, mid, Y0, Z1, "south")
    d.fill(X1, 1, Z1 - 3, X2, 1, Z1 - 1, "spruce_planks")              # covered porch
    for x in (X1, X2):
        for y in range(Y0, 6):
            d.set(x, y, Z1 - 3, log("stripped_birch_log"))
    for x in range(X1 - 1, X2 + 2):
        d.set(x, 7, Z1 - 4, st("spruce_stairs", "south"))
        for z in range(Z1 - 3, Z1):
            d.set(x, 7, z, slab("spruce_slab"))
    for x in range(X1 + 1, X2):
        if x != mid:
            d.set(x, 2, Z1 - 3, "spruce_fence")
    d.sign(mid, 6, Z1 - 1, "north", ["SCHOOL", "DIST. No. 7"], S)
    d.set(mid, 6, Z1 - 2, LANT) if False else None
    d.set(mid - 2, 6, Z1 - 2, LANT)
    d.set(mid + 2, 6, Z1 - 2, LANT)
    for x in (19, 20):                                                  # porch bench
        sit_out(d, x, Y0, Z1 - 1, "north", S) if False else d.chair(x, Y0, Z1 - 1, "south", S, sit=False)
    d.set(27, Y0, Z1 - 1, "barrel[facing=up,open=false]")
    d.set(26, Y0, Z1 - 1, "spruce_log[axis=x]") if False else None
    d.hut(X1 + 1, Y0, Z1 + 1)
    keep(d, X1 + 2, Y0, Z1 + 1)
    board(d, [(19, 13), (19, 14), (19, 15)], Y0 + 1, "east", ledge=S)
    plan(d, Y0, 19, 9, [
        # 19..27
        ".........",   # z9  (hut x19, door x23)
        "ct......B",   # z10 teacher's desk
        ".t......B",   # z11
        "...De.De.",   # z12
        "...De.De.",   # z13
        ".w.De.De.",   # z14 (link to the art lean-to at x28 z14)
        "...De.De.",   # z15
        "...De.De.",   # z16
        "........K",   # z17
        "p.......K",   # z18
        "...XFX...",   # z19 fireplace
    ], {"c": seat("west", S), "t": tslab("spruce_slab"), "B": shelf, "D": tslab("birch_slab"),
        "e": seat("east", S), "w": work, "K": "spruce_log[axis=x]", "p": "potted_fern", "X": "cobblestone",
        "F": FIRE_N})
    plan(d, Y0 + 1, 19, 10, [".i......B", ".p......B"], {"i": candle(1), "p": "flower_pot", "B": shelf})
    d.fill(22, 3, 19, 24, 3, 19, "cobblestone")
    d.set(22, 4, 19, LANT_S)
    d.set(24, 4, 19, "potted_fern")
    for x in (21, 22, 24, 25):
        d.set(x, Y0 + 1, 9, "tripwire_hook[attached=false,facing=south,powered=false]")
    for z in (11, 15):
        d.set(mid, 6, z, LANT)
    chimney(d, mid, Z2, Y0, ridge)
    for x in (20, 26):                                                  # shutters on the street windows
        shutters(d, x, 3, Z1, "north", "birch")
    for z in (10, 16):
        shutters(d, X1, 3, z, "west", "birch")
    lamp_post(d, X1 - 2, Z1 - 2)
    lamp_post(d, X2 + 2, Z1 - 2)
    ground(d, mid, 0, mid, Z1 - 4, "spruce_planks")

    # ------------------------------------------------------------------ L2: teacherage
    if L >= 2:
        entry(d, 9, Y0, 8, "south")
        plan(d, Y0, 5, 9, [
            # 5..13
            "L.....wTe",   # z9  log pile, small table
            "X.e......",   # z10 hmm
            "X.e......",   # z11
            "F~e......",   # z12 fireplace, settle facing it
            "X~.......",   # z13
            "........n",   # z14
            "KC.....nb",   # z15 kitchenette, bed
        ], {"L": "spruce_log[axis=z]", "X": "cobblestone", "F": "campfire[facing=east,lit=true,signal_fire=false,waterlogged=false]",
            "~": "green_carpet", "e": seat("east", S), "w": seat("west", S), "T": "spruce_fence",
            "K": "barrel[facing=up,open=false]", "C": "water_cauldron[level=3]", "n": tslab("spruce_slab"),
            "b": "air"})
        d.set(12, 3, 9, "spruce_pressure_plate[powered=false]")
        d.set(5, 2, 10, "cobblestone")
        d.set(5, 2, 11, "cobblestone")
        d.set(5, 3, 11, "cobblestone")
        d.set(5, 3, 12, "cobblestone")
        d.set(5, 3, 13, "cobblestone")
        d.set(5, 4, 12, LANT_S)
        d.bed(13, Y0, 15, "south", "brown")
        d.set(12, 3, 15, candle(1))
        d.set(13, 3, 14, "potted_fern") if False else None
        d.set(9, 5, 12, LANT)
        chimney(d, 4, 12, Y0, 13)
        for x in range(3, 16):
            if x != 9:
                d.set(x, 2, 5, "spruce_fence")
        ground(d, 9, 0, 9, 7, "spruce_planks")
        flowers(d, [(4, 6), (5, 6), (6, 6), (7, 6), (11, 6), (12, 6), (13, 6)],
                ["fern", "blue_orchid", "allium", "dandelion", "lily_of_the_valley", "fern", "blue_orchid"])
        d.sign(9, 5, 7, "north", ["TEACHER"], S)
        d.set(10, 4, 7, "wall_torch[facing=north]")

    # ------------------------------------------------------------------ L3: art lean-to, upper-grades house
    if L >= 3:
        link(d, X2, Y0, 14, "east")
        plan(d, Y0, 29, 12, [
            # 29..32
            "L..M",        # z12 loom, map table
            "....",        # z13
            "....",        # z14 (link)
            ".tt.",        # z15 work table
            ".ss.",        # z16
            "E..W",        # z17 easel, wash bucket
        ], {"L": itm("loom", "south"), "M": itm("cartography_table", "south"), "t": tslab("spruce_slab"),
            "s": seat("south", S), "E": "spruce_fence", "W": "water_cauldron[level=3]"})
        d.set(29, 3, 17, trap("birch", "north", "bottom", True))
        d.set(30, 3, 15, candle(2, "orange"))
        d.set(31, 3, 15, "flower_pot")
        d.set(30, 5, 14, LANT)
        # upper grades schoolhouse
        entry(d, 41, Y0, 8, "south")
        board(d, [(39, 19), (40, 19), (41, 19), (42, 19), (43, 19)], Y0 + 1, "north", ledge=S)
        plan(d, Y0, 37, 9, [
            # 37..45
            "B........",   # z9
            "B........",   # z10
            ".nnn.nnn.",   # z11
            ".TTT.TTT.",   # z12
            ".........",   # z13
            ".nnn.nnn.",   # z14
            ".TTT.TTT.",   # z15
            ".........",   # z16
            "...MM.c.X",   # z17
            "........F",   # z18 wood fire on the east wall
            "........X",   # z19
        ], {"B": shelf, "n": seat("north", S), "T": tslab("birch_slab"), "M": tslab("spruce_slab"),
            "c": seat("south", S), "X": "cobblestone",
            "F": "campfire[facing=west,lit=true,signal_fire=false,waterlogged=false]"})
        plan(d, Y0 + 1, 37, 9, ["B", "B"], {"B": shelf})
        d.fill(45, 3, 17, 45, 3, 19, "cobblestone")
        d.set(40, 3, 17, candle(1))
        d.set(41, 3, 17, "flower_pot")
        d.set(45, 3, 9, "potted_fern") if False else None
        for z in (11, 15):
            d.set(41, 6, z, LANT)
        chimney(d, 46, 18, Y0, c2["ridge"])
        d.sign(41, 6, 7, "north", ["UPPER", "GRADES"], S)
        d.set(42, 5, 7, "wall_torch[facing=north]")
        for x in (38, 44):
            shutters(d, x, 3, 8, "north", "birch")
        ground(d, 41, 0, 41, 7, "spruce_planks")

    # ------------------------------------------------------------------ L4: gymnasium + log playground
    if L >= 4:
        entry(d, 25, Y0, 26, "south", double=True)
        ground(d, 25, 21, 26, 25, "spruce_planks")
        for x in range(11, 40):
            for z in range(27, 36):
                d.set(x, 1, z, "birch_planks" if (x + z) % 2 else "spruce_planks")
        for x in (12, 38):                                              # hoops
            for y in (4, 5):
                d.set(x, y, 31, "white_stained_glass")
            d.set(x + (1 if x == 12 else -1), 5, 31, "iron_bars")
        for x in (15, 16, 17, 18, 32, 33, 34, 35):                      # benches along the north wall
            d.chair(x, Y0, 27, "north", S)
        for x in (15, 16, 17, 18):
            d.chair(x, Y0, 35, "south", S)
        for z in (28, 30, 32, 34):                                      # climbing ropes / wall ladders
            for y in range(2, 8):
                d.set(39, y, z, "ladder[facing=west,waterlogged=false]") if z in (28, 34) else None
        for y in range(3, 9):
            d.set(25, y, 33, "chain[axis=y,waterlogged=false]") if False else None
        d.set(11, 2, 35, "barrel[facing=up,open=false]")
        d.set(11, 2, 34, "hay_block[axis=y]")
        d.set(11, 3, 35, "target[power=0]")
        for x in (14, 20, 26, 32):
            d.set(x, 8, 31, LANT)
        d.sign(25, 7, 25, "north", ["GYMNASIUM"], S)
        # log playground: rail fence, swing frame, balance logs, sand box, stump seats, fir tree
        for z in range(22, 41):
            d.set(2, 2, z, "spruce_fence")
            d.set(8, 2, z, "spruce_fence") if z not in (24,) else None
        for x in range(3, 8):
            d.set(x, 2, 22, "spruce_fence")
            d.set(x, 2, 40, "spruce_fence")
        ground(d, 3, 23, 7, 39, "grass_block[snowy=false]")
        for z in (25, 29):
            for y in range(2, 6):
                d.set(5, y, z, log("spruce_log"))
        d.fill(5, 6, 25, 5, 6, 29, log("spruce_log", "z"))
        for z in (26, 28):
            d.set(5, 5, z, "chain[axis=y,waterlogged=false]")
            d.set(5, 4, z, "chain[axis=y,waterlogged=false]")
            d.set(5, 3, z, tslab("spruce_slab"))
        d.fill(4, 2, 31, 4, 2, 35, log("stripped_spruce_log", "z"))
        ground(d, 5, 36, 7, 38, "sand")
        for z in (31, 33):
            d.set(7, 2, z, log("spruce_log"))
        plant_tree(d, 6, 32, "spruce") if False else None

    # ------------------------------------------------------------------ L5: lunch hall, garden, woodshop, shed
    if L >= 5:
        entry(d, 46, Y0, 26, "south")
        stairs(d, 51, 31, Y0, 7, "south")
        plan(d, Y0, 41, 27, [
            # 41..51
            "......SoCoF",   # z27 kitchen run on the north wall
            "...........",   # z28
            "......ooooo",   # z29 serving counter (gap at x46)
            "..n........",   # z30
            ".wTe.......",   # z31
            ".wTe.......",   # z32
            ".wTe.......",   # z33
            ".wTe.......",   # z34
            ".wTe.......",   # z35
            "..s........",   # z36
            "K.........K",   # z37
        ], {"S": "smoker[facing=south,lit=true]", "o": tslab("spruce_slab"), "C": "water_cauldron[level=3]",
            "F": "furnace[facing=south,lit=false]", "n": seat("north", S), "s": seat("south", S),
            "w": seat("west", S), "e": seat("east", S), "T": "spruce_planks", "K": "barrel[facing=up,open=false]"})
        d.set(47, 2, 29, "air")
        for z, it in ((31, candle(3)), (33, "flower_pot"), (35, candle(3))):
            d.set(43, 3, z, it)
        d.set(48, 3, 29, "cake[bites=0]")
        d.set(50, 3, 29, "flower_pot")
        for x in range(45, 50):                                         # second dining table
            d.set(x, 2, 33, "spruce_planks")
            d.chair(x, 2, 32, "north", S)
            d.chair(x, 2, 34, "south", S)
        for z in (29, 34):
            d.set(46, 6, z, LANT)
        chimney(d, 52, 28, Y0, 17)
        d.sign(46, 5, 25, "north", ["LUNCH", "ROOM"], S)
        # reading loft upstairs
        rails(d, 7, [(50, 32), (50, 33), (50, 34), (51, 31)], "spruce_fence")
        plan(d, 7, 41, 27, [
            # 41..51
            "BBBB.BBBB..",   # z27
            "...........",   # z28
            "..nnn......",   # z29
            "..TTT......",   # z30
            "..sss......",   # z31
            "...........",   # z32
            "B..........",   # z33
            "B.e.e......",   # z34
            "B.~~~......",   # z35
            "B..........",   # z36
            "..p.....L..",   # z37
        ], {"B": shelf, "n": seat("north", S), "s": seat("south", S), "T": tslab("spruce_slab"),
            "e": seat("east", "dark_oak"), "~": "brown_carpet", "p": "potted_fern",
            "L": "lectern[facing=north,has_book=false,powered=false]"})
        plan(d, 8, 41, 27, ["BBBB.BBBB"], {"B": shelf})
        d.set(44, 8, 30, LANT_S)
        for z in (29, 34):
            d.set(46, 10, z, LANT)
        # school garden: rail fence, crop rows on alternate lines, a scarecrow
        for x in range(12, 40):
            for z in range(40, 49):
                if x in (12, 39) or z in (40, 48):
                    if not (z == 40 and x == 25):
                        d.set(x, 2, z, "spruce_fence")
                elif z % 2:
                    d.set(x, 1, z, "farmland[moisture=7]")
                    d.set(x, 2, z, ("carrots[age=7]", "potatoes[age=7]", "wheat[age=7]")[x % 3])
                else:
                    d.set(x, 1, z, "coarse_dirt")
        d.set(25, 2, 44, "spruce_fence")
        d.set(25, 3, 44, "hay_block[axis=y]")
        d.set(25, 4, 44, "carved_pumpkin[facing=north]")
        d.set(13, 2, 41, "composter[level=6]")
        # woodshop
        entry(d, 48, Y0, 42, "south", double=True)
        plan(d, Y0, 45, 43, [
            # 45..51
            ".......",     # z43
            "GW...WS",     # z44 grindstone, workbenches, stonecutter
            ".......",     # z45
            "LLL.ttt",     # z46 lumber stack, bench
            "LLL.CCB",     # z47 crafting tables, barrel
        ], {"G": "grindstone[face=floor,facing=south]", "W": tslab("spruce_slab"),
            "S": "stonecutter[facing=south]", "L": "stripped_spruce_log[axis=x]", "t": tslab("spruce_slab"),
            "C": "crafting_table", "B": "barrel[facing=up,open=false]"})
        d.set(45, 3, 47, "stripped_spruce_log[axis=x]")
        d.set(46, 3, 47, "stripped_spruce_log[axis=x]")
        d.set(50, 3, 46, "flower_pot") if False else None
        d.set(48, 5, 45, LANT)
        d.sign(48, 5, 41, "north", ["WOOD", "SHOP"], S)
        # wagon shed: hay along the walls, a farm cart
        entry(d, 6, Y0, 42, "south", double=True)
        for z in (44, 46, 48):
            d.set(3, 2, z, "hay_block[axis=y]")
            d.set(9, 2, z, "hay_block[axis=y]")
        d.set(3, 3, 46, "hay_block[axis=y]")
        d.fill(6, 2, 45, 6, 2, 47, tslab("spruce_slab"))
        d.set(5, 2, 46, "spruce_trapdoor[facing=west,half=bottom,open=true,powered=false,waterlogged=false]")
        d.set(6, 2, 44, "spruce_fence")
        d.set(6, 3, 47, "barrel[facing=up,open=false]")
        d.set(6, 5, 46, LANT)
        d.sign(6, 5, 41, "north", ["WAGON", "SHED"], S)
        for y in range(Y0, 14):                                         # flagpole by the porch
            d.set(16, y, 4, "spruce_fence")
        d.set(16, 14, 4, "red_wool")
        d.set(16, 13, 4, "white_wool")
    return d


@design("school")
def school_v2(pack, rel, L):
    return common_materials({"Hearthwood": sch_hearthwood, "Cascadia": sch_cascadia, "Neoterra": sch_neoterra}[pack](rel, L))
