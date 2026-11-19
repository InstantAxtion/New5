"""
Neoterra military buildings, levels 1-5 (category military/):

  guardtower      (blockhutguardtower)     slim tower that grows taller each level, 2 beds,
                                           ladder up to a lookout (glass pod from L4).
  archery         (blockhutarchery)        bunk house (2 beds per level) + shooting range with one
                                           target block and one `work` firing spot per level.
  combatacademy   (blockhutcombatacademy)  bunk house (2 beds per level) + sand arena with hay
                                           training dummies (1/2/3/6/9 like the official packs).
  stable          (blockhutstable)         stalls tagged `stall` (2 per level) with hay, paddock,
                                           stable-hand beds.
  barracks        (blockhutbarracks)       HQ + courtyard; each level adds a child barracks tower
                                           hut (max 4) in a corner, like the official barracks.
  barrackstower   (blockhutbarrackstower)  the child tower: one storey with 2 beds per level
                                           (2-10 beds). Tagged invisible; upgrade it from its hut.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit import Kit, SUBST, edge, put, rack, tree, planter, bed  # noqa: E402


def bunkhouse(k, x1, x2, z1, z2, beds, door_x):
    """Single-storey bunk house: beds in rows from the back wall (4 per row), door on the north
    side, furnace + barrel by the front-right corner, front strip kept free for the hut/door."""
    bp = k.bp
    k.box(x1, x2, z1, z2, 1, 6)
    k.opening(door_x, 2, z1, door_x, 3, z1)
    k.door(door_x, 2, z1, "south")
    spots = [(x, z) for z in (z2 - 2, z2 - 5, z2 - 8) for x in range(x1 + 1, x2 - 2, 2)]
    for x, z in spots[:beds]:
        bed(bp, x, 2, z, "south")
    bp.set(x2 - 1, 2, z1 + 2, "furnace[facing=west,lit=false]")
    bp.set(x2 - 1, 2, z1 + 3, "barrel[facing=west,open=false]")
    k.lights(x1 + 2, x2 - 2, z1 + 2, z2 - 2, 6, step=3)


# ============================================================================ guard tower
def build_guardtower(L):
    k = Kit("guardtower", "military", L, (11, 30, 11))
    bp = k.bp
    k.ground(paved=[(4, 6, 0, 1)])
    height = [12, 15, 18, 21, 24][L - 1]
    k.box(2, 8, 2, 8, 1, height, windows=True)
    k.opening(5, 2, 2, 5, 3, 2)
    k.door(5, 2, 2, "south")
    for f in range(5, height, 5):                                        # intermediate floors
        for x in range(3, 8):
            for z in range(3, 8):
                bp.set(x, f, z, k.st.floor(x, z))
    for y in range(2, height + 1):                                       # ladder to the lookout
        bp.set(7, y, 7, "ladder[facing=north,waterlogged=false]")
    bed(bp, 3, 2, 6, "south")
    bed(bp, 5, 2, 6, "south")
    bp.set(3, 2, 3, "barrel[facing=up,open=false]")
    # lookout platform cantilevered around the top
    for x in range(1, 10):
        for z in range(1, 10):
            bp.set(x, height, z, (k.glow or k.band) if edge(x, z, 1, 9, 1, 9) else k.D)
    bp.set(7, height, 7, "ladder[facing=north,waterlogged=false]")
    k.railing_ring(1, 9, 1, 9, height + 1)
    if L >= 4:  # glass observation pod over the lookout
        for x in range(3, 8):
            for z in range(3, 8):
                if edge(x, z, 3, 7, 3, 7) and (x, z) != (5, 3):
                    for y in (height + 1, height + 2):
                        bp.set(x, y, z, k.G)
                bp.set(x, height + 3, z, k.W if edge(x, z, 3, 7, 3, 7) else "glass")
        bp.set(5, height + 3, 5, "sea_lantern")
    if L >= 5:
        k.mast(5, height + 4, 5)
    hut = (4, 2, 3)
    k.landscape(trees=[(0, 0)], lamps=[(9, 0)])
    return k.finish_hut(hut, "blockhutguardtower")


# ============================================================================ archery
def build_archery(L):
    k = Kit("archery", "military", L, (29, 18, 21))
    bp = k.bp
    k.ground(paved=[(12, 27, 3, 19)])
    bunkhouse(k, 1, 11, 4, 18, 2 * L, 6)
    # range: firing line at x13, targets on a back wall at x27
    for z in range(3, 20):
        for y in (2, 3, 4):
            bp.set(27, y, z, k.W)
    for i in range(L):
        z = 5 + 3 * i
        bp.set(27, 3, z, "target[power=0]")
        bp.set(26, 2, z, "air")
        k.tag((13, 2, z), "work")
        k.set(12, 2, z, k.st.counter)                                    # firing stand
    k.opening(11, 2, 12, 11, 3, 12)                                      # bunk house -> range
    k.railing_ring(12, 27, 2, 20, 2, skip={(12, 12)})
    if L >= 2:
        k.canopy(12, 16, 3, 19, 6, columns=[(16, 3), (16, 19)])
    if L >= 3:
        bp.set(9, 2, 6, "fletching_table")
        bp.set(8, 2, 6, "barrel[facing=up,open=false]")
    if L >= 5:
        for z in range(3, 20, 4):
            bp.set(27, 5, z, "sea_lantern")
    hut = (3, 2, 6)
    k.landscape(trees=[(0, 1), (0, 18)], lamps=[(13, 0), (26, 0)])
    return k.finish_hut(hut, "blockhutarchery")


# ============================================================================ combat academy
def build_combatacademy(L):
    k = Kit("combatacademy", "military", L, (29, 18, 25))
    bp = k.bp
    k.ground()
    bunkhouse(k, 1, 11, 6, 18, 2 * L, 6)
    # arena (sand) with training dummies
    C = (20, 12)
    for x in range(12, 29):
        for z in range(2, 23):
            d = math.hypot(x - C[0], z - C[1])
            if d < 8.5:
                bp.set(x, 1, z, "sand" if d < 7.5 else k.W)
            if 7.5 <= d < 8.5 and not (abs(z - 15) <= 1 and x < C[0]):
                put(bp, x, 2, z, k.st.railing)
    dummies = [(C[0] + round(4 * math.cos(math.radians(a * 40))), C[1] + round(4 * math.sin(math.radians(a * 40))))
               for a in range(9)]
    for x, z in dummies[: [1, 2, 3, 6, 9][L - 1]]:
        bp.set(x, 2, z, "hay_block[axis=y]")
        bp.set(x, 3, z, "carved_pumpkin[facing=west]")
    bp.set(*(C[0], 2, C[1]), "air")
    k.opening(11, 2, 15, 11, 3, 15)                                      # bunk house -> arena
    if L >= 2:  # spectator seats along the west side of the arena
        for z in (8, 10, 14, 16):
            k.seat(13, 2, z, "west")
    if L >= 3:
        bp.set(9, 2, 8, "grindstone[face=floor,facing=north]")
        bp.set(8, 2, 8, "anvil[facing=north]")
    if L >= 5:
        for a in range(0, 360, 45):
            x, z = C[0] + round(8 * math.cos(math.radians(a))), C[1] + round(8 * math.sin(math.radians(a)))
            if 0 <= x < 29:
                bp.set(x, 1, z, "sea_lantern")
    hut = (3, 2, 8)
    k.landscape(trees=[(0, 1), (0, 22)], lamps=[(13, 0), (27, 0)])
    return k.finish_hut(hut, "blockhutcombatacademy")


# ============================================================================ stable
def build_stable(L):
    k = Kit("stable", "military", L, (21, 16, 29))
    bp = k.bp
    k.ground(paved=[(8, 12, 0, 3)])
    X1, X2, Z1, Z2 = 2, 18, 4, 17
    k.box(X1, X2, Z1, Z2, 1, 7)
    k.opening(9, 2, Z1, 11, 4, Z1)                                       # wide stable door
    k.opening(9, 2, Z2, 11, 4, Z2)                                       # to the paddock
    # stalls along both long walls: tagged `stall`, with hay
    stalls = [(x, z) for z in (6, 13) for x in (4, 7, 13, 16)] + [(x, z) for z in (6, 13) for x in (10,)]
    for i, (x, z) in enumerate(stalls[: 2 * L]):
        side = 1 if z < 10 else -1
        for dz in (0, side, 2 * side):
            put(bp, x - 1, 2, z + dz, k.st.railing)                     # stall dividers
        bp.set(x, 2, z - side, "hay_block[axis=y]")
        k.tag((x, 2, z + side), "stall")
    beds = [2, 4, 4, 6, 8][L - 1]
    k.lights(5, 15, 7, 15, 7, step=5)
    # stable-hand loft for the beds
    k.box(X1, X2, Z1, Z2, 7, 12, glass_front=False)
    k.stairs(17, 16, 2, 6, "north", cut_y=7)
    for i in range(beds):
        bed(bp, 4 + 2 * (i % 6), 8, 14 if i < 6 else 6, "south" if i < 6 else "north")
    bp.set(4, 8, 9, "barrel[facing=up,open=false]")
    k.lights(6, 14, 8, 14, 12, step=4)
    # paddock behind the stable
    for x in range(1, 20):
        for z in range(18, 28):
            bp.set(x, 1, z, "grass_block[snowy=false]")
    k.railing_ring(1, 19, 18, 28, 2, skip={(9, 18), (10, 18), (11, 18)})
    if L >= 3:
        bp.set(15, 2, 24, "water_cauldron[level=3]")
        for x in (4, 5):
            bp.set(x, 2, 26, "hay_block[axis=y]")
    hut = (16, 2, 9)
    k.landscape(trees=[(0, 1), (20, 1)], lamps=[(7, 0), (13, 0)])
    return k.finish_hut(hut, "blockhutstable")


# ============================================================================ barracks + towers
TOWER = 7            # tower footprint (7x7)
TOWER_H = 24         # tower blueprint height
CORNERS = [(0, 0), (20, 0), (0, 20), (20, 20)]


def build_barrackstower(L):
    """Child tower: one storey (2 beds) per level, ladder up to a lookout."""
    k = Kit("barrackstower", "military", L, (TOWER, TOWER_H, TOWER))
    bp = k.bp
    k.ground()
    top = 1 + 4 * L
    k.box(0, 6, 0, 6, 1, top, glass_front=False)
    for x, z in ((3, 0), (3, 6), (0, 3), (6, 3)):                         # door on every side
        k.opening(x, 2, z, x, 3, z)
    for s in range(L):
        f = 1 + 4 * s
        if s > 0:
            for x in range(1, 6):
                for z in range(1, 6):
                    bp.set(x, f, z, k.st.floor(x, z))
        bed(bp, 1, f + 1, 4, "south")
        bed(bp, 4, f + 1, 4, "south")
        k.st.ceiling_light(bp, 3, f + 4, 3)
    for y in range(2, top + 1):
        bp.set(5, y, 1, "ladder[facing=south,waterlogged=false]")
    k.railing_ring(0, 6, 0, 6, top + 1)
    if L >= 4:
        bp.set(3, top + 1, 3, "sea_lantern")
    hut = (2, 2, 2)
    return k.finish_hut(hut, "blockhutbarrackstower", invisible=True)


def build_barracks(L):
    k = Kit("barracks", "military", L, (27, TOWER_H + 2, 27))
    bp = k.bp
    k.ground(paved=[(7, 19, 0, 26), (0, 26, 7, 19)])
    # HQ in the middle
    X1, X2, Z1, Z2 = 9, 17, 9, 17
    k.box(X1, X2, Z1, Z2, 1, 7, chamfer=True)
    k.opening(13, 2, Z1, 13, 3, Z1)
    k.door(13, 2, Z1, "south")
    k.set(11, 2, 14, k.st.counter)
    k.set(12, 2, 14, k.st.counter)
    bp.set(15, 2, 15, "anvil[facing=north]")
    bp.set(15, 2, 14, "grindstone[face=floor,facing=west]")
    bp.set(10, 2, 16, "barrel[facing=up,open=false]")
    bp.set(11, 2, 16, "barrel[facing=up,open=false]")
    if L >= 2:
        bp.set(14, 2, 16, "smithing_table")
    k.lights(11, 15, 11, 15, 7, step=4)
    hut = (15, 2, 11)
    # tower slots: leave them to the child towers, add one tower hut per level (max 4)
    for i, (cx, cz) in enumerate(CORNERS):
        for x in range(cx, cx + TOWER):
            for z in range(cz, cz + TOWER):
                for y in range(1, TOWER_H + 2):
                    bp.set(x, y, z, SUBST)
        if i < min(L, 4):
            k.child((cx + 2, 2, cz + 2), "blockhutbarrackstower", "military/barrackstower0.blueprint")
    # courtyard training: targets + dummies
    for z in (4, 22):
        bp.set(13, 2, z, "target[power=0]")
    if L >= 3:  # perimeter wall between the towers with railing on top
        for x in range(7, 20):
            for z in (0, 26):
                if not (z == 0 and 11 <= x <= 15):
                    k.fill(x, 2, z, x, 3, z, k.W)
                    put(bp, x, 4, z, k.st.railing)
        for z in range(7, 20):
            for x in (0, 26):
                k.fill(x, 2, z, x, 3, z, k.W)
                put(bp, x, 4, z, k.st.railing)
    if L >= 5:
        k.mast(13, 8, 13)
    k.landscape(trees=[(9, 4), (17, 4)], lamps=[(10, 1), (16, 1)])
    return k.finish_hut(hut, "blockhutbarracks")


BUILDERS = {"military/guardtower": build_guardtower,
            "military/barracks": build_barracks, "military/barrackstower": build_barrackstower}

def barracks_preview(L):
    """Barracks with its towers built at the same level (preview / checks only)."""
    b = build_barracks(L)
    for cx, cz in CORNERS[: min(L, 4)]:
        t = build_barrackstower(L)
        for x in range(t.sx):
            for y in range(1, t.sy):
                for z in range(t.sz):
                    b.grid[y][cz + z][cx + x] = t.grid[y][z][x]
                    if (x, y, z) in t.tile_entities:
                        b.tile_entities[(cx + x, y, cz + z)] = t.tile_entities[(x, y, z)]
    for y in range(b.sy):
        for z in range(b.sz):
            for x in range(b.sx):
                if b.grid[y][z][x] == SUBST:
                    b.grid[y][z][x] = "minecraft:air"
    return b


if __name__ == "__main__":
    root = Path(sys.argv[1])
    for key, fn in BUILDERS.items():
        cat, name = key.rsplit("/", 1)
        (root / cat).mkdir(parents=True, exist_ok=True)
        for lvl in range(1, 6):
            fn(lvl).save(root / cat / f"{name}{lvl}.blueprint")
        print(f"{key}: 5 levels")
    if len(sys.argv) > 2:
        prev = Path(sys.argv[2])
        prev.mkdir(parents=True, exist_ok=True)
        for lvl in range(1, 6):
            barracks_preview(lvl).save(prev / f"barracks{lvl}_furnished.blueprint")
