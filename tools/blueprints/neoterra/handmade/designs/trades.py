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
    d.sign(7, 5, z1 - 3, "north", ["BUILD", "& DESIGN"], "birch", glow=True, color="cyan") if False else None
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
    d.plant(x1 - 1 + 1, y0, z1 - 1, "potted_bamboo") if False else None
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
            d.plant(x, 8, uz1 - 1, "potted_red_tulip") if False else None
        for z in (5, 8):
            win(d, hx1, 8, z)
            win(d, hx2, 8, z)
    d.sign(7, 4, hz1 - 1, "north", ["Master", "Builder"], "dark_oak", hanging=False) if False else None
    d.sign(10, 4, hz1 - 1, "north", ["Master Builder", "& Mason"], "dark_oak")
    # chimney + fireplace on the west wall
    d.hearth(hx1 + 1, y0, 9, "east", ridge + 2, "bricks", "campfire")
    for y in range(y0, ridge + 2):
        d.set(hx1, y, 9, "bricks")
    d.hut(4, y0, 4)
    # ---- ground floor
    d.item(5, y0, 4, "cartography_table") if False else None
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
        d.set(13, y0, 9, AIR) if False else None
    for x in (6, 10):
        d.set(x, 5, 7, LANT)
    d.rug(6, 6, 9, 8, y0, ("red_carpet", "orange_carpet"))
    # ---- upper floor: drafting room & library
    if two:
        yb = 7
        for z in (8, 9, 10):
            pass
        for x in range(4, 10):
            d.bookshelf(x, yb, hz2 - 1, 2)
        d.item(4, yb, 3, "lectern", "south") if False else None
        d.item(10, yb, hz2 - 1, "lectern", "north")
        d.item(4, yb, 3 - 0 + 1, "cartography_table") if False else None
        d.item(4, yb, 3, "cartography_table")
        d.item(4, yb, 4, "crafting_table")
        d.table(6, yb, 5, "dark_oak", "slab")
        d.table(7, yb, 5, "dark_oak", "slab")
        d.chair(6, yb, 4, "north", "dark_oak")
        d.chair(7, yb, 4, "north", "dark_oak")
        d.candle(6, yb + 1, 5, 2) if False else None
        for z in (5, 6, 7, 8):
            d.set(12, yb, z, "dark_oak_fence")
        d.set(12, yb, 9, "dark_oak_fence")
        if L >= 4:
            d.bed(4, yb, 8, "west")
            d.set(4, yb, 7, sl("dark_oak", "top"))
            d.candle(4, yb + 1, 7, 1)
            d.item(11, yb, 3 + 1, "jukebox") if False else None
            d.item(10, yb, 3, "jukebox")
            d.chair(6, yb, 6, "south", "dark_oak")
            d.chair(7, yb, 6, "south", "dark_oak")
        for x in (6, 10):
            d.set(x, 9, 7, LANT)
        d.set(8, 9, 7, "dark_oak_planks") if False else None
    # ---- yard wall & shed
    for x in range(hx2 + 1, 27):
        for z in (hz1,):
            pass
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
        d.set(x, 1, sz1, "stone_bricks") if False else None
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
    d.set(10, y0 + 1, 14, sl("oak", "bottom")) if False else None
    d.set(11, y0, 14, AIR)
    for x in (10, 11, 12):
        d.set(x, y0 + 1, 14, lg("stripped_oak_log", "x"))
    d.set(8, y0, 14, "water_cauldron[level=3]")
    if L >= 4:
        d.chair(5, y0, 14, "south", "dark_oak")
        d.chair(6, y0, 14, "south", "dark_oak")
    # cottage front: flower boxes
    d.set(4, y0, hz1 - 1 - (1 if two else 0), "rose_bush[half=lower]") if False else None
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
    d.double_door(mid - 1, y0, z1, "x", "south", "spruce") if False else None
    for x in (mid - 2, mid + 2):
        for y in range(y0, 6):
            d.set(x, y, z1 - 1, tr("spruce", "west" if x < mid else "east", "bottom", True)) if False else None
    for x in range(mid - 1, mid + 2):
        d.set(x, 5, z1, lg("dark_oak_log", "x"))
    # hay-hoist beam at the peak
    d.set(mid, ridge - 1, z1, "hay_block[axis=y]") if False else None
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
        d.set(mid, y0 + 1, z, sl("spruce")) if False else None
    d.chair(mid - 1, y0, z1 + 5, "west", "spruce")
    d.chair(mid - 1, y0, z1 + 6, "west", "spruce")
    if b_items(L):
        tools = ["anvil", "smithing_table", "grindstone", "stonecutter",
                 "hopper" if L <= 3 else "domum_ornamentum:architectscutter"]
        if L >= 5:
            tools.append("ender_chest")
        for i, t in enumerate(tools):
            d.item(x2 - 1, y0, z2 - 1 - i, t, "west")
    for z in range(z1 + 3, z2, 4):
        d.set(mid, 6, z, lg("stripped_spruce_log", "x")) if False else None
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
            for i, x in enumerate(range(lx1 + 1, lx2 + 2)):
                d.set(x, 7 - (i + 1) // 3 if False else 6, z, st("spruce", "west")) if False else None
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
