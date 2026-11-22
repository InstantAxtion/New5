"""
Transport pieces A – rails, canals and bridges for Neoterra, Hearthwood and Cascadia, designed by hand.

RAILS (railstraight 5x5x8 anchor (2,1,0), railcorner 5x5x5 anchor (2,1,0), railstop 9x9x14 controller (6,2,13),
Neoterra railstop 9x8x16 controller (6,2,15)) – sizes and anchors unchanged.
  Cross-section: track on RAIL_X = 2 (railstop: x = 1), rail on RAIL_Y = 2 on a solid bed at y = 1 (ground layer).
  The straight runs along z (0..7); every straight has an always-on boost: powered rails at z = 3 and 4 with a
  redstone block in the bed under z = 3 (one boost every 8 blocks keeps carts at full speed, in both directions).
  The corner enters at the north edge (x = 2) and leaves at the east edge (z = 2) as a real curve: a diagonal of
  curve rails (2,1) NE -> (3,1) SW -> (3,2) NE, so a cart swings through instead of hitting a hard 90.
  Joining: corner anchor + (3, 0, 2) with 3 quarter turns gives the straight leaving east.
  The rail stop is a terminus: track along x = 1 into a buffer block at the south end; the last two rails are
  powered rails without power (they brake an arriving cart); a button on top of the buffer powers them and the cart
  departs north (it is pushed away from the buffer). Platform x 2..8 at y = 2 (stand on y = 3) with steps at the
  north end, shelter, 4 seats (sit_out), lighting, a name board and a "press to depart" sign.
  Neoterra   tram line on a green (grass) track bed with a concrete rail beam, light-gray curbs, flush in-ground
             lights, catenary masts with an overhead chain wire; stop = concrete platform, yellow safety edge, glass
             shelter with a cantilevered white roof and ceiling lights, glowing departure board, ticket machine,
             station totem, azalea planter.
  Hearthwood branch line: gravel ballast with stripped-spruce sleepers every other block, grass verges, black
             railway lamps, white mile posts; halt = brick platform with stone coping, timber-framed brick waiting
             wall with leaded windows, tiled lean-to canopy on cast-iron columns with a fretwork valance, nameboard
             on posts, hedge, flower bed, red buffer beam.
  Cascadia   logging railroad: spruce-log ties in gravel, coarse-dirt/podzol verges, log lamp posts, whistle post,
             boulders; flag stop = plank platform on log cribbing, log shed with a steep gable roof, freight
             barrels and hay, water cauldron, hanging station sign, log buffer.

CANALS (canalstraight 9x7x8, canalcorner / canalintersection 9x7x9, canallock 9x7x12; anchor (4,2,0)).
  SIZE CHANGE: sy 6 -> 7 and anchor y 1 -> 2 (gy 2) for the whole family in all packs, so the canal can be sunk one
  block below the towpath with a sealed bed (water at y = 1 on a bed at y = 0). The anchor is still the ground
  layer above the channel centre, as before.
  Cross-section index 0..8: 0 towpath, 1 coping (quay wall below), 2..6 water (5 wide), 7 coping, 8 towpath.
  Ground/towpath/coping at y = 2, water source blocks at y = 1 (all level 0), bed at y = 0, quay walls y 0..1.
  Corner: north edge -> east edge (corner anchor + (5, 0, 4), 3 turns, is the next straight).
  Intersection: four arms, four little hump footbridges (deck y = 4, two blocks of clearance over the water) join
  the towpath islands. Lock: lower reach z 0..5, closed lock gates (fence gates, which water cannot pass) at z = 5,
  sill step at z = 6, upper reach z 6..11 with its water ONE block higher (bed y 1, water y 2, towpath y 3): the
  next piece at the south end goes one block up (anchor + (0, 1, 12)). Balance beams, gate posts with paddle levers.
  Neoterra   concrete quays, cyan bed, smooth-stone coping with a glass balustrade, andesite towpath with flush
             lights, white/gray footbridges.
  Hearthwood brick quays, clay bed, stone-brick coping left open, dirt towpath, black lamps and bollards, brick
             hump bridges, white balance beams.
  Cascadia   log-crib quays, river-rock bed, river-rock kerb with a spruce rail fence, coarse-dirt towpath, lanterns
             on fence posts, log pilings, plank footbridges.

BRIDGE (bridgestart 7x8x10 anchor (3,0,0); bridgestraight 7x10x8 (Neoterra 7x8x8) anchor (3,0,0); bridgepillar
  7x20x7 anchor (3,19,3)) – sizes and anchors unchanged.
  Deck width 7: x 0 and 6 railing line, x 1..5 walkway; the straight's deck is ONE layer at the anchor level y = 0
  (stand on y = 1). The start ramps from bank level (z = 0) up RAMP_RISE = 4 in half-slab steps to deck height at
  z = 8..9: the first straight goes at start anchor + (0, 4, 10); straights join every 8. The pillar's anchor is the
  centre of its top layer, which lies at deck level and is all "keep" (it never cuts the deck); its body hangs
  below to the river bed – place it at a straight's anchor (the joint row). Everything in the pillar that is not
  masonry is "keep" too, so it never carves the abutment or removes river water.
  Neoterra   concrete deck with flush lights, glass balustrade with a slab handrail, light posts at the joints,
             glass ramp; slim pier with a hammerhead cap.
  Hearthwood stone bridge: cobbled walk between stone kerbs, stone parapets with slab coping, black lamps on the
             joints, newel piers at the bank; pier with pointed cutwaters, mossy waterline and corbelled haunches.
  Cascadia   covered timber bridge (Oregon style): log posts, plank walls with a window strip, trusses, lantern,
             steep shingle roof; plank approach on a log crib with rail fences; trestle bent pier on a rock footing.
"""
import json

from nbtlib import tag as T

from hm import Design, design, AIR, KEEP, SOLID

PACKS = ("Neoterra", "Hearthwood", "Cascadia")

