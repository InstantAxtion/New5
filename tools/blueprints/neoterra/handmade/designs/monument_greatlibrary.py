"""
Grand project: the Great Library (greatlibrary + greatlibrarywing). Bonus: citizens gain skill faster.

  Hearthwood  Oxford: a domed round READING ROOM (Radcliffe Camera) in honey Cotswold stone – rusticated ground
              storey with arched windows, an upper storey with paired pilasters and tall windows, balustrade,
              drum, ribbed lead dome and lantern. Inside: radial reading desks, a circular issue desk, a book
              stair up to the gallery. Grows into a quadrangle: Gothic library ranges (Divinity School /
              Duke Humfrey's Library, lecture room / map room) at L4, the south range with the gate tower
              (Tower of the Five Orders), exam hall, tea room and the iron screen to the street at L5.
              Wings: square Gothic BOOK-STACK TOWERS with battlements on the street corners.
  Neoterra    Contemporary civic library (Seattle Central / Stuttgart): a glass-and-concrete podium, stacked
              glass volumes that cantilever over the entrance plaza, a cylindrical BOOK SPIRAL tower (a ramp
              of shelves around a light well), stepped reading terraces and a crown pavilion.
              Wings: slim glass book-stack towers with white fins and glowing tops.
  Cascadia    Mountain-lodge reading hall: a long log hall with exposed log trusses and two river-rock
              fireplaces, mezzanine galleries, a covered porch, a cross wing, side reading cabins, decks and
              a lookout cupola. Wings: timber fire-lookout BOOK TOWERS on log cribs.
Every room is furnished by hand at explicit coordinates (per level where things are added).
"""
import math

from hm import Design, design, AIR, D4, OPP, CW

WING = "monuments/greatlibrarywing0.blueprint"


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


def ladder(facing):
    return f"ladder[facing={facing},waterlogged=false]"


CHAIN = "chain[axis=y,waterlogged=false]"


def chandelier(d, x, z, ytop, ybot, soul=False, arms=None):
    """Chain from ytop down to a lantern at ybot; optional arms (block) around the lantern one higher."""
    for y in range(ybot + 1, ytop + 1):
        d.set(x, y, z, CHAIN)
    d.set(x, ybot, z, lantern(True, soul))
    if arms:
        for dx, dz in D4.values():
            d.set(x + dx, ybot + 1, z + dz, arms)
            d.set(x + dx, ybot, z + dz, lantern(True, soul))


def lamp_post(d, x, z, y, base, post, h=2, top=None):
    d.set(x, y, z, base)
    for k in range(h):
        d.set(x, y + 1 + k, z, post)
    d.set(x, y + 1 + h, z, top or lantern(False))


def desk(d, x, y, z, chair_side, wood, top=None, light=None):
    """Reading desk: a top slab at (x,z), the chair on `chair_side` facing it, optional candle / lamp on the desk."""
    d.set(x, y, z, slab(top or f"{wood}_slab", "top"))
    dx, dz = D4[chair_side]
    d.chair(x + dx, y, z + dz, chair_side, wood)
    if light:
        d.set(x, y + 1, z, light)


def shelves(d, cells, y, h=1):
    for x, z in cells:
        d.bookshelf(x, y, z, h)


def tree(d, x, z, y, trunk, leaves, h=4, r=2):
    """One hand-placed tree: trunk of h, a rounded crown."""
    for k in range(h):
        d.set(x, y + k, z, log(trunk))
    top = y + h
    for dy in (-1, 0, 1):
        rr = r if dy < 1 else r - 1
        for dx in range(-rr, rr + 1):
            for dz in range(-rr, rr + 1):
                if abs(dx) + abs(dz) <= rr + (0 if dy else 1) and (dx, dz, dy) != (0, 0, -1):
                    if d.bp.inside(x + dx, top + dy, z + dz) and d.air(x + dx, top + dy, z + dz):
                        d.set(x + dx, top + dy, z + dz, f"{leaves}[distance=1,persistent=true,waterlogged=false]")
    d.set(x, top + 1, z, f"{leaves}[distance=1,persistent=true,waterlogged=false]")


# round-plan helpers ---------------------------------------------------------------------------------------
def inside(cx, cz, x, z, R):
    return math.hypot(x - cx, z - cz) <= R + 0.45


