"""
Hand-design toolkit for MineColonies huts (vanilla blocks only).

Every hut type is designed by hand in designs/*.py: one function per type that draws the building for a given pack
and level with the helpers below. The toolkit only takes care of the bookkeeping:

  * the hut's game requirements (requirements.json, per pack-relative path): beds, racks, work blocks, seats ("sit"
    tags), work spots, bookshelves, outdoor fixtures and – for fisherman / plantation / miner / nether worker /
    concrete mixer – the functional cluster (pond, crop beds, shaft, portal, basin), copied with cluster();
  * the hut block entity (path, corners, tags) and the ground-level tag;
  * pane / fence / wall connections (set after drawing);
  * a final check that every requirement was placed (Design.finish raises otherwise).

Coordinates: x east, y up, z south. The street / entrance side is NORTH (z = 0). The ground surface is at y = gy
(default 1); floors stand on it, so the first walkable layer is gy + 1.

Facing conventions (vanilla):
  stairs  facing = side of the tall back.        roof stairs face UP-slope (toward the ridge)
  chair   back   = side the backrest is on       (a chair south of a table has back="south")
  bed     facing = from foot toward head         (head against a wall: facing toward that wall)
  wall sign / wall torch / ladder: facing = direction it faces, away from the supporting block
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from nbtlib import tag as T

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))
sys.path.insert(0, str(HERE.parent))
from blueprint import Blueprint, load, parse_state, format_state, AIR  # noqa: E402
from common import connect_panes, rack_te, RACK_STATE  # noqa: E402

SOLID = "structurize:blocksolidsubstitution"
KEEP = "structurize:blocksubstitution"
REQ = json.loads((HERE / "requirements.json").read_text())
D4 = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}
CW = {"north": "east", "east": "south", "south": "west", "west": "north"}

# restyling of the decorative blocks inside functional clusters (snapshots come from the Neoterra pack)
CLUSTER_SKIN = {
    "Hearthwood": {"white_concrete": "stone_bricks", "light_gray_concrete": "mossy_stone_bricks",
                   "gray_concrete": "dark_oak_log[axis=y]", "cyan_concrete": "dark_oak_planks",
                   "smooth_stone": "oak_planks", "polished_andesite": "stone_bricks",
                   "quartz_pillar": "stripped_dark_oak_log[axis=y]", "smooth_quartz": "calcite",
                   "light_gray_concrete_framed": "dark_oak_planks", "birch_door": "dark_oak_door",
                   "light_blue_stained_glass_pane": "glass_pane"},
    "Cascadia": {"white_concrete": "cobblestone", "light_gray_concrete": "mossy_cobblestone",
                 "gray_concrete": "spruce_log[axis=y]", "cyan_concrete": "spruce_planks",
                 "smooth_stone": "spruce_planks", "polished_andesite": "andesite",
                 "quartz_pillar": "spruce_log[axis=y]", "smooth_quartz": "stripped_spruce_log[axis=y]",
                 "birch_door": "spruce_door", "light_blue_stained_glass_pane": "glass_pane"},
}


def _skin(pack, state):
    m = CLUSTER_SKIN.get(pack)
    if not m:
        return state
    name, props = parse_state(state)
    n = name.split(":")[1]
    new = m.get(n)
    if new is None:
        return state
    if "[" in new or n.endswith("_door") is False:
        if n.endswith("_door"):
            return format_state(_mc(new), props)
        return _mc(new)
    return format_state(_mc(new), props)


# premium (expensive / late-game) materials: capped on levels 1-3 by preview.py
PREMIUM = ("quartz", "copper", "prismarine", "sea_lantern", "blackstone", "nether_brick", "end_rod", "amethyst",
           "glazed_terracotta", "purpur", "end_stone", "crying_obsidian", "froglight", "gold_block", "iron_block",
           "diamond_block", "emerald_block", "beacon", "lapis_block", "redstone_lamp",
           "tinted_glass", "shroomlight", "gilded", "netherite", "lodestone", "respawn_anchor", "conduit")
PREMIUM_CAP = {1: 0.10, 2: 0.15, 3: 0.20}


def premium_share(bp, gy):
    total = prem = 0
    for x, y, z, st in bp.blocks():
        if y == gy or st == AIR or "substitution" in st:
            continue
        total += 1
        n = st.split("[")[0].split(":")[-1]
        if any(k in n for k in PREMIUM):
            prem += 1
    return prem / total if total else 0.0


# --------------------------------------------------------------------------------------------- pack palettes
# Starting vocabularies; a design may use any vanilla block it likes.
PALETTES = {
    # Farmworks: practical farm buildings – stone-brick plinths, spruce framing, cobble and glass
    "Farmworks": dict(
        wood="spruce", wood2="oak", log="stripped_spruce_log", plank="spruce_planks",
        wall="stone_bricks", wall2="cobblestone", trim="spruce_planks", base="stone_bricks",
        accent="green_terracotta", floor="smooth_stone", floor2="spruce_planks", glass="glass_pane",
        glass2="glass_pane", roof="spruce_planks", roofslab="spruce_slab", roofstairs="spruce_stairs",
        path="gravel", light="lantern", lamp="lantern",
        rug=("green_carpet", "brown_carpet"), plant="potted_fern", fire="campfire",
        hearth="stone_bricks", counter="spruce_slab", bed="green",
    ),
    # modern / near-future: white concrete & quartz, big glazing, flat roofs & terraces, cyan accents
    "Neoterra": dict(
        wood="birch", wood2="mangrove", log="stripped_birch_log", plank="birch_planks",
        wall="white_concrete", wall2="light_gray_concrete", trim="smooth_quartz", base="polished_andesite",
        accent="cyan_terracotta", floor="smooth_stone", floor2="polished_diorite", glass="glass_pane",
        glass2="light_gray_stained_glass_pane", roof="smooth_quartz", roofslab="smooth_quartz_slab",
        roofstairs="smooth_quartz_stairs", path="smooth_stone", light="sea_lantern", lamp="lantern",
        rug=("cyan_carpet", "light_gray_carpet"), plant="potted_bamboo", fire="soul_campfire",
        hearth="polished_blackstone_bricks", counter="smooth_quartz_slab", bed="cyan",
    ),
    # English village / Tudor: brick plinth, white plaster with dark-oak framing, steep tiled gables, chimneys
    "Hearthwood": dict(
        wood="dark_oak", wood2="oak", log="stripped_dark_oak_log", plank="oak_planks",
        wall="calcite", wall2="bricks", trim="dark_oak_planks", base="stone_bricks",
        accent="red_terracotta", floor="oak_planks", floor2="spruce_planks", glass="glass_pane",
        glass2="glass_pane", roof="deepslate_tiles", roofslab="deepslate_tile_slab",
        roofstairs="deepslate_tile_stairs", path="gravel", light="lantern", lamp="lantern",
        rug=("red_carpet", "orange_carpet"), plant="potted_red_tulip", fire="campfire",
        hearth="bricks", counter="dark_oak_slab", bed="red",
    ),
    # Pacific Northwest: river-rock footing, spruce logs & board-and-batten, steep spruce roofs, porches, moss
    "Cascadia": dict(
        wood="spruce", wood2="dark_oak", log="spruce_log", plank="spruce_planks",
        wall="spruce_planks", wall2="stripped_spruce_log", trim="dark_oak_planks", base="cobblestone",
        accent="mossy_cobblestone", floor="spruce_planks", floor2="stripped_spruce_wood", glass="glass_pane",
        glass2="glass_pane", roof="spruce_planks", roofslab="spruce_slab", roofstairs="spruce_stairs",
        path="coarse_dirt", light="lantern", lamp="lantern",
        rug=("brown_carpet", "green_carpet"), plant="potted_fern", fire="campfire",
        hearth="cobblestone", counter="spruce_slab", bed="brown",
    ),
}


def _mc(s: str) -> str:
    return s if ":" in s else "minecraft:" + s


class RequirementError(RuntimeError):
    pass


class Design:
    def __init__(self, pack: str, rel: str, size: tuple[int, int, int], gy: int = 1, ground: str | None = None,
                 paving: str | None = None):
        """size = (sx, sy, sz). Fills below gy with earth substitution and y = gy with `paving` (default: pack path)."""
        self.pack, self.rel = pack, rel
        self.req = REQ[rel]
        self.level = self.req["level"]
        self.P = PALETTES[pack]
        sx, sy, sz = size
        self.bp = Blueprint(sx, sy, sz, Path(rel).name)
        self.gy = gy
        self.tags: dict[tuple[int, int, int], list[str]] = {}
        self.hut_pos = None
        self.child_positions = []
        self.is_child = bool(self.req.get("child"))
        self.placed = {"beds": 0, "racks": 0, "items": {}, "floor_items": 0, "yard": {}, "seats": 0, "spots": {},
                       "bookshelves": 0, "cluster": False}
        pave = paving or self.P["path"]
        if gy >= 1:
            self.fill(0, 0, 0, sx - 1, gy - 1, sz - 1, ground or SOLID)
        self.fill(0, gy, 0, sx - 1, gy, sz - 1, pave)

    # ------------------------------------------------------------------------------------------- variety
    def vary(self, options, salt=""):
        """Pick one of `options` per building type (stable across levels, different between types), so a town in
        one pack mixes roof colours, wall materials and trims instead of repeating one palette."""
        import hashlib
        base = self.req.get("base", "")
        h = int(hashlib.md5(f"{self.pack}:{base}:{salt}".encode()).hexdigest()[:8], 16)
        return options[h % len(options)]

    # ------------------------------------------------------------------------------------------- basics
    @property
    def sx(self):
        return self.bp.sx

    @property
    def sy(self):
        return self.bp.sy

    @property
    def sz(self):
        return self.bp.sz

    def set(self, x, y, z, block, te=None):
        if not self.bp.inside(x, y, z):
            raise IndexError(f"{self.rel} [{self.pack}]: ({x},{y},{z}) outside {self.sx}x{self.sy}x{self.sz}")
        self.bp.set(x, y, z, _mc(block) if block != AIR else AIR, te)

    def get(self, x, y, z):
        return self.bp.get(x, y, z)

    def air(self, x, y, z):
        return self.bp.get(x, y, z) == AIR

    def fill(self, x1, y1, z1, x2, y2, z2, block):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            for z in range(min(z1, z2), max(z1, z2) + 1):
                for x in range(min(x1, x2), max(x1, x2) + 1):
                    self.set(x, y, z, block)

    def clear(self, x1, y1, z1, x2, y2, z2):
        self.fill(x1, y1, z1, x2, y2, z2, AIR)

    def box(self, x1, y1, z1, x2, y2, z2, wall, floor=None, ceiling=None):
        """Hollow box: walls on the four sides from y1 to y2, optional floor at y1-1 / ceiling at y2+1, inside air."""
        for y in range(y1, y2 + 1):
            for z in range(z1, z2 + 1):
                for x in range(x1, x2 + 1):
                    edge = x in (x1, x2) or z in (z1, z2)
                    self.set(x, y, z, wall if edge else AIR)
        if floor:
            self.fill(x1, y1 - 1, z1, x2, y1 - 1, z2, floor)
        if ceiling:
            self.fill(x1, y2 + 1, z1, x2, y2 + 1, z2, ceiling)

    def frame(self, x1, y1, z1, x2, y2, z2, post, beam=None):
        """Timber frame on an existing wall rectangle: posts at corners (+ every 4), beam along the top (y2)."""
        for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
            for y in range(y1, y2 + 1):
                self.set(x, y, z, post)
        if beam:
            for x in range(x1, x2 + 1):
                for z in (z1, z2):
                    self.set(x, y2, z, f"{beam}[axis=x]")
            for z in range(z1, z2 + 1):
                for x in (x1, x2):
                    self.set(x, y2, z, f"{beam}[axis=z]")

    def layer(self, y, x0, z0, rows: list[str], legend: dict[str, str]):
        """Stamp an ASCII plan: rows run north->south, characters west->east. ' ' leaves the cell as it is,
        '.' sets air, any other character is looked up in `legend`."""
        for dz, row in enumerate(rows):
            for dx, ch in enumerate(row):
                if ch == " ":
                    continue
                self.set(x0 + dx, y, z0 + dz, AIR if ch == "." else legend[ch])

    # ------------------------------------------------------------------------------------------- openings
    def door(self, x, y, z, facing="north", wood=None, hinge="left"):
        wood = wood or self.P["wood"]
        for half, yy in (("lower", y), ("upper", y + 1)):
            self.set(x, yy, z, f"{wood}_door[facing={facing},half={half},hinge={hinge},open=false,powered=false]")

    def double_door(self, x, y, z, along="x", facing="north", wood=None):
        """Two doors at (x,z) and the next cell along `along`."""
        dx, dz = (1, 0) if along == "x" else (0, 1)
        self.door(x, y, z, facing, wood, "left")
        self.door(x + dx, y, z + dz, facing, wood, "right")

    def window(self, x1, y1, z1, x2, y2, z2, glass=None):
        self.fill(x1, y1, z1, x2, y2, z2, glass or self.P["glass"])

    # ------------------------------------------------------------------------------------------- roofs
    def gable(self, x1, z1, x2, z2, y, axis="x", stairs=None, ridge=None, end=None, overhang=1, under=None):
        """Gable roof over the wall rectangle x1..x2 / z1..z2 whose wall tops are at y-1.
        axis = direction of the ridge. Eave stairs sit at y on the wall line, overhang rows step down below.
        end = block that closes the gable triangles at both ends (default: the pack wall).
        under = optional block placed under every roof stair inside the walls (solid ceiling look)."""
        stairs = stairs or self.P["roofstairs"]
        ridge = ridge or self.P["roofslab"]
        end = end or self.P["wall"]
        o = overhang
        if axis == "x":
            lo, hi, a1, a2 = z1, z2, x1, x2
        else:
            lo, hi, a1, a2 = x1, x2, z1, z2
        L, H = lo - o, hi + o
        n = H - L + 1
        for i in range(n):
            w = L + i
            k = min(i, n - 1 - i)
            yy = y + k - o
            mid = (n % 2 == 1 and i == n // 2)
            if axis == "x":
                face = "south" if i < n / 2 else "north"
            else:
                face = "east" if i < n / 2 else "west"
            for a in range(a1 - o, a2 + o + 1):
                x, z = (a, w) if axis == "x" else (w, a)
                if mid:
                    st = ridge if "slab" not in ridge else f"{ridge}[type=bottom,waterlogged=false]"
                else:
                    st = f"{stairs}[facing={face},half=bottom,shape=straight,waterlogged=false]"
                if self.bp.inside(x, yy, z):
                    self.set(x, yy, z, st)
                if under and lo <= w <= hi and a1 <= a <= a2 and not mid and yy - 1 >= y:
                    self.set(x, yy - 1, z, f"{stairs}[facing={OPP[face]},half=top,shape=straight,waterlogged=false]")
            # gable triangles
            if lo <= w <= hi:
                for a in (a1, a2):
                    x, z = (a, w) if axis == "x" else (w, a)
                    for yy2 in range(y, yy):
                        if self.air(x, yy2, z):
                            self.set(x, yy2, z, end)
        return y + (n - 1) // 2 - o                                      # ridge height

    def hip(self, x1, z1, x2, z2, y, stairs=None, cap=None, overhang=1):
        """Hip roof: rings of stairs climbing inward, capped with full blocks / slabs."""
        stairs = stairs or self.P["roofstairs"]
        cap = cap or self.P["roofslab"]
        X1, Z1, X2, Z2 = x1 - overhang, z1 - overhang, x2 + overhang, z2 + overhang
        i = 0
        while X1 + i <= X2 - i and Z1 + i <= Z2 - i:
            a1, a2, b1, b2 = X1 + i, X2 - i, Z1 + i, Z2 - i
            yy = y + i - overhang
            for x in range(a1, a2 + 1):
                for z in range(b1, b2 + 1):
                    if not (x in (a1, a2) or z in (b1, b2)):
                        continue
                    if a2 - a1 < 2 or b2 - b1 < 2:
                        st = cap if "slab" not in cap else f"{cap}[type=bottom,waterlogged=false]"
                    else:
                        if z == b1:
                            f = "south"
                        elif z == b2:
                            f = "north"
                        elif x == a1:
                            f = "east"
                        else:
                            f = "west"
                        shape = "straight"
                        if (x in (a1, a2)) and (z in (b1, b2)):
                            shape = "outer_left" if (x == a1) == (z == b1) else "outer_right"
                            f = "south" if z == b1 else "north"
                        st = f"{stairs}[facing={f},half=bottom,shape={shape},waterlogged=false]"
                    self.set(x, yy, z, st)
            i += 1
        return y + i - 1 - overhang

    def flat(self, x1, z1, x2, z2, y, slab=None, parapet=None, coping=None):
        """Flat roof deck at y over the rectangle, with an optional parapet (1 high) and coping slabs on it."""
        self.fill(x1, y, z1, x2, y, z2, slab or self.P["roof"])
        if parapet:
            for x in range(x1, x2 + 1):
                for z in range(z1, z2 + 1):
                    if x in (x1, x2) or z in (z1, z2):
                        self.set(x, y + 1, z, parapet)
                        if coping:
                            self.set(x, y + 2, z, f"{coping}[type=bottom,waterlogged=false]")

    # ------------------------------------------------------------------------------------------- furniture
    def chair(self, x, y, z, back, wood=None, sit=True, arms=False):
        """Stairs seat; `back` = side of the backrest. sit=True adds the MineColonies 'sit' tag."""
        wood = wood or self.P["wood"]
        self.set(x, y, z, f"{wood}_stairs[facing={back},half=bottom,shape=straight,waterlogged=false]")
        if arms:
            for side in (CW[back], OPP[CW[back]]):
                dx, dz = D4[side]
                if self.air(x + dx, y, z + dz):
                    self.set(x + dx, y, z + dz,
                             f"{wood}_trapdoor[facing={side},half=bottom,open=true,powered=false,waterlogged=false]")
        if sit:
            self.tag(x, y, z, "sit")
            self.placed["seats"] += 1

    def table(self, x, y, z, wood=None, kind="post", top=None):
        """kind 'post': fence + pressure plate; 'slab': top slab; 'block': any full `top` block."""
        wood = wood or self.P["wood"]
        if kind == "post":
            self.set(x, y, z, f"{wood}_fence[east=false,north=false,south=false,waterlogged=false,west=false]")
            self.set(x, y + 1, z, top or f"{wood}_pressure_plate[powered=false]")
        elif kind == "slab":
            self.set(x, y, z, f"{top or wood + '_slab'}[type=top,waterlogged=false]")
        else:
            self.set(x, y, z, top)

    def dining(self, x, y, z, length=1, along="x", wood=None, chairs=("n", "s", "e", "w"), sit=True, kind="post"):
        """Table of `length` cells starting at (x,z) along `along`, chairs around it on the given sides."""
        dx, dz = (1, 0) if along == "x" else (0, 1)
        cells = [(x + dx * i, z + dz * i) for i in range(length)]
        for cx, cz in cells:
            self.table(cx, y, cz, wood, kind)
        side = {"n": "north", "s": "south", "e": "east", "w": "west"}
        for c in chairs:
            d = side[c]
            ox, oz = D4[d]
            if along == "x" and d in ("north", "south") or along == "z" and d in ("east", "west"):
                for cx, cz in cells:
                    self.chair(cx + ox, y, cz + oz, d, wood, sit)
            else:
                cx, cz = cells[0] if d in ("west", "north") else cells[-1]
                self.chair(cx + ox, y, cz + oz, d, wood, sit)

    def seating(self, x1, z1, x2, z2, y, need, wood=None, kind="post", rug=None, step=4):
        """Fill the free floor area x1..x2/z1..z2 (inclusive) with 4-chair tables on a `step` grid (table in the
        middle of a 3x3 group, aisles between groups) until `need` seats are placed. Returns seats placed.
        Cells that are not air (or have no floor) are skipped, so draw fixed furniture first."""
        placed = 0
        for tz in range(z1 + 1, z2, step):
            for tx in range(x1 + 1, x2, step):
                if placed >= need:
                    return placed
                cells = [(tx + a, tz + b) for a in (-1, 0, 1) for b in (-1, 0, 1)]
                if not all(x1 <= cx <= x2 and z1 <= cz <= z2 and self.air(cx, y, cz) and self.air(cx, y + 1, cz)
                           and self.get(cx, y - 1, cz) != AIR for cx, cz in cells):
                    continue
                if rug:
                    self.rug(tx - 1, tz - 1, tx + 1, tz + 1, y, rug, "plain")
                    for cx, cz in cells:
                        if (cx, cz) != (tx, tz) and abs(cx - tx) + abs(cz - tz) == 1:
                            continue
                self.set(tx, y, tz, AIR)
                self.table(tx, y, tz, wood, kind)
                for side, (dx, dz) in D4.items():
                    if placed >= need:
                        break
                    self.set(tx + dx, y, tz + dz, AIR)
                    self.chair(tx + dx, y, tz + dz, side, wood)
                    placed += 1
        return placed

    def bed(self, x, y, z, facing, color=None):
        """Bed with its HEAD at (x,z); the foot is one cell opposite to `facing`."""
        color = color or self.P["bed"]
        fx, fz = D4[OPP[facing]]
        self.set(x, y, z, f"{color}_bed[facing={facing},occupied=false,part=head]")
        self.set(x + fx, y, z + fz, f"{color}_bed[facing={facing},occupied=false,part=foot]")
        self.placed["beds"] += 1

    def rack(self, x, y, z, facing="north"):
        self.set(x, y, z, RACK_STATE.format(facing=facing), rack_te())
        self.placed["racks"] += 1

    def item(self, x, y, z, block, facing=None):
        """A work block (crafting_table, furnace, anvil, barrel, ...). Counted against the hut's requirements."""
        name = block.split("[")[0]
        st = block
        if "[" not in block:
            st = _default_state(name, facing)
        self.set(x, y, z, st)
        key = _mc(name)
        self.placed["items"][key] = self.placed["items"].get(key, 0) + 1

    def yard_item(self, x, y, z, block, te=None):
        """Outdoor fixture (beehive, grave, target): counted against the hut's yard requirements."""
        name = block.split("[")[0]
        self.set(x, y, z, block if "[" in block else _default_state(name, None), te)
        key = _mc(name)
        self.placed["yard"][key] = self.placed["yard"].get(key, 0) + 1

    def grave(self, x, y, z, facing="south", name="Unknown Citizen"):
        """MineColonies named grave (graveyard yard requirement)."""
        te = T.Compound({"id": T.String("minecolonies:namedgrave"), "Item": T.String(""),
                         "content": T.List[T.String]([T.String(name)])})
        self.yard_item(x, y, z, f"minecolonies:blockminecoloniesnamedgrave[facing={facing}]", te)

    def floor_item(self, x, y, z, block="minecolonies:composted_dirt"):
        self.set(x, y, z, block)
        self.placed["floor_items"] += 1

    def bookshelf(self, x, y, z, h=1):
        for k in range(h):
            self.set(x, y + k, z, "bookshelf")
            self.placed["bookshelves"] += 1

    def keg(self, x, y, z, facing="north"):
        """Decorative cask: a barrel lying on its side (not counted as a work barrel)."""
        self.set(x, y, z, f"barrel[facing={facing},open=false]")

    def counter(self, x1, z1, x2, z2, y, top=None, body=None):
        """Bar / shop counter: a solid body (default: pack planks) under a top slab one higher is not possible in one
        block, so the counter is the body block with an upside-down slab look: body at y, nothing above."""
        top = top or self.P["counter"]
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for z in range(min(z1, z2), max(z1, z2) + 1):
                self.set(x, y, z, body or f"{top}[type=top,waterlogged=false]")

    def hearth(self, x, y, z, facing, top, frame=None, fire=None, width=3):
        """Fireplace against a wall: `facing` = direction it opens to (into the room); (x,z) = fire cell.
        Frame on both sides and above, chimney flue up to `top` (exclusive) behind/above the fire."""
        frame = frame or self.P["hearth"]
        fire = fire or self.P["fire"]
        sx, sz = D4[CW[facing]]
        half = width // 2
        for k in range(-half, half + 1):
            cx, cz = x + sx * k, z + sz * k
            if k == 0:
                self.set(cx, y, cz, f"{fire}[facing={facing},lit=true,signal_fire=false,waterlogged=false]")
            else:
                self.set(cx, y, cz, frame)
            self.set(cx, y + 1, cz, frame)
        for yy in range(y + 2, top):
            self.set(x, yy, z, frame)

    def lamp(self, x, y, z, kind=None, hanging=True):
        kind = kind or self.P["lamp"]
        if kind in ("lantern", "soul_lantern"):
            self.set(x, y, z, f"{kind}[hanging={'true' if hanging else 'false'},waterlogged=false]")
        else:
            self.set(x, y, z, kind)

    def wall_torch(self, x, y, z, facing):
        self.set(x, y, z, f"wall_torch[facing={facing}]")

    def plant(self, x, y, z, kind=None):
        self.set(x, y, z, kind or self.P["plant"])

    def candle(self, x, y, z, n=1, color=""):
        c = f"{color}_candle" if color else "candle"
        self.set(x, y, z, f"{c}[candles={n},lit=false,waterlogged=false]")

    def rug(self, x1, z1, x2, z2, y, colors=None, pattern="border"):
        """Carpet rug; pattern 'border' (edge colour 0, centre colour 1), 'check' or 'plain'."""
        c = colors or self.P["rug"]
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for z in range(min(z1, z2), max(z1, z2) + 1):
                if not self.air(x, y, z):
                    continue
                if pattern == "plain":
                    k = 0
                elif pattern == "check":
                    k = (x + z) % 2
                else:
                    k = 0 if x in (x1, x2) or z in (z1, z2) else 1
                self.set(x, y, z, c[k % len(c)])

    def sign(self, x, y, z, facing, lines, wood=None, hanging=False, glow=False, color="black"):
        """Wall sign (or wall hanging sign) with text. For a wall sign the supporting block is opposite `facing`;
        a wall hanging sign hangs from a bracket on the block on its left/right (sideways to `facing`)."""
        wood = wood or self.P["wood"]
        msgs = [json.dumps({"text": t}) for t in (list(lines) + ["", "", "", ""])[:4]]
        side = T.Compound({"messages": T.List[T.String]([T.String(m) for m in msgs]), "color": T.String(color),
                           "has_glowing_text": T.Byte(1 if glow else 0)})
        te = T.Compound({"id": T.String("minecraft:hanging_sign" if hanging else "minecraft:sign"),
                         "front_text": side, "back_text": T.Compound(dict(side)), "is_waxed": T.Byte(1)})
        st = f"{wood}_wall_hanging_sign[facing={facing},waterlogged=false]" if hanging else \
            f"{wood}_wall_sign[facing={facing},waterlogged=false]"
        self.set(x, y, z, st, te)

    def banner(self, x, y, z, facing, color="red"):
        self.set(x, y, z, f"{color}_wall_banner[facing={facing}]")

    def flowerbox(self, x1, z1, x2, z2, y, flowers=("poppy", "dandelion", "azure_bluet", "oxeye_daisy")):
        """Window box: trapdoor-faced planter of grass/dirt with flowers on top is two blocks; here: a row of
        flowering azalea / flowers in pots for the sill."""
        i = 0
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for z in range(min(z1, z2), max(z1, z2) + 1):
                self.set(x, y, z, "potted_" + flowers[i % len(flowers)])
                i += 1

    # ------------------------------------------------------------------------------------------- game bits
    # ------------------------------------------------------------------------------------------- child huts
    def reserve(self, x1, y1, z1, x2, y2, z2):
        """Space a child hut's blueprint will be built into: Structurize keeps these cells as they are."""
        self.fill(x1, y1, z1, x2, y2, z2, KEEP)

    def child_hut(self, x, y, z, path, facing="north"):
        """Place a child hut (barracks tower, sky-tower flat, bunker room, twin-builder annex, wonder wing).
        `path` is the child's level-0 path from requirements (e.g. 'military/barrackstower0.blueprint'); the child
        blueprint of the same level is pasted so that ITS hut block lands on (x,y,z)."""
        spec = next((c for c in self.req.get("children", []) if c["path"] == path), None)
        if spec is None:
            raise RequirementError(f"{self.rel}: no child '{path}' in requirements")

        def pos(a, b, c):
            return T.Compound({"x": T.Int(a), "y": T.Int(b), "z": T.Int(c)})
        name = Path(path).stem
        te = T.Compound({
            "id": T.String("minecolonies:colonybuilding"), "mirror": T.Byte(0), "inWarehouse": T.Byte(0),
            "colony": T.Int(0), "type": T.String("minecraft:"), "version": T.Int(0), "tagSIze": T.Int(0),
            "Item": T.String(""), "pack": T.String(self.pack), "path": T.String(path),
            "inventory": T.List[T.Compound]([T.Compound({"empty": T.Byte(1)}) for _ in range(27)]),
            "blueprintDataProvider": T.Compound({"corner1": pos(0, 0, 0), "corner2": pos(0, 0, 0), "path": T.String(path),
                                                 "schematicName": T.String(name), "pack": T.String(self.pack),
                                                 "posTagMap": T.List[T.Compound]([])})})
        self.set(x, y, z, f"{spec['hut']}[facing={facing}]", te)
        self.placed.setdefault("children", {})
        self.placed["children"][path] = self.placed["children"].get(path, 0) + 1
        self.child_positions.append((x, y, z, path))

    def hut(self, x, y, z, facing="north"):
        """The hut block. Must stay at the same place relative to the building on every level.
        For parks, watchtowers, piers and stops (pieces with a decoration controller) this places the controller."""
        if self.req.get("hut") is None:
            raise RequirementError(f"{self.rel}: plain piece has no hut / controller block - use d.anchor(x, y, z)")
        if "decorationcontroller" in self.req["hut"]:
            self.set(x, y, z, f"{self.req['hut']}[facing={facing},mirror=false,waterlogged=false]")
        else:
            self.set(x, y, z, f"{self.req['hut']}[facing={facing}]")
        self.hut_pos = (x, y, z)

    # ------------------------------------------------------------------------------------------- entities
    _FACING_BYTE = {"down": 0, "up": 1, "north": 2, "south": 3, "west": 4, "east": 5}
    _YAW = {"south": 0.0, "west": 90.0, "north": 180.0, "east": 270.0}

    @staticmethod
    def _item(item):
        if not item:
            return T.Compound({})
        return T.Compound({"id": T.String(_mc(item)), "count": T.Int(1)})

    @staticmethod
    def _uuid():
        import random
        return T.IntArray([random.getrandbits(32) - 2 ** 31 for _ in range(4)])

    def item_frame(self, x, y, z, facing, item=None, glow=False, rotation=0):
        """An item frame hanging in cell (x, y, z) on the block behind it; `facing` = the way the frame looks
        (away from the wall), e.g. "south" for a frame on a north wall; "up" = lying on the floor. The builder
        places it with its item (a label for a chest row, a tool on a workshop wall, a map...)."""
        b = self._FACING_BYTE[facing]
        e = 0.03125
        px, py, pz = x + 0.5, y + 0.5, z + 0.5
        if facing == "south":
            pz = z + e
        elif facing == "north":
            pz = z + 1 - e
        elif facing == "east":
            px = x + e
        elif facing == "west":
            px = x + 1 - e
        elif facing == "up":
            py = y + e
        else:
            py = y + 1 - e
        pitch = -90.0 if facing == "up" else (90.0 if facing == "down" else 0.0)
        self.bp.entities.append(T.Compound({
            "id": T.String("minecraft:glow_item_frame" if glow else "minecraft:item_frame"),
            "Pos": T.List[T.Double]([T.Double(px), T.Double(py), T.Double(pz)]),
            "TileX": T.Int(x), "TileY": T.Int(y), "TileZ": T.Int(z), "Facing": T.Byte(b),
            "Rotation": T.List[T.Float]([T.Float(self._YAW.get(facing, 0.0)), T.Float(pitch)]),
            "ItemRotation": T.Byte(rotation), "Item": self._item(item), "Fixed": T.Byte(0), "Invisible": T.Byte(0),
            "UUID": self._uuid(),
        }))

    def armor_stand(self, x, y, z, facing="south", head=None, chest=None, legs=None, feet=None, mainhand=None,
                    offhand=None, arms=True):
        """An armour stand standing on the floor of cell (x, y, z), looking `facing`, wearing the given items."""
        self.bp.entities.append(T.Compound({
            "id": T.String("minecraft:armor_stand"),
            "Pos": T.List[T.Double]([T.Double(x + 0.5), T.Double(y), T.Double(z + 0.5)]),
            "Rotation": T.List[T.Float]([T.Float(self._YAW.get(facing, 0.0)), T.Float(0.0)]),
            "ArmorItems": T.List[T.Compound]([self._item(feet), self._item(legs), self._item(chest), self._item(head)]),
            "HandItems": T.List[T.Compound]([self._item(mainhand), self._item(offhand)]),
            "ShowArms": T.Byte(1 if arms else 0), "NoBasePlate": T.Byte(0), "Small": T.Byte(0),
            "Invisible": T.Byte(0), "UUID": self._uuid(),
        }))

    def farm_test(self, expect, inputs=None, spawns=None, ticks=6000, min_count=1, light=None, mine=None,
                  blocks=None, blocks_min=None, presses=None):
        """Farmworks: how the in-game farm test runs this farm (python handmade.py writes it for the mod's test).
        expect   : {"minecraft:sugar_cane": 8, ...} items that must turn up in the farm's output containers
                   (containers tagged with d.tag(x, y, z, "farm_output")) after `ticks` game ticks;
        inputs   : {(x, y, z): [("minecraft:bone_meal", 64), ...]} items put into containers / dispensers first
                   (what a player would load: fuel, bone meal, seeds, buckets...);
        spawns   : [("minecraft:cow", x, y, z, count), ...] mobs / animals / villagers the player brings in
                   (mob farms: mobs put on the spawning floor, as if they had spawned there);
        mine     : [(x, y, z, "minecraft:cobblestone", n), ...] the test plays the player mining a generator: every 40
                   ticks, if that block is there it is broken; passes when it was broken at least n times
                   (i.e. it regenerated);
        blocks   : [(x, y, z, "minecraft:lava_cauldron"), ...] blocks to find at the end – at least `blocks_min`
                   of them (default all) must hold the given block;
        presses  : [(x, y, z), ...] buttons / levers the player presses every 200 ticks (e.g. dispensers);
        Item "minecraft:potion" in inputs is a water bottle.
        Coordinates are this design's grid coordinates. Blocks that random-tick (crops, cane, bamboo, kelp, cocoa,
        saplings, ...) are random-ticked by the test at the default rate x 10."""
        self.farm = dict(expect=dict(expect), inputs={f"{x},{y},{z}": list(v) for (x, y, z), v in (inputs or {}).items()},
                         spawns=[list(s) for s in (spawns or [])], ticks=ticks, light=light,
                         mine=[list(m) for m in (mine or [])], blocks=[list(b) for b in (blocks or [])],
                         blocks_min=blocks_min, presses=[list(p) for p in (presses or [])])

    def anchor(self, x, y, z):
        """Plain pieces (walls, roads, rails, canals, bridges, subway, boardwalk, cliff climb): the placement anchor
        (the cell the build tool's cursor sits on). No block is placed. Keep it where the pack's other pieces of the
        same family have theirs so pieces line up."""
        self.hut_pos = (x, y, z)

    def tag(self, x, y, z, name):
        self.tags.setdefault((x, y, z), []).append(name)

    def spot(self, x, y, z, name):
        """A tagged work spot where a citizen stands at (x,y,z): the tag goes on the floor block below."""
        self.tag(x, y - 1, z, name)
        self.placed["spots"][name] = self.placed["spots"].get(name, 0) + 1

    def cluster_size(self):
        c = self.req.get("cluster")
        return tuple(c["size"]) if c else None

    def cluster(self, x0, z0):
        """Paste the hut's functional cluster with its north-west corner at (x0, z0), its ground on this design's
        ground. Cells marked 'keep' in the snapshot are left as they are."""
        c = self.req["cluster"]
        src = load(HERE / c["file"])
        dy = self.gy - c["ground"]
        for x, y, z, s in src.blocks():
            if s == _mc(KEEP):
                continue
            ty = y + dy
            if ty < 0:
                continue
            te = src.tile_entities.get((x, y, z))
            if s.startswith("domum_ornamentum:") and "architectscutter" not in s:
                from vanillaize import convert
                n, props = parse_state(s)
                s = _mc(convert(n.split(":")[1], props, te))
                te = None
            s = _skin(self.pack, s)
            self.bp.set(x0 + x, ty, z0 + z, s, te)
        for x, y, z, t in c["tags"]:
            self.tag(x0 + x, self.gy + y, z0 + z, t)
        self.placed["cluster"] = True

    # ------------------------------------------------------------------------------------------- finishing
    def check(self):
        r = self.req
        p = dict(self.placed)
        # count what is really in the finished grid (catches required blocks overwritten later)
        real = {"beds": 0, "racks": 0, "bookshelves": 0, "items": {}}
        for *_, st in self.bp.blocks():
            n = st.split("[")[0]
            short = n.split(":")[1]
            if short.endswith("_bed") and "part=head" in st:
                real["beds"] += 1
            elif short == "blockminecoloniesrack":
                real["racks"] += 1
            elif short == "bookshelf":
                real["bookshelves"] += 1
            real["items"][n] = real["items"].get(n, 0) + 1
        p["beds"] = min(p["beds"], real["beds"])
        p["racks"] = min(p["racks"], real["racks"])
        p["bookshelves"] = min(p["bookshelves"], real["bookshelves"])
        p["items"] = {k: min(v, real["items"].get(k, 0)) for k, v in p["items"].items()}
        miss = []
        if self.hut_pos is None:
            miss.append("hut block" if r.get("hut") else "anchor (d.anchor)")
        elif r.get("hut") and not self.bp.get(*self.hut_pos).startswith(self.req["hut"]):
            miss.append(f"hut block at {self.hut_pos} was overwritten ({self.bp.get(*self.hut_pos)})")
        if p["beds"] < r["beds"]:
            miss.append(f"beds {p['beds']}/{r['beds']}")
        if p["racks"] < r["racks"]:
            miss.append(f"racks {p['racks']}/{r['racks']}")
        for k, n in r["items"].items():
            if p["items"].get(k, 0) < n:
                miss.append(f"{k} {p['items'].get(k, 0)}/{n}")
        for k, n in r["yard"].items():
            if p["yard"].get(k, 0) < n:
                miss.append(f"yard {k} {p['yard'].get(k, 0)}/{n}")
        if p["floor_items"] < r["floor_items"]:
            miss.append(f"composted dirt {p['floor_items']}/{r['floor_items']}")
        outs = sum(ns.count("sit_out") for ns in self.tags.values())
        if outs < r.get("yard_seats", 0):
            miss.append(f"outdoor seats (sit_out tags) {outs}/{r['yard_seats']}")
        if p["seats"] < r["seats"]:
            miss.append(f"seats {p['seats']}/{r['seats']}")
        for k, n in r["spots"].items():
            if p["spots"].get(k, 0) < n:
                miss.append(f"spot '{k}' {p['spots'].get(k, 0)}/{n}")
        if p["bookshelves"] < r["bookshelves"]:
            miss.append(f"bookshelves {p['bookshelves']}/{r['bookshelves']}")
        if r.get("cluster") and not p["cluster"]:
            miss.append("functional cluster (call cluster())")
        names = {}
        for ns in self.tags.values():
            for n in ns:
                names[n] = names.get(n, 0) + 1
        for k, n in r.get("tagreq", {}).items():
            if names.get(k, 0) < n:
                miss.append(f"tag '{k}' {names.get(k, 0)}/{n}")
        for (cx, cy, cz, cpath) in self.child_positions:
            spec = next((c for c in r.get("children", []) if c["path"] == cpath), None)
            if spec and not self.bp.get(cx, cy, cz).startswith(spec["hut"]):
                miss.append(f"child hut at {(cx, cy, cz)} was overwritten")
        for c in r.get("children", []):
            got = self.placed.get("children", {}).get(c["path"], 0)
            if got != c["count"]:
                miss.append(f"child huts {c['path']} {got}/{c['count']}")
        if miss:
            raise RequirementError(f"{self.pack} {self.rel}: missing " + ", ".join(miss))

    def finish(self) -> Blueprint:
        self.check()
        bp = self.bp
        connect_panes(bp)
        if self.pack == "Cascadia":
            cascadia_roofs(bp, self.gy)
        # trim empty layers on top
        top = max((y for y in range(bp.sy) if any(c != AIR for row in bp.grid[y] for c in row)), default=0)
        if bp.sy > top + 2:
            bp.grid = bp.grid[:top + 2]
            bp.sy = top + 2
        hx, hy, hz = self.hut_pos

        def pos(x, y, z):
            return T.Compound({"x": T.Int(x), "y": T.Int(y), "z": T.Int(z)})
        if self.is_child:
            tags = {self.hut_pos: ["invisible"]}
        else:
            tags = {(0, self.gy, 0): ["groundlevel"]}
            tags.setdefault(self.hut_pos, []).append(self.pack.lower())
        for q, ns in self.tags.items():
            tags.setdefault(q, []).extend(ns)
        name = Path(self.rel).stem
        if self.req.get("piece"):
            bp.primary_offset = self.hut_pos
            farm = getattr(self, "farm", None)
            if farm is not None:
                hx, hy, hz = self.hut_pos
                rel = lambda k: ",".join(str(int(a) - b) for a, b in zip(k.split(","), (hx, hy, hz)))
                outs = [f"{x - hx},{y - hy},{z - hz}" for (x, y, z), ns in self.tags.items() if "farm_output" in ns]
                bp.farm_test = dict(expect=farm["expect"], ticks=farm["ticks"], outputs=outs,
                                    inputs={rel(k): v for k, v in farm["inputs"].items()},
                                    spawns=[[s[0], s[1] - hx, s[2] - hy, s[3] - hz, s[4]] for s in farm["spawns"]],
                                    mine=[[m[0] - hx, m[1] - hy, m[2] - hz, m[3], m[4]] for m in farm["mine"]],
                                    blocks=[[b[0] - hx, b[1] - hy, b[2] - hz, b[3]] for b in farm["blocks"]],
                                    blocks_min=farm["blocks_min"] if farm["blocks_min"] is not None else len(farm["blocks"]),
                                    presses=[[q[0] - hx, q[1] - hy, q[2] - hz] for q in farm["presses"]])
            bp.architects = [self.pack]
            bp.name = f"{name}.blueprint"
            if self.req.get("hut") is None:          # plain piece: no controller, no tags
                return bp
            bp.tile_entities[self.hut_pos] = T.Compound({
                "id": T.String("minecolonies:decorationcontroller"), "path": T.String(self.rel),
                "name": T.String(name), "pack": T.String(self.pack), "Item": T.String(""),
                "mirror": T.Byte(0), "rotation": T.Int(0),
                "blueprintDataProvider": T.Compound({
                    "corner1": pos(-hx, -hy, -hz),
                    "corner2": pos(bp.sx - 1 - hx, bp.sy - 1 - hy, bp.sz - 1 - hz),
                    "path": T.String(self.rel), "schematicName": T.String(name), "pack": T.String(self.pack),
                    "posTagMap": T.List[T.Compound]([
                        T.Compound({"tagPos": pos(x - hx, y - hy, z - hz),
                                    "tagNameList": T.List[T.Compound]([T.Compound({"tagName": T.String(n)})
                                                                        for n in ns])})
                        for (x, y, z), ns in sorted(tags.items())]),
                }),
            })
            return bp
        te = T.Compound({
            "id": T.String("minecolonies:colonybuilding"), "mirror": T.Byte(0), "inWarehouse": T.Byte(0),
            "colony": T.Int(1), "type": T.String("minecraft:"), "version": T.Int(0), "tagSIze": T.Int(0),
            "Item": T.String(""), "pack": T.String(self.pack), "path": T.String(self.rel),
            "inventory": T.List[T.Compound]([T.Compound({"empty": T.Byte(1)}) for _ in range(27)]),
            "blueprintDataProvider": T.Compound({
                "corner1": pos(-hx, -hy, -hz),
                "corner2": pos(bp.sx - 1 - hx, bp.sy - 1 - hy, bp.sz - 1 - hz),
                "path": T.String(self.rel), "schematicName": T.String(name),
                "posTagMap": T.List[T.Compound]([
                    T.Compound({"tagPos": pos(x - hx, y - hy, z - hz),
                                "tagNameList": T.List[T.Compound]([T.Compound({"tagName": T.String(n)}) for n in ns])})
                    for (x, y, z), ns in sorted(tags.items())]),
            }),
        })
        bp.tile_entities[self.hut_pos] = te
        bp.primary_offset = self.hut_pos
        bp.architects = [self.pack]
        bp.name = f"{name}.blueprint"
        return bp


