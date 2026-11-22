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
    d.rug(cx, cz - 7, cx, cz - 4, y, ("red_carpet",), "plain")
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
    hw_hedges(d, L)
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


def hw_hedges(d, L):
    """Clipped yew hedges along the outer walls of the ranges (the plot edge under their eaves)."""
    yew = "spruce_leaves[distance=1,persistent=true,waterlogged=false]"
    if L >= 3:
        for z in range(9, 36):
            d.set(0, 2, z, yew)
    if L >= 4:
        for z in range(9, 36):
            d.set(44, 2, z, yew)
    if L >= 5:
        for x in range(1, 44):
            if x != 22:
                d.set(x, 2, 44, yew)
        for z in range(36, 44):
            d.set(0, 2, z, yew)
            d.set(44, 2, z, yew)


def hw_square(d, L):
    """L3: iron railing on a stone curb round the rotunda with four gaps, four lamp standards, two benches."""
    cx, cz = HW_C
    for x, z in ring(cx, cz, 10):
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
    d.rug(5, 11, 5, 33, y, ("red_carpet",), "plain")
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
    d.rug(22, 38, 23, 40, y, ("purple_carpet",), "plain")
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


# ================================================================================================ NEOTERRA
NT_SIZE = (43, 40, 41)
NT_TX, NT_TZ, NT_TW = (1, 35), 1, 7          # glass book-stack towers (wings)
NT_WHUT = (5, 1, 1)
NT_SP = (34, 20)                              # book spiral centre
NT_SR = 5
W = "white_concrete"
G = "light_gray_concrete"
QS = "smooth_quartz_slab"
NT_HELIX = [(33, 19), (34, 19), (35, 19), (35, 20), (35, 21), (34, 21), (33, 21), (33, 20)]

COMMON = {
    "quartz_pillar": "white_concrete", "smooth_quartz": "white_concrete", "quartz_block": "white_concrete",
    "smooth_quartz_slab": "smooth_stone_slab", "smooth_quartz_stairs": "polished_diorite_stairs",
    "quartz_stairs": "polished_diorite_stairs", "quartz_slab": "smooth_stone_slab",
    "sea_lantern": "glowstone", "polished_blackstone": "polished_deepslate",
    "polished_blackstone_slab": "polished_deepslate_slab", "cut_copper": "orange_terracotta",
}


def nt_common(d):
    """Neoterra L1-3: quartz, sea lanterns and end rods give way to concrete, smooth stone, glowstone and
    lightning-rod posts (same shapes); the building visibly 'goes premium' with the L4-5 upgrade."""
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
        if props and any(k in new for k in ("_stairs", "_slab")):
            d.bp.set(x, y, z, "minecraft:" + new + "[" + ",".join(f"{k}={v}" for k, v in props.items()) + "]")
        else:
            d.bp.set(x, y, z, "minecraft:" + new)
    return d


def nt_wing(rel, L):
    """Glass book-stack tower: white corner fins, floor bands, blue-tinted glass, one room per storey linked by
    a ladder, a glowing crown."""
    d = Design("Neoterra", rel, (NT_TW, 34, NT_TW), gy=0, paving="smooth_stone")
    n, T = NT_TW - 1, 5 * L
    for y in range(1, T + 1):
        for i in range(n + 1):
            for x, z in ((i, 0), (i, n), (0, i), (n, i)):
                d.set(x, y, z, "light_blue_stained_glass_pane")
        for x, z in ((0, 0), (n, 0), (0, n), (n, n)):
            d.set(x, y, z, W)
    d.fill(1, 0, 1, n - 1, 0, n - 1, "polished_diorite")
    for F in range(5, T + 1, 5):
        d.fill(0, F, 0, n, F, n, W)
        if F < T:
            d.fill(1, F, 1, n - 1, F, n - 1, "smooth_stone")
    for y in range(1, T):                          # the ladder runs up a white service strip
        if L > 1 and y < T - 4 + 1:
            d.set(0, y, n - 1, G)
            d.set(1, y, n - 1, ladder("east"))
    d.door(3, 1, 0, "south", "birch")
    d.set(2, 1, 0, W)
    d.set(4, 1, 0, W)
    d.set(2, 2, 0, W)
    d.set(4, 2, 0, W)
    # ---- ground: info point (hut, lectern), bench, plants
    d.hut(*NT_WHUT)
    d.item(4, 1, 3, "lectern[facing=north,has_book=true,powered=false]")
    d.chair(1, 1, 2, "west", "birch")
    d.chair(1, 1, 3, "west", "birch")
    d.set(1, 1, 1, "potted_bamboo")
    d.set(5, 1, 5, "potted_bamboo")
    d.bookshelf(5, 1, 3)
    d.bookshelf(5, 1, 4)
    d.set(3, 1, 5, slab(QS, "top"))
    d.set(3, 2, 5, "flower_pot")
    d.set(3, 4, 3, "sea_lantern")
    # ---- storey 2: stacks
    if L >= 2:
        y = 6
        for z in (1, 2, 3, 4):
            d.bookshelf(5, y, z, 2)
        d.bookshelf(2, y, 1, 2)
        d.bookshelf(3, y, 1, 2)
        d.chair(3, y, 3, "south", "birch", sit=False)
        d.set(2, y, 5, "barrel[facing=up,open=false]")
        d.set(3, y, 5, "cyan_carpet")
        d.set(3, y + 3, 3, "sea_lantern")
    # ---- storey 3: listening room
    if L >= 3:
        y = 11
        d.set(5, y, 1, "jukebox[has_record=false]")
        d.set(5, y, 2, "note_block[instrument=harp,note=0,powered=false]")
        d.rug(2, 2, 4, 4, y, ("cyan_carpet", "light_blue_carpet"))
        d.chair(2, y, 3, "west", "birch")
        d.chair(4, y, 4, "south", "birch")
        d.set(3, y, 1, "potted_bamboo")
        d.set(5, y, 5, slab(QS, "top"))
        d.set(5, y + 1, 5, "candle[candles=2,lit=false,waterlogged=false]")
        d.set(3, y + 3, 3, "sea_lantern")
    # ---- storey 4: study pod
    if L >= 4:
        y = 16
        desk(d, 5, y, 3, "west", "birch", top=QS, light="end_rod[facing=up]")
        d.bookshelf(5, y, 1, 2)
        d.bookshelf(5, y, 5, 2)
        d.set(2, y, 1, "potted_azalea_bush")
        d.rug(2, 3, 3, 4, y, ("lime_carpet",), "plain")
        d.set(2, y, 5, "chest[facing=north,type=single,waterlogged=false]")
        d.set(3, y + 3, 3, "sea_lantern")
    # ---- storey 5: sky lounge
    if L >= 5:
        y = 21
        for x in (2, 3, 4):
            d.chair(x, y, 2, "south", "mangrove")
        d.set(3, y, 1, slab("mangrove_slab", "top"))
        d.set(1, y, 1, "potted_bamboo")
        d.set(5, y, 1, "potted_bamboo")
        d.set(5, y, 4, slab(QS, "top"))
        d.set(5, y + 1, 4, "brewing_stand[has_bottle_0=true,has_bottle_1=true,has_bottle_2=false]")
        d.rug(2, 3, 4, 4, y, ("white_carpet",), "plain")
        d.set(3, y + 3, 3, "sea_lantern")
    # ---- crown: glass lantern box with end-rod antennae
    d.fill(1, T + 1, 1, n - 1, T + 1, n - 1, AIR)
    for i in range(n + 1):
        for x, z in ((i, 0), (i, n), (0, i), (n, i)):
            d.set(x, T + 1, z, "light_gray_stained_glass_pane" if 0 < i < n else W)
    d.set(3, T + 1, 3, "sea_lantern")
    d.fill(2, T + 2, 2, 4, T + 2, 4, slab(QS))
    for x, z in ((0, 0), (n, 0), (0, n), (n, n)):
        d.set(x, T + 2, z, "end_rod[facing=up]")
    if L >= 3:
        d.set(3, T + 3, 3, W)
        d.set(3, T + 4, 3, "end_rod[facing=up]")
    if L >= 5:
        d.set(3, T + 5, 3, "end_rod[facing=up]")
    return d


def nt_shell(d, x1, z1, x2, z2, y1, y2, kind, glass):
    """Curtain wall on a rectangle: white corner columns; 'grid' = mullions every 3, 'diagrid' = Seattle-style
    diagonal lattice of white members over the glass."""
    for y in range(y1, y2 + 1):
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                if not (x in (x1, x2) or z in (z1, z2)):
                    continue
                u = x if z in (z1, z2) else z
                if x in (x1, x2) and z in (z1, z2):
                    b = W
                elif kind == "grid":
                    b = W if u % 3 == 0 else glass
                else:
                    b = W if (u + y) % 4 == 0 or (u - y) % 4 == 0 else glass
                d.set(x, y, z, b)


def nt_slab(d, x1, z1, x2, z2, y, floor="polished_diorite"):
    d.fill(x1, y, z1, x2, y, z2, floor)
    for x in range(x1, x2 + 1):
        for z in (z1, z2):
            d.set(x, y, z, W)
    for z in range(z1, z2 + 1):
        for x in (x1, x2):
            d.set(x, y, z, W)


def nt_parapet(d, x1, z1, x2, z2, y):
    for x in range(x1, x2 + 1):
        for z in (z1, z2):
            d.set(x, y, z, slab(QS, "bottom"))
    for z in range(z1, z2 + 1):
        for x in (x1, x2):
            d.set(x, y, z, slab(QS, "bottom"))


