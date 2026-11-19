"""
Neoterra update 3 – mystic, defence, education extras, infrastructure and parks.

Huts (cheap 1-3 / premium 4-5):
  mystic/enchanter                 Arcane Observatory  octagonal library hall + glass dome, bookshelf rings
  mystic/graveyard                 Memorial Garden     walled lawn, named graves 4/8/12/16/20, chapel + obelisk
  mystic/mysticalsite              Starstone Circle    ring of white monoliths round an amethyst crystal, 8 seats
  mystic/netherworker              Rift Lab            glass hall around an obsidian portal frame (`portal` tag)
  military/gatehouse (1-3)         Gate Towers         twin towers over a 4-wide gate (`gate`, `knight`, `archer`)
  military/wallguardtower          Wall Tower          guard tower that plugs into the Neoterra wall
  education/communitycollege       Campus Hall         alternative university: L-shaped hall + lecture terrace
  infrastructure/mineshafts/simplequarry, mediumquarry (+ shafts re-skinned from the official layouts)

Decorations / infrastructure (single blueprints unless noted):
  walls/        wallstraight, wallinsidecorner, walloutsidecorner, wallgate, wallstairs, watchtower1-3
  infrastructure/roads/      roadstraight, roadcorner, roadtjunction, roadintersection, roadstairs, avenue
  infrastructure/rails/      railstraight, railcorner, railstop
  infrastructure/canals/     canalstraight, canalcorner, canalintersection, canallock
  infrastructure/bridge/     bridgestart, bridgestraight, bridgepillar
  infrastructure/subway/     subwaystraight, subwaycorner, subwayentrance
  infrastructure/boardwalk/  boardwalkstraight, boardwalkcorner, pier
  infrastructure/cliffclimb/ cliffclimbbase, cliffclimbsegment, cliffclimblanding
  decorations/parks/         bench, smallpark, mediumpark, parklarge, plaza, fountain
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

from nbtlib import tag as NBT

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from kit import Kit, Shapes, SUBST, edge, put, rack, tree, planter, bed, in_octagon, decoration_te  # noqa: E402
from common import connect_panes, street_lamp, parse_state, format_state  # noqa: E402
from blueprint import load  # noqa: E402

SOLID = "structurize:blocksolidsubstitution"
REF = Path(__file__).resolve().parent / "ref"
LADDER = "ladder[facing={},waterlogged=false]"
FGATE = "birch_fence_gate[facing={},in_wall=false,open=false,powered=false]"
IRON_GATE = "minecolonies:gate_iron[facing={},half=lower,hinge=left,open=false,powered=false]"
INFRA_STYLE = 3        # walls, roads etc. are bought in bulk: cheap palette with cyan accents
PARK_STYLE = 5         # parks are showpieces: glowing premium palette


def seat(k, x, y, z, back, tag="sit"):
    k.bp.set(x, y, z, f"{k.st.SEAT}[facing={back},half=bottom,shape=straight,waterlogged=false]")
    k.tag((x, y, z), tag)


def single(k, fname):
    """Finish a one-off piece (no anchor block): name, offset, panes."""
    connect_panes(k.bp)
    k.bp.name = f"{fname}.blueprint"
    k.bp.architects = ["Neoterra"]
    return k.bp


def deco(k, anchor, fname, ground_y=1):
    """Finish a decoration with a decoration controller and its tags (for parks etc.)."""
    connect_panes(k.bp)
    tags = {(0, ground_y, 0): ["groundlevel"]}
    for p, names in k.tags.items():
        tags.setdefault(p, []).extend(names)
    path = f"{k.category}/{fname}.blueprint"
    k.bp.set(*anchor, "minecolonies:decorationcontroller[facing=north,mirror=false,waterlogged=false]",
             decoration_te(path, fname, (k.sx, k.sy, k.sz), anchor, tags))
    k.bp.primary_offset = anchor
    k.bp.name = f"{fname}.blueprint"
    k.bp.architects = ["Neoterra"]
    return k.bp


# ============================================================================ enchanter
def build_enchanter(L):
    k = Kit("enchanter", "mystic", L, (25, 24, 25))
    sh, bp = Shapes(k), k.bp
    C, R = 12, 9
    k.ground(paved=[(11, 13, 0, 3)])
    top = 8 + (L >= 3) * 2
    for x in range(C - R - 1, C + R + 2):
        for z in range(C - R - 1, C + R + 2):
            dx, dz = x - C, z - C
            if in_octagon(dx, dz, R - 1):
                bp.set(x, 1, z, k.st.floor(x, z))
            elif in_octagon(dx, dz, R):
                bp.set(x, top, z, k.band)
                for y in range(2, top):
                    fin = (abs(dx) + abs(dz)) % 4 == 0
                    bp.set(x, y, z, k.W if (fin or y == top - 1 or y == 2) else k.G)
    # glass dome over the octagon, crowned by a light / rod
    for y in range(top, top + 7):
        r = (R - 0.5) * math.sqrt(max(0.0, 1 - ((y - top) / 6.5) ** 2))
        for x in range(C - R, C + R + 1):
            for z in range(C - R, C + R + 1):
                d = math.hypot(x - C, z - C)
                if r - 1.2 <= d < r and not (y == top and not in_octagon(x - C, z - C, R - 1)):
                    rib = (x == C or z == C) and y > top
                    bp.set(x, y, z, k.W if rib else ("glass" if k.st.early else "light_blue_stained_glass"))
    bp.set(C, top + 7, C, k.W)
    bp.set(C, top + 8, C, "end_rod[facing=up]" if not k.st.early else "lightning_rod[facing=up,powered=false,waterlogged=false]")
    k.opening(C, 2, C - R, C, 3, C - R)
    k.door(C, 2, C - R, "south")
    # bookshelf rings: each level adds more shelving (the enchanter's study)
    rings = [(5, 1), (5, 2), (6, 2), (6, 3), (6, 4)][L - 1]
    rr, hh = rings
    for x in range(C - rr - 1, C + rr + 2):
        for z in range(C - rr - 1, C + rr + 2):
            d = math.hypot(x - C, z - C)
            if rr - 0.5 <= d < rr + 0.5 and not (abs(x - C) <= 1 and z < C):
                for y in range(2, 2 + hh):
                    bp.set(x, y, z, "bookshelf")
    bp.set(C, 2, C, "enchanting_table")
    for x, z in ((C - 2, C), (C + 2, C)):
        bp.set(x, 2, z, "lectern[facing=north,has_book=false,powered=false]" if L >= 2 else "air")
    if L >= 4:
        for x, z in ((C - 3, C - 3), (C + 3, C - 3), (C - 3, C + 3), (C + 3, C + 3)):
            bp.set(x, 2, z, "amethyst_block")
            bp.set(x, 3, z, "amethyst_cluster[facing=up,waterlogged=false]")
    for i in range(L):
        rack(bp, C - 2 + i, 2, C + R - 2, "north")
    k.landscape(trees=[(1, 1, 3), (23, 1, 3), (1, 23, 3), (23, 23, 3)], lamps=[(9, 1), (15, 1)])
    return k.finish_hut((C + 3, 2, C - 4), "blockhutenchanter", te_id="minecolonies:enchanter")


# ============================================================================ graveyard
def grave(bp, x, y, z, facing="south"):
    bp.set(x, y, z, f"minecolonies:blockminecoloniesnamedgrave[facing={facing}]",
           NBT.Compound({"id": NBT.String("minecolonies:namedgrave"), "Item": NBT.String(""),
                         "content": NBT.List[NBT.String]([NBT.String("Unknown Citizen")])}))


def build_graveyard(L):
    k = Kit("graveyard", "mystic", L, (25, 16, 25))
    bp = k.bp
    k.ground(paved=[(11, 13, 0, 24)])
    for x in range(25):                                                  # low white boundary wall
        for z in range(25):
            if edge(x, z, 0, 24, 0, 24) and not (11 <= x <= 13 and z == 0):
                bp.set(x, 2, z, k.W)
                put(bp, x, 3, z, k.st.railing if (x + z) % 2 else k.W)
    # graves in rows either side of the central path
    n = [4, 8, 12, 16, 20][L - 1]
    spots = [(x, z) for z in (5, 8, 11, 14, 17) for x in (4, 7, 17, 20)]
    for x, z in spots[:n]:
        grave(bp, x, 2, z, "south")
        bp.set(x, 1, z + 1, "moss_block" if L >= 3 else "grass_block[snowy=false]")
        bp.set(x, 2, z + 1, ["poppy", "azure_bluet", "lily_of_the_valley", "cornflower"][(x + z) % 4])
    # chapel at the back with the hut
    k.box(8, 16, 19, 23, 1, 7, front="north")
    k.opening(12, 2, 19, 12, 3, 19)
    k.door(12, 2, 19, "south")
    for x in (10, 14):
        seat(k, x, 2, 21, "south")
    rack(bp, 9, 2, 22, "north")
    # obelisk in the middle
    h = 3 + L
    k.fill(12, 2, 11, 12, 1 + h, 11, k.W)
    bp.set(12, 2 + h, 11, (k.glow or "lantern[hanging=false,waterlogged=false]"))
    for x, z in ((11, 11), (13, 11), (12, 10), (12, 12)):
        bp.set(x, 1, z, k.AC)
    k.lights(10, 14, 20, 22, 7, step=4)
    if L >= 2:
        for x, z in ((2, 2), (22, 2), (2, 18), (22, 18)):
            tree(bp, x, 2, z, h=4)
    if L >= 4:
        for z in range(3, 18, 4):
            for x in (10, 14):
                street_lamp(bp, x, 2, z, premium=True)
    return k.finish_hut((15, 2, 22), "blockhutgraveyard")


# ============================================================================ mystical site
def build_mysticalsite(L):
    k = Kit("mysticalsite", "mystic", L, (23, 20, 23))
    bp = k.bp
    C = 11
    k.ground(paved=[(10, 12, 0, 6)])
    for x in range(23):                                                  # stone circle plaza
        for z in range(23):
            d = math.hypot(x - C, z - C)
            if d < 9.5:
                bp.set(x, 1, z, k.AC if 6.5 <= d < 7.5 else ("smooth_stone" if k.st.early else k.D))
    # monoliths (taller and more each level)
    n = [6, 6, 8, 8, 10][L - 1]
    h = [4, 5, 6, 7, 8][L - 1]
    for i in range(n):
        a = 2 * math.pi * i / n + math.pi / n
        x, z = round(C + 8 * math.cos(a)), round(C + 8 * math.sin(a))
        k.fill(x, 2, z, x, 1 + h, z, k.W)
        bp.set(x, 2 + h, z, k.glow or k.AC)
    # crystal in the centre
    k.fill(C - 1, 2, C - 1, C + 1, 2, C + 1, "amethyst_block")
    k.fill(C, 3, C, C, 2 + min(L, 4), C, "amethyst_block")
    bp.set(C, 3 + min(L, 4), C, "amethyst_cluster[facing=up,waterlogged=false]")
    if L >= 3:
        for x, z in ((C - 1, C - 1), (C + 1, C - 1), (C - 1, C + 1), (C + 1, C + 1)):
            bp.set(x, 3, z, "amethyst_cluster[facing=up,waterlogged=false]")
    if L >= 5:
        bp.set(C, 1, C, "beacon")
    # 8 seats facing the crystal
    for (x, z, back) in ((C - 4, C - 1, "west"), (C - 4, C + 1, "west"), (C + 4, C - 1, "east"),
                         (C + 4, C + 1, "east"), (C - 1, C + 4, "south"), (C + 1, C + 4, "south"),
                         (C - 3, C - 3, "north"), (C + 3, C - 3, "north")):
        seat(k, x, 2, z, back)
    k.landscape(trees=[(1, 1, 3), (21, 1, 3), (1, 21, 3), (21, 21, 3)], lamps=[(8, 2), (14, 2)])
    return k.finish_hut((C, 2, 4), "blockhutmysticalsite")


# ============================================================================ nether worker
def build_netherworker(L):
    k = Kit("netherworker", "mystic", L, (23, 16, 21))
    bp = k.bp
    k.ground(paved=[(10, 12, 0, 3)])
    k.box(3, 19, 4, 17, 1, 10, front="north", glass_front=True)
    k.opening(11, 2, 4, 11, 3, 4)
    k.door(11, 2, 4, "south")
    # obsidian portal frame 4 wide x 5 tall (unlit) against the back wall
    px, pz = 9, 14
    for i in range(4):
        bp.set(px + i, 2, pz, "obsidian")
        bp.set(px + i, 6, pz, "obsidian")
    for y in range(3, 6):
        bp.set(px, y, pz, "obsidian")
        bp.set(px + 3, y, pz, "obsidian")
        for i in (1, 2):
            bp.set(px + i, y, pz, "air")
    k.tag((px + 2, 2, pz), "portal")                                     # the worker walks into the block above
    k.tag((px + 1, 1, pz - 1), "vault")
    for x in range(px - 1, px + 5):                                      # basalt dais and soul-fire braziers
        bp.set(x, 1, pz - 1, "polished_blackstone" if not k.st.early else "polished_andesite")
    for x in (px - 2, px + 5):
        bp.set(x, 2, pz, "soul_sand" if L >= 2 else "netherrack")
        bp.set(x, 3, pz, "soul_lantern[hanging=false,waterlogged=false]" if L >= 2 else "lantern[hanging=false,waterlogged=false]")
    for i in range(L):
        rack(bp, 4, 2, 6 + i, "east")
    bp.set(18, 2, 6, "crafting_table")
    bp.set(18, 2, 7, "blast_furnace[facing=west,lit=false]" if L >= 3 else "furnace[facing=west,lit=false]")
    if L >= 3:
        for x in range(4, 19, 2):
            bp.set(x, 9, 5, "crying_obsidian" if L >= 4 else "obsidian")
    k.lights(6, 17, 7, 15, 10, step=5)
    k.landscape(trees=[(1, 1, 3), (21, 1, 3)], lamps=[(8, 1), (14, 1)])
    return k.finish_hut((16, 2, 7), "blockhutnetherworker")


# ============================================================================ walls
WALL_H = 8          # walkway level (y); parapet above
WALL_D = 5          # thickness in z (0 = outside face)


def wall_section(k, x1, x2, z0=0, depth=WALL_D, gaps=()):
    bp = k.bp
    for x in range(x1, x2 + 1):
        if x in gaps:
            continue
        for z in range(z0, z0 + depth):
            bp.set(x, 1, z, k.W)
            face = z in (z0, z0 + depth - 1)
            for y in range(2, WALL_H):
                if face:
                    s = k.W
                    if y == 5:
                        s = k.band
                    elif z == z0 and y == 6 and x % 3 == 1:
                        s = k.G
                    bp.set(x, y, z, s)
            bp.set(x, WALL_H, z, "smooth_stone" if z not in (z0, z0 + depth - 1) else k.W)
        put(bp, x, WALL_H + 1, z0, k.W if x % 2 == 0 else k.st.railing)       # crenellated parapet
        put(bp, x, WALL_H + 1, z0 + depth - 1, k.st.railing)
        if x % 4 == 2 and bp.inside(x, WALL_H - 1, z0 + depth):
            bp.set(x, WALL_H - 1, z0 + depth, "lantern[hanging=true,waterlogged=false]")


def build_wallstraight():
    k = Kit("wallstraight", "walls", INFRA_STYLE, (8, WALL_H + 2, WALL_D + 1))
    k.bp.fill(0, 0, 0, 7, 0, WALL_D, SOLID)
    wall_section(k, 0, 7)
    k.bp.primary_offset = (4, 1, 2)
    return single(k, "wallstraight")


def corner_pillar(k, x1, z1, size=WALL_D):
    bp = k.bp
    for x in range(x1, x1 + size):
        for z in range(z1, z1 + size):
            bp.set(x, 1, z, k.W)
            e = edge(x, z, x1, x1 + size - 1, z1, z1 + size - 1)
            for y in range(2, WALL_H + 2):
                if e:
                    bp.set(x, y, z, k.band if y in (5, WALL_H + 1) else k.W)
            bp.set(x, WALL_H, z, k.W if e else "smooth_stone")
    cx, cz = x1 + size // 2, z1 + size // 2
    bp.set(cx, WALL_H + 2, cz, k.W)
    bp.set(cx, WALL_H + 3, cz, "lantern[hanging=false,waterlogged=false]")


def build_wallcorner(kind):
    """Corner piece: two half-walls meeting at a square pillar."""
    S = 8
    k = Kit(f"wall{kind}corner", "walls", INFRA_STYLE, (S, WALL_H + 4, S))
    bp = k.bp
    bp.fill(0, 0, 0, S - 1, 0, S - 1, SOLID)
    if kind == "outside":   # wall runs along x at z0..4 and along z at x0..4 (pillar at the outer corner)
        wall_section(k, WALL_D, S - 1)
        for z in range(WALL_D, S):                                       # the z-run: rotate by hand
            for x in range(0, WALL_D):
                bp.set(x, 1, z, k.W)
                face = x in (0, WALL_D - 1)
                for y in range(2, WALL_H):
                    if face:
                        bp.set(x, y, z, k.band if y == 5 else k.W)
                bp.set(x, WALL_H, z, k.W if face else "smooth_stone")
            put(bp, 0, WALL_H + 1, z, k.W if z % 2 == 0 else k.st.railing)
            put(bp, WALL_D - 1, WALL_H + 1, z, k.st.railing)
        corner_pillar(k, 0, 0)
    else:                   # inside corner: pillar at the far end, walls coming in from both sides
        wall_section(k, 0, S - WALL_D - 1, z0=S - WALL_D)
        for z in range(0, S - WALL_D):
            for x in range(S - WALL_D, S):
                bp.set(x, 1, z, k.W)
                face = x in (S - WALL_D, S - 1)
                for y in range(2, WALL_H):
                    if face:
                        bp.set(x, y, z, k.band if y == 5 else k.W)
                bp.set(x, WALL_H, z, k.W if face else "smooth_stone")
            put(bp, S - 1, WALL_H + 1, z, k.W if z % 2 == 0 else k.st.railing)
            put(bp, S - WALL_D, WALL_H + 1, z, k.st.railing)
        corner_pillar(k, S - WALL_D, S - WALL_D)
    bp.primary_offset = (S // 2, 1, S // 2)
    return single(k, f"wall{kind}corner")


def build_wallgate():
    k = Kit("wallgate", "walls", INFRA_STYLE, (14, WALL_H + 6, WALL_D + 1))
    bp = k.bp
    bp.fill(0, 0, 0, 13, 0, WALL_D, SOLID)
    wall_section(k, 0, 13)
    for x in range(5, 9):                                                # 4-wide, 4-tall gateway
        for z in range(WALL_D):
            for y in range(2, 6):
                bp.set(x, y, z, "air")
            bp.set(x, 1, z, "smooth_stone" if z != 2 else k.AC)
        bp.set(x, 2, 2, FGATE.format("south"))
    for x in (4, 9):                                                     # glowing jambs + raised arch
        for y in range(2, 7):
            bp.set(x, y, 0, k.AC)
    for x in range(4, 10):
        bp.set(x, 6, 0, k.AC)
        for y in range(WALL_H + 1, WALL_H + 4):
            bp.set(x, y, 0, k.W if x in (4, 9) or y == WALL_H + 3 else "glass")
    bp.set(6, WALL_H + 4, 0, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    bp.primary_offset = (7, 1, 2)
    return single(k, "wallgate")


def build_wallstairs():
    """Stair tower on the inside of the wall up to the walkway."""
    k = Kit("wallstairs", "walls", INFRA_STYLE, (8, WALL_H + 2, WALL_D + 8))
    bp = k.bp
    bp.fill(0, 0, 0, 7, 0, WALL_D + 7, SOLID)
    wall_section(k, 0, 7)
    for x in range(8):
        for z in range(WALL_D, WALL_D + 8):
            bp.set(x, 1, z, "smooth_stone")
    for i in range(WALL_H - 1):
        z = WALL_D + 6 - i
        for x in (2, 3, 4):
            for yy in range(1, 2 + i):
                bp.set(x, yy, z, k.W)
            bp.set(x, 2 + i, z, f"{k.st.SEAT}[facing=north,half=bottom,shape=straight,waterlogged=false]")
        put(bp, 5, 3 + i, z, k.st.railing)
    for x in (2, 3, 4):                                                  # cut the inside parapet at the stair top
        bp.set(x, WALL_H + 1, WALL_D - 1, "air")
        bp.set(x, WALL_H, WALL_D - 1, "smooth_stone")
    bp.primary_offset = (4, 1, 2)
    return single(k, "wallstairs")


def build_watchtower(L):
    k = Kit("watchtower", "walls", INFRA_STYLE + (L >= 3) * 2, (11, WALL_H + 14, 11))
    bp = k.bp
    bp.fill(0, 0, 0, 10, 0, 10, SOLID)
    bp.fill(0, 1, 0, 10, 1, 10, "smooth_stone")
    wall_section(k, 0, 10, z0=3)
    H = WALL_H + 3 + 2 * L
    k.box(2, 8, 2, 8, 1, H, front="north", glass_front=False)
    for z in range(3, 3 + WALL_D):
        for x in (2, 8):
            for y in (WALL_H + 1, WALL_H + 2):
                bp.set(x, y, z, "air")
    for x in range(3, 8):
        for z in range(3, 8):
            bp.set(x, WALL_H, z, "smooth_stone")
    for y in range(WALL_H + 1, H + 1):
        bp.set(7, y, 7, LADDER.format("north"))
    for x in range(1, 10):
        for z in range(1, 10):
            bp.set(x, H, z, k.band if edge(x, z, 1, 9, 1, 9) else ("smooth_stone" if k.st.early else k.D))
    bp.set(7, H, 7, LADDER.format("north"))
    k.railing_ring(1, 9, 1, 9, H + 1)
    bp.set(5, H + 1, 5, "lantern[hanging=false,waterlogged=false]" if k.st.early else "sea_lantern")
    bp.set(5, H + 2, 5, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    return deco(k, (5, 1, 0), f"watchtower{L}")


# ============================================================================ wall guard tower (hut)
def build_wallguardtower(L):
    k = Kit("wallguardtower", "military", L, (13, 28, 11))
    bp = k.bp
    k.ground(paved=[(5, 7, 8, 10)])
    wall_section(k, 0, 1)
    wall_section(k, 11, 12)
    H = [13, 15, 17, 19, 21][L - 1]
    k.box(2, 10, 0, 8, 1, H, front="south", glass_front=False)
    k.opening(6, 2, 8, 6, 3, 8)
    k.door(6, 2, 8, "north")
    for f in (5, WALL_H):                                                # floors (walkway level opens to the wall)
        for x in range(3, 10):
            for z in range(1, 8):
                bp.set(x, f, z, k.st.floor(x, z))
    for z in range(1, WALL_D - 1):
        for y in (WALL_H + 1, WALL_H + 2):
            bp.set(2, y, z, "air")
            bp.set(10, y, z, "air")
    for y in range(2, H + 1):
        bp.set(9, y, 7, LADDER.format("north"))
    bed(bp, 3, 2, 5, "south")
    bed(bp, 4, 2, 5, "south")
    bp.set(3, 2, 1, "barrel[facing=up,open=false]")
    for i in range(min(L, 3)):
        rack(bp, 5 + i, 6, 1, "south")
    for x in range(1, 12):                                               # lookout
        for z in range(-1 + 1, 10):
            if bp.inside(x, H, z):
                bp.set(x, H, z, (k.glow or k.band) if edge(x, z, 1, 11, 0, 9) else k.D)
    bp.set(9, H, 7, LADDER.format("north"))
    k.railing_ring(1, 11, 0, 9, H + 1)
    if L >= 4:
        for x in range(4, 9):
            for z in range(2, 7):
                if edge(x, z, 4, 8, 2, 6):
                    for y in (H + 1, H + 2):
                        bp.set(x, y, z, k.G)
                bp.set(x, H + 3, z, k.W if edge(x, z, 4, 8, 2, 6) else "glass")
        bp.set(6, H + 1, 6, "air")
        bp.set(6, H + 2, 6, "air")
        bp.set(6, H + 3, 4, "sea_lantern")
    k.lights(4, 8, 2, 6, 5, step=4)
    return k.finish_hut((7, 2, 6), "blockhutguardtower")


# ============================================================================ gatehouse (levels 1-3)
def build_gatehouse(L):
    k = Kit("gatehouse", "military", L, (18, 18, 9), style_level=[2, 3, 5][L - 1])
    bp = k.bp
    k.ground(paved=[(7, 10, 0, 8)])
    D = 7
    for side, (x1, x2) in enumerate(((0, 6), (11, 17))):                # twin towers
        k.box(x1, x2, 0, D - 1, 1, 12, front="north", glass_front=False)
        for x in range(x1 + 1, x2):                                      # upper storey level with the bridge walk
            for z in range(1, D - 1):
                bp.set(x, 8, z, k.st.floor(x, z))
        lx = x2 - 1 if side == 0 else x1 + 1
        for y in range(2, 13):
            bp.set(lx, y, D - 2, LADDER.format("north"))
        bp.set(lx, 8, D - 2, LADDER.format("north"))
        k.opening(x1 + 3, 2, D - 1, x1 + 3, 3, D - 1)
        k.door(x1 + 3, 2, D - 1, "north")
        bed(bp, x1 + 1, 2, 1, "south")
        bed(bp, x1 + 2, 2, 1, "south")
        bp.set(x1 + 1 if side else x2 - 2, 9, 1, "barrel[facing=up,open=false]")
        for x in range(x1, x2 + 1):                                      # tower tops
            for z in range(0, D):
                bp.set(x, 12, z, (k.glow or k.band) if edge(x, z, x1, x2, 0, D - 1) else ("smooth_stone" if k.st.early else k.D))
        bp.set(lx, 12, D - 2, LADDER.format("north"))
        k.railing_ring(x1, x2, 0, D - 1, 13)
    # bridge over the gate (archers' walk) at y8
    for x in range(7, 11):
        for z in range(0, D):
            bp.set(x, 1, z, "smooth_stone" if z != 3 else k.AC)
            for y in range(2, 8):
                bp.set(x, y, z, "air")
            bp.set(x, 8, z, k.W if z in (0, D - 1) else ("smooth_stone" if k.st.early else k.D))
        for y in range(9, 11):
            bp.set(x, y, 0, k.W if y == 10 or x in (7, 10) else k.G)
        put(bp, x, 9, D - 1, k.st.railing)
    for x in (6, 11):                                                    # tower doors onto the bridge walk
        k.opening(x, 9, 3, x, 10, 3)
        bp.set(x, 8, 3, k.W)
    # gate leaf, 4 wide
    for x in range(7, 11):
        k.tag((x, 1, 2), "gate")
        if L == 3:
            for y in range(2, 6):
                bp.set(x, y, 2, IRON_GATE.format("south"))
        else:
            for y in range(2, 2 + L):
                bp.set(x, y, 2, FGATE.format("south"))
    for x in (7, 10):
        k.tag((x, 1, 5), "knight")
        k.tag((x, 8, 2), "archer")
    if L >= 2:
        for x in (7, 10):
            bp.set(x, 7, 0, "lantern[hanging=true,waterlogged=false]")
    if L == 3:
        for x in (0, 6, 11, 17):
            bp.set(x, 14, 0, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    return k.finish_hut((4, 2, 4), "blockhutgatehouse")


# ============================================================================ community college
def build_communitycollege(L):
    k = Kit("communitycollege", "education", L, (27, 18, 25))
    bp = k.bp
    k.ground(paved=[(3, 23, 16, 22)])
    floors = 1 + (L >= 3)
    top = 1 + 5 * floors
    k.box(2, 24, 2, 9, 1, top, front="south")                            # long wing
    k.box(2, 9, 9, 15, 1, top, front="east")                             # short wing (L-shape)
    for x in range(3, 9):
        for y in range(2, top):
            bp.set(x, y, 9, "air")
    if floors == 2:
        for x in range(3, 24):
            for z in range(3, 9):
                bp.set(x, 6, z, k.st.floor(x, z))
        for x in range(3, 9):
            for z in range(9, 15):
                bp.set(x, 6, z, k.st.floor(x, z))
        k.stairs(23, 4, 2, 4, "south", cut_y=6)
    k.opening(13, 2, 9, 14, 3, 9)
    # lecture room: rows of seats facing the board
    for z in (4, 6):
        for x in range(12, 22, 2):
            seat(k, x, 2, z, "north")
    for x in range(12, 22, 3):
        bp.set(x, 2, 3, "bookshelf")
    bp.set(10, 2, 4, "lectern[facing=south,has_book=false,powered=false]")
    # library corner in the short wing
    n = [6, 10, 14, 18, 22][L - 1]
    shelves = [(3, z) for z in range(10, 15)] + [(x, 14) for x in range(4, 9)] + [(8, z) for z in range(10, 14)] + [(x, 3) for x in range(3, 9)]
    for x, z in shelves[:n]:
        bp.set(x, 2, z, "bookshelf")
        if L >= 4:
            bp.set(x, 3, z, "bookshelf")
    for x, z in ((5, 11), (6, 12)):
        seat(k, x, 2, z, "west")
    if L >= 2:
        bp.set(7, 2, 11, "lectern[facing=west,has_book=false,powered=false]")
    # outdoor lecture terrace with benches facing a speaker spot
    for x in range(12, 23, 2):
        seat(k, x, 2, 19, "south", "sit_out")
    k.tag((17, 1, 21), "stand_out")
    k.lights(5, 22, 5, 8, top, step=4)
    if L >= 2:
        k.canopy(11, 23, 17, 21, 6, columns=[(11, 17), (23, 17), (11, 21), (23, 21)])
    k.landscape(trees=[(1, 23, 4), (25, 23, 4), (25, 1, 3)], lamps=[(10, 16), (24, 16)], planters=[(1, 2, 18)])
    return k.finish_hut((22, 2, 7), "blockhutuniversity")


# ============================================================================ quarries
QUARRY_MAP = {
    "domum_ornamentum:double_crossed": "minecraft:light_gray_concrete",
    "domum_ornamentum:framed": "minecraft:white_concrete",
    "domum_ornamentum:horizontal_plain": "minecraft:white_concrete",
    "domum_ornamentum:one_crossed_lr": "minecraft:cyan_concrete",
    "domum_ornamentum:one_crossed_rl": "minecraft:cyan_concrete",
    "domum_ornamentum:plain": "minecraft:smooth_stone",
    "domum_ornamentum:shingle": "minecraft:light_gray_concrete",
    "minecraft:wall_torch": "minecraft:air",
    "minecraft:torch": "minecraft:air",
    "minecraft:spruce_fence_gate": "minecraft:birch_fence_gate",
    "minecraft:stone_bricks": "minecraft:white_concrete",
}


def reskin_shaft(name, out_dir):
    bp = load(REF / f"{name}shaft1.blueprint")
    for x, y, z, s in list(bp.blocks()):
        n, props = parse_state(s)
        if n in QUARRY_MAP:
            new = QUARRY_MAP[n]
            keep = new.endswith("fence_gate")
            bp.grid[y][z][x] = format_state(new, props if keep else {})
            bp.tile_entities.pop((x, y, z), None)
    bp.architects = ["Neoterra"]
    bp.name = f"{name}shaft1.blueprint"
    out_dir.mkdir(parents=True, exist_ok=True)
    bp.save(out_dir / f"{name}shaft1.blueprint")
    return bp


def build_quarry(name, shaft):
    """Surface rig over the official pit footprint (same size and hut position as the official one)."""
    sx, sy_shaft, sz = shaft.sx, shaft.sy, shaft.sz
    ox, oy, oz = shaft.primary_offset
    big = name == "mediumquarry"
    k = Kit(name, "infrastructure/mineshafts", 4, (sx, 12 if big else 9, sz))
    bp = k.bp
    pit = set()
    for x in range(sx):
        for z in range(sz):
            for y in (oy, oy - 1, oy - 2):
                if shaft.get(x, y, z) == "minecraft:air":
                    pit.add((x, z))
    for x in range(sx):
        for z in range(sz):
            if (x, z) in pit:
                bp.set(x, 0, z, SUBST)
                bp.set(x, 1, z, SUBST)
            else:
                bp.set(x, 0, z, SOLID)
                near = any((x + dx, z + dz) in pit for dx in (-1, 0, 1) for dz in (-1, 0, 1))
                bp.set(x, 1, z, k.AC if near else ("smooth_stone" if (x + z) % 2 else "polished_andesite"))
                if near:
                    put(bp, x, 2, z, "glass_pane")
    hx, hz = ox, oz
    # control cabin around the hut
    cx1, cx2 = max(0, hx - 3), min(sx - 1, hx + 3)
    cz1, cz2 = max(0, hz - 2), min(sz - 1, hz + 3)
    for x in range(cx1, cx2 + 1):
        for z in range(cz1, cz2 + 1):
            if (x, z) in pit:
                continue
            e = edge(x, z, cx1, cx2, cz1, cz2)
            bp.set(x, 1, z, "smooth_stone")
            if e:
                for y in range(2, 6):
                    bp.set(x, y, z, "glass" if y in (3, 4) and (x + z) % 2 else k.W)
            else:
                for y in range(2, 6):
                    bp.set(x, y, z, "air")
            bp.set(x, 6, z, k.band if e else "white_concrete")
    k.opening(hx, 2, cz2, hx, 3, cz2)
    for i in range(4 if big else 2):
        if (cx1 + 1, cz1 + 1 + i) not in pit:
            rack(bp, cx1 + 1, 2, cz1 + 1 + i, "east")
    if big:
        for x, z in ((2, 2), (sx - 3, 2), (2, sz - 3), (sx - 3, sz - 3)):  # floodlight masts
            if (x, z) not in pit:
                k.fill(x, 2, z, x, 9, z, "white_concrete")
                bp.set(x, 10, z, "sea_lantern")
    connect_panes(bp)
    bp = k.finish_hut((hx, 1, hz), name)
    bp.name = f"{name}1.blueprint"
    # finish_hut sets the hut at y1 – the official quarry also keeps its hut on the rim layer
    return bp


# ============================================================================ roads
def road_surface(k, x, z, line=False):
    k.bp.set(x, 1, z, k.AC if line else "gray_concrete")


def build_road(kind):
    W = 7
    sizes = {"roadstraight": (W, 8), "roadcorner": (W, W), "roadtjunction": (W + 6, W),
             "roadintersection": (W + 6, W + 6), "avenue": (W + 6, 16)}
    sx, sz = sizes[kind]
    k = Kit(kind, "infrastructure/roads", INFRA_STYLE, (sx, 7, sz))
    bp = k.bp
    bp.fill(0, 0, 0, sx - 1, 0, sz - 1, SOLID)
    walk = "smooth_stone"
    for x in range(sx):
        for z in range(sz):
            bp.set(x, 1, z, walk)
    if kind == "roadstraight":
        for z in range(sz):
            for x in range(1, W - 1):
                road_surface(k, x, z, line=(x == 3 and z % 4 < 2))
    elif kind == "avenue":   # boulevard: two carriageways + tree median
        for z in range(sz):
            for x in list(range(1, 6)) + list(range(8, 12)):
                road_surface(k, x, z, line=(x in (3, 10) and z % 4 < 2))
            bp.set(6, 1, z, "grass_block[snowy=false]")
            bp.set(7, 1, z, "grass_block[snowy=false]")
        for z in (3, 11):
            tree(bp, 6, 2, z, h=4)
        for z in (7, 15):
            street_lamp(bp, 7, 2, z)
        k.bp.primary_offset = (6, 1, 8)
        return single(k, kind)
    elif kind == "roadcorner":
        for x in range(1, W):
            for z in range(1, W):
                road_surface(k, x, z, line=((x == 3 and z >= 3) or (z == 3 and x >= 3)) and (x + z) % 4 < 2)
    else:
        for x in range(sx):
            for z in range(1, W - 1):
                road_surface(k, x, z, line=(z == 3 and x % 4 < 2 and not 3 <= x <= sx - 4))
        if kind == "roadintersection":
            for z in range(sz):
                for x in range(4, 4 + W - 2):
                    road_surface(k, x, z, line=(x == 6 and z % 4 < 2 and not 3 <= z <= sz - 4))
        else:
            for z in range(W - 1, sz):
                for x in range(4, 4 + W - 2):
                    road_surface(k, x, z)
    if kind in ("roadstraight",):
        street_lamp(bp, 0, 2, 4)
    bp.primary_offset = (sx // 2, 1, sz // 2)
    return single(k, kind)


def build_roadstairs():
    k = Kit("roadstairs", "infrastructure/roads", INFRA_STYLE, (7, 9, 8))
    bp = k.bp
    bp.fill(0, 0, 0, 6, 0, 7, SOLID)
    for i in range(6):
        for x in range(7):
            for y in range(1, 1 + i):
                bp.set(x, y, i + 1, "smooth_stone")
            if x in (0, 6):
                bp.set(x, 1 + i, i + 1, "smooth_stone")
                put(bp, x, 2 + i, i + 1, "glass_pane")
            else:
                bp.set(x, 1 + i, i + 1, f"polished_andesite_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]")
    for x in range(7):
        bp.set(x, 1, 0, "smooth_stone")
        bp.set(x, 6, 7, "smooth_stone")
    bp.primary_offset = (3, 1, 0)
    return single(k, "roadstairs")


# ============================================================================ rails
def build_rail(kind):
    if kind == "railstop":
        k = Kit("railstop", "infrastructure/rails", PARK_STYLE, (9, 8, 16))
        bp = k.bp
        bp.fill(0, 0, 0, 8, 0, 15, SOLID)
        for z in range(16):
            bp.set(1, 1, z, "polished_andesite")
            bp.set(1, 2, z, "rail[shape=north_south,waterlogged=false]")
            for x in range(3, 9):                                        # raised platform
                bp.set(x, 1, z, k.W)
                bp.set(x, 2, z, ("smooth_stone" if x != 3 else k.AC))
        for z in range(2, 14):
            bp.set(8, 3, z, k.G if z % 3 else k.W)
        k.canopy(3, 8, 1, 14, 6, columns=[(8, 1), (8, 14), (8, 7)])
        for x, z in ((3, 1), (3, 14)):
            k.fill(x, 3, z, x, 5, z, k.W)
        for z in (4, 6, 9, 11):
            seat(k, 7, 3, z, "east", "sit_out")
        for z in (5, 10):
            bp.set(4, 5, z, "lantern[hanging=true,waterlogged=false]")
        k.tag((5, 2, 8), "stand_out")
        return deco(k, (6, 2, 15), "railstop")
    k = Kit(kind, "infrastructure/rails", INFRA_STYLE, (5, 5, 8 if kind == "railstraight" else 5))
    bp = k.bp
    bp.fill(0, 0, 0, k.sx - 1, 0, k.sz - 1, SOLID)
    for x in range(k.sx):
        for z in range(k.sz):
            bp.set(x, 1, z, "polished_andesite" if x not in (0, k.sx - 1) else k.W)
    if kind == "railstraight":
        for z in range(8):
            bp.set(2, 2, z, "rail[shape=north_south,waterlogged=false]")
            bp.set(2, 1, z, "gravel")
        for z in (0, 4):
            put(bp, 0, 2, z, "glass_pane")
            put(bp, 4, 2, z, "glass_pane")
    else:
        cells = [(2, 0, "north_south"), (2, 1, "north_south"), (2, 2, "north_east"), (3, 2, "east_west"), (4, 2, "east_west")]
        for x, z, sh_ in cells:
            bp.set(x, 1, z, "gravel")
            bp.set(x, 2, z, f"rail[shape={sh_},waterlogged=false]")
        for x in range(k.sx):
            bp.set(x, 1, 4, k.W)
    bp.primary_offset = (2, 1, 0)
    return single(k, kind)


# ============================================================================ canals
def canal_cell(k, x, z, water, bank_rail=False):
    bp = k.bp
    if water:
        bp.set(x, 0, z, "smooth_stone")
        bp.set(x, 1, z, "water[level=0]")
    else:
        bp.set(x, 0, z, SOLID)
        bp.set(x, 1, z, k.W)
        if bank_rail:
            put(bp, x, 2, z, k.st.railing)


def build_canal(kind):
    S = 9
    sizes = {"canalstraight": (S, 8), "canalcorner": (S, S), "canalintersection": (S, S), "canallock": (S, 12)}
    sx, sz = sizes[kind]
    k = Kit(kind, "infrastructure/canals", INFRA_STYLE, (sx, 6, sz))
    bp = k.bp
    for x in range(sx):
        for z in range(sz):
            if kind in ("canalstraight", "canallock"):
                water = 2 <= x <= 6
            elif kind == "canalcorner":
                water = (2 <= x <= 6 and z >= 2) or (2 <= z <= 6 and x >= 2)
            else:
                water = 2 <= x <= 6 or 2 <= z <= 6
            rail = (not water) and (x in (1, sx - 2) or z in (1, sz - 2))
            canal_cell(k, x, z, water, bank_rail=rail and (x in (1, sx - 2) or kind != "canalstraight"))
    if kind == "canallock":   # glass lock gates + a footbridge
        for x in range(2, 7):
            for z in (3, 8):
                bp.set(x, 1, z, "glass")
                bp.set(x, 2, z, k.W)
        for x in range(0, sx):
            if x in (0, sx - 1):
                put(bp, x, 3, 8, k.st.railing)
        for x in (0, 8):
            for z in (3, 8):
                bp.set(x, 2, z, k.AC)
                bp.set(x, 3, z, "lantern[hanging=false,waterlogged=false]")
    if kind == "canalstraight":
        for z in (0, 7):
            street_lamp(bp, 0, 2, z)
    connect_panes(bp)
    bp.primary_offset = (sx // 2, 1, 0)
    return single(k, kind)


# ============================================================================ bridge
def build_bridge(kind):
    if kind == "bridgepillar":
        k = Kit(kind, "infrastructure/bridge", INFRA_STYLE, (7, 20, 7))
        bp = k.bp
        for y in range(0, 19):
            for x in range(1, 6):
                for z in range(1, 6):
                    if edge(x, z, 1, 5, 1, 5) or y == 18:
                        bp.set(x, y, z, k.band if y % 6 == 3 and edge(x, z, 1, 5, 1, 5) else k.W)
        for x in range(7):
            for z in range(7):
                bp.set(x, 19, z, k.W)
        bp.primary_offset = (3, 19, 3)
        return single(k, kind)
    L = 8 if kind == "bridgestraight" else 10
    k = Kit(kind, "infrastructure/bridge", INFRA_STYLE, (7, 8, L))
    bp = k.bp
    for z in range(L):
        rise = 0 if kind == "bridgestraight" else min(4, z // 2)
        for x in range(7):
            for y in range(0, rise + 1):
                if kind == "bridgestart" or y == rise:
                    bp.set(x, y, z, k.W if x in (0, 6) else ("smooth_stone" if y == rise else k.W))
            if x in (0, 6):
                put(bp, x, rise + 1, z, k.st.railing)
        if kind == "bridgestraight":
            bp.set(3, 0, z, k.AC if z % 3 == 0 else "smooth_stone")
    if kind == "bridgestraight":
        for z in (0, 7):
            bp.set(0, 1, z, k.W)
            bp.set(0, 2, z, k.W)
            bp.set(0, 3, z, "lantern[hanging=false,waterlogged=false]")
        bp.primary_offset = (3, 0, 0)
    else:
        for z in range(L):                                               # smooth the ramp with slabs on odd steps
            rise = min(4, z // 2)
            if z % 2 == 1 and rise < 4:
                for x in range(1, 6):
                    bp.set(x, rise + 1, z, "smooth_stone_slab[type=bottom,waterlogged=false]")
        bp.primary_offset = (3, 0, 0)
    connect_panes(bp)
    return single(k, kind)


# ============================================================================ subway
def build_subway(kind):
    if kind == "subwayentrance":
        k = Kit(kind, "infrastructure/subway", PARK_STYLE, (7, 14, 14))
        bp = k.bp
        # surface at y8, tunnel floor at y1; stairs run down along +z
        for x in range(7):
            for z in range(14):
                for y in range(0, 9):
                    bp.set(x, y, z, SOLID if y < 8 else "smooth_stone")
        for i in range(7):
            z = 2 + i
            for x in range(1, 6):
                for y in range(8 - i, 12 - i if i else 12):
                    bp.set(x, y, z, "air")
                bp.set(x, 7 - i, z, f"{k.st.SEAT}[facing=north,half=bottom,shape=straight,waterlogged=false]")
            for x in (0, 6):
                for y in range(7 - i, 9):
                    bp.set(x, y, z, k.W)
        for z in range(9, 14):                                           # landing / tunnel mouth
            for x in range(1, 6):
                for y in range(1, 6):
                    bp.set(x, y, z, "air")
                bp.set(x, 0, z, "smooth_stone")
        for x in range(1, 6):
            bp.set(x, 0, 9, "smooth_stone")
        for z in range(1, 9):                                            # glass entrance canopy
            for x in (0, 6):
                for y in (9, 10):
                    put(bp, x, y, z, k.G)
            for x in range(7):
                bp.set(x, 11, z, k.band if x in (0, 6) else k.G)
        for x in range(1, 6):
            bp.set(x, 9, 1, "air")
        bp.set(3, 12, 1, k.W)
        bp.set(3, 13, 1, "sea_lantern")
        bp.primary_offset = (3, 8, 0)
        return single(k, kind)
    k = Kit(kind, "infrastructure/subway", INFRA_STYLE, (9, 7, 8 if kind == "subwaystraight" else 9))
    bp = k.bp
    sz = k.sz
    for x in range(9):
        for z in range(sz):
            straight = kind == "subwaystraight"
            inside = (1 <= x <= 7) if straight else ((1 <= x <= 7 and z >= 1) and (z <= 7 or x <= 7))
            if kind == "subwaycorner":
                inside = (1 <= x <= 7 and 1 <= z <= 7) or (1 <= x <= 7 and z == 0) or (x == 8 and 1 <= z <= 7)
            for y in range(7):
                if not inside or y in (0, 6):
                    bp.set(x, y, z, k.W if y in (0, 6) or x in (0, 8) else SOLID)
                else:
                    bp.set(x, y, z, "air")
            if inside:
                bp.set(x, 0, z, "polished_andesite")
                bp.set(x, 6, z, k.W)
                if (x + z) % 4 == 0:
                    k.st.ceiling_light(bp, x, 6, z)
    if kind == "subwaystraight":
        for z in range(sz):
            bp.set(4, 1, z, "rail[shape=north_south,waterlogged=false]")
            bp.set(1, 1, z, "smooth_stone_slab[type=bottom,waterlogged=false]")
            bp.set(7, 1, z, "smooth_stone_slab[type=bottom,waterlogged=false]")
            for x in (0, 8):
                bp.set(x, 3, z, k.band)
    else:
        for x, z, s in ((4, 0, "north_south"), (4, 1, "north_south"), (4, 2, "north_south"), (4, 3, "north_south"),
                        (4, 4, "north_east"), (5, 4, "east_west"), (6, 4, "east_west"), (7, 4, "east_west"), (8, 4, "east_west")):
            bp.set(x, 1, z, f"rail[shape={s},waterlogged=false]")
    bp.primary_offset = (4, 1, 0)
    return single(k, kind)


# ============================================================================ boardwalk
def build_boardwalk(kind):
    sizes = {"boardwalkstraight": (5, 8), "boardwalkcorner": (5, 5), "pier": (9, 12)}
    sx, sz = sizes[kind]
    k = Kit(kind, "infrastructure/boardwalk", PARK_STYLE if kind == "pier" else INFRA_STYLE, (sx, 10, sz))
    bp = k.bp
    deck = "smooth_stone" if k.st.early else k.D
    for x in range(sx):
        for z in range(sz):
            bp.set(x, 2, z, deck)
            if (x in (0, sx - 1)) and (z % 4 == 0):
                for y in (0, 1):
                    bp.set(x, y, z, k.W)                                 # piles into the water / ground
    for x in range(sx):
        for z in range(sz):
            e_side = x in (0, sx - 1) if kind != "pier" else (x in (0, sx - 1) or z == sz - 1)
            if kind == "boardwalkcorner":
                e_side = x == sx - 1 or z == sz - 1
            if e_side:
                put(bp, x, 3, z, k.st.railing)
    if kind == "pier":
        for x, z in ((2, 10), (6, 10)):
            street_lamp(bp, x, 3, z, premium=True)
        for z in (3, 6):
            seat(k, 1, 3, z, "west", "sit_out")
            seat(k, sx - 2, 3, z, "east", "sit_out")
        bp.set(4, 3, sz - 2, "barrel[facing=up,open=false]")
        for x in range(sx):
            bp.set(x, 2, 0, deck)
            bp.set(x, 3, 0, "air")
        return deco(k, (4, 2, 0), "pier", ground_y=2)
    connect_panes(bp)
    bp.primary_offset = (sx // 2, 2, 0)
    return single(k, kind)


# ============================================================================ cliff climb
def build_cliffclimb(kind):
    H = {"cliffclimbbase": 9, "cliffclimbsegment": 8, "cliffclimblanding": 6}[kind]
    k = Kit(kind, "infrastructure/cliffclimb", INFRA_STYLE, (7, H + 1, 7))
    bp = k.bp
    for y in range(0, H + 1):
        for x in range(7):
            for z in range(7):
                if edge(x, z, 0, 6, 0, 6):
                    bp.set(x, y, z, k.band if y % 4 == 3 else (k.G if (x + z) % 2 and 1 <= y < H else k.W))
    if kind == "cliffclimblanding":
        for x in range(1, 6):
            for z in range(1, 6):
                bp.set(x, 0, z, "smooth_stone")
        for x in range(7):
            for z in range(7):
                bp.set(x, H, z, k.band if edge(x, z, 0, 6, 0, 6) else k.W)
        k.opening(3, 1, 0, 3, 2, 0)
        k.opening(3, 1, 6, 3, 2, 6)
        bp.primary_offset = (3, 0, 0)
        return single(k, kind)
    # spiral stair around a central column: 8 steps per turn of the 5x5 inside
    ring = [(1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (5, 2), (5, 3), (5, 4), (5, 5), (4, 5), (3, 5), (2, 5), (1, 5), (1, 4), (1, 3), (1, 2)]
    facing = ["east"] * 4 + ["south"] * 4 + ["west"] * 4 + ["north"] * 4
    k.fill(2, 0, 2, 4, H, 4, k.W)
    for i in range(H):
        j = (2 * i) % 16
        for jj in (j, (j + 1) % 16):
            x, z = ring[jj]
            bp.set(x, i, z, f"{k.st.SEAT}[facing={facing[jj]},half=bottom,shape=straight,waterlogged=false]" if jj == j else "smooth_stone_slab[type=top,waterlogged=false]")
    if kind == "cliffclimbbase":
        k.opening(1, 1, 0, 1, 2, 0)
    bp.primary_offset = (3, 0, 0)
    return single(k, kind)


# ============================================================================ parks
def build_park(kind):
    if kind == "bench":
        k = Kit("bench", "decorations/parks", PARK_STYLE, (5, 5, 3))
        bp = k.bp
        bp.fill(0, 0, 0, 4, 0, 2, SOLID)
        for x in range(5):
            for z in range(3):
                bp.set(x, 1, z, "smooth_stone")
        for x in (1, 2, 3):
            seat(k, x, 2, 1, "south", "sit_out")
        planter(bp, 0, 2, 1)
        planter(bp, 4, 2, 1)
        return deco(k, (2, 1, 0), "bench")
    S = {"smallpark": 11, "mediumpark": 17, "parklarge": 25, "plaza": 19, "fountain": 9}[kind]
    k = Kit(kind, "decorations/parks", PARK_STYLE, (S, 12, S))
    bp = k.bp
    C = S // 2
    bp.fill(0, 0, 0, S - 1, 0, S - 1, SOLID)
    for x in range(S):
        for z in range(S):
            on_path = abs(x - C) <= 1 or abs(z - C) <= 1
            ring = abs(math.hypot(x - C, z - C) - C * 0.6) < 0.8
            if kind == "plaza":
                bp.set(x, 1, z, k.AC if (x % 6 == 0 or z % 6 == 0) and (x - C) * (z - C) else ("white_concrete" if (x + z) % 2 else k.D))
            else:
                bp.set(x, 1, z, ("smooth_stone" if (x + z) % 2 else k.D) if (on_path or ring) else "grass_block[snowy=false]")
                if not (on_path or ring) and (x * 7 + z * 3) % 11 == 0 and kind != "fountain":
                    bp.set(x, 2, z, ["poppy", "azure_bluet", "cornflower", "oxeye_daisy", "short_grass"][(x + z) % 5])
    # centre piece
    if kind in ("smallpark", "fountain"):
        for x in range(C - 2, C + 3):
            for z in range(C - 2, C + 3):
                e = edge(x, z, C - 2, C + 2, C - 2, C + 2)
                bp.set(x, 1, z, k.W if e else "water[level=0]")
                if e:
                    bp.set(x, 2, z, ("smooth_quartz_slab[type=bottom,waterlogged=false]"))
        k.fill(C, 1, C, C, 3, C, k.W)
        bp.set(C, 4, C, "sea_lantern")
    elif kind in ("mediumpark", "parklarge"):
        r = 3 if kind == "mediumpark" else 5
        for x in range(S):
            for z in range(S):
                d = math.hypot(x - C, z - C)
                if d < r:
                    bp.set(x, 1, z, "water[level=0]")
                    bp.set(x, 0, z, "smooth_stone")
                elif d < r + 1:
                    bp.set(x, 1, z, k.W)
        k.fill(C, 1, C, C, 2 + r // 2, C, k.W)
        bp.set(C, 3 + r // 2, C, "sea_lantern")
        if kind == "parklarge":   # glass pavilion in one quadrant + lily pads
            for x in range(17, 23):
                for z in range(2, 8):
                    bp.set(x, 1, z, k.D)
            k.canopy(17, 22, 2, 7, 6, columns=[(17, 2), (22, 2), (17, 7), (22, 7)])
            for x in (18, 20):
                seat(k, x, 2, 5, "south", "sit_out")
            for x, z in ((C - 2, C + 1), (C + 2, C - 2), (C + 1, C + 3)):
                bp.set(x, 2, z, "lily_pad")
    elif kind == "plaza":     # tiered sculpture: stacked rings with a light core
        for t, r in enumerate((3, 2, 1)):
            for x in range(C - r, C + r + 1):
                for z in range(C - r, C + r + 1):
                    if edge(x, z, C - r, C + r, C - r, C + r):
                        bp.set(x, 2 + t * 2, z, k.W)
                        bp.set(x, 3 + t * 2, z, k.G if t < 2 else k.W)
        k.fill(C, 2, C, C, 8, C, "sea_lantern")
        bp.set(C, 9, C, "end_rod[facing=up]")
    # benches round the edge, trees in the corners, lamps
    benches = []
    for off in (-3, 3):
        if S >= 11:
            benches += [(C + off, 2, 1, "north"), (C + off, 2, S - 2, "south"), (1, 2, C + off, "west"), (S - 2, 2, C + off, "east")]
    for x, y, z, back in benches:
        seat(k, x, y, z, back, "sit_out")
    for x, z in ((1, 1), (S - 2, 1), (1, S - 2), (S - 2, S - 2)):
        if kind in ("plaza", "fountain"):
            planter(bp, x, 2, z)
        else:
            tree(bp, x, 2, z, h=4 if S > 11 else 3)
    if S >= 17:
        for x, z in ((C - 4, C - 4), (C + 4, C - 4), (C - 4, C + 4), (C + 4, C + 4)):
            if bp.get(x, 1, z) not in ("minecraft:water[level=0]",):
                street_lamp(bp, x, 2, z, premium=True)
    k.tag((C, 1, C - 3 if kind != "fountain" else C - 3), "stand_out")
    k.tag((C + 3 if S > 9 else C + 3, 1, C), "stand_out")
    return deco(k, (C, 1, 0), kind)


# ============================================================================ registry
HUTS = {
    "mystic/enchanter": (build_enchanter, 5),
    "mystic/graveyard": (build_graveyard, 5),
    "mystic/mysticalsite": (build_mysticalsite, 5),
    "mystic/netherworker": (build_netherworker, 5),
    "military/gatehouse": (build_gatehouse, 3),
    "military/wallguardtower": (build_wallguardtower, 5),
    "education/communitycollege": (build_communitycollege, 5),
}

SINGLES = {
    "walls": [build_wallstraight, lambda: build_wallcorner("inside"), lambda: build_wallcorner("outside"),
              build_wallgate, build_wallstairs],
    "infrastructure/roads": [lambda n=n: build_road(n) for n in ("roadstraight", "roadcorner", "roadtjunction",
                                                                 "roadintersection", "avenue")] + [build_roadstairs],
    "infrastructure/rails": [lambda n=n: build_rail(n) for n in ("railstraight", "railcorner", "railstop")],
    "infrastructure/canals": [lambda n=n: build_canal(n) for n in ("canalstraight", "canalcorner",
                                                                   "canalintersection", "canallock")],
    "infrastructure/bridge": [lambda n=n: build_bridge(n) for n in ("bridgestart", "bridgestraight", "bridgepillar")],
    "infrastructure/subway": [lambda n=n: build_subway(n) for n in ("subwaystraight", "subwaycorner", "subwayentrance")],
    "infrastructure/boardwalk": [lambda n=n: build_boardwalk(n) for n in ("boardwalkstraight", "boardwalkcorner", "pier")],
    "infrastructure/cliffclimb": [lambda n=n: build_cliffclimb(n) for n in ("cliffclimbbase", "cliffclimbsegment",
                                                                            "cliffclimblanding")],
    "decorations/parks": [lambda n=n: build_park(n) for n in ("bench", "smallpark", "mediumpark", "parklarge",
                                                              "plaza", "fountain")],
}


def build_all(root: Path, only=()):
    for key, (fn, levels) in HUTS.items():
        if only and not any(o in key for o in only):
            continue
        cat, name = key.rsplit("/", 1)
        (root / cat).mkdir(parents=True, exist_ok=True)
        for lvl in range(1, levels + 1):
            fn(lvl).save(root / cat / f"{name}{lvl}.blueprint")
        print(f"{key}: {levels} levels")
    if only:
        return
    (root / "walls").mkdir(parents=True, exist_ok=True)
    for lvl in (1, 2, 3):
        build_watchtower(lvl).save(root / "walls" / f"watchtower{lvl}.blueprint")
    for cat, fns in SINGLES.items():
        (root / cat).mkdir(parents=True, exist_ok=True)
        for fn in fns:
            bp = fn()
            bp.save(root / cat / bp.name)
        print(f"{cat}: {len(fns)} pieces")
    ms = root / "infrastructure/mineshafts"
    for q in ("simplequarry", "mediumquarry"):
        shaft = reskin_shaft(q, ms)
        build_quarry(q, shaft).save(ms / f"{q}1.blueprint")
    print("quarries + shafts")


if __name__ == "__main__":
    build_all(Path(sys.argv[1]), sys.argv[2:])
