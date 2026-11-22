"""
Transport pieces B – subway, boardwalk and cliff climb for Neoterra, Hearthwood and Cascadia, designed by hand.

SUBWAY (subwaystraight 9x7x8 anchor (4,1,0); subwaycorner 9x7x9 anchor (4,1,0); subwayentrance 9x14x14 anchor
  (4,8,0)).  SIZE CHANGE: the entrance was 7 wide (anchor x 3); it is now 9 wide (anchor x 4) in every pack so its
  tunnel end has exactly the straight's cross-section (a 7 wide entrance left a one-block step in both walls).
  Cross-section, x 0..8 (SUB_ROW "WwetRtewW"): wall | walkway, walkway edge | trench, track, trench | edge, walkway
  | wall.  Floor slab y = 0, walkway (curb) blocks y = 1 so people stand on y = 2 with 4 free blocks up to the
  ceiling slab at y = 6; the track trench is one block lower: rail on the floor at y = 1 (x = 4).
  Straights run along z (0..7) and join every 8; each has an always-on boost (powered rails z = 3, 4, redstone
  block in the floor under z = 3).  Corner: north arm -> east arm around a square chamber; the rail is a real
  curve at (4,1,4); next straight = corner anchor + (5, 0, 4), 3 quarter turns.  Entrance: street level is its
  ground layer y = 8 (= anchor); a 5 wide stair (x 2..6) goes down from z = 1 (tread y 7) to z = 6 (tread y 2)
  onto a cross platform at z = 7 and the tunnel z 7..13; the ceiling steps down with the stair (z 4: y 8, z 5: y 7,
  z >= 6: y 6) so every tread has 3 free blocks above.  The track ends in a buffer at z = 8 (last two rails are
  unpowered powered rails = brake; the button on the buffer sends the cart off).  First straight = entrance
  anchor + (0, -7, 14).  The kiosk over the stair head is the pack's landmark:
  Neoterra   metro portal: glass-walled stair head between light-gray frames, cantilevered white canopy with
             light panels, glowing "METRO" fascia sign and a cyan "M" totem, moss planter; inside white concrete
             tube with a cyan eye-level stripe, light-gray portal frames, yellow platform edges, ceiling lights.
  Hearthwood Edwardian tube kiosk: ox-blood terracotta walls, granite arch with the "UNDERGROUND" board,
             stone-brick cornice, black lamp standards, flower pots; inside a brick vault with brick ribs, white
             tile walls with a red band, stone-brick platforms with smooth-stone coping, hanging lanterns.
  Cascadia   mine-adit portal: river-rock knee walls, spruce log posts, steep A-frame roof, gable sign, lanterns;
             inside a rock tunnel with spruce timber sets (log posts + cap beam) every few blocks, plank lagging
             ceiling, plank walkways, track on spruce ties in gravel, lanterns on the cap beams.

BOARDWALK (boardwalkstraight 5x10x8 anchor (2,2,0); boardwalkcorner 5x5 anchor (2,2,0); pier 9x10x12).
  Cross-section x 0..4: railing | 3 wide walkway | railing; the deck is ONE layer at the anchor level y = 2 (stand
  on y = 3); piles y 0..1 under the railing lines at z = 1 and z = 6 (corner: its four corners) with a cap beam;
  everything else below the deck is 'keep' (water and sand stay).  Straights join every 8; corner north -> east,
  next straight = corner anchor + (3, 0, 2), 3 quarter turns.  Lamps stand on the railing line, alternating sides.
  PIER: controller moved from (4,2,0) to (4,3,0) – the decoration controller is invisible and has no collision,
  so in the deck layer it would be a hole in the walkway; one higher it stands on the deck (facing down) where a
  player walks through it.  The pier's neck (z 0..4, x 2..6) has the boardwalk cross-section; a boardwalk end at
  anchor A continues as a pier at A + (0, 1, 8).  The head (z 5..11, full width) has 4 sit_out seats, lamps and a
  fishing / viewing end.
  Neoterra   mangrove decking between light-gray concrete edge beams, glass balustrade, slim lamp posts with light
             cubes, concrete piles; pier head with a white canopy on concrete fins, viewing scope, moss planters.
  Hearthwood Victorian seaside promenade: oak boards, dark-oak fascia, white-painted (birch) railings between
             dark posts, black lamp standards; pier head with a tiled hip-roof shelter on dark-oak posts,
             benches, life-ring board and a fishing corner (barrel, rod rack).
  Cascadia   log dock: spruce planks on log stringers, log piles running up through the deck as posts, rail fence,
             lanterns on the posts; pier head with a fishing shack lean-to, crates, barrels, log benches.

CLIFF CLIMB (cliffclimbbase 7x10x7, cliffclimbsegment 7x9x7, cliffclimblanding 7x7x7; anchor (3,0,0)).
  A square switchback stair tower: outer ring (x / z = 0, 6) = corner posts and stringers with a railing, lane
  x 1..5 / z 1..5, solid spine x = 3, z 2..4.  One segment is one full turn rising CLIMB_RISE = 9: north landing
  (z = 1) -> flight A going south on x 1..2 (3 steps) -> south landing west half (x 1..2, z = 5) -> one step up
  (x = 3) -> south landing east part -> flight B going north on x 4..5 (3 steps) -> next north landing.  Every
  tread has 3+ free blocks above.  Stacking: segment on top of the base = base anchor + (0, 10, 0), segments every
  + (0, 9, 0), landing on the last segment at + (0, 9, 0).  The base is the same turn one block higher on a solid
  plinth, with entry steps on the north side; the landing is a full deck at the top with a stairwell opening over
  flight B, a railing, a shelter and the exit (gap in the south railing).
  Neoterra   white stair on light-gray concrete stringers, glass balustrade, concrete frame posts, light panels in
             the spine; landing = viewing deck with a cantilevered canopy, benches, planters.
  Hearthwood stone steps (stone-brick stairs and landings, mossy stringers), dark-oak handrail fence, stone piers,
             lanterns on the rail posts; landing = stone terrace with a little tiled lych-gate shelter and bench.
  Cascadia   timber trail stairs: spruce treads on log stringers, rail fence, log posts, river-rock spine,
             lanterns; landing = log lookout deck with a lean-to roof, bench and a trail sign.
"""
import json

from nbtlib import tag as T

from hm import Design, design, AIR, KEEP, SOLID

PACKS = ("Neoterra", "Hearthwood", "Cascadia")

# ---------------------------------------------------------------------------------------------- family constants
# subway
SUB_ROW = "WwetRtewW"          # cross-section x 0..8: Wall, walk, edge, trench, Rail, trench, edge, walk, Wall
SUB_FLOOR_Y, SUB_CURB_Y, SUB_RAIL_Y, SUB_CEIL_Y = 0, 1, 1, 6
SUB_LEN = 8                    # straight length (z)
SUB_POWER_Z = (3, 4)           # boosted rails in every straight
ENT_GY = 8                     # entrance street level (= anchor y); tunnel walkway level is ENT_DROP lower
ENT_DROP = 7
ENT_STAIR_X = (2, 6)           # stair lane
# boardwalk
BW_DECK_Y = 2                  # deck layer (= anchor y), stand on BW_DECK_Y + 1
BW_RAIL_X = (0, 4)
BW_PILE_Z = (1, 6)
# cliff climb
CLIMB_RISE = 9                 # one turn = one segment
BASE_RISE = 10                 # base height (first segment anchor = base anchor + (0, 10, 0))

LANTERN = "lantern[hanging=false,waterlogged=false]"
HANGING = "lantern[hanging=true,waterlogged=false]"
GRASS = "grass_block[snowy=false]"
PODZOL = "podzol[snowy=false]"