def nt_library(rel, L):
    d = Design("Neoterra", rel, NT_SIZE, gy=1, paving="smooth_stone")
    nt_plaza(d, L)
    # ---- A: the podium (x 10..28, z 12..26): storey 1 at L1, storey 2 at L2
    nt_shell(d, 10, 12, 28, 26, 2, 5, "grid", "glass_pane")
    d.fill(11, 1, 13, 27, 1, 25, "polished_diorite")
    nt_slab(d, 10, 12, 28, 26, 6)
    nt_a_ground(d, L)
    if L == 1:
        nt_parapet(d, 10, 12, 28, 26, 7)
    else:
        nt_shell(d, 10, 12, 28, 26, 7, 10, "grid", "glass_pane")
        nt_slab(d, 10, 12, 28, 26, 11, "smooth_stone")
        nt_a_upper(d, L)
    if L == 2:
        nt_parapet(d, 10, 12, 28, 26, 12)
    # ---- B: cantilevered volume (x 9..27, z 5..21): one storey at L3, two from L4, diagrid skin
    if L >= 3:
        top = 16 if L == 3 else 21
        nt_slab(d, 9, 5, 27, 21, 11)
        nt_shell(d, 9, 5, 27, 21, 12, top - 1, "diagrid", "light_gray_stained_glass_pane")
        for x in (9, 27):                                # slim pilotis under the cantilever
            for y in range(2, 11):
                d.set(x, y, 5, W)
        nt_slab(d, 9, 5, 27, 21, 16)
        nt_b_lower(d, L)
        nt_terrace(d, L)
        if L >= 4:
            nt_slab(d, 9, 5, 27, 21, 21, "smooth_stone")
            nt_b_upper(d, L)
        if L == 3:
            nt_parapet(d, 9, 5, 27, 21, 17)
            nt_solar(d, 17, ((13, 9), (17, 9), (21, 9), (13, 15), (17, 15), (21, 15)))
        if L == 4:
            nt_parapet(d, 9, 5, 27, 21, 22)
            nt_solar(d, 22, ((13, 8), (17, 8), (21, 8), (13, 14), (17, 14), (21, 14)))
    if L >= 4:
        nt_spiral(d, L)
    if L >= 5:
        nt_crown(d)
        nt_auditorium(d)
        nt_garden(d)
        nt_cafe(d)
        nt_deck(d)
    nt_lights(d, L)
    for tx in NT_TX:
        d.reserve(tx, 1, NT_TZ, tx + NT_TW - 1, 34, NT_TZ + NT_TW - 1)
        d.child_hut(tx + NT_WHUT[0], 1 + NT_WHUT[1], NT_TZ + NT_WHUT[2], WING)
    return nt_common(d) if L <= 3 else d


NT_LIGHTS = {   # ceiling lights set into the slabs: (level from which, slab y, cells)
    1: (6, ((14, 16), (19, 18), (24, 22), (15, 22), (23, 14), (19, 23), (22, 21), (25, 21), (22, 23), (25, 23),
            (21, 20), (26, 24))),
    2: (11, ((15, 15), (20, 19), (25, 15), (16, 23), (24, 20), (22, 22), (24, 23), (23, 21), (22, 24))),
    3: (16, ((14, 9), (22, 9), (18, 16), (14, 18), (24, 13), (23, 17), (23, 18))),
    4: (21, ((17, 9), (21, 9), (17, 14), (21, 14), (13, 7), (25, 17))),
}


def nt_lights(d, L):
    for lv, (y, cells) in NT_LIGHTS.items():
        if L >= lv:
            for x, z in cells:
                d.set(x, y, z, "sea_lantern")


def nt_deck(d):
    """L5: east reading deck beside the spiral (x 30..41, z 9..13): mangrove boards, rail, loungers, planters."""
    for x in range(30, 42):
        for z in range(9, 14):
            d.set(x, 2, z, slab("mangrove_slab"))
    for x in range(30, 42):
        d.set(x, 3, 9, fence("mangrove_fence"))
    for z in range(10, 14):
        d.set(41, 3, z, fence("mangrove_fence"))
    for x in (32, 35, 38):
        d.chair(x, 3, 12, "south", "birch", sit=False)
        d.chair(x + 1, 3, 12, "south", "birch", sit=False)
    for x in (31, 34, 37, 40):
        d.set(x, 3, 10, "potted_bamboo")
    lamp_post(d, 36, 10, 3, W, "iron_bars", h=2, top="sea_lantern")


def nt_solar(d, y, cells):
    """Rows of solar panels (daylight detectors on a quartz rack) on a roof, at hand-picked spots."""
    for x, z in cells:
        for dx in (0, 1, 2):
            d.set(x + dx, y, z, "daylight_detector[inverted=false,power=0]")
            d.set(x + dx, y, z + 1, "daylight_detector[inverted=false,power=0]")


def nt_plaza(d, L):
    """Entrance plaza under the cantilever: paving bands, planters, benches, bike rack, (L5) reflecting pool."""
    for x in range(0, 43):
        for z in range(0, 12):
            if (x + 2 * z) % 7 == 0:
                d.set(x, 1, z, "light_gray_concrete")
    for z in range(0, 12):
        for x in (18, 19, 20):
            d.set(x, 1, z, "polished_diorite")
    # entrance canopy and doors (A north wall at z=12)
    d.fill(16, 6, 10, 22, 6, 11, slab(QS))
    for x in (16, 22):
        for y in range(2, 6):
            d.set(x, y, 10, "iron_bars")
    if L >= 2:
        for x, z in ((12, 9), (25, 9)):                 # planters with bamboo
            d.fill(x, 2, z, x + 2, 2, z, "white_concrete")
            d.set(x + 1, 2, z, "moss_block")
            d.set(x + 1, 3, z, "bamboo[age=0,leaves=small,stage=0]")
        for x in (13, 14, 24, 25):
            d.chair(x, 2, 7, "north", "birch", sit=False)
    if L >= 3:
        for x, z in ((9, 1), (29, 1)):
            tree(d, x, z, 2, "birch_log", "birch_leaves", h=4, r=2)
        for x in range(30, 34):                         # bike rack
            d.set(x, 2, 10, "iron_bars")
    if L >= 5:                                          # reflecting pool with a book sculpture
        for x in range(23, 33):
            for z in range(3, 7):
                edge = x in (23, 32) or z in (3, 6)
                d.set(x, 1, z, "smooth_quartz" if edge else "water")
                if not edge:
                    d.set(x, 0, z, "light_blue_concrete")
        d.set(27, 1, 4, "smooth_quartz")
        d.set(27, 2, 4, "white_concrete")
        d.set(27, 3, 4, "cyan_terracotta")
        d.set(28, 3, 4, "cyan_terracotta")
        d.set(27, 4, 4, stair("quartz_stairs", "east"))
        d.set(28, 4, 4, stair("quartz_stairs", "west"))
        for x in (10, 15):
            lamp_post(d, x, 4, 2, "polished_andesite", "iron_bars", h=3, top="sea_lantern")


def nt_a_ground(d, L):
    """A ground floor (walk 2): the 'living room' – front desk, browsing shelves, lounge, reading table."""
    y = 2
    d.double_door(18, y, 12, "x", "south", "birch")
    d.hut(25, y, 14, "north")
    d.counter(21, 16, 24, 16, y, QS)
    for x in (22, 23):
        d.chair(x, y, 17, "south", "birch")
    d.set(21, y + 1, 16, "potted_bamboo")
    d.set(24, y + 1, 16, "black_stained_glass_pane")
    for x in range(14, 18):
        d.bookshelf(x, y, 20)
        d.bookshelf(x, y, 23)
    d.table(15, y, 16, "birch", "slab", QS)
    d.table(16, y, 16, "birch", "slab", QS)
    for x in (15, 16):
        d.chair(x, y, 15, "north", "birch")
        d.chair(x, y, 17, "south", "birch")
    d.rug(21, 20, 26, 24, y, ("cyan_carpet", "light_gray_carpet"))
    d.set(23, y, 22, slab("birch_slab", "top"))
    d.set(24, y, 22, slab("birch_slab", "top"))
    d.set(23, y + 1, 22, "potted_bamboo")
    for x in (22, 23, 24, 25):
        d.chair(x, y, 24, "south", "mangrove")
    d.chair(21, y, 21, "west", "mangrove")
    d.chair(21, y, 22, "west", "mangrove")
    d.item(19, y, 25, "lectern[facing=north,has_book=true,powered=false]")
    for x, z in ((27, 13), (13, 13), (27, 25), (11, 25), (11, 20)):
        d.set(x, y, z, "potted_bamboo")
    if L >= 2:                                          # stair flight 1 (walk 2 -> 7) rising south
        for i in range(5):
            d.set(11, 2 + i, 14 + i, stair("smooth_quartz_stairs", "south"))
            for yy in range(2, 2 + i):
                d.set(11, yy, 14 + i, W)
        for z in (15, 16, 17):
            d.set(11, 6, z, AIR)
    if L >= 4:
        d.clear(28, 2, 20, 28, 3, 20)


def nt_a_upper(d, L):
    """A upper floor (walk 7): children's library (west) and quiet study carrels (east)."""
    y = 7
    if L == 2:
        for z in (15, 16, 17):
            d.set(12, y, z, fence("birch_fence"))
    for x in range(14, 19):
        d.bookshelf(x, y, 25)
    for z in range(18, 23):
        d.bookshelf(27, y, z)
    d.rug(14, 18, 16, 20, y, ("yellow_carpet", "lime_carpet"))
    d.table(15, y, 19, "birch", "post")
    d.chair(14, y, 19, "west", "birch")
    d.chair(16, y, 19, "east", "birch")
    d.chair(15, y, 20, "south", "birch")
    d.rug(21, 21, 24, 24, y, ("light_blue_carpet", "pink_carpet"))   # story corner
    d.chair(25, y, 22, "east", "mangrove", arms=True)
    d.chair(21, y, 22, "west", "birch")
    d.chair(21, y, 23, "west", "birch")
    d.set(23, y, 24, "jukebox[has_record=false]")
    for x in (20, 22, 24, 26):                          # study carrels along the north glass
        d.set(x, y, 13, slab(QS, "top"))
        d.chair(x, y, 14, "south", "birch")
        d.set(x, y + 1, 13, "end_rod[facing=up]" if x in (20, 24) else "potted_cactus")
    d.set(13, y, 24, "potted_bamboo")
    d.set(17, y, 13, "potted_bamboo")
    d.set(13, y, 13, "barrel[facing=up,open=false]")
    if L >= 4:
        d.clear(28, 7, 20, 28, 8, 20)


def nt_b_lower(d, L):
    """B lower floor (walk 12): the 'mixing chamber' – reference island, computer desks on the north glass,
    printer bay, lounge; doors to the roof terrace."""
    y = 12
    if L >= 3:                                          # stair flight 2 (walk 7 -> 12) rising north
        for i in range(5):
            d.set(12, 7 + i, 18 - i, stair("smooth_quartz_stairs", "north"))
        for z in (15, 16, 17):
            d.set(12, 11, z, AIR)
            d.set(13, y, z, "glass_pane")
    for x in range(16, 21):                             # reference island
        d.set(x, y, 11, slab(QS, "top"))
        d.set(x, y, 13, slab(QS, "top"))
    d.set(16, y, 12, slab(QS, "top"))
    d.set(20, y, 12, slab(QS, "top"))
    d.chair(18, y, 12, "south", "birch")
    d.set(17, y + 1, 11, "black_stained_glass_pane")
    d.set(19, y + 1, 13, "black_stained_glass_pane")
    for x in (12, 15, 18, 21, 24):                      # computer desks along the north glass
        d.set(x, y, 6, slab(QS, "top"))
        d.set(x + 1, y, 6, slab(QS, "top"))
        d.set(x, y + 1, 6, "black_stained_glass_pane")
        d.chair(x, y, 7, "south", "birch")
    d.set(26, y, 6, "potted_bamboo")
    d.set(10, y, 6, "potted_bamboo")
    d.set(26, y, 11, "dropper[facing=up,triggered=false]")
    d.set(26, y, 12, "dropper[facing=up,triggered=false]")
    d.set(26, y, 13, "barrel[facing=up,open=false]")
    d.rug(22, 17, 24, 18, y, ("gray_carpet",), "plain")
    for x in (22, 23, 24):
        d.chair(x, y, 19, "south", "mangrove")
    d.set(23, y, 17, slab("mangrove_slab", "top"))
    d.set(23, y + 1, 17, "potted_cactus")
    for z in (16, 17, 18):
        d.bookshelf(10, y, z)
    for x in (14, 15, 16, 20, 21, 22):                  # reference stacks behind the island
        d.bookshelf(x, y, 9, 2)
    d.double_door(18, y, 21, "x", "north", "birch")


