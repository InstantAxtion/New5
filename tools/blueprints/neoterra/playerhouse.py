"""
Neoterra Player House ("Skyhome"), a decoration (no hut block): a large, fully equipped
player base. Uses MineColonies' decoration controller block, like the official
`decorations/housing/playermansion` blueprint, so the builder can build it but it does not
count as a colony building. Single blueprint (decorations have no levels), premium palette.

  Ground floor   workshop wing (4 furnaces, 2 blast furnaces, 2 smokers, crafting table,
                 smithing table, stonecutter, loom, cartography & fletching tables, anvil),
                 entrance hall, storage vault (~120 barrels).
  Upper floor    floating glass box: enchanting library (30 bookshelves), lounge with jukebox,
                 bedroom suite (2 beds) with brewing station; doors to the back roof terrace.
  Roof           roof garden with a working beacon on an iron-block base, seating, railing.
  Garden         pool, vegetable farm (wheat, carrots, potatoes, beetroot) with water channel,
                 composter, nether portal frame (light it yourself), trees, lamp spires.

35 x 22 x 29. Front = north (z 0). y 0 foundation, y 1 ground.
"""
from __future__ import annotations

import sys
from pathlib import Path

from nbtlib import tag as T

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    Blueprint, Style, put, connect_panes, tree, planter, street_lamp, do_slab, bed, door, chair,
    PACK_NAME,
)

SX, SY, SZ = 35, 22, 29
GX1, GX2, GZ1, GZ2 = 3, 30, 6, 22          # ground floor shell
UX1, UX2, UZ1, UZ2 = 6, 27, 4, 19          # floating upper box
SLAB, ROOF = 7, 13
PATH = "decorations/housing/playerhouse.blueprint"


def decoration_te(controller, tags):
    cx, cy, cz = controller

    def pos(x, y, z):
        return T.Compound({"x": T.Int(x), "y": T.Int(y), "z": T.Int(z)})

    tag_list = [T.Compound({"tagPos": pos(x - cx, y - cy, z - cz),
                            "tagNameList": T.List[T.Compound]([T.Compound({"tagName": T.String(n)}) for n in names])})
                for (x, y, z), names in sorted(tags.items())]
    return T.Compound({
        "id": T.String("minecolonies:decorationcontroller"),
        "path": T.String(PATH),
        "name": T.String("playerhouse"),
        "pack": T.String(PACK_NAME),
        "Item": T.String(""),
        "mirror": T.Byte(0),
        "rotation": T.Int(0),
        "blueprintDataProvider": T.Compound({
            "corner1": pos(-cx, -cy, -cz),
            "corner2": pos(SX - 1 - cx, SY - 1 - cy, SZ - 1 - cz),
            "path": T.String(PATH),
            "schematicName": T.String("playerhouse"),
            "pack": T.String(PACK_NAME),
            "posTagMap": T.List[T.Compound](tag_list),
        }),
    })


def edge(x, z, x1, x2, z1, z2):
    return x in (x1, x2) or z in (z1, z2)


