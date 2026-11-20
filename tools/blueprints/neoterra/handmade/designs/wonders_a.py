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
    for z in range(0, ne + 1 if not cross else ne + 1):
        for x, f in ((10, "east"), (20, "west")):
            if d.air(x, NH, z):
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
    pz = list(range(4, ne - 2, 2)) if not cross else list(range(5, 17, 2))
    pews(d, 12, 14, pz, 2, "dark_oak")
    pews(d, 16, 18, pz, 2, "dark_oak")
    for z in range(5, ne - 1, 4):
        chandelier(d, 15, z, rdg - 1, NH - 3 if L == 1 else 11)
    for z in range(4, ne - 1, 3):                        # wall candles / banners between the windows
        for x, f in ((12, "east"), (18, "west")):
            if L >= 2 and d.air(x, 5, z):
                d.set(x, 5, z, f"wall_torch[facing={f}]" if z % 2 else f"red_wall_banner[facing={f}]")
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
        stamp(d, hc_palace, 21, 1, L)
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
    d.fill(cx - 1, 5, cz - 1, cx + 1, 5, cz + 1, slab("dark_oak_slab"))
    d.set(cx, 4, cz, "chain[axis=y,waterlogged=false]")
    for x, z in ((a1 + 2, b1 + 2), (a2 - 2, b1 + 2), (a1 + 2, b2 - 2), (a2 - 2, b2 - 2)):
        d.set(x, 2, z, "rose_bush[half=lower]")
        d.set(x, 3, z, "rose_bush[half=upper]")
    for x in range(a1 + 1, a2):
        for z in (b1 + 1, b2 - 1):
            if d.air(x, 2, z) and d.get(x, 1, z).endswith("grass_block") and x != cx:
                d.set(x, 2, z, "allium" if x % 2 else "lily_of_the_valley")
    # walks: carrels (lectern + stool) on the north walk, benches on the others, lanterns
    for x in range(x1 + 2, x2 - 1, 3):
        d.set(x, 2, z1 + 1, "lectern[facing=south,has_book=true,powered=false]")
    for z in range(z1 + 3, z2 - 2, 3):
        d.chair(x2 - 1, 2, z, "east", "dark_oak")
    for x in range(x1 + 3, x2 - 2, 4):
        d.chair(x, 2, z2 - 1, "south", "dark_oak")
    for x in range(x1 + 2, x2 - 1, 4):
        for z in (z1 + 2, z2 - 2):
            d.set(x, 6, z, lantern(True))
    for z in range(z1 + 4, z2 - 3, 4):
        d.set(x1 + 2, 6, z, lantern(True))
        d.set(x2 - 2, 6, z, lantern(True))
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
    for z in range(33, 42, 2):
        for x, f in ((10, "east"), (20, "west")):
            pass
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
    for z in range(33, 38, 2):
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
                d.set(cx + dx, 11, cz + dz, stair("stone_brick_stairs", "north", "top") if False else S)
            elif not _oct(dx, dz, r - 2):                           # bench ring
                ex = [s2 for s2, (ox, oz) in D4.items() if not _oct(dx + ox, dz + oz, r - 1)]
                if ex and abs(dx) + abs(dz) != 0:
                    d.chair(cx + dx, 2, cz + dz, ex[0], "stone_brick")
    for dx, dz in ((0, -5), (0, 5), (-5, 0), (5, 0), (-3, -4), (3, -4), (-3, 4), (3, 4),
                   (-4, -3), (4, -3), (-4, 3), (4, 3)):
        if _oct(dx, dz, r) and not _oct(dx, dz, r - 1) and (dx, dz) != (0, -5):
            lancet(d, cx + dx, cz + dz, 4, 9)
    for y in range(2, 12):                                          # central pier
        d.set(cx, y, cz, "polished_andesite" if y < 11 else "chiseled_stone_bricks")
    for ox, oz in D4.values():
        d.set(cx + ox, 8, cz + oz, lantern(True) if False else "lantern[hanging=false,waterlogged=false]") \
            if False else d.set(cx + ox, 7, cz + oz, lantern(True))
        d.set(cx + ox, 8, cz + oz, stair("stone_brick_stairs", {(1, 0): "west", (-1, 0): "east", (0, 1): "north",
                                                                 (0, -1): "south"}[(ox, oz)], "top"))
    d.set(cx, 2, cz - 2, "lectern[facing=north,has_book=true,powered=false]")
    d.fill(cx - r, 11, cz - r, cx + r, 11, cz + r, AIR)
    for dx in range(-r, r + 1):
        for dz in range(-r, r + 1):
            if _oct(dx, dz, r):
                d.set(cx + dx, 11, cz + dz, S if not _oct(dx, dz, r - 1) else "dark_oak_planks")
    spire(d, cx, cz, 12, 5, "deepslate_tiles", "deepslate_tile_stairs", step=2, needle=2,
          broach=False, top="lightning_rod[facing=up,powered=false,waterlogged=false]")
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


