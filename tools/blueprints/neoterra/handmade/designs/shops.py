"""
Shops & workshops: cook (restaurant), cookery (kitchen), baker, florist, dyer, glassblower, concretemixer.

See the per-type section headers for what each design is in each pack.
"""
from hm import Design, design, AIR, D4, OPP, CW


# ============================================================================================ small helpers
def st(m, facing, half="bottom", shape="straight"):
    return f"{m}_stairs[facing={facing},half={half},shape={shape},waterlogged=false]"


def sl(m, t="bottom"):
    return f"{m}_slab[type={t},waterlogged=false]"


def lg(m, axis="y"):
    return f"{m}[axis={axis}]"


def td(m, facing, half="bottom", open_=False):
    return f"{m}_trapdoor[facing={facing},half={half},open={'true' if open_ else 'false'},powered=false,waterlogged=false]"


def lant(hang=True, soul=False):
    return f"{'soul_' if soul else ''}lantern[hanging={'true' if hang else 'false'},waterlogged=false]"


CAKE = "cake[bites=0]"


def furn(d, x, y, z, facing, kind="furnace", lit=False):
    d.item(x, y, z, f"{kind}[facing={facing},lit={'true' if lit else 'false'}]")


def cauldron(d, x, y, z):
    d.item(x, y, z, "water_cauldron[level=3]")


def roof(d, x1, z1, x2, z2, y, axis, stairs, ridge, end=None, oh=1, ends=(1, 1), keep=False, under=None):
    """Gable over wall rect x1..x2/z1..z2 whose wall tops are at y-1. ends = overhang beyond the gable ends (lo, hi).
    keep=True only writes into air (for wings butting against a bigger roof). Returns ridge y."""
    if axis == "x":
        lo, hi, a1, a2 = z1, z2, x1, x2
    else:
        lo, hi, a1, a2 = x1, x2, z1, z2
    L, H = lo - oh, hi + oh
    n = H - L + 1
    for i in range(n):
        w = L + i
        k = min(i, n - 1 - i)
        yy = y + k - oh
        mid = n % 2 == 1 and i == n // 2
        face = ("south" if i < n / 2 else "north") if axis == "x" else ("east" if i < n / 2 else "west")
        for a in range(a1 - ends[0], a2 + ends[1] + 1):
            x, z = (a, w) if axis == "x" else (w, a)
            s = (ridge if "slab" not in ridge else sl(ridge.replace("_slab", ""))) if mid else st(stairs, face)
            if d.bp.inside(x, yy, z) and (not keep or d.air(x, yy, z)):
                d.set(x, yy, z, s)
            if under and lo < w < hi and a1 <= a <= a2 and not mid and yy - 1 >= y:
                if not keep or d.air(x, yy - 1, z):
                    d.set(x, yy - 1, z, under)
        if lo <= w <= hi and end:
            for a in (a1, a2):
                x, z = (a, w) if axis == "x" else (w, a)
                for yy2 in range(y, yy):
                    if d.air(x, yy2, z):
                        d.set(x, yy2, z, end)
    return y + (n - 1) // 2 - oh


def perim(x1, z1, x2, z2):
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if x in (x1, x2) or z in (z1, z2):
                yield x, z


def hood(d, x1, x2, z, y, wallside, m="brick"):
    """Range hood: upside-down stairs over a cooking line (back against the wall side)."""
    for x in range(x1, x2 + 1):
        d.set(x, y, z, st(m, wallside, "top"))


def hood_z(d, x, z1, z2, y, wallside, m="brick"):
    for z in range(z1, z2 + 1):
        d.set(x, y, z, st(m, wallside, "top"))


# -------------------------------------------------------------------------------------------- pack shells
def hw_body(d, x1, z1, x2, z2, y0, y1, wall="calcite", base="stone_bricks", floor="oak_planks", step=3,
            beam="stripped_dark_oak_log", ceiling="dark_oak_planks"):
    """Hearthwood storey: stone plinth course, plaster walls, dark-oak posts every `step`, top beam, ceiling."""
    d.box(x1, y0, z1, x2, y1, z2, wall, floor=floor)
    for x, z in perim(x1, z1, x2, z2):
        d.set(x, y0, z, base)
        on_post = (z in (z1, z2) and (x - x1) % step == 0) or (x in (x1, x2) and (z - z1) % step == 0) \
            or (x in (x1, x2) and z in (z1, z2))
        if on_post:
            for y in range(y0 + 1, y1):
                d.set(x, y, z, lg(beam))
        d.set(x, y1, z, lg(beam, "x" if z in (z1, z2) else "z"))
    for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        d.set(x, y1, z, lg(beam))
    if ceiling:
        d.fill(x1 + 1, y1 + 1, z1 + 1, x2 - 1, y1 + 1, z2 - 1, ceiling)


def cas_body(d, x1, z1, x2, z2, y0, y1, floor="spruce_planks", logm="stripped_spruce_log", post="spruce_log",
             footing=True, ceiling=None):
    """Cascadia storey: horizontal light logs, dark corner posts, river-rock footing course."""
    d.box(x1, y0, z1, x2, y1, z2, lg(logm, "x"), floor=floor)
    for x, z in perim(x1, z1, x2, z2):
        for y in range(y0, y1 + 1):
            d.set(x, y, z, lg(logm, "x" if z in (z1, z2) else "z"))
        if footing:
            d.set(x, y0, z, "mossy_cobblestone" if (x * 7 + z * 3) % 4 == 0 else "cobblestone")
            d.set(x, y0 - 1, z, "cobblestone")
    for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        for y in range(y0 + (1 if footing else 0), y1 + 1):
            d.set(x, y, z, lg(post))
    if ceiling:
        d.fill(x1 + 1, y1 + 1, z1 + 1, x2 - 1, y1 + 1, z2 - 1, ceiling)


def neo_body(d, x1, z1, x2, z2, y0, y1, wall="white_concrete", pillar="light_gray_concrete",
             floor="polished_diorite", roof_="smooth_quartz", parapet="white_concrete", coping="smooth_quartz_slab"):
    """Neoterra box: concrete walls, gray corner pillars, flat roof with parapet + coping. Returns roof y."""
    d.box(x1, y0, z1, x2, y1, z2, wall, floor=floor)
    for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        for y in range(y0, y1 + 1):
            d.set(x, y, z, pillar)
    if roof_:
        d.flat(x1, z1, x2, z2, y1 + 1, roof_, parapet, coping)
    return y1 + 1


def awning(d, x1, x2, z, y, colors=("red_wool", "white_wool"), outward="north", skip=()):
    """Striped awning: two rows of wool stepping down and out from the wall face at row z."""
    dz = D4[outward][1]
    for x in range(x1, x2 + 1):
        c = colors[(x - x1) % len(colors)]
        d.set(x, y, z, c)
        d.set(x, y - 1, z + dz, c)


def awning_z(d, z1, z2, x, y, colors=("red_wool", "white_wool"), outward="east"):
    dx = D4[outward][0]
    for z in range(z1, z2 + 1):
        c = colors[(z - z1) % len(colors)]
        d.set(x, y, z, c)
        d.set(x + dx, y - 1, z, c)


# ============================================================================================ BAKER
# Hearthwood "Ye Olde Bakehouse": Cotswold shop – plaster & timber on a stone plinth, steep tiled gable, huge
#   brick oven wall with a tall chimney, striped awning over the shop window, cakes on the counter, flour sacks.
#   L2 cross-gabled tea room wing, L3 rear flour store, L4 kitchen garden, L5 hanging sign + flower boxes.
# Cascadia "Trailhead Bakery": gable-to-street log cabin with a deep porch, a stone beehive oven built into the
#   west wall, flour sacks and hay; L2 café tables inside, L3 side deck, L4 lean-to store, L5 picnic tables.
# Neoterra "LUMEN BAKERY": white box with a full glass shopfront, cyan canopy, glass display counter, stacked
#   deck ovens in polished andesite; L3 adds an upper café floor (glass) and roof terrace by L5.
def baker_hw(rel, L):
    d = Design("Hearthwood", rel, (55, 42, 45))
    x1, z1, x2, z2, y0, y1 = 3, 5, 15, 11, 2, 5
    oak = "dark_oak"
    hw_body(d, x1, z1, x2, z2, y0, y1)
    # shop front: door, display windows under a striped awning
    d.door(7, y0, z1, "south", oak)
    for x in (4, 5, 9, 10, 12, 13):
        d.window(x, 3, z1, x, 4, z1)
    for z in (7, 9):
        d.window(x1, 3, z, x1, 4, z)
    for x in (5, 9, 13):
        d.window(x, 3, z2, x, 4, z2)
    ridge = roof(d, x1, z1, x2, z2, 6, "x", "deepslate_tile", "deepslate_tile_slab", "calcite")
    # oven wall: bricks along the back of the bakehouse, furnaces + smoker set into it, chimney stack
    for x in range(10, 15):
        for y in range(y0, 6):
            d.set(x, y, 10, "bricks")
    for y in range(6, ridge + 3):
        d.set(12, y, 11, "bricks")
        d.set(13, y, 11, "bricks")
        if y < 8:
            d.set(12, y, 10, "bricks")
            d.set(13, y, 10, "bricks")
    oven = [(11, 2), (13, 2), (11, 3), (13, 3), (12, 3)]
    for i, (x, y) in enumerate(oven):
        if i < L:
            furn(d, x, y, 10, "north", lit=i == 0)
    furn(d, 12, 2, 10, "north", "smoker", lit=True)
    for x in range(10, 15):
        d.set(x, 4, 9, st("brick", "south", "top"))
    # baker's corner: cauldron sink, kneading table (crafting), flour sacks and a proving bench
    cauldron(d, 14, 2, 9)
    d.item(10, 2, 9, "crafting_table")
    for z, h in ((6, 2), (7, 1)):
        for y in range(y0, y0 + h):
            d.set(14, y, z, "white_wool")
    d.set(13, 2, 6, "hay_block[axis=x]")
    for x in (11, 12):
        d.set(x, 2, 7, sl("spruce", "top"))
    d.set(11, 3, 7, "white_carpet")
    d.set(12, 3, 7, CAKE)
    # shop: counter with cakes, bread shelves (racks) on the back wall, window display
    for x in range(4, 9):
        d.set(x, 2, 8, sl(oak, "top"))
    d.set(4, 3, 8, CAKE)
    d.set(6, 3, 8, CAKE)
    d.set(8, 3, 8, "candle[candles=3,lit=false,waterlogged=false]")
    d.hut(4, 2, 10)
    for i, x in enumerate((5, 6, 8)):
        if i < min(L, 3):
            d.rack(x, 2, 10, "north")
        else:
            d.keg(x, 2, 10, "north")
        d.set(x, 3, 10, sl("spruce", "top"))
        d.set(x, 4, 10, CAKE if x % 2 else "decorated_pot[cracked=false,facing=north,waterlogged=false]")
    for x in (4, 5):
        d.set(x, 2, 6, sl(oak, "top"))
        d.set(x, 3, 6, CAKE)
    for x in (5, 8, 12):
        d.lamp(x, 5, 7)
    # street: striped awning, sign, bench
    awning(d, 4, 10, 4, 5)
    d.sign(7, 6, 4, "north", ["", "BAKERY"], oak)
    d.set(12, 2, 3, st(oak, "north"))
    d.set(13, 2, 3, st(oak, "north"))
    d.set(11, 2, 3, "potted_red_tulip")
    d.set(14, 2, 3, "potted_red_tulip")
    # ---- L2+: tea room cross-wing to the east, gable to the street
    if L >= 2:
        wx1, wz1, wx2, wz2 = 16, 4, 23, 12
        hw_body(d, wx1, wz1, wx2, wz2, y0, y1)
        for y in (2, 3):
            d.set(15, y, 8, AIR)
            d.set(16, y, 8, AIR)
        for z in range(wz1 + 2, wz2 - 1, 3):
            d.window(wx2, 3, z, wx2, 4, z)
        for x in (18, 19, 20):
            d.window(x, 3, wz1, x, 4, wz1)
            d.window(x, 3, wz2, x, 4, wz2)
        roof(d, wx1, wz1, wx2, wz2, 6, "z", "deepslate_tile", "deepslate_tile_slab", "calcite", keep=True,
             ends=(1, 1))
        d.window(19, 7, wz1, 20, 8, wz1)
        need = 8 if L == 2 else 12
        for tx, tz in [(18, 7), (21, 7)] + ([(19, 10)] if need > 8 else []):   # tea tables
            d.dining(tx, y0, tz, 1, "x", "oak", ("n", "s", "e", "w"))
        if need > 8:                                            # rug under the third table
            d.rug(17, 9, 21, 11, y0, ("red_carpet",), "plain")
        else:                                                   # L2: a dresser of cakes in the empty end
            for x, top in ((18, CAKE), (19, "potted_red_tulip"), (20, CAKE)):
                d.set(x, y0, 11, sl("oak", "top"))
                d.set(x, 3, 11, top)
        d.lamp(19, 5, 8)
        d.door(22, y0, wz1, "south", oak)
    # ---- L3+: rear flour store (shed roof) behind the shop, door through the back wall
    if L >= 3:
        sx1, sx2, sz1, sz2 = 3, 10, 11, 15
        hw_body(d, sx1, sz1 + 1, sx2, sz2, y0, 4, wall="bricks", base="stone_bricks", ceiling="spruce_planks")
        roof(d, sx1, sz1 + 1, sx2, sz2, 5, "x", "deepslate_tile", "deepslate_tile_slab", "bricks", keep=True,
             ends=(1, 0))
        d.door(7, y0, sz1, "north", oak)
        d.set(7, 2, 12, AIR)
        d.set(7, 3, 12, AIR)
        for x in (4, 5, 6, 9):
            d.set(x, 2, 14, "white_wool" if x % 2 else "hay_block[axis=x]")
        d.set(4, 3, 14, "white_wool")
        if L >= 4:
            d.rack(9, 2, 13, "west")
        if L >= 5:
            d.rack(8, 2, 14, "north")
        d.keg(4, 2, 13, "east")
        d.lamp(6, 4, 13)
        d.window(sx1, 3, 13, sx1, 3, 14)
    # ---- L4+: kitchen garden behind the tea room
    if L >= 4:
        gx1, gx2, gz1, gz2 = 12, 23, 13, 21
        for x, z in perim(gx1, gz1, gx2, gz2):
            d.set(x, 2, z, "stone_brick_wall")
        d.set(17, 2, gz2, "dark_oak_fence_gate[facing=south,in_wall=true,open=false,powered=false]")
        for x in range(gx1 + 1, gx2):
            for z in range(gz1 + 1, gz2):
                d.set(x, 1, z, "grass_block[snowy=false]")
        for x in range(gx1 + 2, gx2 - 1, 3):
            for z in range(gz1 + 3, gz2 - 1):
                d.set(x, 1, z, "farmland[moisture=7]")
                d.set(x, 2, z, "wheat[age=7]")
        d.door(18, y0, 12, "north", oak)
        for z in range(gz1 + 1, gz2):
            d.set(18, 1, z, "gravel")
        d.set(gx2 - 1, 2, gz2 - 1, "flowering_azalea")
        d.set(gx1 + 1, 2, gz2 - 1, "composter[level=4]")
    if L >= 5:
        d.sign(2, 4, 8, "west", ["Ye Olde", "Bakehouse"], oak)
        for x in (4, 5, 9, 10, 12, 13):
            d.set(x, 2, 4, "potted_red_tulip" if x % 2 else "potted_oxeye_daisy")
        d.set(2, 2, 6, "rose_bush[half=lower]")
        d.set(2, 3, 6, "rose_bush[half=upper]")
    return d


def porch(d, x1, x2, z1, z2, y0, ytop, posts, wood="spruce", rail=True, gap=(), roof_="spruce", post="spruce_log"):
    """Covered porch in front of a north wall (z2 = row in front of the wall). Shed roof at ytop sloping north."""
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            d.set(x, y0 - 1, z, f"{wood}_planks")
    for x in posts:
        for y in range(y0, ytop):
            d.set(x, y, z1, lg(post))
    for x in range(x1 - 1, x2 + 2):
        d.set(x, ytop, z1 - 1, st(roof_, "south"))
        for z in range(z1, z2 + 1):
            d.set(x, ytop, z, sl(roof_, "bottom") if z < z2 else sl(roof_, "bottom"))
    if rail:
        for x in range(x1, x2 + 1):
            if x not in posts and x not in gap:
                d.set(x, y0, z1, f"{wood}_fence")


