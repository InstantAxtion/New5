"""
Farmworks – a decorations-only style pack of automatic mob and food farms.

Every farm uses mechanics that work without timing-sensitive redstone (no observers / zero-tick tricks),
so they function as soon as the colony builder places them:

  decorations/mobfarms/mobtower      dark spawning platform 25 blocks up, water channels push mobs into a
                                     drop shaft, the fall kills them, hoppers collect the drops into chests
                                     (stay within 24-128 blocks)
  decorations/mobfarms/ironfarm      villager pods with beds above a golem spawning floor, water pushes
                                     golems into a sign-held lava blade, hoppers collect iron & poppies
                                     (bring 3 villagers and a name-tagged zombie)
  decorations/mobfarms/cactusfarm    three stacked tiers of cactus on fence-supported sand; cactus breaks
                                     itself against fence posts, drops fall to a water stream -> hoppers
  decorations/foodfarms/eggfarm      chicken coop floored with hoppers: eggs and feathers go straight
                                     into chests (throw in a few eggs to start the flock)
  decorations/foodfarms/autokitchen  six smokers fed by hoppers: raw food in the top chest, fuel in the side
                                     chest, cooked food comes out in the bottom chests
  decorations/foodfarms/bonemeal     composter line: crops / seeds in, bone meal out
  decorations/foodfarms/smeltery     four-furnace super-smelter for ores, sand and kelp

usage: python farms.py <out-pack-dir>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import styleinfra  # noqa: E402
from styleinfra import P, SOLID, FENCE, LANT, HLANT  # noqa: E402

PACK = "Farmworks"
styleinfra.M[PACK] = dict(post="stripped_spruce_log[axis=y]", beam_x="stripped_spruce_log[axis=x]",
                          beam_z="stripped_spruce_log[axis=z]", plank="spruce_planks", stairs="stone_brick",
                          slab="stone_brick_slab", fence="spruce_fence", gate="spruce_fence_gate", stone="stone_bricks",
                          stone2="cobblestone", pave="stone_bricks", pave2="smooth_stone", curb="stone_bricks",
                          wall="stone_bricks", light="lantern", roof="spruce", trim="stripped_spruce_log[axis=y]",
                          water_edge="stone_bricks")
WALL = "stone_bricks"
GLASS = "glass"


def hopper(facing):
    return f"hopper[enabled=true,facing={facing}]"


def chest(facing="north"):
    return f"chest[facing={facing},type=single,waterlogged=false]"


# ============================================================================ mob tower
def mobtower():
    S = 21                                  # platform 21x21, 2x2 drop shaft in the middle
    TOP = 26                                # spawning floor height
    p = P(PACK, (S, TOP + 5, S), "mobtower", "decorations/mobfarms")
    p.found()
    C = S // 2                              # 10 -> shaft at 9..10
    sh = (C - 1, C)
    # ground floor: kill / collection room around the shaft bottom
    for x in range(S):
        for z in range(S):
            p.S(x, 1, z, WALL)
    for x in range(C - 4, C + 4):
        for z in range(C - 4, C + 4):
            e = x in (C - 4, C + 3) or z in (C - 4, C + 3)
            for y in range(2, 5):
                p.S(x, y, z, WALL if e else "air")
            p.S(x, 5, z, WALL)
    for x in sh:                            # shaft bottom: hoppers into chests, slab gap to hit mobs
        for z in sh:
            p.S(x, 1, z, hopper("north" if z == sh[0] else "south"))
    for x in sh:
        p.S(x, 1, sh[0] - 1, chest("south"))
        p.S(x, 1, sh[1] + 1, chest("north"))
        p.S(x, 1, sh[0] - 2, WALL)
    p.fill(C, 2, C - 4, C, 3, C - 4, "air")                                   # door into the collection room
    p.S(C, 4, C - 3, HLANT)
    # shaft walls up to the platform (dark inside, so no lights)
    for y in range(2, TOP):
        for x in range(C - 2, C + 2):
            for z in range(C - 2, C + 2):
                if x in sh and z in sh:
                    p.S(x, y, z, "air")
                else:
                    p.S(x, y, z, WALL)
    for x in sh:                            # chests need air above to open
        p.S(x, 2, sh[0] - 1, "air")
        p.S(x, 2, sh[1] + 1, "air")
    # spawning platform: plus-shaped water channels to the shaft, enclosed and roofed (dark)
    for x in range(S):
        for z in range(S):
            p.S(x, TOP, z, WALL)
            e = x in (0, S - 1) or z in (0, S - 1)
            for y in range(TOP + 1, TOP + 3):
                p.S(x, y, z, WALL if e else "air")
            p.S(x, TOP + 3, z, WALL)
    for x in sh:
        for z in sh:
            p.S(x, TOP, z, "air")
    for k in range(1, 9):                   # four channels, sources at the outer ends
        for a in sh:
            for (x, z) in ((a, sh[0] - k), (a, sh[1] + k), (sh[0] - k, a), (sh[1] + k, a)):
                p.S(x, TOP, z, WALL)
                p.S(x, TOP + 1, z, "water[level=0]" if k == 8 else "air")
    # access ladder outside the shaft to the roof (for the player to check on it)
    for y in range(2, TOP + 4):
        p.S(C + 2, y, C - 3, "ladder[facing=north,waterlogged=false]")
    p.lamp(1, 2, 1)
    p.lamp(S - 2, 2, S - 2)
    return p.deco((C, 1, 0))


# ============================================================================ iron farm
def ironfarm():
    p = P(PACK, (13, 18, 13), "ironfarm", "decorations/mobfarms")
    p.found()
    C, F = 6, 3                               # spawning floor at y3, collection room below
    for x in range(13):
        for z in range(13):
            p.S(x, 1, z, WALL)
            e = x in (0, 12) or z in (0, 12)
            p.S(x, 2, z, WALL if e else "air")
            p.S(x, F, z, WALL)
    p.S(C, F, C, hopper("down"))              # drops fall into the floor hopper ...
    p.S(C, 2, C, chest("north"))              # ... and into the chest in the room below
    p.fill(C, 2, 0, C, 2, 0, "air")           # door into the collection room
    p.S(C, 5, C, "oak_sign[rotation=0,waterlogged=false]")   # sign holds the lava at golem head height
    p.S(C, 6, C, "lava[level=0]")
    for x, z in ((C - 1, C), (C + 1, C), (C, C - 1), (C, C + 1)):
        p.S(x, 6, z, GLASS)
    p.S(C, 7, C, GLASS)
    for x in range(1, 12):                    # glass walls, 3 high
        for z in range(1, 12):
            if x in (1, 11) or z in (1, 11):
                for y in range(F + 1, F + 4):
                    p.S(x, y, z, GLASS)
    for (x, z) in ((C, 2), (C, 10), (2, C), (10, C)):   # water pushes golems to the centre
        p.S(x, F + 1, z, "water[level=0]")
    V = F + 5                                 # villager pods on a deck above
    for x in range(1, 12):
        for z in range(1, 12):
            if x in (1, 11) or z in (1, 11):
                p.S(x, V, z, WALL)
    for x in range(2, 11):
        for z in (2, 3, 4, 8, 9, 10):
            p.S(x, V, z, WALL)
    for x in (3, 6, 9):
        p.S(x, V + 1, 3, "white_bed[facing=north,occupied=false,part=head]")
        p.S(x, V + 1, 4, "white_bed[facing=north,occupied=false,part=foot]")
        for y in (V + 1, V + 2):
            p.S(x - 1, y, 4, GLASS)
            p.S(x + 1, y, 4, GLASS)
            p.S(x, y, 5, GLASS)
        p.S(x, V + 3, 4, GLASS)
    for y in (V + 1, V + 2):                  # zombie cell (bring a name-tagged zombie)
        for x, z in ((5, 9), (7, 9), (6, 8), (6, 10)):
            p.S(x, y, z, GLASS)
    p.S(6, V + 3, 9, GLASS)
    for y in range(2, V + 2):
        p.S(12, y, 6, "ladder[facing=east,waterlogged=false]")
    return p.deco((C, 1, 0))


# ============================================================================ cactus farm
def cactusfarm():
    p = P(PACK, (11, 17, 11), "cactusfarm", "decorations/mobfarms")
    p.found()
    for x in range(11):
        for z in range(11):
            p.S(x, 1, z, WALL)
    # water stream on the floor towards the collection hopper
    for x in range(1, 10):
        for z in range(1, 10):
            p.S(x, 1, z, WALL)
            p.S(x, 2, z, "air")
    for x in range(1, 10):                    # hopper row under the end of the stream, funnelled to the chest
        p.S(x, 1, 8, hopper("east" if x < 5 else "west" if x > 5 else "south"))
    p.S(5, 1, 9, chest("north"))
    for z in range(1, 10):                    # sources along the back edge, flowing to the front hopper
        p.S(1, 2, z, "air")
    for x in range(1, 10):
        p.S(x, 2, 1, "water[level=0]")
    for x in range(1, 10):                    # glass walls keep water and items in
        for y in (2, 3):
            p.S(x, y, 0, GLASS)
            p.S(x, y, 10, GLASS)
            p.S(x, y, 9, GLASS)
    for z in range(0, 11):
        for y in (2, 3):
            p.S(0, y, z, GLASS)
            p.S(10, y, z, GLASS)
    # three tiers of cactus: fence post -> sand -> cactus, breaker fence next to the second block
    for t in range(3):
        y0 = 4 + 4 * t
        for x in range(2, 9, 2):
            for z in range(2, 9, 2):
                if (x + z + t) % 4:
                    continue
                p.S(x, y0, z, "spruce_fence" + FENCE)
                p.S(x, y0 + 1, z, "sand")
                p.S(x, y0 + 2, z, "cactus[age=0]")
                p.S(x + 1, y0 + 3, z, "spruce_fence" + FENCE)
    for y in range(2, 16):
        p.S(10, y, 5, "ladder[facing=east,waterlogged=false]")
    return p.deco((5, 1, 0))


# ============================================================================ food
def eggfarm():
    p = P(PACK, (9, 7, 9), "eggfarm", "decorations/foodfarms")
    p.found()
    for x in range(9):
        for z in range(9):
            p.S(x, 1, z, WALL)
    for x in range(2, 7):                     # hopper floor: rows feed into the chest line at the front
        for z in range(2, 7):
            p.S(x, 2, z, hopper("north"))
    for x in range(2, 7):
        p.S(x, 2, 1, chest("south"))
    for x in range(1, 8):
        for z in range(1, 8):
            e = x in (1, 7) or z in (1, 7)
            if e and z != 1:
                p.S(x, 2, z, WALL)
                p.S(x, 3, z, GLASS)
                p.S(x, 4, z, GLASS)
            if not e:
                p.S(x, 3, z, "air")
            p.S(x, 5, z, "spruce_slab[type=bottom,waterlogged=false]")
    for x in range(2, 7):
        p.S(x, 3, 1, GLASS)
        p.S(x, 4, 1, GLASS)
    p.S(4, 4, 4, HLANT)
    return p.deco((4, 1, 0))


def autokitchen(name="autokitchen", block="smoker", n=6):
    W = n + 4
    p = P(PACK, (W, 9, 7), name, "decorations/foodfarms")
    p.found()
    for x in range(W):
        for z in range(7):
            p.S(x, 1, z, WALL)
    x0 = 2
    for i in range(n):
        x = x0 + i
        p.S(x, 3, 3, f"{block}[facing=north,lit=false]")
        p.S(x, 4, 3, hopper("down"))                             # input from above
        p.S(x, 5, 3, hopper("east" if i < n - 1 else "down"))    # input line
        p.S(x, 3, 4, hopper("north"))                            # fuel from behind
        p.S(x, 4, 4, hopper("west" if i > 0 else "north"))       # fuel line
    # output: hoppers below ovens chain into chests in front
    for i in range(n):
        x = x0 + i
        p.S(x, 2, 3, hopper("north"))
        p.S(x, 2, 2, chest("south"))
    p.S(x0, 6, 3, chest("north"))                                # raw food in
    p.S(x0 + n - 1, 5, 4, chest("north"))                        # fuel in
    p.S(x0 - 1, 3, 3, LANT)
    for x in range(W):
        for z in (0, 6):
            p.S(x, 2, z, "spruce_fence" + FENCE)
    return p.deco((1, 1, 0))


def bonemeal():
    p = P(PACK, (9, 8, 5), "bonemeal", "decorations/foodfarms")
    p.found()
    for x in range(9):
        for z in range(5):
            p.S(x, 1, z, WALL)
    for x in range(2, 7):
        p.S(x, 5, 2, hopper("east" if x < 6 else "down"))   # feed chain
        p.S(x, 4, 2, hopper("down"))                        # pulls from the chain, fills the composter
        p.S(x, 3, 2, "composter[level=0]")
        p.S(x, 2, 2, hopper("north"))                       # pulls bone meal out
        p.S(x, 2, 1, chest("south"))
    p.S(2, 6, 2, chest("north"))
    return p.deco((4, 1, 0))


def build_all(root: Path):
    out = {"decorations/mobfarms/mobtower": mobtower(), "decorations/mobfarms/ironfarm": ironfarm(),
           "decorations/mobfarms/cactusfarm": cactusfarm(), "decorations/foodfarms/eggfarm": eggfarm(),
           "decorations/foodfarms/autokitchen": autokitchen(),
           "decorations/foodfarms/smeltery": autokitchen("smeltery", "furnace", 4),
           "decorations/foodfarms/bonemeal": bonemeal()}
    for rel, bp in out.items():
        f = root / f"{rel}.blueprint"
        f.parent.mkdir(parents=True, exist_ok=True)
        bp.name = f.name
        bp.save(f)
    (root / "pack.json").write_text(json.dumps({
        "icon": "farmworks.png", "name": PACK, "authors": ["New5"],
        "desc": "Decorations only: automatic mob farms (mob tower, iron farm, cactus farm) and food farms "
                "(egg farm, auto-smoker kitchen, bone-meal composters, super-smelter). No timing-sensitive redstone.",
        "mods": ["structurize", "minecolonies"], "version": "1", "pack-format": "1"}, indent=2) + "\n")
    print(f"{PACK}: {len(out)} farms")


if __name__ == "__main__":
    build_all(Path(sys.argv[1]))
