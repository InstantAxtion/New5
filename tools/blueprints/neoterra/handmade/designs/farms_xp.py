"""
Farmworks mob & XP farms (decorations/xpfarms/): classic spawning-platform towers (Java 1.21.1, no spawners).

All of them share one layout, the "plus" platform of the classic mob tower:

        a 2x2 (slime farm: 3x3) drop hole in the middle, four arms 8 long running out from it.

  * water farms (creeper, xp grinder, spider): every arm is a water channel with two (three) water SOURCES at its
    outer end (d = 8). The water flows 7 cells towards the hole, so the weakest flowing water (level 7, amount 1)
    lies in the cell next to the hole and cannot spread any further: the hole stays dry, the water never pours
    down the shaft (FlowingFluid: a spread needs amount - dropOff > 0). Only the 8 sources per floor are placed;
    the channel cells marked "flow" are air in the blueprint and fill with flowing water in game.
    The four quadrants between the arms are the spawning floors, raised one block above the channel floor so the
    water cannot spread onto them; mobs wander off the edge into a channel and are carried into the hole.
  * dry farms (gold, drowned, slime): the platform is a cross of 2-wide (3-wide) corridors whose only connection
    is the 2x2 centre. The centre cells hold OPEN trapdoors over the hole: WalkNodeEvaluator types a trapdoor
    cell as PathType.TRAPDOOR (malus 0, accepted as a standing node), so a mob strolling from one arm to another
    paths straight across the centre and drops (the well-known "trapdoor trick"). Open trapdoors are not
    waterlogged, so flowing water can never enter them (drowned tank). Slimes do not path at all, they hop in
    random directions and fall in.

Kill: fall damage in the shaft (ceil(fall - 3) >= max health; armour does not reduce it), or campfires over hoppers
(slimes split, so the children are finished by campfire damage - CampfireBlock.entityInside hurts only living
entities, items lie on the campfire and the hopper below sucks them in, a campfire is not a full block).
Collection: hoppers under the landing (facing north, output side) into double chests tagged farm_output.

Fall heights (feet level of the lowest spawning floor -> landing):
  creeper  29 -> hopper bowl 3.69 : 25.3 blocks, 23 damage  (creeper 20 hp)
  spider   26 -> hopper top 4     : 22 blocks,   19 damage  (spider 16 hp; 4x4 shaft so they cannot climb)
  xp       30 -> closed trapdoor 8.19 : 21.8 blocks, 19 damage -> 20-hp mobs are left on 1 hp (XP mode),
           30 -> hopper 3.69 (trapdoors open, AUTO mode): 26.3 blocks, 24 damage
  gold     29 -> 3.69 : 25.3 / drowned 29 -> 3.69 : 25.3 (both 20 hp)

Repeaters / comparators are not used. Redstone (xp grinder only): lever -> redstone dust -> trapdoors, see there.
"""
from hm import Design, design, AIR

SB = "stone_bricks"
CB = "cobblestone"
MSB = "mossy_stone_bricks"
LOG = "stripped_spruce_log"
GLASS = "glass"
WATER = "water[level=0]"
FENCE = "spruce_fence[east=false,north=false,south=false,waterlogged=false,west=false]"
HX, HZ = 9, 11                       # north-west cell of the drop hole
Z0 = 2                               # north wall of the platform


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


def trapdoor(facing, half="bottom", open_=True, powered=False, wood="spruce"):
    """facing = the side the player faced when placing; an OPEN trapdoor lies against the side OPPOSITE to
    `facing` (TrapDoorBlock: facing=east -> box x 0..3, the west edge)."""
    return (f"{wood}_trapdoor[facing={facing},half={half},open={'true' if open_ else 'false'},"
            f"powered={'true' if powered else 'false'},waterlogged=false]")


def hopper(facing):
    return f"hopper[enabled=true,facing={facing}]"


def campfire():
    return "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]"


# ------------------------------------------------------------------------------------------------ plus geometry
def classify(x, z, w):
    """('hole', 0, None) / ('arm', d, side) with d = 1 next to the hole ... 8 at the outer end / ('quad', dz, None)
    with dz = distance from the hole rows in z (used for the creeper strips)."""
    hx1, hz1 = HX + w - 1, HZ + w - 1
    inx, inz = HX <= x <= hx1, HZ <= z <= hz1
    if inx and inz:
        return "hole", 0, None
    if inx:
        return ("arm", HZ - z, "n") if z < HZ else ("arm", z - hz1, "s")
    if inz:
        return ("arm", HX - x, "w") if x < HX else ("arm", x - hx1, "e")
    dz = HZ - z if z < HZ else z - hz1
    return "quad", dz, None


