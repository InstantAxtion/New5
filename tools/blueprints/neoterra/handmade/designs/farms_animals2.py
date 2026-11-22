"""
Farmworks animal farms, part 2 (decorations/animalfarms/): squid farm, piglin barter station, villager breeder and
froglight farm. Stone-brick plinths, spruce framing, cobble walls, glass to watch the mechanism, lanterns.

Mechanics were checked against the 1.21.1 game code (decompiled), not only tutorials:
  * Squid.aiStep OVERWRITES the squid's velocity every tick while it is in water (tx/ty/tz * speed), so water
    currents and bubble columns do not move squids. Squids only leave water by their own random swimming. The squid
    farm therefore uses a pool whose whole floor is a curtain of wall SIGNS (no collision, and FlowingFluid never
    flows into a sign): a squid that swims down through the floor is out of the water, falls into the dry chamber
    below and dies there (WaterAnimal.handleAirSupply: 300 ticks of air, then 2 damage a second).
  * Piglins pick up a dropped gold ingot at once if they are not already admiring one (PiglinAi.wantsToPickup), hold
    it 119 ticks and throw a bartering loot roll towards a random spot nearby (no player around).
  * Frogs eat only size-1 magma cubes they can PATH to (ShootTongue.canPathfindToTarget, < 1.75 blocks); the
    magma_cube loot table drops a froglight whose colour follows the frog variant (warm -> pearlescent,
    temperate -> ochre, cold -> verdant). Frogs get their variant from the biome they spawn/hatch in.
  * Villagers breed (VillagerMakeLove) when both have 12 food points, see each other (line of sight), are within
    sqrt(5) blocks of each other, and a free bed is reachable (path to within 1 block) from the parent.

Redstone conventions (1.21.1 block states):
  * repeater facing = the side its INPUT comes from (DiodeBlock reads pos.relative(facing)); it outputs the other way.
  * redstone_wall_torch facing = away from the block it is attached to; the torch turns off when that block is
    powered. dropper facing = the side it drops / inserts into. hopper facing = output side (never up).
  * redstone dust is placed with explicit connections.
"""
from hm import Design, design, AIR

SB = "stone_bricks"
CB = "cobblestone"
LOG = "stripped_spruce_log"
FENCE = "spruce_fence[east=false,north=false,south=false,waterlogged=false,west=false]"
WATER = "water[level=0]"


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


def dropper(facing):
    return f"dropper[facing={facing},triggered=false]"


def repeater(facing, delay=4):
    return f"repeater[delay={delay},facing={facing},locked=false,powered=false]"


def dust(n="none", e="none", s="none", w="none"):
    return f"redstone_wire[east={e},north={n},power=0,south={s},west={w}]"


def gate(facing):
    return f"spruce_fence_gate[facing={facing},in_wall=false,open=false,powered=false]"


def shell(d, X1, Z1, X2, Z2, y0, top, floor=None, door_x=None, windows=(), posts_every=4):
    """Farmworks barn walls: stone-brick course at y0, cobble above up to `top`, stripped spruce posts at the corners
    and every `posts_every`, log beam along the top. Interior is cleared (y0..top); `floor` is laid at y0 - 1."""
    for y in range(y0, top + 1):
        for x in range(X1, X2 + 1):
            for z in range(Z1, Z2 + 1):
                if x in (X1, X2) or z in (Z1, Z2):
                    d.set(x, y, z, SB if y == y0 else CB)
                else:
                    d.set(x, y, z, AIR)
    if floor:
        for x in range(X1 + 1, X2):
            for z in range(Z1 + 1, Z2):
                d.set(x, y0 - 1, z, floor)
    posts = {(X1, Z1), (X2, Z1), (X1, Z2), (X2, Z2)}
    for x in range(X1 + posts_every, X2 - 1, posts_every):
        posts |= {(x, Z1), (x, Z2)}
    for z in range(Z1 + posts_every, Z2 - 1, posts_every):
        posts |= {(X1, z), (X2, z)}
    for x in range(X1, X2 + 1):
        for z in (Z1, Z2):
            d.set(x, top, z, logb("x"))
    for z in range(Z1, Z2 + 1):
        for x in (X1, X2):
            d.set(x, top, z, logb("z"))
    for (x, z) in posts:
        for y in range(y0, top + 1):
            d.set(x, y, z, logb("y"))
    for (x, y, z) in windows:
        d.set(x, y, z, "glass_pane")
    if door_x is not None:
        d.door(door_x, y0, Z1, "south", "spruce")


