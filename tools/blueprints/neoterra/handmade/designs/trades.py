"""
Trades group: builder, sawmill, lumberjack, fletcher, warehouse, deliveryman, composter.

See the per-type docstrings below for what each building is in each pack.
"""
from hm import Design, design, AIR, D4, OPP, CW


# =============================================================================================== small helpers
def st(m, facing, half="bottom", shape="straight"):
    """Stairs state for material m ("spruce", "deepslate_tile", "smooth_quartz" ...)."""
    return f"{m}_stairs[facing={facing},half={half},shape={shape},waterlogged=false]"


def sl(m, t="bottom"):
    return f"{m}_slab[type={t},waterlogged=false]"


def tr(m, facing, half="top", open_=False):
    return f"{m}_trapdoor[facing={facing},half={half},open={'true' if open_ else 'false'},powered=false,waterlogged=false]"


def lg(m, axis="y"):
    return f"{m}[axis={axis}]"


LANT = "lantern[hanging=true,waterlogged=false]"
LANT_S = "lantern[hanging=false,waterlogged=false]"
SLANT = "soul_lantern[hanging=true,waterlogged=false]"


def rack_col(d, x, z, y, h=3, facing="north"):
    for k in range(h):
        d.rack(x, y + k, z, facing)
    return h


def rack_line(d, cells, y, need, h=3, facing="north"):
    """Rack columns on the given (x, z) cells until `need` racks are placed. Returns racks placed."""
    n = 0
    for x, z in cells:
        if n >= need:
            break
        n += rack_col(d, x, z, y, h, facing)
    return n


def aisles(d, x1, z1, x2, z2, y, need, h=3, along="z", lamp_y=None, lamp=LANT):
    """Shelving: double rows of rack columns running `along`, separated by 1-wide walkways (walkway first).
    Fills row pair by row pair until `need` racks are placed; returns racks placed."""
    n = 0
    if along == "z":
        across, length = range(x1, x2 + 1), range(z1, z2 + 1)
    else:
        across, length = range(z1, z2 + 1), range(x1, x2 + 1)
    across = list(across)
    rows = [a for i, a in enumerate(across) if i % 3 != 0]
    walk = [a for i, a in enumerate(across) if i % 3 == 0]
    for a in rows:
        if n >= need:
            break
        for b in length:
            x, z = (a, b) if along == "z" else (b, a)
            n += rack_col(d, x, z, y, h, "north" if along == "z" else "west")
    if lamp_y:
        for a in walk:
            for b in list(length)[1::4]:
                x, z = (a, b) if along == "z" else (b, a)
                if d.air(x, lamp_y, z) and not d.air(x, lamp_y + 1, z):
                    d.set(x, lamp_y, z, lamp)
    return n


def run_stairs(d, x, z, y, steps, direction, m, fill=None):
    """Straight flight: first stair block at (x, y, z), rising one per cell toward `direction`.
    Supports filled below, 3 cells cleared above every step (cuts the stair hole in the floor above).
    Returns the (x, z) of the landing cell (first cell after the flight, at floor height y+steps)."""
    dx, dz = D4[direction]
    for i in range(steps):
        cx, cz = x + dx * i, z + dz * i
        yy = y + i
        d.set(cx, yy, cz, st(m, direction))
        if fill:
            for k in range(y, yy):
                d.set(cx, k, cz, fill)
        for k in range(1, 4):
            d.set(cx, yy + k, cz, AIR)
    return x + dx * steps, z + dz * steps


def ladder(d, x, z, y1, y2, facing):
    """Ladder from y1 up to y2 (inclusive; y2 = floor level of the upper storey), air kept above."""
    for y in range(y1, y2 + 1):
        d.set(x, y, z, f"ladder[facing={facing},waterlogged=false]")
    d.set(x, y2 + 1, z, AIR)
    d.set(x, y2 + 2, z, AIR)


def log_pile(d, x1, z1, x2, z2, y, h, wood="spruce_log", axis="x"):
    """Stacked logs lying along `axis`, a stepped pile (top row one shorter)."""
    for k in range(h):
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                inner = (axis == "x" and z1 + k <= z <= z2 - k) or (axis == "z" and x1 + k <= x <= x2 - k)
                if k == 0 or inner:
                    d.set(x, y + k, z, lg(wood, axis))


def pallet(d, x, z, y, block, h=1):
    """Building material on a pallet: a top slab of planks with blocks stacked on it is not possible, so the
    pallet is a spruce slab beside the stack; here simply stacks of the material."""
    for k in range(h):
        d.set(x, y + k, z, block)


def fence_line(d, cells, y, fence):
    for x, z in cells:
        d.set(x, y, z, fence)


def ring(x1, z1, x2, z2):
    out = []
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if x in (x1, x2) or z in (z1, z2):
                out.append((x, z))
    return out


# ------------------------------------------------------------------------------------------------ pack shells
def neo_block(d, x1, z1, x2, z2, y0, ytop, floors=(), wall="white_concrete", floor="polished_diorite",
              pillar="light_gray_concrete", roof="smooth_quartz", parapet=True, band="cyan_terracotta"):
    """Modern box: walls y0..ytop, floor under y0, intermediate floors at `floors` (with a coloured band in the wall),
    flat roof at ytop+1 with a parapet and coping."""
    d.box(x1, y0, z1, x2, ytop, z2, wall, floor=floor)
    for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        d.fill(x, y0, z, x, ytop, z, pillar)
    for yf in floors:
        d.fill(x1 + 1, yf, z1 + 1, x2 - 1, yf, z2 - 1, "smooth_stone")
        if band:
            for x, z in ring(x1, z1, x2, z2):
                d.set(x, yf, z, band)
    if parapet:
        d.flat(x1, z1, x2, z2, ytop + 1, roof, wall, "smooth_quartz_slab")
    else:
        d.fill(x1, ytop + 1, z1, x2, ytop + 1, z2, roof)


def neo_ribbon(d, x1, z1, x2, z2, y1, y2, glass="glass_pane", every=4, skip=()):
    """Ribbon glazing along a wall line (x1==x2 or z1==z2), with a mullion every `every` cells."""
    if z1 == z2:
        for i, x in enumerate(range(x1, x2 + 1)):
            if every and i % every == every - 1 or x in skip:
                continue
            d.window(x, y1, z1, x, y2, z1, glass)
    else:
        for i, z in enumerate(range(z1, z2 + 1)):
            if every and i % every == every - 1 or z in skip:
                continue
            d.window(x1, y1, z, x1, y2, z, glass)


def hw_walls(d, x1, z1, x2, z2, y0, y1, floor="oak_planks", infill="calcite", base="stone_bricks", step=3,
             beam=True):
    """Timber-framed walls y0..y1: plaster infill, dark-oak posts at the corners and every `step`, a stone-brick
    base course at y0 and a sill beam on top."""
    d.box(x1, y0, z1, x2, y1, z2, infill, floor=floor)
    post = lg("stripped_dark_oak_log", "y")
    for x, z in ring(x1, z1, x2, z2):
        corner = x in (x1, x2) and z in (z1, z2)
        if corner or (z in (z1, z2) and (x - x1) % step == 0) or (x in (x1, x2) and (z - z1) % step == 0):
            d.fill(x, y0, z, x, y1, z, post)
        if base:
            d.set(x, y0, z, base)
        if beam:
            d.set(x, y1, z, lg("stripped_dark_oak_log", "x" if z in (z1, z2) else "z"))


def cas_walls(d, x1, z1, x2, z2, y0, y1, floor="spruce_planks", log="stripped_spruce_log", corner="spruce_log",
              plinth=True):
    """Log walls y0..y1 (horizontal logs), light stripped corner posts, river-rock footing under the walls."""
    d.box(x1, y0, z1, x2, y1, z2, log, floor=floor)
    for x, z in ring(x1, z1, x2, z2):
        ax = "x" if z in (z1, z2) else "z"
        for y in range(y0, y1 + 1):
            d.set(x, y, z, lg(log, ax))
        rock = "mossy_cobblestone" if (x * 7 + z * 3) % 4 == 0 else "cobblestone"
        d.set(x, y0 - 1, z, rock)
        if plinth:
            d.set(x, y0, z, rock if (x + z) % 3 else "andesite")
    for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        d.fill(x, y0 + (1 if plinth else 0), z, x, y1, z, lg(corner, "y"))


def win(d, x, y, z, h=2, glass="glass_pane"):
    d.window(x, y, z, x, y + h - 1, z, glass)


def shutters(d, x, y, z, facing, h=2, m="spruce"):
    """Open shutters either side of a window cell in a wall facing `facing` (outside)."""
    ox, oz = D4[facing]
    for side in (CW[facing], OPP[CW[facing]]):
        sx, sz = D4[side]
        for k in range(h):
            if d.air(x + sx + ox, y + k, z + sz + oz):
                d.set(x + sx + ox, y + k, z + sz + oz, tr(m, side, "bottom", True))


# =============================================================================================== BUILDER
"""
Builder
  Neoterra   "Construction office & yard": two-storey glass-fronted office (L1 single storey) with the workshop
             below and a drafting library above; walled materials yard with steel canopy rack aisles, material
             stacks, and from L4 a yellow tower crane.
  Hearthwood "Master builder's yard": timber-framed workshop house (upper drafting floor from L2) and a long
             open-fronted tiled cart shed with rack bays across the back of a walled yard, timber/stone stacks.
  Cascadia   "Timber framers' barn": tall gable-to-street barn with big doors and hay-hoist beam, rack walls along
             both sides, drafting loft; a log lean-to for lumber racks from L4.
"""


def b_items(L):
    return L >= 2


def builder_neo(rel, L):
    d = Design("Neoterra", rel, (27, 20, 19), paving="smooth_stone")
    x1, z1, x2, z2 = 2, 3, 12, 11
    y0 = 2
    two = L >= 2
    ytop = 10 if two else 5
    neo_block(d, x1, z1, x2, z2, y0, ytop, floors=(6,) if two else ())
    # glass street front, side ribbons
    for x in range(x1 + 1, x2):
        d.window(x, 2, z1, x, 4, z1, "glass_pane")
        if two:
            d.window(x, 7, z1, x, 9, z1, "light_gray_stained_glass_pane")
    d.double_door(6, y0, z1, "x", "south", "birch")
    neo_ribbon(d, x1, z1 + 1, x1, z2 - 1, 3, 4)
    if two:
        neo_ribbon(d, x2, z1 + 1, x2, z2 - 1, 8, 9)
        neo_ribbon(d, x1, z1 + 1, x1, z2 - 1, 8, 9)
    # canopy over the entrance + sign
    for x in range(4, 10):
        for z in (z1 - 1, z1 - 2):
            d.set(x, 5, z, sl("smooth_quartz", "top"))
    d.sign(8, 6, z1 - 1, "north", ["BUILD", "& DESIGN"], "birch", glow=True, color="cyan")
    d.hut(3, y0, 4)
    # ---- ground floor: drafting desk at the front, racks at the back, workshop (L2+) on the east wall
    d.item(4, y0, 5, "cartography_table")
    d.item(5, y0, 5, "crafting_table")
    d.table(4, y0, 7, kind="slab", top="smooth_quartz_slab")
    d.table(5, y0, 7, kind="slab", top="smooth_quartz_slab")
    d.chair(4, y0, 8, "south", "birch")
    d.chair(5, y0, 8, "south", "birch")
    d.set(4, y0 + 1, 7, "white_candle[candles=1,lit=false,waterlogged=false]")
    racks = rack_line(d, [(x, z2 - 1) for x in range(x1 + 1, x1 + 5)], y0, 9 if L == 1 else 12)
    d.item(7, y0, z2 - 1, "barrel", "up")
    d.item(8, y0, z2 - 1, "barrel", "up")
    if two:
        for i, b in enumerate(("smithing_table", "anvil", "grindstone", "stonecutter")):
            d.item(x2 - 1, y0, 5 + i, b, "west" if b != "anvil" else "north")
        if L <= 3:
            d.item(x2 - 1, y0, 9, "hopper")
        else:
            d.item(x2 - 1, y0, 9, "domum_ornamentum:architectscutter", "west")
        if L >= 5:
            d.item(9, y0, z2 - 1, "ender_chest", "north")
        d.rug(7, 6, 9, 8, y0, ("gray_carpet",), "plain")
    for x in (4, 8):
        d.set(x, 5 if not two else 5, 7, "sea_lantern")
    # ---- upper floor: drafting library
    if two:
        run_stairs(d, 10, 4, y0, 4, "south", "smooth_quartz", fill="smooth_quartz")
        # landing at (10,8) on y6; railing along the stair well
        for z in (4, 5, 6, 7):
            d.set(9, 7, z, "glass_pane")
        yb = 7
        for z in range(5, 11):
            d.bookshelf(x1 + 1, yb, z, 2)
        d.item(4, yb, z2 - 1, "lectern", "north")
        d.item(5, yb, z2 - 1, "cartography_table")
        d.item(6, yb, z2 - 1, "crafting_table")
        # drafting table with chairs
        d.table(6, yb, 6, kind="slab", top="smooth_quartz_slab")
        d.table(7, yb, 6, kind="slab", top="smooth_quartz_slab")
        d.chair(6, yb, 5, "north", "birch")
        d.chair(7, yb, 5, "north", "birch")
        if L >= 4:
            d.table(6, yb, 8, kind="slab", top="smooth_quartz_slab")
            d.table(7, yb, 8, kind="slab", top="smooth_quartz_slab")
            d.chair(6, yb, 9, "south", "birch")
            d.chair(5, yb, 6, "west", "birch")
            d.chair(8, yb, 6, "east", "birch")
            d.chair(7, yb, 9, "south", "birch")
            d.bed(x2 - 1, yb, z2 - 1, "south")
            d.set(x2 - 1, yb, z2 - 3, sl("birch", "top"))
            d.item(8, yb, z2 - 1, "jukebox")
        d.set(8, yb, 4, "potted_bamboo")
        for x in (5, 9):
            d.set(x, 10, 7, "sea_lantern")
    # ---- materials yard
    if L >= 3:
        yx1, yx2, yz1, yz2 = 14, 24, 3, 15
        for x, z in ring(yx1, yz1, yx2, yz2):
            if x == yx1 and z <= z2:
                continue
            d.set(x, y0, z, "light_gray_concrete")
            d.set(x, y0 + 1, z, "white_stained_glass_pane" if x != yx1 else "light_gray_concrete")
        for x in (17, 18, 19):
            for y in (2, 3):
                d.set(x, y, yz1, AIR)
        d.fill(yx1 + 1, 1, yz1 + 1, yx2 - 1, 1, yz2 - 1, "gray_concrete")
        for x in range(yx1 + 1, yx2):
            d.set(x, 1, yz1 + 3, "yellow_concrete")
        # covered rack aisles under a flat steel canopy at the back of the yard
        cz1 = 9
        for x, z in ((yx1 + 1, cz1), (yx2 - 1, cz1), (yx1 + 1, yz2 - 1), (yx2 - 1, yz2 - 1)):
            d.fill(x, y0, z, x, 5, z, "gray_concrete")
        d.fill(yx1 + 1, 6, cz1, yx2 - 1, 6, yz2 - 1, sl("smooth_stone"))
        for x in range(yx1 + 1, yx2):
            d.set(x, 6, cz1 - 1, "cyan_concrete")
        need = {3: 22, 4: 33, 5: 44}[L] - racks
        n = 0
        for z in (cz1 + 2, cz1 + 3):
            cells = [(x, z) for x in range(16, 23)]
            n += rack_line(d, cells, y0, need - n)
        racks += n
        for x in (17, 21):
            d.set(x, 5, cz1 + 1, SLANT)
            d.set(x, 5, cz1 + 4, SLANT)
        # material stacks on the open yard
        for x, z, b, h in ((22, 5, "stone_bricks", 2), (23, 5, "stone_bricks", 1), (22, 6, "bricks", 1),
                           (16, 6, "white_concrete", 2), (16, 5, "white_concrete", 1), (19, 6, "glass", 1)):
            pallet(d, x, z, y0, b, h)
        log_pile(d, 18, 6, 20, 7, y0, 2, "birch_log", "x")
    # ---- tower crane (L4+)
    if L >= 4:
        mx, mz = 23, 13
        for y in range(y0, 17):
            d.set(mx, y, mz, "yellow_concrete" if y % 2 == 0 else "yellow_stained_glass")
        d.set(mx, 17, mz, "yellow_concrete")
        for x in range(15, 26):
            d.set(x, 17, mz, "yellow_concrete" if x in (15, 23, 25) else "iron_bars")
        d.set(mx, 18, mz, "yellow_concrete")
        d.set(24, 16, mz, "gray_concrete")
        d.set(25, 16, mz, "gray_concrete")
        d.set(mx - 1, 16, mz, "light_gray_stained_glass")       # cab
        for y in range(11, 17):
            d.set(16, y, mz, "chain[axis=y,waterlogged=false]")
        d.set(16, 10, mz, "stone_bricks")
        d.set(mx, 2, mz - 1, AIR)
    # roof: solar panels
    if L >= 3:
        for x in range(x1 + 2, x2 - 1):
            for z in (z1 + 2, z1 + 4):
                d.set(x, ytop + 2, z, "daylight_detector[inverted=false,power=0]")
    for x in (3, 11):
        d.set(x, y0, z1 - 1, "moss_block")
        d.set(x, y0 + 1, z1 - 1, "azalea")
    return d


