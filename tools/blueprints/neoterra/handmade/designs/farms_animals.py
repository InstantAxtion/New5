"""
Farmworks animal farms (decorations/animalfarms/): stone-brick and spruce barns around proven vanilla (Java 1.21.1)
animal mechanics. What is automatic and what the player does is written on each farm's sign and below.

Redstone conventions used here (1.21.1 block states):
  * observer  facing = the side it WATCHES; it pulses (2 game ticks) out of the opposite face.
  * comparator facing = the side its INPUT comes from (DiodeBlock reads pos.relative(facing)); output goes the other way.
  * dispenser facing = the side it shoots / uses its item into. hopper facing = output side (never up).
  * redstone dust is placed as a cross (all four sides) where it stands alone; a lone dust recomputes to a cross
    anyway and then powers every horizontal neighbour.
Fluids: only lava sources (level=0) are placed, each one held in place by a non-flammable sign or slab under it
(lava cannot flow into a waterloggable block) and solid blocks around it.
"""
from hm import Design, design, AIR

SB = "stone_bricks"
CB = "cobblestone"
LOG = "stripped_spruce_log"
LAVA = "lava[level=0]"
GRASS = "grass_block[snowy=false]"
FENCE = "spruce_fence[east=false,north=false,south=false,waterlogged=false,west=false]"
DUST = "redstone_wire[east=side,north=side,power=0,south=side,west=side]"


def logb(axis="y"):
    return f"{LOG}[axis={axis}]"


def slab(b, t="bottom"):
    return f"{b}_slab[type={t},waterlogged=false]"


def stair(b, facing, half="bottom"):
    return f"{b}_stairs[facing={facing},half={half},shape=straight,waterlogged=false]"


def lantern(d, x, y, z, hanging=True):
    d.set(x, y, z, f"lantern[hanging={'true' if hanging else 'false'},waterlogged=false]")


def chest(facing="north"):
    return f"chest[facing={facing},type=single,waterlogged=false]"


def hopper(facing="down"):
    return f"hopper[enabled=true,facing={facing}]"


def dispenser(facing):
    return f"dispenser[facing={facing},triggered=false]"


def observer(facing):
    return f"observer[facing={facing},powered=false]"


# ------------------------------------------------------------------------------------------------- the barn
def barn(d, X1, Z1, X2, Z2, top, door_x, floor="spruce_planks", roof=True, roof_y=None, windows=(),
         back_door_x=None):
    """Stone-brick plinth course, cobble walls up to `top` with stripped-spruce posts every 4 and a log beam on top,
    gable roof (ridge along x) with spruce-plank gables, spruce door in the north wall."""
    gy = 1
    for x in range(X1, X2 + 1):
        for z in range(Z1, Z2 + 1):
            d.set(x, gy, z, SB if x in (X1, X2) or z in (Z1, Z2) else floor)
    for y in range(gy + 1, top + 1):
        for x in range(X1, X2 + 1):
            for z in range(Z1, Z2 + 1):
                if x in (X1, X2) or z in (Z1, Z2):
                    d.set(x, y, z, SB if y == gy + 1 else CB)
                else:
                    d.set(x, y, z, AIR)
    posts = {(X1, Z1), (X2, Z1), (X1, Z2), (X2, Z2)}
    for x in range(X1 + 4, X2 - 1, 4):
        posts |= {(x, Z1), (x, Z2)}
    for z in range(Z1 + 4, Z2 - 1, 4):
        posts |= {(X1, z), (X2, z)}
    for x in range(X1, X2 + 1):
        for z in (Z1, Z2):
            d.set(x, top, z, logb("x"))
    for z in range(Z1, Z2 + 1):
        for x in (X1, X2):
            d.set(x, top, z, logb("z"))
    for (x, z) in posts:
        for y in range(gy + 1, top + 1):
            d.set(x, y, z, logb("y"))
    for (x, z) in windows:
        d.set(x, 3, z, "glass_pane")
        d.set(x, 4, z, "glass_pane")
    d.door(door_x, gy + 1, Z1, "south", "spruce")
    if back_door_x is not None:
        d.door(back_door_x, gy + 1, Z2, "north", "spruce")
    if roof:
        d.gable(X1, Z1, X2, Z2, roof_y or top + 1, axis="x", end="spruce_planks")