def build() -> Blueprint:
    st = Style(5)
    bp = Blueprint(SX, SY, SZ, "playerhouse.blueprint")
    W, G, TR, D, AC = st.WHITE, st.GLASS, st.TRIM, st.DECK, st.ACCENT
    glow = st.GLOW
    sit = []

    # ------------------------------------------------------------ ground & garden
    bp.fill(0, 0, 0, SX - 1, 0, SZ - 1, "structurize:blocksolidsubstitution")
    for x in range(SX):
        for z in range(SZ):
            if 16 <= x <= 18 and z < GZ1:
                s = W if x in (16, 18) else "smooth_quartz"
            elif GX1 <= x <= GX2 and GZ1 <= z <= GZ2:
                s = st.floor(x, z)
            else:
                s = "grass_block[snowy=false]"
            bp.set(x, 1, z, s)

    # ------------------------------------------------------------ ground floor shell
    for x in range(GX1, GX2 + 1):
        for z in range(GZ1, GZ2 + 1):
            if not edge(x, z, GX1, GX2, GZ1, GZ2):
                continue
            for y in range(2, SLAB):
                corner = x in (GX1, GX2) and z in (GZ1, GZ2)
                if y == SLAB - 1:
                    s = "sea_lantern"                                      # light strip
                elif corner:
                    s = W
                elif z == GZ1:
                    s = st.WOOD if (x - GX1) % 4 == 0 else G
                elif y in (3, 4) and (x + z) % 4:
                    s = G
                else:
                    s = W
                bp.set(x, y, z, s)
    for x in (16, 17, 18):
        bp.set(x, 2, GZ1, f"waxed_copper_door[facing=south,half=lower,hinge={'left' if x < 17 else 'right'},open=false,powered=false]")
        bp.set(x, 3, GZ1, f"waxed_copper_door[facing=south,half=upper,hinge={'left' if x < 17 else 'right'},open=false,powered=false]")
        bp.set(x, 4, GZ1, G)
    for y in (2, 3):
        bp.set(17, y, GZ2, "air")                                          # back door to the garden
    # partitions between workshop | hall | storage
    for xp in (13, 21):
        for z in range(GZ1 + 1, GZ2):
            for y in range(2, SLAB):
                bp.set(xp, y, z, W if y < 5 else G)
        for z in (10, 17):
            for y in (2, 3):
                bp.set(xp, y, z, "air")
    # slab / upper floor floor / ground roof terraces
    for x in range(GX1, GX2 + 1):
        for z in range(GZ1, GZ2 + 1):
            bp.set(x, SLAB, z, AC if edge(x, z, GX1, GX2, GZ1, GZ2) else st.floor(x, z))
    for x in range(5, 30, 4):
        for z in (9, 13, 18):
            st.ceiling_light(bp, x, SLAB, z)

    # ------------------------------------------------------------ floating upper box
    for x in range(UX1, UX2 + 1):
        for z in range(UZ1, UZ2 + 1):
            e = edge(x, z, UX1, UX2, UZ1, UZ2)
            if z < GZ1:
                bp.set(x, SLAB, z, glow if e else D)                       # cantilevered floor
            bp.set(x, ROOF, z, AC if e else D)
            if not e:
                continue
            for y in range(SLAB + 1, ROOF):
                corner = x in (UX1, UX2) and z in (UZ1, UZ2)
                if corner:
                    s = "sea_lantern"
                elif y == ROOF - 1:
                    s = W
                elif z == UZ1:
                    s = G                                                  # full-height glass front
                elif y in (9, 10):
                    s = G
                else:
                    s = W
                bp.set(x, y, z, s)
    for xp in (12, 21):
        for z in range(UZ1 + 1, UZ2):
            for y in range(SLAB + 1, ROOF):
                bp.set(xp, y, z, W if y < 11 else G)
        for y in (SLAB + 1, SLAB + 2):
            bp.set(xp, y, 15, "air")
    for x in (16, 17):                                                     # doors to the back terrace
        for y in (SLAB + 1, SLAB + 2):
            bp.set(x, y, UZ2, "air")
    for x, z in ((9, 16), (15, 7), (18, 12), (24, 8), (24, 15)):
        st.ceiling_light(bp, x, ROOF, z)
    # terrace railing on the exposed ground-floor roof
    for x in range(GX1, GX2 + 1):
        for z in range(GZ1, GZ2 + 1):
            inside_box = UX1 <= x <= UX2 and UZ1 <= z <= UZ2
            if edge(x, z, GX1, GX2, GZ1, GZ2) and not inside_box:
                put(bp, x, SLAB + 1, z, st.railing)
    for x in (8, 26):
        planter(bp, x, SLAB + 1, 21)
    for x in (12, 14, 19, 21):
        chair(bp, x, SLAB + 1, 21, st.SEAT, "south", sit)

    # ------------------------------------------------------------ stairs
    # ground -> upper floor: x15, rising south z8 -> z13, landing z14
    for i in range(6):
        z, y = 8 + i, 2 + i
        if y > 2:
            bp.fill(15, 2, z, 15, y - 1, z, W)
        bp.set(15, y, z, f"{st.SEAT}[facing=south,half=bottom,shape=straight,waterlogged=false]")
    for z in range(8, 13):
        bp.set(15, SLAB, z, "air")
        put(bp, 16, SLAB + 1, z, st.railing)
    put(bp, 15, SLAB + 1, 7, st.railing)
    # upper floor -> roof: x19, rising north z13 -> z8, landing z7
    for i in range(6):
        z, y = 13 - i, SLAB + 1 + i
        if y > SLAB + 1:
            bp.fill(19, SLAB + 1, z, 19, y - 1, z, W)
        bp.set(19, y, z, f"{st.SEAT}[facing=north,half=bottom,shape=straight,waterlogged=false]")
    for z in range(9, 14):
        bp.set(19, ROOF, z, "air")
        put(bp, 18, ROOF + 1, z, st.railing)
    put(bp, 19, ROOF + 1, 14, st.railing)

    # ------------------------------------------------------------ ground floor rooms
    y = 2
    # workshop (x4..12)
    for z, s in ((9, "furnace"), (10, "furnace"), (11, "furnace"), (12, "furnace"),
                 (14, "blast_furnace"), (15, "blast_furnace"), (17, "smoker"), (18, "smoker")):
        bp.set(4, y, z, f"{s}[facing=east,lit=false]")
    for z in (8, 13, 16, 19, 20):
        bp.set(4, y, z, "barrel[facing=east,open=false]")
    for x, s in ((5, "crafting_table"), (6, "smithing_table"), (7, "stonecutter[facing=north]"),
                 (8, "loom[facing=north]"), (9, "cartography_table"), (10, "fletching_table"),
                 (11, "anvil[facing=east]"), (12, "barrel[facing=north,open=false]")):
        bp.set(x, y, 21, s)
    for x in range(7, 11):
        put(bp, x, y, 14, st.counter)                                      # central workbench
    # entrance hall (x14..20): controller, ender chest, lectern, seats
    controller = (19, 2, 8)
    bp.set(20, y, 12, "ender_chest[facing=west,waterlogged=false]")
    bp.set(20, y, 13, "crafting_table")
    bp.set(20, y, 19, "lectern[facing=west,has_book=false,powered=false]")
    for x in (17, 18):
        chair(bp, x, y, 18, st.SEAT, "south", sit)
    # storage vault (x22..29): barrel walls + island, 3 high
    for yy in (2, 3, 4):
        for z in range(8, 21):
            bp.set(29, yy, z, "barrel[facing=west,open=false]")
        for x in range(23, 29):
            bp.set(x, yy, 21, "barrel[facing=north,open=false]")
        for z in range(10, 19):
            bp.set(25, yy, z, "barrel[facing=west,open=false]")
            bp.set(26, yy, z, "barrel[facing=east,open=false]")

    # ------------------------------------------------------------ upper floor rooms
    y = SLAB + 1
    # enchanting library (x7..11): 5x5 ring of bookshelves, 2 high
    for x in range(7, 12):
        for z in range(9, 14):
            ring = x in (7, 11) or z in (9, 13)
            for yy in (y, y + 1):
                bp.set(x, yy, z, "bookshelf" if ring else "air")
    for yy in (y, y + 1):
        bp.set(9, yy, 13, "air")                                          # way in (south side)
    bp.set(9, y, 11, "enchanting_table")
    bp.set(8, y, 16, "anvil[facing=north]")
    bp.set(9, y, 16, "grindstone[face=floor,facing=north]")
    bp.set(10, y, 16, "lectern[facing=north,has_book=false,powered=false]")
    for x in range(7, 12):
        bp.set(x, y, 18, "bookshelf")
    # lounge (x13..20)
    for x in (14, 15, 16):
        chair(bp, x, y, 6, st.SEAT, "south", sit)                          # sofa facing the glass front
    put(bp, 15, y, 8, st.counter)
    bp.set(13, y, 18, "jukebox[has_record=false]")
    bp.set(14, y, 18, "barrel[facing=up,open=false]")
    # bedroom suite + brewing (x22..26)
    bed(bp, 24, y, 6, "north")
    bed(bp, 26, y, 6, "north")
    bp.set(25, y, 5, "barrel[facing=south,open=false]")
    for z in (12, 13):
        bp.set(26, y, z, "barrel[facing=west,open=false]")
    bp.set(26, y, 16, "brewing_stand[has_bottle_0=false,has_bottle_1=false,has_bottle_2=false]")
    bp.set(26, y, 17, "brewing_stand[has_bottle_0=false,has_bottle_1=false,has_bottle_2=false]")
    bp.set(26, y, 18, "water_cauldron[level=3]")
    bp.set(25, y, 18, "barrel[facing=north,open=false]")

    # ------------------------------------------------------------ roof: beacon, garden, railing
    for x in range(UX1, UX2 + 1):
        for z in range(UZ1, UZ2 + 1):
            if edge(x, z, UX1, UX2, UZ1, UZ2):
                put(bp, x, ROOF + 1, z, st.railing)
    bp.fill(23, ROOF, 9, 25, ROOF, 11, "iron_block")
    bp.set(24, ROOF + 1, 10, "beacon")
    for x, z in ((8, 6), (8, 17), (13, 17)):
        planter(bp, x, ROOF + 1, z)
    tree(bp, 10, ROOF + 1, 13, h=2)
    for x in (22, 23, 24):
        chair(bp, x, ROOF + 1, 16, st.SEAT, "south", sit)

    # ------------------------------------------------------------ garden: pool, farm, portal, trees
    for x in range(19, 31):
        for z in range(24, 28):
            e = edge(x, z, 19, 30, 24, 27)
            bp.set(x, 1, z, W if e else "water[level=0]")
            if not e:
                bp.set(x, 0, z, "sea_lantern" if (x + z) % 3 == 0 else "smooth_quartz")
    for x in range(19, 31):
        bp.set(x, 1, 23, D)
    crops = ["wheat[age=7]", "carrots[age=7]", "potatoes[age=7]", "beetroots[age=3]"]
    for x in range(3, 13):
        for z in range(24, 28):
            if z == 25:
                bp.set(x, 1, z, "water[level=0]")                         # irrigation channel
            else:
                bp.set(x, 1, z, "farmland[moisture=7]")
                bp.set(x, 2, z, crops[(x // 3) % 4])
    bp.set(13, 2, 24, "composter[level=0]")
    for x in range(13, 17):                                                # nether portal frame (unlit)
        for yy in range(2, 7):
            if x in (13, 16) or yy in (2, 6):
                bp.set(x, yy, 28, "obsidian")
    tree(bp, 1, 2, 2, h=4)
    tree(bp, 32, 2, 2, h=4)
    tree(bp, 1, 2, 22, h=4)
    tree(bp, 32, 2, 21, h=4)
    for x in (12, 22):
        street_lamp(bp, x, 2, 1, premium=True)

    connect_panes(bp)
    tags = {(0, 1, 0): ["groundlevel"]}
    for p in sit:
        tags.setdefault(p, []).append("sit")
    bp.set(*controller, "minecolonies:decorationcontroller[facing=north,mirror=false,waterlogged=false]",
           decoration_te(controller, tags))
    bp.primary_offset = controller
    bp.architects = ["Neoterra"]
    return bp


if __name__ == "__main__":
    out = Path(sys.argv[1])
    out.parent.mkdir(parents=True, exist_ok=True)
    b = build()
    b.save(out)
    n = sum(1 for *_, s in b.blocks() if s not in ("minecraft:air", "structurize:blocksolidsubstitution"))
    print(f"playerhouse: {n} blocks")
