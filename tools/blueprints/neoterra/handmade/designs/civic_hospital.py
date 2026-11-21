"""Civic: hospital (hand-designed, all packs). Shared shells/helpers live in _civic_common.py."""
from designs import _civic_common as _c
globals().update({k: v for k, v in vars(_c).items() if not k.startswith("__")})
from hm import design  # noqa: E402,F401


def hosp_hearthwood(rel, L):
    d = new("Hearthwood", rel, (55, 30, 51))
    adm_nf = 2 if L >= 3 else 1
    a = bldg(d, 22, 8, 32, 18, adm_nf, "gable", "z")
    ext_door(d, 27, Y0, 8, "south")
    for x in (25, 29):                                              # porch
        for y in range(Y0, 5):
            put(d, x, y, 5, "oak_fence")
    d.fill(25, 5, 5, 29, 5, 7, "oak_planks")
    d.gable(25, 5, 29, 7, 6, "z", f"{d.S['roof']}_stairs", f"{d.S['roof']}_slab", "calcite", overhang=0)
    d.fill(25, 1, 4, 29, 1, 7, "stone_bricks")
    d.sign(27, 4, 4, "north", ["COTTAGE", "HOSPITAL"], "oak")
    d.hut(23, Y0, 9)
    keep(d, 24, Y0, 9)
    if d.req["seats"]:
        d.chair(29, Y0, 9, "north", "oak")
        d.chair(30, Y0, 9, "north", "oak")
    put(d, 31, Y0, 9, "potted_red_tulip")
    for x in (27, 28, 29):
        put(d, x, Y0, 12, slab("dark_oak_slab", "top"))
    d.chair(28, Y0, 13, "south", "oak", sit=False)
    put(d, 27, Y0 + 1, 12, "candle[candles=1,lit=false,waterlogged=false]")
    line_items(d, 31, 10, "z", Y0, "west", ["brewing_stand", "furnace", "water_cauldron"])
    if d.req["racks"]:
        line_items(d, 31, 16, "z", Y0, "west", ["rack"])
    line_items(d, 28, 17, "x", Y0, "north", ["barrel"] * need(d, "barrel"))
    chimney(d, 32, 12, Y0, a["ridge"] + 1)
    flowerbed(d, 22, 2, 24, 6)
    flowerbed(d, 30, 2, 32, 6)
    for x in (20, 34):
        post_lamp(d, x, 4)
    if L == 1:
        ward(d, (23, 14, 24, 17), Y0, beds_left(d), head=("w",))
    if L >= 2:
        e = bldg(d, 32, 10, 46, 18, 2 if L >= 4 else 1, "gable", "x", win="nse")
        link(d, 32, Y0, 14, "east")
        ward(d, (33, 11, 45, 17), Y0, min(beds_left(d), {2: 4, 3: 4}.get(L, 6)), head=("n", "s"))
        d.sign(39, 5, 9, "north", ["VICTORIA", "WARD"], "oak")
        chimney(d, 46, 14, Y0, e["ridge"] + 1)
    if L >= 3:
        stair_up(d, 25, 12, Y0, 7, "south")
        dorm(d, (26, 9, 31, 17), 7, 3, head="e", color="white")
        office(d, (23, 9, 24, 17), 7) if False else corners(d, (23, 9, 31, 17), 7)
        w = bldg(d, 8, 10, 22, 18, 2 if L >= 4 else 1, "gable", "x", win="nsw")
        link(d, 22, Y0, 14, "west")
        ward(d, (9, 11, 21, 17), Y0, min(beds_left(d), 2 if L == 3 else 4), head=("n", "s"))
        d.sign(15, 5, 9, "north", ["ALBERT", "WARD"], "oak")
        lawn(d, 8, 2, 20, 7)
        lawn(d, 32, 2, 44, 7)
        for x in (11, 17, 35, 41):
            plant_tree(d, x, 4)
    if L >= 4:
        stair_up(d, 34, 15, Y0, 7, "east")
        stair_up(d, 20, 15, Y0, 7, "west")
        ward(d, (33, 11, 45, 16), 7, beds_left(d), head=("n",))
        lounge(d, (9, 11, 21, 17), 7)
        # surgery wing behind the admin block
        s_ = bldg(d, 22, 18, 32, 30, 1, "gable", "z", wh=5)
        link(d, 26, Y0, 18, "south")
        cx, cz = 27, 24                                             # operating table under a lamp
        d.set(cx, Y0, cz, "white_concrete")
        d.set(cx, Y0, cz + 1, "white_concrete")
        put(d, cx, 6, cz, "chain[axis=y,waterlogged=false]") if False else None
        d.set(cx, 6, cz, "sea_lantern") if False else None
        line_items(d, 23, 29, "x", Y0, "north", [])
        for x in range(23, 32):
            if x % 2:
                put(d, x, Y0, 29, "water_cauldron[level=3]" if x % 4 == 1 else slab("smooth_stone_slab", "top"))
                put(d, x, Y0 + 1, 29, "brewing_stand[has_bottle_0=true,has_bottle_1=true,has_bottle_2=false]") if x % 4 == 3 else None
        for z in (21, 27):
            put(d, 23, Y0, z, "white_wool")
            put(d, 31, Y0, z, "white_wool")
        lights(d, (23, 19, 31, 29), Y0, 5)
        d.sign(27, 5, 31, "south", ["OPERATING", "THEATRE"], "oak")
    if L >= 5:
        # children's / maternity wing behind the west ward + chapel + walled garden + carriage house
        m = bldg(d, 8, 18, 20, 30, 2, "gable", "z", mat="calcite", up="calcite")
        link(d, 14, Y0, 18, "south")
        ward(d, (9, 19, 19, 29), Y0, 6, head=("w", "e"), color="light_blue")
        for z in range(20, 29, 2):
            put(d, 14, Y0, z, "white_wool") if False else None
        stair_up(d, 19, 20, Y0, 7, "south")
        lounge(d, (9, 19, 19, 24), 7)
        table_set(d, (9, 25, 19, 29), 7, "study", sit=False)
        d.sign(14, 5, 31, "south", ["CHILDREN'S", "WARD"], "oak")
        ch = bldg(d, 36, 22, 44, 34, 1, "gable", "z", mat="stone_bricks", up="stone_bricks", gable_end="stone_bricks", wh=6)
        ext_door(d, 40, Y0, 22, "south")
        for z in range(25, 32, 2):
            for x in (38, 39, 41, 42):
                d.chair(x, Y0, z, "south", "oak", sit=False)
        d.set(40, Y0, 33, "oak_planks")
        put(d, 40, Y0 + 1, 33, "candle[candles=4,lit=false,waterlogged=false]")
        d.window(40, 4, 34, 40, 6, 34, "light_blue_stained_glass_pane")
        lights(d, (37, 23, 43, 33), Y0, 6)
        lawn(d, 1, 32, 54, 50)
        for x in range(1, 54):
            put(d, x, 2, 50, "brick_wall")
        for z in range(32, 51):
            put(d, 0, 2, z, "brick_wall")
            put(d, 54, 2, z, "brick_wall")
        path(d, 25, 31, 27, 49)
        path(d, 2, 40, 53, 41)
        for x, z in ((6, 36), (20, 36), (32, 46), (48, 36), (12, 46), (46, 46)):
            plant_tree(d, x, z)
        for x in range(4, 52, 6):
            flowerbed(d, x, 43, x + 2, 44)
        for x, z in ((15, 38), (36, 38)):
            park_bench(d, x, z, "x", "north")
        fountain(d, 26, 45, 2)
        cr = bldg(d, 47, 8, 54, 18, 1, "gable", "z", mat="bricks")
        d.double_door(50, Y0, 8, "x", "south", "oak")
        cart(d, 50, 12, "z")
        put(d, 53, Y0, 16, "hay_block[axis=y]")
        put(d, 48, Y0, 16, "hay_block[axis=y]")
        d.sign(51, 5, 7, "north", ["AMBULANCE"], "oak")
    return d