# ---------------------------------------------------------------------------------------------- block states
def stairs(n, facing, half="bottom", shape="straight"):
    return f"{n}_stairs[facing={facing},half={half},shape={shape},waterlogged=false]"


def slab(n, t="bottom"):
    return f"{n}_slab[type={t},waterlogged=false]"


def wall(n, up=True):
    return f"{n}_wall[east=none,north=none,south=none,up={'true' if up else 'false'},waterlogged=false,west=none]"


def log(n, axis="y"):
    return f"{n}[axis={axis}]"


def leaves(n):
    return f"{n}_leaves[distance=1,persistent=true,waterlogged=false]"


def rail(shape):
    return f"rail[shape={shape},waterlogged=false]"


def prail(powered, shape="north_south"):
    return f"powered_rail[powered={'true' if powered else 'false'},shape={shape},waterlogged=false]"


def button(kind="stone", face="floor", facing="north"):
    return f"{kind}_button[face={face},facing={facing},powered=false]"


def trap(n, facing, half="bottom", open_=False):
    return f"{n}_trapdoor[facing={facing},half={half},open={'true' if open_ else 'false'},powered=false,waterlogged=false]"


def sign_te(lines, glow=False, color="black", hanging=False):
    msgs = [json.dumps({"text": t}) for t in (list(lines) + ["", "", "", ""])[:4]]
    side = T.Compound({"messages": T.List[T.String]([T.String(m) for m in msgs]), "color": T.String(color),
                       "has_glowing_text": T.Byte(1 if glow else 0)})
    return T.Compound({"id": T.String("minecraft:hanging_sign" if hanging else "minecraft:sign"),
                       "front_text": side, "back_text": T.Compound(dict(side)), "is_waxed": T.Byte(1)})


def wall_sign(d, x, y, z, facing, lines, wood, glow=False, color="black"):
    d.set(x, y, z, f"{wood}_wall_sign[facing={facing},waterlogged=false]", sign_te(lines, glow, color))


def hang_sign(d, x, y, z, rotation, lines, wood, glow=False, color="black"):
    """Ceiling hanging sign under the block above (rotation 0 = text to the south, 8 = north)."""
    d.set(x, y, z, f"{wood}_hanging_sign[attached=false,rotation={rotation},waterlogged=false]",
          sign_te(lines, glow, color, hanging=True))


def post_sign(d, x, y, z, rotation, lines, wood):
    d.set(x, y, z, f"{wood}_sign[rotation={rotation},waterlogged=false]", sign_te(lines))


def plan(d, y, rows, legend, x0=0, z0=0):
    """Stamp a hand-drawn plan at height y: rows north -> south, characters west -> east; ' ' leaves the cell,
    '.' sets air, other characters come from legend."""
    w = len(rows[0])
    for r in rows:
        assert len(r) == w, f"{d.rel} {d.pack} y={y}: ragged plan row {r!r}"
    for dz, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch == " ":
                continue
            d.set(x0 + dx, y, z0 + dz, AIR if ch == "." else legend[ch])


def seat(d, x, y, z, wood, back):
    """Outdoor seat: a stair with its backrest on `back`, tagged sit_out."""
    d.set(x, y, z, stairs(wood, back))
    d.tag(x, y, z, "sit_out")


# ================================================================================================ SUBWAY
# per-pack tunnel materials: wall(y, u) gives the wall block at height y (u = position along the wall, for
# hand-laid stone patterns); walk / edge = walkway blocks (y 1), floor = slab under walkways, tfloor = trench floor
# (u = along-track index; even = sleeper rows), ceil = ceiling slab.
CAS_ROCK = {   # Cascadia tunnel wall courses (y 1..5), laid by hand along 8 positions; c cobble, a andesite,
               # t tuff, m mossy cobble, s stone
    1: "cmcacmtc",
    2: "atcsmcaa",
    3: "csatacst",
    4: "tacmscac",
    5: "smtcatms",
}
CAS_ROCKS = {"c": "cobblestone", "a": "andesite", "t": "tuff", "m": "mossy_cobblestone", "s": "stone"}


def sub_mat(pack):
    if pack == "Neoterra":
        def wallb(y, u):
            return {0: "light_gray_concrete", 1: "light_gray_concrete", 3: "cyan_terracotta"}.get(y, "white_concrete")
        return dict(wall=wallb, walk="smooth_stone", edge="yellow_concrete", floor="light_gray_concrete",
                    tfloor=lambda u: "gray_concrete", ceil="white_concrete", wallceil="light_gray_concrete")
    if pack == "Hearthwood":
        def wallb(y, u):
            return {0: "stone_bricks", 1: "stone_bricks", 2: "white_terracotta", 3: "red_terracotta",
                    4: "white_terracotta"}.get(y, "bricks")

        def tfl(u):
            return log("stripped_spruce_log", "x") if u % 2 == 0 else "gravel"
        return dict(wall=wallb, walk="stone_bricks", edge="smooth_stone", floor="stone_bricks", tfloor=tfl,
                    ceil="bricks", wallceil="bricks")

    def wallb(y, u):
        if y == 0:
            return "cobblestone"
        return CAS_ROCKS[CAS_ROCK[min(y, 5)][u % 8]]

    def tfl(u):
        return log("spruce_log", "x") if u % 2 == 0 else "gravel"
    return dict(wall=wallb, walk="spruce_planks", edge="stripped_spruce_wood[axis=y]", floor="cobblestone",
                tfloor=tfl, ceil="spruce_planks", wallceil="stone")


def sub_cell(d, x, z, kind, M, u, tfu=None, y0=0):
    """One column of the tunnel (y0 .. y0 + 6) of the given kind: W wall, w walkway, e walkway edge,
    t / R / C trench (R, C get their rail later)."""
    if kind == "W":
        for y in range(0, SUB_CEIL_Y):
            d.set(x, y0 + y, z, M["wall"](y, u))
        d.set(x, y0 + SUB_CEIL_Y, z, M["wallceil"])
        return
    d.set(x, y0 + SUB_FLOOR_Y, z, M["floor"])
    d.set(x, y0 + SUB_CEIL_Y, z, M["ceil"])
    if kind in "we":
        d.set(x, y0 + SUB_CURB_Y, z, M["walk"] if kind == "w" else M["edge"])
        lo = SUB_CURB_Y + 1
    else:
        d.set(x, y0 + SUB_FLOOR_Y, z, M["tfloor"](u if tfu is None else tfu))
        lo = SUB_RAIL_Y
    for y in range(lo, SUB_CEIL_Y):
        d.set(x, y0 + y, z, AIR)


def sub_straight_section(d, M, z, y0=0):
    for x, k in enumerate(SUB_ROW):
        # the two walls run in opposite directions, so the stone pattern is not mirrored
        sub_cell(d, x, z, k, M, z if x < 4 else z + 3, tfu=z, y0=y0)


def sub_track(d, zs, y0=0, power=True):
    for z in zs:
        d.set(4, y0 + SUB_RAIL_Y, z, rail("north_south"))
    if power:
        for z in SUB_POWER_Z:
            d.set(4, y0 + SUB_RAIL_Y, z, prail(True))
        d.set(4, y0 + SUB_FLOOR_Y, SUB_POWER_Z[0], "redstone_block")


def hw_rib(d, z, y0=0):
    """Hearthwood brick rib across the vault at z (walls stay, the haunch becomes a brick arch)."""
    for y in range(1, 6):
        d.set(0, y0 + y, z, "bricks")
        d.set(8, y0 + y, z, "bricks")
    d.set(1, y0 + 5, z, "bricks")
    d.set(7, y0 + 5, z, "bricks")
    d.set(2, y0 + 5, z, stairs("brick", "west", "top"))
    d.set(6, y0 + 5, z, stairs("brick", "east", "top"))


