"""
Farmworks crafting stations (decorations/craftfarms/): auto bakery, nugget compactor, item sorter, super smelter.
Vanilla Java 1.21.1 mechanics, checked against the decompiled 1.21.1 code (CrafterBlock / CrafterBlockEntity,
ComparatorBlock, RedStoneWireBlock, HopperBlockEntity).

Block-state conventions used here:
  comparator  facing = the side its INPUT is on (DiodeBlock reads pos.relative(facing)); output on the opposite side.
              mode=subtract: out = back - max(side); compare: out = back unless side > back.
  hopper      facing = output direction (down / sideways, never up); enabled=false while powered (locked).
  crafter     orientation = <front>_<top>; the front is where the result goes (into a container there, else dropped).
  redstone_wire  connections are recomputed by the game when it signals; the ones written here are what it shows.

THE CRAFTER PATTERN PROBLEM. A crafter's recipe grid is simply what is in its 9 slots; locked ("disabled") slots
live in the block entity (int array "disabled_slots"). The colony builder may or may not copy that NBT, and the farm
test places bare block states (no block-entity data at all). So none of these stations relies on locked slots:
  * a hopper fills a crafter EVENLY - CrafterBlockEntity.canPlaceItem refuses a slot while a later free slot is
    empty (smallerStackExist), so items go to slot 0, 1, 2, ... one by one;
  * a comparator reading a crafter outputs the number of non-empty (or locked) slots (getRedstoneSignal);
  * so "craft when N slots are filled" makes the recipe without any preset pattern:
        N = 3  ->  wheat in slots 0,1,2 = the top row = BREAD
        N = 9  ->  9 nuggets = ingot, 9 ingots = block (any 3x3 recipe)
    The comparator's signal runs B (strongly powered block) -> dust on B -> dust on X (one up) -> dust on top of
    the crafter (one down); every dust step costs 1, so the crafter sees (signal - 2). For N = 3 the comparator
    compares (3 - 2 = 1 at the third item, 0 before). For N = 9 it subtracts a constant 6 (a second comparator
    reading a COMPOSTER at level 6 into its side): 9 - 6 - 2 = 1, 8 items -> 0.
    The crafter fires on the rising edge (TRIGGERED), crafts 4 game ticks later; the hopper feeding it moves one
    item per 8 ticks, so the grid is crafted and empty again before the next item arrives.
  The player must NOT lock any crafter slot (a locked slot counts in the comparator signal) - the signs say so.
"""
from hm import Design, design, AIR

SB = "stone_bricks"
CB = "cobblestone"
LOG = "stripped_spruce_log"
PA = "polished_andesite"
FENCE = "spruce_fence[east=false,north=false,south=false,waterlogged=false,west=false]"


def logb(axis="y"):
    return f"{LOG}[axis={axis}]"


def lantern(d, x, y, z, hanging=True):
    d.set(x, y, z, f"lantern[hanging={'true' if hanging else 'false'},waterlogged=false]")


def chest(facing="north"):
    return f"chest[facing={facing},type=single,waterlogged=false]"


def hopper(f):
    return f"hopper[enabled=true,facing={f}]"


def comparator(facing, mode="compare"):
    return f"comparator[facing={facing},mode={mode},powered=false]"


def wire(n="none", e="none", s="none", w="none"):
    return f"redstone_wire[east={e},north={n},power=0,south={s},west={w}]"


WIRE_X = wire(e="side", w="side")
WIRE_Z = wire(n="side", s="side")


def crafter(front="down", top="north"):
    o = f"{front}_{top}" if front in ("down", "up") else f"{front}_up"
    return f"crafter[crafting=false,orientation={o},triggered=false]"


# ------------------------------------------------------------------------------------------------ the shed
def shed(d, X1, Z1, X2, Z2, top, door_x, floor="smooth_stone", windows_front=(), windows_side=(), win_y=(3, 4)):
    """Stone-brick plinth, cobble walls with stripped-spruce posts and a log beam on top, gable roof (ridge along x)
    with spruce gable ends, spruce door in the north wall."""
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
        posts.add((x, Z1))
        posts.add((x, Z2))
    for z in range(Z1 + 4, Z2 - 1, 4):
        posts.add((X1, z))
        posts.add((X2, z))
    for x in range(X1, X2 + 1):
        for z in (Z1, Z2):
            d.set(x, top, z, logb("x"))
    for z in range(Z1, Z2 + 1):
        for x in (X1, X2):
            d.set(x, top, z, logb("z"))
    for (x, z) in posts:
        for y in range(gy + 1, top + 1):
            d.set(x, y, z, logb("y"))
    for (x, z) in list(windows_front) + list(windows_side):
        for y in win_y:
            d.set(x, y, z, "glass_pane")
    d.door(door_x, gy + 1, Z1, "south", "spruce")
    d.gable(X1, Z1, X2, Z2, top + 1, axis="x", end="spruce_planks")


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


