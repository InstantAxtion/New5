"""Civic: university (hand-designed, all packs). Shared shells/helpers live in _civic_common.py."""
from designs import _civic_common as _c
globals().update({k: v for k, v in vars(_c).items() if not k.startswith("__")})
from hm import design  # noqa: E402,F401


def uni_hearthwood(rel, L):
    """Oxford college growing into a full quadrangle campus."""
    d = new("Hearthwood", rel, (49, 30, 57))
    SB = "stone_bricks"
    # ---- L1: Old Schools – the study (common room) with fireplace, study table, lectern, rack
    os_nf = 2 if L >= 4 else 1
    b = bldg(d, 8, 8, 20, 15, os_nf, "gable", "x", mat=SB, up=SB, gable_end=SB)
    ext_door(d, 14, Y0, 8, "south", double=False)
    d.sign(14, 5, 7, "north", ["OLD SCHOOLS", "", "Collegium"], "dark_oak")
    d.hut(19, Y0, 9)
    keep(d, 18, Y0, 9)
    d.hearth(9, Y0, 12, "east", b["ridge"] + 2, "bricks", "campfire")
    chimney(d, 8, 12, Y0, b["ridge"] + 1)
    d.chair(11, Y0, 11, "west", "dark_oak", arms=False)
    d.chair(11, Y0, 13, "west", "dark_oak", arms=False)
    d.item(19, Y0, 13, "lectern", "west")
    keep(d, 18, Y0, 13)
    d.rack(19, Y0, 11, "west")
    keep(d, 18, Y0, 11)
    d.item(9, Y0, 9, "furnace", "east")
    keep(d, 10, Y0, 9)
    if os_nf == 2:
        stair_up(d, 13, 14, Y0, 7, "east")
    long_table(d, 14, 12, 16, Y0, "dark_oak")
    shelf_wall(d, (9, 9, 19, 14), "s", Y0, 3, skip=[(9, 14), (19, 14)])
    rug_in(d, (9, 9, 19, 14), Y0, ("red_carpet", "brown_carpet"))
    corners(d, (9, 9, 19, 14), Y0)
    wall_art(d, (9, 9, 19, 14), Y0, "n", ("blue", "white"))
    if os_nf == 2:                                                  # upper storey: student sets
        dorm(d, (9, 9, 19, 13), 7, 5, head="n")
    # forecourt
    path(d, 13, 0, 15, 7)
    for x in (11, 17):
        post_lamp(d, x, 5)
    flowerbed(d, 9, 5, 11, 6)
    flowerbed(d, 17, 5, 19, 6)
    # ---- L2: gate tower + laboratory range
    if L >= 2:
        g = bldg(d, 21, 7, 25, 15, 3, "flat", mat=SB, up=SB, win="nesw", ws=2)
        d.clear(22, Y0, 7, 24, 5, 15)                              # gate passage
        for x in range(22, 25):
            for z in range(7, 16):
                d.set(x, 1, z, "stone_bricks")
        for z in (7, 15):
            d.set(22, 5, z, st("stone_brick_stairs", "west", "top"))
            d.set(24, 5, z, st("stone_brick_stairs", "east", "top"))
            d.set(23, 5, z, "chiseled_stone_bricks")
        for x, z in ((21, 7), (25, 7), (21, 15), (25, 15)):        # corner turrets
            for y in range(g["top"] + 2, g["top"] + 5):
                d.set(x, y, z, SB if y < g["top"] + 4 else "stone_brick_wall")
        d.banner(22, 9, 6, "north", "blue")
        d.banner(24, 9, 6, "north", "blue")
        clockface(d, 23, 13, 7, "north", "smooth_quartz")
        for y in range(Y0, g["top"] + 1):                          # ladder up the tower
            d.set(25 - 1, y, 14, "ladder[facing=north,waterlogged=false]") if y >= 6 else None
        office(d, (22, 8, 24, 14), 7)
        shelf_wall(d, (22, 8, 24, 14), "w", 12, 3)
        d.set(23, 12, 11, "dark_oak_slab[type=top,waterlogged=false]")
        # laboratory
        lb_nf = 2 if L >= 4 else 1
        b2 = bldg(d, 26, 8, 38, 15, lb_nf, "gable", "x", mat=SB, up=SB, gable_end=SB)
        ext_door(d, 32, Y0, 8, "south")
        chimney(d, 38, 13, Y0, b2["ridge"] + 1)
        fur = max(0, need(d, "furnace") - 1)
        reqs = [("brewing_stand", 37, 10, None), ("water_cauldron", 37, 11, None), ("crafting_table", 37, 12, None)]
        reqs += [("furnace", 37, 13 + i, "west") if i < 1 else ("furnace", 36, 14, "north") for i in range(fur)]
        for it, x, z, f in reqs:
            keep(d, x - 1, Y0, z) if x == 37 else keep(d, x, Y0, z - 1)
        lab(d, (27, 9, 37, 14), Y0, req=reqs)
        d.sign(32, 5, 7, "north", ["LABORATORY"], "dark_oak")
        if lb_nf == 2:
            stair_up(d, 28, 14, Y0, 7, "east")
            dorm(d, (27, 9, 37, 13), 7, 5, head="n")
        path(d, 31, 0, 33, 7)
        flowerbed(d, 27, 5, 29, 6)
        flowerbed(d, 35, 5, 37, 6)
        post_lamp(d, 30, 5)
        post_lamp(d, 34, 5)
    # ---- L3: great hall (lecture) closes the quad; quad lawn with paths and strollers
    if L >= 3:
        h = bldg(d, 8, 32, 38, 40, 1, "gable", "x", mat=SB, up=SB, gable_end=SB, wh=6)
        for x in (22, 23, 24):                                      # louvre on the ridge
            for z in (35, 36, 37):
                d.set(x, h["ridge"], z, "dark_oak_planks")
        for x, z in ((22, 35), (24, 35), (22, 37), (24, 37)):
            d.set(x, h["ridge"] + 1, z, "dark_oak_fence")
        d.hip(22, 35, 24, 37, h["ridge"] + 2, "deepslate_tile_stairs", "deepslate_tile_slab", overhang=0)
        for x in range(10, 38, 4):                                  # buttresses
            for z, f in ((31, "south"), (41, "north")):
                for y in range(Y0, 6):
                    put(d, x, y, z, SB)
                put(d, x, 6, z, st("stone_brick_stairs", f))
        link(d, 23, Y0, 32, "south")
        lecture(d, (9, 33, 37, 39), Y0, "w", need=None, h=6)
        d.set(10, Y0, 35, "dark_oak_planks") if False else None
        for x in (11,):
            for z in range(33, 40):
                put(d, x, Y0, z, "red_carpet")
        shelf_wall(d, (9, 33, 37, 39), "e", Y0, 3)
        # quad
        lawn(d, 15, 16, 31, 31)
        path(d, 22, 16, 24, 31)
        path(d, 15, 23, 31, 24)
        for x, z in ((20, 23), (26, 23), (23, 19), (23, 28), (18, 24), (28, 24), (23, 17), (23, 30)):
            d.spot(x, Y0, z, "leisure")
            keep(d, x, Y0, z)
        for x, z in ((17, 18), (29, 18), (17, 29), (29, 29)):
            plant_tree(d, x, z)
        for x, z in ((20, 20), (26, 27)):
            park_bench(d, x, z, "x", "north" if z < 24 else "south")
        hedge(d, 15, 31, 21, 31)
        hedge(d, 25, 31, 31, 31)
    # ---- L4: library range (west of the quad), two storeys
    if L >= 4:
        lb = bldg(d, 8, 16, 14, 31, 2, "gable", "z", mat=SB, up=SB, gable_end=SB, ws=2)
        link(d, 14, Y0, 23, "west")
        r1 = (9, 17, 13, 30)
        shelf_wall(d, r1, "w", Y0, 3)
        for z in range(19, 29, 3):
            for x in (11, 12):
                d.bookshelf(x, Y0, z, 2)
        for z in (18, 21, 24, 27):
            desk(d, 13, Y0, z, "west", sit=True)
        stair_up(d, 10, 29, Y0, 7, "north") if False else stair_up(d, 9, 29, Y0, 7, "north") if False else None
        stair_up(d, 13, 30, Y0, 7, "north")
        shelf_wall(d, r1, "w", 7, 3)
        long_table_z(d, 11, 19, 24, 7)
        lights(d, r1, 7)
        rug_in(d, r1, Y0, ("green_carpet",), pattern="plain")
        # cloister arcade along the quad side of the library
        for z in range(16, 32):
            if z % 2:
                for y in range(Y0, 5):
                    put(d, 16, y, z, "stone_brick_wall")
            put(d, 16, 5, z, SB)
            put(d, 15, 5, z, slab("deepslate_tile_slab", "top")) if False else d.set(15, 5, z, slab("stone_brick_slab", "top"))
            d.set(16, 5, z, SB)
    # ---- L5: chapel with bell-cote (east of the quad), kitchen, master's garden, fountain
    if L >= 5:
        c = bldg(d, 32, 16, 38, 31, 1, "gable", "z", mat=SB, up=SB, gable_end=SB, wh=7, ws=2)
        link(d, 32, Y0, 23, "east")
        for z in range(18, 29, 2):                                  # pews
            for x in (34, 36, 37):
                if d.air(x, Y0, z):
                    d.chair(x, Y0, z, "south", "dark_oak")
        d.set(35, Y0, 30, "dark_oak_planks")
        put(d, 35, Y0 + 1, 30, "candle[candles=4,lit=false,waterlogged=false]")
        put(d, 34, Y0, 30, "candle[candles=3,lit=false,waterlogged=false]")
        put(d, 36, Y0, 30, "candle[candles=3,lit=false,waterlogged=false]")
        d.window(35, 4, 31, 35, 7, 31, "purple_stained_glass_pane")
        d.set(35, c["ridge"] + 1, 16, "stone_brick_wall")
        d.set(35, c["ridge"] + 2, 16, "stone_bricks")
        bell(d, 35, c["ridge"] + 1, 17) if False else None
        for x in (34, 36):
            d.set(x, c["ridge"] + 1, 16, "stone_brick_wall")
            d.set(x, c["ridge"] + 2, 16, "stone_brick_slab[type=bottom,waterlogged=false]")
        d.set(35, c["ridge"] + 1, 16, AIR)
        bell(d, 35, c["ridge"] + 1, 16)
        for z in range(18, 30):
            put(d, 35, Y0, z, "red_carpet")
        lights(d, (33, 17, 37, 30), Y0, 7)
        fountain(d, 23, 24, 2)
        for x, z in ((23, 21), (23, 27)):
            pass
        # master's garden west of the Old Schools
        lawn(d, 1, 16, 6, 44)
        for z in range(18, 44, 4):
            flowerbed(d, 2, z, 3, z + 1)
            plant_tree(d, 5, z + 2) if z % 8 == 2 else None
        for z in range(16, 45):
            put(d, 0, 2, z, "dark_oak_fence")
        path(d, 39, 0, 47, 3, border=False)
        for x in range(40, 47, 3):
            cart(d, x, 2)
        # the New Building: three-storey student residence south of the hall, garden between
        nb = bldg(d, 10, 45, 36, 52, 3, "gable", "x", mat=SB, up=SB, gable_end=SB)
        ext_door(d, 23, Y0, 45, "south", double=True)
        arch(d, 23, Y0, 40, "south")
        path(d, 23, 41, 24, 44)
        lawn(d, 8, 41, 38, 44)
        flowerbed(d, 9, 42, 20, 43)
        flowerbed(d, 27, 42, 37, 43)
        stair_up(d, 12, 51, Y0, 7, "east")
        stair_up(d, 33, 51, 7, 12, "west")
        lounge(d, (11, 46, 22, 50), Y0)
        table_set(d, (25, 46, 35, 50), Y0, "dining")
        dorm(d, (11, 46, 35, 50), 7, 10, head="n")
        dorm(d, (11, 46, 35, 50), 12, 10, head="n")
        for x in (14, 32):
            chimney(d, x, 52, Y0 + 1, nb["ridge"] + 1)
    shelf_runs(d, [], 0)
    return d


