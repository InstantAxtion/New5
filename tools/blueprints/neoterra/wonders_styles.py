"""
Grand Projects – a different real-world monument per pack.

  Neoterra    modernist A-frame cathedral + concrete campaniles | cable-stayed bridge + glass lift towers |
              android guardian + light obelisks | concrete grain elevator + storage bins
  Hearthwood  (wonders.py) gothic brick church + bell towers | stone arch viaduct + pylons | knight statue + braziers |
              tithe barn + brick dovecotes (this module)
  Cascadia    stave church with stacked roofs + log bell houses | covered timber bridge over a creek + toll cabins |
              Paul Bunyan with his axe + axe stumps | log barn + corn cribs

Each wonder has two wing child huts (neoterra:blockhutwonderwing) so several builders can work at once.
"""
from __future__ import annotations

import math

from wonders import W, wing_bp, hut_te, SUBST, WING  # noqa: F401

NEO_GLASS = "light_blue_stained_glass"


def _neo(L):
    prem = L >= 4
    return dict(frame="quartz_block" if prem else "white_concrete", panel="light_gray_concrete", glass=NEO_GLASS,
                floor="smooth_quartz" if prem else "polished_andesite", light="sea_lantern", metal="iron_block",
                plaza="smooth_stone")


def _casc(L):
    prem = L == 5
    return dict(log="spruce_log[axis=y]", logx="stripped_spruce_log[axis=x]", logz="stripped_spruce_log[axis=z]",
                plank="spruce_planks", roof="spruce" if not prem else "mangrove", stone="cobblestone",
                stone2="mossy_cobblestone", floor="spruce_planks", plaza="coarse_dirt", glass="glass")


def _ground(w, mat):
    for x in range(w.sx):
        for z in range(w.sz):
            w.S(x, 0, z, "structurize:blocksolidsubstitution")
            w.S(x, 1, z, mat)


def _bed_free(w, x, y, z):
    return w.get(x, y, z) == "minecraft:air"


# ====================================================================================================== NEOTERRA
def neo_cathedral(style, L):
    SX, SY, SZ = 29, 44, 39
    w = W(style, L, SX, SY, SZ, f"cathedral{L}.blueprint")
    m = _neo(L)
    _ground(w, m["plaza"])
    cx, z1, z2 = 14, 8, 33
    Ht = (12, 18, 24, 28, 32)[L - 1]
    hw = 10
    for z in range(z1, z2 + 1):
        w.S(cx, 1, z, m["floor"])
        for x in range(cx - hw, cx + hw + 1):
            w.S(x, 1, z, m["floor"])
        rib = (z - z1) % 4 == 0 or z in (z1, z2)
        for y in range(2, Ht + 1):
            half = round(hw * (1 - (y - 2) / (Ht - 2)))
            for x in (cx - half, cx + half):
                w.S(x, y, z, m["frame"] if rib else m["glass"])
            if z in (z1, z2):                                  # gable ends: glass with concrete mullions
                for x in range(cx - half + 1, cx + half):
                    w.S(x, y, z, m["frame"] if (x - cx) % 4 == 0 else m["glass"])
            else:
                for x in range(cx - half + 1, cx + half):
                    w.S(x, y, z, "air")
    for x in range(cx - 1, cx + 2):                            # entrance
        for y in range(2, 6):
            w.S(x, y, z1, "air")
    for x in range(cx - 3, cx + 4):
        w.S(x, 6, z1 - 1, "smooth_quartz_slab[type=top,waterlogged=false]")
    for z in range(z1 + 4, z2 - 5, 2):                         # pews
        for x in list(range(cx - 6, cx - 1)) + list(range(cx + 2, cx + 7)):
            w.S(x, 2, z, "quartz_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]")
    w.box(cx - 3, 2, z2 - 4, cx + 3, 2, z2 - 2, "smooth_quartz")
    w.S(cx, 3, z2 - 2, "sea_lantern")
    for z in range(z1 + 3, z2, 5):
        w.S(cx, Ht - 2, z, "end_rod[facing=down]")
    if L >= 3:
        for y in range(Ht + 1, Ht + 3 + L):                    # cross of light on the ridge
            w.S(cx, y, z1 + 2, m["light"] if y == Ht + 2 else "end_rod[facing=up]")
    hut = (cx, 3, z2 - 3)
    path = "wonders/cathedralwing0.blueprint"
    w.wing(1, 1, 5, 5, (3, 2, 3), path)
    w.wing(23, 1, 27, 5, (25, 2, 3), path)
    return w.finish("neoterra:blockhutcathedral[facing=north]", hut, f"wonders/cathedral{L}.blueprint")