def approach(d, cx, Z1, sign_lines, x_sign=None):
    """Controller on the north edge, gravel path to the door, lantern posts and the entrance sign."""
    for z in range(0, Z1):
        for x in (cx - 1, cx, cx + 1):
            d.set(x, 1, z, "gravel")
    d.hut(cx, 1, 0)
    for x in (cx - 2, cx + 2):
        d.set(x, 2, Z1 - 1, FENCE)
        lantern(d, x, 3, Z1 - 1, hanging=False)
    xs = x_sign if x_sign is not None else cx + 1
    d.sign(xs, 3, Z1 - 1, "north", sign_lines, "spruce")


# ================================================================================================ wool
@design("woolfarm")
def woolfarm(pack, rel, L):
    """Observer wool farm (the standard 1.21 design), four stalls side by side.

    Per stall (cell x = c, sheep at (c,5,7)):
        (c,4,7) grass block the sheep stands on     (c,3,7) rail, (c,2,7) hopper under it (line west to the chest)
        (c,4,8) observer facing north (watches the grass)      -> pulses into (c,4,9) stone brick
        (c,5,8) dispenser with shears, facing north (into the sheep)
        (c,5,9) redstone dust on that stone brick: powered by it, it powers the dispenser in front of it
    When the sheep eats the grass (grass -> dirt) its wool grows back at the same moment; the observer sees the grass
    change and the dispenser shears the sheep. The wool lands on the grass block; a HOPPER MINECART on the rail under
    it picks the items up through the grass (hopper minecarts pull items through a full block) and the hopper under
    the rail empties the cart into the chest. The dirt turns back into grass from the grass blocks next to it
    (under the glass walls); lanterns between the stalls keep the light up for that, day and night."""
    d = Design(pack, rel, size=(17, 14, 15), gy=1, paving="grass_block")
    X1, Z1, X2, Z2, top = 1, 2, 15, 13, 8
    cx = 8
    barn(d, X1, Z1, X2, Z2, top, cx, windows=[(3, Z1), (5, Z1), (11, Z1), (13, Z1), (X1, 5), (X2, 5),
                                               (X1, 10), (X2, 10)], roof_y=top + 1)
    cells = (5, 7, 9, 11)
    # machine block x4..12, z6..9
    d.fill(4, 2, 6, 12, 4, 9, SB)
    for x in range(4, 13):
        d.set(x, 2, 7, hopper("west"))                    # collection line -> chest at x3
        d.set(x, 3, 6, AIR)                               # slot to put the hopper minecarts on the rails
        for z in (6, 7, 8):
            d.set(x, 4, z, GRASS)
        d.set(x, 3, 7, "chiseled_stone_bricks" if x in (4, 12) else SB)
        for y in (5, 6):
            d.set(x, y, 6, "glass")                      # front glass
        d.set(x, 5, 8, "glass")
        d.set(x, 6, 8, "glass")
        d.set(x, 7, 6, "glass")
        d.set(x, 7, 7, "glass")
        d.set(x, 7, 8, "glass")
        d.set(x, 5, 9, "glass")
    for x in range(4, 13, 2):                             # walls between the stalls: glass with a lantern on top
        d.set(x, 5, 7, "glass")
        lantern(d, x, 6, 7, hanging=False)
    for c in cells:
        d.set(c, 3, 7, "rail[shape=east_west,waterlogged=false]")
        d.set(c, 5, 7, AIR)
        d.set(c, 6, 7, AIR)
        d.set(c, 4, 8, observer("north"))
        d.set(c, 5, 8, dispenser("north"))
        d.set(c, 4, 9, SB)
        d.set(c, 5, 9, DUST)
    d.set(3, 2, 7, chest("east"))
    d.tag(3, 2, 7, "farm_output")
    d.set(3, 3, 7, AIR)
    d.set(3, 2, 6, AIR)
    d.set(3, 3, 6, AIR)
    for z in (8, 9):
        for y in (2, 3, 4):
            d.set(3, y, z, SB)
    d.set(2, 2, 9, chest("east"))                        # spare chest for shears / minecarts
    d.set(2, 2, 10, "barrel[facing=up,open=false]")
    # back gallery (floor y4) to refill the shears, stairs up on the east side
    d.fill(4, 2, 10, 14, 4, 12, SB)
    for x in range(4, 15):
        d.set(x, 4, 10, "spruce_planks")
        d.set(x, 4, 11, "spruce_planks")
        d.set(x, 4, 12, "spruce_planks")
    for x in (13, 14):
        d.clear(x, 2, 6, x, 6, 9)
        d.set(x, 2, 7, stair("spruce", "south"))
        d.set(x, 2, 8, "spruce_planks")
        d.set(x, 3, 8, stair("spruce", "south"))
        d.set(x, 2, 9, "spruce_planks")
        d.set(x, 3, 9, "spruce_planks")
        d.set(x, 4, 9, "spruce_planks")
    for x in (4, 8, 12):
        lantern(d, x, top - 1, 11)
    for x in (5, 11):
        lantern(d, x, top - 1, 4)
    # tie beams under the roof
    for x in (5, 11):
        for z in range(Z1 + 1, Z2):
            d.set(x, top, z, logb("z"))
    d.set(2, 2, 3, "crafting_table")
    d.set(14, 2, 3, "barrel[facing=up,open=false]")
    d.set(14, 2, 4, "hay_block[axis=y]")
    approach(d, cx, Z1, ["Wool Farm", "Bring: 4 sheep,", "4 hopper carts,", "4 shears"])
    d.farm_test(expect={"minecraft:white_wool": 4}, ticks=10000,
                inputs={(c, 5, 8): [("minecraft:shears", 1)] for c in cells},
                spawns=[("minecraft:sheep", c, 5, 7, 1) for c in cells]
                + [("minecraft:hopper_minecart", c, 3, 7, 1) for c in cells])
    return d


