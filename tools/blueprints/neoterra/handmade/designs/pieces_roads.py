"""
Road pieces – hand-designed streets for Neoterra, Hearthwood and Cascadia.

Pieces (sizes and anchors unchanged from the generated set):
  roadstraight      7x7x8   anchor (3,1,4)  street running north-south (along z)
  roadcorner        7x7x7   anchor (3,1,3)  street turning from the north edge to the east edge
  roadtjunction     13x7x7  anchor (6,1,3)  through street east-west, branch leaving the south edge (x 3..9)
  roadintersection  13x7x13 anchor (6,1,6)  two streets crossing; 3-long arms with crossings, 3x3 corner plazas
  avenue            13x7x16 anchor (6,1,8)  boulevard along z with a planted 3-wide median (tiles with itself)
  roadstairs        7x9x8   anchor (3,1,0)  street stair climbing south: rise RISE over 8 blocks, mid landing

Cross-section (all packs, all 7-wide pieces), index a across the street:
  a = 0 and a = 6   sidewalk: base block at y = 1, raised paving slab at y = 2 (curb = the slab edge)
  a = 1 .. 5        carriageway at y = 1 (a = 1 / 5 gutter side, a = 3 centre)
Pieces join edge to edge: carriageway to carriageway, sidewalk slabs to sidewalk slabs, all at the same height.
Street lamps stand on the sidewalk, staggered (west side z = 1, east side z = 5 on a straight) so a run of
straights gives a lamp every 8 blocks on each side, 4 apart across the street.

Packs:
  Neoterra    gray-concrete asphalt with a dashed white centre line, smooth-stone pavements with andesite
              joints, iron grate drains at the curb, white zebra crossings with sandstone tactile strips, slim
              column lights (sea-lantern head, solar-panel cap), birch tree pits and moss planters; avenue with
              green cycle lanes and a birch-planted median with double lights.
  Hearthwood  stone-sett lanes with a cobbled centre kennel (gutter) and iron grates, brick pavements with
              stone bands, black Victorian lamp posts, calcite/deepslate zebras with Belisha beacons, box
              hedges, flower beds and a finger post; avenue as a hedged village green with oaks.
  Cascadia    packed-dirt road with wheel ruts and gravel ditches, river-rock sumps, raised spruce boardwalks
              on log curbs, log lamp posts with gallows brackets and hanging lanterns, corduroy log crossings,
              rail fences, firs, boulders, barrels and a wooden signpost; avenue with a fir-lined rock median.
"""
from hm import Design, design, AIR

PACKS = ("Neoterra", "Hearthwood", "Cascadia")
W = 7            # street width (sidewalk + 5 carriageway + sidewalk)
GY = 1           # carriageway surface layer
CURB = 2         # sidewalk paving slab layer
RISE = 4         # roadstairs: the street at the top is RISE blocks higher
STAIR_Y = [1, 2, 3, 3, 3, 4, 5, 5]   # roadstairs walking-surface block per z row (z0 landing, z3-4 mid landing)


def slab(n, t="bottom"):
    return f"{n}[type={t},waterlogged=false]"


def stairs(n, facing, half="bottom"):
    return f"{n}[facing={facing},half={half},shape=straight,waterlogged=false]"


def wall(n):
    return f"{n}[east=none,north=none,south=none,up=true,waterlogged=false,west=none]"


def leaves(n):
    return f"{n}_leaves[distance=1,persistent=true,waterlogged=false]"


def log(n, axis="y"):
    return f"{n}[axis={axis}]"


GRATE = "iron_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]"
LANTERN = "lantern[hanging=false,waterlogged=false]"
HANGING = "lantern[hanging=true,waterlogged=false]"


