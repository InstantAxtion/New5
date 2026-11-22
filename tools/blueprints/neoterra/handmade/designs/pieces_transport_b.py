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
        return dict(wall=wallb, walk="smooth_stone", edge="yellow_terracotta", floor="light_gray_concrete",
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
