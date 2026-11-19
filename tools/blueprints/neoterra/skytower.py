"""
Neoterra Skytower: apartment tower with a penthouse that houses up to 25 citizens.

MineColonies caps one residence hut at 5 residents (residents = hut level). The Skytower gets
past that the same way the official barracks contain barracks towers: hut blocks placed inside
a building's blueprint become child buildings of it.

  skytower1-5       the tower itself (residence hut in the lobby). Its residents live in the
                    glass penthouse (1-5 beds with the tower's level). Each level also upgrades
                    the shell: L1 full tower shell + stair core, L2 lobby + trees, L3 balconies +
                    roof garden, L4 premium palette + roof trees + lamps, L5 glowing crown.
  skytowerflat1-5   one apartment floor. The tower places 4 of these as child residence huts
                    (level 0); upgrade each floor's hut separately, 1-5 beds each.
                    Tagged "invisible" so it does not clutter the Build Tool list.

Inside the tower blueprint the four apartment interiors are `structurize:blocksubstitution`
(leave as is), so upgrading the tower never overwrites the flats and vice versa.

Tower: 19 x 40 x 19. Front = north (z 0).
"""
from __future__ import annotations

import sys
from pathlib import Path

from nbtlib import tag as T

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    Blueprint, Style, put, hut_te, connect_panes, tree, planter, street_lamp, do_slab,
    bed, door, chair, PACK_NAME,
)

SX, SY, SZ = 19, 40, 19
X1, X2, Z1, Z2 = 2, 16, 3, 15            # shell
STOREY = 5
FLOORS = [1, 6, 11, 16, 21]              # lobby + 4 apartment floors (slab heights)
PENT = 26                                # penthouse floor slab
PENT_ROOF = 33
FLAT_X1, FLAT_X2, FLAT_Z1, FLAT_Z2 = 3, 12, 4, 14     # apartment interior (child region)
FLAT_HUT = (4, 9)                        # (x, z) of each apartment's hut block
FLAT_SIZE = (FLAT_X2 - FLAT_X1 + 1, STOREY - 1, FLAT_Z2 - FLAT_Z1 + 1)


def edge(x, z, x1, x2, z1, z2):
    return x in (x1, x2) or z in (z1, z2)


def child_hut_te(path):
    """A not-yet-built (level 0) child hut, mirroring the official barracks towers."""
    zero = T.Compound({"x": T.Int(0), "y": T.Int(0), "z": T.Int(0)})
    return T.Compound({
        "id": T.String("minecolonies:colonybuilding"),
        "mirror": T.Byte(0), "inWarehouse": T.Byte(0), "colony": T.Int(0),
        "type": T.String("minecraft:"), "version": T.Int(0), "tagSIze": T.Int(0), "Item": T.String(""),
        "pack": T.String(PACK_NAME), "path": T.String(path),
        "blueprintDataProvider": T.Compound({
            "corner1": zero, "corner2": zero, "path": T.String(path),
            "schematicName": T.String(Path(path).stem), "pack": T.String(PACK_NAME),
            "posTagMap": T.List[T.Compound]([]),
        }),
    })


