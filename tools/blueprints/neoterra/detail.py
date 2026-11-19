"""
Neoterra detail pass – runs over every generated blueprint and makes it richer, level by level.

The generators lay out the buildings (shell, rooms, all hut requirements). This pass then:

  1. texture   – swaps the flat base materials for a wide, theme-based mix: white walls become
                 calcite / diorite / quartz panels, floors get tile grids with inlays, cyan accents
                 become terracotta, oxidised copper and prismarine, glass gets tinted bands.
                 Levels 1-3 stay on cheap blocks, levels 4-5 use premium ones.
  2. facade    – window boxes of flowering azalea under upper windows (L2+), hanging vines (L4+).
  3. roof      – green-roof planting, vents, solar arrays, roof trees, glowing roof edges; level 5
                 gets a glass sky-lounge with a spire on the highest roof (blueprint grows taller).
  4. ground    – grass, flowers, bushes, tall flowers and trees in the lawns (denser each level).
  5. interior  – potted plants in room corners, rugs, pendant lights (L4-5), plants on counters.

Anything that carries a block entity, a tag, a hut requirement or a path is protected. After each
step the blueprint is walk-checked again (huts, beds, racks, workstations and tagged seats/guard
spots); if the step made anything unreachable it is rolled back.

usage: python detail.py <pack-or-dir> [more dirs/files...]
"""
from __future__ import annotations

import copy
import hashlib
import re
import sys
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from blueprint import load, parse_state, AIR  # noqa: E402
import walkcheck  # noqa: E402

MC = "minecraft:"
CHEAP_FORBIDDEN = ("domum", "quartz", "deepslate", "sea_lantern", "stained_glass", "end_rod")


def h(*a):
    """Deterministic 0..1 hash."""
    d = hashlib.md5(repr(a).encode()).digest()
    return int.from_bytes(d[:4], "little") / 2 ** 32


def pick(table, r):
    acc = 0.0
    for w, s in table:
        acc += w
        if r < acc:
            return s
    return table[-1][1]


# ------------------------------------------------------------------ material families
WHITE = {"white_concrete"}
FLOORS = {"light_gray_concrete", "smooth_stone", "polished_andesite"}
CYAN = {"cyan_concrete"}
GLASS = {"glass", "light_blue_stained_glass"}

WALL_MIX = {
    1: [(.78, "white_concrete"), (.22, "calcite")],
    2: [(.6, "white_concrete"), (.25, "calcite"), (.15, "polished_diorite")],
    3: [(.4, "white_concrete"), (.28, "calcite"), (.14, "polished_diorite"), (.1, "birch_planks"), (.08, "bone_block[axis=y]")],
    4: [(.32, "smooth_quartz"), (.24, "quartz_bricks"), (.22, "white_concrete"), (.14, "calcite"),
        (.08, "white_glazed_terracotta[facing=north]")],
    5: [(.27, "smooth_quartz"), (.22, "quartz_bricks"), (.13, "calcite"), (.12, "white_concrete"),
        (.08, "polished_diorite"), (.06, "chiseled_quartz_block"), (.06, "bone_block[axis=y]"),
        (.06, "white_glazed_terracotta[facing=north]")],
}
COURSE = {1: None, 2: "smooth_stone", 3: "polished_tuff", 4: "quartz_bricks", 5: "chiseled_quartz_block"}
HOMES = ("cottage", "house", "apartment", "quadplex", "playerhouse", "skytower", "tavern", "library", "school",
         "university", "communitycollege", "bunker")
WOOD_FIELD = {1: "birch_planks", 2: "birch_planks", 3: "bamboo_mosaic", 4: "birch_planks", 5: "bamboo_mosaic"}
WOOD_GROUT = {1: "stripped_birch_log[axis=x]", 2: "stripped_birch_log[axis=x]", 3: "stripped_bamboo_block[axis=x]",
              4: "stripped_warped_stem[axis=x]", 5: "stripped_warped_stem[axis=x]"}
