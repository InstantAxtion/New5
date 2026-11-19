"""
Neoterra education buildings, levels 1-5 (category education/):

  school      (blockhutschool)     classroom with 10 tagged seats (`sit`) facing a teacher spot
                                   (`work`) and a board; playground (L2), art & reading loft (L3),
                                   premium + garden (L4), rooftop observatory (L5).
  library     (blockhutlibrary)    double-height reading hall; bookshelves grow every level
                                   (~10 / 30 / 54 / 100+ / 120+ like the official packs), study seats,
                                   mezzanine (L3), glass reading dome (L5).
  university  (blockhutuniversity) campus: round research rotunda (bookshelves grow per level),
                                   lecture wing, lab wing (furnaces, brewing), quad with trees and
                                   `leisure` spots (L3+), glowing dome (L5).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit import Kit, edge, put, rack, tree, planter  # noqa: E402

CARPETS = ["red_carpet", "blue_carpet", "yellow_carpet", "green_carpet", "purple_carpet", "white_carpet"]


# ============================================================================ school
def build_school(L):
    k = Kit("school", "education", L, (23, 20, 23))
    bp = k.bp
    X1, X2, Z1, Z2 = 2, 20, 4, 14
    k.ground(paved=[(9, 11, 0, 3)])
    k.box(X1, X2, Z1, Z2, 1, 7, chamfer=True)
    k.opening(10, 2, Z1, 10, 3, Z1)
    k.door(10, 2, Z1, "south")
    # board + teacher spot at the back, 10 desks facing it
    k.fill(6, 3, Z2 - 1, 14, 4, Z2 - 1, "black_concrete")
    k.tag((10, 2, 12), "work")
    for row, z in enumerate((7, 9)):
        for i, x in enumerate((4, 7, 10, 13, 16)):
            k.set(x, 2, z + 1, k.st.counter)                              # desk in front of the seat
            k.seat(x, 2, z, "north")                                      # backrest north: faces the board
            bp.set(x + 1, 2, z, CARPETS[(i + row) % len(CARPETS)])
    for i in range([2, 2, 4, 6, 8][L - 1]):
        bp.set(3 + i % 2, 2 + i // 2 % 2, 13 - (i // 4), "bookshelf")
    k.lights(5, 17, 7, 12, 7, step=4)
    hut = (18, 2, 6)
    if L >= 2:  # playground behind the school
        for x in range(3, 20):
            for z in range(16, 22):
                bp.set(x, 1, z, "sand" if (4 <= x <= 7 and 17 <= z <= 20) else "grass_block[snowy=false]")
        k.opening(10, 2, Z2, 10, 3, Z2)
        for y in (2, 3, 4):                                             # slide tower
            bp.set(12, y, 18, k.AC)
        for i, z in enumerate((19, 20, 21)):
            bp.set(12, 4 - i, z, f"{k.st.SEAT}[facing=north,half=bottom,shape=straight,waterlogged=false]")
        for x in (15, 18):                                              # swing frame
            k.fill(x, 2, 18, x, 4, 18, k.T)
        k.fill(15, 5, 18, 18, 5, 18, k.T)
        for x in (16, 17):
            bp.set(x, 4, 18, "chain[axis=y,waterlogged=false]")
            bp.set(x, 3, 18, "smooth_stone_slab[type=bottom,waterlogged=false]")
        k.railing_ring(2, 20, 15, 22, 2, skip={(10, 15)})
    if L >= 3:  # art & reading loft upstairs
        k.box(6, X2, 4, Z2, 7, 12, front="north", chamfer=True)
        k.stairs(3, 6, 2, 6, "south", cut_y=7)
        k.opening(6, 8, 12, 6, 9, 12)                                     # loft door from the stair landing
        for x in range(8, 13):
            bp.set(x, 8, 13, "bookshelf")
        for x in (9, 11, 14):
            k.set(x, 8, 9, k.st.counter)
            k.seat(x, 8, 10, "south")
        bp.set(16, 8, 13, "loom[facing=north]")
        bp.set(17, 8, 13, "cartography_table")
        k.lights(9, 17, 7, 12, 12, step=4)
        k.railing_ring(X1, X2, Z1, Z2, 8, skip={(x, z) for x in range(6, X2 + 1) for z in range(Z1, Z2 + 1)})
    if L >= 4:
        for x in (4, 18):
            planter(bp, x, 2, 16)
    if L >= 5:  # rooftop observatory: small glass dome
        for x in range(10, 17):
            for z in range(6, 13):
                d = math.hypot(x - 13, z - 9)
                if d < 3.5:
                    bp.set(x, 13, z, "glass" if d < 2.5 else k.W)
                    if 2.5 <= d < 3.5:
                        bp.set(x, 14, z, "glass")
        bp.set(13, 13, 9, "sea_lantern")
        k.railing_ring(6, X2, 4, Z2, 13)
        for y in range(8, 13):
            bp.set(19, y, 13, "ladder[facing=west,waterlogged=false]")
    k.landscape(trees=[(0, 1), (22, 1), (0, 20), (22, 20)], lamps=[(8, 0), (12, 0)])
    return k.finish_hut(hut, "blockhutschool")


# ============================================================================ library
def build_library(L):
    k = Kit("library", "education", L, (25, 22, 23))
    bp = k.bp
    X1, X2, Z1, Z2 = 2, 22, 4, 20
    k.ground(paved=[(11, 13, 0, 3)])
    top = 10                                                            # double-height hall
    k.box(X1, X2, Z1, Z2, 1, top, chamfer=True)
    k.opening(12, 2, Z1, 12, 3, Z1)
    k.door(12, 2, Z1, "south")
    target = [10, 30, 54, 104, 121][L - 1]
    shelves = []
    # wall shelves (inner face of side + back walls), then freestanding stacks
    for y in range(2, 9):
        for z in range(6, Z2):
            shelves += [(X1 + 1, y, z), (X2 - 1, y, z)]
        for x in range(4, X2 - 1):
            shelves.append((x, y, Z2 - 1))
    for z in range(10, 18, 2):
        for x in list(range(5, 10)) + list(range(15, 20)):
            for y in (2, 3):
                shelves.append((x, y, z))
    shelves.sort(key=lambda p: (p[1], p[2] < 10, p[0]))
    for p in shelves[:target]:
        bp.set(*p, "bookshelf")
    # reading tables with seats in the middle aisle
    seats = 4 if L < 4 else 8
    for i in range(seats // 2):
        z = 8 + 3 * i
        k.set(12, 2, z, k.st.counter)
        k.seat(11, 2, z, "west")
        k.seat(13, 2, z, "east")
    bp.set(12, 2, 19, "lectern[facing=north,has_book=false,powered=false]")
    k.lights(6, 19, 7, 18, top, step=4)
    hut = (20, 2, 6)
    if L >= 2:
        k.canopy(9, 15, 1, 3, 6, columns=[(9, 1), (15, 1)])
    if L >= 3:  # mezzanine gallery along the back with stairs
        for x in range(3, X2):
            for z in range(15, Z2):
                bp.set(x, 6, z, k.D)
        for x in range(3, X2):
            if x not in (3,):
                put(bp, x, 7, 14, k.st.railing)
        k.stairs(3, 9, 2, 5, "south", cut_y=6, rail=False)
        bp.set(3, 6, 14, "air")
        for x in range(6, 19, 3):
            k.seat(x, 7, 16, "south")
    if L >= 4:
        bp.set(10, 2, 6, "enchanting_table")
    if L >= 5:  # glass reading dome on the roof
        for x in range(5, 20):
            for z in range(6, 19):
                d = math.hypot(x - 12, (z - 12) * 1.1)
                if d < 6.5:
                    bp.set(x, top, z, "glass" if d < 5.5 else k.W)
                    if 5.5 <= d < 6.5:
                        bp.set(x, top + 1, z, "glass")
                    if 4.5 <= d < 5.5:
                        bp.set(x, top + 2, z, "glass")
        bp.set(12, top + 3, 12, "sea_lantern")
    k.landscape(trees=[(0, 1), (24, 1), (0, 21), (24, 21)], lamps=[(9, 0), (15, 0)],
                planters=[(5, 2, 2), (19, 2, 2)])
    return k.finish_hut(hut, "blockhutlibrary")


# ============================================================================ university
def build_university(L):
    k = Kit("university", "education", L, (37, 28, 37))
    bp = k.bp
    C = 18
    k.ground(paved=[(16, 20, 0, 6)])
    # quad paving + lawn
    for x in range(37):
        for z in range(37):
            d = math.hypot(x - C, z - C)
            if d < 16 and not (abs(x - C) <= 1 or abs(z - C) <= 1):
                bp.set(x, 1, z, "grass_block[snowy=false]")
            elif d < 16:
                bp.set(x, 1, z, "smooth_stone" if k.st.early else "smooth_quartz")
    # research rotunda (r7) in the centre, double height
    R, top = 7, 11
    for x in range(C - R - 1, C + R + 2):
        for z in range(C - R - 1, C + R + 2):
            d = math.hypot(x - C, z - C)
            if d < R - 0.5:
                bp.set(x, 1, z, k.st.floor(x, z))
                bp.set(x, top, z, "glass" if d < 3 and L >= 3 else (k.D if not k.st.early else "smooth_stone"))
            elif d < R + 0.5:
                bp.set(x, top, z, k.band)
                for y in range(2, top):
                    door_gap = abs(x - C) <= 1 and z < C and y <= 4
                    ang = math.degrees(math.atan2(z - C, x - C)) % 360
                    if door_gap:
                        bp.set(x, y, z, "air")
                    elif y == top - 1:
                        bp.set(x, y, z, k.W)
                    elif int(ang / 30) % 2 == 0 and y < top - 2:
                        bp.set(x, y, z, k.G)
                    else:
                        bp.set(x, y, z, k.W)
    # bookshelf rings inside the rotunda
    target = [4, 21, 41, 46, 47][L - 1]
    ring = [(x, z) for x in range(C - 6, C + 7) for z in range(C - 6, C + 7)
            if 5.5 <= math.hypot(x - C, z - C) < 6.5 and not (abs(x - C) <= 1 and z < C)]
    ring.sort(key=lambda p: math.atan2(p[1] - C, p[0] - C))
    placed = 0
    for y in (2, 3, 4):
        for x, z in ring:
            if placed < target:
                bp.set(x, y, z, "bookshelf")
                placed += 1
    for x, z in ((C - 2, C), (C + 2, C)):
        k.set(x, 2, z, k.st.counter)
        k.seat(x, 2, z + 1, "south")
    bp.set(C, 2, C + 3, "lectern[facing=north,has_book=false,powered=false]")
    k.lights(C - 4, C + 4, C - 4, C + 4, top, step=4)
    hut = (C + 3, 2, C - 4)
    # lab wing (west) with furnaces and brewing
    k.box(2, 9, 12, 24, 1, 7)
    k.opening(9, 2, 18, 9, 3, 18)
    for i in range([1, 1, 3, 3, 3][L - 1]):
        bp.set(3, 2, 14 + i, "furnace[facing=east,lit=false]")
    if L >= 2:
        bp.set(3, 2, 20, "brewing_stand[has_bottle_0=false,has_bottle_1=false,has_bottle_2=false]")
        bp.set(3, 2, 21, "water_cauldron[level=3]")
        bp.set(3, 2, 22, "crafting_table")
    rack(bp, 8, 2, 23, "north")
    k.lights(5, 7, 14, 22, 7, step=4)
    # lecture wing (east) with tiered seats
    if L >= 2:
        k.box(27, 34, 12, 24, 1, 8)
        k.opening(27, 2, 18, 27, 3, 18)
        k.fill(30, 3, 23, 33, 4, 23, "black_concrete")
        for z in range(14, 21, 2):
            k.seat(30, 2, z, "west")
            k.seat(32, 2, z, "west")
        k.lights(29, 33, 14, 22, 8, step=4)
    # quad leisure spots, trees
    if L >= 3:
        for a in range(8):
            ang = math.radians(a * 45 + 22.5)
            x, z = round(C + 11 * math.cos(ang)), round(C + 11 * math.sin(ang))
            if 2 <= x <= 9 and 12 <= z <= 24 or 27 <= x <= 34 and 12 <= z <= 24:
                continue
            k.seat(x, 2, z, "north" if z > C else "south")
            k.tag((x, 2, z), "leisure")
        for x, z in ((C - 11, C - 11), (C + 11, C - 11), (C - 11, C + 11), (C + 11, C + 11)):
            k.tag((x + 1, 2, z), "leisure")
    if L >= 5:  # glowing dome over the rotunda
        for x in range(C - 6, C + 7):
            for z in range(C - 6, C + 7):
                d = math.hypot(x - C, z - C)
                for y, (r1, r2) in ((top + 1, (5.5, 6.5)), (top + 2, (4.5, 5.5)), (top + 3, (3, 4.5))):
                    if r1 <= d < r2:
                        bp.set(x, y, z, "sea_lantern" if (x + z) % 4 == 0 else "glass")
        bp.set(C, top + 4, C, "end_rod[facing=up]")
    k.landscape(trees=[(C - 12, C - 12, 4), (C + 12, C - 12, 4), (C - 12, C + 12, 4), (C + 12, C + 12, 4),
                       (1, 1), (35, 1), (1, 35), (35, 35)],
                lamps=[(15, 2), (21, 2)])
    return k.finish_hut(hut, "blockhutuniversity")


BUILDERS = {"education/school": build_school, "education/library": build_library,
            "education/university": build_university}

if __name__ == "__main__":
    root = Path(sys.argv[1])
    for key, fn in BUILDERS.items():
        cat, name = key.rsplit("/", 1)
        (root / cat).mkdir(parents=True, exist_ok=True)
        for lvl in range(1, 6):
            fn(lvl).save(root / cat / f"{name}{lvl}.blueprint")
        print(f"{key}: 5 levels")
