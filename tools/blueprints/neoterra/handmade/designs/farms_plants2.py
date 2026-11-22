"""
Farmworks plant farms, part 2 (decorations/cropfarms/): moss, glow lichen, glow berries, dripstone, mushrooms,
sea pickles, chorus. Java 1.21.1 vanilla mechanics only, every rule below checked against the 1.21.1 source.

Redstone conventions (Java block states):
  observer   facing = the side it WATCHES; it pulses (2 gt) out of its back (the opposite side).
  piston     facing = the push direction, extended=false.
  repeater / comparator   facing = the side the INPUT comes from (DiodeBlock reads pos.relative(facing));
             the output leaves on the opposite side. delay=4 is 4 redstone ticks = 8 game ticks.
  dispenser  facing = the side it shoots / uses its item into.   hopper facing = output side (never up).
  redstone dust powers the block under it (and the block it points at); a block powered by dust activates a
  piston / dispenser next to it (but no other dust). Dust may sit on glass (not a conductor) and on hoppers.
  wall torch facing = away from the block it hangs on; it powers the block ABOVE it and the dust next to it.

Clocks used:
  * torch clock (the one from the chicken cooker): block B, a redstone torch on B, dust + repeaters back into B.
    B is powered for 2 + 8*(k+1) game ticks, then unpowered for as long (k repeaters on the long side). It starts
    by itself when the blocks are placed and never burns out (it toggles far less than 8 times in 60 ticks).
  * hopper clock (the classic two-hopper clock): hoppers A -> B and B -> A, a comparator out of each, boosted by a
    repeater, locks the OTHER hopper (dust/repeater pointing into it). The items wander A -> B -> A, 8 ticks each,
    so every half period is 8 * (number of items) game ticks. Used where the cycle must be minutes long.

Push reactions (1.21.1 Blocks.java): moss carpet, azalea, flowering azalea, short grass, cave vines, glow lichen,
pointed dripstone, mushrooms, sea pickles, chorus plant and chorus flower are all PushReaction.DESTROY: a piston
pushing into them breaks them and they drop their loot (no tool) - except glow lichen (drops only with shears) and
the chorus flower (drops only when broken by an entity).

Only water SOURCE blocks are placed; cells described as "flow" are left as air and fill with flowing water.
"""
from hm import Design, design, AIR

SB = "stone_bricks"
CB = "cobblestone"
GLASS = "glass"
TGLASS = "tinted_glass"
WATER = "water[level=0]"
PLANK = "spruce_planks"
FENCE = "spruce_fence[east=false,north=false,south=false,waterlogged=false,west=false]"


# --------------------------------------------------------------------------------------------- block states
def logb(axis="y"):
    return f"stripped_spruce_log[axis={axis}]"


def slab(b, t="bottom"):
    return f"{b}_slab[type={t},waterlogged=false]"


def stair(b, facing, half="bottom"):
    return f"{b}_stairs[facing={facing},half={half},shape=straight,waterlogged=false]"


def hopper(f):
    return f"hopper[enabled=true,facing={f}]"


def observer(f):
    return f"observer[facing={f},powered=false]"


def piston(f, sticky=False):
    return f"{'sticky_piston' if sticky else 'piston'}[extended=false,facing={f}]"


def dispenser(f):
    return f"dispenser[facing={f},triggered=false]"


def rep(inp, delay=4):
    """Repeater whose INPUT comes from side `inp` (output on the opposite side)."""
    return f"repeater[delay={delay},facing={inp},locked=false,powered=false]"


def comp(inp):
    """Comparator reading the block on side `inp` (a container), output on the opposite side."""
    return f"comparator[facing={inp},mode=compare,powered=false]"


def dust(n="none", e="none", s="none", w="none"):
    return f"redstone_wire[east={e},north={n},power=0,south={s},west={w}]"


DNS = dust(n="side", s="side")
DEW = dust(e="side", w="side")