def hc_palace(d, L):
    """Bishop's palace: stone ground floor (hall + kitchen), timber-framed jettied upper floor (study and
    chamber), tiled gable with a brick chimney."""
    S = "stone_bricks"
    x1, z1, x2, z2 = 1, 29, 8, 41
    d.fill(x1, 1, z1, x2, 1, z2, "spruce_planks")
    d.box(x1, 2, z1, x2, 5, z2, S, floor=None)
    for z in range(z1, z2 + 1):
        for x in (x1, x2):
            d.set(x, 2, z, "polished_andesite")
    d.fill(x1, 6, z1, x2, 6, z2, "dark_oak_planks")
    d.box(x1, 7, z1, x2, 10, z2, "calcite")
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
    # windows with shutters and boxes
    for z in range(z1 + 2, z2 - 1, 3):
        for x, f in ((x1, "west"), (x2, "east")):
            d.window(x, 3, z, x, 4, z)
            d.window(x, 8, z, x, 9, z)
            ox, oz = D4[f]
            if d.bp.inside(x + ox, 2, z + oz) and x + ox >= 0:
                d.set(x + ox, 8, z + oz, trap("spruce_trapdoor", f, "top"))
                if x + ox != 9:
                    d.set(x + ox, 7, z + oz, "potted_red_tulip") if False else None
    rd = d.gable(x1, z1, x2, z2, 11, "z", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite", 1)
    # door on the north gable with a hood
    d.door(4, 2, z1, "south", "dark_oak")
    d.set(4, 4, z1, S)
    d.set(3, 5, z1 - 1, stair("deepslate_tile_stairs", "east"))
    d.set(4, 5, z1 - 1, slab("deepslate_tile_slab"))
    d.set(5, 5, z1 - 1, stair("deepslate_tile_stairs", "west"))
    d.set(4, 4, z1 - 1, lantern(True))
    d.sign(5, 3, z1 - 1, "north", ["Bishop's", "Palace"], "dark_oak")
    # chimney + hearth in the hall
    d.hearth(x1 + 1, 2, 35, "east", rd + 3, "bricks", "campfire")
    for y in range(6, rd + 3):
        d.set(x1, y, 35, "bricks")
    d.set(x1, rd + 3, 35, slab("brick_slab"))
    # ground floor: great hall with a long table, kitchen at the back
    d.dining(4, 2, 32, 5, "z", "dark_oak", chairs=("e", "w"), sit=True)
    d.rug(3, 31, 7, 31, 2, ("red_carpet",), "plain")
    for x in (3, 6):
        d.lamp(x, 5, 34)
    d.item(7, 2, 40, "furnace", "west")
    d.item(7, 2, 39, "smoker", "west")
    d.set(7, 2, 38, "barrel[facing=up,open=false]")
    d.set(2, 2, 40, "crafting_table")
    d.set(3, 2, 40, "cauldron")
    d.set(2, 4, 40, "decorated_pot[cracked=false,facing=north,waterlogged=false]") if False else None
    d.set(7, 3, 40, "decorated_pot[cracked=false,facing=west,waterlogged=false]")
    # stair up along the east wall
    for i, y in enumerate(range(2, 6)):
        d.set(7, y, 30 + i, stair("dark_oak_stairs", "south"))
        if y > 2:
            d.fill(7, 2, 30 + i, 7, y - 1, 30 + i, "dark_oak_planks")
    d.clear(7, 6, 30, 7, 6, 34)
    d.set(6, 7, 30, fence("dark_oak_fence"))
    # upper floor: study (books) and chamber (bed)
    for z in range(31, 35):
        d.set(2, 7, z, "bookshelf")
        d.set(2, 8, z, "chiseled_bookshelf[facing=east,slot_0_occupied=true,slot_1_occupied=false,"
              "slot_2_occupied=true,slot_3_occupied=true,slot_4_occupied=false,slot_5_occupied=true]")
    d.set(4, 7, 33, "lectern[facing=east,has_book=true,powered=false]")
    d.chair(4, 7, 35, "south", "dark_oak")
    d.set(4, 7, 36, slab("dark_oak_slab", "top"))
    d.candle(4, 8, 36, 2)
    d.fill(2, 7, 37, 7, 9, 37, "dark_oak_planks")
    d.door(5, 7, 37, "south", "dark_oak")
    d.bed(3, 7, 40, "south", "purple")
    d.set(2, 7, 40, slab("dark_oak_slab", "top"))
    d.candle(2, 8, 40, 1)
    d.set(6, 7, 40, "barrel[facing=up,open=false]")
    d.rug(3, 38, 6, 39, 7, ("purple_carpet",), "plain")
    for z in (33, 39):
        d.lamp(4, 10, z)
    # garden: hedge and benches
    for z in range(29, 42):
        if d.air(0, 2, z):
            d.set(0, 2, z, "oak_leaves[distance=1,persistent=true,waterlogged=false]")


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
    for z in range(z1 + 1, z2):                                    # bookcases + desks alternate
        if z % 2 == 0:
            d.set(x1 + 1, 9, z, "bookshelf")
            d.set(x1 + 1, 10, z, "chiseled_bookshelf[facing=east,slot_0_occupied=true,slot_1_occupied=true,"
                  "slot_2_occupied=false,slot_3_occupied=true,slot_4_occupied=true,slot_5_occupied=false]")
        else:
            d.set(x1 + 1, 9, z, "lectern[facing=east,has_book=true,powered=false]") if z % 4 == 1 else \
                d.chair(x1 + 1, 9, z, "west", "dark_oak")
    for z in range(z1 + 2, z2 - 1, 4):
        d.lamp(x1 + 2, 13, z)
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
    d.set(46, 11, 11, lantern(True)) if False else d.set(46, 9, 12, "lantern[hanging=false,waterlogged=false]")


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
    for z in range(9, 17, 2):
        for x in (3,):
            d.set(x, 2, z, "mossy_stone_bricks")
            d.set(x, 3, z, slab("mossy_stone_brick_slab"))
            d.set(x, 1, z + 1, "podzol")
    for x, z in ((36, 35), (36, 38), (39, 41), (42, 35), (42, 38)):
        d.set(x, 2, z, "cobblestone_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
        d.set(x, 1, z + 1, "podzol")
    for x, z in ((10, 0), (20, 0), (27, 0), (46, 0), (46, 20), (30, 29)):
        d.set(x, 2, z, wallb("stone_brick_wall"))
        d.set(x, 3, z, fence("dark_oak_fence"))
        d.set(x, 4, z, "lantern[hanging=false,waterlogged=false]")
    for x in (8, 22):
        d.chair(x, 2, 0, "north", "dark_oak")
    # churchyard wall with coping along the street and the east side, lych-gate on the street
    for x in range(28, 48):
        if 35 <= x <= 37:
            continue
        d.set(x, 2, 0, "mossy_stone_bricks" if x % 3 == 0 else "stone_bricks")
        d.set(x, 3, 0, slab("stone_brick_slab"))
    for z in range(21, 44):
        if d.air(47, 2, z):
            d.set(47, 2, z, "mossy_stone_bricks" if z % 3 == 0 else "stone_bricks")
            d.set(47, 3, z, slab("stone_brick_slab"))
    for x in (34, 38):
        d.fill(x, 2, 0, x, 4, 0, log("dark_oak_log"))
    for x in range(33, 40):
        d.set(x, 5, 0, stair("deepslate_tile_stairs", "south") if False else slab("deepslate_tile_slab"))
    d.fill(34, 5, 0, 38, 5, 0, log("dark_oak_log", "x"))
    for x in range(33, 40):
        d.set(x, 6, 0, slab("deepslate_tile_slab"))
    d.set(36, 7, 0, wallb("stone_brick_wall"))
    for x in range(35, 38):
        d.set(x, 1, 0, "gravel")
    # gargoyles under the nave cornice
    for z in range(9, 17, 3):
        d.set(10, 15, z, stair("stone_brick_stairs", "east", "top"))
        d.set(20, 15, z, stair("stone_brick_stairs", "west", "top"))
    # gravel paths
    for x in range(26, 48):
        d.set(x, 1, 18, "gravel")
    for z in range(17, 30):
        d.set(30, 1, z, "gravel")


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
    """Log building with a river-rock footing, notched corners, steep shingled gable (ridge along z), a covered
    porch on the north door, stone chimney on the south gable, shuttered windows with flower boxes.
    kind: 'parsonage' (living room, kitchen, bedroom), 'hall' (parish hall: long tables, stage, hearth),
    'store' (stabbur-like storehouse on stone piers)."""
    x2, z2 = x1 + w - 1, z1 + l - 1
    R, RB, RS, LG, LG2, WD, TRIM, ACC = CC_PAL[pal or kind]
    fy = 2 if kind == "store" else 1                                # floor level (store sits on piers)
    if kind == "store":
        for x in range(x1, x2 + 1, w - 1):
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
                    d.set(x, y + 0, z, "cobblestone" if (x + z) % 3 else "mossy_cobblestone")
                    continue
                corner = x in (x1, x2) and z in (z1, z2)
                ax = "x" if z in (z1, z2) else "z"
                if corner:
                    ax = "x" if y % 2 else "z"
                if corner:
                    d.set(x, y, z, log(LG2 if y % 2 else LG, ax))
                elif ACC and y == top:
                    d.set(x, y, z, ACC)
                else:
                    d.set(x, y, z, log(LG, ax) if (y + (0 if ax == "x" else 1)) % 2 else log(LG2, ax))
    if kind != "store":
        d.fill(x1 + 1, 1, z1 + 1, x2 - 1, 1, z2 - 1, "spruce_planks")
    # windows with shutters and flower boxes
    wy = fy + 2
    for z in range(z1 + 2, z2 - 1, 3):
        for x, f in ((x1, "west"), (x2, "east")):
            d.window(x, wy, z, x, wy + 1, z)
            ox = -1 if f == "west" else 1
            if d.bp.inside(x + ox, wy, z) and d.air(x + ox, wy, z):
                for dz in (-1, 1):
                    if d.air(x + ox, wy, z + dz) and d.air(x + ox, wy + 1, z + dz):
                        d.set(x + ox, wy, z + dz, trap(f"{WD}_trapdoor", f, "bottom", True))
                        d.set(x + ox, wy + 1, z + dz, trap(f"{WD}_trapdoor", f, "bottom", True))
                d.set(x + ox, wy - 1, z, trap(f"{WD}_trapdoor", f, "top"))
                d.set(x + ox, wy, z, "potted_red_tulip" if z % 2 else "potted_cornflower")
    # door + porch on the north side
    dx = (x1 + x2) // 2
    d.door(dx, fy + 1, z1, "south", WD)
    if kind == "store":
        d.set(dx, 2, z1 - 1, stair("spruce_stairs", "south"))
    else:
        d.fill(x1, 1, z1 - 2, x2, 1, z1 - 1, "spruce_planks")
        for x in (x1, x2):
            d.fill(x, 2, z1 - 2, x, top - 1, z1 - 2, log(TRIM))
        for x in range(x1 + 1, x2):
            if x != dx:
                d.set(x, 2, z1 - 2, fence("spruce_fence"))
        for x in range(x1 - 1, x2 + 2):
            d.set(x, top, z1 - 2, stair(R, "south"))
            d.set(x, top, z1 - 1, RB)
        d.set(dx - 1, top - 1, z1 - 1, lantern(True))
        d.chair(x1 + 1, 2, z1 - 1, "north", "spruce", sit=False)
        d.set(x2 - 1, 2, z1 - 1, "barrel[facing=up,open=false]")
    if w <= 9:
        rd = steep_gable(d, x1, z1, x2, z2, top + 1, R, RB, log(LG, "x"), "z", 1)
    else:
        rd = d.gable(x1, z1, x2, z2, top + 1, "z", R, RS, log(LG, "x"), 1)
    for z in range(z1 - 1, z2 + 2):                                 # ridge cap
        if w % 2 == 1 and w > 9:
            d.set(dx, rd, z, RB)
            d.set(dx, rd + 1, z, slab(RS))
    for zz in (z1, z2):                                             # gable king post + finial
        for y in range(top + 1, rd):
            if not d.get(dx, y, zz).endswith("air"):
                d.set(dx, y, zz, log(TRIM))
    d.set(dx, rd + (2 if w > 9 else 1), z1 - 1, fence("spruce_fence")) if d.air(dx, rd + 1, z1 - 1) else None
    # chimney on the south gable
    if kind != "store":
        for y in range(1, rd + 2):
            d.set(dx, y, z2 + 1, "cobblestone" if y % 3 else "mossy_cobblestone")
        d.set(dx, rd + 2, z2 + 1, "campfire[facing=north,lit=false,signal_fire=false,waterlogged=false]")
        d.hearth(dx, fy + 1, z2 - 1, "north", fy + 4, "cobblestone", "campfire")
        for y in range(fy + 4, top + 1):
            d.set(dx, y, z2 - 1, AIR)
    y = fy + 1
    # interiors
    if kind == "parsonage":
        d.dining(x1 + 2, y, z1 + 3, 2, "z", "spruce", chairs=("e", "w"))
        d.rug(x1 + 1, z1 + 2, x1 + 4, z1 + 5, y, ("green_carpet", "brown_carpet"))
        d.set(x2 - 1, y, z1 + 1, "crafting_table")
        d.item(x2 - 1, y, z1 + 2, "furnace", "west")
        d.set(x2 - 1, y, z1 + 3, "barrel[facing=up,open=false]")
        d.set(x2 - 1, y + 1, z1 + 3, "decorated_pot[cracked=false,facing=west,waterlogged=false]")
        d.bed(x1 + 1, y, z2 - 1, "south", "green")
        d.set(x1 + 2, y, z2 - 1, slab("spruce_slab", "top"))
        d.candle(x1 + 2, y + 1, z2 - 1, 2)
        d.set(x2 - 1, y, z2 - 2, "bookshelf")
        d.set(x2 - 1, y + 1, z2 - 2, "bookshelf")
        d.set(x2 - 1, y, z2 - 3, "lectern[facing=west,has_book=true,powered=false]")
        d.chair(dx - 1, y, z2 - 3, "west", "spruce", sit=False)
        for z in range(z1 + 2, z2, 4):
            d.lamp(dx, top, z)
    elif kind == "hall":
        for xx in (x1 + 2, x2 - 2):
            d.dining(xx, y, z1 + 3, l - 7, "z", "spruce", chairs=("e", "w"))
        d.fill(x1 + 1, y, z2 - 3, x2 - 1, y, z2 - 2, slab("spruce_slab", "top"))          # stage
        d.set(x1 + 1, y + 1, z2 - 2, "note_block[instrument=harp,note=0,powered=false]")
        d.set(x2 - 1, y + 1, z2 - 2, "jukebox[has_record=false]")
        for xx in range(x1 + 1, x2):
            d.set(xx, top - 1, z2 - 1, "red_wall_banner[facing=north]" if xx % 2 else "white_wall_banner[facing=north]")
        for z in range(z1 + 3, z2 - 3, 4):
            chandelier(d, dx, z, rd - 2, top - 1)
        d.set(x1 + 1, y, z1 + 1, "barrel[facing=up,open=false]")
        d.set(x2 - 1, y, z1 + 1, "barrel[facing=up,open=false]")
        d.set(x1 + 1, y + 1, z1 + 1, "potted_fern")
    elif kind == "lodge":
        fy2 = fy + 5
        d.fill(x1 + 1, fy2, z1 + 1, x2 - 1, fy2, z2 - 1, "spruce_planks")
        for i in range(4):                                           # stair up along the west wall
            zz = z1 + 2 + i
            d.set(x1 + 1, y + i, zz, stair("spruce_stairs", "south"))
            if i:
                d.fill(x1 + 1, y, zz, x1 + 1, y + i - 1, zz, "spruce_planks")
        d.clear(x1 + 1, fy2, z1 + 2, x1 + 1, fy2, z1 + 6)
        d.set(x1 + 1, fy2, z1 + 6, "spruce_planks")
        d.clear(x1 + 1, fy2, z1 + 3, x1 + 1, fy2, z1 + 5)
        d.dining(dx, y, z1 + 3, l - 6, "z", "spruce", chairs=("e", "w"))
        d.set(x2 - 1, y, z1 + 1, "barrel[facing=up,open=false]")
        d.set(x2 - 1, y, z1 + 2, "crafting_table")
        d.item(x2 - 1, y, z1 + 3, "smoker", "west")
        d.set(x2 - 1, y, z1 + 4, "barrel[facing=up,open=false]")
        for z in range(z1 + 3, z2 - 1, 3):
            d.lamp(dx + 2, fy2 - 1, z)
        u = fy2 + 1                                                  # dormitory
        for z in range(z1 + 2, z2 - 1, 2):
            d.bed(x2 - 1, u, z, "east", "brown")
        for z in range(z1 + 8, z2 - 1, 2):
            d.bed(x1 + 1, u, z, "west", "green")
        d.rug(dx - 1, z1 + 2, dx + 1, z2 - 2, u, ("brown_carpet", "green_carpet"))
        for z in range(z1 + 3, z2 - 1, 4):
            d.lamp(dx, top, z)
        d.set(dx, u, z1 + 1, "barrel[facing=up,open=false]")
    elif kind == "store":
        for z in range(z1 + 1, z2):
            d.set(x1 + 1, y, z, "barrel[facing=up,open=false]" if z % 2 else "hay_block[axis=y]")
            d.set(x2 - 1, y, z, "barrel[facing=east,open=false]" if z % 2 else "white_wool")
        d.set(x1 + 1, y + 1, z1 + 2, "barrel[facing=up,open=false]")
        d.lamp(dx, top, (z1 + z2) // 2)
    return rd


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
    for x in range(44, 47):
        for z in range(20, 30, 2):
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
                    d.set(x + ox, 6, z, stair("spruce_stairs", OPP[f], "top") if False else
                          trap("spruce_trapdoor", f, "top"))
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
    d.rug(13, 12, 13, 22 if L >= 3 else zE - 3, 2, ("red_carpet",), "plain")
    pz = [14, 16, 18, 20] if L >= 3 else ([14, 16, 18] if L == 2 else [14, 16])
    pews(d, 10, 12, pz, 2, "spruce")
    pews(d, 14, 16, pz, 2, "spruce")
    for z in (14, 18, 22):
        if z < zE - 1:
            chandelier(d, 13, z, nr - 3, WT - 3)
    for z in range(13, zE - 1, 4):                 # wall lamps and hymn boards
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
        cc_log_house(d, 30, 4, 8, 11, "parsonage")
        for x in range(15, 30):
            d.set(x, 1, 3 if x < 34 else 3, "gravel") if False else d.set(x, 1, 2, "gravel")
    if L >= 4:
        cc_log_house(d, 29, 19, 15, 13, "hall", H=7)
        for z in range(2, 18):
            d.set(36, 1, z, "gravel") if z < 2 else None
        for z in range(15, 19):
            d.set(36, 1, z, "gravel")
    if L >= 3:
        cc_log_house(d, 40, 4, 5, 7, "store", H=4)
    if L >= 4:
        cc_yard(d, L)
        cc_lychgate(d, 11, 1, 15)
        for x in list(range(0, 10)) + list(range(17, 46)):
            if d.air(x, 2, 0) and not (0 <= x <= 6 or 20 <= x <= 26):
                d.set(x, 2, 0, fence("spruce_fence"))
    if L >= 5:
        cc_log_house(d, 2, 31, 9, 9, "parsonage", pal="cabin_birch")      # sexton's cabin
        cc_log_house(d, 16, 32, 9, 9, "parsonage", pal="cabin_red")       # verger's cabin
        for z in range(8, 29):                                              # graveyard rail fences
            for x in (0, 27):
                if d.air(x, 2, z) and z != 18:
                    d.set(x, 2, z, fence("spruce_fence"))
        for x1, z1 in ((2, 31), (16, 32)):                                  # front gardens and lamp posts
            for x in range(x1, x1 + 9):
                if x != x1 + 4 and d.air(x, 2, z1 - 3):
                    d.set(x, 1, z1 - 3, "podzol" if False else "coarse_dirt")
                    d.set(x, 2, z1 - 3, ("poppy", "cornflower", "oxeye_daisy", "allium")[x % 4])
            d.set(x1 + 4, 1, z1 - 3, "gravel")
            for x in (x1 - 1, x1 + 9):
                if d.air(x, 2, z1 - 3):
                    d.set(x, 2, z1 - 3, log("stripped_spruce_log"))
                    d.set(x, 3, z1 - 3, fence("spruce_fence"))
                    d.set(x, 4, z1 - 3, lantern(False))
        cc_log_house(d, 30, 36, 13, 11, "lodge", H=9)            # pilgrims' lodge, dormitory upstairs
        cc_log_house(d, 0, 41, 5, 6, "store", H=4)                 # smokehouse / woodshed
        for z in range(32, 36):
            d.set(36, 1, z, "gravel")
        for x, z in ((27, 36), (44, 36), (44, 14), (27, 13)):
            yew(d, x, z, 2, "spruce_leaves", "spruce_log")
        for x in range(0, 30, 4):
            if d.air(x, 2, 44):
                d.set(x, 2, 44, log("stripped_spruce_log"))
                d.set(x, 3, 44, lantern(False))
    for tx in CC_TX:
        d.reserve(tx, 1, CC_TZ, tx + CC_TW - 1, 40, CC_TZ + CC_TW - 1)
        d.child_hut(tx + CC_WHUT[0], 1 + CC_WHUT[1], CC_TZ + CC_WHUT[2], CATH_WING)
    return d



# ---------------------------------------------------------------------------- Neoterra: crown cathedral
NC_SIZE = (51, 44, 42)
NC_C = (16, 18)                                 # centre of the crown
NC_TX, NC_TZ, NC_TW = (1, 27), 1, 5            # campanile (wings)
NC_WHUT = (1, 1, 3)
NC_H = {1: 9, 2: 13, 3: 18, 4: 23, 5: 31}       # rib height
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
    for xx in range(x1 + 2, x2 - 1, 3):
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
        for x in range(x1 + 2, x2 - 1, 4):                          # planters on the flat roof
            d.set(x, 7, z1 + 2, "moss_block")
            d.set(x, 8, z1 + 2, "azalea")
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
    for xx in range(x1 + 3, x2 - 1, 3):
        for zz in (15, 17):
            d.chair(xx, 7, zz, "south", "birch", sit=False)
            d.set(xx, 7, zz - 1, slab("birch_slab", "top"))
    d.set(43, 7, 19, "lectern[facing=north,has_book=true,powered=false]")
    for xx in range(x1 + 2, x2 - 1, 4):
        for zz in (9, 16):
            d.set(xx, 10, zz, "sea_lantern")
    # roof terrace: green roof, planters, solar panels
    for x in range(x1 + 1, x2):
        for z in range(z1 + 1, z2):
            if (x + z) % 5 == 0:
                d.set(x, 11, z, "moss_block")
                d.set(x, 12, z, "flowering_azalea" if x % 2 else "azalea")
    for x in range(x1 + 2, x2 - 1, 3):
        d.set(x, 12, z2 - 2, "daylight_detector[inverted=false,power=0]")
        d.set(x + 1, 12, z2 - 2, "daylight_detector[inverted=false,power=0]")


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
    for x in range(x1 + 2, x2 - 1, 3):
        for z in range(z1 + 2, z2 - 1, 3):
            d.set(x, 11, z, "azalea")
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
    for x in (x1 + 1, x2 - 1):
        for z in range(z1 + 2, z2 - 1, 2):
            d.chair(x, 2, z, "west" if x == x1 + 1 else "east", "cherry", sit=False)
    d.double_door(cx - 1, 2, z1, "x", "south", "cherry")
    # canopy walk from the cathedral's east side
    for x in range(30, x1):
        d.set(x, 1, cz - 3, "smooth_quartz")
        d.set(x, 1, cz - 2, "smooth_quartz")
    for x in range(28, x1 + 1):
        for z in (cz - 4, cz - 3, cz - 2, cz - 1):
            if d.air(x, 6, z):
                d.set(x, 6, z, slab("smooth_quartz_slab", "top"))
        if x % 3 == 0:
            for z in (cz - 4, cz - 1):
                if d.air(x, 2, z):
                    d.fill(x, 2, z, x, 5, z, "white_concrete")
    for x in range(cx - 1, cx + 1):
        pass


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
    rows = [r for r in (4.5, 6.5, 8.5, 10.5) if r < Rb - 1.8]
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
    d.rug(cx, zf + 1, cx, cz - 3, 2, ("light_blue_carpet",), "plain")
    d.hut(14, 2, 13)
    # hanging lights: rings of lights on chains from the glass roof
    for a in range(0, 360, 90 if L < 4 else 45):
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
    if L >= 4:
        nc_parish_centre(d, L)
    if L >= 5:
        nc_baptistery(d, L)
        for x, z in ((33, 2), (33, 24), (48, 24), (48, 40), (2, 38), (10, 40), (22, 40)):
            if d.air(x, 2, z):
                d.set(x, 1, z, "moss_block")
                d.set(x, 2, z, log("cherry_log"))
                d.set(x, 3, z, log("cherry_log"))
                for ddx in (-1, 0, 1):
                    for ddz in (-1, 0, 1):
                        for yy in (4, 5):
                            if d.bp.inside(x + ddx, yy, z + ddz) and d.air(x + ddx, yy, z + ddz) \
                                    and not (yy == 5 and ddx and ddz):
                                d.set(x + ddx, yy, z + ddz,
                                      "cherry_leaves[distance=1,persistent=true,waterlogged=false]")
        for z in range(24, 41, 4):                                   # benches along the garden walk
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


def colossus_hall(d, x1, z1, x2, z2, ph, floor, wood, banner, L):
    """Foundation hall filling the plinth: rug walk, model of the statue, lecterns, benches, banners, lights."""
    cx = (x1 + x2) // 2
    d.fill(x1 + 1, 1, z1 + 1, x2 - 1, 1, z2 - 1, floor)
    d.rug(cx, z1 + 1, cx, z2 - 2, 2, ("red_carpet",) if banner == "red" else (f"{banner}_carpet",), "plain")
    d.set(cx, 2, z2 - 1, "chiseled_quartz_block" if L < 3 else "gold_block")         # model on a pedestal
    d.set(cx - 1, 2, z2 - 1, "lectern[facing=north,has_book=true,powered=false]")
    d.set(cx + 1, 2, z2 - 1, "lectern[facing=north,has_book=true,powered=false]")
    d.candle(cx, 3, z2 - 1, 3)
    for z in range(z1 + 2, z2 - 1, 3):
        for x, f in ((x1 + 1, "east"), (x2 - 1, "west")):
            d.set(x, 3 if ph > 4 else 2, z, f"{banner}_wall_banner[facing={f}]") if ph > 4 else None
    for z in range(z1 + 3, z2 - 1, 4):
        if x2 - x1 >= 8:
            d.chair(cx - 2, 2, z, "west", wood, sit=False)
            d.chair(cx + 2, 2, z, "east", wood, sit=False)
    if x2 - x1 >= 10:
        for z in range(z1 + 2, z2 - 1, 2):
            d.set(x1 + 1, 2, z, "bookshelf")
            d.set(x2 - 1, 2, z, "chiseled_bookshelf[facing=west,slot_0_occupied=true,slot_1_occupied=false,"
                  "slot_2_occupied=true,slot_3_occupied=true,slot_4_occupied=false,slot_5_occupied=true]")
        for x in range(x1 + 3, x2 - 2, 3):
            if x != cx:
                d.set(x, 2, z2 - 1, "white_stained_glass")                 # display cases
                d.set(x, 3, z2 - 1, "decorated_pot[cracked=false,facing=north,waterlogged=false]")
    for z in range(z1 + 2, z2, 3):
        d.set(cx, ph - 1, z, lantern(True))


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
            d.set(x + ox, 3, z, "potted_red_tulip" if z % 2 else "potted_azure_bluet")
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
        for z in range(z1 + 2, z2 - 1, 3):
            for x in (x1 + 2, x2 - 2):
                d.set(x, y, z, HS["carve"])
                d.set(x, y + 1, z, "white_stained_glass" if z % 2 else "decorated_pot[cracked=false,facing=north,waterlogged=false]")
        d.set(cx, y, z2 - 1, "lectern[facing=north,has_book=true,powered=false]")
        d.rug(cx - 1, z1 + 1, cx + 1, z2 - 2, y, ("red_carpet", "yellow_carpet"))
        for z in range(z1 + 2, z2 - 1, 2):
            d.set(x1 + 1, y, z, "bookshelf")
            d.set(x2 - 1, y, z, "bookshelf")
    else:
        for z in range(z1 + 3, z2 - 2, 2):
            for x in (cx - 2, cx - 1, cx + 1, cx + 2):
                d.chair(x, y, z, "north", "oak", sit=False)
        d.set(cx, y, z2 - 1, HS["carve"])
        d.candle(cx, y + 1, z2 - 1, 4)
        d.set(cx, 5, z2, "yellow_stained_glass_pane")
    for z in range(z1 + 3, z2 - 1, 4):
        chandelier(d, cx, z, rd - 1, 6)


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
    colossus_hall(d, x1, z1, x2, z2, ph, "polished_granite", "oak", "red", L)
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
        for x in range(cx - 6, cx + 7):
            for z in range(z1 - 6, z1 - 1):
                if d.get(x, 1, z).endswith(("grass_block", "gravel")):
                    d.set(x, 1, z, "bricks" if (x + 2 * z) % 4 == 0 else "cut_sandstone")
        for x in (cx - 6, cx + 6):
            d.chair(x, 2, z1 - 4, "west" if x < cx else "east", "oak", sit=False)
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
                    if (x + z) % 5 == 0 and r < R - 1.4:
                        d.chair(x, 2, z, "south" if z > ecz + 4 else ("west" if x < cx else "east"), "oak",
                                sit=False)
        for x in (cx - 3, cx + 3):
            d.set(x, 2, ecz + 3, HS["carve"])
            d.set(x, 3, ecz + 3, "potted_flowering_azalea_bush")
    # ---- L5: museum and chapel pavilions, avenue of trees, boundary wall with gate piers
    if L >= 5:
        hk_pavilion(d, 1, 19, 9, 31, "museum")
        hk_pavilion(d, 35, 19, 43, 31, "chapel")
        for z in range(2, 14, 4):
            for x in (cx - 8, cx + 8):
                yew(d, x, z, 2, "oak_leaves", "oak_log")
        for x in range(0, 45):
            if d.air(x, 2, 0) and not cx - 2 <= x <= cx + 2:
                d.set(x, 2, 0, HS["quoin"] if x % 6 == 0 else W)
                d.set(x, 3, 0, slab(HS["sl"]))
        for x in (cx - 3, cx + 3):
            d.fill(x, 2, 0, x, 4, 0, HS["quoin"])
            d.set(x, 5, 0, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        for x, z in ((5, 35), (39, 35), (3, 42), (41, 42), (22, 44)):
            yew(d, x, z, 2, "oak_leaves", "oak_log")
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
    for x in range(x1 + 2, x1 + 6):
        d.set(x, 3, zc, log("stripped_spruce_log", "x")) if False else None
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
            if (x in (x1 - 1, x2 + 1) or z in (z1 - 1, z2 + 1)) and d.air(x, 2, z):
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
    colossus_hall(d, x1, z1, x2, z2, ph, "spruce_planks", "spruce", "green", L)
    d.hearth(x1 + 1, 2, cz, "east", ph, "cobblestone", "campfire")
    d.set(x2 - 1, 2, z1 + 1, "barrel[facing=up,open=false]")
    d.set(x2 - 1, 2, z1 + 2, "barrel[facing=up,open=false]")
    d.item(x2 - 1, 2, cz + 1, "grindstone", "west")
    d.clear(cx, 2, z1 - 1, cx, 3, z1 - 1)
    d.door(cx, 2, z1, "south", "mangrove")
    d.set(cx, 1, z1 - 1, "spruce_planks")
    d.set(cx - 1, 2, z1 - 1, "barrel[facing=up,open=false]")
    d.sign(cx + 1, 3, z1 - 1, "north", ["TIMBER", "GIANT"], "spruce")
    d.hut(19, 2, 22)
    # statue
    lumberjack(cx, cz, ph + 1, COLO_H["Cascadia"][L]).commit(d, ph + 1)
    # surroundings by level
    if L >= 2:                                                       # woodpiles and stumps
        for z in range(z1, z1 + 5):
            for y in (2, 3):
                d.set(x1 - 4, y, z, log("spruce_log", "x"))
        for x, z in ((cx - 7, z1 - 5), (cx + 7, z1 - 6), (cx + 8, z2)):
            d.set(x, 2, z, log("spruce_log"))
            d.set(x, 3, z, "brown_carpet") if False else d.set(x, 3, z, "moss_carpet")
    if L >= 3:                                                       # split-rail fence and lamp posts
        for z in range(0, z1 - 1):
            for x in (cx - 3, cx + 3):
                if d.air(x, 2, z) and z % 4 != 3:
                    d.set(x, 2, z, fence("spruce_fence"))
        for x, z in ((cx - 6, 2), (cx + 6, 2)):
            lamp_post(d, x, z, "cobblestone", log("stripped_spruce_log"))
        for x in range(cx - 4, cx + 5):
            if d.air(x, 2, z2 + 3):
                d.set(x, 2, z2 + 3, ("fern", "sweet_berry_bush[age=3]", "fern", "large_fern[half=lower]")[x % 4])
                if x % 4 == 3:
                    d.set(x, 3, z2 + 3, "large_fern[half=upper]")
    if L >= 4:
        cc_log_house(d, 1, 24, 11, 13, "hall", H=5, pal="museum")       # logging museum
        cg_sawmill(d, 31, 26, 41, 32)
        for x, z in ((3, 6), (39, 6), (2, 44), (40, 44)):
            yew(d, x, z, 2, "spruce_leaves", "spruce_log")
    if L >= 5:
        cc_log_house(d, 31, 37, 9, 10, "lodge", H=9, pal="bunk")       # bunkhouse
        cc_log_house(d, 2, 41, 7, 7, "store", H=4)                      # tool store
        for x in range(12, 30):                                         # flume / log chute by the path
            if d.air(x, 2, 46):
                d.set(x, 1, 46, "water")
                d.set(x, 2, 47, log("spruce_log", "x"))
        for x, z in ((14, 40), (28, 40), (14, 2), (28, 2)):
            d.chair(x, 2, z, "north", "spruce", sit=False)
        for x, z in ((12, 43), (30, 3), (12, 3)):
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


def nb_visitor_centre(d, x1, z1, x2, z2, two=False):
    """Visitor centre: deepslate-clad box with an orange fin facade, glass front, cut-copper roof canopy, green
    roof; shop counter, cafe tables, info screens, plants."""
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
    for x in range(x1 + 2, x2 - 1, 3):
        for z in range(z1 + 2, z2 - 1, 3):
            d.set(x, top + 2, z, "azalea" if (x + z) % 2 else "flowering_azalea")
    for x in range(x1 - 1, x2 + 2):
        d.set(x, 6 if not two else 6, z1 - 1, slab("waxed_cut_copper_slab", "top"))
    cxx = (x1 + x2) // 2
    d.double_door(cxx, 2, z1, "x", "south", "cherry")
    if two:
        d.fill(x1 + 1, 6, z1 + 1, x2 - 1, 6, z2 - 1, "gray_concrete")
        for i in range(4):
            z = z2 - 5 + i
            d.set(x2 - 1, 2 + i, z, stair("smooth_quartz_stairs", "south"))
            if i:
                d.fill(x2 - 1, 2, z, x2 - 1, 1 + i, z, "gray_concrete")
        d.clear(x2 - 1, 6, z2 - 5, x2 - 1, 6, z2 - 1)
        d.set(x2 - 1, 5, z2 - 1, "gray_concrete")
        d.clear(x2 - 1, 6, z2 - 4, x2 - 1, 6, z2 - 1)
        for x in range(x1 + 2, x2 - 2, 3):                          # gallery upstairs
            d.set(x, 7, z2 - 1, "white_concrete")
            d.set(x, 8, z2 - 1, "white_stained_glass")
            d.dining(x, 7, z1 + 3, 1, "x", "cherry", chairs=("n", "s")) if x < x2 - 3 else None
        for x in range(x1 + 2, x2 - 1, 4):
            d.set(x, 10, (z1 + z2) // 2, "sea_lantern")
    # ground floor: shop counter, cafe, info screens
    d.counter(x1 + 1, z2 - 2, x1 + 4, z2 - 2, 2, body="smooth_quartz")
    d.set(x1 + 1, 2, z2 - 1, "barrel[facing=up,open=false]")
    d.item(x1 + 2, 2, z2 - 1, "smoker", "north")
    for x in range(x1 + 2, x2 - 3, 4):
        d.dining(x, 2, z1 + 3, 1, "x", "cherry", chairs=("n", "s"))
    d.set(x2 - 1, 3, z1 + 2, "black_stained_glass_pane") if False else None
    d.set(x2 - 2, 2, z1 + 1, "lectern[facing=west,has_book=true,powered=false]")
    d.set(x1 + 1, 2, z1 + 1, "potted_bamboo")
    d.set(x2 - 1, 2, z1 + 1, "potted_bamboo")
    for x in range(x1 + 2, x2 - 1, 3):
        d.set(x, 5, (z1 + z2) // 2, "end_rod[facing=down]")


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
    colossus_hall(d, x1, z1, x2, z2, ph, "polished_diorite", "cherry", "orange", L)
    d.clear(cx, 2, z1 - 1, cx, 3, z1 - 1)
    d.door(cx, 2, z1, "south", "cherry")
    d.set(cx, 1, z1 - 1, "smooth_quartz")
    d.sign(cx + 1, 3, z1 - 1, "north", ["BEACON"], "cherry", glow=True, color="orange") \
        if d.air(cx + 1, 3, z1 - 1) else None
    d.hut(22, 2, 23)
    # statue
    H = COLO_H["Neoterra"][L]
    sc, orb = beacon_figure(cx, cz, ph + 1, H)
    sc.commit(d, ph + 1)
    ox, oy, oz, r = orb
    if L >= 3:
        for ddx, ddz, f in ((1, 0, "east"), (-1, 0, "west"), (0, 1, "south"), (0, -1, "north")):
            x, z = int(round(ox + ddx * (r + 1.5))), int(round(oz + ddz * (r + 1.5)))
            if d.bp.inside(x, int(round(oy)), z) and d.air(x, int(round(oy)), z):
                d.set(x, int(round(oy)), z, f"end_rod[facing={f}]")
        tp = int(round(oy + r)) + 1
        for y in range(tp, tp + 2):
            if d.bp.inside(int(round(ox)), y, int(round(oz))):
                d.set(int(round(ox)), y, int(round(oz)), "end_rod[facing=up]")
    # approach: light bollards and planters
    for z in range(1, z1 - 1, 3):
        for x in (cx - 3, cx + 3):
            d.set(x, 2, z, "smooth_quartz")
            d.set(x, 3, z, "end_rod[facing=up]")
    if L >= 2:
        for z in range(2, z1 - 2, 6):
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
        nb_visitor_centre(d, 1, 33, 13, 44, two=L >= 5)
        for x in range(36, 47, 5):                                   # sculpture garden
            d.set(x, 1, 36, "moss_block")
            d.set(x, 2, 36, "polished_blackstone")
            d.set(x, 3, 36, "waxed_copper_block" if x % 2 else "orange_concrete")
            d.set(x, 4, 36, "end_rod[facing=up]")
    if L >= 5:
        nb_visitor_centre(d, 35, 39, 47, 47)                             # cafe pavilion
        for x, z in ((3, 26), (45, 26), (3, 14), (45, 14), (20, 46), (28, 46)):
            if d.air(x, 2, z):
                d.set(x, 1, z, "moss_block")
                d.set(x, 2, z, log("cherry_log"))
                d.set(x, 3, z, log("cherry_log"))
                for ddx in (-1, 0, 1):
                    for ddz in (-1, 0, 1):
                        for yy in (4, 5):
                            if d.bp.inside(x + ddx, yy, z + ddz) and d.air(x + ddx, yy, z + ddz) \
                                    and not (yy == 5 and ddx and ddz):
                                d.set(x + ddx, yy, z + ddz,
                                      "cherry_leaves[distance=1,persistent=true,waterlogged=false]")
        for x, z in ((16, 6), (32, 6), (16, 12), (32, 12)):
            d.chair(x, 2, z, "west" if x < cx else "east", "cherry", sit=False)
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
