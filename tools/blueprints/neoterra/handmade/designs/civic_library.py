"""Civic: library (hand-designed, all packs).

Round 4: no automatic placement. The building shells come from a local copy of the civic shell (walls, floors,
window openings, roofs only – no window dressing, no light grids, no tie-beam lanterns). Every piece of furniture,
light, rail, planter, tree and lamp below is placed at a hand-chosen coordinate, room by room, level by level.
"""
from designs._civic_common import (Y0, st, slab, log, framing, flight, new, link, chimney, plant_tree, aframe,
                                   park_bench, post_lamp, lamppost, common_materials, wallblock, OUT)
from hm import design, AIR, D4  # noqa: F401

GRASS = "grass_block[snowy=false]"
LEAF = "oak_leaves[distance=1,persistent=true,waterlogged=false]"


# --------------------------------------------------------------------------------------------- local helpers
def shell(d, x1, z1, x2, z2, nf=1, roof="gable", axis="x", win="nesw", ws=3, mat=None, up=None, wh=4,
          glassy=False, parapet=True, beams=True):
    """Structure only: plinth, storey walls + floor slabs, corner posts, window openings, roof (and structural tie
    beams under gable roofs). No decoration or lights – those are placed by hand per room."""
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
                d.set(x, Y0, z, S["base"] if not (d.pack == "Cascadia" and (x * 7 + z) % 5 == 0) else "mossy_cobblestone")
    if d.pack == "Hearthwood":
        for f, y in enumerate(ys):
            m = mat if f == 0 else up
            if m in ("calcite", "yellow_terracotta", "white_terracotta"):
                framing(d, x1, z1, x2, z2, y, y + wh - 1, S["post"], every=3)
    for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        for y in range(Y0, top + 1):
            if d.pack == "Hearthwood":
                if mat == up or y < ys[0] + wh:
                    d.set(x, y, z, ("cut_sandstone" if y % 2 else "chiseled_sandstone") if mat == "smooth_sandstone"
                          else ("smooth_stone" if y % 2 else "stone_bricks"))
                else:
                    d.set(x, y, z, log(S["post"]))
            elif d.pack == "Cascadia":
                d.set(x, y, z, log(S["post"]))
            else:
                d.set(x, y, z, "light_gray_concrete")
    sides = {"n": (z1, "x"), "s": (z2, "x"), "w": (x1, "z"), "e": (x2, "z")}
    for f, y in enumerate(ys):                                         # window openings
        for sd in win:
            line, along = sides[sd]
            a1, a2 = (x1, x2) if along == "x" else (z1, z2)
            if a2 - a1 - 3 < 1:
                continue
            for a in range(a1 + 2, a2 - 1):
                if glassy:
                    if (a - a1) % 4 == 0:
                        continue
                elif (a - a1 - 2) % ws != 0:
                    continue
                x, z = (a, line) if along == "x" else (line, a)
                h2 = wh - 1 if glassy or d.pack == "Neoterra" else 2
                for yy in range(y + 1, y + 1 + h2):
                    d.set(x, yy, z, S["glass"] if d.pack != "Neoterra" or f == 0 else
                          "light_gray_stained_glass_pane" if glassy else S["glass"])
    ridge = top
    if roof == "gable":
        ridge = d.gable(x1, z1, x2, z2, top + 1, axis, f"{S['roof']}_stairs", f"{S['roof']}_slab",
                        up if d.pack != "Cascadia" else "spruce_planks", overhang=1)
        ends = ((x1, (z1 + z2) // 2), (x2, (z1 + z2) // 2)) if axis == "x" else (((x1 + x2) // 2, z1), ((x1 + x2) // 2, z2))
        for ex, ez in ends:
            for yy in range(top + 1, ridge):
                if d.pack == "Hearthwood" and "stairs" not in d.get(ex, yy, ez):
                    d.set(ex, yy, ez, log(S["post"]))
            if ridge - top >= 4:
                d.set(ex, top + 2, ez, S["glass"])
        if beams:                                                     # structural tie beams (no lights)
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
                        d.set(x, top + 2, z, "white_concrete" if d.pack == "Neoterra" else S["base"])
                        d.set(x, top + 3, z, slab("smooth_quartz_slab"))
        edge = slab("smooth_quartz_slab", "top")
        for x in range(x1 - 1, x2 + 2):                                # cantilevered roof edge
            for z in (z1 - 1, z2 + 1):
                if d.bp.inside(x, top + 1, z) and d.air(x, top + 1, z):
                    d.set(x, top + 1, z, edge)
        for z in range(z1, z2 + 1):
            for x in (x1 - 1, x2 + 1):
                if d.bp.inside(x, top + 1, z) and d.air(x, top + 1, z):
                    d.set(x, top + 1, z, edge)
        ridge = top + 1
    return dict(ys=ys, top=top, ridge=ridge, x1=x1, z1=z1, x2=x2, z2=z2)


def door_out(d, x, y, z, facing, double=False, wood=None, stoop=None):
    """Exterior door (facing = into the room), the cells in front and behind cleared, one stoop block outside."""
    wood = wood or d.S["wood"]
    if double:
        d.double_door(x, y, z, "x", facing, wood)
    else:
        d.door(x, y, z, facing, wood)
    ox, oz = D4[facing]
    for cx in ([x, x + 1] if double else [x]):
        for s in (1, -1):
            d.clear(cx + ox * s, y, z + oz * s, cx + ox * s, y + 2, z + oz * s)
        d.set(cx - ox, 1, z - oz, stoop or (d.S["base"] if d.pack != "Cascadia" else "spruce_planks"))


def stair(d, x, z, y0, yU, rise, rails, fence=None):
    """One flight (first step at x,z) plus the railing cells I list for that opening."""
    block = f"{d.S['wood']}_stairs" if d.pack != "Neoterra" else "smooth_quartz_stairs"
    flight(d, x, z, y0, yU, rise, block, under=d.S["floor"] if d.pack != "Neoterra" else "smooth_quartz")
    fence = fence or (f"{d.S['wood']}_fence" if d.pack != "Neoterra" else "glass_pane")
    for (rx, rz) in rails:
        d.set(rx, yU, rz, fence)


def press(d, x1, x2, z, y, h):
    """A bookcase run along x (x1..x2) at row z, h high."""
    for x in range(x1, x2 + 1):
        d.bookshelf(x, y, z, h)


def pressz(d, x, z1, z2, y, h):
    for z in range(z1, z2 + 1):
        d.bookshelf(x, y, z, h)


def cases(d, cells, y, h):
    for (x, z) in cells:
        d.bookshelf(x, y, z, h)


def seats(d, lst, y, wood, sit=True):
    for (x, z, back) in lst:
        d.chair(x, y, z, back, wood, sit=sit)


def tops(d, cells, y, blk):
    for (x, z) in cells:
        d.set(x, y, z, slab(blk, "top"))


def hang(d, cells, y):
    for (x, z) in cells:
        d.set(x, y, z, "lantern[hanging=true,waterlogged=false]")


def panel(d, cells, y, blk="sea_lantern"):
    for (x, z) in cells:
        d.set(x, y, z, blk)


def rails_at(d, cells, y, fence):
    for (x, z) in cells:
        d.set(x, y, z, fence)


def bed_of(d, cells):
    """Flower bed: each (x, z, flower) planted on grass."""
    for (x, z, fl) in cells:
        d.set(x, 1, z, GRASS)
        if fl:
            d.set(x, 2, z, fl)


def sill(d, x, y, z, facing, flower, trap="dark_oak_trapdoor"):
    """Window box under one window: trapdoor ledge on the wall + a potted flower on it."""
    d.set(x, y, z, f"{trap}[facing={facing},half=top,open=false,powered=false,waterlogged=false]")
    d.set(x, y + 1, z, "potted_" + flower)


# =============================================================================================== HEARTHWOOD
def lib_hearthwood(rel, L):
    """Oxford-ish college library: sandstone hall with columned porch, stall-system bookcases; later a stacks
    wing, a domed rotunda (Radcliffe-style), a scriptorium wing, cloister garden and the librarian's cottage."""
    d = new("Hearthwood", rel, (49, 34, 55))
    SS = "smooth_sandstone"
    W = "dark_oak"
    hnf = 2 if L >= 3 else 1
    hh = 3 if L >= 3 else 2                                           # press height grows with the level
    h = shell(d, 16, 8, 30, 20, hnf, "gable", "x", win="nsew", ws=2)
    door_out(d, 23, Y0, 8, "south")
    d.sign(23, 5, 7, "north", ["LIBRARY", "", "Sapere aude"], W)
    for x in (21, 25):                                                # columned porch
        for y in range(Y0, 6):
            d.set(x, y, 5, "quartz_pillar[axis=y]")
    d.fill(21, 6, 5, 25, 6, 7, "cut_sandstone")
    for x in range(21, 26):
        d.set(x, 7, 5, st("sandstone_stairs", "south"))
    d.fill(21, 1, 4, 25, 1, 7, "cut_sandstone")
    hang(d, [(23, 6)], 5)                                             # porch lantern over the door
    # --- street front: lamp posts, low hedges and two flower beds
    post_lamp(d, 14, 5)
    post_lamp(d, 32, 5)
    for x in list(range(16, 21)) + list(range(26, 31)):
        d.set(x, 2, 2, LEAF)
    bed_of(d, [(16, 3, "red_tulip"), (17, 3, "oxeye_daisy"), (18, 3, "red_tulip"), (19, 3, "oxeye_daisy"),
               (20, 3, "red_tulip"), (16, 4, "cornflower"), (17, 4, None), (18, 4, "allium"), (19, 4, None),
               (20, 4, "cornflower"),
               (26, 3, "red_tulip"), (27, 3, "oxeye_daisy"), (28, 3, "red_tulip"), (29, 3, "oxeye_daisy"),
               (30, 3, "red_tulip"), (26, 4, "cornflower"), (27, 4, None), (28, 4, "allium"), (29, 4, None),
               (30, 4, "cornflower")])

    # --- reading hall, ground floor (x17-29, z9-19)
    d.hut(17, Y0, 9)
    tops(d, [(26, 11), (27, 11), (28, 11)], Y0, f"{W}_slab")         # librarian's issue desk by the door
    d.chair(27, Y0, 10, "north", W)
    d.item(28, Y0, 10, "lectern", "west")
    d.candle(26, Y0 + 1, 11, 2)
    d.set(29, Y0, 10, "chiseled_bookshelf[facing=west,slot_0_occupied=true,slot_1_occupied=true,slot_2_occupied=false,"
                      "slot_3_occupied=true,slot_4_occupied=true,slot_5_occupied=false]")
    press(d, 17, 19, 11, Y0, hh)                                      # west stall presses with window desks
    press(d, 17, 19, 15, Y0, hh)
    tops(d, [(17, 12), (17, 13), (17, 16), (17, 17)], Y0, f"{W}_slab")
    seats(d, [(18, 12, "east"), (18, 13, "east"), (18, 16, "east"), (18, 17, "east")], Y0, W)
    d.candle(17, Y0 + 1, 12, 1)
    d.candle(17, Y0 + 1, 16, 1)
    for x0 in (20, 24):                                               # twin reading tables either side of the aisle
        for x in range(x0, x0 + 3):
            d.table(x, Y0, 14, W, "block", "dark_oak_planks")
            d.chair(x, Y0, 13, "north", W)
            d.chair(x, Y0, 15, "south", W)
    d.candle(21, Y0 + 1, 14, 3)
    d.candle(25, Y0 + 1, 14, 3)
    press(d, 26, 28, 17, Y0, hh)                                      # east press
    for z in range(9, 20):                                            # red runner from the door
        if L >= 4 or z < 19:
            d.set(23, Y0, z, "red_carpet")
    if L >= 4:
        cases(d, [(20, 19), (21, 19), (25, 19), (26, 19)], Y0, 3)    # bookcases flank the rotunda arch
    else:
        cases(d, [(21, 19), (22, 19), (24, 19), (25, 19)], Y0, hh)    # south wall bookcase, globe stand between
        d.set(23, Y0, 19, "dark_oak_fence[east=false,north=false,south=false,waterlogged=false,west=false]")
        d.set(23, Y0 + 1, 19, "light_blue_stained_glass")
    if L < 3:                                                         # fireside-less reading nook (books!)
        seats(d, [(29, 15, "east"), (29, 17, "east")], Y0, W)
        d.table(29, Y0, 16, W)
        hang(d, [(18, 13), (22, 14), (26, 14)], 5)                    # hung from the tie beams
    else:
        stair(d, 29, 14, Y0, 7, "south", [(28, 15), (28, 16), (28, 17), (29, 14)])
        hang(d, [(18, 13), (22, 14), (26, 14), (23, 10)], 5)
        # --- upper reading gallery (y7)
        y = 7
        cases(d, [(17, 9), (17, 11), (17, 13), (17, 15), (17, 17), (17, 19),
                  (19, 9), (21, 9), (23, 9), (25, 9), (27, 9), (29, 9),
                  (29, 11), (29, 13), (18, 19), (19, 19), (21, 19), (23, 19), (25, 19)], y, 3)
        tops(d, [(17, 12), (17, 16)], y, f"{W}_slab")                  # window desks between the cases
        seats(d, [(18, 12, "east"), (18, 16, "east")], y, W)
        for x in range(21, 26):                                       # long reading table
            d.table(x, y, 14, W, "block", "dark_oak_planks")
            d.chair(x, y, 13, "north", W)
            d.chair(x, y, 15, "south", W)
        seats(d, [(20, 14, "west"), (26, 14, "east")], y, W)
        d.candle(22, y + 1, 14, 3)
        d.candle(24, y + 1, 14, 2)
        hang(d, [(22, 14), (26, 17), (18, 11)], 10)
        for x, fl in ((18, "red_tulip"), (20, "cornflower"), (22, "allium"), (24, "allium"), (26, "oxeye_daisy"),
                      (28, "red_tulip")):
            sill(d, x, 7, 7, "north", fl)                             # window boxes on the upper front windows
        for z, fl in ((10, "red_tulip"), (12, "cornflower"), (14, "oxeye_daisy"), (16, "cornflower"), (18, "red_tulip")):
            sill(d, 15, 7, z, "west", fl)                             # ... and on the west (side street) windows
        for x, fl in ((18, "allium"), (20, "red_tulip"), (24, "oxeye_daisy"), (26, "red_tulip"), (28, "allium")):
            sill(d, x, 7, 21, "south", fl)
        seats(d, [(28, 10, "east"), (28, 12, "east")], y, W)            # armchair corner in the gallery
        d.table(28, y, 11, W)
        d.bookshelf(27, y, 19, 3)
        for x in (18, 19, 27, 28):                                    # benches under the porch-side windows
            d.chair(x, Y0, 6, "south", W, sit=False)

    if L >= 2:
        # --- stacks wing (x31-41, z10-18)
        swnf = 2 if L >= 4 else 1
        shell(d, 30, 9, 42, 19, swnf, "gable", "z", win="nse")
        link(d, 30, Y0, 12, "east")
        press(d, 32, 40, 13, Y0, hh)
        press(d, 32, 40, 16, Y0, hh)
        if L >= 3:
            tops(d, [(32, 10), (35, 10), (38, 10)], Y0, f"{W}_slab")  # desks under the north windows
            seats(d, [(32, 11, "south"), (35, 11, "south"), (38, 11, "south")], Y0, W)
            d.candle(35, Y0 + 1, 10, 1)
        hang(d, [(34, 11), (38, 11), (36, 15)], 5)
        d.sign(36, 5, 8, "north", ["STACKS"], W)
        if swnf > 1:
            stair(d, 41, 11, Y0, 7, "south", [(40, 12), (40, 13), (40, 14), (41, 11)])
            link(d, 30, 7, 12, "east")
            y = 7                                                     # map & rare-book room
            cases(d, [(33, 10), (34, 10), (36, 10), (37, 10), (39, 10), (40, 10)], y, 3)
            tops(d, [(32, 10), (35, 10), (38, 10)], y, f"{W}_slab")
            seats(d, [(32, 11, "south"), (35, 11, "south"), (38, 11, "south")], y, W)
            for (x, z) in ((35, 14), (36, 14), (35, 15), (36, 15)):
                d.set(x, y, z, "cartography_table")
            press(d, 32, 39, 18, y, 2)
            seats(d, [(31, 15, "west"), (31, 17, "west")], y, W)
            d.table(31, y, 16, W)
            hang(d, [(36, 15), (33, 11)], 10)
    if L >= 4:
        # --- the rotunda: domed round reading room behind the hall
        cx, cz, R = 23, 30, 7
        wins = {(30, 30), (16, 30), (28, 25), (18, 25), (28, 35), (18, 35), (29, 27), (17, 27), (29, 33),
                (17, 33), (26, 24), (20, 24), (26, 36), (20, 36)}
        for y in range(Y0, 11):                                       # round wall (structure) + window list
            for x in range(cx - R, cx + R + 1):
                for z in range(cz - R, cz + R + 1):
                    dd = (x - cx) ** 2 + (z - cz) ** 2
                    if (R - 0.5) ** 2 <= dd <= (R + 0.5) ** 2:
                        d.set(x, y, z, "glass_pane" if (x, z) in wins and 4 <= y <= 7 else SS)
                    elif dd < (R - 0.5) ** 2:
                        d.set(x, y, z, AIR)
                        if y == Y0:
                            d.set(x, 1, z, "polished_andesite" if (x + z) % 2 else "smooth_stone")
        for k in range(0, R + 1):                                     # stepped dome
            y = 11 + k
            r = R - k
            for x in range(cx - R, cx + R + 1):
                for z in range(cz - R, cz + R + 1):
                    dd = (x - cx) ** 2 + (z - cz) ** 2
                    if (r - 0.6) ** 2 <= dd <= (r + 0.6) ** 2 or (r <= 0 and dd == 0):
                        d.set(x, y, z, "mud_bricks" if k < R - 1 else "cut_sandstone")
        d.set(cx, 11 + R + 1, cz, "lantern[hanging=false,waterlogged=false]")
        d.clear(cx - 1, Y0, cz + R, cx + 1, 4, cz + R)                # garden door (south) and hall arch (north)
        d.clear(cx - 1, Y0, cz - R, cx + 1, 4, cz - R)
        d.clear(cx - 1, Y0, h["z2"], cx + 1, 4, h["z2"])
        for z in range(h["z2"], cz - R + 1):                          # covered passage
            for x in range(cx - 1, cx + 2):
                d.set(x, 1, z, "polished_andesite")
        for z in range(h["z2"] + 1, cz - R):
            for x in (cx - 2, cx + 2):
                for y in range(Y0, 6):
                    d.set(x, y, z, SS)
            for x in range(cx - 2, cx + 3):
                d.set(x, 6, z, "cut_sandstone")
        hang(d, [(23, 21)], 5)
        # radial presses in six alcoves (N and S kept for the doors)
        cases(d, [(27, 30), (28, 30), (29, 30), (17, 30), (18, 30), (19, 30),
                  (26, 27), (27, 26), (27, 27), (20, 27), (19, 26), (19, 27),
                  (26, 33), (27, 34), (27, 33), (20, 33), (19, 34), (19, 33)], Y0, 3)
        d.item(cx, Y0, cz, "enchanting_table")
        tops(d, [(21, 28), (25, 28), (21, 32), (25, 32)], Y0, f"{W}_slab")   # four study desks round the table
        seats(d, [(20, 28, "west"), (26, 28, "east"), (20, 32, "west"), (26, 32, "east")], Y0, W)
        for (x, z) in ((21, 28), (25, 32)):
            d.candle(x, Y0 + 1, z, 2)
        for y in range(9, 18):                                        # chandelier from the dome
            d.set(cx, y, cz, "chain[axis=y,waterlogged=false]")
        d.set(cx, 8, cz, "lantern[hanging=true,waterlogged=false]")
        for (x, z) in ((29, 30), (17, 30)):
            d.set(x, 5, z, "lantern[hanging=false,waterlogged=false]")
    if L >= 5:
        # --- scriptorium wing (x5-15, z10-20), two storeys
        shell(d, 4, 9, 16, 21, 2, "gable", "z", win="nsw", mat=SS, up="calcite")
        link(d, 16, Y0, 14, "west")
        stair(d, 15, 19, Y0, 7, "north", [(14, 16), (14, 17), (14, 18), (15, 19)])
        tops(d, [(5, 11), (5, 14), (5, 17)], Y0, f"{W}_slab")         # copy desks under the west windows
        seats(d, [(6, 11, "east"), (6, 14, "east"), (6, 17, "east")], Y0, W)
        for x in (8, 10, 12):                                          # two rows of scribes' desks facing north
            tops(d, [(x, 12), (x, 17)], Y0, f"{W}_slab")
            seats(d, [(x, 13, "south"), (x, 18, "south")], Y0, W)
        d.candle(8, Y0 + 1, 12, 1)
        d.candle(12, Y0 + 1, 17, 1)
        d.candle(5, Y0 + 1, 14, 2)
        cases(d, [(7, 10), (8, 10), (10, 10), (11, 10), (13, 10), (14, 10)], Y0, 3)
        d.set(6, Y0, 20, "barrel[facing=up,open=false]")                 # ink & parchment store
        d.set(7, Y0, 20, "barrel[facing=up,open=false]")
        d.set(8, Y0, 20, "cartography_table")
        door_out(d, 10, Y0, 21, "north", stoop="gravel")                # garden door
        hang(d, [(10, 15), (7, 19)], 5)
        y = 7                                                          # manuscript gallery
        cases(d, [(5, 10), (5, 12), (5, 13), (5, 15), (5, 16), (5, 18), (5, 19), (5, 20),
                  (7, 10), (8, 10), (10, 10), (11, 10), (13, 10), (14, 10)], y, 3)
        for x in (8, 10, 12):                                          # glass display cases
            d.set(x, y, 14, "dark_oak_planks")
            d.set(x, y + 1, 14, "glass")
        tops(d, [(10, 18)], y, f"{W}_slab")                            # archivist's desk
        d.chair(10, y, 19, "south", W)
        d.candle(10, y + 1, 18, 3)
        hang(d, [(10, 11), (10, 15), (10, 19)], 10)
        # --- cloister garden west of the rotunda
        d.fill(3, 1, 24, 14, 1, 43, GRASS)
        for x in range(2, 15):
            d.set(x, 2, 44, "sandstone_wall")
        for z in range(24, 45):
            d.set(2, 2, z, "sandstone_wall")
        d.fill(10, 1, 22, 10, 1, 43, "gravel")
        bed_of(d, [(4, 26, "red_tulip"), (5, 26, "oxeye_daisy"), (6, 26, "red_tulip"), (4, 27, "allium"),
                   (5, 27, "pink_tulip"), (6, 27, "allium"),
                   (12, 26, "cornflower"), (13, 26, "oxeye_daisy"), (12, 27, "lily_of_the_valley"),
                   (13, 27, "cornflower"),
                   (4, 36, "pink_tulip"), (5, 36, "oxeye_daisy"), (6, 36, "pink_tulip"), (4, 37, "cornflower"),
                   (5, 37, "red_tulip"), (6, 37, "cornflower"),
                   (12, 36, "allium"), (13, 36, "red_tulip"), (12, 37, "oxeye_daisy"), (13, 37, "allium")])
        d.set(7, 2, 32, "stone_brick_wall")                             # bird bath beside the path
        d.set(7, 3, 32, "water_cauldron[level=3]")
        seats(d, [(9, 30, "west"), (9, 31, "west")], Y0, W, sit=False)  # bench facing the bird bath
        plant_tree(d, 5, 40)
        plant_tree(d, 13, 31)
        lamppost(d, 11, Y0, 24, "dark_oak_fence")
        lamppost(d, 11, Y0, 42, "dark_oak_fence")
        # --- librarian's cottage (x35-43, z35-43)
        lc = shell(d, 34, 34, 44, 44, 2, "gable", "x", mat="calcite", up="calcite")
        door_out(d, 39, Y0, 34, "south", stoop="gravel")
        stair(d, 35, 37, Y0, 7, "south", [(36, 38), (36, 39), (36, 40), (35, 37)])
        d.hearth(43, Y0, 38, "west", 6, "bricks", "campfire")          # parlour fireplace
        chimney(d, 44, 38, Y0, lc["ridge"] + 1)
        seats(d, [(41, 37, "west"), (41, 39, "west")], Y0, W)
        d.table(41, Y0, 38, W)
        d.rug(38, 37, 40, 39, Y0, ("red_carpet", "orange_carpet"))
        cases(d, [(37, 35), (41, 35), (42, 35)], Y0, 2)
        for x, b in ((37, "barrel[facing=up,open=false]"), (38, slab(f"{W}_slab", "top")), (39, "water_cauldron[level=3]"),
                     (40, slab(f"{W}_slab", "top")), (41, "smoker[facing=north,lit=false]"),
                     (42, slab(f"{W}_slab", "top")), (43, "barrel[facing=up,open=false]")):
            d.set(x, Y0, 43, b)                                         # kitchen along the back wall
        d.table(39, Y0, 41, W)
        d.table(40, Y0, 41, W)
        seats(d, [(38, 41, "west"), (41, 41, "east"), (39, 40, "north"), (40, 40, "north")], Y0, W)
        hang(d, [(39, 38), (39, 41)], 5)
        y = 7                                                           # bedrooms upstairs
        d.bed(43, y, 36, "east", "red")
        d.bed(43, y, 41, "east", "blue")
        for z in (37, 40):
            d.set(43, y, z, "barrel[facing=up,open=false]")
            d.candle(43, y + 1, z, 1)
        d.set(41, y, 36, "chest[facing=west,type=single,waterlogged=false]")
        tops(d, [(38, 35)], y, f"{W}_slab")
        d.chair(38, y, 36, "south", W)
        cases(d, [(36, 35), (37, 35)], y, 1)
        d.set(37, y + 1, 35, "potted_red_tulip")
        d.rug(38, 38, 40, 40, y, ("orange_carpet", "red_carpet"))
        hang(d, [(40, 39)], 10)
        for x in range(34, 45):                                         # front garden fence with a gate
            d.set(x, 2, 30, "dark_oak_fence_gate[facing=north,in_wall=false,open=false,powered=false]" if x == 39
                  else "dark_oak_fence")
        d.fill(39, 1, 31, 39, 1, 33, "gravel")
        bed_of(d, [(35, 31, "red_tulip"), (36, 31, "oxeye_daisy"), (37, 31, "red_tulip"), (38, 31, "pink_tulip"),
                   (35, 32, "cornflower"), (36, 32, None), (37, 32, "allium"), (38, 32, "cornflower"),
                   (40, 31, "pink_tulip"), (41, 31, "red_tulip"), (42, 31, "oxeye_daisy"), (43, 31, "red_tulip"),
                   (40, 32, "cornflower"), (41, 32, "allium"), (42, 32, None), (43, 32, "cornflower")])
    return d


# =============================================================================================== NEOTERRA
def lib_neoterra(rel, L):
    """Modern public library: glass pavilion with reception and book walls, a terracotta stacks block, later a
    five-storey media tower, a lecture auditorium, a café kiosk and a public park."""
    d = new("Neoterra", rel, (51, 45, 51), paving="smooth_stone")
    Q = "smooth_quartz"
    B, M = "birch", "mangrove"
    nf = 2 if L >= 3 else 1
    shell(d, 16, 8, 30, 18, nf, "flat", glassy=True, win="nsew")
    door_out(d, 22, Y0, 8, "south", double=True)
    d.sign(22, 6, 7, "north", ["PUBLIC", "LIBRARY"], B, glow=True, color="orange")
    d.sign(23, 6, 7, "north", ["", "open late"], B, glow=True, color="orange")
    for x in range(19, 28):                                           # entrance canopy
        for z in range(4, 8):
            if d.air(x, 6, z):
                d.set(x, 6, z, slab("smooth_quartz_slab", "top"))
    for x in (13, 33):                                                # street lamps with azalea planters
        post_lamp(d, x, 5)
        d.set(x, 2, 3, "moss_block")
        d.set(x, 3, 3, "flowering_azalea")
    # --- ground floor (x17-29, z9-17)
    d.hut(17, Y0, 9)
    for x in range(25, 29):                                           # reception counter
        d.set(x, Y0, 11, Q)
    d.item(26, Y0, 10, "lectern", "south")
    d.chair(27, Y0, 10, "north", M)
    d.set(29, Y0, 9, "potted_bamboo")
    d.set(21, Y0, 9, "potted_bamboo")
    d.set(24, Y0, 9, "potted_bamboo")
    for x in range(19, 24):                                           # communal reading table
        d.table(x, Y0, 14, B, "block", Q)
        d.chair(x, Y0, 13, "north", M)
        d.chair(x, Y0, 15, "south", M)
    pressz(d, 17, 10, 16, Y0, 3)                                      # book wall behind the west glazing
    press(d, 17, 21, 17, Y0, 3)
    panel(d, [(21, 14), (26, 11), (19, 11)], 6)
    if L < 3:                                                         # lounge corner
        seats(d, [(25, 16, "south"), (26, 16, "south"), (27, 16, "south")], Y0, B)
        tops(d, [(26, 14)], Y0, "smooth_quartz_slab")
        d.set(28, Y0, 16, "potted_bamboo")
    else:
        stair(d, 28, 16, Y0, 7, "west", [(25, 15), (26, 15), (27, 15), (28, 16)])
        y = 7                                                         # upstairs study floor
        pressz(d, 17, 9, 17, y, 3)
        press(d, 19, 25, 10, y, 3)
        press(d, 19, 25, 12, y, 3)
        tops(d, [(18, 17), (20, 17), (22, 17)], y, "smooth_quartz_slab")   # carrels on the south glass
        seats(d, [(18, 16, "north"), (20, 16, "north"), (22, 16, "north")], y, M)
        seats(d, [(28, 10, "east"), (28, 11, "east"), (28, 12, "east")], y, B)   # lounge sofa
        tops(d, [(26, 11)], y, "smooth_quartz_slab")
        d.set(29, y, 9, "potted_bamboo")
        panel(d, [(22, 11), (22, 15), (27, 11)], 11)
        for (x, z) in ((18, 10), (19, 10), (18, 16), (19, 16), (27, 10), (28, 10)):   # green roof planters
            d.set(x, 12, z, "moss_block")
        for (x, z) in ((18, 10), (28, 10), (19, 16)):
            d.set(x, 13, z, "flowering_azalea")
    if L >= 2:
        # --- stacks block (x31-39, z9-17)
        shell(d, 30, 8, 40, 18, nf, "flat", glassy=False, win="ns", mat="orange_terracotta", up="orange_terracotta")
        link(d, 30, Y0, 13, "east")
        for z in (10, 12, 15, 17):
            press(d, 32, 38, z, Y0, 3)
        panel(d, [(34, 13), (37, 13)], 6)
        d.sign(35, 6, 7, "north", ["STACKS"], B, glow=True, color="orange")
        if nf > 1:
            link(d, 30, 7, 13, "east")
            y = 7
            press(d, 32, 38, 10, y, 3)
            press(d, 32, 38, 12, y, 3)
            for x in range(31, 40):                                   # glass partition of the group-study room
                if x != 35:
                    d.set(x, y, 14, "glass_pane")
                    d.set(x, y + 1, 14, "glass_pane")
            d.door(35, y, 14, "south", B)
            for x in range(33, 38):
                d.table(x, y, 16, B, "block", Q)
                d.chair(x, y, 15, "north", M)
                d.chair(x, y, 17, "south", M)
            panel(d, [(35, 11), (35, 16)], 11)
            for (x1, z1) in ((32, 10), (32, 15)):                     # two solar arrays on the roof
                d.fill(x1, 12, z1, x1 + 6, 12, z1 + 1, "daylight_detector[inverted=false,power=0]")
    if L >= 4:
        # --- media tower (x17-27, z19-31), five floors
        shell(d, 16, 18, 28, 32, 5, "flat", glassy=True, win="esw")
        link(d, 22, Y0, 18, "south")
        stair(d, 17, 20, Y0, 7, "south", [(18, 21), (18, 22), (18, 23), (17, 20)])
        stair(d, 27, 30, 7, 12, "north", [(26, 27), (26, 28), (26, 29), (27, 30)])
        stair(d, 17, 20, 12, 17, "south", [(18, 21), (18, 22), (18, 23), (17, 20)])
        stair(d, 27, 30, 17, 22, "north", [(26, 27), (26, 28), (26, 29), (27, 30)])
        # ground: enchanting alcove – shelves ring the table at two blocks, gaps north and south
        d.item(22, Y0, 25, "enchanting_table")
        cases(d, [(20, 23), (21, 23), (23, 23), (24, 23), (20, 27), (21, 27), (23, 27), (24, 27),
                  (20, 24), (20, 26), (24, 24), (24, 26)], Y0, 2)
        seats(d, [(21, 25, "west"), (23, 25, "east")], Y0, M)
        d.rug(19, 29, 25, 30, Y0, ("orange_carpet", "white_carpet"))
        panel(d, [(22, 25), (22, 20)], 6)
        d.sign(22, 6, 33, "south", ["MEDIA", "TOWER"], B, glow=True, color="orange")
        # floor 1: periodicals lounge
        y = 7
        press(d, 20, 24, 20, y, 2)
        seats(d, [(20, 28, "south"), (21, 28, "south"), (22, 28, "south")], y, B)
        tops(d, [(21, 26)], y, "smooth_quartz_slab")
        d.chair(24, y, 26, "east", B)
        d.set(19, y, 30, "potted_bamboo")
        panel(d, [(22, 24)], 11)
        # floor 2: music & media room
        y = 12
        d.set(20, y, 20, "jukebox[has_record=false]")
        d.set(24, y, 20, "jukebox[has_record=false]")
        d.set(22, y, 20, "note_block[instrument=harp,note=0,powered=false]")
        seats(d, [(20, 22, "south"), (24, 22, "south")], y, M)
        press(d, 19, 23, 28, y, 3)
        panel(d, [(22, 24)], 16)
        # floor 3: quiet study carrels
        y = 17
        tops(d, [(17, 27), (17, 29), (17, 31)], y, "smooth_quartz_slab")
        seats(d, [(18, 27, "east"), (18, 29, "east"), (18, 31, "east")], y, M)
        press(d, 20, 24, 21, y, 3)
        press(d, 20, 24, 23, y, 3)
        panel(d, [(22, 27)], 21)
        # floor 4: sky reading room facing the south glass
        y = 22
        seats(d, [(19, 30, "north"), (21, 30, "north"), (23, 30, "north")], y, B)
        tops(d, [(20, 30), (22, 30)], y, "smooth_quartz_slab")
        press(d, 18, 26, 19, y, 1)
        d.set(18, y, 30, "potted_bamboo")
        panel(d, [(22, 25)], 26)
        for (x, z) in ((19, 21), (20, 21), (25, 29), (25, 30)):        # roof planters
            d.set(x, 27, z, "moss_block")
        d.set(19, 28, 21, "flowering_azalea")
        d.set(25, 28, 30, "azalea")
    if L >= 5:
        # --- auditorium (x31-45, z21-31), lecture hall + study commons above
        shell(d, 30, 20, 46, 32, 2, "flat", wh=6, win="e")
        door_out(d, 38, Y0, 32, "north", double=True)
        stair(d, 45, 22, Y0, 9, "south", [(44, 25), (44, 26), (44, 27), (45, 24)])
        for x in range(33, 44):                                       # stage
            for z in (21, 22):
                d.set(x, Y0, z, slab("smooth_quartz_slab"))
        d.set(38, Y0 + 1, 22, "lectern[facing=south,has_book=false,powered=false]")
        d.fill(35, 4, 21, 41, 6, 21, "white_concrete")                # projection screen
        for z in (24, 26, 28, 30):                                    # seating rows, aisle x38-39
            for x in list(range(34, 38)) + list(range(40, 44)):
                d.chair(x, Y0, z, "south", B)
        panel(d, [(35, 24), (41, 24), (35, 29), (41, 29)], 8)
        y = 9
        for (tx, tz) in ((33, 23), (39, 23), (33, 28), (39, 28)):     # group tables
            for x in (tx, tx + 1):
                d.table(x, y, tz, B, "block", Q)
                d.chair(x, y, tz - 1, "north", M)
                d.chair(x, y, tz + 1, "south", M)
        pressz(d, 31, 22, 30, y, 3)
        panel(d, [(36, 25), (36, 29), (42, 26)], 15)
        for (x, z) in ((32, 22), (33, 22), (44, 30), (43, 30)):
            d.set(x, 16, z, "moss_block")
        d.set(32, 17, 22, "flowering_azalea")
        # --- park
        d.fill(2, 1, 34, 48, 1, 49, GRASS)
        d.fill(2, 1, 40, 48, 1, 41, "polished_diorite")
        for (x, z) in ((5, 37), (16, 46), (27, 37), (40, 46), (46, 37)):
            plant_tree(d, x, z)
        park_bench(d, 9, 43, "x", "south")
        park_bench(d, 31, 43, "x", "south")
        park_bench(d, 20, 38, "x", "north")
        bed_of(d, [(x, z, f) for (x, z), f in zip(
            [(10, 46), (11, 46), (12, 46), (13, 46), (10, 47), (11, 47), (12, 47), (13, 47),
             (33, 46), (34, 46), (35, 46), (36, 46), (33, 47), (34, 47), (35, 47), (36, 47)],
            ["allium", "azure_bluet", "white_tulip", "orange_tulip", "orange_tulip", "allium", "azure_bluet",
             "white_tulip", "white_tulip", "orange_tulip", "allium", "azure_bluet", "azure_bluet", "white_tulip",
             "orange_tulip", "allium"])])
        for x in (12, 25, 38):
            post_lamp(d, x, 39)
        # --- café kiosk (x5-11, z9-15)
        shell(d, 4, 8, 12, 16, 1, "flat", glassy=True, win="nse")
        door_out(d, 8, Y0, 8, "south")
        d.set(6, Y0, 15, "smoker[facing=north,lit=false]")              # coffee bar on the back wall
        d.set(7, Y0, 15, "water_cauldron[level=3]")
        d.set(8, Y0, 15, "barrel[facing=up,open=false]")
        d.set(9, Y0, 15, "barrel[facing=up,open=false]")
        tops(d, [(5, 13), (6, 13), (7, 13), (8, 13), (9, 13)], Y0, "smooth_quartz_slab")
        seats(d, [(6, 12, "north"), (8, 12, "north")], Y0, M)
        d.table(6, Y0, 10, B)
        seats(d, [(5, 10, "west"), (7, 10, "east")], Y0, M)
        d.table(10, Y0, 11, B)
        seats(d, [(10, 10, "north"), (10, 12, "south")], Y0, M)
        panel(d, [(8, 12)], 6)
        for x in range(4, 13):                                         # striped awning
            for z in range(4, 8):
                d.set(x, 6, z, f"{('orange' if x % 2 else 'white')}_concrete" if z == 4 else
                      slab("smooth_quartz_slab", "top"))
        for tx in (6, 10):                                             # terrace tables under the awning
            d.table(tx, Y0, 5, B)
            seats(d, [(tx - 1, 5, "west"), (tx + 1, 5, "east")], Y0, M)
        d.sign(8, 4, 7, "north", ["CAFE"], B, glow=True, color="orange")
    return d


# =============================================================================================== CASCADIA
def lib_cascadia(rel, L):
    """Mountain reading lodge: a big glazed A-frame with stacks under the eaves and a stone hearth; later a
    children's A-frame with a story circle, a log archive, a long stacks hall, a bindery, a cabin and a deck."""
    d = new("Cascadia", rel, (55, 30, 55), paving="coarse_dirt")
    S = "spruce"
    X1, X2, Z1, Z2 = 16, 34, 6, 18
    ridge = aframe(d, X1, Z1, X2, Z2)
    mid = 25
    d.double_door(mid, Y0, Z1, "x", "south", S)
    d.sign(mid, 8, Z1 - 1, "north", ["READING", "LODGE"], S)
    for x in range(X1, X2 + 1):                                       # front deck with a railing
        d.fill(x, 1, Z1 - 4, x, 1, Z1 - 1, "spruce_planks")
        if x < 24 or x > 27:
            d.set(x, Y0, Z1 - 4, "spruce_fence")
    for y in range(Y0, ridge + 2):                                     # stone chimney in the back gable
        for x in (mid, mid + 1):
            if y < ridge - 1 or x == mid:
                d.set(x, y, Z2, "cobblestone" if (x + y) % 3 else "mossy_cobblestone")
    d.hearth(mid, Y0, Z2 - 1, "north", ridge + 1, "cobblestone", "campfire")
    d.hut(X1 + 4, Y0, Z1 + 1)
    d.item(X2 - 4, Y0, Z1 + 1, "lectern", "west")
    # stacks stepped under the A-frame slopes (west x17-19, east x31-33)
    zr = (7, 17) if L >= 2 else (8, 16)
    hts = (1, 2, 3) if L >= 2 else (1, 1, 2)
    for (x, hgt) in ((17, hts[0]), (18, hts[1]), (19, hts[2]), (33, hts[0]), (32, hts[1]), (31, hts[2])):
        pressz(d, x, zr[0], zr[1], Y0, hgt)
    for z in (9, 12):                                                 # four reading tables
        for tx in (22, 29):
            d.table(tx, Y0, z, S, "post")
            d.chair(tx - 1, Y0, z, "west", S)
            d.chair(tx + 1, Y0, z, "east", S)
    d.rug(24, 8, 27, 15, Y0, ("brown_carpet", "green_carpet"))
    for z in (8, 12, 16):                                             # collar beams with lanterns
        for x in range(X1 + 7, X2 - 6):
            d.set(x, 9, z, log("stripped_spruce_log", "x"))
    hang(d, [(25, 8), (25, 12), (25, 16)], 8)
    post_lamp(d, X1 - 2, Z1 - 2)
    post_lamp(d, X2 + 2, Z1 - 2)
    if L >= 2:
        # --- children's A-frame with the story corner
        aframe(d, 38, 8, 50, 16)
        d.door(44, Y0, 8, "south", S)
        d.set(44, 1, 7, "spruce_planks")
        for (x, hgt) in ((39, 1), (40, 2), (49, 1), (48, 2)):
            pressz(d, x, 9, 15, Y0, hgt)
        d.rug(42, 10, 46, 14, Y0, ("lime_carpet", "yellow_carpet"))
        d.chair(44, Y0, 15, "south", S)                                # storyteller's chair facing the rug
        d.set(42, Y0, 15, "potted_fern")
        d.set(46, Y0, 15, "potted_fern")
        d.set(44, 7, 12, "chain[axis=y,waterlogged=false]")
        hang(d, [(44, 12)], 6)
        d.sign(44, 7, 7, "north", ["STORY", "CORNER"], S)
        post_lamp(d, 37, 6)
        post_lamp(d, 51, 6)
        bed_of(d, [(38, 5, "fern"), (39, 5, "blue_orchid"), (40, 5, "fern"), (41, 5, "dandelion"),
                   (38, 6, "lily_of_the_valley"), (39, 6, "fern"), (40, 6, "allium"), (41, 6, "fern"),
                   (47, 5, "fern"), (48, 5, "dandelion"), (49, 5, "fern"), (50, 5, "blue_orchid"),
                   (47, 6, "fern"), (48, 6, "allium"), (49, 6, "fern"), (50, 6, "lily_of_the_valley")])
        for x in range(35, 38):                                       # covered walk between the A-frames
            for z in range(10, 14):
                d.set(x, 1, z, "spruce_planks")
                d.set(x, 6, z, slab("spruce_slab"))
        for x in (35, 37):
            for z in (10, 13):
                for y in range(Y0, 6):
                    d.set(x, y, z, log("spruce_log"))
        cx, cz = 44, 3                                                # story fire circle
        d.fill(cx - 2, 1, cz - 2, cx + 2, 1, cz + 2, "gravel")
        d.set(cx, Y0, cz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        for (x, z, ax) in ((cx - 2, cz, "z"), (cx + 2, cz, "z"), (cx, cz - 2, "x")):
            d.set(x, Y0, z, log("stripped_spruce_log", ax))
    if L >= 3:
        # --- log archive (x3-11, z7-17), two storeys
        shell(d, 2, 6, 12, 18, 2, "gable", "z")
        door_out(d, 7, Y0, 6, "south")
        d.sign(7, 5, 5, "north", ["ARCHIVE"], S)
        stair(d, 11, 8, Y0, 7, "south", [(10, 9), (10, 10), (10, 11), (11, 8)])
        for z in (8, 11, 14, 17):
            press(d, 3, 8, z, Y0, 3)
        tops(d, [(11, 15)], Y0, "spruce_slab")                         # archivist's desk
        d.chair(10, Y0, 15, "west", S)
        d.candle(11, Y0 + 1, 15, 2)
        hang(d, [(6, 9), (6, 16)], 5)
        for z in (8, 11, 14, 17):
            press(d, 3, 9, z, 7, 2)
        hang(d, [(6, 12), (6, 16)], 10)
    if L >= 4:
        # --- long stacks hall (x9-43, z25-33)
        shell(d, 8, 24, 44, 34, 2, "gable", "x", ws=3)
        door_out(d, 26, Y0, 24, "south", double=True)
        d.fill(26, 1, 19, 27, 1, 23, "spruce_planks")
        stair(d, 10, 33, Y0, 7, "east", [(11, 32), (12, 32), (13, 32), (10, 33)])
        for x in (12, 13, 16, 17, 20, 21, 24, 29, 32, 33, 36, 37, 40, 41):
            pressz(d, x, 26, 32, Y0, 3)
        d.item(26, Y0, 30, "enchanting_table")
        seats(d, [(26, 28, "north"), (26, 32, "south")], Y0, S)
        hang(d, [(26, 30), (18, 25), (34, 25), (18, 33), (34, 33)], 5)
        y = 7
        press(d, 9, 43, 25, y, 1)
        press(d, 15, 43, 33, y, 1)
        for x0 in (16, 30):
            for x in range(x0, x0 + 5):
                d.table(x, y, 29, S, "block", "spruce_planks")
                d.chair(x, y, 28, "north", S)
                d.chair(x, y, 30, "south", S)
            d.candle(x0 + 1, y + 1, 29, 3)
            d.candle(x0 + 3, y + 1, 29, 2)
        hang(d, [(18, 29), (30, 29), (26, 26)], 10)
        d.sign(26, 6, 23, "north", ["THE STACKS"], S)
    if L >= 5:
        # --- librarian's cabin (x45-51, z41-49)
        shell(d, 44, 40, 52, 50, 2, "gable", "z", mat="mangrove_planks", up="mangrove_planks")
        door_out(d, 48, Y0, 40, "south")
        stair(d, 51, 42, Y0, 7, "south", [(50, 43), (50, 44), (50, 45), (51, 42)])
        d.hearth(45, Y0, 45, "east", 6, "cobblestone", "campfire")
        chimney(d, 44, 45, Y0, 17)
        seats(d, [(47, 44, "east"), (47, 46, "east")], Y0, S)
        d.rug(46, 44, 46, 46, Y0, ("brown_carpet",))
        cases(d, [(45, 41), (46, 41)], Y0, 2)
        for x, b in ((45, "smoker[facing=north,lit=false]"), (46, "water_cauldron[level=3]"),
                     (47, slab("spruce_slab", "top")), (48, slab("spruce_slab", "top")),
                     (49, "barrel[facing=up,open=false]")):
            d.set(x, Y0, 49, b)
        d.table(49, Y0, 47, S)
        seats(d, [(48, 47, "west"), (50, 47, "east")], Y0, S)
        hang(d, [(48, 43), (48, 47)], 5)
        y = 7
        d.bed(45, y, 42, "west", "brown")
        d.bed(45, y, 48, "west", "green")
        d.set(45, y, 43, "barrel[facing=up,open=false]")
        d.set(45, y, 47, "barrel[facing=up,open=false]")
        d.candle(45, y + 1, 43, 1)
        tops(d, [(49, 49)], y, "spruce_slab")
        d.chair(49, y, 48, "north", S)
        d.rug(47, 44, 48, 46, y, ("green_carpet", "brown_carpet"))
        d.set(51, y, 49, "chest[facing=west,type=single,waterlogged=false]")
        hang(d, [(48, 46)], 10)
        # --- bookbindery & print shop (x3-15, z39-51)
        shell(d, 2, 38, 16, 52, 2, "gable", "z", mat="stripped_dark_oak_log", up="stripped_dark_oak_log")
        door_out(d, 9, Y0, 38, "south", double=True)
        d.sign(9, 5, 37, "north", ["BINDERY"], S)
        d.set(3, Y0, 41, "loom[facing=east]")
        d.set(3, Y0, 42, "crafting_table")
        d.set(3, Y0, 43, "cartography_table")
        d.set(3, Y0, 44, "stonecutter[facing=east]")
        d.set(7, Y0, 44, "spruce_planks")                              # the press
        d.set(8, Y0, 44, "spruce_planks")
        d.set(7, Y0 + 1, 44, "piston[extended=false,facing=down]")
        d.set(8, Y0 + 1, 44, "piston[extended=false,facing=down]")
        tops(d, [(10, 41), (11, 41)], Y0, "spruce_slab")               # binding bench
        seats(d, [(10, 42, "south"), (11, 42, "south")], Y0, S)
        press(d, 4, 11, 48, Y0, 2)
        press(d, 4, 11, 50, Y0, 2)
        stair(d, 14, 47, Y0, 7, "north", [(13, 43), (13, 44), (13, 45), (14, 46)])
        hang(d, [(8, 42), (8, 47)], 5)
        y = 7
        for z in (41, 44, 47, 50):
            press(d, 4, 8, z, y, 2)
        for x in (10, 11):
            d.table(x, y, 45, S, "block", "spruce_planks")
            d.chair(x, y, 44, "north", S)
            d.chair(x, y, 46, "south", S)
        hang(d, [(11, 42), (11, 46)], 10)
        # --- reading garden with the lookout deck
        for x in range(18, 43):
            if x not in (24, 30, 31):
                d.set(x, 2, 37, "spruce_fence")
        for (x, z) in ((19, 49), (20, 49), (35, 41), (36, 41), (41, 51), (17, 44)):
            d.set(x, 1, z, "moss_block")
        plant_tree(d, 19, 50)
        plant_tree(d, 35, 50)
        plant_tree(d, 39, 41)
        park_bench(d, 26, 49, "x", "south")
        park_bench(d, 36, 46, "z", "east")
        post_lamp(d, 30, 39)
        post_lamp(d, 42, 47)
        dk = (20, 40, 32, 46)
        for x in range(dk[0], dk[2] + 1):
            for z in range(dk[1], dk[3] + 1):
                d.set(x, 4, z, "spruce_planks")
                if (x in (dk[0], dk[2]) or z in (dk[1], dk[3])) and (x, z) != (24, 40):
                    d.set(x, 5, z, "spruce_fence")
        for x, z in ((dk[0], dk[1]), (dk[2], dk[1]), (dk[0], dk[3]), (dk[2], dk[3])):
            for y in range(Y0, 4):
                d.set(x, y, z, log("spruce_log"))
        stair(d, 24, 37, Y0, 5, "south", [])                           # steps up to the deck
        seats(d, [(23, 45, "south"), (24, 45, "south"), (28, 45, "south"), (29, 45, "south")], 5, S, sit=False)
        d.table(26, 5, 44, S)
        d.set(31, 5, 41, "lantern[hanging=false,waterlogged=false]")
    return d


@design("library")
def library_v2(pack, rel, L):
    return common_materials({"Hearthwood": lib_hearthwood, "Cascadia": lib_cascadia, "Neoterra": lib_neoterra}[pack](rel, L))