def barrel(f="up"):
    return f"barrel[facing={f},open=false]"


def chest(f="north"):
    return f"chest[facing={f},type=single,waterlogged=false]"


def lantern(d, x, y, z, hanging=True):
    d.set(x, y, z, f"lantern[hanging={'true' if hanging else 'false'},waterlogged=false]")


def output(d, x, y, z, f="up"):
    d.set(x, y, z, barrel(f))
    d.tag(x, y, z, "farm_output")


def support(d, x, y, z, block=SB):
    """Put `block` under (x, y, z) unless something solid is there already."""
    if d.air(x, y - 1, z):
        d.set(x, y - 1, z, block)


# --------------------------------------------------------------------------------------------- clocks
def torch_clock(d, bx, y, bz, k=1, south=False, sup=SB):
    """Torch clock around block B = (bx, y, bz): wall torch on B's west face, the loop runs north of B (south of B
    with south=True): dust, k repeaters (delay 4), a dust corner, dust back, one repeater into B.
    B is powered for 2 + 8*(k+1) gt, unpowered for as long. Supports (`sup`) go under every loop cell.
    B's east side, the side away from the loop and the cells above / below B are free for outputs.
    Returns the torch position."""
    s = 1 if south else -1
    tx = bx - 1
    d.set(bx, y, bz, SB)
    d.set(tx, y, bz, "redstone_wall_torch[facing=west,lit=true]")
    far = bz + s * (2 + k)
    cells = {(tx, bz + s): DNS, (tx, far): dust(e="side", **({"n": "side"} if south else {"s": "side"})),
             (bx, far): dust(w="side", **({"n": "side"} if south else {"s": "side"}))}
    for i in range(1, k + 1):
        cells[(tx, bz + s * (1 + i))] = rep("north" if south else "south")
    for zz in range(min(bz + 2 * s, far - s), max(bz + 2 * s, far - s) + 1):
        if zz != far:
            cells[(bx, zz)] = DNS
    cells[(bx, bz + s)] = rep("south" if south else "north")
    for (x, z), st in cells.items():
        d.set(x, y, z, st)
        support(d, x, y, z, sup)
    support(d, bx, y, bz, sup)
    return (tx, y, bz)


def hopper_clock(d, hx, y, hz, sup=SB):
    """Two-hopper clock. A = (hx, y, hz) feeds B = (hx+1, y, hz) and back. Comparators read them from the outside
    (west of A, east of B), each followed by a repeater (delay 1) that restores full strength; A's line runs round
    the south side into a repeater that locks B from the south, B's line round the north side locks A from the
    north. While A holds items, A's line ("S", the output) is on.
    Footprint x hx-3 .. hx+4, z hz-2 .. hz+2. Returns positions used by the farms."""
    cells = {
        (hx, hz): hopper("east"), (hx + 1, hz): hopper("west"),
        (hx - 1, hz): comp("east"), (hx - 2, hz): rep("east", 1),
        (hx + 2, hz): comp("west"), (hx + 3, hz): rep("west", 1),
        # A's line -> lock B from the south
        (hx - 3, hz): dust(e="side", s="side"), (hx - 3, hz + 1): DNS, (hx - 3, hz + 2): dust(n="side", e="side"),
        (hx - 2, hz + 2): DEW, (hx - 1, hz + 2): DEW, (hx, hz + 2): DEW, (hx + 1, hz + 2): dust(w="side", n="side"),
        (hx + 1, hz + 1): rep("south", 1),
        # B's line -> lock A from the north
        (hx + 4, hz): dust(w="side", n="side"), (hx + 4, hz - 1): DNS, (hx + 4, hz - 2): dust(s="side", w="side"),
        (hx + 3, hz - 2): DEW, (hx + 2, hz - 2): DEW, (hx + 1, hz - 2): DEW, (hx, hz - 2): dust(e="side", s="side"),
        (hx, hz - 1): rep("north", 1),
    }
    for (x, z), st in cells.items():
        d.set(x, y, z, st)
        support(d, x, y, z, sup)
    return dict(A=(hx, y, hz), B=(hx + 1, y, hz), RA=(hx - 2, y, hz), RB=(hx + 3, y, hz),
                S=(hx - 3, y, hz + 2))


