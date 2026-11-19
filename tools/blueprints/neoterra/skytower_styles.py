"""
Pack-specific sky towers (residence hut + four flat child huts, skytowerflat1-5).

  Hearthwood  red-brick mansion block: white storey bands, projecting bay windows, mansard roof with dormers,
              lobby with the porter's beds, stair/ladder core at the east end, one 14 x 9 flat per floor
  Cascadia    stepped terrace lodge: river-rock ground floor, timber floors that each step back with a railed deck in
              front, ladder core at the back, 11 x 6 flats, steep gable roof with a mossy ridge on top

Requirements as the Neoterra sky tower: lobby beds = level, every flat has beds = level, furnace, crafting table,
barrel and seats.

usage: python skytower_styles.py <pack dir> <Hearthwood|Cascadia>
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import connect_panes  # noqa: E402
from twinbuilder import hut_te, SOLID, SUBST  # noqa: E402
from bunker_styles import G  # noqa: E402

HUT = "minecolonies:blockhutcitizen[facing=north]"
FLAT = {"Hearthwood": (14, 9), "Cascadia": (11, 6)}           # interior x, z
DOOR = {"Hearthwood": (13, 4), "Cascadia": (10, 3)}           # local cell just inside the flat door (east wall)
SEAT = {"Hearthwood": "dark_oak_stairs", "Cascadia": "spruce_stairs"}
TABLE = {"Hearthwood": "dark_oak_slab[type=top,waterlogged=false]", "Cascadia": "spruce_slab[type=top,waterlogged=false]"}
BED = {"Hearthwood": "red", "Cascadia": "green"}


def flat_hut(style):
    sx, sz = FLAT[style]
    return (0, 0, sz // 2)


def furnish_flat(style, g, L, ox, oy, oz, tags):
    sx, sz = FLAT[style]
    dx, dz = DOOR[style]
    for i in range(L):                                          # beds along the back wall
        x = 1 + 2 * i
        g.bed(ox + x, oy, oz + sz - 1, "north", BED[style])
    g.S(ox + 1, oy, oz, "furnace[facing=south,lit=false]")
    g.S(ox + 2, oy, oz, "crafting_table")
    g.S(ox + 3, oy, oz, "barrel[facing=south,open=false]")
    tx, tz = sx // 2, sz // 2 - (1 if style == "Cascadia" else 0)
    g.S(ox + tx, oy, oz + tz, TABLE[style])
    for sxx, f in ((tx - 1, "west"), (tx + 1, "east")):
        if (sxx, tz) != (dx, dz):
            g.S(ox + sxx, oy, oz + tz, f"{SEAT[style]}[facing={f},half=bottom,shape=straight,waterlogged=false]")
            tags.setdefault((ox + sxx, oy, oz + tz), []).append("sit")
    g.S(ox + tx, oy + 3, oz + 1, "lantern[hanging=true,waterlogged=false]")


def build_flat(style, L):
    sx, sz = FLAT[style]
    g = G(sx, 4, sz, f"skytowerflat{L}.blueprint")
    tags = {}
    furnish_flat(style, g, L, 0, 0, 0, tags)
    hut = flat_hut(style)
    tags.setdefault(hut, []).append("invisible")
    path = f"fundamentals/skytowerflat{L}.blueprint"
    g.S(*hut, HUT, hut_te(style, path, (sx, 4, sz), hut, tags))
    g.bp.primary_offset = hut
    g.bp.architects = [style]
    return g.bp


def place_flat(g, style, x1, F, z1, regions):
    sx, sz = FLAT[style]
    for x in range(x1, x1 + sx):
        for z in range(z1, z1 + sz):
            for y in range(F + 1, F + 5):
                g.S(x, y, z, SUBST)
    h = flat_hut(style)
    hp = (x1 + h[0], F + 1, z1 + h[2])
    g.S(*hp, HUT, hut_te(style, "fundamentals/skytowerflat0.blueprint", (0, 0, 0), hp, {}, child=True))
    regions.append((x1, F + 1, z1))


def ladder_core(g, x, z, y1, y2, facing):
    for y in range(y1, y2 + 1):
        g.S(x, y, z, f"ladder[facing={facing},waterlogged=false]")


# ------------------------------------------------------------------------------------------------ Hearthwood
def mansion(L):
    style = "Hearthwood"
    SX, SY, SZ = 27, 38, 19
    g = G(SX, SY, SZ, f"skytower{L}.blueprint")
    for x in range(SX):
        for z in range(SZ):
            g.S(x, 0, z, SOLID)
            g.S(x, 1, z, "stone_bricks" if (x + z) % 5 else "polished_andesite")
    tags = {(0, 1, 0): ["groundlevel"]}
    regions = []
    FH = 5
    x1, x2, z1, z2 = 2, 23, 3, 14
    floors = 5
    top = 1 + FH * floors
    for f in range(floors):
        F = 1 + FH * f
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                edge = x in (x1, x2) or z in (z1, z2)
                corner = x in (x1, x2) and z in (z1, z2)
                g.S(x, F, z, "white_terracotta" if edge else ("dark_oak_planks" if f else "stone_bricks"))
                for y in range(F + 1, F + FH):
                    if not edge:
                        g.S(x, y, z, "air")
                        continue
                    along = x - x1 if z in (z1, z2) else z - z1
                    if corner:
                        s = "stone_bricks"
                    elif y in (F + 2, F + 3) and along % 3 != 0:
                        s = "glass_pane"
                    else:
                        s = "bricks"
                    g.S(x, y, z, s)
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            g.S(x, top, z, "white_terracotta" if x in (x1, x2) or z in (z1, z2) else "dark_oak_planks")
    # inner wall between the flats (x3..16) and the stair core (x18..22)
    for f in range(floors):
        F = 1 + FH * f
        for z in range(z1 + 1, z2):
            for y in range(F + 1, F + FH):
                g.S(17, y, z, "bricks" if f else "air")
    ladder_core(g, 22 - 1, z2 - 1, 2, top, "north")
    for f in range(1, floors):
        F = 1 + FH * f
        place_flat(g, style, 3, F, 4, regions)
        g.S(17, F + 1, 8, "dark_oak_door[facing=west,half=lower,hinge=left,open=false,powered=false]")
        g.S(17, F + 2, 8, "dark_oak_door[facing=west,half=upper,hinge=left,open=false,powered=false]")
        g.S(20, F + 3, 8, "lantern[hanging=true,waterlogged=false]")
    # bay windows on the front, floors 1-4
    for f in range(1, floors):
        F = 1 + FH * f
        for bx in (5, 12):
            for x in range(bx, bx + 3):
                g.S(x, F, z1 - 1, "bricks")
                for y in (F + 1, F + 2, F + 3):
                    g.S(x, y, z1 - 1, "glass_pane")
                g.S(x, F + 4, z1 - 1, "dark_oak_slab[type=bottom,waterlogged=false]")
    # mansard roof with dormers
    for k in range(4):
        y = top + 1 + k
        for x in range(x1 + k, x2 + 1 - k):
            for z in range(z1 + k, z2 + 1 - k):
                ring = x in (x1 + k, x2 - k) or z in (z1 + k, z2 - k)
                if not ring:
                    continue
                if x == x1 + k:
                    f = "east"
                elif x == x2 - k:
                    f = "west"
                elif z == z1 + k:
                    f = "south"
                else:
                    f = "north"
                g.S(x, y, z, f"deepslate_tile_stairs[facing={f},half=bottom,shape=straight,waterlogged=false]" if L >= 4 else
                    f"dark_oak_stairs[facing={f},half=bottom,shape=straight,waterlogged=false]")
    g.box(x1 + 4, top + 5, z1 + 4, x2 - 4, top + 5, z2 - 4, "deepslate_tiles" if L >= 4 else "dark_oak_planks")
    for dx in (6, 12, 18):
        g.S(dx, top + 1, z1, "glass_pane")
        g.S(dx, top + 2, z1, "glass_pane")
        g.S(dx, top + 3, z1 + 1, "dark_oak_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]")
    for cx in (x1 + 2, x2 - 2):                                 # chimneys
        for y in range(top + 1, top + 8):
            g.S(cx, y, z2 - 2, "bricks")
        g.S(cx, top + 8, z2 - 2, "decorated_pot[cracked=false,facing=north,waterlogged=false]")
    # lobby: entrance, porter's beds, sitting room
    g.S(10, 2, z1, "dark_oak_door[facing=south,half=lower,hinge=left,open=false,powered=false]")
    g.S(10, 3, z1, "dark_oak_door[facing=south,half=upper,hinge=left,open=false,powered=false]")
    for i in range(L):
        g.bed(3 + 2 * i, 2, z2 - 1, "north", BED[style])
    for x in (6, 8):
        g.S(x, 2, 7, "dark_oak_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]")
        tags[(x, 2, 7)] = ["sit"]
    g.S(7, 2, 8, "dark_oak_slab[type=top,waterlogged=false]")
    g.S(3, 2, 4, "barrel[facing=up,open=false]")
    g.S(4, 2, 4, "crafting_table")
    g.S(10, 5, 9, "lantern[hanging=true,waterlogged=false]")
    hut = (15, 2, 4)
    connect_panes(g.bp)
    path = f"fundamentals/skytower{L}.blueprint"
    g.S(*hut, HUT, hut_te(style, path, (SX, SY, SZ), hut, tags))
    g.bp.primary_offset = hut
    g.bp.architects = [style]
    g.bp.regions = regions
    return g.bp


# ------------------------------------------------------------------------------------------------ Cascadia
def terrace(L):
    style = "Cascadia"
    SX, SY, SZ = 23, 40, 21
    g = G(SX, SY, SZ, f"skytower{L}.blueprint")
    for x in range(SX):
        for z in range(SZ):
            g.S(x, 0, z, SOLID)
            g.S(x, 1, z, "coarse_dirt" if (x * 3 + z) % 4 else "cobblestone")
    tags = {(0, 1, 0): ["groundlevel"]}
    regions = []
    FH = 5
    x1, x2, zb = 2, 20, 18
    tiers = 5
    for f in range(tiers):
        F = 1 + FH * f
        zf = 2 + 2 * f
        for x in range(x1, x2 + 1):
            for z in range(zf, zb + 1):
                edge = x in (x1, x2) or z in (zf, zb)
                corner = x in (x1, x2) and z in (zf, zb)
                g.S(x, F, z, ("spruce_planks" if f else "cobblestone") if not edge else ("cobblestone" if f == 0 else "stripped_spruce_log[axis=x]"))
                for y in range(F + 1, F + FH):
                    if not edge:
                        g.S(x, y, z, "air")
                        continue
                    along = x - x1 if z in (zf, zb) else z - zf
                    if corner or along % 4 == 0:
                        s = "spruce_log[axis=y]"
                    elif y == F + 2 and along % 2 == 1:
                        s = "glass"
                    else:
                        s = "cobblestone" if f == 0 else "mangrove_planks"
                    g.S(x, y, z, s)
        if f >= 1:                                              # deck on the roof of the tier below, with railing
            for x in range(x1, x2 + 1):
                for z in (zf - 2, zf - 1):
                    g.S(x, F, z, "spruce_planks")
                g.S(x, F + 1, zf - 2, "spruce_fence")
    top = 1 + FH * tiers
    ztop = 2 + 2 * (tiers - 1)
    # ladder core at the back east corner
    ladder_core(g, 19, 17, 2, top - FH, "north")
    for f in range(1, tiers):
        F = 1 + FH * f
        zf = 2 + 2 * f
        sx, sz = FLAT[style]
        place_flat(g, style, 3, F, zf + 1, regions)
        for z in range(zf + 1, zb):                              # inner wall between flat and core
            for y in range(F + 1, F + FH):
                g.S(14, y, z, "mangrove_planks")
        dz = zf + 1 + DOOR[style][1]
        g.S(14, F + 1, dz, "spruce_door[facing=west,half=lower,hinge=left,open=false,powered=false]")
        g.S(14, F + 2, dz, "spruce_door[facing=west,half=upper,hinge=left,open=false,powered=false]")
        g.S(17, F + 3, 15, "lantern[hanging=true,waterlogged=false]")
    # steep gable roof with a mossy ridge on the top tier
    a, b, k = x1 - 1, x2 + 1, 0
    while a < b:
        for z in range(ztop - 1, zb + 2):
            g.S(a, top + k, z, "spruce_stairs[facing=east,half=bottom,shape=straight,waterlogged=false]")
            g.S(b, top + k, z, "spruce_stairs[facing=west,half=bottom,shape=straight,waterlogged=false]")
        for x in range(a + 1, b):
            g.S(x, top + k, ztop, "mangrove_planks")
            g.S(x, top + k, zb, "mangrove_planks")
        a, b, k = a + 1, b - 1, k + 1
    for z in range(ztop - 1, zb + 2):
        g.S(a, top + k, z, "moss_block")
    g.S(19, top - FH + 1, 17, "air")
    # lobby
    g.S(11, 2, 2, "spruce_door[facing=south,half=lower,hinge=left,open=false,powered=false]")
    g.S(11, 3, 2, "spruce_door[facing=south,half=upper,hinge=left,open=false,powered=false]")
    for i in range(L):
        g.bed(3 + 2 * i, 2, zb - 1, "north", BED[style])
    for x in (6, 8):
        g.S(x, 2, 6, "spruce_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]")
        tags[(x, 2, 6)] = ["sit"]
    g.S(7, 2, 7, "spruce_slab[type=top,waterlogged=false]")
    g.S(3, 2, 3, "barrel[facing=up,open=false]")
    g.S(4, 2, 3, "crafting_table")
    for x in range(5, 18, 6):
        g.S(x, 4, 10, "lantern[hanging=true,waterlogged=false]")
    for z in range(4, 15, 3):                                   # firewood under the eaves
        g.S(x2 + 1, 2, z, "spruce_log[axis=x]")
    hut = (16, 2, 4)
    connect_panes(g.bp)
    path = f"fundamentals/skytower{L}.blueprint"
    g.S(*hut, HUT, hut_te(style, path, (SX, SY, SZ), hut, tags))
    g.bp.primary_offset = hut
    g.bp.architects = [style]
    g.bp.regions = regions
    return g.bp


BUILD = {"Hearthwood": mansion, "Cascadia": terrace}


def assemble(style, bp, L):
    f = build_flat(style, L)
    for x1, y1, z1 in bp.regions:
        for y in range(f.sy):
            for z in range(f.sz):
                for x in range(f.sx):
                    bp.set(x1 + x, y1 + y, z1 + z, f.get(x, y, z))
    return bp


def build_all(root: Path, style: str):
    d = root / "fundamentals"
    d.mkdir(parents=True, exist_ok=True)
    for L in range(1, 6):
        BUILD[style](L).save(d / f"skytower{L}.blueprint")
        build_flat(style, L).save(d / f"skytowerflat{L}.blueprint")
    print(f"{style}: own sky tower + flats x 5 levels")


if __name__ == "__main__":
    build_all(Path(sys.argv[1]), sys.argv[2])