def inner(w):
    n = w + 16
    return range(1, n + 1), range(Z0 + 1, Z0 + 1 + n)


def outer(w):
    n = w + 16
    return 0, Z0, n + 1, Z0 + n + 1                      # x1, z1, x2, z2 of the platform walls


def platform_walls(d, w, y1, y2, banded=True):
    """Outer platform walls (cobble, stone-brick bands, spruce-log posts at the corners and every 5)."""
    X1, Z1, X2, Z2 = outer(w)
    for y in range(y1, y2 + 1):
        for x in range(X1, X2 + 1):
            for z in range(Z1, Z2 + 1):
                if x in (X1, X2) or z in (Z1, Z2):
                    edge_x = x in (X1, X2)
                    edge_z = z in (Z1, Z2)
                    post = (edge_x and edge_z) or (edge_z and (x - X1) % 5 == 0 and X1 < x < X2) or \
                           (edge_x and (z - Z1) % 5 == 0 and Z1 < z < Z2)
                    d.set(x, y, z, logb() if post else CB)


def band(d, w, y, block=SB):
    X1, Z1, X2, Z2 = outer(w)
    for x in range(X1, X2 + 1):
        for z in range(Z1, Z2 + 1):
            if x in (X1, X2) or z in (Z1, Z2):
                d.set(x, y, z, block)


def water_floor(d, w, y0, kind):
    """One spawning floor of a water farm. y0 = channel floor block; returns the ceiling y.
    kind 'xp'     : quadrants raised 1, 2 air high (every hostile mob except endermen fits)
    kind 'creeper': quadrants cut into 1-wide strips (spiders, 1.4 wide, cannot spawn) under closed top-half
                    trapdoors: 2 - 3/16 = 1.8125 clear -> creepers (1.7) fit, zombies / skeletons /
                    witches (1.95+) do not. Creepers are the only mob that can spawn on this floor.
    kind 'spider' : ONE block high, quadrants at the SAME level as the water (a step would let spiders climb out
                    of the channel): every quadrant cell next to a channel holds a standing sign - flowing water
                    cannot enter a sign (FlowingFluid.canHoldFluid), mobs walk through it. Only spiders (0.9 tall)
                    spawn; the open quadrants give them the 3x3 room they need."""
    pitch = 2 if kind == "spider" else 4
    xs, zs = inner(w)
    X1, Z1, X2, Z2 = outer(w)
    d.fill(X1, y0, Z1, X2, y0, Z2, SB)
    platform_walls(d, w, y0 + 1, y0 + pitch - 1)
    for x in xs:
        for z in zs:
            k, dist, _ = classify(x, z, w)
            if k == "hole":
                d.clear(x, y0, z, x, y0 + pitch - 1, z)
            elif k == "arm":
                d.set(x, y0 + 1, z, WATER if dist == 8 else AIR)          # sources at d=8, else: flow
                d.clear(x, y0 + 2, z, x, y0 + pitch - 1, z)
            elif kind == "spider":
                edge = any(classify(x + a, z + b, w)[0] == "arm" for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))
                           if (x + a) in xs and (z + b) in zs)
                d.set(x, y0 + 1, z, f"spruce_sign[rotation={(x * 3 + z) % 16},waterlogged=false]" if edge else AIR)
            else:
                d.set(x, y0 + 1, z, "stone")                                # raised spawning floor
                if kind == "creeper":
                    if dist % 2 == 1:                                       # strip
                        d.set(x, y0 + 2, z, AIR)
                        d.set(x, y0 + 3, z, trapdoor("north", "top", False))
                    else:                                                   # separator
                        d.set(x, y0 + 2, z, SB)
                        d.set(x, y0 + 3, z, SB)
                else:
                    d.clear(x, y0 + 2, z, x, y0 + pitch - 1, z)
    return y0 + pitch


def cross_floor(d, w, y0, pitch, floor, fill_arm, centre, wall=CB, light=None):
    """One floor of a dry farm: a cross of w-wide corridors 8 long. Cells outside the cross stay as they are
    (open air) - the platform IS the cross. fill_arm(x, y, z, d) fills an arm cell at height y (y0+1..),
    centre(x, y, z) a hole cell. light: every 3rd wall cell at y0+2 becomes this block."""
    xs, zs = inner(w)
    for x in range(0, w + 18):
        for z in range(Z0, Z0 + w + 18):
            k = None
            if x in xs and z in zs:
                k, dist, side = classify(x, z, w)
                if k == "quad":
                    k = None
            near = any(classify(x + a, z + b, w)[0] in ("arm", "hole")
                       for a in (-1, 0, 1) for b in (-1, 0, 1)
                       if (x + a) in xs and (z + b) in zs)
            if k is None and not near:
                continue
            d.set(x, y0, z, floor if k else SB)
            for y in range(y0 + 1, y0 + pitch):
                if k == "arm":
                    fill_arm(x, y, z, dist)
                elif k == "hole":
                    centre(x, y, z)
                else:
                    post = (x + z) % 5 == 0
                    blk = wall
                    if light and y == y0 + 2 and (x + z) % 3 == 0:
                        blk = light
                    elif post:
                        blk = logb()
                    d.set(x, y, z, blk)
            if k == "hole":
                d.set(x, y0, z, AIR)


