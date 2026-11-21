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

from designs import _civic_common as _cc
_g = {k: v for k, v in vars(_cc).items() if not k.startswith('__') and k not in globals()}
globals().update(_g)


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
