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


@design("school")
def school_v2(pack, rel, L):
    return common_materials({"Hearthwood": sch_hearthwood}[pack](rel, L))