ROOF_WOOD = ("minecraft:dark_oak_stairs", "minecraft:spruce_stairs")
ROOF_SLAB = ("minecraft:dark_oak_slab", "minecraft:spruce_slab")


def cascadia_roofs(bp, gy):
    """Cascadia: wooden roof slopes become cobbled-deepslate shingles (dark, rough) so roofs stand out from the warm
    log and plank walls. Only sky-exposed stair rows of 5+ with the same facing (real roof courses, not outdoor
    stairs or seats) and the ridge slabs between them change."""
    def exposed(x, y, z):
        return all(bp.get(x, yy, z) == AIR for yy in range(y + 1, bp.sy))
    roof = set()
    for y in range(gy + 3, bp.sy):
        for z in range(bp.sz):
            for x in range(bp.sx):
                st = bp.grid[y][z][x]
                if not st.startswith(ROOF_WOOD) or not exposed(x, y, z):
                    continue
                props = parse_state(st)[1]
                if props.get("half") != "bottom":
                    continue
                f = props.get("facing")
                ax = (1, 0) if f in ("north", "south") else (0, 1)
                run = 1
                for sgn in (1, -1):
                    k = 1
                    while True:
                        n = bp.get(x + sgn * k * ax[0], y, z + sgn * k * ax[1])
                        if n.startswith(ROOF_WOOD) and parse_state(n)[1].get("facing") == f:
                            run += 1
                            k += 1
                        else:
                            break
                if run >= 5:
                    roof.add((x, y, z))
    for (x, y, z) in roof:
        name, props = parse_state(bp.grid[y][z][x])
        bp.grid[y][z][x] = format_state("minecraft:cobbled_deepslate_stairs", props)
    for y in range(gy + 3, bp.sy):
        for z in range(bp.sz):
            for x in range(bp.sx):
                st = bp.grid[y][z][x]
                if st.startswith(ROOF_SLAB) and exposed(x, y, z) and any(
                        (x + dx, y + dy, z + dz) in roof for dx, dz in D4.values() for dy in (-1, 0)):
                    props = parse_state(st)[1]
                    bp.grid[y][z][x] = format_state("minecraft:cobbled_deepslate_slab", props)
    return len(roof)