# ---------------------------------------------------------------------------- apartment floor
def flat_interior(bp, level, ox, oy, oz, sit):
    """Furnish one apartment (level = beds). (ox, oy, oz) = world pos of the region's corner."""
    st = Style(level)

    def P(x, z):  # world x/z of a tower coordinate inside the flat
        return x - FLAT_X1 + ox, z - FLAT_Z1 + oz
    y = oy
    for i, bx in enumerate((3, 5, 7, 9, 11)[:level]):
        x, z = P(bx, 13)
        bed(bp, x, y, z, "south")
    for z, s in ((6, "furnace[facing=west,lit=false]"), (7, "smoker[facing=west,lit=false]"),
                 (8, "crafting_table"), (9, "barrel[facing=west,open=false]")):     # (12,5)/(12,11) = doorways
        x, zz = P(12, z)
        bp.set(x, y, zz, s)
    x, z = P(7, 8)
    put(bp, x, y, z, st.counter)                                         # dining table
    chair(bp, x - 1, y, z, st.SEAT, "west", sit)
    chair(bp, x + 1, y, z, st.SEAT, "east", sit)
    if level >= 2:
        for bx in (4, 5, 6):
            x, z = P(bx, 5)
            chair(bp, x, y, z, st.SEAT, "south", sit)                    # sofa facing the window
    if level >= 3:
        x, z = P(10, 5)
        planter(bp, x, y, z)
    if level >= 4:
        x, z = P(3, 10)
        bp.set(x, y, z, "bookshelf")
        bp.set(x, y + 1, z, "bookshelf")
        x, z = P(3, 9)
        bp.set(x, y, z, "jukebox[has_record=false]")
    if level >= 5:
        x, z = P(12, 10)
        bp.set(x, y, z, "ender_chest[facing=west,waterlogged=false]")
    for bx, bz in ((5, 7), (9, 7), (6, 11), (10, 11)):
        x, z = P(bx, bz)
        if bp.get(x, y + 3, z) == "minecraft:air":
            bp.set(x, y + 3, z, "lantern[hanging=true,waterlogged=false]")


def build_flat(level: int) -> Blueprint:
    sx, sy, sz = FLAT_SIZE
    bp = Blueprint(sx, sy, sz, f"skytowerflat{level}.blueprint")
    sit = []
    flat_interior(bp, level, 0, 0, 0, sit)
    hut = (FLAT_HUT[0] - FLAT_X1, 0, FLAT_HUT[1] - FLAT_Z1)
    tags = {hut: ["invisible"]}
    for p in sit:
        tags.setdefault(p, []).append("sit")
    path = f"fundamentals/skytowerflat{level}.blueprint"
    bp.set(*hut, "minecolonies:blockhutcitizen[facing=north]", hut_te(path, (sx, sy, sz), hut, tags))
    bp.primary_offset = hut
    bp.architects = ["Neoterra"]
    return bp


