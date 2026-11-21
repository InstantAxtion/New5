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
    troughs = [(7, 9), (12, 9), (7, 7)] if z2 == 11 else [(7, 9), (12, 9), (7, 12), (12, 12), (7, 15), (12, 15)]
    for z in range(z1 + 4, z2):
        for mx in (7, 12):
            if (mx, z) in troughs:
                d.item(mx, 2, z, "water_cauldron[level=3]")
            else:
                hay(d, mx, 2, z, "z")
        if (z - z1 - 4) % 3 == 0 and z > z1 + 4:
            for x in (5, 6, 13, 14):
                d.set(x, 2, z, "spruce_fence")
    for z in range(z1 + 5, z2, 3):                                     # stall doors into the pasture
        d.set(x2, 2, z, gate("spruce", "east"))
        d.set(x2, 3, z, AIR)
    d.window(x1, 3, z1 + 5, x1, 3, z1 + 6)
    for z in range(z1 + 2, z2, 4):
        d.lamp(9, 5, z)
        d.lamp(10, 5, z + 2)
    for z in range(z1 + 7, z2, 3):                                     # stall lanterns over the partitions
        hang2(d, 6, z, 4)
        hang2(d, 13, z, 4)
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
    for x in ((3, 7, 11) if L < 3 else (3, 7, 11, 15, 19, 23)):        # pendant lamps over the cubicle rails
        hang2(d, x, bz2 - 2, 4)
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
    for x in range(x1 + 1, 14):
        d.set(x, 2, z2 - 2, "iron_bars" if x % 4 != 0 else gate("birch", "south"))
        if x % 4 == 3:
            for z in range(z1 + 1, z2 - 2):
                if x + 2 < 14:
                    d.set(x + 2, 2, z, "iron_bars")
    for x, z in ((5, z2 - 3), (9, z2 - 3), (13, z2 - 3), (4, z1 + 1), (6, z1 + 1)):     # drinkers
        d.item(x, 2, z, "water_cauldron[level=3]")
    for x in range(x1 + 1, 14, 4):
        d.set(x + 1, 2, z1, gate("birch", "north"))
        d.set(x + 1, 3, z1, AIR)
    for x in range(x1 + 2, 14, 3):
        d.set(x, 5, z2 - 1, "sea_lantern")
    for x in (5, 9):                                                   # heat lamps over the pen rails
        hang2(d, x, z1 + 3, 4)
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
def flowers(d, x1, x2, rows, kinds, ground=GRASS):
    """Planted rows: along each row z in `rows`, from x1 to x2, flowers cycling through `kinds`."""
    for z in rows:
        for x in range(x1, x2 + 1):
            d.set(x, 1, z, ground)
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
    flowers(d, gx1 + 1, 13, (4, 5, 6), ("allium", "lily_of_the_valley", "cornflower"))
    flowers(d, 15, gx2 - 1, (4, 5, 6), ("oxeye_daisy", "poppy", "azure_bluet"))
    flowers(d, gx1 + 1, 13, (9, 13), ("cornflower", "allium", "lily_of_the_valley"))
    flowers(d, 15, gx2 - 1, (9, 13, 15), ("dandelion", "oxeye_daisy", "poppy"))
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
    flowers(d, 2, 20, (mz1 + 2, mz1 + 4, mz1 + 6), ("dandelion", "poppy", "cornflower", "oxeye_daisy",
                                                       "short_grass", "fern"))
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
    flowers(d, mx1 + 1, mx2 - 1, (mz1 + 2, mz1 + 4, mz1 + 7, mz1 + 10, mz1 + 13),
            ("cornflower", "allium", "oxeye_daisy", "azure_bluet", "short_grass"))
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
    flowers(d, 2, 9, (13, 15), ("poppy", "dandelion", "cornflower", "short_grass"))
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
        # further bays (as wide as this shed is): grain sacks two high, seed barrels, a hay bale by the post
        for k, (lo, hi) in ((7, ("white_wool", "brown_wool")), (8, ("barrel[facing=up,open=false]", None)),
                            (10, ("white_wool", "white_wool")), (11, ("hay_block[axis=x]", None)),
                            (13, ("barrel[facing=up,open=false]", "white_wool")), (14, ("brown_wool", None)),
                            (16, ("hay_block[axis=x]", "hay_block[axis=z]")), (17, ("barrel[facing=up,open=false]",
                                                                                    None))):
            if x1 + k < x2:
                d.set(x1 + k, 2, z2 - 1, lo)
                if hi:
                    d.set(x1 + k, 3, z2 - 1, hi)
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
        for x in (x1 + 1, x1 + 6):                                     # planters under the glass band
            d.set(x, 1, z1 - 1, "moss_block")
            d.set(x, 2, z1 - 1, "flowering_azalea")
        for z in range(z1 + 1, z2):
            d.set(x1 + 1, 2, z, "iron_block" if z == z1 + 1 else "white_concrete")
            d.set(x1 + 1, 3, z, "lightning_rod[facing=up,powered=false,waterlogged=false]" if z == z1 + 1 else
                  "iron_trapdoor[facing=east,half=bottom,open=false,powered=false,waterlogged=false]")
        for k, lo, hi in ((2, "light_gray_concrete", "potted_bamboo"), (3, "barrel[facing=north,open=false]", None),
                          (4, "barrel[facing=north,open=false]", None), (5, "light_gray_concrete", None),
                          (7, "barrel[facing=north,open=false]", None), (8, "light_gray_concrete", "potted_bamboo"),
                          (10, "barrel[facing=north,open=false]", None), (11, "barrel[facing=north,open=false]", None),
                          (13, "light_gray_concrete", "potted_azure_bluet"),
                          (14, "barrel[facing=north,open=false]", None)):
            if x1 + k < x2:                                           # tool lockers along the back wall
                d.set(x1 + k, 2, z2 - 1, lo)
                if hi:
                    d.set(x1 + k, 3, z2 - 1, hi)
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
BEDCOL = {"poultry": "yellow", "cattle": "white", "sheep": "light_gray", "pig": "pink", "rabbit": "brown",
          "bees": "orange", "horse": "red"}
TOP = "[type=top,waterlogged=false]"


def shutters(d, x, z, y1, y2, face, wood, span=1, sides="lr"):
    """Open board shutters either side of ONE window: (x, z) is its first column in a wall facing `face`, span
    columns along the wall, rows y1..y2; the shutters hang flat against the outside wall."""
    fx, fz = D4[face]
    ax, az = (1, 0) if fz else (0, 1)
    ks = ([-1] if "l" in sides else []) + ([span] if "r" in sides else [])
    for y in range(y1, y2 + 1):
        for k in ks:
            d.set(x + ax * k + fx, y, z + az * k + fz, trap(wood, face, "bottom", open_=True))


def window_box(d, x, z, y, face, wood, flowers_, span=1):
    """Window box under ONE window whose lowest pane row is y (wall at row z facing `face`): a soil box hung
    on the wall at y-1 with flowers in front of the lower panes and a board front."""
    fx, fz = D4[face]
    ax, az = (1, 0) if fz else (0, 1)
    for k in range(span):
        cx, cz = x + ax * k + fx, z + az * k + fz
        d.set(cx, y - 1, cz, "rooted_dirt")
        d.set(cx, y, cz, flowers_[k % len(flowers_)])
        d.set(cx + fx, y - 1, cz + fz, trap(wood, face, "bottom", open_=True))


def hang2(d, x, z, ybot, kind="lantern"):
    """Lantern at (x, ybot, z) on a chain up to the ceiling right above it."""
    d.set(x, ybot, z, f"{kind}[hanging=true,waterlogged=false]")
    y = ybot + 1
    while y < ybot + 8 and d.bp.inside(x, y, z) and d.air(x, y, z):
        d.set(x, y, z, "chain[axis=y,waterlogged=false]")
        y += 1


# Exterior of the cottage per pack and type: chimney side, porch, door and shutter woods, which windows get
# shutters / window boxes (offsets from the cottage's west wall), garden planting.
COTX = {
    ("Hearthwood", "poultry"): dict(chim="w", porch="hood", door="spruce", shut="spruce", shutg=(2, 6),
                                    shutu=(), boxg=(2, 6), boxu=(), fl=("dandelion", "poppy"), lamp=3,
                                    garden=("dandelion", "oxeye_daisy", "poppy")),
    ("Hearthwood", "cattle"): dict(chim="e", porch="gabled", door="dark_oak", shut="spruce", shutg=(),
                                   shutu=(1, 5), boxg=(), boxu=(1, 5), fl=("lily_of_the_valley", "oxeye_daisy"),
                                   lamp=7, garden=("cornflower", "oxeye_daisy", "lily_of_the_valley")),
    ("Hearthwood", "sheep"): dict(chim="w", porch="pentice", door="oak", shut="birch", shutg=(2, 6), shutu=(),
                                  boxg=(), boxu=(1, 5), fl=("allium", "azure_bluet"), lamp=3,
                                  garden=("allium", "azure_bluet", "cornflower")),
    ("Hearthwood", "pig"): dict(chim="e", porch="hood", door="spruce", shut="mangrove", shutg=(2, 6), shutu=(5,),
                                boxg=(6,), boxu=(), fl=("pink_tulip", "allium"), lamp=3,
                                garden=("pink_tulip", "allium", "poppy")),
    ("Hearthwood", "rabbit"): dict(chim="w", porch="gabled", door="oak", shut="jungle", shutg=(), shutu=(1, 5),
                                   boxg=(), boxu=(1, 5), fl=("dandelion", "cornflower"), lamp=7, garden="carrots"),
    ("Hearthwood", "bees"): dict(chim="e", porch="pentice", door="spruce", shut="oak", shutg=(2, 6), shutu=(),
                                 boxg=(2, 6), boxu=(), fl=("allium", "cornflower"), lamp=7,
                                 garden=("allium", "lily_of_the_valley", "cornflower")),
    ("Hearthwood", "horse"): dict(chim="w", porch="gabled", door="dark_oak", shut="dark_oak", shutg=(10, 12),
                                  shutu=(1, 5), boxg=(10, 12), boxu=(), fl=("red_tulip", "poppy"), lamp=8,
                                  garden=("red_tulip", "poppy", "oxeye_daisy")),
    ("Cascadia", "poultry"): dict(chim="e", porch="stoop", door="spruce", shut="spruce", shutg=(2, 6, 8),
                                  boxg=(2, 6), fl=("dandelion", "red_tulip")),
    ("Cascadia", "cattle"): dict(chim="w", porch="full", door="dark_oak", shut="dark_oak", shutg=(2, 6, 10),
                                 boxg=(), fl=()),
    ("Cascadia", "sheep"): dict(chim="e", porch="deck", door="spruce", shut="birch", shutg=(2, 6), boxg=(),
                                fl=()),
    ("Cascadia", "pig"): dict(chim="e", porch="full", door="spruce", shut="spruce", shutg=(2, 10), boxg=(6,),
                              fl=("pink_tulip", "fern")),
    ("Cascadia", "rabbit"): dict(chim="w", porch="stoop", door="oak", shut="oak", shutg=(2, 6), boxg=(2, 6),
                                 fl=("dandelion", "poppy")),
    ("Cascadia", "bees"): dict(chim="w", porch="full", door="spruce", shut="jungle", shutg=(2, 6, 12),
                               boxg=(12,), fl=("allium", "cornflower")),
    ("Cascadia", "horse"): dict(chim="w", porch="deck", door="dark_oak", shut="dark_oak", shutg=(2, 6, 12),
                                boxg=(), fl=()),
    ("Neoterra", "poultry"): dict(roof="green", glass="light_gray_stained_glass_pane", fins=(1, 7), ledge=(2, 3),
                                  plant=("flowering_azalea", "azalea"), beds=(1, 7)),
    ("Neoterra", "cattle"): dict(roof="solar", glass="glass_pane", fins=(), ledge=(5, 6, 7),
                                 plant=("azalea", "flowering_azalea", "azalea"), beds=(1, 2, 7)),
    ("Neoterra", "sheep"): dict(roof="green", glass="white_stained_glass_pane", fins=(2, 4, 6), ledge=(),
                                plant=(), beds=(7,)),
    ("Neoterra", "pig"): dict(roof="solar", glass="light_gray_stained_glass_pane", fins=(6, 8, 10),
                              ledge=(1, 2, 3), plant=("flowering_azalea", "azalea", "flowering_azalea"),
                              beds=(1, 11)),
    ("Neoterra", "rabbit"): dict(roof="green", glass="lime_stained_glass_pane", fins=(), ledge=(1, 2, 6, 7),
                                 plant=("azalea", "flowering_azalea"), beds=(1, 2, 7)),
    ("Neoterra", "bees"): dict(roof="green", glass="yellow_stained_glass_pane", fins=(1, 3, 5, 7), ledge=(),
                               plant=(), beds=(2, 7)),
    ("Neoterra", "horse"): dict(roof="solar", glass="gray_stained_glass_pane", fins=(2, 4, 8, 10), ledge=(6,),
                                plant=("flowering_azalea",), beds=(1, 11)),
}


