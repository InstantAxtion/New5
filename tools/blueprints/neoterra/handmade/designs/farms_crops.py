"""
Farmworks crop & plant farms (decorations/cropfarms/), Java 1.21.1 vanilla mechanics only.

Redstone conventions used below (Java block states):
  observer  facing = the side it WATCHES; it pulses (2 gt) out of its back (the opposite side).
  piston    facing = the push direction, extended=false.
  hopper    facing = output direction (down or sideways, never up).
  repeater  facing = the side its INPUT comes from (DiodeBlock reads pos.relative(facing)); output is opposite.
  redstone dust powers the block under it (and the block it points at); a block powered by dust activates a piston
  next to it (but does not power other dust).
  cocoa     facing = towards the jungle log it hangs on.

Collection trick used by most farms: MUD (14/16 high) and FARMLAND (15/16) are lower than a full block, so items lying
on them are inside the pick-up area of a hopper right under them (the minecraft wiki's cane farm note: "a line of
hoppers can replace the minecart if the cane is planted on mud").

Only water SOURCE blocks are placed. Cells described as "flow" are left as air and fill with flowing water in game.
"""
from hm import Design, design, AIR

SB = "stone_bricks"
CB = "cobblestone"
GLASS = "glass"
WATER = "water[level=0]"
MUD = "mud"
PLANK = "spruce_planks"


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


def dust(n="none", e="none", s="none", w="none"):
    return f"redstone_wire[east={e},north={n},power=0,south={s},west={w}]"


def barrel(f="up"):
    return f"barrel[facing={f},open=false]"


def lantern(d, x, y, z, hanging=True):
    d.set(x, y, z, f"lantern[hanging={'true' if hanging else 'false'},waterlogged=false]")


FENCE = "spruce_fence[east=false,north=false,south=false,waterlogged=false,west=false]"


def output(d, x, y, z, f="up"):
    d.set(x, y, z, barrel(f))
    d.tag(x, y, z, "farm_output")


# ------------------------------------------------------------------------------------------------ building kit
def shell(d, X1, Z1, X2, Z2, top, floor="smooth_stone", wall="glass", plinth=SB, post_step=4, floor_y=1):
    """Stone-brick plinth course (y=2), walls (glass by default) up to `top` with stripped-spruce corner/mid posts
    and a log beam on top. Interior is cleared, floor laid at y=1."""
    for x in range(X1, X2 + 1):
        for z in range(Z1, Z2 + 1):
            edge = x in (X1, X2) or z in (Z1, Z2)
            d.set(x, floor_y, z, SB if edge else floor)
            for y in range(2, top + 1):
                if not edge:
                    d.set(x, y, z, AIR)
                elif y == 2:
                    d.set(x, y, z, plinth)
                else:
                    d.set(x, y, z, wall)
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
    return posts


def entrance(d, x, z, name, bring, facing="north", path_to=0, sign_side=1, sign_wall=None):
    """Door in the north wall at (x, 2, z), a wall sign beside it, a lantern over it and a gravel path north."""
    d.door(x, 2, z, facing=facing, wood="spruce")
    sx = x + sign_side
    if sign_wall:
        d.set(sx, 3, z, sign_wall)
    d.sign(sx, 3, z - 1, "north", [name, "Farmworks", "Bring:", bring], wood="spruce")
    lantern(d, x, 4, z - 1, hanging=False) if d.air(x, 4, z - 1) else None
    for zz in range(path_to, z):
        d.set(x, 1, zz, "gravel")


def roof(d, X1, Z1, X2, Z2, y, axis="x", glass=False):
    if glass:
        return d.gable(X1, Z1, X2, Z2, y, axis=axis, stairs="spruce_stairs", ridge="spruce_slab", end=PLANK)
    return d.gable(X1, Z1, X2, Z2, y, axis=axis, stairs="spruce_stairs", ridge="spruce_slab", end=PLANK)


def controller(d, x):
    d.hut(x, 1, 0)


