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


def windows(d, X1, Z1, X2, Z2, ys=(3, 4)):
    """Glass-pane windows in a cobble wall: every wall cell at `ys` that is cobblestone and not next to a post."""
    for x in range(X1, X2 + 1):
        for z in range(Z1, Z2 + 1):
            if not (x in (X1, X2) or z in (Z1, Z2)):
                continue
            nb = [d.get(x + a, ys[0], z + b) for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            if any("log" in n for n in nb):
                continue
            for y in ys:
                if d.get(x, y, z) == "minecraft:cobblestone":
                    d.set(x, y, z, "glass_pane")


def entrance(d, x, z, name, bring, facing="north", path_to=0, sign_side=1, sign_wall=None, lines=None):
    """Door in the north wall at (x, 2, z), a wall sign beside it, a lantern over it and a gravel path north."""
    d.door(x, 2, z, facing=facing, wood="spruce")
    sx = x + sign_side
    if sign_wall:
        d.set(sx, 3, z, sign_wall)
    d.sign(sx, 3, z - 1, "north", lines or [name, "Farmworks", "Bring:", bring], wood="spruce")
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
    """Observer + piston kelp farm (wiki: pistons break the 2nd kelp block; "an observer facing the bottom kelp
    plant detects when it grows"). Per kelp column x (every other x, rows A north / B south of a water row K):
      base kelp (y3) on stone, cut cell (y4) above it, glass ceiling (y5) over the whole tank;
      observer (y3) beside the base, facing it: when the kelp grows into y4 the base turns from kelp head into kelp
      plant -> the observer pulses its back into the stone behind it (strong power) -> the lone dust on that stone
      (y4, a '+' with no neighbours, so it powers all four sides) powers the piston (y4) next to it -> the piston
      breaks the kelp in y4 and pushes the item into row K. The base turns back into a head (with a fresh random
      age, so it can always grow again) -> one more harmless pulse, then all is quiet: no clock, no loop.
      The cut cell refills as a SOURCE: its neighbours along x and in row K are water sources that are never
      pushed. Row K is one block of water under the glass ceiling, over a hopper line: floating items stay in the
      water cell and the hoppers under it take them (east -> output barrel)."""
    d = Design(pack, rel, size=(20, 14, 15), gy=1, paving="grass_block")
    X1, Z1, X2, Z2 = 1, 3, 18, 11
    shell(d, X1, Z1, X2, Z2, 7, floor="spruce_planks", wall="glass")
    A, K, B = 6, 7, 8
    rows = ((5, A, 4, "south"), (9, B, 10, "north"))       # piston/observer row, kelp row, back row, facing
    KX1, KX2 = 3, 15
    for x in range(KX1 - 1, KX2 + 2):
        for z in range(4, 11):
            for y in (2, 3, 4):
                d.set(x, y, z, SB)
            d.set(x, 5, z, GLASS if 5 <= z <= 9 else AIR)
    for x in range(KX1, KX2 + 1):
        k = (x - KX1) % 2 == 0
        d.set(x, 3, K, hopper("east"))
        d.set(x, 4, K, WATER)
        for (pz, kz, bz, f) in rows:
            d.set(x, 3, kz, "kelp[age=0]" if k else SB)
            d.set(x, 4, kz, WATER)
            if k:
                d.set(x, 3, pz, observer(f))
                d.set(x, 4, pz, piston(f))
                d.set(x, 4, bz, "redstone_wire[east=side,north=side,power=0,south=side,west=side]")
            else:
                d.set(x, 4, bz, SB)
    d.set(KX2 + 1, 3, K, hopper("down"))
    output(d, KX2 + 1, 2, K)
    for z in range(Z1 + 1, Z2):                            # walkways round the tank
        for x in (17,):
            d.set(x, 1, z, "spruce_planks")
            for y in (2, 3, 4, 5):
                d.set(x, y, z, AIR)
    entrance(d, 17, Z1, "Kelp", "nothing", sign_side=-1)
    d.set(17, 2, 10, "smoker[facing=north,lit=false]")
    for x in range(X1 + 1, X2):                            # tie beam with lanterns
        d.set(x, 7, 7, logb("x"))
    for x in (2, 6, 10, 14, 17):
        lantern(d, x, 6, 7)
    roof(d, X1, Z1, X2, Z2, 8, axis="x")
    controller(d, 9)
    for z in (1, 2):
        d.set(9, 1, z, "gravel")
    for x in range(9, 18):
        d.set(x, 1, 2, "gravel")
    d.farm_test(expect={"minecraft:kelp": 20}, ticks=12000)
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


def button(f):
    return f"stone_button[face=wall,facing={f},powered=false]"


# ================================================================================================ cocoa
@design("cocoa")
def cocoa(pack, rel, L):
    """Push-button cocoa harvester. Cocoa cannot be replanted by any vanilla machine (dispensers do not plant it),
    so this is the usual semi-automatic farm: a wall of jungle logs with pods on both faces, a row of pistons
    facing each face. Pressing the button pushes every piston into its pod (cocoa breaks when pushed), the beans
    drop into the hopper lines under the pod rows and run into the output barrel. Replant by hand from the
    walkway side (right-click the logs with cocoa beans); pods ripen on their own (no light needed).
    Wiring: the button powers the stone it sits on; the dust on that stone runs round both piston rows (y4), and
    every dust powers the stone under it, which sits right behind a piston."""
    d = Design(pack, rel, size=(19, 13, 14), gy=1, paving="grass_block")
    X1, Z1, X2, Z2 = 1, 3, 17, 11
    shell(d, X1, Z1, X2, Z2, 6, floor="spruce_planks", wall=CB, post_step=4)
    windows(d, X1, Z1, X2, Z2)
    x1, x2 = 3, 13
    LOGZ = 7
    sides = ((5, 6, 4, "south", "north"), (9, 8, 10, "north", "south"))   # piston row, pod row, back row
    for x in range(2, 15):
        for z in range(4, 11):
            d.set(x, 2, z, SB)
    for x in range(x1, x2 + 1):
        d.set(x, 3, LOGZ, "jungle_log[axis=y]")
        d.set(x, 4, LOGZ, "jungle_leaves[distance=1,persistent=true,waterlogged=false]")
        for (pz, cz, bz, f, podf) in sides:
            d.set(x, 2, cz, hopper("east"))
            d.set(x, 3, cz, f"cocoa[age=2,facing={'south' if cz < LOGZ else 'north'}]")
            d.set(x, 3, pz, piston(f))
            d.set(x, 3, bz, SB)
    for z in range(4, 11):                                  # west end: stone column carrying the dust round
        d.set(2, 3, z, SB)
    for x in range(2, 15):
        e = "side" if x < 14 else "none"
        d.set(x, 4, 4, dust(e=e, w="side" if x > 2 else "none", s="side" if x == 2 else "none"))
        if x <= 13:
            d.set(x, 4, 10, dust(e="side" if x < 13 else "none", w="side" if x > 2 else "none",
                                 n="side" if x == 2 else "none"))
    for z in range(5, 10):
        d.set(2, 4, z, dust(n="side", s="side"))
    d.set(2, 4, 7, "repeater[delay=1,facing=north,locked=false,powered=false]")   # input from the north
    d.set(14, 3, 4, SB)
    d.set(15, 3, 4, button("east"))
    for z in range(5, 10):
        d.set(14, 3, z, GLASS)
    # collector: pod-row hoppers run east into x=14, then south into the barrel
    d.set(14, 2, 6, hopper("south"))
    d.set(14, 2, 7, hopper("south"))
    d.set(14, 2, 8, hopper("south"))
    output(d, 14, 2, 9)
    d.set(14, 3, 9, GLASS)
    for z in range(Z1 + 1, Z2):
        for x in (15, 16):
            d.set(x, 1, z, "spruce_planks")
    entrance(d, 16, Z1, "Cocoa", "cocoa beans", sign_side=-1)
    d.set(16, 2, 10, "chest[facing=west,type=single,waterlogged=false]")
    d.sign(15, 3, 5, "east", ["Press the", "button to", "harvest,", "then replant"], wood="spruce")
    for x in range(X1 + 1, X2):
        d.set(x, 6, 7, logb("x"))
    for x in (4, 8, 12, 16):
        lantern(d, x, 5, 7) if d.air(x, 5, 7) else None
    roof(d, X1, Z1, X2, Z2, 7, axis="x")
    controller(d, 9)
    for z in (1, 2):
        d.set(9, 1, z, "gravel")
    for x in range(9, 17):
        d.set(x, 1, 2, "gravel")
    d.farm_test(expect={"minecraft:cocoa_beans": 40}, presses=[(15, 3, 4)], ticks=600)
    return d


# ================================================================================================ sweet berries
@design("sweetberry")
def sweetberry(pack, rel, L):
    """Fox-picked sweet berry farm (the vanilla way to harvest berries without breaking the bushes: a fox picks a
    ripe bush, keeps one berry in its mouth and drops the rest, the bush stays and regrows). Bushes stand on
    hydrated FARMLAND (15/16 high) over hoppers, so dropped berries are inside the hoppers' pick-up area; the fox
    lanes between the bush rows are farmland over hoppers too. Foxes are too small to trample farmland. The pen
    has no roof: foxes only sleep in the daytime under cover, and the bushes need light >= 9 to grow.
    The water that keeps the farmland wet sits in the middle, under a slab the foxes walk over.
    The fox lanes are FULL blocks (coarse dirt): the fox's berry search (MoveToBlockGoal) only looks at its own
    block level and the two below, and a fox standing on 15/16-high farmland counts as one level lower, so it
    would never see bushes standing on the same farmland. Berries pop out at the bush itself and land on the
    bush's farmland, where the hopper under it takes them."""
    d = Design(pack, rel, size=(19, 9, 14), gy=1, paving="grass_block")
    PX1, PZ1, PX2, PZ2 = 3, 5, 13, 11                       # pen walls
    for x in range(PX1, PX2 + 1):
        for z in range(PZ1, PZ2 + 1):
            edge = x in (PX1, PX2) or z in (PZ1, PZ2)
            d.set(x, 1, z, SB)
            if edge:
                d.set(x, 2, z, SB)
                for y in (3, 4):
                    d.set(x, y, z, "glass_pane")
                d.set(x, 5, z, slab("spruce", "bottom"))
    for (x, z) in ((PX1, PZ1), (PX2, PZ1), (PX1, PZ2), (PX2, PZ2), (8, PZ1), (8, PZ2), (PX1, 8), (PX2, 8)):
        for y in (2, 3, 4):
            d.set(x, y, z, logb())
        d.set(x, 5, z, "lantern[hanging=false,waterlogged=false]")
    zs = list(range(PZ1 + 1, PZ2))                          # 6..10
    collect(d, PX1 + 1, PX2, zs)
    WX, WZ = 8, 8
    for x in range(PX1 + 1, PX2):
        for z in zs:
            if (x, z) == (WX, WZ):
                d.set(x, 2, z, WATER)
                d.set(x, 3, z, slab("spruce", "bottom"))
                continue
            if z in (6, 10) or (z == 8 and abs(x - WX) > 1):
                d.set(x, 2, z, "farmland[moisture=7]")
                d.set(x, 3, z, "sweet_berry_bush[age=3]")
            else:                                           # fox lanes: full blocks (see docstring)
                d.set(x, 2, z, "coarse_dirt")
    d.door(8, 2, PZ1, facing="north", wood="spruce")
    d.set(8, 1, PZ1, SB)
    # east lean-to over the collector: barrel, chest, roof
    SX1, SX2 = 14, 17
    for x in range(SX1, SX2 + 1):
        for z in range(4, 13):
            edge = x == SX2 or z in (4, 12)
            if x == SX1 and z in range(PZ1, PZ2 + 1):
                continue
            d.set(x, 1, z, SB if edge else "spruce_planks" if d.get(x, 1, z) in ("minecraft:grass_block",) else d.get(x, 1, z))
            for y in (2, 3, 4):
                d.set(x, y, z, (SB if y == 2 else CB) if edge else AIR)
    for (x, z) in ((SX2, 4), (SX2, 12), (SX1, 4), (SX1, 12), (SX2, 8)):
        for y in (2, 3, 4):
            d.set(x, y, z, logb())
    for z in (6, 10):
        d.set(SX2, 3, z, "glass_pane")
    for z in range(3, 14):                                   # lean-to roof sloping east
        for x, y in ((14, 6), (15, 6), (16, 5), (17, 5), (18, 4)):
            if x == 14:
                d.set(x, 5, z, logb("z")) if 4 <= z <= 12 else None
                d.set(x, 6, z, stair("spruce", "west"))
            elif y == 6:
                d.set(x, 6, z, stair("spruce", "west"))
            else:
                d.set(x, y, z, stair("spruce", "west"))
    for z in range(4, 13):
        d.set(15, 5, z, PLANK) if 5 <= z <= 11 else None
    for x in (15, 16):
        for y in (2, 3):
            d.set(x, y, 4, AIR)
    d.door(16, 2, 4, facing="north", wood="spruce")
    d.set(15, 2, 4, SB)
    d.set(15, 3, 4, CB)
    d.sign(15, 3, 3, "north", ["Sweet Berries", "Farmworks", "Bring:", "2 foxes (leads)"], wood="spruce")
    d.set(16, 2, 12 - 1, "chest[facing=west,type=single,waterlogged=false]")
    lantern(d, 16, 4, 8)
    d.set(16, 5, 8, PLANK)
    # paths
    controller(d, 9)
    for z in (1, 2):
        d.set(9, 1, z, "gravel")
    for x in range(8, 17):
        d.set(x, 1, 3, "gravel")
    for z in (3, 4):
        d.set(8, 1, z, "gravel")
    d.set(9, 1, 3, "gravel")
    d.farm_test(expect={"minecraft:sweet_berries": 12}, spawns=[("minecraft:fox", 6, 3, 7, 2)], ticks=16000)
    return d


def repeater(inp, delay=4):
    """Repeater whose INPUT is on side `inp` (Java: facing = input side), output on the opposite side."""
    return f"repeater[delay={delay},facing={inp},locked=false,powered=false]"


def dispenser(f):
    return f"dispenser[facing={f},triggered=false]"


# ================================================================================================ flowers
@design("flowers")
def flowers(pack, rel, L):
    """Bone-meal flower farm with a water flush (the common design: dispensers bone-meal a grass bed, a water
    dispenser washes the flowers into hoppers). One button does a whole cycle on every press:
      * three water dispensers (west end, y3) either place their water or pick it up again (they alternate);
      * the same pulse runs through repeaters (3 x 4 ticks to the first, 5 x 4 to the second bone-meal dispenser),
        so the bone meal comes AFTER the water has drained back (flowing water vanishes 5 ticks per block).
    Press A: water on -> it flows east over the grass (6 blocks of flow), breaks every flower / grass tuft and
    carries the items to the hoppers under the stream end (x=11). The bone meal then finds water on the grass and
    is not used. Press B: water off -> the bone meal grows new flowers on the dry grass. The water source cells
    stand on stone, not grass (grass under a full water block turns to dirt)."""
    d = Design(pack, rel, size=(15, 14, 13), gy=1, paving="grass_block")
    X1, Z1, X2, Z2 = 0, 3, 14, 11
    shell(d, X1, Z1, X2, Z2, 6, floor="spruce_planks", wall=CB, post_step=3)
    windows(d, X1, Z1, X2, Z2)
    rows = (6, 7, 8)
    for x in range(2, 13):
        for z in range(4, 11):
            d.set(x, 2, z, SB)
    for x in range(4, 12):
        for z in (5, 9):
            d.set(x, 3, z, GLASS)
    for z in rows:
        d.set(3, 3, z, dispenser("east"))
        d.set(3, 4, z, dust(n="side", s="side"))
        d.set(4, 2, z, SB)
        d.set(4, 3, z, AIR)                                  # water source (from the dispenser)
        for x in range(5, 11):
            d.set(x, 2, z, "grass_block[snowy=false]")
        d.set(11, 2, z, hopper("south"))
        d.set(12, 3, z, GLASS)
    output(d, 11, 2, 9)
    d.set(11, 3, 9, GLASS)
    # controls: button on the west aisle, dust over the water dispensers, delayed line to the bone meal
    for z in (4, 5, 9):
        d.set(3, 3, z, SB)
    d.set(3, 4, 4, dust(s="side"))
    d.set(2, 3, 4, button("west"))
    d.set(3, 4, 5, dust(n="side", s="side"))
    d.set(3, 4, 9, dust(n="side", e="side"))
    line = {4: repeater("west"), 5: repeater("west"), 6: repeater("west"), 7: dust(e="side", w="side"),
            8: repeater("west"), 9: repeater("west"), 10: dust(w="side")}
    for x, st in line.items():
        d.set(x, 3, 9, SB if x in (7, 10) else GLASS)
        d.set(x, 4, 9, st)
    for x in (7, 10):
        d.set(x, 2, 9, dispenser("north"))                   # bone meal, aimed at the grass row z=8
    d.sign(2, 3, 5, "west", ["Press: water", "on / off.", "Bone meal", "after drain"], wood="spruce")
    for z in range(Z1 + 1, Z2):
        d.set(1, 1, z, "spruce_planks")
        for y in (2, 3, 4):
            d.set(1, y, z, AIR)
        d.set(2, 1, z, "spruce_planks")
        if z not in (4, 5):
            for y in (2, 3):
                d.set(2, y, z, AIR)
    for x in range(2, 14):
        d.set(x, 1, 10, "spruce_planks")
        for y in (2, 3, 4):
            d.set(x, y, 10, AIR)
    d.set(12, 2, 9, "chest[facing=south,type=single,waterlogged=false]")
    entrance(d, 1, Z1, "Flowers", "", sign_side=1, lines=["Flower Farm", "Bring:", "bone meal,", "3 water buckets"])
    for x in range(X1 + 1, X2):
        d.set(x, 6, 7, logb("x"))
    for x in (1, 7, 13):
        lantern(d, x, 5, 7)
    roof(d, X1, Z1, X2, Z2, 7, axis="x")
    controller(d, 7)
    for z in (1, 2):
        d.set(7, 1, z, "gravel")
    for x in range(1, 8):
        d.set(x, 1, 2, "gravel")
    inputs = {(3, 3, z): [("minecraft:water_bucket", 1)] for z in rows}
    inputs.update({(x, 2, 9): [("minecraft:bone_meal", 64)] for x in (7, 10)})
    d.farm_test(expect={"minecraft:poppy": 4}, inputs=inputs, presses=[(2, 3, 4)], ticks=6000)
    return d


# ================================================================================================ villager crops
@design("villagercrops")
def villagercrops(pack, rel, L):
    """Villager crop farm: a farmer villager (job site: the composter in the middle of the field) harvests ripe
    wheat / carrots / potatoes and replants from what it picks up. The whole field is FARMLAND over hoppers, so
    a good share of every harvest drops straight into the hoppers before the farmer grabs it; the farmer also
    composts its spare seeds and the hopper under the composter takes the bone meal. Everything runs east into
    the output barrel. Open sky over the field (crops need light >= 9); glass walls keep the villager in.
    Water (two sources under slabs) keeps the farmland wet."""
    d = Design(pack, rel, size=(17, 9, 15), gy=1, paving="grass_block")
    FX1, FZ1, FX2, FZ2 = 3, 5, 11, 11                       # field
    for x in range(FX1 - 1, FX2 + 2):                      # low wall: stone-brick plinth, glass panes, slab cap
        for z in range(FZ1 - 1, FZ2 + 2):
            edge = x in (FX1 - 1, FX2 + 1) or z in (FZ1 - 1, FZ2 + 1)
            d.set(x, 1, z, SB)
            if edge:
                d.set(x, 2, z, SB)
                d.set(x, 3, z, "glass_pane")
                d.set(x, 4, z, slab("stone_brick"))
    for (x, z) in ((FX1 - 1, FZ1 - 1), (FX2 + 1, FZ1 - 1), (FX1 - 1, FZ2 + 1), (FX2 + 1, FZ2 + 1),
                   (7, FZ2 + 1), (FX1 - 1, 8), (FX2 + 1, 8)):
        d.set(x, 2, z, logb())
        d.set(x, 3, z, logb())
        d.set(x, 4, z, "lantern[hanging=false,waterlogged=false]")
    collect(d, FX1, FX2 + 1, list(range(FZ1, FZ2 + 1)))
    crops = {5: "wheat", 6: "carrots", 7: "potatoes", 9: "potatoes", 10: "carrots", 11: "wheat"}
    for x in range(FX1, FX2 + 1):
        for z in range(FZ1, FZ2 + 1):
            if z == 8 and x in (5, 9):
                d.set(x, 2, z, WATER)
                d.set(x, 3, z, slab("spruce"))
            elif z == 8 and x == 7:
                d.item(x, 2, z, "composter")
            else:
                d.set(x, 2, z, "farmland[moisture=7]")
                if z in crops:
                    d.set(x, 3, z, f"{crops[z]}[age=7]")
    for z in range(FZ1, FZ2 + 1):
        d.set(FX2 + 1, 2, z, SB)
    # gate house on the north side: door into the field, barrel side aisle on the east
    d.door(7, 2, FZ1 - 1, facing="north", wood="spruce")
    d.set(7, 4, FZ1 - 1, SB)
    d.set(15, 2, 12, "chest[facing=west,type=single,waterlogged=false]")
    d.set(15, 2, 11, "hay_block[axis=y]")
    d.set(15, 3, 11, "lantern[hanging=false,waterlogged=false]")
    d.set(6, 3, FZ1 - 1, SB)
    d.sign(6, 3, FZ1 - 2, "north", ["Villager Farm", "Farmworks", "Bring:", "1 villager"], wood="spruce")
    controller(d, 8)
    for z in range(0, FZ1 - 1):
        d.set(7, 1, z, "gravel")
    for z in range(2, 14):
        d.set(14, 1, z, "gravel")
    for x in range(7, 15):
        d.set(x, 1, 2, "gravel")
    d.farm_test(expect={"minecraft:carrot": 8, "minecraft:potato": 4}, spawns=[("minecraft:villager", 4, 3, 8, 1)],
                ticks=8000)
    return d


# ================================================================================================ tree farm
@design("treefarm")
def treefarm(pack, rel, L):
    """Player-harvested birch grove (birch: a straight 5-7 log trunk, no branches, no 2x2 needed, so every log is
    reached from the ground or one step up). Six saplings on dirt, four blocks apart so the crowns don't block
    each other, fenced and lit by lanterns on the posts (no mob spawns at night). Next to it a tool shed with a
    sapling chest, a log barrel, crafting table and chopping block. Replant the sapling the leaves drop.
    Fully automatic tree farms in Java need TNT duping or wither-cages; this one is meant to be easy to chop."""
    d = Design(pack, rel, size=(20, 9, 16), gy=1, paving="grass_block")
    GX1, GZ1, GX2, GZ2 = 1, 3, 13, 14                       # grove fence
    for x in range(GX1, GX2 + 1):
        for z in (GZ1, GZ2):
            d.set(x, 2, z, FENCE)
    for z in range(GZ1, GZ2 + 1):
        for x in (GX1, GX2):
            d.set(x, 2, z, FENCE)
    for (x, z) in ((GX1, GZ1), (GX2, GZ1), (GX1, GZ2), (GX2, GZ2), (GX1, 8), (GX2, 8), (4, GZ1), (10, GZ1),
                   (4, GZ2), (10, GZ2)):
        d.set(x, 2, z, logb())
        d.set(x, 3, z, "lantern[hanging=false,waterlogged=false]")
    d.set(7, 2, GZ1, "spruce_fence_gate[facing=north,in_wall=false,open=false,powered=false]")
    saps = [(x, z) for x in (3, 7, 11) for z in (6, 11)]
    for x in range(GX1 + 1, GX2):
        for z in range(GZ1 + 1, GZ2):
            d.set(x, 1, z, "grass_block[snowy=false]")
    for (x, z) in saps:
        d.set(x, 1, z, "dirt")
        d.set(x, 2, z, "birch_sapling[stage=0]")
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            d.set(x + dx, 1, z + dz, "coarse_dirt")
    for z in range(GZ1 + 1, GZ2):                           # gravel walk up the middle of the grove
        d.set(5, 1, z, "gravel") if z not in (6, 11) else None
        d.set(9, 1, z, "gravel") if z not in (6, 11) else None
    for x in range(GX1 + 1, GX2):
        d.set(x, 1, 9, "gravel")
    # tool shed
    SX1, SZ1, SX2, SZ2 = 14, 4, 19, 10
    shell(d, SX1, SZ1, SX2, SZ2, 4, floor="spruce_planks", wall=CB, post_step=3)
    for z in (6, 8):
        d.set(SX2, 3, z, "glass_pane")
    d.set(SX1, 3, 7, "glass_pane")
    d.door(16, 2, SZ1, facing="north", wood="spruce")
    d.set(18, 2, 9, "chest[facing=north,type=single,waterlogged=false]")
    d.set(18, 2, 5, barrel())
    d.set(18, 2, 7, "crafting_table")
    d.set(15, 2, 9, "oak_log[axis=y]")
    d.set(15, 2, 5, "grindstone[face=floor,facing=north]")
    d.gable(SX1, SZ1, SX2, SZ2, 5, axis="z", stairs="spruce_stairs", ridge="spruce_slab", end=PLANK)
    lantern(d, 16, 4, 7)
    d.set(16, 5, 7, PLANK) if d.air(16, 5, 7) else None
    d.sign(17, 3, SZ1 - 1, "north", ["Birch Grove", "Farmworks", "Bring: axe,", "birch saplings"], wood="spruce")
    d.set(17, 3, SZ1, PLANK) if "glass" in d.get(17, 3, SZ1) else None
    controller(d, 10)
    for z in range(0, GZ1):
        d.set(7, 1, z, "gravel")
        d.set(16, 1, z, "gravel")
    for x in range(7, 17):
        d.set(x, 1, 1, "gravel")
    d.farm_test(expect={}, blocks=[(x, 2, z, "minecraft:birch_log") for (x, z) in saps], blocks_min=4, ticks=8000)
    return d