# ---------------------------------------------------------------------------- tower
def build_tower(level: int, preview_flats: int = 0) -> Blueprint:
    """preview_flats > 0 furnishes the apartments (for preview images only, never saved)."""
    L, st = level, Style(level)
    bp = Blueprint(SX, SY, SZ, f"skytower{L}.blueprint")
    W, G, TR, D = st.WHITE, st.GLASS, st.TRIM, st.DECK
    glow, band = st.GLOW, st.band
    sit = []

    bp.fill(0, 0, 0, SX - 1, 0, SZ - 1, "structurize:blocksolidsubstitution")
    for x in range(SX):
        for z in range(SZ):
            if 8 <= x <= 10 and z < Z1:
                s = W if x in (8, 10) else "smooth_stone"
            elif X1 <= x <= X2 and Z1 <= z <= Z2:
                s = st.floor(x, z)
            else:
                s = "grass_block[snowy=false]"
            bp.set(x, 1, z, s)

    # ------------------------------------------------ storeys: slabs, walls, core partition
    for i, F in enumerate(FLOORS + [PENT]):
        if i > 0:
            for x in range(X1, X2 + 1):
                for z in range(Z1, Z2 + 1):
                    bp.set(x, F, z, band if edge(x, z, X1, X2, Z1, Z2) else st.floor(x, z))
        top = F + STOREY if F != PENT else PENT_ROOF
        for x in range(X1, X2 + 1):
            for z in range(Z1, Z2 + 1):
                if not edge(x, z, X1, X2, Z1, Z2):
                    continue
                for y in range(F + 1, top):
                    corner = x in (X1, X2) and z in (Z1, Z2)
                    if F == PENT:
                        s = ("sea_lantern" if not st.early else W) if corner else G       # all-glass penthouse
                    elif corner:
                        s = W
                    elif z == Z1:
                        s = st.WOOD if (x - X1) % 3 == 0 else G
                    elif y in (F + 2, F + 3) and (x + z) % 3:
                        s = G
                    else:
                        s = W
                    bp.set(x, y, z, s)
        if F != PENT:
            for y in range(F + 1, F + STOREY):
                for z in range(Z1 + 1, 13):
                    bp.set(13, y, z, W)
                for x in (14, 15):
                    bp.set(x, y, 12, W)
            for z in (5, 11):
                for y in (F + 1, F + 2):
                    bp.set(13, y, z, "air")
    # roof
    for x in range(X1, X2 + 1):
        for z in range(Z1, Z2 + 1):
            e = edge(x, z, X1, X2, Z1, Z2)
            bp.set(x, PENT_ROOF, z, band if e else ("smooth_stone" if L < 3 else "grass_block[snowy=false]"))
            if e:
                put(bp, x, PENT_ROOF + 1, z, st.railing)

    # ------------------------------------------------ stair runs (lobby -> 4 floors -> penthouse)
    for i, F in enumerate(FLOORS):
        if i % 2 == 0:
            col, zs, facing = 15, list(range(6, 11)), "south"
        else:
            col, zs, facing = 14, list(range(10, 5, -1)), "north"
        for z in zs[:4]:
            bp.set(col, F + STOREY, z, "air")
        for k, z in enumerate(zs):
            bp.set(col, F + 1 + k, z, f"{st.SEAT}[facing={facing},half=bottom,shape=straight,waterlogged=false]")
    # guard rail around the stairwell opening in the penthouse floor (last run: col 15)
    for z in range(5, 11):
        put(bp, 14, PENT + 1, z, st.railing)
    put(bp, 15, PENT + 1, 5, st.railing)

    # ------------------------------------------------ apartment floors: child huts + substitution
    for F in FLOORS[1:]:
        for x in range(FLAT_X1, FLAT_X2 + 1):
            for z in range(FLAT_Z1, FLAT_Z2 + 1):
                for y in range(F + 1, F + STOREY):
                    bp.set(x, y, z, "structurize:blocksubstitution")
        hx, hz = FLAT_HUT
        if preview_flats:
            for x in range(FLAT_X1, FLAT_X2 + 1):
                for z in range(FLAT_Z1, FLAT_Z2 + 1):
                    for y in range(F + 1, F + STOREY):
                        bp.set(x, y, z, "minecraft:air")
            flat_interior(bp, preview_flats, FLAT_X1, F + 1, FLAT_Z1, [])
        bp.set(hx, F + 1, hz, "minecolonies:blockhutcitizen[facing=north]",
               child_hut_te("fundamentals/skytowerflat0.blueprint"))
        # balconies (part of the shell) from level 3
        if L >= 3:
            for x in range(4, 11):
                for z in range(0, Z1):
                    e = x in (4, 10) or z == 0
                    bp.set(x, F, z, (glow or W) if e else D)
                    if e:
                        put(bp, x, F + 1, z, st.railing)
            for x in (6, 7):
                for y in (F + 1, F + 2):
                    bp.set(x, y, Z1, "air")

    # ------------------------------------------------ lobby (tower hut)
    hut = (6, 2, 6)
    put(bp, 6, 2, 7, st.counter)
    door(bp, 9, 2, Z1, "south", "birch" if st.early else "waxed_copper")
    for z in range(8, 13):
        bp.set(3, 2, z, "barrel[facing=east,open=false]")                 # parcel boxes
    if L >= 2:
        for x in (8, 9, 10):
            chair(bp, x, 2, 10, st.SEAT, "south", sit)
        planter(bp, 11, 2, 5)
        planter(bp, 3, 2, 5)
        tree(bp, 1, 2, 1, h=3)
        tree(bp, 17, 2, 1, h=3)
    for x, z in ((5, 9), (9, 7), (9, 12)):
        st.ceiling_light(bp, x, FLOORS[1], z)

    # ------------------------------------------------ penthouse (tower residents)
    y = PENT + 1
    for bx in (3, 5, 7, 9, 11)[:L]:
        bed(bp, bx, y, 13, "south")
    for bx in (4, 5, 6, 7):
        chair(bp, bx, y, 5, st.SEAT, "south", sit)
    put(bp, 9, y, 8, st.counter)
    chair(bp, 8, y, 8, st.SEAT, "west", sit)
    chair(bp, 10, y, 8, st.SEAT, "east", sit)
    for z, s in ((5, "furnace[facing=west,lit=false]"), (6, "smoker[facing=west,lit=false]"),
                 (7, "crafting_table"), (8, "barrel[facing=west,open=false]")):
        bp.set(12, y, z, s)
    bp.set(13, y, 14, "jukebox[has_record=false]")
    bp.set(14, y, 14, "ender_chest[facing=north,waterlogged=false]")
    for x, z in ((5, 8), (9, 11), (5, 12)):
        st.ceiling_light(bp, x, PENT_ROOF, z)
    for yy in range(PENT + 1, PENT_ROOF + 1):
        bp.set(15, yy, 14, "ladder[facing=west,waterlogged=false]")      # up to the roof garden

    # ------------------------------------------------ roof garden, premium extras, crown
    if L >= 3:
        for x in (4, 8, 12):
            planter(bp, x, PENT_ROOF + 1, 6)
        for x in (6, 7, 8):
            chair(bp, x, PENT_ROOF + 1, 12, st.SEAT, "south", sit)
    if L >= 4:
        tree(bp, 5, PENT_ROOF + 1, 9, h=2)
        tree(bp, 11, PENT_ROOF + 1, 9, h=2)
        street_lamp(bp, 7, 2, 0, premium=True)
        street_lamp(bp, 11, 2, 0, premium=True)
    if L >= 5:
        for x, z in ((X1, Z1), (X2, Z1), (X1, Z2), (X2, Z2)):
            bp.fill(x, PENT_ROOF + 1, z, x, PENT_ROOF + 3, z, W)
        for x in range(X1, X2 + 1):
            for z in range(Z1, Z2 + 1):
                if edge(x, z, X1, X2, Z1, Z2):
                    bp.set(x, PENT_ROOF + 4, z, "sea_lantern" if (x + z) % 2 else W)   # glowing crown
        bp.set(9, PENT_ROOF + 1, 14, TR)
        for yy in range(PENT_ROOF + 2, SY - 1):
            bp.set(9, yy, 14, "chain[axis=y,waterlogged=false]")
        bp.set(9, SY - 1, 14, "lightning_rod[facing=up,powered=false,waterlogged=false]")

    connect_panes(bp)
    tags = {hut: ["neoterra"], (0, 1, 0): ["groundlevel"]}
    for p in sit:
        tags.setdefault(p, []).append("sit")
    path = f"fundamentals/skytower{L}.blueprint"
    bp.set(*hut, "minecolonies:blockhutcitizen[facing=north]", hut_te(path, (SX, SY, SZ), hut, tags))
    bp.primary_offset = hut
    bp.architects = ["Neoterra"]
    return bp


if __name__ == "__main__":
    out_dir = Path(sys.argv[1])
    out_dir.mkdir(parents=True, exist_ok=True)
    for lvl in range(1, 6):
        t = build_tower(lvl)
        t.save(out_dir / f"skytower{lvl}.blueprint")
        f = build_flat(lvl)
        f.save(out_dir / f"skytowerflat{lvl}.blueprint")
        n = sum(1 for *_, s in t.blocks() if s not in ("minecraft:air", "structurize:blocksolidsubstitution",
                                                        "structurize:blocksubstitution"))
        print(f"skytower{lvl}: {n} blocks, penthouse beds {lvl}; skytowerflat{lvl}: {lvl} beds")
    if len(sys.argv) > 2:  # preview copies with furnished flats
        prev = Path(sys.argv[2])
        prev.mkdir(parents=True, exist_ok=True)
        for lvl in range(1, 6):
            build_tower(lvl, preview_flats=lvl).save(prev / f"skytower{lvl}_furnished.blueprint")
