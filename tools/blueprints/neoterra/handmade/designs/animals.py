"""
Animal husbandry huts + stable, hand-made for the three packs.

Common idea: a working farm building (barn / coop / sty / hutch house / apiary shed / stable) with the herder's
work room (crafting table, racks, feed) inside, and fenced pens / paddocks with gates and water troughs
(the required water cauldrons) outside.  The pens grow with the level; the building gains wings, lofts and decor.

  Hearthwood  English farmstead: brick plinth, timber-framed brick/plaster walls, steep deepslate-tile gables,
              oak/dark-oak fencing, cottage-garden touches.
  Cascadia    Pacific-Northwest homestead: log or red board barns with gambrel / A-frame roofs, river-rock
              footings, spruce rail fences, hay and lanterns.
  Neoterra    Modern agri-tech: white concrete frame, glass curtain walls, flat roofs with solar arrays and green
              roofs, birch fencing on andesite curbs, glowing signage.
"""
import copy

from hm import Design, design, AIR, D4, OPP, REQ, rels_for

GROWTH = 1.6

GRASS = "grass_block[snowy=false]"


# ============================================================================================ shared helpers
def st(block, facing, half="bottom", shape="straight"):
    return f"{block}[facing={facing},half={half},shape={shape},waterlogged=false]"


def slab(block, typ="bottom"):
    return f"{block}[type={typ},waterlogged=false]"


def trap(wood, facing, half="bottom", open_=False):
    return f"{wood}_trapdoor[facing={facing},half={half},open={'true' if open_ else 'false'},powered=false," \
           f"waterlogged=false]"


def gate(wood, facing):
    return f"{wood}_fence_gate[facing={facing},in_wall=false,open=false,powered=false]"


def pen(d, x1, z1, x2, z2, fence, gates=(), ground=GRASS, y=2, patches=None):
    """Fenced pen: ground on y-1 inside the fence line, fence on the border, gates at the given (x, z)."""
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            g = ground
            if patches and (x * 7 + z * 3) % patches[1] == 0:
                g = patches[0]
            d.set(x, y - 1, z, g)
            if x in (x1, x2) or z in (z1, z2):
                d.set(x, y, z, fence)
            else:
                d.set(x, y, z, AIR)
                d.set(x, y + 1, z, AIR)
    wood = fence.replace("_fence", "")
    for gx, gz in gates:
        d.set(gx, y, gz, gate(wood, "north" if gz in (z1, z2) else "east"))


def trough(d, cells, y=2):
    """Water troughs (the hut's required water cauldrons)."""
    for x, z in cells:
        d.item(x, y, z, "water_cauldron[level=3]")


def path(d, x1, z1, x2, z2, block, y=1):
    d.fill(x1, y, z1, x2, y, z2, block)


