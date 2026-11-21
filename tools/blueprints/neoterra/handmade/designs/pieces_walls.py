"""
Town walls – hand-designed wall family for the three style packs.

  Hearthwood  English town rampart: stone-brick plinth, brick curtain wall with a stone string course, a 2-wide
              stone walkway behind a crenellated parapet (merlons with slab caps), dark-oak rail with lanterns on
              the town side, stone pilasters. Gatehouse with two flanking towers, pointed stone arch, raised
              portcullis, keystones and a welcome sign; corner turret on the outside corner; brick stair with stone
              balustrade; watchtower that grows from a crenellated bastion (L1) to a two-storey keep (L2) to a
              belfry tower with a steep slate spire (L3).
  Cascadia    Log palisade: river-rock footing, upright spruce logs with staggered tips and loopholes, a plank
              fighting platform on posts with knee braces behind it, rail fence with lanterns. Gate between two
              log blockhouses with a big timber lintel and hanging signs; covered lookout on the outside corner;
              timber stair on log stringers; watchtower = fire lookout: blockhouse (L1), second blockhouse storey
              with lookout deck (L2), tall log trestle with a glazed cab and catwalk (L3).
  Neoterra    Modern barrier: andesite plinth, white concrete wall with a cyan band, glass blast screen with
              concrete fins and a slab cap, a 4-wide walkway lit by a sea-lantern strip, glass railing with end-rod
              bollards and planters on the town side. Gate = portal with glass guard booths and glowing signs;
              corner light mast; concrete stair with glass balustrade; watchtower grows from a glazed podium (L1)
              to a concrete core with a deck (L2) to an observation cab with an antenna mast (L3).

Connection constants (all pieces of a pack share them):
  the wall band runs along x with its OUTSIDE face at z = 0 (north), DEPTH rows deep; walkway floor at WALK_Y
  (stand on WALK_Y + 1), walkway rows k = 1 .. DEPTH-2, inner rail row k = DEPTH-1.
  Outside corner = band in the north rows + east columns (turns south, outside east).
  Inside corner  = band in the south rows + east columns, outside faces on the inner sides of the L (turns north,
  outside west). Gate/stairs/watchtower carry the same band (watchtower: band starts at z = TOWER_BAND_Z).
Sizes/anchors are unchanged from the generated set.
"""
import json

from nbtlib import tag as T

import hm
from hm import Design, design, AIR, KEEP

DEPTH = {"Hearthwood": 4, "Cascadia": 4, "Neoterra": 6}
WALK_Y = {"Hearthwood": 7, "Cascadia": 6, "Neoterra": 6}
TOWER_BAND_Z = {"Hearthwood": 3, "Cascadia": 3, "Neoterra": 3}
ANCHOR_Z = {"Hearthwood": 1, "Cascadia": 1, "Neoterra": 2}


def stairs(b, facing, half="bottom", shape="straight"):
    return f"{b}[facing={facing},half={half},shape={shape},waterlogged=false]"


def slab(b, t="bottom"):
    return f"{b}[type={t},waterlogged=false]"


def log(b, ax):
    return f"{b}[axis={ax}]"


def lantern(hanging=False):
    return f"lantern[hanging={'true' if hanging else 'false'},waterlogged=false]"


def ladder(facing):
    return f"ladder[facing={facing},waterlogged=false]"


def end_rod(f="up"):
    return f"end_rod[facing={f}]"


