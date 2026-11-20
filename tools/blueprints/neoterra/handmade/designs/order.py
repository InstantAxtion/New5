"""
Military & mystic orders: guardtower, archery, combatacademy, enchanter, alchemist, graveyard, mysticalsite.

Guard tower
  Hearthwood  Village watch tower: square stone-brick ground storey, timber-framed bunk room above, steep hipped
              tile roof; L2 adds an open lookout storey with an alarm bell, L3 an armoury wing, L4 a fenced drill
              yard with dummies, L5 a jettied lookout gallery with banners.
  Cascadia    Fire lookout: log bunk cabin with porch and stone chimney beside a timber trestle tower with a glazed
              cab and catwalk on top; the tower grows taller every level, L3 woodshed, L5 flag and water tank.
  Neoterra    Security tower: glazed guard lobby with crew room and a slim concrete shaft carrying a cantilevered
              glass observation pod with antenna; the shaft grows each level, L3 roof terrace, L4 armoury wing.
Archery, combat academy, enchanter, alchemist, graveyard, mystical site: see the section headers below.
"""
from hm import Design, design, AIR, D4, OPP, CW

ST = lambda m, f, h="bottom", s="straight": f"{m}_stairs[facing={f},half={h},shape={s},waterlogged=false]"
SL = lambda m, t="bottom": f"{m}_slab[type={t},waterlogged=false]"
TD = lambda m, f, h="top", o="false": f"{m}_trapdoor[facing={f},half={h},open={o},powered=false,waterlogged=false]"
LOG = lambda m, a="y": f"{m}[axis={a}]"
LANT = "lantern[hanging=true,waterlogged=false]"
LANT_S = "lantern[hanging=false,waterlogged=false]"
SLANT = "soul_lantern[hanging=true,waterlogged=false]"
ROD = lambda f="up": f"lightning_rod[facing={f},powered=false,waterlogged=false]"
ENDROD = lambda f="up": f"end_rod[facing={f}]"


def soft(d, fn, *a, **k):
    """Run a drawing helper so that it only writes into air cells (roofs meeting existing walls)."""
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
    """Ladder column (facing away from the supporting wall) from y1 to y2 inclusive (y2 = the deck hole)."""
    for y in range(y1, y2 + 1):
        d.set(x, y, z, f"ladder[facing={facing},waterlogged=false]")


def flight(d, x, y, z, dirn, n, mat, under=None):
    """Straight stair flight rising toward `dirn`; first step at (x,y,z). Clears 3 cells of headroom above
    each step (cuts the hole in the deck above). Returns the cell after the top step."""
    dx, dz = D4[dirn]
    for i in range(n):
        cx, cz = x + dx * i, z + dz * i
        d.set(cx, y + i, cz, ST(mat, dirn))
        if under:
            for yy in range(y, y + i):
                d.set(cx, yy, cz, under)
        for k in range(1, 4):
            if d.bp.inside(cx, y + i + k, cz):
                d.set(cx, y + i + k, cz, AIR)
    return x + dx * n, z + dz * n


def dummy(d, x, y, z, facing="north", head="carved_pumpkin"):
    """Training dummy: fence post, hay-bale body, pumpkin head."""
    d.set(x, y, z, "oak_fence")
    d.set(x, y + 1, z, "hay_block[axis=y]")
    d.set(x, y + 2, z, f"{head}[facing={facing}]")


def weapon_rack(d, x1, z1, x2, z2, y, wood, facing):
    """Wall rack: shelf slab with spears (lightning rods) and shields (banners) above."""
    for x in range(min(x1, x2), max(x1, x2) + 1):
        for z in range(min(z1, z2), max(z1, z2) + 1):
            d.set(x, y, z, SL(wood, "top"))
            d.set(x, y + 1, z, ROD())


def hw_frame(d, x1, z1, x2, z2, y1, y2, step=2, beam="stripped_dark_oak_log", infill="calcite"):
    """Timber-framed storey walls (calcite infill, dark-oak studs every `step`, top beam)."""
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if not (x in (x1, x2) or z in (z1, z2)):
                continue
            for y in range(y1, y2 + 1):
                stud = (x in (x1, x2) and (z - z1) % step == 0) or (z in (z1, z2) and (x - x1) % step == 0) \
                    or (x in (x1, x2) and z in (z1, z2))
                if y == y2:
                    d.set(x, y, z, LOG(beam, "x" if z in (z1, z2) else "z"))
                else:
                    d.set(x, y, z, LOG(beam) if stud else infill)


def cs_walls(d, x1, z1, x2, z2, y1, y2, log="spruce_log", corner="stripped_spruce_log", footing=True):
    """Log-cabin walls: horizontal logs, stripped corner posts, river-rock footing on the ground row."""
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if not (x in (x1, x2) or z in (z1, z2)):
                continue
            corner_ = x in (x1, x2) and z in (z1, z2)
            for y in range(y1, y2 + 1):
                d.set(x, y, z, LOG(corner) if corner_ else LOG(log, "x" if z in (z1, z2) else "z"))
            if footing:
                d.set(x, y1 - 1, z, "mossy_cobblestone" if (x * 7 + z * 3) % 4 == 0 else "cobblestone")


def nt_walls(d, x1, z1, x2, z2, y1, y2, wall="white_concrete", corner="light_gray_concrete"):
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if not (x in (x1, x2) or z in (z1, z2)):
                continue
            c = x in (x1, x2) and z in (z1, z2)
            for y in range(y1, y2 + 1):
                d.set(x, y, z, corner if c else wall)


def interior(d, x1, z1, x2, z2, y1, y2):
    d.clear(x1 + 1, y1, z1 + 1, x2 - 1, y2, z2 - 1)


def hipcap(d, x1, z1, x2, z2, y, stairs, cap, ceiling, overhang=1):
    """Hip roof with a flat ceiling under it (fills the inner area at y so the attic is closed)."""
    d.fill(x1 + 1, y, z1 + 1, x2 - 1, y, z2 - 1, ceiling)
    return soft(d, d.hip, x1, z1, x2, z2, y, stairs, cap, overhang)


# ================================================================================================ GUARD TOWER
def gt_hearthwood(rel, L):
    d = Design("Hearthwood", rel, (21, 26, 22))
    x1, z1, x2, z2 = 3, 4, 9, 10
    # ground storey: rubble-faced stone brick
    d.box(x1, 2, z1, x2, 5, z2, "stone_bricks", floor="spruce_planks")
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if (x in (x1, x2) or z in (z1, z2)) and (x * 5 + z * 3) % 7 == 0:
                d.set(x, 3 + (x + z) % 3, z, "mossy_stone_bricks")
            if (x in (x1, x2) or z in (z1, z2)):
                d.set(x, 1, z, "cobblestone")
    d.fill(x1, 6, z1, x2, 6, z2, "dark_oak_planks")
    hw_frame(d, x1, z1, x2, z2, 7, 10)
    top = 11
    # arrow slits below, leaded windows above
    for z in (6, 8):
        d.window(x1, 3, z, x1, 4, z)
    d.window(x2, 3, 6, x2, 4, 6)
    for x in (5, 7):
        d.window(x, 3, z2, x, 4, z2)
    for x in (5, 7):
        d.window(x, 8, z1, x, 9, z1)
        d.window(x, 8, z2, x, 9, z2)
    d.window(x1, 8, 7, x1, 9, 7)
    d.door(6, 2, z1, "south", "dark_oak")
    d.set(6, 4, z1, "chiseled_stone_bricks")
    d.set(5, 4, z1 - 1, "wall_torch[facing=north]")
    d.set(7, 4, z1 - 1, "wall_torch[facing=north]")
    # ladder in the south-east corner, all floors
    lx, lz = x2 - 1, z2 - 1
    # ---- guard room
    d.hut(x1 + 1, 2, z1 + 1)
    d.item(x2 - 1, 2, z1 + 1, "barrel")
    d.set(x2 - 1, 3, z1 + 1, "decorated_pot[cracked=false,facing=west,waterlogged=false]")
    weapon_rack(d, x2 - 1, z1 + 2, x2 - 1, z1 + 3, 2, "dark_oak", "west")
    d.banner(x2 - 1, 4, z1 + 3, "west", "red")
    d.dining(5, 2, 7, 2, "z", "dark_oak", ("w",), sit=False)
    d.chair(6, 2, 7, "east", "dark_oak", sit=False)
    d.lamp(6, 5, 7)
    d.set(x1 + 1, 2, z2 - 1, "smithing_table")
    d.banner(x1 + 1, 4, z2 - 1, "east", "red")
    # ---- bunk room
    d.bed(x1 + 1, 7, z1 + 1, "west")
    d.bed(x1 + 1, 7, z1 + 4, "west")
    d.set(x1 + 1, 7, z1 + 2, SL("dark_oak", "top"))
    d.candle(x1 + 1, 8, z1 + 2, 2)
    d.set(x1 + 1, 7, z1 + 3, "chest[facing=east,type=single,waterlogged=false]")
    d.set(x2 - 1, 7, z1 + 1, "chiseled_bookshelf[facing=west,slot_0_occupied=true,slot_1_occupied=false,"
                             "slot_2_occupied=true,slot_3_occupied=false,slot_4_occupied=false,slot_5_occupied=true]")
    d.rug(x1 + 3, z1 + 2, x1 + 4, z1 + 4, 7, ("red_carpet",), "plain")
    d.lamp(6, 10, 6)
    if L == 1:
        ladder(d, lx, lz, 2, 6, "west")
        hipcap(d, x1, z1, x2, z2, top, "deepslate_tile_stairs", "deepslate_tile_slab", "dark_oak_planks")
    else:
        # open lookout storey with corner posts, rail and alarm bell
        ladder(d, lx, lz, 2, 11, "west")
        d.set(x2, 7, lz, "stripped_dark_oak_log[axis=y]")
        d.fill(x1, 11, z1, x2, 11, z2, "dark_oak_planks")
        d.set(lx, 11, lz, "ladder[facing=west,waterlogged=false]")
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                if x in (x1, x2) or z in (z1, z2):
                    post = (x in (x1, x2, 6)) and (z in (z1, z2, 7))
                    d.set(x, 12, z, LOG("stripped_dark_oak_log") if post else "dark_oak_fence")
                    d.set(x, 13, z, LOG("stripped_dark_oak_log") if post else AIR)
                    d.set(x, 14, z, LOG("stripped_dark_oak_log", "x" if z in (z1, z2) else "z"))
        d.set(x2, 12, lz, "stripped_dark_oak_log[axis=y]")
        hipcap(d, x1, z1, x2, z2, 15, "deepslate_tile_stairs", "deepslate_tile_slab", "dark_oak_planks")
        d.set(6, 14, 7, "bell[attachment=ceiling,facing=north,powered=false]")
        d.chair(x1 + 1, 12, z1 + 1, "west", "dark_oak", sit=False)
    if L >= 3:
        # armoury wing to the east
        ax2 = 16
        d.box(x2, 2, 5, ax2, 5, 9, "bricks", floor="spruce_planks")
        for x in range(x2, ax2 + 1):
            d.set(x, 1, 5, "stone_bricks")
            d.set(x, 1, 9, "stone_bricks")
            d.set(x, 2, 5, "stone_bricks")
            d.set(x, 2, 9, "stone_bricks")
        d.fill(ax2, 1, 5, ax2, 2, 9, "stone_bricks")
        d.set(x2, 2, 7, AIR)
        d.set(x2, 3, 7, AIR)
        d.door(13, 2, 5, "south", "dark_oak")
        d.window(11, 3, 5, 11, 4, 5)
        d.window(15, 3, 5, 15, 4, 5)
        d.window(ax2, 3, 7, ax2, 4, 7)
        d.window(12, 3, 9, 14, 4, 9)
        soft(d, d.gable, x2, 5, ax2, 9, 6, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "bricks", 1)
        weapon_rack(d, 10, 8, 15, 8, 2, "dark_oak", "north")
        for x in (11, 14):
            d.banner(x, 4, 8, "north", "red" if x == 11 else "white")
        d.set(15, 2, 6, "grindstone[face=floor,facing=west]")
        d.set(10, 2, 6, "chest[facing=east,type=single,waterlogged=false]")
        d.lamp(12, 5, 7)
    if L >= 4:
        # fenced drill yard behind
        yx1, yz1, yx2, yz2 = 3, 12, 17, 19
        d.fill(yx1, 1, yz1, yx2, 1, yz2, "coarse_dirt")
        for x in range(yx1, yx2 + 1):
            for z in range(yz1, yz2 + 1):
                if x in (yx1, yx2) or z in (yz1, yz2):
                    d.set(x, 2, z, "dark_oak_fence")
        d.set(10, 2, yz1, "dark_oak_fence_gate[facing=north,in_wall=false,open=false,powered=false]")
        d.fill(10, 1, z2 + 1, 10, 1, yz1, "gravel")
        d.door(6, 2, z2, "north", "dark_oak")
        d.fill(6, 1, z2 + 1, 6, 1, yz1 - 1, "gravel")
        d.set(6, 2, yz1, "dark_oak_fence_gate[facing=north,in_wall=false,open=false,powered=false]")
        for x in (6, 9, 12):
            dummy(d, x, 2, 17, "north")
        d.set(15, 2, 18, "hay_block[axis=x]")
        d.set(15, 3, 18, "target[power=0]")
        d.set(16, 2, 13, "water_cauldron[level=3]")
        for x, z in ((yx1, yz1), (yx2, yz1), (yx1, yz2), (yx2, yz2)):
            d.set(x, 3, z, LANT_S)
    if L >= 5:
        # jettied lookout gallery round the lookout storey
        for x in range(x1 - 1, x2 + 2):
            for z in range(z1 - 1, z2 + 2):
                if x in (x1 - 1, x2 + 1) or z in (z1 - 1, z2 + 1):
                    d.set(x, 11, z, "dark_oak_planks")
                    d.set(x, 12, z, "dark_oak_fence")
                    if (x + z) % 2 == 0 and z in (z1 - 1,):
                        d.set(x, 10, z, ST("dark_oak", "north", "top"))
        for z in (z1, z2):
            d.set(6, 12, z, AIR)
        d.banner(6, 9, z1 - 1, "north", "red")
        d.banner(x1 - 1, 9, 7, "west", "red")
        d.banner(x2 + 1, 9, 7, "east", "red") if d.air(x2 + 1, 9, 7) else None
    return d


