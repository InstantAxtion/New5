"""
Pack-specific military buildings – a different real-world version per pack.

  Neoterra    modern security compound: concrete wall with steel fence and light pylons, painted parade ground,
              flat-roofed barracks block; square concrete watch towers with glass bands and antennas; checkpoint
              gatehouse with concrete booths and a glass skybridge; square tower with a glass observation deck
  Hearthwood  stone castle: crenellated curtain wall, timber-framed great hall, ROUND corner towers with conical
              roofs (castle gatehouse and round bastion from military_real)
  Cascadia    frontier stockade: pointed log palisade, log barracks cabin with porch, overhanging blockhouses;
              stockade gate with log watch platforms and a timber bridge; river-rock tower with a timber lookout

Requirements kept per building: hut, child keeps (one more per level, 4 bunks per level), gatehouse footprint
18 x 9 with gate / knight / archer tags at the usual places, wall guard tower bunks, racks and barrel.

usage: python military_styles.py <pack dir> <style>
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import rack_te  # noqa: E402
from twinbuilder import hut_te, SOLID, SUBST  # noqa: E402
import military_real as MR  # noqa: E402
from military_real import B, RACK  # noqa: E402

KEEP = {"Neoterra": 7, "Hearthwood": 9, "Cascadia": 9}
PLOT = {"Neoterra": (33, 29), "Hearthwood": (27, 27), "Cascadia": (31, 25)}
KEEP_FH = {"Neoterra": 5, "Hearthwood": 4, "Cascadia": 4}


def corners(style):
    sx, sz = PLOT[style]
    k = KEEP[style]
    return [(0, 0), (sx - k, 0), (0, sz - k), (sx - k, sz - k)]


def keep_height(style, L):
    fh = KEEP_FH[style]
    return 1 + fh * (L + 1) + (12 if style == "Cascadia" else 9)


# ================================================================================================ barracks
def barracks(style, L):
    SX, SZ = PLOT[style]
    k = KEEP[style]
    SY = keep_height(style, 5) + 2
    b = B(style, L, SX, SY, SZ, f"barracks{L}.blueprint")
    m = b.k
    neo, casc = style == "Neoterra", style == "Cascadia"
    ground = {"Neoterra": "smooth_stone", "Hearthwood": "gravel", "Cascadia": "coarse_dirt"}[style]
    for x in range(SX):
        for z in range(SZ):
            b.S(x, 0, z, SOLID)
            b.S(x, 1, z, ground if 0 < x < SX - 1 and 0 < z < SZ - 1 else m["wall"])
    if neo:                                                 # painted parade ground lines
        for x in range(k + 2, SX - k - 2):
            b.S(x, 1, k + 2, "white_concrete")
            b.S(x, 1, SZ // 2, "yellow_concrete")
    # ---- perimeter
    gx = SX // 2
    for x in range(SX):
        for z in range(SZ):
            if not (x in (0, SX - 1) or z in (0, SZ - 1)):
                continue
            if z == 0 and abs(x - gx) <= (2 if neo else 1):
                continue
            if neo:
                for y in (2, 3):
                    b.S(x, y, z, "light_gray_concrete")
                for y in (4, 5):
                    b.S(x, y, z, "iron_bars")
                if (x + z) % 6 == 0:
                    for y in range(2, 7):
                        b.S(x, y, z, "white_concrete")
                    b.S(x, 7, z, "sea_lantern")
            elif casc:
                for y in range(2, 7):
                    b.S(x, y, z, "spruce_log[axis=y]" if (x + z) % 2 else "stripped_spruce_log[axis=y]")
                b.S(x, 7, z, "spruce_fence")
            else:
                for y in range(2, 7):
                    b.S(x, y, z, m["wall"] if (x + y + z) % 5 else m["wall2"])
    if style == "Hearthwood":
        b.crenels(0, 0, SX - 1, SZ - 1, 7, m["wall"])
    # gate furniture
    if neo:
        for x in (gx - 3, gx + 3):
            for y in range(2, 6):
                b.S(x, y, 0, "yellow_concrete" if y % 2 else "black_concrete")
    elif casc:
        for x in (gx - 2, gx + 2):
            for y in range(2, 9):
                b.S(x, y, 0, "spruce_log[axis=y]")
        for x in range(gx - 2, gx + 3):
            b.S(x, 9, 0, "spruce_log[axis=x]")
    else:
        for x in range(gx - 1, gx + 2):
            b.S(x, 5, 0, m["trim"])
            for y in (2, 3, 4):
                b.S(x, y, 0, "air")
    # ---- hall
    hx1, hx2 = k + 1, SX - k - 2
    hz2 = SZ - 2
    hz1 = hz2 - (9 if neo else 8 if casc else 8)
    floors = 1 if L <= 2 else 2
    fh = KEEP_FH[style]
    top = 1 + fh * floors
    for x in range(hx1, hx2 + 1):
        for z in range(hz1, hz2 + 1):
            b.S(x, 1, z, m["floor"])
            edge = x in (hx1, hx2) or z in (hz1, hz2)
            for y in range(2, top + 1):
                if not edge:
                    b.S(x, y, z, "air")
                    continue
                corner = x in (hx1, hx2) and z in (hz1, hz2)
                along = x - hx1 if z in (hz1, hz2) else z - hz1
                if neo:
                    s = "white_concrete" if corner else ("light_blue_stained_glass_pane" if (y - 2) % fh in (1, 2) else "light_gray_concrete")
                elif casc:
                    s = "spruce_log[axis=y]" if corner else (
                        "glass" if (y - 2) % fh == 1 and along % 3 == 1 else ("stripped_spruce_log[axis=x]" if z in (hz1, hz2) else "stripped_spruce_log[axis=z]"))
                else:
                    s = m["timber"] if corner or along % 4 == 0 else (m["glass"] if (y - 2) % 5 in (1, 2) and along % 2 == 0 else m["wall"] if y <= 3 else m["wall2"])
                b.S(x, y, z, s)
        if floors == 2:
            for z in range(hz1 + 1, hz2):
                if hx1 < x < hx2:
                    b.S(x, 1 + fh, z, m["floor"])
    if floors == 2:
        b.ladder(hx1 + 1, hz2 - 1, 2, 1 + fh, "east")
    if neo:
        b.ring(hx1, hz1, hx2, hz2, top + 1, top + 1, "white_concrete")
        for y in range(top + 1, top + 7):
            b.S(hx2 - 1, y, hz2 - 1, "iron_bars")
        b.S(hx2 - 1, top + 7, hz2 - 1, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    elif casc:
        b.gable_x(hx1, hx2, hz1, hz2, top + 1, "spruce", "stripped_spruce_log[axis=z]")
        for x in range(hx1, hx2 + 1):                       # porch with log posts along the front
            for z in (hz1 - 1, hz1 - 2):
                b.S(x, 1, z, "spruce_planks")
                b.S(x, 5, z, "spruce_slab[type=bottom,waterlogged=false]")
            if (x - hx1) % 3 == 0:
                for y in range(2, 5):
                    b.S(x, y, hz1 - 2, "stripped_spruce_log[axis=y]")
    else:
        b.gable_x(hx1, hx2, hz1, hz2, top + 1, m["roof"], m["wall"])
    door_x = (hx1 + hx2) // 2
    b.door(door_x, hz1, "south", wood=m["wood"])
    # armoury
    b.S(hx1 + 2, 2, hz2 - 1, "anvil[facing=north]")
    if L >= 3:
        b.S(hx1 + 4, 2, hz2 - 1, "smithing_table")
    b.S(hx2 - 2, 2, hz2 - 1, "barrel[facing=up,open=false]")
    b.S(hx2 - 3, 2, hz2 - 1, "barrel[facing=up,open=false]")
    hut = (hx2 - 4, 2, hz2 - 1)
    for x in range(hx1 + 2, hx2 - 1, 4):
        b.S(x, top - 1 if floors == 1 else fh, hz1 + 4, "lantern[hanging=true,waterlogged=false]" if not neo else "sea_lantern")
    # parade ground: flag + training
    fz = (k + hz1) // 2
    pole = "iron_bars" if neo else ("spruce_log[axis=y]" if casc else f"{m['wood']}_fence")
    for y in range(2, 10 + L):
        b.S(gx, y, fz, pole)
    for dx in (1, 2, 3):
        for dy in (0, 1):
            b.S(gx + dx, 8 + L + dy, fz, m["accent"] if (dx + dy) % 2 else "white_wool")
    for i in range(min(L + 1, 5)):
        x = k + 2 + i * 3
        if neo:
            b.S(x, 2, k + 1, "target[power=0]")
        elif casc:
            b.S(x, 2, k + 1, "spruce_log[axis=y]")
            b.S(x, 3, k + 1, "target[power=0]")
        else:
            b.S(x, 2, k + 1, "hay_block[axis=y]")
            b.S(x, 3, k + 1, "target[power=0]")
    # ---- keeps (child huts)
    n = min(L, 4)
    path = "military/barrackstower0.blueprint"
    for i, (rx, rz) in enumerate(corners(style)):
        if i < n:
            for y in range(1, SY):
                for x in range(rx, rx + k):
                    for z in range(rz, rz + k):
                        b.S(x, y, z, SUBST)
            th = (rx + k // 2, 2, rz + k // 2)
            b.S(*th, "minecolonies:blockhutbarrackstower[facing=north]", hut_te(style, path, (0, 0, 0), th, {}, child=True))
    return b.finish_hut("minecolonies:blockhutbarracks[facing=north]", hut, f"military/barracks{L}.blueprint")


def keep(style, L):
    k = KEEP[style]
    fh = KEEP_FH[style]
    SY = keep_height(style, 5) + 1
    b = B(style, L, k, SY, k, f"barrackstower{L}.blueprint")
    m = b.k
    c = k // 2
    floors = L + 1
    if style == "Hearthwood":
        def inside(x, z, r):
            return math.hypot(x - c, z - c) <= r
        R = c + 0.3
    else:
        def inside(x, z, r):
            return abs(x - c) <= r and abs(z - c) <= r
        R = c
    if style == "Cascadia":                                 # paved apron under the overhang
        for x in range(k):
            for z in range(k):
                b.S(x, 0, z, "cobblestone")
    for f in range(floors):
        y0 = fh * f
        inset = 1 if (style == "Cascadia" and f == 0) else 0      # blockhouse: narrower ground storey
        for x in range(k):
            for z in range(k):
                if not inside(x, z, R - inset):
                    continue
                wall = not inside(x, z, R - inset - 1)
                b.S(x, y0, z, m["wall"] if wall else m["floor"])
                for y in range(y0 + 1, y0 + fh):
                    if not wall:
                        b.S(x, y, z, "air")
                        continue
                    if style == "Neoterra":
                        s = "light_blue_stained_glass_pane" if y == y0 + 2 and f > 0 else "light_gray_concrete"
                    elif style == "Cascadia":
                        s = ("cobblestone" if f == 0 else ("stripped_spruce_log[axis=x]" if z in (0, k - 1) else "stripped_spruce_log[axis=z]"))
                        if f > 0 and y == y0 + 2 and (x == c or z == c):
                            s = "glass"
                    else:
                        s = m["glass"] if y == y0 + 2 and f > 0 and (x == c or z == c) else m["wall"]
                    b.S(x, y, z, s)
        if f > 0:
            for (bx, bz, fc) in ((c - 2, c - 1, "north"), (c + 2, c - 1, "north"), (c - 2, c + 1, "south"), (c + 2, c + 1, "south")):
                b.bed(bx, y0 + 1, bz, fc)
    top = fh * floors
    for x in range(k):
        for z in range(k):
            if inside(x, z, R):
                b.S(x, top, z, m["floor"])
    lz = c + 2 if (k <= 7 or style == "Cascadia") else c + 3
    if style == "Cascadia":                                 # post to climb against through the overhanging floors
        for y in range(1, top + 1):
            if b.get(c, y, lz + 1) in ("minecraft:air",) or y >= fh:
                b.S(c, y, lz + 1, "spruce_log[axis=y]")
    b.ladder(c, lz, 1, top, "north")
    for (x, z, facing) in ((c, 0 + (1 if style == "Cascadia" else 0), "south"), (c, k - 1 - (1 if style == "Cascadia" else 0), "north"),
                           (0 + (1 if style == "Cascadia" else 0), c, "east"), (k - 1 - (1 if style == "Cascadia" else 0), c, "west")):
        if style == "Hearthwood" and not inside(x, z, R):
            continue
        b.S(x, 1, z, f"{m['wood']}_door[facing={facing},half=lower,hinge=left,open=false,powered=false]")
        b.S(x, 2, z, f"{m['wood']}_door[facing={facing},half=upper,hinge=left,open=false,powered=false]")
    if style == "Neoterra":
        for x in range(k):
            for z in range(k):
                if x in (0, k - 1) or z in (0, k - 1):
                    b.S(x, top + 1, z, "light_blue_stained_glass_pane")
        for y in range(top + 1, top + 6):
            b.S(1, y, 1, "iron_bars")
        b.S(1, top + 6, 1, "sea_lantern")
    elif style == "Cascadia":
        for x in range(k):
            for z in range(k):
                if x in (0, k - 1) or z in (0, k - 1):
                    b.S(x, top + 1, z, "spruce_fence")
        for x, z in ((0, 0), (0, k - 1), (k - 1, 0), (k - 1, k - 1)):
            for y in range(top + 1, top + 4):
                b.S(x, y, z, "spruce_log[axis=y]")
        b.cone(c, c, c + 1, top + 4, "spruce_planks")
    else:
        for x in range(k):
            for z in range(k):
                if inside(x, z, R) and not inside(x, z, R - 1):
                    b.S(x, top + 1, z, m["wall"])
        b.cone(c, c, c + 1, top + 2, "deepslate_tiles" if L == 5 else "dark_oak_planks")
    hut = (c, 1, c)
    b.tags = {}
    return b.finish_hut("minecolonies:blockhutbarrackstower[facing=north]", hut, f"military/barrackstower{L}.blueprint",
                        {hut: ["invisible"]})


# ================================================================================================ gatehouse (18 x 9)
def gatehouse(style, L):
    if style == "Hearthwood":
        return MR.gatehouse(style, L)
    neo = style == "Neoterra"
    SX, SY, SZ = 18, (16 if neo else 21), 9
    b = B(style, L, SX, SY, SZ, f"gatehouse{L}.blueprint", maxL=3)
    m = b.k
    for x in range(SX):
        for z in range(SZ):
            b.S(x, 0, z, SOLID)
            b.S(x, 1, z, "smooth_stone" if neo else "spruce_planks")
    z1, z2 = (1, 7) if neo else (2, 6)
    roof = 13 if neo else 12
    for tx1, tx2 in ((0, 5), (12, 17)):
        for y in range(2, roof + 1):
            for x in range(tx1, tx2 + 1):
                for z in range(z1, z2 + 1):
                    edge = x in (tx1, tx2) or z in (z1, z2)
                    if not edge:
                        b.S(x, y, z, "air")
                        continue
                    corner = x in (tx1, tx2) and z in (z1, z2)
                    if neo:
                        s = "white_concrete" if corner else ("light_blue_stained_glass_pane" if y >= 9 and y <= 11 else "light_gray_concrete")
                    else:
                        if y >= 9:                          # open timber platform: posts + railing
                            s = "spruce_log[axis=y]" if corner else ("spruce_fence" if y == 9 else "air")
                        else:
                            s = "spruce_log[axis=y]" if corner else ("stripped_spruce_log[axis=x]" if z in (z1, z2) else "stripped_spruce_log[axis=z]")
                    b.S(x, y, z, s)
        for x in range(tx1 + 1, tx2):
            for z in range(z1 + 1, z2):
                b.S(x, 8, z, m["floor"])
        if not neo:                                         # watch deck overhanging the log guardroom
            for x in range(tx1, tx2 + 1):
                for z in range(SZ):
                    b.S(x, 8, z, "spruce_planks")
                    for y in range(9, roof):
                        b.S(x, y, z, "air")
                    if (x in (tx1, tx2) or z in (0, SZ - 1)):
                        b.S(x, 9, z, "spruce_fence")
            for x, z in ((tx1, 0), (tx2, 0), (tx1, SZ - 1), (tx2, SZ - 1)):
                for y in range(2, roof):
                    b.S(x, y, z, "spruce_log[axis=y]")
        if neo:
            for x in range(tx1, tx2 + 1):
                for z in range(z1, z2 + 1):
                    b.S(x, roof, z, "white_concrete")
            b.S(tx1 + 2, roof + 1, z1 + 2, "sea_lantern")
        else:
            for x in range(tx1, tx2 + 1):
                for z in range(z1, z2 + 1):
                    if x in (tx1, tx2) or z in (z1, z2):
                        b.S(x, roof, z, "spruce_log[axis=y]" if x in (tx1, tx2) and z in (z1, z2) else "air")
            b.gable_z(tx1, tx2, 0, SZ - 1, roof, "spruce", "spruce_planks")
    # passage and bridge / gallery (floor y8 between x 6..11 so archers stand at (7,8,2) and (10,8,2))
    for x in range(6, 12):
        for z in range(SZ):
            for y in range(2, 8):
                b.S(x, y, z, "air" if 7 <= x <= 10 or not (z1 <= z <= z2) else ("light_gray_concrete" if neo else "spruce_log[axis=y]"))
            b.S(x, 8, z, m["floor"] if (neo and 1 <= z <= 7) or (not neo) else "air")
    for x in range(6, 12):
        if neo:
            for y in range(9, 12):
                b.S(x, y, 1, "light_blue_stained_glass_pane")
                b.S(x, y, 7, "light_blue_stained_glass_pane")
            b.S(x, 12, 1, "white_concrete")
            for z in range(1, 8):
                b.S(x, 12, z, "white_concrete")
        else:
            b.S(x, 9, 0, "spruce_fence")
            b.S(x, 9, SZ - 1, "spruce_fence")
    for x in (5, 12):
        for y in (9, 10):
            b.S(x, y, 4, "air")
    for x in range(7, 11):
        for y in range(2, 2 + (1, 2, 4)[L - 1]):
            b.S(x, y, 2, f"{m['wood']}_fence_gate[facing=south,in_wall=false,open=false,powered=false]" if L < 3 else
                "minecolonies:gate_iron[facing=south,half=lower,hinge=left,open=false,powered=false]")
    dz = 6 if neo else 5
    for x in (6, 11):                                       # doorway through the passage wall to each tower door
        for y in (2, 3):
            b.S(x, y, dz, "air")
    for x, facing in ((5, "west"), (12, "east")):
        b.S(x, 2, dz, f"{m['wood']}_door[facing={facing},half=lower,hinge=left,open=false,powered=false]")
        b.S(x, 3, dz, f"{m['wood']}_door[facing={facing},half=upper,hinge=left,open=false,powered=false]")
    lz = z2 - 1
    b.ladder(1, lz, 2, 8, "north")
    b.ladder(16, lz, 2, 8, "north")
    for tx in (1, 13):
        if neo:
            b.bed(tx, 9, z1 + 2, "north")
            b.bed(tx + 2, 9, z1 + 2, "north")
            b.bed(tx, 9, z2 - 2, "south")
            b.bed(tx + 2, 9, z2 - 2, "south")
        else:                                               # bunks out on the covered deck
            for bz in (2, 6):
                b.bed(tx, 9, bz, "east")
            b.bed(tx + 2, 9, 1, "south")
            b.bed(tx + 2, 9, 6, "south")
    b.S(2, 2, z1 + 1, "barrel[facing=up,open=false]")
    b.S(15, 2, z1 + 1, "barrel[facing=up,open=false]")
    if neo:
        for x in (6, 11):
            for y in range(2, 8):
                b.S(x, y, 0, "yellow_concrete" if y % 2 else "black_concrete")
    tags = {(x, 1, 2): ["gate"] for x in range(7, 11)}
    tags.update({(7, 1, 5): ["knight"], (10, 1, 5): ["knight"], (7, 8, 2): ["archer"], (10, 8, 2): ["archer"]})
    return b.finish_hut("minecolonies:blockhutgatehouse[facing=north]", (4, 2, 4), f"military/gatehouse{L}.blueprint", tags)


# ================================================================================================ wall guard tower
def wallguardtower(style, L):
    if style == "Hearthwood":
        return MR.wallguardtower(style, L)
    neo = style == "Neoterra"
    SX = SZ = 11 if neo else 13
    SY = 32
    b = B(style, L, SX, SY, SZ, f"wallguardtower{L}.blueprint")
    m = b.k
    for x in range(SX):
        for z in range(SZ):
            b.S(x, 0, z, SOLID)
            b.S(x, 1, z, "smooth_stone" if neo else "cobblestone")
    fh = 5 if neo else 4
    floors = 2 + (L >= 3) + (L >= 5)
    x1, x2 = (1, 9) if neo else (2, 10)
    z1, z2 = x1, x2
    for f in range(floors):
        y0 = 1 + fh * f
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                edge = x in (x1, x2) or z in (z1, z2)
                b.S(x, y0, z, m["wall"] if edge else m["floor"])
                for y in range(y0 + 1, y0 + fh):
                    if not edge:
                        b.S(x, y, z, "air")
                        continue
                    corner = x in (x1, x2) and z in (z1, z2)
                    if neo:
                        s = "white_concrete" if corner else ("light_blue_stained_glass_pane" if y == y0 + 2 and f > 0 else "light_gray_concrete")
                    else:
                        s = "mossy_cobblestone" if corner else ("glass" if y == y0 + 2 and f > 0 and (x == 6 or z == 6) else "cobblestone")
                    b.S(x, y, z, s)
    top = 1 + fh * floors
    if neo:                                                 # glass observation deck, cantilevered to the full plot
        for x in range(SX):
            for z in range(SZ):
                b.S(x, top, z, "smooth_stone")
                edge = x in (0, SX - 1) or z in (0, SZ - 1)
                for y in range(top + 1, top + 4):
                    b.S(x, y, z, ("white_concrete" if (x in (0, SX - 1) and z in (0, SZ - 1)) else "light_blue_stained_glass_pane") if edge else "air")
                b.S(x, top + 4, z, "white_concrete")
        for y in range(top + 5, top + 10):
            b.S(5, y, 5, "iron_bars")
        b.S(5, top + 10, 5, "sea_lantern")
    else:                                                   # timber lookout deck with railing and a pitched roof
        for x in range(SX):
            for z in range(SZ):
                b.S(x, top, z, "spruce_planks")
                if x in (0, SX - 1) or z in (0, SZ - 1):
                    b.S(x, top + 1, z, "spruce_fence")
        for x, z in ((0, 0), (0, SZ - 1), (SX - 1, 0), (SX - 1, SZ - 1)):
            for y in range(top + 1, top + 4):
                b.S(x, y, z, "spruce_log[axis=y]")
        b.gable_z(0, SX - 1, 0, SZ - 1, top + 4, "spruce", "spruce_planks")
    lx = x1 + 2
    b.ladder(lx, z2 - 1, 2, top, "north")
    dx = (x1 + x2) // 2
    b.S(dx, 2, z1, f"{m['wood']}_door[facing=south,half=lower,hinge=left,open=false,powered=false]")
    b.S(dx, 3, z1, f"{m['wood']}_door[facing=south,half=upper,hinge=left,open=false,powered=false]")
    racks = 1 + (L >= 3) + (L >= 5)
    for i, (x, z) in enumerate(((x2 - 1, z2 - 1), (x2 - 1, z2 - 2), (x2 - 1, z2 - 3))[:racks]):
        b.S(x, 2, z, RACK.format("west"), rack_te())
    b.S(x1 + 1, 2, z1 + 1, "barrel[facing=up,open=false]")
    y1 = 2 + fh
    cx = dx
    b.bed(cx - 2, y1, z1 + 2, "north")
    b.bed(cx + 2, y1, z1 + 2, "north")
    b.bed(cx - 2, y1, z2 - 3, "south")
    b.bed(cx + 2, y1, z2 - 3, "south")
    hut = (dx + 1, 2, (z1 + z2) // 2)
    return b.finish_hut("minecolonies:blockhutguardtower[facing=north]", hut, f"military/wallguardtower{L}.blueprint")


def build_all(root: Path, style: str):
    d = root / "military"
    d.mkdir(parents=True, exist_ok=True)
    for L in range(1, 6):
        barracks(style, L).save(d / f"barracks{L}.blueprint")
        keep(style, L).save(d / f"barrackstower{L}.blueprint")
        wallguardtower(style, L).save(d / f"wallguardtower{L}.blueprint")
    for L in range(1, 4):
        gatehouse(style, L).save(d / f"gatehouse{L}.blueprint")
    print(f"{style}: pack-specific barracks, keeps, gatehouse, wall guard tower")


if __name__ == "__main__":
    build_all(Path(sys.argv[1]), sys.argv[2])