# ============================================================================================ pack styles
class Style:
    """Materials of one pack's street. carr(a, t): carriageway block at across-index a (1..5), along-index t."""

    def __init__(self, pack):
        self.pack = pack
        if pack == "Neoterra":
            self.base, self.pave, self.joint = "smooth_stone", "smooth_stone_slab", "polished_andesite_slab"
            self.tactile = "smooth_sandstone_slab"
            self.zebra = ("white_concrete", "gray_concrete")
        elif pack == "Hearthwood":
            self.base, self.pave, self.joint = "bricks", "brick_slab", "stone_brick_slab"
            self.tactile = None
            self.zebra = ("calcite", "polished_deepslate")
        else:
            self.base, self.pave, self.joint = "stripped_spruce_log", "spruce_slab", "dark_oak_slab"
            self.tactile = None
            self.zebra = None

    def carr(self, a, t):
        if self.pack == "Neoterra":
            return "gray_concrete"
        if self.pack == "Hearthwood":
            if a == 3:
                return "cobblestone"                                   # centre kennel
            return self.sett(a, t)
        return {1: "gravel", 2: "dirt_path", 3: "coarse_dirt", 4: "dirt_path", 5: "gravel"}[a]

    def sett(self, x, z):
        """Hearthwood sett texture: mostly stone bricks, a cracked sett and a worn andesite sett in a fixed weave."""
        k = (x * 3 + z * 5) % 11
        return "cracked_stone_bricks" if k == 0 else "andesite" if k == 6 else "stone_bricks"

    def plain(self, x, z):
        """Junction box surface (no lanes)."""
        if self.pack == "Neoterra":
            return "gray_concrete"
        if self.pack == "Hearthwood":
            return self.sett(x, z)
        return "gravel" if (x * 3 + z * 5) % 9 == 0 else "coarse_dirt"


# -------------------------------------------------------------------------------------- cell painters
def sidewalk(d, S, x, z, joint=False, axis="z", y=GY):
    base = S.base if S.pack != "Cascadia" else log(S.base, axis)
    d.set(x, y, z, base)
    d.set(x, y + 1, z, slab(S.joint if joint else S.pave))


def tactile(d, S, x, z, axis="z"):
    if S.tactile:
        base = S.base
        d.set(x, GY, z, base)
        d.set(x, CURB, z, slab(S.tactile))
    else:
        sidewalk(d, S, x, z, axis=axis)


def crossing(d, S, x, z, stripe, axis, mid=True, a=3, t=0):
    """One cell of a pedestrian crossing. stripe: True = light stripe. axis: direction pedestrians walk.
    Cascadia lays a single corduroy row of logs (mid=True cells) across its dirt road; elsewhere the road."""
    if S.zebra:
        d.set(x, GY, z, S.zebra[0] if stripe else S.zebra[1])
    elif mid:
        d.set(x, GY, z, log("spruce_log", axis))
    else:
        d.set(x, GY, z, S.carr(a, t))


# ----------------------------------------------------------------------------------------- street props
def neo_lamp(d, x, z, y=CURB):
    """Neoterra column light: andesite plinth, slim iron pole, sea-lantern head, solar cap."""
    d.set(x, y, z, "polished_andesite")
    d.set(x, y + 1, z, "iron_bars")
    d.set(x, y + 2, z, "iron_bars")
    d.set(x, y + 3, z, "sea_lantern")
    d.set(x, y + 4, z, "daylight_detector[inverted=false,power=0]")


def hw_lamp(d, x, z, y=CURB):
    """Hearthwood Victorian lamp post: black (deepslate) post, lantern on top."""
    for k in range(3):
        d.set(x, y + k, z, wall("polished_deepslate_wall"))
    d.set(x, y + 3, z, LANTERN)


def hw_beacon(d, x, z, y=CURB):
    """Belisha beacon: black-and-white striped pole with an amber globe."""
    d.set(x, y, z, wall("polished_deepslate_wall"))
    d.set(x, y + 1, z, wall("diorite_wall"))
    d.set(x, y + 2, z, wall("polished_deepslate_wall"))
    d.set(x, y + 3, z, "glowstone")


