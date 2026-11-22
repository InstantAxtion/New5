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
  Cascadia   log-crib quays, river-rock bed, stripped-log coping with a rail fence, coarse-dirt towpath, lanterns
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
