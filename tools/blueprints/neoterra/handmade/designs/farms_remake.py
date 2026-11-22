"""
Farmworks: hand-made remakes of the seven ORIGINAL generated farms (tools/blueprints/neoterra/farms.py), at the same
paths. Java 1.21.1 vanilla mechanics, every one checked in the in-game farm test (handmade/farmtest.sh).

  decorations/mobfarms/ironfarm       villager-pod iron farm: 3 villagers + a zombie scare on a glass deck over a
                                      water-swept golem platform, 2x2 drop into a lava blade, hoppers -> chest
  decorations/mobfarms/cactusfarm     two tiers of 12 cacti that break against fence posts, a water stream carries
                                      the cactus to a hopper row -> chest
  decorations/mobfarms/mobtower       three-floor dark spawning tower (water channels, 25-block drop) -> chests
  decorations/foodfarms/eggfarm       chicken coop floored with hoppers -> chest
  decorations/foodfarms/autokitchen   six-smoker bank: raw food chest + fuel chest -> cooked food chest
  decorations/foodfarms/bonemeal      five-composter line: crops chest -> bone meal chest
  decorations/foodfarms/smeltery      eight-furnace super smelter: ore chest + fuel chest -> ingot chest

Block-state conventions (1.21.1):
  hopper    facing = OUTPUT side (down / north / south / east / west, never up); a hopper pulls from the container
            directly ABOVE it (any container, also another hopper) and pushes into the one it faces.
  furnace / smoker: items pushed in from the TOP go to the input slot, from any SIDE to the fuel slot; a hopper
            UNDER it pulls the result (and empty buckets).
  composter: a hopper above inserts (only from the top, levels 0-6); at level 7 it turns 8 (bone meal ready) 20 ticks
            later and a hopper below pulls the bone meal out, resetting it to 0.
  wall sign facing = the side it faces, away from the block it hangs on.
Only water / lava SOURCE blocks are placed; cells described as "flow" are air in the blueprint and fill with flowing
water in game.

The decoration "smeltery" shares its requirement base name with the colony Smeltery hut (craftsmanship/metallurgy),
so hm.rels_for("smeltery") would hand this farm's path to the hut design (and the hut's paths to this one). This
file re-keys the farm's requirement entry (in memory only) to the base "farmsmeltery" and registers under that.
"""
import hm
from hm import Design, design, AIR

SB = "stone_bricks"
CB = "cobblestone"
MSB = "mossy_stone_bricks"
CSB = "chiseled_stone_bricks"
LOG = "stripped_spruce_log"
GLASS = "glass"
WATER = "water[level=0]"
LAVA = "lava[level=0]"
FENCE = "spruce_fence[east=false,north=false,south=false,waterlogged=false,west=false]"

_SMELTERY = "decorations/foodfarms/smeltery.blueprint"
if _SMELTERY in hm.REQ:
    hm.REQ[_SMELTERY]["base"] = "farmsmeltery"


def logb(axis="y"):
    return f"{LOG}[axis={axis}]"


def slab(b, t="bottom"):
    return f"{b}_slab[type={t},waterlogged=false]"


def stair(b, facing, half="bottom"):
    return f"{b}_stairs[facing={facing},half={half},shape=straight,waterlogged=false]"


def lantern(d, x, y, z, hanging=True):
    d.set(x, y, z, f"lantern[hanging={'true' if hanging else 'false'},waterlogged=false]")


def chest(facing="north", t="single"):
    return f"chest[facing={facing},type={t},waterlogged=false]"


def hopper(facing):
    assert facing != "up"
    return f"hopper[enabled=true,facing={facing}]"


def barrel(f="up"):
    return f"barrel[facing={f},open=false]"


def gate(facing):
    return f"spruce_fence_gate[facing={facing},in_wall=false,open=false,powered=false]"


# ------------------------------------------------------------------------------------------------- shared pieces
def shed(d, X1, Z1, X2, Z2, top, door_x, floor="smooth_stone", posts_every=4, roof=True, roof_y=None,
         windows=(), wall=CB):
    """Stone-brick plinth course, cobble walls up to `top` with stripped-spruce posts and a log beam on top,
    spruce gable roof (ridge along x) with spruce-plank gables, spruce door in the north wall."""
    gy = 1
    for x in range(X1, X2 + 1):
        for z in range(Z1, Z2 + 1):
            d.set(x, gy, z, SB if x in (X1, X2) or z in (Z1, Z2) else floor)
    for y in range(gy + 1, top + 1):
        for x in range(X1, X2 + 1):
            for z in range(Z1, Z2 + 1):
                if x in (X1, X2) or z in (Z1, Z2):
                    d.set(x, y, z, SB if y == gy + 1 else wall)
                else:
                    d.set(x, y, z, AIR)
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
        for y in range(gy + 1, top + 1):
            d.set(x, y, z, logb("y"))
    for (x, y, z) in windows:
        d.set(x, y, z, "glass_pane")
    d.door(door_x, gy + 1, Z1, "south", "spruce")
    if roof:
        d.gable(X1, Z1, X2, Z2, roof_y or top + 1, axis="x", end="spruce_planks")