def cas_lamp(d, x, z, arm=None, y=CURB):
    """Cascadia log lamp post; with `arm` (dx, dz) a gallows bracket carries a hanging lantern over the road,
    without one the lantern stands on a fence cap."""
    if arm:
        for k in range(4):
            d.set(x, y + k, z, log("spruce_log"))
        ax, az = x + arm[0], z + arm[1]
        d.set(ax, y + 3, az, "spruce_fence")
        d.set(ax, y + 2, az, HANGING)
    else:
        for k in range(3):
            d.set(x, y + k, z, log("spruce_log"))
        d.set(x, y + 3, z, "spruce_fence")
        d.set(x, y + 4, z, LANTERN)


def birch_tree(d, x, z, y):
    """Small birch: trunk from y, crown on the two layers above (3x3 + cross)."""
    for k in range(3):
        d.set(x, y + k, z, log("birch_log"))
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            if (dx, dz) != (0, 0):
                d.set(x + dx, y + 3, z + dz, leaves("birch"))
    d.set(x, y + 3, z, log("birch_log"))
    for dx, dz in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
        d.set(x + dx, y + 4, z + dz, leaves("birch"))


def oak_tree(d, x, z, y):
    for k in range(3):
        d.set(x, y + k, z, log("oak_log"))
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            if (dx, dz) != (0, 0):
                d.set(x + dx, y + 2, z + dz, leaves("oak"))
                if abs(dx) + abs(dz) == 1:
                    d.set(x + dx, y + 3, z + dz, leaves("oak"))
    d.set(x, y + 3, z, leaves("oak"))


def fir(d, x, z, y):
    """Small fir (spruce): trunk y..y+2, tiered crown y+1..y+4."""
    for k in range(3):
        d.set(x, y + k, z, log("spruce_log"))
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            if (dx, dz) != (0, 0):
                d.set(x + dx, y + 1, z + dz, leaves("spruce"))
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        d.set(x + dx, y + 2, z + dz, leaves("spruce"))
    d.set(x, y + 3, z, leaves("spruce"))
    d.set(x, y + 4, z, leaves("spruce"))


def new(pack, rel, size, anchor):
    d = Design(pack, rel, size=size, gy=GY)
    d.anchor(*anchor)
    return d, Style(pack)


# ============================================================================================ straight
@design("roadstraight")
def roadstraight(pack, rel, L):
    d, S = new(pack, rel, (7, 7, 8), (3, 1, 4))
    for z in range(8):
        sidewalk(d, S, 0, z, joint=z in (0, 4))
        sidewalk(d, S, 6, z, joint=z in (0, 4))
        for a in range(1, 6):
            d.set(a, GY, z, S.carr(a, z))
    if pack == "Neoterra":
        for z in (2, 3, 4, 5):
            d.set(3, GY, z, "white_concrete")                         # dashed centre line, 4 on / 4 off
        d.set(5, GY, 1, GRATE)
        d.set(1, GY, 5, GRATE)
        neo_lamp(d, 0, 1)
        neo_lamp(d, 6, 5)
    elif pack == "Hearthwood":
        d.set(3, GY, 1, GRATE)                                         # kennel grates every 4
        d.set(3, GY, 5, GRATE)
        hw_lamp(d, 0, 1)
        hw_lamp(d, 6, 5)
    else:
        d.set(5, GY, 1, "mossy_cobblestone")                           # river-rock sumps in the ditches
        d.set(1, GY, 5, "mossy_cobblestone")
        cas_lamp(d, 0, 1, arm=(1, 0))
        cas_lamp(d, 6, 5, arm=(-1, 0))
    return d