def tie_beams(d, xs, z1, z2, y, lamps=True):
    for x in xs:
        for z in range(z1, z2 + 1):
            d.set(x, y, z, logb("z"))
        if lamps:
            lantern(d, x, y - 1, (z1 + z2) // 2)


# ------------------------------------------------------------------------------------------------ crafter module
def crafter_module(d, x0, y0, z0, need, front="down", top="north", lamp=True):
    """Crafter C at (x0,y0,z0) that crafts as soon as `need` (3 or 9) of its slots are filled (see module doc).

        C  (x0,  y0,  z0)    crafter, result out of `front`
        K  (x0+1,y0,  z0)    comparator facing west (reads C), compare (need 3) / subtract (need 9)
        B  (x0+2,y0,  z0)    redstone lamp, strongly powered by K (lights while the crafter fires)
        X  (x0+1,y0+1,z0)    block on top of K
        D1 (x0+2,y0+1,z0)    dust on B: K-6/K;  D2 (x0+1,y0+2,z0) dust on X: -1;  D3 (x0,y0+1,z0) dust on C: -2
      need 9 only:
        K2 (x0+1,y0,z0-1)    comparator facing north reading the composter, output south into K's side (6)
        CP (x0+1,y0,z0-2)    composter[level=6] - the constant
    Feed: a hopper on the west (x0-1,y0,z0) facing east. Never a hopper UNDER a crafter: it would pull items back
    out of the grid (the crafter does not refuse extraction) - results go into a barrel below or sideways into a
    hopper. Keep air / plain blocks at
    (x0+3,y0+1,z0), (x0+1,y0,z0+1), (x0+2,y0,z0+-1), (x0+3,y0,z0), and nothing powered next to C."""
    d.set(x0, y0, z0, crafter(front, top))
    d.set(x0 + 1, y0, z0, comparator("west", "subtract" if need == 9 else "compare"))
    d.set(x0 + 1, y0 - 1, z0, PA)
    d.set(x0 + 2, y0, z0, "redstone_lamp[lit=false]" if lamp else PA)
    d.set(x0 + 2, y0 - 1, z0, PA)
    d.set(x0 + 1, y0 + 1, z0, PA)
    d.set(x0 + 2, y0 + 1, z0, wire(e="side", w="up"))
    d.set(x0 + 1, y0 + 2, z0, WIRE_X)
    d.set(x0, y0 + 1, z0, wire(e="up", w="side"))
    for (x, y) in ((x0 + 2, y0 + 2), (x0, y0 + 2)):        # the dust steps need air above the lower dust
        d.set(x, y, z0, AIR)
    if need == 9:
        d.set(x0 + 1, y0, z0 - 1, comparator("north"))
        d.set(x0 + 1, y0 - 1, z0 - 1, PA)
        d.set(x0 + 1, y0, z0 - 2, "composter[level=6]")
        d.set(x0 + 1, y0 - 1, z0 - 2, PA)


# ================================================================================================ auto bakery
@design("autobread")
def autobread(pack, rel, L):
    """Auto bakery: wheat chest -> hopper -> crafter that fires at 3 filled slots (= top row = bread) -> barrel.

    Per bench (x0 = 4 and 10): wheat chest (x0-1,4,6) over the feed hopper (x0-1,3,6) -> crafter (x0,3,6) facing
    down into the bread barrel (x0,2,6). Comparator (x0+1,3,6) reads the crafter; dust (x0+2,4,6) -> (x0+1,5,6) ->
    (x0,4,6) on the crafter = signal - 2, so the crafter fires exactly when the third wheat lands in slot 2."""
    d = Design(pack, rel, size=(15, 12, 12), gy=1, paving="grass_block")
    X1, Z1, X2, Z2, top = 1, 2, 13, 9, 6
    cx = 7
    shed(d, X1, Z1, X2, Z2, top, cx, windows_front=[(3, Z1), (4, Z1), (10, Z1), (11, Z1)],
         windows_side=[(X1, 4), (X2, 4)])
    # back counter along the south wall
    d.fill(2, 2, 7, 12, 2, 8, SB)
    d.fill(2, 3, 8, 12, 5, 8, CB)
    for x in range(2, 13):
        d.set(x, 2, 7, PA)
    ins = []
    for x0 in (4, 10):
        hx = x0 - 1
        crafter_module(d, x0, 3, 6, 3)
        d.set(hx, 3, 6, hopper("east"))
        d.set(hx, 2, 6, SB)
        d.set(hx, 4, 6, chest("north"))
        ins.append((hx, 4, 6))
        d.set(x0, 2, 6, "barrel[facing=north,open=false]")
        d.tag(x0, 2, 6, "farm_output")
        d.set(x0 + 1, 2, 6, SB)
        d.set(x0 + 2, 2, 6, SB)
        d.set(x0 + 3, 2, 6, SB) if x0 + 3 < X2 else None
        d.set(x0 + 3, 3, 6, "glass") if x0 + 3 < X2 else None
        d.sign(x0 + 1, 3, 5, "north", ["Wheat: chest", "Bread: barrel", "Never lock", "crafter slots!"], "spruce")
    d.set(2, 2, 6, SB)
    d.set(2, 3, 6, "glass")
    # front corners: work bench and a smoker
    d.set(2, 2, 3, "crafting_table")
    d.set(2, 2, 4, "barrel[facing=up,open=false]")
    d.set(12, 2, 3, "smoker[facing=west,lit=false]")
    d.set(12, 2, 4, "hay_block[axis=y]")
    d.set(12, 3, 4, "hay_block[axis=y]")
    tie_beams(d, (7,), 3, 8, top)
    approach(d, cx, Z1, ["Auto Bakery", "Bring: wheat", "(top chests)", "3 wheat = bread"])
    d.farm_test(expect={"minecraft:bread": 60}, ticks=2400,
                inputs={p: [("minecraft:wheat", 64), ("minecraft:wheat", 64)] for p in ins})
    return d


# ================================================================================================ compactor
@design("compactor")
def compactor(pack, rel, L):
    """Nugget compactor: two lines (iron, gold) of two crafters each that fire when all 9 slots are filled.

    Line at x = a (a = 2 iron, a = 10 gold):
        nugget chest (a,5,6) -> hopper (a,4,6) -> crafter C1 (a+1,4,6) [9 nuggets -> ingot] facing south into the
        hopper (a+1,4,7) -> chain (a+1,3,7..9) -> crafter C2 (a+2,3,9) [9 ingots -> block] down into the block
        barrel (a+2,2,9),
        opened from the back aisle (z10). An ingot chest (a+1,4,9) over the last chain hopper feeds C2 directly.
    Each crafter has the subtract comparator + composter(level 6) circuit described at the top of the file."""
    d = Design(pack, rel, size=(19, 13, 14), gy=1, paving="grass_block")
    X1, Z1, X2, Z2, top = 1, 2, 17, 12, 7
    cx = 9
    shed(d, X1, Z1, X2, Z2, top, cx, windows_front=[(3, Z1), (4, Z1), (14, Z1), (15, Z1)],
         windows_side=[(X1, 4), (X2, 4), (X1, 9), (X2, 9)])
    ins = {}
    for a, metal in ((2, "iron"), (10, "gold")):
        # stage 1: nuggets -> ingot
        crafter_module(d, a + 1, 4, 6, 9, front="south")      # out sideways: a hopper UNDER a crafter would
        d.set(a + 1, 4, 7, hopper("down"))                    # pull the nuggets back out of its grid
        d.set(a + 1, 3, 6, PA)
        d.set(a, 4, 6, hopper("east"))
        d.set(a, 3, 6, PA)
        d.set(a, 2, 6, SB)
        d.set(a, 5, 6, chest("north"))
        ins[(a, 5, 6)] = [(f"minecraft:{metal}_nugget", 64)] * 3
        # chain down to stage 2
        for z in (7, 8):
            d.set(a + 1, 3, z, hopper("south"))
        for z in (6, 7, 8):
            d.set(a + 1, 2, z, SB)
        d.set(a + 1, 3, 9, hopper("east"))
        d.set(a + 1, 2, 9, SB)
        d.set(a + 1, 4, 9, chest("south"))
        ins[(a + 1, 4, 9)] = [(f"minecraft:{metal}_ingot", 27)]
        # stage 2: ingots -> block
        crafter_module(d, a + 2, 3, 9, 9)
        d.set(a + 2, 2, 9, "barrel[facing=south,open=false]")
        d.tag(a + 2, 2, 9, "farm_output")
        # glass screens around the redstone
        d.set(a + 5, 2, 9, SB)
        d.set(a + 5, 3, 9, "glass")
        d.set(a + 2, 2, 8, SB)
        d.set(a + 2, 3, 8, "glass")
        d.sign(a, 3, 5, "north", [f"{metal.title()} nuggets", "in this chest", "-> ingots", "-> blocks"], "spruce")
    # back aisle z = 10..11, reached along the middle corridor (x 8..9)
    d.sign(9, 3, 11, "north", ["Ingots: lower", "chests. Blocks:", "barrels. Never", "lock crafter slots"],
           "spruce")
    d.set(9, 2, 11, "crafting_table")
    tie_beams(d, (9,), 3, 11, top)
    approach(d, cx, Z1, ["Compactor", "Bring: iron and", "gold nuggets", "(or ingots)"])
    d.farm_test(expect={"minecraft:iron_block": 5, "minecraft:gold_block": 5}, ticks=3000, inputs=ins)
    return d


# ================================================================================================ item sorter
SORT = [("iron_ingot", "Iron ingots"), ("gold_ingot", "Gold ingots"), ("copper_ingot", "Copper ingots"),
        ("coal", "Coal"), ("redstone", "Redstone")]


@design("itemsorter")
def itemsorter(pack, rel, L):
    """Hopper-line item sorter, 41-item filter technique, five sorted chests plus an overflow chest.

    Stream: input chest (1,6,6) -> hopper line (1..16,5,6) facing east -> (17,5..3,6) down -> overflow chest.
    One slice per sorted item at x = 2, 5, 8, 11, 14 (z6 = filter row, chests face the north aisle):
        F  (x,4,6)    filter hopper under the stream, facing north (into air: it never pushes). Holds 41 of the
                      item in slot 1 and one filler in each other slot, so it only accepts that item.
                      Comparator signal = 1 + 14*(41+4)/320 = 2 (floor); with a 42nd item 3.
        G  (x,3,6)    hopper under F, facing down into the chest (x,2,6); LOCKED normally, pulls 1 when unlocked.
        K' (x,4,7)    comparator facing north, reads F -> dust (x,4,8) [s] -> (x+1,3,8) [s-1] -> (x+1,3,7) [s-2]
                      -> side of K.
        K  (x+1,3,6)  comparator facing east, SUBTRACT, back = composter[level=1] at (x+2,3,6), output west into G:
                      out = 1 - (s-2)  ->  1 (G locked) while F holds 41, 0 (G unlocked) when the 42nd arrives;
                      G takes that one item (slot 1 first) and locks again. No torch, so no torch burn-out.
    Filler items: any item that never travels down the line (a renamed stick); the test uses plain sticks."""
    d = Design(pack, rel, size=(19, 13, 11), gy=1, paving="grass_block")
    X1, Z1, X2, Z2, top = 0, 2, 18, 9, 7
    cx = 9
    shed(d, X1, Z1, X2, Z2, top, cx, windows_front=[(3, Z1), (4, Z1), (14, Z1), (15, Z1)],
         windows_side=[(X1, 4), (X2, 4)])
    # the stream
    for x in range(1, 17):
        d.set(x, 5, 6, hopper("east"))
    d.set(1, 6, 6, chest("north"))
    d.set(1, 4, 6, PA)
    d.set(1, 3, 6, PA)
    d.set(1, 2, 6, SB)
    for y in (5, 4, 3):
        d.set(17, y, 6, hopper("down"))
    d.set(17, 2, 6, chest("north"))
    inputs = {}
    for i, (item, label) in enumerate(SORT):
        x = 2 + 3 * i
        d.set(x, 4, 6, hopper("north"))                       # F
        d.set(x, 3, 6, hopper("down"))                        # G
        d.set(x, 2, 6, chest("north"))
        d.tag(x, 2, 6, "farm_output")
        d.set(x, 4, 7, comparator("north"))                   # K'
        d.set(x, 3, 7, PA)
        d.set(x, 4, 8, wire(n="side", e="side"))             # D1
        d.set(x, 3, 8, PA)
        d.set(x + 1, 3, 8, wire(n="side", w="up"))           # D2
        d.set(x + 1, 2, 8, PA)
        d.set(x + 1, 3, 7, WIRE_Z)                            # D3
        d.set(x + 1, 2, 7, PA)
        d.set(x + 1, 3, 6, comparator("east", "subtract"))    # K
        d.set(x + 1, 2, 6, SB)
        d.set(x + 2, 3, 6, "composter[level=1]")
        d.set(x + 2, 2, 6, SB)
        d.set(x + 1, 4, 6, "chiseled_stone_bricks")
        d.set(x + 2, 4, 6, "glass")
        d.sign(x + 1, 4, 5, "north", [label, "<-", "filter: 41 +", "4 fillers"], "spruce")
        inputs[(x, 4, 6)] = [(f"minecraft:{item}", 41)] + [("minecraft:stick", 1)] * 4
    # input chest platform: two steps up so the chest over the stream is in reach
    d.set(1, 2, 5, "spruce_stairs[facing=west,half=bottom,shape=straight,waterlogged=false]")
    d.set(1, 2, 4, "spruce_planks")
    mix = []
    for _ in range(3):
        for item, _l in SORT:
            mix.append((f"minecraft:{item}", 8))
        mix.append(("minecraft:cobblestone", 8))
    inputs[(1, 6, 6)] = mix
    # aisle furniture + the filter list
    tie_beams(d, (6, 12), 3, 8, top)
    approach(d, cx, Z1, ["Item Sorter", "Filters: iron,", "gold, copper", "coal, redstone"])
    d.sign(cx - 1, 3, Z1 - 1, "north", ["Each top hopper:", "41 of its item", "+ 1 renamed", "stick x4"], "spruce")
    d.farm_test(expect={f"minecraft:{item}": 20 for item, _l in SORT}, ticks=2400, inputs=inputs)
    return d


# ================================================================================================ super smelter
@design("supersmelter")
def supersmelter(pack, rel, L):
    """Nine-furnace super smelter with even distribution (the end-of-line trick of ilmango's smelter).

    Furnaces F (x,2,6), x = 3..11, facing north (the aisle). Per furnace x = 3..10:
        T (x,4,6)  input line, hoppers facing east;  D (x,3,6) hopper facing down into F, pulls from T
        L (x,3,7)  fuel line, hoppers facing east;   G (x,2,7) hopper facing north into F's side (fuel slot)
        O (x,1,6)  hopper under F (pulls the result), output line facing east (in the floor)
        B (x,3,5) block with dust on top (x,4,5): powered -> locks D;  C (x,2,8) block with dust (x,3,8): locks G
    End of the lines (x = 11): E (11,4,6) and L9 (11,3,7) face down into D9 / G9, which are never locked, so they
    feed the ninth furnace and keep the line ends draining.
    Comparator K (12,4,6, facing west) reads E -> Q (13,4,6) -> redstone wall torch (14,4,6) on Q (inverter) ->
    dust (14,3,6) under it -> north route (14..11,3,5) up onto the B row; south route (14,3,7..8),(13..11,3,8) onto
    the C row ((11,2,8) is glass so G9 is not locked).
    Torch lit (E empty) = every D and G locked, the lines stream on to the end. When the first item reaches E the
    torch goes out and all D/G hoppers unlock for ~8 ticks: each takes the item that is in its T/L hopper right then
    (one per furnace) and E drains into furnace 9; E empty -> locked again. One cycle per stream front (~70 ticks),
    so the torch toggles far below the burn-out rate. Output: O line -> (12,1,6) north -> (12,1,5) north ->
    output barrel (12,1,4) set in the aisle floor."""
    d = Design(pack, rel, size=(18, 13, 12), gy=1, paving="grass_block")
    X1, Z1, X2, Z2, top = 1, 2, 16, 10, 7
    cx = 7
    shed(d, X1, Z1, X2, Z2, top, cx, windows_front=[(3, Z1), (4, Z1), (11, Z1), (12, Z1)],
         windows_side=[(X1, 4), (X2, 4)])
    xs = range(3, 12)
    for x in xs:
        d.set(x, 2, 6, "furnace[facing=north,lit=false]")
        d.set(x, 1, 6, hopper("east"))
        d.set(x, 2, 7, hopper("north"))
        if x <= 11:
            d.set(x, 2, 5, AIR)
            d.set(x, 1, 5, AIR)                             # 1-deep service trench in front of the furnaces
            d.set(x, 0, 5, SB)
    d.set(2, 1, 5, AIR)                                     # step down into the trench at its west end
    d.set(2, 0, 5, SB)
    for x in range(3, 11):
        d.set(x, 4, 6, hopper("east"))
        d.set(x, 3, 6, hopper("down"))
        d.set(x, 3, 7, hopper("east"))
        d.set(x, 3, 5, PA)                                  # B
        d.set(x, 4, 5, WIRE_X)
        d.set(x, 2, 8, PA)                                  # C
        d.set(x, 3, 8, WIRE_X)
    # line ends: E drops straight into furnace 9 (raised one block) - a hopper under E would pull its item out at
    # once and the comparator would never see it; L9 feeds furnace 9's fuel slot from the side.
    d.set(11, 4, 6, hopper("down"))                         # E
    d.set(11, 3, 6, "furnace[facing=north,lit=false]")      # F9
    d.set(11, 2, 6, hopper("down"))                         # F9's output hopper -> O line
    d.set(11, 3, 7, hopper("north"))                        # L9
    d.set(11, 2, 7, SB)
    d.set(12, 4, 6, comparator("west"))                     # K
    d.set(12, 3, 6, PA)
    d.set(13, 4, 6, PA)                                     # Q
    d.set(14, 4, 6, "redstone_wall_torch[facing=east,lit=true]")
    d.set(14, 3, 6, WIRE_Z)
    d.set(14, 2, 6, PA)
    # north route onto the B row: (14,3,5) -> (12,3,5) -> up onto S (11,3,5) -> (11,4,5) -> B row dust
    d.set(14, 3, 5, wire(s="side", w="side"))
    d.set(13, 3, 5, WIRE_X)
    d.set(12, 3, 5, wire(e="side", w="up"))
    d.set(11, 3, 5, PA)                                     # S
    d.set(11, 4, 5, WIRE_X)
    d.set(12, 2, 5, "glass")                                # glass: no power into the output hopper below
    for x in (13, 14):
        d.set(x, 2, 5, PA)
    for x in (12, 13, 14):
        d.set(x, 4, 5, AIR)
    # south route onto the C row
    d.set(14, 3, 7, WIRE_Z)
    d.set(14, 3, 8, wire(n="side", w="side"))
    for x in (11, 12, 13):
        d.set(x, 3, 8, WIRE_X)
    d.set(11, 2, 8, "glass")
    for x in (12, 13):
        d.set(x, 2, 8, PA)
    d.set(14, 2, 7, PA)
    d.set(14, 2, 8, PA)
    # output: in the floor to a barrel in the aisle
    d.set(12, 1, 6, hopper("north"))
    d.set(12, 1, 5, hopper("north"))
    d.set(12, 1, 4, "barrel[facing=up,open=false]")
    d.tag(12, 1, 4, "farm_output")
    # input chest over T1; fuel chest over an extra fuel hopper L0 (2,3,7) so it can be reached past the T line
    d.set(3, 5, 6, chest("north"))
    d.set(2, 3, 7, hopper("east"))                          # L0
    d.set(2, 2, 7, PA)
    d.set(2, 4, 7, chest("north"))
    d.set(2, 3, 8, AIR)                                     # the C-row dust ends here: keep air (else L0 locks)
    d.sign(2, 3, 3, "east", ["Top chest: ore,", "sand, food...", "Low chest left:", "coal / fuel"], "spruce")
    tie_beams(d, (5, 9), 3, 9, top)
    approach(d, cx, Z1, ["Super Smelter", "Bring: things", "to smelt and", "coal for fuel"])
    d.farm_test(expect={"minecraft:iron_ingot": 100}, ticks=5000,
                inputs={(3, 5, 6): [("minecraft:raw_iron", 64), ("minecraft:raw_iron", 64)],
                        (2, 4, 7): [("minecraft:coal", 64)]})
    return d