def gambrel(d, x1, z1, x2, z2, y, axis, stairs, block, slab_, end, overhang=1, kb=None):
    """Barn (gambrel) roof over walls x1..x2/z1..z2 with wall tops at y-1: a steep lower slope (2 up per step)
    then a shallow upper slope. Returns the ridge height."""
    if axis == "x":
        lo, hi, a1, a2 = z1, z2, x1, x2
    else:
        lo, hi, a1, a2 = x1, x2, z1, z2
    o = overhang
    L, H = lo - o, hi + o
    n = H - L + 1
    half = n // 2
    kb = kb if kb is not None else max(2, (half + 1) // 2)
    h = [y - 1]
    for k in range(1, half + 1):
        h.append(h[-1] + (2 if k <= kb else 1))
    top = h[half - 1]
    for i in range(n):
        w = L + i
        k = min(i, n - 1 - i)
        mid = n % 2 == 1 and i == half
        if axis == "x":
            face = "south" if i < n / 2 else "north"
        else:
            face = "east" if i < n / 2 else "west"
        for a in range(a1 - o, a2 + o + 1):
            x, z = (a, w) if axis == "x" else (w, a)
            if mid:
                d.set(x, top, z, block)
                d.set(x, top + 1, z, slab(slab_))
                continue
            d.set(x, h[k], z, st(stairs, face))
            if k >= 1:
                for yy in range(h[k - 1] + 1, h[k]):
                    d.set(x, yy, z, block)
        if lo <= w <= hi:
            for a in (a1, a2):
                x, z = (a, w) if axis == "x" else (w, a)
                yt = (top + 1) if mid else h[k]
                for yy in range(y, yt):
                    if d.air(x, yy, z):
                        d.set(x, yy, z, end)
    return top + 1


def solar(d, x1, z1, x2, z2, y, step=2):
    """Rows of solar panels (daylight detectors) on a flat roof, rows running along x."""
    for z in range(z1, z2 + 1, step):
        for x in range(x1, x2 + 1):
            d.set(x, y, z, "daylight_detector[inverted=false,power=0]")


def hw_walls(d, x1, z1, x2, z2, top, floor="spruce_planks", infill="calcite", post_step=3, y0=2,
             lower=2):
    """Hearthwood farm walls: stone-brick plinth, brick lower courses, timber-framed infill above."""
    d.box(x1, y0, z1, x2, top, z2, "bricks", floor=floor)
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if not (x in (x1, x2) or z in (z1, z2)):
                continue
            d.set(x, y0, z, "stone_bricks")
            for y in range(y0 + lower, top + 1):
                post = (x in (x1, x2) and (z - z1) % post_step == 0) or (z in (z1, z2) and (x - x1) % post_step == 0) \
                    or (x in (x1, x2) and z in (z1, z2))
                if y == top:
                    d.set(x, y, z, f"stripped_dark_oak_log[axis={'x' if z in (z1, z2) else 'z'}]")
                elif post:
                    d.set(x, y, z, "stripped_dark_oak_log[axis=y]")
                else:
                    d.set(x, y, z, infill)
    for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        for y in range(y0 + 1, top + 1):
            d.set(x, y, z, "stripped_dark_oak_log[axis=y]")


def cs_logs(d, x1, z1, x2, z2, top, floor="spruce_planks", y0=2, log="stripped_spruce_log"):
    """Cascadia log walls: light stripped horizontal logs, dark corner posts, river-rock footing."""
    d.box(x1, y0, z1, x2, top, z2, f"{log}[axis=z]", floor=floor)
    for x in range(x1, x2 + 1):
        for y in range(y0, top + 1):
            d.set(x, y, z1, f"{log}[axis=x]")
            d.set(x, y, z2, f"{log}[axis=x]")
    for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        for y in range(y0, top + 1):
            d.set(x, y, z, "spruce_log[axis=y]")
    footing(d, x1, z1, x2, z2)


def cs_red(d, x1, z1, x2, z2, top, floor="spruce_planks", y0=2):
    """Cascadia red barn walls: red boards, stripped spruce corner posts, dark sill and eave beams."""
    d.box(x1, y0, z1, x2, top, z2, "mangrove_planks", floor=floor)
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if x in (x1, x2) or z in (z1, z2):
                d.set(x, y0, z, "dark_oak_planks")
                d.set(x, top, z, f"stripped_spruce_log[axis={'x' if z in (z1, z2) else 'z'}]")
    for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        for y in range(y0, top + 1):
            d.set(x, y, z, "stripped_spruce_log[axis=y]")
    footing(d, x1, z1, x2, z2)


def footing(d, x1, z1, x2, z2):
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if x in (x1, x2) or z in (z1, z2):
                d.set(x, 1, z, "mossy_cobblestone" if (x + 2 * z) % 3 == 0 else "cobblestone")


def nt_walls(d, x1, z1, x2, z2, top, floor="polished_diorite", y0=2, col_step=4, glass="glass_pane",
             glaze=(3, None), sides="nsew"):
    """Neoterra pavilion: white concrete shell, light-gray columns, andesite base course, glass bands between
    the columns from y=glaze[0] to glaze[1] (default top-1) on the listed sides."""
    d.box(x1, y0, z1, x2, top, z2, "white_concrete", floor=floor)
    g1, g2 = glaze[0], glaze[1] if glaze[1] else top - 1
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if not (x in (x1, x2) or z in (z1, z2)):
                continue
            d.set(x, y0, z, "polished_andesite")
            col = (z in (z1, z2) and (x - x1) % col_step == 0) or (x in (x1, x2) and (z - z1) % col_step == 0) \
                or (x in (x1, x2) and z in (z1, z2))
            side = "n" if z == z1 else "s" if z == z2 else "w" if x == x1 else "e"
            if col:
                for y in range(y0 + 1, top + 1):
                    d.set(x, y, z, "light_gray_concrete")
            elif side in sides and not (x in (x1, x2) and z in (z1, z2)):
                for y in range(g1, g2 + 1):
                    d.set(x, y, z, glass)


def nt_roof(d, x1, z1, x2, z2, y, solar_rows=True, green=False):
    """Flat roof with parapet and coping; solar rows or a green roof inside."""
    d.flat(x1, z1, x2, z2, y, "smooth_quartz", "white_concrete", "smooth_quartz_slab")
    if green:
        for x in range(x1 + 1, x2):
            for z in range(z1 + 1, z2):
                d.set(x, y + 1, z, "moss_carpet" if (x + z) % 3 else "azalea" if (x * z) % 7 == 0 else "moss_carpet")
    elif solar_rows:
        solar(d, x1 + 1, z1 + 1, x2 - 1, z2 - 1, y + 1)


def racks(d, cells, y, facing):
    for x, z in cells:
        d.rack(x, y, z, facing)


def hay(d, x, y, z, axis="y"):
    d.set(x, y, z, f"hay_block[axis={axis}]")


def need_racks(d):
    return d.req["racks"]


# ============================================================================================ CHICKEN HERDER
def chicken_hw(rel, L):
    """Cotswold hen house: brick & timber coop with a nesting-box wall, pop hole into a fenced run with a
    duck pond, rear feed store from L3, dovecote gable from L5."""
    d = farm_design("Hearthwood", rel, (23, 16, 22), paving="grass_block[snowy=false]")
    x1, z1, x2, z2 = 3, 3, 11, 9
    hw_walls(d, x1, z1, x2, z2, 5, floor="spruce_planks")
    ridge = d.gable(x1, z1, x2, z2, 6, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite", overhang=1)
    path(d, 6, 0, 8, z1 - 1, "gravel")
    d.door(7, 2, z1, "south", "dark_oak")
    for x in (5, 9):
        d.window(x, 3, z1, x, 4, z1)
        d.set(x, 2, z1 - 1, "potted_red_tulip" if x == 5 else "potted_azure_bluet")
    d.window(x1, 3, 6, x1, 4, 6)
    d.hut(4, 2, 4)
    # nesting boxes along the back wall: hay in dark-oak cubbies, two tiers
    for x in range(7, 11):
        d.set(x, 2, z2 - 1, "dark_oak_planks" if x % 2 else "hay_block[axis=x]")
        d.set(x, 3, z2 - 1, slab("dark_oak_slab", "top") if x % 2 else "hay_block[axis=x]")
        d.set(x, 4, z2 - 1, slab("dark_oak_slab", "bottom"))
    # roosting perches (fence rails) on the east side above a litter of hay
    for z in (5, 6, 7):
        d.set(x2 - 1, 2, z, "hay_block[axis=z]" if z == 6 else "composter[level=7]")
    d.set(x2 - 2, 2, 5, "dark_oak_fence")
    d.set(x2 - 2, 3, 5, slab("dark_oak_slab"))
    d.item(x1 + 1, 2, 8, "crafting_table")
    nr = need_racks(d)
    rk = [(x1 + 1, 6), (x1 + 1, 7), (x1 + 1, 5)][:min(nr, 3) if L < 3 else 0]
    racks(d, rk, 2, "east")
    d.lamp(7, 5, 6)
    # pop hole into the run
    d.set(x2, 2, 6, AIR)
    d.set(x2, 3, 6, "bricks")
    # run
    rz2 = 10 if L == 1 else 16 if L < 4 else 19
    pen(d, 12, 3, 20, rz2, "oak_fence", gates=[(16, 3)], patches=("coarse_dirt", 7))
    d.set(x2 + 1, 2, 6, AIR)
    path(d, 15, 0, 17, 2, "gravel")
    trough(d, [(19, 4), (19, 5)])
    hay(d, 13, 2, rz2 - 1)
    d.set(14, 2, rz2 - 1, "composter[level=3]")
    if L >= 2:
        d.set(13, 2, 9, "dark_oak_fence")
        d.set(13, 3, 9, "lantern[hanging=false,waterlogged=false]")
    if L >= 4:                                                     # duck pond in the run
        for x in range(16, 19):
            for z in range(14, 17):
                d.set(x, 1, z, "water")
        for x, z in ((15, 14), (15, 16), (19, 15), (17, 13), (17, 17)):
            d.set(x, 1, z, "mud")
        d.set(15, 2, 15, "sugar_cane")
        d.set(15, 1, 15, "dirt")
    # rear feed store / egg room (cross gable) from L3
    if L >= 3:
        fx1, fx2, fz1, fz2 = 3, 9, 9, 15
        hw_walls(d, fx1, fz1, fx2, fz2, 5, floor="spruce_planks", infill="bricks")
        d.gable(fx1, fz1 + 1, fx2, fz2, 6, "z", "deepslate_tile_stairs", "deepslate_tile_slab", "bricks")
        for x in range(fx1 + 1, fx2):                              # open through to the coop
            if x in (5, 6):
                d.set(x, 2, fz1, AIR)
                d.set(x, 3, fz1, AIR)
        # move nesting tier there: keep coop boxes, add feed sacks & racks
        rk = [(fx1 + 1, z) for z in range(fz1 + 1, fz2)][:nr]
        racks(d, rk, 2, "east")
        for z in range(fz1 + 2, fz2):
            d.set(fx2 - 1, 2, z, "barrel[facing=up,open=false]" if z % 2 else "hay_block[axis=y]")
        d.set(fx2 - 1, 3, fz1 + 2, "hay_block[axis=x]")
        d.window(fx2, 3, 12, fx2, 4, 12)
        d.window(fx1, 3, 12, fx1, 4, 12)
        d.lamp(6, 5, 12)
        d.set(6, 2, fz2 - 1, "water_cauldron[level=1]")            # egg washing
        d.set(5, 2, fz2 - 1, slab("dark_oak_slab", "top"))
        d.set(7, 2, fz2 - 1, slab("dark_oak_slab", "top"))
        d.set(7, 3, fz2 - 1, "candle[candles=3,lit=false,waterlogged=false]")
    if L >= 4:                                                     # cottage garden by the door
        for x in range(1, 6):
            if x != 3:
                d.set(x, 2, 1, "peony[half=lower]")
                d.set(x, 3, 1, "peony[half=upper]")
        d.set(10, 2, 1, "flowering_azalea")
        d.set(11, 2, 1, "flowering_azalea")
    if L >= 5:                                                     # dovecote in the street gable + weathervane
        mx = 7
        d.set(x1, ridge - 1, 6, "dark_oak_trapdoor[facing=west,half=bottom,open=true,powered=false,waterlogged=false]")
        d.set(x2, ridge - 2, 6, AIR)
        d.set(x2 + 1, ridge - 3, 6, slab("dark_oak_slab", "top"))
        d.set(mx, ridge + 1, 6, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        d.sign(7, 4, z1 - 1, "north", ["Fresh", "Eggs"], "dark_oak")
        d.set(13, 2, 1, "dark_oak_fence")
        d.set(13, 3, 1, "lantern[hanging=false,waterlogged=false]")
    return d


def chicken_cs(rel, L):
    """Homestead log coop: narrow A-frame with the gable to the street, chicken ramp to a hen loft, a long
    rail-fenced run down the east side, feed lean-to from L2 and a hen-house deck from L4."""
    d = farm_design("Cascadia", rel, (21, 18, 25), paving=GRASS)
    x1, z1, x2, z2 = 3, 4, 9, 13
    cs_logs(d, x1, z1, x2, z2, 4)
    ridge = d.gable(x1, z1, x2, z2, 5, "z", "dark_oak_stairs", "dark_oak_slab", "spruce_planks", overhang=1)
    # hen loft inside the roof
    d.fill(x1 + 1, 5, z1 + 5, x2 - 1, 5, z2 - 1, "spruce_planks")
    d.door(6, 2, z1, "south", "spruce")
    d.window(4, 3, z1, 4, 3, z1)
    d.window(8, 3, z1, 8, 3, z1)
    d.set(6, ridge - 2, z1, "spruce_trapdoor[facing=north,half=bottom,open=true,powered=false,waterlogged=false]")
    d.hut(4, 2, z1 + 1)
    d.item(x2 - 1, 2, z1 + 1, "crafting_table")
    # nesting boxes along west wall under the loft, ladder to the loft
    for z in range(z1 + 5, z2):
        d.set(x1 + 1, 2, z, "hay_block[axis=z]" if z % 2 else "barrel[facing=east,open=false]")
        d.set(x1 + 1, 3, z, trap("spruce", "east", "top"))
    for y in range(2, 6):
        d.set(6, y, z1 + 5, "ladder[facing=north,waterlogged=false]")
    for z in range(z1 + 6, z2):                                      # straw on the loft
        d.set(5, 6, z, "hay_block[axis=z]")
        d.set(7, 6, z, "hay_block[axis=z]")
    nr = need_racks(d)
    racks(d, [(x2 - 1, z) for z in range(z1 + 2, z1 + 2 + nr)], 2, "west")
    d.lamp(6, 4, z1 + 2)
    # pop hole + ramp into the run
    d.set(x2, 2, z2 - 2, AIR)
    rz2 = 17 if L == 1 else 21 if L < 4 else 23
    pen(d, 11, 2, 19, rz2, "spruce_fence", gates=[(15, 2), (11, 8)], patches=("coarse_dirt", 5))
    d.set(10, 2, z2 - 2, AIR)
    d.set(10, 2, 8, AIR)
    d.set(10, 3, 8, AIR)
    trough(d, [(18, 3), (18, 4)])
    hay(d, 12, 2, rz2 - 1)
    hay(d, 12, 3, rz2 - 1)
    d.set(13, 2, rz2 - 1, "hay_block[axis=x]")
    for z in range(5, rz2 - 2, 5):                                   # dust-bath pits
        d.set(16, 1, z, "sand")
    path(d, 5, 0, 7, z1 - 1, "dirt_path")
    path(d, 14, 0, 16, 1, "dirt_path")
    if L >= 2:                                                       # feed lean-to on the west wall (open side)
        for z in range(z1 + 1, z1 + 6):
            d.set(1, 1, z, "cobblestone")
            d.set(2, 4, z, st("spruce_stairs", "east"))
        for z in (z1 + 1, z1 + 5):
            for y in (2, 3):
                d.set(1, y, z, "spruce_log[axis=y]")
            d.set(1, 4, z, slab("spruce_slab"))
        for z in range(z1 + 2, z1 + 5):
            d.set(1, 4, z, slab("spruce_slab"))
            d.set(2, 2, z, "hay_block[axis=z]")
        d.set(1, 2, z1 + 3, "barrel[facing=up,open=false]")
    if L >= 4:                                                       # porch deck at the street gable
        d.fill(x1 - 1, 1, 1, x2 + 1, 1, z1 - 1, "spruce_planks")
        for x in (x1 - 1, x2 + 1):
            for y in (2, 3, 4):
                d.set(x, y, 1, "spruce_log[axis=y]")
        for x in range(x1 - 1, x2 + 2):
            for z in (1, 2, 3):
                d.set(x, 5, z, slab("dark_oak_slab"))
        d.chair(x1, 2, 2, "south", "spruce", sit=False)
        d.keg(x2, 2, 2, "north")
        d.set(x2, 3, 2, "lantern[hanging=false,waterlogged=false]")
    if L >= 5:
        d.sign(6, 4, z1 - 1, "north", ["Hen House", "~ eggs ~"], "spruce")
        for z in range(z2 + 2, 22):
            d.set(4, 2, z, "sweet_berry_bush[age=3]" if z % 2 else "fern")
        d.set(8, 2, 20, "spruce_fence")
        d.set(8, 3, 20, "carved_pumpkin[facing=north]")
    return d


def chicken_nt(rel, L):
    """Urban poultry pavilion: glass-fronted white hen house behind a street-facing run so passers-by see the
    hens; green roof, solar canopy, egg-shop counter from L3, roof garden from L5."""
    d = farm_design("Neoterra", rel, (19, 14, 21), paving="smooth_stone")
    x1, z1, x2, z2 = 2, 11, 14, 18
    nt_walls(d, x1, z1, x2, z2, 5, sides="ne")
    nt_roof(d, x1, z1, x2, z2, 6, solar_rows=L < 5, green=L >= 5)
    d.double_door(12, 2, z1, "x", "south", "birch")
    d.hut(10, 2, z1 + 1)
    d.item(x2 - 1, 2, z2 - 1, "crafting_table")
    nr = need_racks(d)
    racks(d, [(x2 - 1, z) for z in range(z2 - 2, z2 - 2 - nr, -1)][:4], 2, "west")
    if nr >= 5:
        d.rack(x2 - 2, 2, z2 - 1, "north")
    # nesting wall: birch boxes with hay, west half
    for x in range(x1 + 1, 9):
        d.set(x, 2, z2 - 1, "hay_block[axis=x]")
        d.set(x, 3, z2 - 1, trap("birch", "north", "top"))
        d.set(x, 4, z2 - 1, "hay_block[axis=x]")
    for x in range(x1 + 1, 9, 2):
        d.set(x, 5, z1 + 3, "end_rod[facing=down]")
    # roost frame
    for x in range(x1 + 2, 8, 2):
        d.set(x, 2, z1 + 3, "birch_fence")
        d.set(x, 3, z1 + 3, slab("birch_slab"))
    # glazed opening to the run
    d.set(5, 2, z1, AIR)
    d.set(5, 3, z1, "glass_pane")
    # run in front, toward the street
    rz1 = 6 if L < 2 else 3 if L < 4 else 2
    rx2 = 9 if L < 2 else 10
    pen(d, 2, rz1, rx2, z1 - 1, "birch_fence", gates=[(6, rz1)], patches=("coarse_dirt", 7))
    for x in range(2, rx2 + 1):                                      # restore the house wall line
        pass
    trough(d, [(3, z1 - 2), (4, z1 - 2)])
    d.set(rx2 - 1, 2, z1 - 2, "composter[level=4]")
    d.set(rx2 - 1, 2, rz1 + 1, "hay_block[axis=y]")
    # walkway to the door
    path(d, 11, 0, 14, z1 - 1, "polished_andesite")
    for z in range(1, z1 - 1, 3):
        if z > 2:
            d.set(15, 2, z, "potted_bamboo")
    d.sign(9, 5, z1 - 1, "north", ["EGG LAB", "urban hens"], "birch", glow=True, color="cyan")
    if L >= 2:
        # canopy over the walkway
        for z in range(z1 - 3, z1):
            for x in range(11, 15):
                d.set(x, 5, z, slab("smooth_quartz_slab", "top"))
        for y in range(2, 5):
            d.set(14, y, z1 - 3, "light_gray_concrete")
    if L >= 3:                                                       # egg shop counter by the entrance
        d.counter(9, z1 + 2, 9, z1 + 4, 2, "smooth_quartz_slab")
        d.set(9, 3, z1 + 2, "candle[candles=4,lit=false,waterlogged=false]")
    if L >= 4:                                                       # planters along the street
        for x in range(11, 17):
            if x not in (12, 13):
                d.set(x, 1, 1, "moss_block")
                d.set(x, 2, 1, "flowering_azalea" if x % 2 else "azalea")
    if L >= 5:                                                       # roof garden access: ladder & railing
        for y in range(2, 7):
            d.set(x1 + 1, y, z1 + 1, "ladder[facing=south,waterlogged=false]")
        d.set(x1 + 1, 6, z1 + 1, "ladder[facing=south,waterlogged=false]")
        d.lamp(x2 - 2, 8, z2 - 2, "lantern", hanging=False)
    return d


def stairs_up(d, x, z, y0, y1, dirn, block, wood_planks):
    """Straight flight from floor y0 up to the deck at y1 (stairs on y0..y1-1), rising toward `dirn`; clears
    the deck above each step for headroom and supports the steps."""
    dx, dz = D4[dirn]
    for i, y in enumerate(range(y0, y1)):
        cx, cz = x + dx * i, z + dz * i
        d.set(cx, y, cz, st(block, dirn))
        for yy in range(y0, y):
            d.set(cx, yy, cz, wood_planks)
        for yy in range(y + 1, y + 4):
            if yy >= y1:
                d.set(cx, yy, cz, AIR)
    # landing cell beyond the top step must be the deck


@design("chickenherder")
def chickenherder(pack, rel, L):
    return farmstead({"Hearthwood": chicken_hw, "Cascadia": chicken_cs, "Neoterra": chicken_nt}[pack], pack, rel, L, "poultry")


def stone_fold(d, x1, z1, x2, z2, stone, fence, gates=(), ground=GRASS, y=2):
    """Dry-stone fold: a stone course with a fence rail on top, gates in gaps."""
    pen(d, x1, z1, x2, z2, fence, (), ground, y)
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if x in (x1, x2) or z in (z1, z2):
                d.set(x, y, z, stone if (x + z) % 4 else "mossy_" + stone if not stone.startswith("mossy") else stone)
                d.set(x, y + 1, z, fence)
    wood = fence.replace("_fence", "")
    for gx, gz in gates:
        d.set(gx, y, gz, gate(wood, "north" if gz in (z1, z2) else "east"))
        d.set(gx, y + 1, gz, AIR)


def sawtooth(d, x1, z1, x2, z2, y, stairs, glass, end):
    """North-light sawtooth roof over walls with tops at y-1: teeth 3 deep, glazing facing north (street)."""
    z = z1
    while z <= z2:
        for x in range(x1, x2 + 1):
            for k, zz in enumerate((z, z + 1, z + 2)):
                if zz > z2:
                    continue
                hh = y + 2 - k
                d.set(x, hh, zz, st(stairs, "north") if 0 < k else f"{stairs.replace('_stairs', '')}")
                if k == 0:
                    for yy in range(y, hh):
                        d.set(x, yy, zz, glass if x not in (x1, x2) else end)
                if x in (x1, x2):
                    for yy in range(y, hh):
                        if d.air(x, yy, zz):
                            d.set(x, yy, zz, end)
        z += 3


# ============================================================================================ COWBOY (cattle)
def cow_hw(rel, L):
    """Cotswold cow byre: long brick-and-timber byre with a cross-passage door, mangers with water troughs,
    stalls opening onto the paddock behind, hay loft under the tiled roof (pitching door in the gable).
    L3 lengthens the byre, L4 adds a hay rick and cart, L5 a milk stand by the lane."""
    d = farm_design("Hearthwood", rel, (27, 18, 27), paving=GRASS)
    x1, z1, z2 = 3, 3, 11
    x2 = 13 if L < 3 else 19
    pz2 = 20 if L < 3 else 25
    px2 = 15 if L < 3 else 23
    pen(d, x1, z2, px2, pz2, "oak_fence", gates=[(px2, z2 + 3)], patches=("coarse_dirt", 11))
    hw_walls(d, x1, z1, x2, z2, 7, floor="cobblestone", infill="calcite", post_step=3)
    d.fill(x1 + 1, 6, z1 + 1, x2 - 1, 6, z2 - 1, "spruce_planks")       # loft deck
    ridge = d.gable(x1, z1, x2, z2, 8, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite")
    # cross passage door and windows
    path(d, 7, 0, 9, z1 - 1, "gravel")
    d.double_door(8, 2, z1, "x", "south", "dark_oak")
    for x in range(x1 + 2, x2 - 1, 3):
        if x not in (8, 9):
            d.window(x, 3, z1, x, 4, z1)
    d.hut(x1 + 1, 2, z1 + 1)
    d.item(x1 + 1, 2, z1 + 2, "crafting_table")
    nr = need_racks(d)
    rk = [(x, z1 + 1) for x in (5, 6, 10, 11, 12, 14, 15)][:nr]
    racks(d, rk, 2, "south")
    # manger row: hay and water troughs; stalls behind with dividers; gates into the paddock
    need_c = d.req["items"]["minecraft:water_cauldron"]
    c = 0
    for x in range(x1 + 1, x2):
        if x % 2 == 1 and c < need_c:
            d.item(x, 2, z1 + 4, "water_cauldron[level=3]")
            c += 1
        else:
            hay(d, x, 2, z1 + 4, "x")
    for x in range(x1 + 3, x2 - 1, 3):
        for z in range(z1 + 5, z2):
            d.set(x, 2, z, "dark_oak_fence")
    for x in range(x1 + 2, x2 - 1, 3):
        d.set(x, 2, z2, gate("dark_oak", "south"))
        d.set(x, 3, z2, AIR)
    for x in range(x1 + 2, x2, 3):
        d.lamp(x, 5, z1 + 2)
    # ladder to the hay loft, hay stacked up there, pitching door in the west gable
    for y in range(2, 7):
        d.set(x2 - 1, y, z1 + 2, "ladder[facing=west,waterlogged=false]")
    for x in range(x1 + 1, x2 - 2):
        for z in (z1 + 4, z1 + 5):
            if (x + z) % 5:
                hay(d, x, 7, z, "x")
        if x % 2:
            hay(d, x, 8, z1 + 4, "z")
    d.set(x1, 7, 7, trap("dark_oak", "west", open_=True))
    d.set(x1, 8, 7, trap("dark_oak", "west", open_=True))
    d.set(x1 + 1, 7, 7, AIR)
    # paddock: hay feeder, salt lick, shade tree
    hay(d, px2 - 2, 2, pz2 - 2)
    d.set(px2 - 3, 2, pz2 - 2, "composter[level=8]")
    d.set(x1 + 2, 2, pz2 - 2, "oak_log[axis=y]")
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            d.set(x1 + 2 + dx, 5, pz2 - 2 + dz, "oak_leaves[distance=1,persistent=true,waterlogged=false]")
    d.set(x1 + 2, 3, pz2 - 2, "oak_log[axis=y]")
    d.set(x1 + 2, 4, pz2 - 2, "oak_log[axis=y]")
    d.set(x1 + 2, 6, pz2 - 2, "oak_leaves[distance=1,persistent=true,waterlogged=false]")
    if L >= 2:
        d.sign(x1 + 4, 4, z1 - 1, "north", ["Home Farm", "Byre"], "dark_oak")
        d.set(x1 + 1, 2, z1 - 1, "potted_red_tulip")
    if L >= 4:                                                         # hay rick and a farm cart by the lane
        rx = x2 + 2
        for y, w in ((2, 1), (3, 1), (4, 0)):
            for dx in range(-w, w + 1):
                for dz in range(-w, w + 1):
                    hay(d, rx + 1 + dx, y, z1 + 3 + dz)
        d.set(rx + 1, 5, z1 + 3, slab("deepslate_tile_slab"))
        d.set(rx + 4, 2, z1 + 1, "dark_oak_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
        d.set(rx + 4, 2, z1 + 2, "dark_oak_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
        d.set(rx + 3, 2, z1 + 1, "dark_oak_fence")
    if L >= 5:                                                         # milk-churn stand at the lane
        d.set(x1 + 6, 2, 1, slab("stone_brick_slab", "top"))
        d.set(x1 + 5, 2, 1, slab("stone_brick_slab", "top"))
        d.set(x1 + 6, 3, 1, "cauldron")
        d.set(x1 + 5, 3, 1, "cauldron")
        for x in (x1, x1 + 1, x1 + 2):
            d.set(x, 2, 1, "potted_oxeye_daisy" if x % 2 else "potted_cornflower")
        d.set(x1 + 9, ridge + 1, 7, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    return d


def cow_cs(rel, L):
    """Red gambrel dairy barn, gable to the road: big double barn doors with the hay door above, a central
    aisle with mangers and tie stalls both sides, dairy/work room at the front, loft under the gambrel and a
    rail-fenced pasture to the east. L3 lengthens the barn, L4 adds a silo, L5 a porch bench and signage."""
    d = farm_design("Cascadia", rel, (29, 22, 27), paving=GRASS)
    x1, x2, z1 = 4, 15, 3
    z2 = 11 if L < 3 else 17
    pz2 = 15 if L < 3 else 24
    pen(d, x2, z1 + 3, 27, pz2, "spruce_fence", gates=[(21, pz2), (27, z1 + 6)], patches=("coarse_dirt", 6))
    cs_red(d, x1, z1, x2, z2, 5, floor="spruce_planks")
    d.fill(x1 + 1, 6, z1 + 1, x2 - 1, 6, z2 - 1, "spruce_planks")
    ridge = gambrel(d, x1, z1, x2, z2, 6, "z", "dark_oak_stairs", "dark_oak_planks", "dark_oak_slab",
                    "mangrove_planks", kb=3)
    # front: double doors, white-ish trim cross braces, hay door + hood
    path(d, 8, 0, 11, z1 - 1, "dirt_path")
    d.double_door(9, 2, z1, "x", "south", "spruce")
    for x in (8, 11):
        for y in range(2, 5):
            d.set(x, y, z1, "stripped_spruce_log[axis=y]")
    for x in range(8, 12):
        d.set(x, 4, z1, "stripped_spruce_log[axis=x]")
    d.window(6, 3, z1, 6, 3, z1)
    d.window(13, 3, z1, 13, 3, z1)
    d.set(9, 8, z1, "spruce_door[facing=south,half=lower,hinge=left,open=false,powered=false]")
    d.set(9, 9, z1, "spruce_door[facing=south,half=upper,hinge=left,open=false,powered=false]")
    d.set(10, 8, z1, "spruce_door[facing=south,half=lower,hinge=right,open=false,powered=false]")
    d.set(10, 9, z1, "spruce_door[facing=south,half=upper,hinge=right,open=false,powered=false]")
    d.set(9, 10, z1 - 1, st("dark_oak_stairs", "south", "top"))
    d.set(10, 10, z1 - 1, st("dark_oak_stairs", "south", "top"))
    d.set(9, 11, z1 - 1, "dark_oak_planks")
    d.set(10, 11, z1 - 1, "dark_oak_planks")
    # front work / dairy room
    d.hut(x1 + 1, 2, z1 + 1)
    d.item(x1 + 1, 2, z1 + 2, "crafting_table")
    nr = need_racks(d)
    racks(d, [(12, z1 + 1), (13, z1 + 1), (14, z1 + 1), (14, z1 + 2), (14, z1 + 3)][:nr], 2, "south")
    d.set(x1 + 2, 2, z1 + 1, "barrel[facing=up,open=false]")
    # stalls: west x5..6 + manger x7, aisle 8..11, manger x12 + stalls x13..14
    need_c = d.req["items"]["minecraft:water_cauldron"]
    c = 0
    for z in range(z1 + 4, z2):
        for mx in (7, 12):
            if (z % 3 == 0) and c < need_c:
                d.item(mx, 2, z, "water_cauldron[level=3]")
                c += 1
            else:
                hay(d, mx, 2, z, "z")
        if (z - z1 - 4) % 3 == 0 and z > z1 + 4:
            for x in (5, 6, 13, 14):
                d.set(x, 2, z, "spruce_fence")
    for z in range(z1 + 4, z2):                                        # extra troughs if the barn is short
        if c < need_c:
            for mx in (7, 12):
                if c < need_c and d.get(mx, 2, z).startswith("minecraft:hay"):
                    d.item(mx, 2, z, "water_cauldron[level=3]")
                    c += 1
    for z in range(z1 + 5, z2, 3):                                     # stall doors into the pasture
        d.set(x2, 2, z, gate("spruce", "east"))
        d.set(x2, 3, z, AIR)
    d.window(x1, 3, z1 + 5, x1, 3, z1 + 6)
    for z in range(z1 + 2, z2, 4):
        d.lamp(9, 5, z)
        d.lamp(10, 5, z + 2)
    # loft: ladder up, hay stacks along both slopes
    for y in range(2, 7):
        d.set(10, y, z2 - 1, "ladder[facing=north,waterlogged=false]")
    for z in range(z1 + 1, z2 - 1):
        for x in (6, 13):
            hay(d, x, 7, z, "z")
            if z % 2:
                hay(d, x, 8, z, "z")
    path(d, 16, 0, 18, z1 + 2, "coarse_dirt")
    trough_x = 25
    hay(d, trough_x, 2, pz2 - 2)
    hay(d, trough_x - 1, 2, pz2 - 2)
    d.set(trough_x, 3, pz2 - 2, "hay_block[axis=y]")
    if L >= 2:
        d.sign(9, 7, z1 - 1, "north", ["Cedar Creek", "Dairy"], "spruce")
        d.set(x1 - 1, 2, z1 - 1, "barrel[facing=up,open=false]")
        d.set(x1 - 1, 3, z1 - 1, "lantern[hanging=false,waterlogged=false]")
    if L >= 4:                                                         # stave silo on the west side
        sx, sz = 1, z1 + 8
        for y in range(2, 13):
            for dx in (0, 1, 2):
                for dz in (0, 1, 2):
                    if (dx, dz) == (1, 1):
                        continue
                    d.set(sx + dx, y, sz + dz, "spruce_planks" if y % 3 else "stripped_spruce_log[axis=x]")
        d.set(sx + 1, 13, sz + 1, "dark_oak_planks")
        for dx in (0, 1, 2):
            for dz in (0, 1, 2):
                if (dx, dz) != (1, 1):
                    d.set(sx + dx, 13, sz + dz, slab("dark_oak_slab"))
        d.set(sx + 1, 14, sz + 1, slab("dark_oak_slab"))
        d.set(sx + 1, 1, sz + 1, "cobblestone")
        for y in range(2, 13):
            d.set(sx + 1, y, sz + 1, "hay_block[axis=y]")
    if L >= 5:
        d.chair(x1 + 1, 2, z1 - 1, "south", "spruce", sit=False)
        d.chair(x1 + 2, 2, z1 - 1, "south", "spruce", sit=False)
        d.set(x2 + 1, 2, z1 - 1, "spruce_fence")
        d.set(x2 + 1, 3, z1 - 1, "lantern[hanging=false,waterlogged=false]")
        d.set(9, ridge + 1, z1 + 4, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    return d


def cow_nt(rel, L):
    """Agri-tech dairy: glass milking parlour cube on the street corner, a long open-sided freestall barn
    behind it (columns, birch rails, flat solar roof), drinkers and a feed line inside, pasture on the east.
    L3 lengthens the freestall barn, L5 adds a green-roof terrace to the parlour."""
    d = farm_design("Neoterra", rel, (27, 14, 25), paving="smooth_stone")
    # pasture east of the parlour
    pen(d, 13, 2, 25, 10, "birch_fence", gates=[(19, 2), (13, 6)])
    # parlour
    x1, z1, x2, z2 = 2, 2, 10, 9
    nt_walls(d, x1, z1, x2, z2, 5, sides="nwe")
    nt_roof(d, x1, z1, x2, z2, 6, solar_rows=L < 5, green=L >= 5)
    d.double_door(5, 2, z1, "x", "south", "birch")
    d.door(6, 2, z2, "north", "birch")
    d.hut(x1 + 1, 2, z1 + 1)
    d.item(x1 + 1, 2, z1 + 2, "crafting_table")
    nr = need_racks(d)
    racks(d, [(x1 + 1, z) for z in range(z1 + 3, z1 + 3 + min(nr, 4))], 2, "east")
    if nr >= 5:
        d.rack(x1 + 2, 2, z2 - 1, "north")
    # milking stalls: herringbone row with steel (iron bars) rails and the milk tank
    for z in range(z1 + 2, z2 - 1):
        d.set(x2 - 2, 2, z, "iron_bars")
        d.set(x2 - 1, 2, z, "gray_carpet")
    d.set(x2 - 3, 2, z1 + 1, "iron_block")
    d.set(x2 - 3, 3, z1 + 1, "iron_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]")
    d.set(x2 - 1, 2, z1 + 1, "white_concrete")
    d.set(x2 - 1, 3, z1 + 1, "heavy_weighted_pressure_plate[power=0]")
    for x in range(x1 + 2, x2 - 1, 3):
        d.set(x, 5, z1 + 4, "sea_lantern")
    # covered link to the freestall barn
    path(d, 5, z2 + 1, 7, 11, "polished_andesite")
    # freestall barn
    bx2 = 14 if L < 3 else 24
    bz1, bz2 = 12, 22
    for x in range(x1, bx2 + 1):
        for z in range(bz1, bz2 + 1):
            d.set(x, 1, z, "smooth_stone")
            edge = x in (x1, bx2) or z in (bz1, bz2)
            col = edge and ((x - x1) % 4 == 0 and z in (bz1, bz2) or (z - bz1) % 5 == 0 and x in (x1, bx2))
            for y in range(2, 7):
                d.set(x, y, z, "light_gray_concrete" if col else AIR)
            if edge and not col:
                d.set(x, 2, z, "birch_fence")
                d.set(x, 1, z, "polished_andesite")
            d.set(x, 7, z, "smooth_quartz" if edge else "light_gray_stained_glass" if (x - x1) % 4 == 2 else
                  "smooth_quartz")
    d.flat(x1, bz1, bx2, bz2, 7, "smooth_quartz", "white_concrete", "smooth_quartz_slab")
    for x in range(x1 + 1, bx2):
        for z in range(bz1 + 1, bz2):
            if (x - x1) % 4 == 2:
                d.set(x, 7, z, "light_gray_stained_glass")
                d.set(x, 8, z, AIR)
            elif z % 2 == 0:
                d.set(x, 8, z, "daylight_detector[inverted=false,power=0]")
    d.set(6, 2, bz1, gate("birch", "north"))
    d.set(bx2, 2, 17, gate("birch", "east"))
    # inside: feed line (hay) along the middle, drinkers on the north side, cubicles to the south
    need_c = d.req["items"]["minecraft:water_cauldron"]
    cells = [(x, bz1 + 1) for x in range(x1 + 2, bx2 - 1, 2) if x != 6][:need_c]
    trough(d, cells)
    for x in range(x1 + 1, bx2):
        if x % 3 != 0:
            hay(d, x, 2, 17, "x")
    for x in range(x1 + 1, bx2, 2):
        for z in (bz2 - 2, bz2 - 1):
            d.set(x, 2, z, "iron_bars")
        if x + 1 < bx2:
            d.set(x + 1, 2, bz2 - 1, "gray_carpet")
    for x in range(x1 + 2, bx2, 4):
        d.set(x, 6, 15, "end_rod[facing=down]")
    d.sign(5, 6, z1 - 1, "north", ["AGRI-DAIRY", "fresh milk"], "birch", glow=True, color="cyan")
    if L >= 2:                                                         # canopy over the entrance
        for x in range(3, 9):
            d.set(x, 5, z1 - 1, slab("smooth_quartz_slab", "top"))
    if L >= 4:
        for x in range(x1, x2 + 1, 2):
            d.set(x, 1, 0, "moss_block")
            d.set(x, 2, 0, "azalea")
    if L >= 5:
        for y in range(2, 7):
            d.set(x2 - 1, y, z2 - 1, "ladder[facing=north,waterlogged=false]")
        for x in (x1 + 2, x2 - 2):
            d.chair(x, 7, z1 + 2, "north", "birch", sit=False)
    return d


@design("cowboy")
def cowboy(pack, rel, L):
    return farmstead({"Hearthwood": cow_hw, "Cascadia": cow_cs, "Neoterra": cow_nt}[pack], pack, rel, L, "cattle")


# ============================================================================================ SHEPHERD
def sheep_hw(rel, L):
    """Shearing barn & sheepfold: timber-framed barn with its gable to the lane, shearing floor, loom by the
    window, dye vats (water cauldrons) and wool bales; a dry-stone sheepfold beside it. L3 lengthens the barn,
    L4 adds a wool-drying line, L5 a shepherd's hut on wheels in the fold."""
    d = farm_design("Hearthwood", rel, (25, 18, 24), paving=GRASS)
    x1, x2, z1 = 3, 10, 3
    z2 = 11 if L < 3 else 15
    fz2 = 14 if L < 3 else 21
    stone_fold(d, x2, z1 + 1, 22, fz2, "cobblestone", "oak_fence", gates=[(16, fz2), (22, z1 + 4)])
    hw_walls(d, x1, z1, x2, z2, 5, floor="spruce_planks", infill="calcite")
    ridge = d.gable(x1, z1, x2, z2, 6, "z", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite")
    path(d, 6, 0, 7, z1 - 1, "gravel")
    d.double_door(6, 2, z1, "x", "south", "dark_oak")
    d.window(4, 3, z1, 4, 4, z1)
    d.window(9, 3, z1, 9, 4, z1)
    d.window(x1, 3, 7, x1, 4, 8)
    d.set(6, ridge - 2, z1, "glass_pane")
    d.set(7, ridge - 2, z1, "glass_pane")
    d.hut(x1 + 1, 2, z1 + 1)
    d.item(x1 + 1, 2, z1 + 2, "crafting_table")
    d.item(x1 + 1, 2, 7, "loom", "east")
    d.chair(x1 + 2, 2, 7, "east", "dark_oak", sit=False)
    # dye vats against the west wall + wool of each colour
    trough(d, [(x1 + 1, 9), (x1 + 1, 10), (x1 + 2, z2 - 1)])
    for i, col in enumerate(("white_wool", "light_gray_wool", "brown_wool")):
        d.set(x2 - 1, 2, z2 - 1 - i, col)
        d.set(x2 - 1, 3, z2 - 1 - i, "white_wool" if i != 1 else "black_wool")
    d.set(x2 - 2, 2, z2 - 1, "white_wool")
    nr = need_racks(d)
    racks(d, [(x2 - 1, z) for z in range(z1 + 1, z1 + 1 + min(nr, 4))], 2, "west")
    if nr >= 5:
        d.rack(x2 - 2, 2, z1 + 1, "south")
    # shearing pen: hurdles round a board, gate from the fold through the east wall
    for z in (6, 8):
        d.set(x2 - 3, 2, z, "oak_fence")
    d.set(x2 - 3, 2, 7, gate("oak", "east"))
    d.set(x2, 2, 7, gate("oak", "east"))
    d.set(x2, 3, 7, AIR)
    d.set(x2 - 2, 1, 7, "stripped_oak_wood[axis=y]")
    d.set(x2 - 2, 2, 6, AIR)
    d.banner(x2 - 1, 4, z2 - 3, "west", "white")
    d.lamp(6, 5, 6)
    d.lamp(6, 5, z2 - 3)
    # fold furniture: hay racks, water trough, a shelter tree
    hay(d, 20, 2, fz2 - 1)
    d.set(19, 2, fz2 - 1, "hay_block[axis=x]")
    d.set(21, 2, z1 + 2, "water_cauldron[level=3]")
    if L >= 2:
        d.sign(5, 4, z1 - 1, "north", ["Fleece &", "Fold"], "dark_oak")
        for x in (x1, x1 + 1, x2 - 1, x2):
            d.set(x, 2, z1 - 1, "potted_allium" if x % 2 else "potted_cornflower")
    if L >= 4:                                                          # wool drying line behind the barn
        for z in (z2 + 2, z2 + 6):
            if z < 23:
                for y in (2, 3, 4):
                    d.set(5, y, z, "oak_fence")
        for z in range(z2 + 3, min(z2 + 6, 23)):
            d.set(5, 4, z, "white_wool" if z % 2 else "light_gray_wool")
    if L >= 5:                                                          # shepherd's hut on wheels in the fold
        hx1, hz1 = 17, fz2 - 6
        for x in range(hx1, hx1 + 4):
            for z in (hz1, hz1 + 1, hz1 + 2):
                d.set(x, 3, z, "dark_oak_planks" if x in (hx1, hx1 + 3) or z != hz1 + 1 else "oak_planks")
                d.set(x, 4, z, "green_terracotta" if not (x == hx1 + 1 and z == hz1) else "glass_pane")
                d.set(x, 5, z, slab("dark_oak_slab", "bottom") if z == hz1 + 1 else st("dark_oak_stairs",
                                                                                       "south" if z == hz1 else "north"))
        for x in (hx1, hx1 + 3):
            for z in (hz1, hz1 + 2):
                d.set(x, 2, z, "dark_oak_fence")
        d.set(hx1 + 1, 4, hz1 + 1, AIR)
        d.set(hx1 + 2, 4, hz1 + 1, AIR)
        d.set(hx1 - 1, 2, hz1 + 1, st("dark_oak_stairs", "east"))
    return d


def sheep_cs(rel, L):
    """Ranch shearing shed: long log shed with a deep covered shearing porch to the road, wool press and
    loom, wash tubs; a big rail-fenced sheep pasture behind with a run-in shelter. L3 lengthens the shed,
    L5 adds a sheepdog kennel and pasture shelter."""
    d = farm_design("Cascadia", rel, (27, 16, 26), paving=GRASS)
    x1, z1, z2 = 3, 8, 14
    x2 = 12 if L < 3 else 17
    pz2 = 20 if L < 3 else 24
    px2 = 18 if L < 3 else 24
    pen(d, 2, z2, px2, pz2, "spruce_fence", gates=[(px2, z2 + 3)], patches=("coarse_dirt", 9))
    cs_logs(d, x1, z1, x2, z2, 4)
    ridge = d.gable(x1, z1, x2, z2, 5, "x", "dark_oak_stairs", "dark_oak_slab", "spruce_planks")
    # porch: lean-to on posts, rail along the front
    pz = 4
    d.fill(x1, 1, pz, x2, 1, z1 - 1, "spruce_planks")
    for x in range(x1 - 1, x2 + 2):
        d.set(x, 4, pz - 1, st("dark_oak_stairs", "south"))
        for z in range(pz, z1):
            d.set(x, 5 if z >= z1 - 1 else 4, z, slab("dark_oak_slab") if z < z1 - 1 else st("dark_oak_stairs", "south"))
    for x in range(x1, x2 + 1, 3):
        for y in (2, 3):
            d.set(x, y, pz, "spruce_log[axis=y]")
    for x in range(x1 + 1, x2):
        if d.air(x, 2, pz) and x not in (7, 8):
            d.set(x, 2, pz, "spruce_fence")
    path(d, 7, 0, 8, pz - 1, "dirt_path")
    d.double_door(7, 2, z1, "x", "south", "spruce")
    for x in (x1 + 2, x2 - 2):
        d.window(x, 3, z1, x, 3, z1)
    # shearing board on the porch: stripped stump + wool basket
    d.set(5, 2, 6, "stripped_spruce_wood[axis=y]")
    d.set(4, 2, 6, "white_wool")
    d.set(10, 2, 6, "white_wool")
    d.set(10, 3, 6, "white_wool")
    d.chair(11, 2, 6, "south", "spruce", sit=False)
    # inside
    d.hut(x1 + 1, 2, z1 + 1)
    d.item(x1 + 1, 2, z1 + 2, "crafting_table")
    d.item(x1 + 1, 2, z1 + 4, "loom", "east")
    trough(d, [(x1 + 1, z2 - 1), (x1 + 2, z2 - 1), (x1 + 3, z2 - 1)])
    nr = need_racks(d)
    racks(d, [(x, z1 + 1) for x in range(x2 - 1, x2 - 1 - min(nr, 4), -1)], 2, "south")
    if nr >= 5:
        d.rack(x2 - 1, 2, z1 + 2, "west")
    for x in range(x1 + 5, x2 - 1, 2):                                 # wool press / bales
        d.set(x, 2, z2 - 1, "white_wool")
        d.set(x, 3, z2 - 1, "white_wool" if x % 4 else "brown_wool")
    d.set(x1 + 4, 2, z2 - 1, "piston[extended=false,facing=up]")
    d.set(9, 2, z2, gate("spruce", "south"))
    d.set(9, 3, z2, AIR)
    d.lamp(6, 4, 11)
    d.lamp(x2 - 3, 4, 11)
    # pasture: hay feeder and a log run-in shelter
    hay(d, px2 - 2, 2, pz2 - 1)
    hay(d, px2 - 3, 2, pz2 - 1)
    if L >= 2:
        d.set(x2 + 1, 2, pz, "barrel[facing=up,open=false]")
        d.set(x2 + 1, 3, pz, "lantern[hanging=false,waterlogged=false]")
    if L >= 4:                                                          # run-in shelter in the pasture
        sx1, sz1 = 4, pz2 - 4
        for x in range(sx1, sx1 + 5):
            d.set(x, 4, sz1, st("dark_oak_stairs", "south"))
            for z in range(sz1 + 1, sz1 + 3):
                d.set(x, 4, z, slab("dark_oak_slab"))
            d.set(x, 2, sz1 + 3, "stripped_spruce_log[axis=x]")
            d.set(x, 3, sz1 + 3, "stripped_spruce_log[axis=x]")
        for x in (sx1, sx1 + 4):
            for y in (2, 3):
                d.set(x, y, sz1, "spruce_log[axis=y]")
                d.set(x, y, sz1 + 3, "spruce_log[axis=y]")
            d.set(x, 4, sz1 + 3, slab("dark_oak_slab"))
        hay(d, sx1 + 2, 2, sz1 + 2, "x")
    if L >= 5:                                                          # dog kennel and signage
        d.set(x2 + 2, 2, 7, "spruce_planks")
        d.set(x2 + 2, 3, 7, st("spruce_stairs", "east"))
        d.set(x2 + 3, 3, 7, st("spruce_stairs", "west"))
        d.set(x2 + 3, 2, 7, "spruce_planks")
        d.set(x2 + 2, 2, 6, "white_carpet")
        d.sign(9, ridge - 1, z1 - 1, "north", ["Woolly Ridge", "Ranch"], "spruce")
    return d


def sheep_nt(rel, L):
    """Wool lab: white textile studio with a north-light sawtooth roof, loom and dyeing line inside, glass
    street front showing the bolts of wool; pasture behind with a smart shelter. L3 adds a teeth row, L5 a
    rooftop wind turbine mast and street planters."""
    d = farm_design("Neoterra", rel, (23, 16, 25), paving="smooth_stone")
    x1, z1, x2 = 2, 2, 14
    z2 = 8 if L < 3 else 11
    pz2 = 19 if L < 3 else 23
    pen(d, 2, z2, 20, pz2, "birch_fence", gates=[(20, z2 + 3)])
    nt_walls(d, x1, z1, x2, z2, 4, sides="new", col_step=3)
    sawtooth(d, x1, z1, x2, z2, 5, "smooth_quartz_stairs", "light_blue_stained_glass", "white_concrete")
    d.double_door(7, 2, z1, "x", "south", "birch")
    d.hut(x1 + 1, 2, z1 + 1)
    d.item(x1 + 1, 2, z1 + 2, "crafting_table")
    d.item(x1 + 3, 2, z1 + 3, "loom", "north")
    d.chair(x1 + 3, 2, z1 + 4, "south", "birch", sit=False)
    trough(d, [(x2 - 1, z1 + 1), (x2 - 2, z1 + 1), (x2 - 3, z1 + 1)])
    for i, c in enumerate(("cyan", "light_blue", "white", "lime")):    # coloured wool shelves (display)
        d.set(x2 - 1, 2, z1 + 2 + i, f"{c}_wool")
    nr = need_racks(d)
    racks(d, [(x, z2 - 1) for x in range(x1 + 1, x1 + 1 + nr)], 2, "north")
    d.set(8, 2, z2, gate("birch", "south"))
    d.set(8, 3, z2, AIR)
    for x in range(x1 + 2, x2 - 1, 3):
        d.set(x, 4, z1 + 3, "end_rod[facing=down]")
    path(d, 7, 0, 8, z1 - 1, "polished_andesite")
    d.sign(5, 4, z1 - 1, "north", ["WOOL LAB", "textiles"], "birch", glow=True, color="cyan")
    # pasture: shelter with green roof and a drinker
    hay(d, 18, 2, pz2 - 2)
    hay(d, 17, 2, pz2 - 2)
    for x in range(4, 9):
        for z in range(pz2 - 4, pz2):
            d.set(x, 4, z, "moss_block")
    for x, z in ((4, pz2 - 4), (8, pz2 - 4), (4, pz2 - 1), (8, pz2 - 1)):
        d.set(x, 2, z, "light_gray_concrete")
        d.set(x, 3, z, "light_gray_concrete")
    if L >= 2:
        for x in (x1, x2):
            d.set(x, 2, 0, "potted_bamboo")
    if L >= 4:
        for x in range(10, 14):
            d.set(x, 1, 0, "moss_block")
            d.set(x, 2, 0, "flowering_azalea" if x % 2 else "azalea")
    if L >= 5:                                                          # wind turbine mast
        for y in range(2, 13):
            d.set(x2 + 2, y, z1 + 1, "light_gray_concrete" if y < 6 else "end_rod[facing=up]")
        for k in (1, 2):
            d.set(x2 + 2 + k, 12, z1 + 1, "end_rod[facing=east]")
            d.set(x2 + 2 - k, 12, z1 + 1, "end_rod[facing=west]")
            d.set(x2 + 2, 12 + k, z1 + 1, "end_rod[facing=up]")
    return d


@design("shepherd")
def shepherd(pack, rel, L):
    return farmstead({"Hearthwood": sheep_hw, "Cascadia": sheep_cs, "Neoterra": sheep_nt}[pack], pack, rel, L, "sheep")


# ============================================================================================ SWINEHERDER
def pig_hw(rel, L):
    """Brick pigsties: a timber-framed feed house (swill barrels, composter, racks) on a gravel lane, and a
    terrace of little brick sties with pent tiled roofs, each opening onto its own walled yard with a trough
    and a mud wallow. 2 sties at L1, 3 from L3, 4 at L5."""
    d = farm_design("Hearthwood", rel, (25, 16, 23), paving=GRASS)
    x1, z1, x2, z2 = 3, 3, 9, 9
    hw_walls(d, x1, z1, x2, z2, 5, floor="spruce_planks", infill="bricks")
    ridge = d.gable(x1, z1, x2, z2, 6, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite")
    path(d, 5, 0, 7, z1 - 1, "gravel")
    path(d, 10, 0, 11, 21, "gravel")
    d.door(6, 2, z1, "south", "dark_oak")
    d.door(x2, 2, 6, "east", "dark_oak")
    d.window(4, 3, z1, 4, 4, z1)
    d.window(8, 3, z1, 8, 4, z1)
    d.window(x1, 3, 6, x1, 4, 6)
    d.hut(x1 + 1, 2, z1 + 1)
    d.item(x1 + 1, 2, z1 + 2, "crafting_table")
    d.item(x2 - 1, 2, z2 - 1, "composter")
    nr = need_racks(d)
    racks(d, ([(x1 + 1, z) for z in (6, 7, 8)] + [(5, 8), (6, 8)])[:nr], 2, "east")
    for z in (z1 + 1, z1 + 2):                                          # swill barrels and a meal bin
        d.keg(x2 - 1, 2, z, "up")
    d.set(x2 - 2, 2, z1 + 1, "hay_block[axis=y]")
    d.lamp(6, 5, 6)
    # the sties
    n = 2 if L < 3 else 3 if L < 5 else 4
    need_c = d.req["items"]["minecraft:water_cauldron"]
    per = [need_c // n + (1 if i < need_c % n else 0) for i in range(n)]
    for i in range(n):
        za, zb = 3 + 4 * i, 7 + 4 * i
        for x in range(12, 23):
            for z in range(za, zb + 1):
                d.set(x, 1, z, GRASS)
                if x in (12, 22) or z in (za, zb):
                    d.set(x, 2, z, "bricks")
                    d.set(x, 3, z, "dark_oak_fence" if x < 19 else "bricks")
                else:
                    d.set(x, 2, z, AIR)
                    d.set(x, 3, z, AIR)
        d.set(12, 2, za + 2, gate("dark_oak", "east"))
        d.set(12, 3, za + 2, AIR)
        # sty house x19..22 with a pent roof falling to the yard
        for z in range(za, zb + 1):
            d.set(19, 2, z, "bricks")
            d.set(19, 3, z, "bricks")
            for x in range(18, 23):
                d.set(x, 4, z, st("deepslate_tile_stairs", "east") if x == 18 else
                      slab("deepslate_tile_slab", "bottom") if x < 21 else "deepslate_tiles")
            d.set(22, 5, z, slab("deepslate_tile_slab"))
        d.set(19, 2, za + 2, AIR)
        d.set(19, 3, za + 2, AIR)
        for x in (20, 21):
            d.set(x, 1, za + 1, "hay_block[axis=x]")
            d.set(x, 1, za + 3, "hay_block[axis=x]")
        # yard: trough by the gate, mud wallow
        for k in range(per[i]):
            d.item(13 + k, 2, za + 1, "water_cauldron[level=3]")
        for x in (15, 16, 17):
            for z in (za + 2, za + 3):
                d.set(x, 1, z, "mud" if (x, z) != (16, za + 2) else "water")
    if L >= 2:
        d.sign(6, 4, z1 - 1, "north", ["Swine", "Cote"], "dark_oak")
        d.set(x1 + 1, 2, z1 - 1, "potted_red_tulip")
    if L >= 4:                                                          # muck heap and apple tree by the lane
        for x in (4, 5):
            for z in (14, 15):
                d.set(x, 1, z, "podzol[snowy=false]")
                d.set(x, 2, z, "composter[level=8]" if (x + z) % 2 else "coarse_dirt")
        d.set(6, 2, 18, "oak_log[axis=y]")
        d.set(6, 3, 18, "oak_log[axis=y]")
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                d.set(6 + dx, 4, 18 + dz, "flowering_azalea_leaves[distance=1,persistent=true,waterlogged=false]")
        d.set(6, 5, 18, "flowering_azalea_leaves[distance=1,persistent=true,waterlogged=false]")
    if L >= 5:
        d.set(10, 2, 1, "dark_oak_fence")
        d.set(10, 3, 1, "lantern[hanging=false,waterlogged=false]")
        d.set(6, ridge + 1, 6, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    return d


def mono(d, x1, z1, x2, z2, y, stairs, slab_, end, overhang=1):
    """Skillion roof sloping down to the south: high at the north wall, one step per two rows."""
    rows = list(range(z1 - overhang, z2 + overhang + 1))
    n = len(rows)
    for i, z in enumerate(rows):
        k = (n - 1 - i)
        h = y + k // 2
        for x in range(x1 - overhang, x2 + overhang + 1):
            d.set(x, h, z, st(stairs, "north") if k % 2 == 0 else slab(slab_, "top"))
        if z1 <= z <= z2:
            for x in (x1, x2):
                for yy in range(y, h):
                    if d.air(x, yy, z):
                        d.set(x, yy, z, end)
    return y + (n - 1) // 2


def hog_hut(d, x0, z0, wood):
    """Little A-frame farrowing hut (3 x 3), open to the north."""
    for z in (z0, z0 + 1, z0 + 2):
        d.set(x0, 2, z, st(f"{wood}_stairs", "east"))
        d.set(x0 + 2, 2, z, st(f"{wood}_stairs", "west"))
        d.set(x0 + 1, 3, z, slab(f"{wood}_slab"))
        d.set(x0 + 1, 2, z, "hay_block[axis=z]" if z == z0 + 2 else AIR)
    d.set(x0 + 1, 2, z0 + 2, f"{wood}_planks")


def pig_cs(rel, L):
    """Hog barn: low log barn with a skillion roof on a river-rock footing, farrowing pens inside, and a
    muddy rail-fenced hog lot with A-frame hog huts, a long trough line and a mud wallow."""
    d = farm_design("Cascadia", rel, (27, 18, 24), paving=GRASS)
    x1, z1, x2, z2 = 3, 3, 11, 11
    lz2 = 14 if L < 3 else 21
    pen(d, x2, z1, 25, lz2, "spruce_fence", gates=[(18, lz2)], ground="coarse_dirt", patches=(GRASS, 3))
    cs_logs(d, x1, z1, x2, z2, 4)
    mono(d, x1, z1, x2, z2, 5, "dark_oak_stairs", "dark_oak_slab", "spruce_planks")
    path(d, 6, 0, 7, z1 - 1, "dirt_path")
    d.double_door(6, 2, z1, "x", "south", "spruce")
    d.window(4, 3, z1, 4, 3, z1)
    d.window(9, 3, z1, 9, 3, z1)
    d.hut(x1 + 1, 2, z1 + 1)
    d.item(x1 + 1, 2, z1 + 2, "crafting_table")
    d.item(x2 - 1, 2, z1 + 1, "composter")
    nr = need_racks(d)
    racks(d, [(x1 + 1, z) for z in range(z1 + 3, z1 + 3 + nr)], 2, "east")
    d.keg(x2 - 2, 2, z1 + 1, "up")
    d.keg(x2 - 1, 2, z1 + 2, "up")
    # farrowing pens on the east side, gates onto the hog lot
    for z in range(z1 + 4, z2):
        d.set(7, 2, z, "spruce_fence" if z != z1 + 6 else gate("spruce", "east"))
    d.set(8, 2, z1 + 7, "spruce_fence")
    d.set(9, 2, z1 + 7, "spruce_fence")
    d.set(8, 2, z1 + 4, "spruce_fence")
    d.set(9, 2, z1 + 4, "spruce_fence")
    for z in (z1 + 5, z2 - 1):
        hay(d, 9, 2, z, "z")
    d.set(x2, 2, z1 + 5, gate("spruce", "east"))
    d.set(x2, 3, z1 + 5, AIR)
    d.set(x2, 2, z2 - 2, gate("spruce", "east"))
    d.set(x2, 3, z2 - 2, AIR)
    d.lamp(5, 4, 7)
    # hog lot
    need_c = d.req["items"]["minecraft:water_cauldron"]
    trough(d, [(13 + i, z1 + 1) for i in range(need_c)])
    for x in range(16, 21):
        for z in range(z1 + 5, z1 + 9):
            if (x - 18) ** 2 + (z - z1 - 7) ** 2 <= 5:
                d.set(x, 1, z, "mud" if (x + z) % 3 else "water")
    hog_hut(d, 21, z1 + 4, "spruce")
    if L >= 3:
        hog_hut(d, 21, 15, "spruce")
        d.set(13, 2, 18, "spruce_log[axis=x]")
        d.set(14, 2, 18, "spruce_log[axis=x]")
    if L >= 2:
        d.sign(6, 4, z1 - 1, "north", ["Hog Barn"], "spruce")
        d.set(x1 - 1, 2, z1 - 1, "barrel[facing=up,open=false]")
    if L >= 4:                                                          # feed lean-to on the west wall
        for z in range(z1 + 1, z2):
            d.set(x1 - 1, 4, z, slab("dark_oak_slab", "top"))
            d.set(x1 - 2, 4, z, st("dark_oak_stairs", "east"))
        for z in (z1 + 1, z2 - 1):
            for y in (2, 3):
                d.set(x1 - 2, y, z, "spruce_log[axis=y]")
        for z in range(z1 + 2, z2 - 1):
            d.set(x1 - 1, 2, z, "barrel[facing=up,open=false]" if z % 3 == 0 else "hay_block[axis=z]")
    if L >= 5:
        d.set(x2 + 1, 2, 1, "spruce_fence")
        d.set(x2 + 1, 3, 1, "lantern[hanging=false,waterlogged=false]")
        for x in range(1, 5):
            d.set(x, 2, 22, "sweet_berry_bush[age=3]")
    return d


def pig_nt(rel, L):
    """Welfare pig unit: long low white barn with a glass clerestory band and green roof; indoor pens with
    steel rails and drinkers off a service corridor, each opening to an outdoor run with a mud wallow; the
    feed / office room is at the east end by the street path."""
    d = farm_design("Neoterra", rel, (23, 14, 23), paving="smooth_stone")
    x1, z1, x2, z2 = 2, 12, 20, 20
    rz1 = 6 if L < 3 else 2
    pen(d, 2, rz1, 13, z1, "birch_fence", gates=[(8, rz1)])
    nt_walls(d, x1, z1, x2, z2, 4, sides="nsew", glaze=(4, 4))
    nt_roof(d, x1, z1, x2, z2, 5, solar_rows=False, green=True)
    if L >= 3:
        solar(d, 15, z1 + 1, x2 - 1, z2 - 1, 6)
    path(d, 15, 0, 18, z1 - 1, "polished_andesite")
    d.double_door(16, 2, z1, "x", "south", "birch")
    # office / feed room x15..19
    for z in range(z1 + 1, z2):
        d.set(14, 2, z, "white_concrete" if z != z2 - 1 else AIR)
        d.set(14, 3, z, "white_concrete" if z != z2 - 1 else AIR)
        d.set(14, 4, z, "white_concrete")
    d.hut(x2 - 1, 2, z1 + 1)
    d.item(x2 - 1, 2, z1 + 2, "crafting_table")
    d.item(x2 - 1, 2, z1 + 3, "composter")
    nr = need_racks(d)
    racks(d, [(x2 - 1, z) for z in range(z1 + 4, z1 + 4 + min(nr, 3))], 2, "west")
    racks(d, [(x, z2 - 1) for x in (x2 - 2, x2 - 3)][:max(0, nr - 3)], 2, "north")
    d.set(15, 2, z1 + 1, "hopper[enabled=true,facing=down]")
    d.set(15, 3, z1 + 1, "iron_block")
    d.set(17, 4, z1 + 4, "sea_lantern")
    # pens x3..13: steel rails, drinkers, gate to the run; corridor along the south wall
    need_c = d.req["items"]["minecraft:water_cauldron"]
    c = 0
    for x in range(x1 + 1, 14):
        d.set(x, 2, z2 - 2, "iron_bars" if x % 4 != 0 else gate("birch", "south"))
        if x % 4 == 3:
            for z in range(z1 + 1, z2 - 2):
                if x + 2 < 14:
                    d.set(x + 2, 2, z, "iron_bars")
    for x in range(x1 + 1, 14):
        if x % 4 == 1 and c < need_c:
            d.item(x, 2, z2 - 3, "water_cauldron[level=3]")
            c += 1
    for x in range(x1 + 1, 14):
        if c < need_c and d.air(x, 2, z1 + 1) and x % 2 == 0:
            d.item(x, 2, z1 + 1, "water_cauldron[level=3]")
            c += 1
    for x in range(x1 + 1, 14, 4):
        d.set(x + 1, 2, z1, gate("birch", "north"))
        d.set(x + 1, 3, z1, AIR)
    for x in range(x1 + 2, 14, 3):
        d.set(x, 5, z2 - 1, "sea_lantern")
    # run: mud wallow and shade
    for x in range(4, 8):
        for z in range(z1 - 4, z1 - 1):
            d.set(x, 1, z, "mud" if (x + z) % 4 else "water")
    d.sign(16, 4, z1 - 1, "north", ["PORK & CO", "welfare farm"], "birch", glow=True, color="cyan")
    if L >= 2:
        for x in range(15, 19):
            d.set(x, 4, z1 - 1, slab("smooth_quartz_slab", "top"))
    if L >= 4:
        for z in range(2, z1 - 1, 2):
            d.set(20, 1, z, "moss_block")
            d.set(20, 2, z, "azalea")
    if L >= 5:
        for x in (10, 11):
            for z in (rz1 + 1, rz1 + 2):
                d.set(x, 4, z, "smooth_quartz_slab[type=bottom,waterlogged=false]")
        for x, z in ((10, rz1 + 1),):
            d.set(x, 2, z, "light_gray_concrete")
            d.set(x, 3, z, "light_gray_concrete")
    return d


@design("swineherder")
def swineherder(pack, rel, L):
    return farmstead({"Hearthwood": pig_hw, "Cascadia": pig_cs, "Neoterra": pig_nt}[pack], pack, rel, L, "pig")


# ============================================================================================ RABBIT HUTCH
def hutch_row(d, x1, x2, z, y, wood, face, tiers=2):
    """Row of rabbit hutches on legs: per tier a bedding cell (hay) behind a wire front, slab lid on top.
    Built along x at row z, fronts facing `face` (north/south)."""
    fz = z + D4[face][1]
    for x in range(x1, x2 + 1):
        d.set(x, y, z, f"{wood}_fence")
        for t in range(tiers):
            d.set(x, y + 1 + t, z, "hay_block[axis=x]" if (x + t) % 2 else f"{wood}_planks")
        d.set(x, y + 1 + tiers, z, slab(f"{wood}_slab"))
        for t in range(tiers):
            d.set(x, y + 1 + t, fz, trap(wood, face, "bottom", open_=True) if (x + t) % 2 else "iron_bars")


def hutch_col(d, x, z1, z2, y, wood, face, tiers=2):
    """Same as hutch_row, running along z with fronts facing east/west."""
    fx = x + D4[face][0]
    for z in range(z1, z2 + 1):
        d.set(x, y, z, f"{wood}_fence")
        for t in range(tiers):
            d.set(x, y + 1 + t, z, "hay_block[axis=z]" if (z + t) % 2 else f"{wood}_planks")
        d.set(x, y + 1 + tiers, z, slab(f"{wood}_slab"))
        for t in range(tiers):
            d.set(fx, y + 1 + t, z, "iron_bars")


def carrots(d, x1, z1, x2, z2, water=None):
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            d.set(x, 1, z, "farmland[moisture=7]")
            d.set(x, 2, z, "carrots[age=7]" if (x + z) % 3 else "carrots[age=5]")
    if water:
        d.set(water[0], 1, water[1], "water")
        d.set(water[0], 2, water[1], AIR)


def rabbit_hw(rel, L):
    """Rabbit warren cottage: a tiny brick-and-plaster cottage with a catslide roof, tiered hutches along
    the inside walls and a fenced rabbit garden behind with carrot rows; L3 adds an outdoor hutch range under
    a pent roof, L5 a garden well and flower border."""
    d = farm_design("Hearthwood", rel, (19, 16, 20), paving=GRASS)
    x1, z1, x2, z2 = 3, 3, 11, 9
    gz2 = 14 if L < 3 else 18
    pen(d, 2, z2, 16, gz2, "oak_fence", gates=[(16, z2 + 2)])
    hw_walls(d, x1, z1, x2, z2, 5, floor="oak_planks", infill="calcite")
    ridge = d.gable(x1, z1, x2, z2 + 1, 6, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite")
    path(d, 6, 0, 7, z1 - 1, "gravel")
    d.door(7, 2, z1, "south", "dark_oak")
    for x in (5, 9):
        d.window(x, 3, z1, x, 4, z1)
    d.set(x1 + 1, 4, z1 - 1, trap("dark_oak", "north", "top"))
    d.hut(x1 + 1, 2, z1 + 1)
    d.item(x1 + 2, 2, z1 + 1, "crafting_table")
    nr = need_racks(d)
    racks(d, [(x2 - 1, z) for z in range(z1 + 1, z1 + 1 + min(nr, 4))], 2, "west")
    if nr >= 5:
        d.rack(x2 - 2, 2, z1 + 1, "south")
    hutch_col(d, x1 + 1, z1 + 3, z2 - 1, 2, "oak", "east", tiers=1)
    hutch_row(d, x1 + 3, x2 - 3, z2 - 1, 2, "oak", "north", tiers=1)
    d.set(7, 2, 6, "brown_carpet")
    d.set(6, 2, 6, "brown_carpet")
    d.lamp(7, 5, 6)
    d.door(x2 - 2, 2, z2, "north", "dark_oak")
    # garden: carrot rows, clover, a hollow log burrow
    carrots(d, 4, z2 + 2, 9, z2 + 3, water=(7, z2 + 2))
    d.set(12, 2, z2 + 3, "oak_log[axis=x]")
    d.set(13, 2, z2 + 3, "oak_log[axis=x]")
    for x in range(11, 15):
        if x % 2:
            d.set(x, 2, z2 + 1, "short_grass")
    if L >= 3:                                                          # outdoor hutch range with pent roof
        hutch_row(d, 4, 13, gz2 - 1, 2, "dark_oak", "north", tiers=2)
        for x in range(3, 15):
            d.set(x, 5, gz2 - 1, st("deepslate_tile_stairs", "north"))
            d.set(x, 5, gz2 - 2, slab("deepslate_tile_slab"))
        for y in (2, 3, 4):
            d.set(3, y, gz2 - 2, "dark_oak_fence")
            d.set(14, y, gz2 - 2, "dark_oak_fence")
        carrots(d, 4, z2 + 5, 9, z2 + 5)
    if L >= 2:
        d.sign(9, 2, z1 - 1, "north", ["Warren", "Cottage"], "dark_oak")
    if L >= 4:
        for x in (1, 2, 3, 4, 10, 11, 12):
            d.set(x, 2, 1, "poppy" if x % 2 else "cornflower")
    if L >= 5:                                                          # well
        wx, wz = 15, 4
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                d.set(wx + dx, 2, wz + dz, "cobblestone" if (dx, dz) != (0, 0) else "water")
                d.set(wx + dx, 1, wz + dz, "cobblestone" if (dx, dz) != (0, 0) else "water")
        for dx in (-1, 1):
            d.set(wx + dx, 3, wz, "oak_fence")
            d.set(wx + dx, 4, wz, "oak_fence")
        for dx in (-1, 0, 1):
            d.set(wx + dx, 5, wz, slab("deepslate_tile_slab"))
        d.set(wx, 4, wz, "chain[axis=y,waterlogged=false]")
        d.set(x1 + 4, ridge + 1, 6, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    return d


def rabbit_cs(rel, L):
    """Rabbitry cabin: steep A-frame log cabin with its gable to the road, a two-tier hutch range under a
    lean-to on the east wall, and a rail-fenced rabbit run with a carrot patch and hollow logs."""
    d = farm_design("Cascadia", rel, (21, 16, 21), paving=GRASS)
    x1, z1, x2, z2 = 3, 3, 9, 10
    rz2 = 13 if L < 3 else 19
    pen(d, 12, 2, 19, rz2, "spruce_fence", gates=[(15, 2)], patches=("coarse_dirt", 6))
    cs_logs(d, x1, z1, x2, z2, 3)
    ridge = d.gable(x1, z1, x2, z2, 4, "z", "dark_oak_stairs", "dark_oak_slab", "spruce_planks", overhang=1)
    path(d, 6, 0, 6, z1 - 1, "dirt_path")
    d.door(6, 2, z1, "south", "spruce")
    d.window(6, 5, z1, 6, 6, z1)
    d.window(4, 3, z1, 4, 3, z1)
    d.window(8, 3, z1, 8, 3, z1)
    d.hut(x1 + 1, 2, z1 + 1)
    d.item(x2 - 1, 2, z1 + 1, "crafting_table")
    nr = need_racks(d)
    racks(d, [(x1 + 1, z) for z in range(z1 + 2, z1 + 2 + nr)], 2, "east")
    d.set(x2 - 1, 2, z2 - 1, "barrel[facing=up,open=false]")
    d.set(x2 - 1, 2, z2 - 2, "barrel[facing=up,open=false]")
    d.set(x2 - 1, 3, z2 - 1, "lantern[hanging=false,waterlogged=false]")
    d.set(x2 - 2, 2, z2 - 1, "hay_block[axis=y]")
    d.set(6, 5, 6, "lantern[hanging=true,waterlogged=false]")
    d.door(x2, 2, 6, "east", "spruce")
    # hutch range on the east wall under a lean-to
    for z in range(z1 + 4, z2 + 1):
        d.set(x2 + 1, 2, z, "spruce_fence")
        d.set(x2 + 1, 3, z, "hay_block[axis=z]" if z % 2 else "spruce_planks")
        d.set(x2 + 1, 4, z, "hay_block[axis=z]" if z % 2 == 0 else "spruce_planks")
        d.set(x2 + 2, 3, z, "iron_bars")
        d.set(x2 + 2, 4, z, "iron_bars")
        d.set(x2 + 1, 5, z, st("dark_oak_stairs", "west"))
        d.set(x2 + 2, 5, z, slab("dark_oak_slab"))
    # run: carrot patch, hollow logs, clover
    carrots(d, 13, rz2 - 3, 16, rz2 - 2)
    d.set(17, 2, 5, "spruce_log[axis=z]")
    d.set(17, 2, 6, "spruce_log[axis=z]")
    for x, z in ((14, 4), (16, 8), (13, 9)):
        d.set(x, 2, z, "fern")
    if L >= 2:
        d.sign(6, 4, z1 - 1, "north", ["Bunny", "Barn"], "spruce")
    if L >= 4:                                                          # porch deck at the gable
        d.fill(x1, 1, 1, x2, 1, z1 - 1, "spruce_planks")
        for x in (x1, x2):
            for y in (2, 3):
                d.set(x, y, 1, "spruce_log[axis=y]")
        for x in range(x1, x2 + 1):
            d.set(x, 4, 1, slab("dark_oak_slab"))
            d.set(x, 4, 2, slab("dark_oak_slab"))
        d.chair(x1 + 1, 2, 2, "south", "spruce", sit=False)
    if L >= 5:
        for z in range(13, 20):
            d.set(4, 2, z, "sweet_berry_bush[age=3]")
        d.set(8, 2, 16, "spruce_log[axis=y]")
        d.set(8, 3, 16, "carved_pumpkin[facing=north]")
    return d


def rabbit_nt(rel, L):
    """Rabbitry studio: low glass pavilion with an indoor clover run, white hutch pods with cyan doors and
    a skylit flat roof; a street-side outdoor run with raised carrot planters."""
    d = farm_design("Neoterra", rel, (17, 12, 21), paving="smooth_stone")
    x1, z1, x2, z2 = 2, 9, 14, 18
    rz1 = 4 if L < 3 else 2
    pen(d, 2, rz1, 9, z1 - 1, "birch_fence", gates=[(5, rz1)])
    nt_walls(d, x1, z1, x2, z2, 4, sides="new", col_step=3)
    d.flat(x1, z1, x2, z2, 5, "smooth_quartz", "white_concrete", "smooth_quartz_slab")
    for x in range(x1 + 2, x2 - 1):
        for z in range(z1 + 2, z2 - 1, 3):
            d.set(x, 5, z, "glass")
    path(d, 11, 0, 12, z1 - 1, "polished_andesite")
    d.double_door(11, 2, z1, "x", "south", "birch")
    d.hut(x2 - 1, 2, z1 + 1)
    d.item(x2 - 1, 2, z1 + 2, "crafting_table")
    nr = need_racks(d)
    racks(d, [(x2 - 1, z) for z in range(z1 + 3, z1 + 3 + nr)], 2, "west")
    # indoor run: moss floor behind a low glass barrier, hutch pods along the back wall
    for x in range(x1 + 1, 9):
        for z in range(z1 + 1, z2):
            d.set(x, 1, z, "moss_block")
    for z in range(z1 + 1, z2):
        d.set(9, 2, z, "glass_pane" if z != z1 + 4 else gate("birch", "east"))
    for x in range(x1 + 1, 9):
        d.set(x, 2, z2 - 1, "white_concrete" if x % 2 else "cyan_terracotta")
        d.set(x, 3, z2 - 1, slab("smooth_quartz_slab"))
    for x in range(x1 + 2, 9, 2):
        d.set(x, 2, z2 - 2, "hay_block[axis=x]")
    carrots(d, x1 + 2, z1 + 2, x1 + 4, z1 + 2)
    for x in range(x1 + 1, x2, 3):
        d.set(x, 4, z1 + 5, "end_rod[facing=down]")
    # outdoor run: raised planters
    for x in range(3, 9):
        d.set(x, 1, z1 - 2, "smooth_quartz")
    carrots(d, 3, rz1 + 1, 4, rz1 + 2)
    d.sign(7, 4, z1 - 1, "north", ["RABBITRY", "clover & co"], "birch", glow=True, color="cyan")
    if L >= 2:
        for x in range(10, 14):
            d.set(x, 4, z1 - 1, slab("smooth_quartz_slab", "top"))
    if L >= 4:
        for z in range(1, z1 - 1, 2):
            d.set(14, 1, z, "moss_block")
            d.set(14, 2, z, "azalea")
    if L >= 5:
        solar(d, x1 + 1, z1 + 1, x2 - 1, z1 + 1, 6)
        solar(d, x1 + 1, z2 - 1, x2 - 1, z2 - 1, 6)
    return d


@design("rabbithutch")
def rabbithutch(pack, rel, L):
    return farmstead({"Hearthwood": rabbit_hw, "Cascadia": rabbit_cs, "Neoterra": rabbit_nt}[pack], pack, rel, L, "rabbit")


# ============================================================================================ BEEKEEPER
def flowers(d, x1, z1, x2, z2, kinds, ground=GRASS, step=1):
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            d.set(x, 1, z, ground)
            if (x + 2 * z) % step == 0:
                d.set(x, 2, z, kinds[(x * 3 + z) % len(kinds)])


def bee_hw(rel, L):
    """Honey house & bee garden: a little timber-framed honey house (extracting bench, racks, honey jars,
    candles) beside a walled cottage garden whose south brick wall holds the hives in bee boles; lavender
    and flower beds, fruit trees, gravel paths."""
    d = farm_design("Hearthwood", rel, (21, 14, 21), paving=GRASS)
    x1, z1, x2, z2 = 3, 3, 9, 9
    hw_walls(d, x1, z1, x2, z2, 4, floor="oak_planks", infill="calcite")
    ridge = d.gable(x1, z1, x2, z2, 5, "z", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite")
    path(d, 6, 0, 6, z1 - 1, "gravel")
    d.door(6, 2, z1, "south", "dark_oak")
    d.window(4, 3, z1, 4, 3, z1)
    d.window(8, 3, z1, 8, 3, z1)
    d.window(x1, 3, 6, x1, 3, 7)
    d.door(x2, 2, 7, "east", "dark_oak")
    d.hut(x1 + 1, 2, z1 + 1)
    d.item(x1 + 1, 2, z1 + 2, "crafting_table")
    nr = need_racks(d)
    racks(d, [(x1 + 1, z) for z in range(z2 - 1, z2 - 1 - nr, -1)], 2, "east")
    # extracting bench: honey blocks, bottles (brewing stand), candles on the counter
    for x in range(x1 + 3, x2):
        d.set(x, 2, z2 - 1, slab("oak_slab", "top"))
    d.set(x1 + 3, 3, z2 - 1, "honey_block")
    d.set(x1 + 4, 3, z2 - 1, "candle[candles=3,lit=false,waterlogged=false]")
    d.set(x1 + 5, 3, z2 - 1, "brewing_stand[has_bottle_0=true,has_bottle_1=true,has_bottle_2=false]")
    d.set(x2 - 1, 2, z1 + 1, "honeycomb_block")
    d.set(x2 - 1, 3, z1 + 1, "honeycomb_block")
    d.lamp(6, 4, 6)
    # walled garden east of the house
    gx1, gx2, gz1, gz2 = 10, 19, 3, 17
    for x in range(gx1, gx2 + 1):
        for z in range(gz1, gz2 + 1):
            edge = x in (gx1, gx2) or z in (gz1, gz2)
            if edge:
                d.set(x, 2, z, "bricks")
                d.set(x, 3, z, slab("brick_slab") if z != gz2 else "bricks")
    d.set(gx1, 2, 7, AIR)
    d.set(gx1, 3, 7, AIR)
    d.set(14, 2, gz1, gate("dark_oak", "north"))
    d.set(14, 3, gz1, AIR)
    path(d, 14, 0, 14, gz1 - 1, "gravel")
    # bee wall: the south garden wall is raised to 4 high with boles holding the hives
    hives = d.req["yard"]["minecraft:beehive"]
    bole_x = [12, 14, 16, 18]
    for x in range(gx1, gx2 + 1):
        for y in (4, 5):
            d.set(x, y, gz2, "bricks")
        d.set(x, 6, gz2, slab("deepslate_tile_slab"))
    for i, x in enumerate(bole_x):
        if i < hives:
            d.yard_item(x, 3, gz2, "beehive[facing=north,honey_level=3]")
        else:
            d.set(x, 3, gz2, "beehive[facing=north,honey_level=0]" if L >= 4 else "bricks")
    # paths and beds
    for x in range(gx1 + 1, gx2):
        d.set(x, 1, 7, "gravel")
    for z in range(gz1 + 1, gz2):
        d.set(14, 1, z, "gravel")
    flowers(d, gx1 + 1, gz1 + 1, 13, 6, ("allium", "lily_of_the_valley", "cornflower"))
    flowers(d, 15, gz1 + 1, gx2 - 1, 6, ("oxeye_daisy", "poppy", "azure_bluet"))
    flowers(d, gx1 + 1, 8, 13, gz2 - 2, ("cornflower", "allium", "lily_of_the_valley"), step=2)
    flowers(d, 15, 8, gx2 - 1, gz2 - 2, ("dandelion", "oxeye_daisy", "poppy"), step=2)
    if L >= 2:
        d.sign(5, 3, z1 - 1, "north", ["Honey", "House"], "dark_oak")
    if L >= 3:                                                          # apple tree (flowering) in the garden
        for tx, tz in ((12, 11),):
            d.set(tx, 2, tz, "oak_log[axis=y]")
            d.set(tx, 3, tz, "oak_log[axis=y]")
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    d.set(tx + dx, 4, tz + dz, "flowering_azalea_leaves[distance=1,persistent=true,waterlogged=false]")
            d.set(tx, 5, tz, "flowering_azalea_leaves[distance=1,persistent=true,waterlogged=false]")
    if L >= 4:
        d.chair(17, 2, 11, "east", "dark_oak", sit=False)
        d.chair(17, 2, 12, "east", "dark_oak", sit=False)
    if L >= 5:                                                          # skeps on a bench by the house
        for z in range(11, 16):
            d.set(4, 2, z, "peony[half=lower]")
            d.set(4, 3, z, "peony[half=upper]")
        d.set(6, 2, 12, "beehive[facing=north,honey_level=5]")
        d.set(7, 2, 12, "beehive[facing=north,honey_level=5]")
        d.set(6, 1, 12, "stone_bricks")
    return d


def bee_cs(rel, L):
    """Mountain apiary: log honey shack with a deep porch and stone chimney (wax melting stove), hives on
    log stump stands in a wildflower meadow behind a spruce rail fence, sunflowers along the fence."""
    d = farm_design("Cascadia", rel, (23, 16, 22), paving=GRASS)
    x1, z1, x2, z2 = 3, 6, 11, 12
    cs_logs(d, x1, z1, x2, z2, 4)
    ridge = d.gable(x1, z1, x2, z2, 5, "x", "dark_oak_stairs", "dark_oak_slab", "spruce_planks")
    # porch
    d.fill(x1, 1, 3, x2, 1, z1 - 1, "spruce_planks")
    for x in range(x1 - 1, x2 + 2):
        for z in range(2, z1):
            d.set(x, 5, z, slab("dark_oak_slab") if z > 2 else st("dark_oak_stairs", "south"))
    for x in (x1, x2):
        for y in (2, 3, 4):
            d.set(x, y, 3, "spruce_log[axis=y]")
    for x in range(x1 + 1, x2):
        if x not in (6, 7):
            d.set(x, 2, 3, "spruce_fence")
    path(d, 6, 0, 7, 2, "dirt_path")
    d.door(7, 2, z1, "south", "spruce")
    d.window(5, 3, z1, 5, 3, z1)
    d.window(9, 3, z1, 9, 3, z1)
    d.chair(x1 + 1, 2, 4, "south", "spruce", sit=False)
    d.keg(x2 - 1, 2, 4, "north")
    d.set(x2 - 1, 3, 4, "honey_block")
    # stone chimney + wax stove on the west wall
    d.hearth(x1 + 1, 2, 9, "east", ridge + 2, "cobblestone", "campfire")
    for y in range(2, ridge + 2):
        d.set(x1, y, 9, "mossy_cobblestone" if y % 3 == 0 else "cobblestone")
    d.hut(x1 + 1, 2, z1 + 1)
    d.item(x2 - 1, 2, z1 + 1, "crafting_table")
    nr = need_racks(d)
    racks(d, [(x2 - 1, z) for z in range(z1 + 2, z1 + 2 + nr)], 2, "west")
    for x in range(6, 9):
        d.set(x, 2, z2 - 1, slab("spruce_slab", "top"))
    d.set(6, 3, z2 - 1, "honey_block")
    d.set(7, 3, z2 - 1, "candle[candles=4,lit=false,waterlogged=false]")
    d.set(8, 3, z2 - 1, "honeycomb_block")
    d.lamp(7, 4, 9)
    d.door(9, 2, z2, "north", "spruce")
    # meadow behind: rail fence, stumps with hives
    mz1, mz2 = z2, 20
    for x in range(1, 22):
        for z in range(mz1, mz2 + 1):
            if x in (1, 21) or z == mz2 or (z == mz1 and not (x1 <= x <= x2)):
                d.set(x, 2, z, "spruce_fence")
    d.set(15, 2, mz1, gate("spruce", "north"))
    flowers(d, 2, mz1 + 1, 20, mz2 - 1, ("dandelion", "poppy", "cornflower", "oxeye_daisy", "short_grass",
                                         "fern"), step=2)
    hives = d.req["yard"]["minecraft:beehive"]
    spots = [(6, 16), (11, 17), (16, 16), (8, 19), (14, 19)]
    for i, (x, z) in enumerate(spots):
        if i < hives:
            d.set(x, 2, z, "stripped_spruce_log[axis=y]")
            d.yard_item(x, 3, z, "beehive[facing=north,honey_level=3]")
        elif L >= 4 and i < hives + 1:
            d.set(x, 2, z, "stripped_spruce_log[axis=y]")
            d.set(x, 3, z, "bee_nest[facing=north,honey_level=0]")
    for x in range(13, 21, 2):
        d.set(x, 2, mz1 + 1, "sunflower[half=lower]")
        d.set(x, 3, mz1 + 1, "sunflower[half=upper]")
    if L >= 2:
        d.sign(7, 4, 2, "north", ["Wildflower", "Honey"], "spruce")
    if L >= 4:
        d.set(19, 2, 3, "spruce_fence")
        d.set(19, 3, 3, "lantern[hanging=false,waterlogged=false]")
        d.keg(18, 2, 4, "up")
        d.keg(18, 3, 4, "north")
    if L >= 5:
        for x in range(13, 21):
            d.set(x, 2, 8, "allium")
    return d


def bee_nt(rel, L):
    """Urban apiary: a glass honey lab (white concrete frame, honey-amber accent band) beside a pollinator
    meadow where the hives stand on quartz plinths; the lab has a green roof with more hives at L5."""
    d = farm_design("Neoterra", rel, (19, 14, 19), paving="smooth_stone")
    x1, z1, x2, z2 = 2, 2, 9, 9
    nt_walls(d, x1, z1, x2, z2, 5, sides="nwe", col_step=3)
    for x in range(x1, x2 + 1):
        d.set(x, 5, z1, "orange_terracotta")
    nt_roof(d, x1, z1, x2, z2, 6, solar_rows=False, green=True)
    path(d, 5, 0, 6, z1 - 1, "polished_andesite")
    d.double_door(5, 2, z1, "x", "south", "birch")
    d.door(x2, 2, 6, "east", "birch")
    d.hut(x1 + 1, 2, z1 + 1)
    d.item(x1 + 1, 2, z1 + 2, "crafting_table")
    nr = need_racks(d)
    racks(d, [(x1 + 1, z) for z in range(z2 - 1, z2 - 1 - nr, -1)], 2, "east")
    # extraction lab: steel bench with honey, glass jars
    for x in range(4, x2):
        d.set(x, 2, z2 - 1, "iron_block" if x == 4 else slab("smooth_quartz_slab", "top"))
    d.set(5, 3, z2 - 1, "honey_block")
    d.set(6, 3, z2 - 1, "glass")
    d.set(7, 3, z2 - 1, "honey_block")
    d.set(4, 3, z2 - 1, "hopper[enabled=true,facing=down]")
    d.set(x2 - 1, 2, z1 + 1, "honeycomb_block")
    d.set(x2 - 1, 3, z1 + 1, "potted_bamboo")
    for x in (4, 7):
        d.set(x, 5, 5, "sea_lantern")
    # meadow
    mx1, mz1, mx2, mz2 = 11, 2, 17, 17
    pen(d, mx1, mz1, mx2, mz2, "birch_fence", gates=[(14, mz1), (mx1, 6)])
    d.set(x2 + 1, 1, 6, "polished_andesite")
    flowers(d, mx1 + 1, mz1 + 1, mx2 - 1, mz2 - 1, ("cornflower", "allium", "oxeye_daisy", "azure_bluet",
                                                      "short_grass"), step=2)
    for z in range(mz1 + 1, mz2):
        d.set(14, 1, z, "polished_andesite")
        d.set(14, 2, z, AIR)
    hives = d.req["yard"]["minecraft:beehive"]
    for i, z in enumerate((8, 11, 14)):
        if i < hives:
            d.set(13, 2, z, "smooth_quartz")
            d.set(13, 1, z, "smooth_quartz")
            d.yard_item(13, 3, z, "beehive[facing=east,honey_level=3]")
    d.sign(4, 5, z1 - 1, "north", ["APIARY", "city honey"], "birch", glow=True, color="yellow")
    # second meadow strip behind the lab
    flowers(d, 2, 11, 9, 17, ("poppy", "dandelion", "cornflower", "short_grass"), step=2)
    for x in range(2, 10):
        d.set(x, 2, 11, "birch_fence")
    if L >= 3:
        for z in (8, 11, 14):
            d.set(15, 2, z, "light_gray_concrete")
            d.set(15, 3, z, "end_rod[facing=up]")
    if L >= 5:                                                          # rooftop hives on the green roof
        d.set(4, 7, 4, "beehive[facing=south,honey_level=2]")
        d.set(7, 7, 4, "beehive[facing=south,honey_level=2]")
        for y in range(2, 7):
            d.set(x2 - 1, y, z2 - 2, "ladder[facing=west,waterlogged=false]")
    return d


@design("beekeeper")
def beekeeper(pack, rel, L):
    return farmstead({"Hearthwood": bee_hw, "Cascadia": bee_cs, "Neoterra": bee_nt}[pack], pack, rel, L, "bees")


# ============================================================================================ STABLE
def stalls(d, n, a0, b_back, b_front, axis, lower, upper, wood, spots_left, manger="hay_block[axis=y]"):
    """Row of n horse stalls, 3 cells pitch (divider + 2 cells), laid along `axis` from a0; each stall runs
    from its back b_back to its front b_front (gate + fence there), a hay manger in the back corner and a
    'stall' work spot inside. Dividers are only drawn where the cell is free (walls are kept)."""
    P = (lambda a, b: (a, b)) if axis == "x" else (lambda a, b: (b, a))
    step = 1 if b_front > b_back else -1
    lo, hi = min(b_back, b_front), max(b_back, b_front)
    gface = ("south" if step > 0 else "north") if axis == "x" else ("east" if step > 0 else "west")
    placed = 0
    for i in range(n):
        a = a0 + 3 * i
        for div in (a, a + 3):
            for b in range(lo, hi + 1):
                x, z = P(div, b)
                if d.air(x, 2, z):
                    d.set(x, 2, z, lower)
                    d.set(x, 3, z, upper)
        x, z = P(a + 1, b_front)
        d.set(x, 2, z, gate(wood, gface))
        x, z = P(a + 2, b_front)
        d.set(x, 2, z, upper)
        x, z = P(a + 2, b_back)
        d.set(x, 2, z, manger)
        if placed < spots_left:
            x, z = P(a + 1, b_back + step)
            d.spot(x, 2, z, "stall")
            placed += 1
    return placed


def saddle_rack(d, x, z, wood, carpet="brown_carpet"):
    d.set(x, 2, z, f"{wood}_fence")
    d.set(x, 3, z, carpet)


def stable_hw(rel, L):
    """Coaching stable block: long brick-and-timber range with a steep tiled roof and a clock cupola on the
    ridge; tack room with saddle racks at the west end, loose boxes either side of a cobbled aisle, grooms'
    loft upstairs. It grows a pair of boxes per level; a fenced paddock lies behind."""
    d = farm_design("Hearthwood", rel, (27, 20, 27), paving=GRASS)
    nst = d.req["spots"]["stall"]
    ns = (nst + 1) // 2
    x1, z1, z2 = 3, 3, 14
    x2 = x1 + 6 + 3 * ns
    pen(d, x1, z2 + 2, x2, 25, "oak_fence", gates=[(x2, z2 + 4)], patches=("coarse_dirt", 9))
    hw_walls(d, x1, z1, x2, z2, 9, floor="cobblestone", infill="calcite", post_step=3, lower=4)
    d.fill(x1 + 1, 6, z1 + 1, x2 - 1, 6, z2 - 1, "spruce_planks")
    ridge = d.gable(x1, z1, x2, z2, 10, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite")
    # tack room (x4..8) with entrance from the lane
    path(d, 5, 0, 7, z1 - 1, "gravel")
    d.double_door(5, 2, z1, "x", "south", "dark_oak")
    for z in range(z1 + 1, z2):
        for y in range(2, 6):
            d.set(9, y, z, "bricks" if z not in (8, 9) or y > 3 else AIR)
    d.hut(x1 + 1, 2, z1 + 1)
    d.item(x1 + 1, 2, z1 + 2, "barrel")
    if d.req["items"].get("minecraft:water_cauldron"):
        d.item(x1 + 1, 2, z1 + 3, "water_cauldron[level=3]")
    for z in range(z1 + 5, z2 - 3):
        saddle_rack(d, 8, z, "dark_oak")
    d.set(x1 + 1, 2, z2 - 1, "chest[facing=east,type=single,waterlogged=false]")
    d.set(x1 + 2, 2, z2 - 1, "grindstone[face=floor,facing=north]")
    stairs_up(d, 7, z1 + 1, 2, 6, "south", "dark_oak_stairs", "dark_oak_planks")
    for z in range(z1 + 1, z1 + 5):
        d.set(6, 7, z, "dark_oak_fence")
    d.lamp(5, 5, 7)
    # windows: tack room front, box windows on both long walls (top half), loft windows
    d.window(x1, 3, 7, x1, 4, 8)
    for i in range(ns):
        xw = 11 + 3 * i
        d.window(xw, 4, z1, xw, 4, z1)
        d.window(xw, 4, z2, xw, 4, z2)
        d.window(xw, 8, z1, xw, 8, z1)
        d.window(xw, 8, z2, xw, 8, z2)
    # boxes along the aisle (z8..9)
    left = nst
    left -= stalls(d, ns, 9, z1 + 1, z1 + 4, "x", "dark_oak_planks", "dark_oak_fence", "dark_oak", left)
    stalls(d, ns, 9, z2 - 1, z2 - 4, "x", "dark_oak_planks", "dark_oak_fence", "dark_oak", left)
    for x in range(10, x2):
        for z in (8, 9):
            d.set(x, 1, z, "cobblestone" if (x + z) % 2 else "stone_bricks")
    for x in range(11, x2, 3):
        d.lamp(x, 5, 8)
    d.door(x2, 2, 8, "east", "dark_oak")
    path(d, x2 + 1, 8, x2 + 1, z2 + 3, "gravel")
    # grooms' loft: beds along both walls under the eaves
    beds = d.req["beds"]
    bx = list(range(x1 + 6, x2 - 1, 2))
    k = 0
    for x in bx:
        for zz, f in ((z1 + 1, "north"), (z2 - 1, "south")):
            if k < beds:
                d.bed(x, 7, zz, f)
                k += 1
    for x in range(x1 + 7, x2 - 1, 4):
        d.lamp(x, 9, 8)
    d.set(x1 + 1, 7, z1 + 1, "chest[facing=east,type=single,waterlogged=false]")
    # clock cupola on the ridge
    cx = (x1 + x2) // 2
    cz = (z1 + z2) // 2
    for dx in (-1, 0, 1):
        for dz in (0, 1):
            for y in (ridge, ridge + 1, ridge + 2):
                corner = dx != 0
                d.set(cx + dx, y, cz + dz, "dark_oak_planks" if y == ridge else
                      "dark_oak_fence" if corner and y < ridge + 2 else "calcite" if y < ridge + 2 else
                      "dark_oak_planks")
    d.set(cx, ridge + 1, cz, "bell[attachment=ceiling,facing=north,powered=false]")
    d.set(cx, ridge + 1, cz + 1, AIR)
    for dx in (-1, 0, 1):
        d.set(cx + dx, ridge + 3, cz, st("deepslate_tile_stairs", "south"))
        d.set(cx + dx, ridge + 3, cz + 1, st("deepslate_tile_stairs", "north"))
    d.set(cx, ridge + 4, cz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    d.sign(cx, ridge + 2, cz - 1, "north", ["XII", "IX  +  III", "VI"], "dark_oak")
    d.sign(6, 5, z1 - 1, "north", ["Mews", "& Livery"], "dark_oak")
    # paddock: water trough tub, hay, jump
    hay(d, x1 + 2, 2, 24)
    d.set(x1 + 3, 2, 24, "hay_block[axis=x]")
    if L >= 3:
        for x in (12, 14):
            d.set(x, 2, 20, "oak_fence")
        d.set(12, 3, 20, "oak_fence")
        d.set(14, 3, 20, "oak_fence")
        d.set(13, 3, 20, "oak_fence")
    if L >= 4:
        for x in (1, 2, x1 + 6, x1 + 7, x1 + 8):
            d.set(x, 2, 1, "potted_red_tulip")
    if L >= 5:
        d.set(x2 + 1, 2, 1, "dark_oak_fence")
        d.set(x2 + 1, 3, 1, "lantern[hanging=false,waterlogged=false]")
        d.set(x1 + 9, 2, 1, "dark_oak_fence")
        d.set(x1 + 9, 3, 1, "lantern[hanging=false,waterlogged=false]")
    return d


def stable_cs(rel, L):
    """Ranch horse barn: long log barn with its gable to the road, big double doors and a hay door with a
    hood, centre aisle with stalls both sides, tack and feed rooms at the front, wranglers' bunk loft under
    the roof, and a round rail-fenced corral behind. Grows a pair of stalls per level."""
    d = farm_design("Cascadia", rel, (25, 20, 33), paving=GRASS)
    nst = d.req["spots"]["stall"]
    ns = (nst + 1) // 2
    x1, x2, z1 = 4, 16, 3
    z2 = 8 + 3 * ns
    cs_logs(d, x1, z1, x2, z2, 5)
    d.fill(x1 + 1, 6, z1 + 1, x2 - 1, 6, z2 - 1, "spruce_planks")
    ridge = d.gable(x1, z1, x2, z2, 7, "z", "dark_oak_stairs", "dark_oak_slab", "spruce_planks")
    # front: doors, hay door + hood
    path(d, 9, 0, 11, z1 - 1, "dirt_path")
    d.double_door(9, 2, z1, "x", "south", "spruce")
    d.set(11, 2, z1, "spruce_log[axis=y]")
    d.set(11, 3, z1, "spruce_log[axis=y]")
    d.window(6, 3, z1, 6, 4, z1)
    d.window(14, 3, z1, 14, 4, z1)
    d.set(10, 8, z1, "spruce_door[facing=south,half=lower,hinge=left,open=false,powered=false]")
    d.set(10, 9, z1, "spruce_door[facing=south,half=upper,hinge=left,open=false,powered=false]")
    for x in (9, 10, 11):
        d.set(x, 10, z1 - 1, st("dark_oak_stairs", "south", "top"))
    d.set(10, 11, z1 - 1, "dark_oak_planks")
    d.sign(10, 7, z1 - 1, "north", ["Lone Pine", "Horse Barn"], "spruce")
    # tack room (west) and feed room (east) at the front, aisle x9..11
    for z in range(z1 + 1, 8):
        for y in range(2, 6):
            d.set(8, y, z, f"stripped_spruce_log[axis=y]" if z == 7 else "spruce_planks")
            d.set(12, y, z, f"stripped_spruce_log[axis=y]" if z == 7 else "spruce_planks")
    d.door(8, 2, 5, "east", "spruce")
    d.door(12, 2, 5, "west", "spruce")
    d.hut(x1 + 1, 2, z1 + 1)
    d.item(x1 + 1, 2, z1 + 3, "barrel")
    for x in (x1 + 1, x1 + 2):
        saddle_rack(d, x, 7, "spruce")
    d.set(x1 + 1, 2, z1 + 2, "spruce_fence")
    d.set(x1 + 1, 3, z1 + 2, "lantern[hanging=false,waterlogged=false]")
    if d.req["items"].get("minecraft:water_cauldron"):
        d.item(13, 2, z1 + 1, "water_cauldron[level=3]")
    for z in range(z1 + 1, 8):
        hay(d, 15, 2, z, "z")
        if z % 2:
            hay(d, 15, 3, z, "z")
    d.keg(14, 2, z1 + 3, "up")
    d.keg(14, 2, z1 + 4, "up")
    # stalls from z=8
    left = nst
    left -= stalls(d, ns, 8, x1 + 1, 8, "z", "spruce_planks", "spruce_fence", "spruce", left)
    stalls(d, ns, 8, x2 - 1, 12, "z", "spruce_planks", "spruce_fence", "spruce", left)
    for z in range(9, z2, 3):
        d.window(x1, 3, z, x1, 3, z)
        d.window(x2, 3, z, x2, 3, z)
        d.lamp(10, 5, z)
    # loft: ladder, bunks under the roof
    for y in range(2, 7):
        d.set(10, y, z2 - 1, "ladder[facing=north,waterlogged=false]")
    beds = d.req["beds"]
    k = 0
    for z in range(z1 + 2, z2 - 2, 2):
        for x, f in ((7, "west"), (13, "east")):
            if k < beds:
                d.bed(x, 7, z, f, "brown")
                k += 1
    for z in range(z1 + 3, z2 - 2, 4):
        d.set(10, 7, z, "barrel[facing=up,open=false]")
        d.set(10, 8, z, "lantern[hanging=false,waterlogged=false]")
    d.window(10, 8, z2, 10, 9, z2)
    # corral behind
    cz1 = z2 + 2
    cz2 = 31
    cx, ccz = 10, (cz1 + cz2) // 2
    pen(d, 2, cz1, 22, cz2, "spruce_fence", ground="coarse_dirt", patches=(GRASS, 5))
    for x, z in ((3, cz1 + 1), (21, cz1 + 1), (3, cz2 - 1), (21, cz2 - 1)):     # rounded corners
        d.set(x, 2, z, "spruce_fence")
    d.set(cx, 2, cz1, gate("spruce", "north"))
    d.set(9, 2, z2, "spruce_door[facing=south,half=lower,hinge=left,open=false,powered=false]")
    d.set(9, 3, z2, "spruce_door[facing=south,half=upper,hinge=left,open=false,powered=false]")
    path(d, 9, z2 + 1, 10, cz1 - 1, "dirt_path")
    hay(d, cx + 4, 2, ccz)
    if L >= 4:                                                          # hitching rail and water trough out front
        for x in range(1, 4):
            d.set(x, 2, 2, "spruce_fence")
        d.set(18, 2, 1, "spruce_fence")
        d.set(18, 3, 1, "lantern[hanging=false,waterlogged=false]")
    if L >= 5:
        d.set(19, 2, 3, "spruce_fence")
        d.set(20, 2, 3, "spruce_fence")
        d.set(21, 2, 3, "spruce_fence")
        d.set(x2 + 2, 2, 6, "spruce_log[axis=x]")
        d.set(x2 + 3, 2, 6, "spruce_log[axis=x]")
    return d


def stable_nt(rel, L):
    """Equestrian centre: two-storey glass grooms' house (tack lounge below, capsule bedrooms above) joined
    to a low white stable wing with a raised clerestory aisle and solar roof, stalls with steel-bar fronts,
    and a show-jumping arena with birch rails. The stable wing grows a pair of stalls per level."""
    d = farm_design("Neoterra", rel, (31, 16, 25), paving="smooth_stone")
    nst = d.req["spots"]["stall"]
    ns = (nst + 1) // 2
    # grooms' house
    x1, z1, x2, z2 = 2, 2, 11, 9
    nt_walls(d, x1, z1, x2, z2, 5, sides="nw", col_step=3)
    d.fill(x1, 6, z1, x2, 6, z2, "light_gray_concrete")
    d.box(x1, 7, z1, x2, 10, z2, "white_concrete")
    for x in range(x1 + 1, x2):
        d.window(x, 8, z1, x, 9, z1, "light_gray_stained_glass_pane")
    for z in range(z1 + 1, z2):
        d.window(x1, 8, z, x1, 9, z, "light_gray_stained_glass_pane")
    nt_roof(d, x1, z1, x2, z2, 11, solar_rows=True)
    d.fill(x1, 6, z1 - 1, x2, 6, z1 - 1, "cyan_terracotta")
    d.double_door(5, 2, z1, "x", "south", "birch")
    d.hut(x1 + 1, 2, z1 + 1)
    d.item(x1 + 1, 2, z1 + 2, "barrel")
    if d.req["items"].get("minecraft:water_cauldron"):
        d.item(x1 + 1, 2, z2 - 1, "water_cauldron[level=3]")
    for x in range(x1 + 2, 8):
        saddle_rack(d, x, z2 - 1, "birch", "cyan_carpet")
    d.chair(x1 + 1, 2, z1 + 4, "west", "birch", sit=False)
    d.chair(x1 + 1, 2, z1 + 5, "west", "birch", sit=False)
    d.set(x1 + 2, 2, z1 + 4, slab("smooth_quartz_slab", "top"))
    stairs_up(d, x2 - 1, z1 + 1, 2, 6, "south", "smooth_quartz_stairs", "white_concrete")
    for x in (4, 7):
        d.set(x, 5, 5, "sea_lantern")
    # capsule bedrooms upstairs
    beds = d.req["beds"]
    k = 0
    for x in (3, 5, 7, 9):
        if k < beds:
            d.bed(x, 7, z1 + 1, "north", "cyan")
            k += 1
    for x in (3, 5, 7):
        if k < beds:
            d.bed(x, 7, z2 - 1, "south", "cyan")
            k += 1
    if k < beds:
        d.bed(x2 - 2, 7, z2 - 1, "south", "cyan")
        k += 1
    d.set(x2 - 1, 7, z1 + 1, "birch_fence")
    for x in (4, 8):
        d.set(x, 10, 5, "sea_lantern")
    # stable wing east of the house
    sx1, sx2 = x2, x2 + 1 + 3 * ns
    sz1, sz2 = 2, 12
    nt_walls(d, sx1, sz1, sx2, sz2, 4, sides="", col_step=3)
    d.flat(sx1, sz1, sx2, sz2, 5, "smooth_quartz", None, None)
    for x in range(sx1, sx2 + 1):                                     # raised clerestory over the aisle
        for z in (sz1 + 4, sz1 + 7):
            d.set(x, 5, z, "white_concrete")
            d.set(x, 6, z, "glass" if sx1 < x < sx2 else "white_concrete")
            d.set(x, 7, z, "white_concrete")
        for z in (sz1 + 5, sz1 + 6):
            d.set(x, 5, z, AIR)
            d.set(x, 8, z, "smooth_quartz")
            if x in (sx1, sx2):
                d.set(x, 5, z, "white_concrete")
                d.set(x, 6, z, "glass")
                d.set(x, 7, z, "white_concrete")
        d.set(x, 8, sz1 + 4, slab("smooth_quartz_slab"))
        d.set(x, 8, sz1 + 7, slab("smooth_quartz_slab"))
    solar(d, sx1 + 1, sz1 + 1, sx2 - 1, sz1 + 2, 6, step=1)
    solar(d, sx1 + 1, sz2 - 2, sx2 - 1, sz2 - 1, 6, step=1)
    for x in range(sx1 + 2, sx2, 3):                                  # stall windows (top band)
        d.window(x, 4, sz1, x, 4, sz1)
        d.window(x, 4, sz2, x, 4, sz2)
    d.set(sx1, 2, 7, AIR)
    d.set(sx1, 3, 7, AIR)
    d.door(sx1, 2, 7, "east", "birch")
    left = nst
    left -= stalls(d, ns, sx1, sz1 + 1, sz1 + 4, "x", "smooth_quartz", "iron_bars", "birch", left)
    stalls(d, ns, sx1, sz2 - 1, sz2 - 4, "x", "smooth_quartz", "iron_bars", "birch", left)
    for x in range(sx1 + 1, sx2):
        d.set(x, 1, 7, "polished_andesite")
        d.set(x, 1, 8, "polished_andesite")
    for x in range(sx1 + 2, sx2, 3):
        d.set(x, 8, 8, "sea_lantern")
    d.door(sx2, 2, 8, "east", "birch")
    d.sign(sx1 + 3, 4, sz1 - 1, "north", ["EQUESTRIAN", "CENTRE"], "birch", glow=True, color="cyan")
    # arena
    ax2 = 18 if L < 3 else 28
    pen(d, 2, 15, ax2, 23, "birch_fence", gates=[(8, 15)], ground="coarse_dirt")
    for x in range(2, ax2 + 1):
        for z in (15, 23):
            d.set(x, 1, z, "polished_andesite")
    path(d, 8, z2 + 1, 8, 14, "polished_andesite")
    for jx in range(5, ax2 - 1, 6):                                   # show jumps
        d.set(jx, 2, 19, "white_concrete")
        d.set(jx + 2, 2, 19, "white_concrete")
        d.set(jx + 1, 2, 19, "birch_fence")
        d.set(jx, 3, 19, "cyan_concrete")
        d.set(jx + 2, 3, 19, "cyan_concrete")
        d.set(jx + 1, 3, 19, "birch_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]")
    if L >= 4:
        for x in range(x1, x2 + 1, 2):
            d.set(x, 1, 0, "moss_block")
            d.set(x, 2, 0, "azalea")
    return d


@design("stable")
def stable(pack, rel, L):
    return farmstead({"Hearthwood": stable_hw, "Cascadia": stable_cs, "Neoterra": stable_nt}[pack], pack, rel, L, "horse")


# ============================================================================================ FARMSTEAD GROWTH
# Every type keeps its core (the hut building with its pens, drawn above) in the north-west of the plot. The
# farmstead grows around it level by level with real farm buildings, in the pack's style:
#   L2  a cart / wood / equipment shed       (east strip, by the lane)
#   L3  the herder's cottage                 (east strip)
#   L4  a second livestock hall for the type (south strip: poultry house, calf house, lambing shed, farrowing
#       house, hutch house, honey & candle house, indoor riding school)
#   L5  hay barn / threshing barn with granary or silos (south-east)
# plus a window-dressing pass (sills, shutters) and lamps along the paths.
EAST, SOUTH = 28, 15
LEAVES = "[distance=1,persistent=true,waterlogged=false]"


def farm_design(pack, rel, size, **kw):
    sx, sy, sz = size
    d = Design(pack, rel, (sx + EAST, max(sy, 24), sz + SOUTH), **kw)
    d.ex, d.ez = sx, sz
    return d


def hang(d, x, ytop, z, ybot, kind="lantern"):
    """Lantern on a chain hanging from ytop down to ybot."""
    for y in range(ybot + 1, ytop + 1):
        d.set(x, y, z, "chain[axis=y,waterlogged=false]")
    d.set(x, ybot, z, f"{kind}[hanging=true,waterlogged=false]")


def lamp_post(d, x, z, pack):
    if pack == "Neoterra":
        d.set(x, 2, z, "light_gray_concrete")
        d.set(x, 3, z, "end_rod[facing=up]")
        d.set(x, 4, z, "end_rod[facing=up]")
        d.set(x, 5, z, "sea_lantern")
    else:
        w = "dark_oak" if pack == "Hearthwood" else "spruce"
        d.set(x, 2, z, f"{w}_fence")
        d.set(x, 3, z, f"{w}_fence")
        d.set(x, 4, z, "lantern[hanging=false,waterlogged=false]")


def tree(d, x, z, log="oak_log", leaves="oak_leaves", h=4, r=2):
    for y in range(2, 2 + h):
        d.set(x, y, z, f"{log}[axis=y]")
    top = 1 + h
    for y, rr in ((top - 1, r), (top, r), (top + 1, 1)):
        for dx in range(-rr, rr + 1):
            for dz in range(-rr, rr + 1):
                if abs(dx) == rr and abs(dz) == rr and rr > 1:
                    continue
                if (dx or dz or y > top - 1) and d.bp.inside(x + dx, y, z + dz) and d.air(x + dx, y, z + dz):
                    d.set(x + dx, y, z + dz, leaves + LEAVES)
    d.set(x, top + 1, z, leaves + LEAVES)


def bed_of(d, x1, z1, x2, z2, kinds, ground=GRASS, edge=None):
    """Flower bed with an optional edging (slabs/trapdoors) at y=2 around it."""
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            d.set(x, 1, z, ground)
            d.set(x, 2, z, kinds[(x * 5 + z * 3) % len(kinds)])


def bench(d, x, z, back, wood, n=2, along="x"):
    for i in range(n):
        cx, cz = (x + i, z) if along == "x" else (x, z + i)
        d.set(cx, 2, cz, st(f"{wood}_stairs", back))


def shelf(d, x, y, z, wood, item):
    d.set(x, y, z, slab(f"{wood}_slab", "top"))
    d.set(x, y + 1, z, item)


POTS = ("potted_red_tulip", "decorated_pot[cracked=false,facing=north,waterlogged=false]",
        "candle[candles=3,lit=false,waterlogged=false]", "potted_fern", "potted_azure_bluet")


# ------------------------------------------------------------------------------------------- L2: shed
def shed(d, pack, x1, z1, w=7):
    """w x 5 shed, open to the north lane."""
    x2, z2 = x1 + w - 1, z1 + 4
    if pack == "Hearthwood":                                           # cart shed
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                d.set(x, 1, z, "cobblestone")
                if (x in (x1, x2) and z > z1) or z == z2:
                    for y in (2, 3, 4):
                        d.set(x, y, z, "bricks" if y < 4 else "stripped_dark_oak_log[axis=y]")
        for x in list(range(x1, x2, 3)) + [x2]:
            for y in (2, 3, 4):
                d.set(x, y, z1, "dark_oak_log[axis=y]")
        for x in range(x1, x2 + 1):
            d.set(x, 4, z1, "stripped_dark_oak_log[axis=x]")
        d.gable(x1, z1, x2, z2, 5, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "bricks")
        # hay cart
        for z in (z1 + 1, z1 + 2, z1 + 3):
            d.set(x1 + 1, 2, z, slab("dark_oak_slab", "top"))
            d.set(x1 + 2, 2, z, slab("dark_oak_slab", "top"))
        hay(d, x1 + 1, 3, z1 + 2, "z")
        hay(d, x1 + 2, 3, z1 + 2, "z")
        d.set(x1 + 1, 3, z1 + 1, "hay_block[axis=x]")
        d.set(x1 + 2, 2, z1 + 0, "dark_oak_fence")
        # tool bay
        d.set(x1 + 4, 2, z2 - 1, "grindstone[face=floor,facing=north]")
        d.set(x1 + 5, 2, z2 - 1, "barrel[facing=up,open=false]")
        d.set(x1 + 5, 3, z2 - 1, "white_wool")
        d.set(x1 + 5, 2, z2 - 2, "brown_wool")
        d.set(x1 + 5, 2, z2 - 3, "composter[level=4]")
        for x in (x1 + 4, x1 + 5):
            d.set(x, 4, z2 - 1, "tripwire_hook[attached=false,facing=north,powered=false]")
        for x in range(x1 + 7, x2):                                   # extra bays: sacks, kegs, a plough
            for y in (2, 3):
                d.set(x, y, z2 - 1, ("white_wool", "brown_wool", "barrel[facing=up,open=false]")[(x + y) % 3])
            d.set(x, 2, z2 - 2, "hay_block[axis=x]" if x % 2 else "barrel[facing=north,open=false]")
        if w >= 10:
            d.set(x2 - 2, 2, z1 + 1, "anvil[facing=east]")
            d.set(x2 - 1, 2, z1 + 1, "dark_oak_fence")
            d.set(x2 - 1, 3, z1 + 1, slab("dark_oak_slab"))
        for x in range(x1 + 3, x2, 4):
            hang(d, x, 6, z1 + 2, 5)
        d.set(x1 - 1, 2, z1, "barrel[facing=up,open=false]")
        d.set(x1 - 1, 3, z1, "lantern[hanging=false,waterlogged=false]")
    elif pack == "Cascadia":                                           # woodshed with lean-to roof
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                d.set(x, 1, z, "coarse_dirt")
        for x in list(range(x1, x2, 3)) + [x2]:
            for z in (z1, z2):
                for y in (2, 3, 4):
                    d.set(x, y, z, "spruce_log[axis=y]")
        mono(d, x1, z1, x2, z2, 5, "dark_oak_stairs", "dark_oak_slab", "spruce_planks")
        for x in range(x1 + 1, x2):                                     # firewood stack along the back
            for y in (2, 3, 4):
                d.set(x, y, z2, "oak_log[axis=z]" if (x + y) % 2 else "stripped_spruce_log[axis=z]")
        for z in range(z1 + 1, z2):
            for y in (2, 3):
                d.set(x1, y, z, "birch_log[axis=x]" if (z + y) % 2 else "spruce_log[axis=x]")
        d.set(x1 + 2, 2, z1 + 2, "stripped_oak_log[axis=y]")         # chopping block
        d.set(x2 - 2, 2, z1 + 2, "spruce_fence")                      # sawhorse
        d.set(x2 - 1, 2, z1 + 2, "spruce_fence")
        d.set(x2 - 2, 3, z1 + 2, slab("spruce_slab"))
        d.set(x2 - 1, 3, z1 + 2, slab("spruce_slab"))
        d.set(x2 - 1, 2, z2 - 1, "cauldron")                          # wheelbarrow
        d.set(x2 - 1, 2, z2 - 2, trap("spruce", "north", "top"))
        d.set(x2 - 1, 2, z1 + 1, "grindstone[face=floor,facing=east]")
        for x in range(x1 + 3, x2, 4):
            hang(d, x, 5, z1 + 2, 4)
        d.keg(x1 - 1, 2, z1, "up")
        d.set(x1 - 1, 3, z1, "lantern[hanging=false,waterlogged=false]")
    else:                                                              # equipment pod + drone pad
        nt_walls(d, x1, z1, x2, z2, 4, sides="n", col_step=3, floor="polished_andesite")
        nt_roof(d, x1, z1, x2, z2, 5, solar_rows=True)
        d.double_door(x1 + 3, 2, z1, "x", "south", "birch")
        for z in range(z1 + 1, z2):
            d.set(x1 + 1, 2, z, "iron_block" if z == z1 + 1 else "white_concrete")
            d.set(x1 + 1, 3, z, "lightning_rod[facing=up,powered=false,waterlogged=false]" if z == z1 + 1 else
                  "iron_trapdoor[facing=east,half=bottom,open=false,powered=false,waterlogged=false]")
        for x in range(x1 + 2, x2):
            d.set(x, 2, z2 - 1, "barrel[facing=north,open=false]" if x % 2 else "light_gray_concrete")
            d.set(x, 3, z2 - 1, "potted_bamboo" if x % 2 else slab("smooth_quartz_slab"))
        d.set(x2 - 1, 2, z1 + 1, "smooth_quartz_stairs[facing=east,half=bottom,shape=straight,waterlogged=false]")
        d.set(x2 - 1, 4, z1 + 2, "sea_lantern")
        d.set(x1 + 3, 4, z1 + 2, "end_rod[facing=down]")
        px = x2 + 2
        if px + 2 < d.sx:
            for dx in range(3):
                for dz in range(3):
                    d.set(px + dx - 1, 1, z1 + 1 + dz, "cyan_concrete" if (dx == 1 or dz == 1) and
                          (dx, dz) != (1, 1) else "polished_andesite")
            d.set(px, 1, z1 + 2, "sea_lantern")


# ------------------------------------------------------------------------------------------- L3: cottage
def cottage(d, pack, x1, z1, w=9):
    """Herder's cottage, w x 8, front door to the north."""
    x2, z2 = x1 + w - 1, z1 + 7
    xm = x1 + 4
    if pack == "Hearthwood":
        hw_walls(d, x1, z1, x2, z2, 5, floor="oak_planks", infill="bricks", lower=4)
        hw_walls(d, x1, z1, x2, z2, 9, floor="spruce_planks", y0=7, lower=0, post_step=2)
        for x in range(x1, x2 + 1):                                    # jetty bressumer
            d.set(x, 6, z1, "dark_oak_planks")
            d.set(x, 6, z2, "dark_oak_planks")
        ridge = d.gable(x1, z1, x2, z2, 10, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite")
        d.door(xm, 2, z1, "south", "dark_oak")
        d.set(xm, 4, z1 - 1, st("deepslate_tile_stairs", "south", "top"))
        for x in (x1 + 2, x1 + 6):
            d.window(x, 3, z1, x, 4, z1)
            d.window(x, 3, z2, x, 4, z2)
            d.window(x - 1, 8, z1, x, 8, z1)
            d.window(x - 1, 8, z2, x, 8, z2)
        d.window(x1, 3, z1 + 3, x1, 4, z1 + 3)
        # kitchen on the west wall
        d.set(x1 + 1, 2, z1 + 1, "smoker[facing=east,lit=true]")
        d.set(x1 + 1, 2, z1 + 2, "water_cauldron[level=3]")
        d.set(x1 + 1, 2, z1 + 4, "barrel[facing=up,open=false]")
        d.set(x1 + 1, 2, z1 + 5, slab("dark_oak_slab", "top"))
        d.set(x1 + 1, 3, z1 + 5, "candle[candles=2,lit=false,waterlogged=false]")
        for z in (z1 + 1, z1 + 2, z1 + 4, z1 + 5):
            shelf(d, x1 + 1, 4, z, "dark_oak", POTS[z % len(POTS)])
        d.table(x1 + 3, 2, z1 + 3, "dark_oak")
        d.chair(x1 + 3, 2, z1 + 2, "north", "dark_oak", sit=False)
        d.chair(x1 + 3, 2, z1 + 4, "south", "dark_oak", sit=False)
        d.chair(x1 + 4, 2, z1 + 3, "east", "dark_oak", sit=False)
        # inglenook on the east wall, flue through the roof
        d.hearth(x2 - 1, 2, z1 + 3, "west", ridge + 2, "bricks", "campfire")
        d.set(x2 - 1, ridge + 2, z1 + 3, slab("brick_slab"))
        d.rug(x1 + 5, z1 + 2, x1 + 6, z1 + 4, 2, ("red_carpet", "orange_carpet"), "check")
        d.chair(x1 + 5, 2, z1 + 1, "north", "oak", sit=False)
        hang(d, x1 + 3, 5, z1 + 3, 4)
        stairs_up(d, x1 + 3, z2 - 1, 2, 6, "east", "dark_oak_stairs", "dark_oak_planks")
        for x in (x1 + 4, x1 + 5):
            d.set(x, 7, z2 - 2, "dark_oak_fence")
        # bedroom upstairs
        d.bed(x1 + 1, 7, z1 + 1, "north", "red")
        d.bed(x1 + 3, 7, z1 + 1, "north", "red")
        d.set(x1 + 2, 7, z1 + 1, "barrel[facing=up,open=false]")
        d.candle(x1 + 2, 8, z1 + 1, 1)
        d.set(x1 + 5, 7, z1 + 1, "chiseled_bookshelf[facing=south,slot_0_occupied=true,slot_1_occupied=true,"
                                 "slot_2_occupied=false,slot_3_occupied=true,slot_4_occupied=false,"
                                 "slot_5_occupied=true]")
        d.set(x1 + 6, 7, z1 + 1, "barrel[facing=south,open=false]")
        d.set(x1 + 6, 8, z1 + 1, "potted_red_tulip")
        d.set(x1 + 1, 7, z1 + 5, "lectern[facing=east,has_book=false,powered=false]")
        d.rug(x1 + 2, z1 + 3, x1 + 5, z1 + 4, 7, ("red_carpet", "white_carpet"), "border")
        hang(d, x1 + 3, 11, z1 + 3, 9)
        # garden front: path, beds, bench, lamp
        path(d, xm, z1 - 2, xm, z1 - 1, "gravel")
        bed_of(d, x1, z1 - 2, xm - 2, z1 - 1, ("poppy", "cornflower", "oxeye_daisy", "allium"))
        bed_of(d, xm + 2, z1 - 2, x2, z1 - 1, ("azure_bluet", "poppy", "lily_of_the_valley"))
        lamp_post(d, xm - 1, z1 - 2, pack)
        bench(d, x2 + 1, z1 + 2, "east", "dark_oak", 2, "z")
    elif pack == "Cascadia":
        cs_logs(d, x1, z1, x2, z2, 4, log="spruce_log")
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                if x in (x1, x2) or z in (z1, z2):
                    for y in (2, 3, 4):
                        if "spruce_log" in d.get(x, y, z) and not (x in (x1, x2) and z in (z1, z2)):
                            d.set(x, y, z, d.get(x, y, z).replace("spruce_log", "stripped_spruce_log"))
        ridge = d.gable(x1, z1, x2, z2, 5, "x", "dark_oak_stairs", "dark_oak_slab", "spruce_planks")
        d.door(xm, 2, z1, "south", "spruce")
        for x in (x1 + 2, x1 + 6):
            d.window(x, 3, z1, x, 3, z1)
            d.window(x, 3, z2, x, 3, z2)
        d.window(xm, 6, z1, xm, 7, z1)
        d.window(xm, 6, z2, xm, 7, z2)
        # porch
        for x in range(x1 - 1, x2 + 2):
            for z in range(z1 - 3, z1):
                d.set(x, 1, z, "spruce_planks")
            d.set(x, 5, z1 - 3, st("dark_oak_stairs", "south"))
            d.set(x, 5, z1 - 2, slab("dark_oak_slab", "top"))
        for x in (x1 - 1, x1 + 3, x1 + 5, x2 + 1):
            for y in (2, 3, 4):
                d.set(x, y, z1 - 3, "spruce_log[axis=y]")
        for x in range(x1, x2 + 1):
            if d.air(x, 2, z1 - 3) and x != xm:
                d.set(x, 2, z1 - 3, "spruce_fence")
        d.chair(x1 + 1, 2, z1 - 2, "north", "spruce", sit=False)
        d.chair(x1 + 2, 2, z1 - 2, "north", "spruce", sit=False)
        d.keg(x2 - 1, 2, z1 - 2, "up")
        d.set(x2 - 1, 3, z1 - 2, "lantern[hanging=false,waterlogged=false]")
        d.set(x2, 2, z1 - 2, "barrel[facing=north,open=false]")
        # stone fireplace & chimney on the west gable
        d.hearth(x1 + 1, 2, z1 + 3, "east", ridge + 2, "cobblestone", "campfire")
        for y in range(1, ridge + 2):
            d.set(x1 - 1, y, z1 + 3, "mossy_cobblestone" if y % 3 == 0 else "cobblestone")
            if y < 5:
                d.set(x1 - 1, y, z1 + 2, "cobblestone")
                d.set(x1 - 1, y, z1 + 4, "cobblestone")
        d.set(x1 + 1, ridge + 2, z1 + 3, slab("cobblestone_slab"))
        d.rug(x1 + 2, z1 + 2, x1 + 3, z1 + 4, 2, ("brown_carpet", "green_carpet"), "check")
        d.chair(x1 + 3, 2, z1 + 5, "south", "spruce", sit=False)
        # kitchen corner, table, bunks
        d.set(x1 + 1, 2, z2 - 1, "furnace[facing=north,lit=true]")
        d.set(x1 + 2, 2, z2 - 1, "water_cauldron[level=3]")
        d.set(x1 + 3, 2, z2 - 1, "barrel[facing=up,open=false]")
        for x in (x1 + 1, x1 + 2, x1 + 3):
            shelf(d, x, 4, z2 - 1, "spruce", POTS[x % len(POTS)])
        d.table(x1 + 5, 2, z1 + 3, "spruce")
        d.chair(x1 + 5, 2, z1 + 2, "north", "spruce", sit=False)
        d.chair(x1 + 5, 2, z1 + 4, "south", "spruce", sit=False)
        d.bed(x2 - 1, 2, z1 + 1, "east", "brown")
        d.bed(x2 - 1, 2, z2 - 1, "east", "brown")
        d.set(x2 - 1, 2, z1 + 3, "barrel[facing=up,open=false]")
        d.set(x2 - 1, 3, z1 + 3, "candle[candles=2,lit=false,waterlogged=false]")
        d.banner(x2 - 1, 4, z1 + 4, "west", "brown")
        hang(d, xm, ridge - 1, z1 + 3, 5)
        if x2 + 3 < d.sx:
            lamp_post(d, x2 + 2, z1 - 3, pack)
            tree(d, x2 + 2, z2 + 1, "spruce_log", "spruce_leaves", 6, 1)
    else:
        nt_walls(d, x1, z1, x2, z2, 5, sides="nse", col_step=4)
        d.fill(x1, 6, z1 - 1, x2, 6, z2, "light_gray_concrete")
        d.box(x1, 7, z1 - 1, x2, 9, z2, "white_concrete")
        for x in range(x1 + 1, x2):
            d.window(x, 7, z1 - 1, x, 8, z1 - 1, "light_gray_stained_glass_pane")
        for z in range(z1, z2):
            d.window(x2, 7, z, x2, 8, z, "light_gray_stained_glass_pane")
        nt_roof(d, x1, z1 - 1, x2, z2, 10, solar_rows=False, green=True)
        d.fill(x1, 6, z1 - 1, x2, 6, z1 - 1, "cyan_terracotta")
        d.double_door(xm, 2, z1, "x", "south", "birch")
        # open-plan living: kitchen wall, island, lounge
        for z in range(z1 + 1, z2):
            d.set(x1 + 1, 2, z, "smoker[facing=east,lit=false]" if z == z1 + 2 else
                  "water_cauldron[level=3]" if z == z1 + 3 else "white_concrete")
            d.set(x1 + 1, 4, z, "light_gray_stained_glass")
        for z in (z1 + 1, z1 + 4, z1 + 5):
            d.set(x1 + 1, 3, z, "potted_bamboo" if z % 2 else "candle[candles=3,lit=false,waterlogged=false]")
        for z in (z1 + 2, z1 + 4):
            d.set(x1 + 3, 2, z, "smooth_quartz")
        d.set(x1 + 3, 2, z1 + 3, "smooth_quartz")
        d.set(x1 + 3, 3, z1 + 3, "potted_azure_bluet")
        for z in (z1 + 2, z1 + 3, z1 + 4):
            d.chair(x1 + 4, 2, z, "east", "birch", sit=False)
        d.chair(x2 - 1, 2, z1 + 2, "east", "mangrove", sit=False)
        d.chair(x2 - 1, 2, z1 + 3, "east", "mangrove", sit=False)
        d.set(x2 - 2, 2, z1 + 3, slab("smooth_quartz_slab"))
        d.rug(x2 - 3, z1 + 1, x2 - 2, z1 + 4, 2, ("cyan_carpet", "light_gray_carpet"), "check")
        d.set(x2 - 1, 2, z1 + 1, "potted_bamboo")
        for x in (x1 + 3, x1 + 6):
            d.set(x, 6, z1 + 3, "sea_lantern")
        stairs_up(d, x1 + 3, z2 - 1, 2, 6, "east", "smooth_quartz_stairs", "white_concrete")
        d.set(x1 + 4, 7, z2 - 2, "glass_pane")
        d.set(x1 + 5, 7, z2 - 2, "glass_pane")
        # bedroom
        d.bed(x1 + 2, 7, z1, "north", "cyan")
        d.bed(x1 + 4, 7, z1, "north", "cyan")
        d.set(x1 + 3, 7, z1, "white_concrete")
        d.set(x1 + 3, 8, z1, "potted_bamboo")
        d.set(x1 + 1, 7, z1 + 3, "white_concrete")
        d.set(x1 + 1, 8, z1 + 3, "candle[candles=2,lit=false,waterlogged=false]")
        d.chair(x1 + 2, 7, z1 + 3, "east", "birch", sit=False)
        d.set(x2 - 1, 7, z1 + 1, "barrel[facing=up,open=false]")
        d.set(x2 - 1, 7, z1 + 2, "barrel[facing=up,open=false]")
        d.rug(x1 + 3, z1 + 2, x1 + 6, z1 + 4, 7, ("light_gray_carpet",), "plain")
        for x in (x1 + 3, x1 + 6):
            d.set(x, 9, z1 + 3, "sea_lantern")
        for x in range(x1, x2 + 1, 2):
            d.set(x, 1, z1 - 2, "moss_block")
            d.set(x, 2, z1 - 2, "azalea" if x != xm else AIR)
        path(d, xm, z1 - 2, xm + 1, z1 - 1, "polished_andesite")
        d.set(xm, 2, z1 - 2, AIR)


# ------------------------------------------------------------------------------------------- L4: livestock hall
def hall(d, pack, kind, x1, z1, size):
    """Second livestock building, w x 9, door to the north; interior per kind. With `loft` the gabled halls get
    a hay loft, the Neoterra hall an upper office/store floor and the riding school taller walls and a gallery."""
    w, loft, dep = size
    x2, z2 = x1 + w - 1, z1 + dep - 1
    xm = (x1 + x2) // 2
    zc = z1 + dep // 2
    wood = {"Hearthwood": "dark_oak", "Cascadia": "spruce", "Neoterra": "birch"}[pack]
    top = 7 if (loft and kind == "horse") else 5
    if pack == "Hearthwood":
        hw_walls(d, x1, z1, x2, z2, top, floor="spruce_planks" if kind in ("bees", "rabbit") else "cobblestone")
        ridge = d.gable(x1, z1, x2, z2, top + 1, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite")
        ytop, ylamp = ridge - 1, 5
        for x in range(xm - 1, xm + 2):                                # ridge ventilator
            d.set(x, ridge, zc, "dark_oak_planks")
            d.set(x, ridge + 1, zc, slab("deepslate_tile_slab"))
    elif pack == "Cascadia":
        cs_logs(d, x1, z1, x2, z2, top)
        ridge = d.gable(x1, z1, x2, z2, top + 1, "x", "dark_oak_stairs", "dark_oak_slab", "spruce_planks")
        ytop, ylamp = ridge - 1, 5
    else:
        ntop = 9 if loft else top
        nt_walls(d, x1, z1, x2, z2, ntop, sides="nsew", col_step=3, glaze=(4, 4))
        if loft:
            for x in range(x1 + 1, x2):
                for z in (z1, z2):
                    if d.get(x, 5, z) != "minecraft:light_gray_concrete":
                        d.set(x, 8, z, "light_gray_stained_glass_pane")
                d.set(x, 6, z1, "cyan_terracotta")
                d.set(x, 6, z2, "cyan_terracotta")
        nt_roof(d, x1, z1, x2, z2, ntop + 1, solar_rows=True)
        if not loft:
            for x in range(x1 + 1, x2):
                d.set(x, 6, zc, "glass")
                d.set(x, 7, zc, AIR)
        ytop, ylamp = 5, 5
    if loft and kind != "horse":                                       # hay loft / upper floor
        deck = "light_gray_concrete" if pack == "Neoterra" else "spruce_planks"
        d.fill(x1 + 1, 6, z1 + 1, x2 - 1, 6, z2 - 1, deck)
        for x in range(x1 + 2, x2 - 1):
            for z in ((z1 + 1, z2 - 1) if pack == "Neoterra" else (z1 + 2, z2 - 2)):
                if pack == "Neoterra":
                    d.set(x, 7, z, "barrel[facing=up,open=false]" if x % 3 else "white_concrete")
                    d.set(x, 8, z, "potted_bamboo" if x % 3 == 0 else AIR)
                else:
                    hay(d, x, 7, z, "x")
                    if x % 2:
                        hay(d, x, 7, z + (1 if z < zc else -1), "x")
        for x in range(x1 + 3, x2 - 2, 4):
            if pack == "Neoterra":
                d.set(x, 7, zc - 1, "white_concrete")
                d.set(x, 8, zc - 1, "potted_azure_bluet")
                d.chair(x, 7, zc, "south", "birch", sit=False)
                d.set(x, 10, zc, "sea_lantern")
        ytop, ylamp = 5, 5
    d.double_door(xm, 2, z1, "x", "south", wood)
    for x in range(x1 + 2, x2 - 1, 3):
        if pack != "Neoterra" and abs(x - xm) > 1:
            d.window(x, 3, z1, x, 4, z1)
            d.window(x, 3, z2, x, 4, z2)
    d.window(x1, 3, zc, x1, 4, zc)
    d.window(x2, 3, zc, x2, 4, zc)
    xs = [x for x in range(x1 + 1, x2) if x not in (xm, xm + 1)]
    upper = f"{wood}_fence"
    lower = "smooth_quartz" if pack == "Neoterra" else f"{wood}_planks"
    if kind in ("cattle", "sheep", "pig"):
        manger = {"cattle": "hay_block[axis=x]", "sheep": "hay_block[axis=y]", "pig": "water_cauldron[level=3]"}[kind]
        for zb, zf in ((z1 + 1, z1 + 3), (z2 - 1, z2 - 3)):
            for x in xs:
                d.set(x, 2, zb, manger if x % 2 else ("hay_block[axis=x]" if kind == "pig" else
                                                      "water_cauldron[level=3]"))
                d.set(x, 2, zf, gate(wood, "south" if zf > zb else "north") if (x - x1) % 3 == 2 else upper)
                if (x - x1) % 3 == 0:
                    for z in range(min(zb, zf) + 1, max(zb, zf)):
                        d.set(x, 2, z, lower if kind == "pig" else upper)
            for x in xs:
                if kind == "pig" and x % 4 == 1:
                    d.set(x, 1, (zb + zf) // 2, "hay_block[axis=x]")
        if kind == "sheep":
            for x in (x1 + 1, x2 - 1):
                d.set(x, 2, zc, "white_wool")
                d.set(x, 3, zc, "white_wool")
    elif kind == "poultry":
        for zz, face in ((z1 + 1, "south"), (z2 - 1, "north")):
            for x in xs:
                d.set(x, 2, zz, "hay_block[axis=x]")
                d.set(x, 3, zz, trap(wood, face, "top"))
                d.set(x, 4, zz, "hay_block[axis=x]")
        for x in xs[::3]:
            d.set(x, 2, zc - 1, "composter[level=6]")
            d.set(x, 2, zc + 1, "water_cauldron[level=3]")
        for x in xs[1::4]:
            d.set(x, 2, zc, upper)
            d.set(x, 3, zc, slab(f"{wood}_slab"))
    elif kind == "rabbit":
        hutch_row(d, x1 + 1, xm - 1, z1 + 1, 2, wood if pack != "Neoterra" else "birch", "south", 2)
        hutch_row(d, xm + 2, x2 - 1, z1 + 1, 2, wood if pack != "Neoterra" else "birch", "south", 2)
        hutch_row(d, x1 + 1, x2 - 1, z2 - 1, 2, wood if pack != "Neoterra" else "birch", "north", 2)
        for x in xs[1::3]:
            d.set(x, 2, zc, slab(f"{wood}_slab", "top"))
            d.set(x, 3, zc, "potted_dandelion")
    elif kind == "bees":
        for zz, face in ((z1 + 1, "south"), (z2 - 1, "north")):
            for x in xs:
                k = x % 4
                d.set(x, 2, zz, ("barrel[facing=up,open=false]", "honey_block", "beehive[facing=%s,honey_level=5]"
                                 % face, "honeycomb_block")[k])
                shelf(d, x, 3, zz, wood, ("candle[candles=4,lit=false,waterlogged=false]", "honey_block",
                                          "decorated_pot[cracked=false,facing=north,waterlogged=false]",
                                          "candle[candles=2,lit=false,waterlogged=false]")[k])
        for x in xs[1::4]:
            d.set(x, 2, zc, slab(f"{wood}_slab", "top"))
            if x + 1 not in (xm, xm + 1):
                d.set(x + 1, 2, zc, "water_cauldron[level=3]")
            d.set(x, 3, zc, "brewing_stand[has_bottle_0=true,has_bottle_1=true,has_bottle_2=true]")
    elif kind == "horse":                                              # indoor riding school
        for x in range(x1 + 1, x2):
            for z in range(z1 + 1, z2):
                d.set(x, 1, z, "sand" if pack != "Neoterra" else "smooth_sandstone")
        for x in range(x1 + 2, x2 - 1):
            d.set(x, 2, z1 + 2, upper if x not in (xm, xm + 1) else AIR)
        for x in range(x1 + 1, x2):
            if x not in (xm, xm + 1):
                d.set(x, 2, z1 + 1, st(f"{wood}_stairs", "north"))
        for jx in range(x1 + 4, x2 - 2, 6):
            d.set(jx, 2, zc + 1, upper)
            d.set(jx + 2, 2, zc + 1, upper)
            d.set(jx + 1, 2, zc + 1, trap(wood, "north", "top"))
            d.set(jx, 3, zc + 1, "white_wool" if pack != "Neoterra" else "cyan_concrete")
            d.set(jx + 2, 3, zc + 1, "red_wool" if pack != "Neoterra" else "cyan_concrete")
        d.set(x2 - 2, 2, z2 - 1, st(f"{wood}_stairs", "south"))
        d.set(x2 - 1, 2, z2 - 1, f"{wood}_planks")
    if loft and kind != "horse":
        for y in range(2, 7):
            d.set(x1 + 1, y, zc, "ladder[facing=east,waterlogged=false]")
        d.set(x1 + 2, 2, zc, AIR)
        d.set(x1 + 2, 3, zc, AIR)
    if loft and kind == "horse":                                       # spectators' gallery
        deck = "light_gray_concrete" if pack == "Neoterra" else f"{wood}_planks"
        for x in range(x1 + 1, x2):
            d.set(x, 6, z1 + 1, deck)
            d.set(x, 6, z1 + 2, deck)
            d.set(x, 7, z1 + 3, upper)
            d.set(x, 6, z1 + 3, slab(f"{wood}_slab", "top"))
            if x % 2:
                d.set(x, 7, z1 + 1, st(f"{wood}_stairs", "north"))
        for y in range(2, 8):
            d.set(x2 - 1, y, z1 + 1, "ladder[facing=west,waterlogged=false]")
        d.set(x2 - 1, 7, z1 + 1, "ladder[facing=west,waterlogged=false]")
        d.set(x2 - 1, 7, z1 + 3, AIR)
    for x in range(x1 + 2, x2 - 1, 4):
        if pack == "Neoterra":
            d.set(x, 5, zc + 1, "sea_lantern")
        elif loft and kind != "horse":
            hang(d, x, 5, zc + 1, 4)
        else:
            hang(d, x, ytop, zc, ylamp - 1 if kind != "horse" else ylamp + top - 5)
    lamp_post(d, xm - 2, z1 - 1, pack)
    d.sign(xm + 3, 4, z1 - 1, "north", {"poultry": ["Laying", "House"], "cattle": ["Calf", "House"],
                                         "sheep": ["Lambing", "Shed"], "pig": ["Farrowing", "House"],
                                         "rabbit": ["Hutch", "House"], "bees": ["Honey &", "Candles"],
                                         "horse": ["Riding", "School"]}[kind], wood,
           glow=pack == "Neoterra", color="cyan" if pack == "Neoterra" else "black")


# ------------------------------------------------------------------------------------------- L5: hay barn
def haybarn(d, pack, x1, z1, size=(11, 9)):
    """Big hay / threshing barn n x dep plus granary or silos to the east (x2+2..x2+4)."""
    n, dep, sh = size
    x2, z2 = x1 + n - 1, z1 + dep - 1
    xm = (x1 + x2) // 2
    if pack == "Hearthwood":                                           # stone threshing barn + granary
        d.box(x1, 2, z1, x2, 6, z2, "cobblestone", floor="stone_bricks")
        for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
            for y in range(2, 7):
                d.set(x, y, z, "stone_bricks" if y % 2 else "polished_andesite")
        for x in range(x1 + 2, x2 - 1, 4):                             # buttresses
            for z, f in ((z1 - 1, "south"), (z2 + 1, "north")):
                d.set(x, 2, z, "stone_bricks")
                d.set(x, 3, z, "stone_bricks")
                d.set(x, 4, z, st("stone_brick_stairs", f))
        ridge = d.gable(x1, z1, x2, z2, 7, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "cobblestone")
        for z in (z1, z2):                                             # wagon doors
            for x in range(xm - 1, xm + 2):
                for y in range(2, 6):
                    d.set(x, y, z, AIR)
                d.set(x, 6, z, "stripped_dark_oak_log[axis=x]")
        d.set(x1, ridge - 2, z1 + 4, AIR)                              # owl hole
        for x in [x for x in range(x1 + 1, x2) if abs(x - xm) > 1]:   # hay bays, stepped toward the floor
            for z in range(z1 + 1, z2):
                for y in range(2, 2 + min(4, abs(x - xm))):
                    hay(d, x, y, z, "z" if (y + x) % 2 else "x")
        for x in (xm - 1, xm, xm + 1):                                 # loaded wagon on the threshing floor
            d.set(x, 2, z1 + 3, slab("dark_oak_slab", "top"))
            d.set(x, 2, z1 + 5, slab("dark_oak_slab", "top"))
            d.set(x, 2, z1 + 4, slab("dark_oak_slab", "top"))
            hay(d, x, 3, z1 + 4, "x")
        for z in (z1 + 3, z1 + 5):
            d.set(xm - 1, 3, z, trap("dark_oak", "north" if z < z1 + 4 else "south", open_=True))
        d.set(xm, 2, z1 + 2, "dark_oak_fence")
        for z in (z1 + 6, z1 + 7):
            d.set(xm + 1, 2, z, "white_wool")
            d.set(xm - 1, 2, z, "barrel[facing=up,open=false]")
        hang(d, xm, ridge - 1, z1 + 4, 6)
        gx = x2 + 2                                                    # granary on staddle stones
        for dx in range(3):
            for dz in range(3):
                x, z = gx + dx, z1 + 2 + dz
                if (dx, dz) in ((0, 0), (2, 0), (0, 2), (2, 2)):
                    d.set(x, 2, z, "andesite_wall[east=none,north=none,south=none,up=true,waterlogged=false,"
                                   "west=none]")
                    d.set(x, 3, z, slab("andesite_slab", "top"))
                for y in (4, 5, 6):
                    d.set(x, y, z, "oak_planks" if dx != 1 or dz != 1 else "hay_block[axis=y]")
                d.set(x, 7, z, slab("deepslate_tile_slab"))
        d.set(gx + 1, 8, z1 + 3, "deepslate_tiles")
        d.set(gx + 1, 5, z1 + 2, "dark_oak_trapdoor[facing=north,half=bottom,open=true,powered=false,"
                                 "waterlogged=false]")
    elif pack == "Cascadia":                                           # pole hay barn + stave silo
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                d.set(x, 1, z, "coarse_dirt")
                if (x in (x1, x2) or z in (z1, z2)):
                    post = (x - x1) % 5 == 0 and z in (z1, z2) or (z - z1) % 4 == 0 and x in (x1, x2)
                    for y in range(2, 7):
                        if post:
                            d.set(x, y, z, "spruce_log[axis=y]")
                        elif y <= 3 and z != z1:
                            d.set(x, y, z, "spruce_planks")
                    if not post:
                        d.set(x, 6, z, "stripped_spruce_log[axis=%s]" % ("x" if z in (z1, z2) else "z"))
        ridge = d.gable(x1, z1, x2, z2, 7, "x", "dark_oak_stairs", "dark_oak_slab", "spruce_planks")
        for x in range(x1 + 1, x2):
            for z in range(z1 + 3, z2):
                h = 5 if x not in (xm, xm + 1) else 0
                for y in range(2, 2 + h):
                    hay(d, x, y, z, "x" if (y + z) % 2 else "z")
        for x in (xm, xm + 1):                                         # hay wagon in the drive
            for z in (z1 + 4, z1 + 5, z1 + 6):
                d.set(x, 2, z, slab("spruce_slab", "top"))
                hay(d, x, 3, z, "z")
        d.set(xm, 2, z1 + 3, "spruce_fence")
        hang(d, xm, ridge - 1, z1 + 2, 6)
        sx = x2 + 2                                                    # stave silo
        for y in range(2, sh - 1):
            for dx in range(3):
                for dz in range(3):
                    if (dx, dz) != (1, 1):
                        d.set(sx + dx, y, z1 + 2 + dz, "spruce_planks" if y % 4 else "stripped_spruce_log[axis=x]")
                    else:
                        d.set(sx + dx, y, z1 + 2 + dz, "hay_block[axis=y]")
        for dx in range(3):
            for dz in range(3):
                d.set(sx + dx, sh - 1, z1 + 2 + dz, slab("dark_oak_slab") if (dx, dz) != (1, 1) else "dark_oak_planks")
        d.set(sx + 1, sh, z1 + 3, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        for y in range(2, sh - 2):
            d.set(sx + 1, y, z1 + 1, "ladder[facing=north,waterlogged=false]")
    else:                                                              # feed hub: machine hall + two silos
        nt_walls(d, x1, z1, x2, z2, 6, sides="nwe", col_step=5, floor="smooth_stone")
        nt_roof(d, x1, z1, x2, z2, 7, solar_rows=True)
        for x in range(xm - 1, xm + 2):
            for y in range(2, 6):
                d.set(x, y, z1, AIR)
            d.set(x, 6, z1, "cyan_terracotta")
        for x in range(x1 + 1, x2):
            for z in range(z1 + 4, z2):
                if x not in (xm - 1, xm, xm + 1):
                    for y in range(2, 2 + (3 if z > z1 + 5 else 2)):
                        hay(d, x, y, z, "x")
        d.set(xm, 2, z1 + 2, "iron_block")
        d.set(xm, 3, z1 + 2, "hopper[enabled=true,facing=down]")
        d.set(xm + 1, 2, z1 + 2, "iron_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
        for x in (x1 + 3, x2 - 3):
            d.set(x, 6, z1 + 4, "sea_lantern")
        for sz_ in (z1, z1 + 5):                                       # silos
            sx = x2 + 2
            for y in range(2, sh):
                for dx in range(3):
                    for dz in range(3):
                        if (dx, dz) != (1, 1):
                            d.set(sx + dx, y, sz_ + dz, "light_gray_concrete" if y % 5 else "cyan_terracotta")
                        else:
                            d.set(sx + dx, y, sz_ + dz, "hay_block[axis=y]")
            for dx in range(3):
                for dz in range(3):
                    d.set(sx + dx, sh, sz_ + dz, slab("smooth_quartz_slab"))
            d.set(sx + 1, sh + 1, sz_ + 1, "end_rod[facing=up]")
        for x in range(x2 + 1, x2 + 2):
            d.set(x, 13, z1 + 1, "iron_bars")
            d.set(x, 12, z1 + 1, slab("smooth_stone_slab", "top"))


# ------------------------------------------------------------------------------------------- type extras
MAT = {
    "Hearthwood": dict(wall="calcite", base="stone_bricks", trim="stripped_dark_oak_log", plank="dark_oak_planks",
                       wood="dark_oak", rs="deepslate_tile_stairs", rsl="deepslate_tile_slab", rb="deepslate_tiles",
                       floor="spruce_planks", fence="dark_oak_fence", awn=("red_wool", "white_wool")),
    "Cascadia": dict(wall="stripped_spruce_log", base="cobblestone", trim="spruce_log", plank="spruce_planks",
                     wood="spruce", rs="dark_oak_stairs", rsl="dark_oak_slab", rb="dark_oak_planks",
                     floor="spruce_planks", fence="spruce_fence", awn=("green_wool", "white_wool")),
    "Neoterra": dict(wall="white_concrete", base="polished_andesite", trim="light_gray_concrete",
                     plank="birch_planks", wood="birch", rs="smooth_quartz_stairs", rsl="smooth_quartz_slab",
                     rb="smooth_quartz", floor="polished_diorite", fence="birch_fence", awn=("cyan_wool", "white_wool")),
}


def bldg(d, pack, x1, z1, x2, z2, top, axis="x", roof="gable", glass_rows=(3, 4)):
    """Small outbuilding shell: base course, corner/trim posts, walls, windows every 3, pack roof.
    Returns the ridge / roof height."""
    M = MAT[pack]
    d.box(x1, 2, z1, x2, top, z2, M["wall"], floor=M["floor"])
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if x in (x1, x2) or z in (z1, z2):
                d.set(x, 2, z, M["base"])
                if (x in (x1, x2) and z in (z1, z2)):
                    for y in range(3, top + 1):
                        d.set(x, y, z, M["trim"] + ("[axis=y]" if "log" in M["trim"] else ""))
                elif ((x - x1) % 3 == 0 and z in (z1, z2)) or ((z - z1) % 3 == 0 and x in (x1, x2)):
                    pass
                else:
                    if ((x - x1) % 3 == 1 and z in (z1, z2) and x < x2 - 1) or \
                            ((z - z1) % 3 == 1 and x in (x1, x2) and z < z2 - 1):
                        for y in glass_rows:
                            d.set(x, y, z, "glass_pane")
    if pack == "Neoterra" or roof == "flat":
        if pack == "Neoterra":
            nt_roof(d, x1, z1, x2, z2, top + 1, solar_rows=False, green=True)
        else:
            d.flat(x1, z1, x2, z2, top + 1, M["rb"])
        return top + 1
    if roof == "hip":
        return d.hip(x1, z1, x2, z2, top + 1, M["rs"], M["rsl"])
    return d.gable(x1, z1, x2, z2, top + 1, axis, M["rs"], M["rsl"], M["wall"] if pack != "Cascadia" else
                   "spruce_planks")


def extra(d, pack, kind, x1, z1):
    """Type-specific L5 building in the east strip (region 11 x 9 from (x1, z1))."""
    M = MAT[pack]
    w = M["wood"]
    if kind == "poultry":                                              # dovecote tower + duck pond
        tx1, tz1 = x1 + 1, z1 + 2
        top = 10
        ridge = bldg(d, pack, tx1, tz1, tx1 + 4, tz1 + 4, top, roof="hip")
        for y in (8, 9):
            for k in (1, 3):
                for x, z, f in ((tx1 + k, tz1, "north"), (tx1 + k, tz1 + 4, "south"), (tx1, tz1 + k, "west"),
                                (tx1 + 4, tz1 + k, "east")):
                    d.set(x, y, z, AIR if y == 9 else M["wall"])
                    dx, dz = D4[f]
                    if y == 8:
                        d.set(x + dx, 8, z + dz, slab(M["rsl"] if pack != "Cascadia" else "spruce_slab", "top"))
        for y in (4, 6, 8):                                            # nesting ledges inside
            for x in range(tx1 + 1, tx1 + 4):
                d.set(x, y, tz1 + 3, slab(f"{w}_slab", "top"))
            d.set(tx1 + 3, y, tz1 + 2, slab(f"{w}_slab", "top"))
        for y in range(2, 9):
            d.set(tx1 + 1, y, tz1 + 1, "ladder[facing=south,waterlogged=false]")
        d.door(tx1 + 2, 2, tz1, "south", w)
        d.set(tx1 + 2, ridge + 1, tz1 + 2, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        for x in range(x1 + 7, x1 + 11):
            for z in range(z1 + 3, z1 + 7):
                edge = x in (x1 + 7, x1 + 10) or z in (z1 + 3, z1 + 6)
                d.set(x, 1, z, "mud" if edge else "water")
        d.set(x1 + 8, 2, z1 + 4, "lily_pad")
        d.set(x1 + 7, 2, z1 + 3, "sugar_cane")
        d.set(x1 + 7, 1, z1 + 3, "dirt")
        bench(d, x1 + 7, z1 + 8, "south", w, 3)
        lamp_post(d, x1 + 6, z1 + 8, pack)
    elif kind == "cattle":                                             # creamery & farm shop
        ridge = bldg(d, pack, x1 + 1, z1 + 2, x1 + 9, z1 + 7, 5)
        d.double_door(x1 + 5, 2, z1 + 2, "x", "south", w)
        for x in range(x1, x1 + 11):                                   # striped awning
            d.set(x, 5, z1 + 1, M["awn"][x % 2])
        for x in (x1, x1 + 10):
            for y in (2, 3, 4):
                d.set(x, y, z1 + 1, M["fence"])
        d.set(x1 + 2, 2, z1 + 1, "cauldron")
        d.set(x1 + 3, 2, z1 + 1, "cauldron")
        d.set(x1 + 8, 2, z1 + 1, slab(f"{w}_slab", "top"))
        d.set(x1 + 8, 3, z1 + 1, "cake[bites=0]")
        for x in range(x1 + 2, x1 + 9):                                # shop counter and shelves
            if x not in (x1 + 5, x1 + 6):
                d.set(x, 2, z1 + 4, slab(f"{w}_slab", "top"))
                d.set(x, 3, z1 + 4, ("cake[bites=0]", "yellow_terracotta", "candle[candles=2,lit=false,"
                                     "waterlogged=false]")[x % 3])
            d.set(x, 2, z1 + 6, "barrel[facing=up,open=false]" if x % 2 else "water_cauldron[level=3]")
            shelf(d, x, 4, z1 + 6, w, ("yellow_terracotta", "decorated_pot[cracked=false,facing=north,"
                                       "waterlogged=false]", "honey_block")[x % 3])
        hang(d, x1 + 5, ridge - 1, z1 + 4, 4)
        d.sign(x1 + 7, 4, z1 + 1, "north", ["Creamery", "milk ~ cheese"], w)
    elif kind == "sheep":                                              # dye house + drying racks
        ridge = bldg(d, pack, x1 + 1, z1 + 1, x1 + 8, z1 + 5, 5)
        d.door(x1 + 4, 2, z1 + 1, "south", w)
        cols = {"Hearthwood": ("red", "yellow", "blue", "brown", "white", "red", "blue", "yellow"),
                "Cascadia": ("orange", "green", "lime", "cyan", "purple", "magenta", "pink", "light_blue"),
                "Neoterra": ("cyan", "light_blue", "magenta", "lime", "pink", "orange", "cyan", "white")}[pack]
        for i, x in enumerate(range(x1 + 2, x1 + 8)):
            d.set(x, 2, z1 + 4, "water_cauldron[level=3]")
            d.set(x, 2, z1 + 2, f"{cols[i % 8]}_wool" if x != x1 + 4 else AIR)
            if x != x1 + 4:
                d.set(x, 3, z1 + 2, f"{cols[(i + 3) % 8]}_wool")
        hang(d, x1 + 4, ridge - 1, z1 + 3, 4)
        for z in (z1 + 7, z1 + 8):                                     # drying racks outside
            for x in range(x1, x1 + 11):
                if (x - x1) % 5 == 0:
                    for y in (2, 3):
                        d.set(x, y, z, M["fence"])
                d.set(x, 4, z, f"{cols[(x + z) % 8]}_wool")
        d.sign(x1 + 6, 4, z1, "north", ["Dye", "House"], w)
    elif kind == "pig":                                                # smokehouse + muck heap
        sx1, sz1 = x1 + 2, z1 + 2
        ridge = bldg(d, pack, sx1, sz1, sx1 + 4, sz1 + 4, 6, glass_rows=())
        d.door(sx1 + 2, 2, sz1, "south", w)
        d.set(sx1 + 2, 1, sz1 + 2, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        d.set(sx1 + 2, 2, sz1 + 2, AIR)
        for x in (sx1 + 1, sx1 + 3):
            for z in (sz1 + 1, sz1 + 3):
                d.set(x, 6, z, "chain[axis=y,waterlogged=false]")
                d.set(x, 5, z, "chain[axis=y,waterlogged=false]")
                d.set(x, 4, z, "dried_kelp_block")
        for y in range(ridge - 1, ridge + 3):
            d.set(sx1 + 2, y, sz1 + 2, "bricks" if pack != "Neoterra" else "polished_blackstone_bricks")
        d.set(sx1 + 2, ridge + 3, sz1 + 2, "campfire[facing=north,lit=false,signal_fire=false,waterlogged=false]")
        for x in range(x1 + 8, x1 + 11):
            for z in range(z1 + 2, z1 + 5):
                d.set(x, 2, z, "composter[level=%d]" % (3 + (x + z) % 5))
        for z in range(z1 + 6, z1 + 9):                                # log pile for the smoker
            for y in (2, 3):
                d.set(x1 + 9, y, z, "oak_log[axis=x]")
                d.set(x1 + 10, y, z, "oak_log[axis=x]")
        d.sign(sx1 + 3, 4, sz1 - 1, "north", ["Smoke", "House"], w)
    elif kind == "rabbit":                                             # glasshouse with carrot beds
        gx1, gz1, gx2, gz2 = x1, z1 + 1, x1 + 10, z1 + 7
        for x in range(gx1, gx2 + 1):
            for z in range(gz1, gz2 + 1):
                edge = x in (gx1, gx2) or z in (gz1, gz2)
                d.set(x, 1, z, M["floor"] if pack != "Cascadia" else "spruce_planks")
                for y in range(2, 7):
                    if edge:
                        post = (x - gx1) % 5 == 0 and z in (gz1, gz2) or x in (gx1, gx2) and z in (gz1, gz2)
                        d.set(x, y, z, M["base"] if y == 2 else (M["trim"] + ("[axis=y]" if "log" in M["trim"]
                                                                               else "")) if post else "glass")
                    else:
                        d.set(x, y, z, AIR)
                d.set(x, 7, z, "glass" if not edge else M["base"] if pack != "Cascadia" else "spruce_planks")
                if gz1 + 2 <= z <= gz2 - 2 and not edge:
                    d.set(x, 8, z, "glass")
        for x in range(gx1 + 1, gx2):
            d.set(x, 9, gz1 + 3, slab(M["rsl"] if pack != "Cascadia" else "spruce_slab"))
        d.door(gx1 + 5, 2, gz1, "south", w)
        for z in (gz1 + 1, gz2 - 1):
            for x in range(gx1 + 1, gx2):
                if x != gx1 + 5 or z != gz1 + 1:
                    d.set(x, 2, z, "farmland[moisture=7]")
                    d.set(x, 3, z, ("carrots[age=7]", "beetroots[age=3]", "carrots[age=5]")[x % 3])
        d.set(gx2 - 1, 2, gz1 + 3, "water_cauldron[level=3]")
        for z in (gz1 + 2, gz1 + 4):
            d.set(gx1 + 1, 2, z, slab(f"{w}_slab", "top"))
            d.set(gx1 + 1, 3, z, "potted_dandelion" if z % 2 else "potted_fern")
        hang(d, gx1 + 5, 8, gz1 + 3, 6)
    elif kind == "bees":                                               # orchard with skeps + honey stall
        for tx in (x1 + 1, x1 + 5, x1 + 9):
            for tz in (z1 + 1, z1 + 5):
                for y in (2, 3):
                    d.set(tx, y, tz, "oak_log[axis=y]" if pack != "Neoterra" else "birch_log[axis=y]")
                for dx in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        d.set(tx + dx, 4, tz + dz, "flowering_azalea_leaves" + LEAVES)
                d.set(tx, 5, tz, "flowering_azalea_leaves" + LEAVES)
                d.set(tx + 1, 2, tz + 1, "beehive[facing=south,honey_level=2]" if (tx + tz) % 2 else "poppy")
        for x in range(x1 + 3, x1 + 8):                                # honey stall under an awning
            d.set(x, 2, z1 + 8, slab(f"{w}_slab", "top"))
            d.set(x, 3, z1 + 8, ("honey_block", "candle[candles=3,lit=false,waterlogged=false]",
                                 "honeycomb_block")[x % 3])
            d.set(x, 5, z1 + 8, M["awn"][x % 2])
        for x in (x1 + 3, x1 + 7):
            d.set(x, 4, z1 + 8, M["fence"])
            d.set(x, 4, z1 + 8, M["fence"])
        d.set(x1 + 3, 3, z1 + 8, M["fence"])
        d.set(x1 + 7, 3, z1 + 8, M["fence"])
    elif kind == "horse":                                              # farrier's forge
        fx1, fz1, fx2, fz2 = x1 + 1, z1 + 2, x1 + 9, z1 + 7
        for x in range(fx1, fx2 + 1):
            for z in range(fz1, fz2 + 1):
                d.set(x, 1, z, "cobblestone" if pack != "Neoterra" else "polished_andesite")
                if z == fz2 or x in (fx1, fx2) and z > fz1 + 2:
                    for y in (2, 3, 4):
                        d.set(x, y, z, M["base"] if y == 2 else M["wall"])
        for x, z in ((fx1, fz1), (fx2, fz1), (fx1, fz2), (fx2, fz2), (x1 + 5, fz1)):
            for y in (2, 3, 4):
                d.set(x, y, z, M["trim"] + ("[axis=y]" if "log" in M["trim"] else ""))
        if pack == "Neoterra":
            nt_roof(d, fx1, fz1, fx2, fz2, 5, solar_rows=True)
            ridge = 6
        else:
            ridge = d.gable(fx1, fz1, fx2, fz2, 5, "x", M["rs"], M["rsl"], M["wall"])
        d.hearth(x1 + 5, 2, fz2 - 1, "north", ridge + 2, "bricks" if pack != "Neoterra" else
                 "polished_blackstone_bricks", "campfire")
        d.set(x1 + 3, 2, fz1 + 2, "anvil[facing=east]")
        d.set(x1 + 7, 2, fz1 + 2, "water_cauldron[level=3]")
        d.set(fx1 + 1, 2, fz2 - 1, "blast_furnace[facing=north,lit=true]")
        d.set(fx2 - 1, 2, fz2 - 1, "grindstone[face=floor,facing=north]")
        d.set(fx2 - 1, 2, fz2 - 2, "smithing_table")
        for x in range(fx1 + 1, fx1 + 4):
            d.set(x, 4, fz2 - 1, "tripwire_hook[attached=false,facing=north,powered=false]")
        for x in range(x1, x1 + 11, 2):                                # hitching rail
            d.set(x, 2, z1, M["fence"])
        d.sign(x1 + 5, 4, fz1 - 1, "north", ["Farrier"], w)


def rick(d, pack, x1, z1, big=False):
    """Thatched hay rick (5 x 5, or 7 x 7) or a wrapped-bale stack for Neoterra."""
    if big:
        x1 -= 1
        z1 -= 1
    lay = ((2, 3), (3, 3), (4, 3), (5, 2), (6, 1), (7, 0)) if big else ((2, 2), (3, 2), (4, 2), (5, 1), (6, 0))
    for y, r in lay:
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                cx, cz = x1 + 2 + dx, z1 + 2 + dz
                if pack == "Neoterra":
                    if y < 5:
                        d.set(cx, y, cz, "white_wool")
                else:
                    d.set(cx, y, cz, "hay_block[axis=y]")
    if pack != "Neoterra":
        d.set(x1 + 2, 7, z1 + 2, slab("spruce_slab"))
    return True


def shed_fit(d, pack, kind, x1, z1, w):
    """Type-specific fit-out of the L2 shed's east bay and a sign naming it."""
    M = MAT[pack]
    x2, z2 = x1 + w - 1, z1 + 4
    label = {"poultry": ["Feed &", "Egg Store"], "cattle": ["Milk", "Churns"], "sheep": ["Wool", "Store"],
             "pig": ["Swill", "House"], "rabbit": ["Root", "Store"], "bees": ["Skeps &", "Frames"],
             "horse": ["Tack &", "Harness"]}[kind]
    goods = {"poultry": ("white_wool", "hay_block[axis=y]", "turtle_egg[eggs=4,hatch=0]"),
             "cattle": ("cauldron", "water_cauldron[level=3]", "barrel[facing=up,open=false]"),
             "sheep": ("white_wool", "light_gray_wool", "brown_wool"),
             "pig": ("composter[level=8]", "barrel[facing=up,open=false]", "pumpkin"),
             "rabbit": ("barrel[facing=up,open=false]", "pumpkin", "melon"),
             "bees": ("beehive[facing=north,honey_level=0]", "honeycomb_block", "barrel[facing=up,open=false]"),
             "horse": ("hay_block[axis=y]", "barrel[facing=up,open=false]", "brown_wool")}[kind]
    for i, x in enumerate(range(x2 - 3, x2)):                       # one bay of goods against the back wall
        d.set(x, 2, z2 - 1, goods[i % 3])
    if d.air(x1 + 2, 4, z1 - 1):
        d.sign(x1 + 2, 4, z1 - 1, "north", label, M["wood"])


RECOLOR = {
    ("Hearthwood", "poultry"): {"deepslate_tile_stairs": "brick_stairs", "deepslate_tile_slab": "brick_slab",
                                "deepslate_tiles": "bricks", "bricks": "stone_bricks", "calcite": "yellow_terracotta",
                                "stripped_dark_oak_log": "stripped_oak_log", "dark_oak_planks": "oak_planks"},
    ("Hearthwood", "cattle"): {"deepslate_tile_stairs": "dark_prismarine_stairs",
                               "deepslate_tile_slab": "dark_prismarine_slab", "deepslate_tiles": "dark_prismarine",
                               "calcite": "smooth_sandstone", "bricks": "sandstone", "brick_slab": "sandstone_slab"},
    ("Hearthwood", "sheep"): {"deepslate_tile_stairs": "mud_brick_stairs", "deepslate_tile_slab": "mud_brick_slab",
                              "deepslate_tiles": "mud_bricks", "calcite": "white_terracotta",
                              "stripped_dark_oak_log": "stripped_oak_log", "dark_oak_planks": "oak_planks"},
    ("Hearthwood", "pig"): {"deepslate_tile_stairs": "granite_stairs", "deepslate_tile_slab": "granite_slab",
                            "deepslate_tiles": "polished_granite", "calcite": "pink_terracotta",
                            "bricks": "mud_bricks", "brick_slab": "mud_brick_slab"},
    ("Hearthwood", "rabbit"): {"calcite": "light_blue_terracotta", "stone_bricks": "andesite"},
    ("Hearthwood", "bees"): {"stripped_dark_oak_log": "stripped_oak_log", "dark_oak_planks": "oak_planks",
                             "stone_bricks": "mossy_stone_bricks"},
    ("Hearthwood", "horse"): {"deepslate_tile_stairs": "dark_oak_stairs", "deepslate_tile_slab": "dark_oak_slab",
                              "deepslate_tiles": "dark_oak_planks", "bricks": "stone_bricks",
                              "stone_bricks": "cobblestone", "brick_slab": "stone_brick_slab"},
    ("Cascadia", "poultry"): {"dark_oak_stairs": "mangrove_stairs", "dark_oak_slab": "mangrove_slab",
                              "spruce_planks": "birch_planks"},
    ("Cascadia", "cattle"): {"dark_oak_stairs": "dark_prismarine_stairs", "dark_oak_slab": "dark_prismarine_slab",
                             "dark_oak_planks": "dark_prismarine"},
    ("Cascadia", "sheep"): {"stripped_spruce_log": "stripped_birch_log", "spruce_log": "dark_oak_log"},
    ("Cascadia", "pig"): {"stripped_spruce_log": "spruce_log", "spruce_log": "stripped_spruce_log",
                          "cobblestone": "tuff", "cobblestone_slab": "tuff_slab"},
    ("Cascadia", "rabbit"): {"stripped_spruce_log": "stripped_mangrove_log", "spruce_log": "stripped_spruce_log",
                             "cobblestone": "tuff",
                             "dark_oak_stairs": "warped_stairs", "dark_oak_slab": "warped_slab"},
    ("Cascadia", "bees"): {"dark_oak_stairs": "cherry_stairs", "dark_oak_slab": "cherry_slab",
                           "spruce_planks": "birch_planks", "cobblestone": "andesite"},
    ("Cascadia", "horse"): {"cobblestone": "mossy_cobblestone", "spruce_planks": "dark_oak_planks"},
    ("Neoterra", "poultry"): {"white_concrete": "birch_planks", "cyan_terracotta": "orange_terracotta",
                              "cyan_concrete": "orange_concrete", "cyan_carpet": "orange_carpet"},
    ("Neoterra", "cattle"): {"white_concrete": "light_gray_concrete", "light_gray_concrete": "gray_concrete",
                             "cyan_terracotta": "lime_terracotta", "cyan_concrete": "lime_concrete",
                             "smooth_quartz": "white_concrete"},
    ("Neoterra", "sheep"): {"white_concrete": "light_gray_terracotta", "light_gray_concrete": "polished_deepslate",
                            "cyan_terracotta": "magenta_terracotta",
                            "cyan_concrete": "magenta_concrete"},
    ("Neoterra", "pig"): {"white_concrete": "white_terracotta", "light_gray_concrete": "stripped_mangrove_log"},
    ("Neoterra", "rabbit"): {"white_concrete": "brown_terracotta", "light_gray_concrete": "stripped_cherry_log", "cyan_terracotta": "pink_terracotta",
                             "cyan_concrete": "pink_concrete", "cyan_carpet": "pink_carpet"},
    ("Neoterra", "bees"): {"white_concrete": "orange_terracotta", "cyan_terracotta": "yellow_terracotta", "cyan_concrete": "yellow_concrete",
                           "cyan_wool": "yellow_wool"},
    ("Neoterra", "horse"): {"white_concrete": "gray_concrete", "light_gray_concrete": "polished_blackstone",
                            "smooth_quartz": "deepslate_tiles"},
}


def recolor(d, mapping):
    bp = d.bp
    for y in range(bp.sy):
        for z in range(bp.sz):
            row = bp.grid[y][z]
            for x in range(bp.sx):
                b = row[x]
                if b == AIR:
                    continue
                name, _, rest = b.partition("[")
                n = name.split(":")[-1]
                if n in mapping:
                    row[x] = "minecraft:" + mapping[n] + ("[" + rest if rest else "")


PREMIUM_DOWN = {
    "smooth_quartz": "smooth_stone", "smooth_quartz_slab": "smooth_stone_slab",
    "smooth_quartz_stairs": "polished_diorite_stairs", "quartz_block": "calcite", "quartz_pillar": "calcite",
    "quartz_slab": "smooth_stone_slab", "quartz_stairs": "polished_diorite_stairs",
    "sea_lantern": "glowstone", "iron_block": "smooth_stone",
    "dark_prismarine": "deepslate_tiles", "dark_prismarine_stairs": "deepslate_tile_stairs",
    "dark_prismarine_slab": "deepslate_tile_slab",
    "polished_blackstone": "polished_deepslate", "polished_blackstone_bricks": "deepslate_bricks",
    "polished_blackstone_stairs": "polished_deepslate_stairs", "polished_blackstone_slab": "polished_deepslate_slab",
}


def downgrade(d):
    """Levels 1-3: premium materials become their everyday counterparts (concrete / smooth stone decks, tile
    roofs, lanterns and chains); levels 4-5 keep the quartz, prismarine and sea-lantern upgrade."""
    bp = d.bp
    for y in range(bp.sy):
        for z in range(bp.sz):
            row = bp.grid[y][z]
            for x in range(bp.sx):
                b = row[x]
                if b == AIR:
                    continue
                name, _, rest = b.partition("[")
                n = name.split(":")[-1]
                if n == "end_rod":
                    ax = "y" if ("facing=up" in rest or "facing=down" in rest) else \
                        "x" if ("east" in rest or "west" in rest) else "z"
                    row[x] = f"minecraft:chain[axis={ax},waterlogged=false]"
                elif n in PREMIUM_DOWN:
                    row[x] = "minecraft:" + PREMIUM_DOWN[n] + ("[" + rest if rest else "")


# ------------------------------------------------------------------------------------------- core rooms
def _st(w, f):
    return f"{w}_stairs[facing={f},half=bottom,shape=straight,waterlogged=false]"


def _top(w):
    return f"{w}_slab[type=top,waterlogged=false]"


HOOK = "tripwire_hook[attached=false,facing={},powered=false]"
EGGS = "turtle_egg[eggs=4,hatch=0]"
CANDLE = "candle[candles=3,lit=false,waterlogged=false]"
LANT = "lantern[hanging=false,waterlogged=false]"
POT = "decorated_pot[cracked=false,facing=north,waterlogged=false]"


def core_rooms(d, pack, kind, L):
    """Hand-placed furniture for the core buildings' rooms (work rooms, stores, lofts), per type and pack.
    Each entry: (x, y, z, block, from-level, extra condition). Cells must be free (they are by design; the
    check only guards the shorter early-level buildings)."""
    E = []
    if (pack, kind) == ("Hearthwood", "poultry"):
        E = [(5, 2, 4, "barrel[facing=up,open=false]"), (5, 2, 5, "white_wool"),              # feed bins + sack
             (9, 2, 4, _top("dark_oak")), (10, 2, 4, _top("dark_oak")),                      # egg table
             (9, 3, 4, EGGS), (10, 3, 4, CANDLE),
             (4, 4, 5, _top("dark_oak")), (4, 5, 5, "potted_dandelion"),                     # wall shelves
             (4, 4, 7, _top("dark_oak")), (4, 5, 7, EGGS),
             (8, 4, 4, HOOK.format("south")), (5, 4, 8, HOOK.format("north"))]
    elif (pack, kind) == ("Cascadia", "poultry"):
        E = [(5, 2, 5, "barrel[facing=up,open=false]"), (7, 2, 5, "white_wool"),
             (6, 2, 12, _top("spruce")), (7, 2, 12, _top("spruce")), (6, 3, 12, EGGS), (7, 3, 12, CANDLE),
             (8, 4, 7, _top("spruce")), (8, 5, 7, "potted_fern"), (8, 4, 9, _top("spruce")), (8, 5, 9, EGGS),
             (6, 6, 12, LANT)]
    elif (pack, kind) == ("Neoterra", "poultry"):
        E = [(3, 2, 15, "barrel[facing=up,open=false]"), (3, 2, 16, "composter[level=5]"),
             (5, 2, 12, _top("smooth_stone")), (6, 2, 12, _top("smooth_stone")), (5, 3, 12, EGGS),
             (6, 3, 12, "potted_bamboo"), (6, 2, 13, _st("birch", "south")),
             (9, 2, 17, "potted_bamboo"), (11, 2, 17, "barrel[facing=up,open=false]")]
    elif (pack, kind) == ("Hearthwood", "cattle"):
        x2 = 13 if L < 3 else 19
        E = [(4, 2, 6, "cauldron"), (5, 4, 4, _top("dark_oak")), (5, 5, 4, CANDLE),
             (6, 4, 4, _top("dark_oak")), (6, 5, 4, POT), (x2 - 1, 2, 6, "barrel[facing=up,open=false]"),
             (11, 4, 4, _top("dark_oak")), (11, 5, 4, "potted_red_tulip"),
             (x2 - 2, 7, 9, "barrel[facing=up,open=false]"), (5, 7, 9, LANT), (x2 - 3, 7, 9, "white_wool")]
    elif (pack, kind) == ("Cascadia", "cattle"):
        E = [(5, 2, 6, "cauldron"), (11, 2, 4, "cauldron"), (6, 2, 6, _st("spruce", "west")),
             (9, 7, 5, "barrel[facing=up,open=false]"), (11, 7, 5, "barrel[facing=up,open=false]"),
             (10, 7, 12, LANT), (8, 7, 8, _st("spruce", "west")), (8, 7, 9, _top("spruce")),
             (8, 8, 9, CANDLE)]
    elif (pack, kind) == ("Neoterra", "cattle"):
        E = [(4, 2, 3, "light_gray_concrete"), (4, 3, 3, "brewing_stand[has_bottle_0=true,has_bottle_1=true,"
                                                         "has_bottle_2=false]"),
             (5, 2, 7, "barrel[facing=up,open=false]"), (6, 2, 7, "barrel[facing=up,open=false]"),
             (7, 2, 7, "potted_bamboo"), (5, 2, 5, _st("birch", "west")), (6, 2, 5, _top("smooth_stone")),
             (6, 3, 5, "potted_azure_bluet")]
    elif (pack, kind) == ("Hearthwood", "sheep"):
        z2 = 11 if L < 3 else 15
        E = [(4, 2, z2 - 4, "white_wool"), (4, 2, z2 - 3, "light_gray_wool"), (4, 2, z2 - 2, "barrel[facing=up,"
                                                                                           "open=false]"),
             (4, 4, 9, _top("dark_oak")), (4, 5, 9, "potted_cornflower"), (4, 4, 10, _top("dark_oak")),
             (4, 5, 10, CANDLE), (7, 2, z2 - 3, _top("oak")), (7, 2, z2 - 2, _top("oak")),
             (7, 3, z2 - 3, "white_carpet"), (7, 3, z2 - 2, "light_gray_carpet"), (6, 2, z2 - 2, _st("oak", "west"))]
    elif (pack, kind) == ("Cascadia", "sheep"):
        E = [(7, 2, 11, _top("spruce")), (8, 2, 11, _top("spruce")), (7, 3, 11, "white_carpet"),
             (8, 3, 11, "white_carpet"), (9, 2, 11, _st("spruce", "east")),
             (6, 4, 10, _top("spruce")), (6, 5, 10, POT), (10, 4, 10, _top("spruce")), (10, 5, 10, CANDLE),
             (11, 2, 12, "barrel[facing=up,open=false]")]
    elif (pack, kind) == ("Neoterra", "sheep"):
        E = [(8, 2, 5, "light_gray_concrete"), (9, 2, 5, "light_gray_concrete"), (8, 3, 5, "white_carpet"),
             (9, 3, 5, "cyan_carpet"), (8, 2, 6, _st("birch", "south")), (10, 2, 3, "potted_bamboo"),
             (6, 2, 3, "barrel[facing=up,open=false]")]
    elif (pack, kind) == ("Hearthwood", "pig"):
        E = [(7, 2, 8, "cauldron"), (6, 2, 6, "dark_oak_fence"), (6, 3, 6, "dark_oak_pressure_plate[powered=false]"),
             (6, 2, 7, _st("dark_oak", "south")), (8, 4, 7, _top("dark_oak")), (8, 5, 7, POT),
             (5, 4, 4, _top("dark_oak")), (5, 5, 4, CANDLE)]
    elif (pack, kind) == ("Cascadia", "pig"):
        E = [(8, 2, 4, "barrel[facing=up,open=false]"), (6, 2, 10, "cauldron"), (5, 2, 9, _st("spruce", "west")),
             (6, 4, 5, _top("spruce")), (6, 5, 5, CANDLE)]
    elif (pack, kind) == ("Neoterra", "pig"):
        E = [(15, 2, 16, _top("smooth_stone")), (15, 3, 16, "potted_bamboo"), (16, 2, 16, _st("birch", "west")),
             (15, 2, 17, "barrel[facing=up,open=false]"), (15, 2, 18, "composter[level=6]"),
             (16, 2, 18, "potted_azure_bluet")]
    elif (pack, kind) == ("Hearthwood", "rabbit"):
        E = [(6, 2, 4, "barrel[facing=up,open=false]"), (5, 2, 8, "composter[level=5]"),
             (8, 2, 6, "dark_oak_fence"), (8, 3, 6, "dark_oak_pressure_plate[powered=false]"),
             (8, 2, 7, _st("dark_oak", "south")), (10, 4, 8, _top("dark_oak")), (10, 5, 8, "potted_dandelion"),
             (5, 4, 4, _top("dark_oak")), (5, 5, 4, CANDLE)]
    elif (pack, kind) == ("Cascadia", "rabbit"):
        E = [(6, 2, 7, "spruce_fence"), (6, 3, 7, "spruce_pressure_plate[powered=false]"),
             (7, 2, 7, _st("spruce", "east")), (7, 2, 5, "barrel[facing=up,open=false]"),
             (8, 4, 6, _top("spruce")), (8, 5, 6, "potted_fern")]
    elif (pack, kind) == ("Neoterra", "rabbit"):
        E = [(10, 2, 17, _top("smooth_stone")), (11, 2, 17, _top("smooth_stone")), (10, 3, 17, "potted_bamboo"),
             (11, 3, 17, CANDLE), (11, 2, 16, _st("birch", "north")), (12, 2, 17, "barrel[facing=up,open=false]")]
    elif (pack, kind) == ("Hearthwood", "bees"):
        E = [(8, 2, 5, "cauldron"), (8, 2, 6, "barrel[facing=up,open=false]"), (8, 4, 5, _top("oak")),
             (8, 5, 5, "honey_block"), (8, 4, 6, _top("oak")), (8, 5, 6, CANDLE), (5, 2, 7, _st("oak", "south"))]
    elif (pack, kind) == ("Cascadia", "bees"):
        E = [(5, 2, 11, "barrel[facing=up,open=false]"), (10, 2, 11, "barrel[facing=up,open=false]"),
             (6, 2, 9, _st("spruce", "east")), (5, 2, 9, "brown_carpet"), (5, 2, 8, "brown_carpet"),
             (9, 4, 7, _top("spruce")), (9, 5, 7, "honey_block")]
    elif (pack, kind) == ("Neoterra", "bees"):
        E = [(5, 2, 7, _st("birch", "north")), (6, 2, 7, _st("birch", "north")), (4, 2, 5, "potted_bamboo"),
             (7, 2, 4, "honeycomb_block"), (7, 3, 4, CANDLE)]
    elif (pack, kind) == ("Hearthwood", "horse"):
        nst = d.req["spots"]["stall"]
        x2 = 3 + 6 + 3 * ((nst + 1) // 2)
        E = [(4, 4, 8, HOOK.format("east")), (4, 4, 9, HOOK.format("east")), (4, 4, 10, HOOK.format("east")),
             (4, 2, 10, _st("dark_oak", "west")), (4, 2, 11, _st("dark_oak", "west")),
             (6, 2, 13, "barrel[facing=up,open=false]"), (7, 2, 13, "hay_block[axis=y]"),
             (12, 7, 8, LANT), (x2 - 2, 7, 4, "barrel[facing=up,open=false]"), (x2 - 2, 7, 13, "barrel[facing=up,"
                                                                                               "open=false]")]
    elif (pack, kind) == ("Cascadia", "horse"):
        E = [(6, 4, 4, HOOK.format("south")), (7, 4, 4, HOOK.format("south")), (7, 2, 4, _st("spruce", "north")),
             (13, 2, 7, "barrel[facing=up,open=false]"), (10, 7, 20, LANT)]
    elif (pack, kind) == ("Neoterra", "horse"):
        E = [(7, 2, 5, _top("smooth_stone")), (8, 2, 5, _top("smooth_stone")), (8, 2, 4, _st("birch", "south")),
             (7, 3, 5, "potted_bamboo"), (9, 2, 8, "potted_bamboo"), (5, 2, 6, "light_gray_carpet"),
             (6, 2, 6, "light_gray_carpet"), (4, 7, 5, "potted_azure_bluet"), (9, 7, 5, "barrel[facing=up,"
                                                                                       "open=false]")]
    for x, y, z, b in E:
        if d.bp.inside(x, y, z) and d.air(x, y, z) and not d.air(x, y - 1, z):
            d.set(x, y, z, b)
        elif d.bp.inside(x, y, z) and d.air(x, y, z) and ("hook" in b or y > 3):
            d.set(x, y, z, b)


# Building sizes chosen per type and pack (shed (width, rick), cottage width, hall (width, loft, depth),
# barn (length, depth, silo height)) so that every level has at least 1.5x the blocks of the one before.
SIZES = {
    "bee_cs": ((19, 1), 15, (17, True, 11), (25, 9, 16)), "bee_hw": ((17, 0), 9, (17, True, 11), (23, 9, 16)),
    "bee_nt": ((13, 0), 9, (15, True, 9), (19, 11, 16)), "chicken_cs": ((17, 0), 11, (15, True, 9), (15, 9, 16)),
    "chicken_hw": ((13, 0), 9, (19, True, 9), (21, 9, 16)), "chicken_nt": ((15, 0), 9, (15, True, 9), (21, 9, 16)),
    "cow_cs": ((19, 2), 13, (25, True, 11), (23, 11, 20)), "cow_hw": ((19, 1), 9, (23, True, 13), (23, 11, 20)),
    "cow_nt": ((19, 1), 9, (23, True, 9), (23, 11, 20)), "pig_cs": ((19, 1), 13, (19, True, 9), (21, 9, 16)),
    "pig_hw": ((17, 0), 9, (21, True, 9), (21, 9, 16)), "pig_nt": ((19, 1), 13, (19, True, 11), (23, 11, 20)),
    "rabbit_cs": ((15, 0), 9, (15, False, 9), (11, 9, 16)), "rabbit_hw": ((17, 0), 9, (15, True, 11), (19, 9, 16)),
    "rabbit_nt": ((15, 0), 9, (13, True, 9), (19, 9, 16)), "sheep_cs": ((19, 1), 9, (19, True, 9), (21, 9, 16)),
    "sheep_hw": ((17, 0), 9, (21, True, 9), (21, 9, 16)), "sheep_nt": ((13, 0), 9, (15, True, 9), (21, 9, 16)),
    "stable_cs": ((19, 1), 15, (21, True, 13), (25, 11, 16)),
    "stable_hw": ((19, 1), 15, (23, True, 13), (25, 11, 20)),
    "stable_nt": ((19, 1), 13, (25, True, 11), (25, 11, 20)),
}


def farmstead(core, pack, rel, L, kind):
    d = core(rel, L)
    core_rooms(d, pack, kind, L)
    ex, ez = d.ex, d.ez
    lane = {"Hearthwood": "gravel", "Cascadia": "dirt_path", "Neoterra": "polished_andesite"}[pack]
    sz_shed, sz_cot, sz_hall, sz_barn = SIZES[core.__name__]
    flip = kind in ("cattle", "pig", "bees")                           # hall east / barn west in the south strip
    hall_x = ex + 26 - sz_hall[0] + 1 if flip else 2
    barn_x = 2 if flip else ex - 2
    if L >= 2:
        path(d, ex, 0, ex, ez, lane)
        shed(d, pack, ex + 1, 2, sz_shed[0])
        shed_fit(d, pack, kind, ex + 1, 2, sz_shed[0])
        if sz_shed[1]:
            rick(d, pack, ex + 22, 2, sz_shed[1] == 2)
    if L >= 3:
        cottage(d, pack, ex + 2, 10, sz_cot, kind)
    if L >= 4:
        path(d, 0, ez + 1, d.sx - 1, ez + 1, lane)
        hall(d, pack, kind, hall_x, ez + 2, sz_hall)
    if L >= 5:
        extra(d, pack, kind, ex + 17, 8)
        haybarn(d, pack, barn_x, ez + 2, sz_barn)
    front(d, pack, kind, L)
    recolor(d, RECOLOR[(pack, kind)])
    if L <= 3:
        downgrade(d)
    return d