# --------------------------------------------------------------------------------------------- cross-sections
def section(pack, k, ax):
    """Blocks of the wall column at depth k (0 = outside face) for a run along axis `ax` ('x' or 'z')."""
    if pack == "Hearthwood":
        if k == 0:
            s = {1: "stone_bricks", 2: "stone_bricks", 7: "stone_bricks", 8: "bricks"}
            s.update({y: "bricks" for y in range(3, 7)})
        elif k in (1, 2):
            s = {1: "stone_bricks", 7: "stone_bricks"}
            s.update({y: "bricks" for y in range(2, 7)})
        else:
            s = {1: "stone_bricks", 2: "stone_bricks", 7: "stone_bricks", 8: "dark_oak_fence"}
            s.update({y: "bricks" for y in range(3, 7)})
        return s
    if pack == "Cascadia":
        if k == 0:
            s = {1: "cobblestone", 2: "cobblestone"}
            s.update({y: log("spruce_log", "y") for y in range(3, 10)})
        elif k == 1:
            s = {1: "coarse_dirt", 4: log("stripped_spruce_log", ax), 6: "spruce_planks"}
        elif k == 2:
            s = {1: "coarse_dirt", 6: "spruce_planks"}
        else:
            s = {1: "coarse_dirt", 6: log("stripped_spruce_log", ax), 7: "spruce_fence"}
        return s
    # Neoterra
    if k == 0:
        s = {1: "polished_andesite", 2: "polished_andesite", 3: "white_concrete", 4: "white_concrete",
             5: "white_concrete", 6: "cyan_terracotta", 7: "white_concrete", 8: "light_gray_stained_glass_pane",
             9: slab("smooth_stone_slab")}
    elif k == 5:
        s = {1: "polished_andesite", 2: "polished_andesite", 3: "white_concrete", 4: "white_concrete",
             5: "white_concrete", 6: "white_concrete", 7: "glass_pane"}
    else:
        deck = {1: "sea_lantern", 2: "smooth_stone", 3: "smooth_stone", 4: "polished_andesite"}[k]
        s = {1: "polished_andesite", 6: deck}
        s.update({y: "light_gray_concrete" for y in range(2, 6)})
    return s


def column(d, x, z, k, ax):
    for y, b in section(d.pack, k, ax).items():
        d.set(x, y, z, b)


def run_x(d, x1, x2, z0, sign=1):
    """Band along x: outer face row z0, depth rows toward +z (sign=1) or -z."""
    for x in range(x1, x2 + 1):
        for k in range(DEPTH[d.pack]):
            column(d, x, z0 + sign * k, k, "x")


def run_z(d, z1, z2, x0, sign):
    """Band along z: outer face column x0, depth columns toward x0 + sign*k."""
    for z in range(z1, z2 + 1):
        for k in range(DEPTH[d.pack]):
            column(d, x0 + sign * k, z, k, "z")


def keep_ground(d, x1, z1, x2, z2):
    """Cells of the box outside the wall: leave the terrain as it is."""
    d.fill(x1, 0, z1, x2, d.gy, z2, KEEP)


# --------------------------------------------------------------------------------------------- single features
def h_merlon(d, x, z):
    d.set(x, 9, z, "bricks")
    d.set(x, 10, z, slab("stone_brick_slab"))


def c_tip(d, x, z):
    d.set(x, 10, z, log("spruce_log", "y"))


def c_post(d, x, z, braces):
    """Platform post on the rail row; braces = list of (x, z, facing) knee braces next to it."""
    for y in range(2, 6):
        d.set(x, y, z, log("spruce_log", "y"))
    for bx, bz, f in braces:
        d.set(bx, 5, bz, stairs("spruce_stairs", f, "top"))


def n_fin(d, x, z):
    d.set(x, 8, z, "light_gray_concrete")
    d.set(x, 9, z, "light_gray_concrete")


def n_bollard(d, x, z):
    d.set(x, 7, z, "white_concrete")
    d.set(x, 8, z, end_rod())


def n_planter(d, x, z):
    d.set(x, 7, z, "moss_block")
    d.set(x, 8, z, "flowering_azalea")


def sign_te(lines, glow=False, color="black", hanging=False):
    msgs = [json.dumps({"text": t}) for t in (list(lines) + ["", "", "", ""])[:4]]
    side = T.Compound({"messages": T.List[T.String]([T.String(m) for m in msgs]), "color": T.String(color),
                       "has_glowing_text": T.Byte(1 if glow else 0)})
    return T.Compound({"id": T.String("minecraft:hanging_sign" if hanging else "minecraft:sign"),
                       "front_text": side, "back_text": T.Compound(dict(side)), "is_waxed": T.Byte(1)})


