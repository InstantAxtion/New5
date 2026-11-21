"""Civic: communitycollege (hand-designed, all packs).

Round 4: no automatic placement. Building shells come from shell() (walls, floors, window openings, roofs –
structure only, no dressing, no lights). Every room and yard is furnished with explicit, hand-chosen coordinates
below, per pack and per level.
"""
from designs._civic_common import (Y0, st, slab, log, flight, framing, blackboard, sit_out, new, link, wallblock,
                                   common_materials, chimney, plant_tree, put)
from hm import design, AIR, D4, OPP, CW  # noqa: F401

LH = "lantern[hanging=true,waterlogged=false]"
LS = "lantern[hanging=false,waterlogged=false]"


def td(wood, facing, half="top", opened=False):
    return (f"{wood}_trapdoor[facing={facing},half={half},open={'true' if opened else 'false'},"
            f"powered=false,waterlogged=false]")


def cand(n=1, color=""):
    return f"{color + '_' if color else ''}candle[candles={n},lit=false,waterlogged=false]"


def chest(facing, typ="single"):
    return f"chest[facing={facing},type={typ},waterlogged=false]"


def place(d, items):
    """Explicit hand-placed list of (x, y, z, block)."""
    for x, y, z, b in items:
        d.set(x, y, z, b)


def shelf(d, cells, y, h):
    """Bookshelves (counted) on the listed (x, z) cells, h high from y."""
    for x, z in cells:
        d.bookshelf(x, y, z, h)


def seat(d, cells, y, back, wood, sit=True):
    for x, z in cells:
        d.chair(x, y, z, back, wood, sit=sit)


def outseat(d, cells, y, back, wood):
    for x, z in cells:
        sit_out(d, x, y, z, back, wood)


def tops(d, cells, y, blk):
    for x, z in cells:
        d.set(x, y, z, slab(blk, "top"))


def hang(d, cells, y):
    for x, z in cells:
        d.set(x, y, z, LH)


def panel(d, cells, y):
    """Neoterra: ceiling light panel set into the ceiling slab at y."""
    for x, z in cells:
        d.set(x, y, z, "sea_lantern")


def carpet(d, cells, y, color):
    for x, z in cells:
        d.set(x, y, z, f"{color}_carpet")


def lamppost(d, x, z, style):
    col = {"hw": ("stone_brick_wall", "dark_oak_fence", "dark_oak_fence", LS),
           "cs": ("spruce_log[axis=y]", "spruce_fence", "spruce_fence", LS),
           "nt": ("light_gray_concrete", "birch_fence", "birch_fence", "sea_lantern")}[style]
    for k, b in enumerate(col):
        d.set(x, 2 + k, z, b)


def entry(d, x, z, facing, double=False, along="x", wood=None, step=None):
    """Exterior door in a wall (facing = into the building), approach cells cleared, a step stone outside."""
    wood = wood or d.S["wood"]
    if double:
        d.double_door(x, Y0, z, along, facing, wood)
    else:
        d.door(x, Y0, z, facing, wood)
    ox, oz = D4[OPP[facing]]
    cells = [(x, z)] + ([(x + (along == "x"), z + (along == "z"))] if double else [])
    for cx, cz in cells:
        for k in range(3):
            d.set(cx + ox, Y0 + k, cz + oz, AIR)
            d.set(cx - ox, Y0 + k, cz - oz, AIR)
        d.set(cx + ox, 1, cz + oz, step or d.S["base"])


def stair(d, x, z, y0, yU, rise, rails, block=None, under=None, fence=None):
    """Straight flight between storeys plus the railing cells listed by hand (upper floor, along the hole)."""
    block = block or f"{d.S['wood']}_stairs"
    under = under or d.S["floor"]
    flight(d, x, z, y0, yU, rise, block, under=under)
    fence = fence or f"{d.S['wood']}_fence"
    for rx, ry, rz in rails:
        d.set(rx, ry, rz, fence)