def nt_terrace(d, L):
    """Roof terrace on the podium (walk 12, x 10..28, z 22..26): glass balustrade, planters, deckchairs."""
    y = 12
    for x in range(11, 28):
        d.set(x, y, 26, "glass_pane")
    for z in range(22, 26):
        d.set(10, y, z, "glass_pane")
        d.set(28, y, z, "glass_pane")
    for x in (10, 28):                                  # corner planters
        d.set(x, y, 26, "moss_block")
        d.set(x, y + 1, 26, "flowering_azalea")
    for x, z in ((12, 23), (25, 23)):
        d.set(x, y, z, "moss_block")
        d.set(x, y + 1, z, "flowering_azalea")
        d.set(x + 1, y, z, "moss_block")
        d.set(x + 1, y + 1, z, "azalea")
    for x in (15, 16, 21, 22):
        d.chair(x, y, 25, "south", "birch")
    d.table(18, y, 24, "birch", "post")
    d.table(19, y, 24, "birch", "post")
    d.chair(18, y, 23, "north", "birch")
    d.chair(19, y, 23, "north", "birch")
    for x in (14, 24):
        d.set(x, y, 23, "iron_bars")
        d.set(x, y + 1, 23, "sea_lantern")


def nt_b_upper(d, L):
    """B upper floor (walk 17): the reading room – two long tables with lamps, wall shelves, view north."""
    y = 17
    for i in range(5):                                  # flight 3 (walk 12 -> 17) rising south
        d.set(11, 12 + i, 14 + i, stair("smooth_quartz_stairs", "south"))
    for z in (15, 16, 17):
        d.set(11, 16, z, AIR)
    for zr in (9, 14):
        for x in range(15, 24):
            d.set(x, y, zr, slab("birch_slab", "top"))
            if x % 2:
                d.chair(x, y, zr - 1, "north", "birch")
                d.chair(x, y, zr + 1, "south", "birch")
            elif x in (16, 20):
                d.set(x, y + 1, zr, "end_rod[facing=up]")
    for z in range(7, 20, 2):
        d.bookshelf(26, y, z, 2)
    for x in range(16, 25, 2):
        d.bookshelf(x, y, 20, 2)
    for x, z in ((10, 6), (26, 6), (13, 20), (25, 20)):
        d.set(x, y, z, "potted_bamboo")
    d.rug(13, 11, 25, 11, y, ("cyan_carpet",), "plain")
    if L >= 5:                                          # flight 4 (walk 17 -> 22) rising north
        for i in range(5):
            d.set(12, 17 + i, 18 - i, stair("smooth_quartz_stairs", "north"))
        for z in (15, 16, 17):
            d.set(12, 21, z, AIR)
    else:
        for z in (15, 16, 17):
            d.set(12, y, z, fence("birch_fence"))


def nt_spiral(d, L):
    """The book spiral: a glass cylinder (centre NT_SP, R 5) with helical white fins; inside a square helix
    stair winds round a column of books from walk 2 to walk 22, a ring room on every floor."""
    cx, cz = NT_SP
    R = NT_SR
    top = 26 if L == 4 else 33
    rg = ring(cx, cz, R)
    inn = interior(cx, cz, R)
    for x, z in inn:
        d.set(x, 1, z, "polished_diorite")
    for x, z in rg:
        a = ang(cx, cz, x, z)
        for y in range(2, top + 1):
            fin = int((a + y * 12) % 60) < 13
            d.set(x, y, z, W if fin or y in (6, 11, 16, 21, 26) else "light_blue_stained_glass_pane")
    for F in (6, 11, 16, 21):
        for x, z in inn:
            d.set(x, F, z, "smooth_stone")
    for x, z in disk(cx, cz, R):
        d.set(x, top + 1, z, "white_stained_glass" if inside(cx, cz, x, z, R - 1) else W)
    # helix: step k (1..20) at height 1+k on cell NT_HELIX[k % 8]
    for k in range(1, 21):
        x, z = NT_HELIX[k % 8]
        nx, nz = NT_HELIX[(k + 1) % 8]
        f = {(1, 0): "east", (-1, 0): "west", (0, 1): "south", (0, -1): "north"}[(nx - x, nz - z)]
        d.set(x, 1 + k, z, stair("smooth_quartz_stairs", f))
        for F in (6, 11, 16, 21):
            if 1 + k in (F - 1, F - 2, F - 3):
                d.set(x, F, z, AIR)
    for y in range(2, top + 1):
        d.bookshelf(cx, y, cz)
    d.clear(29, 2, 20, 29, 3, 20)
    d.clear(29, 7, 20, 29, 8, 20)
    # ---- ring rooms, each its own use
    y = 2                                               # foyer: returns desk, benches, plants
    d.counter(31, 17, 31, 18, y, QS)
    d.item(31, y, 23, "barrel")
    d.chair(37, y, 19, "east", "birch")
    d.chair(37, y, 20, "east", "birch")
    d.chair(37, y, 21, "east", "birch")
    d.set(31, y, 22, "potted_bamboo")
    d.set(36, y, 24, "potted_bamboo")
    d.set(36, y, 16, "potted_bamboo")
    y = 7                                               # stacks: radial shelf rows
    for x, z in ((30, 18), (30, 22), (37, 18), (37, 22), (34, 16), (34, 24), (32, 16), (36, 24)):
        d.bookshelf(x, y, z, 2)
    d.chair(31, y, 20, "west", "birch")
    y = 12                                              # media lab: screens and headphones
    for x, z, s in ((31, 18, "east"), (31, 22, "east"), (37, 18, "west"), (37, 22, "west")):
        d.set(x, y, z, slab(QS, "top"))
        d.set(x, y + 1, z, "black_stained_glass_pane")
        d.chair(x + (1 if s == "east" else -1), y, z, s, "birch")
    d.set(34, y, 16, "jukebox[has_record=false]")
    d.set(34, y, 24, "potted_bamboo")
    y = 17                                              # study carrels on the glass
    for x, z, s in ((34, 16, "south"), (30, 20, "east"), (38, 20, "west"), (34, 24, "north")):
        desk(d, x, y, z, s, "mangrove", top=QS, light="end_rod[facing=up]" if s in ("south", "north") else None)
    d.set(31, y, 17, "potted_cactus")
    d.set(37, y, 23, "potted_cactus")
    y = 22                                              # sky reading lounge under the glass roof
    d.rug(30, 22, 32, 24, y, ("white_carpet", "light_blue_carpet"))
    d.chair(31, y, 24, "south", "mangrove", arms=False)
    d.chair(30, y, 23, "west", "mangrove")
    d.set(31, y, 23, slab("mangrove_slab", "top"))
    d.set(37, y, 18, "potted_bamboo")
    d.set(37, y, 22, "potted_bamboo")
    d.bookshelf(36, y, 17, 2)
    d.bookshelf(34, y, 16, 2)
    for F in (6, 11, 16, 21):                           # lights set into each ceiling
        d.set(37, F, 20, "sea_lantern")
        if F != 21:
            d.set(31, F, 20, "sea_lantern")
    if L >= 5:
        for x, z in rg:
            a = ang(cx, cz, x, z)
            if int(a) % 45 < 12:
                d.set(x, top + 2, z, "end_rod[facing=up]")


def nt_auditorium(d):
    """L5: auditorium pavilion on the west side (x 1..8, z 11..33): mangrove fins and glass, green roof;
    raked tiers of seats facing a stage and screen; linked to the podium lobby."""
    x1, z1, x2, z2 = 1, 11, 8, 33
    for y in range(2, 10):
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                if x in (x1, x2) or z in (z1, z2):
                    u = x + z
                    corner = x in (x1, x2) and z in (z1, z2)
                    d.set(x, y, z, W if corner or y == 9 else
                          (log("stripped_mangrove_log") if u % 2 else "light_gray_stained_glass_pane"))
    d.fill(x1, 10, z1, x2, 10, z2, W)
    d.fill(x1 + 1, 10, z1 + 1, x2 - 1, 10, z2 - 1, "moss_block")
    for x, z in ((3, 15), (6, 19), (3, 24), (6, 29)):
        d.set(x, 11, z, "flowering_azalea")
    d.fill(x1 + 1, 1, z1 + 1, x2 - 1, 1, z2 - 1, "polished_diorite")
    for z in range(z1 + 1, 24):                          # tiers rising to the north
        lvl = 1 + (23 - z) // 4
        for yy in range(2, 2 + lvl):
            d.fill(x1 + 2, yy, z, x2 - 1, yy, z, "gray_concrete")
    for z in range(z1 + 1, 24):                          # aisle steps on the west
        lvl = (23 - z) // 4 + 1
        if (23 - z) % 4 == 0:
            d.set(2, 1 + lvl, z, stair("smooth_quartz_stairs", "north"))
        for yy in range(2, 1 + lvl):
            d.set(2, yy, z, "gray_concrete")
        if (23 - z) % 4:
            d.set(2, 1 + lvl, z, "gray_concrete")
    for z in (13, 15, 17, 19, 21, 23, 25, 27):           # seats
        lvl = 0 if z > 23 else 1 + (23 - z) // 4
        for x in range(3, 8):
            d.chair(x, 2 + lvl, z, "north", "mangrove")
    d.fill(2, 2, 30, 7, 2, 32, slab(QS, "bottom"))      # stage, lectern and screen
    d.item(5, 3, 31, "lectern[facing=north,has_book=true,powered=false]")
    d.fill(3, 4, 33, 6, 7, 33, "white_concrete")
    d.set(2, 3, 30, "potted_bamboo")
    d.set(7, 3, 30, "potted_bamboo")
    d.door(8, 2, 24, "west", "birch")
    d.door(10, 2, 24, "east", "birch")
    d.door(4, 2, 11, "south", "birch")
    for x, z in ((4, 14), (4, 20), (4, 26), (4, 31)):
        d.set(x, 10, z, "sea_lantern")