# ================================================================================ observer cane / bamboo module
def cane_module(d, x1, x2, z0, plant, plant2=None):
    """Two rows of `plant` on MUD over hopper lines, a water row between them (sources, keeps cane alive).
    Rows (z): z0 dust / back blocks, z0+1 piston (y4) + observer (y5) facing south, z0+2 plant row A, z0+3 water,
    z0+4 plant row B, z0+5 piston + observer facing north, z0+6 dust / back blocks.
    Plant base at y3 (on mud at y2), piston cuts at y4, observer watches y5: when the plant grows into y5, the
    observer pulses its back into the dust line at y5, the dust powers the block under it (y4) which is right
    behind every piston of the row -> pistons push into y4, the plant breaks there (and above), items drop onto the
    mud / into the water and the hoppers underneath take them. The base block (y3) stays and regrows.
    Hoppers at y1 run east, a collector column at x2+2 ends in the output barrel (x2+2, 1, z0+5)."""
    rows = {"A": (z0 + 1, z0 + 2, z0, "south"), "B": (z0 + 5, z0 + 4, z0 + 6, "north")}
    for x in range(x1, x2 + 1):
        for (pz, cz, bz, f) in rows.values():
            d.set(x, 1, cz, hopper("east"))
            d.set(x, 2, cz, MUD)
            d.set(x, 3, cz, plant)
            if plant2:
                d.set(x, 4, cz, plant2)
            for y in (2, 3):
                d.set(x, y, pz, SB)
            d.set(x, 4, pz, piston(f))
            d.set(x, 5, pz, observer(f))
            for y in (1, 2, 3, 4):
                d.set(x, y, bz, SB)
            n, s = ("none", "side") if f == "south" else ("side", "none")
            d.set(x, 5, bz, dust(n=n, s=s, e="side" if x < x2 else "none", w="side" if x > x1 else "none"))
        d.set(x, 1, z0 + 3, hopper("east"))
        d.set(x, 2, z0 + 3, WATER)
    # ends: glass walls x1-1 and x2+1 from y2 up to y6 over the five mechanism rows
    for xe in (x1 - 1, x2 + 1):
        for z in range(z0, z0 + 7):
            for y in range(2, 7):
                d.set(xe, y, z, GLASS)
    for z in (z0 + 2, z0 + 3, z0 + 4):
        d.set(x2 + 1, 1, z, hopper("east"))
        d.set(x1 - 1, 1, z, SB)
    # collector column
    cx = x2 + 2
    for z in (z0 + 2, z0 + 3, z0 + 4):
        d.set(cx, 1, z, hopper("south"))
    output(d, cx, 1, z0 + 5)
    return cx


# ================================================================================================ sugar cane
@design("sugarcane")
def sugarcane(pack, rel, L):
    """Observer + piston sugar cane farm (wiki: 'pillar 3 blocks: cane, piston at the second block, observer at the
    third'), planted on mud over hopper lines. 22 canes in two rows around a water row."""
    d = Design(pack, rel, size=(21, 16, 15), gy=1, paving="grass_block")
    X1, Z1, X2, Z2 = 1, 3, 19, 13
    shell(d, X1, Z1, X2, Z2, 7, floor="spruce_planks", wall="glass")
    for z in range(Z1 + 1, Z2):                               # stone side walls, glass only at the front/back
        for y in range(3, 7):
            if d.get(X1, y, z) == "minecraft:glass":
                d.set(X1, y, z, CB)
            if d.get(X2, y, z) == "minecraft:glass":
                d.set(X2, y, z, CB)
    cx = cane_module(d, 3, 14, 5, "sugar_cane[age=0]", "sugar_cane[age=0]")
    # walkway east of the module, door in the north wall over it
    for z in range(Z1 + 1, Z2):
        for x in (17, 18):
            d.set(x, 1, z, "spruce_planks")
    d.set(cx, 1, 4, "spruce_planks")
    entrance(d, 17, Z1, "Sugar Cane", "nothing", sign_side=1)
    # spare-cane chest corner and lighting
    d.set(18, 2, 12, "chest[facing=west,type=single,waterlogged=false]")
    d.set(18, 2, 11, "composter[level=0]")
    for x in range(X1 + 1, X2):                                # tie beam with hanging lanterns
        d.set(x, 7, 8, logb("x"))
    for x in (4, 8, 12, 16):
        lantern(d, x, 6, 8)
    roof(d, X1, Z1, X2, Z2, 8, axis="x")
    controller(d, 10)
    for z in (1, 2):
        d.set(10, 1, z, "gravel")
    for x in range(10, 18):
        d.set(x, 1, 2, "gravel")
    d.farm_test(expect={"minecraft:sugar_cane": 20}, ticks=9000)
    return d