def cottage(d, pack, x1, z1, w=9, kind="poultry"):
    """Herder's cottage, w x 8, front door to the north. Shell per pack with the type's own porch, chimney
    side and window dressing; inside the type's own rooms (COTTAGE_ROOMS)."""
    o = COTX[(pack, kind)]
    x2, z2 = x1 + w - 1, z1 + 7
    xm = x1 + 4

    def P(a, y, b, blk):
        d.set(x1 + a, y, z1 + b, blk)

    if pack == "Hearthwood":
        hw_walls(d, x1, z1, x2, z2, 5, floor="oak_planks", infill="bricks", lower=4)
        hw_walls(d, x1, z1, x2, z2, 9, floor="spruce_planks", y0=7, lower=0, post_step=2)
        for x in range(x1, x2 + 1):                                    # jetty bressumer
            d.set(x, 6, z1, "dark_oak_planks")
            d.set(x, 6, z2, "dark_oak_planks")
        ridge = d.gable(x1, z1, x2, z2, 10, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite")
        d.door(xm, 2, z1, "south", o["door"])
        ground = [2, 6] + ([10, 12] if w >= 15 else [])
        upper = [1, 5] + ([9, 12] if w >= 15 else [])
        for a in ground:
            d.window(x1 + a, 3, z1, x1 + a, 4, z1)
            d.window(x1 + a, 3, z2, x1 + a, 4, z2)
        for a in upper:
            d.window(x1 + a, 8, z1, x1 + a + 1, 8, z1)
            d.window(x1 + a, 8, z2, x1 + a + 1, 8, z2)
        side = x2 if o["chim"] == "w" else x1                          # gable-end window opposite the hearth
        d.window(side, 3, z1 + 3, side, 4, z1 + 3)
        hx, hf = (x1 + 1, "east") if o["chim"] == "w" else (x2 - 1, "west")
        d.hearth(hx, 2, z1 + 3, hf, ridge + 2, "bricks", "campfire")
        d.set(hx, ridge + 2, z1 + 3, slab("brick_slab"))
        stairs_up(d, x1 + 3, z2 - 1, 2, 6, "east", "dark_oak_stairs", "dark_oak_planks")
        for x in (x1 + 4, x1 + 5):                                     # stair-well railing upstairs
            d.set(x, 7, z2 - 2, "dark_oak_fence")
        # porch
        if o["porch"] == "hood":
            d.set(xm, 4, z1 - 1, st("deepslate_tile_stairs", "south", "top"))
        elif o["porch"] == "pentice":                                  # lean-to roof along the whole front
            for x in range(x1, x2 + 1):
                d.set(x, 5, z1 - 1, st("deepslate_tile_stairs", "south"))
        else:                                                          # little gabled porch with benches
            for x in (xm - 1, xm, xm + 1):
                for z in (z1 - 2, z1 - 1):
                    d.set(x, 1, z, "stone_bricks")
            for x in (xm - 1, xm + 1):
                d.set(x, 2, z1 - 2, "dark_oak_fence")
                d.set(x, 3, z1 - 2, "dark_oak_fence")
            for z in (z1 - 2, z1 - 1):
                d.set(xm - 1, 4, z, st("deepslate_tile_stairs", "east"))
                d.set(xm + 1, 4, z, st("deepslate_tile_stairs", "west"))
                d.set(xm, 4, z, "dark_oak_planks")
                d.set(xm, 5, z, slab("deepslate_tile_slab"))
            d.chair(xm - 1, 2, z1 - 1, "west", "dark_oak", sit=False)
            d.chair(xm + 1, 2, z1 - 1, "east", "dark_oak", sit=False)
        # window dressing (hand-chosen windows)
        for a in o["shutg"]:
            shutters(d, x1 + a, z1, 3, 4, "north", o["shut"])
        for a in o["shutu"]:
            shutters(d, x1 + a, z1, 8, 8, "north", o["shut"], span=2)
        for a in o["boxg"]:
            window_box(d, x1 + a, z1, 3, "north", o["shut"], o["fl"])
        for a in o["boxu"]:
            window_box(d, x1 + a, z1, 8, "north", o["shut"], o["fl"], span=2)
        # front garden: path, planted strip, lamp, bench on the east side
        if o["porch"] != "gabled":
            path(d, xm, z1 - 2, xm, z1 - 1, "gravel")
        path(d, x1, z1 - 3, x2, z1 - 3, "gravel")                      # garden walk along the front to the lane
        beds = [a for a in (0, 1, w - 2, w - 1) if a not in o["boxg"] and a != o["lamp"]]
        for a in beds:                                                 # corner flower / vegetable beds
            if o["garden"] == "carrots":
                d.set(x1 + a, 1, z1 - 2, "farmland[moisture=7]")
                d.set(x1 + a, 2, z1 - 2, "carrots[age=7]")
            else:
                d.set(x1 + a, 1, z1 - 2, GRASS)
                d.set(x1 + a, 2, z1 - 2, o["garden"][a % len(o["garden"])])
        lamp_post(d, x1 + o["lamp"], z1 - 2, pack)
        if w < 15:
            bench(d, x2 + 1, z1 + 2, "east", "dark_oak", 2, "z")
        d.set(x1 - 1, 2, z2 + 1, "water_cauldron[level=3]")             # rain butt at the back corner
        d.set(x2 + 1, 2, z2 + 1, "oak_log[axis=x]")                    # log pile with a chopping block
        d.set(x2 + 1, 3, z2 + 1, "oak_log[axis=x]")
        d.set(x2 + 1, 2, z2, "stripped_oak_log[axis=y]")
    elif pack == "Cascadia":
        cs_logs(d, x1, z1, x2, z2, 4, log="spruce_log")
        for x in range(x1 + 1, x2):                                    # light stripped logs between dark posts
            for y in (2, 3, 4):
                d.set(x, y, z1, "stripped_spruce_log[axis=x]")
                d.set(x, y, z2, "stripped_spruce_log[axis=x]")
        for z in range(z1 + 1, z2):
            for y in (2, 3, 4):
                d.set(x1, y, z, "stripped_spruce_log[axis=z]")
                d.set(x2, y, z, "stripped_spruce_log[axis=z]")
        ridge = d.gable(x1, z1, x2, z2, 5, "x", "dark_oak_stairs", "dark_oak_slab", "spruce_planks")
        d.door(xm, 2, z1, "south", o["door"])
        front = [2, 6] + ([w - 3] if w >= 11 else [])
        for a in front:
            d.window(x1 + a, 3, z1, x1 + a, 3, z1)
            d.window(x1 + a, 3, z2, x1 + a, 3, z2)
        # porch
        if o["porch"] == "full":
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
        elif o["porch"] == "stoop":
            for x in (xm - 1, xm, xm + 1):
                for z in (z1 - 2, z1 - 1):
                    d.set(x, 1, z, "spruce_planks")
                d.set(x, 5, z1 - 2, st("dark_oak_stairs", "south"))
            for x in (xm - 1, xm + 1):
                for y in (2, 3, 4):
                    d.set(x, y, z1 - 2, "spruce_log[axis=y]")
        else:                                                          # open deck with a rail
            for x in range(x1 - 1, x2 + 2):
                for z in (z1 - 2, z1 - 1):
                    d.set(x, 1, z, "spruce_planks")
                if x != xm:
                    d.set(x, 2, z1 - 2, "spruce_fence")
            for x in (x1 - 1, x2 + 1):
                d.set(x, 2, z1 - 1, "spruce_fence")
                d.set(x, 3, z1 - 2, "lantern[hanging=false,waterlogged=false]")
        # stone fireplace with the chimney stack outside the gable end
        if o["chim"] == "w":
            hx, hf, cx = x1 + 1, "east", x1 - 1
        else:
            hx, hf, cx = x2 - 1, "west", x2 + 1
        d.hearth(hx, 2, z1 + 3, hf, 4, "cobblestone", "campfire")
        wx = x1 if o["chim"] == "w" else x2
        for y in (2, 3, 4):                                            # fire-back through the log wall
            d.set(wx, y, z1 + 3, "cobblestone")
        for y in range(1, ridge + 2):
            d.set(cx, y, z1 + 3, "mossy_cobblestone" if y % 3 == 0 else "cobblestone")
            if y < 5:
                d.set(cx, y, z1 + 2, "cobblestone")
                d.set(cx, y, z1 + 4, "cobblestone")
        d.set(cx, ridge + 2, z1 + 3, slab("cobblestone_slab"))
        for a in o["shutg"]:
            shutters(d, x1 + a, z1, 3, 3, "north", o["shut"])
        for a in o["boxg"]:
            window_box(d, x1 + a, z1, 3, "north", o["shut"], o["fl"])
        if x2 + 3 < d.sx and o["chim"] == "w":
            lamp_post(d, x2 + 2, z1 - 3, pack)
            tree(d, x2 + 2, z2 + 1, "spruce_log", "spruce_leaves", 6, 1)
        if kind in ("poultry", "sheep"):                               # winter woodpile under the west eave
            for z in range(z1 + 1, z2):
                for y in (2, 3, 4):
                    d.set(x1 - 1, y, z, "spruce_log[axis=x]")
            d.set(x1 - 2, 2, z1 + 3, "stripped_spruce_log[axis=y]")    # chopping block
            d.set(x1 - 1, 2, z2 + 1, "water_cauldron[level=3]")         # rain butt and compost bin
            d.set(x1, 2, z2 + 1, "composter[level=4]")
    else:
        nt_walls(d, x1, z1, x2, z2, 5, sides="nse", col_step=4)
        d.fill(x1, 6, z1 - 1, x2, 6, z2, "light_gray_concrete")
        d.box(x1, 7, z1 - 1, x2, 9, z2, "white_concrete")
        for x in range(x1 + 1, x2):
            d.window(x, 7, z1 - 1, x, 8, z1 - 1, o["glass"])
        for z in range(z1, z2):
            d.window(x2, 7, z, x2, 8, z, o["glass"])
        nt_roof(d, x1, z1 - 1, x2, z2, 10, solar_rows=o["roof"] == "solar", green=o["roof"] == "green")
        d.fill(x1, 6, z1 - 1, x2, 6, z1 - 1, "cyan_terracotta")
        d.double_door(xm, 2, z1, "x", "south", "birch")
        stairs_up(d, x1 + 3, z2 - 1, 2, 6, "east", "smooth_quartz_stairs", "white_concrete")
        d.set(x1 + 4, 7, z2 - 2, "glass_pane")
        d.set(x1 + 5, 7, z2 - 2, "glass_pane")
        for a in o["fins"]:                                            # birch sun fins on the upper glazing
            for y in (7, 8):
                d.set(x1 + a, y, z1 - 2, trap("birch", "east", "bottom", open_=True))
        for a, p in zip(o["ledge"], o["plant"] * 4):                   # planter ledges under the upper glazing
            d.set(x1 + a, 6, z1 - 2, "moss_block")
            d.set(x1 + a, 7, z1 - 2, p)
        for a in o["beds"]:                                            # planting beds along the front
            d.set(x1 + a, 1, z1 - 2, "moss_block")
            d.set(x1 + a, 2, z1 - 2, "azalea" if a % 2 else "flowering_azalea")
        path(d, xm, z1 - 2, xm + 1, z1 - 1, "polished_andesite")
    COTTAGE_ROOMS[(pack, kind)](d, P, x1, z1, w, BEDCOL[kind])


def _shelf(d, P, a, b, wd, item, y=4):
    P(a, y, b, slab(f"{wd}_slab", "top"))
    P(a, y + 1, b, item)


CANDLE2 = "candle[candles=2,lit=false,waterlogged=false]"
CANDLE4 = "candle[candles=4,lit=false,waterlogged=false]"
BARREL = "barrel[facing=up,open=false]"
WCAULD = "water_cauldron[level=3]"
MILK = "powder_snow_cauldron[level=3]"
BREW = "brewing_stand[has_bottle_0=true,has_bottle_1=true,has_bottle_2=false]"
PRESS = "piston[extended=false,facing=down]"


def _ch(d, x1, z1, a, y, b, back, wood):
    d.chair(x1 + a, y, z1 + b, back, wood, sit=False)


def _tb(d, x1, z1, a, y, b, wood):
    d.table(x1 + a, y, z1 + b, wood)


# ---- Hearthwood cottages (ground floor y=2, bedroom y=7; stairs along the south wall, a = 3..6)
def cot_hw_poultry(d, P, x1, z1, w, bc):
    wd = "dark_oak"
    P(1, 2, 1, "hay_block[axis=y]")                                   # brooder box by the fire, lid on
    P(1, 3, 1, trap(wd, "north", "bottom"))
    P(5, 2, 1, WCAULD)                                                 # egg-washing sink
    P(6, 2, 1, slab(f"{wd}_slab", "top"))
    P(6, 3, 1, EGGS)                                                   # egg basket
    P(7, 2, 1, BARREL)                                                 # layers' mash
    _shelf(d, P, 5, 1, wd, POT)
    _shelf(d, P, 7, 1, wd, "potted_dandelion")
    P(3, 2, 2, slab(f"{wd}_slab", "top"))                              # fireside: side table and chair
    P(3, 3, 2, CANDLE)
    _ch(d, x1, z1, 3, 2, 3, "east", wd)
    d.rug(x1 + 2, z1 + 2, x1 + 2, z1 + 4, 2, ("yellow_carpet",), "plain")
    _tb(d, x1, z1, 5, 2, 4, wd)                                        # kitchen table for four
    _tb(d, x1, z1, 6, 2, 4, wd)
    for a, b, back in ((5, 3, "north"), (6, 3, "north"), (5, 5, "south"), (6, 5, "south"), (7, 4, "east")):
        _ch(d, x1, z1, a, 2, b, back, wd)
    hang2(d, x1 + 5, z1 + 4, 4)
    P(7, 2, 6, BARREL)
    # bedroom
    d.bed(x1 + 2, 7, z1 + 1, "north", bc)
    d.bed(x1 + 4, 7, z1 + 1, "north", bc)
    P(3, 7, 1, BARREL)
    P(3, 8, 1, CANDLE2)
    P(1, 7, 4, "barrel[facing=east,open=false]")
    P(1, 7, 5, slab(f"{wd}_slab", "top"))                              # feather pillows on the blanket box
    P(1, 8, 5, "white_carpet")
    P(7, 7, 1, "barrel[facing=west,open=false]")
    P(7, 8, 1, "potted_dandelion")
    P(6, 7, 1, slab(f"{wd}_slab", "top"))                              # dressing table
    P(6, 8, 1, "candle[candles=1,lit=false,waterlogged=false]")
    _ch(d, x1, z1, 6, 7, 2, "south", wd)
    d.rug(x1 + 2, z1 + 3, x1 + 5, z1 + 4, 7, ("yellow_carpet", "white_carpet"), "border")
    hang2(d, x1 + 4, z1 + 3, 9)


def cot_hw_cattle(d, P, x1, z1, w, bc):
    wd = "dark_oak"
    P(1, 2, 1, MILK)                                                   # dairy wall: setting pan,
    P(1, 2, 2, slab(f"{wd}_slab", "top"))                              # cheese press,
    P(1, 3, 2, PRESS)
    P(1, 2, 3, BARREL)                                                 # butter churn with dasher,
    P(1, 3, 3, f"{wd}_fence")
    P(1, 2, 4, "cauldron")                                             # whey tub, cheese board
    P(1, 2, 5, slab(f"{wd}_slab", "top"))
    P(1, 3, 5, "cake[bites=0]")
    for b, it in ((1, "yellow_terracotta"), (2, "yellow_terracotta"), (4, "yellow_terracotta"), (5, POT)):
        _shelf(d, P, 1, b, wd, it)                                     # cheese wheels ripening
    P(5, 2, 1, "cauldron")                                             # milk churns by the door
    P(6, 2, 1, BARREL)
    P(6, 3, 1, "potted_red_tulip")
    for a in (4, 5):
        _tb(d, x1, z1, a, 2, 4, wd)
    for a, b, back in ((4, 3, "north"), (5, 3, "north"), (4, 5, "south"), (5, 5, "south"), (3, 4, "west")):
        _ch(d, x1, z1, a, 2, b, back, wd)
    d.rug(x1 + 6, z1 + 2, x1 + 6, z1 + 4, 2, ("white_carpet", "black_carpet"), "check")   # cowhide
    hang2(d, x1 + 4, z1 + 4, 4)
    P(7, 2, 6, BARREL)
    # bedroom (flue on the east side)
    d.bed(x1 + 1, 7, z1 + 2, "west", bc)
    d.bed(x1 + 1, 7, z1 + 4, "west", bc)
    P(1, 7, 3, BARREL)
    P(1, 8, 3, CANDLE2)
    P(4, 7, 1, WCAULD)                                                 # wash stand
    P(5, 7, 1, slab(f"{wd}_slab", "top"))
    P(5, 8, 1, "potted_azure_bluet")
    P(6, 7, 1, "barrel[facing=south,open=false]")
    P(7, 7, 1, "barrel[facing=south,open=false]")
    d.rug(x1 + 3, z1 + 2, x1 + 5, z1 + 4, 7, ("brown_carpet", "white_carpet"), "border")
    hang2(d, x1 + 4, z1 + 3, 9)


def cot_hw_sheep(d, P, x1, z1, w, bc):
    wd = "dark_oak"
    P(3, 2, 2, slab(f"{wd}_slab", "top"))                              # fireside: two chairs, candle table
    P(3, 3, 2, CANDLE)
    _ch(d, x1, z1, 3, 2, 3, "east", wd)
    _ch(d, x1, z1, 3, 2, 4, "east", wd)
    d.rug(x1 + 2, z1 + 2, x1 + 2, z1 + 4, 2, ("white_carpet",), "plain")
    P(6, 2, 1, "loom[facing=south]")                                   # spinning corner
    P(7, 2, 1, "grindstone[face=floor,facing=west]")                   # spinning wheel
    _ch(d, x1, z1, 6, 2, 2, "south", wd)
    _shelf(d, P, 6, 1, wd, "light_gray_carpet")
    _shelf(d, P, 7, 1, wd, "white_carpet")
    P(7, 2, 2, "white_wool")                                           # fleece baskets
    P(7, 3, 2, "white_carpet")
    P(7, 2, 3, BARREL)
    P(7, 2, 4, "light_gray_wool")
    P(7, 3, 4, "light_gray_carpet")
    _tb(d, x1, z1, 5, 2, 4, wd)
    _ch(d, x1, z1, 5, 2, 5, "south", wd)
    _ch(d, x1, z1, 6, 2, 4, "east", wd)
    hang2(d, x1 + 5, z1 + 4, 4)
    P(7, 2, 6, BARREL)
    P(7, 3, 6, "white_carpet")
    # bedroom
    d.bed(x1 + 5, 7, z1 + 1, "north", bc)
    d.bed(x1 + 7, 7, z1 + 1, "north", bc)
    P(6, 7, 1, BARREL)
    P(6, 8, 1, CANDLE2)
    P(1, 7, 1, "barrel[facing=east,open=false]")
    P(1, 7, 5, "white_wool")                                           # yarn basket and knitting chair
    P(1, 8, 5, "white_carpet")
    _ch(d, x1, z1, 2, 7, 5, "west", wd)
    d.rug(x1 + 3, z1 + 2, x1 + 4, z1 + 4, 7, ("light_gray_carpet", "white_carpet"), "check")
    hang2(d, x1 + 4, z1 + 3, 9)


def cot_hw_pig(d, P, x1, z1, w, bc):
    wd = "dark_oak"
    P(1, 2, 1, "smoker[facing=east,lit=true]")                         # smokehouse kitchen
    P(1, 2, 2, "stripped_oak_log[axis=y]")                             # chopping block
    P(1, 3, 2, "oak_pressure_plate[powered=false]")
    P(1, 2, 3, WCAULD)
    P(1, 2, 4, BARREL)                                                 # brine tub, salt barrel
    P(1, 2, 5, BARREL)
    P(1, 3, 5, "potted_red_mushroom")
    _shelf(d, P, 1, 1, wd, POT)
    _shelf(d, P, 1, 3, wd, CANDLE)
    _shelf(d, P, 1, 4, wd, "potted_brown_mushroom")
    P(5, 2, 1, "barrel[facing=north,open=false]")                      # cider keg
    P(6, 2, 1, "composter[level=8]")                                   # swill pail for the pigs
    P(7, 2, 1, "pumpkin")
    for b in (3, 4):
        _tb(d, x1, z1, 5, 2, b, wd)
        _ch(d, x1, z1, 4, 2, b, "west", wd)
        _ch(d, x1, z1, 6, 2, b, "east", wd)
    _ch(d, x1, z1, 5, 2, 5, "south", wd)
    d.rug(x1 + 2, z1 + 2, x1 + 2, z1 + 5, 2, ("brown_carpet",), "plain")
    hang2(d, x1 + 5, z1 + 3, 4)
    P(7, 2, 5, "barrel[facing=west,open=false]")
    P(7, 2, 6, BARREL)
    # bedroom
    d.bed(x1 + 1, 7, z1 + 1, "west", bc)
    d.bed(x1 + 1, 7, z1 + 5, "west", bc)
    P(1, 7, 2, BARREL)
    P(1, 8, 2, CANDLE2)
    P(1, 7, 4, "barrel[facing=east,open=false]")
    P(6, 7, 1, "lectern[facing=south,has_book=false,powered=false]")   # the farm ledger
    P(7, 7, 1, "barrel[facing=south,open=false]")
    d.rug(x1 + 3, z1 + 2, x1 + 5, z1 + 4, 7, ("pink_carpet", "white_carpet"), "border")
    hang2(d, x1 + 4, z1 + 3, 9)


def cot_hw_rabbit(d, P, x1, z1, w, bc):
    wd = "dark_oak"
    P(1, 2, 1, "hay_block[axis=y]")                                   # the house rabbit's basket
    P(1, 3, 1, "brown_carpet")
    P(5, 2, 1, "furnace[facing=south,lit=true]")                       # stew range, sink, peelings
    P(6, 2, 1, WCAULD)
    P(7, 2, 1, "composter[level=4]")
    _shelf(d, P, 5, 1, wd, "potted_dandelion")
    _shelf(d, P, 6, 1, wd, POT)
    P(7, 2, 2, BARREL)                                                 # pantry: root bin, pumpkins
    P(7, 2, 3, "pumpkin")
    P(7, 2, 4, slab(f"{wd}_slab", "top"))
    P(7, 3, 4, "melon")
    _tb(d, x1, z1, 4, 2, 4, wd)
    for a, b, back in ((4, 3, "north"), (5, 4, "east"), (4, 5, "south"), (3, 4, "west")):
        _ch(d, x1, z1, a, 2, b, back, wd)
    d.rug(x1 + 2, z1 + 2, x1 + 3, z1 + 3, 2, ("green_carpet", "lime_carpet"), "check")
    hang2(d, x1 + 4, z1 + 4, 4)
    P(7, 2, 5, "barrel[facing=west,open=false]")
    P(7, 2, 6, BARREL)
    # bedroom
    d.bed(x1 + 5, 7, z1 + 1, "north", bc)
    d.bed(x1 + 7, 7, z1 + 1, "north", bc)
    P(6, 7, 1, BARREL)
    P(6, 8, 1, CANDLE2)
    P(1, 7, 1, slab(f"{wd}_slab", "top"))                              # writing desk
    P(1, 8, 1, CANDLE)
    _ch(d, x1, z1, 2, 7, 1, "east", wd)
    P(1, 7, 4, "bookshelf")
    P(1, 7, 5, slab(f"{wd}_slab", "top"))
    P(1, 8, 5, "potted_fern")
    d.rug(x1 + 3, z1 + 2, x1 + 5, z1 + 4, 7, ("green_carpet", "brown_carpet"), "border")
    hang2(d, x1 + 4, z1 + 3, 9)


def cot_hw_bees(d, P, x1, z1, w, bc):
    wd = "dark_oak"
    P(1, 2, 1, "cauldron")                                             # honey kitchen: settling tank,
    P(1, 2, 2, slab(f"{wd}_slab", "top"))                              # bottling stand,
    P(1, 3, 2, BREW)
    P(1, 2, 3, slab(f"{wd}_slab", "top"))                              # jars,
    P(1, 3, 3, "honey_block")
    P(1, 2, 4, "piston[extended=false,facing=up]")                     # wax press,
    P(1, 2, 5, BARREL)
    for b, it in ((1, "honey_block"), (2, "honey_block"), (3, "honeycomb_block"), (5, CANDLE4)):
        _shelf(d, P, 1, b, wd, it)
    P(5, 2, 1, slab(f"{wd}_slab", "top"))                              # candle-dipping bench
    P(5, 3, 1, CANDLE4)
    P(6, 2, 1, slab(f"{wd}_slab", "top"))
    P(6, 3, 1, CANDLE2)
    _ch(d, x1, z1, 5, 2, 2, "south", wd)
    P(7, 2, 1, WCAULD)                                                 # wax melting pot by the fire
    _tb(d, x1, z1, 4, 2, 4, wd)
    _ch(d, x1, z1, 4, 2, 5, "south", wd)
    _ch(d, x1, z1, 3, 2, 4, "west", wd)
    _ch(d, x1, z1, 4, 2, 3, "north", wd)
    d.rug(x1 + 5, z1 + 3, x1 + 6, z1 + 4, 2, ("orange_carpet", "yellow_carpet"), "check")
    hang2(d, x1 + 4, z1 + 4, 4)
    P(7, 2, 5, "beehive[facing=west,honey_level=0]")                   # a skep in for mending
    P(7, 2, 6, BARREL)
    # bedroom
    d.bed(x1 + 1, 7, z1 + 1, "west", bc)
    d.bed(x1 + 1, 7, z1 + 3, "west", bc)
    P(1, 7, 2, BARREL)
    P(1, 8, 2, CANDLE2)
    P(5, 7, 1, "bookshelf")                                            # reading corner
    P(6, 7, 1, "lectern[facing=south,has_book=false,powered=false]")
    _ch(d, x1, z1, 6, 7, 2, "south", wd)
    P(7, 7, 1, "barrel[facing=south,open=false]")
    d.rug(x1 + 3, z1 + 3, x1 + 5, z1 + 4, 7, ("orange_carpet", "yellow_carpet"), "border")
    hang2(d, x1 + 4, z1 + 3, 9)


def cot_hw_horse(d, P, x1, z1, w, bc):
    wd = "dark_oak"
    for b in range(1, 7):                                              # tack-room partition
        for y in range(2, 6):
            P(8, y, b, "dark_oak_planks")
    d.door(x1 + 8, 2, z1 + 2, "east", wd)
    # living room
    _tb(d, x1, z1, 5, 2, 3, wd)
    for a, b, back in ((5, 2, "north"), (5, 4, "south"), (4, 3, "west"), (6, 3, "east")):
        _ch(d, x1, z1, a, 2, b, back, wd)
    _ch(d, x1, z1, 3, 2, 4, "east", wd)
    P(3, 2, 5, slab(f"{wd}_slab", "top"))
    P(3, 3, 5, CANDLE)
    d.banner(x1 + 7, 4, z1 + 4, "west", "red")                         # show rosettes
    d.banner(x1 + 7, 4, z1 + 5, "west", "blue")
    P(7, 2, 1, "barrel[facing=north,open=false]")
    P(7, 2, 6, BARREL)
    hang2(d, x1 + 5, z1 + 3, 4)
    # tack room
    saddle_rack(d, x1 + 13, z1 + 2, wd)
    saddle_rack(d, x1 + 13, z1 + 4, wd, "red_carpet")
    P(13, 4, 2, HOOK.format("west"))
    P(13, 4, 4, HOOK.format("west"))
    P(13, 4, 3, HOOK.format("west"))
    P(9, 2, 1, "grindstone[face=floor,facing=north]")
    P(10, 2, 1, slab(f"{wd}_slab", "top"))                             # harness bench
    P(10, 3, 1, LANT)
    P(11, 2, 1, "crafting_table")
    _ch(d, x1, z1, 10, 2, 2, "south", wd)
    P(13, 2, 6, "hay_block[axis=x]")
    P(12, 2, 6, BARREL)
    P(11, 2, 6, BARREL)
    P(11, 3, 6, "brown_carpet")
    hang2(d, x1 + 11, z1 + 4, 4)
    # bedroom
    d.bed(x1 + 9, 7, z1 + 1, "north", bc)
    d.bed(x1 + 11, 7, z1 + 1, "north", bc)
    P(10, 7, 1, BARREL)
    P(10, 8, 1, CANDLE2)
    P(13, 7, 1, "barrel[facing=south,open=false]")
    P(13, 7, 2, "barrel[facing=west,open=false]")
    P(1, 7, 1, "bookshelf")
    P(2, 7, 1, "lectern[facing=south,has_book=false,powered=false]")
    _tb(d, x1, z1, 3, 7, 3, wd)                                        # sitting room: card table, armchairs
    _ch(d, x1, z1, 3, 7, 2, "north", wd)
    _ch(d, x1, z1, 3, 7, 4, "south", wd)
    _ch(d, x1, z1, 2, 7, 3, "west", wd)
    P(1, 7, 5, "barrel[facing=east,open=false]")
    P(1, 8, 5, "potted_red_tulip")
    d.rug(x1 + 9, z1 + 3, x1 + 12, z1 + 4, 7, ("red_carpet", "white_carpet"), "border")
    hang2(d, x1 + 10, z1 + 3, 9)
    hang2(d, x1 + 4, z1 + 3, 9)


# ---- Cascadia cabins (one room, y=2; hearth on the chimney side)
def cot_cs_poultry(d, P, x1, z1, w, bc):
    wd = "spruce"
    P(1, 2, 1, BARREL)
    P(2, 2, 1, "furnace[facing=south,lit=true]")
    P(3, 2, 1, WCAULD)
    _shelf(d, P, 1, 1, wd, POT)
    _shelf(d, P, 3, 1, wd, CANDLE)
    P(5, 2, 1, slab(f"{wd}_slab", "top"))                              # egg counter
    P(5, 3, 1, EGGS)
    P(6, 2, 1, slab(f"{wd}_slab", "top"))
    P(6, 3, 1, "potted_dandelion")
    d.bed(x1 + 1, 2, z1 + 4, "west", bc)
    d.bed(x1 + 1, 2, z1 + 6, "west", bc)
    P(1, 2, 5, BARREL)
    P(1, 3, 5, CANDLE2)
    _tb(d, x1, z1, 5, 2, 4, wd)
    for a, b, back in ((5, 3, "north"), (5, 5, "south"), (6, 4, "east"), (4, 4, "west")):
        _ch(d, x1, z1, a, 2, b, back, wd)
    _ch(d, x1, z1, 7, 2, 3, "west", wd)                                # by the fire
    d.rug(x1 + 7, z1 + 2, x1 + 8, z1 + 4, 2, ("yellow_carpet", "brown_carpet"), "check")
    P(9, 2, 1, "hay_block[axis=y]")                                   # brooder box by the fire
    P(9, 3, 1, trap(wd, "north", "bottom"))
    P(8, 2, 1, BARREL)
    P(9, 2, 5, "composter[level=6]")
    P(9, 2, 6, BARREL)
    hang2(d, x1 + 5, z1 + 4, 4)


def cot_cs_cattle(d, P, x1, z1, w, bc):
    wd = "spruce"
    P(11, 2, 1, MILK)                                                  # dairy corner
    P(10, 2, 1, slab(f"{wd}_slab", "top"))
    P(10, 3, 1, PRESS)                                                 # cheese press
    P(9, 2, 1, BARREL)                                                 # churn
    P(9, 3, 1, f"{wd}_fence")
    P(8, 2, 1, slab(f"{wd}_slab", "top"))
    P(8, 3, 1, "cake[bites=0]")
    P(11, 2, 2, "cauldron")
    for a, it in ((9, "yellow_terracotta"), (10, "yellow_terracotta"), (11, POT)):
        _shelf(d, P, a, 1, wd, it)
    d.bed(x1 + 11, 2, z1 + 4, "east", bc)
    d.bed(x1 + 11, 2, z1 + 6, "east", bc)
    P(11, 2, 5, BARREL)
    P(11, 3, 5, CANDLE2)
    _ch(d, x1, z1, 3, 2, 2, "east", wd)                                # fireside
    _ch(d, x1, z1, 3, 2, 4, "east", wd)
    P(3, 2, 3, slab(f"{wd}_slab", "top"))
    P(3, 3, 3, CANDLE)
    d.rug(x1 + 2, z1 + 2, x1 + 2, z1 + 4, 2, ("white_carpet", "black_carpet"), "check")
    for a in (6, 7):
        _tb(d, x1, z1, a, 2, 4, wd)
        _ch(d, x1, z1, a, 2, 3, "north", wd)
        _ch(d, x1, z1, a, 2, 5, "south", wd)
    P(5, 4, 6, HOOK.format("north"))                                   # hat and lasso hooks
    P(6, 4, 6, HOOK.format("north"))
    P(1, 2, 1, BARREL)
    P(1, 2, 6, BARREL)
    P(1, 3, 6, LANT)
    hang2(d, x1 + 6, z1 + 4, 4)


def cot_cs_sheep(d, P, x1, z1, w, bc):
    wd = "spruce"
    P(1, 2, 1, "loom[facing=south]")
    P(2, 2, 1, "grindstone[face=floor,facing=west]")                   # spinning wheel
    _ch(d, x1, z1, 2, 2, 2, "south", wd)
    _shelf(d, P, 1, 1, wd, "white_carpet")
    _shelf(d, P, 2, 1, wd, POT)
    P(1, 2, 3, "white_wool")
    P(1, 3, 3, "white_carpet")
    P(1, 2, 4, "light_gray_wool")
    P(1, 3, 4, "light_gray_carpet")
    d.bed(x1 + 1, 2, z1 + 6, "west", bc)
    d.bed(x1 + 6, 2, z1 + 6, "east", bc)
    P(7, 2, 6, BARREL)
    P(7, 3, 6, CANDLE2)
    _tb(d, x1, z1, 4, 2, 4, wd)
    _ch(d, x1, z1, 3, 2, 4, "west", wd)
    _ch(d, x1, z1, 5, 2, 4, "east", wd)
    _ch(d, x1, z1, 5, 2, 2, "west", wd)                                # by the fire
    d.rug(x1 + 6, z1 + 2, x1 + 6, z1 + 4, 2, ("white_carpet",), "plain")
    P(7, 2, 1, BARREL)
    P(6, 2, 1, "barrel[facing=north,open=false]")
    hang2(d, x1 + 4, z1 + 4, 4)


def cot_cs_pig(d, P, x1, z1, w, bc):
    wd = "spruce"
    P(1, 2, 1, "smoker[facing=south,lit=true]")
    P(2, 2, 1, "stripped_oak_log[axis=y]")                             # chopping block
    P(2, 3, 1, "spruce_pressure_plate[powered=false]")
    P(3, 2, 1, WCAULD)
    P(1, 2, 2, BARREL)
    P(1, 2, 3, BARREL)
    P(1, 3, 3, "potted_red_mushroom")
    _shelf(d, P, 1, 1, wd, POT)
    _shelf(d, P, 3, 1, wd, CANDLE)
    d.bed(x1 + 8, 2, z1 + 6, "south", bc)
    d.bed(x1 + 10, 2, z1 + 6, "south", bc)
    P(9, 2, 6, BARREL)
    P(9, 3, 6, CANDLE2)
    for a in (5, 6):
        _tb(d, x1, z1, a, 2, 4, wd)
        _ch(d, x1, z1, a, 2, 3, "north", wd)
        _ch(d, x1, z1, a, 2, 5, "south", wd)
    _ch(d, x1, z1, 9, 2, 3, "west", wd)                                # by the fire
    P(9, 2, 2, slab(f"{wd}_slab", "top"))
    P(9, 3, 2, CANDLE)
    d.rug(x1 + 10, z1 + 2, x1 + 10, z1 + 4, 2, ("pink_carpet", "brown_carpet"), "check")
    P(11, 2, 1, "composter[level=8]")
    P(10, 2, 1, "barrel[facing=north,open=false]")
    P(11, 2, 6, "pumpkin")
    hang2(d, x1 + 5, z1 + 4, 4)


def cot_cs_rabbit(d, P, x1, z1, w, bc):
    wd = "spruce"
    P(5, 2, 1, "composter[level=4]")
    P(6, 2, 1, WCAULD)
    P(7, 2, 1, "furnace[facing=south,lit=true]")
    _shelf(d, P, 6, 1, wd, "potted_dandelion")
    _shelf(d, P, 7, 1, wd, POT)
    d.bed(x1 + 4, 2, z1 + 6, "south", bc)
    d.bed(x1 + 6, 2, z1 + 6, "south", bc)
    P(5, 2, 6, BARREL)
    P(5, 3, 6, CANDLE2)
    _tb(d, x1, z1, 6, 2, 3, wd)
    _ch(d, x1, z1, 6, 2, 2, "north", wd)
    _ch(d, x1, z1, 7, 2, 3, "east", wd)
    _ch(d, x1, z1, 5, 2, 3, "west", wd)
    _ch(d, x1, z1, 3, 2, 3, "east", wd)                                # by the fire
    d.rug(x1 + 2, z1 + 2, x1 + 2, z1 + 4, 2, ("brown_carpet", "lime_carpet"), "check")
    P(1, 2, 1, "hay_block[axis=y]")                                   # rabbit basket
    P(1, 3, 1, "brown_carpet")
    P(7, 2, 5, BARREL)
    P(1, 2, 6, BARREL)
    P(1, 2, 5, "barrel[facing=east,open=false]")
    hang2(d, x1 + 6, z1 + 3, 4)


def cot_cs_bees(d, P, x1, z1, w, bc):
    wd = "spruce"
    P(13, 2, 1, "cauldron")                                            # honey kitchen
    P(12, 2, 1, slab(f"{wd}_slab", "top"))
    P(12, 3, 1, BREW)
    P(11, 2, 1, slab(f"{wd}_slab", "top"))
    P(11, 3, 1, "honey_block")
    P(13, 2, 2, "piston[extended=false,facing=up]")                    # wax press
    P(13, 2, 3, BARREL)
    for a, it in ((11, "honey_block"), (12, "honeycomb_block"), (13, CANDLE4)):
        _shelf(d, P, a, 1, wd, it)
    P(8, 2, 1, slab(f"{wd}_slab", "top"))                              # candle bench
    P(8, 3, 1, CANDLE4)
    P(9, 2, 1, slab(f"{wd}_slab", "top"))
    P(9, 3, 1, "candle[candles=3,lit=false,waterlogged=false]")
    _ch(d, x1, z1, 8, 2, 2, "south", wd)
    d.bed(x1 + 2, 2, z1 + 6, "south", bc)
    d.bed(x1 + 4, 2, z1 + 6, "south", bc)
    P(3, 2, 6, BARREL)
    P(3, 3, 6, CANDLE2)
    for b in (4, 5):
        _tb(d, x1, z1, 10, 2, b, wd)
        _ch(d, x1, z1, 9, 2, b, "west", wd)
        _ch(d, x1, z1, 11, 2, b, "east", wd)
    _ch(d, x1, z1, 3, 2, 2, "east", wd)                                # by the fire
    P(3, 2, 3, slab(f"{wd}_slab", "top"))
    P(3, 3, 3, CANDLE)
    d.rug(x1 + 2, z1 + 2, x1 + 2, z1 + 4, 2, ("orange_carpet",), "plain")
    P(13, 2, 6, "beehive[facing=west,honey_level=0]")                  # skeps in for the winter
    P(12, 2, 6, "beehive[facing=north,honey_level=0]")
    P(13, 2, 5, BARREL)
    hang2(d, x1 + 10, z1 + 4, 4)
    hang2(d, x1 + 4, z1 + 3, 4)


def cot_cs_horse(d, P, x1, z1, w, bc):
    wd = "spruce"
    saddle_rack(d, x1 + 13, z1 + 2, wd)                               # tack corner
    saddle_rack(d, x1 + 13, z1 + 4, wd, "red_carpet")
    P(13, 4, 3, HOOK.format("west"))
    P(13, 4, 5, HOOK.format("west"))
    P(13, 2, 1, BARREL)
    P(13, 2, 6, "hay_block[axis=x]")
    P(12, 2, 6, BARREL)
    P(11, 2, 6, "grindstone[face=floor,facing=north]")
    d.bed(x1 + 5, 2, z1 + 6, "south", bc)
    d.bed(x1 + 7, 2, z1 + 6, "south", bc)
    P(6, 2, 6, BARREL)
    P(6, 3, 6, CANDLE2)
    _tb(d, x1, z1, 9, 2, 3, wd)
    for a, b, back in ((9, 2, "north"), (10, 3, "east"), (8, 3, "west"), (9, 4, "south")):
        _ch(d, x1, z1, a, 2, b, back, wd)
    _ch(d, x1, z1, 3, 2, 2, "east", wd)                                # by the fire
    _ch(d, x1, z1, 3, 2, 4, "east", wd)
    P(3, 2, 3, slab(f"{wd}_slab", "top"))
    P(3, 3, 3, CANDLE)
    d.rug(x1 + 2, z1 + 2, x1 + 2, z1 + 4, 2, ("red_carpet",), "plain")
    P(1, 2, 1, "barrel[facing=north,open=false]")
    for a in (1, 2):                                                   # deck: bench, boot barrel, saddle on the rail
        _ch(d, x1, z1, a, 2, -1, "south", wd)
    P(3, 2, -1, BARREL)
    P(8, 2, -1, LANT)
    P(11, 2, -1, "hay_block[axis=x]")
    P(8, 3, -2, "brown_carpet")
    d.banner(x1 + 6, 4, z1 + 1, "south", "red")                        # rodeo pennants over the door wall
    d.banner(x1 + 2, 4, z1 + 1, "south", "yellow")
    hang2(d, x1 + 9, z1 + 3, 4)
    hang2(d, x1 + 4, z1 + 3, 4)


# ---- Neoterra houses (open-plan ground floor y=2 with the kitchen on the closed west wall; bedroom y=7)
QZ = "smooth_quartz"
QT = "smooth_quartz_slab[type=top,waterlogged=false]"
CAB = "light_gray_stained_glass"


def _nt_light(d, x1, z1, cells):
    for a, y, b in cells:
        d.set(x1 + a, y, z1 + b, "sea_lantern")


def cot_nt_poultry(d, P, x1, z1, w, bc):
    for b, blk, top in ((1, QZ, "potted_bamboo"), (2, WCAULD, None), (3, "smoker[facing=east,lit=false]", None),
                        (4, QZ, EGGS), (5, "barrel[facing=east,open=false]", None)):
        P(1, 2, b, blk)
        if top:
            P(1, 3, b, top)
        P(1, 4, b, CAB)
    P(3, 2, 3, QZ)                                                     # island with two stools
    P(3, 2, 4, QZ)
    _ch(d, x1, z1, 4, 2, 3, "east", "birch")
    _ch(d, x1, z1, 4, 2, 4, "east", "birch")
    _ch(d, x1, z1, 7, 2, 2, "east", "mangrove")                        # sofa against the glass
    _ch(d, x1, z1, 7, 2, 3, "east", "mangrove")
    P(6, 2, 3, slab("smooth_quartz_slab"))
    d.rug(x1 + 5, z1 + 2, x1 + 6, z1 + 4, 2, ("yellow_carpet", "light_gray_carpet"), "check")
    P(7, 2, 4, "potted_dandelion")
    P(7, 2, 6, "barrel[facing=up,open=false]")
    _nt_light(d, x1, z1, ((3, 6, 3), (6, 6, 3)))
    d.bed(x1 + 2, 7, z1, "north", bc)
    d.bed(x1 + 4, 7, z1, "north", bc)
    P(3, 7, 0, "white_concrete")
    P(3, 8, 0, "potted_bamboo")
    P(7, 7, 2, QZ)                                                     # desk
    P(7, 8, 2, CANDLE2)
    _ch(d, x1, z1, 6, 7, 2, "west", "birch")
    P(1, 7, 4, "barrel[facing=east,open=false]")
    P(1, 7, 5, "barrel[facing=east,open=false]")
    d.rug(x1 + 2, z1 + 2, x1 + 5, z1 + 4, 7, ("yellow_carpet",), "plain")
    _nt_light(d, x1, z1, ((3, 10, 3), (6, 10, 4)))


def cot_nt_cattle(d, P, x1, z1, w, bc):
    for b, blk, top in ((1, "white_concrete", "cake[bites=0]"), (2, WCAULD, None),
                        (3, "smoker[facing=east,lit=false]", None), (4, QT, PRESS), (5, MILK, None)):
        P(1, 2, b, blk)
        if top:
            P(1, 3, b, top)
        P(1, 4, b, CAB)
    for a in (4, 5):                                                   # dining table
        d.table(x1 + a, 2, z1 + 3, "birch", kind="slab", top="smooth_quartz_slab")
        _ch(d, x1, z1, a, 2, 4, "south", "birch")
    _ch(d, x1, z1, 3, 2, 3, "west", "birch")
    _ch(d, x1, z1, 6, 2, 3, "east", "birch")
    _ch(d, x1, z1, 7, 2, 4, "east", "mangrove")                        # reading seat
    _ch(d, x1, z1, 7, 2, 5, "east", "mangrove")
    d.rug(x1 + 6, z1 + 4, x1 + 6, z1 + 5, 2, ("lime_carpet",), "plain")
    P(7, 2, 1, "potted_bamboo")
    P(7, 2, 6, "barrel[facing=up,open=false]")
    _nt_light(d, x1, z1, ((4, 6, 3), (7, 6, 4)))
    d.bed(x1 + 1, 7, z1 + 1, "west", bc)
    d.bed(x1 + 1, 7, z1 + 3, "west", bc)
    P(1, 7, 2, "white_concrete")
    P(1, 8, 2, CANDLE2)
    P(6, 7, 0, WCAULD)                                                 # soaking tub by the window
    P(7, 7, 0, WCAULD)
    P(7, 7, 2, "white_concrete")
    P(7, 8, 2, "potted_azure_bluet")
    P(1, 7, 5, "barrel[facing=east,open=false]")
    d.rug(x1 + 3, z1 + 2, x1 + 5, z1 + 4, 7, ("lime_carpet", "white_carpet"), "border")
    _nt_light(d, x1, z1, ((4, 10, 3),))


def cot_nt_sheep(d, P, x1, z1, w, bc):
    P(1, 2, 1, "barrel[facing=east,open=false]")                       # wool store
    P(1, 2, 2, "barrel[facing=east,open=false]")
    for b, blk, top in ((3, "smoker[facing=east,lit=false]", None), (4, WCAULD, None), (5, QZ, "potted_bamboo")):
        P(1, 2, b, blk)
        if top:
            P(1, 3, b, top)
        P(1, 4, b, CAB)
    P(7, 2, 1, "loom[facing=west]")                                    # weaving studio by the glass
    _ch(d, x1, z1, 6, 2, 1, "west", "birch")
    P(7, 2, 2, "white_wool")
    P(7, 3, 2, "white_carpet")
    P(7, 2, 3, "light_gray_wool")
    P(7, 3, 3, "magenta_carpet")
    d.table(x1 + 3, 2, z1 + 3, "birch", kind="slab", top="smooth_quartz_slab")
    _ch(d, x1, z1, 3, 2, 2, "north", "birch")
    _ch(d, x1, z1, 3, 2, 4, "south", "birch")
    d.rug(x1 + 5, z1 + 3, x1 + 6, z1 + 5, 2, ("magenta_carpet", "white_carpet"), "check")
    P(7, 2, 6, "barrel[facing=up,open=false]")
    _nt_light(d, x1, z1, ((3, 6, 3), (6, 6, 2)))
    d.bed(x1 + 5, 7, z1, "north", bc)
    d.bed(x1 + 7, 7, z1, "north", bc)
    P(6, 7, 0, "white_concrete")
    P(6, 8, 0, CANDLE2)
    P(1, 7, 0, "barrel[facing=east,open=false]")
    _ch(d, x1, z1, 1, 7, 1, "west", "mangrove")                        # knitting chair and yarn basket
    P(1, 7, 2, "white_wool")
    P(1, 8, 2, "white_carpet")
    d.rug(x1 + 2, z1 + 2, x1 + 5, z1 + 4, 7, ("light_gray_carpet", "white_carpet"), "border")
    _nt_light(d, x1, z1, ((3, 10, 3), (6, 10, 2)))


def cot_nt_pig(d, P, x1, z1, w, bc):
    for b, blk, top in ((1, "smoker[facing=east,lit=false]", None), (2, QZ, "birch_pressure_plate[powered=false]"),
                        (3, WCAULD, None), (4, "barrel[facing=east,open=false]", None),
                        (5, "barrel[facing=east,open=false]", None)):
        P(1, 2, b, blk)
        if top:
            P(1, 3, b, top)
        P(1, 4, b, CAB)
    d.table(x1 + 5, 2, z1 + 3, "birch", kind="slab", top="smooth_quartz_slab")
    _ch(d, x1, z1, 5, 2, 4, "south", "birch")
    _ch(d, x1, z1, 6, 2, 3, "east", "birch")
    for a in (8, 9, 10):                                               # breakfast bar
        P(a, 2, 3, QZ)
        _ch(d, x1, z1, a, 2, 4, "south", "birch")
    _ch(d, x1, z1, 11, 2, 5, "east", "mangrove")                       # lounge
    _ch(d, x1, z1, 11, 2, 6, "east", "mangrove")
    P(10, 2, 5, slab("smooth_quartz_slab"))
    d.rug(x1 + 9, z1 + 5, x1 + 10, z1 + 6, 2, ("pink_carpet", "white_carpet"), "check")
    P(11, 2, 1, "potted_bamboo")
    P(7, 2, 6, "barrel[facing=up,open=false]")
    _nt_light(d, x1, z1, ((5, 6, 3), (9, 6, 3), (10, 6, 5)))
    d.bed(x1 + 11, 7, z1 + 1, "east", bc)
    d.bed(x1 + 11, 7, z1 + 3, "east", bc)
    P(11, 7, 2, "white_concrete")
    P(11, 8, 2, CANDLE2)
    P(2, 7, 1, QZ)                                                     # office desk
    P(2, 8, 1, CANDLE)
    _ch(d, x1, z1, 2, 7, 2, "south", "birch")
    P(1, 7, 0, "bookshelf")
    P(3, 7, 0, "barrel[facing=south,open=false]")
    d.rug(x1 + 5, z1 + 2, x1 + 8, z1 + 4, 7, ("pink_carpet", "light_gray_carpet"), "border")
    _nt_light(d, x1, z1, ((3, 10, 2), (7, 10, 3), (10, 10, 2)))


def cot_nt_rabbit(d, P, x1, z1, w, bc):
    for b, blk, top in ((1, WCAULD, None), (2, "smoker[facing=east,lit=false]", None), (3, QZ, "potted_dandelion"),
                        (4, "composter[level=5]", None), (5, "barrel[facing=east,open=false]", None)):
        P(1, 2, b, blk)
        if top:
            P(1, 3, b, top)
        if b != 4:
            P(1, 4, b, CAB)
    for b, p in ((1, "fern"), (2, "azalea"), (3, "fern")):            # herb planters along the glass
        P(7, 2, b, "moss_block")
        P(7, 3, b, p)
    P(6, 2, 1, "hay_block[axis=y]")                                   # rabbit basket
    P(6, 3, 1, "brown_carpet")
    d.table(x1 + 4, 2, z1 + 4, "birch", kind="slab", top="smooth_quartz_slab")
    for a, b, back in ((4, 3, "north"), (4, 5, "south"), (5, 4, "east"), (3, 4, "west")):
        _ch(d, x1, z1, a, 2, b, back, "birch")
    P(7, 2, 6, "barrel[facing=up,open=false]")
    _nt_light(d, x1, z1, ((4, 6, 4), (6, 6, 2)))
    d.bed(x1 + 1, 7, z1, "north", bc)
    d.bed(x1 + 3, 7, z1, "north", bc)
    P(2, 7, 0, "white_concrete")
    P(2, 8, 0, CANDLE2)
    P(7, 7, 2, QZ)                                                     # desk
    P(7, 8, 2, "potted_fern")
    _ch(d, x1, z1, 6, 7, 2, "west", "birch")
    d.rug(x1 + 2, z1 + 3, x1 + 5, z1 + 4, 7, ("pink_carpet", "white_carpet"), "check")
    _nt_light(d, x1, z1, ((3, 10, 3),))


def cot_nt_bees(d, P, x1, z1, w, bc):
    for b, blk, top in ((1, "cauldron", None), (2, QT, BREW), (3, "smoker[facing=east,lit=false]", None),
                        (4, WCAULD, None), (5, "barrel[facing=east,open=false]", None)):
        P(1, 2, b, blk)
        if top:
            P(1, 3, b, top)
    for b in (1, 3, 5):                                                # honey jar shelves
        P(1, 4, b, QT)
        P(1, 5, b, "honey_block")
    P(7, 2, 1, QT)                                                     # candle bar
    P(7, 3, 1, CANDLE4)
    P(7, 2, 2, QT)
    P(7, 3, 2, CANDLE2)
    _ch(d, x1, z1, 6, 2, 1, "west", "birch")
    _ch(d, x1, z1, 6, 2, 2, "west", "birch")
    P(7, 2, 3, "honeycomb_block")
    d.table(x1 + 3, 2, z1 + 4, "birch", kind="slab", top="smooth_quartz_slab")
    _ch(d, x1, z1, 3, 2, 5, "south", "birch")
    _ch(d, x1, z1, 4, 2, 4, "east", "birch")
    P(7, 2, 6, "barrel[facing=up,open=false]")
    _nt_light(d, x1, z1, ((3, 6, 4), (6, 6, 2)))
    d.bed(x1 + 7, 7, z1 + 1, "east", bc)
    d.bed(x1 + 7, 7, z1 + 3, "east", bc)
    P(7, 7, 2, "white_concrete")
    P(7, 8, 2, CANDLE2)
    P(1, 7, 0, "bookshelf")
    P(1, 7, 1, "lectern[facing=east,has_book=false,powered=false]")
    d.rug(x1 + 2, z1 + 2, x1 + 4, z1 + 4, 7, ("yellow_carpet", "white_carpet"), "border")
    _nt_light(d, x1, z1, ((3, 10, 3),))


def cot_nt_horse(d, P, x1, z1, w, bc):
    for b, blk, top in ((1, "smoker[facing=east,lit=false]", None), (2, WCAULD, None), (3, QZ, "potted_bamboo"),
                        (4, "barrel[facing=east,open=false]", None)):
        P(1, 2, b, blk)
        if top:
            P(1, 3, b, top)
        P(1, 4, b, CAB)
    saddle_rack(d, x1 + 11, z1 + 1, "birch")                          # tack wall
    saddle_rack(d, x1 + 11, z1 + 2, "birch", "red_carpet")
    P(11, 2, 3, "hay_block[axis=z]")
    P(11, 2, 4, "barrel[facing=west,open=false]")
    _ch(d, x1, z1, 8, 2, 5, "south", "mangrove")                       # lounge
    _ch(d, x1, z1, 9, 2, 5, "south", "mangrove")
    P(8, 2, 3, slab("smooth_quartz_slab"))
    P(9, 2, 3, slab("smooth_quartz_slab"))
    d.rug(x1 + 8, z1 + 4, x1 + 9, z1 + 4, 2, ("red_carpet",), "plain")
    d.table(x1 + 5, 2, z1 + 3, "birch", kind="slab", top="smooth_quartz_slab")
    _ch(d, x1, z1, 5, 2, 4, "south", "birch")
    _ch(d, x1, z1, 6, 2, 3, "east", "birch")
    P(7, 2, 6, "barrel[facing=up,open=false]")
    _nt_light(d, x1, z1, ((5, 6, 3), (9, 6, 4)))
    d.bed(x1 + 9, 7, z1, "north", bc)
    d.bed(x1 + 11, 7, z1, "north", bc)
    P(10, 7, 0, "white_concrete")
    P(10, 8, 0, CANDLE2)
    P(1, 7, 0, "barrel[facing=east,open=false]")
    P(2, 7, 0, QZ)
    P(2, 8, 0, CANDLE)
    _ch(d, x1, z1, 2, 7, 1, "south", "birch")
    d.rug(x1 + 4, z1 + 2, x1 + 8, z1 + 4, 7, ("red_carpet", "light_gray_carpet"), "border")
    _ch(d, x1, z1, 4, 7, 2, "west", "mangrove")                        # reading corner on the rug
    P(4, 7, 3, "barrel[facing=up,open=false]")
    P(4, 8, 3, "potted_fern")
    _nt_light(d, x1, z1, ((4, 10, 3), (9, 10, 2)))


COTTAGE_ROOMS = {(p, k): globals()[f"cot_{s}_{k}"] for p, s in (("Hearthwood", "hw"), ("Cascadia", "cs"),
                                                                    ("Neoterra", "nt"))
                 for k in ("poultry", "cattle", "sheep", "pig", "rabbit", "bees", "horse")}


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
    dx = {"Hearthwood": xm, "Cascadia": x2 - 3, "Neoterra": x1 + 2}[pack]
    d.double_door(dx, 2, z1, "x", "south", wood)
    front = [x for x in range(x1 + 2, x2 - 1, 3) if x < dx - 2 or x > dx + 3]
    if pack != "Neoterra":
        for x in front:
            d.window(x, 3, z1, x, 4, z1)
            shutters(d, x, z1, 3, 4, "north", wood)                    # shutters on every street window
        for x in range(x1 + 2, x2 - 1, 3):
            d.window(x, 3, z2, x, 4, z2)
        boxed = ([x for x in front if x < dx][-1:] + [x for x in front if x > dx][:1]) if pack == "Hearthwood" \
            else front[:1]
        for x in boxed:                                                # window boxes by the doors
            window_box(d, x, z1, 3, "north", wood, ("poppy", "oxeye_daisy") if pack == "Hearthwood" else
                       ("fern", "dandelion"))
    else:
        for a in (5, 7, w - 4):                                        # planters at the foot of the glass
            d.set(x1 + a, 1, z1 - 1, "moss_block")
            d.set(x1 + a, 2, z1 - 1, "flowering_azalea" if a == 7 else "azalea")
    d.window(x1, 3, zc, x1, 4, zc)
    d.window(x2, 3, zc, x2, 4, zc)
    if pack == "Cascadia":
        hall_cs(d, kind, x1, z1, x2, z2, loft)
    elif pack == "Neoterra":
        hall_nt(d, kind, x1, z1, x2, z2, loft)
    else:
        _hall_hw_rooms(d, pack, kind, x1, z1, x2, z2, xm, zc, wood, loft, top, ytop, ylamp)
    lamp_post(d, dx - 1, z1 - 1, pack)
    d.sign(dx + 2 if pack != "Neoterra" else x1 + 6, 4, z1 - 1, "north",
           {"poultry": ["Laying", "House"], "cattle": ["Calf", "House"],
                                         "sheep": ["Lambing", "Shed"], "pig": ["Farrowing", "House"],
                                         "rabbit": ["Hutch", "House"], "bees": ["Honey &", "Candles"],
                                         "horse": ["Riding", "School"]}[kind], wood,
           glow=pack == "Neoterra", color="cyan" if pack == "Neoterra" else "black")


def _hall_hw_rooms(d, pack, kind, x1, z1, x2, z2, xm, zc, wood, loft, top, ytop, ylamp):
    """Hearthwood hall: pens / work rows along both long walls with a central aisle, ladder at the west end."""
    w = x2 - x1 + 1
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
                    hang2(d, x, zf, 4)                                 # stall lantern over the partition
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
    elif kind == "bees":                                               # honey extraction & candle workshop
        tb = slab(f"{wood}_slab", "top")
        for x, z, blk, top_ in (
                (x1 + 1, z1 + 1, "water_cauldron[level=3]", None),             # washing tub
                (x1 + 2, z1 + 1, tb, "brewing_stand[has_bottle_0=true,has_bottle_1=true,has_bottle_2=false]"),
                (x1 + 3, z1 + 1, tb, "honey_block"),                             # bottling bench
                (x1 + 4, z1 + 1, "barrel[facing=up,open=false]", None),
                (x1 + 4, zc, tb, "candle[candles=4,lit=false,waterlogged=false]"),   # candle table
                (x1 + 5, zc, tb, "candle[candles=2,lit=false,waterlogged=false]"),
                (x1 + 2, z2 - 1, tb, "beehive[facing=north,honey_level=0]"),     # skeps wintering on a bench
                (x1 + 3, z2 - 1, tb, None),
                (x1 + 4, z2 - 1, tb, "beehive[facing=north,honey_level=0]"),
                (x1 + 5, z2 - 1, tb, None),
                (x1 + 6, z2 - 1, tb, "beehive[facing=north,honey_level=0]"),
                (x2 - 3, z2 - 1, "piston[extended=false,facing=up]", None),       # wax press and melt pot
                (x2 - 2, z2 - 1, "water_cauldron[level=3]", None),
                (x2 - 1, z1 + 1, "barrel[facing=up,open=false]", "honeycomb_block"),  # store bay
                (x2 - 1, z1 + 2, "barrel[facing=up,open=false]", "honey_block"),
                (x2 - 2, z1 + 1, "honeycomb_block", None),
                (xm + 3, z1 + 1, tb, "honey_block"),                             # sales counter by the door
                (xm + 4, z1 + 1, tb, "candle[candles=3,lit=false,waterlogged=false]")):
            d.set(x, 2, z, blk)
            if top_:
                d.set(x, 3, z, top_)
        d.chair(x1 + 4, 2, zc + 1, "south", wood, sit=False)
        d.chair(x1 + 5, 2, zc + 1, "south", wood, sit=False)
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
    for x in (x1 + 3, xm + 2, x2 - 3):                                # three lights down the aisle
        if pack == "Neoterra":
            d.set(x, 5, zc + 1, "sea_lantern")
        elif loft and kind != "horse":
            hang(d, x, 5, zc + 1, 4)
        else:
            hang(d, x, ytop, zc, ylamp - 1 if kind != "horse" else ylamp + top - 5)


def hall_cs(d, kind, x1, z1, x2, z2, loft):
    """Cascadia livestock hall: a feed alley along the north wall, ONE row of pens (or the work line) along the
    south side, an end bay with the loft ladder at the west end; the doors sit at the east end of the front."""
    wd = "spruce"
    w, dep = x2 - x1 + 1, z2 - z1 + 1
    E, B, bc = w - 2, dep - 2, dep // 2

    def P(a, y, b, blk):
        d.set(x1 + a, y, z1 + b, blk)

    TS = slab(f"{wd}_slab", "top")
    lad = 1
    if kind in ("cattle", "sheep", "pig"):
        manger, trough = {"cattle": ("hay_block[axis=z]", WCAULD), "sheep": ("hay_block[axis=y]", WCAULD),
                          "pig": (WCAULD, "composter[level=7]")}[kind]
        for a in range(3, E + 1):                                      # feed fence between alley and pens
            P(a, 2, 3, f"{wd}_fence")
        for a0 in range(3, E, 4):                                      # pens 3 wide: manger, gate, trough
            for b in range(4, B + 1):
                P(a0, 2, b, f"{wd}_planks" if kind == "pig" else f"{wd}_fence")
            if a0 > 3:
                hang2(d, x1 + a0, z1 + B - 1, 4)                       # stall lantern over the partition
            for k, blk in ((1, manger), (2, gate(wd, "north")), (3, trough)):
                if a0 + k <= E:
                    P(a0 + k, 2, 3, blk)
        for a in range(4, E + 1):
            for b in range(4, B + 1):
                if (a - 3) % 4:
                    P(a, 1, b, {"pig": "mud", "cattle": "coarse_dirt", "sheep": "spruce_planks"}[kind])
        for a, blk in {"cattle": ((4, "cauldron"), (5, "cauldron"), (6, BARREL)),
                       "sheep": ((4, "white_wool"), (5, "light_gray_wool"), (6, "loom[facing=south]")),
                       "pig": ((4, "composter[level=8]"), (5, BARREL), (6, "pumpkin"))}[kind]:
            P(a, 2, 1, blk)                                            # alley store along the north wall
        P(1, 2, 1, "hay_block[axis=y]")                               # end bay: hay, feed barrel, fork rack
        P(1, 3, 1, "hay_block[axis=y]")
        P(2, 2, 1, BARREL)
        P(1, 2, B, BARREL)
        P(2, 2, B, "hay_block[axis=x]")
    elif kind == "poultry":                                            # deep-litter house
        for a in range(3, E + 1):                                      # nest boxes along the south wall
            P(a, 2, B, "hay_block[axis=x]")
            P(a, 3, B, trap(wd, "north", "top"))
            P(a, 4, B, "hay_block[axis=x]")
        for a0 in range(4, E - 2, 4):                                  # roosting perches
            P(a0, 2, B - 2, f"{wd}_fence")
            P(a0 + 2, 2, B - 2, f"{wd}_fence")
            for k in range(3):
                P(a0 + k, 3, B - 2, slab(f"{wd}_slab"))
        for a in range(3, E - 3, 3):                                   # feeders and drinkers on the north wall
            P(a, 2, 1, "composter[level=6]")
            P(a + 1, 2, 1, WCAULD)
        for a in range(1, E + 1):
            for b in range(1, B):
                if d.air(x1 + a, 2, z1 + b):
                    P(a, 1, b, "coarse_dirt")
    elif kind == "rabbit":                                             # hutch walls at both ends, a grass run
        hutch_col(d, x1 + 1, z1 + 1, z2 - 1, 2, wd, "east", 2)
        hutch_col(d, x2 - 1, z1 + 3, z2 - 1, 2, wd, "west", 2)
        pen(d, x1 + 4, z1 + 3, x2 - 4, z2 - 2, f"{wd}_fence", gates=((x1 + w // 2, z1 + 3),))
        P(5, 2, 4, "hay_block[axis=y]")
        P(E - 4, 2, B - 2, WCAULD)
        P(3, 2, 1, BARREL)
        P(4, 2, 1, "composter[level=4]")
        lad = None
    elif kind == "bees":                                               # honey house
        for b in range(1, B - 1):                                      # skeps wintering on the west shelves
            P(1, 2, b, "beehive[facing=east,honey_level=0]")
            P(1, 3, b, TS)
            P(1, 4, b, "beehive[facing=east,honey_level=0]")
        for a, blk, top_ in ((1, WCAULD, None), (2, TS, BREW), (3, TS, "honey_block"),
                             (4, "piston[extended=false,facing=up]", None), (5, "cauldron", None),
                             (6, TS, "honey_block"), (7, BARREL, None), (8, TS, "honeycomb_block")):
            P(a, 2, B, blk)                                            # extraction line on the south wall
            if top_:
                P(a, 3, B, top_)
        for a in (5, 6, 7):                                            # candle-dipping table
            P(a, 2, bc, TS)
            _ch(d, x1, z1, a, 2, bc + 1, "south", wd)
        P(5, 3, bc, CANDLE4)
        P(7, 3, bc, CANDLE2)
        for b, top_ in ((2, "honey_block"), (3, CANDLE)):              # sales counter by the doors
            P(E, 2, b, TS)
            P(E, 3, b, top_)
        P(E, 2, B, BARREL)
        P(E - 1, 2, B, BARREL)
        lad = E
    else:                                                              # riding school, gallery at the west end
        for a in range(1, E + 1):
            for b in range(1, B + 1):
                P(a, 1, b, "sand")
        for b in range(1, B + 1):
            P(1, 6, b, f"{wd}_planks")
            P(2, 6, b, f"{wd}_planks")
            P(3, 6, b, TS)
            P(3, 7, b, f"{wd}_fence")
            if b % 2 and b != B:
                P(1, 7, b, st(f"{wd}_stairs", "west"))
            P(4, 2, b, f"{wd}_fence" if b != bc else AIR)
        for b in (1, B):
            for y in range(2, 6):
                P(3, y, b, f"{wd}_fence")
        for y in range(2, 8):
            P(1, y, B, "ladder[facing=east,waterlogged=false]")
        P(3, 7, B - 1, AIR)
        for a, b in ((8, bc - 2), (8, bc + 2), (E - 3, bc)):           # barrel-racing pattern
            P(a, 2, b, BARREL)
        ja = (E + 8) // 2                                              # a jump across the long side
        P(ja, 2, bc - 1, f"{wd}_fence")
        P(ja, 2, bc, trap(wd, "north", "top"))
        P(ja, 2, bc + 1, f"{wd}_fence")
        P(ja, 3, bc - 1, "white_wool")
        P(ja, 3, bc + 1, "red_wool")
        P(E, 2, 2, st(f"{wd}_stairs", "east"))                         # mounting block by the doors
        P(E, 2, 3, f"{wd}_planks")
        lad = None
        for a in (6, (E + 4) // 2, E - 2):
            hang2(d, x1 + a, z1 + bc, 6)
    if loft and lad is not None and kind != "horse":
        for y in range(2, 7):
            P(lad, y, bc, f"ladder[facing={'east' if lad == 1 else 'west'},waterlogged=false]")
    if kind != "horse":
        for a in (3, w // 2, E - 3):                                   # lanterns over the alley
            if loft:
                hang(d, x1 + a, 5, z1 + 2, 4)
            else:
                hang2(d, x1 + a, z1 + 2, 4)


def hall_nt(d, kind, x1, z1, x2, z2, loft):
    """Neoterra livestock hall: entrance aisle at the west end, a central drive/feed alley down the length with
    pens (or the work island) on both sides of it, the loft ladder at its east end."""
    wd = "birch"
    w, dep = x2 - x1 + 1, z2 - z1 + 1
    E, B, bc = w - 2, dep - 2, dep // 2

    def P(a, y, b, blk):
        d.set(x1 + a, y, z1 + b, blk)

    lad = True
    if kind in ("cattle", "sheep", "pig"):
        manger, trough = {"cattle": ("hay_block[axis=x]", WCAULD), "sheep": ("hay_block[axis=y]", WCAULD),
                          "pig": (WCAULD, "composter[level=7]")}[kind]
        div = "smooth_quartz" if kind == "pig" else f"{wd}_fence"
        for b in list(range(1, bc)) + list(range(bc + 1, B + 1)):     # west boundary of the pens
            P(4, 2, b, f"{wd}_fence")
        for lb, face in ((bc - 1, "north"), (bc + 1, "south")):        # headlock lines along the feed alley
            for a in range(5, E + 1):
                P(a, 2, lb, f"{wd}_fence")
            for a0 in range(4, E, 4):
                for k, blk in ((1, manger), (2, gate(wd, face)), (3, trough)):
                    if a0 + k <= E:
                        P(a0 + k, 2, lb, blk)
        for a0 in range(8, E, 4):                                      # pen dividers
            for b in list(range(1, bc - 1)) + list(range(bc + 2, B + 1)):
                P(a0, 2, b, div)
            for b in (1, B):                                           # pendant lamps over each divider
                hang2(d, x1 + a0, z1 + b, 4)
        for a, b, blk in {"cattle": ((1, 1, "cauldron"), (1, 2, "cauldron"), (1, B, BARREL), (1, B - 1, BARREL)),
                          "sheep": ((1, 1, "white_wool"), (1, 2, "white_wool"), (1, 3, "loom[facing=east]")),
                          "pig": ((1, 1, "composter[level=8]"), (1, 2, BARREL), (1, 3, BARREL))}[kind]:
            P(a, 2, b, blk)
    elif kind == "poultry":                                            # aviary barn
        for a in range(6, E - 1):                                      # double-sided nest island
            P(a, 2, bc, "hay_block[axis=x]")
            P(a, 3, bc, "smooth_quartz_slab[type=bottom,waterlogged=false]")
        P(5, 2, bc, "white_concrete")
        P(E - 1, 2, bc, "white_concrete")
        for a in range(6, E + 1):                                      # perch rail along the north glass
            P(a, 2, 1, f"{wd}_fence" if a % 2 == 0 else AIR)
            P(a, 3, 1, slab(f"{wd}_slab"))
        for a in range(5, E, 3):                                       # feeder / drinker line on the south side
            P(a, 2, B, "composter[level=6]")
            P(a + 1, 2, B, WCAULD)
        P(1, 2, 1, QT)                                                 # egg grading bench
        P(1, 3, 1, EGGS)
        P(1, 2, 2, QT)
        P(1, 3, 2, EGGS)
        P(1, 2, 3, BARREL)
    elif kind == "rabbit":                                             # back-to-back hutch island
        hutch_row(d, x1 + 5, x2 - 2, z1 + bc, 2, wd, "north", 2)
        hutch_row(d, x1 + 5, x2 - 2, z1 + bc + 1, 2, wd, "south", 2)
        P(1, 2, 1, "composter[level=5]")
        P(1, 2, 2, BARREL)
        P(1, 2, B, "hay_block[axis=y]")
        P(1, 3, B, "hay_block[axis=y]")
        P(1, 2, B - 1, BARREL)
        P(2, 2, B, "composter[level=6]")
        P(E, 2, 1, QT)
        P(E, 3, 1, "potted_dandelion")
        P(E, 2, B, "hay_block[axis=y]")                               # bedding store in the far corner
        P(E, 3, B, "hay_block[axis=y]")
        P(E, 2, B - 1, BARREL)
        P(E - 1, 2, B, BARREL)
        P(E - 1, 3, B, "potted_dandelion")
    elif kind == "bees":                                               # honey lab: central island
        isl = ((QT, BREW), (QT, "honey_block"), (WCAULD, None), ("cauldron", None), (QT, "honeycomb_block"),
               (QT, CANDLE4), (QT, BREW), (QT, "honey_block"), (WCAULD, None), (QT, CANDLE2))
        for i, a in enumerate(range(5, E - 1)):
            blk, top_ = isl[i % len(isl)]
            P(a, 2, bc, blk)
            if top_:
                P(a, 3, bc, top_)
        for a in (6, 8, 10):
            _ch(d, x1, z1, a, 2, bc + 1, "south", wd)
        for a in range(5, E + 1, 2):                                   # skep store along the north glass
            P(a, 2, 1, "beehive[facing=south,honey_level=0]")
            P(a + 1 if a + 1 <= E else a, 2, 1, QT)
        P(1, 2, 1, BARREL)
        P(1, 2, 2, BARREL)
    else:                                                              # riding hall: round pen + viewing lounge
        for a in range(1, E + 1):
            for b in range(1, B + 1):
                P(a, 1, b, "smooth_sandstone")
        pa = E - 4                                                     # glass partition of the lounge
        for b in range(1, B + 1):
            for y in (2, 3, 4):
                P(pa, y, b, "glass_pane")
        d.door(x1 + pa, 2, z1 + bc, "east", wd)
        for a in range(pa + 1, E + 1):
            for b in range(1, B + 1):
                P(a, 1, b, "polished_diorite")
        for b in (1, 2, 3):                                            # lounge sofa facing the glass
            _ch(d, x1, z1, E, 2, b, "east", "mangrove")
        P(E - 1, 2, 2, slab("smooth_quartz_slab"))
        for b in (B - 1, B):
            _ch(d, x1, z1, E, 2, b, "east", "mangrove")
        P(E - 2, 2, B, "potted_bamboo")
        P(pa + 1, 2, 1, "potted_bamboo")
        cx = (4 + pa) // 2                                             # round pen (hand-drawn octagon, r=3)
        for dx, dz in ((-1, -3), (1, -3), (2, -2), (3, -1), (3, 0), (3, 1), (2, 2), (1, 3), (0, 3), (-1, 3),
                       (-2, 2), (-3, 1), (-3, 0), (-3, -1), (-2, -2)):
            P(cx + dx, 2, bc + dz, f"{wd}_fence")
        P(cx, 2, bc - 3, gate(wd, "north"))
        P(cx, 2, bc, "hay_block[axis=y]")
        P(1, 2, 1, st("smooth_quartz_stairs", "west"))                 # mounting block
        P(1, 2, 2, "smooth_quartz")
        for b in (B - 2, B - 1, B):                                    # tack lockers
            P(1, 2, b, "barrel[facing=east,open=false]")
        lad = False
        for a in (cx - 3, cx + 3, E - 2):
            P(a, 9 if loft else 5, bc, "sea_lantern")
    if loft and lad and kind != "horse":
        for y in range(2, 7):
            P(E, y, bc, "ladder[facing=west,waterlogged=false]")
    if kind != "horse":
        for a in (3, w // 2, E - 3):
            P(a, 6 if loft else 5, bc, "sea_lantern")


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
        wa = x1 + 4                                                    # two vent windows on the lane side,
        wb = max(x for x in range(xm + 3, x2 - 1) if (x - x1) % 4 == 0)  # clear of the buttresses
        for wx in (wa, wb):
            d.window(wx, 3, z1, wx, 4, z1)
            shutters(d, wx, z1, 3, 4, "north", "dark_oak")
        for x in [x for x in range(x1 + 1, x2) if abs(x - xm) > 1]:   # hay bays, stepped toward the floor
            for z in range(z1 + 1, z2):
                for y in range(2, 2 + min(5, abs(x - xm))):
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
        for x in (x1 + 2, x1 + 3, x2 - 3, x2 - 2):                     # planters at the foot of the glass
            d.set(x, 1, z1 - 1, "moss_block")
            d.set(x, 2, z1 - 1, "azalea" if x in (x1 + 2, x2 - 2) else "flowering_azalea")
        for x in range(xm - 1, xm + 2):
            for y in range(2, 6):
                d.set(x, y, z1, AIR)
            d.set(x, 6, z1, "cyan_terracotta")
        for x in range(x1 + 1, x2):
            for z in range(z1 + 4, z2):
                if x not in (xm - 1, xm, xm + 1):
                    for y in range(2, 2 + (4 if z > z1 + 5 else 3 if z == z1 + 5 else 2)):   # stepped stack
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
        shutters(d, tx1 + 1, tz1, 3, 4, "north", w, sides="l")        # one shutter: the door is beside it
        d.set(tx1 + 2, ridge + 1, tz1 + 2, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        d.set(tx1 - 1, 2, tz1 - 1, "composter[level=6]")                # grain bin, rain butt, straw bale
        d.set(tx1 - 1, 2, tz1 + 5, "water_cauldron[level=3]")          # at the tower's corners
        d.set(tx1 + 5, 2, tz1 + 5, "hay_block[axis=y]")
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
        shutters(d, x1 + 2, z1 + 2, 3, 4, "north", w)                  # shop window under the awning
        for x in range(x1, x1 + 11):                                   # striped awning
            d.set(x, 5, z1 + 1, M["awn"][x % 2])
        for x in (x1, x1 + 10):
            for y in (2, 3, 4):
                d.set(x, y, z1 + 1, M["fence"])
        d.set(x1 + 2, 2, z1 + 1, "cauldron")
        d.set(x1 + 3, 2, z1 + 1, "cauldron")
        d.set(x1 + 8, 2, z1 + 1, slab(f"{w}_slab", "top"))
        d.set(x1 + 8, 3, z1 + 1, "cake[bites=0]")
        tb = slab(f"{w}_slab", "top")
        for k, top_ in ((2, "cake[bites=0]"), (3, "yellow_terracotta"), (4, CANDLE),          # shop counter, gap
                        (7, "yellow_terracotta"), (8, "cake[bites=0]")):                      # for the door
            d.set(x1 + k, 2, z1 + 4, tb)
            d.set(x1 + k, 3, z1 + 4, top_)
        for k, low, sh in ((2, "water_cauldron[level=3]", "yellow_terracotta"),      # cheese room behind:
                           (3, "barrel[facing=up,open=false]", None),               # vats, brine barrels,
                           (4, "water_cauldron[level=3]", "yellow_terracotta"),     # cheese wheels on shelves
                           (6, "barrel[facing=up,open=false]", POT),
                           (7, "barrel[facing=up,open=false]", "yellow_terracotta"),
                           (8, "water_cauldron[level=3]", None)):
            d.set(x1 + k, 2, z1 + 6, low)
            if sh:
                shelf(d, x1 + k, 4, z1 + 6, w, sh)
        hang(d, x1 + 5, ridge - 1, z1 + 4, 4)
        d.sign(x1 + 7, 4, z1 + 1, "north", ["Creamery", "milk ~ cheese"], w)
    elif kind == "sheep":                                              # dye house + drying racks
        ridge = bldg(d, pack, x1 + 1, z1 + 1, x1 + 8, z1 + 5, 5)
        d.door(x1 + 4, 2, z1 + 1, "south", w)
        shutters(d, x1 + 2, z1 + 1, 3, 4, "north", w)
        window_box(d, x1 + 5, z1 + 1, 3, "north", w, ("blue_orchid", "allium") if pack != "Hearthwood" else
                   ("cornflower", "poppy"))
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
        for k, top_ in ((4, "honey_block"), (5, CANDLE), (6, "honeycomb_block")):  # honey stall, awning
            d.set(x1 + k, 2, z1 + 8, slab(f"{w}_slab", "top"))
            d.set(x1 + k, 3, z1 + 8, top_)
        for k in range(3, 8):
            d.set(x1 + k, 5, z1 + 8, M["awn"][k % 2])
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


# ------------------------------------------------------------------------------------------- street fronts
HWF = ("poppy", "cornflower", "oxeye_daisy", "allium")
CSF = ("fern", "dandelion", "fern", "red_tulip")
FRONTS = {   # hand-placed street furniture along each farm's road edge: lamp posts, benches, planted strips
    ("Hearthwood", "poultry"): [("bed", 19, 21, 1, HWF)],
    ("Cascadia", "poultry"): [("bed", 12, 13, 1, CSF), ("lamp", 18, 1)],
    ("Neoterra", "poultry"): [("bench", 3, 1, 2), ("lamp", 9, 1), ("planter", 2, 1)],
    ("Hearthwood", "cattle"): [("lamp", 11, 1), ("bench", 13, 1, 2), ("bed", 16, 17, 1, HWF)],
    ("Cascadia", "cattle"): [("lamp", 13, 1), ("bed", 20, 21, 1, CSF)],
    ("Neoterra", "cattle"): [("lamp", 12, 1), ("bench", 24, 1, 2)],
    ("Hearthwood", "sheep"): [("lamp", 2, 1), ("bench", 12, 1, 2), ("bed", 15, 17, 1, HWF)],
    ("Cascadia", "sheep"): [("lamp", 5, 1), ("bed", 10, 11, 1, CSF), ("bench", 13, 1, 2)],
    ("Neoterra", "sheep"): [("lamp", 5, 1), ("bench", 16, 1, 2)],
    ("Hearthwood", "pig"): [("lamp", 2, 1), ("bench", 13, 1, 2), ("bed", 16, 18, 1, HWF)],
    ("Cascadia", "pig"): [("lamp", 4, 1), ("bed", 9, 10, 1, CSF), ("bench", 15, 1, 2)],
    ("Neoterra", "pig"): [("bench", 3, 1, 2), ("lamp", 11, 1), ("planter", 20, 1)],
    ("Hearthwood", "rabbit"): [("lamp", 8, 1), ("bench", 14, 1, 2)],
    ("Cascadia", "rabbit"): [("lamp", 11, 1), ("bed", 13, 13, 1, CSF), ("bed", 17, 17, 1, CSF)],
    ("Neoterra", "rabbit"): [("bench", 2, 1, 2), ("lamp", 9, 1)],
    ("Hearthwood", "bees"): [("lamp", 4, 1), ("bench", 8, 1, 2), ("bed", 16, 18, 1, ("allium", "allium",
                                                                                   "lily_of_the_valley"))],
    ("Cascadia", "bees"): [("bed", 2, 3, 1, CSF), ("bench", 11, 1, 2), ("lamp", 14, 1)],
    ("Neoterra", "bees"): [("lamp", 9, 1), ("bench", 16, 1, 2)],
    ("Hearthwood", "horse"): [("bench", 15, 1, 2), ("bed", 19, 21, 1, HWF)],
    ("Cascadia", "horse"): [("bed", 5, 6, 1, CSF), ("bench", 13, 1, 2)],
    ("Neoterra", "horse"): [("lamp", 12, 1), ("bench", 14, 1, 2)],
}


def front(d, pack, kind, L):
    """Street front of the farm (from L1): the hand-placed pieces of FRONTS for this type and pack."""
    wood = MAT[pack]["wood"]
    for piece in FRONTS[(pack, kind)]:
        if piece[0] == "lamp":
            lamp_post(d, piece[1], piece[2], pack)
        elif piece[0] == "bench":
            bench(d, piece[1], piece[2], "south", wood, piece[3])
        elif piece[0] == "planter":
            d.set(piece[1], 1, piece[2], "moss_block")
            d.set(piece[1], 2, piece[2], "flowering_azalea")
        elif piece[0] == "bed":
            flowers(d, piece[1], piece[2], (piece[3],), piece[4])


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


# Street windows of the core buildings, dressed by hand: ("shut", x, z, y1, y2[, span]) shutters either side of the
# window at (x, z) in a north wall; ("box", x, z, y[, span]) a window box under it (y = lowest pane row);
# Neoterra: ("plant", x, z) a planter in the paving in front of the glass at (x, z); ("ledge", x, z, y) a planter
# ledge under an upper window; ("fin", x, z, y1, y2) a birch sun fin on the column at (x, z).
CORE_DRESS = {
    ("Hearthwood", "poultry"): [("shut", 5, 3, 3, 4)],
    ("Hearthwood", "cattle"): [("shut", 5, 3, 3, 3)],
    ("Hearthwood", "sheep"): [("shut", 9, 3, 3, 4), ("box", 6, 3, 7, 2)],
    ("Hearthwood", "pig"): [("shut", 4, 3, 3, 4), ("shut", 8, 3, 3, 4), ("box", 8, 3, 3)],
    ("Hearthwood", "rabbit"): [("shut", 5, 3, 3, 3), ("shut", 9, 3, 3, 4), ("box", 5, 3, 3)],
    ("Hearthwood", "bees"): [("shut", 8, 3, 3, 3)],
    ("Hearthwood", "horse"): [("shut", 11, 3, 8, 8), ("shut", 11, 3, 4, 4)],
    ("Cascadia", "poultry"): [("shut", 4, 4, 3, 3), ("shut", 8, 4, 3, 3), ("box", 4, 4, 3)],
    ("Cascadia", "cattle"): [("shut", 6, 3, 3, 3)],
    ("Cascadia", "sheep"): [("shut", 5, 8, 3, 3)],
    ("Cascadia", "pig"): [("shut", 9, 3, 3, 3)],
    ("Cascadia", "rabbit"): [("shut", 4, 3, 3, 3), ("shut", 8, 3, 3, 3), ("box", 8, 3, 3)],
    ("Cascadia", "bees"): [("shut", 5, 6, 3, 3), ("shut", 9, 6, 3, 3), ("box", 9, 6, 3)],
    ("Cascadia", "horse"): [("shut", 6, 3, 3, 3), ("shut", 14, 3, 3, 4), ("shut", 10, 11, 8, 9)],
    ("Neoterra", "poultry"): [("plant", 11, 10)],
    ("Neoterra", "cattle"): [("plant", 3, 1), ("plant", 8, 1)],
    ("Neoterra", "sheep"): [("plant", 3, 1), ("plant", 4, 1), ("plant", 12, 1), ("plant", 13, 1)],
    ("Neoterra", "pig"): [("fin", 6, 11, 4, 4), ("fin", 10, 11, 4, 4), ("fin", 14, 11, 4, 4)],
    ("Neoterra", "rabbit"): [("plant", 10, 8), ("plant", 13, 8)],
    ("Neoterra", "bees"): [("plant", 3, 1), ("plant", 7, 1)],
    ("Neoterra", "horse"): [("plant", 3, 1), ("plant", 9, 1), ("plant", 10, 1), ("ledge", 4, 2, 8), ("ledge", 5, 2, 8)],
}
DRESS_SKIPPED = []


def core_dress(d, pack, kind):
    """Shutters, window boxes and planters on the core buildings' street windows (CORE_DRESS). A piece is only
    drawn when all of its cells are free at this level (so a later porch or prop never gets half a shutter)."""
    o = COTX[(pack, kind)]
    wood, fl = o.get("shut", "birch"), o.get("fl") or ("poppy", "dandelion")
    for e in CORE_DRESS[(pack, kind)]:
        kindp, x, z = e[0], e[1], e[2]
        if kindp == "shut":
            y1, y2 = e[3], e[4]
            span = e[5] if len(e) > 5 else 1
            cells = [(xx, y, z - 1) for y in range(y1, y2 + 1) for xx in (x - 1, x + span)]
        elif kindp == "box":
            y, span = e[3], (e[4] if len(e) > 4 else 1)
            cells = [(x + k, yy, zz) for k in range(span) for yy, zz in ((y - 1, z - 1), (y, z - 1), (y - 1, z - 2))]
        elif kindp == "plant":
            cells = [(x, 2, z)]
        elif kindp == "ledge":
            cells = [(x, e[3] - 1, z - 1), (x, e[3], z - 1)]
        else:
            cells = [(x, y, z - 1) for y in range(e[3], e[4] + 1)]
        if not all(d.air(*c) for c in cells):
            DRESS_SKIPPED.append((pack, kind, e))
            continue
        if kindp == "shut":
            shutters(d, x, z, y1, y2, "north", wood, span)
        elif kindp == "box":
            window_box(d, x, z, y, "north", wood, fl, span)
        elif kindp == "plant":
            d.set(x, 1, z, "moss_block")
            d.set(x, 2, z, "flowering_azalea" if x % 2 else "azalea")
        elif kindp == "ledge":
            d.set(x, e[3] - 1, z - 1, "moss_block")
            d.set(x, e[3], z - 1, "azalea")
        else:
            for y in range(e[3], e[4] + 1):
                d.set(x, y, z - 1, trap("birch", "east", "bottom", open_=True))


def paddock(d, pack, x1, z1, x2, z2, gate_at, high=True):
    """Fenced horse paddock: post-and-rail fence (two rails high for horses), one gate, lanterns on the corner
    posts. Every coordinate is chosen per farm by the caller."""
    fence = MAT[pack]["fence"]
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if x in (x1, x2) or z in (z1, z2):
                if (x, z) == gate_at:
                    d.set(x, 2, z, gate(MAT[pack]["wood"], "east" if x in (x1, x2) else "south"))
                    continue
                d.set(x, 2, z, fence)
                if high:
                    d.set(x, 3, z, fence)
    for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        d.set(x, 4 if high else 3, z, "lantern[hanging=false,waterlogged=false]")


def jump(d, pack, x, z, along="z"):
    """Show jump across z..z+3 (or x..x+3 with along="x"): wing standards with coloured caps, a ground rail
    and a top pole."""
    w = MAT[pack]["wood"]
    caps = ("cyan_concrete", "white_concrete") if pack == "Neoterra" else ("white_wool", "red_wool")
    cell = (lambda k: (x, z + k)) if along == "z" else (lambda k: (x + k, z))
    for k, cap in ((0, caps[0]), (3, caps[1])):
        cx, cz = cell(k)
        d.set(cx, 2, cz, f"{w}_fence")
        d.set(cx, 3, cz, f"{w}_fence")
        d.set(cx, 4, cz, cap)
    for k in (1, 2):
        cx, cz = cell(k)
        d.set(cx, 2, cz, trap(w, "north", "top"))
        d.set(cx, 3, cz, f"stripped_{w}_log[axis={along}]")


def field_shelter(d, pack, x1, z1):
    """3 x 2 open field shelter in a paddock corner: four posts, slab roof, hay and water under it."""
    w = MAT[pack]["wood"]
    for x in (x1, x1 + 2):
        for z in (z1, z1 + 1):
            d.set(x, 2, z, f"{w}_fence")
            d.set(x, 3, z, f"{w}_fence")
    for x in range(x1, x1 + 3):
        for z in (z1, z1 + 1):
            d.set(x, 4, z, slab(MAT[pack]["rsl"] if pack != "Cascadia" else "spruce_slab"))
    d.set(x1 + 1, 2, z1 + 1, "hay_block[axis=y]")
    d.set(x1 + 1, 2, z1, "water_cauldron[level=3]")
    d.set(x1 + 1, 3, z1, "lantern[hanging=true,waterlogged=false]")


def stackyard(d, pack, cx, cz, ring=False):
    """L5 stackyard: a big hay rick (wrapped bales in Neoterra) centred on (cx, cz), with a fenced ring and a
    gate where the farm has room for it."""
    rick(d, pack, cx - 1, cz - 1, True)
    if pack == "Neoterra":                                             # wrapped bales stacked as a pyramid
        for y, r in ((5, 2), (6, 1)):
            for x in range(cx - r, cx + r + 1):
                for z in range(cz - r, cz + r + 1):
                    d.set(x, y, z, "white_wool")
    if ring:
        for x in range(cx - 4, cx + 5):
            for z in range(cz - 4, cz + 5):
                if abs(x - cx) == 4 or abs(z - cz) == 4:
                    d.set(x, 2, z, MAT[pack]["fence"] if (x, z) != (cx - 4, cz) else gate(MAT[pack]["wood"], "east"))


def yard_extras(d, pack, core, L):
    """Hand-placed yard pieces that make the later levels grow: paddocks with jumps for the stables and a hay
    stackyard at L5 for the big-stock farms (coordinates chosen per farm from its L5 layout)."""
    n = core.__name__
    if n == "stable_cs":
        if L >= 3:
            paddock(d, pack, 28, 21, 48, 31, (28, 26))
        if L >= 4:
            for x in (32, 36, 40, 44):
                jump(d, pack, x, 24)
            d.set(46, 2, 22, "water_cauldron[level=3]")
            d.set(47, 2, 22, "hay_block[axis=y]")
            field_shelter(d, pack, 45, 29)
    elif n == "stable_hw" and L >= 4:
        paddock(d, pack, 29, 19, 44, 26, (29, 22))
        for x in (34, 37, 40, 43):
            jump(d, pack, x, 21)
        field_shelter(d, pack, 30, 24)
        d.set(31, 2, 20, "water_cauldron[level=3]")
        d.set(32, 2, 20, "hay_block[axis=y]")
        d.set(28, 2, 21, st("dark_oak_stairs", "east"))                  # mounting block by the gate
        d.set(28, 2, 20, "stone_bricks")
    elif n == "stable_nt" and L >= 4:
        paddock(d, pack, 33, 19, 46, 25, (33, 22))
        for x in (37, 42):
            jump(d, pack, x, 20)
        if L >= 5:                                                     # L5: a third jump, trough, gate lamps
            jump(d, pack, 39, 24, along="x")
            d.set(45, 2, 20, "water_cauldron[level=3]")
            d.set(45, 2, 21, "hay_block[axis=y]")
            lamp_post(d, 32, 20, pack)
            lamp_post(d, 32, 24, pack)
    if L >= 5:
        spot = {"cow_cs": (52, 22, True), "cow_hw": (47, 21, False), "cow_nt": (46, 20, False),
                "pig_nt": (43, 19, False), "stable_nt": (52, 20, False), "stable_hw": (50, 22, True)}.get(n)
        if spot:
            stackyard(d, pack, *spot)


def farmstead(core, pack, rel, L, kind):
    d = core(rel, L)
    core_rooms(d, pack, kind, L)
    core_dress(d, pack, kind)
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
    yard_extras(d, pack, core, L)
    recolor(d, RECOLOR[(pack, kind)])
    if L <= 3:
        downgrade(d)
    return d