def shell(d, x1, z1, x2, z2, nf=1, roof="gable", axis="x", win="nesw", ws=3, mat=None, up=None, wh=4,
          gable_end=None, glassy=False, parapet=True, tie=True):
    """Structure only (copy of _civic_common.bldg without its dressing/light passes): plinth, storey walls and
    floors, corner posts, window openings, roof, gable-end posts, tie beams."""
    S = d.S
    mat = mat or S["wall"]
    up = up or S["up"]
    fh = wh + 1
    ys = [Y0 + fh * f for f in range(nf)]
    top = ys[-1] + wh - 1
    d.fill(x1, 1, z1, x2, 1, z2, S["floor"] if d.pack != "Neoterra" else "polished_diorite")
    for f, y in enumerate(ys):
        m = mat if f == 0 else up
        for yy in range(y, y + (wh if f == nf - 1 else fh)):
            for x in range(x1, x2 + 1):
                d.set(x, yy, z1, wallblock(d, m, "n"))
                d.set(x, yy, z2, wallblock(d, m, "s"))
            for z in range(z1 + 1, z2):
                d.set(x1, yy, z, wallblock(d, m, "w"))
                d.set(x2, yy, z, wallblock(d, m, "e"))
            if yy < y + wh:
                d.clear(x1 + 1, yy, z1 + 1, x2 - 1, yy, z2 - 1)
        if f < nf - 1:
            yb = y + wh
            d.fill(x1 + 1, yb, z1 + 1, x2 - 1, yb, z2 - 1, S["floor"] if d.pack != "Neoterra" else "smooth_stone")
            for x in range(x1, x2 + 1):
                for z in (z1, z2):
                    d.set(x, yb, z, wallblock(d, S["band"], "n" if z == z1 else "s"))
            for z in range(z1, z2 + 1):
                for x in (x1, x2):
                    d.set(x, yb, z, wallblock(d, S["band"], "w"))
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if x in (x1, x2) or z in (z1, z2):
                d.set(x, Y0, z, S["base"] if not (d.pack == "Cascadia" and (x * 7 + z) % 5 == 0)
                      else "mossy_cobblestone")
    if d.pack == "Hearthwood":
        for f, y in enumerate(ys):
            m = mat if f == 0 else up
            if m in ("calcite", "white_terracotta"):
                framing(d, x1, z1, x2, z2, y, y + wh - 1, S["post"], every=3)
    for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        for y in range(Y0, top + 1):
            if d.pack == "Hearthwood":
                if mat == up or y < ys[0] + wh:
                    d.set(x, y, z, "smooth_stone" if y % 2 else "stone_bricks")
                else:
                    d.set(x, y, z, log(S["post"]))
            elif d.pack == "Cascadia":
                d.set(x, y, z, log(S["post"]))
            else:
                d.set(x, y, z, "light_gray_concrete")
    sides = {"n": (z1, "x"), "s": (z2, "x"), "w": (x1, "z"), "e": (x2, "z")}
    for f, y in enumerate(ys):
        for sd in win:
            line, along = sides[sd]
            a1, a2 = (x1, x2) if along == "x" else (z1, z2)
            for a in range(a1 + 2, a2 - 1):
                if glassy:
                    if (a - a1) % 4 == 0:
                        continue
                elif (a - a1 - 2) % ws != 0:
                    continue
                x, z = (a, line) if along == "x" else (line, a)
                h2 = wh - 1 if glassy or d.pack == "Neoterra" else 2
                for yy in range(y + 1, y + 1 + h2):
                    d.set(x, yy, z, S["glass"])
    ridge = top
    if roof == "gable":
        ridge = d.gable(x1, z1, x2, z2, top + 1, axis, f"{S['roof']}_stairs", f"{S['roof']}_slab",
                        gable_end or (up if d.pack != "Cascadia" else "spruce_planks"), overhang=1)
        ends = ((x1, (z1 + z2) // 2), (x2, (z1 + z2) // 2)) if axis == "x" else \
            (((x1 + x2) // 2, z1), ((x1 + x2) // 2, z2))
        for ex, ez in ends:
            for yy in range(top + 1, ridge):
                if d.pack == "Hearthwood" and "stairs" not in d.get(ex, yy, ez):
                    d.set(ex, yy, ez, log(S["post"]))
            if ridge - top >= 4:
                d.set(ex, top + 2, ez, S["glass"])
        if d.pack == "Cascadia":
            for yy in range(top + 1, ridge):
                for a in range((x1 if axis == "z" else z1), (x2 if axis == "z" else z2) + 1):
                    for e in ((z1, z2) if axis == "z" else (x1, x2)):
                        x, z = (a, e) if axis == "z" else (e, a)
                        if d.get(x, yy, z) == "minecraft:spruce_planks" and a % 2 == 0:
                            d.set(x, yy, z, log("stripped_spruce_log"))
        if tie:                                                          # tie beams (structure, no lamps)
            if axis == "x":
                for x in range(x1 + 2, x2 - 1, 4):
                    for z in range(z1 + 1, z2):
                        d.set(x, top + 1, z, log(S["post"], "z"))
            else:
                for z in range(z1 + 2, z2 - 1, 4):
                    for x in range(x1 + 1, x2):
                        d.set(x, top + 1, z, log(S["post"], "x"))
    else:
        d.fill(x1, top + 1, z1, x2, top + 1, z2, "smooth_quartz" if d.pack == "Neoterra" else S["band"])
        if parapet:
            for x in range(x1, x2 + 1):
                for z in range(z1, z2 + 1):
                    if x in (x1, x2) or z in (z1, z2):
                        d.set(x, top + 2, z, "white_concrete")
                        d.set(x, top + 3, z, slab("smooth_quartz_slab"))
        for x in range(x1, x2 + 1):                                 # cantilevered roof edge
            for z in (z1 - 1, z2 + 1):
                put(d, x, top + 1, z, slab("smooth_quartz_slab", "top"))
        for z in range(z1, z2 + 1):
            for x in (x1 - 1, x2 + 1):
                put(d, x, top + 1, z, slab("smooth_quartz_slab", "top"))
        ridge = top + 1
    return dict(ys=ys, top=top, ridge=ridge, x1=x1, z1=z1, x2=x2, z2=z2)


# ============================================================================================== HEARTHWOOD
# Mechanics' institute: a timber-framed lecture hall behind a walled front garden (L1), a brick reading room and a
# technical school with a forge (L2), a gallery library upstairs (L3), a theatre at the back (L4), a hostel and a
# commons cottage round a back lawn (L5).

def col_hearthwood(rel, L):
    d = new("Hearthwood", rel, (49, 30, 49))
    W = "dark_oak"
    mnf = 2 if L >= 3 else 1
    # ---------------------------------------------------------------- shells
    M = shell(d, 16, 12, 30, 22, mnf, "gable", "z")
    if L >= 2:
        shell(d, 30, 13, 38, 21, 2 if L >= 3 else 1, "gable", "x", win="nes", mat="bricks", up="bricks")
        T = shell(d, 4, 13, 16, 23, 2 if L >= 5 else 1, "gable", "x", win="nws", mat="bricks", up="bricks")
    if L >= 4:
        shell(d, 14, 26, 36, 38, 1, "gable", "x", wh=7)
    if L >= 5:
        shell(d, 2, 26, 12, 40, 2, "gable", "z", mat="white_terracotta", up="white_terracotta")
        shell(d, 38, 28, 46, 38, 2, "gable", "z", mat="calcite", up="calcite")

    # ---------------------------------------------------------------- front garden (L1+)
    d.fill(4, 1, 1, 44, 1, 8, "grass_block[snowy=false]")
    d.fill(22, 1, 0, 24, 1, 9, "gravel")
    d.fill(21, 1, 1, 21, 1, 8, "stone_bricks")
    d.fill(25, 1, 1, 25, 1, 8, "stone_bricks")
    for x in list(range(3, 21)) + list(range(26, 46)):                 # garden wall along the street
        d.set(x, 2, 0, "brick_wall")
    for x in (21, 25):                                                  # gate piers with lanterns
        place(d, [(x, 2, 0, "stone_bricks"), (x, 3, 0, "stone_bricks"), (x, 4, 0, LS)])
    # portico
    d.fill(21, 1, 9, 25, 1, 11, "polished_andesite")
    for x in (21, 25):
        for y in range(Y0, 6):
            d.set(x, y, 10, "quartz_pillar[axis=y]")
    d.fill(21, 6, 10, 25, 6, 11, "smooth_stone")
    entry(d, 23, 12, "south", step="polished_andesite")
    d.sign(23, 5, 11, "north", ["MECHANICS'", "INSTITUTE"], W)
    # outdoor class on the west lawn: speaker's plinth, two benches facing it, a chalk easel
    d.set(10, 1, 3, "polished_andesite")
    d.set(10, Y0, 3, slab("stone_brick_slab"))
    d.tag(10, Y0, 3, "stand_out")
    d.placed["spots"]["stand_out"] = d.placed["spots"].get("stand_out", 0) + 1
    outseat(d, [(8, 6), (9, 6), (10, 6), (11, 6), (12, 6)], Y0, "south", W)
    outseat(d, [(8, 8), (9, 8), (10, 8), (11, 8), (12, 8)], Y0, "south", W)
    place(d, [(12, 2, 3, "dark_oak_fence"), (12, 3, 3, "black_concrete"), (12, 4, 3, td(W, "north", "bottom")),
              (7, 2, 3, "potted_oxeye_daisy")])
    lamppost(d, 14, 6, "hw")
    lamppost(d, 32, 6, "hw")
    # east lawn: rose border along the wall, an oak with a bench under it
    border = "rodcrodcrodcr"
    fl = {"r": "rose_bush[half=lower]", "o": "oxeye_daisy", "d": "red_tulip", "c": "cornflower"}
    for i, ch in enumerate(border):
        d.set(28 + i, 2, 2, fl[ch])
        if ch == "r":
            d.set(28 + i, 3, 2, "rose_bush[half=upper]")
    plant_tree(d, 36, 6)
    place(d, [(34, 2, 7, st("dark_oak_stairs", "south")), (35, 2, 7, st("dark_oak_stairs", "south")),
              (33, 2, 7, td(W, "west", "bottom", True)), (36, 2, 8, "potted_allium")])
    if L >= 3:                                                          # front beds along the wings
        for x, f in zip(range(4, 16), "dcodcodcodco"):
            d.set(x, 1, 10, "grass_block[snowy=false]")
            d.set(x, 2, 10, fl[f])
        for x in range(39, 46):
            d.set(x, 2, 11, "dark_oak_fence")
        for x, f in zip(range(39, 45), "rcorco"):
            d.set(x, 1, 12, "grass_block[snowy=false]")
            d.set(x, 2, 12, fl[f] if f != "r" else "rose_bush[half=lower]")
            if f == "r":
                d.set(x, 3, 12, "rose_bush[half=upper]")
        lamppost(d, 5, 9, "hw")
        for z in (2, 5, 8):                                             # rose pergola over the garden path
            for x in (21, 25):
                for y in (2, 3, 4):
                    d.set(x, y, z, "dark_oak_fence")
            for x in range(21, 26):
                d.set(x, 5, z, log("stripped_dark_oak_log", "x"))
                d.set(x, 6, z, "flowering_azalea_leaves[distance=1,persistent=true,waterlogged=false]")
        for z in range(1, 12):                                          # side walls of the garden
            d.set(3, 2, z, "brick_wall")
            d.set(45, 2, z, "brick_wall")
        lamppost(d, 15, 9, "hw")
        lamppost(d, 44, 9, "hw")
        plant_tree(d, 5, 5)

    # ---------------------------------------------------------------- lecture hall, ground floor (all levels)
    d.hut(17, Y0, 13, "north")
    d.item(23, Y0, 20, "lectern", "north")
    blackboard(d, 22, 21, 24, 21, Y0 + 1, "north", "black_concrete", W)
    for z in (15, 17):                                                  # two desk rows facing the board
        seat(d, [(19, z), (20, z), (21, z), (25, z), (26, z), (27, z)], Y0, "north", W)
        tops(d, [(19, z + 1), (20, z + 1), (21, z + 1), (25, z + 1), (26, z + 1), (27, z + 1)], Y0, "dark_oak_slab")
    place(d, [(19, 3, 16, cand(1)), (27, 3, 16, cand(2)), (21, 3, 18, cand(1)), (25, 3, 18, "flower_pot")])
    shelf(d, [(29, 15), (29, 16), (29, 18), (29, 19)], Y0, 3)          # book bays between the east windows
    place(d, [(17, 2, 15, chest("east", "left")), (17, 2, 16, chest("east", "right")),
              (17, 3, 15, "potted_red_tulip"), (17, 3, 16, cand(3)),
              (29, 2, 13, "potted_fern"), (17, 2, 21, "potted_fern"), (29, 2, 21, "potted_cornflower"),
              (19, 4, 21, "blue_wall_banner[facing=north]"), (26, 4, 21, "white_wall_banner[facing=north]")])
    carpet(d, [(23, z) for z in range(14, 19)], Y0, "red")
    hang(d, [(20, 14), (26, 14), (20, 18), (26, 18)], 5)
    if mnf > 1:                                                         # stair to the gallery along the north wall
        stair(d, 24, 13, Y0, 7, "east", [(24, 7, 13), (25, 7, 14), (26, 7, 14), (27, 7, 14)])
        # gallery library upstairs
        shelf(d, [(17, 13), (17, 15), (17, 16), (17, 18), (17, 19), (17, 21)], 7, 3)
        shelf(d, [(19, 13), (20, 13), (22, 13), (23, 13)], 7, 3)
        for x0 in (20, 24):                                             # two reading tables
            for x in range(x0, x0 + 3):
                d.set(x, 7, 17, "dark_oak_planks")
            seat(d, [(x0, 16), (x0 + 1, 16), (x0 + 2, 16)], 7, "north", W)
            seat(d, [(x0, 18), (x0 + 1, 18), (x0 + 2, 18)], 7, "south", W)
        place(d, [(21, 8, 17, cand(3)), (25, 8, 17, cand(2)), (26, 8, 17, "potted_red_tulip")])
        for z in (15, 19):                                              # carrels at the east wall
            d.set(29, 7, z, slab("dark_oak_slab", "top"))
            d.set(29, 8, z, cand(1))
            d.chair(28, 7, z, "west", W)
        place(d, [(29, 7, 21, "potted_fern"), (18, 7, 21, "potted_allium")])
        carpet(d, [(23, z) for z in range(15, 21)], 7, "red")
        hang(d, [(21, 14), (25, 14), (21, 18), (25, 18)], 10)

    # ---------------------------------------------------------------- reading room (L2+)
    if L >= 2:
        link(d, 30, Y0, 17, "east")
        d.sign(34, 4, 12, "north", ["READING", "ROOM"], W)
        shelf(d, [(31, 14), (33, 14), (34, 14), (36, 14), (37, 14)], Y0, 3)
        shelf(d, [(33, 20), (34, 20)], Y0, 2)
        d.item(37, Y0, 17, "lectern", "west")
        for x in range(32, 36):
            d.set(x, Y0, 17, "dark_oak_planks")
        seat(d, [(x, 16) for x in range(32, 36)], Y0, "north", W)
        seat(d, [(x, 18) for x in range(32, 36)], Y0, "south", W)
        place(d, [(33, 3, 17, cand(2)), (34, 3, 17, "potted_red_tulip"), (35, 3, 17, cand(1)),
                  (37, 2, 20, slab("dark_oak_slab", "top")), (37, 3, 20, LS), (36, 2, 20, st("dark_oak_stairs", "south")),
                  (31, 2, 20, "potted_fern")])
        hang(d, [(32, 15), (36, 19)], 5)
        if L >= 3:                                                      # seminar room upstairs
            link(d, 30, 7, 17, "east")
            for x in range(33, 36):
                for z in (16, 17):
                    d.set(x, 7, z, "dark_oak_planks")
            seat(d, [(33, 15), (34, 15), (35, 15)], 7, "north", W)
            seat(d, [(33, 18), (34, 18), (35, 18)], 7, "south", W)
            seat(d, [(36, 16), (36, 17)], 7, "east", W)
            blackboard(d, 37, 16, 37, 17, 8, "west", "black_concrete", W)
            shelf(d, [(31, 14), (33, 14), (34, 14), (36, 14), (37, 14)], 7, 3)
            shelf(d, [(33, 20), (34, 20), (36, 20), (37, 20)], 7, 2)
            place(d, [(34, 8, 16, cand(3)), (34, 8, 17, "flower_pot"), (31, 7, 20, "potted_oxeye_daisy")])
            hang(d, [(32, 17), (36, 15)], 10)

    # ---------------------------------------------------------------- technical school with forge (L2+)
    if L >= 2:
        link(d, 16, Y0, 17, "west")
        d.sign(10, 4, 12, "north", ["TECHNICAL", "SCHOOL"], W)
        chimney(d, 4, 18, Y0, T["ridge"] + 1)
        d.hearth(5, Y0, 18, "east", 6, "bricks", "campfire")
        place(d, [(5, 2, 14, "barrel[facing=up,open=false]"), (5, 2, 15, "water_cauldron[level=3]"),
                  (5, 2, 16, "smithing_table"), (5, 2, 20, "blast_furnace[facing=east,lit=false]"),
                  (5, 2, 21, "grindstone[face=floor,facing=east]"), (5, 2, 22, "barrel[facing=up,open=false]"),
                  (7, 2, 18, "anvil[facing=north]"),
                  (7, 2, 14, "crafting_table"), (8, 2, 14, slab("dark_oak_slab", "top")),
                  (10, 2, 14, "fletching_table"), (11, 2, 14, slab("dark_oak_slab", "top")),
                  (13, 2, 14, "stonecutter[facing=south]"), (14, 2, 14, "loom[facing=south]"),
                  (8, 3, 14, "flower_pot"), (11, 3, 14, cand(1))])
        for x in (7, 8, 10, 11, 13, 14):                                # tool wall above the benches
            d.set(x, 4, 14, td(W, "south", "bottom", True))
        tops(d, [(9, 18), (10, 18), (11, 18)], Y0, "dark_oak_slab")     # demonstration bench
        place(d, [(9, 3, 18, cand(2)), (11, 3, 18, LS)])
        seat(d, [(9, 19), (11, 19)], Y0, "south", W)
        seat(d, [(10, 17)], Y0, "north", W)
        place(d, [(6, 2, 22, log("stripped_oak_log", "x")), (7, 2, 22, log("stripped_oak_log", "x")),
                  (8, 2, 22, log("stripped_oak_log", "x")), (7, 3, 22, log("stripped_oak_log", "x")),
                  (10, 2, 22, "barrel[facing=up,open=false]"), (11, 2, 22, "barrel[facing=up,open=false]"),
                  (13, 2, 22, chest("north", "left")), (14, 2, 22, chest("north", "right")),
                  (15, 4, 15, "blue_wall_banner[facing=west]"), (15, 4, 20, "red_wall_banner[facing=west]")])
        hang(d, [(10, 16), (10, 20), (14, 18)], 5)
        if L >= 5:                                                      # drawing class upstairs
            link(d, 16, 7, 17, "west")
            blackboard(d, 5, 16, 5, 20, 8, "east", "black_concrete", W)
            tops(d, [(7, 17), (7, 18)], 7, "dark_oak_slab")
            d.set(7, 8, 17, cand(1))
            d.chair(6, 7, 18, "west", W, sit=False)
            for z in (15, 16, 19, 20, 21):
                tops(d, [(9, z), (12, z)], 7, "dark_oak_slab")
                seat(d, [(10, z), (13, z)], 7, "east", W)
            shelf(d, [(15, 14), (15, 15), (15, 20), (15, 21), (15, 22)], 7, 2)
            place(d, [(5, 7, 14, "potted_fern"), (5, 7, 22, "potted_red_tulip"), (9, 8, 15, "flower_pot")])
            hang(d, [(10, 16), (10, 20), (6, 18)], 10)

    # ---------------------------------------------------------------- theatre (L4+)
    if L >= 4:
        entry(d, 25, 26, "south", double=True, step="stone_bricks")
        d.fill(25, 1, 23, 26, 1, 25, "stone_bricks")
        d.sign(25, 5, 25, "north", ["THEATRE"], W)
        d.fill(17, 2, 35, 33, 2, 37, "dark_oak_planks")                 # stage
        place(d, [(24, 2, 34, st("dark_oak_stairs", "south")), (27, 2, 34, st("dark_oak_stairs", "south"))])
        for x in (17, 33):                                              # proscenium curtains
            for y in range(3, 8):
                d.set(x, y, 35, "red_wool")
        d.fill(17, 8, 35, 33, 8, 35, "red_wool")
        blackboard(d, 23, 37, 28, 37, 4, "north", "black_concrete", W)
        d.item(29, 3, 36, "lectern", "north")
        place(d, [(18, 3, 37, "potted_fern"), (32, 3, 37, "potted_fern"), (21, 3, 36, "red_candle[candles=3,lit=false,waterlogged=false]")])
        for z in (29, 31, 33):
            seat(d, [(x, z) for x in range(16, 24)] + [(x, z) for x in range(28, 35)], Y0, "north", W)
        carpet(d, [(x, z) for x in (25, 26) for z in range(27, 34)], Y0, "red")
        place(d, [(15, 5, 30, "red_wall_banner[facing=east]"), (15, 5, 33, "white_wall_banner[facing=east]"),
                  (35, 5, 30, "red_wall_banner[facing=west]"), (35, 5, 33, "white_wall_banner[facing=west]")])
        hang(d, [(20, 30), (28, 30), (24, 33)], 8)

    # ---------------------------------------------------------------- hostel and commons (L5)
    if L >= 5:
        entry(d, 7, 26, "south", step="stone_bricks")
        d.sign(7, 5, 25, "north", ["HOSTEL"], W)
        stair(d, 11, 28, Y0, 7, "south", [(10, 7, 29), (10, 7, 30), (10, 7, 31), (11, 7, 28)])
        chimney(d, 2, 33, Y0, 16)
        d.hearth(3, Y0, 33, "east", 6, "bricks", "campfire")
        # common room by the fire
        seat(d, [(6, 32), (6, 33), (6, 34)], Y0, "east", W)
        place(d, [(5, 2, 33, td(W, "north")), (5, 3, 33, "potted_red_tulip")])
        d.chair(4, Y0, 31, "north", W)
        d.chair(4, Y0, 35, "south", W)
        carpet(d, [(4, 32), (4, 33), (4, 34), (5, 32), (5, 34)], Y0, "red")
        seat(d, [(4, 27), (5, 27)], Y0, "north", W)                     # hall bench, coat chest, notices
        place(d, [(9, 2, 27, chest("south", "right")), (10, 2, 27, chest("south", "left")),
                  (8, 4, 27, "white_wall_banner[facing=south]"), (9, 3, 27, "potted_fern")])
        for x in range(5, 9):                                           # dining table
            d.set(x, Y0, 37, "dark_oak_planks")
        seat(d, [(x, 36) for x in range(5, 9)], Y0, "north", W)
        seat(d, [(x, 38) for x in range(5, 9)], Y0, "south", W)
        d.chair(4, Y0, 37, "west", W)
        d.chair(9, Y0, 37, "east", W)
        place(d, [(6, 3, 37, cand(3)), (7, 3, 37, "flower_pot"),
                  (11, 2, 35, "smoker[facing=west,lit=false]"), (11, 2, 36, slab("dark_oak_slab", "top")),
                  (11, 3, 36, "cake[bites=0]"), (11, 2, 37, "barrel[facing=west,open=false]"),
                  (11, 2, 38, slab("dark_oak_slab", "top")), (11, 3, 38, "flower_pot")])
        hang(d, [(7, 29), (8, 33), (7, 37)], 5)
        # dormitory upstairs
        for z in (28, 30, 32, 35, 37, 39):
            d.bed(3, 7, z, "west", "blue")
        for z in (29, 31, 36, 38):
            d.set(3, 7, z, slab("dark_oak_slab", "top"))
            d.set(3, 8, z, cand(1))
        place(d, [(3, 7, 33, chest("east", "left")), (3, 7, 34, chest("east", "right")),
                  (11, 7, 35, slab("dark_oak_slab", "top")), (11, 8, 35, cand(2)),
                  (11, 7, 37, slab("dark_oak_slab", "top")), (11, 8, 37, "flower_pot"),
                  (11, 7, 39, chest("west"))])
        seat(d, [(10, 35), (10, 37)], 7, "west", W)
        carpet(d, [(7, z) for z in range(28, 40)], 7, "blue")
        hang(d, [(7, 28), (7, 32), (7, 36)], 10)
        # commons cottage: café with fireplace downstairs, tutor's flat upstairs
        entry(d, 42, 28, "south", step="stone_bricks")
        d.sign(42, 4, 27, "north", ["COMMONS"], W)
        stair(d, 45, 30, Y0, 7, "south", [(44, 7, 31), (44, 7, 32), (44, 7, 33), (45, 7, 30)])
        chimney(d, 38, 33, Y0, 16)
        d.hearth(39, Y0, 33, "east", 6, "bricks", "campfire")
        d.chair(41, Y0, 32, "east", W)
        d.chair(41, Y0, 34, "east", W)
        carpet(d, [(40, 32), (40, 33), (40, 34)], Y0, "red")
        place(d, [(39, 2, 37, "smoker[facing=north,lit=true]"), (40, 2, 37, slab("smooth_stone_slab", "top")),
                  (41, 2, 37, "water_cauldron[level=3]"), (42, 2, 37, slab("smooth_stone_slab", "top")),
                  (43, 2, 37, "furnace[facing=north,lit=false]"), (44, 2, 37, "barrel[facing=up,open=false]"),
                  (40, 3, 37, "flower_pot"), (42, 3, 37, cand(1)), (39, 2, 29, "potted_red_tulip")])
        tops(d, [(40, 35), (41, 35), (42, 35), (43, 35)], Y0, "dark_oak_slab")
        place(d, [(41, 3, 35, "cake[bites=0]"), (43, 3, 35, cand(2))])
        d.table(43, Y0, 31, W)
        d.chair(43, Y0, 30, "north", W)
        d.chair(42, Y0, 31, "west", W)
        d.chair(44, Y0, 31, "east", W)
        d.chair(43, Y0, 32, "south", W)
        hang(d, [(42, 30), (41, 36)], 5)
        d.bed(39, 7, 30, "west", "red")
        d.bed(39, 7, 32, "west", "red")
        place(d, [(39, 7, 31, slab("dark_oak_slab", "top")), (39, 8, 31, cand(1)),
                  (41, 7, 37, slab("dark_oak_slab", "top")), (41, 8, 37, cand(1)), (43, 7, 37, chest("north")),
                  (44, 7, 37, "potted_fern")])
        shelf(d, [(39, 37), (39, 36)], 7, 2)
        d.chair(41, 7, 36, "north", W)
        carpet(d, [(41, 31), (42, 31), (41, 32), (42, 32), (41, 33), (42, 33)], 7, "orange")
        hang(d, [(42, 30), (42, 34)], 10)
        # back lawn: orchard row, beds, a bench pair
        d.fill(2, 1, 41, 46, 1, 48, "grass_block[snowy=false]")
        d.fill(13, 1, 39, 13, 1, 48, "gravel")
        for x, z in ((6, 44), (20, 45), (30, 44), (42, 45)):
            plant_tree(d, x, z)
        for x, f in zip(range(15, 28), "dcodcodcodcod"):
            d.set(x, 2, 47, fl[f])
        outseat(d, [(24, 42), (25, 42)], Y0, "north", W)
        outseat(d, [(35, 42), (36, 42)], Y0, "north", W)
        lamppost(d, 14, 42, "hw")
        lamppost(d, 37, 40, "hw")
    return d


# ============================================================================================== NEOTERRA
# Learning pavilion: a glass lecture pavilion behind an outdoor amphitheatre (L1), maker space (L2), learning
# commons upstairs with roof gardens (L3), a three-storey library (L4), a studio tower and a café (L5).

QS = "smooth_quartz_slab"


def nt_table(d, x, y, z, chairs):
    """One four-seat study table: white post table with the listed chairs (n/s/e/w)."""
    d.table(x, y, z, "birch")
    for c in chairs:
        dx, dz = D4[{"n": "north", "s": "south", "e": "east", "w": "west"}[c]]
        d.chair(x + dx, y, z + dz, {"n": "north", "s": "south", "e": "east", "w": "west"}[c], "birch")


def nt_planter(d, x, y, z, top="flowering_azalea"):
    d.set(x, y, z, "moss_block")
    d.set(x, y + 1, z, top)


def col_neoterra(rel, L):
    d = new("Neoterra", rel, (51, 30, 51), paving="smooth_stone")
    B = "birch"
    Q = "smooth_quartz"
    nf = 2 if L >= 3 else 1
    # ---------------------------------------------------------------- shells
    P = shell(d, 14, 16, 30, 26, nf, "flat", glassy=True, win="nsw")
    if L >= 2:
        MK = shell(d, 30, 16, 40, 26, nf, "flat", win="ns", mat="orange_terracotta", up="mangrove_planks")
    if L >= 4:
        LB = shell(d, 2, 16, 14, 32, 3, "flat", glassy=True, win="nsw", mat="white_concrete", up="mangrove_planks")
    if L >= 5:
        ST = shell(d, 36, 30, 46, 40, 5, "flat", glassy=True, win="nsew", mat="white_concrete", up="mangrove_planks")
        CF = shell(d, 16, 30, 30, 38, 1, "flat", glassy=True, win="nsw")
    entry(d, 22, 16, "south", double=True, step="polished_andesite")
    d.sign(22, 6, 15, "north", ["LEARNING", "PAVILION"], B, glow=True, color="orange")

    # ---------------------------------------------------------------- amphitheatre (L1+)
    for x in range(16, 29):
        for z in (13, 14):
            d.set(x, 1, z, "polished_andesite")
    d.spot(22, Y0, 14, "stand_out")
    if L >= 2:
        d.item(24, Y0, 14, "lectern", "north")
    for k, z in ((1, 9), (2, 7)):                                        # two raised tiers behind the front row
        d.fill(15, Y0, z - 1, 29, Y0 + k - 1, z, Q)
    for k, z in ((0, 11), (1, 9), (2, 7)):
        outseat(d, [(x, z) for x in range(16, 29) if x != 22], Y0 + k, "north", B)
    lamppost(d, 14, 13, "nt")
    lamppost(d, 30, 13, "nt")
    place(d, [(15, 2, 11, "potted_bamboo"), (29, 2, 11, "potted_bamboo")])
    if L >= 3:                                                          # shade canopy over the stage
        d.fill(14, 7, 12, 30, 7, 13, slab(QS, "top"))
        for x in (14, 30):
            d.fill(x, Y0, 12, x, 6, 12, "white_concrete")
        panel(d, [(18, 13), (22, 13), (26, 13)], 7)

    # ---------------------------------------------------------------- pavilion lecture room (all levels)
    d.hut(15, Y0, 17, "north")
    d.item(28, Y0, 21, "lectern", "west")
    d.fill(29, 4, 19, 29, 5, 23, "black_concrete")                      # wall screen
    d.fill(29, 3, 19, 29, 3, 23, slab("smooth_stone_slab", "top"))
    for z in (18, 19, 20, 22, 23, 24):                                  # two desk columns facing the screen
        seat(d, [(19, z), (23, z)], Y0, "west", B)
        tops(d, [(20, z), (24, z)], Y0, QS)
    place(d, [(20, 3, 18, cand(1, "white")), (24, 3, 20, "flower_pot"), (24, 3, 23, cand(1, "cyan"))])
    shelf(d, [(29, 17), (29, 18), (29, 24), (29, 25)], Y0, 3)
    place(d, [(15, 2, 25, "potted_bamboo"), (26, 2, 25, "potted_bamboo"), (26, 2, 17, "potted_white_tulip")])
    carpet(d, [(x, 21) for x in range(21, 28)], Y0, "cyan")
    panel(d, [(18, 21), (22, 19), (22, 23), (26, 21)], 6)
    if nf == 1:
        seat(d, [(15, 21), (15, 22), (15, 23)], Y0, "west", B)           # waiting bench by the glass
    else:
        stair(d, 16, 19, Y0, 7, "south", [(17, 7, 20), (17, 7, 21), (17, 7, 22), (16, 7, 19)],
              block="smooth_quartz_stairs", under=Q, fence="glass_pane")
        # learning commons upstairs: four study pods and a book wall
        nt_table(d, 20, 7, 19, "nswe")
        nt_table(d, 25, 7, 19, "nswe")
        nt_table(d, 20, 7, 23, "nswe")
        nt_table(d, 25, 7, 23, "nsw")
        shelf(d, [(29, 17), (29, 18), (29, 19), (29, 23), (29, 24), (29, 25)], 7, 3)
        place(d, [(15, 7, 17, "potted_bamboo"), (15, 7, 25, "potted_bamboo"), (22, 7, 25, "potted_white_tulip")])
        carpet(d, [(22, z) for z in range(17, 26)], 7, "light_gray")
        panel(d, [(20, 21), (25, 21)], 11)
    ry = P["top"] + 2                                                   # roof garden
    for x, z in ((15, 17), (29, 17), (15, 25), (29, 25), (22, 25)):
        nt_planter(d, x, ry, z)
    place(d, [(27, ry, 19, "smooth_stone"), (27, ry + 1, 19, "iron_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]"),
              (17, ry, 21, "lightning_rod[facing=up,powered=false,waterlogged=false]")])
    for x in range(18, 26):
        d.set(x, ry, 23, "moss_block")
        d.set(x, ry + 1, 23, "azalea" if x % 2 else "fern")

    # ---------------------------------------------------------------- maker space (L2+)
    if L >= 2:
        link(d, 30, Y0, 21, "east")
        d.sign(35, 6, 15, "north", ["MAKER", "SPACE"], B, glow=True, color="orange")
        place(d, [(31, 2, 17, "crafting_table"), (33, 2, 17, "smithing_table"), (34, 2, 17, "stonecutter[facing=south]"),
                  (36, 2, 17, "loom[facing=south]"), (37, 2, 17, "cartography_table"),
                  (39, 2, 17, "grindstone[face=floor,facing=south]")])
        for x in (33, 34, 36, 37):
            d.set(x, 4, 17, td(B, "south", "bottom", True))
        tops(d, [(33, 21), (34, 21), (35, 21), (36, 21)], Y0, "smooth_stone_slab")   # build island
        place(d, [(34, 3, 21, LS), (35, 3, 21, "flower_pot"), (36, 3, 21, "lightning_rod[facing=up,powered=false,waterlogged=false]")])
        seat(d, [(33, 22), (36, 22)], Y0, "south", B)
        seat(d, [(34, 20), (35, 20)], Y0, "north", B)
        place(d, [(31, 2, 25, "barrel[facing=up,open=false]"), (31, 3, 25, "barrel[facing=up,open=false]"),
                  (32, 2, 25, "barrel[facing=up,open=false]"), (34, 2, 25, chest("north", "left")),
                  (35, 2, 25, chest("north", "right")), (37, 2, 25, "anvil[facing=east]"), (39, 2, 25, "potted_bamboo")])
        shelf(d, [(36, 25), (38, 25)], Y0, 2)                           # manuals and pattern books
        tops(d, [(39, 20), (39, 21), (39, 22)], Y0, "birch_slab")       # pegboard bench on the east wall
        for z in range(19, 24):
            d.set(39, 4, z, td(B, "west", "bottom", True))
        d.set(39, 3, 21, "flower_pot")
        panel(d, [(33, 19), (37, 23)], 6)
        for x in (32, 35, 38):
            nt_planter(d, x, 2, 14)
        plant_tree(d, 34, 10)                                           # street trees by the maker space
        plant_tree(d, 39, 10)
        ry2 = MK["top"] + 2                                             # solar array on the roof
        for z in (19, 20, 22, 23):
            for x in range(32, 39):
                d.set(x, ry2, z, "daylight_detector[inverted=false,power=0]")
        if nf > 1:                                                      # classroom upstairs
            link(d, 30, 7, 21, "east")
            d.fill(39, 8, 19, 39, 9, 23, "gray_concrete")
            tops(d, [(37, 23), (37, 24)], 7, QS)
            d.set(37, 8, 24, cand(1, "white"))
            d.chair(38, 7, 23, "east", B, sit=False)
            for z in (18, 19, 20, 22, 23, 24):
                seat(d, [(31, z), (34, z)], 7, "west", B)
                tops(d, [(32, z), (35, z)], 7, QS)
            shelf(d, [(x, 25) for x in range(31, 40)], 7, 1)
            place(d, [(39, 7, 17, "potted_bamboo"), (31, 7, 17, "potted_white_tulip")])
            panel(d, [(33, 21), (37, 21)], 11)

    # ---------------------------------------------------------------- library (L4+)
    if L >= 4:
        link(d, 14, Y0, 21, "west")
        d.sign(8, 6, 15, "north", ["LIBRARY"], B, glow=True, color="orange")
        stair(d, 3, 30, Y0, 7, "north", [(4, 7, 27), (4, 7, 28), (4, 7, 29), (3, 7, 30)],
              block="smooth_quartz_stairs", under=Q, fence="glass_pane")
        stair(d, 13, 18, 7, 12, "south", [(12, 12, 19), (12, 12, 20), (12, 12, 21), (13, 12, 18)],
              block="smooth_quartz_stairs", under=Q, fence="glass_pane")
        # ground: issue desk, reading table, two double-sided stacks
        tops(d, [(11, 18), (12, 18), (11, 19)], Y0, QS)
        place(d, [(11, 3, 18, LS), (12, 3, 18, "flower_pot"), (3, 2, 17, "potted_bamboo"), (10, 2, 31, "potted_bamboo")])
        d.chair(12, Y0, 17, "north", B, sit=False)
        for x in range(5, 9):
            d.set(x, Y0, 20, Q)
        seat(d, [(x, 19) for x in range(5, 9)], Y0, "north", B)
        seat(d, [(x, 21) for x in range(5, 9)], Y0, "south", B)
        place(d, [(6, 3, 20, cand(1, "white")), (8, 3, 20, "potted_white_tulip")])
        stacks = [(x, z) for z in (24, 27) for x in range(5, 12)]
        shelf(d, stacks, Y0, 2)
        panel(d, [(7, 20), (8, 22), (8, 29)], 6)
        # first floor: carrels on the west glass, lounge, two stacks
        for z in (18, 20, 22):
            d.set(3, 7, z, slab(QS, "top"))
            d.chair(4, 7, z, "east", B)
        place(d, [(3, 8, 18, cand(1, "cyan")), (3, 8, 22, "flower_pot")])
        seat(d, [(7, 19), (8, 19)], 7, "north", B)
        seat(d, [(7, 21), (8, 21)], 7, "south", B)
        place(d, [(7, 7, 20, td(B, "north")), (8, 7, 20, td(B, "north")), (8, 8, 20, "potted_bamboo"),
                  (11, 7, 17, "potted_white_tulip")])
        carpet(d, [(x, z) for x in (6, 9) for z in (19, 20, 21)], 7, "cyan")
        shelf(d, [(x, z) for z in (26, 29) for x in range(6, 12)], 7, 2)
        panel(d, [(8, 20), (9, 27)], 11)
        # second floor: archive stacks and a seminar table
        shelf(d, [(x, z) for z in (22, 26) for x in range(4, 11)], 12, 3)
        for x in range(5, 10):
            d.set(x, 12, 30, Q)
        seat(d, [(x, 29) for x in range(5, 10)], 12, "north", B)
        seat(d, [(x, 31) for x in range(5, 10)], 12, "south", B)
        place(d, [(7, 13, 30, LS), (3, 12, 17, "potted_bamboo"), (11, 12, 17, "potted_bamboo")])
        panel(d, [(7, 20), (7, 28)], 16)
        ry3 = LB["top"] + 2
        for x, z in ((3, 17), (13, 17), (3, 31), (13, 31)):
            nt_planter(d, x, ry3, z)
        for z in range(20, 29, 2):
            d.set(8, ry3, z, "moss_block")
            d.set(8, ry3 + 1, z, "flowering_azalea")

    # ---------------------------------------------------------------- studio tower and café (L5)
    if L >= 5:
        entry(d, 41, 30, "south", double=True, step="polished_andesite")
        d.sign(41, 6, 29, "north", ["STUDIOS"], B, glow=True, color="orange")
        stair(d, 37, 31, 2, 7, "south", [(38, 7, 32), (38, 7, 33), (38, 7, 34), (37, 7, 31)],
              block="smooth_quartz_stairs", under=Q, fence="glass_pane")
        stair(d, 45, 39, 7, 12, "north", [(44, 12, 36), (44, 12, 37), (44, 12, 38), (45, 12, 39)],
              block="smooth_quartz_stairs", under=Q, fence="glass_pane")
        stair(d, 37, 31, 12, 17, "south", [(38, 17, 32), (38, 17, 33), (38, 17, 34), (37, 17, 31)],
              block="smooth_quartz_stairs", under=Q, fence="glass_pane")
        stair(d, 45, 39, 17, 22, "north", [(44, 22, 36), (44, 22, 37), (44, 22, 38), (45, 22, 39)],
              block="smooth_quartz_stairs", under=Q, fence="glass_pane")
        # ground: gallery lobby with reception and sculpture plinths
        tops(d, [(44, 32), (44, 33)], 2, QS)
        d.chair(45, 2, 32, "east", B, sit=False)
        d.set(44, 3, 33, "potted_white_tulip")
        seat(d, [(40, 34), (41, 34)], 2, "north", B)
        seat(d, [(40, 36), (41, 36)], 2, "south", B)
        place(d, [(40, 2, 35, td(B, "north")), (41, 2, 35, td(B, "north")),
                  (39, 2, 39, "chiseled_quartz_block"), (39, 3, 39, "decorated_pot[cracked=false,facing=north,waterlogged=false]"),
                  (43, 2, 39, "chiseled_quartz_block"), (43, 3, 39, "amethyst_cluster[facing=up,waterlogged=false]"),
                  (45, 2, 38, "quartz_pillar[axis=y]"), (45, 3, 38, "potted_bamboo")])
        panel(d, [(41, 33), (41, 37)], 6)
        # 1st: painting studio – easels, paint table, supply barrels
        for x in (40, 42):
            place(d, [(x, 7, 38, "birch_fence"), (x, 8, 38, td(B, "north", "bottom", True))])
            d.chair(x, 7, 37, "north", B)
        tops(d, [(40, 33), (41, 33), (42, 33)], 7, "birch_slab")
        place(d, [(40, 8, 33, "flower_pot"), (41, 8, 33, cand(2, "red")), (42, 8, 33, cand(3, "cyan")),
                  (44, 7, 31, "barrel[facing=up,open=false]"), (45, 7, 31, "barrel[facing=up,open=false]"),
                  (39, 7, 39, "decorated_pot[cracked=false,facing=north,waterlogged=false]")])
        carpet(d, [(x, z) for x in (40, 41, 42) for z in (35, 36)], 7, "yellow")
        panel(d, [(41, 34), (41, 37)], 11)
        # 2nd: music room – piano, drum kit, listening chairs, record player
        place(d, [(42, 12, 34, "polished_blackstone"), (43, 12, 34, "polished_blackstone"),
                  (42, 13, 34, "white_carpet"), (43, 13, 34, "black_carpet"),
                  (39, 12, 38, "note_block[instrument=basedrum,note=0,powered=false]"),
                  (40, 12, 38, "note_block[instrument=snare,note=0,powered=false]"),
                  (41, 12, 38, "note_block[instrument=hat,note=0,powered=false]"),
                  (44, 12, 31, "jukebox[has_record=false]")])
        d.chair(42, 12, 35, "south", B)
        seat(d, [(40, 32), (41, 32)], 12, "north", B)
        carpet(d, [(x, z) for x in (40, 41, 42) for z in (36, 37)], 12, "purple")
        panel(d, [(41, 34), (41, 37)], 16)
        # 3rd: design studio – drafting tables, loom and map table
        for x in (40, 42):
            d.set(x, 17, 36, slab("birch_slab", "top"))
            d.chair(x, 17, 37, "south", B)
        place(d, [(40, 18, 36, cand(1, "white")), (43, 17, 31, "cartography_table"), (44, 17, 31, "loom[facing=south]"),
                  (39, 17, 39, "potted_bamboo")])
        tops(d, [(40, 33), (41, 33)], 17, QS)
        d.set(41, 18, 33, "flower_pot")
        panel(d, [(41, 34), (41, 37)], 21)
        # 4th: seminar room with the city view
        for x in range(40, 43):
            for z in (34, 35):
                d.set(x, 22, z, Q)
        seat(d, [(40, 33), (41, 33), (42, 33)], 22, "north", B)
        seat(d, [(40, 36), (41, 36), (42, 36)], 22, "south", B)
        place(d, [(41, 23, 34, cand(3, "white")), (41, 23, 35, "potted_white_tulip"), (39, 22, 39, "potted_bamboo")])
        panel(d, [(41, 34), (41, 37)], 26)
        ry4 = ST["top"] + 2
        for x in range(38, 45):
            for z in (33, 34, 36, 37):
                d.set(x, ry4, z, "daylight_detector[inverted=false,power=0]")
        # café: kitchen line on the east wall, servery, three tables
        entry(d, 23, 30, "south", double=True, step="polished_andesite")
        d.sign(23, 6, 29, "north", ["CAFE"], B, glow=True, color="orange")
        place(d, [(29, 2, 32, "smoker[facing=west,lit=true]"), (29, 2, 33, slab(QS, "top")),
                  (29, 2, 34, "water_cauldron[level=3]"), (29, 2, 35, slab(QS, "top")),
                  (29, 2, 36, "furnace[facing=west,lit=false]"), (29, 2, 37, "barrel[facing=up,open=false]")])
        tops(d, [(27, z) for z in range(32, 37)], Y0, QS)
        place(d, [(27, 3, 33, "cake[bites=0]"), (27, 3, 35, "flower_pot"), (29, 3, 33, "potted_bamboo")])
        nt_table(d, 19, 2, 33, "nswe")
        nt_table(d, 23, 2, 35, "nswe")
        nt_table(d, 19, 2, 37, "nwe")
        place(d, [(17, 2, 31, "potted_bamboo"), (25, 2, 37, "potted_white_tulip")])
        panel(d, [(20, 34), (24, 33), (28, 34)], 6)
        ry5 = CF["top"] + 2
        for x, z in ((17, 31), (29, 31), (17, 37), (29, 37)):
            nt_planter(d, x, ry5, z)
        for x in range(19, 28):
            d.set(x, ry5, 34, "daylight_detector[inverted=false,power=0]")
        # back lawn
        d.fill(2, 1, 42, 48, 1, 49, "grass_block[snowy=false]")
        d.fill(2, 1, 41, 48, 1, 41, "smooth_stone")
        for x, z in ((6, 45), (18, 46), (30, 45), (44, 46)):
            plant_tree(d, x, z)
        outseat(d, [(11, 46), (12, 46)], Y0, "south", B)
        outseat(d, [(36, 46), (37, 46)], Y0, "south", B)
        lamppost(d, 14, 44, "nt")
        lamppost(d, 34, 44, "nt")
    return d


# ============================================================================================== CASCADIA
# Valley college: a long log hall with a deep porch and a fire circle for outdoor classes (L1), a woodshop and a
# library lodge (L2), study lofts (L3), a bunkhouse with porch (L4), a sawmill classroom, greenhouse and ag barn (L5).

def col_cascadia(rel, L):
    d = new("Cascadia", rel, (53, 28, 51), paving="coarse_dirt")
    S = "spruce"
    mnf = 2 if L >= 3 else 1
    # ---------------------------------------------------------------- shells
    H = shell(d, 12, 16, 30, 26, mnf, "gable", "x")
    if L >= 2:
        shell(d, 30, 17, 38, 25, 1, "gable", "z", win="nes", mat="stripped_spruce_log", up="stripped_spruce_log")
        shell(d, 2, 16, 12, 26, 2 if L >= 3 else 1, "gable", "z", win="nws", mat="stripped_dark_oak_log",
              up="stripped_dark_oak_log")
    if L >= 4:
        BK = shell(d, 36, 30, 50, 40, 2, "gable", "x", mat="mangrove_planks", up="mangrove_planks")
    if L >= 5:
        shell(d, 36, 42, 50, 50, 2, "gable", "x", mat="stripped_spruce_log", up="stripped_spruce_log")
        shell(d, 20, 32, 32, 44, 1, "gable", "z", mat="mangrove_planks", up="mangrove_planks", wh=6)
    chimney(d, 12, 22, Y0, H["ridge"] + 1)                              # shared stone chimney, two hearths

    # ---------------------------------------------------------------- porch and entrance
    d.fill(12, 1, 13, 30, 1, 15, "spruce_planks")
    for x in (12, 18, 24, 30):
        for y in range(Y0, 6):
            d.set(x, y, 13, log("spruce_log"))
    for x in range(11, 32):
        d.set(x, 6, 12, st("spruce_stairs", "south"))
        for z in range(13, 16):
            d.set(x, 6, z, slab("spruce_slab"))
    entry(d, 21, 16, "south", step="spruce_planks")
    d.sign(21, 4, 15, "north", ["VALLEY", "COLLEGE"], S)
    hang(d, [(15, 14), (27, 14)], 5)
    seat(d, [(14, 15), (15, 15)], Y0, "south", S)                       # porch bench and a rocking chair
    place(d, [(26, 2, 15, "barrel[facing=up,open=false]"), (27, 2, 15, "barrel[facing=up,open=false]"),
              (26, 3, 15, "potted_fern")])
    d.chair(28, Y0, 14, "west", S)

    # ---------------------------------------------------------------- fire circle (L1+)
    d.layer(1, 16, 1, ["           ", "           ", "           ", "     g     ", "    ggg    ", "   ggggg   ",
                       "    ggg    ", "     g     "], {"g": "gravel"})
    d.set(21, Y0, 6, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    outseat(d, [(20, 3), (21, 3), (22, 3)], Y0, "north", S)
    outseat(d, [(18, 5), (18, 6), (18, 7)], Y0, "west", S)
    outseat(d, [(24, 5), (24, 6), (24, 7)], Y0, "east", S)
    d.set(21, 1, 9, log("stripped_spruce_log"))
    d.spot(21, Y0, 9, "stand_out")
    if L >= 2:
        d.item(22, Y0, 9, "lectern", "north")
    place(d, [(16, 2, 9, log("spruce_log", "x")), (17, 2, 9, log("spruce_log", "x")), (16, 3, 9, log("spruce_log", "x"))])
    lamppost(d, 16, 3, "cs")
    lamppost(d, 26, 3, "cs")

    # ---------------------------------------------------------------- hall: lecture room (all levels)
    d.hut(13, Y0, 17, "north")
    d.item(28, Y0, 21, "lectern", "west")
    blackboard(d, 29, 19, 29, 23, Y0 + 1, "west", "black_concrete", S)
    for z in (18, 19, 20, 22, 23, 24):                                  # benches with desks facing the board
        seat(d, [(18, z), (22, z)], Y0, "west", S)
        tops(d, [(19, z), (23, z)], Y0, "spruce_slab")
    place(d, [(19, 3, 18, cand(1)), (23, 3, 20, LS), (23, 3, 24, cand(2))])
    d.hearth(13, Y0, 22, "east", 6, "cobblestone", "campfire")
    seat(d, [(15, 21), (15, 23)], Y0, "east", S)
    carpet(d, [(14, 21), (14, 22), (14, 23)], Y0, "brown")
    place(d, [(13, 2, 19, chest("east", "left")), (13, 2, 20, chest("east", "right")), (13, 3, 19, "potted_fern"),
              (29, 2, 17, "potted_fern"), (29, 2, 25, "potted_fern")])
    shelf(d, [(21, 25), (22, 25), (24, 25), (25, 25), (27, 25), (28, 25)], Y0, 2)
    shelf(d, [(23, 25), (26, 25)], Y0, 1)
    hang(d, [(18, 19), (18, 23), (26, 19), (26, 23)], 5)
    if mnf > 1:
        stair(d, 15, 25, Y0, 7, "east", [(15, 7, 25), (16, 7, 24), (17, 7, 24), (18, 7, 24)])
        # study loft
        shelf(d, [(x, 17) for x in (13, 15, 16, 18, 19, 21, 22, 24, 25, 27, 28, 29)], 7, 3)
        shelf(d, [(x, 17) for x in (14, 17, 20, 23, 26)], 7, 1)
        for x in range(19, 24):
            d.set(x, 7, 21, "spruce_planks")
        seat(d, [(x, 20) for x in range(19, 24)], 7, "north", S)
        seat(d, [(x, 22) for x in range(19, 24)], 7, "south", S)
        place(d, [(20, 8, 21, cand(3)), (22, 8, 21, LS)])
        d.hearth(13, 7, 22, "east", 11, "cobblestone", "campfire")
        seat(d, [(15, 21), (15, 23)], 7, "east", S)
        for z in (20, 22):
            d.set(29, 7, z, slab("spruce_slab", "top"))
            d.chair(28, 7, z, "west", S)
        place(d, [(29, 8, 20, cand(1)), (29, 7, 25, "potted_fern"), (14, 7, 21, "brown_carpet"), (14, 7, 23, "brown_carpet")])
        hang(d, [(18, 21), (26, 21), (22, 24)], 10)

    # ---------------------------------------------------------------- woodshop (L2+)
    if L >= 2:
        link(d, 30, Y0, 21, "east")
        d.sign(34, 4, 16, "north", ["WOOD", "SHOP"], S)
        place(d, [(37, 2, 18, "crafting_table"), (37, 2, 20, "stonecutter[facing=west]"),
                  (37, 2, 21, slab("spruce_slab", "top")), (37, 2, 23, "grindstone[face=floor,facing=west]"),
                  (37, 2, 24, "barrel[facing=up,open=false]"),
                  (32, 2, 18, "fletching_table"), (33, 2, 18, slab("spruce_slab", "top")),
                  (34, 2, 18, slab("spruce_slab", "top")), (33, 3, 18, "flower_pot")])
        for x in (33, 34, 36):
            d.set(x, 4, 18, td(S, "south", "bottom", True))
        tops(d, [(33, 21), (34, 21), (35, 21)], Y0, "spruce_slab")
        place(d, [(33, 3, 21, cand(1)), (35, 3, 21, log("stripped_spruce_log", "x"))])
        seat(d, [(33, 22), (35, 22)], Y0, "south", S)
        d.chair(34, Y0, 20, "north", S)
        place(d, [(32, 2, 24, log("spruce_log", "x")), (33, 2, 24, log("spruce_log", "x")),
                  (34, 2, 24, log("spruce_log", "x")), (32, 3, 24, log("spruce_log", "x")),
                  (33, 3, 24, log("spruce_log", "x"))])
        hang(d, [(34, 19), (34, 23)], 5)
        for z in (18, 20, 22, 24):                                      # log pile against the east wall
            d.set(39, 2, z, log("spruce_log", "z"))
            d.set(39, 3, z, log("spruce_log", "z"))

    # ---------------------------------------------------------------- library lodge (L2+)
    if L >= 2:
        entry(d, 7, 16, "south", step="cobblestone")
        d.sign(8, 4, 15, "north", ["LIBRARY", "LODGE"], S)
        d.hearth(11, Y0, 22, "west", 6, "cobblestone", "campfire")
        shelf(d, [(x, z) for z in (18, 20, 22, 24) for x in range(3, 7)], Y0, 2)
        seat(d, [(9, 21), (9, 23)], Y0, "west", S)
        place(d, [(9, 2, 22, td(S, "north")), (9, 3, 22, LS)])
        carpet(d, [(10, 21), (10, 22), (10, 23)], Y0, "brown")
        tops(d, [(9, 18), (10, 18)], Y0, "spruce_slab")
        d.set(10, 3, 18, cand(2))
        d.chair(10, Y0, 19, "south", S)
        place(d, [(11, 2, 25, "potted_fern"), (11, 2, 17, "potted_fern")])
        hang(d, [(7, 18), (7, 22)], 5)
        if L >= 3:
            stair(d, 4, 25, Y0, 7, "east", [(4, 7, 25), (5, 7, 24), (6, 7, 24), (7, 7, 24)])
            for x in range(5, 9):
                d.set(x, 7, 20, "spruce_planks")
            seat(d, [(x, 19) for x in range(5, 9)], 7, "north", S)
            seat(d, [(x, 21) for x in range(5, 9)], 7, "south", S)
            place(d, [(6, 8, 20, cand(2)), (8, 8, 20, "potted_fern")])
            shelf(d, [(3, 17), (3, 19), (3, 20), (3, 22), (3, 23)], 7, 2)
            shelf(d, [(3, 18), (3, 21)], 7, 1)
            d.set(11, 7, 20, slab("spruce_slab", "top"))
            d.set(11, 8, 20, LS)
            d.chair(10, 7, 20, "west", S)
            place(d, [(11, 7, 17, chest("west")), (11, 7, 25, "potted_fern")])
            carpet(d, [(x, 23) for x in range(5, 11)], 7, "green")
            hang(d, [(7, 18), (7, 22)], 10)

    # ---------------------------------------------------------------- bunkhouse (L4+)
    if L >= 4:
        entry(d, 43, 30, "south", step="spruce_planks")
        d.sign(43, 4, 29, "north", ["BUNKHOUSE"], S)
        stair(d, 49, 32, Y0, 7, "south", [(48, 7, 33), (48, 7, 34), (48, 7, 35), (49, 7, 32)])
        chimney(d, 36, 35, Y0, BK["ridge"] + 1)
        d.hearth(37, Y0, 35, "east", 6, "cobblestone", "campfire")
        place(d, [(44, 2, 31, "smoker[facing=south,lit=true]"), (45, 2, 31, slab("spruce_slab", "top")),
                  (46, 2, 31, "water_cauldron[level=3]"), (47, 2, 31, slab("spruce_slab", "top")),
                  (48, 2, 31, "furnace[facing=south,lit=false]"), (45, 3, 31, "flower_pot"),
                  (38, 2, 31, "barrel[facing=up,open=false]"), (39, 2, 31, "barrel[facing=up,open=false]"),
                  (38, 3, 31, "barrel[facing=up,open=false]")])
        for x in range(40, 47):                                         # mess table
            d.set(x, Y0, 36, "spruce_planks")
        seat(d, [(x, 35) for x in range(40, 47)], Y0, "north", S)
        seat(d, [(x, 37) for x in range(40, 47)], Y0, "south", S)
        place(d, [(41, 3, 36, cand(3)), (43, 3, 36, LS), (45, 3, 36, cand(2))])
        hang(d, [(40, 33), (46, 33), (43, 39)], 5)
        for x in (38, 40, 42, 44):                                      # dormitory upstairs
            d.bed(x, 7, 31, "north", "brown")
            d.bed(x, 7, 39, "south", "green")
        for x in (39, 41, 43):
            for z in (31, 39):
                d.set(x, 7, z, slab("spruce_slab", "top"))
                d.set(x, 8, z, cand(1))
        place(d, [(46, 7, 31, chest("south", "right")), (47, 7, 31, chest("south", "left")),
                  (46, 7, 39, chest("north", "left")), (47, 7, 39, chest("north", "right"))])
        carpet(d, [(x, 35) for x in range(38, 47)], 7, "brown")
        hang(d, [(38, 35), (42, 35), (46, 35)], 10)
        # porch along the street side
        d.fill(36, 1, 27, 50, 1, 29, "spruce_planks")
        for x in (36, 40, 44, 48):
            for y in (2, 3, 4):
                d.set(x, y, 27, log("spruce_log"))
        d.fill(36, 5, 27, 50, 5, 29, slab("spruce_slab"))
        for x in (37, 38, 39, 41, 42, 45, 46, 47, 49, 50):
            d.set(x, 2, 27, "spruce_fence")
        seat(d, [(38, 29), (39, 29), (46, 29), (47, 29)], Y0, "south", S, sit=False)
        hang(d, [(41, 28), (46, 28)], 4)
        for x in range(36, 51):                                         # porch eave
            d.set(x, 5, 26, st("spruce_stairs", "north"))
        for x, z in ((30, 40), (34, 40), (30, 43), (34, 43)):          # woodshed behind the hall
            for y in (2, 3, 4):
                d.set(x, y, z, log("spruce_log"))
        for x in range(29, 36):
            for z in range(40, 44):
                d.set(x, 5, z, slab("spruce_slab"))
        for x in range(31, 34):
            for z in (41, 42, 43):
                for y in (2, 3):
                    d.set(x, y, z, log("spruce_log", "z"))
        d.set(32, 4, 42, log("spruce_log", "z"))
        for z in (31, 32, 33, 34, 36, 37, 38, 39):                     # firewood rack along the bunkhouse
            d.set(35, 2, z, log("spruce_log", "x"))
            d.set(35, 3, z, log("spruce_log", "x"))
        for z in range(31, 40):
            d.set(35, 4, z, slab("spruce_slab"))
        place(d, [(47, 2, 25, "water_cauldron[level=3]"), (48, 2, 25, "water_cauldron[level=3]"),
                  (49, 2, 28, "barrel[facing=up,open=false]"), (50, 2, 28, "barrel[facing=up,open=false]"),
                  (50, 3, 28, "barrel[facing=up,open=false]")])
        for z in range(27, 41):                                         # split-rail fence on the east line
            if z not in (30, 38):
                d.set(52, 2, z, "spruce_fence")
        lamppost(d, 34, 33, "cs")
        lamppost(d, 52, 30, "cs")
        lamppost(d, 52, 38, "cs")

    # ---------------------------------------------------------------- sawmill class, greenhouse, ag barn (L5)
    if L >= 5:
        entry(d, 43, 42, "south", double=True, step="spruce_planks")
        d.sign(43, 4, 41, "north", ["SAWMILL", "CLASS"], S)
        stair(d, 49, 44, Y0, 7, "south", [(48, 7, 45), (48, 7, 46), (48, 7, 47), (49, 7, 44)])
        place(d, [(39, 2, 46, slab("spruce_slab", "top")), (40, 2, 46, "stonecutter[facing=south]"),
                  (41, 2, 46, slab("spruce_slab", "top")), (42, 2, 46, slab("spruce_slab", "top")),
                  (41, 3, 46, log("stripped_spruce_log", "x")), (42, 3, 46, log("stripped_spruce_log", "x")),
                  (38, 2, 43, "crafting_table"), (39, 2, 43, slab("spruce_slab", "top")), (40, 2, 43, "fletching_table"),
                  (46, 2, 43, "grindstone[face=floor,facing=south]"), (47, 2, 43, "barrel[facing=up,open=false]")])
        seat(d, [(39, 45), (42, 45)], Y0, "north", S)
        for x in range(37, 47):
            d.set(x, 2, 49, log("spruce_log", "x"))
        for x in (37, 39, 40, 42, 43):
            d.set(x, 3, 49, log("spruce_log", "x"))
        hang(d, [(40, 45), (46, 46), (43, 48)], 5)
        for x in range(40, 45):                                         # study room upstairs
            d.set(x, 7, 46, "spruce_planks")
        seat(d, [(x, 45) for x in range(40, 45)], 7, "north", S)
        seat(d, [(x, 47) for x in range(40, 45)], 7, "south", S)
        place(d, [(41, 8, 46, cand(2)), (43, 8, 46, LS), (37, 7, 49, "potted_fern")])
        shelf(d, [(x, 43) for x in (37, 39, 40, 42, 43, 45, 46)], 7, 2)
        hang(d, [(38, 46), (42, 46), (46, 46)], 10)
        lamppost(d, 35, 44, "cs")
        lamppost(d, 51, 44, "cs")
        # greenhouse
        gh = (4, 32, 16, 42)
        for x in range(gh[0], gh[2] + 1):
            for z in range(gh[1], gh[3] + 1):
                if x in (gh[0], gh[2]) or z in (gh[1], gh[3]):
                    for y in range(Y0, 5):
                        d.set(x, y, z, "glass" if (x + z) % 3 else log("spruce_log"))
                else:
                    d.set(x, 1, z, "spruce_planks")
                d.set(x, 5, z, "glass")
        rows = {34: "carrots[age=7]", 35: "potatoes[age=7]", 37: "beetroots[age=3]", 38: "wheat[age=7]"}
        for z, crop in rows.items():
            for x in list(range(5, 10)) + list(range(11, 16)):
                d.set(x, 1, z, "farmland[moisture=7]")
                d.set(x, 2, z, crop)
        for x in list(range(5, 10)) + list(range(11, 16)):
            d.set(x, 1, 40, "grass_block[snowy=false]")
            d.set(x, 2, 40, "sweet_berry_bush[age=2]" if x % 2 else "fern")
        place(d, [(10, 1, 36, "water"), (15, 2, 33, "water_cauldron[level=3]"), (5, 2, 33, "composter[level=4]"),
                  (5, 2, 41, "potted_blue_orchid"), (15, 2, 41, "barrel[facing=up,open=false]")])
        d.set(10, 2, 32, AIR)
        d.set(10, 3, 32, AIR)
        d.door(10, 2, 32, "south", S)
        # ag barn
        entry(d, 26, 32, "south", double=True, step="spruce_planks")
        d.sign(26, 5, 31, "north", ["AG BARN"], S)
        place(d, [(21, 2, 34, "hay_block[axis=y]"), (21, 3, 34, "hay_block[axis=y]"), (21, 2, 35, "hay_block[axis=y]"),
                  (21, 2, 40, "hay_block[axis=y]"), (31, 2, 34, "hay_block[axis=y]"), (31, 2, 37, "hay_block[axis=y]"),
                  (31, 2, 43, "composter[level=6]"), (22, 2, 43, "barrel[facing=up,open=false]"),
                  (23, 2, 43, "barrel[facing=up,open=false]"),
                  (26, 2, 37, "spruce_fence"), (26, 2, 38, slab("spruce_slab", "top")),
                  (26, 2, 39, slab("spruce_slab", "top")), (26, 3, 39, "hay_block[axis=y]"),
                  (25, 2, 39, td(S, "west", "bottom", True)), (27, 2, 39, td(S, "east", "bottom", True)),
                  (28, 2, 43, "cauldron"), (29, 2, 43, "cauldron")])
        hang(d, [(24, 34), (28, 42), (26, 38)], 7)
    return d


@design("communitycollege")
def communitycollege_v3(pack, rel, L):
    return common_materials({"Hearthwood": col_hearthwood, "Cascadia": col_cascadia, "Neoterra": col_neoterra}[pack](rel, L))