# ================================================================================================ bamboo
@design("bamboo")
def bamboo(pack, rel, L):
    """Same proven observer + piston module as the cane farm (bamboo breaks when a piston pushes it; everything
    above falls as items). Bamboo needs light >= 9 where it grows, so it stands in a glass-roofed greenhouse
    (sky light passes glass) with lanterns for the night."""
    d = Design(pack, rel, size=(21, 12, 15), gy=1, paving="grass_block")
    X1, Z1, X2, Z2 = 1, 3, 19, 13
    shell(d, X1, Z1, X2, Z2, 7, floor="spruce_planks", wall="glass", post_step=3)
    cx = cane_module(d, 3, 14, 5, "bamboo[age=0,leaves=none,stage=0]", "bamboo[age=0,leaves=none,stage=0]")
    for z in range(Z1 + 1, Z2):
        for x in (17, 18):
            d.set(x, 1, z, "spruce_planks")
    d.set(cx, 1, 4, "spruce_planks")
    entrance(d, 17, Z1, "Bamboo", "nothing", sign_side=1)
    d.set(18, 2, 12, "chest[facing=west,type=single,waterlogged=false]")
    d.set(18, 2, 4, "composter[level=0]")
    # glass roof on spruce rafters: a low ridge of glass, stone-brick cornice
    for x in range(X1, X2 + 1):
        for z in range(Z1, Z2 + 1):
            edge = x in (X1, X2) or z in (Z1, Z2)
            d.set(x, 8, z, slab("stone_brick") if edge else GLASS)
    for x in range(X1 + 3, X2, 3):
        for z in range(Z1 + 1, Z2):
            d.set(x, 8, z, logb("z"))
    for x in range(X1 + 1, X2):
        d.set(x, 9, 8, "spruce_slab[type=bottom,waterlogged=false]")
    for x in (5, 11, 17):
        lantern(d, x, 7, 8)
    for x in (2, 8, 14):
        lantern(d, x, 7, 4)
    controller(d, 10)
    for z in (1, 2):
        d.set(10, 1, z, "gravel")
    for x in range(10, 18):
        d.set(x, 1, 2, "gravel")
    d.farm_test(expect={"minecraft:bamboo": 32}, ticks=6000)
    return d