# ============================================================================================ corner
@design("roadcorner")
def roadcorner(pack, rel, L):
    """North edge -> east edge. Outer sidewalk along the west and south edges with a fillet at (1,5); inner
    corner sidewalk cell (6,0) joins the two inner sidewalks."""
    d, S = new(pack, rel, (7, 7, 7), (3, 1, 3))
    side = {(0, z) for z in range(7)} | {(x, 6) for x in range(7)} | {(6, 0), (1, 5)}
    for z in range(7):
        for x in range(7):
            if (x, z) in side:
                axis = "x" if z == 6 and x > 0 else "z"
                sidewalk(d, S, x, z, joint=(x, z) in ((0, 0), (0, 6), (6, 6), (6, 0), (1, 5)), axis=axis)
            else:
                a = 6 - max(6 - x, z)                                  # square ring around the inner corner
                d.set(x, GY, z, S.carr(a, x + z))
    if pack == "Neoterra":
        for x, z in ((3, 1), (3, 2), (4, 3), (5, 3)):
            d.set(x, GY, z, "white_concrete")
        d.set(1, GY, 3, GRATE)
        d.set(3, GY, 5, GRATE)
        neo_lamp(d, 0, 6)
    elif pack == "Hearthwood":
        d.set(3, GY, 3, GRATE)
        hw_lamp(d, 0, 6)
    else:
        d.set(1, GY, 3, "mossy_cobblestone")
        d.set(3, GY, 5, "mossy_cobblestone")
        cas_lamp(d, 0, 6)
    return d


# ============================================================================================ T junction
@design("roadtjunction")
def roadtjunction(pack, rel, L):
    """Through street east-west (a = z), branch to the south through x 3..9; crossings on both stubs."""
    d, S = new(pack, rel, (13, 7, 7), (6, 1, 3))
    stubs = (0, 1, 2, 10, 11, 12)
    for x in range(13):
        if x in (1, 11):
            tactile(d, S, x, 0, axis="x")
        else:
            sidewalk(d, S, x, 0, joint=x in (3, 6, 9), axis="x")
        for z in range(1, 6):
            if x in stubs:
                crossing(d, S, x, z, z % 2 == 1, "z", mid=x in (1, 11), a=z, t=x)
            else:
                d.set(x, GY, z, S.carr(z, x))
        if x in (1, 11):
            tactile(d, S, x, 6, axis="x")
        elif x in stubs:
            sidewalk(d, S, x, 6, axis="x")
        elif x in (3, 9):
            sidewalk(d, S, x, 6, joint=True)
        else:
            d.set(x, GY, 6, S.carr(x - 3, 0) if pack != "Hearthwood" else S.plain(x, 6))
    if pack == "Neoterra":
        for x in (6, 7, 8):
            d.set(x, GY, 6, "white_concrete")                         # stop line of the branch
        d.set(4, GY, 1, GRATE)
        d.set(8, GY, 1, GRATE)
        neo_lamp(d, 6, 0)
        d.sign(6, 4, 1, "south", ["", "< CENTRE", "PARK >", ""], wood="birch", glow=True, color="cyan")
    elif pack == "Hearthwood":
        d.set(6, GY, 3, GRATE)
        hw_lamp(d, 6, 0)
        d.sign(6, 4, 1, "south", ["< Market Sq", "", "Church >", ""], wood="dark_oak")
        for x, z in ((0, 0), (0, 6), (12, 0), (12, 6)):
            hw_beacon(d, x, z)
    else:
        d.set(4, GY, 5, "mossy_cobblestone")
        d.set(8, GY, 5, "mossy_cobblestone")
        cas_lamp(d, 6, 0)
        d.sign(6, 4, 1, "south", ["< Sawmill", "", "Harbor >", ""], wood="spruce")
    return d


# ============================================================================================ intersection
NW, NE, SW, SE = (0, 0), (10, 0), (0, 10), (10, 10)


@design("roadintersection")
def roadintersection(pack, rel, L):
    """Arms N/S (x 3..9) and W/E (z 3..9), 3 long, each a crossing; central box; 3x3 corner plazas."""
    d, S = new(pack, rel, (13, 7, 13), (6, 1, 6))
    for z in range(13):
        for x in range(13):
            in_ns = 3 <= x <= 9
            in_we = 3 <= z <= 9
            if not in_ns and not in_we:
                continue                                                # plazas: drawn per pack below
            if (x, z) in ((3, 3), (9, 3), (3, 9), (9, 9)):
                sidewalk(d, S, x, z, joint=True)
            elif in_ns and not in_we:                                   # north / south arm
                if x in (3, 9) and z in (1, 11):
                    tactile(d, S, x, z)
                elif x in (3, 9):
                    sidewalk(d, S, x, z)
                else:
                    crossing(d, S, x, z, x % 2 == 0, "x", mid=z in (1, 11), a=x - 3, t=z)
            elif in_we and not in_ns:                                   # west / east arm
                if z in (3, 9) and x in (1, 11):
                    tactile(d, S, x, z, axis="x")
                elif z in (3, 9):
                    sidewalk(d, S, x, z, axis="x")
                else:
                    crossing(d, S, x, z, z % 2 == 0, "z", mid=x in (1, 11), a=z - 3, t=x)
            else:
                d.set(x, GY, z, S.plain(x, z))
    PLAZA[pack](d, S)
    return d


