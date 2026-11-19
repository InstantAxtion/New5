"""
Pack-specific architecture: designs every hut from scratch for Hearthwood (cozy modern) and Cascadia
(Oregon / Pacific Northwest), sharing no geometry with Neoterra or with each other.

Only the hut's *requirements* are taken from the raw generator output of the same hut and level:
the hut block (and its block entity / tags), beds, racks, workstations, bookshelves, seats, tagged
spots, outdoor fixtures (beehives, graves, targets) and – for a few huts whose game logic depends on a
precise layout – the functional cluster itself (fishing pond, plantation beds, mine shaft head,
nether portal frame, concrete-mixing basin). Everything else (plan, storeys, walls, windows, roofs,
porches, decks, towers, chimneys, furnishing) is designed here, per pack:

  Cascadia    timber lodges: river-rock base, log posts, vertical spruce siding with dark battens,
              steep A-frame / gambrel / long-gable roofs, covered entries, wrap-around decks,
              fire-lookout tower, river-stone chimney; basalt at level 5.
  Hearthwood  cozy modern homes: brick plinth, white plaster ground floor with wide framed windows,
              timber-clad upper floor, dark gable / hip / shed roofs with deep eaves, front porch,
              brick chimney, glass sunroom, dormers; deepslate roofs at level 5.

Each building gets its own variant (plan shape, roof, wing side, extras) – unique within the pack –
and grows level by level (bigger plan, more storeys, wings, porch/deck, tower).

usage: python archgen.py <raw-pack-dir> <out-pack-dir> <Hearthwood|Cascadia>
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import random
import re
import sys
from multiprocessing import Pool
from pathlib import Path

from nbtlib import tag as NBT

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from blueprint import Blueprint, load, parse_state, format_state, AIR  # noqa: E402
from common import connect_panes  # noqa: E402

STYLE = "Cascadia"
SOLID = "structurize:blocksolidsubstitution"

# ---------------------------------------------------------------------------- requirement extraction
WALL_ITEMS = ("blockminecoloniesrack", "crafting_table", "furnace", "smoker", "blast_furnace", "barrel", "anvil",
              "smithing_table", "stonecutter", "lectern", "cartography_table", "loom", "grindstone", "brewing_stand",
              "cauldron", "composter", "barrel_block", "enchanting_table", "fletching_table", "hopper", "jukebox",
              "ender_chest", "architectscutter", "bookshelf", "chest", "bell")
FLOOR_ITEMS = ("composted_dirt",)
YARD_ITEMS = ("beehive", "bee_nest", "blockminecoloniesnamedgrave", "target")
CLUSTER_TAGS = ("work", "ladder", "cobble", "portal", "vault", "bamboo", "cactus", "sugar", "kelp")
CLUSTER_BUILDINGS = ("fisherman", "plantation", "miner", "netherworker", "concretemixer")
SPOT_TAGS = ("stall", "leisure", "stand_in", "stand_out", "work")
SKIP = ("bunker", "skytower", "barracks", "gatehouse", "wallguardtower")


def nm(s):
    return parse_state(s)[0].split(":", 1)[1]


class Program:
    def __init__(self, bp, name):
        self.bp, self.name = bp, name
        self.base = re.sub(r"\d.*$", "", name)
        self.tags = {}
        self.hut = None
        for p, te in bp.tile_entities.items():
            bdp = te.get("blueprintDataProvider")
            st = bp.get(*p)
            if bdp is not None and ("blockhut" in st or "warehouse" in st or "decorationcontroller" in st
                                    or "quarry" in st or "plantationfield" in st):
                self.hut = (p, st, te)
                for e in bdp.get("posTagMap", []):
                    q = (p[0] + int(e["tagPos"]["x"]), p[1] + int(e["tagPos"]["y"]), p[2] + int(e["tagPos"]["z"]))
                    self.tags.setdefault(q, []).extend(str(t["tagName"]) for t in e["tagNameList"])
        self.gy = next((q[1] for q, n in self.tags.items() if "groundlevel" in n), 1)
        self.items, self.floor_items, self.yard, self.seats, self.yard_seats, self.spots = [], [], [], 0, 0, []
        self.beds = []
        self.racks = []
        self.bookshelves = 0
        self.cluster = set()
        hp = self.hut[0] if self.hut else None
        for x, y, z, s in bp.blocks():
            n = nm(s)
            p = (x, y, z)
            if p == hp:
                continue
            if n.endswith("_bed"):
                if "part=foot" in s:
                    self.beds.append(n)
                continue
            if n == "bookshelf":
                self.bookshelves += 1
                continue
            te = bp.tile_entities.get(p)
            if any(n == k or n.endswith(k) for k in YARD_ITEMS):
                self.yard.append((s, copy.deepcopy(te) if te is not None else None))
            elif any(k == n or n.endswith("_" + k) or n == k for k in FLOOR_ITEMS):
                self.floor_items.append((s, copy.deepcopy(te) if te is not None else None))
            elif n == "blockminecoloniesrack":
                self.racks.append((s, copy.deepcopy(te) if te is not None else None))
            elif any(n == k or n.endswith(k) for k in WALL_ITEMS):
                self.items.append((s, copy.deepcopy(te) if te is not None else None))
        for p, names in self.tags.items():
            if "sit" in names:
                self.seats += 1
            if "sit_out" in names:
                self.yard_seats += 1
            for t in names:
                if t in SPOT_TAGS and self.base not in CLUSTER_BUILDINGS:
                    self.spots.append(t)
        if self.base in CLUSTER_BUILDINGS:
            self.cluster = self._cluster()

    def _cluster(self):
        """Cells of the functional layout that must be kept as-is (pond, crop beds, shaft head, portal, basin)."""
        bp = self.bp
        core = {q for q, n in self.tags.items() if any(t in CLUSTER_TAGS for t in n)}
        for x, y, z, s in bp.blocks():
            n = nm(s)
            if n in ("water", "obsidian", "crying_obsidian") or (self.base == "miner" and n in ("ladder", "cobblestone")):
                core.add((x, y, z))
        if not core:
            return set()
        self.cluster_cells = {(x + dx, z + dz) for x, _, z in core for dx in (-1, 0, 1) for dz in (-1, 0, 1)}
        xs = [p[0] for p in self.cluster_cells]
        zs = [p[1] for p in self.cluster_cells]
        return (min(xs), max(xs), min(zs), max(zs))


# ---------------------------------------------------------------------------- pack design vocabulary
MATS = {
    "Cascadia": dict(
        base=["cobblestone", "mossy_cobblestone", "cobblestone"], base5=["smooth_basalt", "polished_basalt[axis=y]", "mossy_cobblestone"],
        post="dark_oak_log[axis=y]", beam_x="dark_oak_log[axis=x]", beam_z="dark_oak_log[axis=z]",
        wall="spruce_planks", batten="stripped_spruce_log[axis=y]", wall2="spruce_planks",
        frame="stripped_dark_oak_log[axis=y]", glass="glass_pane", floor="spruce_planks", floor2="stripped_spruce_log[axis=x]",
        roof="spruce", roof5="dark_oak", ridge="dark_oak_planks", deck="spruce_planks", rail="spruce_fence",
        chimney=["cobblestone", "mossy_cobblestone"], door="spruce_door", light="lantern",
        rug=["brown_carpet", "green_carpet"], accent=["red_terracotta", "green_terracotta", "brown_terracotta"]),
    "Hearthwood": dict(
        base=["bricks"], base5=["bricks", "polished_deepslate"],
        post="stripped_dark_oak_log[axis=y]", beam_x="stripped_dark_oak_log[axis=x]", beam_z="stripped_dark_oak_log[axis=z]",
        wall="white_terracotta", batten="white_terracotta", wall2="birch_planks",
        frame="dark_oak_planks", glass="glass_pane", floor="oak_planks", floor2="oak_planks",
        roof="dark_oak", roof5="deepslate_tile", ridge="dark_oak_planks", deck="oak_planks", rail="dark_oak_fence",
        chimney=["bricks"], door="dark_oak_door", light="lantern",
        rug=["orange_carpet", "white_carpet", "brown_carpet"], accent=["orange_terracotta", "brown_terracotta", "yellow_terracotta"]),
}
# per-building material variants (wall, batten/upper cladding, post/trim) and roof / base options
SIDINGS = {
    "Cascadia": [("spruce_planks", "stripped_spruce_log[axis=y]", "dark_oak_log[axis=y]"),
                 ("dark_oak_planks", "stripped_dark_oak_log[axis=y]", "spruce_log[axis=y]"),
                 ("stripped_spruce_log[axis=y]", "dark_oak_planks", "dark_oak_log[axis=y]"),
                 ("mangrove_planks", "stripped_mangrove_log[axis=y]", "dark_oak_log[axis=y]"),
                 ("birch_planks", "stripped_birch_log[axis=y]", "spruce_log[axis=y]"),
                 ("red_terracotta", "stripped_birch_log[axis=y]", "dark_oak_log[axis=y]"),
                 ("oak_planks", "stripped_oak_log[axis=y]", "spruce_log[axis=y]")],
    "Hearthwood": [("white_terracotta", "birch_planks", "dark_oak_planks"),
                   ("light_gray_terracotta", "oak_planks", "dark_oak_planks"),
                   ("white_terracotta", "spruce_planks", "stripped_spruce_log[axis=y]"),
                   ("bricks", "white_terracotta", "dark_oak_planks"),
                   ("pink_terracotta", "birch_planks", "stripped_birch_log[axis=y]"),
                   ("yellow_terracotta", "oak_planks", "spruce_planks"),
                   ("white_terracotta", "dark_oak_planks", "dark_oak_planks"),
                   ("light_blue_terracotta", "birch_planks", "white_terracotta")],
}
ROOFMATS = {"Cascadia": ["spruce", "dark_oak", "mangrove", "spruce"], "Hearthwood": ["dark_oak", "spruce", "brick", "mud_brick"]}
BASES = {"Cascadia": [["cobblestone", "mossy_cobblestone"], ["stone_bricks", "mossy_stone_bricks"], ["andesite", "cobblestone"],
                      ["tuff", "cobblestone"]],
         "Hearthwood": [["bricks"], ["stone_bricks"], ["mud_bricks"], ["polished_andesite", "stone_bricks"]]}
FUNC_EXTRA = {
    "Cascadia": {"farmer": "silo", "composter": "silo", "chickenherder": "silo", "cowboy": "silo", "sawmill": "water_wheel",
                 "lumberjack": "water_wheel", "fletcher": "water_wheel", "baker": "stone_chimney", "cook": "stone_chimney",
                 "cookery": "stone_chimney", "smeltery": "stone_chimney", "blacksmith": "stone_chimney",
                 "stonesmeltery": "stone_chimney", "townhall": "cupola", "school": "cupola", "library": "cupola",
                 "university": "cupola", "hospital": "covered_entry", "guardtower": "lookout", "archery": "lookout"},
    "Hearthwood": {"baker": "brick_chimney", "cook": "brick_chimney", "cookery": "brick_chimney", "smeltery": "brick_chimney",
                   "blacksmith": "brick_chimney", "stonesmeltery": "brick_chimney", "townhall": "cupola", "school": "cupola",
                   "library": "cupola", "university": "cupola", "florist": "sunroom", "composter": "sunroom",
                   "alchemist": "sunroom", "dyer": "awning", "fletcher": "awning", "glassblower": "awning",
                   "mechanic": "awning", "deliveryman": "awning", "farmer": "silo", "hospital": "porch"},
}

PLANS = {
    "Cascadia": ["longhall", "aframe", "lodge_L", "barn", "longhall_T"],
    "Hearthwood": ["box", "house_L", "split", "house_T", "box_wide"],
}
ROOFS = {
    "Cascadia": ["aframe", "gambrel", "gable_steep"],
    "Hearthwood": ["gable", "hip", "shed"],
}
EXTRAS = {
    "Cascadia": ["lookout", "stone_chimney", "deck", "covered_entry", "loft_dormer"],
    "Hearthwood": ["porch", "brick_chimney", "sunroom", "dormers", "balcony"],
}


def h(*a):
    return int.from_bytes(hashlib.md5(repr(a).encode()).digest()[:4], "little") / 2 ** 32


_VARIANTS = {}


def variant(style, base):
    """Unique (plan, roof, wing side, extras order) per building within the pack."""
    key = (style, base)
    if key in _VARIANTS:
        return _VARIANTS[key]
    taken = {v for (s, _), v in _VARIANTS.items() if s == style}
    rng = random.Random(f"{style}|{base}")
    for _ in range(500):
        v = (rng.choice(PLANS[style]), rng.choice(ROOFS[style]), rng.choice(("east", "west")),
             tuple(rng.sample(EXTRAS[style], 3)), rng.randint(0, 2), rng.randrange(len(SIDINGS[style])),
             rng.randrange(len(ROOFMATS[style])), rng.randrange(len(BASES[style])), rng.randint(0, 2))
        if v[:2] + v[5:8] not in {t[:2] + t[5:8] for t in taken}:
            break
    _VARIANTS[key] = v
    return v


# ---------------------------------------------------------------------------- the builder
class Arch:
    FH = 4                                                       # floor-to-floor height

    def __init__(self, prog: Program, level: int, style: str):
        self.P, self.L, self.style = prog, level, style
        self.M = dict(MATS[style])
        self.top = level >= 5
        (self.plan, self.roof, self.wing_side, self.extras, self.prop, si, ri, bi, self.win) = variant(style, prog.base)
        wall, batten, post = SIDINGS[style][si]
        self.M.update(wall=wall, batten=batten, post=post if "[" in post or post.endswith("planks") else post)
        if style == "Hearthwood":
            self.M.update(wall2=batten, frame=post)
        self.M["roof"] = ROOFMATS[style][ri]
        self.M["base"] = BASES[style][bi]
        fx = FUNC_EXTRA[style].get(prog.base)
        if fx:
            self.extras = (fx,) + tuple(e for e in self.extras if e != fx)[:2]
        self.gy = 1

    # ---- sizing ---------------------------------------------------------
    def needs(self):
        P = self.P
        shelf_cells = math.ceil(P.bookshelves / 3)
        wall = len(P.items) + shelf_cells + len(P.floor_items) + 1 + math.ceil(len(P.racks) / 3)
        beds = len(P.beds)
        seats = P.seats
        spots = len(P.spots)
        return wall, beds, seats, spots

    def floors(self):
        f = {1: 1, 2: 1, 3: 2, 4: 2, 5: 3}[self.L]
        if self.style == "Cascadia" and self.plan in ("aframe", "barn"):
            f = min(f, 2)
        return f

    def volumes(self, scale):
        """Volumes as (x1, x2, z1, z2, floors, roof) in a local frame; the first one is the main hall."""
        W = 9 + 2 * scale + self.prop * 2 + (self.L - 1)
        D = 7 + 2 * scale + (self.L - 1)
        if self.plan in ("longhall", "barn", "box_wide"):
            W += 4
        nf = self.floors()
        if nf >= 2:
            W = max(W, 13)
        vols = [(0, W - 1, 0, D - 1, nf, self.roof)]
        if self.L >= 3 and self.plan in ("lodge_L", "house_L", "longhall_T", "house_T", "split"):
            ww, dd = max(7, D - 2), 7 + self.L
            if self.plan in ("lodge_L", "house_L"):
                x1 = W if self.wing_side == "east" else -ww
                vols.append((x1, x1 + ww - 1, 0, dd - 1, max(1, nf - 1), self.roof))
            elif self.plan in ("longhall_T", "house_T"):
                mid = W // 2
                vols.append((mid - ww // 2, mid - ww // 2 + ww - 1, D, D + dd - 1, max(1, nf - 1), self.roof))
            else:  # split: offset volume, other roof
                x1 = W - 3 if self.wing_side == "east" else -ww + 3
                vols.append((x1, x1 + ww - 1, D - 2, D - 2 + dd, nf, "shed" if self.style == "Hearthwood" else "gable_steep"))
        return vols

    # ---- block helpers --------------------------------------------------
    def S(self, x, y, z, s, te=None, force=False):
        bp = self.bp
        if not bp.inside(x, y, z):
            return
        if not force and (x, y, z) in self.locked:
            return
        bp.set(x, y, z, s if ":" in s else "minecraft:" + s, te)

    def pick(self, lst, *k):
        return lst[int(h(self.P.base, *k) * len(lst)) % len(lst)]

    def stairs(self, facing, half="bottom"):
        mat = self.M["roof5"] if self.top else self.M["roof"]
        return f"{mat}_stairs[facing={facing},half={half},shape=straight,waterlogged=false]"

    # ---- build ------------------------------------------------------------
    def build(self):
        import walkcheck
        for scale in range(0, 16):
            res = self._try(scale)
            if res is not None and not walkcheck.analyse(res)[1]:
                return res
        raise RuntimeError(f"{self.P.name}: requirements do not fit")

    def _try(self, scale):
        vols = self.volumes(scale)
        P = self.P
        # local frame -> blueprint frame: margin for porch/deck/tower/yard
        minx = min(v[0] for v in vols)
        minz = min(v[2] for v in vols)
        maxx = max(v[1] for v in vols)
        maxz = max(v[3] for v in vols)
        m = 4
        yard_d = 0
        if P.yard or P.yard_seats or self.P.base in ("chickenherder", "cowboy", "shepherd", "swineherder", "rabbithutch",
                                                     "graveyard", "archery", "beekeeper", "mysticalsite"):
            yard_d = 8 + len(P.yard) // 4
        cl = P.cluster if P.cluster else None
        cw = cd = 0
        if cl:
            cw, cd = cl[1] - cl[0] + 1, cl[3] - cl[2] + 1
        ox, oz = m - minx, m - minz
        sx = maxx - minx + 1 + 2 * m + max(0, cw - (maxx - minx + 1)) if cl else maxx - minx + 1 + 2 * m
        sz = maxz - minz + 1 + 2 * m + yard_d + (cd + 2 if cl else 0)
        nf = max(v[4] for v in vols)
        sy = self.gy + nf * self.FH + 22
        self.bp = Blueprint(sx, sy, sz, f"{P.name}.blueprint")
        self.locked = set()
        self.tags = {}
        self.vols = [(v[0] + ox, v[1] + ox, v[2] + oz, v[3] + oz, v[4], v[5]) for v in vols]
        self.front_z = min(v[2] for v in self.vols)      # front is north (low z)
        self.ground()
        for i, v in enumerate(self.vols):
            self.shell(v, main=(i == 0))
        self.connect_volumes()
        self.entrance()
        self.stair_core()
        if not self.furnish():
            return None
        yard_z = max(v[3] for v in self.vols) + 3
        if cl:
            self.copy_cluster(cl, ox_c=m, oz_c=yard_z)
            yard_z += cd + 2
        if yard_d:
            self.yard(yard_z, yard_d)
        for i, v in enumerate(self.vols):
            self.roof_on(v)
        self.exteriors()
        self.lights()
        connect_panes(self.bp)
        self.finish()
        return self.bp

    # ---- ground / shell ---------------------------------------------------
    def ground(self):
        bp, M = self.bp, self.M
        apron = M["base5"] if self.top else M["base"]
        for x in range(bp.sx):
            for z in range(bp.sz):
                bp.set(x, 0, z, SOLID)
                if self.style == "Cascadia":
                    s = ["gravel", "coarse_dirt", "cobblestone", "mossy_cobblestone"][int(h("ap", x // 2, z // 2) * 4)]
                    s = s if s not in ("gravel",) else "cobblestone"
                else:
                    s = "stone_bricks" if (x + z) % 4 else "polished_andesite"
                bp.set(x, self.gy, z, "minecraft:" + s)

    def floor_y(self, f):
        return self.gy + f * self.FH

    def shell(self, v, main):
        x1, x2, z1, z2, nf, _ = v
        M = self.M
        base = M["base5"] if self.top else M["base"]
        for f in range(nf):
            fy = self.floor_y(f)
            for x in range(x1, x2 + 1):
                for z in range(z1, z2 + 1):
                    edge = x in (x1, x2) or z in (z1, z2)
                    corner = x in (x1, x2) and z in (z1, z2)
                    # floor
                    if not edge:
                        fl = M["floor2"] if z % 4 == 0 else M["floor"]
                        self.S(x, fy, z, fl if f or True else fl)
                    else:
                        self.S(x, fy, z, self.pick(base, x, z) if f == 0 else M["beam_x"] if z in (z1, z2) else M["beam_z"])
                    for k in range(1, self.FH):
                        y = fy + k
                        if not edge:
                            self.S(x, y, z, AIR)
                            continue
                        along = (x - x1) if z in (z1, z2) else (z - z1)
                        if corner:
                            s = M["post"]
                        elif f == 0 and k == 1 and self.style == "Cascadia":
                            s = self.pick(base, x, y, z)                       # river-rock knee wall
                        elif k == 2 and ((self.win == 0 and along % 3 != 0) or (self.win == 1 and along % 4 != 0)
                                         or (self.win == 2 and along % 2 == 1)):
                            s = M["glass"]
                        elif k == 3 and self.win == 2 and along % 2 == 1:
                            s = M["glass"]
                        elif k == 3 and along % 3 != 0 and (self.style == "Hearthwood" and f == 0):
                            s = M["glass"]                                     # tall ground-floor windows
                        elif along % 3 == 0:
                            s = M["frame"] if self.style == "Hearthwood" else M["batten"]
                        else:
                            s = (M["wall"] if (self.style == "Cascadia" or f == 0) else M["wall2"])
                        self.S(x, y, z, s)
            # ceiling / next floor slab
        fy = self.floor_y(nf)
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                edge = x in (x1, x2) or z in (z1, z2)
                self.S(x, fy, z, (M["beam_x"] if z in (z1, z2) else M["beam_z"]) if edge else M["floor"])

    def connect_volumes(self):
        main = self.vols[0]
        for v in self.vols[1:]:
            # shared wall: find overlapping span and open a 2-high doorway on each floor in common
            nf = min(main[4], v[4])
            for f in range(nf):
                y = self.floor_y(f) + 1
                if v[0] > main[1] - 1 or v[1] < main[0] + 1:          # side by side in x
                    xw = main[1] if v[0] >= main[1] else main[0]
                    xv = v[0] if v[0] >= main[1] else v[1]
                    zc = (max(main[2], v[2]) + min(main[3], v[3])) // 2
                    for x in range(min(xw, xv), max(xw, xv) + 1):
                        for yy in (y, y + 1):
                            self.S(x, yy, zc, AIR, force=True)
                        self.S(x, y - 1, zc, self.M["floor"], force=True)
                        self.locked |= {(x, y, zc), (x, y + 1, zc)}
                else:
                    zw = main[3] if v[2] >= main[3] else main[2]
                    zv = v[2] if v[2] >= main[3] else v[3]
                    xc = (max(main[0], v[0]) + min(main[1], v[1])) // 2
                    for z in range(min(zw, zv), max(zw, zv) + 1):
                        for yy in (y, y + 1):
                            self.S(xc, yy, z, AIR, force=True)
                        self.S(xc, y - 1, z, self.M["floor"], force=True)
                        self.locked |= {(xc, y, z), (xc, y + 1, z)}

    def entrance(self):
        x1, x2, z1, z2, nf, _ = self.vols[0]
        self.door_x = (x1 + x2) // 2
        y = self.gy + 1
        d = self.M["door"]
        self.S(self.door_x, y, z1, f"{d}[facing=south,half=lower,hinge=left,open=false,powered=false]", force=True)
        self.S(self.door_x, y + 1, z1, f"{d}[facing=south,half=upper,hinge=left,open=false,powered=false]", force=True)
        for dz in (1, 2):
            for yy in (y, y + 1):
                self.locked.add((self.door_x, yy, z1 + dz))
        self.locked |= {(self.door_x, y, z1 - 1), (self.door_x, y + 1, z1 - 1)}
        # entry step / path
        for z in range(0, z1):
            self.S(self.door_x, self.gy, z, "spruce_planks" if self.style == "Cascadia" else "bricks", force=True)

    def stair_core(self):
        """Straight stair along the back wall of the main volume, one flight per floor."""
        x1, x2, z1, z2, nf, _ = self.vols[0]
        self.stair_cells = set()
        if nf < 2:
            return
        zs = z2 - 1
        for f in range(nf - 1):
            fy = self.floor_y(f)
            x0 = x1 + 1 if f % 2 == 0 else x2 - 1
            dx = 1 if f % 2 == 0 else -1
            facing = "east" if dx == 1 else "west"
            for i in range(self.FH):
                x = x0 + dx * i
                y = fy + 1 + i
                for yy in range(fy + 1, y):
                    self.S(x, yy, zs, self.M["floor"], force=True)
                self.S(x, y, zs, self.stairs(facing).replace(self.M["roof5"] if self.top else self.M["roof"], self.M["roof"]),
                       force=True)
                if i < self.FH - 1:
                    self.S(x, self.floor_y(f + 1), zs, AIR, force=True)   # opening in the slab above
                for yy in range(y + 1, y + 3):
                    self.S(x, yy, zs, AIR, force=True)
                self.stair_cells |= {(x, yy, zs) for yy in range(fy + 1, fy + self.FH + 3)}
                self.stair_cells |= {(x, yy, zs - 1) for yy in range(fy + 1, fy + self.FH + 3)}
                # guard rail beside the opening
                if i < self.FH - 1 and (x, self.floor_y(f + 1) + 1, zs - 1) not in self.locked:
                    self.S(x, self.floor_y(f + 1) + 1, zs - 1, self.M["rail"] + "[east=false,north=false,south=false,waterlogged=false,west=false]", force=True)
            x_land = x0 + dx * self.FH
            self.locked |= {(x_land, self.floor_y(f + 1) + k, zs) for k in (1, 2)}
            self.locked |= {(x_land, self.floor_y(f + 1) + k, zs - 1) for k in (1, 2)}
        self.locked |= self.stair_cells

    # ---- furnishing -------------------------------------------------------
    def wall_cells(self):
        """Interior cells along walls, per floor, in a stable order: (x, y, z, inward_dx, inward_dz)."""
        out = []
        for v in self.vols:
            x1, x2, z1, z2, nf, _ = v
            for f in range(nf):
                y = self.floor_y(f) + 1
                ring = []
                for x in range(x1 + 2, x2 - 1):                 # corners stay free so nothing gets boxed in
                    ring.append((x, y, z1 + 1, 0, 1))
                    ring.append((x, y, z2 - 1, 0, -1))
                for z in range(z1 + 2, z2 - 1):
                    ring.append((x1 + 1, y, z, 1, 0))
                    ring.append((x2 - 1, y, z, -1, 0))
                for c in ring:
                    x, y_, z, dx, dz = c
                    if (x, y_, z) in self.locked or (x, y_ + 1, z) in self.locked:
                        continue
                    if not self.air(x, y_, z) or not self.air(x, y_ + 1, z):
                        continue
                    # keep doorways clear: no item right in front of an opening
                    if any(self.air(x - dx + ax, y_, z - dz + az) and self.air(x - dx + ax, y_ + 1, z - dz + az)
                           and (ax, az) == (0, 0) for ax, az in ((0, 0),)):
                        continue
                    out.append(c)
        return out

    def air(self, x, y, z):
        return self.bp.inside(x, y, z) and self.bp.get(x, y, z) == AIR

    def furnish(self):
        P, bp = self.P, self.bp
        cells = self.wall_cells()
        used = set()

        def take(n_need, cond=lambda c: True):
            for c in cells:
                if c[:3] in used or not cond(c):
                    continue
                x, y, z, dx, dz = c
                if any((x + a, y, z + b) in used for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))) and n_need == "spaced":
                    continue
                used.add(c[:3])
                return c
            return None

        # hut block: ground floor, near the entrance
        hut_c = take(1, lambda c: c[1] == self.gy + 1)
        if hut_c is None:
            return False
        self.hut_pos = hut_c[:3]
        # beds: need the next cell inward free
        for color in P.beds:
            c = take("spaced", lambda c: self.air(c[0] + c[3], c[1], c[2] + c[4])
                     and (c[0] + c[3], c[1], c[2] + c[4]) not in self.locked)
            if c is None:
                return False
            x, y, z, dx, dz = c
            facing = {(0, 1): "north", (0, -1): "south", (1, 0): "west", (-1, 0): "east"}[(dx, dz)]
            # head against the wall, foot inward
            bp.set(x, y, z, f"minecraft:{color}[facing={facing},occupied=false,part=head]")
            bp.set(x + dx, y, z + dz, f"minecraft:{color}[facing={facing},occupied=false,part=foot]")
            self.locked |= {(x, y, z), (x + dx, y, z + dz)}
            used.add((x + dx, y, z + dz))
        # wall items
        for s, te in P.items:
            c = take(1)
            if c is None:
                return False
            x, y, z, dx, dz = c
            name, props = parse_state(s)
            if "facing" in props and props["facing"] in ("north", "south", "east", "west"):
                props = dict(props)
                n = name.split(":")[1]
                inward = {(0, 1): "south", (0, -1): "north", (1, 0): "east", (-1, 0): "west"}[(dx, dz)]
                props["facing"] = inward
                s = format_state(name, props)
            bp.set(x, y, z, s, te)
            self.locked.add((x, y, z))
        # racks: stacks of three along the walls, then free-standing rack aisles in the open floor
        racks = list(P.racks)
        while racks:
            c = take(1)
            if c is None:
                break
            x, y, z, dx, dz = c
            facing = {(0, 1): "south", (0, -1): "north", (1, 0): "east", (-1, 0): "west"}[(dx, dz)]
            for k in range(3):
                if not racks:
                    break
                s, te = racks.pop()
                name, props = parse_state(s)
                props = dict(props)
                props["facing"] = facing
                bp.set(x, y + k, z, format_state(name, props), te)
                self.locked.add((x, y + k, z))
        if racks:
            for x, y, z in self.open_cells():
                if not racks:
                    break
                if x % 3 == 0 or (x, y, z) in self.locked:          # every third column stays an aisle
                    continue
                for k in range(3):
                    if not racks or not self.air(x, y + k, z):
                        break
                    s, te = racks.pop()
                    bp.set(x, y + k, z, s, te)
                    self.locked.add((x, y + k, z))
        if racks:
            return False
        # bookshelves: stacks of three
        left = P.bookshelves
        while left > 0:
            c = take(1)
            if c is None:
                return False
            x, y, z, _, _ = c
            for k in range(min(3, left)):
                bp.set(x, y + k, z, "minecraft:bookshelf")
                self.locked.add((x, y + k, z))
            left -= 3
        # floor items (composted dirt): replace the floor block, keep air above
        for s, te in P.floor_items:
            c = take(1)
            if c is None:
                return False
            x, y, z, _, _ = c
            bp.set(x, y - 1, z, s, te)
            self.locked |= {(x, y - 1, z), (x, y, z)}
        # seats: rows in the open floor (benches facing the main wall)
        self.sit = []
        need = P.seats
        if need:
            free = self.open_cells()
            for x, y, z in free:
                if need <= 0:
                    break
                if (x + z) % 2 or z % 3 == 0:
                    continue
                bp.set(x, y, z, f"minecraft:{self.M['roof']}_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]")
                self.locked.add((x, y, z))
                self.tags.setdefault((x, y, z), []).append("sit")
                need -= 1
            if need > 0:
                return False
        # spot tags (work / stall / leisure / stand): open floor cells
        free = [c for c in self.open_cells() if c not in self.locked]
        for i, t in enumerate(P.spots):
            if i >= len(free):
                return False
            x, y, z = free[i * 2 % max(1, len(free))]
            self.tags.setdefault((x, y - 1, z), []).append(t)
        return True

    def open_cells(self):
        out = []
        for v in self.vols:
            x1, x2, z1, z2, nf, _ = v
            for f in range(nf):
                y = self.floor_y(f) + 1
                for z in range(z1 + 3, z2 - 2):
                    for x in range(x1 + 3, x2 - 2):
                        if (x, y, z) in self.locked or (x, y + 1, z) in self.locked:
                            continue
                        if self.air(x, y, z) and self.air(x, y + 1, z) and self.air(x, y + 2, z):
                            out.append((x, y, z))
        return out

    # ---- clusters / yard ----------------------------------------------------
    def copy_cluster(self, cl, ox_c, oz_c):
        src = self.P.bp
        x1, x2, z1, z2 = cl
        dx, dz = ox_c - x1, oz_c - z1
        sgy = self.P.gy
        cells = self.P.cluster_cells
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                if (x, z) not in cells:
                    continue
                for y in range(0, src.sy):
                    ty = y - sgy + self.gy
                    if not self.bp.inside(x + dx, ty, z + dz) or ty < 0:
                        continue
                    s = src.get(x, y, z)
                    if s == AIR and y <= sgy:
                        continue
                    te = src.tile_entities.get((x, y, z))
                    self.bp.set(x + dx, ty, z + dz, s, copy.deepcopy(te) if te is not None else None)
                    self.locked.add((x + dx, ty, z + dz))
        for (x, y, z), names in self.P.tags.items():
            if x1 <= x <= x2 and z1 <= z <= z2:
                for t in names:
                    if t in CLUSTER_TAGS:
                        self.tags.setdefault((x + dx, y - sgy + self.gy, z + dz), []).append(t)

    def yard(self, z0, depth):
        """Fenced yard behind the building: hives / graves / targets / pens / outdoor seats."""
        bp, M = self.bp, self.M
        x1, x2 = 2, bp.sx - 3
        z2 = min(bp.sz - 2, z0 + depth)
        gate_x = (x1 + x2) // 2
        for x in range(x1, x2 + 1):
            for z in range(z0, z2 + 1):
                edge = x in (x1, x2) or z in (z0, z2)
                bp.set(x, self.gy, z, "minecraft:" + ("grass_block[snowy=false]" if self.P.base in (
                    "chickenherder", "cowboy", "shepherd", "swineherder", "rabbithutch", "beekeeper", "graveyard") else
                    ("coarse_dirt" if self.style == "Cascadia" else "stone_bricks")))
                if edge:
                    if x == gate_x and z == z0:
                        self.S(x, self.gy + 1, z, f"{M['rail'].replace('fence', 'fence_gate')}[facing=north,in_wall=false,open=false,powered=false]")
                    else:
                        self.S(x, self.gy + 1, z, M["rail"] + "[east=false,north=false,south=false,waterlogged=false,west=false]")
        # path from the building to the yard gate
        for z in range(max(v[3] for v in self.vols) + 1, z0):
            self.S(gate_x, self.gy, z, M["deck"], force=True)
        # back door of the main volume onto the path
        mv = self.vols[0]
        if mv[0] < gate_x < mv[1]:
            for yy in (self.gy + 1, self.gy + 2):
                if (gate_x, yy, mv[3]) not in self.locked:
                    self.S(gate_x, yy, mv[3], AIR, force=True)
        spots = [(x, z) for z in range(z0 + 2, z2 - 1, 2) for x in range(x1 + 2, x2 - 1, 2) if x != gate_x]
        i = 0
        for s, te in self.P.yard:
            if i >= len(spots):
                break
            x, z = spots[i]
            i += 1
            n = nm(s)
            if "beehive" in n or "bee_nest" in n:
                self.S(x, self.gy + 1, z, M["post"])
                self.S(x, self.gy + 2, z, s, te)
                self.S(x + 1, self.gy + 1, z, "cornflower")
            else:
                self.S(x, self.gy + 1, z, s, te)
        for k in range(self.P.yard_seats):
            if i >= len(spots):
                break
            x, z = spots[i]
            i += 1
            self.S(x, self.gy + 1, z, f"{M['roof']}_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]")
            self.tags.setdefault((x, self.gy + 1, z), []).append("sit_out")
        if self.P.base in ("chickenherder", "cowboy", "shepherd", "swineherder", "rabbithutch"):
            for x in range(x1 + 2, x2 - 1, 5):
                self.S(x, self.gy + 1, z2 - 1, "hay_block[axis=y]")

    # ---- roofs --------------------------------------------------------------
    def roof_on(self, v):
        x1, x2, z1, z2, nf, form = v
        y0 = self.floor_y(nf)
        M = self.M
        ridge = M["ridge"]
        ov = 1
        X1, X2, Z1, Z2 = x1 - ov, x2 + ov, z1 - ov, z2 + ov
        along_x = (x2 - x1) >= (z2 - z1)
        span = (Z2 - Z1 + 1) if along_x else (X2 - X1 + 1)

        def prof(i):
            if form == "aframe":
                return 2 * i
            if form == "gambrel":
                return 2 * i if i < 3 else 6 + (i - 3) // 1
            if form == "gable_steep":
                return int(1.5 * i)
            if form == "shed":
                return i // 2
            return i                                                           # gable / hip

        if form == "hip":
            for i in range(0, min(X2 - X1, Z2 - Z1) // 2 + 1):
                for x in range(X1 + i, X2 - i + 1):
                    for z in range(Z1 + i, Z2 - i + 1):
                        ring = x in (X1 + i, X2 - i) or z in (Z1 + i, Z2 - i)
                        if not ring:
                            continue
                        if x == X1 + i:
                            f = "east"
                        elif x == X2 - i:
                            f = "west"
                        elif z == Z1 + i:
                            f = "south"
                        else:
                            f = "north"
                        self.S(x, y0 + 1 + i, z, self.stairs(f))
                last = i
            return
        for u in range((X1 if along_x else Z1), (X2 if along_x else Z2) + 1):
            end = u in ((x1, x2) if along_x else (z1, z2))
            for j in range(span):
                if form == "shed":
                    hgt = prof(j)
                    prev = prof(j - 1) if j else -1
                    face = "south" if along_x else "east"
                else:
                    i = min(j, span - 1 - j)
                    hgt = prof(i)
                    prev = prof(i - 1) if i else -1
                    first = j < span - 1 - j
                    face = (("south" if first else "north") if along_x else ("east" if first else "west"))
                    if j == span - 1 - j:
                        face = None
                w = (Z1 if along_x else X1) + j
                x, z = (u, w) if along_x else (w, u)
                for k in range(min(prev + 1, hgt), hgt + 1):
                    if k == hgt:
                        self.S(x, y0 + 1 + k, z, self.stairs(face) if face else ridge)
                    else:
                        self.S(x, y0 + 1 + k, z, ridge if form != "aframe" else self.stairs(face, "top") if face else ridge)
                if end:                                        # gable end wall with a window
                    inside = (Z1 + 1 <= w <= Z2 - 1) if along_x else (X1 + 1 <= w <= X2 - 1)
                    if inside and (x1 <= x <= x2 and z1 <= z <= z2):
                        for k in range(0, hgt + 1):
                            if (x, y0 + 1 + k, z) in self.locked:
                                continue
                            if self.bp.get(x, y0 + 1 + k, z) == AIR:
                                s = M["glass"] if (k in (1, 2) and abs(j - span // 2) <= 1) else (M["batten"] if j % 2 else M["wall2"])
                                self.S(x, y0 + 1 + k, z, s)

    # ---- pack extras --------------------------------------------------------
    def exteriors(self):
        L = self.L
        extras = list(self.extras)
        if L >= 2:
            self.extra(extras[0])
        if L >= 3:
            self.extra(extras[1])
        if L >= 4:
            self.extra(extras[2])
        if L >= 5:
            self.extra("lookout" if self.style == "Cascadia" else "sunroom")

    def extra(self, kind):
        x1, x2, z1, z2, nf, _ = self.vols[0]
        M = self.M
        gy = self.gy
        if kind in ("porch", "covered_entry", "deck"):
            depth = 3 if kind != "deck" else 2
            xa, xb = (self.door_x - 3, self.door_x + 3) if kind != "deck" else (x1, x2)
            for x in range(xa, xb + 1):
                for d in range(1, depth + 1):
                    z = z1 - d
                    self.S(x, gy, z, M["deck"])
                    if kind == "deck" and d == depth and x != self.door_x:
                        self.S(x, gy + 1, z, M["rail"] + "[east=false,north=false,south=false,waterlogged=false,west=false]")
            if kind != "deck":
                for x in (xa, xb):
                    for y in range(gy + 1, gy + 4):
                        self.S(x, y, z1 - depth, M["post"])
                for x in range(xa - 1, xb + 2):
                    for d in range(0, depth + 1):
                        f = "south" if self.style == "Hearthwood" else "north"
                        self.S(x, gy + 4, z1 - d, self.stairs("south") if d == depth else M["ridge"])
                self.S(self.door_x, gy + 3, z1 - 1, "lantern[hanging=true,waterlogged=false]")
        elif kind in ("brick_chimney", "stone_chimney"):
            mat = M["chimney"]
            x = x1 - 1 if self.wing_side == "east" else x2 + 1
            z = (z1 + z2) // 2
            top = self.floor_y(nf) + 7
            for y in range(gy + 1, top):
                for dz in (0, 1):
                    self.S(x, y, z + dz, self.pick(mat, x, y, z + dz))
            self.S(x, top, z, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        elif kind == "sunroom":
            xa = x1 - 6 if self.wing_side == "east" else x2 + 1
            xb = xa + 5
            za, zb = z1 + 1, min(z2 - 1, z1 + 6)
            for x in range(xa, xb + 1):
                for z in range(za, zb + 1):
                    e = x in (xa, xb) or z in (za, zb)
                    self.S(x, gy, z, M["floor"])
                    for y in range(gy + 1, gy + 4):
                        corner = x in (xa, xb) and z in (za, zb)
                        self.S(x, y, z, M["post"] if corner else ("glass" if e else AIR))
                    self.S(x, gy + 4, z, "glass" if not e else M["ridge"])
            wall_x = x1 if self.wing_side == "east" else x2
            zc = (za + zb) // 2
            for y in (gy + 1, gy + 2):
                if (wall_x, y, zc) not in self.locked:
                    self.S(wall_x, y, zc, AIR, force=True)
                self.S(xa if self.wing_side == "east" else xb, y, zc, AIR, force=True)
        elif kind in ("dormers", "loft_dormer", "balcony"):
            y = self.floor_y(nf) + 1
            for x in range(x1 + 2, x2 - 1, 4):
                for k in range(3):
                    self.S(x, y + k, z1, "glass" if k < 2 else M["ridge"], force=False)
                self.S(x, y + 2, z1 - 1, self.stairs("north"))
        elif kind == "silo":
            cx = x2 + 4 if self.wing_side == "west" else x1 - 4
            cz = (z1 + z2) // 2
            H = self.floor_y(nf) + 6
            for y in range(gy + 1, H + 1):
                for x in range(cx - 2, cx + 3):
                    for z in range(cz - 2, cz + 3):
                        d = math.hypot(x - cx, z - cz)
                        if 1.5 <= d < 2.5:
                            self.S(x, y, z, (M["accent"][0] if (y // 3) % 2 else M["wall"]) if self.style == "Cascadia"
                                   else ("white_terracotta" if (y // 4) % 2 else "light_gray_terracotta"))
            for k in range(3):
                for x in range(cx - 2 + k, cx + 3 - k):
                    for z in range(cz - 2 + k, cz + 3 - k):
                        if math.hypot(x - cx, z - cz) < 2.6 - k:
                            self.S(x, H + 1 + k, z, M["ridge"])
            self.S(cx, H + 4, cz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        elif kind == "water_wheel":
            wx = x1 - 2 if self.wing_side == "east" else x2 + 2
            cz, cy = (z1 + z2) // 2, gy + 4
            for z in range(cz - 3, cz + 4):
                for y in range(cy - 3, cy + 4):
                    d = math.hypot(z - cz, y - cy)
                    if 2.5 <= d < 3.5 or (z == cz or y == cy) and d < 3:
                        if y > gy:
                            self.S(wx, y, z, M["beam_z"] if z != cz else M["post"])
            self.S(wx + (1 if wx < x1 else -1), cy, cz, M["post"].replace("axis=y", "axis=x"))
            for z in range(cz - 3, cz + 4):                       # mill race below the wheel
                self.S(wx, gy, z, "water[level=0]")
                self.S(wx, gy - 1 if gy > 0 else gy, z, "cobblestone")
        elif kind == "cupola":
            cx, cz = (x1 + x2) // 2, (z1 + z2) // 2
            base = max((y for y in range(self.bp.sy) if self.bp.get(cx, y, cz) != AIR), default=self.floor_y(nf))
            for x in range(cx - 1, cx + 2):
                for z in range(cz - 1, cz + 2):
                    corner = x != cx and z != cz
                    for y in range(base + 1, base + 4):
                        self.S(x, y, z, M["post"] if corner else ("glass" if (x, z) != (cx, cz) else AIR))
                    self.S(x, base + 4, z, M["ridge"])
            self.S(cx, base + 3, cz, "bell[attachment=ceiling,facing=north,powered=false]")
            for x, z, f in ((cx, cz - 1, "south"), (cx, cz + 1, "north"), (cx - 1, cz, "east"), (cx + 1, cz, "west")):
                self.S(x, base + 5, z, self.stairs(f))
            self.S(cx, base + 5, cz, M["ridge"])
            self.S(cx, base + 6, cz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        elif kind == "awning":
            for x in range(x1 + 1, x2):
                if abs(x - self.door_x) <= 1:
                    continue
                for d, y in ((1, gy + 4), (2, gy + 3)):
                    self.S(x, y, z1 - d, "red_wool" if x % 2 else "white_wool")
        elif kind == "lookout":
            tx = x2 + 2 if self.wing_side == "east" else x1 - 4
            tz = z1
            H = self.floor_y(nf) + 4
            for x, z in ((tx, tz), (tx + 2, tz), (tx, tz + 2), (tx + 2, tz + 2)):
                for y in range(gy + 1, H + 1):
                    self.S(x, y, z, M["post"])
            for y in range(gy + 1, H + 1):
                self.S(tx + 1, y, tz + 1, "ladder[facing=north,waterlogged=false]")
                self.S(tx + 1, y, tz + 2, M["post"])
            for x in range(tx - 1, tx + 4):
                for z in range(tz - 1, tz + 4):
                    self.S(x, H + 1, z, M["deck"])
                    if x in (tx - 1, tx + 3) or z in (tz - 1, tz + 3):
                        self.S(x, H + 2, z, M["rail"] + "[east=false,north=false,south=false,waterlogged=false,west=false]")
            self.S(tx + 1, H + 1, tz + 1, "ladder[facing=north,waterlogged=false]", force=True)
            for i in range(3):
                for x in range(tx - 1 + i, tx + 4 - i):
                    for z in range(tz - 1 + i, tz + 4 - i):
                        if x in (tx - 1 + i, tx + 3 - i) or z in (tz - 1 + i, tz + 3 - i):
                            self.S(x, H + 4 + i, z, M["ridge"])
            for x, z in ((tx - 1, tz - 1), (tx + 3, tz - 1), (tx - 1, tz + 3), (tx + 3, tz + 3)):
                self.S(x, H + 3, z, M["post"])

    def lights(self):
        for v in self.vols:
            x1, x2, z1, z2, nf, _ = v
            for f in range(nf):
                yc = self.floor_y(f + 1) - 1
                for x in range(x1 + 2, x2 - 1, 4):
                    for z in range(z1 + 2, z2 - 1, 4):
                        if self.air(x, yc, z) and self.air(x, yc - 1, z) and (x, yc, z) not in self.locked:
                            self.S(x, yc, z, "lantern[hanging=true,waterlogged=false]")
                # rugs
                y = self.floor_y(f) + 1
                for z in range((z1 + z2) // 2 - 1, (z1 + z2) // 2 + 2):
                    for x in range(x1 + 3, x2 - 2):
                        if self.air(x, y, z) and (x, y, z) not in self.locked and self.air(x, y + 1, z):
                            self.S(x, y, z, self.pick(self.M["rug"], x // 3, f))

    # ---- anchor ---------------------------------------------------------------
    def finish(self):
        bp, P = self.bp, self.P
        hp, st, te = P.hut
        te = copy.deepcopy(te)
        hx, hy, hz = self.hut_pos
        tags = {(0, self.gy, 0): ["groundlevel"], self.hut_pos: [self.style.lower()]}
        for q, names in P.tags.items():
            if q == hp and "invisible" in names:
                tags[self.hut_pos].append("invisible")
        for q, names in self.tags.items():
            tags.setdefault(q, []).extend(names)

        def pos(x, y, z):
            return NBT.Compound({"x": NBT.Int(x), "y": NBT.Int(y), "z": NBT.Int(z)})
        bdp = te["blueprintDataProvider"]
        bdp["corner1"] = pos(-hx, -hy, -hz)
        bdp["corner2"] = pos(bp.sx - 1 - hx, bp.sy - 1 - hy, bp.sz - 1 - hz)
        bdp["posTagMap"] = NBT.List[NBT.Compound]([
            NBT.Compound({"tagPos": pos(x - hx, y - hy, z - hz),
                          "tagNameList": NBT.List[NBT.Compound]([NBT.Compound({"tagName": NBT.String(n)}) for n in ns])})
            for (x, y, z), ns in sorted(tags.items())])
        if "pack" in te:
            te["pack"] = NBT.String(self.style)
        if "pack" in bdp:
            bdp["pack"] = NBT.String(self.style)
        name, props = parse_state(st)
        if "facing" in props:
            props = dict(props)
            props["facing"] = "north"
        bp.set(hx, hy, hz, format_state(name, props), te)
        bp.primary_offset = (hx, hy, hz)
        bp.architects = [self.style]
        bp.name = f"{P.name}.blueprint"
        # trim unused height
        top = max((y for y in range(bp.sy) if any(c != AIR for row in bp.grid[y] for c in row)), default=0)
        cut = bp.sy - (top + 2)
        if cut > 0:
            bp.grid = bp.grid[:top + 2]
            bp.sy = top + 2
            bdp["corner2"]["y"] = NBT.Int(bp.sy - 1 - hy)


# ---------------------------------------------------------------------------- driver
def eligible(path: Path):
    p = path.as_posix()
    m = re.search(r"(\d+)\.blueprint$", path.name)
    if not m or any(k in p for k in ("/mineshafts/", "/supplies/", "/fields/", "/walls/", "/infrastructure/", "/parks/")):
        return None
    if any(path.name.startswith(k) for k in SKIP):
        return None
    lvl = int(m.group(1))
    return lvl if 1 <= lvl <= 5 else None


def process(args):
    global STYLE
    src, dst, STYLE = Path(args[0]), Path(args[1]), args[2]
    L = eligible(src)
    if not L:
        return None
    raw = load(src)
    prog = Program(raw, src.stem)
    if prog.hut is None:
        return f"{src.name}: no hut, skipped"
    bp = Arch(prog, L, STYLE).build()
    dst.parent.mkdir(parents=True, exist_ok=True)
    bp.save(dst)
    return f"{src.name}: {bp.sx}x{bp.sy}x{bp.sz}"


def main():
    src, dst, style = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    jobs = [(str(f), str(dst / f.relative_to(src)), style) for f in sorted(src.rglob("*.blueprint"))]
    with Pool() as pool:
        for line in pool.imap_unordered(process, jobs, chunksize=1):
            if line:
                print(line)


if __name__ == "__main__":
    main()