# ================================================================================================ kelp
@design("kelp")
def kelp(pack, rel, L):
    """Observer + piston kelp farm (wiki: pistons break the 2nd kelp block, the observer above the piston watches
    the 3rd; flowing water at the top carries the floating items to hoppers).
      * Kelp only grows into water with amount 8 (a source or FALLING water): after a cut the cell is refilled by
        water falling from the source above it, so the kelp regrows.
      * All pistons of a row share one dust line: whenever any kelp of the row reaches its observer, every kelp of
        the row is cut at the 2nd block. A cut re-rolls the base kelp's random age, so a plant that stopped at
        height 2 (age 25) is freed by its neighbours instead of staying stuck.
      * Flowing water does not spread sideways over water, so the item stream on top (y6) runs as a centre lane
        over solid blocks (row K) fed from sources in the middle (x=9); it spills sideways into the lanes over the
        kelp rows, whose flow follows the centre lane's slope towards the hoppers at both ends ("flow" cells are
        air in the blueprint)."""
    d = Design(pack, rel, size=(19, 15, 14), gy=1, paving="grass_block")
    X1, Z1, X2, Z2 = 1, 3, 17, 11
    shell(d, X1, Z1, X2, Z2, 8, floor="spruce_planks", wall="glass")
    A, K, B = 6, 7, 8
    rows = ((5, A, 4, "south"), (9, B, 10, "north"))       # piston row, kelp row, dust row, facing
    KX1, KX2 = 4, 14
    kelps = (5, 7, 11, 13)
    for x in range(3, 16):
        for z in range(4, 11):
            d.set(x, 2, z, SB)
            for y in (3, 4, 5):
                d.set(x, y, z, SB)
    for x in range(KX1, KX2 + 1):
        for (pz, kz, dz, f) in rows:
            k = x in kelps
            if k:
                d.set(x, 3, kz, "kelp_plant")
                d.set(x, 4, kz, "kelp[age=0]")
                d.set(x, 5, kz, WATER)
                d.set(x, 4, pz, piston(f))
                d.set(x, 5, pz, observer(f))
            n, s = ("none", "side") if f == "south" else ("side", "none")
            if not k:
                n = s = "none"
            d.set(x, 5, dz, dust(n=n, s=s, e="side" if x < KX2 else "none", w="side" if x > KX1 else "none"))
            d.set(x, 6, pz, GLASS)
            d.set(x, 7, pz, GLASS)
        for z in (A, K, B):
            d.set(x, 6, z, WATER if (x == 9 and z == K) else AIR)     # item stream ("flow" except the source)
    for xe, wx in ((3, 2), (15, 16)):
        d.set(xe, 5, A, hopper("south"))
        d.set(xe, 5, B, hopper("north"))
        for y in (5, 4, 3):
            d.set(xe, y, K, hopper("down"))
        output(d, xe, 2, K)
        for z in range(5, 10):
            d.set(xe, 6, z, AIR if z in (A, K, B) else GLASS)
            d.set(wx, 6, z, GLASS)
            d.set(xe, 7, z, GLASS if z in (5, 9) else AIR)
        for z in range(Z1 + 1, Z2):
            d.set(wx, 1, z, "spruce_planks")
            for y in (2, 3, 4, 5):
                d.set(wx, y, z, AIR)
    for x in range(3, 16):
        for z in (4, 10):
            for y in (3, 4):
                d.set(x, y, z, SB)
    entrance(d, 2, Z1, "Kelp", "nothing", sign_side=1)
    d.door(16, 2, Z1, facing="north", wood="spruce")
    for z in (0, 1, 2):
        d.set(16, 1, z, "gravel")
    d.set(16, 2, 9, "chest[facing=west,type=single,waterlogged=false]")
    d.set(16, 2, 10, "smoker[facing=west,lit=false]")
    for x in range(X1 + 1, X2):                            # tie beam with lanterns over the tank
        d.set(x, 9, 7, logb("x"))
    for x in (2, 6, 12, 16):
        lantern(d, x, 8, 7)
    roof(d, X1, Z1, X2, Z2, 9, axis="x")
    controller(d, 9)
    for z in (1, 2):
        d.set(9, 1, z, "gravel")
    for x in range(2, 10):
        d.set(x, 1, 2, "gravel")
    d.farm_test(expect={"minecraft:kelp": 10}, ticks=12000,
                blocks=[(x, 6, z, "minecraft:water") for x in (3, 15) for z in (A, K, B)], blocks_min=99)
    return d


def collect(d, x1, x2, zs, y=1):
    """Hopper lines under the rows `zs` (x1..x2, running east) and a collector column at x2+1 running south into
    the output barrel just south of the last row. Returns the barrel position."""
    cx = x2 + 1
    for z in zs:
        for x in range(x1, x2 + 1):
            d.set(x, y, z, hopper("east"))
    zs = sorted(zs)
    for z in range(zs[0], zs[-1] + 1):
        d.set(cx, y, z, hopper("south"))
    output(d, cx, y, zs[-1] + 1)
    return cx, y, zs[-1] + 1