# ============================================================================================ straight
@design("wallstraight")
def wallstraight(pack, rel, L):
    if pack == "Neoterra":
        d = Design(pack, rel, (8, 10, 6))
        run_x(d, 0, 7, 0)
        n_fin(d, 0, 0)
        n_fin(d, 4, 0)
        for y in range(3, 6):                                   # expansion joint on the outer face
            d.set(0, y, 0, "light_gray_concrete")
        n_bollard(d, 0, 5)
        n_planter(d, 3, 5)
        n_planter(d, 4, 5)
        d.anchor(4, 1, 2)
        return d
    d = Design(pack, rel, (8, 11, 4))
    run_x(d, 0, 7, 0)
    if pack == "Hearthwood":
        for x in (1, 2, 5, 6):
            h_merlon(d, x, 0)
        for y in range(3, 7):                                   # stone pilaster on the town side
            d.set(0, y, 3, "stone_bricks")
        d.set(3, 9, 3, lantern())
        d.set(2, 2, 0, "mossy_stone_bricks")
        d.set(6, 1, 0, "mossy_stone_bricks")
        d.set(5, 2, 3, "mossy_stone_bricks")
    else:
        for x in (0, 2, 3, 6):
            c_tip(d, x, 0)
        for x in (1, 5):                                        # loopholes at eye height
            d.set(x, 8, 0, AIR)
        c_post(d, 0, 3, [(1, 3, "west")])
        c_post(d, 4, 3, [(3, 3, "east"), (5, 3, "west")])
        d.set(7, 5, 3, stairs("spruce_stairs", "east", "top"))  # brace toward the next piece's post
        d.set(0, 8, 3, lantern())
        d.set(2, 2, 0, "mossy_cobblestone")
        d.set(5, 1, 0, "mossy_cobblestone")
        d.set(6, 2, 0, "mossy_cobblestone")
    d.anchor(4, 1, 1)
    return d


# ============================================================================================ corners
def corner_square(d, x1, z1, x2, z2, kfun):
    """The square where both runs meet: every cell gets the section of its depth k (kfun(x, z)), so parapet,
    walkway and rail turn the corner as L-shaped courses."""
    for z in range(z1, z2 + 1):
        for x in range(x1, x2 + 1):
            k = kfun(x, z)
            column(d, x, z, k, "x" if k == 0 and z == z1 else "z")


@design("walloutsidecorner")
def walloutsidecorner(pack, rel, L):
    """Wall comes in from the west (outside north) and turns south (outside east)."""
    D = DEPTH[pack]
    sy = 12 if pack == "Neoterra" else 13
    d = Design(pack, rel, (8, sy, 8))
    e = 8 - D                                                    # first column of the south arm
    keep_ground(d, 0, D, e - 1, 7)
    run_x(d, 0, e - 1, 0)                                        # west arm
    run_z(d, D, 7, 7, -1)                                        # south arm
    corner_square(d, e, 0, 7, D - 1, lambda x, z: min(z, 7 - x))
    if pack == "Hearthwood":
        h_merlon(d, 1, 0)
        h_merlon(d, 2, 0)
        h_merlon(d, 7, 5)
        h_merlon(d, 7, 6)
        d.set(1, 9, 3, lantern())
        d.set(4, 9, 6, lantern())
        # corner turret over the walkway bend (x4..7, z0..3)
        for y in range(8, 11):
            for x in range(4, 8):
                d.set(x, y, 0, "bricks")
                d.set(x, y, 3, "bricks")
            for z in range(0, 4):
                d.set(4, y, z, "bricks")
                d.set(7, y, z, "bricks")
        for y in (8, 9):                                         # walkway doorways (west and south)
            for z in (1, 2):
                d.set(4, y, z, AIR)
            for x in (5, 6):
                d.set(x, y, 3, AIR)
        for y in range(2, 11):                                   # stone quoin on the outer corner
            d.set(7, y, 0, "stone_bricks")
        d.set(4, 10, 3, "stone_bricks")
        d.set(5, 9, 0, "iron_bars")                              # arrow slits
        d.set(7, 9, 2, "iron_bars")
        d.fill(4, 11, 0, 7, 11, 3, "stone_bricks")               # roof deck
        for y in range(8, 12):                                   # ladder to the turret roof
            d.set(6, y, 1, ladder("west"))
        d.set(5, 10, 2, lantern(True))
        for x, z in ((4, 0), (7, 0), (4, 3), (7, 3)):            # corner merlons
            d.set(x, 12, z, "bricks")
        for x, z in ((5, 0), (6, 0), (4, 1), (4, 2), (7, 1), (7, 2), (5, 3), (6, 3)):
            d.set(x, 12, z, slab("stone_brick_slab"))
        d.set(6, 2, 0, "mossy_stone_bricks")
        d.set(7, 2, 5, "mossy_stone_bricks")
        d.anchor(4, 1, 4)
    elif pack == "Cascadia":
        for x, z in ((0, 0), (2, 0), (3, 0), (7, 4), (7, 6)):
            c_tip(d, x, z)
        for x, z in ((1, 0), (7, 5)):
            d.set(x, 8, z, AIR)
        c_post(d, 0, 3, [(1, 3, "west")])
        c_post(d, 4, 7, [(4, 6, "south")])
        # covered lookout on the corner: tall post at the inner corner, palisade logs carried up as the other
        # three posts, a small hipped shingle roof over the walkway bend
        for y in range(2, 11):
            d.set(4, y, 3, log("spruce_log", "y"))
        for x, z in ((4, 0), (7, 0), (7, 3)):
            d.set(x, 10, z, log("spruce_log", "y"))
        for x, z in ((5, 0), (6, 0), (7, 1), (7, 2)):           # open lookout slots under the roof
            d.set(x, 10, z, AIR)
        d.set(3, 5, 3, stairs("spruce_stairs", "east", "top"))
        d.set(4, 5, 4, stairs("spruce_stairs", "north", "top"))
        d.hip(4, 0, 7, 3, 11, stairs="spruce_stairs", cap="spruce_slab", overhang=0)
        d.set(5, 11, 2, lantern(True))
        d.set(7, 2, 1, "mossy_cobblestone")
        d.set(3, 2, 0, "mossy_cobblestone")
        d.anchor(4, 1, 4)
    else:
        n_fin(d, 0, 0)
        n_fin(d, 4, 0)
        n_fin(d, 7, 4)
        for y in range(8, 11):                                   # light mast on the corner
            d.set(7, y, 0, "light_gray_concrete")
        d.set(7, 11, 0, "sea_lantern")
        for y in range(3, 6):
            d.set(7, y, 0, "light_gray_concrete")
        n_bollard(d, 0, 5)
        n_planter(d, 2, 5)
        n_bollard(d, 2, 7)
        d.anchor(4, 1, 4)
    return d


