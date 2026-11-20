"""
Fortifications: barracks (+ its child barrackstower), gatehouse, wallguardtower.

Barracks (child huts = the towers with the bunk rooms; one more tower per level, 4 at L4/L5)
  Hearthwood  Stone castle: round corner towers (child) on a crenellated curtain wall with a gate tower and
              portcullis, a stone great hall with a steep tiled roof (armoury, mess table, hearth) along the back
              wall, archery butts and dummies in the bailey. L1-2 a low bailey wall, L3 the full curtain wall with
              wall walk and gate tower, L5 well, flag and banners.
  Cascadia    Frontier stockade fort: log blockhouses with overhanging upper storeys (child) at the corners, a
              pointed log palisade with a firing step and a timber gate with a walkway over it, a log barracks hall
              with porch and stone chimney, targets on the parade ground. L1-2 split-rail fence, L3 palisade.
  Neoterra    Security compound: slim concrete dorm towers with glass bands and roof watch posts (child) at the
              corners, a steel-bar perimeter fence on a concrete plinth with a sliding steel gate and guard booth,
              a glass-fronted HQ (armoury + briefing room) and a shooting range. L3 HQ upper floor, L5 helipad.
Gatehouse / wall guard tower: see the section headers below.
"""
from hm import Design, design, AIR, D4, OPP, CW, KEEP

ST = lambda m, f, h="bottom", s="straight": f"{m}_stairs[facing={f},half={h},shape={s},waterlogged=false]"
SL = lambda m, t="bottom": f"{m}_slab[type={t},waterlogged=false]"
TD = lambda m, f, h="top", o="false": f"{m}_trapdoor[facing={f},half={h},open={o},powered=false,waterlogged=false]"
LOG = lambda m, a="y": f"{m}[axis={a}]"
LANT = "lantern[hanging=true,waterlogged=false]"
LANT_S = "lantern[hanging=false,waterlogged=false]"
ROD = lambda f="up": f"lightning_rod[facing={f},powered=false,waterlogged=false]"
ENDROD = lambda f="up": f"end_rod[facing={f}]"
CHAIN = "chain[axis=y,waterlogged=false]"


def soft(d, fn, *a, **k):
    """Run a drawing helper so that it only writes into air cells."""
    orig = d.set

    def s(x, y, z, b, te=None):
        if d.bp.inside(x, y, z) and d.air(x, y, z):
            orig(x, y, z, b, te)
    d.set = s
    try:
        return fn(*a, **k)
    finally:
        del d.set


def ladder(d, x, z, y1, y2, facing):
    for y in range(y1, y2 + 1):
        d.set(x, y, z, f"ladder[facing={facing},waterlogged=false]")


def dummy(d, x, y, z, facing="north", head="carved_pumpkin"):
    d.set(x, y, z, "oak_fence")
    d.set(x, y + 1, z, "hay_block[axis=y]")
    d.set(x, y + 2, z, f"{head}[facing={facing}]")


def weapon_rack(d, cells, y, wood):
    for x, z in cells:
        d.set(x, y, z, SL(wood, "top"))
        d.set(x, y + 1, z, ROD())


def butt(d, x, y, z, facing="west"):
    """Archery butt: hay bale with the target on top (target counted as a yard fixture)."""
    d.set(x, y, z, "hay_block[axis=y]")
    d.yard_item(x, y + 1, z, "target")


def stone_mix(x, y, z, base="stone_bricks"):
    h = (x * 7 + y * 13 + z * 5) % 11
    if h == 0:
        return "mossy_stone_bricks"
    if h == 1:
        return "andesite" if base == "stone_bricks" else base
    return base


def beds(d, y, slots, n, color=None, ox=0, oz=0):
    for x, z, f in slots[:n]:
        d.bed(ox + x, y, oz + z, f, color)