# ---------------------------------------------------------------------------------------------- family constants
RAIL_X, RAIL_Y, BED_Y = 2, 2, 1          # railstraight / railcorner track position
STOP_RAIL_X = 1                           # railstop track column
POWER_Z = (3, 4)                          # powered rails in every straight (redstone block under the first)
CANAL_GY = 2                              # canal ground / towpath layer (water at CANAL_GY - 1, bed at 0)
CANAL_ROW = "TCWWWWWCT"                   # towpath, coping, 5 water, coping, towpath
LOCK_GATE_Z, LOCK_STEP = 5, 1             # lock gates row; upper reach is LOCK_STEP higher
RAMP = [(0, "F"), (1, "S"), (1, "F"), (2, "S"), (2, "F"), (3, "S"), (3, "F"), (4, "S"), (4, "F"), (4, "F")]
RAMP_RISE = 4                             # bridgestart deck height at its south end (= bridgestraight y 0)
PILLAR_TOP = 19                           # bridgepillar anchor layer (deck level)

WATER = "water[level=0]"
LANTERN = "lantern[hanging=false,waterlogged=false]"
HANGING = "lantern[hanging=true,waterlogged=false]"
GRASS = "grass_block[snowy=false]"
PODZOL = "podzol[snowy=false]"


# ---------------------------------------------------------------------------------------------- block states
def stairs(n, facing, half="bottom"):
    return f"{n}_stairs[facing={facing},half={half},shape=straight,waterlogged=false]"


def slab(n, t="bottom"):
    return f"{n}_slab[type={t},waterlogged=false]"


def wall(n, north="none", east="none", south="none", west="none", up=True):
    return (f"{n}_wall[east={east},north={north},south={south},up={'true' if up else 'false'},"
            f"waterlogged=false,west={west}]")


def log(n, axis="y"):
    return f"{n}[axis={axis}]"


def leaves(n):
    return f"{n}_leaves[distance=1,persistent=true,waterlogged=false]"


def gate(wood, facing="north", open_=False):
    return f"{wood}_fence_gate[facing={facing},in_wall=false,open={'true' if open_ else 'false'},powered=false]"


def rail(shape):
    return f"rail[shape={shape},waterlogged=false]"


def prail(powered, shape="north_south"):
    return f"powered_rail[powered={'true' if powered else 'false'},shape={shape},waterlogged=false]"


def button(kind="stone", face="floor", facing="north"):
    return f"{kind}_button[face={face},facing={facing},powered=false]"


def sign_te(lines, glow=False, color="black", hanging=False):
    msgs = [json.dumps({"text": t}) for t in (list(lines) + ["", "", "", ""])[:4]]
    side = T.Compound({"messages": T.List[T.String]([T.String(m) for m in msgs]), "color": T.String(color),
                       "has_glowing_text": T.Byte(1 if glow else 0)})
    return T.Compound({"id": T.String("minecraft:hanging_sign" if hanging else "minecraft:sign"),
                       "front_text": side, "back_text": T.Compound(dict(side)), "is_waxed": T.Byte(1)})


def wall_sign(d, x, y, z, facing, lines, wood, glow=False, color="black"):
    d.set(x, y, z, f"{wood}_wall_sign[facing={facing},waterlogged=false]", sign_te(lines, glow, color))


def post_sign(d, x, y, z, rotation, lines, wood):
    """Standing sign (rotation 0 = text to the south, 4 west, 8 north, 12 east)."""
    d.set(x, y, z, f"{wood}_sign[rotation={rotation},waterlogged=false]", sign_te(lines))


def hang_sign(d, x, y, z, rotation, lines, wood, glow=False, color="black"):
    """Ceiling hanging sign under the block above."""
    d.set(x, y, z, f"{wood}_hanging_sign[attached=false,rotation={rotation},waterlogged=false]",
          sign_te(lines, glow, color, hanging=True))


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


# ================================================================================================ RAILS
def rail_straight_track(d):
    """The working track of a straight: plain rails, two powered rails, redstone block under the first."""
    for z in range(8):
        d.set(RAIL_X, RAIL_Y, z, rail("north_south"))
    for z in POWER_Z:
        d.set(RAIL_X, RAIL_Y, z, prail(True))
    d.set(RAIL_X, BED_Y, POWER_Z[0], "redstone_block")


CORNER_PATH = [((2, 0), "north_south"), ((2, 1), "north_east"), ((3, 1), "south_west"), ((3, 2), "north_east"),
               ((4, 2), "east_west")]


def rail_corner_track(d):
    for (x, z), shape in CORNER_PATH:
        d.set(x, RAIL_Y, z, rail(shape))


@design("railstraight")
def railstraight(pack, rel, L):
    d = Design(pack, rel, (5, 5, 8), gy=1)
    if pack == "Neoterra":
        # green track: concrete rail beam in grass, light-gray curbs, flush lights in the curbs
        for z in range(8):
            plan(d, 1, ["LGSGL"], {"L": "light_gray_concrete", "G": GRASS, "S": "smooth_stone"}, z0=z)
        d.set(0, 1, 2, "sea_lantern")
        d.set(4, 1, 6, "sea_lantern")
        rail_straight_track(d)
        # catenary mast on the west curb with an arm to the overhead wire
        d.set(0, 2, 1, "polished_andesite")
        d.set(0, 3, 1, "iron_bars")
        d.set(0, 4, 1, "light_gray_concrete")
        d.set(1, 4, 1, "chain[axis=x,waterlogged=false]")
        for z in range(8):
            d.set(2, 4, z, "chain[axis=z,waterlogged=false]")
    elif pack == "Hearthwood":
        for z in range(8):
            if z % 2 == 0:       # sleeper rows
                plan(d, 1, ["GXXXG"], {"G": GRASS, "X": log("stripped_spruce_log", "x")}, z0=z)
            else:
                plan(d, 1, ["GgggG"], {"G": GRASS, "g": "gravel"}, z0=z)
        rail_straight_track(d)
        # black railway lamp on the west verge, white mile post on the east verge
        d.set(0, 2, 5, wall("polished_deepslate"))
        d.set(0, 3, 5, wall("polished_deepslate"))
        d.set(0, 4, 5, LANTERN)
        d.set(4, 2, 2, wall("diorite"))
        d.set(4, 3, 2, slab("smooth_stone"))
    else:
        for z in range(8):
            if z % 2 == 0:
                plan(d, 1, ["CTTTP"], {"C": "coarse_dirt", "P": PODZOL, "T": log("spruce_log", "x")}, z0=z)
            else:
                plan(d, 1, ["CgggP"], {"C": "coarse_dirt", "P": PODZOL, "g": "gravel"}, z0=z)
        rail_straight_track(d)
        # log lamp post on the west side, whistle post with a "W" board on the east side, a fern
        d.set(0, 2, 2, log("spruce_log"))
        d.set(0, 3, 2, "spruce_fence")
        d.set(0, 4, 2, LANTERN)
        d.set(4, 2, 5, log("stripped_spruce_log"))
        d.set(4, 3, 5, log("stripped_spruce_log"))
        wall_sign(d, 4, 3, 4, "north", ["", "W", "", ""], "spruce")
        d.set(4, 2, 7, "fern")
    d.anchor(2, 1, 0)
    return d