@design("wallinsidecorner")
def wallinsidecorner(pack, rel, L):
    """Wall comes in from the west (outside north) and turns north (outside west): a re-entrant corner."""
    D = DEPTH[pack]
    sy = 12 if pack == "Neoterra" else 13
    d = Design(pack, rel, (8, sy, 8))
    o = 8 - D                                                    # outer face row / column of the L
    keep_ground(d, 0, 0, o - 1, o - 1)
    run_x(d, 0, o - 1, o)                                        # west arm (outer row z = o)
    run_z(d, 0, o - 1, o, 1)                                     # north arm (outer column x = o)
    corner_square(d, o, o, 7, 7, lambda x, z: max(z - o, x - o))
    if pack == "Hearthwood":
        h_merlon(d, 1, 4)
        h_merlon(d, 2, 4)
        h_merlon(d, 4, 4)                                        # corner merlon
        h_merlon(d, 4, 1)
        h_merlon(d, 4, 2)
        for y in range(2, 9):                                    # stone quoin in the angle
            d.set(4, y, 4, "stone_bricks")
        d.set(7, 9, 7, lantern())
        d.set(3, 2, 4, "mossy_stone_bricks")
        d.anchor(4, 1, 4)
    elif pack == "Cascadia":
        for x, z in ((0, 4), (2, 4), (4, 4), (4, 2), (4, 0)):
            c_tip(d, x, z)
        for x, z in ((1, 4), (4, 1)):
            d.set(x, 8, z, AIR)
        c_post(d, 7, 7, [(6, 7, "east"), (7, 6, "south")])
        c_post(d, 3, 7, [(2, 7, "east")])
        c_post(d, 7, 3, [(7, 2, "south")])
        d.set(7, 8, 7, lantern())
        d.set(2, 2, 4, "mossy_cobblestone")
        d.anchor(4, 1, 4)
    else:
        n_fin(d, 0, 2)
        n_fin(d, 2, 2)
        n_fin(d, 2, 0)
        n_planter(d, 7, 7)
        n_planter(d, 6, 7)
        n_planter(d, 7, 6)
        n_bollard(d, 3, 7)
        n_bollard(d, 7, 3)
        d.anchor(4, 1, 4)
    return d


