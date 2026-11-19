"""
Neoterra update 1 – colony essentials (all huts levels 1-5 unless noted; cheap 1-3, premium 4-5).

  decorations/supplies/supplycamp, camp      Pod camp: inflatable-look dome pods round a crate deck
  decorations/supplies/supplyship, ship      Catamaran with a glass bridge (floats on 3 water layers)
  fundamentals/miner                         Mine Head: glass hall + lattice headframe tower over the
                                             shaft (ladder/cobble tags where the miner starts digging)
  infrastructure/mineshafts/miner*           mine nodes re-skinned from the official tunnel layouts
  agriculture/horticulture/farmer            Agri-Dome: glass dome barn + silo, racks, composters
  decorations/fields/neofield, neofieldlarge scarecrow fields (9x9 / 13x13 farmland, irrigated)
  fundamentals/hospital                      Cross Clinic: plus-shaped wards, 2 red beds per level
  fundamentals/tavern (levels 1-3)           A-Frame Lodge: glass-gabled A-frame, bar + 8 beds
  agriculture/husbandry/fisherman            Marina: pond with jetty and fishing spots, wave canopy
  craftsmanship/metallurgy/smeltery          Foundry: tall block with glowing twin stacks, 1 furnace/level
  craftsmanship/metallurgy/blacksmith        Forge: shed-roof hall with a forge hood, anvil court
  craftsmanship/luxury/baker                 Bakehouse: rounded loaf vault + cafe terrace, 1 furnace/level
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

from nbtlib import tag as NBT

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from kit import Kit, Shapes, SUBST, edge, put, rack, tree, planter, bed, in_octagon  # noqa: E402
from common import (Blueprint, Style, hut_te, connect_panes, street_lamp, PACK_NAME,  # noqa: E402
                    parse_state, format_state)
from blueprint import load  # noqa: E402

SOLID = "structurize:blocksolidsubstitution"
FLUID = "structurize:blockfluidsubstitution"
REF = Path(__file__).resolve().parent / "ref"


def stairs(k, facing, half="bottom"):
    return f"{k.st.SEAT}[facing={facing},half={half},shape=straight,waterlogged=false]"


def table(k, x, y, z, seats=("west", "east")):
    k.set(x, y, z, k.st.counter)
    for side in seats:
        dx, dz = {"west": (-1, 0), "east": (1, 0), "north": (0, -1), "south": (0, 1)}[side]
        k.seat(x + dx, y, z + dz, side)


def tag_anchor_te(name, size, anchor, tags):
    ax, ay, az = anchor
    sx, sy, sz = size

    def pos(x, y, z):
        return NBT.Compound({"x": NBT.Int(x), "y": NBT.Int(y), "z": NBT.Int(z)})
    tl = [NBT.Compound({"tagPos": pos(x - ax, y - ay, z - az),
                        "tagNameList": NBT.List[NBT.Compound]([NBT.Compound({"tagName": NBT.String(n)}) for n in ns])})
          for (x, y, z), ns in sorted(tags.items())]
    return NBT.Compound({
        "id": NBT.String("structurize:tagsubstitution"),
        "blueprintDataProvider": NBT.Compound({
            "corner1": pos(-ax, -ay, -az), "corner2": pos(sx - 1 - ax, sy - 1 - ay, sz - 1 - az),
            "path": NBT.String(""), "schematicName": NBT.String(name), "pack": NBT.String(""),
            "posTagMap": NBT.List[NBT.Compound](tl),
        }),
    })


def finish_tag_anchor(k, name, anchor, ground_y, invisible):
    connect_panes(k.bp)
    tags = {(0, ground_y, 0): ["groundlevel"]}
    if invisible:
        tags.setdefault(anchor, []).append("invisible")
    for p, ns in k.tags.items():
        tags.setdefault(p, []).extend(ns)
    k.bp.name = f"{name}.blueprint"
    k.bp.set(*anchor, "structurize:blocktagsubstitution", tag_anchor_te(name, (k.sx, k.sy, k.sz), anchor, tags))
    k.bp.primary_offset = anchor
    k.bp.architects = ["Neoterra"]
    return k.bp


# ============================================================================ supply camp
def build_supplycamp(name="supplycamp", invisible=True):
    k = Kit(name, "decorations/supplies", 4, (19, 9, 17))
    sh, bp = Shapes(k), k.bp
    bp.fill(0, 0, 0, 18, 0, 16, SOLID)                                   # ground layer (must be solid)
    for x in range(19):
        for z in range(17):
            bp.set(x, 1, z, "grass_block[snowy=false]")
    for x in range(5, 14):                                               # crate deck
        for z in range(5, 12):
            bp.set(x, 1, z, k.W if edge(x, z, 5, 13, 5, 11) else k.D)
    # three dome pods
    for cx, cz in ((3, 3), (15, 3), (9, 14)):
        for x in range(cx - 3, cx + 4):
            for z in range(cz - 3, cz + 4):
                if not bp.inside(x, 2, z):
                    continue
                d = math.hypot(x - cx, z - cz)
                for y, r in ((2, 2.6), (3, 2.6), (4, 2.1), (5, 1.2)):
                    if r - 1 <= d < r + 0.01 or (y == 5 and d < r):
                        door = abs(x - cx) <= 0 and (z - cz) == (2 if cz < 8 else -2) and y <= 3
                        bp.set(x, y, z, "air" if door else (k.W if y in (2, 4) else k.G))
    bed(bp, 2, 2, 3, "west")
    bed(bp, 16, 2, 3, "east")
    bp.set(9, 2, 15, "crafting_table")
    bp.set(8, 2, 14, "furnace[facing=east,lit=false]")
    bp.set(10, 2, 14, "domum_ornamentum:architectscutter[facing=west]")
    for x in (6, 12):
        rack(bp, x, 2, 6, "south")
    for x in (7, 11):
        bp.set(x, 2, 10, "barrel[facing=up,open=false]")
    bp.set(9, 2, 8, "sea_lantern")
    k.fill(9, 3, 8, 9, 5, 8, "chain[axis=y,waterlogged=false]")         # beacon mast
    bp.set(9, 6, 8, "lantern[hanging=false,waterlogged=false]")
    anchor = (9, 2, 6)
    return finish_tag_anchor(k, name, anchor, 0, invisible)


# ============================================================================ supply ship
def build_supplyship(name="supplyship", invisible=True):
    k = Kit(name, "decorations/supplies", 4, (33, 16, 17))
    bp = k.bp
    WATER_LAYERS = 3                                                     # y0-2 must be water
    for x in range(33):
        for z in range(17):
            for y in range(WATER_LAYERS):
                bp.set(x, y, z, FLUID)
    # catamaran: two hulls (z 2-5 and 11-14) joined by a deck
    for hz1, hz2 in ((2, 5), (11, 14)):
        for x in range(3, 30):
            nose = max(0, x - 25)
            for z in range(hz1 + (1 if nose >= 3 else 0), hz2 + 1 - (1 if nose >= 3 else 0)):
                for y in range(1, 4):
                    edge_cell = z in (hz1, hz2) or x in (3, 29) or y == 1
                    bp.set(x, y, z, (k.AC if y == 3 else k.W) if edge_cell else "air")
    for x in range(4, 29):                                               # main deck
        for z in range(2, 15):
            bp.set(x, 4, z, k.D if 3 < z < 14 else k.W)
    k.railing_ring(4, 28, 2, 14, 5, skip={(16, 2), (16, 14)})
    # glass bridge cabin
    for x in range(8, 18):
        for z in range(5, 12):
            if edge(x, z, 8, 17, 5, 11):
                for y in range(5, 9):
                    bp.set(x, y, z, k.G if y < 8 else k.W)
            bp.set(x, 9, z, k.band if edge(x, z, 8, 17, 5, 11) else k.W)
    k.opening(17, 5, 8, 17, 6, 8)
    for x in (9, 11, 13):
        bed(bp, x, 5, 6, "south")
    bp.set(15, 5, 6, "crafting_table")
    bp.set(16, 5, 6, "furnace[facing=south,lit=false]")
    for x in (9, 12):
        rack(bp, x, 5, 10, "north")
    bp.set(15, 5, 10, "domum_ornamentum:architectscutter[facing=north]")
    bp.set(12, 9, 8, "sea_lantern")
    k.fill(13, 10, 8, 13, 13, 8, "chain[axis=y,waterlogged=false]")      # mast
    bp.set(13, 14, 8, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    anchor = (22, 5, 8)
    return finish_tag_anchor(k, name, anchor, WATER_LAYERS - 1, invisible)


# ============================================================================ mineshafts (re-skinned)
def reskin_mineshafts(out_dir):
    """Keep the official tunnel geometry the miner expects, swap the materials."""
    mapping = {
        "domum_ornamentum:double_crossed": "minecraft:light_gray_concrete",
        "minecraft:oak_slab": "minecraft:smooth_stone_slab",
        "minecraft:oak_fence": "minecraft:iron_bars",
        "minecraft:oak_stairs": "minecraft:polished_andesite_stairs",
        "minecraft:oak_sign": "minecraft:air",
        "minecraft:torch": "minecraft:lantern",
        "minecraft:wall_torch": "minecraft:lantern",
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    for f in sorted(REF.glob("miner*.blueprint")):
        bp = load(f)
        for x, y, z, s in list(bp.blocks()):
            name, props = parse_state(s)
            if name in mapping:
                new = mapping[name]
                if new == "minecraft:lantern":
                    props = {"hanging": "false", "waterlogged": "false"}
                elif new in ("minecraft:light_gray_concrete", "minecraft:air"):
                    props = {}
                bp.grid[y][z][x] = format_state(new, props)
                bp.tile_entities.pop((x, y, z), None)
        bp.architects = ["Neoterra"]
        bp.name = f.name
        bp.save(out_dir / f.name)
    return out_dir


# ============================================================================ miner
def build_miner(L):
    k = Kit("miner", "fundamentals", L, (21, 34, 19))
    bp = k.bp
    G0 = 2                                                               # ground floor height
    bp.fill(0, 0, 0, 20, 0, 18, SUBST)
    bp.fill(0, 1, 0, 20, 1, 18, SOLID)
    for x in range(21):
        for z in range(19):
            bp.set(x, G0, z, "grass_block[snowy=false]")
    # shaft: ladder column (x4) with its cobblestone backing (x3), open well around it
    SX_, SZ_ = 4, 6
    for x in range(3, 8):
        for z in range(4, 9):
            bp.set(x, 1, z, "air")
            bp.set(x, G0, z, "air")
    for y in (1, G0, G0 + 1):
        bp.set(SX_ - 1, y, SZ_, "minecraft:cobblestone")
        bp.set(SX_, y, SZ_, "ladder[facing=east,waterlogged=false]")
    k.tag((SX_, G0 + 1, SZ_), "ladder")
    k.tag((SX_ - 1, G0 + 1, SZ_), "cobble")
    for x in range(2, 9):
        for z in range(3, 10):
            if edge(x, z, 2, 8, 3, 9):
                bp.set(x, G0, z, k.W)
                if not (x == SX_ and z == 3):
                    put(bp, x, G0 + 1, z, k.st.railing)
    # headframe: lattice tower over the shaft that grows with the level, wheel on top
    top = G0 + [8, 11, 14, 17, 20][L - 1]
    for x, z in ((2, 3), (8, 3), (2, 9), (8, 9)):
        for y in range(G0 + 1, top + 1):
            bp.set(x, y, z, k.W if (y - G0) % 4 else k.AC)
    for y in range(G0 + 4, top + 1, 4):
        for x in range(2, 9):
            for z in (3, 9):
                bp.set(x, y, z, k.W)
        for z in range(3, 10):
            for x in (2, 8):
                bp.set(x, y, z, k.W)
    for x in range(2, 9):
        for z in range(3, 10):
            bp.set(x, top + 1, z, k.band if edge(x, z, 2, 8, 3, 9) else k.D)
    for a in range(0, 360, 30):                                          # sheave wheel
        x, y = round(5 + 3 * math.cos(math.radians(a))), round(top + 5 + 3 * math.sin(math.radians(a)))
        bp.set(x, y, 6, "iron_block" if k.st.early else "sea_lantern")
    bp.set(5, top + 5, 6, "iron_block")
    k.fill(5, top + 2, 6, 5, top + 4, 6, "iron_bars[east=false,north=false,south=false,waterlogged=false,west=false]")
    # glass hall beside the shaft
    k.box(10, 19, 3, 15, G0, G0 + 6)
    k.opening(14, G0 + 1, 3, 14, G0 + 2, 3)
    k.door(14, G0 + 1, 3, "south")
    k.opening(10, G0 + 1, 6, 10, G0 + 2, 6)
    for i in range(L + 1):
        rack(bp, 11 + i, G0 + 1, 14, "north")
    bp.set(18, G0 + 1, 14, "crafting_table")
    bp.set(18, G0 + 1, 13, "furnace[facing=west,lit=false]")
    k.lights(12, 18, 5, 13, G0 + 6, step=3)
    hut = (17, G0 + 1, 5)
    if L >= 2:  # ore sorting line
        for x in range(12, 17):
            k.set(x, G0 + 1, 9, k.st.counter)
        bp.set(12, G0 + 2, 9, "hopper[enabled=true,facing=down]")
    if L >= 3:  # ore display vitrine
        for i, ore in enumerate(["coal_block", "iron_block", "waxed_copper_block", "lapis_block"]):
            bp.set(11 + i, G0 + 1, 12, ore)
    if L >= 5:
        k.mast(17, G0 + 7, 13)
    for x, z in ((0, 0), (20, 0), (0, 18), (20, 18)):
        if L >= 2:
            tree(bp, x, G0 + 1, z, h=3)
    if L >= 4:
        street_lamp(bp, 12, G0 + 1, 1, premium=True)
        street_lamp(bp, 18, G0 + 1, 1, premium=True)
    connect_panes(bp)
    tags = {hut: ["neoterra"], (0, G0, 0): ["groundlevel"]}
    for p, ns in k.tags.items():
        tags.setdefault(p, []).extend(ns)
    path = f"fundamentals/miner{L}.blueprint"
    bp.set(*hut, "minecolonies:blockhutminer[facing=north]", hut_te(path, (k.sx, k.sy, k.sz), hut, tags))
    bp.primary_offset = hut
    bp.architects = ["Neoterra"]
    return bp


# ============================================================================ farmer + fields
def build_farmer(L):
    k = Kit("farmer", "agriculture/horticulture", L, (29, 22, 27))
    sh, bp = Shapes(k), k.bp
    C = (12, 13)
    k.ground(paved=[(11, 13, 0, 3)])
    R = 9
    sh.drum(*C, R, 1, 6, doors=(270, 0), glass_every=30, roof=False)
    for x in range(C[0] - R - 1, C[0] + R + 2):                         # glass dome roof
        for z in range(C[1] - R - 1, C[1] + R + 2):
            d = math.hypot(x - C[0], z - C[1])
            for y, (r1, r2) in ((6, (7.5, 9.5)), (7, (6, 7.5)), (8, (4, 6)), (9, (0, 4))):
                if r1 <= d < r2:
                    bp.set(x, y, z, k.W if (x + z) % 4 == 0 and y < 9 else "glass")
    for i in range(L + 1):
        rack(bp, 6 + i, 2, 19, "north")
    for x in (15, 16, 17):
        bp.set(x, 2, 19, "composter[level=0]")
    bp.set(18, 2, 17, "crafting_table")
    for x in range(8, 16, 2):                                            # seed beds inside the dome
        for z in (9, 10):
            bp.set(x, 1, z, "farmland[moisture=7]")
            bp.set(x, 2, z, "wheat[age=7]")
        bp.set(x + 1, 1, 9, "water[level=0]")
    hut = (15, 2, 7)
    if L >= 2:  # silo
        for x in range(22, 28):
            for z in range(4, 10):
                d = math.hypot(x - 25, z - 7)
                if 1.5 <= d < 2.5:
                    for y in range(2, 6 + 3 * min(L, 4)):
                        bp.set(x, y, z, k.AC if y % 3 == 0 else k.W)
                elif d < 1.5:
                    bp.set(x, 6 + 3 * min(L, 4), z, k.W)
    if L >= 3:  # hay & barrel store
        for x in range(20, 27):
            bp.set(x, 2, 20, "hay_block[axis=x]")
        for x in range(20, 27, 2):
            bp.set(x, 2, 22, "barrel[facing=up,open=false]")
    if L >= 4:
        bp.set(C[0], 10, C[1], "sea_lantern")
    for x, z in ((10, 15), (14, 15)):
        bp.set(x, 5, z, "lantern[hanging=true,waterlogged=false]" if k.st.early else "sea_lantern")
    k.landscape(trees=[(1, 1, 3), (27, 25, 3), (1, 25, 3)], lamps=[(9, 1), (15, 1)])
    return k.finish_hut(hut, "blockhutfarmer")


def build_field(size=9, name="neofield"):
    S = size + 2
    k = Kit(name, "decorations/fields", 4, (S, 5, S))
    bp = k.bp
    c = S // 2
    bp.fill(0, 0, 0, S - 1, 0, S - 1, SOLID)
    for x in range(S):
        for z in range(S):
            e = edge(x, z, 0, S - 1, 0, S - 1)
            if e:
                bp.set(x, 1, z, k.W if (x + z) % 2 else "smooth_stone")
            elif (x, z) == (c, c):
                bp.set(x, 1, z, "smooth_stone")
            elif x == c or z == c:
                bp.set(x, 1, z, "water[level=0]")
            else:
                bp.set(x, 1, z, "farmland[moisture=7]")
    bp.set(c, 2, c, "minecolonies:blockhutfield[facing=north,half=lower]",
           NBT.Compound({"id": NBT.String("minecolonies:scarecrow"), "Item": NBT.String("")}))
    bp.set(c, 3, c, "minecolonies:blockhutfield[facing=north,half=upper]")
    for x, z in ((0, 0), (S - 1, 0), (0, S - 1), (S - 1, S - 1)):
        bp.set(x, 2, z, "lantern[hanging=false,waterlogged=false]")
    bp.primary_offset = (c, 2, c)
    bp.architects = ["Neoterra"]
    bp.name = f"{name}.blueprint"
    return bp


# ============================================================================ hospital
def build_hospital(L):
    k = Kit("hospital", "fundamentals", L, (31, 18, 31))
    bp = k.bp
    C = 15
    k.ground(paved=[(14, 16, 0, 4)])
    arms = [(C - 4, C + 4, 3, 27), (3, 27, C - 4, C + 4)]                # cross plan
    cells = {(x, z) for x1, x2, z1, z2 in arms for x in range(x1, x2 + 1) for z in range(z1, z2 + 1)}
    for x, z in cells:
        boundary = any((x + dx, z + dz) not in cells for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        bp.set(x, 1, z, k.st.floor(x, z))
        bp.set(x, 7, z, k.band if boundary else ("smooth_stone" if k.st.early else k.D))
        if boundary:
            for y in range(2, 7):
                bp.set(x, y, z, k.G if y in (3, 4, 5) and (x + z) % 3 else k.W)
    k.opening(C, 2, 3, C, 3, 3)
    k.door(C, 2, 3, "south")
    # wards: beds in the east and west arms, 2 per level (red), cyan beds for staff at L4+
    spots = [(x, C - 3, "north") for x in (5, 7, 9)] + [(x, C - 3, "north") for x in (21, 23, 25)] + \
            [(x, C + 3, "south") for x in (5, 7, 9)] + [(x, C + 3, "south") for x in (21, 23, 25)]
    n = [2, 4, 6, 6, 8][L - 1]
    for x, z, f in spots[:n]:
        bed(bp, x, 2, z, f, "red")
    if L >= 4:
        bed(bp, C - 3, 2, 24, "south", "cyan")
        bed(bp, C + 3, 2, 24, "south", "cyan")
    bp.set(C + 3, 2, 9, "furnace[facing=west,lit=false]")
    bp.set(C + 3, 2, 10, "brewing_stand[has_bottle_0=false,has_bottle_1=false,has_bottle_2=false]")
    bp.set(C + 3, 2, 11, "water_cauldron[level=3]")
    if L >= 2:
        rack(bp, C - 3, 2, 9, "east")
    if L >= 3:
        for z in (20, 21, 22):
            bp.set(C - 3, 2, z, "barrel[facing=east,open=false]")
        table(k, C, 2, 19)
    hut = (C - 3, 2, 6)
    k.lights(5, 25, 13, 17, 7, step=5)
    k.lights(13, 17, 5, 25, 7, step=5)
    # glowing cross on the roof
    for x, z in cells:
        if (abs(x - C) <= 1 and 8 <= z <= 22) or (abs(z - C) <= 1 and 8 <= x <= 22):
            bp.set(x, 7, z, "sea_lantern" if not k.st.early else k.AC)
    if L >= 5:
        k.mast(C, 8, C)
    k.landscape(trees=[(2, 2, 3), (28, 2, 3), (2, 28, 3), (28, 28, 3)], lamps=[(12, 1), (18, 1)],
                planters=[(7, 2, 7), (23, 2, 7)])
    return k.finish_hut(hut, "blockhuthospital")


# ============================================================================ tavern (levels 1-3)
def build_tavern(L):
    k = Kit("tavern", "fundamentals", L, (25, 26, 27))
    bp = k.bp
    k.ground(paved=[(11, 13, 0, 4)])
    X1, X2, Z1, Z2 = 2, 22, 5, 23
    mid = (X1 + X2) // 2
    # steep A-frame (rises 2 per block): stair + block on each step, glass gable ends
    for z in range(Z1, Z2 + 1):
        for x in range(X1, X2 + 1):
            h = 2 + 2 * ((X2 - X1) // 2 - abs(x - mid))                  # roof height over x
            if z in (Z1, Z2):
                for y in range(2, h):
                    door = abs(x - mid) <= 1 and y <= 4 and z == Z1
                    bp.set(x, y, z, "air" if door else (k.W if (x in (X1, X2) or y in (6, 7)) else k.G))
            facing = "east" if x < mid else "west"
            if x == mid:
                bp.set(x, h, z, k.band)
            else:
                bp.set(x, h - 1, z, k.W)
                bp.set(x, h, z, stairs(k, facing))
            if z not in (Z1, Z2):
                bp.set(x, 1, z, k.st.floor(x, z))
    # loft floor (beds) at y7 across the middle
    for x in range(6, 19):
        for z in range(Z1 + 1, Z2):
            bp.set(x, 7, z, k.D)
    for z in range(Z1 + 1, Z2):
        put(bp, 6, 8, z, k.st.railing)
    k.stairs(17, 9, 2, 5, "south", cut_y=7, rail=False)
    bp.set(17, 7, 9, "air")
    for i in range(8):                                                    # 8 beds upstairs
        bed(bp, 8 + 2 * (i % 4) + (i // 4), 8, 15 if i < 4 else 19, "south" if i < 4 else "north")
    # bar downstairs + tables (sit tags 8 / 12 / 16)
    for z in range(13, 21):
        k.set(5, 2, z, k.st.counter)
    for z in (14, 16, 18):
        bp.set(3, 2, z, "barrel[facing=east,open=false]")
    n_tables = [4, 6, 8][L - 1]
    spots = [(9, 9), (13, 9), (9, 12), (13, 12), (9, 15), (13, 15), (9, 18), (13, 18)]
    for tx, tz in spots[:n_tables]:
        table(k, tx, 2, tz)
    for x, z in ((9, 11), (13, 11), (9, 17), (13, 17)):
        bp.set(x, 6, z, "lantern[hanging=true,waterlogged=false]")
    hut = (16, 2, 7)
    if L >= 2:  # beer garden
        for x in range(2, 23):
            for z in range(24, 27):
                bp.set(x, 1, z, k.D)
        for tx in (6, 12, 18):
            table(k, tx, 2, 25)
        k.opening(12, 2, Z2, 12, 3, Z2)
    if L >= 3:  # neon sign on the front gable
        for x in range(9, 16):
            bp.set(x, 9, Z1 - 1, k.AC if k.st.early or x % 2 == 0 else "sea_lantern")
        bp.set(12, 2, 22, "jukebox[has_record=false]")
    k.landscape(trees=[(0, 1, 3), (24, 1, 3)], lamps=[(9, 1), (15, 1)])
    return k.finish_hut(hut, "blockhuttavern")


# ============================================================================ fisherman
def build_fisherman(L):
    k = Kit("fisherman", "agriculture/husbandry", L, (27, 16, 25))
    bp = k.bp
    k.ground(paved=[(2, 9, 2, 22)])
    # pond (2 deep) east of the boathouse
    PX1, PX2, PZ1, PZ2 = 12, 24, 4, 20
    for x in range(PX1, PX2 + 1):
        for z in range(PZ1, PZ2 + 1):
            e = edge(x, z, PX1, PX2, PZ1, PZ2)
            bp.set(x, 1, z, k.W if e else "water[level=0]")
            bp.set(x, 0, z, "smooth_stone" if e else "water[level=0]")
    # jetty into the pond with fishing spots
    for x in range(PX1, PX1 + 7):
        for z in (11, 12):
            bp.set(x, 1, z, k.D)
    for x, z in ((PX1 + 1, 11), (PX1 + 3, 12), (PX1 + 5, 11), (PX1 + 6, 12)):
        k.tag((x, 2, z), "work")
    # boathouse with a wave canopy
    k.box(2, 9, 5, 19, 1, 6)
    k.opening(9, 2, 11, 9, 3, 12)
    k.opening(5, 2, 5, 5, 3, 5)
    k.door(5, 2, 5, "south")
    for i in range(L + 1):
        rack(bp, 3 + i, 2, 18, "north")
    bp.set(8, 2, 18, "barrel[facing=north,open=false]")
    bp.set(3, 2, 8, "smoker[facing=east,lit=false]")
    bp.set(3, 2, 9, "crafting_table")
    k.lights(4, 8, 8, 16, 6, step=4)
    hut = (7, 2, 7)
    for x in range(PX1, PX2 + 1):                                          # wave canopy over the jetty
        y = 6 + round(math.sin((x - PX1) / 2.0))
        for z in range(9, 15):
            bp.set(x, y, z, (k.glow or k.band) if z in (9, 14) else k.D)
    for x in (PX1 + 3, PX1 + 9):
        for z in (9, 14):
            for y in range(2, 6 + round(math.sin((x - PX1) / 2.0))):
                bp.set(x, y, z, k.T)
            bp.set(x, 1, z, k.W)
    if L >= 3:
        for z in (6, 16):
            for x in range(PX1 + 1, PX1 + 4):
                bp.set(x, 1, z, k.D)
    if L >= 4:
        for x in range(PX1 + 1, PX2, 4):
            bp.set(x, 0, PZ1 + 1, "sea_lantern")
    k.landscape(trees=[(1, 1, 3), (1, 23, 3), (25, 23, 3)], lamps=[(11, 2), (11, 22)])
    return k.finish_hut(hut, "blockhutfisherman")


# ============================================================================ smeltery
def build_smeltery(L):
    k = Kit("smeltery", "craftsmanship/metallurgy", L, (23, 32, 21))
    bp = k.bp
    k.ground(paved=[(9, 11, 0, 3)])
    k.box(2, 18, 4, 16, 1, 10, wall="gray_concrete" if k.st.early else "polished_deepslate")
    k.opening(10, 2, 4, 10, 3, 4)
    k.door(10, 2, 4, "south")
    for i in range(L):
        bp.set(4 + 2 * i, 2, 15, "furnace[facing=north,lit=false]")
    if L >= 5:
        bp.set(14, 2, 15, "blast_furnace[facing=north,lit=false]")
    for i in range(L):
        rack(bp, 3, 2, 6 + i, "east")
    bp.set(17, 2, 6, "crafting_table")
    k.lights(5, 15, 7, 13, 10, step=4)
    hut = (15, 2, 6)
    # twin stacks, glowing bands, growing with the level
    for cx in (6, 14):
        h = 12 + 3 * L
        for x in range(cx - 2, cx + 3):
            for z in range(8, 13):
                d = math.hypot(x - cx, z - 10)
                if 1.2 <= d < 2.3:
                    for y in range(10, h):
                        bp.set(x, y, z, ("sea_lantern" if not k.st.early else k.AC) if y % 5 == 0 else k.W)
    if L >= 3:  # ingot store
        for z in range(6, 12):
            bp.set(17, 2, z, "barrel[facing=west,open=false]")
    k.landscape(trees=[(0, 1, 3), (22, 1, 3)], lamps=[(7, 1), (13, 1)])
    return k.finish_hut(hut, "blockhutsmeltery")


# ============================================================================ blacksmith
def build_blacksmith(L):
    k = Kit("blacksmith", "craftsmanship/metallurgy", L, (27, 18, 23))
    bp = k.bp
    k.ground(paved=[(15, 25, 3, 20), (10, 12, 0, 3)])
    X1, X2, Z1, Z2 = 2, 14, 4, 18
    # shed roof: low at the back, high glass front
    for x in range(X1, X2 + 1):
        for z in range(Z1, Z2 + 1):
            top = 10 - (z - Z1) * 5 // (Z2 - Z1)
            e = edge(x, z, X1, X2, Z1, Z2)
            bp.set(x, 1, z, k.st.floor(x, z))
            bp.set(x, top, z, k.band if e else k.W)
            if e:
                for y in range(2, top):
                    s = k.G if (z == Z1 and y > 2) or (y in (3, 4) and (x + z) % 3) else k.W
                    bp.set(x, y, z, s)
    k.opening(8, 2, Z1, 8, 3, Z1)
    k.door(8, 2, Z1, "south")
    k.opening(X2, 2, 11, X2, 3, 12)
    # forge with hood
    k.fill(4, 2, 16, 6, 2, 17, "polished_blackstone_bricks" if not k.st.early else "stone_bricks")
    bp.set(5, 3, 16, "blast_furnace[facing=north,lit=false]" if L >= 3 else "furnace[facing=north,lit=false]")
    k.fill(4, 5, 15, 6, 5, 17, k.T)
    k.fill(5, 6, 16, 5, 9, 16, k.T)
    for i in range(min(L, 3)):
        bp.set(9 + i * 2, 2, 12, "anvil[facing=north]")
    bp.set(12, 2, 16, "smithing_table")
    bp.set(13, 2, 16, "grindstone[face=floor,facing=west]")
    for i in range(L + 1):
        rack(bp, 3, 2, 6 + i, "east")
    hut = (12, 2, 6)
    # anvil court outside with a water quench trough
    k.fill(17, 1, 8, 20, 1, 8, "water[level=0]")
    if L >= 2:
        k.canopy(15, 25, 3, 20, 6, columns=[(15, 3), (25, 3), (15, 20), (25, 20)])
        bp.set(22, 2, 12, "anvil[facing=west]")
    if L >= 4:
        bp.set(24, 2, 15, "smithing_table")
    k.landscape(trees=[(0, 1, 3), (0, 21, 3)], lamps=[(9, 1), (13, 1)])
    return k.finish_hut(hut, "blockhutblacksmith")


# ============================================================================ baker
def build_baker(L):
    k = Kit("baker", "craftsmanship/luxury", L, (27, 16, 23))
    sh, bp = Shapes(k), k.bp
    k.ground(paved=[(2, 24, 17, 21)])
    sh.vault(3, 23, 3, 15, 3)
    for x in range(4, 23):
        for z in range(4, 15):
            bp.set(x, 1, z, k.st.floor(x, z))
    for i in range(L):
        bp.set(5 + 2 * i, 2, 4, "furnace[facing=south,lit=false]")
    bp.set(16, 2, 4, "smoker[facing=south,lit=false]")
    bp.set(17, 2, 4, "crafting_table")
    bp.set(18, 2, 4, "water_cauldron[level=3]")
    for i in range(L):
        rack(bp, 20, 2, 5 + i, "west")
    for x in range(6, 15):
        k.set(x, 2, 8, k.st.counter)                                      # bakery counter
    hut = (21, 2, 13)
    if L >= 2:  # cafe terrace
        k.opening(13, 2, 15, 13, 3, 15)
        for tx in (5, 10, 16, 21):
            table(k, tx, 2, 19)
        k.canopy(2, 24, 17, 21, 6, columns=[(2, 21), (24, 21)])
    if L >= 3:
        for tx in (8, 13):
            table(k, tx, 2, 12)
    k.landscape(trees=[(0, 1, 3), (26, 1, 3)], lamps=[(8, 22), (18, 22)])
    return k.finish_hut(hut, "blockhutbaker")


HUTS = {
    "fundamentals/miner": (build_miner, 5),
    "agriculture/horticulture/farmer": (build_farmer, 5),
    "fundamentals/hospital": (build_hospital, 5),
    "fundamentals/tavern": (build_tavern, 3),
    "agriculture/husbandry/fisherman": (build_fisherman, 5),
    "craftsmanship/metallurgy/smeltery": (build_smeltery, 5),
    "craftsmanship/metallurgy/blacksmith": (build_blacksmith, 5),
    "craftsmanship/luxury/baker": (build_baker, 5),
}


def build_all(root: Path):
    for key, (fn, levels) in HUTS.items():
        cat, name = key.rsplit("/", 1)
        (root / cat).mkdir(parents=True, exist_ok=True)
        for lvl in range(1, levels + 1):
            fn(lvl).save(root / cat / f"{name}{lvl}.blueprint")
        print(f"{key}: {levels} levels")
    sup = root / "decorations/supplies"
    sup.mkdir(parents=True, exist_ok=True)
    build_supplycamp("supplycamp", True).save(sup / "supplycamp.blueprint")
    build_supplycamp("camp", False).save(sup / "camp.blueprint")
    build_supplyship("supplyship", True).save(sup / "supplyship.blueprint")
    build_supplyship("ship", False).save(sup / "ship.blueprint")
    fields = root / "decorations/fields"
    fields.mkdir(parents=True, exist_ok=True)
    build_field(9, "neofield").save(fields / "neofield.blueprint")
    build_field(13, "neofieldlarge").save(fields / "neofieldlarge.blueprint")
    reskin_mineshafts(root / "infrastructure/mineshafts")
    print("supplies, fields, mineshafts")


if __name__ == "__main__":
    build_all(Path(sys.argv[1]))