def nt_garden(d):
    """L5: reading garden behind the podium (x 10..28, z 28..39): paths, birches, benches, a pergola."""
    for z in range(27, 40):
        for x in (18, 19, 20):
            d.set(x, 1, z, "polished_diorite")
    for x in range(10, 29):
        d.set(x, 1, 33, "polished_diorite")
    for x in range(10, 29):
        for z in range(28, 40):
            if d.get(x, 1, z) == "minecraft:smooth_stone":
                d.set(x, 1, z, "grass_block[snowy=false]")
    for x, z in ((13, 30), (25, 30), (13, 37), (25, 37)):
        tree(d, x, z, 2, "birch_log", "birch_leaves", h=4, r=2)
    for x in (16, 22):                                   # benches facing the central walk
        for z in (30, 36):
            d.chair(x, 2, z, "west" if x < 19 else "east", "birch", sit=False)
            d.chair(x, 2, z + 1, "west" if x < 19 else "east", "birch", sit=False)
    for x in (17, 21):                                   # pergola over the crossing
        for z in (32, 34):
            for y in (2, 3, 4):
                d.set(x, y, z, W)
    for x in range(17, 22):
        for z in (32, 33, 34):
            d.set(x, 5, z, slab("mangrove_slab"))
    for x, z in ((3, 36), (7, 39), (36, 39)):           # birch grove at the back corners
        tree(d, x, z, 2, "birch_log", "birch_leaves", h=5, r=2)
    for z in (35, 36):
        d.chair(6, 2, z, "west", "birch", sit=False)
    d.set(5, 2, 38, "moss_block")
    d.set(5, 3, 38, "flowering_azalea")
    for x in range(11, 28):                              # low box hedge along the garden's back edge
        if x not in (18, 19, 20):
            d.set(x, 2, 39, "oak_leaves[distance=1,persistent=true,waterlogged=false]")
    for x, f in ((11, "allium"), (12, "cornflower"), (14, "allium"), (15, "cornflower"),
                 (23, "allium"), (24, "cornflower"), (26, "allium"), (27, "cornflower")):
        d.set(x, 2, 34, f)


def nt_cafe(d):
    """L5: garden cafe pavilion (x 30..40, z 28..37): glass box, mangrove roof terrace edge, counter, tables."""
    x1, z1, x2, z2 = 30, 28, 40, 37
    nt_shell(d, x1, z1, x2, z2, 2, 5, "grid", "glass_pane")
    d.fill(x1 + 1, 1, z1 + 1, x2 - 1, 1, z2 - 1, "mangrove_planks")
    nt_slab(d, x1, z1, x2, z2, 6, "smooth_stone")
    for x in range(x1 - 1, x2 + 2):
        d.set(x, 6, z1 - 1, slab("mangrove_slab"))
    d.double_door(34, 2, z1, "x", "south", "birch")
    d.counter(32, 36, 38, 36, 2, "mangrove_slab")
    d.item(39, 2, 36, "smoker", "north")
    d.set(31, 2, 36, "water_cauldron[level=3]")
    d.set(33, 3, 36, "flower_pot")
    d.set(36, 3, 36, "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]")
    d.chair(35, 2, 35, "north", "birch")
    for x, z in ((32, 31), (38, 31)):
        d.table(x, 2, z, "birch", "post")
        d.chair(x - 1, 2, z, "west", "birch")
        d.chair(x + 1, 2, z, "east", "birch")
        d.chair(x, 2, z + 1, "south", "birch")
    d.rug(34, 30, 36, 32, 2, ("orange_carpet", "white_carpet"))
    d.set(31, 2, 29, "potted_bamboo")
    d.set(39, 2, 29, "potted_bamboo")
    for x, z in ((33, 31), (37, 31), (35, 34)):
        d.set(x, 6, z, "sea_lantern")


def nt_crown(d):
    """L5: C, the double-height top reading hall (x 10..28, z 12..28, walk 22) cantilevered south over the
    terrace, glass on all sides with a diagrid, a roof garden on top."""
    x1, z1, x2, z2 = 10, 12, 28, 28
    nt_slab(d, x1, z1, x2, z2, 21, "smooth_stone")
    nt_shell(d, x1, z1, x2, z2, 22, 29, "diagrid", "light_blue_stained_glass_pane")
    nt_slab(d, x1, z1, x2, z2, 30, "smooth_quartz")
    nt_parapet(d, x1, z1, x2, z2, 31)
    d.clear(28, 22, 20, 29, 23, 20)
    y = 22
    for z in range(14, 27, 3):                           # shelves along the west glass, two high
        d.bookshelf(11, y, z, 2)
        d.bookshelf(11, y, z + 1, 2)
    for x in range(14, 25, 2):
        d.bookshelf(x, y, 27, 2)
    for zr in (16, 22):                                  # two long tables with lamps
        for x in range(16, 24):
            d.set(x, y, zr, slab("mangrove_slab", "top"))
            if x % 2 == 0:
                d.chair(x, y, zr - 1, "north", "mangrove")
                d.chair(x, y, zr + 1, "south", "mangrove")
            elif x in (17, 21):
                d.set(x, y + 1, zr, "end_rod[facing=up]")
    d.counter(24, 13, 27, 13, y, QS)                     # coffee bar
    d.item(27, y, 14, "smoker", "west")
    d.set(27, y, 15, "water_cauldron[level=3]")
    d.set(25, y + 1, 13, "flower_pot")
    d.chair(25, y, 14, "south", "birch")
    d.rug(13, 24, 15, 26, y, ("cyan_carpet", "white_carpet"))
    d.chair(13, y, 26, "south", "mangrove", arms=True)
    d.chair(15, y, 26, "south", "mangrove", arms=True)
    d.set(14, y, 25, slab("mangrove_slab", "top"))
    for x, z in ((27, 27), (13, 13), (27, 19)):
        d.set(x, y, z, "potted_bamboo")
    for x, z in ((16, 19), (22, 19), (19, 14), (19, 25), (13, 20), (25, 24)):
        chandelier(d, x, z, 29, 27)
    # roof garden on the crown
    for x, z in ((14, 16), (24, 16), (14, 24), (24, 24)):
        d.set(x, 31, z, "moss_block")
        d.set(x, 32, z, "flowering_azalea")
    for x in range(17, 22):
        d.set(x, 31, 20, "daylight_detector[inverted=false,power=0]")
        d.set(x, 31, 21, "daylight_detector[inverted=false,power=0]")
    for y in range(31, 36):                              # mast
        d.set(19, y, 14, "iron_bars" if y < 35 else "end_rod[facing=up]")


# ================================================================================================ CASCADIA
CG_SIZE = (47, 40, 46)
CG_TX, CG_TZ, CG_TW = (2, 38), 25, 7         # timber lookout book towers (wings)
CG_WHUT = (5, 1, 1)
LOGX, LOGZ, LOGY = log("stripped_spruce_log", "x"), log("stripped_spruce_log", "z"), log("spruce_log")
ROCK = ("cobblestone", "mossy_cobblestone", "andesite", "cobblestone", "tuff")


def rock(x, y, z):
    return ROCK[(x * 7 + y * 3 + z * 5) % len(ROCK)]


def cg_walls(d, x1, z1, x2, z2, y2, plinth=2):
    """Log walls: river-rock plinth up to `plinth`, stripped logs laid along each wall, dark spruce corner posts."""
    for y in range(2, y2 + 1):
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                if not (x in (x1, x2) or z in (z1, z2)):
                    continue
                if x in (x1, x2) and z in (z1, z2):
                    b = LOGY if y > plinth else rock(x, y, z)
                elif y <= plinth:
                    b = rock(x, y, z)
                else:
                    b = LOGX if z in (z1, z2) else LOGZ
                d.set(x, y, z, b)


def cg_wing(rel, L):
    """Fire-lookout book tower: river-rock base, stripped-log walls with spruce corner posts, a storey per level
    linked by a ladder, a glazed lookout cab with a hipped cap on top."""
    d = Design("Cascadia", rel, (CG_TW, 34, CG_TW), gy=0, paving="coarse_dirt")
    n, T = CG_TW - 1, 4 * L + 1
    for y in range(1, T + 1):
        for i in range(n + 1):
            for x, z in ((i, 0), (i, n), (0, i), (n, i)):
                corner = x in (0, n) and z in (0, n)
                if y == 1:
                    b = rock(x, y, z)
                elif corner:
                    b = LOGY
                else:
                    b = LOGX if z in (0, n) else LOGZ
                d.set(x, y, z, b)
    d.fill(1, 0, 1, n - 1, 0, n - 1, "spruce_planks")
    for F in range(5, T + 1, 4):
        d.fill(1, F, 1, n - 1, F, n - 1, "spruce_planks")
        for i in range(n + 1):
            for x, z in ((i, 0), (i, n), (0, i), (n, i)):
                d.set(x, F, z, "dark_oak_planks" if not (x in (0, n) and z in (0, n)) else LOGY)
    for w in range(1, T - 3, 4):                     # a window per face and storey
        for x, z in ((3, 0), (3, n), (0, 3), (n, 3)):
            if w == 1 and (x, z) == (3, 0):
                continue
            d.set(x, w + 2, z, "glass_pane")
            d.set(x, w + 1, z, "glass_pane" if w > 1 else d.get(x, w + 1, z))
    d.door(3, 1, 0, "south", "spruce")
    for y in range(1, T - 3 if L > 1 else 1):
        d.set(1, y, n - 1, ladder("east"))
    # ---- ground: issue room (hut, lectern), coat pegs, firewood, stove
    d.hut(*CG_WHUT)
    d.item(4, 1, 3, "lectern[facing=north,has_book=true,powered=false]")
    d.set(1, 1, 1, "barrel[facing=up,open=false]")
    d.set(1, 2, 1, "lantern[hanging=false,waterlogged=false]")
    d.set(5, 1, 5, log("oak_log", "x"))
    d.set(5, 1, 4, log("oak_log", "x"))
    d.set(5, 2, 5, log("oak_log", "x"))
    d.bookshelf(1, 1, 2)
    d.bookshelf(1, 1, 3)
    d.rug(2, 2, 3, 3, 1, ("brown_carpet",), "plain")
    d.lamp(3, 4, 3)
    if L >= 2:                                       # stacks
        y = 6
        for z in (1, 2, 3, 4):
            d.bookshelf(5, y, z, 2)
        d.bookshelf(2, y, 1, 2)
        d.bookshelf(3, y, 1, 2)
        d.set(2, y, 5, "barrel[facing=up,open=false]")
        d.chair(3, y, 4, "south", "spruce", sit=False)
        d.lamp(3, y + 2, 3)
    if L >= 3:                                       # ranger's map room
        y = 10
        d.item(4, y, 4, "cartography_table")
        d.chair(4, y, 3, "north", "spruce", sit=False)
        d.set(5, y, 1, "chest[facing=west,type=single,waterlogged=false]")
        d.set(5, y, 2, "chest[facing=west,type=single,waterlogged=false]")
        d.set(2, y, 1, "potted_fern")
        d.rug(2, 2, 3, 3, y, ("green_carpet",), "plain")
        d.set(5, y + 1, 4, "green_wall_banner[facing=west]")
        d.lamp(3, y + 2, 3)
    if L >= 4:                                       # reading nook with a stove
        y = 14
        d.set(5, y, 3, "campfire[facing=west,lit=true,signal_fire=false,waterlogged=false]")
        d.set(5, y, 2, "cobblestone")
        d.set(5, y, 4, "cobblestone")
        d.chair(3, y, 3, "west", "spruce", arms=False)
        d.chair(3, y, 1, "north", "spruce")
        d.set(2, y, 2, slab("spruce_slab", "top"))
        d.set(2, y + 1, 2, "candle[candles=2,lit=false,waterlogged=false]")
        d.bookshelf(2, y, 5, 2)
        d.bookshelf(3, y, 5, 2)
        d.rug(2, 3, 3, 4, y, ("red_carpet",), "plain")
        d.lamp(4, y + 2, 2)
    if L >= 5:                                       # lookout cab: fire finder, telescope, logbook
        y = 18
        for x in (1, 2, 4, 5):
            for z in (0, n):
                d.set(x, y + 1, z, "glass_pane")
                d.set(x, y + 2, z, "glass_pane")
        for z in (1, 2, 4, 5):
            for x in (0, n):
                d.set(x, y + 1, z, "glass_pane")
                d.set(x, y + 2, z, "glass_pane")
        d.item(3, y, 3, "cartography_table")
        d.set(3, y, 1, fence("spruce_fence"))
        d.set(3, y + 1, 1, "lightning_rod[facing=north,powered=false,waterlogged=false]")
        d.chair(4, y, 3, "east", "spruce", sit=False)
        d.set(5, y, 5, slab("spruce_slab", "top"))
        d.set(5, y + 1, 5, "candle[candles=1,lit=false,waterlogged=false]")
        d.set(2, y, 5, "barrel[facing=up,open=false]")
        d.lamp(3, y + 2, 3)
    # cap: hipped shingle roof with a finial
    top = d.hip(0, 0, n, n, T + 1, "spruce_stairs", "spruce_slab", overhang=0)
    d.set(3, top + 1, 3, fence("spruce_fence"))
    d.set(3, top + 2, 3, "lantern[hanging=false,waterlogged=false]")
    return d