# ============================================================================================ stairs
@design("wallstairs")
def wallstairs(pack, rel, L):
    """A straight wall with a stair flight on the town side, rising straight at the walkway (x3..4); the rail
    has a gap where the flight lands."""
    D, W = DEPTH[pack], WALK_Y[pack]
    sz = 13 if pack == "Neoterra" else 12
    d = Design(pack, rel, (8, 10 if pack == "Neoterra" else 11, sz))
    run_x(d, 0, 7, 0)
    keep_ground(d, 0, D, 7, sz - 1)
    n = W - 2                                                    # steps y = 2 .. W-1
    zl = D + 1                                                   # far landing row (landing rows D .. D+1)
    steps = [(zl + n - i, 2 + i) for i in range(n)]              # (z, y) from the foot up
    foot = zl + n + 1                                            # ground row in front of the first step
    for x in (3, 4):                                             # rail gap at the landing
        d.set(x, W + 1, D - 1, AIR)
    if pack == "Hearthwood":
        for z in range(D, foot + 1):
            for x in range(2, 6):
                d.set(x, 1, z, "stone_bricks")
        for z in (D, D + 1):                                     # landing on a solid brick pier
            for x in range(2, 6):
                for y in range(2, W):
                    d.set(x, y, z, "bricks")
                d.set(x, W, z, "stone_bricks")
        for z, y in steps:
            for x in (3, 4):
                for yy in range(2, y):
                    d.set(x, yy, z, "bricks")
                d.set(x, y, z, stairs("stone_brick_stairs", "north"))
            for x in (2, 5):                                     # cheek walls with a stone balustrade
                for yy in range(2, y + 1):
                    d.set(x, yy, z, "stone_bricks" if yy == y else "bricks")
        for x in (2, 5):
            for z, y in steps + [(D + 1, W), (D, W)]:
                d.set(x, y + 1, z, f"stone_brick_wall[east=none,north=low,south=low,up=false,waterlogged=false,"
                                   f"west=none]")
            d.set(x, W + 1, D, "stone_brick_wall[east=none,north=none,south=low,up=true,waterlogged=false,"
                               "west=none]")
            z0, y0 = steps[0]
            d.set(x, y0 + 1, z0, "stone_brick_wall[east=none,north=low,south=none,up=true,waterlogged=false,"
                                 "west=none]")
            d.set(x, y0 + 2, z0, lantern())                      # lanterns on the newel posts at the foot
        d.set(2, 2, steps[1][0], "mossy_stone_bricks")
        for x in (1, 2, 5, 6):
            h_merlon(d, x, 0)
        d.anchor(4, 1, 1)
    elif pack == "Cascadia":
        for z in range(D, foot + 1):
            for x in range(3, 5):
                d.set(x, 1, z, "gravel")
        for z in (D, D + 1):                                     # landing deck on posts
            for x in range(2, 6):
                d.set(x, W, z, "spruce_planks")
        for x in (2, 5):
            for y in range(2, W):
                d.set(x, y, D + 1, log("spruce_log", "y"))
            d.set(x, 1, D + 1, "cobblestone")
            for z in (D, D + 1):
                d.set(x, W + 1, z, "spruce_fence")
        for z, y in steps:
            for x in (3, 4):
                d.set(x, y, z, stairs("spruce_stairs", "north"))
            for x in (2, 5):                                     # log stringers with a rail fence on top
                d.set(x, y, z, log("stripped_spruce_log", "z"))
                d.set(x, y + 1, z, "spruce_fence")
        z0, y0 = steps[0]
        for x in (2, 5):                                         # newel posts with lanterns at the foot
            d.set(x, 1, z0, "cobblestone")
            d.set(x, y0, z0, log("spruce_log", "y"))
            d.set(x, y0 + 1, z0, log("spruce_log", "y"))
            d.set(x, y0 + 2, z0, lantern())
        for x in (0, 2, 3, 6):
            c_tip(d, x, 0)
        for x in (1, 5):
            d.set(x, 8, 0, AIR)
        c_post(d, 0, 3, [(1, 3, "west")])
        d.set(7, 5, 3, stairs("spruce_stairs", "east", "top"))
        d.set(1, 2, 0, "mossy_cobblestone")
        d.anchor(4, 1, 1)
    else:
        for z in range(D, foot + 1):
            for x in range(2, 6):
                d.set(x, 1, z, "polished_andesite")
        for z in (D, D + 1):
            for x in range(2, 6):
                for y in range(2, W):
                    d.set(x, y, z, "white_concrete")
                d.set(x, W, z, "smooth_stone")
        for z, y in steps:
            for x in (3, 4):
                for yy in range(2, y):
                    d.set(x, yy, z, "light_gray_concrete")
                d.set(x, y, z, stairs("polished_andesite_stairs", "north"))
            for x in (2, 5):
                for yy in range(2, y + 1):
                    d.set(x, yy, z, "white_concrete")
                d.set(x, y + 1, z, "glass_pane")
        for x in (2, 5):
            for z in (D, D + 1):
                d.set(x, W + 1, z, "glass_pane")
            z0, y0 = steps[0]
            d.set(x, y0 + 1, z0, end_rod())                      # light bollards at the foot
        for x, z in ((1, foot), (6, foot)):                      # planters flanking the foot
            d.set(x, 1, z, "polished_andesite")
            d.set(x, 2, z, "moss_block")
            d.set(x, 3, z, "flowering_azalea")
        n_fin(d, 0, 0)
        n_fin(d, 4, 0)
        for y in range(3, 6):
            d.set(0, y, 0, "light_gray_concrete")
        n_bollard(d, 0, 5)
        n_bollard(d, 7, 5)
        d.anchor(4, 1, 2)
    return d