def hw_haunch(d, z, y0=0):
    d.set(1, y0 + 5, z, stairs("brick", "west", "top"))
    d.set(7, y0 + 5, z, stairs("brick", "east", "top"))


def cas_set(d, z, y0=0, lamp=True):
    """Cascadia timber set: log posts in both walls, a cap beam across under the lagging, lantern under it."""
    for y in range(1, 5):
        d.set(0, y0 + y, z, log("spruce_log"))
        d.set(8, y0 + y, z, log("spruce_log"))
    for x in range(0, 9):
        d.set(x, y0 + 5, z, log("spruce_log", "x"))
    if lamp:
        d.set(4, y0 + 4, z, HANGING)


def neo_frame(d, z, y0=0):
    """Neoterra portal frame: light-gray concrete ring in walls and ceiling."""
    for y in range(1, 6):
        d.set(0, y0 + y, z, "light_gray_concrete")
        d.set(8, y0 + y, z, "light_gray_concrete")
    for x in range(1, 8):
        d.set(x, y0 + SUB_CEIL_Y, z, "light_gray_concrete")


@design("subwaystraight")
def subwaystraight(pack, rel, L):
    d = Design(pack, rel, (9, 7, SUB_LEN), gy=1)
    M = sub_mat(pack)
    for z in range(SUB_LEN):
        sub_straight_section(d, M, z)
    sub_track(d, range(SUB_LEN))
    if pack == "Neoterra":
        neo_frame(d, 2)
        neo_frame(d, 5)
        d.set(4, 6, 0, "sea_lantern")              # ceiling light panels over the track, one per bay
        d.set(4, 6, 7, "sea_lantern")
        d.set(1, 6, 3, "glowstone")                # softer downlights over the walkways
        d.set(7, 6, 4, "glowstone")
        wall_sign(d, 1, 3, 4, "east", ["Line 1", "<-  ->"], "birch", glow=True, color="cyan")
    elif pack == "Hearthwood":
        for z in range(SUB_LEN):
            hw_haunch(d, z)
        hw_rib(d, 2)
        hw_rib(d, 5)
        d.set(4, 5, 0, HANGING)
        d.set(4, 5, 7, HANGING)
        d.set(2, 5, 3, HANGING)
        d.set(6, 5, 4, HANGING)
    else:
        cas_set(d, 2)
        cas_set(d, 5)
        d.set(1, 5, 0, HANGING)
        d.set(7, 5, 7, HANGING)
    d.anchor(4, 1, 0)
    return d


# corner: north arm (x 1..7 at z = 0) -> east arm (z 1..7 at x = 8) around a 7x7 chamber
CORNER_MAP = ["WwetRtewW",
              "WwetRteww",
              "WwetRteee",
              "WwetRtttt",
              "WwetCRRRR",
              "Wwetttttt",
              "Wweeeeeee",
              "Wwwwwwwww",
              "WWWWWWWWW"]


@design("subwaycorner")
def subwaycorner(pack, rel, L):
    d = Design(pack, rel, (9, 7, 9), gy=1)
    M = sub_mat(pack)
    for z, row in enumerate(CORNER_MAP):
        for x, k in enumerate(row):
            u = z if x == 0 else (x + 2 if z == 8 else 0)
            sub_cell(d, x, z, k, M, u, tfu=(z if x <= 5 else x))
    for z in range(4):
        d.set(4, SUB_RAIL_Y, z, rail("north_south"))
    d.set(4, SUB_RAIL_Y, 4, rail("north_east"))
    for x in range(5, 9):
        d.set(x, SUB_RAIL_Y, 4, rail("east_west"))
    if pack == "Neoterra":
        d.set(4, 6, 1, "sea_lantern")
        d.set(7, 6, 4, "sea_lantern")
        d.set(2, 6, 6, "glowstone")
        d.set(7, 6, 1, "glowstone")
        # the inner corner pillar is a light-gray column with a direction sign on the chamber side
        for y in range(1, 6):
            d.set(8, y, 0, "light_gray_concrete")
        wall_sign(d, 1, 3, 5, "east", ["Line 1", "-> east"], "birch", glow=True, color="cyan")
    elif pack == "Hearthwood":
        # vault haunches along the two outer walls, a brick pier at the inner corner
        for z in range(0, 8):
            d.set(1, 5, z, stairs("brick", "west", "top"))
        for x in range(2, 9):
            d.set(x, 5, 7, stairs("brick", "south", "top"))
        d.set(1, 5, 7, "bricks")
        for y in range(1, 6):
            d.set(8, y, 0, "bricks")
        d.set(4, 5, 1, HANGING)
        d.set(7, 5, 4, HANGING)
        d.set(3, 5, 5, HANGING)
    else:
        # timber: a set across each arm mouth and a log post in the inner corner
        for y in range(1, 5):
            d.set(0, y, 1, log("spruce_log"))
            d.set(7, y, 8, log("spruce_log"))
            d.set(8, y, 0, log("spruce_log"))
        for x in range(0, 9):
            d.set(x, 5, 1, log("spruce_log", "x"))
        for z in range(0, 9):
            d.set(7, 5, z, log("spruce_log", "z"))
        d.set(4, 4, 1, HANGING)
        d.set(7, 4, 4, HANGING)
        d.set(2, 5, 6, HANGING)
    d.anchor(4, 1, 0)
    return d


# ------------------------------------------------------------------------------------------------ entrance
def ent_shaft(d, M, side, ceilb):
    """The stair shaft z 1..6 and the platform / tunnel z 7..13 (common to all packs).
    side(y, z) -> block for the shaft side walls x = 1 / 7; ceilb = ceiling block of the stair (z 4..6)."""
    # tunnel part: like a straight, with a cross platform at z = 7 and the buffer at z = 8
    for z in range(7, 14):
        sub_straight_section(d, M, z)
    for x in range(1, 8):                       # cross platform (stair foot)
        sub_cell(d, x, 7, "e" if 2 <= x <= 6 else "w", M, 0)
    for z in range(1, 7):                       # side walls of the shaft
        tread = ENT_GY - z
        top = {1: 8, 2: 8, 3: 8, 4: 8, 5: 7, 6: 6}[z]
        for y in range(tread - 1, top + 1):
            d.set(1, y, z, side(y, z))
            d.set(7, y, z, side(y, z))
    for z in range(1, 7):
        tread = ENT_GY - z
        ceil = {4: 8, 5: 7, 6: 6}.get(z)        # z 1..3: open to the kiosk
        for x in range(ENT_STAIR_X[0], ENT_STAIR_X[1] + 1):
            d.set(x, tread, z, stairs(M["stair"], "north"))
            d.set(x, tread - 1, z, M["stairbed"])
            for y in range(tread + 1, (ceil if ceil else ENT_GY + 1)):
                d.set(x, y, z, AIR)
            if ceil:
                d.set(x, ceil, z, ceilb)
    # track: buffer with a departure button, brake rails, then plain rails into the next straight
    d.set(4, SUB_RAIL_Y, 8, M["buffer"])
    d.set(4, SUB_RAIL_Y + 1, 8, M["button"])
    d.set(4, SUB_RAIL_Y, 9, prail(False))
    d.set(4, SUB_RAIL_Y, 10, prail(False))
    for z in range(11, 14):
        d.set(4, SUB_RAIL_Y, z, rail("north_south"))


@design("subwayentrance")
def subwayentrance(pack, rel, L):
    return {"Neoterra": neo_entrance, "Hearthwood": hw_entrance, "Cascadia": cas_entrance}[pack](pack, rel)


