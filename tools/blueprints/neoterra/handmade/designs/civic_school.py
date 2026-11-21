"""Civic: school (hand-designed, all packs). Shared shells/helpers live in _civic_common.py."""
from designs import _civic_common as _c
globals().update({k: v for k, v in vars(_c).items() if not k.startswith("__")})
from hm import design  # noqa: E402,F401


def sch_hearthwood(rel, L):
    d = new("Hearthwood", rel, (49, 28, 49))
    sr = bldg(d, 16, 8, 30, 16, 1, "gable", "x", ws=3)
    ext_door(d, 27, Y0, 8, "south")
    for x in (26, 28):
        for y in range(Y0, 5):
            put(d, x, y, 5, "oak_fence")
    d.fill(26, 5, 5, 28, 5, 7, "oak_planks")
    d.gable(26, 5, 28, 7, 6, "z", f"{d.S['roof']}_stairs", f"{d.S['roof']}_slab", "yellow_terracotta", overhang=0)
    d.sign(27, 4, 4, "north", ["VILLAGE", "SCHOOL", "est. 1872"], "oak")
    # bell-cote on the west gable
    rg = sr["ridge"]
    for z in (11, 13):
        d.set(16, rg + 1, z, "brick_wall")
    d.fill(16, rg + 2, 11, 16, rg + 2, 13, slab("brick_slab"))
    d.set(16, rg + 2, 12, "bricks")
    bell(d, 16, rg + 1, 12, "east")
    d.hut(29, Y0, 9)
    keep(d, 28, Y0, 9)
    classroom(d, (17, 9, 29, 15), Y0, board="w", need=d.req["seats"], teacher_spot=True)
    shelf_runs(d, [(29, 11, 29, 14, Y0 + 1, 1), (29, 11, 29, 14, Y0 + 2, 1)], d.req["bookshelves"])
    for z in (10, 11):
        put(d, 28, Y0 + 1, z, "oak_fence") if False else None
    chimney(d, 30, 14, Y0 + 3, rg + 1)
    flowerbed(d, 17, 5, 24, 6)
    for x in (15, 31):
        post_lamp(d, x, 6)
    path(d, 26, 0, 28, 4)
    if L >= 2:
        inf = bldg(d, 30, 8, 38, 16, 1, "gable", "z")
        link(d, 30, Y0, 12, "east")
        lounge(d, (31, 9, 37, 15), Y0)
        for x in range(31, 38, 2):
            put(d, x, Y0, 15, "white_wool" if x % 4 == 1 else "light_blue_wool")
        shelf_wall(d, (31, 9, 37, 15), "e", Y0, 1, chisel=False)
        d.sign(34, 5, 7, "north", ["INFANTS"], "oak")
        playground(d, 30, 18, 46, 30)
    if L >= 3:
        ar = bldg(d, 18, 16, 26, 25, 2, "gable", "z", mat="bricks", up="yellow_terracotta")
        link(d, 22, Y0, 16, "south")
        art_room(d, (19, 17, 25, 24), Y0)
        stair_up(d, 25, 19, Y0, 7, "south") if False else stair_up(d, 19, 20, Y0, 7, "south")
        table_set(d, (20, 17, 25, 24), 7, "study", sit=False)
        for z in range(17, 25, 2):
            put(d, 25, 7, z, "loom[facing=west]") if False else put(d, 25, 7, z, "white_wool" if z % 4 == 1 else "pink_wool")
        lights(d, (19, 17, 25, 24), 7)
        chimney(d, 26, 20, Y0, 17)
    if L >= 4:
        mh = bldg(d, 2, 6, 14, 18, 2, "gable", "z", mat="bricks", up="yellow_terracotta")
        ext_door(d, 8, Y0, 6, "south")
        d.sign(8, 5, 5, "north", ["SCHOOL", "HOUSE"], "oak")
        stair_up(d, 13, 8, Y0, 7, "south")
        lounge(d, (3, 7, 12, 11), Y0)
        kitchen(d, (3, 13, 13, 17), Y0)
        dorm(d, (3, 7, 13, 17), 7, 2, head="w", color="yellow")
        office(d, (3, 13, 12, 17), 7) if False else None
        chimney(d, 2, 12, Y0, 16)
        for x in range(1, 15):
            put(d, x, 2, 3, "oak_fence")
        flowerbed(d, 3, 4, 6, 5)
        flowerbed(d, 10, 4, 13, 5)
        hl = bldg(d, 14, 26, 30, 36, 1, "gable", "x", wh=6)
        ext_door(d, 22, Y0, 26, "south", double=True)
        path(d, 22, 25, 23, 25, border=False)
        long_table(d, 17, 30, 27, Y0, "oak")
        long_table(d, 17, 33, 27, Y0, "oak")
        d.fill(15, Y0, 27, 29, Y0, 27, "oak_planks") if False else None
        for x in range(16, 29):
            put(d, x, Y0, 27, slab("oak_slab", "top")) if x in (20, 21, 22, 23, 24) else None
        wall_art(d, (15, 27, 29, 35), Y0, colors=("yellow", "red"))
        lights(d, (15, 27, 29, 35), Y0, 6)
        d.sign(22, 6, 37, "south", ["SCHOOL", "HALL"], "oak")
    if L >= 5:
        sr2 = bldg(d, 2, 22, 12, 36, 2, "gable", "z", mat="yellow_terracotta", up="yellow_terracotta")
        ext_door(d, 7, Y0, 22, "south")
        stair_up(d, 11, 24, Y0, 7, "south")
        classroom(d, (3, 23, 10, 35), Y0, board="s")
        classroom(d, (3, 23, 11, 35), 7, board="s")
        d.sign(7, 5, 21, "north", ["JUNIOR", "SCHOOL"], "oak")
        kt = bldg(d, 30, 32, 40, 40, 2, "gable", "z", mat="bricks", up="yellow_terracotta")
        link(d, 30, Y0, 34, "east")
        kitchen(d, (31, 33, 39, 39), Y0)
        table_set(d, (31, 35, 39, 39), Y0, "study", sit=False)
        stair_up(d, 39, 34, Y0, 7, "south")
        dorm(d, (31, 33, 37, 38), 7, 2, head="w", color="yellow", desks=False)
        chimney(d, 40, 36, Y0, 17)
        # playing field and school garden
        lawn(d, 2, 40, 28, 48)
        for z in range(41, 48):
            for x in (3, 27):
                if z in (43, 46):
                    for y in (2, 3, 4):
                        put(d, x, y, z, "white_concrete" if y < 4 else "white_concrete")
        for x in range(3, 28):
            put(d, x, 1, 44, "white_concrete") if x == 15 else None
        for x in range(42, 48):
            for z in range(34, 47):
                if x in (42, 47) or z in (34, 46):
                    put(d, x, 2, z, "oak_fence")
                else:
                    d.set(x, 1, z, "farmland[moisture=7]")
                    d.set(x, 2, z, ("carrots[age=7]", "potatoes[age=7]", "beetroots[age=3]", "wheat[age=7]")[z % 4])
        put(d, 44, 2, 33, "composter[level=4]")
    return d