@design("railcorner")
def railcorner(pack, rel, L):
    d = Design(pack, rel, (5, 5, 5), gy=1)
    if pack == "Neoterra":
        plan(d, 1, ["LGSGL",
                    "LGSSG",
                    "LGGSS",
                    "LGGGG",
                    "LLLLL"], {"L": "light_gray_concrete", "G": GRASS, "S": "smooth_stone"})
        d.set(0, 1, 4, "sea_lantern")
        rail_corner_track(d)
        # mast on the inside of the curve, wire following the track
        d.set(4, 2, 0, "polished_andesite")
        d.set(4, 3, 0, "iron_bars")
        d.set(4, 4, 0, "light_gray_concrete")
        d.set(3, 4, 0, "chain[axis=x,waterlogged=false]")
        for (x, z), ax in (((2, 0), "z"), ((2, 1), "z"), ((3, 1), "x"), ((3, 2), "z"), ((4, 2), "x")):
            d.set(x, 4, z, f"chain[axis={ax},waterlogged=false]")
        # small planter of moss + azalea on the outside of the curve
        d.set(1, 2, 3, "moss_block")
        d.set(1, 3, 3, "azalea")
    elif pack == "Hearthwood":
        plan(d, 1, ["GXXXG",
                    "GggZg",
                    "GGgZg",
                    "GGGZg",
                    "GGGGG"], {"G": GRASS, "g": "gravel", "X": log("stripped_spruce_log", "x"),
                               "Z": log("stripped_spruce_log", "z")})
        rail_corner_track(d)
        d.set(0, 2, 4, wall("polished_deepslate"))
        d.set(0, 3, 4, wall("polished_deepslate"))
        d.set(0, 4, 4, LANTERN)
        d.set(1, 2, 3, leaves("oak"))          # clipped box bush on the outside of the curve
    else:
        plan(d, 1, ["CTTTP",
                    "CggTg",
                    "CCgTg",
                    "PCCTg",
                    "PPCCP"], {"C": "coarse_dirt", "P": PODZOL, "g": "gravel", "T": log("spruce_log", "x"),
                               "U": log("spruce_log", "z")})
        for z in (1, 2, 3):
            d.set(3, 1, z, log("spruce_log", "z"))
        rail_corner_track(d)
        # boulder and a fern on the outside of the curve
        d.set(0, 2, 4, "mossy_cobblestone")
        d.set(1, 2, 4, slab("mossy_cobblestone"))
        d.set(0, 2, 3, slab("cobblestone"))
        d.set(1, 2, 3, "fern")
    d.anchor(2, 1, 0)
    return d


# ------------------------------------------------------------------------------------------------ rail stop
def stop_track(d, length, bed_even, bed_odd, buffer_block, btn):
    """Terminus track along x = 1: rails, two unpowered powered rails before the buffer, button on the buffer."""
    end = length - 1
    for z in range(end):
        d.set(STOP_RAIL_X, 1, z, bed_even if z % 2 == 0 else bed_odd)
    for z in range(end - 2):
        d.set(STOP_RAIL_X, 2, z, rail("north_south"))
    d.set(STOP_RAIL_X, 2, end - 2, prail(False))
    d.set(STOP_RAIL_X, 2, end - 1, prail(False))
    d.set(STOP_RAIL_X, 2, end, buffer_block)
    d.set(STOP_RAIL_X, 3, end, btn)


@design("railstop")
def railstop(pack, rel, L):
    return {"Neoterra": neo_stop, "Hearthwood": hw_stop, "Cascadia": cas_stop}[pack](pack, rel)


def neo_stop(pack, rel):
    d = Design(pack, rel, (9, 8, 16), gy=1, paving="light_gray_concrete")
    # track bed: smooth-stone beam, grass verge
    for z in range(16):
        d.set(0, 1, z, GRASS)
    stop_track(d, 16, "smooth_stone", "smooth_stone", "yellow_concrete", button("stone"))
    d.set(1, 1, 15, "light_gray_concrete")
    # platform x 2..8, z 2..15: yellow safety edge, tactile strip, diorite paving
    for z in range(2, 16):
        plan(d, 2, ["YTDDDDD"], {"Y": "yellow_concrete", "T": "smooth_stone", "D": "polished_diorite"}, x0=2, z0=z)
    # entrance at the north end: a half-step ramp, azalea planter
    for x in range(3, 8):
        d.set(x, 2, 1, slab("smooth_stone"))
    d.set(8, 2, 0, "moss_block")
    d.set(8, 2, 1, "moss_block")
    d.set(8, 3, 0, "azalea")
    d.set(8, 3, 1, "flowering_azalea")
    # glass shelter: back wall of panes between concrete posts, cantilevered flat roof with ceiling lights
    for y in range(3, 6):
        d.set(8, y, 5, "light_gray_concrete")
        d.set(8, y, 14, "light_gray_concrete")
        for z in range(6, 14):
            d.set(8, y, z, "glass_pane")
    for z in range(5, 15):
        for x in range(3, 9):
            d.set(x, 6, z, "white_concrete")
            d.set(x, 7, z, slab("smooth_stone"))
        d.set(3, 6, z, "cyan_terracotta")          # fascia stripe along the front edge
    d.set(5, 6, 8, "sea_lantern")
    d.set(5, 6, 11, "sea_lantern")
    # benches (birch, backs to the glass) and the departure board between them
    for z in (7, 8, 11, 12):
        seat(d, 7, 3, z, "birch", "east")
    d.set(8, 4, 9, "black_concrete")
    d.set(8, 4, 10, "black_concrete")
    wall_sign(d, 7, 4, 9, "west", ["NEXT TRAM", "", "Central", "2 min"], "birch", glow=True, color="cyan")
    wall_sign(d, 7, 4, 10, "west", ["THEN", "", "Harbour", "9 min"], "birch", glow=True, color="cyan")
    d.set(7, 3, 10, "cauldron")                  # litter bin
    # ticket machine at the entrance
    d.set(8, 3, 3, "light_gray_concrete")
    d.set(8, 4, 3, "light_blue_stained_glass")
    d.set(7, 4, 3, button("stone", "wall", "west"))
    wall_sign(d, 7, 3, 3, "west", ["TICKETS", "tap here", "", ""], "birch")
    # station totem with glowing name
    d.set(4, 3, 4, "white_concrete")
    d.set(4, 4, 4, "cyan_concrete")
    d.set(4, 5, 4, "white_concrete")
    wall_sign(d, 3, 4, 4, "west", ["NEOTERRA", "CENTRAL", "", "tram stop"], "birch", glow=True, color="white")
    wall_sign(d, 5, 4, 4, "east", ["NEOTERRA", "CENTRAL", "", "tram stop"], "birch", glow=True, color="white")
    # column light at the north end of the platform
    d.set(6, 3, 2, "polished_andesite")
    d.set(6, 4, 2, "iron_bars")
    d.set(6, 5, 2, "iron_bars")
    d.set(6, 6, 2, "sea_lantern")
    d.set(6, 7, 2, slab("smooth_stone"))
    # depart sign beside the buffer button
    post_sign(d, 2, 3, 15, 8, ["To depart", "press the", "button on", "the buffer"], "birch")
    d.hut(6, 2, 15)
    return d