def approach(d, cx, Z1, lines, x_sign=None, z_path=0):
    """Controller on the north edge, gravel path to the door, lantern posts and the entrance sign."""
    for z in range(z_path, Z1):
        for x in (cx - 1, cx, cx + 1):
            d.set(x, 1, z, "gravel")
    d.hut(cx, 1, 0)
    for x in (cx - 2, cx + 2):
        d.set(x, 2, Z1 - 1, FENCE)
        lantern(d, x, 3, Z1 - 1, hanging=False)
    xs = x_sign if x_sign is not None else cx + 1
    d.sign(xs, 3, Z1 - 1, "north", lines, "spruce")


def tie_beams(d, xs, z1, z2, y, lamps_z=None):
    for x in xs:
        for z in range(z1, z2 + 1):
            d.set(x, y, z, logb("z"))
        for z in (lamps_z or ((z1 + z2) // 2,)):
            lantern(d, x, y - 1, z)


# ================================================================================================ machine bank
def bank(d, x0, n, zF, yF, block, fuel=True):
    """A row of n cookers / composters at (x0..x0+n-1, yF, zF), fronts facing north.

        input : chest (x0, yF+3, zF) -> chain of hoppers (x, yF+2, zF) facing east (the last one down);
                under every chain hopper a hopper (x, yF+1, zF) facing DOWN pulls from it and feeds the block's top.
        fuel  : chest (x0, yF+2, zF+1) -> chain (x, yF+1, zF+1) facing east (the last one down); under each a hopper
                (x, yF, zF+1) facing NORTH pushes into the block's back = fuel slot.
        output: hoppers (x, yF-1, zF) under the blocks pull the results, chained east into the chest
                (x0+n, yF-1, zF) (tagged farm_output).
    The chain hoppers pass on every other item and the hopper under them takes the rest, so the first blocks get the
    most - with a full chest every block gets work. Returns (input chest, fuel chest, output chest) positions."""
    for i in range(n):
        x = x0 + i
        last = i == n - 1
        d.set(x, yF, zF, block)
        d.set(x, yF + 1, zF, hopper("down"))
        d.set(x, yF + 2, zF, hopper("down" if last else "east"))
        d.set(x, yF - 1, zF, hopper("east"))
        if fuel:
            d.set(x, yF, zF + 1, hopper("north"))
            d.set(x, yF + 1, zF + 1, hopper("down" if last else "east"))
    cin = (x0, yF + 3, zF)
    d.set(*cin, chest("west"))
    cf = None
    if fuel:
        cf = (x0, yF + 2, zF + 1)
        d.set(*cf, chest("west"))
    cout = (x0 + n, yF - 1, zF)
    d.set(*cout, chest("north"))
    d.tag(*cout, "farm_output")
    return cin, cf, cout


def loading_steps(d, x, zF, yF, wood="spruce"):
    """Spruce steps up to a landing at (x, yF+1, zF..zF+1) beside the input / fuel chests; the steps run north."""
    top = yF + 1
    for z in (zF, zF + 1):
        d.fill(x, 2, z, x, top - 1, z, SB)
        d.set(x, top, z, f"{wood}_planks")
    k = 1
    for y in range(top - 1, 1, -1):                  # one step per block down, going north
        z = zF - k
        d.set(x, y, z, stair(wood, "south"))
        if y > 2:
            d.fill(x, 2, z, x, y - 1, z, SB)
        k += 1


def bank_hall(d, n, lines, block, fuel, chimney=True, x0=3, extra_w=0):
    """Workshop around a bank: walls X 1..x0+n+2(+extra_w), Z 2..8; bank at z=6 (fuel row z=7), loading steps
    at x0-1 up to a landing beside the input / fuel chests, output chest at the east end of the bank."""
    X1, Z1, X2, Z2 = 1, 2, x0 + n + 2 + extra_w, 8
    zF, yF = 6, 3
    top = 7
    cx = (X1 + X2) // 2
    win = [(x, y, Z1) for x in (X1 + 2, X2 - 2) for y in (3, 4)] + \
          [(X1, y, 4) for y in (3, 4)] + [(X2, y, 4) for y in (3, 4)]
    shed(d, X1, Z1, X2, Z2, top, cx, windows=win)
    # hearth wall behind the bank (z = 7): stone bricks, glass over the hoppers to watch them
    for x in range(x0, x0 + n):
        for y in range(2, top):
            d.set(x, y, zF + 1, SB if y == 2 else (GLASS if y <= yF + 2 else CB))
        for y in range(yF + 4, top):
            d.set(x, y, zF, CB)
    cin, cf, cout = bank(d, x0, n, zF, yF, block, fuel)
    for x in range(x0 + 1, x0 + n):
        d.set(x, yF + 3, zF, slab("spruce"))         # shelf over the chain (only the first hopper has a chest)
        if fuel:
            d.set(x, yF + 2, zF + 1, slab("spruce"))
    loading_steps(d, x0 - 1, zF, yF)
    d.set(x0 + n, yF, zF, AIR)                      # chest lid needs air
    tie_beams(d, range(x0 + 1, X2, 4), Z1 + 1, Z2 - 1, top, lamps_z=(4,))
    if chimney:
        xc = x0 + n // 2
        for y in range(top + 1, top + 6):
            d.set(xc, y, Z2, "bricks")
        d.set(xc, top + 6, Z2, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    approach(d, cx, Z1, lines)
    return cin, cf, cout, (X1, Z1, X2, Z2)


# ================================================================================================ autokitchen
@design("autokitchen")
def autokitchen(pack, rel, L):
    """Auto-smoker kitchen: six smokers fed by hoppers (the super-smelter layout, see bank()).
    Raw food goes into the chest on top of the bank (reached from the loading steps), fuel into the chest behind it;
    cooked food collects in the chest at the east end. Smokers cook any raw meat / fish / potato / kelp in 5 s."""
    d = Design(pack, rel, size=(13, 16, 10), gy=1, paving="grass_block")
    cin, cf, cout, (X1, Z1, X2, Z2) = bank_hall(
        d, 6, ["Auto Kitchen", "raw food: top", "fuel: back chest", "Bring: food+fuel"],
        "smoker[facing=north,lit=false]", True)
    # kitchen dressing: barrels, cauldron sink, crafting table, hanging lanterns
    d.set(X2 - 1, 2, 3, "crafting_table")
    d.set(X2 - 1, 2, 4, barrel("up"))
    d.set(X2 - 1, 3, 4, "potted_fern")
    d.set(X1 + 1, 2, 3, "cauldron")
    d.farm_test(expect={"minecraft:cooked_beef": 12, "minecraft:cooked_porkchop": 6},
                inputs={cin: [("minecraft:beef", 32), ("minecraft:porkchop", 32)],
                        cf: [("minecraft:coal", 16)]}, ticks=6000)
    return d


@design("farmsmeltery")
def smeltery(pack, rel, L):
    """Eight-furnace super smelter (see bank()): ores / sand / raw food into the top chest, fuel into the back
    chest, ingots and glass come out in the chest at the east end."""
    d = Design(pack, rel, size=(14, 16, 10), gy=1, paving="grass_block")
    cin, cf, cout, (X1, Z1, X2, Z2) = bank_hall(
        d, 8, ["Smeltery", "ore/sand: top", "fuel: back chest", "Bring: ore+fuel"],
        "furnace[facing=north,lit=false]", True, x0=3, extra_w=-1)
    d.set(X1 + 1, 2, 3, "anvil[facing=west]")
    d.set(X2 - 1, 2, 3, "smithing_table")
    d.set(X2 - 1, 2, 4, barrel("up"))
    d.farm_test(expect={"minecraft:iron_ingot": 20},
                inputs={cin: [("minecraft:raw_iron", 64)], cf: [("minecraft:coal", 16)]}, ticks=6000)
    return d


# ================================================================================================ bone meal
@design("bonemeal")
def bonemeal(pack, rel, L):
    """Composter line: five composters fed from the crop chest on top through hoppers (see bank(), no fuel row);
    the hoppers under them pull the bone meal into the chest at the east end. Seeds 30 %, wheat / potatoes /
    carrots 65 %, pumpkins / melons 65 %, bread / pie 85-100 % per item to raise a level, 7 levels per bone meal."""
    d = Design(pack, rel, size=(12, 16, 10), gy=1, paving="grass_block")
    cin, cf, cout, (X1, Z1, X2, Z2) = bank_hall(
        d, 5, ["Bone Meal Mill", "crops & seeds", "-> top chest", "Bring: crops"],
        "composter[level=0]", False, chimney=False)
    d.set(X1 + 1, 2, 3, "hay_block[axis=y]")
    d.set(X2 - 1, 2, 3, barrel("up"))
    d.set(X2 - 1, 2, 4, "composter[level=0]")
    d.farm_test(expect={"minecraft:bone_meal": 8}, inputs={cin: [("minecraft:wheat", 192)]}, ticks=6000)
    return d


# ================================================================================================ egg farm
@design("eggfarm")
def eggfarm(pack, rel, L):
    """Hopper-floored chicken coop. The hens stand on a 5x3 floor of hoppers (y2); every egg they lay (one every
    5-10 minutes per hen) lands in the hopper under them and runs along the floor (rows facing north, the front row
    to the middle) into the chest (5,2,5) at the front of the pen. Glass pen 2 high under a plank ceiling, gate at
    the front left."""
    d = Design(pack, rel, size=(11, 12, 11), gy=1, paving="grass_block")
    X1, Z1, X2, Z2, top = 1, 2, 9, 10, 6
    cx = 5
    shed(d, X1, Z1, X2, Z2, top, cx, floor="spruce_planks",
         windows=[(3, 4, Z1), (7, 4, Z1), (X1, 4, 4), (X2, 4, 4), (X1, 4, 7), (X2, 4, 7)])
    # pen: hopper floor x3..7, z6..8; border y2 stone bricks; glass walls y3..4; plank ceiling y5
    for x in range(2, 9):
        for z in range(5, 10):
            edge = x in (2, 8) or z in (5, 9)
            d.set(x, 2, z, SB if edge else hopper("north"))
            for y in (3, 4):
                d.set(x, y, z, GLASS if edge else AIR)
            d.set(x, 5, z, "spruce_planks")
    for x in (3, 4):
        d.set(x, 2, 6, hopper("east"))
    for x in (6, 7):
        d.set(x, 2, 6, hopper("west"))
    d.set(cx, 2, 6, hopper("north"))
    d.set(cx, 2, 5, chest("north"))
    d.tag(cx, 2, 5, "farm_output")
    d.set(3, 3, 5, gate("north"))                       # way in for the hens
    d.set(3, 4, 5, slab("spruce", "top"))
    for x in (2, 8):
        for y in (3, 4):
            d.set(x, y, 5, logb())
            d.set(x, y, 9, logb())
    lantern(d, 5, 4, 7)                                   # hangs from the pen ceiling (hens keep laying at night)
    # nesting shelf look on the pen front: spruce trapdoors under the ceiling
    for x in range(4, 8):
        d.set(x, 5, 4, "spruce_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
    # coop dressing: feed barrel, hay, composter, crafting table
    d.set(2, 2, 3, barrel("up"))
    d.set(2, 2, 4, "hay_block[axis=y]")
    d.set(8, 2, 3, "composter[level=0]")
    d.set(8, 2, 4, "crafting_table")
    lantern(d, 2, 3, 4, hanging=False)
    lantern(d, 8, 3, 4, hanging=False)
    approach(d, cx, Z1, ["Egg Coop", "eggs -> chest", "Bring: 6+ hens", "(seeds to breed)"])
    d.farm_test(expect={"minecraft:egg": 5}, ticks=13000,
                spawns=[("minecraft:chicken", x, 3, z, 1) for (x, z) in ((3, 7), (5, 7), (7, 7), (4, 8), (6, 8),
                                                                         (4, 6))])
    return d


# ================================================================================================ cactus farm
@design("cactusfarm")
def cactusfarm(pack, rel, L):
    """Two tiers of cactus over a water stream.

    Hall floor y2, water at y3: SOURCES along the back row (z = 13), flowing 7 cells north to the hopper row under
    z = 6 (flow, level 7 at the end); the stream carries everything to the hoppers (x2..10, y2, z6 -> towards x6 ->
    chest (6,2,5) in the front wall, opened from the collection room).
    Cactus columns at x 3/5/7/9, z 7/9/11 (no two side by side - a cactus breaks next to a solid block, another
    cactus included): tier 1 = fence (y4, hanging over the water) / sand y5 / cactus y6, tier 2 = fence y8 / sand y9 /
    cactus y10. A fence post at x 4/6/8 at the height where each cactus grows its second block (y7, y11): the new
    block has a solid neighbour and breaks at once (CactusBlock.canSurvive), the item drops beside the column into
    the stream. Every cactus stays one block tall, so it keeps growing."""
    d = Design(pack, rel, size=(13, 20, 16), gy=1, paving="grass_block")
    X1, X2 = 1, 11                     # side walls
    ZR, ZF, ZB = 2, 5, 14              # room north wall / hall front wall (chest) / hall back wall
    top = 13                           # hall ceiling
    # ---- collection room x2..10, z3..4 (floor y1), walls y2..4, beam y5, slab roof y6
    for x in range(X1, X2 + 1):
        for z in range(ZR, ZF):
            edge = x in (X1, X2) or z == ZR
            d.set(x, 1, z, SB if edge else "smooth_stone")
            for y in range(2, 5):
                d.set(x, y, z, (logb() if (x in (X1, X2) and z == ZR) or (z == ZR and x in (4, 8)) else
                                SB if y == 2 else CB) if edge else AIR)
            d.set(x, 5, z, logb("x") if z == ZR else logb("z") if x in (X1, X2) else "spruce_planks")
    for x in range(X1 - 1, X2 + 2):
        for z in range(ZR - 1, ZF):
            d.set(x, 6, z, slab("spruce"))
    for (x, z) in ((3, ZR), (9, ZR)):
        d.set(x, 3, z, "glass_pane")
        d.set(x, 4, z, "glass_pane")
    d.door(6, 2, ZR, "south", "spruce")
    # ---- hall x2..10, z6..13: floor y2, water y3, glass walls with spruce posts up to the ceiling
    for x in range(X1, X2 + 1):
        for z in range(ZF, ZB + 1):
            edge = x in (X1, X2) or z in (ZF, ZB)
            d.set(x, 1, z, SB)
            d.set(x, 2, z, SB)
            for y in range(3, top):
                if not edge:
                    d.set(x, y, z, AIR)
                elif (x in (X1, X2) and (z - ZF) % 3 == 0) or (z == ZB and (x - X1) % 5 == 0):
                    d.set(x, y, z, logb())
                else:
                    d.set(x, y, z, GLASS)
            d.set(x, top, z, logb("z") if x in (X1, X2) else logb("x") if z in (ZF, ZB) else "spruce_planks")
    for x in range(X1 + 1, X2):
        for z in range(ZF + 1, ZB):
            d.set(x, 3, z, WATER if z == ZB - 1 else AIR)        # sources at the back, the rest: flow
        d.set(x, 2, ZF + 1, hopper("east" if x < 6 else "west" if x > 6 else "north"))
    d.set(6, 2, ZF, chest("north"))
    d.tag(6, 2, ZF, "farm_output")
    for x in range(X1 + 1, X2):                                  # the room roof meets the hall's glass front
        d.set(x, 5, ZF, logb("x"))
    # ---- the cactus columns (two tiers) and the breaker fences
    cols = [(x, z) for x in (3, 5, 7, 9) for z in (7, 9, 11)]
    for base in (4, 8):
        for (x, z) in cols:
            d.set(x, base, z, FENCE)
            d.set(x, base + 1, z, "sand")
            d.set(x, base + 2, z, "cactus[age=0]")
        for x in (4, 6, 8):
            for z in (7, 9, 11):
                d.set(x, base + 3, z, FENCE)
    for x in (3, 9):
        lantern(d, x, top - 1, 13)
    # ---- gable roof over the hall (ridge north-south)
    d.gable(X1, ZF, X2, ZB, top + 1, axis="z", end="spruce_planks")
    # ---- room furnishing and entrance
    lantern(d, 3, 4, 3)
    lantern(d, 9, 4, 3)
    d.set(2, 2, 4, barrel("up"))
    d.set(10, 2, 4, "crafting_table")
    approach(d, 6, ZR, ["Cactus Farm", "cactus -> chest", "Bring: nothing", "(smelt: green dye)"])
    d.farm_test(expect={"minecraft:cactus": 8}, ticks=6000)
    return d


# ================================================================================================ mob tower
@design("mobtower")
def mobtower(pack, rel, L):
    """General mob tower (the classic): three dark spawning floors (y0 = 27, 31, 35) of 2-high quadrants with water
    channels into a 2x2 hole; every hostile mob that spawns there (zombies, skeletons, spiders, creepers, witches...)
    walks off into a channel, is carried into the hole and falls 23-31 blocks onto the hoppers in the glass landing
    of the base room - dead. Bones, arrows, rotten flesh, string, gunpowder go to the chests. Distinct from the
    creeper / spider farms (any mob) and from the XP grinder (no XP mode, three floors, fully automatic).
    Built from the tested farms_xp modules (water_floor 'xp', tower, roof_box): see there for the water and fall
    numbers. Works at night and in the dark; the player stays 24-128 blocks away (AFK spot by the base)."""
    from designs import farms_xp as X
    w = 2
    d = Design(pack, rel, size=(20, 44, 22), gy=1, paving="grass_block")
    shaft = (X.HX, X.HZ, X.HX + 1, X.HZ + 1)
    floors = (27, 31, 35)
    X.tower(d, w, shaft, 3, floors[0],
            lines=["Mob Tower", "bones, arrows,", "flesh, string", "Bring: nothing"])
    y = floors[0]
    for y0 in floors:
        y = X.water_floor(d, w, y0, "xp")
        X.band(d, w, y0, CSB if y0 == floors[0] else X.SB)
    X.roof_box(d, w, y)
    # banner flags on the roof corners and a mossy plinth band on the piers
    X1, Z1, X2, Z2 = X.outer(w)
    for (x, z) in ((X1, Z1), (X2, Z1), (X1, Z2), (X2, Z2)):
        for yy in range(2, 5):
            d.set(x, yy, z, MSB if yy == 2 else d.get(x, yy, z))
    # test: zombies and skeletons where they would end up - in the channels of every floor - plus some on floors
    cells = [(3, 5), (6, 8), (13, 5), (16, 8), (3, 15), (6, 18), (13, 15), (16, 18)]
    spawns = [(m, x, y0 + 1, z, 1) for y0 in floors for m in ("minecraft:zombie", "minecraft:skeleton")
              for (x, z) in X.CHANNEL]
    spawns += [("minecraft:skeleton", x, floors[1] + 2, z, 1) for (x, z) in cells[::2]]
    d.farm_test(expect={"minecraft:rotten_flesh": 2, "minecraft:bone": 2, "minecraft:arrow": 1}, spawns=spawns,
                ticks=6000)
    return d


# ================================================================================================ iron farm
# Golem spawning (1.21.1 Villager.spawnGolemIfNeeded / SpawnUtil LEGACY_IRON_GOLEM): a villager that sees a hostile
# within 8 blocks panics; while panicking it tries every 100 ticks - if it and 2 more villagers within 10 blocks
# slept in a bed in the last 24000 ticks and none saw a golem in the last 600 - 10 spawn attempts: a random column
# within +-8 x/z of the villager, scanned DOWN from villager y+6 to y-6 for the FIRST spot with air/liquid on a
# solid block that is not glass / glass pane (/ ice, leaves, glowstone, sea lantern...); the golem appears there
# if the block below has a full top and the two above are free. Everything within reach of that scan except the
# golem platform is therefore glass, glass pane, a bottom slab / stair / bed / fence (no full top) or a column that
# runs on up to y+6 (see ironfarm()).
IV = 15                                      # villagers' feet (pod floor y14)


@design("ironfarm")
def ironfarm(pack, rel, L):
    """Iron golem farm (the 1.21 villager-pod design). Platform 20x20, floor y10, glass walls; villager deck y14-18
    with a timber roof from y21.

    Villager deck (feet y15): three 1x1 villager pods west / north / east of the zombie cell (9,15,9); each pod has
    its bed head right beside the villager and a workstation. Between pod and zombie: fence / air / fence. A fence
    is 1.5 high, the villagers' eyes (1.62) and the zombie's (1.74) are above it, so they see each other across the
    two fences and the gap, but neither can reach the other (4 blocks). The zombie cell has a stone-brick ceiling
    (no sun). Iron doors (buttons outside) let the player put the villagers and the zombie in from the glass
    gallery around the deck (ladder on the east wall). Every floor up here is glass (no golem can spawn on glass)
    and every ceiling is glass, so the spawn scan falls through to the platform.
    Golem platform (floor y10, golems at y11, 3 clear up to the deck): water SOURCES along all four walls (x = 1,
    18, z = 1, 18; not in the corners, where a cell between two sources would become a source), the rest flows
    inward (air in the blueprint). The 2x2 hole (9..10, 9..10) is 7 cells from the
    sources, so the water next to it is the weakest (level 7) and never pours in. Golems are carried to the middle
    and fall through the lava blade: lava sources in the hole at y10 (held up by crimson wall signs at y9 - lava
    cannot flow into a sign - and by the platform floor around), golem at y8 in the 2x2 kill chamber with its head
    in the lava. Iron and poppies land on the 4 hoppers (y7, items stay 2 blocks under the lava) -> hopper column
    -> chest (10,2,9) in the room under the platform.
    Rate: one golem about every 700-900 ticks while the villagers can see the zombie in daylight (they must sleep
    every night - the beds are in the pods - and are panicked by the zombie during the day)."""
    d = Design(pack, rel, size=(21, 28, 20), gy=1, paving="grass_block")
    P = 10                                     # platform floor
    HX, HZ = 9, 9                              # hole north-west cell
    # ---------------------------------------------------------------- room under the platform (y2..9)
    RZ1 = 3
    for x in range(0, 20):
        for z in range(RZ1, 20):
            edge = x in (0, 19) or z in (RZ1, 19)
            d.set(x, 1, z, SB if edge else "smooth_stone")
            for y in range(2, P):
                if edge:
                    post = (x in (0, 19) and (z - RZ1) % 4 == 0) or (z in (RZ1, 19) and x % 5 == 0) or \
                           (x in (0, 19) and z == 19)
                    d.set(x, y, z, logb() if post else (SB if y == 2 or y == P - 1 else CB))
                else:
                    d.set(x, y, z, AIR)
    for (x, z) in ((0, 0), (19, 0)):          # porch pillars under the platform's north edge
        for y in range(1, P):
            d.set(x, y, z, SB if y in (1, P - 1) else logb())
    for x in range(0, 20):
        d.set(x, P - 1, 0, logb("x"))
    # windows into the room
    for (x, z) in ((3, RZ1), (4, RZ1), (15, RZ1), (16, RZ1), (0, 7), (0, 14), (19, 14), (7, 19), (12, 19)):
        for y in (4, 5):
            d.set(x, y, z, "glass_pane")
    d.door(10, 2, RZ1, "south", "spruce")
    # ---------------------------------------------------------------- platform y10 + glass walls + water
    for x in range(0, 20):
        for z in range(0, 20):
            d.set(x, P, z, SB if x in (0, 19) or z in (0, 19) else "smooth_stone")
            edge = x in (0, 19) or z in (0, 19)
            for y in range(P + 1, P + 4):
                d.set(x, y, z, GLASS if edge else AIR)
            # sources along the walls but not in the corners: a cell next to TWO sources (the inner corner cell)
            # would turn into a source itself and the whole platform would fill with sources
            if not edge and ((x in (1, 18) and 3 <= z <= 16) or (z in (1, 18) and 3 <= x <= 16)):
                d.set(x, P + 1, z, WATER)
    # ---------------------------------------------------------------- hole, lava blade, kill chamber, collection
    hole = [(HX, HZ), (HX + 1, HZ), (HX, HZ + 1), (HX + 1, HZ + 1)]
    for x in range(HX - 1, HX + 3):
        for z in range(HZ - 1, HZ + 3):
            inside = (x, z) in hole
            d.set(x, P - 3, z, SB)                                 # under the hoppers / chamber ring
            d.set(x, P - 2, z, AIR if inside else GLASS)           # chamber (golem feet y8), glass to watch
            d.set(x, P - 1, z, AIR if inside else GLASS)           # wall signs hang on this ring
    for (x, z) in hole:
        d.set(x, P, z, LAVA)
        d.set(x, P + 1, z, AIR)
        face = "east" if x == HX else "west"                       # sign on the outer (west / east) chamber wall
        d.set(x, P - 1, z, f"crimson_wall_sign[facing={face},waterlogged=false]")
    d.set(HX, P - 3, HZ, hopper("east"))
    d.set(HX, P - 3, HZ + 1, hopper("east"))
    d.set(HX + 1, P - 3, HZ + 1, hopper("north"))
    d.set(HX + 1, P - 3, HZ, hopper("down"))
    for y in range(3, P - 3):
        d.set(HX + 1, y, HZ, hopper("down"))
    d.set(HX + 1, 2, HZ, chest("north"))
    d.tag(HX + 1, 2, HZ, "farm_output")
    # stone-brick casing round the hopper column (open to the north so the chest can be reached)
    for y in range(2, P - 3):
        for (x, z) in ((HX, HZ), (HX + 2, HZ), (HX, HZ + 1), (HX + 1, HZ + 1), (HX + 2, HZ + 1)):
            d.set(x, y, z, SB if y in (2, P - 4) else logb() if (x, z) in ((HX, HZ), (HX + 2, HZ)) else CB)
    # room furniture and light
    for (x, z) in ((4, 6), (15, 6), (4, 15), (15, 15), (9, 15)):
        lantern(d, x, P - 1, z)
    d.set(1, 2, 18, barrel("up"))
    d.set(2, 2, 18, barrel("up"))
    d.set(18, 2, 18, "crafting_table")
    d.set(17, 2, 18, "anvil[facing=north]")
    d.set(1, 2, 4, "smithing_table")
    # ---------------------------------------------------------------- villager deck (floor y14, pods y15-17)
    Y = IV
    FLOOR, CEIL = Y - 1, Y + 3                 # 14 glass floor, 18 glass ceiling
    BX1, BZ1, BX2, BZ2 = 4, 4, 14, 10          # pod block
    A = (9, 9)
    S1, S2, S3 = (5, 9), (9, 5), (13, 9)       # the villagers stand ON their bed heads
    fences = [(8, 9), (6, 9), (9, 8), (9, 6), (10, 9), (12, 9)]
    gaps = [(7, 9), (9, 7), (11, 9)]
    beds = [(S1, (5, 8), "south"), (S2, (10, 5), "west"), (S3, (13, 8), "south")]
    work = [((5, 10), "fletching_table"), ((8, 5), "fletching_table"), ((13, 10), "cartography_table")]
    for x in range(BX1, BX2 + 1):
        for z in range(BZ1, BZ2 + 1):
            d.set(x, FLOOR, z, GLASS)
            d.set(x, CEIL, z, GLASS)
            post = (x in (BX1, BX2) and z in (BZ1, BZ2))
            for y in (Y, Y + 1, Y + 2):
                d.set(x, y, z, logb() if post else "spruce_planks")
    for c in (A, *gaps):
        for y in (Y, Y + 1, Y + 2):
            d.set(c[0], y, c[1], AIR)
    for (x, z) in fences:
        d.set(x, Y, z, FENCE)
        d.set(x, Y + 1, z, AIR)
        d.set(x, Y + 2, z, AIR)
    for (head, foot, facing) in beds:
        d.set(head[0], Y, head[1], f"green_bed[facing={facing},occupied=false,part=head]")
        d.set(foot[0], Y, foot[1], f"green_bed[facing={facing},occupied=false,part=foot]")
        d.set(head[0], Y + 1, head[1], AIR)    # villager on the bed: 0.56 + 1.95 -> 3 high
        d.set(head[0], Y + 2, head[1], AIR)    # (planks stay over the foot: it cannot stand there)
    for (c, blk) in work:
        d.set(c[0], Y, c[1], blk)
    d.set(A[0], Y + 2, A[1], SB)               # the zombie's sun shade (2-high cell), glass ceiling over it
    # night blinds: a panicking villager never goes to bed (only VillagerCalmDown - no hostile in sight - hands it
    # back to its schedule), so the zombie must be hidden at night. In each arm the sight line crosses the fence
    # cell next to the pod (D') at y17 (eyes 17.18 on the bed -> 16.74). A sticky piston in the arm's side wall
    # at y17 holds a plank in that cell; the daylight detector on top of the piston powers it by day, the piston
    # pushes the plank on into a niche and only its arm (y 17.375-17.625, above the sight line) and its head plate
    # (the far quarter of the cell, beside the sight line) stay in the cell. At dusk the detector goes to 0, the
    # piston pulls the plank back: no zombie in sight, the villagers calm down and sleep; at dawn it opens again.
    blinds = [((6, 8), "south"), ((8, 6), "east"), ((12, 8), "south")]
    for ((x, z), f) in blinds:
        dx, dz = {"south": (0, 1), "east": (1, 0)}[f]
        d.set(x, Y + 2, z, "spruce_planks")  # PROBE: blinds fixed closed
        d.set(x + dx, Y + 2, z + dz, "spruce_planks")                  # the blind (in the sight line at night)
        d.set(x + 2 * dx, Y + 2, z + 2 * dz, AIR)                       # niche it is pushed into by day
        d.set(x, CEIL, z, GLASS)
    # iron doors (villagers cannot open them) with a button on the gallery side
    doors = [((4, 9), "west", (4, 10)), ((9, 4), "north", (8, 4)), ((14, 9), "east", (14, 10)),
             ((9, 10), "south", (10, 10))]
    for ((x, z), f, (bx, bz)) in doors:
        d.door(x, Y, z, f, "iron")
        dx, dz = {"west": (-1, 0), "north": (0, -1), "east": (1, 0), "south": (0, 1)}[f]
        d.set(bx + dx, Y + 1, bz + dz, f"stone_button[face=wall,facing={f},powered=false]")
        d.set(x, Y + 2, z, "spruce_planks")
    # gallery ring around the pod block (glass floor y14, glass-pane railing), bridge east to the ladder
    GX1, GZ1, GX2, GZ2 = 3, 3, 15, 11
    for x in range(GX1, GX2 + 1):
        for z in range(GZ1, GZ2 + 1):
            if x in (GX1, GX2) or z in (GZ1, GZ2):
                d.set(x, FLOOR, z, GLASS)
    for x in range(GX1 - 1, GX2 + 2):
        for z in range(GZ1 - 1, GZ2 + 2):
            if (x in (GX1 - 1, GX2 + 1) or z in (GZ1 - 1, GZ2 + 1)) and not (x == GX2 + 1 and z == 7):
                d.set(x, FLOOR, z, GLASS)
                d.set(x, Y, z, "glass_pane")
    for x in range(GX2 + 1, 20):
        d.set(x, FLOOR, 7, GLASS)
        if x > GX2:
            d.set(x, Y, 6, "glass_pane")
            d.set(x, Y, 8, "glass_pane")
            d.set(x, FLOOR, 6, GLASS)
            d.set(x, FLOOR, 8, GLASS)
    for y in range(2, FLOOR + 1):
        d.set(20, y, 7, "ladder[facing=east,waterlogged=false]")
    d.set(19, Y, 7, AIR)
    # roof posts from the gallery corners up to the roof beam (y21) - unbroken columns, nothing to spawn on
    RT = 21
    corners = [(GX1 - 1, GZ1 - 1), (GX2 + 1, GZ1 - 1), (GX1 - 1, GZ2 + 1), (GX2 + 1, GZ2 + 1),
               (9, GZ1 - 1), (9, GZ2 + 1)]
    for (x, z) in corners:
        for y in range(Y, RT):
            d.set(x, y, z, logb())
    for x in range(GX1 - 1, GX2 + 2):
        for z in (GZ1 - 1, GZ2 + 1):
            d.set(x, RT, z, logb("x"))
    for z in range(GZ1 - 1, GZ2 + 2):
        for x in (GX1 - 1, GX2 + 1):
            d.set(x, RT, z, logb("z"))
    d.gable(GX1 - 1, GZ1 - 1, GX2 + 1, GZ2 + 1, RT + 1, axis="x", end="spruce_planks")
    for x in range(GX1, GX2 + 1, 4):
        for z in range(GZ1, GZ2 + 1):
            d.set(x, RT, z, logb("z"))
        for z in (5, 9):
            lantern(d, x, RT - 1, z)
    # ---------------------------------------------------------------- entrance
    approach(d, 10, RZ1, ["Iron Farm", "Bring: 3 villagers", "+ 1 zombie (name", "tag), ladder east"])
    d.sign(9, 3, RZ1 - 1, "north", ["Doors on the", "glass deck: one", "villager per pod,", "zombie in middle"],
           "spruce")
    # test: three villagers in their pods, the zombie in its cell. They claim the beds, sleep the first night
    # (run tick ~11000) and from the morning (~23000) the zombie makes them spawn golems.
    # PROBE (temporary): night detector
    d.set(20, 2, 15, "daylight_detector[inverted=false,power=0]")
    d.set(20, 2, 16, "dropper[facing=south,triggered=false]")
    d.set(20, 2, 17, chest("north"))
    d.tag(20, 2, 17, "farm_output")
    for (x, z) in ((8, 9), (9, 8), (10, 9)):
        d.set(x, 16, z, "stone")      # PROBE seal
    d.set(4, 15, 8, "observer[facing=east,powered=false]")
    d.set(3, 15, 8, "dropper[facing=down,triggered=false]")
    d.set(3, 14, 8, chest("north"))
    d.tag(3, 14, 8, "farm_output")
    d.set(6, 17, 11, "observer[facing=north,powered=false]")
    d.set(6, 17, 12, "dropper[facing=down,triggered=false]")
    d.set(6, 16, 12, chest("north"))
    d.tag(6, 16, 12, "farm_output")
    d.farm_test(expect={"minecraft:iron_ingot": 6, "minecraft:stick": 1, "minecraft:bone": 1, "minecraft:feather": 1}, inputs={(20, 2, 16): [("minecraft:stick", 64)], (3, 15, 8): [("minecraft:bone", 64)], (6, 17, 12): [("minecraft:feather", 64)]},
                spawns=[("minecraft:villager", x, Y, z, 1) for (x, z) in (S1, S2, S3)] +
                       [("minecraft:zombie", A[0], Y, A[1], 1)], ticks=27000,
                blocks=[(9, 10, 9, "minecraft:lava"), (10, 10, 10, "minecraft:lava"), (9, 9, 9, "minecraft:crimson_wall_sign"),
                        (8, 11, 9, "minecraft:water"), (9, 11, 8, "minecraft:water"), (4, 11, 4, "minecraft:water"),
                        (9, 11, 9, "minecraft:air"), (9, 8, 9, "minecraft:air"), (9, 7, 9, "minecraft:hopper")])
    return d