def entrance(d, cx, gy, Z1, door_x, lines):
    """Controller in the middle of the north edge, gravel path to the door, lantern posts and the sign."""
    lo, hi = min(cx, door_x) - 1, max(cx, door_x) + 1
    for z in range(0, Z1):
        for x in range(lo, hi + 1):
            if z == Z1 - 1 and abs(x - door_x) > 1:
                continue
            d.set(x, gy, z, "gravel")
    d.hut(cx, gy, 0)
    for x in (door_x - 2, door_x + 2):
        d.set(x, gy + 1, Z1 - 1, FENCE)
        lantern(d, x, gy + 2, Z1 - 1, hanging=False)
    d.sign(door_x + 1, gy + 2, Z1 - 1, "north", lines, "spruce")


# ================================================================================================ squid
@design("squidfarm")
def squidfarm(pack, rel, L):
    """Squid farm: a sunken pool with a sign floor over a dry kill chamber (automatic, slow - vanilla squid rates).

    Build it on a river or ocean shore with the ground at sea level (y 62-64): squids only spawn in water between
    sea level - 13 and sea level, with water above and below the spawn block (WaterAnimal spawn rules), in river /
    ocean biomes. Light does not matter for squids. (Glow squids need total darkness BELOW y 30 - the farm catches
    them too if a glow squid ever gets in, but at sea level none will spawn.)

    Pool: water SOURCES x4..11, z5..9, y5..8 (4 deep, top flush with the ground). Its floor (y4) is a curtain of wall
    signs in three 2-wide strips (x4/5, x7/8, x10/11; the sign at the west of a strip faces east and hangs on the
    block west of it, the east one faces west) between stone-brick ribs (x6, x9). Water never flows into a sign, so
    the pool stays full; signs have no collision, so a squid swimming down through the floor leaves the water and
    falls into the chamber below (y2..3). Out of water a squid's own swimming stops (it only falls), it runs out of
    air after 15 s and drowns 5 s later, on a floor of hoppers (y1) under the strips. The hoppers run south to a
    hopper line (z10, under the chamber's glass south wall) that empties west into the chest at (3,1,10) in the
    cellar. Stairs down along the west side (x2)."""
    gy = 8
    d = Design(pack, rel, size=(15, 21, 15), gy=gy, paving="grass_block")
    # ---- below ground: stone-brick shell for pool, chamber, stairwell and cellar
    d.fill(1, 0, 3, 13, gy - 1, 13, SB)
    # pool water, 4 deep
    for x in range(4, 12):
        for z in range(5, 10):
            for y in range(5, 9):
                d.set(x, y, z, WATER)
    # sign floor (y4) between ribs
    for z in range(5, 10):
        for (x, facing) in ((4, "east"), (5, "west"), (7, "east"), (8, "west"), (10, "east"), (11, "west")):
            d.sign(x, 4, z, facing, ["", "", "", ""], "spruce")
        for x in (6, 9):
            d.set(x, 4, z, "chiseled_stone_bricks" if z in (5, 9) else SB)
    # kill chamber (y2..3) with hopper floor (y1) under the strips
    for x in range(4, 12):
        for z in range(5, 10):
            d.set(x, 2, z, AIR)
            d.set(x, 3, z, AIR)
            if x in (6, 9):
                d.set(x, 1, z, "polished_andesite")
            else:
                d.set(x, 1, z, hopper("south"))
        d.set(x, 1, 10, hopper("west"))                 # collection line under the south wall
        d.set(x, 2, 10, "glass")
        d.set(x, 3, 10, "glass")
    for x in (6, 9):                                     # light in the chamber (no hostile spawns in the dark)
        lantern(d, x, 2, 5, hanging=False)
        lantern(d, x, 2, 9, hanging=False)
    for z in range(5, 10):                               # west window onto the chamber from the stairs
        d.set(3, 2, z, "glass")
        d.set(3, 3, z, "glass")
    d.set(3, 1, 10, chest("east"))
    d.tag(3, 1, 10, "farm_output")
    d.set(3, 2, 10, "glass")                             # (a chest opens under glass)
    # cellar z11..12, x2..12, standing y2..3
    for x in range(2, 13):
        for z in (11, 12):
            d.set(x, 1, z, "spruce_planks")
            d.set(x, 2, z, AIR)
            d.set(x, 3, z, AIR)
    for x in (5, 9):
        lantern(d, x, 3, 12)
    d.set(12, 2, 12, "barrel[facing=up,open=false]")
    d.set(11, 2, 12, chest("north"))
    d.set(4, 2, 12, "crafting_table")
    # stairwell x2 from the ground (z4) down to the cellar (z11)
    for z in range(5, 11):
        for y in range(2, gy + 1):
            d.set(2, y, z, AIR)
    for i, z in enumerate(range(5, 11)):
        d.set(2, gy - 1 - i, z, stair("spruce", "north"))
    d.set(2, 1, 11, "spruce_planks")
    d.set(2, 4, 11, AIR)                                 # headroom at the foot of the stairs
    # ---- the pool house above ground
    X1, Z1, X2, Z2, top = 1, 2, 13, 13, gy + 5
    shell(d, X1, Z1, X2, Z2, gy + 1, top, door_x=7,
          windows=[(x, gy + 2, Z1) for x in (3, 4, 10, 11)] + [(x, gy + 3, Z1) for x in (3, 4, 10, 11)]
          + [(X1, gy + 2, z) for z in (5, 6, 9, 10)] + [(X1, gy + 3, z) for z in (5, 6, 9, 10)]
          + [(X2, gy + 2, z) for z in (5, 6, 9, 10)] + [(X2, gy + 3, z) for z in (5, 6, 9, 10)])
    for x in range(X1 + 1, X2):                          # walkway floor around the pool (planks), pool edge stone
        for z in range(Z1 + 1, Z2):
            if 4 <= x <= 11 and 5 <= z <= 9:
                continue
            if x == 2 and 5 <= z <= 10:
                continue                                  # stairwell opening
            edge = x in (3, 12) or z in (4, 10)
            d.set(x, gy, z, "polished_andesite" if edge else "spruce_planks")
    for z in range(6, 11):                               # railing along the stairwell
        d.set(3, gy + 1, z, FENCE)
    d.set(2, gy + 1, 11, FENCE)
    for (x, z) in ((3, 3), (12, 3), (3, 12), (12, 12)):
        lantern(d, x, gy + 1, z, hanging=False)
    for x in (5, 9):
        for z in range(Z1 + 1, Z2):
            d.set(x, top, z, logb("z"))
    for x in (5, 9):
        lantern(d, x, top - 1, 7)
    d.set(12, gy + 1, 11, "barrel[facing=up,open=false]")
    d.set(11, gy + 1, 12, "crafting_table")
    d.gable(X1, Z1, X2, Z2, top + 1, axis="x", end="spruce_planks")
    entrance(d, 7, gy, Z1, 7, ["Squid Farm", "Build at sea", "level by river", "or ocean"])
    d.sign(6, gy + 2, Z1 - 1, "north", ["Ink sacs in", "the cellar", "chest. Bring:", "nothing"], "spruce")
    # the test puts squids into the pool where they spawn (4 deep water), they must find the sign floor
    d.farm_test(expect={"minecraft:ink_sac": 3}, ticks=6000,
                spawns=[("minecraft:squid", 5, 6, 6, 1), ("minecraft:squid", 8, 7, 8, 1),
                        ("minecraft:squid", 10, 6, 7, 1), ("minecraft:squid", 7, 6, 6, 1)])
    return d