def cross_cap(d, w, y):
    """Roof over the cross: stone-brick deck with spruce bottom slabs on top (no mob can spawn on a bottom slab)."""
    xs, zs = inner(w)
    for x in range(0, w + 18):
        for z in range(Z0, Z0 + w + 18):
            near = any((x + a) in xs and (z + b) in zs and classify(x + a, z + b, w)[0] in ("arm", "hole")
                       for a in (-1, 0, 1) for b in (-1, 0, 1))
            if near:
                d.set(x, y, z, SB)
                d.set(x, y + 1, z, slab("spruce"))


def roof_box(d, w, y):
    """Flat roof over a box platform: the ceiling layer at y (stone bricks), spruce slab deck and a parapet with
    coping, lanterns at the corners (lit and slabbed: nothing spawns up there)."""
    X1, Z1, X2, Z2 = outer(w)
    d.fill(X1, y, Z1, X2, y, Z2, SB)
    d.flat(X1, Z1, X2, Z2, y + 1, slab="spruce_slab[type=bottom,waterlogged=false]", parapet=SB,
           coping="stone_brick_slab")
    for x, z in ((X1 + 1, Z1 + 1), (X2 - 1, Z1 + 1), (X1 + 1, Z2 - 1), (X2 - 1, Z2 - 1)):
        d.set(x, y + 1, z, FENCE)
        lantern(d, x, y + 2, z, hanging=False)


# ------------------------------------------------------------------------------------------------ the base
def base_room(d, X1, Z1, X2, Z2, top, door_x, floor="smooth_stone", windows=(), roof="gable", beams=(6, 13),
              lamps_z=(7, 14)):
    """Stone-brick plinth, cobble walls with spruce-log posts and a log beam on top, spruce gable roof,
    door in the north wall."""
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
            d.set(x, y, z, logb())
    for (x, y, z) in windows:
        d.set(x, y, z, "glass_pane")
    d.door(door_x, gy + 1, Z1, "south", "spruce")
    for x in beams:                                       # tie beams with lanterns hanging under them
        for z in range(Z1 + 1, Z2):
            d.set(x, top, z, logb("z"))
        for z in lamps_z:
            lantern(d, x, top - 1, z)
    if roof == "gable":
        d.gable(X1, Z1, X2, Z2, top + 1, axis="x", end="spruce_planks")
    else:
        d.flat(X1, Z1, X2, Z2, top + 1, slab="spruce_slab[type=bottom,waterlogged=false]")


def approach(d, door_x, Z1, lines):
    for z in range(0, Z1):
        for x in (door_x - 1, door_x, door_x + 1):
            d.set(x, 1, z, "gravel")
    d.hut(10, 1, 0)
    for x in (door_x - 2, door_x + 2):
        d.set(x, 2, Z1 - 1, FENCE)
        lantern(d, x, 3, Z1 - 1, hanging=False)
    d.sign(door_x + 1, 3, Z1 - 1, "north", lines, "spruce")


def yard(d, w, lamp_cells):
    """Ground under the platform: grass with lantern posts (lit, so nothing spawns in the platform's shadow) and
    stone-brick corner piers carrying the platform."""
    X1, Z1, X2, Z2 = outer(w)
    for (x, z) in lamp_cells:
        d.set(x, 2, z, FENCE)
        d.set(x, 3, z, FENCE)
        lantern(d, x, 4, z, hanging=False)


def piers(d, w, y_top):
    X1, Z1, X2, Z2 = outer(w)
    for (x, z) in ((X1, Z1), (X2, Z1), (X1, Z2), (X2, Z2)):
        d.set(x, 1, z, SB)
        for y in range(2, y_top + 1):
            d.set(x, y, z, SB if y % 6 else "chiseled_stone_bricks")


def column(d, cx1, cz1, cx2, cz2, y1, y2):
    """Drop shaft: air inside cx1..cx2 / cz1..cz2, stone-brick ring around it with arrow-slit windows."""
    for y in range(y1, y2 + 1):
        for x in range(cx1 - 1, cx2 + 2):
            for z in range(cz1 - 1, cz2 + 2):
                if cx1 <= x <= cx2 and cz1 <= z <= cz2:
                    d.set(x, y, z, AIR)
                else:
                    corner = x in (cx1 - 1, cx2 + 1) and z in (cz1 - 1, cz2 + 1)
                    d.set(x, y, z, logb() if corner else (MSB if (x * 7 + y * 3 + z) % 11 == 0 else SB))


