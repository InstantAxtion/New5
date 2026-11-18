"""
Neoterra Town Hall, levels 1-5 (MineColonies hut: minecolonies:blockhuttownhall).

Style: realistic near-future (~2045) civic architecture: white concrete, clear/tinted glass,
charcoal trim, warm timber louvres and decking, green roofs, solar panels.

Every level has the same 45 x 62 x 45 footprint, so upgrades build on top of each other:

  L1  Founding Hall   round glass podium (r15): hut + reception, crafting/smelting corner,
                      bed, spiral stair core to a roof terrace, solar panels.
  L2  Civic Ring      second-floor ring building (r11) with a full player workshop and storage;
                      green roof ring with planting on the podium.
  L3  Archive Tower   two-storey glass tower (r9) with timber mullions: enchanting library
                      (30 bookshelves), quarters with beds, planted balcony, street lamps.
                      Glass goes tinted, recessed DO ceiling lights, quartz stairs.
  L4  Sky Lounge      glass sky lounge (r7), timber roof deck, ender chest / jukebox / bar,
                      exterior glass bubble-column elevator lobby -> roof, trees + water features.
  L5  Landmark        vertical timber sun-shading fins, roof garden with trees, antenna mast,
                      glass-floored skywalk (doubles as an elytra launch).

Coordinates: x/z 0..44 (centre 22), y 0 = foundation (solid substitution), y 1 = ground.
The front (main entrance + skywalk) faces north (-z).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    Blueprint, Spec, Style, put, hut_te, dist, toward_center, angle, connect_panes,
    do_slab, do_stairs, do_pillar, do_paperwall, do_light,
)

SX = SZ = 45
SY = 62
C = 22

FLOORS = [1, 9, 17, 25, 33, 41]                 # floor slab heights
TOP = {1: 9, 2: 17, 3: 33, 4: 41, 5: 41}        # highest floor reached by the stair core
TUBE = (C, C + 10)                              # elevator water column (x, z)


def build(level: int) -> Blueprint:
    L = level
    bp = Blueprint(SX, SY, SZ, f"townhall{L}.blueprint")
    early = Style(L).early

    # ---------------------------------------------------------------- materials
    WHITE = "white_concrete"
    GLASS = "glass" if early else "light_gray_stained_glass"     # clear, later lightly tinted
    TRIM = "gray_concrete" if early else "polished_deepslate"         # charcoal trim
    ACCENT = TRIM
    WOOD = "stripped_spruce_log[axis=y]"                              # timber louvres / fins
    DECK = "spruce_planks"                                            # timber floors, soffits, bands
    LEAVES = "azalea_leaves[distance=1,persistent=true,waterlogged=false]"
    CORE = "light_gray_concrete" if early else WHITE
    SEAT = "spruce_stairs"
    railing = Style(L).railing

    def tree(x, y, z, h=3):
        """Small street/roof-garden tree: timber trunk + leaf crown."""
        for k in range(h):
            bp.set(x, y + k, z, "stripped_oak_log[axis=y]")
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for k in (h, h + 1):
                    if k == h + 1 and abs(dx) + abs(dz) == 2:
                        continue
                    if (dx, dz) != (0, 0) or k > h - 1:
                        bp.set(x + dx, y + k, z + dz, "oak_leaves[distance=1,persistent=true,waterlogged=false]")
        bp.set(x, y + h + 2, z, "oak_leaves[distance=1,persistent=true,waterlogged=false]")

    def planter(x, y, z, plant="flowering_azalea"):
        bp.set(x, y, z, "moss_block")
        bp.set(x, y + 1, z, plant)

    def ceiling_light(x, y_ceiling, z):
        """Light fixture for a ceiling slab at y_ceiling."""
        if early:
            bp.set(x, y_ceiling - 1, z, "lantern[hanging=true,waterlogged=false]")
        else:
            put(bp, x, y_ceiling, z, do_light(WHITE, "sea_lantern"))

    def floor_mat(x, z):
        d = dist(x, z, C)
        if early:
            return "smooth_stone" if round(d) in (6, 10) else "polished_andesite"
        if round(d) in (6, 10):
            return WHITE
        if round(d) == 13:
            return DECK
        return "light_gray_concrete"

    def in_core(x, z, r=3):
        return abs(x - C) <= r and abs(z - C) <= r

    def disc(y, r, spec_fn, skip_core=True):
        for x in range(SX):
            for z in range(SZ):
                if dist(x, z, C) < r + 0.5 and not (skip_core and in_core(x, z, 2)):
                    s = spec_fn(x, z)
                    if s is not None:
                        put(bp, x, y, z, s)

    def ring(y1, y2, r, spec_fn):
        for x in range(SX):
            for z in range(SZ):
                if r - 0.5 <= dist(x, z, C) < r + 0.5:
                    for y in range(y1, y2 + 1):
                        s = spec_fn(x, y, z)
                        if s is not None:
                            put(bp, x, y, z, s)

    def cardinal_gap(x, z, half_width):
        return abs(x - C) <= half_width or abs(z - C) <= half_width

    def pillar_slot(x, z, n=24, width=0.14):
        k = angle(x, z, C) / 360 * n
        return abs(k - round(k)) < width

    # ---------------------------------------------------------------- ground & plaza
    bp.fill(0, 0, 0, SX - 1, 0, SZ - 1, "structurize:blocksolidsubstitution")
    for x in range(SX):
        for z in range(SZ):
            d = dist(x, z, C)
            if d >= 21.5:
                bp.set(x, 1, z, "grass_block[snowy=false]")
            elif early:
                bp.set(x, 1, z, "polished_andesite" if 17.5 <= d < 18.5 else "smooth_stone")
            else:
                path = abs(x - C) <= 2 or abs(z - C) <= 2
                if 18.5 <= d < 21.5 and not path:
                    bp.set(x, 1, z, "grass_block[snowy=false]")        # lawn ring
                elif 17.5 <= d < 18.5:
                    bp.set(x, 1, z, WHITE)
                else:
                    bp.set(x, 1, z, "smooth_stone" if (x // 2 + z // 2) % 2 else "polished_andesite")

    # ---------------------------------------------------------------- L1: podium (r15)
    disc(1, 14, lambda x, z: floor_mat(x, z))

    def podium_wall(x, y, z):
        if cardinal_gap(x, z, 2) and y <= 5:
            return "air"                       # four entrances, 5 wide x 4 tall
        if y == 8:
            return WHITE                        # fascia band
        if pillar_slot(x, z):
            if early:
                return WHITE
            col = "pillar_base" if y == 2 else ("pillar_capital" if y == 7 else "pillar_column")
            return do_pillar(WHITE, col)
        if cardinal_gap(x, z, 2) and y in (6, 7):
            return DECK                         # timber lintel over the entrances
        return GLASS

    ring(2, 8, 15, podium_wall)
    disc(9, 15, lambda x, z: WHITE if dist(x, z, C) >= 14.5 else ("smooth_stone" if early else floor_mat(x, z)))
    if not early:  # flared eave under the roof edge
        ring(8, 8, 16, lambda x, y, z: do_stairs(WHITE, toward_center(x, z, C), half="top"))
    ring(10, 10, 15, lambda x, y, z: railing)
    for a in range(8):  # ceiling lights of the hall
        for r in (7, 11):
            ang = math.radians(a * 45 + 22.5)
            x, z = round(C + r * math.cos(ang)), round(C + r * math.sin(ang))
            ceiling_light(x, 9, z)

    # ---------------------------------------------------------------- L2: civic ring (r11)
    if L >= 2:
        def civic_wall(x, y, z):
            if cardinal_gap(x, z, 1) and y <= 12:
                return "air"
            if y == 16:
                return WHITE
            if y == 13:
                return DECK                     # timber band
            if pillar_slot(x, z, 16, 0.12):
                return WOOD
            return GLASS
        disc(9, 10, lambda x, z: floor_mat(x, z))
        ring(10, 16, 11, civic_wall)
        disc(17, 11, lambda x, z: WHITE if dist(x, z, C) >= 10.5 else floor_mat(x, z))
        ring(18, 18, 11, lambda x, y, z: railing)
        for a in range(8):
            ang = math.radians(a * 45 + 22.5)
            x, z = round(C + 7 * math.cos(ang)), round(C + 7 * math.sin(ang))
            ceiling_light(x, 17, z)

    # ---------------------------------------------------------------- L3: archive tower (r9)
    if L >= 3:
        def tower_wall(x, y, z):
            if y in (24, 32):
                return WHITE                    # slab edge bands
            if pillar_slot(x, z, 12, 0.10):
                return WOOD                     # timber mullions
            return GLASS
        ring(18, 24, 9, tower_wall)
        disc(25, 11, lambda x, z: WHITE if dist(x, z, C) >= 8.5 else floor_mat(x, z))   # floor + balcony
        ring(26, 26, 11, lambda x, y, z: railing)
        ring(26, 32, 9, tower_wall)
        disc(33, 9, lambda x, z: WHITE if dist(x, z, C) >= 8.5 else floor_mat(x, z))
        ring(25, 25, 12, lambda x, y, z: do_stairs(WHITE, toward_center(x, z, C), half="top"))
        ring(34, 34, 9, lambda x, y, z: railing)
        for y_ceiling in (25, 33):
            for a in range(6):
                ang = math.radians(a * 60 + 30)
                x, z = round(C + 6 * math.cos(ang)), round(C + 6 * math.sin(ang))
                ceiling_light(x, y_ceiling, z)

    # ---------------------------------------------------------------- L4: sky lounge (r7) + deck
    if L >= 4:
        def lounge_wall(x, y, z):
            if y == 40:
                return WHITE
            if pillar_slot(x, z, 8, 0.10):
                return WHITE
            return GLASS
        ring(34, 40, 7, lounge_wall)
        disc(41, 10, lambda x, z: WHITE if dist(x, z, C) >= 9.5 else (DECK if dist(x, z, C) >= 7.5 else "smooth_stone"))
        ring(41, 41, 11, lambda x, y, z: do_stairs(WHITE, toward_center(x, z, C), half="top"))
        ring(42, 42, 10, lambda x, y, z: railing)
        for a in range(6):
            ang = math.radians(a * 60)
            x, z = round(C + 5 * math.cos(ang)), round(C + 5 * math.sin(ang))
            ceiling_light(x, 41, z)

    # ---------------------------------------------------------------- green roofs (L2+)
    if L >= 2:  # planted ring on the podium roof around the civic ring
        for x in range(SX):
            for z in range(SZ):
                d = dist(x, z, C)
                if 12.5 <= d < 14.5 and not cardinal_gap(x, z, 1):
                    bp.set(x, 9, z, "grass_block[snowy=false]")
                    if pillar_slot(x, z, 16, 0.08):
                        bp.set(x, 10, z, "flowering_azalea" if L >= 3 else "azalea")
                    elif (x + z) % 3 == 0:
                        bp.set(x, 10, z, "short_grass")

    # ---------------------------------------------------------------- L5: timber louvres + roof garden
    if L >= 5:
        # vertical timber sun-shading fins around the tower (brise-soleil)
        for a in range(16):
            ang = math.radians(a * 22.5 + 11.25)
            # hung from the balcony edge, outside the railing so the balcony stays walkable
            x, z = round(C + 12 * math.cos(ang)), round(C + 12 * math.sin(ang))
            if abs(x - C) <= 1 and z > C:
                continue                            # keep clear of the elevator
            for y in range(18, 33):
                bp.set(x, y, z, WOOD)
        # roof garden on the deck: lawn ring with trees
        for x in range(SX):
            for z in range(SZ):
                d = dist(x, z, C)
                if 7.5 <= d < 9.5 and not cardinal_gap(x, z, 1):
                    bp.set(x, 41, z, "grass_block[snowy=false]")
        for a in range(4):
            ang = math.radians(a * 90 + 45)
            tree(round(C + 8 * math.cos(ang)), 42, round(C + 8 * math.sin(ang)))

    # ---------------------------------------------------------------- stair core
    top = TOP[L]
    core_top = top + 3
    for x in range(C - 3, C + 4):
        for z in range(C - 3, C + 4):
            ring_d = max(abs(x - C), abs(z - C))
            for y in range(2, core_top + 1):
                if ring_d == 3:
                    bp.set(x, y, z, ACCENT if (y - 1) % 8 == 0 and y > 1 else CORE)
                elif ring_d <= 1:
                    bp.set(x, y, z, CORE)               # central column
                else:
                    bp.set(x, y, z, "air")
            bp.set(x, 1, z, floor_mat(x, z) if ring_d >= 2 else CORE)
            bp.set(x, core_top + 1, z, WHITE)          # cap
    stair_mat = "smooth_stone" if early else "smooth_quartz"
    stair_state = "polished_andesite_stairs" if early else "smooth_quartz_stairs"
    exits = spiral(bp, top, stair_mat, stair_state)
    for (x, z, ox, oz), f in exits:
        for y in (f + 1, f + 2):
            bp.set(ox, y, oz, "air")

    # solar panels on the stair-house roof (every level), antenna mast at level 5
    for x in range(C - 2, C + 3):
        for z in range(C - 2, C + 3):
            bp.set(x, core_top + 2, z, "daylight_detector[inverted=false,power=0]")
    if L >= 5:
        bp.set(C, core_top + 2, C, TRIM)
        for y in range(core_top + 3, core_top + 9):
            bp.set(C, y, C, "chain[axis=y,waterlogged=false]")
        bp.set(C, core_top + 9, C, "lightning_rod[facing=up,powered=false,waterlogged=false]")

    # ---------------------------------------------------------------- furniture & function
    sit = []
    hut = (C + 6, 2, C - 6)
    # reception desk around the hut block
    for x, z in ((C + 4, C - 7), (C + 4, C - 6), (C + 4, C - 5), (C + 5, C - 4), (C + 6, C - 4), (C + 7, C - 4)):
        put(bp, x, 2, z, "smooth_stone_slab[type=top,waterlogged=false]" if early else do_slab(WHITE, "top"))
    # crafting & smelting corner (north-west)
    bp.set(C - 7, 2, C - 6, "crafting_table")
    bp.set(C - 8, 2, C - 5, "furnace[facing=east,lit=false]")
    bp.set(C - 8, 2, C - 4, "furnace[facing=east,lit=false]")
    for z in (C - 7, C - 8):
        bp.set(C - 6, 2, z, "barrel[facing=up,open=false]")
        bp.set(C - 5, 2, z, "barrel[facing=up,open=false]")
    # bed (respawn point) in the south-west
    bp.set(C - 8, 2, C + 6, "light_gray_bed[facing=south,occupied=false,part=foot]")
    bp.set(C - 8, 2, C + 7, "light_gray_bed[facing=south,occupied=false,part=head]")
    # waiting benches (south-east, facing the core)
    for x in range(C + 5, C + 9):
        bp.set(x, 2, C + 7, f"{SEAT}[facing=south,half=bottom,shape=straight,waterlogged=false]")
        sit.append((x, 2, C + 7))
    # planters
    for x, z in ((C - 10, C - 3), (C - 10, C + 3), (C + 10, C - 3), (C + 10, C + 3)):
        bp.set(x, 2, z, "moss_block")
        bp.set(x, 3, z, "flowering_azalea" if not early else "azalea")

    if L >= 2:  # workshop on the civic ring floor (y10)
        y = 10
        ws = [
            ((C - 6, C - 6), "smithing_table"),
            ((C - 7, C - 5), "stonecutter[facing=east]"),
            ((C - 5, C - 7), "grindstone[face=floor,facing=south]"),
            ((C - 8, C - 3), "anvil[facing=east]"),
            ((C + 6, C - 6), "loom[facing=west]"),
            ((C + 7, C - 5), "cartography_table"),
            ((C + 5, C - 7), "fletching_table"),
            ((C + 8, C - 3), "crafting_table"),
            ((C + 6, C + 6), "blast_furnace[facing=west,lit=false]"),
            ((C + 7, C + 5), "smoker[facing=west,lit=false]"),
            ((C + 5, C + 7), "furnace[facing=north,lit=false]"),
            ((C + 8, C + 3), "brewing_stand[has_bottle_0=false,has_bottle_1=false,has_bottle_2=false]"),
            ((C + 4, C + 8), "water_cauldron[level=3]"),
        ]
        for (x, z), s in ws:
            bp.set(x, y, z, s)
        for x, z in ((C - 6, C + 6), (C - 7, C + 5), (C - 5, C + 7), (C - 8, C + 3), (C - 3, C + 8)):
            bp.set(x, y, z, "barrel[facing=up,open=false]")
            bp.set(x, y + 1, z, "barrel[facing=up,open=false]")

    if L >= 3:  # enchanting library (y18) + quarters (y26)
        y = 18
        # the library is a 5x5 room against the core; pick a side the stair exit does not use
        exit_side = {f: side_of(ox, oz) for (_, _, ox, oz), f in exits}
        side = next(sd for sd in ("north", "east", "west") if sd != exit_side.get(17))
        for u in range(-2, 3):
            for v in range(4, 9):
                x, z = rot(side, u, v)
                edge = abs(u) == 2 or v in (4, 8)
                for yy in (y, y + 1):
                    bp.set(x, yy, z, "bookshelf" if edge else "air")
        for yy in (y, y + 1):
            bp.set(*_xz(rot(side, 2, 6), yy), "air")          # way in
        bp.set(*_xz(rot(side, 0, 6), y), "enchanting_table")
        bp.set(C - 5, y, C + 5, "lectern[facing=north,has_book=false,powered=false]")
        bp.set(C + 5, y, C + 5, "anvil[facing=north]")
        bp.set(C + 6, y, C + 3, "grindstone[face=floor,facing=west]")
        for x in range(C - 7, C - 3):
            bp.set(x, y, C + 7, "bookshelf")
            bp.set(x, y + 1, C + 7, "bookshelf")
        # quarters
        y = 26
        for (fx, fz), (hx, hz), facing in (
            ((C - 6, C - 4), (C - 7, C - 4), "west"), ((C - 6, C + 4), (C - 7, C + 4), "west"),
            ((C + 6, C - 4), (C + 7, C - 4), "east"), ((C + 6, C + 4), (C + 7, C + 4), "east"),
        ):
            bp.set(fx, y, fz, f"white_bed[facing={facing},occupied=false,part=foot]")
            bp.set(hx, y, hz, f"white_bed[facing={facing},occupied=false,part=head]")
        for x, z in ((C - 6, C - 6), (C + 6, C - 6), (C - 6, C + 6), (C + 6, C + 6)):
            bp.set(x, y, z, "barrel[facing=up,open=false]")
            bp.set(x, y, z + (1 if z < C else -1), "barrel[facing=up,open=false]")

    if L >= 4:  # sky lounge (y34)
        y = 34
        bp.set(C - 5, y, C, "ender_chest[facing=east,waterlogged=false]")
        bp.set(C + 5, y, C, "jukebox[has_record=false]")
        for x in range(C - 2, C + 3):
            put(bp, x, y, C + 5, do_slab(TRIM, "top"))   # bar counter
        for x in (C - 2, C, C + 2):
            bp.set(x, y, C + 4, f"{SEAT}[facing=north,half=bottom,shape=straight,waterlogged=false]")
            sit.append((x, y, C + 4))
        for x, z in ((C - 4, C - 4), (C + 4, C - 4)):
            bp.set(x, y, z, "potted_flowering_azalea_bush")

    # ---------------------------------------------------------------- exterior extras
    if L >= 3:  # street lamps along the plaza ring (paths stay clear)
        for a in range(16):
            ang = math.radians(a * 22.5 + 11.25)
            x, z = round(C + 17 * math.cos(ang)), round(C + 17 * math.sin(ang))
            if cardinal_gap(x, z, 2):
                continue
            bp.fill(x, 2, z, x, 4, z, "polished_blackstone_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
            bp.set(x, 5, z, "lantern[hanging=false,waterlogged=false]")
    if L >= 4:  # trees on the lawn ring + water features in the corners
        for a in range(8):
            ang = math.radians(a * 45 + 22.5)
            tree(round(C + 20 * math.cos(ang)), 2, round(C + 20 * math.sin(ang)), h=4)
        for cx, cz in ((5, 5), (39, 5), (5, 39), (39, 39)):
            bp.fill(cx - 2, 1, cz - 2, cx + 2, 1, cz + 2, "smooth_stone")
            bp.fill(cx - 1, 1, cz - 1, cx + 1, 1, cz + 1, "water[level=0]")
            bp.fill(cx - 1, 0, cz - 1, cx + 1, 0, cz + 1, "smooth_stone")
            bp.set(cx, 0, cz, "sea_lantern")                # underwater light
    if L >= 5:  # glass-floored skywalk cantilevered north off the roof deck (also an elytra launch)
        for z in range(C - 18, C - 9):
            for x in range(C - 1, C + 2):
                bp.set(x, 41, z, "glass" if x == C else "smooth_stone")
            put(bp, C - 2, 42, z, railing)
            put(bp, C + 2, 42, z, railing)
            bp.set(C - 2, 41, z, WHITE)
            bp.set(C + 2, 41, z, WHITE)
        for x in range(C - 1, C + 2):
            bp.set(x, 42, C - 10, "air")                  # open the deck railing to the skywalk

    # ---------------------------------------------------------------- elevator (L4+)
    if L >= 4:
        tx, tz = TUBE
        deck = 41
        for x in range(tx - 1, tx + 2):
            for z in range(tz - 1, tz + 2):
                for y in range(2, deck + 3):
                    if (x, z) == TUBE:
                        bp.set(x, y, z, "water[level=0]" if y <= deck else "air")
                    elif y == deck:
                        bp.set(x, y, z, WHITE)
                    else:
                        bp.set(x, y, z, TRIM if y % 8 == 1 else "glass")
                bp.set(x, deck + 3, z, WHITE)
        bp.set(tx, 1, tz, "soul_sand")
        # bottom door from the lobby, top exit onto the deck (water never flows through doors)
        bp.set(tx, 2, tz - 1, "waxed_copper_door[facing=south,half=lower,hinge=left,open=false,powered=false]")
        bp.set(tx, 3, tz - 1, "waxed_copper_door[facing=south,half=upper,hinge=left,open=false,powered=false]")
        bp.set(tx, deck + 1, tz - 1, "air")
        bp.set(tx, deck + 2, tz - 1, "air")

    connect_panes(bp)

    # ---------------------------------------------------------------- hut block
    hx, hy, hz = hut
    tags = {hut: ["neoterra"], (C, 1, C - 20): ["groundlevel"]}
    for p in sit:
        tags.setdefault(p, []).append("sit")
    path = f"fundamentals/townhall{L}.blueprint"
    bp.set(hx, hy, hz, "minecolonies:blockhuttownhall[facing=north]",
           hut_te(path, (SX, SY, SZ), hut, tags))
    bp.primary_offset = hut
    bp.architects = ["Neoterra"]
    return bp


def rot(side, u, v):
    """Map (u = sideways, v = distance from centre) to x/z on the given side of the core."""
    return {"north": (C + u, C - v), "south": (C - u, C + v),
            "east": (C + v, C + u), "west": (C - v, C - u)}[side]


def _xz(xz, y):
    return xz[0], y, xz[1]


def side_of(x, z):
    dx, dz = x - C, z - C
    if abs(dx) >= abs(dz):
        return "east" if dx > 0 else "west"
    return "south" if dz > 0 else "north"


def spiral(bp: Blueprint, top: int, landing_mat: str, stair_block: str):
    """
    Square spiral stair in the 1-wide ring between the central column and the core wall.
    Rises one block per side cell; corners are flat landings. Returns the exits:
    ((cell_x, cell_z, wall_x, wall_z), floor_y) for every floor reached.
    """
    c = C
    cells = []  # (x, z, kind, facing, outward)
    cells.append((c - 2, c - 2, "corner", None, (0, -1)))
    for x in (c - 1, c, c + 1):
        cells.append((x, c - 2, "side", "east", (0, -1)))
    cells.append((c + 2, c - 2, "corner", None, (1, 0)))
    for z in (c - 1, c, c + 1):
        cells.append((c + 2, z, "side", "south", (1, 0)))
    cells.append((c + 2, c + 2, "corner", None, (0, 1)))
    for x in (c + 1, c, c - 1):
        cells.append((x, c + 2, "side", "west", (0, 1)))
    cells.append((c - 2, c + 2, "corner", None, (-1, 0)))
    for z in (c + 1, c, c - 1):
        cells.append((c - 2, z, "side", "north", (-1, 0)))

    floors = [f for f in FLOORS if f <= top]
    exits = []
    walk = 2          # current walking level (feet)
    i = 0
    done_floors = set()
    while True:
        x, z, kind, facing, (ox, oz) = cells[i % len(cells)]
        floor_here = walk - 1
        if floor_here in floors and floor_here not in done_floors:
            # landing + exit through the core wall
            if floor_here > 1:
                bp.set(x, floor_here, z, landing_mat)
            exits.append(((x, z, x + ox, z + oz), floor_here))
            done_floors.add(floor_here)
            if floor_here == top:
                break
        elif kind == "corner":
            bp.set(x, walk - 1, z, landing_mat)
        else:
            bp.set(x, walk, z, f"{stair_block}[facing={facing},half=bottom,shape=straight,waterlogged=false]")
            walk += 1
        i += 1
    return exits


if __name__ == "__main__":
    out_dir = Path(sys.argv[1])
    out_dir.mkdir(parents=True, exist_ok=True)
    for lvl in range(1, 6):
        b = build(lvl)
        b.save(out_dir / f"townhall{lvl}.blueprint")
        n = sum(1 for *_, s in b.blocks() if s != "minecraft:air")
        print(f"townhall{lvl}: {n} blocks")