def hw_stop(pack, rel):
    d = Design(pack, rel, (9, 9, 14), gy=1)
    for z in range(14):
        d.set(0, 1, z, GRASS)
    stop_track(d, 14, log("stripped_spruce_log", "x"), "gravel", "red_terracotta", button("stone"))
    d.set(1, 1, 13, "stone_bricks")
    # brick platform with a white stone coping edge
    for z in range(2, 14):
        plan(d, 1, ["BBBBBBB"], {"B": "bricks"}, x0=2, z0=z)
        plan(d, 2, ["CBBBBBB"], {"C": "smooth_stone", "B": "bricks"}, x0=2, z0=z)
    for x in range(3, 8):
        d.set(x, 2, 1, stairs("brick", "south"))
    d.set(8, 2, 1, "bricks")
    d.set(8, 2, 0, "bricks")
    d.set(8, 3, 1, "bricks")
    # flower bed at the entrance beside a brick pier with a pot
    d.set(8, 2, 0, GRASS)
    d.set(8, 3, 0, "red_tulip")
    d.set(8, 4, 1, "potted_red_tulip")
    # box hedge along the far verge
    for z in range(5, 12):
        d.set(0, 2, z, leaves("oak"))
    # waiting wall: timber posts, brick infill, leaded windows
    for y in range(3, 6):
        for z in range(5, 13):
            d.set(8, y, z, "bricks")
        d.set(8, y, 5, log("stripped_dark_oak_log"))
        d.set(8, y, 12, log("stripped_dark_oak_log"))
    for z in (6, 7, 10, 11):
        d.set(8, 4, z, "glass_pane")
    d.set(8, 5, 8, log("stripped_dark_oak_log", "z"))
    d.set(8, 5, 9, log("stripped_dark_oak_log", "z"))
    # canopy: cast-iron columns, fretwork valance, plank ceiling, tiled lean-to roof (z 4..13)
    for z in (5, 9, 12):
        for y in range(3, 6):
            d.set(3, y, z, wall("polished_deepslate"))
    for z in (6, 7, 8, 10, 11):
        d.set(3, 5, z, "dark_oak_fence")
    for z in range(4, 14):
        d.set(3, 6, z, stairs("deepslate_tile", "east"))
        for x in range(4, 9):
            d.set(x, 6, z, "dark_oak_planks")
        d.set(4, 7, z, stairs("deepslate_tile", "east"))
        for x in range(5, 9):
            d.set(x, 7, z, "deepslate_tiles")
        d.set(5, 8, z, stairs("deepslate_tile", "east"))
        for x in range(6, 9):
            d.set(x, 8, z, slab("deepslate_tile"))
    d.set(5, 5, 7, HANGING)
    d.set(5, 5, 10, HANGING)
    # benches against the waiting wall, bin between them, timetable + notice on the wall
    for z in (6, 7, 10, 11):
        seat(d, 7, 3, z, "dark_oak", "east")
    d.set(7, 3, 8, "potted_red_tulip")
    d.set(7, 3, 9, "cauldron")
    wall_sign(d, 7, 4, 8, "west", ["TIMETABLE", "Up: :00 :30", "Down: :15", ":45"], "dark_oak")
    wall_sign(d, 7, 4, 9, "west", ["Passengers", "must cross", "by the steps", "only"], "dark_oak")
    # nameboard on two posts, readable from the train and from the platform
    d.set(5, 3, 2, "dark_oak_fence")
    d.set(5, 3, 4, "dark_oak_fence")
    for z in (2, 3, 4):
        d.set(5, 4, z, "dark_oak_planks")
        d.set(5, 5, z, slab("dark_oak"))
    for z, txt in ((2, "HEARTH-"), (3, "WOOD"), (4, "HALT")):
        wall_sign(d, 4, 4, z, "west", ["", txt, "", ""], "dark_oak")
    for z, txt in ((4, "HEARTH-"), (3, "WOOD"), (2, "HALT")):
        wall_sign(d, 6, 4, z, "east", ["", txt, "", ""], "dark_oak")
    # railway lamp at the platform end
    d.set(7, 3, 2, wall("polished_deepslate"))
    d.set(7, 4, 2, wall("polished_deepslate"))
    d.set(7, 5, 2, LANTERN)
    post_sign(d, 2, 3, 13, 8, ["To depart", "press the", "button on", "the buffer"], "dark_oak")
    d.hut(6, 2, 13)
    return d


