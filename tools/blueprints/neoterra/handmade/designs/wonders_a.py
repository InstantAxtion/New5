"""
Grand projects A: cathedral (+ cathedralwing) and colossus (+ colossuswing).

Cathedral
  Hearthwood  English Gothic cathedral (Salisbury / Wells): stone nave with lean-to aisles and clerestory, west
              front with a traceried rose window and a gabled portal between two square WEST TOWERS (the wings),
              cruciform with transepts and a square-ended chancel, flying buttresses with pinnacles, a crossing
              tower that ends in a tall octagonal spire at L5.
              L1 nave + tower bases, L2 aisles + rose, L3 transepts / crossing / chancel, L4 crossing tower,
              battlements, flying buttresses, L5 spire, tower spirelets, churchyard.
  Cascadia    Mountain stave church (Borgund / Heddal) in a timber chapel close: tiered dark shingle roofs over a
              central mast hall, wrap-around covered gallery (svalgang), round apse with a pointed cap, roof
              turret with stacked spire tiers and carved ridge finials; the wings are free-standing timber
              BELFRIES with skirted bases at the front corners of a fenced yard.
  Neoterra    Contemporary crown cathedral (Brasilia-style): a ring of white concrete ribs that pinch in and flare
              out into a crown, stained-glass panels between them, sunken entry, circular nave around a central
              altar; the wings are slim white CAMPANILE with open bell frames, flanking the forecourt.
Colossus
  Hearthwood  "The Old King": crowned stone king in a long robe and cloak, hands on a sword planted point-down,
              on a stepped stone-brick plinth with a foundation hall; wings = stone guard PYLONS with braziers.
  Cascadia    "Timber Giant": a carved, painted log giant (plaid shirt, denim, boots, beard, red cap) leaning on
              a huge felling axe, on a river-rock and log crib plinth; wings = carved timber POLES with
              spread-wing tops over little log shrines.
  Neoterra    "Beacon": a smooth quartz figure with chrome (iron) joints raising a glowing orb, on a stepped white
              terrace plinth with glass skirts; wings = glass and steel light PYLONS with end-rod beams.
  The statue grows with every level (12 -> 36 blocks), the wings grow with it.
"""
import math

from hm import Design, design, AIR, D4, OPP, CW

CATH_WING = "wonders/cathedralwing0.blueprint"
COLO_WING = "wonders/colossuswing0.blueprint"


# ------------------------------------------------------------------------------------------------ helpers
def stair(name, facing, half="bottom", shape="straight"):
    return f"{name}[facing={facing},half={half},shape={shape},waterlogged=false]"


def slab(name, t="bottom"):
    return f"{name}[type={t},waterlogged=false]"


def log(name, axis="y"):
    return f"{name}[axis={axis}]"


def wallb(name):
    return f"{name}[east=none,north=none,south=none,up=true,waterlogged=false,west=none]"


def fence(name):
    return f"{name}[east=false,north=false,south=false,waterlogged=false,west=false]"


def trap(name, facing, half="bottom", open_=False):
    return f"{name}[facing={facing},half={half},open={'true' if open_ else 'false'},powered=false,waterlogged=false]"


def lantern(hanging=True, soul=False):
    return f"{'soul_' if soul else ''}lantern[hanging={'true' if hanging else 'false'},waterlogged=false]"


CHAIN = "chain[axis=y,waterlogged=false]"
SG_GOTHIC = ("blue", "red", "blue", "yellow", "purple", "blue", "red", "light_blue")


def sglass(x, y, z, cols=SG_GOTHIC, pane=True):
    c = cols[(x * 7 + y * 3 + z * 5) % len(cols)]
    return f"{c}_stained_glass_pane" if pane else f"{c}_stained_glass"


def chandelier(d, x, z, ytop, ybot, soul=False):
    for y in range(ybot + 1, ytop + 1):
        d.set(x, y, z, CHAIN)
    d.set(x, ybot, z, lantern(True, soul))


def pews(d, x1, x2, zs, y, wood, back="north"):
    for z in zs:
        for x in range(x1, x2 + 1):
            d.chair(x, y, z, back, wood, sit=True)


def spire(d, cx, cz, y0, half, height, block, edge=None, octagon=True, top=None):
    """Tapering spire: per layer a ring of `block`; where the next layer steps in, the ring is made of `edge`
    stairs (facing up-slope) so the taper reads smooth. Octagonal corners are chamfered."""
    edge = edge or block.replace("_tiles", "_tile").replace("_planks", "") + "_stairs"
    rs = [int(round(half * (1 - k / height) + 0.25)) for k in range(height)] + [-1]
    for k in range(height):
        r, rn, y = rs[k], rs[k + 1], y0 + k
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                cut = octagon and r >= 2 and abs(dx) == r and abs(dz) == r
                if cut:
                    continue
                ring = max(abs(dx), abs(dz)) == r or (octagon and r >= 2 and abs(dx) + abs(dz) == 2 * r - 1)
                if not ring:
                    d.set(cx + dx, y, cz + dz, AIR)
                    continue
                if rn < r and r > 0:
                    if abs(dz) >= abs(dx):
                        f = "south" if dz < 0 else "north"
                    else:
                        f = "east" if dx < 0 else "west"
                    shape = "straight"
                    if abs(dx) == abs(dz) or (octagon and r >= 2 and abs(dx) + abs(dz) == 2 * r - 1
                                              and abs(dx) != r and abs(dz) != r):
                        shape = "outer_left" if (dx < 0) == (dz < 0) else "outer_right"
                        f = "south" if dz < 0 else "north"
                    d.set(cx + dx, y, cz + dz, stair(edge, f, "bottom", shape))
                else:
                    d.set(cx + dx, y, cz + dz, block)
    if top:
        d.set(cx, y0 + height, cz, top)


def lancet(d, x, z, y1, y2, cols=SG_GOTHIC, pane=True):
    for y in range(y1, y2 + 1):
        d.set(x, y, z, sglass(x, y, z, cols, pane))


def rose(d, cx, cy, z, R, frame, cols=("blue", "red", "yellow")):
    """Rose window in the wall plane z: tracery spokes and rim of `frame`, coloured rings of glass panes."""
    for dx in range(-R, R + 1):
        for dy in range(-R, R + 1):
            r = math.hypot(dx, dy)
            if r > R + 0.5:
                continue
            if r < 0.6:
                c = "yellow"
            elif r > R - 0.5:
                spoke = dx == 0 or dy == 0 or abs(dx) == abs(dy)
                if spoke:
                    d.set(cx + dx, cy + dy, z, frame)
                    continue
                c = cols[0]
            elif r > R - 1.5:
                c = cols[1]
            else:
                c = cols[2] if (dx + dy) % 2 else cols[0]
            d.set(cx + dx, cy + dy, z, f"{c}_stained_glass_pane")


# ================================================================================================ CATHEDRAL
# ---------------------------------------------------------------------------- Hearthwood: English Gothic
HC_SIZE = (31, 60, 33)
HC_TX, HC_TZ, HC_TW = (5, 19), 1, 7          # west towers (wings) x origin, z origin, footprint
HC_WHUT = (1, 1, 5)                            # wing hut, tower-local
HC_TOP = {1: 17, 2: 21, 3: 25, 4: 29, 5: 29}   # tower wall top (local y)


