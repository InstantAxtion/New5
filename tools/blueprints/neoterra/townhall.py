"""
Neoterra Town Hall, levels 1-5 (MineColonies hut: minecolonies:blockhuttownhall).

Every level has the same 45 x 62 x 45 footprint, so upgrades build on top of each other.
The building grows upward with each level:

  L1  "Founding Hall"   round glass podium (r15) with the hut, reception, crafting/smelting
                        corner, a bed, and a spiral stair core up to a roof terrace.
  L2  "Civic Ring"      second floor ring building (r11): a full player workshop
                        (smithing, stonecutter, grindstone, anvil, loom, cartography,
                        fletching, blast furnace, smoker, brewing) + storage. Terrace railings.
  L3  "Archive Tower"   two-storey glass tower (r9): enchanting library (15+ bookshelves),
                        residents' quarters with beds, wrap-around balcony. Materials upgrade
                        to quartz, tinted glass, sea-lantern lighting, Domum Ornamentum trim.
  L4  "Sky Lounge"      glass sky lounge (r7) with ender chest, jukebox and bar, a roof deck,
                        and an exterior glass bubble-column elevator from the lobby to the deck.
  L5  "Spire"           spire with antenna, elytra launch pad, glowing halo ring, light fins,
                        plaza fountains and lamp spires.

Coordinates: x/z 0..44 (centre 22), y 0 = foundation (solid substitution), y 1 = ground.
The front (main entrance + launch pad) faces north (-z).
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
    early = Style(L).early          # levels 1-3 cheap, premium from level 4

    # ---------------------------------------------------------------- materials
    WHITE = "white_concrete"
    GLASS = "glass" if early else "light_blue_stained_glass"
    TRIM = "gray_concrete" if early else "polished_deepslate"
    ACCENT = "cyan_concrete"
    CORE = "light_gray_concrete" if early else WHITE
    SEAT = "polished_andesite_stairs" if early else "smooth_quartz_stairs"
    railing = Style(L).railing
    trim_slab = "smooth_stone_slab[type=bottom]" if early else do_slab(WHITE)

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
            return ACCENT
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
                if 17.5 <= d < 18.5:
                    bp.set(x, 1, z, "sea_lantern" if pillar_slot(x, z, 32, 0.12) else WHITE)
                elif 19.5 <= d < 20.5:
                    bp.set(x, 1, z, ACCENT)
                else:
                    bp.set(x, 1, z, "light_gray_concrete" if (x + z) % 2 else "smooth_stone")

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
            return ACCENT                       # lintel over the entrances
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
                return ACCENT if early else TRIM
            if pillar_slot(x, z, 16, 0.12):
                return WHITE
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
                return TRIM
            return GLASS
        ring(18, 24, 9, tower_wall)
        disc(25, 11, lambda x, z: WHITE if dist(x, z, C) >= 8.5 else floor_mat(x, z))   # floor + balcony
        ring(26, 26, 11, lambda x, y, z: railing)
        ring(26, 32, 9, tower_wall)
        disc(33, 9, lambda x, z: WHITE if dist(x, z, C) >= 8.5 else floor_mat(x, z))
        if not early:
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
        disc(41, 10, lambda x, z: WHITE if dist(x, z, C) >= 9.5 else ("smooth_quartz" if (x + z) % 2 else "light_gray_concrete"))
        ring(41, 41, 11, lambda x, y, z: do_stairs(WHITE, toward_center(x, z, C), half="top"))
        ring(42, 42, 10, lambda x, y, z: railing)
        for a in range(6):
            ang = math.radians(a * 60)
            x, z = round(C + 5 * math.cos(ang)), round(C + 5 * math.sin(ang))
            ceiling_light(x, 41, z)

    # ---------------------------------------------------------------- L5: spire, halo, fins
    if L >= 5:
        # halo ring around the sky lounge, carried on 4 spokes
        ring(37, 37, 12, lambda x, y, z: "sea_lantern" if pillar_slot(x, z, 24, 0.2) else WHITE)
        ring(37, 37, 13, lambda x, y, z: ACCENT)
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            for r in range(8, 12):
                bp.set(C + dx * r, 37, C + dz * r, "waxed_cut_copper")
        # vertical light fins on the tower
        for a in range(8):
            ang = math.radians(a * 45 + 22.5)
            x, z = round(C + 10 * math.cos(ang)), round(C + 10 * math.sin(ang))
            for y in range(18, 33):
                if y == 25:
                    continue
                bp.set(x, y, z, "sea_lantern" if y % 3 == 0 else WHITE)

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

    # spire on top of the core: glass lantern drum, tapering mast, antenna
    if L >= 5:
        y0 = core_top + 2                                   # 47
        for y in range(y0, y0 + 3):                         # 5x5 drum, glass faces + white corners
            for x in range(C - 2, C + 3):
                for z in range(C - 2, C + 3):
                    edge = max(abs(x - C), abs(z - C)) == 2
                    corner = abs(x - C) == 2 and abs(z - C) == 2
                    if edge:
                        bp.set(x, y, z, WHITE if corner else GLASS)
                    else:
                        bp.set(x, y, z, "sea_lantern")
        bp.fill(C - 2, y0 + 3, C - 2, C + 2, y0 + 3, C + 2, WHITE)
        for y in range(y0 + 4, y0 + 8):                     # 3x3 mast with cyan bands
            bp.fill(C - 1, y, C - 1, C + 1, y, C + 1, ACCENT if y % 2 == 0 else WHITE)
        for y in range(y0 + 8, y0 + 11):
            bp.set(C, y, C, WHITE)
        bp.set(C, y0 + 11, C, "sea_lantern")
        bp.set(C, y0 + 12, C, "end_rod[facing=up]")
        bp.set(C, y0 + 13, C, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):   # fins down the mast
            for y in range(y0 + 4, y0 + 7):
                put(bp, C + dx * 2, y, C + dz * 2, do_slab(WHITE, "top" if y % 2 else "bottom"))

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
    bp.set(C - 8, 2, C + 6, "cyan_bed[facing=south,occupied=false,part=foot]")
    bp.set(C - 8, 2, C + 7, "cyan_bed[facing=south,occupied=false,part=head]")
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
    if L >= 3:  # planters + benches around the plaza
        for a in range(12):
            if a % 3 == 0:
                continue                                  # keep the 4 approach paths clear
            ang = math.radians(a * 30)
            x, z = round(C + 19 * math.cos(ang)), round(C + 19 * math.sin(ang))
            bp.set(x, 1, z, "moss_block")
            bp.set(x, 2, z, "flowering_azalea")
    if L >= 4:  # fountains in the plaza corners
        for cx, cz in ((5, 5), (39, 5), (5, 39), (39, 39)):
            bp.fill(cx - 2, 1, cz - 2, cx + 2, 1, cz + 2, WHITE)
            bp.fill(cx - 1, 1, cz - 1, cx + 1, 1, cz + 1, "water[level=0]")
            bp.set(cx, 1, cz, "sea_lantern")
            bp.set(cx, 2, cz, "water[level=0]")
            bp.set(cx, 0, cz, "smooth_stone")
            for x in range(cx - 1, cx + 2):
                for z in range(cz - 1, cz + 2):
                    bp.set(x, 0, z, "smooth_stone")
    if L >= 5:  # lamp spires on the plaza ring + elytra launch pad
        for a in range(4):
            ang = math.radians(a * 90 + 45)
            x, z = round(C + 16.5 * math.cos(ang)), round(C + 16.5 * math.sin(ang))
            bp.fill(x, 2, z, x, 6, z, WHITE)
            bp.set(x, 7, z, "sea_lantern")
            bp.set(x, 8, z, "end_rod[facing=up]")
        # launch pad: cantilevered north from the roof deck
        for z in range(C - 18, C - 9):
            for x in range(C - 1, C + 2):
                bp.set(x, 41, z, "yellow_concrete" if z == C - 18 else ("sea_lantern" if x == C and z % 2 == 0 else "light_gray_concrete"))
            put(bp, C - 2, 42, z, railing)
            put(bp, C + 2, 42, z, railing)
            bp.set(C - 2, 41, z, WHITE)
            bp.set(C + 2, 41, z, WHITE)
        for x in range(C - 1, C + 2):
            bp.set(x, 42, C - 10, "air")                  # open the deck railing to the pad

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
                        bp.set(x, y, z, "tinted_glass" if y % 8 == 1 else "light_blue_stained_glass")
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
