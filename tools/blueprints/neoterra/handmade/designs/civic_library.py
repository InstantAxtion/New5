"""Civic: library (hand-designed, all packs). Shared shells/helpers live in _civic_common.py."""
from designs import _civic_common as _c
globals().update({k: v for k, v in vars(_c).items() if not k.startswith("__")})
from hm import design  # noqa: E402,F401


def lib_hearthwood(rel, L):
    d = new("Hearthwood", rel, (49, 34, 55))
    SS = "smooth_sandstone"
    hnf = 2 if L >= 3 else 1
    h = bldg(d, 16, 8, 30, 20, hnf, "gable", "x", win="nsew", ws=2)
    ext_door(d, 23, Y0, 8, "south")
    d.sign(23, 5, 7, "north", ["LIBRARY", "", "Sapere aude"], "dark_oak")
    for x in (21, 25):                                              # columned porch
        for y in range(Y0, 6):
            put(d, x, y, 5, "quartz_pillar[axis=y]")
    d.fill(21, 6, 5, 25, 6, 7, "cut_sandstone")
    for x in range(21, 26):
        d.set(x, 7, 5, st("sandstone_stairs", "south"))
    d.fill(21, 1, 4, 25, 1, 7, "cut_sandstone")
    d.hut(17, Y0, 9)
    keep(d, 18, Y0, 9)
    d.item(23, Y0, 18, "lectern", "north")
    keep(d, 23, Y0, 17)
    # stalls from both long walls with reading desks in the window bays
    for z in (11, 15):
        stall_row(d, 17, 19, z, Y0, 3)
        stall_row(d, 27, 29, z, Y0, 3)
    for z in (12, 13, 16, 17):
        desk(d, 17, Y0, z, "east")
        desk(d, 29, Y0, z, "west")
    for z in range(9, 20):
        put(d, 23, Y0, z, "red_carpet")
    rug_in(d, (21, 10, 25, 19), Y0, ("red_carpet", "green_carpet"))
    if hnf > 1:
        stair_up(d, 21, 19, Y0, 7, "west") if False else stair_up(d, 20, 19, Y0, 7, "east")
        shelf_wall(d, (17, 9, 29, 19), "n", 7, 3)
        shelf_wall(d, (17, 9, 29, 19), "w", 7, 3)
        shelf_wall(d, (17, 9, 29, 19), "e", 7, 3)
        long_table(d, 21, 13, 25, 7, "dark_oak")
        lights(d, (17, 9, 29, 19), 7)
    for x in (14, 32):
        post_lamp(d, x, 5)
    hedge(d, 16, 2, 20, 2)
    hedge(d, 26, 2, 30, 2)
    flowerbed(d, 16, 3, 20, 4)
    flowerbed(d, 26, 3, 30, 4)
    if L >= 2:
        swnf = 2 if L >= 4 else 1
        sw = bldg(d, 30, 9, 42, 19, swnf, "gable", "z", win="nse")
        link(d, 30, Y0, 14, "east")
        for z in range(10, 19, 3):
            stall_row(d, 32, 40, z, Y0, 3)
        if swnf > 1:
            stair_up(d, 41, 10, Y0, 7, "south")
            office(d, (31, 10, 40, 18), 7)
            table_set(d, (31, 10, 40, 18), 7, "study", sit=False)
        d.sign(36, 5, 8, "north", ["STACKS"], "dark_oak")
        chimney(d, 42, 14, Y0, sw["ridge"] + 1)
    if L >= 4:
        # the rotunda (Radcliffe-style domed reading room) behind the hall
        cx, cz, R = 23, 30, 7
        for y in range(Y0, 11):
            for x in range(cx - R, cx + R + 1):
                for z in range(cz - R, cz + R + 1):
                    dd = (x - cx) ** 2 + (z - cz) ** 2
                    if (R - 0.5) ** 2 <= dd <= (R + 0.5) ** 2:
                        d.set(x, y, z, SS if not (y in (4, 5, 6, 7) and (x + z) % 3 == 0) else "glass_pane")
                    elif dd < (R - 0.5) ** 2:
                        d.set(x, y, z, AIR)
                        if y == Y0:
                            d.set(x, 1, z, "polished_andesite" if (x + z) % 2 else "smooth_stone")
        for k in range(0, R + 1):                                   # stepped dome
            y = 11 + k
            r = R - k
            for x in range(cx - R, cx + R + 1):
                for z in range(cz - R, cz + R + 1):
                    dd = (x - cx) ** 2 + (z - cz) ** 2
                    if (r - 0.6) ** 2 <= dd <= (r + 0.6) ** 2 or (r <= 0 and dd == 0):
                        d.set(x, y, z, "mud_bricks" if k < R - 1 else "cut_sandstone")
        d.set(cx, 11 + R + 1, cz, "lantern[hanging=false,waterlogged=false]")
        d.fill(cx - 1, Y0, cz + R, cx + 1, 4, cz + R, AIR)
        for x in range(cx - 1, cx + 2):
            for z in range(cz + 2, cz + R + 2):
                keep(d, x, Y0, z, 3)
        d.fill(cx - 1, Y0, cz - R, cx + 1, 4, cz - R, AIR)
        d.fill(cx - 1, Y0, h["z2"], cx + 1, 4, h["z2"], AIR)
        for x in range(cx - 1, cx + 2):
            for z in range(h["z2"], cz - 1):
                d.set(x, 1, z, "polished_andesite")
                keep(d, x, Y0, z, 3)
        for z in range(h["z2"] + 1, cz - R):
            for x in (cx - 2, cx + 2):
                for y in range(Y0, 6):
                    d.set(x, y, z, SS)
            for x in range(cx - 2, cx + 3):
                d.set(x, 6, z, "cut_sandstone")
        for x in range(cx - R + 1, cx + R):                          # radial presses
            for z in range(cz - R + 1, cz + R):
                dd = (x - cx) ** 2 + (z - cz) ** 2
                if (R - 1.5) ** 2 <= dd < (R - 0.5) ** 2 and (x, Y0, z) not in d.res:
                    for k in range(4):
                        if d.air(x, Y0 + k, z):
                            d.bookshelf(x, Y0 + k, z)
        d.item(cx, Y0, cz, "enchanting_table")
        for x, z, b in ((cx - 2, cz, "east"), (cx + 2, cz, "west"), (cx, cz + 2, "south")):
            put(d, x, Y0, z, slab("dark_oak_slab", "top"))
        for x, z, back in ((cx - 3, cz, "west"), (cx + 3, cz, "east"), (cx, cz + 3, "south"), (cx - 3, cz + 2, "west"),
                           (cx + 3, cz + 2, "east"), (cx - 2, cz + 3, "south"), (cx + 2, cz + 3, "south")):
            if d.air(x, Y0, z):
                d.chair(x, Y0, z, back, "dark_oak")
        for z in range(cz - 4, cz + 5, 4):
            put(d, cx, 10, z, "chain[axis=y,waterlogged=false]")
            put(d, cx, 9, z, "lantern[hanging=true,waterlogged=false]")
    if L >= 5:
        # manuscripts wing (two storeys) + cloister garden + librarian's cottage
        mw = bldg(d, 4, 9, 16, 21, 2, "gable", "z", win="nsw", mat="smooth_sandstone", up="calcite")
        link(d, 16, Y0, 14, "west")
        stair_up(d, 5, 20, Y0, 7, "north")
        for z in range(10, 20, 3):
            stall_row(d, 7, 14, z, Y0, 2)
        office(d, (5, 10, 15, 20), 7)
        table_set(d, (5, 10, 15, 20), 7, "study", sit=False)
        lawn(d, 2, 24, 14, 44)
        for x in range(2, 15):
            put(d, x, 2, 44, "sandstone_wall")
        for z in range(24, 45):
            put(d, 2, 2, z, "sandstone_wall")
        path(d, 8, 23, 9, 43)
        for z in range(26, 43, 4):
            flowerbed(d, 4, z, 6, z + 1)
            flowerbed(d, 11, z, 13, z + 1)
        plant_tree(d, 5, 40)
        plant_tree(d, 12, 32)
        lc = bldg(d, 34, 34, 44, 44, 2, "gable", "x", mat="calcite", up="calcite")
        ext_door(d, 39, Y0, 34, "south")
        stair_up(d, 35, 43, Y0, 7, "east")
        lounge(d, (35, 35, 43, 39), Y0)
        kitchen(d, (35, 40, 43, 43), Y0)
        dorm(d, (35, 35, 43, 43), 7, 2, head="n")
        chimney(d, 44, 39, Y0, lc["ridge"] + 1)
        flowerbed(d, 35, 30, 43, 32)
        for x in range(34, 45):
            put(d, x, 2, 29, "dark_oak_fence")
    shelf_runs(d, [], 0)
    return d


