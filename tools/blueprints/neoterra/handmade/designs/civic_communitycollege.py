"""Civic: communitycollege (hand-designed, all packs). Shared shells/helpers live in _civic_common.py."""
from designs import _civic_common as _c
globals().update({k: v for k, v in vars(_c).items() if not k.startswith("__")})
from hm import design  # noqa: E402,F401


def col_hearthwood(rel, L):
    d = new("Hearthwood", rel, (49, 30, 49))
    mnf = 2 if L >= 3 else 1
    m = bldg(d, 16, 12, 30, 22, mnf, "gable", "z")
    ext_door(d, 23, Y0, 12, "south")
    for x in (21, 25):
        for y in range(Y0, 6):
            put(d, x, y, 10, "quartz_pillar[axis=y]")
    d.fill(21, 6, 10, 25, 6, 11, "smooth_stone")
    d.fill(21, 1, 9, 25, 1, 11, "polished_andesite")
    d.sign(23, mnf * 5 + 4, 11, "north", ["MECHANICS'", "INSTITUTE"], "dark_oak") if False else \
        d.sign(23, 5, 11, "north", ["MECHANICS'", "INSTITUTE"], "dark_oak")
    d.hut(17, Y0, 13)
    keep(d, 18, Y0, 13)
    d.item(23, Y0, 20, "lectern", "north")
    keep(d, 23, Y0, 19)
    blackboard(d, 21, 21, 25, 21, Y0 + 1, "north")
    for z in (15, 17):
        for x in list(range(18, 22)) + list(range(24, 28)):
            if d.placed["seats"] < d.req["seats"]:
                d.chair(x, Y0, z, "north", "dark_oak")
    runs = [(17, 15, 17, 21, Y0, 2), (29, 14, 29, 21, Y0, 2), (17, 15, 17, 21, Y0 + 2, 1), (29, 14, 29, 21, Y0 + 2, 1)]
    corners(d, (17, 13, 29, 21), Y0)
    wall_art(d, (17, 13, 29, 21), Y0, "ew", ("blue", "white"))
    # walled front garden with the speaker's plinth and benches
    lawn(d, 4, 1, 44, 8)
    path(d, 22, 0, 24, 9)
    for x in range(3, 46):
        if x not in (22, 23, 24):
            put(d, x, 2, 0, "brick_wall")
    outdoor_class(d, 10, 3, "south")
    for x in (14, 32):
        post_lamp(d, x, 6)
    flowerbed(d, 28, 3, 40, 4)
    plant_tree(d, 36, 7)
    if L >= 2:
        rr = bldg(d, 30, 13, 38, 21, 2 if L >= 3 else 1, "gable", "x", mat="bricks", up="bricks")
        link(d, 30, Y0, 17, "east")
        runs += [(31, 14, 37, 14, Y0, 2), (31, 20, 37, 20, Y0, 2)]
        long_table(d, 32, 18, 35, Y0, "dark_oak", sit=False)
        if L >= 3:
            link(d, 30, 7, 17, "east")
            table_set(d, (31, 14, 37, 20), 7, "study", sit=False)
            for x in (40, 44):
                post_lamp(d, x, 10)
            flowerbed(d, 39, 12, 44, 14)
            for x in range(39, 46):
                put(d, x, 2, 11, "dark_oak_fence")
            flowerbed(d, 4, 10, 15, 11)
            for x in (5, 15):
                post_lamp(d, x, 9)
            runs += [(31, 14, 37, 14, 7, 3), (31, 20, 37, 20, 7, 3)]
        d.sign(34, 5, 12, "north", ["READING", "ROOM"], "dark_oak")
        if need(d, "lectern") > 1:
            d.item(37, Y0, 16, "lectern", "west")
            keep(d, 36, Y0, 16)
    if L >= 2:
        tw = bldg(d, 4, 13, 16, 23, 2 if L >= 5 else 1, "gable", "x", mat="bricks", up="bricks")
        if L >= 5:
            stair_up(d, 5, 22, Y0, 7, "east") if False else None
            link(d, 16, 7, 17, "west")
            classroom(d, (5, 14, 15, 22), 7, board="w")
        link(d, 16, Y0, 17, "west")
        workshop(d, (5, 14, 15, 22), Y0)
        chimney(d, 4, 18, Y0, tw["ridge"] + 1)
        d.sign(10, 5, 12, "north", ["TECHNICAL", "SCHOOL"], "dark_oak")
    if mnf > 1:
        stair_up(d, 19, 14, Y0, 7, "east")
        runs += [(17, 13, 17, 21, 7, 3), (18, 21, 27, 21, 7, 3), (17, 13, 27, 13, 7, 3)]
        table_set(d, (18, 14, 28, 20), 7, "study", sit=False)
        clockface(d, 23, 14, 12, "north", "white_concrete") if False else None
    if L >= 4:
        th = bldg(d, 14, 26, 36, 38, 1, "gable", "x", wh=7)
        ext_door(d, 25, Y0, 26, "south", double=True)
        path(d, 25, 23, 26, 25, border=False)
        lecture(d, (15, 27, 35, 37), Y0, "s", h=7)
        for x in range(18, 33):
            put(d, x, Y0, 36, "red_carpet")
        d.sign(25, 6, 25, "north", ["THEATRE"], "dark_oak")
    if L >= 5:
        hs = bldg(d, 2, 26, 12, 40, 2, "gable", "z", mat="white_terracotta", up="white_terracotta")
        ext_door(d, 7, Y0, 26, "south")
        stair_up(d, 11, 28, Y0, 7, "south")
        lounge(d, (3, 27, 10, 32), Y0)
        table_set(d, (3, 33, 11, 39), Y0, "dining")
        dorm(d, (3, 27, 11, 39), 7, 6, head="w", color="blue")
        chimney(d, 2, 33, Y0, 16)
        d.sign(7, 5, 25, "north", ["HOSTEL"], "dark_oak")
        ct = bldg(d, 38, 28, 46, 38, 2, "gable", "z", mat="calcite", up="calcite")
        ext_door(d, 42, Y0, 28, "south")
        stair_up(d, 45, 30, Y0, 7, "south")
        lounge(d, (39, 29, 44, 33), Y0)
        kitchen(d, (39, 34, 45, 37), Y0)
        dorm(d, (39, 29, 44, 37), 7, 2, head="w")
        chimney(d, 46, 33, Y0, 16)
        lawn(d, 2, 40, 46, 48)
        for x in range(4, 46, 6):
            plant_tree(d, x, 44)
            flowerbed(d, x + 2, 41, x + 4, 42)
    shelf_runs(d, runs, d.req["bookshelves"])
    return d


