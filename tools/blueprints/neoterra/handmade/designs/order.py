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
