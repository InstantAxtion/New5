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


def dome(d, cx, cz, y0, R, H, block, rib=None, nrib=16, hole=0.0, stairs=None):
    """Solid-shell dome on the circle of radius R whose foot is at y0, H high; ribs every 360/nrib degrees;
    cells within `hole` of the centre stay open (for a lantern). With `stairs`, each step of the outer face
    is smoothed by a stair facing up-slope."""
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
        if stairs and not isrib and dd > hole + 0.6:
            dx, dz = x - cx, z - cz
            out = ("east" if dx > 0 else "west") if abs(dx) >= abs(dz) else ("south" if dz > 0 else "north")
            ox, oz = D4[out]
            ix, iz = D4[OPP[out]]
            if tops.get((x + ox, z + oz), y0 - 1) < t and tops.get((x + ix, z + iz), t + 1) > t:
                d.set(x, t + 1, z, stair(stairs, OPP[out]))
    return max(tops.values())


# ================================================================================================ HEARTHWOOD
HW_SIZE = (45, 52, 45)
HW_C = (22, 22)
HW_R = 8
HW_TX, HW_TZ, HW_TW = (1, 37), 1, 7          # book-stack towers (wings): x origins, z origin, footprint
HW_WHUT = (5, 1, 1)                           # wing hut, tower-local
HW_WTOP = {1: 5, 2: 9, 3: 13, 4: 17, 5: 25}   # tower roof slab (local y)
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
    # ---- storey 5 (L5): map and globe room
    if L >= 5:
        y = 18
        d.set(3, y, 3, fence("dark_oak_fence"))
        d.set(3, y + 1, 3, "lime_stained_glass")
        d.set(5, y, 1, "chest[facing=west,type=single,waterlogged=false]")
        d.set(5, y, 2, "chest[facing=west,type=single,waterlogged=false]")
        d.set(5, y + 1, 4, "blue_wall_banner[facing=west]")
        d.set(2, y, 1, slab("spruce_slab", "top"))
        d.set(3, y, 1, slab("spruce_slab", "top"))
        d.set(2, y + 1, 1, "white_carpet")
        d.chair(2, y, 2, "south", "spruce", sit=False)
        d.set(5, y, 5, "potted_fern")
        d.rug(2, 4, 4, 5, y, ("light_blue_carpet",), "plain")
        d.lamp(4, y + 2, 3)
    # ---- storey 6 (L5): observatory (telescope at the window, star-chart table, armillary)
    if L >= 5:
        y = 22
        d.set(3, y, 1, fence("dark_oak_fence"))
        d.set(3, y + 1, 1, "lightning_rod[facing=north,powered=false,waterlogged=false]")
        d.item(4, y, 4, "cartography_table")
        d.chair(4, y, 3, "north", "dark_oak", sit=False)
        d.set(5, y, 1, "chiseled_bookshelf[facing=west,slot_0_occupied=true,slot_1_occupied=false,"
                       "slot_2_occupied=true,slot_3_occupied=true,slot_4_occupied=false,slot_5_occupied=false]")
        d.set(2, y, 5, "candle[candles=4,lit=false,waterlogged=false]")
        d.set(5, y, 5, "spruce_slab[type=top,waterlogged=false]")
        d.set(5, y + 1, 5, "end_rod[facing=up]")
        d.rug(2, 3, 3, 3, y, ("black_carpet",), "plain")
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
    """Radcliffe-Camera-like rotunda. Floor on the ground (y=1), ground storey y=2..8, gallery floor y=9,
    upper storey y=10..16, entablature 17, balustrade 18, drum 18..23, dome from 25 (L3+)."""
    cx, cz = HW_C
    R = HW_R
    rg = ring(cx, cz, R)
    inn = interior(cx, cz, R)
    for x, z in disk(cx, cz, 9.3):
        d.set(x, 1, z, "stone_bricks")
    for x, z in inn:
        dd = math.hypot(x - cx, z - cz)
        d.set(x, 1, z, "polished_deepslate" if int(dd + 0.5) in (2, 5) else "calcite")
    # ground storey: rusticated walls, arched bays every 45 degrees (north bay = entrance)
    for x, z in rg:
        for y in range(2, 9):
            d.set(x, y, z, HQ if y % 2 == 0 else HS)
        a = ang(cx, cz, x, z)
        bay = min(range(8), key=lambda k: adiff(a, k * 45))
        if adiff(a, bay * 45) * math.pi / 180 * R < 1.3 and bay != 6:
            for y in range(3, 7):
                d.set(x, y, z, "glass_pane")
            d.set(x, 7, z, HC)
    d.door(22, 2, 14, "south", "dark_oak")
    for y in (4, 5, 6):
        d.set(22, y, 14, "glass_pane")
    d.set(22, 7, 14, HC)
    for x in (21, 23):                                 # entrance surround with a little pediment
        for y in range(2, 7):
            d.set(x, y, 13, HQ if y < 6 else HC)
    d.set(22, 7, 13, slab("smooth_sandstone_slab", "top"))
    d.set(21, 7, 13, stair("sandstone_stairs", "east"))
    d.set(23, 7, 13, stair("sandstone_stairs", "west"))
    d.set(22, 8, 13, slab("smooth_sandstone_slab"))
    for x, z in disk(cx, cz, 9):                       # cornice
        if not inside(cx, cz, x, z, R):
            d.set(x, 9, z, slab("smooth_sandstone_slab", "top"))
    for x, z in rg:
        d.set(x, 9, z, HQ)
    hw_rotunda_ground(d, L)
    if L == 1:                                         # balustrade and a temporary low lead dome with a lantern
        for x, z in disk(cx, cz, 9):
            if not inside(cx, cz, x, z, R):
                a = ang(cx, cz, x, z)
                pier = min(adiff(a, 22.5 + 45 * k) for k in range(8)) * math.pi / 180 * 9 < 1.0
                d.set(x, 10, z, HQ if pier else wallb("sandstone_wall"))
        for x, z in rg:
            d.set(x, 10, z, HS)
        top = dome(d, cx, cz, 11, R - 1, 3, "deepslate_tiles", "polished_deepslate", 16,
                   stairs="deepslate_tile_stairs")
        d.set(cx, top + 1, cz, HQ)
        d.set(cx, top + 2, cz, wallb("sandstone_wall"))
        d.set(cx, top + 3, cz, lantern(False))
        chandelier(d, cx, cz, top - 1, 7)
        return
    # ---- L2+: upper storey with pilasters, tall windows, entablature and balustrade
    for x, z in rg:
        for y in range(10, 17):
            d.set(x, y, z, HS)
        a = ang(cx, cz, x, z)
        bay = min(range(8), key=lambda k: adiff(a, k * 45))
        if adiff(a, bay * 45) * math.pi / 180 * R < 0.9:
            for y in range(11, 15):
                d.set(x, y, z, "glass_pane")
            d.set(x, 15, z, HC)
    for x, z in disk(cx, cz, 9):
        if inside(cx, cz, x, z, R):
            continue
        a = ang(cx, cz, x, z)
        pil = min(adiff(a, 22.5 + 45 * k) for k in range(8)) * math.pi / 180 * 9 < 1.0
        if pil:
            d.set(x, 10, z, HQ)
            for y in range(11, 16):
                d.set(x, y, z, wallb("sandstone_wall"))
            d.set(x, 16, z, HC)
        d.set(x, 17, z, HQ)
        d.set(x, 18, z, HQ if pil else wallb("sandstone_wall"))
    for x, z in rg:
        d.set(x, 17, z, HQ)
    hw_gallery(d, L)
    if L == 2:
        top = dome(d, cx, cz, 18, R - 1, 3, "deepslate_tiles", "polished_deepslate", 16,
                   stairs="deepslate_tile_stairs")
        for x, z in rg:
            d.set(x, 18, z, HS)
        d.set(cx, top + 1, cz, HQ)
        d.set(cx, top + 2, cz, wallb("sandstone_wall"))
        d.set(cx, top + 3, cz, lantern(False))
        chandelier(d, cx, cz, top - 1, 6)
        return
    # ---- L3+: drum, ribbed lead dome, lantern
    for x, z in inn:
        if not inside(cx, cz, x, z, 6):
            d.set(x, 17, z, "dark_oak_planks")
    for x, z in ring(cx, cz, 7):
        for y in range(18, 24):
            d.set(x, y, z, HS)
        a = ang(cx, cz, x, z)
        if min(adiff(a, 22.5 + 45 * k) for k in range(8)) * math.pi / 180 * 7 < 0.8:
            for y in (19, 20, 21):
                d.set(x, y, z, "glass_pane")
            d.set(x, 22, z, HC)
        d.set(x, 24, z, HQ)
    for x, z in disk(cx, cz, 8):
        if not inside(cx, cz, x, z, 7):
            d.set(x, 24, z, slab("smooth_sandstone_slab", "top"))
    top = dome(d, cx, cz, 25, 7, 8, "deepslate_tiles", "polished_deepslate", 8, hole=1.5,
               stairs="deepslate_tile_stairs")
    for dx in (-1, 0, 1):                              # lantern
        for dz in (-1, 0, 1):
            if (dx, dz) == (0, 0):
                continue
            for y in range(top, top + 3):
                d.set(cx + dx, y, cz + dz, HQ if dx and dz else "glass_pane")
            d.set(cx + dx, top + 3, cz + dz, HQ)
            d.set(cx + dx, top + 4, cz + dz, slab("smooth_sandstone_slab"))
    for y in range(top - 1, top + 3):
        d.set(cx, y, cz, AIR)
    d.set(cx, top + 3, cz, HQ)
    d.set(cx, top + 4, cz, HQ)
    d.set(cx, top + 5, cz, wallb("sandstone_wall"))
    d.set(cx, top + 6, cz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    chandelier(d, cx, cz, top + 2, 6)
    for dx, dz in D4.values():                         # corona of lights hanging in the well
        d.set(cx + dx, 12, cz + dz, slab("dark_oak_slab", "top"))
        d.set(cx + dx * 2, 12, cz + dz * 2, slab("dark_oak_slab", "top"))
        d.set(cx + dx * 2, 11, cz + dz * 2, lantern(True))


def hw_rotunda_ground(d, L):
    """Ground-floor reading room (walk y=2): circular issue desk, window desks, shelf piers, the book stair (L2+)."""
    cx, cz = HW_C
    y = 2
    d.hut(24, y, 16, "north")
    for dx in (-1, 0, 1):                              # circular issue desk, open to the south
        for dz in (-1, 0, 1):
            if (dx, dz) in ((0, 0), (0, 1)):
                continue
            d.set(cx + dx, y, cz + dz, slab("dark_oak_slab", "top") if (dx, dz) != (0, -1) else "dark_oak_planks")
    d.chair(cx, y, cz, "south", "dark_oak")
    d.set(cx - 1, y + 1, cz - 1, "candle[candles=3,lit=false,waterlogged=false]")
    d.set(cx + 1, y + 1, cz - 1, "potted_red_tulip")
    d.set(cx, y + 1, cz - 1, "chiseled_bookshelf[facing=north,slot_0_occupied=true,slot_1_occupied=true,"
                             "slot_2_occupied=true,slot_3_occupied=true,slot_4_occupied=false,slot_5_occupied=true]")
    d.rug(cx, cz - 7, cx, cz - 3, y, ("red_carpet",), "plain")
    d.rug(cx - 2, cz - 2, cx + 2, cz + 2, y, ("blue_carpet", "blue_carpet"))
    for a, side in ((0, "west"), (45, "west"), (135, "east"), (180, "east"), (225, "east"), (315, "west")):
        x, z = rim(cx, cz, HW_R, a)
        desk(d, x, y, z, side, "dark_oak",
             light="candle[candles=1,lit=false,waterlogged=false]" if a in (0, 180) else None)
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
    for i in range(8):                                 # book stair: steps rise east, shelves fill the stringer
        x = 18 + i
        d.set(x, y + i, 28, stair("dark_oak_stairs", "east"))
        for yy in range(y, y + i):
            d.bookshelf(x, yy, 28)


def hw_gallery(d, L):
    """Gallery ring (walk y=10) around the open well: shelf piers, window desks, globe, railing."""
    cx, cz = HW_C
    y = 10
    inn = interior(cx, cz, HW_R)
    for x, z in inn:
        dd = math.hypot(x - cx, z - cz)
        d.set(x, 9, z, AIR if dd <= 3.45 else "dark_oak_planks")
    for x in range(18, 25):                            # stair well
        d.set(x, 9, 28, AIR)
    for x, z in inn:                                   # railing round the well
        dd = math.hypot(x - cx, z - cz)
        if dd > 3.45 and any(math.hypot(x + dx - cx, z + dz - cz) <= 3.45 for dx, dz in D4.values()):
            d.set(x, y, z, fence("dark_oak_fence"))
    for x in range(18, 25):
        d.set(x, y, 27, fence("dark_oak_fence"))
    for x in range(20, 25):                            # low book wall behind the stair well
        d.bookshelf(x, y, 29)
    for a in (22.5, 157.5, 202.5, 247.5, 292.5, 337.5):
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
    d.rug(cx - 6, cz - 1, cx - 5, cz + 1, y, ("green_carpet",), "plain")
    d.rug(cx + 5, cz - 1, cx + 6, cz + 1, y, ("green_carpet",), "plain")


def hw_library(rel, L):
    d = Design("Hearthwood", rel, HW_SIZE, gy=1, paving="gravel")
    cx, cz = HW_C
    if L >= 3:                                         # the quad lawn
        for x in range(10, 35):
            for z in range(9, 36):
                d.set(x, 1, z, "grass_block[snowy=false]")
    for x, z in disk(cx, cz, 12):                      # Radcliffe Square setts
        d.set(x, 1, z, "cobblestone" if (x + z) % 3 else "andesite")
    for z in range(0, 11):                             # walk from the street
        for x in (21, 22, 23):
            d.set(x, 1, z, "stone_bricks")
    hw_rotunda(d, L)
    if L >= 3:
        hw_square(d, L)
        hw_range(d, L, west=True)
    if L >= 4:
        hw_range(d, L, west=False)
        hw_garden(d, L)
    if L >= 5:
        hw_south_range(d)
        hw_screen(d)
        hw_forecourt(d)
    for tx in HW_TX:
        d.reserve(tx, 1, HW_TZ, tx + HW_TW - 1, 34, HW_TZ + HW_TW - 1)
        d.child_hut(tx + HW_WHUT[0], 1 + HW_WHUT[1], HW_TZ + HW_WHUT[2], WING)
    return d


def hw_square(d, L):
    """L3: iron railing on a stone curb round the rotunda with four gaps, four lamp standards, two benches."""
    cx, cz = HW_C
    for x, z in ring(cx, cz, 11):
        a = ang(cx, cz, x, z)
        if min(adiff(a, k * 90) for k in range(4)) < 9:
            continue
        d.set(x, 2, z, "stone_bricks")
        d.set(x, 3, z, "iron_bars")
    for x, z in ((14, 12), (30, 12), (14, 32), (30, 32)):
        lamp_post(d, x, z, 2, "stone_bricks", fence("dark_oak_fence"), h=2)
    for x in (18, 26):
        d.chair(x, 2, 10, "north", "dark_oak", sit=False)
        d.chair(x + 1, 2, 10, "north", "dark_oak", sit=False)


def hw_range(d, L, west):
    """Gothic library range (Bodleian Old Schools): sandstone, buttresses, lancets, steep slate gable.
    West: Divinity School below, Duke Humfrey's Library above. East: lecture room below, map room above.
    The west range is single-storey at L3 and gets its upper floor at L4."""
    x1, x2 = (1, 9) if west else (35, 43)
    qx, ox = (x2, x1) if west else (x1, x2)           # quad-side and outer wall
    qo = 1 if west else -1                             # step from the quad wall out into the quad
    z1, z2 = 10, 34
    two = L >= 4
    top = 12 if two else 6
    d.fill(x1 + 1, 1, z1 + 1, x2 - 1, 1, z2 - 1, "polished_andesite")
    for x in range(x1 + 1, x2):
        for z in range(z1 + 1, z2):
            if (x + z) % 2 == 0:
                d.set(x, 1, z, "stone_bricks")
    d.box(x1, 2, z1, x2, top, z2, HS)
    for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        for y in range(2, top + 1):
            d.set(x, y, z, HQ)
    for x in range(x1, x2 + 1):                        # plinth and string course
        for z in (z1, z2):
            d.set(x, 2, z, "stone_bricks")
    for z in range(z1, z2 + 1):
        for x in (x1, x2):
            d.set(x, 2, z, "stone_bricks")
    if two:
        d.fill(x1 + 1, 7, z1 + 1, x2 - 1, 7, z2 - 1, "dark_oak_planks")
        for x in range(x1, x2 + 1):
            for z in (z1, z2):
                d.set(x, 7, z, HQ)
        for z in range(z1, z2 + 1):
            for x in (x1, x2):
                d.set(x, 7, z, HQ)
    # buttresses on the quad side
    for z in (14, 18, 26, 30):
        for y in range(2, top):
            d.set(qx + qo, y, z, HQ if y < top - 1 else stair("sandstone_stairs", "west" if west else "east"))
        d.set(qx + qo, 2, z, "stone_bricks")
    # windows: lancets on both long sides, a big window at each storey of the north gable
    storeys = ((3, 5), (9, 11)) if two else ((3, 5),)
    for y1, y2 in storeys:
        for z in (12, 16, 28, 32):
            hw_lancet(d, qx, z, y1, y2, None)
        for z in (12, 16, 20, 24, 28, 32):
            hw_lancet(d, ox, z, y1, y2, None)
        mx = (x1 + x2) // 2
        for x in (mx - 1, mx, mx + 1):
            for y in range(y1, y2 + 1):
                d.set(x, y, z1, "glass_pane")
        d.set(mx, y2 + 1, z1, HC)
    for z in (20, 24):
        hw_lancet(d, qx, z, 3, 5, None)
    if two:                                            # great window over the door
        for z in (21, 22, 23):
            for y in range(9, 12):
                d.set(qx, y, z, "glass_pane")
        d.set(qx, 12, 22, HC)
    d.door(qx, 2, 22, "east" if west else "west", "dark_oak")
    d.set(qx, 4, 22, HC)
    # roof
    ridge = d.gable(x1, z1, x2, z2, top + 1, "z", stairs="deepslate_tile_stairs", ridge="deepslate_tile_slab",
                    end=HS, overhang=1)
    for z in (z1, z2):
        d.set((x1 + x2) // 2, ridge + 1, z, wallb("sandstone_wall"))
        d.set((x1 + x2) // 2, ridge + 2, z, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    if west:
        hw_divinity(d, L, two)
        if two:
            hw_humfrey(d)
    else:
        hw_lecture(d)
        hw_maproom(d)


def hw_range_stair(d, sx, inner):
    """Stair up the outer wall at the south end of a range (walk 2 -> 8), shelves under it, rail beside the well."""
    for i in range(6):
        z = 33 - i
        d.set(sx, 2 + i, z, stair("dark_oak_stairs", "north"))
        for yy in range(2, 2 + i):
            d.bookshelf(sx, yy, z)
        if i < 5:
            d.set(sx, 7, z, AIR)
    for z in range(29, 34):
        d.set(inner, 8, z, fence("dark_oak_fence"))


def hw_divinity(d, L, two):
    """West range ground floor (walk 2): the Divinity School as an exhibition hall – lecterns with open books,
    benches along the walls, a long carpet, hanging lights."""
    y = 2
    for z in (13, 17, 27, 31):
        d.item(5, y, z, "lectern[facing=north,has_book=true,powered=false]")
        d.set(5, y, z + 1, "red_carpet")
    d.rug(4, 11, 6, 33, y, ("red_carpet", "yellow_carpet"))
    for z in (12, 13, 15, 16, 20, 24, 28, 29, 31, 32):
        if not two or z < 29:
            d.chair(2, y, z, "west", "dark_oak")
    for z in (12, 13, 15, 16, 28, 29, 31, 32):
        d.chair(8, y, z, "east", "dark_oak")
    for z in (14, 18, 26, 30):
        d.set(8, y + 2, z, "yellow_wall_banner[facing=west]")
        d.set(2, y + 2, z, "yellow_wall_banner[facing=east]")
    for z in (20, 24):
        d.set(8, y, z, "potted_fern")
    d.set(2, y, 22, "potted_fern")
    d.bookshelf(2, y, 21, 2)
    d.bookshelf(2, y, 23, 2)
    if two:
        for z in (13, 19, 25):
            d.lamp(5, 6, z)
        hw_range_stair(d, 2, 3)
    else:
        for z in (13, 19, 25, 31):
            chandelier(d, 5, z, 9, 6)


def hw_humfrey(d):
    """West range upper floor (walk 8): Duke Humfrey's Library – book presses between the windows with desks."""
    y = 8
    for z in (14, 18, 22, 26):                         # presses on the outer side
        d.bookshelf(2, y, z, 2)
        d.bookshelf(3, y, z, 2)
    for z in (12, 16, 20, 24):
        desk(d, 2, y, z, "east", "dark_oak", light="candle[candles=1,lit=false,waterlogged=false]"
             if z in (12, 20) else None)
    for z in (14, 18, 26, 30):                         # presses on the quad side
        d.bookshelf(8, y, z, 2)
        d.bookshelf(7, y, z, 2)
    for z in (12, 16, 28, 32):
        desk(d, 8, y, z, "west", "dark_oak")
    d.rug(4, 12, 6, 32, y, ("brown_carpet",), "plain")
    for z in (20, 22, 24):                             # reading table under the great window
        d.set(7, y, z, slab("spruce_slab", "top"))
    d.chair(7, y, 21, "north", "spruce")
    d.chair(7, y, 23, "south", "spruce")
    d.set(7, y + 1, 22, "lantern[hanging=false,waterlogged=false]")
    for z in (11, 33):
        d.set(5, y, z, "potted_fern")
    for z in (12, 18, 24, 30):                         # tie beams with lamps under the roof
        d.fill(2, 13, z, 8, 13, z, log("dark_oak_log", "x"))
        d.set(5, 12, z, CHAIN)
        d.set(5, 11, z, lantern(True))


def hw_lecture(d):
    """East range ground floor (walk 2): lecture room – rows of benches facing the lectern and blackboard."""
    y = 2
    for z in (13, 16, 19, 22):
        for x in (37, 38, 40, 41):
            d.chair(x, y, z, "north", "oak")
    d.item(39, y, 28, "lectern[facing=north,has_book=true,powered=false]")
    d.fill(37, 3, 34, 40, 5, 34, "black_terracotta")      # blackboard set into the end wall
    d.fill(37, 2, 33, 40, 2, 33, slab("dark_oak_slab", "top"))   # chalk ledge / demonstrator's bench
    d.set(37, 3, 33, "potted_red_tulip")
    d.set(40, 3, 33, "candle[candles=3,lit=false,waterlogged=false]")
    d.chair(37, y, 30, "west", "oak")
    d.set(36, 2, 11, "potted_fern")
    d.set(41, 2, 11, "barrel[facing=up,open=false]")
    d.set(40, 2, 11, "barrel[facing=up,open=false]")
    d.rug(39, 11, 39, 26, y, ("gray_carpet",), "plain")
    for z in (14, 20, 26):
        d.lamp(39, 6, z)
    hw_range_stair(d, 42, 41)


def hw_maproom(d):
    """East range upper floor (walk 8): map room and archive – map tables, plan chests, globes, cartographers."""
    y = 8
    for z in (13, 14, 15):                             # big map table
        for x in (38, 39, 40):
            d.set(x, y, z, slab("spruce_slab", "top") if (x + z) % 2 else "dark_oak_planks")
    d.set(39, y + 1, 14, "white_carpet")
    for x, z, s in ((37, 14, "east"), (41, 14, "west")):
        d.chair(x, y, z, s, "spruce")
    d.item(36, y, 18, "cartography_table")
    d.item(36, y, 24, "cartography_table")
    d.chair(37, y, 18, "east", "spruce")
    d.chair(37, y, 24, "east", "spruce")
    for z in (19, 20, 21, 25, 26, 27):                 # plan chests along the walls
        d.set(36, y, z, "chest[facing=east,type=single,waterlogged=false]")
    for z in (17, 18, 20, 22, 24, 26):
        d.bookshelf(42, y, z, 2)
    for x, z in ((40, 20), (40, 24)):                  # globes
        d.set(x, y, z, fence("dark_oak_fence"))
        d.set(x, y + 1, z, "light_blue_stained_glass" if z == 20 else "lime_stained_glass")
    d.rug(38, 17, 40, 27, y, ("light_blue_carpet", "blue_carpet"))
    d.set(36, y, 11, "potted_fern")
    d.set(42, y, 11, "barrel[facing=up,open=false]")
    for z in (12, 18, 24, 30):
        d.fill(36, 13, z, 42, 13, z, log("dark_oak_log", "x"))
        d.set(39, 12, z, CHAIN)
        d.set(39, 11, z, lantern(True))


def hw_garden(d, L):
    """L4: the quad garden – four clipped trees, flower borders, benches facing the rotunda."""
    for x, z in ((12, 11), (32, 11), (12, 33), (32, 33)):
        tree(d, x, z, 2, "oak_log", "oak_leaves", h=3, r=2)
    for x, z, b in ((16, 34, "north"), (17, 34, "north"), (27, 34, "north"), (28, 34, "north")):
        d.chair(x, 2, z, "south", "dark_oak", sit=False)
    for x in range(14, 31, 2):
        d.set(x, 2, 35, ("rose_bush[half=lower]" if x % 4 else "peony[half=lower]"))
        d.set(x, 3, 35, ("rose_bush[half=upper]" if x % 4 else "peony[half=upper]"))


def hw_south_range(d):
    """L5: two-storey south range with the gate tower (Tower of the Five Orders): exam hall and long gallery
    west, tea room and senior common room east; porter's lodge, muniment room, bindery and treasury in the
    tower."""
    z1, z2 = 37, 43
    d.fill(2, 1, z1 + 1, 42, 1, z2 - 1, "oak_planks")
    d.box(1, 2, z1, 43, 12, z2, HS)
    d.fill(2, 7, z1 + 1, 42, 7, z2 - 1, "dark_oak_planks")
    for x in range(1, 44):
        for z in (z1, z2):
            d.set(x, 2, z, "stone_bricks")
            d.set(x, 7, z, HQ)
    for z in range(z1, z2 + 1):
        for x in (1, 43):
            d.set(x, 2, z, "stone_bricks")
            d.set(x, 7, z, HQ)
    d.gable(1, z1, 43, z2, 13, "x", stairs="deepslate_tile_stairs", ridge="deepslate_tile_slab", end=HS, overhang=1)
    for x in (4, 8, 12, 16, 28, 32, 36, 40):
        for z in (z1, z2):
            hw_lancet(d, x, z, 3, 5, None)
            hw_lancet(d, x, z, 9, 11, None)
    for x in (10, 34):                                 # dormers lighting the upper floors
        for dx in (-1, 0, 1):
            d.set(x + dx, 13, z1 - 1, HS)
            d.set(x + dx, 14, z1 - 1, HS)
        d.set(x, 13, z1 - 1, "glass_pane")
        d.set(x - 1, 15, z1 - 1, stair("deepslate_tile_stairs", "east"))
        d.set(x + 1, 15, z1 - 1, stair("deepslate_tile_stairs", "west"))
        d.set(x, 15, z1 - 1, "deepslate_tiles")
        d.set(x, 16, z1 - 1, slab("deepslate_tile_slab"))
    # partitions to the tower
    d.fill(17, 2, z1 + 1, 17, 12, z2 - 1, HS)
    d.fill(27, 2, z1 + 1, 27, 12, z2 - 1, HS)
    d.door(13, 2, z1, "south", "dark_oak")
    d.door(31, 2, z1, "south", "dark_oak")
    for x in (1, 43):
        for z in (z1 + 2, z1 + 4):
            hw_lancet(d, x, z, 3, 5, None)
            hw_lancet(d, x, z, 9, 11, None)
    # common-room chimney stack against the east gable
    for y in range(2, 19):
        for z in (39, 40, 41):
            d.set(44, y, z, "bricks")
    for y in range(13, 19):
        d.set(43, y, 40, "bricks")
    for z in (39, 41):
        d.set(44, 19, z, "bricks")
    hw_exam(d)
    hw_tearoom(d)
    hw_gallery_south(d)
    hw_common_room(d)
    hw_gate_tower(d)


def hw_south_stair(d, x0, step):
    """Stair along the south wall (z=42) from walk 2 up to walk 8, rising toward +x (step=1) or -x (step=-1)."""
    for i in range(6):
        x = x0 + step * i
        d.set(x, 2 + i, 42, stair("dark_oak_stairs", "east" if step > 0 else "west"))
        for yy in range(2, 2 + i):
            d.bookshelf(x, yy, 42)
        if i < 5:
            d.set(x, 7, 42, AIR)
            d.set(x, 8, 41, fence("dark_oak_fence"))


def hw_gallery_south(d):
    """Upper floor west (walk 8, x 2..16): the long picture gallery – portraits (banners), busts on plinths,
    benches down the middle, a cabinet of curiosities."""
    y = 8
    hw_south_stair(d, 2, 1)
    for x, c in ((4, "red"), (8, "blue"), (12, "green"), (15, "purple")):
        d.set(x, y + 1, 38, f"{c}_wall_banner[facing=south]")
    for x in (6, 10, 14):                              # busts on plinths
        d.set(x, y, 38, "polished_andesite")
        d.set(x, y + 1, 38, "skeleton_skull[rotation=8]")
    for x in (7, 8, 11, 12):
        d.chair(x, y, 40, "north", "dark_oak")
    d.rug(3, 39, 16, 40, y, ("red_carpet",), "plain")
    d.set(16, y, 42, "chiseled_bookshelf[facing=north,slot_0_occupied=true,slot_1_occupied=true,"
                     "slot_2_occupied=false,slot_3_occupied=true,slot_4_occupied=true,slot_5_occupied=true]")
    d.set(15, y, 42, "glass")
    d.set(14, y, 42, "glass")
    d.set(16, y, 38, "potted_fern")
    for x in (5, 9, 13):
        d.lamp(x, 12, 40)


def hw_common_room(d):
    """Upper floor east (walk 8, x 28..42): senior common room – fireplace, armchairs, card tables, decanters."""
    y = 8
    hw_south_stair(d, 42, -1)
    d.set(42, y, 40, "campfire[facing=west,lit=true,signal_fire=false,waterlogged=false]")
    d.set(42, y, 39, "bricks")
    d.set(42, y, 41, "bricks")
    d.fill(42, y + 1, 39, 42, y + 1, 41, "bricks")
    d.set(43, y, 40, "bricks")
    d.chair(39, y, 39, "west", "dark_oak", arms=True)
    d.chair(39, y, 41, "west", "dark_oak", arms=False)
    d.set(40, y, 40, slab("dark_oak_slab", "top"))
    d.rug(38, 38, 41, 40, y, ("green_carpet", "lime_carpet"))
    for x in (30, 34):                                 # card tables
        d.table(x, y, 39, "dark_oak", "post")
        d.chair(x - 1, y, 39, "west", "dark_oak")
        d.chair(x + 1, y, 39, "east", "dark_oak")
        d.chair(x, y, 40, "south", "dark_oak")
    d.counter(28, 38, 28, 41, y, "dark_oak_slab")      # sideboard with decanters
    d.set(28, y + 1, 38, "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]")
    d.set(28, y + 1, 40, "potted_red_tulip")
    d.set(28, y + 1, 41, "candle[candles=3,lit=false,waterlogged=false]")
    d.bookshelf(36, y, 38, 2)
    d.bookshelf(37, y, 38, 2)
    for x in (31, 38):
        d.lamp(x, 12, 40)


def hw_exam(d):
    """Exam Schools hall (walk 2, x 2..16, z 38..42): rows of single desks, invigilator's desk, clock."""
    y = 2
    for x in (3, 6, 9):
        for z in (39, 41):
            desk(d, x, y, z, "east", "oak")
    d.set(15, y, 40, slab("dark_oak_slab", "top"))
    d.set(15, y, 39, slab("dark_oak_slab", "top"))
    d.chair(16, y, 40, "east", "dark_oak")
    d.set(15, y + 1, 39, "candle[candles=2,lit=false,waterlogged=false]")
    d.set(16, y + 2, 42, "bell[attachment=single_wall,facing=north,powered=false]")
    d.rug(12, 38, 13, 42, y, ("light_gray_carpet",), "plain")
    d.set(2, y, 38, "potted_fern")
    d.set(16, y, 38, "barrel[facing=up,open=false]")
    for x in (5, 11):
        d.lamp(x, 6, 40)


def hw_tearoom(d):
    """Tea room (walk 2, x 28..42, z 38..42): counter with a stove and kettle, small tables, dresser."""
    y = 2
    d.counter(38, 38, 42, 38, y, "spruce_slab")
    d.item(42, y, 39, "smoker", "west")
    d.set(42, y, 40, "water_cauldron[level=3]")
    d.set(42, y, 41, "barrel[facing=up,open=false]")
    d.set(39, y + 1, 38, "potted_red_tulip")
    d.set(41, y + 1, 38, "candle[candles=1,lit=false,waterlogged=false]")
    for x, z in ((30, 40), (34, 40)):
        d.table(x, y, z, "dark_oak", "post")
        d.chair(x - 1, y, z, "west", "dark_oak")
        d.chair(x + 1, y, z, "east", "dark_oak")
        d.chair(x, y, z + 1, "south", "dark_oak")
    d.rug(29, 39, 35, 41, y, ("red_carpet", "white_carpet"), "check")
    for x in (29, 30):
        d.set(x, y, 42, slab("dark_oak_slab", "top"))
        d.set(x, y + 1, 42, "flower_pot")
    d.set(28, y, 38, "potted_fern")
    for x in (31, 38):
        d.lamp(x, 6, 40)


def hw_gate_tower(d):
    """Gate tower x 18..26, z 35..43 with a passage at x=22; porter's lodge west with the ladder."""
    x1, x2, z1, z2 = 18, 26, 35, 43
    top = 25
    d.fill(x1 + 1, 1, z1 + 1, x2 - 1, 1, z2 - 1, "stone_bricks")
    d.box(x1, 2, z1, x2, top, z2, HS)
    for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):      # corner turrets with ogee caps
        for y in range(2, top + 6):
            d.set(x, y, z, HQ)
        ox, oz = (1 if x == x2 else -1), (1 if z == z2 else -1)
        for y in range(top - 6, top + 5):
            d.set(x + ox, y, z, HS if y % 3 else HQ)
            d.set(x, y, z + oz, HS if y % 3 else HQ)
        d.set(x + ox, top + 5, z, stair("sandstone_stairs", "west" if ox > 0 else "east"))
        d.set(x, top + 5, z + oz, stair("sandstone_stairs", "north" if oz > 0 else "south"))
        d.set(x, top + 6, z, HQ)
        d.set(x, top + 7, z, wallb("sandstone_wall"))
        d.set(x, top + 8, z, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    d.fill(21, 21, z1 - 1, 23, 23, z1 - 1, "white_terracotta")     # clock face over the top window
    d.set(22, 22, z1 - 1, "black_terracotta")
    d.set(22, 23, z1 - 1, "black_terracotta")
    for F in (7, 13, 19):
        d.fill(x1 + 1, F, z1 + 1, x2 - 1, F, z2 - 1, "spruce_planks")
        for x in range(x1, x2 + 1):
            for z in (z1, z2):
                d.set(x, F, z, HQ)
    d.fill(x1 + 1, top, z1 + 1, x2 - 1, top, z2 - 1, "stone_bricks")
    d.hip(20, 37, 24, 41, top + 1, "deepslate_tile_stairs", "deepslate_tile_slab", overhang=0)   # leaded cap
    d.set(22, top + 4, 39, wallb("sandstone_wall"))
    d.set(22, top + 5, 39, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    for i in range(0, 9):                              # battlements
        for x, z in ((x1 + i, z1), (x1 + i, z2), (x1, z1 + i), (x2, z1 + i)):
            d.set(x, top + 1, z, HS)
            if i % 2 == 0:
                d.set(x, top + 2, z, slab("smooth_sandstone_slab"))
    # the five orders on the quad face: paired columns each storey
    for y1, y2 in ((2, 6), (8, 12), (14, 18), (20, 24)):
        for x in (19, 20, 24, 25):
            d.set(x, y1, z1 - 1, HQ)
            for y in range(y1 + 1, y2):
                d.set(x, y, z1 - 1, wallb("sandstone_wall"))
            d.set(x, y2, z1 - 1, HC)
    for y in (13, 19, 25):
        for x in range(19, 26):
            d.set(x, y, z1 - 1, slab("smooth_sandstone_slab", "top"))
    for yw in ((9, 11), (15, 17), (21, 23)):
        for x in (21, 22, 23):
            for y in range(yw[0], yw[1] + 1):
                d.set(x, y, z1, "glass_pane")
                d.set(x, y, z2, "glass_pane")
        d.set(22, yw[1] + 1, z1, HC)
    d.fill(21, 13, z1 - 1, 23, 14, z1 - 1, HC)            # carved royal arms panel
    # passage
    d.fill(21, 2, z1, 21, 6, z2, HS)
    d.fill(23, 2, z1, 23, 6, z2, HS)
    d.clear(22, 2, z1, 22, 5, z2)
    d.set(22, 6, z1, HC)
    d.set(22, 6, z2, HC)
    d.lamp(22, 5, 39)
    d.door(21, 2, 39, "east", "dark_oak")
    d.set(22, 1, 44, "stone_bricks")
    # porter's lodge (x 19..20): ladder, desk, key cabinet
    for y in range(2, 20):
        d.set(19, y, 42, ladder("north"))
    for F in (7, 13, 19):
        d.set(19, F, 42, ladder("north"))
    d.set(20, 2, 36, slab("dark_oak_slab", "top"))
    d.chair(20, 2, 37, "south", "dark_oak")
    d.set(19, 2, 36, "barrel[facing=up,open=false]")
    d.set(24, 2, 36, "potted_fern")
    d.set(25, 2, 42, "barrel[facing=up,open=false]")
    d.set(24, 2, 42, "barrel[facing=up,open=false]")
    d.set(25, 2, 36, "chest[facing=west,type=single,waterlogged=false]")
    d.door(23, 2, 41, "west", "dark_oak")
    d.lamp(20, 6, 39)
    d.lamp(25, 6, 39)
    # muniment room (walk 8): charters in chests, a clerk's desk
    y = 8
    for z in (36, 37, 38):
        d.set(25, y, z, "chest[facing=west,type=single,waterlogged=false]")
    for x in (22, 23, 24, 25):
        d.set(x, y, 42, "barrel[facing=north,open=false]")
    desk(d, 21, y, 36, "south", "dark_oak", light="candle[candles=2,lit=false,waterlogged=false]")
    d.rug(20, 38, 23, 40, y, ("brown_carpet", "orange_carpet"))
    d.bookshelf(19, y, 36, 2)
    d.lamp(22, 12, 39)
    # bindery (walk 14): bench, press, loom for headbands, glue pot
    y = 14
    d.item(25, y, 37, "crafting_table")
    d.item(25, y, 38, "loom", "west")
    d.item(25, y, 40, "anvil", "north")
    d.set(25, y, 41, "water_cauldron[level=3]")
    d.counter(20, 36, 23, 36, y, "spruce_slab")
    d.set(21, y + 1, 36, "brown_carpet")
    d.set(22, y + 1, 36, "white_carpet")
    d.chair(22, y, 37, "south", "spruce")
    d.set(20, y, 42, "barrel[facing=up,open=false]")
    d.set(21, y, 42, "barrel[facing=up,open=false]")
    d.lamp(22, 18, 39)
    # treasury of rare books (walk 20): glass cases, a lectern, a padded chair, chandelier
    y = 20
    for x, z in ((21, 37), (23, 37), (21, 41), (23, 41)):
        d.set(x, y, z, "dark_oak_planks")
        d.set(x, y + 1, z, "glass")
    d.item(25, y, 39, "lectern[facing=west,has_book=true,powered=false]")
    d.chair(20, y, 39, "west", "dark_oak", arms=True)
    d.bookshelf(25, y, 36, 2)
    d.bookshelf(25, y, 42, 2)
    d.rug(21, 38, 24, 40, y, ("purple_carpet", "magenta_carpet"))
    chandelier(d, 22, 39, 24, 23)


def hw_forecourt(d):
    """L5: the forecourt behind the screen – box hedges, two basins with spouts, lamp standards."""
    for x in list(range(8, 19)) + list(range(26, 37)):
        d.set(x, 2, 5, "oak_leaves[distance=1,persistent=true,waterlogged=false]")
        if x not in (8, 18, 26, 36):
            d.set(x, 3, 5, "oak_leaves[distance=1,persistent=true,waterlogged=false]")
    for bx in (15, 29):                                # basins
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if (dx, dz) == (0, 0):
                    d.set(bx, 1, 8, "water")
                    continue
                d.set(bx + dx, 2, 8 + dz, wallb("stone_brick_wall") if dx and dz else "stone_brick_slab[type=bottom,waterlogged=false]")
        d.set(bx, 2, 8, "stone_bricks")
        d.set(bx, 3, 8, wallb("sandstone_wall"))
        d.set(bx, 4, 8, HC)
    for x in (10, 34):
        lamp_post(d, x, 7, 2, "stone_bricks", fence("dark_oak_fence"), h=2)


def hw_screen(d):
    """L5: the street screen between the towers – stone dwarf wall with iron railings, gate piers, lamps."""
    z = 4
    for x in range(8, 37):
        if 20 <= x <= 24:
            continue
        d.set(x, 2, z, "stone_bricks")
        d.set(x, 3, z, "iron_bars" if (x - 8) % 4 else HQ)
        if (x - 8) % 4 == 0:
            d.set(x, 4, z, slab("smooth_sandstone_slab"))
    for x in (19, 25):
        for y in range(2, 5):
            d.set(x, y, z, HQ)
        d.set(x, 5, z, HC)
        d.set(x, 6, z, lantern(False))


# ------------------------------------------------------------------------------------------------ registry
LIBRARY = {"Hearthwood": hw_library}
LIBRARY_WING = {"Hearthwood": hw_wing}


@design("greatlibrary")
def greatlibrary(pack, rel, L):
    return LIBRARY[pack](rel, L)


@design("greatlibrarywing")
def greatlibrarywing(pack, rel, L):
    return LIBRARY_WING[pack](rel, L)