def plaza_floor(d, S, x0, z0, cells=None):
    for dz in range(3):
        for dx in range(3):
            if cells is None or (dx, dz) in cells:
                sidewalk(d, S, x0 + dx, z0 + dz, joint=(dx + dz) % 2 == 0)


def neo_plazas(d, S):
    # box junction drains at the four mouths
    for x, z in ((4, 4), (8, 4), (4, 8), (8, 8)):
        d.set(x, GY, z, GRATE)
    # NW / SE: birch in a tree pit, column light on the inner corner of the plaza
    for (x0, z0), (tx, tz), (lx, lz) in ((NW, (1, 1), (2, 2)), (SE, (11, 11), (10, 10))):
        plaza_floor(d, S, x0, z0)
        d.set(tx, GY, tz, "grass_block[snowy=false]")
        d.set(tx, CURB, tz, AIR)
        birch_tree(d, tx, tz, CURB)
        neo_lamp(d, lx, lz)
    # NE / SW: moss planter (2x2) with azaleas, a bench facing the junction, a light
    plaza_floor(d, S, *NE)
    for x, z in ((11, 0), (12, 0), (11, 1), (12, 1)):
        d.set(x, CURB, z, "moss_block")
    d.set(12, 3, 0, "flowering_azalea")
    d.set(11, 3, 1, "azalea")
    d.set(12, 3, 1, "moss_carpet")
    d.set(11, 3, 0, "moss_carpet")
    d.set(12, CURB, 2, stairs("polished_andesite_stairs", "east"))      # bench, looks west at the crossing
    neo_lamp(d, 10, 2)
    plaza_floor(d, S, *SW)
    for x, z in ((0, 11), (1, 11), (0, 12), (1, 12)):
        d.set(x, CURB, z, "moss_block")
    d.set(0, 3, 12, "flowering_azalea")
    d.set(1, 3, 11, "azalea")
    d.set(0, 3, 11, "moss_carpet")
    d.set(1, 3, 12, "moss_carpet")
    d.set(0, CURB, 10, stairs("polished_andesite_stairs", "west"))
    neo_lamp(d, 2, 10)
    d.sign(2, 4, 9, "north", ["", "MAIN ST", "", ""], wood="birch", glow=True, color="cyan")