def neo_entrance(pack, rel):
    d = Design(pack, rel, (9, 14, 14), gy=ENT_GY, paving="light_gray_concrete")
    M = dict(sub_mat(pack), stair="polished_andesite", stairbed="polished_andesite", buffer="yellow_concrete",
             button=button("stone"))
    ent_shaft(d, M, lambda y, z: "white_concrete" if y != ENT_GY - z + 2 else "cyan_terracotta", "white_concrete")
    neo_frame(d, 10)
    d.set(4, 6, 12, "sea_lantern")
    d.set(4, 6, 8, "glowstone")
    d.set(1, 6, 5, "sea_lantern")              # light panels in the shaft walls at head height
    d.set(7, 7, 4, "sea_lantern")
    wall_sign(d, 7, 3, 9, "west", ["Line 1", "Platform", "<- trains"], "birch", glow=True, color="cyan")
    # street level: paving with a strip of smooth stone in front, the opening x 2..6 z 1..3 is open (air above stair)
    for x in range(0, 9):
        d.set(x, ENT_GY, 0, "smooth_stone")
    # kiosk: four light-gray frames, glass side walls, white back wall, cantilevered canopy
    for (x, z) in ((1, 0), (7, 0), (1, 4), (7, 4)):
        for y in range(9, 13):
            d.set(x, y, z, "light_gray_concrete")
    for z in (1, 2, 3):
        for y in range(9, 13):
            d.set(1, y, z, "glass_pane")
            d.set(7, y, z, "glass_pane")
    for x in range(2, 7):
        for y in range(9, 13):
            d.set(x, y, 4, "white_concrete")
    d.set(4, 9, 4, "cyan_terracotta")
    wall_sign(d, 4, 11, 3, "north", ["METRO", "Line 1", "v  platforms  v"], "birch", glow=True, color="cyan")
    # canopy y 13 (x 0..8, z 0..5) with a light-gray fascia and two light panels over the stair
    for x in range(0, 9):
        for z in range(0, 6):
            edge = x in (0, 8) or z in (0, 5)
            d.set(x, 13, z, "light_gray_concrete" if edge else "white_concrete")
    d.set(3, 13, 2, "sea_lantern")
    d.set(5, 13, 2, "sea_lantern")
    # fascia header inside the canopy with the glowing name board facing the street
    for x in range(2, 7):
        d.set(x, 12, 1, "light_gray_concrete")
    for x in (3, 4, 5):
        wall_sign(d, x, 12, 0, "north", ["", "METRO" if x == 4 else ("M" if x == 3 else "1"), ""], "birch",
                  glow=True, color="white")
    # cyan "M" totem beside the entrance, moss planter on the other side
    for y in range(9, 12):
        d.set(8, y, 1, "cyan_concrete")
    d.set(8, 12, 1, "sea_lantern")
    wall_sign(d, 8, 11, 0, "north", ["", "M", ""], "birch", glow=True, color="white")
    for z in (1, 2, 3):
        d.set(0, 9, z, "moss_block")
    d.set(0, 10, 1, "azalea")
    d.set(0, 10, 2, "flowering_azalea")
    d.set(0, 10, 3, "azalea")
    # plaza over the tunnel: bench and a light bollard
    for z in range(6, 14):
        for x in range(0, 9):
            d.set(x, ENT_GY, z, "light_gray_concrete" if (x + z) % 4 else "smooth_stone")
    d.set(2, 9, 8, stairs("birch", "west"))
    d.set(2, 9, 9, stairs("birch", "west"))
    d.set(6, 9, 10, "polished_andesite")
    d.set(6, 10, 10, "sea_lantern")
    d.anchor(4, ENT_GY, 0)
    return d


def hw_entrance(pack, rel):
    d = Design(pack, rel, (9, 14, 14), gy=ENT_GY, paving="stone_bricks")
    M = dict(sub_mat(pack), stair="stone_brick", stairbed="stone_bricks", buffer="red_terracotta",
             button=button("stone"))

    def side(y, z):
        t = ENT_GY - z
        return "stone_bricks" if y <= t else ("red_terracotta" if y == t + 2 else "white_terracotta")
    ent_shaft(d, M, side, "bricks")
    for z in range(7, 14):
        hw_haunch(d, z)
    hw_rib(d, 10)
    d.set(4, 5, 12, HANGING)
    d.set(4, 5, 8, HANGING)
    d.set(2, 5, 7, HANGING)
    # lanterns in niches of the shaft walls
    d.set(1, 6, 4, LANTERN)
    d.set(7, 5, 5, LANTERN)
    wall_sign(d, 7, 3, 11, "west", ["Platform 1", "Way out ^"], "dark_oak")
    # street: stone setts in front
    for x in range(0, 9):
        d.set(x, ENT_GY, 0, "polished_andesite")
    # kiosk walls x 1 / 7, back wall z 4 in ox-blood terracotta on a stone plinth course
    for z in range(0, 5):
        for y in range(9, 13):
            blk = "stone_bricks" if y == 9 else "red_terracotta"
            d.set(1, y, z, blk)
            d.set(7, y, z, blk)
    for x in range(2, 7):
        for y in range(9, 13):
            d.set(x, y, 4, "stone_bricks" if y == 9 else "red_terracotta")
    for z in (2,):
        d.set(1, 10, z, "glass_pane")
        d.set(1, 11, z, "glass_pane")
        d.set(7, 10, z, "glass_pane")
        d.set(7, 11, z, "glass_pane")
    d.set(4, 11, 4, "glass_pane")              # semicircular-ish fanlight in the back wall
    d.set(3, 11, 4, stairs("polished_granite", "west", "top"))
    d.set(5, 11, 4, stairs("polished_granite", "east", "top"))
    # front arch over the opening: granite springers, terracotta header with the name board hanging under it
    d.set(2, 11, 0, stairs("polished_granite", "west", "top"))
    d.set(6, 11, 0, stairs("polished_granite", "east", "top"))
    for x in range(2, 7):
        d.set(x, 12, 0, "red_terracotta")
    hang_sign(d, 4, 11, 0, 8, ["UNDERGROUND", "", "Line 1"], "dark_oak")
    # flat roof with a stone-brick cornice
    for x in range(1, 8):
        for z in range(0, 5):
            edge = x in (1, 7) or z in (0, 4)
            d.set(x, 13, z, slab("stone_brick") if edge else slab("smooth_stone"))
    # black lamp standards either side of the arch, flower pots along the side walls
    for x in (0, 8):
        d.set(x, 9, 0, wall("polished_deepslate"))
        d.set(x, 10, 0, wall("polished_deepslate"))
        d.set(x, 11, 0, LANTERN)
    wall_sign(d, 0, 11, 2, "west", ["UNDERGROUND"], "dark_oak")
    d.set(0, 9, 3, "potted_red_tulip")
    d.set(8, 9, 2, "potted_azure_bluet")
    d.set(8, 9, 3, "potted_red_tulip")
    # green over the tunnel: grass, a clipped box hedge and a bench
    for z in range(5, 14):
        for x in range(0, 9):
            d.set(x, ENT_GY, z, GRASS)
    for x in range(0, 9):
        d.set(x, ENT_GY, 5, "gravel")
    for z in range(8, 12):
        d.set(0, 9, z, leaves("oak"))
        d.set(8, 9, z, leaves("oak"))
    d.set(4, 9, 9, stairs("dark_oak", "south"))
    d.set(3, 9, 9, trap("dark_oak", "west", open_=True))
    d.set(5, 9, 9, trap("dark_oak", "east", open_=True))
    d.set(2, 9, 11, "rose_bush[half=lower]")
    d.set(2, 10, 11, "rose_bush[half=upper]")
    d.anchor(4, ENT_GY, 0)
    return d


