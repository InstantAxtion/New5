"""
Cascadia University (education/university1-5): a Pacific Northwest college campus hall.

  L1  river-rock schoolhouse hall, steep timber gable, entrance hood, lecture room with lectern and desks
  L2  second storey, columned portico with pediment, bell tower with clock faces
  L3  two lecture wings left and right (symmetrical H front, side gables)
  L4  library hall behind with tall windows and book stacks; open belfry with a bell
  L5  tuff and basalt, copper spire, lanterns on the portico

The hut sits at the back of the main hall on every level (the anchor never moves relative to the hall).

usage: python university_cascadia.py <Cascadia pack dir>
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import rack_te  # noqa: E402
from twinbuilder import hut_te, SOLID  # noqa: E402
from wonders import W  # noqa: E402

STYLE = "Cascadia"
HUT = "minecolonies:blockhutuniversity[facing=north]"
RACK = "minecolonies:blockminecoloniesrack[facing={},variant=blockrackemptysingle]"


def mats(L):
    if L == 5:
        return dict(base="tuff_bricks", base2="polished_tuff", wall="spruce_planks", frame="stripped_spruce_log[axis=y]",
                    col="polished_basalt[axis=y]", trim="tuff_bricks", roof="dark_oak", ridge="moss_block",
                    floor="dark_oak_planks", face="calcite", spire="waxed_weathered_cut_copper", plaza="tuff_bricks")
    return dict(base="cobblestone", base2="mossy_cobblestone", wall="spruce_planks", frame="spruce_log[axis=y]",
                col="stripped_spruce_log[axis=y]", trim="stone_bricks", roof="dark_oak", ridge="moss_block",
                floor="spruce_planks", face="calcite", spire="dark_oak_planks", plaza="cobblestone")


def build(L):
    m = mats(L)
    wings = L >= 3
    library = L >= 4
    W_ = 33 if wings else 15
    D = 27 if library else 18
    TOP = (16, 22, 25, 30, 33)[L - 1]
    w = W(STYLE, L, W_, TOP + 2, D, f"university{L}.blueprint")
    cx, zf = W_ // 2, 4                     # hall centre line, hall front wall
    hx1, hx2, hz1, hz2 = cx - 6, cx + 6, zf, zf + 12
    tags = {(0, 1, 0): ["groundlevel"]}

    # ---- ground, plinth -------------------------------------------------------------------------
    for x in range(W_):
        for z in range(D):
            w.S(x, 0, z, SOLID)
            w.S(x, 1, z, m["plaza"])

    def plinth(x1, x2, z1, z2):
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                w.S(x, 2, z, m["base2"] if (x + z) % 3 == 0 else m["base"])
                if x1 < x < x2 and z1 < z < z2:
                    w.S(x, 2, z, m["floor"])

    def walls(x1, x2, z1, z2, storeys, frame_every=4):
        top = 2 + 5 * storeys
        for y in range(3, top + 1):
            for x in range(x1, x2 + 1):
                for z in range(z1, z2 + 1):
                    edge = x in (x1, x2) or z in (z1, z2)
                    if not edge:
                        w.S(x, y, z, "air")
                        continue
                    corner = x in (x1, x2) and z in (z1, z2)
                    along = (x - x1) if z in (z1, z2) else (z - z1)
                    if corner or along % frame_every == 0:
                        s = m["frame"]
                    elif y == 3:
                        s = m["base"]                       # river-rock skirt
                    elif (y - 3) % 5 == 4:
                        s = m["trim"]                       # storey band
                    elif (y - 3) % 5 in (1, 2, 3) and along % 2 == 0:
                        s = "glass_pane"                    # tall window
                    else:
                        s = m["wall"]
                    w.S(x, y, z, s)
        for s in range(1, storeys):                         # upper floors
            for x in range(x1 + 1, x2):
                for z in range(z1 + 1, z2):
                    w.S(x, 2 + 5 * s + 1, z, m["floor"])
        return top

    def ladder(x, z, wall_facing, storeys):
        for y in range(3, 3 + 5 * (storeys - 1) + 1):
            w.S(x, y, z, f"ladder[facing={wall_facing},waterlogged=false]")

    # ---- main hall ------------------------------------------------------------------------------
    storeys = 1 if L == 1 else 2
    plinth(hx1, hx2, hz1, hz2)
    top = walls(hx1, hx2, hz1, hz2, storeys)
    w.gable_z(hx1, hx2, hz1, hz2, top + 1, m["roof"], m["wall"])
    for z in range(hz1 - 1, hz2 + 2):                      # moss ridge
        w.S(cx, top + 7, z, m["ridge"])
    if storeys > 1:
        ladder(hx1 + 1, hz2 - 1, "east", storeys)
    # entrance: double door on the centre line
    for x, hinge in ((cx - 1, "left"), (cx, "right"), (cx + 1, "right")):
        for y in (3, 4, 5):
            w.S(x, y, hz1, "air")
    w.S(cx, 3, hz1, "spruce_door[facing=south,half=lower,hinge=left,open=false,powered=false]")
    w.S(cx, 4, hz1, "spruce_door[facing=south,half=upper,hinge=left,open=false,powered=false]")
    w.S(cx - 1, 3, hz1, m["frame"]); w.S(cx + 1, 3, hz1, m["frame"])
    w.S(cx - 1, 4, hz1, m["frame"]); w.S(cx + 1, 4, hz1, m["frame"])
    w.S(cx - 1, 5, hz1, w.stair("stone_bricks", "east", "top")); w.S(cx + 1, 5, hz1, w.stair("stone_bricks", "west", "top"))
    w.S(cx, 5, hz1, m["trim"])
    # front steps
    for x in range(cx - 3, cx + 4):
        w.S(x, 2, 1, w.stair("cobblestone" if L < 5 else "tuff_brick", "south"))
        for z in (2, 3):
            w.S(x, 2, z, m["base"])

    # lecture room: desks facing the lectern at the back, bookshelves along the walls
    for z in range(hz1 + 3, hz1 + 9, 2):
        for x in list(range(hx1 + 3, cx - 1)) + list(range(cx + 2, hx2 - 2)):
            w.S(x, 3, z, w.stair("spruce", "north"))
            tags[(x, 3, z)] = ["sit"]
            w.S(x, 3, z + 1, "spruce_slab[type=top,waterlogged=false]") if z + 1 < hz1 + 9 else None
    for z in range(hz1 + 2, hz2):
        w.S(cx, 3, z, "green_carpet")
    w.S(cx, 3, hz2 - 3, "lectern[facing=north,has_book=false,powered=false]")
    hut = (cx - 2, 3, hz2 - 1)
    w.S(cx + 2, 3, hz2 - 1, RACK.format("north"), rack_te())
    shelves = (4, 8, 12, 14, 16)[L - 1]
    n = 0
    for z in range(hz1 + 2, hz2 - 1):
        for x in (hx1 + 1, hx2 - 1):
            if n >= shelves or (x == hx1 + 1 and z == hz2 - 1) or (wings and z == hz1 + 6):
                continue
            w.S(x, 3, z, "bookshelf")
            n += 1
    for z in range(hz1 + 3, hz2, 4):                       # hanging lights
        w.S(cx, top - 1 if storeys == 1 else 7, z, "lantern[hanging=true,waterlogged=false]")
    if storeys > 1:                                         # upstairs reading room
        for z in range(hz1 + 2, hz2 - 1, 2):
            for x in (hx1 + 1, hx2 - 1):
                w.S(x, 9, z, "bookshelf")
                w.S(x, 10, z, "bookshelf")
        w.S(cx, 9, hz1 + 6, "lectern[facing=north,has_book=false,powered=false]")
        for z in range(hz1 + 3, hz2 - 1, 4):
            w.S(cx, 12, z, "lantern[hanging=true,waterlogged=false]")

    # ---- portico (L1: entrance hood) ---------------------------------------------------------------
    if L == 1:
        for x in (cx - 2, cx + 2):
            for y in range(3, 7):
                w.S(x, y, 2, m["col"])
        w.gable_z(cx - 2, cx + 2, 2, 3, 7, m["roof"], m["wall"])
    else:
        for x in (cx - 5, cx - 3, cx + 3, cx + 5):
            for y in range(3, 10):
                w.S(x, y, 2, m["col"])
            w.S(x, 3, 2, m["trim"])
        w.box(cx - 6, 10, 2, cx + 6, 10, 3, m["trim"])     # architrave
        w.box(cx - 6, 11, 2, cx + 6, 11, 3, w.slab(m["roof"]))
        for k in range(6):                                  # triangular pediment on the front
            y = 11 + k
            x1, x2 = cx - 6 + k, cx + 6 - k
            w.S(x1, y, 2, w.stair(m["roof"], "east"))
            w.S(x2, y, 2, w.stair(m["roof"], "west"))
            for x in range(x1 + 1, x2):
                w.S(x, y, 2, m["trim"] if k == 0 else m["wall"])
        w.S(cx, 17, 2, w.slab(m["roof"]))
        w.S(cx, 13, 2, m["face"])
        if L == 5:
            for x in (cx - 5, cx + 5):
                w.S(x, 9, 1, "lantern[hanging=true,waterlogged=false]")
                w.S(x, 10, 1, m["trim"])

    # ---- bell tower over the entrance ------------------------------------------------------------
    if L >= 2:
        tx1, tx2, tz1, tz2 = cx - 2, cx + 2, hz1 + 1, hz1 + 5
        tt = (0, 17, 19, 21, 23)[L - 1]
        for y in range(top + 1, tt + 1):
            for x in range(tx1, tx2 + 1):
                for z in range(tz1, tz2 + 1):
                    edge = x in (tx1, tx2) or z in (tz1, tz2)
                    corner = x in (tx1, tx2) and z in (tz1, tz2)
                    w.S(x, y, z, (m["frame"] if corner else m["wall"]) if edge else "air")
        w.box(tx1, top + 1, tz1 + 1, tx2, top + 1, tz2 - 1, m["floor"])
        for x, z in ((tx1, tz1), (tx2, tz1), (tx1, tz2), (tx2, tz2)):   # corner posts carry the tower to the floor
            for y in range(3, top + 1):
                w.S(x, y, z, m["frame"])
            tags.pop((x, 3, z), None)
        # clock faces on the three visible sides
        cy = tt - 2
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                w.S(cx + dx, cy + dy, tz1, m["face"])
                w.S(tx1, cy + dy, (tz1 + tz2) // 2 + dx, m["face"])
                w.S(tx2, cy + dy, (tz1 + tz2) // 2 + dx, m["face"])
        w.S(cx, cy, tz1, "dark_oak_log[axis=z]")
        w.S(cx, cy + 1, tz1, "dark_oak_fence")
        w.S(tx1, cy, (tz1 + tz2) // 2, "dark_oak_log[axis=x]")
        w.S(tx2, cy, (tz1 + tz2) // 2, "dark_oak_log[axis=x]")
        w.box(tx1, tt + 1, tz1, tx2, tt + 1, tz2, m["trim"])
        y = tt + 2
        if L >= 4:                                          # open belfry with a bell
            for yy in range(y, y + 3):
                for x in range(tx1, tx2 + 1):
                    for z in range(tz1, tz2 + 1):
                        corner = x in (tx1, tx2) and z in (tz1, tz2)
                        w.S(x, yy, z, m["col"] if corner else "air")
            w.box(tx1, y + 3, tz1, tx2, y + 3, tz2, m["trim"])
            w.S(cx, y + 2, (tz1 + tz2) // 2, "bell[attachment=ceiling,facing=north,powered=false]")
            y += 4
        r = 3
        while r >= 0:                                       # pyramid / spire roof
            for x in range(cx - r, cx + r + 1):
                for z in range((tz1 + tz2) // 2 - r, (tz1 + tz2) // 2 + r + 1):
                    w.S(x, y, z, m["spire"] if L == 5 else m["roof"] + "_planks")
            r -= 1
            y += 1
        if L == 5:
            w.S(cx, y, (tz1 + tz2) // 2, "lightning_rod[facing=up,powered=false,waterlogged=false]")

    # ---- lecture wings ---------------------------------------------------------------------------
    if wings:
        for x1, x2, side in ((cx - 15, cx - 7, -1), (cx + 7, cx + 15, 1)):
            z1, z2 = hz1 + 1, hz1 + 11
            plinth(x1, x2, z1, z2)
            wt = walls(x1, x2, z1, z2, 2)
            w.gable_x(x1, x2, z1, z2, wt + 1, m["roof"], m["wall"])
            for x in range(x1 - 1, x2 + 2):
                w.S(x, wt + 6, (z1 + z2) // 2, m["ridge"])
            # link to the hall (2 high opening through both walls and the gap)
            gx = (hx1, x2) if side < 0 else (x1, hx2)
            for x in range(min(gx), max(gx) + 1):
                for y in (3, 4):
                    w.S(x, y, hz1 + 6, "air")
                w.S(x, 2, hz1 + 6, m["floor"])
                w.S(x, 5, hz1 + 6, m["trim"])
                for z in (hz1 + 5, hz1 + 7):
                    if not (x1 <= x <= x2) and not (hx1 <= x <= hx2):
                        for y in (3, 4, 5):
                            w.S(x, y, z, m["base"])
            # front door of the wing
            dx = (x1 + x2) // 2
            w.S(dx, 3, z1, "spruce_door[facing=south,half=lower,hinge=left,open=false,powered=false]")
            w.S(dx, 4, z1, "spruce_door[facing=south,half=upper,hinge=left,open=false,powered=false]")
            # classroom: desks + lectern, book stacks along the outer wall
            ox = x1 + 1 if side < 0 else x2 - 1
            for z in range(z1 + 1, z2):
                if z != hz1 + 6:
                    w.S(ox, 3, z, "bookshelf")
                    if L >= 4:
                        w.S(ox, 4, z, "bookshelf")
            for z in range(z1 + 3, z2 - 1, 2):
                for x in range(x1 + 3, x2 - 2):
                    if x != dx:
                        w.S(x, 3, z, w.stair("spruce", "north"))
                        tags[(x, 3, z)] = ["sit"]
            w.S(dx, 3, z2 - 1, "lectern[facing=north,has_book=false,powered=false]")
            ladder(x2 - 1 if side < 0 else x1 + 1, z2 - 1, "west" if side < 0 else "east", 2)
            for z in range(z1 + 2, z2, 4):
                w.S(dx, 7, z, "lantern[hanging=true,waterlogged=false]")

    # ---- library hall behind ---------------------------------------------------------------------
    if library:
        lx1, lx2, lz1, lz2 = cx - 5, cx + 5, hz2, hz2 + 9
        plinth(lx1, lx2, lz1 + 1, lz2)
        for y in range(3, 14):
            for x in range(lx1, lx2 + 1):
                for z in range(lz1 + 1, lz2 + 1):
                    edge = x in (lx1, lx2) or z == lz2
                    if not edge:
                        w.S(x, y, z, "air")
                        continue
                    along = (z - lz1) if x in (lx1, lx2) else (x - lx1)
                    if along % 3 == 0:
                        s = m["frame"]
                    elif y == 3:
                        s = m["base"]
                    elif 4 <= y <= 11:
                        s = "glass_pane"                     # tall library windows
                    else:
                        s = m["wall"]
                    w.S(x, y, z, s)
        w.gable_z(lx1, lx2, lz1 + 1, lz2, 14, m["roof"], m["wall"])
        for x in range(cx - 1, cx + 2):                     # opening from the hall
            for y in (3, 4, 5):
                w.S(x, y, hz2, "air")
        w.S(cx - 1, 3, hz2, m["frame"]); w.S(cx + 1, 3, hz2, m["frame"])
        w.S(cx - 1, 4, hz2, m["frame"]); w.S(cx + 1, 4, hz2, m["frame"])
        # stacks: freestanding double shelves with aisles
        for x in (cx - 3, cx + 3):
            for z in range(lz1 + 3, lz2 - 1):
                for y in (3, 4, 5):
                    w.S(x, y, z, "bookshelf")
        w.S(cx, 3, lz2 - 2, "lectern[facing=north,has_book=false,powered=false]")
        for z in range(lz1 + 2, lz2, 3):
            w.S(cx, 12, z, "lantern[hanging=true,waterlogged=false]")
            w.S(cx, 13, z, "chain[axis=y,waterlogged=false]")

    bp = w.finish(HUT, hut, f"education/university{L}.blueprint")
    # re-write the hut with the sit tags
    w.S(*hut, HUT, hut_te(STYLE, f"education/university{L}.blueprint", (w.sx, w.sy, w.sz), hut, tags))
    return bp


def main():
    root = Path(sys.argv[1])
    d = root / "education"
    d.mkdir(parents=True, exist_ok=True)
    for L in range(1, 6):
        build(L).save(d / f"university{L}.blueprint")
    print("Cascadia: university 1-5 (campus hall)")


if __name__ == "__main__":
    main()