def split(total, floors, cap):
    """Distribute `total` beds over `floors` as evenly as possible (max `cap` each)."""
    out = []
    left = total
    for i in range(floors):
        k = -(-left // (floors - i))
        out.append(min(cap, k))
        left -= out[-1]
    return out


# =========================================================================================== BARRACKS TOWERS
# --- Hearthwood: round stone tower, 9x9 box ----------------------------------------------------------------
HW_RING = ["...###...",
           ".##...##.",
           ".#.....#.",
           "#.......#",
           "#.......#",
           "#.......#",
           ".#.....#.",
           ".##...##.",
           "...###..."]


def mask(rows):
    foot, wall, inner = set(), set(), set()
    for z, row in enumerate(rows):
        xs = [x for x, c in enumerate(row) if c == "#"]
        for x in range(min(xs), max(xs) + 1):
            foot.add((x, z))
            (wall if row[x] == "#" else inner).add((x, z))
    return foot, wall, inner


HW_FOOT, HW_WALL, HW_IN = mask(HW_RING)
HW_TB = 9                                   # tower box
HW_THUT = (6, 1, 2)
HW_TST = {1: 2, 2: 3, 3: 3, 4: 4, 5: 5}     # storeys incl. the ground-floor guard room
HW_TSY = 4 * 5 + 7
HW_BED_SLOTS = [(3, 1, "north"), (5, 7, "south"), (5, 1, "north"), (3, 7, "south"), (7, 3, "east"),
                (7, 5, "east")]


def bt_hearthwood(rel, L):
    n = HW_TST[L]
    top = 4 * n
    d = Design("Hearthwood", rel, (HW_TB, HW_TSY, HW_TB), gy=0, paving="spruce_planks")
    for x in range(HW_TB):
        for z in range(HW_TB):
            if (x, z) not in HW_FOOT:
                for y in range(HW_TSY):
                    d.set(x, y, z, KEEP)
    for (x, z) in HW_WALL:
        d.set(x, 0, z, "cobblestone")
        for y in range(1, top + 2):
            d.set(x, y, z, stone_mix(x, y, z))
        d.set(x, 1, z, "cobblestone" if (x + z) % 3 else "mossy_cobblestone")
        # merlons on the parapet
        if (x + z) % 2 == 0:
            d.set(x, top + 2, z, stone_mix(x, top + 2, z))
    # string courses at the floors
    for k in range(1, n + 1):
        for (x, z) in HW_WALL:
            d.set(x, 4 * k, z, "polished_andesite" if k < n else "stone_bricks")
        for (x, z) in HW_IN:
            d.set(x, 4 * k, z, "spruce_planks" if k < n else "stone_bricks")
    # doors north and south, ladder on the west wall up to the roof
    d.door(4, 1, 0, "south", "spruce")
    d.door(4, 1, 8, "north", "spruce")
    d.set(4, 3, 0, "chiseled_stone_bricks")
    d.set(4, 3, 8, "chiseled_stone_bricks")
    ladder(d, 1, 4, 1, top, "east")
    # arrow slits
    for k in range(n):
        y = 4 * k + 2
        d.set(8, y, 4, "glass_pane")
        if k:
            d.set(4, y, 0, "glass_pane")
            d.set(4, y, 8, "glass_pane")
        d.set(1, y + 1, 1, "glass_pane") if k else None
        d.set(7, y + 1, 7, "glass_pane") if k else None
    # ground floor: guard room
    d.hut(*HW_THUT)
    weapon_rack(d, [(7, 3), (7, 5)], 1, "spruce")
    d.set(7, 1, 4, "chest[facing=west,type=single,waterlogged=false]")
    d.keg(2, 1, 6, "east")
    d.keg(2, 2, 6, "north")
    d.banner(7, 3, 4, "west", "red")
    d.lamp(4, 3, 4)
    # bunk floors
    per = split(4 * L, n - 1, 6)
    for k in range(1, n):
        y = 4 * k + 1
        m = per[k - 1]
        beds(d, y, HW_BED_SLOTS, m, "red")
        d.set(1, y, 3, "chest[facing=east,type=single,waterlogged=false]")
        if m <= 4:
            weapon_rack(d, [(7, 3), (7, 5)], y, "spruce")
            d.banner(7, y + 2, 4, "west", "white" if k % 2 else "red")
        else:
            d.set(7, y, 4, SL("spruce", "top"))
            d.candle(7, y + 1, 4, 2)
        d.rug(3, 3, 5, 5, y, ("red_carpet",), "plain")
        d.lamp(4, y + 2, 4)
    # roof: battlements, brazier, flag at L5
    d.set(6, top + 1, 6, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    if L >= 4:
        for y in range(top + 1, top + 6):
            d.set(4, y, 4, "spruce_fence")
        d.set(5, top + 5, 4, "red_wool")
        d.set(6, top + 5, 4, "red_wool")
        d.set(5, top + 4, 4, "white_wool")
        d.set(6, top + 4, 4, "red_wool") if L == 5 else None
    return d


# --- Cascadia: log blockhouse, 9x9 box (7x7 stone ground storey, 9x9 overhanging log storeys) --------------
CS_TB = 9
CS_THUT = (2, 1, 2)
CS_TUP = {1: 1, 2: 1, 3: 2, 4: 2, 5: 3}     # overhanging log storeys
CS_TSY = 24
CS_BED_SLOTS = [(1, 1, "west"), (7, 1, "east"), (1, 7, "west"), (7, 7, "east"), (1, 3, "west"), (7, 3, "east"),
                (1, 5, "west"), (7, 5, "east")]
RIVER = ["cobblestone", "mossy_cobblestone", "andesite", "cobblestone", "tuff", "mossy_cobblestone"]


def rock(x, y, z):
    return RIVER[(x * 5 + z * 3 + y * 7) % len(RIVER)]


def bt_cascadia(rel, L):
    nu = CS_TUP[L]
    d = Design("Cascadia", rel, (CS_TB, CS_TSY, CS_TB), gy=0, paving="spruce_planks")
    roof_y = 4 * (nu + 1) + 1
    for x in range(CS_TB):
        for z in range(CS_TB):
            ground = 1 <= x <= 7 and 1 <= z <= 7
            for y in range(0, 4 if not ground else 0):
                d.set(x, y, z, KEEP)
            for y in range(roof_y + 6, CS_TSY):
                d.set(x, y, z, KEEP)
    # ground storey: river-rock walls
    for x in range(1, 8):
        for z in range(1, 8):
            if x in (1, 7) or z in (1, 7):
                for y in range(0, 4):
                    d.set(x, y, z, rock(x, y, z))
    d.door(4, 1, 1, "south", "spruce")
    d.door(4, 1, 7, "north", "spruce")
    for z in (3, 5):
        d.set(1, 2, z, "spruce_fence")
        d.set(7, 2, z, "spruce_fence")
    # overhanging log storeys
    for k in range(1, nu + 1):
        d.fill(0, 4 * k, 0, 8, 4 * k, 8, "spruce_planks")
        for x in range(9):
            for z in range(9):
                if x in (0, 8) or z in (0, 8):
                    d.set(x, 4 * k, z, LOG("dark_oak_log", "x" if z in (0, 8) else "z"))
                    corner = x in (0, 8) and z in (0, 8)
                    for y in range(4 * k + 1, 4 * k + 4):
                        d.set(x, y, z, LOG("spruce_log") if corner else
                              LOG("stripped_spruce_log", "x" if z in (0, 8) else "z"))
        y = 4 * k + 2
        for x, z in ((0, 4), (8, 4), (4, 0), (4, 8), (2, 0), (6, 0), (2, 8), (6, 8)):
            d.set(x, y, z, "glass_pane")
        # murder-hole trapdoors under the overhang
        for x in (2, 4, 6):
            d.set(x, 4 * k - 1, 0, TD("spruce", "south", "top")) if k == 1 else None
            d.set(x, 4 * k - 1, 8, TD("spruce", "north", "top")) if k == 1 else None
    top = 4 * (nu + 1)
    d.fill(0, top, 0, 8, top, 8, "spruce_planks")
    for x in range(9):
        for z in range(9):
            if x in (0, 8) or z in (0, 8):
                d.set(x, top, z, LOG("dark_oak_log", "x" if z in (0, 8) else "z"))
    ridge = d.hip(0, 0, 8, 8, top + 1, "dark_oak_stairs", "dark_oak_slab", overhang=0)
    if L >= 3:                                                     # lookout lantern on the roof peak
        d.set(4, ridge + 1, 4, "spruce_fence")
        d.set(4, ridge + 2, 4, LANT_S)
    # central post + ladder
    for y in range(1, top):
        d.set(4, y, 5, LOG("stripped_spruce_log"))
    ladder(d, 4, 4, 1, 4 * nu, "north")
    # ground floor: store and guard room
    d.hut(*CS_THUT)
    d.set(6, 1, 2, "barrel[facing=up,open=false]")
    d.set(6, 2, 2, "barrel[facing=up,open=false]")
    d.set(6, 1, 6, "chest[facing=west,type=single,waterlogged=false]")
    d.set(2, 1, 6, "spruce_log[axis=z]")
    d.set(2, 2, 6, "spruce_log[axis=z]")
    d.set(3, 3, 3, LANT)
    # bunk rooms
    per = split(4 * L, nu, 8)
    for k in range(1, nu + 1):
        y = 4 * k + 1
        beds(d, y, CS_BED_SLOTS, per[k - 1], "brown")
        free = [(1, z) for z in (2, 4, 6)] + [(7, z) for z in (2, 4, 6)]
        for i, (x, z) in enumerate(free):
            if d.air(x, y, z) and i % 2 == 0:
                d.set(x, y, z, "chest[facing=%s,type=single,waterlogged=false]" % ("east" if x == 1 else "west"))
        d.set(3, y + 2, 4, LANT)
        d.set(5, y + 2, 6, LANT)
    return d


# --- Neoterra: slim concrete dorm tower, 7x7 ----------------------------------------------------------------
NT_TB = 7
NT_THUT = (1, 1, 1)
NT_TSY = 30
NT_BED_SLOTS = [(1, 1, "west"), (5, 1, "east"), (1, 5, "west"), (5, 5, "east")]


def bt_neoterra(rel, L):
    n = L + 1
    top = 4 * n
    d = Design("Neoterra", rel, (NT_TB, NT_TSY, NT_TB), gy=0, paving="polished_diorite")
    for x in range(7):
        for z in range(7):
            if x in (0, 6) or z in (0, 6):
                corner = x in (0, 6) and z in (0, 6)
                for y in range(1, top + 1):
                    d.set(x, y, z, "light_gray_concrete" if corner else "white_concrete")
    for k in range(1, n + 1):
        d.fill(1, 4 * k, 1, 5, 4 * k, 5, "light_gray_concrete" if k < n else "smooth_stone")
        for x in range(7):
            for z in range(7):
                if (x in (0, 6) or z in (0, 6)) and not (x in (0, 6) and z in (0, 6)):
                    d.set(x, 4 * k, z, "cyan_terracotta")
    # ribbon windows
    for k in range(n):
        y = 4 * k + 2
        for a in (2, 3, 4):
            for yy in (y, y + 1):
                if k:
                    d.set(a, yy, 0, "glass_pane")
                    d.set(a, yy, 6, "glass_pane")
                d.set(0, yy, a, "light_gray_stained_glass_pane")
                d.set(6, yy, a, "light_gray_stained_glass_pane")
    for z in (0, 6):
        for x in (2, 4):
            d.window(x, 1, z, x, 3, z)
    d.door(3, 1, 0, "south", "birch")
    d.door(3, 1, 6, "north", "birch")
    d.set(3, 3, 0, "glass")
    d.set(3, 3, 6, "glass")
    # lift core + ladder
    for y in range(1, top):
        d.set(3, y, 3, "light_gray_concrete")
    ladder(d, 3, 2, 1, top, "north")
    d.hut(*NT_THUT)
    d.set(5, 1, 1, "smooth_quartz_slab[type=top,waterlogged=false]")
    d.set(5, 1, 5, "light_gray_shulker_box[facing=up]")
    d.set(1, 1, 5, "potted_bamboo")
    d.set(3, 3, 4, "sea_lantern")
    for k in range(1, n):
        y = 4 * k + 1
        beds(d, y, NT_BED_SLOTS, 4, "cyan")
        d.set(1, y, 3, "smooth_quartz_slab[type=top,waterlogged=false]")
        d.set(1, y + 1, 3, "potted_bamboo" if k % 2 else "potted_cactus")
        d.set(5, y, 3, "light_gray_shulker_box[facing=up]")
        d.set(3, y + 2, 4, "sea_lantern")
    # roof watch post: glass rail, searchlight, antenna
    for x in range(7):
        for z in range(7):
            if x in (0, 6) or z in (0, 6):
                d.set(x, top + 1, z, "light_gray_concrete" if x in (0, 6) and z in (0, 6) else
                      "light_gray_stained_glass_pane")
    d.set(5, top + 1, 5, "sea_lantern")
    d.set(5, top + 2, 5, "daylight_detector[inverted=false,power=0]")
    for y in range(top + 2, top + 5):
        d.set(0, y, 0, ROD() if y == top + 4 else "iron_bars")
    if L >= 3:
        d.set(6, top + 2, 6, ENDROD())
        d.set(6, top + 2, 0, ENDROD())
        d.set(0, top + 2, 6, ENDROD())
    return d


@design("barrackstower")
def barrackstower(pack, rel, L):
    return {"Hearthwood": bt_hearthwood, "Cascadia": bt_cascadia, "Neoterra": bt_neoterra}[pack](rel, L)


TOWER = "military/barrackstower0.blueprint"


# ================================================================================================ BARRACKS
def hw_bar(rel, L):
    S = 33
    d = Design("Hearthwood", rel, (S, HW_TSY + 2, S), gy=1, paving="grass_block[snowy=false]")
    boxes = {"SW": (1, 23), "SE": (23, 23), "NW": (1, 1), "NE": (23, 1)}
    order = ["SW", "SE", "NW", "NE"]
    built = order[:min(L, 4)]
    full = L >= 3
    # bailey ground
    d.fill(4, 1, 4, 28, 1, 28, "coarse_dirt")
    for x in range(15, 18):
        for z in range(2, 19):
            d.set(x, 1, z, "gravel" if (x + z) % 4 else "cobblestone")
    # ---- walls ----------------------------------------------------------------------------------------
    def wall_cells():
        cells = []   # (x, z, role) role: 'out' = outer (parapet) line, 'in' = walk line
        for z in range(3, 30):
            cells.append((3, z, "out"))
            cells.append((4, z, "in"))
            cells.append((29, z, "out"))
            cells.append((28, z, "in"))
        for x in range(5, 28):
            cells.append((x, 3, "out"))
            cells.append((x, 4, "in"))
            if not 10 <= x <= 22:
                cells.append((x, 29, "out"))
                cells.append((x, 28, "in"))
        return cells

    def keep_cell(x, z):
        """False for cells inside a built tower box that are not right where a wall run meets the tower."""
        for k in built:
            X0, Z0 = boxes[k]
            rx, rz = x - X0, z - Z0
            if 0 <= rx < HW_TB and 0 <= rz < HW_TB:
                bands = {"NW": (rz >= 7 or rx >= 7), "NE": (rz >= 7 or rx <= 1),
                         "SW": (rz <= 1 or rx >= 7), "SE": (rz <= 1 or rx <= 1)}[k]
                return bands
        return True

    for x, z, role in wall_cells():
        if not keep_cell(x, z):
            continue
        gate = 15 <= x <= 17 and z in (3, 4)
        if gate:
            continue
        if full:
            if role == "in" and x not in (3, 29) and z not in (3, 29):
                for y in range(2, 6):
                    d.set(x, y, z, stone_mix(x, y, z))
            else:
                for y in range(2, 7):
                    d.set(x, y, z, stone_mix(x, y, z))
                if (x + z) % 2 == 0:
                    d.set(x, 7, z, stone_mix(x, 7, z))
            d.set(x, 2, z, "cobblestone" if (x * 3 + z) % 4 else "mossy_cobblestone")
        elif role == "out":
            d.set(x, 2, z, "stone_bricks")
            d.set(x, 3, z, "mossy_cobblestone_wall" if (x + z) % 5 == 0 else "cobblestone_wall")
    # wall-walk lanes: inner line top is the walk; make sure the corners of the inner line are walkable
    if full:
        # gate tower with winch room and battlements
        for x in range(13, 20):
            for z in range(2, 6):
                edge = x in (13, 19) or z in (2, 5)
                for y in range(2, 11):
                    d.set(x, y, z, stone_mix(x, y, z) if edge or y in (6, 10) or y < 6 else AIR)
                d.set(x, 11, z, stone_mix(x, 11, z) if edge else AIR)
                if edge and (x + z) % 2 == 1:
                    d.set(x, 12, z, stone_mix(x, 12, z))
        d.clear(15, 2, 2, 17, 5, 5)
        for z in (2, 5):
            d.set(15, 5, z, ST("stone_brick", "west", "top"))
            d.set(17, 5, z, ST("stone_brick", "east", "top"))
            d.set(16, 6, z, "chiseled_stone_bricks")
        for x in range(15, 18):
            d.set(x, 5, 3, "iron_bars")                       # raised portcullis
        for x in (14, 18):                                    # torches on the front
            d.set(x, 4, 1, "wall_torch[facing=north]")
        # doorways from the wall walks into the winch room, chains and winch
        for x, f in ((13, "east"), (19, "west")):
            d.set(x, 7, 4, AIR)
            d.set(x, 8, 4, AIR)
        for x in range(15, 18):
            d.set(x, 7, 3, CHAIN)
            d.set(x, 8, 3, CHAIN)
            d.set(x, 9, 3, CHAIN)
        d.set(16, 7, 4, "grindstone[face=floor,facing=east]")
        ladder(d, 18, 3, 7, 10, "west")
        d.set(14, 9, 4, LANT)
        d.set(16, 8, 2, "glass_pane")
        d.banner(14, 8, 1, "north", "red")
        d.banner(18, 8, 1, "north", "red")
        # stairs up to the wall walk on both side walls
        for xs, inner in ((5, 4), (27, 28)):
            for i in range(4):
                z = 18 - i
                d.set(xs, 2 + i, z, ST("stone_brick", "north"))
                for y in range(2, 2 + i):
                    d.set(xs, y, z, "stone_bricks")
        # stairs up to the north wall walk beside the gate tower
        for i in range(4):
            for x in (11, 21):
                d.set(x, 2 + i, 8 - i, ST("stone_brick", "north"))
                for y in range(2, 2 + i):
                    d.set(x, y, 8 - i, "stone_bricks")
    else:
        for x in (14, 18):                                    # gate posts of the bailey wall
            for y in range(2, 5):
                d.set(x, y, 3, "stone_bricks")
            d.set(x, 5, 3, LANT_S)
    # ---- great hall ---------------------------------------------------------------------------------
    hx1, hz1, hx2, hz2 = 10, 19, 22, 29
    d.box(hx1, 2, hz1, hx2, 6, hz2, "stone_bricks", floor="oak_planks")
    for x in range(hx1, hx2 + 1):
        for z in range(hz1, hz2 + 1):
            if x in (hx1, hx2) or z in (hz1, hz2):
                for y in range(2, 7):
                    d.set(x, y, z, stone_mix(x, y, z))
                d.set(x, 2, z, "cobblestone" if (x + z) % 3 else "mossy_cobblestone")
    d.fill(hx1 + 1, 7, hz1 + 1, hx2 - 1, 7, hz2 - 1, "dark_oak_planks")
    for x in (hx1, hx2):                                      # buttress-like quoins
        for z in (hz1, hz2):
            for y in range(2, 7):
                d.set(x, y, z, "polished_andesite" if y % 2 else "stone_bricks")
    ridge = soft(d, d.gable, hx1, hz1, hx2, hz2, 7, "x", "deepslate_tile_stairs", "deepslate_tile_slab",
                 "stone_bricks", 1)
    for x in (hx1 - 1, hx2 + 1):                              # keep the roof off the towers
        for z in range(hz1 - 1, hz2 + 2):
            for y in range(5, ridge + 1):
                if "deepslate_tile" in d.get(x, y, z):
                    d.set(x, y, z, AIR)
    for z in range(hz1, hz2 + 1):                             # gable ends: tile-hung top
        for x in (hx1, hx2):
            for y in range(7, ridge):
                if d.get(x, y, z) == "minecraft:stone_bricks" and (z + y) % 4 == 0:
                    d.set(x, y, z, "mossy_stone_bricks")
    # doorway, leaded windows
    d.door(16, 2, hz1, "south", "dark_oak")
    d.set(16, 4, hz1, "chiseled_stone_bricks")
    d.set(15, 4, hz1, ST("stone_brick", "west", "top"))
    d.set(17, 4, hz1, ST("stone_brick", "east", "top"))
    d.set(15, 3, hz1 - 1, "wall_torch[facing=north]")
    d.set(17, 3, hz1 - 1, "wall_torch[facing=north]")
    for x in (12, 13, 19, 20):
        d.window(x, 3, hz1, x, 5, hz1)
    for x in (13, 19):
        d.window(x, 4, hz2, x, 5, hz2)
    d.set(16, 8, hz1, "glass_pane")
    # interior
    d.hut(11, 2, 20)
    weapon_rack(d, [(11, 22), (11, 23), (11, 24)], 2, "dark_oak")
    d.banner(11, 4, 23, "east", "red")
    d.item(13, 2, 26, "anvil", "east")
    d.item(11, 2, 28, "barrel")
    d.item(12, 2, 28, "barrel")
    d.set(11, 2, 27, "grindstone[face=floor,facing=east]")
    if L >= 3:
        d.item(11, 2, 26, "smithing_table")
    d.set(13, 2, 28, "chest[facing=north,type=single,waterlogged=false]")
    d.set(14, 2, 28, "chest[facing=north,type=single,waterlogged=false]")
    # mess table with benches
    for x in range(15, 19):
        d.table(x, 2, 24, "dark_oak", "block", "dark_oak_planks" if x % 2 else "stripped_dark_oak_wood[axis=x]")
        d.chair(x, 2, 23, "north", "dark_oak", sit=False)
        d.chair(x, 2, 25, "south", "dark_oak", sit=False)
    d.set(15, 3, 24, "candle[candles=3,lit=false,waterlogged=false]")
    d.set(18, 3, 24, "candle[candles=2,lit=false,waterlogged=false]")
    # hearth on the east wall, chimney through the roof
    d.hearth(21, 2, 24, "west", ridge + 3, "bricks", "campfire")
    for y in range(2, ridge + 3):
        d.set(22, y, 24, "bricks")
    d.rug(19, 23, 20, 25, 2, ("red_carpet",), "plain")
    d.banner(21, 4, 21, "west", "red")
    d.banner(21, 4, 27, "west", "white")
    for x in (13, 16, 19):
        d.lamp(x, 6, 22)
        d.lamp(x, 6, 26)
    # ---- bailey -------------------------------------------------------------------------------------
    nt = {1: 2, 2: 3, 3: 4, 4: 5, 5: 5}[L]
    for i in range(nt):
        butt(d, 26, 2, 6 + 2 * i)
    for z in range(6, 15, 2):
        d.set(21, 1, z, "stone_bricks")                       # shooting line marks
    for x, z in ((8, 9), (8, 13)):
        dummy(d, x, 2, z, "east")
    d.set(7, 2, 16, "hay_block[axis=x]")
    d.set(8, 2, 16, "hay_block[axis=y]")
    d.set(7, 2, 6, "water_cauldron[level=3]")
    d.set(7, 2, 7, "chest[facing=east,type=single,waterlogged=false]") if L >= 2 else None
    if L >= 2:
        for x, z in ((13, 9), (19, 9)):                       # lantern posts by the path
            d.set(x, 2, z, "cobblestone_wall")
            d.set(x, 3, z, "cobblestone_wall")
            d.set(x, 4, z, LANT_S)
    if L >= 4:                                                # flag pole
        for y in range(2, 11):
            d.set(11, y, 12, "spruce_fence")
        d.set(11, 1, 12, "stone_bricks")
        for x, y in ((12, 10), (13, 10), (12, 9), (13, 9)):
            d.set(x, y, 12, "red_wool" if (x + y) % 2 else "white_wool")
    if L >= 5:                                                # well
        for x in range(19, 22):
            for z in range(12, 15):
                d.set(x, 2, z, "cobblestone" if (x, z) != (20, 13) else "water[level=0]")
                d.set(x, 1, z, "cobblestone")
        for x, z in ((19, 12), (21, 12), (19, 14), (21, 14)):
            d.set(x, 3, z, "spruce_fence")
            d.set(x, 4, z, "spruce_fence")
        d.fill(19, 5, 12, 21, 5, 14, "spruce_slab[type=bottom,waterlogged=false]")
        d.set(20, 4, 13, CHAIN)
        for x in range(6, 27, 4):                             # banners along the north wall
            if not 12 <= x <= 20:
                d.banner(x, 5, 5, "south", "red")
    # ---- towers (child huts) --------------------------------------------------------------------------
    for k in built:
        X0, Z0 = boxes[k]
        for (rx, rz) in HW_FOOT:
            d.reserve(X0 + rx, 1, Z0 + rz, X0 + rx, HW_TSY, Z0 + rz)
        d.child_hut(X0 + HW_THUT[0], 2, Z0 + HW_THUT[2], TOWER)
    return d


def cs_bar(rel, L):
    d = Design("Cascadia", rel, (33, CS_TSY + 2, 29), gy=1, paving="grass_block[snowy=false]")
    boxes = {"SW": (1, 19), "NE": (23, 1), "SE": (23, 19), "NW": (1, 1)}
    order = ["SW", "NE", "SE", "NW"]
    built = order[:min(L, 4)]
    full = L >= 3
    # parade ground
    for x in range(4, 29):
        for z in range(4, 25):
            d.set(x, 1, z, "coarse_dirt" if (x * 3 + z * 7) % 5 else "gravel")
    for x in range(15, 18):
        for z in range(0, 13):
            d.set(x, 1, z, "dirt_path")

    def in_ground(x, z):
        for k in built:
            X0, Z0 = boxes[k]
            if 1 <= x - X0 <= 7 and 1 <= z - Z0 <= 7:
                return True
        return False
    lines = [(3, z) for z in range(3, 26)] + [(29, z) for z in range(3, 26)] + \
            [(x, 3) for x in range(4, 29)] + [(x, 25) for x in range(4, 29)]
    inner = {(3, 0): (4, 0), (29, 0): (28, 0)}
    for x, z in lines:
        if in_ground(x, z) or (15 <= x <= 17 and z == 3):
            continue
        if full:
            for y in range(2, 7):
                d.set(x, y, z, LOG("spruce_log"))
            d.set(x, 7, z, "spruce_fence" if (x + z) % 2 else LOG("stripped_spruce_log"))
            d.set(x, 1, z, rock(x, 1, z))
            # firing step on the inside
            ix, iz = (x + (1 if x == 3 else -1 if x == 29 else 0), z + (1 if z == 3 else -1 if z == 25 else 0))
            if 4 <= ix <= 28 and 4 <= iz <= 24 and not in_ground(ix, iz) and not (14 <= ix <= 18 and iz == 4):
                if d.air(ix, 4, iz):
                    d.set(ix, 4, iz, SL("spruce", "top"))
                if (ix + iz) % 4 == 0 and d.air(ix, 3, iz):
                    for y in (2, 3):
                        d.set(ix, y, iz, "spruce_fence")
        else:
            post = (x + z) % 3 == 0
            d.set(x, 2, z, LOG("spruce_log") if post else "spruce_fence")
            d.set(x, 3, z, "spruce_fence" if post else AIR)
    # gate
    if full:
        for x in (14, 18):
            for z in (2, 3, 4):
                for y in range(2, 10 if z == 3 else 7):
                    d.set(x, y, z, LOG("spruce_log"))
                d.set(x, 1, z, rock(x, 1, z))
            d.set(x, 10, 3, LANT_S)
        for x in range(14, 19):
            for z in (2, 3, 4):
                d.set(x, 6, z, "spruce_planks" if 15 <= x <= 17 else d.get(x, 6, z))
            d.set(x, 7, 2, "spruce_fence")
            d.set(x, 9, 3, LOG("stripped_spruce_log", "x"))
        for x in (15, 17):
            d.set(x, 5, 2, ST("spruce", "east" if x == 15 else "west", "top"))
        ladder(d, 14, 5, 2, 6, "south")
        d.set(14, 6, 5, "ladder[facing=south,waterlogged=false]")
        for x in (15, 16, 17):                                # gate leaves swung open against the palisade
            pass
        d.set(13, 2, 4, TD("spruce", "east", "bottom", "true"))
        d.set(19, 2, 4, TD("spruce", "west", "bottom", "true"))
        d.sign(16, 8, 1, "north", ["FORT", "TIMBERLINE", "~ 1872 ~"], "spruce")
        d.set(16, 8, 2, "spruce_planks")
        d.set(15, 8, 2, "spruce_planks")
        d.set(17, 8, 2, "spruce_planks")
        if L >= 5:                                            # roofed walkway with the alarm bell
            for x in range(13, 20):
                d.set(x, 10, 1, ST("dark_oak", "south"))
                d.set(x, 11, 2, ST("dark_oak", "south"))
                d.set(x, 11, 3, SL("dark_oak"))
                d.set(x, 11, 4, ST("dark_oak", "north"))
                d.set(x, 10, 5, ST("dark_oak", "north"))
            d.set(16, 10, 3, "bell[attachment=ceiling,facing=north,powered=false]")
            d.set(14, 10, 3, LOG("spruce_log"))
            d.set(18, 10, 3, LOG("spruce_log"))
    else:
        for x in (14, 18):
            for y in range(2, 5):
                d.set(x, y, 3, LOG("spruce_log"))
            d.set(x, 5, 3, LANT_S)
    # ---- barracks hall: log building with porch and stone chimney -------------------------------------
    x1, z1, x2, z2 = 11, 13, 21, 21
    d.fill(x1, 1, z1, x2, 1, z2, "cobblestone")
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if x in (x1, x2) or z in (z1, z2):
                corner = x in (x1, x2) and z in (z1, z2)
                for y in range(2, 6):
                    d.set(x, y, z, LOG("stripped_spruce_log") if corner else LOG("spruce_log", "x" if z in (z1, z2) else "z"))
                d.set(x, 2, z, rock(x, 2, z))
            else:
                d.set(x, 1, z, "spruce_planks")
                for y in range(2, 6):
                    d.set(x, y, z, AIR)
    for x in range(x1, x2 + 1):
        d.set(x, 6, z1, LOG("stripped_spruce_log", "x"))
        d.set(x, 6, z2, LOG("stripped_spruce_log", "x"))
    for z in range(z1, z2 + 1):
        d.set(x1, 6, z, LOG("stripped_spruce_log", "z"))
        d.set(x2, 6, z, LOG("stripped_spruce_log", "z"))
    d.fill(x1 + 1, 6, z1 + 1, x2 - 1, 6, z2 - 1, "spruce_planks")
    ridge = d.gable(x1, z1, x2, z2, 7, "x", "dark_oak_stairs", "dark_oak_slab", "spruce_planks", 1)
    for z in range(z1, z2 + 1):                               # board-and-batten gables
        for x in (x1, x2):
            for y in range(7, ridge):
                if d.get(x, y, z) == "minecraft:spruce_planks" and z % 2 == 0:
                    d.set(x, y, z, LOG("stripped_spruce_log"))
    d.door(16, 2, z1, "south", "spruce")
    d.set(16, 4, z1, LOG("stripped_spruce_log", "x"))
    for x in (13, 19):
        d.window(x, 3, z1, x, 4, z1)
        d.window(x, 3, z2, x, 4, z2)
    for z in (15, 19):
        d.window(x1, 3, z, x1, 4, z)
    d.window(16, 8, z1 - 0, 16, 9, z1) if d.get(16, 8, z1) == "minecraft:spruce_planks" else None
    # porch
    for x in range(x1, x2 + 1):
        for z in range(z1 - 3, z1):
            d.set(x, 1, z, "spruce_planks")
            d.set(x, 5, z, SL("spruce"))
        d.set(x, 5, z1 - 4, ST("spruce", "south"))
    for x in (x1, 14, 18, x2):
        for y in range(2, 5):
            d.set(x, y, z1 - 3, LOG("spruce_log"))
    for x in range(x1 + 1, x2):
        if x not in (14, 18) and not 15 <= x <= 17:
            d.set(x, 2, z1 - 3, "spruce_fence")
    d.chair(12, 2, z1 - 1, "south", "spruce", sit=False)
    d.chair(20, 2, z1 - 1, "south", "spruce", sit=False)
    d.keg(13, 2, z1 - 1, "north")
    d.set(15, 4, z1 - 2, LANT)
    d.set(17, 4, z1 - 2, LANT)
    d.sign(16, 5, z1 - 1, "north", ["BARRACKS"], "spruce") if False else None
    # stone chimney on the east gable
    d.hearth(x2 - 1, 2, 17, "west", ridge + 2, "cobblestone", "campfire")
    for y in range(1, ridge + 2):
        d.set(x2 + 1, y, 17, rock(x2 + 1, y, 17))
        d.set(x2, y, 17, rock(x2, y, 17))
    # interior
    d.hut(12, 2, 14)
    weapon_rack(d, [(12, 16), (12, 17), (12, 18)], 2, "spruce")
    d.banner(12, 4, 17, "east", "green")
    d.item(12, 2, 20, "barrel")
    d.item(14, 2, 20, "barrel")
    d.item(13, 2, 20, "anvil", "east")
    if L >= 3:
        d.item(15, 2, 20, "smithing_table")
    d.set(12, 3, 20, "barrel[facing=up,open=false]") if False else None
    for x in range(15, 19):
        d.table(x, 2, 17, "spruce", "block", "stripped_spruce_wood[axis=x]")
        d.chair(x, 2, 16, "north", "spruce", sit=False)
    d.set(15, 3, 17, "candle[candles=2,lit=false,waterlogged=false]")
    d.rug(19, 16, 19, 18, 2, ("brown_carpet",), "plain")
    d.chair(19, 2, 15, "north", "spruce", sit=False)
    d.set(20, 2, 14, "chest[facing=west,type=single,waterlogged=false]")
    for x in (13, 16, 19):
        d.lamp(x, 5, 17)
    # behind the hall: woodpile
    for x in range(12, 17):
        d.set(x, 2, 23, LOG("spruce_log", "x"))
        if x % 2:
            d.set(x, 3, 23, LOG("spruce_log", "x"))
    d.set(18, 2, 23, "chopping_block" if False else "spruce_log[axis=y]")
    # ---- parade ground ----------------------------------------------------------------------------
    nt = {1: 2, 2: 3, 3: 4, 4: 5, 5: 5}[L]
    for i in range(nt):
        butt(d, 6, 2, 10 + 2 * i)
    for x, z in ((26, 12), (26, 15)):
        dummy(d, x, 2, z, "west")
    d.set(25, 2, 18, "water_cauldron[level=3]")
    d.set(26, 2, 18, "hay_block[axis=x]")
    d.set(26, 2, 19, "hay_block[axis=y]") if L >= 2 else None
    for i in range(nt):
        d.set(11, 1, 10 + 2 * i, "stripped_spruce_log[axis=x]")
    if L >= 2:                                               # flag pole
        for y in range(2, 13):
            d.set(16, y, 8, LOG("stripped_spruce_log") if y < 3 else "spruce_fence")
        d.set(16, 1, 8, "cobblestone")
        for x, y in ((17, 12), (18, 12), (17, 11), (18, 11)):
            d.set(x, y, 8, "green_wool" if y == 12 else "white_wool")
        for x, z in ((15, 7), (17, 7), (15, 9), (17, 9)):
            d.set(x, 1, z, "cobblestone")
    if L >= 4:
        for x, z in ((8, 6), (24, 6), (8, 22), (24, 22)):
            d.set(x, 2, z, "spruce_fence")
            d.set(x, 3, z, LANT_S)
    if L >= 5:                                               # water well
        for x in range(23, 26):
            for z in range(8, 11):
                d.set(x, 2, z, rock(x, 2, z) if (x, z) != (24, 9) else "water[level=0]")
        for x, z in ((23, 8), (25, 8), (23, 10), (25, 10)):
            d.set(x, 3, z, "spruce_fence")
        d.fill(23, 4, 8, 25, 4, 10, SL("dark_oak"))
    # ---- blockhouses (child huts) -----------------------------------------------------------------
    for k in built:
        X0, Z0 = boxes[k]
        d.reserve(X0 + 1, 1, Z0 + 1, X0 + 7, 4, Z0 + 7)
        d.reserve(X0, 5, Z0, X0 + 8, CS_TSY, Z0 + 8)
        d.child_hut(X0 + CS_THUT[0], 2, Z0 + CS_THUT[2], TOWER)
    return d


def nt_bar(rel, L):
    d = Design("Neoterra", rel, (27, NT_TSY + 2, 33), gy=1, paving="smooth_stone")
    boxes = {"SW": (1, 25), "SE": (19, 25), "NW": (1, 1), "NE": (19, 1)}
    order = ["SW", "SE", "NW", "NE"]
    built = order[:min(L, 4)]
    full = L >= 3

    def in_box(x, z):
        for k in built:
            X0, Z0 = boxes[k]
            if 0 <= x - X0 < 7 and 0 <= z - Z0 < 7:
                return True
        return False
    # ground: parade ground with lane markings, lawn strips
    for x in range(2, 25):
        for z in range(2, 31):
            d.set(x, 1, z, "light_gray_concrete" if (x in (2, 24) or z in (2, 30)) else "smooth_stone")
    for z in range(2, 20):
        d.set(13, 1, z, "yellow_concrete" if z % 2 else "smooth_stone")
    # ---- perimeter fence --------------------------------------------------------------------------
    lines = [(1, z) for z in range(1, 32)] + [(25, z) for z in range(1, 32)] + \
            [(x, 1) for x in range(2, 25)] + [(x, 31) for x in range(2, 25)]
    for x, z in lines:
        if in_box(x, z) or (11 <= x <= 15 and z == 1):
            continue
        d.set(x, 2, z, "light_gray_concrete")
        post = (x + z) % 4 == 0 or (x in (1, 25) and z in (1, 31))
        if full:
            for y in (3, 4, 5):
                d.set(x, y, z, "white_concrete" if post else "iron_bars")
            if post:
                d.set(x, 6, z, ENDROD())
        else:
            d.set(x, 3, z, "white_concrete" if post else "light_gray_stained_glass_pane")
    # gate
    for x in (10, 16):
        for y in range(2, 7 if full else 4):
            d.set(x, y, 1, "gray_concrete" if y % 2 else "cyan_concrete")
        d.set(x, 7 if full else 4, 1, "sea_lantern")
    if full:
        for x in range(4, 10):                               # sliding steel gate, parked open behind the fence
            for y in (3, 4, 5):
                d.set(x, y, 2, "iron_bars")
            d.set(x, 2, 2, "polished_andesite")
        d.set(4, 2, 2, "gray_concrete")
        # guard booth
        for x in range(16, 19):
            for z in range(3, 6):
                edge = x in (16, 18) or z in (3, 5)
                for y in range(2, 5):
                    d.set(x, y, z, ("glass" if y > 2 else "white_concrete") if edge else AIR)
                d.set(x, 5, z, "smooth_quartz_slab[type=bottom,waterlogged=false]")
                d.set(x, 1, z, "polished_diorite")
        d.door(17, 2, 5, "north", "birch")
        d.set(17, 2, 3, "smooth_quartz_slab[type=top,waterlogged=false]")
        d.set(16, 2, 4, "birch_stairs[facing=east,half=bottom,shape=straight,waterlogged=false]") if False else None
        d.sign(11, 6, 0, "north", ["SECURITY", "COMPOUND", "AUTHORISED", "ONLY"], "birch", glow=True, color="cyan") \
            if False else None
    for x in range(11, 16):
        d.set(x, 1, 1, "yellow_concrete" if x % 2 else "black_concrete")
    # ---- HQ ---------------------------------------------------------------------------------------
    x1, z1, x2, z2 = 8, 20, 18, 30
    top = 11 if full else 6
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            edge = x in (x1, x2) or z in (z1, z2)
            d.set(x, 1, z, "polished_diorite")
            for y in range(2, top + 1):
                if y == 7:
                    d.set(x, y, z, "light_gray_concrete" if not edge else "cyan_terracotta")
                else:
                    d.set(x, y, z, ("light_gray_concrete" if x in (x1, x2) and z in (z1, z2) else "white_concrete")
                          if edge else AIR)
    d.flat(x1, z1, x2, z2, top + 1, "smooth_quartz", "white_concrete", "smooth_quartz_slab")
    for x in range(x1 + 1, x2):                               # glass street front
        d.window(x, 2, z1, x, 6, z1, "glass_pane")
        if full:
            d.window(x, 8, z1, x, 11, z1, "light_blue_stained_glass_pane")
    for z in range(z1 + 2, z2 - 1, 3):
        d.window(x1, 3, z, x1, 5, z, "light_gray_stained_glass_pane")
        d.window(x2, 3, z, x2, 5, z, "light_gray_stained_glass_pane")
        if full:
            d.window(x1, 9, z, x1, 10, z, "light_gray_stained_glass_pane")
            d.window(x2, 9, z, x2, 10, z, "light_gray_stained_glass_pane")
    d.double_door(13, 2, z1, "x", "south", "birch")
    for x in range(11, 17):                                   # entrance canopy
        for z in (z1 - 1, z1 - 2):
            d.set(x, 6, z, "smooth_quartz_slab[type=top,waterlogged=false]")
    d.sign(13, 7, z1 - 1, "north", ["GARRISON"], "birch", glow=True, color="cyan")
    d.sign(14, 7, z1 - 1, "north", ["HQ"], "birch", glow=True, color="cyan")
    # interior: armoury (back west), briefing (east), lobby
    d.hut(9, 2, 21)
    d.item(9, 2, 29, "barrel")
    d.item(10, 2, 29, "barrel")
    d.item(11, 2, 29, "anvil", "east")
    if L >= 3:
        d.item(12, 2, 29, "smithing_table")
    for z in range(25, 29):
        d.set(9, 2, z, "smooth_quartz_slab[type=top,waterlogged=false]")
        d.set(9, 3, z, ROD())
    for x in range(9, 14):                                    # glass partition of the armoury
        if x != 11:
            d.set(x, 2, 24, "light_gray_concrete")
            d.set(x, 3, 24, "light_gray_stained_glass_pane")
            d.set(x, 4, 24, "light_gray_stained_glass_pane")
    d.set(13, 2, 25, "light_gray_concrete")
    for z in range(25, 30):
        if z != 27:
            d.set(13, 2, z, "light_gray_concrete")
            d.set(13, 3, z, "light_gray_stained_glass_pane")
    # briefing table
    for z in (25, 26, 27):
        d.table(15, 2, z, "birch", "block", "smooth_quartz")
        d.chair(14, 2, z, "west", "birch", sit=False) if z != 27 else None
        d.chair(16, 2, z, "east", "birch", sit=False)
    for z in range(24, 29):
        d.set(17, 3, z, "black_stained_glass")
    d.set(17, 4, 26, "cyan_stained_glass")
    d.plant(17, 2, 21, "potted_bamboo")
    d.set(16, 2, 21, "smooth_quartz_slab[type=top,waterlogged=false]")
    for x in range(10, 18, 3):
        for z in (22, 27):
            d.set(x, 6, z, "sea_lantern")
    if full:                                                  # upper floor: ops room, stair along the east wall
        for i in range(5):
            d.set(17, 2 + i, 21 + i, "smooth_quartz_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]")
            for y in range(2 + i + 1, 2 + i + 4):
                if y <= 7:
                    d.set(17, y, 21 + i, AIR)
        d.set(16, 2, 21, AIR)
        d.set(17, 2, 21, "smooth_quartz_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]")
        d.set(17, 7, 26, AIR)
        for z in range(21, 27):
            d.set(16, 8, z, "light_gray_stained_glass_pane") if z < 26 else None
        for x in range(9, 16, 3):
            d.set(x, 8, 22, "smooth_quartz_slab[type=top,waterlogged=false]")
            d.chair(x, 8, 23, "south", "birch", sit=False)
            d.set(x, 9, 22, "black_stained_glass_pane")
        d.set(12, 8, 28, "smooth_quartz")
        d.set(12, 9, 28, "lectern[facing=north,has_book=false,powered=false]") if False else None
        for x in range(10, 17, 3):
            d.set(x, 11, 26, "sea_lantern")
        d.rug(9, 25, 15, 29, 8, ("light_gray_carpet", "cyan_carpet"))
    if L >= 4:                                                # solar panels on the roof
        for x in range(x1 + 2, x2 - 1):
            for z in (z1 + 2, z1 + 3):
                d.set(x, top + 2, z, "daylight_detector[inverted=false,power=0]")
    if L >= 5:                                                # helipad
        for x in range(x1 + 2, x2 - 1):
            for z in range(z1 + 5, z2 - 1):
                d.set(x, top + 1, z, "yellow_concrete" if (x == 11 or x == 15 or (z == 27 and 11 <= x <= 15))
                      else "gray_concrete")
        for x, z in ((x1 + 2, z1 + 5), (x2 - 2, z1 + 5), (x1 + 2, z2 - 2), (x2 - 2, z2 - 2)):
            d.set(x, top + 2, z, "redstone_lamp[lit=true]") if False else d.set(x, top + 2, z, ENDROD())
    # ---- shooting range (east) and parade ground ---------------------------------------------------
    nt = {1: 2, 2: 3, 3: 4, 4: 5, 5: 5}[L]
    for z in range(9, 19):
        for y in (2, 3, 4):
            d.set(24, y, z, "gray_concrete")
    for i in range(nt):
        z = 10 + 2 * i
        d.set(23, 2, z, "polished_andesite")
        d.yard_item(23, 3, z, "target")
    for z in range(9, 20, 2):                                 # firing booths
        d.set(17, 2, z, "white_concrete")
        d.set(17, 3, z, "light_gray_stained_glass_pane")
    for z in range(9, 19):
        d.set(20, 1, z, "yellow_concrete") if z % 2 else None
    for x in (4, 6):                                          # planters
        for z in range(10, 18):
            d.set(x, 1, z, "grass_block[snowy=false]")
            if z % 3 == 0:
                d.set(x, 2, z, "azalea")
    if L >= 2:                                                # three flag masts at the gate
        for i, x in enumerate((5, 7, 9)):
            for y in range(2, 10):
                d.set(x, y, 7, "iron_bars")
            d.set(x, 1, 7, "polished_andesite")
            d.set(x, 9, 6, ("cyan_wool", "white_wool", "light_blue_wool")[i])
            d.set(x, 8, 6, ("cyan_wool", "white_wool", "light_blue_wool")[i])
    for x, z in ((3, 19), (23, 19), (3, 3), (23, 3)):
        d.set(x, 2, z, "andesite_wall") if not in_box(x, z) else None
        d.set(x, 3, z, ENDROD()) if not in_box(x, z) else None
    # ---- dorm towers (child huts) -----------------------------------------------------------------
    for k in built:
        X0, Z0 = boxes[k]
        d.reserve(X0, 1, Z0, X0 + 6, NT_TSY, Z0 + 6)
        d.child_hut(X0 + NT_THUT[0], 2, Z0 + NT_THUT[2], TOWER)
    return d


@design("barracks")
def barracks(pack, rel, L):
    return {"Hearthwood": hw_bar, "Cascadia": cs_bar, "Neoterra": nt_bar}[pack](rel, L)


# ================================================================================================ GATEHOUSE
# Hearthwood: twin D-shaped stone towers, arched passage with timber gates and (L2+) a raised iron portcullis,
#             crenellated fighting gallery above the arch for the archers, bunk rooms in the towers.
# Cascadia:   timber gate between two log blockhouse towers, plank walkway (roofed from L2) over the gate.
# Neoterra:   security checkpoint: two concrete guard blocks, steel bar gate, glazed control bridge with a roof
#             terrace, bunk pods upstairs.
# Tags: gate = ground under the gate line, knight = ground just behind the gate, archer = wall-walk deck.
D7 = ["..###..",
      ".#...#.",
      "#.....#",
      "#.....#",
      "#.....#",
      "#.....#",
      "#.....#",
      "#.....#",
      "#.....#",
      "#######"]
D7_FOOT, D7_WALL, D7_IN = mask(D7)


def gate_tags(d, xs, z, kx, kz, ax, adeck, az):
    for x in xs:
        d.tag(x, d.gy, z, "gate")
    for x in kx:
        d.tag(x, d.gy, kz, "knight")
    for x in ax:
        d.tag(x, adeck, az, "archer")


def gh_hearthwood(rel, L):
    d = Design("Hearthwood", rel, (20, 18, 13), gy=1, paving="gravel")
    Z0 = 1
    for X0 in (1, 12):
        for (rx, rz) in D7_WALL:
            x, z = X0 + rx, Z0 + rz
            d.set(x, 1, z, "cobblestone")
            for y in range(2, 13):
                d.set(x, y, z, stone_mix(x, y, z))
            if (x + z) % 2 == 0:
                d.set(x, 13, z, stone_mix(x, 13, z))
        for (rx, rz) in D7_IN:
            x, z = X0 + rx, Z0 + rz
            d.set(x, 1, z, "spruce_planks")
            d.set(x, 7, z, "spruce_planks")
            d.set(x, 11, z, "stone_bricks")
        for (rx, rz) in D7_WALL:
            d.set(X0 + rx, 7, Z0 + rz, "polished_andesite")
        for y in (4, 9):                                      # arrow slits on the round front
            d.set(X0 + 3, y, Z0, "glass_pane")
            d.set(X0, y, Z0 + 4, "glass_pane") if X0 == 1 else d.set(X0 + 6, y, Z0 + 4, "glass_pane")
        d.set(X0 + 3, 9, Z0 + 9, "glass_pane")
    # gate block between the towers: passage x8..11, z3..9
    for x in range(8, 12):
        for z in range(3, 10):
            d.set(x, 1, z, "cobblestone" if (x + z) % 3 else "stone_bricks")
            for y in range(2, 7):
                d.set(x, y, z, AIR)
            d.set(x, 7, z, "stone_bricks")
        for z in (3, 9):
            d.set(x, 8, z, stone_mix(x, 8, z))
            if z == 3 and x % 2 == 0 or z == 9 and False:
                d.set(x, 9, z, stone_mix(x, 9, z))
        for z in range(4, 9):
            d.set(x, 8, z, AIR)
            d.set(x, 9, z, AIR)
    for z in (3, 9):                                          # pointed arch faces
        d.set(8, 6, z, ST("stone_brick", "west", "top"))
        d.set(11, 6, z, ST("stone_brick", "east", "top"))
        d.set(9, 7, z, "chiseled_stone_bricks") if z == 3 else None
    # gates on the gate line z=4
    for x in range(8, 12):
        for y in (2, 3, 4):
            d.set(x, y, 4, "dark_oak_fence_gate[facing=north,in_wall=false,open=false,powered=false]")
        if L >= 2:
            d.set(x, 6, 4, "iron_bars")
            d.set(x, 5, 4, "iron_bars")
        else:
            d.set(x, 6, 4, LOG("dark_oak_log", "x"))
    gate_tags(d, range(8, 12), 4, (8, 11), 6, (9, 10), 7, 4)
    # doors from the passage into the towers, ladders, gallery doorways
    d.door(7, 2, 7, "west", "dark_oak")
    d.door(12, 2, 7, "east", "dark_oak")
    for x in (7, 12):
        d.set(x, 8, 6, AIR)
        d.set(x, 9, 6, AIR)
    ladder(d, 2, 9, 2, 11, "east")
    ladder(d, 17, 9, 2, 11, "west")
    # guard rooms
    d.hut(3, 2, 3)
    d.item(2, 2, 6, "barrel")
    d.item(17, 2, 6, "barrel")
    weapon_rack(d, [(6, 4), (6, 5)], 2, "dark_oak")
    weapon_rack(d, [(13, 4), (13, 5)], 2, "dark_oak")
    d.set(15, 2, 3, "chest[facing=south,type=single,waterlogged=false]")
    d.dining(4, 2, 8, 1, "x", "dark_oak", ("e",), sit=False)
    d.dining(15, 2, 8, 1, "x", "dark_oak", ("w",), sit=False)
    for x in (4, 15):
        d.lamp(x, 6, 5)
    # bunk rooms
    for X0 in (1, 12):
        y = 8
        for x in (X0 + 1, X0 + 5):
            pass
        d.bed(X0 + 1, y, 4, "west", "red")
        d.bed(X0 + 1, y, 6, "west", "red")
        d.bed(X0 + 5, y, 4, "east", "red") if X0 == 12 else d.bed(X0 + 5, y, 3, "east", "red")
        d.bed(X0 + 5, y, 8, "east", "red") if X0 == 1 else d.bed(X0 + 5, y, 8, "east", "red")
        d.set(X0 + 1, y, 5, SL("dark_oak", "top"))
        d.candle(X0 + 1, y + 1, 5, 2)
        d.lamp(X0 + 3, 10, 5)
        d.rug(X0 + 3, 4, X0 + 3, 7, y, ("red_carpet",), "plain")
    # battlements: gallery front, flags
    for x in range(8, 12):
        d.set(x, 2, 2, AIR)
    for x in (7, 12):
        d.set(x, 5, 2, "wall_torch[facing=north]")
    if L >= 2:
        d.banner(7, 9, 2, "north", "red") if d.air(7, 9, 2) else None
        d.banner(12, 9, 2, "north", "red") if d.air(12, 9, 2) else None
    if L >= 3:                                                # machicolations over the gate, flags on the towers
        for x in range(8, 12):
            d.set(x, 7, 2, ST("stone_brick", "south", "top"))
            d.set(x, 8, 2, stone_mix(x, 8, 2))
            if x % 2 == 0:
                d.set(x, 9, 2, stone_mix(x, 9, 2))
            d.set(x, 9, 3, AIR) if x % 2 == 0 else None
        for X0 in (1, 12):
            for y in range(12, 17):
                d.set(X0 + 3, y, 6, "dark_oak_fence")
            d.set(X0 + 4, 16, 6, "red_wool")
            d.set(X0 + 4, 15, 6, "white_wool")
    for x in range(1, 19):                                    # approach path
        for z in (0, 11, 12):
            if 7 <= x <= 12:
                d.set(x, 1, z, "cobblestone" if (x + z) % 2 else "gravel")
    return d


def gh_cascadia(rel, L):
    d = Design("Cascadia", rel, (18, 18, 11), gy=1, paving="coarse_dirt")
    for X0 in (1, 11):
        x1, x2, z1, z2 = X0, X0 + 5, 2, 7
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                edge = x in (x1, x2) or z in (z1, z2)
                corner = x in (x1, x2) and z in (z1, z2)
                d.set(x, 1, z, rock(x, 1, z) if edge else "spruce_planks")
                for y in range(2, 11):
                    if not edge:
                        b = AIR
                    elif y <= 3:
                        b = rock(x, y, z)
                    elif corner:
                        b = LOG("spruce_log")
                    else:
                        b = LOG("stripped_spruce_log", "x" if z in (z1, z2) else "z")
                    d.set(x, y, z, b)
                if not edge:
                    d.set(x, 7, z, "spruce_planks")
                else:
                    d.set(x, 7, z, LOG("dark_oak_log", "x" if z in (z1, z2) else "z"))
        d.set(x1, 7, z1, LOG("spruce_log"))
        soft(d, d.hip, x1, z1, x2, z2, 11, "dark_oak_stairs", "dark_oak_slab", 1)
        d.fill(x1 + 1, 11, z1 + 1, x2 - 1, 11, z2 - 1, "spruce_planks")
        for y in (5, 9):
            d.set(X0 + 2, y, z1, "glass_pane")
            d.set(X0 + 3, y, z1, "glass_pane") if y == 9 else None
            d.set(x1 if X0 == 1 else x2, y, 5, "glass_pane")
    # passage x7..10 under the walkway, gate at z=3
    for x in range(7, 11):
        for z in range(1, 9):
            d.set(x, 1, z, "dirt_path")
        for y in (2, 3, 4) if L >= 2 else (2, 3):
            d.set(x, y, 3, "spruce_fence_gate[facing=north,in_wall=false,open=false,powered=false]")
        d.set(x, 6, 2, LOG("spruce_log", "x"))
        for z in range(2, 8):
            d.set(x, 7, z, "spruce_planks")
        d.set(x, 8, 2, LOG("spruce_log", "x") if x % 2 else "spruce_fence")
        d.set(x, 8, 7, "spruce_fence")
    for x in (7, 10):
        d.set(x, 5, 3, ST("spruce", "east" if x == 7 else "west", "top"))
    gate_tags(d, range(7, 11), 3, (7, 10), 5, (8, 9), 7, 3)
    # doors, ladders, walkway doorways
    d.door(6, 2, 5, "west", "spruce")
    d.door(11, 2, 5, "east", "spruce")
    for x in (6, 11):
        d.set(x, 8, 4, AIR)
        d.set(x, 9, 4, AIR)
    ladder(d, 5, 6, 2, 7, "north")
    ladder(d, 12, 6, 2, 7, "north")
    d.hut(2, 2, 3)
    d.item(2, 2, 6, "barrel")
    d.item(15, 2, 3, "barrel")
    d.set(15, 2, 6, "chest[facing=west,type=single,waterlogged=false]")
    weapon_rack(d, [(5, 3)], 2, "spruce")
    weapon_rack(d, [(12, 3)], 2, "spruce")
    d.set(3, 5, 4, LANT)
    d.set(14, 5, 4, LANT)
    # bunks (4 per tower)
    for bx in ((2, 3), (14, 15)):
        for x in bx:
            d.bed(x, 8, 3, "north", "brown")
            d.bed(x, 8, 6, "south", "brown")
        d.set(bx[0] + (2 if bx[0] == 2 else -1), 10, 5, LANT)
    # palisade stubs on both sides
    for x in (0, 17):
        for z in (4, 5):
            for y in range(2, 9):
                d.set(x, y, z, LOG("spruce_log"))
            d.set(x, 9, z, "spruce_fence")
    if L >= 2:                                                # roof over the walkway
        for x in range(7, 11):
            d.set(x, 11, 1, ST("dark_oak", "south"))
            d.set(x, 11, 8, ST("dark_oak", "north"))
            for z in range(2, 8):
                d.set(x, 12, z, SL("dark_oak"))
            d.set(x, 11, 2, "spruce_planks") if False else None
        for x in (7, 10):
            for z in (2, 7):
                for y in (9, 10, 11):
                    d.set(x, y, z, "spruce_fence")
        d.set(8, 11, 4, LANT)
        d.sign(8, 9, 1, "north", ["CAMP GATE"], "spruce") if False else None
    if L >= 3:
        d.set(9, 11, 5, "bell[attachment=ceiling,facing=north,powered=false]")
        for x in (6, 11):
            d.set(x, 5, 1, "wall_torch[facing=north]")
        d.banner(3, 6, 1, "north", "green")
        d.banner(14, 6, 1, "north", "green")
    return d


def gh_neoterra(rel, L):
    d = Design("Neoterra", rel, (22, 18, 11), gy=1, paving="smooth_stone")
    for X0 in (1, 14):
        x1, x2, z1, z2 = X0, X0 + 6, 2, 8
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                edge = x in (x1, x2) or z in (z1, z2)
                corner = x in (x1, x2) and z in (z1, z2)
                d.set(x, 1, z, "polished_diorite")
                for y in range(2, 11):
                    d.set(x, y, z, ("light_gray_concrete" if corner else "white_concrete") if edge else AIR)
                d.set(x, 6, z, "cyan_terracotta" if edge and not corner else "light_gray_concrete")
                d.set(x, 11, z, "smooth_quartz")
                if edge:
                    d.set(x, 12, z, "smooth_quartz_slab[type=bottom,waterlogged=false]")
        for x in range(x1 + 1, x2):                           # glazing
            d.window(x, 2, z1, x, 4, z1, "glass_pane")
            d.window(x, 8, z1, x, 9, z1, "light_gray_stained_glass_pane")
            d.window(x, 8, z2, x, 9, z2, "light_gray_stained_glass_pane")
        outer = x1 if X0 == 1 else x2
        for z in range(z1 + 2, z2 - 1):
            d.window(outer, 3, z, outer, 4, z, "light_gray_stained_glass_pane")
    # passage x8..13 with the steel gate on z=3
    for x in range(8, 14):
        for z in range(0, 11):
            d.set(x, 1, z, "gray_concrete" if 9 <= x <= 12 else "light_gray_concrete")
    for z in (0, 10):
        for x in range(9, 13):
            d.set(x, 1, z, "yellow_concrete" if x % 2 else "black_concrete")
    for x in (8, 13):
        d.set(x, 2, 3, "gray_concrete")
        d.set(x, 3, 3, "sea_lantern")
    for x in range(9, 13):
        for y in ((2, 3) if L == 1 else (2, 3, 4)):
            d.set(x, y, 3, "iron_bars")
    gate_tags(d, range(9, 13), 3, (8, 13), 5, (10, 11), 11, 4)
    # glazed control bridge (upper floor level) with roof terrace
    for x in range(8, 14):
        for z in range(2, 9):
            d.set(x, 6, z, "light_gray_concrete")
            for y in range(7, 11):
                d.set(x, y, z, "light_blue_stained_glass_pane" if z in (2, 8) else AIR)
            d.set(x, 11, z, "smooth_quartz")
        d.set(x, 12, 2, "light_gray_stained_glass_pane")
        d.set(x, 12, 8, "light_gray_stained_glass_pane")
        d.set(x, 5, 2, "smooth_quartz_slab[type=top,waterlogged=false]")
    d.sign(10, 6, 1, "north", ["CHECK", "POINT"], "birch", glow=True, color="cyan")
    d.sign(11, 6, 1, "north", ["GATE", "01"], "birch", glow=True, color="cyan")
    for x in (7, 14):
        d.set(x, 7, 5, AIR)
        d.set(x, 8, 5, AIR)
    for x in range(9, 13):
        d.set(x, 7, 3, "smooth_quartz_slab[type=top,waterlogged=false]")
        d.set(x, 8, 3, "black_stained_glass_pane") if x in (9, 12) else None
    d.chair(10, 7, 4, "south", "birch", sit=False)
    d.chair(11, 7, 4, "south", "birch", sit=False)
    ladder(d, 12, 7, 7, 11, "north")
    d.set(12, 7, 8, "white_concrete")
    for y in range(7, 12):
        d.set(12, y, 8, "white_concrete")
    d.set(9, 10, 6, "sea_lantern")
    # guard blocks: doors from the passage, ladders up, desks
    d.door(7, 2, 5, "west", "birch")
    d.door(14, 2, 5, "east", "birch")
    for X0, lx in ((1, 4), (14, 17)):
        ladder(d, lx, 7, 2, 6, "north")
    d.hut(2, 2, 3)
    d.item(2, 2, 7, "barrel")
    d.item(19, 2, 7, "barrel")
    for z in (3, 4):
        d.set(6, 2, z, "smooth_quartz_slab[type=top,waterlogged=false]")
        d.set(15, 2, z, "smooth_quartz_slab[type=top,waterlogged=false]")
    d.set(6, 3, 3, "black_stained_glass_pane")
    d.set(15, 3, 3, "black_stained_glass_pane")
    d.chair(5, 2, 4, "east", "birch", sit=False)
    d.chair(16, 2, 4, "west", "birch", sit=False)
    d.set(19, 2, 3, "light_gray_shulker_box[facing=up]")
    d.set(3, 5, 5, "sea_lantern")
    d.set(17, 5, 5, "sea_lantern")
    # bunk pods upstairs (4 per block)
    for X0 in (1, 14):
        y = 7
        d.bed(X0 + 1, y, 3, "west", "cyan")
        d.bed(X0 + 1, y, 7, "west", "cyan")
        d.bed(X0 + 5, y, 3, "east", "cyan")
        d.bed(X0 + 5, y, 7, "east", "cyan") if X0 == 1 else d.bed(X0 + 5, y, 7, "east", "cyan")
        d.set(X0 + 1, y, 5, "light_gray_shulker_box[facing=up]")
        d.set(X0 + 3, 10, 4, "sea_lantern")
    # roof terrace access from the bridge, rails, searchlights
    for X0 in (1, 14):
        for x in range(X0, X0 + 7):
            for z in (2, 8):
                pass
    if L >= 2:                                                # planters and bollards on the approach
        for x in (6, 15):
            d.set(x, 1, 0, "grass_block[snowy=false]")
            d.set(x, 2, 0, "azalea")
        for x in (8, 13):
            d.set(x, 2, 0, "polished_andesite")
    if L >= 3:
        for x, z in ((1, 2), (20, 2), (1, 8), (20, 8)):
            d.set(x, 13, z, ENDROD())
        d.set(8, 12, 5, "sea_lantern")
        d.set(13, 12, 5, "sea_lantern")
        for x in range(3, 7):
            d.set(x, 12, 5, "daylight_detector[inverted=false,power=0]")
            d.set(x + 13, 12, 5, "daylight_detector[inverted=false,power=0]")
    return d


@design("gatehouse")
def gatehouse(pack, rel, L):
    return {"Hearthwood": gh_hearthwood, "Cascadia": gh_cascadia, "Neoterra": gh_neoterra}[pack](rel, L)


# ================================================================================================ WALL GUARD TOWER
# Hearthwood: square stone tower astride a crenellated curtain-wall section; armoury below, bunks at wall-walk
#             level with doors onto the walks, battlements; L2 lookout storey, L3 machicolations, L4 flag,
#             L5 tiled spire roof.
# Cascadia:   log blockhouse on a palisade section with a plank firing walk; L2 roof lookout with bell,
#             L3 porch lean-to, L5 flag.
# Neoterra:   concrete watch post on a security wall: lobby/armoury, bunks at wall-walk level, glazed watch cab
#             (L2+) with antenna and searchlights.
RACKS = {1: 1, 2: 1, 3: 2, 4: 2, 5: 3}


def wt_hearthwood(rel, L):
    d = Design("Hearthwood", rel, (15, 26, 11), gy=1, paving="grass_block[snowy=false]")
    x1, x2, z1, z2 = 4, 10, 2, 8
    # curtain wall: z3 parapet, z4..6 deck at y7
    for x in range(0, 15):
        if x1 <= x <= x2:
            continue
        for z in range(3, 7):
            d.set(x, 1, z, "cobblestone")
            for y in range(2, 8):
                d.set(x, y, z, stone_mix(x, y, z))
        d.set(x, 8, 3, stone_mix(x, 8, 3))
        if x % 2 == 0:
            d.set(x, 9, 3, stone_mix(x, 9, 3))
        d.set(x, 8, 6, "dark_oak_fence") if x in (0, 1, 13, 14) else None
    top = 12 if L == 1 else 17
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            edge = x in (x1, x2) or z in (z1, z2)
            d.set(x, 1, z, "cobblestone" if edge else "spruce_planks")
            for y in range(2, top + 2):
                d.set(x, y, z, stone_mix(x, y, z) if edge else AIR)
            if edge and (x + z) % 2 == 0:
                d.set(x, top + 2, z, stone_mix(x, top + 2, z))
            for yy in (7, 12, 17):
                if yy <= top:
                    d.set(x, yy, z, ("polished_andesite" if edge else ("spruce_planks" if yy < top else "stone_bricks")))
    for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):     # quoins
        for y in range(2, top + 2, 2):
            d.set(x, y, z, "polished_andesite")
    d.door(7, 2, z2, "north", "dark_oak")
    d.set(7, 4, z2, "chiseled_stone_bricks")
    for x in (x1, x2):                                        # doors onto the wall walks
        d.door(x, 8, 5, "east" if x == x1 else "west", "dark_oak")
    for y in (4, 9):
        d.set(7, y, z1, "glass_pane")
        d.set(6, y + 1, z2, "glass_pane") if y == 9 else None
    if L >= 2:
        for x in (6, 8):
            d.window(x, 14, z1, x, 15, z1)
            d.window(x, 14, z2, x, 15, z2)
        d.window(x1, 14, 5, x1, 15, 5)
        d.window(x2, 14, 5, x2, 15, 5)
    ladder(d, 9, 3, 2, top, "south")
    # armoury
    d.hut(5, 2, 3)
    d.item(5, 2, 7, "barrel")
    nr = RACKS[L]
    for i in range(nr):
        d.rack(9, 2, 7 - i, "west")
    weapon_rack(d, [(5, 5), (5, 6)], 2, "dark_oak")
    d.set(7, 2, 5, "grindstone[face=floor,facing=north]")
    d.lamp(7, 6, 5)
    # bunks at wall-walk level
    for x in (5, 6):
        d.bed(x, 8, 3, "north", "red")
        d.bed(x, 8, 7, "south", "red")
    d.set(8, 8, 7, "chest[facing=north,type=single,waterlogged=false]")
    d.lamp(7, 11, 5)
    if L >= 2:                                                # lookout storey
        d.set(5, 13, 7, "chest[facing=north,type=single,waterlogged=false]")
        d.dining(6, 13, 5, 1, "x", "dark_oak", ("w", "e"), sit=False)
        d.set(5, 13, 3, "cartography_table")
        d.lamp(7, 16, 5)
        d.banner(5, 15, 7, "north", "red") if False else None
    if L >= 3:                                                # machicolations round the top
        for x in range(x1, x2 + 1):
            for z in (z1 - 1, z2 + 1):
                d.set(x, top, z, ST("stone_brick", "south" if z == z1 - 1 else "north", "top"))
                d.set(x, top + 1, z, stone_mix(x, top + 1, z))
                if x % 2 == 0:
                    d.set(x, top + 2, z, stone_mix(x, top + 2, z))
    if L >= 4:
        for y in range(top + 1, top + 6):
            d.set(7, y, 5, "dark_oak_fence")
        d.set(8, top + 5, 5, "red_wool")
        d.set(9, top + 5, 5, "red_wool")
        d.set(8, top + 4, 5, "white_wool")
    if L >= 5:
        d.banner(7, 10, z1 - 1, "north", "red") if d.air(7, 10, z1 - 1) else None
        for x in (2, 12):
            d.set(x, 8, 5, LANT_S)
        d.banner(7, 5, z2 + 1, "south", "red")
    return d


def wt_cascadia(rel, L):
    d = Design("Cascadia", rel, (13, 22, 13), gy=1, paving="coarse_dirt")
    # palisade z4 with a plank walk (deck y7) behind it
    for x in range(0, 13):
        if 2 <= x <= 10:
            continue
        for y in range(2, 9):
            d.set(x, y, 4, LOG("spruce_log"))
        d.set(x, 9, 4, "spruce_fence" if x % 2 else LOG("stripped_spruce_log"))
        d.set(x, 1, 4, rock(x, 1, 4))
        for z in (5, 6):
            d.set(x, 7, z, "spruce_planks")
        for y in range(2, 7):
            d.set(x, y, 6, "spruce_fence" if x in (0, 12) else AIR)
    # blockhouse: river-rock ground storey 7x7, overhanging log storey 9x9
    gx1, gz1, gx2, gz2 = 3, 3, 9, 9
    for x in range(gx1, gx2 + 1):
        for z in range(gz1, gz2 + 1):
            edge = x in (gx1, gx2) or z in (gz1, gz2)
            d.set(x, 1, z, rock(x, 1, z) if edge else "spruce_planks")
            for y in range(2, 7):
                d.set(x, y, z, rock(x, y, z) if edge and y < 4 else (LOG("spruce_log", "x" if z in (gz1, gz2) else "z")
                                                                     if edge else AIR))
    d.fill(2, 7, 2, 10, 7, 10, "spruce_planks")
    ux1, uz1, ux2, uz2 = 2, 2, 10, 10
    for x in range(ux1, ux2 + 1):
        for z in range(uz1, uz2 + 1):
            if x in (ux1, ux2) or z in (uz1, uz2):
                corner = x in (ux1, ux2) and z in (uz1, uz2)
                d.set(x, 7, z, LOG("dark_oak_log", "x" if z in (uz1, uz2) else "z"))
                for y in range(8, 11):
                    d.set(x, y, z, LOG("spruce_log") if corner else LOG("stripped_spruce_log", "x" if z in (uz1, uz2) else "z"))
                d.set(x, 11, z, LOG("dark_oak_log", "x" if z in (uz1, uz2) else "z"))
    d.fill(ux1 + 1, 11, uz1 + 1, ux2 - 1, 11, uz2 - 1, "spruce_planks")
    ridge = d.hip(ux1, uz1, ux2, uz2, 12, "dark_oak_stairs", "dark_oak_slab", 1)
    for x, z in ((6, 2), (6, 10), (4, 2), (8, 2)):
        d.set(x, 9, z, "glass_pane")
    for x in (ux1, ux2):
        d.set(x, 9, 7, "glass_pane")
    d.door(6, 2, gz2, "north", "spruce")
    for x in (ux1, ux2):                                      # doors onto the firing walk
        d.door(x, 8, 5, "east" if x == ux1 else "west", "spruce")
    for x in (gx1, gx2):
        d.set(x, 4, 6, "spruce_fence")
    # central post + ladder
    for y in range(2, 11):
        d.set(6, y, 5, LOG("stripped_spruce_log"))
    ladder(d, 6, 4, 2, 7, "north")
    d.hut(4, 2, 4)
    d.item(8, 2, 4, "barrel")
    for i in range(RACKS[L]):
        d.rack(4, 2, 6 + i if i < 2 else 8, "east") if i < 2 else d.rack(8, 2, 8, "west")
    d.set(8, 2, 7, "chest[facing=west,type=single,waterlogged=false]")
    d.set(5, 5, 7, LANT)
    for x in (3, 9):
        d.bed(x, 8, 3, "west" if x == 3 else "east", "brown")
        d.bed(x, 8, 7, "west" if x == 3 else "east", "brown")
    d.set(3, 8, 9, "chest[facing=north,type=single,waterlogged=false]")
    d.set(5, 10, 7, LANT)
    if L >= 2:                                                # roof lookout with alarm bell
        for x, z in ((5, 5), (7, 5), (5, 7), (7, 7)):
            for y in range(ridge, ridge + 3):
                d.set(x, y, z, "spruce_fence")
        d.fill(5, ridge + 3, 5, 7, ridge + 3, 7, SL("dark_oak"))
        d.set(6, ridge + 2, 6, "bell[attachment=ceiling,facing=north,powered=false]")
        d.fill(5, ridge - 1, 5, 7, ridge - 1, 7, "spruce_planks")
        for x in range(5, 8):
            for z in range(5, 8):
                d.set(x, ridge, z, AIR) if (x, z) != (5, 5) and (x, z) != (7, 5) and (x, z) != (5, 7) and (x, z) != (7, 7) else None
    if L >= 3:                                                # lean-to porch over the door
        for x in range(4, 9):
            d.set(x, 5, 11, ST("spruce", "south"))
            d.set(x, 5, 10, SL("spruce"))
        for x in (4, 8):
            for y in (2, 3, 4):
                d.set(x, y, 11, LOG("spruce_log"))
        d.keg(9, 2, 11, "north") if False else None
        d.set(5, 2, 11, "spruce_log[axis=x]")
        d.set(5, 3, 11, AIR)
    if L >= 4:
        for x in (0, 12):
            d.set(x, 8, 5, LANT_S)
    if L >= 5:
        for y in range(8, 13):
            d.set(0, y, 6, "spruce_fence")
        d.set(0, 12, 7, "green_wool")
        d.set(0, 11, 7, "white_wool")
        for x in range(9, 12):
            d.set(x, 2, 11, LOG("spruce_log", "x"))
    return d


def wt_neoterra(rel, L):
    d = Design("Neoterra", rel, (11, 26, 13), gy=1, paving="smooth_stone")
    # security wall z4..6, walk deck at y8, glass parapet on the outside
    for x in range(0, 11):
        if 2 <= x <= 8:
            continue
        for z in range(4, 7):
            d.set(x, 1, z, "polished_andesite")
            for y in range(2, 9):
                d.set(x, y, z, "white_concrete" if z == 4 else "light_gray_concrete")
        d.set(x, 5, 4, "cyan_terracotta")
        d.set(x, 9, 4, "light_gray_stained_glass_pane")
        d.set(x, 9, 6, "iron_bars")
    x1, z1, x2, z2 = 2, 2, 8, 8
    top = 13
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            edge = x in (x1, x2) or z in (z1, z2)
            corner = x in (x1, x2) and z in (z1, z2)
            d.set(x, 1, z, "polished_diorite")
            for y in range(2, top):
                d.set(x, y, z, ("light_gray_concrete" if corner else "white_concrete") if edge else AIR)
            d.set(x, 8, z, "cyan_terracotta" if edge and not corner else "light_gray_concrete")
            d.set(x, top, z, "smooth_quartz")
    for a in (4, 5, 6):                                        # glazing
        for y in (3, 4, 5, 6):
            d.set(a, y, z1, "glass_pane")
        for y in (10, 11):
            d.set(a, y, z1, "light_gray_stained_glass_pane")
            d.set(a, y, z2, "light_gray_stained_glass_pane")
    d.door(5, 2, z2, "north", "birch")
    d.window(4, 2, z2, 4, 6, z2, "glass_pane")
    d.window(6, 2, z2, 6, 6, z2, "glass_pane")
    d.set(5, 4, z2, "glass")
    for x in (x1, x2):
        d.door(x, 9, 5, "east" if x == x1 else "west", "birch")
    # core + ladder
    for y in range(2, top):
        d.set(5, y, 5, "light_gray_concrete")
    yl = top if L == 1 else 18
    ladder(d, 5, 4, 2, yl, "north")
    d.hut(3, 2, 3)
    d.item(7, 2, 3, "barrel")
    for i in range(RACKS[L]):
        d.rack(3, 2, 5 + i, "east")
    d.set(7, 2, 7, "light_gray_shulker_box[facing=up]")
    d.set(7, 2, 6, "smooth_quartz_slab[type=top,waterlogged=false]")
    d.set(7, 3, 6, "black_stained_glass_pane")
    for y in (7,):
        d.set(4, y, 6, "sea_lantern")
    for x in (3, 7):
        d.bed(x, 9, 3, "west" if x == 3 else "east", "cyan")
        d.bed(x, 9, 7, "west" if x == 3 else "east", "cyan")
    d.set(6, 12, 6, "sea_lantern")
    if L == 1:
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                if x in (x1, x2) or z in (z1, z2):
                    d.set(x, top + 1, z, "light_gray_stained_glass_pane")
        d.set(7, top + 1, 7, "sea_lantern")
    else:                                                     # glazed watch cab cantilevered over the wall
        c1, c2 = 1, 9
        for x in range(c1, c2 + 1):
            for z in range(c1, c2 + 1):
                edge = x in (c1, c2) or z in (c1, c2)
                d.set(x, top, z, "smooth_quartz")
                for y in range(top + 1, top + 4):
                    d.set(x, y, z, ("light_gray_concrete" if x in (c1, c2) and z in (c1, c2) else
                                    ("white_concrete" if y == top + 1 else "light_blue_stained_glass_pane"))
                          if edge else AIR)
                d.set(x, top + 4, z, "white_concrete" if edge else "smooth_quartz")
                d.set(x, top + 5, z, "smooth_quartz_slab[type=bottom,waterlogged=false]") if edge else None
        for x in range(c1 + 1, c2):
            d.set(x, top - 1, c1, "smooth_quartz_slab[type=top,waterlogged=false]") if not x1 <= x <= x2 else None
        for z in range(c1, c2 + 1):
            for x in (c1, c2):
                if not z1 <= z <= z2:
                    pass
        d.set(5, top + 4, 4, AIR)
        d.set(5, top + 5, 4, AIR)
        ladder(d, 5, 4, top + 1, top + 5, "north")
        for y in range(top + 1, top + 5):
            d.set(5, y, 5, "light_gray_concrete")
        d.set(3, top + 1, 3, "smooth_quartz_slab[type=top,waterlogged=false]")
        d.set(4, top + 1, 3, "smooth_quartz_slab[type=top,waterlogged=false]")
        d.set(3, top + 2, 3, "black_stained_glass_pane")
        d.chair(3, top + 1, 4, "south", "birch", sit=False)
        d.set(7, top + 3, 7, "sea_lantern")
        # roof: rail, searchlight, antenna
        for x in range(c1, c2 + 1):
            for z in (c1, c2):
                d.set(x, top + 5, z, "light_gray_stained_glass_pane")
        for z in range(c1, c2 + 1):
            for x in (c1, c2):
                d.set(x, top + 5, z, "light_gray_stained_glass_pane")
        if L >= 3:
            d.set(7, top + 5, 3, "sea_lantern")
            d.set(7, top + 6, 3, "daylight_detector[inverted=false,power=0]")
        if L >= 4:
            for y in range(top + 5, top + 9):
                d.set(3, y, 7, "iron_bars" if y < top + 8 else ROD())
        if L >= 5:
            for x, z in ((c1, c1), (c2, c1), (c1, c2), (c2, c2)):
                d.set(x, top + 6, z, ENDROD())
    return d


@design("wallguardtower")
def wallguardtower(pack, rel, L):
    return {"Hearthwood": wt_hearthwood, "Cascadia": wt_cascadia, "Neoterra": wt_neoterra}[pack](rel, L)