def disk(cx, cz, R):
    r = int(R) + 1
    return [(x, z) for x in range(cx - r, cx + r + 1) for z in range(cz - r, cz + r + 1) if inside(cx, cz, x, z, R)]


def ring(cx, cz, R):
    """Wall ring of a round tower of radius R: cells inside R with a 4-neighbour outside."""
    return [(x, z) for x, z in disk(cx, cz, R)
            if any(not inside(cx, cz, x + dx, z + dz, R) for dx, dz in D4.values())]


def interior(cx, cz, R):
    rs = set(ring(cx, cz, R))
    return [c for c in disk(cx, cz, R) if c not in rs]


def ang(cx, cz, x, z):
    return math.degrees(math.atan2(z - cz, x - cx)) % 360


def adiff(a, b):
    return abs((a - b + 180) % 360 - 180)


def rim(cx, cz, R, a):
    """The interior cell along the ray at angle a (0 = east, 90 = south) right inside the wall ring."""
    rs = set(ring(cx, cz, R))
    best = None
    for k in range(0, int(R * 4)):
        r = k / 4
        c = (round(cx + r * math.cos(math.radians(a))), round(cz + r * math.sin(math.radians(a))))
        if c in rs:
            break
        best = c
    return best


def dome(d, cx, cz, y0, R, H, block, rib=None, nrib=16, hole=0.0):
    """Solid-shell dome on the circle of radius R whose foot is at y0, H high; ribs every 360/nrib degrees;
    cells within `hole` of the centre stay open (for a lantern)."""
    tops = {}
    for x, z in disk(cx, cz, R):
        dd = math.hypot(x - cx, z - cz)
        tops[(x, z)] = y0 + int(round(H * math.sqrt(max(0.0, 1 - (dd / (R + 0.5)) ** 2))))
    for (x, z), t in tops.items():
        dd = math.hypot(x - cx, z - cz)
        if dd <= hole:
            continue
        lo = min(tops.get((x + dx, z + dz), y0 - 1) for dx, dz in D4.values()) + 1
        a = ang(cx, cz, x, z)
        isrib = rib and dd > 0.8 and min(adiff(a, k * 360 / nrib) for k in range(nrib)) * math.pi / 180 * dd < 0.55
        for y in range(max(y0, min(lo, t)), t + 1):
            d.set(x, y, z, rib if isrib else block)
    return max(tops.values())


# ================================================================================================ HEARTHWOOD
HW_SIZE = (45, 52, 45)
HW_C = (22, 22)
HW_R = 8
HW_TX, HW_TZ, HW_TW = (1, 37), 1, 7          # book-stack towers (wings): x origins, z origin, footprint
HW_WHUT = (5, 1, 1)                           # wing hut, tower-local
HW_WTOP = {1: 5, 2: 9, 3: 13, 4: 17, 5: 21}   # tower roof slab (local y)
HS = "smooth_sandstone"
HQ = "cut_sandstone"
HC = "chiseled_sandstone"


def hw_lancet(d, x, z, y1, y2, along, glass="glass_pane"):
    """Lancet window in a wall: panes y1..y2, a pointed head (two upside-down stairs) is drawn by the caller
    for 2-wide windows; 1-wide lancets get a chiseled head stone."""
    for y in range(y1, y2 + 1):
        d.set(x, y, z, glass)
    d.set(x, y2 + 1, z, HC)