def _default_state(name, facing):
    n = name.split(":")[-1]
    f = facing or "north"
    if n in ("furnace", "smoker", "blast_furnace"):
        return f"{n}[facing={f},lit=false]"
    if n == "barrel":
        return f"barrel[facing={facing or 'up'},open=false]"
    if n == "anvil":
        return f"anvil[facing={f}]"
    if n in ("grindstone",):
        return f"grindstone[face=floor,facing={f}]"
    if n == "lectern":
        return f"lectern[facing={f},has_book=false,powered=false]"
    if n in ("beehive", "bee_nest"):
        return f"{n}[facing={f},honey_level=0]"
    if n in ("stonecutter", "loom"):
        return f"{n}[facing={f}]"
    if n == "chest":
        return f"chest[facing={f},type=single,waterlogged=false]"
    if n == "brewing_stand":
        return "brewing_stand[has_bottle_0=false,has_bottle_1=false,has_bottle_2=false]"
    if n == "cauldron":
        return "cauldron"
    if n == "composter":
        return "composter[level=0]"
    if n == "hopper":
        return "hopper[enabled=true,facing=down]"
    if n == "jukebox":
        return "jukebox[has_record=false]"
    if n == "bell":
        return f"bell[attachment=floor,facing={f},powered=false]"
    if n == "ender_chest":
        return f"ender_chest[facing={f},waterlogged=false]"
    if n == "target":
        return "target[power=0]"
    if n == "barrel_block":
        return f"minecolonies:barrel_block[facing={f},variant=0perc]"
    if "architectscutter" in n:
        return f"{name}[facing={f}]"
    return name


