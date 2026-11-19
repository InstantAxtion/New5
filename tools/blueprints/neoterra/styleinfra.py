"""
Walls, infrastructure and parks designed per pack (no shared geometry with Neoterra or each other).

  Cascadia    log palisades on river-rock footings with pointed tops and a timber walkway, log bastions,
              timber watchtowers, gravel/cobble lanes with log curbs, rails on spruce sleepers, mossy
              canals, red covered bridges on stone piers, timber-shored tunnels, plank boardwalks on log
              piles, timber switchback climbs, forest-clearing parks with log benches and fire pits.
  Hearthwood  brick ramparts with stone coping and lantern pillars, brick turrets, brick-paved streets
              with stone curbs and lamp posts, tram stops, brick canals and arch bridges, tiled subway,
              oak promenades, brick stair towers, garden squares with flower beds, gazebo and fountain.

usage: python styleinfra.py <out-pack-dir> <Hearthwood|Cascadia>
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

from nbtlib import tag as NBT

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from blueprint import Blueprint  # noqa: E402
from common import connect_panes  # noqa: E402

SOLID = "structurize:blocksolidsubstitution"

M = {
    "Cascadia": dict(post="dark_oak_log[axis=y]", beam_x="dark_oak_log[axis=x]", beam_z="dark_oak_log[axis=z]",
                     plank="spruce_planks", stairs="spruce", slab="spruce_slab", fence="spruce_fence",
                     gate="spruce_fence_gate", stone="cobblestone", stone2="mossy_cobblestone", pave="coarse_dirt",
                     pave2="gravel", curb="stripped_spruce_log", wall="red_terracotta", light="lantern",
                     roof="dark_oak", trim="stripped_dark_oak_log[axis=y]", water_edge="mossy_cobblestone"),
    "Hearthwood": dict(post="stripped_dark_oak_log[axis=y]", beam_x="stripped_dark_oak_log[axis=x]",
                       beam_z="stripped_dark_oak_log[axis=z]", plank="oak_planks", stairs="dark_oak", slab="oak_slab",
                       fence="dark_oak_fence", gate="dark_oak_fence_gate", stone="bricks", stone2="stone_bricks",
                       pave="bricks", pave2="stone_bricks", curb="stone_bricks", wall="white_terracotta",
                       light="lantern", roof="dark_oak", trim="dark_oak_planks", water_edge="stone_bricks"),
}
FENCE = "[east=false,north=false,south=false,waterlogged=false,west=false]"
LANT = "lantern[hanging=false,waterlogged=false]"
HLANT = "lantern[hanging=true,waterlogged=false]"


class P:
    """A piece being built."""

    def __init__(self, style, size, name, cat):
        self.s, self.m = style, M[style]
        self.bp = Blueprint(*size, f"{name}.blueprint")
        self.name, self.cat = name, cat
        self.tags = {}

    def S(self, x, y, z, s):
        if self.bp.inside(x, y, z):
            self.bp.set(x, y, z, s if ":" in s else "minecraft:" + s)

    def fill(self, x1, y1, z1, x2, y2, z2, s):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for y in range(min(y1, y2), max(y1, y2) + 1):
                for z in range(min(z1, z2), max(z1, z2) + 1):
                    self.S(x, y, z, s)

    def found(self, y=0):
        self.fill(0, y, 0, self.bp.sx - 1, y, self.bp.sz - 1, SOLID)

    def st(self, facing, half="bottom", mat=None):
        return f"{mat or self.m['stairs']}_stairs[facing={facing},half={half},shape=straight,waterlogged=false]"

    def lamp(self, x, y, z, h=3):
        self.fill(x, y, z, x, y + h - 1, z, self.m["post"] if self.s == "Cascadia" else "dark_oak_fence" + FENCE)
        self.S(x, y + h, z, LANT)

    def done(self, offset):
        connect_panes(self.bp)
        self.bp.primary_offset = offset
        self.bp.architects = [self.s]
        return self.bp

    def deco(self, anchor, ground_y=1):
        """Decoration controller with tags (parks, watchtowers, rail stop, pier)."""
        connect_panes(self.bp)
        ax, ay, az = anchor
        tags = {(0, ground_y, 0): ["groundlevel"]}
        for p, n in self.tags.items():
            tags.setdefault(p, []).extend(n)

        def pos(x, y, z):
            return NBT.Compound({"x": NBT.Int(x), "y": NBT.Int(y), "z": NBT.Int(z)})
        path = f"{self.cat}/{self.name}.blueprint"
        te = NBT.Compound({
            "id": NBT.String("minecolonies:decorationcontroller"), "path": NBT.String(path),
            "name": NBT.String(self.name), "pack": NBT.String(self.s), "Item": NBT.String(""),
            "mirror": NBT.Byte(0), "rotation": NBT.Int(0),
            "blueprintDataProvider": NBT.Compound({
                "corner1": pos(-ax, -ay, -az),
                "corner2": pos(self.bp.sx - 1 - ax, self.bp.sy - 1 - ay, self.bp.sz - 1 - az),
                "path": NBT.String(path), "schematicName": NBT.String(self.name), "pack": NBT.String(self.s),
                "posTagMap": NBT.List[NBT.Compound]([
                    NBT.Compound({"tagPos": pos(x - ax, y - ay, z - az),
                                  "tagNameList": NBT.List[NBT.Compound]([NBT.Compound({"tagName": NBT.String(t)}) for t in n])})
                    for (x, y, z), n in sorted(tags.items())]),
            }),
        })
        self.bp.set(ax, ay, az, "minecolonies:decorationcontroller[facing=north,mirror=false,waterlogged=false]", te)
        self.bp.primary_offset = anchor
        self.bp.architects = [self.s]
        return self.bp

    def seat(self, x, y, z, back):
        self.S(x, y, z, self.st(back))
        self.tags.setdefault((x, y, z), []).append("sit_out")


# ============================================================================ walls
WH = 7          # walkway height


def wall_run(p, x1, x2, z0=0):
    """A wall segment along x, depth 4 (z0..z0+3), walkway at WH."""
    m = p.m
    for x in range(x1, x2 + 1):
        if p.s == "Cascadia":                           # palisade: stone footing, log stakes, pointed tops
            p.fill(x, 1, z0, x, 1, z0 + 1, m["stone"] if x % 3 else m["stone2"])
            p.fill(x, 2, z0, x, WH + 1, z0, m["post"])
            p.S(x, WH + 2, z0, "dark_oak_fence" + FENCE if x % 2 else m["post"])
            p.S(x, WH + 3, z0, "air" if x % 2 else "lightning_rod[facing=up,powered=false,waterlogged=false]")
            for z in (z0 + 1, z0 + 2):                  # walkway on log beams
                p.S(x, WH, z, m["plank"])
            p.S(x, WH - 1, z0 + 2, m["beam_x"])
            if x % 4 == 0:
                p.fill(x, 1, z0 + 2, x, WH - 2, z0 + 2, m["post"])
            p.S(x, WH + 1, z0 + 3, m["fence"] + FENCE)
            p.S(x, WH, z0 + 3, m["plank"])
            p.S(x, 1, z0 + 3, m["pave"])
        else:                                           # brick rampart with coping, crenels, lantern pillars
            for z in range(z0, z0 + 3):
                p.fill(x, 1, z, x, WH - 1, z, m["stone"] if (x + z) % 7 else m["stone2"])
                p.S(x, WH, z, m["stone2"])
            p.S(x, WH + 1, z0, m["stone"] if x % 2 == 0 else "air")
            p.S(x, WH + 2, z0, "stone_brick_slab[type=bottom,waterlogged=false]" if x % 2 == 0 else "air")
            p.S(x, WH + 1, z0 + 2, m["fence"] + FENCE)
            if x % 6 == 3:
                p.fill(x, 1, z0 + 3, x, WH + 1, z0 + 3, m["stone2"])
                p.S(x, WH + 2, z0 + 3, LANT)
            else:
                p.S(x, 1, z0 + 3, m["pave"])


def build_walls(style):
    out = {}
    p = P(style, (8, WH + 4, 4), "wallstraight", "walls")
    p.found()
    wall_run(p, 0, 7)
    out["walls/wallstraight"] = p.done((4, 1, 1))

    p = P(style, (14, WH + 7, 4), "wallgate", "walls")
    p.found()
    wall_run(p, 0, 13)
    m = p.m
    for x in range(5, 9):
        for z in range(0, 4):
            p.fill(x, 1, z, x, WH - 1, z, "air")
            p.S(x, 1, z, m["pave2"])
        p.S(x, 2, 1, m["gate"] + "[facing=south,in_wall=false,open=false,powered=false]")
    for x in (4, 9):
        p.fill(x, 1, 0, x, WH + 2, 0, m["post"] if style == "Cascadia" else m["stone2"])
    for x in range(3, 11):                              # gate roof
        k = min(x - 3, 10 - x)
        p.S(x, WH + 1 + k, 0, p.st("east" if x < 7 else "west") if x not in (6, 7) else m["trim"].split("[")[0] + ("" if "[" not in m["trim"] else "[axis=x]"))
    out["walls/wallgate"] = p.done((7, 1, 1))

    p = P(style, (8, WH + 4, 12), "wallstairs", "walls")
    p.found()
    wall_run(p, 0, 7)
    for i in range(WH - 1):
        z = 10 - i
        for x in (2, 3, 4):
            p.fill(x, 1, z, x, 1 + i, z, m["stone"] if style == "Hearthwood" else m["plank"])
            p.S(x, 2 + i, z, p.st("north"))
        p.S(5, 3 + i, z, m["fence"] + FENCE)
    for x in (2, 3, 4):
        p.fill(x, 1, 4, x, WH, 4, m["stone"] if style == "Hearthwood" else m["plank"])
        p.S(x, WH + 1, 3, "air")
    out["walls/wallstairs"] = p.done((4, 1, 1))

    for kind in ("inside", "outside"):
        p = P(style, (8, WH + 6, 8), f"wall{kind}corner", "walls")
        p.found()
        wall_run(p, 3, 7, z0=0 if kind == "outside" else 4)
        # bastion / turret
        cx, cz = (1, 1) if kind == "outside" else (5, 5)
        cx, cz = (2, 2) if kind == "outside" else (5, 1)
        for x in range(cx - 2, cx + 3):
            for z in range(cz - 2, cz + 3):
                if not p.bp.inside(x, 1, z):
                    continue
                e = x in (cx - 2, cx + 2) or z in (cz - 2, cz + 2)
                if style == "Cascadia":
                    if e:
                        p.fill(x, 1, z, x, WH + 2, z, m["post"])
                    p.S(x, WH + 1, z, m["plank"])
                else:
                    p.fill(x, 1, z, x, WH + 1, z, m["stone"] if e else "air")
                    p.S(x, WH + 1, z, m["stone2"])
                    if e:
                        p.S(x, WH + 2, z, m["stone"] if (x + z) % 2 else "air")
        p.S(cx, WH + 2, cz, LANT)
        out[f"walls/wall{kind}corner"] = p.done((4, 1, 4))

    for L in (1, 2, 3):
        # Cascadia: tall fire-lookout on timber legs; Hearthwood: squat stone tower
        H = WH + 4 + 3 * L if style != "Cascadia" else WH + 9 + 5 * L
        p = P(style, (9, H + 8, 9), f"watchtower{L}", "walls")
        p.found()
        wall_run(p, 0, 8, z0=3)
        for x, z in ((1, 1), (7, 1), (1, 7), (7, 7)):
            p.fill(x, 1, z, x, H, z, m["post"] if style == "Cascadia" else m["stone2"])
        if style == "Hearthwood":
            for x in range(1, 8):
                for z in range(1, 8):
                    if x in (1, 7) or z in (1, 7):
                        p.fill(x, 1, z, x, H, z, m["stone"] if (x + z) % 5 else m["stone2"])
            p.fill(4, 2, 1, 4, 3, 1, "air")
        for x in range(0, 9):
            for z in range(0, 9):
                p.S(x, H + 1, z, m["plank"] if style == "Cascadia" else m["stone2"])
                if x in (0, 8) or z in (0, 8):
                    p.S(x, H + 2, z, m["fence"] + FENCE if style == "Cascadia" else (m["stone"] if (x + z) % 2 else "air"))
        for y in range(2, H + 2):
            p.S(2, y, 2, "ladder[facing=south,waterlogged=false]")
            p.S(2, y, 1, m["post"] if style == "Cascadia" else m["stone"])
        for i in range(3):                              # pyramid roof on posts
            for x in range(1 + i, 8 - i):
                for z in range(1 + i, 8 - i):
                    if x in (1 + i, 7 - i) or z in (1 + i, 7 - i):
                        p.S(x, H + 5 + i, z, m["roof"] + "_planks")
        for x, z in ((1, 1), (7, 1), (1, 7), (7, 7)):
            p.fill(x, H + 2, z, x, H + 4, z, m["post"])
        p.S(4, H + 4, 4, HLANT)
        out[f"walls/watchtower{L}"] = p.deco((4, 1, 0))
    return out


# ============================================================================ roads / rails
def road_piece(style, name, sx, sz, cells_fn, lamps=()):
    p = P(style, (sx, 7, sz), name, "infrastructure/roads")
    p.found()
    m = p.m
    for x in range(sx):
        for z in range(sz):
            kind = cells_fn(x, z)
            if kind == "road":
                s = (m["pave2"] if (x * 3 + z) % 5 == 0 else m["pave"]) if style == "Cascadia" else \
                    ("bricks" if (x + z) % 2 else "mud_bricks")
            elif kind == "curb":
                s = (m["curb"] + "[axis=" + ("z" if True else "x") + "]") if style == "Cascadia" else m["curb"]
            else:
                s = "cobblestone" if style == "Cascadia" else "stone_bricks"
            p.S(x, 1, z, s)
    for x, z in lamps:
        p.lamp(x, 2, z)
    return p.done((sx // 2, 1, sz // 2))


def build_roads(style):
    out = {}
    W = 7

    def straight(x, z):
        return "road" if 1 <= x <= W - 2 else "curb" if x in (0, W - 1) else "walk"
    out["infrastructure/roads/roadstraight"] = road_piece(style, "roadstraight", W, 8, straight, [(0, 4)])
    out["infrastructure/roads/roadcorner"] = road_piece(style, "roadcorner", W, W,
                                                        lambda x, z: "road" if (x >= 1 and z >= 1) else "curb")
    out["infrastructure/roads/roadtjunction"] = road_piece(style, "roadtjunction", W + 6, W,
                                                           lambda x, z: "road" if (1 <= z <= W - 2 or 4 <= x <= W) else "curb")
    out["infrastructure/roads/roadintersection"] = road_piece(style, "roadintersection", W + 6, W + 6,
                                                              lambda x, z: "road" if (1 <= z - 3 <= W - 2 or 4 <= x <= W) else "curb")
    out["infrastructure/roads/avenue"] = road_piece(style, "avenue", W + 6, 16,
                                                    lambda x, z: "walk" if x in (6, 7) else ("curb" if x in (0, 12) else "road"),
                                                    [(6, 3), (7, 11)])
    p = P(style, (7, 9, 8), "roadstairs", "infrastructure/roads")
    p.found()
    for i in range(6):
        for x in range(7):
            p.fill(x, 1, i + 1, x, i, i + 1, p.m["stone"])
            p.S(x, 1 + i, i + 1, p.st("south", mat="cobblestone" if style == "Cascadia" else "brick"))
            if x in (0, 6):
                p.S(x, 1 + i, i + 1, p.m["stone"])
                p.S(x, 2 + i, i + 1, p.m["fence"] + FENCE)
    out["infrastructure/roads/roadstairs"] = p.done((3, 1, 0))
    return out


def build_rails(style):
    out = {}
    m = M[style]
    for name, sz in (("railstraight", 8), ("railcorner", 5)):
        p = P(style, (5, 5, sz), name, "infrastructure/rails")
        p.found()
        for x in range(5):
            for z in range(sz):
                p.S(x, 1, z, m["pave2"] if style == "Cascadia" else m["pave"])
        if name == "railstraight":
            for z in range(sz):
                p.S(1, 1, z, m["plank"])
                p.S(3, 1, z, m["plank"])
                p.S(2, 2, z, "rail[shape=north_south,waterlogged=false]")
        else:
            for x, z, sh in ((2, 0, "north_south"), (2, 1, "north_south"), (2, 2, "north_east"), (3, 2, "east_west"), (4, 2, "east_west")):
                p.S(x, 2, z, f"rail[shape={sh},waterlogged=false]")
        out[f"infrastructure/rails/{name}"] = p.done((2, 1, 0))
    p = P(style, (9, 9, 14), "railstop", "infrastructure/rails")
    p.found()
    for z in range(14):
        p.S(1, 1, z, m["pave2"])
        p.S(1, 2, z, "rail[shape=north_south,waterlogged=false]")
        for x in range(3, 9):
            p.S(x, 1, z, m["stone"])
            p.S(x, 2, z, m["plank"])
    for z in (2, 7, 12):
        p.fill(8, 3, z, 8, 6, z, m["post"])
        p.fill(3, 3, z, 3, 5, z, m["post"])
    for z in range(1, 14):
        for x in range(3, 9):
            p.S(x, 6 + (1 if x > 5 else 0), z, p.st("west") if x == 3 else (m["roof"] + "_planks"))
    for z in (4, 6, 9, 11):
        p.seat(7, 3, z, "east")
    p.S(5, 5, 7, HLANT)
    out["infrastructure/rails/railstop"] = p.deco((6, 2, 13), ground_y=2)
    return out


def build_canals(style):
    out = {}
    m = M[style]
    shapes = {"canalstraight": (9, 8, lambda x, z: 2 <= x <= 6),
              "canalcorner": (9, 9, lambda x, z: (2 <= x <= 6 and z >= 2) or (2 <= z <= 6 and x >= 2)),
              "canalintersection": (9, 9, lambda x, z: 2 <= x <= 6 or 2 <= z <= 6),
              "canallock": (9, 12, lambda x, z: 2 <= x <= 6)}
    for name, (sx, sz, wet) in shapes.items():
        p = P(style, (sx, 6, sz), name, "infrastructure/canals")
        for x in range(sx):
            for z in range(sz):
                if wet(x, z):
                    p.S(x, 0, z, m["stone"])
                    p.S(x, 1, z, "water[level=0]")
                else:
                    p.S(x, 0, z, SOLID)
                    edge = any(wet(x + dx, z + dz) for dx in (-1, 0, 1) for dz in (-1, 0, 1)
                               if 0 <= x + dx < sx and 0 <= z + dz < sz)
                    p.S(x, 1, z, m["water_edge"] if edge else m["pave"])
                    if edge and (x + z) % 3 == 0 and style == "Cascadia":
                        p.S(x, 2, z, m["beam_z"])
                    elif edge and style == "Hearthwood":
                        p.S(x, 2, z, m["fence"] + FENCE)
        if name == "canallock":
            for z in (3, 8):
                for x in range(1, 8):
                    p.S(x, 2, z, m["plank"])
                    if x in (1, 7):
                        p.S(x, 3, z, LANT)
                for x in range(2, 7):
                    p.S(x, 1, z, m["plank"] if style == "Cascadia" else "stone_bricks")
        out[f"infrastructure/canals/{name}"] = p.done((sx // 2, 1, 0))
    return out


def build_bridges(style):
    out = {}
    m = M[style]
    # straight span
    p = P(style, (7, 10, 8), "bridgestraight", "infrastructure/bridge")
    for z in range(8):
        for x in range(7):
            p.S(x, 0, z, m["plank"] if style == "Cascadia" else m["stone"])
        if style == "Cascadia":                       # covered bridge
            for x in (0, 6):
                p.fill(x, 1, z, x, 3, z, m["wall"] if z % 3 else m["post"])
                if z % 3 == 1:
                    p.S(x, 2, z, "air")
            for x in range(-1, 8):
                k = 3 - abs(x - 3)
                p.S(x, 4 + k, z, p.st("east" if x < 3 else "west") if x != 3 else "dark_oak_planks")
        else:                                          # brick parapets with lamp pillars
            for x in (0, 6):
                p.S(x, 1, z, m["stone2"])
                p.S(x, 2, z, "stone_brick_slab[type=bottom,waterlogged=false]" if z % 4 else LANT)
    out["infrastructure/bridge/bridgestraight"] = p.done((3, 0, 0))
    # ramp
    p = P(style, (7, 8, 10), "bridgestart", "infrastructure/bridge")
    for z in range(10):
        rise = min(4, z // 2)
        for x in range(7):
            p.fill(x, 0, z, x, rise, z, m["stone"])
            if x in (0, 6):
                p.S(x, rise + 1, z, m["fence"] + FENCE)
    out["infrastructure/bridge/bridgestart"] = p.done((3, 0, 0))
    # pier / arch pillar
    p = P(style, (7, 20, 7), "bridgepillar", "infrastructure/bridge")
    for y in range(0, 19):
        for x in range(1, 6):
            for z in range(1, 6):
                d = max(abs(x - 3), abs(z - 3))
                if style == "Cascadia":
                    p.S(x, y, z, m["stone2"] if (x + y + z) % 4 == 0 else m["stone"])
                else:
                    if d == 2 or y == 18:
                        p.S(x, y, z, m["stone"] if y % 5 else m["stone2"])
    for x in range(7):
        for z in range(7):
            p.S(x, 19, z, m["plank"] if style == "Cascadia" else m["stone2"])
    out["infrastructure/bridge/bridgepillar"] = p.done((3, 19, 3))
    return out


def build_subway(style):
    out = {}
    m = M[style]
    for name, sz in (("subwaystraight", 8), ("subwaycorner", 9)):
        p = P(style, (9, 7, sz), name, "infrastructure/subway")
        for x in range(9):
            for z in range(sz):
                inside = 1 <= x <= 7 and (z >= 0 if name == "subwaystraight" else (1 <= z <= 7 or (z == 0)))
                for y in range(7):
                    if not inside or y in (0, 6):
                        p.S(x, y, z, (m["stone"] if y == 0 or y == 6 else SOLID) if inside or y in (0, 6) else SOLID)
                    else:
                        p.S(x, y, z, "air")
                if inside:
                    p.S(x, 0, z, m["pave2"])
        for z in range(0, sz, 3):                      # timber shoring / tiled arches
            for x in (1, 7):
                p.fill(x, 1, z, x, 5, z, m["post"] if style == "Cascadia" else "white_terracotta")
            for x in range(1, 8):
                p.S(x, 5, z, m["beam_x"] if style == "Cascadia" else "bricks")
            p.S(4, 4, z, HLANT)
        if name == "subwaystraight":
            for z in range(sz):
                p.S(4, 1, z, "rail[shape=north_south,waterlogged=false]")
        else:
            for x, z, sh in ((4, 0, "north_south"), (4, 1, "north_south"), (4, 2, "north_south"), (4, 3, "north_south"),
                             (4, 4, "north_east"), (5, 4, "east_west"), (6, 4, "east_west"), (7, 4, "east_west"), (8, 4, "east_west")):
                p.S(x, 1, z, f"rail[shape={sh},waterlogged=false]")
        out[f"infrastructure/subway/{name}"] = p.done((4, 1, 0))
    p = P(style, (7, 14, 14), "subwayentrance", "infrastructure/subway")
    for x in range(7):
        for z in range(14):
            for y in range(0, 8):
                p.S(x, y, z, SOLID)
            p.S(x, 8, z, m["pave"])
    for i in range(7):
        z = 2 + i
        for x in range(1, 6):
            for y in range(8 - i, 12):
                p.S(x, y, z, "air")
            p.S(x, 7 - i, z, p.st("north", mat="cobblestone" if style == "Cascadia" else "brick"))
        for x in (0, 6):
            p.fill(x, 7 - i, z, x, 8, z, m["stone"])
    for z in range(9, 14):
        for x in range(1, 6):
            p.fill(x, 1, z, x, 5, z, "air")
            p.S(x, 0, z, m["pave2"])
    for z in (1, 4, 7):                                # entrance portal frames
        for x in (0, 6):
            p.fill(x, 9, z, x, 11, z, m["post"])
        for x in range(0, 7):
            p.S(x, 12, z, m["beam_x"])
    for z in range(1, 8):
        for x in range(-1, 8):
            k = 3 - abs(x - 3)
            p.S(x, 12 + k, z, p.st("east" if x < 3 else "west") if x != 3 else m["roof"] + "_planks")
    out["infrastructure/subway/subwayentrance"] = p.done((3, 8, 0))
    return out


def build_boardwalk(style):
    out = {}
    m = M[style]
    for name, (sx, sz) in (("boardwalkstraight", (5, 8)), ("boardwalkcorner", (5, 5)), ("pier", (9, 12))):
        p = P(style, (sx, 10, sz), name, "infrastructure/boardwalk")
        for x in range(sx):
            for z in range(sz):
                p.S(x, 2, z, m["plank"])
                if x in (0, sx - 1) and z % 4 == 0:
                    p.fill(x, 0, z, x, 1, z, m["post"])
                rail = (x in (0, sx - 1)) if name != "boardwalkcorner" else (x == sx - 1 or z == sz - 1)
                if name == "pier":
                    rail = x in (0, sx - 1) or z == sz - 1
                if rail and z > 0:
                    p.S(x, 3, z, m["fence"] + FENCE)
        if name == "pier":
            for x, z in ((1, 10), (7, 10)):
                p.lamp(x, 3, z, 2)
            for z in (3, 6):
                p.seat(1, 3, z, "west")
                p.seat(sx - 2, 3, z, "east")
            out[f"infrastructure/boardwalk/{name}"] = p.deco((4, 2, 0), ground_y=2)
        else:
            out[f"infrastructure/boardwalk/{name}"] = p.done((sx // 2, 2, 0))
    return out


def build_cliffclimb(style):
    out = {}
    m = M[style]
    for name, H in (("cliffclimbbase", 9), ("cliffclimbsegment", 8), ("cliffclimblanding", 6)):
        p = P(style, (7, H + 1, 7), name, "infrastructure/cliffclimb")
        for y in range(0, H + 1):
            for x, z in ((0, 0), (6, 0), (0, 6), (6, 6)):
                p.S(x, y, z, m["post"] if style == "Cascadia" else m["stone2"])
            if style == "Hearthwood":
                for x in range(7):
                    for z in range(7):
                        if (x in (0, 6) or z in (0, 6)) and y % 4 != 2:
                            p.S(x, y, z, m["stone"])
        if name == "cliffclimblanding":
            for x in range(7):
                for z in range(7):
                    p.S(x, 0, z, m["plank"])
                    p.S(x, H, z, m["roof"] + "_planks")
            out[f"infrastructure/cliffclimb/{name}"] = p.done((3, 0, 0))
            continue
        ring = [(1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (5, 2), (5, 3), (5, 4), (5, 5), (4, 5), (3, 5), (2, 5), (1, 5), (1, 4), (1, 3), (1, 2)]
        face = ["east"] * 4 + ["south"] * 4 + ["west"] * 4 + ["north"] * 4
        p.fill(2, 0, 2, 4, H, 4, m["post"] if style == "Cascadia" else m["stone2"])
        for i in range(H):
            j = (2 * i) % 16
            for jj in (j, (j + 1) % 16):
                x, z = ring[jj]
                p.S(x, i, z, p.st(face[jj]) if jj == j else f"{m['slab']}[type=top,waterlogged=false]")
        if name == "cliffclimbbase":
            p.fill(1, 1, 0, 1, 2, 0, "air")
        out[f"infrastructure/cliffclimb/{name}"] = p.done((3, 0, 0))
    return out


# ============================================================================ parks
def build_parks(style):
    out = {}
    m = M[style]
    p = P(style, (5, 5, 3), "bench", "decorations/parks")
    p.found()
    for x in range(5):
        for z in range(3):
            p.S(x, 1, z, m["pave"] if style == "Hearthwood" else m["pave2"])
    if style == "Cascadia":
        p.S(0, 2, 1, "stripped_spruce_log[axis=y]")
        p.S(4, 2, 1, "stripped_spruce_log[axis=y]")
    else:
        p.S(0, 2, 1, "potted_azalea_bush")
        p.S(4, 2, 1, "potted_azalea_bush")
    for x in (1, 2, 3):
        p.seat(x, 2, 1, "south")
    out["decorations/parks/bench"] = p.deco((2, 1, 0))

    for name, S in (("smallpark", 11), ("mediumpark", 17), ("parklarge", 25), ("plaza", 19), ("fountain", 9)):
        p = P(style, (S, 12, S), name, "decorations/parks")
        p.found()
        C = S // 2
        for x in range(S):
            for z in range(S):
                path = abs(x - C) <= 1 or abs(z - C) <= 1
                if name in ("plaza", "fountain"):
                    s = (m["pave"] if (x + z) % 2 else m["pave2"]) if style == "Hearthwood" else \
                        ("cobblestone" if (x * 7 + z * 3) % 5 else "mossy_cobblestone")
                else:
                    s = (m["pave"] if style == "Hearthwood" else "coarse_dirt") if path else \
                        ("grass_block[snowy=false]" if style == "Hearthwood" else ("podzol[snowy=false]" if (x + z) % 5 == 0 else "grass_block[snowy=false]"))
                p.S(x, 1, z, s)
                if not path and name not in ("plaza", "fountain") and (x * 5 + z * 3) % 13 == 0:
                    p.S(x, 2, z, ("fern" if style == "Cascadia" else ["poppy", "cornflower", "azure_bluet", "oxeye_daisy"][(x + z) % 4]))
        if name in ("smallpark", "fountain", "plaza") or style == "Hearthwood":
            r = 2 if S <= 11 else 3
            for x in range(C - r, C + r + 1):
                for z in range(C - r, C + r + 1):
                    e = max(abs(x - C), abs(z - C)) == r
                    p.S(x, 1, z, (m["stone2"] if style == "Hearthwood" else "mossy_cobblestone") if e else "water[level=0]")
                    if e:
                        p.S(x, 2, z, ("stone_brick_slab[type=bottom,waterlogged=false]" if style == "Hearthwood"
                                      else "cobblestone_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]"))
            p.fill(C, 1, C, C, 2, C, m["stone2"] if style == "Hearthwood" else "mossy_cobblestone")
            p.S(C, 3, C, LANT)
        else:                                            # Cascadia clearing: fire pit with log seats + spring
            p.S(C, 1, C, "cobblestone")
            p.S(C, 2, C, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
            for dx, dz, back in ((-2, 0, "west"), (2, 0, "east"), (0, -2, "north"), (0, 2, "south")):
                p.seat(C + dx, 2, C + dz, back)
        if S >= 17:                                      # shelter / gazebo in a corner
            gx, gz = S - 6, 2
            for x in range(gx, gx + 5):
                for z in range(gz, gz + 5):
                    p.S(x, 1, z, m["plank"])
            for x, z in ((gx, gz), (gx + 4, gz), (gx, gz + 4), (gx + 4, gz + 4)):
                p.fill(x, 2, z, x, 4, z, m["post"])
            for i in range(3):
                for x in range(gx - 1 + i, gx + 6 - i):
                    for z in range(gz - 1 + i, gz + 6 - i):
                        if x in (gx - 1 + i, gx + 5 - i) or z in (gz - 1 + i, gz + 5 - i):
                            p.S(x, 5 + i, z, m["roof"] + "_planks")
            p.seat(gx + 2, 2, gz + 3, "south")
            p.S(gx + 2, 4, gz + 2, HLANT)
        for off in (-4, 4):
            if S >= 11:
                p.seat(C + off, 2, 1, "north")
                p.seat(C + off, 2, S - 2, "south")
        for x, z in ((1, 1), (S - 2, S - 2)):
            p.lamp(x, 2, z)
        p.tags.setdefault((C, 1, C - 3 if S > 9 else 1), []).append("stand_out")
        out[f"decorations/parks/{name}"] = p.deco((C, 1, 0))
    return out


def main():
    root, style = Path(sys.argv[1]), sys.argv[2]
    pieces = {}
    for fn in (build_walls, build_roads, build_rails, build_canals, build_bridges, build_subway, build_boardwalk,
               build_cliffclimb, build_parks):
        pieces.update(fn(style))
    for rel, bp in pieces.items():
        out = root / f"{rel}.blueprint"
        out.parent.mkdir(parents=True, exist_ok=True)
        bp.name = out.name
        bp.save(out)
    print(f"{style}: {len(pieces)} infrastructure / wall / park pieces")


if __name__ == "__main__":
    main()