FLOOR_FIELD = {1: [(.6, "polished_andesite"), (.4, "smooth_stone")],
               2: [(1.0, "polished_andesite")],
               3: [(.7, "polished_diorite"), (.3, "calcite")],
               4: [(.5, "calcite"), (.5, "polished_diorite")],
               5: [(.7, "smooth_quartz"), (.3, "calcite")]}
FLOOR_GROUT = {1: "smooth_stone", 2: "smooth_stone", 3: "polished_andesite", 4: "smooth_quartz",
               5: "polished_deepslate"}
FLOOR_INLAY = {1: "smooth_stone", 2: "cyan_terracotta", 3: "cyan_terracotta", 4: "prismarine_bricks",
               5: "dark_prismarine"}
CYAN_MIX = {
    1: [(.8, "cyan_concrete"), (.2, "cyan_terracotta")],
    2: [(.6, "cyan_concrete"), (.4, "cyan_terracotta")],
    3: [(.45, "cyan_concrete"), (.3, "cyan_terracotta"), (.25, "waxed_oxidized_cut_copper")],
    4: [(.4, "prismarine_bricks"), (.2, "dark_prismarine"), (.2, "cyan_concrete"), (.2, "waxed_oxidized_copper")],
    5: [(.3, "dark_prismarine"), (.3, "prismarine_bricks"), (.15, "waxed_oxidized_copper_grate[waterlogged=false]"),
        (.15, "waxed_oxidized_cut_copper"), (.1, "cyan_concrete")],
}
GLASS_BANDS = {4: ["light_blue_stained_glass", "light_blue_stained_glass", "cyan_stained_glass"],
               5: ["light_blue_stained_glass", "cyan_stained_glass", "light_blue_stained_glass", "white_stained_glass"]}

FLOWERS = ["dandelion", "poppy", "azure_bluet", "oxeye_daisy", "cornflower", "allium", "lily_of_the_valley",
           "red_tulip", "white_tulip", "orange_tulip", "pink_tulip"]
POTS = ["potted_fern", "potted_azalea_bush", "potted_flowering_azalea_bush", "potted_bamboo", "potted_oak_sapling",
        "potted_lily_of_the_valley", "potted_cornflower", "potted_blue_orchid", "potted_cactus", "potted_birch_sapling"]
LEAVES = "azalea_leaves[distance=1,persistent=true,waterlogged=false]"
FLEAVES = "flowering_azalea_leaves[distance=1,persistent=true,waterlogged=false]"
OAK_LEAVES = "oak_leaves[distance=1,persistent=true,waterlogged=false]"
DIRS = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
TAG_TARGETS = ("sit", "sit_in", "sit_out", "work", "stand_in", "stand_out", "knight", "archer")


def nm(s):
    return parse_state(s)[0].split(":", 1)[1]