# ============================================================================================ gate
@design("wallgate")
def wallgate(pack, rel, L):
    D, W = DEPTH[pack], WALK_Y[pack]
    d = Design(pack, rel, (14, 14, D))
    run_x(d, 0, 13, 0)
    if pack == "Hearthwood":
        _gate_hearthwood(d, D, W)
    elif pack == "Cascadia":
        _gate_cascadia(d, D, W)
    else:
        _gate_neoterra(d, D, W)
    d.anchor(7, 1, ANCHOR_Z[pack])
    return d


def _gate_hearthwood(d, D, W):
    # gate passage x5..8, pointed arch, keystones, raised portcullis, lanterns
    for z in range(D):
        for x in range(5, 9):
            d.set(x, 1, z, "stone_bricks")
            for y in range(2, 6):
                d.set(x, y, z, AIR)
        d.set(5, 5, z, stairs("stone_brick_stairs", "west", "top"))
        d.set(8, 5, z, stairs("stone_brick_stairs", "east", "top"))
        for x in (4, 9):                                         # stone jambs
            for y in range(2, 6):
                d.set(x, y, z, "stone_bricks")
        for x in range(4, 10):
            d.set(x, 6, z, "stone_bricks")
    d.set(6, 6, 0, "chiseled_stone_bricks")
    d.set(7, 6, 0, "chiseled_stone_bricks")
    d.set(6, 5, 1, "iron_bars")
    d.set(7, 5, 1, "iron_bars")
    d.set(6, 5, 2, lantern(True))
    d.set(7, 5, 2, lantern(True))
    d.set(6, 6, 3, "dark_oak_wall_sign[facing=south,waterlogged=false]", sign_te(["", "Welcome to"]))
    d.set(7, 6, 3, "dark_oak_wall_sign[facing=south,waterlogged=false]", sign_te(["", "Hearthwood"]))
    for x in (5, 8):                                             # merlons over the gate
        h_merlon(d, x, 0)
    # flanking towers x0..3 and x10..13
    for x0 in (0, 10):
        for y in range(8, 11):
            for i in range(4):
                d.set(x0 + i, y, 0, "bricks")
                d.set(x0 + i, y, D - 1, "bricks")
                d.set(x0, y, i, "bricks")
                d.set(x0 + 3, y, i, "bricks")
            for z in (1, 2):
                d.set(x0 + 1, y, z, AIR)
                d.set(x0 + 2, y, z, AIR)
        for y in (8, 9):                                         # walkway passes through the tower
            for z in (1, 2):
                d.set(x0, y, z, AIR)
                d.set(x0 + 3, y, z, AIR)
        for y in range(2, 11):                                   # stone quoins
            d.set(x0, y, 0, "stone_bricks")
            d.set(x0 + 3, y, 0, "stone_bricks")
        d.fill(x0, 11, 0, x0 + 3, 11, 3, "stone_bricks")
        for x, z in ((0, 0), (3, 0), (0, 3), (3, 3)):
            d.set(x0 + x, 12, z0 := z, "bricks")
            d.set(x0 + x, 13, z, slab("stone_brick_slab"))
        for x, z in ((1, 0), (2, 0), (0, 1), (0, 2), (3, 1), (3, 2), (1, 3), (2, 3)):
            d.set(x0 + x, 12, z, slab("stone_brick_slab"))
        d.set(x0 + 2, 12, 2, "red_banner[rotation=0]")
    for y in range(8, 12):                                       # ladders up to the tower roofs
        d.set(1, y, 1, ladder("south"))
        d.set(12, y, 1, ladder("south"))
    d.set(1, 9, 0, "iron_bars")
    d.set(12, 9, 0, "iron_bars")
    d.set(2, 10, 2, lantern(True))
    d.set(11, 10, 2, lantern(True))
    d.set(2, 2, 0, "mossy_stone_bricks")
    d.set(11, 2, 3, "mossy_stone_bricks")