def collector(d, cx1, cz1, cx2, cz2, ytop, y_hop=3, landing="hopper"):
    """Landing over hoppers (y_hop) in a glass box up to ytop. Each column of hoppers faces north; the north row
    feeds a row of chests (y_hop, z = cz1-1) standing on stone bricks, opened from the room (z = cz1-2).
    landing='campfire': lit campfires on the hoppers (slime farm)."""
    hy = y_hop
    for x in range(cx1, cx2 + 1):
        for z in range(cz1, cz2 + 1):
            d.set(x, hy, z, hopper("north"))
            d.set(x, hy - 1, z, SB)
            if landing == "campfire":
                d.set(x, hy + 1, z, campfire())
    n = cx2 - cx1 + 1
    for i, x in enumerate(range(cx1, cx2 + 1)):
        t = "single" if n % 2 and i == n - 1 else ("left" if i % 2 == 0 else "right")
        d.set(x, hy, cz1 - 1, chest("north", t))
        d.tag(x, hy, cz1 - 1, "farm_output")
        d.set(x, hy - 1, cz1 - 1, SB)
    for y in range(hy, ytop + 1):
        for x in range(cx1 - 1, cx2 + 2):
            for z in range(cz1 - 1, cz2 + 2):
                inside = cx1 <= x <= cx2 and cz1 <= z <= cz2
                if inside:
                    continue
                if y == hy and z == cz1 - 1 and cx1 <= x <= cx2:
                    continue                                    # the chests
                d.set(x, y, z, GLASS)
    for x in (cx1 - 1, cx2 + 1):
        for z in (cz1 - 1, cz2 + 1):
            for y in range(hy, ytop + 1):
                d.set(x, y, z, logb())


def tower(d, w, shaft, y_shaft, y_platform, door_x=10, top=5, lines=(), windows=None, ytop_glass=5, with_piers=True):
    """Ground part shared by the tower farms: base room around the glass landing, approach, yard, piers, shaft.
    shaft = (cx1, cz1, cx2, cz2) inner cells of the drop shaft below the platform."""
    BX1, BZ1, BX2, BZ2 = 4, 5, 15, 16
    if windows is None:
        windows = [(6, 3, BZ1), (7, 3, BZ1), (12, 3, BZ1), (13, 3, BZ1), (BX1, 3, 8), (BX1, 3, 12),
                   (BX2, 3, 8), (BX2, 3, 12), (7, 3, BZ2), (12, 3, BZ2)]
    base_room(d, BX1, BZ1, BX2, BZ2, top, door_x, windows=windows)
    cx1, cz1, cx2, cz2 = shaft
    collector(d, cx1, cz1, cx2, cz2, ytop_glass)
    column(d, cx1, cz1, cx2, cz2, ytop_glass + 1, y_platform - 1)
    approach(d, door_x, BZ1, list(lines))
    X1, Z1, X2, Z2 = outer(w)
    yard(d, w, [(2, 4), (X2 - 2, 4), (2, Z2 - 2), (X2 - 2, Z2 - 2), (2, 11), (X2 - 2, 11)])
    if with_piers:
        piers(d, w, y_platform - 1)
    d.set(14, 2, 15, "barrel[facing=up,open=false]")
    d.set(5, 2, 15, "crafting_table")
    return BX1, BZ1, BX2, BZ2


def strip_spawns(mob, y, cells, n_each=1):
    return [(mob, x, y, z, n_each) for (x, z) in cells]


# Test note: the test server has no player. A hostile mob with no player within 32 blocks counts up noActionTime
# and RandomStrollGoal stops after 100 ticks (Mob.checkDespawn never resets it), so in the test mobs stand still
# 5 s after spawning (in game the player AFK at the farm keeps them wandering). The tests therefore put most mobs
# where a wandering mob ends up - in the water channels / on the centre trapdoors - plus some on the spawning
# floors, and check transport, kill and collection.
CHANNEL = ((9, 5), (16, 11), (10, 18), (3, 12))           # channel cells (d = 6, 6, 6, 6) of a 2x2-hole platform
CENTRE = ((HX, HZ), (HX + 1, HZ), (HX, HZ + 1), (HX + 1, HZ + 1))