def gt_cascadia(rel, L):
    d = Design("Cascadia", rel, (23, 32, 20), paving="coarse_dirt")
    # bunk cabin
    x1, z1, x2, z2 = 2, 6, 10, 12
    cs_walls(d, x1, z1, x2, z2, 2, 5)
    d.fill(x1 + 1, 1, z1 + 1, x2 - 1, 1, z2 - 1, "spruce_planks")
    d.door(6, 2, z1, "south", "spruce")
    d.window(4, 3, z1, 4, 4, z1)
    d.window(8, 3, z1, 8, 4, z1)
    d.window(x2, 3, 9, x2, 4, 9)
    d.window(6, 3, z2, 6, 4, z2)
    ridge = soft(d, d.gable, x1, z1, x2, z2, 6, "x", "dark_oak_stairs", "dark_oak_slab", "stripped_spruce_log", 1)
    d.fill(x1 + 1, 6, z1 + 1, x2 - 1, 6, z2 - 1, "spruce_planks")
    # stone chimney on the west gable
    d.hearth(x1 + 1, 2, 9, "east", 6, "cobblestone", "campfire")
    for y in range(1, ridge + 2):
        d.set(x1, y, 9, "mossy_cobblestone" if y % 3 == 0 else "cobblestone")
    d.set(x1 - 1, 1, 9, "cobblestone")
    # porch
    for x in range(x1, x2 + 1):
        for z in range(z1 - 3, z1):
            d.set(x, 1, z, "spruce_planks")
        d.set(x, 5, z1 - 3, ST("spruce", "south"))
        for z in range(z1 - 2, z1):
            d.set(x, 5, z, SL("spruce", "top"))
    for x in (x1, x2):
        for y in range(2, 5):
            d.set(x, y, z1 - 3, LOG("spruce_log"))
    for x in range(x1 + 1, x2):
        if x not in (5, 6, 7):
            d.set(x, 2, z1 - 3, "spruce_fence")
    d.chair(x1 + 1, 2, z1 - 1, "south", "spruce", sit=False)
    d.keg(x2 - 1, 2, z1 - 1, "north")
    d.lamp(6, 4, z1 - 2)
    # inside
    d.hut(x1 + 2, 2, z1 + 1)
    d.item(x2 - 1, 2, z1 + 1, "barrel")
    d.bed(x1 + 2, 2, z2 - 1, "south")
    d.bed(x2 - 1, 2, z2 - 1, "south")
    d.set(x2 - 2, 2, z2 - 1, SL("spruce", "top"))
    d.set(x2 - 2, 3, z2 - 1, LANT_S)
    d.table(6, 2, 9, "spruce")
    d.chair(6, 2, 8, "north", "spruce", sit=False)
    d.chair(7, 2, 9, "east", "spruce", sit=False)
    d.rug(4, 8, 8, 10, 2, ("brown_carpet", "green_carpet"))
    weapon_rack(d, x2 - 1, 8, x2 - 1, 8, 2, "spruce", "west")
    d.lamp(6, 5, 9)
    # trestle lookout tower
    tx1, tz1, tx2, tz2 = 14, 7, 18, 11
    yc = {1: 9, 2: 12, 3: 15, 4: 18, 5: 21}[L]
    for x, z in ((tx1, tz1), (tx2, tz1), (tx1, tz2), (tx2, tz2)):
        d.set(x, 1, z, "cobblestone")
        for y in range(2, yc):
            d.set(x, y, z, LOG("spruce_log"))
    for y in range(4, yc, 3):                                     # girts and sway bracing
        for x in range(tx1 + 1, tx2):
            for z in (tz1, tz2):
                d.set(x, y, z, LOG("stripped_spruce_log", "x"))
        for z in range(tz1 + 1, tz2):
            for x in (tx1, tx2):
                d.set(x, y, z, LOG("stripped_spruce_log", "z"))
        for k in range(1, 4):
            if y + k < yc - 1:
                for x, z in ((tx1 + k, tz1), (tx2 - k, tz2), (tx1, tz1 + k), (tx2, tz2 - k)):
                    d.set(x, y + k, z, "spruce_fence")
    mx = (tx1 + tx2) // 2
    for y in range(2, yc):
        d.set(mx, y, tz1 + 3, LOG("spruce_log"))
    d.set(mx, 1, tz1 + 3, "cobblestone")
    ladder(d, mx, tz1 + 2, 2, yc, "north")
    # cab + catwalk
    d.fill(tx1 - 1, yc, tz1 - 1, tx2 + 1, yc, tz2 + 1, "spruce_planks")
    for x in range(tx1 - 1, tx2 + 2):
        for z in range(tz1 - 1, tz2 + 2):
            if x in (tx1 - 1, tx2 + 1) or z in (tz1 - 1, tz2 + 1):
                d.set(x, yc + 1, z, "spruce_fence")
                if (x + z) % 2 == 0:
                    d.set(x, yc - 1, z, ST("spruce", OPP["north" if z == tz1 - 1 else "south" if z == tz2 + 1 else "west" if x == tx1 - 1 else "east"], "top"))
    d.set(mx, yc, tz1 + 2, "ladder[facing=north,waterlogged=false]")
    cx1, cz1, cx2, cz2 = tx1, tz1, tx2, tz2
    cs_walls(d, cx1, cz1, cx2, cz2, yc + 1, yc + 3, footing=False)
    for x in range(cx1 + 1, cx2):
        d.window(x, yc + 2, cz1, x, yc + 3, cz1)
        d.window(x, yc + 2, cz2, x, yc + 3, cz2)
    for z in range(cz1 + 1, cz2):
        d.window(cx1, yc + 2, z, cx1, yc + 3, z)
        d.window(cx2, yc + 2, z, cx2, yc + 3, z)
    d.door(cx1 + 1, yc + 1, cz1, "south", "spruce")
    hipcap(d, cx1, cz1, cx2, cz2, yc + 4, "dark_oak_stairs", "dark_oak_slab", "spruce_planks")
    d.set(mx + 1, yc + 1, tz1 + 2, "cartography_table")             # fire finder
    d.set(mx, yc + 1, tz1 + 3, "spruce_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]")
    d.lamp(mx, yc + 3, tz1 + 2)
    d.set(tx2 + 1, yc + 2, tz1 - 1, "bell[attachment=floor,facing=north,powered=false]") if False else None
    if L >= 3:
        # woodshed lean-to behind the cabin with a woodpile
        for x in range(x1 + 1, x2):
            d.set(x, 1, z2 + 1, "spruce_planks")
            d.set(x, 1, z2 + 2, "spruce_planks")
            d.set(x, 4, z2 + 3, ST("spruce", "north"))
            for z in (z2 + 1, z2 + 2):
                d.set(x, 5, z, SL("spruce"))
            if x % 2:
                d.set(x, 2, z2 + 1, LOG("spruce_log", "x"))
                d.set(x, 3, z2 + 1, LOG("oak_log", "x"))
            else:
                d.set(x, 2, z2 + 1, LOG("birch_log", "x"))
        for x in (x1 + 1, x2 - 1):
            for y in range(2, 4):
                d.set(x, y, z2 + 3, LOG("spruce_log"))
        d.set(x2 - 2, 2, z2 + 2, "chipped_anvil[facing=east]") if False else None
    if L >= 4:
        # rain-water tank on stilts and a split-rail fence round the site
        for x, z in ((13, 15), (15, 15), (13, 17), (15, 17)):
            for y in range(2, 5):
                d.set(x, y, z, "spruce_fence")
        d.fill(13, 5, 15, 15, 5, 17, "spruce_planks")
        for x in range(13, 16):
            for z in range(15, 18):
                if (x, z) != (14, 16):
                    d.set(x, 6, z, LOG("stripped_spruce_log", "x" if z != 16 else "z"))
        d.set(14, 6, 16, "water_cauldron[level=3]")
        for x in range(0, 23):
            if x not in (5, 6, 7):
                d.set(x, 2, 1, "spruce_fence" if x % 4 else "spruce_log[axis=y]")
    if L >= 5:
        for y in range(yc + 5, yc + 9):
            d.set(mx, y, tz1 + 2, "spruce_fence")
        d.set(mx, yc + 8, tz1 + 1, "red_wall_banner[facing=north]")
        d.set(tx2 + 1, yc + 1, tz1 + 2, "bell[attachment=floor,facing=east,powered=false]")
    return d


def gt_neoterra(rel, L):
    d = Design("Neoterra", rel, (21, 34, 18), paving="smooth_stone")
    x1, z1, x2, z2 = 2, 3, 13, 9
    nt_walls(d, x1, z1, x2, z2, 2, 5)
    d.fill(x1, 1, z1, x2, 1, z2, "polished_diorite")
    d.flat(x1, z1 - 1, x2, z2, 6, "smooth_quartz", "white_concrete", "smooth_quartz_slab")
    for x in range(x1, x2 + 1):
        d.set(x, 6, z1 - 1, "cyan_terracotta")
    for x in range(x1 + 1, x2):
        d.window(x, 2, z1, x, 5, z1, "glass_pane")
    for x in (6, 10):
        d.set(x, 2, z1, "light_gray_concrete")
        for y in range(3, 6):
            d.set(x, y, z1, "light_gray_concrete")
    d.double_door(7, 2, z1, "x", "south", "birch")
    d.sign(10, 5, z1 - 1, "north", ["", "SECURITY", "POST"], "birch", glow=True, color="cyan")
    # shaft
    sx1, sz1, sx2, sz2 = 6, 9, 10, 13
    yp = 7 + 3 * L
    nt_walls(d, sx1, sz1, sx2, sz2, 2, yp - 1, "light_gray_concrete", "gray_concrete")
    d.fill(sx1 + 1, 1, sz1 + 1, sx2 - 1, 1, sz2 - 1, "polished_diorite")
    for y in range(3, yp - 1):
        d.set(8, y, sz2, "cyan_stained_glass")
    d.set(8, 2, sz1, AIR)
    d.set(8, 3, sz1, AIR)
    ladder(d, 8, sz2 - 1, 2, yp, "north")
    # pod
    px1, pz1, px2, pz2 = 4, 7, 12, 15
    d.fill(px1, yp, pz1, px2, yp, pz2, "light_gray_concrete")
    d.set(8, yp, sz2 - 1, "ladder[facing=north,waterlogged=false]")
    nt_walls(d, px1, pz1, px2, pz2, yp + 1, yp + 3, "light_gray_stained_glass_pane", "white_concrete")
    d.flat(px1, pz1, px2, pz2, yp + 4, "white_concrete", "smooth_quartz", None)
    for x in range(px1, px2 + 1):
        for z in (pz1, pz2):
            d.set(x, yp, z, "cyan_terracotta")
    for z in range(pz1, pz2 + 1):
        for x in (px1, px2):
            d.set(x, yp, z, "cyan_terracotta")
    for x in range(px1 + 1, px2):                                # console desk along the street glass
        d.set(x, yp + 1, pz1 + 1, SL("smooth_quartz", "top"))
        if x % 2:
            d.set(x, yp + 2, pz1 + 1, "black_stained_glass_pane")
    for x in (6, 8, 10):
        d.chair(x, yp + 1, pz1 + 2, "south", "birch", sit=False)
    d.set(px1 + 2, yp + 1, pz2 - 2, "cartography_table")
    d.set(px2 - 1, yp + 1, pz2 - 1, "potted_bamboo")
    for x in (6, 10):
        d.set(x, yp + 3, 11, "sea_lantern")
        d.set(x, yp + 3, 11, AIR)
        d.set(x, yp + 4, 11, "sea_lantern")
    # antenna and beacon
    for y in range(yp + 6, yp + 9):
        d.set(8, y, 11, "iron_bars")
    d.set(8, yp + 5, 11, "sea_lantern")
    d.set(8, yp + 9, 11, ROD())
    # lobby
    d.hut(x1 + 1, 2, z1 + 1)
    d.item(x1 + 1, 2, z2 - 1, "barrel")
    for x in (x1 + 2, x1 + 3):                                  # lockers
        d.set(x, 2, z2 - 1, "iron_block")
        d.set(x, 3, z2 - 1, "iron_trapdoor[facing=north,half=bottom,open=true,powered=false,waterlogged=false]")
    for z in range(z1 + 2, z1 + 5):                             # front desk with screens
        d.set(5, 2, z, "smooth_quartz")
        if z != z1 + 3:
            d.set(5, 3, z, "black_stained_glass_pane")
    d.chair(4, 2, z1 + 3, "west", "birch", sit=False)
    # crew room behind a glass partition
    for z in range(z1 + 1, z2):
        d.set(10, 2, z, "white_concrete" if z == z1 + 1 else "light_gray_stained_glass_pane")
        for y in (3, 4):
            d.set(10, y, z, "light_gray_stained_glass_pane")
        d.set(10, 5, z, "white_concrete")
    d.door(10, 2, z1 + 3, "east", "birch")
    d.bed(x2 - 1, 2, z1 + 1, "east")
    d.bed(x2 - 1, 2, z2 - 1, "east")
    d.set(x2 - 1, 2, z1 + 3, "white_concrete")
    d.set(x2 - 1, 3, z1 + 3, "end_rod[facing=up]")
    for x in range(x1 + 2, x2, 3):
        d.set(x, 5, 6, "sea_lantern")
    d.window(x1, 3, 6, x1, 4, 7, "glass_pane")
    d.window(x2, 3, 5, x2, 4, 7, "glass_pane")
    if L >= 3:                                                  # roof terrace on the lobby
        for x in range(x1 + 1, x2):
            d.set(x, 7, z1, "azalea" if x % 3 == 0 else "moss_block")
        d.set(x1 + 1, 7, z1 + 3, "white_concrete")
        for z in range(z1 + 1, z1 + 5, 2):
            d.chair(x1 + 2, 7, z, "west", "birch", sit=False)
        d.set(x1 + 3, 7, z1 + 2, SL("smooth_quartz", "top"))
        ladder(d, x1 - 1, z1 + 2, 2, 6, "west")
        d.set(x1, 7, z1 + 2, AIR)
        d.set(x1, 8, z1 + 2, AIR)
    if L >= 4:                                                  # armoury wing
        ax1, ax2 = 14, 19
        nt_walls(d, ax1, 5, ax2, 12, 2, 5)
        d.fill(ax1, 1, 5, ax2, 1, 12, "polished_diorite")
        d.flat(ax1, 5, ax2, 12, 6, "smooth_quartz", "white_concrete", "smooth_quartz_slab")
        d.set(ax1, 2, 7, AIR) if False else None
        d.door(16, 2, 5, "south", "birch")
        d.window(18, 3, 5, 18, 4, 5, "glass_pane")
        for z in range(7, 11, 2):
            d.window(ax2, 3, z, ax2, 4, z, "glass_pane")
        weapon_rack(d, ax1 + 1, 8, ax1 + 1, 11, 2, "birch", "east")
        for z in (8, 10):
            d.banner(ax1 + 1, 4, z, "east", "cyan")
        d.set(ax2 - 1, 2, 11, "smithing_table")
        d.set(ax2 - 1, 2, 10, "grindstone[face=floor,facing=west]")
        d.set(17, 5, 9, "sea_lantern")
    if L >= 5:                                                  # helipad markings on the pod roof
        for x in range(px1 + 1, px2):
            for z in range(pz1 + 1, pz2):
                if (x in (6, 10) and 9 <= z <= 13) or (z == 11 and 6 <= x <= 10):
                    d.set(x, yp + 4, z, "yellow_concrete")
        d.set(8, yp + 4, 11, "white_concrete")
    return d


@design("guardtower")
def guardtower(pack, rel, L):
    return {"Hearthwood": gt_hearthwood, "Cascadia": gt_cascadia, "Neoterra": gt_neoterra}[pack](rel, L)


# ================================================================================================ ARCHERY
"""
Archery
  Hearthwood  Village butts: brick-and-timber longhouse on the street (fletcher's shop + mess below, bunk room
              under the gable above), a covered shooting gallery on its back wall (L2+) and a hedged grass range
              with gravel lanes running to hay-bale butts and an earth berm.
  Cascadia    Hunting lodge: long log lodge with bunk beds on the west, a shooting shed with a shed roof at the
              head of a fenced range on the east, targets in front of a stacked-log backstop.
  Neoterra    Indoor archery centre: two-storey glazed clubhouse on the street (lobby/workshop, dorm above,
              roof terrace L4+) in front of a long white range hall with skylights, glass lane dividers and a
              lit black backstop.
"""
TARGETS = {1: 3, 2: 5, 3: 6, 4: 7, 5: 9}


def lane_order(xs):
    c = sum(xs) / len(xs)
    return sorted(xs, key=lambda x: (abs(x - c), x))


def place_beds(d, slots, n, color=None):
    """slots: list of (x, y, z, facing); places the first n."""
    for x, y, z, f in slots[:n]:
        d.bed(x, y, z, f, color)