def cg_hall_roof_y(z):
    return 8 + min(z - 9, 23 - z)


def cg_library(rel, L):
    d = Design("Cascadia", rel, CG_SIZE, gy=1, paving="coarse_dirt")
    for z in range(0, 10):                             # gravel path from the road
        for x in (22, 23, 24):
            d.set(x, 1, z, "gravel")
    hx1, hx2 = (17, 29) if L == 1 else (14, 32)      # the hall is lengthened by two bays at L2
    d.fill(hx1 + 1, 1, 11, hx2 - 1, 1, 21, "spruce_planks")
    if L >= 3:
        cg_cross_wing(d, L)
    cg_walls(d, hx1, 10, hx2, 22, 8)
    posts = (17, 23, 29) if L == 1 else (14, 18, 23, 28, 32)
    wins = (19, 26) if L == 1 else (16, 20, 25, 29)
    for x in posts:                                   # posts between the bays
        for z in (10, 22):
            for y in range(3, 9):
                d.set(x, y, z, LOGY)
    for x0 in wins:                                   # windows, two panes wide, dark sills
        for z in (10, 22):
            for x in (x0, x0 + 1):
                for y in (4, 5, 6):
                    d.set(x, y, z, "glass_pane")
                d.set(x, 3, z, "dark_oak_planks")
    d.door(23, 2, 10, "south", "spruce")
    d.set(23, 4, 10, "dark_oak_planks")
    d.gable(hx1, 10, hx2, 22, 9, "x", stairs="spruce_stairs", ridge="spruce_slab", end="spruce_planks", overhang=1)
    for x in (hx1, hx2):                              # board-and-batten gables with a round window
        for y in range(9, 15):
            for z in range(11, 22):
                if d.get(x, y, z) == "minecraft:spruce_planks" and z % 3 == 1:
                    d.set(x, y, z, log("dark_oak_log"))
        d.set(x, 11, 16, "glass_pane")
        d.set(x, 12, 16, "glass_pane")
    if L >= 3:                                        # tidy the hall's attic where the cross roof meets it
        for z in range(11, 22):
            for x in range(15, 32):
                for y in range(9, cg_hall_roof_y(z)):
                    d.set(x, y, z, AIR)
        d.clear(22, 2, 22, 24, 4, 22)
        d.set(22, 5, 22, stair("spruce_stairs", "west", "top"))
        d.set(24, 5, 22, stair("spruce_stairs", "east", "top"))
    for x in ((20, 26) if L == 1 else (17, 21, 25, 29)):   # log trusses
        d.fill(x, 8, 11, x, 8, 21, log("spruce_log", "z"))
        for y in range(9, 15):
            d.set(x, y, 16, LOGY)
        for k in range(1, 4):
            d.set(x, 8 + k, 16 - k - 1, log("stripped_spruce_log", "z"))
            d.set(x, 8 + k, 16 + k + 1, log("stripped_spruce_log", "z"))
    cg_fireplace(d, hx2, 1)
    if L >= 2:
        cg_fireplace(d, 14, -1)
    for x in (hx1 - 1, hx2 + 1):                      # rain barrels under the eave corners
        for z in (9, 23):
            d.set(x, 2, z, "water_cauldron[level=3]")
    if L >= 3:
        for x, z in ((18, 23), (28, 23), (18, 35), (28, 35)):
            d.set(x, 2, z, "water_cauldron[level=3]")
    if L >= 4:
        for x, z in ((8, 35), (38, 35), (8, 45), (38, 45)):
            d.set(x, 2, z, "water_cauldron[level=3]")
    cg_hall(d, L)
    if L >= 2:
        cg_galleries(d, L)
        cg_porch(d, L)
    if L >= 3:
        cg_cabin(d, L, west=True)
    if L >= 4:
        cg_cabin(d, L, west=False)
        cg_annex(d, L)
    if L >= 5:
        cg_dormers(d)
        cg_fence(d, L)
        cg_decks(d)
        cg_cupola(d)
        cg_yard(d)
        cg_lookout(d)
        cg_cabin_porch(d)
        cg_boardwalks(d)
        cg_finish_l5(d)
    for tx in CG_TX:
        d.reserve(tx, 1, CG_TZ, tx + CG_TW - 1, 34, CG_TZ + CG_TW - 1)
        d.child_hut(tx + CG_WHUT[0], 1 + CG_WHUT[1], CG_TZ + CG_WHUT[2], WING)
    return d


def cg_fireplace(d, xw, out):
    """River-rock fireplace recessed into the gable wall at x=xw (out = +1 east / -1 west), chimney outside."""
    inn = xw - out
    face = "west" if out > 0 else "east"
    for z in (15, 16, 17):
        for y in range(2, 9):
            d.set(xw, y, z, rock(xw, y, z))
        for y in range(2, 17):
            d.set(xw + out, y, z, rock(xw + out, y, z))
    for y in range(17, 18):
        d.set(xw + out, y, 15, rock(xw + out, y, 15))
        d.set(xw + out, y, 17, rock(xw + out, y, 17))
    d.set(xw, 2, 16, f"campfire[facing={face},lit=true,signal_fire=false,waterlogged=false]")
    d.set(xw, 3, 16, AIR)
    for z in (15, 17):
        d.set(inn, 2, z, "cobblestone")
        d.set(inn, 3, z, "cobblestone")
    for z in (15, 16, 17):
        d.set(inn, 4, z, slab("spruce_slab", "top"))
        d.set(inn, 1, z, "smooth_stone")
    d.set(inn, 5, 15, "lantern[hanging=false,waterlogged=false]")
    d.set(inn, 5, 17, "potted_fern")
    d.set(xw, 5, 16, "dark_oak_planks")


def cg_hall(d, L):
    """Great hall floor (walk 2): long reading tables, a fireside lounge, wall shelves, lights on the trusses."""
    y = 2
    d.hut(25, y, 11, "north")
    if L == 1:                                         # the first, three-bay hall
        for zr in (15, 18):
            for x in range(18, 22):
                d.set(x, y, zr, slab("dark_oak_slab", "top"))
                d.chair(x, y, zr - 1, "north", "spruce")
                d.chair(x, y, zr + 1, "south", "spruce")
            d.set(19, y + 1, zr, "lantern[hanging=false,waterlogged=false]")
            d.set(21, y + 1, zr, "candle[candles=2,lit=false,waterlogged=false]")
        d.rug(25, 15, 27, 17, y, ("brown_carpet",), "plain")
        d.chair(25, y, 15, "west", "dark_oak")
        d.chair(25, y, 17, "west", "dark_oak")
        d.set(26, y, 16, slab("spruce_slab", "top"))
        d.set(26, y + 1, 16, "candle[candles=1,lit=false,waterlogged=false]")
        for x in (21, 22, 23, 24):
            d.bookshelf(x, y, 21, 2)
        for x in (21, 22):
            d.bookshelf(x, y, 11, 2)
        d.set(18, y, 11, "barrel[facing=up,open=false]")
        d.set(19, y, 11, "barrel[facing=up,open=false]")
        d.set(28, y, 11, "potted_fern")
        d.set(18, y, 21, "potted_fern")
        d.set(28, y, 21, log("oak_log", "x"))
        d.set(27, y, 21, log("oak_log", "x"))
        d.set(28, y + 1, 21, log("oak_log", "x"))
        for x in (20, 26):
            d.set(x, 7, 16, CHAIN)
            d.set(x, 6, 16, lantern(True))
        return
    for zr in (15, 18):
        for x in range(17, 22):
            d.set(x, y, zr, slab("dark_oak_slab", "top"))
            d.chair(x, y, zr - 1, "north", "spruce")
            d.chair(x, y, zr + 1, "south", "spruce")
        d.set(18, y + 1, zr, "candle[candles=2,lit=false,waterlogged=false]")
        d.set(20, y + 1, zr, "lantern[hanging=false,waterlogged=false]")
    d.rug(28, 15, 30, 17, y, ("brown_carpet", "brown_carpet"), "plain")
    d.chair(28, y, 15, "west", "dark_oak", arms=False)
    d.chair(28, y, 17, "west", "dark_oak", arms=False)
    d.set(29, y, 16, slab("spruce_slab", "top"))
    d.set(29, y + 1, 16, "candle[candles=1,lit=false,waterlogged=false]")
    d.chair(16, y, 15, "east", "dark_oak", arms=False)   # west fireside chairs
    d.chair(16, y, 17, "east", "dark_oak", arms=False)
    for x in (18, 19, 27, 28):
        d.bookshelf(x, y, 11, 2)
    for x in (18, 19, 21, 22, 27):
        d.bookshelf(x, y, 21, 2)
    if L < 3:
        d.bookshelf(23, y, 21, 2)
        d.bookshelf(24, y, 21, 2)
    d.set(21, y, 11, "barrel[facing=up,open=false]")          # card catalogue
    d.set(22, y, 11, "barrel[facing=up,open=false]")
    d.set(15, y, 11, "potted_fern")
    d.set(31, y, 11, "potted_fern")
    d.set(31, y, 21, log("oak_log", "x"))                    # firewood
    d.set(30, y, 21, log("oak_log", "x"))
    d.set(31, y + 1, 21, log("oak_log", "x"))
    for x in (17, 21, 25, 29):
        d.set(x, 7, 16, CHAIN)
        d.set(x, 6, 16, lantern(True))