# ================================================================================================ piglins
@design("piglinbarter")
def piglinbarter(pack, rel, L):
    """Piglin barter station (Nether). Fully automatic once loaded with gold.

    Pen: 2x2 (x6..7, z6..7, standing y2..3) for 2-4 ADULT piglins, glass walls, a floor of hoppers (y1).
    Feed: the gold chest (5,5,6) on the deck -> hopper (5,4,6) facing east -> dropper D (6,4,6) facing down in the
    pen ceiling. Clock: redstone torch T (6,4,4) on the block BT (6,4,5) -> dust (6,4,3) -> repeaters (7,4,3),
    (8,4,3) [facing west = input from the west] -> dust (9,4,3) -> repeater (9,4,4) [facing north] -> dust (9,4,5)
    -> repeaters (8,4,5), (7,4,5) [facing east] into BT. Four repeaters at 4 ticks + the torch: BT is powered for
    34 game ticks out of 68; each time it turns on, D (next to BT) drops ONE ingot. An ingot appears right in the
    piglins' reach (above the floor hoppers' pick-up zone), so a piglin that is not busy grabs it first, admires it
    6 s and throws its barter items, which land on the hopper floor. The hoppers run to the chest at (9,1,7).
    One ingot every 3.4 s keeps 2+ piglins busy; if all are busy the ingot falls onto the hoppers and ends up in the
    chest too (put it back in the gold chest). Babies don't barter - use adults. Keep it away from portals."""
    d = Design(pack, rel, size=(13, 16, 14), gy=1, paving="blackstone")
    X1, Z1, X2, Z2, top = 1, 2, 11, 12, 8
    shell(d, X1, Z1, X2, Z2, 2, top, floor="polished_blackstone_bricks", door_x=3,
          windows=[(x, y, Z1) for x in (3, 9) for y in (3, 4)] + [(X1, y, z) for z in (6, 7) for y in (3, 4)]
          + [(X2, y, z) for z in (7, 8) for y in (3, 4)])
    # pen walls and floor
    for x in range(5, 9):
        for z in range(5, 9):
            edge = x in (5, 8) or z in (5, 8)
            d.set(x, 1, z, SB if edge else hopper("east"))
            for y in (2, 3):
                d.set(x, y, z, "glass" if edge else AIR)
            d.set(x, 4, z, "glass")
    for x in (5, 8):
        for z in (5, 8):
            for y in (2, 3):
                d.set(x, y, z, logb("y"))
    d.set(6, 1, 6, hopper("east"))
    d.set(7, 1, 6, hopper("south"))
    d.set(6, 1, 7, hopper("east"))
    d.set(7, 1, 7, hopper("east"))
    d.set(8, 1, 7, hopper("east"))
    d.set(9, 1, 7, chest("west"))
    d.tag(9, 1, 7, "farm_output")
    # feed
    d.set(6, 4, 6, dropper("down"))
    d.set(5, 4, 6, hopper("east"))
    d.set(5, 5, 6, chest("west"))
    d.set(5, 4, 5, "glass")
    # clock plinth (solid) north of the pen
    d.fill(6, 1, 3, 9, 3, 4, "polished_andesite")
    d.fill(9, 1, 5, 9, 3, 5, "polished_andesite")
    d.set(6, 4, 5, "chiseled_stone_bricks")             # BT
    d.set(6, 4, 4, "redstone_wall_torch[facing=north,lit=true]")
    d.set(6, 4, 3, dust(s="side", e="side"))
    d.set(7, 4, 3, repeater("west"))
    d.set(8, 4, 3, repeater("west"))
    d.set(9, 4, 3, dust(w="side", s="side"))
    d.set(9, 4, 4, repeater("north"))
    d.set(9, 4, 5, dust(n="side", w="side"))
    d.set(8, 4, 5, repeater("east"))
    d.set(7, 4, 5, repeater("east"))
    # deck (floor y4, standing y5) on the west side, stairs up from the south
    for x in range(2, 5):
        for z in range(4, 9):
            d.set(x, 4, z, "spruce_planks")
    for (x, z) in ((2, 4), (4, 4), (2, 8), (4, 8)):
        for y in (2, 3):
            d.set(x, y, z, logb("y"))
    d.set(2, 2, 11, stair("spruce", "north"))
    d.set(2, 3, 10, stair("spruce", "north"))
    d.set(2, 4, 9, stair("spruce", "north"))
    for z in (4, 5, 7, 8):
        d.set(4, 5, z, FENCE)
    for x in (2, 3):
        d.set(x, 5, 4, FENCE)
    lantern(d, 3, 7, 6)
    # room: lanterns, gold-block plinth for show, barrel for the loot
    for (x, z) in ((3, 10), (10, 10), (10, 4), (6, 10)):
        lantern(d, x, top - 1, z)
    d.set(10, 2, 7, "barrel[facing=up,open=false]")
    d.set(10, 2, 8, chest("west"))
    d.set(10, 2, 10, "smithing_table")
    d.set(4, 2, 10, "crafting_table")
    for x in (4, 8):
        for z in range(Z1 + 1, Z2):
            d.set(x, top, z, logb("z"))
    d.gable(X1, Z1, X2, Z2, top + 1, axis="x", stairs="spruce_stairs", ridge="spruce_slab", end="spruce_planks")
    entrance(d, 6, 1, Z1, 3, ["Piglin Barter", "Bring: 2-4 adult", "piglins, gold", "ingots (deck)"])
    d.farm_test(expect={"minecraft:gravel": 1}, ticks=6000, dimension="nether",
                inputs={(5, 5, 6): [("minecraft:gold_ingot", 64)]},
                spawns=[("minecraft:piglin", 6, 2, 6, 2), ("minecraft:piglin", 7, 2, 7, 2)])
    return d