def cas_entrance(pack, rel):
    d = Design(pack, rel, (9, 14, 14), gy=ENT_GY, paving="coarse_dirt")
    M = dict(sub_mat(pack), stair="spruce", stairbed="cobblestone", buffer=log("spruce_log", "x"),
             button=button("spruce"))

    def side(y, z):
        return CAS_ROCKS[CAS_ROCK[min(max(y - (ENT_GY - z), 1), 5)][(z + y) % 8]]
    ent_shaft(d, M, side, "spruce_planks")
    for z in (8, 11):
        cas_set(d, z)
    # timber frames down the stair: log posts against the walls carrying a beam under the plank ceiling
    for x in range(2, 7):
        d.set(x, 7, 5, log("spruce_log", "x"))
    d.set(1, 6, 4, LANTERN)
    d.set(7, 5, 5, LANTERN)
    wall_sign(d, 7, 3, 9, "west", ["Line 1", "Trains ->"], "spruce")
    # street: plank threshold
    for x in range(0, 9):
        d.set(x, ENT_GY, 0, "spruce_planks")
    # portal: river-rock knee walls, log posts, A-frame roof (ridge along z) with a plank gable and sign
    for z in range(0, 5):
        d.set(1, 9, z, "mossy_cobblestone" if z % 2 else "cobblestone")
        d.set(7, 9, z, "cobblestone" if z % 2 else "mossy_cobblestone")
        d.set(1, 10, z, "spruce_planks")
        d.set(7, 10, z, "spruce_planks")
    for (x, z) in ((1, 0), (7, 0), (1, 4), (7, 4)):
        d.set(x, 9, z, log("spruce_log"))
        d.set(x, 10, z, log("spruce_log"))
    for x in range(1, 8):
        d.set(x, 11, 0, log("spruce_log", "x"))     # header beam over the portal
    for x in range(2, 7):
        for y in (9, 10, 11):
            d.set(x, y, 4, "spruce_planks")         # back wall
    for z in range(0, 5):
        d.set(0, 10, z, stairs("spruce", "east"))
        d.set(1, 11, z, stairs("spruce", "east"))
        d.set(2, 12, z, stairs("spruce", "east"))
        d.set(3, 13, z, stairs("spruce", "east"))
        d.set(8, 10, z, stairs("spruce", "west"))
        d.set(7, 11, z, stairs("spruce", "west"))
        d.set(6, 12, z, stairs("spruce", "west"))
        d.set(5, 13, z, stairs("spruce", "west"))
        d.set(4, 13, z, "spruce_planks")
    for x in (3, 4, 5):
        d.set(x, 12, 1, "spruce_planks")            # front gable infill (set back one) with the sign
        d.set(x, 12, 4, "spruce_planks")
    wall_sign(d, 4, 12, 0, "north", ["SUBWAY", "Line 1"], "spruce")
    d.set(0, 9, 1, HANGING)
    d.set(8, 9, 3, HANGING)
    # over the tunnel: rough ground, a boulder, ferns and a log bench
    for z in range(5, 14):
        for x in range(0, 9):
            d.set(x, ENT_GY, z, GRASS if (x * 3 + z) % 5 else "coarse_dirt")
    d.set(7, 9, 9, "mossy_cobblestone")
    d.set(7, 9, 10, slab("cobblestone"))
    d.set(6, 9, 9, "fern")
    d.set(1, 9, 7, "fern")
    d.set(2, 9, 11, log("stripped_spruce_log", "z"))
    d.set(2, 9, 12, log("stripped_spruce_log", "z"))
    d.anchor(4, ENT_GY, 0)
    return d


# ================================================================================================ BOARDWALK
def bw_ground(d):
    """Below the deck everything is left as it is (water, sand) except the piles drawn later."""
    d.fill(0, 0, 0, d.sx - 1, BW_DECK_Y - 1, d.sz - 1, KEEP)


def bw_mat(pack):
    if pack == "Neoterra":
        return dict(board="mangrove_planks", edge="light_gray_concrete", rail="glass_pane", pile="light_gray_concrete",
                    cap="light_gray_concrete", wood="birch")
    if pack == "Hearthwood":
        return dict(board="oak_planks", edge=log("stripped_dark_oak_log", "z"), edge_x=log("stripped_dark_oak_log", "x"),
                    rail="birch_fence", pile=log("dark_oak_log"), cap=log("dark_oak_log", "x"), wood="dark_oak")
    return dict(board="spruce_planks", edge=log("stripped_spruce_log", "z"), edge_x=log("stripped_spruce_log", "x"),
                rail="spruce_fence", pile=log("spruce_log"), cap=log("spruce_log", "x"), wood="spruce")


def bw_lamp(d, pack, x, z):
    """Lamp standard on the railing line at (x, z), standing on the deck."""
    y = BW_DECK_Y + 1
    if pack == "Neoterra":
        d.set(x, y, z, "light_gray_concrete")
        d.set(x, y + 1, z, wall("andesite"))
        d.set(x, y + 2, z, "sea_lantern")
    elif pack == "Hearthwood":
        d.set(x, y, z, wall("polished_deepslate"))
        d.set(x, y + 1, z, wall("polished_deepslate"))
        d.set(x, y + 2, z, LANTERN)
    else:
        d.set(x, BW_DECK_Y, z, log("spruce_log"))
        d.set(x, y, z, log("spruce_log"))
        d.set(x, y + 1, z, log("spruce_log"))
        d.set(x, y + 2, z, LANTERN)


def bw_post(d, pack, x, z):
    """Plain railing post (no lamp) at (x, z)."""
    y = BW_DECK_Y + 1
    if pack == "Neoterra":
        d.set(x, y, z, "light_gray_concrete")
    elif pack == "Hearthwood":
        d.set(x, y, z, log("stripped_dark_oak_log"))
        d.set(x, y + 1, z, "dark_oak_pressure_plate[powered=false]")
    else:
        d.set(x, BW_DECK_Y, z, log("spruce_log"))
        d.set(x, y, z, log("spruce_log"))


def bw_pile(d, pack, x, z):
    M = bw_mat(pack)
    for y in range(0, BW_DECK_Y):
        d.set(x, y, z, M["pile"])


def bw_row(d, pack, z, x0=0, along="z"):
    """One deck row of the boardwalk cross-section starting at x0 (railing, 3 boards, railing)."""
    M = bw_mat(pack)
    edge = M["edge"] if along == "z" else M.get("edge_x", M["edge"])
    for i in range(5):
        x = x0 + i
        d.set(x, BW_DECK_Y, z, edge if i in (0, 4) else M["board"])
        d.set(x, BW_DECK_Y + 1, z, M["rail"] if i in (0, 4) else AIR)
        for y in range(BW_DECK_Y + 2, d.sy):
            d.set(x, y, z, AIR)


def bw_bent(d, pack, z, x0=0):
    """Pile bent under the deck at row z: two piles under the railings and a cap beam between them."""
    M = bw_mat(pack)
    bw_pile(d, pack, x0, z)
    bw_pile(d, pack, x0 + 4, z)
    for x in range(x0 + 1, x0 + 4):
        d.set(x, BW_DECK_Y - 1, z, M["cap"])