# ================================================================================================ chicken
@design("chickencooker")
def chickencooker(pack, rel, L):
    """Automatic cooked-chicken farm (the classic egg-dispenser + lava-blade cooker).

    Breeder pen (y6): chickens stand on a floor of 14 hoppers (y5) that funnel every egg they lay into the hopper
    R = (7,5,6) and down (7,4,6) -> (7,3,6) into the dispenser D = (7,3,7), facing south.
    Trigger: comparator C = (7,5,7) reads R (facing north = its input side); each time an egg comes in or out of R
    its output toggles, and the observer O = (7,4,7) (facing up: watches C) pulses down into D, which throws the
    eggs it holds into the chick chamber. 1 in 8 eggs hatches.
    Chick chamber (7,3,8..9): bottom slabs (chickens stand at y3.5) with lava sources at y4 right over them; the lava
    cannot flow into the slab cells. Chicks (0.35 high) live under the lava; when one grows up (0.7 high, ~20 min)
    its head reaches into the lava and it burns: cooked chicken + feathers fall on the slabs and the hoppers under
    them (they pull items through slabs) carry them to the chest at (5,2,8)."""
    d = Design(pack, rel, size=(17, 15, 14), gy=1, paving="grass_block")
    X1, Z1, X2, Z2, top = 1, 2, 15, 11, 8
    cx = 8
    barn(d, X1, Z1, X2, Z2, top, cx, windows=[(3, Z1), (4, Z1), (12, Z1), (13, Z1), (X1, 8), (X2, 8)],
         back_door_x=None)
    # solid machine core under the pen and around the cooker
    d.fill(3, 2, 4, 12, 4, 6, SB)
    d.fill(6, 2, 7, 10, 5, 10, SB)
    # breeder pen: hopper floor y5, glass walls y6..7
    for x in range(4, 13):
        d.set(x, 5, 5, hopper("south"))
        d.set(x, 5, 6, hopper("east" if x < cx else "west"))
    d.set(cx, 5, 6, hopper("down"))                       # R
    d.set(cx, 4, 6, hopper("down"))
    d.set(cx, 3, 6, hopper("south"))                      # into the dispenser
    for x in range(3, 14):
        for y in (6, 7):
            d.set(x, y, 4, "glass")
            d.set(x, y, 7, "glass")
    for z in (5, 6):
        for y in (6, 7):
            d.set(3, y, z, "glass")
            d.set(13, y, z, "glass")
    for x in (3, 13):
        for z in (4, 7):
            d.set(x, 5, z, SB)
    d.set(3, 5, 5, SB)
    d.set(3, 5, 6, SB)
    d.set(13, 5, 5, SB)
    d.set(13, 5, 6, SB)
    d.fill(3, 2, 4, 3, 4, 6, SB)
    d.fill(13, 2, 4, 13, 4, 6, SB)
    d.fill(4, 5, 4, 12, 5, 4, SB)
    d.set(cx, 6, 4, "spruce_fence_gate[facing=north,in_wall=false,open=false,powered=false]")
    d.set(cx, 7, 4, AIR)
    d.fill(4, 5, 7, 12, 5, 7, SB)
    # dispenser and its clock: torch + 2 repeaters (period 36 ticks, the torch toggles 3x a minute-tick: no burnout)
    d.set(cx, 3, 7, dispenser("south"))
    bt = cx - 1                                            # (7,3,7): the block that powers the dispenser
    d.set(bt, 3, 7, SB)
    d.set(bt - 1, 3, 7, "redstone_wall_torch[facing=west,lit=true]")
    d.set(bt - 1, 3, 6, DUST)
    d.set(bt - 1, 3, 5, "repeater[delay=4,facing=south,locked=false,powered=false]")
    d.set(bt - 1, 3, 4, DUST)
    d.set(bt, 3, 4, DUST)
    d.set(bt, 3, 5, DUST)
    d.set(bt, 3, 6, "repeater[delay=4,facing=north,locked=false,powered=false]")
    # chick chamber: slab floor, lava blade, glass on the east side; the hoppers under the slabs only collect
    # (they push west into a separate line), so they are ready to pull a drop the tick it lands
    for z in (8, 9):
        d.set(cx, 3, z, slab("stone_brick"))
        d.set(cx, 4, z, LAVA)
        d.set(cx + 1, 3, z, "glass")
        d.set(cx + 1, 4, z, "glass")
        d.set(cx, 2, z, hopper("west"))
    d.set(cx - 1, 2, 9, hopper("north"))
    d.set(cx - 1, 2, 8, hopper("west"))
    d.set(cx - 2, 2, 8, chest("east"))
    d.tag(cx - 2, 2, 8, "farm_output")
    d.fill(cx - 2, 3, 7, cx - 2, 5, 10, AIR)
    d.set(bt - 1, 3, 7, "redstone_wall_torch[facing=west,lit=true]")
    d.fill(cx - 2, 2, 9, cx - 2, 5, 10, AIR)
    d.set(cx - 2, 2, 7, AIR)
    d.fill(cx + 2, 2, 7, cx + 2, 5, 10, AIR)
    # the cooker housing above the lava: stone, with a chimney-like cap
    d.fill(cx - 1, 5, 8, cx + 1, 5, 10, SB)
    d.set(cx, 6, 9, "chiseled_stone_bricks")
    # gallery to the pen gate (y5 deck along z3) with stairs from the east
    for x in range(3, 12):
        d.set(x, 5, 3, "spruce_planks")
    d.set(12, 4, 3, stair("spruce", "west"))
    d.set(13, 3, 3, stair("spruce", "west"))
    d.set(13, 2, 3, "spruce_planks")
    d.set(14, 2, 3, stair("spruce", "west"))
    lantern(d, 3, 6, 3, hanging=False)
    # room furniture
    d.set(2, 2, 9, chest("east"))
    d.set(2, 2, 10, "barrel[facing=up,open=false]")
    d.set(14, 2, 9, "hay_block[axis=y]")
    d.set(14, 2, 10, "composter[level=0]")
    d.set(2, 2, 3, "crafting_table")
    for x in (4, 12):
        lantern(d, x, top - 1, 9)
    lantern(d, cx, top - 1, 5)
    for x in (5, 11):
        for z in range(Z1 + 1, Z2):
            d.set(x, top, z, logb("z"))
    approach(d, cx, Z1, ["Chicken Cooker", "Bring: chickens", "(10+) or eggs", "to throw in"])
    d.farm_test(expect={"minecraft:cooked_chicken": 3}, ticks=3000,
                inputs={(cx, 5, 6): [("minecraft:egg", 16)]},
                spawns=[("minecraft:chicken", cx, 3, 8, 2), ("minecraft:chicken", cx, 3, 9, 2),
                        ("minecraft:chicken", 6, 6, 5, 3)])
    return d