# ================================================================================================ creeper farm
@design("creeperfarm")
def creeperfarm(pack, rel, L):
    """Creeper tower (gunpowder). Two creeper-only spawning floors on top of a 25-block drop shaft.

    Spawning floor (y0 = 28 and 32): quadrants of 1-wide stone strips raised one block over the water channels,
    each strip roofed with closed top-half spruce trapdoors (1.8125 clear: creepers 1.7 fit, every 1.95-tall mob
    does not) and separated by stone-brick rows (no 3-wide room, so no spiders). Creepers walk off the strip ends
    into the channels; the water (8 sources per floor at the outer arm ends, flowing 7 cells) carries them into
    the 2x2 hole. They fall 25 blocks onto the hoppers (23 damage, 20 hp) in the glass landing of the base room;
    the hoppers feed two double chests. Dark inside (no light on the floors); roof slabbed and lit."""
    w = 2
    d = Design(pack, rel, size=(20, 40, 22), gy=1, paving="grass_block")
    shaft = (HX, HZ, HX + 1, HZ + 1)
    floors = (28, 32)
    tower(d, w, shaft, 3, floors[0],
          lines=["Creeper Farm", "gunpowder", "Bring: nothing", "(works at night)"])
    y = floors[0]
    for y0 in floors:
        y = water_floor(d, w, y0, "creeper")
    roof_box(d, w, y)
    # test: creepers stand on the strips where they would have spawned (both floors, all four quadrants)
    cells = [(4, 10), (6, 8), (14, 6), (16, 10), (3, 13), (7, 15), (13, 17), (15, 13)]
    spawns = (strip_spawns("minecraft:creeper", 30, cells) + strip_spawns("minecraft:creeper", 34, cells[::2])
              + [("minecraft:creeper", x, y0 + 1, z, 1) for y0 in floors for (x, z) in CHANNEL])
    d.farm_test(expect={"minecraft:gunpowder": 3}, spawns=spawns, ticks=6000)
    return d


# ================================================================================================ spider farm
@design("spiderfarm")
def spiderfarm(pack, rel, L):
    """Spider tower (string), no spawner. Three spider-only floors on top of a 4x4 drop shaft.

    Spawning floor (y0 = 25, 27, 29, 31): ONE block high - nothing but spiders (0.9 tall) fits, and the 8x8
    quadrants give them the 3x3 room they need. Quadrants and water channels are on the same level (a step lets a
    spider climb back out of a channel); standing signs along the channel edges hold the water back. Spiders walk
    into the 1-high channels and the water carries them into the 2x2 hole. Below the lowest floor the shaft
    widens to 4x4: a falling spider (1.4 wide) does not touch a wall, so it cannot climb (Spider: climbing =
    horizontal collision, which resets the fall). 22-block fall -> 19 damage (16 hp). A spider that does climb
    ends up under the platform ceiling and falls the full height later. 16 hoppers -> four chests."""
    w = 2
    d = Design(pack, rel, size=(20, 37, 22), gy=1, paving="grass_block")
    shaft = (HX - 1, HZ - 1, HX + 2, HZ + 2)
    floors = (25, 27, 29, 31)
    windows = [(5, 3, 5), (6, 3, 5), (13, 3, 5), (14, 3, 5), (4, 3, 12), (15, 3, 12), (7, 3, 16), (12, 3, 16)]
    tower(d, w, shaft, 3, floors[0], windows=windows,
          lines=["Spider Farm", "string", "Bring: nothing", "(works at night)"])
    y = floors[0]
    for y0 in floors:
        y = water_floor(d, w, y0, "spider")
    roof_box(d, w, y)
    cells = [(4, 5), (6, 7), (13, 5), (15, 7), (4, 16), (6, 18), (13, 16), (15, 18)]
    spawns = (strip_spawns("minecraft:spider", floors[0] + 1, cells) + strip_spawns("minecraft:spider", floors[2] + 1, cells[::2])
              + [("minecraft:spider", x, y0 + 1, z, 1) for y0 in floors for (x, z) in CHANNEL])
    d.farm_test(expect={"minecraft:string": 3}, spawns=spawns, ticks=6000)
    return d


