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
        d.rug(17, 9, 21, 11, y0, ("red_carpet",), "plain")
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
    d.rug(6, 6, 7, Z2 - 1, y0, ("red_carpet",), "plain")
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
    for x in (7, 15):
        d.plant(x, y0, z1 + 1, "potted_bamboo")
    xs = range(8, 13) if L == 1 else range(x1 + 2, x2 - 1)      # chef's counter: stools at the pass
    for x in xs:
        d.chair(x, y0, 10, "north", "mangrove")
        seats += 1
    if L >= 2:                                                   # table for two by the east window
        d.table(x2 - 1, y0, 7, "birch", "slab", "smooth_quartz_slab")
        d.chair(x2 - 1, y0, 6, "north", "birch")
        d.chair(x2 - 1, y0, 8, "south", "birch")
        seats += 2
    d.rug(x1 + 2, 8, x2 - 2, 9, y0, ("light_gray_carpet",), "plain")
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
        d.rug(x1 + 3, 9, x2 - 1, 10, 7, ("cyan_carpet",), "plain")
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
    d = Design("Hearthwood", rel, (50, 42, 46))
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
    d = Design("Cascadia", rel, (50, 42, 47), paving="coarse_dirt")
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
    d = Design("Neoterra", rel, (48, 42, 44), paving="smooth_stone")
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
    d = Design("Hearthwood", rel, (51, 42, 46))
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
    d = Design("Cascadia", rel, (50, 42, 46), paving="coarse_dirt")
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
    d = Design("Neoterra", rel, (49, 42, 44), paving="smooth_stone")
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
    d = Design("Hearthwood", rel, (48, 42, 44))
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
    d = Design("Cascadia", rel, (49, 42, 41), paving="coarse_dirt")
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
    d = Design("Neoterra", rel, (46, 42, 40), paving="smooth_stone")
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
    d = Design("Hearthwood", rel, (49, 42, 46))
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
    d = Design("Cascadia", rel, (48, 42, 47), paving="coarse_dirt")
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
    d = Design("Neoterra", rel, (48, 42, 41), paving="smooth_stone")
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
        extra=(), ext=(), sign=None, roofitems=(), chimney=True, dormer=True):
    """Draw one add-on building and lay its hand-drawn plans. n storeys (pitch 5; a tall single storey has 8-high
    walls). Stairs are fixed: flight k rises along the north interior row from the west (k even) or along the
    south row from the east (k odd). door = (side, offset from x1/z1). ext = [(dx, y, dz, block)] relative to
    (x1, z1); sign = (dx, y, dz, facing, lines); roofitems = [(dx, dz, block)] on a flat roof."""
    S = STY[d.pack]
    P = d.pack
    y0 = 2
    salt = f"m{x1},{z1}"
    mwall = d.vary(["smooth_sandstone", "white_terracotta", "calcite", "yellow_terracotta", "bricks"], salt) \
        if P == "Hearthwood" else d.vary(["white_concrete", "light_gray_concrete", "white_terracotta",
                                          "quartz_block"], salt)
    mroof = d.vary({"Hearthwood": ["dark_prismarine", "brick", "mud_brick", "granite"],
                    "Cascadia": ["cobbled_deepslate", "dark_prismarine", "mangrove", "deepslate_tile"]}.get(P, ["x"]),
                   salt)
    mlog = d.vary(["stripped_spruce_log", "stripped_dark_oak_log", "spruce_log", "stripped_birch_log"], salt)
    H = 8 if tall else 4
    tops = []
    for k in range(n):
        yb = y0 + 5 * k
        yt = yb + H - 1
        if P == "Hearthwood":
            hw_body(d, x1, z1, x2, z2, yb, yt, wall=wall or ("bricks" if k == 0 and n > 2 else mwall),
                    base="stone_bricks" if k == 0 else "dark_oak_planks", floor=S["floor"] if k == 0 else None,
                    ceiling=None if tall else "dark_oak_planks")
        elif P == "Cascadia":
            cas_body(d, x1, z1, x2, z2, yb, yt, floor=S["floor"] if k == 0 else None, footing=k == 0,
                     ceiling=None if tall else "spruce_planks", logm=mlog)
            if wall == "glass":
                for x, z in perim(x1, z1, x2, z2):
                    if not ((x - x1) % 3 == 0 and z in (z1, z2) or (z - z1) % 3 == 0 and x in (x1, x2)):
                        for yy in range(yb + 1, yt + 1):
                            d.set(x, yy, z, "glass")
        else:
            neo_body(d, x1, z1, x2, z2, yb, yt, wall=wall or mwall, floor=S["floor"] if k == 0 else None,
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
            elif along % 3 == 2 and (P != "Hearthwood" or "log" not in d.get(x, ya, z)):
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
        d.flat(x1, z1, x2, z2, ytop + 1, "smooth_quartz", "white_concrete", "smooth_quartz_slab")
        for (ddx, ddz, blk) in roofitems:
            d.set(x1 + ddx, ytop + 2, z1 + ddz, blk)
        return ytop + 1
    gwall = mwall if P == "Hearthwood" else "spruce_planks"
    if roofkind == "hip":
        ridge = d.hip(x1, z1, x2, z2, ytop + 1, mroof + "_stairs", mroof + "_slab", 1)
        d.set((x1 + x2) // 2, ridge + 1, (z1 + z2) // 2, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    else:
        ridge = roof(d, x1, z1, x2, z2, ytop + 1, axis, mroof, mroof + "_slab", gwall)
        if dormer:
            dormers(d, x1, z1, x2, z2, ytop + 1, axis, gwall, mroof, glass)
    if chimney:                                                    # stack on the outside of a gable end
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


def grow(d, L, base):
    """Add the type's add-on buildings and site dressing for this level (hand-written per type and pack)."""
    fn = GROW.get((base, d.pack))
    if fn:
        fn(d, L)
    reskin(d)
    if L <= 3:
        plain(d)


GROW = {}


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


# ============================================================================================ COOK add-ons
@growth("cook", "Hearthwood")
def _g_cook_hw(d, L):
    if L >= 2:
        SHED(d, 27, 2, ["KkYkhkYkK",
                        "....l....",
                        "..UAU.UVU",
                        "....l....",
                        "WWhk.kYkK"], ["Pantry"])
    if L >= 3:
        plans = [["       b.Zb",
                  ".......l...",
                  "omUuU..wR.p",
                  "..wte..wTR.",
                  "...s...wR.p",
                  "......l....",
                  "kYk.D.bb.Vc"],
                 ["       NHND",
                  ".......lf..",
                  "Hf..rrr..fH",
                  "N...rrr...N",
                  "Hf..rrr..fH",
                  "...l.......",
                  "kD........."]]
        if L >= 5:
            plans.append(["HN.bb.bb.NH",
                          "f....l....f",
                          "..T.....T..",
                          "..s.....s..",
                          "...rrrrr...",
                          ".k.........",
                          "kD.        "])
        HOUSE(d, 27, 12, plans, ["Staff", "House"])
    if L >= 4:
        SHED(d, 41, 3, ["kYkkk.kkk",
                        "....l....",
                        "..k.k.k.k",
                        ".........",
                        "pkkkk.kkp"], ["Brew", "House"])
    if L >= 5:
        SHED(d, 42, 23, ["uuu.WWW.u",
                         "....l....",
                         "..TTT.TTT",
                         ".........",
                         "WWW.p.uuu"], ["Laundry"])
    if L >= 4:
        HALL(d, 2, 30, ["bP.P.P.P.P.P.P.Pb",
                        "........l........",
                        ".nnnnnnn.nnnnnnn.",
                        ".TTTTTTT.TTTTTTT.",
                        ".sssssss.sssssss.",
                        "....l.......l....",
                        "rrrrrrrrrrrrrrrrr",
                        "...TTTTTTTTTTT...",
                        "p..sssssssssss..p"], ["Banquet", "Hall"])
    if L >= 5:
        HALL(d, 24, 30, ["p.b.b.b...b.b.b.p",
                         ".................",
                         ".wte..wte..wte...",
                         "........l........",
                         "..rrrrrrrrrrrrr..",
                         "..rrrrrrRrrrrrr..",
                         "........l........",
                         ".wte..wte..wte.Z.",
                         "p......UUU......p"], ["Garden", "Room"])
        for x in (5, 14, 31, 40):                                    # orchard along the back of the site
            tree(d, x, 45)
        tree(d, 48, 34)
        tree(d, 22, 47)
        tree(d, 48, 46)
        lamp_post(d, 10, 44)
        lamp_post(d, 26, 44)
        bench(d, 19, 44, "north", 3)
        bench(d, 35, 44, "north", 3)


@growth("cook", "Cascadia")
def _g_cook_cas(d, L):
    if L >= 2:
        SHED(d, 30, 2, ["hYkkh.kkY",
                        ".........",
                        "..k.l.kKk",
                        ".........",
                        "WhkYk.hWk"], ["Root", "Cellar"])
    if L >= 3:
        plans = [["       oUmu",
                  ".......l...",
                  "..nnn..p..b",
                  "..TTT......",
                  "..sss..wTe.",
                  "....l......",
                  "kYk.hW..kYk"],
                 ["       HNH.",
                  ".......f.f.",
                  "Hf.......fH",
                  "N..rrrrr..N",
                  "Hf.......fH",
                  "..l........",
                  "kDk........"]]
        if L >= 5:
            plans.append(["HNH.bb.HNHD",
                          "f.f.l..f.f.",
                          "...........",
                          "..T..T..T..",
                          "..s..s..s..",
                          "kk.........",
                          "Yh.        "])
        HOUSE(d, 30, 12, plans, ["Bunkhouse"])
    if L >= 4:
        SHED(d, 46, 2, ["Ykh.kYh.k",
                        "....l....",
                        "..h.h.h.h",
                        ".........",
                        "kkk.h.kkk"], ["Smoke", "House"])
    if L >= 5:
        SHED(d, 46, 12, ["uu.WW.uu.",
                         "....l....",
                         "..UUU.UUU",
                         ".........",
                         "WW..p..uu"], ["Wash", "House"])
    if L >= 4:
        HALL(d, 2, 24, ["kYk.oUmU..UoUm.kY",
                        "........l........",
                        ".nnnnnn...nnnnnn.",
                        ".TTTTTT...TTTTTT.",
                        ".ssssss...ssssss.",
                        "........l........",
                        ".nnnnnn...nnnnnn.",
                        ".TTTTTT...TTTTTT.",
                        ".ssssss...ssssss."], ["Mess", "Hall"])
    if L >= 5:
        HALL(d, 24, 24, ["h.h.h.k...k.h.h.h",
                         ".................",
                         "..rrrrrrrrrrrrr..",
                         "..rrrrrrrrrrrrr..",
                         "Z.rrrrrrlrrrrrr.L",
                         "..rrrrrrrrrrrrr..",
                         "..rrrrrrrrrrrrr..",
                         ".................",
                         "wte.wte.kYk.wte.p"], ["Dance", "Barn"])
        for x in (6, 16, 30, 40):
            spruce_tree(d, x, 40)
        spruce_tree(d, 50, 30)
        lamp_post(d, 11, 38)
        lamp_post(d, 35, 38)
        bench(d, 22, 38, "north", 3)


@growth("cook", "Neoterra")
def _g_cook_neo(d, L):
    if L >= 2:
        SHED(d, 23, 2, ["kkk.kkk.k",
                        ".........",
                        "..k.l.k.k",
                        ".........",
                        "KkK.KkK.K"], ["COLD", "STORE"])
    if L >= 3:
        plans = [["       bEbC",
                  ".......l...",
                  "..wTe..TT..",
                  "..wTe..s...",
                  "..wTe......",
                  "....l....p.",
                  "p.Z..kk..Vp"],
                 ["       HNHD",
                  ".......f.f.",
                  "HfN......fH",
                  "...rrrr....",
                  "HfN......fH",
                  "...l.......",
                  "kD........."]]
        if L >= 5:
            plans.append(["Hf.bb.bb.fH",
                          ".....l.....",
                          "..TT...TT..",
                          "..s.....s..",
                          "...rrrrr...",
                          "p..........",
                          "Dk.        "])
        HOUSE(d, 23, 12, plans, ["STAFF"], roofitems=SOLAR + GREEN([1, 3, 5, 7, 9, 11], 7))
    if L >= 4:
        SHED(d, 37, 2, ["KkK.kkk.K",
                        "....l....",
                        "..kKk.kKk",
                        ".........",
                        "p.k.k.k.p"], ["WINE"])
    if L >= 5:
        SHED(d, 38, 12, ["u.u.u.W.W",
                         "....l....",
                         "..UUUUU..",
                         ".........",
                         "p.WWW.uup"], ["LAUNDRY"])
    if L >= 4:
        HALL(d, 3, 21, ["pb.b.b.b.b.b.b.bp",
                        ".................",
                        ".nn..nn...nn..nn.",
                        ".TT..TT...TT..TT.",
                        ".ss..ss...ss..ss.",
                        "........l........",
                        ".nn..nn...nn..nn.",
                        ".TT..TT...TT..TT.",
                        ".ss..ss.p.ss..ss."], ["SKY", "DINING"],
             roofitems=GREEN([2, 4, 6, 8, 10, 12, 14, 16], 9) + [(x, 3, "daylight_detector[inverted=false,power=0]")
                                                                  for x in range(3, 15)])
    if L >= 5:
        HALL(d, 25, 25, ["b.b.b.b...b.b.b.b",
                         ".................",
                         "..wTe.......wTe..",
                         "..wTe...l...wTe..",
                         ".................",
                         "....TTTTTTTTT....",
                         "....s...C...s....",
                         ".................",
                         "p.kk..Z...Z..kk.p"], ["ORBIT", "HOTEL"],
             roofitems=SOLAR + GREEN([9, 11, 13, 15], 8))
        for x in (6, 16, 30, 40):
            tree(d, x, 39, "birch")
        tree(d, 46, 28, "birch")
        tree(d, 25, 41, "birch")
        tree(d, 46, 40, "birch")
        lamp_post(d, 11, 37)
        lamp_post(d, 35, 37)
        bench(d, 21, 37, "north", 3)


def garden(d, gz, trees=(6, 16, 30, 40), extra_trees=(), lamps=(11, 35), benches=(20, 36)):
    """The L5 garden strip along the back of the site: hand-placed trees, lamp posts and benches."""
    kind = {"Hearthwood": "oak", "Cascadia": "spruce", "Neoterra": "birch"}[d.pack]
    for x, z in [(x, gz) for x in trees] + list(extra_trees):
        if kind == "spruce":
            spruce_tree(d, x, z)
        else:
            tree(d, x, z, kind)
    for x in lamps:
        lamp_post(d, x, gz - 1)
    for x in benches:
        bench(d, x, gz - 1, "north", 3)


# ============================================================================================ COOKERY add-ons
@growth("cookery", "Hearthwood")
def _g_cookery_hw(d, L):
    if L >= 2:
        SHED(d, 25, 2, ["hYkKkhYkK",
                        "....l....",
                        "..hh.YkY.",
                        "....l....",
                        "kKkYhkKkh"], ["Larder"])
    if L >= 3:
        plans = [["       uUuU",
                  ".......l...",
                  "uUu..wte..p",
                  "...........",
                  "UoU..wte..k",
                  "....l......",
                  "kKk.hh.YkKk"],
                 ["       HNH.",
                  ".......f.f.",
                  "Hf..T....fH",
                  "N...s.....N",
                  "Hf.rrr...fH",
                  "...l.......",
                  "kD........."]]
        if L >= 5:
            plans.append(["bbE..C.TT.D",
                          ".....l..s..",
                          "...........",
                          "..wTe...Hf.",
                          "..wTe......",
                          "pk.........",
                          "kD.        "])
        HOUSE(d, 25, 12, plans, ["Scullery"])
    if L >= 4:
        HALL(d, 2, 24, ["oUoUmUu..UuUoUoUm",
                        "........l........",
                        "..UUUUU...UUUUU..",
                        "..UAUVU...UAUVU..",
                        ".................",
                        "kK.....l.....kKk.",
                        ".................",
                        "..nnnn....nnnn...",
                        "..TTTT....TTTT..."], ["Great", "Kitchen"])
        SHED(d, 40, 2, ["kkkkk.kkk",
                        "....l....",
                        "..YkY.KkK",
                        ".........",
                        "hhh.k.hhh"], ["Stores"])
    if L >= 5:
        HALL(d, 24, 24, ["b.p.b.p...p.b.p.b",
                         ".................",
                         ".nnnnnnnnnnnnnnn.",
                         ".TTTTTTTTTTTTTTT.",
                         ".sssssssssssssss.",
                         "........l........",
                         "..wte.......wte..",
                         "..wte...Z...wte..",
                         "p...............p"], ["Servants'", "Hall"])
        SHED(d, 41, 12, ["uuUUoUUuu",
                         "....l....",
                         "..UUU.UUU",
                         ".........",
                         "kKk.p.kKk"], ["Bake", "House"])
        garden(d, 39, extra_trees=((47, 29), (22, 41), (48, 41)))


@growth("cookery", "Cascadia")
def _g_cookery_cas(d, L):
    if L >= 2:
        SHED(d, 24, 3, ["YhkKhkYkh",
                        "....l....",
                        "..k.h.kYk",
                        ".........",
                        "hkKkYhkKh"], ["Larder"])
    if L >= 3:
        plans = [["       oUmU",
                  ".......l...",
                  "UuU..nnn..h",
                  ".....TTT...",
                  "kk...sss..k",
                  "....l......",
                  "YhkWW.kYhkK"],
                 ["       H.H.",
                  ".......f.f.",
                  "Hf.....N.fH",
                  "....rrr....",
                  "Hf.....N.fH",
                  "...l.......",
                  "kDk........"]]
        if L >= 5:
            plans.append(["HfN.bb.NfH.",
                          ".....l.....",
                          "...........",
                          ".T..T..T...",
                          ".s..s..s...",
                          "kh.........",
                          "Yk.        "])
        HOUSE(d, 24, 13, plans, ["Camp", "Kitchen"])
    if L >= 4:
        HALL(d, 2, 26, ["omUuUoUm..UoUmkYk",
                        "........l........",
                        "..nnnnnnn........",
                        "..TTTTTTT...hh.k.",
                        "..sssssss........",
                        "........l........",
                        "..nnnnnnn...wte..",
                        "..TTTTTTT...wte..",
                        "..sssssss.......p"], ["Cook", "Shack"])
        SHED(d, 39, 3, ["hYh.kKk.h",
                        "....l....",
                        "..kkk.YkY",
                        ".........",
                        "KkK.h.kkk"], ["Supply"])
    if L >= 5:
        HALL(d, 24, 26, ["k.h.k.h...h.k.h.k",
                         ".................",
                         "..wte..wte..wte..",
                         "........l........",
                         "..wte..wte..wte..",
                         ".................",
                         "..rrrrrrrrrrrrr..",
                         "........Z........",
                         "bb.b.b.....b.b.bb"], ["Dining", "Lodge"])
        SHED(d, 40, 14, ["uu.UUU.uu",
                         "....l....",
                         "..UoU.UmU",
                         ".........",
                         "hkh.p.hkh"], ["Smoke", "Room"])
        garden(d, 41, extra_trees=((47, 31), (22, 43), (48, 43)), benches=(20, 36))


@growth("cookery", "Neoterra")
def _g_cookery_neo(d, L):
    if L >= 2:
        SHED(d, 28, 2, ["KKk.kKK.k",
                        "....l....",
                        "..kkk.kkk",
                        ".........",
                        "kKk.kKk.K"], ["DRY", "STORE"])
    if L >= 3:
        plans = [["       UoUm",
                  ".......l...",
                  "UUU..UUU...",
                  "...........",
                  "UuU..UAU..k",
                  "....l......",
                  "kkk.p..kKk."],
                 ["       bbCE",
                  ".......l...",
                  "TT.TT.TT...",
                  "s..s..s....",
                  "...........",
                  "p..l.......",
                  "kD........."]]
        if L >= 5:
            plans.append(["HfN.bbb.NfH",
                          "....l......",
                          "..wTe......",
                          "..wTe..Hf..",
                          "...........",
                          "p..........",
                          "kD.        "])
        HOUSE(d, 28, 11, plans, ["PREP"], roofitems=SOLAR + GREEN([1, 3, 5, 7, 9, 11], 7))
    if L >= 4:
        HALL(d, 2, 18, ["UoUoUmUu..UuUoUoU",
                        "........l........",
                        "..UUUU.....UUUU..",
                        "..UAUU.....UUVU..",
                        ".................",
                        "kKkKk..l.....kKkK",
                        ".................",
                        "..UUUUUUUUUUUUU..",
                        "..s...s...s...s.."], ["PRODUCTION"],
             roofitems=[(x, 3, "daylight_detector[inverted=false,power=0]") for x in range(3, 16)])
        SHED(d, 42, 2, ["kKk.KkK.k",
                        "....l....",
                        "..KkK.kKk",
                        ".........",
                        "k.kKk.k.p"], ["DRY", "GOODS"])
    if L >= 5:
        HALL(d, 24, 22, ["p.b.b.b...b.b.b.p",
                         ".................",
                         ".nn.nn.nn.nn.nn..",
                         ".TT.TT.TT.TT.TT..",
                         ".ss.ss.ss.ss.ss..",
                         "........l........",
                         "..UUUUU...UUUUU..",
                         "..UAUVU...UAUVU..",
                         "p...............p"], ["STAFF", "CANTEEN"], roofitems=SOLAR + GREEN([9, 11, 13, 15], 8))
        SHED(d, 43, 11, ["UUoUUmUUu",
                         "....l....",
                         "..UUUUU..",
                         ".........",
                         "kKk.p.kKk"], ["PASTRY"])
        garden(d, 36, extra_trees=((48, 23), (22, 38), (48, 38)))


# ============================================================================================ BAKER add-ons
@growth("baker", "Hearthwood")
def _g_baker_hw(d, L):
    if L >= 2:
        SHED(d, 27, 2, ["WWWkYkWWW",
                        "....l....",
                        "..WhW.WhW",
                        ".........",
                        "hhWkWkhhW"], ["Flour", "Store"])
    if L >= 3:
        plans = [["       bpbZ",
                  ".......l...",
                  "oUuUA..wR..",
                  "..wte..wT..",
                  "...s...wR.p",
                  "....l......",
                  "kYk.DVc.bbp"],
                 ["       NHD.",
                  ".......lf..",
                  "Hf..T....p.",
                  "N...s......",
                  "..rrrrr....",
                  "...l.......",
                  "kV........."]]
        if L >= 5:
            plans.append(["Hf.b..b.fHN",
                          ".....l.....",
                          "..T......p.",
                          "..s........",
                          "...rrrr....",
                          ".k.........",
                          "kD.        "])
        HOUSE(d, 27, 12, plans, ["Baker's", "House"])
    if L >= 4:
        HALL(d, 2, 25, ["1o1o1o1..1o1o1o1W",
                        "........l........",
                        "..UUUUU...UUUUU..",
                        "..UAUVU...UVUAU..",
                        ".................",
                        "WW.....l.......WW",
                        "hW.............Wh",
                        "..kYkYk...kYkYk..",
                        "u...............x"], ["Bake", "Hall"], extra=["bricks"])
        SHED(d, 42, 2, ["hhh.WWW.h",
                        "....l....",
                        "..hWh.WhW",
                        ".........",
                        "WkW.h.WkW"], ["Mill", "Loft"])
    if L >= 5:
        HALL(d, 24, 25, ["VAVAV.b...b.VAVAV",
                         ".................",
                         ".wte..wte..wte...",
                         "........l........",
                         ".wte..wte..wte...",
                         ".................",
                         ".wte..wte..wte...",
                         "........l........",
                         "p..UUUUUUUUUUU..p"], ["Pastry", "Cafe"])
        SHED(d, 42, 12, ["AVAVAVAVA",
                         "....l....",
                         "..UUU.UUU",
                         ".........",
                         "kYk.p.kYk"], ["Cake", "Shop"])
        garden(d, 39, trees=(5, 14, 30, 40), extra_trees=((48, 28), (22, 42), (48, 42)), lamps=(10, 26),
               benches=(19, 35))


@growth("baker", "Cascadia")
def _g_baker_cas(d, L):
    if L >= 2:
        SHED(d, 26, 2, ["WhWkWhWkW",
                        "....l....",
                        "..hWh.kYk",
                        ".........",
                        "WWkhh.WWk"], ["Flour", "Shed"])
        spruce_tree(d, 24, 25)
        lamp_post(d, 24, 11)
    if L >= 3:
        plans = [["       oUmu",
                  ".......l...",
                  "UAU..nnn..p",
                  "...h.TTT...",
                  "kk...sss..k",
                  "....l......",
                  "YhD.bb.VcWk"],
                 ["       NHN.",
                  ".......lf..",
                  "Hf.......fH",
                  "N..rrr....N",
                  "...........",
                  "...l.......",
                  "kDh........"]]
        if L >= 5:
            plans.append(["bHf....fHbb",
                          ".....l.....",
                          "..T..T.....",
                          "..s..s.....",
                          "...rrrr....",
                          ".k.........",
                          "Dh.        "])
        HOUSE(d, 26, 12, plans, ["Baker's", "Cabin"])
    if L >= 4:
        HALL(d, 2, 28, ["1o1o1o1..1o1o1o1h",
                        "........l........",
                        "..TTTTTTT.TTTTT..",
                        "..TAVATVT.TATVT..",
                        ".................",
                        "hW.....l.......Wh",
                        "W...............W",
                        "..kYkhk...khkYk..",
                        "u...............x"], ["Bake", "House"], extra=["cobblestone"])
        SHED(d, 41, 2, ["WWh.hWW.k",
                        "....l....",
                        "..kWk.hWh",
                        ".........",
                        "hhh.W.kYk"], ["Grain"])
    if L >= 5:
        HALL(d, 24, 28, ["k.h.k.b...b.k.h.k",
                         ".................",
                         ".nnn..nnn..nnn...",
                         ".TTT..TTT..TTT...",
                         ".sss..sss..sss...",
                         "........l........",
                         "..wte.......wte..",
                         ".................",
                         "p.AVA.UUUUU.AVA.p"], ["Cafe"])
        SHED(d, 41, 12, ["AVA.AVA.A",
                         "....l....",
                         "..TTT.TTT",
                         ".........",
                         "kYk.p.kYk"], ["Pie", "Shop"])
        garden(d, 42, extra_trees=((47, 31), (22, 45), (48, 45)))


@growth("baker", "Neoterra")
def _g_baker_neo(d, L):
    if L >= 2:
        SHED(d, 26, 2, ["WWkWWkWWk",
                        "....l....",
                        "..WkW.WkW",
                        ".........",
                        "kWWkWWkWW"], ["FLOUR"])
    if L >= 3:
        plans = [["       UoUm",
                  ".......l...",
                  "UAUVU..UUU.",
                  "...........",
                  "..UAU..wte.",
                  "....l......",
                  "kkk.p..kKk."],
                 ["       bECb",
                  ".......l...",
                  "TT.TT......",
                  "s..s.......",
                  "....rrrr...",
                  "p..l.......",
                  "kD........."]]
        if L >= 5:
            plans.append(["HfN.bb..NfH",
                          "....l......",
                          "..T.....T..",
                          "..s.....s..",
                          "...rrrrr...",
                          "p.........p",
                          "kD.        "])
        HOUSE(d, 26, 12, plans, ["PATISSERIE"], roofitems=SOLAR + GREEN([1, 3, 5, 7, 9, 11], 7))
    if L >= 4:
        HALL(d, 2, 15, ["1o1o1o1..1o1o1o1W",
                        "........l........",
                        "UUUU.......UUUU..",
                        "UAUV.......VUAU..",
                        ".....kKkKk.......",
                        "........l........",
                        "..UUUUUUUUUUUUU..",
                        "..s.s.s.s.s.s.s..",
                        "kKk...........kKk"], ["BAKE", "LAB"], extra=["polished_andesite"],
             roofitems=[(x, 3, "daylight_detector[inverted=false,power=0]") for x in range(3, 16)])
        SHED(d, 40, 2, ["kWWk.kWWk",
                        "....l....",
                        "..WWk.kWW",
                        ".........",
                        "WkW.p.WkW"], ["GRAIN"])
    if L >= 5:
        HALL(d, 24, 24, ["p.b.b.b...b.b.b.p",
                         ".................",
                         "..wTe..wTe..wTe..",
                         "........l........",
                         "..wTe..wTe..wTe..",
                         ".................",
                         "..rrrrrrrrrrrrr..",
                         ".................",
                         "p..UAUVUAUVUAU..p"], ["LUMEN", "CAFE"], roofitems=SOLAR + GREEN([9, 11, 13, 15], 8))
        SHED(d, 41, 12, ["AVAVA.AVA",
                         "....l....",
                         "..UUU.UUU",
                         ".........",
                         "p.kKk.k.p"], ["CAKE", "BAR"])
        garden(d, 38, extra_trees=((48, 27), (22, 40), (48, 40)))