@design("boardwalkstraight")
def boardwalkstraight(pack, rel, L):
    d = Design(pack, rel, (5, 10, 8), gy=BW_DECK_Y)
    bw_ground(d)
    for z in range(8):
        bw_row(d, pack, z)
    for z in BW_PILE_Z:
        bw_bent(d, pack, z)
    # one lamp per straight (west rail over the first bent), plain posts over the other piles
    bw_lamp(d, pack, 0, 1)
    bw_post(d, pack, 4, 1)
    bw_post(d, pack, 0, 6)
    bw_post(d, pack, 4, 6)
    if pack == "Neoterra":
        d.set(2, BW_DECK_Y, 3, "light_gray_concrete")     # a concrete inlay band across the deck at mid-bay
        d.set(1, BW_DECK_Y, 3, "light_gray_concrete")
        d.set(3, BW_DECK_Y, 3, "light_gray_concrete")
    elif pack == "Hearthwood":
        d.set(4, BW_DECK_Y + 1, 3, log("stripped_dark_oak_log"))     # intermediate posts at mid-bay
        d.set(0, BW_DECK_Y + 1, 4, log("stripped_dark_oak_log"))
    else:
        d.set(1, BW_DECK_Y, 3, "stripped_spruce_wood[axis=y]")     # a patched board and a rope coil (chain)
        d.set(3, BW_DECK_Y + 1, 4, AIR)
    d.anchor(2, BW_DECK_Y, 0)
    return d


@design("boardwalkcorner")
def boardwalkcorner(pack, rel, L):
    d = Design(pack, rel, (5, 10, 5), gy=BW_DECK_Y)
    bw_ground(d)
    M = bw_mat(pack)
    # deck: boards inside, edge beams under the outer railing (west and south) and the inner post
    for z in range(5):
        for x in range(5):
            outer = x == 0 or z == 4
            if x == 0:
                blk = M["edge"]
            elif z == 4:
                blk = M.get("edge_x", M["edge"])
            elif (x, z) == (4, 0):
                blk = M["edge"] if pack != "Cascadia" else log("spruce_log")
            else:
                blk = M["board"]
            d.set(x, BW_DECK_Y, z, blk)
            d.set(x, BW_DECK_Y + 1, z, M["rail"] if outer else AIR)
    d.set(4, BW_DECK_Y + 1, 0, M["rail"])
    for (x, z) in ((0, 0), (4, 0), (0, 4), (4, 4)):
        bw_pile(d, pack, x, z)
    for i in range(1, 4):
        d.set(0, BW_DECK_Y - 1, i, log(M["cap"].split("[")[0], "z") if "log" in M["cap"] else M["cap"])
        d.set(i, BW_DECK_Y - 1, 4, M["cap"])
    bw_lamp(d, pack, 0, 4)                                 # lamp on the outer corner
    bw_post(d, pack, 4, 0)                                 # inner corner post
    if pack == "Neoterra":
        d.set(1, BW_DECK_Y + 1, 3, "moss_block")            # little planter in the outer corner
        d.set(1, BW_DECK_Y + 2, 3, "flowering_azalea")
    elif pack == "Hearthwood":
        d.set(1, BW_DECK_Y + 1, 3, "potted_red_tulip")
    else:
        d.set(1, BW_DECK_Y + 1, 3, "barrel[facing=up,open=false]")
    d.anchor(2, BW_DECK_Y, 0)
    return d


# ------------------------------------------------------------------------------------------------ pier
PIER_CTRL = (4, BW_DECK_Y + 1, 0)


def pier_frame(d, pack):
    """Neck (z 0..4, boardwalk cross-section on x 2..6) and head (z 5..11, x 0..8) deck with railings and piles."""
    M = bw_mat(pack)
    bw_ground(d)
    for z in range(0, 5):
        for x in (0, 1, 7, 8):
            for y in range(BW_DECK_Y, d.sy):
                d.set(x, y, z, KEEP)
        bw_row(d, pack, z, x0=2)
    for z in range(5, 12):
        for x in range(9):
            rim = x in (0, 8) or z == 11 or (z == 5 and x not in (3, 4, 5))
            if rim:
                blk = M["edge"] if x in (0, 8) else M.get("edge_x", M["edge"])
            else:
                blk = M["board"]
            d.set(x, BW_DECK_Y, z, blk)
            d.set(x, BW_DECK_Y + 1, z, M["rail"] if rim else AIR)
            for y in range(BW_DECK_Y + 2, d.sy):
                d.set(x, y, z, AIR)
    bw_bent(d, pack, 1, x0=2)
    for (x, z) in ((0, 5), (8, 5), (0, 8), (8, 8), (0, 11), (4, 11), (8, 11), (2, 5), (6, 5)):
        bw_pile(d, pack, x, z)
    for x in range(1, 8):
        d.set(x, BW_DECK_Y - 1, 11, M["cap"])
        d.set(x, BW_DECK_Y - 1, 8, M["cap"])


@design("pier")
def pier(pack, rel, L):
    d = Design(pack, rel, (9, 10, 12), gy=BW_DECK_Y)
    pier_frame(d, pack)
    {"Neoterra": neo_pier, "Hearthwood": hw_pier, "Cascadia": cas_pier}[pack](d)
    d.hut(*PIER_CTRL, facing="down")
    return d


def neo_pier(d):
    y = BW_DECK_Y + 1
    bw_lamp(d, "Neoterra", 2, 2)
    bw_post(d, "Neoterra", 6, 2)
    # canopy: white roof on two concrete fins at the far corners, light panels in its soffit
    for x in (1, 7):
        for yy in range(y, y + 3):
            d.set(x, yy, 10, "light_gray_concrete")
    for x in range(1, 8):
        for z in range(7, 11):
            d.set(x, y + 3, z, "light_gray_concrete" if z == 7 or x in (1, 7) else "white_concrete")
    d.set(3, y + 3, 8, "sea_lantern")
    d.set(5, y + 3, 8, "sea_lantern")
    # four seats under the canopy looking out over the water to east and west
    for z in (8, 9):
        seat(d, 1, y, z, "birch", "east")
        seat(d, 7, y, z, "birch", "west")
    # viewing scope at the end, planters on the shoulders, life ring on the end rail
    d.set(4, y, 10, wall("andesite"))
    d.set(4, y + 1, 10, "lightning_rod[facing=south,powered=false,waterlogged=false]")
    for x in (1, 7):
        d.set(x, y, 6, "moss_block")
        d.set(x, y + 1, 6, "flowering_azalea" if x == 1 else "azalea")
    d.set(0, y, 5, "light_gray_concrete")
    d.set(8, y, 5, "light_gray_concrete")
    d.set(0, y, 11, "light_gray_concrete")
    d.set(8, y, 11, "light_gray_concrete")
    wall_sign(d, 3, y, 10, "north", ["Viewpoint", "", "Harbour"], "birch")
    d.set(3, y, 11, "light_gray_concrete")


def hw_pier(d):
    y = BW_DECK_Y + 1
    bw_lamp(d, "Hearthwood", 6, 2)
    bw_post(d, "Hearthwood", 2, 2)
    bw_lamp(d, "Hearthwood", 0, 5)
    bw_lamp(d, "Hearthwood", 8, 5)
    bw_post(d, "Hearthwood", 0, 11)
    bw_post(d, "Hearthwood", 8, 11)
    # shelter: four dark-oak posts with a deepslate-tile hip roof
    for (x, z) in ((2, 7), (6, 7), (2, 10), (6, 10)):
        for yy in range(y, y + 3):
            d.set(x, yy, z, log("stripped_dark_oak_log"))
    d.hip(2, 7, 6, 10, y + 3, stairs="deepslate_tile_stairs", cap="deepslate_tile_slab")
    # back-to-back benches in the shelter (looking north to the town and south out to sea)
    for x in (3, 4, 5):
        seat(d, x, y, 8, "dark_oak", "south")
        seat(d, x, y, 9, "dark_oak", "north")
    # lantern under the roof, name board on the front post, fishing corner with bait barrels
    d.set(4, y + 3, 8, HANGING)
    wall_sign(d, 2, y + 1, 6, "north", ["Pier Head", "", "No diving"], "dark_oak")
    d.set(1, y, 10, "barrel[facing=up,open=false]")
    d.set(7, y, 10, "barrel[facing=up,open=false]")
    d.set(7, y + 1, 10, "potted_red_tulip")