def cg_galleries(d, L):
    """L2: mezzanine galleries along both long walls (walk 7), each reached by a stair with shelves under it."""
    for z1 in (11, 20):
        d.fill(15, 6, z1, 31, 6, z1 + 1, "spruce_planks")
    for i in range(5):                                # north stair rising east, south stair rising west
        d.set(16 + i, 2 + i, 13, stair("spruce_stairs", "east"))
        d.set(30 - i, 2 + i, 19, stair("spruce_stairs", "west"))
        for yy in range(2, 2 + i):
            d.bookshelf(16 + i, yy, 13)
            d.bookshelf(30 - i, yy, 19)
    y = 7
    for x in range(15, 32):
        if not 16 <= x <= 20:
            d.set(x, y, 13, fence("spruce_fence"))
        if not 26 <= x <= 30:
            d.set(x, y, 19, fence("spruce_fence"))
    # north gallery: shelves on the wall, a two-chair reading nook
    for x in list(range(15, 21)) + list(range(26, 32)):
        d.bookshelf(x, y, 11, 2 if x not in (15, 31) else 1)
    d.chair(22, y, 11, "north", "spruce")
    d.chair(24, y, 11, "north", "spruce")
    d.set(23, y, 11, slab("spruce_slab", "top"))
    d.set(23, y + 1, 11, "lantern[hanging=false,waterlogged=false]")
    # south gallery: writing desks between the shelves
    for x in list(range(15, 20)) + list(range(28, 32)):
        d.bookshelf(x, y, 21, 2)
    for x in (21, 24):
        desk(d, x, y, 21, "north", "spruce", light="candle[candles=1,lit=false,waterlogged=false]" if x == 21 else None)
    d.set(26, y, 21, "potted_fern")


def cg_porch(d, L):
    """L2: covered front porch (z 5..9): log posts, shingle lean-to, rail, rocking chairs, woodpile, lanterns."""
    d.fill(15, 1, 4, 31, 1, 9, "spruce_planks")
    for x in (15, 19, 27, 31):
        for y in range(2, 7):
            d.set(x, y, 5, LOGY)
        d.set(x, 2, 5, rock(x, 2, 5))
    d.fill(15, 7, 5, 31, 7, 5, log("spruce_log", "x"))
    for x in range(14, 33):
        d.set(x, 8, 4, stair("spruce_stairs", "south"))
        d.set(x, 8, 5, stair("spruce_stairs", "south"))
        d.set(x, 9, 6, stair("spruce_stairs", "south"))
        d.set(x, 9, 7, stair("spruce_stairs", "south"))
        d.set(x, 10, 8, stair("spruce_stairs", "south"))
        d.set(x, 9, 8, "spruce_planks")
    for x in range(16, 31):
        if not 22 <= x <= 24 and x not in (19, 27):
            d.set(x, 2, 5, fence("spruce_fence"))
    for x in (17, 29):
        d.chair(x, 2, 8, "south", "spruce", sit=False)
        d.chair(x + 1, 2, 8, "south", "spruce", sit=False)
    for x in (20, 26):
        d.set(x, 6, 7, lantern(True))
        d.set(x, 7, 7, CHAIN)
        d.set(x, 8, 7, "spruce_planks")
    d.set(16, 2, 9, log("oak_log", "x"))
    d.set(16, 2, 8, log("oak_log", "x"))
    d.set(16, 3, 9, log("oak_log", "x"))
    d.set(30, 2, 9, "potted_fern")
    d.sign(23, 5, 9, "north", ["Great Library", "Reading Hall"], wood="spruce")


def cg_dormers(d):
    """L2: two shed dormers on each roof slope lighting the galleries."""
    for x0 in (18, 26):
        for z, f, zi in ((11, "south", 12), (21, "north", 20)):
            for x in (x0, x0 + 1, x0 + 2):
                for y in (10, 11):
                    d.set(x, y, z, "spruce_planks" if x != x0 + 1 else "glass_pane")
                d.set(x, 12, z, stair("spruce_stairs", f))
                d.set(x, 12, zi, stair("spruce_stairs", f))
            d.set(x0, 10, zi, "spruce_planks")
            d.set(x0 + 2, 10, zi, "spruce_planks")
            d.set(x0, 11, zi, "spruce_planks")
            d.set(x0 + 2, 11, zi, "spruce_planks")


CG_CABIN = {True: (2, 8, 11, 19), False: (35, 8, 44, 19)}