def hw_plazas(d, S):
    d.set(6, GY, 6, GRATE)
    hedge = leaves("oak")
    # every plaza: a box hedge along its two outer edges, Belisha beacons at the kerbs of the two crossings
    specs = {
        NW: dict(hedge=((0, 0), (1, 0), (2, 0), (0, 1), (0, 2)), beacons=((2, 1), (1, 2)), mid=(1, 1)),
        NE: dict(hedge=((10, 0), (11, 0), (12, 0), (12, 1), (12, 2)), beacons=((10, 1), (11, 2)), mid=(11, 1)),
        SW: dict(hedge=((0, 10), (0, 11), (0, 12), (1, 12), (2, 12)), beacons=((1, 10), (2, 11)), mid=(1, 11)),
        SE: dict(hedge=((12, 10), (12, 11), (12, 12), (11, 12), (10, 12)), beacons=((11, 10), (10, 11)), mid=(11, 11)),
    }
    for (x0, z0), sp in specs.items():
        plaza_floor(d, S, x0, z0, cells={(x - x0, z - z0) for x, z in sp["beacons"]} | {(2 if x0 == 0 else 0,
                                                                                         2 if z0 == 0 else 0)})
        for x, z in sp["hedge"]:
            d.set(x, GY, z, "grass_block[snowy=false]")
            d.set(x, CURB, z, hedge)
        for x, z in sp["beacons"]:
            hw_beacon(d, x, z)
        mx, mz = sp["mid"]
        d.set(mx, GY, mz, "grass_block[snowy=false]")
    # inner plaza corners: plain brick paving (pedestrian corner); mids: lamp / flowers / finger post
    hw_lamp(d, 1, 1, y=CURB)
    hw_lamp(d, 11, 11, y=CURB)
    d.set(1, CURB, 11, "rose_bush[half=lower]")
    d.set(1, 3, 11, "rose_bush[half=upper]")
    for k in range(5):                                                 # finger post, arms above the beacons
        d.set(11, CURB + k, 1, "dark_oak_fence")
    d.sign(11, 6, 2, "south", ["Village Green", "v", "", ""], wood="dark_oak")
    d.sign(10, 6, 1, "west", ["< Mill Lane", "", "", ""], wood="dark_oak")


def cas_plazas(d, S):
    # NW: rail fence corner and a fir
    for (x0, z0) in (NW, NE, SW, SE):
        for dz in range(3):
            for dx in range(3):
                d.set(x0 + dx, GY, z0 + dz, "grass_block[snowy=false]")
    # boardwalk returns on the inner corner cells of every plaza
    for x, z in ((2, 2), (10, 2), (2, 10), (10, 10)):
        sidewalk(d, S, x, z, joint=True)
    # NW: rail fence + fir
    for x, z in ((0, 0), (1, 0), (2, 0), (0, 1), (0, 2)):
        d.set(x, CURB, z, "spruce_fence")
    d.set(1, GY, 1, "podzol[snowy=false]")
    fir(d, 1, 1, CURB)
    d.set(2, CURB, 1, "fern")
    # NE: signpost, barrels and hay by the corner
    for x, z in ((12, 0), (12, 1), (12, 2), (11, 0), (10, 0)):
        d.set(x, CURB, z, "spruce_fence")
    for k in range(3):
        d.set(11, CURB + k, 1, log("spruce_log"))
    d.set(11, 5, 1, LANTERN)
    d.sign(11, 3, 2, "south", ["Trailhead", "v", "", ""], wood="spruce")
    d.sign(10, 3, 1, "west", ["< Lumber Mill", "", "", ""], wood="spruce")
    d.set(11, CURB, 2, "barrel[facing=up,open=false]")
    d.set(10, CURB, 1, "hay_block[axis=x]")
    # SW: boulder with ferns, lamp
    for x, z in ((0, 10), (0, 11), (0, 12), (1, 12), (2, 12)):
        d.set(x, CURB, z, "spruce_fence")
    d.set(1, CURB, 11, "mossy_cobblestone")
    d.set(1, 3, 11, slab("cobblestone_slab"))
    d.set(2, CURB, 11, "fern")
    d.set(1, CURB, 10, "large_fern[half=lower]")
    d.set(1, 3, 10, "large_fern[half=upper]")
    # SE: fir + lamp post on the inner corner
    for x, z in ((12, 10), (12, 11), (12, 12), (11, 12), (10, 12)):
        d.set(x, CURB, z, "spruce_fence")
    d.set(11, GY, 11, "podzol[snowy=false]")
    fir(d, 11, 11, CURB)
    d.set(11, CURB, 10, "fern")
    cas_lamp(d, 2, 2)
    cas_lamp(d, 10, 10)
    d.set(2, GY, 2, log("stripped_spruce_log", "z"))
    d.set(10, GY, 10, log("stripped_spruce_log", "z"))


PLAZA = {"Neoterra": neo_plazas, "Hearthwood": hw_plazas, "Cascadia": cas_plazas}