# --------------------------------------------------------------------------------------------- building kit
def shell(d, X1, Z1, X2, Z2, top, floor=PLANK, wall=CB, post_step=4, windows=()):
    """Farm building: stone-brick plinth course (y2), walls up to `top` with stripped-spruce corner / mid posts and
    a log beam at `top`, floor at y1. Interior is cleared. `windows` = (x, z) wall cells that get glass panes at
    y3..4."""
    for x in range(X1, X2 + 1):
        for z in range(Z1, Z2 + 1):
            edge = x in (X1, X2) or z in (Z1, Z2)
            d.set(x, 1, z, SB if edge else floor)
            for y in range(2, top + 1):
                d.set(x, y, z, (SB if y == 2 else wall) if edge else AIR)
    posts = {(X1, Z1), (X2, Z1), (X1, Z2), (X2, Z2)}
    for x in range(X1 + post_step, X2 - 1, post_step):
        posts |= {(x, Z1), (x, Z2)}
    for z in range(Z1 + post_step, Z2 - 1, post_step):
        posts |= {(X1, z), (X2, z)}
    for (x, z) in posts:
        for y in range(2, top):
            d.set(x, y, z, logb())
    for x in range(X1, X2 + 1):
        for z in (Z1, Z2):
            d.set(x, top, z, logb("x"))
    for z in range(Z1 + 1, Z2):
        for x in (X1, X2):
            d.set(x, top, z, logb("z"))
    for (x, z) in windows:
        if (x, z) not in posts:
            for y in (3, 4):
                d.set(x, y, z, "glass_pane")
    return posts


def roof(d, X1, Z1, X2, Z2, y, axis="x"):
    return d.gable(X1, Z1, X2, Z2, y, axis=axis, stairs="spruce_stairs", ridge="spruce_slab", end=PLANK)


def entrance(d, x, Z1, lines, cx=None, sign_dx=1):
    """Door in the north wall at x, sign beside it, lanterns on fence posts, controller on the north edge and a
    gravel path from the controller to the door."""
    cx = x if cx is None else cx
    d.door(x, 2, Z1, facing="north", wood="spruce")
    d.sign(x + sign_dx, 3, Z1 - 1, "north", lines, wood="spruce")
    for xx in (x - 2, x + 2):
        if d.air(xx, 2, Z1 - 1) and xx != x + sign_dx:
            d.set(xx, 2, Z1 - 1, FENCE)
            lantern(d, xx, 3, Z1 - 1, hanging=False)
    d.hut(cx, 1, 0)
    for z in range(1, Z1):
        d.set(x, 1, z, "gravel")
    for xx in range(min(x, cx), max(x, cx) + 1):
        d.set(xx, 1, 1, "gravel")