def col_neoterra(rel, L):
    d = new("Neoterra", rel, (51, 30, 51), paving="smooth_stone")
    Q = "smooth_quartz"
    nf = 2 if L >= 3 else 1
    p = bldg(d, 14, 16, 30, 26, nf, "flat", glassy=True, win="nsw")
    ext_door(d, 22, Y0, 16, "south", double=True)
    d.sign(22, 6, 15, "north", ["LEARNING", "PAVILION"], "birch", glow=True, color="orange")
    d.hut(15, Y0, 17)
    keep(d, 16, Y0, 17)
    d.item(28, Y0, 21, "lectern", "west")
    keep(d, 27, Y0, 21)
    for z in range(19, 24):
        d.set(29, 4, z, "black_concrete")
        d.set(29, 5, z, "black_concrete")
    for x in (19, 21, 23, 25):
        for z in (19, 20, 22, 23):
            if d.placed["seats"] < d.req["seats"]:
                d.chair(x, Y0, z, "west", "birch")
    runs = [(15, 25, 22, 25, Y0, 2), (15, 19, 15, 24, Y0, 2), (23, 25, 29, 25, Y0, 2), (15, 25, 29, 25, Y0 + 2, 1)]
    corners(d, (15, 17, 29, 25), Y0, ["potted_bamboo"])
    # amphitheatre: stage by the pavilion, tiers rising to the street
    for x in range(16, 29):
        for z in (13, 14):
            d.set(x, 1, z, "polished_andesite")
    d.spot(22, Y0, 14, "stand_out")
    keep(d, 22, Y0, 14)
    if need(d, "lectern") > 1:
        d.item(24, Y0, 14, "lectern", "north")
        keep(d, 24, Y0, 13)
    for k, z in enumerate((11, 9, 7)):
        for zz in (z, z - 1):
            for x in range(15, 30):
                for y in range(Y0, Y0 + k):
                    d.set(x, y, zz, Q)
        for x in range(16, 29):
            if x != 22:
                sit_out(d, x, Y0 + k, z, "north", "birch")
    for x in (14, 30):
        post_lamp(d, x, 13)
    if L >= 2:
        mk = bldg(d, 30, 16, 40, 26, nf, "flat", glassy=False, win="ns", mat="orange_terracotta", up="mangrove_planks")
        link(d, 30, Y0, 21, "east")
        workshop(d, (31, 17, 39, 25), Y0)
        d.sign(35, 6, 15, "north", ["MAKER", "SPACE"], "birch", glow=True, color="orange")
        roof_garden(d, mk, "solar")
        for x in (32, 35, 38):                                       # planters along the maker space front
            put(d, x, 2, 14, "moss_block")
            put(d, x, 3, 14, "flowering_azalea")
    if nf > 1:
        stair_up(d, 16, 19, Y0, 7, "south")
        table_set(d, (16, 17, 29, 25), 7, "study", sit=False)
        runs += [(17, 25, 29, 25, 7, 3)]
        roof_garden(d, p, "garden")
        if L >= 2:
            link(d, 30, 7, 21, "east")
            classroom(d, (31, 17, 39, 25), 7, board="e")
    if L >= 3:
        for k, z in enumerate((5,)):
            for x in range(15, 30):
                for y in range(Y0, Y0 + 3):
                    d.set(x, y, z, Q) if False else None
        for x in range(14, 31):                                      # shade canopy over the stage
            d.set(x, 7, 12, slab("smooth_quartz_slab", "top"))
            d.set(x, 7, 13, slab("smooth_quartz_slab", "top"))
        for x in (14, 30):
            for y in range(Y0, 7):
                d.set(x, y, 12, "white_concrete")
    if L >= 4:
        lb = bldg(d, 2, 16, 14, 32, 3, "flat", glassy=True, win="nsw", mat="white_concrete", up="mangrove_planks")
        link(d, 14, Y0, 21, "west")
        stair_up(d, 3, 30, Y0, 7, "north")
        stair_up(d, 13, 18, 7, 12, "south")
        for y in (Y0, 7, 12):
            for z in range(20, 31, 3):
                stall_row(d, 4, 11, z, y, 2)
            lights(d, (3, 17, 13, 31), y)
        runs += [(3, 17, 12, 17, Y0, 3)]
        roof_garden(d, lb, "garden")
        d.sign(8, 6, 15, "north", ["LIBRARY"], "birch", glow=True, color="orange")
    if L >= 5:
        st_ = bldg(d, 36, 30, 46, 40, 5, "flat", glassy=True, win="nsew", mat="white_concrete", up="mangrove_planks")
        ext_door(d, 41, Y0, 30, "south", double=True)
        for k in range(4):
            stair_up(d, 37 if k % 2 == 0 else 45, 31 if k % 2 == 0 else 39, Y0 + 5 * k, Y0 + 5 * k + 5,
                     "south" if k % 2 == 0 else "north")
        lounge(d, (38, 32, 44, 38), Y0)
        for k in range(1, 5):
            (art_room if k % 2 else classroom)(d, (38, 32, 44, 38), Y0 + 5 * k)
        roof_garden(d, st_, "solar")
        cf = bldg(d, 16, 30, 30, 38, 1, "flat", glassy=True, win="nsw")
        ext_door(d, 23, Y0, 30, "south", double=True)
        kitchen(d, (17, 31, 29, 33), Y0)
        table_set(d, (17, 34, 29, 37), Y0, "dining")
        roof_garden(d, cf, "garden")
        lawn(d, 2, 42, 48, 49)
        for x in range(4, 48, 6):
            plant_tree(d, x, 45)
            park_bench(d, x + 2, 47, "x", "south")
    shelf_runs(d, runs, d.req["bookshelves"])
    return d