# ================================================================================================ xp grinder
@design("xpgrinder")
def xpgrinder(pack, rel, L):
    """Mob grinder with an XP mode: one dark spawning floor, water channels, a drop into a player kill chamber.

    Spawning floor y0 = 29 (2-high quadrants, any 2-high hostile mob). Mobs fall 21.8 blocks onto the kill
    chamber floor (y = 8): four spruce trapdoors (half=bottom). Lever ON (as built) = AUTO: the trapdoors are open
    and the mobs fall on to the hoppers (26 blocks, dead) -> chests. Lever OFF = XP: the trapdoors close, mobs land
    on them with 19 damage (20-hp mobs on 1 hp, spiders die) and the player finishes them with one hit through the
    13/16-high slot in the chamber front (no mob fits through it). Flip back to AUTO to drop the loot left on
    the trapdoors into the hoppers.

    Redstone: lever (8,9,9) on the floor of block (8,8,9) -> powers the dust at (8,9,10) beside it; the dust runs
    around the top of the chamber walls (8,9,10..13) (9..11,9,13) (11,9,11..12). Dust strongly powers the block it
    sits on, so every chamber wall block (y = 8) is powered and opens / closes the trapdoor next to it
    (TrapDoorBlock: hasNeighborSignal). 9 dust, last one at power 7. Dust connections are set explicitly."""
    w = 2
    d = Design(pack, rel, size=(20, 37, 22), gy=1, paving="grass_block")
    shaft = (HX, HZ, HX + 1, HZ + 1)
    y0 = 29
    c = 8                                                    # kill chamber trapdoor layer
    BX1, BZ1, BX2, BZ2 = 4, 5, 15, 16
    windows = [(6, 3, BZ1), (7, 3, BZ1), (12, 3, BZ1), (13, 3, BZ1), (BX1, 3, 8), (BX2, 3, 8),
               (6, 9, BZ1), (7, 9, BZ1), (12, 9, BZ1), (13, 9, BZ1), (BX1, 9, 8), (BX1, 9, 12),
               (BX2, 9, 8), (BX2, 9, 12), (7, 9, BZ2), (12, 9, BZ2)]
    tower(d, w, shaft, 3, y0, top=10, windows=windows, ytop_glass=6,
          lines=["XP Grinder", "lever ON: auto", "lever OFF: XP", "Bring: a sword"])
    # upper storey floor (y=7) with a ladder hole, kill room y=8..10
    d.fill(BX1 + 1, 7, BZ1 + 1, BX2 - 1, 7, BZ2 - 1, "spruce_planks")
    for x in (BX1, BX2):
        for z in range(BZ1, BZ2 + 1):
            if d.get(x, 7, z).endswith("cobblestone"):
                d.set(x, 7, z, SB)
    for y in range(2, 8):
        d.set(14, y, 15, "ladder[facing=west,waterlogged=false]")
    d.set(14, 7, 15, "ladder[facing=west,waterlogged=false]")
    d.set(14, 8, 15, "ladder[facing=west,waterlogged=false]")
    d.set(14, 2, 15, AIR)                                   # (barrel spot of the shared base)
    d.set(14, 2, 15, "ladder[facing=west,waterlogged=false]")
    d.set(13, 2, 15, "barrel[facing=up,open=false]")
    # landing / chamber column: glass box y3..6 (collector), ring at y=7, chamber y=8, dust y=9, shaft above
    for x in range(HX - 1, HX + 3):
        for z in range(HZ - 1, HZ + 3):
            inside = HX <= x <= HX + 1 and HZ <= z <= HZ + 1
            d.set(x, 7, z, AIR if inside else SB)
            d.set(x, c, z, AIR if inside else SB)
            d.set(x, c + 1, z, AIR if inside else SB)
    # trapdoors hug the west / east walls when open (the 2x2 passage stays 1.625 wide)
    for z in (HZ, HZ + 1):
        d.set(HX, c, z, trapdoor("east", "bottom", True, True))
        d.set(HX + 1, c, z, trapdoor("west", "bottom", True, True))
    # front slot: air at y=8 in front of the chamber, solid above it
    d.set(HX, c, HZ - 1, AIR)
    d.set(HX + 1, c, HZ - 1, AIR)
    # dust ring on the chamber walls (y=9) and the lever
    def wire(x, z, power, **conn):
        sides = {k: conn.get(k, "none") for k in ("east", "north", "south", "west")}
        d.set(x, c + 1, z, "redstone_wire[" + ",".join(f"{k}={v}" for k, v in sides.items()) + f",power={power}]")
    wire(HX - 1, HZ - 1, 15, north="side", south="side")
    wire(HX - 1, HZ, 14, north="side", south="side")
    wire(HX - 1, HZ + 1, 13, north="side", south="side")
    wire(HX - 1, HZ + 2, 12, north="side", east="side")
    wire(HX, HZ + 2, 11, east="side", west="side")
    wire(HX + 1, HZ + 2, 10, east="side", west="side")
    wire(HX + 2, HZ + 2, 9, west="side", north="side")
    wire(HX + 2, HZ + 1, 8, north="side", south="side")
    wire(HX + 2, HZ, 7, north="side", south="side")
    d.set(HX - 1, c, HZ - 2, SB)
    d.set(HX - 1, c + 1, HZ - 2, "lever[face=floor,facing=north,powered=true]")
    d.sign(HX, c + 1, BZ1 + 1, "south", ["Lever ON: auto", "Lever OFF: XP", "hit their feet", "through the slot"],
           "spruce")
    # cover over the chamber ring (y=10) and the shaft column up to the platform
    column(d, HX, HZ, HX + 1, HZ + 1, c + 2, y0 - 1)
    # ground-floor lights hang from the plank floor
    for x in (6, 13):
        lantern(d, x, 6, 7)
        lantern(d, x, 6, 14)
    # the spawning floor
    yc = water_floor(d, w, y0, "xp")
    band(d, w, y0)
    roof_box(d, w, yc)
    cells = [(3, 5), (6, 8), (13, 5), (16, 8), (3, 15), (6, 18), (13, 15), (16, 18)]
    spawns = (strip_spawns("minecraft:zombie", y0 + 2, cells[:4]) + strip_spawns("minecraft:skeleton", y0 + 2, cells[4:])
              + strip_spawns("minecraft:zombie", y0 + 2, cells[4:]) + strip_spawns("minecraft:skeleton", y0 + 2, cells[:4]))
    spawns += [(m, x, y0 + 1, z, 2) for m in ("minecraft:zombie", "minecraft:skeleton") for (x, z) in CHANNEL]
    d.farm_test(expect={"minecraft:rotten_flesh": 1, "minecraft:bone": 1}, spawns=spawns, ticks=6000)
    return d