def cas_pier(d):
    y = BW_DECK_Y + 1
    bw_lamp(d, "Cascadia", 2, 2)
    bw_post(d, "Cascadia", 6, 2)
    for (x, z) in ((0, 5), (8, 5), (0, 8)):
        bw_post(d, "Cascadia", x, z)
    bw_lamp(d, "Cascadia", 0, 11)
    # fishing shack in the south-east corner: plank walls, log corner posts, lean-to roof, door opening west
    for z in range(8, 12):
        for yy in range(y, y + 3):
            d.set(8, yy, z, "spruce_planks")
    for x in range(5, 9):
        for yy in range(y, y + 3):
            d.set(x, yy, 11, "spruce_planks")
    for (x, z) in ((8, 8), (8, 11), (5, 11), (5, 8)):
        for yy in range(BW_DECK_Y, y + 3):
            d.set(x, yy, z, log("spruce_log"))
    for z in range(7, 12):
        d.set(4, y + 3, z, slab("spruce"))
        for x in range(5, 9):
            d.set(x, y + 3, z, "spruce_planks" if x == 8 else slab("spruce", "top"))
    d.set(8, y + 1, 10, "glass_pane")
    d.set(6, y, 10, "barrel[facing=up,open=false]")
    d.set(7, y, 10, "barrel[facing=up,open=false]")
    d.set(7, y + 1, 10, "barrel[facing=up,open=false]")
    d.set(7, y, 9, "composter[level=0]")
    d.set(6, y + 2, 9, HANGING)
    # log benches along the west rail looking out, and one at the end
    for z in (6, 7, 8):
        seat(d, 1, y, z, "spruce", "east")
    seat(d, 3, y, 10, "spruce", "north")
    d.set(2, y, 10, "barrel[facing=up,open=false]")
    d.set(4, y, 6, "barrel[facing=up,open=false]")


# ================================================================================================ CLIFF CLIMB
# One turn of the switchback, in segment coordinates (y 0..8; the whole thing repeats every CLIMB_RISE).
# Lane treads: (x, y, z, kind)  L = landing block, S<facing> = stair rising toward <facing>.
CLIMB_TREADS = (
    [(x, 0, 1, "L") for x in range(1, 6)]                                    # north landing
    + [(x, 1 + i, 2 + i, "Ssouth") for i in range(3) for x in (1, 2)]        # flight A, going south
    + [(x, 4, 5, "L") for x in (1, 2)]                                       # south landing, west half
    + [(3, 5, 5, "Seast")]                                                   # one step up across the landing
    + [(x, 5, 5, "L") for x in (4, 5)]                                       # south landing, east part
    + [(x, 6 + i, 4 - i, "Snorth") for i in range(3) for x in (4, 5)]        # flight B, going north
)
# undersides (soffits) of the flights and landings: (x, y, z, kind) U<facing> = upside-down stair, B = slab top
CLIMB_SOFFITS = (
    [(x, i, 2 + i, "Unorth") for i in range(3) for x in (1, 2)]
    + [(x, 5 + i, 4 - i, "Usouth") for i in range(3) for x in (4, 5)]
    + [(x, 3, 5, "B") for x in (1, 2)] + [(3, 4, 5, "L")] + [(x, 4, 5, "B") for x in (4, 5)]
    + [(x, -1, 1, "B") for x in range(1, 6)]
)
# outer ring: (x, z, t) stringer top at t, railing at t + 1 (t of the lane cell next to it)
CLIMB_RING = (
    [(0, 1, 0), (0, 2, 1), (0, 3, 2), (0, 4, 3), (0, 5, 4)]
    + [(6, 1, 0), (6, 2, 8), (6, 3, 7), (6, 4, 6), (6, 5, 5)]
    + [(x, 0, 0) for x in range(1, 6)]
    + [(1, 6, 4), (2, 6, 4), (3, 6, 5), (4, 6, 5), (5, 6, 5)]
)
CLIMB_POSTS = ((0, 0), (6, 0), (0, 6), (6, 6))
CLIMB_SPINE = [(3, z) for z in (2, 3, 4)]


def climb_mat(pack):
    if pack == "Neoterra":
        return dict(tread="polished_diorite", land="polished_diorite", soffit="polished_diorite",
                    underslab="smooth_stone", stringer=lambda ax: "light_gray_concrete",
                    rail="glass_pane", post=lambda y: "light_gray_concrete", plinth="polished_andesite",
                    spine={2: "wwwwcwwww", 3: "wwwwcwwww", 4: "wwwwcwwww"},
                    spineb={"w": "white_concrete", "c": "cyan_terracotta"})
    if pack == "Hearthwood":
        return dict(tread="stone_brick", land="stone_bricks", soffit="stone_brick", underslab="stone_brick",
                    stringer=lambda ax: "stone_bricks", rail="dark_oak_fence",
                    post=lambda y: "mossy_stone_bricks" if y % 9 in (0, 5) else "stone_bricks",
                    plinth="stone_bricks",
                    spine={2: "sssmsscss", 3: "scsssmsss", 4: "msssscssm"},
                    spineb={"s": "stone_bricks", "m": "mossy_stone_bricks", "c": "chiseled_stone_bricks"})
    return dict(tread="spruce", land="spruce_planks", soffit="spruce", underslab="spruce",
                stringer=lambda ax: log("stripped_spruce_log", ax), rail="spruce_fence",
                post=lambda y: log("spruce_log"), plinth="cobblestone",
                spine={2: "camcacmca", 3: "macatcamc", 4: "cmcatmcac"},
                spineb={"c": "cobblestone", "m": "mossy_cobblestone", "a": "andesite", "t": "tuff"})


def climb_turn(d, M, dy, lo, hi, wrap=True):
    """Draw one turn shifted up by dy, keeping only layers lo..hi. With wrap, layers outside one period fold
    back into it (a segment holds its own turn plus the railing of the turn below / soffit of the turn above)."""
    def put(x, y, z, blk):
        yy = (y % CLIMB_RISE if wrap else y) + dy
        if lo <= yy <= hi:
            d.set(x, yy, z, blk)

    for x, y, z, k in CLIMB_SOFFITS:
        if k == "B":
            put(x, y, z, slab(M["underslab"], "top"))
        elif k == "L":
            put(x, y, z, M["land"])
        else:
            put(x, y, z, stairs(M["soffit"], k[1:], "top"))
    for x, y, z, k in CLIMB_TREADS:
        put(x, y, z, M["land"] if k == "L" else stairs(M["tread"], k[1:]))
    for x, z, t in CLIMB_RING:
        ax = "z" if x in (0, 6) else "x"
        put(x, t, z, M["stringer"](ax))
        put(x, t - 1, z, M["stringer"](ax))
        put(x, t + 1, z, M["rail"])
    for x, z in CLIMB_POSTS:
        for y in range(CLIMB_RISE):
            put(x, y, z, M["post"](y))
    for x, z in CLIMB_SPINE:
        for y in range(CLIMB_RISE):
            put(x, y, z, M["spineb"][M["spine"][z][y]])