def cas_stop(pack, rel):
    d = Design(pack, rel, (9, 9, 14), gy=1, paving="coarse_dirt")
    stop_track(d, 14, log("spruce_log", "x"), "gravel", log("spruce_log", "x"), button("spruce"))
    d.set(1, 1, 13, "cobblestone")
    # plank platform on log cribbing
    for z in range(2, 14):
        plan(d, 1, ["LCCCCCC"], {"L": log("spruce_log", "z"), "C": "cobblestone"}, x0=2, z0=z)
        plan(d, 2, ["EPPPPPP"], {"E": log("stripped_spruce_log", "z"), "P": "spruce_planks"}, x0=2, z0=z)
    for x in range(3, 8):
        d.set(x, 2, 1, stairs("spruce", "south"))
    # rail fence along the far verge, ferns
    for z in range(2, 13):
        d.set(0, 2, z, "spruce_fence")
    d.set(0, 2, 0, "fern")
    d.set(8, 2, 0, "fern")
    # log shed (z 8..13): back wall of horizontal logs, south wall, corner posts, steep gable roof
    for y in range(3, 6):
        for z in range(8, 14):
            d.set(8, y, z, log("spruce_log", "z"))
        for x in range(4, 8):
            d.set(x, y, 13, log("spruce_log", "x"))
        d.set(8, y, 8, log("spruce_log"))
        d.set(8, y, 13, log("spruce_log"))
        d.set(3, y, 8, log("spruce_log"))
        d.set(3, y, 13, log("spruce_log"))
    d.set(8, 4, 10, "glass_pane")
    for z in range(7, 14):
        d.set(3, 6, z, stairs("spruce", "east"))
        d.set(8, 6, z, stairs("spruce", "west"))
        d.set(4, 7, z, stairs("spruce", "east"))
        d.set(7, 7, z, stairs("spruce", "west"))
        d.set(5, 8, z, stairs("spruce", "east"))
        d.set(6, 8, z, stairs("spruce", "west"))
    for z in (8, 13):
        for x in range(4, 8):
            d.set(x, 6, z, log("stripped_spruce_log", "x"))     # tie beams
    for x in (5, 6):
        d.set(x, 7, 13, "spruce_planks")                       # south gable
    # benches inside the shed
    for z in (9, 10, 11):
        seat(d, 7, 3, z, "spruce", "east")
    seat(d, 5, 3, 12, "spruce", "south")
    d.set(5, 7, 10, HANGING)
    hang_sign(d, 5, 5, 8, 4, ["CASCADIA", "FLAG STOP", "", "est. 1889"], "spruce")
    # freight corner: barrels, hay, water cauldron
    d.set(8, 3, 4, "hay_block[axis=y]")
    d.set(8, 3, 5, "barrel[facing=up,open=false]")
    d.set(8, 3, 6, "barrel[facing=west,open=false]")
    d.set(8, 4, 5, "barrel[facing=up,open=false]")
    d.set(8, 3, 7, "water_cauldron[level=3]")
    # log lamp post at the platform head
    d.set(7, 3, 2, log("spruce_log"))
    d.set(7, 4, 2, log("spruce_log"))
    d.set(7, 5, 2, "spruce_fence")
    d.set(7, 6, 2, LANTERN)
    post_sign(d, 2, 3, 13, 8, ["To depart", "press the", "button on", "the buffer"], "spruce")
    d.hut(6, 2, 13)
    return d


# ================================================================================================ CANALS
CANAL_STYLE = {
    #            quay wall              bed                  coping                     towpath
    "Neoterra": ("light_gray_concrete", "cyan_terracotta", "smooth_stone", "polished_andesite"),
    "Hearthwood": ("bricks", "clay", "stone_bricks", "dirt_path"),
    "Cascadia": (log("spruce_log", "z"), None, None, "coarse_dirt"),
}
RIVER_ROCK = ("cobblestone", "mossy_cobblestone", "andesite", "cobblestone", "tuff")


def canal_rows(d, rows, z0=0, y=CANAL_GY):
    """Lay the channel from a hand-drawn map (T towpath, C coping/quay, W water): bed at y-2, water at y-1, the
    ground layer at y. Cascadia's quays are log cribs (logs laid along the bank) under a river-rock kerb, on a
    river-rock bed."""
    quay, bed, coping, tow = CANAL_STYLE[d.pack]
    for dz, row in enumerate(rows):
        z = z0 + dz
        for x, ch in enumerate(row):
            if d.pack == "Cascadia":
                along_z = 0 < x < 8 and (row[x - 1] == "W" or row[x + 1] == "W") if ch == "C" else False
                along_x = (0 < dz < len(rows) - 1 and (rows[dz - 1][x] == "W" or rows[dz + 1][x] == "W")
                           if ch == "C" else False)
                ax = "y" if along_z and along_x else ("z" if along_z else "x")
                quay = log("spruce_log", ax)
                coping = "mossy_cobblestone" if (x * 5 + z * 3) % 4 == 0 else "cobblestone"   # river-rock kerb
                bed = RIVER_ROCK[(x * 3 + z * 7) % len(RIVER_ROCK)]
            if ch == "T":
                d.set(x, y, z, tow)
            elif ch == "C":
                for yy in range(y - 2, y):
                    d.set(x, yy, z, quay)
                d.set(x, y, z, coping)
            elif ch == "W":
                d.set(x, y - 2, z, bed)
                d.set(x, y - 1, z, WATER)
                d.set(x, y, z, AIR)


def railing(d, cells, y):
    """Neoterra glass balustrade / Cascadia rail fence on the listed coping cells."""
    blk = {"Neoterra": "glass_pane", "Cascadia": "spruce_fence"}.get(d.pack)
    if blk:
        for x, z in cells:
            d.set(x, y, z, blk)


def neo_canal_light(d, x, z, y=3, bars=2):
    """Slim column light: andesite foot, bar shaft, sea-lantern head."""
    d.set(x, y, z, "polished_andesite")
    for k in range(bars):
        d.set(x, y + 1 + k, z, "iron_bars")
    d.set(x, y + 1 + bars, z, "sea_lantern")


def hw_lamp(d, x, z, y=3):
    d.set(x, y, z, wall("polished_deepslate"))
    d.set(x, y + 1, z, wall("polished_deepslate"))
    d.set(x, y + 2, z, LANTERN)


@design("canalstraight")
def canalstraight(pack, rel, L):
    d = Design(pack, rel, (9, 7, 8), gy=CANAL_GY)
    canal_rows(d, [CANAL_ROW] * 8)
    if pack == "Neoterra":
        railing(d, [(x, z) for x in (1, 7) for z in range(8) if (x, z) != (7, 4)], 3)
        neo_canal_light(d, 7, 4)
        d.set(0, 2, 3, "sea_lantern")            # flush towpath lights
        d.set(8, 2, 7, "sea_lantern")
    elif pack == "Hearthwood":
        hw_lamp(d, 1, 2)
        d.set(7, 3, 1, wall("deepslate_tile"))   # mooring bollards
        d.set(7, 3, 5, wall("deepslate_tile"))
        d.set(1, 3, 6, wall("diorite"))          # white mile post
        d.set(1, 4, 6, slab("smooth_stone"))
        d.set(8, 3, 3, "short_grass")
    else:
        railing(d, [(x, z) for x in (1, 7) for z in range(8) if (x, z) != (7, 5)], 3)
        d.set(1, 4, 3, LANTERN)                  # lantern on a fence post
        d.set(7, 3, 5, log("spruce_log"))        # mooring piling
        d.set(7, 4, 5, log("spruce_log"))
        d.set(0, 3, 6, "fern")
    d.anchor(4, CANAL_GY, 0)
    return d