def uni_neoterra(rel, L):
    """Research campus: pavilion -> lab block & bridge -> lecture theatre & quad -> extra storeys -> dorm tower,
    student union, sports court."""
    d = new("Neoterra", rel, (53, 40, 55), paving="smooth_stone")
    Q = "smooth_quartz"
    pv_nf = 3 if L >= 4 else 1
    p = bldg(d, 6, 6, 18, 14, pv_nf, "flat", glassy=True, win="nsw")
    ext_door(d, 11, Y0, 6, "south", double=True)
    d.sign(12, 6, 5, "north", ["INSTITUTE OF", "SCIENCE"], "birch", glow=True, color="cyan")
    for x in range(9, 16):
        for z in (3, 4, 5):
            put(d, x, 6, z, slab("smooth_quartz_slab", "top"))
    d.hut(7, Y0, 7)
    keep(d, 8, Y0, 7)
    d.item(17, Y0, 7, "lectern", "west")
    keep(d, 16, Y0, 7)
    d.rack(7, Y0, 13, "north")
    keep(d, 7, Y0, 12)
    d.item(17, Y0, 13, "furnace", "west")
    keep(d, 16, Y0, 13)
    if pv_nf > 1:
        stair_up(d, 8, 9, Y0, 7, "south")
        stair_up(d, 16, 12, 7, 12, "north")
    for x in range(10, 15):
        d.table(x, Y0, 10, "birch", "block", Q)
    for x in range(10, 15):
        d.chair(x, Y0, 9, "north", "mangrove")
        d.chair(x, Y0, 11, "south", "mangrove")
    shelf_wall(d, (7, 7, 17, 13), "s", Y0, 3)
    rug_in(d, (9, 8, 15, 12), Y0, ("cyan_carpet",), inset=0, pattern="plain")
    corners(d, (7, 7, 17, 13), Y0, ["potted_bamboo"])
    if pv_nf > 1:
        r2 = (7, 7, 17, 13)
        table_set(d, r2, 7, "dining")
        lights(d, r2, 7)
        office(d, (7, 7, 11, 13), 12)
        office(d, (13, 7, 17, 13), 12, desk_side="s")
        d.fill(12, 12, 7, 12, 15, 13, "light_gray_stained_glass")
        link(d, 12, 12, 10, "east") if False else arch(d, 12, 12, 10, "east")
        roof_garden(d, p, "garden")
    path(d, 10, 0, 13, 5, "smooth_stone")
    for x in (4, 20):
        post_lamp(d, x, 4)
    if L >= 2:
        lb_nf = {2: 1, 3: 1, 4: 2, 5: 3}[L]
        b2 = bldg(d, 26, 6, 40, 14, lb_nf, "flat", glassy=True, win="nse")
        d.box(18, Y0, 8, 26, 5, 12, "glass", floor="polished_diorite")
        d.fill(18, 6, 8, 26, 6, 12, Q)
        d.clear(19, Y0, 9, 25, 5, 11)
        for x in (18, 26):
            arch(d, x, Y0, 10, "east")
        for x in range(19, 26, 2):
            put(d, x, Y0, 9, "potted_bamboo")
            put(d, x, 5, 10, "sea_lantern") if False else d.set(x, 6, 10, "sea_lantern")
        ext_door(d, 33, Y0, 6, "south", double=True)
        d.sign(33, 6, 5, "north", ["LABS"], "birch", glow=True, color="cyan")
        fur = max(0, need(d, "furnace") - 1)
        reqs = [("brewing_stand", 39, 8, None), ("water_cauldron", 39, 9, None), ("crafting_table", 39, 10, None)]
        reqs += [("furnace", 39, 11 + i, "west") for i in range(fur)]
        for it, x, z, f in reqs:
            keep(d, x - 1, Y0, z)
        lab(d, (27, 7, 39, 13), Y0, req=reqs)
        if lb_nf > 1:
            stair_up(d, 28, 13, Y0, 7, "east")
            classroom(d, (27, 7, 39, 12), 7, board="e")
            roof_garden(d, b2, "solar")
        if lb_nf > 2:
            stair_up(d, 38, 13, 7, 12, "west")
            office(d, (27, 7, 32, 13), 12)
            office(d, (34, 7, 39, 13), 12, desk_side="s")
            d.fill(33, 12, 7, 33, 15, 13, "light_gray_stained_glass")
            arch(d, 33, 12, 10, "east")
        for x in (22, 44):
            plant_tree(d, x, 3)
    if L >= 3:
        X1, X2, Z1, Z2 = 14, 38, 38, 47
        bldg(d, X1, Z1, X2, Z2, 1, "flat", wh=8, win="s", ws=4)
        shelf_wall(d, (X1 + 1, Z1 + 1, X2 - 1, Z2 - 1), "w", Y0, 3)
        shelf_wall(d, (X1 + 1, Z1 + 1, X2 - 1, Z2 - 1), "e", Y0, 3)
        for x in range(X1, X2 + 1):
            d.set(x, 9, Z1, "cyan_terracotta")
        ext_door(d, 26, Y0, Z1, "north", double=True)
        for x in range(18, 35):
            d.set(x, 6, Z1 + 1, "black_concrete")
            d.set(x, 7, Z1 + 1, "black_concrete")
        d.set(26, 7, Z1 + 1, "sea_lantern")
        put(d, 20, Y0, Z1 + 2, Q)
        for k in range(3):                                          # raked tiers rising south
            zs = Z1 + 4 + 2 * k
            for z in (zs, zs + 1):
                for x in range(X1 + 1, X2):
                    for y in range(Y0, Y0 + k):
                        d.set(x, y, z, Q)
            for x in range(X1 + 3, X2 - 2):
                if x in (20, 26, 32):
                    continue
                d.chair(x, Y0 + k, zs, "south", "birch")
        lights(d, (X1 + 1, Z1 + 1, X2 - 1, Z2 - 1), Y0, 8)
        lawn(d, 6, 16, 46, 36)
        path(d, 25, 15, 27, 37)
        path(d, 6, 26, 46, 26)
        for x, z in ((12, 26), (18, 26), (34, 26), (40, 26), (26, 19), (26, 23), (26, 30), (26, 34)):
            d.spot(x, Y0, z, "leisure")
            keep(d, x, Y0, z)
        for x, z in ((10, 20), (42, 20), (10, 32), (42, 32), (18, 20), (34, 32)):
            plant_tree(d, x, z)
        for x, z in ((20, 24), (30, 24)):
            park_bench(d, x, z, "x", "north")
        for x, z in ((20, 28), (30, 28)):
            park_bench(d, x, z, "x", "south")
        fountain(d, 26, 26, 2) if L >= 4 else None
    if L >= 4:
        un = bldg(d, 6, 17, 14, 34, 2, "flat", glassy=True, win="nsew")
        ext_door(d, 14, Y0, 25, "west", double=True, along="z")
        kitchen(d, (7, 18, 13, 21), Y0)
        table_set(d, (7, 23, 13, 33), Y0, "dining")
        stair_up(d, 7, 33, Y0, 7, "north")
        lounge(d, (7, 18, 13, 26), 7)
        table_set(d, (7, 27, 13, 33), 7, "dining")
        roof_garden(d, un, "garden")
        d.sign(14, 6, 21, "east", ["STUDENT", "UNION"], "birch", glow=True, color="cyan")
    if L >= 5:
        dt = bldg(d, 38, 17, 46, 34, 6, "flat", glassy=True, win="nsew")
        ext_door(d, 38, Y0, 25, "east")
        for k in range(5):
            stair_up(d, 39 + (k % 2) * 6, 18 if k % 2 == 0 else 33, Y0 + 5 * k, Y0 + 5 * k + 5,
                     "south" if k % 2 == 0 else "north")
        for k in range(6):
            y = Y0 + 5 * k
            if k == 0:
                lounge(d, (39, 19, 45, 32), y)
            else:
                dorm(d, (39, 20, 45, 31), y, 6, head="e")
        roof_garden(d, dt, "solar")
        # sports court beside the street
        for x in range(42, 52):
            for z in range(1, 15):
                edge = x in (42, 51) or z in (1, 14) or z == 8
                d.set(x, 1, z, "white_concrete" if edge else "light_blue_terracotta")
        for z in (2, 13):
            put(d, 46, 2, z, "iron_bars")
            put(d, 46, 3, z, "iron_bars")
            put(d, 46, 4, z, "white_stained_glass")
    return d