def cg_cabin(d, L, west):
    """Side reading cabin (log, steep gable along z, stone stove), joined to the hall by a covered breezeway.
    West (L3): children's den.  East (L4): periodicals cabin."""
    x1, z1, x2, z2 = CG_CABIN[west]
    d.fill(x1 + 1, 1, z1 + 1, x2 - 1, 1, z2 - 1, "spruce_planks")
    cg_walls(d, x1, z1, x2, z2, 6)
    for z in (11, 12, 16, 17):
        for x in (x1, x2):
            if (x == x2) == west:                         # the hall side gets the door instead
                continue
            for y in (3, 4, 5):
                d.set(x, y, z, "glass_pane")
    for x in (x1 + 3, x1 + 4, x1 + 5, x1 + 6):
        for y in (3, 4, 5):
            d.set(x, y, z2, "glass_pane")
    d.gable(x1, z1, x2, z2, 7, "z", stairs="spruce_stairs", ridge="spruce_slab", end="spruce_planks", overhang=1)
    mid = (x1 + x2) // 2
    d.door(mid, 2, z1, "south", "spruce")
    # breezeway to the hall
    hx, cx_, dirn = (14, x2, 1) if west else (32, x1, -1)
    d.door(cx_, 2, 12, "east" if west else "west", "spruce")
    d.door(hx, 2, 12, "west" if west else "east", "spruce")
    for x in range(min(cx_, hx) + 1, max(cx_, hx)):
        d.set(x, 1, 12, "spruce_planks")
        d.set(x, 1, 11, "spruce_planks")
        d.set(x, 1, 13, "spruce_planks")
        for z in (11, 13):
            d.set(x, 2, z, fence("spruce_fence"))
        for z in (10, 11, 12, 13, 14):
            d.set(x, 5, z, slab("spruce_slab", "top"))
    for x in (min(cx_, hx) + 1, max(cx_, hx) - 1):
        for z in (11, 13):
            for y in (3, 4):
                d.set(x, y, z, LOGY)
    # stove in the back corner
    sx = x1 + 1 if west else x2 - 1
    d.set(sx, 2, z2 - 1, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for y in range(3, 13):
        d.set(sx, y, z2 - 1, rock(sx, y, z2 - 1))
    d.set(sx + (1 if west else -1), 2, z2 - 1, "cobblestone")
    d.set(sx, 2, z2 - 2, AIR)
    d.lamp(mid, 6, 13)
    d.lamp(mid, 6, 17)
    y = 2
    if west:                                              # children's den
        d.rug(4, 12, 7, 15, y, ("lime_carpet", "yellow_carpet"))
        d.chair(5, y, 17, "south", "spruce", arms=True)       # storyteller's chair
        for x in (4, 6, 7):
            d.chair(x, y, 14, "north", "birch")
        for z in (10, 11, 12):
            d.bookshelf(3, y, z)
        for x in (4, 5):
            d.bookshelf(x, y, 9)
        d.table(9, y, 10, "birch", "post")
        d.chair(9, y, 11, "south", "birch")
        d.chair(8, y, 10, "west", "birch")
        d.set(10, y, 18, "barrel[facing=up,open=false]")
        d.set(9, y, 18, "barrel[facing=up,open=false]")
        d.set(10, y, 9, "potted_fern")
        d.set(3, y, 18, AIR)
    else:                                                  # periodicals cabin
        for z in (10, 13, 16):
            d.item(43, y, z, "lectern[facing=west,has_book=true,powered=false]")
        for x, z in ((38, 11), (38, 15)):
            d.chair(x, y, z, "west", "dark_oak", arms=False)
            d.chair(x + 2, y, z, "east", "dark_oak", arms=False)
            d.set(x + 1, y, z, slab("spruce_slab", "top"))
            d.set(x + 1, y + 1, z, "candle[candles=1,lit=false,waterlogged=false]")
        d.counter(37, 18, 41, 18, y, "spruce_slab")
        d.set(38, y + 1, 18, "flower_pot")
        d.set(40, y + 1, 18, "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=false]")
        for x in (37, 38, 40, 41):
            d.bookshelf(x, y, 9)
        d.rug(38, 12, 40, 14, y, ("brown_carpet", "orange_carpet"))
        d.set(36, y, 9, "potted_fern")


def cg_decks(d):
    """L4: plank decks with log rails along both sides of the cross wing, benches and planters."""
    for x0, x1_ in ((14, 18), (28, 32)):
        for x in range(x0, x1_ + 1):
            for z in range(23, 35):
                d.set(x, 2, z, slab("spruce_slab"))
        rx = x0 if x0 == 14 else x1_
        for z in range(23, 36):
            d.set(rx, 3, z, fence("spruce_fence"))
        for x in range(x0, x1_ + 1):
            d.set(x, 3, 35, fence("spruce_fence"))
        d.set(x0, 2, 35, rock(x0, 2, 35))
    d.set(32, 3, 28, AIR)
    d.set(14, 3, 28, AIR)
    for z in (25, 26, 31, 32):
        d.chair(16, 3, z, "west", "spruce", sit=False)
    for z in (24, 33):
        d.set(30, 3, z, "potted_fern")
    d.table(30, 3, 29, "spruce", "post")
    d.chair(30, 3, 30, "south", "spruce", sit=False)
    d.chair(29, 3, 29, "west", "spruce", sit=False)
    for x, z in ((16, 28), (30, 26)):
        lamp_post(d, x, z, 3, "spruce_planks", fence("spruce_fence"), h=1)
    for px in (14, 32):                                    # shingled lean-to roofs over the decks
        for z in (24, 29, 35):
            for y in range(3, 7):
                d.set(px, y, z, LOGY)
    for z in range(24, 36):
        for i, x in enumerate((13, 14, 15, 16, 17, 18)):
            d.set(x, 7 + i // 2, z, stair("spruce_stairs", "east"))
        for i, x in enumerate((33, 32, 31, 30, 29, 28)):
            d.set(x, 7 + i // 2, z, stair("spruce_stairs", "west"))


def cg_fence(d, L):
    """L3: split-rail fence round the property, open at the road gate and the side paths."""
    rail = fence("spruce_fence")
    for x in range(0, 47):
        if not 21 <= x <= 25:
            d.set(x, 2, 0, rail)
    for z in range(1, 46):
        if z not in (12, 13):
            d.set(0, 2, z, rail)
            d.set(46, 2, z, rail)
    for x in (20, 26):
        d.set(x, 2, 0, LOGY)
        d.set(x, 3, 0, LOGY)
        d.set(x, 4, 0, lantern(False))


def cg_cupola(d):
    """L5: a timber lookout cupola on the hall ridge with louvres, a shingle cap and a weathervane."""
    x1, z1, x2, z2 = 21, 14, 25, 18
    for y in range(15, 21):
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                if x in (x1, x2) or z in (z1, z2):
                    corner = x in (x1, x2) and z in (z1, z2)
                    if corner:
                        d.set(x, y, z, LOGY)
                    elif y in (17, 18):
                        d.set(x, y, z, "glass_pane")
                    else:
                        d.set(x, y, z, LOGX if z in (z1, z2) else LOGZ)
    top = d.hip(x1, z1, x2, z2, 21, "spruce_stairs", "spruce_slab", overhang=1)
    d.set(23, top + 1, 16, fence("spruce_fence"))
    d.set(23, top + 2, 16, "lightning_rod[facing=up,powered=false,waterlogged=false]")


def cg_yard(d):
    """L5: fire-pit amphitheatre with log benches, a woodshed, picnic tables, spruces and a totem sign post."""
    cx, cz = 42, 39                                        # fire pit ring (x 39..45, z 35..43)
    d.set(cx, 1, cz, "cobblestone")
    d.set(cx, 2, cz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for dx, dz in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)):
        d.set(cx + dx, 2, cz + dz, slab("cobblestone_slab"))
    for x in range(39, 46):                               # log benches in a horseshoe
        if abs(x - cx) > 1:
            d.set(x, 2, 35, log("stripped_spruce_log", "x"))
    for z in (36, 37, 38, 39, 40, 41, 42):
        d.set(39, 2, z, log("stripped_spruce_log", "z"))
        d.set(45, 2, z, log("stripped_spruce_log", "z"))
    # woodshed (x 1..7, z 36..43): open-fronted lean-to with stacked cordwood
    for x in (1, 7):
        for z in (36, 43):
            for y in range(2, 6):
                d.set(x, y, z, LOGY)
    for x in range(1, 8):
        for z in range(35, 45):
            d.set(x, 6 if z < 40 else 5, z, stair("spruce_stairs", "south") if z < 40 else
                  stair("spruce_stairs", "north"))
    for x in range(2, 7):
        for y in (2, 3, 4):
            d.set(x, y, 43, log("oak_log", "z"))
        d.set(x, 2, 42, log("oak_log", "z"))
    d.set(4, 2, 38, log("spruce_log"))
    d.set(4, 3, 38, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    for x, z in ((10, 24), (10, 30)):                      # picnic tables
        d.set(x, 2, z, slab("spruce_slab", "top"))
        d.set(x + 1, 2, z, slab("spruce_slab", "top"))
        for xx in (x, x + 1):
            d.chair(xx, 2, z - 1, "north", "spruce", sit=False)
            d.chair(xx, 2, z + 1, "south", "spruce", sit=False)
    for x, z in ((1, 2), (1, 21), (45, 21), (44, 32), (9, 33), (37, 33)):
        cg_spruce(d, x, z)
    for y in range(2, 6):                                  # carved sign post at the road
        d.set(19, y, 1, LOGY if y < 5 else "carved_pumpkin[facing=north]")
    d.sign(19, 3, 0, "north", ["Great Library", "Reading Hall"], wood="spruce")


def cg_spruce(d, x, z):
    """A hand-placed spruce: trunk and stacked tiers."""
    for y in range(2, 8):
        d.set(x, y, z, log("spruce_log"))
    lv = "spruce_leaves[distance=1,persistent=true,waterlogged=false]"
    for y, r in ((4, 2), (5, 1), (6, 2), (7, 1), (8, 1), (9, 0)):
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                if abs(dx) + abs(dz) <= r + (1 if r == 2 else 0) and d.bp.inside(x + dx, y, z + dz) \
                        and d.air(x + dx, y, z + dz):
                    d.set(x + dx, y, z + dz, lv)
    d.set(x, 10, z, lv)


def cg_lookout(d):
    """L5: a fire lookout on the street corner (x 37..43, z 1..7): log legs with girts and cross-bracing, a
    ladder up a centre post, a glazed cab with the fire finder, bunk and radio, hipped shingle cap."""
    x1, z1, x2, z2 = 37, 1, 43, 7
    for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        d.set(x, 2, z, rock(x, 2, z))
        for y in range(3, 20):
            d.set(x, y, z, LOGY)
    for yg in (7, 13):                                     # girts
        for x in range(x1 + 1, x2):
            d.set(x, yg, z1, LOGX)
            d.set(x, yg, z2, LOGX)
        for z in range(z1 + 1, z2):
            d.set(x1, yg, z, LOGZ)
            d.set(x2, yg, z, LOGZ)
    for y0, y1 in ((3, 6), (8, 12), (14, 18)):             # X-bracing on every face
        n = y1 - y0
        for k in range(n + 1):
            o = 1 + round(k * 4 / n)
            for a in (o, 6 - o):
                d.set(x1 + a, y0 + k, z1, fence("spruce_fence"))
                d.set(x1 + a, y0 + k, z2, fence("spruce_fence"))
                d.set(x1, y0 + k, z1 + a, fence("spruce_fence"))
                d.set(x2, y0 + k, z1 + a, fence("spruce_fence"))
    for y in range(2, 19):
        d.set(40, y, 5, LOGY)
    d.fill(x1, 19, z1, x2, 19, z2, "spruce_planks")
    for y in range(2, 20):
        d.set(40, y, 4, ladder("north"))
    for y in range(20, 23):                                # cab
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                if x in (x1, x2) or z in (z1, z2):
                    corner = x in (x1, x2) and z in (z1, z2)
                    d.set(x, y, z, LOGY if corner else ("glass_pane" if y < 22 else
                                                         (LOGX if z in (z1, z2) else LOGZ)))
    d.hip(x1, z1, x2, z2, 23, "spruce_stairs", "spruce_slab", overhang=1)
    y = 20
    d.item(41, y, 5, "cartography_table")
    d.chair(42, y, 5, "east", "spruce", sit=False)
    d.bed(38, y, 2, "west", "green")
    d.set(42, y, 2, "jukebox[has_record=false]")
    d.set(38, y, 6, "barrel[facing=up,open=false]")
    d.set(38, y, 5, "spruce_slab[type=top,waterlogged=false]")
    d.set(38, y + 1, 5, "lantern[hanging=false,waterlogged=false]")
    d.set(41, y, 3, fence("spruce_fence"))
    d.set(41, y + 1, 3, "lightning_rod[facing=north,powered=false,waterlogged=false]")
    d.lamp(40, 22, 5)


def cg_cabin_porch(d):
    """L5: a shingled porch along the front of the west cabin with a bench and a lantern."""
    for x in (2, 6, 11):
        d.set(x, 2, 5, rock(x, 2, 5))
        for y in range(3, 6):
            d.set(x, y, 5, LOGY)
    for x in range(1, 13):
        d.set(x, 6, 4, stair("spruce_stairs", "south"))
        d.set(x, 6, 5, stair("spruce_stairs", "south"))
        d.set(x, 7, 6, stair("spruce_stairs", "south"))
        d.set(x, 6, 6, "spruce_planks")
        d.set(x, 1, 6, "spruce_planks")
        d.set(x, 1, 7, "spruce_planks")
    d.chair(3, 2, 7, "south", "spruce", sit=False)
    d.chair(4, 2, 7, "south", "spruce", sit=False)
    d.set(9, 2, 7, "potted_fern")
    d.set(6, 5, 6, lantern(True))


def cg_boardwalks(d):
    """L5: plank boardwalks down both side yards to the back of the lodge."""
    for z in range(20, 35):
        for x in (12, 13):
            d.set(x, 2, z, slab("spruce_slab"))
        for x in (33, 34):
            d.set(x, 2, z, slab("spruce_slab"))
    for z in (22, 28, 34):
        lamp_post(d, 14 if z != 34 else 11, z, 2, rock(14, 2, z), fence("spruce_fence"), h=1)
        lamp_post(d, 35, z, 2, rock(35, 2, z), fence("spruce_fence"), h=1)


def cg_finish_l5(d):
    """L5 finishing touches: annex chimney and dormers, river-rock entrance terrace, a log gateway over the
    road, more spruces, antler chandeliers in the hall."""
    for y in range(2, 19):                                 # annex gable chimney (bindery stove flue)
        for z in (39, 40, 41):
            d.set(38, y, z, rock(38, y, z))
    for z in (39, 41):
        d.set(38, 19, z, rock(38, 19, z))
    for x0 in (14, 30):                                    # dormers on the annex's north slope
        for x in (x0, x0 + 1, x0 + 2):
            for y in (14, 15):
                d.set(x, y, 37, "spruce_planks" if x != x0 + 1 else "glass_pane")
            d.set(x, 16, 37, stair("spruce_stairs", "south"))
            d.set(x, 16, 38, stair("spruce_stairs", "south"))
    for x in range(15, 32):                                # river-rock terrace before the porch
        for z in (1, 2, 3):
            if not 21 <= x <= 25:
                d.set(x, 2, z, slab(rock(x, 2, z) + "_slab"))
    for x in (20, 26):                                     # log gateway over the road
        for y in range(5, 8):
            d.set(x, y, 0, LOGY)
    d.fill(19, 8, 0, 27, 8, 0, log("spruce_log", "x"))
    d.sign(23, 7, 0, "north", ["Great Library"], wood="spruce")
    for x, z in ((44, 12), (1, 30), (45, 44), (8, 44)):
        cg_spruce(d, x, z)
    for x in (21, 25):                                     # antler chandeliers
        d.set(x, 6, 13, CHAIN)
        d.set(x, 5, 13, lantern(True))


def cg_cross_upper(d):
    """L5 upper storey of the cross wing (walk 10): the writers' retreat – desks at the windows, a stove,
    armchairs, a long shelf wall; reached by a ladder from the archive loft."""
    d.fill(20, 9, 23, 26, 9, 33, "spruce_planks")
    for z in (25, 26, 30, 31):
        for x in (19, 27):
            for y in (11, 12):
                d.set(x, y, z, "glass_pane")
    for x in (22, 23, 24):
        for y in range(10, 14):
            d.set(x, y, 34, "glass_pane")
    for y in range(7, 10):
        d.set(26, y, 31, ladder("west"))
    y = 10
    for z in (25, 30):
        desk(d, 20, y, z, "east", "spruce", light="lantern[hanging=false,waterlogged=false]" if z == 25 else
             "candle[candles=2,lit=false,waterlogged=false]")
    d.set(20, y, 26, "potted_fern")
    for z in range(23, 30):
        d.bookshelf(26, y, z, 2)
    d.set(23, y, 23, "campfire[facing=south,lit=true,signal_fire=false,waterlogged=false]")
    d.set(22, y, 23, "cobblestone")
    d.set(24, y, 23, "cobblestone")
    d.chair(22, y, 25, "north", "dark_oak")
    d.chair(24, y, 25, "north", "dark_oak")
    d.set(23, y, 25, slab("spruce_slab", "top"))
    d.rug(22, 27, 24, 29, y, ("red_carpet", "black_carpet"))
    d.set(25, y, 33, "barrel[facing=up,open=false]")
    d.set(21, y, 33, "chest[facing=north,type=single,waterlogged=false]")
    for z in (24, 28, 32):
        d.set(23, 14, z, CHAIN)
        d.set(23, 13, z, lantern(True))


def cg_annex(d, L):
    """L4: the lodge annex behind the cross wing (x 9..37, z 36..44), a storey and a half under a long
    shingle roof: rare-book room and bindery below, scholars' loft and archive stacks above."""
    x1, z1, x2, z2 = 9, 36, 37, 44
    d.fill(x1 + 1, 1, z1 + 1, x2 - 1, 1, z2 - 1, "spruce_planks")
    for z in (35,):
        for x in (22, 23, 24):
            d.set(x, 1, z, "spruce_planks")
    tall = L >= 5                                          # L5: raised to two full storeys
    cg_walls(d, x1, z1, x2, z2, 12 if tall else 8)
    if tall:
        for x in (11, 16, 21, 26, 31, 35):
            for z in (z1, z2):
                if not (x == 21 and z == z1):
                    d.set(x, 9, z, "glass_pane")
                    d.set(x, 10, z, "glass_pane")
    for x in (13, 18, 28, 33):
        for z in (z1, z2):
            for xx in (x, x + 1):
                for y in (4, 5, 6):
                    d.set(xx, y, z, "glass_pane")
                d.set(xx, 3, z, "dark_oak_planks")
    d.door(23, 2, z1, "south", "spruce")
    d.door(30, 2, z2, "north", "spruce")
    d.fill(x1 + 1, 6, z1 + 1, x2 - 1, 6, z2 - 1, "spruce_planks")
    d.fill(24, 2, z1 + 1, 24, 5, z2 - 1, LOGZ)            # partition
    d.door(24, 2, 41, "east", "spruce")
    d.gable(x1, z1, x2, z2, 13 if tall else 9, "x", stairs="spruce_stairs", ridge="spruce_slab",
            end="spruce_planks", overhang=1)
    for x in (x1, x2):
        for z in (39, 40, 41):
            d.set(x, 7, z, "glass_pane")
            d.set(x, 8, z, "glass_pane")
    for i in range(5):                                    # stair up the north wall, rising east
        d.set(11 + i, 2 + i, 37, stair("spruce_stairs", "east"))
        for yy in range(2, 2 + i):
            d.bookshelf(11 + i, yy, 37)
        if i < 4:
            d.set(11 + i, 6, 37, AIR)
            d.set(11 + i, 7, 38, fence("spruce_fence"))
    y = 2
    # rare-book room (x 10..23)
    for x in (17, 19, 21):
        d.set(x, y, 40, "spruce_planks")
        d.set(x, y + 1, 40, "glass")
    d.item(13, y, 42, "lectern[facing=north,has_book=true,powered=false]")
    d.item(20, y, 43, "lectern[facing=north,has_book=true,powered=false]")
    d.chair(11, y, 41, "west", "dark_oak", arms=True)
    d.chair(11, y, 43, "west", "dark_oak", arms=False)
    d.set(11, y, 42, slab("spruce_slab", "top"))
    d.set(11, y + 1, 42, "candle[candles=3,lit=false,waterlogged=false]")
    for x in (16, 17, 18, 19):
        d.bookshelf(x, y, 37, 2)
    d.rug(16, 41, 22, 42, y, ("red_carpet",), "plain")
    d.set(22, y, 37, "potted_fern")
    for x in (14, 20):
        d.lamp(x, 5, 40)
    # bindery (x 25..36)
    d.item(26, y, 37, "crafting_table")
    d.item(27, y, 37, "loom", "south")
    d.item(29, y, 37, "anvil", "east")
    d.set(31, y, 37, "water_cauldron[level=3]")
    d.item(33, y, 37, "grindstone", "south")
    d.counter(26, 40, 26, 42, y, "spruce_slab")
    d.set(26, y + 1, 41, "white_carpet")
    d.chair(27, y, 41, "east", "spruce")
    for z in (39, 40, 41, 42, 43):
        d.set(36, y, z, "barrel[facing=west,open=false]")
    for x in (32, 33, 34):
        d.bookshelf(x, y, 43, 2)
    d.set(25, y, 43, "potted_fern")
    for x in (28, 33):
        d.lamp(x, 5, 40)
    y = 7
    # scholars' loft (x 10..23): two bunks, a desk under the gable window, a trunk
    d.bed(10, y, 42, "west", "green")
    d.bed(10, y, 40, "west", "brown")
    d.set(10, y, 41, slab("spruce_slab", "top"))
    d.set(10, y + 1, 41, "lantern[hanging=false,waterlogged=false]")
    d.set(13, y, 43, "chest[facing=north,type=single,waterlogged=false]")
    desk(d, 18, y, 43, "north", "spruce", light="candle[candles=1,lit=false,waterlogged=false]")
    desk(d, 21, y, 43, "north", "spruce")
    d.rug(15, 40, 17, 41, y, ("green_carpet",), "plain")
    d.set(23, y, 39, "potted_fern")
    # archive stacks (x 25..36): shelf rows with aisles
    for x in (27, 30, 33):
        for z in (39, 40, 41):
            d.bookshelf(x, y, z, 2)
    d.chair(35, y, 40, "east", "spruce")
    d.set(36, y, 40, slab("spruce_slab", "top"))
    d.set(25, y, 43, "barrel[facing=up,open=false]")
    for x in (16, 29, 34):
        d.set(x, 9, 40, CHAIN)
        d.set(x, 8, 40, lantern(True))


def cg_cross_wing(d, L):
    """L3: the south cross wing (x 19..27, z 22..34): map and natural-history room with an archive loft."""
    x1, z1, x2, z2 = 19, 22, 27, 34
    tall = L >= 5                                         # L5: raised to two full storeys
    d.fill(x1 + 1, 1, z1 + 1, x2 - 1, 1, z2 - 1, "spruce_planks")
    cg_walls(d, x1, z1, x2, z2, 13 if tall else 8)
    for z in (25, 26, 30, 31):
        for x in (x1, x2):
            for y in (4, 5, 6):
                d.set(x, y, z, "glass_pane")
            d.set(x, 3, z, "dark_oak_planks")
    for x in (22, 23, 24):
        for y in range(3, 8):
            d.set(x, y, z2, "glass_pane")
    d.door(x2, 2, 28, "west", "spruce")
    if tall:
        d.gable(x1, z1, x2, z2, 14, "z", stairs="spruce_stairs", ridge="spruce_slab", end="spruce_planks",
                overhang=1)
        cg_cross_upper(d)
    else:
        d.gable(x1, 18, x2, z2, 9, "z", stairs="spruce_stairs", ridge="spruce_slab", end="spruce_planks",
                overhang=1)
    if L >= 4:                                            # door through to the lodge annex
        d.door(23, 2, z2, "north", "spruce")
    for z in (25, 28):
        d.fill(x1 + 1, 8, z, x2 - 1, 8, z, log("spruce_log", "x"))
    y = 2
    for x in (22, 23, 24):                                # map table
        for z in (25, 26):
            d.set(x, y, z, slab("spruce_slab", "top"))
    d.set(23, y + 1, 25, "white_carpet")
    d.set(23, y + 1, 26, "white_carpet")
    for x in (22, 24):
        d.chair(x, y, 24, "north", "spruce")
        d.chair(x, y, 27, "south", "spruce")
    d.item(26, y, 24, "cartography_table")
    for z in (24, 25, 26):                                # specimen cases
        d.set(20, y, z, "spruce_planks")
        d.set(20, y + 1, z, "glass")
    d.set(20, y + 2, 25, "potted_dead_bush")
    d.set(26, y, 30, fence("spruce_fence"))               # globe
    d.set(26, y + 1, 30, "lime_stained_glass")
    for z in (31, 32, 33):
        d.bookshelf(26, y, z, 2)
    d.rug(22, 29, 24, 32, y, ("green_carpet", "brown_carpet"))
    d.set(20, y, 33, "potted_fern")
    # archive loft (walk 7, z 30..33) up a ladder
    d.fill(x1 + 1, 6, 30, x2 - 1, 6, z2 - 1, "spruce_planks")
    for y2 in range(2, 7):
        d.set(20, y2, 29, ladder("east"))
    d.set(20, 6, 29, ladder("east"))
    for x in range(21, 27):
        d.set(x, 7, 30, fence("spruce_fence"))
    for x in (21, 22, 23):
        d.set(x, 7, 33, "barrel[facing=north,open=false]")
    d.set(26, 7, 33, "chest[facing=north,type=single,waterlogged=false]")
    d.set(26, 7, 32, "chest[facing=west,type=single,waterlogged=false]")
    desk(d, 24, 7, 33, "north", "spruce", light="lantern[hanging=false,waterlogged=false]")
    for z in (25, 28):
        d.set(23, 7, z, CHAIN)
        d.set(23, 6, z, lantern(True))


# ------------------------------------------------------------------------------------------------ registry
LIBRARY = {"Hearthwood": hw_library, "Neoterra": nt_library, "Cascadia": cg_library}
LIBRARY_WING = {"Hearthwood": hw_wing, "Neoterra": nt_wing, "Cascadia": cg_wing}


@design("greatlibrary")
def greatlibrary(pack, rel, L):
    return LIBRARY[pack](rel, L)


@design("greatlibrarywing")
def greatlibrarywing(pack, rel, L):
    return LIBRARY_WING[pack](rel, L)