def _gate_cascadia(d, D, W):
    # gate opening x5..8 through the palisade, big timber lintel, hanging signs
    for z in range(D):
        for x in range(5, 9):
            d.set(x, 1, z, "gravel")
            for y in range(2, 6):
                d.set(x, y, z, AIR)
    for x in range(4, 10):
        d.set(x, 6, 0, log("stripped_spruce_log", "x"))
    for y in range(2, 6):                                        # inner gate posts
        d.set(4, y, 3, log("spruce_log", "y"))
        d.set(9, y, 3, log("spruce_log", "y"))
    d.set(5, 5, 3, stairs("spruce_stairs", "west", "top"))
    d.set(8, 5, 3, stairs("spruce_stairs", "east", "top"))
    d.set(5, 5, 0, stairs("spruce_stairs", "west", "top"))
    d.set(8, 5, 0, stairs("spruce_stairs", "east", "top"))
    d.set(6, 5, 1, "spruce_hanging_sign[attached=false,rotation=0,waterlogged=false]",
          sign_te(["", "CASCADIA"], hanging=True))
    d.set(7, 5, 1, "spruce_hanging_sign[attached=false,rotation=0,waterlogged=false]",
          sign_te(["", "Est. 1886"], hanging=True))
    for x in (5, 7, 8):
        c_tip(d, x, 0)
    d.set(6, 8, 0, AIR)                                          # loophole over the gate
    # log blockhouses x0..3 and x10..13
    for x0 in (0, 10):
        for y in range(2, 11):
            if y == W:
                continue
            for i in range(4):
                for (x, z, ax) in ((x0 + i, 0, "x"), (x0 + i, 3, "x"), (x0, i, "z"), (x0 + 3, i, "z")):
                    corner = x in (x0, x0 + 3) and z in (0, 3)
                    d.set(x, y, z, log("spruce_log", "y") if corner else log("stripped_spruce_log", ax))
            for x in (x0 + 1, x0 + 2):
                for z in (1, 2):
                    d.set(x, y, z, AIR)
        for x in range(x0, x0 + 4):                              # floor of the upper room (= platform level)
            for z in range(4):
                d.set(x, W, z, "spruce_planks")
                d.set(x, 1, z, "cobblestone" if z in (0, 3) or x in (x0, x0 + 3) else "spruce_planks")
        for y in (W + 1, W + 2):                                 # platform runs through the upper room
            for z in (1, 2):
                d.set(x0, y, z, AIR)
                d.set(x0 + 3, y, z, AIR)
        d.set(x0 + 1, W + 2, 0, AIR)                             # loopholes
        d.set(x0 + 2, W + 2, 0, AIR)
        for z in range(4):
            d.set(x0 + (0 if x0 == 0 else 3), 2, z, "cobblestone")
        d.hip(x0, 0, x0 + 3, 3, 11, stairs="spruce_stairs", cap="spruce_slab", overhang=0)
        d.set(x0 + 1, 11, 1, lantern(True))
    # store rooms in the blockhouse bases, door to the town side
    d.door(1, 2, 3, "south", wood="spruce")
    d.door(12, 2, 3, "south", wood="spruce")
    d.item(2, 2, 1, "barrel", "up")
    d.item(11, 2, 1, "barrel", "up")
    d.set(1, 2, 1, "hay_block[axis=y]")
    d.set(12, 2, 1, "hay_block[axis=y]")