# ================================================================================================ gold farm
@design("goldfarm")
def goldfarm(pack, rel, L):
    """Nether gold farm (zombified piglins): build it in a NETHER WASTES or CRIMSON FOREST biome.

    Three cross-shaped floors (y0 = 28, 31, 34) of MAGMA BLOCKS, 2 high: on magma only fire-immune mobs can spawn
    (MagmaBlock: isValidSpawn = fireImmune) -> zombified piglins (and the odd magma cube); 2 high keeps ghasts and
    endermen out. No water (it evaporates in the Nether): the four 2-wide arms meet only in the 2x2 centre, which
    holds open trapdoors over the hole - a piglin strolling from arm to arm paths onto the trapdoors (PathType
    TRAPDOOR is walkable to the path finder) and drops 25 blocks onto the hoppers (23 damage, 20 hp). Gold
    nuggets and rotten flesh go to the chests; gold ingots only drop on player kills. Never hit a piglin here."""
    w = 2
    d = Design(pack, rel, size=(20, 40, 22), gy=1, paving="netherrack")
    shaft = (HX, HZ, HX + 1, HZ + 1)
    floors = (28, 31, 34)
    tower(d, w, shaft, 3, floors[0],
          lines=["Gold Farm", "build in Nether", "Wastes. Bring:", "nothing"], with_piers=False)
    # magma arms, trapdoor centre (each trapdoor against the outer edge of its cell)
    for y0 in floors:
        def arm(x, y, z, dist):
            d.set(x, y, z, AIR)

        def centre(x, y, z, y0=y0):
            if y == y0 + 1:
                face = "east" if x == HX else "west"
                d.set(x, y, z, trapdoor(face, "bottom", True, False, "crimson"))
            else:
                d.set(x, y, z, AIR)
        cross_floor(d, w, y0, 3, "magma_block", arm, centre, wall="nether_bricks")
    cross_cap(d, w, floors[-1] + 3)
    for y0 in floors:                                    # the hole through every floor
        d.clear(HX, y0, HZ, HX + 1, y0, HZ + 1)
    cells = [(9, 4), (10, 7), (2, 11), (5, 12), (14, 11), (17, 12), (9, 16), (10, 19)]
    spawns = ([("minecraft:zombified_piglin", x, y0 + 1, z, 1) for y0 in floors for (x, z) in cells[::2]]
              + [("minecraft:zombified_piglin", x, y0 + 1, z, 1) for y0 in floors for (x, z) in CENTRE])
    d.farm_test(expect={"minecraft:gold_nugget": 2, "minecraft:rotten_flesh": 1}, spawns=spawns, ticks=6000)
    return d


