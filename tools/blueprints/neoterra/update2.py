"""
Neoterra update 2 – production & farming (levels 1-5, cheap 1-3 / premium 4-5).

  craftsmanship/carpentry/fletcher        Arrow Works       wedge (arrowhead) workshop + test lane
  craftsmanship/luxury/cookery            Test Kitchen      glass cube kitchen, roof herb garden (furnaces 1-4)
  craftsmanship/luxury/alchemist          Apothecary Tower  round tower + greenhouse (brewing stands = level,
                                                            nether-wart soul sand beds)
  craftsmanship/luxury/dyer               Colour Lab        striped concrete facade, dye vats (cauldrons)
  craftsmanship/luxury/glassblower        Glass Pavilion    all-glass octagon, sand pile (furnaces = level)
  craftsmanship/luxury/concretemixer      Mixer Plant       silos + mixing basin (water pool)
  craftsmanship/masonry/crusher           Crusher Mill      stepped hopper tower, gravel/sand heaps
  craftsmanship/masonry/sifter            Sifting Terrace   stepped open terraces with screens
  craftsmanship/masonry/stonesmeltery     Kiln House        twin brick kiln domes + hall (furnaces = level)
  agriculture/horticulture/florist        Flower Atrium     greenhouse with composted-dirt beds (4/8/12/16/20)
  agriculture/horticulture/plantation     Plantation Park   tagged cactus / bamboo / sugar cane beds round a pavilion
  agriculture/horticulture/composter      Bio Hub           round green-roof hub with compost barrels (1-5)
  agriculture/husbandry/beekeeper         Apiary            hexagon pavilion in a meadow (beehives 1-3)
  agriculture/husbandry/chickenherder     Coop Pods         dome pods in a fenced yard
  agriculture/husbandry/cowboy            Cattle Barn       vaulted barn + paddock + troughs
  agriculture/husbandry/shepherd          Hill Fold         round stone fold + shelter, meadow
  agriculture/husbandry/swineherder       Sty Row           row of sawtooth sties + mud yard
  agriculture/husbandry/rabbithutch       Burrow Garden     earth-sheltered mound with round windows
  agriculture/fields/neobamboo, neocactus, neosugar, neokelp   plantation fields (official tag format)
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

from nbtlib import tag as NBT

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from kit import Kit, Shapes, edge, put, rack, tree, planter, bed, in_octagon  # noqa: E402
from common import connect_panes, street_lamp, PACK_NAME  # noqa: E402

SOLID = "structurize:blocksolidsubstitution"
GATE = "birch_fence_gate[facing=north,in_wall=false,open=false,powered=false]"


def stairs(k, facing, half="bottom"):
    return f"{k.st.SEAT}[facing={facing},half={half},shape=straight,waterlogged=false]"


def pen(k, x1, x2, z1, z2, gate, floor="grass_block[snowy=false]"):
    """Animal pen: floor, glass-pane railing (animals can't pass), a fence gate."""
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            k.bp.set(x, 1, z, floor if not edge(x, z, x1, x2, z1, z2) else k.W)
            if edge(x, z, x1, x2, z1, z2):
                put(k.bp, x, 2, z, k.st.railing)
    k.bp.set(*gate, GATE)


def trough(k, x1, x2, z):
    for x in range(x1, x2 + 1):
        k.bp.set(x, 2, z, "water_cauldron[level=3]")


def finish(k, hut, block):
    return k.finish_hut(hut, block)


# ============================================================================ fletcher
def build_fletcher(L):
    k = Kit("fletcher", "craftsmanship/carpentry", L, (31, 16, 21))
    bp = k.bp
    k.ground(paved=[(20, 29, 8, 12)])
    cells = {(x, z) for x in range(2, 20) for z in range(2, 19) if abs(z - 10) <= (20 - x) * 0.55 + 1.5}
    for x, z in cells:
        boundary = any((x + dx, z + dz) not in cells for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        bp.set(x, 1, z, k.st.floor(x, z))
        bp.set(x, 6, z, k.band if boundary else ("smooth_stone" if k.st.early else k.D))
        if boundary:
            for y in range(2, 6):
                bp.set(x, y, z, k.G if y in (3, 4) and (x + z) % 3 else k.W)
    k.opening(19, 2, 10, 19, 3, 10)
    k.door(19, 2, 10, "west")
    for i in range(min(L + 1, 5)):
        bp.set(5 + i, 2, 10, "fletching_table")
    for i in range(L + 1):
        rack(bp, 4 + i, 2, 5 if (4 + i, 5) in cells else 6, "south")
    bp.set(12, 2, 12, "crafting_table")
    bp.set(29, 2, 10, k.W)                                              # test lane with a target
    bp.set(29, 3, 10, "target[power=0]")
    if L >= 2:
        k.canopy(20, 28, 8, 12, 5, columns=[(20, 8), (28, 8), (20, 12), (28, 12)])
    if L >= 3:
        for z in range(4, 17, 3):
            if (2, z) in cells:
                bp.set(3, 2, z, "barrel[facing=east,open=false]")
    if L >= 5:
        bp.set(3, 6, 10, "sea_lantern")
    k.lights(4, 14, 8, 12, 6, step=4)
    k.landscape(trees=[(1, 1, 3), (1, 19, 3), (29, 1, 3)], lamps=[(21, 6), (27, 6)])
    return finish(k, (14, 2, 9), "blockhutfletcher")


# ============================================================================ cookery (kitchen)
def build_cookery(L):
    k = Kit("cookery", "craftsmanship/luxury", L, (19, 16, 19))
    bp = k.bp
    k.ground(paved=[(8, 10, 0, 3)])
    k.box(3, 15, 4, 16, 1, 8, glass_front=True)
    for x in range(3, 16):                                              # glass sides too: a glass cube
        for z in (4, 16):
            for y in range(2, 7):
                if x not in (3, 15):
                    bp.set(x, y, z, k.G)
    k.opening(9, 2, 4, 9, 3, 4)
    k.door(9, 2, 4, "south")
    for i in range([1, 2, 3, 4, 4][L - 1]):
        bp.set(5 + 2 * i, 2, 15, "furnace[facing=north,lit=false]")
    bp.set(13, 2, 15, "smoker[facing=north,lit=false]")
    bp.set(14, 2, 15, "water_cauldron[level=3]")
    for x in range(6, 13):
        k.set(x, 2, 10, k.st.counter)                                   # cooking island
    for i in range(L):
        rack(bp, 4, 2, 6 + i, "east")
    k.lights(6, 12, 7, 13, 8, step=3)
    if L >= 2:  # roof herb garden
        for x in range(4, 15):
            for z in range(5, 16):
                if (x + z) % 2 == 0:
                    bp.set(x, 8, z, "grass_block[snowy=false]")
                    bp.set(x, 9, z, ["fern", "azure_bluet", "oxeye_daisy", "short_grass"][(x * z) % 4])
        k.railing_ring(3, 15, 4, 16, 9)
        for y in range(2, 9):
            bp.set(14, y, 14, "ladder[facing=west,waterlogged=false]")
    if L >= 5:
        for x, z in ((3, 4), (15, 4), (3, 16), (15, 16)):
            k.fill(x, 2, z, x, 7, z, "sea_lantern")
    k.landscape(trees=[(1, 1, 3), (17, 1, 3)], lamps=[(7, 1), (11, 1)])
    return finish(k, (13, 2, 6), "blockhutkitchen")


# ============================================================================ alchemist
def build_alchemist(L):
    k = Kit("alchemist", "craftsmanship/luxury", L, (27, 32, 23))
    sh, bp = Shapes(k), k.bp
    k.ground(paved=[(7, 9, 0, 4)])
    C = (8, 11)
    floors = 1 + min(L, 4)
    for i in range(floors):
        sh.drum(*C, 5, 1 + 5 * i, 6 + 5 * i, doors=(270,) if i == 0 else (), glass_every=40, floor=(i == 0))
    k.door(8, 2, 6, "south")
    for y in range(2, 1 + 5 * floors):
        bp.set(11, y, 13, "ladder[facing=west,waterlogged=false]")
    for i in range(1, floors):
        bp.set(11, 1 + 5 * i, 13, "ladder[facing=west,waterlogged=false]")
    top = 1 + 5 * floors
    for x in range(C[0] - 4, C[0] + 5):                                  # spiral glass cap
        for z in range(C[1] - 4, C[1] + 5):
            d = math.hypot(x - C[0], z - C[1])
            for y, r in ((top + 1, 3.5), (top + 2, 2.5), (top + 3, 1.5)):
                if r - 1 <= d < r:
                    bp.set(x, y, z, "glass" if (x + y) % 3 else k.AC)
    bp.set(C[0], top + 4, C[1], "end_rod[facing=up]" if not k.st.early else "lightning_rod[facing=up,powered=false,waterlogged=false]")
    for i in range(L):
        bp.set(5 + i, 2, 12, "brewing_stand[has_bottle_0=false,has_bottle_1=false,has_bottle_2=false]")
    bp.set(10, 2, 9, "water_cauldron[level=3]")
    for i in range(L):
        rack(bp, 5 + i, 2, 14, "north")
    # greenhouse annex with nether-wart beds and glow-berry vines
    k.box(14, 25, 4, 18, 1, 6, glass_front=True)
    for x in range(15, 25):
        for z in range(5, 18):
            for y in range(2, 6):
                if edge(x, z, 14, 25, 4, 18):
                    bp.set(x, y, z, k.G if y > 2 else k.W)
    k.opening(14, 2, 11, 14, 3, 11)
    k.opening(13, 2, 11, 13, 3, 11)
    for x in range(16, 24, 3):
        for z in range(6, 17):
            if z != 11:
                bp.set(x, 1, z, "soul_sand")
                bp.set(x, 2, z, "nether_wart[age=3]")
    if L >= 3:
        for x in range(15, 25, 2):
            bp.set(x, 5, 5, "cave_vines[age=0,berries=true]")
    k.landscape(trees=[(1, 1, 3), (25, 21, 3)], lamps=[(6, 1), (10, 1)])
    return finish(k, (6, 2, 9), "blockhutalchemist")


# ============================================================================ dyer
def build_dyer(L):
    k = Kit("dyer", "craftsmanship/luxury", L, (21, 14, 19))
    bp = k.bp
    k.ground(paved=[(9, 11, 0, 3)])
    colors = ["red", "orange", "yellow", "lime", "cyan", "blue", "purple", "magenta"]
    X1, X2, Z1, Z2 = 3, 17, 4, 15
    for x in range(X1, X2 + 1):
        for z in range(Z1, Z2 + 1):
            e = edge(x, z, X1, X2, Z1, Z2)
            bp.set(x, 1, z, k.st.floor(x, z))
            bp.set(x, 8, z, k.band if e else ("smooth_stone" if k.st.early else k.D))
            if e:
                for y in range(2, 8):
                    glass = y in (3, 4) and z != Z1 and (x + z) % 3
                    stripe = colors[(x + z) // 2 % min(len(colors), 2 + 2 * L)]
                    bp.set(x, y, z, k.G if glass else (f"{stripe}_concrete" if z == Z1 or x in (X1, X2) else k.W))
    k.opening(10, 2, Z1, 10, 3, Z1)
    k.door(10, 2, Z1, "south")
    bp.set(16, 2, 14, "furnace[facing=west,lit=false]")
    for i in range(min(L + 1, 5)):
        bp.set(5 + 2 * i, 2, 13, "water_cauldron[level=3]")              # dye vats
    for i in range(L):
        rack(bp, 4, 2, 6 + i, "east")
    bp.set(16, 2, 6, "loom[facing=west]")
    bp.set(16, 2, 7, "crafting_table")
    k.lights(6, 14, 7, 12, 8, step=4)
    k.landscape(trees=[(1, 1, 3), (19, 1, 3), (1, 17, 3)], lamps=[(8, 1), (12, 1)])
    return finish(k, (15, 2, 10), "blockhutdyer")


# ============================================================================ glassblower
def build_glassblower(L):
    k = Kit("glassblower", "craftsmanship/luxury", L, (25, 16, 23))
    bp = k.bp
    C, R = (11, 11), 9
    k.ground(paved=[(10, 12, 0, 2)])
    for x in range(C[0] - R - 1, C[0] + R + 2):
        for z in range(C[1] - R - 1, C[1] + R + 2):
            dx, dz = x - C[0], z - C[1]
            if in_octagon(dx, dz, R) and in_octagon(dx, dz, R - 1):
                bp.set(x, 1, z, k.st.floor(x, z))
                bp.set(x, 7, z, "glass" if (dx + dz) % 2 else k.W)
            elif in_octagon(dx, dz, R):
                bp.set(x, 7, z, k.band)
                for y in range(2, 7):
                    bp.set(x, y, z, k.W if y == 6 or (abs(dx) + abs(dz)) % 4 == 0 else "glass")
    k.opening(11, 2, 2, 11, 3, 2)
    k.door(11, 2, 2, "south")
    for i in range(L):
        bp.set(7 + 2 * i, 2, 18, "furnace[facing=north,lit=false]")
    k.fill(5, 2, 9, 6, 2, 13, "sand")                                   # sand pile
    k.fill(5, 3, 10, 5, 3, 12, "sand")
    for i in range(L):
        rack(bp, 16, 2, 8 + i, "west")
    bp.set(16, 2, 14, "crafting_table")
    if L >= 4:  # glass art plinths
        for i, c in enumerate(["light_blue", "cyan", "lime", "magenta", "yellow"][:L]):
            bp.set(9 + i, 2, 6, "smooth_stone")
            bp.set(9 + i, 3, 6, f"{c}_stained_glass")
    k.landscape(trees=[(1, 1, 3), (23, 1, 3), (23, 21, 3)], lamps=[(8, 0), (14, 0)])
    return finish(k, (13, 2, 4), "blockhutglassblower")


# ============================================================================ concrete mixer
def build_concretemixer(L):
    k = Kit("concretemixer", "craftsmanship/luxury", L, (27, 26, 23))
    bp = k.bp
    k.ground(paved=[(2, 24, 15, 21)])
    k.box(2, 12, 3, 13, 1, 7)
    k.opening(7, 2, 3, 7, 3, 3)
    k.door(7, 2, 3, "south")
    k.opening(7, 2, 13, 7, 3, 13)
    for i in range(L):
        rack(bp, 3, 2, 5 + i, "east")
    bp.set(11, 2, 5, "crafting_table")
    k.lights(5, 10, 6, 11, 7, step=4)
    # mixing basin: 18+ water source blocks the mixer uses to harden concrete powder
    for x in range(4, 23):
        for z in range(16, 20):
            e = edge(x, z, 4, 22, 16, 19)
            bp.set(x, 1, z, k.W if e else "water[level=0]")
            if not e:
                bp.set(x, 0, z, "smooth_stone")
    # silos with coloured bands
    for i, cx in enumerate((16, 21)[: 1 + (L >= 2)]):
        h = 8 + 3 * L
        for x in range(cx - 3, cx + 4):
            for z in range(4, 11):
                d = math.hypot(x - cx, z - 7)
                if 1.8 <= d < 2.8:
                    for y in range(2, h):
                        bp.set(x, y, z, (["cyan", "light_gray", "white"][y % 3] + "_concrete") if y % 4 == 0 else k.W)
                elif d < 1.8:
                    bp.set(x, h, z, k.W)
    if L >= 3:  # conveyor bridge from silo to basin
        for z in range(11, 16):
            bp.set(16, 6, z, k.T)
            bp.set(16, 7, z, "rail[shape=north_south,waterlogged=false]")
    k.landscape(trees=[(1, 1, 3), (25, 1, 3)], lamps=[(5, 1), (9, 1)])
    return finish(k, (10, 2, 10), "blockhutconcretemixer")


# ============================================================================ crusher
def build_crusher(L):
    k = Kit("crusher", "craftsmanship/masonry", L, (23, 24, 21))
    bp = k.bp
    k.ground(paved=[(2, 20, 2, 18)])
    k.box(5, 15, 5, 15, 1, 7, wall="smooth_stone" if k.st.early else "calcite")
    k.opening(10, 2, 5, 10, 3, 5)
    k.door(10, 2, 5, "south")
    # inverted-pyramid hopper tower on top (wider each step)
    top = 7
    for t in range(min(L + 1, 5)):
        a, b = 8 - t, 12 + t
        y = top + 1 + t
        for x in range(a, b + 1):
            for z in range(a, b + 1):
                if edge(x, z, a, b, a, b):
                    bp.set(x, y, z, k.AC if t % 2 else k.W)
    for x in range(8 - min(L, 4), 13 + min(L, 4)):
        for z in range(8 - min(L, 4), 13 + min(L, 4)):
            bp.set(x, top + 1 + min(L, 4), z, k.band if edge(x, z, 8 - min(L, 4), 12 + min(L, 4), 8 - min(L, 4), 12 + min(L, 4)) else bp.get(x, top + 1 + min(L, 4), z))
    bp.set(10, 2, 10, "grindstone[face=floor,facing=north]")
    bp.set(9, 2, 10, "stonecutter[facing=north]")
    for i in range(L):
        rack(bp, 6, 2, 7 + i, "east")
    bp.set(14, 2, 14, "crafting_table")
    for x, z, m in ((3, 3, "gravel"), (18, 3, "sand"), (3, 17, "cobblestone"), (18, 17, "sand")):
        k.fill(x - 1, 2, z - 1, x + 1, 2, z + 1, m)
        bp.set(x, 3, z, m)
    k.lights(7, 13, 7, 13, 7, step=3)
    k.landscape(trees=[(0, 10, 3), (22, 10, 3)], lamps=[(8, 1), (12, 1)])
    return finish(k, (13, 2, 7), "blockhutcrusher")


# ============================================================================ sifter
def build_sifter(L):
    k = Kit("sifter", "craftsmanship/masonry", L, (25, 16, 21))
    bp = k.bp
    k.ground()
    tiers = min(L + 1, 4)
    for t in range(tiers):                                               # stepped open terraces
        x1, x2, z1, z2 = 2 + 2 * t, 22 - 2 * t, 3 + 2 * t, 18 - 2 * t
        fy = 1 + 2 * t
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                for y in range(1, fy + 1):
                    bp.set(x, y, z, k.W if edge(x, z, x1, x2, z1, z2) else ("smooth_stone" if y == fy else k.st.LIGHTGRAY))
        for x in range(x1, x2 + 1, 3):                                   # screens on each terrace
            for zz in (z1 + 1, z2 - 1):
                if t < tiers - 1 or zz == z2 - 1:
                    bp.set(x, fy + 1, zz, "iron_bars[east=true,north=false,south=false,waterlogged=false,west=true]")
    for t in range(1, tiers):                                            # steps between terraces
        bp.set(1 + 2 * t, 2 * t, 10, stairs(k, "east"))
    topy = 1 + 2 * (tiers - 1)
    cx, cz = 12, 10
    k.fill(cx - 2, topy + 1, cz - 2, cx + 2, topy + 4, cz + 2, k.G)       # sifting booth on top
    for x in range(cx - 2, cx + 3):
        for z in range(cz - 2, cz + 3):
            if not edge(x, z, cx - 2, cx + 2, cz - 2, cz + 2):
                for y in range(topy + 1, topy + 4):
                    bp.set(x, y, z, "air")
            bp.set(x, topy + 4, z, k.band if edge(x, z, cx - 2, cx + 2, cz - 2, cz + 2) else k.W)
    k.opening(cx - 2, topy + 1, cz, cx - 2, topy + 2, cz)
    for i in range(L):
        if i < 2:
            rack(bp, cx + 1, topy + 1, cz - 1 + i, "west")
    bp.set(cx - 1, topy + 1, cz + 1, "crafting_table")
    for x, m in ((4, "sand"), (20, "gravel")):
        k.fill(x, 2, 19, x + 1, 2, 19, m)
    hut = (cx + 1, topy + 1, cz + 1)
    k.landscape(trees=[(0, 0, 3), (24, 0, 3), (0, 20, 3), (24, 20, 3)], lamps=[(8, 1), (16, 1)])
    return finish(k, hut, "blockhutsifter")


# ============================================================================ stone smeltery
def build_stonesmeltery(L):
    k = Kit("stonesmeltery", "craftsmanship/masonry", L, (27, 18, 21))
    bp = k.bp
    k.ground(paved=[(11, 13, 0, 3)])
    k.box(6, 20, 4, 14, 1, 7)
    k.opening(12, 2, 4, 12, 3, 4)
    k.door(12, 2, 4, "south")
    for i in range(L):
        bp.set(8 + 2 * i, 2, 13, "furnace[facing=north,lit=false]")
    for i in range(L):
        rack(bp, 7, 2, 6 + i, "east")
    bp.set(19, 2, 6, "crafting_table")
    k.lights(9, 18, 7, 12, 7, step=4)
    # brick kiln domes either side
    for cx in ((3, 23) if L >= 2 else (3,)):
        for x in range(cx - 3, cx + 4):
            for z in range(6, 13):
                d = math.hypot(x - cx, z - 9)
                for y in range(2, 8):
                    r = 3.2 * math.sqrt(max(0, 1 - ((y - 2) / 5.5) ** 2))
                    if r - 1 <= d < r and bp.inside(x, y, z):
                        bp.set(x, y, z, "bricks")
                if d < 1:
                    bp.set(x, 1, z, "magma_block" if L >= 3 else "bricks")
        k.fill(cx, 8, 9, cx, 8 + L, 9, "bricks")
        bp.set(cx, 9 + L, 9, "campfire[facing=north,lit=false,signal_fire=false,waterlogged=false]")
    k.landscape(trees=[(0, 18, 3), (26, 18, 3)], lamps=[(9, 1), (15, 1)])
    return finish(k, (18, 2, 9), "blockhutstonesmeltery")


# ============================================================================ florist
def build_florist(L):
    k = Kit("florist", "agriculture/horticulture", L, (27, 16, 21))
    sh, bp = Shapes(k), k.bp
    k.ground(paved=[(0, 3, 9, 11)])
    sh.vault(3, 24, 3, 17, 4)
    for x in range(4, 24):
        for z in range(4, 17):
            bp.set(x, 1, z, k.st.floor(x, z))
    n = [4, 8, 12, 16, 20][L - 1]
    beds_ = [(x, z) for z in (6, 14) for x in range(6, 22, 2)] + [(x, z) for z in (9, 11) for x in range(12, 22, 2)]
    for x, z in beds_[:n]:
        bp.set(x, 1, z, "minecolonies:composted_dirt", NBT.Compound({"id": NBT.String("minecolonies:composteddirt"),
                                                                      "Item": NBT.String("")}))
    flowers = ["poppy", "dandelion", "cornflower", "allium", "azure_bluet", "oxeye_daisy", "lily_of_the_valley"]
    for i, x in enumerate(range(6, 22, 3)):
        bp.set(x, 2, 10, "air")
    for i in range(L):
        rack(bp, 5, 2, 7 + i, "east")
    bp.set(5, 2, 12, "barrel[facing=east,open=false]")
    if L >= 2:
        for i, x in enumerate(range(5, 24, 2)):
            bp.set(x, 1, 18, "grass_block[snowy=false]")
            bp.set(x, 2, 18, flowers[i % len(flowers)])
    k.landscape(trees=[(1, 1, 3), (25, 1, 3), (25, 19, 3)], lamps=[(1, 8), (1, 12)])
    return finish(k, (6, 2, 10), "blockhutflorist")


# ============================================================================ plantation
def build_plantation(L):
    k = Kit("plantation", "agriculture/horticulture", L, (29, 16, 29))
    sh, bp = Shapes(k), k.bp
    C = 14
    k.ground(paved=[(13, 15, 0, 28), (0, 28, 13, 15)])
    sh.drum(C, C, 4, 1, 6, doors=(270, 90), glass_every=45)
    for i in range(min(L, 4)):
        rack(bp, C - 2 + i, 2, C + 2, "north")
    hut = (C + 2, 2, C - 2)
    # cactus beds (NW): sand, tagged `cactus` on the sand, gaps between plants
    n_cactus = [9, 12, 14, 16, 18][L - 1]
    spots = [(x, z) for x in range(2, 12, 2) for z in range(2, 12, 2)]
    for x, z in spots[:n_cactus]:
        bp.set(x, 1, z, "sand")
        k.tag((x, 1, z), "cactus")
    # bamboo grove (NE): coarse dirt, tagged `bamboo`
    for i, (x, z) in enumerate([(x, z) for x in range(17, 27) for z in range(2, 12, 2)][:20]):
        bp.set(x, 1, z, "coarse_dirt")
        k.tag((x, 1, z), "bamboo")
    # sugar cane (south): sand rows beside water channels, tagged `sugar`
    n_sugar = [10, 12, 15, 18, 20][L - 1]
    cells = []
    for z0 in (18, 22, 26):
        for x in range(2, 27):
            if 12 <= x <= 16:
                continue
            bp.set(x, 1, z0, "water[level=0]")
            cells += [(x, z0 - 1)]
    for x, z in cells[:n_sugar]:
        bp.set(x, 1, z, "sand")
        k.tag((x, 1, z), "sugar")
    if L >= 3:
        k.railing_ring(0, 28, 0, 28, 2, skip={(14, 0), (14, 28), (0, 14), (28, 14)})
    if L >= 4:
        for x, z in ((C - 3, C - 3), (C + 3, C - 3), (C - 3, C + 3), (C + 3, C + 3)):
            bp.set(x, 6, z, "sea_lantern")
    return finish(k, hut, "blockhutplantation")


# ============================================================================ composter
def build_composter(L):
    k = Kit("composter", "agriculture/horticulture", L, (21, 14, 21))
    sh, bp = Shapes(k), k.bp
    C = 10
    k.ground(paved=[(9, 11, 0, 3)])
    sh.drum(C, C, 7, 1, 6, doors=(270,), glass_every=30, roof=False)
    sh.disc(C, C, 7, 6, lambda x, z: k.band if math.hypot(x - C, z - C) >= 6.5 else "grass_block[snowy=false]")
    for a in range(0, 360, 40):                                          # green roof planting
        x, z = round(C + 4 * math.cos(math.radians(a))), round(C + 4 * math.sin(math.radians(a)))
        bp.set(x, 7, z, "fern")
    for i in range(L):                                                   # compost barrels ring
        a = math.radians(30 + i * 60)
        x, z = round(C + 4 * math.cos(a)), round(C + 4 * math.sin(a))
        bp.set(x, 2, z, f"minecolonies:barrel_block[facing=north,variant=0perc]")
    for i in range(L):
        rack(bp, C - 2 + i, 2, C - 4, "south")
    bp.set(C + 4, 2, C - 2, "composter[level=0]")
    hut = (C, 2, C)
    k.landscape(trees=[(1, 1, 3), (19, 1, 3), (1, 19, 3), (19, 19, 3)], lamps=[(8, 1), (12, 1)])
    return finish(k, hut, "blockhutcomposter")


# ============================================================================ beekeeper
def build_beekeeper(L):
    k = Kit("beekeeper", "agriculture/husbandry", L, (23, 16, 23))
    bp = k.bp
    C = 11
    k.ground()
    # hexagon pavilion (honeycomb roof pattern)
    def in_hex(x, z, r):
        dx, dz = abs(x - C), abs(z - C)
        return dz <= r * 0.87 and dx + dz * 0.58 <= r
    for x in range(C - 7, C + 8):
        for z in range(C - 7, C + 8):
            if in_hex(x, z, 6):
                inner = in_hex(x, z, 5)
                bp.set(x, 1, z, k.st.floor(x, z))
                bp.set(x, 6, z, ("yellow_concrete" if (x + 2 * z) % 3 == 0 else k.W) if inner else k.band)
                if not inner:
                    for y in range(2, 6):
                        door = x == C and z < C and y <= 3
                        bp.set(x, y, z, "air" if door else (k.G if y in (3, 4) else k.W))
    for i in range(min(L, 3)):
        rack(bp, C - 1 + i, 2, C + 3, "north")
    bp.set(C + 3, 2, C, "crafting_table")
    hut = (C - 3, 2, C)
    # meadow with hives on posts
    hives = [(3, 3), (19, 3), (19, 19)][: [1, 1, 2, 2, 3][L - 1]]
    for x, z in hives:
        bp.set(x, 2, z, k.T)
        bp.set(x, 3, z, "beehive[facing=south,honey_level=0]")
    flowers = ["cornflower", "dandelion", "poppy", "allium", "oxeye_daisy"]
    for x in range(1, 22, 3):
        for z in (1, 21):
            bp.set(x, 2, z, flowers[(x + z) % 5])
    if L >= 4:
        for x in range(2, 21, 4):
            for z in (6, 16):
                bp.set(x, 2, z, "flowering_azalea")
    k.landscape(trees=[(1, 11, 3), (21, 11, 3)], lamps=[(9, 1), (13, 1)])
    return finish(k, hut, "blockhutbeekeeper")


# ============================================================================ chicken herder
def build_chickenherder(L):
    k = Kit("chickenherder", "agriculture/husbandry", L, (25, 14, 23))
    bp = k.bp
    k.ground()
    pen(k, 1, 23, 9, 21, (12, 2, 9))
    for i, cx in enumerate((5, 12, 19)[: 1 + (L >= 2) + (L >= 4)]):      # dome coop pods
        for x in range(cx - 3, cx + 4):
            for z in range(12, 19):
                d = math.hypot(x - cx, z - 15)
                for y, r in ((2, 2.8), (3, 2.8), (4, 2.2), (5, 1.3)):
                    if r - 1 <= d < r or (y == 5 and d < r):
                        door = x == cx and z == 12 and y <= 3
                        bp.set(x, y, z, "air" if door else (k.W if y in (2, 5) else k.G))
        bp.set(cx, 2, 15, "hay_block[axis=y]")
    k.box(5, 19, 2, 7, 1, 6)
    k.opening(12, 2, 2, 12, 3, 2)
    k.door(12, 2, 2, "south")
    k.opening(12, 2, 7, 12, 3, 7)
    for i in range(L):
        rack(bp, 6 + i, 2, 6, "north")
    bp.set(18, 2, 6, "crafting_table")
    trough(k, 16, 17, 10)
    return finish(k, (16, 2, 3), "blockhutchickenherder")


# ============================================================================ cowboy
def build_cowboy(L):
    k = Kit("cowboy", "agriculture/husbandry", L, (29, 16, 25))
    sh, bp = Shapes(k), k.bp
    k.ground()
    sh.vault(2, 13, 4, 16, 4)
    for x in range(3, 13):
        for z in range(5, 16):
            bp.set(x, 1, z, k.st.floor(x, z))
    for i in range(L):
        rack(bp, 4 + i, 2, 15, "north")
    bp.set(11, 2, 15, "crafting_table")
    for z in (6, 8, 13):
        bp.set(4, 2, z, "hay_block[axis=y]")
    pen(k, 14, 27, 2, 22, (14, 2, 10))
    k.opening(13, 2, 10, 13, 3, 10)
    trough(k, 20, 22, 4)
    if L >= 3:
        trough(k, 20, 22, 20)
        for x in (25, 26):
            bp.set(x, 2, 12, "hay_block[axis=y]")
    if L >= 4:
        k.canopy(22, 27, 14, 21, 5, columns=[(22, 14), (27, 14)])
    return finish(k, (11, 2, 6), "blockhutcowboy")


# ============================================================================ shepherd
def build_shepherd(L):
    k = Kit("shepherd", "agriculture/husbandry", L, (27, 14, 27))
    bp = k.bp
    C = 13
    k.ground()
    for x in range(27):                                                  # round stone fold
        for z in range(27):
            d = math.hypot(x - C, z - C)
            if 10.5 <= d < 11.5 and not (8 <= x <= 18 and z <= 9):
                gap = abs(x - C) <= 0 and z > C
                if not gap:
                    bp.set(x, 2, z, "stone_bricks" if k.st.early else "calcite")
                    put(bp, x, 3, z, k.st.railing)
                else:
                    bp.set(x, 2, z, GATE.replace("north", "south"))
    # shelter with a sloped green roof on the north side of the fold
    k.box(8, 18, 3, 9, 1, 6)
    for x in range(8, 19):
        for z in range(3, 10):
            bp.set(x, 6, z, "grass_block[snowy=false]" if not edge(x, z, 8, 18, 3, 9) else k.band)
    k.opening(13, 2, 9, 13, 3, 9)
    k.opening(15, 2, 3, 15, 3, 3)
    k.door(15, 2, 3, "south")
    for i in range(L):
        rack(bp, 9 + i, 2, 4, "south")
    bp.set(17, 2, 4, "loom[facing=south]")
    bp.set(17, 2, 5, "crafting_table")
    bp.set(9, 2, 8, "hay_block[axis=y]")
    trough(k, 12, 14, 19)
    return finish(k, (16, 2, 7), "blockhutshepherd")


# ============================================================================ swineherder
def build_swineherder(L):
    k = Kit("swineherder", "agriculture/husbandry", L, (29, 16, 21))
    sh, bp = Shapes(k), k.bp
    k.ground()
    k.box(2, 26, 2, 8, 1, 4, roof=False)
    for x in range(3, 26):
        for z in range(3, 8):
            bp.set(x, 4, z, "air")
    sh.sawtooth(2, 26, 2, 8, 4, tooth=4)
    k.opening(14, 2, 2, 14, 3, 2)
    k.door(14, 2, 2, "south")
    for x in range(4, 26, 4):                                            # sty doors to the yard
        k.opening(x, 2, 8, x, 3, 8)
    for i in range(L):
        rack(bp, 3 + i // 4, 2, 3 + i % 4, "east")
    bp.set(25, 2, 3, "crafting_table")
    bp.set(24, 2, 3, "composter[level=0]")
    pen(k, 1, 27, 9, 19, (14, 2, 19), floor="mud" if not k.st.early else "dirt")
    for x in range(3, 26, 6):
        bp.set(x, 2, 15, "hay_block[axis=y]")
    trough(k, 12, 16, 17)
    return finish(k, (20, 2, 4), "blockhutswineherder")


# ============================================================================ rabbit hutch
def build_rabbithutch(L):
    k = Kit("rabbithutch", "agriculture/husbandry", L, (27, 14, 19))
    bp = k.bp
    k.ground()
    # earth-sheltered mound: a low dome covered in grass with round windows
    C = (8, 9)
    for x in range(0, 17):
        for z in range(1, 18):
            d = math.hypot((x - C[0]) / 1.0, (z - C[1]) / 1.0)
            h = 1 + int(5.5 * math.sqrt(max(0.0, 1 - (d / 7.5) ** 2)))
            if d < 7.5:
                for y in range(2, h + 1):
                    shell = y == h or d > 6.3
                    bp.set(x, y, z, ("grass_block[snowy=false]" if y == h else "dirt") if shell else "air")
                bp.set(x, 1, z, k.st.floor(x, z))
    for (x, z) in ((C[0], 2), (2, C[1]), (C[0] + 6, 5)):
        k.fill(x, 3, z, x, 4, z, "glass")
    k.opening(C[0], 2, 2, C[0], 3, 3)
    k.opening(15, 2, C[1], 16, 3, C[1])
    for i in range(L):
        rack(bp, 5 + i, 2, 13, "north")
    bp.set(11, 2, 12, "crafting_table")
    bp.set(C[0], 5, C[1], "lantern[hanging=true,waterlogged=false]")
    pen(k, 17, 26, 1, 17, (17, 2, 9))
    for x, z in ((20, 4), (23, 13), (21, 9)):
        bp.set(x, 2, z, "hay_block[axis=y]")
    for x in range(18, 26, 2):
        bp.set(x, 2, 15, "carrots[age=7]")
        bp.set(x, 1, 15, "farmland[moisture=7]")
    return finish(k, (C[0] + 2, 2, C[1] - 2), "blockhutrabbithutch")


# ============================================================================ plantation fields
def plantation_field(kind, plant_tag, soil, size=(13, 11)):
    """Plantation field blueprint in the official format: anchor + `<kind>_field` + plant tags."""
    sx, sz = size
    k = Kit(f"neo{kind}", "agriculture/fields", 4, (sx, 6, sz))
    bp = k.bp
    bp.fill(0, 0, 0, sx - 1, 0, sz - 1, SOLID)
    anchor = (sx // 2, 1, 0)
    tags = {anchor: [f"{kind}_field"]}
    for x in range(sx):
        for z in range(sz):
            e = edge(x, z, 0, sx - 1, 0 if kind != "kelp" else 1, sz - 1)
            if kind == "kelp" and z == 0:                                 # walkway in front of the tank
                bp.set(x, 1, z, k.W)
            elif e and kind == "kelp":                                      # tank walls hold the water
                bp.set(x, 1, z, k.W)
                for y in (2, 3, 4):
                    bp.set(x, y, z, "glass")
                bp.set(x, 5, z, k.band)
            elif e:
                bp.set(x, 1, z, k.W)
                put(bp, x, 2, z, k.st.railing)
            elif kind in ("sugar",) and z % 3 == 1:
                bp.set(x, 1, z, "water[level=0]")
            elif kind == "kelp":
                bp.set(x, 1, z, soil)
                for y in (2, 3, 4):
                    bp.set(x, y, z, "water[level=0]")
                tags[(x, 1, z)] = [plant_tag]
            elif (x + z) % 2 == 0 or kind in ("sugar",):
                bp.set(x, 1, z, soil)
                tags[(x, 1, z)] = [plant_tag]
            else:
                bp.set(x, 1, z, "smooth_stone" if kind != "bamboo" else soil)
    bp.set(*anchor, "minecolonies:blockhutplantationfield[facing=north,mirror=false]")
    if kind != "kelp":
        bp.set(anchor[0], 2, anchor[2], "air")
    connect_panes(bp)

    def pos(x, y, z):
        return NBT.Compound({"x": NBT.Int(x), "y": NBT.Int(y), "z": NBT.Int(z)})
    ax, ay, az = anchor
    path = f"agriculture/fields/neo{kind}.blueprint"
    te = NBT.Compound({
        "id": NBT.String("minecolonies:plantationfield"), "path": NBT.String(path), "Item": NBT.String(""),
        "mirror": NBT.Byte(0), "rotation": NBT.Int(0), "name": NBT.String(f"neo{kind}"), "pack": NBT.String(PACK_NAME),
        "blueprintDataProvider": NBT.Compound({
            "corner1": pos(-ax, -ay, -az), "corner2": pos(sx - 1 - ax, 5 - ay, sz - 1 - az),
            "path": NBT.String(path), "schematicName": NBT.String(f"neo{kind}"), "pack": NBT.String(PACK_NAME),
            "posTagMap": NBT.List[NBT.Compound]([
                NBT.Compound({"tagPos": pos(x - ax, y - ay, z - az),
                              "tagNameList": NBT.List[NBT.Compound]([NBT.Compound({"tagName": NBT.String(n)}) for n in ns])})
                for (x, y, z), ns in sorted(tags.items())]),
        }),
    })
    bp.tile_entities[anchor] = te
    bp.primary_offset = anchor
    bp.name = f"neo{kind}.blueprint"
    bp.architects = ["Neoterra"]
    return bp


HUTS = {
    "craftsmanship/carpentry/fletcher": build_fletcher,
    "craftsmanship/luxury/cookery": build_cookery,
    "craftsmanship/luxury/alchemist": build_alchemist,
    "craftsmanship/luxury/dyer": build_dyer,
    "craftsmanship/luxury/glassblower": build_glassblower,
    "craftsmanship/luxury/concretemixer": build_concretemixer,
    "craftsmanship/masonry/crusher": build_crusher,
    "craftsmanship/masonry/sifter": build_sifter,
    "craftsmanship/masonry/stonesmeltery": build_stonesmeltery,
    "agriculture/horticulture/florist": build_florist,
    "agriculture/horticulture/plantation": build_plantation,
    "agriculture/horticulture/composter": build_composter,
    "agriculture/husbandry/beekeeper": build_beekeeper,
    "agriculture/husbandry/chickenherder": build_chickenherder,
    "agriculture/husbandry/cowboy": build_cowboy,
    "agriculture/husbandry/shepherd": build_shepherd,
    "agriculture/husbandry/swineherder": build_swineherder,
    "agriculture/husbandry/rabbithutch": build_rabbithutch,
}


def build_all(root: Path, only=()):
    for key, fn in HUTS.items():
        if only and not any(o in key for o in only):
            continue
        cat, name = key.rsplit("/", 1)
        (root / cat).mkdir(parents=True, exist_ok=True)
        for lvl in range(1, 6):
            fn(lvl).save(root / cat / f"{name}{lvl}.blueprint")
        print(f"{key}: 5 levels")
    if not only:
        f = root / "agriculture/fields"
        f.mkdir(parents=True, exist_ok=True)
        plantation_field("bamboo", "bamboo", "coarse_dirt").save(f / "neobamboo.blueprint")
        plantation_field("cactus", "cactus", "sand").save(f / "neocactus.blueprint")
        plantation_field("sugar", "sugar", "sand").save(f / "neosugar.blueprint")
        plantation_field("kelp", "kelp", "dirt", size=(11, 10)).save(f / "neokelp.blueprint")
        print("4 plantation fields")


if __name__ == "__main__":
    build_all(Path(sys.argv[1]), sys.argv[2:])