def sch_neoterra(rel, L):
    d = new("Neoterra", rel, (53, 30, 51), paving="smooth_stone")
    fins = ("yellow_concrete", "lime_concrete", "orange_concrete")
    pnf = 2 if L >= 3 else 1
    p = bldg(d, 6, 6, 20, 16, pnf, "flat", glassy=True, win="nsw")
    for x in range(7, 20, 3):
        for y in range(Y0, 5 * pnf + 2):
            d.set(x, y, 5, fins[x % 3])
    ext_door(d, 12, Y0, 6, "south", double=True)
    d.sign(12, 6, 4, "north", ["SUNRISE", "SCHOOL"], "birch", glow=True, color="yellow")
    d.hut(7, Y0, 7)
    keep(d, 8, Y0, 7)
    classroom(d, (7, 7, 19, 15), Y0, board="s", need=d.req["seats"], teacher_spot=True)
    shelf_runs(d, [(7, 9, 7, 13, Y0, 1), (7, 9, 7, 13, Y0 + 1, 1)], d.req["bookshelves"])
    for x in (4, 22):
        post_lamp(d, x, 4)
    for x in range(8, 19, 4):
        put(d, x, 2, 3, "moss_block")
        put(d, x, 3, 3, "flowering_azalea")
    if pnf > 1:
        stair_up(d, 19, 8, Y0, 7, "south")
        classroom(d, (7, 7, 18, 15), 7, board="n")
        roof_garden(d, p, "solar")
    if L >= 2:
        c2 = bldg(d, 24, 6, 36, 16, 1, "flat", glassy=True, win="nse")
        for x in range(25, 36, 3):
            for y in range(Y0, 7):
                d.set(x, y, 5, fins[(x + 1) % 3])
        ext_door(d, 30, Y0, 6, "south")
        d.box(20, Y0, 9, 24, 5, 13, "glass", floor="polished_diorite")
        d.fill(20, 6, 9, 24, 6, 13, "smooth_quartz")
        d.clear(21, Y0, 10, 23, 5, 12)
        arch(d, 20, Y0, 11, "east")
        arch(d, 24, Y0, 11, "east")
        if L >= 3:
            art_room(d, (25, 7, 35, 15), Y0)
            d.sign(30, 6, 4, "north", ["ART STUDIO"], "birch", glow=True, color="lime")
        else:
            classroom(d, (25, 7, 35, 15), Y0, board="e")
        roof_garden(d, c2, "garden")
    if L >= 4:
        gy = bldg(d, 6, 20, 34, 32, 1, "flat", wh=8, win="n", mat="light_gray_concrete")
        link(d, 12, Y0, 16, "south") if False else ext_door(d, 20, Y0, 20, "north", double=True)
        for x in range(7, 34):
            for z in range(21, 32):
                d.set(x, 1, z, "white_concrete" if x in (7, 33, 20) or z in (21, 31) else "orange_terracotta")
        for x in (8, 32):
            d.set(x, 4, 26, "white_stained_glass")
            d.set(x, 5, 26, "white_stained_glass")
            put(d, x + (1 if x == 8 else -1), 4, 26, "iron_bars")
        for z in range(22, 31, 2):
            put(d, 7, Y0, z, "light_blue_wool")
        for x in range(10, 31, 4):
            for z in (23, 29):
                d.set(x, 9, z, "sea_lantern")
        d.sign(20, 7, 19, "north", ["SPORTS", "HALL"], "birch", glow=True, color="yellow")
    if L >= 3:
        playground(d, 38, 28, 50, 44)
        for x in range(38, 51):
            put(d, x, 6, 27, slab("smooth_quartz_slab", "top"))
    if L >= 5:
        sc = bldg(d, 38, 6, 50, 24, 3, "flat", glassy=True, win="nsew")
        ext_door(d, 44, Y0, 6, "south", double=True)
        stair_up(d, 39, 8, Y0, 7, "south")
        stair_up(d, 49, 22, 7, 12, "north")
        lab(d, (39, 7, 49, 15), Y0)
        table_set(d, (39, 16, 49, 23), Y0, "dining")
        shelf_wall(d, (39, 7, 49, 23), "e", 7, 3)
        table_set(d, (39, 8, 48, 23), 7, "study", sit=False)
        classroom(d, (39, 7, 49, 23), 12, board="s")
        roof_garden(d, sc, "garden")
        d.sign(44, 6, 4, "north", ["SCIENCE", "& LIBRARY"], "birch", glow=True, color="orange")
        cn = bldg(d, 6, 36, 30, 46, 1, "flat", glassy=True, win="nsw")
        ext_door(d, 18, Y0, 36, "north", double=True)
        kitchen(d, (7, 37, 29, 39), Y0)
        table_set(d, (7, 40, 29, 45), Y0, "dining")
        roof_garden(d, cn, "solar")
        for x in range(32, 38):
            for z in range(36, 47, 3):
                plant_tree(d, x, z) if x == 34 else None
    return d