def builder_hw(rel, L):
    d = Design("Hearthwood", rel, (29, 22, 27), paving="gravel")
    hx1, hz1, hx2, hz2 = 3, 3, 14, 11
    y0 = 2
    two = L >= 2
    hw_walls(d, hx1, hz1, hx2, hz2, y0, 5)
    for x in range(hx1, hx2 + 1):
        for z in (hz1, hz2):
            d.set(x, y0, z, "bricks" if (x + z) % 2 else "stone_bricks")
    roof_y = 6
    if two:
        d.fill(hx1, 6, hz1 - 1, hx2, 6, hz2, "dark_oak_planks")
        hw_walls(d, hx1, hz1 - 1, hx2, hz2, 7, 9, floor=None, base=None, step=2)
        for x in range(hx1, hx2 + 1, 2):
            d.set(x, 5, hz1 - 1, st("dark_oak", "south", "top"))
        d.fill(hx1 + 1, 6, hz1, hx2 - 1, 6, hz2 - 1, "spruce_planks")
        roof_y = 10
    uz1 = hz1 - 1 if two else hz1
    ridge = d.gable(hx1, uz1, hx2, hz2, roof_y, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite")
    # windows / door
    for x in (5, 11, 13):
        if x == 13:
            continue
        win(d, x, 3, hz1)
        d.set(x, 2, hz1 - 1, tr("dark_oak", "north", "top"))
    win(d, 12, 3, hz1)
    d.door(8, y0, hz1, "south", "dark_oak")
    d.door(9, y0, hz1, "south", "dark_oak", "right")
    d.set(8, 4, hz1, "dark_oak_planks")
    d.set(9, 4, hz1, "dark_oak_planks")
    for z in (5, 8):
        win(d, hx1, 3, z)
    if two:
        for x in (5, 8, 11):
            win(d, x, 8, uz1)
            d.set(x, 7, uz1 - 1, tr("dark_oak", "north", "top"))
            d.set(x, 8 - 1 + 0, uz1 - 1, tr("dark_oak", "north", "top"))
        for z in (5, 8):
            win(d, hx1, 8, z)
            win(d, hx2, 8, z)
    d.sign(10, 4, hz1 - 1, "north", ["Master Builder", "& Mason"], "dark_oak")
    # chimney + fireplace on the west wall
    d.hearth(hx1 + 1, y0, 9, "east", ridge + 2, "bricks", "campfire")
    for y in range(y0, ridge + 2):
        d.set(hx1, y, 9, "bricks")
    d.hut(4, y0, 4)
    # ---- ground floor
    d.item(12, y0, 4, "cartography_table")
    d.item(13, y0, 4, "crafting_table")
    d.table(12, y0, 6, "dark_oak")
    d.chair(12, y0, 7, "south", "dark_oak")
    d.chair(13, y0, 6, "east", "dark_oak")
    d.item(13, y0, 10, "barrel", "up")
    d.item(13, y0, 9, "barrel", "up")
    if two:
        d.item(10, y0, 10, "anvil", "east")
        d.item(9, y0, 10, "smithing_table")
        d.item(8, y0, 10, "grindstone", "north")
        d.item(7, y0, 10, "stonecutter", "north")
        if L <= 3:
            d.item(6, y0, 10, "hopper")
        else:
            d.item(6, y0, 10, "domum_ornamentum:architectscutter", "north")
        if L >= 5:
            d.item(5, y0, 10, "ender_chest", "north")
        # stairs up along the east wall, rising south
        run_stairs(d, 13, 5, y0, 4, "south", "dark_oak", fill="dark_oak_planks")
    for x in (6, 10):
        d.set(x, 5, 7, LANT)
    d.rug(6, 6, 9, 8, y0, ("red_carpet", "orange_carpet"))
    # ---- upper floor: drafting room & library
    if two:
        yb = 7
        for x in range(4, 10):
            d.bookshelf(x, yb, hz2 - 1, 2)
        d.item(10, yb, hz2 - 1, "lectern", "north")
        d.item(4, yb, 3, "cartography_table")
        d.item(4, yb, 4, "crafting_table")
        d.table(6, yb, 5, "dark_oak", "slab")
        d.table(7, yb, 5, "dark_oak", "slab")
        d.chair(6, yb, 4, "north", "dark_oak")
        d.chair(7, yb, 4, "north", "dark_oak")
        for z in (5, 6, 7, 8):
            d.set(12, yb, z, "dark_oak_fence")
        d.set(12, yb, 9, "dark_oak_fence")
        if L >= 4:
            d.bed(4, yb, 8, "west")
            d.set(4, yb, 7, sl("dark_oak", "top"))
            d.candle(4, yb + 1, 7, 1)
            d.item(10, yb, 3, "jukebox")
            d.chair(6, yb, 6, "south", "dark_oak")
            d.chair(7, yb, 6, "south", "dark_oak")
        for x in (6, 10):
            d.set(x, 9, 7, LANT)
    # ---- yard wall & shed
    wall = "cobblestone_wall"
    for x in range(hx2 + 1, 27):
        d.set(x, y0, hz1 + 2, wall)
    for z in range(hz1 + 2, 25):
        d.set(26, y0, z, wall)
    for x in range(2, 27):
        d.set(x, y0, 25, wall)
    for z in range(hz2 + 1, 25):
        d.set(2, y0, z, wall)
    for x in (19, 20, 21):
        d.set(x, y0, hz1 + 2, AIR)
    d.set(18, y0, hz1 + 2, "stone_bricks")
    d.set(22, y0, hz1 + 2, "stone_bricks")
    d.set(18, y0 + 1, hz1 + 2, LANT_S)
    d.set(22, y0 + 1, hz1 + 2, LANT_S)
    sx1, sx2 = {1: (17, 23), 2: (15, 25), 3: (9, 25), 4: (4, 25), 5: (4, 25)}[L]
    sz1, sz2 = 17, 23
    for x in range(sx1, sx2 + 1):
        for y in range(y0, 6):
            d.set(x, y, sz2, "bricks")
        d.set(x, 1, sz2, "stone_bricks")
    for z in range(sz1, sz2 + 1):
        for x in (sx1, sx2):
            for y in range(y0, 6):
                d.set(x, y, z, "bricks" if z > sz1 else lg("stripped_dark_oak_log", "y"))
    for x in range(sx1, sx2 + 1, 3):
        for y in range(y0, 6):
            d.set(x, y, sz1, lg("stripped_dark_oak_log", "y"))
    for x in range(sx1, sx2 + 1):
        d.set(x, 6, sz1, lg("stripped_dark_oak_log", "x"))
    for x in range(sx1 + 1, sx2):
        for z in range(sz1 + 1, sz2):
            d.set(x, 1, z, "spruce_planks")
    d.fill(sx1, 6, sz1, sx1, 6, sz2, "bricks")
    d.fill(sx2, 6, sz1, sx2, 6, sz2, "bricks")
    d.fill(sx1 + 1, 6, sz2, sx2 - 1, 6, sz2, "bricks")
    d.gable(sx1, sz1, sx2, sz2, 7, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "bricks")
    need = {1: 9, 2: 12, 3: 22, 4: 33, 5: 44}[L] - 0
    shed_racks = need - (0)
    n = rack_line(d, [(x, sz2 - 1) for x in range(sx1 + 1, sx2)], y0, shed_racks)
    if n < shed_racks:
        n += rack_line(d, [(x, sz2 - 3) for x in range(sx1 + 2, sx2 - 1)], y0, shed_racks - n)
    for x in range(sx1 + 2, sx2 - 1, 4):
        d.set(x, 6, sz1 + 2, LANT) if d.air(x, 6, sz1 + 2) else None
    # tie beams to hang lamps from
    for x in range(sx1 + 3, sx2 - 1, 6):
        for z in range(sz1 + 1, sz2):
            d.set(x, 6, z, lg("stripped_dark_oak_log", "z"))
        d.set(x, 5, sz1 + 2, LANT)
    # yard: timber & stone stacks, sawhorse
    log_pile(d, 16, 13, 20, 14, y0, 2, "oak_log", "x")
    for x, z, b, h in ((23, 13, "stone_bricks", 2), (24, 13, "stone_bricks", 1), (23, 14, "cobblestone", 1),
                       (24, 14, "bricks", 2)):
        pallet(d, x, z, y0, b, h)
    d.set(10, y0, 14, "oak_fence")
    d.set(12, y0, 14, "oak_fence")
    d.set(11, y0, 14, AIR)
    for x in (10, 11, 12):
        d.set(x, y0 + 1, 14, lg("stripped_oak_log", "x"))
    d.set(8, y0, 14, "water_cauldron[level=3]")
    if L >= 4:
        d.chair(5, y0, 14, "south", "dark_oak")
        d.chair(6, y0, 14, "south", "dark_oak")
    # cottage front: flower boxes
    return d


def builder_cas(rel, L):
    d = Design("Cascadia", rel, (27, 24, 31), paving="coarse_dirt")
    x1, x2, z1 = 5, 17, 4
    z2 = {1: 14, 2: 18, 3: 22, 4: 22, 5: 26}[L]
    y0 = 2
    cas_walls(d, x1, z1, x2, z2, y0, 6)
    ridge = d.gable(x1, z1, x2, z2, 7, "z", "dark_oak_stairs", "dark_oak_slab", "spruce_planks", overhang=1)
    # board-and-batten gable end
    mid = (x1 + x2) // 2
    for y in range(7, ridge):
        for x in range(x1, x2 + 1):
            if d.get(x, y, z1) == "minecraft:spruce_planks" and x % 2 == 0:
                d.set(x, y, z1, lg("stripped_spruce_log", "y"))
    # big barn doors
    for x in range(mid - 1, mid + 2):
        for y in range(y0, 6):
            d.set(x, y, z1, AIR)
    for x in range(mid - 1, mid + 2):
        d.set(x, 5, z1, lg("dark_oak_log", "x"))
    # hay-hoist beam at the peak
    d.set(mid, ridge - 2, z1 - 1, lg("dark_oak_log", "z"))
    d.set(mid, ridge - 2, z1 - 2, lg("dark_oak_log", "z"))
    for y in range(ridge - 5, ridge - 2):
        d.set(mid, y, z1 - 2, "chain[axis=y,waterlogged=false]")
    d.set(mid, ridge - 6, z1 - 2, "lantern[hanging=true,waterlogged=false]")
    d.set(mid, ridge - 4, z1, AIR)
    win(d, mid, ridge - 4, z1, 1)
    for x in (x1 + 2, x2 - 2):
        win(d, x, 3, z1)
        shutters(d, x, 3, z1, "north")
    for z in range(z1 + 3, z2 - 1, 4):
        win(d, x1, 3, z)
        win(d, x2, 3, z)
    d.sign(mid - 2, 6, z1 - 1, "north", ["TIMBER", "FRAMERS"], "spruce")
    d.sign(mid + 2, 6, z1 - 1, "north", ["& BUILDERS", "est. 1902"], "spruce")
    d.hut(x1 + 1, y0, z1 + 1)
    # ---- interior: workbench island in the nave, racks down both sides
    d.item(x1 + 2, y0, z1 + 1, "crafting_table")
    d.item(x1 + 3, y0, z1 + 1, "cartography_table")
    d.item(x2 - 1, y0, z1 + 1, "barrel", "up")
    d.item(x2 - 2, y0, z1 + 1, "barrel", "up")
    need = {1: 9, 2: 12, 3: 24, 4: 33, 5: 44}[L]
    lean = L >= 4
    side = [(x1 + 1, z) for z in range(z1 + 4, z2 - 1)]
    n = rack_line(d, side, y0, min(need, 12 if lean else need))
    if n < need and not lean:
        n += rack_line(d, [(x2 - 1, z) for z in range(z1 + 4, z2 - 1)], y0, need - n)
    # workbench + saw horse in the nave
    for z in (z1 + 5, z1 + 6):
        d.set(mid, y0, z, "stripped_spruce_wood[axis=y]")
    d.chair(mid - 1, y0, z1 + 5, "west", "spruce")
    d.chair(mid - 1, y0, z1 + 6, "west", "spruce")
    if b_items(L):
        tools = ["anvil", "smithing_table", "grindstone", "stonecutter",
                 "hopper" if L <= 3 else "domum_ornamentum:architectscutter"]
        if L >= 5:
            tools.append("ender_chest")
        for i, t in enumerate(tools):
            d.item(x2 - 1, y0, z2 - 1 - i, t, "west")
    # tie beams + lamps
    for z in range(z1 + 3, z2, 4):
        for x in range(x1 + 1, x2):
            d.set(x, 7, z, lg("stripped_spruce_log", "x"))
        d.set(mid, 6, z, LANT)
    # ---- loft at the back (L2+): drafting room and library under the roof (headroom x8..14)
    if L >= 2:
        lz1 = z1 + 8 if L == 2 else z1 + 10
        d.fill(x1 + 1, 7, lz1, x2 - 1, 7, z2 - 1, "spruce_planks")
        yb = 8
        for z in range(lz1, lz1 + 6):                       # knee-wall bookcases under both eaves
            d.bookshelf(x1 + 2, yb, z)
            d.bookshelf(x2 - 2, yb, z)
        d.item(9, yb, z2 - 1, "lectern", "north")
        d.item(10, yb, z2 - 1, "cartography_table")
        d.item(11, yb, z2 - 1, "crafting_table")
        d.table(mid, yb, z2 - 4, "spruce")
        d.chair(mid - 1, yb, z2 - 4, "west", "spruce")
        d.chair(mid + 1, yb, z2 - 4, "east", "spruce")
        for x in range(9, 15):
            d.set(x, yb, lz1, "spruce_fence")
        run_stairs(d, 8, lz1 - 5, y0, 5, "south", "spruce", fill="spruce_planks")
        for z in range(lz1 - 5, lz1):
            d.set(9, 7, z, AIR)
        if L >= 4:
            d.bed(14, yb, z2 - 1, "south")
            d.set(13, yb, z2 - 1, sl("spruce", "top"))
            d.set(13, yb + 1, z2 - 1, LANT_S)
            d.item(12, yb, z2 - 1, "jukebox")
            d.chair(mid, yb, z2 - 5, "north", "spruce")
            d.chair(mid, yb, z2 - 3, "south", "spruce")
    # ---- lean-to lumber shed on the east side (L4+)
    if lean:
        lz2 = z2 - 2
        lx1, lx2 = x2, x2 + 6
        for z in range(z1 + 2, lz2 + 1):
            for x in range(lx1 + 1, lx2 + 1):
                d.set(x, 1, z, "spruce_planks")
        for z in range(z1 + 2, lz2 + 1, 4):
            d.fill(lx2, y0, z, lx2, 5, z, lg("spruce_log", "y"))
        d.fill(lx2, y0, lz2, lx2, 5, lz2, lg("spruce_log", "y"))
        for z in range(z1 + 1, lz2 + 2):
            for x in range(lx1 + 1, lx2 + 2):
                d.set(x, 6, z, sl("spruce", "bottom") if x > lx1 + 3 else sl("spruce", "top"))
        for z in range(z1 + 6, z1 + 9):
            for y in (y0, y0 + 1):
                d.set(x2, y, z, AIR)
        n += rack_line(d, [(lx1 + 2, z) for z in range(z1 + 3, lz2)], y0, need - n)
        n += rack_line(d, [(lx1 + 3, z) for z in range(z1 + 3, lz2)], y0, need - n)
        log_pile(d, lx1 + 5, z1 + 3, lx1 + 5, lz2 - 1, y0, 1, "stripped_spruce_log", "z")
    # yard: log pile, saw horse
    log_pile(d, 2, z1 + 2, 3, z1 + 8, y0, 2, "spruce_log", "z")
    d.keg(x1 - 1, y0, z1 - 2, "north")
    for x in (x1 + 1, x1 + 2):                                     # bench by the doors
        d.chair(x, y0, z1 - 1, "south", "spruce")
    return d


@design("builder")
def builder(pack, rel, L):
    return {"Neoterra": builder_neo, "Hearthwood": builder_hw, "Cascadia": builder_cas}[pack](rel, L)


# =============================================================================================== SAWMILL
"""
Sawmill
  Neoterra   "Timber processing hall": glazed concrete shed with a north-light sawtooth roof, a straight saw line
             (stonecutters with in-feed / out-feed logs) down the middle, timber racks, log yard behind.
             Grows eastward bay by bay.
  Hearthwood "Watermill": stone mill house beside a mill race with an undershot water wheel and axle into the
             gear room; saw bench inside; timber-framed upper office from L3, log lean-to at L5.
  Cascadia   "Steam sawmill": long open-sided pole shed with the saw line, log deck at the in-feed end; from L3 a
             false-front mill office and a copper teepee waste burner.
"""


def saw_line(d, cells, y, n, feed="stripped_birch_log", axis="x"):
    """Stonecutters (the saws) on consecutive cells with a log on the in-feed and out-feed end."""
    d.set(*_xyz(cells[0], y), lg(feed, axis))
    for c in cells[1:n + 1]:
        d.item(c[0], y, c[1], "stonecutter", "north" if axis == "x" else "west")
    d.set(*_xyz(cells[n + 1], y), lg(feed, axis))


def _xyz(c, y):
    return c[0], y, c[1]


SAWS = {1: 3, 2: 4, 3: 5, 4: 6, 5: 7}


def saw_neo(rel, L):
    d = Design("Neoterra", rel, (25, 12, 23), paving="smooth_stone")
    x1, z1, z2 = 3, 4, 13
    x2 = {1: 13, 2: 14, 3: 16, 4: 18, 5: 20}[L]
    y0 = 2
    d.box(x1, y0, z1, x2, 6, z2, "light_gray_concrete", floor="polished_andesite")
    for x, z in ring(x1, z1, x2, z2):
        pillar = (z in (z1, z2) and (x - x1) % 3 == 0) or (x in (x1, x2) and (z - z1) % 3 == 0)
        if not pillar:
            d.window(x, 3, z, x, 5, z, "glass_pane")
        else:
            d.fill(x, y0, z, x, 6, z, "white_concrete")
    d.fill(x1, 6, z1, x2, 6, z1, "cyan_terracotta")
    # sawtooth roof: north-light glazing rows
    d.fill(x1, 7, z1, x2, 7, z2, "smooth_quartz")
    for z in range(z1, z2 + 1):
        k = (z - z1) % 3
        for x in range(x1, x2 + 1):
            if k == 0:
                d.set(x, 8, z, "light_blue_stained_glass")
                d.set(x, 7, z, "light_blue_stained_glass") if x not in (x1, x2) and z not in (z1, z2) else None
            elif k == 1:
                d.set(x, 8, z, st("smooth_quartz", "north"))
    d.double_door(x1 + 3, y0, z1, "x", "south", "birch")
    for x in range(x1 + 2, x1 + 7):
        for z in (z1 - 1, z1 - 2):
            d.set(x, 5, z, sl("smooth_quartz", "top"))
    d.sign(x1 + 5, 6, z1 - 1, "north", ["NEOTERRA", "TIMBER WORKS"], "birch", glow=True, color="cyan")
    d.hut(x1 + 1, y0, z1 + 1)
    d.item(x1 + 1, y0, z1 + 2, "crafting_table")
    if L >= 3:
        d.item(x1 + 1, y0, z1 + 3, "cartography_table")
        d.item(x1 + 1, y0, z1 + 4, "lectern", "east")
        d.chair(x1 + 2, y0, z1 + 4, "east", "birch", sit=False)
    if L >= 4:
        d.item(x1 + 1, y0, z1 + 6, "domum_ornamentum:architectscutter", "east")
    # saw line down the middle (along x)
    zc = 9
    n = SAWS[L]
    saw_line(d, [(x, zc) for x in range(x1 + 3, x1 + 3 + n + 2)], y0, n)
    for x in range(x1 + 3, x1 + 5 + n):
        d.set(x, 1, zc - 1, "yellow_concrete")
        d.set(x, 1, zc + 1, "yellow_concrete")
    # racks with timber stacks between them on the back wall
    r = 0
    for i, x in enumerate(range(x1 + 2, x2, 2)):
        if r < L:
            d.rack(x, y0, z2 - 1, "north")
            r += 1
        else:
            d.set(x, y0, z2 - 1, "birch_planks")
        d.set(x + 1, y0, z2 - 1, "stripped_birch_wood[axis=y]")
        d.set(x + 1, y0 + 1, z2 - 1, "birch_planks")
    for x in range(x1 + 2, x2, 3):
        d.set(x, 6, 6, "sea_lantern")
        d.set(x, 6, 11, "sea_lantern")
    # log yard behind
    for i, x in enumerate(range(x1, x2 - 2, 5)):
        log_pile(d, x, 16, x + 3, 18, y0, 2, "birch_log", "x")
    for x in range(x1 - 1, x2 + 2):
        d.set(x, y0, 20, "light_gray_concrete")
        d.set(x, y0 + 1, 20, "white_stained_glass_pane")
    d.set(x2 + 2, y0, 6, "moss_block")
    d.set(x2 + 2, y0 + 1, 6, "azalea")
    return d


def saw_hw(rel, L):
    d = Design("Hearthwood", rel, (25, 21, 25), paving="gravel")
    x1, x2, z1 = 4, 13, 4
    z2 = {1: 12, 2: 13, 3: 14, 4: 15, 5: 15}[L]
    y0 = 2
    d.box(x1, y0, z1, x2, 5, z2, "stone_bricks", floor="spruce_planks")
    for x, z in ring(x1, z1, x2, z2):
        for y in range(y0, 6):
            h = (x * 31 + y * 7 + z * 13) % 7
            if h == 0:
                d.set(x, y, z, "mossy_stone_bricks")
            elif h == 1:
                d.set(x, y, z, "andesite")
        d.set(x, y0, z, "cobblestone")
    two = L >= 3
    if two:
        d.fill(x1, 6, z1, x2, 6, z2, "dark_oak_planks")
        d.fill(x1 + 1, 6, z1 + 1, x2 - 1, 6, z2 - 1, "spruce_planks")
        hw_walls(d, x1, z1, x2, z2, 7, 9, floor=None, base=None, step=2)
        ridge = d.gable(x1, z1, x2, z2, 10, "z", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite")
    else:
        ridge = d.gable(x1, z1, x2, z2, 6, "z", "deepslate_tile_stairs", "deepslate_tile_slab", "stone_bricks")
    # door, windows
    d.door(10, y0, z1, "south", "dark_oak")
    for x in (6, 7):
        win(d, x, 3, z1)
    for z in range(z1 + 2, z2 - 1, 3):
        win(d, x1, 3, z)
    if two:
        for x in (6, 8, 10):
            win(d, x, 8, z1)
            win(d, x, 8, z2)
        win(d, (x1 + x2) // 2, 11, z1)
    d.sign(11, 4, z1 - 1, "north", ["Wheelwright", "Saw Mill"], "dark_oak")
    # mill race and water wheel on the east side
    for z in range(0, 25):
        d.set(16, 1, z, "water[level=0]")
        d.set(17, 1, z, "water[level=0]")
        d.set(15, 1, z, "stone_bricks")
        d.set(18, 1, z, "stone_bricks")
        d.set(18, 2, z, "stone_brick_wall")
    for x in (16, 17):                                            # footbridge at the front
        d.set(x, 2, 1, sl("spruce", "bottom"))
    d.set(18, 2, 1, AIR)
    wc, wy = 9, 4
    for dy in range(-3, 4):
        for dz in range(-3, 4):
            r = (dy * dy + dz * dz) ** 0.5
            if 2.5 <= r < 3.6:
                d.set(16, wy + dy, wc + dz, "dark_oak_planks" if (dy + dz) % 2 else "stripped_dark_oak_log[axis=x]")
            elif r < 2.5 and (dy == 0 or dz == 0):
                d.set(16, wy + dy, wc + dz, "stripped_spruce_log[axis=x]" if (dy, dz) == (0, 0) else
                      lg("stripped_spruce_log", "y" if dz == 0 else "z"))
    for x in (14, 15):
        d.set(x, wy, wc, "dark_oak_log[axis=x]")
    d.set(x2, wy, wc, "dark_oak_log[axis=x]")
    d.set(x2 - 1, y0, wc, "grindstone[face=floor,facing=east]")   # gear train
    d.set(x2 - 1, wy, wc, lg("dark_oak_log", "x"))
    d.fill(x2 - 1, y0 + 1, wc, x2 - 1, wy - 1, wc, lg("dark_oak_log", "y"))
    # ---- mill floor
    d.hut(5, y0, 5)
    d.item(5, y0, 6, "crafting_table")
    n = SAWS[L]
    saw_line(d, [(8, z) for z in range(z1 + 1, z1 + n + 3)], y0, n, "stripped_oak_log", "z")
    r = rack_line(d, [(x1 + 1, z) for z in range(z2 - 1, z1 + 2, -1)], y0, min(L, 3), 1, "east")
    if L > 3:
        rack_line(d, [(x, z2 - 1) for x in range(x1 + 2, x1 + 5)], y0, L - 3, 1, "north")
    log_pile(d, 11, z2 - 2, 12, z2 - 1, y0, 2, "oak_log", "z")
    for z in range(z1 + 2, z2 - 1, 3):
        d.set(9, 5, z, LANT)
    # ---- upper office (L3+)
    if two:
        run_stairs(d, 11, z1 + 1, y0, 4, "south", "dark_oak", fill="dark_oak_planks")
        for z in range(z1 + 1, z1 + 4):
            d.set(10, 7, z, "dark_oak_fence")
        yb = 7
        d.item(5, yb, z2 - 1, "lectern", "north")
        d.item(6, yb, z2 - 1, "cartography_table")
        d.table(6, yb, 7, "dark_oak")
        d.chair(6, yb, 8, "south", "dark_oak", sit=False)
        if L >= 4:
            d.item(5, yb, 5, "domum_ornamentum:architectscutter", "south")
        d.set(8, 9, (z1 + z2) // 2, LANT)
        log_pile(d, 9, z2 - 2, 12, z2 - 1, yb, 1, "stripped_oak_log", "x")
    # ---- log lean-to on the west (L5), log piles in the yard
    if L >= 5:
        for z in range(z1 + 1, z2):
            for x in range(1, x1):
                d.set(x, 5, z, sl("deepslate_tile", "bottom") if x < 3 else sl("deepslate_tile", "top"))
        for z in (z1 + 1, z2 - 1):
            d.fill(1, y0, z, 1, 4, z, lg("stripped_dark_oak_log", "y"))
        log_pile(d, 2, z1 + 2, 3, z2 - 2, y0, 2, "oak_log", "z")
    log_pile(d, 5, z2 + 3, 10, z2 + 4, y0, 2, "oak_log", "x")
    d.set(12, y0, z1 - 1, "oak_fence")
    d.set(12, y0 + 1, z1 - 1, LANT_S)
    return d


def saw_cas(rel, L):
    d = Design("Cascadia", rel, (31, 21, 25), paving="coarse_dirt")
    x1, z1, z2 = 4, 7, 14
    x2 = {1: 15, 2: 16, 3: 18, 4: 20, 5: 22}[L]
    y0 = 2
    d.fill(x1, 1, z1, x2, 1, z2, "spruce_planks")
    post = lg("spruce_log", "y")
    for x, z in ring(x1, z1, x2, z2):
        if (z in (z1, z2) and ((x - x1) % 4 == 0 or x == x2)) or (x in (x1, x2) and z in (z1, z2)):
            d.fill(x, y0, z, x, 5, z, post)
            d.set(x, 1, z, "cobblestone")
        elif z == z2 or (x == x2 and z > z1):
            d.fill(x, y0, z, x, 3, z, "spruce_planks")              # half-height board wall
    for x in range(x1, x2 + 1):
        d.set(x, 6, z1, lg("stripped_spruce_log", "x"))
        d.set(x, 6, z2, lg("stripped_spruce_log", "x"))
    for z in range(z1, z2 + 1):
        d.set(x1, 6, z, lg("stripped_spruce_log", "z"))
        d.set(x2, 6, z, lg("stripped_spruce_log", "z"))
    for x in range(x1 + 4, x2, 4):                                   # tie beams
        for z in range(z1 + 1, z2):
            d.set(x, 6, z, lg("stripped_spruce_log", "z"))
        d.set(x, 5, (z1 + z2) // 2 - 1, LANT)
    d.gable(x1, z1, x2, z2, 7, "x", "dark_oak_stairs", "dark_oak_slab", "spruce_planks")
    # saw line
    zc = 10
    n = SAWS[L]
    saw_line(d, [(x, zc) for x in range(x1 + 3, x1 + 5 + n)], y0, n, "stripped_spruce_log", "x")
    d.hut(x1 + 1, y0, z1 + 1)
    d.item(x1 + 2, y0, z2 - 1, "crafting_table")
    rack_line(d, [(x, z2 - 1) for x in range(x1 + 4, x2, 2)], y0, L, 1, "north")
    for x in range(x1 + 5, x2, 2):
        if d.air(x, y0, z2 - 1):
            d.set(x, y0, z2 - 1, "spruce_planks")
            d.set(x, y0 + 1, z2 - 1, sl("spruce"))
    # log deck at the in-feed (west) end: logs rolled down a ramp
    log_pile(d, 0, z1 + 1, 2, z2 - 1, y0, 2, "spruce_log", "z")
    log_pile(d, 1, 16, 7, 18, y0, 3, "spruce_log", "x")
    log_pile(d, 9, 17, 14, 18, y0, 2, "dark_oak_log", "x")
    # sawdust & lumber stacks in front
    for x in range(x1 + 2, x1 + 6):
        d.set(x, y0, z1 - 2, "stripped_spruce_wood[axis=x]")
    d.set(x1 + 3, y0 + 1, z1 - 2, "stripped_spruce_wood[axis=x]")
    if L >= 3:
        # mill office: false-front cabin at the north-east
        ox1, oz1, ox2, oz2 = 24, 3, 29, 9
        cas_walls(d, ox1, oz1, ox2, oz2, y0, 5)
        rg = d.gable(ox1, oz1, ox2, oz2, 6, "z", "dark_oak_stairs", "dark_oak_slab", "spruce_planks")
        for x in range(ox1, ox2 + 1):
            for y in range(6, rg + 2):
                d.set(x, y, oz1 - 1, "spruce_planks")
            d.set(x, rg + 2, oz1 - 1, sl("spruce"))
        d.door(26, y0, oz1, "south", "spruce")
        win(d, 28, 3, oz1)
        win(d, ox2, 3, 6)
        d.sign(27, rg, oz1 - 2, "north", ["MILL", "OFFICE"], "spruce")
        d.item(ox1 + 1, y0, oz2 - 1, "lectern", "north")
        d.item(ox1 + 2, y0, oz2 - 1, "cartography_table")
        d.chair(ox2 - 1, y0, oz2 - 1, "south", "spruce", sit=False)
        d.table(ox2 - 1, y0, oz2 - 2, "spruce")
        if L >= 4:
            d.item(ox1 + 1, y0, oz1 + 2, "domum_ornamentum:architectscutter", "east")
        d.set(26, 5, 6, LANT)
        # teepee burner
        cx, cz = 26, 19
        for y in range(y0, 13):
            rr = 3 if y < 6 else 2 if y < 9 else 1 if y < 12 else 0
            for dx in range(-3, 4):
                for dz in range(-3, 4):
                    dist = (dx * dx + dz * dz) ** 0.5
                    if rr - 0.5 <= dist < rr + 0.5 or (rr == 0 and dist < 0.5):
                        b = "iron_bars" if y >= 11 else ("weathered_cut_copper" if (y + dx) % 3 else "exposed_cut_copper")
                        d.set(cx + dx, y, cz + dz, b)
        for k in (0, 1):
            d.set(cx, y0 + k, cz - 3, AIR)
        d.set(cx, y0, cz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        d.set(cx, 1, cz - 1, "magma_block")
        d.set(cx, 1, cz + 1, "magma_block")
    return d


@design("sawmill")
def sawmill(pack, rel, L):
    return {"Neoterra": saw_neo, "Hearthwood": saw_hw, "Cascadia": saw_cas}[pack](rel, L)


# =============================================================================================== LUMBERJACK
"""
Lumberjack
  Neoterra   "Urban forestry station": compact white pavilion with a timber-slatted front, a glass tool room, a
             covered log store, sapling nursery planters; L3 terrace bench, L4 glasshouse with composter, L5 green
             roof.
  Hearthwood "Woodcutter's cottage": plastered timber-framed cottage with a big brick chimney, an open log store
             lean-to stacked with logs, chopping block and saw horse; fenced garden (composter) from L4 and a
             saw-pit shed at L5.
  Cascadia   "Forester's A-frame lodge": steep A-frame cabin on a river-rock base with a front deck, stone chimney,
             log piles; grows deeper, porch rockers at L3, garden at L4, woodshed at L5.
"""
JACK_RACKS = {1: 2, 2: 3, 3: 4, 4: 5, 5: 6}


def chopping_block(d, x, z, y, log="oak_log"):
    d.set(x, y, z, lg(log, "y"))
    d.set(x, y + 1, z, "lever[face=floor,facing=north,powered=false]")       # the axe in the block


def sawhorse(d, x, z, y, m="oak", along="x"):
    dx, dz = (1, 0) if along == "x" else (0, 1)
    d.set(x, y, z, f"{m}_fence")
    d.set(x + 2 * dx, y, z + 2 * dz, f"{m}_fence")
    for k in range(3):
        d.set(x + k * dx, y + 1, z + k * dz, lg(f"stripped_{m}_log", along))


def jack_neo(rel, L):
    d = Design("Neoterra", rel, (21, 12, 21), paving="smooth_stone")
    x1, z1, x2, z2 = 3, 4, 11, 10
    y0 = 2
    neo_block(d, x1, z1, x2, z2, y0, 5, floor="polished_diorite")
    for x in range(x1 + 1, x2):                                          # mangrove slat front + glass
        if x in (5, 6):
            continue
        d.window(x, 3, z1, x, 4, z1, "glass_pane")
        d.set(x, y0, z1, "stripped_mangrove_wood[axis=y]" if x % 2 else "white_concrete")
    d.double_door(5, y0, z1, "x", "south", "mangrove")
    neo_ribbon(d, x2, z1 + 1, x2, z2 - 1, 3, 4, every=0)
    d.sign(8, 5, z1 - 1, "north", ["FORESTRY", "STATION"], "mangrove", glow=True, color="lime")
    d.hut(x1 + 1, y0, z1 + 1)
    d.item(x1 + 1, y0, z1 + 2, "crafting_table")
    rack_line(d, [(x, z2 - 1) for x in range(x1 + 1, x2)], y0, JACK_RACKS[L], 1)
    for x in range(x1 + 1, x2):
        if d.air(x, y0 + 1, z2 - 1):
            d.set(x, y0 + 1, z2 - 1, "chiseled_bookshelf[facing=north,slot_0_occupied=false,slot_1_occupied=false,"
                                     "slot_2_occupied=false,slot_3_occupied=false,slot_4_occupied=false,slot_5_occupied=false]")
            break
    # tool wall: grindstone for the axes, saw horse
    d.set(x2 - 1, y0, z1 + 1, "grindstone[face=floor,facing=west]")
    d.set(x2 - 1, y0, z1 + 2, sl("mangrove", "top"))
    d.set(x2 - 1, y0 + 1, z1 + 2, "potted_oak_sapling")
    d.set(7, 5, 7, "sea_lantern")
    # covered log store (west)
    for z in (z1, z2):
        d.fill(1, y0, z, 1, 4, z, "light_gray_concrete")
    d.fill(0, 5, z1, 2, 5, z2, sl("smooth_quartz"))
    log_pile(d, 1, z1 + 1, 2, z2 - 1, y0, 3, "birch_log", "z")
    # nursery planters (front)
    for x in range(x2 + 2, x2 + 8):
        for z in (z1, z1 + 1, z1 + 3, z1 + 4):
            d.set(x, 1, z, "moss_block")
            d.set(x, y0, z, "birch_sapling[stage=0]" if (x + z) % 2 else "oak_sapling[stage=0]")
    for x in range(x2 + 1, x2 + 9):
        d.set(x, y0, z1 - 1, sl("smooth_stone"))
    if L >= 2:
        sawhorse(d, x2 + 3, z2 + 2, y0, "birch")
        log_pile(d, x2 + 2, z2 + 4, x2 + 7, z2 + 5, y0, 2, "oak_log", "x")
    if L >= 3:                                                           # terrace bench under a pergola
        for x, z in ((x1, z1 - 3), (x1 + 4, z1 - 3)):
            d.fill(x, y0, z, x, 4, z, "stripped_birch_log[axis=y]")
        for x in range(x1, x1 + 5):
            d.set(x, 5, z1 - 3, "stripped_birch_log[axis=x]")
            for z in (z1 - 2, z1 - 1):
                d.set(x, 5, z, "birch_slab[type=top,waterlogged=false]" if x % 2 else AIR)
        d.chair(x1 + 1, y0, z1 - 3, "north", "birch")
        d.chair(x1 + 3, y0, z1 - 3, "north", "birch")
        d.table(x1 + 2, y0, z1 - 3, "birch", "slab")
    if L >= 4:                                                           # glasshouse with composter
        gx1, gz1, gx2, gz2 = 3, 13, 10, 18
        d.box(gx1, y0, gz1, gx2, 4, gz2, "glass", floor="smooth_stone")
        d.fill(gx1, 5, gz1, gx2, 5, gz2, "glass")
        for x, z in ((gx1, gz1), (gx2, gz1), (gx1, gz2), (gx2, gz2)):
            d.fill(x, y0, z, x, 5, z, "white_concrete")
        d.door(6, y0, gz1, "north", "mangrove")
        d.item(gx1 + 1, y0, gz2 - 1, "composter")
        d.item(gx1 + 2, y0, gz2 - 1, "barrel", "up")
        for x in range(gx1 + 3, gx2):
            d.set(x, 1, gz2 - 1, "moss_block")
            d.set(x, y0, gz2 - 1, "spruce_sapling[stage=0]")
        for z in range(gz1 + 1, gz2 - 1):
            d.set(gx2 - 1, 1, z, "moss_block")
            d.set(gx2 - 1, y0, z, "birch_sapling[stage=0]")
        d.fill(6, 1, z2 + 1, 6, 1, gz1 - 1, "polished_andesite")
        d.door(7, y0, z2, "south", "mangrove")
    if L >= 5:                                                           # green roof
        for x in range(x1 + 1, x2):
            for z in range(z1 + 1, z2):
                d.set(x, 7, z, "moss_carpet" if (x + z) % 3 else "azalea")
    return d


def jack_hw(rel, L):
    d = Design("Hearthwood", rel, (25, 17, 21), paving="gravel")
    x1, z1, x2, z2 = 6, 4, 14, 10
    y0 = 2
    hw_walls(d, x1, z1, x2, z2, y0, 5)
    ridge = d.gable(x1, z1, x2, z2, 6, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite")
    d.door(9, y0, z1, "south", "dark_oak")
    for x in (7, 11, 13):
        win(d, x, 3, z1)
    for x in (8, 12):
        win(d, x, 3, z2)
    # chimney stack at the east gable
    d.hearth(x2 - 1, y0, 7, "west", ridge + 2, "bricks", "campfire")
    d.fill(x2, y0, 6, x2, ridge + 2, 8, "bricks")
    d.fill(x2 + 1, y0, 7, x2 + 1, ridge + 1, 7, "bricks")
    d.hut(x1 + 1, y0, z1 + 1)
    d.item(x1 + 1, y0, z1 + 2, "crafting_table")
    rack_line(d, [(x, z2 - 1) for x in range(x1 + 1, x2 - 2)], y0, JACK_RACKS[L], 1)
    d.rug(x1 + 3, 6, x2 - 3, 8, y0, ("brown_carpet", "red_carpet"))
    if L >= 3:
        d.chair(x2 - 2, y0, z1 + 1, "north", "dark_oak", arms=True)
        d.chair(x2 - 2, y0, z2 - 1, "south", "dark_oak", arms=True)
    d.set(10, 5, 7, LANT)
    # log store lean-to on the west wall, stacked full
    lx = x1 - 3 if L >= 2 else x1 - 2
    for z in range(z1, z2 + 1):
        for x in range(lx, x1):
            d.set(x, 5, z, sl("deepslate_tile", "top" if x == x1 - 1 else "bottom"))
    for z in (z1, z2):
        d.fill(lx, y0, z, lx, 4, z, lg("stripped_dark_oak_log", "y"))
    log_pile(d, lx, z1 + 1, x1 - 1, z2 - 1, y0, 3, "oak_log", "z")
    # yard: chopping block and saw horse
    chopping_block(d, 4, 13, y0)
    sawhorse(d, 7, 13, y0)
    for x in range(10, 13):
        d.set(x, y0, 13, lg("oak_log", "x"))
    if L >= 4:                                                           # fenced back garden with composter
        for x, z in ring(x1, z2 + 4, x2 + 4, 19):
            d.set(x, y0, z, "oak_fence")
        d.set(x1 + 3, y0, z2 + 4, AIR)                                 # garden entrance
        d.item(x1 + 1, y0, 18, "composter")
        d.item(x1 + 2, y0, 18, "barrel", "up")
        for x in range(x1 + 4, x2 + 3):
            for z in (16, 17):
                d.set(x, 1, z, "farmland[moisture=7]")
                d.set(x, y0, z, "oak_sapling[stage=0]" if x % 2 else "birch_sapling[stage=0]")
    if L >= 5:                                                           # open saw-pit shed east
        sx1, sx2 = 17, 22
        for x, z in ((sx1, z1), (sx2, z1), (sx1, z2), (sx2, z2)):
            d.fill(x, y0, z, x, 4, z, lg("stripped_dark_oak_log", "y"))
        d.gable(sx1, z1, sx2, z2, 5, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "oak_planks")
        for x in range(sx1, sx2 + 1):
            d.set(x, 4, z1, lg("stripped_dark_oak_log", "x"))
            d.set(x, 4, z2, lg("stripped_dark_oak_log", "x"))
        for x in range(sx1 + 1, sx2):
            d.set(x, 1, 7, "oak_planks")
        log_pile(d, sx1 + 1, z1 + 1, sx2 - 1, z1 + 1, y0, 1, "stripped_oak_log", "x")
        d.rack(sx2 - 1, y0, z2 - 1, "north")
        d.set(sx1 + 1, y0, z2 - 1, "oak_planks")
        d.set(sx1 + 2, y0, z2 - 1, "oak_planks")
        d.set(sx1 + 1, y0 + 1, z2 - 1, "oak_planks")
    return d


def jack_cas(rel, L):
    d = Design("Cascadia", rel, (23, 15, 25), paving="coarse_dirt")
    x1, x2, z1 = 5, 15, 7
    z2 = {1: 13, 2: 15, 3: 17, 4: 17, 5: 17}[L]
    y0 = 2
    # river-rock base course and A-frame roof right down to it
    d.box(x1, y0, z1, x2, y0, z2, "cobblestone", floor="spruce_planks")
    for x, z in ring(x1, z1, x2, z2):
        if (x + 2 * z) % 3 == 0:
            d.set(x, y0, z, "mossy_cobblestone")
    ridge = d.gable(x1, z1, x2, z2, 3, "z", "dark_oak_stairs", "dark_oak_slab", "stripped_spruce_log[axis=y]",
                    overhang=1)
    mid = (x1 + x2) // 2
    # gable fronts: stripped log boards with a big triangle of glass
    for y in range(3, ridge):
        for x in range(x1, x2 + 1):
            for z in (z1, z2):
                if d.get(x, y, z).startswith("minecraft:stripped_spruce_log"):
                    if abs(x - mid) < (ridge - y) - 1 and y >= 5 and z == z1:
                        d.set(x, y, z, "glass_pane")
    for y in (y0, y0 + 1):
        d.set(mid, y, z1, AIR)
    d.door(mid, y0, z1, "south", "spruce")
    win(d, mid - 2, 3, z1)
    win(d, mid + 2, 3, z1)
    # stone chimney at the back gable
    d.hearth(mid, y0, z2 - 1, "north", ridge + 2, "cobblestone", "campfire")
    d.fill(mid, y0, z2, mid, ridge + 2, z2, "cobblestone")
    d.set(mid, ridge + 2, z2, "mossy_cobblestone")
    # loft-free interior: racks under the eaves, workbench
    d.hut(mid - 2, y0, z1 + 1)
    d.item(mid - 3, y0, z1 + 1, "crafting_table")
    sides = [(x1 + 2, z) for z in range(z1 + 3, z2 - 1)] + [(x2 - 2, z) for z in range(z1 + 3, z2 - 1)]
    rack_line(d, sides, y0, min(JACK_RACKS[L], len(sides)), 1, "east")
    d.rug(mid - 1, z1 + 3, mid + 1, z2 - 3, y0, ("brown_carpet", "green_carpet"))
    d.set(mid, ridge - 2, z1 + 3, LANT)
    d.set(mid, ridge - 1, z1 + 3, lg("spruce_log", "z")) if d.air(mid, ridge - 1, z1 + 3) else None
    # front deck with railing
    dz1 = z1 - 4
    d.fill(x1 - 1, 1, dz1, x2 + 1, 1, z1 - 2, "spruce_planks")
    for x in range(x1 - 1, x2 + 2):
        d.set(x, 1, z1 - 1, "spruce_planks")
        if abs(x - mid) > 1:
            d.set(x, y0, dz1, "spruce_fence")
    for x in (x1 - 1, x2 + 1):
        for z in range(dz1, z1 - 1):
            d.set(x, y0, z, "spruce_fence")
        d.set(x, y0 + 1, dz1, LANT_S)
    if L >= 3:
        d.chair(mid - 3, y0, z1 - 2, "south", "spruce", arms=True)
        d.chair(mid + 3, y0, z1 - 2, "south", "spruce", arms=True)
    # log piles and chopping block in the yard
    log_pile(d, 0, 9, 2, 17, y0, 3, "spruce_log", "z")
    chopping_block(d, 18, 9, y0, "spruce_log")
    sawhorse(d, 18, 12, y0, "spruce", "z")
    if L >= 4:
        for x, z in ring(x1, z2 + 2, x2, 23):
            d.set(x, y0, z, "spruce_fence")
        d.set(x2, y0, 21, AIR)
        d.item(x1 + 1, y0, 22, "composter")
        d.item(x1 + 2, y0, 22, "barrel", "up")
        for x in range(x1 + 4, x2):
            d.set(x, 1, 21, "podzol[snowy=false]")
            d.set(x, y0, 21, "spruce_sapling[stage=0]")
    if L >= 5:                                                           # woodshed with the extra racks
        wx1, wx2, wz1, wz2 = 17, 21, 15, 20
        for x, z in ((wx1, wz1), (wx2, wz1), (wx1, wz2), (wx2, wz2)):
            d.fill(x, y0, z, x, 4, z, lg("spruce_log", "y"))
        for z in range(wz1 - 1, wz2 + 2):
            for x in range(wx1 - 1, wx2 + 2):
                d.set(x, 5, z, sl("dark_oak"))
        log_pile(d, wx1 + 1, wz2, wx2 - 1, wz2, y0, 2, "spruce_log", "x")
        d.rack(wx2, y0, wz1 + 2, "west")
        d.rack(wx2, y0, wz1 + 3, "west")
    return d


@design("lumberjack")
def lumberjack(pack, rel, L):
    return {"Neoterra": jack_neo, "Hearthwood": jack_hw, "Cascadia": jack_cas}[pack](rel, L)


# =============================================================================================== FLETCHER
"""
Fletcher
  Neoterra   "Archery studio": glass-fronted white studio with the fletching benches along the back wall and a
             glazed indoor/outdoor shooting lane beside it (shooting booth, targets on a hay backstop).
  Hearthwood "The Bow & Quiver": timber-framed bowyer's shop with a bay shop window and hanging sign; garden
             archery lane with straw butts behind; from L3 a stave-drying shed with arrow barrels.
  Cascadia   "Bowyer's cabin": log workshop gable-to-street with a side porch that is the shooting line of a long
             range with a hay-bale berm; grows longer, adds a stave rack and barrels.
"""
FLETCH = {1: 2, 2: 3, 3: 4, 4: 5, 5: 5}
FRACKS = {1: 2, 2: 3, 3: 4, 4: 5, 5: 6}


def butt(d, x, z, y, facing, target=True, w=2):
    """Straw archery butt: hay bales two high with target faces (one counted as the yard target)."""
    dx, dz = (1, 0) if facing in ("north", "south") else (0, 1)
    for k in range(w):
        cx, cz = x + dx * k, z + dz * k
        d.set(cx, y, cz, "hay_block[axis=y]")
        if k == 0 and target:
            d.yard_item(cx, y + 1, cz, "target[power=0]")
        else:
            d.set(cx, y + 1, cz, "target[power=0]" if k % 2 == 0 else "hay_block[axis=y]")


def fl_neo(rel, L):
    d = Design("Neoterra", rel, (25, 10, 25), paving="smooth_stone")
    x1, z1, z2 = 3, 4, 11
    x2 = 10 if L <= 2 else 12
    y0 = 2
    neo_block(d, x1, z1, x2, z2, y0, 5)
    for x in range(x1 + 1, x2):
        d.window(x, 2, z1, x, 4, z1, "glass_pane")
    d.double_door(5, y0, z1, "x", "south", "birch")
    d.sign(8, 5, z1 - 1, "north", ["ARROW", "STUDIO"], "birch", glow=True, color="cyan")
    for x in range(x1, x2 + 1):
        d.set(x, 5, z1 - 1, sl("smooth_quartz", "top"))
    d.hut(x1 + 1, y0, z1 + 1)
    d.item(x1 + 1, y0, z1 + 2, "crafting_table")
    for i in range(FLETCH[L]):
        d.item(x1 + 3 + i, y0, z2 - 1, "fletching_table")
    for i in range(FLETCH[L]):
        d.chair(x1 + 3 + i, y0, z2 - 2, "south", "birch", sit=False) if i % 2 == 0 else None
    rack_line(d, [(x1 + 1, z) for z in range(z2 - 1, z1 + 2, -1)], y0, FRACKS[L], 2, "east")
    if L >= 3:
        for i in range(5):
            d.item(x2 - 1, y0, z1 + 3 + i, "barrel", "west")
    d.set(7, 5, 7, "sea_lantern")
    d.set(x2 - 3, 5, 7, "sea_lantern")
    # shooting lane to the east, glazed sides, booth at the street end
    lx1, lx2 = 15, 19
    d.fill(lx1, 1, z1, lx2, 1, 22, "grass_block[snowy=false]")
    for z in range(z1, 23):
        for x in (lx1 - 1, lx2 + 1):
            d.set(x, y0, z, "light_gray_concrete")
            d.set(x, y0 + 1, z, "glass_pane")
            d.set(x, y0 + 2, z, "glass_pane")
            d.set(x, 1, z, "smooth_stone")
    for x in range(lx1 - 1, lx2 + 2):
        for z in range(z1, z1 + 4):
            d.set(x, 1, z, "polished_diorite")
            d.set(x, 5, z, "smooth_quartz")
        d.set(x, y0, z1 + 4, sl("smooth_quartz", "top"))        # shooting line counter
    for z in range(z1, z1 + 4):
        for x in (lx1 - 1, lx2 + 1):
            d.fill(x, y0, z, x, 4, z, "white_concrete" if z in (z1, z1 + 3) else "glass_pane")
    for x in range(lx1, lx2 + 1):
        d.set(x, y0, z1, AIR) if x != lx1 + 2 else None
        d.set(x, y0 + 1, z1, AIR)
    d.set(lx1 + 2, y0, z1 + 4, AIR)
    d.set(lx1 + 2, y0, z1 + 4, "birch_fence_gate[facing=north,in_wall=false,open=true,powered=false]")
    d.set(lx1, 4, z1 + 2, "sea_lantern")
    d.set(lx2, 4, z1 + 2, "sea_lantern")
    for x in range(lx1 - 1, lx2 + 2):
        d.set(x, y0, 23, "hay_block[axis=x]")
        d.set(x, y0 + 1, 23, "hay_block[axis=x]")
    butt(d, lx1, 22, y0, "north")
    butt(d, lx2 - 1, 22, y0, "north", target=False)
    return d


def fl_hw(rel, L):
    d = Design("Hearthwood", rel, (23, 17, 27), paving="gravel")
    x1, z1, x2, z2 = 4, 4, 13, 10
    y0 = 2
    hw_walls(d, x1, z1, x2, z2, y0, 5)
    ridge = d.gable(x1, z1, x2, z2, 6, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite")
    # bay shop window
    for x in range(6, 10):
        d.set(x, y0, z1 - 1, "dark_oak_planks")
        d.window(x, 3, z1 - 1, x, 4, z1 - 1)
        d.set(x, 5, z1 - 1, sl("deepslate_tile", "bottom"))
    for x in range(6, 10):
        d.set(x, 3, z1, AIR)
        d.set(x, 4, z1, AIR)
    d.door(11, y0, z1, "south", "dark_oak")
    d.sign(12, 4, z1 - 1, "north", ["The Bow", "& Quiver"], "dark_oak", hanging=True)
    win(d, x1, 3, 7)
    win(d, x2, 3, 7)
    d.door(8, y0, z2, "north", "dark_oak")
    d.hut(x1 + 1, y0, z1 + 1)
    d.item(x1 + 1, y0, z1 + 2, "crafting_table")
    # display of bows in the bay: armour-less, so racks of arrows (fletching tables) behind the counter
    for x in range(6, 10):
        d.set(x, y0, z1, sl("dark_oak", "top"))
    for i in range(FLETCH[L]):
        d.item(x1 + 1 + i if i < 3 else x2 - 1, y0, z2 - 1 if i < 3 else z2 - 1 - (i - 3) - 1, "fletching_table")
    d.chair(x1 + 2, y0, z2 - 2, "south", "dark_oak", sit=False)
    rack_line(d, [(x2 - 1, z) for z in range(z1 + 1, z1 + 4)], y0, min(FRACKS[L], 3), 1, "west")
    d.set(8, 5, 7, LANT)
    d.rug(6, 6, 9, 7, y0, ("green_carpet", "brown_carpet"))
    # back garden: archery lane with straw butts
    gz1, gz2 = z2 + 1, 24
    for x, z in ring(x1 - 2, gz1, x2 + 2, gz2):
        if z == gz1 and x1 <= x <= x2:
            continue
        d.set(x, y0, z, "oak_fence")
    d.set(x1 - 2, y0, gz1 + 2, AIR)
    d.fill(6, 1, gz1, 10, 1, gz2 - 1, "grass_block[snowy=false]")
    butt(d, 6, gz2 - 2, y0, "north")
    butt(d, 9, gz2 - 2, y0, "north", target=False)
    for x in range(6, 11):
        d.set(x, 1, gz1 + 2, "stone_bricks")                        # shooting mark
    d.set(x1 - 1, y0, gz1 + 4, "rose_bush[half=lower]")
    d.set(x1 - 1, y0 + 1, gz1 + 4, "rose_bush[half=upper]")
    if L >= 3:                                                       # stave-drying shed with arrow barrels
        sx1, sx2, sz1, sz2 = 14, 19, 12, 20
        hw_walls(d, sx1, sz1, sx2, sz2, y0, 4, floor="spruce_planks", step=2)
        d.gable(sx1, sz1, sx2, sz2, 5, "z", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite")
        for y in (y0, y0 + 1):
            d.set(sx1, y, sz1 + 2, AIR)
        d.set(sx1, y0, sz1 + 2, AIR)
        for i in range(5):
            d.item(sx2 - 1, y0, sz1 + 1 + i, "barrel", "west")
        rack_line(d, [(sx1 + 1, z) for z in range(sz2 - 1, sz1 + 3, -1)], y0, FRACKS[L] - 3, 1, "east")
        d.set(sx1 + 3, 4, sz1 + 4, LANT)
        d.fill(sx1 - 1, 1, sz1 + 2, sx1 - 1, 1, sz1 + 2, "spruce_planks")
        d.fill(x2 + 1, y0, 11, x2 + 2, y0, 11, AIR)
    return d


def fl_cas(rel, L):
    d = Design("Cascadia", rel, (27, 16, 23), paving="coarse_dirt")
    x1, x2, z1 = 3, 11, 5
    z2 = {1: 12, 2: 12, 3: 14, 4: 14, 5: 16}[L]
    y0 = 2
    cas_walls(d, x1, z1, x2, z2, y0, 5)
    ridge = d.gable(x1, z1, x2, z2, 6, "z", "dark_oak_stairs", "dark_oak_slab", "spruce_planks")
    mid = (x1 + x2) // 2
    d.door(mid, y0, z1, "south", "spruce")
    for x in (mid - 2, mid + 2):
        win(d, x, 3, z1)
        shutters(d, x, 3, z1, "north")
    win(d, mid, ridge - 3, z1, 1)
    d.door(x2, y0, z1 + 3, "west", "spruce")
    win(d, x2, 3, z1 + 5)
    if z2 > 13:
        win(d, x2, 3, z2 - 2)
    win(d, x1, 3, z1 + 3)
    # crossed-arrows sign
    d.sign(mid, 5, z1 - 1, "north", ["BOWS", "& ARROWS"], "spruce")
    d.hut(x1 + 1, y0, z1 + 1)
    d.item(x1 + 1, y0, z1 + 2, "crafting_table")
    for i in range(FLETCH[L]):
        d.item(x1 + 1, y0, z1 + 4 + i, "fletching_table")
    d.chair(x1 + 2, y0, z1 + 5, "west", "spruce", sit=False)
    rack_line(d, [(x, z2 - 1) for x in range(x1 + 1, x2)], y0, FRACKS[L], 1)
    if L >= 3:
        for i, (x, z) in enumerate([(x2 - 1, z1 + 1), (x2 - 2, z1 + 1), (x2 - 3, z1 + 1), (x2 - 1, z1 + 2),
                                    (x2 - 1, z1 + 6)]):
            d.item(x, y0, z, "barrel", "up")
    d.set(mid, 5, z1 + 4, LANT)
    d.set(mid, 5, z2 - 3, LANT)
    # side porch = shooting line, range to the east with a hay-bale berm
    px1, px2 = x2 + 1, x2 + 3
    for x in range(px1, px2 + 1):
        for z in range(z1, z2 + 1):
            d.set(x, 1, z, "spruce_planks")
    for z in range(z1, z2 + 1):
        for x in range(px1, px2 + 2):
            d.set(x, 5, z, sl("spruce", "top") if x == px1 else sl("spruce", "bottom"))
    for z in (z1, z2):
        d.fill(px2, y0, z, px2, 4, z, lg("spruce_log", "y"))
    for z in range(z1 + 1, z2):
        if z not in (z1 + 1,):
            d.set(px2, y0, z, "spruce_fence")
    d.set(px2, 4, z1 + 4, LANT)
    rz1, rz2 = 6, 11
    for x in range(px2 + 1, 26):
        for z in (rz1 - 1, rz2 + 1):
            d.set(x, y0, z, "spruce_fence")
    for z in range(rz1 - 1, rz2 + 2):
        for y in (y0, y0 + 1, y0 + 2):
            d.set(25, y, z, "hay_block[axis=z]")
        d.set(26, y0, z, "hay_block[axis=z]")
    butt(d, 24, rz1 + 1, y0, "west", w=1)
    d.set(24, y0, rz2 - 1, "hay_block[axis=y]")
    d.set(24, y0 + 1, rz2 - 1, "target[power=0]")
    for x in range(px2 + 2, 24, 4):
        d.set(x, y0, rz1 - 1, "spruce_fence")
        d.set(x, y0 + 1, rz1 - 1, "torch")
    if L >= 2:                                                       # stave drying rack
        for z in (z2 + 2, z2 + 5):
            d.fill(x1 + 1, y0, z, x1 + 1, y0 + 1, z, "spruce_fence")
            d.fill(x1 + 5, y0, z, x1 + 5, y0 + 1, z, "spruce_fence")
            for x in range(x1 + 1, x1 + 6):
                d.set(x, y0 + 2, z, lg("stripped_spruce_log", "x"))
    return d


@design("fletcher")
def fletcher(pack, rel, L):
    return {"Neoterra": fl_neo, "Hearthwood": fl_hw, "Cascadia": fl_cas}[pack](rel, L)


# =============================================================================================== WAREHOUSE
"""
Warehouse
  Neoterra   "Logistics hub": white concrete storage block with clerestory glazing, glowing roof sign and solar
             roof; rack aisles (3 high) behind a front office strip; widens at L3, adds a racked upper floor at
             L4, truck bay with pallets beside it.
  Hearthwood "Tithe barn": long stone barn with buttresses, gable to the street and a gabled cart porch; a central
             nave with cross-aisles of rack bays either side; grows a bay pair per level.
  Cascadia   "Freight depot": long board-and-batten depot on a raised timber loading dock with a canopy and rail
             siding along the street; rack aisles run back from the dock; grows sideways along the track.
"""
WH = {1: 36, 2: 72, 3: 144, 4: 216, 5: 324}


def wh_office(d, L, cells, desk):
    """Office furniture for a warehouse: cells = list of (x, y, z, facing) for the work blocks in order,
    desk = (x, y, z, chair side, chair side) table and two chairs."""
    items = ["crafting_table"]
    if L >= 3:
        items += ["cartography_table", "lectern", "crafting_table", "barrel", "barrel", "barrel", "barrel"]
    if L >= 5:
        items.append("ender_chest")
    for (x, y, z, f), it in zip(cells, items):
        d.item(x, y, z, it, f if it != "barrel" else "up")
    if L >= 3:
        x, y, z, a, b = desk
        d.table(x, y, z, kind="slab")
        for side in (a, b):
            dx, dz = D4[side]
            d.chair(x + dx, y, z + dz, side)
    return len(items)


def wh_neo(rel, L):
    d = Design("Neoterra", rel, (25, 16, 21), paving="smooth_stone")
    x1, z1, z2 = 3, 4, 16
    x2 = 11 if L <= 2 else 17
    up = L >= 4
    y0 = 2
    ytop = 10 if up else 5
    neo_block(d, x1, z1, x2, z2, y0, ytop, floors=(6,) if up else (), floor="smooth_stone")
    # clerestory glazing above the racks, full glass office front
    for z in (z1, z2):
        neo_ribbon(d, x1 + 1, z, x2 - 1, z, 5, 5, "light_gray_stained_glass_pane", every=3)
    for x in (x1, x2):
        neo_ribbon(d, x, z1 + 1, x, z2 - 1, 5, 5, "light_gray_stained_glass_pane", every=3)
    if up:
        for z in (z1, z2):
            neo_ribbon(d, x1 + 1, z, x2 - 1, z, 9, 9, "light_gray_stained_glass_pane", every=3)
    for x in range(x1 + 1, 11):
        d.window(x, 2, z1, x, 4, z1, "glass_pane")
    d.door(8, y0, z1, "south", "birch")
    d.set(8, 4, z1, "white_concrete")
    if L >= 3:                                                       # loading bay with roller door frame
        for x in range(12, 15):
            for y in range(y0, 5):
                d.set(x, y, z1, AIR)
        for x in (11, 15):
            d.fill(x, y0, z1 - 1, x, 4, z1 - 1, "yellow_concrete")
            d.set(x, y0, z1 - 2, "black_concrete")
            d.set(x, y0 + 1, z1 - 2, "yellow_concrete")
        for x in range(11, 16):
            d.set(x, 5, z1 - 1, "light_gray_concrete")
            d.set(x, 5, z1 - 2, sl("smooth_quartz", "top"))
        for x in range(12, 15):
            d.set(x, 4, z1, "iron_trapdoor[facing=south,half=top,open=false,powered=false,waterlogged=false]")
    d.sign((x1 + x2) // 2, ytop, z1 - 1, "north", ["NEOTERRA", "LOGISTICS"], "birch", glow=True, color="cyan")
    d.hut(x1 + 1, y0, z1 + 1)
    # office strip z5..7, cross aisle z8, racks z9..15
    cells = [(x1 + 2, y0, z1 + 1, "north"), (x1 + 3, y0, z1 + 1, "north"), (x1 + 4, y0, z1 + 1, "north"),
             (9, y0, z1 + 1, "north"), (10, y0, z1 + 1, "north"), (10, y0, z1 + 2, "west"),
             (10, y0, z1 + 3, "west"), (x1 + 1, y0, z1 + 3, "east"), (x1 + 1, y0, z1 + 2, "east")]
    wh_office(d, L, cells, (6, y0, z1 + 3, "west", "east"))
    n = aisles(d, x1 + 1, z1 + 5, x2 - 1, z2 - 1, y0, min(WH[L], 168))
    for x in range(x1 + 1, x2, 3):
        for z in range(z1 + 6, z2, 3):
            d.set(x, 6 if up else ytop + 1, z, "pearlescent_froglight[axis=y]" if up else "sea_lantern")
    if up:
        sx = 12
        run_stairs(d, sx, z1 + 3, y0, 4, "east", "smooth_quartz", fill="smooth_quartz")
        for x in range(sx, sx + 4):
            d.set(x, 7, z1 + 2, "glass_pane")
        n += aisles(d, x1 + 1, z1 + 5, x2 - 1, z2 - 1, 7, WH[L] - n)
        for x in range(x1 + 1, x2, 3):
            for z in range(z1 + 6, z2, 3):
                d.set(x, 11, z, "sea_lantern")
        d.set(x1 + 2, 7, z1 + 1, "potted_bamboo")
    # roof: solar
    if L >= 3:
        for x in range(x1 + 2, x2 - 1, 2):
            for z in range(z1 + 2, z2 - 1):
                d.set(x, ytop + 2, z, "daylight_detector[inverted=false,power=0]")
    # truck bay / pallets
    bx = x2 + 2
    for z in range(z1, z2 + 1, 4):
        d.set(bx + 2, 1, z, "yellow_concrete")
    if bx + 4 < d.sx:
        for z in (z1 + 1, z1 + 2):
            d.keg(bx + 3, y0, z, "up" if z % 2 else "north")
        d.set(bx + 3, y0, z1 + 6, "oak_planks")
        d.set(bx + 3, y0 + 1, z1 + 6, "barrel[facing=up,open=false]")
    return d


def wh_hw(rel, L):
    d = Design("Hearthwood", rel, (21, 23, 30), paving="gravel")
    x1, x2, z1 = 3, 17, 4
    U = {1: 1, 2: 2, 3: 3, 4: 4, 5: 6}[L]
    z2 = 9 + 3 * U
    y0 = 2
    d.box(x1, y0, z1, x2, 6, z2, "stone_bricks", floor="spruce_planks")
    for x, z in ring(x1, z1, x2, z2):
        for y in range(y0, 7):
            h = (x * 13 + y * 5 + z * 7) % 9
            if h < 2:
                d.set(x, y, z, "cobblestone" if h == 0 else "mossy_stone_bricks")
        d.set(x, y0, z, "cobblestone")
    # buttresses along the long sides
    for z in range(z1 + 3, z2, 3):
        for x, f in ((x1 - 1, "east"), (x2 + 1, "west")):
            d.fill(x, y0, z, x, 4, z, "stone_bricks")
            d.set(x, 5, z, st("stone_brick", f))
    for z in range(z1 + 3, z2, 6):
        for x in (x1, x2):
            d.set(x, 5, z + 1, "glass_pane")
            d.set(x, 4, z + 1, "glass_pane")
    ridge = d.gable(x1, z1, x2, z2, 7, "z", "deepslate_tile_stairs", "deepslate_tile_slab", "stone_bricks")
    # tie beams + lanterns over the nave
    for z in range(z1 + 2, z2, 3):
        for x in range(x1 + 1, x2):
            d.set(x, 7, z, lg("stripped_dark_oak_log", "x"))
        d.set(10, 6, z, LANT)
    # cart porch (midstrey)
    for z in range(z1 - 3, z1):
        for y in range(y0, 6):
            d.set(8, y, z, "stone_bricks")
            d.set(12, y, z, "stone_bricks")
        d.set(8, 1, z, "stone_bricks")
        d.set(12, 1, z, "stone_bricks")
        for x in range(9, 12):
            d.set(x, 1, z, "spruce_planks")
    d.gable(8, z1 - 3, 12, z1 - 1, 6, "z", "deepslate_tile_stairs", "deepslate_tile_slab", "stone_bricks", overhang=0)
    for x in range(9, 12):
        for y in range(y0, 5):
            d.set(x, y, z1, AIR)
            d.set(x, y, z1 - 3, AIR)
        d.set(x, 5, z1 - 3, lg("stripped_dark_oak_log", "x"))
        d.set(x, 5, z1, lg("stripped_dark_oak_log", "x"))
    d.set(10, ridge - 3, z1, "glass_pane")
    d.sign(9, 4, z1 - 4, "north", ["Tithe Barn", "Stores"], "dark_oak")
    d.set(7, y0 + 2, z1 - 1, "wall_torch[facing=north]")
    d.set(13, y0 + 2, z1 - 1, "wall_torch[facing=north]")
    d.hut(x1 + 1, y0, z1 + 1)
    cells = [(x1 + 2, y0, z1 + 1, "north"), (x1 + 3, y0, z1 + 1, "north"), (x1 + 4, y0, z1 + 1, "north"),
             (x2 - 1, y0, z1 + 1, "north"), (x2 - 1, y0, z1 + 2, "west"), (x2 - 2, y0, z1 + 1, "west"),
             (x2 - 3, y0, z1 + 1, "west"), (x2 - 1, y0, z1 + 3, "west"), (x1 + 1, y0, z1 + 3, "east")]
    wh_office(d, L, cells, (x1 + 3, y0, z1 + 3, "south", "east"))
    # rack bays: double rows across the barn either side of the 3-wide nave, cross aisles between
    n = 0
    for u in range(U):
        za = 9 + 3 * u
        for z in (za, za + 1):
            for x in list(range(x1 + 1, 9)) + list(range(12, x2)):
                if n < WH[L]:
                    n += rack_col(d, x, z, y0)
    return d


def wh_cas(rel, L):
    d = Design("Cascadia", rel, (29, 19, 23), paving="coarse_dirt")
    x1, z1, z2 = 3, 6, 19
    U = L
    x2 = 9 + 3 * U
    y0 = 3                                                           # raised floor at dock height
    d.fill(x1, 2, z1, x2, 2, z2, "cobblestone")
    d.box(x1, y0, z1, x2, 7, z2, "spruce_planks", floor="spruce_planks")
    for x, z in ring(x1, z1, x2, z2):
        if (x + z) % 2 == 0:
            for y in range(y0, 8):
                d.set(x, y, z, lg("stripped_spruce_log", "y"))
        d.set(x, 2, z, "mossy_cobblestone" if (x * 3 + z) % 5 == 0 else "cobblestone")
    for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        d.fill(x, y0, z, x, 7, z, lg("spruce_log", "y"))
    ridge = d.gable(x1, z1, x2, z2, 8, "x", "dark_oak_stairs", "dark_oak_slab", "spruce_planks")
    # dock: raised deck with canopy, steps at the west end, rail siding along the street
    for x in range(x1, x2 + 1):
        for z in range(2, z1):
            d.set(x, 1, z, "cobblestone")
            d.set(x, 2, z, "spruce_planks")
    for x in range(x1, x2 + 1, 4):
        d.fill(x, y0, 2, x, 6, 2, lg("spruce_log", "y"))
    d.fill(x2, y0, 2, x2, 6, 2, lg("spruce_log", "y"))
    for x in range(x1 - 1, x2 + 2):
        d.set(x, 7, 1, st("dark_oak", "south"))
        for z in range(2, z1):
            d.set(x, 7, z, sl("dark_oak", "bottom" if z < 4 else "top"))
    d.set(x1 - 1, 2, 3, st("spruce", "east"))
    d.set(x1 - 1, 2, 4, st("spruce", "east"))
    for x in range(0, d.sx):
        d.set(x, 1, 0, "gravel")
        d.set(x, 2, 0, "rail[shape=east_west,waterlogged=false]")
    # doors: office door + sliding freight doors at each aisle bay
    d.door(5, y0, z1, "south", "spruce")
    win(d, 7, 4, z1)
    for u in range(U):
        ax = 11 + 3 * u
        for y in range(y0, 6):
            d.set(ax, y, z1, AIR)
    for u in range(U):
        ax = 11 + 3 * u
        d.set(ax, 6, z1 - 1, LANT)
    d.sign(6, 6, z1 - 1, "north", ["FREIGHT", "DEPOT"], "spruce")
    d.set(x1 + 1, y0, 3, "barrel[facing=north,open=false]")
    d.set(x1 + 1, y0 + 1, 3, "barrel[facing=up,open=false]")
    d.set(x2 - 1, y0, 3, "hay_block[axis=x]")
    d.hut(x1 + 1, y0, z1 + 1)
    cells = [(x1 + 1, y0, z1 + 3, "east"), (x1 + 1, y0, z1 + 4, "east"), (x1 + 1, y0, z1 + 5, "east"),
             (x1 + 1, y0, z1 + 6, "east"), (x1 + 1, y0, z2 - 1, "east"), (x1 + 2, y0, z2 - 1, "north"),
             (x1 + 3, y0, z2 - 1, "north"), (x1 + 4, y0, z2 - 1, "north"), (x1 + 1, y0, z1 + 7, "east")]
    wh_office(d, L, cells, (x1 + 3, y0, z1 + 9, "north", "south"))
    d.set(x1 + 2, 7, z1 + 5, LANT)
    n = aisles(d, 8, z1 + 2, x2 - 1, z2 - 1, y0, WH[L])
    for u in range(U + 1):
        ax = 8 + 3 * u
        for z in range(z1 + 3, z2, 4):
            d.set(ax, 7, z, LANT) if d.air(ax, 7, z) and not d.air(ax, 8, z) else None
    for x in range(8, x2, 3):
        for z in range(z1 + 1, z2):
            d.set(x, 8, z, lg("stripped_spruce_log", "z"))
        for z in range(z1 + 3, z2, 4):
            d.set(x, 7, z, LANT)
    return d


@design("warehouse")
def warehouse(pack, rel, L):
    return {"Neoterra": wh_neo, "Hearthwood": wh_hw, "Cascadia": wh_cas}[pack](rel, L)


# =============================================================================================== DELIVERYMAN
"""
Deliveryman
  Neoterra   "Courier depot": glass-fronted parcel shop with a customer counter and a full-height sorting wall of
             parcel barrels; waiting seats; from L3 an upper dispatch office/archive (bookshelves), L4 crew bunk;
             loading canopy with parcel stacks beside it.
  Hearthwood "Post house & coaching stables": timber-framed post office with a pigeonhole sorting wall behind
             the counter, coaching stables (stalls, hay, tack/feed barrels) across the yard from L2, postmaster's
             office upstairs from L3.
  Cascadia   "Express & freight office": log office on a deep porch with hitching rail and freight barrels,
             stable lean-to with stalls from L2, back records room (bookshelves, bunk) from L3.
"""
DLV = {1: 8, 2: 31, 3: 41, 4: 41, 5: 41}
DSEAT = {1: 0, 2: 3, 3: 6, 4: 6, 5: 6}


def barrel_wall(d, cells, y, need, facing, h=3):
    """Pigeonhole wall: barrels lying with their lids facing into the room, `h` high."""
    n = 0
    for x, z in cells:
        for k in range(h):
            if n >= need:
                return n
            d.item(x, y + k, z, "barrel", facing)
            n += 1
    return n


def stall(d, x1, z1, x2, z2, y, fence, hay=True):
    """Horse stall: fence partitions on its x1/x2 sides, hay bale + water trough at the back (z2)."""
    for z in range(z1, z2 + 1):
        d.set(x1, y, z, fence)
        d.set(x2, y, z, fence)
    if hay:
        d.set(x1 + 1, y, z2, "hay_block[axis=x]")
    if x2 - x1 > 2:
        d.set(x2 - 1, y, z2, "water_cauldron[level=3]")


def dl_neo(rel, L):
    d = Design("Neoterra", rel, (23, 15, 21), paving="smooth_stone")
    x1, z1, x2, z2 = 3, 4, 15, 13
    y0 = 2
    up = L >= 3
    ytop = 10 if up else 5
    neo_block(d, x1, z1, x2, z2, y0, ytop, floors=(6,) if up else (), band="orange_terracotta")
    for x in range(x1 + 1, x2):
        d.window(x, 2, z1, x, 4, z1, "glass_pane")
        if up:
            d.window(x, 8, z1, x, 9, z1, "light_gray_stained_glass_pane")
    d.double_door(7, y0, z1, "x", "south", "birch")
    for x in range(x1, x2 + 1):
        d.set(x, 5, z1 - 1, sl("smooth_quartz", "top"))
        d.set(x, 5, z1, "orange_concrete")
    d.sign(9, 6, z1 - 1, "north", ["NEO", "COURIER"], "birch", glow=True, color="orange")
    d.sign(5, 6, z1 - 1, "north", ["PARCELS", "& POST"], "birch", glow=True, color="cyan")
    neo_ribbon(d, x1, z1 + 1, x1, z2 - 1, 3, 4)
    d.hut(x1 + 1, y0, z1 + 1)
    # sorting wall on the back wall, more on the east wall
    cells = [(x, z2 - 1) for x in range(x1 + 1, x2 - 1)]
    n = barrel_wall(d, cells, y0, DLV[L], "north")
    if n < DLV[L]:
        n += barrel_wall(d, [(x2 - 1, z) for z in range(z2 - 2, z2 - 5, -1)], y0, DLV[L] - n, "west")
    if n < DLV[L]:                                                   # parcel scales / sorting bench barrels
        n += barrel_wall(d, [(x1 + 5, z1 + 5), (x1 + 6, z1 + 5)], y0, DLV[L] - n, "up", 1)
    # counter across the shop with a flap
    for x in range(x1 + 1, x2 - 3):
        d.set(x, y0, z1 + 3, sl("smooth_quartz", "top") if x != x1 + 1 else "quartz_block")
    d.set(x2 - 3, y0, z1 + 3, "birch_fence_gate[facing=east,in_wall=false,open=true,powered=false]")
    d.item(x1 + 1, y0, z1 + 5, "crafting_table")
    d.item(x1 + 2, y0, z1 + 5, "cartography_table")
    if L >= 2:
        d.item(x1 + 3, y0, z1 + 5, "lectern", "north")
    if L >= 5:
        d.item(x1 + 4, y0, z1 + 5, "ender_chest", "north")
    # waiting bench at the window
    seats = 0
    for x in range(x1 + 7, x1 + 7 + min(DSEAT[L], 3)):
        d.chair(x, y0, z1 + 1, "north", "birch")
        seats += 1
    d.plant(x1 + 2, y0, z1 + 1, "potted_bamboo")
    for x in (6, 10):
        d.set(x, 5 if not up else 5, 8, "sea_lantern")
    if up:
        run_stairs(d, x2 - 1, z1 + 1, y0, 4, "south", "smooth_quartz", fill="smooth_quartz")
        for z in range(z1 + 1, z1 + 5):
            d.set(x2 - 2, 7, z, "glass_pane")
        yb = 7
        for z in range(z1 + 1, z1 + 7):
            d.bookshelf(x1 + 1, yb, z, 2)
        d.item(x1 + 2, yb, z2 - 1, "lectern", "north")
        d.item(x1 + 3, yb, z2 - 1, "cartography_table")
        d.table(7, yb, 7, kind="slab", top="smooth_quartz_slab")
        d.table(8, yb, 7, kind="slab", top="smooth_quartz_slab")
        d.chair(7, yb, 6, "north", "birch")
        d.chair(8, yb, 6, "north", "birch")
        d.chair(9, yb, 7, "east", "birch")
        if L >= 4:
            d.bed(x2 - 2, yb, z2 - 1, "south")
            d.set(x2 - 3, yb, z2 - 1, sl("birch", "top"))
        for x in (6, 10):
            d.set(x, 10, 8, "sea_lantern")
    # loading canopy with parcel stacks (east)
    if L >= 2:
        for z in (z1 + 1, z2 - 1):
            d.fill(x2 + 4, y0, z, x2 + 4, 4, z, "light_gray_concrete")
        for x in range(x2 + 1, x2 + 6):
            for z in range(z1 + 1, z2):
                d.set(x, 5, z, sl("smooth_quartz", "top"))
        d.door(x2, y0, 8, "east", "birch")
        for z in (z1 + 2, z1 + 3):
            d.keg(x2 + 2, y0, z, "up")
            d.keg(x2 + 2, y0 + 1, z, "north")
        d.set(x2 + 3, 1, z2 - 2, "yellow_concrete")
        d.set(x2 + 3, 1, z2 - 3, "yellow_concrete")
    return d


def dl_hw(rel, L):
    d = Design("Hearthwood", rel, (27, 18, 23), paving="gravel")
    x1, z1, x2, z2 = 3, 4, 13, 11
    y0 = 2
    up = L >= 3
    hw_walls(d, x1, z1, x2, z2, y0, 5)
    for x in range(x1, x2 + 1):
        d.set(x, y0, z1, "bricks")
    if up:
        d.fill(x1, 6, z1 - 1, x2, 6, z2, "dark_oak_planks")
        d.fill(x1 + 1, 6, z1, x2 - 1, 6, z2 - 1, "spruce_planks")
        hw_walls(d, x1, z1 - 1, x2, z2, 7, 9, floor=None, base=None, step=2)
        for x in range(x1, x2 + 1, 2):
            d.set(x, 5, z1 - 1, st("dark_oak", "south", "top"))
        ridge = d.gable(x1, z1 - 1, x2, z2, 10, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite")
        for x in (5, 8, 11):
            win(d, x, 8, z1 - 1)
    else:
        ridge = d.gable(x1, z1, x2, z2, 6, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite")
    for x in (5, 6, 10, 11):
        win(d, x, 3, z1)
    d.door(8, y0, z1, "south", "dark_oak")
    d.sign(9, 4, z1 - 1, "north", ["Royal Mail", "Post House"], "dark_oak")
    d.set(7, y0, z1 - 1, "red_concrete")                               # pillar box
    d.set(7, y0 + 1, z1 - 1, "red_terracotta")
    d.hearth(x1 + 1, y0, 8, "east", ridge + 2, "bricks", "campfire")
    d.fill(x1, y0, 8, x1, ridge + 2, 8, "bricks")
    d.hut(x1 + 1, y0, z1 + 1)
    # counter + pigeonhole wall
    for x in range(x1 + 4, x2):
        d.set(x, y0, z1 + 3, sl("dark_oak", "top"))
    cells = [(x, z2 - 1) for x in range(x1 + 4, x2)]
    n = barrel_wall(d, cells, y0, min(DLV[L], 27), "north")
    d.item(x2 - 1, y0, z1 + 4, "crafting_table")
    d.item(x2 - 1, y0, z1 + 5, "cartography_table")
    if L >= 2:
        d.item(x2 - 1, y0, z1 + 6, "lectern", "west")
    if L >= 5:
        d.item(x1 + 5, y0, z1 + 4, "ender_chest", "north")
    seats = 0
    for x in range(x1 + 6, x1 + 6 + min(DSEAT[L], 3)):
        d.chair(x, y0, z1 + 1, "north", "dark_oak")
    d.set(8, 5, 7, LANT)
    if up:
        run_stairs(d, x1 + 2, z1 + 1, y0, 4, "south", "dark_oak", fill="dark_oak_planks")
        for z in range(z1 + 1, z1 + 4):
            d.set(x1 + 3, 7, z, "dark_oak_fence")
        yb = 7
        for x in range(x1 + 3, x2 - 1):
            d.bookshelf(x, yb, z2 - 1, 2)
        d.item(x2 - 1, yb, z2 - 1, "lectern", "west")
        d.item(x2 - 1, yb, z1 + 3, "cartography_table")
        d.table(8, yb, z1 + 2, "dark_oak")
        d.chair(7, yb, z1 + 2, "west", "dark_oak")
        d.chair(9, yb, z1 + 2, "east", "dark_oak")
        d.chair(8, yb, z1 + 1, "north", "dark_oak")
        if L >= 4:
            d.bed(x2 - 1, yb, z1, "north")
            d.set(x2 - 2, yb, z1, sl("dark_oak", "top"))
            d.candle(x2 - 2, yb + 1, z1, 1)
        d.set(8, 9, 7, LANT)
    # coaching stables across the yard (L2+)
    if L >= 2:
        sx1, sx2, sz1, sz2 = 16, 24, 4, 12
        d.box(sx1, y0, sz1, sx2, 4, sz2, "bricks", floor="spruce_planks")
        for x in range(sx1, sx2 + 1, 2):
            for z in (sz1, sz2):
                d.fill(x, y0 + 1, z, x, 4, z, lg("stripped_dark_oak_log", "y"))
        for z in range(sz1, sz2 + 1, 2):
            d.fill(sx1, y0 + 1, z, sx1, 4, z, lg("stripped_dark_oak_log", "y"))
        rg = d.gable(sx1, sz1, sx2, sz2, 5, "z", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite")
        for z in (sz1 + 2, sz1 + 6):                                   # stable doors on the yard side
            for y in (y0, y0 + 1):
                d.set(sx1, y, z, AIR)
            d.set(sx1, y0 + 2, z, lg("stripped_dark_oak_log", "z"))
        # stalls along the east wall
        for zz in range(sz1 + 1, sz2 - 1, 3):
            for x in range(sx2 - 4, sx2):
                d.set(x, y0, zz, "dark_oak_fence")
            d.set(sx2 - 1, y0, zz + 1, "hay_block[axis=x]")
            d.set(sx2 - 1, y0, zz + 2, "water_cauldron[level=3]") if zz + 2 < sz2 else None
        # tack & feed barrels along the west side
        need = DLV[L] - n
        n += barrel_wall(d, [(sx1 + 1, z) for z in (sz1 + 1, sz1 + 3, sz1 + 4, sz1 + 5, sz1 + 7)], y0, need,
                         "east", h=3 if need > 5 else 1)
        n += barrel_wall(d, [(x, sz2 - 1) for x in range(sx1 + 2, sx2 - 4)] + [(sx1 + 2, sz1 + 1), (sx1 + 3, sz1 + 1)],
                         y0, DLV[L] - n, "north", 2)
        d.set(20, 4, 8, LANT)
        d.set(20, 1, sz1 - 1, "gravel")
        # mounting block & trough in the yard
        d.set(15, y0, 14, "stone_bricks")
        d.set(15, y0, 15, st("stone_brick", "north"))
        for x in range(17, 20):
            d.set(x, y0, 14, "water_cauldron[level=3]" if x == 18 else "spruce_planks")
    return d


def dl_cas(rel, L):
    d = Design("Cascadia", rel, (27, 16, 25), paving="coarse_dirt")
    x1, z1, x2 = 3, 7, 12
    z2 = 14 if L < 3 else 19
    y0 = 2
    cas_walls(d, x1, z1, x2, z2, y0, 5)
    if L >= 3:
        for x in range(x1 + 1, x2):
            d.set(x, y0, 14, lg("stripped_spruce_log", "x"))
            d.set(x, y0 + 1, 14, lg("stripped_spruce_log", "x"))
            d.set(x, y0 + 2, 14, lg("stripped_spruce_log", "x"))
            d.set(x, y0 + 3, 14, lg("stripped_spruce_log", "x"))
        d.door(x1 + 2, y0, 14, "south", "spruce")
    ridge = d.gable(x1, z1, x2, z2, 6, "z", "dark_oak_stairs", "dark_oak_slab", "spruce_planks")
    mid = (x1 + x2) // 2
    # false front
    for x in range(x1 - 1, x2 + 2):
        for y in range(6, ridge + 2):
            d.set(x, y, z1 - 1, "spruce_planks" if x not in (x1 - 1, x2 + 1) else lg("spruce_log", "y"))
        d.set(x, ridge + 2, z1 - 1, sl("dark_oak"))
    d.sign(mid, ridge - 1, z1 - 2, "north", ["EXPRESS", "& FREIGHT"], "spruce")
    d.door(mid, y0, z1, "south", "spruce")
    for x in (x1 + 2, x2 - 2):
        win(d, x, 3, z1)
    win(d, x1, 3, z1 + 3)
    # porch with hitching rail
    pz = z1 - 4
    for x in range(x1 - 1, x2 + 2):
        for z in range(pz, z1 - 1):
            d.set(x, 1, z, "spruce_planks")
        d.set(x, 1, z1 - 1, "spruce_planks")
    for x in (x1 - 1, x2 + 1, mid - 2, mid + 2):
        d.fill(x, y0, pz, x, 4, pz, lg("spruce_log", "y"))
    for x in range(x1 - 2, x2 + 3):
        for z in range(pz, z1 - 1):
            d.set(x, 5, z, sl("dark_oak"))
        d.set(x, 5, pz - 1, st("dark_oak", "south"))
    for x in range(x1 + 1, x2):
        if abs(x - mid) > 1:
            d.set(x, y0, pz - 2, "spruce_fence")
    d.hut(x1 + 1, y0, z1 + 1)
    # freight office: counter, barrel wall at the back (or partition), porch barrels
    for x in range(x1 + 1, x2 - 2):
        d.set(x, y0, z1 + 3, sl("spruce", "top"))
    d.item(x2 - 1, y0, z1 + 1, "crafting_table")
    d.item(x2 - 1, y0, z1 + 2, "cartography_table")
    if L >= 2:
        d.item(x2 - 1, y0, z1 + 3, "lectern", "west")
    if L >= 5:
        d.item(x1 + 1, y0, z1 + 5, "ender_chest", "east")
    bz = 13
    n = barrel_wall(d, [(x, bz) for x in range(x1 + 1, x2) if x != x1 + 2], y0, DLV[L], "north")
    n += barrel_wall(d, [(x1 + 1, z1 + 4)], y0, DLV[L] - n, "east")
    seats = 0
    if DSEAT[L] >= 3:
        d.chair(x1 + 1, y0, z1 - 2, "south", "spruce")
        d.chair(x1 + 2, y0, z1 - 2, "south", "spruce")
        d.chair(x2 - 1, y0, z1 - 2, "south", "spruce")
    d.set(mid, 5, z1 + 3, LANT)
    # records room behind (L3+)
    if L >= 3:
        for z in range(15, 19):
            d.bookshelf(x1 + 1, y0, z, 2)
            d.bookshelf(x2 - 1, y0, z, 1)
        d.bookshelf(x2 - 2, y0, 18, 1)
        d.bookshelf(x2 - 3, y0, 18, 1)
        d.item(x1 + 3, y0, 18, "lectern", "north")
        d.item(x1 + 4, y0, 18, "cartography_table")
        d.table(mid, y0, 16, "spruce")
        d.chair(mid - 1, y0, 16, "west", "spruce")
        d.chair(mid + 1, y0, 16, "east", "spruce")
        d.chair(mid, y0, 17, "south", "spruce")
        if L >= 4:
            d.bed(x2 - 2, y0, 15, "north")
        d.set(mid, 5, 17, LANT)
    # stable lean-to (L2+)
    if L >= 2:
        lx1, lx2 = x2, x2 + 8
        lz1, lz2 = z1, z1 + 8
        for x in range(lx1 + 1, lx2 + 1):
            for z in range(lz1, lz2 + 1):
                d.set(x, 1, z, "spruce_planks")
        for z in range(lz1, lz2 + 1):
            d.set(lx2, y0, z, lg("stripped_spruce_log", "z"))
            d.set(lx2, y0 + 1, z, lg("stripped_spruce_log", "z"))
        for x in range(lx1, lx2 + 1):
            d.set(x, y0, lz2, lg("stripped_spruce_log", "x"))
            d.set(x, y0 + 1, lz2, lg("stripped_spruce_log", "x"))
        for x, z in ((lx2, lz1), (lx2, lz2)):
            d.fill(x, y0, z, x, 4, z, lg("spruce_log", "y"))
        for z in range(lz1 - 1, lz2 + 2):
            for x in range(lx1 + 1, lx2 + 2):
                d.set(x, 5, z, sl("dark_oak", "top" if x < lx1 + 4 else "bottom"))
        for zz in (lz1 + 1, lz1 + 4):
            for x in range(lx2 - 3, lx2):
                d.set(x, y0, zz, "spruce_fence")
            d.set(lx2 - 1, y0, zz + 1, "hay_block[axis=x]")
        d.set(lx2 - 1, y0, lz2 - 1, "water_cauldron[level=3]")
        d.set(lx1 + 2, 4, lz1 + 3, LANT)
        n += barrel_wall(d, [(lx1 + 1, z) for z in range(lz2 - 1, lz1, -1)], y0, DLV[L] - n, "east", 2)
    # porch freight barrels (counted)
    n += barrel_wall(d, [(x2, z1 - 3), (x2 + 1, z1 - 3)], y0, DLV[L] - n, "up", 2)
    return d


@design("deliveryman")
def deliveryman(pack, rel, L):
    return {"Neoterra": dl_neo, "Hearthwood": dl_hw, "Cascadia": dl_cas}[pack](rel, L)


# =============================================================================================== COMPOSTER
"""
Composter
  Neoterra   "Green recycling station": white pavilion with a green roof and big glazing, three-sided concrete
             compost bays in front holding the compost barrels, planters; grows a bay per level.
  Hearthwood "Compost yard & potting shed": brick-walled garden yard with a timber potting shed against the
             back wall, plank compost bins and the barrels in a row, vegetable/flower beds.
  Cascadia   "Compost shed": open pole shed with a mossy roof over log-crib compost bins, wheel-less hand cart
             and rough fences; grows longer.
"""
CBAR = {1: 1, 2: 2, 3: 3, 4: 4, 5: 4}


def cp_neo(rel, L):
    d = Design("Neoterra", rel, (17, 9, 17), paving="smooth_stone")
    x1, z1, x2, z2 = 3, 9, 13, 14
    y0 = 2
    neo_block(d, x1, z1, x2, z2, y0, 4, floor="polished_andesite", roof="moss_block")
    for x in range(x1 + 1, x2):
        d.window(x, 3, z1, x, 4, z1, "glass_pane")
    d.door(8, y0, z1, "south", "birch")
    for x in range(x1 + 1, x2):
        for z in range(z1 + 1, z2):
            d.set(x, 6, z, "moss_carpet" if (x + z) % 4 else "azalea")
    d.sign(6, 2, z1 - 1, "north", ["RECYCLE", "& COMPOST"], "birch", glow=True, color="lime")
    d.hut(x1 + 1, y0, z1 + 1)
    d.item(x1 + 2, y0, z2 - 1, "composter")
    rack_line(d, [(x, z2 - 1) for x in range(x1 + 3, x2)], y0, L, 1)
    d.set(8, 5, 11, "sea_lantern")
    # compost bays in the forecourt: concrete U-bins, a barrel in each
    for i in range(CBAR[L] if L < 5 else 4):
        bx = x1 + i * 3
        for z in range(4, 7):
            d.set(bx, y0, z, "light_gray_concrete")
            d.set(bx + 2, y0, z, "light_gray_concrete")
        d.set(bx + 1, y0, 4, "light_gray_concrete")
        d.set(bx + 1, 1, 5, "podzol[snowy=false]")
        d.item(bx + 1, y0, 5, "minecolonies:barrel_block", "south")
        d.set(bx + 1, 1, 6, "rooted_dirt")
    for x in (1, 15):
        for z in range(9, 15):
            d.set(x, 1, z, "moss_block")
            d.set(x, y0, z, "fern" if z % 2 else "azalea")
    if L >= 5:
        for x in (x1, x1 + 11):
            d.fill(x, y0, 3, x, 4, 3, "white_concrete") if x <= x2 else None
        for x in range(x1 - 1, x1 + 13):
            for z in range(3, 8):
                d.set(x, 5, z, "glass") if z in (3, 7) or x in (x1 - 1, x1 + 12) else d.set(x, 5, z, "glass")
        d.fill(x1 + 11, y0, 7, x1 + 11, 4, 7, "white_concrete")
    return d


def cp_hw(rel, L):
    d = Design("Hearthwood", rel, (19, 13, 17), paving="gravel")
    y0 = 2
    # brick garden wall
    wx1, wz1, wx2, wz2 = 2, 3, 16, 15
    for x, z in ring(wx1, wz1, wx2, wz2):
        d.set(x, y0, z, "bricks")
        d.set(x, y0 + 1, z, "bricks" if z != wz1 else "brick_wall")
    for x in (8, 9, 10):
        d.set(x, y0, wz1, AIR)
        d.set(x, y0 + 1, wz1, AIR)
    for x in (7, 11):
        d.set(x, y0 + 2, wz1, LANT_S)
    d.fill(wx1 + 1, 1, wz1 + 1, wx2 - 1, 1, wz2 - 1, "coarse_dirt")
    for z in range(wz1, wz2):
        d.set(9, 1, z, "gravel")
    # potting shed against the back wall
    sx1, sz1, sx2, sz2 = 3, 10, 9, 14
    hw_walls(d, sx1, sz1, sx2, sz2, y0, 4, step=3)
    d.gable(sx1, sz1, sx2, sz2, 5, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite")
    d.door(6, y0, sz1, "south", "dark_oak")
    win(d, 4, 3, sz1)
    win(d, 8, 3, sz1)
    d.hut(sx1 + 1, y0, sz1 + 1)
    d.item(sx1 + 1, y0, sz2 - 1, "composter")
    rack_line(d, [(x, sz2 - 1) for x in range(sx1 + 2, sx2)] + [(sx2 - 1, sz1 + 1)], y0, L, 1)
    for x in range(sx1 + 2, sx2):
        if d.air(x, y0, sz2 - 1):
            d.set(x, y0, sz2 - 1, sl("spruce", "top"))
            d.set(x, y0 + 1, sz2 - 1, "flower_pot")
            break
    d.set(6, 4, 12, LANT)
    # compost bins: plank-sided boxes with the barrel inside
    for i in range(CBAR[L]):
        bx = 11 + (i % 2) * 3
        bz = 5 + (i // 2) * 4
        for dz in range(3):
            d.set(bx, y0, bz + dz, "spruce_fence" if dz else "spruce_planks")
            d.set(bx + 2, y0, bz + dz, "spruce_fence" if dz else "spruce_planks")
        d.set(bx + 1, y0, bz, "spruce_planks")
        d.item(bx + 1, y0, bz + 1, "minecolonies:barrel_block", "south")
        d.set(bx + 1, 1, bz + 2, "podzol[snowy=false]")
    # beds of vegetables / flowers
    for x in range(3, 8):
        for z in (5, 6):
            d.set(x, 1, z, "farmland[moisture=7]")
            d.set(x, y0, z, "carrots[age=5]" if x % 2 else "beetroots[age=2]")
    for x in range(3, 8):
        d.set(x, y0, 8, ["poppy", "dandelion", "cornflower", "oxeye_daisy", "allium"][x % 5])
    d.set(15, y0, 13, "water_cauldron[level=3]")
    if L >= 5:
        d.set(15, y0, 12, "flowering_azalea")
        d.set(12, y0, 13, "oak_fence")
        d.set(12, y0 + 1, 13, LANT_S)
    return d


def cp_cas(rel, L):
    d = Design("Cascadia", rel, (19, 12, 15), paving="coarse_dirt")
    x1, z1, z2 = 3, 4, 10
    x2 = {1: 9, 2: 11, 3: 13, 4: 15, 5: 15}[L]
    y0 = 2
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            d.set(x, 1, z, "packed_mud")
    for x in list(range(x1, x2 + 1, 3)) + [x2]:
        for z in (z1, z2):
            d.fill(x, y0, z, x, 4, z, lg("spruce_log", "y"))
            d.set(x, 1, z, "cobblestone")
    for x in range(x1, x2 + 1):
        d.set(x, 5, z1, lg("stripped_spruce_log", "x"))
        d.set(x, 5, z2, lg("stripped_spruce_log", "x"))
        d.set(x, y0, z2, lg("spruce_log", "x")) if d.air(x, y0, z2) else None
        d.set(x, y0 + 1, z2, lg("spruce_log", "x")) if d.air(x, y0 + 1, z2) else None
    rg = d.gable(x1, z1, x2, z2, 6, "x", "dark_oak_stairs", "dark_oak_slab", "spruce_planks")
    for x in range(x1, x2 + 1):                                     # moss on the north slope
        for k, z in enumerate(range(z1 - 1, (z1 + z2) // 2)):
            y = 6 + k - 1 + 1
            if (x + k) % 3 == 0 and d.air(x, y, z):
                d.set(x, y, z, "moss_carpet")
    d.hut(x1 + 1, y0, z1 + 1)
    d.item(x1 + 1, y0, z2 - 1, "composter")
    rack_line(d, [(x1 + 2, z2 - 1)] + [(x, z2 - 1) for x in range(x1 + 4, x2, 3)] + [(x2 - 1, z1 + 1)], y0, L, 1)
    # log-crib bins along the back with the barrels
    for i in range(CBAR[L]):
        bx = x1 + 3 + i * 3
        if bx + 1 >= x2:
            bx = x1 + 3 + (i - 2) * 3
        d.item(bx, y0, z2 - 2, "minecolonies:barrel_block", "north")
        d.set(bx - 1, y0, z2 - 2, lg("spruce_log", "z")) if d.air(bx - 1, y0, z2 - 2) else None
    d.set(x1 + 3, 4, (z1 + z2) // 2, LANT)
    # hand cart and fence
    d.set(x2 + 2, y0, 6, "spruce_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]")
    d.set(x2 + 2, y0, 7, "composter[level=4]")
    for z in range(2, 13):
        d.set(1, y0, z, "spruce_fence")
    for x in range(1, 18):
        d.set(x, y0, 13, "spruce_fence")
    d.set(x1 + 1, y0, z1 - 2, "fern")
    return d


@design("composter")
def composter(pack, rel, L):
    return {"Neoterra": cp_neo, "Hearthwood": cp_hw, "Cascadia": cp_cas}[pack](rel, L)