def _gate_neoterra(d, D, W):
    # 6-wide portal x4..9 (clear y2..4) under a concrete bridge beam carrying the walkway; road with lane marks
    for z in range(D):
        for x in range(4, 10):
            d.set(x, 1, z, "light_gray_concrete" if x in (4, 9) else "gray_concrete")
            for y in range(2, 5):
                d.set(x, y, z, AIR)
            d.set(x, 5, z, "white_concrete")
    for z in (1, 3, 5):
        d.set(6, 1, z, "white_concrete")
        d.set(7, 1, z, "white_concrete")
    for x in range(4, 10):                                       # light strip in the portal soffit
        if x in (5, 8):
            d.set(x, 5, 2, "sea_lantern")
    for x, txt in ((6, ["", "NEO"]), (7, ["", "TERRA"])):        # glowing name signs on both faces
        d.set(x, 4, 0, "birch_wall_sign[facing=north,waterlogged=false]", sign_te(txt, True, "cyan"))
        d.set(x, 4, D - 1, "birch_wall_sign[facing=south,waterlogged=false]", sign_te(txt, True, "cyan"))
    n_fin(d, 4, 0)
    n_fin(d, 9, 0)
    n_bollard(d, 4, D - 1)
    n_bollard(d, 9, D - 1)
    # guard booths x0..3 / x10..13 (glass toward the portal, door to the town) with a glazed walkway room above
    for x0 in (0, 10):
        inner = x0 + 3 if x0 == 0 else x0                        # face toward the portal
        outer = x0 if x0 == 0 else x0 + 3
        door_x = x0 + 1 if x0 == 0 else x0 + 2
        glass_x = x0 + 2 if x0 == 0 else x0 + 1
        for y in range(2, 6):
            for x in (x0 + 1, x0 + 2):
                for z in range(1, D - 1):
                    d.set(x, y, z, AIR)
            for z in range(1, D - 1):
                d.set(inner, y, z, "light_blue_stained_glass_pane" if y in (3, 4) else "white_concrete")
                d.set(outer, y, z, "white_concrete")
            d.set(glass_x, y, D - 1, "light_blue_stained_glass_pane" if y in (3, 4) else "white_concrete")
            d.set(door_x, y, D - 1, "white_concrete")
        d.door(door_x, 2, D - 1, "south", wood="birch")
        for y in range(2, W + 1):                                # ladder from the booth up to the walkway
            d.set(door_x, y, 1, ladder("south"))
        d.set(glass_x, 2, 1, slab("smooth_stone_slab", "top"))   # desk facing the portal window
        d.chair(glass_x, 2, 2, "south", wood="birch", sit=False)
        d.set(glass_x, 2, 4, "potted_bamboo")
        d.set(glass_x, 5, 3, "sea_lantern")
        # walkway room y W+1 .. W+3: open ends on the walkway rows, glass on the outer and town faces
        for y in range(W + 1, W + 4):
            for x in range(x0, x0 + 4):
                for z in (0, D - 1):
                    post = x in (x0, x0 + 3)
                    low = y == W + 1 and z == 0
                    d.set(x, y, z, "white_concrete" if post or low else "light_gray_stained_glass_pane")
            for z in range(1, D - 1):
                for x in range(x0, x0 + 4):
                    side = x in (x0, x0 + 3)
                    d.set(x, y, z, "light_gray_stained_glass_pane" if side and y == W + 3 else AIR)
        for x in range(x0, x0 + 4):                              # roof with a cyan fascia and corner lights
            for z in range(D):
                edge = x in (x0, x0 + 3) or z in (0, D - 1)
                d.set(x, W + 4, z, "cyan_terracotta" if edge else "white_concrete")
                d.set(x, W + 5, z, "white_concrete")
        for x, z in ((x0, 0), (x0 + 3, 0), (x0, D - 1), (x0 + 3, D - 1)):
            d.set(x, W + 6, z, end_rod())
        d.set(x0 + 1, W + 6, 2, "light_gray_concrete")           # roof plant housing
        d.set(x0 + 2, W + 6, 2, "light_gray_concrete")