def lib_neoterra(rel, L):
    d = new("Neoterra", rel, (51, 45, 51), paving="smooth_stone")
    Q = "smooth_quartz"
    nf = 2 if L >= 3 else 1
    p = bldg(d, 16, 8, 30, 18, nf, "flat", glassy=True, win="nsew")
    ext_door(d, 22, Y0, 8, "south", double=True)
    d.sign(22, 6, 7, "north", ["PUBLIC", "LIBRARY"], "birch", glow=True, color="orange")
    d.sign(23, 6, 7, "north", ["", "open late"], "birch", glow=True, color="orange")
    for x in range(19, 28):
        for z in range(4, 8):
            put(d, x, 6, z, slab("smooth_quartz_slab", "top"))
    d.hut(17, Y0, 9)
    keep(d, 18, Y0, 9)
    for x in range(25, 29):
        d.set(x, Y0, 11, Q)
    d.item(26, Y0, 10, "lectern", "north")
    keep(d, 26, Y0, 9)
    d.chair(27, Y0, 12, "south", "mangrove", sit=False)
    for tz in (14,):
        for tx in range(19, 24):
            d.table(tx, Y0, tz, "birch", "block", Q)
            d.chair(tx, Y0, tz - 1, "north", "mangrove")
            d.chair(tx, Y0, tz + 1, "south", "mangrove")
    shelf_wall(d, (17, 9, 29, 17), "s", Y0, 3)
    shelf_wall(d, (17, 9, 29, 17), "w", Y0, 2, skip=[(17, 9)])
    corners(d, (17, 9, 29, 17), Y0, ["potted_bamboo"])
    for x in (13, 33):
        post_lamp(d, x, 5)
        put(d, x, 2, 3, "moss_block")
        put(d, x, 3, 3, "flowering_azalea")
    if nf > 1:
        stair_up(d, 29, 12, Y0, 7, "south") if False else stair_up(d, 28, 16, Y0, 7, "west")
        for z in (10, 13):
            stall_row(d, 18, 26, z, 7, 3)
        shelf_wall(d, (17, 9, 29, 17), "w", 7, 3)
        lights(d, (17, 9, 29, 17), 7)
        roof_garden(d, p, "garden")
    if L >= 2:
        sb = bldg(d, 30, 8, 40, 18, nf, "flat", glassy=False, win="ns", mat="orange_terracotta", up="orange_terracotta")
        link(d, 30, Y0, 13, "east")
        for z in (10, 12, 15, 17):
            stall_row(d, 32, 38, z, Y0, 3)
        if nf > 1:
            link(d, 30, 7, 13, "east")
            for z in (10, 12, 15, 17):
                stall_row(d, 32, 38, z, 7, 3)
            roof_garden(d, sb, "solar")
        d.sign(35, 6, 7, "north", ["STACKS"], "birch", glow=True, color="orange")
    if L >= 4:
        tw = bldg(d, 16, 18, 28, 32, 5, "flat", glassy=True, win="esw")
        link(d, 22, Y0, 18, "south")
        for k in range(4):
            stair_up(d, 17 if k % 2 == 0 else 27, 19 if k % 2 == 0 else 31, Y0 + 5 * k, Y0 + 5 * k + 5,
                     "south" if k % 2 == 0 else "north")
        d.item(22, Y0, 25, "enchanting_table")
        for x, z, back in ((20, 25, "west"), (24, 25, "east"), (22, 27, "south"), (22, 23, "north")):
            d.chair(x, Y0, z, back, "mangrove")
        rug_in(d, (19, 22, 25, 28), Y0, ("orange_carpet", "white_carpet"), inset=0)
        for k in range(1, 5):
            y = Y0 + 5 * k
            for z in (21, 24, 27, 30):
                stall_row(d, 19, 25, z, y, 2 if k % 2 else 3)
            lights(d, (17, 19, 27, 31), y)
        roof_garden(d, tw, "garden")
        d.sign(22, 6, 33, "south", ["MEDIA", "TOWER"], "birch", glow=True, color="orange")
    if L >= 5:
        au = bldg(d, 30, 20, 46, 32, 2, "flat", wh=6, win="e")
        stair_up(d, 45, 22, Y0, 8, "south")
        table_set(d, (31, 21, 45, 31), 8, "study", sit=False)
        link(d, 28, Y0, 26, "east") if False else ext_door(d, 38, Y0, 32, "north", double=True)
        lecture(d, (31, 21, 44, 31), Y0, "n", h=6)
        roof_garden(d, au, "garden")
        lawn(d, 2, 34, 48, 49)
        path(d, 2, 40, 48, 41, "polished_diorite")
        for x in range(4, 48, 7):
            plant_tree(d, x, 37)
            park_bench(d, x + 2, 43, "x", "south")
            flowerbed(d, x, 46, x + 3, 47, ("allium", "azure_bluet", "white_tulip", "orange_tulip"))
            post_lamp(d, x + 5, 39)
        # café kiosk
        ck = bldg(d, 4, 8, 12, 16, 1, "flat", glassy=True, win="nse")
        ext_door(d, 8, Y0, 8, "south")
        kitchen(d, (5, 9, 11, 10), Y0)
        table_set(d, (5, 11, 11, 15), Y0, "dining")
        for x in range(4, 13):
            for z in range(4, 8):
                put(d, x, 6, z, f"{('orange' if x % 2 else 'white')}_concrete" if z == 4 else slab("smooth_quartz_slab", "top"))
        d.sign(8, 6, 7, "north", ["CAFE"], "birch", glow=True, color="orange") if False else None
    return d