def col_cascadia(rel, L):
    d = new("Cascadia", rel, (53, 28, 51), paving="coarse_dirt")
    mnf = 2 if L >= 3 else 1
    h = bldg(d, 12, 16, 30, 26, mnf, "gable", "x")
    ext_door(d, 21, Y0, 16, "south")
    d.fill(12, 1, 13, 30, 1, 15, "spruce_planks")
    for x in (12, 18, 24, 30):
        for y in range(Y0, 6):
            put(d, x, y, 13, log("spruce_log"))
    for x in range(11, 32):
        d.set(x, 6, 12, st("spruce_stairs", "south"))
        for z in range(13, 16):
            d.set(x, 6, z, slab("spruce_slab"))
    d.sign(21, 5, 15, "north", ["VALLEY", "COLLEGE"], "spruce")
    for x in (15, 27):
        put(d, x, 5, 14, "lantern[hanging=true,waterlogged=false]")
    d.hut(13, Y0, 17)
    keep(d, 14, Y0, 17)
    d.item(28, Y0, 21, "lectern", "west")
    keep(d, 27, Y0, 21)
    blackboard(d, 29, 19, 29, 23, Y0 + 1, "west", "black_concrete", "spruce")
    for x in (18, 20, 22, 24):
        for z in (18, 19, 20, 22, 23, 24):
            if d.placed["seats"] < d.req["seats"]:
                d.chair(x, Y0, z, "west", "spruce")
    d.hearth(13, Y0, 22, "east", 7, "cobblestone", "campfire")
    chimney(d, 11, 22, Y0, h["ridge"] + 1)
    runs = [(13, 25, 17, 25, Y0, 2), (23, 25, 28, 25, Y0, 2), (13, 25, 28, 25, Y0 + 2, 1), (13, 17, 13, 20, Y0 + 1, 1)]
    # fire circle with log benches and the speaker's stump
    cx, cz = 21, 6
    for x in range(cx - 4, cx + 5):
        for z in range(cz - 4, cz + 5):
            if abs(x - cx) + abs(z - cz) <= 5:
                d.set(x, 1, z, "gravel" if abs(x - cx) + abs(z - cz) <= 2 else "coarse_dirt")
    d.set(cx, Y0, cz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for x in (cx - 1, cx, cx + 1):
        sit_out(d, x, Y0, cz - 3, "north", "spruce")
    for z in (cz - 1, cz, cz + 1):
        sit_out(d, cx - 3, Y0, z, "west", "spruce")
        sit_out(d, cx + 3, Y0, z, "east", "spruce")
    d.set(cx, 1, cz + 3, log("stripped_spruce_log"))
    d.spot(cx, Y0, cz + 3, "stand_out")
    keep(d, cx, Y0, cz + 3)
    if need(d, "lectern") > 1:
        d.item(cx + 1, Y0, cz + 3, "lectern", "north")
        keep(d, cx + 1, Y0, cz + 4)
    for x, z in ((cx - 5, cz - 3), (cx + 5, cz - 3)):
        post_lamp(d, x, z)
    if L >= 2:
        sh = bldg(d, 30, 17, 38, 25, 1, "gable", "z", mat="stripped_spruce_log", up="stripped_spruce_log")
        link(d, 30, Y0, 21, "east")
        workshop(d, (31, 18, 37, 24), Y0)
        d.sign(34, 5, 16, "north", ["SHOP"], "spruce")
        for z in range(18, 25, 2):
            put(d, 39, 2, z, log("spruce_log", "z"))
            put(d, 39, 3, z, log("spruce_log", "z"))
    if L >= 2:
        rl = bldg(d, 2, 16, 12, 26, 2 if L >= 3 else 1, "gable", "z", mat="stripped_dark_oak_log", up="stripped_dark_oak_log")
        if L >= 3:
            stair_up(d, 11, 25, Y0, 7, "north") if False else stair_up(d, 4, 25, Y0, 7, "east")
            table_set(d, (3, 17, 11, 25), 7, "study", sit=False)
            runs += [(3, 17, 11, 17, 7, 2)]
        ext_door(d, 7, Y0, 16, "south")
        for z in range(18, 26, 2):
            stall_row(d, 3, 6, z, Y0, 2)
        for z in (18, 21, 24):
            desk(d, 10, Y0, z, "west")
        runs += [(3, 17, 6, 17, Y0, 2)]
        chimney(d, 2, 21, Y0, 13)
    if mnf > 1:
        stair_up(d, 15, 25, Y0, 7, "east")
        runs += [(13, 17, 29, 17, 7, 3), (13, 17, 13, 25, 7, 3), (29, 17, 29, 25, 7, 3)]
        table_set(d, (14, 18, 28, 24), 7, "study", sit=False)
    if L >= 4:
        bk = bldg(d, 36, 30, 50, 40, 2, "gable", "x", mat="mangrove_planks", up="mangrove_planks")
        ext_door(d, 43, Y0, 30, "south")
        stair_up(d, 49, 32, Y0, 7, "south")
        kitchen(d, (37, 31, 48, 33), Y0)
        table_set(d, (37, 34, 48, 39), Y0, "dining")
        dorm(d, (37, 31, 48, 39), 7, 8, head="n")
        chimney(d, 50, 35, Y0, 16)
        d.sign(43, 5, 29, "north", ["BUNKHOUSE"], "spruce")
        for x in range(36, 51):                                      # bunkhouse porch
            for z in (27, 28, 29):
                d.set(x, 1, z, "spruce_planks")
            if x % 4 == 0:
                for y in range(Y0, 5):
                    put(d, x, y, 27, log("spruce_log"))
            for z in (27, 28, 29):
                put(d, x, 5, z, slab("spruce_slab"))
        for x in range(36, 51):                                      # porch rail and woodpile
            if x % 4 and x not in (43,):
                put(d, x, Y0, 26, "spruce_fence")
        for x in range(30, 35):
            for y in (Y0, Y0 + 1):
                put(d, x, y, 41, log("spruce_log", "x"))
        for z in range(31, 40):                                      # rail fence beside the bunkhouse
            put(d, 35, Y0, z, "spruce_fence")
        for x in range(37, 50, 4):                                   # lanterns on the bunkhouse back wall
            put(d, x, 4, 41, "wall_torch[facing=south]") if False else put(d, x, 5, 41, "lantern[hanging=true,waterlogged=false]") if False else None
        for z in (30, 34, 38):
            post_lamp(d, 52, z)
        for z in (32, 36):
            put(d, 34, Y0, z, "spruce_fence")
            put(d, 34, Y0 + 1, z, "lantern[hanging=false,waterlogged=false]")
        for x in (37, 41, 45, 49):
            d.chair(x, Y0, 28, "south", "spruce", sit=False)
            put(d, x + 1, Y0, 28, "barrel[facing=up,open=false]") if False else put(d, x + 1, 4, 28, "lantern[hanging=true,waterlogged=false]")
    if L >= 5:
        sm = bldg(d, 36, 42, 50, 50, 2, "gable", "x", mat="stripped_spruce_log")
        stair_up(d, 49, 44, Y0, 7, "south")
        table_set(d, (37, 43, 48, 49), 7, "study", sit=False)
        lights(d, (37, 43, 49, 49), 7)
        ext_door(d, 43, Y0, 42, "south", double=True)
        workshop(d, (37, 43, 49, 49), Y0)
        for x in range(37, 50, 2):
            put(d, x, Y0, 49, log("spruce_log", "x"))
        d.sign(43, 5, 41, "north", ["SAWMILL", "CLASS"], "spruce")
        for x in range(37, 50, 3):
            put(d, x, Y0, 51, log("spruce_log", "x")) if d.bp.inside(x, Y0, 51) else None
        for x in (35, 51):
            post_lamp(d, x, 44)
        gh = (4, 32, 16, 42)
        for x in range(gh[0], gh[2] + 1):
            for z in range(gh[1], gh[3] + 1):
                edge = x in (gh[0], gh[2]) or z in (gh[1], gh[3])
                if edge:
                    for y in range(Y0, 5):
                        d.set(x, y, z, "glass" if (x + z) % 3 else log("spruce_log"))
                else:
                    d.set(x, 1, z, "farmland[moisture=7]" if (x + z) % 2 else "spruce_planks")
                    if (x + z) % 2:
                        d.set(x, Y0, z, ("fern", "sweet_berry_bush[age=2]", "carrots[age=7]")[x % 3])
                d.set(x, 5, z, "glass")
        d.set(10, Y0, 32, AIR)
        d.set(10, Y0 + 1, 32, AIR)
        d.door(10, Y0, 32, "south", "spruce")
        bn = bldg(d, 20, 32, 32, 44, 1, "gable", "z", mat="mangrove_planks", up="mangrove_planks", wh=6)
        ext_door(d, 26, Y0, 32, "south", double=True)
        for z in range(34, 44, 3):
            put(d, 21, Y0, z, "hay_block[axis=y]")
            put(d, 31, Y0, z, "hay_block[axis=y]")
        cart(d, 26, 38, "z")
        store(d, (21, 33, 31, 43), Y0, aisle="z") if False else None
        d.sign(26, 6, 31, "north", ["AG BARN"], "spruce")
    shelf_runs(d, runs, d.req["bookshelves"])
    return d


@design("communitycollege")
def communitycollege_v2(pack, rel, L):
    return common_materials({"Hearthwood": col_hearthwood, "Cascadia": col_cascadia, "Neoterra": col_neoterra}[pack](rel, L))