CORNER_MAP = ["TCWWWWWCT",
              "TCWWWWWCC",
              "TCWWWWWWW",
              "TCWWWWWWW",
              "TCWWWWWWW",
              "TCWWWWWWW",
              "TCCWWWWWW",
              "TCCCCCCCC",
              "TTTTTTTTT"]


@design("canalcorner")
def canalcorner(pack, rel, L):
    d = Design(pack, rel, (9, 7, 9), gy=CANAL_GY)
    canal_rows(d, CORNER_MAP)
    outer = [(1, z) for z in range(7)] + [(2, 6)] + [(x, 7) for x in range(1, 9)]
    inner = [(7, 0), (7, 1), (8, 1)]
    if pack == "Neoterra":
        railing(d, [c for c in outer + inner if c != (1, 7)], 3)
        neo_canal_light(d, 1, 7)
        d.set(0, 2, 2, "sea_lantern")
        d.set(5, 2, 8, "sea_lantern")
    elif pack == "Hearthwood":
        hw_lamp(d, 1, 7)
        d.set(7, 3, 1, wall("deepslate_tile"))
        d.set(1, 3, 2, wall("deepslate_tile"))
        d.set(6, 3, 7, wall("deepslate_tile"))
    else:
        railing(d, outer + inner, 3)
        d.set(1, 4, 7, LANTERN)
        d.set(8, 4, 1, LANTERN)
        d.set(0, 3, 8, "fern")
    d.anchor(4, CANAL_GY, 0)
    return d


CROSS_MAP = ["TCWWWWWCT",
             "CCWWWWWCC",
             "WWWWWWWWW",
             "WWWWWWWWW",
             "WWWWWWWWW",
             "WWWWWWWWW",
             "WWWWWWWWW",
             "CCWWWWWCC",
             "TCWWWWWCT"]

FOOTBRIDGE = {"Neoterra": ("polished_diorite", "polished_diorite"), "Hearthwood": ("brick", "bricks"),
              "Cascadia": ("spruce", "spruce_planks")}


def footbridge(d, cells, up, down):
    """Hump footbridge over one arm: cells = the 7 cells from island to island; deck at y 4 over the 3 middle
    water cells, stairs up at both ends, arch springers under the first and last water cells."""
    st, deck = FOOTBRIDGE[d.pack]
    (a, b, c, e, f, g, h) = cells
    d.set(a[0], 3, a[1], stairs(st, up))
    d.set(b[0], 4, b[1], stairs(st, up))
    for x, z in (c, e, f):
        d.set(x, 4, z, deck)
    d.set(g[0], 4, g[1], stairs(st, down))
    d.set(h[0], 3, h[1], stairs(st, down))
    d.set(b[0], 3, b[1], stairs(st, down, "top"))
    d.set(g[0], 3, g[1], stairs(st, up, "top"))


@design("canalintersection")
def canalintersection(pack, rel, L):
    d = Design(pack, rel, (9, 7, 9), gy=CANAL_GY)
    canal_rows(d, CROSS_MAP)
    footbridge(d, [(x, 0) for x in range(1, 8)], "east", "west")      # north arm
    footbridge(d, [(x, 8) for x in range(1, 8)], "east", "west")      # south arm
    footbridge(d, [(0, z) for z in range(1, 8)], "south", "north")    # west arm
    footbridge(d, [(8, z) for z in range(1, 8)], "south", "north")    # east arm
    if pack == "Neoterra":
        neo_canal_light(d, 1, 1)
        neo_canal_light(d, 7, 7)
        for x, z in ((7, 1), (1, 7)):
            d.set(x, 3, z, "moss_block")
            d.set(x, 4, z, "azalea")
        for x, z in ((0, 0), (8, 8)):
            d.set(x, 2, z, "sea_lantern")
    elif pack == "Hearthwood":
        hw_lamp(d, 1, 1)
        hw_lamp(d, 7, 7)
        d.set(7, 3, 1, wall("deepslate_tile"))
        d.set(1, 3, 7, wall("deepslate_tile"))
    else:
        for x, z in ((1, 1), (7, 7)):
            d.set(x, 3, z, log("spruce_log"))
            d.set(x, 4, z, log("spruce_log"))
            d.set(x, 5, z, LANTERN)
        for x, z in ((7, 1), (1, 7)):
            d.set(x, 3, z, log("spruce_log"))
    d.anchor(4, CANAL_GY, 0)
    return d


LOCK_WOOD = {"Neoterra": "mangrove", "Hearthwood": "dark_oak", "Cascadia": "spruce"}