def beams(d, X1, X2, z1, z2, y, xs, lamps=True):
    """Tie beams across the building (along z) at the given x, with hanging lanterns."""
    for x in xs:
        for z in range(z1, z2 + 1):
            if d.air(x, y, z):
                d.set(x, y, z, logb("z"))
        if lamps and d.air(x, y - 1, (z1 + z2) // 2):
            lantern(d, x, y - 1, (z1 + z2) // 2)


# ================================================================================================ moss
@design("mossfarm")
def mossfarm(pack, rel, L):
    """Bone-meal moss farm (moss carpet / azalea farm): a dispenser bone-meals a moss block, the moss patch feature
    re-mosses the row and puts plants on it, pistons break the plants, hopper minecarts under the moss collect.

    Moss row M: 5 moss blocks (4..8, 3, 8) over rails (y2) carrying 5 hopper minecarts, hoppers (y1) -> barrel.
    D = (6,3,7) dispenser with bone meal, facing south into the middle moss block. MossBlock.performBonemeal places
    the moss_patch_bonemeal feature at the cell above: in every column within 2-3 blocks that has an air cell on top
    of a #moss_replaceable block it lays moss and, with 60% chance, a plant on top (short grass 50, moss carpet 25,
    tall grass 10, azalea 7, flowering azalea 4). Everything round the row (stone bricks, glass, planks, smooth
    stone) is not moss_replaceable, and the plant channel (y4) has a glass lid (y5), so only the row grows plants
    (no tall grass: it needs two air cells). A moss block only takes bone meal while the cell above it is AIR.
    Torch clock, B = (6,4,7) right above D: B on -> D fires 4 gt later (plants appear); repeater R1 (7,4,7, delay 4,
    input from B) -> dust round the east end -> dust on the back blocks (y5, z10) -> five pistons (y4, z9, facing
    north) fire 8 gt after B and break every plant in the channel (all PushReaction.DESTROY). The items drop onto
    the moss; the hopper minecart under each moss block pulls them through it. Pistons retract before the next
    dispense (B off after 18 gt, period 36 gt)."""
    d = Design(pack, rel, size=(14, 15, 15), gy=1, paving="grass_block")
    X1, Z1, X2, Z2, top = 1, 2, 12, 13, 7
    shell(d, X1, Z1, X2, Z2, top, windows=[(3, Z1), (4, Z1), (9, Z1), (10, Z1), (X1, 6), (X1, 9), (X2, 5),
                                           (X2, 10), (4, Z2), (8, Z2)])
    a, b, c, mz = 4, 8, 6, 8
    d.fill(3, 2, 4, 9, 3, 10, SB)                              # machine pedestal
    for x in range(a, b + 1):
        d.set(x, 1, mz, hopper("east"))
        d.set(x, 2, mz, "rail[shape=east_west,waterlogged=false]")
        d.set(x, 3, mz, "moss_block")
        d.set(x, 2, mz + 1, AIR)                               # slot: put the carts on the rails from the alcove
        d.set(x, 2, mz + 2, AIR)                               # alcove under the back blocks
        d.set(x, 3, mz + 2, AIR)
        d.set(x, 4, mz, AIR)                                   # plant channel
        d.set(x, 5, mz, GLASS)                                 # its lid
        d.set(x, 4, mz + 1, piston("north"))
        d.set(x, 5, mz + 1, GLASS)
        d.set(x, 4, mz + 2, SB)                                # back blocks
        d.set(x, 5, mz + 2, dust(e="side" if x < b + 1 else "none", w="side"))
        d.set(x, 5, mz - 1, GLASS)
    d.set(9, 1, mz, hopper("east"))
    output(d, 10, 1, mz)
    d.set(3, 4, mz, SB)
    d.set(3, 5, mz, GLASS)
    d.set(9, 5, mz, GLASS)
    # dispenser, reached through a short tunnel from the west aisle
    d.set(c, 3, mz - 1, dispenser("south"))
    for x in (3, 4, 5):
        d.set(x, 3, mz - 1, AIR)
    d.set(4, 4, mz - 1, SB)
    # clock: B above the dispenser, torch on its west face, loop to the north
    torch_clock(d, c, 4, mz - 1, k=1)
    d.set(c + 1, 4, mz - 1, rep("west"))                      # R1, input from B
    d.set(c + 2, 4, mz - 1, DEW)
    d.set(9, 4, mz - 1, dust(w="side", s="side"))
    d.set(9, 4, mz, DNS)
    d.set(9, 4, mz + 1, DNS)
    d.set(9, 4, mz + 2, dust(n="side", w="up"))              # climbs onto the back-block line
    for z in (4, 5, 6):                                        # glass case round the clock
        for x in (4, 7):
            d.set(x, 4, z, GLASS)
    # aisles, furniture, light
    d.set(11, 2, 12, chest("west"))
    d.set(11, 2, 11, barrel())
    d.set(2, 2, 12, "composter[level=0]")
    d.set(2, 2, 3, "crafting_table")
    d.sign(2, 3, mz - 1, "east", ["Bone meal", "dispenser", "(through the", "tunnel)"], wood="spruce")
    beams(d, X1, X2, Z1 + 1, Z2 - 1, top, (3, 9), lamps=False)
    for x, z in ((3, 3), (10, 3), (3, 12), (10, 12), (6, 11)):
        lantern(d, x, top - 1, z)
    roof(d, X1, Z1, X2, Z2, top + 1, axis="x")
    entrance(d, c, Z1, ["Moss Farm", "Bring:", "bone meal,", "5 hopper carts"])
    d.farm_test(expect={"minecraft:moss_carpet": 20, "minecraft:azalea": 3},
                inputs={(c, 3, mz - 1): [("minecraft:bone_meal", 192)]},
                spawns=[("minecraft:hopper_minecart", x, 2, mz, 1) for x in range(a, b + 1)], ticks=6000)
    return d


# ================================================================================================ glow berries
@design("glowberry")
def glowberry(pack, rel, L):
    """Glow berry farm: six cave vines kept two blocks long, bone-mealed and cut as soon as they grow.

    Per column x = 5..10:  ceiling (x,6,8) glass;  T = (x,5,8) the top vine, never cut;  K = (x,4,8) the cut cell;
    hopper (x,3,8) under K (line east -> hopper down -> barrel (11,2,8)).
    D = (x,4,7) dispenser with bone meal facing K (south); piston (x,4,9) facing north into K.
    A cave vine head grows one block down on a random tick (10 %): the new head appears in K. Torch clock
    B = (4,5,7): B on -> the dust on top of the dispensers powers them -> 4 gt later every dispenser bone-meals its
    K (CaveVinesBlock: bone meal on a vine without berries gives it berries; on air nothing happens and nothing is
    used) -> repeater RP (4,5,8, delay 4, input from B) -> dust on the back blocks -> 8 gt after B the pistons break
    K (cave vines are PushReaction.DESTROY) and K drops its glow berries onto the hopper. T turns back into a vine
    head with a fresh random age (0..24 < 25), so it always grows again: one glow berry per growth, no waste."""
    d = Design(pack, rel, size=(15, 14, 14), gy=1, paving="grass_block")
    X1, Z1, X2, Z2, top = 1, 2, 13, 12, 8
    shell(d, X1, Z1, X2, Z2, top, windows=[(3, Z1), (4, Z1), (10, Z1), (11, Z1), (X1, 6), (X1, 10), (X2, 5),
                                           (X2, 10), (4, Z2), (7, Z2), (10, Z2)])
    a, b, kz = 5, 10, 8
    d.fill(3, 2, kz - 1, 11, 3, kz + 2, SB)                    # pedestal under dispensers / hoppers / pistons
    d.fill(3, 4, kz, 11, 4, kz + 2, SB)
    d.fill(3, 2, 4, 4, 4, kz - 1, SB)                          # clock pedestal
    for x in range(a, b + 1):
        d.set(x, 3, kz, hopper("east"))
        d.set(x, 4, kz, AIR)                                   # K
        d.set(x, 5, kz, "cave_vines[age=0,berries=false]")    # T
        d.set(x, 6, kz, GLASS)                                 # ceiling the vines hang from
        d.set(x, 4, kz - 1, dispenser("south"))
        d.set(x, 5, kz - 1, dust(e="side", w="side"))
        d.set(x, 4, kz + 1, piston("north"))
        d.set(x, 5, kz + 1, GLASS)
        d.set(x, 5, kz + 2, dust(e="side" if x < b else "none", w="side"))
    d.set(11, 3, kz, hopper("down"))
    output(d, 11, 2, kz)
    for y in (4, 5, 6):
        d.set(11, y, kz, GLASS)
    d.set(11, 4, kz - 1, GLASS)
    # clock and the delayed line to the pistons
    torch_clock(d, a - 1, 5, kz - 1, k=1)
    d.set(a - 1, 5, kz, rep("north"))                          # RP, input from B
    d.set(a - 1, 5, kz + 1, DNS)
    d.set(a - 1, 5, kz + 2, dust(n="side", e="side"))
    # aisles: north aisle (z3..6) in front of the dispensers, west aisle, east aisle to the barrel
    d.set(12, 2, 11, chest("west"))
    d.set(12, 2, 3, barrel())
    d.set(2, 2, 11, "composter[level=0]")
    beams(d, X1, X2, Z1 + 1, Z2 - 1, top, (3, 7, 11), lamps=False)
    for x, z in ((6, 4), (9, 4), (2, 8), (12, 6), (7, 11)):
        lantern(d, x, top - 1, z)
    roof(d, X1, Z1, X2, Z2, top + 1, axis="x")
    entrance(d, 8, Z1, ["Glow Berries", "Bring:", "bone meal for", "6 dispensers"], cx=7)
    d.farm_test(expect={"minecraft:glow_berries": 15},
                inputs={(x, 4, kz - 1): [("minecraft:bone_meal", 64)] for x in range(a, b + 1)}, ticks=12000)
    return d


# ================================================================================================ sea pickles
@design("seapickle")
def seapickle(pack, rel, L):
    """Bone-meal sea pickle farm in a glass tank.

    Pad (y3, z8): water sources x4..10 over a row of live tube coral blocks (x5..9, y2); the mother pickle P sits on
    the middle coral block (7,3,8), waterlogged. D = (7,3,7) dispenser with bone meal facing P (south).
    SeaPickleBlock.performBonemeal (only on a coral block): every water cell of the 5x5 diamond round P (same level)
    that has a coral block under it gets a new pickle (1-4) with chance 1/6 - here only the four coral cells of the
    row qualify, the pickles cannot appear anywhere else. P becomes 4 pickles and is never touched.
    Pistons (y3, z9) facing north stand behind the four outer pad cells; repeaters (delay 1) behind them read the
    dust line z11. Torch clock B = (7,5,6): B on -> the dust (7,5,7) powers the block (7,4,7) above D -> D fires 4 gt
    later; repeater RP (8,5,6, input from B) -> dust along the east wall, down to the line z11 -> pistons fire 10 gt
    after B, break every new pickle (PushReaction.DESTROY: the cell keeps its water, it refills as a source from the
    two source cells beside it) and push the drops north.
    North row (z7, y3): FLOW - water from the pad flows over a row of hoppers (y2), so the pad sources have a lower
    neighbour to the north and their current carries the pickles onto the hoppers: west half -> barrel (2,2,7),
    east half -> barrel (12,2,7). No hopper under D (it would empty the dispenser)."""
    d = Design(pack, rel, size=(15, 13, 15), gy=1, paving="grass_block")
    X1, Z1, X2, Z2, top = 1, 1, 13, 13, 7
    shell(d, X1, Z1, X2, Z2, top, windows=[(3, Z1), (4, Z1), (10, Z1), (11, Z1), (X1, 5), (X1, 9), (X2, 5),
                                           (X2, 9), (4, Z2), (7, Z2), (10, Z2)])
    c, pz = 7, 8
    d.fill(3, 2, 6, 11, 2, 11, SB)                             # pedestal
    # collection rows (y2) under the north row
    for x in (4, 5, 6):
        d.set(x, 2, 7, hopper("west"))
    for x in (8, 9, 10):
        d.set(x, 2, 7, hopper("east"))
    d.set(3, 2, 7, hopper("west"))
    d.set(11, 2, 7, hopper("east"))
    output(d, 2, 2, 7)
    output(d, 12, 2, 7)
    # coral row, pad, mother, dispenser
    for x in range(5, 10):
        d.set(x, 2, pz, "tube_coral_block")
    for x in range(4, 11):
        d.set(x, 3, pz, WATER)
        if x != c:
            d.set(x, 3, pz - 1, AIR)                            # flow
        d.set(x, 4, pz, GLASS)
        d.set(x, 4, pz - 1, GLASS)
    d.set(c, 3, pz, "sea_pickle[pickles=1,waterlogged=true]")
    d.set(c, 3, pz - 1, dispenser("south"))
    d.set(c, 4, pz - 1, SB)                                    # powered by the dust on top -> powers D
    # tank walls
    for x in range(3, 12):
        d.set(x, 3, pz - 2, GLASS)
        d.set(x, 4, pz - 2, GLASS)
    d.set(c, 3, pz - 2, AIR)                                   # reach D from the north aisle
    for z in (pz - 1, pz):
        for x in (3, 11):
            d.set(x, 3, z, GLASS)
            d.set(x, 4, z, GLASS)
    # pistons, repeaters, dust line
    for x in range(3, 12):
        d.set(x, 3, pz + 1, SB)
        d.set(x, 3, pz + 2, SB)
        d.set(x, 4, pz + 1, GLASS)
    for x in (5, 6, 8, 9):
        d.set(x, 3, pz + 1, piston("north"))
        d.set(x, 3, pz + 2, rep("south", 1))
    for x in range(5, 11):
        d.set(x, 3, pz + 3, DEW)
    d.set(11, 3, pz + 3, SB)
    # clock (y5) on a small ceiling over the north aisle, line to the pistons along the east wall
    d.fill(6, 4, 3, 7, 4, 5, SB)
    d.set(6, 4, 6, SB)
    torch_clock(d, c, 5, pz - 2, k=1)
    d.set(c, 5, pz - 1, DNS)
    d.set(c + 1, 5, pz - 2, rep("west"))                      # RP, input from B
    d.set(9, 5, 6, DEW)
    d.set(10, 5, 6, DEW)
    d.set(11, 5, 6, dust(w="side", s="side"))
    for z in (7, 8, 9):
        d.set(11, 5, z, DNS)
    d.set(11, 4, 9, SB)
    d.set(11, 4, 10, SB)
    d.set(11, 5, 10, dust(n="side", s="side"))
    d.set(11, 4, 11, dust(n="up", w="side"))
    d.set(10, 3, 11, dust(e="side", w="side"))
    # aisles and furniture
    d.set(2, 2, 12, chest("east"))
    d.set(12, 2, 12, barrel())
    d.set(2, 2, 3, "crafting_table")
    d.set(9, 2, 2, "spruce_slab[type=bottom,waterlogged=false]")
    beams(d, X1, X2, Z1 + 1, Z2 - 1, top, (3, 11), lamps=False)
    for x, z in ((3, 3), (11, 3), (3, 12), (11, 12), (7, 12)):
        lantern(d, x, top - 1, z)
    roof(d, X1, Z1, X2, Z2, top + 1, axis="x")
    entrance(d, c, Z1, ["Sea Pickles", "Bring:", "bone meal", "(dispenser ahead)"])
    d.farm_test(expect={"minecraft:sea_pickle": 20},
                inputs={(c, 3, pz - 1): [("minecraft:bone_meal", 192)]}, ticks=6000)
    return d


# ================================================================================================ dripstone
@design("dripstonefarm")
def dripstonefarm(pack, rel, L):
    """Pointed dripstone farm, 20 stalactites in two rows sharing one piston line.

    Per column (x = 3..12, rows z6 and z10): water source W (y8) on a dripstone block D (y7), the stalactite tip T1
    (y6) under it, the cut cell T2 (y5), a MUD block (y4) on a hopper (y3).
    PointedDripstoneBlock.randomTick: with chance 0.0114 the top stalactite piece, when the block above it is a
    dripstone block with a water SOURCE on top, grows: half the time the stalactite gets a new tip below it
    (into T2), half the time a stalagmite grows up from the first sturdy floor under the tip - the mud (sturdy
    top face) - also into T2. Either way a pointed dripstone appears in T2.
    Pistons (y5) beside every T2 (z7 facing north, z9 facing south) are powered through the shared back blocks (z8)
    by the dust on top of them. An observer (14,6,8) watches the torch of a slow torch clock (period 68 gt) and
    pulses (2 gt) on every change: the pistons break whatever is in T2 (PushReaction.DESTROY), the drop falls on
    the mud and the hopper under it takes it (mud is 14/16 high). T1 is never touched; T2 is free again at once."""
    d = Design(pack, rel, size=(19, 16, 15), gy=1, paving="grass_block")
    X1, Z1, X2, Z2, top = 1, 2, 17, 13, 10
    shell(d, X1, Z1, X2, Z2, top, windows=[(3, Z1), (4, Z1), (6, Z1), (7, Z1), (10, Z1), (11, Z1),
                                           (X1, 6), (X1, 10), (4, Z2), (7, Z2), (10, Z2), (13, Z2)])
    xs = range(3, 13)
    rows = (6, 10)
    d.fill(2, 2, 5, 13, 4, 11, SB)                             # pedestal
    for x in xs:
        for zr in rows:
            d.set(x, 3, zr, hopper("east"))
            d.set(x, 4, zr, "mud")
            d.set(x, 5, zr, AIR)                               # T2
            d.set(x, 6, zr, "pointed_dripstone[thickness=tip,vertical_direction=down,waterlogged=false]")
            d.set(x, 7, zr, "dripstone_block")
        d.set(x, 5, 7, piston("north"))
        d.set(x, 5, 8, SB)
        d.set(x, 5, 9, piston("south"))
        d.set(x, 6, 8, DEW)
        for z in (5, 11):
            for y in (5, 6, 7):
                d.set(x, y, z, GLASS)
        for z in (7, 9):
            d.set(x, 6, z, GLASS)
        for z in (7, 8, 9):
            d.set(x, 7, z, GLASS)
    for z in range(5, 12):                                     # glass ends
        for y in (5, 6, 7):
            d.set(2, y, z, GLASS)
            d.set(13, y, z, GLASS)
    d.fill(2, 8, 5, 13, 8, 11, SB)                             # water trays
    for x in xs:
        for zr in rows:
            d.set(x, 8, zr, WATER)
    # collection: both hopper rows run east into the column x13 -> barrel (13,2,10)
    for z in range(6, 10):
        d.set(13, 3, z, hopper("south"))
    d.set(13, 3, 10, hopper("down"))
    output(d, 13, 2, 10)
    d.set(13, 2, 11, AIR)
    # clock tower east of the rows: observer -> dust -> back-block line
    d.fill(14, 2, 3, 16, 5, 8, SB)
    torch_clock(d, 16, 6, 8, k=3)
    d.set(14, 6, 8, observer("east"))
    d.set(13, 5, 8, SB)
    d.set(13, 6, 8, DEW)
    for z in range(3, 9):                                      # glass case round the clock
        for x in (14,):
            if d.air(x, 6, z):
                d.set(x, 6, z, GLASS)
    # aisles, furniture, light
    d.set(16, 2, 12, chest("west"))
    d.set(15, 2, 12, barrel())
    d.set(2, 2, 12, "cauldron")
    d.set(2, 2, 3, "crafting_table")
    beams(d, X1, X2, Z1 + 1, Z2 - 1, top, (4, 8, 12), lamps=False)
    for x, z in ((3, 3), (8, 3), (12, 3), (8, 12), (15, 10)):
        lantern(d, x, top - 1, z)
    roof(d, X1, Z1, X2, Z2, top + 1, axis="x")
    entrance(d, 8, Z1, ["Dripstone", "Farmworks", "Bring:", "nothing"], cx=9)
    d.farm_test(expect={"minecraft:pointed_dripstone": 8}, ticks=18000)
    return d
