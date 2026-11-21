"""Civic: townhall (hand-designed, all packs). Shared shells/helpers live in _civic_common.py."""
from designs import _civic_common as _c
globals().update({k: v for k, v in vars(_c).items() if not k.startswith("__")})
from hm import design  # noqa: E402,F401


def th_hearthwood(rel, L):
    d = new("Hearthwood", rel, (55, 36, 53))
    two = L >= 3
    nf = 2 if two else 1
    # ---- core guildhall (L1+): public hall
    c = bldg(d, 20, 14, 32, 22, nf, "gable", "x", win="nesw")
    d.hut(21, Y0, 15)
    keep(d, 22, Y0, 15)
    d.set(23, Y0, 15, slab("dark_oak_slab", "top"))
    put(d, 23, Y0 + 1, 15, "candle[candles=2,lit=false,waterlogged=false]")
    d.chair(23, Y0, 16, "south", "dark_oak", sit=False)
    long_table(d, 25, 18, 27, Y0, "dark_oak")
    line_items(d, 21, 17, "z", Y0, "east", ["crafting_table", "furnace", "furnace"])
    barrels(d, 31, 15, "z", Y0, 2, "west")
    d.bed(31, Y0, 21, "east")
    put(d, 31, Y0, 20, slab("dark_oak_slab", "top"))
    put(d, 31, Y0 + 1, 20, "candle[candles=1,lit=false,waterlogged=false]")
    rug_in(d, (21, 15, 31, 21), Y0, ("red_carpet", "yellow_carpet"))
    wall_art(d, (21, 15, 31, 21), Y0, "s", ("red", "yellow"))
    # entrance tower over the door (stub L1-2, clock & belfry L3+)
    tt = {1: 9, 2: 14}.get(L, 25)
    t = bldg(d, 24, 9, 28, 14, 1, "flat", wh=tt - 1, mat="stone_bricks", up="stone_bricks", win="", deco=False,
             parapet=False)
    d.clear(25, Y0, 14, 27, 4, 14)
    ext_door(d, 26, Y0, 9, "south")
    d.sign(26, 5, 8, "north", ["TOWN", "HALL"], "dark_oak")
    d.banner(25, 6, 8, "north", "red")
    d.banner(27, 6, 8, "north", "red")
    d.fill(25, 6, 10, 27, 6, 13, "dark_oak_planks")
    by = tt - 3
    d.fill(25, by, 10, 27, by, 13, "dark_oak_planks")
    for y in range(by + 1, tt):
        for x in range(25, 28):
            d.set(x, y, 9, AIR)
            d.set(x, y, 14, AIR)
        for z in range(10, 14):
            d.set(24, y, z, AIR)
            d.set(28, y, z, AIR)
    bell(d, 26, tt - 1, 11)
    d.fill(24, tt, 9, 28, tt, 14, "stone_bricks")
    rt = d.hip(24, 9, 28, 14, tt + 1, f"{d.S['roof']}_stairs", f"{d.S['roof']}_slab", overhang=1)
    d.set(26, rt + 1, 11, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    if two:
        clockface(d, 26, by - 3, 9, "north", "white_concrete")
        clockface(d, 24, by - 3, 11, "west", "white_concrete")
        clockface(d, 28, by - 3, 11, "east", "white_concrete")
        for x in range(24, 29):
            put(d, x, by - 6, 8, st("stone_brick_stairs", "south", "top"))
    # forecourt: patterned paving, lamp posts, flower beds
    for x in range(14, 39):
        for z in range(1, 9):
            d.set(x, 1, z, "stone_bricks" if (x + z) % 3 else "polished_andesite")
    for x in (21, 31):
        post_lamp(d, x, 7)
    flowerbed(d, 20, 12, 23, 13)
    flowerbed(d, 29, 12, 32, 13)
    # ---- L2: workshop wing (west) + stores wing (east)
    if L >= 2:
        w = bldg(d, 8, 14, 20, 22, nf, "gable", "x", mat="bricks", up="calcite")
        link(d, 20, Y0, 18, "west")
        items = work_items(d, L)
        a, b = items[:11], items[11:]
        line_items(d, 9, 15, "x", Y0, "south", a[:11])
        line_items(d, 9, 21, "x", Y0, "north", b + [None] * 0)
        d.hearth(13, Y0, 18, "north", 6, "bricks", "campfire") if False else None
        for x in range(11, 18):
            if x % 2:
                put(d, x, Y0, 18, slab("dark_oak_slab", "top"))
                put(d, x, Y0 + 1, 18, ("flower_pot", "candle[candles=2,lit=false,waterlogged=false]")[x % 4 == 1])
        lights(d, (9, 15, 19, 21), Y0)
        chimney(d, 8, 16, Y0, w["ridge"] + 1)
        d.sign(14, 5, 13, "north", ["Guild", "Workshop"], "dark_oak")
        ext_door(d, 8, Y0, 18, "east")
        s_ = bldg(d, 32, 14, 44, 22, nf, "gable", "x", mat="bricks", up="calcite")
        link(d, 32, Y0, 18, "east")
        nb = need(d, "barrel") - 4
        barrels(d, 33, 15, "x", Y0, min(11, (nb + 1) // 2), "south")
        if nb > 22:
            pass
        rest = nb - 2 * min(11, (nb + 1) // 2)
        if rest > 0:
            barrels(d, 33, 21, "x", Y0, (rest + 1) // 2, "north")
        ext_door(d, 44, Y0, 18, "west", double=True, along="z")
        store(d, (33, 17, 43, 20), Y0)
        cart(d, 47, 16, "z")
        put(d, 47, 2, 21, "hay_block[axis=y]")
        path(d, 45, 18, 52, 19, border=False)
    # ---- L3: upper floor: archive (W), council chamber (centre), quarters (E)
    if two:
        stair_up(d, 22, 21, Y0, 7, "east")
        link(d, 20, 7, 18, "east")
        link(d, 32, 7, 18, "east")
        for x in range(23, 30):
            pass
        long_table(d, 24, 17, 29, 7, "dark_oak", top="dark_oak_planks")
        d.item(30, 7, 15, "lectern", "west")
        keep(d, 29, 7, 15)
        if L >= 4:
            d.item(21, 7, 15, "jukebox")
            keep(d, 22, 7, 15)
        wall_art(d, (21, 15, 31, 21), 7, "n", ("red", "yellow"))
        rug_in(d, (21, 15, 31, 20), 7, ("red_carpet",), inset=1, pattern="plain")
        shelf_wall(d, (9, 15, 19, 21), "n", 7, 3)
        shelf_wall(d, (9, 15, 19, 21), "w", 7, 3)
        d.item(14, 7, 19, "enchanting_table")
        keep(d, 14, 7, 20)
        for z in (17, 20):                                          # freestanding record presses
            stall_row(d, 11, 12, z, 7, 2)
        for z in (17, 20):                                          # clerks' desks under the windows
            desk(d, 18, 7, z, "west", sit=False)
        d.rug(13, 18, 15, 20, 7, ("green_carpet",), "plain")
        lights(d, (9, 15, 19, 21), 7)
        dorm(d, (33, 15, 43, 21), 7, 5, head="n")
        if L >= 4:
            d.item(43, 7, 21, "ender_chest", "west")
            keep(d, 42, 7, 21)
    # ---- L4: rear wing – banquet hall & kitchen below, mayor's apartment above
    if L >= 4:
        r = bldg(d, 20, 22, 32, 35, 2, "gable", "z", mat="bricks", up="calcite")
        link(d, 26, Y0, 22, "south")
        long_table_z(d, 26, 25, 31, Y0, "dark_oak")
        kitchen(d, (21, 31, 31, 34), Y0)
        wall_art(d, (21, 23, 31, 33), Y0, "ew", ("red", "yellow"))
        stair_up(d, 31, 24, Y0, 7, "south")
        office(d, (21, 23, 30, 27), 7)
        dorm(d, (21, 29, 31, 34), 7, 2, head="s")
        lounge(d, (21, 28, 31, 34), 7)
        chimney(d, 32, 30, Y0, r["ridge"] + 1)
        # walled garden behind with a bandstand
        lawn(d, 8, 36, 46, 51)
        for x in range(8, 47):
            put(d, x, 2, 51, "brick_wall")
        for z in range(36, 52):
            put(d, 8, 2, z, "brick_wall")
            put(d, 46, 2, z, "brick_wall")
        path(d, 25, 35, 27, 50)
        bx, bz = 26, 43
        for x in range(bx - 3, bx + 4):
            for z in range(bz - 3, bz + 4):
                if abs(x - bx) + abs(z - bz) <= 4:
                    d.set(x, 1, z, "stone_bricks")
        for x, z in ((bx - 2, bz - 2), (bx + 2, bz - 2), (bx - 2, bz + 2), (bx + 2, bz + 2)):
            for y in range(Y0, 6):
                d.set(x, y, z, "dark_oak_fence")
        d.hip(bx - 2, bz - 2, bx + 2, bz + 2, 6, "deepslate_tile_stairs", "deepslate_tile_slab", overhang=1)
        for x, z in ((12, 40), (40, 40), (12, 48), (40, 48)):
            plant_tree(d, x, z)
        flowerbed(d, 15, 37, 22, 38)
        flowerbed(d, 30, 37, 37, 38)
        flowerbed(d, 10, 49, 22, 50)
        flowerbed(d, 30, 49, 44, 50)
        for x, z in ((21, 42), (31, 42), (21, 46), (31, 46)):
            post_lamp(d, x, z)
        for x, z in ((18, 44), (33, 44)):
            park_bench(d, x, z, "x", "south")
    # ---- L5: market square with stalls & fountain; courthouse (W) and guard house (E) round the garden
    if L >= 5:
        fountain(d, 26, 4, 2)
        for x, col in ((15, "red"), (35, "blue")):
            market_stall(d, x, 2, col)
        for x, col in ((10, "yellow"), (40, "green")):
            market_stall(d, x, 5, col)
        ch = bldg(d, 8, 24, 18, 34, 2, "gable", "z", mat="stone_bricks", up="stone_bricks", gable_end="stone_bricks")
        ext_door(d, 13, Y0, 24, "south")
        for x in range(9, 18):
            pass
        d.item(13, Y0, 32, "lectern", "north") if False else put(d, 13, Y0, 32, "dark_oak_planks")
        lecture(d, (9, 25, 17, 33), Y0, "s")
        stair_up(d, 9, 26, Y0, 7, "south")
        office(d, (9, 25, 17, 33), 7)
        shelf_wall(d, (9, 25, 17, 33), "e", 7, 3)
        d.sign(13, 5, 23, "north", ["COURT", "HOUSE"], "dark_oak")
        gh = bldg(d, 34, 24, 44, 34, 2, "gable", "z", mat="bricks", up="calcite")
        ext_door(d, 39, Y0, 24, "south")
        d.sign(39, 5, 23, "north", ["WATCH", "HOUSE"], "dark_oak")
        table_set(d, (35, 25, 43, 29), Y0, "dining")
        for x in range(36, 43, 2):                                 # cells
            d.fill(x, Y0, 31, x, 4, 33, "iron_bars")
        stair_up(d, 43, 27, Y0, 7, "south")
        dorm(d, (35, 25, 42, 33), 7, 6, head="w")
        # covered market house: open arcade below, corn exchange above
        mx1, mz1, mx2, mz2 = 46, 24, 54, 36
        m = bldg(d, mx1, mz1, mx2, mz2, 2, "gable", "z", mat="stone_bricks", up="calcite")
        for x in range(mx1, mx2 + 1):
            for z in range(mz1, mz2 + 1):
                if (x in (mx1, mx2) or z in (mz1, mz2)) and not ((x in (mx1, mx2) and (z - mz1) % 3 == 0) or
                                                                 (z in (mz1, mz2) and (x - mx1) % 4 == 0)):
                    for y in range(Y0, 6):
                        d.set(x, y, z, AIR)
                    d.set(x, 5, z, "stone_brick_slab[type=top,waterlogged=false]")
        for x, z, col in ((48, 27, "red"), (51, 27, "yellow"), (48, 31, "green"), (51, 31, "blue")):
            put(d, x, Y0, z, slab("dark_oak_slab", "top"))
            put(d, x + 1, Y0, z, f"{col}_wool")
            put(d, x, Y0 + 1, z, ("melon", "pumpkin", "hay_block[axis=y]", "carved_pumpkin[facing=north]")[x % 4])
        stair_up(d, 47, 35, Y0, 7, "north") if False else stair_up(d, 53, 34, Y0, 7, "north")
        table_set(d, (47, 25, 52, 35), 7, "dining")
        d.sign(50, 6, 23, "north", ["MARKET", "HOUSE"], "dark_oak")
        for z in (26, 30):
            put(d, 33, 4, z, "lantern[hanging=false,waterlogged=false]") if False else None
    return d


def th_neoterra(rel, L):
    d = new("Neoterra", rel, (53, 45, 49), paving="smooth_stone")
    Q = "smooth_quartz"
    two = L >= 3
    nf = 2 if two else 1
    c = bldg(d, 18, 12, 32, 22, nf, "flat", glassy=True, win="nesw")
    ext_door(d, 24, Y0, 12, "south", double=True)
    d.hut(19, Y0, 13)
    keep(d, 20, Y0, 13)
    for x in range(21, 24):
        d.set(x, Y0, 15, Q)
    d.chair(22, Y0, 16, "south", "mangrove", sit=False)
    for x, z in ((25, 17), (26, 17), (25, 18), (26, 18)):
        d.table(x, Y0, z, "birch", "block", Q)
    for x in (25, 26):
        d.chair(x, Y0, 16, "north", "birch")
        d.chair(x, Y0, 19, "south", "birch")
    for z in (17, 18):
        d.chair(24, Y0, z, "west", "birch")
        d.chair(27, Y0, z, "east", "birch")
    line_items(d, 19, 17, "z", Y0, "east", ["crafting_table", "furnace", "furnace"])
    barrels(d, 31, 13, "z", Y0, 2, "west")
    d.bed(31, Y0, 21, "east", "cyan")
    put(d, 31, Y0, 20, "white_concrete")
    put(d, 31, Y0 + 1, 20, "end_rod[facing=up]")
    corners(d, (19, 13, 31, 21), Y0, ["potted_bamboo"])
    for x in range(20, 31):
        for z in (12, 11, 10, 9):
            pass
    for x in range(21, 30):                                         # entrance canopy
        for z in range(8, 12):
            put(d, x, 6 if not two else 6, z, slab("smooth_quartz_slab", "top"))
    d.sign(25, 7 if two else 7, 11, "north", ["CIVIC", "CENTRE"], "birch", glow=True, color="cyan") if False else \
        d.sign(25, 6 if not two else 7, 11 if two else 7, "north", ["CIVIC", "CENTRE"], "birch", glow=True, color="cyan")
    # plaza paving pattern
    for x in range(10, 41):
        for z in range(1, 12):
            if d.get(x, 1, z) == "minecraft:smooth_stone":
                d.set(x, 1, z, "polished_diorite" if (x // 2 + z // 2) % 2 else "smooth_stone")
    for x in (20, 30):
        post_lamp(d, x, 4)
    for x in (16, 34):
        put(d, x, 2, 9, "moss_block")
        put(d, x, 3, 9, "flowering_azalea")
    if L >= 2:
        w = bldg(d, 6, 12, 18, 22, nf, "flat", glassy=True, win="nsw")
        link(d, 18, Y0, 17, "west")
        items = work_items(d, L)
        line_items(d, 7, 13, "x", Y0, "south", items[:11])
        line_items(d, 7, 21, "x", Y0, "north", items[11:])
        for x in range(9, 16):
            put(d, x, Y0, 17, slab("smooth_quartz_slab", "top"))
            put(d, x, Y0 + 1, 17, ("flower_pot", "end_rod[facing=up]", AIR)[x % 3]) if x % 3 < 2 else None
        ext_door(d, 6, Y0, 17, "east")
        d.sign(12, 6, 11, "north", ["MAKER", "SPACE"], "birch", glow=True, color="orange")
        s_ = bldg(d, 32, 12, 44, 22, nf, "flat", glassy=False, win="ns")
        link(d, 32, Y0, 17, "east")
        nb = need(d, "barrel") - 4
        barrels(d, 33, 13, "x", Y0, min(11, (nb + 1) // 2), "south")
        rest = nb - 2 * min(11, (nb + 1) // 2)
        if rest > 0:
            barrels(d, 33, 21, "x", Y0, (rest + 1) // 2, "north")
        ext_door(d, 44, Y0, 17, "west", double=True, along="z")
        store(d, (33, 15, 43, 19), Y0)
        # clock fin with bell frame
        ft = 17 if L == 2 else 28
        for x in range(46, 49):
            for z in range(7, 10):
                for y in range(Y0, ft + 1):
                    d.set(x, y, z, "white_concrete")
        for y in range(Y0 + 1, ft - 3):
            d.set(47, y, 7, "cyan_stained_glass")
        clockface(d, 47, ft - 1, 7, "north", "black_concrete", hand="sea_lantern")
        for x, z in ((46, 7), (48, 7), (46, 9), (48, 9)):
            for y in range(ft + 1, ft + 4):
                d.set(x, y, z, "quartz_pillar[axis=y]")
        d.fill(46, ft + 4, 7, 48, ft + 4, 9, Q)
        bell(d, 47, ft + 3, 8)
        d.set(47, ft + 5, 8, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    if two:
        stair_up(d, 20, 21, Y0, 7, "east")
        link(d, 18, 7, 17, "east")
        link(d, 32, 7, 17, "east")
        for x in range(22, 29):                                     # horseshoe council table
            d.table(x, 7, 19, "birch", "block", Q)
            d.chair(x, 7, 20, "south", "mangrove")
        for z in (15, 16, 17, 18):
            for x, back in ((22, "west"), (28, "east")):
                d.table(x, 7, z, "birch", "block", Q)
                d.chair(x + (-1 if back == "west" else 1), 7, z, back, "mangrove")
        d.item(25, 7, 13, "lectern", "south")
        keep(d, 25, 7, 14)
        d.banner(25, 9, 13, "south", "cyan") if False else None
        if L >= 4:
            d.item(30, 7, 13, "jukebox")
            keep(d, 30, 7, 14)
        shelf_wall(d, (7, 13, 17, 21), "w", 7, 3)
        shelf_wall(d, (7, 13, 17, 21), "s", 7, 3)
        d.item(12, 7, 16, "enchanting_table")
        keep(d, 12, 7, 17)
        table_set(d, (8, 13, 16, 15), 7, "study", sit=False)
        dorm(d, (33, 13, 43, 21), 7, 5, head="n")
        if L >= 4:
            d.item(43, 7, 21, "ender_chest", "west")
            keep(d, 42, 7, 21)
        for b in (w, s_):
            roof_garden(d, b, "garden" if b is w else "solar")
    if L >= 4:
        r = bldg(d, 18, 22, 32, 34, 3, "flat", glassy=True, win="esw")
        link(d, 25, Y0, 22, "south")
        long_table(d, 21, 27, 29, Y0, "birch", top=Q)
        long_table(d, 21, 30, 29, Y0, "birch", top=Q)
        kitchen(d, (19, 33, 31, 33), Y0) if False else None
        corners(d, (19, 23, 31, 33), Y0, ["potted_bamboo"])
        stair_up(d, 31, 24, Y0, 7, "south")
        office(d, (19, 23, 25, 33), 7)
        lounge(d, (26, 23, 30, 33), 7)
        stair_up(d, 19, 32, 7, 12, "north")
        table_set(d, (20, 23, 31, 33), 12, "study", sit=False)
        roof_garden(d, r, "garden")
        fountain(d, 25, 4, 2)
        for x, z in ((12, 3), (38, 3), (12, 8), (38, 8)):
            plant_tree(d, x, z)
        for x in (15, 33):
            park_bench(d, x, 5, "x", "north")
    if L >= 5:
        tw = bldg(d, 34, 24, 46, 40, 6, "flat", glassy=True, win="nsew")
        ext_door(d, 40, Y0, 40, "north", double=True)
        link(d, 34, Y0, 30, "east") if False else None
        for k in range(5):
            stair_up(d, 35 if k % 2 == 0 else 45, 25 if k % 2 == 0 else 39, Y0 + 5 * k, Y0 + 5 * k + 5,
                     "south" if k % 2 == 0 else "north")
        lounge(d, (36, 26, 44, 38), Y0)
        for k in range(1, 6):
            y = Y0 + 5 * k
            office(d, (36, 25, 44, 31), y)
            table_set(d, (36, 33, 44, 38), y, "study", sit=False)
        roof_garden(d, tw, "solar")
        for i, b in enumerate((c,)):
            roof_garden(d, b, "garden")
        for x, col in ((8, "orange"), (42, "lime")):
            market_stall(d, x, 4, col)
        d.sign(40, 6, 41, "south", ["CITY", "OFFICES"], "birch", glow=True, color="cyan")
    return d


def th_cascadia(rel, L):
    d = new("Cascadia", rel, (55, 34, 55), paving="coarse_dirt")
    loft = L >= 3
    c = bldg(d, 14, 10, 28, 22, 2 if loft else 1, "gable", "z")
    ext_door(d, 21, Y0, 10, "south")
    d.fill(13, 1, 5, 29, 1, 9, "spruce_planks")                   # porch
    for x in (13, 17, 25, 29):
        for y in range(Y0, 6):
            put(d, x, y, 5, log("spruce_log"))
    for x in range(12, 31):
        d.set(x, 6, 4, st("spruce_stairs", "south"))
        for z in range(5, 10):
            d.set(x, 6, z, slab("spruce_slab"))
    for x in range(14, 29):
        if x not in (13, 17, 25, 29) and abs(x - 21) > 1:
            put(d, x, Y0, 5, "spruce_fence")
    d.sign(21, 5, 9, "north", ["GRANGE", "HALL"], "spruce")
    for x in (15, 27):
        d.chair(x, Y0, 7, "south", "spruce", sit=False)
    d.hut(15, Y0, 11)
    keep(d, 16, Y0, 11)
    for z in range(13, 18):
        d.table(21, Y0, z, "spruce", "block", "stripped_spruce_wood[axis=y]")
        d.chair(20, Y0, z, "west", "spruce")
        d.chair(22, Y0, z, "east", "spruce")
    d.chair(21, Y0, 18, "south", "spruce")
    line_items(d, 27, 11, "z", Y0, "west", ["crafting_table", "furnace", "furnace"])
    barrels(d, 27, 15, "z", Y0, 2, "west")
    d.bed(15, Y0, 19, "west")
    put(d, 15, Y0, 20, slab("spruce_slab", "top"))
    d.hearth(15, Y0, 16, "east", c["ridge"] + 2, "cobblestone", "campfire")
    chimney(d, 13, 16, Y0, c["ridge"] + 1)
    rug_in(d, (16, 12, 26, 20), Y0, ("brown_carpet", "green_carpet"))
    if L >= 2:
        w = bldg(d, 14, 22, 28, 32, 1, "gable", "z")
        link(d, 21, Y0, 22, "south")
        items = work_items(d, L)
        line_items(d, 15, 23, "z", Y0, "east", items[:9])
        line_items(d, 27, 23, "z", Y0, "west", items[9:])
        workshop(d, (17, 24, 25, 31), Y0)
        ext_door(d, 21, Y0, 32, "north", double=True)
        chimney(d, 28, 27, Y0, w["ridge"] + 1)
        # barrel shed lean-to
        nb = need(d, "barrel") - 4
        sh = bldg(d, 29, 12, 35, 22, 1, "gable", "z", win="e")
        link(d, 29, Y0 if False else Y0, 19, "east") if False else None
        ext_door(d, 32, Y0, 12, "south", double=False)
        barrels(d, 34, 13, "z", Y0, min(9, (nb + 1) // 2), "west")
        rest = nb - 2 * min(9, (nb + 1) // 2)
        if rest > 0:
            barrels(d, 30, 14, "z", Y0, (rest + 1) // 2, "east")
        for x, z in ((38, 14), (39, 14)):
            for y in (2, 3):
                put(d, x, y, z, log("spruce_log", "z"))
        cart(d, 37, 18, "z")
    if loft:
        stair_up(d, 17, 21, Y0, 7, "east")
        shelf_wall(d, (16, 11, 26, 15), "w", 7, 3)
        shelf_wall(d, (16, 11, 26, 15), "n", 7, 3)
        shelf_wall(d, (16, 11, 26, 15), "e", 7, 2)
        d.item(21, 7, 13, "enchanting_table")
        d.item(18, 7, 16, "lectern", "south")
        keep(d, 18, 7, 17)
        keep(d, 21, 7, 14)
        if L >= 4:
            d.item(15, 7, 19, "ender_chest", "east")
            keep(d, 16, 7, 19)
        dorm(d, (15, 17, 25, 21), 7, 5, head="n")
        # fire-lookout bell tower
        tx1, tz1 = 40, 4
        for x, z in ((tx1, tz1), (tx1 + 4, tz1), (tx1, tz1 + 4), (tx1 + 4, tz1 + 4)):
            for y in range(Y0, 18):
                d.set(x, y, z, log("spruce_log"))
        for y in (7, 12):
            for a in range(1, 4):
                for (x, z, ax) in ((tx1 + a, tz1, "x"), (tx1 + a, tz1 + 4, "x"), (tx1, tz1 + a, "z"),
                                   (tx1 + 4, tz1 + a, "z")):
                    d.set(x, y, z, log("spruce_log", ax))
        d.fill(tx1, 17, tz1, tx1 + 4, 17, tz1 + 4, "spruce_planks")
        for x in range(tx1, tx1 + 5):
            for z in range(tz1, tz1 + 5):
                if x in (tx1, tx1 + 4) or z in (tz1, tz1 + 4):
                    d.set(x, 18, z, "spruce_fence")
        for x, z in ((tx1, tz1), (tx1 + 4, tz1), (tx1, tz1 + 4), (tx1 + 4, tz1 + 4)):
            for y in range(18, 21):
                d.set(x, y, z, log("spruce_log"))
        d.hip(tx1, tz1, tx1 + 4, tz1 + 4, 21, "dark_oak_stairs", "dark_oak_slab", overhang=1)
        d.set(tx1 + 2, 21, tz1 + 2, "spruce_planks")
        bell(d, tx1 + 2, 20, tz1 + 2)
    else:
        for y in range(Y0, 6):
            d.set(32, y, 6, log("spruce_log"))
            d.set(34, y, 6, log("spruce_log"))
        d.fill(32, 6, 6, 34, 6, 6, log("spruce_log", "x"))
        bell(d, 33, 5, 6)
    if L >= 4:
        m = bldg(d, 2, 10, 12, 24, 2, "gable", "z")
        ext_door(d, 7, Y0, 10, "south")
        d.sign(7, 5, 9, "north", ["MAYOR"], "spruce")
        stair_up(d, 11, 12, Y0, 7, "south")
        lounge(d, (3, 11, 10, 16), Y0)
        kitchen(d, (3, 17, 10, 21), Y0)
        table_set(d, (4, 17, 9, 21), Y0, "dining")
        office(d, (3, 11, 11, 16), 7)
        d.item(3, 7, 21, "jukebox")
        keep(d, 4, 7, 21)
        for x in (3, 11):                                            # porch posts and roof over the mayor's door
            for y in range(Y0, 5):
                put(d, x, y, 9, log("spruce_log"))
        for x in range(2, 13):
            for z in (8, 9):
                put(d, x, 5, z, slab("spruce_slab"))
        dorm(d, (3, 17, 11, 21), 7, 2, head="w")
        chimney(d, 2, 16, Y0, m["ridge"] + 1)
        for x in range(1, 13):
            put(d, x, 2, 6, "spruce_fence")
        flowerbed(d, 2, 7, 5, 8, ("fern", "blue_orchid", "allium", "lily_of_the_valley"))
        flowerbed(d, 9, 7, 12, 8, ("fern", "blue_orchid", "allium", "lily_of_the_valley"))
        plant_tree(d, 4, 3)
        plant_tree(d, 10, 3)
    if L >= 5:
        f = bldg(d, 36, 14, 48, 28, 2, "gable", "z", mat="mangrove_planks", up="mangrove_planks")
        d.double_door(41, Y0, 14, "x", "south", "spruce")
        for x in (40, 43):
            d.set(x, Y0, 14, AIR)
            d.set(x, Y0 + 1, 14, AIR)
            d.set(x, Y0 + 2, 14, AIR)
        d.sign(42, 6, 13, "north", ["FIRE", "HALL"], "spruce")
        for z in range(16, 26):                                      # engine bay: cart, hoses
            put(d, 42, Y0, z, "red_wool" if z % 3 else "barrel[facing=up,open=false]") if z in (18, 19, 20) else None
        cart(d, 41, 18, "z")
        kitchen(d, (37, 15, 40, 27), Y0)
        table_set(d, (37, 20, 40, 27), Y0, "dining")
        for z in range(16, 26, 2):
            put(d, 47, Y0 + 1, z, "lantern[hanging=false,waterlogged=false]") if False else None
        stair_up(d, 47, 22, Y0, 7, "south")
        dorm(d, (37, 15, 45, 26), 7, 6, head="w", desks=False)
        for y in range(Y0, 24):                                      # hose-drying tower
            for x, z in ((50, 22), (52, 22), (50, 24), (52, 24)):
                d.set(x, y, z, log("spruce_log"))
            if y % 5 == 0:
                for x in (50, 51, 52):
                    d.set(x, y, 22, log("spruce_log", "x"))
                    d.set(x, y, 24, log("spruce_log", "x"))
        d.hip(50, 22, 52, 24, 24, "dark_oak_stairs", "dark_oak_slab", overhang=1)
        jl = bldg(d, 36, 34, 46, 42, 1, "gable", "x", mat="cobblestone", up="cobblestone", gable_end="cobblestone")
        ext_door(d, 41, Y0, 34, "south")
        d.sign(41, 5, 33, "north", ["JAIL"], "spruce")
        for x in range(38, 45, 2):
            d.fill(x, Y0, 39, x, 4, 41, "iron_bars")
        table_set(d, (37, 35, 45, 37), Y0, "dining")
        lv = bldg(d, 2, 28, 12, 42, 1, "gable", "z", mat="stripped_spruce_log")
        ext_door(d, 7, Y0, 28, "south", double=True)
        for z in range(30, 42, 3):                                  # stalls with hay
            for x in (3, 11):
                put(d, x, Y0, z, "hay_block[axis=y]")
            d.fill(4, Y0, z + 2, 4, Y0 + 1, z + 2, "spruce_fence")
            d.fill(10, Y0, z + 2, 10, Y0 + 1, z + 2, "spruce_fence")
        d.sign(7, 5, 27, "north", ["LIVERY"], "spruce")
        # boardwalk main street with hitching rails and lamps
        for x in range(0, 55):
            for z in range(0, 3):
                d.set(x, 1, z, "spruce_planks")
        for x in range(2, 53, 6):
            put(d, x, 2, 3, "spruce_fence")
            put(d, x, 3, 3, "lantern[hanging=false,waterlogged=false]")
    return d


@design("townhall")
def townhall_v2(pack, rel, L):
    return common_materials({"Hearthwood": th_hearthwood, "Cascadia": th_cascadia, "Neoterra": th_neoterra}[pack](rel, L))