def lib_cascadia(rel, L):
    d = new("Cascadia", rel, (55, 30, 55), paving="coarse_dirt")
    X1, X2, Z1, Z2 = 16, 34, 6, 18
    ridge = aframe(d, X1, Z1, X2, Z2)
    mid = (X1 + X2) // 2
    d.double_door(mid, Y0, Z1, "x", "south", "spruce")
    keep(d, mid, Y0, Z1 + 1, 3)
    keep(d, mid + 1, Y0, Z1 + 1, 3)
    d.sign(mid, 8, Z1 - 1, "north", ["READING", "LODGE"], "spruce")
    for x in range(X1, X2 + 1):                                     # front deck
        for z in range(Z1 - 4, Z1):
            d.set(x, 1, z, "spruce_planks")
        if abs(x - mid - 0.5) > 1.5:
            put(d, x, Y0, Z1 - 4, "spruce_fence")
    for y in range(Y0, ridge + 2):
        for x in (mid, mid + 1):
            if y < ridge - 1 or x == mid:
                d.set(x, y, Z2, "cobblestone" if (x + y) % 3 else "mossy_cobblestone")
    d.hearth(mid, Y0, Z2 - 1, "north", ridge + 1, "cobblestone", "campfire")
    d.hut(X1 + 4, Y0, Z1 + 1)
    keep(d, X1 + 5, Y0, Z1 + 1)
    d.item(X2 - 4, Y0, Z1 + 1, "lectern", "west")
    keep(d, X2 - 5, Y0, Z1 + 1)
    for z in range(Z1 + 1, Z2):                                      # eave stacks
        for (x, hh) in ((X1 + 1, 1), (X1 + 2, 2), (X1 + 3, 3), (X2 - 1, 1), (X2 - 2, 2), (X2 - 3, 3)):
            if (x, Y0, z) not in d.res:
                for k in range(hh):
                    if d.air(x, Y0 + k, z):
                        d.bookshelf(x, Y0 + k, z)
    for z in (Z1 + 3, Z1 + 6):
        for tx in (mid - 3, mid + 4):
            d.table(tx, Y0, z, "spruce", "post")
            d.chair(tx - 1, Y0, z, "west", "spruce")
            d.chair(tx + 1, Y0, z, "east", "spruce")
    rug_in(d, (mid - 1, Z1 + 2, mid + 2, Z2 - 3), Y0, ("brown_carpet", "green_carpet"), inset=0)
    for z in range(Z1 + 2, Z2 - 1, 4):
        for x in range(X1 + 7, X2 - 6):
            d.set(x, 9, z, log("stripped_spruce_log", "x"))
        d.set(mid, 8, z, "lantern[hanging=true,waterlogged=false]")
    for x in (X1 - 2, X2 + 2):
        post_lamp(d, x, Z1 - 2)
    if L >= 2:
        # children's A-frame on the east, joined by a covered walk
        r2 = aframe(d, 38, 8, 50, 16)
        d.door(44, Y0, 8, "south", "spruce")
        keep(d, 44, Y0, 9, 3)
        for z in range(9, 16):
            for (x, hh) in ((39, 1), (40, 2), (49, 1), (48, 2)):
                for k in range(hh):
                    if d.air(x, Y0 + k, z):
                        d.bookshelf(x, Y0 + k, z)
        rug_in(d, (42, 10, 46, 14), Y0, ("lime_carpet", "yellow_carpet", "light_blue_carpet"), inset=0, pattern="border")
        for x in (42, 46):
            d.chair(x, Y0, 15, "south", "spruce", sit=False)
        d.sign(44, 7, 7, "north", ["STORY", "CORNER"], "spruce")
        for x in (37, 51):
            post_lamp(d, x, 6)
        flowerbed(d, 38, 5, 41, 6, ("fern", "blue_orchid", "allium", "dandelion"))
        flowerbed(d, 47, 5, 50, 6, ("fern", "blue_orchid", "allium", "dandelion"))
        for x in range(35, 38):
            for z in range(10, 14):
                d.set(x, 1, z, "spruce_planks")
                d.set(x, 6, z, slab("spruce_slab"))
        for x in (35, 37):
            for z in (10, 13):
                for y in range(Y0, 6):
                    d.set(x, y, z, log("spruce_log"))
        cx, cz = 44, 3                                              # story fire circle
        d.set(cx, Y0, cz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        for (x, z, ax) in ((cx - 2, cz, "z"), (cx + 2, cz, "z"), (cx, cz - 2, "x")):
            d.set(x, Y0, z, log("stripped_spruce_log", ax))
        for x in range(cx - 2, cx + 3):
            for z in range(cz - 2, cz + 3):
                if d.get(x, 1, z) == "minecraft:coarse_dirt":
                    d.set(x, 1, z, "gravel")
    if L >= 3:
        ar = bldg(d, 2, 6, 12, 18, 2, "gable", "z")
        ext_door(d, 7, Y0, 6, "south")
        d.sign(7, 5, 5, "north", ["ARCHIVE"], "spruce")
        stair_up(d, 11, 8, Y0, 7, "south")
        for z in range(8, 18, 3):
            stall_row(d, 3, 8, z, Y0, 3)
        for z in range(8, 18, 3):
            stall_row(d, 3, 9, z, 7, 2)
        lights(d, (3, 7, 11, 17), 7)
        chimney(d, 2, 12, Y0, 15)
    if L >= 4:
        sh = bldg(d, 8, 24, 44, 34, 2, "gable", "x", ws=3)
        ext_door(d, 26, Y0, 24, "south", double=True)
        path(d, 26, 19, 27, 23, "spruce_planks", border=False)
        stair_up(d, 9, 33, Y0, 7, "east")
        for x in range(12, 44, 4):
            for xx in (x, x + 1):
                for z in range(26, 33):
                    if (xx, Y0, z) not in d.res and d.air(xx, Y0, z) and abs(xx - 26.5) > 2:
                        for k in range(3):
                            d.bookshelf(xx, Y0 + k, z)
        d.item(26, Y0, 30, "enchanting_table")
        for x in range(9, 44):
            for z in (25, 33):
                if (x, 7, z) not in d.res and d.air(x, 7, z):
                    d.bookshelf(x, 7, z)
        table_set(d, (10, 26, 43, 32), 7, "dining")
        chimney(d, 44, 29, Y0, 16)
        d.sign(26, 6, 23, "north", ["THE STACKS"], "spruce")
    if L >= 5:
        # librarian's cabin, a lookout deck and a reading garden
        cb = bldg(d, 44, 40, 52, 50, 2, "gable", "z", mat="mangrove_planks", up="mangrove_planks")
        ext_door(d, 48, Y0, 40, "south")
        lounge(d, (45, 41, 51, 45), Y0)
        kitchen(d, (45, 46, 51, 49), Y0)
        stair_up(d, 51, 42, Y0, 7, "south")
        dorm(d, (45, 41, 51, 49), 7, 2, head="w")
        chimney(d, 52, 45, Y0, 17)
        # bookbindery & print shop
        bb = bldg(d, 2, 38, 16, 52, 2, "gable", "z", mat="stripped_dark_oak_log", up="stripped_dark_oak_log")
        ext_door(d, 9, Y0, 38, "south", double=True)
        d.sign(9, 5, 37, "north", ["BINDERY"], "spruce")
        workshop(d, (3, 39, 15, 45), Y0)
        for z in (48, 50):
            stall_row(d, 4, 11, z, Y0, 2)
        stair_up(d, 15, 40, Y0, 7, "south") if False else stair_up(d, 3, 46, Y0, 7, "north") if False else None
        stair_up(d, 14, 47, Y0, 7, "north")
        table_set(d, (3, 39, 15, 51), 7, "study", sit=False)
        for z in range(40, 52, 3):
            stall_row(d, 4, 8, z, 7, 2)
        chimney(d, 16, 45, Y0, 18)
        for x in range(4, 42):
            for z in range(38, 52):
                if (x * 3 + z) % 9 == 0:
                    d.set(x, 1, z, "moss_block")
        for x in range(6, 40, 6):
            plant_tree(d, x, 48)
            park_bench(d, x + 2, 42, "x", "south")
        for x in range(4, 42):
            put(d, x, 2, 37, "spruce_fence") if x % 8 else None
        dk = (20, 40, 32, 46)
        for x in range(dk[0], dk[2] + 1):
            for z in range(dk[1], dk[3] + 1):
                d.set(x, 4, z, "spruce_planks")
                if x in (dk[0], dk[2]) or z in (dk[1], dk[3]):
                    d.set(x, 5, z, "spruce_fence")
        for x, z in ((dk[0], dk[1]), (dk[2], dk[1]), (dk[0], dk[3]), (dk[2], dk[3])):
            for y in range(Y0, 4):
                d.set(x, y, z, log("spruce_log"))
        for k in range(3):
            d.set(dk[0] + 3 + k, Y0 + k, dk[1] - 1, st("spruce_stairs", "east")) if False else None
        for z in range(dk[1] + 1, dk[3]):
            for x in range(dk[0] + 1, dk[2]):
                if (x + z) % 4 == 0:
                    d.chair(x, 5, z, "south", "spruce", sit=False)
    return d


@design("library")
def library_v2(pack, rel, L):
    return common_materials({"Hearthwood": lib_hearthwood, "Cascadia": lib_cascadia, "Neoterra": lib_neoterra}[pack](rel, L))