def ar_hearthwood(rel, L):
    d = Design("Hearthwood", rel, (27, 20, 31))
    X2 = {1: 13, 2: 13, 3: 17, 4: 21, 5: 23}[L]
    x1, z1, z2 = 3, 3, 9
    d.box(x1, 2, z1, X2, 5, z2, "bricks", floor="oak_planks")
    for x in range(x1, X2 + 1):
        for z in range(z1, z2 + 1):
            if x in (x1, X2) or z in (z1, z2):
                d.set(x, 2, z, "stone_bricks")
    d.fill(x1, 6, z1, X2, 6, z2, "dark_oak_planks")
    hw_frame(d, x1, z1, X2, z2, 7, 10)
    soft(d, d.gable, x1, z1, X2, z2, 11, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite", 1)
    door = 7
    d.door(door, 2, z1, "south", "dark_oak")
    for x in range(x1 + 2, X2 - 1, 3):
        if abs(x - door) > 1:
            d.window(x, 3, z1, x, 4, z1)
    for x in range(x1 + 1, X2, 2):
        if x % 4 == 1:
            d.window(x, 8, z1, x, 9, z1)
            d.window(x, 8, z2, x, 9, z2)
    d.window(x1, 3, 6, x1, 4, 6)
    d.window(X2, 3, 6, X2, 4, 6)
    d.window(x1, 8, 6, x1, 9, 6)
    d.window(X2, 8, 6, X2, 9, 6)
    d.door(10, 2, z2, "north", "dark_oak")
    for x in (12, 13) if X2 > 13 else ():
        pass
    d.sign(door + 2, 5, z1 - 1, "east", ["The Butts", "Bowyers &", "Fletchers"], "dark_oak", hanging=True)
    d.set(door + 3, 5, z1 - 1, "dark_oak_planks")
    # ground floor: fletcher's shop and mess
    d.hut(x1 + 1, 2, z1 + 1)
    d.item(X2 - 1, 2, z1 + 1, "furnace", "west")
    if L >= 3:
        d.item(X2 - 2, 2, z1 + 1, "fletching_table")
        d.set(X2 - 3, 2, z1 + 1, "crafting_table")
    else:
        d.set(X2 - 2, 2, z1 + 1, "crafting_table")
    weapon_rack(d, X2 - 1, z1 + 3, X2 - 1, z1 + 4, 2, "dark_oak", "west")
    d.keg(X2 - 1, 2, z2 - 1, "west")
    d.set(X2 - 1, 3, z2 - 1, "decorated_pot[cracked=false,facing=west,waterlogged=false]")
    d.dining(8, 2, 6, 2 if L < 3 else 4, "x", "dark_oak", ("n", "s"), sit=False)
    d.banner(x1 + 1, 4, 6, "east", "green")
    for x in range(x1 + 3, X2 - 1, 4):
        d.lamp(x, 5, 6)
    # stair up along the back wall
    flight(d, x1 + 1, 2, z2 - 1, "east", 4, "dark_oak", "dark_oak_planks")
    for x in range(x1 + 2, x1 + 5):
        d.set(x, 7, z2 - 2, "dark_oak_fence")
    # bunk room
    slots = [(x, 7, z1 + 1, "north") for x in range(x1 + 2, X2, 2)] + \
            [(x, 7, z2 - 1, "south") for x in range(x1 + 6, X2, 2)]
    place_beds(d, slots, d.req["beds"])
    for x, y, z, f in slots[:d.req["beds"]]:
        if d.air(x + 1, 7, z) and f == "north":
            d.set(x + 1, 7, z, "chest[facing=south,type=single,waterlogged=false]")
    d.rug(x1 + 5, 6, X2 - 2, 6, 7, ("green_carpet",), "plain")
    for x in range(x1 + 2, X2, 4):
        d.lamp(x, 10, 6)
    # range
    rz1, rz2 = 10, 28
    d.fill(2, 1, rz1, 24, 1, rz2 + 2, "grass_block[snowy=false]")
    xs = list(range(4, 21, 2))
    for z in range(rz1, rz2 + 1):
        for y in (2, 3):
            d.set(2, y, z, "oak_leaves[distance=7,persistent=true,waterlogged=false]")
            d.set(24, y, z, "oak_leaves[distance=7,persistent=true,waterlogged=false]")
    for x in xs:
        for z in range(13, rz2):
            d.set(x, 1, z, "gravel")
    order = lane_order(xs)
    for i, x in enumerate(order):
        d.set(x, 2, rz2, "hay_block[axis=y]")
        if i < TARGETS[L]:
            d.yard_item(x, 3, rz2, "target")
        else:
            d.set(x, 3, rz2, "hay_block[axis=x]")
    for x in range(3, 24):                                        # earth berm behind the butts
        d.set(x, 2, rz2 + 1, "dirt")
        d.set(x, 3, rz2 + 1, "grass_block[snowy=false]")
        d.set(x, 2, rz2 + 2, "grass_block[snowy=false]")
        if x not in xs:
            d.set(x, 2, rz2, "grass_block[snowy=false]")
            d.set(x, 3, rz2, "short_grass")
    d.fill(3, 1, rz1, 23, 1, 12, "gravel")
    for i, x in enumerate(order[:L]):
        d.spot(x, 2, 12, "work")
    if L >= 2:                                                    # covered shooting gallery
        gx2 = max(X2, 15)
        for x in range(x1, gx2 + 1):
            d.set(x, 5, 13, ST("deepslate_tile", "south"))
            for z in (10, 11, 12):
                d.set(x, 5, z, SL("deepslate_tile"))
        for x in range(x1, gx2 + 1, 4):
            for y in range(2, 5):
                d.set(x if x not in xs else x + 1, y, 12, LOG("stripped_dark_oak_log"))
        d.set(x1 + 2, 2, 10, "dark_oak_slab[type=bottom,waterlogged=false]") if False else None
    # quiver barrels and a bench at the line
    d.keg(23, 2, 11, "north")
    d.set(23, 3, 11, "hay_block[axis=y]") if False else None
    for x, z in ((2, rz1 - 1), (24, rz1 - 1)):
        pass
    d.set(22, 2, 10, "dark_oak_fence")
    d.set(22, 3, 10, LANT_S)
    if L >= 4:                                                    # spectators' benches by the hedge
        for z in range(15, 26, 4):
            d.chair(23, 2, z, "east", "dark_oak", sit=False)
            d.chair(23, 2, z + 1, "east", "dark_oak", sit=False)
    return d


def ar_cascadia(rel, L):
    d = Design("Cascadia", rel, (31, 20, 27), paving="coarse_dirt")
    x1, x2, z1 = 2, 10, 3
    Z2 = {1: 13, 2: 13, 3: 15, 4: 15, 5: 17}[L]
    cs_walls(d, x1, z1, x2, Z2, 2, 6)
    d.fill(x1 + 1, 1, z1 + 1, x2 - 1, 1, Z2 - 1, "spruce_planks")
    ridge = soft(d, d.gable, x1, z1, x2, Z2, 7, "z", "dark_oak_stairs", "dark_oak_slab", "spruce_planks", 1)
    d.door(6, 2, z1, "south", "spruce")
    d.window(4, 3, z1, 4, 5, z1)
    d.window(8, 3, z1, 8, 5, z1)
    d.window(6, 8, z1, 6, 9, z1)
    for z in range(z1 + 3, Z2, 3):
        d.window(x1, 3, z, x1, 4, z)
    d.door(x2, 2, z1 + 3, "east", "spruce")
    d.window(x2, 3, z1 + 1, x2, 4, z1 + 1)
    # elk antlers over the door: dead bushes on a bracket
    d.set(6, 5, z1 - 1, "spruce_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
    d.sign(6, 4, z1 - 1, "north", ["HUNTERS'", "LODGE"], "spruce")
    # stone chimney at the back
    d.hearth(6, 2, Z2 - 1, "north", 7, "cobblestone", "campfire")
    for y in range(1, ridge + 2):
        d.set(6, y, Z2, "mossy_cobblestone" if y % 3 == 0 else "cobblestone")
    # front room: workshop
    d.hut(x1 + 2, 2, z1 + 1)
    d.item(x1 + 1, 2, z1 + 3, "furnace", "east")
    if L >= 3:
        d.item(x1 + 1, 2, z1 + 4, "fletching_table")
    else:
        d.set(x1 + 1, 2, z1 + 4, "crafting_table")
    d.set(x2 - 1, 2, z1 + 1, "spruce_trapdoor[facing=west,half=top,open=false,powered=false,waterlogged=false]") if False else None
    weapon_rack(d, x2 - 1, z1 + 1, x2 - 1, z1 + 1, 2, "spruce", "west")
    d.table(6, 2, z1 + 3, "spruce")
    d.chair(5, 2, z1 + 3, "west", "spruce", sit=False)
    d.chair(7, 2, z1 + 3, "east", "spruce", sit=False)
    d.set(x1 + 1, 2, z1 + 5, "barrel[facing=up,open=false]")
    d.lamp(6, 6, z1 + 3)
    d.rug(4, z1 + 2, 8, z1 + 4, 2, ("brown_carpet", "green_carpet"))
    # bunk room: bunks (bed - slab - bed) along both walls
    zs = list(range(z1 + 8, Z2 - 1, 2))
    slots = []
    for z in zs:
        slots.append((x1 + 1, z, "west"))
    for z in zs:
        slots.append((x2 - 1, z, "east"))
    need = d.req["beds"]
    i = 0
    for x, z, f in slots:
        if i >= need:
            break
        d.bed(x, 2, z, f)
        i += 1
        if i < need:
            fx = x + (1 if f == "west" else -1)
            d.set(x, 3, z, SL("spruce", "top"))
            d.set(fx, 3, z, SL("spruce", "top"))
            d.bed(x, 4, z, f)
            i += 1
    for z in range(z1 + 7, Z2, 4):
        d.lamp(6, 6, z)
    d.fill(x1 + 1, 7, z1 + 1, x2 - 1, 7, Z2 - 1, "spruce_planks")
    # covered porch along the range side
    for z in range(z1, z1 + 6):
        d.set(x2 + 1, 1, z, "spruce_planks")
        d.set(x2 + 1, 5, z, SL("spruce"))
    # range on the east
    rx1, rx2 = 12, 30
    xs = list(range(13, 30, 2))
    for x in range(rx1, rx2 + 1):
        for z in range(1, 26):
            d.set(x, 1, z, "podzol" if (x * 3 + z) % 5 == 0 else "grass_block[snowy=false]")
    for x in xs:
        for z in range(7, 23):
            d.set(x, 1, z, "coarse_dirt")
    for z in range(1, 26):
        for x in (rx1, rx2):
            d.set(x, 2, z, "spruce_fence" if z % 4 else LOG("spruce_log"))
    d.set(rx1, 2, z1 + 3, AIR)
    d.set(x2 + 1, 2, z1 + 3, AIR) if False else None
    # shooting shed (north)
    for x in range(rx1 + 1, rx2):
        d.set(x, 1, 3, "spruce_planks")
        for z in (2, 3, 4, 5):
            d.set(x, 1, z, "spruce_planks")
        d.set(x, 6, 2, ST("spruce", "south"))
        d.set(x, 5, 6, ST("spruce", "north"))
        for z in (3, 4, 5):
            d.set(x, 6 if z < 4 else 5, z, SL("spruce", "bottom") if z >= 4 else SL("spruce", "bottom"))
    for x in range(rx1 + 1, rx2):
        d.set(x, 2, 2, "spruce_fence" if x % 6 else LOG("spruce_log"))
        for y in (3, 4, 5):
            if x % 6 == 0:
                d.set(x, y, 2, LOG("spruce_log"))
    for x in range(rx1 + 2, rx2, 6):
        for y in range(2, 5):
            d.set(x, y, 6, LOG("spruce_log"))
    order = lane_order(xs)
    for x in order[:L]:
        d.spot(x, 2, 5, "work")
    d.keg(rx2 - 1, 2, 3, "north")
    d.set(rx2 - 1, 3, 3, LANT_S)
    # log-crib backstop with targets
    for x in range(rx1 + 1, rx2):
        for y in (2, 3, 4):
            d.set(x, y, 24, LOG("spruce_log" if y != 3 else "stripped_spruce_log", "x"))
        d.set(x, 5, 24, SL("spruce"))
    for i, x in enumerate(order):
        d.set(x, 2, 23, "hay_block[axis=y]")
        if i < TARGETS[L]:
            d.yard_item(x, 3, 23, "target")
    for x in range(rx1 + 1, rx2):
        if x not in xs:
            d.set(x, 2, 23, "fern")
    if L >= 4:                                                   # skinning rack and stump seats by the lodge
        for z in (20, 22):
            d.set(4, 2, z, LOG("spruce_log"))
            d.set(4, 3, z, SL("spruce"))
        d.set(7, 2, 21, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        d.chair(7, 2, 20, "north", "spruce", sit=False) if False else None
        for x, z in ((6, 21), (8, 21), (7, 22)):
            d.set(x, 2, z, LOG("stripped_spruce_log"))
    return d


def ar_neoterra(rel, L):
    d = Design("Neoterra", rel, (25, 18, 33), paving="smooth_stone")
    x1, x2, z1, z2 = 3, 21, 2, 9
    # clubhouse
    nt_walls(d, x1, z1, x2, z2, 2, 6)
    d.fill(x1, 1, z1, x2, 1, z2, "polished_diorite")
    d.fill(x1, 7, z1, x2, 7, z2, "light_gray_concrete")
    nt_walls(d, x1, z1, x2, z2, 8, 11)
    d.flat(x1, z1, x2, z2, 12, "smooth_quartz", "white_concrete", "smooth_quartz_slab")
    for x in range(x1, x2 + 1):
        d.set(x, 7, z1, "cyan_terracotta")
    for x in range(x1 + 1, x2):
        if x % 4 != 3:
            d.window(x, 2, z1, x, 5, z1, "glass_pane")
            d.window(x, 8, z1, x, 10, z1, "light_gray_stained_glass_pane")
    d.double_door(11, 2, z1, "x", "south", "birch")
    d.window(11, 5, z1, 12, 6, z1, "glass_pane")
    for x in range(10, 15):
        d.set(x, 6, z1 - 1, SL("smooth_quartz", "top"))
    d.sign(x1 + 4, 6, z1 - 1, "north", ["", "ARCHERY", "CENTRE"], "birch", glow=True, color="cyan")
    for z in range(z1 + 2, z2 - 1, 2):
        d.window(x1, 3, z, x1, 5, z)
        d.window(x2, 9, z, x2, 10, z)
    # lobby / workshop
    d.hut(x1 + 1, 2, z1 + 1)
    for x in range(14, 19):                                       # reception desk
        d.set(x, 2, z1 + 3, "smooth_quartz")
    d.chair(16, 2, z1 + 4, "south", "birch", sit=False) if False else None
    d.item(x2 - 1, 2, z1 + 1, "furnace", "west")
    if L >= 3:
        d.item(x2 - 1, 2, z1 + 2, "fletching_table")
    else:
        d.set(x2 - 1, 2, z1 + 2, "crafting_table")
    weapon_rack(d, x2 - 1, z1 + 4, x2 - 1, z1 + 5, 2, "birch", "west")
    for x in range(x1 + 3, x1 + 6):                               # lounge
        d.chair(x, 2, z1 + 1, "north", "birch", sit=False)
    d.set(x1 + 4, 2, z1 + 2, SL("smooth_quartz", "top"))
    d.plant(x1 + 6, 2, z1 + 1, "potted_bamboo")
    for x in range(x1 + 2, x2, 4):
        d.set(x, 6, 5, "sea_lantern")
    flight(d, x1 + 1, 2, z2 - 1, "east", 5, "smooth_quartz", "white_concrete")
    for x in range(x1 + 3, x1 + 6):
        d.set(x, 8, z2 - 2, "light_gray_stained_glass_pane")
    # dorm
    slots = [(x, 8, z1 + 1, "north") for x in range(x1 + 1, x2, 2)] + \
            [(x, 8, z2 - 1, "south") for x in range(x1 + 7, x2, 2)]
    place_beds(d, slots, d.req["beds"], "cyan")
    d.rug(x1 + 1, 5, x2 - 1, 6, 8, ("light_gray_carpet",), "plain")
    for x in range(x1 + 2, x2, 4):
        d.set(x, 11, 5, "sea_lantern")
    # range hall
    hz2 = 30
    nt_walls(d, x1, z2, x2, hz2, 2, 7)
    for x in range(x1, x2 + 1):
        d.set(x, 7, z2, "light_gray_concrete")
    d.flat(x1, z2 + 1, x2, hz2, 8, "smooth_quartz", "white_concrete", "smooth_quartz_slab")
    for z in range(z2 + 3, hz2 - 1, 4):
        for x in range(x1 + 2, x2 - 1):
            d.set(x, 8, z, "glass")
    for z in range(z2 + 2, hz2 - 1, 2):
        d.window(x1, 5, z, x1, 6, z, "glass_pane")
        d.window(x2, 5, z, x2, 6, z, "glass_pane")
    d.double_door(13, 2, z2, "x", "north", "birch")
    for z in range(z2 + 1, hz2 + 1):                              # cyan band and fins along the hall
        for x in (x1, x2):
            d.set(x, 7, z, "cyan_terracotta")
            if z % 4 == 0:
                for y in range(2, 5):
                    d.set(x, y, z, "light_gray_concrete")
    for x in range(x1, x2 + 1):
        d.set(x, 7, hz2, "cyan_terracotta")
    d.sign(x2 + 1, 4, 14, "east", ["", "ARCHERY", "RANGE"], "birch", glow=True, color="cyan")
    d.fill(x1 + 1, 1, z2 + 1, x2 - 1, 1, hz2 - 1, "smooth_stone")
    d.fill(x1 + 1, 1, z2 + 4, x2 - 1, 1, z2 + 4, "cyan_concrete")                 # shooting line
    xs = list(range(4, 21, 2))
    order = lane_order(xs)
    for x in xs:
        for z in range(z2 + 5, hz2 - 1):
            d.set(x, 1, z, "light_gray_concrete")
    for x in range(5, 20, 2):
        for z in range(z2 + 5, z2 + 10):
            d.set(x, 2, z, "light_gray_stained_glass_pane")
    for x in range(x1 + 1, x2):                                   # backstop
        for y in range(2, 7):
            d.set(x, y, hz2 - 1, "black_concrete")
        d.set(x, 7, hz2 - 1, "sea_lantern" if x % 2 == 0 else "black_concrete")
    for i, x in enumerate(order):
        d.set(x, 2, hz2 - 2, "white_concrete")
        if i < TARGETS[L]:
            d.yard_item(x, 3, hz2 - 2, "target")
    for x in order[:L]:
        d.spot(x, 2, z2 + 3, "work")
    for x in (x1 + 1, x2 - 1):
        d.chair(x, 2, z2 + 2, "north", "birch", sit=False)
    if L >= 4:                                                    # roof terrace
        d.set(x2 - 1, 12, z2 - 1, AIR)
        ladder(d, x2 - 1, z2 - 1, 8, 12, "north")
        d.set(x2 - 1, 8, z2 - 1, "ladder[facing=north,waterlogged=false]")
        for x in range(x1 + 2, x2 - 2, 3):
            d.set(x, 13, z1 + 1, "azalea")
            d.set(x, 13, z2 - 2, "moss_carpet")
        for x in range(x1 + 3, x1 + 9, 2):
            d.chair(x, 13, z1 + 4, "south", "birch", sit=False)
        d.set(x1 + 10, 13, z1 + 4, "smooth_quartz_slab[type=top,waterlogged=false]")
    return d


@design("archery")
def archery(pack, rel, L):
    return {"Hearthwood": ar_hearthwood, "Cascadia": ar_cascadia, "Neoterra": ar_neoterra}[pack](rel, L)


# ================================================================================================ COMBAT ACADEMY
"""
Combat academy
  Hearthwood  Fencing school & tiltyard: gable-fronted brick-and-timber drill hall on the west (armoury and
              forge below, barracks under the roof), a fenced sand ring with pells and dummies on the east, and
              (L2+) a three-tier grandstand under a red-and-white striped canopy on the south side.
  Cascadia    Fight barn: a big log barn with a dirt sparring ring fenced in the middle, two-tier log bleachers
              along both long walls (L2+), a bunk loft over the front armoury and (L3+) a forge lean-to.
  Neoterra    Rooftop arena: a low glazed training centre (lobby, gym with dummies, dorm) whose roof is an
              open-air court with ring markings, floodlight masts, a stair kiosk and (L2+) tiered stands under a
              cantilevered canopy.
"""


def ca_hearthwood(rel, L):
    d = Design("Hearthwood", rel, (30, 20, 27))
    x1, x2, z1 = 2, 10, 2
    Z2 = {1: 12, 2: 14, 3: 16, 4: 18, 5: 20}[L]
    d.box(x1, 2, z1, x2, 5, Z2, "bricks", floor="spruce_planks")
    for x in range(x1, x2 + 1):
        for z in range(z1, Z2 + 1):
            if x in (x1, x2) or z in (z1, Z2):
                d.set(x, 2, z, "stone_bricks")
    d.fill(x1, 6, z1, x2, 6, Z2, "dark_oak_planks")
    hw_frame(d, x1, z1, x2, Z2, 7, 10)
    soft(d, d.gable, x1, z1, x2, Z2, 11, "z", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite", 1)
    for y in range(11, 15):
        d.set(6, y, z1, LOG("stripped_dark_oak_log"))
    # big arched double door and crossed-sword sign
    d.double_door(5, 2, z1, "x", "south", "dark_oak")
    d.set(5, 4, z1, ST("stone_brick", "west", "top"))
    d.set(6, 4, z1, ST("stone_brick", "east", "top"))
    d.banner(4, 4, z1 - 1, "north", "red")
    d.banner(7, 4, z1 - 1, "north", "red")
    d.sign(6, 5, z1 - 1, "north", ["Academy of", "Arms"], "dark_oak")
    d.window(3, 3, z1, 3, 4, z1)
    d.window(9, 3, z1, 9, 4, z1)
    for x in (4, 8):
        d.window(x, 8, z1, x, 9, z1)
    d.window(6, 12, z1, 6, 12, z1) if False else None
    for z in range(z1 + 2, Z2 - 1, 3):
        d.window(x1, 3, z, x1, 4, z)
        d.window(x1, 8, z, x1, 9, z)
        d.window(x2, 8, z, x2, 9, z)
    d.door(x2, 2, z1 + 3, "east", "dark_oak")
    # armoury / forge
    d.hut(x1 + 1, 2, z1 + 1)
    d.item(x1 + 1, 2, z1 + 3, "furnace", "east")
    d.item(x1 + 1, 2, z1 + 4, "barrel")
    if L >= 3:
        d.item(x1 + 1, 2, z1 + 6, "anvil", "south")
        d.item(x1 + 1, 2, z1 + 7, "grindstone", "east")
    d.set(x1 + 1, 2, z1 + 5, "water_cauldron[level=3]")
    weapon_rack(d, x2 - 1, z1 + 1, x2 - 1, z1 + 2, 2, "dark_oak", "west")
    d.banner(x2 - 1, 4, z1 + 5, "west", "red")
    dummy(d, 7, 2, z1 + 6, "west")
    d.lamp(6, 5, z1 + 3)
    d.lamp(6, 5, Z2 - 3)
    # stairs up the middle aisle (rising south)
    sz = Z2 - 5
    flight(d, 6, 2, sz, "south", 4, "dark_oak", "dark_oak_planks")
    for z in range(sz, sz + 3):
        d.set(5, 7, z, "dark_oak_fence")
        d.set(7, 7, z, "dark_oak_fence")
    # barracks under the roof
    slots = []
    for z in range(z1 + 1, Z2, 2):
        slots += [(x1 + 1, 7, z, "west"), (x2 - 1, 7, z, "east")]
    place_beds(d, slots, d.req["beds"])
    for x, y, z, f in slots[:d.req["beds"]]:
        if d.air(x, 7, z + 1) and z + 1 < Z2:
            d.set(x, 7, z + 1, "chest[facing=%s,type=single,waterlogged=false]" % ("east" if f == "west" else "west"))
    for z in range(z1 + 2, Z2, 4):
        d.lamp(6, 12, z) if d.air(6, 12, z) else None
    # sand ring
    rx1, rz1, rx2, rz2 = 13, 3, 27, 18
    d.fill(rx1, 1, rz1, rx2, 1, rz2, "sand")
    for x in range(rx1, rx2 + 1):
        for z in range(rz1, rz2 + 1):
            if x in (rx1, rx2) or z in (rz1, rz2):
                d.set(x, 1, z, "stone_bricks")
                d.set(x, 2, z, "dark_oak_fence" if (x + z) % 5 else LOG("stripped_dark_oak_log"))
    d.set(rx1, 2, 5, "dark_oak_fence_gate[facing=east,in_wall=false,open=false,powered=false]")
    d.fill(x2 + 1, 1, 5, rx1, 1, 5, "gravel")
    d.set(20, 2, rz1, "dark_oak_fence_gate[facing=north,in_wall=false,open=false,powered=false]")
    d.fill(20, 1, 0, 20, 1, rz1 - 1, "gravel")
    for x in (16, 20, 24):
        dummy(d, x, 2, rz1 + 2, "south")
    for z in (8, 12):                                             # pells: posts to hack at
        d.set(rx2 - 2, 2, z, LOG("stripped_oak_log"))
        d.set(rx2 - 2, 3, z, LOG("stripped_oak_log"))
    d.set(rx2 - 1, 2, rz1 + 1, "hay_block[axis=y]")
    d.set(rx2 - 1, 3, rz1 + 1, "target[power=0]")
    weapon_rack(d, rx1 + 1, 9, rx1 + 1, 12, 2, "dark_oak", "east")
    d.rug(17, 9, 21, 13, 2, ("white_carpet", "red_carpet"))
    for x, z in ((rx1, rz1), (rx2, rz1), (rx1, rz2), (rx2, rz2)):
        d.set(x, 3, z, LANT_S)
    if L >= 2:                                                    # grandstand
        gx1, gx2 = 14, 26
        n = 0
        for x in range(gx1, gx2 + 1):
            for t, z in enumerate((20, 21, 22)):
                d.set(x, 1, z, "stone_bricks")
                for y in range(2, 2 + t):
                    d.set(x, y, z, "dark_oak_planks")
                if n < 32 and x not in (gx1, gx2):
                    d.chair(x, 2 + t, z, "south", "dark_oak")
                    n += 1
                else:
                    d.set(x, 2 + t, z, SL("dark_oak"))
        for x in range(gx1 - 1, gx2 + 2):
            for y in range(2, 6):
                d.set(x, y, 23, "bricks" if x in (gx1 - 1, gx2 + 1) else ("dark_oak_planks" if y < 4 else AIR))
        for x in (gx1 - 1, gx2 + 1, 20):
            for y in range(2, 8):
                d.set(x, y, 23, LOG("stripped_dark_oak_log"))
            for y in range(2, 7):
                d.set(x, y, 19, "dark_oak_fence" if x != 20 else AIR)
        for x in range(gx1 - 1, gx2 + 2):
            for z in range(19, 24):
                y = 7 if z >= 21 else 6
                d.set(x, y, z, "red_wool" if x % 2 else "white_wool")
            d.set(x, 6, 19, ST("dark_oak", "south", "top") if False else ("red_wool" if x % 2 else "white_wool"))
        for x in range(gx1, gx2 + 1, 3):
            d.banner(x, 5, 18, "north", "red" if x % 2 else "white") if d.air(x, 5, 18) else None
    if L >= 4:                                                    # quintain in the ring
        d.set(24, 2, 15, "dark_oak_fence")
        d.set(24, 3, 15, "dark_oak_fence")
        d.set(24, 4, 15, "dark_oak_fence")
        d.set(23, 4, 15, "dark_oak_fence")
        d.set(25, 4, 15, "dark_oak_fence")
        d.set(23, 3, 15, "white_banner") if False else None
        d.set(16, 2, 15, "hay_block[axis=y]")
        d.set(16, 3, 15, "target[power=0]")
    if L >= 5:
        for x in (rx1, rx2):
            for y in range(3, 7):
                d.set(x, y, rz1, LOG("stripped_dark_oak_log"))
            d.banner(x, 6, rz1 - 1, "north", "red")
    return d


def ca_cascadia(rel, L):
    d = Design("Cascadia", rel, (28, 20, 28), paving="coarse_dirt")
    x1, x2, z1 = 3, 19, 4
    Z2 = 16 if L == 1 else 25
    cs_walls(d, x1, z1, x2, Z2, 2, 7)
    d.fill(x1 + 1, 1, z1 + 1, x2 - 1, 1, Z2 - 1, "spruce_planks")
    soft(d, d.gable, x1, z1, x2, Z2, 8, "z", "dark_oak_stairs", "dark_oak_slab", "spruce_planks", 1)
    for x in range(x1, x2 + 1):                                   # board-and-batten gables over the logs
        for y in range(8, 18):
            for z in (z1, Z2):
                if d.get(x, y, z) == "minecraft:spruce_planks" and x % 3 == 0:
                    d.set(x, y, z, LOG("stripped_spruce_log"))
    mid = 11
    d.double_door(mid - 1, 2, z1, "x", "south", "spruce")
    d.double_door(mid + 1, 2, z1, "x", "south", "spruce") if False else None
    for y in (2, 3):
        d.set(mid + 1, y, z1, AIR)
    d.set(mid + 1, 2, z1, "spruce_fence_gate[facing=north,in_wall=false,open=false,powered=false]")
    for x in range(mid - 2, mid + 3):
        d.set(x, 4, z1, LOG("stripped_spruce_log", "x"))
    d.window(mid - 4, 3, z1, mid - 4, 5, z1)
    d.window(mid + 4, 3, z1, mid + 4, 5, z1)
    d.window(mid, 9, z1, mid, 11, z1)
    d.sign(mid, 6, z1 - 1, "north", ["FIGHT BARN", "est. 1902"], "spruce")
    for z in range(z1 + 3, Z2 - 1, 3):
        d.window(x1, 4, z, x1, 5, z)
        d.window(x2, 4, z, x2, 5, z)
    # front: armoury, hut and gear
    d.hut(x1 + 1, 2, z1 + 1)
    d.item(x1 + 1, 2, z1 + 3, "furnace", "east")
    d.item(x1 + 1, 2, z1 + 4, "barrel")
    d.set(x1 + 1, 2, z1 + 2, "water_cauldron[level=3]")
    weapon_rack(d, x2 - 1, z1 + 1, x2 - 1, z1 + 4, 2, "spruce", "west")
    d.set(x2 - 2, 2, z1 + 1, "barrel[facing=north,open=false]")
    # bunk loft over the front (deck y6), ladder against the west wall
    d.fill(x1 + 1, 6, z1 + 1, x2 - 1, 6, z1 + 5, "spruce_planks")
    for x in range(x1 + 1, x2):
        d.set(x, 7, z1 + 6, "spruce_fence")
        d.set(x, 5, z1 + 6, ST("spruce", "north", "top")) if x % 2 else None
    ladder(d, x1 + 1, z1 + 6, 2, 7, "east")
    d.set(x1 + 1, 7, z1 + 6, "ladder[facing=east,waterlogged=false]")
    d.set(x1 + 2, 7, z1 + 6, AIR)
    slots = [(x, 7, z1 + 1, "north") for x in range(x1 + 2, x2, 2)] + \
            [(x, 7, z1 + 4, "south") for x in range(x1 + 4, x2, 2)]
    # head south at z1+4 means foot at z1+3: keep z1+5 walkway? use z1+5 heads south
    slots = [(x, 7, z1 + 1, "north") for x in range(x1 + 2, x2, 2)] + \
            [(x, 7, z1 + 5, "south") for x in range(x1 + 4, x2, 2)]
    place_beds(d, slots, d.req["beds"])
    for x in range(x1 + 3, x2, 4):
        d.lamp(x, 5, z1 + 3)
        if d.air(x, 11, z1 + 3):
            d.lamp(x, 11, z1 + 3)
    # sparring ring
    rx1, rx2 = 7, 15
    rz1, rz2 = z1 + 8, Z2 - 3
    for x in range(rx1, rx2 + 1):
        for z in range(rz1, rz2 + 1):
            d.set(x, 1, z, "coarse_dirt" if (x + z) % 3 else "dirt")
            if x in (rx1, rx2) or z in (rz1, rz2):
                d.set(x, 2, z, "spruce_fence" if (x, z) not in ((rx1, rz1), (rx2, rz1), (rx1, rz2), (rx2, rz2))
                      else LOG("spruce_log"))
    d.set(11, 2, rz1, "spruce_fence_gate[facing=north,in_wall=false,open=false,powered=false]")
    for x, z in ((rx1, rz1), (rx2, rz1), (rx1, rz2), (rx2, rz2)):
        d.set(x, 3, z, LANT_S)
    dummy(d, 9, 2, rz1 + 2, "south")
    dummy(d, 13, 2, rz1 + 2, "south")
    d.set(11, 2, rz2 - 1, "hay_block[axis=x]")
    d.set(10, 2, rz2 - 1, "hay_block[axis=x]")
    for z in range(rz1, rz2 + 1, 4):
        d.lamp(11, 7, z)
    if L >= 2:                                                    # bleachers along both walls
        n = 0
        for z in range(z1 + 9, z1 + 17):
            for x, xb, f in ((x1 + 2, x1 + 1, "west"), (x2 - 2, x2 - 1, "east")):
                d.chair(x, 2, z, f, "spruce")
                d.set(xb, 2, z, LOG("spruce_log", "z"))
                d.chair(xb, 3, z, f, "spruce")
                n += 2
        for z in (z1 + 8, z1 + 17):
            for x in (x1 + 1, x1 + 2, x2 - 2, x2 - 1):
                d.set(x, 2, z, LOG("stripped_spruce_log"))
    else:
        d.set(x2, 2, Z2 - 3, AIR)
    if L >= 3:                                                    # forge lean-to on the east wall
        fx1, fx2 = x2, x2 + 5
        fz1, fz2 = z1 + 2, z1 + 8
        for x in range(fx1 + 1, fx2 + 1):
            for z in range(fz1, fz2 + 1):
                d.set(x, 1, z, "cobblestone")
                d.set(x, 6 - (x - fx1) // 2, z, SL("dark_oak") if (x - fx1) % 2 == 0 else "dark_oak_planks")
        for x, z in ((fx2, fz1), (fx2, fz2)):
            for y in range(2, 4):
                d.set(x, y, z, LOG("spruce_log"))
        d.item(fx1 + 2, 2, fz1 + 2, "anvil", "south")
        d.item(fx1 + 2, 2, fz1 + 4, "grindstone", "east")
        d.set(fx2, 2, fz1 + 3, "cobblestone")
        d.set(fx2, 3, fz1 + 3, "cobblestone")
        d.set(fx2 - 1, 2, fz1 + 3, "campfire[facing=west,lit=true,signal_fire=false,waterlogged=false]")
        d.set(fx1 + 1, 2, fz2, "water_cauldron[level=3]")
        d.door(x2, 2, fz1 + 3, "east", "spruce")
    if L >= 4:                                                    # outdoor log-lifting yard
        for x in (22, 24):
            d.set(x, 2, 18, LOG("spruce_log", "z"))
            d.set(x, 2, 19, LOG("spruce_log", "z"))
        dummy(d, 23, 2, 22, "west")
        d.set(25, 2, 22, "hay_block[axis=y]")
        d.set(25, 3, 22, "target[power=0]")
    if L >= 5:
        for z in (z1 + 9, z1 + 13):
            d.banner(x1 + 1, 6, z, "east", "green")
            d.banner(x2 - 1, 6, z, "west", "green")
    return d


def ca_neoterra(rel, L):
    d = Design("Neoterra", rel, (23, 16, 23), paving="smooth_stone")
    x1, z1, x2, z2 = 2, 3, 20, 19
    nt_walls(d, x1, z1, x2, z2, 2, 6)
    d.fill(x1, 1, z1, x2, 1, z2, "polished_diorite")
    d.fill(x1, 7, z1, x2, 7, z2, "light_gray_concrete")
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if x in (x1, x2) or z in (z1, z2):
                d.set(x, 7, z, "cyan_terracotta")
                d.set(x, 8, z, "light_gray_stained_glass_pane")
    for x in range(x1 + 1, x2):                                   # glazed street front
        if x % 3 != 2:
            d.window(x, 2, z1, x, 5, z1, "glass_pane")
    for z in range(z1 + 2, z2 - 1, 3):
        d.window(x1, 3, z, x1, 5, z)
        d.window(x2, 3, z, x2, 5, z)
    d.double_door(10, 2, z1, "x", "south", "birch")
    d.sign(13, 6, z1 - 1, "north", ["", "COMBAT", "ACADEMY"], "birch", glow=True, color="cyan")
    # court markings on the roof
    for x in range(x1 + 1, x2):
        for z in range(z1 + 1, z2):
            r = ((x - 11) ** 2 + (z - 13) ** 2) ** 0.5
            if 4.5 <= r < 5.5:
                d.set(x, 7, z, "cyan_concrete")
            elif r < 1:
                d.set(x, 7, z, "white_concrete")
    # floodlight masts
    for x, z in ((x1 + 1, z2 - 1), (x2 - 1, z2 - 1), (x2 - 1, z1 + 1)):
        for y in range(8, 12):
            d.set(x, y, z, "iron_bars")
        d.set(x, 12, z, "sea_lantern")
        d.set(x, 13, z, "daylight_detector[inverted=false,power=0]")
    # ground floor: lobby / armoury (north), gym (west), dorm (east)
    d.hut(x1 + 1, 2, z1 + 1)
    for x in range(x1 + 4, x1 + 7):
        d.set(x, 2, z1 + 3, "smooth_quartz")
    d.item(x2 - 1, 2, z1 + 1, "furnace", "west")
    d.item(x2 - 1, 2, z1 + 2, "barrel")
    if L >= 3:
        d.item(x2 - 1, 2, z1 + 4, "anvil", "south")
        d.item(x2 - 2, 2, z1 + 4, "grindstone", "north")
    weapon_rack(d, x2 - 4, z1 + 1, x2 - 2, z1 + 1, 2, "birch", "south")
    for x in range(x1 + 1, x2):                                   # partition
        if x in (6, 7, 14, 15):
            continue
        d.set(x, 2, z1 + 5, "white_concrete")
        for y in (3, 4):
            d.set(x, y, z1 + 5, "light_gray_stained_glass_pane")
        d.set(x, 5, z1 + 5, "white_concrete")
        d.set(x, 6, z1 + 5, "white_concrete")
    for x in (6, 7, 14, 15):
        d.set(x, 4, z1 + 5, "white_concrete")
        d.set(x, 5, z1 + 5, "white_concrete")
        d.set(x, 6, z1 + 5, "white_concrete")
    for z in range(z1 + 6, z2):
        if z in (z1 + 8,):
            continue
        d.set(11, 2, z, "white_concrete")
        for y in (3, 4):
            d.set(11, y, z, "light_gray_stained_glass_pane")
        d.set(11, 5, z, "white_concrete")
        d.set(11, 6, z, "white_concrete")
    d.set(11, 4, z1 + 8, "white_concrete")
    # gym
    d.rug(x1 + 2, z1 + 7, 9, z2 - 1, 2, ("blue_carpet", "light_blue_carpet"))
    for z in (z1 + 9, z1 + 12):
        dummy(d, 5, 2, z, "east")
        d.set(9, 2, z, "iron_block")
        d.set(9, 3, z, "target[power=0]")
    # stair to the roof along the west wall (rising south)
    flight(d, x1 + 1, 2, z1 + 7, "south", 5, "smooth_quartz", "white_concrete")
    # kiosk over the stair on the roof
    kx1, kz1, kx2, kz2 = x1, z1 + 8, x1 + 3, z1 + 13
    for x in range(kx1, kx2 + 1):
        for z in range(kz1, kz2 + 1):
            if x in (kx1, kx2) or z in (kz1, kz2):
                for y in range(8, 11):
                    d.set(x, y, z, "white_concrete" if x == kx1 or y == 10 else "light_gray_stained_glass_pane")
    d.fill(kx1, 11, kz1, kx2, 11, kz2, "smooth_quartz_slab[type=bottom,waterlogged=false]")
    d.door(kx2, 8, kz2 - 1, "east", "birch")
    # dorm
    slots = []
    for z in range(z1 + 6, z2, 2):
        slots += [(x2 - 1, 2, z, "east"), (12, 2, z, "west")]
    place_beds(d, slots, d.req["beds"], "cyan")
    for x in range(x1 + 3, x2, 4):
        for z in (z1 + 2, z1 + 9, z1 + 13):
            d.set(x, 6, z, "sea_lantern")
    # roof furniture
    dummy(d, 8, 8, 13, "east")
    dummy(d, 14, 8, 13, "west")
    d.set(x2 - 1, 8, z1 + 3, "water_cauldron[level=3]") if False else None
    if L >= 2:                                                    # stands with cantilevered canopy
        for x in range(x1 + 2, x1 + 18):
            if x > x2 - 2:
                break
        n = 0
        for x in range(x1 + 1, x2):
            if n >= 32:
                break
            d.set(x, 8, z1 + 1, "white_concrete")
            d.chair(x, 9, z1 + 1, "north", "birch")
            d.chair(x, 8, z1 + 2, "north", "birch")
            n += 2
        for x in range(x1, x2 + 1):
            for z in range(z1, z1 + 4):
                d.set(x, 12, z, "smooth_quartz_slab[type=bottom,waterlogged=false]")
        for x in (x1, 11, x2):
            for y in range(8, 12):
                d.set(x, y, z1, "light_gray_concrete")
        for x in range(x1 + 2, x2 - 1, 4):
            d.set(x, 11, z1 + 2, "end_rod[facing=down]")
    if L >= 4:                                                    # planters round the court edge
        for z in range(z1 + 5, z2, 3):
            d.set(x2 - 1, 8, z, "azalea")
    return d


@design("combatacademy")
def combatacademy(pack, rel, L):
    return {"Hearthwood": ca_hearthwood, "Cascadia": ca_cascadia, "Neoterra": ca_neoterra}[pack](rel, L)


# ================================================================================================ ENCHANTER
"""
Enchanter
  Hearthwood  Scholar's house: timber-framed study with a stone plinth, oriel window and steep tiled roof; the
              enchanting table stands in a ring of bookcases in the ground-floor study, L2+ a book-lined reading
              room upstairs with lecterns, L4 a single-storey library wing, L5 a walled physic garden.
  Cascadia    Mountain library: a long log-walled A-frame hall with a fully glazed front gable and porch; both
              knee walls lined with books, the enchanting circle in the far end under the ridge lanterns; the hall
              grows longer every level.
  Neoterra    Arcane tower: an 11x11 white tower with amethyst-tinted window strips, one book-lined storey per
              level (ladder core), enchanting circle on the ground floor and a crystal crown with end rods.
"""


def ench_ring(d, cx, y, cz, gap="north", h=2):
    """Bookcase ring two blocks out from the enchanting table (valid vanilla layout), one gap to walk in."""
    gx, gz = D4[gap]
    d.item(cx, y, cz, "enchanting_table")
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            if max(abs(dx), abs(dz)) != 2:
                continue
            if (dx, dz) == (2 * gx, 2 * gz) or (abs(dx) == 1 and dz == 2 * gz and gz) or \
                    (abs(dz) == 1 and dx == 2 * gx and gx):
                continue
            d.bookshelf(cx + dx, y, cz + dz, h)
    d.set(cx + gx * 2, y + 2, cz + gz * 2, SL("oak", "bottom")) if False else None


def line_walls(d, x1, z1, x2, z2, y, h, skip=()):
    """Line the inner face of a room (x1..x2/z1..z2 are the inner cells) with bookshelves where free."""
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if not (x in (x1, x2) or z in (z1, z2)) or (x, z) in skip:
                continue
            for k in range(h):
                if d.air(x, y + k, z):
                    d.bookshelf(x, y + k, z)


def en_hearthwood(rel, L):
    d = Design("Hearthwood", rel, (24, 20, 20))
    x1, z1, x2, z2 = 3, 3, 13, 11
    d.box(x1, 2, z1, x2, 5, z2, "stone_bricks", floor="spruce_planks")
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if (x in (x1, x2) or z in (z1, z2)) and (x + z) % 3 == 0:
                d.set(x, 3 + (x * z) % 2, z, "mossy_stone_bricks")
    d.fill(x1, 6, z1, x2, 6, z2, "dark_oak_planks")
    if L == 1:
        for x in range(x1, x2 + 1):
            for z in (z1, z2):
                d.set(x, 6, z, LOG("stripped_dark_oak_log", "x"))
        soft(d, d.gable, x1, z1, x2, z2, 7, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite", 1)
    else:
        hw_frame(d, x1, z1, x2, z2, 7, 10)
        soft(d, d.gable, x1, z1, x2, z2, 11, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite", 1)
        d.fill(x1 + 1, 11, z1 + 1, x2 - 1, 11, z2 - 1, "dark_oak_planks")
    # chimney on the west gable
    top = 13 if L == 1 else 17
    for y in range(2, top):
        d.set(x1 - 1, y, 7, "bricks")
    d.set(x1 - 1, 1, 7, "bricks")
    d.set(x1 - 1, top, 7, "brick_wall") if False else None
    # door, oriel bay and windows
    d.door(8, 2, z1, "south", "dark_oak")
    d.set(8, 4, z1, "chiseled_stone_bricks")
    d.sign(10, 4, z1 - 1, "north", ["Lore &", "Enchantment"], "dark_oak")
    for x in (5, 11):
        d.window(x, 3, z1, x, 4, z1)
        d.window(x, 3, z2, x, 4, z2)
    d.window(x2, 3, 7, x2, 4, 7)
    if L >= 2:                                                    # oriel window on brackets
        for x in range(6, 11):
            d.set(x, 7, z1 - 1, "dark_oak_planks")
            d.set(x, 6, z1 - 1, ST("dark_oak", "north", "top"))
            for y in (8, 9):
                d.set(x, y, z1 - 1, "glass_pane" if x not in (6, 10) else LOG("stripped_dark_oak_log"))
            d.set(x, 10, z1 - 1, ST("deepslate_tile", "south"))
            d.set(x, 8, z1, AIR)
            d.set(x, 9, z1, AIR)
        for x in (4, 12):
            d.window(x, 8, z2, x, 9, z2)
    # study: enchanting circle
    ench_ring(d, 8, 2, 7, "north")
    d.set(8, 5, 7, LANT)
    d.hut(x1 + 1, 2, z1 + 1)
    racks = [(x2 - 1, 2, z1 + 1, "west"), (x1 + 1, 2, z2 - 1, "east"), (x1 + 1, 2, z2 - 2, "east"),
             (x1 + 1, 2, z1 + 3, "east"), (x2 - 1, 2, z2 - 1, "west")]
    for x, y, z, f in racks[:d.req["racks"]]:
        d.rack(x, y, z, f)
    d.set(x1 + 1, 2, z1 + 4, "potted_azure_bluet") if False else None
    d.set(x1 + 1, 2, z1 + 2, "chiseled_bookshelf[facing=east,slot_0_occupied=true,slot_1_occupied=true,"
                             "slot_2_occupied=false,slot_3_occupied=true,slot_4_occupied=false,slot_5_occupied=true]")
    d.rug(7, 6, 9, 8, 2, ("purple_carpet",), "plain") if False else None
    if L >= 2:
        # stairs along the east wall rising south to the reading room
        flight(d, x2 - 1, 2, z1 + 2, "south", 4, "dark_oak", "dark_oak_planks")
        for z in range(z1 + 2, z1 + 5):
            d.set(x2 - 2, 7, z, "dark_oak_fence")
        skip = {(x2 - 1, z) for z in range(z1 + 1, z1 + 8)}
        skip |= {(x, z1 + 1) for x in range(6, 11)}
        line_walls(d, x1 + 1, z1 + 1, x2 - 1, z2 - 1, 7, 3, skip)
        d.item(6, 7, 7, "lectern", "east")
        d.item(10, 7, 7, "lectern", "west")
        d.table(8, 7, 7, "dark_oak", "post")
        d.chair(8, 7, 6, "north", "dark_oak", sit=False)
        d.chair(8, 7, 8, "south", "dark_oak", sit=False)
        d.rug(6, 5, 10, 9, 7, ("purple_carpet", "magenta_carpet"))
        d.chair(7, 7, z1 + 1, "south", "dark_oak", sit=False)
        d.chair(9, 7, z1 + 1, "south", "dark_oak", sit=False)
        d.lamp(8, 10, 5)
        d.lamp(8, 10, 9)
    if L >= 4:                                                    # library wing to the east
        wx1, wx2, wz1, wz2 = x2, 21, 4, 11
        d.box(wx1, 2, wz1, wx2, 5, wz2, "bricks", floor="spruce_planks")
        hw_frame(d, wx1, wz1, wx2, wz2, 4, 5, 2, infill="calcite")
        for x in range(wx1, wx2 + 1):
            for z in (wz1, wz2):
                d.set(x, 2, z, "stone_bricks")
        soft(d, d.gable, wx1, wz1, wx2, wz2, 6, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite", 1)
        d.fill(wx1 + 1, 6, wz1 + 1, wx2 - 1, 6, wz2 - 1, "dark_oak_planks")
        d.set(x2, 2, 9, AIR)
        d.set(x2, 3, 9, AIR)
        for x in (16, 19):
            d.window(x, 3, wz1, x, 4, wz1)
        d.window(wx2, 3, 7, wx2, 4, 8)
        line_walls(d, wx1 + 1, wz1 + 1, wx2 - 1, wz2 - 1, 2, 4 if L >= 5 else 3,
                   {(wx1 + 1, 9), (wx1 + 1, 8), (wx1 + 1, 10)})
        if L >= 5:
            for z in range(z1 + 4, z2):
                for y in (2, 3, 4):
                    if d.air(x1 + 1, y, z):
                        d.bookshelf(x1 + 1, y, z)
        d.dining(16, 2, 7, 3, "x", "dark_oak", ("n", "s"), sit=False)
        for x in (16, 18):
            d.candle(x, 3, 7, 3) if False else None
        d.lamp(17, 5, 7)
    if L >= 5:                                                    # walled physic garden behind
        gx1, gz1, gx2, gz2 = 3, 13, 15, 18
        d.fill(gx1, 1, gz1, gx2, 1, gz2, "grass_block[snowy=false]")
        for x in range(gx1, gx2 + 1):
            for z in range(gz1, gz2 + 1):
                if x in (gx1, gx2) or z == gz2:
                    d.set(x, 2, z, "stone_brick_wall")
        for x in range(gx1 + 2, gx2 - 1, 2):
            for z in (gz1 + 1, gz1 + 3):
                d.set(x, 2, z, ["lilac[half=lower]", "peony[half=lower]", "rose_bush[half=lower]"][x % 3])
                d.set(x, 3, z, ["lilac[half=upper]", "peony[half=upper]", "rose_bush[half=upper]"][x % 3])
        d.door(8, 2, z2, "north", "dark_oak")
        d.fill(8, 1, z2 + 1, 8, 1, gz2 - 1, "gravel")
        d.set(9, 2, gz2 - 1, "stone_brick_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]")
        d.set(gx1 + 1, 2, gz2 - 1, "oak_sapling[stage=0]") if False else None
    return d


def en_cascadia(rel, L):
    d = Design("Cascadia", rel, (17, 18, 30), paving="coarse_dirt")
    x1, x2, z1 = 3, 13, 3
    Z2 = {1: 12, 2: 15, 3: 18, 4: 23, 5: 28}[L]
    cs_walls(d, x1, z1, x2, Z2, 2, 4)
    d.fill(x1 + 1, 1, z1 + 1, x2 - 1, 1, Z2 - 1, "spruce_planks")
    ridge = soft(d, d.gable, x1, z1, x2, Z2, 5, "z", "dark_oak_stairs", "dark_oak_slab", "spruce_planks", 1)
    # glazed front gable with log mullions; solid back gable
    for x in range(x1 + 1, x2):
        for y in range(2, ridge):
            if d.get(x, y, z1) in ("minecraft:spruce_planks",) or y <= 4:
                d.set(x, y, z1, LOG("stripped_spruce_log") if x % 3 == 2 else "glass_pane")
    for y in range(2, 5):
        d.set(x1, y, z1, LOG("stripped_spruce_log"))
        d.set(x2, y, z1, LOG("stripped_spruce_log"))
    d.door(8, 2, z1, "south", "spruce")
    for x in range(x1, x2 + 1):
        d.set(x, 5, z1, LOG("spruce_log", "x")) if d.get(x, 5, z1) == "minecraft:glass_pane" else None
    # porch deck
    for x in range(x1, x2 + 1):
        d.set(x, 1, z1 - 1, "spruce_planks")
        d.set(x, 1, z1 - 2, "spruce_planks")
    d.set(x1, 2, z1 - 2, LOG("spruce_log"))
    d.set(x2, 2, z1 - 2, LOG("spruce_log"))
    d.set(x1, 3, z1 - 2, LANT_S)
    d.set(x2, 3, z1 - 2, LANT_S)
    d.sign(8, 2, z1 - 2, "north", ["MOUNTAIN", "LIBRARY"], "spruce") if False else None
    d.set(6, 2, z1 - 1, "spruce_stairs[facing=east,half=bottom,shape=straight,waterlogged=false]")
    d.set(10, 2, z1 - 1, "spruce_stairs[facing=west,half=bottom,shape=straight,waterlogged=false]")
    # inside
    d.hut(x1 + 1, 2, z1 + 1)
    racks = [(x2 - 1, 2, z1 + 1, "west"), (x2 - 1, 2, z1 + 2, "west"), (x1 + 1, 2, z1 + 2, "east"),
             (x2 - 1, 2, z1 + 3, "west"), (x1 + 1, 2, z1 + 3, "east")]
    for x, y, z, f in racks[:d.req["racks"]]:
        d.rack(x, y, z, f)
    cz = Z2 - 3
    ench_ring(d, 8, 2, cz, "north")
    d.rug(7, cz - 1, 9, cz + 1, 2, ("purple_carpet",), "plain") if False else None
    line_walls(d, x1 + 1, z1 + 4, x2 - 1, Z2 - 1, 2, 3,
               {(x, z) for x in range(x1 + 2, x2 - 1) for z in (z1 + 4, Z2 - 1)})
    for z in range(z1 + 6, Z2 - 4, 4):                             # reading desks between the stacks
        d.table(8, 2, z, "spruce", "post")
        d.chair(7, 2, z, "west", "spruce", sit=False)
        d.chair(9, 2, z, "east", "spruce", sit=False)
    if L >= 2:
        d.item(7, 2, z1 + 3, "lectern", "south")
        d.item(9, 2, z1 + 3, "lectern", "south")
    for z in range(z1 + 2, Z2 - 1, 3):
        d.lamp(8, 8, z) if d.air(8, 9, z) or True else None
        d.set(8, 9, z, "chain[axis=y,waterlogged=false]") if d.air(8, 9, z) else None
    d.set(8, 4, Z2, "glass_pane")
    d.set(8, 5, Z2, "glass_pane") if d.get(8, 5, Z2) == "minecraft:spruce_planks" else None
    # stone chimney stove on the east wall at the front
    d.set(x2 + 1, 1, z1 + 5, "cobblestone")
    for y in range(2, ridge - 1):
        d.set(x2 + 1, y, z1 + 5, "mossy_cobblestone" if y % 3 == 0 else "cobblestone")
    if L >= 3:                                                    # moss and ferns along the eaves
        for z in range(z1, Z2 + 1, 2):
            d.set(x1 - 2, 2, z, "fern") if d.bp.inside(x1 - 2, 2, z) else None
            d.set(x2 + 2, 2, z, "fern") if z != z1 + 5 else None
    if L >= 5:
        for z in (Z2 + 1,):
            for x in range(x1, x2 + 1, 2):
                d.set(x, 2, z, "spruce_fence")
    return d


def en_neoterra(rel, L):
    d = Design("Neoterra", rel, (19, 32, 19), paving="smooth_stone")
    x1, z1, x2, z2 = 4, 4, 14, 14
    nf = {1: 1, 2: 2, 3: 2, 4: 3, 5: 4}[L]
    H = 5
    top = 2 + nf * H                                              # roof deck y
    nt_walls(d, x1, z1, x2, z2, 2, top - 1)
    d.fill(x1, 1, z1, x2, 1, z2, "polished_diorite")
    for i in range(1, nf):
        d.fill(x1 + 1, 2 + i * H - 1, z1 + 1, x2 - 1, 2 + i * H - 1, z2 - 1, "light_gray_concrete")
        for x in range(x1, x2 + 1):
            for z in (z1, z2):
                d.set(x, 2 + i * H - 1, z, "purpur_block")
        for z in range(z1, z2 + 1):
            for x in (x1, x2):
                d.set(x, 2 + i * H - 1, z, "purpur_block")
    d.flat(x1, z1, x2, z2, top, "smooth_quartz", "white_concrete", "smooth_quartz_slab")
    # amethyst-tinted window strips up the middle of every face
    for y in range(3, top - 1):
        if (y - 2) % H == H - 1:
            continue
        for c in (8, 10):
            d.set(c, y, z2, "purple_stained_glass_pane")
            d.set(x1, y, c, "purple_stained_glass_pane")
            d.set(x2, y, c, "purple_stained_glass_pane")
            if y > 5:
                d.set(c, y, z1, "purple_stained_glass_pane")
    d.double_door(8, 2, z1, "x", "south", "birch")
    d.door(10, 2, z1, "south", "birch") if False else None
    for x in range(7, 12):
        d.set(x, 5, z1 - 1, SL("smooth_quartz", "top"))
    d.sign(10, 4, z1 - 1, "north", ["", "ARCANUM"], "birch", glow=True, color="magenta")
    # ground floor: enchanting circle
    ench_ring(d, 9, 2, 9, "north")
    d.set(9, 5, 9, "end_rod[facing=down]")
    d.hut(x1 + 1, 2, z1 + 1)
    racks = [(x2 - 1, 2, z1 + 1, "west"), (x1 + 1, 2, z2 - 1, "east"), (x1 + 1, 2, 9, "east"),
             (x2 - 1, 2, 9, "west"), (9, 2, z2 - 1, "north")]
    for x, y, z, f in racks[:d.req["racks"]]:
        d.rack(x, y, z, f)
    d.plant(x1 + 1, 2, z1 + 3, "potted_bamboo")
    for x, z in ((x1 + 2, z1 + 2), (x2 - 2, z1 + 2), (x1 + 2, z2 - 2), (x2 - 2, z2 - 2)):
        d.set(x, 5, z, "sea_lantern")
    # ladder core in the south-east corner
    lx, lz = x2 - 1, z2 - 1
    ladder(d, lx, lz, 2, top - H - 1 if nf > 1 else 2, "west")
    for i in range(1, nf):
        y = 2 + i * H
        line_walls(d, x1 + 1, z1 + 1, x2 - 1, z2 - 1, y, 3, {(lx, lz), (lx - 1, lz), (lx, lz - 1)})
        d.set(9, y, 9, "amethyst_block")
        d.set(9, y + 1, 9, "amethyst_cluster[facing=up,waterlogged=false]")
        if i == 1:
            d.item(7, y, 9, "lectern", "east")
            d.item(11, y, 9, "lectern", "west")
        else:
            d.chair(8, y, 7, "north", "birch", sit=False)
            d.chair(10, y, 7, "north", "birch", sit=False)
            d.set(9, y, 7, SL("smooth_quartz", "top"))
        d.rug(7, 7, 11, 11, y, ("magenta_carpet", "purple_carpet"))
        for x, z in ((7, 7), (11, 7), (7, 11), (11, 11)):
            d.set(x, y + 3, z, "sea_lantern")
    # crystal crown on the roof
    for x in range(7, 12):
        for z in range(7, 12):
            if abs(x - 9) + abs(z - 9) <= 2:
                d.set(x, top + 1, z, "amethyst_block")
    d.set(9, top + 2, 9, "budding_amethyst")
    d.set(9, top + 3, 9, "amethyst_cluster[facing=up,waterlogged=false]")
    for x, z in ((x1 + 1, z1 + 1), (x2 - 1, z1 + 1), (x1 + 1, z2 - 1), (x2 - 1, z2 - 1)):
        d.set(x, top + 1, z, ENDROD())
    if L >= 3:                                                    # planters round the tower foot
        for x in range(x1 - 2, x2 + 3):
            for z in (z1 - 2, z2 + 2):
                if x not in (8, 9, 10) or z == z2 + 2:
                    d.set(x, 1, z, "moss_block")
                    if x % 3 == 0:
                        d.set(x, 2, z, "azalea")
    return d


@design("enchanter")
def enchanter(pack, rel, L):
    return {"Hearthwood": en_hearthwood, "Cascadia": en_cascadia, "Neoterra": en_neoterra}[pack](rel, L)


# ================================================================================================ ALCHEMIST
"""
Alchemist
  Hearthwood  Apothecary: narrow gable-fronted shop with leaded shop windows full of potted herbs and a hanging
              sign; shop counter at the front, brewing bench and island behind with herb-drying beams hung with
              roots; L2+ timber-framed drying loft with stores upstairs, L3+ walled herb garden with nether wart
              beds, L4+ a glass lean-to greenhouse, L5 flower boxes.
  Cascadia    Herbalist's cabin: long low log cabin with a deep porch hung with drying racks, a cobble hearth with
              the cauldron over the fire, brewing bench along the back wall; grows along x, L4+ moss-roofed
              potting shed and raised beds, L5 greenhouse.
  Neoterra    Pharmacy lab: white flat-roofed storefront with a glowing green cross, glass counter and a glazed lab
              behind with quartz benches, a fume hood and grow-light planters; L3 wider, L4+ rooftop greenhouse.
"""


def drying_beam(d, x1, x2, z, y, beam):
    """Herb-drying rack: a beam under the ceiling with roots and vines hanging from it."""
    for x in range(x1, x2 + 1):
        d.set(x, y, z, LOG(beam, "x"))
        if d.air(x, y - 1, z):
            d.set(x, y - 1, z, "hanging_roots[waterlogged=false]" if x % 2 else
                  "cave_vines_plant[berries=false]" if False else "hanging_roots[waterlogged=false]")


def al_hearthwood(rel, L):
    d = Design("Hearthwood", rel, (22, 20, 23))
    x1, x2, z1, z2 = 4, 12, 3, 12
    d.box(x1, 2, z1, x2, 5, z2, "calcite", floor="oak_planks")
    hw_frame(d, x1, z1, x2, z2, 2, 5, 2)
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if x in (x1, x2) or z in (z1, z2):
                d.set(x, 1, z, "stone_bricks")
    d.fill(x1, 6, z1, x2, 6, z2, "dark_oak_planks")
    if L == 1:
        soft(d, d.gable, x1, z1, x2, z2, 7, "z", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite", 1)
    else:
        hw_frame(d, x1, z1, x2, z2, 7, 10, 2)
        soft(d, d.gable, x1, z1, x2, z2, 11, "z", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite", 1)
        for x in (6, 10):
            d.window(x, 8, z1, x, 9, z1)
            d.window(x, 8, z2, x, 9, z2)
        d.window(x1, 8, 7, x1, 9, 7)
        d.window(x2, 8, 9, x2, 9, 9)
    # brick chimney on the east side
    for y in range(1, 15 if L > 1 else 12):
        d.set(x2 + 1, y, 9, "bricks")
    # shop front: door + two shop windows with display sills
    d.door(8, 2, z1, "south", "dark_oak")
    for xs in ((5, 6, 7), (9, 10, 11)):
        for x in xs:
            d.window(x, 3, z1, x, 4, z1)
            d.set(x, 2, z1 + 1, SL("dark_oak", "top"))
            d.set(x, 3, z1 + 1, ["potted_fern", "decorated_pot[cracked=false,facing=south,waterlogged=false]",
                                 "potted_allium"][x % 3])
        d.set(xs[0], 2, z1 - 1, TD("dark_oak", "north", "top", "true"))
    for x in (5, 7, 9, 11):
        d.set(x, 2, z1 - 1, "potted_red_tulip" if x % 4 == 1 else "potted_blue_orchid")
    d.sign(10, 5, z1 - 1, "east", ["Apothecary", "Tinctures &", "Remedies"], "dark_oak", hanging=True)
    d.set(11, 5, z1 - 1, "dark_oak_planks")
    d.window(x1, 3, 9, x1, 4, 9)
    d.window(x2, 3, 6, x2, 4, 6)
    d.window(7, 3, z2, 7, 4, z2)
    # shop: counter with a scale (pots) and the hut
    d.hut(x1 + 1, 2, 5)
    for x in range(5, 10):
        d.set(x, 2, 7, SL("dark_oak", "top") if x != 7 else "dark_oak_planks")
    d.set(6, 3, 7, "decorated_pot[cracked=false,facing=north,waterlogged=false]")
    d.set(8, 3, 7, "potted_brown_mushroom")
    d.chair(7, 2, 5, "south", "dark_oak", sit=False) if False else None
    d.set(x2 - 1, 2, 5, "chiseled_bookshelf[facing=west,slot_0_occupied=true,slot_1_occupied=true,"
                        "slot_2_occupied=false,slot_3_occupied=true,slot_4_occupied=true,slot_5_occupied=false]")
    d.lamp(8, 5, 5)
    # workshop: brewing bench, island, cauldron, racks
    d.item(5, 2, 11, "water_cauldron[level=3]")
    for x in range(6, 10):
        d.set(x, 2, 11, "dark_oak_planks")
    stands = [(6, 3, 11), (8, 3, 11), (7, 3, 9), (9, 3, 11), (8, 3, 9)]
    d.set(7, 2, 9, "dark_oak_planks")
    d.set(8, 2, 9, "dark_oak_planks")
    for i, (x, y, z) in enumerate(stands):
        if i < L:
            d.item(x, y, z, "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]")
        else:
            d.set(x, y, z, "potted_crimson_fungus" if i % 2 else "flower_pot")
    racks = [(5, 2, 9, "east"), (5, 2, 10, "east"), (5, 7, 9, "east"), (5, 7, 10, "east"), (5, 7, 11, "east")]
    if L == 1:
        racks = racks[:1]
    nground = 2
    for i, (x, y, z, f) in enumerate(racks[:d.req["racks"]]):
        d.rack(x, y, z, f)
    drying_beam(d, 6, 10, 10, 5, "stripped_dark_oak_log")
    d.lamp(7, 5, 8)
    if L >= 2:
        flight(d, 11, 2, 11, "north", 4, "dark_oak", "dark_oak_planks")
        for z in range(9, 12):
            d.set(10, 7, z, "dark_oak_fence")
        # drying loft upstairs
        drying_beam(d, 6, 9, 5, 10, "stripped_dark_oak_log")
        drying_beam(d, 6, 9, 7, 10, "stripped_dark_oak_log")
        for x in (6, 7, 8):
            d.set(x, 7, 4, "barrel[facing=north,open=false]" if x == 7 else "decorated_pot[cracked=false,facing=south,waterlogged=false]")
        d.set(x2 - 1, 7, 4, "chest[facing=west,type=single,waterlogged=false]")
        d.table(9, 7, 6, "dark_oak")
        d.candle(9, 8, 6, 3) if False else None
        d.chair(9, 7, 7, "south", "dark_oak", sit=False)
        d.lamp(8, 10, 9)
    if L >= 3:                                                    # walled herb garden
        gx1, gz1, gx2, gz2 = 3, 13, 15, 21
        d.fill(gx1, 1, gz1, gx2, 1, gz2, "grass_block[snowy=false]")
        for x in range(gx1, gx2 + 1):
            for z in range(gz1, gz2 + 1):
                if x in (gx1, gx2) or z == gz2:
                    d.set(x, 2, z, "brick_wall")
        d.door(8, 2, z2, "north", "dark_oak")
        for z in range(z2 + 1, gz2):
            d.set(8, 1, z, "gravel")
        for x in list(range(gx1 + 2, 7)) + list(range(10, gx2 - 1)):
            for z in (15, 16, 18, 19):
                if z in (15, 16):
                    d.set(x, 1, z, "soul_sand")
                    d.set(x, 2, z, "nether_wart[age=3]")
                else:
                    d.set(x, 1, z, "farmland[moisture=7]")
                    d.set(x, 2, z, "beetroots[age=3]" if x % 2 else "carrots[age=7]")
        d.set(gx2 - 1, 2, gz1 + 1, "composter[level=4]")
        d.set(gx1 + 1, 2, gz2 - 1, "water_cauldron[level=3]")
    if L >= 4:                                                    # glass lean-to greenhouse on the west
        hx1, hx2 = 0, x1
        for z in range(5, 11):
            d.set(1, 1, z, "stone_bricks")
            d.set(1, 2, z, "stone_bricks")
            d.set(1, 3, z, "glass_pane")
            d.set(2, 4, z, "glass")
            d.set(3, 5, z, "glass")
            d.set(2, 1, z, "farmland[moisture=7]")
            d.set(2, 2, z, ["allium", "azure_bluet", "cornflower", "lily_of_the_valley"][z % 4])
            d.set(3, 1, z, "oak_planks")
        for x in (1, 2, 3):
            for y in range(2, 6 - (3 - x)):
                d.set(x, y, 4, "glass_pane" if x > 1 else "stone_bricks")
                d.set(x, y, 11, "glass_pane" if x > 1 else "stone_bricks")
        d.set(1, 3, 4, "glass_pane")
        d.set(1, 3, 11, "glass_pane")
        d.set(x1, 2, 7, AIR)
        d.set(x1, 3, 7, AIR)
        d.set(x1, 4, 7, "stripped_dark_oak_log[axis=y]") if False else None
    if L >= 5:
        for x in (6, 10):
            d.set(x, 7, z1 - 1, TD("dark_oak", "north", "top", "true"))
        d.set(8, 4, z1 - 1, "lantern[hanging=false,waterlogged=false]") if False else None
        d.wall_torch(7, 4, z1 - 1, "north")
        d.wall_torch(9, 4, z1 - 1, "north")
    return d


def al_cascadia(rel, L):
    d = Design("Cascadia", rel, (26, 16, 21), paving="coarse_dirt")
    x1, z1, z2 = 3, 6, 12
    X2 = {1: 11, 2: 13, 3: 15, 4: 15, 5: 15}[L]
    cs_walls(d, x1, z1, X2, z2, 2, 5)
    d.fill(x1 + 1, 1, z1 + 1, X2 - 1, 1, z2 - 1, "spruce_planks")
    ridge = soft(d, d.gable, x1, z1, X2, z2, 6, "x", "spruce_stairs", "spruce_slab", "spruce_planks", 1)
    d.fill(x1 + 1, 6, z1 + 1, X2 - 1, 6, z2 - 1, "spruce_planks")
    for x in range(x1 - 1, X2 + 2):                               # moss on the eaves
        d.set(x, 5, z2 + 1, "moss_carpet") if False else None
    # porch with drying racks
    for x in range(x1, X2 + 1):
        for z in range(z1 - 3, z1):
            d.set(x, 1, z, "spruce_planks")
        d.set(x, 5, z1 - 3, ST("spruce", "south"))
        d.set(x, 5, z1 - 2, SL("spruce", "top"))
        d.set(x, 5, z1 - 1, SL("spruce", "top"))
    for x in range(x1, X2 + 1, 4):
        for y in range(2, 5):
            d.set(x, y, z1 - 3, LOG("spruce_log"))
    drying_beam(d, x1 + 1, x1 + 3, z1 - 2, 4, "stripped_spruce_log")
    drying_beam(d, X2 - 3, X2 - 1, z1 - 2, 4, "stripped_spruce_log")
    for x in range(x1 + 1, X2):
        if x % 4 and d.air(x, 2, z1 - 3):
            d.set(x, 2, z1 - 3, "spruce_fence")
    door = 7
    d.door(door, 2, z1, "south", "spruce")
    d.set(door, 2, z1 - 3, AIR)
    d.set(door + 1, 2, z1 - 1, "potted_fern")
    d.set(door - 1, 2, z1 - 1, "barrel[facing=up,open=false]") if False else None
    for x in range(x1 + 2, X2 - 1, 4):
        if x != door:
            d.window(x, 3, z1, x + 1 if x + 1 != door else x, 4, z1)
    d.window(x1, 3, 9, x1, 4, 9)
    d.sign(door + 1, 4, z1 - 1, "north", ["HERBS &", "TONICS"], "spruce")
    # hearth with the cauldron over the fire, chimney through the roof
    hx = X2 - 2
    for x in (hx - 1, hx + 1):
        for y in (2, 3, 4):
            d.set(x, y, z2 - 1, "cobblestone")
    d.set(hx, 2, z2 - 1, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    d.item(hx, 3, z2 - 1, "water_cauldron[level=3]")
    d.set(hx, 4, z2 - 1, "cobblestone")
    for y in range(1, ridge + 2):
        d.set(hx, y, z2, "mossy_cobblestone" if y % 3 == 0 else "cobblestone")
    for y in range(5, 7):
        d.set(hx, y, z2 - 1, "cobblestone")
    # brewing bench along the back wall
    d.hut(x1 + 1, 2, z1 + 1)
    for x in range(x1 + 1, hx - 1):
        d.set(x, 2, z2 - 1, SL("spruce", "top"))
    stands = [(x1 + 2, 3, z2 - 1), (x1 + 4, 3, z2 - 1), (x1 + 3, 3, z2 - 1), (x1 + 5, 3, z2 - 1), (x1 + 6, 3, z2 - 1)]
    for i, (x, y, z) in enumerate(stands):
        if i < L:
            d.item(x, y, z, "brewing_stand[has_bottle_0=true,has_bottle_1=true,has_bottle_2=false]")
        elif d.get(x, y - 1, z) != AIR:
            d.set(x, y, z, "flower_pot" if i % 2 else "potted_red_mushroom")
    racks = [(x1 + 1, 2, z1 + 3, "east"), (x1 + 1, 2, z1 + 4, "east"), (x1 + 2, 2, z1 + 1, "south"),
             (x1 + 3, 2, z1 + 1, "south"), (x1 + 1, 2, z1 + 2, "east")]
    for x, y, z, f in racks[:d.req["racks"]]:
        d.rack(x, y, z, f)
    d.table(x1 + 4, 2, z1 + 3, "spruce")
    d.chair(x1 + 5, 2, z1 + 3, "east", "spruce", sit=False)
    drying_beam(d, x1 + 2, X2 - 4, z1 + 3, 5, "stripped_spruce_log")
    d.lamp(X2 - 3, 5, z1 + 2)
    d.rug(X2 - 4, z1 + 2, X2 - 2, z1 + 3, 2, ("green_carpet",), "plain")
    if L >= 4:                                                    # raised beds with mushrooms & berries
        for x in range(4, 14, 3):
            for dx in (0, 1):
                d.set(x + dx, 1, 15, "spruce_planks")
                d.set(x + dx, 2, 15, "podzol")
                d.set(x + dx, 3, 15, "sweet_berry_bush[age=3]" if x % 2 else "fern")
                d.set(x + dx, 1, 17, "spruce_planks")
                d.set(x + dx, 2, 17, "mycelium[snowy=false]")
                d.set(x + dx, 3, 17, "red_mushroom" if dx else "brown_mushroom")
        d.set(3, 2, 18, "composter[level=6]")
    if L >= 5:                                                    # greenhouse on the east end
        gx1, gx2 = X2, 22
        for x in range(gx1, gx2 + 1):
            for z in range(z1, z2 + 1):
                d.set(x, 1, z, "cobblestone" if x in (gx1, gx2) or z in (z1, z2) else "farmland[moisture=7]")
                edge = x in (gx1, gx2) or z in (z1, z2)
                if x == gx1:
                    continue
                if edge:
                    d.set(x, 2, z, LOG("spruce_log") if x == gx2 and z in (z1, z2) else "glass_pane")
                    d.set(x, 3, z, "glass_pane")
                    d.set(x, 4, z, "glass_pane")
                else:
                    d.set(x, 2, z, ["lily_of_the_valley", "allium", "blue_orchid", "oxeye_daisy"][(x + z) % 4]
                          if z != 9 else AIR)
                    if z == 9:
                        d.set(x, 1, z, "spruce_planks")
                d.set(x, 5, z, "glass")
        d.set(X2, 2, 9, AIR)
        d.set(X2, 3, 9, AIR)
    return d


def al_neoterra(rel, L):
    d = Design("Neoterra", rel, (19, 14, 17), paving="smooth_stone")
    x1, z1, z2 = 2, 3, 13
    X2 = 12 if L < 3 else 16
    nt_walls(d, x1, z1, X2, z2, 2, 6)
    d.fill(x1, 1, z1, X2, 1, z2, "polished_diorite")
    d.flat(x1, z1 - 1, X2, z2, 7, "smooth_quartz", "white_concrete", "smooth_quartz_slab")
    for x in range(x1, X2 + 1):
        d.set(x, 7, z1 - 1, "lime_terracotta")
    for x in range(x1 + 1, X2):
        d.window(x, 2, z1, x, 5, z1, "glass_pane")
    d.double_door(6, 2, z1, "x", "south", "birch")
    # glowing green cross sign
    cx, cy = X2 - 2, 9
    for x, y in ((cx, cy - 1), (cx, cy), (cx, cy + 1), (cx - 1, cy), (cx + 1, cy)):
        d.set(x, y, z1 - 1, "lime_concrete")
    d.set(cx, cy, z1 - 1, "verdant_froglight[axis=y]")
    d.set(cx, 7, z1 - 1, "white_concrete") if False else None
    d.sign(4, 6, z1 - 1, "north", ["", "PHARMACY"], "birch", glow=True, color="lime")
    # store: glass counter and shelves
    d.hut(x1 + 1, 2, z1 + 1)
    for x in range(x1 + 1, X2):
        if x in (8,):
            continue
        d.set(x, 2, z1 + 4, "smooth_quartz")
        d.set(x, 3, z1 + 4, "light_blue_stained_glass_pane") if x % 2 else None
    for z in range(z1 + 1, z1 + 4):
        d.set(X2 - 1, 2, z, SL("smooth_quartz", "top"))
        d.set(X2 - 1, 3, z, ["potted_allium", "decorated_pot[cracked=false,facing=west,waterlogged=false]",
                             "potted_azure_bluet"][z % 3])
    for x in range(x1 + 2, X2, 3):
        d.set(x, 6, z1 + 2, "sea_lantern")
    # lab behind a glass partition
    for x in range(x1 + 1, X2):
        d.set(x, 2, z1 + 6, "white_concrete" if x != 8 else AIR)
        for y in (3, 4):
            d.set(x, y, z1 + 6, "light_gray_stained_glass_pane" if x != 8 else AIR)
        d.set(x, 5, z1 + 6, "white_concrete")
        d.set(x, 6, z1 + 6, "white_concrete")
    d.door(8, 2, z1 + 6, "north", "birch")
    for x in range(x1 + 1, X2):                                   # quartz bench on the back wall
        d.set(x, 2, z2 - 1, "smooth_quartz")
    stands = [(x1 + 2, 3, z2 - 1), (x1 + 4, 3, z2 - 1), (x1 + 6, 3, z2 - 1), (x1 + 8, 3, z2 - 1),
              (x1 + 3, 3, z2 - 1)]
    for i, (x, y, z) in enumerate(stands):
        if i < L:
            d.item(x, y, z, "brewing_stand[has_bottle_0=true,has_bottle_1=true,has_bottle_2=true]")
    # fume hood over the bench, sink (cauldron)
    for x in range(x1 + 1, x1 + 10):
        d.set(x, 5, z2 - 1, "iron_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
    d.item(X2 - 1, 2, z2 - 1, "water_cauldron[level=3]")
    d.set(X2 - 1, 3, z2, "lever[face=wall,facing=north,powered=false]") if False else None
    racks = [(x1 + 1, 2, z1 + 7, "east"), (x1 + 1, 2, z1 + 8, "east"), (X2 - 1, 2, z1 + 7, "west"),
             (X2 - 1, 2, z1 + 8, "west"), (x1 + 1, 2, z1 + 2, "east")]
    for x, y, z, f in racks[:d.req["racks"]]:
        d.rack(x, y, z, f)
    # grow-light planters
    for x in range(x1 + 3, x1 + 6):
        d.set(x, 2, z1 + 7, "moss_block")
        d.set(x, 3, z1 + 7, ["lily_of_the_valley", "fern", "allium", "blue_orchid"][x % 4])
        d.set(x, 6, z1 + 7, "end_rod[facing=down]")
    for x in range(x1 + 2, X2, 3):
        d.set(x, 6, z2 - 2, "sea_lantern")
    for z in range(z1 + 7, z2, 3):
        d.window(x1, 3, z, x1, 5, z)
        d.window(X2, 3, z, X2, 5, z)
    if L >= 4:                                                    # rooftop greenhouse
        gx1, gz1, gx2, gz2 = x1 + 1, z1 + 3, x1 + 9, z2 - 1
        for x in range(gx1, gx2 + 1):
            for z in range(gz1, gz2 + 1):
                if x in (gx1, gx2) or z in (gz1, gz2):
                    for y in (8, 9, 10):
                        d.set(x, y, z, "glass_pane" if not (x in (gx1, gx2) and z in (gz1, gz2)) else "white_concrete")
                elif z != (gz1 + gz2) // 2:
                    d.set(x, 8, z, ["allium", "azure_bluet", "cornflower", "lily_of_the_valley"][(x + z) % 4])
                    d.set(x, 7, z, "moss_block")
        d.fill(gx1, 11, gz1, gx2, 11, gz2, "glass")
        d.door(gx2, 8, (gz1 + gz2) // 2, "east", "birch")
        ladder(d, X2 + 1, z2 - 2, 2, 7, "east")
        d.set(X2, 8, z2 - 2, AIR)
        d.set(X2, 9, z2 - 2, AIR)
    return d


@design("alchemist")
def alchemist(pack, rel, L):
    return {"Hearthwood": al_hearthwood, "Cascadia": al_cascadia, "Neoterra": al_neoterra}[pack](rel, L)


# ================================================================================================ GRAVEYARD
"""
Graveyard
  Hearthwood  Village churchyard: mossy stone wall with a roofed oak lychgate on the street, gravel path to a
              small stone chapel (pews, altar, vestry rack) at the back, rows of headstones either side; L3+
              bell-cote, L4+ yew trees, L5 lanterns along the path.
  Cascadia    Pioneer cemetery: split-rail fence with a log gate arch, caretaker's log chapel with a porch bench
              on the west, graves in a grid among tall spruces on the east, lanterns on posts.
  Neoterra    Memorial park: low concrete-and-glass columbarium pavilion with benches facing a reflecting pool,
              graves in a neat lawn grid on smooth paths, birch trees and lit bollards.
"""
NAMES_G = ["Ada Fletcher", "Tom Mason", "Mary Cooper", "Will Baker", "Ann Smith", "John Miller", "Rose Thatcher",
           "Hugh Carter", "Ellen Shepherd", "Sam Fisher", "Jane Turner", "Ned Woods", "Lucy Weaver",
           "Owen Potter", "Grace Brewer", "Alf Tanner", "Ivy Chandler", "Ben Cartwright", "Meg Glover",
           "Walt Sawyer", "Iris Wright", "Jack Dyer", "Nell Hayward", "Rob Archer"]


def graves(d, slots, n, facing):
    for i, (x, y, z) in enumerate(slots[:n]):
        d.grave(x, y, z, facing, NAMES_G[i % len(NAMES_G)])


def tree(d, x, y, z, log, leaves, h, r=2, cone=False):
    for k in range(h):
        d.set(x, y + k, z, LOG(log))
    for k in range(r + 2):
        yy = y + h - 2 + k
        rr = max(0, r - k) if cone else (r if k < 2 else 1 if k == 2 else 0)
        for dx in range(-rr, rr + 1):
            for dz in range(-rr, rr + 1):
                if abs(dx) + abs(dz) > rr + (0 if cone else 1):
                    continue
                if d.bp.inside(x + dx, yy, z + dz) and d.air(x + dx, yy, z + dz):
                    d.set(x + dx, yy, z + dz, f"{leaves}[distance=1,persistent=true,waterlogged=false]")
    if d.air(x, y + h, z):
        d.set(x, y + h, z, f"{leaves}[distance=1,persistent=true,waterlogged=false]")


def gy_hearthwood(rel, L):
    d = Design("Hearthwood", rel, (25, 20, 28))
    d.fill(1, 1, 1, 23, 1, 26, "grass_block[snowy=false]")
    # wall
    for x in range(1, 24):
        for z in range(1, 27):
            if x in (1, 23) or z in (1, 26):
                d.set(x, 2, z, "mossy_stone_brick_wall" if (x + z) % 3 == 0 else "stone_brick_wall")
    # lychgate
    gx = 12
    for x in range(gx - 1, gx + 2):
        d.set(x, 2, 1, AIR)
    for x in (gx - 2, gx + 2):
        for z in (0, 2):
            for y in range(2, 5):
                d.set(x, y, z, LOG("stripped_oak_log"))
    for x in range(gx - 3, gx + 4):
        d.set(x, 5, 0, ST("deepslate_tile", "south"))
        d.set(x, 6, 1, SL("deepslate_tile"))
        d.set(x, 5, 1, "oak_planks")
        d.set(x, 5, 2, ST("deepslate_tile", "north"))
    for z in (0, 2):
        d.set(gx - 2, 5, z, "oak_planks")
        d.set(gx + 2, 5, z, "oak_planks")
    d.set(gx - 1, 4, 1, LANT)
    d.set(gx + 1, 4, 1, LANT)
    d.chair(gx - 2, 2, 1, "west", "oak", sit=False)
    d.chair(gx + 2, 2, 1, "east", "oak", sit=False)
    for z in range(0, 19):
        for x in (gx - 1, gx, gx + 1):
            d.set(x, 1, z, "gravel")
    # chapel
    cx1, cz1, cx2, cz2 = 8, 18, 16, 25
    d.box(cx1, 2, cz1, cx2, 5, cz2, "stone_bricks", floor="stone_bricks")
    for x in range(cx1, cx2 + 1):
        for z in range(cz1, cz2 + 1):
            if (x in (cx1, cx2) or z in (cz1, cz2)) and (x * 3 + z) % 5 == 0:
                d.set(x, 2 + (x + z) % 4, z, "mossy_stone_bricks")
    soft(d, d.gable, cx1, cz1, cx2, cz2, 6, "z", "deepslate_tile_stairs", "deepslate_tile_slab", "stone_bricks", 1)
    d.door(gx, 2, cz1, "south", "oak")
    d.set(gx, 4, cz1, "chiseled_stone_bricks")
    d.set(gx, 8, cz1, "glass_pane")
    d.set(gx, 9, cz1, "glass_pane")
    for z in (20, 23):
        d.window(cx1, 3, z, cx1, 5, z)
        d.window(cx2, 3, z, cx2, 5, z)
    d.window(gx, 4, cz2, gx, 6, cz2, "red_stained_glass_pane")
    # altar, pews, vestry rack
    d.set(gx - 1, 2, cz2 - 1, "chiseled_stone_bricks")
    d.set(gx, 2, cz2 - 1, "chiseled_stone_bricks")
    d.set(gx + 1, 2, cz2 - 1, "chiseled_stone_bricks")
    d.candle(gx - 1, 3, cz2 - 1, 3)
    d.candle(gx + 1, 3, cz2 - 1, 3)
    d.set(gx, 3, cz2 - 1, "white_banner") if False else None
    d.rug(gx, cz1 + 1, gx, cz2 - 2, 2, ("red_carpet",), "plain")
    for z in (cz1 + 2, cz1 + 4):
        for x in (cx1 + 1, cx1 + 2, cx2 - 2, cx2 - 1):
            d.chair(x, 2, z, "north", "oak", sit=(z == cz1 + 2 and x in (cx1 + 2, cx2 - 2)))
    d.rack(cx1 + 1, 2, cz2 - 1, "east")
    d.hut(cx2 - 1, 2, cz2 - 1)
    for z in (cz1 + 2, cz2 - 2):
        d.set(gx, 5, z, LANT)
    # graves either side of the path
    slots = []
    for z in (5, 8, 11, 14):
        for x in (10, 14, 8, 16, 6, 18, 4, 20):
            slots.append((x, 2, z))
    graves(d, slots, d.req["yard"]["minecolonies:blockminecoloniesnamedgrave"], "north")
    for x, y, z in slots[:d.req["yard"]["minecolonies:blockminecoloniesnamedgrave"]]:
        if (x + z) % 3 == 0:
            d.set(x, 2, z + 1, "poppy")
        elif (x + z) % 3 == 1:
            d.set(x, 2, z + 1, "oxeye_daisy")
    if L >= 3:                                                    # bell-cote on the front gable
        for y in range(10, 13):
            d.set(gx - 1, y, cz1, "stone_bricks")
            d.set(gx + 1, y, cz1, "stone_bricks")
        d.set(gx, 12, cz1, "bell[attachment=ceiling,facing=north,powered=false]")
        d.set(gx, 13, cz1, "stone_brick_slab[type=bottom,waterlogged=false]")
        d.set(gx - 1, 13, cz1, "stone_brick_slab[type=bottom,waterlogged=false]")
        d.set(gx + 1, 13, cz1, "stone_brick_slab[type=bottom,waterlogged=false]")
    if L >= 4:                                                    # yews
        tree(d, 4, 2, 22, "dark_oak_log", "spruce_leaves", 4, 2)
        tree(d, 20, 2, 22, "dark_oak_log", "spruce_leaves", 4, 2)
    if L >= 5:
        for z in (4, 10, 16):
            for x in (gx - 2, gx + 2):
                d.set(x, 2, z, "stone_brick_wall")
                d.set(x, 3, z, LANT_S)
        d.chair(3, 2, 17, "east", "oak", sit=False)
        d.chair(21, 2, 17, "west", "oak", sit=False)
    return d


def gy_cascadia(rel, L):
    d = Design("Cascadia", rel, (29, 22, 23), paving="coarse_dirt")
    d.fill(1, 1, 1, 27, 1, 21, "grass_block[snowy=false]")
    for x in range(1, 28):
        for z in range(1, 22):
            if (x * 7 + z * 5) % 11 == 0:
                d.set(x, 1, z, "podzol[snowy=false]")
            if x in (1, 27) or z in (1, 21):
                d.set(x, 2, z, LOG("spruce_log") if (x + z) % 4 == 0 else "spruce_fence")
    # log gate arch
    gx = 16
    for x in range(gx - 1, gx + 2):
        d.set(x, 2, 1, AIR)
    for x in (gx - 2, gx + 2):
        for y in range(2, 7):
            d.set(x, y, 1, LOG("spruce_log"))
    for x in range(gx - 3, gx + 4):
        d.set(x, 7, 1, LOG("stripped_spruce_log", "x"))
    d.sign(gx, 6, 0, "north", ["PINE HILL", "CEMETERY"], "spruce")
    d.sign(gx, 6, 2, "south", ["REST IN", "PEACE"], "spruce")
    for z in range(0, 21):
        d.set(gx, 1, z, "coarse_dirt")
    # caretaker's chapel (log) on the west
    x1, z1, x2, z2 = 3, 6, 10, 13
    cs_walls(d, x1, z1, x2, z2, 2, 5)
    d.fill(x1 + 1, 1, z1 + 1, x2 - 1, 1, z2 - 1, "spruce_planks")
    soft(d, d.gable, x1, z1, x2, z2, 6, "z", "dark_oak_stairs", "dark_oak_slab", "spruce_planks", 1)
    for y in range(9, 12):
        d.set(6, y, z1 - 1, "spruce_fence" if y < 11 else "spruce_fence")
    d.set(7, 9, z1 - 1, "spruce_fence")
    d.set(5, 9, z1 - 1, "spruce_fence")
    d.door(6, 2, z1, "south", "spruce")
    d.window(8, 3, z1, 8, 4, z1)
    d.window(x2, 3, 9, x2, 4, 10)
    d.window(6, 3, z2, 7, 4, z2, "yellow_stained_glass_pane")
    # porch with bench
    for x in range(x1, x2 + 1):
        for z in (z1 - 2, z1 - 1):
            d.set(x, 1, z, "spruce_planks")
        d.set(x, 5, z1 - 2, ST("spruce", "south"))
        d.set(x, 5, z1 - 1, SL("spruce", "top"))
    for x in (x1, x2):
        for y in range(2, 5):
            d.set(x, y, z1 - 2, LOG("spruce_log"))
    d.chair(x1 + 1, 2, z1 - 1, "south", "spruce", sit=True)
    d.chair(x1 + 2, 2, z1 - 1, "south", "spruce", sit=True)
    d.lamp(6, 4, z1 - 1)
    for z in range(z1 - 1, 1, -1):
        d.set(6, 1, z, "coarse_dirt")
    for x in range(7, gx):
        d.set(x, 1, 3, "coarse_dirt")
    # inside: altar table, benches, rack
    d.set(6, 2, z2 - 1, "spruce_planks")
    d.set(7, 2, z2 - 1, "spruce_planks")
    d.candle(6, 3, z2 - 1, 2)
    d.candle(7, 3, z2 - 1, 1)
    for z in (z1 + 2, z1 + 4):
        d.chair(4, 2, z, "north", "spruce", sit=False)
        d.chair(5, 2, z, "north", "spruce", sit=False)
        d.chair(8, 2, z, "north", "spruce", sit=False)
        d.chair(9, 2, z, "north", "spruce", sit=False)
    d.rack(x2 - 1, 2, z1 + 1, "west")
    d.hut(x1 + 1, 2, z1 + 1)
    d.lamp(6, 5, 9)
    # graves in a grid on the east
    slots = []
    for z in (5, 8, 11, 14, 17):
        for x in (14, 18, 12, 20, 22, 24):
            slots.append((x, 2, z))
    n = d.req["yard"]["minecolonies:blockminecoloniesnamedgrave"]
    graves(d, slots, n, "north")
    for x, y, z in slots[:n]:
        if (x + z) % 2:
            d.set(x, 2, z + 1, "fern" if x % 4 else "lily_of_the_valley")
    for z in range(4, 20):
        d.set(gx, 1, z, "coarse_dirt")
    trees = [(25, 4), (4, 18), (9, 19), (25, 19), (12, 19), (19, 19)]
    for i, (x, z) in enumerate(trees[:1 + L]):
        tree(d, x, 2, z, "spruce_log", "spruce_leaves", 6 + i % 2, 2, cone=True)
    for z in (4, 10, 16):
        d.set(gx - 1, 2, z, "spruce_fence")
        d.set(gx - 1, 3, z, LANT_S)
    return d


def gy_neoterra(rel, L):
    d = Design("Neoterra", rel, (23, 14, 25), paving="smooth_stone")
    d.fill(1, 1, 1, 21, 1, 23, "grass_block[snowy=false]")
    for x in range(1, 22):
        for z in range(1, 24):
            if x in (1, 21) or z in (1, 23):
                d.set(x, 1, z, "smooth_stone")
                if not (z == 1 and 9 <= x <= 13):
                    d.set(x, 2, z, "white_concrete" if z == 1 else "birch_leaves[distance=1,persistent=true,waterlogged=false]")
    d.sign(8, 2, 0, "north", ["", "MEMORIAL", "GARDENS"], "birch", glow=True, color="light_gray") if False else None
    for x in (8, 14):
        d.set(x, 2, 1, "light_gray_concrete")
        d.set(x, 3, 1, "light_gray_concrete")
        d.set(x, 4, 1, "sea_lantern")
    d.sign(8, 3, 0, "north", ["MEMORIAL", "GARDENS"], "birch", glow=True, color="white")
    # central path and cross paths
    for z in range(0, 24):
        d.set(11, 1, z, "smooth_stone")
        d.set(10, 1, z, "polished_diorite")
        d.set(12, 1, z, "polished_diorite")
    # pavilion with columbarium wall at the back
    px1, pz1, px2, pz2 = 4, 16, 18, 22
    d.fill(px1, 1, pz1, px2, 1, pz2, "polished_diorite")
    for x in range(px1, px2 + 1):
        for y in range(2, 6):
            d.set(x, y, pz2, "light_gray_concrete" if (x + y) % 2 else "smooth_quartz")
    for z in range(pz1, pz2 + 1):
        for x in (px1, px2):
            for y in range(2, 6):
                d.set(x, y, z, "white_concrete" if z in (pz1, pz2) else "light_gray_stained_glass_pane")
    d.fill(px1 - 1, 6, pz1 - 1, px2 + 1, 6, pz2, "smooth_quartz")
    for x in range(px1 - 1, px2 + 2):
        d.set(x, 6, pz1 - 1, "smooth_quartz_slab[type=bottom,waterlogged=false]")
    for x in range(px1 + 2, px2 - 1, 3):
        d.set(x, 5, 19, "sea_lantern") if False else None
    d.fill(px1 + 1, 5, pz1 + 2, px2 - 1, 5, pz1 + 2, "sea_lantern") if False else None
    for x in range(px1 + 2, px2 - 1, 4):
        d.set(x, 5, pz1 + 3, "end_rod[facing=down]")
    # reflecting pool and benches
    for x in range(7, 16):
        for z in (pz1 + 1, pz1 + 2):
            if x not in (10, 11, 12):
                d.set(x, 1, z, "water[level=0]")
    d.chair(9, 2, pz1 + 4, "south", "birch", sit=True)
    d.chair(13, 2, pz1 + 4, "south", "birch", sit=True)
    d.chair(8, 2, pz1 + 4, "south", "birch", sit=False)
    d.chair(14, 2, pz1 + 4, "south", "birch", sit=False)
    d.set(11, 2, pz2 - 1, "smooth_quartz")
    d.set(11, 3, pz2 - 1, "white_candle[candles=3,lit=false,waterlogged=false]")
    d.set(10, 2, pz2 - 1, "potted_white_tulip")
    d.set(12, 2, pz2 - 1, "potted_lily_of_the_valley")
    d.rack(px1 + 1, 2, pz2 - 1, "east")
    d.hut(px2 - 1, 2, pz2 - 1)
    # graves on the lawns
    slots = []
    for z in (4, 7, 10, 13):
        for x in (8, 14, 6, 16, 4, 18):
            slots.append((x, 2, z))
    n = d.req["yard"]["minecolonies:blockminecoloniesnamedgrave"]
    graves(d, slots, n, "north")
    for z in (5, 8, 11, 14):
        for x in range(3, 20):
            if x not in (10, 11, 12):
                d.set(x, 1, z, "smooth_stone_slab[type=double,waterlogged=false]" if False else "smooth_stone")
    for i, (x, z) in enumerate([(3, 3), (19, 3), (3, 15), (19, 15), (3, 9), (19, 9)][:1 + L]):
        tree(d, x, 2, z, "birch_log", "birch_leaves", 4, 1)
    for z in (4, 9, 14):
        for x in (9, 13):
            d.set(x, 2, z, "end_rod[facing=up]") if False else None
            d.set(x, 2, z, "white_concrete") if False else None
    for z in (3, 9, 15):
        d.set(9, 2, z, "white_concrete_powder") if False else None
        d.set(9, 2, z, "end_rod[facing=up]")
        d.set(13, 2, z, "end_rod[facing=up]")
    return d


@design("graveyard")
def graveyard(pack, rel, L):
    return {"Hearthwood": gy_hearthwood, "Cascadia": gy_cascadia, "Neoterra": gy_neoterra}[pack](rel, L)


# ================================================================================================ MYSTICAL SITE
"""
Mystical site
  Hearthwood  Stone circle on a village green: a ring of standing stones round an altar stone with candles,
              eight benches facing in, a holy well (L2+), lintels turning the stones into trilithons (L3+),
              a hawthorn and flower meadow (L4+), lanterns (L5).
  Cascadia    Sacred spring: a mossy rock outcrop with a waterfall into a pool, an open log pavilion with a
              hip roof beside it, log benches round a fire pit, cairns and spruces that multiply with level.
  Neoterra    Crystal plaza: a round quartz plaza with an amethyst crystal on a plinth in a ring of water,
              white pylons with light rods, benches facing the crystal, a floating canopy ring (L3+).
"""


def ms_hearthwood(rel, L):
    d = Design("Hearthwood", rel, (23, 12, 23))
    c = 11
    for x in range(1, 22):
        for z in range(1, 22):
            r = ((x - c) ** 2 + (z - c) ** 2) ** 0.5
            d.set(x, 1, z, "grass_block[snowy=false]" if r > 2.5 else "moss_block")
    for z in range(0, 5):
        d.set(c, 1, z, "gravel")
    stones = []
    import math
    n = 12
    for i in range(n):
        a = 2 * math.pi * i / n
        x = round(c + 7 * math.sin(a))
        z = round(c - 7 * math.cos(a))
        stones.append((x, z))
    for i, (x, z) in enumerate(stones):
        if i == 0:
            continue                                              # entrance gap on the street side
        h = 3 + (i % 2)
        for y in range(2, 2 + h):
            d.set(x, y, z, ["stone", "andesite", "mossy_cobblestone", "cobblestone"][(i + y) % 4]
                  if y < 2 + h - 1 else "stone")
    if L >= 3:                                                    # lintels on pairs
        for i in range(1, n - 1, 2):
            (ax, az), (bx, bz) = stones[i], stones[i + 1]
            for x, z in ((ax, az), (bx, bz)):
                for y in range(2, 6):
                    d.set(x, y, z, "stone" if y != 3 else "mossy_cobblestone")
            steps = max(abs(bx - ax), abs(bz - az))
            for k in range(steps + 1):
                d.set(round(ax + (bx - ax) * k / steps), 6, round(az + (bz - az) * k / steps), "stone")
    # altar
    d.set(c, 2, c, "chiseled_stone_bricks")
    d.set(c - 1, 2, c, "stone_brick_slab[type=top,waterlogged=false]")
    d.set(c + 1, 2, c, "stone_brick_slab[type=top,waterlogged=false]")
    d.candle(c - 1, 3, c, 3)
    d.candle(c + 1, 3, c, 2)
    d.set(c, 3, c, "potted_flowering_azalea_bush")
    d.hut(c, 2, c + 2)
    # benches facing in
    for x, z, back in ((c - 3, c - 3, "north"), (c + 3, c - 3, "north"), (c - 3, c + 3, "south"),
                       (c + 3, c + 3, "south")):
        d.chair(x, 2, z, back, "oak")
        d.chair(x + (1 if x < c else -1), 2, z, back, "oak")
    if L >= 2:                                                    # holy well
        wx, wz = 18, 18
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                d.set(wx + dx, 2, wz + dz, "stone_bricks" if (dx, dz) != (0, 0) else "water[level=0]")
        d.set(wx, 1, wz, "water[level=0]")
        for dx, dz in ((-1, -1), (1, 1)):
            for y in (3, 4):
                d.set(wx + dx, y, wz + dz, "oak_fence")
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                d.set(wx + dx, 5, wz + dz, SL("dark_oak"))
        d.set(wx, 4, wz, "chain[axis=y,waterlogged=false]")
    if L >= 4:
        tree(d, 4, 2, 4, "oak_log", "flowering_azalea_leaves", 3, 2)
        tree(d, 18, 2, 4, "oak_log", "flowering_azalea_leaves", 3, 2)
        for x, z in ((3, 16), (5, 19), (7, 20), (15, 3), (2, 10), (20, 11)):
            d.set(x, 2, z, "cornflower" if x % 2 else "poppy")
    if L >= 5:
        for x, z in ((c - 1, 2), (c + 1, 2)):
            d.set(x, 2, z, "oak_fence")
            d.set(x, 3, z, LANT_S)
    return d


def ms_cascadia(rel, L):
    d = Design("Cascadia", rel, (25, 16, 25), paving="coarse_dirt")
    for x in range(1, 24):
        for z in range(1, 24):
            d.set(x, 1, z, "podzol[snowy=false]" if (x * 5 + z * 3) % 7 == 0 else "grass_block[snowy=false]")
    for z in range(0, 9):
        d.set(12, 1, z, "coarse_dirt")
        d.set(11, 1, z, "coarse_dirt")
    # rock outcrop with waterfall into a pool (south)
    for x in range(6, 19):
        for z in range(18, 24):
            hgt = 6 - abs(x - 12) // 2 - (23 - z) // 2
            for y in range(2, 2 + max(1, hgt)):
                d.set(x, y, z, "mossy_cobblestone" if (x + y + z) % 3 == 0 else
                      ("tuff" if (x + z) % 4 == 0 else "andesite"))
            d.set(x, 2 + max(1, hgt), z, "moss_block")
    for x in range(9, 16):
        for z in range(13, 18):
            if abs(x - 12) + abs(z - 15) <= 4:
                d.set(x, 1, z, "water[level=0]")
                d.set(x, 0, z, "gravel") if False else None
    for y in range(2, 6):
        d.set(12, y, 18, "water[level=0]")
    d.set(12, 6, 18, "water[level=0]")
    for x in (11, 13):
        d.set(x, 1, 13, "mossy_cobblestone")
    # fire pit and log benches (8 seats)
    fx, fz = 12, 9
    d.set(fx, 1, fz, "cobblestone")
    d.set(fx, 2, fz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for x, z, back in ((fx - 3, fz, "west"), (fx + 3, fz, "east")):
        for dz in (-1, 0, 1):
            d.chair(x, 2, z + dz, back, "spruce")
    d.chair(fx - 1, 2, fz - 3, "north", "spruce")
    d.chair(fx + 1, 2, fz - 3, "north", "spruce")
    d.hut(fx, 2, fz - 3)
    # open log pavilion (east)
    px1, pz1, px2, pz2 = 17, 5, 21, 11
    for x in range(px1, px2 + 1):
        for z in range(pz1, pz2 + 1):
            d.set(x, 1, z, "spruce_planks")
    for x, z in ((px1, pz1), (px2, pz1), (px1, pz2), (px2, pz2), (px1, 8), (px2, 8)):
        d.set(x, 1, z, "cobblestone")
        for y in range(2, 5):
            d.set(x, y, z, LOG("spruce_log"))
    for x in range(px1, px2 + 1):
        for z in (pz1, pz2):
            d.set(x, 5, z, LOG("stripped_spruce_log", "x"))
    for z in range(pz1, pz2 + 1):
        for x in (px1, px2):
            d.set(x, 5, z, LOG("stripped_spruce_log", "z"))
    soft(d, d.hip, px1, pz1, px2, pz2, 6, "dark_oak_stairs", "dark_oak_slab", 1)
    d.set(19, 5, 8, LANT)
    d.set(19, 2, 10, "spruce_planks")
    d.candle(19, 3, 10, 4)
    d.set(19, 2, 6, "decorated_pot[cracked=false,facing=north,waterlogged=false]")
    # cairns
    cairns = [(4, 5), (4, 13), (20, 15), (7, 16), (3, 9)]
    for i, (x, z) in enumerate(cairns[:L]):
        d.set(x, 2, z, "cobblestone")
        d.set(x, 3, z, "mossy_cobblestone")
        d.set(x, 4, z, "cobblestone_wall")
    trees = [(2, 20), (22, 20), (2, 2), (22, 2), (6, 22), (18, 22)]
    for i, (x, z) in enumerate(trees[:1 + L]):
        tree(d, x, 2, z, "spruce_log", "spruce_leaves", 6, 2, cone=True)
    return d


def ms_neoterra(rel, L):
    d = Design("Neoterra", rel, (21, 14, 21), paving="smooth_stone")
    c = 10
    for x in range(0, 21):
        for z in range(0, 21):
            r = ((x - c) ** 2 + (z - c) ** 2) ** 0.5
            if r <= 9.3:
                d.set(x, 1, z, "smooth_quartz" if r > 3.5 else "polished_diorite")
                if 2.0 <= r < 3.0:
                    d.set(x, 1, z, "water[level=0]")
                if 8.5 <= r <= 9.3 and z > 2:
                    d.set(x, 1, z, "moss_block")
                    if (x + z) % 3 == 0:
                        d.set(x, 2, z, "azalea")
            else:
                d.set(x, 1, z, "grass_block[snowy=false]")
    # crystal plinth
    d.set(c, 2, c, "smooth_quartz")
    d.set(c, 3, c, "amethyst_block")
    d.set(c, 4, c, "budding_amethyst")
    d.set(c, 5, c, "amethyst_cluster[facing=up,waterlogged=false]")
    for dx, dz, f in ((1, 0, "east"), (-1, 0, "west"), (0, 1, "south"), (0, -1, "north")):
        d.set(c + dx, 2, c + dz, "amethyst_block")
        d.set(c + dx, 3, c + dz, f"amethyst_cluster[facing=up,waterlogged=false]")
    # pylons
    import math
    for i in range(8):
        a = 2 * math.pi * (i + 0.5) / 8
        x = round(c + 7 * math.sin(a))
        z = round(c - 7 * math.cos(a))
        for y in range(2, 5):
            d.set(x, y, z, "white_concrete" if y < 4 else "sea_lantern")
        d.set(x, 5, z, ENDROD())
    # benches facing the crystal (8 seats)
    for x, z, back in ((c - 5, c - 1, "west"), (c - 5, c + 1, "west"), (c + 5, c - 1, "east"), (c + 5, c + 1, "east"),
                       (c - 1, c + 5, "south"), (c + 1, c + 5, "south"), (c - 2, c + 5, "south"), (c + 2, c + 5, "south")):
        d.chair(x, 2, z, back, "birch")
    d.hut(c, 2, c - 5)
    if L >= 2:
        for x, z in ((c - 5, c), (c + 5, c), (c, c + 5)):
            d.set(x, 2, z, SL("smooth_quartz", "top"))
    if L >= 3:                                                    # floating canopy ring on the pylons
        for x in range(0, 21):
            for z in range(0, 21):
                r = ((x - c) ** 2 + (z - c) ** 2) ** 0.5
                if 6.5 <= r < 8.0 and d.air(x, 6, z):
                    d.set(x, 6, z, "white_stained_glass" if (x + z) % 2 else "smooth_quartz_slab[type=bottom,waterlogged=false]")
    if L >= 4:
        for x, z in ((c, c - 3), (c, c + 3), (c - 3, c), (c + 3, c)):
            d.set(x, 1, z, "sea_lantern")
    if L >= 5:
        for y in range(6, 9):
            d.set(c, y, c, "end_rod[facing=up]") if False else None
        d.set(c, 6, c, "end_rod[facing=up]")
    return d


@design("mysticalsite")
def mysticalsite(pack, rel, L):
    return {"Hearthwood": ms_hearthwood, "Cascadia": ms_cascadia, "Neoterra": ms_neoterra}[pack](rel, L)