@design("canallock")
def canallock(pack, rel, L):
    d = Design(pack, rel, (9, 7, 12), gy=CANAL_GY)
    quay, bed, coping, tow = CANAL_STYLE[pack]
    g = LOCK_GATE_Z
    canal_rows(d, [CANAL_ROW] * (g + 1))                         # lower reach z 0..5
    canal_rows(d, [CANAL_ROW] * (11 - g), z0=g + 1, y=CANAL_GY + LOCK_STEP)   # upper reach, one higher
    for z in range(g + 1, 12):
        for x in (0, 8):
            d.set(x, CANAL_GY, z, SOLID)                         # raised towpath sits on ground fill
        for x in range(2, 7):
            d.set(x, 0, z, d.get(x, 1, z))                       # bed under the raised bed (sill / step)
    # towpath steps up at the sill
    step = {"Neoterra": "polished_andesite", "Hearthwood": "cobblestone", "Cascadia": "spruce"}[pack]
    for x in (0, 8):
        d.set(x, 3, g + 1, stairs(step, "south"))
    # the lock gates: a closed row of fence gates holding back the upper water
    for x in range(2, 7):
        d.set(x, 2, g, gate(LOCK_WOOD[pack]))
    post = {"Neoterra": "light_gray_concrete", "Hearthwood": log("stripped_dark_oak_log"),
            "Cascadia": log("spruce_log")}[pack]
    for x in (1, 7):
        d.set(x, 3, g, post)
        d.set(x, 4, g, "lever[face=floor,facing=north,powered=false]")   # paddle gear
    wall_sign(d, 0, 3, g, "west", ["LOCK No. 1", "keep gates", "closed", ""], LOCK_WOOD[pack])
    if pack == "Neoterra":
        railing(d, [(x, z) for x in (1, 7) for z in range(g)], 3)
        railing(d, [(x, z) for x in (1, 7) for z in range(g + 1, 12) if (x, z) != (7, 9)], 4)
        neo_canal_light(d, 7, 9, y=4, bars=1)
        d.set(8, 2, 2, "sea_lantern")
        d.set(0, 3, 9, "sea_lantern")
    else:
        beam = log("stripped_birch_log" if pack == "Hearthwood" else "stripped_spruce_log", "z")
        for x in (1, 7):
            for z in range(g - 3, g):
                d.set(x, 3, z, beam)                              # balance beams, swung parallel to the bank
        if pack == "Hearthwood":
            hw_lamp(d, 1, 9, y=4)
            d.set(7, 3, 1, wall("deepslate_tile"))
            d.set(7, 4, 10, wall("deepslate_tile"))
        else:
            railing(d, [(x, z) for x in (1, 7) for z in range(g - 3)], 3)
            railing(d, [(x, z) for x in (1, 7) for z in range(g + 1, 12)], 4)
            d.set(7, 5, 9, LANTERN)
            d.set(1, 5, 9, LANTERN)
    d.anchor(4, CANAL_GY, 0)
    return d


# ================================================================================================ BRIDGE
@design("bridgestraight")
def bridgestraight(pack, rel, L):
    if pack == "Neoterra":
        d = Design(pack, rel, (7, 8, 8), gy=0, paving="smooth_stone")
        for z in range(8):
            plan(d, 0, ["ASSLSSA"], {"A": "polished_andesite", "S": "smooth_stone", "L": "light_gray_concrete"},
                 z0=z)
            for x in (0, 6):
                post = z in (0, 4)
                d.set(x, 1, z, "polished_andesite" if post else "glass_pane")
                d.set(x, 2, z, "polished_andesite" if z == 0 else slab("smooth_stone"))
        d.set(1, 0, 2, "sea_lantern")            # flush deck lights
        d.set(5, 0, 6, "sea_lantern")
        d.set(0, 3, 0, "end_rod[facing=up]")
        d.set(6, 3, 0, "end_rod[facing=up]")
    elif pack == "Hearthwood":
        d = Design(pack, rel, (7, 10, 8), gy=0, paving="cobblestone")
        for z in range(8):
            plan(d, 0, ["KKcccKK"], {"K": "stone_bricks", "c": "cobblestone"}, z0=z)
            for x in (0, 6):
                d.set(x, 1, z, "stone_bricks")
                d.set(x, 2, z, slab("stone_brick"))
        d.set(2, 0, 5, "mossy_cobblestone")
        d.set(4, 0, 2, "mossy_cobblestone")
        # lamps on the parapet, staggered: west on the joint, east mid-span
        for x, z in ((0, 0), (6, 4)):
            d.set(x, 1, z, "chiseled_stone_bricks")
            d.set(x, 2, z, wall("polished_deepslate"))
            d.set(x, 3, z, wall("polished_deepslate"))
            d.set(x, 4, z, LANTERN)
    else:
        d = Design(pack, rel, (7, 10, 8), gy=0, paving="spruce_planks")
        for z in range(8):
            plan(d, 0, ["EPPPPPE"], {"E": log("stripped_spruce_log", "z"), "P": "spruce_planks"}, z0=z)
            for x in (0, 6):
                if z in (0, 4):
                    for y in (1, 2, 3):
                        d.set(x, y, z, log("spruce_log"))       # wall posts
                else:
                    d.set(x, 1, z, "spruce_planks")              # kick board
                    d.set(x, 2, z, "spruce_fence")               # window strip
                    d.set(x, 3, z, log("stripped_spruce_log", "z"))   # top plate
            # roof: steep gable over the whole width (shingled dark by the Cascadia roof pass)
            d.set(0, 4, z, stairs("spruce", "east"))
            d.set(6, 4, z, stairs("spruce", "west"))
            d.set(1, 5, z, stairs("spruce", "east"))
            d.set(5, 5, z, stairs("spruce", "west"))
            d.set(2, 6, z, stairs("spruce", "east"))
            d.set(4, 6, z, stairs("spruce", "west"))
            d.set(3, 6, z, "spruce_planks")
            d.set(3, 7, z, slab("spruce"))
        for z in (0, 4):                                         # trusses: tie beam and king post
            for x in range(1, 6):
                d.set(x, 4, z, log("stripped_spruce_log", "x"))
            d.set(3, 5, z, "spruce_fence")
        d.set(3, 3, 4, HANGING)
    d.anchor(3, 0, 0)
    return d