def neo_cathedral_wing(style, L):
    H = (8, 14, 20, 26, 32)[L - 1]
    size = (5, 42, 5)

    def draw(w):
        m = _neo(L)
        w.box(0, 0, 0, 4, 0, 4, m["floor"])
        for y in range(1, H + 1):
            for x in range(5):
                for z in range(5):
                    edge = x in (0, 4) or z in (0, 4)
                    corner = x in (0, 4) and z in (0, 4)
                    if not edge:
                        w.S(x, y, z, "air")
                    elif corner or y > H - 4:
                        w.S(x, y, z, m["frame"] if corner else "air")
                    else:
                        w.S(x, y, z, m["panel"] if (y // 2) % 2 else m["frame"])
        w.box(0, H + 1, 0, 4, H + 1, 4, m["frame"])
        w.S(2, H, 2, "bell[attachment=ceiling,facing=north,powered=false]")
        w.S(2, 1, 4, "air"); w.S(2, 2, 4, "air")
        for y in range(H + 2, H + 2 + min(L + 1, 5)):
            w.S(2, y, 2, "end_rod[facing=up]")
        w.S(2, 1, 0, "birch_door[facing=south,half=lower,hinge=left,open=false,powered=false]")
        w.S(2, 2, 0, "birch_door[facing=south,half=upper,hinge=left,open=false,powered=false]")

    return wing_bp(style, L, f"cathedralwing{L}.blueprint", size, (2, 1, 2), f"wonders/cathedralwing{L}.blueprint", draw)


def neo_bridge(style, L):
    SX, SY, SZ = 63, 40, 13
    w = W(style, L, SX, SY, SZ, f"grandbridge{L}.blueprint")
    m = _neo(L)
    _ground(w, m["plaza"])
    z1, z2, DY = 4, 8, 9
    for i in range(DY - 1):                                    # ramps
        for z in range(z1, z2 + 1):
            for y in range(2, 3 + i):
                w.S(7 + i, y, z, m["frame"] if y < 2 + i else "smooth_stone")
                w.S(55 - i, y, z, m["frame"] if y < 2 + i else "smooth_stone")
    for x in range(15, 48):
        for z in range(z1, z2 + 1):
            w.S(x, DY, z, "smooth_stone" if z not in (z1, z2) else m["frame"])
        for z in (z1, z2):
            w.S(x, DY + 1, z, "light_blue_stained_glass_pane")
    for px in range(15, 48, 8):                                # slim piers
        w.box(px, 2, 6, px, DY - 1, 6, m["frame"])
    # A-pylon in the middle with fanned stay cables
    px = 31
    PH = DY + 6 + 3 * L
    for y in range(2, PH + 1):
        t = (y - 2) / (PH - 2)
        off = round(4 * (1 - t))
        for z in (6 - max(1, off), 6 + max(1, off)):
            w.S(px, y, z, m["frame"])
    for y in range(PH - 1, PH + 2):
        for z in range(5, 8):
            w.S(px, y, z, m["frame"])
    w.S(px, PH + 2, 6, "sea_lantern")
    for k in range(1, 5):                                      # cables: stepped lines of iron bars to the deck edges
        reach = 4 * k
        top = PH - k
        for side in (-1, 1):
            for i in range(reach + 1):
                x = px + side * i
                y = top - round((top - (DY + 1)) * i / reach)
                if DY + 1 < y and w.get(x, y, 4) == "minecraft:air":
                    w.S(x, y, 4, "iron_bars")
                    w.S(x, y, 8, "iron_bars")
    hut = (px + 2, DY + 1, 6)
    path = "wonders/grandbridgewing0.blueprint"
    w.wing(1, 1, 3, 3, (2, 2, 2), path)
    w.wing(59, 1, 61, 3, (60, 2, 2), path)
    return w.finish("neoterra:blockhutgrandbridge[facing=north]", hut, f"wonders/grandbridge{L}.blueprint")


def neo_bridge_wing(style, L):
    """Slim glass lift shaft."""
    H = (8, 12, 16, 20, 24)[L - 1]
    size = (3, 39, 3)

    def draw(w):
        m = _neo(L)
        for y in range(0, H + 1):
            for x in range(3):
                for z in range(3):
                    corner = x in (0, 2) and z in (0, 2)
                    if y == 0 or y == H:
                        w.S(x, y, z, m["frame"])
                    elif (x, z) != (1, 1):
                        w.S(x, y, z, m["frame"] if corner else NEO_GLASS)
        for y in (1, 2):
            w.S(1, y, 2, "air")
        w.S(1, H + 1, 1, "sea_lantern")

    return wing_bp(style, L, f"grandbridgewing{L}.blueprint", size, (1, 1, 1), f"wonders/grandbridgewing{L}.blueprint", draw)


def neo_colossus(style, L):
    SX, SY, SZ = 23, 46, 25
    w = W(style, L, SX, SY, SZ, f"colossus{L}.blueprint")
    m = _neo(L)
    _ground(w, m["plaza"])
    # glass plinth hall
    x1, x2, z1, z2 = 6, 16, 8, 18
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            w.S(x, 1, z, m["floor"])
            edge = x in (x1, x2) or z in (z1, z2)
            corner = x in (x1, x2) and z in (z1, z2)
            for y in range(2, 7):
                w.S(x, y, z, (m["frame"] if corner or y == 6 else NEO_GLASS) if edge else "air")
            w.S(x, 7, z, m["frame"])
    w.S(11, 2, z1, "birch_door[facing=south,half=lower,hinge=left,open=false,powered=false]")
    w.S(11, 3, z1, "birch_door[facing=south,half=upper,hinge=left,open=false,powered=false]")
    hut = (11, 2, 16)
    body, dark = "white_concrete", "gray_concrete"
    if L >= 1:
        for fx in (9, 12):
            w.box(fx, 8, 12, fx + 1, 8, 15, dark)
    if L >= 2:
        for fx in (9, 12):
            w.box(fx, 9, 13, fx + 1, 17, 14, body)
            w.box(fx, 12, 13, fx + 1, 12, 14, "cyan_concrete")
        w.box(9, 18, 12, 13, 19, 15, dark)
    if L >= 3:
        w.box(9, 20, 12, 13, 26, 15, body)
        w.box(10, 23, 12, 12, 24, 12, "cyan_concrete")
    if L >= 4:
        w.box(7, 25, 13, 15, 27, 14, dark)                     # shoulders
        w.box(7, 19, 13, 7, 24, 14, body)                      # arms
        w.box(15, 20, 13, 15, 24, 14, body)
        w.box(10, 28, 12, 12, 31, 15, body)                    # helmet
        w.box(10, 30, 12, 12, 30, 12, "sea_lantern")           # visor
    if L >= 5:
        for y in range(10, 38):                                # spear
            w.S(16, y, 13, "end_rod[facing=up]" if y > 34 else "iron_bars")
        w.S(16, 38, 13, "sea_lantern")
        w.box(10, 32, 13, 12, 33, 14, "cyan_concrete")
    path = "wonders/colossuswing0.blueprint"
    w.wing(1, 1, 3, 3, (2, 2, 2), path)
    w.wing(19, 1, 21, 3, (20, 2, 2), path)
    return w.finish("neoterra:blockhutcolossus[facing=north]", hut, f"wonders/colossus{L}.blueprint")


def neo_colossus_wing(style, L):
    H = (4, 7, 10, 13, 16)[L - 1]
    size = (3, 45, 3)

    def draw(w):
        m = _neo(L)
        for y in range(0, H + 1):
            for x in range(3):
                for z in range(3):
                    if (x, z) != (1, 1) or y == 0:
                        w.S(x, y, z, m["frame"] if y % 3 else "cyan_concrete")
        w.S(1, 1, 1, "air"); w.S(1, 2, 1, "air")
        w.S(1, 1, 2, "air"); w.S(1, 2, 2, "air")
        w.S(1, H + 1, 1, "sea_lantern")
        w.S(1, H + 2, 1, "end_rod[facing=up]")

    return wing_bp(style, L, f"colossuswing{L}.blueprint", size, (1, 1, 1), f"wonders/colossuswing{L}.blueprint", draw)


def neo_granary(style, L):
    SX, SY, SZ = 33, 44, 21
    w = W(style, L, SX, SY, SZ, f"royalgranary{L}.blueprint")
    m = _neo(L)
    _ground(w, m["plaza"])
    H = (10, 16, 22, 27, 32)[L - 1]
    sil = [(10, 13), (16, 13), (22, 13)]
    for cx, cz in sil:
        for y in range(2, H + 1):
            for x in range(cx - 3, cx + 4):
                for z in range(cz - 3, cz + 4):
                    d = math.hypot(x - cx, z - cz)
                    if 2.4 < d <= 3.3:
                        w.S(x, y, z, m["frame"] if y % 5 else m["panel"])
    for x in range(7, 26):                                     # head house gallery on top
        for z in range(11, 16):
            w.S(x, H + 1, z, m["panel"])
            for y in range(H + 2, H + 5):
                edge = x in (7, 25) or z in (11, 15)
                w.S(x, y, z, (NEO_GLASS if y == H + 3 else m["frame"]) if edge else "air")
            w.S(x, H + 5, z, m["frame"])
    # control building in front (the hut)
    for x in range(12, 21):
        for z in range(3, 9):
            w.S(x, 1, z, m["floor"])
            edge = x in (12, 20) or z in (3, 8)
            for y in range(2, 6):
                w.S(x, y, z, ((NEO_GLASS if y in (3, 4) else m["frame"]) if edge else "air"))
            w.S(x, 6, z, m["frame"])
    w.S(16, 2, 3, "birch_door[facing=south,half=lower,hinge=left,open=false,powered=false]")
    w.S(16, 3, 3, "birch_door[facing=south,half=upper,hinge=left,open=false,powered=false]")
    if L >= 3:                                                 # conveyor up to the head house
        for y in range(7, H + 1):
            w.S(26, y, 13, "iron_bars")
    hut = (16, 2, 7)
    path = "wonders/royalgranarywing0.blueprint"
    w.wing(0, 9, 4, 17, (2, 2, 13), path)
    w.wing(28, 9, 32, 17, (30, 2, 13), path)
    return w.finish("neoterra:blockhutroyalgranary[facing=north]", hut, f"wonders/royalgranary{L}.blueprint")


def neo_granary_wing(style, L):
    H = (4, 6, 8, 10, 12)[L - 1]
    size = (5, 43, 9)

    def draw(w):
        m = _neo(L)
        for x in range(5):
            for z in range(9):
                w.S(x, 0, z, m["floor"])
                edge = x in (0, 4) or z in (0, 8)
                for y in range(1, H + 1):
                    w.S(x, y, z, (m["panel"] if (y + z) % 4 else m["frame"]) if edge else "air")
                w.S(x, H + 1, z, m["frame"])
        w.S(2, 1, 0, "birch_door[facing=south,half=lower,hinge=left,open=false,powered=false]")
        w.S(2, 2, 0, "birch_door[facing=south,half=upper,hinge=left,open=false,powered=false]")
        for y in range(H + 2, H + 5):
            w.S(2, y, 4, "iron_bars")

    return wing_bp(style, L, f"royalgranarywing{L}.blueprint", size, (2, 1, 4), f"wonders/royalgranarywing{L}.blueprint", draw)


# ====================================================================================================== CASCADIA
def casc_cathedral(style, L):
    """Stave church: log hall wrapped in a low gallery, stacked steep roof tiers and a spire."""
    SX, SY, SZ = 25, 44, 31
    w = W(style, L, SX, SY, SZ, f"cathedral{L}.blueprint")
    m = _casc(L)
    _ground(w, m["plaza"])
    x1, x2, z1, z2 = 7, 17, 9, 25
    for x in range(x1 - 2, x2 + 3):                            # stone footing
        for z in range(z1 - 2, z2 + 3):
            w.S(x, 1, z, m["stone"] if (x + z) % 3 else m["stone2"])
    # gallery (svalgang): low arcade around the hall
    for x in range(x1 - 2, x2 + 3):
        for z in range(z1 - 2, z2 + 3):
            outer = x in (x1 - 2, x2 + 2) or z in (z1 - 2, z2 + 2)
            if outer and ((x + z) % 3 == 0):
                for y in range(2, 5):
                    w.S(x, y, z, m["log"])
            if outer or x in (x1 - 1, x2 + 1) or z in (z1 - 1, z2 + 1):
                w.S(x, 5, z, f"{m['roof']}_slab[type=bottom,waterlogged=false]")
    H = 6 + (L >= 2) * 3
    for y in range(2, H + 1):
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                edge = x in (x1, x2) or z in (z1, z2)
                corner = x in (x1, x2) and z in (z1, z2)
                if not edge:
                    w.S(x, y, z, "air")
                    continue
                w.S(x, y, z, m["log"] if corner else (m["logx"] if z in (z1, z2) else m["logz"]))
    for z in range(z1 + 3, z2 - 2, 4):
        for x in (x1, x2):
            w.S(x, 4, z, m["glass"])
    for x in range(x1 + 1, x2):
        for z in range(z1 + 1, z2):
            w.S(x, 1, z, m["floor"])
    for x in range(11, 14):
        for y in range(2, 5):
            w.S(x, y, z1, "air")
    w.S(12, 2, z1, "spruce_door[facing=south,half=lower,hinge=left,open=false,powered=false]")
    w.S(12, 3, z1, "spruce_door[facing=south,half=upper,hinge=left,open=false,powered=false]")
    w.S(11, 2, z1, m["log"]); w.S(11, 3, z1, m["log"]); w.S(13, 2, z1, m["log"]); w.S(13, 3, z1, m["log"])
    # roof tier 1
    top1 = w.gable_z(x1, x2, z1, z2, H + 1, m["roof"], m["plank"])
    if L >= 3:                                                 # tier 2: raised central box with its own roof
        bx1, bx2, bz1, bz2 = 10, 14, 13, 21
        b0 = top1 - 2
        for y in range(b0, b0 + 4):
            for x in range(bx1, bx2 + 1):
                for z in range(bz1, bz2 + 1):
                    if x in (bx1, bx2) or z in (bz1, bz2):
                        w.S(x, y, z, m["logz"] if x in (bx1, bx2) else m["logx"])
        top2 = w.gable_z(bx1, bx2, bz1, bz2, b0 + 4, m["roof"], m["plank"])
        if L >= 4:                                             # tier 3: belfry and spire
            for y in range(top2 - 1, top2 + 3):
                for x in (11, 13):
                    for z in (16, 18):
                        w.S(x, y, z, m["log"])
            w.S(12, top2 + 2, 17, "bell[attachment=ceiling,facing=north,powered=false]")
            for x in range(11, 14):
                for z in range(16, 19):
                    w.S(x, top2 + 3, z, m["plank"])
            for k in range(6 + L):
                w.S(12, top2 + 4 + k, 17, f"{m['roof']}_planks" if k < 4 + L else f"{m['roof']}_fence")
    for z in range(z1 + 3, z2 - 3, 2):                         # benches
        for x in list(range(x1 + 2, 11)) + list(range(14, x2 - 1)):
            w.S(x, 2, z, "spruce_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]")
    w.box(10, 2, z2 - 2, 14, 2, z2 - 2, m["plank"])
    for z in range(z1 + 3, z2, 5):
        w.S(12, H, z, "lantern[hanging=true,waterlogged=false]")
    hut = (12, 2, z2 - 3)
    path = "wonders/cathedralwing0.blueprint"
    w.wing(0, 2, 4, 6, (2, 2, 4), path)
    w.wing(20, 2, 24, 6, (22, 2, 4), path)
    return w.finish("neoterra:blockhutcathedral[facing=north]", hut, f"wonders/cathedral{L}.blueprint")


def casc_cathedral_wing(style, L):
    H = (4, 6, 8, 10, 12)[L - 1]
    size = (5, 43, 5)

    def draw(w):
        m = _casc(L)
        w.box(0, 0, 0, 4, 0, 4, m["stone"])
        for y in range(1, H + 1):
            for x, z in ((0, 0), (0, 4), (4, 0), (4, 4)):
                w.S(x, y, z, m["log"])
            if y <= 3:
                for x in range(1, 4):
                    w.S(x, y, 4, m["logx"])
                for z in range(1, 4):
                    w.S(0, y, z, m["logz"])
                    w.S(4, y, z, m["logz"])
        w.box(0, H + 1, 0, 4, H + 1, 4, m["plank"])
        w.S(2, H, 2, "bell[attachment=ceiling,facing=north,powered=false]")
        w.cone(2, 2, 3, H + 2, f"{m['roof']}_planks")

    return wing_bp(style, L, f"cathedralwing{L}.blueprint", size, (2, 1, 2), f"wonders/cathedralwing{L}.blueprint", draw)


def casc_bridge(style, L):
    """Oregon-style covered bridge over a creek."""
    SX, SY, SZ = 53, 24, 15
    w = W(style, L, SX, SY, SZ, f"grandbridge{L}.blueprint")
    m = _casc(L)
    _ground(w, m["plaza"])
    for x in range(20, 33):                                    # creek bed with water under the span
        for z in range(SZ):
            w.S(x, 1, z, m["stone2"] if x in (20, 32) else "water[level=0]")
            w.S(x, 0, z, m["stone"])
    z1, z2 = 4, 10
    DY = 4
    for i in range(DY - 1):                                    # approach ramps
        for z in range(z1 + 1, z2):
            for y in range(2, 3 + i):
                w.S(5 + i, y, z, m["stone"] if y < 2 + i else m["plank"])
                w.S(47 - i, y, z, m["stone"] if y < 2 + i else m["plank"])
    for x in (8, 9, 43, 44):                                   # stone abutments
        for z in range(z1, z2 + 1):
            for y in range(2, DY):
                w.S(x, y, z, m["stone"])
    x1, x2 = 8, 44
    WH = DY + (3 if L == 1 else 5)
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            w.S(x, DY, z, m["plank"] if z not in (z1, z2) else m["logx"])
        if L >= 2:
            for y in range(DY + 1, WH + 1):
                for z in (z1, z2):
                    window = (x - x1) % 6 == 3 and y == DY + 3
                    w.S(x, y, z, "air" if window else ("spruce_log[axis=y]" if (x - x1) % 6 == 0 else m["plank"]))
        else:
            for z in (z1, z2):
                w.S(x, DY + 1, z, "spruce_fence")
    if L >= 2:
        w.gable_x(x1, x2, z1, z2, WH + 1, m["roof"], m["plank"])
        for z in range(z1 + 1, z2):                            # portals stay open
            for y in range(DY + 1, DY + 4):
                w.S(x1, y, z, "air")
                w.S(x2, y, z, "air")
    if L >= 4:                                                 # truss: diagonal braces on the outside
        for x in range(x1, x2 - 3, 6):
            for k in range(3):
                for z in (z1 - 1, z2 + 1):
                    w.S(x + k + 1, DY + 1 + k, z, "stripped_spruce_log[axis=x]")
    if L >= 5:
        for x in range(x1 + 3, x2 - 2, 6):
            w.S(x, WH, 7, "lantern[hanging=true,waterlogged=false]")
    hut = (26, DY + 1, 9)
    path = "wonders/grandbridgewing0.blueprint"
    w.wing(0, 0, 6, 4, (3, 2, 2), path)
    w.wing(46, 0, 52, 4, (49, 2, 2), path)
    return w.finish("neoterra:blockhutgrandbridge[facing=north]", hut, f"wonders/grandbridge{L}.blueprint")


def casc_bridge_wing(style, L):
    """Log toll cabin with a porch."""
    size = (7, 23, 5)

    def draw(w):
        m = _casc(L)
        w.box(0, 0, 0, 6, 0, 4, m["stone"])
        H = 3 + (L >= 3)
        for y in range(1, H + 1):
            for x in range(1, 7):
                for z in range(5):
                    edge = x in (1, 6) or z in (0, 4)
                    corner = x in (1, 6) and z in (0, 4)
                    w.S(x, y, z, (m["log"] if corner else (m["logx"] if z in (0, 4) else m["logz"])) if edge else "air")
        for z in (0, 4):                                       # porch posts on the open side
            for y in range(1, H + 1):
                w.S(0, y, z, m["log"])
        w.gable_z(0, 6, 0, 4, H + 1, m["roof"], m["plank"])
        w.S(1, 1, 2, "spruce_door[facing=west,half=lower,hinge=left,open=false,powered=false]")
        w.S(1, 2, 2, "spruce_door[facing=west,half=upper,hinge=left,open=false,powered=false]")
        w.S(6, 2, 2, m["glass"])

    return wing_bp(style, L, f"grandbridgewing{L}.blueprint", size, (3, 1, 2), f"wonders/grandbridgewing{L}.blueprint", draw)


def casc_colossus(style, L):
    """Paul Bunyan with his axe, on a river-rock base with a log cabin hall inside."""
    SX, SY, SZ = 25, 46, 25
    w = W(style, L, SX, SY, SZ, f"colossus{L}.blueprint")
    m = _casc(L)
    _ground(w, m["plaza"])
    x1, x2, z1, z2 = 6, 18, 9, 19
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            w.S(x, 1, z, m["floor"])
            edge = x in (x1, x2) or z in (z1, z2)
            for y in range(2, 7):
                w.S(x, y, z, (m["stone"] if (x + y + z) % 4 else m["stone2"]) if edge else "air")
            w.S(x, 7, z, m["stone"])
    w.S(12, 2, z1, "spruce_door[facing=south,half=lower,hinge=left,open=false,powered=false]")
    w.S(12, 3, z1, "spruce_door[facing=south,half=upper,hinge=left,open=false,powered=false]")
    hut = (12, 2, 17)
    plaid = lambda x, y: "red_wool" if (x + y) % 2 else "black_wool"   # noqa: E731
    if L >= 1:                                                 # boots
        for fx in (9, 14):
            w.box(fx, 8, 12, fx + 1, 9, 16, "black_wool")
    if L >= 2:                                                 # jeans
        for fx in (9, 14):
            w.box(fx, 10, 13, fx + 1, 17, 15, "blue_wool")
        w.box(9, 17, 13, 15, 18, 15, "blue_wool")
        w.box(9, 19, 13, 15, 19, 15, "brown_wool")             # belt
    if L >= 3:                                                 # plaid shirt
        for x in range(9, 16):
            for y in range(20, 27):
                for z in range(13, 16):
                    w.S(x, y, z, plaid(x, y))
    if L >= 4:
        for y in range(19, 27):                                # arms
            for x in (8, 16):
                for z in (13, 14):
                    w.S(x, y, z, plaid(x, y) if y > 21 else "orange_terracotta")
        w.box(11, 27, 13, 13, 27, 15, "orange_terracotta")     # neck
        w.box(10, 28, 12, 14, 32, 16, "orange_terracotta")     # head
        w.box(10, 28, 12, 14, 29, 12, "black_wool")            # beard
        w.box(10, 28, 12, 10, 30, 16, "black_wool")
        w.box(14, 28, 12, 14, 30, 16, "black_wool")
        w.S(11, 31, 12, "black_wool"); w.S(13, 31, 12, "black_wool")
        w.box(10, 33, 12, 14, 33, 16, "red_wool")              # toque
    if L >= 5:                                                 # the axe on his shoulder
        for k in range(10):
            w.S(17, 18 + k, 14, "stripped_spruce_log[axis=y]")
        w.box(17, 28, 12, 17, 30, 15, "iron_block")
        w.S(12, 34, 14, "red_wool")
    path = "wonders/colossuswing0.blueprint"
    w.wing(1, 1, 5, 5, (3, 2, 3), path)
    w.wing(19, 1, 23, 5, (21, 2, 3), path)
    return w.finish("neoterra:blockhutcolossus[facing=north]", hut, f"wonders/colossus{L}.blueprint")


def casc_colossus_wing(style, L):
    size = (5, 45, 5)

    def draw(w):
        m = _casc(L)
        H = (2, 3, 4, 5, 6)[L - 1]
        for y in range(0, H + 1):
            for x in range(5):
                for z in range(5):
                    d = math.hypot(x - 2, z - 2)
                    if d <= 2.4:
                        w.S(x, y, z, "spruce_log[axis=y]" if d > 1.4 or y == H else "stripped_spruce_wood[axis=y]")
        for y in (1, 2):
            w.S(2, y, 4, "air")
            w.S(2, y, 3, "air")
            w.S(2, y, 2, "air")
        for k in range(3):                                     # axe stuck in the stump
            w.S(2, H + 1 + k, 2, "stripped_spruce_log[axis=y]")
        w.S(1, H + 1, 2, "iron_block")
        w.S(1, H + 2, 2, "iron_block")

    return wing_bp(style, L, f"colossuswing{L}.blueprint", size, (2, 1, 2), f"wonders/colossuswing{L}.blueprint", draw)


def casc_granary(style, L):
    """Big log barn with a gambrel roof."""
    SX, SY, SZ = 39, 30, 25
    w = W(style, L, SX, SY, SZ, f"royalgranary{L}.blueprint")
    m = _casc(L)
    _ground(w, m["plaza"])
    x1, x2, z1, z2 = 7, 31, 7, 17
    H = (5, 6, 6, 7, 8)[L - 1]
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            w.S(x, 1, z, m["floor"])
            edge = x in (x1, x2) or z in (z1, z2)
            corner = x in (x1, x2) and z in (z1, z2)
            for y in range(2, H + 2):
                if not edge:
                    w.S(x, y, z, "air")
                    continue
                w.S(x, y, z, m["log"] if corner else (m["logx"] if z in (z1, z2) else m["logz"]))
    for x in range(18, 21):
        for y in range(2, 5):
            w.S(x, y, z1, "air")
    if L == 1:
        w.gable_x(x1, x2, z1, z2, H + 2, m["roof"], m["plank"])
    else:
        y = H + 2
        a, b = z1 - 1, z2 + 1
        for step in range(3):
            for x in range(x1 - 1, x2 + 2):
                w.S(x, y, a, f"{m['roof']}_planks")
                w.S(x, y, b, f"{m['roof']}_planks")
            for z in range(a + 1, b):
                w.S(x1, y, z, m["plank"])
                w.S(x2, y, z, m["plank"])
            y += 1
            if step < 2:
                a, b = a + 1, b - 1
        w.gable_x(x1, x2, a + 1, b - 1, y, m["roof"], m["plank"])
        w.S(19, H + 4, z1, "spruce_trapdoor[facing=north,half=bottom,open=true,powered=false,waterlogged=false]")
        if L >= 4:                                             # moss on the ridge
            for x in range(x1, x2 + 1, 2):
                w.S(x, y + 6, 12, "moss_block")
    for x in range(x1 + 2, x2 - 1):
        if x % 4:
            w.S(x, 2, z2 - 1, "hay_block[axis=x]")
    for z in range(z1 + 2, z2 - 1, 3):
        w.S(x1 + 1, 2, z, "barrel[facing=up,open=false]")
    for x in range(x1 + 3, x2 - 2, 6):
        w.S(x, H + 1, 12, "lantern[hanging=true,waterlogged=false]")
    for x in range(x1, x2 + 1, 2):                             # mossy sill along the front
        w.S(x, 1, z1 - 1, "mossy_cobblestone")
    hut = (19, 2, 10)
    path = "wonders/royalgranarywing0.blueprint"
    w.wing(0, 9, 4, 15, (2, 2, 12), path)
    w.wing(34, 9, 38, 15, (36, 2, 12), path)
    return w.finish("neoterra:blockhutroyalgranary[facing=north]", hut, f"wonders/royalgranary{L}.blueprint")


def casc_granary_wing(style, L):
    """Corn crib: slatted log crib on stone piers with a pitched roof."""
    size = (5, 29, 7)
    H = (3, 4, 5, 6, 7)[L - 1]

    def draw(w):
        m = _casc(L)
        for x in range(5):
            for z in range(7):
                w.S(x, 0, z, m["stone"] if x in (0, 4) and z in (0, 6) else m["plank"])
                edge = x in (0, 4) or z in (0, 6)
                corner = x in (0, 4) and z in (0, 6)
                for y in range(1, H + 1):
                    if not edge:
                        w.S(x, y, z, "air")
                    elif corner:
                        w.S(x, y, z, m["log"])
                    else:
                        w.S(x, y, z, "spruce_fence" if y % 2 else m["plank"])
        w.gable_z(0, 4, 0, 6, H + 1, m["roof"], m["plank"])
        w.S(2, 1, 0, "spruce_door[facing=south,half=lower,hinge=left,open=false,powered=false]")
        w.S(2, 2, 0, "spruce_door[facing=south,half=upper,hinge=left,open=false,powered=false]")
        for z in (4, 5):
            w.S(1, 1, z, "hay_block[axis=y]")

    return wing_bp(style, L, f"royalgranarywing{L}.blueprint", size, (2, 1, 3), f"wonders/royalgranarywing{L}.blueprint", draw)


# ====================================================================================================== HEARTHWOOD
def hearth_granary_wing(style, L):
    """Square brick dovecote with a pyramid roof and pigeon holes, on a paved 7 x 7 yard."""
    size = (7, 29, 7)
    H = (4, 6, 8, 9, 10)[L - 1]

    def draw(w):
        for x in range(7):
            for z in range(7):
                w.S(x, 0, z, "bricks" if x in (0, 6) or z in (0, 6) else "stone_bricks")
        for x in range(1, 6):
            for z in range(1, 6):
                edge = x in (1, 5) or z in (1, 5)
                for y in range(1, H + 1):
                    if not edge:
                        w.S(x, y, z, "air")
                    else:
                        hole = y >= H - 2 and (x == 3 or z == 3) and y % 2 == 0
                        w.S(x, y, z, "air" if hole else ("white_terracotta" if y == H - 3 else "bricks"))
        w.S(3, 1, 1, "dark_oak_door[facing=south,half=lower,hinge=left,open=false,powered=false]")
        w.S(3, 2, 1, "dark_oak_door[facing=south,half=upper,hinge=left,open=false,powered=false]")
        for k in range(3):
            for x in range(1 + k, 6 - k):
                for z in range(1 + k, 6 - k):
                    if x in (1 + k, 5 - k) or z in (1 + k, 5 - k) or k == 2:
                        w.S(x, H + 1 + k, z, "dark_oak_planks" if k == 2 else "deepslate_tiles")

    return wing_bp(style, L, f"royalgranarywing{L}.blueprint", size, (3, 1, 3), f"wonders/royalgranarywing{L}.blueprint", draw)


def wonder_set(style, base):
    if style == "Neoterra":
        return {"cathedral": (neo_cathedral, neo_cathedral_wing), "grandbridge": (neo_bridge, neo_bridge_wing),
                "colossus": (neo_colossus, neo_colossus_wing), "royalgranary": (neo_granary, neo_granary_wing)}
    if style == "Cascadia":
        return {"cathedral": (casc_cathedral, casc_cathedral_wing), "grandbridge": (casc_bridge, casc_bridge_wing),
                "colossus": (casc_colossus, casc_colossus_wing), "royalgranary": (casc_granary, casc_granary_wing)}
    out = dict(base)
    out["royalgranary"] = (base["royalgranary"][0], hearth_granary_wing)
    return out