def hc_wing(rel, L):
    d = Design("Hearthwood", rel, (HC_TW, 46, HC_TW), gy=0, paving="polished_andesite")
    S, T = "stone_bricks", HC_TOP[L]
    n = HC_TW - 1
    d.box(0, 1, 0, n, T, n, S)
    for y in range(1, T + 1):                      # angle shafts on the corners
        for x, z in ((0, 0), (n, 0), (0, n), (n, n)):
            d.set(x, y, z, "chiseled_stone_bricks" if y % 6 == 0 else "polished_andesite")
    d.fill(0, 1, 0, n, 1, n, "polished_andesite")
    d.clear(1, 1, 1, n - 1, 1, n - 1)
    for y in (7, 13, 19, 25):                      # string courses
        if y < T:
            for i in range(1, n):
                for (x, z, f) in ((i, 0, "north"), (i, n, "south"), (0, i, "west"), (n, i, "east")):
                    d.set(x, y, z, "chiseled_stone_bricks" if i == 3 else S)
    # ground floor: west portal on the street, side doors (one leads into the nave)
    d.door(3, 1, 0, "south", "dark_oak")
    d.set(3, 3, 0, "chiseled_stone_bricks")
    d.door(0, 1, 2, "east", "dark_oak")
    d.door(n, 1, 2, "west", "dark_oak", "right")
    d.hut(*HC_WHUT)
    d.set(1, 1, 1, "water_cauldron[level=3]")             # holy-water stoup
    d.lamp(3, 5, 3)
    d.set(3, 6, 3, CHAIN)
    # tall lancets on the street side and both flanks
    for y1, y2 in ((4, 6), (9, 12), (15, 18), (21, 24)):
        if y2 < T - 6:
            lancet(d, 3, 0, y1, y2)
            for x in (0, n):
                lancet(d, x, 4, y1, y2)
    # ladder up the south wall to the bell chamber
    bf = T - 6
    for y in range(1, bf + 1):
        d.set(3, y, n - 1, "ladder[facing=north,waterlogged=false]")
    d.fill(1, bf, 1, n - 1, bf, n - 1, "dark_oak_planks")
    d.set(3, bf, n - 1, "ladder[facing=north,waterlogged=false]")
    # belfry: paired louvred openings on all four sides
    for i in (2, 4):
        for y in range(bf + 1, bf + 5):
            for x, z, f in ((i, 0, "north"), (i, n, "south"), (0, i, "west"), (n, i, "east")):
                d.set(x, y, z, trap("dark_oak_trapdoor", f, "top", True) if y < bf + 4 else
                      stair("stone_brick_stairs", OPP[f], "top"))
    d.fill(1, T - 1, 3, n - 1, T - 1, 3, log("dark_oak_log", "x"))
    d.item(3, T - 2, 3, "bell[attachment=ceiling,facing=north,powered=false]")
    d.fill(1, T, 1, n - 1, T, n - 1, "stone_bricks")
    # crown of the tower
    if L <= 3:                                     # temporary tiled pyramid cap
        d.hip(0, 0, n, n, T + 1, "deepslate_tile_stairs", "deepslate_tile_slab", overhang=0)
        d.set(3, T + 4, 3, wallb("stone_brick_wall"))
    else:
        for i in range(0, n + 1):                  # battlements
            for x, z in ((i, 0), (i, n), (0, i), (n, i)):
                d.set(x, T + 1, z, S)
                if i % 2 == 0:
                    d.set(x, T + 2, z, slab("stone_brick_slab"))
        for x, z in ((0, 0), (n, 0), (0, n), (n, n)):  # corner pinnacles
            h = 4 if L == 4 else 7
            for y in range(T + 1, T + 1 + h):
                d.set(x, y, z, "polished_andesite" if y < T + h - 1 else wallb("stone_brick_wall"))
            d.set(x, T + 1 + h, z, "lightning_rod[facing=up,powered=false,waterlogged=false]" if L == 5
                  else slab("stone_brick_slab"))
        if L == 5:                                 # lead-clad spirelet
            spire(d, 3, 3, T + 1, 2, 10, "deepslate_tiles", octagon=False, top=wallb("stone_brick_wall"))
            d.set(3, T + 12, 3, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    return d


def hc_buttress(d, x, z, out, y_top, fly_to=None, fly_y=None):
    """Stepped buttress pier at (x, z) (`out` = side facing away from the wall), optional flying arch to the
    nave wall at column fly_to, landing at fly_y, plus a pinnacle on top."""
    S = "stone_bricks"
    for y in range(2, y_top + 1):
        d.set(x, y, z, S)
    for y in (5, 9):
        if y < y_top:
            ox, oz = D4[out]
            if d.bp.inside(x + ox, y, z + oz) and d.air(x + ox, y, z + oz):
                d.set(x + ox, y, z + oz, stair("stone_brick_stairs", OPP[out]))
    d.set(x, y_top + 1, z, "polished_andesite")
    d.set(x, y_top + 2, z, wallb("stone_brick_wall"))
    d.set(x, y_top + 3, z, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    if fly_to is not None:
        step = 1 if fly_to > x else -1
        xs = list(range(x + step, fly_to, step))
        for i, xx in enumerate(xs):
            yy = y_top - 1 + (i * (fly_y - y_top + 1)) // max(1, len(xs) - 1)
            d.set(xx, yy + 1, z, slab("stone_brick_slab"))
            d.set(xx, yy, z, stair("stone_brick_stairs", "east" if step > 0 else "west", "top"))


def hc_cathedral(rel, L):
    d = Design("Hearthwood", rel, HC_SIZE, gy=1, paving="grass_block")
    S, ST = "stone_bricks", "stone_brick_stairs"
    ne = 14 if L == 1 else 17                     # nave east end
    aisles = L >= 2
    cross = L >= 3
    # paths
    d.fill(13, 1, 0, 17, 1, 0, "gravel")
    if aisles:
        d.fill(0, 1, 0, 30, 1, 0, "gravel")
    # ---------------- nave -------------
    d.fill(12, 1, 1, 18, 1, ne, "polished_andesite")
    for x in (11, 19):
        d.fill(x, 2, 1, x, 16, ne, S)
    d.fill(11, 2, 1, 19, 16, 1, S)
    if not cross:
        d.fill(11, 2, ne, 19, 16, ne, S)
    d.clear(12, 2, 2, 18, 16, ne - 1 if not cross else ne)
    for z in range(2, ne + 1, 2):                  # checkered stone floor
        for x in range(12, 19):
            if (x + z) % 4 == 0:
                d.set(x, 1, z, "smooth_stone")
    # cornice
    for z in range(0, ne + 1 if not cross else ne + 1):
        for x, f in ((10, "east"), (20, "west")):
            if d.air(x, 16, z):
                d.set(x, 16, z, stair(ST, f, "top"))
    # clerestory lancets (above the aisle roofs)
    for z in range(9, ne, 3):
        for x in (11, 19):
            lancet(d, x, z, 13, 15)
    if not aisles:                                 # L1: tall side lancets in the plain nave walls
        for z in (9, 12):
            for x in (11, 19):
                lancet(d, x, z, 4, 10)
        for z in (8, 11, ne):
            for x, out in ((10, "west"), (20, "east")):
                for y in range(2, 11):
                    d.set(x, y, z, S)
                d.set(x, 11, z, stair(ST, OPP[out]))
    # ---------------- aisles -------------
    if aisles:
        for side, (xo, xi, xw) in (("west", (6, 10, 11)), ("east", (24, 20, 19))):
            x1, x2 = min(xo, xi), max(xo, xi)
            d.fill(x1, 1, 8, x2, 1, ne, "polished_andesite")
            d.fill(xo, 2, 8, xo, 7, ne, S)
            d.fill(x1, 2, ne, x2, 7, ne, S)
            d.clear(x1 + (1 if side == "west" else 0), 2, 8, x2 - (0 if side == "west" else 1), 7, ne - 1)
            # lean-to roof rising to the nave wall
            step = 1 if side == "west" else -1
            up = "east" if side == "west" else "west"
            for i, x in enumerate(range(xo - step, xw, step)):
                y = 7 + i
                for z in range(8, ne + 2):
                    if z == ne + 1 and cross:
                        continue
                    d.set(x, y, z, stair("deepslate_tile_stairs", up))
                    if i >= 1:
                        for yy in range(8, y):
                            if z == ne and d.air(x, yy, z):
                                d.set(x, yy, z, S)
            # arcade: piers every 3, pointed arches between
            for z in range(8, ne):
                pier = (z - 8) % 3 == 0
                for y in range(2, 8):
                    if pier or y >= 7:
                        d.set(xw, y, z, S if not pier else "polished_andesite")
                    elif y == 6:
                        a = (z - 8) % 3
                        d.set(xw, y, z, stair(ST, "south" if a == 1 else "north", "top"))
                    else:
                        d.set(xw, y, z, AIR)
            # aisle windows between the buttresses
            for z in range(9, ne, 3):
                lancet(d, xo, z, 3, 5)
                lancet(d, xo, z + 1, 3, 5)
            # side chapels: candle stands
            for z in range(10, ne, 3):
                d.set(xo + step, 2, z, "chiseled_stone_bricks")
                d.candle(xo + step, 3, z, 3)
            for z in range(9, ne, 3):
                d.lamp(xo + 2 * step, 6, z)
    # ---------------- crossing, transepts, chancel -------------
    if cross:
        d.fill(2, 1, 18, 28, 1, 26, "polished_andesite")
        d.fill(12, 1, 27, 18, 1, 31, "polished_andesite")
        d.box(2, 2, 18, 28, 16, 26, S)
        d.box(11, 2, 26, 19, 16, 31, S)
        d.clear(3, 2, 19, 27, 16, 25)
        d.clear(12, 2, 18, 18, 16, 30)
        d.clear(12, 2, 26, 18, 16, 26)
        for x in (6, 7, 8, 9, 10, 20, 21, 22, 23, 24):  # open the aisles into the transepts
            d.clear(x, 2, 18, x, 6, 18)
        # transept gable ends with rose / lancets
        r = 4 if L >= 4 else 3
        for x in (2, 28):
            if L >= 4:
                rose_x(d, x, 11, 22, 3, "chiseled_stone_bricks")
            for z in (20, 24):
                lancet(d, x, z, 3, 7)
        for z in (18, 26):
            for x in (5, 8, 22, 25):
                lancet(d, x, z, 4, 10)
        # big east window, five lights
        for x in range(13, 18):
            lancet(d, x, 31, 4, 12 if x in (14, 15, 16) else 10)
        d.set(15, 13, 31, sglass(15, 13, 31))
        for z in (28, 30):
            for x in (11, 19):
                lancet(d, x, z, 4, 12)
        # roofs: transept (x) + chancel (z)
        d.gable(2, 18, 28, 26, 17, "x", "deepslate_tile_stairs", "deepslate_tile_slab", S, 1)
        d.gable(11, 27, 19, 31, 17, "z", "deepslate_tile_stairs", "deepslate_tile_slab", S, 1)
        for z in range(18, 32):
            for x, f in ((10, "east"), (20, "west")):
                if z >= 27 and d.air(x, 16, z):
                    d.set(x, 16, z, stair(ST, f, "top"))
        # crossing tower
        ct = {3: 23, 4: 31, 5: 31}[L]
        d.box(11, 17, 18, 19, ct, 26, S)
        d.clear(12, 2, 19, 18, ct - 1, 25)
        for y in range(2, ct + 1):
            for x, z in ((11, 18), (19, 18), (11, 26), (19, 26)):
                d.set(x, y, z, "polished_andesite")
        d.fill(12, ct - 1, 19, 18, ct - 1, 25, "dark_oak_planks")      # lantern ceiling
        for i in (13, 15, 17):                                          # lantern windows
            for y in range(19, min(ct - 2, 27)):
                if y < 21 or L >= 4:
                    for x, z in ((i, 18), (i, 26), (11, i + 9), (19, i + 9)):
                        d.set(x, y, z, sglass(x, y, z))
        if L == 3:
            d.hip(11, 18, 19, 26, ct + 1, "deepslate_tile_stairs", "deepslate_tile_slab", overhang=0)
        else:
            for i in range(9):
                for x, z in ((11 + i, 18), (11 + i, 26), (11, 18 + i), (19, 18 + i)):
                    d.set(x, ct + 1, z, S)
                    if i % 2 == 0:
                        d.set(x, ct + 2, z, slab("stone_brick_slab"))
            for x, z in ((11, 18), (19, 18), (11, 26), (19, 26)):
                for y in range(ct + 1, ct + 5):
                    d.set(x, y, z, "polished_andesite")
                d.set(x, ct + 5, z, wallb("stone_brick_wall"))
                d.set(x, ct + 6, z, "lightning_rod[facing=up,powered=false,waterlogged=false]")
            d.fill(12, ct, 19, 18, ct, 25, S)
            if L == 5:
                spire(d, 15, 22, ct + 1, 3.5, 22, "deepslate_tiles", top=wallb("stone_brick_wall"))
                for y in range(ct + 23, ct + 26):
                    d.set(15, y, 22, wallb("stone_brick_wall"))
                d.set(14, ct + 24, 22, wallb("stone_brick_wall"))
                d.set(16, ct + 24, 22, wallb("stone_brick_wall"))
                # spire lucarnes (gabled dormers) on the four faces
                for x, z, f in ((15, 18, "north"), (15, 26, "south"), (11, 22, "west"), (19, 22, "east")):
                    ox, oz = D4[f]
                    bx, bz = 15 + ox * 2, 22 + oz * 2
                    d.set(bx, ct + 3, bz, "dark_oak_trapdoor[facing=%s,half=bottom,open=true,powered=false,"
                          "waterlogged=false]" % f)
        # interior: choir stalls, altar, lectern, organ pipes
        for z in range(27, 30):
            d.chair(12, 2, z, "west", "dark_oak")
            d.chair(18, 2, z, "east", "dark_oak")
        d.rug(15, 18, 15, 29, 2, ("red_carpet",), "plain")
        d.set(14, 2, 30, "chiseled_stone_bricks")
        d.set(15, 2, 30, "chiseled_quartz_block")
        d.set(16, 2, 30, "chiseled_stone_bricks")
        d.candle(14, 3, 30, 3)
        d.set(15, 3, 30, "gold_block" if L >= 4 else "candle[candles=4,lit=false,waterlogged=false]")
        d.candle(16, 3, 30, 3)
        d.set(13, 2, 21, "lectern[facing=south,has_book=true,powered=false]")
        for x0, step in ((3, 1), (27, -1)):
            d.set(x0, 2, 22, "chiseled_stone_bricks")
            d.candle(x0, 3, 22, 4)
            d.chair(x0 + 2 * step, 2, 21, "west" if step > 0 else "east", "dark_oak")
            d.chair(x0 + 2 * step, 2, 23, "west" if step > 0 else "east", "dark_oak")
            d.lamp(x0 + 3 * step, 12, 22)
            d.set(x0 + 3 * step, 13, 22, CHAIN)
            d.set(x0 + 3 * step, 14, 22, CHAIN)
            d.set(x0 + 3 * step, 15, 22, CHAIN)
            d.set(x0 + 3 * step, 16, 22, S)
        chandelier(d, 15, 22, ct - 2, 10)
    else:
        # L1/L2 sanctuary at the east end of the nave
        d.fill(12, 2, ne - 2, 18, 2, ne - 1, slab("polished_andesite_slab"))
        d.set(14, 3, ne - 1, "chiseled_stone_bricks")
        d.set(15, 3, ne - 1, "chiseled_quartz_block")
        d.set(16, 3, ne - 1, "chiseled_stone_bricks")
        d.candle(14, 4, ne - 1, 3)
        d.candle(16, 4, ne - 1, 3)
        d.set(13, 3, ne - 2, "lectern[facing=north,has_book=true,powered=false]")
        for x in (14, 15, 16):                                          # east window
            lancet(d, x, ne, 5, 13 if x == 15 else 11)
    # ---------------- nave roof and west front -------------
    d.gable(11, 1, 19, ne, 17, "z", "deepslate_tile_stairs", "deepslate_tile_slab", S, 1)
    d.set(15, 22, 0, wallb("stone_brick_wall"))     # cross on the west gable
    d.set(15, 23, 0, wallb("stone_brick_wall"))
    # portal: two doors with a trumeau, gabled hood on shafts
    d.door(14, 2, 1, "south", "dark_oak", "left")
    d.door(16, 2, 1, "south", "dark_oak", "right")
    d.set(15, 2, 1, "chiseled_stone_bricks")
    d.set(15, 3, 1, "polished_andesite")
    d.fill(14, 4, 1, 16, 4, 1, "chiseled_stone_bricks")
    for x in (13, 17):
        for y in range(2, 6):
            d.set(x, y, 0, wallb("stone_brick_wall"))
    d.set(13, 6, 0, stair(ST, "east"))
    d.set(14, 6, 0, S)
    d.set(14, 7, 0, stair(ST, "east"))
    d.set(15, 6, 0, S)
    d.set(15, 7, 0, S)
    d.set(15, 8, 0, slab("stone_brick_slab"))
    d.set(16, 6, 0, S)
    d.set(16, 7, 0, stair(ST, "west"))
    d.set(17, 6, 0, stair(ST, "west"))
    for x in (14, 15, 16):
        d.set(x, 5, 0, stair(ST, "north", "top"))
    if L >= 2:
        rose(d, 15, 12, 1, 3, "chiseled_stone_bricks")
    else:
        for x in (13, 15, 17):
            lancet(d, x, 1, 9, 14 if x == 15 else 13)
    # nave furnishing: pews either side of the central walk, font, chandeliers, hut by the entrance
    d.hut(12, 2, 2)
    d.set(17, 2, 3, "water_cauldron[level=3]")
    d.set(18, 2, 3, "chiseled_stone_bricks")
    d.rug(15, 3, 15, ne - (3 if not cross else 0), 2, ("red_carpet",), "plain")
    pz = list(range(5, ne - 2, 2)) if not cross else list(range(5, 17, 2))
    pews(d, 12, 14, pz, 2, "dark_oak")
    pews(d, 16, 18, pz, 2, "dark_oak")
    for z in range(5, ne - 1, 4):
        chandelier(d, 15, z, 20, 11)
    # ---------------- buttresses (L4: flying) -------------
    if L >= 4:
        for z in (11, 14):
            hc_buttress(d, 4, z, "west", 10, 10, 14)
            hc_buttress(d, 26, z, "east", 10, 20, 14)
        for z in (28, 30):
            hc_buttress(d, 10, z, "west", 12)
            hc_buttress(d, 20, z, "east", 12)
        for x in (12, 18):
            hc_buttress(d, x, 32, "south", 12)
        for x in (2, 28):
            for z in (18, 26):
                hc_buttress(d, x + (-1 if x == 2 else 1), z, "west" if x == 2 else "east", 13)
    elif aisles:
        for z in (11, 14):
            for x, out in ((5, "west"), (25, "east")):
                for y in range(2, 8):
                    d.set(x, y, z, S)
                d.set(x, 8, z, slab("stone_brick_slab"))
    # ---------------- churchyard -------------
    if L >= 5:
        for x, z in ((1, 9), (29, 9), (1, 30), (29, 30), (8, 30), (22, 30)):
            yew(d, x, z, 2)
        for z in (12, 15):
            for x in (1, 29):
                d.set(x, 2, z, "mossy_stone_bricks")
                d.set(x, 3, z, slab("mossy_stone_brick_slab"))
        for x in (3, 27):
            d.set(x, 2, 1, "polished_andesite")
            d.set(x, 3, 1, lantern(False))
    # reserve the west towers last so nothing drawn above leaks into them
    for tx in HC_TX:
        d.reserve(tx, 1, HC_TZ, tx + HC_TW - 1, HC_SIZE[1] - 1, HC_TZ + HC_TW - 1)
        d.child_hut(tx + HC_WHUT[0], 1 + HC_WHUT[1], HC_TZ + HC_WHUT[2], CATH_WING)
    return d


def yew(d, x, z, y, leaves="oak_leaves", trunk="spruce_log"):
    """Small clipped churchyard tree: trunk with a rounded crown, only into free cells."""
    L = f"{leaves}[distance=1,persistent=true,waterlogged=false]"
    d.set(x, y, z, log(trunk))
    d.set(x, y + 1, z, log(trunk))
    for yy, r in ((y + 1, 1), (y + 2, 1), (y + 3, 0)):
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                xx, zz = x + dx, z + dz
                if (dx or dz or yy > y + 1) and d.bp.inside(xx, yy, zz) and d.air(xx, yy, zz) \
                        and not (abs(dx) == abs(dz) == 1 and yy == y + 1):
                    d.set(xx, yy, zz, L)


def rose_x(d, x, cy, cz, R, frame, cols=("blue", "red", "yellow")):
    """Rose window in the wall plane x (transept gable ends)."""
    for dz in range(-R, R + 1):
        for dy in range(-R, R + 1):
            r = math.hypot(dz, dy)
            if r > R + 0.5:
                continue
            if r < 0.6:
                c = "yellow"
            elif r > R - 0.5:
                if dz == 0 or dy == 0 or abs(dz) == abs(dy):
                    d.set(x, cy + dy, cz + dz, frame)
                    continue
                c = cols[0]
            elif r > R - 1.5:
                c = cols[1]
            else:
                c = cols[2] if (dz + dy) % 2 else cols[0]
            d.set(x, cy + dy, cz + dz, f"{c}_stained_glass_pane")



# ---------------------------------------------------------------------------- Cascadia: stave church close
CC_SIZE = (27, 46, 31)
CC_TX, CC_TZ, CC_TW = (0, 20), 1, 7           # timber belfries (wings)
CC_WHUT = (1, 1, 5)
CC_SHAFT = {1: 9, 2: 11, 3: 13, 4: 14, 5: 15}  # belfry shaft top (local y)


def steep_gable(d, x1, z1, x2, z2, y, stairs, body, end, axis="z", overhang=1, ridge=None):
    """Very steep gable (rises 2 per step, like a stave-church roof) over walls whose tops are at y-1."""
    o = overhang
    lo, hi, a1, a2 = (x1, x2, z1, z2) if axis == "z" else (z1, z2, x1, x2)
    L, H = lo - o, hi + o
    n = H - L + 1
    top = y
    for i in range(n):
        w = L + i
        k = min(i, n - 1 - i)
        yy = y - 1 + 2 * k - (o - 1 if o > 1 else 0)
        mid = n % 2 == 1 and i == n // 2
        if axis == "z":
            face = "east" if i < n / 2 else "west"
        else:
            face = "south" if i < n / 2 else "north"
        for a in range(a1 - o, a2 + o + 1):
            x, z = (w, a) if axis == "z" else (a, w)
            if mid:
                d.set(x, yy - 1, z, body)
                d.set(x, yy, z, ridge or body)
            else:
                d.set(x, yy, z, stair(stairs, face))
                if k >= 1:
                    d.set(x, yy - 1, z, body)
        top = max(top, yy)
        if lo <= w <= hi:
            for a in (a1, a2):
                x, z = (w, a) if axis == "z" else (a, w)
                for y2 in range(y, yy - (0 if mid else 1)):
                    if d.air(x, y2, z):
                        d.set(x, y2, z, end)
    return top


def cc_wing(rel, L):
    """Free-standing timber belfry: log base with a shingled skirt, open bell stage, needle spire."""
    d = Design("Cascadia", rel, (CC_TW, 40, CC_TW), gy=0, paving="cobblestone")
    n = CC_TW - 1
    T = CC_SHAFT[L]
    R = "dark_oak_stairs"
    d.fill(0, 1, 0, n, 1, n, "mossy_cobblestone")                  # river-rock footing
    d.box(0, 2, 0, n, 5, n, log("stripped_spruce_log"))
    for x, z in ((0, 0), (n, 0), (0, n), (n, n)):
        d.fill(x, 1, z, x, 5, z, log("spruce_log"))
    d.clear(1, 1, 1, n - 1, 5, n - 1)
    d.fill(1, 0, 1, n - 1, 0, n - 1, "spruce_planks")
    d.door(3, 1, 0, "south", "spruce")
    for x, z in ((0, 3), (n, 3)):
        d.window(x, 3, z, x, 4, z)
    d.hut(*CC_WHUT)
    d.set(5, 1, 5, stair("spruce_stairs", "south"))
    d.lamp(2, 5, 2)

    def ring(y, r, c=3):
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                if max(abs(dx), abs(dz)) != r:
                    continue
                if abs(dx) == abs(dz):
                    sh, f = ("outer_left" if (dx < 0) == (dz < 0) else "outer_right"), ("south" if dz < 0 else "north")
                elif abs(dz) == r:
                    sh, f = "straight", ("south" if dz < 0 else "north")
                else:
                    sh, f = "straight", ("east" if dx < 0 else "west")
                d.set(c + dx, y, c + dz, stair(R, f, "bottom", sh))
    ring(6, 3)
    # shaft (5x5) with the ladder
    for y in range(6, T + 1):
        for x in range(1, 6):
            for z in range(1, 6):
                edge = x in (1, 5) or z in (1, 5)
                d.set(x, y, z, ("spruce_planks" if (x + z) % 2 else log("stripped_spruce_log")) if edge else AIR)
        for x, z in ((1, 1), (5, 1), (1, 5), (5, 5)):
            d.set(x, y, z, log("spruce_log"))
    d.fill(2, 6, 2, 4, 6, 4, "spruce_planks")
    for y in range(1, 6):
        d.set(3, y, 5, log("spruce_log"))
    for y in range(1, T):
        d.set(3, y, 4, "ladder[facing=north,waterlogged=false]")
    d.set(3, 9, 1, "glass_pane")
    # bell stage
    d.fill(2, T, 2, 4, T, 4, "spruce_planks")
    d.set(3, T, 4, "spruce_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
    for y in range(T + 1, T + 4):
        for x, z in ((1, 1), (5, 1), (1, 5), (5, 5)):
            d.set(x, y, z, log("spruce_log"))
    for i in range(2, 5):
        for x, z, f in ((i, 1, "north"), (i, 5, "south"), (1, i, "west"), (5, i, "east")):
            d.set(x, T + 1, z, fence("spruce_fence"))
            d.set(x, T + 3, z, stair("spruce_stairs", OPP[f], "top") if i != 3 else "spruce_planks")
    d.fill(2, T + 3, 3, 4, T + 3, 3, log("dark_oak_log", "x"))
    d.item(3, T + 2, 3, "bell[attachment=ceiling,facing=north,powered=false]")
    d.fill(1, T + 4, 1, 5, T + 4, 5, "dark_oak_planks")
    ring(T + 4, 3)
    h = {1: 3, 2: 4, 3: 6, 4: 9, 5: 12}[L]
    spire(d, 3, 3, T + 5, 1.6, h, "dark_oak_planks", octagon=False)
    d.set(3, T + 5 + h, 3, "lightning_rod[facing=up,powered=false,waterlogged=false]" if L >= 3
          else fence("dark_oak_fence"))
    return d


def dragon(d, x, y, z, out):
    """Carved dragon-head finial at a gable apex, projecting toward `out`."""
    ox, oz = D4[out]
    d.set(x, y, z, fence("dark_oak_fence"))
    d.set(x, y + 1, z, stair("dark_oak_stairs", OPP[out], "top"))
    if d.bp.inside(x + ox, y + 1, z + oz) and d.air(x + ox, y + 1, z + oz):
        d.set(x + ox, y + 1, z + oz, stair("dark_oak_stairs", out, "top"))


def cc_cathedral(rel, L):
    d = Design("Cascadia", rel, CC_SIZE, gy=1, paving="grass_block")
    W, R, RB = log("stripped_spruce_log"), "dark_oak_stairs", "dark_oak_planks"
    TR = log("stripped_spruce_log")
    # path from the gate
    d.fill(12, 1, 0, 14, 1, 10, "gravel")
    # ---------------- gallery (svalgang), L4+
    if L >= 4:
        d.fill(5, 1, 9, 21, 1, 27, "cobblestone")
        for x in range(5, 22):
            for z in range(9, 28):
                if x in (5, 21) or z in (9, 27):
                    d.set(x, 2, z, "spruce_planks")
                    d.set(x, 3, z, fence("spruce_fence"))
                    d.set(x, 4, z, "stripped_spruce_wood[axis=y]" if (x + z) % 3 == 0 else
                          stair("spruce_stairs", "north" if z == 9 else "south" if z == 27 else
                                "west" if x == 5 else "east", "top"))
                    if (x + z) % 3 == 0 or (x in (5, 21) and z in (9, 27)):
                        d.set(x, 3, z, TR)
                        d.set(x, 2, z, TR)
                else:
                    d.set(x, 1, z, "spruce_planks")
        for (x, z) in ((13, 9), (13, 27)):
            d.set(x, 2, z, AIR)
            d.set(x, 3, z, AIR)
            d.set(x, 4, z, stair("spruce_stairs", "south" if z == 9 else "north", "top"))
        for (x, z) in ((5, 18), (21, 18)):
            d.set(x, 2, z, AIR)
            d.set(x, 3, z, AIR)
        # lean-to roof of the gallery
        for x in range(4, 23):
            for z in range(8, 29):
                ring = min(x - 4, 22 - x, z - 8, 28 - z)
                if ring <= 2:
                    y = 5 + ring
                    if ring == 0:
                        y = 4
                    elif ring == 1:
                        y = 5
                    else:
                        y = 6
                    if x in (4, 22) and z in (8, 28):
                        continue
                    if min(x - 4, 22 - x) <= min(z - 8, 28 - z):
                        f = "east" if x < 13 else "west"
                    else:
                        f = "south" if z < 18 else "north"
                    d.set(x, y, z, stair(R, f))
    # ---------------- aisles (lower tier), L2+
    if L >= 2:
        d.fill(7, 1, 10, 19, 1, 24, "spruce_planks")
        for x in range(7, 20):
            for z in range(10, 25):
                if x in (7, 19) or z in (10, 24):
                    d.fill(x, 2, z, x, 7, z, "spruce_planks")
        for x, z in ((7, 10), (19, 10), (7, 24), (19, 24)):
            d.fill(x, 2, z, x, 7, z, TR)
        for x in range(7, 20):
            for z in (10, 24):
                d.set(x, 2, z, "cobblestone")
        for z in range(10, 25):
            for x in (7, 19):
                d.set(x, 2, z, "cobblestone")
        d.clear(8, 2, 11, 18, 7, 23)
        for z in (13, 17, 21):                      # small round-headed windows
            for x in (7, 19):
                d.set(x, 5, z, "glass_pane")
        for x in range(6, 21):                      # lean-to roof
            for z in range(9, 26):
                ring = min(x - 6, 20 - x, z - 9, 25 - z)
                if ring <= 2:
                    y = 7 + ring
                    if (x in (6, 20)) and (z in (9, 25)):
                        continue
                    if min(x - 6, 20 - x) <= min(z - 9, 25 - z):
                        f = "east" if x < 13 else "west"
                    else:
                        f = "south" if z < 17 else "north"
                    d.set(x, y, z, stair(R, f))
                    if ring >= 1:
                        d.set(x, y - 1, z, RB)
    # ---------------- nave (mast hall)
    d.fill(10, 1, 12, 16, 1, 22, "spruce_planks")
    for x in range(9, 18):
        for z in range(11, 24):
            if x in (9, 17) or z in (11, 23):
                d.fill(x, 2, z, x, 13, z, W)
    for x, z in ((9, 11), (17, 11), (9, 23), (17, 23)):
        d.fill(x, 2, z, x, 13, z, log("spruce_log"))
    for x in range(9, 18):
        for z in (11, 23):
            d.set(x, 2, z, "cobblestone")
    for z in range(11, 24):
        for x in (9, 17):
            d.set(x, 2, z, "cobblestone")
    d.clear(10, 2, 12, 16, 13, 22)
    if L >= 2:                                     # masts and arcade toward the aisles
        for x in (9, 17):
            for z in range(12, 23):
                for y in range(2, 9):
                    d.set(x, y, z, TR if (z - 12) % 3 == 0 else (AIR if y < 8 else stair(
                        "spruce_stairs", "east" if x == 9 else "west", "top") if y == 8 else AIR))
        for z in range(12, 23, 3):
            for x in (9, 17):
                d.set(x, 9, z, TR)
    for z in (13, 17, 21):                         # clerestory "eye" windows
        for x in (9, 17):
            d.set(x, 11, z, "glass_pane")
    for x in (11, 15):
        d.set(x, 11, 11, "glass_pane")
    nr = steep_gable(d, 9, 11, 17, 23, 14, R, RB, W, "z", 1)
    # carved west portal
    pz = 11 if L == 1 else 10
    if pz == 10:
        d.clear(13, 2, 11, 13, 3, 11)
        d.set(13, 4, 11, TR)
    d.door(13, 2, pz, "south", "spruce")
    for y in range(2, 5):
        d.set(12, y, pz - 1, TR)
        d.set(14, y, pz - 1, TR)
    d.set(12, 5, pz - 1, stair("dark_oak_stairs", "east"))
    d.set(13, 5, pz - 1, RB)
    d.set(14, 5, pz - 1, stair("dark_oak_stairs", "west"))
    d.set(13, 6, pz - 1, slab("dark_oak_slab"))
    d.set(13, 4, pz, TR)
    d.set(13, 1, pz - 1, "spruce_planks")
    # ---------------- chancel + apse, L3+
    if L >= 3:
        d.fill(10, 1, 23, 16, 1, 27, "spruce_planks")
        for x in range(10, 17):
            for z in range(24, 28):
                if x in (10, 16):
                    d.fill(x, 2, z, x, 9, z, W)
        d.clear(11, 2, 23, 15, 9, 27)
        for y in range(10, 14):
            for x in range(10, 17):
                d.set(x, y, 23, W)
        steep_gable(d, 10, 24, 16, 27, 10, R, RB, W, "z", 1)
        for x in range(11, 16):                    # apse
            for z in range(27, 31):
                r = math.hypot(x - 13, z - 27)
                if 1.6 < r <= 2.6 and z >= 28:
                    d.fill(x, 2, z, x, 8, z, W)
                    d.set(x, 1, z, "cobblestone")
                elif r <= 1.6:
                    d.set(x, 1, z, "spruce_planks")
        for z in range(27, 30):
            for x in range(11, 16):
                if math.hypot(x - 13, z - 27) <= 1.6:
                    d.clear(x, 2, z, x, 8, z)
        for k, (rr, y) in enumerate(((3.0, 9), (2.2, 10), (1.5, 11), (0.6, 12))):
            for x in range(10, 17):
                for z in range(26, 31):
                    if math.hypot(x - 13, z - 27) <= rr and z >= 27 and d.air(x, y, z):
                        dx, dz = x - 13, z - 27
                        f = ("east" if dx < 0 else "west") if abs(dx) > abs(dz) else "north"
                        d.set(x, y, z, stair(R, f) if rr > 1 else RB)
        d.set(13, 13, 28, fence("spruce_fence"))
        d.set(13, 4, 29, "yellow_stained_glass_pane")
        # altar in the apse
        d.set(13, 2, 28, "stripped_spruce_wood[axis=y]")
        d.candle(13, 3, 28, 4)
        d.set(12, 2, 27, "spruce_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
        d.set(14, 2, 27, "spruce_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
        d.lamp(13, 8, 28)
        d.set(12, 2, 25, "lectern[facing=south,has_book=true,powered=false]")
        for z in (24, 26):
            d.chair(11, 2, z, "west", "spruce")
            d.chair(15, 2, z, "east", "spruce")
        alt_z = None
    else:
        d.set(13, 2, 22, "stripped_spruce_wood[axis=y]")
        d.candle(13, 3, 22, 4)
        d.set(13, 2, 21, AIR)
        d.set(11, 2, 21, "lectern[facing=south,has_book=true,powered=false]")
        d.set(13, 9, 23, "yellow_stained_glass_pane")
    # pews, hut, lighting
    d.hut(10, 2, 12)
    d.rug(13, 12, 13, 22 if L >= 3 else 20, 2, ("red_carpet",), "plain")
    pz = [14, 16, 18, 20] if L >= 3 else [14, 16, 18]
    pews(d, 10, 12, pz, 2, "spruce")
    pews(d, 14, 16, pz, 2, "spruce")
    for z in (14, 18, 22):
        chandelier(d, 13, z, nr - 3, 10)
    if L >= 2:
        for z in (13, 19):
            d.lamp(8, 6, z)
            d.lamp(18, 6, z)
    # ---------------- roof turret (takrytter), stacked tiers
    cz = 17
    th = {1: 23, 2: 24, 3: 26, 4: 27, 5: 28}[L]
    for y in range(nr - 2, th + 1):
        for x in range(12, 15):
            for z in range(cz - 1, cz + 2):
                d.set(x, y, z, RB if (x, z) != (13, cz) else AIR)
    for x, z in ((12, cz - 1), (14, cz - 1), (12, cz + 1), (14, cz + 1)):
        d.fill(x, th - 2, z, x, th, z, TR)
    for x, z in ((13, cz - 1), (13, cz + 1), (12, cz), (14, cz)):
        d.set(x, th - 1, z, fence("spruce_fence"))
        d.set(x, th - 2, z, fence("spruce_fence"))
    def skirt(y, r):
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                if max(abs(dx), abs(dz)) != r:
                    continue
                x, z = 13 + dx, cz + dz
                if abs(dx) == abs(dz):
                    sh = "outer_left" if (dx < 0) == (dz < 0) else "outer_right"
                    f = "south" if dz < 0 else "north"
                elif abs(dz) == r:
                    sh, f = "straight", "south" if dz < 0 else "north"
                else:
                    sh, f = "straight", "east" if dx < 0 else "west"
                d.set(x, y, z, stair(R, f, "bottom", sh))
    skirt(th + 1, 2)
    d.fill(12, th + 1, cz - 1, 14, th + 1, cz + 1, RB)
    if L >= 4:
        skirt(nr + 1, 2)
    top = th + 2
    if L >= 3:
        for y in range(th + 2, th + 4):
            d.fill(12, y, cz - 1, 14, y, cz + 1, RB)
        skirt(th + 3, 2) if L >= 4 else None
        d.fill(12, th + 4, cz - 1, 14, th + 4, cz + 1, RB)
        skirt(th + 4, 1)
        d.set(13, th + 4, cz, RB)
        top = th + 5
    if L == 5:
        for y in range(top, top + 10):
            d.set(13, y, cz, RB)
            if y < top + 4:
                for x, z, f in ((12, cz, "east"), (14, cz, "west"), (13, cz - 1, "south"), (13, cz + 1, "north")):
                    d.set(x, y, z, stair(R, f))
        d.set(13, top + 10, cz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        top += 10
    else:
        d.set(13, top, cz, fence("dark_oak_fence"))
    # dragon heads on the gables (L5), crosses on ridges
    if L >= 5:
        dragon(d, 13, nr + 1, 10, "north")
        dragon(d, 13, nr + 1, 24, "south")
    else:
        d.set(13, nr + 1, 10, fence("spruce_fence"))
        d.set(13, nr + 2, 10, fence("spruce_fence"))
    # ---------------- yard: rail fence, lanterns, graves
    if L >= 3:
        for x in range(0, 27):
            for z in (7,):
                if x in range(6, 21) and not 11 <= x <= 15:
                    d.set(x, 2, z, fence("spruce_fence"))
        for x in (11, 15):
            d.set(x, 2, 7, log("stripped_spruce_log"))
            d.set(x, 3, 7, lantern(False))
    if L >= 5:
        for x in (1, 3, 23, 25):
            for z in (12, 16, 20, 24):
                d.set(x, 2, z, "mossy_cobblestone_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
                d.set(x, 1, z - 1, "podzol")
        for x, z in ((2, 28), (24, 28), (8, 29), (18, 29)):
            yew(d, x, z, 2, "spruce_leaves", "spruce_log")
    for tx in CC_TX:
        d.reserve(tx, 1, CC_TZ, tx + CC_TW - 1, 40, CC_TZ + CC_TW - 1)
        d.child_hut(tx + CC_WHUT[0], 1 + CC_WHUT[1], CC_TZ + CC_WHUT[2], CATH_WING)
    return d



# ---------------------------------------------------------------------------- Neoterra: crown cathedral
NC_SIZE = (33, 40, 33)
NC_C = (16, 18)                                 # centre of the crown
NC_TX, NC_TZ, NC_TW = (1, 27), 1, 5            # campanile (wings)
NC_WHUT = (1, 1, 3)
NC_H = {1: 12, 2: 16, 3: 20, 4: 24, 5: 28}      # rib height
NC_TOP = {1: 13, 2: 17, 3: 21, 4: 25, 5: 29}    # campanile height (local)
NC_RIBS = 12


def nc_wing(rel, L):
    """Slim white campanile: glass lobby, four quartz shafts tied by rings, open bell cage and a cross."""
    d = Design("Neoterra", rel, (NC_TW, 40, NC_TW), gy=0, paving="smooth_stone")
    n, T = NC_TW - 1, NC_TOP[L]
    d.fill(0, 1, 0, n, 3, n, "light_blue_stained_glass_pane")
    d.clear(1, 1, 1, n - 1, 3, n - 1)
    d.fill(1, 0, 1, n - 1, 0, n - 1, "polished_diorite")
    for x, z in ((0, 0), (n, 0), (0, n), (n, n)):
        d.fill(x, 1, z, x, T, z, "quartz_pillar[axis=y]")
    d.door(2, 1, 0, "south", "birch")
    d.hut(*NC_WHUT)
    d.set(3, 1, 3, "potted_bamboo")
    d.fill(0, 4, 0, n, 4, n, "smooth_quartz")
    d.set(2, 3, 2, "sea_lantern")
    d.fill(1, 3, 1, 3, 3, 3, "smooth_quartz_slab[type=top,waterlogged=false]")
    d.set(2, 3, 2, "sea_lantern")
    for y in range(8, T - 3, 4):                     # tie rings
        for i in range(1, n):
            for x, z in ((i, 0), (i, n), (0, i), (n, i)):
                d.set(x, y, z, "white_concrete" if y % 8 else "cyan_terracotta")
    for y in range(5, T - 3):                         # slender central mast with the bell rope chain
        d.set(2, y, 2, "iron_bars")
    # bell cage
    for i in range(1, n):
        for x, z in ((i, 0), (i, n), (0, i), (n, i)):
            d.set(x, T - 3, z, "white_concrete")
            d.set(x, T, z, "smooth_quartz")
    d.fill(1, T, 1, 3, T, 3, "smooth_quartz")
    d.item(2, T - 1, 2, "bell[attachment=ceiling,facing=north,powered=false]")
    d.set(2, T - 3, 2, "white_concrete")
    d.set(2, T - 2, 2, "end_rod[facing=up]")
    # cross
    for y in range(T + 1, T + 5):
        d.set(2, y, 2, "white_concrete")
    d.set(1, T + 3, 2, "white_concrete")
    d.set(3, T + 3, 2, "white_concrete")
    return d


def nc_radius(t, H):
    tw = 0.58 * H
    Rb, Rw, Rt = 12.0, 7.0 + (28 - H) / 7, 11.5 - (28 - H) / 10
    if t <= tw:
        return Rw + (Rb - Rw) * ((tw - t) / tw) ** 2
    return Rw + (Rt - Rw) * ((t - tw) / (H - tw)) ** 1.6


def nc_cathedral(rel, L):
    d = Design("Neoterra", rel, NC_SIZE, gy=1, paving="smooth_stone")
    cx, cz = NC_C
    H = NC_H[L]
    y0 = 2
    glass_top = H - 4
    cols = ("light_blue", "light_blue", "blue", "cyan", "light_blue", "white", "blue")
    # plaza paving
    for x in range(33):
        for z in range(33):
            if (x + z) % 2 == 0 and math.hypot(x - cx, z - cz) > 13:
                d.set(x, 1, z, "white_concrete")
    # reflecting pool ring (L3+)
    if L >= 3:
        for x in range(33):
            for z in range(33):
                r = math.hypot(x - cx, z - cz)
                if 13.2 <= r <= 14.8 and not (14 <= x <= 18 and z < cz):
                    d.set(x, 1, z, "water")
                    d.set(x, 0, z, "light_blue_concrete")
                elif 12.5 <= r < 13.2 or 14.8 < r <= 15.5:
                    if not (14 <= x <= 18 and z < cz):
                        d.set(x, 1, z, "smooth_quartz")
    # shell: ribs and stained glass
    ang = [2 * math.pi * k / NC_RIBS for k in range(NC_RIBS)]
    for t in range(0, H + 1):
        r1 = nc_radius(t, H)
        r2 = nc_radius(min(H, t + 1), H)
        lo, hi = min(r1, r2) - 0.5, max(r1, r2) + 0.5
        for x in range(33):
            for z in range(33):
                dx, dz = x - cx, z - cz
                dd = math.hypot(dx, dz)
                if not (lo <= dd <= hi):
                    continue
                phi = math.atan2(dz, dx)
                da = min(abs((phi - a + math.pi) % (2 * math.pi) - math.pi) for a in ang)
                rib = da * dd <= (0.85 if t <= glass_top else 0.7)
                y = y0 + t
                if rib:
                    d.set(x, y, z, "white_concrete")
                elif t <= glass_top:
                    d.set(x, y, z, f"{cols[(x * 3 + y + z * 5) % len(cols)]}_stained_glass")
    # floor and interior air
    for x in range(33):
        for z in range(33):
            dd = math.hypot(x - cx, z - cz)
            if dd < 11.6:
                d.set(x, 1, z, "polished_diorite" if (int(dd) % 3) else "white_concrete")
    # glass roof inside the crown
    rg = nc_radius(glass_top, H)
    for x in range(33):
        for z in range(33):
            dd = math.hypot(x - cx, z - cz)
            if dd <= rg - 0.4 and d.air(x, y0 + glass_top, z):
                d.set(x, y0 + glass_top, z, "light_blue_stained_glass" if dd > 2 else "white_stained_glass")
    # entrance vestibule (north)
    d.fill(13, 1, 2, 19, 1, 9, "polished_diorite")
    d.box(13, 2, 3, 19, 5, 8, "smooth_quartz")
    d.clear(14, 2, 3, 18, 5, 9)
    for x in (14, 15, 17, 18):
        for y in (2, 3, 4):
            d.set(x, y, 3, "light_gray_stained_glass_pane")
    d.set(16, 4, 3, "light_gray_stained_glass_pane")
    d.double_door(15, 2, 3, "x", "south", "birch")
    d.set(17, 2, 3, AIR)
    d.set(17, 3, 3, AIR)
    d.door(17, 2, 3, "south", "birch", "right")
    d.set(16, 2, 3, "smooth_quartz")
    d.set(16, 3, 3, "smooth_quartz")
    d.fill(12, 6, 2, 20, 6, 9, "smooth_quartz_slab[type=bottom,waterlogged=false]")
    d.fill(13, 5, 2, 19, 5, 2, "smooth_quartz")
    for x in (13, 19):
        d.set(x, 2, 2, "smooth_quartz")
    d.fill(14, 5, 3, 18, 5, 8, "smooth_quartz")
    d.clear(14, 2, 4, 18, 4, 9)
    for x in (14, 18):
        for z in (5, 7):
            d.set(x, 4, z, "sea_lantern")
    # sanctuary: round altar platform, concentric pews
    for x in range(cx - 2, cx + 3):
        for z in range(cz - 2, cz + 3):
            if math.hypot(x - cx, z - cz) <= 2.3:
                d.set(x, 2, z, "smooth_quartz_slab[type=bottom,waterlogged=false]")
    d.set(cx, 2, cz, "smooth_quartz")
    d.set(cx, 3, cz + 0, "white_carpet")
    d.candle(cx, 3, cz, 4, "white")
    d.set(cx, 2, cz + 1, "smooth_quartz")
    d.set(cx, 3, cz + 1, "end_rod[facing=up]")
    d.set(cx, 2, cz - 2, "lectern[facing=north,has_book=true,powered=false]")
    rows = (4.5, 6.5, 8.5) if L >= 2 else (4.5, 6.5)
    used = set()
    for rr in rows:
        nseg = int(2 * math.pi * rr * 1.2)
        for k in range(nseg):
            a = 2 * math.pi * k / nseg
            x, z = cx + round(rr * math.cos(a)), cz + round(rr * math.sin(a))
            dx, dz = x - cx, z - cz
            if abs(dx) <= 1 or abs(dz) <= 1 or (x, z) in used:
                continue
            used.add((x, z))
            back = ("east" if dx > 0 else "west") if abs(dx) >= abs(dz) else ("south" if dz > 0 else "north")
            if d.air(x, 2, z):
                d.chair(x, 2, z, back, "birch")
    d.rug(cx, cz - 10, cx, cz - 3, 2, ("light_blue_carpet",), "plain")
    d.hut(14, 2, 9)
    # hanging lights: end-rod clusters on chains from the glass roof
    for a in range(0, 360, 90 if L < 4 else 45):
        rr = 5.5
        x, z = cx + round(rr * math.cos(math.radians(a + 22))), cz + round(rr * math.sin(math.radians(a + 22)))
        for y in range(y0 + glass_top - 4, y0 + glass_top):
            d.set(x, y, z, CHAIN)
        d.set(x, y0 + glass_top - 5, z, "sea_lantern" if L >= 3 else lantern(True))
    # central light shaft / cross above the roof (L4+)
    if L >= 4:
        for y in range(y0 + glass_top + 1, y0 + H + (5 if L == 5 else 2)):
            d.set(cx, y, cz, "white_concrete")
        yc = y0 + H + (3 if L == 5 else 0)
        if L == 5:
            d.set(cx - 1, yc, cz, "white_concrete")
            d.set(cx + 1, yc, cz, "white_concrete")
        d.set(cx, y0 + H + (5 if L == 5 else 2), cz, "end_rod[facing=up]")
    # evangelists on the forecourt (L5): four bronze figures
    if L >= 5:
        for x, z in ((10, 6), (22, 6), (11, 3), (21, 3)):
            d.set(x, 2, z, "polished_andesite")
            d.set(x, 3, z, "oxidized_copper")
            d.set(x, 4, z, "oxidized_cut_copper")
            d.set(x, 5, z, "oxidized_copper")
    # planters along the approach
    if L >= 2:
        for x in (12, 20):
            for z in (0, 1):
                d.set(x, 1, z, "moss_block")
                d.set(x, 2, z, "potted_bamboo" if z else "flowering_azalea")
    for tx in NC_TX:
        d.reserve(tx, 1, NC_TZ, tx + NC_TW - 1, 39, NC_TZ + NC_TW - 1)
        d.child_hut(tx + NC_WHUT[0], 1 + NC_WHUT[1], NC_TZ + NC_WHUT[2], CATH_WING)
    return d



# ================================================================================================ COLOSSUS
class Sculpt:
    """Voxel sculpting buffer: ellipsoid sections, limbs (chains of balls) and boxes; committed as a shell."""

    def __init__(self):
        self.c = {}

    def put(self, x, y, z, block):
        self.c[(x, y, z)] = block

    def ell(self, cx, cz, y1, y2, fx, fz, block, only=None):
        y1, y2 = int(round(y1)), int(round(y2))
        for y in range(y1, y2 + 1):
            t = (y - y1) / max(1, y2 - y1)
            hx, hz = fx(t) if callable(fx) else fx, fz(t) if callable(fz) else fz
            for x in range(int(cx - hx) - 2, int(cx + hx) + 3):
                for z in range(int(cz - hz) - 2, int(cz + hz) + 3):
                    if ((x - cx) / (hx + 0.5)) ** 2 + ((z - cz) / (hz + 0.5)) ** 2 <= 1.0:
                        if only is None or only(x, y, z):
                            self.put(x, y, z, block(x, y, z) if callable(block) else block)

    def ball(self, cx, cy, cz, r, block):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            for y in range(int(cy - r) - 1, int(cy + r) + 2):
                for z in range(int(cz - r) - 1, int(cz + r) + 2):
                    if (x - cx) ** 2 + (y - cy) ** 2 + (z - cz) ** 2 <= (r + 0.45) ** 2:
                        self.put(x, y, z, block(x, y, z) if callable(block) else block)

    def limb(self, p1, p2, r, block, r2=None):
        r2 = r if r2 is None else r2
        n = max(2, int(math.dist(p1, p2) * 2) + 1)
        for i in range(n + 1):
            t = i / n
            self.ball(*(a + (b - a) * t for a, b in zip(p1, p2)), r + (r2 - r) * t, block)

    def box(self, x1, y1, z1, x2, y2, z2, block):
        for x in range(int(round(min(x1, x2))), int(round(max(x1, x2))) + 1):
            for y in range(int(round(min(y1, y2))), int(round(max(y1, y2))) + 1):
                for z in range(int(round(min(z1, z2))), int(round(max(z1, z2))) + 1):
                    self.put(x, y, z, block(x, y, z) if callable(block) else block)

    def commit(self, d, ymin, hollow=True):
        for (x, y, z), b in self.c.items():
            if y < ymin or not d.bp.inside(x, y, z):
                continue
            if hollow and all((x + a, y + b2, z + c) in self.c for a, b2, c in
                              ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))):
                continue
            d.set(x, y, z, b)


def eyes(sc, cx, y, cz_front_fn, u, block):
    for sx in (-1, 1):
        x = int(round(cx + sx * max(1, 0.22 * u)))
        zs = [z for (xx, yy, z) in sc.c if xx == x and yy == y]
        if zs:
            sc.put(x, y, min(zs), block)


def king(cx, cz, y0, H):
    """Crowned stone king in robe and cloak, hands folded on a sword planted point-down."""
    u = H / 8
    sc = Sculpt()
    robe, skin, gold = "smooth_stone", "calcite", "gold_block"
    cloak = lambda x, y, z: "deepslate_tiles" if x % 3 == 0 else "polished_deepslate"
    hem = lambda x, y, z: "chiseled_stone_bricks" if y == y0 else robe
    sc.ell(cx, cz + 0.55 * u, y0, y0 + 6.8 * u, lambda t: 1.75 * u - 0.25 * u * t, 0.75 * u, cloak)
    sc.ell(cx, cz, y0, y0 + 4.3 * u, lambda t: 1.65 * u - 0.45 * u * t, lambda t: 1.05 * u - 0.3 * u * t, hem)
    sc.ell(cx, cz, y0 + 4.3 * u, y0 + 6.9 * u, lambda t: 1.15 * u + 0.35 * u * t, 0.72 * u, robe)
    sc.ell(cx, cz, y0 + 4.3 * u, y0 + 4.3 * u, 1.2 * u, 0.78 * u, "polished_andesite")   # girdle
    sc.ell(cx, cz, y0 + 6.9 * u, y0 + 7.1 * u, 0.35 * u, 0.35 * u, skin)
    sc.ell(cx, cz - 0.05 * u, y0 + 7.0 * u, y0 + 8.0 * u, 0.52 * u, 0.58 * u, skin)
    sc.ell(cx, cz - 0.42 * u, y0 + 6.3 * u, y0 + 7.35 * u, lambda t: 0.25 * u + 0.25 * u * t, 0.3 * u, "stone")
    # crown: gold band with points
    yc = int(round(y0 + 8.0 * u)) + 1
    hx, hz = 0.52 * u, 0.58 * u
    for x in range(int(cx - hx) - 1, int(cx + hx) + 2):
        for z in range(int(cz - hz) - 1, int(cz + hz) + 2):
            e = ((x - cx) / (hx + 0.5)) ** 2 + ((z - cz) / (hz + 0.5)) ** 2
            if 0.45 <= e <= 1.0:
                sc.put(x, yc, z, gold)
                if (x + z) % 2 == 0:
                    sc.put(x, yc + 1, z, gold)
    # arms: shoulders -> elbows at the sides -> hands meeting on the pommel in front
    zf = cz - 1.45 * u
    for sx in (-1, 1):
        sh = (cx + sx * 1.45 * u, y0 + 6.6 * u, cz)
        el = (cx + sx * 1.55 * u, y0 + 5.1 * u, cz - 0.6 * u)
        ha = (cx + sx * 0.35 * u, y0 + 4.9 * u, zf + 0.2 * u)
        sc.limb(sh, el, 0.42 * u, robe, 0.38 * u)
        sc.limb(el, ha, 0.36 * u, robe, 0.3 * u)
        sc.ball(*ha, 0.32 * u, skin)
    # sword
    w = max(0, int(round(0.12 * u)))
    sc.ball(cx, y0 + 5.55 * u, zf, max(0.4, 0.22 * u), gold)
    sc.box(cx, y0 + 4.4 * u, zf, cx, y0 + 5.3 * u, zf, "dark_oak_log[axis=y]")
    sc.box(cx - 0.75 * u, y0 + 4.2 * u, zf, cx + 0.75 * u, y0 + 4.2 * u, zf, gold)
    sc.box(cx - w, y0, zf, cx + w, y0 + 4.1 * u, zf, "iron_block")
    eyes(sc, cx, int(round(y0 + 7.55 * u)), None, u, "polished_deepslate")
    return sc


def lumberjack(cx, cz, y0, H):
    """Painted timber giant: plaid shirt, denim, boots, beard, red toque, resting on a felling axe."""
    u = H / 8
    sc = Sculpt()
    skin, denim, boot = "stripped_oak_wood[axis=y]", "blue_terracotta", "dark_oak_wood[axis=y]"
    k = max(1, int(round(u / 2)))
    plaid = lambda x, y, z: "red_wool" if ((x // k) + (y // k)) % 2 == 0 else (
        "black_wool" if (x // k) % 2 and (y // k) % 2 else "red_terracotta")
    for sx in (-1, 1):
        sc.limb((cx + sx * 0.6 * u, y0 + 4.0 * u, cz), (cx + sx * 0.8 * u, y0 + 0.7 * u, cz), 0.55 * u, denim,
                0.5 * u)
        sc.ell(cx + sx * 0.8 * u, cz - 0.3 * u, y0, y0 + 0.8 * u, 0.5 * u, 0.85 * u, boot)
    sc.ell(cx, cz, y0 + 3.6 * u, y0 + 4.2 * u, 1.15 * u, 0.7 * u, denim)
    sc.ell(cx, cz, y0 + 4.2 * u, y0 + 4.2 * u, 1.2 * u, 0.75 * u, "dark_oak_planks")      # belt
    sc.put(int(round(cx)), int(round(y0 + 4.2 * u)), int(round(cz - 0.75 * u)) - 0, "gold_block")
    sc.ell(cx, cz, y0 + 4.4 * u, y0 + 7.0 * u, lambda t: 1.2 * u + 0.35 * u * t, lambda t: 0.75 * u + 0.1 * u * t,
           plaid)
    sc.ell(cx, cz, y0 + 6.9 * u, y0 + 7.1 * u, 0.35 * u, 0.35 * u, skin)
    sc.ell(cx, cz, y0 + 7.0 * u, y0 + 8.2 * u, 0.55 * u, 0.6 * u, skin)
    sc.ell(cx, cz - 0.38 * u, y0 + 6.4 * u, y0 + 7.45 * u, lambda t: 0.45 * u - 0.05 * u * t, 0.32 * u,
           "spruce_planks")                                                               # beard
    sc.ell(cx, cz + 0.05 * u, y0 + 8.15 * u, y0 + 8.8 * u, lambda t: 0.58 * u - 0.3 * u * t,
           lambda t: 0.62 * u - 0.3 * u * t, "red_wool")                                   # toque
    sc.ball(cx, y0 + 8.95 * u, cz, max(0.4, 0.16 * u), "white_wool")
    # right arm down to the axe handle, left fist on the hip
    ax, az = cx + 1.95 * u, cz - 0.35 * u
    sc.limb((cx + 1.45 * u, y0 + 6.6 * u, cz), (cx + 1.85 * u, y0 + 5.4 * u, cz - 0.1 * u), 0.45 * u, plaid, 0.4 * u)
    sc.limb((cx + 1.85 * u, y0 + 5.4 * u, cz - 0.1 * u), (ax, y0 + 4.4 * u, az), 0.38 * u, plaid, 0.32 * u)
    sc.ball(ax, y0 + 4.3 * u, az, 0.36 * u, skin)
    sc.limb((cx - 1.45 * u, y0 + 6.6 * u, cz), (cx - 2.0 * u, y0 + 5.3 * u, cz + 0.2 * u), 0.45 * u, plaid, 0.4 * u)
    sc.limb((cx - 2.0 * u, y0 + 5.3 * u, cz + 0.2 * u), (cx - 1.3 * u, y0 + 4.5 * u, cz - 0.2 * u), 0.38 * u, plaid,
            0.34 * u)
    sc.ball(cx - 1.25 * u, y0 + 4.5 * u, cz - 0.2 * u, 0.34 * u, skin)
    # felling axe resting head-down beside the right boot
    hw = max(0, int(round(0.08 * u)))
    sc.box(ax - hw, y0 + 0.8 * u, az, ax + hw, y0 + 4.9 * u, az, "stripped_spruce_log[axis=y]")
    sc.box(ax - hw, y0, az - 0.9 * u, ax + hw, y0 + 0.9 * u, az + 0.35 * u, "iron_block")
    sc.box(ax - hw, y0, az - 0.9 * u, ax + hw, y0 + 0.9 * u, az - 0.9 * u, "smooth_stone")
    eyes(sc, cx, int(round(y0 + 7.65 * u)), None, u, "black_wool")
    return sc


def beacon_figure(cx, cz, y0, H, lit=True):
    """Smooth quartz figure with chrome joints and a visor, raising a glowing orb."""
    u = H / 8
    sc = Sculpt()
    q, chrome = "smooth_quartz", "iron_block"
    for sx in (-1, 1):
        hip, knee, ank = (cx + sx * 0.55 * u, y0 + 4.0 * u, cz), (cx + sx * 0.62 * u, y0 + 2.2 * u, cz - 0.05 * u), \
            (cx + sx * 0.7 * u, y0 + 0.5 * u, cz)
        sc.limb(hip, knee, 0.5 * u, q, 0.42 * u)
        sc.limb(knee, ank, 0.4 * u, q, 0.32 * u)
        sc.ball(*knee, 0.4 * u, chrome)
        sc.ell(cx + sx * 0.7 * u, cz - 0.25 * u, y0, y0 + 0.4 * u, 0.4 * u, 0.75 * u, chrome)
    sc.ell(cx, cz, y0 + 3.7 * u, y0 + 4.3 * u, 1.0 * u, 0.6 * u, q)
    sc.ell(cx, cz, y0 + 4.3 * u, y0 + 4.3 * u, 0.95 * u, 0.62 * u, chrome)
    sc.ell(cx, cz, y0 + 4.4 * u, y0 + 6.9 * u, lambda t: 0.9 * u + 0.45 * u * t, 0.62 * u, q)
    sc.ell(cx, cz, y0 + 6.9 * u, y0 + 7.1 * u, 0.3 * u, 0.3 * u, chrome)
    sc.ell(cx, cz, y0 + 7.0 * u, y0 + 8.0 * u, 0.45 * u, 0.5 * u, q)
    yv = int(round(y0 + 7.5 * u))
    for (x, y, z) in list(sc.c):
        if y == yv and z <= cz - 0.2 * u and abs(x - cx) <= 0.5 * u + 0.5 and (x, y, z - 1) not in sc.c:
            sc.put(x, y, z, "cyan_stained_glass")
    # chest light
    sc.put(int(round(cx)), int(round(y0 + 6.0 * u)), int(round(cz - 0.62 * u)) - 0, "sea_lantern")
    # left arm down, right arm raised with the orb
    sc.ball(cx - 1.35 * u, y0 + 6.6 * u, cz, 0.45 * u, chrome)
    sc.limb((cx - 1.35 * u, y0 + 6.6 * u, cz), (cx - 1.6 * u, y0 + 5.0 * u, cz), 0.38 * u, q, 0.34 * u)
    sc.limb((cx - 1.6 * u, y0 + 5.0 * u, cz), (cx - 1.5 * u, y0 + 3.7 * u, cz - 0.2 * u), 0.32 * u, q, 0.3 * u)
    sc.ball(cx + 1.35 * u, y0 + 6.6 * u, cz, 0.45 * u, chrome)
    sc.limb((cx + 1.35 * u, y0 + 6.6 * u, cz), (cx + 1.55 * u, y0 + 8.3 * u, cz), 0.38 * u, q, 0.34 * u)
    sc.ball(cx + 1.55 * u, y0 + 8.3 * u, cz, 0.36 * u, chrome)
    sc.limb((cx + 1.55 * u, y0 + 8.3 * u, cz), (cx + 1.4 * u, y0 + 9.7 * u, cz), 0.32 * u, q, 0.3 * u)
    sc.ball(cx + 1.4 * u, y0 + 10.5 * u, cz, max(0.8, 0.62 * u), "sea_lantern" if lit else "white_stained_glass")
    return sc, (cx + 1.4 * u, y0 + 10.5 * u, cz, 0.62 * u)


COLO_H = {"Hearthwood": {1: 14, 2: 19, 3: 24, 4: 29, 5: 34},
          "Cascadia": {1: 12, 2: 17, 3: 23, 4: 29, 5: 34},
          "Neoterra": {1: 10, 2: 14, 3: 19, 4: 24, 5: 29}}


def pylon_base(d, n, wall, floor, door_wood, hut):
    d.fill(0, 0, 0, n, 0, n, floor)
    d.box(0, 1, 0, n, 4, n, wall)
    d.door(n // 2, 1, 0, "south", door_wood)
    d.hut(*hut)


# ---------------------------------------------------------------------------- Hearthwood: The Old King
HK_SIZE = (27, 52, 27)
HK_PX, HK_PZ, HK_PW = (1, 21), 1, 5
HK_WHUT = (1, 1, 3)
HK_PT = {1: 8, 2: 10, 3: 13, 4: 16, 5: 19}


def hk_wing(rel, L):
    """Stone guard pylon: battered stone-brick shaft with a lantern niche, brazier bowl on top."""
    d = Design("Hearthwood", rel, (HK_PW, 30, HK_PW), gy=0, paving="stone_bricks")
    n, T = HK_PW - 1, HK_PT[L]
    pylon_base(d, n, "stone_bricks", "polished_andesite", "dark_oak", HK_WHUT)
    d.fill(0, 1, 0, n, 1, n, "polished_andesite")
    d.clear(1, 1, 1, n - 1, 1, n - 1)
    d.hut(*HK_WHUT)                                         # the clear above took the hut block out
    d.door(2, 1, 0, "south", "dark_oak")
    for x, z in ((0, 0), (n, 0), (0, n), (n, n)):
        d.fill(x, 1, z, x, 4, z, "chiseled_stone_bricks")
    d.lamp(2, 4, 2)
    d.set(3, 1, 3, "chiseled_stone_bricks")
    d.candle(3, 2, 3, 3)
    for i in range(n + 1):                                  # set-back
        for x, z, f in ((i, 0, "south"), (i, n, "north"), (0, i, "east"), (n, i, "west")):
            sh = "straight"
            if i in (0, n):
                sh = "outer_left" if (x == 0) == (z == 0) else "outer_right"
                f = "south" if z == 0 else "north"
            d.set(x, 5, z, stair("stone_brick_stairs", f, "bottom", sh))
    d.fill(1, 5, 1, 3, T, 3, "stone_bricks")
    for y in range(6, T + 1):
        for x, z in ((1, 1), (3, 1), (1, 3), (3, 3)):
            d.set(x, y, z, "polished_andesite")
    for y in range(7, T - 1, 4):
        d.set(2, y, 1, "chiseled_stone_bricks")
    if L >= 2:
        d.set(2, T - 2, 0, "red_wall_banner[facing=north]")
    # brazier bowl
    for x, z, f in ((1, 1, None), (3, 1, None), (1, 3, None), (3, 3, None)):
        d.set(x, T + 1, z, slab("stone_brick_slab"))
    for x, z, f in ((2, 1, "south"), (2, 3, "north"), (1, 2, "east"), (3, 2, "west")):
        d.set(x, T + 1, z, stair("stone_brick_stairs", f, "top"))
    d.set(2, T + 1, 2, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    return d


def hk_colossus(rel, L):
    d = Design("Hearthwood", rel, HK_SIZE, gy=1, paving="grass_block")
    S, ST = "stone_bricks", "stone_brick_stairs"
    cx, cz = 13, 16
    # gravel approach
    d.fill(11, 1, 0, 15, 1, 7, "gravel")
    # plinth: base course, die with blind arcading, cornice, deck at y8
    d.fill(3, 1, 7, 23, 1, 24, "stone_bricks")
    d.fill(4, 2, 8, 22, 8, 23, S)
    for x in range(3, 24):
        for z in range(7, 25):
            if x in (3, 23) or z in (7, 24):
                if d.air(x, 2, z):
                    f = "south" if z == 7 else "north" if z == 24 else "east" if x == 3 else "west"
                    d.set(x, 2, z, stair(ST, f))
    for x in range(4, 23):
        for z in range(8, 24):
            if x in (4, 22) or z in (8, 23):
                d.set(x, 3, z, "polished_andesite")
                if (x + z) % 3 == 0 and not (x in (4, 22) and z in (8, 23)):
                    d.set(x, 5, z, "chiseled_stone_bricks")
                d.set(x, 8, z, "polished_andesite")
    for x in range(3, 24):
        for z in range(7, 25):
            if (x in (3, 23) or z in (7, 24)) and not (x in (3, 23) and z in (7, 24)):
                f = "north" if z == 7 else "south" if z == 24 else "west" if x == 3 else "east"
                d.set(x, 8, z, stair(ST, OPP[f], "top"))
    for x, z in ((3, 7), (23, 7), (3, 24), (23, 24)):
        d.fill(x, 2, z, x, 9, z, "chiseled_stone_bricks")
    # foundation hall inside the plinth
    d.clear(8, 2, 9, 18, 6, 14)
    d.fill(8, 1, 9, 18, 1, 14, "polished_andesite")
    d.fill(12, 2, 7, 14, 2, 7, AIR)
    d.fill(12, 1, 7, 14, 1, 7, "polished_andesite")
    d.double_door(12, 2, 8, "x", "south", "dark_oak")
    d.set(14, 2, 8, "chiseled_stone_bricks")
    d.set(14, 3, 8, "chiseled_stone_bricks")
    d.set(11, 2, 7, stair(ST, "east"))
    d.set(15, 2, 7, stair(ST, "west"))
    d.set(13, 4, 7, stair(ST, "south", "top"))
    d.set(13, 5, 7, "chiseled_stone_bricks")
    d.hut(9, 2, 10)
    d.rug(11, 10, 15, 13, 2, ("red_carpet", "yellow_carpet"))
    d.set(13, 2, 14, "chiseled_stone_bricks")                  # model of the statue on a pedestal
    d.set(13, 3, 14, "gold_block" if L >= 3 else "smooth_stone")
    for x in (10, 16):
        d.set(x, 2, 14, "lectern[facing=north,has_book=true,powered=false]")
    for x in (8, 18):
        for z in (10, 13):
            d.set(x, 4, z, "red_wall_banner[facing=%s]" % ("east" if x == 8 else "west"))
    for x in (10, 16):
        d.lamp(x, 6, 11)
    d.sign(13, 6, 7, "north", ["THE OLD KING", "Guardian of", "the Realm", f"Anno {L}"], "dark_oak")
    # braziers on the plinth corners (L3+), shields on the die (L2+)
    if L >= 2:
        for x in (7, 19):
            d.set(x, 5, 7, "red_wall_banner[facing=north]")
    if L >= 3:
        for x, z in ((3, 7), (23, 7), (3, 24), (23, 24)):
            d.set(x, 10, z, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    # statue
    sc = king(cx, cz, 9, COLO_H["Hearthwood"][L])
    sc.commit(d, 9)
    # garden: clipped hedges and lanterns (L4+), stone benches (L5)
    if L >= 4:
        for z in range(9, 25, 1):
            for x in (1, 25):
                if z % 4 != 0:
                    d.set(x, 2, z, "oak_leaves[distance=1,persistent=true,waterlogged=false]")
                else:
                    d.set(x, 2, z, "polished_andesite")
                    d.set(x, 3, z, lantern(False))
    if L >= 5:
        for x in (8, 18):
            d.chair(x, 2, 5, "north", "stone_brick", sit=True)
            d.chair(x + 1, 2, 5, "north", "stone_brick", sit=True)
        for x in range(2, 25):
            if not 11 <= x <= 15 and d.air(x, 2, 0) and not (1 <= x <= 5 or 21 <= x <= 25):
                d.set(x, 2, 0, "oak_leaves[distance=1,persistent=true,waterlogged=false]")
    for px in HK_PX:
        d.reserve(px, 1, HK_PZ, px + HK_PW - 1, 30, HK_PZ + HK_PW - 1)
        d.child_hut(px + HK_WHUT[0], 1 + HK_WHUT[1], HK_PZ + HK_WHUT[2], COLO_WING)
    return d

# ---------------------------------------------------------------------------- Cascadia: Timber Giant
CG_SIZE = (25, 50, 29)
CG_PX, CG_PZ, CG_PW = (0, 20), 1, 5
CG_WHUT = (1, 1, 3)
CG_PT = {1: 9, 2: 11, 3: 14, 4: 17, 5: 20}


def cg_wing(rel, L):
    """Carved timber pole on a little log shrine: painted bands, carved faces, spread-wing crest."""
    d = Design("Cascadia", rel, (CG_PW, 30, CG_PW), gy=0, paving="cobblestone")
    n, T = CG_PW - 1, CG_PT[L]
    d.fill(0, 0, 0, n, 0, n, "spruce_planks")
    d.fill(0, 1, 0, n, 1, n, "mossy_cobblestone")
    d.box(0, 2, 0, n, 4, n, log("spruce_log", "x"))
    for z in range(n + 1):
        for y in (2, 3, 4):
            d.set(0, y, z, log("spruce_log", "z"))
            d.set(n, y, z, log("spruce_log", "z"))
    for x, z in ((0, 0), (n, 0), (0, n), (n, n)):
        d.fill(x, 1, z, x, 4, z, log("stripped_spruce_log"))
    d.clear(1, 1, 1, n - 1, 4, n - 1)
    d.door(2, 1, 0, "south", "spruce")
    d.hut(*CG_WHUT)
    d.set(3, 1, 3, "barrel[facing=up,open=false]")
    d.lamp(2, 4, 2)
    for i in range(n + 1):
        for x, z, f in ((i, 0, "south"), (i, n, "north"), (0, i, "east"), (n, i, "west")):
            sh = "straight"
            if i in (0, n):
                sh = "outer_left" if (x == 0) == (z == 0) else "outer_right"
                f = "south" if z == 0 else "north"
            d.set(x, 5, z, stair("dark_oak_stairs", f, "bottom", sh))
    # the pole (3x3), carved in stacked figures
    bands = ["stripped_spruce_log[axis=y]", "red_terracotta", "stripped_spruce_log[axis=y]", "black_terracotta"]
    for y in range(5, T + 1):
        k = (y - 5) // 3
        b = bands[k % len(bands)]
        for x in range(1, 4):
            for z in range(1, 4):
                d.set(x, y, z, b)
        if k % 2 == 0 and (y - 5) % 3 == 1:            # carved face: eyes and a beak on the street side
            d.set(1, y, 1, "black_terracotta")
            d.set(3, y, 1, "black_terracotta")
            d.set(2, y - 1, 0, stair("spruce_stairs", "south", "top"))
    for x in (1, 3):
        d.set(x, T + 1, 2, "stripped_spruce_log[axis=y]")
    d.fill(1, T + 1, 1, 3, T + 1, 3, "stripped_spruce_log[axis=y]")
    # spread wings and head
    for x, f in ((0, "east"), (4, "west")):
        d.set(x, T + 1, 2, stair("red_terracotta" and "spruce_stairs", f, "top"))
        d.set(x, T + 2, 2, stair("dark_oak_stairs", f))
    d.set(2, T + 2, 2, "black_terracotta")
    d.set(2, T + 2, 1, "red_terracotta")
    d.set(2, T + 2, 0, stair("spruce_stairs", "south", "top"))
    d.set(2, T + 3, 2, log("stripped_spruce_log"))
    d.set(2, T + 4, 2, "lantern[hanging=false,waterlogged=false]")
    return d


def cg_colossus(rel, L):
    d = Design("Cascadia", rel, CG_SIZE, gy=1, paving="grass_block")
    cx, cz = 12, 17
    d.fill(10, 1, 0, 14, 1, 8, "coarse_dirt")
    # river-rock base
    rock = ("cobblestone", "mossy_cobblestone", "andesite", "cobblestone", "tuff")
    for x in range(3, 22):
        for z in range(9, 27):
            for y in range(2, 5):
                d.set(x, y, z, rock[(x * 7 + z * 3 + y * 5) % len(rock)])
    for x in range(2, 23):
        for z in range(8, 28):
            if (x in (2, 22) or z in (8, 27)) and d.air(x, 2, z):
                d.set(x, 2, z, "mossy_cobblestone" if (x + z) % 2 else "cobblestone")
    # log crib above: alternating courses
    for y in range(5, 8):
        ax = "x" if y % 2 else "z"
        for x in range(4, 21):
            for z in range(10, 26):
                if x in (4, 20) or z in (10, 25):
                    a = "x" if z in (10, 25) else "z"
                    if x in (4, 20) and z in (10, 25):
                        a = ax
                    d.set(x, y, z, log("spruce_log", a))
                else:
                    d.set(x, y, z, "spruce_planks")
    for x, z in ((4, 10), (20, 10), (4, 25), (20, 25)):
        d.fill(x, 5, z, x, 9, z, log("stripped_spruce_log"))
        d.set(x, 10, z, "lantern[hanging=false,waterlogged=false]")
    d.fill(4, 8, 10, 20, 8, 25, "spruce_planks")
    for x in range(3, 22):                               # deck eaves
        for z in (9, 26):
            d.set(x, 8, z, slab("spruce_slab", "top"))
    for z in range(9, 27):
        for x in (3, 21):
            d.set(x, 8, z, slab("spruce_slab", "top"))
    # camp hall inside
    d.clear(7, 2, 11, 17, 6, 16)
    d.fill(7, 1, 11, 17, 1, 16, "spruce_planks")
    d.clear(11, 2, 9, 13, 4, 10)
    d.fill(11, 1, 9, 13, 1, 10, "spruce_planks")
    d.door(12, 2, 9, "south", "spruce")
    d.fill(11, 2, 8, 13, 2, 8, AIR)
    d.set(11, 2, 8, stair("cobblestone_stairs", "east"))
    d.set(13, 2, 8, stair("cobblestone_stairs", "west"))
    d.set(11, 2, 9, log("stripped_spruce_log"))
    d.set(13, 2, 9, log("stripped_spruce_log"))
    d.fill(11, 4, 9, 13, 4, 9, log("stripped_spruce_log", "x"))
    d.set(11, 3, 9, log("stripped_spruce_log"))
    d.set(13, 3, 9, log("stripped_spruce_log"))
    for y in (5, 6):
        for x in range(7, 18):
            d.set(x, y, 10, "spruce_planks")
    d.hut(8, 2, 12)
    d.set(12, 2, 16, "cobblestone")
    d.hearth(12, 2, 15, "north", 8, "cobblestone", "campfire")
    d.set(12, 3, 15, "cobblestone")
    d.chair(10, 2, 13, "west", "spruce")
    d.chair(14, 2, 13, "east", "spruce")
    d.set(16, 2, 12, "barrel[facing=up,open=false]")
    d.set(16, 2, 13, "barrel[facing=up,open=false]")
    for x in (9, 15):
        d.lamp(x, 6, 14)
    d.sign(12, 5, 8, "north", ["TIMBER GIANT", "carved from", "old-growth", "spruce"], "spruce")
    # statue
    sc = lumberjack(cx, cz, 9, COLO_H["Cascadia"][L])
    sc.commit(d, 9)
    # logging yard props
    if L >= 2:
        for x, z in ((1, 12), (1, 13), (1, 14)):
            d.set(x, 2, z, log("spruce_log", "x"))
        d.set(1, 3, 13, log("spruce_log", "x"))
    if L >= 3:
        for x, z in ((23, 12), (23, 13), (23, 14)):
            d.set(x, 2, z, log("spruce_log", "x"))
        d.set(23, 3, 13, log("spruce_log", "x"))
        for z in range(18, 28, 3):
            d.set(0, 2, z, fence("spruce_fence"))
            d.set(24, 2, z, fence("spruce_fence"))
    if L >= 4:
        d.set(1, 2, 20, "hay_block[axis=y]")
        d.set(23, 2, 20, "hay_block[axis=y]")
        for x in (8, 16):
            d.set(x, 2, 6, log("stripped_spruce_log"))
            d.set(x, 3, 6, "lantern[hanging=false,waterlogged=false]")
    if L >= 5:
        for x, z in ((1, 27), (23, 27)):
            yew(d, x, z, 2, "spruce_leaves", "spruce_log")
        d.chair(9, 2, 6, "north", "spruce")
        d.chair(15, 2, 6, "north", "spruce")
    for px in CG_PX:
        d.reserve(px, 1, CG_PZ, px + CG_PW - 1, 30, CG_PZ + CG_PW - 1)
        d.child_hut(px + CG_WHUT[0], 1 + CG_WHUT[1], CG_PZ + CG_WHUT[2], COLO_WING)
    return d


# ---------------------------------------------------------------------------- Neoterra: Beacon
NB_SIZE = (29, 54, 29)
NB_PX, NB_PZ, NB_PW = (0, 24), 0, 5
NB_WHUT = (1, 1, 3)
NB_PT = {1: 9, 2: 12, 3: 15, 4: 18, 5: 22}


def nb_wing(rel, L):
    """Glass light pylon: lobby, chrome-cornered glass shaft with a glowing core, end-rod crown."""
    d = Design("Neoterra", rel, (NB_PW, 34, NB_PW), gy=0, paving="smooth_stone")
    n, T = NB_PW - 1, NB_PT[L]
    d.fill(0, 0, 0, n, 0, n, "polished_diorite")
    d.fill(0, 1, 0, n, 3, n, "light_gray_stained_glass_pane")
    d.clear(1, 1, 1, n - 1, 3, n - 1)
    for x, z in ((0, 0), (n, 0), (0, n), (n, n)):
        d.fill(x, 1, z, x, 3, z, "white_concrete")
    d.door(2, 1, 0, "south", "birch")
    d.hut(*NB_WHUT)
    d.set(3, 1, 3, "potted_bamboo")
    d.fill(0, 4, 0, n, 4, n, "smooth_quartz")
    d.set(2, 3, 2, "sea_lantern")
    for y in range(5, T + 1):
        for x in range(1, 4):
            for z in range(1, 4):
                c = x in (1, 3) and z in (1, 3)
                d.set(x, y, z, "iron_block" if c else ("sea_lantern" if (x, z) == (2, 2) else
                                                     "light_blue_stained_glass"))
        if y % 4 == 0:
            for x, z in ((2, 1), (2, 3), (1, 2), (3, 2)):
                d.set(x, y, z, "cyan_terracotta")
    d.fill(1, T + 1, 1, 3, T + 1, 3, "smooth_quartz_slab[type=bottom,waterlogged=false]")
    d.set(2, T + 1, 2, "beacon" if L >= 4 else "sea_lantern")
    for y in range(T + 2, T + 2 + (2 + L // 2)):
        d.set(2, y, 2, "end_rod[facing=up]")
    for x, z in ((1, 1), (3, 1), (1, 3), (3, 3)):
        d.set(x, T + 2, z, "end_rod[facing=up]")
    return d


def nb_colossus(rel, L):
    d = Design("Neoterra", rel, NB_SIZE, gy=1, paving="smooth_stone")
    cx, cz = 14, 16
    for x in range(29):
        for z in range(29):
            if (x // 2 + z // 2) % 2 == 0:
                d.set(x, 1, z, "white_concrete")
    # tier 1 terrace (y2..3)
    d.fill(3, 2, 7, 25, 3, 25, "smooth_quartz")
    for x in range(10, 19):                                    # front steps
        d.set(x, 2, 5, stair("smooth_quartz_stairs", "south"))
        d.set(x, 2, 6, "smooth_quartz")
        d.set(x, 3, 6, stair("smooth_quartz_stairs", "south"))
    for x in range(3, 26):
        for z in (7, 25):
            d.set(x, 3, z, "cyan_terracotta" if x % 4 == 1 else "smooth_quartz")
    # glass gallery (hall) y4..6, roof y7
    d.box(5, 4, 9, 23, 6, 23, "light_gray_stained_glass_pane")
    for x in range(5, 24, 3):
        for z in (9, 23):
            d.fill(x, 4, z, x, 6, z, "white_concrete")
    for z in range(9, 24, 3):
        for x in (5, 23):
            d.fill(x, 4, z, x, 6, z, "white_concrete")
    d.fill(4, 7, 8, 24, 7, 24, "white_concrete")
    for x in range(4, 25):
        for z in (8, 24):
            d.set(x, 7, z, "smooth_quartz")
    d.fill(6, 3, 10, 22, 3, 22, "polished_diorite")
    d.double_door(13, 4, 9, "x", "south", "birch")
    d.fill(13, 6, 9, 14, 6, 9, "white_concrete")
    d.hut(7, 4, 11)
    # exhibit: scale model, info kiosks, benches, lights
    d.set(14, 4, 16, "smooth_quartz")
    d.set(14, 5, 16, "white_stained_glass")
    for x in (10, 18):
        d.set(x, 4, 13, "lectern[facing=north,has_book=true,powered=false]")
    for x in (10, 11, 17, 18):
        d.chair(x, 4, 20, "south", "birch")
    for x, z in ((9, 12), (19, 12), (9, 20), (19, 20)):
        d.set(x, 6, z, "end_rod[facing=down]")
    d.set(6, 4, 22, "potted_bamboo")
    d.set(22, 4, 22, "potted_bamboo")
    # upper tier deck y8 with planters
    d.fill(7, 8, 10, 21, 8, 22, "smooth_quartz")
    for x in range(7, 22):
        for z in (10, 22):
            d.set(x, 8, z, "cyan_terracotta" if x % 2 else "smooth_quartz")
    if L >= 2:
        for x, z in ((5, 8), (23, 8), (5, 24), (23, 24)):
            d.set(x, 8, z, "moss_block")
            d.set(x, 9, z, "flowering_azalea")
    if L >= 3:
        for x in range(4, 25, 4):
            d.set(x, 2, 26, "sea_lantern")
            d.set(x, 1, 27, "moss_block")
            d.set(x, 2, 27, "potted_bamboo")
    # statue
    H = NB_COL = COLO_H["Neoterra"][L]
    sc, orb = beacon_figure(cx, cz, 9, H)
    sc.commit(d, 9)
    ox, oy, oz, r = orb
    if L >= 3:                                                 # light rays from the orb
        for ddx, ddz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            x, z = int(round(ox + ddx * (r + 1.5))), int(round(oz + ddz * (r + 1.5)))
            if d.bp.inside(x, int(round(oy)), z) and d.air(x, int(round(oy)), z):
                d.set(x, int(round(oy)), z, "end_rod[facing=%s]" % {(1, 0): "east", (-1, 0): "west",
                                                                     (0, 1): "south", (0, -1): "north"}[(ddx, ddz)])
        top = int(round(oy + r)) + 1
        for y in range(top, top + 2):
            if d.bp.inside(int(round(ox)), y, int(round(oz))):
                d.set(int(round(ox)), y, int(round(oz)), "end_rod[facing=up]")
    # water mirrors left and right (L4+)
    if L >= 4:
        for x0 in (0, 26):
            for z in range(9, 25):
                for x in range(x0, x0 + 3):
                    d.set(x, 1, z, "water" if 1 <= x - x0 <= 1 or True else "smooth_quartz")
                    d.set(x, 0, z, "light_blue_concrete")
        for z in range(9, 25):
            d.set(0, 1, z, "smooth_quartz")
            d.set(28, 1, z, "smooth_quartz")
    for px in NB_PX:
        d.reserve(px, 1, NB_PZ, px + NB_PW - 1, 34, NB_PZ + NB_PW - 1)
        d.child_hut(px + NB_WHUT[0], 1 + NB_WHUT[1], NB_PZ + NB_WHUT[2], COLO_WING)
    return d


# ------------------------------------------------------------------------------------------------ registry
CATHEDRAL = {"Hearthwood": hc_cathedral, "Cascadia": cc_cathedral, "Neoterra": nc_cathedral}
CATHEDRAL_WING = {"Hearthwood": hc_wing, "Cascadia": cc_wing, "Neoterra": nc_wing}
COLOSSUS = {"Hearthwood": hk_colossus, "Cascadia": cg_colossus, "Neoterra": nb_colossus}
COLOSSUS_WING = {"Hearthwood": hk_wing, "Cascadia": cg_wing, "Neoterra": nb_wing}


@design("cathedral")
def cathedral(pack, rel, L):
    return CATHEDRAL[pack](rel, L)


@design("cathedralwing")
def cathedralwing(pack, rel, L):
    return CATHEDRAL_WING[pack](rel, L)


@design("colossus")
def colossus(pack, rel, L):
    return COLOSSUS[pack](rel, L)


@design("colossuswing")
def colossuswing(pack, rel, L):
    return COLOSSUS_WING[pack](rel, L)