class Detailer:
    def __init__(self, bp, level, name):
        self.bp, self.L, self.name = bp, level, name
        self._score = None
        self.tags = self._tags()
        self.protect = set(bp.tile_entities)
        for p in self.tags:
            x, y, z = p
            self.protect |= {(x, y, z), (x, y + 1, z), (x, y + 2, z)}
        self.sensitive = set()
        for x, y, z, s in bp.blocks():
            n = nm(s)
            if any(k in n for k in ("door", "ladder", "stairs", "trapdoor", "bed", "blockhut", "rack", "gate",
                                    "water", "lava", "rail", "scaffold", "substitution", "chest", "barrel",
                                    "furnace", "smoker", "anvil", "table", "cauldron", "brewing", "composter",
                                    "beehive", "lectern", "grave", "obsidian", "loom", "grindstone", "stonecutter",
                                    "target", "hay_block", "sand", "coarse_dirt", "composted", "farmland",
                                    "soul_sand", "fence")):
                self.sensitive.add((x, y, z))
        self.sensitive |= set(self.tags)
        self.sensitive |= set(bp.tile_entities)

    # -------------------------------------------------------------- helpers
    def _tags(self):
        out = {}
        for (ax, ay, az), te in self.bp.tile_entities.items():
            bdp = te.get("blueprintDataProvider")
            if bdp is None:
                continue
            for e in bdp.get("posTagMap", []):
                p = (ax + int(e["tagPos"]["x"]), ay + int(e["tagPos"]["y"]), az + int(e["tagPos"]["z"]))
                out.setdefault(p, []).extend(str(t["tagName"]) for t in e["tagNameList"])
        return out

    def get(self, x, y, z):
        return self.bp.get(x, y, z) if self.bp.inside(x, y, z) else AIR

    def n(self, x, y, z):
        return nm(self.get(x, y, z))

    def air(self, x, y, z):
        return self.get(x, y, z) == AIR

    def solid(self, x, y, z):
        n = self.n(x, y, z)
        return n != "air" and not any(k in n for k in ("pane", "bars", "flower", "grass", "fern", "carpet", "torch",
                                                       "lantern", "rod", "chain", "rail", "vine", "button", "sign",
                                                       "paperwall", "slab", "stairs", "door", "ladder", "_wall",
                                                       "fence", "leaves", "water", "substitution", "tulip",
                                                       "poppy", "dandelion", "bluet", "daisy", "allium", "lily",
                                                       "cornflower", "potted", "sapling"))

    def covered(self, x, y, z, reach=10):
        for yy in range(y + 1, min(self.bp.sy, y + reach + 1)):
            if self.solid(x, yy, z):
                return True
        return False

    def sky(self, x, y, z):
        return all(self.air(x, yy, z) for yy in range(y, self.bp.sy))

    def near_sensitive(self, x, y, z, r=1):
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                for dy in (-1, 0, 1):
                    if (x + dx, y + dy, z + dz) in self.sensitive:
                        return True
        return False

    def put(self, x, y, z, s):
        if (x, y, z) in self.protect or not self.bp.inside(x, y, z):
            return False
        self.bp.set(x, y, z, s if ":" in s else MC + s)
        return True

    def grow(self, extra):
        bp = self.bp
        if extra <= 0:
            return
        for _ in range(extra):
            bp.grid.append([[AIR] * bp.sx for _ in range(bp.sz)])
        bp.sy += extra
        for te in bp.tile_entities.values():
            bdp = te.get("blueprintDataProvider")
            if bdp is None:
                continue
            c1, c2 = bdp["corner1"], bdp["corner2"]
            if all(int(c[k]) == 0 for c in (c1, c2) for k in "xyz"):
                continue                                               # child-hut placeholder
            c2["y"] = type(c2["y"])(int(c2["y"]) + extra)

    # -------------------------------------------------------------- reachability metric
    def metric(self):
        _, problems, seen = walkcheck.analyse(self.bp, return_seen=True)
        bad_tags = 0
        for (x, y, z), names in self.tags.items():
            if not any(t in TAG_TARGETS for t in names):
                continue
            ok = any((x + dx, y + dy, z + dz) in seen for dx, dz in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1))
                     for dy in (-1, 0, 1, 2))
            bad_tags += not ok
        return len(problems) + bad_tags

    def guarded(self, step):
        if self._score is None:
            self._score = self.metric()
        grid = copy.deepcopy(self.bp.grid)
        sy = self.bp.sy
        tes = {p: copy.deepcopy(t) for p, t in self.bp.tile_entities.items()}
        step()
        after = self.metric()
        if after > self._score:
            self.bp.grid, self.bp.sy, self.bp.tile_entities = grid, sy, tes
            return False
        self._score = after
        return True

    # -------------------------------------------------------------- 1. texture
    def texture(self):
        bp, L = self.bp, self.L
        for x, y, z, s in list(bp.blocks()):
            if (x, y, z) in self.protect:
                continue
            n = nm(s)
            top_open = not self.solid(x, y + 1, z)
            r = h("t", x, y, z, self.name)
            if n in WHITE and not top_open:
                course = COURSE[L]
                if course and y % (6 if L >= 4 else 5) == 0:
                    new = course
                elif L >= 4 and (x % 6 == 0 or z % 6 == 0) and not (x % 6 == 0 and z % 6 == 0):
                    new = "quartz_pillar[axis=y]"
                else:
                    new = pick(WALL_MIX[L], h("w", x // 2, y, z // 2, self.name))
            elif (n in FLOORS or (n in WHITE and top_open)) and any(k in self.name for k in HOMES) \
                    and top_open and self.covered(x, y, z, 8) and L >= 2:
                new = WOOD_GROUT[L] if z % 4 == 0 else WOOD_FIELD[L]
            elif n in FLOORS or (n in WHITE and top_open):
                grid = 4 if L <= 3 else 5
                gx, gz = x % grid == 0, z % grid == 0
                if L == 1:
                    new = pick(FLOOR_FIELD[1], r) if n != "light_gray_concrete" else n
                elif gx and gz:
                    new = FLOOR_INLAY[L]
                elif gx or gz:
                    new = FLOOR_GROUT[L] if (L < 5 or self.covered(x, y, z, 8)) else "polished_diorite"
                else:
                    new = pick(FLOOR_FIELD[L], h("f", x // 2, z // 2, self.name))
            elif n in CYAN:
                new = pick(CYAN_MIX[L], r)
            elif n in GLASS and L >= 4:
                band = GLASS_BANDS[L]
                new = band[(y // 2) % len(band)]
            else:
                continue
            bp.set(x, y, z, MC + new)

    # -------------------------------------------------------------- 2. facade
    def facade(self):
        if self.L < 2:
            return
        bp, L = self.bp, self.L
        for x, y, z, s in list(bp.blocks()):
            if "glass" not in s or "pane" in s or y < 4:
                continue
            for dname, (dx, dz) in DIRS.items():
                bx, by, bz = x + dx, y - 1, z + dz
                if not (self.air(x + dx, y, z + dz) and self.air(bx, by, bz) and self.air(bx, by - 1, bz)
                        and self.air(bx, by - 2, bz) and not self.covered(bx, by, bz, 12)):
                    continue
                if not self.solid(x, y - 1, z) or h("wb", x, y, z, dname) > (.45 if L < 4 else .7):
                    continue
                if self.near_sensitive(bx, by, bz):
                    continue
                self.put(bx, by, bz, FLEAVES if h("fl", x, z) < .6 else LEAVES)
                if L >= 4:
                    back = {"north": "south", "south": "north", "east": "west", "west": "east"}[dname]
                    props = {k: "false" for k in ("east", "north", "south", "west", "up")}
                    props[back] = "true"
                    vine = "vine[" + ",".join(f"{k}={v}" for k, v in sorted(props.items())) + "]"
                    for k in range(1, 1 + int(1 + 2 * h("vl", x, y, z))):
                        if self.air(bx, by - k, bz) and self.solid(x, by - k, z) and self.air(bx, by - k - 1, bz):
                            self.put(bx, by - k, bz, vine)
                        else:
                            break

    # -------------------------------------------------------------- 3. roof
    def roof_groups(self):
        bp = self.bp
        tops = {}
        for x in range(bp.sx):
            for z in range(bp.sz):
                for y in range(bp.sy - 1, 2, -1):
                    if not self.air(x, y, z):
                        if self.solid(x, y, z) and y >= 4 and self.sky(x, y + 1, z):
                            tops[(x, z)] = y
                        break
        seen, groups = set(), []
        for p, y in tops.items():
            if p in seen:
                continue
            g, stack = [], [p]
            seen.add(p)
            while stack:
                cx, cz = stack.pop()
                g.append((cx, cz))
                for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    q = (cx + dx, cz + dz)
                    if q not in seen and tops.get(q) == y:
                        seen.add(q)
                        stack.append(q)
            if len(g) >= 12:
                groups.append((y, set(g)))
        return groups

    def roof(self):
        L = self.L
        if L < 2:
            return
        groups = self.roof_groups()
        if not groups:
            return
        need = 0
        hi = max(y for y, _ in groups)
        top_y, top_g = max(groups, key=lambda t: (t[0] >= hi - 6, len(t[1])))
        if L >= 4:
            need = top_y + (11 if L == 5 else 8) - (self.bp.sy - 1)
        self.grow(need)
        trees = []
        for y, g in groups:
            edge = {(x, z) for x, z in g if any((x + dx, z + dz) not in g for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
            inner = g - edge
            lounge = set()
            if L == 5 and g is top_g and len(inner) >= 16:
                lounge = self.sky_lounge(y, inner)
            for x, z in sorted(inner - lounge):
                if self.near_sensitive(x, y + 1, z, 2) or not self.air(x, y + 1, z):
                    continue
                r = h("r", x, z, y, self.name)
                ground = self.n(x, y, z)
                replaceable = ground in WHITE | FLOORS | {"calcite", "polished_diorite", "smooth_quartz", "quartz_bricks",
                                                          "polished_deepslate", "cyan_terracotta", "prismarine_bricks",
                                                          "dark_prismarine", "white_concrete"}
                if L <= 3:
                    if r < .03:
                        self.put(x, y + 1, z, "light_gray_concrete")             # HVAC box with grille
                        self.put(x, y + 2, z, "iron_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]")
                    elif L == 3 and r < .3 and replaceable:
                        self.put(x, y, z, "moss_block")
                        self.put(x, y + 1, z, ["moss_carpet", "short_grass", "fern", "azure_bluet"][int(r * 40) % 4])
                    continue
                garden = .42 if L == 4 else .5
                if r < garden and replaceable:
                    self.put(x, y, z, "moss_block" if r < garden * .6 else "grass_block[snowy=false]")
                    rr = h("p", x, z)
                    plant = ("short_grass" if rr < .3 else "fern" if rr < .45 else
                             FLOWERS[int(rr * 100) % len(FLOWERS)] if rr < .75 else "moss_carpet")
                    self.put(x, y + 1, z, plant)
                    if rr > .93 and all(abs(x - tx) + abs(z - tz) > 6 for tx, tz in trees) and self.tree_fits(x, y + 1, z):
                        self.tree(x, y + 1, z, 3)
                        trees.append((x, z))
                elif r < garden + .2 and x % 3 != 0:
                    self.put(x, y + 1, z, "daylight_detector[inverted=false,power=0]")
            # glowing / accented roof edge
            for x, z in edge:
                if (x, y, z) in self.protect or self.near_sensitive(x, y, z, 1):
                    continue
                if (x + z) % (2 if L == 5 else 4) == 0 and L >= 4 and self.n(x, y, z) in WHITE | {"calcite", "smooth_quartz",
                                                                                                    "quartz_bricks", "white_concrete"}:
                    self.put(x, y, z, "sea_lantern")

    def tree_fits(self, x, y, z, h_=3):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for dy in range(0, h_ + 3):
                    if not self.air(x + dx, y + dy, z + dz) and not (dx == dz == 0 and dy == 0):
                        return False
        return y + h_ + 2 < self.bp.sy

    def tree(self, x, y, z, h_=3):
        self.put(x, y - 1, z, "grass_block[snowy=false]")
        for k in range(h_):
            self.put(x, y + k, z, "stripped_birch_log[axis=y]" if self.L >= 4 else "stripped_oak_log[axis=y]")
        leaves = FLEAVES if self.L >= 5 else (LEAVES if self.L >= 4 else OAK_LEAVES)
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for k in (h_, h_ + 1):
                    if k == h_ + 1 and abs(dx) + abs(dz) == 2:
                        continue
                    if self.air(x + dx, y + k, z + dz):
                        self.put(x + dx, y + k, z + dz, leaves)
        if self.air(x, y + h_ + 2, z):
            self.put(x, y + h_ + 2, z, leaves)

    def sky_lounge(self, y, inner):
        """Level 5 crown: glass pavilion with a glowing rim and a spire, on the highest roof."""
        best = None
        xs = sorted({x for x, _ in inner})
        zs = sorted({z for _, z in inner})
        for size in (9, 8, 7, 6, 5, 4):
            for x1 in xs:
                for z1 in zs:
                    cells = {(x, z) for x in range(x1, x1 + size) for z in range(z1, z1 + size)}
                    if cells <= inner and not any(self.near_sensitive(x, y + 1, z, 1) for x, z in cells):
                        best = (x1, z1, size)
                        break
                if best:
                    break
            if best:
                break
        if not best:
            return set()
        x1, z1, s = best
        x2, z2 = x1 + s - 1, z1 + s - 1
        cx, cz = (x1 + x2) // 2, (z1 + z2) // 2
        used = set()
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                used.add((x, z))
                e = x in (x1, x2) or z in (z1, z2)
                corner = x in (x1, x2) and z in (z1, z2)
                for yy in range(y + 1, y + 4):
                    if corner:
                        self.put(x, yy, z, "quartz_pillar[axis=y]")
                    elif e:
                        door = (z == z2 and x == cx and yy <= y + 2)
                        self.put(x, yy, z, "air" if door else
                                 ("light_blue_stained_glass" if yy < y + 3 else "cyan_stained_glass"))
                    else:
                        self.put(x, yy, z, "air")
                self.put(x, y + 4, z, "sea_lantern" if e and (x + z) % 2 == 0 else
                         ("smooth_quartz" if e else "light_blue_stained_glass"))
                if not e:
                    self.put(x, y + 1, z, "white_carpet" if (x + z) % 2 else "light_blue_carpet")
        for x, z in ((x1 + 1, z1 + 1), (x2 - 1, z1 + 1)):
            self.put(x, y + 1, z, "potted_flowering_azalea_bush")
        # spire
        for k in range(5, 9):
            self.put(cx, y + k, cz, "quartz_pillar[axis=y]" if k < 8 else "sea_lantern")
        self.put(cx, y + 9, cz, "end_rod[facing=up]")
        self.put(cx, y + 10, cz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        return used

    # -------------------------------------------------------------- 4. ground
    def ground(self):
        bp, L = self.bp, self.L
        p_plant = [.1, .15, .2, .24, .28][L - 1]
        trees = []
        if L >= 4:
            self.hedges()
        for x in range(bp.sx):
            for z in range(bp.sz):
                for y in range(1, bp.sy - 2):
                    if self.n(x, y, z) != "grass_block" or not self.sky(x, y + 1, z):
                        continue
                    if (x, y + 1, z) in self.protect or self.near_sensitive(x, y + 1, z, 1):
                        break
                    deep = all(self.n(x + dx, y, z + dz) == "grass_block" and self.air(x + dx, y + 1, z + dz)
                               for dx in (-1, 0, 1) for dz in (-1, 0, 1))
                    r = h("g", x, z, self.name)
                    if L >= 4 and deep and r > .965 and all(abs(x - tx) + abs(z - tz) > 7 for tx, tz in trees) \
                            and self.tree_fits(x, y + 1, z, 3 + (L == 5)):
                        self.tree(x, y + 1, z, 3 + (L == 5))
                        trees.append((x, z))
                    elif L >= 3 and deep and r < .05 * (L - 2):
                        self.put(x, y + 1, z, FLEAVES if r < .025 * (L - 2) else LEAVES)
                    elif L >= 4 and deep and r < .05 * (L - 2) + .03:
                        self.put(x, y + 1, z, "flowering_azalea" if r < .05 * (L - 2) + .015 else "azalea")
                    elif L == 5 and deep and r > .93 and self.air(x, y + 2, z):
                        tall = ["lilac", "rose_bush", "peony"][int(r * 1000) % 3]
                        self.put(x, y + 1, z, f"{tall}[half=lower]")
                        self.put(x, y + 2, z, f"{tall}[half=upper]")
                    elif h("gp", x, z) < p_plant:
                        rr = h("gk", x, z)
                        if L >= 4 and rr < .15:
                            self.put(x, y + 1, z, f"pink_petals[facing=north,flower_amount={1 + int(rr * 26) % 4}]")
                        else:
                            self.put(x, y + 1, z, "short_grass" if rr < .4 else "fern" if rr < .5 else
                                     FLOWERS[int(rr * 997) % len(FLOWERS)])
                    break

    def hedges(self):
        """Clipped hedge round the lot (gaps at paths), lantern posts on it; flowering at level 5."""
        bp = self.bp
        ring = [(x, z) for x in range(bp.sx) for z in range(bp.sz) if x in (0, bp.sx - 1) or z in (0, bp.sz - 1)]
        for i, (x, z) in enumerate(ring):
            y = next((yy for yy in range(1, min(6, bp.sy - 2)) if self.n(x, yy, z) == "grass_block"
                      and self.sky(x, yy + 1, z)), None)
            if y is None or self.near_sensitive(x, y + 1, z, 1):
                continue
            path_near = any(self.n(x + dx, y, z + dz) not in ("grass_block", "air") and self.air(x + dx, y + 1, z + dz)
                            for dx in range(-2, 3) for dz in range(-2, 3) if bp.inside(x + dx, y, z + dz))
            if path_near or i % 11 >= 8:              # gaps every few blocks so the lot stays open
                continue
            self.put(x, y + 1, z, FLEAVES if self.L == 5 and (x + z) % 3 == 0 else LEAVES)
            if (x + z) % 6 == 0:
                self.put(x, y + 2, z, "lantern[hanging=false,waterlogged=false]")

    # -------------------------------------------------------------- 5. interior
    def interior(self):
        bp, L = self.bp, self.L
        p_pot = [.25, .4, .55, .75, .9][L - 1]
        rug = {2: ("light_gray_carpet", "light_gray_carpet"), 3: ("cyan_carpet", "light_gray_carpet"),
               4: ("light_blue_carpet", "cyan_carpet"), 5: ("white_carpet", "cyan_carpet")}

        def floor_cell(x, y, z):
            return (self.air(x, y, z) and self.air(x, y + 1, z) and self.solid(x, y - 1, z)
                    and self.covered(x, y, z, 8) and "glass" not in self.n(x, y - 1, z))

        cells = [(x, y, z) for x in range(bp.sx) for z in range(bp.sz) for y in range(1, bp.sy - 2)
                 if floor_cell(x, y, z)]
        cellset = set(cells)
        for x, y, z in cells:
            if self.near_sensitive(x, y, z, 1):
                continue
            wx = self.solid(x - 1, y, z) or self.solid(x + 1, y, z)
            wz = self.solid(x, y, z - 1) or self.solid(x, y, z + 1)
            r = h("i", x, y, z, self.name)
            if wx and wz:
                if r < p_pot:
                    self.put(x, y, z, POTS[int(r * 1000) % len(POTS)])
                continue
            if L >= 2 and all((x + dx, y, z + dz) in cellset for dx in (-1, 0, 1) for dz in (-1, 0, 1)):
                border = not all((x + dx, y, z + dz) in cellset for dx in (-2, 0, 2) for dz in (-2, 0, 2))
                inner, edge = rug[L]
                self.put(x, y, z, edge if border else inner)
        # bookshelves along walls, spore blossoms under high ceilings
        if L >= 3:
            for x, y, z in cells:
                if (x, y, z) in self.protect or self.near_sensitive(x, y, z, 1) or not self.air(x, y, z):
                    continue
                walls = [d for d, (dx, dz) in DIRS.items() if self.solid(x + dx, y, z + dz)]
                if len(walls) == 1 and h("bs", x, y, z) < .07 + .02 * (L - 3):
                    away = {"north": "south", "south": "north", "east": "west", "west": "east"}[walls[0]]
                    slots = ",".join(f"slot_{i}_occupied={'true' if h('sl', x, z, i) < .6 else 'false'}" for i in range(6))
                    self.put(x, y, z, f"chiseled_bookshelf[facing={away},{slots}]")
        if L >= 4:
            for x, y, z, s in list(bp.blocks()):
                if self.solid(x, y, z) and all(self.air(x, y - k, z) for k in range(1, 5)) \
                        and self.covered(x, y - 1, z, 1) and h("sb", x, y, z) < .04 \
                        and self.solid_floor_below(x, y - 5, z, 4):
                    self.put(x, y - 1, z, "spore_blossom")
        # counter-top plants and candles
        if L >= 3:
            for x, y, z, s in list(bp.blocks()):
                if "slab" in s and "type=top" in s and self.air(x, y + 1, z) and h("c", x, y, z) < .3 \
                        and self.covered(x, y, z, 6) and not self.near_sensitive(x, y + 1, z, 0):
                    self.put(x, y + 1, z, POTS[int(h("cp", x, z) * 100) % len(POTS)] if h("cc", x, z) < .6 else
                             f"white_candle[candles={1 + int(h('cn', x, z) * 4) % 4},lit=false,waterlogged=false]")
        # pendant lights
        if L >= 4:
            for x, y, z, s in list(bp.blocks()):
                if x % 4 != 2 or z % 4 != 2 or not self.solid(x, y, z):
                    continue
                if all(self.air(x, y - k, z) for k in range(1, 5)) and self.solid_floor_below(x, y - 5, z, 4):
                    if L == 5 and (x + z) % 8 == 4:
                        self.put(x, y - 1, z, "end_rod[facing=down]")
                    else:
                        self.put(x, y - 1, z, "chain[axis=y,waterlogged=false]")
                        self.put(x, y - 2, z, "lantern[hanging=true,waterlogged=false]")

    def solid_floor_below(self, x, y, z, reach):
        for k in range(reach + 1):
            if self.solid(x, y - k, z):
                return True
        return False


# ------------------------------------------------------------------ driver
def kind_and_level(path: Path):
    p = path.as_posix()
    m = re.search(r"(\d+)(?:_furnished|_cutaway)?\.(blueprint|preview)$", path.name)
    lvl = int(m.group(1)) if m else None
    if any(k in p for k in ("/mineshafts/", "/supplies/", "/fields/")):
        return "skip", 0
    if "/parks/" in p:
        return "park", 5
    if "/walls/" in p and "watchtower" not in path.name:
        return "tile", 3
    if "watchtower" in path.name:
        return "building", [3, 3, 5][(lvl or 1) - 1]
    if "/infrastructure/" in p:
        return "tile", 3
    if "gatehouse" in path.name:
        return "building", [2, 3, 5][(lvl or 1) - 1]
    if not lvl or lvl > 5:
        return "skip", 0
    if any(k in path.name for k in ("bunker", "skytowerflat", "barrackstower")):
        return "child", lvl
    return "building", lvl


def process(path_str):
    path = Path(path_str)
    kind, L = kind_and_level(path)
    if kind == "skip":
        return f"{path.name}: skipped"
    bp = load(path)
    if kind == "tile" and any(w in st for *_, st in bp.blocks() for w in CHEAP_FORBIDDEN):
        L = 5                                   # showpiece infrastructure (pier, rail stop, subway entrance)
    d = Detailer(bp, L, path.stem)
    done = []
    d.texture()
    done.append("texture")
    if kind in ("building",):
        if d.guarded(d.facade):
            done.append("facade")
        if d.guarded(d.roof):
            done.append("roof")
    if kind in ("building", "park"):
        if d.guarded(d.ground):
            done.append("ground")
    if kind in ("building", "child"):
        if d.guarded(d.interior):
            done.append("interior")
    if L <= 3 and kind in ("building", "child"):   # cheap hut levels must stay cheap
        for x, y, z, s in bp.blocks():
            assert not any(w in s for w in CHEAP_FORBIDDEN) or (x, y, z) in d.protect or "domum" in s \
                or kind == "park", f"{path.name}: premium block {s} at level {L}"
    bp.save(path)
    return f"{path.name}: L{L} {kind} [{', '.join(done)}] {bp.sx}x{bp.sy}x{bp.sz}"


def main():
    files = []
    for a in sys.argv[1:]:
        p = Path(a)
        files += sorted(p.rglob("*.blueprint")) + sorted(p.rglob("*.preview")) if p.is_dir() else [p]
    with Pool() as pool:
        for line in pool.imap_unordered(process, [str(f) for f in files], chunksize=1):
            print(line)


if __name__ == "__main__":
    main()