# ================================================================================================ pumpkin & melon
@design("pumpkinmelon")
def pumpkinmelon(pack, rel, L):
    """Observer + piston pumpkin / melon farm (the classic: stems on hydrated farmland, each with exactly one free
    fruit cell; an observer watches the fruit cell, a piston breaks the fruit). Pumpkin stems north of a water row,
    melon stems south of it. The fruit cells are MUD over hoppers, the stem farmland is on hoppers too, so whatever
    the piston pushes around ends up in the hopper lines.
    Per stem x: piston (y3) facing the fruit cell, observer above the fruit cell facing DOWN (watches it); its
    output (up) strongly powers the stone brick on top of it, which powers the dust line next to it (y5, over the
    piston row); the dust powers the brick under it, which sits on the piston -> the piston fires. (Dust cannot
    climb over an observer: observers are not redstone conductors.) Stems are placed full grown (age 7)."""
    d = Design(pack, rel, size=(21, 14, 15), gy=1, paving="grass_block")
    X1, Z1, X2, Z2 = 1, 3, 19, 11
    shell(d, X1, Z1, X2, Z2, 7, floor="spruce_planks", wall="glass")
    x1, x2 = 3, 13
    W = 7
    sides = ((4, 5, 6, "south", "pumpkin_stem[age=7]"), (10, 9, 8, "north", "melon_stem[age=7]"))
    for x in range(x1, x2 + 1):
        d.set(x, 2, W, WATER)
        for (pz, fz, sz, f, stem) in sides:
            d.set(x, 2, fz, MUD)
            d.set(x, 2, sz, "farmland[moisture=7]")
            d.set(x, 3, sz, stem)
            d.set(x, 2, pz, SB)
            d.set(x, 3, pz, piston(f))
            d.set(x, 4, fz, observer("down"))
            d.set(x, 5, fz, SB)                       # strongly powered by the observer below it
            d.set(x, 4, pz, SB)                       # sits on the piston; powered by the dust on it
            d.set(x, 5, pz, dust(e="side" if x < x2 else "none", w="side" if x > x1 else "none"))
    for xe in (x1 - 1, x2 + 1):                     # glass ends keep fruit cells closed and items in
        for z in range(4, 11):
            for y in (2, 3, 4, 5):
                d.set(xe, y, z, GLASS)
    cx, cy, cz = collect(d, x1, x2 + 1, (5, 6, 7, 8, 9))
    for z in (5, 6, 7, 8, 9):
        d.set(x2 + 1, 2, z, GLASS)
    for z in range(Z1 + 1, Z2):
        for x in (16, 17, 18):
            d.set(x, 1, z, "spruce_planks")
    d.set(15, 1, 4, "spruce_planks")
    entrance(d, 17, Z1, "Pumpkins+Melons", "nothing", sign_side=1)
    d.set(18, 2, 10, "chest[facing=west,type=single,waterlogged=false]")
    d.set(18, 2, 9, "crafting_table")
    for x in range(X1 + 1, X2):
        d.set(x, 7, 7, logb("x"))
    for x in (4, 9, 13, 17):
        lantern(d, x, 6, 7)
    # glass gable: sky light for the stems (they need light >= 9)
    roof(d, X1, Z1, X2, Z2, 8, axis="x")
    for x in range(X1 + 1, X2):
        for z in range(Z1, Z2 + 1):
            for y in range(8, 14):
                st = d.get(x, y, z)
                if "spruce_stairs" in st and x % 4 != 1:
                    d.set(x, y, z, st.replace("spruce_stairs", "glass").split("[")[0])
    controller(d, 10)
    for z in (1, 2):
        d.set(10, 1, z, "gravel")
    for x in range(10, 18):
        d.set(x, 1, 2, "gravel")
    d.farm_test(expect={"minecraft:pumpkin": 8, "minecraft:melon_slice": 16}, ticks=12000)
    return d
