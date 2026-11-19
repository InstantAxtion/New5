"""
Neoterra signature buildings: every hut gets its own form (levels 1-5, cheap 1-3 / premium 4-5).

  fundamentals/cook                    Halo Bistro      round 2-storey dining drum, terrace ring,
                                                        rooftop bar, glass cupola
  fundamentals/lumberjack              Arbor Vault      long glass barrel-vault greenhouse, lab,
                                                        nursery, giant indoor tree
  craftsmanship/carpentry/sawmill      Timber Works     sawtooth-roof factory, log yard, silo
  craftsmanship/masonry/stonemason     Stepped Atelier  stone ziggurat, terraces, crown sculpture
  craftsmanship/metallurgy/mechanic    Gear Hub         octagonal tech hub, gear sculpture,
                                                        satellite pod + bridge, radar dish
  education/school                     Crescent School  crescent around a playground courtyard
  education/library                    Book Tower       round tower, one storey per level, dome
  military/archery                     Arrow Range      long range under arched canopies, round
                                                        bunk tower
  military/combatacademy               Colosseum        ring arena, tiered seats, gate block
  military/stable                      Equestrian Hall  barrel-vault riding hall + stall block

Gameplay counts follow the official packs: cook furnaces = level, school 10 seats + teacher spot,
library bookshelves 10/30/54/104/121, archery targets = level, beds 2/level for archery & combat
academy, combat dummies 1/2/3/6/9, stable stalls 2/level.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit import Kit, Shapes, SUBST, edge, put, rack, tree, planter, bed, in_octagon  # noqa: E402
from common import street_lamp  # noqa: E402


def stair_state(k, facing):
    return f"{k.st.SEAT}[facing={facing},half=bottom,shape=straight,waterlogged=false]"


def table(k, x, y, z, seats=("west", "east")):
    k.set(x, y, z, k.st.counter)
    for side in seats:
        dx, dz = {"west": (-1, 0), "east": (1, 0), "north": (0, -1), "south": (0, 1)}[side]
        k.seat(x + dx, y, z + dz, side)


# ============================================================================ Halo Bistro (cook)
def build_cook(L):
    k = Kit("cook", "fundamentals", L, (33, 26, 33))
    sh, bp = Shapes(k), k.bp
    C = 16
    k.ground(paved=[(15, 17, 0, 5)])
    sh.disc(C, C, 14, 1, lambda x, z: k.D if L >= 2 else "grass_block[snowy=false]", r_in=10.5)  # terrace ring
    sh.drum(C, C, 10, 1, 7, doors=(270,), glass_every=24)
    k.door(C, 2, C - 10, "south")
    # kitchen in the south part: counter line, furnaces (1 per level) on the back wall
    for x in range(10, 23):
        if x not in (15, 16, 17):
            k.set(x, 2, 20, k.st.counter)
    for i in range(L):
        bp.set(12 + 2 * i, 2, 24, "furnace[facing=north,lit=false]")
        k.tag((12 + 2 * i, 2, 23), "work")
    bp.set(21, 2, 23, "smoker[facing=west,lit=false]")
    bp.set(21, 2, 22, "crafting_table")
    rack(bp, 11, 2, 23, "east")
    k.tag((17, 2, 22), "work")
    # dining tables on a ring
    n = 3 + 2 * min(L, 3)
    for i in range(n):
        a = math.radians(200 + i * (140 / max(1, n - 1)))
        tx, tz = round(C + 6 * math.cos(a)), round(C + 6 * math.sin(a))
        if abs(tx - C) <= 1:
            continue
        table(k, tx, 2, tz, ("north", "south"))
    k.lights(C - 6, C + 6, C - 6, C + 4, 7, step=4)
    hut = (C + 3, 2, C - 8)
    if L >= 2:  # terrace tables under the drum's overhang
        sh.disc(C, C, 12, 7, lambda x, z: (k.glow or k.band) if math.hypot(x - C, z - C) >= 11.5 else k.D, r_in=10.5)
        for a in (210, 240, 300, 330):
            tx, tz = round(C + 12.5 * math.cos(math.radians(a))), round(C + 12.5 * math.sin(math.radians(a)))
            table(k, tx, 2, tz, ("west", "east"))
    if L >= 3:  # second dining floor (r8) + stairs
        sh.drum(C, C, 8, 7, 13, glass_every=20)
        k.stairs(C - 6, C - 2, 2, 6, "south", cut_y=7)
        for a in (30, 90, 150, 210, 330):
            tx, tz = round(C + 4.5 * math.cos(math.radians(a))), round(C + 4.5 * math.sin(math.radians(a)))
            table(k, tx, 8, tz, ("west", "east"))
        bp.set(C + 5, 8, C + 2, "jukebox[has_record=false]")
        k.lights(C - 4, C + 4, C - 4, C + 4, 13, step=4)
        sh.disc(C, C, 10, 8, lambda x, z: k.st.railing, r_in=9.5)              # railing on the lower roof
        k.opening(C - 8, 8, C, C - 8, 9, C)                               # door to the lower roof terrace
    if L >= 4:  # rooftop bar
        sh.disc(C, C, 8, 14, lambda x, z: k.st.railing, r_in=7.5)
        for y in range(8, 14):
            bp.set(C + 6, y, C + 3, "ladder[facing=west,waterlogged=false]")
        bp.set(C + 6, 13, C + 3, "ladder[facing=west,waterlogged=false]")
        for x in range(C - 3, C + 2):
            k.set(x, 14, C + 4, k.st.counter)
        for x in (C - 3, C - 1, C + 1):
            k.seat(x, 14, C + 5, "south")
    if L >= 5:  # glass cupola
        for x in range(C - 5, C + 6):
            for z in range(C - 5, C + 6):
                d = math.hypot(x - C, z - C)
                for y, (r1, r2) in ((14, (4.5, 5.5)), (15, (4.5, 5.5)), (16, (3.5, 4.5)), (17, (2, 3.5))):
                    if r1 <= d < r2 and not (abs(x - C - 6) <= 1):
                        bp.set(x, y, z, "sea_lantern" if (x + z) % 5 == 0 else "glass")
        bp.set(C, 18, C, "end_rod[facing=up]")
    k.landscape(trees=[(1, 1, 4), (31, 1, 4), (1, 31, 4), (31, 31, 4)], lamps=[(13, 1), (19, 1)])
    return k.finish_hut(hut, "blockhutcook")


# ============================================================================ Arbor Vault (forester)
def build_lumberjack(L):
    k = Kit("lumberjack", "fundamentals", L, (37, 18, 23))
    sh, bp = Shapes(k), k.bp
    k.ground(paved=[(0, 3, 9, 13)])
    x2 = [18, 26, 34, 34, 34][L - 1]
    sh.vault(3, x2, 3, 19, 5)
    # lab at the west end (inside the vault): floor + racks + work counter
    for x in range(4, x2):
        for z in range(4, 19):
            bp.set(x, 1, z, k.st.floor(x, z) if x < 11 else "grass_block[snowy=false]")
    for i in range(1 + L):
        rack(bp, 4 + i, 2, 18, "north")
    bp.set(10, 2, 18, "crafting_table")
    for z in (5, 6, 7):
        k.set(9, 2, z, k.st.counter)
    for z in (15, 16):
        bp.set(4, 2, z, "stripped_oak_log[axis=x]")
    hut = (5, 2, 6)
    # nursery rows of saplings
    saps = ["oak", "birch", "spruce", "jungle", "acacia", "cherry", "dark_oak"]
    i = 0
    for x in range(13, x2 - 1, 3):
        for z in (6, 10, 14, 17):
            if L >= 3 and abs(x - 26) <= 2 and abs(z - 11) <= 3:
                continue
            bp.set(x, 2, z, f"{saps[i % len(saps)]}_sapling[stage=0]")
            i += 1
    if L >= 3:  # giant indoor tree
        k.fill(26, 2, 11, 26, 9, 11, "stripped_oak_log[axis=y]")
        for x in range(22, 31):
            for z in range(7, 16):
                for y in range(8, 13):
                    d = math.sqrt((x - 26) ** 2 + (z - 11) ** 2 + ((y - 10) * 1.4) ** 2)
                    if d < 4.2 and bp.get(x, y, z) == "minecraft:air":
                        bp.set(x, y, z, "oak_leaves[distance=1,persistent=true,waterlogged=false]")
        for z in (8, 14):
            k.seat(24, 2, z, "west")
            k.tag((24, 2, z), "sit")
    if L >= 4:
        bp.set(9, 2, 9, "composter[level=0]")
        bp.set(9, 2, 10, "barrel[facing=west,open=false]")
    k.landscape(trees=[(1, 1, 4), (1, 21, 4), (35, 1, 4), (35, 21, 4)], lamps=[(0, 7), (0, 15)])
    return k.finish_hut(hut, "blockhutlumberjack")


# ============================================================================ Timber Works (sawmill)
def build_sawmill(L):
    k = Kit("sawmill", "craftsmanship/carpentry", L, (39, 22, 27))
    sh, bp = Shapes(k), k.bp
    k.ground(paved=[(2, 36, 18, 25), (17, 19, 0, 4)])
    x2 = [21, 33, 33, 33, 33][L - 1]
    wall = "spruce_planks" if k.st.early else "stripped_spruce_wood[axis=y]"
    k.box(2, x2, 5, 17, 1, 7, wall=wall, roof=False)
    for x in range(3, x2):
        for z in range(6, 17):
            bp.set(x, 7, z, "air")
    sh.sawtooth(2, x2, 5, 17, 7, tooth=4)
    k.opening(18, 2, 5, 18, 3, 5)
    k.door(18, 2, 5, "south")
    k.opening(10, 2, 17, 12, 4, 17)                                       # loading door to the yard
    # saw line + counters
    for x in range(4, 4 + min(2 + L, 7)):
        bp.set(x, 2, 9, "stonecutter[facing=north]")
        k.set(x, 2, 11, k.st.counter)
    for i in range(L):
        rack(bp, 14 + i, 2, 15, "north")
    bp.set(20, 2, 15, "crafting_table")
    hut = (19, 2, 7)
    k.lights(5, x2 - 2, 8, 14, 7, step=4)
    # log yard
    for x0 in range(3, 3 + 8 * min(L + 1, 4), 8):
        k.fill(x0, 2, 20, x0 + 5, 2 + min(L, 3) - 1, 22, "stripped_spruce_log[axis=x]")
    if L >= 3:  # silo
        for x in range(32, 38):
            for z in range(20, 26):
                d = math.hypot(x - 35, z - 23)
                if 1.5 <= d < 2.5:
                    for y in range(2, 15):
                        bp.set(x, y, z, k.AC if y % 4 == 0 else k.W)
                elif d < 1.5:
                    bp.set(x, 15, z, k.W)
        k.mast(35, 15, 23)
        # office mezzanine inside the hall (floor y4, clear of the sawtooth roof)
        for x in range(22, x2):
            for z in range(6, 11):
                bp.set(x, 4, z, k.D)
        for x in range(23, x2):
            put(bp, x, 5, 11, k.st.railing)
        k.stairs(22, 13, 2, 3, "north", cut_y=None)                         # up to the mezzanine
        bp.set(30, 5, 7, "lectern[facing=south,has_book=false,powered=false]")
        bp.set(31, 5, 7, "cartography_table")
    if L >= 4:
        bp.set(26, 2, 15, "domum_ornamentum:architectscutter[facing=north]")
    k.landscape(trees=[(1, 1, 3), (37, 1, 3)], lamps=[(15, 1), (21, 1)])
    return k.finish_hut(hut, "blockhutsawmill")


# ============================================================================ Stepped Atelier (stonemason)
def build_stonemason(L):
    k = Kit("stonemason", "craftsmanship/masonry", L, (33, 26, 33))
    bp = k.bp
    k.ground(paved=[(15, 17, 0, 3)])
    bands = (["smooth_stone", "polished_andesite", "stone_bricks"] if k.st.early
             else ["calcite", "polished_diorite", "smooth_quartz"])
    tiers = [(2, 30, 1, 6), (6, 26, 6, 11), (10, 22, 11, 16), (13, 19, 16, 20)]
    for t, (a, b, fy, ty) in enumerate(tiers[: min(L + 1, 4) if L >= 2 else 1]):
        for x in range(a, b + 1):
            for z in range(a, b + 1):
                e = edge(x, z, a, b, a, b)
                if not e:
                    bp.set(x, fy, z, k.st.floor(x, z))
                    bp.set(x, ty, z, k.D if not k.st.early else "smooth_stone")
                    continue
                bp.set(x, ty, z, k.band)
                for y in range(fy + 1, ty):
                    window = y in (fy + 2, fy + 3) and (x + z) % 4 == 1
                    bp.set(x, y, z, k.G if window else bands[(y + t) % 3])
        # terrace railing on this tier's roof (outside the next tier)
        for x in range(a, b + 1):
            for z in range(a, b + 1):
                if edge(x, z, a, b, a, b):
                    put(bp, x, ty + 1, z, k.st.railing)
    k.opening(16, 2, 2, 16, 3, 2)
    k.door(16, 2, 2, "south")
    # workshop on the base tier
    for x in range(5, 5 + min(L + 2, 7)):
        bp.set(x, 2, 6, "stonecutter[facing=south]")
    for i in range(L + 1):
        rack(bp, 5 + i, 2, 28, "north")
    bp.set(27, 2, 28, "crafting_table")
    stones = ["smooth_stone", "polished_andesite", "polished_diorite", "polished_granite", "stone_bricks",
              "bricks", "calcite", "polished_tuff"]
    for i in range(3 + L):
        x, z = 6 + (i % 4) * 5, 20 + (i // 4) * 3
        k.fill(x, 2, z, x + 1, 3, z + 1, stones[i])
    hut = (19, 2, 5)
    k.lights(6, 26, 6, 26, 6, step=5)
    # stairs up through the tiers (inside, west side)
    if L >= 2:
        k.stairs(8, 9, 2, 5, "south", cut_y=6)
    if L >= 3:
        k.stairs(12, 13, 7, 5, "south", cut_y=11)
        bp.set(12, 11, 18, k.st.floor(12, 18))
        for x in range(14, 19):
            bp.set(x, 12, 14, "bookshelf")
        bp.set(20, 12, 20, "lectern[facing=north,has_book=false,powered=false]")
    if L >= 4:  # crown sculpture on the top tier
        k.fill(16, 21, 16, 16, 24, 16, "smooth_quartz")
        bp.set(16, 25, 16, "sea_lantern")
        bp.set(10, 2, 12, "grindstone[face=floor,facing=north]")
    if L >= 5:
        for x, z in ((2, 2), (30, 2), (2, 30), (30, 30)):
            bp.fill(x, 2, z, x, 5, z, "sea_lantern")
    k.landscape(trees=[(0, 0, 3), (32, 0, 3)], lamps=[(14, 0), (18, 0)])
    return k.finish_hut(hut, "blockhutstonemason")


# ============================================================================ Gear Hub (mechanic)
def build_mechanic(L):
    k = Kit("mechanic", "craftsmanship/metallurgy", L, (35, 26, 31))
    bp = k.bp
    C = 15
    R = 11
    k.ground(paved=[(14, 16, 0, 4)])
    clad = "light_gray_concrete" if k.st.early else "waxed_cut_copper"
    for x in range(C - R - 1, C + R + 2):
        for z in range(C - R - 1, C + R + 2):
            dx, dz = x - C, z - C
            inside = in_octagon(dx, dz, R)
            inner = in_octagon(dx, dz, R - 1)
            if inside and inner:
                bp.set(x, 1, z, k.st.floor(x, z))
                bp.set(x, 8, z, "smooth_stone" if k.st.early else k.D)
            elif inside:
                bp.set(x, 8, z, k.band)
                for y in range(2, 8):
                    bp.set(x, y, z, k.G if y in (3, 4, 5) and (x + z) % 3 else clad)
    k.opening(C, 2, C - R, C, 3, C - R)
    k.door(C, 2, C - R, "south")
    # gear sculpture in the middle: a ring of teeth
    for a in range(0, 360, 30):
        x, z = round(C + 3 * math.cos(math.radians(a))), round(C + 3 * math.sin(math.radians(a)))
        bp.set(x, 2, z, "waxed_copper_block" if not k.st.early else "iron_block")
    bp.set(C, 2, C, "iron_block")
    bp.set(C, 3, C, "waxed_copper_bulb[lit=true,powered=false]")
    # benches around the walls
    for x in range(C - 6, C - 1):
        k.set(x, 2, C + 8, k.st.counter)
    for x, s in ((C - 6, "piston[extended=false,facing=up]"), (C - 4, "observer[facing=north,powered=false]"),
                 (C - 2, "dispenser[facing=up,triggered=false]")):
        bp.set(x, 3, C + 8, s)
    for i in range(L + 1):
        rack(bp, C + 2 + i, 2, C + 9, "north")
    bp.set(C + 8, 2, C, "crafting_table")
    bp.set(C + 8, 2, C + 1, "anvil[facing=north]")
    hut = (C + 4, 2, C - 7)
    k.lights(C - 7, C + 7, C - 7, C + 7, 8, step=5)
    for a in range(0, 360, 45):                                        # copper light ring
        x, z = round(C + 8 * math.cos(math.radians(a))), round(C + 8 * math.sin(math.radians(a)))
        bp.set(x, 7, z, "waxed_copper_bulb[lit=true,powered=false]")
    if L >= 2:  # robot gantry over the gear
        for x in (C - 4, C + 4):
            k.fill(x, 2, C - 4, x, 6, C - 4, "iron_block")
        k.fill(C - 4, 7, C - 4, C + 4, 7, C - 4, "iron_block")
        bp.set(C, 6, C - 4, "chain[axis=y,waterlogged=false]")
        bp.set(C, 5, C - 4, "lightning_rod[facing=down,powered=false,waterlogged=false]")
    if L >= 3:  # satellite pod (east) + glass bridge
        PC = 29
        for x in range(PC - 4, PC + 5):
            for z in range(C - 4, C + 5):
                dx, dz = x - PC, z - C
                if in_octagon(dx, dz, 4):
                    bp.set(x, 8, z, k.band if not in_octagon(dx, dz, 3) else "smooth_stone")
                    if not in_octagon(dx, dz, 3):
                        for y in range(2, 8):
                            bp.set(x, y, z, k.G if y in (3, 4, 5) else clad)
                    else:
                        bp.set(x, 1, z, k.st.floor(x, z))
        for x in range(C + R, PC - 3):
            for z in (C - 1, C, C + 1):
                bp.set(x, 1, z, k.D)
                for y in (2, 3, 4):
                    bp.set(x, y, z, "air" if z == C or y < 4 else k.G)
                bp.set(x, 5, z, "glass")
            for y in (2, 3, 4):
                bp.set(x, y, C - 1, k.G)
                bp.set(x, y, C + 1, k.G)
        k.opening(C + R, 2, C, PC - 4, 3, C)
        bp.set(PC + 2, 2, C, "lectern[facing=west,has_book=false,powered=false]")
        bp.set(PC + 2, 2, C + 1, "cartography_table")
    if L >= 4:  # radar dish on the roof
        k.fill(C, 9, C, C, 11, C, "iron_block")
        for x in range(C - 3, C + 4):
            for z in range(C - 3, C + 4):
                d = math.hypot(x - C, z - C)
                if d < 3.5:
                    bp.set(x, 12 + (1 if d > 2.5 else 0), z, k.W if d > 1 else "sea_lantern")
    if L >= 5:
        k.mast(C - 6, 9, C + 6)
    k.landscape(trees=[(1, 1, 3), (1, 29, 3), (33, 29, 3)], lamps=[(12, 0), (18, 0)])
    return k.finish_hut(hut, "blockhutmechanic")


# ============================================================================ Crescent School
def build_school(L):
    k = Kit("school", "education", L, (37, 20, 31))
    bp = k.bp
    C, CZ, R1, R2 = 18, 23, 10, 16
    k.ground()
    spans = {1: (240, 300), 2: (215, 325), 3: (190, 350), 4: (180, 360), 5: (180, 360)}
    a1, a2 = spans[L]
    storeys = 1 if L < 3 else 2

    def in_band(x, z):
        d = math.hypot(x - C, z - CZ)
        ang = math.degrees(math.atan2(z - CZ, x - C)) % 360
        return R1 - 0.5 <= d < R2 + 0.5 and a1 <= ang <= a2
    cells = [(x, z) for x in range(37) for z in range(31) if in_band(x, z)]
    cellset = set(cells)
    for x, z in cells:
        boundary = any((x + dx, z + dz) not in cellset for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        for s in range(storeys):
            fy = 1 + 6 * s
            bp.set(x, fy, z, k.st.floor(x, z))
            bp.set(x, fy + 6, z, k.band if boundary else ("smooth_stone" if k.st.early else k.D))
            if boundary:
                inner = math.hypot(x - C, z - CZ) < (R1 + R2) / 2
                for y in range(fy + 1, fy + 6):
                    glass = y in (fy + 2, fy + 3, fy + 4) and (inner or (x + z) % 3)
                    bp.set(x, y, z, k.G if glass else k.W)
    # doors: north entrance + courtyard door
    for (x, z) in ((C, CZ - R2), (C, CZ - R1)):
        k.opening(x, 2, z, x, 3, z)
    # classroom in the north middle: board on the north wall, 10 seats facing it
    k.fill(C - 4, 3, CZ - R2 + 1, C + 4, 4, CZ - R2 + 1, "black_concrete")
    k.tag((C, 2, CZ - R2 + 2), "work")
    for i, x in enumerate((C - 5, C - 3, C - 1, C + 2, C + 4)):
        for z in (CZ - 13, CZ - 11):
            k.set(x, 2, z - 1, k.st.counter)
            k.seat(x, 2, z, "south")
    for i in range([2, 2, 4, 6, 8][L - 1]):
        a = math.radians(a1 + 6 + i * 4)
        x, z = round(C + 14 * math.cos(a)), round(CZ + 14 * math.sin(a))
        bp.set(x, 2, z, "bookshelf")
    hut = (C + 6, 2, CZ - 12)
    k.lights(C - 8, C + 8, CZ - 14, CZ - 11, 7, step=4)
    # courtyard playground
    if L >= 2:
        for x in range(C - 8, C + 9):
            for z in range(CZ - 8, 31):
                if math.hypot(x - C, z - CZ) < R1 - 1:
                    bp.set(x, 1, z, "sand" if abs(x - C) <= 3 and z > CZ else "grass_block[snowy=false]")
        for y in (2, 3, 4):
            bp.set(C - 5, y, CZ, k.AC)
        for i, z in enumerate((CZ + 1, CZ + 2, CZ + 3)):
            bp.set(C - 5, 4 - i, z, stair_state(k, "north"))
        for x in (C + 3, C + 6):
            k.fill(x, 2, CZ - 2, x, 4, CZ - 2, k.T)
        k.fill(C + 3, 5, CZ - 2, C + 6, 5, CZ - 2, k.T)
        for x in (C + 4, C + 5):
            bp.set(x, 4, CZ - 2, "chain[axis=y,waterlogged=false]")
            bp.set(x, 3, CZ - 2, "smooth_stone_slab[type=bottom,waterlogged=false]")
    if L >= 3:  # upper floor: art room + reading room, stairs
        k.stairs(C - 7, CZ - 13, 2, 6, "east", cut_y=7)
        for x in (C - 1, C + 1, C + 3):
            k.set(x, 8, CZ - 12, k.st.counter)
            k.seat(x, 8, CZ - 11, "south")
        bp.set(C + 5, 8, CZ - 14, "loom[facing=south]")
        bp.set(C + 6, 8, CZ - 14, "cartography_table")
        k.lights(C - 6, C + 6, CZ - 14, CZ - 11, 13, step=4)
    if L >= 4:  # roof garden on the crescent
        for x, z in cells[:: 9]:
            if bp.get(x, 13, z) != "minecraft:air" and "concrete" not in bp.get(x, 13, z):
                planter(bp, x, 14, z)
    if L >= 5:
        k.mast(C, 14, CZ - 13)
    k.landscape(trees=[(1, 1, 3), (35, 1, 3), (1, 29, 3), (35, 29, 3)], lamps=[(C - 3, 1), (C + 3, 1)])
    return k.finish_hut(hut, "blockhutschool")


# ============================================================================ Book Tower (library)
def build_library(L):
    k = Kit("library", "education", L, (27, 36, 27))
    sh, bp = Shapes(k), k.bp
    C, R, H = 13, 10, 5
    k.ground(paved=[(12, 14, 0, 3)])
    floors = [1 + H * i for i in range(L + 1)]                 # L+1 storeys
    for i, F in enumerate(floors):
        sh.drum(C, C, R, F, F + H, doors=(270,) if i == 0 else (), glass_every=20, floor=(i == 0), roof=True)
    k.door(C, 2, C - R, "south")
    # alternating stair runs at the east side (like the apartment core)
    for i, F in enumerate(floors[:-1] if L > 0 else []):
        col, zs, facing = (C + 7, range(C - 2, C + 3), "south") if i % 2 == 0 else (C + 6, range(C + 2, C - 3, -1), "north")
        zs = list(zs)
        for z in zs[:4]:
            bp.set(col, F + H, z, "air")
        for j, z in enumerate(zs):
            bp.set(col, F + 1 + j, z, stair_state(k, facing))
    # bookshelves on the outer ring, floor by floor, up to the official count
    target = [10, 30, 54, 104, 121][L - 1]
    ring = [(x, z) for x in range(C - R, C + R + 1) for z in range(C - R, C + R + 1)
            if R - 1.5 <= math.hypot(x - C, z - C) < R - 0.5 and not (abs(x - C) <= 1 and z < C)
            and not (x >= C + 5 and abs(z - C) <= 3)]
    placed = 0
    for F in floors:
        for y in (F + 1, F + 2, F + 3):
            for x, z in ring:
                if placed < target and bp.get(x, y, z) == "minecraft:air":
                    bp.set(x, y, z, "bookshelf")
                    placed += 1
    # reading tables in the middle of each floor
    for i, F in enumerate(floors):
        if i <= 1 or L >= 4:
            table(k, C - 2, F + 1, C + 1)
            if i == 0:
                table(k, C - 2, F + 1, C - 3)
        k.lights(C - 4, C + 2, C - 4, C + 4, F + H, step=4)
    bp.set(C, 2, C + 6, "lectern[facing=north,has_book=false,powered=false]")
    if L >= 4:
        bp.set(C - 5, 2, C, "enchanting_table")
    hut = (C + 3, 2, C - 7)
    top = floors[-1] + H
    sh.disc(C, C, R, top + 1, lambda x, z: k.st.railing, r_in=R - 0.5)
    if L >= 5:  # glass dome
        for x in range(C - R, C + R + 1):
            for z in range(C - R, C + R + 1):
                d = math.hypot(x - C, z - C)
                for y, (r1, r2) in ((top + 1, (7.5, 8.5)), (top + 2, (6.5, 7.5)), (top + 3, (5, 6.5)), (top + 4, (0, 5))):
                    if r1 <= d < r2:
                        bp.set(x, y, z, "sea_lantern" if (x * z) % 7 == 0 and y < top + 4 else "glass")
    k.landscape(trees=[(1, 1, 4), (25, 1, 4), (1, 25, 4), (25, 25, 4)], lamps=[(10, 1), (16, 1)],
                planters=[(5, 2, 3), (21, 2, 3)])
    return k.finish_hut(hut, "blockhutlibrary")


# ============================================================================ Arrow Range (archery)
def build_archery(L):
    k = Kit("archery", "military", L, (47, 20, 21))
    sh, bp = Shapes(k), k.bp
    k.ground(paved=[(13, 44, 3, 17)])
    # round bunk tower at the west end (2 storeys), beds 2 per level
    C = (7, 10)
    sh.drum(*C, 6, 1, 7, doors=(0,), glass_every=30)
    if L >= 3:
        sh.drum(*C, 6, 7, 13, glass_every=30)
        k.stairs(3, 7, 2, 6, "south", cut_y=7)
    spots = [(5, 13, 2), (7, 13, 2), (9, 13, 2), (5, 6, 2), (9, 6, 2),
             (5, 13, 8), (7, 13, 8), (9, 13, 8), (6, 6, 8), (8, 6, 8)]
    for x, z, y in spots[: 2 * L]:
        bed(bp, x, y, z, "south" if z > 10 else "north")
    bp.set(10, 2, 9, "furnace[facing=west,lit=false]")
    if L >= 3:
        bp.set(10, 2, 11, "fletching_table")
    hut = (4, 2, 9)
    k.lights(5, 9, 8, 12, 7, step=4)
    # range: arched canopy segments over the firing line + target wall
    for x in range(13, 45):
        for z in range(3, 18):
            bp.set(x, 1, z, "smooth_stone" if x < 17 else "grass_block[snowy=false]")
    for z in range(3, 18):
        for y in (2, 3, 4, 5):
            bp.set(44, y, z, k.W)
    for i in range(L):
        z = 5 + 3 * i
        bp.set(44, 3, z, "target[power=0]")
        k.set(15, 2, z, k.st.counter)
        k.tag((14, 2, z), "work")
    k.railing_ring(13, 44, 2, 18, 2, skip={(13, 10)})
    for seg in range(min(L + 1, 4)):
        x1 = 13 + seg * 8
        sh.vault(x1, x1 + 3, 2, 18, 3, rib_every=3, end_doors=False)
        for x in range(x1 + 1, x1 + 3):
            for z in range(3, 18):
                for y in range(2, 4):
                    bp.set(x, y, z, "air")
        for x in (x1, x1 + 3):
            for z in range(3, 18):
                for y in range(2, 8):
                    if z not in (2, 18) and bp.get(x, y, z) != "minecraft:air" and y < 6:
                        bp.set(x, y, z, "air")
    if L >= 5:
        for z in range(3, 18, 3):
            bp.set(44, 6, z, "sea_lantern")
    k.landscape(trees=[(1, 1, 3), (1, 19, 3)], lamps=[(14, 0), (30, 0)])
    return k.finish_hut(hut, "blockhutarchery")


# ============================================================================ Colosseum (combat academy)
def build_combatacademy(L):
    k = Kit("combatacademy", "military", L, (39, 20, 39))
    sh, bp = Shapes(k), k.bp
    C = 19
    k.ground(paved=[(17, 21, 0, 4)])
    # arena floor + tiered seating + outer arcaded wall
    for x in range(39):
        for z in range(39):
            d = math.hypot(x - C, z - C)
            ang = math.degrees(math.atan2(z - C, x - C)) % 360
            gate = abs(ang - 270) < 10
            if d < 9.5:
                bp.set(x, 1, z, "sand")
            elif d < 13.5:
                tier = int(d - 9.5)                                      # 0..3
                for y in range(2, 2 + tier):
                    bp.set(x, y, z, k.st.LIGHTGRAY if not gate else "air")
            elif d < 15.5:
                arch = int(ang / 15) % 2 == 0
                top = 6 + min(L, 3) * 2
                for y in range(2, top):
                    if gate and y <= 5:
                        bp.set(x, y, z, "air")
                    elif arch and 2 <= y <= 4 and d < 14.5:
                        bp.set(x, y, z, "air")
                    else:
                        bp.set(x, y, z, k.W if y < top - 1 else k.band)
    # spectator seats on the tiers (tagged sit)
    if L >= 2:
        for a in range(0, 360, 20):
            if abs(a - 270) < 15:
                continue
            for r, y in ((10, 2), (12, 4)):
                x, z = round(C + r * math.cos(math.radians(a))), round(C + r * math.sin(math.radians(a)))
                dx, dz = C - x, C - z
                back = ("west" if dx > 0 else "east") if abs(dx) >= abs(dz) else ("north" if dz > 0 else "south")
                k.seat(x, y, z, back)
    # dummies
    dummies = [(C + round(5 * math.cos(math.radians(a * 40))), C + round(5 * math.sin(math.radians(a * 40))))
               for a in range(9)]
    for x, z in dummies[: [1, 2, 3, 6, 9][L - 1]]:
        bp.set(x, 2, z, "hay_block[axis=y]")
        bp.set(x, 3, z, "carved_pumpkin[facing=north]")
    # bunk rooms under the south stands (beds 2 per level)
    for x in range(C - 6, C + 7):
        for z in range(C + 10, C + 14):
            for y in range(2, 5):
                bp.set(x, y, z, "air")
            bp.set(x, 5, z, k.st.LIGHTGRAY)
            bp.set(x, 1, z, k.st.floor(x, z))
    for x in range(C - 6, C + 7):
        for y in range(2, 5):
            bp.set(x, y, C + 9, k.W if abs(x - C) > 1 or y > 3 else "air")
    for i in range(2 * L):
        bed(bp, C - 5 + i, 2, C + 12, "south")
    bp.set(C + 6, 2, C + 11, "furnace[facing=west,lit=false]")
    bp.set(C + 6, 2, C + 10, "barrel[facing=west,open=false]")
    if L >= 3:
        bp.set(C - 6, 2, C + 10, "anvil[facing=north]")
        bp.set(C - 6, 2, C + 11, "grindstone[face=floor,facing=east]")
    for x in (C - 3, C + 3):
        k.st.ceiling_light(bp, x, 5, C + 11)
    hut = (C + 3, 2, C - 7)
    if L >= 5:
        sh.disc(C, C, 15, 6 + 3 * 2, lambda x, z: "sea_lantern" if (x + z) % 3 == 0 else k.band, r_in=14.5)
    k.landscape(trees=[(1, 1, 4), (37, 1, 4), (1, 37, 4), (37, 37, 4)], lamps=[(16, 1), (22, 1)])
    return k.finish_hut(hut, "blockhutcombatacademy")


# ============================================================================ Equestrian Hall (stable)
def build_stable(L):
    k = Kit("stable", "military", L, (43, 18, 33))
    sh, bp = Shapes(k), k.bp
    k.ground(paved=[(6, 8, 0, 3)])
    # stall block (west): 2 storeys, stalls ground, loft beds
    k.box(2, 13, 4, 26, 1, 7)
    k.box(2, 13, 4, 26, 7, 12, glass_front=False)
    k.opening(7, 2, 4, 8, 4, 4)
    k.opening(13, 2, 14, 13, 4, 16)                                       # into the riding hall
    stalls = [(4, z) for z in (7, 10, 13, 18, 21, 24)] + [(11, z) for z in (7, 10, 21, 24)]
    for x, z in stalls[: 2 * L]:
        side = 1 if x < 7 else -1
        for dz in (-1, 1):
            put(bp, x + side, 2, z + dz, k.st.railing)
        bp.set(x - side, 2, z, "hay_block[axis=y]")
        k.tag((x, 2, z), "stall")
    k.lights(4, 12, 6, 24, 7, step=5)
    k.lights(4, 12, 6, 24, 12, step=5)
    k.stairs(9, 25, 2, 6, "north", cut_y=7)                               # after the lights (no overlap)
    beds = [2, 4, 4, 6, 8][L - 1]
    for i in range(beds):
        bed(bp, 3 + 2 * (i % 4), 8, 6 if i < 4 else 14, "north" if i < 4 else "south")
    bp.set(12, 8, 6, "barrel[facing=up,open=false]")
    hut = (8, 2, 6)
    # riding hall (east): barrel vault over a sand arena
    x2 = [24, 32, 40, 40, 40][L - 1]
    for x in range(14, x2 + 1):
        for z in range(5, 26):
            bp.set(x, 1, z, "sand")
    sh.vault(14, x2, 4, 26, 4, rib_every=4)
    if L >= 2:
        for x in range(16, x2 - 1, 6):
            bp.set(x, 2, 6, "hay_block[axis=y]")
    # paddock
    for x in range(1, 42):
        for z in range(27, 33):
            bp.set(x, 1, z, "grass_block[snowy=false]")
    k.railing_ring(1, 41, 27, 32, 2, skip={(7, 27)})
    k.opening(7, 2, 26, 7, 3, 26)
    if L >= 3:
        bp.set(30, 2, 30, "water_cauldron[level=3]")
    k.landscape(trees=[(0, 1, 3), (42, 1, 3)], lamps=[(5, 0), (10, 0)])
    return k.finish_hut(hut, "blockhutstable")


BUILDERS = {
    "fundamentals/cook": build_cook,
    "fundamentals/lumberjack": build_lumberjack,
    "craftsmanship/carpentry/sawmill": build_sawmill,
    "craftsmanship/masonry/stonemason": build_stonemason,
    "craftsmanship/metallurgy/mechanic": build_mechanic,
    "education/school": build_school,
    "education/library": build_library,
    "military/archery": build_archery,
    "military/combatacademy": build_combatacademy,
    "military/stable": build_stable,
}

if __name__ == "__main__":
    root = Path(sys.argv[1])
    only = sys.argv[2:]
    for key, fn in BUILDERS.items():
        if only and not any(o in key for o in only):
            continue
        cat, name = key.rsplit("/", 1)
        (root / cat).mkdir(parents=True, exist_ok=True)
        for lvl in range(1, 6):
            fn(lvl).save(root / cat / f"{name}{lvl}.blueprint")
        print(f"{key}: 5 levels")