@design("bridgestart")
def bridgestart(pack, rel, L):
    d = Design(pack, rel, (7, 8, 10), gy=0, paving=SOLID)
    for z, (t, kind) in enumerate(RAMP):
        for x in range(1, 6):
            for y in range(0, t):
                d.set(x, y, z, SOLID)                            # embankment fill
        if pack == "Neoterra":
            walk = {"F": "light_gray_concrete" , "S": slab("smooth_stone")}
            for x in range(1, 6):
                d.set(x, t, z, walk[kind] if x == 3 else ("smooth_stone" if kind == "F" else slab("smooth_stone")))
            for x in (0, 6):
                for y in range(0, t):
                    d.set(x, y, z, "light_gray_concrete")
                d.set(x, t, z, "polished_andesite")
                d.set(x, t + 1, z, "glass_pane")
                d.set(x, t + 2, z, slab("smooth_stone"))
        elif pack == "Hearthwood":
            for x in range(1, 6):
                kerb = x in (1, 5)
                if kind == "F":
                    d.set(x, t, z, "stone_bricks" if kerb else "cobblestone")
                else:
                    d.set(x, t, z, slab("stone_brick") if kerb else slab("cobblestone"))
            for x in (0, 6):
                for y in range(0, t + 2):
                    d.set(x, y, z, "stone_bricks")
                d.set(x, t + 2, z, slab("stone_brick"))
        else:
            for x in range(1, 6):
                d.set(x, t, z, "spruce_planks" if kind == "F" else slab("spruce"))
            for x in (0, 6):
                d.set(x, 0, z, "cobblestone")
                for y in range(1, t + 1):
                    d.set(x, y, z, log("spruce_log", "z"))
                d.set(x, t + 1, z, "spruce_fence")
    # river face of the abutment (below the deck at z = 9)
    face = {"Neoterra": "light_gray_concrete", "Hearthwood": "stone_bricks", "Cascadia": log("spruce_log", "x")}[pack]
    for x in range(7):
        for y in range(0, RAMP_RISE):
            d.set(x, y, 9, "cobblestone" if pack == "Cascadia" and y == 0 else face)
    # bank-end features
    if pack == "Neoterra":
        for x in (0, 6):
            d.set(x, 1, 0, "polished_andesite")
            d.set(x, 2, 0, "sea_lantern")            # light bollards
            d.set(x, 3, 0, slab("smooth_stone"))
        for x in (0, 6):
            d.set(x, RAMP_RISE + 1, 8, "polished_andesite")    # post where the glass meets the bridge
    elif pack == "Hearthwood":
        for x in (0, 6):
            d.set(x, 1, 0, "stone_bricks")
            d.set(x, 2, 0, "chiseled_stone_bricks")
            d.set(x, 3, 0, wall("polished_deepslate"))
            d.set(x, 4, 0, wall("polished_deepslate"))
            d.set(x, 5, 0, LANTERN)
    else:
        for x in (0, 6):
            for y in (1, 2, 3):
                d.set(x, y, 0, log("spruce_log"))
        for x in range(7):
            d.set(x, 4, 0, log("spruce_log", "x"))               # portal beam over the entrance
        d.set(1, 3, 0, HANGING)
        d.set(5, 3, 0, HANGING)
        hang_sign(d, 3, 3, 0, 0, ["CASCADIA", "COVERED", "BRIDGE", "walk horses"], "spruce")
    d.anchor(3, 0, 0)
    return d


@design("bridgepillar")
def bridgepillar(pack, rel, L):
    d = Design(pack, rel, (7, 20, 7), gy=0, paving=KEEP)
    d.fill(0, 0, 0, 6, PILLAR_TOP, 6, KEEP)          # never cut the deck, the abutment or the river
    top = PILLAR_TOP - 1                              # y 18: directly under the deck
    if pack == "Neoterra":
        d.fill(1, 0, 1, 5, 0, 5, "stone")
        d.fill(1, 1, 1, 5, 1, 5, "polished_andesite")
        d.fill(2, 2, 2, 4, top - 3, 4, "light_gray_concrete")
        d.fill(2, 11, 2, 4, 11, 4, "cyan_terracotta")            # accent band
        d.fill(1, top - 2, 2, 5, top - 2, 4, "white_concrete")
        d.set(0, top - 2, 3, stairs("polished_diorite", "east", "top"))
        d.set(6, top - 2, 3, stairs("polished_diorite", "west", "top"))
        d.fill(0, top - 1, 2, 6, top - 1, 4, "white_concrete")
        d.fill(0, top, 1, 6, top, 5, "white_concrete")            # hammerhead cap under the deck
        for z in (1, 5):
            d.set(0, top - 1, z, stairs("polished_diorite", "south" if z == 1 else "north", "top"))
            d.set(6, top - 1, z, stairs("polished_diorite", "south" if z == 1 else "north", "top"))
    elif pack == "Hearthwood":
        d.fill(0, 0, 1, 6, 1, 5, "stone")                          # footing on the river bed
        for y in range(2, 15):
            blk = "mossy_stone_bricks" if y <= 4 else "stone_bricks"
            d.fill(1, y, 2, 5, y, 4, blk)
            if y <= 12:
                d.set(0, y, 3, blk)                                # pointed cutwaters
                d.set(6, y, 3, blk)
        d.set(0, 13, 3, stairs("stone_brick", "east"))
        d.set(6, 13, 3, stairs("stone_brick", "west"))
        d.fill(0, 14, 2, 6, 14, 4, "chiseled_stone_bricks")        # string course
        # corbelled haunches widening to the full deck under the joint
        d.fill(0, 15, 2, 6, 15, 4, "stone_bricks")
        for x in range(7):
            d.set(x, 15, 1, stairs("stone_brick", "south", "top"))
            d.set(x, 15, 5, stairs("stone_brick", "north", "top"))
            d.set(x, 16, 0, stairs("stone_brick", "south", "top"))
            d.set(x, 16, 6, stairs("stone_brick", "north", "top"))
        d.fill(0, 16, 1, 6, 16, 5, "stone_bricks")
        d.fill(0, 17, 0, 6, top, 6, "stone_bricks")
    else:
        plan(d, 0, ["mcAcmcA",
                    "cmcAccm",
                    "AccmcAc",
                    "cAcmcmc",
                    "mccAcmc"], {"m": "mossy_cobblestone", "c": "cobblestone", "A": "andesite"}, z0=1)
        d.fill(0, 1, 2, 6, 1, 4, "cobblestone")
        d.set(0, 1, 3, "mossy_cobblestone")
        d.set(5, 1, 2, "mossy_cobblestone")
        d.fill(1, 2, 3, 5, 2, 3, "mossy_cobblestone")
        for x in (1, 3, 5):                                         # trestle bent: three log posts
            d.fill(x, 3, 3, x, top - 1, 3, log("spruce_log"))
        for y in (8, 13):                                           # girts
            d.fill(0, y, 3, 6, y, 3, log("stripped_spruce_log", "x"))
        for x, ys in ((2, (4, 5, 10, 15)), (4, (6, 7, 11, 16))):  # lattice of fence braces between the posts
            for y in ys:
                d.set(x, y, 3, "spruce_fence")
        d.fill(0, top, 3, 6, top, 3, log("spruce_log", "x"))       # cap beam
        for x in (1, 5):                                            # stringers under the deck
            for z in range(7):
                if z != 3:
                    d.set(x, top, z, log("spruce_log", "z"))
            d.set(x, top - 1, 2, "spruce_fence")
            d.set(x, top - 1, 4, "spruce_fence")
    d.anchor(3, PILLAR_TOP, 3)
    return d