def sch_cascadia(rel, L):
    d = new("Cascadia", rel, (53, 28, 51), paving="coarse_dirt")
    X1, X2, Z1, Z2 = 18, 28, 8, 20
    b = bldg(d, X1, Z1, X2, Z2, 1, "gable", "z", wh=5)
    mid = 23
    ridge = b["ridge"]
    for x in range(mid - 1, mid + 2):
        for z in range(Z1, Z1 + 3):
            d.set(x, ridge, z, "birch_planks")
    for x, z in ((mid - 1, Z1), (mid + 1, Z1), (mid - 1, Z1 + 2), (mid + 1, Z1 + 2)):
        for y in range(ridge + 1, ridge + 3):
            d.set(x, y, z, "birch_fence")
    d.hip(mid - 1, Z1, mid + 1, Z1 + 2, ridge + 3, "spruce_stairs", "spruce_slab", overhang=1)
    d.set(mid, ridge + 3, Z1 + 1, "spruce_planks")
    bell(d, mid, ridge + 2, Z1 + 1)
    ext_door(d, mid, Y0, Z1, "south")
    d.fill(X1, 1, Z1 - 3, X2, 1, Z1 - 1, "spruce_planks")
    for x in (X1, X2):
        for y in range(Y0, 6):
            put(d, x, y, Z1 - 3, log("stripped_birch_log"))
    for x in range(X1 - 1, X2 + 2):
        d.set(x, 7, Z1 - 4, st("spruce_stairs", "south"))
        for z in range(Z1 - 3, Z1):
            d.set(x, 7, z, slab("spruce_slab"))
    d.sign(mid, 6, Z1 - 1, "north", ["SCHOOL", "DIST. No. 7"], "spruce")
    d.hut(X1 + 1, Y0, Z1 + 1)
    keep(d, X1 + 2, Y0, Z1 + 1)
    classroom(d, (X1 + 1, Z1 + 1, X2 - 1, Z2 - 1), Y0, board="s", need=d.req["seats"], teacher_spot=True, h=5)
    shelf_runs(d, [(X1 + 1, Z2 - 4, X1 + 1, Z2 - 2, Y0, 1), (X1 + 1, Z2 - 4, X1 + 1, Z2 - 2, Y0 + 1, 1),
                   (X1 + 1, Z2 - 4, X1 + 1, Z2 - 2, Y0 + 2, 1)], d.req["bookshelves"])
    for z in (Z1 + 1, Z1 + 2):
        put(d, X2 - 1, Y0 + 1, z, "spruce_fence")
    chimney(d, mid, Z2 + 1, Y0, ridge)
    for x in (X1 - 2, X2 + 2):
        post_lamp(d, x, Z1 - 2)
    if L >= 2:
        tc = bldg(d, 4, 8, 14, 16, 1, "gable", "z", mat="stripped_spruce_log", up="stripped_spruce_log")
        ext_door(d, 9, Y0, 8, "south")
        lounge(d, (5, 9, 13, 12), Y0)
        dorm(d, (5, 13, 13, 15), Y0, 1, head="s", color="red")
        chimney(d, 4, 12, Y0, 13)
        for x in range(3, 16):
            put(d, x, 2, 5, "spruce_fence") if x != 9 else None
        flowerbed(d, 4, 6, 7, 7, ("fern", "blue_orchid", "allium", "dandelion"))
        d.sign(9, 5, 7, "north", ["TEACHER"], "spruce")
    if L >= 3:
        lt = bldg(d, X2, 11, 33, 18, 1, "gable", "z", mat="mangrove_planks", up="mangrove_planks", win="e")
        link(d, X2, Y0, 14, "east")
        art_room(d, (X2 + 1, 12, 32, 17), Y0)
        c2 = bldg(d, 36, 8, 46, 20, 1, "gable", "z", wh=5)
        ext_door(d, 41, Y0, 8, "south")
        classroom(d, (37, 9, 45, 19), Y0, board="s", h=5)
        d.sign(41, 6, 7, "north", ["UPPER", "GRADES"], "spruce")
        chimney(d, 41, 21, Y0, c2["ridge"])
    if L >= 4:
        gm = bldg(d, 10, 26, 40, 36, 1, "gable", "x", wh=7, mat="mangrove_planks", up="mangrove_planks")
        ext_door(d, 25, Y0, 26, "south", double=True)
        path(d, 25, 21, 26, 25, "spruce_planks", border=False)
        for x in range(11, 40):
            for z in range(27, 36):
                d.set(x, 1, z, "birch_planks" if (x + z) % 2 else "spruce_planks")
        for x in (12, 38):
            d.set(x, 5, 31, "white_stained_glass")
            put(d, x + (1 if x == 12 else -1), 5, 31, "iron_bars")
        for z in range(28, 35, 3):
            bench(d, 15, z, 19, z, Y0, "west", "spruce", tag=None) if False else None
        lights(d, (11, 27, 39, 35), Y0, 7)
        d.sign(25, 7, 25, "north", ["GYMNASIUM"], "spruce")
        playground(d, 2, 22, 8, 40)
    if L >= 5:
        lr = bldg(d, 40, 26, 52, 38, 2, "gable", "z", mat="stripped_spruce_log", up="stripped_spruce_log")
        ext_door(d, 46, Y0, 26, "south")
        kitchen(d, (41, 27, 51, 30), Y0)
        table_set(d, (41, 31, 51, 37), Y0, "dining")
        stair_up(d, 51, 31, Y0, 7, "south")
        classroom(d, (41, 27, 50, 37), 7, board="w")
        chimney(d, 52, 32, Y0, 17)
        d.sign(46, 5, 25, "north", ["LUNCH", "ROOM"], "spruce")
        for x in range(12, 40):
            for z in range(40, 49):
                if x in (12, 39) or z in (40, 48):
                    put(d, x, 2, z, "spruce_fence")
                elif z % 2:
                    d.set(x, 1, z, "farmland[moisture=7]")
                    d.set(x, 2, z, ("carrots[age=7]", "potatoes[age=7]", "wheat[age=7]")[x % 3])
        ws = bldg(d, 44, 42, 52, 48, 1, "gable", "x", mat="stripped_spruce_log", win="")
        ext_door(d, 48, Y0, 42, "south", double=True)
        workshop(d, (45, 43, 51, 47), Y0)
        bn = bldg(d, 2, 42, 10, 50, 1, "gable", "z", mat="mangrove_planks", up="mangrove_planks", wh=5)
        ext_door(d, 6, Y0, 42, "south", double=True)
        for z in range(44, 50, 2):
            put(d, 3, Y0, z, "hay_block[axis=y]")
            put(d, 9, Y0, z, "hay_block[axis=y]")
        cart(d, 6, 46, "z")
        d.sign(6, 5, 41, "north", ["WAGON", "SHED"], "spruce")
        for y in range(Y0, 14):
            d.set(16, y, 4, "spruce_fence")
        d.set(16, 14, 4, "red_wool")
        d.set(16, 13, 4, "white_wool")
    return d


@design("school")
def school_v2(pack, rel, L):
    return common_materials({"Hearthwood": sch_hearthwood, "Cascadia": sch_cascadia, "Neoterra": sch_neoterra}[pack](rel, L))
