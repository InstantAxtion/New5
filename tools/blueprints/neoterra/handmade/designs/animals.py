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
from hm import Design, design, AIR, D4, OPP

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
    d = Design("Hearthwood", rel, (23, 16, 22), paving="grass_block[snowy=false]")
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
                d.set(x, 2, 1, "rose_bush[half=lower]")
                d.set(x, 3, 1, "rose_bush[half=upper]")
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
    d = Design("Cascadia", rel, (21, 18, 25), paving=GRASS)
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
    pen(d, 11, 2, 19, rz2, "spruce_fence", gates=[(15, 2), (11, 8)], patches=("podzol", 5))
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
    d = Design("Neoterra", rel, (19, 14, 21), paving="smooth_stone")
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
        d.set(15, 2, z, "potted_bamboo") if z > 2 else None
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


@design("chickenherder")
def chickenherder(pack, rel, L):
    return {"Hearthwood": chicken_hw, "Cascadia": chicken_cs, "Neoterra": chicken_nt}[pack](rel, L)