def baker_cas(rel, L):
    d = Design("Cascadia", rel, (54, 42, 48), paving="coarse_dirt")
    x1, z1, x2, z2, y0, y1 = 6, 7, 16, 19, 2, 6
    cas_body(d, x1, z1, x2, z2, y0, y1)
    ridge = roof(d, x1, z1, x2, z2, 7, "z", "dark_oak", "dark_oak_slab", "spruce_planks", ends=(2, 1),
                 under=None)
    for z in range(z1, z2 + 1):                         # board ceiling on tie beams
        for x in range(x1 + 1, x2):
            if d.air(x, 7, z):
                d.set(x, 7, z, "spruce_planks")
    # gable-end detail: dark board-and-batten + loft window
    mid = 11
    for y in range(7, ridge):
        for x in range(x1 + 1, x2):
            if d.get(x, y, z1) == "minecraft:spruce_planks" and (x - mid) % 2 == 0:
                d.set(x, y, z1, lg("stripped_dark_oak_log"))
    d.window(mid, 8, z1, mid, 9, z1)
    # porch across the front
    porch(d, x1, x2, 3, 6, y0, 6, (x1, 9, 13, x2), gap=(10, 11, 12))
    d.door(mid, y0, z1, "south", "spruce")
    for x in (8, 14):
        d.window(x, 3, z1, x, 4, z1)
    d.sign(mid, 5, z1 - 1, "north", ["TRAILHEAD", "BAKERY"], "spruce")
    d.set(x1 + 1, y0, 5, st("spruce", "north"))
    d.set(x1 + 2, y0, 5, st("spruce", "north"))
    d.set(x2 - 1, y0, 5, "hay_block[axis=y]")
    d.set(x2 - 1, y0 + 1, 5, "white_wool")
    for x in (10, 12):
        d.lamp(x, 5, 4)
    for z in (9, 12, 16):
        d.window(x2, 3, z, x2, 4, z)
    d.window(x1, 3, 10, x1, 4, 11)
    # stone bread oven built out through the west wall, its chimney beside the roof
    for z in range(13, 18):
        for y in range(y0, 5):
            for x in range(3, 8):
                if x == 7 and y < 4:
                    continue
                d.set(x, y, z, "cobblestone" if (x + y + z) % 3 else "mossy_cobblestone")
    for z in range(13, 18):
        for x in range(3, 7):
            d.set(x, 5, z, sl("cobblestone") if x in (3, 6) or z in (13, 17) else "cobblestone")
        d.set(2, 4, z, st("cobblestone", "east"))
    for y in range(5, ridge + 2):
        d.set(4, y, 15, "cobblestone")
        d.set(4, y, 14, "stone_bricks" if y % 2 else "cobblestone")
    oven = [(13, 2), (17, 2), (13, 3), (17, 3), (15, 3)]
    for z in range(13, 18):
        d.set(7, 2, z, "cobblestone")
        d.set(7, 3, z, "cobblestone")
    for i, (z, y) in enumerate(oven):
        if i < L:
            furn(d, 7, y, z, "east", lit=i == 0)
    furn(d, 7, 2, 15, "east", "smoker", lit=True)
    for z in range(13, 18):
        d.set(8, 4, z, st("cobblestone", "west", "top"))
    # bakery back: sink, kneading table, racks of bread along the back wall, flour + hay
    cauldron(d, 15, 2, 14)
    d.item(15, 2, 16, "crafting_table")
    d.set(15, 2, 15, sl("spruce", "top"))
    d.set(15, 3, 15, CAKE)
    for i, x in enumerate(range(8, 13)):
        if i < L:
            d.rack(x, 2, 18, "north")
        else:
            d.set(x, 2, 18, "white_wool" if i % 2 else "hay_block[axis=x]")
        d.set(x, 3, 18, sl("spruce", "top"))
    for x in (8, 10, 12):
        d.set(x, 4, 18, "decorated_pot[cracked=false,facing=north,waterlogged=false]")
    d.set(14, 2, 18, "white_wool")
    d.set(14, 3, 18, "white_wool")
    d.set(15, 2, 18, "hay_block[axis=y]")
    # sales counter across the room (gap at the east end)
    for x in range(7, 14):
        d.set(x, 2, 12, "stripped_spruce_wood[axis=y]")
    for x in (8, 10, 12):
        d.set(x, 3, 12, CAKE)
    d.set(13, 3, 12, "lantern[hanging=false,waterlogged=false]")
    d.hut(x1 + 1, y0, z1 + 1)
    for z in (9, 15):
        d.lamp(mid, 6, z)
    # front room: L2+ café tables
    if L >= 2:
        d.dining(8, y0, 9, 1, "x", "spruce", ("e", "w", "s"))
        d.dining(14, y0, 9, 1, "x", "spruce", ("e", "w", "s"))
        d.set(7, y0, 10, AIR)
    if L == 2:
        d.chair(12, y0, 10, "east", "spruce")
        d.chair(10, y0, 10, "west", "spruce")
    # L3+: side deck with picnic tables (east), door through the east wall
    if L >= 3:
        for z in range(9, 19):
            for x in range(17, 23):
                d.set(x, 1, z, "spruce_planks")
        for x, z in perim(17, 9, 22, 18):
            if x == 17:
                continue
            d.set(x, 2, z, "spruce_fence")
        d.set(22, 2, 13, AIR)
        d.set(22, 2, 14, AIR)
        for x, z in ((22, 9), (22, 18)):
            d.set(x, 2, z, lg("spruce_log"))
            d.set(x, 3, z, "lantern[hanging=false,waterlogged=false]")
        d.door(x2, y0, 11, "west", "spruce")
        d.window(x2, 3, 9, x2, 4, 9)
        d.dining(19, y0, 15, 2, "z", "dark_oak", ("e", "w"))
        d.dining(19, y0, 11, 1, "z", "dark_oak", ("e", "w"))
    # L4+: woodshed lean-to on the back with firewood for the oven
    if L >= 4:
        for x in range(x1, x2 + 1):
            for z in range(z2 + 1, z2 + 5):
                if x in (x1, x2) or z == z2 + 4:
                    for y in range(y0, 5):
                        d.set(x, y, z, lg("spruce_log") if (x in (x1, x2) and z == z2 + 4) or y == 4 else AIR)
            for i, z in enumerate(range(z2 + 1, z2 + 6)):
                d.set(x, 5 - (i // 2), z, st("dark_oak", "north") if i % 2 == 0 else sl("dark_oak"))
        for x in range(x1 + 1, x2):
            if x in (11,):
                continue
            for y in range(y0, 4):
                d.set(x, y, z2 + 3, lg("oak_log", "z") if (x + y) % 3 else lg("birch_log", "z"))
        d.set(11, 2, z2 + 3, AIR)
        d.set(12, 2, z2 + 1, AIR)
    if L >= 5:
        d.dining(20, y0, 23, 2, "x", "spruce", ("n", "s"), sit=False)
        for (x, z) in ((19, 5), (20, 5)):
            d.set(x, 1, z, "podzol")
            d.set(x, 2, z, "fern")
        d.set(3, 1, 9, "podzol")
        d.set(3, 2, 9, "large_fern[half=lower]")
        d.set(3, 3, 9, "large_fern[half=upper]")
        d.set(x1 - 1, 2, z1 + 1, "composter[level=3]")
    return d


def glass_front(d, x1, x2, z, y1, y2, glass="glass_pane", mull="light_gray_concrete", every=4):
    for x in range(x1, x2 + 1):
        for y in range(y1, y2 + 1):
            d.set(x, y, z, mull if every and (x - x1) % every == 0 else glass)


def billboard(d, x1, x2, z, y, words, color="cyan", frame="smooth_quartz", panel="white_concrete"):
    """Rooftop sign: two posts, a 2-high panel set back at z, glowing words on its street face (one sign per
    word, centred), end-rod lights on top."""
    for x in (x1, x2):
        for yy in range(y, y + 4):
            d.set(x, yy, z, frame)
    for x in range(x1 + 1, x2):
        d.set(x, y + 2, z, panel)
        d.set(x, y + 3, z, panel)
        d.set(x, y + 4, z, sl("smooth_quartz"))
    d.set(x1, y + 4, z, "end_rod[facing=up]")
    d.set(x2, y + 4, z, "end_rod[facing=up]")
    x0 = (x1 + x2) // 2 - (len(words) - 1) // 2
    for i, w in enumerate(words):
        d.sign(x0 + i, y + 3, z - 1, "north", ["", w], "birch", glow=True, color=color)


def planter(d, x, z, y, plant="flowering_azalea", box="smooth_quartz"):
    d.set(x, y, z, box)
    d.set(x, y + 1, z, plant)


def baker_neo(rel, L):
    d = Design("Neoterra", rel, (54, 42, 44), paving="smooth_stone")
    x1, z1, z2, y0, y1 = 3, 4, 11, 2, 5
    x2 = 13 if L == 1 else 21
    neo_body(d, x1, z1, x2, z2, y0, y1)
    glass_front(d, x1 + 1, x2 - 1, z1, y0, y1, every=0)
    for x in range(x1 + 4, x2, 5):
        for y in range(y0, y1 + 1):
            d.set(x, y, z1, "light_gray_concrete")
    d.double_door(6, y0, z1, "x", "south", "birch")
    d.fill(x1, y1 + 1, z1, x2, y1 + 1, z1, "cyan_terracotta")          # cyan fascia band
    for x in range(x1, x2 + 1):                                       # canopy
        d.set(x, y1 + 1, z1 - 1, sl("smooth_quartz", "top"))
        d.set(x, y1 + 1, z1 - 2, sl("smooth_quartz", "top"))
    for x in range(x1 + 1, x2, 3):
        d.set(x, y1, z1 - 2, "end_rod[facing=down]")
    for x, txt in ((8, ["LUMEN"]), (9, ["BAKERY"]), (10, ["& CAFE"] if L >= 2 else ["EST.2084"])):
        d.sign(x, y1 + 2, z1 - 1, "north", ["", txt[0]], "birch", glow=True, color="cyan")
        d.set(x, y1 + 2, z1, "white_concrete")
    for z in (6, 9):
        d.window(x1, 3, z, x1, 4, z)
    billboard(d, x1 + 2, x1 + 8, z1 + 1, y1 + 2, ["FRESH", "BREAD", "DAILY"], "yellow")
    for x in (x1, x1 + 1, 12, 13):                                   # planters along the pavement
        planter(d, x, z1 - 3, y0)
    for x in range(8, 13):                                           # window display of cakes
        d.set(x, y0, z1 + 1, sl("smooth_quartz", "top"))
        d.set(x, 3, z1 + 1, CAKE if x % 2 == 0 else "candle_cake[lit=false]")
    # display counter: glass-fronted cases with cakes on quartz tops
    for x in range(4, 10):
        d.set(x, 2, 7, "light_blue_stained_glass" if x > 4 else "smooth_quartz")
        d.set(x, 3, 7, CAKE if x % 2 else "smooth_quartz_slab[type=bottom,waterlogged=false]")
    d.set(10, 2, 7, "smooth_quartz")
    d.hut(4, 2, 5)
    d.plant(5, 2, 5, "potted_bamboo")
    # production line on the back wall: racks (shelves of loaves), sink, work table, deck ovens
    for i, x in enumerate((4, 5, 6)):
        if i < L:
            d.rack(x, 2, 10, "north")
        else:
            d.set(x, 2, 10, "white_concrete")
        d.set(x, 3, 10, sl("birch", "top"))
    for i, x in enumerate((4, 6)):
        d.set(x, 4, 10, CAKE)
    cauldron(d, 7, 2, 10)
    d.item(8, 2, 10, "crafting_table")
    d.set(9, 2, 10, sl("smooth_quartz", "top"))
    d.set(9, 3, 10, "white_carpet")
    oven = [(10, 2), (12, 2), (10, 3), (12, 3), (11, 3)]
    for x in (10, 11, 12):
        for y in (2, 3, 4, 5):
            d.set(x, y, 10, "polished_andesite")
    for i, (x, y) in enumerate(oven):
        if i < L:
            furn(d, x, y, 10, "north", lit=i == 0)
    furn(d, 11, 2, 10, "north", "smoker", lit=True)
    for x in (10, 11, 12):
        d.set(x, 4, 9, st("polished_andesite", "south", "top"))
    if L >= 4:
        d.rack(12, 2, 6, "west")
    if L >= 5:
        d.rack(12, 2, 7, "west")
    d.set(12, 2, 8, "white_wool")
    for x in (5, 8, 11):
        d.set(x, y1 + 1, 8, "sea_lantern")
    # L2+: café wing with glass street front, booths
    if L >= 2:
        for y in (2, 3):
            d.set(13, y, 7, AIR)
            d.set(13, y, 8, AIR)
        for x in range(14, 21):
            d.set(x, y1 + 1, 8, "sea_lantern" if x % 3 == 0 else "smooth_quartz")
        need = 8 if L == 2 else 12
        for tx, tz in [(15, 6), (18, 6)] + ([(18, 9)] if need > 8 else []):   # cafe tables
            d.dining(tx, y0, tz, 1, "x", "birch", ("n", "s", "e", "w"), kind="slab")
        d.window(x2, 3, 6, x2, 4, 9)
        d.plant(20, 2, 5, "potted_bamboo")
        d.plant(14, 2, 10, "potted_bamboo")
    # oven flue through the roof
    for y in range(6, 10):
        d.set(11, y, 11, "polished_andesite")
    d.set(11, 10, 11, "iron_bars") 
    d.set(11, 11, 11, sl("smooth_stone"))
    # L3+: solar panels on the shop roof; L4 roof terrace over the café with an outside stair; L5 pergola
    if L >= 3:
        for x in range(x1 + 2, 13, 2):
            for z in (6, 7, 8):
                d.set(x, 7, z, "daylight_detector[inverted=false,power=0]")
    if L >= 4:
        for x in range(14, x2):                                      # planters along the back parapet
            d.set(x, 7, z2 - 1, "moss_block")
            if x % 2:
                d.set(x, 8, z2 - 1, "azalea")
        for i in range(5):                                            # outside stair up the east side
            z, y = 11 - i, 2 + i
            d.set(22, y, z, st("smooth_quartz", "north"))
            for yy in range(2, y):
                d.set(22, yy, z, "light_gray_concrete")
        d.set(22, 6, 6, "smooth_quartz")
        for z in (6, 7):
            d.set(x2, 7, z, AIR)
            d.set(x2, 8, z, AIR)
        d.dining(16, 7, 6, 1, "x", "birch", ("e", "w", "n", "s"), kind="post")
        d.set(16, 9, 6, "white_banner[rotation=0]")
        d.dining(19, 7, 8, 1, "x", "birch", ("n", "s"), kind="post")
    if L >= 5:
        for x, z in ((14, 5), (20, 5), (14, 9), (20, 9)):
            for y in (7, 8, 9):
                d.set(x, y, z, "birch_fence")
        for x in range(14, 21):
            for z in range(5, 10):
                if (x + z) % 2 == 0 or x in (14, 20):
                    d.set(x, 10, z, sl("birch"))
        for x in (x1 + 1, x2 - 1):
            d.set(x, 2, z1 - 3, "flowering_azalea")
    return d


@design("baker")
def baker(pack, rel, L):
    d = {"Hearthwood": baker_hw, "Cascadia": baker_cas, "Neoterra": baker_neo}[pack](rel, L)
    grow(d, L, "baker")
    return d


def line(d, x, y, z, along, facing, seq, counter="smooth_stone", L=5, wood="spruce"):
    """Lay a fitted line of work blocks along x or z. Codes: F furnace, S smoker, C water cauldron (counted),
    c water cauldron (decor), T crafting table, R rack, M loom, K keg, b barrel (work, counted), - counter slab,
    W flour sack (white wool), H hay bale, P decorated pot, s fitted counter block, '.' skip."""
    dx, dz = (1, 0) if along == "x" else (0, 1)
    nf = 0
    for i, c in enumerate(seq):
        cx, cz = x + dx * i, z + dz * i
        if c == "F":
            furn(d, cx, y, cz, facing, lit=nf == 0)
            nf += 1
        elif c == "S":
            furn(d, cx, y, cz, facing, "smoker", lit=True)
        elif c == "C":
            cauldron(d, cx, y, cz)
        elif c == "c":
            d.set(cx, y, cz, "water_cauldron[level=3]")
        elif c == "T":
            d.item(cx, y, cz, "crafting_table")
        elif c == "R":
            d.rack(cx, y, cz, facing)
        elif c == "M":
            d.item(cx, y, cz, f"loom[facing={facing}]")
        elif c == "K":
            d.keg(cx, y, cz, facing)
        elif c == "b":
            d.item(cx, y, cz, "barrel[facing=up,open=false]")
        elif c == "-":
            d.set(cx, y, cz, sl(counter, "top"))
        elif c == "s":
            d.set(cx, y, cz, counter)
        elif c == "W":
            d.set(cx, y, cz, "white_wool")
        elif c == "H":
            d.set(cx, y, cz, "hay_block[axis=y]")
        elif c == "P":
            d.set(cx, y, cz, f"decorated_pot[cracked=false,facing={facing},waterlogged=false]")


def range_seq(n_furn, total, smoker_at=2, extra=""):
    """Cooking line: furnaces with a smoker in it, padded with counters to `total` cells."""
    s = ["F"] * n_furn
    s.insert(min(smoker_at, len(s)), "S")
    s = "".join(s) + extra
    return (s + "-" * total)[:total]


def booth(d, x, z, y, wood, w=2, along="x"):
    """One booth at (x, z): bench (back out) - table - bench, `w` wide."""
    for i in range(w):
        if along == "x":
            d.chair(x + i, y, z, "north", wood)
            d.table(x + i, y, z + 1, wood, "slab")
            d.chair(x + i, y, z + 2, "south", wood)
        else:
            d.chair(x, y, z + i, "west", wood)
            d.table(x + 1, y, z + i, wood, "slab")
            d.chair(x + 2, y, z + i, "east", wood)
    return True


def bar_row(d, x1, x2, z, y, top, stool_side, wood):
    """Counter along x with stools on `stool_side` (north/south). Returns seats."""
    dz = D4[stool_side][1]
    for x in range(x1, x2 + 1):
        d.set(x, y, z, top)
        d.chair(x, y, z + dz, stool_side, wood)
    return x2 - x1 + 1


# ============================================================================================ COOK
# Hearthwood "The Brown Trout": dining house – a long timber-framed hall with its gable to the street, a brick
#   kitchen wing on the side with a range under a hood and a big chimney, serving hatch into the hall,
#   inglenook fireplace. The hall grows backwards each level; L4 entrance porch, L5 herb garden + sign.
# Cascadia "Hungry Logger Diner": long low log cookhouse along the street, diner counter with stools facing
#   an open kitchen line, booths along the windows, covered porch; L3+ porch dining, stone chimney.
# Neoterra "Orbit Bistro": glass-fronted concrete restaurant, open kitchen behind a quartz pass, L3 adds a
#   glazed upper dining floor with a straight stair, L5 a roof terrace.
def cook_hw(rel, L):
    d = Design("Hearthwood", rel, (54, 42, 50))
    y0, y1 = 2, 5
    oak = "dark_oak"
    Z2 = {1: 13, 2: 19}.get(L, 25)
    # kitchen wing first (brick), then the hall over the shared wall
    hw_body(d, 13, 5, 22, 13, y0, y1, wall="bricks", base="stone_bricks", step=3)
    hw_body(d, 3, 5, 13, Z2, y0, y1)
    ridge = roof(d, 3, 5, 13, Z2, 6, "z", "deepslate_tile", "deepslate_tile_slab", "calcite")
    roof(d, 13, 5, 22, 13, 6, "x", "deepslate_tile", "deepslate_tile_slab", "bricks", keep=True, ends=(0, 1))
    for z in range(6, Z2):                                       # hall: lime-washed ceiling beams
        if (z - 5) % 3 == 0:
            for x in range(4, 13):
                d.set(x, 6, z, lg("stripped_dark_oak_log", "x"))
    # front: double door, windows, gable window, sign
    d.double_door(7, y0, 5, "x", "south", oak)
    for x in (4, 5, 10, 11):
        d.window(x, 3, 5, x, 4, 5)
    d.window(7, 7, 5, 8, 8, 5)
    d.sign(9, 4, 4, "north", ["The", "Brown Trout", "~ dining ~"], oak)
    for z in range(7, Z2 - 1, 3):
        d.window(3, 3, z, 3, 4, z + 1)
    for x in (5, 8, 11):
        d.window(x, 3, Z2, x, 4, Z2)
    # kitchen: range on the back wall under a brick hood, chimney, island, sink, pantry rack, back door
    seq = "T" + range_seq(L, 6) + "C"
    line(d, 14, y0, 12, "x", "north", seq, counter="smooth_stone")
    hood(d, 15, 20, 12, 4, "south")
    for y in range(4, ridge + 2):
        d.set(17, y, 13, "bricks")
        d.set(18, y, 13, "bricks")
    for x in range(15, 21):
        if x - 15 < L + 1:
            d.spot(x, y0, 11, "work")
    for x in (16, 17, 18, 19):
        d.set(x, y0, 8, sl("spruce", "top"))
    d.set(16, 3, 8, "candle[candles=2,lit=false,waterlogged=false]")
    d.set(18, 3, 8, "decorated_pot[cracked=false,facing=north,waterlogged=false]")
    d.rack(21, y0, 6, "west")
    d.keg(21, y0, 7, "west")
    d.keg(21, y0 + 1, 7, "west")
    d.set(20, y0, 6, "hay_block[axis=y]")
    d.door(22, y0, 9, "west", oak)
    for x in (15, 19):
        d.window(x, 3, 5, x, 4, 5)
    d.lamp(17, 5, 9)
    d.lamp(20, 5, 9)
    # serving hatch + kitchen door through the shared wall
    d.set(13, y0, 7, sl(oak, "top"))
    d.set(13, 3, 7, AIR)
    d.set(13, y0, 10, AIR)
    d.set(13, 3, 10, AIR)
    # hall: maître d' corner, inglenook, tables
    d.hut(4, y0, 6)
    d.set(12, y0, 6, "potted_red_tulip")
    seats = 0
    if L >= 2:
        d.hearth(4, y0, 16, "east", ridge + 2, "bricks", "campfire")
        for y in range(y0, ridge + 2):
            d.set(3, y, 16, "bricks")
        d.set(3, 3, 15, "calcite")
        d.chair(5, y0, 14, "north", oak, arms=True)
        d.chair(5, y0, 18, "south", oak, arms=True)
        seats += 2
    if L >= 3:
        d.item(4, y0, 7, "jukebox")
    d.set(10, y0, 6, "lectern[facing=north,has_book=true,powered=false]")      # host stand by the door
    if L >= 3:                                                   # bar across the far end, back bar behind
        for x in range(4, 13):
            d.set(x, y0, Z2 - 1, "barrel[facing=north,open=false]" if x % 2 else "brewing_stand[has_bottle_0=true,"
                  "has_bottle_1=false,has_bottle_2=true]")
            d.set(x, 4, Z2 - 1, lant())
        seats += bar_row(d, 6, 11, Z2 - 3, y0, "stripped_dark_oak_wood[axis=y]", "north", oak)
        d.set(7, 3, Z2 - 3, "candle[candles=3,lit=true,waterlogged=false]")          # on the bar top
        d.set(10, 3, Z2 - 3, "decorated_pot[cracked=false,facing=north,waterlogged=false]")
        d.set(12, y0, Z2 - 3, f"{oak}_fence_gate[facing=east,in_wall=false,open=false,powered=false]")
    for z in ([8] if L < 3 else [8, 20]):                        # booths under the west windows
        booth(d, 4, z, y0, oak)
        seats += 4
        d.set(4, y0, z + 3, "potted_azalea_bush")
    for c in ([9] if L == 1 else [9, 13, 17]):                   # 4-tops down the middle
        d.dining(8, y0, c, 2, "x", oak, ("n", "s"))
        seats += 4
    for c in {1: [], 2: [12, 16]}.get(L, [12, 16, 20]):          # tables for two by the east windows
        d.table(12, y0, c, oak, "post")
        d.chair(12, y0, c - 1, "north", oak)
        d.chair(12, y0, c + 1, "south", oak)
        seats += 2
    if L >= 4:                                                   # street terrace tables under the windows
        for tx in (4, 11):
            d.table(tx, y0, 2, oak, "post")
            d.chair(tx - 1, y0, 2, "west", oak)
            d.chair(tx + 1, y0, 2, "east", oak)
            seats += 2
    d.rug(6, 6, 7, 7, y0, ("red_carpet",), "plain")             # door mat inside the entrance
    need = {1: 8, 2: 20, 3: 34}.get(L, 37)
    assert seats >= need, (seats, need)
    for z in range(8, Z2, 4):
        d.lamp(8, 5, z)
    # L4+: gabled entrance porch; L5: herb garden behind the kitchen and a hanging sign
    if L >= 4:
        for x, z in ((6, 2), (9, 2)):
            for y in range(y0, 5):
                d.set(x, y, z, lg("stripped_dark_oak_log"))
        for z in range(2, 5):
            for x in range(6, 10):
                d.set(x, 1, z, "stone_bricks")
        roof(d, 6, 2, 9, 4, 5, "z", "deepslate_tile", "deepslate_tile_slab", "calcite", keep=True, ends=(1, 0),
             oh=1)
        for x in range(7, 9):
            for y in range(5, 7):
                if d.get(x, y, 2) == "minecraft:calcite":
                    d.set(x, y, 2, AIR)
        d.set(5, 2, 3, "potted_red_tulip")
        d.set(10, 2, 3, "potted_red_tulip")
    if L >= 5:
        for x, z in perim(14, 15, 23, 22):
            d.set(x, y0, z, "spruce_fence")
        d.set(18, y0, 15, "spruce_fence_gate[facing=south,in_wall=false,open=false,powered=false]")
        for x in range(15, 23):
            for z in range(16, 22):
                d.set(x, 1, z, "grass_block[snowy=false]" if x in (18,) else "farmland[moisture=7]")
                if x != 18:
                    d.set(x, 2, z, ("carrots[age=7]", "potatoes[age=7]", "beetroots[age=3]")[x % 3])
        d.set(18, 1, 14, "gravel")
        d.set(15, 2, 21, "composter[level=5]")
    return d


def cook_cas(rel, L):
    d = Design("Cascadia", rel, (58, 42, 48), paving="coarse_dirt")
    y0, y1 = 2, 5
    x1, z1, z2 = 3, 7, 15
    x2 = 15 if L == 1 else 25
    cas_body(d, x1, z1, x2, z2, y0, y1, ceiling="spruce_planks")
    ridge = roof(d, x1, z1, x2, z2, 6, "x", "dark_oak", "dark_oak_slab", "spruce_planks", ends=(1, 1))
    for y in range(6, ridge):                                    # board-and-batten gables
        for z in range(z1 + 1, z2):
            for x in (x1, x2):
                if d.get(x, y, z) == "minecraft:spruce_planks" and z % 2 == 0:
                    d.set(x, y, z, lg("stripped_dark_oak_log"))
    # porch along the street
    posts = tuple(range(x1, x2 + 1, 4)) + (x2,)
    porch(d, x1, x2, 3, 6, y0, 6, posts, gap=(8, 9, 10))
    d.door(9, y0, z1, "south", "spruce")
    for x in range(x1 + 2, x2 - 1):
        if (x - x1) % 4 in (1, 2) and abs(x - 9) > 1:
            d.window(x, 3, z1, x, 4, z1)
    d.sign(9, 5, z1 - 1, "north", ["HUNGRY", "LOGGER", "DINER"], "spruce")
    for x in range(x1 + 2, x2 - 1, 4):
        d.window(x, 3, z2, x, 4, z2)
    # stone chimney on the east gable
    for y in range(y0, ridge + 2):
        for z in (10, 11):
            d.set(x2 + 1, y, z, "cobblestone" if (y + z) % 3 else "mossy_cobblestone")
    # open kitchen line on the back wall, counter + stools
    n = x2 - x1 - 2
    seq = "R" + "T" + range_seq(L, 6, 1) + "c" + "-" * 40
    line(d, x1 + 1, y0, z2 - 1, "x", "north", seq[:n + 1], counter="spruce")
    for x in range(x1 + 2, x1 + 9):
        d.set(x, 4, z2 - 1, st("cobblestone", "south", "top"))
    for i in range(L + 1):
        d.spot(x1 + 2 + i, y0, z2 - 2, "work")
    for x in range(x1 + 2, x2):
        d.set(x, y0, z2 - 3, "stripped_spruce_wood[axis=y]")
        if x % 3 == 0:
            d.set(x, 3, z2 - 3, "candle[candles=1,lit=false,waterlogged=false]")
    seats = 0
    need = {1: 8, 2: 20, 3: 34}.get(L, 37)
    for x in range(x1 + 2, x2):
        if seats < need:
            d.chair(x, y0, z2 - 4, "north", "spruce")
            seats += 1
    d.hut(x1 + 1, y0, z1 + 1)
    if L >= 3:
        d.item(x2 - 1, y0, z1 + 1, "jukebox")
    # booths along the street windows
    for bx in range(x1 + 2, x2 - 2, 4):
        if seats >= need:
            break
        if abs(bx + 1 - 9) <= 2:
            continue
        for z in (z1 + 1, z1 + 2):
            d.chair(bx, y0, z, "west", "dark_oak")
            d.table(bx + 1, y0, z, "dark_oak", "slab")
            d.chair(bx + 2, y0, z, "east", "dark_oak")
        seats += 4
    for x in range(x1 + 3, x2, 4):
        d.lamp(x, y1, z1 + 4)
    # porch dining (L3+): tables along the porch
    if seats < need:
        for tx in range(x1 + 1, x2, 3):
            if seats >= need:
                break
            if abs(tx - 9) <= 1:
                continue
            d.table(tx, y0, 5, "spruce", "post")
            d.chair(tx - 1, y0, 5, "west", "spruce")
            d.chair(tx + 1, y0, 5, "east", "spruce")
            seats += 2
    for x in (x1, x2):
        d.set(x, 5, 4, "lantern[hanging=true,waterlogged=false]")
    if L >= 5:
        for x in range(10, 13):
            d.set(x, 2, 18, "spruce_log[axis=x]")
        d.set(13, 2, 18, "spruce_log[axis=y]")
        d.set(13, 3, 18, "lantern[hanging=false,waterlogged=false]")
        for x in range(4, 8):
            for y in (2, 3):
                d.set(x, y, 18, lg("oak_log", "z"))
        d.set(16, 2, 18, "barrel[facing=up,open=false]")
        d.set(17, 2, 18, "composter[level=5]")
    return d


def cook_neo(rel, L):
    d = Design("Neoterra", rel, (50, 42, 44), paving="smooth_stone")
    x1, z1, x2, z2, y0 = 3, 4, 19, 16, 2
    two = L >= 3
    neo_body(d, x1, z1, x2, z2, y0, 5, roof_=None)
    d.fill(x1, 6, z1, x2, 6, z2, "light_gray_concrete")
    if two:
        neo_body(d, x1, z1, x2, z2, 7, 10, floor=None)
        d.fill(x1 + 1, 6, z1 + 1, x2 - 1, 6, z2 - 1, "polished_diorite")
        top = 11
    else:
        d.flat(x1, z1, x2, z2, 6, "light_gray_concrete", "white_concrete", "smooth_quartz_slab")
        top = 6
    if two:
        d.flat(x1, z1, x2, z2, top, "smooth_quartz", "white_concrete", "smooth_quartz_slab")
    # glass street front, cyan band, side windows
    glass_front(d, x1 + 1, x2 - 1, z1, y0, 5, every=4)
    d.fill(x1, 6, z1, x2, 6, z1, "cyan_terracotta")
    d.double_door(10, y0, z1, "x", "south", "birch")
    for z in range(z1 + 2, z2 - 4, 2):
        d.window(x1, 3, z, x1, 4, z + 1)
        d.window(x2, 3, z, x2, 4, z + 1)
    if two:
        glass_front(d, x1 + 1, x2 - 1, z1, 7, 10, "light_gray_stained_glass_pane", every=0)
        for z in range(z1 + 1, z2):
            for y in (8, 9):
                d.set(x1, y, z, "glass_pane")
                d.set(x2, y, z, "glass_pane")
    for x in range(9, 13):                                       # entrance canopy
        for z in (z1 - 1, z1 - 2):
            d.set(x, 5, z, sl("smooth_quartz", "top"))
    for x, t in ((9, "ORBIT"), (12, "BISTRO")):
        d.sign(x, 6, z1 - 1, "north", ["", t], "birch", glow=True, color="cyan")
    # open kitchen behind a quartz pass
    for x in range(x1 + 1, x2 - 1):
        d.set(x, y0, 11, "smooth_quartz")
        d.set(x, 3, 11, "light_blue_stained_glass_pane" if x % 2 else AIR)
    seq = "T" + range_seq(L, 8, 2) + "C" + "-" * 6
    line(d, x1 + 1, y0, z2 - 1, "x", "north", seq[:x2 - x1 - 2], counter="smooth_quartz")
    d.rack(x2 - 1, y0, z2 - 1, "north")
    for x in range(x1 + 2, x1 + 11):
        d.set(x, 5, z2 - 1, st("polished_andesite", "south", "top"))
    for i in range(L + 1):
        d.spot(x1 + 2 + i, y0, z2 - 2, "work")
    for x in (x1 + 3, x1 + 4, x1 + 6, x1 + 7):
        d.set(x, y0, 13, sl("smooth_quartz", "top"))
    for x in range(x1 + 2, x2 - 1, 3):
        d.set(x, 6, 13, "sea_lantern")
    for y in range(top, top + 4):                                # kitchen extract stack
        d.set(x1 + 5, y, z2 - 1, "polished_andesite")
    d.set(x1 + 5, top + 4, z2 - 1, sl("smooth_stone"))
    # dining room
    d.hut(x2 - 1, y0, z1 + 1)
    if L >= 3:
        d.item(x2 - 1, y0, 10, "jukebox")
    need = {1: 8, 2: 20, 3: 34}.get(L, 37)
    if two:                                                      # stair to the upper floor, west wall
        for i in range(5):
            d.set(x1 + 1, y0 + i, 6 + i, st("smooth_quartz", "south"))
            for yy in range(y0, y0 + i):
                d.set(x1 + 1, yy, 6 + i, "white_concrete")
        for z in range(6, 10):
            d.set(x1 + 1, 6, z, AIR)
            d.set(x1 + 2, 7, z, "glass_pane")
    d.set(12, y0, z1 + 1, "lectern[facing=north,has_book=true,powered=false]")   # host stand
    seats = 0
    for bx in ((5, 16) if L == 1 else (5, 8, 13, 16)):           # booths against the glass front
        booth(d, bx, z1 + 1, y0, "birch")
        seats += 4
    for x in (7, 15):                                            # azalea planters between the booths
        planter(d, x, z1 + 1, y0)
    xs = range(8, 13) if L == 1 else range(x1 + 2, x2 - 1)      # chef's counter: stools at the pass
    for x in xs:
        d.chair(x, y0, 10, "north", "mangrove")
        seats += 1
    if L >= 2:                                                   # table for two by the east window
        d.table(x2 - 1, y0, 7, "birch", "slab", "smooth_quartz_slab")
        d.chair(x2 - 1, y0, 6, "north", "birch")
        d.chair(x2 - 1, y0, 8, "south", "birch")
        seats += 2
    for x in range(x1 + 2, x2 - 1):                             # dark stone runner down the dining aisle
        d.set(x, 1, 8, "polished_andesite")
        d.set(x, 1, 9, "polished_andesite")
    for x in range(x1 + 2, x2 - 1, 3):
        d.set(x, 6, 8, "sea_lantern")
    if two:                                                      # upper dining room
        for bx in (7, 10, 13, 16):
            booth(d, bx, z1 + 1, 7, "mangrove")
            seats += 4
        for tx in (7, 11, 15):
            d.dining(tx, 7, 12, 2, "x", "mangrove", ("n", "s"), kind="slab")
            seats += 4
        for x in (9, 13, 17):
            d.plant(x, 7, 12, "potted_bamboo")
        for x in range(x1 + 3, x2 - 1):                         # cyan runner inlaid in the upper floor
            d.set(x, 6, 9, "cyan_terracotta")
            d.set(x, 6, 10, "cyan_terracotta")
        for x in range(x1 + 3, x2 - 1):                          # upper bar on the back wall
            if d.air(x, 7, z2 - 1):
                d.set(x, 7, z2 - 1, "smooth_quartz")
        for x in range(x1 + 2, x2 - 1, 3):
            d.set(x, 11, 10, "sea_lantern")
    assert seats >= need, (seats, need)
    if L >= 4:                                                   # cantilevered balcony over the entrance
        for x in range(x1 + 2, x2 - 1):
            d.set(x, 6, z1 - 1, "smooth_quartz")
    if L >= 5:
        for x in range(x1 + 1, x2, 3):
            d.set(x, top + 1, z2 - 1, "azalea")
        for x in range(x1 + 2, x2 - 1, 4):
            d.set(x, top + 1, z1 + 2, "daylight_detector[inverted=false,power=0]")
        for x in (x1 + 1, x2 - 1):
            d.set(x, y0, z1 - 2, "flowering_azalea")
    return d


@design("cook")
def cook(pack, rel, L):
    d = {"Hearthwood": cook_hw, "Cascadia": cook_cas, "Neoterra": cook_neo}[pack](rel, L)
    grow(d, L, "cook")
    return d


# ============================================================================================ COOKERY
# Hearthwood "Great Kitchen": a square stone abbey-style kitchen under a steep hip roof with a timber louvre
#   lantern on top, two big fireplaces with chimneys, range along the back wall, central work table. L2 larder
#   lean-to with hams and casks, L3 scullery with a well, L4 herb garden, L5 bread oven in the yard.
# Cascadia "Camp Cookhouse": long log cookhouse with a cobblestone cookstove chimney, an open-sided smokehouse
#   shed beside it, firewood stacks; L3 back porch, L4 water tower, L5 picnic table.
# Neoterra "Central Kitchen": industrial-modern prep kitchen: gray concrete shed with a cyan band, stainless
#   (andesite/iron) cooking line, walk-in cold room of packed ice with the racks, loading bay with a roller
#   door, extract ducts and condensers on the roof growing with each level.
def cookery_hw(rel, L):
    d = Design("Hearthwood", rel, (54, 42, 44))
    x1, z1, x2, z2, y0, y1 = 5, 5, 15, 15, 2, 6
    d.box(x1, y0, z1, x2, y1, z2, "stone_bricks", floor="stone_bricks")
    for x, z in perim(x1, z1, x2, z2):
        if (x * 3 + z * 5) % 7 == 0:
            d.set(x, 3, z, "mossy_stone_bricks")
        d.set(x, y0, z, "stone_bricks" if (x + z) % 3 else "mossy_stone_bricks")
        d.set(x, y1, z, "stone_bricks")
    for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):     # corner buttresses
        dx = -1 if x == x1 else 1
        dz = -1 if z == z1 else 1
        d.set(x + dx, y0, z, st("stone_brick", "east" if dx < 0 else "west"))
        d.set(x, y0, z + dz, st("stone_brick", "south" if dz < 0 else "north"))
    for x in range(x1 + 1, x2):
        for z in range(z1 + 1, z2):
            d.set(x, 1, z, "stone_bricks" if (x + z) % 2 else "polished_andesite")
    top = d.hip(x1, z1, x2, z2, y1 + 1, "deepslate_tile_stairs", "deepslate_tile_slab", 1)
    # louvre lantern on the ridge
    cx, cz = 10, 10
    for x in (cx - 1, cx + 1):
        for z in (cz - 1, cz + 1):
            d.set(x, top + 1, z, "dark_oak_fence")
    for x in range(cx - 1, cx + 2):
        for z in range(cz - 1, cz + 2):
            d.set(x, top + 2, z, sl("dark_oak"))
    d.set(cx, top + 3, cz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    # door, tall lancet windows
    d.double_door(9, y0, z1, "x", "south", "dark_oak")
    d.set(9, 4, z1, "stone_brick_stairs[facing=east,half=top,shape=straight,waterlogged=false]")
    d.set(10, 4, z1, "stone_brick_stairs[facing=west,half=top,shape=straight,waterlogged=false]")
    for x in (7, 13):
        d.window(x, 3, z1, x, 5, z1)
        d.window(x, 3, z2, x, 5, z2)
    for z in (7, 13):
        d.window(x2, 3, z, x2, 5, z)
    # two fireplaces with chimneys (west wall)
    for fz in (8, 12):
        d.hearth(x1 + 1, y0, fz, "east", y1 + 1, "bricks", "campfire")
        for y in range(y0, top + 3):
            d.set(x1, y, fz, "bricks")
        d.set(x1 + 1, 4, fz, "bricks")
        d.set(x1 + 1, 5, fz, "bricks")
        d.set(x1 + 1, 6, fz, "bricks")
        d.set(x1 + 1, 4, fz - 1, "chain[axis=y,waterlogged=false]")
    d.set(x1 + 1, 3, 10, lant(False))
    # range along the back wall
    seq = range_seq(min(L, 4), 6, 2) + "C"
    line(d, 8, y0, z2 - 1, "x", "north", seq, counter="smooth_stone")
    hood(d, 8, 13, z2 - 1, 4, "south", "stone_brick")
    for y in range(4, y1 + 1):
        d.set(10, y, z2 - 1, "stone_bricks")
    # central work table with produce
    for x in range(9, 12):
        for z in (9, 10):
            d.set(x, y0, z, sl("dark_oak", "top"))
    d.set(9, 3, 9, CAKE)
    d.set(11, 3, 10, "decorated_pot[cracked=false,facing=north,waterlogged=false]")
    d.set(10, 3, 9, "pumpkin")
    d.set(10, 3, 10, "melon")
    # racks (shelving) along the east wall
    for i, z in enumerate((7, 8, 9, 11, 12)):
        if i < L:
            d.rack(x2 - 1, y0, z, "west")
        d.set(x2 - 1, 4, z, sl("dark_oak", "top"))
        d.set(x2 - 1, 5, z, "decorated_pot[cracked=false,facing=west,waterlogged=false]" if z % 2 else "carved_pumpkin[facing=west]")
    d.hut(x1 + 1, y0, z1 + 1)
    d.set(x2 - 1, y0, z1 + 1, "barrel[facing=up,open=false]")
    d.set(x2 - 2, y0, z1 + 1, "white_wool")
    for x, z in ((8, 8), (12, 8), (8, 12), (12, 12)):
        d.set(x, y1, z, "chain[axis=y,waterlogged=false]")
        d.set(x, y1 - 1, z, lant())
    for x in range(x1 + 1, x2):
        d.set(x, y1, 10, lg("stripped_dark_oak_log", "x"))
    # L2+: larder lean-to on the east with hanging hams (hay) and casks
    if L >= 2:
        lx1, lx2 = x2, x2 + 5
        d.box(lx1, y0, 7, lx2, 4, 13, "stone_bricks", floor="stone_bricks")
        roof(d, lx1, 7, lx2, 13, 5, "x", "deepslate_tile", "deepslate_tile_slab", "stone_bricks", keep=True,
             ends=(0, 1))
        d.set(x2, y0, 10, AIR)
        d.set(x2, 3, 10, AIR)
        d.set(x2 - 1, y0, 10, AIR)
        for z in (8, 9, 11, 12):
            d.keg(lx2 - 1, y0, z, "west")
            d.keg(lx2 - 1, 3, z, "west")
        d.set(lx1 + 2, 4, 11, lant())
        d.set(lx1 + 1, y0, 12, "white_wool")
        d.set(lx1 + 1, y0, 8, "pumpkin")
        d.window(lx2, 3, 10, lx2, 3, 10)
    # L3+: scullery / well-house on the west (open timber shed with a well)
    if L >= 3:
        for x, z in ((1, 6), (4, 6), (1, 14), (4, 14)):
            for y in range(y0, 5):
                d.set(x, y, z, lg("stripped_dark_oak_log"))
        roof(d, 1, 6, 4, 14, 5, "z", "deepslate_tile", "deepslate_tile_slab", None, keep=True, ends=(1, 1), oh=1)
        for x in range(1, 5):
            for z in range(6, 15):
                d.set(x, 1, z, "stone_bricks")
        for x in (2, 3):
            for z in (9, 10):
                d.set(x, 1, z, "water")
        for x, z in perim(1, 8, 4, 11):
            d.set(x, 2, z, "stone_brick_wall")
        for x in (2, 3):
            for z in (9, 10):
                d.set(x, 2, z, AIR)
        d.set(2, y0, 13, "water_cauldron[level=3]")
        d.set(3, y0, 13, "water_cauldron[level=3]")
    # L4+: herb garden in front; L5: bread oven in the yard and a sign
    if L >= 4:
        for x, z in perim(4, 1, 16, 3):
            if z == 1:
                d.set(x, y0, z, "spruce_fence")
        for x in range(4, 17):
            if x in (9, 10):
                d.set(x, 1, 2, "gravel")
                d.set(x, 1, 3, "gravel")
                d.set(x, 1, 4, "gravel")
                continue
            for z in (2, 3):
                d.set(x, 1, z, "farmland[moisture=7]" if z == 2 else "grass_block[snowy=false]")
            d.set(x, y0, 2, ("beetroots[age=3]", "carrots[age=7]", "potatoes[age=7]")[x % 3])
            d.set(x, y0, 3, "sweet_berry_bush[age=3]" if x % 4 == 0 else "fern")
        d.set(9, y0, 1, "spruce_fence_gate[facing=north,in_wall=false,open=false,powered=false]")
        d.set(10, y0, 1, "spruce_fence_gate[facing=north,in_wall=false,open=false,powered=false]")
    if L >= 5:
        for x in range(17, 21):
            for z in range(17, 21):
                for y in (2, 3):
                    d.set(x, y, z, "bricks")
                d.set(x, 4, z, sl("brick"))
        d.set(18, 2, 17, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        for y in range(4, 8):
            d.set(19, y, 19, "bricks")
        d.sign(8, 4, z1 - 1, "north", ["The", "Great Kitchen"], "dark_oak")
    return d


def cookery_cas(rel, L):
    d = Design("Cascadia", rel, (54, 42, 46), paving="coarse_dirt")
    x1, z1, x2, z2, y0, y1 = 4, 5, 12, 17, 2, 5
    cas_body(d, x1, z1, x2, z2, y0, y1, ceiling=None)
    ridge = roof(d, x1, z1, x2, z2, 6, "z", "spruce", "spruce_slab", "spruce_planks", ends=(1, 1),
                 under=None)
    for x in range(x1 + 1, x2):                                  # tie beams
        for z in range(z1 + 2, z2, 3):
            d.set(x, 6, z, lg("stripped_spruce_log", "x"))
    for y in range(6, ridge):
        for x in range(x1 + 1, x2):
            if d.get(x, y, z1) == "minecraft:spruce_planks" and x % 2 == 0:
                d.set(x, y, z1, lg("dark_oak_log"))
    d.door(8, y0, z1, "south", "spruce")
    d.sign(8, 5, z1 - 1, "north", ["CAMP", "COOKHOUSE"], "spruce")
    for x in (6, 10):
        d.window(x, 3, z1, x, 4, z1)
    for z in (8, 11):
        d.window(x1, 3, z, x1, 4, z)
    # stone cookstove + chimney on the back wall
    for x in range(5, 12):
        for y in range(y0, 5):
            if d.air(x, y, z2 - 1) and y >= 4:
                d.set(x, y, z2 - 1, st("cobblestone", "south", "top"))
    seq = "C" + range_seq(min(L, 4), 5, 2) + "K"
    line(d, 5, y0, z2 - 1, "x", "north", seq, counter="cobblestone")
    for y in range(y0, ridge + 3):
        for x in (7, 8, 9):
            if y >= 5 or x == 8:
                d.set(x, y, z2, "cobblestone" if (x + y) % 4 else "mossy_cobblestone")
    d.set(8, ridge + 3, z2, sl("cobblestone"))
    for x in (7, 9):
        d.set(x, ridge + 2, z2, AIR)
    # racks on the west wall, prep counter on the east wall, chopping table in the middle
    for i, z in enumerate(range(7, 12)):
        if i < L:
            d.rack(x1 + 1, y0, z, "east")
        else:
            d.keg(x1 + 1, y0, z, "east")
    for z in range(7, 13):
        d.set(x2 - 1, y0, z, sl("spruce", "top"))
    d.set(x2 - 1, 3, 8, "dried_kelp_block")
    d.set(x2 - 1, 3, 10, "brown_mushroom_block[down=true,east=true,north=true,south=true,up=true,west=true]")
    d.set(x2 - 1, 3, 12, "potted_brown_mushroom")
    for z in (10, 11):
        d.set(8, y0, z, "stripped_spruce_wood[axis=y]")
    d.set(8, 3, 10, "lantern[hanging=false,waterlogged=false]")
    d.hut(x1 + 1, y0, z1 + 1)
    d.set(x1 + 1, y0, 12, "hay_block[axis=y]")
    d.dining(7, y0, 14, 2, "x", "spruce", ("n", "s"), sit=False)   # cooks' mess table in the back half
    d.set(x2 - 1, y0, 13, "barrel[facing=up,open=false]")
    for z in (8, 12):
        d.set(8, 5, z, lant())
    # L2+: open smokehouse shed to the east with smoking fires and hanging meat
    if L >= 2:
        sx1, sx2, sz1, sz2 = 13, 19, 9, 15
        for x, z in ((sx1, sz1), (sx2, sz1), (sx1, sz2), (sx2, sz2), (16, sz1), (16, sz2)):
            for y in range(y0, 5):
                d.set(x, y, z, lg("spruce_log"))
        roof(d, sx1, sz1, sx2, sz2, 5, "x", "spruce", "spruce_slab", None, keep=True, ends=(0, 1))
        for x in range(sx1, sx2 + 1):
            for z in range(sz1, sz2 + 1):
                d.set(x, 1, z, "packed_mud")
        for x in range(sx1 + 1, sx2):
            d.set(x, 4, 12, lg("stripped_spruce_log", "x"))
        for x in (14, 16, 18):
            d.set(x, 1, 12, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
            d.set(x, 3, 12, "hay_block[axis=y]")
        d.set(x2, y0, 13, AIR)
        d.door(x2, y0, 13, "east", "spruce")
        for z in range(sz1 + 1, sz2):
            if z != 12:
                d.set(sx2, y0, z, "spruce_fence")
    # L3+: firewood stacks along the west wall under a little roof
    if L >= 3:
        for z in range(7, 16):
            for y in (2, 3):
                d.set(2, y, z, lg("oak_log" if (y + z) % 3 else "birch_log", "x"))
            d.set(2, 4, z, sl("spruce"))
            d.set(3, 4, z, st("spruce", "east"))
    # L4+: water tower behind; L5: picnic table + chopping block
    if L >= 4:
        for x, z in ((17, 19), (20, 19), (17, 22), (20, 22)):
            for y in range(y0, 7):
                d.set(x, y, z, lg("spruce_log"))
        for x in range(17, 21):
            for z in range(19, 23):
                d.set(x, 7, z, "spruce_planks")
                for y in (8, 9, 10):
                    if x in (17, 20) or z in (19, 22):
                        d.set(x, y, z, lg("stripped_spruce_log", "x" if z in (19, 22) else "z"))
                d.set(x, 11, z, sl("spruce"))
        for y in range(8, 11):
            for x in (18, 19):
                for z in (20, 21):
                    d.set(x, y, z, "water")
    if L >= 5:
        d.dining(9, y0, 20, 2, "x", "spruce", ("n", "s"), sit=False)
        d.set(14, y0, 18, lg("oak_log"))
        d.set(14, 3, 18, "lantern[hanging=false,waterlogged=false]")
    return d


def cookery_neo(rel, L):
    d = Design("Neoterra", rel, (56, 42, 41), paving="smooth_stone")
    x1, z1, z2, y0, y1 = 3, 4, 14, 2, 5
    x2 = 15 if L == 1 else 22
    neo_body(d, x1, z1, x2, z2, y0, y1, wall="light_gray_concrete", pillar="gray_concrete", floor="smooth_stone",
             roof_="light_gray_concrete", parapet="light_gray_concrete", coping="smooth_stone_slab")
    d.fill(x1, y1, z1, x2, y1, z1, "cyan_concrete")
    for x in range(x1 + 1, x2):                                  # ribbon window
        if x % 4 != 3:
            d.set(x, 4, z1, "glass_pane")
    d.double_door(6, y0, z1, "x", "south", "iron")
    for y in range(y0, 10):                                      # vertical sign fin on the corner
        d.set(x1, y, z1 - 1, "cyan_terracotta" if y < 9 else "smooth_quartz")
    d.set(x1, 10, z1 - 1, "end_rod[facing=up]")
    for x in range(5, 10):                                       # entrance canopy
        for z in (z1 - 1, z1 - 2):
            d.set(x, 5, z, sl("smooth_quartz", "top"))
    d.sign(9, 4, z1 - 1, "north", ["CENTRAL", "KITCHEN"], "birch", glow=True, color="cyan")
    billboard(d, 8, 14, z1 + 2, y1 + 2, ["CENTRAL", "KITCHEN"], "cyan")
    for x in (10, 11):                                           # takeaway hatch with its own canopy
        d.set(x, y0, z1, "smooth_quartz")
        d.set(x, 3, z1, AIR)
        d.set(x, 5, z1 - 1, sl("smooth_quartz", "top"))
    d.sign(12, 4, z1 - 1, "north", ["TAKE", "AWAY"], "birch", glow=True, color="lime")
    for x in (x1 + 1, 13, 14):
        planter(d, x, z1 - 2, y0, "azalea")
    # cooking line in brushed steel (andesite) on the back wall, hood, extract
    seq = range_seq(min(L, 4), 6, 2) + "C"
    for x in range(x1 + 1, x1 + 9):
        d.set(x, y0, z2 - 1, "polished_andesite")
    line(d, x1 + 2, y0, z2 - 1, "x", "north", seq, counter="polished_andesite")
    hood(d, x1 + 1, x1 + 8, z2 - 1, 4, "south", "polished_andesite")
    for x in range(x1 + 2, x1 + 8):
        d.set(x, y0, 9, sl("smooth_stone", "top"))
    d.set(x1 + 3, 3, 9, "heavy_weighted_pressure_plate[power=0]")
    d.set(x1 + 6, 3, 9, "heavy_weighted_pressure_plate[power=0]")
    d.hut(x1 + 1, y0, z1 + 1)
    for x in range(x1 + 2, x2 - 1, 3):
        d.set(x, y1 + 1, 8, "sea_lantern")
    # roof plant: ducts and condensers
    for x in range(x1 + 2, x1 + 9):
        d.set(x, y1 + 2, z2 - 2, "polished_andesite")
    for i in range(L):
        cx = x1 + 2 + 3 * i
        if cx + 1 < x2:
            d.set(cx, y1 + 2, 7, "smooth_stone")
            d.set(cx + 1, y1 + 2, 7, "smooth_stone")
            d.set(cx, y1 + 3, 7, "iron_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]")
            d.set(cx + 1, y1 + 3, 7, "iron_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]")
    d.set(x1 + 5, y1 + 3, z2 - 2, "polished_andesite")
    d.set(x1 + 5, y1 + 4, z2 - 2, "iron_bars")
    if L == 1:
        d.rack(x2 - 1, y0, z2 - 1, "north")
        d.set(x2 - 1, y0, z2 - 2, "barrel[facing=up,open=false]")
        d.door(x2, y0, 8, "west", "iron")
        return d
    # L2+: walk-in cold room of packed ice holding the racks; loading bay with roller door on the east
    cx1, cx2, cz1 = 15, 21, 8
    d.box(cx1, y0, cz1, cx2 - 0, y1, z2, "packed_ice")
    for x, z in perim(cx1, cz1, cx2, z2):
        if x == x2 or z == z2:
            d.set(x, y0, z, "light_gray_concrete")
            for y in range(y0, y1 + 1):
                d.set(x, y, z, "light_gray_concrete")
    d.door(cx1, y0, 10, "west", "iron")
    for i, (x, z) in enumerate([(16, 13), (17, 13), (18, 13), (19, 13), (20, 13)]):
        if i < L:
            d.rack(x, y0, z, "north")
        else:
            d.set(x, y0, z, "blue_ice")
    d.set(20, y0, 9, "powder_snow_cauldron[level=3]")
    d.set(18, y1, 10, "sea_lantern")
    for z in (5, 6):
        for y in (y0, 3, 4):
            d.set(x2, y, z, AIR)
        d.set(x2, 5, z, "iron_trapdoor[facing=east,half=top,open=false,powered=false,waterlogged=false]")
    for z in range(5, 8):
        for x in (x2 + 1, x2 + 2):
            d.set(x, 1, z, "smooth_stone")
    d.set(x2 + 1, y0, 7, "barrel[facing=up,open=false]")
    d.set(x2 + 2, y0, 7, "barrel[facing=up,open=false]")
    for x in range(16, 21):
        if x < 20:
            d.set(x, y0, 6, "hay_block[axis=x]" if x % 2 else "melon")
    if L >= 3:                                                   # staff break bench + bins outside
        d.set(x1 - 1, y0, 8, "composter[level=4]")
        d.set(x1 - 1, y0, 9, "composter[level=2]")
    if L >= 4:                                                   # solar on the roof
        for x in range(x1 + 2, x2 - 1, 2):
            for z in (10, 11):
                d.set(x, y1 + 2, z, "daylight_detector[inverted=false,power=0]")
    if L >= 5:
        for x in (x1 + 1, x2 - 3):
            d.set(x, y0, z1 - 2, "flowering_azalea")
    return d


@design("cookery")
def cookery(pack, rel, L):
    d = {"Hearthwood": cookery_hw, "Cascadia": cookery_cas, "Neoterra": cookery_neo}[pack](rel, L)
    grow(d, L, "cookery")
    return d


def glass_gable(d, x1, z1, x2, z2, y, axis, frame="dark_oak", glass="glass", every=3, end="glass_pane", oh=0):
    """Glazed gable roof (stepped glass) with timber rafters every `every` cells and a timber ridge."""
    if axis == "x":
        lo, hi, a1, a2 = z1, z2, x1, x2
    else:
        lo, hi, a1, a2 = x1, x2, z1, z2
    L, H = lo - oh, hi + oh
    n = H - L + 1
    for i in range(n):
        w = L + i
        k = min(i, n - 1 - i)
        yy = y + k - oh
        mid = n % 2 == 1 and i == n // 2
        face = ("south" if i < n / 2 else "north") if axis == "x" else ("east" if i < n / 2 else "west")
        for a in range(a1, a2 + 1):
            x, z = (a, w) if axis == "x" else (w, a)
            if mid:
                s = sl(frame)
            elif (a - a1) % every == 0 or a == a2:
                s = st(frame, face)
            else:
                s = glass
            d.set(x, yy, z, s)
        if lo <= w <= hi:
            for a in (a1, a2):
                x, z = (a, w) if axis == "x" else (w, a)
                for yy2 in range(y, yy):
                    if d.air(x, yy2, z):
                        d.set(x, yy2, z, end)
    return y + (n - 1) // 2 - oh


FLOWERS = {"Hearthwood": ["poppy", "oxeye_daisy", "red_tulip", "pink_tulip", "lily_of_the_valley", "cornflower"],
           "Cascadia": ["dandelion", "azure_bluet", "blue_orchid", "allium", "fern"],
           "Neoterra": ["white_tulip", "orange_tulip", "torchflower"]}


def flower(d, i):
    """Flower for this pack: English cottage flowers / Pacific-Northwest wildflowers / designer white-orange."""
    f = FLOWERS[d.pack]
    return f[i % len(f)]


def beds(d, cells, y, n_compost, start=0):
    """Plant beds: the first n_compost cells are composted dirt (the florist's work beds, kept clear), the rest
    are grass with flowers."""
    for i, (x, z) in enumerate(cells):
        if i < n_compost:
            d.floor_item(x, y, z)
        else:
            d.set(x, y, z, "grass_block[snowy=false]")
            d.set(x, y + 1, z, flower(d, i + start))


def flower_stall(d, x1, x2, z, y, wood="spruce"):
    """Market stall of flower buckets: slab shelf with potted flowers, a second tier behind."""
    for i, x in enumerate(range(x1, x2 + 1)):
        d.set(x, y, z, sl(wood, "top"))
        d.set(x, y + 1, z, "potted_" + flower(d, i))


# ============================================================================================ FLORIST
# Hearthwood "Rose & Thistle": timber-framed flower shop with a bay of flower buckets out front, and a Victorian
#   glasshouse (brick plinth, glazed gable roof with dark-oak rafters) beside it holding the composted beds.
#   L3 the glasshouse doubles in length, L4 a picket-fenced cottage garden, L5 a rose arbour and sign.
# Cascadia "Fireweed Nursery": steep A-frame log shop with a porch of flower buckets, a long hoop-style
#   greenhouse beside it with raised beds; L2+ outdoor raised planter boxes, L4 potting shed, L5 a rain barrel
#   and wheelbarrow.
# Neoterra "BLOOM LAB": a single glass pavilion on a concrete frame, living green wall, flower bar at the
#   front, grid of quartz-edged planters; grows in length, L4 green roof edges, L5 glowing sign + benches.
def florist_hw(rel, L):
    d = Design("Hearthwood", rel, (54, 42, 44))
    y0, y1 = 2, 5
    oak = "dark_oak"
    hw_body(d, 3, 4, 12, 10, y0, y1)
    ridge = roof(d, 3, 4, 12, 10, 6, "x", "deepslate_tile", "deepslate_tile_slab", "calcite")
    d.door(6, y0, 4, "south", oak)
    for x in (4, 8, 9, 10):
        d.window(x, 3, 4, x, 4, 4)
    for x in (5, 9):
        d.window(x, 3, 10, x, 4, 10)
    d.window(3, 3, 7, 3, 4, 7)
    for y in range(y0, ridge + 2):                                # small brick chimney in the back wall
        d.set(4, y, 10, "bricks")
    # flower buckets under the windows and a bench of pots
    flower_stall(d, 8, 11, 3, y0, oak)
    for x in (3, 4, 5):
        d.set(x, y0, 3, "potted_" + flower(d, x + 5))
    awning(d, 8, 11, 4, 5, ("green_wool", "white_wool"))
    d.sign(6, 5, 3, "north", ["Rose &", "Thistle", "florist"], oak)
    # shop: counter with wrapping (crafting? no) and vases, racks of pots on the back wall, barrel
    d.hut(4, y0, 5)
    for x in (8, 9, 10):
        d.set(x, y0, 7, sl(oak, "top"))
    d.set(8, 3, 7, "potted_red_tulip")
    d.set(10, 3, 7, "decorated_pot[cracked=false,facing=north,waterlogged=false]")
    for i, x in enumerate((4, 5, 6, 7, 8)):
        if i < L:
            d.rack(x, y0, 9, "north")
        else:
            d.set(x, y0, 9, "potted_" + flower(d, i))
    for i, x in enumerate((4, 5, 6, 7, 8)):
        d.set(x, 3, 9, sl("spruce", "top"))
        d.set(x, 4, 9, "potted_" + flower(d, i + 3))
    d.item(10, y0, 9, "barrel")
    d.set(11, y0, 9, "composter[level=6]")
    d.lamp(7, 5, 7)
    # glasshouse
    gz2 = 10 if L < 3 else 16
    gx1, gx2, gz1 = 12, 21, 5
    for x, z in perim(gx1, gz1, gx2, gz2):
        if x == gx1 and z <= 10:
            continue
        d.set(x, 1, z, "bricks")
        d.set(x, y0, z, "bricks")
        for y in range(3, 6):
            d.set(x, y, z, lg("stripped_dark_oak_log") if (x - gx1) % 3 == 0 and z in (gz1, gz2)
                  or (z - gz1) % 3 == 0 and x in (gx1, gx2) else "glass_pane")
    for x in range(gx1 + 1, gx2):
        for z in range(gz1 + 1, gz2):
            d.set(x, 1, z, "bricks" if (x in (16, 17)) else "packed_mud")
            for y in range(y0, 6):
                d.set(x, y, z, AIR)
    glass_gable(d, gx1, gz1, gx2, gz2, 6, "z", oak, "glass", 3, "glass_pane")
    d.set(gx1, y0, 7, AIR)
    d.set(gx1, 3, 7, AIR)
    cells = []
    for z in range(gz1 + 1, gz2):
        for x in (13, 14, 19, 20):
            cells.append((x, z))
    beds(d, cells, 1, 4 * L)
    for z in range(gz1 + 2, gz2 - 1, 2):                       # potting bench down the middle
        d.set(16, y0, z, sl("spruce", "top"))
        d.set(16, 3, z, "potted_" + flower(d, z))
    d.set(17, y0, gz2 - 1, "water_cauldron[level=3]")
    d.set(16, y0, gz2 - 1, "potted_fern")
    if L >= 2:
        d.set(gx2, y0, 8, AIR)
        d.set(gx2, 3, 8, AIR)
        d.door(gx2, y0, 8, "west", oak)
    if L >= 4:                                                   # cottage garden with picket fence
        for x, z in perim(1, 11, 11, 19):
            d.set(x, y0, z, "birch_fence")
        d.set(6, y0, 11, "birch_fence_gate[facing=south,in_wall=false,open=false,powered=false]")
        d.door(6, y0, 10, "north", oak)
        for x in range(2, 11):
            for z in range(12, 19):
                d.set(x, 1, z, "grass_block[snowy=false]")
                if x != 6 and (x + z) % 2 == 0:
                    d.set(x, y0, z, flower(d, x * 3 + z))
            d.set(6, 1, 11 + 1, "gravel")
        for z in range(12, 19):
            d.set(6, 1, z, "gravel")
            d.set(6, y0, z, AIR)
    if L >= 5:                                                   # rose arbour + benches
        for x in (5, 7):
            for y in (2, 3, 4):
                d.set(x, y, 16, "dark_oak_fence")
        for x in (5, 6, 7):
            d.set(x, 5, 16, sl(oak))
            d.set(x, 4, 15, "flowering_azalea_leaves[distance=1,persistent=true,waterlogged=false]")
        d.set(4, y0, 18, st(oak, "south"))
        d.set(8, y0, 18, st(oak, "south"))
        d.set(1, y0, 3, "rose_bush[half=lower]")
        d.set(1, 3, 3, "rose_bush[half=upper]")
    return d


def florist_cas(rel, L):
    d = Design("Cascadia", rel, (54, 42, 45), paving="coarse_dirt")
    y0 = 2
    x1, z1, x2, z2 = 4, 7, 10, 15
    cas_body(d, x1, z1, x2, z2, y0, 3)
    roof(d, x1, z1, x2, z2, 4, "z", "dark_oak", "dark_oak_slab", "stripped_spruce_log[axis=y]",
                 ends=(2, 1))
    d.door(7, y0, z1, "south", "spruce")
    d.window(7, 5, z1, 7, 6, z1)
    for x in (5, 9):
        d.window(x, 3, z1, x, 3, z1)
    porch(d, x1, x2, 4, 6, y0, 5, (x1, x2), gap=(6, 7, 8), rail=False)
    d.sign(7, 4, z1 - 1, "north", ["FIREWEED", "NURSERY"], "spruce")
    flower_stall(d, x1, x1 + 1, 4, y0, "spruce")
    flower_stall(d, x2 - 1, x2, 4, y0, "spruce")
    d.set(x1, 4, 5, lant())
    d.set(x2, 4, 5, lant())
    # shop interior: racks of pots down the west wall, counter, barrel
    d.hut(x1 + 1, y0, z1 + 1)
    for i, z in enumerate(range(10, 15)):
        if i < L:
            d.rack(x1 + 1, y0, z, "east")
        else:
            d.set(x1 + 1, y0, z, "potted_" + flower(d, i))
    d.item(x2 - 1, y0, z2 - 1, "barrel")
    for z in (12, 13):                                          # display table of potted flowers mid-shop
        d.set(7, y0, z, sl("spruce", "top"))
        d.set(7, 3, z, "potted_" + flower(d, z + 3))
    for z in (9, 10, 11):
        d.set(x2 - 1, y0, z, sl("spruce", "top"))
        d.set(x2 - 1, 3, z, "potted_" + flower(d, z))
    d.set(7, 4, 11, lant())
    for z in (10, 13):
        d.window(x2, 3, z, x2, 3, z)
    # long greenhouse to the east: spruce frame, glass, raised beds
    gx1, gx2, gz1, gz2 = 12, 20, 5 if L < 3 else 5, 14 if L < 3 else 21
    for x, z in perim(gx1, gz1, gx2, gz2):
        d.set(x, y0, z, lg("spruce_log") if (x in (gx1, gx2) and (z - gz1) % 3 == 0) or z in (gz1, gz2)
              and (x - gx1) % 4 == 0 else "glass_pane")
        for y in (3, 4):
            d.set(x, y, z, lg("spruce_log") if (x in (gx1, gx2) and (z - gz1) % 3 == 0) or z in (gz1, gz2)
                  and (x - gx1) % 4 == 0 else "glass_pane")
        d.set(x, 1, z, "cobblestone")
    for x in range(gx1 + 1, gx2):
        for z in range(gz1 + 1, gz2):
            d.set(x, 1, z, "gravel")
    glass_gable(d, gx1, gz1, gx2, gz2, 5, "z", "spruce", "glass", 3, "glass_pane")
    d.door(16, y0, gz1, "south", "spruce")
    cells = []
    for z in range(gz1 + 2, gz2 - 1):
        for x in (gx1 + 1, gx1 + 2, gx2 - 2, gx2 - 1):
            cells.append((x, z))
    beds(d, cells, y0, 4 * L)
    d.set(16, y0, gz2 - 1, "water_cauldron[level=3]")
    d.set(16, 4, (gz1 + gz2) // 2, lant())
    for x in (13, 14):                                          # potting bench + soil barrel / composter by the door
        d.set(x, y0, gz1 + 1, sl("spruce", "top"))
        d.set(x, 3, gz1 + 1, "flower_pot")
    d.set(18, y0, gz1 + 1, "barrel[facing=up,open=false]")
    d.set(19, y0, gz1 + 1, "composter[level=5]")
    # L2+: raised planter boxes in the yard in front of the greenhouse
    if L >= 2:
        for x in range(13, 20, 3):
            for z in (1, 2):
                d.set(x, y0, z, "grass_block[snowy=false]")
                d.set(x, 3, z, flower(d, x + z))
                d.set(x + 1, y0, z, "grass_block[snowy=false]")
                d.set(x + 1, 3, z, flower(d, x + z + 4))
    # L4+: potting shed (lean-to) on the back of the shop
    if L >= 4:
        for x, z in perim(x1, z2, x2, z2 + 4):
            if z == z2:
                continue
            for y in (2, 3):
                d.set(x, y, z, lg("stripped_spruce_log", "x" if z == z2 + 4 else "z"))
        for x in range(x1 - 1, x2 + 2):
            for i, z in enumerate(range(z2 + 1, z2 + 6)):
                d.set(x, 4 - (i // 3), z, st("dark_oak", "north") if i % 3 == 0 else sl("dark_oak"))
        d.set(7, y0, z2, AIR)
        d.set(7, 3, z2, AIR)
        d.door(7, y0, z2, "south", "spruce")
        for x in (x1 + 1, x1 + 2):
            d.set(x, y0, z2 + 3, sl("spruce", "top"))
            d.set(x, 3, z2 + 3, "flower_pot")
        d.set(x2 - 1, y0, z2 + 3, "composter[level=7]")
        d.set(x2 - 1, y0, z2 + 1, "hay_block[axis=y]")
    if L >= 5:
        d.set(gx2 + 2, y0, 8, "water_cauldron[level=3]")
        d.set(2, y0, 10, "flowering_azalea")
        d.set(2, y0, 13, "azalea")
        d.set(22, y0, 18, "flowering_azalea")
    return d


def florist_neo(rel, L):
    d = Design("Neoterra", rel, (54, 42, 45), paving="smooth_stone")
    y0, y1 = 2, 6
    x1, z1, x2 = 4, 4, 18
    z2 = 12 if L < 3 else 18
    d.fill(x1, 1, z1, x2, 1, z2, "polished_diorite")
    for x, z in perim(x1, z1, x2, z2):
        post = (x - x1) % 4 == 0 and z in (z1, z2) or (z - z1) % 4 == 0 and x in (x1, x2) \
            or x in (x1, x2) and z in (z1, z2)
        for y in range(y0, y1 + 1):
            d.set(x, y, z, "light_gray_concrete" if post else "glass_pane")
        d.set(x, y1 + 1, z, "smooth_quartz")
    for x in range(x1 + 1, x2):                                 # glass roof on a quartz grid
        for z in range(z1 + 1, z2):
            d.set(x, y1 + 1, z, "smooth_quartz" if (x - x1) % 4 == 0 or (z - z1) % 4 == 0 else "glass")
    d.double_door(10, y0, z1, "x", "south", "birch")
    for x, t in ((10, "BLOOM"), (11, "LAB")):
        d.sign(x, y1 + 1, z1 - 1, "north", ["", t], "birch", glow=True, color="green")
    # living wall along the back, flower bar at the front, racks on the west
    for x in range(x1 + 1, x2):
        for y in range(y0, y1 + 1):
            d.set(x, y, z2 - 1, "moss_block" if (x + y) % 3 else
                  "flowering_azalea_leaves[distance=1,persistent=true,waterlogged=false]")
    d.hut(x2 - 1, y0, z1 + 1)
    for x in range(13, 17):
        d.set(x, y0, 7, "smooth_quartz")
        d.set(x, 3, 7, "potted_" + flower(d, x))
    d.item(x2 - 1, y0, 7, "barrel")
    for i, z in enumerate(range(z1 + 1, z1 + 6)):
        if i < L:
            d.rack(x1 + 1, y0, z, "east")
        else:
            d.set(x1 + 1, y0, z, "potted_" + flower(d, i))
    # planters: quartz-edged beds in a grid (composted dirt work beds first)
    cells = []
    for z in range(z1 + 3, z2 - 2, 2):
        for x in (7, 8, 10, 11, 13, 14):
            if z < 8 and x >= 13:
                continue
            cells.append((x, z))
    beds(d, cells, 1, 4 * L)
    for x in range(x1 + 2, x2 - 1, 4):
        d.set(x, y1, (z1 + z2) // 2, "end_rod[facing=down]")
    d.plant(x1 + 1, y0, z2 - 2, "potted_bamboo")
    d.plant(x2 - 1, y0, z2 - 2, "potted_bamboo")
    if L >= 4:                                                  # green roof edges
        for x in range(x1, x2 + 1):
            d.set(x, y1 + 2, z2, "azalea" if x % 2 else "moss_carpet")
            d.set(x, y1 + 2, z1, "moss_carpet")
    if L >= 5:
        for x in (x1 - 2, x2 + 2):
            for z in (z1 + 2, z1 + 6):
                d.set(x, y0, z, st("birch", "east" if x < x1 else "west"))
        for x in (x1 - 2, x2 + 2):
            d.set(x, y0, z1 + 4, "flowering_azalea")
    return d


@design("florist")
def florist(pack, rel, L):
    d = {"Hearthwood": florist_hw, "Cascadia": florist_cas, "Neoterra": florist_neo}[pack](rel, L)
    grow(d, L, "florist")
    return d


DYES = {"Hearthwood": ["red", "yellow", "blue", "brown", "orange", "green"],          # madder, weld, woad...
        "Cascadia": ["brown", "green", "red", "black", "light_gray", "gray"],        # bark, moss, alder
        "Neoterra": ["magenta", "cyan", "lime", "pink", "light_blue", "purple"]}     # synthetic brights


def dy(d, i):
    c = DYES[d.pack]
    return c[i % len(c)]


def drying_line(d, x1, x2, z, y, beam="stripped_spruce_log", post="spruce_log", k=0, kind="banner"):
    """Posts at both ends, a beam at y, and cloths hanging from it: wall banners on both faces of the beam
    (kind 'banner') or hanks of wool under it (kind 'wool')."""
    for x in (x1, x2):
        for yy in range(2, y + 1):
            d.set(x, yy, z, lg(post) if post.endswith("_log") else post)
    for x in range(x1 + 1, x2):
        d.set(x, y, z, lg(beam, "x"))
        c = dy(d, x + k)
        if kind == "banner":
            d.set(x, y, z - 1, f"{c}_wall_banner[facing=north]")
            d.set(x, y, z + 1, f"{dy(d, x + k + 5)}_wall_banner[facing=south]")
        elif (x - x1) % 2 == 1:
            d.set(x, y - 1, z, f"{c}_wool")


def vats(d, cells, y, n):
    """Dye vats: water cauldrons over fires (campfire sunk into the ground), first n counted."""
    for i, (x, z) in enumerate(cells):
        d.set(x, y - 1, z, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        if i < n:
            cauldron(d, x, y, z)
        else:
            d.set(x, y, z, "water_cauldron[level=2]")


# ============================================================================================ DYER
# Hearthwood "Madder & Woad Dyeworks": brick-and-plaster workshop with a tall square boiler chimney, loom and
#   bolts of coloured cloth inside; an open timber vat shed beside it with fired cauldrons, and drying lines
#   of coloured cloths in the yard behind (L3+). L4 a wool bale loft, L5 sign + hollyhocks.
# Cascadia "Riverbend Dye Shed": long open-sided timber pavilion gable to the street over a mill race, vats
#   along the water, log loom room at the back, drying frames with hanks of coloured wool; grows in length.
# Neoterra "CHROMA TEXTILES": concrete studio with a facade of rainbow concrete fins, glass front, vat line
#   inside, rooftop drying deck with banners on rails (L3+).
def dyer_hw(rel, L):
    d = Design("Hearthwood", rel, (57, 42, 44))
    y0, y1 = 2, 5
    oak = "dark_oak"
    nv = {1: 2, 2: 3, 3: 4}.get(L, 5)
    hw_body(d, 3, 4, 12, 10, y0, y1, wall="calcite")
    for x, z in perim(3, 4, 12, 10):
        if "calcite" in d.get(x, 3, z):
            d.set(x, 3, z, "bricks")
    ridge = roof(d, 3, 4, 12, 10, 6, "x", "deepslate_tile", "deepslate_tile_slab", "calcite")
    d.door(6, y0, 4, "south", oak)
    for x in (4, 8, 10):
        d.window(x, 4, 4, x, 4, 4)
        d.window(x, 4, 10, x, 4, 10)
    # boiler chimney (square, tall) on the west end
    for y in range(y0, ridge + 5):
        d.set(2, y, 7, "bricks")
        d.set(2, y, 6, "bricks")
        d.set(2, y, 8, "bricks")
        d.set(1, y, 7, "bricks")
    d.set(2, ridge + 5, 7, "bricks")
    furn(d, 4, y0, 7, "east", lit=True)                          # boiler furnace against the chimney
    d.set(4, 3, 7, "bricks")
    d.set(4, 4, 7, "bricks")
    d.set(4, 5, 7, "bricks")
    d.set(4, y0, 6, "water_cauldron[level=3]")
    d.set(4, y0, 8, "bricks")
    # workshop: loom, cutting table (crafting), racks of cloth bolts, coloured wool stacks
    d.item(7, y0, 9, f"loom[facing=north]")
    d.item(8, y0, 9, "crafting_table")
    for z, c in ((5, "red"), (6, "blue"), (7, "yellow")):
        d.set(11, y0, z, f"{c}_wool")
        d.set(11, 3, z, f"{dy(d, z)}_wool")
    for i, (x, z, f) in enumerate(((9, 9, "north"), (10, 9, "north"), (11, 9, "north"), (11, 5, "west"),
                                   (11, 6, "west"))):
        if i < L:
            d.rack(x, y0, z, f)
            d.set(x, 3, z, AIR)
        elif z == 9:
            d.set(x, y0, z, f"{dy(d, i)}_wool")
    d.set(5, y0, 9, "white_wool")
    d.set(5, 3, 9, "white_wool")
    d.hut(5, y0, 5)
    d.lamp(8, 5, 7)
    d.rug(7, 6, 9, 7, y0, ("light_blue_carpet", "orange_carpet"), "check")
    # vat shed to the east: open timber shed with fired vats
    sx1, sx2, sz1, sz2 = 13, 21 if L >= 3 else 18, 4, 10
    for x, z in perim(sx1, sz1, sx2, sz2):
        if x == sx1:
            continue
        if (x - sx1) % 3 == 0 and z in (sz1, sz2) or x == sx2 and z in (sz1, sz2):
            for y in range(y0, 5):
                d.set(x, y, z, lg("stripped_dark_oak_log"))
    for x in range(sx1, sx2 + 1):
        d.set(x, 5, sz1, lg("stripped_dark_oak_log", "x"))
        d.set(x, 5, sz2, lg("stripped_dark_oak_log", "x"))
        for z in range(sz1, sz2 + 1):
            d.set(x, 1, z, "cobblestone" if (x + z) % 3 else "mossy_cobblestone")
    roof(d, sx1, sz1, sx2, sz2, 6, "x", "deepslate_tile", "deepslate_tile_slab", None, keep=True, ends=(0, 1))
    d.set(12, y0, 7, AIR)
    d.set(12, 3, 7, AIR)
    cells = [(x, 8) for x in range(14, sx2)][:5] + [(x, 6) for x in range(14, sx2)]
    vats(d, cells[:max(nv, 3 if L < 3 else 5)], y0, nv)
    for x in range(14, sx2):
        if x % 3 == 0:
            d.set(x, 4, 7, "chain[axis=y,waterlogged=false]")
    d.set(sx2 - 1, y0, 5, "barrel[facing=up,open=false]")
    d.set(sx2 - 1, 3, 5, "blue_wool")
    # L3+: drying lines in the yard behind
    if L >= 3:
        for x in range(3, 22):
            for z in range(12, 21):
                d.set(x, 1, z, "grass_block[snowy=false]")
        drying_line(d, 4, 20, 14, 5, "stripped_dark_oak_log", "dark_oak_log", 0)
        if L >= 4:
            drying_line(d, 4, 20, 18, 5, "stripped_dark_oak_log", "dark_oak_log", 3)
        d.door(9, y0, 10, "north", oak)
    if L >= 4:                                                   # wool bales by the shed
        for x in (22, 23):
            for z in (5, 6, 7):
                d.set(x, y0, z, f"{dy(d, x + z)}_wool")
            d.set(x, 3, 6, "white_wool")
    if L >= 5:
        d.sign(6, 5, 3, "north", ["Madder &", "Woad", "dyeworks"], oak)
        for z in (12, 20):
            d.set(1, y0, z, "rose_bush[half=lower]")
            d.set(1, 3, z, "rose_bush[half=upper]")
        d.set(1, y0, 16, "lilac[half=lower]")
        d.set(1, 3, 16, "lilac[half=upper]")
    return d


def dyer_cas(rel, L):
    d = Design("Cascadia", rel, (54, 42, 50), paving="coarse_dirt")
    y0 = 2
    nv = {1: 2, 2: 3, 3: 4}.get(L, 5)
    x1, x2, z1 = 5, 13, 4
    z2 = {1: 14, 2: 16}.get(L, 20)
    # mill race along the west side
    for z in range(1, 28):
        d.set(2, 1, z, "water")
        d.set(3, 1, z, "water")
        d.set(1, 1, z, "mossy_cobblestone" if z % 3 == 0 else "cobblestone")
        d.set(4, 1, z, "mossy_cobblestone" if z % 4 == 0 else "cobblestone")
    # open pavilion: log posts, board floor, steep roof gable to the street
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            d.set(x, 1, z, "spruce_planks")
    for x in (x1, x2):
        for z in range(z1, z2 + 1, 3):
            for y in range(y0, 6):
                d.set(x, y, z, lg("spruce_log"))
        for z in range(z1, z2 + 1):
            d.set(x, 6, z, lg("stripped_spruce_log", "z"))
    for z in (z1, z2):
        for x in range(x1, x2 + 1):
            d.set(x, 6, z, lg("stripped_spruce_log", "x"))
        for y in range(y0, 6):
            d.set(x2, y, z, lg("spruce_log"))
    ridge = roof(d, x1, z1, x2, z2, 7, "z", "dark_oak", "dark_oak_slab", "spruce_planks", ends=(2, 1))
    for x in range(x1 + 1, x2):
        for z in range(z1 + 3, z2, 3):
            d.set(x, 6, z, lg("stripped_spruce_log", "x"))
    for x in (8, 9, 10):
        d.set(x, ridge - 2, z1, "spruce_planks")
    d.sign(9, ridge - 2, z1 - 1, "north", ["RIVERBEND", "DYE CO."], "spruce")
    # vats along the race side, fired from below
    cells = [(x1 + 1, z) for z in range(z1 + 2, z2 - 4, 2)][:5]
    vats(d, cells, y0, nv)
    for z in range(z1 + 1, z2 - 4):
        if d.air(x1, y0, z):
            d.set(x1, y0, z, "spruce_fence")
    # rinsing trough (water) and stirring paddles
    d.set(x1 + 3, y0, z1 + 2, "barrel[facing=up,open=false]")
    d.set(x1 + 3, 3, z1 + 2, "red_wool")
    # loom room: closed log room at the back of the pavilion
    rz1 = z2 - 4
    for x, z in perim(x1, rz1, x2, z2):
        for y in range(y0, 6):
            if d.air(x, y, z):
                d.set(x, y, z, lg("stripped_spruce_log", "x" if z in (rz1, z2) else "z"))
    for y in (2, 3):
        d.set(9, y, rz1, AIR)
    d.door(9, y0, rz1, "north", "spruce")
    d.window(x2, 3, z2 - 2, x2, 4, z2 - 2)
    d.item(x1 + 1, y0, z2 - 1, "loom[facing=north]")
    d.item(x1 + 2, y0, z2 - 1, "crafting_table")
    furn(d, x2 - 1, y0, z2 - 1, "north", lit=True)
    d.set(x2 - 1, 3, z2 - 1, "cobblestone")
    for y in range(4, ridge + 2):
        d.set(x2 - 1, y, z2, "cobblestone")
    for i, z in enumerate(range(rz1 + 1, z2 - 1)):
        if i < L:
            d.rack(x1 + 1, y0, z, "east")
    spare = [(x2 - 1, rz1 + 1, "west"), (x2 - 1, rz1 + 2, "west"), (x2 - 2, z2 - 1, "north")]
    for x, z, f in spare[:max(0, L - (z2 - 2 - rz1))]:
        d.rack(x, y0, z, f)
    d.hut(x2 - 1, y0, z1 + 1)
    for x in (x2 - 3, x2 - 2):                                  # bins of spun hanks in the loom room
        d.set(x, y0, rz1 + 1, "barrel[facing=up,open=false]")
    d.set(x2 - 1, y0, z1 + 3, "water_cauldron[level=3]")         # rinse tub + dyestuff barrels by the posts
    d.set(x2 - 1, y0, z1 + 4, "barrel[facing=up,open=false]")
    d.set(x2 - 1, 3, z1 + 4, "barrel[facing=up,open=false]")
    d.set(9, 5, z2 - 2, lant())
    d.set(9, 5, z1 + 3, lant())
    # drying frames with hanks of wool beside the pavilion
    drying_line(d, 15, 21, 6, 5, "stripped_spruce_log", "spruce_log", 0, "wool")
    if L >= 2:
        drying_line(d, 15, 21, 9, 5, "stripped_spruce_log", "spruce_log", 4, "wool")
    if L >= 3:
        drying_line(d, 15, 21, 12, 5, "stripped_spruce_log", "spruce_log", 8, "wool")
    if L >= 4:
        drying_line(d, 15, 21, 15, 5, "stripped_spruce_log", "spruce_log", 2, "wool")
        for x in range(15, 22):
            d.set(x, 1, 18, "spruce_planks")
        for x in (16, 18, 20):
            d.set(x, y0, 18, "white_wool")
            d.set(x, 3, 18, "white_wool")
    if L >= 5:
        for z in (24, 26):
            d.set(8, y0, z, "barrel[facing=up,open=false]")
            d.set(9, y0, z, "barrel[facing=up,open=false]")
        d.set(17, y0, 22, "flowering_azalea")
        d.set(12, y0, 25, "large_fern[half=lower]")
        d.set(12, 3, 25, "large_fern[half=upper]")
    return d


def dyer_neo(rel, L):
    d = Design("Neoterra", rel, (54, 42, 45), paving="smooth_stone")
    y0, y1 = 2, 6
    nv = {1: 2, 2: 3, 3: 4}.get(L, 5)
    x1, z1, z2 = 3, 5, 13
    x2 = 14 if L < 3 else 21
    neo_body(d, x1, z1, x2, z2, y0, y1)
    glass_front(d, x1 + 1, x2 - 1, z1, y0, y1, every=0)
    for i, x in enumerate(range(x1, x2 + 1, 2)):                # rainbow fins
        for y in range(y0, y1 + 2):
            d.set(x, y, z1 - 1, f"{dy(d, i)}_concrete")
    d.double_door(6, y0, z1, "x", "south", "birch")
    d.set(7, y0, z1 - 1, AIR)
    d.set(7, 3, z1 - 1, AIR)
    d.sign(9, y1 + 2, z1 - 1, "north", ["CHROMA", "TEXTILES"], "birch", glow=True, color="magenta")
    # vat line down the middle of the studio
    cells = [(x, 9) for x in range(x1 + 3, x1 + 3 + 2 * 5, 2)]
    for i, (x, z) in enumerate(cells):
        if i < nv:
            d.set(x, 1, z, "magma_block")
            cauldron(d, x, y0, z)
        elif x < x2 - 1:
            d.set(x, y0, z, "smooth_quartz")
    d.item(x1 + 1, y0, z2 - 1, "loom[facing=north]")
    d.item(x1 + 2, y0, z2 - 1, "crafting_table")
    furn(d, x1 + 3, y0, z2 - 1, "north")
    d.set(x1 + 3, 3, z2 - 1, "polished_andesite")
    for i in range(L):
        d.rack(x1 + 4 + i, y0, z2 - 1, "north")
    for i, x in enumerate(range(x1 + 4 + L, x2)):
        d.set(x, y0, z2 - 1, f"{dy(d, i)}_wool")
    d.hut(x1 + 1, y0, z1 + 1)
    for x in range(x1 + 2, x2 - 1, 3):
        d.set(x, y1 + 1, 9, "sea_lantern")
    for x in range(x1 + 2, x2 - 1, 2):                          # swatch wall: banners over the work line
        d.set(x, 5, z2 - 1, f"{dy(d, x)}_wall_banner[facing=north]")
    if L >= 3:                                                  # new east bay: cloth cutting table + bolt shelf
        for x in (16, 17, 18):
            d.set(x, y0, 7, sl("birch", "top"))
        d.set(16, 3, 7, f"{dy(d, 1)}_carpet")
        d.set(17, 3, 7, "white_carpet")
        d.set(18, 3, 7, f"{dy(d, 4)}_carpet")
        for x in (17, 18):
            d.chair(x, y0, 8, "south", "birch", sit=False)
        for z in (6, 7):
            d.set(20, y0, z, f"{dy(d, z)}_wool")
            d.set(20, 3, z, f"{dy(d, z + 2)}_wool")
            d.set(20, 4, z, f"{dy(d, z)}_carpet")
    # L3+: roof drying deck with banners on steel rails; L5 pergola of stained glass
    if L >= 3:
        for z in (8, 11):
            for x in range(x1 + 2, x2 - 1):
                d.set(x, y1 + 4, z, "light_gray_concrete") if x in (x1 + 2, x2 - 2) else \
                    d.set(x, y1 + 4, z, "iron_bars")
            for x in (x1 + 2, x2 - 2):
                for y in (y1 + 2, y1 + 3):
                    d.set(x, y, z, "light_gray_concrete")
            for x in range(x1 + 3, x2 - 2):
                d.set(x, y1 + 3, z - 1, f"{dy(d, x + z)}_wall_banner[facing=north]")
                d.set(x, y1 + 3, z + 1, f"{dy(d, x + z + 3)}_wall_banner[facing=south]")
    if L >= 4:
        for x in range(x1 + 1, x2, 2):
            d.set(x, y1 + 2, z2 - 1, "azalea")
    if L >= 5:
        for x in range(x1 + 1, x2):
            d.set(x, y1 + 1, z1, f"{dy(d, x)}_stained_glass")
    return d


@design("dyer")
def dyer(pack, rel, L):
    d = {"Hearthwood": dyer_hw, "Cascadia": dyer_cas, "Neoterra": dyer_neo}[pack](rel, L)
    grow(d, L, "dyer")
    return d


GLASS = {"Hearthwood": ["red", "blue", "yellow", "green"],                     # leaded church-window colours
         "Cascadia": ["orange", "brown", "lime", "light_gray"],                # amber / bottle tones
         "Neoterra": ["cyan", "light_blue", "magenta", "purple", "pink", "white"]}


def glass_c(d, i, pane=False):
    g = GLASS[d.pack]
    return f"{g[i % len(g)]}_stained_glass{'_pane' if pane else ''}"


# ============================================================================================ GLASSBLOWER
# Hearthwood "The Glass Cone": an English glass cone – a tall tapering brick cone with an arched doorway; inside,
#   a central brick furnace (glory holes on each face) whose flue rises to the open top, the marver bench
#   (crafting) and racks of cullet. L2+ a timber-framed shop wing with leaded windows full of coloured glass,
#   L4 cullet bins in the yard, L5 sign and lamps.
# Cascadia "Ember Glassworks": log workshop around a massive river-rock furnace stack, covered porch with
#   display shelves of stained glass; grows sideways, L4 a firewood/sand lean-to.
# Neoterra "PRISM GLASS STUDIO": white concrete cube with a stained-glass mosaic curtain wall, furnace island
#   under an extract hood in the middle; L3 a cantilevered glass display box over the entrance, L5 roof sign.
def glassblower_hw(rel, L):
    d = Design("Hearthwood", rel, (54, 42, 44))
    y0 = 2
    cx, cz = 15, 13
    top = 16
    for y in range(y0, top + 1):
        r = 5.4 if y <= 6 else max(1.6, 5.4 - (y - 6) * 0.38)
        for x in range(cx - 6, cx + 7):
            for z in range(cz - 6, cz + 7):
                dd = ((x - cx) ** 2 + (z - cz) ** 2) ** 0.5
                if r - 1.1 <= dd <= r:
                    d.set(x, y, z, "bricks")
    for x in range(cx - 5, cx + 6):
        for z in range(cz - 5, cz + 6):
            if ((x - cx) ** 2 + (z - cz) ** 2) ** 0.5 <= 5.4:
                d.set(x, 1, z, "bricks" if (x + z) % 2 else "stone_bricks")
    # arched doorway on the street side + a back door
    for y in (2, 3, 4):
        for x in (cx - 1, cx, cx + 1):
            d.set(x, y, cz - 5, AIR)
            if y < 4:
                d.set(x, y, cz - 4, AIR)
    d.set(cx - 1, 4, cz - 5, st("brick", "west", "top"))
    d.set(cx + 1, 4, cz - 5, st("brick", "east", "top"))
    # central furnace with glory holes, flue up the middle to the open top
    for x in (cx - 1, cx, cx + 1):
        for z in (cz - 1, cz, cz + 1):
            for y in (2, 3, 4):
                d.set(x, y, z, "bricks")
    for y in range(5, top + 2):
        d.set(cx, y, cz, "bricks")
    d.set(cx, top + 2, cz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    holes = [(cx, 2, cz - 1, "north"), (cx, 2, cz + 1, "south"), (cx - 1, 2, cz, "west"), (cx + 1, 2, cz, "east"),
             (cx, 3, cz - 1, "north")]
    for i, (x, y, z, f) in enumerate(holes):
        if i < L:
            furn(d, x, y, z, f, lit=True)
        else:
            if y == 2:
                d.set(x, y, z, "magma_block")
    for x, z in ((cx - 1, cz - 1), (cx + 1, cz - 1), (cx - 1, cz + 1), (cx + 1, cz + 1)):
        d.set(x, 4, z, sl("brick"))
    # workplaces round the wall: marver bench (crafting), racks of cullet, annealing shelf
    d.item(cx - 3, y0, cz + 3, "crafting_table")
    d.set(cx - 4, y0, cz + 1, sl("smooth_stone", "top"))
    d.set(cx - 4, 3, cz + 1, glass_c(d, 0))
    rk = [(cx + 3, cz + 3, "west"), (cx + 4, cz + 1, "west"), (cx + 4, cz - 1, "west"), (cx - 2, cz + 4, "north"),
          (cx + 2, cz + 4, "north")]
    for i, (x, z, f) in enumerate(rk):
        if i < L:
            d.rack(x, y0, z, f)
    d.set(cx - 4, y0, cz - 1, "water_cauldron[level=3]")
    for x in (cx - 2, cx + 3):                                  # cullet barrels either side of the doorway
        d.set(x, y0, cz - 3, "barrel[facing=up,open=false]")
    d.hut(cx - 3, y0, cz - 3)
    for x, z in ((cx - 3, cz), (cx + 3, cz)):
        d.set(x, 2, z, "lantern[hanging=false,waterlogged=false]")
    # L2+: shop wing on the west with coloured glass in leaded windows
    if L >= 2:
        sx1, sx2, sz1, sz2 = 2, 10, 5, 11
        hw_body(d, sx1, sz1, sx2, sz2, y0, 5)
        roof(d, sx1, sz1, sx2, sz2, 6, "x", "deepslate_tile", "deepslate_tile_slab", "calcite", keep=True,
             ends=(1, 0))
        d.door(6, y0, sz1, "south", "dark_oak")
        for i, x in enumerate((3, 4, 8, 9)):
            d.window(x, 3, sz1, x, 4, sz1, glass_c(d, i, True))
        for x in (3, 4, 8, 9):                                  # display shelves behind the windows
            d.set(x, y0, sz1 + 1, sl("dark_oak", "top"))
            d.set(x, 3, sz1 + 1, glass_c(d, x))
        for x in range(3, 8):
            d.set(x, y0, sz2 - 1, sl("dark_oak", "top"))
            d.set(x, 3, sz2 - 1, glass_c(d, x + 3, True) if x % 2 else glass_c(d, x + 3))
        d.set(sx2, y0, 8, AIR)
        d.set(sx2, 3, 8, AIR)
        for y in (2, 3):
            d.set(10, y, 8, AIR)
            d.set(11, y, 8, AIR)
        d.lamp(6, 5, 8)
        d.sign(6, 5, sz1 - 1, "north", ["The", "Glass Cone"], "dark_oak")
    if L >= 4:                                                  # cullet bins in the yard
        for i, x in enumerate(range(3, 10, 2)):
            for z in (14, 15):
                d.set(x, 1, z, "cobblestone")
            d.set(x, y0, 14, glass_c(d, i))
            d.set(x, y0, 15, glass_c(d, i + 4))
            d.set(x + 1, y0, 14, "cobblestone_wall")
            d.set(x + 1, y0, 15, "cobblestone_wall")
        d.set(3, y0, 17, "sand")
        d.set(4, y0, 17, "sand")
        d.set(3, 3, 17, "sand")
    if L >= 5:
        for x in (11, 19):
            d.set(x, y0, 6, "dark_oak_fence")
            d.set(x, 3, 6, "dark_oak_fence")
            d.set(x, 4, 6, "lantern[hanging=false,waterlogged=false]")
    return d


def glassblower_cas(rel, L):
    d = Design("Cascadia", rel, (54, 42, 43), paving="coarse_dirt")
    y0, y1 = 2, 5
    x1, z1, z2 = 3, 7, 14
    x2 = 13 if L < 3 else 20
    cas_body(d, x1, z1, x2, z2, y0, y1, ceiling=None)
    ridge = roof(d, x1, z1, x2, z2, 6, "x", "spruce", "spruce_slab", "spruce_planks", ends=(1, 1))
    porch(d, x1, x2, 3, 6, y0, 6, tuple(range(x1, x2 + 1, 5)) + (x2,), gap=(6, 7, 8), rail=False)
    d.door(7, y0, z1, "south", "spruce")
    for x in (5, 9, 10, 11) + ((15, 16, 17) if L >= 3 else ()):
        d.window(x, 3, z1, x, 4, z1, glass_c(d, x, True))
    # porch display shelves of coloured glass
    for x in range(x1 + 1, x2):
        if x in (6, 7, 8):
            continue
        if (x - x1) % 5 == 0:
            continue
        d.set(x, y0, 5, sl("spruce", "top"))
        d.set(x, 3, 5, glass_c(d, x))
    d.sign(7, 5, z1 - 1, "north", ["EMBER", "GLASSWORKS"], "spruce")
    # river-rock furnace stack at the back, rising through the roof
    fx = 8
    for x in range(fx - 1, fx + 2):
        for y in range(y0, ridge + 3):
            d.set(x, y, z2, "cobblestone" if (x + y) % 3 else "mossy_cobblestone")
        for y in range(y0, 5):
            d.set(x, y, z2 - 1, "cobblestone")
    for y in range(ridge + 3, ridge + 5):
        d.set(fx, y, z2, "cobblestone")
    hole = [(fx, 2), (fx - 1, 2), (fx + 1, 2), (fx, 3), (fx - 1, 3)]
    for i, (x, y) in enumerate(hole):
        if i < L:
            furn(d, x, y, z2 - 1, "north", lit=True)
    d.set(fx, 4, z2 - 1, "cobblestone")
    for x in range(fx - 1, fx + 2):
        d.set(x, 5, z2 - 2, st("cobblestone", "south", "top"))
    d.item(x1 + 1, y0, z2 - 1, "crafting_table")
    d.set(x1 + 2, y0, z2 - 1, sl("spruce", "top"))
    d.set(x1 + 1, y0, z2 - 2, "water_cauldron[level=3]")
    for i in range(L):
        d.rack(x2 - 1, y0, z1 + 1 + i, "west") if i < 3 else d.rack(x2 - 2 - (i - 3), y0, z2 - 1, "north")
    d.hut(x1 + 1, y0, z1 + 1)
    for x in range(5, 12, 3):
        d.set(x, 5, 10, lant())
    # workbench with blowpipes (lightning rods) on the wall
    for x in (10, 11):
        d.set(x, y0, 10, "stripped_spruce_wood[axis=y]")
    d.set(10, 3, 10, glass_c(d, 2))
    d.set(11, 3, 10, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    for z in (10, 11):                                          # marver bench on the west wall + gaffer's chair
        d.set(x1 + 1, y0, z, "stripped_spruce_wood[axis=y]")
    d.set(x1 + 1, 3, 10, "flower_pot")
    d.set(x1 + 1, 3, 11, glass_c(d, 4, True))
    d.chair(x1 + 2, y0, 10, "east", "spruce", sit=False, arms=True)
    for z in (z2 - 1, z2 - 2):                                  # sand barrels in the back corner
        d.set(x2 - 1, y0, z, "barrel[facing=up,open=false]")
    if L >= 3:                                                  # showroom in the extension
        for x in (15, 17):
            d.set(x, y0, 10, "stripped_spruce_wood[axis=y]")
            d.set(x, 3, 10, glass_c(d, x))
            d.set(x, y0, 12, "stripped_spruce_wood[axis=y]")
            d.set(x, 3, 12, glass_c(d, x + 3, True))
        d.set(17, 5, 11, lant())
    if L >= 4:                                                  # sand & firewood lean-to on the west end
        for z in range(z1 + 1, z2):
            d.set(1, y0, z, "sand" if z < 11 else lg("oak_log", "x"))
            d.set(1, 3, z, "sand" if z < 10 else lg("oak_log", "x"))
            d.set(1, 4, z, sl("spruce"))
            d.set(2, 4, z, st("spruce", "east"))
        d.set(1, 4, z1, sl("spruce"))
    if L >= 5:
        d.set(x2 + 2, y0, 4, "flowering_azalea")
        d.set(x2 + 2, y0, 6, "large_fern[half=lower]")
        d.set(x2 + 2, 3, 6, "large_fern[half=upper]")
        for x in (x1, x2):
            d.set(x, 5, 4, lant())
    return d


def glassblower_neo(rel, L):
    d = Design("Neoterra", rel, (54, 42, 45), paving="smooth_stone")
    y0, y1 = 2, 7
    x1, z1, x2, z2 = 4, 5, 16, 15
    neo_body(d, x1, z1, x2, z2, y0, y1)
    for x in range(x1 + 1, x2):                                 # stained-glass mosaic street wall
        for y in range(y0, y1 + 1):
            d.set(x, y, z1, glass_c(d, x * 3 + y * 7))
    for x in (x1 + 4, x2 - 4):
        for y in range(y0, y1 + 1):
            d.set(x, y, z1, "light_gray_concrete")
    d.double_door(10, y0, z1, "x", "south", "birch")
    for x in (10, 11):
        d.set(x, 4, z1, "white_concrete")
    for z in range(z1 + 2, z2 - 1, 3):
        d.window(x2, 3, z, x2, 6, z, "glass_pane")
        d.window(x1, 3, z, x1, 6, z, "glass_pane")
    d.sign(10, y1 + 1, z1 - 1, "north", ["PRISM", "GLASS"], "birch", glow=True, color="light_blue")
    d.sign(11, y1 + 1, z1 - 1, "north", ["", "STUDIO"], "birch", glow=True, color="light_blue")
    # furnace island under an extract hood
    for x in (9, 10, 11):
        for z in (10, 11):
            d.set(x, y0, z, "polished_andesite")
            d.set(x, 3, z, "polished_andesite")
    fz = [(9, 2, 10, "north"), (10, 2, 10, "north"), (11, 2, 10, "north"), (9, 2, 11, "south"), (11, 2, 11, "south")]
    for i, (x, y, z, f) in enumerate(fz):
        if i < L:
            furn(d, x, y, z, f, lit=True)
    for x in (9, 10, 11):
        for z in (10, 11):
            d.set(x, 6, z, "polished_andesite")
    for y in range(7, y1 + 4):
        d.set(10, y, 10, "polished_andesite")
    d.set(10, y1 + 4, 10, sl("smooth_stone"))
    d.item(x1 + 1, y0, z2 - 1, "crafting_table")
    for i in range(L):
        d.rack(x2 - 1, y0, z2 - 1 - i, "west")
    for x in range(x1 + 2, x1 + 6):                             # gallery plinths
        d.set(x, y0, z2 - 1, "smooth_quartz")
        d.set(x, 3, z2 - 1, glass_c(d, x))
    for z in (z1 + 2, z1 + 4):
        d.set(x1 + 1, y0, z, "smooth_quartz")
        d.set(x1 + 1, 3, z, glass_c(d, z, True))
    d.hut(x2 - 1, y0, z1 + 1)
    # studio fittings: marver bench + stool and quench bucket on the west wall, annealing lehr with sand and
    # cullet bins on the south wall, a sales shelf and the order lectern by the hut
    d.set(5, y0, 11, sl("smooth_stone", "top"))
    d.set(5, 3, 11, "flower_pot")
    d.set(5, y0, 12, sl("smooth_stone", "top"))
    d.set(5, 3, 12, glass_c(d, 2, True))
    d.chair(6, y0, 12, "east", "birch", sit=False)
    d.set(5, y0, 13, "water_cauldron[level=3]")
    d.set(11, y0, 14, "barrel[facing=up,open=false]")
    d.set(12, y0, 14, "blast_furnace[facing=north,lit=true]")
    d.set(13, y0, 14, "blast_furnace[facing=north,lit=false]")
    d.set(14, y0, 14, "barrel[facing=up,open=false]")
    for x in (13, 14):
        d.set(x, y0, 6, sl("birch", "top"))
    d.set(13, 3, 6, "decorated_pot[cracked=false,facing=south,waterlogged=false]")
    d.set(14, 3, 6, "potted_" + "blue_orchid")
    d.set(6, y0, 6, sl("birch", "top"))
    d.set(6, 3, 6, glass_c(d, 5, True))
    d.set(15, y0, 8, "lectern[facing=west,has_book=true,powered=false]")
    for x in range(x1 + 2, x2 - 1, 3):
        d.set(x, y1 + 1, 8, "sea_lantern")
        d.set(x, y1 + 1, 13, "sea_lantern")
    if L >= 3:                                                  # cantilevered glass display box on the front
        for x in range(7, 15):
            d.set(x, 4, z1 - 1, "smooth_quartz")
            d.set(x, 4, z1 - 2, "smooth_quartz")
            for y in (5, 6):
                d.set(x, y, z1 - 2, glass_c(d, x + y, True) if x in (7, 14) else "glass_pane")
            d.set(x, 7, z1 - 2, "smooth_quartz")
            d.set(x, 7, z1 - 1, "smooth_quartz")
        for x in range(8, 14):
            d.set(x, 5, z1 - 1, glass_c(d, x))
    if L >= 4:
        for x in range(x1 + 1, x2, 2):
            d.set(x, y1 + 2, z2 - 1, "azalea")
    if L >= 5:
        for x in range(x1 + 2, x2 - 1, 2):
            d.set(x, y1 + 2, z1 + 2, "daylight_detector[inverted=false,power=0]")
        for x in (x1 - 2, x2 + 2):
            d.set(x, y0, z1 - 1, "flowering_azalea")
    return d


@design("glassblower")
def glassblower(pack, rel, L):
    d = {"Hearthwood": glassblower_hw, "Cascadia": glassblower_cas, "Neoterra": glassblower_neo}[pack](rel, L)
    grow(d, L, "glassblower")
    return d


def silo(d, cx, cz, y0, h, wall="white_concrete", band="cyan_concrete", r=2.3, cap="smooth_quartz_slab"):
    """Round silo (about 5 across) standing on the ground, banded, with a cap and a ladder on the north side."""
    for y in range(y0, y0 + h):
        for x in range(cx - 3, cx + 4):
            for z in range(cz - 3, cz + 4):
                dd = ((x - cx) ** 2 + (z - cz) ** 2) ** 0.5
                if dd <= r:
                    edge = dd > r - 1.2
                    if edge:
                        d.set(x, y, z, band if (y - y0) % 5 == 4 else wall)
    for x in range(cx - 3, cx + 4):
        for z in range(cz - 3, cz + 4):
            if ((x - cx) ** 2 + (z - cz) ** 2) ** 0.5 <= r:
                d.set(x, y0 + h, z, f"{cap}[type=bottom,waterlogged=false]")


# ============================================================================================ CONCRETE MIXER
# All three are built around the required mixing basin (a 19x4 water channel pasted with d.cluster).
# Hearthwood "Thatcham Lime & Mortar Works": stone-brick workshop with a tall square lime kiln, sand and
#   gravel bays walled in cobblestone, and an open timber shed roofing the basin (L2+). L4 a second kiln
#   stack and wheelbarrow yard, L5 sign + lamps.
# Cascadia "Cascade Aggregate Co.": a log office shack, a tall timber hopper tower with a plank chute running
#   down to the basin, open log-walled sand/gravel bins; tower grows with level, L5 a second chute.
# Neoterra "NEOCRETE PLANT": glass control office with cyan trim, a row of white banded silos (1 at L1, 2 at
#   L2, 3 at L3+) with chutes down to the basin, L4 conveyor bridge, L5 roof sign.
def concretemixer_hw(rel, L):
    d = Design("Hearthwood", rel, (55, 42, 45))
    y0 = 2
    d.cluster(3, 17)                                             # basin x3..21, z17..20
    # workshop
    x1, z1, x2, z2 = 3, 4, 12, 11
    hw_body(d, x1, z1, x2, z2, y0, 5, wall="stone_bricks", base="cobblestone", beam="stripped_spruce_log")
    for x, z in perim(x1, z1, x2, z2):
        if (x + z) % 5 == 0 and "stone_bricks" in d.get(x, 3, z):
            d.set(x, 3, z, "mossy_stone_bricks")
    ridge = roof(d, x1, z1, x2, z2, 6, "x", "deepslate_tile", "deepslate_tile_slab", "stone_bricks")
    d.door(6, y0, z1, "south", "spruce")
    d.door(9, y0, z2, "north", "spruce")
    for x in (4, 8, 10):
        d.window(x, 3, z1, x, 4, z1)
    d.window(x1, 3, 7, x1, 4, 8)
    d.hut(4, y0, 5)
    d.item(4, y0, 10, "crafting_table")
    for i in range(L):
        x, z, f = [(5, 10, "north"), (6, 10, "north"), (7, 10, "north"), (11, 5, "west"), (11, 6, "west")][i]
        d.rack(x, y0, z, f)
    for x, z, b in ((11, 8, "white_concrete_powder"), (11, 9, "light_gray_concrete_powder"),
                    (10, 10, "gray_concrete_powder")):
        d.set(x, y0, z, b)
    d.set(11, 3, 9, "white_concrete_powder")
    d.set(8, y0, 7, sl("spruce", "top"))
    d.set(8, 3, 7, "flower_pot")
    d.lamp(7, 5, 7)
    # lime kiln: tall square stone tower with a fire arch
    kx1, kz1 = 14, 5
    for y in range(y0, ridge + 6 if L >= 3 else ridge + 3):
        for x in range(kx1, kx1 + 3):
            for z in range(kz1, kz1 + 3):
                if x in (kx1, kx1 + 2) or z in (kz1, kz1 + 2) or y < 5:
                    d.set(x, y, z, "stone_bricks" if (x + y + z) % 4 else "mossy_stone_bricks")
    d.set(kx1 + 1, y0, kz1, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    d.set(kx1 + 1, 3, kz1, AIR)
    d.set(kx1 + 1, 4, kz1, st("stone_brick", "north", "top"))
    # sand & gravel bays (cobblestone walls)
    for x in range(18, 24):
        for z in (5, 6, 7, 8, 9):
            if x in (18, 20, 23):
                d.set(x, y0, z, "cobblestone_wall")
    for z in (5, 6, 7, 8):
        d.set(19, y0, z, "sand")
        d.set(21, y0, z, "gravel")
        d.set(22, y0, z, "gravel")
        if z < 7:
            d.set(19, 3, z, "sand")
            d.set(21, 3, z, "gravel")
    # basin shed (L2+): timber posts, gable roof over the channel
    if L >= 2:
        for x in range(3, 22, 3):
            for z in (16, 21):
                for y in range(y0, 6):
                    d.set(x, y, z, lg("stripped_spruce_log"))
        for x in (21,):
            for z in (16, 21):
                for y in range(y0, 6):
                    d.set(x, y, z, lg("stripped_spruce_log"))
        roof(d, 3, 16, 21, 21, 6, "x", "deepslate_tile", "deepslate_tile_slab", None, ends=(1, 1))
        for x in range(3, 22):
            d.set(x, 5, 16, lg("stripped_spruce_log", "x"))
            d.set(x, 5, 21, lg("stripped_spruce_log", "x"))
    for x in range(3, 22):
        d.set(x, 1, 15, "gravel")
    if L >= 4:
        for x, z in ((15, 12), (16, 12)):
            d.set(x, y0, z, "white_concrete_powder")
        d.set(17, y0, 12, "gray_concrete_powder")
        d.set(15, 3, 12, "white_concrete_powder")
        d.set(19, y0, 12, "cauldron")
        d.set(20, y0, 12, "composter[level=0]")
    if L >= 5:
        d.sign(6, 5, z1 - 1, "north", ["Lime &", "Mortar", "Works"], "spruce")
        for x in (2, 13):
            d.set(x, y0, 3, "spruce_fence")
            d.set(x, 3, 3, "lantern[hanging=false,waterlogged=false]")
    return d


def concretemixer_cas(rel, L):
    d = Design("Cascadia", rel, (54, 42, 47), paving="coarse_dirt")
    y0 = 2
    d.cluster(2, 21)                                             # basin x2..20, z21..24
    # office shack
    x1, z1, x2, z2 = 3, 5, 10, 11
    cas_body(d, x1, z1, x2, z2, y0, 4, ceiling=None)
    roof(d, x1, z1, x2, z2, 5, "z", "dark_oak", "dark_oak_slab", "spruce_planks", ends=(1, 1))
    d.door(6, y0, z1, "south", "spruce")
    d.window(8, 3, z1, 9, 3, z1)
    d.window(x1, 3, 8, x1, 3, 8)
    d.sign(6, 4, z1 - 1, "north", ["CASCADE", "AGGREGATE", "CO."], "spruce")
    d.hut(4, y0, 6)
    d.item(9, y0, 10, "crafting_table")
    for i in range(L):
        x, z, f = [(4, 10, "north"), (5, 10, "north"), (6, 10, "north"), (9, 7, "west"), (9, 8, "west")][i]
        d.rack(x, y0, z, f)
    d.set(8, y0, 10, "barrel[facing=up,open=false]")
    d.set(7, 4, 8, lant())
    # hopper tower: log frame, plank bin on top, chute to the basin
    h = {1: 8, 2: 9}.get(L, 11)
    tx1, tz1 = 14, 9
    for x in (tx1, tx1 + 3):
        for z in (tz1, tz1 + 3):
            for y in range(y0, h + 4):
                d.set(x, y, z, lg("spruce_log"))
    for x in range(tx1, tx1 + 4):
        for z in range(tz1, tz1 + 4):
            for y in (h, h + 1, h + 2, h + 3):
                if x in (tx1, tx1 + 3) or z in (tz1, tz1 + 3):
                    if not "log" in d.get(x, y, z):
                        d.set(x, y, z, "spruce_planks" if y < h + 3 else lg("stripped_spruce_log", "x"))
                elif y == h:
                    d.set(x, y, z, "spruce_planks")
                else:
                    d.set(x, y, z, "gravel")
    for x in range(tx1 - 1, tx1 + 5):
        for z in range(tz1 - 1, tz1 + 5):
            d.set(x, h + 4, z, sl("dark_oak"))
    d.set(tx1 + 1, h - 1, tz1 + 1, "hopper[enabled=true,facing=down]")
    d.set(tx1 + 2, h - 1, tz1 + 2, "hopper[enabled=true,facing=down]")
    # chute: plank slide from the tower down to the basin
    cz = tz1 + 4
    for i in range(h - 3):
        y = h - 1 - i
        z = cz + i
        if z >= 21 or y < 3:
            break
        d.set(tx1 + 1, y, z, st("spruce", "north"))
        d.set(tx1 + 2, y, z, st("spruce", "north"))
        if i % 3 == 0:
            for yy in range(y0, y):
                d.set(tx1 + 3, yy, z, "spruce_fence")
    # open bins of sand and gravel
    for i, (m, bx) in enumerate((("sand", 3), ("gravel", 7), ("sand", 11))):
        for x in range(bx, bx + 3):
            for z in (14, 15, 16, 17):
                if x == bx or z == 17 or x == bx + 2 and bx == 11:
                    d.set(x, y0, z, lg("spruce_log", "z" if x in (bx,) else "x"))
                else:
                    d.set(x, y0, z, m)
                    if z > 15:
                        d.set(x, 3, z, m)
    if L >= 3:
        for x in range(2, 21):
            d.set(x, 1, 19, "gravel")
            d.set(x, 1, 20, "gravel")
    if L >= 5:
        for i in range(5):
            if 16 + i < 21:
                d.set(19, 6 - i, 16 + i, st("spruce", "north"))
        for x in (2, 12):
            d.set(x, y0, 3, lg("spruce_log"))
            d.set(x, 3, 3, lant(False))
    return d


def concretemixer_neo(rel, L):
    d = Design("Neoterra", rel, (54, 42, 45), paving="smooth_stone")
    y0 = 2
    d.cluster(2, 18)                                             # basin x2..20, z18..21
    # glass control office (two storeys at L3+)
    x1, z1, x2, z2 = 3, 3, 10, 9
    neo_body(d, x1, z1, x2, z2, y0, 5)
    glass_front(d, x1 + 1, x2 - 1, z1, y0, 5, every=0)
    d.fill(x1, 6, z1, x2, 6, z1, "cyan_terracotta")
    d.double_door(5, y0, z1, "x", "south", "birch")
    d.window(x2, 3, 5, x2, 4, 7)
    d.hut(x2 - 1, y0, z1 + 1)
    d.item(x1 + 1, y0, z2 - 1, "crafting_table")
    for i in range(L):
        d.rack(x1 + 2 + i, y0, z2 - 1, "north")
    d.set(x1 + 1, y0, z1 + 2, "smooth_quartz")
    d.set(x1 + 1, 3, z1 + 2, "potted_bamboo")
    for z in (6, 7):                                            # control desk at the window over the yard
        d.set(x2 - 1, y0, z, sl("birch", "top"))
    d.set(x2 - 1, 3, 6, "potted_azalea_bush")
    d.chair(x2 - 2, y0, 6, "west", "birch", sit=False)
    d.set(x1 + 1, y0, 6, "barrel[facing=up,open=false]")         # sample barrels
    d.set(x1 + 1, y0, 7, "barrel[facing=up,open=false]")
    for x in (5, 8):
        d.set(x, 6, 6, "sea_lantern")
    d.sign(8, 6, z1 - 1, "north", ["NEOCRETE"], "birch", glow=True, color="cyan")
    # silos with chutes down to the basin
    n = min(L, 3)
    sil = [(15, 6), (15, 12), (6, 13)][:n]
    for cx, cz in sil:
        silo(d, cx, cz, y0, 9 + (2 if L >= 4 else 0))
    for cx, cz in sil:                                           # chute from the silo foot to the basin
        z = cz + 3
        while z < 18:
            d.set(cx, 3, z, "smooth_stone_slab[type=bottom,waterlogged=false]")
            d.set(cx, y0, z, "light_gray_concrete")
            z += 1
    if L >= 4:                                                   # conveyor bridge office -> silos
        for x in range(x2 + 1, 13):
            d.set(x, 7, 5, "smooth_stone_slab[type=top,waterlogged=false]")
            d.set(x, 8, 4, "iron_bars")
            d.set(x, 8, 6, "iron_bars")
    if L >= 5:
        for x in range(x1, x2 + 1):
            d.set(x, 8, z2, "cyan_concrete")
        d.set(x1 + 1, 8, z1 + 1, "azalea")
        d.set(x2 - 1, 8, z1 + 1, "azalea")
    return d


@design("concretemixer")
def concretemixer(pack, rel, L):
    d = {"Hearthwood": concretemixer_hw, "Cascadia": concretemixer_cas,
            "Neoterra": concretemixer_neo}[pack](rel, L)
    grow(d, L, "concretemixer")
    return d


# ============================================================================================ ADD-ON BUILDINGS
# The huts grow into complexes of add-on buildings. bld() draws ONE building's structure (storeys, walls,
# windows, door, fixed straight stair, roof) and then lays its furniture exactly as written in the building's
# hand-drawn floor plans (one ASCII plan per storey, rows north->south, columns west->east over the interior).
# All exterior dressing is an explicit list per building. Nothing is placed by scanning or by a generic room
# routine - every piece sits where the plan or the list puts it.
STY = {
    "Hearthwood": dict(wood="dark_oak", wood2="spruce", floor="oak_planks", rug=("red_carpet", "orange_carpet"),
                       bed="red", banner="red", plant="potted_red_tulip", chim="bricks", stone="stone_brick"),
    "Cascadia": dict(wood="spruce", wood2="dark_oak", floor="spruce_planks", rug=("brown_carpet", "green_carpet"),
                     bed="brown", banner="green", plant="potted_fern", chim="cobblestone", stone="cobblestone"),
    "Neoterra": dict(wood="birch", wood2="mangrove", floor="polished_diorite", rug=("cyan_carpet", "light_gray_carpet"),
                     bed="cyan", banner="cyan", plant="potted_bamboo", chim="polished_andesite",
                     stone="smooth_stone"),
}
INTO = {"north": "south", "south": "north", "east": "west", "west": "east"}   # wall side -> facing into room


def _stair_flight(d, x0, z, yb, step, mat, fill):
    """5-step straight flight along x from x0 (step = +1 east / -1 west), rising from standing level yb to yb+5."""
    face = "east" if step > 0 else "west"
    for i in range(5):
        x = x0 + step * i
        d.set(x, yb + i, z, st(mat, face))
        for yy in range(yb, yb + i):
            d.set(x, yy, z, fill)
        if i in (1, 2, 3):
            d.set(x, yb + 4, z, AIR)


def tree(d, x, z, kind="oak", h=4):
    """One garden tree at (x, z): trunk + rounded crown of persistent leaves."""
    leaves = f"{kind}_leaves[distance=1,persistent=true,waterlogged=false]"
    for y in range(2, 2 + h):
        d.set(x, y, z, lg(f"{kind}_log"))
    top = 2 + h
    for dy, r in ((-2, 2), (-1, 2), (0, 1), (1, 0)):
        for a in range(-r, r + 1):
            for b in range(-r, r + 1):
                if abs(a) + abs(b) > r + (1 if r == 2 else 0):
                    continue
                xx, yy, zz = x + a, top + dy, z + b
                if d.bp.inside(xx, yy, zz) and d.air(xx, yy, zz):
                    d.set(xx, yy, zz, leaves)


def spruce_tree(d, x, z, h=6):
    leaves = "spruce_leaves[distance=1,persistent=true,waterlogged=false]"
    for y in range(2, 2 + h):
        d.set(x, y, z, lg("spruce_log"))
    for i, y in enumerate(range(4, 3 + h)):
        r = 2 if i % 2 == 0 and i < 3 else 1
        for a in range(-r, r + 1):
            for b in range(-r, r + 1):
                if (a or b) and abs(a) + abs(b) <= r + (r > 1) and d.air(x + a, y, z + b):
                    d.set(x + a, y, z + b, leaves)
    d.set(x, 2 + h, z, leaves)


def lamp_post(d, x, z, h=3):
    """One lamp post at (x, z)."""
    for y in range(2, 2 + h):
        d.set(x, y, z, f"{STY[d.pack]['wood']}_fence" if d.pack != "Neoterra" else "iron_bars")
    d.set(x, 2 + h, z, lant(False) if d.pack != "Neoterra" else "sea_lantern")


def bench(d, x, z, facing, n=2):
    """One outdoor bench of n seats starting at (x, z) (facing = the way people look)."""
    px, pz = D4[CW[facing]]
    for i in range(n):
        d.chair(x + px * i, 2, z + pz * i, OPP[facing], STY[d.pack]["wood"], sit=False)


def dormers(d, x1, z1, x2, z2, Y, axis, wallm, roofm, glass=None):
    """Gabled dormer windows along both eaves of a gable roof (part of the roof structure)."""
    if axis == "x":
        for x in range(x1 + 2, x2 - 1, 4):
            for z in (z1, z2):
                d.set(x, Y, z, glass or "glass_pane")
                for a in (x - 1, x + 1):
                    d.set(a, Y, z, wallm)
                d.set(x - 1, Y + 1, z, st(roofm, "east"))
                d.set(x, Y + 1, z, sl(roofm))
                d.set(x + 1, Y + 1, z, st(roofm, "west"))
    else:
        for z in range(z1 + 2, z2 - 1, 4):
            for x in (x1, x2):
                d.set(x, Y, z, glass or "glass_pane")
                for b in (z - 1, z + 1):
                    d.set(x, Y, b, wallm)
                d.set(x, Y + 1, z - 1, st(roofm, "south"))
                d.set(x, Y + 1, z, sl(roofm))
                d.set(x, Y + 1, z + 1, st(roofm, "north"))


def place_plan(d, rows, x0, y, z0, extra=()):
    """Lay one hand-drawn floor plan. Legend:
    ' ' leave, '.' keep clear | n s e w chair (backrest on that side) | t table (post) | T wood top slab (desk,
    counter, coffee table) | U stone top slab (worktop) | H bed head, f its foot | N nightstand + candle |
    D wardrobe | b bookcase (2 high, faces the room) | k crate | K crate + sack | Y crate + hay | h hay bale |
    W flour/wool sack | p potted plant | P pot on a shelf | V flower pot on a shelf | c candle on a shelf |
    A cake on a shelf | o stove | m smoker | u sink | x crafting table | g grindstone | a anvil | q stonecutter |
    z smithing table | F fletching table | C cartography table | E lectern | M loom | Z music box (note block) |
    r R rug colours | l lamp hanging from the ceiling above | L standing lamp | G planted bed | 1-9 extra[i-1]."""
    S = STY[d.pack]
    w, w2 = S["wood"], S["wood2"]
    D_, W_ = len(rows), len(rows[0])
    for r in rows:
        if len(r) != W_:
            raise ValueError(f"plan row width {len(r)} != {W_}: {r!r}")

    def facing(dx, dz):
        return "south" if dz == 0 else "north" if dz == D_ - 1 else "east" if dx == 0 else "west" if dx == W_ - 1 \
            else "south"
    for dz, row in enumerate(rows):
        for dx, ch in enumerate(row):
            x, z = x0 + dx, z0 + dz
            if ch in " .f":
                continue
            f = facing(dx, dz)
            if ch in "nsew":
                d.chair(x, y, z, {"n": "north", "s": "south", "e": "east", "w": "west"}[ch], w, sit=False)
            elif ch == "t":
                d.table(x, y, z, w, "post")
            elif ch == "T":
                d.set(x, y, z, sl(w, "top"))
            elif ch == "U":
                d.set(x, y, z, sl(S["stone"], "top"))
            elif ch == "H":
                foot = [(sd, (ddx, ddz)) for sd, (ddx, ddz) in D4.items()
                        if 0 <= dz + ddz < D_ and 0 <= dx + ddx < W_ and rows[dz + ddz][dx + ddx] == "f"]
                if not foot:
                    raise ValueError(f"bed head without foot at {dx},{dz}")
                d.bed(x, y, z, OPP[foot[0][0]], S["bed"])
                d.placed["beds"] -= 1                                 # furniture, not a hut requirement
            elif ch == "N":
                d.set(x, y, z, sl(w2, "top"))
                d.set(x, y + 1, z, "candle[candles=2,lit=false,waterlogged=false]")
            elif ch == "D":
                d.set(x, y, z, f"{w}_planks")
                d.set(x, y + 1, z, f"{w}_planks")
                d.set(x, y + 2, z, sl(w))
            elif ch == "b":
                for yy in (y, y + 1):
                    d.set(x, yy, z, f"chiseled_bookshelf[facing={f},slot_0_occupied=true,slot_1_occupied=true,"
                                    f"slot_2_occupied=false,slot_3_occupied=true,slot_4_occupied=false,"
                                    f"slot_5_occupied=true]")
            elif ch in "kKY":
                d.set(x, y, z, "barrel[facing=up,open=false]")
                if ch != "k":
                    d.set(x, y + 1, z, "white_wool" if ch == "K" else "hay_block[axis=y]")
            elif ch == "h":
                d.set(x, y, z, "hay_block[axis=y]")
            elif ch == "W":
                d.set(x, y, z, "white_wool")
                d.set(x, y + 1, z, "white_carpet")
            elif ch == "p":
                d.set(x, y, z, S["plant"])
            elif ch in "PVcA":
                d.set(x, y, z, sl(w2, "top"))
                d.set(x, y + 1, z, {"P": "decorated_pot[cracked=false,facing=north,waterlogged=false]",
                                    "V": "potted_" + flower(d, dx + dz), "A": CAKE,
                                    "c": "candle[candles=3,lit=false,waterlogged=false]"}[ch])
            elif ch == "o":
                d.set(x, y, z, f"furnace[facing={f},lit=true]")
            elif ch == "m":
                d.set(x, y, z, f"smoker[facing={f},lit=false]")
            elif ch == "u":
                d.set(x, y, z, "water_cauldron[level=3]")
            elif ch == "x":
                d.set(x, y, z, "crafting_table")
            elif ch == "g":
                d.set(x, y, z, f"grindstone[face=floor,facing={f}]")
            elif ch == "a":
                d.set(x, y, z, f"anvil[facing={CW[f]}]")
            elif ch == "q":
                d.set(x, y, z, f"stonecutter[facing={f}]")
            elif ch == "z":
                d.set(x, y, z, "smithing_table")
            elif ch == "F":
                d.set(x, y, z, "fletching_table")
            elif ch == "C":
                d.set(x, y, z, "cartography_table")
            elif ch == "E":
                d.set(x, y, z, f"lectern[facing={f},has_book=true,powered=false]")
            elif ch == "M":
                d.set(x, y, z, f"loom[facing={f}]")
            elif ch == "Z":
                d.set(x, y, z, "note_block[instrument=harp,note=0,powered=false]")
            elif ch in "rR":
                d.set(x, y, z, S["rug"][0 if ch == "r" else 1])
            elif ch == "l":
                c = next((yy for yy in range(y + 3, y + 12) if not d.air(x, yy, z)), None)
                if c is not None:
                    ly = max(y + 3, c - 3)
                    for yy in range(ly + 1, c):
                        d.set(x, yy, z, "chain[axis=y,waterlogged=false]")
                    d.set(x, ly, z, lant())
            elif ch == "L":
                d.set(x, y, z, f"{w}_fence" if d.pack != "Neoterra" else "iron_bars")
                d.set(x, y + 1, z, lant(False))
            elif ch == "G":
                d.set(x, y - 1, z, "grass_block[snowy=false]")
                d.set(x, y, z, flower(d, dx * 3 + dz))
            elif ch.isdigit():
                e = extra[int(ch) - 1]
                if isinstance(e, tuple):
                    d.set(x, y, z, e[0])
                    d.set(x, y + 1, z, e[1])
                else:
                    d.set(x, y, z, e)
            else:
                raise ValueError(f"unknown plan char {ch!r}")


def bld(d, x1, z1, x2, z2, n, door, plans, axis="x", roofkind="gable", tall=False, wall=None, glass=None,
        extra=(), ext=(), sign=None, roofitems=(), chimney=True, dormer=True, mwall=None, mroof=None, mlog=None,
        keep_roof=False, win=3, lower=None, deck=None, parapet=None):
    """Draw one add-on building and lay its hand-drawn plans. n storeys (pitch 5; a tall single storey has 8-high
    walls). Stairs are fixed: flight k rises along the north interior row from the west (k even) or along the
    south row from the east (k odd). door = (side, offset from x1/z1). ext = [(dx, y, dz, block)] relative to
    (x1, z1); sign = (dx, y, dz, facing, lines); roofitems = [(dx, dz, block)] on a flat roof."""
    S = STY[d.pack]
    P = d.pack
    y0 = 2
    salt = f"m{x1},{z1}"
    mwall = mwall or (d.vary(["smooth_sandstone", "white_terracotta", "calcite", "yellow_terracotta", "bricks"], salt)
                      if P == "Hearthwood" else d.vary(["white_concrete", "light_gray_concrete", "white_terracotta",
                                                        "quartz_block"], salt))
    mroof = mroof or d.vary({"Hearthwood": ["dark_prismarine", "brick", "mud_brick", "granite"],
                             "Cascadia": ["cobbled_deepslate", "dark_prismarine", "mangrove", "deepslate_tile"]}
                            .get(P, ["x"]), salt)
    mlog = mlog or d.vary(["stripped_spruce_log", "stripped_dark_oak_log", "spruce_log", "stripped_birch_log"], salt)
    H = 8 if tall else 4
    tops = []
    for k in range(n):
        yb = y0 + 5 * k
        yt = yb + H - 1
        if P == "Hearthwood":
            hw_body(d, x1, z1, x2, z2, yb, yt, wall=wall or ((lower or "bricks") if k == 0 and (n > 2 or lower)
                                                            else mwall),
                    base="stone_bricks" if k == 0 else "dark_oak_planks", floor=S["floor"] if k == 0 else None,
                    ceiling=None if tall else "dark_oak_planks")
        elif P == "Cascadia":
            cas_body(d, x1, z1, x2, z2, yb, yt, floor=S["floor"] if k == 0 else None, footing=k == 0,
                     ceiling=None if tall else "spruce_planks", logm=mlog)
            if wall and wall != "glass":
                for x, z in perim(x1, z1, x2, z2):                 # river-rock / plank-sided storey
                    if not (x in (x1, x2) and z in (z1, z2)):
                        for yy in range(yb + 1, yt + 1):
                            d.set(x, yy, z, wall)
            if lower and k == 0:
                for x, z in perim(x1, z1, x2, z2):
                    if not (x in (x1, x2) and z in (z1, z2)):
                        for yy in range(yb + 1, yt + 1):
                            d.set(x, yy, z, lower)
            if wall == "glass":
                for x, z in perim(x1, z1, x2, z2):
                    if not ((x - x1) % 3 == 0 and z in (z1, z2) or (z - z1) % 3 == 0 and x in (x1, x2)):
                        for yy in range(yb + 1, yt + 1):
                            d.set(x, yy, z, "glass")
        else:
            neo_body(d, x1, z1, x2, z2, yb, yt, wall=(lower if lower and k == 0 else wall or mwall),
                     floor=S["floor"] if k == 0 else None,
                     roof_=None)
            if not tall:
                d.fill(x1, yb + 4, z1, x2, yb + 4, z2, "light_gray_concrete")
                d.fill(x1 + 1, yb + 4, z1 + 1, x2 - 1, yb + 4, z2 - 1, "smooth_stone")
        tops.append(yb)
    ytop = (y0 + H) if tall else (y0 + 5 * n - 1)
    side, off = door
    if side in ("north", "south"):
        dx, dz = x1 + off, z1 if side == "north" else z2
    else:
        dx, dz = x1 if side == "west" else x2, z1 + off
    # window openings (structure): every third wall cell, two rows in a tall hall
    rows_w = [(yb + 1, yb + 2) for yb in tops] if not tall else [(3, 4), (6, 7)]
    for (ya, yb_) in rows_w:
        for x, z in perim(x1, z1, x2, z2):
            if x in (x1, x2) and z in (z1, z2) or ya < 5 and abs(x - dx) + abs(z - dz) <= 1 or wall == "glass":
                continue
            along = x - x1 if z in (z1, z2) else z - z1
            if P == "Neoterra":
                if along % 4 != 0:
                    d.set(x, ya, z, glass or "glass_pane")
                    d.set(x, yb_, z, glass or "glass_pane")
            elif along % win == win - 1 and (P != "Hearthwood" or "log" not in d.get(x, ya, z)):
                d.window(x, ya, z, x, yb_, z, glass)
    # door + transom + path
    for yy in (y0, y0 + 1, y0 + 2):
        d.set(dx, yy, dz, AIR)
    d.door(dx, y0, dz, INTO[side], S["wood"])
    d.set(dx, y0 + 2, dz, "glass_pane" if P != "Neoterra" else "white_concrete")
    ox, oz = D4[side]
    for i in range(1, 4):
        a, b = dx + ox * i, dz + oz * i
        if d.bp.inside(a, 1, b):
            d.set(a, 1, b, {"Hearthwood": "gravel", "Cascadia": "dirt_path", "Neoterra": "smooth_stone"}[P])
    # fixed stairs
    ix1, iz1, ix2, iz2 = x1 + 1, z1 + 1, x2 - 1, z2 - 1
    mat = {"Hearthwood": "dark_oak", "Cascadia": "spruce", "Neoterra": "smooth_quartz"}[P]
    fill = {"Hearthwood": "dark_oak_planks", "Cascadia": "spruce_planks", "Neoterra": "white_concrete"}[P]
    for k in range(n - 1):
        if k % 2 == 0:
            _stair_flight(d, ix1 + 1, iz1, tops[k], 1, mat, fill)
        else:
            _stair_flight(d, ix2 - 1, iz2, tops[k], -1, mat, fill)
    if len(plans) != n:
        raise ValueError(f"{len(plans)} plans for {n} storeys")
    for k, rows in enumerate(plans):
        if len(rows) != iz2 - iz1 + 1 or len(rows[0]) != ix2 - ix1 + 1:
            raise ValueError(f"plan {k} is {len(rows[0])}x{len(rows)}, interior {ix2 - ix1 + 1}x{iz2 - iz1 + 1}")
        place_plan(d, rows, ix1, tops[k], iz1, extra)
    for (ddx, yy, ddz, blk) in ext:
        d.set(x1 + ddx, yy, z1 + ddz, blk)
    if sign:
        sx_, sy_, sz_, sf, lines = sign
        d.sign(x1 + sx_, sy_, z1 + sz_, sf, lines, S["wood"], glow=P == "Neoterra",
               color="cyan" if P == "Neoterra" else "black")
    # roof
    if roofkind == "glass":
        if P == "Neoterra":
            d.flat(x1, z1, x2, z2, ytop + 1, "glass", "light_gray_concrete", "smooth_stone_slab")
            for x in range(x1, x2 + 1, 3):
                for z in range(z1, z2 + 1):
                    d.set(x, ytop + 1, z, "light_gray_concrete")
            return ytop + 1
        return glass_gable(d, x1, z1, x2, z2, ytop + 1, axis, S["wood"], "glass", 3, "glass_pane", oh=0)
    if P == "Neoterra" or roofkind == "flat":
        d.flat(x1, z1, x2, z2, ytop + 1, deck or "smooth_quartz", parapet or "white_concrete", "smooth_quartz_slab")
        for (ddx, ddz, blk) in roofitems:
            d.set(x1 + ddx, ytop + 2, z1 + ddz, blk)
        return ytop + 1
    gwall = mwall if P == "Hearthwood" else "spruce_planks"
    if roofkind == "hip":
        ridge = d.hip(x1, z1, x2, z2, ytop + 1, mroof + "_stairs", mroof + "_slab", 1)
        d.set((x1 + x2) // 2, ridge + 1, (z1 + z2) // 2, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    else:
        ridge = roof(d, x1, z1, x2, z2, ytop + 1, axis, mroof, mroof + "_slab", gwall, keep=keep_roof)
        if dormer:
            dormers(d, x1, z1, x2, z2, ytop + 1, axis, gwall, mroof, glass)
    if isinstance(chimney, tuple):                                 # stack at a hand-picked spot outside a wall
        cx, cz = chimney
        for yy in range(y0, ridge + 3):
            d.set(cx, yy, cz, S["chim"])
        d.set(cx, ridge + 3, cz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    elif chimney:                                                  # stack on the outside of a gable end
        if axis == "x":
            cx, cz, wx, wz, f = x2 + 1, (z1 + z2) // 2, x2, (z1 + z2) // 2, "west"
        else:
            cx, cz, wx, wz, f = (x1 + x2) // 2, z2 + 1, (x1 + x2) // 2, z2, "north"
        if d.bp.inside(cx, ridge + 3, cz):
            for yy in range(y0, ridge + 3):
                d.set(cx, yy, cz, S["chim"])
            d.set(cx, ridge + 3, cz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
            d.set(wx, y0, wz, f"campfire[facing={f},lit=true,signal_fire=false,waterlogged=false]")
            d.set(wx, y0 + 1, wz, S["chim"])
    return ridge


def bldL(d, L, n3, x1, z1, x2, z2, n, door, plans, *a, **kw):
    """An add-on that first goes up at level 3 with only n3 storeys and gets its full height at level 4."""
    k = n3 if L == 3 else n
    return bld(d, x1, z1, x2, z2, k, door, plans[:k], *a, **kw)


def grow(d, L, base):
    """Add the type's add-on buildings and site dressing for this level (hand-written per type and pack)."""
    fn = GROW.get((base, d.pack))
    if fn:
        fn(d, L)
    if L >= 5 and base in SHOP_TYPES:
        yard_wall(d)
    reskin(d)
    if L <= 3:
        plain(d)


GROW = {}
SHOP_TYPES = ("baker", "concretemixer", "cook", "cookery", "dyer", "florist", "glassblower")


def yard_wall(d):
    """L5: the finished complex gets a boundary along the back and sides of its yard (the street side stays
    open): a stone garden wall with coping (Hearthwood), a split-rail fence on log posts (Cascadia), a white
    planter wall with a clipped hedge (Neoterra). It runs round the outermost built cells and steps round
    anything already standing there (trees, posts, buildings), leaving gaps by doors."""
    bp = d.bp
    xs, zs = [], []
    for x, y, z, stt in bp.blocks():
        if y >= d.gy + 1 and stt != AIR and "substitution" not in stt:
            xs.append(x)
            zs.append(z)
    x1, x2, z1, z2 = min(xs), max(xs), min(zs), max(zs)
    cells = [(x1, z) for z in range(z1 + 4, z2 + 1)] + [(x, z2) for x in range(x1 + 1, x2)] + \
            [(x2, z) for z in range(z1 + 4, z2 + 1)]
    y = d.gy + 1
    for i, (x, z) in enumerate(cells):
        if not (d.air(x, y, z) and d.air(x, y + 1, z)) or "water" in d.get(x, d.gy, z):
            continue
        if any("door" in d.get(x + a, yy, z + b) for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)) for yy in (y, y + 1)):
            continue
        if d.pack == "Hearthwood":
            d.set(x, y, z, "mossy_stone_bricks" if (x * 7 + z * 3) % 5 == 0 else "stone_bricks")
            d.set(x, y + 1, z, sl("stone_brick"))
        elif d.pack == "Cascadia":
            post = (x + z) % 4 == 0 or (x, z) in ((x1, z2), (x2, z2))
            for yy in (y, y + 1):
                d.set(x, yy, z, lg("spruce_log") if post else "spruce_fence")
        else:
            d.set(x, y, z, "white_concrete")
            d.set(x, y + 1, z, "azalea_leaves[distance=1,persistent=true,waterlogged=false]")


def growth(base, pack):
    def reg(fn):
        GROW[(base, pack)] = fn
        return fn
    return reg


# ============================================================================================ PALETTE VARIETY
# Every building type gets its own roof / wall / timber / accent combination from its pack's family (stable per
# type via d.vary), so a street of one pack mixes slate, red tile and blue slate roofs, plaster, Cotswold stone
# and colour-washed walls, etc. Applied as a re-skin of the pack's base materials at the end of each design.
ROOF_SRC = {"Hearthwood": ("deepslate_tile",), "Cascadia": ("dark_oak", "spruce"), "Neoterra": ("smooth_quartz",)}
ROOF_FAM = {
    "Hearthwood": ["deepslate_tile", "dark_prismarine", "brick", "mud_brick", "granite", "deepslate_tile"],
    "Cascadia": ["cobbled_deepslate", "dark_prismarine", "mangrove", "spruce", "deepslate_tile", "dark_oak"],
    "Neoterra": ["smooth_quartz", "deepslate_tile", "cut_copper", "smooth_stone"],
}
FULL = {"deepslate_tile": "deepslate_tiles", "brick": "bricks", "mud_brick": "mud_bricks", "spruce": "spruce_planks",
        "dark_oak": "dark_oak_planks", "mangrove": "mangrove_planks", "smooth_stone": "smooth_stone",
        "cobbled_deepslate": "cobbled_deepslate", "dark_prismarine": "dark_prismarine", "granite": "granite",
        "cut_copper": "cut_copper", "smooth_quartz": "smooth_quartz"}
WALL_SRC = {"Hearthwood": "calcite", "Cascadia": "stripped_spruce_log", "Neoterra": "white_concrete"}
WALL_FAM = {
    "Hearthwood": ["calcite", "smooth_sandstone", "white_terracotta", "yellow_terracotta", "light_blue_terracotta",
                   "calcite"],
    "Cascadia": ["stripped_spruce_log", "stripped_dark_oak_log", "mangrove_planks", "birch_planks",
                 "stripped_spruce_log"],
    "Neoterra": ["white_concrete", "light_gray_concrete", "white_terracotta", "quartz_block", "white_concrete"],
}
TRIM_FAM = {"Hearthwood": ["dark_oak", "spruce", "oak", "dark_oak"]}
SHUTTER_FAM = {"Hearthwood": ["crimson", "warped", "spruce", "oak", "dark_oak"],
               "Cascadia": ["crimson", "spruce", "warped", "dark_oak", "birch"],
               "Neoterra": ["birch", "mangrove", "cherry", "birch"]}
ACCENT_FAM = {"Neoterra": ["cyan", "orange", "yellow", "lime", "magenta"],
              "Cascadia": ["red", "green", "yellow", "red"], "Hearthwood": ["red", "blue", "green", "yellow"]}


PAL = {   # (roof, wall, trim, shutter/door accent wood, accent colour) chosen per type so no two look alike
    "Hearthwood": {
        "cook": ("mud_brick", "yellow_terracotta", "oak", "crimson", "red"),
        "cookery": ("granite", "calcite", "spruce", "warped", "green"),
        "baker": ("brick", "calcite", "dark_oak", "crimson", "red"),
        "florist": ("deepslate_tile", "white_terracotta", "oak", "warped", "green"),
        "dyer": ("dark_prismarine", "light_blue_terracotta", "dark_oak", "spruce", "blue"),
        "glassblower": ("deepslate_tile", "smooth_sandstone", "spruce", "crimson", "yellow"),
        "concretemixer": ("spruce", "calcite", "dark_oak", "oak", "yellow"),
        "tavern": ("deepslate_tile", "calcite", "dark_oak", "crimson", "red"),
    },
    "Cascadia": {
        "cook": ("mangrove", "stripped_spruce_log", None, "crimson", "red"),
        "cookery": ("cobbled_deepslate", "stripped_dark_oak_log", None, "spruce", "yellow"),
        "baker": ("dark_oak", "birch_planks", None, "crimson", "red"),
        "florist": ("dark_prismarine", "stripped_spruce_log", None, "warped", "green"),
        "dyer": ("deepslate_tile", "mangrove_planks", None, "birch", "yellow"),
        "glassblower": ("cobbled_deepslate", "stripped_spruce_log", None, "crimson", "red"),
        "concretemixer": ("dark_prismarine", "stripped_dark_oak_log", None, "spruce", "yellow"),
        "tavern": ("spruce", "stripped_spruce_log", None, "crimson", "red"),
    },
    "Neoterra": {
        "cook": ("smooth_quartz", "white_concrete", None, "mangrove", "orange"),
        "cookery": ("smooth_stone", "light_gray_concrete", None, "birch", "cyan"),
        "baker": ("smooth_quartz", "white_terracotta", None, "cherry", "yellow"),
        "florist": ("cut_copper", "quartz_block", None, "birch", "lime"),
        "dyer": ("smooth_quartz", "white_concrete", None, "mangrove", "magenta"),
        "glassblower": ("cut_copper", "white_concrete", None, "cherry", "cyan"),
        "concretemixer": ("smooth_stone", "light_gray_concrete", None, "birch", "orange"),
        "tavern": ("smooth_quartz", "white_concrete", None, "birch", "cyan"),
    },
}


def palette(d):
    r, w, t, sh, ac = PAL[d.pack][d.req["base"]]
    return dict(roof=r, wall=w, trim=t or "dark_oak", shutter=sh, accent=ac)


def reskin(d):
    from blueprint import parse_state, format_state
    P = d.pack
    pal = palette(d)
    bp = d.bp
    src_roofs = ROOF_SRC[P]
    # topmost block of every column = the roof surface
    tops = {}
    for x in range(bp.sx):
        for z in range(bp.sz):
            for y in range(bp.sy - 1, d.gy, -1):
                if bp.get(x, y, z) != AIR:
                    tops[(x, z)] = y
                    break
    wsrc, wdst = WALL_SRC[P], pal["wall"]
    for (x, z), ytop in tops.items():
        for y in (ytop, ytop - 1):
            stt = bp.get(x, y, z)
            name, props = parse_state(stt)
            n = name.split(":")[1]
            for r in src_roofs:
                if n in (r + "_stairs", r + "_slab") and pal["roof"] != r:
                    bp.set(x, y, z, format_state("minecraft:" + pal["roof"] + n[len(r):], props), None)
                elif n == FULL.get(r) and P == "Neoterra" and y == ytop - 1:
                    bp.set(x, y, z, "minecraft:" + FULL[pal["roof"]], None)
    for x, y, z, stt in list(bp.blocks()):
        name, props = parse_state(stt)
        n = name.split(":")[1]
        new = None
        if n == wsrc and wdst != wsrc:
            new = format_state("minecraft:" + wdst, props if wdst.endswith("_log") else {})
        elif P == "Hearthwood" and pal["trim"] != "dark_oak" and "dark_oak" in n and "trapdoor" not in n \
                and (x, y, z) not in bp.tile_entities:
            new = format_state("minecraft:" + n.replace("dark_oak", pal["trim"]), props)
        elif n.endswith("_trapdoor") and n != "iron_trapdoor" and props.get("open") == "true" \
                and n != pal["shutter"] + "_trapdoor":
            new = format_state(f"minecraft:{pal['shutter']}_trapdoor", props)
        elif P == "Neoterra" and n in ("cyan_terracotta", "cyan_concrete") and pal["accent"] != "cyan":
            new = "minecraft:" + n.replace("cyan", pal["accent"])
        if new:
            bp.set(x, y, z, new, bp.tile_entities.get((x, y, z)))


# ============================================================================================ MATERIAL TIERS
# Levels 1-3 are built from common materials; the premium ones (quartz, copper, prismarine, sea lanterns, end
# rods, froglights, blackstone...) appear from level 4 when the complex is upgraded.
PLAIN = [("smooth_quartz_stairs", "polished_diorite_stairs"), ("quartz_stairs", "polished_diorite_stairs"),
         ("smooth_quartz_slab", "smooth_stone_slab"), ("quartz_slab", "smooth_stone_slab"),
         ("smooth_quartz", "smooth_stone"), ("quartz_block", "calcite"), ("quartz_pillar", "calcite"),
         ("chiseled_quartz_block", "calcite"), ("quartz_bricks", "calcite"),
         ("dark_prismarine_stairs", "deepslate_tile_stairs"), ("dark_prismarine_slab", "deepslate_tile_slab"),
         ("dark_prismarine", "deepslate_tiles"), ("prismarine_bricks", "stone_bricks"), ("prismarine", "stone_bricks"),
         ("cut_copper_stairs", "stone_brick_stairs"), ("cut_copper_slab", "smooth_stone_slab"),
         ("cut_copper", "smooth_stone"), ("sea_lantern", "glowstone"), ("pearlescent_froglight", "glowstone"),
         ("polished_blackstone_bricks", "polished_deepslate"), ("polished_blackstone", "polished_deepslate"),
         ("blackstone", "cobbled_deepslate"), ("iron_block", "smooth_stone"), ("shroomlight", "glowstone")]
FULLB = ("glowstone", "smooth_stone", "calcite", "deepslate_tiles", "stone_bricks", "polished_deepslate",
         "cobbled_deepslate")


def plain(d):
    from blueprint import parse_state, format_state
    bp = d.bp
    for x, y, z, stt in list(bp.blocks()):
        name, props = parse_state(stt)
        n = name.split(":")[1]
        if n == "end_rod":
            bp.set(x, y, z, "minecraft:" + ("lantern[hanging=true,waterlogged=false]" if props.get("facing") == "down"
                                            else "lantern[hanging=false,waterlogged=false]"), None)
            continue
        for a, b in PLAIN:
            if n == a:
                bp.set(x, y, z, format_state("minecraft:" + b, {} if b in FULLB else props),
                       bp.tile_entities.get((x, y, z)))
                break


# ---------------------------------------------------------------------------- the three add-on shapes
# SHED 11x7 (one room 9x5, door west), HOUSE 13x9 (rooms 11x7, door west, 2-3 storeys, chimney on the east gable),
# HALL 19x11 with 8-high walls (one hall 17x9, door north). Their exterior dressing is fixed relative to the
# shape: a lamp beside the door, the name sign, window boxes under the street-side windows.
def _box(dx, dz, y, facing, pot, wood):
    return [(dx, y, dz, td(wood, facing, "top")), (dx, y + 1, dz, pot)]


def SHED(d, x1, z1, plan, sign, extra=(), ext=(), **kw):
    P, w = d.pack, STY[d.pack]["wood"]
    e = list(ext)
    if P != "Neoterra":
        e += [(-1, 4, 2, "wall_torch[facing=west]")]
        e += _box(2, -1, 2, "north", "potted_" + flower(d, 1), w) + _box(8, -1, 2, "north", "potted_" + flower(d, 2), w)
    else:
        e += [(-1, 2, 1, "smooth_quartz"), (-1, 3, 1, "azalea"), (-1, 2, 5, "smooth_quartz"), (-1, 3, 5, "azalea")]
    return bld(d, x1, z1, x1 + 10, z1 + 6, 1, ("west", 3), [plan], "x", extra=extra, ext=e,
               sign=(-1, 3, 4, "west", sign), chimney=False, **kw)


def HOUSE(d, x1, z1, plans, sign, extra=(), ext=(), **kw):
    P, w = d.pack, STY[d.pack]["wood"]
    e = list(ext)
    if P != "Neoterra":
        e += [(-1, 4, 3, "wall_torch[facing=west]")]
        e += _box(2, -1, 2, "north", "potted_" + flower(d, 3), w) + _box(5, -1, 2, "north", "potted_" + flower(d, 4), w)
        e += _box(8, -1, 7, "north", "potted_" + flower(d, 5), w)
    else:
        e += [(-1, 2, 2, "smooth_quartz"), (-1, 3, 2, "flowering_azalea"), (-1, 2, 6, "smooth_quartz"),
              (-1, 3, 6, "flowering_azalea")]
    return bld(d, x1, z1, x1 + 12, z1 + 8, len(plans), ("west", 4), plans, "x", extra=extra, ext=e,
               sign=(-1, 3, 5, "west", sign), **kw)


def HALL(d, x1, z1, plan, sign, extra=(), ext=(), **kw):
    P, w = d.pack, STY[d.pack]["wood"]
    e = list(ext)
    if P != "Neoterra":
        e += [(8, 4, -1, "wall_torch[facing=north]"), (10, 4, -1, "wall_torch[facing=north]")]
        e += _box(2, -1, 2, "north", "potted_" + flower(d, 6), w) + _box(14, -1, 2, "north", "potted_" + flower(d, 7), w)
    else:
        e += [(7, 2, -1, "smooth_quartz"), (7, 3, -1, "flowering_azalea"), (11, 2, -1, "smooth_quartz"),
              (11, 3, -1, "flowering_azalea")]
    kw.setdefault("chimney", False)
    return bld(d, x1, z1, x1 + 18, z1 + 10, 1, ("north", 9), [plan], "x", tall=True, extra=extra, ext=e,
               sign=(12, 3, -1, "north", sign), **kw)


GLASSHOUSE = dict(wall="glass", roofkind="glass")


SOLAR = [(2, 2, "daylight_detector[inverted=false,power=0]"), (3, 2, "daylight_detector[inverted=false,power=0]"),
         (4, 2, "daylight_detector[inverted=false,power=0]"), (2, 3, "daylight_detector[inverted=false,power=0]"),
         (3, 3, "daylight_detector[inverted=false,power=0]"), (4, 3, "daylight_detector[inverted=false,power=0]")]


def GREEN(dxs, dz):
    return [(x, dz, "moss_block") for x in dxs] + [(x, dz - 1, "azalea") for x in dxs[::2]]


# ============================================================================================ SITE PIECES
# Each helper below draws ONE piece at the coordinates its caller passes; none of them looks for a place by itself.
# The complexes further down list every building, window box, lamp, sign, cart and tree by hand.
def put(d, items):
    """Explicit exterior dressing: [(x, y, z, block), ...] at absolute coordinates."""
    for x, y, z, b in items:
        d.set(x, y, z, b)


def wbox(x, z, facing, pot, wood="spruce", y=2):
    """One window box just outside a ground-floor window: a trapdoor sill with a potted flower on it."""
    return [(x, y, z, td(wood, facing, "top")), (x, y + 1, z, "potted_" + pot)]


def torch(x, y, z, facing):
    return [(x, y, z, f"wall_torch[facing={facing}]")]


def label(d, x, y, z, facing, lines, wood=None, color=None):
    """The building's name board at one spot beside its door."""
    P = d.pack
    d.sign(x, y, z, facing, lines, wood or STY[P]["wood"], glow=P == "Neoterra",
           color=color or ("cyan" if P == "Neoterra" else "black"))


def cart(d, x, z, along, load, wood="spruce"):
    """Hand cart whose bed starts at (x, z): 3 long along `along`, a load on it, wheels at the ends, a shaft."""
    dx, dz = (1, 0) if along == "x" else (0, 1)
    sx, sz = (0, 1) if along == "x" else (1, 0)
    for i in range(3):
        d.set(x + dx * i, 2, z + dz * i, sl(wood, "top"))
        d.set(x + dx * i, 3, z + dz * i, load)
    for i in (0, 2):
        for s, f in ((-1, "north" if along == "x" else "west"), (1, "south" if along == "x" else "east")):
            d.set(x + dx * i + sx * s, 2, z + dz * i + sz * s, td("dark_oak", f, "bottom", True))
    d.set(x + dx * 3, 2, z + dz * 3, f"{wood}_fence")


def pile(d, x1, z1, x2, z2, block, peak=None):
    """A heap of loose material over the given rectangle, optionally a second course on the cells in `peak`."""
    d.fill(x1, 2, z1, x2, 2, z2, block)
    for x, z in peak or ():
        d.set(x, 3, z, block)


def stall(d, x, z, facing, wood, colors, goods):
    """Market stall 3 wide starting at (x, z): counter (top slabs) with goods, posts at the back, wool canopy.
    `facing` = the side the customers stand on (north/south: stall runs along x; east/west: along z)."""
    along_x = facing in ("north", "south")
    dx, dz = (1, 0) if along_x else (0, 1)
    bx, bz = (0, -D4[facing][1]) if along_x else (-D4[facing][0], 0)
    for i in range(3):
        cx, cz = x + dx * i, z + dz * i
        d.set(cx, 2, cz, sl(wood, "top"))
        d.set(cx, 3, cz, goods[i % len(goods)])
        d.set(cx + bx, 5, cz + bz, colors[i % len(colors)])
        d.set(cx, 5, cz, colors[(i + 1) % len(colors)])
    for i in (0, 2):
        for y in (2, 3, 4):
            d.set(x + dx * i + bx, y, z + dz * i + bz, f"{wood}_fence")


def well(d, x, z, stone, roofm, post):
    """Village well centred on (x, z): stone ring, water, two posts, a little roof and a bucket chain."""
    for a in (-1, 0, 1):
        for b in (-1, 0, 1):
            d.set(x + a, 1, z + b, stone)
            if a or b:
                d.set(x + a, 2, z + b, stone)
    d.set(x, 1, z, "water")
    d.set(x, 0, z, stone)
    for a in (-1, 1):
        for y in (3, 4):
            d.set(x + a, y, z, post)
    for a in (-1, 0, 1):
        d.set(x + a, 5, z - 1, st(roofm, "south"))
        d.set(x + a, 5, z + 1, st(roofm, "north"))
        d.set(x + a, 5, z, sl(roofm))
    d.set(x, 4, z, "chain[axis=y,waterlogged=false]")


def picnic(d, x, z, wood, n=2):
    """Outdoor table `n` long along x starting at (x, z) with a bench on each long side (decor seating)."""
    for i in range(n):
        d.table(x + i, 2, z, wood, "slab")
        d.chair(x + i, 2, z - 1, "north", wood, sit=False)
        d.chair(x + i, 2, z + 1, "south", wood, sit=False)


def firepit(d, x, z, ring="cobblestone_slab"):
    d.set(x, 1, z, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for a, b in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        d.set(x + a, 1, z + b, ring.replace("_slab", "") if "slab" in ring else ring)


def woodpile(d, x1, x2, z, h=2, roofm="spruce"):
    """Stacked firewood against a wall along x (logs lying along z) with a slab lid."""
    for x in range(x1, x2 + 1):
        for y in range(2, 2 + h):
            d.set(x, y, z, lg("oak_log", "z"))
        d.set(x, 2 + h, z, sl(roofm))


def hoist(d, x, z, y, out, bale="hay_block[axis=y]"):
    """Sack hoist: beam pushed out from the gable at (x, y, z) two cells toward `out`, chain and a bale on it."""
    ox, oz = D4[out]
    for i in (1, 2):
        d.set(x + ox * i, y, z + oz * i, lg("stripped_spruce_log", "x" if ox else "z"))
    for yy in range(y - 2, y):
        d.set(x + ox * 2, yy, z + oz * 2, "chain[axis=y,waterlogged=false]")
    d.set(x + ox * 2, y - 3, z + oz * 2, bale)


def porch_lean(d, x1, x2, zf, zw, y, roofm, post, posts, gap=(), floor=None):
    """Lean-to porch along a north- or south-facing wall: front row zf, wall row zw (rows between are under
    it). Posts at the listed x, railing along the front except the `gap` cells, roof at y sloping out."""
    s = 1 if zw > zf else -1
    front = "south" if s > 0 else "north"
    for x in range(x1, x2 + 1):
        for z in range(min(zf, zw - s), max(zf, zw - s) + 1):
            if floor:
                d.set(x, 1, z, floor)
            d.set(x, y, z, sl(roofm, "top") if z != zf else st(roofm, front))
        if x in posts:
            for yy in range(2, y):
                d.set(x, yy, zf, lg(post) if post.endswith(("_log", "_wood")) else post)
        elif x not in gap:
            d.set(x, 2, zf, f"{STY[d.pack]['wood']}_fence")


def porch_lean_z(d, z1, z2, xf, xw, y, roofm, post, posts, gap=(), floor=None):
    """As porch_lean, along an east- or west-facing wall (front column xf, wall column xw)."""
    s = 1 if xw > xf else -1
    front = "east" if s > 0 else "west"
    for z in range(z1, z2 + 1):
        for x in range(min(xf, xw - s), max(xf, xw - s) + 1):
            if floor:
                d.set(x, 1, z, floor)
            d.set(x, y, z, sl(roofm, "top") if x != xf else st(roofm, front))
        if z in posts:
            for yy in range(2, y):
                d.set(xf, yy, z, lg(post) if post.endswith(("_log", "_wood")) else post)
        elif z not in gap:
            d.set(xf, 2, z, f"{STY[d.pack]['wood']}_fence")


def pavilion(d, x1, z1, x2, z2, h, posts, axis, roofm, post, floor=None, end=None):
    """Open-sided shed: posts at the listed (x, z), a beam ring at the top, gable roof. Returns ridge y."""
    for x, z in posts:
        for y in range(2, 2 + h):
            d.set(x, y, z, lg(post) if post.endswith(("_log", "_wood")) else post)
    for x, z in perim(x1, z1, x2, z2):
        d.set(x, 2 + h, z, lg("stripped_spruce_log" if d.pack != "Hearthwood" else "stripped_dark_oak_log",
                              "x" if z in (z1, z2) else "z"))
    if floor:
        d.fill(x1, 1, z1, x2, 1, z2, floor)
    return roof(d, x1, z1, x2, z2, 3 + h, axis, roofm, roofm + "_slab", end)


def canopy(d, x1, z1, x2, z2, y, posts, slab="smooth_stone_slab", post="light_gray_concrete", y0=2):
    """Flat canopy / pergola: a slab deck at y on slim columns (standing from y0) at the listed (x, z)."""
    for x, z in posts:
        for yy in range(y0, y):
            d.set(x, yy, z, post)
    d.fill(x1, y, z1, x2, y, z2, f"{slab}[type=bottom,waterlogged=false]")


def stack(d, x, z, top, mat, y0=2):
    """One free-standing chimney stack at (x, z) from y0 up to `top`, a smoking campfire cap on it."""
    for y in range(y0, top):
        d.set(x, y, z, mat)
    d.set(x, top, z, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")


def bed_colour(d, x1, z1, x2, z2, y, colour):
    """Re-dye the beds of one storey (x1..x2 / z1..z2 at standing level y) so stacked bedroom floors differ."""
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            stt = d.get(x, y, z)
            if stt.split("[")[0].endswith("_bed"):
                d.set(x, y, z, "minecraft:" + colour + "_bed[" + stt.split("[", 1)[1],
                      d.bp.tile_entities.get((x, y, z)))


def bed_row(d, cells, flower_i=0):
    """Flower / herb bed: grass with a plant on each of the listed (x, z) cells."""
    for i, (x, z) in enumerate(cells):
        d.set(x, 1, z, "grass_block[snowy=false]")
        d.set(x, 2, z, flower(d, i + flower_i))


# ============================================================================================ BAKER complexes
# Bakery round a market square.
# Hearthwood "market-square bakery": a little flour store and sack cart (L2), the baker's narrow three-storey
#   house, gable to the street (L3), a three-storey granary with a sack hoist on its gable (L4), a long tea-room
#   range with a striped awning and terrace tables, market stalls and a well on the square (L5).
# Cascadia "trail-town bakery": a tall mill shed with the millstone (L2), the baker's porch cabin (L3), a long
#   granary with a hay hoist (L4), a café with a deep plank porch, wool-canopied stalls and a well (L5).
# Neoterra "boulangerie lab": a banded flour silo (L2), a two-storey patisserie lab with a canopy (L3), the
#   baker's four-storey loft tower with an accent fin (L4), a long glass café with a canopy and a rooftop sign,
#   kiosks round a planted plaza (L5).
@growth("baker", "Hearthwood")
def _g_baker_hw(d, L):
    if L >= 2:                                                       # flour store + sack cart
        bld(d, 27, 4, 33, 10, 1, ("west", 3), [["WkWkW",
                                                 ".....",
                                                 "..l.h",
                                                 ".....",
                                                 "kWhWk"]], "z", chimney=False, dormer=False,
            mwall="smooth_sandstone", mroof="mud_brick")
        cart(d, 28, 13, "x", "white_wool", "dark_oak")
        put(d, torch(26, 4, 6, "west"))
        label(d, 26, 3, 9, "west", ["Flour"])
    if L >= 3:                                                       # baker's narrow three-storey house
        bldL(d, L, 2, 36, 3, 44, 11, 3, ("north", 7), [[".     .",
                                                 ".......",
                                                 "o..wTe.",
                                                 "U..wTe.",
                                                 "u......",
                                                 "...l..p",
                                                 "kYk.D.b"],
                                                ["       ",
                                                 "Hf...fH",
                                                 "N.....N",
                                                 ".......",
                                                 "..wT...",
                                                 "D.rrr..",
                                                 ".     ."],
                                                ["HN...NH",
                                                 "f.....f",
                                                 ".......",
                                                 "..l....",
                                                 "wTe....",
                                                 "D.....D",
                                                 "       "]], "z", chimney=(40, 12), dormer=True,
            mwall="calcite", mroof="brick", lower="bricks")
        put(d, wbox(38, 2, "north", "red_tulip", "crimson") + torch(42, 4, 2, "north")
            + [(41, 7, 2, "red_wall_banner[facing=north]")])
        label(d, 44, 3, 2, "north", ["Baker's", "House"], color="red")
    if L >= 4:                                                       # granary with a sack hoist
        bld(d, 44, 14, 52, 26, 3, ("west", 6), [[".     .",
                                                  ".......",
                                                  "WhW.WhW",
                                                  ".......",
                                                  "kKk.kKk",
                                                  ".......",
                                                  "hWh.hWh",
                                                  ".......",
                                                  "kYk.kYk",
                                                  ".......",
                                                  "WWh.hWW"],
                                                 ["       ",
                                                  ".......",
                                                  "hhh.hhh",
                                                  ".......",
                                                  "WWW.WWW",
                                                  "...l...",
                                                  "hWh.hWh",
                                                  ".......",
                                                  "KkK.KkK",
                                                  ".......",
                                                  ".     ."],
                                                 ["kYk.kYk",
                                                  ".......",
                                                  "WhW.WhW",
                                                  ".......",
                                                  "hhh.hhh",
                                                  "...l...",
                                                  "WWW.WWW",
                                                  ".......",
                                                  "kKk.kKk",
                                                  ".......",
                                                  "       "]], "z", chimney=False, dormer=False,
            mwall="stone_bricks", mroof="dark_prismarine", win=4)
        hoist(d, 48, 14, 19, "north", "white_wool")
        put(d, [(48, 17, 14, td("spruce", "north", "bottom", True))] + torch(43, 4, 19, "west"))
        label(d, 43, 3, 22, "west", ["Granary"])
    if L >= 5:                                                       # tea-room range with awning
        bld(d, 4, 30, 26, 36, 2, ("north", 11), [[".     ...........APAp",
                                                   ".....................",
                                                   ".wTe.wTe.wTe.wTe.wTe.",
                                                   "....l.........l......",
                                                   "UUUUoUUU...l...kYk.ZE"],
                                                  ["       ...b.b.b.....p",
                                                   ".....................",
                                                   "..wte..wte..wte..wte.",
                                                   "....l.........l......",
                                                   "p.D...D.....D...D...p"]], "x", chimney=(27, 33), dormer=True,
            mwall="white_terracotta", mroof="brick")
        awning(d, 5, 25, 29, 5, ("red_wool", "white_wool"), "north")
        label(d, 17, 3, 29, "north", ["Tea", "Room"], color="red")
        put(d, torch(14, 3, 29, "north"))
        for x in (6, 10, 19, 23):                                    # terrace tables
            picnic(d, x, 25, "oak", 2)
        stall(d, 28, 17, "south", "spruce", ("red_wool", "white_wool"), ("hay_block[axis=x]", "cake[bites=0]", "hay_block[axis=x]"))
        stall(d, 28, 25, "north", "spruce", ("yellow_wool", "white_wool"), ("honey_block", "hay_block[axis=x]", "decorated_pot[cracked=false,facing=north,waterlogged=false]"))
        stall(d, 38, 25, "north", "spruce", ("blue_wool", "white_wool"), ("melon", "pumpkin", "hay_block[axis=y]"))
        well(d, 35, 20, "stone_bricks", "dark_oak", "dark_oak_fence")
        for x, z in ((8, 40), (20, 41), (32, 40), (46, 38), (51, 41), (39, 42), (51, 31)):
            tree(d, x, z)
        lamp_post(d, 26, 13)
        lamp_post(d, 42, 28)
        bench(d, 30, 22, "east", 2)


@growth("baker", "Cascadia")
def _g_baker_cas(d, L):
    if L >= 2:                                                       # tall mill shed with the millstone
        bld(d, 26, 3, 34, 11, 1, ("west", 4), [["WkWhWkW",
                                                 ".......",
                                                 "h.....h",
                                                 "...g...",
                                                 "W..l..W",
                                                 ".......",
                                                 "kWkhkWk"]], "z", tall=True, chimney=False, dormer=False,
            mlog="stripped_spruce_log", mroof="mangrove", lower="cobblestone")
        put(d, torch(25, 4, 6, "west") + [(25, 2, 4, "hay_block[axis=y]"), (25, 2, 10, "white_wool")])
        put(d, wbox(28, 2, "north", "cornflower") + wbox(31, 2, "north", "poppy")          # mill eaves
            + [(28, 2, 12, "barrel[facing=up,open=false]"), (29, 2, 12, "barrel[facing=up,open=false]"),
               (29, 3, 12, "white_wool")])
        if L == 2:                                                   # (the L3 porch takes over this side)
            put(d, wbox(35, 5, "east", "allium") + wbox(35, 8, "east", "oxeye_daisy"))
        label(d, 25, 3, 9, "west", ["Mill"])
    if L >= 3:                                                       # baker's porch cabin
        bld(d, 37, 3, 45, 13, 2, ("west", 5), [[".     .",
                                                 ".......",
                                                 "o..wTe.",
                                                 "U..wTe.",
                                                 ".......",
                                                 "...l..p",
                                                 "D......",
                                                 ".......",
                                                 "kYk.bbp"],
                                                ["       ",
                                                 "Hf...fH",
                                                 "N.....N",
                                                 ".......",
                                                 "..rrr..",
                                                 "...l...",
                                                 "Hf...fH",
                                                 "N.....N",
                                                 "D.....D"]], "z", chimney=(46, 8), dormer=False,
            mlog="stripped_spruce_log", mroof="dark_oak")
        porch_lean_z(d, 5, 11, 35, 37, 6, "spruce", "spruce_log", (5, 11), gap=(7, 8, 9), floor="spruce_planks")
        put(d, torch(36, 4, 7, "west"))
        label(d, 36, 3, 10, "west", ["Baker"])
    if L >= 4:                                                       # long granary with hay hoist
        bld(d, 26, 16, 34, 30, 3, ("west", 7), [[".     .",
                                                  ".......",
                                                  "WhW.WhW",
                                                  ".......",
                                                  "kKk.kKk",
                                                  ".......",
                                                  ".......",
                                                  "hWh.hWh",
                                                  ".......",
                                                  "kYk.kYk",
                                                  ".......",
                                                  "...l...",
                                                  "WWh.hWW"],
                                                 ["       ",
                                                  ".......",
                                                  "hhh.hhh",
                                                  ".......",
                                                  "WWW.WWW",
                                                  "...l...",
                                                  ".......",
                                                  "hWh.hWh",
                                                  ".......",
                                                  "KkK.KkK",
                                                  ".......",
                                                  ".......",
                                                  ".     ."],
                                                 ["kYk.kYk",
                                                  ".......",
                                                  "WhW.WhW",
                                                  ".......",
                                                  "hhh.hhh",
                                                  "...l...",
                                                  ".......",
                                                  "WWW.WWW",
                                                  ".......",
                                                  "kKk.kKk",
                                                  ".......",
                                                  ".......",
                                                  "       "]], "z", chimney=False, dormer=False,
            mlog="stripped_dark_oak_log", mroof="cobbled_deepslate", wall="spruce_planks", win=4)
        hoist(d, 30, 16, 19, "north")
        put(d, torch(25, 4, 22, "west"))
        label(d, 25, 3, 25, "west", ["Granary"])
    if L >= 5:                                                       # cafe with a deep plank porch
        bld(d, 3, 30, 23, 37, 1, ("north", 10), [["pA.A.....l.....A.Ap",
                                                   "...................",
                                                   ".wTe..wTe...wTe...o",
                                                   "...................",
                                                   "..l....nnnnnn...l..",
                                                   "kYk.UUUUUUUUUU.hWhZ"]], "x", chimney=False, dormer=False,
            mlog="stripped_birch_log", mroof="mangrove")
        porch_lean(d, 3, 23, 27, 30, 6, "spruce", "spruce_log", (3, 8, 18, 23), gap=(12, 13, 14),
                   floor="spruce_planks")
        put(d, torch(12, 4, 29, "north") + torch(14, 4, 29, "north"))
        label(d, 16, 3, 29, "north", ["Cafe"])
        for x in (5, 19):
            d.table(x, 2, 28, "spruce", "slab")
            d.chair(x - 1, 2, 28, "west", "spruce", sit=False)
            d.chair(x + 1, 2, 28, "east", "spruce", sit=False)
        stall(d, 38, 18, "south", "spruce", ("red_wool", "white_wool"), ("hay_block[axis=x]", "hay_block[axis=x]", "cake[bites=0]"))
        stall(d, 44, 18, "south", "spruce", ("green_wool", "white_wool"), ("pumpkin", "melon", "pumpkin"))
        stall(d, 40, 26, "north", "spruce", ("yellow_wool", "brown_wool"), ("hay_block[axis=y]", "hay_block[axis=x]", "decorated_pot[cracked=false,facing=north,waterlogged=false]"))
        well(d, 47, 28, "cobblestone", "spruce", "spruce_fence")
        bld(d, 44, 34, 52, 42, 2, ("west", 4), [[".     .",                 # rooms over the square
                                                  ".......",
                                                  "Hf...fH",
                                                  ".....N.",
                                                  "Hf.....",
                                                  "...wTe.",
                                                  "k.D.D.k"],
                                                 ["       ",
                                                  "Hf...fH",
                                                  "N.....N",
                                                  "Hf...fH",
                                                  ".......",
                                                  "..l....",
                                                  "D.....D"]], "x", roofkind="hip", chimney=False, dormer=False,
            mlog="spruce_log", mroof="dark_prismarine", lower="cobblestone")
        put(d, torch(43, 4, 37, "west") + wbox(46, 33, "north", "allium") + wbox(49, 33, "north", "poppy")
            + wbox(53, 36, "east", "cornflower") + wbox(53, 39, "east", "oxeye_daisy")
            + [(47, 2, 43, "barrel[facing=up,open=false]"), (48, 2, 43, "barrel[facing=up,open=false]")])
        label(d, 43, 3, 40, "west", ["Rooms"])
        cart(d, 38, 34, "z", "hay_block[axis=y]")
        for x, z in ((38, 43), (27, 40), (6, 42), (51, 22), (51, 13)):
            spruce_tree(d, x, z)
        lamp_post(d, 36, 15)
        lamp_post(d, 36, 30)


@growth("baker", "Neoterra")
def _g_baker_neo(d, L):
    if L >= 2:                                                       # banded flour silo
        silo(d, 28, 6, 2, 12, "white_concrete", "cyan_concrete")
        for y in range(2, 14):
            d.set(28, y, 2, "ladder[facing=north,waterlogged=false]")
        put(d, [(26, 2, 10, "hopper[enabled=true,facing=down]"), (26, 3, 10, "smooth_stone_slab[type=bottom,"
                                                                                 "waterlogged=false]")])
        label(d, 30, 3, 2, "north", ["FLOUR"])
    if L >= 3:                                                       # two-storey patisserie lab
        bldL(d, L, 1, 3, 15, 21, 23, 2, ("north", 9), [[".     ....p..AVA.",
                                                  ".................",
                                                  "UUoUU..wTe..wTe.p",
                                                  ".................",
                                                  ".UUUU....l...AAA.",
                                                  ".................",
                                                  "kKk.x.mo.Z...kYkp"],
                                                 ["       ...bEb...p",
                                                  ".................",
                                                  "Hf.....wTe.....fH",
                                                  "N...............N",
                                                  "Hf....rrrrr....fH",
                                                  "........l........",
                                                  "D.wT.D.....D.Te.D"]], mwall="white_terracotta",
            roofitems=GREEN([1, 3, 5, 7, 9, 11, 13, 15], 7))
        canopy(d, 9, 12, 15, 14, 6, [(9, 12), (15, 12)])
        planter(d, 8, 14, 2)
        planter(d, 16, 14, 2)
        label(d, 14, 3, 14, "north", ["PATISSERIE"])
    if L >= 4:                                                       # baker's four-storey loft tower
        bld(d, 26, 14, 34, 22, 4, ("west", 4), [[".     .",
                                                  ".......",
                                                  "UoUu..b",
                                                  "......b",
                                                  "..wTe..",
                                                  "..wTe..",
                                                  "p.....p"],
                                                 ["       ",
                                                  "Hf...fH",
                                                  "N.....N",
                                                  ".......",
                                                  "..rrr..",
                                                  "D......",
                                                  ".     ."],
                                                 [".     .",
                                                  ".......",
                                                  "bb..E..",
                                                  ".......",
                                                  "wT...Te",
                                                  ".......",
                                                  "       "],
                                                 ["       ",
                                                  ".......",
                                                  "HN..bb.",
                                                  "f......",
                                                  "..wTe..",
                                                  "...l...",
                                                  "D.....D"]], mwall="white_concrete", lower="glass",
            roofitems=GREEN([1, 3, 5], 5))
        put(d, [(35, y, 18, "cyan_terracotta") for y in range(2, 23)]
            + [(25, 5, z, "smooth_stone_slab[type=bottom,waterlogged=false]") for z in (17, 18, 19)])
        label(d, 25, 3, 20, "west", ["LOFT"])
    if L >= 5:                                                       # long glass cafe
        bld(d, 38, 3, 48, 30, 1, ("west", 13), [["pAPA.APAp",
                                                  ".........",
                                                  ".wTe...wU",
                                                  ".......wU",
                                                  ".wTe...wU",
                                                  ".......wU",
                                                  ".wTe...wU",
                                                  "....l....",
                                                  ".........",
                                                  "..nnn....",
                                                  "..TTT...p",
                                                  "..sss....",
                                                  ".........",
                                                  "....l....",
                                                  "..nnn....",
                                                  "..TTT...p",
                                                  "..sss....",
                                                  ".........",
                                                  ".wTe.wTe.",
                                                  ".........",
                                                  ".wTe.wTe.",
                                                  "....l....",
                                                  ".........",
                                                  "UUUoUUu..",
                                                  ".........",
                                                  "kYk.Z.AAp"]], tall=True, wall="glass",
            roofitems=GREEN([2, 4, 6, 8], 26) + GREEN([2, 4, 6, 8], 3))
        canopy(d, 35, 8, 37, 24, 6, [(35, 8), (35, 12), (35, 20), (35, 24)])
        for tz in (10, 22):                                          # terrace tables under the canopy
            d.table(36, 2, tz, "birch", "slab", "smooth_quartz_slab")
            d.chair(36, 2, tz - 1, "north", "birch", sit=False)
            d.chair(36, 2, tz + 1, "south", "birch", sit=False)
        planter(d, 36, 14, 2)
        planter(d, 36, 18, 2)
        billboard(d, 40, 46, 16, 12, ["LUMEN", "CAFE"])
        stall(d, 26, 28, "north", "birch", ("yellow_concrete", "white_concrete"), ("hay_block[axis=x]", "cake[bites=0]", "decorated_pot[cracked=false,facing=north,waterlogged=false]"))
        stall(d, 31, 28, "north", "birch", ("white_concrete", "yellow_concrete"), ("hay_block[axis=x]", "honey_block", "hay_block[axis=x]"))
        for x, z in ((25, 38), (33, 40), (50, 36), (42, 40), (6, 36), (14, 40)):
            tree(d, x, z, "birch")
        for x in (24, 28, 32):
            planter(d, x, 33, 2)
        bench(d, 27, 35, "north", 3)
        lamp_post(d, 23, 26, 4)
        lamp_post(d, 36, 32, 4)


# ============================================================================================ CONCRETE MIXER complexes
# Industrial yards round the mixing basin.
# Hearthwood "lime & mortar works": walled aggregate bays (L2), a hipped two-storey works office (L3), a tall
#   mason's shed (L4), a five-storey flat-topped batching tower with a hopper and a conveyor gantry down to the
#   basin, plus a barrow yard (L5).
# Cascadia "cascade aggregate": a powder shed (L2), the porch office (L3), a tall repair shop (L4), a five-storey
#   gabled hopper tower with a plank chute, gravel heaps and an ore cart (L5).
# Neoterra "NEOCRETE": a banded powder silo and bays (L2), a two-storey glass HQ (L3), a two-storey materials lab
#   (L4), a six-storey batch tower, a row of silos and a conveyor bridge (L5).
CMX = ["white_concrete_powder", "light_gray_concrete_powder", "gray_concrete_powder", "sand", "gravel"]
# plan digits 6-8 with extra=CMX + BINS: a filled bin (barrel heaped with powder / sand / gravel)
BINS = [("barrel[facing=up,open=false]", c) for c in ("white_concrete_powder", "sand", "gravel")]


def bays(d, x1, z, n, w, wall, mats):
    """A row of n open-fronted material bays starting at x1 (each w wide inside), back wall at z, side walls
    2 high running 3 toward the street (z-3), each bay heaped with its material."""
    x = x1
    for i in range(n + 1):
        for zz in range(z - 3, z + 1):
            for y in (2, 3):
                d.set(x + i * (w + 1), y, zz, wall)
    for i in range(n):
        a = x1 + 1 + i * (w + 1)
        for xx in range(a, a + w):
            for y in (2, 3):
                d.set(xx, y, z, wall)
        pile(d, a, z - 2, a + w - 1, z - 1, mats[i % len(mats)], [(a + w // 2, z - 1)])


def gantry(d, x1, x2, z, y, post, deck):
    """Conveyor gantry along x at height y from x1 to x2: a slab deck on posts every 3 cells."""
    for x in range(min(x1, x2), max(x1, x2) + 1):
        d.set(x, y, z, f"{deck}[type=bottom,waterlogged=false]")
        if (x - x1) % 3 == 0:
            for yy in range(2, y):
                d.set(x, yy, z, post)


@growth("concretemixer", "Hearthwood")
def _g_conc_hw(d, L):
    if L >= 2:                                                       # walled aggregate bays
        bays(d, 27, 8, 3, 2, "cobblestone", ["sand", "gravel", "white_concrete_powder"])
        put(d, [(37, 2, 3, "barrel[facing=up,open=false]"), (37, 2, 4, "barrel[facing=up,open=false]"),
                (37, 3, 3, "white_concrete_powder")])
    if L >= 3:                                                       # hipped works office
        bld(d, 40, 3, 48, 11, 2, ("west", 4), [[".     .",
                                                 ".......",
                                                 "b.TTT.C",
                                                 ".......",
                                                 "...s...",
                                                 "wT...Ep",
                                                 "kYk.k.D"],
                                                ["       ",
                                                 "Hf...fH",
                                                 "N.....N",
                                                 ".......",
                                                 "Hf...fH",
                                                 "N..l..N",
                                                 "D.....D"]], "x", roofkind="hip", chimney=(49, 7), dormer=False,
            mwall="calcite", mroof="brick", lower="stone_bricks")
        put(d, torch(39, 4, 6, "west") + wbox(39, 5, "west", "poppy", "oak") + wbox(39, 11, "west", "dandelion", "oak"))
        put(d, wbox(42, 2, "north", "red_tulip", "oak") + wbox(45, 2, "north", "allium", "oak"))   # street windows
        label(d, 39, 3, 9, "west", ["Works", "Office"])
    if L >= 4:                                                       # tall mason's shed
        bld(d, 3, 26, 23, 32, 1, ("north", 10), [["qqq.zgz..l..aga.qqq",
                                                   "...................",
                                                   "..UUUU.......UUUU..",
                                                   "..s..s.......s..s..",
                                                   "k1k.k2k.x.Y.k3k.k4k"]], "x", tall=True, chimney=False,
            dormer=False, mwall="stone_bricks", mroof="mud_brick", extra=CMX)
        put(d, torch(12, 4, 25, "north") + torch(14, 4, 25, "north"))
        # under the eaves: window boxes, a banker stonecutter and grindstone by the door, lime barrels on the
        # west end, a rain butt and more barrels along the back, a barrel by the east gable
        put(d, wbox(5, 25, "north", "poppy", "oak") + wbox(20, 25, "north", "cornflower", "oak") +
            [(8, 2, 25, "stonecutter[facing=north]"), (18, 2, 25, "grindstone[face=floor,facing=north]"),
             (2, 2, 28, "barrel[facing=up,open=false]"), (2, 3, 28, "barrel[facing=up,open=false]"),
             (2, 2, 29, "barrel[facing=up,open=false]"), (6, 2, 33, "water_cauldron[level=3]"),
             (16, 2, 33, "barrel[facing=up,open=false]"), (17, 2, 33, "barrel[facing=up,open=false]"),
             (24, 2, 30, "barrel[facing=up,open=false]")])
        label(d, 16, 3, 25, "north", ["Mason's", "Shed"])
        cart(d, 6, 36, "x", "gravel", "oak")
    if L >= 5:                                                       # batching tower with hopper + gantry
        bld(d, 28, 15, 36, 23, 5, ("west", 4), [[".     .",
                                                  ".......",
                                                  "1k2.3k4",
                                                  ".......",
                                                  "....l..",
                                                  ".......",
                                                  "kYk.kKk"],
                                                 ["       ",                # sand & gravel bins
                                                  ".......",
                                                  "7k7.8k8",
                                                  ".......",
                                                  "8k7.7k8",
                                                  "...l...",
                                                  ".     ."],
                                                 [".     .",                # powder sacks and bins
                                                  ".......",
                                                  "kKk.kYk",
                                                  ".......",
                                                  "6k6.KkK",
                                                  "....l..",
                                                  "       "],
                                                 ["       ",
                                                  ".......",
                                                  "Hf...fH",
                                                  "N.....N",
                                                  "...l...",
                                                  "D......",
                                                  ".     ."],
                                                 ["bE...C.",
                                                  ".......",
                                                  ".......",
                                                  "..wTe..",
                                                  "...l...",
                                                  "k.....k",
                                                  "       "]], "x", roofkind="flat", chimney=False, dormer=False,
            mwall="stone_bricks", mroof="brick", lower="cobblestone", extra=CMX + BINS, deck="stone_bricks",
            parapet="cobblestone_wall",
            roofitems=[(3, 3, "hopper[enabled=true,facing=down]"), (4, 3, "hopper[enabled=true,facing=down]"),
                       (3, 4, "hopper[enabled=true,facing=down]"), (4, 4, "hopper[enabled=true,facing=down]"),
                       (6, 6, "lightning_rod[facing=up,powered=false,waterlogged=false]")])
        gantry(d, 24, 27, 18, 7, "oak_fence", "smooth_stone_slab")
        put(d, torch(27, 4, 18, "west"))
        label(d, 27, 3, 21, "west", ["Batching", "Tower"])
        bays(d, 38, 32, 4, 3, "stone_bricks", ["gravel", "sand", "cobblestone", "light_gray_concrete_powder"])
        for x, z in ((8, 40), (20, 41), (50, 16), (50, 40)):
            tree(d, x, z)
        cart(d, 30, 27, "x", "white_concrete_powder", "oak")
        lamp_post(d, 26, 13)
        lamp_post(d, 37, 26)


@growth("concretemixer", "Cascadia")
def _g_conc_cas(d, L):
    if L >= 2:                                                       # powder shed
        bld(d, 24, 3, 30, 9, 1, ("west", 3), [["1k2k3",
                                                ".....",
                                                "...k4",
                                                "..l..",
                                                "4k5k1"]], "z", chimney=False, dormer=False,
            mlog="stripped_spruce_log", mroof="dark_prismarine", lower="cobblestone", extra=CMX)
        put(d, torch(23, 4, 5, "west"))
        label(d, 23, 3, 8, "west", ["Powder"])
    if L >= 3:                                                       # porch office
        bld(d, 24, 13, 32, 21, 2, ("west", 4), [[".     .",
                                                  ".......",
                                                  "E..wTe.",
                                                  ".......",
                                                  "..TTT..",
                                                  "..s.s..",
                                                  "kYk.C.b"],
                                                 ["       ",
                                                  "Hf...fH",
                                                  "N.....N",
                                                  "Hf...fH",
                                                  ".......",
                                                  "D.l...D",
                                                  "k.....k"]], "z", chimney=(28, 22), dormer=False,
            mlog="stripped_dark_oak_log", mroof="mangrove")
        porch_lean_z(d, 14, 20, 22, 24, 6, "spruce", "spruce_log", (14, 20), gap=(16, 17, 18))
        put(d, torch(23, 4, 16, "west") + wbox(33, 15, "east", "cornflower") + wbox(33, 18, "east", "oxeye_daisy"))
        label(d, 23, 3, 19, "west", ["Office"])
    if L >= 4:                                                       # tall repair shop
        bld(d, 3, 28, 23, 34, 1, ("north", 10), [["aga.z.z...l...q.q.q",
                                                   "...................",
                                                   "..UUUU...h...UUUU..",
                                                   "..s..s.........s..s",
                                                   "k1k.k2k.YkY.k3k.k4k"]], "x", tall=True, chimney=(24, 31),
            dormer=False, mlog="spruce_log", mroof="cobbled_deepslate", lower="cobblestone", extra=CMX)
        put(d, torch(12, 4, 27, "north") + torch(14, 4, 27, "north"))
        # under the eaves: window boxes, a saw horse and a grindstone out front, oil barrels at the west end,
        # a rain butt and a stack of barrels behind, a chopping block by the east chimney
        put(d, wbox(5, 27, "north", "cornflower") + wbox(20, 27, "north", "poppy") +
            [(8, 2, 27, "grindstone[face=floor,facing=north]"), (17, 2, 27, sl("spruce", "top")),
             (18, 2, 27, sl("spruce", "top")), (2, 2, 30, "barrel[facing=up,open=false]"),
             (2, 3, 30, "barrel[facing=up,open=false]"), (2, 2, 31, "barrel[facing=up,open=false]"),
             (6, 2, 35, "water_cauldron[level=3]"), (15, 2, 35, "barrel[facing=up,open=false]"),
             (16, 2, 35, "barrel[facing=up,open=false]"), (24, 2, 33, lg("stripped_oak_log"))])
        label(d, 16, 3, 27, "north", ["Repair", "Shop"])
    if L >= 5:                                                       # gabled hopper tower + chute
        bld(d, 37, 3, 45, 11, 5, ("west", 4), [[".     .",
                                                 ".......",
                                                 "1k1.2k2",
                                                 ".......",
                                                 "3k3.l..",
                                                 ".......",
                                                 "kYk.kYk"],
                                                ["       ",
                                                 ".......",
                                                 "Hf...fH",
                                                 "N.....N",
                                                 "...l...",
                                                 "D......",
                                                 ".     ."],
                                                [".     .",                 # bin floor
                                                 ".......",
                                                 "6k8.7k6",
                                                 ".......",
                                                 "7k6.8k7",
                                                 "...l...",
                                                 "       "],
                                                ["       ",                 # sack loft
                                                 ".......",
                                                 "kKk.kYk",
                                                 ".......",
                                                 "KkK.6k8",
                                                 "....l..",
                                                 ".     ."],
                                                ["E.b...C",
                                                 ".......",
                                                 "..wTe..",
                                                 ".......",
                                                 "...l...",
                                                 "k.....k",
                                                 "       "]], "z", chimney=False, dormer=False,
            mlog="stripped_dark_oak_log", mroof="dark_prismarine", lower="cobblestone", extra=CMX + BINS)
        for i in range(8):                                           # plank chute stepping down to the yard
            x, y = 46 + i // 2, 16 - i
            if d.bp.inside(x, y, 7):
                d.set(x, y, 7, st("spruce", "west"))
        for y in range(2, 9):
            d.set(49, y, 7, lg("spruce_log"))
        put(d, torch(36, 4, 6, "west"))
        label(d, 36, 3, 9, "west", ["Hopper", "Tower"])
        pile(d, 48, 9, 51, 12, "gravel", [(49, 10), (50, 10), (49, 11), (50, 11)])
        pile(d, 40, 15, 44, 17, "sand", [(41, 16), (42, 16), (43, 16)])
        cart(d, 36, 22, "z", "cobblestone")
        for x, z in ((8, 41), (20, 40), (32, 42), (50, 30), (44, 42)):
            spruce_tree(d, x, z)
        lamp_post(d, 34, 13)
        lamp_post(d, 34, 25)


@growth("concretemixer", "Neoterra")
def _g_conc_neo(d, L):
    if L >= 2:                                                       # banded powder silo + bays
        silo(d, 24, 7, 2, 10, "white_concrete", "cyan_concrete")
        for y in range(2, 12):
            d.set(24, y, 3, "ladder[facing=north,waterlogged=false]")
        bays(d, 27, 9, 2, 3, "light_gray_concrete", ["white_concrete_powder", "gray_concrete_powder"])
    if L >= 3:                                                       # two-storey glass HQ
        bld(d, 38, 3, 48, 11, 2, ("west", 6), [[".     .bE",
                                                 ".........",
                                                 "..TTT...C",
                                                 "...s.....",
                                                 ".wTe.wTe.",
                                                 ".........",
                                                 "kYk.x.kYk"],
                                                ["       HN",
                                                 ".......f.",
                                                 "Hf.......",
                                                 "N...wTe..",
                                                 ".........",
                                                 "Hf.l....p",
                                                 "N.....D.D"]], mwall="light_gray_concrete", lower="glass",
            roofitems=SOLAR + [(x, 6, "daylight_detector[inverted=false,power=0]") for x in (2, 3, 4, 6, 7, 8)])
        put(d, [(37, 5, z, "smooth_stone_slab[type=bottom,waterlogged=false]") for z in (8, 9, 10)])
        label(d, 37, 3, 11, "west", ["NEOCRETE", "HQ"])
    if L >= 4:                                                       # two-storey materials lab
        bld(d, 3, 25, 23, 31, 2, ("north", 10), [[".     ...l.........",
                                                   "...................",
                                                   "q.q.UUUU...UUUU.x.z",
                                                   "....s..s...s..s....",
                                                   "k1k.k2k.E.C.k3k.k4k"],
                                                  ["       ..b.b.b.b...",
                                                   "...................",
                                                   "Hf..wTe.....wTe..fH",
                                                   "N.................N",
                                                   "Hf....D.l.D......fH"]], mwall="white_concrete", extra=CMX,
            roofitems=GREEN([1, 3, 5, 7, 9, 11, 13, 15, 17], 5))
        canopy(d, 10, 22, 16, 24, 6, [(10, 22), (16, 22)])
        label(d, 15, 3, 24, "north", ["MATERIALS", "LAB"])
    if L >= 5:                                                       # six-storey batch tower, silos, bridge
        bld(d, 26, 14, 34, 22, 6, ("west", 4), [[".     .",
                                                  ".......",
                                                  "1k2.3k4",
                                                  ".......",
                                                  "....l..",
                                                  ".......",
                                                  "kYk.kKk"],
                                                 ["       ",
                                                  ".......",
                                                  "E.b.b.C",
                                                  ".......",
                                                  "wT...Te",
                                                  ".......",
                                                  ".     ."],
                                                 [".     .",                # powder store: filled bins
                                                  ".......",
                                                  "6k7.k8k",
                                                  ".......",
                                                  "8k6.7k6",
                                                  "...l...",
                                                  "       "],
                                                 ["       ",
                                                  ".......",
                                                  "kKk.kYk",
                                                  ".......",
                                                  "5555.55",
                                                  ".......",
                                                  ".     ."],
                                                 [".     .",
                                                  ".......",
                                                  "Hf...fH",
                                                  "N.....N",
                                                  "...l...",
                                                  "D.....D",
                                                  "       "],
                                                 ["       ",
                                                  ".......",
                                                  "bE...C.",
                                                  ".......",
                                                  "..wTe..",
                                                  "...l...",
                                                  "k.....k"]], mwall="light_gray_concrete", lower="glass",
            extra=CMX + BINS)
        put(d, [(30, y, 13, "cyan_terracotta") for y in range(2, 33)])
        billboard(d, 27, 33, 18, 33, ["NEOCRETE"])
        label(d, 25, 3, 20, "west", ["BATCH"])
        for cx in (40, 46):                                           # silo row beside the tower
            silo(d, cx, 18, 2, 14, "white_concrete", "cyan_concrete")
        silo(d, 46, 26, 2, 10, "white_concrete", "cyan_concrete")
        gantry(d, 35, 37, 18, 12, "light_gray_concrete", "smooth_stone_slab")
        for x, z in ((8, 38), (18, 40), (50, 10), (50, 20)):
            tree(d, x, z, "birch")
        lamp_post(d, 24, 26, 4)
        lamp_post(d, 36, 24, 4)


# ============================================================================================ COOK complexes
# Restaurant: a street range of service buildings, a banquet / mess hall, and guest rooms.
# Hearthwood "coaching restaurant": pantry + staff house in a street range east of the inn (L2/L3), a tall
#   gable-to-court banquet hall (L4) that becomes an L with a garden-room wing, plus a four-storey hipped guest
#   tower and an orchard terrace (L5).
# Cascadia "logging-camp cookhouse": a sod-roofed river-rock root cellar (L2), a long two-storey bunkhouse
#   (L3), a wide mess hall with a deep front porch (L4), a three-storey hipped lodge and a stone smokehouse
#   round a fire-pit yard (L5).
# Neoterra "sky restaurant": cold-store box (L2), staff block with a green roof (L3), a glass dining pavilion
#   with roof terrace (L4), a five-storey hotel tower with a rooftop sign and a fountain plaza (L5).
@growth("cook", "Hearthwood")
def _g_cook_hw(d, L):
    if L >= 2:                                                       # pantry on the street
        bld(d, 27, 3, 35, 9, 1, ("north", 4), [["Yk...kK",
                                                 ".......",
                                                 "W.UAU.W",
                                                 "...l...",
                                                 "kKk.hWk"]], "x", chimney=False, dormer=False,
            mwall="smooth_sandstone", mroof="brick")
        put(d, wbox(29, 2, "north", "red_tulip", "crimson") + torch(30, 4, 2, "north"))
        label(d, 32, 3, 2, "north", ["Pantry"])
    if L >= 3:                                                       # staff house closing the street range
        bldL(d, L, 1, 38, 3, 50, 11, 2, ("north", 9), [[".     ....b",
                                                  "o.........b",
                                                  "m..wte.....",
                                                  "U..wte..l..",
                                                  "u..........",
                                                  "......wTe..",
                                                  "kYk...p..Dp"],
                                                 ["       HNH.",
                                                  ".......f.f.",
                                                  "Hf.......fH",
                                                  "N..rrrr...N",
                                                  "Hf.......fH",
                                                  "...l.......",
                                                  "kD.....D..k"]], "x", chimney=(51, 7), dormer=True,
            mwall="white_terracotta", mroof="granite")
        put(d, wbox(40, 2, "north", "poppy", "crimson") + wbox(43, 2, "north", "oxeye_daisy", "crimson")
            + torch(48, 4, 2, "north"))
        label(d, 45, 3, 2, "north", ["Staff", "House"])
    if L >= 4:                                                       # banquet hall, gable end to the court
        bld(d, 38, 15, 50, 37, 1, ("west", 11), [["PcP.bZb.PcP",
                                                   "...........",
                                                   "...n...n...",
                                                   "..wte.wte..",
                                                   "..wte.wte..",
                                                   "..wte.wte..",
                                                   "..wtelwte..",
                                                   "..wte.wte..",
                                                   "..wte.wte..",
                                                   "..wte.wte..",
                                                   "..wte.wte..",
                                                   "..wtelwte..",
                                                   "..wte.wte..",
                                                   "...s...s...",
                                                   "...........",
                                                   "...........",
                                                   "..l.....l..",
                                                   "..TTTTTTT..",
                                                   "..sssssss..",
                                                   "...........",
                                                   "pAPA...APAp"]], "z", tall=True, chimney=(44, 38),
            dormer=False, mwall="calcite", mroof="dark_prismarine", lower="bricks")
        put(d, torch(37, 4, 25, "west") + torch(37, 4, 27, "west")
            + [(37, 7, 21, "red_wall_banner[facing=west]"), (37, 7, 31, "red_wall_banner[facing=west]")])
        # window boxes along both long walls (the west ones north of where the L5 garden room joins),
        # a cider barrel at the back corner
        put(d, wbox(37, 17, "west", "red_tulip", "crimson") + wbox(37, 20, "west", "oxeye_daisy", "crimson")
            + wbox(51, 20, "east", "poppy", "crimson") + wbox(51, 26, "east", "cornflower", "crimson")
            + wbox(51, 32, "east", "allium", "crimson") + [(51, 2, 36, "barrel[facing=up,open=false]")])
        label(d, 37, 3, 28, "west", ["Banquet", "Hall"])
    if L >= 5:                                                       # garden-room wing makes the hall an L
        bld(d, 26, 29, 38, 37, 1, ("north", 6), [["pV.......Vp",
                                                   "...........",
                                                   ".wte...wte.",
                                                   ".wte.l.wte.",
                                                   "...........",
                                                   "...TTTTT...",
                                                   "Z..psssp..b"]], "x", tall=True, chimney=False, dormer=False,
            mwall="smooth_sandstone", mroof="dark_prismarine", keep_roof=True)
        put(d, wbox(28, 28, "north", "pink_tulip", "crimson") + wbox(36, 28, "north", "cornflower", "crimson")
            + torch(31, 4, 28, "north") + torch(33, 4, 28, "north"))
        put(d, wbox(25, 31, "west", "pink_tulip", "crimson") + wbox(25, 34, "west", "allium", "crimson")
            + [(40, 2, 38, "water_cauldron[level=3]"), (41, 2, 38, "barrel[facing=up,open=false]")])
        bench(d, 30, 38, "south", 2)                                  # bench under the eaves facing the orchard
        label(d, 34, 3, 28, "north", ["Garden", "Room"])
        bld(d, 26, 14, 34, 22, 4, ("west", 4), [[".     .",              # guest tower
                                                  ".......",
                                                  "..T...p",
                                                  "..Te...",
                                                  "..T....",
                                                  "wTe...p",
                                                  "p.kYk.b"],
                                                 ["       ",
                                                  "Hf.l...",
                                                  "N......",
                                                  "Hf..wT.",
                                                  ".......",
                                                  "D.rrr..",
                                                  ".     ."],
                                                 [".     .",
                                                  ".......",
                                                  "Hf...fH",
                                                  "N.....N",
                                                  "...l...",
                                                  "D.wT..D",
                                                  "       "],
                                                 ["       ",
                                                  ".......",
                                                  "H....bb",
                                                  "f......",
                                                  "N.wTe..",
                                                  "...l...",
                                                  "D.p.p.D"]], "x", roofkind="hip", chimney=False, dormer=False,
            mwall="calcite", mroof="brick", lower="bricks")
        put(d, torch(25, 4, 17, "west") + torch(25, 4, 19, "west"))
        label(d, 25, 3, 20, "west", ["Guest", "Rooms"])
        for x, z in ((6, 45), (16, 47), (46, 44), (52, 30)):         # orchard and shade trees
            tree(d, x, z)
        for x in (27, 32):                                           # terrace tables before the garden room
            picnic(d, x, 42, "oak", 2)
        d.fill(25, 1, 40, 37, 1, 44, "stone_bricks")
        canopy(d, 25, 40, 37, 44, 6, [(25, 40), (31, 40), (37, 40), (25, 44), (31, 44), (37, 44)],
               "oak_slab", "oak_fence")                                # vine pergola over the terrace
        for x in (26, 28, 30, 32, 34, 36):
            d.set(x, 5, 40, "vine[east=false,north=false,south=false,up=true,west=false]")
        well(d, 30, 26, "stone_bricks", "dark_oak", "dark_oak_fence")
        lamp_post(d, 24, 40)
        lamp_post(d, 38, 40)
        bench(d, 9, 40, "north", 3)
        bench(d, 18, 42, "north", 3)


@growth("cook", "Cascadia")
def _g_cook_cas(d, L):
    if L >= 2:                                                       # sod-roofed river-rock root cellar
        bld(d, 30, 4, 36, 12, 1, ("west", 4), [["kYhKk",
                                                 ".....",
                                                 "Y...K",
                                                 ".....",
                                                 "W.l.k",
                                                 ".....",
                                                 "kKhYk"]], "z", chimney=False, dormer=False,
            wall="cobblestone", mroof="mossy_cobblestone", mlog="spruce_log")
        put(d, torch(29, 4, 7, "west") + [(29, 2, 5, "barrel[facing=up,open=false]"), (29, 2, 11, "hay_block[axis=y]")])
        label(d, 29, 3, 10, "west", ["Root", "Cellar"])
    if L >= 3:                                                       # long two-storey bunkhouse
        bld(d, 3, 24, 23, 30, 2, ("north", 14), [[".     .........kYhk",
                                                   "...................",
                                                   "o..wte..wte..wte..p",
                                                   "m......l.......l...",
                                                   "UuU.kK.Z.....D.D.kY"],
                                                  ["       H.H.H.H.H.H.",
                                                   ".......f.f.f.f.f.f.",
                                                   "...................",
                                                   "Hf.....l.....l...fH",
                                                   "N.k.kD.D.kD.D.k...N"]], "x", chimney=(2, 27), dormer=False,
            mlog="spruce_log", mroof="mangrove")
        put(d, [(x, 5, z, sl("spruce", "top")) for x in (16, 17, 18) for z in (22, 23)]
            + [(x, y, 22, "spruce_fence") for x in (16, 18) for y in (2, 3, 4)] + torch(16, 4, 23, "north"))
        label(d, 19, 3, 23, "north", ["Bunkhouse"])
    if L >= 4:                                                       # mess hall with a deep front porch
        bld(d, 38, 24, 56, 36, 1, ("north", 9), [["kYk.......omoUuUk",
                                                   ".................",
                                                   ".nnnn..nnn..nnnn.",
                                                   ".TTTT..TTT..TTTT.",
                                                   ".ssss..sss..ssss.",
                                                   "........l........",
                                                   ".nnnn..nnn..nnnn.",
                                                   ".TTTT..TTT..TTTT.",
                                                   ".ssss..sss..ssss.",
                                                   ".................",
                                                   "b.Z.h.kYk.kYk.h.b"]], "x", tall=True, chimney=(57, 30),
            dormer=False, mlog="stripped_spruce_log", mroof="dark_prismarine")
        porch_lean(d, 39, 55, 21, 24, 6, "spruce", "spruce_log", (39, 43, 51, 55), gap=(46, 47, 48),
                   floor="spruce_planks")
        put(d, torch(46, 4, 23, "north") + torch(48, 4, 23, "north") + [(41, 2, 22, "barrel[facing=up,open=false]"),
                                                                         (53, 2, 22, "hay_block[axis=y]")])
        label(d, 50, 3, 23, "north", ["Mess", "Hall"])
        # back eaves: window boxes, slop barrels by the kitchen end, firewood stacked against the wall
        put(d, wbox(43, 37, "south", "cornflower") + wbox(52, 37, "south", "poppy")
            + [(40, 2, 37, "barrel[facing=up,open=false]"), (41, 2, 37, "barrel[facing=up,open=false]")])
        woodpile(d, 46, 49, 37, 2, "spruce")
        pavilion(d, 28, 26, 34, 30, 3, [(28, 26), (34, 26), (28, 30), (34, 30), (31, 30)], "x", "spruce",
                 "spruce_log")                                         # open wood shed
        woodpile(d, 29, 33, 29, 2, "spruce")
        woodpile(d, 29, 33, 28, 2, "spruce")
        cart(d, 30, 34, "x", "oak_log[axis=x]")
    if L >= 5:
        bld(d, 40, 4, 50, 14, 3, ("west", 5), [[".     ..b",               # three-storey lodge
                                                 "........b",
                                                 "..wTe....",
                                                 ".........",
                                                 ".......Z.",
                                                 "..wTe....",
                                                 "....l....",
                                                 "........p",
                                                 "kYk.D.kYk"],
                                                ["       ..",
                                                 "Hf.....fH",
                                                 "N.......N",
                                                 "Hf.....fH",
                                                 "...l.....",
                                                 "D.......D",
                                                 ".........",
                                                 ".........",
                                                 "...     ."],
                                                ["HNH...HNH",
                                                 "f.f...f.f",
                                                 ".........",
                                                 "Hf.....fH",
                                                 "N...l...N",
                                                 "Hf.....fH",
                                                 ".........",
                                                 "D.......D",
                                                 "         "]], "x", roofkind="hip", chimney=(51, 9), dormer=False,
            mlog="stripped_dark_oak_log", mroof="mangrove", lower="cobblestone")
        porch_lean_z(d, 6, 12, 38, 40, 6, "spruce", "spruce_log", (6, 12), gap=(8, 9, 10), floor="spruce_planks")
        put(d, torch(39, 4, 8, "west") + torch(39, 4, 10, "west"))
        label(d, 39, 3, 11, "west", ["Lodge"])
        bld(d, 30, 38, 36, 44, 1, ("north", 3), [["k...k",                   # stone smokehouse
                                                   ".....",
                                                   "Y.h.Y",
                                                   ".....",
                                                   "kWhWk"]], "x", roofkind="hip", chimney=(37, 41), dormer=False,
            wall="mossy_cobblestone", mroof="deepslate_tile", mlog="spruce_log")
        put(d, torch(32, 4, 37, "north"))
        label(d, 34, 3, 37, "north", ["Smoke", "House"])
        firepit(d, 16, 40)
        for x, z in ((10, 38), (19, 43)):
            picnic(d, x, z, "spruce", 2)
        woodpile(d, 24, 28, 44)
        bld(d, 42, 39, 50, 45, 1, ("north", 4), [["uUu..WW",              # wash house
                                                   ".......",
                                                   "W.....h",
                                                   "...l...",
                                                   "uUu.kWk"]], "x", chimney=False, dormer=False,
            mlog="stripped_birch_log", mroof="dark_prismarine")
        put(d, torch(45, 4, 38, "north"))
        label(d, 47, 3, 38, "north", ["Wash", "House"])
        for x, z in ((4, 44), (26, 36), (38, 45), (54, 44)):
            spruce_tree(d, x, z)
        lamp_post(d, 22, 36)
        lamp_post(d, 40, 40)


@growth("cook", "Neoterra")
def _g_cook_neo(d, L):
    if L >= 2:                                                       # cold store
        bld(d, 23, 3, 31, 9, 1, ("west", 3), [["kKk.kKk",
                                                ".......",
                                                ".......",
                                                "..l....",
                                                "KkK.KkK"]], mwall="light_gray_concrete")
        planter(d, 22, 4, 2)
        planter(d, 22, 8, 2)
        label(d, 22, 3, 5, "west", ["COLD", "STORE"])
        canopy(d, 24, 10, 30, 11, 5, [(24, 11), (30, 11)])             # delivery bay behind the store
        put(d, [(x, 2, 10, "barrel[facing=up,open=false]") for x in (25, 26, 27, 28, 29)]
            + [(x, 3, 10, "barrel[facing=up,open=false]") for x in (25, 26, 28)])
        lamp_post(d, 32, 10, 3)
    if L >= 3:                                                       # staff block with green roof
        bldL(d, L, 1, 34, 3, 44, 11, 2, ("west", 5), [[".     .bE",
                                                 ".........",
                                                 "..wTe.wTe",
                                                 "..wTe.wTe",
                                                 ".........",
                                                 "....l....",
                                                 "kk.UoUuZp"],
                                                ["       HN",
                                                 ".......f.",
                                                 "Hf.....fH",
                                                 "N.......N",
                                                 "Hf..l..fH",
                                                 ".........",
                                                 "D.wT.Te.D"]],
            mwall="white_terracotta", roofitems=SOLAR + GREEN([1, 3, 5, 7, 9], 7))
        put(d, [(33, 5, z, "smooth_stone_slab[type=bottom,waterlogged=false]") for z in (7, 8, 9)])
        planter(d, 33, 5, 2)
        planter(d, 33, 11, 2)
        label(d, 33, 3, 10, "west", ["STAFF"])
    if L >= 4:                                                       # glass dining pavilion, roof terrace
        bld(d, 23, 19, 41, 31, 1, ("north", 9), [["pb.b.........b.bp",
                                                   ".................",
                                                   "p..nn.......nn..p",
                                                   "...TT...l...TT...",
                                                   ".wTe..wTe.wTe..p.",
                                                   ".................",
                                                   "...nnn.....nnn...",
                                                   "...TTT..l..TTT...",
                                                   "...sss.....sss...",
                                                   ".....nnnnnn......",
                                                   "p.UUUUuUUUUU.Z..p"]], tall=True, wall="glass",
            roofitems=GREEN([2, 4, 6, 8, 10, 12, 14, 16], 11) + [(x, 2, "white_stained_glass_pane") for x in
                                                                   range(1, 18)])
        put(d, [(27, 3, 30, "decorated_pot[cracked=false,facing=north,waterlogged=false]"),   # bar-top dressing
                (32, 3, 30, "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]"),
                (34, 3, 30, "candle[candles=3,lit=true,waterlogged=false]")])
        canopy(d, 25, 21, 39, 28, 15, [(25, 21), (32, 21), (39, 21), (25, 28), (32, 28), (39, 28)],    # roof pergola
               "birch_slab", "birch_fence", 12)
        canopy(d, 23, 12, 31, 15, 5, [(23, 12), (31, 12), (23, 15), (31, 15)])     # street cafe terrace
        for x in (25, 29):
            d.table(x, 2, 13, "birch", "slab")
            d.chair(x - 1, 2, 13, "west", "birch", sit=False)
            d.chair(x + 1, 2, 13, "east", "birch", sit=False)
        for x in (24, 27, 30):
            planter(d, x, 16, 2, "potted_bamboo" if x == 27 else "flowering_azalea")
        for x in (28, 35):                                          # roof terrace tables under the pergola
            d.table(x, 12, 24, "birch", "slab")
            d.chair(x - 1, 12, 24, "west", "birch", sit=False)
            d.chair(x + 1, 12, 24, "east", "birch", sit=False)
        planter(d, 30, 18, 2)
        planter(d, 34, 18, 2)
        label(d, 32, 8, 18, "north", ["SKY", "DINING"])
    if L >= 5:
        bld(d, 39, 33, 47, 41, 6, ("west", 4), [[".     .",              # hotel tower
                                                  ".......",
                                                  "..T...p",
                                                  "..Te...",
                                                  "..T....",
                                                  "wTe...p",
                                                  "p.....b"],
                                                 ["       ",
                                                  "Hf.....",
                                                  "N...wT.",
                                                  "Hf.....",
                                                  ".......",
                                                  "D.p.p..",
                                                  ".     ."],
                                                 [".     .",
                                                  ".......",
                                                  "Hf...fH",
                                                  "N.....N",
                                                  "...l...",
                                                  "D.wT..D",
                                                  "       "],
                                                 ["       ",                # twin room, beds to the north
                                                  ".......",
                                                  "H.N.N.H",
                                                  "f.....f",
                                                  "..wTe..",
                                                  "D.....p",
                                                  ".     ."],
                                                 [".     .",                # suite: double bed + sofa corner
                                                  ".......",
                                                  "HH...bb",
                                                  "ff.....",
                                                  ".....wT",
                                                  "D.l..p.",
                                                  "       "],
                                                 ["       ",
                                                  ".....HN",
                                                  "bb...f.",
                                                  ".......",
                                                  "wTe.l..",
                                                  "..rrr..",
                                                  "D.p.p.D"]], mwall="light_gray_concrete", lower="glass")
        bed_colour(d, 40, 34, 46, 40, 17, "white")
        bed_colour(d, 40, 34, 46, 40, 22, "lime")
        billboard(d, 40, 46, 37, 33, ["ORBIT", "HOTEL"])
        put(d, [(38, 5, z, "smooth_stone_slab[type=bottom,waterlogged=false]") for z in (36, 37, 38)])
        label(d, 38, 3, 35, "west", ["HOTEL"])
        d.fill(29, 1, 35, 31, 1, 37, "water")                         # fountain plaza
        for x, z in perim(28, 34, 32, 38):
            d.set(x, 2, z, "smooth_stone_slab[type=bottom,waterlogged=false]")
        for x, z in ((24, 33), (24, 41), (36, 41)):
            tree(d, x, z, "birch")
        bench(d, 27, 40, "north", 3)
        bench(d, 31, 40, "north", 3)
        for x, z in ((22, 31), (36, 32)):
            lamp_post(d, x, z, 4)


# ============================================================================================ COOKERY complexes
# Kitchen: a service courtyard of larder, scullery, stores and the servants' quarters.
# Hearthwood "manor kitchen court": stone larder (L2), a low scullery & brewhouse range with two stacks closing
#   the court to the south (L3), a three-storey gabled servants' hall with a tall stack (L4), a long two-storey
#   stores range with a sack hoist and a bake house with an oven chimney, well and herb beds (L5).
# Cascadia "camp commissary": hipped stone smokehouse (L2), tall camp kitchen (L3), a two-storey supply barn
#   with a hay hoist (L4), an open cookout pavilion over a grill and the cooks' three-storey quarters (L5).
# Neoterra "food lab": long dry-store bar (L2), a glazed prep kitchen hall (L3), a three-storey test-lab block
#   with solar roof (L4), a staff canteen with a roof garden and a planted court (L5).
@growth("cookery", "Hearthwood")
def _g_cookery_hw(d, L):
    if L >= 2:                                                       # stone larder
        bld(d, 24, 3, 30, 11, 1, ("west", 4), [["kYKYk",
                                                 ".....",
                                                 "h...W",
                                                 ".....",
                                                 "Y.l.K",
                                                 ".....",
                                                 "kKhYk"]], "z", chimney=False, dormer=False,
            wall="stone_bricks", mroof="mud_brick")
        put(d, torch(23, 4, 6, "west"))
        label(d, 23, 3, 9, "west", ["Larder"])
    if L >= 3:                                                       # scullery & brewhouse range
        bld(d, 2, 28, 20, 34, 1, ("north", 9), [["uUuUu...l...kYkhk",
                                                  ".................",
                                                  "..UUU..wte..k.k..",
                                                  "..s.s........l...",
                                                  "kKk.h.WW.p.kYk.kY"]], "x", chimney=(6, 35), dormer=True,
            mwall="white_terracotta", mroof="dark_prismarine")
        stack(d, 16, 35, 12, "bricks")
        put(d, wbox(4, 27, "north", "red_tulip", "warped") + wbox(7, 27, "north", "cornflower", "warped")
            + wbox(16, 27, "north", "oxeye_daisy", "warped") + torch(10, 4, 27, "north") + torch(12, 4, 27, "north"))
        label(d, 13, 3, 27, "north", ["Scullery"])
    if L >= 4:                                                       # servants' hall, three storeys, gable z
        bld(d, 33, 3, 41, 13, 3, ("west", 5), [[".     .",
                                                 ".......",
                                                 "o..n..b",
                                                 "U.wTe.b",
                                                 "..wTe..",
                                                 "...s...",
                                                 "u......",
                                                 "......p",
                                                 "kYk.D.k"],
                                                ["       ",
                                                 "Hf...fH",
                                                 "N.....N",
                                                 "Hf...fH",
                                                 ".......",
                                                 "..rrr..",
                                                 "D.....D",
                                                 ".......",
                                                 ".     ."],
                                                ["       ",
                                                 ".......",
                                                 "bb...H.",
                                                 ".....f.",
                                                 "wTe....",
                                                 "...l...",
                                                 ".......",
                                                 "D.T.T.D",
                                                 "k.....k"]], "z", chimney=(37, 14), dormer=True,
            mwall="calcite", mroof="brick", lower="stone_bricks")
        put(d, torch(32, 4, 7, "west") + wbox(32, 5, "west", "pink_tulip", "warped")
            + wbox(32, 11, "west", "poppy", "warped"))
        label(d, 32, 3, 10, "west", ["Servants'", "Hall"])
    if L >= 5:
        bld(d, 24, 15, 32, 35, 2, ("west", 10), [[".     .",                # stores range
                                                   ".......",
                                                   "kYk.kYk",
                                                   ".......",
                                                   "KkK.KkK",
                                                   ".......",
                                                   "hWh.hWh",
                                                   ".......",
                                                   "kKk.kKk",
                                                   ".......",
                                                   "...l...",
                                                   "YkY.YkY",
                                                   ".......",
                                                   "kkk.kkk",
                                                   ".......",
                                                   "WhW.WhW",
                                                   ".......",
                                                   ".......",
                                                   "kKk.kYk"],
                                                  ["       ",
                                                   "Hf...fH",
                                                   "N.....N",
                                                   "Hf...fH",
                                                   ".......",
                                                   "D..l..D",
                                                   "Hf...fH",
                                                   "N.....N",
                                                   "Hf...fH",
                                                   ".......",
                                                   "..wTe..",
                                                   ".......",
                                                   "Hf...fH",
                                                   "N.....N",
                                                   "Hf...fH",
                                                   "...l...",
                                                   "D.....D",
                                                   ".......",
                                                   "kD...Dk"]], "z", chimney=False, dormer=True,
            mwall="smooth_sandstone", mroof="mud_brick")
        hoist(d, 28, 15, 14, "north", "white_wool")
        put(d, torch(23, 4, 24, "west") + torch(23, 4, 26, "west"))
        label(d, 23, 3, 28, "west", ["Stores"])
        bld(d, 36, 17, 46, 25, 1, ("north", 5), [["kW.....Wk",               # bake house
                                                   ".........",
                                                   "UAU.l.UAU",
                                                   ".........",
                                                   "o.......o",
                                                   ".........",
                                                   "o.o.W.o.o"]], "x", chimney=(47, 21), dormer=False,
            mwall="bricks", mroof="granite")
        put(d, wbox(38, 16, "north", "lily_of_the_valley", "warped") + wbox(44, 16, "north", "red_tulip", "warped")
            + torch(40, 4, 16, "north"))
        label(d, 42, 3, 16, "north", ["Bake", "House"])
        well(d, 12, 24, "stone_bricks", "spruce", "spruce_fence")
        bed_row(d, [(x, z) for z in (38, 40) for x in range(4, 19)], 2)     # herb garden behind the scullery
        woodpile(d, 21, 23, 33, 2, "spruce")
        for x, z in ((40, 33), (49, 40), (28, 40)):
            tree(d, x, z)
        lamp_post(d, 22, 22)
        bench(d, 6, 22, "south", 3)


@growth("cookery", "Cascadia")
def _g_cookery_cas(d, L):
    if L >= 2:                                                       # hipped stone smokehouse
        bld(d, 24, 4, 30, 10, 1, ("west", 3), [["kYhYk",
                                                 ".....",
                                                 "....W",
                                                 "..l..",
                                                 "kKhKk"]], "x", roofkind="hip", chimney=(31, 7), dormer=False,
            wall="cobblestone", mroof="deepslate_tile", mlog="spruce_log")
        put(d, torch(23, 4, 6, "west"))
        label(d, 23, 3, 8, "west", ["Smoke", "House"])
    if L >= 3:                                                       # tall camp kitchen
        bld(d, 24, 14, 42, 20, 1, ("west", 3), [["omoUuUomo.kYk.hWh",
                                                  ".................",
                                                  "...UUUU...UUUU...",
                                                  ".................",
                                                  "kYk.kYk.l.kKk.hWh"]], "x", tall=True, chimney=(32, 13),
            dormer=False, mlog="stripped_spruce_log", mroof="cobbled_deepslate", lower="cobblestone")
        porch_lean(d, 25, 41, 23, 20, 6, "spruce", "spruce_log", (25, 29, 33, 37, 41), floor="spruce_planks")
        put(d, torch(23, 4, 16, "west") + torch(23, 4, 18, "west")
            + wbox(43, 16, "east", "cornflower") + wbox(43, 19, "east", "oxeye_daisy"))
        label(d, 23, 3, 15, "west", ["Camp", "Kitchen"])
    if L >= 4:                                                       # supply barn with hay hoist
        bld(d, 2, 26, 20, 34, 2, ("north", 9), [[".     ......kYkYk",
                                                  ".................",
                                                  "kKk.kKk...kKk.kKk",
                                                  ".................",
                                                  "hhh.YYY...YkY.hhh",
                                                  ".................",
                                                  "kYk.kYk.l.kYk.kYk"],
                                                 ["       ..H.H.H.H.",
                                                  ".........f.f.f.f.",
                                                  ".................",
                                                  "Hf.....l.......fH",
                                                  "N...............N",
                                                  "Hf....kYk......fH",
                                                  "D.D.....l.....D.D"]], "x", chimney=False, dormer=False,
            mlog="stripped_dark_oak_log", mroof="mangrove", wall="birch_planks", lower="cobblestone")
        hoist(d, 20, 30, 13, "east")
        put(d, torch(10, 4, 25, "north") + torch(12, 4, 25, "north"))
        # under the eaves: window boxes, flour barrels at the west end, hay bales and a rain butt behind,
        # a barrel under the hoist
        put(d, wbox(4, 25, "north", "cornflower") + wbox(16, 25, "north", "poppy")
            + [(1, 2, 29, "barrel[facing=up,open=false]"), (1, 2, 30, "barrel[facing=up,open=false]"),
               (6, 2, 35, "hay_block[axis=x]"), (7, 2, 35, "hay_block[axis=x]"),
               (14, 2, 35, "water_cauldron[level=3]"), (21, 2, 32, "barrel[facing=up,open=false]")])
        label(d, 14, 3, 25, "north", ["Supply", "Barn"])
    if L >= 5:
        pavilion(d, 24, 27, 36, 35, 4, [(24, 27), (30, 27), (36, 27), (24, 35), (30, 35), (36, 35)], "x",
                 "spruce", "spruce_log")                               # open cookout shelter
        firepit(d, 30, 31)
        for x, z in ((25, 29), (32, 29), (25, 33), (32, 33)):
            picnic(d, x, z, "spruce", 2)
        put(d, [(26, 2, 31, "smoker[facing=east,lit=true]"), (34, 2, 31, "furnace[facing=west,lit=true]")])
        bld(d, 44, 4, 52, 12, 3, ("south", 4), [[".     .",              # cooks' quarters
                                                  ".......",
                                                  "o.wTe.b",
                                                  "U.wTe.b",
                                                  "u.....p",
                                                  ".......",
                                                  "kY...Yk"],
                                                 ["       ",
                                                  "Hf...fH",
                                                  "N.....N",
                                                  "Hf...fH",
                                                  "...l...",
                                                  "D......",
                                                  ".     ."],
                                                 ["Hf...fH",
                                                  "N.....N",
                                                  ".......",
                                                  "..wTe..",
                                                  "...l...",
                                                  "D.....D",
                                                  "       "]], "x", chimney=(43, 8), dormer=False,
            mlog="spruce_log", mroof="dark_prismarine", lower="mossy_cobblestone")
        put(d, torch(47, 4, 13, "south"))
        label(d, 49, 3, 13, "south", ["Cooks'", "Quarters"])
        woodpile(d, 38, 42, 21, 2)
        for x, z in ((4, 40), (14, 42), (44, 40), (51, 30), (40, 42)):
            spruce_tree(d, x, z)
        lamp_post(d, 22, 24)
        lamp_post(d, 42, 25)


@growth("cookery", "Neoterra")
def _g_cookery_neo(d, L):
    if L >= 2:                                                       # long dry-store bar
        bld(d, 28, 3, 40, 7, 1, ("west", 2), [["kKk.kKk.kKk",
                                               "...........",
                                               "KkK.KkK.KkK"]], mwall="light_gray_concrete")
        planter(d, 27, 3, 2)
        planter(d, 27, 7, 2)
        label(d, 27, 3, 4, "west", ["DRY", "STORE"])
    if L >= 3:                                                       # glazed prep kitchen hall
        bld(d, 3, 18, 21, 26, 1, ("north", 9), [["UoUmUu..l...uUoUm",
                                                  ".................",
                                                  ".UUUU.......UUUU.",
                                                  ".s..s.......s..s.",
                                                  ".................",
                                                  ".................",
                                                  "kKk.x.p...p.E.kKk"]], tall=True, mwall="white_concrete",
            roofitems=[(x, z, "daylight_detector[inverted=false,power=0]") for x in range(2, 17, 2)
                       for z in (2, 3, 5, 6)])
        canopy(d, 9, 15, 15, 17, 6, [(9, 15), (15, 15)])
        label(d, 14, 3, 17, "north", ["PREP"])
        planter(d, 8, 17, 2)
    if L >= 4:                                                       # three-storey test lab
        bld(d, 40, 3, 48, 13, 3, ("west", 5), [[".     .",
                                                 ".......",
                                                 "UoU.UmU",
                                                 ".......",
                                                 "...l...",
                                                 ".wTTe..",
                                                 ".......",
                                                 ".......",
                                                 "kKp.pKk"],
                                                ["       ",
                                                 ".......",
                                                 "E.b.b.C",
                                                 ".......",
                                                 "wT...Te",
                                                 ".......",
                                                 "..l....",
                                                 ".......",
                                                 ".     ."],
                                                ["Hf...fH",
                                                 "N.....N",
                                                 ".......",
                                                 "Hf...fH",
                                                 "N.....N",
                                                 "...l...",
                                                 "D.wTe.D",
                                                 ".......",
                                                 "       "]], mwall="white_terracotta", lower="glass",
            roofitems=SOLAR + [(x, 7, "daylight_detector[inverted=false,power=0]") for x in (2, 3, 4)])
        put(d, [(39, 5, z, "smooth_stone_slab[type=bottom,waterlogged=false]") for z in (7, 8, 9)]
            + [(44, y, 2, "cyan_terracotta") for y in range(2, 17)])
        label(d, 39, 3, 10, "west", ["TEST", "LAB"])
    if L >= 5:
        bld(d, 26, 18, 44, 30, 1, ("north", 9), [["p.b.b...l...b.b.p",          # staff canteen
                                                   ".................",
                                                   ".wTe.wTe...wTe.p.",
                                                   ".................",
                                                   "..nnnn.....nnnn..",
                                                   "..TTTT.....TTTT..",
                                                   "..ssss.....ssss..",
                                                   "........l........",
                                                   "..wTe.wTe.wTe.wTe",
                                                   ".................",
                                                   "p.UUUUUuUUUUUU..p"]], tall=True, wall="glass",
            roofitems=GREEN([2, 4, 6, 8, 10, 12, 14, 16], 11) + GREEN([2, 4, 6, 8, 10, 12, 14, 16], 3))
        label(d, 35, 8, 17, "north", ["STAFF", "CANTEEN"])
        d.box(31, 12, 22, 39, 14, 26, "glass")                         # rooftop herb glasshouse
        d.fill(31, 15, 22, 39, 15, 26, "light_gray_stained_glass")
        for x, z in perim(31, 22, 39, 26):
            if (x - 31) % 4 == 0 and z in (22, 26) or x in (31, 39):
                for y in (12, 13, 14):
                    d.set(x, y, z, "light_gray_concrete")
        for x in range(32, 39):
            for z in (23, 25):
                d.set(x, 11, z, "grass_block[snowy=false]")
                d.set(x, 12, z, "fern" if x % 2 else "sweet_berry_bush[age=3]")
        canopy(d, 32, 14, 38, 17, 6, [(32, 14), (38, 14)])
        for x in (4, 8, 12, 16, 20):                                  # planted court
            planter(d, x, 30, 2, "flowering_azalea" if x % 8 else "potted_bamboo")
        for x, z in ((4, 36), (14, 36), (24, 37), (48, 22), (48, 34), (52, 9), (52, 28)):
            tree(d, x, z, "birch")
        bench(d, 8, 34, "north", 3)
        bench(d, 16, 34, "north", 3)
        lamp_post(d, 23, 33, 4)
        lamp_post(d, 47, 28, 4)


# ============================================================================================ DYER complexes
# Dyeworks: vats, weaving, drying and selling cloth.
# Hearthwood "Madder & Woad": an open timber vat shed with fired vats (L2), a long low weavers' range with
#   dormers and a row of looms (L3), a four-storey hipped drying tower whose slatted top storey is hung with
#   coloured cloths (L4), a tall cloth hall and a yard of drying lines and vats (L5).
# Cascadia "Riverbend Woollens": a fleece shed (L2), a tall loom house (L3), a gabled drying tower with a slatted
#   loft (L4), a two-storey fulling mill and drying frames hung with hanks of wool (L5).
# Neoterra "CHROMA": yarn store (L2), a two-storey studio (L3), a five-storey colour tower with rainbow fins
#   (L4), a glass cloth hall with banner rails on its roof (L5).
def slats(d, x1, z1, x2, z2, ys, mat):
    """Louvred drying storey: the wall cells between the corner posts at the given heights become slats."""
    for x, z in perim(x1, z1, x2, z2):
        if not (x in (x1, x2) and z in (z1, z2)):
            for y in ys:
                d.set(x, y, z, mat)


@growth("dyer", "Hearthwood")
def _g_dyer_hw(d, L):
    if L >= 2:                                                       # open vat shed
        pavilion(d, 27, 3, 37, 11, 4, [(27, 3), (32, 3), (37, 3), (27, 11), (32, 11), (37, 11), (27, 7),
                                       (37, 7)], "x", "dark_prismarine", "dark_oak_log", floor="stone_bricks")
        vats(d, [(29, 5), (31, 5), (33, 5), (35, 5), (29, 9), (31, 9), (33, 9), (35, 9)], 2, 0)
        put(d, [(28, 2, 7, "red_wool"), (29, 2, 7, "yellow_wool"), (36, 2, 7, "blue_wool"),
                (34, 2, 7, "barrel[facing=up,open=false]")])
        label(d, 32, 4, 2, "north", ["Vat", "Shed"], color="blue")
        woodpile(d, 26, 33, 13, 2, "dark_oak")                          # fuel for the vat fires
        put(d, [(x, 2, 13, "barrel[facing=up,open=false]") for x in (35, 36, 37)]
            + [(35, 3, 13, "barrel[facing=up,open=false]")])
        cart(d, 45, 12, "x", "red_wool", "dark_oak")
    if L >= 3:                                                       # long weavers' range with dormers
        bld(d, 3, 24, 27, 30, 1, ("north", 12), [["M.M.M.M.........M.M.M.M",
                                                   "s.s.s.s.........s.s.s.s",
                                                   ".......................",
                                                   "WKW.YkY...l.....WKW.YkY",
                                                   "b.b.p......E.....p.b.b."]], "x", chimney=(2, 27), dormer=True,
            mwall="light_blue_terracotta", mroof="dark_prismarine", win=3)
        put(d, wbox(5, 23, "north", "cornflower", "spruce") + wbox(8, 23, "north", "allium", "spruce")
            + wbox(20, 23, "north", "blue_orchid", "spruce") + wbox(23, 23, "north", "cornflower", "spruce")
            + torch(14, 4, 23, "north"))
        label(d, 17, 3, 23, "north", ["Weavers"], color="blue")
    if L >= 4:                                                       # four-storey drying tower
        bld(d, 40, 3, 48, 11, 4, ("west", 4), [[".     .",
                                                 ".......",
                                                 "WKW.WKW",
                                                 ".......",
                                                 "uu.l.uu",
                                                 ".......",
                                                 "kYk.kYk"],
                                                ["       ",
                                                 ".......",
                                                 "WWW.WWW",
                                                 ".......",
                                                 "KkK.KkK",
                                                 ".......",
                                                 ".     ."],
                                                [".     .",
                                                 ".......",
                                                 "WhW.WhW",
                                                 ".......",
                                                 "kYk.kYk",
                                                 ".......",
                                                 "       "],
                                                ["       ",
                                                 ".......",
                                                 ".......",
                                                 "...l...",
                                                 ".......",
                                                 ".......",
                                                 "......."]], "x", roofkind="hip", chimney=False, dormer=False,
            mwall="calcite", mroof="dark_prismarine", lower="bricks")
        slats(d, 40, 3, 48, 11, (18, 19), "dark_oak_fence")
        for i, x in enumerate((42, 44, 46)):                          # cloths hung out of the loft
            put(d, [(x, 19, 2, f"{dy(d, i)}_wall_banner[facing=north]"),
                    (x, 19, 12, f"{dy(d, i + 2)}_wall_banner[facing=south]")])
        for i, z in enumerate((5, 7, 9)):
            put(d, [(49, 19, z, f"{dy(d, i + 1)}_wall_banner[facing=east]")])
        put(d, torch(39, 4, 6, "west"))
        label(d, 39, 3, 9, "west", ["Drying", "Loft"], color="blue")
    if L >= 5:                                                       # cloth hall + drying yard
        bld(d, 31, 15, 51, 25, 1, ("north", 10), [["b.bWKW...l...WKWb.b",
                                                   "...................",
                                                   ".TTTTT.......TTTTT.",
                                                   "..s.s.........s.s..",
                                                   "........l..........",
                                                   "M.M.M.........M.M.M",
                                                   "...................",
                                                   "WWW.YkY.....YkY.WWW",
                                                   "pE....kYk.kYk....Ep"]], "x", tall=True, chimney=False,
            dormer=False, mwall="white_terracotta", mroof="brick", lower="bricks")
        put(d, torch(40, 4, 14, "north") + torch(42, 4, 14, "north")
            + [(x, 7, 14, f"{dy(d, i)}_wall_banner[facing=north]") for i, x in enumerate((33, 36, 46, 49))])
        label(d, 44, 3, 14, "north", ["Cloth", "Hall"], color="blue")
        # back eaves toward the drying yard: mordant barrels, a rinse tub, a window box on the west end
        put(d, [(34, 2, 26, "barrel[facing=up,open=false]"), (35, 2, 26, "barrel[facing=up,open=false]"),
                (45, 2, 26, "water_cauldron[level=3]"), (46, 2, 26, "barrel[facing=up,open=false]"),
                (52, 2, 22, "barrel[facing=up,open=false]"), (52, 3, 22, "barrel[facing=up,open=false]")]
            + wbox(30, 23, "west", "cornflower", "oak"))
        for k, z in enumerate((30, 34, 38)):                         # drying lines
            drying_line(d, 30, 50, z, 5, "stripped_dark_oak_log", "dark_oak_log", k)
        vats(d, [(x, 42) for x in range(31, 50, 3)], 2, 0)
        for x, z in ((6, 38), (16, 40), (24, 36)):
            tree(d, x, z)
        lamp_post(d, 28, 28)
        bench(d, 10, 33, "north", 3)


@growth("dyer", "Cascadia")
def _g_dyer_cas(d, L):
    if L >= 2:                                                       # fleece shed
        bld(d, 25, 3, 31, 11, 1, ("west", 4), [["WkWkW",
                                                 ".....",
                                                 "W...h",
                                                 ".....",
                                                 "K.l.W",
                                                 ".....",
                                                 "kWhWk"]], "z", chimney=False, dormer=False,
            mlog="stripped_spruce_log", mroof="deepslate_tile")
        put(d, torch(24, 4, 6, "west") + [(24, 2, 4, "white_wool"), (24, 2, 10, "hay_block[axis=y]")])
        label(d, 24, 3, 9, "west", ["Fleece"])
    if L >= 3:                                                       # tall loom house
        bld(d, 25, 15, 45, 21, 1, ("west", 3), [["M.M.M.M.M.M.M.M.M.M",
                                                 "s.s.s.s.s.s.s.s.s.s",
                                                 "...................",
                                                 "...l.....l.....l...",
                                                 "WKWYkY.kYk.WKW.hWhp"]], "x", tall=True, chimney=False,
            dormer=False, mlog="stripped_spruce_log", mroof="cobbled_deepslate", lower="cobblestone")
        put(d, torch(24, 4, 17, "west") + torch(24, 4, 19, "west"))
        # under the eaves: window boxes on the street side, fleece barrels and a wash tub at the back,
        # bales by the east gable
        put(d, wbox(30, 14, "north", "cornflower") + wbox(36, 14, "north", "allium") + wbox(42, 14, "north", "poppy")
            + [(27, 2, 22, "barrel[facing=up,open=false]"), (28, 2, 22, "barrel[facing=up,open=false]"),
               (40, 2, 22, "water_cauldron[level=3]"), (46, 2, 18, "hay_block[axis=y]"),
               (46, 2, 19, "hay_block[axis=y]")])
        label(d, 24, 3, 16, "west", ["Loom", "House"])
    if L >= 4:                                                       # gabled drying tower with slatted loft
        bld(d, 35, 3, 43, 11, 4, ("west", 4), [[".     .",
                                                 ".......",
                                                 "WKW.WKW",
                                                 ".......",
                                                 "uu.l.uu",
                                                 ".......",
                                                 "kYk.kYk"],
                                                ["       ",
                                                 ".......",
                                                 "hhh.WWW",
                                                 ".......",
                                                 "KkK.KkK",
                                                 ".......",
                                                 ".     ."],
                                                [".     .",
                                                 ".......",
                                                 "WhW.WhW",
                                                 ".......",
                                                 "kYk.kYk",
                                                 ".......",
                                                 "       "],
                                                ["       ",
                                                 ".......",
                                                 ".......",
                                                 "...l...",
                                                 ".......",
                                                 ".......",
                                                 "......."]], "z", chimney=False, dormer=False,
            mlog="spruce_log", mroof="mangrove", lower="cobblestone")
        slats(d, 35, 3, 43, 11, (18, 19), "spruce_fence")
        for i, x in enumerate((37, 39, 41)):
            put(d, [(x, 19, 2, f"{dy(d, i)}_wall_banner[facing=north]"),
                    (x, 19, 12, f"{dy(d, i + 3)}_wall_banner[facing=south]")])
        put(d, torch(34, 4, 6, "west"))
        label(d, 34, 3, 9, "west", ["Drying", "Tower"])
    if L >= 5:                                                       # two-storey fulling mill
        bld(d, 25, 25, 37, 39, 2, ("north", 9), [[".     ....b",
                                                   "...........",
                                                   "uu.uu...x..",
                                                   "...........",
                                                   "M.M.M...M.M",
                                                   "...........",
                                                   "WKW.l..WKW.",
                                                   "...........",
                                                   "YkY.....YkY",
                                                   "...........",
                                                   "hWh.....hWh",
                                                   "...........",
                                                   "kYk.p.p.kYk"],
                                                  ["       ....",
                                                   "...........",
                                                   "Hf.......fH",
                                                   "N.........N",
                                                   "Hf..wTe..fH",
                                                   "...........",
                                                   "WWW.l...WWW",
                                                   "...........",
                                                   "KkK.....KkK",
                                                   "...........",
                                                   "hhh.....hhh",
                                                   "...........",
                                                   "D.D..b..D.D"]], "z", chimney=(31, 40), dormer=False,
            mlog="stripped_spruce_log", mroof="deepslate_tile", lower="mossy_cobblestone")
        put(d, torch(33, 4, 24, "north") + torch(35, 4, 24, "north"))
        put(d, wbox(24, 27, "west", "cornflower") + wbox(24, 33, "west", "allium") + wbox(38, 30, "east", "poppy")
            + wbox(38, 36, "east", "oxeye_daisy") + [(24, 2, 30, "barrel[facing=up,open=false]")])
        label(d, 36, 3, 24, "north", ["Mill"])
        for k, z in enumerate((25, 29, 33)):                         # drying frames with hanks of wool
            for x in (40, 52):
                for y in (2, 3, 4, 5):
                    d.set(x, y, z, lg("spruce_log"))
            for x in range(41, 52):
                d.set(x, 5, z, lg("stripped_spruce_log", "x"))
                if x % 2 == 1:
                    d.set(x, 4, z, f"{dy(d, x + k)}_wool")
        vats(d, [(41, 36), (44, 36), (47, 36), (50, 36)], 2, 0)
        for x, z in ((8, 34), (14, 44), (44, 44), (51, 10)):
            spruce_tree(d, x, z)
        lamp_post(d, 23, 23)
        lamp_post(d, 40, 40)


@growth("dyer", "Neoterra")
def _g_dyer_neo(d, L):
    if L >= 2:                                                       # yarn store
        bld(d, 25, 4, 33, 10, 1, ("west", 3), [["kKk.MWM",
                                                 ".......",
                                                 ".......",
                                                 "..l....",
                                                 "KWK.KWK"]], mwall="white_concrete")
        planter(d, 24, 5, 2)
        planter(d, 24, 9, 2)
        label(d, 24, 3, 8, "west", ["YARN"])
    if L >= 3:                                                       # two-storey studio
        bldL(d, L, 1, 3, 17, 23, 23, 2, ("north", 10), [[".     .............",
                                                   "...................",
                                                   "M.M.M..wTe.wTe..M.M",
                                                   "........l..........",
                                                   "uuu.WKW.x.E.WKW.kYk"],
                                                  ["       ..b.b.b.b...",
                                                   "...................",
                                                   "Hf..wTe.....wTe..fH",
                                                   "N.................N",
                                                   "Hf..D.D..l..D.D..fH"]], mwall="white_terracotta",
            roofitems=GREEN([1, 3, 5, 7, 9, 11, 13, 15, 17], 5))
        canopy(d, 11, 14, 17, 16, 6, [(11, 14), (17, 14)])
        label(d, 15, 3, 16, "north", ["STUDIO"])
    if L >= 4:                                                       # colour tower with rainbow fins
        bld(d, 37, 4, 45, 12, 4, ("west", 4), [[".     .",
                                                 ".......",
                                                 "MWM.MWM",
                                                 ".......",
                                                 "uu.l.uu",
                                                 ".......",
                                                 "kYk.kYk"],
                                                ["       ",
                                                 ".......",
                                                 "WKW.WKW",
                                                 ".......",
                                                 "E.b.b.C",
                                                 ".......",
                                                 ".     ."],
                                                [".     .",
                                                 ".......",
                                                 "Hf...fH",
                                                 "N.....N",
                                                 "..wTe..",
                                                 "D.....D",
                                                 "       "],
                                                ["       ",
                                                 ".......",
                                                 "bb...HN",
                                                 ".....f.",
                                                 "wTe.l..",
                                                 "..rrr..",
                                                 "D.....D"]], mwall="white_concrete", lower="glass")
        for x, c in ((38, "magenta"), (40, "cyan"), (42, "lime"), (44, "yellow")):
            put(d, [(x, y, 3, f"{c}_concrete") for y in range(2, 23)])
        label(d, 36, 3, 6, "west", ["COLOUR", "LAB"])
    if L >= 5:                                                       # glass cloth hall with roof banner rails
        bld(d, 27, 16, 47, 26, 1, ("north", 10), [["pM.M.M...l...M.M.Mp",
                                                   "...................",
                                                   ".WKW.WKW.....WKW.p.",
                                                   "...................",
                                                   "..TTTTT.....TTTTT..",
                                                   "...s.s.......s.s...",
                                                   "........l..........",
                                                   "uuu.uuu.....uuu.uuu",
                                                   "kYk.E.p.....p.C.kYk"]], tall=True, wall="glass")
        for z in (19, 23):                                           # banner rails on the roof deck
            for x in (29, 45):
                for y in (12, 13, 14):
                    d.set(x, y, z, "light_gray_concrete")
            for i, x in enumerate(range(30, 45)):
                d.set(x, 14, z, "stripped_birch_log[axis=x]")
                d.set(x, 14, z - 1, f"{dy(d, i)}_wall_banner[facing=north]")
                d.set(x, 14, z + 1, f"{dy(d, i + 3)}_wall_banner[facing=south]")
        label(d, 37, 8, 15, "north", ["CHROMA", "TEXTILES"])
        for x in range(28, 47, 3):
            planter(d, x, 28, 2)
        bld(d, 3, 28, 13, 34, 1, ("north", 5), [["MWM.....b",              # showroom
                                                  ".........",
                                                  "..TTTTT..",
                                                  "...s.s...",
                                                  "WKW.p.WKW"]], mwall="white_concrete", lower="glass",
            roofitems=GREEN([1, 3, 5, 7, 9], 3))
        canopy(d, 6, 26, 10, 27, 6, [(6, 26), (10, 26)])
        label(d, 10, 3, 27, "north", ["SHOWROOM"])
        for x, z in ((18, 38), (6, 40), (51, 20), (51, 34), (30, 38), (42, 38)):
            tree(d, x, z, "birch")
        bench(d, 8, 26, "north", 3)
        bench(d, 16, 26, "north", 3)
        lamp_post(d, 25, 14, 4)
        lamp_post(d, 49, 28, 4)


# ============================================================================================ FLORIST complexes
# Glasshouse estates.
# Hearthwood "walled flower garden": potting shed and cold frames (L2), a long Victorian glasshouse (L3), a
#   two-storey seed shop on the street (L4), a big palm house with tea tables, the florist's hipped house, a
#   rose arbour and cottage beds (L5).
# Cascadia "fireweed nursery": a tool shed and raised beds (L2), a long hoop house (L3), the seed store with a
#   porch (L4), a glazed nursery house, the gardener's porch cabin, rain barrels and a wheelbarrow (L5).
# Neoterra "bloom campus": seed kiosk (L2), a planted glass biodome (L3), a two-storey bloom shop (L4), a
#   five-storey vertical-farm tower with a lime accent fin, planter plaza and benches (L5).
FLX = ["flowering_azalea", "azalea"]


@growth("florist", "Hearthwood")
def _g_florist_hw(d, L):
    if L >= 2:                                                       # potting shed + cold frames
        bld(d, 25, 3, 31, 9, 1, ("west", 3), [["VPVkW",
                                                ".....",
                                                "...UV",
                                                "..l..",
                                                "kpWpk"]], "x", chimney=False, dormer=False,
            mwall="white_terracotta", mroof="mud_brick")
        bed_row(d, [(x, 11) for x in range(25, 32)], 1)
        for x, z in perim(24, 10, 32, 13):                            # picket fence round the cold frames
            if (x, z) != (28, 13):
                d.set(x, 2, z, "oak_fence")
        put(d, [(28, 2, 13, "oak_fence_gate[facing=south,in_wall=false,open=false,powered=false]"),
                (32, 2, 4, "composter[level=4]"), (32, 2, 5, "barrel[facing=up,open=false]")])
        for z in range(4, 9):                                         # potting bench + water butts beside the shed
            put(d, [(34, 2, z, sl("spruce", "top")), (34, 3, z, "potted_" + flower(d, z)),
                    (35, 2, z, "barrel[facing=up,open=false]")])
        put(d, [(35, 3, z, "composter[level=6]") for z in (5, 7)])
        put(d, [(x, 2, 12, td("spruce", "north", "bottom", True)) for x in range(25, 32)]
            + torch(24, 4, 5, "west"))
        label(d, 24, 3, 8, "west", ["Potting", "Shed"])
    if L >= 3:                                                       # long Victorian glasshouse
        bld(d, 25, 14, 45, 22, 1, ("west", 4), [["GGGGGGGG...GGGGGGGG",
                                                 "...................",
                                                 "GG.GGGGGG.GGGGGG.GG",
                                                 "...l.......l.......",
                                                 "GG.GGGGGG.GGGGGG.GG",
                                                 "...................",
                                                 "uUVUVU.....UVUVU.kp"]], "x", tall=True, wall="glass",
            roofkind="glass", chimney=False, dormer=False)
        label(d, 24, 3, 20, "west", ["Glass", "House"])
    if L >= 4:                                                       # two-storey seed shop on the street
        bld(d, 37, 2, 47, 10, 3, ("north", 8), [[".     V.V",
                                                  ".........",
                                                  "P......UV",
                                                  "V..TTT..P",
                                                  "...s.....",
                                                  ".........",
                                                  "kWk.l.kVk"],
                                                 ["       HN",
                                                  ".......f.",
                                                  "Hf.......",
                                                  "N...wTe..",
                                                  ".........",
                                                  "..rrr...p",
                                                  "kD.     ."],
                                                 ["Hf.....fH",
                                                  "N.......N",
                                                  ".........",
                                                  "..wTe....",
                                                  "....l....",
                                                  "D.......D",
                                                  "         "]], "x", chimney=(48, 6), dormer=True,
            mwall="smooth_sandstone", mroof="dark_prismarine")
        put(d, wbox(39, 1, "north", "pink_tulip", "warped") + wbox(42, 1, "north", "cornflower", "warped")
            + torch(46, 4, 1, "north"))
        label(d, 44, 3, 1, "north", ["Seed", "Shop"], color="green")
        flower_stall(d, 37, 40, 12, 2, "oak")
    if L >= 5:                                                       # palm house, glazed, gable to the garden
        bld(d, 30, 25, 44, 41, 1, ("north", 7), [["GGGGG...GGGGG",
                                                  ".............",
                                                  "GG..1...1..GG",
                                                  "GG.........GG",
                                                  "....2.L.2....",
                                                  "GG.........GG",
                                                  "GG..1...1..GG",
                                                  ".............",
                                                  "..wte...wte..",
                                                  ".............",
                                                  "GG..1...1..GG",
                                                  "GG.........GG",
                                                  "....2...2....",
                                                  ".............",
                                                  "uUVUV...VUVUp"]], "z", tall=True, wall="glass", roofkind="glass",
            chimney=False, dormer=False, extra=FLX)
        label(d, 35, 3, 24, "north", ["Palm", "House"])
        bld(d, 3, 24, 13, 34, 2, ("north", 8), [[".     ..b",               # florist's house
                                                  ".........",
                                                  "o..wTe..b",
                                                  "U..wTe...",
                                                  "u........",
                                                  "...l....p",
                                                  ".........",
                                                  "..rrrr...",
                                                  "kD.....Dk"],
                                                 ["       ..",
                                                  "Hf.....fH",
                                                  "N.......N",
                                                  ".........",
                                                  "...l.....",
                                                  "Hf.......",
                                                  "N....wTe.",
                                                  ".........",
                                                  "D.bb.p..D"]], "x", roofkind="hip", chimney=(14, 29), dormer=False,
            mwall="white_terracotta", mroof="brick", lower="bricks")
        put(d, wbox(5, 23, "north", "red_tulip", "warped") + wbox(8, 23, "north", "lily_of_the_valley", "warped")
            + torch(10, 4, 23, "north"))
        put(d, wbox(2, 26, "west", "pink_tulip", "warped") + wbox(2, 29, "west", "allium", "warped")    # west eaves
            + wbox(2, 32, "west", "cornflower", "warped") + [(5, 2, 35, "composter[level=4]"),
                                                            (6, 2, 35, "barrel[facing=up,open=false]")])
        label(d, 12, 3, 23, "north", ["Florist's", "House"])
        for x in (19, 21, 23, 25):                                    # rose arbour on the garden path
            for y in (2, 3, 4):
                d.set(x, y, 27, "oak_fence")
                d.set(x, y, 31, "oak_fence")
            for z in range(27, 32):
                d.set(x, 5, z, "oak_leaves[distance=1,persistent=true,waterlogged=false]")
        bed_row(d, [(x, z) for z in (37, 38) for x in range(4, 26)], 3)
        bed_row(d, [(x, z) for x in (47, 48) for z in range(26, 41)], 0)
        for x, z in ((8, 41), (22, 41), (50, 14), (50, 22)):
            tree(d, x, z)
        lamp_post(d, 17, 26)
        lamp_post(d, 28, 24)
        bench(d, 20, 35, "north", 3)


@growth("florist", "Cascadia")
def _g_florist_cas(d, L):
    if L >= 2:                                                       # tool shed + raised beds
        bld(d, 26, 3, 32, 10, 1, ("west", 3), [["gkhkV",
                                                ".....",
                                                "....W",
                                                "..l..",
                                                ".....",
                                                "kWkVk"]], "z", chimney=False, dormer=False,
            mlog="stripped_spruce_log", mroof="dark_prismarine")
        bed_row(d, [(x, 12) for x in range(26, 33)], 0)
        put(d, [(x, 2, 13, "spruce_slab[type=bottom,waterlogged=false]") for x in range(26, 33)]
            + torch(25, 4, 5, "west"))
        label(d, 25, 3, 8, "west", ["Tool", "Shed"])
    if L >= 3:                                                       # long hoop house
        bld(d, 26, 15, 34, 35, 1, ("north", 4), [["GG...GG",
                                                  ".......",
                                                  "GGG.GGG",
                                                  "GGG.GGG",
                                                  ".......",
                                                  "GGG.GGG",
                                                  "GGG.GGG",
                                                  "...l...",
                                                  "GGG.GGG",
                                                  "GGG.GGG",
                                                  ".......",
                                                  "GGG.GGG",
                                                  "GGG.GGG",
                                                  "...l...",
                                                  "GGG.GGG",
                                                  "GGG.GGG",
                                                  ".......",
                                                  ".......",
                                                  "kWkhkWk"]], "z", tall=True, wall="glass", roofkind="glass",
            chimney=False, dormer=False, mlog="stripped_spruce_log")
        label(d, 28, 3, 14, "north", ["Hoop", "House"])
    if L >= 4:                                                       # seed store with porch
        bld(d, 38, 3, 46, 13, 3, ("west", 5), [[".     .",
                                                 ".......",
                                                 "V.....V",
                                                 "P.TTT.P",
                                                 "...s...",
                                                 ".......",
                                                 "kWk.kWk",
                                                 ".......",
                                                 "kVk.hWk"],
                                                ["       ",
                                                 "Hf...fH",
                                                 "N.....N",
                                                 ".......",
                                                 "...l...",
                                                 "D.....D",
                                                 "..wTe..",
                                                 ".......",
                                                 ".     ."],
                                                ["Hf...fH",
                                                 "N.....N",
                                                 ".......",
                                                 "..wTe..",
                                                 "...l...",
                                                 "D.....D",
                                                 ".......",
                                                 "k.....k",
                                                 "       "]], "z", chimney=(42, 14), dormer=False,
            mlog="spruce_log", mroof="mangrove", wall="birch_planks")
        porch_lean_z(d, 5, 11, 36, 38, 6, "spruce", "spruce_log", (5, 11), gap=(7, 8, 9), floor="spruce_planks")
        put(d, torch(37, 4, 7, "west"))
        label(d, 37, 3, 10, "west", ["Seed", "Store"])
    if L >= 5:                                                       # glazed nursery house
        bld(d, 38, 17, 48, 37, 1, ("west", 10), [["GGGG.GGGG",
                                                   ".........",
                                                   "GG.GGG.GG",
                                                   "GG.GGG.GG",
                                                   ".........",
                                                   "GG.GGG.GG",
                                                   "GG.GGG.GG",
                                                   ".........",
                                                   "....l....",
                                                   ".........",
                                                   "GG.GGG.GG",
                                                   "GG.GGG.GG",
                                                   ".........",
                                                   "GG.GGG.GG",
                                                   "GG.GGG.GG",
                                                   ".........",
                                                   "UVUV.VUVU",
                                                   ".........",
                                                   "kWk.p.kWk"]], "z", tall=True, wall="glass", roofkind="glass",
            chimney=False, dormer=False, mlog="stripped_spruce_log")
        label(d, 37, 3, 25, "west", ["Nursery"])
        bld(d, 3, 26, 15, 34, 1, ("north", 6), [["kV...l...Vb",                # gardener's porch cabin
                                                  "...........",
                                                  "Hf..wTe..fH",
                                                  "N.........N",
                                                  "....rrr....",
                                                  "o..........",
                                                  "U.u.D.D.kWk"]], "x", chimney=(2, 30), dormer=False,
            mlog="stripped_spruce_log", mroof="cobbled_deepslate")
        porch_lean(d, 3, 15, 23, 26, 6, "spruce", "spruce_log", (3, 7, 11, 15), gap=(8, 9, 10),
                   floor="spruce_planks")
        label(d, 11, 3, 25, "north", ["Gardener"])
        bed_row(d, [(x, z) for z in (38, 40, 42) for x in range(4, 22)], 1)
        put(d, [(24, 2, 25, "barrel[facing=up,open=false]"), (24, 3, 25, "water_cauldron[level=3]"),
                (36, 2, 15, "barrel[facing=up,open=false]")])
        cart(d, 18, 30, "z", "coarse_dirt")
        for x, z in ((50, 10), (51, 42), (30, 41), (20, 13)):
            spruce_tree(d, x, z)
        lamp_post(d, 24, 13)
        lamp_post(d, 36, 40)


@growth("florist", "Neoterra")
def _g_florist_neo(d, L):
    if L >= 2:                                                       # seed kiosk
        bld(d, 24, 4, 30, 10, 1, ("west", 3), [["VPVPV",
                                                ".....",
                                                "...UV",
                                                "..l..",
                                                "kVkVk"]], mwall="white_concrete", lower="glass")
        planter(d, 23, 5, 2)
        planter(d, 23, 9, 2)
        label(d, 23, 3, 8, "west", ["SEEDS"])
    if L >= 3:                                                       # planted glass biodome
        bld(d, 24, 14, 42, 24, 1, ("west", 5), [["GGGGGGGG.GGGGGGGG",
                                                 ".................",
                                                 "GG.GGGG...GGGG.GG",
                                                 "GG.GGGG...GGGG.GG",
                                                 "........l........",
                                                 "GG.GGGG...GGGG.GG",
                                                 "GG.GGGG...GGGG.GG",
                                                 ".................",
                                                 "pUVUVUVU.UVUVUVUp"]], tall=True, wall="glass", roofkind="glass")
        label(d, 23, 3, 21, "west", ["BIODOME"])
    if L >= 4:                                                       # two-storey bloom shop
        bld(d, 36, 3, 46, 10, 3, ("west", 3), [[".     .VV",
                                                 ".........",
                                                 "...TTT..P",
                                                 "....s...V",
                                                 ".........",
                                                 "kVk.p.kVk"],
                                                ["       HN",
                                                 ".......f.",
                                                 "Hf.......",
                                                 "N...wTe..",
                                                 ".........",
                                                 "D..     ."],
                                                ["Hf.....fH",
                                                 "N.......N",
                                                 "..wTe....",
                                                 "....l....",
                                                 "D.bb....D",
                                                 "         "]], mwall="white_terracotta", lower="glass",
            roofitems=GREEN([1, 3, 5, 7, 9], 6))
        canopy(d, 33, 4, 35, 8, 6, [(33, 4), (33, 8)])
        label(d, 35, 3, 4, "west", ["BLOOM", "SHOP"])
    if L >= 5:                                                       # vertical-farm tower
        bld(d, 3, 23, 11, 31, 5, ("east", 4), [[".     .",
                                                 ".......",
                                                 "GG...GG",
                                                 "GG.l...",
                                                 ".......",
                                                 "......p",
                                                 "kVk.UVU"],
                                                ["       ",
                                                 "GGG.GGG",
                                                 "GGG.GGG",
                                                 ".......",
                                                 "GGG.GGG",
                                                 "GGG....",
                                                 ".     ."],
                                                [".     .",
                                                 ".......",
                                                 "GGG.GGG",
                                                 "GGG.GGG",
                                                 ".......",
                                                 "GGG.GGG",
                                                 "       "],
                                                ["       ",
                                                 "GGG.GGG",
                                                 "GGG.GGG",
                                                 "...l...",
                                                 "GGG.GGG",
                                                 "GGG....",
                                                 ".     ."],
                                                ["HN...bb",
                                                 "f......",
                                                 ".......",
                                                 "wTe....",
                                                 "...l...",
                                                 "D.rrr..",
                                                 "       "]], mwall="white_concrete", lower="glass",
            roofitems=GREEN([1, 3, 5, 7], 7) + GREEN([1, 3, 5, 7], 3))
        put(d, [(7, y, 22, "cyan_terracotta") for y in range(2, 28)])
        label(d, 12, 3, 25, "east", ["VERTICAL", "FARM"])
        for x in range(15, 24, 2):                                    # planter plaza
            planter(d, x, 28, 2)
            planter(d, x, 34, 2, "potted_bamboo")
        bed_row(d, [(x, z) for z in (38, 39) for x in range(14, 40)], 2)
        for x, z in ((46, 30), (46, 40), (32, 31), (4, 38)):
            tree(d, x, z, "birch")
        bench(d, 17, 31, "north", 3)
        bench(d, 25, 31, "north", 3)
        lamp_post(d, 14, 25, 4)
        lamp_post(d, 34, 27, 4)


# ============================================================================================ GLASSBLOWER complexes
# Glassworks: sand bins, a shop range glazed in coloured glass, a cutting / kiln wing and the master's house.
# Hearthwood "the glass cone": open sand & cullet bins (L2), a street shop range with stained-glass windows
#   and a striped awning (L3), a two-storey cutting room running back from the street (L4) that a south
#   engraving wing turns into an L, and the master's four-storey hipped tower (L5).
# Cascadia "ember glassworks": a sand shed with heaps (L2), a porch gallery (L3), a two-storey kiln shed with a
#   river-rock stack (L4), the master's four-storey lodge and a long annealing shed with three stacks (L5).
# Neoterra "PRISM": silica store and hopper (L2), a two-storey stained-glass gallery (L3), a kiln lab with
#   extraction stacks (L4), a six-storey prism tower clad in coloured glass and a glass sculpture plaza (L5).
def GBX(d):
    s = sl(STY[d.pack]["wood2"], "top")
    return [glass_c(d, 0), glass_c(d, 1), glass_c(d, 2), glass_c(d, 3), (s, glass_c(d, 0)), (s, glass_c(d, 1)),
            (s, glass_c(d, 2)), (s, glass_c(d, 3)), (s, glass_c(d, 4))]


@growth("glassblower", "Hearthwood")
def _g_glass_hw(d, L):
    X = GBX(d)
    if L >= 2:                                                       # open sand & cullet bins
        pavilion(d, 3, 22, 13, 28, 3, [(3, 22), (8, 22), (13, 22), (3, 28), (8, 28), (13, 28)], "x", "spruce",
                 "spruce_log", floor="stone_bricks")
        for x in (3, 13):
            for z in range(23, 28):
                d.set(x, 2, z, "stone_brick_wall")
        pile(d, 4, 25, 6, 27, "sand", [(5, 26)])
        pile(d, 10, 25, 12, 27, "red_sand", [(11, 26)])
        put(d, [(7, 2, 27, "gravel"), (9, 2, 27, "barrel[facing=up,open=false]"), (9, 3, 27, glass_c(d, 0)),
                (7, 2, 26, "barrel[facing=up,open=false]")])
        label(d, 8, 4, 21, "north", ["Sand &", "Cullet"])
    if L >= 3:                                                       # street shop with stained-glass windows
        bld(d, 24, 3, 44, 9, 1, ("north", 10), [["567.567..l..765.765",
                                                  "...................",
                                                  ".TTT....1.2....TTT.",
                                                  "..s......l......s..",
                                                  "kYk.5.6.7.8.9.E.x.p"]], "x", chimney=False, dormer=True,
            mwall="smooth_sandstone", mroof="dark_prismarine", glass=glass_c(d, 1, True), extra=X)
        awning(d, 25, 43, 2, 5, ("blue_wool", "white_wool"), "north")
        put(d, torch(33, 3, 2, "north"))
        label(d, 36, 3, 2, "north", ["Glass", "Shop"], color="blue")
    if L >= 4:                                                       # cutting room running back from the street
        bld(d, 36, 12, 44, 28, 2, ("west", 8), [[".     .",
                                                  ".......",
                                                  "qUq.qUq",
                                                  ".......",
                                                  "z.....g",
                                                  "U.....U",
                                                  "q.....q",
                                                  "...l...",
                                                  ".......",
                                                  "x.....z",
                                                  "U.....U",
                                                  ".......",
                                                  "kYk.kYk",
                                                  ".......",
                                                  "1.2.3.4"],
                                                 ["       ",
                                                  "Hf...fH",
                                                  "N.....N",
                                                  ".......",
                                                  "..wTe..",
                                                  ".......",
                                                  "D.....D",
                                                  ".......",
                                                  "Hf...fH",
                                                  "N.....N",
                                                  ".......",
                                                  "...l...",
                                                  "bb...bb",
                                                  ".......",
                                                  "kD...Dk"]], "z", chimney=(40, 29), dormer=True,
            mwall="calcite", mroof="brick", lower="stone_bricks", extra=X)
        put(d, torch(35, 4, 19, "west") + torch(35, 4, 21, "west"))
        label(d, 35, 3, 23, "west", ["Cutting", "Room"])
    if L >= 5:
        bld(d, 24, 22, 36, 30, 1, ("north", 6), [["12.3.....4p",                # engraving wing (makes the L)
                                                   "...........",
                                                   "qUq.....qUq",
                                                   "...........",
                                                   "x.UUUUU...z",
                                                   "...sss.....",
                                                   "kYk.E.p.kYk"]], "x", tall=True, chimney=False, dormer=False,
            mwall="smooth_sandstone", mroof="brick", keep_roof=True, glass=glass_c(d, 2, True), extra=X)
        label(d, 32, 3, 21, "north", ["Engraving"])
        put(d, torch(29, 4, 21, "north"))
        bld(d, 12, 30, 22, 40, 4, ("north", 8), [[".     ..b",                 # master's tower
                                                   ".........",
                                                   "567...765",
                                                   ".........",
                                                   "..wTe....",
                                                   "..wTe...p",
                                                   ".........",
                                                   "....l....",
                                                   "kYk.E.x.p"],
                                                  ["       ..",
                                                   "Hf.....fH",
                                                   "N.......N",
                                                   ".........",
                                                   "...l.....",
                                                   "D.wT..bbD",
                                                   ".........",
                                                   ".........",
                                                   "...     ."],
                                                  [".     ...",
                                                   ".........",
                                                   "Hf.....fH",
                                                   "N.......N",
                                                   "....l....",
                                                   "D..wTe..D",
                                                   ".........",
                                                   ".........",
                                                   "         "],
                                                  ["       ..",
                                                   ".........",
                                                   "H....bbb.",
                                                   "f........",
                                                   "N..wTe...",
                                                   "....l....",
                                                   ".........",
                                                   "567...765",
                                                   "D.......D"]], "x", roofkind="hip", chimney=(23, 35), dormer=False,
            mwall="calcite", mroof="dark_prismarine", lower="bricks", glass=glass_c(d, 3, True), extra=X)
        put(d, torch(19, 4, 29, "north") + wbox(14, 29, "north", "red_tulip", "crimson")
            + wbox(17, 29, "north", "cornflower", "crimson"))
        label(d, 21, 3, 29, "north", ["Master's", "House"])
        pile(d, 46, 32, 49, 34, "sand", [(47, 33), (48, 33)])
        for x, z in ((4, 34), (6, 41), (30, 39), (48, 40), (50, 14)):
            tree(d, x, z)
        lamp_post(d, 23, 12)
        lamp_post(d, 34, 33)


@growth("glassblower", "Cascadia")
def _g_glass_cas(d, L):
    X = GBX(d)
    if L >= 2:                                                       # sand shed with heaps
        pavilion(d, 26, 3, 34, 9, 3, [(26, 3), (30, 3), (34, 3), (26, 9), (30, 9), (34, 9)], "z", "spruce",
                 "spruce_log")
        for z in range(4, 9):
            d.set(26, 2, z, "cobblestone_wall")
        pile(d, 27, 4, 29, 8, "sand", [(28, 5), (28, 6), (28, 7)])
        pile(d, 31, 6, 33, 8, "gravel", [(32, 7)])
        put(d, [(31, 2, 4, "barrel[facing=up,open=false]"), (32, 2, 4, "barrel[facing=up,open=false]"),
                (33, 2, 4, "red_sand"), (35, 2, 5, "oak_log[axis=y]"), (35, 2, 6, "oak_log[axis=y]")])
        label(d, 30, 4, 2, "north", ["Sand", "Shed"])
        woodpile(d, 27, 33, 11, 2)                                      # furnace wood
        woodpile(d, 37, 42, 4, 3)                                       # cordwood stacks for the glory hole
        woodpile(d, 37, 42, 5, 2)
        cart(d, 48, 13, "x", "sand")
    if L >= 3:                                                       # porch gallery
        bld(d, 3, 19, 23, 25, 1, ("north", 10), [["56.78....l....87.65",
                                                   "...................",
                                                   "..1..2..3...3..2..1",
                                                   "...................",
                                                   "kYk.TTT.wTe.TTT.kYk"]], "x", chimney=False, dormer=False,
            mlog="stripped_spruce_log", mroof="mangrove", glass=glass_c(d, 0, True), extra=X)
        porch_lean(d, 3, 23, 17, 19, 6, "spruce", "spruce_log", (3, 8, 18, 23), gap=(12, 13, 14),
                   floor="spruce_planks")
        put(d, torch(12, 4, 18, "north"))
        label(d, 15, 3, 18, "north", ["Gallery"])
    if L >= 4:                                                       # kiln shed with river-rock stack
        bld(d, 27, 13, 35, 29, 2, ("west", 8), [[".     .",
                                                  ".......",
                                                  "o.o.o.o",
                                                  ".......",
                                                  "UUU.UUU",
                                                  ".......",
                                                  "kYk.kYk",
                                                  "...l...",
                                                  ".......",
                                                  "o.....o",
                                                  "U.....U",
                                                  ".......",
                                                  "hWh.567",
                                                  ".......",
                                                  "kYk.kYk"],
                                                 ["       ",
                                                  ".......",
                                                  "kYk.kYk",
                                                  ".......",
                                                  "hhh.hhh",
                                                  ".......",
                                                  "kKk.kKk",
                                                  "...l...",
                                                  ".......",
                                                  "Hf...fH",
                                                  "N.....N",
                                                  "Hf...fH",
                                                  ".......",
                                                  "D.....D",
                                                  "......."]], "z", chimney=(36, 17), dormer=False,
            mlog="spruce_log", mroof="cobbled_deepslate", lower="cobblestone", extra=X)
        stack(d, 36, 24, 17, "mossy_cobblestone")
        put(d, torch(26, 4, 20, "west") + torch(26, 4, 22, "west"))
        label(d, 26, 3, 24, "west", ["Kiln", "Shed"])
    if L >= 5:
        bld(d, 42, 30, 50, 38, 4, ("west", 4), [[".     .",                  # master's lodge
                                                 ".......",
                                                 "o..wTe.",
                                                 "...wTe.",
                                                 "U......",
                                                 "....l.p",
                                                 "kYk.D.b"],
                                                ["       ",
                                                 "Hf...fH",
                                                 "N.....N",
                                                 ".......",
                                                 "..rrr..",
                                                 "D......",
                                                 ".     ."],
                                                [".     .",
                                                 ".......",
                                                 "567.765",
                                                 ".......",
                                                 "wT...Te",
                                                 ".......",
                                                 "       "],
                                                ["       ",
                                                 ".......",
                                                 "Hf...bb",
                                                 "N......",
                                                 "..wTe..",
                                                 "...l...",
                                                 "D.....D"]], "x", roofkind="hip", chimney=(51, 34), dormer=False,
            mlog="stripped_spruce_log", mroof="dark_prismarine", lower="cobblestone", glass=glass_c(d, 2, True),
            extra=X)
        put(d, torch(41, 4, 33, "west"))
        label(d, 41, 3, 36, "west", ["Master"])
        bld(d, 38, 18, 50, 26, 1, ("north", 6), [["o.o.o...o.o",                  # annealing shed
                                                   "...........",
                                                   "UUU.....UUU",
                                                   "...........",
                                                   "567..l..765",
                                                   "...........",
                                                   "kYk.hWh.kYk"]], "x", chimney=False, dormer=False,
            mlog="spruce_log", mroof="mangrove", wall="cobblestone", extra=X)
        for x in (40, 44, 48):
            stack(d, x, 27, 14, "cobblestone")
        put(d, torch(43, 4, 17, "north"))
        label(d, 46, 3, 17, "north", ["Annealing"])
        cart(d, 14, 30, "x", "sand")
        for x, z in ((6, 33), (20, 38), (32, 40), (51, 12), (14, 40), (44, 6)):
            spruce_tree(d, x, z)
        lamp_post(d, 25, 11)
        lamp_post(d, 37, 15)


@growth("glassblower", "Neoterra")
def _g_glass_neo(d, L):
    X = GBX(d)
    if L >= 2:                                                       # silica store + hopper
        bld(d, 22, 3, 30, 9, 1, ("west", 3), [["k1k1k.k",
                                                ".......",
                                                ".......",
                                                "..l....",
                                                "k1k.k1k"]], mwall="light_gray_concrete", extra=["sand"])
        put(d, [(26, 10, 6, "hopper[enabled=true,facing=down]")] + [(26, y, 10, "light_gray_concrete")
                                                                       for y in range(2, 6)]
            + [(26, 6, 10, "hopper[enabled=true,facing=down]")])
        label(d, 21, 3, 5, "west", ["SILICA"])
    if L >= 3:                                                       # two-storey stained-glass gallery
        bld(d, 33, 3, 43, 11, 2, ("west", 6), [[".     .56",
                                                 ".........",
                                                 "1...2...3",
                                                 ".........",
                                                 "..TTT...4",
                                                 "...s.....",
                                                 "567...765"],
                                                ["       HN",
                                                 ".......f.",
                                                 "..wTe....",
                                                 ".........",
                                                 "Hf......p",
                                                 "N...l....",
                                                 "D.bb...bD"]], mwall="white_concrete", lower="glass",
            glass=glass_c(d, 0, True), extra=X, roofitems=GREEN([1, 3, 5, 7, 9], 7))
        put(d, [(x, 7, 2, glass_c(d, i)) for i, x in enumerate(range(34, 43))])
        label(d, 32, 3, 8, "west", ["GALLERY"])
    if L >= 4:                                                       # kiln lab with extraction stacks
        bld(d, 3, 19, 21, 25, 2, ("north", 9), [[".     ..l........",
                                                  ".................",
                                                  "o.o.o...UUU...o.o",
                                                  ".................",
                                                  "kYk.567.x.765.kYk"],
                                                 ["       ..E.C.b.b.",
                                                  ".................",
                                                  "wT...Te.....wT...",
                                                  ".................",
                                                  "Hf....l......D.fH"]], mwall="white_concrete", extra=X)
        for x in (5, 11, 17):
            stack(d, x, 26, 16, "light_gray_concrete")
        canopy(d, 9, 16, 15, 18, 6, [(9, 16), (15, 16)])
        label(d, 14, 3, 18, "north", ["KILN", "LAB"])
    if L >= 5:                                                       # six-storey prism tower
        bld(d, 25, 14, 33, 22, 6, ("west", 4), [[".     .",
                                                  ".......",
                                                  "1.....2",
                                                  ".......",
                                                  "..TTT..",
                                                  "...s...",
                                                  "567.765"],
                                                 ["       ",
                                                  ".......",
                                                  "E.b.b.C",
                                                  ".......",
                                                  "wT...Te",
                                                  ".......",
                                                  ".     ."],
                                                 [".     .",
                                                  ".......",
                                                  "Hf...fH",
                                                  "N.....N",
                                                  "...l...",
                                                  "D.wTe.D",
                                                  "       "],
                                                 ["       ",                # design studio
                                                  ".......",
                                                  "C.TTT.E",
                                                  "...s...",
                                                  ".......",
                                                  "p..l..b",
                                                  ".     ."],
                                                 [".     .",
                                                  ".......",
                                                  "1.2.3.4",
                                                  ".......",
                                                  "..wTe..",
                                                  ".......",
                                                  "       "],
                                                 ["       ",
                                                  ".....HN",
                                                  "bb...f.",
                                                  ".......",
                                                  "wTe.l..",
                                                  "..rrr..",
                                                  "D.....D"]], mwall="white_concrete", glass=glass_c(d, 1, True),
            extra=X)
        billboard(d, 26, 32, 18, 33, ["PRISM"])
        label(d, 24, 3, 20, "west", ["PRISM"])
        for i, (x, z) in enumerate(((40, 30), (44, 34), (40, 38))):     # glass sculpture plaza
            for y in range(2, 6 + i):
                d.set(x, y, z, glass_c(d, i + y))
            d.set(x, 1, z, "smooth_quartz")
        for x, z in ((48, 22), (48, 40), (30, 38), (6, 34), (16, 38)):
            tree(d, x, z, "birch")
        bench(d, 36, 32, "east", 3)
        planter(d, 36, 28, 2)
        planter(d, 46, 28, 2)
        lamp_post(d, 23, 25, 4)
        lamp_post(d, 36, 26, 4)
# ============================================================================================ TAVERN add-ons
@growth("tavern", "Hearthwood")
def _g_tavern_hw(d, L):
    if L >= 2:
        HOUSE(d, 24, 3, [["       hhYk",
                          ".......l...",
                          "zg...kYk..h",
                          "...........",
                          "TTT.....wR.",
                          ".s..l...wR.",
                          "kKk.hh.DbbD"],
                         ["       DHN.",
                          ".......lf..",
                          "Hf.......fH",
                          "N..T....T.N",
                          "...s....s..",
                          "...l.......",
                          "kD........."]], ["Coach", "House"])
    if L >= 3:
        HALL(d, 2, 25, ["h1h1h1h...h1h1h1h",
                        "u.u.u.u...u.u.u.u",
                        ".................",
                        ".................",
                        "........l........",
                        ".................",
                        "kYk.............k",
                        ".................",
                        "zga.DDD...hhh.YYY"], ["Stables"], extra=["oak_fence"])
        SHED(d, 24, 14, ["kKkK.KkKk",
                         "....l....",
                         "..k.k.kYk",
                         ".........",
                         "YkY.p.kKk"], ["Ale", "Store"])
        tree(d, 30, 40)
        tree(d, 36, 30)
        lamp_post(d, 22, 37)
        bench(d, 26, 37, "north", 3)


@growth("tavern", "Cascadia")
def _g_tavern_cas(d, L):
    if L >= 2:
        HOUSE(d, 25, 3, [["       kYkh",
                          ".......l...",
                          "wte..wte..p",
                          "...........",
                          "wte..wte...",
                          "....l......",
                          "kKk.ZD.bbh."],
                         ["       H.H.",
                          ".......f.f.",
                          "Hf.......fH",
                          "...........",
                          "Hf.......fH",
                          "...l.......",
                          "kDk........"]], ["Bunk", "House"])
    if L >= 3:
        HALL(d, 25, 15, ["h1h1h1h...h1h1h1h",
                         "u.u.u.u...u.u.u.u",
                         ".................",
                         ".................",
                         "........l........",
                         ".................",
                         "YkY.........YkYkY",
                         ".................",
                         "zga.DDD...hhh.kKk"], ["Livery"], extra=["spruce_fence"])
        SHED(d, 25, 29, ["kYkY.YkYk",
                         "....l....",
                         "..h.h.kKk",
                         ".........",
                         "kKk.p.YkY"], ["Feed", "Store"])
        spruce_tree(d, 41, 31)
        spruce_tree(d, 45, 8)
        lamp_post(d, 23, 13)


@growth("tavern", "Neoterra")
def _g_tavern_neo(d, L):
    if L >= 2:
        HOUSE(d, 23, 3, [["       UUUU",
                          ".......l...",
                          "wTe..wTe...",
                          "...........",
                          "wTe..wTe...",
                          "....l......",
                          "pkkZ.ssss.p"],
                         ["       HNH.",
                          ".......f.f.",
                          "Hf...T...fH",
                          "N...s.....N",
                          "...........",
                          "p..l.......",
                          "kD........."]], ["SKY", "BAR"], roofitems=SOLAR + GREEN([1, 3, 5, 7, 9, 11], 7))
    if L >= 3:
        HALL(d, 3, 19, ["pb.b.b.b...b.b.bp",
                        ".................",
                        "..rrrrrrrrrrrrr..",
                        "..rrrrrrrrrrrrr..",
                        "..rrrrrrlrrrrrr..",
                        "..rrrrrrrrrrrrr..",
                        ".................",
                        "wte.wte.Z.wte.wte",
                        "p..UUUUUUUUUUU..p"], ["SKYLINE", "BALLROOM"],
             roofitems=SOLAR + GREEN([9, 11, 13, 15], 8))
        SHED(d, 24, 15, ["kKk.kKk.k",
                         "....l....",
                         "..kKk.kKk",
                         ".........",
                         "p.k.k.k.p"], ["CELLAR"])
        tree(d, 26, 32, "birch")
        tree(d, 33, 26, "birch")