def uni_cascadia(rel, L):
    """Timber college: lodges round a quad joined by covered boardwalks."""
    d = new("Cascadia", rel, (53, 30, 55), paving="coarse_dirt")
    st_nf = 2 if L >= 4 else 1
    b = bldg(d, 6, 6, 18, 14, st_nf, "gable", "x")
    ext_door(d, 12, Y0, 6, "south")
    d.fill(5, 1, 2, 19, 1, 5, "spruce_planks")                     # porch
    for x in (5, 19, 9, 15):
        for y in range(Y0, 6):
            put(d, x, y, 2, log("spruce_log"))
    for x in range(4, 21):
        d.set(x, 6, 1, st("spruce_stairs", "south"))
        for z in range(2, 6):
            d.set(x, 6, z, slab("spruce_slab"))
    d.sign(12, 5, 5, "north", ["TIMBERLINE", "COLLEGE"], "spruce")
    d.hut(7, Y0, 7)
    keep(d, 8, Y0, 7)
    d.item(17, Y0, 7, "lectern", "west")
    keep(d, 16, Y0, 7)
    d.rack(7, Y0, 13, "north")
    keep(d, 7, Y0, 12)
    d.item(17, Y0, 13, "furnace", "west")
    keep(d, 16, Y0, 13)
    d.hearth(12, Y0, 13, "north", b["ridge"] + 1, "cobblestone", "campfire")
    chimney(d, 12, 14, Y0, b["ridge"] + 1)
    if st_nf > 1:
        stair_up(d, 16, 8, Y0, 7, "south")
    for x in range(10, 15):
        d.table(x, Y0, 9, "spruce", "block", "stripped_spruce_wood[axis=y]")
        d.chair(x, Y0, 8, "north", "spruce")
        d.chair(x, Y0, 10, "south", "spruce")
    d.chair(11, Y0, 11, "south", "spruce", arms=True) if False else None
    shelf_wall(d, (7, 7, 17, 13), "w", Y0, 3, skip=[(7, 7), (7, 13)])
    shelf_wall(d, (7, 7, 17, 13), "e", Y0, 2, skip=[(17, 7), (17, 13)])
    rug_in(d, (9, 11, 15, 12), Y0, ("brown_carpet",), inset=0, pattern="plain")
    if st_nf > 1:
        dorm(d, (7, 7, 17, 13), 7, 4, head="n")
    if L >= 2:
        c_nf = 1
        b2 = bldg(d, 30, 6, 42, 14, c_nf, "gable", "x")
        ext_door(d, 36, Y0, 6, "south")
        d.sign(36, 5, 5, "north", ["CHEMISTRY"], "spruce")
        chimney(d, 42, 10, Y0, b2["ridge"] + 1)
        fur = max(0, need(d, "furnace") - 1)
        reqs = [("brewing_stand", 41, 8, None), ("water_cauldron", 41, 9, None), ("crafting_table", 41, 10, None)]
        reqs += [("furnace", 41, 11 + i, "west") for i in range(fur)]
        for it, x, z, f in reqs:
            keep(d, x - 1, Y0, z)
        lab(d, (31, 7, 41, 13), Y0, req=reqs)
        shelf_wall(d, (31, 7, 41, 13), "s", Y0, 2, skip=[(31, 13), (41, 13)])
        # covered boardwalk
        for x in range(19, 30):
            for z in range(8, 13):
                d.set(x, 1, z, "spruce_planks")
                d.set(x, 6, z, slab("spruce_slab"))
            for z in (8, 12):
                if x % 3 == 1:
                    for y in range(Y0, 6):
                        d.set(x, y, z, log("spruce_log"))
                else:
                    d.set(x, Y0, z, "spruce_fence")
        for x0 in (18, 30):
            link(d, x0, Y0, 10, "east" if x0 == 18 else "west")
        for x in range(20, 30, 4):
            d.set(x, 5, 10, "lantern[hanging=true,waterlogged=false]")
        for x in (24,):
            d.set(x, Y0, 8, AIR)
            d.set(x, Y0, 12, AIR)
        for x, z in ((22, 3), (27, 3), (46, 4)):
            plant_tree(d, x, z)
    if L >= 3:
        lec = bldg(d, 12, 38, 38, 46, 1, "gable", "x", wh=5)
        ext_door(d, 25, Y0, 38, "north", double=True)
        lecture(d, (13, 39, 37, 45), Y0, "w", h=5)
        shelf_wall(d, (13, 39, 37, 45), "e", Y0, 3)
        chimney(d, 12, 42, Y0, lec["ridge"] + 1)
        lawn(d, 6, 16, 46, 36, "grass_block[snowy=false]")
        for x in range(6, 47):
            for z in range(16, 37):
                if (x * 7 + z * 3) % 11 == 0:
                    d.set(x, 1, z, "moss_block")
        path(d, 24, 15, 26, 37, "spruce_planks", border=False)
        cx, cz = 15, 26
        d.set(cx, 1, cz, "cobblestone")
        d.set(cx, Y0, cz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        for x in range(cx - 1, cx + 2):
            for z in range(cz - 1, cz + 2):
                if (x, z) != (cx, cz):
                    d.set(x, 1, z, "gravel")
        for (x, z, ax) in ((cx - 3, cz, "z"), (cx + 3, cz, "z"), (cx, cz - 3, "x"), (cx, cz + 3, "x"),
                           (cx - 3, cz - 1, "z"), (cx + 3, cz + 1, "z")):
            d.set(x, Y0, z, log("stripped_spruce_log", ax))
        for x, z in ((cx - 2, cz - 2), (cx + 2, cz - 2), (cx - 2, cz + 2), (cx + 2, cz + 2), (32, 22), (36, 28),
                     (25, 20), (25, 32)):
            d.spot(x, Y0, z, "leisure")
            keep(d, x, Y0, z)
        for x, z in ((34, 18), (42, 24), (30, 33), (9, 33), (20, 18)):
            plant_tree(d, x, z)
    if L >= 4:
        rl = bldg(d, 6, 17, 13, 34, 2, "gable", "z")
        ext_door(d, 13, Y0, 25, "west")
        r1 = (7, 18, 12, 33)
        stair_up(d, 12, 33, Y0, 7, "north") if False else stair_up(d, 8, 22, Y0, 7, "south")
        shelf_wall(d, r1, "w", Y0, 3)
        for z in range(19, 33, 4):
            desk(d, 11, Y0, z, "west")
        shelf_wall(d, r1, "w", 7, 2)
        shelf_wall(d, r1, "e", 7, 1)
        lights(d, r1, Y0)
        rug_in(d, r1, Y0, ("green_carpet",), pattern="plain")
        table_set(d, (8, 19, 11, 32), 7, "dining")
    if L >= 4:
        bk_nf = 2 if L >= 5 else 1
        bk = bldg(d, 38, 17, 46, 34, bk_nf, "gable", "z")
        ext_door(d, 38, Y0, 25, "east")
        if bk_nf > 1:
            stair_up(d, 45, 19, Y0, 7, "south")
            dorm(d, (39, 18, 45, 33), 7, 7, head="e")
        dorm(d, (39, 18, 45, 33), Y0, 7, head="e")
        chimney(d, 46, 30, Y0, bk["ridge"] + 1)
    if L >= 5:
        # mess hall lodge on the street, east of the chemistry cabin
        mh = bldg(d, 44, 4, 52, 15, 1, "gable", "z")
        ext_door(d, 48, Y0, 4, "south")
        kitchen(d, (45, 5, 51, 8), Y0)
        table_set(d, (45, 9, 51, 14), Y0, "dining")
        chimney(d, 52, 12, Y0, mh["ridge"] + 1)
        # fire-lookout tower at the quad corner
        tx1, tz1 = 31, 30
        for x, z in ((tx1, tz1), (tx1 + 4, tz1), (tx1, tz1 + 4), (tx1 + 4, tz1 + 4)):
            for y in range(Y0, 16):
                d.set(x, y, z, log("spruce_log"))
        for y in (7, 12):
            for a in range(1, 4):
                for (x, z, ax) in ((tx1 + a, tz1, "x"), (tx1 + a, tz1 + 4, "x"), (tx1, tz1 + a, "z"), (tx1 + 4, tz1 + a, "z")):
                    d.set(x, y, z, log("spruce_log", ax))
        d.fill(tx1, 15, tz1, tx1 + 4, 15, tz1 + 4, "spruce_planks")
        for x in range(tx1, tx1 + 5):
            for z in range(tz1, tz1 + 5):
                if x in (tx1, tx1 + 4) or z in (tz1, tz1 + 4):
                    d.set(x, 16, z, "spruce_fence")
        d.hip(tx1, tz1, tx1 + 4, tz1 + 4, 19, "dark_oak_stairs", "dark_oak_slab", overhang=1)
        for x, z in ((tx1, tz1), (tx1 + 4, tz1), (tx1, tz1 + 4), (tx1 + 4, tz1 + 4)):
            for y in range(16, 19):
                d.set(x, y, z, log("spruce_log"))
        d.set(tx1 + 2, 19, tz1 + 2, "spruce_planks")
        bell(d, tx1 + 2, 18, tz1 + 2)
        # faculty lodge (two storeys) in the south-east corner
        fl = bldg(d, 40, 39, 52, 51, 2, "gable", "x")
        ext_door(d, 48, Y0, 39, "south")
        stair_up(d, 42, 50, Y0, 7, "east")
        office(d, (41, 40, 45, 45), Y0)
        office(d, (47, 40, 51, 45), Y0, desk_side="s")
        lounge(d, (41, 46, 51, 50), Y0) if False else table_set(d, (46, 46, 51, 50), Y0, "dining")
        d.fill(46, Y0, 40, 46, 5, 45, "spruce_planks")
        arch(d, 46, Y0, 42, "east")
        dorm(d, (41, 40, 51, 50), 7, 8, head="n")
        chimney(d, 52, 45, Y0, fl["ridge"] + 1)
        # covered boardwalk round the quad (posts, rail, slab roof)
        for x in range(14, 38):
            for z in (15, 37):
                d.set(x, 1, z, "spruce_planks")
                d.set(x, 6, z, slab("spruce_slab"))
                if x % 4 == 2:
                    for y in range(Y0, 6):
                        d.set(x, y, z, log("spruce_log"))
                    d.set(x, 5, z + (1 if z == 15 else -1), "lantern[hanging=false,waterlogged=false]") if False else None
        for z in range(15, 38):
            for x in (14, 37):
                d.set(x, 1, z, "spruce_planks")
                d.set(x, 6, z, slab("spruce_slab"))
                if z % 4 == 3:
                    for y in range(Y0, 6):
                        d.set(x, y, z, log("spruce_log"))
        for x in range(16, 37, 4):
            d.set(x, 5, 15, "lantern[hanging=true,waterlogged=false]")
            d.set(x, 5, 37, "lantern[hanging=true,waterlogged=false]")
    return d


@design("university")
def university_v2(pack, rel, L):
    return common_materials({"Hearthwood": uni_hearthwood, "Cascadia": uni_cascadia, "Neoterra": uni_neoterra}[pack](rel, L))
