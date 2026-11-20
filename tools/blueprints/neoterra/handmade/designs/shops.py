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


def hood(d, x1, x2, z, y, wallside, m="bricks"):
    """Range hood: upside-down stairs over a cooking line (back against the wall side)."""
    for x in range(x1, x2 + 1):
        d.set(x, y, z, st(m, wallside, "top"))


def hood_z(d, x, z1, z2, y, wallside, m="bricks"):
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
    d = Design("Hearthwood", rel, (27, 20, 23))
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
        d.seating(17, 5, 22, 11, y0, need, "oak", "post", rug=("red_carpet",), step=3)
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


@design("baker")
def baker(pack, rel, L):
    return {"Hearthwood": baker_hw, "Cascadia": baker_hw, "Neoterra": baker_hw}[pack](rel, L)