def hosp_neoterra(rel, L):
    d = new("Neoterra", rel, (53, 45, 51), paving="smooth_stone")
    Q = "smooth_quartz"
    cnf = 1 if L == 1 else 2
    c = bldg(d, 14, 8, 28, 18, cnf, "flat", glassy=True, win="nsw")
    ext_door(d, 20, Y0, 8, "south", double=True)
    for x in range(17, 25):
        for z in range(4, 8):
            put(d, x, 6, z, slab("smooth_quartz_slab", "top"))
    d.sign(21, 6, 3, "north", ["MEDICAL", "CENTRE"], "birch", glow=True, color="lime") if False else \
        d.sign(21, 5, 7, "north", ["MEDICAL", "CENTRE"], "birch", glow=True, color="lime")
    cy = 4 + 5 * cnf
    for k in (-1, 0, 1):                                            # glowing cross on the facade / roof
        d.set(26 + k, cy, 7 if cnf > 1 else 9, "red_concrete")
        d.set(26, cy + k, 7 if cnf > 1 else 9, "red_concrete")
    d.set(26, cy, 7 if cnf > 1 else 9, "sea_lantern")
    d.hut(15, Y0, 9)
    keep(d, 16, Y0, 9)
    for x in range(17, 22):
        d.set(x, Y0, 12, Q)
    d.chair(19, Y0, 13, "south", "mangrove", sit=False)
    put(d, 18, Y0 + 1, 12, "end_rod[facing=up]")
    line_items(d, 27, 9, "z", Y0, "west", ["brewing_stand", "furnace", "water_cauldron"] +
               (["rack"] if d.req["racks"] else []) + ["barrel"] * need(d, "barrel"))
    if d.req["seats"]:
        d.chair(15, Y0, 13, "west", "mangrove")
        d.chair(15, Y0, 14, "west", "mangrove")
        put(d, 15, Y0, 15, "potted_bamboo")
    # treatment bay behind a glass screen
    for x in range(15, 28):
        if x != 21:
            d.set(x, Y0, 16, "white_stained_glass_pane")
            d.set(x, Y0 + 1, 16, "white_stained_glass_pane")
    ward(d, (15, 17, 26, 17), Y0, min(beds_left(d), 2), head=("s",))
    for x in range(16, 27, 4):
        put(d, x, Y0, 17, "potted_bamboo") if False else None
    path(d, 19, 0, 22, 7, "polished_diorite")
    for x in (12, 30):
        post_lamp(d, x, 5)
        put(d, x + (1 if x == 12 else -1), 2, 3, "moss_block")
        put(d, x + (1 if x == 12 else -1), 3, 3, "flowering_azalea")
    if cnf > 1:
        stair_up(d, 15, 11, Y0, 7, "south") if False else stair_up(d, 22, 15, Y0, 7, "east")
        ward(d, (15, 9, 27, 17), 7, min(beds_left(d), 6), head=("n", "s"))
        put(d, 20, 7, 13, Q)
        put(d, 21, 7, 13, Q)
        d.chair(20, 7, 14, "south", "mangrove", sit=False)
        roof_garden(d, c, "garden" if L < 5 else "garden")
    if L >= 3:
        e = bldg(d, 28, 8, 42, 18, 2, "flat", glassy=True, win="nse")
        link(d, 28, Y0, 17, "east")
        link(d, 28, 7, 12, "east")
        lounge(d, (29, 9, 41, 17), Y0)
        table_set(d, (29, 9, 41, 17), Y0, "study", sit=False)
        ward(d, (29, 9, 41, 17), 7, beds_left(d), head=("n", "s"), color="lime")
        roof_garden(d, e, "solar")
        d.sign(35, 6, 7, "north", ["OUTPATIENTS"], "birch", glow=True, color="lime")
    if L >= 4:
        tnf = 4 if L == 4 else 7
        t = bldg(d, 14, 18, 28, 30, tnf, "flat", glassy=True, win="esw")
        link(d, 21, Y0, 18, "south")
        for k in range(tnf - 1):
            stair_up(d, 15 if k % 2 == 0 else 27, 19 if k % 2 == 0 else 29, Y0 + 5 * k, Y0 + 5 * k + 5,
                     "south" if k % 2 == 0 else "north")
        # surgery on the ground floor
        d.set(21, Y0, 24, "white_concrete")
        d.set(21, Y0, 25, "white_concrete")
        for x in range(17, 26):
            put(d, x, Y0, 29, ("water_cauldron[level=3]", slab("smooth_quartz_slab", "top"),
                               "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]")[x % 3])
        d.sign(21, Y0 + 2, 19, "south", ["SURGERY"], "birch", glow=True, color="lime") if False else None
        for k in range(1, tnf):
            y = Y0 + 5 * k
            if k % 2:
                ward(d, (16, 20, 26, 28), y, 6, head=("w", "e"), color="cyan")
            else:
                office(d, (16, 20, 26, 28), y)
        if tnf >= 7:
            ry = t["top"] + 2
            for x in range(16, 27):
                for z in range(20, 29):
                    d.set(x, ry - 1, z, "gray_concrete")
            for i, row in enumerate(["#...#", "#...#", "#####", "#...#", "#...#"]):
                for j, ch in enumerate(row):
                    if ch == "#":
                        d.set(19 + j, ry - 1, 22 + i, "white_concrete")
            for x, z in ((16, 20), (26, 20), (16, 28), (26, 28)):
                d.set(x, ry, z, "end_rod[facing=up]")
        else:
            roof_garden(d, t, "solar")
        # ambulance bay canopy
        for x in range(30, 42):
            for z in range(20, 27):
                d.set(x, 1, z, "polished_andesite")
                put(d, x, 6, z, slab("smooth_quartz_slab", "top"))
            if x % 4 == 2:
                for y in range(Y0, 6):
                    put(d, x, y, 26, "light_gray_concrete")
        for z in range(20, 27, 2):
            d.set(36, 1, z, "yellow_concrete")
        link(d, 28, Y0, 23, "east")
    if L >= 5:
        r = bldg(d, 2, 8, 14, 30, 3, "flat", glassy=True, win="nsw")
        link(d, 14, Y0, 12, "west")
        stair_up(d, 3, 28, Y0, 7, "north")
        stair_up(d, 13, 28, 7, 12, "north")
        for y in (Y0, 7, 12):
            lab(d, (3, 9, 13, 16), y)
            table_set(d, (3, 18, 13, 26), y, "study", sit=False)
        roof_garden(d, r, "garden")
        d.sign(8, 6, 7, "north", ["RESEARCH"], "birch", glow=True, color="lime")
        # healing garden
        lawn(d, 2, 32, 50, 49)
        path(d, 2, 40, 50, 41, "polished_diorite")
        for x in range(4, 50, 6):
            flowerbed(d, x, 34, x + 3, 36, ("allium", "azure_bluet", "white_tulip", "cornflower"))
            plant_tree(d, x + 2, 45)
        for x in range(6, 48, 8):
            park_bench(d, x, 42, "x", "south")
        fountain(d, 26, 40, 2)
    return d


