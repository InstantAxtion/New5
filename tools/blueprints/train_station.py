"""
Generates a medium-sized modern train station as a Structurize/MineColonies blueprint.

Footprint: 37 (x, along the tracks) x 27 (z, street -> back) x 17 (y) blocks.
Vanilla blocks only, valid for Minecraft 1.20.1+ (newer versions are upgraded by DataFixers on load).

Layout along z (front of the station faces north, toward -z):
  z 0-2   street plaza with lamp posts, planters and entrance steps
  z 3-11  station hall: glass curtain-wall front, ticket counter, benches, departure board,
          clock tower on the roof
  z 12-14 platform 1 (side platform, attached to the hall)
  z 15-17 track 1   (rail at z16)
  z 18-20 platform 2/3 (island platform)
  z 21-23 track 2   (rail at z22)
  z 24-25 platform 4 (side platform)
  z 26    glass safety fence
Platforms have canopies with built-in lights; a covered glass footbridge at x32-35
links all platforms. Rails run the full length so you can connect your own lines on both ends.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from blueprint import Blueprint, parse_state, format_state  # noqa: E402

SX, SY, SZ = 37, 17, 27

# --- palette --------------------------------------------------------------
FOUNDATION = "stone"
PLAZA = "light_gray_concrete"
PLAZA_ACCENT = "smooth_stone"
HALL_FLOOR = "polished_andesite"
HALL_FLOOR_ACCENT = "white_concrete"
WALL = "white_concrete"
MULLION = "gray_concrete"
CURTAIN_GLASS = "light_blue_stained_glass"
ROOF = "smooth_stone"
COLUMN = "gray_concrete"
CANOPY = "smooth_quartz"
FASCIA = "white_concrete"
LIGHT = "sea_lantern"
PLATFORM = "smooth_stone"
PLATFORM_EDGE = "yellow_concrete"
BALLAST = "gravel"
RAIL = "rail[shape=east_west]"


def build() -> Blueprint:
    bp = Blueprint(SX, SY, SZ, "modern_train_station")
    bp.architects = ["New5"]
    f = bp.fill

    # ---------------- ground ----------------
    f(0, 0, 0, SX - 1, 0, SZ - 1, FOUNDATION)
    # plaza paving with a stripe pattern
    for x in range(SX):
        for z in range(0, 3):
            bp.set(x, 0, z, PLAZA_ACCENT if x % 4 == 0 else PLAZA)
    # side strips beside the hall
    f(0, 0, 3, 1, 0, 11, PLAZA)
    f(35, 0, 3, 36, 0, 11, PLAZA)

    # ---------------- tracks ----------------
    for zr in (16, 22):
        f(0, 0, zr - 1, SX - 1, 0, zr + 1, BALLAST)
        for x in range(SX):
            bp.set(x, 0, zr, "polished_andesite")  # sleeper bed under the rail
            bp.set(x, 1, zr, RAIL)

    # ---------------- platforms (surface at y1) ----------------
    platforms = [(12, 14, 14), (18, 20, None), (24, 25, 24)]
    for z1, z2, edge in platforms:
        f(3, 1, z1, 35, 1, z2, PLATFORM)
    # yellow safety lines along every edge that faces a track
    for z in (14, 18, 20, 24):
        f(3, 1, z, 35, 1, z, PLATFORM_EDGE)
    # platform end ramps (slabs) toward the outside ends
    for z1, z2, _ in platforms:
        f(2, 1, z1, 2, 1, z2, "smooth_stone_slab[type=bottom]")

    # glass safety fence at the back
    f(2, 1, 26, 36, 1, 26, PLATFORM)
    f(2, 2, 26, 36, 2, 26, "glass_pane")

    # ---------------- station hall: x2-34, z3-11, y1-9 ----------------
    hx1, hx2, hz1, hz2 = 2, 34, 3, 11
    f(hx1, 1, hz1, hx2, 1, hz2, HALL_FLOOR)
    # floor inlay: white border + grid lines
    for x in range(hx1 + 1, hx2):
        for z in range(hz1 + 1, hz2):
            if x in (hx1 + 1, hx2 - 1) or z in (hz1 + 1, hz2 - 1) or (x - 2) % 8 == 0:
                bp.set(x, 1, z, HALL_FLOOR_ACCENT)

    # walls
    f(hx1, 2, hz1, hx2, 8, hz1, CURTAIN_GLASS)  # front: full-height glass
    for x in range(hx1, hx2 + 1):
        if (x - hx1) % 4 == 0:
            f(x, 2, hz1, x, 8, hz1, MULLION)
    f(hx1, 5, hz1, hx2, 5, hz1, MULLION)  # transom band
    f(hx1, 2, hz1, hx1, 8, hz2, WALL)     # west wall
    f(hx2, 2, hz1, hx2, 8, hz2, WALL)     # east wall
    f(hx1, 2, hz2, hx2, 8, hz2, WALL)     # back wall
    # ribbon windows in the side walls
    f(hx1, 4, hz1 + 2, hx1, 6, hz2 - 2, CURTAIN_GLASS)
    f(hx2, 4, hz1 + 2, hx2, 6, hz2 - 2, CURTAIN_GLASS)
    # clerestory band in the back wall
    f(hx1 + 1, 7, hz2, hx2 - 1, 7, hz2, CURTAIN_GLASS)

    # main entrance (3 wide, 3 tall) + steps up from the plaza
    f(17, 2, hz1, 19, 4, hz1, "air")
    f(16, 1, 2, 20, 1, 2, "polished_andesite_stairs[facing=south,half=bottom,shape=straight]")
    # openings to platform 1
    for x0 in (9, 21):
        f(x0, 2, hz2, x0 + 2, 4, hz2, "air")

    # roof
    f(hx1, 9, hz1, hx2, 9, hz2, ROOF)
    for x in range(hx1 + 2, hx2 - 1, 4):  # recessed ceiling lights
        bp.set(x, 9, 5, LIGHT)
        bp.set(x, 9, 9, LIGHT)
    # parapet
    f(hx1, 10, hz1, hx2, 10, hz1, FASCIA)
    f(hx1, 10, hz2, hx2, 10, hz2, FASCIA)
    f(hx1, 10, hz1, hx1, 10, hz2, FASCIA)
    f(hx2, 10, hz1, hx2, 10, hz2, FASCIA)

    # cantilevered entrance canopy over the plaza
    f(13, 7, 0, 23, 7, 2, CANOPY)
    f(13, 7, 0, 23, 7, 0, FASCIA)
    for x in (15, 18, 21):
        bp.set(x, 7, 1, LIGHT)

    # clock tower on the north-west corner (x2-6, z3-7) rising above the roof to y16,
    # with a clock face on the street (north) side and the west side
    f(2, 10, 3, 6, 15, 7, WALL)
    f(2, 15, 3, 6, 15, 7, MULLION)                                 # dark cap band
    f(2, 16, 3, 6, 16, 7, "smooth_stone_slab[type=bottom]")
    f(3, 9, 4, 5, 9, 6, LIGHT)                                      # light under the tower
    # face: black 3x3 dial with a white hub and a hand pointing to 12
    for u in (-1, 0, 1):
        for v in (-1, 0, 1):
            bp.set(4 + u, 12 + v, 3, "black_concrete")              # north face, centre x4
            bp.set(2, 12 + v, 5 + u, "black_concrete")              # west face, centre z5
    for pos in ((4, 12, 3), (4, 13, 3), (3, 12, 3), (2, 12, 5), (2, 13, 5), (2, 12, 6)):
        bp.set(*pos, "white_concrete")                              # hub, minute + hour hand

    # ---- interior ----
    # ticket counter (east end)
    f(26, 2, 6, 32, 2, 6, "smooth_quartz")
    f(26, 3, 6, 32, 3, 6, "glass_pane")
    f(26, 4, 6, 32, 4, 6, "smooth_quartz_slab[type=bottom]")
    for x in (27, 29, 31):
        bp.set(x, 3, 6, "air")  # ticket windows
    f(33, 2, 4, 33, 2, 9, "smooth_quartz")  # back office counter
    # departure board on the back wall (inside face)
    f(12, 5, hz2, 24, 6, hz2, "black_concrete")
    for x in range(13, 24, 2):
        bp.set(x, 5, hz2, "yellow_concrete")
        bp.set(x + 1 if x + 1 < 24 else x, 6, hz2, "orange_concrete")
    # waiting benches (two rows, back to back)
    for x0 in (8, 14):
        f(x0, 2, 6, x0 + 3, 2, 6, "dark_oak_stairs[facing=south,half=bottom,shape=straight]")
        f(x0, 2, 7, x0 + 3, 2, 7, "dark_oak_stairs[facing=north,half=bottom,shape=straight]")
    # planters in the hall corners
    for x, z in ((5, 4), (5, 10), (24, 4), (24, 10)):
        bp.set(x, 2, z, "moss_block")
        bp.set(x, 3, z, "flowering_azalea")

    # ---------------- platform canopies ----------------
    def canopy(z1, z2, col_z, light_z, fascia_zs):
        f(3, 6, z1, 27, 6, z2, CANOPY)
        for z in fascia_zs:
            f(3, 6, z, 27, 6, z, FASCIA)
        for x in range(5, 27, 6):
            f(x, 2, col_z, x, 5, col_z, COLUMN)
        for x in range(8, 27, 6):
            bp.set(x, 6, light_z, LIGHT)

    canopy(12, 15, col_z=13, light_z=14, fascia_zs=(15,))
    canopy(17, 21, col_z=19, light_z=19, fascia_zs=(17, 21))
    canopy(23, 25, col_z=25, light_z=24, fascia_zs=(23,))

    # platform benches between the columns
    for x0 in (7, 13, 19):
        f(x0, 2, 12, x0 + 1, 2, 12, "dark_oak_stairs[facing=north,half=bottom,shape=straight]")
        f(x0, 2, 19, x0 + 1, 2, 19, "dark_oak_stairs[facing=north,half=bottom,shape=straight]")
        f(x0, 2, 25, x0 + 1, 2, 25, "dark_oak_stairs[facing=south,half=bottom,shape=straight]")

    # ---------------- footbridge: deck x32-35, z12-25, floor y5 ----------------
    f(32, 5, 11, 35, 5, 26, "smooth_quartz")
    f(32, 6, 12, 32, 7, 25, CURTAIN_GLASS)
    f(35, 6, 11, 35, 7, 26, CURTAIN_GLASS)
    f(32, 6, 26, 35, 7, 26, CURTAIN_GLASS)
    f(32, 8, 11, 35, 8, 26, FASCIA)
    for z in range(13, 26, 4):
        bp.set(33, 8, z, LIGHT)
        bp.set(34, 8, z, LIGHT)
    # deck support columns
    for z in (13, 19, 25):
        f(35, 2, z, 35, 4, z, COLUMN)
    # staircases from each platform up to the deck (rising toward +x)
    for z1, z2 in ((12, 13), (18, 19), (24, 25)):
        f(32, 6, z1, 32, 7, z2, "air")  # opening in the bridge wall
        for i, x in enumerate(range(28, 32)):
            y_top = 2 + i
            if y_top > 2:
                f(x, 2, z1, x, y_top - 1, z2, WALL)
            f(x, y_top, z1, x, y_top, z2,
              "smooth_quartz_stairs[facing=east,half=bottom,shape=straight]")

    # ---------------- plaza furniture ----------------
    for x in (6, 30):
        f(x, 1, 1, x, 3, 1, "polished_blackstone_wall")
        bp.set(x, 4, 1, "lantern[hanging=false]")
    for x in (10, 26):
        bp.set(x, 1, 0, "moss_block")
        bp.set(x, 2, 0, "flowering_azalea")

    connect_panes(bp)

    # Build Tool anchor: front-centre of the plaza at ground level.
    bp.primary_offset = (18, 0, 0)
    return bp


PANE_LIKE = ("glass_pane", "iron_bars")


def connect_panes(bp: Blueprint):
    """Give glass panes / iron bars the right side connections (they do not auto-update on paste)."""
    dirs = {"north": (0, -1), "south": (0, 1), "west": (-1, 0), "east": (1, 0)}
    for x, y, z, s in list(bp.blocks()):
        name, props = parse_state(s)
        if not name.endswith(PANE_LIKE):
            continue
        for d, (dx, dz) in dirs.items():
            n = parse_state(bp.get(x + dx, y, z + dz))[0]
            solid = n != "minecraft:air" and not any(k in n for k in ("stairs", "slab", "lantern", "rail"))
            props[d] = "true" if solid else "false"
        props["waterlogged"] = "false"
        bp.grid[y][z][x] = format_state(name, props)


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "modern_train_station.blueprint")
    out.parent.mkdir(parents=True, exist_ok=True)
    bp = build()
    bp.save(out)
    print(f"wrote {out}")