def climb_lights(d, pack, dy):
    """Two lights per turn: Neoterra light panels in the spine, otherwise lanterns standing on rail posts."""
    if pack == "Neoterra":
        d.set(3, dy + 2, 2, "sea_lantern")       # faces the north landing
        d.set(3, dy + 7, 4, "sea_lantern")       # faces the south landing step
    else:
        d.set(0, dy + 6, 5, LANTERN)             # on the rail beside the south landing
        d.set(6, dy + 2, 1, LANTERN)             # on the rail beside the north landing


@design("cliffclimbsegment")
def cliffclimbsegment(pack, rel, L):
    d = Design(pack, rel, (7, CLIMB_RISE, 7), gy=0)
    d.fill(0, 0, 0, 6, CLIMB_RISE - 1, 6, AIR)
    M = climb_mat(pack)
    climb_turn(d, M, 0, 0, CLIMB_RISE - 1)
    climb_lights(d, pack, 0)
    if pack == "Hearthwood":
        d.set(0, 3, 3, "mossy_stone_bricks")     # weathered stringer stones
        d.set(6, 6, 4, "mossy_stone_bricks")
    elif pack == "Cascadia":
        d.set(6, 4, 5, "spruce_log[axis=z]")     # bark-on log in the stringer
    d.anchor(3, 0, 0)
    return d


@design("cliffclimbbase")
def cliffclimbbase(pack, rel, L):
    d = Design(pack, rel, (7, BASE_RISE, 7), gy=0)
    M = climb_mat(pack)
    d.fill(0, 1, 0, 6, BASE_RISE - 1, 6, AIR)
    # the turn one block up, on a solid plinth: everything under a tread / stringer is masonry down to the ground
    climb_turn(d, M, 1, 1, BASE_RISE - 1)
    for x, y, z, k in CLIMB_TREADS:
        for yy in range(1, y + 1):
            d.set(x, yy, z, M["plinth"])
    for x, z, t in CLIMB_RING:
        for yy in range(1, t + 1):
            d.set(x, yy, z, M["plinth"])
    d.set(3, 1, 5, M["plinth"])
    climb_lights(d, pack, 1)
    # entry steps from the street on the north side (x 1..3), railing kept on x 4..5
    for x in (1, 2, 3):
        d.set(x, 1, 0, stairs(M["tread"], "south"))
        d.set(x, 2, 0, AIR)
    if pack == "Neoterra":
        for x in range(0, 7):
            d.set(x, 0, 0, "light_gray_concrete")
        post_sign(d, 5, 2, 0, 8, ["SKYSTEPS", "", "Viewpoint ^"], "birch")
        d.set(4, 2, 0, "glass_pane")
    elif pack == "Hearthwood":
        post_sign(d, 5, 2, 0, 8, ["Cliff Steps", "to the", "Top Green"], "dark_oak")
        d.set(0, 1, 1, "mossy_stone_bricks")
        d.set(0, 2, 2, "mossy_stone_bricks")
    else:
        post_sign(d, 5, 2, 0, 8, ["TRAIL", "Lookout ^", ""], "spruce")
        d.set(6, 1, 1, "mossy_cobblestone")
        d.set(0, 1, 2, "mossy_cobblestone")
    d.anchor(3, 0, 0)
    return d


@design("cliffclimblanding")
def cliffclimblanding(pack, rel, L):
    d = Design(pack, rel, (7, 7, 7), gy=0)
    M = climb_mat(pack)
    d.fill(0, 0, 0, 6, 6, 6, AIR)
    # deck over the whole top, open over flight B (x 4..5, z 2..4) where the stair arrives
    for x in range(7):
        for z in range(7):
            if 4 <= x <= 5 and 2 <= z <= 4:
                continue
            d.set(x, 0, z, M["land"])
    d.set(6, 0, 2, M["rail"])                    # railing beside the last step (the turn below)
    for x, z in CLIMB_SPINE:
        d.set(x, 0, z, M["spineb"][M["spine"][z][0]])
    # railing around the deck (gap x 1..3 in the south side = way out onto the cliff top) and the stairwell
    for i in range(7):
        for (x, z) in ((i, 0), (0, i), (6, i), (i, 6)):
            if z == 6 and 1 <= x <= 3:
                continue
            d.set(x, 1, z, M["rail"])
    for z in (2, 3, 4):
        d.set(3, 1, z, M["rail"])
    for x in (4, 5):
        d.set(x, 1, 5, M["rail"])
    {"Neoterra": neo_landing, "Hearthwood": hw_landing, "Cascadia": cas_landing}[pack](d, M)
    d.anchor(3, 0, 0)
    return d


def neo_landing(d, M):
    # canopy on two concrete fins at the north corners, cantilevered south; light panels; benches facing the view
    for (x, z) in ((0, 0), (6, 0)):
        for y in range(1, 5):
            d.set(x, y, z, "light_gray_concrete")
    for x in range(7):
        for z in range(0, 4):
            d.set(x, 5, z, "light_gray_concrete" if z == 0 or x in (0, 6) else "white_concrete")
    d.set(2, 5, 2, "sea_lantern")
    seat_free(d, 1, 1, 2, "birch", "east")
    seat_free(d, 1, 1, 3, "birch", "east")
    d.set(1, 1, 4, "moss_block")
    d.set(1, 2, 4, "flowering_azalea")
    d.set(6, 1, 6, "light_gray_concrete")
    d.set(6, 2, 6, wall("andesite"))
    d.set(6, 3, 6, "sea_lantern")
    d.set(0, 1, 6, "light_gray_concrete")


def seat_free(d, x, y, z, wood, back):
    """Bench seat on a plain piece (no sit tags)."""
    d.set(x, y, z, stairs(wood, back))


def hw_landing(d, M):
    # stone terrace: lych-gate over the way out (two dark-oak posts, little tiled roof, lantern), a bench looking
    # out over the drop, stone piers with a lantern and flower pots at the corners
    for x in (0, 4):
        for y in range(1, 4):
            d.set(x, y, 6, log("dark_oak_log"))
    for x in range(0, 5):
        d.set(x, 4, 5, stairs("deepslate_tile", "south"))
        d.set(x, 4, 6, stairs("deepslate_tile", "north"))
    d.set(2, 3, 5, HANGING)
    seat_free(d, 1, 1, 2, "dark_oak", "east")
    seat_free(d, 1, 1, 3, "dark_oak", "east")
    d.set(1, 1, 1, "potted_red_tulip")
    for (x, z) in ((0, 0), (6, 0), (6, 6), (5, 6)):
        d.set(x, 1, z, "stone_bricks")
    d.set(0, 2, 0, LANTERN)
    d.set(6, 2, 0, "potted_red_tulip")
    d.set(6, 2, 6, LANTERN)
    d.set(5, 2, 6, "potted_azure_bluet")


def cas_landing(d, M):
    # log lookout: lean-to roof over the west side on log posts, bench, lantern, trail sign
    for (x, z) in ((0, 0), (0, 5), (3, 0), (3, 5)):
        for y in range(1, 4):
            d.set(x, y, z, log("spruce_log"))
    for z in range(0, 6):                         # mono-pitch roof falling to the east
        d.set(0, 4, z, "spruce_planks")
        d.set(1, 4, z, stairs("spruce", "west"))
        d.set(2, 4, z, slab("spruce"))
        d.set(3, 4, z, slab("spruce"))
    seat_free(d, 1, 1, 2, "spruce", "east")
    seat_free(d, 1, 1, 3, "spruce", "east")
    d.set(1, 3, 1, HANGING)
    d.set(6, 1, 6, log("spruce_log"))
    d.set(6, 2, 6, LANTERN)
    post_sign(d, 5, 1, 6, 0, ["TRAIL", "<- Ridge", "Town v"], "spruce")
    d.set(1, 1, 4, "barrel[facing=up,open=false]")