# ================================================================================================ villagers
@design("villagerbreeder")
def villagerbreeder(pack, rel, L):
    """Villager breeder (the standard 1.14+ design): breeders and a farmer share a glass room with beds and a crop
    patch; babies leave through a 1-high tunnel and drop into a pen with a tally plate.

    Room x5..9, z8..11 (floor y4, standing y5..6, glass ceiling y7): four beds (z8/z9, along x), a carrot/potato patch
    (z10..11) with two water sources under lily pads, the composter in the west wall (4,5,9). One villager takes the
    composter and farms: it harvests, replants and - once it holds spare food - throws food to the others (vanilla
    food sharing, TradeWithVillager); they also pick up dropped crops. Two villagers with 12 food points each that see
    each other breed in their idle hours (unemployed ones all day) if a free bed exists - one free bed per baby.
    Optional top-up: the button on the gallery (7,7,7) fires the droppers (6,7,8)/(8,7,8) in the ceiling, one bread
    each (3 bread = willing).
    Babies (1 block tall) leave through the 1-high tunnel north of the room (y5, z7) - adults don't fit - and drop
    3 blocks down the chute (7, z6) onto the stone pressure plate in the pen; the plate fires the dropper under it,
    which moves one paper (the tally) towards the chest at (4,1,6). Grown villagers walk out through the pen gate.
    The villagers go in through the fence gate (4,5,11) from the stair landing (villagers can't open gates)."""
    d = Design(pack, rel, size=(13, 18, 16), gy=1, paving="grass_block")
    X1, Z1, X2, Z2, top = 1, 2, 11, 14, 9
    shell(d, X1, Z1, X2, Z2, 2, top, floor="spruce_planks", door_x=3,
          windows=[(x, y, Z1) for x in (7, 8, 9) for y in (3,)] + [(X1, y, z) for z in (6, 11) for y in (3, 4)]
          + [(X2, y, z) for z in (6, 11) for y in (3, 4)] + [(X2, 7, z) for z in (5, 9)])
    # --- solid core under the cells and the plot (x5..10, z6..13, y1..3) and the pen (x5..10, z3..5)
    d.fill(5, 1, 6, 10, 3, 13, SB)
    d.fill(4, 1, 9, 4, 3, 13, SB)
    # pen: x6..10, z3..5, standing y2..3, ceiling y4..5
    for x in range(5, 11):
        for z in range(3, 6):
            d.set(x, 1, z, "spruce_planks")
            d.set(x, 2, z, AIR if x > 5 else "glass")
            d.set(x, 3, z, AIR if x > 5 else "glass")
            d.set(x, 4, z, SB)
            d.set(x, 5, z, SB)
    d.set(5, 2, 4, gate("east"))
    d.set(5, 1, 4, "spruce_planks")
    lantern(d, 10, 3, 3)
    d.set(10, 2, 5, "hay_block[axis=y]")
    # chute (7, z6): plate on the tally dropper, open from y2 to y5, glass sides
    d.set(7, 1, 6, dropper("west"))
    d.set(7, 2, 6, "stone_pressure_plate[powered=false]")
    for y in (3, 4, 5):
        d.set(7, y, 6, AIR)
    for y in (2, 3, 4, 5):
        d.set(6, y, 6, "glass")
        d.set(8, y, 6, "glass")
    d.set(6, 1, 6, hopper("west"))
    d.set(5, 1, 6, hopper("west"))
    d.set(5, 2, 6, "glass")
    d.set(5, 3, 6, "glass")
    d.set(4, 1, 6, chest("east"))
    d.tag(4, 1, 6, "farm_output")
    # tunnel z7: floor y4, open y5, ceiling y6 (gallery floor)
    for x in (6, 7, 8):
        d.set(x, 4, 7, "polished_andesite")
        d.set(x, 5, 7, AIR)
    d.set(5, 5, 7, SB)
    d.set(9, 5, 7, SB)
    d.set(6, 5, 6, SB)
    d.set(8, 5, 6, SB)
    # breeding room x5..9, z8..11: floor y4, standing y5..6, ceiling y7. Four beds (two pairs along x) and a
    # carrot patch with two water sources under lily pads; composter (farmer's job site) in the west wall.
    for x in range(4, 11):
        for z in range(8, 13):
            edge = x in (4, 10) or z == 12
            d.set(x, 4, z, SB)
            for y in (5, 6):
                d.set(x, y, z, ("glass" if 8 <= z <= 11 or 5 <= x <= 9 else SB) if edge else AIR)
            d.set(x, 7, z, SB if edge else "glass")
    for z in (8, 9):
        d.set(5, 4, z, "red_bed[facing=east,occupied=false,part=foot]")
        d.set(6, 4, z, "red_bed[facing=east,occupied=false,part=head]")
        d.set(9, 4, z, "red_bed[facing=west,occupied=false,part=foot]")
        d.set(8, 4, z, "red_bed[facing=west,occupied=false,part=head]")
    crops = ["carrots[age=7]", "carrots[age=4]", "potatoes[age=7]", "carrots[age=2]"]
    for z in (10, 11):
        for x in (5, 6, 8, 9):
            d.set(x, 4, z, "farmland[moisture=7]")
            d.set(x, 5, z, crops[(x + 2 * z) % 4])
        d.set(7, 4, z, WATER)
        d.set(7, 5, z, "lily_pad")
    d.set(4, 5, 9, "composter[level=0]")
    d.set(4, 5, 11, gate("west"))
    d.set(4, 6, 11, "glass")
    for x in (4, 10):
        d.set(x, 4, 8, SB)
    # light for the crops through the glass ceiling (lanterns standing on it)
    for (x, z) in ((5, 10), (9, 10), (7, 9)):
        lantern(d, x, 8, z, hanging=False)
    # droppers for a bread top-up over the beds, the button block between them (pressed from the gallery)
    d.set(6, 7, 8, dropper("down"))
    d.set(8, 7, 8, dropper("down"))
    d.set(7, 7, 8, "chiseled_stone_bricks")
    d.set(7, 7, 7, "stone_button[face=wall,facing=north,powered=false]")
    # gallery y6 (standing y7) over the pen and the tunnel, west part over the aisle
    for x in range(2, 11):
        for z in range(3, 8):
            d.set(x, 6, z, "spruce_planks")
    for x in (2, 3, 4):
        d.set(x, 6, 8, "spruce_planks")
    for x in range(3, 11):
        if x not in (6, 7, 8):
            d.set(x, 7, 7, FENCE)                        # rail in front of the cell wall
    d.set(4, 7, 3, chest("south"))                       # bread store
    d.set(3, 7, 3, "barrel[facing=up,open=false]")
    lantern(d, 9, 7, 4, hanging=False)
    # stairs from the aisle (x2) up to the gallery, landing to the plot gate
    for i, z in enumerate((12, 11, 10, 9, 8)):
        d.set(2, 2 + i, z, stair("spruce", "north"))
    d.set(3, 4, 10, "spruce_planks")
    d.set(3, 4, 11, "spruce_planks")
    d.set(3, 5, 12, FENCE)
    # aisle furniture and lights
    d.set(3, 2, 13, "barrel[facing=up,open=false]")
    d.set(4, 2, 13, "crafting_table")
    for (x, y, z) in ((3, 5, 5), (3, 5, 12), (8, 8, 11), (5, 8, 5)):
        lantern(d, x, y, z)
    for x in (5, 9):
        for z in range(Z1 + 1, Z2):
            d.set(x, top, z, logb("z"))
    d.gable(X1, Z1, X2, Z2, top + 1, axis="x", end="spruce_planks")
    entrance(d, 6, 1, Z1, 3, ["Villager Breeder", "Bring: 2-3 jobless", "villagers (gate", "by the stairs)"])
    d.sign(4, 3, 7, "east", ["Tally: one paper", "per baby landing", "Load paper in", "the dropper"], "spruce")
    # the test: two jobless adults in the room (one takes the composter and only breeds in its idle hours), the gallery
    # button pressed every 200 ticks (bread); at least one baby has to come down the chute onto the tally plate
    d.farm_test(expect={"minecraft:paper": 1}, ticks=11000,
                inputs={(6, 7, 8): [("minecraft:bread", 32)], (8, 7, 8): [("minecraft:bread", 32)],
                        (7, 1, 6): [("minecraft:paper", 64)]},
                presses=[(7, 7, 7)],
                spawns=[("minecraft:villager", 6, 5, 9, 1), ("minecraft:villager", 8, 5, 9, 1)])
    return d


