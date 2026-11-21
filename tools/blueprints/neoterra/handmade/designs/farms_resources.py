"""
Farmworks resource farms (decorations/resourcefarms/): small stone-and-spruce work sheds around proven vanilla
(Java 1.21.1) block-forming mechanics. None of these can deliver items into a chest on their own (cobblestone, stone,
basalt, ice, clay and concrete must be mined by a player; lava ends up in cauldrons; snow layers only drop snowballs
when a player breaks them with a shovel), so every farm_test has expect={} and only checks that the farm builds and
its fluids settle without breaking anything.

Fluid tricks used (checked against the 1.21.1 FlowingFluid / LiquidBlock code):
  * "water over a hole": a NON-source water block that has water (or air) below it never spreads sideways
    (FlowingFluid.spread -> isWaterHole). A lone water SOURCE whose four sides are solid feeds such a column forever.
    This keeps water next to a generator / concrete cell without ever flowing into it.
  * flowing lava touching water (side or above) -> cobblestone; lava flowing DOWN into water -> stone;
    flowing lava above soul soil touching blue ice -> basalt (LiquidBlock.shouldSpreadLiquid / LavaFluid.spreadTo).
  * lava fire safety: lava only lights fires through AIR cells above it, so every lava block has solid blocks over
    its whole 3x3 above-layer, and nothing flammable next to it.
Only water / lava SOURCE blocks are placed; cells marked "flow" are left as air and fill with flowing water in game.
"""
from hm import Design, design, AIR

SB = "stone_bricks"
CB = "cobblestone"
LOG = "stripped_spruce_log"
GLASS = "glass"
WATER = "water[level=0]"
LAVA = "lava[level=0]"


def logb(axis="y"):
    return f"{LOG}[axis={axis}]"


def slab(b, t="bottom"):
    return f"{b}_slab[type={t},waterlogged=false]"


def stair(b, facing, half="bottom"):
    return f"{b}_stairs[facing={facing},half={half},shape=straight,waterlogged=false]"


def lantern(d, x, y, z, hanging=True, soul=False):
    d.set(x, y, z, f"{'soul_lantern' if soul else 'lantern'}[hanging={'true' if hanging else 'false'},waterlogged=false]")


def chest(facing="north"):
    return f"chest[facing={facing},type=single,waterlogged=false]"


FENCE = "spruce_fence[east=false,north=false,south=false,waterlogged=false,west=false]"


# ------------------------------------------------------------------------------------------------- the work shed
def shed(d, X1, Z1, X2, Z2, top, door_x, floor="smooth_stone", back_posts=True, windows_front=(), windows_side=(),
         roof=True):
    """Stone-brick plinth (y=2), cobble walls up to `top` with stripped-spruce corner posts / mid posts and a log
    beam on top, gable roof (ridge along x) with spruce-plank gable ends, door in the north wall."""
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
        if back_posts:
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
    for (x, z) in windows_front:
        d.set(x, 3, z, "glass_pane")
        d.set(x, 4, z, "glass_pane")
    for (x, z) in windows_side:
        d.set(x, 3, z, "glass_pane")
        d.set(x, 4, z, "glass_pane")
    d.door(door_x, gy + 1, Z1, "south", "spruce")
    if roof:
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


