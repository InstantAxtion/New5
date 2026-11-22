"""Civic: hospital (hand-designed, all packs).

Round 4: no automatic placement. Building shells come from the local shell() (structure only: walls, floors,
window openings, roofs, tie beams); every piece of furniture, light, sign, shutter, planter, tree and lamp is
placed at a hand-chosen coordinate below, room by room and level by level.
"""
from designs import _civic_common as _c
globals().update({k: v for k, v in vars(_c).items() if not k.startswith("__")})
from hm import design  # noqa: E402,F401


# ============================================================================ structure helpers (no decoration)

def gable2(d, x1, z1, x2, z2, y, axis, stairs, ridge, end, o=1, e0=1, e1=1):
    """Gable roof like Design.gable, but the ridge ends overhang separately (e0 / e1; 0 = flush with the wall
    line, -1 = start one cell inside) so a wing roof never pokes into the building it abuts."""
    if axis == "x":
        lo, hi, a1, a2 = z1, z2, x1, x2
    else:
        lo, hi, a1, a2 = x1, x2, z1, z2
    L, H = lo - o, hi + o
    n = H - L + 1
    for i in range(n):
        w = L + i
        k = min(i, n - 1 - i)
        yy = y + k - o
        mid = (n % 2 == 1 and i == n // 2)
        face = ("south" if i < n / 2 else "north") if axis == "x" else ("east" if i < n / 2 else "west")
        for a in range(a1 - e0, a2 + e1 + 1):
            x, z = (a, w) if axis == "x" else (w, a)
            st_ = f"{ridge}[type=bottom,waterlogged=false]" if mid else \
                f"{stairs}[facing={face},half=bottom,shape=straight,waterlogged=false]"
            if d.bp.inside(x, yy, z):
                d.set(x, yy, z, st_)
        if lo <= w <= hi:
            for a in (a1, a2):
                x, z = (a, w) if axis == "x" else (w, a)
                for yy2 in range(y, yy):
                    if d.air(x, yy2, z):
                        d.set(x, yy2, z, end)
    return y + (n - 1) // 2 - o


def shell(d, x1, z1, x2, z2, nf=1, roof="gable", axis="x", win="nesw", ws=3, mat=None, up=None, wh=4,
          gable_end=None, glassy=False, ends=(1, 1)):
    """Building shell only: plinth, storey walls + floor slabs + bands, corner posts, window openings, roof and
    tie beams. No lights, sills, shutters or brackets – those are placed by hand per building."""
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
                    d.set(x, yb, z, wallblock(d, S["band"], "n"))
            for z in range(z1, z2 + 1):
                for x in (x1, x2):
                    d.set(x, yb, z, wallblock(d, S["band"], "w"))
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if x in (x1, x2) or z in (z1, z2):
                d.set(x, Y0, z, S["base"] if not (d.pack == "Cascadia" and (x * 7 + z) % 5 == 0) else "mossy_cobblestone")
    if d.pack == "Hearthwood":
        for f, y in enumerate(ys):
            m = mat if f == 0 else up
            if m == "calcite":
                framing(d, x1, z1, x2, z2, y, y + wh - 1, S["post"], every=3)
    for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        for y in range(Y0, top + 1):
            if d.pack == "Hearthwood":
                if mat == up or y < ys[0] + wh:
                    d.set(x, y, z, ("smooth_stone" if y % 2 else "chiseled_stone_bricks") if mat == "stone_bricks"
                          else ("smooth_stone" if y % 2 else "stone_bricks"))
                else:
                    d.set(x, y, z, log(S["post"]))
            elif d.pack == "Cascadia":
                d.set(x, y, z, log(S["post"]))
            else:
                d.set(x, y, z, "light_gray_concrete")
    sides = {"n": (z1, "x"), "s": (z2, "x"), "w": (x1, "z"), "e": (x2, "z")}
    for f, y in enumerate(ys):
        for sd in win:
            line, along = sides[sd]
            a1, a2 = (x1, x2) if along == "x" else (z1, z2)
            for a in range(a1 + 2, a2 - 1):
                if glassy:
                    if (a - a1) % 4 == 0:
                        continue
                elif (a - a1 - 2) % ws != 0:
                    continue
                x, z = (a, line) if along == "x" else (line, a)
                h2 = wh - 1 if glassy or d.pack == "Neoterra" else 2
                for yy in range(y + 1, y + 1 + h2):
                    d.set(x, yy, z, "light_gray_stained_glass_pane" if glassy and f > 0 else S["glass"])
    ridge = top
    if roof == "gable":
        ridge = gable2(d, x1, z1, x2, z2, top + 1, axis, f"{S['roof']}_stairs", f"{S['roof']}_slab",
                       gable_end or (up if d.pack != "Cascadia" else "spruce_planks"), 1, *ends)
        epts = ((x1, (z1 + z2) // 2), (x2, (z1 + z2) // 2)) if axis == "x" else (((x1 + x2) // 2, z1), ((x1 + x2) // 2, z2))
        for i, (ex, ez) in enumerate(epts):
            if ends[i] < 0:
                continue
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
        if axis == "x":                                     # tie beams (structure, no lights)
            for x in range(x1 + 2, x2 - 1, 4):
                for z in range(z1 + 1, z2):
                    d.set(x, top + 1, z, log(S["post"], "z"))
        else:
            for z in range(z1 + 2, z2 - 1, 4):
                for x in range(x1 + 1, x2):
                    d.set(x, top + 1, z, log(S["post"], "x"))
    elif roof == "flat":
        d.fill(x1, top + 1, z1, x2, top + 1, z2, "smooth_quartz")
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                if x in (x1, x2) or z in (z1, z2):
                    d.set(x, top + 2, z, "white_concrete")
                    d.set(x, top + 3, z, slab("smooth_quartz_slab"))
        for x in range(x1, x2 + 1):                         # cantilevered roof edge
            for z in (z1 - 1, z2 + 1):
                put(d, x, top + 1, z, slab("smooth_quartz_slab", "top"))
        for z in range(z1, z2 + 1):
            for x in (x1 - 1, x2 + 1):
                put(d, x, top + 1, z, slab("smooth_quartz_slab", "top"))
        ridge = top + 1
    return dict(ys=ys, top=top, ridge=ridge, x1=x1, z1=z1, x2=x2, z2=z2)


def entry(d, x, y, z, facing, wood=None, double=False, along="x", step=None):
    """Exterior door (facing = into the building); clears the cells in front and behind, sets a threshold."""
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


def stair(d, x, z, y0, yU, rise, rails=(), block=None, fence=None):
    """One flight (first step at x,z rising toward `rise`) plus the railing cells listed by hand (on yU)."""
    block = block or (f"{d.S['wood']}_stairs" if d.pack != "Neoterra" else "smooth_quartz_stairs")
    fence = fence or (f"{d.S['wood']}_fence" if d.pack != "Neoterra" else "glass_pane")
    dx, dz = D4[rise]
    keep(d, x - dx, y0, z - dz, 3)
    lx, lz = flight(d, x, z, y0, yU, rise, block, under=d.S["floor"] if d.pack != "Neoterra" else "smooth_quartz")
    keep(d, lx, yU, lz, 3)
    for rx, rz in rails:
        d.set(rx, yU, rz, fence)
    return lx, lz


def P(d, y, items):
    """Explicit list of (x, z, block) at height y."""
    for x, z, b in items:
        d.set(x, y, z, b)


def hang(d, pts, y):
    for x, z in pts:
        d.set(x, y, z, "lantern[hanging=true,waterlogged=false]")


def panels(d, pts, y):
    """Neoterra ceiling light panels set into the ceiling slab at y."""
    for x, z in pts:
        d.set(x, y, z, "sea_lantern")


def curtain(d, cells, y, glass="white_stained_glass_pane", h=2):
    for x, z in cells:
        for k in range(h):
            d.set(x, y + k, z, glass)


def couch(d, cells, y, top="smooth_stone_slab", cover="white_carpet"):
    """Examination couch / cot: raised slab with a mattress carpet."""
    for x, z in cells:
        d.set(x, y, z, slab(top, "top"))
        d.set(x, y + 1, z, cover)


def stand(d, x, y, z, top, deco=None):
    d.set(x, y, z, top if "slab" not in top else slab(top, "top"))
    if deco:
        d.set(x, y + 1, z, deco)


def shutters(d, pts, y, trap, out="north", h=2):
    """Open shutters at the hand-listed cells (outside face of the wall)."""
    for x, z in pts:
        for k in range(h):
            d.set(x, y + k, z, f"{trap}[facing={out},half=bottom,open=true,powered=false,waterlogged=false]")


def window_box(d, pts, y, trap, out="north"):
    """Sill planter under an upper window: (x, z, flower) cells outside the wall."""
    for x, z, f in pts:
        d.set(x, y, z, f"{trap}[facing={out},half=top,open=false,powered=false,waterlogged=false]")
        d.set(x, y + 1, z, f"potted_{f}")


def plants(d, cells):
    """Flowers in the ground at hand-picked cells (x, z, flower)."""
    for x, z, f in cells:
        d.set(x, 1, z, "grass_block[snowy=false]")
        d.set(x, 2, z, f)


def grass(d, x1, z1, x2, z2):
    d.fill(x1, 1, z1, x2, 1, z2, "grass_block[snowy=false]")


def bed_of(d, x1, z1, x2, z2, flower):
    """One planted bed of a single species (rectangle chosen by hand)."""
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            d.set(x, 1, z, "grass_block[snowy=false]")
            d.set(x, 2, z, flower)


def sit(d, cells, y, back, wood, s=False):
    for x, z in cells:
        d.chair(x, y, z, back, wood, sit=s)


def chest(face, t="single"):
    return f"chest[facing={face},type={t},waterlogged=false]"


CAND = "candle[candles=2,lit=false,waterlogged=false]"
LAMP = "lantern[hanging=false,waterlogged=false]"
REDC = "red_concrete"


# ============================================================================ HEARTHWOOD – cottage hospital

def hw_admin_ground(d, L):
    y = Y0
    S = "dark_oak_slab"
    # reception desk facing the door, the hut block is the register on the desk
    d.hut(27, y, 12)
    P(d, y, [(26, 12, slab(S, "top")), (28, 12, slab(S, "top"))])
    d.candle(26, y + 1, 12, 2)
    d.set(28, y + 1, 12, "potted_azure_bluet")
    d.chair(27, y, 13, "south", "oak", sit=False)
    # fireside waiting corner
    d.hearth(23, y, 9, "east", y + 4, "bricks", "campfire")
    P(d, y, [(24, 9, "red_carpet"), (24, 10, "red_carpet")])
    sit(d, [(25, 9), (25, 10)], y, "east", "oak", True)
    P(d, y, [(23, 11, "potted_fern"), (23, 12, "bookshelf")])
    d.placed["bookshelves"] += 1
    d.set(23, y + 1, 12, "potted_red_tulip")
    sit(d, [(29, 9), (30, 9)], y, "north", "oak", True)          # bench by the door
    d.set(31, y, 9, "potted_fern")
    # dispensary on the east wall
    d.item(31, y, 10, "brewing_stand")
    d.item(31, y, 11, "furnace", "west")
    d.item(31, y, 12, "water_cauldron[level=3]")
    d.set(31, y, 13, chest("west"))
    d.sign(31, y + 2, 11, "west", ["DISPENSARY"], "oak")
    if d.req["racks"]:
        d.rack(31, y, 15, "west")
    if L >= 3:
        for x in (28, 29, 30):
            d.item(x, y, 16, "barrel", "up")
        stair(d, 30, 17, y, 7, "west", rails=[(30, 17), (27, 16), (28, 16), (29, 16)])
    if L == 1:                                                   # two-bed sick bay
        d.bed(23, y, 14, "west", "red")
        curtain(d, [(23, 15), (24, 15)], y)
        d.bed(23, y, 16, "west", "red")
        stand(d, 23, y, 13, "oak_slab", "potted_oxeye_daisy")
        stand(d, 23, y, 17, "oak_slab", CAND)
    else:                                                        # doctor's consulting corner
        stand(d, 23, y, 13, S, CAND)
        d.chair(24, y, 13, "east", "oak", sit=False)
        d.set(23, y, 14, chest("east"))
        curtain(d, [(23, 15), (24, 15)], y)
        couch(d, [(23, 16), (23, 17)], y)
    hang(d, [(27, 10), (24, 14), (29, 14)], 5)


def hw_admin_upper(d, L):
    y = 7
    # matron's office with its own fireplace
    d.hearth(23, y, 9, "east", 11, "bricks", "campfire")
    P(d, y, [(24, 9, "red_carpet"), (24, 10, "red_carpet")])
    d.chair(25, y, 9, "east", "oak", sit=False)
    d.set(26, y, 9, "potted_cornflower")
    d.bookshelf(23, y, 11, 2)
    d.bookshelf(23, y, 12, 2)
    stand(d, 23, y, 13, "dark_oak_slab", CAND)
    d.chair(24, y, 13, "east", "oak", sit=False)
    # nurses' room: tea table, linen cupboard, wash basin
    d.table(29, y, 11, "oak")
    d.chair(28, y, 11, "west", "oak", sit=False)
    d.chair(30, y, 11, "east", "oak", sit=False)
    P(d, y, [(31, 9, chest("west", "left")), (31, 10, chest("west", "right")), (31, 12, "white_wool"),
             (31, 13, "white_wool"), (28, 9, "water_cauldron[level=3]")])
    d.set(31, y + 1, 12, "white_wool")
    # landing corridor: window seat
    sit(d, [(23, 15), (23, 16)], y, "west", "oak")
    d.set(24, y, 16, "potted_allium")
    hang(d, [(26, 10), (28, 14)], 10)


def hw_east_ward(d, L):
    y = Y0
    nf = 2 if L >= 4 else 1
    e = shell(d, 32, 10, 46, 18, nf, "gable", "x", win="nse", ends=(0, 0 if L >= 5 else 1))
    link(d, 32, y, 14, "east")
    chimney(d, 46, 14, y, e["ridge"] + 1)
    d.hearth(45, y, 14, "west", y + 4, "bricks", "campfire")
    # Victoria ward: four beds, curtain on one side, nightstand on the other
    for x in (35, 39):
        d.bed(x, y, 11, "north", "white")
        d.bed(x, y, 17, "south", "white")
    curtain(d, [(34, 11), (34, 12), (38, 11), (38, 12), (34, 16), (34, 17), (38, 16), (38, 17)], y)
    stand(d, 36, y, 11, "oak_slab", CAND)
    stand(d, 40, y, 11, "oak_slab", "potted_red_tulip")
    stand(d, 36, y, 17, "oak_slab", "potted_cornflower")
    stand(d, 40, y, 17, "oak_slab", CAND)
    P(d, y, [(33, 11, "potted_fern"), (33, 17, chest("east"))])
    # nurse's writing desk and the fireside chairs
    P(d, y, [(42, 11, slab("dark_oak_slab", "top")), (43, 11, slab("dark_oak_slab", "top"))])
    d.candle(42, y + 1, 11, 1)
    d.chair(42, y, 12, "south", "oak", sit=False)
    sit(d, [(43, 13), (43, 15)], y, "west", "oak")
    P(d, y, [(44, 13, "red_carpet"), (44, 14, "red_carpet"), (44, 15, "red_carpet"),
             (42, 17, "water_cauldron[level=3]"), (43, 17, slab("oak_slab", "top"))])
    d.set(43, y + 1, 17, "potted_white_tulip")
    hang(d, [(38, 14), (42, 14)], 5)
    shutters(d, [(33, 9), (35, 9), (42, 9), (44, 9)], 3, "warped_trapdoor")
    d.sign(39, 4, 9, "north", ["VICTORIA", "WARD"], "oak")
    if nf > 1:                                                   # convalescent ward upstairs
        u = 7
        link(d, 32, u, 14, "east")
        d.hearth(45, u, 14, "west", 11, "bricks", "campfire")
        for x in (34, 37, 40, 43):
            d.bed(x, u, 17, "south", "white")
        for x, b in ((35, CAND), (38, "potted_allium"), (41, CAND), (44, "potted_oxeye_daisy")):
            stand(d, x, u, 17, "oak_slab", b)
        curtain(d, [(36, 16), (36, 17), (39, 16), (39, 17), (42, 16), (42, 17)], u)
        d.table(37, u, 12, "oak")
        d.chair(36, u, 12, "west", "oak", sit=False)
        d.chair(38, u, 12, "east", "oak", sit=False)
        d.bookshelf(33, u, 11, 2)
        sit(d, [(40, 11), (41, 11)], u, "north", "oak")
        d.set(44, u, 11, "potted_fern")
        d.set(44, u, 14, "red_carpet")
        hang(d, [(38, 14), (42, 14)], 10)
        window_box(d, [(34, 9, "red_tulip"), (40, 9, "cornflower"), (43, 9, "oxeye_daisy")], 7, "oak_trapdoor")


def hw_west_ward(d, L):
    y = Y0
    nf = 2 if L >= 4 else 1
    w = shell(d, 8, 10, 22, 18, nf, "gable", "x", win="nsw", ends=(1, 0))
    link(d, 22, y, 14, "west")
    chimney(d, 8, 14, y, w["ridge"] + 1)
    d.hearth(9, y, 14, "east", y + 4, "bricks", "campfire")
    # Albert ward: one row of beds under the north windows, patients' dining table on the south side
    for x in (11, 14, 17, 20):
        d.bed(x, y, 11, "north", "red")
    for x, b in ((12, CAND), (15, "potted_red_tulip"), (18, CAND), (21, "potted_allium")):
        stand(d, x, y, 11, "oak_slab", b)
    curtain(d, [(13, 11), (13, 12), (16, 11), (16, 12), (19, 11), (19, 12)], y)
    d.set(10, y, 11, "potted_fern")
    for x in (13, 14, 15, 16):
        d.table(x, y, 15, "oak", "block", "oak_planks")
    sit(d, [(13, 14), (14, 14), (15, 14), (16, 14)], y, "north", "oak", True)
    sit(d, [(13, 16), (14, 16), (15, 16), (16, 16)], y, "south", "oak", True)
    d.candle(14, y + 1, 15, 3)
    d.set(16, y + 1, 15, "potted_oxeye_daisy")
    P(d, y, [(10, 13, "red_carpet"), (10, 14, "red_carpet"), (10, 15, "red_carpet"), (21, 17, chest("west")),
             (20, 17, "water_cauldron[level=3]")])
    hang(d, [(14, 15), (18, 13)], 5)
    shutters(d, [(9, 9), (11, 9), (18, 9), (20, 9)], 3, "warped_trapdoor")
    d.sign(15, 4, 9, "north", ["ALBERT", "WARD"], "oak")
    if nf > 1:                                                   # day room upstairs
        u = 7
        link(d, 22, u, 14, "west")
        d.hearth(9, u, 14, "east", 11, "bricks", "campfire")
        P(d, u, [(10, 13, "orange_carpet"), (10, 14, "red_carpet"), (10, 15, "orange_carpet")])
        sit(d, [(11, 13), (11, 14), (11, 15)], u, "east", "oak")
        stand(d, 11, u, 12, "oak_slab", CAND)
        stand(d, 11, u, 16, "oak_slab", "potted_cornflower")
        d.table(16, u, 12, "oak")
        d.chair(15, u, 12, "west", "oak", sit=False)
        d.chair(17, u, 12, "east", "oak", sit=False)
        d.chair(16, u, 13, "south", "oak", sit=False)
        P(d, u, [(19, 11, "note_block[instrument=harp,note=0,powered=false]"),
                 (20, 11, "note_block[instrument=harp,note=5,powered=false]")])
        d.chair(19, u, 12, "south", "oak", sit=False)
        for x in (12, 13, 14, 15, 16):                           # full-height case (backs the schoolroom board)
            d.bookshelf(x, u, 17, 3)
        sit(d, [(19, 17), (20, 17)], u, "south", "oak")
        stand(d, 21, u, 17, "oak_slab", LAMP)
        hang(d, [(14, 14), (18, 14)], 10)
        window_box(d, [(10, 9, "allium"), (13, 9, "red_tulip"), (19, 9, "cornflower")], 7, "oak_trapdoor")


def hw_surgery(d, L):
    y = Y0
    shell(d, 22, 18, 32, 30, 1, "gable", "z", win="esw", wh=5, ends=(-1, 1))
    link(d, 31, y, 18, "south")
    d.fill(23, 1, 19, 31, 1, 29, "smooth_stone")
    # scrub-up corner behind a glazed screen
    P(d, y, [(23, 19, "water_cauldron[level=3]"), (24, 19, "water_cauldron[level=3]"),
             (25, 19, slab("smooth_stone_slab", "top")), (26, 19, chest("south"))])
    d.set(25, y + 1, 19, "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]")
    curtain(d, [(x, 21) for x in range(23, 29)], y, "glass_pane")
    # operating table under a three-lantern chandelier
    P(d, y, [(27, 24, "smooth_stone"), (27, 25, "smooth_stone")])
    P(d, y + 1, [(27, 24, "white_carpet"), (27, 25, "white_carpet")])
    hang(d, [(26, 24), (27, 24), (28, 24)], 6)
    stand(d, 25, y, 24, "smooth_stone_slab", "brewing_stand[has_bottle_0=true,has_bottle_1=true,has_bottle_2=false]")
    stand(d, 29, y, 25, "smooth_stone_slab", CAND)
    d.chair(26, y, 23, "north", "oak", sit=False)
    # students' gallery: three tiers facing the table
    for x in range(24, 31):
        d.chair(x, y, 27, "south", "oak", sit=False)
        d.set(x, y, 28, "oak_planks")
        d.chair(x, y + 1, 28, "south", "oak", sit=False)
        d.set(x, y, 29, "oak_planks")
        d.set(x, y + 1, 29, "oak_planks")
        d.chair(x, y + 2, 29, "south", "oak", sit=False)
    hang(d, [(24, 20), (30, 20)], 6)
    d.sign(27, 5, 31, "south", ["OPERATING", "THEATRE"], "oak")


def hw_children(d, L):
    y = Y0
    shell(d, 8, 18, 20, 30, 2, "gable", "z", mat="calcite", up="calcite", win="esw", ends=(-1, 1))
    link(d, 14, y, 18, "south")
    for z in (20, 23, 26):
        d.bed(9, y, z, "west", "light_blue")
        d.bed(19, y, z, "east", "light_blue")
    for z, b in ((21, CAND), (24, "potted_dandelion"), (27, CAND)):
        stand(d, 9, y, z, "birch_slab", b)
    for z, b in ((21, "potted_oxeye_daisy"), (24, CAND), (27, "potted_blue_orchid")):
        stand(d, 19, y, z, "birch_slab", b)
    d.set(14, y, 24, slab("birch_slab", "top"))
    d.set(14, y + 1, 24, "cake[bites=0]")
    d.chair(13, y, 24, "west", "birch", sit=False)
    d.chair(15, y, 24, "east", "birch", sit=False)
    d.rug(12, 23, 16, 25, y, ("light_blue_carpet", "yellow_carpet"), "check")      # 15 cells, around the table
    stair(d, 10, 29, y, 7, "east", rails=[(10, 29), (11, 28), (12, 28), (13, 28)])
    hang(d, [(12, 22), (16, 26)], 5)
    # schoolroom and playroom upstairs
    u = 7
    d.fill(12, 8, 18, 16, 9, 18, "black_wool")
    d.chair(14, u, 19, "north", "oak", sit=False)
    stand(d, 14, u, 20, "oak_slab", CAND)
    for z in (22, 24):
        for x in (11, 12, 16, 17):
            d.set(x, u, z, slab("birch_slab", "top"))
            d.chair(x, u, z + 1, "south", "birch", sit=False)
    d.bookshelf(9, u, 26)
    d.bookshelf(9, u, 27)
    P(d, u, [(19, 29, chest("west")), (19, 28, chest("west")), (9, 20, "potted_dandelion")])
    d.rug(16, 26, 18, 27, u, ("pink_carpet", "white_carpet"))
    d.chair(17, u, 29, "south", "oak", sit=False)
    hang(d, [(12, 20), (16, 24)], 10)
    d.sign(14, 5, 31, "south", ["CHILDREN'S", "WARD"], "oak")


def hw_garden(d):
    grass(d, 1, 32, 53, 49)
    d.fill(26, 1, 31, 27, 1, 49, "gravel")
    d.fill(2, 1, 40, 53, 1, 41, "gravel")
    for x in range(1, 54):
        d.set(x, 2, 50, "brick_wall")
    for z in range(32, 51):
        d.set(0, 2, z, "brick_wall")
        d.set(54, 2, z, "brick_wall")
    fountain(d, 26, 45, 2)
    for x, z in ((6, 36), (20, 36), (32, 46), (48, 37), (12, 46), (46, 46)):
        plant_tree(d, x, z)
    bed_of(d, 4, 43, 6, 44, "red_tulip")
    bed_of(d, 16, 43, 18, 44, "cornflower")
    bed_of(d, 36, 43, 38, 44, "oxeye_daisy")
    bed_of(d, 50, 43, 52, 44, "allium")
    bed_of(d, 10, 33, 13, 34, "azure_bluet")
    bed_of(d, 30, 37, 32, 38, "red_tulip")
    park_bench(d, 15, 38, "x", "north")
    park_bench(d, 22, 44, "z", "west")
    park_bench(d, 30, 44, "z", "east")
    post_lamp(d, 25, 39)
    post_lamp(d, 28, 42)


def hw_west_eaves(d):
    """Strip under the west eaves of the Albert ward and the children's ward: firewood for the two hearths,
    a water butt, a bench in the afternoon sun, pots by the bench and two wall lanterns."""
    y = Y0
    for z in (15, 16):                                           # log stack against the ward chimney
        d.set(7, y, z, log("oak_log", "z"))
        d.set(7, y + 1, z, log("oak_log", "z"))
    d.set(7, y, 12, "water_cauldron[level=3]")
    sit(d, [(7, 24), (7, 25)], y, "east", "oak")
    P(d, y, [(7, 23, "potted_red_tulip"), (7, 26, "potted_cornflower"), (7, 29, "composter[level=0]")])
    for z in (20, 28):
        d.set(7, 2, z, "oak_fence")                               # lantern posts
        d.set(7, 3, z, "oak_fence")
        d.set(7, 4, z, "lantern[hanging=false,waterlogged=false]")


def hw_herb_garden(d):
    """Walled physic garden east of the surgery (from L4): gravel cross path, four herb beds, potting bench."""
    y = Y0
    grass(d, 47, 21, 52, 29)
    d.fill(49, 1, 21, 50, 1, 29, "gravel")
    d.fill(47, 1, 25, 52, 1, 25, "gravel")
    for x in range(46, 54):
        for z in (20, 30):
            if not (z == 20 and x in (49, 50)):
                d.set(x, y, z, "brick_wall")
    for z in range(21, 30):
        d.set(46, y, z, "brick_wall")
        d.set(53, y, z, "brick_wall")
    for (x1, z1, x2, z2), f in (((47, 21, 48, 23), "fern"), ((51, 21, 52, 23), "lily_of_the_valley"),
                                ((47, 27, 48, 28), "sweet_berry_bush[age=2]"), ((51, 27, 52, 28), "azure_bluet")):
        bed_of(d, x1, z1, x2, z2, f)
    P(d, y, [(47, 29, "composter[level=3]"), (52, 29, "water_cauldron[level=3]"), (48, 24, "potted_allium"),
             (51, 26, "potted_red_tulip")])
    park_bench(d, 52, 24, "z", "east")
    d.set(49, y, 20, "oak_fence_gate[facing=north,in_wall=true,open=false,powered=false]")
    d.set(50, y, 20, "oak_fence_gate[facing=north,in_wall=true,open=false,powered=false]")
    post_lamp(d, 48, 26)


def hw_chapel(d):
    y = Y0
    shell(d, 36, 22, 44, 34, 1, "gable", "z", mat="stone_bricks", up="stone_bricks", gable_end="stone_bricks",
          wh=6, win="ew")
    entry(d, 40, y, 22, "south")
    for z in (24, 27, 30):                                       # lancets one pane taller
        d.set(36, 5, z, "glass_pane")
        d.set(44, 5, z, "glass_pane")
    for z in (25, 27, 29, 31):
        sit(d, [(38, z), (39, z), (41, z), (42, z)], y, "north", "oak")
    P(d, y, [(40, 33, "chiseled_stone_bricks"), (39, 33, "oak_fence"), (41, 33, "oak_fence"),
             (42, 32, "lectern[facing=north,has_book=false,powered=false]")])
    d.candle(40, y + 1, 33, 3)
    d.candle(39, y + 1, 33, 1)
    d.candle(41, y + 1, 33, 1)
    P(d, 5, [(39, 34, "yellow_stained_glass_pane"), (40, 34, "light_blue_stained_glass_pane"),
             (41, 34, "yellow_stained_glass_pane")])
    P(d, 6, [(39, 34, "light_blue_stained_glass_pane"), (40, 34, "red_stained_glass_pane"),
             (41, 34, "light_blue_stained_glass_pane")])
    hang(d, [(40, 24), (40, 28), (40, 32)], 7)


def hw_carriage(d):
    y = Y0
    shell(d, 47, 8, 54, 18, 1, "gable", "x", mat="bricks", win="n", ends=(0, 1))
    d.double_door(50, y, 8, "x", "south", "oak")
    for x in (50, 51):
        d.set(x, y, 9, AIR)
        d.set(x, y + 1, 9, AIR)
        d.set(x, 1, 7, "stone_bricks")
    # ambulance wagon: bed, canvas hood with a red cross, wheels, shafts
    for x in (50, 51):
        for z in (11, 12, 13):
            d.set(x, y, z, slab("spruce_slab", "top"))
            d.set(x, y + 1, z, "white_wool")
        d.set(x, y, 10, "oak_fence")
    d.set(51, y + 1, 12, "red_wool")
    for z in (11, 13):
        d.set(49, y, z, "dark_oak_trapdoor[facing=west,half=bottom,open=true,powered=false,waterlogged=false]")
        d.set(52, y, z, "dark_oak_trapdoor[facing=east,half=bottom,open=true,powered=false,waterlogged=false]")
    # horse stall
    P(d, y, [(48, 15, "oak_fence"), (49, 15, "oak_fence"), (50, 15, "oak_fence_gate[facing=north,in_wall=false,open=false,powered=false]"),
             (48, 17, "hay_block[axis=y]"), (49, 17, "hay_block[axis=x]"), (53, 17, "water_cauldron[level=3]"),
             (53, 9, chest("west"))])
    hang(d, [(51, 15)], 5)
    d.sign(51, 4, 7, "north", ["AMBULANCE"], "oak")


def hosp_hearthwood(rel, L):
    d = new("Hearthwood", rel, (55, 30, 51))
    adm_nf = 2 if L >= 3 else 1
    a = shell(d, 22, 8, 32, 18, adm_nf, "gable", "z")
    entry(d, 27, Y0, 8, "south")
    chimney(d, 22, 9, Y0, a["ridge"] + 1)
    # porch with a name board
    for y in range(Y0, 5):
        d.set(25, y, 5, "oak_fence")
        d.set(29, y, 5, "oak_fence")
    d.fill(25, 1, 4, 29, 1, 7, "stone_bricks")
    d.fill(25, 5, 5, 29, 5, 7, "oak_planks")
    d.fill(26, 4, 5, 28, 4, 5, log("stripped_oak_log", "x"))
    gable2(d, 25, 5, 29, 7, 6, "z", "dark_oak_stairs", "dark_oak_slab", "calcite", o=0, e0=0, e1=0)
    d.sign(27, 4, 4, "north", ["COTTAGE", "HOSPITAL"], "oak")
    hang(d, [(27, 6)], 4)
    P(d, Y0, [(26, 7, "potted_red_tulip"), (28, 7, "potted_cornflower")])
    shutters(d, [(23, 7), (25, 7), (29, 7), (31, 7)], 3, "warped_trapdoor")
    plants(d, [(22, 4, "red_tulip"), (23, 4, "oxeye_daisy"), (24, 4, "red_tulip"), (22, 6, "cornflower"),
               (24, 6, "allium"), (30, 4, "allium"), (31, 4, "oxeye_daisy"), (32, 4, "cornflower"),
               (30, 6, "red_tulip"), (32, 6, "oxeye_daisy")])
    post_lamp(d, 20, 4)
    post_lamp(d, 34, 4)
    hw_admin_ground(d, L)
    if L >= 2:
        hw_east_ward(d, L)
    if L >= 3:
        hw_admin_upper(d, L)
        window_box(d, [(24, 7, "red_tulip"), (30, 7, "cornflower")], 7, "oak_trapdoor")
        hw_west_ward(d, L)
        grass(d, 8, 2, 20, 7)
        grass(d, 33, 2, 44, 7)
        for x in (11, 17, 37, 43):
            plant_tree(d, x, 4)
        park_bench(d, 13, 6, "x", "north")
        park_bench(d, 39, 6, "x", "north")
    if L >= 4:
        hw_surgery(d, L)
        hw_herb_garden(d)
    if L >= 5:
        hw_children(d, L)
        hw_west_eaves(d)
        hw_garden(d)
        hw_chapel(d)
        hw_carriage(d)
    return d


# ============================================================================ NEOTERRA – medical centre

def nt_core_ground(d, L):
    y = Y0
    Q = "smooth_quartz"
    d.hut(15, y, 9)
    keep(d, 16, y, 9)
    sit(d, [(15, 10), (15, 11)], y, "west", "mangrove", True)
    d.set(15, y, 13, "potted_bamboo")
    for x in range(17, 22):
        d.set(x, y, 12, Q)
    d.chair(19, y, 13, "south", "mangrove", sit=False)
    P(d, y + 1, [(17, 12, "end_rod[facing=up]"), (19, 12, "black_stained_glass_pane"), (21, 12, "potted_azure_bluet")])
    d.item(27, y, 9, "brewing_stand")
    d.item(27, y, 10, "furnace", "west")
    d.item(27, y, 11, "water_cauldron[level=3]")
    d.sign(26, 4, 9, "south", ["PHARMACY"], "birch", glow=True, color="lime")
    if d.req["racks"]:
        d.rack(27, y, 12, "west")
    if L >= 3:
        for x, z in ((27, 13), (27, 14), (26, 9)):
            d.item(x, y, z, "barrel", "up")
    # glazed screen to the treatment bay; from L2 the stair flight forms its east half
    curtain(d, [(x, 15) for x in range(15, 20)], y, "white_stained_glass_pane", 3)
    if L == 1:
        curtain(d, [(x, 15) for x in range(22, 28)], y, "white_stained_glass_pane", 3)
    else:
        curtain(d, [(27, 15)], y, "white_stained_glass_pane", 3)
        stair(d, 22, 15, y, 7, "east", rails=[(22, 15), (23, 14), (24, 14), (25, 14), (23, 16), (24, 16), (25, 16)])
    d.bed(16, y, 17, "south", "cyan")
    stand(d, 17, y, 17, "smooth_quartz_slab", "potted_azure_bluet")
    d.set(15, y, 17, "potted_bamboo")
    curtain(d, [(19, 17), (22, 17)], y)
    d.bed(24, y, 17, "south", "cyan")
    stand(d, 25, y, 17, "smooth_quartz_slab", "black_stained_glass_pane")
    d.chair(23, y, 17, "south", "mangrove", sit=False)
    d.set(27, y, 17, "potted_white_tulip")
    panels(d, [(18, 11), (24, 11), (17, 16), (25, 16)], 6)


def nt_core_upper(d, L):
    y = 7
    for x in (16, 19, 22, 25):
        d.bed(x, y, 9, "north", "cyan")
    for x in (17, 20, 23, 26):
        stand(d, x, y, 9, "white_concrete", "end_rod[facing=up]")
    curtain(d, [(18, 9), (18, 10), (21, 9), (21, 10), (24, 9), (24, 10)], y)
    for x in (16, 17, 18):
        d.set(x, y, 16, slab("smooth_quartz_slab", "top"))
    d.set(16, y + 1, 16, "black_stained_glass_pane")
    d.chair(17, y, 17, "south", "mangrove", sit=False)
    d.set(15, y, 17, "potted_bamboo")
    sit(d, [(15, 12), (15, 13)], y, "west", "mangrove")
    d.set(15, y, 14, "potted_azure_bluet")
    panels(d, [(18, 11), (24, 11), (20, 16)], 11)
    # roof terrace: planters along the north parapet, plant room and antenna
    ry = 12
    P(d, ry, [(17, 9, "moss_block"), (18, 9, "moss_block"), (19, 9, "moss_block"), (24, 9, "moss_block"),
              (25, 9, "moss_block"), (25, 15, "smooth_stone"), (26, 15, "smooth_stone"), (25, 16, "smooth_stone"),
              (26, 16, "smooth_stone"), (16, 17, "lightning_rod[facing=up,powered=false,waterlogged=false]")])
    P(d, ry + 1, [(18, 9, "flowering_azalea"), (24, 9, "azalea"), (17, 9, "potted_bamboo"),
                  (25, 15, "iron_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]"),
                  (26, 16, "iron_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]")])


def nt_wing(d, L):
    y = Y0
    Q = "smooth_quartz"
    e = shell(d, 28, 8, 42, 18, 2, "flat", glassy=True, win="nse")
    entry(d, 35, y, 8, "south", double=True)
    for x in range(34, 38):
        for z in (6, 7):
            d.set(x, 6, z, slab("smooth_quartz_slab", "top"))
    d.sign(35, 6, 5, "north", ["OUTPATIENTS"], "birch", glow=True, color="lime")
    link(d, 28, 7, 12, "east")
    # reception and waiting lounge
    for x in (38, 39, 40):
        d.set(x, y, 11, Q)
    d.chair(39, y, 10, "north", "mangrove", sit=False)
    d.set(38, y + 1, 11, "black_stained_glass_pane")
    sit(d, [(30, 11), (31, 11), (32, 11)], y, "north", "mangrove")
    d.set(31, y, 12, slab("smooth_quartz_slab", "top"))
    d.set(31, y + 1, 12, "potted_bamboo")
    sit(d, [(30, 13), (31, 13), (32, 13)], y, "south", "mangrove")
    d.set(41, y, 9, "potted_bamboo")
    # two consulting rooms behind a glazed partition
    curtain(d, [(x, 14) for x in range(29, 42) if x not in (31, 38)], y, "light_gray_stained_glass_pane", 4)
    curtain(d, [(35, 15), (35, 16), (35, 17)], y, "light_gray_stained_glass_pane", 4)
    d.door(31, y, 14, "south", "birch")
    d.door(38, y, 14, "south", "birch")
    d.set(30, y, 16, slab("smooth_quartz_slab", "top"))
    d.set(30, y + 1, 16, "black_stained_glass_pane")
    d.chair(29, y, 16, "west", "mangrove", sit=False)
    d.chair(31, y, 16, "east", "mangrove", sit=False)
    couch(d, [(33, 17), (34, 17)], y, "smooth_quartz_slab")
    d.set(34, y, 15, "water_cauldron[level=3]")
    couch(d, [(36, 17), (37, 17)], y, "smooth_quartz_slab")
    d.chair(40, y, 16, "east", "mangrove", sit=False)
    d.set(41, y, 15, slab("smooth_quartz_slab", "top"))
    d.set(41, y + 1, 15, "black_stained_glass_pane")
    d.set(36, y, 15, chest("east"))
    d.set(41, y, 17, "potted_white_tulip")
    panels(d, [(31, 11), (39, 11), (32, 16), (39, 16)], 6)
    # ward B upstairs
    u = 7
    for x in (30, 34, 38):
        d.bed(x, u, 9, "north", "lime")
        d.bed(x, u, 17, "south", "lime")
    for x in (31, 35, 39):
        stand(d, x, u, 9, "white_concrete", "end_rod[facing=up]")
        stand(d, x, u, 17, "white_concrete", "potted_azure_bluet")
    curtain(d, [(33, 9), (33, 10), (37, 9), (37, 10), (33, 16), (33, 17), (37, 16), (37, 17)], u)
    for z in (12, 13):
        d.set(41, u, z, slab("smooth_quartz_slab", "top"))
    d.set(41, u + 1, 12, "black_stained_glass_pane")
    d.chair(40, u, 12, "west", "mangrove", sit=False)
    d.set(41, u, 9, "potted_bamboo")
    panels(d, [(32, 13), (37, 13)], 11)
    # roof: two rows of solar panels and a vent
    ry = e["top"] + 2
    for z in (11, 12, 14, 15):
        for x in range(31, 40):
            d.set(x, ry, z, "daylight_detector[inverted=false,power=0]")
    P(d, ry, [(40, 10, "smooth_stone"), (30, 16, "moss_block"), (31, 16, "moss_block")])
    d.set(40, ry + 1, 10, "iron_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]")


def nt_tower_floor(d, k, y):
    """Hand-made layout of tower floor k (each floor is its own room)."""
    Q = "smooth_quartz"
    QS = slab("smooth_quartz_slab", "top")
    c = y + 4
    if k == 0:                                                   # surgery
        d.set(22, y, 24, "white_concrete")
        d.set(22, y, 25, "white_concrete")
        P(d, y + 1, [(22, 24, "white_carpet"), (22, 25, "white_carpet")])
        panels(d, [(21, 24), (22, 24), (23, 24), (21, 25), (22, 25), (23, 25)], c)
        stand(d, 20, y, 24, "smooth_quartz_slab", "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]")
        d.set(24, y, 25, "iron_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
        P(d, y, [(23, 19, "water_cauldron[level=3]"), (24, 19, QS), (25, 19, "water_cauldron[level=3]")])
        d.sign(22, y + 2, 19, "south", ["SURGERY"], "birch", glow=True, color="lime")
        for x in range(19, 26):
            d.set(x, y, 29, QS)
        P(d, y + 1, [(20, 29, "brewing_stand[has_bottle_0=true,has_bottle_1=true,has_bottle_2=false]"),
                     (23, 29, "potted_azure_bluet")])
        P(d, y, [(15, 29, "barrel[facing=up,open=false]"), (16, 29, "barrel[facing=up,open=false]"), (15, 28, chest("east"))])
        # two-bed recovery bay on the east wall, curtained off, clear of the ambulance door at z=23
        d.bed(27, y, 20, "east", "light_gray")
        d.bed(27, y, 26, "east", "light_gray")
        curtain(d, [(26, 21), (27, 21), (26, 25), (27, 25)], y)
        P(d, y, [(27, 19, "white_concrete"), (27, 27, "white_concrete")])
        P(d, y + 1, [(27, 19, "black_stained_glass_pane"), (27, 27, "black_stained_glass_pane")])
        panels(d, [(19, 21), (25, 28), (26, 20), (26, 26)], c)
    elif k == 1:                                                 # maternity
        for z in (20, 23, 26):
            d.bed(27, y, z, "east", "pink")
        couch(d, [(27, 21), (27, 24), (27, 27)], y, "smooth_quartz_slab")
        curtain(d, [(26, 22), (27, 22), (26, 25), (27, 25)], y)
        d.set(27, y, 29, "potted_white_tulip")
        couch(d, [(18, 27), (19, 27), (18, 29)], y, "smooth_quartz_slab", "light_blue_carpet")
        d.rug(19, 28, 20, 29, y, ("pink_carpet",), "plain")
        for x in (19, 20):
            d.set(x, y, 20, QS)
        d.chair(19, y, 21, "south", "mangrove", sit=False)
        d.set(20, y + 1, 20, "black_stained_glass_pane")
        sit(d, [(24, 20), (24, 26)], y, "west", "mangrove")
        panels(d, [(21, 22), (21, 27), (25, 24)], c)
    elif k == 2:                                                 # consultants' offices
        curtain(d, [(22, z) for z in range(19, 30) if z not in (21, 27)], y, "light_gray_stained_glass_pane", 4)
        curtain(d, [(x, 24) for x in range(23, 28)], y, "light_gray_stained_glass_pane", 4)
        d.door(22, y, 21, "east", "birch")
        d.door(22, y, 27, "east", "birch")
        for z in (21, 22):
            d.set(26, y, z, QS)
        d.chair(27, y, 21, "east", "mangrove", sit=False)
        sit(d, [(24, 21), (24, 22)], y, "west", "mangrove")
        d.set(26, y + 1, 22, "black_stained_glass_pane")
        d.bookshelf(27, y, 23, 2)
        d.set(23, y, 19, "potted_bamboo")
        for x in (25, 26):
            d.set(x, y, 27, QS)
        d.chair(25, y, 28, "south", "mangrove", sit=False)
        d.chair(25, y, 26, "north", "mangrove", sit=False)
        d.set(26, y + 1, 27, "end_rod[facing=up]")
        d.bookshelf(27, y, 28, 2)
        d.bookshelf(27, y, 29, 2)
        d.set(23, y, 29, "potted_azure_bluet")
        P(d, y, [(19, 27, QS), (20, 27, QS), (17, 29, chest("north", "left")), (18, 29, chest("north", "right"))])
        d.chair(19, y, 28, "south", "mangrove", sit=False)
        d.set(20, y + 1, 27, "black_stained_glass_pane")
        sit(d, [(21, 20), (21, 21), (21, 22)], y, "east", "mangrove")   # waiting seats against the glass
        d.set(20, y, 21, QS)
        d.set(20, y + 1, 21, "potted_azure_bluet")
        P(d, y, [(18, 19, "potted_bamboo"), (21, 25, "water_cauldron[level=3]")])
        panels(d, [(25, 21), (25, 27), (19, 22)], c)
    elif k == 3:                                                 # intensive care
        for x in (19, 22, 25):
            d.bed(x, y, 19, "north", "cyan")
            d.bed(x, y, 29, "south", "cyan")
        for x in (20, 23, 26):
            for z in (19, 29):
                stand(d, x, y, z, "smooth_quartz_slab", "black_stained_glass_pane")
        for x in (18, 21, 24):
            for z in (19, 29):
                d.set(x, y, z, "iron_bars")
        for x in (21, 22, 23):
            d.set(x, y, 24, QS)
        d.chair(22, y, 25, "south", "mangrove", sit=False)
        d.set(21, y + 1, 24, "black_stained_glass_pane")
        d.set(23, y + 1, 24, "potted_azure_bluet")
        panels(d, [(20, 22), (24, 22), (20, 26), (24, 26)], c)
    elif k == 4:                                                 # staff canteen
        P(d, y, [(27, 20, "smoker[facing=west,lit=false]"), (27, 21, QS), (27, 22, "water_cauldron[level=3]"),
                 (27, 23, QS), (27, 24, "furnace[facing=west,lit=false]"), (27, 25, QS)])
        P(d, y + 1, [(27, 21, "cake[bites=0]"), (27, 23, "flower_pot"), (27, 25, "potted_bamboo")])
        for z in (22, 26):
            for x in range(19, 24):
                d.set(x, y, z, Q)
            sit(d, [(x, z - 1) for x in range(19, 24)], y, "north", "mangrove")
            sit(d, [(x, z + 1) for x in range(19, 24)], y, "south", "mangrove")
            d.set(21, y + 1, z, "potted_azure_bluet")
        d.set(17, y, 29, "potted_bamboo")
        panels(d, [(21, 21), (21, 27), (26, 23)], c)
    elif k == 5:                                                 # physiotherapy
        for x in range(20, 25):
            d.set(x, y, 20, "birch_fence")
            d.set(x, y, 22, "birch_fence")
        d.rug(18, 26, 20, 28, y, ("green_carpet",), "plain")
        for x in range(22, 27):
            for z in range(25, 30):
                if x in (22, 26) or z in (25, 29):
                    d.set(x, y, z, Q)
                else:
                    d.set(x, y, z, "water[level=0]")
        for x in range(22, 27):                                  # hand rails round the hydrotherapy pool,
            d.set(x, y + 1, 29, "iron_bars")                     # open on the north (entry) side
        for z in range(25, 29):
            d.set(22, y + 1, z, "iron_bars")
            d.set(26, y + 1, z, "iron_bars")
        couch(d, [(26, 20), (26, 21)], y, "smooth_quartz_slab")
        d.set(27, y, 23, "potted_bamboo")
        panels(d, [(22, 21), (24, 27), (19, 27)], c)
    elif k == 6:                                                 # board room
        for x in range(19, 26):
            d.set(x, y, 24, Q)
        sit(d, [(x, 23) for x in range(19, 26)], y, "north", "mangrove")
        sit(d, [(x, 25) for x in range(19, 26)], y, "south", "mangrove")
        d.chair(18, y, 24, "west", "mangrove", sit=False)
        d.chair(26, y, 24, "east", "mangrove", sit=False)
        d.fill(20, y + 1, 19, 24, y + 2, 19, "black_concrete")
        P(d, y, [(27, 19, "potted_bamboo"), (27, 29, "potted_bamboo"), (19, 29, "potted_azure_bluet")])
        P(d, y + 1, [(20, 24, "potted_white_tulip"), (24, 24, "potted_white_tulip")])
        d.set(22, y, 21, "lectern[facing=south,has_book=false,powered=false]")
        d.bookshelf(27, y, 25, 2)
        d.bookshelf(27, y, 26, 2)
        P(d, y, [(25, 29, chest("north", "left")), (26, 29, chest("north", "right"))])
        panels(d, [(20, 24), (24, 24), (22, 21), (22, 27)], c)


def nt_tower(d, L):
    tnf = 4 if L == 4 else 7
    t = shell(d, 14, 18, 28, 30, tnf, "flat", glassy=True, win="esw")
    link(d, 21, Y0, 18, "south")
    for k in range(tnf - 1):                                     # scissor stair in the west bay
        y = Y0 + 5 * k
        if k % 2 == 0:
            stair(d, 15, 20, y, y + 5, "south")
        else:
            stair(d, 16, 24, y, y + 5, "north")
    for k in range(1, tnf):
        for z in range(20, 25):
            d.set(17, Y0 + 5 * k, z, "glass_pane")
    for k in range(tnf):
        nt_tower_floor(d, k, Y0 + 5 * k)
    ry = t["top"] + 2
    if tnf >= 7:                                                 # helipad
        d.fill(16, ry - 1, 20, 26, ry - 1, 28, "gray_concrete")
        d.layer(ry - 1, 19, 22, ["#...#", "#...#", "#####", "#...#", "#...#"], {"#": "white_concrete"})
        for x, z in ((16, 20), (26, 20), (16, 28), (26, 28)):
            d.set(x, ry, z, "end_rod[facing=up]")
    else:
        for z in (21, 22, 25, 26):
            for x in range(17, 26):
                d.set(x, ry, z, "daylight_detector[inverted=false,power=0]")
        P(d, ry, [(26, 28, "smooth_stone"), (16, 19, "lightning_rod[facing=up,powered=false,waterlogged=false]")])
    # ambulance bay with canopy, bay markings and a parked ambulance
    for x in range(30, 42):
        for z in range(20, 27):
            d.set(x, 1, z, "polished_andesite")
            d.set(x, 6, z, slab("smooth_quartz_slab", "top"))
    for x in (30, 34, 38):
        for y in range(Y0, 6):
            d.set(x, y, 26, "light_gray_concrete")
    for z in (20, 22, 24, 26):
        d.set(36, 1, z, "yellow_concrete")
    for x in (32, 33):
        for z in range(21, 25):
            d.set(x, 2, z, "white_concrete")
            d.set(x, 3, z, "white_concrete" if z != 21 else "light_blue_stained_glass")
        d.set(x, 3, 23, REDC)
    d.set(32, 4, 22, "red_stained_glass")
    d.set(33, 4, 22, "blue_stained_glass")
    panels(d, [(35, 23), (39, 23)], 6)
    link(d, 28, Y0, 23, "east")


def nt_research(d, L):
    Q = "smooth_quartz"
    QS = slab("smooth_quartz_slab", "top")
    r = shell(d, 2, 8, 14, 30, 3, "flat", glassy=True, win="nsw")
    link(d, 14, Y0, 12, "west")
    d.sign(8, 6, 7, "north", ["RESEARCH"], "birch", glow=True, color="lime")
    stair(d, 3, 28, Y0, 7, "north", rails=[(3, 28), (4, 25), (4, 26), (4, 27)])
    stair(d, 13, 28, 7, 12, "north", rails=[(13, 28), (12, 25), (12, 26), (12, 27)])
    y = Y0                                                       # laboratory
    for z in (12, 15):
        for x in range(6, 10):
            d.set(x, y, z, Q)
    P(d, y + 1, [(6, 12, "brewing_stand[has_bottle_0=true,has_bottle_1=true,has_bottle_2=true]"),
                 (8, 12, "amethyst_cluster[facing=up,waterlogged=false]"), (9, 12, "flower_pot"),
                 (7, 15, "lightning_rod[facing=up,powered=false,waterlogged=false]"),
                 (9, 15, "brewing_stand[has_bottle_0=false,has_bottle_1=true,has_bottle_2=false]")])
    sit(d, [(7, 13), (9, 13), (6, 16), (8, 16)], y, "south", "birch")
    for z in (10, 11, 12):
        d.set(3, y, z, Q)
        d.set(3, y + 1, z, "light_gray_stained_glass_pane")
    for x in range(5, 12):
        d.set(x, y, 29, QS)
    P(d, y + 1, [(6, 29, "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=false]"),
                 (8, 29, "water_cauldron[level=3]"), (10, 29, "black_stained_glass_pane")])
    d.chair(10, y, 28, "north", "birch", sit=False)
    for z in (20, 21):
        d.set(13, y, z, "white_shulker_box[facing=up]")
    P(d, y, [(13, 22, "grindstone[face=floor,facing=north]"), (13, 23, chest("west")), (7, 22, Q), (8, 22, Q)])
    d.set(7, y + 1, 22, "black_stained_glass_pane")
    d.chair(7, y, 23, "south", "birch", sit=False)
    for z in (17, 18, 19):                                       # sample store
        d.set(3, y, z, "barrel[facing=east,open=false]")
    for x in range(6, 10):                                       # microscope bench
        d.set(x, y, 26, QS)
    P(d, y + 1, [(6, 26, "end_rod[facing=up]"), (7, 26, "amethyst_cluster[facing=up,waterlogged=false]"),
                 (9, 26, "flower_pot")])
    sit(d, [(6, 25), (8, 25)], y, "north", "birch")
    panels(d, [(7, 13), (7, 21), (9, 26)], 6)
    y = 7                                                        # medical library and records
    for z in (11, 14):
        for x in range(6, 11):
            d.bookshelf(x, y, z, 2)
    for x in (6, 9):
        d.set(x, y, 19, Q)
        d.chair(x, y, 18, "north", "birch", sit=False)
        d.chair(x, y, 20, "south", "birch", sit=False)
        d.set(x, y + 1, 19, "end_rod[facing=up]")
    P(d, y, [(3, 9, chest("east", "left")), (3, 10, chest("east", "right")), (13, 9, "potted_bamboo"),
             (8, 24, "potted_azure_bluet")])
    panels(d, [(8, 12), (8, 19), (8, 25)], 11)
    y = 12                                                       # seminar room
    for x in (6, 7, 8):
        d.set(x, y, 9, Q)
        d.set(x, y + 1, 9, "black_concrete")
        d.set(x, y + 2, 9, "black_concrete")
    for z in (12, 14, 16, 18):
        sit(d, [(5, z), (6, z), (7, z), (9, z), (10, z)], y, "south", "birch")
    d.set(4, y, 10, slab("smooth_quartz_slab", "top"))
    d.set(4, y + 1, 10, "black_stained_glass_pane")
    P(d, y, [(3, 9, "potted_bamboo"), (11, 9, "potted_bamboo"), (8, 23, "potted_white_tulip")])
    d.set(9, y, 10, "lectern[facing=south,has_book=false,powered=false]")
    for z in (20, 21, 22):
        d.bookshelf(3, y, z, 2)
    panels(d, [(7, 11), (7, 17), (8, 24)], 16)
    ry = r["top"] + 2                                            # roof garden
    for x in range(4, 13):
        d.set(x, ry, 10, "moss_block")
    P(d, ry, [(4, 20, "moss_block"), (5, 20, "moss_block"), (4, 21, "moss_block"), (11, 26, "smooth_stone")])
    P(d, ry + 1, [(5, 10, "flowering_azalea"), (8, 10, "azalea"), (11, 10, "flowering_azalea"), (4, 20, "potted_bamboo"),
                  (11, 26, "iron_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]")])


def nt_garden(d):
    grass(d, 2, 32, 50, 49)
    d.fill(2, 1, 40, 50, 1, 41, "polished_diorite")
    d.fill(25, 1, 32, 26, 1, 39, "polished_diorite")
    fountain(d, 26, 45, 2)
    bed_of(d, 4, 34, 7, 36, "allium")
    bed_of(d, 12, 34, 15, 36, "azure_bluet")
    bed_of(d, 34, 34, 37, 36, "white_tulip")
    bed_of(d, 42, 34, 45, 36, "cornflower")
    for x, z in ((6, 45), (14, 46), (36, 46), (44, 45), (19, 35), (31, 35)):
        plant_tree(d, x, z)
    park_bench(d, 9, 42, "x", "south")
    park_bench(d, 40, 42, "x", "south")
    park_bench(d, 22, 44, "z", "west")
    park_bench(d, 30, 44, "z", "east")
    post_lamp(d, 24, 38)
    post_lamp(d, 28, 42)


def hosp_neoterra(rel, L):
    d = new("Neoterra", rel, (53, 45, 51), paving="smooth_stone")
    cnf = 1 if L == 1 else 2
    c = shell(d, 14, 8, 28, 18, cnf, "flat", glassy=True, win="nsw")
    entry(d, 20, Y0, 8, "south", double=True)
    for x in range(17, 25):
        for z in range(4, 8):
            d.set(x, 6, z, slab("smooth_quartz_slab", "top"))
    d.sign(21, 6, 3, "north", ["MEDICAL", "CENTRE"], "birch", glow=True, color="lime")
    cy = c["top"] + 3                                            # cross on the parapet
    P(d, cy, [(26, 8, REDC)])
    P(d, cy + 1, [(25, 8, REDC), (26, 8, "sea_lantern"), (27, 8, REDC)])
    P(d, cy + 2, [(26, 8, REDC)])
    d.fill(19, 1, 0, 22, 1, 7, "polished_diorite")
    for x in (12, 30):
        post_lamp(d, x, 5)
    P(d, 2, [(13, 3, "moss_block"), (29, 3, "moss_block")])
    P(d, 3, [(13, 3, "flowering_azalea"), (29, 3, "flowering_azalea")])
    nt_core_ground(d, L)
    if cnf > 1:
        nt_core_upper(d, L)
    if L >= 3:
        nt_wing(d, L)
    if L >= 5:                                                   # before the tower: its flights cut the research
        nt_research(d, L)                                        # wing's cantilevered roof edge
        nt_garden(d)
    if L >= 4:
        nt_tower(d, L)
    return d


# ============================================================================ CASCADIA – mountain infirmary

def cs_core_ground(d, L):
    y = Y0
    d.hut(7, y, 7)
    keep(d, 8, y, 7)
    for x in (9, 10, 11):
        d.set(x, y, 10, slab("spruce_slab", "top"))
    d.chair(10, y, 11, "south", "spruce", sit=False)
    d.candle(9, y + 1, 10, 2)
    d.set(11, y + 1, 10, "potted_fern")
    d.item(15, y, 7, "brewing_stand")
    d.item(15, y, 8, "furnace", "west")
    d.item(15, y, 9, "water_cauldron[level=3]")
    if d.req["racks"]:
        d.rack(15, y, 10, "west")
    d.hearth(7, y, 13, "east", y + 4, "cobblestone", "campfire")
    P(d, y, [(8, 12, "brown_carpet"), (8, 13, "brown_carpet"), (8, 14, "brown_carpet")])
    d.chair(9, y, 13, "east", "spruce", sit=False)
    if L >= 3:
        for z in (13, 14, 15):
            d.item(15, y, z, "barrel", "up")
        stair(d, 8, 15, y, 7, "east", rails=[(8, 15), (9, 14), (10, 14), (11, 14)])
    if L == 1:
        d.bed(10, y, 15, "south", "white")
        d.bed(13, y, 15, "south", "white")
        stand(d, 11, y, 15, "spruce_slab", CAND)
        d.set(14, y, 15, "potted_fern")
    else:
        couch(d, [(13, 15), (14, 15)], y, "spruce_slab")
        if L == 2:
            P(d, y, [(8, 15, log("spruce_log", "x")), (9, 15, log("spruce_log", "x"))])
            d.set(8, y + 1, 15, log("spruce_log", "x"))
    hang(d, [(11, 8), (12, 12)], 5)


def cs_core_upper(d, L):
    y = 7
    d.hearth(7, y, 13, "east", 11, "cobblestone", "campfire")
    P(d, y, [(8, 12, "green_carpet"), (8, 13, "brown_carpet"), (8, 14, "green_carpet")])
    sit(d, [(9, 12), (9, 13)], y, "east", "spruce")
    for x in (9, 10):
        d.set(x, y, 7, slab("spruce_slab", "top"))
    d.chair(9, y, 8, "south", "spruce", sit=False)
    d.candle(10, y + 1, 7, 1)
    d.bookshelf(7, y, 9, 2)
    d.bookshelf(7, y, 10, 2)
    d.set(12, y, 7, chest("south"))
    sit(d, [(15, 9), (15, 10), (15, 11)], y, "east", "spruce")
    d.table(14, y, 10, "spruce")
    d.set(15, y, 7, "potted_fern")
    hang(d, [(11, 8), (11, 12)], 10)


def cs_ward(d, L):
    y = Y0
    wx2 = 30 if L == 2 else 36
    w = shell(d, 16, 8, wx2, 16, 1, "gable", "x", win="nse", ends=(0, 1))
    link(d, 16, y, 12, "east")
    chimney(d, wx2, 12, y, w["ridge"] + 1)
    d.hearth(wx2 - 1, y, 12, "west", y + 4, "cobblestone", "campfire")
    xs = (19, 23) if L == 2 else (19, 23, 27, 31)
    for x in xs:
        d.bed(x, y, 9, "north", "white")
        d.bed(x, y, 15, "south", "white")
        stand(d, x + 1, y, 9, "spruce_slab", LAMP)
        stand(d, x + 1, y, 15, "spruce_slab", "potted_fern")
    d.rug(18, 12, wx2 - 5, 12, y, ("green_carpet",), "plain")
    sit(d, [(wx2 - 3, 11), (wx2 - 3, 13)], y, "west", "spruce")
    P(d, y, [(wx2 - 2, 11, "brown_carpet"), (wx2 - 2, 12, "brown_carpet"), (wx2 - 2, 13, "brown_carpet"),
             (17, 9, chest("east")), (17, 15, "potted_fern")])
    hang(d, [(22, 12), (26, 12)] + ([(30, 12)] if L >= 3 else []), 5)
    sh = [(20, 7), (22, 7), (26, 7), (28, 7)] + ([(32, 7), (34, 7)] if L >= 3 else [])
    shutters(d, sh, 3, "mangrove_trapdoor")
    d.sign(24, 4, 7, "north", ["WARD"], "spruce")
    if L >= 3:                                                   # screened sleeping porch
        d.fill(16, 1, 17, wx2, 1, 20, "spruce_planks")
        d.fill(16, 6, 17, wx2, 6, 20, slab("spruce_slab"))
        posts = (16, 20, 27, 31, 36)
        for x in range(16, wx2 + 1):
            if x in posts:
                for yy in range(y, 6):
                    d.set(x, yy, 20, log("spruce_log"))
            elif x not in (23, 24):
                d.set(x, y, 20, "spruce_fence")
        d.door(22, y, 16, "south", "spruce")
        for x, z in ((18, 18), (19, 18), (26, 18), (27, 18), (32, 18), (33, 18)):
            d.chair(x, y, z, "north", "spruce", sit=False)
        for x in (20, 28, 34):
            d.set(x, y, 18, slab("spruce_slab", "top"))
        d.set(20, y + 1, 18, "potted_fern")
        d.set(34, y + 1, 18, LAMP)
        d.set(17, y, 19, "potted_blue_orchid")
        hang(d, [(21, 18), (30, 18)], 5)


def cs_south(d, L):
    y = Y0
    z1 = 26
    sn = shell(d, 6, z1, 40, z1 + 8, 2, "gable", "x")
    entry(d, 23, y, z1, "south", double=True)
    d.fill(23, 1, 21, 24, 1, z1 - 1, "spruce_planks")
    chimney(d, 6, 30, y, sn["ridge"] + 1)
    chimney(d, 40, 30, y, sn["ridge"] + 1)
    d.hearth(7, y, 30, "east", y + 4, "cobblestone", "campfire")
    stair(d, 8, 33, y, 7, "east", rails=[(8, 33), (9, 32), (10, 32), (11, 32)])
    # day room (west)
    P(d, y, [(8, 29, "brown_carpet"), (8, 30, "green_carpet"), (8, 31, "brown_carpet"),
             (9, 29, "brown_carpet"), (9, 30, "green_carpet"), (9, 31, "brown_carpet")])
    sit(d, [(10, 29), (10, 30), (10, 31)], y, "east", "spruce")
    stand(d, 10, y, 28, "spruce_slab", LAMP)
    d.bookshelf(13, y, 27, 2)
    d.bookshelf(14, y, 27, 2)
    d.table(13, y, 30, "spruce")
    d.chair(13, y, 29, "north", "spruce", sit=False)
    d.chair(13, y, 31, "south", "spruce", sit=False)
    for z in range(27, 34):
        if z != 30:
            for yy in range(y, 6):
                d.set(16, yy, z, log("stripped_spruce_log", "z"))
    d.door(16, y, 30, "east", "spruce")
    # dining hall (middle)
    for x in range(19, 28):
        d.table(x, y, 30, "spruce", "block", "spruce_planks")
    sit(d, [(x, 29) for x in range(19, 28)], y, "north", "spruce")
    sit(d, [(x, 31) for x in range(19, 28)], y, "south", "spruce")
    P(d, y + 1, [(20, 30, CAND), (23, 30, "potted_fern"), (26, 30, CAND)])
    for z in range(27, 34):
        if z != 30:
            for yy in range(y, 6):
                d.set(30, yy, z, log("stripped_spruce_log", "z"))
    d.door(30, y, 30, "east", "spruce")
    # kitchen (east)
    P(d, y, [(39, 28, "smoker[facing=west,lit=false]"), (39, 29, slab("spruce_slab", "top")),
             (39, 30, "water_cauldron[level=3]"), (39, 31, slab("spruce_slab", "top")),
             (39, 32, "furnace[facing=west,lit=false]"), (35, 30, "spruce_planks"), (36, 30, "spruce_planks"),
             (31, 33, "barrel[facing=up,open=false]"), (32, 33, "barrel[facing=up,open=false]")])
    P(d, y + 1, [(35, 30, "cake[bites=0]"), (36, 30, "flower_pot"), (39, 29, "potted_fern")])
    hang(d, [(11, 30), (23, 30), (35, 30)], 5)
    # staff dormitory upstairs
    u = 7
    d.hearth(7, u, 30, "east", 11, "cobblestone", "campfire")
    sit(d, [(9, 29), (9, 31)], u, "east", "spruce")
    d.set(8, u, 30, "brown_carpet")
    for x in (15, 19, 23, 27, 31, 35):
        d.bed(x, u, 27, "north", "green")
        d.set(x + 1, u, 27, chest("south"))
    P(d, u, [(17, 33, "water_cauldron[level=3]"), (25, 33, "water_cauldron[level=3]"), (33, 33, "water_cauldron[level=3]"),
             (21, 33, slab("spruce_slab", "top")), (29, 33, slab("spruce_slab", "top"))])
    d.chair(21, u, 32, "north", "spruce", sit=False)
    d.chair(29, u, 32, "north", "spruce", sit=False)
    d.candle(21, u + 1, 33, 1)
    d.set(29, u + 1, 33, "potted_blue_orchid")
    hang(d, [(16, 30), (28, 30)], 10)
    # verandah
    d.fill(6, 1, z1 + 9, 40, 1, z1 + 11, "spruce_planks")
    d.fill(6, 6, z1 + 9, 40, 6, z1 + 11, slab("spruce_slab"))
    for x in (6, 12, 18, 29, 35, 40):
        for yy in range(y, 6):
            d.set(x, yy, z1 + 11, log("spruce_log"))
    d.door(23, y, z1 + 8, "north", "spruce")
    for x in (9, 15, 21, 26, 32, 37):
        d.chair(x, y, z1 + 10, "north", "spruce", sit=False)
    hang(d, [(15, z1 + 10), (32, z1 + 10)], 5)


def cs_doctor(d):
    y = Y0
    dh = shell(d, 40, 4, 50, 14, 2, "gable", "z", mat="mangrove_planks", up="mangrove_planks")
    entry(d, 45, y, 4, "south")
    chimney(d, 40, 8, y, dh["ridge"] + 1)
    d.hearth(41, y, 8, "east", y + 4, "cobblestone", "campfire")
    sit(d, [(43, 7), (43, 8), (43, 9)], y, "east", "spruce")
    P(d, y, [(42, 7, "red_carpet"), (42, 8, "red_carpet"), (42, 9, "red_carpet")])
    stand(d, 43, y, 6, "spruce_slab", LAMP)
    P(d, y, [(42, 13, "smoker[facing=north,lit=false]"), (43, 13, slab("spruce_slab", "top")),
             (44, 13, "water_cauldron[level=3]"), (45, 13, slab("spruce_slab", "top")),
             (46, 13, "furnace[facing=north,lit=false]"), (44, 11, "spruce_planks"), (45, 11, "spruce_planks")])
    d.chair(44, y, 10, "north", "spruce", sit=False)
    d.chair(45, y, 12, "south", "spruce", sit=False)
    d.set(44, y + 1, 11, "potted_fern")
    stair(d, 49, 6, y, 7, "south", rails=[(49, 6), (48, 7), (48, 8), (48, 9)])
    hang(d, [(45, 8), (44, 12)], 5)
    u = 7
    d.hearth(41, u, 8, "east", 11, "cobblestone", "campfire")
    d.bed(41, u, 11, "west", "red")
    d.bed(41, u, 12, "west", "red")
    stand(d, 41, u, 10, "spruce_slab", CAND)
    stand(d, 41, u, 13, "spruce_slab", "potted_blue_orchid")
    P(d, u, [(45, 13, chest("north", "left")), (46, 13, chest("north", "right")), (44, 5, slab("spruce_slab", "top"))])
    d.chair(44, u, 6, "south", "spruce", sit=False)
    d.set(44, u + 1, 5, LAMP)
    d.rug(43, 9, 45, 11, u, ("red_carpet", "brown_carpet"))
    hang(d, [(45, 10)], 10)
    d.sign(45, 5, 3, "north", ["DOCTOR"], "spruce")
    # under the eaves: pots by the door, a bench, firewood and water barrels, wall torches
    P(d, y, [(44, 3, "potted_fern"), (46, 3, "potted_blue_orchid"), (51, 10, "barrel[facing=up,open=false]"),
             (51, 12, "water_cauldron[level=3]"), (39, 11, "barrel[facing=up,open=false]")])
    sit(d, [(42, 3), (43, 3)], y, "south", "spruce")
    for z in (6, 7, 8):
        d.set(51, y, z, log("spruce_log", "z"))
        d.set(51, y + 1, z, log("spruce_log", "z"))
    d.wall_torch(45, 4, 15, "south")
    d.wall_torch(39, 4, 12, "west")
    # laundry and boiler house
    lh = shell(d, 42, 18, 50, 24, 1, "gable", "x", mat="cobblestone", up="cobblestone", gable_end="cobblestone")
    entry(d, 46, y, 18, "south")
    chimney(d, 50, 21, y, 16)
    P(d, y, [(43, 23, "water_cauldron[level=3]"), (45, 23, "water_cauldron[level=3]"), (47, 23, "water_cauldron[level=3]"),
             (49, 20, "blast_furnace[facing=west,lit=true]"), (44, 19, "grindstone[face=floor,facing=south]"),
             (43, 20, "barrel[facing=up,open=false]"), (43, 21, "barrel[facing=up,open=false]"),
             (46, 21, slab("birch_slab", "top")), (47, 21, slab("birch_slab", "top"))])
    d.set(46, y + 1, 21, "white_carpet")
    hang(d, [(46, 21)], 5)


def cs_grounds(d):
    y = Y0
    # glasshouse with herb beds
    for x in range(42, 53):
        for z in range(38, 47):
            if x in (42, 52) or z in (38, 46):
                for yy in range(y, 5):
                    d.set(x, yy, z, log("spruce_log") if (x in (42, 47, 52) and z in (38, 46)) or
                          (z in (38, 46) and x in (42, 52)) or (x in (42, 52) and z == 42) else "glass")
            else:
                d.set(x, 1, z, "spruce_planks")
            d.set(x, 5, z, "glass")
    d.set(47, y, 38, AIR)
    d.set(47, y + 1, 38, AIR)
    d.door(47, y, 38, "south", "spruce")
    for z in (40, 41):
        for x in range(43, 52):
            if x != 47:
                d.set(x, 1, z, "podzol")
                d.set(x, y, z, "fern" if x < 47 else "lily_of_the_valley")
    for z in (43, 44):
        for x in range(43, 52):
            if x != 47:
                d.set(x, 1, z, "grass_block[snowy=false]")
                d.set(x, y, z, "sweet_berry_bush[age=2]" if x < 47 else "blue_orchid")
    d.set(51, y, 45, "water_cauldron[level=3]")
    d.set(43, y, 45, "potted_fern")
    # woodshed
    shell(d, 28, 40, 38, 46, 1, "gable", "x", mat="stripped_spruce_log", win="")
    entry(d, 33, y, 40, "south", double=True)
    for x in range(29, 38):
        for yy in (y, y + 1):
            d.set(x, yy, 45, log("spruce_log", "z"))
    P(d, y, [(31, 42, "stripped_spruce_log[axis=y]"), (36, 42, "stonecutter[facing=north]"), (30, 43, "grindstone[face=floor,facing=north]"),
             (37, 43, chest("west"))])
    hang(d, [(32, 43)], 5)
    d.sign(33, 5, 39, "north", ["WOODSHED"], "spruce")
    for x in (4, 16, 25):
        plant_tree(d, x, 48)
    plants(d, [(8, 47, "fern"), (9, 48, "blue_orchid"), (12, 47, "allium"), (20, 48, "lily_of_the_valley"),
               (21, 47, "fern"), (34, 48, "blue_orchid")])


def cs_sun_garden(d):
    """L5 south lawn: the kitchen garden for the infirmary cook and an open sun shelter where convalescent
    patients lie out on cots, plus two spruces on the east lawn."""
    y = Y0
    # kitchen garden: rail fence with a gate, three crop rows between dirt paths, scarecrow, compost, water butt
    for x in range(6, 19):
        for z in (39, 45):
            if (x, z) != (12, 39):
                d.set(x, y, z, "spruce_fence")
    for z in range(40, 45):
        d.set(6, y, z, "spruce_fence")
        d.set(18, y, z, "spruce_fence")
    d.set(12, y, 39, "spruce_fence_gate[facing=north,in_wall=false,open=false,powered=false]")
    for z, crop in ((40, "carrots[age=7]"), (42, "potatoes[age=7]"), (44, "beetroots[age=3]")):
        for x in range(7, 18):
            d.set(x, 1, z, "farmland[moisture=7]")
            d.set(x, y, z, crop)
    for z in (41, 43):
        d.fill(7, 1, z, 17, 1, z, "coarse_dirt")
    P(d, y, [(7, 41, "composter[level=4]"), (17, 41, "water_cauldron[level=3]"), (17, 43, "spruce_fence")])
    d.set(17, y + 1, 43, "hay_block[axis=y]")                    # scarecrow
    d.set(17, y + 2, 43, "carved_pumpkin[facing=north]")
    # sun shelter: four log posts, hipped roof, a rail with a gap on the north, two pairs of cots
    d.fill(20, 1, 39, 26, 1, 45, "spruce_planks")
    for x, z in ((20, 39), (26, 39), (20, 45), (26, 45)):
        for yy in range(y, 5):
            d.set(x, yy, z, log("spruce_log"))
    d.hip(20, 39, 26, 45, 5, "dark_oak_stairs", "dark_oak_slab", overhang=1)
    for x in range(21, 26):
        if x != 23:
            d.set(x, y, 39, "spruce_fence")
        d.set(x, y, 45, "spruce_fence")
    for z in range(40, 45):
        d.set(20, y, z, "spruce_fence")
        d.set(26, y, z, "spruce_fence")
    couch(d, [(22, 41), (22, 42), (24, 41), (24, 42)], y, "spruce_slab", "white_carpet")
    stand(d, 23, y, 43, "spruce_slab", LAMP)
    P(d, y, [(21, 44, "potted_fern"), (25, 44, "potted_blue_orchid")])
    sit(d, [(25, 40)], y, "east", "spruce")
    hang(d, [(23, 42)], 4)
    for x, z in ((46, 30), (51, 34)):
        plant_tree(d, x, z)


def hosp_cascadia(rel, L):
    d = new("Cascadia", rel, (55, 30, 53), paving="coarse_dirt")
    cnf = 2 if L >= 3 else 1
    c = shell(d, 6, 6, 16, 16, cnf, "gable", "z")
    entry(d, 11, Y0, 6, "south")
    chimney(d, 6, 13, Y0, c["ridge"] + 1)
    # front porch with header beam and name board
    d.fill(5, 1, 1, 17, 1, 5, "spruce_planks")
    for x in (5, 9, 13, 17):
        for y in range(Y0, 5):
            d.set(x, y, 1, log("spruce_log"))
    for x in range(6, 17):
        if x not in (9, 13):
            d.set(x, 4, 1, log("spruce_log", "x"))
    for x in range(4, 19):
        d.set(x, 5, 0, st("dark_prismarine_stairs", "south"))
        for z in range(1, 6):
            d.set(x, 5, z, slab("spruce_slab"))
    d.sign(11, 4, 0, "north", ["INFIRMARY", "+"], "spruce")
    sit(d, [(7, 5), (8, 5), (14, 5), (15, 5)], Y0, "south", "spruce", True)
    d.set(6, Y0, 5, "potted_fern")
    d.keg(16, Y0, 5, "up")
    hang(d, [(8, 3), (14, 3)], 4)
    cs_core_ground(d, L)
    if cnf > 1:
        cs_core_upper(d, L)
    if L >= 2:
        cs_ward(d, L)
    if L >= 4:
        cs_south(d, L)
    if L >= 5:
        cs_doctor(d)
        cs_grounds(d)
        cs_sun_garden(d)
    return d


@design("hospital")
def hospital_v2(pack, rel, L):
    return common_materials({"Hearthwood": hosp_hearthwood, "Cascadia": hosp_cascadia, "Neoterra": hosp_neoterra}[pack](rel, L))