# ============================================================================================ avenue
@design("avenue")
def avenue(pack, rel, L):
    """Boulevard along z: sidewalk 0 | carriageway 1-4 | median 5-7 | carriageway 8-11 | sidewalk 12."""
    d, S = new(pack, rel, (13, 7, 16), (6, 1, 8))
    for z in range(16):
        sidewalk(d, S, 0, z, joint=z % 4 == 0)
        sidewalk(d, S, 12, z, joint=z % 4 == 0)
    if pack == "Neoterra":
        for z in range(16):
            for x in (1, 11):
                d.set(x, GY, z, "green_terracotta")                   # cycle lanes
            for x in (2, 3, 4, 8, 9, 10):
                d.set(x, GY, z, "gray_concrete")
            for x in (5, 7):
                d.set(x, GY, z, "smooth_stone")
                d.set(x, CURB, z, slab("smooth_stone_slab"))
            d.set(6, GY, z, "grass_block[snowy=false]")
        for x, z in ((1, 6), (1, 7), (11, 14), (11, 15)):
            d.set(x, GY, z, "white_concrete")                         # cycle-lane symbols
        for x, z in ((4, 3), (8, 11)):
            d.set(x, GY, z, GRATE)
        for z in (3, 11):
            d.set(6, CURB, z, AIR)
            birch_tree(d, 6, z, CURB)
        for z in (7, 15):
            d.set(6, CURB, z, "polished_andesite")
            for k in (3, 4, 5):
                d.set(6, k, z, wall("andesite_wall"))
            d.set(5, 6, z, "sea_lantern")
            d.set(6, 6, z, "smooth_stone")
            d.set(7, 6, z, "sea_lantern")
        for z, p in ((1, "azalea"), (5, "flowering_azalea"), (9, "azalea"), (13, "flowering_azalea")):
            d.set(6, CURB, z, p)
    elif pack == "Hearthwood":
        for z in range(16):
            for x in (1, 2, 3, 4, 8, 9, 10, 11):
                d.set(x, GY, z, S.sett(x, z))
            if z in (0, 15):                                           # paved crossing points of the green
                for x in (5, 6, 7):
                    sidewalk(d, S, x, z, joint=True)
            else:
                for x in (5, 6, 7):
                    d.set(x, GY, z, "grass_block[snowy=false]")
                d.set(5, CURB, z, leaves("oak"))
                d.set(7, CURB, z, leaves("oak"))
        for x, z in ((1, 4), (4, 12), (8, 4), (11, 12)):
            d.set(x, GY, z, GRATE)
        for z in (3, 11):
            oak_tree(d, 6, z, CURB)
        for z, f in ((1, "poppy"), (5, "cornflower"), (9, "oxeye_daisy"), (13, "poppy")):
            d.set(6, CURB, z, f)
        d.set(6, CURB, 7, "stone_bricks")
        hw_lamp(d, 6, 7, y=3)
        hw_lamp(d, 0, 11)
        hw_lamp(d, 12, 3)
    else:
        lanes = {1: "gravel", 2: "dirt_path", 3: "coarse_dirt", 4: "dirt_path",
                 8: "dirt_path", 9: "coarse_dirt", 10: "dirt_path", 11: "gravel"}
        for z in range(16):
            for x, b in lanes.items():
                d.set(x, GY, z, b)
            for x in (5, 7):
                d.set(x, GY, z, "mossy_cobblestone" if z % 5 == 2 else "cobblestone")
                d.set(x, CURB, z, slab("cobblestone_slab"))
            d.set(6, GY, z, "podzol[snowy=false]")
        for x, z in ((1, 9), (11, 1)):
            d.set(x, GY, z, "mossy_cobblestone")
        for z in (3, 11):
            fir(d, 6, z, CURB)
        for z in (7, 15):
            for k in range(4):
                d.set(6, CURB + k, z, log("spruce_log"))
            d.set(6, 6, z, "spruce_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]")
            for x in (5, 7):
                d.set(x, 5, z, "spruce_fence")
                d.set(x, 4, z, HANGING)
        for z, p in ((0, "fern"), (6, "fern"), (9, "sweet_berry_bush[age=1]"), (13, "fern")):
            d.set(6, CURB, z, p)
    return d