# ================================================================================================ froglights
@design("froglight")
def froglight(pack, rel, L):
    """Froglight farm (Nether, basalt deltas): magma cubes spawn on the roof deck and hop off into the frog pit.

    Deck: blackstone floor y6 (standing y7) around a 5x5 hole, glass parapet 3 high; magma cubes spawn there (they
    spawn at any light level, in basalt deltas). Wandering cubes fall through the hole into the pit (no fall damage
    for magma cubes). Pit: x5..9, z6..10, standing y2..5, glass walls 4 high (frogs jump 2) and a floor of 25
    hoppers. Frogs only eat SMALL (size 1) magma cubes they can walk to: the froglight drops where the cube was, on
    the hoppers, which run to the chest at (9,1,12) in the room. Bring one frog of each kind (temperate -> ochre,
    warm -> pearlescent, cold -> verdant froglight; a frog keeps the variant of the biome it grew up in).
    Big and medium cubes are not eaten: they stay in the pit until they despawn (or kill them to split them)."""
    d = Design(pack, rel, size=(15, 12, 15), gy=1, paving="blackstone")
    X1, Z1, X2, Z2 = 1, 2, 13, 14
    shell(d, X1, Z1, X2, Z2, 2, 5, door_x=7,
          windows=[(x, 3, Z1) for x in (4, 10)] + [(x, 4, Z1) for x in (4, 10)]
          + [(X1, y, z) for z in (6, 10) for y in (3, 4)] + [(X2, y, z) for z in (6, 10) for y in (3, 4)])
    # room floor: bottom slabs (nothing spawns on them)
    for x in range(X1 + 1, X2):
        for z in range(Z1 + 1, Z2):
            d.set(x, 1, z, slab("polished_blackstone"))
    # pit
    for x in range(4, 11):
        for z in range(5, 12):
            edge = x in (4, 10) or z in (5, 11)
            d.set(x, 1, z, SB if edge else hopper("east" if x < 9 else "south"))
            for y in (2, 3, 4, 5):
                d.set(x, y, z, ("glass" if y < 5 else SB) if edge else AIR)
    for x in (4, 10):
        for z in (5, 11):
            for y in (2, 3, 4, 5):
                d.set(x, y, z, logb("y"))
    d.set(9, 1, 11, hopper("south"))
    d.set(9, 1, 12, chest("north"))
    d.tag(9, 1, 12, "farm_output")
    d.door(7, 2, 5, "north", "spruce")
    d.set(7, 4, 5, "glass")
    # deck y6 over the whole building except the hole, glass parapet y7..9 with log posts
    for x in range(X1, X2 + 1):
        for z in range(Z1, Z2 + 1):
            hole = 5 <= x <= 9 and 6 <= z <= 10
            d.set(x, 6, z, AIR if hole else ("polished_blackstone_bricks" if x in (X1, X2) or z in (Z1, Z2)
                                              else "blackstone"))
            if x in (X1, X2) or z in (Z1, Z2):
                for y in (7, 8, 9):
                    d.set(x, y, z, "glass")
    for (x, z) in ((X1, Z1), (X2, Z1), (X1, Z2), (X2, Z2), (7, Z1), (7, Z2), (X1, 8), (X2, 8)):
        for y in (6, 7, 8, 9):
            d.set(x, y, z, logb("y"))
        d.set(x, 10, z, "polished_blackstone_brick_slab[type=bottom,waterlogged=false]")
    d.set(7, 7, 8, AIR)
    # room furniture and light (lanterns under the deck)
    for (x, z) in ((2, 3), (12, 3), (2, 13), (12, 13), (7, 13), (2, 8), (12, 8)):
        lantern(d, x, 5, z)
    d.set(11, 2, 13, "barrel[facing=up,open=false]")
    d.set(10, 2, 13, chest("north"))
    d.set(3, 2, 13, "crafting_table")
    d.set(2, 2, 12, "mud")
    entrance(d, 7, 1, Z1, 7, ["Froglight Farm", "Bring: 3 frogs", "(warm, cold,", "temperate)"])
    # test: frogs in the pit, magma cubes (random sizes: about 1 in 3 is small) put where they land from the deck
    d.farm_test(expect={"minecraft:pearlescent_froglight": 2}, ticks=3000, dimension="nether",
                spawns=[("minecraft:frog", 7, 2, 8, 3), ("minecraft:magma_cube", 6, 2, 7, 9),
                        ("minecraft:magma_cube", 8, 2, 9, 9)])
    return d
