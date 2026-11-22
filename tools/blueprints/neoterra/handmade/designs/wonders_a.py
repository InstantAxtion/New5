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

CATH_WING = "monuments/cathedralwing0.blueprint"
COLO_WING = "monuments/colossuswing0.blueprint"


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


def _oct(dx, dz, r):
    """Cell inside the octagon of 'radius' r (r <= 1: plain square)."""
    if r < 0:
        return False
    m = max(abs(dx), abs(dz))
    return m <= r and (r < 2 or abs(dx) + abs(dz) <= r + r // 2)


def _stair_at(stairs, exposed):
    """Roof stair for a cell whose open sides are `exposed` (set of directions): straight facing up-slope, or an
    outer corner where two adjacent sides are open."""
    n, s_, w, e = ("north" in exposed), ("south" in exposed), ("west" in exposed), ("east" in exposed)
    if (n or s_) and (w or e) and not (n and s_) and not (w and e):
        return stair(stairs, "south" if n else "north", "bottom", "outer_left" if w == n else "outer_right")
    for side in ("north", "south", "west", "east"):
        if side in exposed:
            return stair(stairs, OPP[side])
    return None


def spire(d, cx, cz, y0, R, block, stairs, step=3, needle=4, needle_block=None, top=None, cross=False,
          broach=True, slab_block=None):
    """Slender octagonal spire: bands `step` high that narrow by one each, every face of a band ends in stairs
    (straight on the faces, outer-corner shapes on the chamfers), broaches fill the square corners at the foot,
    then a thin needle of `needle_block`, optional cross and a top finial. Returns the y above the finial."""
    nb = needle_block or wallb("stone_brick_wall")
    y = y0
    if broach and R >= 2:                                   # broaches: corner pyramids at the foot
        for dx in range(-R, R + 1):
            for dz in range(-R, R + 1):
                if not _oct(dx, dz, R):
                    ex = {s2 for s2, (ox, oz) in D4.items()
                          if max(abs(dx + ox), abs(dz + oz)) > R}
                    st = _stair_at(stairs, ex)
                    d.set(cx + dx, y, cz + dz, st or (slab(slab_block) if slab_block else block))
    for r in range(R, 0, -1):
        for k in range(step):
            last = k == step - 1
            for dx in range(-r, r + 1):
                for dz in range(-r, r + 1):
                    if not _oct(dx, dz, r):
                        continue
                    ex = {s2 for s2, (ox, oz) in D4.items() if not _oct(dx + ox, dz + oz, r)}
                    if last and not _oct(dx, dz, r - 1):
                        d.set(cx + dx, y, cz + dz, _stair_at(stairs, ex) or block)
                    elif ex or (last and r - 1 >= 0 and any(not _oct(dx + ox, dz + oz, r - 1)
                                                            for ox, oz in D4.values())):
                        d.set(cx + dx, y, cz + dz, block)
                    else:
                        d.set(cx + dx, y, cz + dz, AIR)
            y += 1
    d.set(cx, y, cz, block)                                 # needle
    y += 1
    for k in range(needle):
        d.set(cx, y, cz, nb)
        if cross and k == needle - 2:
            for ox, oz in ((1, 0), (-1, 0)):
                d.set(cx + ox, y, cz + oz, nb)
        y += 1
    d.set(cx, y, cz, top or "lightning_rod[facing=up,powered=false,waterlogged=false]")
    return y + 1


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
HC_SIZE = (48, 64, 44)
HC_TX, HC_TZ, HC_TW = (5, 19), 1, 7          # west towers (wings) x origin, z origin, footprint
HC_WHUT = (1, 1, 5)                            # wing hut, tower-local
HC_TOP = {1: 11, 2: 19, 3: 24, 4: 29, 5: 29}   # tower wall top (local y)


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
    d.rug(2, 2, 4, 3, 1, ("red_carpet", "yellow_carpet"))
    d.set(5, 1, 1, "chiseled_stone_bricks")                  # votive candle stand
    d.candle(5, 2, 1, 4)
    d.chair(5, 1, 4, "east", "dark_oak", sit=False)
    d.set(1, 3, 3, "red_wall_banner[facing=east]")
    d.set(5, 3, 3, "red_wall_banner[facing=west]")
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
    for x in (1, 5):                                 # a ring of three: two smaller bells, the ringers' bench
        d.set(x, T - 2, 3, "bell[attachment=ceiling,facing=north,powered=false]")
    d.set(1, bf + 1, 5, stair("dark_oak_stairs", "west"))
    d.set(5, bf + 1, 1, "barrel[facing=up,open=false]")
    d.set(5, bf + 2, 1, lantern(False))
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
            spire(d, 3, 3, T + 1, 2, "deepslate_tiles", "deepslate_tile_stairs", step=3, needle=3,
                  broach=False)
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
    ne = 10 if L == 1 else 17                     # nave east end
    NH = 10 if L == 1 else 16                     # nave wall top
    aisles = L >= 2
    cross = L >= 3
    # paths
    d.fill(13, 1, 0, 17, 1, 0, "gravel")
    if aisles:
        d.fill(0, 1, 0, 30, 1, 0, "gravel")
    # ---------------- nave -------------
    d.fill(12, 1, 1, 18, 1, ne, "polished_andesite")
    for x in (11, 19):
        d.fill(x, 2, 1, x, NH, ne, S)
    d.fill(11, 2, 1, 19, NH, 1, S)
    if not cross:
        d.fill(11, 2, ne, 19, NH, ne, S)
    d.clear(12, 2, 2, 18, NH, ne - 1 if not cross else ne)
    for z in range(1, ne + 1):                     # plinth course
        for x in (11, 19):
            d.set(x, 2, z, "polished_andesite")
    for z in range(2, ne + 1, 2):                  # checkered stone floor
        for x in range(12, 19):
            if (x + z) % 4 == 0:
                d.set(x, 1, z, "smooth_stone")
    # cornice
    for z in range(0, ne + 1):
        for x, f in ((10, "east"), (20, "west")):
            d.set(x, NH, z, stair(ST, f, "top"))
    # clerestory lancets (above the aisle roofs)
    if aisles:
        for z in range(9, ne, 3):
            for x in (11, 19):
                lancet(d, x, z, 13, 15)
    else:                                          # L1: side lancets in the plain chapel walls
        for x in (11, 19):
            lancet(d, x, 9, 4, 7)
        for z in (8, ne):
            for x, out in ((10, "west"), (20, "east")):
                for y in range(2, 8):
                    d.set(x, y, z, S)
                d.set(x, 8, z, stair(ST, OPP[out]))
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
            # aisle furnishing, one set per bay: votive stand under each window, a kneeling bench and an
            # effigy tomb in the middle bay, lantern in each bay
            for z in (10, 13, 16):
                d.set(xo + step, 2, z, "chiseled_stone_bricks")
                d.candle(xo + step, 3, z, 3)
            d.chair(xo + 2 * step, 2, 10, "south", "dark_oak", sit=False)
            d.set(xo + 2 * step, 2, 13, slab("smooth_stone_slab", "top"))      # tomb chest with effigy
            d.set(xo + 2 * step, 2, 14, slab("smooth_stone_slab", "top"))
            d.set(xo + 2 * step, 3, 13, "white_carpet")
            for z in (9, 12, 15):
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
        for z in range(27, 32):                                         # chancel cornice
            for x, f in ((10, "east"), (20, "west")):
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
                # octagonal belfry drum, then the spire proper
                for y in range(ct + 1, ct + 7):
                    for dx in range(-3, 4):
                        for dz in range(-3, 4):
                            if _oct(dx, dz, 3) and not _oct(dx, dz, 2):
                                d.set(15 + dx, y, 22 + dz, "stone_bricks")
                            elif _oct(dx, dz, 2):
                                d.set(15 + dx, y, 22 + dz, AIR)
                for dx, dz in ((0, -3), (0, 3), (-3, 0), (3, 0)):
                    lancet(d, 15 + dx, 22 + dz, ct + 2, ct + 4)
                    d.set(15 + dx, ct + 5, 22 + dz, "chiseled_stone_bricks")
                for dx, dz in ((-2, -2), (2, -2), (-2, 2), (2, 2)):               # pinnacles on the chamfers
                    for y in range(ct + 1, ct + 7):
                        d.set(15 + dx, y, 22 + dz, "polished_andesite")
                    d.set(15 + dx, ct + 7, 22 + dz, wallb("stone_brick_wall"))
                    d.set(15 + dx, ct + 8, 22 + dz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
                spire(d, 15, 22, ct + 7, 3, "deepslate_tiles", "deepslate_tile_stairs", step=3, needle=7,
                      cross=True, top="end_rod[facing=up]", broach=False)
                d.fill(13, ct + 4, 22, 17, ct + 4, 22, log("dark_oak_log", "x"))   # bell frame, ring of three
                for x in (14, 15, 16):
                    d.set(x, ct + 3, 22, "bell[attachment=ceiling,facing=north,powered=false]")
                for x in (13, 17):
                    d.fill(x, ct + 1, 22, x, ct + 3, 22, log("dark_oak_log"))
        # interior: choir stalls, altar, lectern, organ pipes
        for z in range(27, 30):
            d.chair(12, 2, z, "west", "dark_oak")
            d.chair(18, 2, z, "east", "dark_oak")
        d.rug(15, 18, 15, 29, 2, ("red_carpet",), "plain")
        az = 29 if L >= 4 else 30
        d.set(14, 2, az, "chiseled_stone_bricks")
        d.set(15, 2, az, "chiseled_quartz_block")
        d.set(16, 2, az, "chiseled_stone_bricks")
        d.candle(14, 3, az, 3)
        d.set(15, 3, az, "gold_block" if L >= 4 else "candle[candles=4,lit=false,waterlogged=false]")
        d.candle(16, 3, az, 3)
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
        # west transept: the organ against the south wall with the organist's bench
        for x, h in ((4, 3), (5, 4), (6, 5), (7, 4), (8, 3)):
            d.set(x, 2, 25, "note_block[instrument=flute,note=0,powered=false]")
            for y in range(3, 3 + h):
                d.set(x, y, 25, "iron_bars")
            d.set(x, 3 + h, 25, slab("dark_oak_slab"))
        d.chair(6, 2, 24, "south", "dark_oak", sit=False)
        d.set(5, 2, 24, "lectern[facing=north,has_book=true,powered=false]")
        d.set(4, 5, 19, "red_wall_banner[facing=south]")
        d.set(8, 5, 19, "red_wall_banner[facing=south]")
        # east transept: a bishop's tomb chest with effigy between two candle stands, memorial banners
        d.set(24, 2, 22, slab("smooth_stone_slab", "top"))
        d.set(25, 2, 22, slab("smooth_stone_slab", "top"))
        d.set(24, 3, 22, "white_carpet")
        d.set(25, 3, 22, "white_carpet")
        for z in (20, 24):
            d.set(23, 2, z, "chiseled_stone_bricks")
            d.candle(23, 3, z, 3)
        d.set(24, 5, 25, "blue_wall_banner[facing=north]")
        d.set(24, 5, 19, "blue_wall_banner[facing=south]")
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
            lancet(d, x, ne, 5, (13 if x == 15 else 11) if L > 1 else (9 if x == 15 else 8))
    # ---------------- nave roof and west front -------------
    rdg = d.gable(11, 1, 19, ne, NH + 1, "z", "deepslate_tile_stairs", "deepslate_tile_slab", S, 1)
    d.set(15, rdg + 1, 0, wallb("stone_brick_wall"))     # cross on the west gable
    d.set(15, rdg + 2, 0, wallb("stone_brick_wall"))
    d.set(14, rdg + 2, 0, wallb("stone_brick_wall"))
    d.set(16, rdg + 2, 0, wallb("stone_brick_wall"))
    d.set(15, rdg + 3, 0, wallb("stone_brick_wall"))
    for z in range(2, ne, 2):                            # ridge crest
        if d.get(15, rdg, z).startswith("minecraft:deepslate_tile_slab"):
            d.set(15, rdg + 1, z, "iron_bars")
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
            lancet(d, x, 1, 9, 12 if x == 15 else 11)
    # nave furnishing: pews either side of the central walk, font, chandeliers, hut by the entrance
    d.hut(12, 2, 2)
    d.set(17, 2, 3, "water_cauldron[level=3]")
    d.set(18, 2, 3, "chiseled_stone_bricks")
    d.rug(15, 3, 15, ne - (3 if not cross else 0), 2, ("red_carpet",), "plain")
    # pews either side of the central walk (rows by level), chandeliers down the nave, torches and banners
    pz = {1: (4, 6), 2: (4, 6, 8, 10, 12, 14)}.get(L, (5, 7, 9, 11, 13, 15))
    pews(d, 12, 14, pz, 2, "dark_oak")
    pews(d, 16, 18, pz, 2, "dark_oak")
    for z in ((5,) if L == 1 else (5, 9, 13)):
        chandelier(d, 15, z, rdg - 1, NH - 3 if L == 1 else 11)
    for z, kind in (((4, "torch"), (7, "banner")) if L == 1 else
                    ((4, "torch"), (7, "banner"), (10, "torch"), (13, "banner"))):
        for x, f in ((12, "east"), (18, "west")):
            d.set(x, 5, z, f"wall_torch[facing={f}]" if kind == "torch" else f"red_wall_banner[facing={f}]")
    # churchyard furniture round the core (all levels): lamp posts by the portal, graves and a bench
    for x in (12, 18):
        lamp_post(d, x, 0, "polished_andesite", fence("dark_oak_fence"))
    if L == 1:
        for z in range(9, 11):
            for x in (10, 20):
                d.set(x, 2, z, ("rose_bush[half=lower]", "peony[half=lower]")[z % 2])
                d.set(x, 3, z, ("rose_bush[half=upper]", "peony[half=upper]")[z % 2])
        for x in (13, 17):
            d.chair(x, 2, 12, "south", "dark_oak", sit=False)
        for x, z in ((22, 12), (24, 10), (8, 12)):
            d.set(x, 2, z, "mossy_cobblestone_wall[east=none,north=none,south=none,up=true,waterlogged=false,"
                  "west=none]")
            d.set(x, 1, z + 1, "podzol")
        yew(d, 25, 14, 2)
        yew(d, 4, 14, 2)
    # ---------------- buttresses (L4: flying) -------------
    if L >= 4:
        for z in (11, 14):
            hc_buttress(d, 4, z, "west", 10, 10, 14)
            hc_buttress(d, 26, z, "east", 10, 20, 14)
        for z in (28, 30):
            hc_buttress(d, 10, z, "west", 12)
            hc_buttress(d, 20, z, "east", 12)
        for x in (12, 18):
            if L < 4:
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
        for x in (3, 27):
            d.set(x, 2, 1, "polished_andesite")
            d.set(x, 3, 1, lantern(False))
    if L >= 4:
        hc_cloister(d, L)
        hc_lady_chapel(d, L)
    if L >= 5:
        hc_chapter_house(d, L)
        hc_palace(d, L)
        stamp(d, hc_deanery, 21, 1, L)              # deanery: same house frame, its own rooms
        hc_library(d, L)          # the deanery: same hall-house plan south-east of the choir
        hc_close(d, L)
    # reserve the west towers last so nothing drawn above leaks into them
    for tx in HC_TX:
        d.reserve(tx, 1, HC_TZ, tx + HC_TW - 1, 46, HC_TZ + HC_TW - 1)
        d.child_hut(tx + HC_WHUT[0], 1 + HC_WHUT[1], HC_TZ + HC_WHUT[2], CATH_WING)
    return d


def hc_cloister(d, L):
    """Cloister east of the nave: four vaulted walks round a garth with a well, reached by a slype from the
    east aisle; carrels, benches and lanterns in the walks."""
    S, ST, TS = "stone_bricks", "stone_brick_stairs", "deepslate_tile_stairs"
    x1, z1, x2, z2 = 29, 2, 45, 16
    a1, b1, a2, b2 = x1 + 3, z1 + 3, x2 - 3, z2 - 3                 # arcade line
    d.fill(x1, 1, z1, x2, 1, z2, "polished_andesite")
    d.fill(a1 + 1, 1, b1 + 1, a2 - 1, 1, b2 - 1, "grass_block")
    # outer wall with lancets
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if x in (x1, x2) or z in (z1, z2):
                d.fill(x, 2, z, x, 7, z, S)
                d.set(x, 2, z, "polished_andesite")
    for x in range(x1 + 2, x2 - 1, 3):
        for z in (z1, z2):
            lancet(d, x, z, 4, 5)
    for z in range(z1 + 2, z2 - 1, 3):
        lancet(d, x2, z, 4, 5)
    # arcade: shafts with pointed arches
    for x in range(a1, a2 + 1):
        for z in range(b1, b2 + 1):
            if not (x in (a1, a2) or z in (b1, b2)):
                continue
            corner = x in (a1, a2) and z in (b1, b2)
            pier = corner or ((x - a1) % 3 == 0 if z in (b1, b2) else (z - b1) % 3 == 0)
            d.set(x, 2, z, "polished_andesite" if pier else slab("stone_brick_slab"))
            for y in (3, 4):
                d.set(x, y, z, wallb("stone_brick_wall") if pier else AIR)
            if pier:
                d.set(x, 5, z, S)
            else:
                if z in (b1, b2):
                    f = "east" if (x - a1) % 3 == 1 else "west"
                else:
                    f = "south" if (z - b1) % 3 == 1 else "north"
                d.set(x, 5, z, stair(ST, f, "top"))
            d.set(x, 6, z, S)
    for x, z in ((a1 + (a2 - a1) // 2, b1), (a1 + (a2 - a1) // 2, b2), (a1, b1 + (b2 - b1) // 2),
                 (a2, b1 + (b2 - b1) // 2)):
        d.set(x, 2, z, AIR)                                        # openings into the garth
    # lean-to roofs over the walks
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            ring = min(x - x1, x2 - x, z - z1, z2 - z)
            if ring > 3:
                continue
            y = 8 - ring
            if min(x - x1, x2 - x) <= min(z - z1, z2 - z):
                f = "west" if x - x1 < x2 - x else "east"
            else:
                f = "north" if z - z1 < z2 - z else "south"
            if ring == 0:
                d.set(x, 8, z, stair(TS, f))
            else:
                d.set(x, y, z, stair(TS, f))
                if ring <= 2:
                    d.set(x, y - 1, z, stair(ST, OPP[f], "top"))
    # garth: crossing paths, well, rose beds
    cx, cz = (a1 + a2) // 2, (b1 + b2) // 2
    for x in range(a1 + 1, a2):
        d.set(x, 1, cz, "gravel")
    for z in range(b1 + 1, b2):
        d.set(cx, 1, z, "gravel")
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            d.set(cx + dx, 2, cz + dz, "cobblestone_wall[east=none,north=none,south=none,up=true,waterlogged=false,"
                  "west=none]" if (dx or dz) else "water_cauldron[level=3]")
    for dx, dz in ((-1, -1), (1, 1)):
        d.set(cx + dx, 3, cz + dz, fence("dark_oak_fence"))
        d.set(cx + dx, 4, cz + dz, fence("dark_oak_fence"))
    for x, z, back in ((34, 8, "west"), (34, 9, "west"), (34, 10, "west"), (40, 8, "east"), (40, 9, "east"),
                       (40, 10, "east")):
        d.chair(x, 2, z, back, "dark_oak", sit=False)                  # stone-garth benches facing the well
    lamp_post(d, 33, 6, "polished_andesite", fence("dark_oak_fence"), h=1)
    lamp_post(d, 41, 12, "polished_andesite", fence("dark_oak_fence"), h=1)
    d.fill(cx - 1, 5, cz - 1, cx + 1, 5, cz + 1, slab("dark_oak_slab"))
    d.set(cx, 4, cz, "chain[axis=y,waterlogged=false]")
    for x, z in ((a1 + 2, b1 + 2), (a2 - 2, b1 + 2), (a1 + 2, b2 - 2), (a2 - 2, b2 - 2)):
        d.set(x, 2, z, "rose_bush[half=lower]")
        d.set(x, 3, z, "rose_bush[half=upper]")
    for x, f in ((33, "allium"), (34, "lily_of_the_valley"), (35, "allium"), (36, "lily_of_the_valley"),
                 (38, "lily_of_the_valley"), (39, "allium"), (40, "lily_of_the_valley"), (41, "allium")):
        d.set(x, 2, 6, f)                                              # borders along the garth walks
        d.set(x, 2, 12, f)
    # north walk: study carrels (desk + stool) against the wall; east walk: the monks' bench; south walk:
    # lavatorium (wash trough) and benches; lanterns hang in the walks
    for x in (31, 34, 37, 40, 43):
        d.set(x, 2, 3, "lectern[facing=south,has_book=true,powered=false]")
    for x in (32, 38):
        d.chair(x, 2, 3, "north", "dark_oak", sit=False)
    for z in (5, 8, 11):
        d.chair(44, 2, z, "east", "dark_oak")
    d.set(33, 2, 15, "water_cauldron[level=3]")
    d.set(34, 2, 15, "water_cauldron[level=3]")
    for x in (38, 41):
        d.chair(x, 2, 15, "south", "dark_oak")
    for x, z in ((31, 4), (35, 4), (39, 4), (43, 4), (31, 14), (35, 14), (39, 14), (43, 14),
                 (31, 7), (31, 11), (43, 7), (43, 11)):
        d.set(x, 6, z, lantern(True))
    # slype from the east aisle
    d.fill(25, 1, 8, 28, 1, 10, "polished_andesite")
    for x in range(25, 29):
        for z in (8, 10):
            d.fill(x, 2, z, x, 5, z, S)
        d.set(x, 6, 8, stair(TS, "south"))
        d.set(x, 6, 9, slab("deepslate_tile_slab"))
        d.set(x, 6, 10, stair(TS, "north"))
        d.set(x, 5, 9, S)
        d.clear(x, 2, 9, x, 4, 9)
    d.set(26, 4, 9, lantern(True))
    d.door(24, 2, 9, "east", "dark_oak")
    d.door(29, 2, 9, "east", "dark_oak")
    d.set(29, 4, 9, S)
    d.set(24, 4, 9, S)


def hc_lady_chapel(d, L):
    """Lady chapel beyond the chancel: tall windows, vault, Madonna statue and side altars."""
    S, ST = "stone_bricks", "stone_brick_stairs"
    d.fill(12, 1, 32, 18, 1, 40, "polished_andesite")
    d.box(11, 2, 32, 19, 12, 41, S)
    d.clear(12, 2, 31, 18, 12, 40)
    for z in range(32, 42):
        d.set(11, 2, z, "polished_andesite")
        d.set(19, 2, z, "polished_andesite")
    d.clear(14, 2, 31, 16, 7, 31)                                   # arch from the chancel
    d.set(14, 7, 31, stair(ST, "east", "top"))
    d.set(16, 7, 31, stair(ST, "west", "top"))
    for x in range(12, 19):                                          # restore the east window head
        d.set(x, 8, 31, S if x in (12, 18) else sglass(x, 8, 31))
    for z in (34, 37, 40):
        for x in (11, 19):
            lancet(d, x, z, 4, 10)
    for x in (13, 14, 15, 16, 17):
        lancet(d, x, 41, 4, 10 if x in (14, 15, 16) else 8)
    d.set(15, 11, 41, sglass(15, 11, 41))
    d.gable(11, 32, 19, 41, 13, "z", "deepslate_tile_stairs", "deepslate_tile_slab", S, 1)
    for z in (33, 36, 39):
        hc_buttress(d, 10, z, "west", 10)
        hc_buttress(d, 20, z, "east", 10)
    hc_buttress(d, 12, 42, "south", 10)
    hc_buttress(d, 18, 42, "south", 10)
    # furnishing
    d.rug(15, 32, 15, 38, 2, ("blue_carpet",), "plain")
    d.fill(13, 2, 39, 17, 2, 40, slab("polished_andesite_slab"))
    d.set(15, 3, 40, "chiseled_quartz_block")
    d.set(15, 4, 40, "calcite")
    d.set(15, 5, 40, "calcite")
    d.set(15, 6, 40, "white_stained_glass")                          # statue of the Virgin on the altar
    d.set(15, 3, 39, "blue_carpet")
    d.candle(14, 3, 40, 3, "white")
    d.candle(16, 3, 40, 3, "white")
    for z in (33, 35, 37):                                           # three rows of chairs
        for x in (12, 13, 17, 18):
            d.chair(x, 2, z, "north", "dark_oak")
    for z in (35, 38):
        chandelier(d, 15, z, 15, 9)
    for x, f in ((12, "east"), (18, "west")):
        for z in (32, 36):
            d.set(x, 5, z, f"blue_wall_banner[facing={f}]")


def hc_chapter_house(d, L):
    """Octagonal chapter house off the cloister with a central pier, stone bench ring and a tall tiled roof."""
    S = "stone_bricks"
    cx, cz, r = 38, 26, 5
    for dx in range(-r, r + 1):
        for dz in range(-r, r + 1):
            if not _oct(dx, dz, r):
                continue
            d.set(cx + dx, 1, cz + dz, "polished_andesite" if (dx + dz) % 2 else "smooth_stone")
            edge = not _oct(dx, dz, r - 1)
            for y in range(2, 11):
                d.set(cx + dx, y, cz + dz, S if edge else AIR)
            if edge:
                d.set(cx + dx, 2, cz + dz, "polished_andesite")
                d.set(cx + dx, 11, cz + dz, S)

    # canons' stone benches on the west, east and south walls, the dean's seat in the middle of the south
    # wall, two seats either side of the entrance
    for k in (-2, -1, 0, 1, 2):
        d.chair(cx - 4, 2, cz + k, "west", "stone_brick")
        d.chair(cx + 4, 2, cz + k, "east", "stone_brick")
        if k:
            d.chair(cx + k, 2, cz + 4, "south", "stone_brick")
    d.set(cx, 2, cz + 4, "chiseled_stone_bricks")
    d.chair(cx, 3, cz + 4, "south", "dark_oak", sit=False)
    for k in (-2, 2):
        d.chair(cx + k, 2, cz - 4, "north", "stone_brick")
    for dx, dz in ((0, -5), (0, 5), (-5, 0), (5, 0), (-3, -4), (3, -4), (-3, 4), (3, 4),
                   (-4, -3), (4, -3), (-4, 3), (4, 3)):
        if _oct(dx, dz, r) and not _oct(dx, dz, r - 1) and (dx, dz) != (0, -5):
            lancet(d, cx + dx, cz + dz, 4, 9)
    for y in range(2, 12):                                          # central pier
        d.set(cx, y, cz, "polished_andesite" if y < 11 else "chiseled_stone_bricks")
    for ox, oz in D4.values():
        d.set(cx + ox, 7, cz + oz, lantern(True))
        d.set(cx + ox, 8, cz + oz, stair("stone_brick_stairs", {(1, 0): "west", (-1, 0): "east", (0, 1): "north",
                                                                 (0, -1): "south"}[(ox, oz)], "top"))
    d.set(cx, 2, cz - 2, "lectern[facing=north,has_book=true,powered=false]")
    for ox, oz in ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)):
        d.set(cx + ox, 2, cz + oz, "red_carpet")                     # carpet round the central pier
    d.set(cx, 2, cz + 2, slab("dark_oak_slab", "top"))               # chapter table with candles
    d.set(cx + 1, 2, cz + 2, slab("dark_oak_slab", "top"))
    d.candle(cx, 3, cz + 2, 3)
    d.candle(cx + 1, 3, cz + 2, 1)
    for ox, f in ((-4, "east"), (4, "west")):
        d.set(cx + ox, 6, cz + 2, f"red_wall_banner[facing={f}]")
    d.fill(cx - r, 11, cz - r, cx + r, 11, cz + r, AIR)
    for dx in range(-r, r + 1):
        for dz in range(-r, r + 1):
            if _oct(dx, dz, r) and not _oct(dx, dz, r - 1):
                d.set(cx + dx, 11, cz + dz, S)          # the vault is open into the tall lantern spire
    spire(d, cx, cz, 12, 5, "deepslate_tiles", "deepslate_tile_stairs", step=2, needle=2,
          broach=False, top="lightning_rod[facing=up,powered=false,waterlogged=false]")
    for y in range(12, 17):                                        # corona: a lantern ring on chains
        d.set(cx, y, cz, CHAIN)
    for ox, oz in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
        d.set(cx + ox, 12, cz + oz, lantern(True))
    d.set(cx, 11, cz, "chiseled_stone_bricks")
    # passage from the cloister south walk
    d.fill(37, 1, 16, 39, 1, 21, "polished_andesite")
    for z in range(17, 22):
        for x in (36, 40):
            d.fill(x, 2, z, x, 5, z, S)
        d.fill(37, 6, z, 39, 6, z, S)
        d.set(36, 6, z, stair("deepslate_tile_stairs", "east"))
        d.set(40, 6, z, stair("deepslate_tile_stairs", "west"))
        d.set(38, 7, z, slab("deepslate_tile_slab"))
        d.set(37, 7, z, stair("deepslate_tile_stairs", "east"))
        d.set(39, 7, z, stair("deepslate_tile_stairs", "west"))
        d.clear(37, 2, z, 39, 5, z)
    d.clear(37, 2, 16, 39, 4, 16)
    d.clear(37, 2, 21, 39, 5, 21)
    d.set(38, 5, 19, lantern(True))
    for z in (18, 20):
        d.set(36, 4, z, "glass_pane")
        d.set(40, 4, z, "glass_pane")


def hc_house_shell(d, roof, upper):
    """Close house structure (x1..8, z29..41): stone ground floor, timber-framed upper floor, gable roof, door
    with a tiled hood on the north gable, brick chimney and hall hearth on the west wall, stair along the east
    wall, upstairs partition with a door. No furniture: each house is furnished by its own function."""
    S = "stone_bricks"
    x1, z1, x2, z2 = 1, 29, 8, 41
    d.fill(x1, 1, z1, x2, 1, z2, "spruce_planks")
    d.box(x1, 2, z1, x2, 5, z2, S, floor=None)
    for z in range(z1, z2 + 1):
        for x in (x1, x2):
            d.set(x, 2, z, "polished_andesite")
    d.fill(x1, 6, z1, x2, 6, z2, "dark_oak_planks")
    d.box(x1, 7, z1, x2, 10, z2, upper)
    for x in range(x1, x2 + 1, 2):
        for z in (z1, z2):
            d.fill(x, 7, z, x, 10, z, log("dark_oak_log"))
    for z in range(z1, z2 + 1, 2):
        for x in (x1, x2):
            d.fill(x, 7, z, x, 10, z, log("dark_oak_log"))
    for x in range(x1, x2 + 1):
        for z in (z1, z2):
            d.set(x, 10, z, log("dark_oak_log", "x"))
    for z in range(z1, z2 + 1):
        for x in (x1, x2):
            d.set(x, 10, z, log("dark_oak_log", "z"))
    for z in (31, 34, 37):                                           # window openings, both floors
        for x in (x1, x2):
            d.window(x, 3, z, x, 4, z)
            d.window(x, 8, z, x, 9, z)
    rd = d.gable(x1, z1, x2, z2, 11, "z", f"{roof}_stairs", f"{roof}_slab", upper, 1)
    d.door(4, 2, z1, "south", "dark_oak")
    d.set(4, 4, z1, S)
    d.set(3, 5, z1 - 1, stair(f"{roof}_stairs", "east"))
    d.set(4, 5, z1 - 1, slab(f"{roof}_slab"))
    d.set(5, 5, z1 - 1, stair(f"{roof}_stairs", "west"))
    d.hearth(x1 + 1, 2, 35, "east", rd + 3, "bricks", "campfire")
    for y in range(6, rd + 3):
        d.set(x1, y, 35, "bricks")
    d.set(x1, rd + 3, 35, slab("brick_slab"))
    for i, y in enumerate(range(2, 6)):
        d.set(7, y, 30 + i, stair("dark_oak_stairs", "south"))
        if y > 2:
            d.fill(7, 2, 30 + i, 7, y - 1, 30 + i, "dark_oak_planks")
    d.clear(7, 6, 30, 7, 6, 34)
    d.set(6, 7, 30, fence("dark_oak_fence"))                          # stair-well railing
    d.set(6, 7, 31, fence("dark_oak_fence"))
    d.fill(2, 7, 37, 7, 9, 37, "dark_oak_planks")
    d.door(5, 7, 37, "south", "dark_oak")
    return rd


def hc_palace(d, L):
    """Bishop's palace (red-tile roof, calcite upper floor): great hall with a long table before the hearth,
    kitchen at the back; upstairs the bishop's study (bookcases, lectern, desk) and his chamber."""
    hc_house_shell(d, "brick", "calcite")
    d.lamp(4, 4, 28)
    d.sign(5, 3, 28, "north", ["Bishop's", "Palace"], "dark_oak")
    d.dining(4, 2, 32, 5, "z", "dark_oak", chairs=("e", "w"), sit=True)
    d.rug(3, 31, 5, 31, 2, ("red_carpet",), "plain")
    d.lamp(3, 5, 34)
    d.lamp(6, 5, 34)
    d.item(7, 2, 40, "furnace", "west")
    d.item(7, 2, 39, "smoker", "west")
    d.set(7, 2, 38, "barrel[facing=up,open=false]")
    d.set(2, 2, 40, "crafting_table")
    d.set(3, 2, 40, "cauldron")
    d.set(7, 3, 40, "decorated_pot[cracked=false,facing=west,waterlogged=false]")
    for z in (31, 32, 33, 34):                                       # the bishop's library wall
        d.set(2, 7, z, "bookshelf")
        d.set(2, 8, z, "chiseled_bookshelf[facing=east,slot_0_occupied=true,slot_1_occupied=false,"
              "slot_2_occupied=true,slot_3_occupied=true,slot_4_occupied=false,slot_5_occupied=true]")
    d.set(4, 7, 33, "lectern[facing=east,has_book=true,powered=false]")
    d.chair(4, 7, 35, "south", "dark_oak")
    d.set(4, 7, 36, slab("dark_oak_slab", "top"))
    d.candle(4, 8, 36, 2)
    d.bed(3, 7, 40, "south", "purple")
    d.set(2, 7, 40, slab("dark_oak_slab", "top"))
    d.candle(2, 8, 40, 1)
    d.set(6, 7, 40, "barrel[facing=up,open=false]")
    d.rug(3, 38, 6, 39, 7, ("purple_carpet",), "plain")
    d.lamp(4, 10, 33)
    d.lamp(4, 10, 39)
    window_box(d, 1, 31, 8, "west", "spruce", "red_tulip")
    window_box(d, 1, 37, 8, "west", "spruce", "red_tulip")
    window_box(d, 8, 34, 8, "east", "spruce", "azure_bluet")
    for z in range(29, 42):                                          # box hedge along the west boundary
        d.set(0, 2, z, "oak_leaves[distance=1,persistent=true,waterlogged=false]")


def hc_deanery(d, L):
    """Deanery (blue-slate roof, yellow-washed upper floor): parlour with armchairs at the hearth and a writing
    desk, bookcases by the door, kitchen with a breakfast table at the back; upstairs the dean's bedroom with
    wardrobe chests and a prayer desk, a guest room behind."""
    hc_house_shell(d, "dark_prismarine", "yellow_terracotta")
    d.lamp(4, 4, 28)
    d.sign(5, 3, 28, "north", ["The", "Deanery"], "dark_oak")
    d.chair(4, 2, 34, "east", "oak", sit=False)                     # armchairs facing the fire
    d.chair(4, 2, 36, "east", "oak", sit=False)
    d.set(4, 2, 35, slab("oak_slab", "top"))
    d.rug(3, 34, 3, 36, 2, ("green_carpet",), "plain")
    for x, y in ((2, 2), (3, 2), (2, 3), (3, 3)):
        d.set(x, y, 30, "bookshelf")
    d.set(5, 2, 31, slab("oak_slab", "top"))                         # writing desk
    d.candle(5, 3, 31, 1)
    d.chair(5, 2, 32, "south", "oak", sit=False)
    d.item(2, 2, 40, "smoker", "east")
    d.set(3, 2, 40, "water_cauldron[level=3]")
    d.set(4, 2, 40, "barrel[facing=up,open=false]")
    d.item(7, 2, 40, "furnace", "west")
    d.set(7, 2, 39, "crafting_table")
    d.table(5, 2, 38, "oak")
    d.chair(6, 2, 38, "east", "oak", sit=False)
    d.lamp(4, 5, 32)
    d.lamp(4, 5, 38)
    d.bed(3, 7, 30, "north", "yellow")
    d.set(4, 7, 30, slab("oak_slab", "top"))
    d.candle(4, 8, 30, 2)
    d.set(2, 7, 33, "chest[facing=east,type=single,waterlogged=false]")
    d.set(2, 7, 34, "chest[facing=east,type=single,waterlogged=false]")
    d.set(5, 7, 34, "lectern[facing=north,has_book=true,powered=false]")
    d.chair(5, 7, 35, "south", "oak", sit=False)
    d.bed(6, 7, 40, "south", "light_blue")
    d.set(5, 7, 40, slab("oak_slab", "top"))
    d.candle(5, 8, 40, 1)
    d.set(2, 7, 40, "chest[facing=east,type=single,waterlogged=false]")
    d.rug(2, 38, 4, 39, 7, ("light_blue_carpet",), "plain")
    d.lamp(4, 10, 33)
    d.lamp(4, 10, 39)
    window_box(d, 8, 31, 8, "east", "warped", "allium")
    window_box(d, 8, 37, 8, "east", "warped", "allium")
    for z, f in ((30, "lilac"), (32, "peony"), (34, "lilac"), (36, "peony"), (38, "lilac"), (40, "peony")):
        d.set(0, 2, z, f"{f}[half=lower]")                          # lavender-and-lilac border
        d.set(0, 3, z, f"{f}[half=upper]")


def hc_library(d, L):
    """Chained library over the east cloister walk (as at Wells): stone upper range with lancets, tiled roof,
    bookcases in bays, reading desks; reached by an outside stair."""
    S = "stone_bricks"
    x1, x2, z1, z2 = 42, 45, 2, 16
    d.fill(x1, 8, z1, x2, 8, z2, "dark_oak_planks")
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if x in (x1, x2) or z in (z1, z2):
                d.fill(x, 9, z, x, 13, z, S)
            else:
                d.clear(x, 9, z, x, 13, z)
    for z in range(z1 + 2, z2 - 1, 2):
        for x in (x1, x2):
            lancet(d, x, z, 10, 12)
    for x in range(x1, x2 + 1):
        d.set(x, 9, z1, S)
        d.set(x, 9, z2, S)
    d.gable(x1, z1, x2, z2, 14, "z", "deepslate_tile_stairs", "deepslate_tile_slab", S, 1)
    # three bays: a pair of bookcases, then a chained reading desk, along the inner wall; the walk is free
    for z in (3, 4, 7, 8, 11, 12, 15):
        d.set(43, 9, z, "bookshelf")
        d.set(43, 10, z, "chiseled_bookshelf[facing=east,slot_0_occupied=true,slot_1_occupied=true,"
              "slot_2_occupied=false,slot_3_occupied=true,slot_4_occupied=true,slot_5_occupied=false]")
    for z in (5, 9, 13):
        d.set(43, 9, z, "lectern[facing=east,has_book=true,powered=false]")
        d.set(43, 11, z, CHAIN)
    for z in (6, 10, 14):
        d.set(43, 9, z, "chest[facing=east,type=single,waterlogged=false]")
    for z in (4, 8, 12):
        d.lamp(44, 13, z)
    d.rug(x1 + 2, z1 + 1, x1 + 2, z2 - 1, 9, ("red_carpet",), "plain")
    # outside stair along the east wall, rising south to a door at z = 11
    for i, z in enumerate(range(4, 10)):
        y = 3 + i
        d.set(46, y, z, stair("stone_brick_stairs", "south"))
        d.fill(46, 2, z, 46, y - 1, z, S)
        d.set(47, y + 1, z, wallb("stone_brick_wall"))
        d.fill(47, 2, z, 47, y, z, S)
    d.set(46, 2, 3, stair("stone_brick_stairs", "south"))
    d.fill(46, 2, 10, 46, 8, 11, S)
    d.set(47, 9, 10, wallb("stone_brick_wall"))
    d.fill(47, 2, 10, 47, 8, 11, S)
    d.door(45, 9, 11, "west", "dark_oak")
    d.set(46, 9, 12, "lantern[hanging=false,waterlogged=false]")


def stamp(d, draw, ox, oz, *args):
    """Draw a sub-building with `draw(scratch, *args)` in plot coordinates of a scratch design, then copy it into d
    shifted by (ox, oz). Used to reuse one house plan at several places of a complex."""
    sc = Design(d.pack, d.rel, (d.sx, d.sy, d.sz), gy=d.gy)
    base = {(x, y, z): st for x, y, z, st in sc.bp.blocks()}
    draw(sc, *args)
    for x, y, z, st in sc.bp.blocks():
        if y < d.gy or base.get((x, y, z)) == st:
            continue
        tx, tz = x + ox, z + oz
        if d.bp.inside(tx, y, tz):
            d.bp.set(tx, y, tz, st, sc.bp.tile_entities.get((x, y, z)))
    for (x, y, z), names in sc.tags.items():
        for n in names:
            d.tag(x + ox, y, z + oz, n)


def hc_close(d, L):
    """Cathedral close: lamp posts along the paths, graves, benches, yews, lych-gate on the street."""
    for x, z in ((1, 9), (1, 14), (2, 28), (44, 34), (44, 40), (32, 41), (32, 36)):
        yew(d, x, z, 2)
    for z in (9, 11, 13, 15):                                         # old headstones by the west aisle
        d.set(3, 2, z, "mossy_stone_bricks")
        d.set(3, 3, z, slab("mossy_stone_brick_slab"))
        d.set(3, 1, z + 1, "podzol")
    for x, z in ((36, 35), (36, 38), (39, 41), (42, 35), (42, 38)):
        d.set(x, 2, z, "cobblestone_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
        d.set(x, 1, z + 1, "podzol")
    for x, z in ((10, 0), (20, 0), (27, 0), (46, 0), (46, 20), (30, 29)):
        d.set(x, 2, z, wallb("stone_brick_wall"))
        d.set(x, 3, z, fence("dark_oak_fence"))
        d.set(x, 4, z, "lantern[hanging=false,waterlogged=false]")
    for x in (8, 22):
        d.chair(x, 2, 0, "north", "dark_oak")
    lamp_post(d, 35, 19, "polished_andesite", fence("dark_oak_fence"))       # lamps at the chapter-house door
    lamp_post(d, 41, 19, "polished_andesite", fence("dark_oak_fence"))
    for x, z in ((32, 17), (46, 17), (31, 24), (31, 28)):                   # lamps along the close paths
        lamp_post(d, x, z, "polished_andesite", fence("dark_oak_fence"))
    lamp_post(d, 33, 41, "polished_andesite", fence("dark_oak_fence"))
    d.chair(45, 2, 30, "east", "dark_oak", sit=False)
    d.chair(45, 2, 31, "east", "dark_oak", sit=False)
    for x, z in ((39, 35), (39, 38), (45, 35), (45, 38), (42, 41), (36, 41)):   # more headstones
        d.set(x, 2, z, "cobblestone_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
        d.set(x, 1, z + 1, "podzol")
    d.chair(44, 2, 22, "east", "dark_oak", sit=False)                         # bench under the chapter house
    d.chair(44, 2, 23, "east", "dark_oak", sit=False)
    # churchyard wall with coping along the street and the east side, lych-gate on the street
    for x in range(28, 48):
        if 35 <= x <= 37:
            continue
        d.set(x, 2, 0, "mossy_stone_bricks" if x % 3 == 0 else "stone_bricks")
        d.set(x, 3, 0, slab("stone_brick_slab"))
    for z in range(21, 44):
        d.set(47, 2, z, "mossy_stone_bricks" if z % 3 == 0 else "stone_bricks")
        d.set(47, 3, z, slab("stone_brick_slab"))
    for x in (34, 38):
        d.fill(x, 2, 0, x, 4, 0, log("dark_oak_log"))
    for x in range(33, 40):
        d.set(x, 5, 0, slab("deepslate_tile_slab"))
    d.fill(34, 5, 0, 38, 5, 0, log("dark_oak_log", "x"))
    for x in range(33, 40):
        d.set(x, 6, 0, slab("deepslate_tile_slab"))
    d.set(36, 7, 0, wallb("stone_brick_wall"))
    for x in range(35, 38):
        d.set(x, 1, 0, "gravel")
    # gargoyles under the nave cornice
    for z in (9, 12, 15):
        d.set(10, 15, z, stair("stone_brick_stairs", "east", "top"))
        d.set(20, 15, z, stair("stone_brick_stairs", "west", "top"))
    # gravel paths
    for x in range(26, 48):
        d.set(x, 1, 18, "gravel")
    for z in range(17, 30):
        d.set(30, 1, z, "gravel")


def cherry_tree(d, x, z):
    """One small cherry tree planted at (x, z) in a moss pit: two-log trunk and a 3x3 crown."""
    d.set(x, 1, z, "moss_block")
    d.set(x, 2, z, log("cherry_log"))
    d.set(x, 3, z, log("cherry_log"))
    for ddx in (-1, 0, 1):
        for ddz in (-1, 0, 1):
            for yy in (4, 5):
                if not (yy == 5 and ddx and ddz) and d.bp.inside(x + ddx, yy, z + ddz):
                    d.set(x + ddx, yy, z + ddz, "cherry_leaves[distance=1,persistent=true,waterlogged=false]")


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
CC_SIZE = (48, 50, 48)
CC_TX, CC_TZ, CC_TW = (0, 20), 1, 7           # timber belfries (wings)
CC_WHUT = (1, 1, 5)
CC_SHAFT = {1: 6, 2: 11, 3: 13, 4: 14, 5: 15}  # belfry shaft top (local y)


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
            if not d.bp.inside(x, yy, z):
                continue
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
    d.set(1, 1, 1, "barrel[facing=up,open=false]")
    d.set(1, 2, 1, "candle[candles=2,lit=false,waterlogged=false]")
    d.set(5, 1, 1, "spruce_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
    d.set(5, 2, 1, "potted_fern")
    d.rug(2, 2, 2, 3, 1, ("green_carpet",), "plain")
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
    R, st, nd = {1: (1, 2, 1), 2: (1, 2, 2), 3: (2, 2, 2), 4: (2, 3, 3), 5: (2, 3, 4)}[L]
    spire(d, 3, 3, T + 5, R, "dark_oak_planks", "dark_oak_stairs", step=st, needle=nd,
          needle_block=fence("dark_oak_fence"), cross=L == 5, broach=False,
          top="lightning_rod[facing=up,powered=false,waterlogged=false]" if L >= 3 else fence("dark_oak_fence"))
    return d


CC_PAL = {
    # roof stairs, roof body, roof slab, main log, alternate log, door/shutter wood, gable trim, accent band
    "parsonage": ("mangrove_stairs", "mangrove_planks", "mangrove_slab", "spruce_log", "stripped_spruce_log",
                  "mangrove", "stripped_spruce_log", "red_terracotta"),
    "hall": ("dark_prismarine_stairs", "dark_prismarine", "dark_prismarine_slab", "dark_oak_log",
             "stripped_dark_oak_log", "spruce", "stripped_spruce_log", "green_terracotta"),
    "store": ("spruce_stairs", "spruce_planks", "spruce_slab", "stripped_spruce_log", "spruce_log",
              "spruce", "spruce_log", None),
    "cabin_birch": ("cobbled_deepslate_stairs", "cobbled_deepslate", "cobbled_deepslate_slab", "birch_log",
                    "stripped_birch_log", "dark_oak", "dark_oak_log", "green_terracotta"),
    "cabin_red": ("deepslate_tile_stairs", "deepslate_tiles", "deepslate_tile_slab", "mangrove_log",
                  "stripped_mangrove_log", "spruce", "stripped_spruce_log", "yellow_terracotta"),
    "lodge": ("cobbled_deepslate_stairs", "cobbled_deepslate", "cobbled_deepslate_slab", "spruce_log",
              "stripped_spruce_log", "dark_oak", "stripped_dark_oak_log", "yellow_terracotta"),
}


def cc_log_house(d, x1, z1, w, l, kind, H=5, pal=None):
    """Structure only (no furniture, no dressing): log walls on a river-rock footing (or stone piers for a
    'store'), window openings every third log bay on the long walls, north door with a covered porch frame,
    steep / gable roof with king posts and a finial, stone chimney + hearth on the south gable, and for a
    'lodge' an upper floor with a stair along the west wall. Each building is furnished by its own function."""
    x2, z2 = x1 + w - 1, z1 + l - 1
    R, RB, RS, LG, LG2, WD, TRIM, ACC = CC_PAL[pal or kind]
    fy = 2 if kind == "store" else 1                                # floor level (store sits on piers)
    if kind == "store":
        for x in (x1, x2):
            for z in range(z1, z2 + 1, 2):
                d.set(x, 2, z, "mossy_cobblestone")
    d.fill(x1 + 1, fy, z1 + 1, x2 - 1, fy, z2 - 1, "spruce_planks")
    top = fy + H
    for y in range(fy, top + 1):
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                if not (x in (x1, x2) or z in (z1, z2)):
                    if y > fy:
                        d.set(x, y, z, AIR)
                    continue
                if y == fy and kind != "store":
                    d.set(x, y, z, "cobblestone" if (x + z) % 3 else "mossy_cobblestone")
                    continue
                corner = x in (x1, x2) and z in (z1, z2)
                ax = "x" if z in (z1, z2) else "z"
                if corner:
                    d.set(x, y, z, log(LG2 if y % 2 else LG, "x" if y % 2 else "z"))
                elif ACC and y == top:
                    d.set(x, y, z, ACC)
                else:
                    d.set(x, y, z, log(LG, ax) if (y + (0 if ax == "x" else 1)) % 2 else log(LG2, ax))
    if kind != "store":
        d.fill(x1 + 1, 1, z1 + 1, x2 - 1, 1, z2 - 1, "spruce_planks")
    wy = fy + 2
    for z in range(z1 + 2, z2 - 1, 3):                               # window openings (structure)
        for x in (x1, x2):
            d.window(x, wy, z, x, wy + 1, z)
    dx = (x1 + x2) // 2
    d.door(dx, fy + 1, z1, "south", WD)
    if kind == "store":
        d.set(dx, 2, z1 - 1, stair("spruce_stairs", "south"))
    else:                                                            # porch frame: deck, posts, rail, roof
        d.fill(x1, 1, z1 - 2, x2, 1, z1 - 1, "spruce_planks")
        for x in (x1, x2):
            d.fill(x, 2, z1 - 2, x, top - 1, z1 - 2, log(TRIM))
        for x in range(x1 + 1, x2):
            if x != dx:
                d.set(x, 2, z1 - 2, fence("spruce_fence"))
        for x in range(x1 - 1, x2 + 2):
            d.set(x, top, z1 - 2, stair(R, "south"))
            d.set(x, top, z1 - 1, RB)
    if w <= 9:
        rd = steep_gable(d, x1, z1, x2, z2, top + 1, R, RB, log(LG, "x"), "z", 1)
    else:
        rd = d.gable(x1, z1, x2, z2, top + 1, "z", R, RS, log(LG, "x"), 1)
        for z in range(z1 - 1, z2 + 2):                              # ridge cap
            d.set(dx, rd, z, RB)
            d.set(dx, rd + 1, z, slab(RS))
    for zz in (z1, z2):                                              # gable king posts
        for y in range(top + 1, rd - 1):
            d.set(dx, y, zz, log(TRIM))
    d.set(dx, rd + (2 if w > 9 else 1), z1 - 1, fence("spruce_fence"))   # finial
    if kind != "store":                                              # chimney + hearth
        for y in range(1, rd + 2):
            d.set(dx, y, z2 + 1, "cobblestone" if y % 3 else "mossy_cobblestone")
        d.set(dx, rd + 2, z2 + 1, "campfire[facing=north,lit=false,signal_fire=false,waterlogged=false]")
        d.hearth(dx, fy + 1, z2 - 1, "north", fy + 4, "cobblestone", "campfire")
        for y in range(fy + 4, top + 1):
            d.set(dx, y, z2 - 1, AIR)
    if kind == "lodge":                                              # upper floor + stair (structure)
        fy2 = fy + 5
        d.fill(x1 + 1, fy2, z1 + 1, x2 - 1, fy2, z2 - 1, "spruce_planks")
        for i in range(4):
            zz = z1 + 2 + i
            d.set(x1 + 1, fy + 1 + i, zz, stair("spruce_stairs", "south"))
            if i:
                d.fill(x1 + 1, fy + 1, zz, x1 + 1, fy + i, zz, "spruce_planks")
        d.clear(x1 + 1, fy2, z1 + 2, x1 + 1, fy2, z1 + 5)
        d.set(x1 + 2, fy2 + 1, z1 + 2, fence("spruce_fence"))        # stair-well railing
        d.set(x1 + 2, fy2 + 1, z1 + 3, fence("spruce_fence"))
        d.set(x1 + 2, fy2 + 1, z1 + 4, fence("spruce_fence"))
    return rd


def shutters(d, x, z, y, facing, wood):
    """A pair of open shutters beside the window at (x, y..y+1, z) on a wall whose outside faces `facing`."""
    ox = D4[facing][0]
    for dz in (-1, 1):
        for yy in (y, y + 1):
            d.set(x + ox, yy, z + dz, trap(f"{wood}_trapdoor", facing, "bottom", True))


def window_box(d, x, z, y, facing, wood, flower):
    """Flower box under the window at (x, y, z): trapdoor box front with a potted flower on it."""
    ox = D4[facing][0]
    d.set(x + ox, y - 1, z, trap(f"{wood}_trapdoor", facing, "top"))
    d.set(x + ox, y, z, f"potted_{flower}")


# Each Cascadia building below is furnished by hand: coordinates are absolute plot cells chosen for that room.
def cc_parsonage(d):
    """Parsonage (x30..37, z4..14): kitchen run on the east wall, dining table under the west window,
    armchairs facing the hearth at the back, the pastor's bed and nightstand in the south-west corner, study
    corner with lectern and bookcase; porch with a rocking chair and a rain barrel."""
    cc_log_house(d, 30, 4, 8, 11, "parsonage")
    d.item(36, 2, 5, "smoker", "west")
    d.set(36, 2, 6, "water_cauldron[level=3]")
    d.set(36, 2, 7, "barrel[facing=up,open=false]")
    d.set(36, 3, 7, "decorated_pot[cracked=false,facing=west,waterlogged=false]")
    d.set(36, 2, 8, "crafting_table")
    d.table(31, 2, 7, "spruce")
    d.chair(31, 2, 6, "north", "spruce", sit=False)
    d.chair(31, 2, 8, "south", "spruce", sit=False)
    d.chair(32, 2, 7, "east", "spruce", sit=False)
    d.chair(32, 2, 11, "north", "spruce", sit=False)
    d.chair(34, 2, 11, "north", "spruce", sit=False)
    d.set(33, 2, 12, "green_carpet")
    d.set(34, 2, 12, "green_carpet")
    d.bed(31, 2, 12, "west", "green")
    d.set(31, 2, 13, slab("spruce_slab", "top"))
    d.candle(31, 3, 13, 2)
    d.set(36, 2, 11, "lectern[facing=west,has_book=true,powered=false]")
    d.chair(35, 2, 11, "west", "spruce", sit=False)
    d.bookshelf(36, 2, 12, 2)
    d.set(36, 2, 13, "chiseled_bookshelf[facing=west,slot_0_occupied=true,slot_1_occupied=false,"
          "slot_2_occupied=true,slot_3_occupied=true,slot_4_occupied=false,slot_5_occupied=true]")
    d.lamp(33, 6, 6)
    d.lamp(33, 6, 10)
    d.chair(31, 2, 3, "south", "spruce", sit=False)
    d.set(36, 2, 3, "barrel[facing=up,open=false]")
    d.lamp(32, 5, 3)
    shutters(d, 30, 6, 3, "west", "mangrove")
    shutters(d, 30, 9, 3, "west", "mangrove")
    window_box(d, 30, 12, 3, "west", "mangrove", "red_tulip")
    shutters(d, 37, 6, 3, "east", "mangrove")
    window_box(d, 37, 12, 3, "east", "mangrove", "cornflower")


def cc_stabbur(d):
    """Stabbur storehouse on piers (x40..44, z4..10): barrel stack and hay in the west bay, grain sacks and a
    cask in the east bay, composter and fish barrel at the back, lantern on the ridge beam."""
    cc_log_house(d, 40, 4, 5, 7, "store", H=4)
    for x, y, z, b in ((41, 3, 5, "barrel[facing=up,open=false]"), (41, 4, 5, "barrel[facing=up,open=false]"),
                       (41, 3, 6, "barrel[facing=up,open=false]"), (41, 3, 7, "hay_block[axis=y]"),
                       (43, 3, 5, "white_wool"), (43, 4, 5, "white_wool"), (43, 3, 6, "white_wool"),
                       (43, 3, 7, "barrel[facing=north,open=false]"), (41, 3, 9, "composter[level=0]"),
                       (43, 3, 9, "barrel[facing=up,open=false]")):
        d.set(x, y, z, b)
    d.lamp(42, 6, 7)


def cc_parish_hall(d):
    """Parish hall (x29..43, z19..31): servery on the west by the door, two long tables with benches, a
    stage with lectern and flags on the east side, armchairs at the hearth, two chandeliers; benches on the
    porch."""
    cc_log_house(d, 29, 19, 15, 13, "hall", H=7)
    d.set(30, 2, 20, "barrel[facing=up,open=false]")
    d.item(31, 2, 20, "smoker", "south")
    d.set(30, 2, 21, "water_cauldron[level=3]")
    d.set(30, 2, 22, "crafting_table")
    d.dining(33, 2, 22, 4, "z", "spruce", chairs=("e", "w"))
    d.dining(38, 2, 22, 4, "z", "spruce", chairs=("e", "w"))
    d.fill(41, 2, 22, 42, 2, 28, slab("spruce_slab", "top"))         # stage
    d.set(41, 3, 25, "lectern[facing=west,has_book=true,powered=false]")
    d.set(42, 3, 23, "note_block[instrument=harp,note=0,powered=false]")
    d.set(42, 3, 27, "jukebox[has_record=false]")
    d.set(42, 5, 23, "red_wall_banner[facing=west]")
    d.set(42, 5, 25, "white_wall_banner[facing=west]")
    d.set(42, 5, 27, "red_wall_banner[facing=west]")
    d.chair(35, 2, 28, "north", "spruce", sit=False)
    d.chair(37, 2, 28, "north", "spruce", sit=False)
    d.rug(35, 29, 37, 29, 2, ("red_carpet",), "plain")
    d.set(42, 2, 20, "barrel[facing=up,open=false]")
    d.set(42, 3, 20, "potted_fern")
    chandelier(d, 36, 23, 12, 7)
    chandelier(d, 36, 27, 12, 7)
    d.chair(30, 2, 18, "south", "spruce", sit=False)
    d.chair(42, 2, 18, "south", "spruce", sit=False)
    d.lamp(35, 7, 18)
    shutters(d, 29, 21, 3, "west", "spruce")
    shutters(d, 29, 27, 3, "west", "spruce")
    window_box(d, 29, 24, 3, "west", "spruce", "oxeye_daisy")
    shutters(d, 43, 24, 3, "east", "spruce")
    d.set(31, 2, 26, "lectern[facing=east,has_book=true,powered=false]")      # notice desk with hymn books
    d.bookshelf(30, 2, 27, 2)
    d.bookshelf(30, 2, 28, 2)
    d.set(30, 2, 29, "barrel[facing=up,open=false]")
    d.set(30, 3, 29, "potted_fern")
    for x, z, f in ((28, 18, "poppy"), (28, 17, "cornflower"), (44, 18, "poppy"), (44, 17, "oxeye_daisy")):
        d.set(x, 1, z, "coarse_dirt")
        d.set(x, 2, z, f)


def cc_sexton_cabin(d):
    """Sexton's cabin (x2..10, z31..39, birch logs): tool bench and grindstone by the door, table for two under
    the west window, armchair at the fire, bed with nightstand in the south-west corner, spade board."""
    cc_log_house(d, 2, 31, 9, 9, "parsonage", pal="cabin_birch")
    d.set(9, 2, 32, "crafting_table")
    d.item(9, 2, 33, "grindstone", "west")
    d.set(9, 3, 34, trap("dark_oak_trapdoor", "west", "bottom", True))
    d.table(4, 2, 33, "dark_oak")
    d.chair(4, 2, 34, "south", "dark_oak", sit=False)
    d.chair(5, 2, 33, "east", "dark_oak", sit=False)
    d.chair(5, 2, 36, "north", "dark_oak", sit=False)
    d.rug(5, 37, 7, 37, 2, ("brown_carpet",), "plain")
    d.bed(3, 2, 37, "west", "white")
    d.set(3, 2, 38, slab("dark_oak_slab", "top"))
    d.candle(3, 3, 38, 1)
    d.set(9, 2, 38, "barrel[facing=up,open=false]")
    d.lamp(6, 6, 34)
    d.chair(3, 2, 30, "south", "dark_oak", sit=False)
    shutters(d, 2, 33, 3, "west", "dark_oak")
    window_box(d, 10, 36, 3, "east", "dark_oak", "allium")


def cc_verger_cabin(d):
    """Verger's cabin (x16..24, z32..40, red mangrove logs): vestment chests, candle-making bench with wax
    barrel, armchair at the fire, small table, bookcase, bed on the east side."""
    cc_log_house(d, 16, 32, 9, 9, "parsonage", pal="cabin_red")
    d.set(17, 2, 33, "chest[facing=east,type=single,waterlogged=false]")
    d.set(17, 2, 34, "chest[facing=east,type=single,waterlogged=false]")
    d.set(17, 2, 37, slab("spruce_slab", "top"))
    d.candle(17, 3, 37, 4)
    d.set(17, 2, 38, "barrel[facing=up,open=false]")
    d.chair(19, 2, 37, "north", "spruce", sit=False)
    d.table(22, 2, 34, "spruce")
    d.chair(22, 2, 35, "south", "spruce", sit=False)
    d.chair(21, 2, 34, "west", "spruce", sit=False)
    d.bookshelf(23, 2, 33, 2)
    d.bed(23, 2, 38, "east", "yellow")
    d.set(23, 2, 39, slab("spruce_slab", "top"))
    d.candle(23, 3, 39, 2)
    d.lamp(20, 6, 35)
    d.set(23, 2, 31, "barrel[facing=up,open=false]")
    shutters(d, 24, 34, 3, "east", "spruce")
    window_box(d, 16, 37, 3, "west", "spruce", "poppy")


def cc_pilgrim_lodge(d):
    """Pilgrims' lodge (x30..42, z36..46), two storeys: refectory table and kitchen run downstairs, hearth with
    armchairs; dormitory upstairs with bunks and chests along the east wall, two beds on the west, wash basin."""
    cc_log_house(d, 30, 36, 13, 11, "lodge", H=9)
    d.dining(34, 2, 38, 5, "z", "spruce", chairs=("e", "w"))
    for z, b in ((37, "barrel[facing=up,open=false]"), (38, "crafting_table"), (40, "water_cauldron[level=3]"),
                 (41, "barrel[facing=up,open=false]")):
        d.set(41, 2, z, b)
    d.item(41, 2, 39, "smoker", "west")
    d.chair(35, 2, 43, "north", "spruce", sit=False)
    d.chair(37, 2, 43, "north", "spruce", sit=False)
    d.rug(35, 44, 37, 44, 2, ("brown_carpet",), "plain")
    d.lamp(36, 5, 39)
    d.lamp(36, 5, 42)
    for z in (38, 41, 44):
        d.bed(41, 7, z, "east", "brown")
    d.set(41, 7, 39, "chest[facing=west,type=single,waterlogged=false]")
    d.set(41, 7, 42, "chest[facing=west,type=single,waterlogged=false]")
    d.bed(31, 7, 43, "west", "green")
    d.bed(31, 7, 45, "west", "green")
    d.set(31, 7, 44, "barrel[facing=up,open=false]")
    d.set(33, 7, 37, "water_cauldron[level=3]")
    d.rug(35, 39, 37, 43, 7, ("brown_carpet", "green_carpet"))
    d.lamp(36, 10, 40)
    d.lamp(36, 10, 44)
    d.chair(32, 2, 35, "south", "spruce", sit=False)
    d.set(40, 2, 35, "barrel[facing=up,open=false]")
    d.lamp(34, 9, 35)
    shutters(d, 30, 38, 3, "west", "dark_oak")
    shutters(d, 30, 44, 3, "west", "dark_oak")
    window_box(d, 42, 41, 3, "east", "dark_oak", "dandelion")


def cc_well(d, x, z):
    """Draw-well in the close: river-rock curb round the water, two log posts, a shingled hood, bucket chain."""
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            if dx or dz:
                d.set(x + dx, 2, z + dz, "mossy_cobblestone" if (dx + dz) % 2 else "cobblestone")
    d.set(x, 1, z, "water")
    d.set(x, 0, z, "cobblestone")
    for dx in (-1, 1):
        d.set(x + dx, 3, z, log("stripped_spruce_log"))
        d.set(x + dx, 4, z, log("stripped_spruce_log"))
    d.fill(x - 1, 5, z, x + 1, 5, z, log("spruce_log", "x"))
    for dx in (-2, -1, 0, 1, 2):
        d.set(x + dx, 5, z - 1, stair("dark_oak_stairs", "south"))
        d.set(x + dx, 5, z + 1, stair("dark_oak_stairs", "north"))
        d.set(x + dx, 6, z, slab("dark_oak_slab"))
    d.set(x, 4, z, CHAIN)
    d.set(x, 3, z, CHAIN)
    d.set(x + 2, 2, z, "barrel[facing=up,open=false]")


def cc_smokehouse(d):
    """Smokehouse (x0..4, z41..46): fire pit at the back, smoked fish (dried kelp) racks, salt barrels."""
    cc_log_house(d, 0, 41, 5, 6, "store", H=4)
    d.set(1, 3, 42, "barrel[facing=up,open=false]")
    d.set(3, 3, 42, "barrel[facing=up,open=false]")
    d.set(1, 3, 44, "dried_kelp_block")
    d.set(3, 3, 44, "dried_kelp_block")
    d.set(2, 3, 45, "campfire[facing=north,lit=false,signal_fire=false,waterlogged=false]")
    d.set(2, 5, 44, CHAIN)
    d.lamp(2, 4, 44)


def cg_museum(d):
    """Logging museum (x1..11, z24..36): cross-section of a giant log in the middle, saw and axe displays on the
    west wall, sharpening bench and tool barrel on the east, the visitors' book, benches at the hearth."""
    cc_log_house(d, 1, 24, 11, 13, "hall", H=5, pal="museum")
    d.set(6, 2, 30, "stripped_spruce_wood[axis=y]")                  # log cross-section
    d.set(6, 3, 30, "moss_carpet")
    d.set(5, 2, 30, log("spruce_log", "x"))
    d.set(7, 2, 30, log("spruce_log", "x"))
    d.set(2, 2, 27, "stripped_spruce_wood[axis=y]")
    d.set(2, 3, 27, "iron_bars")
    d.set(2, 2, 29, "stripped_spruce_wood[axis=y]")
    d.set(2, 3, 29, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    d.set(2, 2, 32, "lectern[facing=east,has_book=true,powered=false]")
    d.set(10, 2, 26, "barrel[facing=up,open=false]")
    d.item(10, 2, 27, "grindstone", "west")
    d.set(10, 2, 29, "cartography_table")
    d.set(10, 2, 31, "bookshelf")
    d.chair(5, 2, 33, "north", "spruce", sit=False)
    d.chair(7, 2, 33, "north", "spruce", sit=False)
    d.rug(5, 34, 7, 34, 2, ("green_carpet",), "plain")
    d.lamp(6, 6, 27)
    d.lamp(6, 6, 32)
    d.chair(2, 2, 23, "south", "spruce", sit=False)
    d.set(10, 2, 23, "barrel[facing=up,open=false]")
    d.sign(7, 4, 23, "north", ["LOGGING", "MUSEUM"], "spruce")
    window_box(d, 11, 29, 3, "east", "dark_oak", "fern")


def cg_bunkhouse(d):
    """Bunkhouse (x31..39, z37..46): mess table and stove downstairs, bunks and footlockers upstairs."""
    cc_log_house(d, 31, 37, 9, 10, "lodge", H=9, pal="bunk")
    d.dining(37, 2, 39, 3, "z", "spruce", chairs=("e", "w"))
    d.set(38, 2, 38, "crafting_table")
    d.item(38, 2, 43, "smoker", "west")
    d.set(38, 2, 44, "barrel[facing=up,open=false]")
    d.set(32, 2, 43, "water_cauldron[level=3]")
    d.set(32, 2, 44, "barrel[facing=up,open=false]")
    d.chair(35, 2, 43, "north", "spruce", sit=False)
    d.lamp(35, 5, 40)
    for z in (39, 42, 45):
        d.bed(38, 7, z, "east", "red")
    d.set(38, 7, 40, "chest[facing=west,type=single,waterlogged=false]")
    d.set(38, 7, 43, "chest[facing=west,type=single,waterlogged=false]")
    d.bed(32, 7, 44, "west", "yellow")
    d.rug(34, 40, 35, 43, 7, ("red_carpet", "black_carpet"), "check")
    d.lamp(35, 10, 41)
    d.lamp(35, 10, 44)
    d.chair(32, 2, 36, "south", "spruce", sit=False)
    d.set(38, 2, 36, "barrel[facing=up,open=false]")
    d.lamp(33, 9, 36)
    shutters(d, 31, 39, 3, "west", "spruce")


def cg_toolstore(d):
    """Tool store (x2..8, z41..47): anvil and grindstone on the west, workbench and smithing table on the east,
    oil barrels and a chest of wedges at the back."""
    cc_log_house(d, 2, 41, 7, 7, "store", H=4)
    d.item(3, 3, 42, "grindstone", "east")
    d.set(3, 3, 43, "anvil[facing=north]")
    d.set(3, 3, 45, "barrel[facing=up,open=false]")
    d.set(7, 3, 42, "crafting_table")
    d.set(7, 3, 43, "smithing_table")
    d.set(7, 3, 45, "barrel[facing=up,open=false]")
    d.set(5, 3, 46, "chest[facing=north,type=single,waterlogged=false]")
    d.lamp(5, 6, 44)


def cc_lychgate(d, x1, z, x2):
    """Roofed timber lych-gate in the churchyard fence."""
    for x in (x1, x2):
        d.fill(x, 2, z, x, 4, z, log("stripped_spruce_log"))
        d.set(x, 2, z - 1, stair("spruce_stairs", "east" if x == x1 else "west"))
    for x in range(x1, x2 + 1):
        d.set(x, 5, z, log("spruce_log", "x"))
        d.set(x, 6, z - 1, stair("dark_oak_stairs", "south"))
        d.set(x, 6, z + 1, stair("dark_oak_stairs", "north"))
        d.set(x, 6, z, "dark_oak_planks")
        d.set(x, 7, z, slab("dark_oak_slab"))
    for x in (x1 - 1, x2 + 1):
        d.set(x, 5, z - 1, stair("dark_oak_stairs", "south"))
        d.set(x, 5, z + 1, stair("dark_oak_stairs", "north"))
        d.set(x, 5, z, "dark_oak_planks")
    d.set((x1 + x2) // 2, 4, z, lantern(True))


def cc_yard(d, L):
    """Close furniture: covered walk from the church gallery to the hall porch, woodpiles, a hay wagon,
    benches and flower beds."""
    R = "dark_oak_stairs"
    for x in range(22, 29):
        d.fill(x, 1, 17, x, 1, 19, "spruce_planks")
        for z, f, y in ((16, "south", 5), (17, "south", 6), (19, "north", 6), (20, "north", 5)):
            d.set(x, y, z, stair(R, f))
        d.set(x, 7, 18, slab("dark_oak_slab"))
        d.set(x, 6, 18, "dark_oak_planks")
        if x % 3 == 1:
            for z in (17, 19):
                d.fill(x, 2, z, x, 5, z, log("stripped_spruce_log"))
        else:
            for z in (17, 19):
                d.set(x, 5, z, log("spruce_log", "x"))
    d.set(25, 5, 18, lantern(True))
    # woodpiles against the parsonage and the hall
    for z in range(5, 14, 1):
        d.set(28, 2, z, log("spruce_log", "x"))
        if z % 2:
            d.set(28, 3, z, log("spruce_log", "x"))
    for x in range(44, 47):                                          # firewood stacks by the hall
        for z in (20, 22, 24, 26, 28):
            d.set(x, 2, z, log("oak_log", "z"))
    # hay wagon
    for x in range(41, 46):
        d.set(x, 2, 14, "hay_block[axis=x]")
        d.set(x, 3, 14, "hay_block[axis=x]" if 42 <= x <= 44 else AIR)
    for x in (41, 45):
        d.set(x, 2, 13, "spruce_trapdoor[facing=north,half=bottom,open=true,powered=false,waterlogged=false]")
        d.set(x, 2, 15, "spruce_trapdoor[facing=south,half=bottom,open=true,powered=false,waterlogged=false]")
    d.set(40, 2, 14, fence("spruce_fence"))
    # benches and flower beds along the path
    for z in (5, 9):
        d.chair(11, 2, z, "west", "spruce", sit=False)
        d.chair(15, 2, z, "east", "spruce", sit=False)
    for x in range(8, 11):
        for z in (4, 8):
            d.set(x, 2, z, "rose_bush[half=lower]" if x % 2 else "peony[half=lower]")
            d.set(x, 3, z, "rose_bush[half=upper]" if x % 2 else "peony[half=upper]")
    for x in range(16, 19):
        for z in (4, 8):
            d.set(x, 2, z, "lilac[half=lower]")
            d.set(x, 3, z, "lilac[half=upper]")


def dragon(d, x, y, z, out):
    """Carved dragon-head finial at a gable apex, projecting toward `out`."""
    ox, oz = D4[out]
    d.set(x, y, z, fence("dark_oak_fence"))
    d.set(x, y + 1, z, stair("dark_oak_stairs", OPP[out], "top"))
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
    zE = 19 if L == 1 else 23                    # nave east wall
    WT = 10 if L == 1 else 13                    # nave wall top
    d.fill(10, 1, 12, 16, 1, zE - 1, "spruce_planks")
    for x in range(9, 18):
        for z in range(11, zE + 1):
            if x in (9, 17) or z in (11, zE):
                d.fill(x, 2, z, x, WT, z, W)
    for x, z in ((9, 11), (17, 11), (9, zE), (17, zE)):
        d.fill(x, 2, z, x, WT, z, log("spruce_log"))
    for x in range(9, 18):
        for z in (11, zE):
            d.set(x, 2, z, "cobblestone")
    for z in range(11, zE + 1):
        for x in (9, 17):
            d.set(x, 2, z, "cobblestone")
    d.clear(10, 2, 12, 16, WT, zE - 1)
    if L >= 2:                                     # masts and arcade toward the aisles
        for x in (9, 17):
            for z in range(12, 23):
                for y in range(2, 9):
                    d.set(x, y, z, TR if (z - 12) % 3 == 0 else (AIR if y < 8 else stair(
                        "spruce_stairs", "east" if x == 9 else "west", "top") if y == 8 else AIR))
        for z in range(12, 23, 3):
            for x in (9, 17):
                d.set(x, 9, z, TR)
    for z in (13, 17, 21):                         # clerestory "eye" windows with hoods
        if z < zE:
            for x, f in ((9, "west"), (17, "east")):
                d.set(x, WT - 2, z, "glass_pane")
                ox = -1 if x == 9 else 1
                if L == 1:
                    d.set(x, 5, z, "glass_pane")
                    d.set(x + ox, 6, z, trap("spruce_trapdoor", f, "top"))
    for x in (11, 15):
        d.set(x, WT - 2, 11, "glass_pane")
    nr = steep_gable(d, 9, 11, 17, zE, WT + 1, R, RB, W, "z", 1)
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
        d.set(13, 2, zE - 1, "stripped_spruce_wood[axis=y]")
        d.candle(13, 3, zE - 1, 4)
        d.set(12, 2, zE - 1, "spruce_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
        d.set(14, 2, zE - 1, "spruce_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
        d.set(11, 2, zE - 2, "lectern[facing=south,has_book=true,powered=false]")
        d.set(13, WT - 4, zE, "yellow_stained_glass_pane")
        d.set(13, WT - 3, zE, "yellow_stained_glass_pane")
    # pews, hut, lighting
    d.hut(10, 2, 12)
    d.set(16, 2, 12, "water_cauldron[level=3]")                     # font by the door
    for x in (10, 16):
        lamp_post(d, x, 3, "mossy_cobblestone", log("stripped_spruce_log"))
    if L == 1:                                     # ferns and lilacs along the little chapel
        for x in (8, 18):
            d.set(x, 2, 12, "fern")
            d.set(x, 2, 14, "lilac[half=lower]")
            d.set(x, 3, 14, "lilac[half=upper]")
            d.set(x, 2, 16, "fern")
    d.rug(13, 12, 13, 22 if L >= 3 else zE - 3, 2, ("red_carpet",), "plain")
    pz = [14, 16, 18, 20] if L >= 3 else ([14, 16, 18] if L == 2 else [14, 16])
    pews(d, 10, 12, pz, 2, "spruce")
    pews(d, 14, 16, pz, 2, "spruce")
    for z in (14, 18, 22):
        if z < zE - 1:
            chandelier(d, 13, z, nr - 3, WT - 3)
    for z in ((13, 17) if L == 1 else (13, 17, 21)):     # wall torches between the windows
        d.set(10, 4, z, "wall_torch[facing=east]")
        d.set(16, 4, z, "wall_torch[facing=west]")
    if L >= 2:
        for z in (13, 19):
            d.lamp(8, 6, z)
            d.lamp(18, 6, z)
    # ---------------- roof turret (takrytter), stacked tiers
    cz = (11 + zE) // 2
    th = {1: nr + 2, 2: 24, 3: 26, 4: 27, 5: 28}[L]
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
        top = spire(d, 13, cz, top - 1, 1, RB, R, step=3, needle=6, needle_block=fence("dark_oak_fence"),
                    cross=True, broach=False)
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
    if L >= 4:
        for x in (1, 3, 23, 25):
            for z in (12, 16, 20, 24):
                d.set(x, 2, z, "mossy_cobblestone_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
                d.set(x, 1, z - 1, "podzol")
        for x, z in ((2, 28), (24, 28), (8, 29), (18, 29)):
            yew(d, x, z, 2, "spruce_leaves", "spruce_log")
    # ---------------- the chapel close grows: parsonage, parish hall, stabbur, sexton's and verger's cabins
    if L >= 3:
        cc_parsonage(d)
        for x in range(15, 30):
            d.set(x, 1, 2, "gravel")
    if L >= 4:
        cc_parish_hall(d)
        for z in range(15, 19):
            d.set(36, 1, z, "gravel")
    if L >= 3:
        cc_stabbur(d)
    if L >= 4:
        cc_yard(d, L)
        cc_lychgate(d, 11, 1, 15)
        for x in list(range(7, 10)) + list(range(17, 20)) + list(range(27, 46)):     # street rail fence
            d.set(x, 2, 0, fence("spruce_fence"))
    if L >= 5:
        cc_sexton_cabin(d)
        cc_verger_cabin(d)
        for z in list(range(8, 18)) + list(range(19, 29)):                  # graveyard rail fences
            d.set(0, 2, z, fence("spruce_fence"))
            d.set(27, 2, z, fence("spruce_fence"))
        lamp_post(d, 1, 29, "mossy_cobblestone", log("stripped_spruce_log"))   # sexton's gate lamp
        for x, z, f in ((11, 30, "poppy"), (11, 31, "cornflower"), (11, 32, "allium")):
            d.set(x, 1, z, "coarse_dirt")
            d.set(x, 2, z, f)
        for x, f in ((16, "poppy"), (17, "cornflower"), (18, "oxeye_daisy"), (19, "allium"),    # verger's
                     (21, "allium"), (22, "oxeye_daisy"), (23, "cornflower"), (24, "poppy")):   # front bed
            d.set(x, 1, 29, "coarse_dirt")
            d.set(x, 2, 29, f)
        d.set(20, 1, 29, "gravel")
        lamp_post(d, 15, 29, "mossy_cobblestone", log("stripped_spruce_log"))
        lamp_post(d, 25, 29, "mossy_cobblestone", log("stripped_spruce_log"))
        cc_pilgrim_lodge(d)
        cc_smokehouse(d)
        cc_well(d, 27, 33)
        d.chair(25, 2, 31, "west", "spruce", sit=False)               # bench by the well
        d.chair(25, 2, 32, "west", "spruce", sit=False)
        d.set(29, 2, 31, "barrel[facing=up,open=false]")              # water butt and bucket stand
        d.set(29, 2, 32, "cauldron")
        for x, y, z, b in ((6, 2, 43, "spruce_planks"), (7, 2, 43, "spruce_planks"), (6, 3, 43, "hay_block[axis=y]"),
                           (7, 3, 43, log("oak_log", "x")), (8, 2, 43, fence("spruce_fence")),
                           (6, 2, 42, trap("spruce_trapdoor", "north", "bottom", True)),
                           (6, 2, 44, trap("spruce_trapdoor", "south", "bottom", True))):
            d.set(x, y, z, b)                                         # hand cart by the smokehouse
        for z in range(32, 36):
            d.set(36, 1, z, "gravel")
        for x, f in ((31, "dandelion"), (32, "poppy"), (33, "cornflower"), (34, "oxeye_daisy"),
                     (35, "dandelion"), (37, "dandelion"), (38, "oxeye_daisy"), (39, "cornflower"),
                     (40, "poppy"), (41, "dandelion")):                     # lodge front garden
            d.set(x, 1, 33, "coarse_dirt")
            d.set(x, 2, 33, f)
        for x in (30, 42):
            lamp_post(d, x, 33, "mossy_cobblestone", log("stripped_spruce_log"))
        for x in (33, 39):
            d.chair(x, 2, 32, "north", "spruce", sit=False)
        for x, z in ((27, 36), (44, 36), (44, 14), (27, 13)):
            yew(d, x, z, 2, "spruce_leaves", "spruce_log")
        for x, z in ((9, 45), (13, 44), (25, 44)):                         # lamps along the back lane
            lamp_post(d, x, z, "mossy_cobblestone", log("stripped_spruce_log"), h=1)
    for tx in CC_TX:
        d.reserve(tx, 1, CC_TZ, tx + CC_TW - 1, 40, CC_TZ + CC_TW - 1)
        d.child_hut(tx + CC_WHUT[0], 1 + CC_WHUT[1], CC_TZ + CC_WHUT[2], CATH_WING)
    return d



# ---------------------------------------------------------------------------- Neoterra: crown cathedral
NC_SIZE = (51, 44, 42)
NC_C = (16, 18)                                 # centre of the crown
NC_TX, NC_TZ, NC_TW = (1, 27), 1, 5            # campanile (wings)
NC_WHUT = (1, 1, 3)
NC_H = {1: 9, 2: 13, 3: 19, 4: 23, 5: 31}       # rib height
NC_TOP = {1: 10, 2: 15, 3: 20, 4: 25, 5: 30}    # campanile height (local)
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
    d.set(2, 1, 2, "light_blue_carpet")
    d.set(3, 1, 1, "smooth_quartz_stairs[facing=east,half=bottom,shape=straight,waterlogged=false]")
    d.fill(0, 4, 0, n, 4, n, "smooth_quartz")
    d.set(2, 3, 2, "sea_lantern")
    d.fill(1, 3, 1, 3, 3, 3, "smooth_quartz_slab[type=top,waterlogged=false]")
    d.set(2, 3, 2, "sea_lantern")
    for x, z in ((1, 1), (3, 1), (1, 3), (3, 3)):   # potted azaleas on the lobby roof round the mast
        d.set(x, 5, z, "potted_azalea_bush")
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


NC_RB = {1: 7.0, 2: 9.3, 3: 10.5, 4: 12.0, 5: 13.5}   # crown base radius per level


def nc_radius(t, H, Rb=12.0):
    tw = 0.58 * H
    Rw = Rb * 0.6 + (28 - H) / 9
    Rt = Rb * 0.93
    if t <= tw:
        return Rw + (Rb - Rw) * ((tw - t) / tw) ** 2
    return Rw + (Rt - Rw) * ((t - tw) / (H - tw)) ** 1.6


def nc_parish_centre(d, L):
    """Parish centre: two-storey light-grey concrete block with mangrove cladding, a cut-copper canopy, glass
    front, cafe/hall and office downstairs, meeting rooms upstairs, green roof terrace with planters."""
    x1, z1, x2, z2 = 35, 6, 49, 20
    d.fill(x1, 1, z1, x2, 1, z2, "polished_diorite")
    d.box(x1, 2, z1, x2, 5, z2, "light_gray_concrete")
    two = L >= 5                                                     # a second storey is added at L5
    d.fill(x1, 6, z1, x2, 6, z2, "gray_concrete")
    ry = 11 if two else 6
    if two:
        d.box(x1, 7, z1, x2, 10, z2, "light_gray_concrete")
        d.fill(x1, 11, z1, x2, 11, z2, "smooth_stone")
    for x in range(x1, x2 + 1):                                     # parapet with coping
        for z in range(z1, z2 + 1):
            if x in (x1, x2) or z in (z1, z2):
                d.set(x, ry + 1, z, "white_concrete")
                d.set(x, ry + 2, z, slab("smooth_quartz_slab"))
    # facade: glass street front, mangrove cladding fins, orange accent band
    for x in range(x1 + 1, x2):
        d.window(x, 2, z1, x, 4, z1, "light_gray_stained_glass_pane")
        if two:
            d.window(x, 7, z1, x, 9, z1, "light_gray_stained_glass_pane")
        d.set(x, 5, z1, "orange_terracotta")
    for x in range(x1, x2 + 1, 3):
        d.fill(x, 2, z1, x, 10 if two else 5, z1, "stripped_mangrove_log[axis=y]")
    for z in range(z1 + 2, z2 - 1, 3):
        for x in (x1, x2):
            d.window(x, 3, z, x, 4, z, "glass_pane")
            if two:
                d.window(x, 8, z, x, 9, z, "glass_pane")
    for z in range(z1 + 2, z2 - 1, 3):
        d.window(x1 + 2, 3, z2, x1 + 2, 4, z2)
    d.double_door(41, 2, z1, "x", "south", "mangrove")
    for x in range(x1 - 1, x2 + 2):                                  # cut-copper canopy on steel posts
        d.set(x, 6, z1 - 1, slab("waxed_cut_copper_slab", "top"))
        d.set(x, 6, z1 - 2, slab("waxed_cut_copper_slab", "top"))
    for x in (x1, x2):
        d.fill(x, 2, z1 - 2, x, 5, z1 - 2, "iron_bars")
    d.sign(43, 7, z1 - 1, "north", ["PARISH", "CENTRE"], "mangrove", glow=True, color="orange")
    # ground floor: cafe/hall + office + kitchenette, partition at z = 14
    d.fill(x1 + 1, 2, 14, x2 - 1, 5, 14, "white_concrete")
    d.door(41, 2, 14, "south", "mangrove")
    d.counter(x1 + 1, 8, x1 + 4, 8, 2, body="smooth_quartz")
    d.item(x1 + 1, 2, 10, "smoker", "east")
    d.set(x1 + 1, 2, 11, "cauldron")
    d.set(x1 + 1, 2, 12, "barrel[facing=up,open=false]")
    for xx in (39, 44):
        d.dining(xx, 2, 10, 2, "x", "mangrove", chairs=("n", "s"))
    d.set(x2 - 1, 2, 8, "potted_bamboo")
    d.set(x2 - 1, 2, 12, "potted_bamboo")
    for xx in (37, 40, 43, 46):                                      # pendant lights over the cafe
        d.set(xx, 5, 10, "end_rod[facing=down]")
    d.set(x2 - 2, 2, 17, "lectern[facing=west,has_book=true,powered=false]")
    d.chair(x2 - 1, 2, 17, "east", "mangrove", sit=False)
    d.set(x2 - 1, 2, 19, "chiseled_bookshelf[facing=west,slot_0_occupied=true,slot_1_occupied=true,"
          "slot_2_occupied=false,slot_3_occupied=true,slot_4_occupied=false,slot_5_occupied=true]")
    d.set(x2 - 1, 3, 19, "chiseled_bookshelf[facing=west,slot_0_occupied=false,slot_1_occupied=true,"
          "slot_2_occupied=true,slot_3_occupied=true,slot_4_occupied=false,slot_5_occupied=true]")
    d.set(x2 - 3, 2, 19, "cartography_table")
    d.rug(42, 16, 45, 18, 2, ("orange_carpet", "light_gray_carpet"))
    if not two:
        for x in (37, 41, 45):                                       # planters on the flat roof
            d.set(x, 7, 8, "moss_block")
            d.set(x, 8, 8, "azalea")
        return
    # stair to the upper floor along the west wall (rising south)
    for i in range(4):
        z = 15 + i
        d.set(x1 + 1, 2 + i, z, stair("smooth_quartz_stairs", "south"))
        if i:
            d.fill(x1 + 1, 2, z, x1 + 1, 1 + i, z, "white_concrete")
    d.clear(x1 + 1, 6, 15, x1 + 1, 6, 19)
    d.set(x1 + 1, 5, 19, "white_concrete")
    d.clear(x1 + 1, 6, 16, x1 + 1, 6, 19)
    d.set(x1 + 2, 7, 15, "glass_pane")
    # upper floor: meeting room with a long table, classroom with desks
    d.dining(38, 7, 9, 8, "x", "mangrove", chairs=("n", "s"))
    for xx in (39, 42, 45):                                          # two rows of desks facing the teacher
        for zz in (15, 17):
            d.chair(xx, 7, zz, "north", "birch", sit=False)
            d.set(xx, 7, zz + 1, slab("birch_slab", "top"))
    d.set(43, 7, 13, "lectern[facing=south,has_book=true,powered=false]")
    d.set(47, 7, 19, "chiseled_bookshelf[facing=west,slot_0_occupied=true,slot_1_occupied=true,"
          "slot_2_occupied=true,slot_3_occupied=false,slot_4_occupied=true,slot_5_occupied=false]")
    d.set(47, 7, 15, "potted_bamboo")
    for xx, zz in ((37, 9), (41, 9), (45, 9), (39, 16), (45, 16)):
        d.set(xx, 10, zz, "sea_lantern")
    # roof terrace: green roof, planters, solar panels
    for x, z in ((37, 8), (40, 8), (43, 8), (46, 8), (37, 11), (46, 11), (40, 13), (43, 13)):
        d.set(x, 11, z, "moss_block")                                 # roof-terrace planters
        d.set(x, 12, z, "flowering_azalea" if (x + z) % 2 else "azalea")
    d.chair(41, 12, 11, "north", "birch", sit=False)                  # terrace bench
    d.chair(42, 12, 11, "north", "birch", sit=False)
    for x in (37, 38, 40, 41, 43, 44, 46, 47):                         # solar panels along the south edge
        d.set(x, 12, 18, "daylight_detector[inverted=false,power=0]")


def nc_baptistery(d, L):
    """Baptistery pavilion: polished-blackstone frame round a glass cube, sunken font pool with a light,
    green roof; reached by a canopy walk from the cathedral."""
    x1, z1, x2, z2 = 35, 27, 45, 37
    d.fill(x1, 1, z1, x2, 1, z2, "polished_diorite")
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            edge = x in (x1, x2) or z in (z1, z2)
            corner = x in (x1, x2) and z in (z1, z2)
            for y in range(2, 9):
                if corner or (edge and (x - x1) % 5 == 0 and (z - z1) % 5 == 0):
                    d.set(x, y, z, "polished_blackstone")
                elif edge:
                    d.set(x, y, z, "light_blue_stained_glass" if y < 8 else "polished_blackstone")
    d.fill(x1, 9, z1, x2, 9, z2, "polished_blackstone")
    d.fill(x1 + 1, 10, z1 + 1, x2 - 1, 10, z2 - 1, "moss_block")
    for x in range(x1, x2 + 1):
        for z in (z1, z2):
            d.set(x, 10, z, "polished_blackstone_slab[type=bottom,waterlogged=false]")
    for z in range(z1, z2 + 1):
        for x in (x1, x2):
            d.set(x, 10, z, "polished_blackstone_slab[type=bottom,waterlogged=false]")
    for x, z in ((37, 29), (40, 29), (43, 29), (37, 32), (43, 32), (37, 35), (40, 35), (43, 35)):
        d.set(x, 11, z, "azalea")                                     # shrubs on the green roof
    cx, cz = (x1 + x2) // 2, (z1 + z2) // 2
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            r = math.hypot(dx, dz)
            if r <= 1.5:
                d.set(cx + dx, 1, cz + dz, "water")
                d.set(cx + dx, 0, cz + dz, "sea_lantern")
            elif r <= 2.6:
                d.set(cx + dx, 2, cz + dz, slab("smooth_quartz_slab"))
    d.set(cx, 8, cz, "end_rod[facing=down]")
    d.set(cx, 7, cz, "end_rod[facing=down]")
    for z in (29, 31, 33, 35):                                       # benches facing the font
        d.chair(36, 2, z, "west", "cherry", sit=False)
        d.chair(44, 2, z, "east", "cherry", sit=False)
    d.double_door(cx - 1, 2, z1, "x", "south", "cherry")
    # canopy walk from the cathedral's east side
    for x in range(30, x1):
        d.set(x, 1, cz - 3, "smooth_quartz")
        d.set(x, 1, cz - 2, "smooth_quartz")
    d.fill(28, 6, cz - 4, x1 - 1, 6, cz - 1, slab("smooth_quartz_slab", "top"))
    for x in (30, 33):                                               # canopy posts
        for z in (cz - 4, cz - 1):
            d.fill(x, 2, z, x, 5, z, "white_concrete")


def nc_sanctuary_extras(d, L, cx, cz, Rb):
    """Furniture on the four axes of the round nave (the aisles between the pew quadrants): the baptismal font on
    the west axis, a votive stand with candles on the east axis, the organ console and pipes on the south axis
    behind the altar (L3+), planters where the aisles meet the glass, candles on the altar dais."""
    k = int(Rb - 2)
    wx, ex, sz = cx - k, cx + k, cz + k
    d.set(wx, 2, cz, "smooth_quartz")                                 # font: quartz basin with a light
    d.set(wx, 3, cz, "water_cauldron[level=3]")
    d.set(wx, 2, cz - 1, slab("smooth_quartz_slab"))
    d.set(wx, 2, cz + 1, slab("smooth_quartz_slab"))
    d.set(ex, 2, cz, "smooth_quartz")                                 # votive stand
    d.candle(ex, 3, cz, 4, "white")
    for dz in (-1, 1):
        d.set(ex, 2, cz + dz, slab("smooth_quartz_slab", "top"))
        d.candle(ex, 3, cz + dz, 2 + dz % 2, "white")
    d.set(cx - 2, 3, cz, "candle[candles=3,lit=false,waterlogged=false]")   # candles on the dais
    d.set(cx + 2, 3, cz, "candle[candles=3,lit=false,waterlogged=false]")
    if L >= 3:                                                       # organ behind the altar
        for dx, h in ((-1, 3), (0, 4), (1, 3)):
            d.set(cx + dx, 2, sz, "note_block[instrument=flute,note=0,powered=false]")
            for y in range(3, 3 + h):
                d.set(cx + dx, y, sz, "iron_bars")
            d.set(cx + dx, 3 + h, sz, slab("smooth_quartz_slab"))
        d.chair(cx, 2, sz - 1, "south", "birch", sit=False)
    else:
        d.set(cx, 2, sz, "potted_bamboo")
    for x, z in ((wx, cz - 2), (ex, cz + 2), (cx - 2, sz), (cx + 2, sz)):
        if d.air(x, 2, z):
            d.set(x, 2, z, "potted_bamboo")


def nc_sacristy(d, L):
    """Sacristy and choir room (x4..16, z35..41, L3+): white block with a glass north front. West room = vestry
    (vestment chests and wardrobe, robes hanging, wash basin, candle store, bench); east room = choir room /
    office (music stands, practice organ, desk with the parish books, chairs for the choir). Doors in the end
    walls; a moss roof with planters from L4, a roof garden bench at L5."""
    x1, z1, x2, z2 = 4, 35, 16, 41
    d.fill(x1, 1, z1, x2, 1, z2, "polished_diorite")
    d.box(x1, 2, z1, x2, 5, z2, "white_concrete")
    for x in range(x1 + 1, x2):
        if x != 10:
            d.window(x, 3, z1, x, 4, z1, "light_blue_stained_glass_pane")
    d.fill(x1, 5, z1, x2, 5, z1, "cyan_terracotta")
    d.fill(x1, 6, z1, x2, 6, z2, "smooth_stone")
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if x in (x1, x2) or z in (z1, z2):
                d.set(x, 7, z, slab("smooth_quartz_slab"))
    d.fill(10, 2, z1 + 1, 10, 5, z2 - 1, "white_concrete")         # partition with a door
    d.door(10, 2, 38, "east", "birch")
    d.door(x1, 2, 38, "west", "birch")
    d.door(x2, 2, 38, "east", "birch")
    # vestry
    d.set(5, 2, 40, "chest[facing=north,type=single,waterlogged=false]")
    d.set(6, 2, 40, "chest[facing=north,type=single,waterlogged=false]")
    d.set(7, 2, 40, "barrel[facing=north,open=false]")
    d.set(7, 3, 40, "decorated_pot[cracked=false,facing=north,waterlogged=false]")
    d.set(8, 3, 40, "white_wall_banner[facing=north]")
    d.set(9, 3, 40, "purple_wall_banner[facing=north]")
    d.set(9, 2, 40, "water_cauldron[level=3]")
    d.set(5, 2, 36, "barrel[facing=up,open=false]")
    d.candle(5, 3, 36, 4, "white")
    d.chair(7, 2, 36, "north", "birch", sit=False)
    d.set(8, 2, 36, "potted_bamboo")
    d.set(7, 5, 38, "end_rod[facing=down]")
    # choir room / office
    d.set(12, 2, 40, slab("birch_slab", "top"))
    d.set(13, 2, 40, slab("birch_slab", "top"))
    d.chair(12, 2, 39, "north", "birch", sit=False)
    d.set(13, 3, 40, "candle[candles=2,lit=false,waterlogged=false]")
    d.set(11, 2, 40, "chiseled_bookshelf[facing=north,slot_0_occupied=true,slot_1_occupied=true,"
          "slot_2_occupied=false,slot_3_occupied=true,slot_4_occupied=true,slot_5_occupied=false]")
    d.set(15, 2, 40, "chiseled_bookshelf[facing=north,slot_0_occupied=false,slot_1_occupied=true,"
          "slot_2_occupied=true,slot_3_occupied=true,slot_4_occupied=false,slot_5_occupied=true]")
    d.set(15, 2, 36, "note_block[instrument=harp,note=0,powered=false]")      # practice organ
    d.set(14, 2, 36, "note_block[instrument=harp,note=5,powered=false]")
    d.set(13, 2, 36, "lectern[facing=south,has_book=true,powered=false]")
    d.set(11, 2, 36, "lectern[facing=south,has_book=true,powered=false]")
    d.chair(11, 2, 37, "south", "birch", sit=False)
    d.chair(13, 2, 37, "south", "birch", sit=False)
    d.set(13, 5, 38, "end_rod[facing=down]")
    if L >= 4:
        for x in (6, 9, 12, 15):
            d.set(x, 7, 38, "moss_block")
            d.set(x, 8, 38, "azalea" if x % 2 else "flowering_azalea")


def nc_garden(d):
    """Memorial garden south of the crown (x18..31, z36..41, L5): columbarium wall with candle niches along the
    back, a quartz walk, benches facing the wall, azalea beds, one cherry tree, light bollards."""
    for x in range(18, 32):
        d.set(x, 1, 38, "smooth_quartz")
        d.set(x, 1, 39, "smooth_quartz")
    for x in range(19, 31):
        d.set(x, 2, 41, "chiseled_quartz_block" if x % 3 == 0 else "smooth_quartz")
        d.set(x, 3, 41, "smooth_quartz" if x % 3 else "chiseled_quartz_block")
        d.set(x, 4, 41, slab("smooth_quartz_slab"))
        if x % 3 == 0:
            d.candle(x, 2, 40, 2, "white")
    for x in (20, 21, 28, 29):
        d.chair(x, 2, 39, "north", "birch", sit=False)
    for x, z in ((18, 36), (18, 37), (31, 36), (31, 37), (24, 36), (25, 36)):
        d.set(x, 1, z, "moss_block")
        d.set(x, 2, z, "flowering_azalea" if (x + z) % 2 else "azalea")
    for x in (18, 31):
        d.set(x, 2, 40, "smooth_quartz")
        d.set(x, 3, 40, "end_rod[facing=up]")


def nc_cathedral(rel, L):
    d = Design("Neoterra", rel, NC_SIZE, gy=1, paving="smooth_stone")
    cx, cz = NC_C
    H = NC_H[L]
    Rb = NC_RB[L]
    y0 = 2
    glass_top = H - 4
    cols = ("light_blue", "light_blue", "blue", "cyan", "light_blue", "white", "blue")
    W, Dp = d.sx, d.sz
    # plaza paving: concentric rings of white and light-grey with a quartz compass
    for x in range(W):
        for z in range(Dp):
            r = math.hypot(x - cx, z - cz)
            if r > Rb + 1:
                d.set(x, 1, z, "white_concrete" if int(r) % 3 else "light_gray_concrete")
    # reflecting pool ring (L3+)
    if L >= 3:
        for x in range(W):
            for z in range(Dp):
                r = math.hypot(x - cx, z - cz)
                if Rb + 1.2 <= r <= Rb + 2.8 and not (14 <= x <= 18 and z < cz):
                    d.set(x, 1, z, "water")
                    d.set(x, 0, z, "light_blue_concrete")
                elif (Rb + 0.5 <= r < Rb + 1.2 or Rb + 2.8 < r <= Rb + 3.5) and not (14 <= x <= 18 and z < cz):
                    d.set(x, 1, z, "smooth_quartz")
    # shell: ribs and stained glass
    ang = [2 * math.pi * k / NC_RIBS for k in range(NC_RIBS)]
    for t in range(0, H + 1):
        r1 = nc_radius(t, H, Rb)
        r2 = nc_radius(min(H, t + 1), H, Rb)
        lo, hi = min(r1, r2) - 0.5, max(r1, r2) + 0.5
        for x in range(int(cx - hi) - 1, int(cx + hi) + 2):
            for z in range(int(cz - hi) - 1, int(cz + hi) + 2):
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
    # floor
    for x in range(W):
        for z in range(Dp):
            dd = math.hypot(x - cx, z - cz)
            if dd < Rb - 0.4:
                d.set(x, 1, z, "polished_diorite" if (int(dd) % 3) else "white_concrete")
    # glass roof inside the crown
    rg = nc_radius(glass_top, H, Rb)
    for x in range(int(cx - rg) - 1, int(cx + rg) + 2):
        for z in range(int(cz - rg) - 1, int(cz + rg) + 2):
            dd = math.hypot(x - cx, z - cz)
            if dd <= rg - 0.4 and d.air(x, y0 + glass_top, z):
                d.set(x, y0 + glass_top, z, "light_blue_stained_glass" if dd > 2 else "white_stained_glass")
    # entrance vestibule (north), reaching into the shell
    zf = int(cz - Rb)                                            # shell foot on the axis
    vz1, vz2 = max(1, zf - 4), zf + 2
    d.fill(13, 1, vz1 - 1, 19, 1, vz2, "polished_diorite")
    d.box(13, 2, vz1, 19, 5, vz2, "smooth_quartz")
    d.clear(14, 2, vz1, 18, 5, vz2 + 1)
    d.fill(14, 5, vz1, 18, 5, vz2, "smooth_quartz")
    d.clear(14, 2, vz1 + 1, 18, 4, vz2 + 1)
    for x in (14, 15, 17, 18):
        for y in (2, 3, 4):
            d.set(x, y, vz1, "light_gray_stained_glass_pane")
    d.door(15, 2, vz1, "south", "birch")
    d.door(17, 2, vz1, "south", "birch", "right")
    d.set(16, 2, vz1, "smooth_quartz")
    d.set(16, 3, vz1, "smooth_quartz")
    d.set(16, 4, vz1, "light_gray_stained_glass_pane")
    d.fill(12, 6, vz1 - 1, 20, 6, vz2, slab("smooth_quartz_slab"))
    d.fill(13, 5, vz1 - 1, 19, 5, vz1 - 1, "smooth_quartz")
    for x in (13, 19):
        d.set(x, 2, vz1 - 1, "smooth_quartz")
    d.fill(14, 5, vz1 - 1, 18, 5, vz1 - 1, "cyan_terracotta")
    for x in (14, 18):
        d.set(x, 4, vz1 + 2, "sea_lantern")
        d.set(x, 2, vz1 + 1, "potted_bamboo")
    # sanctuary: round altar platform, concentric pews
    for x in range(cx - 2, cx + 3):
        for z in range(cz - 2, cz + 3):
            if math.hypot(x - cx, z - cz) <= 2.3:
                d.set(x, 2, z, "smooth_quartz_slab[type=bottom,waterlogged=false]")
    d.set(cx, 2, cz, "smooth_quartz")
    d.candle(cx, 3, cz, 4, "white")
    d.set(cx, 2, cz + 1, "smooth_quartz")
    d.set(cx, 3, cz + 1, "end_rod[facing=up]")
    d.set(cx, 2, cz - 2, "lectern[facing=north,has_book=true,powered=false]")
    # seating in the round: concentric arcs of chairs facing the altar in four quadrants, aisles on the axes;
    # the rows per level are fixed, the hut corner by the entrance stays clear
    rows = {1: (4.5,), 2: (4.5, 6.5), 3: (4.5, 6.5), 4: (4.5, 6.5, 8.5), 5: (4.5, 6.5, 8.5, 10.5)}[L]
    used = {(14, 13), (14, 14), (15, 13)}
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
            d.chair(x, 2, z, back, "birch")
    d.rug(cx, zf + 1, cx, cz - 4, 2, ("light_blue_carpet",), "plain")
    d.hut(14, 2, 13)
    nc_sanctuary_extras(d, L, cx, cz, Rb)
    # hanging lights: rings of lights on chains from the glass roof
    for a in ((0, 90, 180, 270) if L < 4 else (0, 45, 90, 135, 180, 225, 270, 315)):   # pendant ring
        rr = Rb * 0.45
        x, z = cx + round(rr * math.cos(math.radians(a + 22))), cz + round(rr * math.sin(math.radians(a + 22)))
        for y in range(y0 + glass_top - 3, y0 + glass_top):
            d.set(x, y, z, CHAIN)
        d.set(x, y0 + glass_top - 4, z, "sea_lantern" if L >= 3 else lantern(True))
    # central cross above the roof (L3+)
    if L >= 3:
        top = y0 + H + (4 if L == 5 else 1)
        for y in range(y0 + glass_top + 1, top + 1):
            d.set(cx, y, cz, "white_concrete")
        d.set(cx - 1, top - 1, cz, "white_concrete")
        d.set(cx + 1, top - 1, cz, "white_concrete")
        d.set(cx, top + 1, cz, "end_rod[facing=up]")
    # evangelists on the forecourt (L5): four bronze figures
    if L >= 5:
        for x, z in ((10, 7), (22, 7), (11, 3), (21, 3)):
            d.set(x, 2, z, "polished_andesite")
            d.set(x, 3, z, "oxidized_copper")
            d.set(x, 4, z, "oxidized_cut_copper")
            d.set(x, 5, z, "oxidized_copper")
    # planters and lamp posts along the approach
    if L >= 2:
        for x in (12, 20):
            for z in (0, 1):
                d.set(x, 1, z, "moss_block")
                d.set(x, 2, z, "potted_bamboo" if z else "flowering_azalea")
        for x in (9, 23):
            d.set(x, 2, 1, "white_concrete")
            d.set(x, 3, 1, "iron_bars")
            d.set(x, 4, 1, "sea_lantern")
    if L >= 2:                                                       # forecourt benches between planters
        for x0 in (6, 22):
            d.set(x0, 1, 1, "moss_block")
            d.set(x0, 2, 1, "flowering_azalea")
            d.set(x0 + 4, 1, 1, "moss_block")
            d.set(x0 + 4, 2, 1, "azalea")
        for x in (7, 8, 24, 25):
            d.chair(x, 2, 1, "north", "birch", sit=False)
    if L >= 3:
        nc_sacristy(d, L)
    if L >= 4:
        nc_parish_centre(d, L)
    if L >= 5:
        nc_baptistery(d, L)
        nc_garden(d)
        for x, z in ((33, 24), (48, 24)):
            cherry_tree(d, x, z)
        for z in (26, 30, 34, 38):                                   # benches along the garden walk
            d.chair(33, 2, z, "west", "birch", sit=False)
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


COLO_H = {"Hearthwood": {1: 10, 2: 14, 3: 20, 4: 26, 5: 35},
          "Cascadia": {1: 10, 2: 14, 3: 20, 4: 26, 5: 35},
          "Neoterra": {1: 9, 2: 13, 3: 18, 4: 25, 5: 34}}


def pylon_base(d, n, wall, floor, door_wood, hut):
    d.fill(0, 0, 0, n, 0, n, floor)
    d.box(0, 1, 0, n, 4, n, wall)
    d.door(n // 2, 1, 0, "south", door_wood)
    d.hut(*hut)


def ring_stairs(d, x1, z1, x2, z2, y, name, half="bottom", inward=True):
    """Stairs all round a rectangle; inward=True puts the tall back toward the inside (a step / plinth course),
    outer corners shaped."""
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if not (x in (x1, x2) or z in (z1, z2)):
                continue
            if x in (x1, x2) and z in (z1, z2):
                f = "south" if z == z1 else "north"
                sh = "outer_left" if (x == x1) == (z == z1) else "outer_right"
            else:
                f = "south" if z == z1 else "north" if z == z2 else "east" if x == x1 else "west"
                sh = "straight"
            if not inward:
                f = OPP[f]
            if d.bp.inside(x, y, z):
                d.set(x, y, z, stair(name, f, half, sh))


def lamp_post(d, x, z, base, post, top="lantern[hanging=false,waterlogged=false]", h=2):
    d.set(x, 2, z, base)
    for y in range(3, 3 + h):
        d.set(x, y, z, post)
    d.set(x, 3 + h, z, top)


def hall_box(x1, z1, x2, z2):
    """Interior corners of a plinth hall (inside the walls)."""
    return x1 + 1, z1 + 1, x2 - 1, z2 - 1


def hk_hall4(d, x1, z1, x2, z2, ph):
    """L4 Hall of the Old King (interior 14..30 x 18..32, one tall storey): the crowned model on a pedestal in the
    middle of a bordered rug with benches before it, warden's desk by the door, a gallery of relic cases with
    lecterns down the west wall, map tables and an armoury rack on the east wall, bookcases and banners at the
    back, a chandelier over the model."""
    ix1, iz1, ix2, iz2 = hall_box(x1, z1, x2, z2)
    cx, cz = (x1 + x2) // 2, (z1 + z2) // 2                           # 22, 25
    TS = slab("oak_slab", "top")
    d.fill(ix1, 1, iz1, ix2, 1, iz2, "polished_granite")
    d.rug(cx, iz1, cx, iz1 + 4, 2, ("red_carpet",), "plain")
    d.set(cx, 2, cz, HS["carve"])
    d.set(cx, 3, cz, "gold_block")
    d.set(cx - 1, 2, cz, "lectern[facing=north,has_book=true,powered=false]")
    d.set(cx + 1, 2, cz, "lectern[facing=north,has_book=true,powered=false]")
    d.rug(cx - 2, cz - 1, cx + 2, cz + 1, 2, ("red_carpet", "yellow_carpet"))
    chandelier(d, cx, cz, ph - 1, ph - 2)
    for x in (cx - 1, cx, cx + 1):
        d.chair(x, 2, cz + 3, "south", "oak", sit=False)
    d.set(25, 2, iz1, TS)
    d.set(26, 2, iz1, TS)
    d.candle(25, 3, iz1, 2)
    d.chair(26, 2, iz1 + 1, "south", "oak", sit=False)
    for k, z in enumerate((20, 23, 26, 29)):                         # relic gallery, west wall
        d.set(ix1, 2, z, HS["carve"])
        d.set(ix1, 3, z, "white_stained_glass" if k % 2 else "decorated_pot[cracked=false,facing=east,waterlogged=false]")
        d.set(ix1 + 1, 2, z + 1, "lectern[facing=west,has_book=true,powered=false]")
        d.set(ix1, 4, z + 1, ("red_wall_banner", "yellow_wall_banner")[k % 2] + "[facing=east]")
    for z in (20, 23):                                               # map tables, east
        d.set(28, 2, z, "cartography_table")
        d.chair(27, 2, z, "west", "oak", sit=False)
    d.set(ix2, 2, 21, "barrel[facing=west,open=false]")
    for z in (26, 27, 28, 29):                                       # armoury rack
        d.set(ix2, 2, z, HS["carve"] if z % 2 else "chest[facing=west,type=single,waterlogged=false]")
        d.set(ix2, 3, z, "iron_bars")
    for x in (ix1, ix1 + 1, ix2 - 1, ix2):                           # bookcases at the back
        d.set(x, 2, iz2, "bookshelf")
        d.set(x, 3, iz2, "bookshelf")
    for x in (cx - 2, cx + 2):
        d.set(x, 3, iz2, "red_wall_banner[facing=north]")
        d.set(x, 2, iz2, "potted_flowering_azalea_bush")
    d.set(cx, 2, iz2, HS["carve"])
    d.set(cx, 3, iz2, "decorated_pot[cracked=false,facing=north,waterlogged=false]")
    d.set(ix2, 2, iz1, "potted_red_tulip")
    for x, z in ((17, 21), (27, 21), (17, 29), (27, 29)):
        d.set(x, ph - 1, z, lantern(True))


def hk_hall5(d, x1, z1, x2, z2, ph):
    """L5 plinth of the Old King (interior 13..31 x 17..33), two storeys. Ground floor = Hall of the Old King: red
    runner to the crowned model, relic cases and a warden's desk by the door, the armoury gallery (weapon racks,
    shields) on the west, the map room on the east, a throne replica on a dais at the back. Upper floor (walk y6)
    = the royal library: book walls, two reading tables, the great map table, scribe's desk, the state bed."""
    ix1, iz1, ix2, iz2 = hall_box(x1, z1, x2, z2)                     # 13, 17, 31, 33
    cx = (x1 + x2) // 2                                              # 22
    TS = slab("oak_slab", "top")
    d.fill(ix1, 1, iz1, ix2, 1, iz2, "polished_granite")
    # ---- structure: upper floor, windows for it, stair on the west wall
    d.fill(ix1, 5, iz1, ix2, 5, iz2, "spruce_planks")
    for z in range(z1 + 2, z2 - 1, 3):
        for x in (x1, x2):
            d.set(x, 6, z, "glass_pane")
    for i, z in enumerate((27, 28, 29, 30)):
        d.set(ix1, 2 + i, z, stair("oak_stairs", "south"))
        if i:
            d.fill(ix1, 2, z, ix1, 1 + i, z, "oak_planks")
    d.clear(ix1, 5, 27, ix1, 5, 29)
    for z in (27, 28, 29):
        d.set(ix1 + 1, 6, z, fence("dark_oak_fence"))
    # ================================================================ ground floor
    d.rug(cx, iz1, cx, iz1 + 5, 2, ("red_carpet",), "plain")
    d.set(cx, 2, 26, HS["carve"])                                    # crowned model on its pedestal
    d.set(cx, 3, 26, "gold_block")
    d.set(cx - 1, 2, 26, "lectern[facing=north,has_book=true,powered=false]")
    d.set(cx + 1, 2, 26, "lectern[facing=north,has_book=true,powered=false]")
    d.rug(cx - 2, 24, cx + 2, 24, 2, ("yellow_carpet",), "plain")
    d.set(cx, 4, 26, lantern(True))
    # warden's desk and relic cases by the door
    d.set(25, 2, iz1, TS)
    d.set(26, 2, iz1, TS)
    d.candle(26, 3, iz1, 2)
    d.chair(25, 2, iz1 + 1, "south", "oak", sit=False)
    d.set(19, 2, iz1, HS["carve"])
    d.set(19, 3, iz1, "white_stained_glass")
    d.set(ix1, 2, iz1, "potted_red_tulip")
    d.set(ix2, 2, iz1, "potted_flowering_azalea_bush")
    # armoury gallery, west: weapon racks (bars), shield banners, a suit of armour on a stand, chests
    for z in (19, 21, 23):
        d.set(ix1, 2, z, HS["carve"])
        d.set(ix1, 3, z, "iron_bars")
        d.set(ix1, 3, z + 1, ("red_wall_banner", "yellow_wall_banner", "red_wall_banner")[(z - 19) // 2] + "[facing=east]")
    d.set(ix1, 2, 20, "chest[facing=east,type=single,waterlogged=false]")
    d.set(ix1, 2, 22, "chest[facing=east,type=single,waterlogged=false]")
    d.set(16, 2, 20, "smithing_table")
    d.set(16, 3, 20, "iron_bars")
    d.set(16, 2, 23, "anvil[facing=north]")
    d.set(17, 2, 21, "lectern[facing=west,has_book=true,powered=false]")
    # map room, east
    for z in (20, 23):
        d.set(28, 2, z, "cartography_table")
        d.chair(29, 2, z, "east", "oak", sit=False)
        d.chair(27, 2, z, "west", "oak", sit=False)
    d.bookshelf(ix2, 2, 19, 2)
    d.bookshelf(ix2, 2, 22, 2)
    d.set(ix2, 2, 20, "chiseled_bookshelf[facing=west,slot_0_occupied=true,slot_1_occupied=true,"
          "slot_2_occupied=false,slot_3_occupied=true,slot_4_occupied=false,slot_5_occupied=true]")
    d.set(ix2, 2, 21, "barrel[facing=west,open=false]")
    d.set(ix2, 3, 21, "potted_red_tulip")
    d.rug(27, 21, 29, 22, 2, ("blue_carpet",), "plain")
    # relic cases down the middle aisles
    for x, z, top in ((18, 26, "decorated_pot[cracked=false,facing=north,waterlogged=false]"),
                      (26, 26, "white_stained_glass"), (18, 29, "white_stained_glass"),
                      (26, 29, "decorated_pot[cracked=false,facing=north,waterlogged=false]")):
        d.set(x, 2, z, HS["carve"])
        d.set(x, 3, z, top)
    # throne replica on a dais, back wall, with banners and bookcases
    d.fill(cx - 2, 2, iz2 - 1, cx + 2, 2, iz2, slab(HS["sl"], "top"))
    d.chair(cx, 3, iz2, "south", "dark_oak", sit=False)
    d.set(cx - 1, 3, iz2, stair(HS["sst"], "east"))
    d.set(cx + 1, 3, iz2, stair(HS["sst"], "west"))
    for x in (cx - 3, cx + 3):
        d.set(x, 3, iz2, "red_wall_banner[facing=north]")
        d.set(x, 2, iz2, "potted_flowering_azalea_bush")
    d.set(cx, 4, iz2, "yellow_wall_banner[facing=north]")
    d.chair(cx - 1, 2, 30, "north", "oak", sit=False)               # benches before the throne
    d.chair(cx + 1, 2, 30, "north", "oak", sit=False)
    d.bookshelf(ix2, 2, 31, 2)
    d.bookshelf(ix2, 2, 32, 2)
    d.set(ix2, 2, iz2, "barrel[facing=up,open=false]")
    d.set(ix1, 2, 32, "chest[facing=east,type=single,waterlogged=false]")
    d.set(ix1, 2, iz2, "potted_red_tulip")
    for x, z in ((16, 19), (28, 19), (16, 31), (28, 31), (cx, 21)):
        d.set(x, 4, z, lantern(True))
    for z in (25, 28):
        d.set(ix2, 4, z, "wall_torch[facing=west]")
    # ================================================================ upper floor: the royal library
    y = 6
    for x in list(range(14, 20)) + list(range(25, 31)):           # book walls along the street side
        d.set(x, y, iz1, "bookshelf")
        d.set(x, y + 1, iz1, "bookshelf" if x % 3 else "chiseled_bookshelf[facing=south,slot_0_occupied=true,"
              "slot_1_occupied=true,slot_2_occupied=true,slot_3_occupied=false,slot_4_occupied=true,"
              "slot_5_occupied=false]")
    for z in range(19, 26):
        d.set(ix2, y, z, "bookshelf")
        d.set(ix2, y + 1, z, "bookshelf")
    for x0 in (15, 26):                                              # two reading tables
        for x in range(x0, x0 + 3):
            d.set(x, y, 21, TS)
            d.chair(x, y, 20, "north", "oak", sit=False)
            d.chair(x, y, 22, "south", "oak", sit=False)
        d.candle(x0 + 1, y + 1, 21, 3)
    d.set(cx, y, 25, "cartography_table")                            # the great map table
    d.set(cx - 1, y, 25, TS)
    d.set(cx + 1, y, 25, TS)
    d.chair(cx, y, 24, "north", "oak", sit=False)
    d.chair(cx - 2, y, 25, "west", "oak", sit=False)
    d.chair(cx + 2, y, 25, "east", "oak", sit=False)
    d.set(cx, y + 1, 25, lantern(False))
    d.rug(cx - 1, 27, cx + 1, 29, y, ("red_carpet", "yellow_carpet"))
    for x in (16, 17):                                               # scribe's desk, back-west
        d.set(x, y, iz2, TS)
    d.chair(16, y, iz2 - 1, "north", "oak", sit=False)
    d.set(17, y + 1, iz2, "candle[candles=2,lit=false,waterlogged=false]")
    d.set(18, y, iz2, "lectern[facing=north,has_book=true,powered=false]")
    d.set(15, y, iz2, "chest[facing=north,type=single,waterlogged=false]")
    d.set(ix1, y, iz2, "barrel[facing=up,open=false]")
    d.set(29, y, iz2, "red_bed[facing=south,occupied=false,part=head]")   # the state bed (display)
    d.set(29, y, iz2 - 1, "red_bed[facing=south,occupied=false,part=foot]")
    for x in (28, 30):
        d.set(x, y, iz2, TS)
        d.candle(x, y + 1, iz2, 1)
    d.rug(28, 29, 30, 30, y, ("yellow_carpet",), "plain")
    d.set(ix2, y, 28, "chest[facing=west,type=single,waterlogged=false]")
    d.set(ix2, y, 27, "potted_flowering_azalea_bush")
    d.set(24, y, iz2, "potted_red_tulip")
    for x in (21, 22, 23):
        d.set(x, y + 1, iz2, ("red_wall_banner", "yellow_wall_banner", "red_wall_banner")[x - 21] + "[facing=north]")
    for z in (19, 23, 31):
        d.set(ix1, y + 1, z, "wall_torch[facing=east]")
    for z in (27, 31):
        d.set(ix2, y + 1, z, "wall_torch[facing=west]")


def hk_hall(d, x1, z1, x2, z2, ph, L):
    """Hall of the Old King (hand-placed): red runner from the door to a crowned model on a pedestal at the back,
    lecterns with the chronicle either side, benches facing the model, bookcases and relic cases in the corners,
    banners and torches on the walls; grows a guest-book desk, relic cases and a chandelier."""
    if L >= 5:
        return hk_hall5(d, x1, z1, x2, z2, ph)
    if L == 4:
        return hk_hall4(d, x1, z1, x2, z2, ph)
    ix1, iz1, ix2, iz2 = hall_box(x1, z1, x2, z2)
    cx, cz = (x1 + x2) // 2, (z1 + z2) // 2
    d.fill(ix1, 1, iz1, ix2, 1, iz2, "polished_granite")
    d.rug(cx, iz1, cx, (cz - 3 if L >= 4 else iz2 - 1), 2, ("red_carpet",), "plain")
    d.set(cx, 2, iz2, "chiseled_sandstone")                              # pedestal with the crowned model
    d.set(cx, 3, iz2, "gold_block" if L >= 3 else "yellow_terracotta")
    d.set(cx - 1, 2, iz2, "lectern[facing=north,has_book=true,powered=false]")
    d.set(cx + 1, 2, iz2, "lectern[facing=north,has_book=true,powered=false]")
    d.set(ix1, 3, cz - 1, "wall_torch[facing=east]")
    d.set(ix2, 3, cz - 1, "wall_torch[facing=west]")
    d.set(ix2, 2, iz1, "potted_red_tulip")
    if L >= 2:
        d.chair(cx - 1, 2, cz, "north", "oak", sit=False)                 # benches looking at the model
        d.chair(cx + 1, 2, cz, "north", "oak", sit=False)
        d.set(cx - 2, 3, iz2, "red_wall_banner[facing=north]")
        d.set(cx + 2, 3, iz2, "red_wall_banner[facing=north]")
    if L >= 3:
        for x, sh in ((ix1, "bookshelf"), (ix2, "chiseled_bookshelf[facing=west,slot_0_occupied=true,"
                                                   "slot_1_occupied=true,slot_2_occupied=false,slot_3_occupied=true,"
                                                   "slot_4_occupied=false,slot_5_occupied=true]")):
            d.set(x, 2, iz2, sh)
            d.set(x, 3, iz2, sh)
        d.set(ix1, 2, cz + 1, "chiseled_sandstone")                       # relic cases
        d.set(ix1, 3, cz + 1, "white_stained_glass")
        d.set(ix2, 2, cz + 1, "chiseled_sandstone")
        d.set(ix2, 3, cz + 1, "decorated_pot[cracked=false,facing=west,waterlogged=false]")
        d.set(cx, ph - 1, cz - 2, lantern(True))
        d.set(cx, ph - 1, cz + 2, lantern(True))
    if L >= 4:
        d.set(cx + 3, 2, iz1, slab("oak_slab", "top"))
        d.candle(cx + 3, 3, iz1, 2)
        d.chair(cx + 4, 2, iz1, "east", "oak", sit=False)                 # warden's desk by the door
        d.set(ix1, 2, iz1 + 2, "chiseled_sandstone")
        d.set(ix1, 3, iz1 + 2, "decorated_pot[cracked=false,facing=east,waterlogged=false]")
        d.set(ix2, 2, iz1 + 2, "chiseled_sandstone")
        d.set(ix2, 3, iz1 + 2, "white_stained_glass")
        d.rug(cx - 2, cz - 1, cx + 2, cz + 1, 2, ("red_carpet", "yellow_carpet"))
    if L <= 3:                                                        # early hall: relic case, desk, chest
        d.set(ix1, 2, iz1 + 1, HS["carve"])
        d.set(ix1, 3, iz1 + 1, "white_stained_glass")
        d.set(ix2, 2, iz1 + 2, slab("oak_slab", "top"))
        d.candle(ix2, 3, iz1 + 2, 2)
        d.chair(ix2 - 1, 2, iz1 + 2, "west", "oak", sit=False)
        d.set(ix2, 2, iz2 - 1, "chest[facing=west,type=single,waterlogged=false]")
        d.set(ix1, 2, iz2 - 1, "potted_red_tulip")
        if L == 1:
            d.set(cx - 2, 3, iz2, "red_wall_banner[facing=north]")
            d.set(cx + 2, 3, iz2, "red_wall_banner[facing=north]")
        if L >= 3:
            d.rug(ix1 + 1, iz2 - 3, ix1 + 2, iz2 - 2, 2, ("yellow_carpet",), "plain")
            d.set(ix1 + 2, 2, iz1 + 1, "lectern[facing=north,has_book=true,powered=false]")
            d.set(ix2 - 2, 2, iz2 - 2, "decorated_pot[cracked=false,facing=north,waterlogged=false]")
    if L >= 5:
        d.set(ix1, 4, cz - 3, "yellow_wall_banner[facing=east]")
        d.set(ix2, 4, cz - 3, "yellow_wall_banner[facing=west]")
        d.set(ix1, 4, cz + 3, "red_wall_banner[facing=east]")
        d.set(ix2, 4, cz + 3, "red_wall_banner[facing=west]")
        chandelier(d, cx, cz, ph - 1, ph - 2)
        for x in (cx - 4, cx + 4):                                       # map tables of the realm
            d.set(x, 2, cz, "cartography_table")
            d.chair(x, 2, cz + 1, "south", "oak", sit=False)
            d.set(x, 2, cz - 1, "lectern[facing=south,has_book=true,powered=false]")
        for x in (cx - 2, cx - 1, cx + 1, cx + 2):                       # front row of benches
            d.chair(x, 2, cz - 3, "north", "oak", sit=False)
        for x in (ix1, ix2):                                              # relic cases by the entrance
            d.set(x, 2, cz - 3, "chiseled_sandstone")
            d.set(x, 3, cz - 3, "white_stained_glass")
            d.set(x, 2, iz2 - 2, "potted_flowering_azalea_bush")
        d.set(cx, 2, cz + 3, slab("smooth_sandstone_slab", "top"))      # throne replica on a dais
        d.chair(cx, 3, cz + 3, "south", "dark_oak", sit=False)
        d.set(cx - 1, 2, cz + 3, stair(HS["sst"], "east"))
        d.set(cx + 1, 2, cz + 3, stair(HS["sst"], "west"))
        for x in (cx - 4, cx + 4):                                       # weapon racks: shield and spears
            d.set(x, 2, cz + 3, "chiseled_sandstone")
            d.set(x, 3, cz + 3, "iron_bars")
        d.rug(cx - 5, cz + 2, cx - 3, cz + 4, 2, ("yellow_carpet",), "plain")
        d.rug(cx + 3, cz + 2, cx + 5, cz + 4, 2, ("yellow_carpet",), "plain")


def cg_hall4(d, x1, z1, x2, z2, ph):
    """L4 camp hall (interior 14..28 x 18..32, one storey): stone hearth with armchairs and a bearskin on the
    west wall, a long mess table across the back half, the cook's run on the east wall, the tool wall along the
    street wall, the watchman's bunk in the south-west corner, the giant's model and a map table."""
    ix1, iz1, ix2, iz2 = hall_box(x1, z1, x2, z2)
    cx, cz = (x1 + x2) // 2, (z1 + z2) // 2                           # 21, 25
    TS = slab("spruce_slab", "top")
    d.fill(ix1, 1, iz1, ix2, 1, iz2, "spruce_planks")
    d.hearth(ix1, 2, cz, "east", ph, "cobblestone", "campfire")
    d.chair(ix1 + 2, 2, cz - 1, "east", "spruce", sit=False)
    d.chair(ix1 + 2, 2, cz + 1, "east", "spruce", sit=False)
    d.rug(ix1 + 1, cz - 1, ix1 + 1, cz + 1, 2, ("brown_carpet",), "plain")
    d.dining(18, 2, 29, 5, "x", "spruce", chairs=("n", "s"), sit=False)
    d.set(20, ph - 1, 29, lantern(True))
    for z, b in ((19, "smoker[facing=west,lit=false]"), (20, "water_cauldron[level=3]"),
                 (21, "barrel[facing=up,open=false]"), (22, "crafting_table"), (23, "barrel[facing=up,open=false]")):
        d.set(ix2, 2, z, b)
    for z in (19, 20, 21):
        d.set(ix2, 3, z, "spruce_trapdoor[facing=west,half=top,open=true,powered=false,waterlogged=false]")
    d.item(24, 2, iz1, "grindstone", "south")                          # tool wall on the street side
    d.set(25, 2, iz1, "anvil[facing=east]")
    d.set(26, 2, iz1, "barrel[facing=up,open=false]")
    for x in (24, 25, 26, 27):
        d.set(x, 3, iz1, "spruce_trapdoor[facing=south,half=top,open=true,powered=false,waterlogged=false]")
    d.set(ix1, 2, iz1, "barrel[facing=up,open=false]")
    d.set(ix1, 3, iz1, "potted_fern")
    d.bed(ix1 + 1, 2, iz2, "south", "green")                         # watchman's bunk
    d.set(ix1, 2, iz2, TS)
    d.candle(ix1, 3, iz2, 2)
    d.set(cx, 2, iz2, log("stripped_spruce_log"))                    # the giant's model
    d.set(cx, 3, iz2, "red_wool")
    d.set(cx, 4, iz2, "black_wool")
    d.set(cx + 1, 2, iz2, "lectern[facing=north,has_book=true,powered=false]")
    d.set(25, 2, 26, "cartography_table")
    d.chair(24, 2, 26, "west", "spruce", sit=False)
    d.set(ix2, 2, iz2, "barrel[facing=up,open=false]")
    d.set(ix2, 2, iz2 - 1, "hay_block[axis=y]")
    d.set(ix2, 3, iz2, "potted_fern")
    d.set(ix1, 4, 21, "green_wall_banner[facing=east]")
    for x, z in ((17, 21), (cx, 23), (25, 22), (25, 30)):
        d.set(x, ph - 1, z, lantern(True))


def cg_hall5(d, x1, z1, x2, z2, ph):
    """L5 crib of the Timber Giant (interior 12..30 x 17..33), two storeys. Ground floor = the camp hall: stone
    hearth with armchairs on the west wall, two long mess tables, the cook's corner, a tool wall with grindstone
    and anvil on the east, the map table, the giant's carved model at the back; stair up on the west wall.
    Upper floor (walk y6) = the bunk loft: bunks with footlockers along the back and east walls, a card table,
    the wash corner, a reading nook, lanterns on the lockers."""
    ix1, iz1, ix2, iz2 = hall_box(x1, z1, x2, z2)                     # 12, 17, 30, 33
    cx = (x1 + x2) // 2                                              # 21
    TS = slab("spruce_slab", "top")
    d.fill(ix1, 1, iz1, ix2, 1, iz2, "spruce_planks")
    # ---- structure
    d.fill(ix1, 5, iz1, ix2, 5, iz2, "spruce_planks")
    for z in range(z1 + 2, z2 - 1, 3):
        for x in (x1, x2):
            d.set(x, 6, z, "glass_pane")
    for i, z in enumerate((18, 19, 20, 21)):
        d.set(ix1, 2 + i, z, stair("spruce_stairs", "south"))
        if i:
            d.fill(ix1, 2, z, ix1, 1 + i, z, "spruce_planks")
    d.clear(ix1, 5, 18, ix1, 5, 20)
    for z in (18, 19, 20):
        d.set(ix1 + 1, 6, z, fence("spruce_fence"))
    # ================================================================ ground floor
    d.hearth(ix1, 2, 26, "east", ph + 1, "cobblestone", "campfire")
    d.chair(14, 2, 25, "east", "spruce", sit=False)
    d.chair(14, 2, 27, "east", "spruce", sit=False)
    d.rug(13, 25, 13, 27, 2, ("brown_carpet",), "plain")
    d.set(ix1, 2, 24, "barrel[facing=up,open=false]")
    d.set(ix1, 3, 24, "potted_fern")
    for x in (17, 25):                                               # two mess tables
        d.dining(x, 2, 20, 4, "z", "spruce", chairs=("e", "w"), sit=False)
        d.set(x, 4, 21, lantern(True))
    for x, b in ((26, "barrel[facing=up,open=false]"), (27, "smoker[facing=south,lit=false]"),
                 (28, "water_cauldron[level=3]"), (29, "crafting_table"), (30, "barrel[facing=up,open=false]")):
        d.set(x, 2, iz1, b)                                          # cook's corner along the street wall
    d.set(ix2, 2, 18, TS)
    d.set(ix2, 3, 18, "decorated_pot[cracked=false,facing=west,waterlogged=false]")
    d.set(ix2, 2, 19, "barrel[facing=west,open=false]")
    d.set(28, 3, iz1, "spruce_trapdoor[facing=south,half=top,open=true,powered=false,waterlogged=false]")
    # tool wall, east
    d.item(ix2, 2, 23, "grindstone", "west")
    d.set(ix2, 2, 24, "anvil[facing=north]")
    d.set(ix2, 2, 26, "smithing_table")
    d.set(ix2, 2, 27, "barrel[facing=up,open=false]")
    for z in (23, 24, 25, 26, 27):
        d.set(ix2, 3, z, "spruce_trapdoor[facing=west,half=top,open=true,powered=false,waterlogged=false]")
    d.set(ix2, 2, 25, "chest[facing=west,type=single,waterlogged=false]")
    # map table and giant model at the back
    d.set(26, 2, 30, "cartography_table")
    d.chair(25, 2, 30, "west", "spruce", sit=False)
    d.chair(26, 2, 31, "south", "spruce", sit=False)
    d.set(cx, 2, iz2, log("stripped_spruce_log"))
    d.set(cx, 3, iz2, "red_wool")
    d.set(cx, 4, iz2, "black_wool")
    d.set(cx + 1, 2, iz2, "lectern[facing=north,has_book=true,powered=false]")
    d.set(cx - 1, 2, iz2, "potted_fern")
    d.rug(cx - 1, 30, cx + 1, 31, 2, ("green_carpet",), "plain")
    d.set(ix1, 2, iz2, "hay_block[axis=y]")                         # the watchman's cot in the corner
    d.bed(ix1 + 2, 2, iz2, "south", "green")
    d.set(ix1 + 1, 2, iz2, TS)
    d.candle(ix1 + 1, 3, iz2, 2)
    d.set(ix2, 2, iz2, "barrel[facing=up,open=false]")
    d.set(ix2, 2, iz2 - 1, "barrel[facing=up,open=false]")
    for x, z in ((14, 21), (cx, 26), (28, 22), (16, 31), (28, 31)):
        d.set(x, 4, z, lantern(True))
    d.set(cx, 2, 27, "stripped_spruce_wood[axis=y]")                 # a giant log round on its cradle
    d.set(cx, 3, 27, "moss_carpet")
    d.set(cx - 1, 2, 27, log("spruce_log", "x"))
    d.set(cx + 1, 2, 27, log("spruce_log", "x"))
    d.set(cx + 1, 3, 27, "lightning_rod[facing=up,powered=false,waterlogged=false]")   # the bucking saw handle
    d.chair(19, 2, iz1, "north", "spruce", sit=False)                # boot benches by the door
    d.chair(23, 2, iz1, "north", "spruce", sit=False)
    d.set(18, 2, iz1, "barrel[facing=up,open=false]")
    # ================================================================ upper floor: the bunk loft
    y = 6
    for x in (14, 17, 20, 23):                                       # bunks along the back wall
        d.bed(x, y, iz2, "south", ("red", "green", "yellow", "blue")[(x - 14) // 3])
        d.set(x + 1, y, iz2, "chest[facing=north,type=single,waterlogged=false]")
        d.set(x + 1, y + 1, iz2, lantern(False))
    for z in (21, 24, 27):                                           # and along the east wall
        d.bed(ix2, y, z, "east", ("brown", "red", "green")[(z - 21) // 3])
        d.set(ix2, y, z + 1, "chest[facing=west,type=single,waterlogged=false]")
    d.set(ix2, y + 1, 22, lantern(False))
    d.table(cx, y, 25, "spruce")                                     # card table
    for side, (ddx, ddz) in (("north", (0, -1)), ("south", (0, 1)), ("west", (-1, 0)), ("east", (1, 0))):
        d.chair(cx + ddx, y, 25 + ddz, side, "spruce", sit=False)
    d.rug(cx - 2, 23, cx + 2, 23, y, ("brown_carpet",), "plain")
    d.set(ix2, y, iz1, "water_cauldron[level=3]")                   # wash corner
    d.set(ix2 - 1, y, iz1, "barrel[facing=up,open=false]")
    d.set(ix2 - 2, y, iz1, TS)
    d.set(ix2 - 2, y + 1, iz1, "decorated_pot[cracked=false,facing=south,waterlogged=false]")
    for x in (26, 27):
        d.set(x, y + 1, iz1, "spruce_trapdoor[facing=south,half=top,open=true,powered=false,waterlogged=false]")
    d.bookshelf(15, y, iz1, 2)                                       # reading nook by the stair
    d.set(16, y, iz1, "bookshelf")
    d.chair(16, y, iz1 + 2, "south", "spruce", sit=False)
    d.set(17, y, iz1 + 2, TS)
    d.set(17, y + 1, iz1 + 2, lantern(False))
    d.set(ix1, y, iz2 - 2, "barrel[facing=up,open=false]")
    d.set(ix1, y, iz2 - 3, "potted_fern")
    d.set(cx, y + 1, iz1, "green_wall_banner[facing=south]")
    d.set(26, y, 29, TS)                                             # mending table by the east windows
    d.chair(26, y, 30, "south", "spruce", sit=False)
    d.chair(25, y, 29, "west", "spruce", sit=False)
    d.set(26, y + 1, 29, "white_wool")
    d.set(18, y, 28, "hay_block[axis=x]")                            # spare straw ticks
    d.set(18, y, 29, "hay_block[axis=x]")


def cg_hall(d, x1, z1, x2, z2, ph, L):
    """Camp hall in the giant's plinth (hand-placed): stone hearth on the west wall with a bench before it, a
    cook's corner (barrels, smoker shelf), the axe-grinding bench, a carved model of the giant at the back,
    a map table, lanterns; later a bunk alcove and a tool wall."""
    if L >= 5:
        return cg_hall5(d, x1, z1, x2, z2, ph)
    if L == 4:
        return cg_hall4(d, x1, z1, x2, z2, ph)
    ix1, iz1, ix2, iz2 = hall_box(x1, z1, x2, z2)
    cx, cz = (x1 + x2) // 2, (z1 + z2) // 2
    d.fill(ix1, 1, iz1, ix2, 1, iz2, "spruce_planks")
    d.hearth(ix1, 2, cz, "east", ph, "cobblestone", "campfire")
    d.chair(ix1 + 2, 2, cz, "east", "spruce", sit=False)                 # bench facing the fire
    d.rug(ix1 + 1, cz - 1, ix1 + 1, cz + 1, 2, ("green_carpet",), "plain")
    d.set(ix2, 2, iz1, "barrel[facing=up,open=false]")                  # cook's corner
    d.set(ix2, 2, iz1 + 1, "barrel[facing=up,open=false]")
    d.item(ix2, 2, cz + 1, "grindstone", "west")
    d.set(cx, 2, iz2, log("stripped_spruce_log"))                         # model of the giant
    d.set(cx, 3, iz2, "red_wool")
    d.set(cx, 2, iz2 - 1, "green_carpet")
    d.set(cx + 1, 2, iz2, "lectern[facing=north,has_book=true,powered=false]")
    d.set(cx, ph - 1, cz, lantern(True))
    if L >= 2:
        d.set(cx - 1, 2, iz1 + 1, "cartography_table")                     # map table with stools
        d.chair(cx - 2, 2, iz1 + 1, "west", "spruce", sit=False)
        d.set(ix2, 3, iz1, "potted_fern")
    if L >= 3:
        d.item(ix2, 2, cz + 2, "smoker", "west")
        d.set(ix2, 2, cz + 3, "crafting_table")
        d.set(ix2, 3, cz - 1, "spruce_trapdoor[facing=west,half=top,open=true,powered=false,waterlogged=false]")
        d.set(cx - 2, 2, iz2, "barrel[facing=north,open=false]")
        d.set(cx + 2, 2, iz2, "hay_block[axis=y]")
        d.dining(cx + 2, 2, cz - 1, 2, "z", "spruce", chairs=("e", "w"))   # mess table for the crew
    if L >= 4:
        d.bed(ix1 + 1, 2, iz2, "south", "green")                         # bunk alcove for the night watchman
        d.set(ix1 + 2, 2, iz2, slab("spruce_slab", "top"))
        d.candle(ix1 + 2, 3, iz2, 2)
        d.set(cx + 3, 2, iz1, "anvil[facing=east]")
        d.set(cx, ph - 1, iz1 + 2, lantern(True))
    if L <= 3:                                                        # early camp: stores and a stool table
        d.set(ix1, 2, iz1, "barrel[facing=up,open=false]")
        d.set(ix1, 2, iz2, "chest[facing=east,type=single,waterlogged=false]")
        d.set(ix2, 3, iz2, "spruce_trapdoor[facing=west,half=top,open=true,powered=false,waterlogged=false]")
        d.set(ix2, 2, iz2, "barrel[facing=up,open=false]")
        if L <= 2:
            d.table(cx + 2, 2, cz, "spruce")
            d.chair(cx + 2, 2, cz + 1, "south", "spruce", sit=False)
            d.chair(cx + 1, 2, cz, "west", "spruce", sit=False)
        else:
            d.bed(ix1 + 1, 2, iz2, "south", "green")
            d.set(ix1 + 2, 2, iz2, slab("spruce_slab", "top"))
            d.set(cx - 2, 2, iz1, "potted_fern")
    if L >= 5:
        d.set(ix1, 4, iz1 + 1, "green_wall_banner[facing=east]")
        d.set(ix2, 4, iz2 - 1, "green_wall_banner[facing=west]")
        d.rug(cx - 1, cz - 2, cx + 1, cz + 2, 2, ("brown_carpet", "green_carpet"))


def nb_hall(d, x1, z1, x2, z2, ph, L):
    """Beacon gallery (hand-placed): reception desk beside the door, the statue model on a lit plinth at the
    back, two info kiosks, a bench pair, planters in the corners; later a media wall, display cases."""
    if L >= 5:
        return nb_hall5(d, x1, z1, x2, z2, ph)
    if L == 4:
        return nb_hall4(d, x1, z1, x2, z2, ph)
    ix1, iz1, ix2, iz2 = hall_box(x1, z1, x2, z2)
    cx, cz = (x1 + x2) // 2, (z1 + z2) // 2
    d.fill(ix1, 1, iz1, ix2, 1, iz2, "polished_diorite")
    d.rug(cx, iz1, cx, iz2 - 1 if L <= 2 else cz - 1, 2, ("orange_carpet",), "plain")
    d.set(cx, 2, iz2, "smooth_quartz")                                   # model on a lit plinth
    d.set(cx, 3, iz2, "white_stained_glass")
    d.set(cx - 1, 2, iz2, "lectern[facing=north,has_book=true,powered=false]")
    d.set(ix2, 2, iz1, "potted_bamboo")
    d.set(ix1, 2, iz2, "potted_bamboo")
    d.set(cx, ph, cz, "sea_lantern")                                     # flush ceiling lights
    d.set(cx, ph, iz1 + 1, "sea_lantern")
    if L >= 2:
        d.counter(cx + 2, iz1 + 1, cx + 3, iz1 + 1, 2, body="white_concrete")   # reception desk
        d.chair(cx + 2, 2, iz1 + 2, "south", "cherry", sit=False)
        d.chair(cx - 1, 2, cz, "north", "cherry", sit=False)
        d.chair(cx + 1, 2, cz, "north", "cherry", sit=False)
    if L >= 3:
        d.set(ix1, 2, cz, "lectern[facing=east,has_book=true,powered=false]")
        d.set(ix2, 2, cz, "lectern[facing=west,has_book=true,powered=false]")
        d.set(ix1, 2, iz1, "potted_bamboo")
        d.set(cx - 2, ph, iz2 - 1, "sea_lantern")
        d.set(cx + 2, ph, iz2 - 1, "sea_lantern")
    if L >= 4:
        for x in (cx - 3, cx + 3):                                       # display cases
            d.set(x, 2, iz2, "white_concrete")
            d.set(x, 3, iz2, "white_stained_glass")
        d.set(ix1, 3, cz + 2, "black_stained_glass_pane")                  # media wall
        d.set(ix1, 3, cz + 3, "black_stained_glass_pane")
        d.rug(cx - 2, cz - 1, cx + 2, cz + 1, 2, ("light_gray_carpet", "orange_carpet"))
    # early gallery (L1-3): a display case and an exhibit pot in the back-east corner, the media panel on the
    # west wall, a rug in front of the bench pair, cases in the four bays at L3
    d.set(ix2, 2, iz2, "smooth_quartz")
    d.set(ix2, 3, iz2, "white_stained_glass")
    d.set(ix2, 2, iz2 - 1, "smooth_quartz_slab[type=top,waterlogged=false]")
    d.set(ix2, 3, iz2 - 1, "decorated_pot[cracked=false,facing=west,waterlogged=false]")
    for z in (cz - 1, cz, cz + 1):
        d.set(ix1, 3, z, "black_stained_glass_pane")
    if L >= 2:
        d.rug(cx - 1, cz + 1, cx + 1, cz + 1, 2, ("light_gray_carpet",), "plain")
        d.set(ix1, 2, iz2 - 1, "chiseled_bookshelf[facing=east,slot_0_occupied=true,slot_1_occupied=true,"
              "slot_2_occupied=false,slot_3_occupied=true,slot_4_occupied=true,slot_5_occupied=false]")
    if L >= 3:
        for x, z, top in ((ix1 + 2, iz1 + 2, "white_stained_glass"), (ix2 - 2, iz1 + 3, "white_stained_glass"),
                          (ix1 + 2, iz2 - 2, "decorated_pot[cracked=false,facing=north,waterlogged=false]"),
                          (ix2 - 2, iz2 - 2, "decorated_pot[cracked=false,facing=north,waterlogged=false]")):
            d.set(x, 2, z, "smooth_quartz")
            d.set(x, 3, z, top)
        d.chair(cx - 3, 2, cz + 2, "east", "cherry", sit=False)
        d.chair(cx + 3, 2, cz + 2, "west", "cherry", sit=False)

def cbook(facing, k=0):
    """Chiseled bookshelf, partly filled (k varies the pattern)."""
    occ = [((i + k) % 3) != 0 for i in range(6)]
    return f"chiseled_bookshelf[facing={facing}," + ",".join(
        f"slot_{i}_occupied={'true' if o else 'false'}" for i, o in enumerate(occ)) + "]"


def nb_hall4(d, x1, z1, x2, z2, ph):
    """L4 Beacon gallery (interior 16..32 x 18..34, one tall storey): reception by the door, the statue model in
    the middle with benches, exhibit plinths on the west front, a media theatre on the EAST wall, the archive
    with a reading table in the back-west corner, souvenir counter at the back, pendant lights."""
    ix1, iz1, ix2, iz2 = hall_box(x1, z1, x2, z2)
    cx = (x1 + x2) // 2                                              # 24
    Q = "smooth_quartz_slab[type=top,waterlogged=false]"
    d.fill(ix1, 1, iz1, ix2, 1, iz2, "polished_diorite")
    d.rug(cx, iz1, cx, iz1 + 5, 2, ("orange_carpet",), "plain")
    d.counter(26, 19, 27, 19, 2, top="smooth_quartz_slab")           # reception
    d.chair(26, 2, 20, "south", "cherry", sit=False)
    d.set(27, 3, 19, "black_stained_glass_pane")
    d.set(ix2, 2, iz1, "potted_bamboo")
    d.set(ix1, 2, iz1, "potted_bamboo")
    d.set(cx, 2, 27, "smooth_quartz")                                # the model, benches round it
    d.set(cx, 3, 27, "white_stained_glass")
    d.set(cx, 4, 27, "end_rod[facing=up]")
    d.rug(cx - 1, 26, cx + 1, 28, 2, ("cyan_carpet",), "plain")
    d.chair(cx, 2, 25, "north", "cherry", sit=False)
    d.chair(cx, 2, 29, "south", "cherry", sit=False)
    d.chair(cx - 2, 2, 27, "west", "cherry", sit=False)
    for x, z, top in ((18, 20, "decorated_pot[cracked=false,facing=north,waterlogged=false]"),
                      (20, 20, "white_stained_glass"), (18, 23, "white_stained_glass")):
        d.set(x, 2, z, Q)
        d.set(x, 3, z, top)
    d.set(19, 2, 20, "lectern[facing=north,has_book=true,powered=false]")
    for z in range(25, 30):                                          # media theatre, east wall
        for y in (3, 4):
            d.set(ix2, y, z, "black_stained_glass_pane")
    for x in (28, 30):
        for z in (26, 27, 28):
            d.chair(x, 2, z, "west", "cherry", sit=False)
    d.set(ix2, 2, 24, "jukebox[has_record=false]")
    for z in range(29, 35):                                          # archive, back-west
        d.set(ix1, 2, z, cbook("east", z))
        d.set(ix1, 3, z, "bookshelf" if z % 2 else cbook("east", z + 1))
    d.dining(18, 2, 31, 2, "z", "cherry", chairs=("e",), sit=False)
    d.set(18, 3, 31, "candle[candles=2,lit=false,waterlogged=false]")
    d.counter(26, 32, 28, 32, 2, top="smooth_quartz_slab")           # souvenir counter and shelves
    d.chair(27, 2, 33, "south", "cherry", sit=False)
    for x in range(25, 32):
        d.set(x, 2, iz2, cbook("north", x))
    for x in (25, 28, 31):
        d.set(x, 3, iz2, "decorated_pot[cracked=false,facing=north,waterlogged=false]")
    d.set(ix2, 2, iz2, "potted_bamboo")
    d.set(cx - 2, 3, iz2, "orange_wall_banner[facing=north]")
    for x, z in ((19, 21), (cx, 22), (29, 22), (19, 28), (29, 27), (cx, 31), (20, 33)):
        d.set(x, ph - 1, z, "end_rod[facing=down]")


def nb_hall5(d, x1, z1, x2, z2, ph):
    """L5 Beacon pedestal (interior 14..34 x 16..36): two storeys. Ground floor = the Beacon gallery: reception
    desk, the statue model in the middle with a ring of benches, exhibit plinths (west front), a media theatre on
    the west wall, an education corner with low tables (east front), souvenir shop at the back, stair on the east
    wall. Upper floor (y5 deck, walk y6) = the Beacon club: open office along the street windows, meeting table,
    lounge round a rug, library wall, control desk looking out of the back windows."""
    ix1, iz1, ix2, iz2 = hall_box(x1, z1, x2, z2)                     # 14, 16, 34, 36
    cx = (x1 + x2) // 2                                              # 24
    Q = "smooth_quartz_slab[type=top,waterlogged=false]"
    d.fill(ix1, 1, iz1, ix2, 1, iz2, "polished_diorite")
    # ---- structure: upper floor deck at y5 with a blackstone spandrel in the glass band, stair on the east wall
    d.fill(ix1, 5, iz1, ix2, 5, iz2, "smooth_quartz")
    for x in range(x1, x2 + 1):
        for z in (z1, z2):
            d.set(x, 5, z, "polished_blackstone")
    for z in range(z1, z2 + 1):
        for x in (x1, x2):
            d.set(x, 5, z, "polished_blackstone")
    for i, z in enumerate((30, 31, 32, 33)):
        d.set(ix2, 2 + i, z, stair("smooth_quartz_stairs", "south"))
        if i:
            d.fill(ix2, 2, z, ix2, 1 + i, z, "white_concrete")
    d.clear(ix2, 5, 30, ix2, 5, 32)
    for z in (30, 31, 32):
        d.set(ix2 - 1, 6, z, "iron_bars")                            # stair-well railing upstairs
    # ================================================================ ground floor
    d.rug(cx, iz1, cx, iz1 + 6, 2, ("orange_carpet",), "plain")      # entrance runner (7)
    d.counter(26, 18, 28, 18, 2, top="smooth_quartz_slab")           # reception desk
    d.chair(26, 2, 19, "south", "cherry", sit=False)
    d.chair(28, 2, 19, "south", "cherry", sit=False)
    d.set(26, 3, 18, "black_stained_glass_pane")
    d.set(28, 3, 18, "potted_bamboo")
    d.set(29, 2, 17, "potted_bamboo")
    d.set(19, 2, 17, "potted_bamboo")
    # statue model in the middle, benches round it
    d.set(cx, 2, 26, "smooth_quartz")
    d.set(cx, 3, 26, "white_stained_glass")
    d.set(cx, 4, 26, "end_rod[facing=up]")
    d.rug(cx - 1, 25, cx + 1, 27, 2, ("cyan_carpet",), "plain")
    d.chair(cx, 2, 24, "north", "cherry", sit=False)
    d.chair(cx, 2, 28, "south", "cherry", sit=False)
    d.chair(cx - 2, 2, 26, "west", "cherry", sit=False)
    d.chair(cx + 2, 2, 26, "east", "cherry", sit=False)
    # exhibits, west front: plinths with pots and glass cases, info lecterns between them
    for x, z, top in ((16, 18, "decorated_pot[cracked=false,facing=north,waterlogged=false]"),
                      (19, 18, "white_stained_glass"),
                      (16, 21, "white_stained_glass"),
                      (19, 21, "decorated_pot[cracked=false,facing=east,waterlogged=false]")):
        d.set(x, 2, z, Q)
        d.set(x, 3, z, top)
    d.set(17, 2, 18, "lectern[facing=north,has_book=true,powered=false]")
    d.set(18, 2, 21, "lectern[facing=north,has_book=true,powered=false]")
    d.set(ix1, 2, iz1, "potted_bamboo")
    # media theatre on the west wall
    for z in range(25, 30):
        for y in (3, 4):
            d.set(ix1, y, z, "black_stained_glass_pane")
    d.set(ix1, 2, 27, "jukebox[has_record=false]")
    for x in (17, 19):
        for z in (26, 27, 28):
            d.chair(x, 2, z, "east", "cherry", sit=False)
    # education corner, east front: two low tables with stools, chalkboard, book trolley
    for tx in (29, 32):
        d.set(tx, 2, 23, Q)
        d.chair(tx, 2, 22, "north", "cherry", sit=False)
        d.chair(tx, 2, 24, "south", "cherry", sit=False)
    for z in (21, 22, 23, 24):
        d.set(ix2, 3, z, "black_stained_glass_pane")                 # chalkboard
    d.set(ix2, 2, 26, cbook("west", 1))
    d.set(ix2, 2, 27, cbook("west", 2))
    d.rug(29, 26, 32, 27, 2, ("light_blue_carpet", "yellow_carpet"), "check")   # play mat (8)
    # souvenir shop at the back
    d.counter(27, 33, 29, 33, 2, top="smooth_quartz_slab")
    d.chair(28, 2, 34, "south", "cherry", sit=False)
    for x in range(26, 33):
        d.set(x, 2, iz2, cbook("north", x))
    for x in (26, 28, 30, 32):
        d.set(x, 3, iz2, "decorated_pot[cracked=false,facing=north,waterlogged=false]")
    d.set(31, 2, 31, "barrel[facing=up,open=false]")
    d.set(31, 3, 31, "potted_bamboo")
    # archive and curator's desk, back west corner
    for z in range(32, 37):
        d.set(ix1, 2, z, cbook("east", z))
        d.set(ix1, 3, z, cbook("east", z + 1))
    d.set(17, 2, 34, Q)
    d.set(18, 2, 34, Q)
    d.chair(17, 2, 35, "south", "cherry", sit=False)
    d.set(18, 3, 34, "black_stained_glass_pane")
    d.set(17, 3, 34, "candle[candles=2,lit=false,waterlogged=false]")
    d.set(20, 2, iz2, "potted_bamboo")
    d.set(cx, 2, iz2, "smooth_quartz")                               # back-wall relief: a second model
    d.set(cx, 3, iz2, "white_stained_glass")
    d.set(cx - 1, 3, iz2, "orange_wall_banner[facing=north]")
    d.set(cx + 1, 3, iz2, "orange_wall_banner[facing=north]")
    for x, z in ((17, 19), (17, 30), (cx, 20), (cx, 32), (30, 20), (30, 29), (21, 26), (27, 26), (29, 35)):
        d.set(x, 4, z, "end_rod[facing=down]")
    # ================================================================ upper floor (walk y6)
    y = 6
    for x in (16, 17, 18, 21, 22, 23, 26, 27, 28):                   # open office along the street windows
        d.set(x, y, iz1, Q)
        d.chair(x, y, iz1 + 1, "south", "cherry", sit=False)
        if x in (17, 22, 27):
            d.set(x, y + 1, iz1, "black_stained_glass_pane")
    d.set(19, y, iz1, "potted_bamboo")
    d.set(25, y, iz1, "potted_bamboo")
    d.set(ix1, y, iz1, "barrel[facing=up,open=false]")
    d.set(ix1, y, iz1 + 1, "barrel[facing=up,open=false]")
    # meeting table, west
    for z in (23, 24, 25):
        d.set(17, y, z, Q)
        d.chair(16, y, z, "west", "cherry", sit=False)
        d.chair(18, y, z, "east", "cherry", sit=False)
    d.chair(17, y, 22, "north", "cherry", sit=False)
    d.set(ix1, y + 1, 24, "black_stained_glass_pane")
    d.set(ix1, y, 21, "potted_bamboo")
    # lounge round a rug in the middle
    d.rug(23, 26, 26, 28, y, ("orange_carpet", "white_carpet"), "border")   # 12
    d.set(24, y, 27, "smooth_quartz_slab[type=bottom,waterlogged=false]")
    d.set(25, y, 27, "smooth_quartz_slab[type=bottom,waterlogged=false]")
    for x in (23, 24, 25, 26):
        d.chair(x, y, 25, "north", "cherry", sit=False)
        d.chair(x, y, 29, "south", "cherry", sit=False)
    d.set(22, y, 27, "potted_bamboo")
    d.set(27, y, 27, "potted_bamboo")
    # library wall, east
    for z in range(18, 28):
        d.set(ix2, y, z, cbook("west", z))
        d.set(ix2, y + 1, z, "bookshelf" if z % 3 else cbook("west", z + 2))
    for z in (20, 24):
        d.chair(31, y, z, "west", "cherry", sit=False)
        d.set(31, y, z + 1, "smooth_quartz_slab[type=bottom,waterlogged=false]")
    # control desk at the back windows: beacon console
    for x in range(19, 30):
        if x in (22, 26):
            continue
        d.set(x, y, iz2, Q)
    for x in (20, 24, 28):
        d.chair(x, y, iz2 - 1, "north", "cherry", sit=False)
        d.set(x, y + 1, iz2, "black_stained_glass_pane")
    d.set(22, y, iz2, "lectern[facing=north,has_book=true,powered=false]")
    d.set(26, y, iz2, "redstone_lamp[lit=false]")
    d.set(ix1, y, iz2, "potted_bamboo")
    d.set(ix1, y, 33, "barrel[facing=up,open=false]")
    d.set(ix1, y, 32, cbook("east", 3))
    d.rug(19, 32, 21, 34, y, ("gray_carpet",), "plain")
    d.rug(28, 32, 30, 34, y, ("gray_carpet",), "plain")
    d.dining(29, y, 22, 2, "z", "cherry", chairs=("w", "n", "s"), sit=False)      # reading table
    d.set(29, y + 1, 22, "candle[candles=3,lit=false,waterlogged=false]")
    d.dining(21, y, 20, 2, "x", "cherry", chairs=("n", "s"), sit=False)          # stand-up table by the office
    for x, b in ((30, "smoker[facing=north,lit=false]"), (31, "water_cauldron[level=3]"), (32, Q),
                 (33, "barrel[facing=up,open=false]")):                          # tea kitchen in the corner
        d.set(x, y, iz2, b)
    d.set(32, y + 1, iz2, "decorated_pot[cracked=false,facing=north,waterlogged=false]")
    for x, z in ((18, 19), (24, 19), (30, 19), (19, 26), (30, 31), (19, 31), (24, 33), (30, 25)):
        d.set(x, 8, z, "sea_lantern")


# ---------------------------------------------------------------------------- Hearthwood: The Old King
HK_SIZE = (45, 60, 46)
HK_C = (22, 25)
HK_DIM = {1: (4, 4, 4), 2: (5, 5, 5), 3: (7, 6, 6), 4: (9, 8, 7), 5: (10, 9, 8)}
HK_PX, HK_PZ, HK_PW = (8, 32), 8, 5
HK_WHUT = (1, 1, 3)
HK_PT = {1: 5, 2: 8, 3: 12, 4: 16, 5: 20}
HS = dict(wall="smooth_sandstone", quoin="cut_sandstone", carve="chiseled_sandstone", st="sandstone_stairs",
          sl="smooth_sandstone_slab", wl="sandstone_wall", sst="smooth_sandstone_stairs")


def hk_wing(rel, L):
    """Sandstone guard obelisk: rusticated base with a lantern niche, tapering shaft, brick band, brazier."""
    d = Design("Hearthwood", rel, (HK_PW, 30, HK_PW), gy=0, paving="cut_sandstone")
    n, T = HK_PW - 1, HK_PT[L]
    d.fill(0, 0, 0, n, 0, n, "cut_sandstone")
    d.box(0, 1, 0, n, 4, n, HS["wall"])
    d.clear(1, 1, 1, n - 1, 4, n - 1)
    for x, z in ((0, 0), (n, 0), (0, n), (n, n)):
        d.fill(x, 1, z, x, 4, z, HS["quoin"])
    d.fill(0, 1, 0, n, 1, 0, HS["quoin"])
    d.door(2, 1, 0, "south", "oak")
    d.hut(*HK_WHUT)
    d.lamp(2, 4, 2)
    d.set(3, 1, 3, HS["carve"])
    d.candle(3, 2, 3, 3)
    d.set(1, 1, 1, "potted_red_tulip")
    d.set(2, 1, 2, "red_carpet")
    for x in (0, n):
        d.set(x, 2, 2, "glass_pane")
    ring_stairs(d, 0, 0, n, n, 5, HS["sst"])
    for y in range(5, T + 1):
        for x in range(1, 4):
            for z in range(1, 4):
                d.set(x, y, z, "bricks" if y % 5 == 0 else (HS["quoin"] if (x, z) != (2, 2) else HS["wall"]))
    for y in range(7, T - 1, 4):
        d.set(2, y, 1, HS["carve"])
    if L >= 2:
        d.set(2, T - 2, 0, "red_wall_banner[facing=north]")
    ring_stairs(d, 1, 1, 3, 3, T + 1, HS["sst"], "top", inward=False)
    d.set(2, T + 1, 2, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    return d


def hk_pavilion(d, x1, z1, x2, z2, kind):
    """Classical sandstone pavilion with a red-tile pediment roof and a columned portico on the street side."""
    W = HS["wall"]
    d.fill(x1, 1, z1, x2, 1, z2, "polished_granite" if kind == "museum" else "cut_sandstone")
    d.box(x1, 2, z1, x2, 7, z2, W)
    for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        d.fill(x, 2, z, x, 7, z, HS["quoin"])
    for x in range(x1, x2 + 1):
        d.set(x, 2, z1, HS["quoin"])
        d.set(x, 2, z2, HS["quoin"])
    for z in range(z1 + 2, z2 - 1, 3):
        for x, f in ((x1, "west"), (x2, "east")):
            d.window(x, 3, z, x, 5, z)
            ox = -1 if f == "west" else 1
            d.set(x + ox, 6, z, stair(HS["sst"], OPP[f], "top"))
            d.set(x + ox, 2, z, stair(HS["sst"], OPP[f], "top"))
    pots = {"museum": ((0, 21, "red_tulip"), (0, 27, "red_tulip"), (10, 24, "azure_bluet")),
            "chapel": ((34, 24, "white_tulip"), (44, 21, "azure_bluet"), (44, 30, "white_tulip"))}[kind]
    for x, z, f in pots:                                             # pots on chosen window sills
        d.set(x, 3, z, f"potted_{f}")
    rd = d.gable(x1, z1, x2, z2, 8, "z", "brick_stairs", "brick_slab", W, 1)
    # portico on the north
    cx = (x1 + x2) // 2
    d.fill(x1, 1, z1 - 3, x2, 1, z1 - 1, "cut_sandstone")
    for x in range(x1, x2 + 1, 2):
        d.fill(x, 2, z1 - 3, x, 6, z1 - 3, HS["wl"] + "[east=none,north=none,south=none,up=true,"
               "waterlogged=false,west=none]")
        d.set(x, 7, z1 - 3, HS["carve"])
    d.fill(x1, 7, z1 - 3, x2, 7, z1 - 1, HS["quoin"])
    for x in range(x1, x2 + 1, 2):
        d.set(x, 7, z1 - 3, HS["carve"])
    d.gable(x1, z1 - 3, x2, z1 - 1, 8, "z", "brick_stairs", "brick_slab", W, 0)
    d.clear(cx, 2, z1 - 2, cx, 3, z1 - 1)
    d.door(cx, 2, z1, "south", "oak")
    d.set(cx - 1, 2, z1 - 1, "potted_flowering_azalea_bush")
    d.set(cx + 1, 2, z1 - 1, "potted_flowering_azalea_bush")
    d.sign(cx, 4, z1 - 1, "north", ["MUSEUM" if kind == "museum" else "CHAPEL", "of the", "Old King"], "oak") \
        if kind == "museum" else d.sign(cx, 4, z1 - 1, "north", ["KING'S", "CHAPEL"], "oak")
    y = 2
    if kind == "museum":
        # four relic cases down the hall, the king's sword and crown at the back, archive shelves in the
        # back corners, curator's desk by the door
        for x, z, top in ((x1 + 2, z1 + 3, "white_stained_glass"), (x2 - 2, z1 + 3,
                          "decorated_pot[cracked=false,facing=north,waterlogged=false]"),
                          (x1 + 2, z1 + 7, "decorated_pot[cracked=false,facing=north,waterlogged=false]"),
                          (x2 - 2, z1 + 7, "white_stained_glass")):
            d.set(x, y, z, HS["carve"])
            d.set(x, y + 1, z, top)
        d.set(cx, y, z2 - 1, HS["carve"])
        d.set(cx, y + 1, z2 - 1, "gold_block")
        d.set(cx, y + 2, z2 - 1, "iron_bars")
        d.set(cx - 1, y, z2 - 1, "lectern[facing=north,has_book=true,powered=false]")
        for x in (x1 + 1, x2 - 1):
            for z in (z2 - 1, z2 - 2):
                d.set(x, y, z, "bookshelf")
                d.set(x, y + 1, z, "bookshelf")
        d.set(x2 - 1, y, z1 + 1, slab("oak_slab", "top"))
        d.chair(x2 - 2, y, z1 + 1, "east", "oak", sit=False)
        d.set(x2 - 1, y + 1, z1 + 1, "candle[candles=2,lit=false,waterlogged=false]")
        d.rug(cx - 1, z1 + 1, cx + 1, z2 - 3, y, ("red_carpet", "yellow_carpet"))
        d.set(x1 + 1, 4, z1 + 5, "red_wall_banner[facing=east]")
        d.set(x2 - 1, 4, z1 + 5, "red_wall_banner[facing=west]")
    else:
        # four rows of chairs either side of the aisle, altar with candles, font by the door
        for z in (z1 + 3, z1 + 5, z1 + 7, z1 + 9):
            for x in (cx - 2, cx - 1, cx + 1, cx + 2):
                d.chair(x, y, z, "north", "oak", sit=False)
        d.set(cx, y, z2 - 1, HS["carve"])
        d.candle(cx, y + 1, z2 - 1, 4)
        d.set(cx - 2, y, z2 - 1, "candle[candles=3,lit=false,waterlogged=false]")
        d.set(cx + 2, y, z2 - 1, "candle[candles=3,lit=false,waterlogged=false]")
        d.set(cx, 5, z2, "yellow_stained_glass_pane")
        d.set(x1 + 1, y, z1 + 1, "water_cauldron[level=3]")
        d.fill(cx, 1, z1 + 1, cx, 1, z2 - 2, "bricks")                 # brick aisle inlaid in the floor
    for z in (z1 + 3, z1 + 7):
        chandelier(d, cx, z, rd - 1, 6)


def hw_cottage(d, x1, z1, x2, z2, door_x):
    """Structure only: Tudor estate cottage on a stone-brick sill, calcite panels in a dark-oak frame, leaded
    windows, deepslate gable roof (ridge along x) with a dark-oak tie beam across the middle, north door."""
    d.fill(x1, 1, z1, x2, 1, z2, "stone_bricks")
    d.fill(x1 + 1, 1, z1 + 1, x2 - 1, 1, z2 - 1, "spruce_planks")
    d.box(x1, 2, z1, x2, 5, z2, "calcite")
    for x in range(x1, x2 + 1):
        for z in (z1, z2):
            d.set(x, 2, z, "stone_bricks")
            d.set(x, 5, z, log("dark_oak_log", "x"))
            if (x - x1) % 4 == 0:
                d.fill(x, 3, z, x, 4, z, log("dark_oak_log"))
    for z in range(z1, z2 + 1):
        for x in (x1, x2):
            d.set(x, 2, z, "stone_bricks")
            d.set(x, 5, z, log("dark_oak_log", "z"))
            if z in (z1, z2):
                d.fill(x, 3, z, x, 4, z, log("dark_oak_log"))
    for x in range(x1 + 2, x2 - 1, 4):
        for z in (z1, z2):
            if x != door_x:
                d.window(x, 3, z, x, 4, z, "glass_pane")
    zm = (z1 + z2) // 2
    for x in (x1, x2):
        d.window(x, 3, zm, x, 4, zm, "glass_pane")
    d.door(door_x, 2, z1, "south", "dark_oak")
    d.set(door_x, 1, z1 - 1, "stone_bricks")
    rd = d.gable(x1, z1, x2, z2, 6, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite", 1)
    d.fill(x1 + 1, 6, zm, x2 - 1, 6, zm, log("dark_oak_log", "x"))      # tie beam
    return rd


def hk_gardener(d):
    """Head gardener's cottage (x1..9, z36..43): potting bench with seedlings and a composter by the door, seed
    barrels, tool rack on the back wall, hearth with an armchair on the east, table for two, bed in the
    south-west corner; vegetable rows and a water butt outside."""
    hw_cottage(d, 1, 36, 9, 43, 5)
    d.hearth(8, 2, 40, "west", 10, "bricks", "campfire")
    d.chair(6, 2, 40, "west", "dark_oak", sit=False)
    d.rug(5, 41, 6, 41, 2, ("green_carpet",), "plain")
    d.bed(2, 2, 42, "south", "green")
    d.set(3, 2, 42, slab("dark_oak_slab", "top"))
    d.candle(3, 3, 42, 1)
    d.table(3, 2, 38, "dark_oak")
    d.chair(2, 2, 38, "west", "dark_oak", sit=False)
    d.chair(3, 2, 39, "south", "dark_oak", sit=False)
    d.set(6, 2, 37, slab("spruce_slab", "top"))                       # potting bench
    d.set(7, 2, 37, slab("spruce_slab", "top"))
    d.set(6, 3, 37, "potted_fern")
    d.set(7, 3, 37, "potted_poppy")
    d.set(8, 2, 37, "composter[level=4]")
    d.set(8, 2, 38, "barrel[facing=up,open=false]")
    d.set(2, 2, 37, "barrel[facing=up,open=false]")
    d.set(5, 2, 42, "chest[facing=north,type=single,waterlogged=false]")
    for x in (5, 6, 7):                                              # tool rack on the back wall
        d.set(x, 3, 42, "spruce_trapdoor[facing=north,half=top,open=true,powered=false,waterlogged=false]")
    d.set(7, 2, 42, "grindstone[face=floor,facing=north]")
    d.set(5, 5, 39, lantern(True))
    d.set(3, 5, 39, lantern(True))
    for x, f in ((3, "red_tulip"), (7, "allium")):                    # window boxes on the street side
        d.set(x, 2, 35, trap("dark_oak_trapdoor", "north", "top"))
        d.set(x, 3, 35, f"potted_{f}")
    d.set(4, 2, 35, "barrel[facing=up,open=false]")                  # water butt by the door
    for x in range(1, 10):                                           # vegetable rows behind
        d.set(x, 1, 45, "farmland[moisture=7]")
        d.set(x, 2, 45, ("carrots[age=7]", "potatoes[age=7]", "beetroots[age=3]")[x % 3])
        if x % 4 == 1:
            d.set(x, 2, 44, "sweet_berry_bush[age=3]")
    d.set(0, 1, 45, "water")


def hk_tearoom(d):
    """Tea room (x35..43, z36..43): serving counter with the cake stand, stove, sink and dresser behind it,
    three tables for two by the windows, flowers; a tea garden with two tables outside the back."""
    hw_cottage(d, 35, 36, 43, 43, 39)
    for x in range(37, 41):
        d.set(x, 2, 41, slab("spruce_slab", "top"))
    d.set(38, 3, 41, "cake[bites=0]")
    d.set(40, 3, 41, "candle[candles=3,lit=false,waterlogged=false]")
    d.item(37, 2, 42, "smoker", "north")
    d.set(38, 2, 42, "water_cauldron[level=3]")
    d.set(39, 2, 42, "barrel[facing=up,open=false]")
    d.set(40, 2, 42, "chiseled_bookshelf[facing=north,slot_0_occupied=true,slot_1_occupied=false,"
          "slot_2_occupied=true,slot_3_occupied=true,slot_4_occupied=false,slot_5_occupied=true]")
    d.set(39, 3, 42, "decorated_pot[cracked=false,facing=north,waterlogged=false]")
    d.chair(41, 2, 42, "south", "oak", sit=False)
    for tx, tz, chairs in ((37, 38, (("west", -1, 0), ("south", 0, 1))), (41, 38, (("east", 1, 0), ("south", 0, 1)))):
        d.table(tx, 2, tz, "oak")
        for f, ox, oz in chairs:
            d.chair(tx + ox, 2, tz + oz, f, "oak", sit=False)
    d.set(36, 2, 37, "potted_azure_bluet")
    d.set(42, 2, 37, "potted_red_tulip")
    d.set(36, 2, 42, "barrel[facing=up,open=false]")
    d.set(36, 3, 42, "potted_allium")
    d.rug(38, 38, 40, 39, 2, ("pink_carpet",), "plain")
    d.set(39, 5, 39, lantern(True))
    d.set(37, 5, 39, lantern(True))
    d.set(41, 5, 39, lantern(True))
    for x, f in ((37, "pink_tulip"), (41, "cornflower")):
        d.set(x, 2, 35, trap("dark_oak_trapdoor", "north", "top"))
        d.set(x, 3, 35, f"potted_{f}")
    d.sign(40, 4, 35, "north", ["TEA ROOM"], "dark_oak")
    for tx in (37, 41):                                              # tea garden behind
        d.table(tx, 2, 45, "oak")
        d.chair(tx - 1, 2, 45, "west", "oak", sit=False)
        d.chair(tx + 1, 2, 45, "east", "oak", sit=False)
        d.set(tx, 1, 44, "gravel")
    d.set(39, 2, 45, "rose_bush[half=lower]")
    d.set(39, 3, 45, "rose_bush[half=upper]")


def hk_parterre(d, x1, z1, x2, z2, open_x):
    """Box-hedge parterre: clipped hedge frame with an opening on the path side, gravel cross walks, four flower
    quarters and a sandstone fountain basin in the middle."""
    H = "oak_leaves[distance=1,persistent=true,waterlogged=false]"
    cx, cz = (x1 + x2) // 2, (z1 + z2) // 2
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            edge = x in (x1, x2) or z in (z1, z2)
            if edge:
                if not (x == open_x and z == cz):
                    d.set(x, 2, z, H)
                d.set(x, 1, z, "grass_block")
            elif x == cx or z == cz:
                d.set(x, 1, z, "gravel")
            else:
                d.set(x, 1, z, "coarse_dirt")
                d.set(x, 2, z, ("poppy", "cornflower", "oxeye_daisy", "allium", "red_tulip")[(x * 3 + z) % 5])
    d.set(open_x, 1, cz, "gravel")
    for ddx in (-1, 0, 1):
        for ddz in (-1, 0, 1):
            d.set(cx + ddx, 1, cz + ddz, "water" if (ddx or ddz) else HS["carve"])
            d.set(cx + ddx, 2, cz + ddz, AIR)
    for ddx, ddz, f in ((-2, 0, "east"), (2, 0, "west"), (0, -2, "south"), (0, 2, "north")):
        d.set(cx + ddx, 2, cz + ddz, stair(HS["sst"], f))            # basin kerb
    d.set(cx, 2, cz, HS["carve"])
    d.set(cx, 3, cz, "sandstone_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
    d.set(cx, 4, cz, "potted_flowering_azalea_bush")


def hk_colossus(rel, L):
    d = Design("Hearthwood", rel, HK_SIZE, gy=1, paving="grass_block")
    cx, cz = HK_C
    a, b, ph = HK_DIM[L]
    x1, x2, z1, z2 = cx - a, cx + a, cz - b, cz + b
    W = HS["wall"]
    # ---- approach: gravel path with brick edging, lamp posts, beds
    for z in range(0, z1):
        for x in range(cx - 1, cx + 2):
            d.set(x, 1, z, "gravel")
        if L >= 2:
            d.set(cx - 2, 1, z, "bricks")
            d.set(cx + 2, 1, z, "bricks")
    lamp_post(d, cx - 3, z1 - 3, HS["quoin"], fence("dark_oak_fence"))
    lamp_post(d, cx + 3, z1 - 3, HS["quoin"], fence("dark_oak_fence"))
    if L >= 2:
        for z in range(1, z1 - 4, 1):
            for x in (cx - 4, cx + 4):
                d.set(x, 1, z, "coarse_dirt")
                d.set(x, 2, z, ("poppy", "cornflower", "oxeye_daisy", "allium", "azure_bluet")[z % 5])
            for x in (cx - 5, cx + 5):
                d.set(x, 2, z, "oak_leaves[distance=1,persistent=true,waterlogged=false]")
    # ---- plinth: rusticated sandstone with quoins, base course, cornice, balustraded deck
    d.box(x1, 2, z1, x2, ph - 1, z2, W)
    for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        d.fill(x, 2, z, x, ph - 1, z, HS["quoin"])
    for x in range(x1 + 2, x2 - 1, 3):
        for z in (z1, z2):
            d.set(x, (2 + ph) // 2, z, HS["carve"])
    for z in range(z1 + 2, z2 - 1, 3):
        for x in (x1, x2):
            if ph >= 6:
                d.set(x, 3, z, "glass_pane")
                d.set(x, 4, z, "glass_pane")
            else:
                d.set(x, (2 + ph) // 2, z, HS["carve"])
    d.fill(x1, ph, z1, x2, ph, z2, "cut_sandstone")
    ring_stairs(d, x1 - 1, z1 - 1, x2 + 1, z2 + 1, 2, HS["sst"])
    ring_stairs(d, x1 - 1, z1 - 1, x2 + 1, z2 + 1, ph, HS["sst"], "top")
    if L >= 2:
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                if x in (x1, x2) or z in (z1, z2):
                    corner = x in (x1, x2) and z in (z1, z2)
                    d.set(x, ph + 1, z, HS["quoin"] if corner else
                          wallb(HS["wl"]) if (x + z) % 2 else slab(HS["sl"]))
        for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
            d.set(x, ph + 2, z, "potted_red_tulip" if L < 4 else "campfire[facing=north,lit=true,"
                  "signal_fire=false,waterlogged=false]")
    # foundation hall inside
    hk_hall(d, x1, z1, x2, z2, ph, L)
    d.clear(cx, 2, z1 - 1, cx, 3, z1 - 1)
    d.door(cx, 2, z1, "south", "oak")
    d.set(cx - 1, 2, z1 - 1, stair(HS["sst"], "east"))
    d.set(cx + 1, 2, z1 - 1, stair(HS["sst"], "west"))
    d.set(cx, 1, z1 - 1, "cut_sandstone")
    d.sign(cx, 4 if ph > 4 else 3, z1 - 1 if ph > 4 else z1 - 1, "north", ["THE OLD KING", "Guardian of", "the Realm"],
           "oak") if ph > 4 else d.sign(cx + 2, 3, z1 - 1, "north", ["THE OLD KING"], "oak")
    d.hut(20, 2, 22)
    # ---- statue
    king(cx, cz, ph + 1, COLO_H["Hearthwood"][L]).commit(d, ph + 1)
    # ---- L3: paved forecourt with a herringbone of sandstone and brick, benches
    if L >= 3:
        for x in range(cx - 6, cx + 7):                                # forecourt paving
            for z in range(z1 - 6, z1 - 1):
                d.set(x, 1, z, "bricks" if (x + 2 * z) % 4 == 0 else "cut_sandstone")
        for x in (cx - 6, cx + 6):
            d.chair(x, 2, z1 - 4, "west" if x < cx else "east", "oak", sit=False)
        hk_parterre(d, 1, 2, 7, 14, 7)
        hk_parterre(d, 37, 2, 43, 14, 37)
    # ---- L4: exedra (curved colonnade) behind the statue with benches and urns
    if L >= 4:
        ecz = z2 + 1
        R = 10
        for x in range(cx - R - 1, cx + R + 2):
            for z in range(ecz, ecz + R + 2):
                r = math.hypot(x - cx, z - ecz)
                if not d.bp.inside(x, 2, z):
                    continue
                if R - 0.5 <= r <= R + 0.5:
                    d.set(x, 1, z, "cut_sandstone")
                    col = (x + z) % 2 == 0
                    for y in range(2, 7):
                        d.set(x, y, z, (wallb(HS["wl"]) if col else AIR) if y < 6 else HS["quoin"])
                    d.set(x, 2, z, HS["quoin"] if col else AIR)
                    d.set(x, 7, z, slab("brick_slab"))
                elif R - 2.5 <= r < R - 0.5:
                    d.set(x, 1, z, "polished_granite")
                    d.set(x, 6, z, slab(HS["sl"], "top"))

        for ox, oz, back in ((-8, 2, "west"), (-7, 5, "west"), (-5, 7, "south"), (-2, 9, "south"),
                             (2, 9, "south"), (5, 7, "south"), (7, 5, "east"), (8, 2, "east")):
            d.chair(cx + ox, 2, ecz + oz, back, "oak", sit=False)         # benches round the exedra
        for x in (cx - 3, cx + 3):
            d.set(x, 2, ecz + 3, HS["carve"])
            d.set(x, 3, ecz + 3, "potted_flowering_azalea_bush")
        hk_gardener(d)
    # ---- L5: museum and chapel pavilions, avenue of trees, boundary wall with gate piers
    if L >= 5:
        hk_pavilion(d, 1, 19, 9, 31, "museum")
        hk_pavilion(d, 35, 19, 43, 31, "chapel")
        for z in (2, 6, 10):                                          # avenue of oaks
            for x in (cx - 8, cx + 8):
                yew(d, x, z, 2, "oak_leaves", "oak_log")
        for x in list(range(0, cx - 2)) + list(range(cx + 3, 45)):      # boundary wall on the street
            d.set(x, 2, 0, HS["quoin"] if x % 6 == 0 else W)
            d.set(x, 3, 0, slab(HS["sl"]))
        for x in (cx - 3, cx + 3):
            d.fill(x, 2, 0, x, 4, 0, HS["quoin"])
            d.set(x, 5, 0, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        hk_tearoom(d)
    for px in HK_PX:
        d.reserve(px, 1, HK_PZ, px + HK_PW - 1, 30, HK_PZ + HK_PW - 1)
        d.child_hut(px + HK_WHUT[0], 1 + HK_WHUT[1], HK_PZ + HK_WHUT[2], COLO_WING)
    return d


# ---------------------------------------------------------------------------- Cascadia: Timber Giant
CG_SIZE = (43, 60, 49)
CG_C = (21, 25)
CG_DIM = {1: (4, 4, 4), 2: (5, 5, 5), 3: (7, 6, 6), 4: (8, 8, 7), 5: (10, 9, 8)}
CG_PX, CG_PZ, CG_PW = (7, 31), 8, 5
CG_WHUT = (1, 1, 3)
CG_PT = {1: 6, 2: 9, 3: 13, 4: 17, 5: 21}
CC_PAL["museum"] = ("dark_prismarine_stairs", "dark_prismarine", "dark_prismarine_slab", "birch_log",
                    "stripped_birch_log", "dark_oak", "dark_oak_log", "green_terracotta")
CC_PAL["bunk"] = ("spruce_stairs", "spruce_planks", "spruce_slab", "mangrove_log", "stripped_mangrove_log",
                  "spruce", "stripped_spruce_log", "yellow_terracotta")


def cg_wing(rel, L):
    """Carved timber pole on a little log shrine: painted bands, carved faces, spread-wing crest."""
    d = Design("Cascadia", rel, (CG_PW, 30, CG_PW), gy=0, paving="cobblestone")
    n, T = CG_PW - 1, CG_PT[L]
    d.fill(0, 0, 0, n, 0, n, "spruce_planks")
    d.fill(0, 1, 0, n, 1, n, "tuff")
    d.box(0, 2, 0, n, 4, n, log("mangrove_log", "x"))
    for z in range(n + 1):
        for y in (2, 3, 4):
            d.set(0, y, z, log("mangrove_log", "z"))
            d.set(n, y, z, log("mangrove_log", "z"))
    for x, z in ((0, 0), (n, 0), (0, n), (n, n)):
        d.fill(x, 1, z, x, 4, z, log("stripped_spruce_log"))
    d.clear(1, 1, 1, n - 1, 4, n - 1)
    d.door(2, 1, 0, "south", "spruce")
    d.hut(*CG_WHUT)
    d.set(3, 1, 3, "barrel[facing=up,open=false]")
    d.set(1, 1, 1, "potted_fern")
    d.set(2, 1, 2, "green_carpet")
    d.lamp(2, 4, 2)
    for i in range(n + 1):
        for x, z, f in ((i, 0, "south"), (i, n, "north"), (0, i, "east"), (n, i, "west")):
            sh = "straight"
            if i in (0, n):
                sh = "outer_left" if (x == 0) == (z == 0) else "outer_right"
                f = "south" if z == 0 else "north"
            d.set(x, 5, z, stair("dark_prismarine_stairs", f, "bottom", sh))
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


def cg_sawmill(d, x1, z1, x2, z2):
    """Open-sided sawmill shed: log posts, mangrove-shingle roof, a log on the carriage, stonecutter 'saw',
    grindstone, stacked boards and sawdust (sand)."""
    d.fill(x1, 1, z1, x2, 1, z2, "coarse_dirt")
    for x in range(x1, x2 + 1, 3):
        for z in (z1, z2):
            d.fill(x, 2, z, x, 5, z, log("spruce_log"))
    for x in range(x1, x2 + 1):
        for z in (z1, z2):
            d.set(x, 6, z, log("spruce_log", "x"))
    d.gable(x1, z1, x2, z2, 7, "x", "mangrove_stairs", "mangrove_slab", log("spruce_log", "x"), 1)
    zc = (z1 + z2) // 2
    for x in range(x1 + 1, x2):
        d.set(x, 2, zc, "rail[shape=east_west,waterlogged=false]")
    d.item(x1 + 6, 2, zc - 1, "stonecutter", "north")
    d.item(x1 + 2, 2, z1 + 1, "grindstone", "north")
    for x in range(x2 - 3, x2):
        for y in (2, 3):
            d.set(x, y, z2 - 1, "spruce_planks" if y == 2 else slab("spruce_slab"))
    d.set(x1 + 1, 2, z2 - 1, "sand")
    d.set(x1 + 1, 2, z2 - 2, "barrel[facing=up,open=false]")
    d.set(x2 - 1, 2, z1 + 1, "crafting_table")
    for x in range(x1 + 2, x2 - 1, 4):
        d.set(x, 5, zc, lantern(True))


def cg_campfire(d, cx, cz):
    """Loggers' fire circle: gravel ring, stone-lined campfire, four split-log benches, a stump table with a
    lantern, kindling basket."""
    for ddx in range(-2, 3):
        for ddz in range(-2, 3):
            if abs(ddx) + abs(ddz) <= 3:
                d.set(cx + ddx, 1, cz + ddz, "gravel")
    d.set(cx, 1, cz, "cobblestone")
    d.set(cx, 2, cz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for ddx, ddz, ax in ((-2, 0, "z"), (2, 0, "z"), (0, -2, "x"), (0, 2, "x")):
        d.set(cx + ddx, 2, cz + ddz, log("stripped_spruce_log", ax))
    d.set(cx + 2, 2, cz + 2, log("spruce_log"))
    d.set(cx + 2, 3, cz + 2, "lantern[hanging=false,waterlogged=false]")
    d.set(cx - 2, 2, cz + 2, "barrel[facing=up,open=false]")
    for x in range(cx - 3, cx + 3):                                  # cordwood stack behind, 3 high
        for y in (2, 3, 4):
            d.set(x, y, cz - 4, log("spruce_log", "z"))
    d.set(cx + 3, 2, cz - 3, log("stripped_spruce_log"))              # chopping block
    d.set(cx + 4, 2, cz - 1, fence("spruce_fence"))                  # sawbuck with a log on it
    d.set(cx + 4, 2, cz + 1, fence("spruce_fence"))
    d.set(cx + 4, 3, cz, log("spruce_log", "z"))
    d.set(cx + 4, 3, cz - 1, log("spruce_log", "z"))
    d.set(cx + 4, 3, cz + 1, log("spruce_log", "z"))


def cg_cookhouse(d):
    """Camp cookhouse (x33..41, z16..24, red mangrove logs): flour and salt barrels on the west wall, a mess
    table for six, the cook's run (stove, sink, bread oven, block) on the east wall, armchair at the hearth;
    bench and water barrel on the porch."""
    cc_log_house(d, 33, 16, 9, 9, "parsonage", pal="cabin_red")
    for z, b in ((17, "barrel[facing=up,open=false]"), (18, "barrel[facing=up,open=false]"),
                 (19, "chest[facing=east,type=single,waterlogged=false]"), (21, "hay_block[axis=y]")):
        d.set(34, 2, z, b)
    d.set(34, 3, 17, "decorated_pot[cracked=false,facing=east,waterlogged=false]")
    d.dining(36, 2, 18, 3, "z", "spruce", chairs=("e", "w"), sit=False)
    for z, b in ((17, "smoker[facing=west,lit=false]"), (18, "water_cauldron[level=3]"),
                 (19, "furnace[facing=west,lit=false]"), (20, "crafting_table"), (21, "barrel[facing=up,open=false]")):
        d.set(40, 2, z, b)
    for z in (18, 19, 20):
        d.set(40, 3, z, "spruce_trapdoor[facing=west,half=top,open=true,powered=false,waterlogged=false]")
    d.chair(39, 2, 22, "east", "spruce", sit=False)
    d.rug(35, 22, 36, 22, 2, ("brown_carpet",), "plain")
    d.lamp(37, 6, 18)
    d.lamp(37, 6, 21)
    d.chair(34, 2, 15, "south", "spruce", sit=False)
    d.set(40, 2, 15, "barrel[facing=up,open=false]")
    d.lamp(36, 5, 15)
    shutters(d, 33, 18, 3, "west", "spruce")
    window_box(d, 41, 21, 3, "east", "spruce", "red_tulip")
    d.sign(38, 4, 15, "north", ["COOKHOUSE"], "spruce")


def cg_logdeck(d):
    """Log deck in the front-east yard (x32..41, z1..7): three stacked piles of peeled logs on skids, a cant-hook
    rack, a loading ramp and a lantern post."""
    for z0, h in ((2, 3), (5, 2)):
        for x in range(33, 41):
            d.set(x, 1, z0, "spruce_planks")
            for y in range(2, 2 + h):
                for z in (z0, z0 + 1):
                    if not (y == 1 + h and x in (33, 40)):
                        d.set(x, y, z, log("stripped_spruce_log" if (x + y) % 3 else "spruce_log", "x"))
    for x in (34, 37, 40):
        d.set(x, 2, 8, fence("spruce_fence"))                       # cant-hook rack
        d.set(x, 3, 8, "spruce_trapdoor[facing=north,half=bottom,open=true,powered=false,waterlogged=false]")
    for x in (41,):
        for z in (2, 3):
            d.set(x, 2, z, stair("spruce_stairs", "west"))            # loading ramp
    lamp_post(d, 32, 7, "mossy_cobblestone", log("stripped_spruce_log"))


def cg_colossus(rel, L):
    d = Design("Cascadia", rel, CG_SIZE, gy=1, paving="grass_block")
    cx, cz = CG_C
    a, b, ph = CG_DIM[L]
    x1, x2, z1, z2 = cx - a, cx + a, cz - b, cz + b
    rock = ("cobblestone", "mossy_cobblestone", "andesite", "tuff", "cobblestone")
    # approach: plank boardwalk with rail fences and lanterns
    for z in range(0, z1):
        for x in range(cx - 1, cx + 2):
            d.set(x, 1, z, "spruce_planks" if L >= 3 else "coarse_dirt")
    lamp_post(d, cx - 3, z1 - 3, "mossy_cobblestone", log("stripped_spruce_log"))
    lamp_post(d, cx + 3, z1 - 3, "mossy_cobblestone", log("stripped_spruce_log"))
    # plinth: river-rock base, mangrove log crib, plank deck with corner posts
    rock_top = max(2, ph - 3)
    for y in range(2, ph):
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                if not (x in (x1, x2) or z in (z1, z2)):
                    continue
                if y <= rock_top:
                    d.set(x, y, z, rock[(x * 7 + z * 3 + y * 5) % len(rock)])
                else:
                    ax = "x" if z in (z1, z2) else "z"
                    if x in (x1, x2) and z in (z1, z2):
                        ax = "x" if y % 2 else "z"
                    d.set(x, y, z, log("mangrove_log", ax))
    d.fill(x1, ph, z1, x2, ph, z2, "spruce_planks")
    for x in range(x1 - 1, x2 + 2):
        for z in (z1 - 1, z2 + 1):
            d.set(x, ph, z, slab("spruce_slab", "top"))
    for z in range(z1 - 1, z2 + 2):
        for x in (x1 - 1, x2 + 1):
            d.set(x, ph, z, slab("spruce_slab", "top"))
    for x in range(x1 - 1, x2 + 2):
        for z in range(z1 - 1, z2 + 2):
            if x in (x1 - 1, x2 + 1) or z in (z1 - 1, z2 + 1):              # river-rock step round the base
                d.set(x, 2, z, "mossy_cobblestone" if (x + z) % 2 else "cobblestone")
    for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        d.fill(x, 2, z, x, ph + 1, z, log("stripped_spruce_log"))
        d.set(x, ph + 2, z, "lantern[hanging=false,waterlogged=false]")
    if L >= 2:                                                       # rail around the deck
        for x in range(x1 + 1, x2):
            for z in (z1, z2):
                d.set(x, ph + 1, z, fence("spruce_fence"))
        for z in range(z1 + 1, z2):
            for x in (x1, x2):
                d.set(x, ph + 1, z, fence("spruce_fence"))
    for z in range(z1 + 2, z2 - 1, 3):
        for x in (x1, x2):
            d.set(x, 3, z, "glass_pane")
    # camp hall inside the plinth
    cg_hall(d, x1, z1, x2, z2, ph, L)
    d.clear(cx, 2, z1 - 1, cx, 3, z1 - 1)
    d.door(cx, 2, z1, "south", "mangrove")
    d.set(cx, 1, z1 - 1, "spruce_planks")
    d.set(cx - 1, 2, z1 - 1, "barrel[facing=up,open=false]")
    d.sign(cx + 1, 3, z1 - 1, "north", ["TIMBER", "GIANT"], "spruce")
    d.hut(19, 2, 22)
    # statue
    lumberjack(cx, cz, ph + 1, COLO_H["Cascadia"][L]).commit(d, ph + 1)
    # surroundings by level
    if L >= 2:
        cg_campfire(d, 3, 15)
    if L >= 3:
        cg_sawmill(d, 31, 26, 41, 32)
    if L >= 2:                                                       # woodpiles and stumps
        for z in range(z1, z1 + 5):
            for y in (2, 3):
                d.set(x1 - 4, y, z, log("spruce_log", "x"))
        for x, z in ((cx - 7, z1 - 5), (cx + 7, z1 - 6), (cx + 8, z2)):
            d.set(x, 2, z, log("spruce_log"))
            d.set(x, 3, z, "moss_carpet")
    if L >= 3:                                                       # split-rail fence and lamp posts
        for z in range(0, z1 - 1):                                    # split rails along the boardwalk,
            if z not in (3, 7, z1 - 3):                                # gaps for the side paths and lamps
                d.set(cx - 3, 2, z, fence("spruce_fence"))
                d.set(cx + 3, 2, z, fence("spruce_fence"))
        for x, z in ((cx - 6, 2), (cx + 6, 2)):
            lamp_post(d, x, z, "cobblestone", log("stripped_spruce_log"))
        for ox, plant in ((-4, "fern"), (-3, "sweet_berry_bush[age=3]"), (-1, "large_fern"), (0, "fern"),
                          (1, "large_fern"), (3, "sweet_berry_bush[age=3]"), (4, "fern")):
            if plant == "large_fern":                                  # undergrowth behind the giant
                d.set(cx + ox, 2, z2 + 3, "large_fern[half=lower]")
                d.set(cx + ox, 3, z2 + 3, "large_fern[half=upper]")
            else:
                d.set(cx + ox, 2, z2 + 3, plant)
    if L >= 4:
        cg_museum(d)
        cg_logdeck(d)
        for x, z in ((3, 6), (2, 44), (40, 44)):
            yew(d, x, z, 2, "spruce_leaves", "spruce_log")
    if L >= 5:
        cg_bunkhouse(d)
        cg_toolstore(d)
        cg_cookhouse(d)
        for x in range(12, 30):                                         # flume / log chute by the path
            d.set(x, 1, 46, "water")
            d.set(x, 2, 47, log("spruce_log", "x"))
        for x, z in ((14, 40), (28, 40), (14, 2), (28, 2)):
            d.chair(x, 2, z, "north", "spruce", sit=False)
        for x, z in ((12, 43), (12, 3)):
            yew(d, x, z, 2, "spruce_leaves", "spruce_log")
    for px in CG_PX:
        d.reserve(px, 1, CG_PZ, px + CG_PW - 1, 30, CG_PZ + CG_PW - 1)
        d.child_hut(px + CG_WHUT[0], 1 + CG_WHUT[1], CG_PZ + CG_WHUT[2], COLO_WING)
    return d


# ---------------------------------------------------------------------------- Neoterra: Beacon
NB_SIZE = (49, 64, 49)
NB_C = (24, 26)
NB_DIM = {1: (4, 4, 4), 2: (5, 5, 5), 3: (7, 7, 6), 4: (9, 9, 7), 5: (11, 11, 8)}
NB_PX, NB_PZ, NB_PW = (9, 35), 8, 5
NB_WHUT = (1, 1, 3)
NB_PT = {1: 6, 2: 9, 3: 13, 4: 17, 5: 22}


def nb_wing(rel, L):
    """Glass light pylon: lobby, chrome-cornered glass shaft with a glowing core, end-rod crown."""
    d = Design("Neoterra", rel, (NB_PW, 34, NB_PW), gy=0, paving="smooth_stone")
    n, T = NB_PW - 1, NB_PT[L]
    d.fill(0, 0, 0, n, 0, n, "polished_diorite")
    d.fill(0, 1, 0, n, 3, n, "light_gray_stained_glass_pane")
    d.clear(1, 1, 1, n - 1, 3, n - 1)
    for x, z in ((0, 0), (n, 0), (0, n), (n, n)):
        d.fill(x, 1, z, x, 3, z, "polished_blackstone")
    d.door(2, 1, 0, "south", "birch")
    d.hut(*NB_WHUT)
    d.set(3, 1, 3, "potted_bamboo")
    d.set(2, 1, 2, "light_blue_carpet")
    d.set(3, 1, 1, "smooth_quartz_stairs[facing=east,half=bottom,shape=straight,waterlogged=false]")
    d.fill(0, 4, 0, n, 4, n, "polished_blackstone")
    for i in range(n + 1):
        d.set(i, 4, 0, "orange_concrete")
    d.set(2, 3, 2, "sea_lantern")
    for y in range(5, T + 1):
        for x in range(1, 4):
            for z in range(1, 4):
                c = x in (1, 3) and z in (1, 3)
                d.set(x, y, z, "iron_block" if c else ("sea_lantern" if (x, z) == (2, 2) else
                                                     "light_blue_stained_glass"))
        if y % 4 == 0:
            for x, z in ((2, 1), (2, 3), (1, 2), (3, 2)):
                d.set(x, y, z, "orange_concrete")
    d.fill(1, T + 1, 1, 3, T + 1, 3, "smooth_quartz_slab[type=bottom,waterlogged=false]")
    d.set(2, T + 1, 2, "beacon" if L >= 4 else "sea_lantern")
    for y in range(T + 2, T + 2 + (2 + L // 2)):
        d.set(2, y, 2, "end_rod[facing=up]")
    for x, z in ((1, 1), (3, 1), (1, 3), (3, 3)):
        d.set(x, T + 2, z, "end_rod[facing=up]")
    return d


def nb_pavilion_shell(d, x1, z1, x2, z2, two=False):
    """Deepslate-clad pavilion structure: orange fins on a glass street front, side windows, cut-copper roof
    edge and canopy, green roof; with two=True a second floor and a stair on the east side. No furniture."""
    d.fill(x1, 1, z1, x2, 1, z2, "polished_diorite")
    top = 10 if two else 5
    d.box(x1, 2, z1, x2, top, z2, "polished_deepslate")
    for x in range(x1 + 1, x2):
        d.window(x, 2, z1, x, 4, z1, "light_gray_stained_glass_pane")
        if two:
            d.window(x, 7, z1, x, 9, z1, "light_gray_stained_glass_pane")
    for x in range(x1, x2 + 1, 3):
        d.fill(x, 2, z1, x, top, z1, "orange_concrete")
    for z in range(z1 + 2, z2 - 1, 3):
        for x in (x1, x2):
            d.window(x, 3, z, x, 4, z, "glass_pane")
    d.fill(x1, top + 1, z1, x2, top + 1, z2, "waxed_cut_copper")
    d.fill(x1 + 1, top + 1, z1 + 1, x2 - 1, top + 1, z2 - 1, "moss_block")
    for x in range(x1 - 1, x2 + 2):
        d.set(x, 6, z1 - 1, slab("waxed_cut_copper_slab", "top"))
    d.double_door((x1 + x2) // 2, 2, z1, "x", "south", "cherry")
    if two:
        d.fill(x1 + 1, 6, z1 + 1, x2 - 1, 6, z2 - 1, "gray_concrete")
        for i in range(4):
            z = z2 - 5 + i
            d.set(x2 - 1, 2 + i, z, stair("smooth_quartz_stairs", "south"))
            if i:
                d.fill(x2 - 1, 2, z, x2 - 1, 1 + i, z, "gray_concrete")
        d.clear(x2 - 1, 6, z2 - 5, x2 - 1, 6, z2 - 2)
        d.set(x2 - 2, 7, z2 - 5, "iron_bars")                        # stair-well railing
        d.set(x2 - 2, 7, z2 - 4, "iron_bars")
        d.set(x2 - 2, 7, z2 - 3, "iron_bars")
    return top


def nb_visitor_centre(d, L):
    """Visitor centre (x1..13, z33..44): information desk inside the door, the statue model in the middle with
    a viewing bench, media wall on the west, souvenir shelves at the back; at L5 an upper gallery with display
    cases and a cafe corner by the glass front."""
    two = L >= 5
    top = nb_pavilion_shell(d, 1, 33, 13, 44, two)
    d.counter(3, 35, 5, 35, 2, body="white_concrete")                # information desk
    d.chair(4, 2, 36, "south", "cherry", sit=False)
    d.set(2, 2, 34, "potted_bamboo")
    d.set(12, 2, 34, "potted_bamboo")
    d.set(7, 2, 39, "white_concrete")                                # statue model
    d.set(7, 3, 39, "white_stained_glass")
    d.chair(6, 2, 37, "north", "cherry", sit=False)
    d.chair(8, 2, 37, "north", "cherry", sit=False)
    d.set(2, 3, 38, "black_stained_glass_pane")                      # media wall
    d.set(2, 3, 39, "black_stained_glass_pane")
    d.set(2, 3, 40, "black_stained_glass_pane")
    d.set(3, 2, 39, "lectern[facing=west,has_book=true,powered=false]")
    d.set(2, 2, 43, "chiseled_bookshelf[facing=south,slot_0_occupied=true,slot_1_occupied=true,"
          "slot_2_occupied=true,slot_3_occupied=false,slot_4_occupied=true,slot_5_occupied=true]")
    d.set(3, 2, 43, "barrel[facing=up,open=false]")
    d.set(4, 2, 43, "chiseled_bookshelf[facing=south,slot_0_occupied=false,slot_1_occupied=true,"
          "slot_2_occupied=true,slot_3_occupied=true,slot_4_occupied=true,slot_5_occupied=false]")
    d.set(5, 2, 43, "decorated_pot[cracked=false,facing=north,waterlogged=false]")
    for x, z in ((4, 38), (7, 36), (10, 39)):
        d.set(x, 5, z, "end_rod[facing=down]")
    d.rug(6, 38, 8, 40, 2, ("cyan_carpet",), "plain")                # mat round the model
    d.chair(6, 2, 41, "south", "cherry", sit=False)
    d.chair(8, 2, 41, "south", "cherry", sit=False)
    d.set(12, 2, 36, cbook("west", 1))                                # brochure racks
    d.set(12, 2, 37, cbook("west", 2))
    d.set(12, 3, 36, "potted_bamboo")
    for x in (9, 10, 11):                                            # visitors' lockers
        d.set(x, 2, 43, "barrel[facing=north,open=false]")
    d.set(12, 2, 43, "potted_bamboo")
    d.set(7, 2, 35, "smooth_quartz_slab[type=top,waterlogged=false]")   # ticket gate posts
    d.set(9, 2, 35, "smooth_quartz_slab[type=top,waterlogged=false]")
    for x, z in ((3, 35), (7, 38), (11, 41), (5, 42)):                # roof garden shrubs
        d.set(x, top + 2, z, "flowering_azalea" if z % 2 else "azalea")
    if two:
        for x in (3, 6, 9):                                          # gallery cases on the back wall
            d.set(x, 7, 43, "white_concrete")
            d.set(x, 8, 43, "white_stained_glass")
        d.dining(4, 7, 36, 1, "x", "cherry", chairs=("n", "s"))
        d.dining(8, 7, 36, 1, "x", "cherry", chairs=("n", "s"))
        d.set(2, 7, 34, "potted_bamboo")
        for x in (3, 7, 11):
            d.set(x, 10, 38, "sea_lantern")


def nb_cafe(d, L):
    """Cafe pavilion (x35..47, z39..47): coffee bar with espresso smoker, sink and cups along the back, three
    tables for two by the windows, plants by the door, pendant lights over the tables."""
    top = nb_pavilion_shell(d, 35, 39, 47, 47)
    d.counter(37, 44, 40, 44, 2, body="white_concrete")
    d.item(37, 2, 46, "smoker", "north")
    d.set(38, 2, 46, "barrel[facing=up,open=false]")
    d.set(39, 2, 46, "water_cauldron[level=3]")
    d.set(40, 2, 46, "crafting_table")
    d.set(38, 3, 46, "decorated_pot[cracked=false,facing=north,waterlogged=false]")
    d.chair(38, 2, 43, "south", "cherry", sit=False)
    d.chair(40, 2, 43, "south", "cherry", sit=False)
    d.dining(37, 2, 41, 1, "x", "cherry", chairs=("n", "s"))
    d.dining(45, 2, 41, 1, "x", "cherry", chairs=("n", "s"))
    d.dining(45, 2, 45, 1, "x", "cherry", chairs=("n", "s"))
    d.set(36, 2, 40, "potted_bamboo")
    d.set(46, 2, 43, "potted_bamboo")
    for x, z in ((37, 41), (45, 41), (45, 45), (39, 45)):
        d.set(x, 5, z, "end_rod[facing=down]")
    for x, z in ((37, 41), (41, 44), (45, 42)):                       # roof garden shrubs
        d.set(x, top + 2, z, "azalea")


def nb_pergola(d, x1, x2, z1, z2, face):
    """Light pergola beside a water mirror: white pillars on both long sides, quartz beams with louvre slabs on
    every other row (open sky between), pendant end-rods; benches facing the water (`face` = side the benches
    look toward), moss planters with azaleas between them."""
    for z in range(z1, z2 + 1, 4):
        for x in (x1, x2):
            d.fill(x, 2, z, x, 5, z, "quartz_pillar")
    for z in range(z1, z2 + 1):
        for x in (x1, x2):
            d.set(x, 6, z, "smooth_quartz")
        if (z - z1) % 2 == 0:
            for x in range(x1 + 1, x2):
                d.set(x, 6, z, slab("smooth_quartz_slab"))
    bx = x2 - 1 if face == "east" else x1 + 1
    px = x1 + 1 if face == "east" else x2 - 1
    for z in range(z1 + 2, z2 - 1, 4):
        d.chair(bx, 2, z, OPP[face], "cherry", sit=False)
        d.chair(bx, 2, z + 1, OPP[face], "cherry", sit=False)
        d.set(px, 1, z, "moss_block")
        d.set(px, 2, z, "flowering_azalea")
        d.set((x1 + x2) // 2, 5, z, "end_rod[facing=down]")
    for z in range(z1 + 4, z2, 4):
        d.set(px, 2, z, "potted_bamboo")


def nb_colossus(rel, L):
    d = Design("Neoterra", rel, NB_SIZE, gy=1, paving="smooth_stone")
    cx, cz = NB_C
    a, b, ph = NB_DIM[L]
    x1, x2, z1, z2 = cx - a, cx + a, cz - b, cz + b
    # patterned plaza: dark/light chevrons
    for x in range(49):
        for z in range(49):
            if (abs(x - cx) + z) % 6 < 2:
                d.set(x, 1, z, "polished_deepslate" if L >= 3 else "light_gray_concrete")
            elif (abs(x - cx) + z) % 6 == 2:
                d.set(x, 1, z, "white_concrete")
    # plinth: blackstone terrace, glass gallery band, quartz deck, orange accent line
    d.box(x1, 2, z1, x2, ph - 1, z2, "polished_blackstone")
    if ph >= 5:
        for x in range(x1 + 1, x2):
            for z in (z1, z2):
                d.window(x, 3, z, x, ph - 2, z, "light_gray_stained_glass_pane")
        for z in range(z1 + 1, z2):
            for x in (x1, x2):
                d.window(x, 3, z, x, ph - 2, z, "light_gray_stained_glass_pane")
        for x in range(x1, x2 + 1, 3):
            for z in (z1, z2):
                d.fill(x, 2, z, x, ph - 1, z, "polished_blackstone")
        for z in range(z1, z2 + 1, 3):
            for x in (x1, x2):
                d.fill(x, 2, z, x, ph - 1, z, "polished_blackstone")
    d.fill(x1, ph, z1, x2, ph, z2, "smooth_quartz")
    for x in range(x1, x2 + 1):
        for z in (z1, z2):
            d.set(x, ph - 1, z, "orange_concrete")
    for z in range(z1, z2 + 1):
        for x in (x1, x2):
            d.set(x, ph - 1, z, "orange_concrete")
    ring_stairs(d, x1 - 1, z1 - 1, x2 + 1, z2 + 1, 2, "polished_blackstone_stairs")
    if L >= 2:
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                if x in (x1, x2) or z in (z1, z2):
                    d.set(x, ph + 1, z, "white_stained_glass_pane")
    nb_hall(d, x1, z1, x2, z2, ph, L)
    d.clear(cx, 2, z1 - 1, cx, 3, z1 - 1)
    d.door(cx, 2, z1, "south", "cherry")
    d.set(cx, 1, z1 - 1, "smooth_quartz")
    d.sign(cx + 1, 3, z1 - 1, "north", ["BEACON"], "cherry", glow=True, color="orange")
    d.hut(22, 2, 23)
    # statue
    H = COLO_H["Neoterra"][L]
    sc, orb = beacon_figure(cx, cz, ph + 1, H)
    sc.commit(d, ph + 1)
    ox, oy, oz, r = orb
    if L >= 3:
        for ddx, ddz, f in ((1, 0, "east"), (-1, 0, "west"), (0, 1, "south"), (0, -1, "north")):
            x, z = int(round(ox + ddx * (r + 1.5))), int(round(oz + ddz * (r + 1.5)))
            d.set(x, int(round(oy)), z, f"end_rod[facing={f}]")             # light rays from the orb
        tp = int(round(oy + r)) + 1
        for y in range(tp, tp + 2):
            if d.bp.inside(int(round(ox)), y, int(round(oz))):
                d.set(int(round(ox)), y, int(round(oz)), "end_rod[facing=up]")
    # approach: light bollards and planters
    bollards = {1: (1, 4, 7, 10, 13, 16, 19), 2: (1, 4, 7, 10, 13, 16, 19), 3: (1, 4, 7, 10, 13, 16)}
    for z in bollards.get(L, (1, 4, 7, 10, 13)):                    # light bollards lining the approach
        for x in (cx - 3, cx + 3):
            d.set(x, 2, z, "smooth_quartz")
            d.set(x, 3, z, "end_rod[facing=up]")
    if L >= 2:
        for x, f in ((cx - 5, "east"), (cx + 5, "west")):           # benches between the planters
            for z in (5, 11):
                d.chair(x, 2, z, OPP[f], "smooth_quartz", sit=False)
                d.set(x, 2, z + 1, "smooth_quartz")
                d.set(x, 3, z + 1, "end_rod[facing=up]")
        for z in ((2, 8) if L == 5 else (2, 8, 14)):                 # planters with bamboo pots
            for x in (cx - 5, cx + 5):
                d.set(x, 1, z, "moss_block")
                d.set(x, 2, z, "flowering_azalea")
                d.set(x, 2, z + 1, "potted_bamboo")
    if L >= 3:                                                       # water mirrors left and right
        for x0 in (x1 - 6, x2 + 3):
            for x in range(x0, x0 + 4):
                for z in range(z1, z2 + 1):
                    if 0 <= x < 49:
                        d.set(x, 1, z, "water")
                        d.set(x, 0, z, "light_blue_concrete")
            for z in range(z1 - 1, z2 + 2):
                for x in (x0 - 1, x0 + 4):
                    if 0 <= x < 49:
                        d.set(x, 1, z, "smooth_quartz")
    if L >= 4:
        nb_visitor_centre(d, L)
        for x in (36, 41, 46):                                       # sculpture garden
            d.set(x, 1, 36, "moss_block")
            d.set(x, 2, 36, "polished_blackstone")
            d.set(x, 3, 36, "waxed_copper_block" if x % 2 else "orange_concrete")
            d.set(x, 4, 36, "end_rod[facing=up]")
    if L >= 5:
        nb_cafe(d, L)
        nb_pergola(d, 1, 5, 15, 31, "east")
        nb_pergola(d, 43, 47, 15, 31, "west")
        for x, z in ((20, 46), (28, 46)):
            cherry_tree(d, x, z)
        for x, z in ((16, 6), (32, 6), (16, 12), (32, 12)):
            d.chair(x, 2, z, "west" if x < cx else "east", "cherry", sit=False)
    for px in NB_PX:
        d.reserve(px, 1, NB_PZ, px + NB_PW - 1, 34, NB_PZ + NB_PW - 1)
        d.child_hut(px + NB_WHUT[0], 1 + NB_WHUT[1], NB_PZ + NB_WHUT[2], COLO_WING)
    return d



# ------------------------------------------------------------------------------------------------ materials
# Early levels are built from common materials; quartz, blackstone, sea lanterns, end rods and metal blocks arrive
# with the L4-5 upgrade. Same shapes, cheaper stone: the building visibly "goes premium" when it grows.
COMMON = {
    "quartz_pillar": "white_concrete", "smooth_quartz": "white_concrete", "quartz_block": "white_concrete",
    "chiseled_quartz_block": "chiseled_stone_bricks",
    "smooth_quartz_slab": "smooth_stone_slab", "smooth_quartz_stairs": "polished_diorite_stairs",
    "sea_lantern": "glowstone", "iron_block": "light_gray_concrete", "gold_block": "yellow_concrete",
    "polished_blackstone": "polished_deepslate", "polished_blackstone_stairs": "polished_deepslate_stairs",
    "polished_blackstone_slab": "polished_deepslate_slab", "polished_blackstone_wall": "polished_deepslate_wall",
    "oxidized_copper": "green_terracotta", "oxidized_cut_copper": "green_terracotta",
}


def common_materials(d):
    """Swap premium blocks for their common counterparts (keeping stair/slab shapes); end rods become
    lightning-rod posts. Used for Neoterra levels 1-3."""
    from blueprint import parse_state
    for x, y, z, st in list(d.bp.blocks()):
        name, props = parse_state(st)
        n = name.split(":")[1]
        if n == "end_rod":
            d.bp.set(x, y, z, f"minecraft:lightning_rod[facing={props.get('facing', 'up')},powered=false,"
                     "waterlogged=false]")
            continue
        new = COMMON.get(n)
        if new is None:
            continue
        keep = any(k in new for k in ("_stairs", "_slab", "_wall"))
        if keep and props:
            d.bp.set(x, y, z, "minecraft:" + new + "[" + ",".join(f"{k}={v}" for k, v in props.items()) + "]")
        else:
            d.bp.set(x, y, z, "minecraft:" + new, d.bp.tile_entities.get((x, y, z)))
    return d


def _early(pack, L, d):
    return common_materials(d) if pack == "Neoterra" and L <= 3 else d


# ------------------------------------------------------------------------------------------------ registry
CATHEDRAL = {"Hearthwood": hc_cathedral, "Cascadia": cc_cathedral, "Neoterra": nc_cathedral}
CATHEDRAL_WING = {"Hearthwood": hc_wing, "Cascadia": cc_wing, "Neoterra": nc_wing}
COLOSSUS = {"Hearthwood": hk_colossus, "Cascadia": cg_colossus, "Neoterra": nb_colossus}
COLOSSUS_WING = {"Hearthwood": hk_wing, "Cascadia": cg_wing, "Neoterra": nb_wing}


@design("cathedral")
def cathedral(pack, rel, L):
    return _early(pack, L, CATHEDRAL[pack](rel, L))


@design("cathedralwing")
def cathedralwing(pack, rel, L):
    return _early(pack, L, CATHEDRAL_WING[pack](rel, L))


@design("colossus")
def colossus(pack, rel, L):
    return _early(pack, L, COLOSSUS[pack](rel, L))


@design("colossuswing")
def colossuswing(pack, rel, L):
    return _early(pack, L, COLOSSUS_WING[pack](rel, L))