# ============================================================================================ stairs
@design("roadstairs")
def roadstairs(pack, rel, L):
    """Street stair climbing south: z0 street landing (y1), steps z1-2, mid landing z3-4, steps z5-6, top
    landing z7 (surface y5 = RISE above). Cheek walls with balustrades on x0 / x6; sidewalks at both ends."""
    d, S = new(pack, rel, (7, 9, 8), (3, 1, 0))
    if pack == "Neoterra":
        fill, cheek, step, land = "light_gray_concrete", "light_gray_concrete", "polished_diorite_stairs", \
            "polished_diorite"
    elif pack == "Hearthwood":
        fill, cheek, step, land = "stone_bricks", "bricks", "stone_brick_stairs", "stone_bricks"
    else:
        fill, cheek, step, land = "cobblestone", "cobblestone", "spruce_stairs", "spruce_planks"
    for z in range(8):
        ys = STAIR_Y[z]
        for x in range(7):
            for y in range(GY, ys):
                d.set(x, y, z, fill if x in range(1, 6) else cheek)
        for x in (0, 6):
            if z in (0, 7):
                sidewalk(d, S, x, z, joint=True, y=ys)
            else:
                c = cheek
                if pack == "Cascadia" and (x + z) % 3 == 0:
                    c = "mossy_cobblestone"
                d.set(x, ys, z, c)
        for x in range(1, 6):
            if z in (0, 7):
                d.set(x, ys, z, S.carr(x, z))
            elif z in (1, 2, 5, 6):
                st = step
                if pack == "Cascadia" and x in (1, 5):
                    st = "cobblestone_stairs"                         # river-rock ends, timber treads
                d.set(x, ys, z, stairs(st, "south"))
            else:
                d.set(x, ys, z, land)
    # balustrades and newels
    for z in range(1, 7):
        ys = STAIR_Y[z]
        for x in (0, 6):
            if pack == "Neoterra":
                d.set(x, ys + 1, z, "glass_pane")
            elif pack == "Hearthwood":
                d.set(x, ys + 1, z, wall("stone_brick_wall"))
            else:
                d.set(x, ys + 1, z, "spruce_fence")
    if pack == "Neoterra":
        for x in (0, 6):
            d.set(x, 3, 1, "polished_andesite")                       # lit newels at the foot
            d.set(x, 4, 1, "sea_lantern")
            d.set(x, 5, 1, "daylight_detector[inverted=false,power=0]")
            d.set(x, 6, 6, "polished_andesite")                       # plain newels at the head
            d.set(x, 7, 6, slab("smooth_stone_slab"))
        d.set(0, 3, 4, "sea_lantern")                                  # landing glow strips in the cheeks
        d.set(6, 3, 3, "sea_lantern")
        d.set(3, 1, 0, "white_concrete")
        d.set(5, 1, 0, GRATE)
        d.set(1, 5, 7, GRATE)
    elif pack == "Hearthwood":
        for x in (0, 6):
            for z in (1, 6):
                y = STAIR_Y[z] + 1
                d.set(x, y, z, "stone_bricks")
                d.set(x, y + 1, z, LANTERN)
        d.set(0, 5, 3, "potted_red_tulip")
        d.set(6, 5, 4, "potted_red_tulip")
        d.set(0, 5, 4, "potted_azure_bluet")
        d.set(6, 5, 3, "potted_azure_bluet")
        d.set(3, 1, 0, GRATE)
    else:
        for x in (0, 6):
            for z in (1, 6):
                y = STAIR_Y[z] + 1
                d.set(x, y, z, log("spruce_log"))
                if z == 6:
                    d.set(x, y + 1, z, log("spruce_log"))
                    d.set(x, y + 2, z, LANTERN)
                else:
                    d.set(x, y + 1, z, LANTERN)
        d.set(0, 4, 3, "potted_fern")
        d.set(6, 4, 4, "potted_fern")
    return d