def hosp_cascadia(rel, L):
    d = new("Cascadia", rel, (55, 30, 53), paving="coarse_dirt")
    cnf = 2 if L >= 3 else 1
    c = bldg(d, 6, 6, 16, 16, cnf, "gable", "z")
    ext_door(d, 11, Y0, 6, "south")
    d.fill(5, 1, 1, 17, 1, 5, "spruce_planks")
    for x in (5, 9, 13, 17):
        for y in range(Y0, 5):
            put(d, x, y, 1, log("spruce_log"))
    for x in range(4, 19):
        d.set(x, 5, 0, st("spruce_stairs", "south"))
        for z in range(1, 6):
            d.set(x, 5, z, slab("spruce_slab"))
    d.sign(11, 4, 5, "north", ["INFIRMARY", "+"], "spruce")
    if d.req["seats"]:
        d.chair(6, Y0, 3, "west", "spruce")
        d.chair(16, Y0, 3, "east", "spruce")
    d.hut(7, Y0, 7)
    keep(d, 8, Y0, 7)
    line_items(d, 15, 7, "z", Y0, "west", ["brewing_stand", "furnace", "water_cauldron"] +
               (["rack"] if d.req["racks"] else []))
    line_items(d, 9, 15, "x", Y0, "north", ["barrel"] * need(d, "barrel"))
    for x in (9, 10, 11):
        put(d, x, Y0, 10, slab("spruce_slab", "top"))
    d.chair(10, Y0, 11, "south", "spruce", sit=False)
    chimney(d, 6, 13, Y0, c["ridge"] + 1)
    d.hearth(7, Y0, 13, "east", 6, "cobblestone", "campfire")
    if L == 1:
        ward(d, (8, 14, 13, 15), Y0, beds_left(d), head=("s",), color="white")
    if cnf > 1:
        stair_up(d, 9, 15, Y0, 7, "east") if False else stair_up(d, 8, 13, Y0, 7, "east")
        office(d, (7, 7, 15, 11), 7)
        dorm(d, (7, 14, 15, 15), 7, 0, head="s") if False else lounge(d, (7, 12, 15, 15), 7)
    if L >= 2:
        wx2 = 30 if L == 2 else 36
        w = bldg(d, 16, 8, wx2, 16, 1, "gable", "x", win="nse")
        link(d, 16, Y0, 12, "east")
        n_here = min(beds_left(d), 4 if L == 2 else 8)
        ward(d, (17, 9, wx2 - 1, 15), Y0, n_here, head=("n", "s"), color="white")
        chimney(d, wx2, 12, Y0, w["ridge"] + 1)
    if L >= 3:
        # screened sleeping porch along the ward
        for x in range(16, wx2 + 1):
            for z in range(17, 21):
                d.set(x, 1, z, "spruce_planks")
                d.set(x, 6, z, slab("spruce_slab"))
            if x % 4 == 0:
                for y in range(Y0, 6):
                    d.set(x, y, 20, log("spruce_log"))
            else:
                d.set(x, Y0, 20, "spruce_fence")
        d.door(22, Y0, 16, "south", "spruce")
        for x in (18, 24, 30, 33):
            d.chair(x, Y0, 18, "north", "spruce", sit=False)
            put(d, x + 1, Y0, 18, slab("spruce_slab", "top"))
    if L >= 4:
        sz1 = 26
        sn = bldg(d, 6, sz1, 40, sz1 + 8, 2, "gable", "x")
        ext_door(d, 23, Y0, sz1, "south", double=True)
        path(d, 23, 21, 24, sz1 - 1, "spruce_planks", border=False)
        stair_up(d, 7, sz1 + 7, Y0, 7, "east")
        ward(d, (14, sz1 + 1, 39, sz1 + 7), Y0, max(beds_left(d), 4), head=("n", "s"), color="green")
        lounge(d, (7, sz1 + 1, 13, sz1 + 6), Y0)
        dorm(d, (14, sz1 + 1, 39, sz1 + 7), 7, 8, head="s", color="white")
        office(d, (7, sz1 + 1, 13, sz1 + 5), 7, desk_side="s")
        for x in range(6, 41):                                      # long verandah
            for z in range(sz1 + 9, sz1 + 12):
                d.set(x, 1, z, "spruce_planks")
                d.set(x, 6, z, slab("spruce_slab"))
            if x % 4 == 2:
                for y in range(Y0, 6):
                    d.set(x, y, sz1 + 11, log("spruce_log"))
        for x in range(8, 40, 4):
            d.chair(x, Y0, sz1 + 10, "south", "spruce", sit=False)
        d.door(23, Y0, sz1 + 8, "north", "spruce")
        chimney(d, 40, sz1 + 4, Y0, 16)
    if L >= 5:
        dh = bldg(d, 40, 4, 50, 14, 2, "gable", "z", mat="mangrove_planks", up="mangrove_planks")
        ext_door(d, 45, Y0, 4, "south")
        stair_up(d, 49, 6, Y0, 7, "south")
        lounge(d, (41, 5, 48, 9), Y0)
        kitchen(d, (41, 10, 49, 13), Y0)
        dorm(d, (41, 5, 49, 13), 7, 2, head="w", color="red")
        d.sign(45, 5, 3, "north", ["DOCTOR"], "spruce")
        # laundry & boiler house with a tall stack
        lh = bldg(d, 42, 18, 50, 24, 1, "gable", "x", mat="cobblestone", up="cobblestone", gable_end="cobblestone")
        ext_door(d, 46, Y0, 18, "south")
        for x in range(43, 50, 2):
            put(d, x, Y0, 23, "water_cauldron[level=3]")
        for x in range(43, 50):
            put(d, x, 4, 21, "white_wool" if x % 2 else "light_blue_wool") if False else None
        chimney(d, 50, 21, Y0, 16)
        # glasshouse + herb garden
        for x in range(42, 53):
            for z in range(38, 47):
                edge = x in (42, 52) or z in (38, 46)
                if edge:
                    for y in range(Y0, 5):
                        d.set(x, y, z, "glass" if (x + z) % 3 else log("spruce_log"))
                else:
                    d.set(x, 1, z, "farmland[moisture=7]" if (x + z) % 2 else "spruce_planks")
                    if (x + z) % 2:
                        d.set(x, Y0, z, ("fern", "sweet_berry_bush[age=2]", "potted_fern")[x % 2])
                d.set(x, 5, z, "glass")
        d.set(47, Y0, 38, AIR)
        d.set(47, Y0 + 1, 38, AIR)
        d.door(47, Y0, 38, "south", "spruce")
        ws = bldg(d, 28, 40, 38, 46, 1, "gable", "x", mat="stripped_spruce_log", win="")
        ext_door(d, 33, Y0, 40, "south", double=True)
        for x in range(29, 38):
            for y in (Y0, Y0 + 1):
                if x not in (33, 34):
                    put(d, x, y, 45, log("spruce_log", "z"))
        workshop(d, (29, 41, 37, 44), Y0)
        d.sign(33, 5, 39, "north", ["WOODSHED"], "spruce")
        for x in range(1, 40, 3):
            plant_tree(d, x, 48) if x % 6 == 1 else flowerbed(d, x, 47, x + 1, 48, ("fern", "blue_orchid", "allium", "lily_of_the_valley"))
    return d


@design("hospital")
def hospital_v2(pack, rel, L):
    return common_materials({"Hearthwood": hosp_hearthwood, "Cascadia": hosp_cascadia, "Neoterra": hosp_neoterra}[pack](rel, L))