# ================================================================================================ drowned farm
@design("drownedfarm")
def drownedfarm(pack, rel, L):
    """Drowned farm: build it in a RIVER biome (drowned spawn in dark river water at any height; in oceans only
    below y = 58). Two cross-shaped tanks (floor y = 28 and 32) of still water, two blocks deep (a drowned spawns in
    water with water below it) and roofed (dark). With no target a drowned walks on the tank floor; the arms meet
    only in the 2x2 centre: two open trapdoors stacked in each centre cell (both water levels) keep the centre
    DRY (flowing water cannot enter a trapdoor) - a drowned that walks onto them is out of the water at once and
    drops 25 blocks onto the hoppers (with water over the centre it would only sink slowly and walk on across).
    Rotten flesh (and any nautilus shell a drowned holds) to the chests; copper ingots and tridents only drop on
    player kills. All water blocks are sources placed by the blueprint (2 layers in the 4 arms)."""
    w = 2
    d = Design(pack, rel, size=(20, 39, 22), gy=1, paving="grass_block")
    shaft = (HX, HZ, HX + 1, HZ + 1)
    floors = (28, 32)
    tower(d, w, shaft, 3, floors[0],
          lines=["Drowned Farm", "build in a", "river biome", "Bring: nothing"], with_piers=False)
    for y0 in floors:
        def arm(x, y, z, dist, y0=y0):
            d.set(x, y, z, WATER if y <= y0 + 2 else AIR)

        def centre(x, y, z, y0=y0):
            if y in (y0 + 1, y0 + 2):
                face = "east" if x == HX else "west"
                d.set(x, y, z, trapdoor(face, "bottom", True, False))
            else:
                d.set(x, y, z, AIR)
        cross_floor(d, w, y0, 4, "stone", arm, centre, wall=CB)
    cross_cap(d, w, floors[-1] + 4)
    for y0 in floors:
        d.clear(HX, y0, HZ, HX + 1, y0, HZ + 1)
    cells = [(9, 4), (10, 7), (2, 11), (5, 12), (14, 11), (17, 12), (9, 16), (10, 19)]
    spawns = ([("minecraft:drowned", x, y0 + 1, z, 1) for y0 in floors for (x, z) in cells[::2]]
              + [("minecraft:drowned", x, y0 + 1, z, 2) for y0 in floors for (x, z) in CENTRE])
    d.farm_test(expect={"minecraft:rotten_flesh": 4}, spawns=spawns, ticks=6000)
    return d


# ================================================================================================ slime farm
@design("slimefarm")
def slimefarm(pack, rel, L):
    """Slime farm: the spawning floors must be in a SLIME CHUNK and below y = 40 (dig a pit; centre the cross on
    the slime chunk, F3+G shows chunk borders). Two cross-shaped floors (y0 = 8, 12) with 3-wide, 3-high arms
    (a big slime is 2.04 wide and tall) and a 3x3 hole in the middle. The floors are LIT (glowstone in the walls):
    slimes in slime chunks spawn at any light level, every other mob needs darkness. Slimes hop in random
    directions, fall down the 3x3 shaft onto lit campfires over hoppers, split, and all sizes die to campfire
    damage there. Small slimes drop the slimeballs, which the hoppers pull through the campfires into the chests."""
    w = 3
    d = Design(pack, rel, size=(21, 19, 23), gy=1, paving="grass_block")
    floors = (8, 12)
    BX1, BZ1, BX2, BZ2 = 4, 5, 16, 17
    door_x = 10
    windows = [(6, 3, BZ1), (7, 3, BZ1), (13, 3, BZ1), (14, 3, BZ1), (BX1, 3, 9), (BX2, 3, 9), (BX1, 3, 13),
               (BX2, 3, 13)]
    base_room(d, BX1, BZ1, BX2, BZ2, 6, door_x, windows=windows, roof="flat", beams=(6, 14), lamps_z=(8, 15))
    collector(d, HX, HZ, HX + 2, HZ + 2, 6, landing="campfire")
    column(d, HX, HZ, HX + 2, HZ + 2, 7, floors[0] - 1)
    approach(d, door_x, BZ1, ["Slime Farm", "slime chunk,", "floors below", "Y=40!"])
    d.set(15, 2, 16, "barrel[facing=up,open=false]")
    d.set(5, 2, 16, "crafting_table")
    X1, Z1, X2, Z2 = outer(w)
    yard(d, w, [(2, 4), (X2 - 2, 4), (2, Z2 - 2), (X2 - 2, Z2 - 2)])
    for y0 in floors:
        def arm(x, y, z, dist):
            d.set(x, y, z, AIR)

        def centre(x, y, z):
            d.set(x, y, z, AIR)
        cross_floor(d, w, y0, 4, "stone", arm, centre, wall=CB, light="glowstone")
    cross_cap(d, w, floors[-1] + 4)
    for y0 in floors:
        d.clear(HX, y0, HZ, HX + 2, y0, HZ + 2)
    cells = [(10, 4), (10, 7), (2, 12), (6, 12), (14, 12), (18, 12), (10, 17), (10, 20)]
    spawns = [("minecraft:slime", x, y0 + 1, z, 1) for y0 in floors for (x, z) in cells[::2]]
    d.farm_test(expect={"minecraft:slime_ball": 2}, spawns=spawns, ticks=6000)
    return d
