"""
Neoterra work huts, levels 1-5:

  fundamentals/cook          "Sky Bistro" restaurant (minecolonies:blockhutcook): glass dining
                             pavilion, open kitchen with one furnace per level (like the official
                             packs), dining seats tagged `sit`, kitchen spots tagged `work`.
  fundamentals/lumberjack    "Timber Lab" forester: workshop + tree nursery (saplings) that
                             gets a glass greenhouse.
  craftsmanship/carpentry/sawmill      "Panel Works" woodcutter: saw lines + log yard.
  craftsmanship/masonry/stonemason     "Stone Atelier": stone yard with block stacks + sculpture.
  craftsmanship/metallurgy/mechanic    "Mech Lab": copper-lit workshop, test bench, robot arm.

Workshop huts share one hall: ground floor workshop with racks, yard on the east side,
canopy (L2), upper floor office + roof terrace (L3), roof access + premium (L4), glow (L5).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit import Kit, edge, put, rack, tree, planter, bed  # noqa: E402


# ============================================================================ restaurant
def build_cook(L):
    k = Kit("cook", "fundamentals", L, (25, 20, 23))
    bp, W, G, T = k.bp, k.W, k.G, k.T
    k.ground(paved=[(10, 14, 0, 4)])
    X1, X2, Z1, Z2 = 2, 22, 5, 18
    k.box(X1, X2, Z1, Z2, 1, 7, chamfer=True)
    # kitchen at the back behind a pass-through counter
    for x in range(X1 + 1, X2):
        if x in (11, 12, 13):
            continue
        k.set(x, 2, 14, k.st.counter)
    k.opening(12, 2, Z1, 12, 3, Z1)
    k.door(12, 2, Z1, "south")
    for i in range(L):                                                  # one furnace per level
        bp.set(4 + 2 * i, 2, 17, "furnace[facing=north,lit=false]")
        k.tag((4 + 2 * i, 2, 16), "work")
    bp.set(15, 2, 17, "smoker[facing=north,lit=false]")
    bp.set(16, 2, 17, "crafting_table")
    for x in (17, 18):
        bp.set(x, 2, 17, "barrel[facing=north,open=false]")
    rack(bp, 20, 2, 17, "north")
    if L >= 3:
        rack(bp, 21, 2, 17, "north")
    k.tag((16, 2, 16), "work")
    # dining tables (2 seats each), more tables every level
    tables = [(6, 8), (10, 8), (15, 8), (19, 8), (6, 11), (10, 11), (15, 11), (19, 11)]
    for tx, tz in tables[: 2 + 2 * min(L, 3)]:
        k.set(tx, 2, tz, k.st.counter)
        k.seat(tx - 1, 2, tz, "west")
        k.seat(tx + 1, 2, tz, "east")
    k.lights(5, 20, 7, 16, 7, step=5)
    hut = (14, 2, 6)
    if L >= 2:  # outdoor terrace under a canopy
        k.canopy(4, 20, 1, 4, 6, columns=[(4, 1), (20, 1)])
        for tx in (6, 18):
            k.set(tx, 2, 2, k.st.counter)
            k.seat(tx - 1, 2, 2, "west")
            k.seat(tx + 1, 2, 2, "east")
    if L >= 3:  # upper sky lounge over the back half + stairs
        k.box(8, X2, 9, Z2, 7, 13, front="north")
        k.opening(14, 8, 9, 15, 9, 9)                                    # door to the roof terrace
        k.stairs(3, 9, 2, 6, "south", cut_y=7)
        for tx, tz in ((11, 12), (15, 12), (19, 12), (11, 15), (15, 15)):
            k.set(tx, 8, tz, k.st.counter)
            k.seat(tx - 1, 8, tz, "west")
            k.seat(tx + 1, 8, tz, "east")
        bp.set(20, 8, 17, "barrel[facing=north,open=false]")
        k.lights(11, 19, 11, 16, 13, step=4)
        k.railing_ring(X1, X2, Z1, Z2, 8, skip={(x, z) for x in range(8, X2 + 1) for z in range(9, Z2 + 1)})
        for x in (5, 17):
            planter(bp, x, 8, 6)
    if L >= 4:  # rooftop bar on the sky lounge roof
        k.railing_ring(8, X2, 9, Z2, 14)
        for y in range(8, 15):
            bp.set(21, y, 17, "ladder[facing=west,waterlogged=false]")
        for x in range(12, 18):
            k.set(x, 14, 14, k.st.counter)
        for x in (12, 14, 16):
            k.seat(x, 14, 15, "south")
        bp.set(18, 14, 13, "jukebox[has_record=false]")
    if L >= 5:
        for x in (10, 20):
            tree(bp, x, 14, 11, h=2)
    k.landscape(trees=[(0, 1), (24, 1), (0, 21), (24, 21)], lamps=[(9, 0), (15, 0)])
    return k.finish_hut(hut, "blockhutcook")


# ============================================================================ workshop template
def workshop(name, category, block, L, racks_per_level, decorate, cladding=None):
    """cladding(level, style) -> wall block for the hall + upper floor (None = white)."""
    k = Kit(name, category, L, (25, 20, 21))
    bp = k.bp
    HX1, HX2, HZ1, HZ2 = 2, 14, 4, 16
    YX1, YX2, YZ1, YZ2 = 16, 23, 3, 18
    k.ground(paved=[(7, 9, 0, 3), (YX1, YX2, YZ1, YZ2)])
    wall = cladding(L, k.st) if cladding else None
    k.box(HX1, HX2, HZ1, HZ2, 1, 7, wall=wall)
    k.opening(8, 2, HZ1, 8, 3, HZ1)
    k.door(8, 2, HZ1, "south")
    k.opening(HX2, 2, 10, HX2, 3, 10)                                    # side door to the yard
    k.lights(5, 13, 7, 15, 7, step=4)
    for i in range(racks_per_level[L - 1]):
        rack(bp, 4 + (i % 9), 2 + i // 9, 15, "north")
    bp.set(13, 2, 15, "crafting_table")
    hut = (12, 2, 6)
    k.set(11, 2, 6, k.st.counter)
    if L >= 2:
        k.canopy(5, 11, 1, 3, 6, columns=[(5, 1), (11, 1)])
        k.railing_ring(YX1, YX2 + 1, YZ1 - 1, YZ2 + 1, 2, skip={(x, YZ1 - 1) for x in range(18, 22)} | {(YX1, 10)})
    if L >= 3:
        k.box(HX1, HX2, 8, HZ2, 7, 13, front="north", wall=wall)
        k.opening(8, 8, 8, 9, 9, 8)
        k.stairs(3, 6, 2, 6, "south", cut_y=7)
        k.railing_ring(HX1, HX2, HZ1, HZ2, 8, skip={(x, z) for x in range(HX1, HX2 + 1) for z in range(8, HZ2 + 1)})
        y = 8
        for x in range(5, 9):
            k.set(x, y, 12, k.st.counter)
        for x in (5, 7):
            k.seat(x, y, 13, "south")
        bp.set(11, y, 15, "lectern[facing=north,has_book=false,powered=false]")
        bp.set(12, y, 15, "cartography_table")
        for x in range(4, 9):
            bp.set(x, y, 15, "bookshelf")
        k.lights(5, 12, 11, 15, 13, step=4)
    if L >= 4:
        k.railing_ring(HX1, HX2, 8, HZ2, 14)
        for yy in range(8, 15):
            bp.set(13, yy, 15, "ladder[facing=west,waterlogged=false]")
        bed(bp, 10, 8, 13, "east")                                       # rest bed upstairs
    if L >= 5:
        k.mast(4, 15, 15)
    decorate(k, L)
    k.landscape(trees=[(0, 1), (0, 19)], lamps=[(4, 0), (12, 0)])
    return k.finish_hut(hut, block)


def deco_forester(k, L):
    bp = k.bp
    # tree nursery in the yard: rows of saplings, more every level
    saplings = ["oak_sapling", "birch_sapling", "spruce_sapling", "jungle_sapling", "acacia_sapling", "cherry_sapling"]
    spots = [(x, z) for z in (5, 9, 13, 17) for x in (18, 21)]
    for i, (x, z) in enumerate(spots[: 2 + 2 * L]):
        bp.set(x, 1, z, "grass_block[snowy=false]")
        bp.set(x, 2, z, f"{saplings[i % len(saplings)]}[stage=0]")
    for x, z in ((5, 7), (6, 7), (5, 8)):
        bp.set(x, 2, z, "stripped_oak_log[axis=x]")                       # log stacks
    if L >= 3:  # glass greenhouse over the nursery (doors: front x18-21, west side z10)
        for x in range(16, 24):
            for z in range(3, 19):
                e = edge(x, z, 16, 23, 3, 18)
                door_cell = (z == 3 and 18 <= x <= 21) or (x == 16 and z == 10)
                if e:
                    for y in (2, 3, 4, 5):
                        if door_cell and y <= 3:
                            bp.set(x, y, z, "air")
                        else:
                            bp.set(x, y, z, k.G if y > 2 else k.W)
                bp.set(x, 6, z, k.band if e else "glass")
    if L >= 4:
        bp.set(9, 2, 12, "composter[level=0]")


def deco_sawmill(k, L):
    bp = k.bp
    if L >= 2 and L < 3:  # sawtooth skylights on the hall roof
        for z in (6, 10, 14):
            for x in range(3, 14):
                bp.set(x, 7, z, "glass")
    if L >= 3:
        for z in (5, 6, 7):
            for x in range(3, 14):
                bp.set(x, 8, z, "glass" if z == 6 else bp.get(x, 8, z))
    for x in range(5, 5 + min(L + 1, 5)):                                 # saw line
        bp.set(x, 2, 9, "stonecutter[facing=north]")
    k.fill(5, 2, 11, 9, 2, 11, k.st.counter)
    for x, z in ((18, 6), (20, 6), (18, 12), (20, 12), (22, 9)):          # log yard
        k.fill(x, 2, z, x + 1, 2 + min(L, 3) - 1, z + 1, "stripped_spruce_log[axis=z]")
    if L >= 3:
        for z in range(14, 18):
            bp.set(22, 2, z, "barrel[facing=west,open=false]")
    if L >= 4:
        bp.set(12, 2, 12, "domum_ornamentum:architectscutter[facing=north]")


def deco_stonemason(k, L):
    bp = k.bp
    if L >= 2:  # monolith sculpture on the forecourt
        k.fill(14, 2, 1, 14, 4 + min(L, 4), 1, "polished_diorite" if k.st.early else "smooth_quartz")
        bp.set(14, 5 + min(L, 4), 1, "sea_lantern" if not k.st.early else "polished_diorite")
    for x in range(5, 5 + min(L + 1, 5)):
        bp.set(x, 2, 9, "stonecutter[facing=north]")
    stones = ["smooth_stone", "polished_andesite", "polished_diorite", "polished_granite", "stone_bricks",
              "bricks", "calcite", "polished_tuff"]
    for i, (x, z) in enumerate([(18, 5), (21, 5), (18, 9), (21, 9), (18, 13), (21, 13), (18, 16), (21, 16)][: 3 + L]):
        k.fill(x, 2, z, x + 1, 3, z + 1, stones[i])                          # block stacks
    if L >= 3:  # sculpture: a stacked monolith
        k.fill(12, 2, 11, 12, 4, 11, "polished_diorite")
        bp.set(12, 5, 11, "sea_lantern" if not k.st.early else "polished_diorite")
    if L >= 4:
        bp.set(10, 2, 12, "grindstone[face=floor,facing=north]")


def deco_mechanic(k, L):
    bp = k.bp
    for x in range(5, 10):                                               # test bench
        k.set(x, 2, 9, k.st.counter)
    for x, s in ((5, "piston[extended=false,facing=up]"), (7, "observer[facing=north,powered=false]"),
                 (9, "dispenser[facing=up,triggered=false]")):
        bp.set(x, 3, 9, s)
    for x in range(4, 4 + min(2 * L, 10)):                               # copper light strip
        bp.set(x, 6, 13, "waxed_copper_bulb[lit=true,powered=false]")
    # robot arm in the yard: base, joints and a gripper
    k.fill(20, 2, 10, 20, 4, 10, "iron_block")
    k.fill(20, 5, 10, 18, 5, 10, "iron_block")
    bp.set(18, 4, 10, "chain[axis=y,waterlogged=false]")
    bp.set(18, 3, 10, "lightning_rod[facing=down,powered=false,waterlogged=false]")
    if L >= 3:
        for z in (6, 14):
            k.fill(22, 2, z, 22, 3, z, "waxed_copper_block")
    if L >= 4:
        bp.set(20, 6, 10, "sea_lantern")
        bp.set(12, 2, 12, "anvil[facing=north]")
        # rooftop vertical-axis wind turbine
        for y in range(15, 19):
            bp.set(9, y, 12, "chain[axis=y,waterlogged=false]")
        for y in (16, 18):
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                bp.set(9 + dx, y, 12 + dz, "waxed_cut_copper")
        bp.set(9, 19, 12, "lightning_rod[facing=up,powered=false,waterlogged=false]")


def build_lumberjack(L):
    return workshop("lumberjack", "fundamentals", "blockhutlumberjack", L, [2, 3, 4, 5, 6], deco_forester,
                    cladding=lambda L, st: "stripped_spruce_log[axis=y]")


def build_sawmill(L):
    return workshop("sawmill", "craftsmanship/carpentry", "blockhutsawmill", L, [1, 2, 3, 4, 6], deco_sawmill,
                    cladding=lambda L, st: "spruce_planks" if st.early else "stripped_spruce_wood[axis=y]")


def build_stonemason(L):
    return workshop("stonemason", "craftsmanship/masonry", "blockhutstonemason", L, [1, 2, 3, 4, 6], deco_stonemason,
                    cladding=lambda L, st: "smooth_stone" if st.early else "polished_diorite")


def build_mechanic(L):
    return workshop("mechanic", "craftsmanship/metallurgy", "blockhutmechanic", L, [1, 2, 3, 4, 6], deco_mechanic,
                    cladding=lambda L, st: "light_gray_concrete" if st.early else "waxed_cut_copper")


BUILDERS = {}  # superseded by unique.py (Halo Bistro, Arbor Vault, Timber Works, Stepped Atelier, Gear Hub)

if __name__ == "__main__":
    root = Path(sys.argv[1])
    for key, fn in BUILDERS.items():
        cat, name = key.rsplit("/", 1)
        (root / cat).mkdir(parents=True, exist_ok=True)
        for lvl in range(1, 6):
            b = fn(lvl)
            b.save(root / cat / f"{name}{lvl}.blueprint")
        print(f"{key}: 5 levels")