def hw_wing(rel, L):
    """Gothic book-stack tower: sandstone, angle buttresses, a lancet per face and storey, battlements and corner
    pinnacles, a lead spirelet at L5. One room per storey, each a different use, linked by a ladder."""
    d = Design("Hearthwood", rel, (HW_TW, 34, HW_TW), gy=0, paving="stone_bricks")
    n, T = HW_TW - 1, HW_WTOP[L]
    d.box(0, 1, 0, n, T, n, HS)
    d.fill(1, 0, 1, n - 1, 0, n - 1, "oak_planks")
    for y in range(1, T + 1):                                  # angle buttress columns
        for x, z in ((0, 0), (n, 0), (0, n), (n, n)):
            d.set(x, y, z, HQ if y % 4 else HC)
    for F in range(5, T, 4):                                   # floors + string courses
        d.fill(1, F, 1, n - 1, F, n - 1, "spruce_planks")
        for i in range(1, n):
            for x, z in ((i, 0), (i, n), (0, i), (n, i)):
                d.set(x, F, z, HQ)
    d.fill(1, T, 1, n - 1, T, n - 1, "stone_bricks")
    # windows: a lancet in each face on every storey (the street face of the ground storey holds the door)
    for w in range(1, T - 3, 4):
        for x, z in ((3, 0), (3, n), (0, 3), (n, 3)):
            if w == 1 and (x, z) in ((3, 0), (n, 3)):
                continue
            hw_lancet(d, x, z, w + 1, w + 2, None)
    d.door(3, 1, 0, "south", "dark_oak")
    d.set(3, 3, 0, HC)
    d.set(2, 3, 0, stair("sandstone_stairs", "west", "top"))
    d.set(4, 3, 0, stair("sandstone_stairs", "east", "top"))
    # ladder in the south-west corner through every floor
    for y in range(1, T - 3 if L > 1 else 1):
        d.set(1, y, n - 1, ladder("east"))
    # ---- ground storey: issue room (hut, lectern for the reading of the day, catalogue shelves)
    d.hut(*HW_WHUT)
    d.item(4, 1, 3, "lectern[facing=north,has_book=true,powered=false]")
    for z in (2, 3):
        d.set(1, 1, z, "chiseled_bookshelf[facing=east,slot_0_occupied=true,slot_1_occupied=true,"
                       "slot_2_occupied=false,slot_3_occupied=true,slot_4_occupied=false,slot_5_occupied=true]")
        d.set(1, 2, z, "chiseled_bookshelf[facing=east,slot_0_occupied=false,slot_1_occupied=true,"
                       "slot_2_occupied=true,slot_3_occupied=true,slot_4_occupied=true,slot_5_occupied=false]")
    d.set(1, 1, 1, "potted_fern")
    d.rug(2, 2, 3, 4, 1, ("red_carpet", "red_carpet"), "plain")
    d.set(5, 1, 4, "barrel[facing=up,open=false]")
    d.set(5, 1, 5, "barrel[facing=up,open=false]")
    d.set(5, 2, 5, "candle[candles=3,lit=false,waterlogged=false]")
    d.set(5, 3, 2, "red_wall_banner[facing=west]")
    d.lamp(3, 4, 3)
    # ---- storey 2: the stacks (shelves along two walls, a library ladder, step stool)
    if L >= 2:
        y = 6
        d.bookshelf(5, y, 1, 2), d.bookshelf(5, y, 2, 2), d.bookshelf(5, y, 3, 2), d.bookshelf(5, y, 4, 2)
        d.bookshelf(2, y, 1, 2), d.bookshelf(3, y, 1, 2)
        d.set(4, y, 1, ladder("west"))
        d.set(4, y + 1, 1, ladder("west"))
        d.chair(3, y, 3, "south", "oak", sit=False)
        d.set(2, y, 5, "chest[facing=north,type=single,waterlogged=false]")
        d.set(3, y, 5, "chest[facing=north,type=single,waterlogged=false]")
        d.set(1, y, 2, "brown_carpet")
        d.set(2, y, 3, "brown_carpet")
        d.lamp(3, y + 2, 3)
    # ---- storey 3: manuscript room (scribe's desk under the window, ink and candles, drying racks)
    if L >= 3:
        y = 10
        desk(d, 3, y, 5, "north", "dark_oak", light="candle[candles=2,lit=false,waterlogged=false]")
        d.set(2, y, 5, "barrel[facing=up,open=false]")
        d.set(4, y, 5, slab("dark_oak_slab", "top"))
        d.set(4, y + 1, 5, "flower_pot")
        for z in (1, 2, 3):
            d.set(5, y, z, trap("spruce_trapdoor", "west", "bottom", True))
            d.set(5, y + 1, z, trap("spruce_trapdoor", "west", "top", True))
        d.set(1, y, 1, "loom[facing=east]")
        d.rug(2, 2, 3, 3, y, ("green_carpet", "green_carpet"), "plain")
        d.set(5, y + 1, 4, "green_wall_banner[facing=west]")
        d.lamp(3, y + 2, 3)
    # ---- storey 4: the librarian's study (two armchairs, a tea table, a bureau)
    if L >= 4:
        y = 14
        d.rug(2, 1, 4, 3, y, ("blue_carpet", "light_blue_carpet"))
        d.chair(2, y, 2, "west", "dark_oak", arms=False)
        d.chair(4, y, 2, "east", "dark_oak", arms=False)
        d.table(3, y, 2, "dark_oak", "slab")
        d.set(3, y + 1, 2, "potted_red_tulip")
        d.set(5, y, 4, slab("dark_oak_slab", "top"))
        d.set(5, y, 5, "chiseled_bookshelf[facing=west,slot_0_occupied=true,slot_1_occupied=true,"
                       "slot_2_occupied=true,slot_3_occupied=false,slot_4_occupied=true,slot_5_occupied=true]")
        d.chair(4, y, 4, "west", "dark_oak", sit=False)
        d.set(5, y + 1, 4, "candle[candles=1,lit=false,waterlogged=false]")
        d.set(2, y, 5, "potted_oak_sapling")
        d.lamp(3, y + 2, 3)
    # ---- storey 5: observatory (telescope at the window, star-chart table, armillary)
    if L >= 5:
        y = 18
        d.set(3, y, 1, fence("dark_oak_fence"))
        d.set(3, y + 1, 1, "lightning_rod[facing=north,powered=false,waterlogged=false]")
        d.item(4, y, 4, "cartography_table")
        d.chair(4, y, 3, "north", "dark_oak", sit=False)
        d.set(5, y, 1, "chiseled_bookshelf[facing=west,slot_0_occupied=true,slot_1_occupied=false,"
                       "slot_2_occupied=true,slot_3_occupied=true,slot_4_occupied=false,slot_5_occupied=false]")
        d.set(2, y, 5, "candle[candles=4,lit=false,waterlogged=false]")
        d.set(5, y, 5, "spruce_slab[type=top,waterlogged=false]")
        d.set(5, y + 1, 5, "end_rod[facing=up]")
        d.rug(2, 3, 3, 3, y, ("black_carpet", "black_carpet"), "plain")
        d.lamp(1, y + 2, 1)
        d.lamp(5, y + 2, 3)
    # ---- crown: battlements, corner pinnacles, L5 spirelet
    for i in range(0, n + 1):
        for x, z in ((i, 0), (i, n), (0, i), (n, i)):
            d.set(x, T + 1, z, HS)
            if i % 2 == 0:
                d.set(x, T + 2, z, slab("smooth_sandstone_slab"))
    for x, z in ((0, 0), (n, 0), (0, n), (n, n)):
        h = 2 + min(L, 4)
        for y in range(T + 1, T + h):
            d.set(x, y, z, HQ)
        d.set(x, T + h, z, wallb("sandstone_wall"))
        d.set(x, T + h + 1, z, "lightning_rod[facing=up,powered=false,waterlogged=false]" if L >= 4
              else slab("smooth_sandstone_slab"))
    if L >= 5:
        for r, y in ((2, T + 1), (2, T + 2), (1, T + 3), (1, T + 4), (1, T + 5)):
            for x in range(3 - r, 4 + r):
                for z in range(3 - r, 4 + r):
                    if x in (3 - r, 3 + r) or z in (3 - r, 3 + r):
                        d.set(x, y, z, "deepslate_tiles")
        d.set(3, T + 6, 3, "deepslate_tiles")
        d.set(3, T + 7, 3, wallb("sandstone_wall"))
        d.set(3, T + 8, 3, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    return d


def hw_rotunda(d, L):
    cx, cz = HW_C
    R = HW_R
    rg = ring(cx, cz, R)
    inn = interior(cx, cz, R)
    # plinth and floor
    for x, z in disk(cx, cz, 9.3):
        d.set(x, 2, z, "stone_bricks")
    for x, z in inn:
        dd = math.hypot(x - cx, z - cz)
        d.set(x, 2, z, "polished_deepslate" if int(dd + 0.5) in (2, 5) else "calcite")
    for x in (21, 22, 23):
        d.set(x, 2, 12, stair("stone_brick_stairs", "south"))
    # ground storey: rusticated walls, arched bays every 45 degrees (north bay = entrance)
    for x, z in rg:
        for y in range(3, 10):
            d.set(x, y, z, HQ if y % 2 else HS)
        a = ang(cx, cz, x, z)
        bay = min(range(8), key=lambda k: adiff(a, k * 45))
        if adiff(a, bay * 45) * math.pi / 180 * R < 1.3:
            if bay == 6:
                continue
            for y in range(4, 8):
                d.set(x, y, z, "glass_pane")
            d.set(x, 8, z, HC)
    d.door(22, 3, 14, "south", "dark_oak")
    for y in (5, 6, 7):
        d.set(22, y, 14, "glass_pane")
    d.set(22, 8, 14, HC)
    for x in (21, 23):                                 # entrance surround
        for y in range(3, 8):
            d.set(x, y, 13, HQ if y < 7 else HC)
    d.set(22, 8, 13, slab("smooth_sandstone_slab", "top"))
    d.set(21, 8, 13, stair("sandstone_stairs", "east"))
    d.set(23, 8, 13, stair("sandstone_stairs", "west"))
    d.set(22, 9, 13, slab("smooth_sandstone_slab"))
    # cornice ring at y=10
    for x, z in disk(cx, cz, 9):
        if not inside(cx, cz, x, z, R):
            d.set(x, 10, z, slab("smooth_sandstone_slab", "top"))
    for x, z in rg:
        d.set(x, 10, z, HQ)
    hw_rotunda_ground(d, L)
    if L == 1:
        for x, z in inn:
            d.set(x, 10, z, "dark_oak_planks")
        top = dome(d, cx, cz, 11, R, 3, "deepslate_tiles", "polished_deepslate", 16)
        d.set(cx, top + 1, cz, HQ)
        d.set(cx, top + 2, cz, wallb("sandstone_wall"))
        d.set(cx, top + 3, cz, lantern(False))
        chandelier(d, cx, cz, 9, 7, arms=None)
        return
    # ---- L2+: upper storey with paired pilasters, tall windows, entablature and balustrade
    for x, z in rg:
        for y in range(11, 18):
            d.set(x, y, z, HS)
        a = ang(cx, cz, x, z)
        bay = min(range(8), key=lambda k: adiff(a, k * 45))
        if adiff(a, bay * 45) * math.pi / 180 * R < 0.9:
            for y in range(12, 16):
                d.set(x, y, z, "glass_pane")
            d.set(x, 16, z, HC)
    for x, z in disk(cx, cz, 9):                      # pilasters between the bays, entablature
        if inside(cx, cz, x, z, R):
            continue
        a = ang(cx, cz, x, z)
        if min(adiff(a, 22.5 + 45 * k) for k in range(8)) * math.pi / 180 * 9 < 1.0:
            d.set(x, 11, z, HQ)
            for y in range(12, 17):
                d.set(x, y, z, "sandstone_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
            d.set(x, 17, z, HC)
        d.set(x, 18, z, HQ)
        d.set(x, 19, z, HQ if min(adiff(a, 22.5 + 45 * k) for k in range(8)) * math.pi / 180 * 9 < 1.0
              else wallb("sandstone_wall"))
    for x, z in rg:
        d.set(x, 18, z, HQ)
    hw_gallery(d, L)
    if L == 2:
        for x, z in inn:
            d.set(x, 18, z, "dark_oak_planks")
        top = dome(d, cx, cz, 19, R, 3, "deepslate_tiles", "polished_deepslate", 16)
        d.set(cx, top + 1, cz, HQ)
        d.set(cx, top + 2, cz, wallb("sandstone_wall"))
        d.set(cx, top + 3, cz, lantern(False))
        chandelier(d, cx, cz, 17, 8)
        return
    # ---- L3+: drum, ribbed lead dome, lantern
    for x, z in inn:
        if not inside(cx, cz, x, z, 5):
            d.set(x, 18, z, "dark_oak_planks")
    for x, z in ring(cx, cz, 6):
        for y in range(19, 24):
            d.set(x, y, z, HS)
        a = ang(cx, cz, x, z)
        if min(adiff(a, 45 * k) for k in range(8)) * math.pi / 180 * 6 < 0.7:
            for y in (20, 21, 22):
                d.set(x, y, z, "glass_pane")
        d.set(x, 24, z, HQ)
    for x, z in disk(cx, cz, 7):
        if not inside(cx, cz, x, z, 6):
            d.set(x, 24, z, slab("smooth_sandstone_slab"))
    top = dome(d, cx, cz, 25, 6, 6, "deepslate_tiles", "polished_deepslate", 16, hole=1.5)
    for dx in (-1, 0, 1):                              # lantern
        for dz in (-1, 0, 1):
            if (dx, dz) == (0, 0):
                continue
            for y in range(top, top + 3):
                d.set(cx + dx, y, cz + dz, HQ if dx and dz else "glass_pane")
            d.set(cx + dx, top + 3, cz + dz, HQ)
            d.set(cx + dx, top + 4, cz + dz, stair("sandstone_stairs", OPP[("east" if dx > 0 else "west")] if dz == 0
                                                  else ("north" if dz > 0 else "south")))
    d.set(cx, top + 3, cz, HQ)
    d.set(cx, top + 4, cz, HQ)
    d.set(cx, top + 5, cz, wallb("sandstone_wall"))
    d.set(cx, top + 6, cz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    chandelier(d, cx, cz, top - 1, 8, arms=None)
    d.set(cx, 13, cz, "chain[axis=y,waterlogged=false]")
    for dx, dz in D4.values():                         # corona of lights in the well
        d.set(cx + dx * 2, 13, cz + dz * 2, slab("dark_oak_slab", "top"))
        d.set(cx + dx * 2, 12, cz + dz * 2, lantern(True))
    for dx, dz in D4.values():
        d.set(cx + dx, 13, cz + dz, slab("dark_oak_slab", "top"))


def hw_rotunda_ground(d, L):
    """Ground-floor reading room (walk y=3): circular issue desk, window desks, shelf piers, the book stair (L2+)."""
    cx, cz = HW_C
    y = 3
    d.hut(24, y, 16, "north")
    # circular issue desk with the librarian's chair, open to the south
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            if (dx, dz) in ((0, 0), (0, 1)):
                continue
            d.set(cx + dx, y, cz + dz, slab("dark_oak_slab", "top") if (dx, dz) != (0, -1) else "dark_oak_planks")
    d.chair(cx, y, cz, "south", "dark_oak")
    d.set(cx - 1, y + 1, cz - 1, "candle[candles=3,lit=false,waterlogged=false]")
    d.set(cx + 1, y + 1, cz - 1, "potted_red_tulip")
    d.set(cx, y + 1, cz - 1, "chiseled_bookshelf[facing=north,slot_0_occupied=true,slot_1_occupied=true,"
                             "slot_2_occupied=true,slot_3_occupied=true,slot_4_occupied=false,slot_5_occupied=true]")
    d.rug(cx, cz - 7, cx, cz - 2, y, ("red_carpet",), "plain")
    d.rug(cx - 2, cz - 2, cx + 2, cz + 2, y, ("blue_carpet", "blue_carpet"))
    # desks under six windows, chairs facing the light
    for a, side in ((0, "west"), (45, "west"), (135, "east"), (180, "east"), (225, "east"), (315, "west")):
        x, z = rim(cx, cz, HW_R, a)
        desk(d, x, y, z, side, "dark_oak",
             light="candle[candles=1,lit=false,waterlogged=false]" if a in (0, 180) else None)
    # shelf piers between the windows, a lantern on each
    piers = (22.5, 67.5, 112.5, 157.5, 202.5, 247.5, 292.5, 337.5) if L == 1 else \
        (22.5, 157.5, 202.5, 247.5, 292.5, 337.5)
    for a in piers:
        x, z = rim(cx, cz, HW_R, a)
        d.bookshelf(x, y, z, 2)
        d.set(x, y + 2, z, lantern(False))
    if L == 1:
        x, z = rim(cx, cz, HW_R, 90)
        desk(d, x, y, z, "north", "dark_oak", light="candle[candles=2,lit=false,waterlogged=false]")
        return
    # book stair along the south wall: steps rise to the east, shelves fill the stringer
    for i in range(8):
        x = 18 + i
        d.set(x, y + i, 28, stair("dark_oak_stairs", "east"))
        for yy in range(y, y + i):
            d.bookshelf(x, yy, 28)
    d.set(17, y, 28, "potted_fern")


def hw_gallery(d, L):
    """Gallery ring (walk y=11) around the open well: shelf piers, window desks, globe, railing."""
    cx, cz = HW_C
    y = 11
    inn = interior(cx, cz, HW_R)
    for x, z in inn:
        dd = math.hypot(x - cx, z - cz)
        d.set(x, 10, z, AIR if dd <= 3.45 else "dark_oak_planks")
    for x in range(18, 25):                       # stair well
        d.set(x, 10, 28, AIR)
    for x, z in inn:                              # railing round the well
        dd = math.hypot(x - cx, z - cz)
        if dd > 3.45 and any(math.hypot(x + dx - cx, z + dz - cz) <= 3.45 for dx, dz in D4.values()):
            d.set(x, y, z, fence("dark_oak_fence"))
    for x in range(18, 25):
        d.set(x, y, 27, fence("dark_oak_fence"))
    for x in range(20, 25):
        d.bookshelf(x, y, 29)
    for a in (22.5, 112.5, 157.5, 202.5, 247.5, 292.5, 337.5):
        x, z = rim(cx, cz, HW_R, a)
        d.bookshelf(x, y, z, 2)
        d.set(x, y + 2, z, lantern(False))
    for a, side in ((0, "west"), (180, "east"), (225, "east"), (315, "west")):
        x, z = rim(cx, cz, HW_R, a)
        desk(d, x, y, z, side, "spruce", light="candle[candles=2,lit=false,waterlogged=false]" if a == 180 else None)
    x, z = rim(cx, cz, HW_R, 135)
    d.set(x, y, z, fence("dark_oak_fence"))           # globe on a stand
    d.set(x, y + 1, z, "light_blue_stained_glass")
    x, z = rim(cx, cz, HW_R, 45)
    d.set(x, y, z, "potted_fern")
    x, z = rim(cx, cz, HW_R, 270)
    d.set(x, y, z, "chiseled_bookshelf[facing=south,slot_0_occupied=true,slot_1_occupied=false,"
                   "slot_2_occupied=true,slot_3_occupied=true,slot_4_occupied=true,slot_5_occupied=false]")
    d.rug(cx - 6, cz - 1, cx - 5, cz + 1, y, ("green_carpet", "green_carpet"), "plain")
    d.rug(cx + 5, cz - 1, cx + 6, cz + 1, y, ("green_carpet", "green_carpet"), "plain")


def hw_library(rel, L):
    d = Design("Hearthwood", rel, HW_SIZE, gy=1, paving="gravel")
    cx, cz = HW_C
    # Radcliffe Square: cobbled setts round the rotunda
    for x, z in disk(cx, cz, 12):
        d.set(x, 1, z, "cobblestone" if (x + z) % 3 else "andesite")
    hw_rotunda(d, L)
    if L >= 3:
        hw_square(d, L)
    if L >= 4:
        hw_range(d, L, west=True)
        hw_range(d, L, west=False)
    if L >= 5:
        hw_south_range(d)
        hw_screen(d)
    for tx in HW_TX:
        d.reserve(tx, 1, HW_TZ, tx + HW_TW - 1, 34, HW_TZ + HW_TW - 1)
        d.child_hut(tx + HW_WHUT[0], 1 + HW_WHUT[1], HW_TZ + HW_WHUT[2], WING)
    return d


def hw_square(d, L):
    """L3: iron railing ring on a stone curb round the rotunda, gaps north and south, four lamp standards."""
    cx, cz = HW_C
    for x, z in ring(cx, cz, 11):
        a = ang(cx, cz, x, z)
        if adiff(a, 270) < 9 or adiff(a, 90) < 9:
            continue
        d.set(x, 2, z, "stone_bricks")
        d.set(x, 3, z, "iron_bars")
    for x, z in ((14, 12), (30, 12), (14, 32), (30, 32)):
        lamp_post(d, x, z, 2, "stone_bricks", fence("dark_oak_fence"), h=2)
    for x, z, f in ((19, 11, "south"), (25, 11, "south")):
        d.chair(x, 2, z, "north", "dark_oak", sit=False)


def hw_range(d, L, west):
    pass


def hw_south_range(d):
    pass


def hw_screen(d):
    pass


# ------------------------------------------------------------------------------------------------ registry
LIBRARY = {"Hearthwood": hw_library}
LIBRARY_WING = {"Hearthwood": hw_wing}


@design("greatlibrary")
def greatlibrary(pack, rel, L):
    return LIBRARY[pack](rel, L)


@design("greatlibrarywing")
def greatlibrarywing(pack, rel, L):
    return LIBRARY_WING[pack](rel, L)