# --------------------------------------------------------------------------------------------- registry
DESIGNS = {}


def design(*bases):
    """Decorator: @design("tavern") def tavern(pack, rel, L) -> Design (unfinished)."""
    def wrap(fn):
        for b in bases:
            DESIGNS[b] = fn
        return fn
    return wrap


def load_designs():
    import importlib
    sys.path.insert(0, str(HERE))
    for f in sorted((HERE / "designs").glob("*.py")):
        if not f.name.startswith("_"):
            try:
                importlib.import_module(f"designs.{f.stem}")
            except Exception as e:                       # one broken file must not block the others
                print(f"WARNING: designs/{f.name} not loaded: {type(e).__name__}: {e}", file=sys.stderr)
    return DESIGNS


STYLE_PACKS = ("Neoterra", "Hearthwood", "Cascadia")


def rels_for(base):
    return sorted((r for r, v in REQ.items() if v["base"] == base), key=lambda r: REQ[r]["level"])


def packs_for(base):
    """Packs a type is built for: requirements' "packs" (e.g. Farmworks farms) or the three style packs."""
    rels = rels_for(base)
    return tuple(REQ[rels[0]].get("packs", STYLE_PACKS)) if rels else STYLE_PACKS


def assemble(design: "Design", bp: Blueprint, designs=None) -> Blueprint:
    """Parent blueprint with every child hut's blueprint (same level) pasted in, for checking and previews."""
    import copy as _copy
    designs = designs or DESIGNS
    out = _copy.deepcopy(bp)
    L = design.level
    for (x, y, z, path) in design.child_positions:
        rel = path.replace("0.blueprint", f"{L}.blueprint")
        base = REQ[rel]["base"]
        child = designs[base](design.pack, rel, L).finish()
        cx, cy, cz = child.primary_offset
        ox, oy, oz = x - cx, y - cy, z - cz
        for (a, b, c, st) in child.blocks():
            tx, ty, tz = a + ox, b + oy, c + oz
            if not out.inside(tx, ty, tz):
                if st != AIR:
                    raise RequirementError(f"{design.pack} {design.rel}: child {rel} sticks out of the parent at "
                                           f"({tx},{ty},{tz})")
                continue
            here = out.get(tx, ty, tz)
            if here == _mc(KEEP) or (st != AIR and "substitution" not in st):
                out.set(tx, ty, tz, st, child.tile_entities.get((a, b, c)))
        # anything still reserved there stays as-is in game; for checks treat it as air
    for (a, b, c, st) in list(out.blocks()):
        if st == _mc(KEEP):
            out.set(a, b, c, AIR)
    return out