def tie_beams(d, xs, z1, z2, y, lamps=True, soul=False):
    for x in xs:
        for z in range(z1, z2 + 1):
            d.set(x, y, z, logb("z"))
        if lamps:
            lantern(d, x, y - 1, (z1 + z2) // 2, soul=soul)


# ================================================================================================ cobblestone
@design("cobblegen")
def cobblegen(pack, rel, L):
    """Six-cell player cobblestone generator (the classic lava + water gen, fluids kept apart by the hole trick).

    Per pair of cells (x = a, a+1, a+2; cells G at y3 z8, the player stands in the niche at z7):
        z9  lava source behind each G           (a,3,9) (c,3,9)
        z8  G  F  G                             F = (b,3,8): falling water from the source S = (b,4,8)
                                                H = (b,2,8): 1-deep pit under F (fills with water)
    F has water below it, so it never spreads sideways into G. When the player mines G, lava flows in from behind
    and, touching the water in F, turns into cobblestone at once (LiquidBlock.shouldSpreadLiquid)."""
    d = Design(pack, rel, size=(17, 16, 13), gy=1, paving="grass_block")
    X1, Z1, X2, Z2, top = 1, 2, 15, 10, 5
    cx = 8
    shed(d, X1, Z1, X2, Z2, top, cx, back_posts=False,
         windows_front=[(4, Z1), (5, Z1), (11, Z1), (12, Z1)], windows_side=[(X1, 4), (X1, 6), (X2, 4), (X2, 6)])
    # generator block: solid stone-brick mass along the back wall, 4 high (its top layer keeps lava fire-safe)
    d.fill(2, 2, 7, 14, 5, 9, SB)
    for x in range(2, 15):
        d.set(x, 5, 7, "chiseled_stone_bricks" if x % 4 == 0 else "polished_andesite")
    for a in (3, 7, 11):
        b, c = a + 1, a + 2
        for g in (a, c):
            d.set(g, 3, 8, CB)                  # the generator cell (pre-filled with cobble)
            d.set(g, 3, 9, LAVA)                # lava source behind it
            d.clear(g, 2, 7, g, 3, 7)           # niche the player stands in
            d.set(g, 4, 7, stair("stone_brick", "south", "top"))
        d.set(b, 4, 8, WATER)                   # source, four solid sides
        d.clear(b, 2, 8, b, 3, 8)               # flow: falling water column + pit
        d.set(b, 3, 7, GLASS)                   # watch the water
        d.set(b, 5, 8, GLASS)
    # room: storage, lights, bench
    tie_beams(d, (5, 11), 3, 6, top)
    d.set(2, 2, 3, chest("east"))
    d.tag(2, 2, 3, "farm_output")
    d.set(2, 2, 4, chest("east"))
    d.set(14, 2, 3, "crafting_table")
    d.set(14, 2, 4, "stonecutter[facing=west]")
    d.set(2, 2, 6, "barrel[facing=up,open=false]")
    approach(d, cx, Z1, ["Cobblestone", "Generator", "Bring:", "a pickaxe"])
    d.farm_test(expect={}, ticks=1200)   # player-mined: checks it builds and lava/water settle
    return d


# ================================================================================================ stone
@design("stonegen")
def stonegen(pack, rel, L):
    """Six-cell player stone generator (lava falling into water makes stone), plus a smooth-stone furnace bench.

    Per pair (x = a, a+1, a+2):
        y4  lava source above each G            (a,4,8) (c,4,8)
        y3  G  W  G                             W = (b,3,8) water source (sides solid except the two G cells)
        y2  H  #  H                             H = pit under each G
    Mining G: the water source flows into G at once (5 ticks); G has a hole under it, so that water only falls and
    never spreads further. The lava above (30 ticks) then flows down into the water -> stone (LavaFluid.spreadTo).
    The player looks through a 1-high window (g,3,7) over a sill and mines G from the corridor (z6)."""
    d = Design(pack, rel, size=(17, 16, 13), gy=1, paving="grass_block")
    X1, Z1, X2, Z2, top = 1, 2, 15, 10, 5
    cx = 8
    shed(d, X1, Z1, X2, Z2, top, cx, back_posts=False,
         windows_front=[(4, Z1), (5, Z1), (11, Z1), (12, Z1)], windows_side=[(X1, 4), (X2, 4), (X2, 6)])
    d.fill(2, 2, 7, 14, 5, 9, SB)
    for x in range(2, 15):
        d.set(x, 2, 7, "polished_andesite")
        d.set(x, 5, 7, "chiseled_stone_bricks" if x % 4 == 0 else "smooth_stone")
    for a in (3, 7, 11):
        b, c = a + 1, a + 2
        for g in (a, c):
            d.set(g, 3, 8, "stone")            # the generator cell (pre-filled with stone)
            d.set(g, 2, 8, AIR)                 # pit under it (flow)
            d.set(g, 4, 8, LAVA)                # lava source above it
            d.set(g, 3, 7, AIR)                 # window to mine through
        d.set(b, 3, 8, WATER)
        d.set(b, 3, 7, GLASS)
    tie_beams(d, (5, 11), 3, 6, top)
    # smooth-stone bench: two furnaces with fuel chests, by the west wall
    d.set(2, 2, 3, chest("east"))
    d.tag(2, 2, 3, "farm_output")
    d.set(2, 2, 4, "furnace[facing=east,lit=false]")
    d.set(2, 2, 5, "furnace[facing=east,lit=false]")
    d.set(14, 2, 3, chest("west"))
    d.set(14, 2, 4, "crafting_table")
    d.set(14, 2, 5, "stonecutter[facing=west]")
    approach(d, cx, Z1, ["Stone Generator", "Bring: Silk", "Touch pickaxe,", "furnace fuel"])
    d.farm_test(expect={}, ticks=1200)
    return d


# ================================================================================================ basalt
@design("basaltgen")
def basaltgen(pack, rel, L):
    """Six-cell player basalt generator: lava flowing over soul soil next to blue ice turns into basalt.

    Per pair (x = a, a+1, a+2):  z9 lava source behind each G;  z8  G  BI  G  (blue ice between);  soul soil under
    each G. No water anywhere. The lava sources stand on stone bricks (a source on soul soil next to blue ice would
    itself turn to basalt)."""
    d = Design(pack, rel, size=(17, 16, 13), gy=1, paving="grass_block")
    X1, Z1, X2, Z2, top = 1, 2, 15, 10, 5
    cx = 8
    shed(d, X1, Z1, X2, Z2, top, cx, back_posts=False,
         windows_front=[(4, Z1), (5, Z1), (11, Z1), (12, Z1)], windows_side=[(X1, 4), (X1, 6), (X2, 4), (X2, 6)])
    d.fill(2, 2, 7, 14, 5, 9, SB)
    for x in range(2, 15):
        d.set(x, 5, 7, "polished_basalt[axis=x]")
    for a in (3, 7, 11):
        b, c = a + 1, a + 2
        for g in (a, c):
            d.set(g, 2, 8, "soul_soil")
            d.set(g, 3, 8, "basalt[axis=y]")    # the generator cell (pre-filled)
            d.set(g, 3, 9, LAVA)
            d.clear(g, 2, 7, g, 3, 7)
            d.set(g, 4, 7, stair("stone_brick", "south", "top"))
        d.set(b, 3, 8, "blue_ice")
        d.set(b, 3, 7, GLASS)
        d.set(b, 2, 7, "polished_basalt[axis=y]")
        d.set(b, 4, 7, "polished_basalt[axis=y]")
    tie_beams(d, (5, 11), 3, 6, top)
    d.set(2, 2, 3, chest("east"))
    d.tag(2, 2, 3, "farm_output")
    d.set(2, 2, 4, chest("east"))
    d.set(14, 2, 3, "stonecutter[facing=west]")
    d.set(14, 2, 4, "crafting_table")
    approach(d, cx, Z1, ["Basalt", "Generator", "Bring:", "a pickaxe"])
    d.farm_test(expect={}, ticks=1200)
    return d


# ================================================================================================ lava
@design("lavafarm")
def lavafarm(pack, rel, L):
    """Lava dripstone farm: 10 lava source cells sit in a sealed tank layer (y7) above the ceiling; a pointed
    dripstone hangs under the ceiling block below each (y5) and drips into a cauldron on the floor (y2), filling it
    with lava (about one fill per ~20 min per cauldron at the normal random-tick speed). Glass skylights over the
    lava, flat stone roof (no timber near the lava). Bring buckets."""
    d = Design(pack, rel, size=(15, 12, 13), gy=1, paving="grass_block")
    X1, Z1, X2, Z2, top = 1, 2, 13, 10, 7
    cx = 7
    shed(d, X1, Z1, X2, Z2, top, cx, roof=False,
         windows_front=[(3, Z1), (4, Z1), (10, Z1), (11, Z1)],
         windows_side=[(X1, 4), (X1, 6), (X1, 8), (X2, 4), (X2, 6), (X2, 8)])
    spots = [(x, z) for z in (4, 8) for x in (3, 5, 7, 9, 11)]
    d.fill(2, 6, 3, 12, 6, 9, SB)                         # ceiling
    d.fill(2, 7, 3, 12, 7, 9, SB)                         # tank layer
    for (x, z) in spots:
        d.set(x, 7, z, LAVA)
        d.set(x, 5, z, "pointed_dripstone[thickness=tip,vertical_direction=down,waterlogged=false]")
        d.set(x, 2, z, "cauldron")
    # roof deck over everything (solid over every lava cell), glass skylights, parapet with coping
    for x in range(X1, X2 + 1):
        for z in range(Z1, Z2 + 1):
            edge = x in (X1, X2) or z in (Z1, Z2)
            d.set(x, 8, z, SB if edge else slab("stone_brick", "top"))
            if edge:
                d.set(x, 9, z, slab("stone_brick"))
    for (x, z) in spots:
        d.set(x, 8, z, GLASS)
    for (x, z) in ((X1, Z1), (X2, Z1), (X1, Z2), (X2, Z2)):
        d.set(x, 9, z, SB)
        lantern(d, x, 10, z, hanging=False)
    # lights under the ceiling over the aisle, tool corner
    for x in (4, 10):
        lantern(d, x, 5, 6)
    d.set(12, 2, 6, chest("west"))
    d.tag(12, 2, 6, "farm_output")
    d.set(2, 2, 6, "barrel[facing=up,open=false]")
    approach(d, cx, Z1, ["Lava Dripstone", "Farm", "Bring:", "buckets"])
    d.farm_test(expect={}, ticks=1200)   # output is lava in cauldrons (blocks), collected by bucket
    return d


# ================================================================================================ snow
@design("snowfarm")
def snowfarm(pack, rel, L):
    """Snow golem yard: a roofed 11x6 smooth-stone yard behind a glass partition; snow golems walking on it leave
    a layer of snow on every free cell they step on (SnowGolem.aiStep, any biome where golems do not melt).
    Snow layers only drop snowballs when a player breaks them with a shovel (loot table needs an entity, block needs
    the tool), so the harvest is manual: walk the yard with a shovel. Soul lanterns only (light 10): brighter than 0
    so no mobs spawn, but below 12 so the snow does not melt. The roof keeps rain off the golems."""
    d = Design(pack, rel, size=(15, 16, 15), gy=1, paving="grass_block")
    X1, Z1, X2, Z2, top = 1, 2, 13, 12, 5
    cx = 7
    shed(d, X1, Z1, X2, Z2, top, cx, windows_front=[(3, Z1), (4, Z1), (10, Z1), (11, Z1)],
         windows_side=[(X1, 7), (X1, 8), (X1, 10), (X2, 7), (X2, 8), (X2, 10)], floor="spruce_planks")
    for x in range(2, 13):
        for z in range(6, 12):
            d.set(x, 1, z, "smooth_stone")
    # glass partition (full height: golems cannot jump it) with a door into the yard
    for x in range(2, 13):
        d.set(x, 2, 5, SB)
        for y in range(3, top + 1):
            d.set(x, y, 5, "glass_pane")
    d.set(cx, 2, 5, AIR)
    d.door(cx, 2, 5, "south", "spruce")
    tie_beams(d, (4, 10), 6, 11, top, soul=True)
    lantern(d, cx, 4, 3, soul=True)
    d.set(cx, top, 3, logb("x"))
    for x in range(2, 13):
        d.set(x, top, 3, logb("x"))
    # vestibule: tool rack corner, storage
    d.set(2, 2, 3, chest("east"))
    d.tag(2, 2, 3, "farm_output")
    d.set(2, 2, 4, chest("east"))
    d.set(12, 2, 3, "crafting_table")
    d.set(12, 2, 4, "barrel[facing=up,open=false]")
    d.set(12, 3, 4, "carved_pumpkin[facing=west]")
    approach(d, cx, Z1, ["Snow Golem Yard", "Bring: 2 snow", "golems, shovel", "(no desert)"])
    d.farm_test(expect={}, spawns=[("minecraft:snow_golem", 5, 2, 8, 1), ("minecraft:snow_golem", 9, 2, 9, 1)],
                ticks=1200)
    return d


# ================================================================================================ ice
@design("icefarm")
def icefarm(pack, rel, L):
    """Ice pond: two 11x3 pools of water sources open to the sky, a walkway between them, low light (soul
    lanterns, block light < 10 at the water) so the pools freeze over in snowy biomes. Harvest the ice with a Silk
    Touch pickaxe (breaking ice without it turns it back into a water source that refreezes). In the well house:
    a 2x2 infinite water source under the roof (never freezes) to refill harvested pool cells by bucket."""
    d = Design(pack, rel, size=(17, 14, 21), gy=1, paving="grass_block")
    cx = 8
    # well house
    X1, Z1, X2, Z2, top = 4, 2, 12, 7, 5
    shed(d, X1, Z1, X2, Z2, top, cx, floor="spruce_planks", windows_front=[(6, Z1), (10, Z1)],
         windows_side=[(X1, 4), (X2, 4)])
    for x in (7, 8):
        for z in (4, 5):
            d.set(x, 0, z, SB)
            d.set(x, 1, z, WATER)          # 2x2 infinite source (sunk into the floor)
    for x in range(6, 10):
        for z in range(3, 7):
            if not (x in (7, 8) and z in (4, 5)):
                d.set(x, 1, z, SB)
    for (x, z) in ((6, 3), (9, 3), (6, 6), (9, 6)):
        d.set(x, 2, z, FENCE)
        d.set(x, 3, z, FENCE)
    d.fill(6, 4, 3, 9, 4, 6, slab("spruce"))
    d.clear(7, 4, 4, 8, 4, 5)
    lantern(d, 5, 4, 6, hanging=False, soul=True)
    d.set(5, 3, 6, slab("spruce", "top"))
    d.set(5, 2, 6, "barrel[facing=up,open=false]")
    d.set(11, 2, 3, chest("west"))
    d.tag(11, 2, 3, "farm_output")
    d.set(11, 2, 4, chest("west"))
    d.door(cx, 2, Z2, "north", "spruce")
    # pond yard behind the house
    YZ1, YZ2 = 8, 19
    for x in range(1, 16):
        for z in range(YZ1, YZ2 + 1):
            d.set(x, 1, z, "gravel")
    pools = [(z1, z1 + 2) for z1 in (10, 14)]
    for (z1, z2) in pools:
        for x in range(2, 15):
            for z in range(z1 - 1, z2 + 2):
                d.set(x, 1, z, SB)
        for x in range(3, 14):
            for z in range(z1, z2 + 1):
                d.set(x, 0, z, SB)
                d.set(x, 1, z, WATER)
    for x in range(2, 15):
        d.set(x, 1, 13, "spruce_planks")       # walkway between the pools
    # fence around the yard (fence posts with soul lanterns), gate-free: entry through the house
    for x in range(0, 17):
        d.set(x, 2, YZ2 + 1, FENCE)
    for z in range(YZ1, YZ2 + 2):
        d.set(0, 2, z, FENCE)
        d.set(16, 2, z, FENCE)
    for x in range(0, 17):
        if not (X1 <= x <= X2):
            d.set(x, 2, YZ1, FENCE)
    for (x, z) in ((0, YZ1), (16, YZ1), (0, YZ2 + 1), (16, YZ2 + 1), (0, 13), (16, 13), (8, YZ2 + 1)):
        d.set(x, 2, z, SB)
        lantern(d, x, 3, z, hanging=False, soul=True)
    for (x, z) in ((2, 13), (14, 13)):
        d.set(x, 2, z, FENCE)
        lantern(d, x, 3, z, hanging=False, soul=True)
    approach(d, cx, Z1, ["Ice Pond", "Snowy biomes", "Bring: Silk", "Touch, bucket"])
    d.farm_test(expect={}, ticks=1200)
    return d


# ================================================================================================ mud & clay
@design("mudclay")
def mudclay(pack, rel, L):
    """Mud & clay works: five drying niches along the back wall. In each niche a dirt block sits on a stone-brick
    root block with a pointed dripstone hanging under it; a dispenser above faces down onto the dirt.
      1. load water bottles into the dispensers, press the button -> the dirt turns into mud (dispenser behaviour
         of water bottles on dirt) and the empty bottle stays in the dispenser;
      2. the dripstone drains the mud: it becomes clay after a few random ticks (PointedDripstoneBlock, no cauldron);
      3. mine the clay (4 clay balls, by hand), put a new dirt block in the niche, press again.
    A one-block water basin at the entrance refills glass bottles forever (bottling never uses up a source)."""
    d = Design(pack, rel, size=(15, 14, 13), gy=1, paving="grass_block")
    X1, Z1, X2, Z2, top = 1, 2, 13, 10, 6
    cx = 7
    shed(d, X1, Z1, X2, Z2, top, cx, back_posts=False, windows_front=[(3, Z1), (4, Z1), (10, Z1), (11, Z1)],
         windows_side=[(X1, 4), (X1, 6), (X2, 4), (X2, 6)])
    d.fill(2, 2, 8, 12, top - 1, 9, SB)                   # back works wall
    for x in range(2, 13):
        d.set(x, top - 1, 8, "polished_andesite")
    for x in (3, 5, 7, 9, 11):
        d.set(x, 2, 8, "pointed_dripstone[thickness=tip,vertical_direction=down,waterlogged=false]")
        d.set(x, 3, 8, SB)                                 # root block
        d.set(x, 4, 8, "dirt")                             # becomes mud, then clay
        d.set(x, 5, 8, "dispenser[facing=down,triggered=false]")
        d.set(x, 5, 7, "stone_button[face=wall,facing=north,powered=false]")
        d.set(x, 1, 8, "mud_bricks")
    for x in (2, 4, 6, 8, 10, 12):
        d.set(x, 4, 8, "mud_bricks")
        d.set(x, 2, 8, "mud_bricks")
        d.set(x, 3, 8, "mud_bricks")
    # bottle basin (1x1 water source, solid all round) and storage
    d.set(3, 1, 3, SB)
    d.set(3, 2, 3, WATER)
    for (x, z) in ((2, 3), (4, 3), (3, 4)):
        d.set(x, 2, z, SB)
    d.set(4, 2, 4, SB)
    d.set(2, 2, 4, SB)
    d.set(12, 2, 3, chest("west"))
    d.tag(12, 2, 3, "farm_output")
    d.set(12, 2, 4, chest("west"))
    d.set(12, 2, 6, "barrel[facing=up,open=false]")
    tie_beams(d, (5, 9), 3, 6, top)
    approach(d, cx, Z1, ["Mud & Clay Works", "Bring: water", "bottles, dirt"])
    d.farm_test(expect={}, ticks=1200)   # clay forms as blocks (mined by the player)
    return d


# ================================================================================================ concrete
@design("concretestation")
def concretestation(pack, rel, L):
    """Concrete station: two fountain kiosks. Each has a water source S (y5) inside a solid stone cap, falling as a
    column through y4/y3 into a 1-deep pit (y2). Four pedestals around the pit: concrete powder placed on a pedestal
    (y3) touches the falling water and hardens at once (ConcretePowderBlock). The column has water below it, so it
    never spreads sideways - the pedestal cells stay dry when the concrete is mined away."""
    d = Design(pack, rel, size=(15, 14, 13), gy=1, paving="grass_block")
    X1, Z1, X2, Z2, top = 1, 2, 13, 10, 6
    cx = 7
    shed(d, X1, Z1, X2, Z2, top, cx, windows_front=[(3, Z1), (4, Z1), (10, Z1), (11, Z1)],
         windows_side=[(X1, 4), (X1, 6), (X1, 8), (X2, 4), (X2, 6), (X2, 8)])
    samples = {4: ("white_concrete", "light_blue_concrete"), 10: ("orange_concrete", "lime_concrete")}
    for fx in (4, 10):
        fz = 6
        d.set(fx, 2, fz, AIR)                              # pit (flow)
        for (x, z) in ((fx - 1, fz), (fx + 1, fz), (fx, fz - 1), (fx, fz + 1)):
            d.set(x, 2, z, "polished_andesite")            # pedestals
        for (x, z) in ((fx - 1, fz - 1), (fx + 1, fz - 1), (fx - 1, fz + 1), (fx + 1, fz + 1)):
            for y in (2, 3, 4):
                d.set(x, y, z, logb("y"))
        for x in range(fx - 1, fx + 2):
            for z in range(fz - 1, fz + 2):
                d.set(x, 5, z, SB)
        d.set(fx, 5, fz, WATER)                            # source; the column below is flow
        d.set(fx, 6, fz, slab("stone_brick"))
        for (x, z) in ((fx - 1, fz), (fx + 1, fz), (fx, fz - 1), (fx, fz + 1)):
            d.set(x, 6, z, stair("stone_brick", {(-1, 0): "east", (1, 0): "west", (0, -1): "south",
                                                 (0, 1): "north"}[(x - fx, z - fz)]))
        a, b = samples[fx]
        d.set(fx - 1, 3, fz, a)
        d.set(fx + 1, 3, fz, b)
    # storage: powder in, concrete out
    d.set(2, 2, 3, chest("east"))
    d.set(2, 2, 4, chest("east"))
    d.set(12, 2, 3, chest("west"))
    d.tag(12, 2, 3, "farm_output")
    d.set(12, 2, 4, chest("west"))
    d.set(2, 2, 9, "barrel[facing=up,open=false]")
    d.set(12, 2, 9, "barrel[facing=up,open=false]")
    d.set(7, 2, 9, "crafting_table")
    tie_beams(d, (7,), 3, 9, top)
    lantern(d, 7, top - 1, 3)
    approach(d, cx, Z1, ["Concrete", "Station", "Bring: concrete", "powder, pickaxe"])
    d.farm_test(expect={}, ticks=1200)
    return d
