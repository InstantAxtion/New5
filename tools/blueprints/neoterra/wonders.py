"""
Grand Projects (wonders) for the Neoterra, Hearthwood and Cascadia packs.

Each wonder is a hut (neoterra:blockhut<wonder>, levels 1-5) whose blueprint reserves space for two
WING child huts (neoterra:blockhutwonderwing, <wonder>wing1-5). MineColonies registers the wings as
separate buildings, so up to three builders can work on one wonder at the same time. The colony bonus
counts the lowest level of the core and its wings (see the Trade Post mod's BuildingWonder).

  cathedral     nave with aisles, apse and rose window; wings = the two front bell towers
  grandbridge   arched viaduct with ramps and a central pavilion; wings = the two end pylons
  colossus      giant statue on a hall plinth, rising a section per level; wings = two fire braziers
  royalgranary  great barn hall with gambrel roof; wings = the two silos

The footprint stays the same at every level (the hut never moves); levels 1-3 use cheaper blocks and
levels 4-5 (5 only, for Hearthwood and Cascadia) the premium set.

usage: python wonders.py <pack dir> <Neoterra|Hearthwood|Cascadia>
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from blueprint import Blueprint  # noqa: E402
from common import connect_panes  # noqa: E402
from twinbuilder import hut_te, SOLID, SUBST  # noqa: E402

WING = "neoterra:blockhutwonderwing[facing=north]"

# cheap / premium materials per style
MATS = {
    "Neoterra": (
        dict(wall="white_concrete", wall2="light_gray_concrete", trim="smooth_stone", post="white_concrete",
             floor="polished_andesite", roof="polished_andesite", glass="light_blue_stained_glass", light="lantern",
             metal="iron_block", plaza="smooth_stone", accent="cyan_concrete", fence="iron_bars"),
        dict(wall="quartz_block", wall2="prismarine_bricks", trim="smooth_quartz", post="quartz_pillar[axis=y]",
             floor="smooth_quartz", roof="prismarine_brick", glass="light_blue_stained_glass", light="sea_lantern",
             metal="gold_block", plaza="quartz_bricks", accent="cyan_concrete", fence="iron_bars")),
    "Hearthwood": (
        dict(wall="white_terracotta", wall2="bricks", trim="stone_bricks", post="stripped_dark_oak_log[axis=y]",
             floor="oak_planks", roof="dark_oak", glass="glass", light="lantern", metal="iron_block",
             plaza="stone_bricks", accent="orange_terracotta", fence="dark_oak_fence"),
        dict(wall="calcite", wall2="bricks", trim="chiseled_stone_bricks", post="stripped_dark_oak_log[axis=y]",
             floor="dark_oak_planks", roof="deepslate_tile", glass="glass", light="lantern", metal="gold_block",
             plaza="polished_andesite", accent="orange_terracotta", fence="dark_oak_fence")),
    "Cascadia": (
        dict(wall="spruce_planks", wall2="cobblestone", trim="mossy_cobblestone", post="spruce_log[axis=y]",
             floor="spruce_planks", roof="spruce", glass="glass", light="lantern", metal="iron_block",
             plaza="cobblestone", accent="moss_block", fence="spruce_fence"),
        dict(wall="spruce_wood[axis=y]", wall2="tuff_bricks", trim="polished_basalt[axis=y]", post="dark_oak_log[axis=y]",
             floor="dark_oak_planks", roof="dark_oak", glass="glass", light="lantern", metal="waxed_weathered_cut_copper",
             plaza="tuff_bricks", accent="moss_block", fence="dark_oak_fence")),
}

# materials whose names do not end in a usable stairs/slab family
STAIR_BASE = {"stone_bricks": "stone_brick", "bricks": "brick", "prismarine_bricks": "prismarine_brick",
              "tuff_bricks": "tuff_brick", "quartz_block": "quartz", "deepslate_tiles": "deepslate_tile"}


def mc(s):
    return s if ":" in s else "minecraft:" + s


class W:
    """Blueprint plus geometry helpers."""

    def __init__(self, style, L, sx, sy, sz, name):
        self.style, self.L = style, L
        self.prem = L == 5 or (style == "Neoterra" and L >= 4)
        self.m = MATS[style][1 if self.prem else 0]
        self.bp = Blueprint(sx, sy, sz, name)
        self.sx, self.sy, self.sz = sx, sy, sz
        self.wings = []

    # -- primitives
    def S(self, x, y, z, s, te=None):
        if 0 <= x < self.sx and 0 <= y < self.sy and 0 <= z < self.sz:
            self.bp.set(x, y, z, mc(s), te)

    def get(self, x, y, z):
        return self.bp.get(x, y, z)

    def box(self, x1, y1, z1, x2, y2, z2, s):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            for z in range(min(z1, z2), max(z1, z2) + 1):
                for x in range(min(x1, x2), max(x1, x2) + 1):
                    self.S(x, y, z, s)

    def ring(self, x1, z1, x2, z2, y1, y2, s):
        for y in range(y1, y2 + 1):
            for x in range(x1, x2 + 1):
                self.S(x, y, z1, s)
                self.S(x, y, z2, s)
            for z in range(z1, z2 + 1):
                self.S(x1, y, z, s)
                self.S(x2, y, z, s)

    def stair(self, mat, facing, half="bottom"):
        return f"{STAIR_BASE.get(mat, mat)}_stairs[facing={facing},half={half},shape=straight,waterlogged=false]"

    def slab(self, mat, kind="bottom"):
        return f"{STAIR_BASE.get(mat, mat)}_slab[type={kind},waterlogged=false]"

    def gable_z(self, x1, x2, z1, z2, y0, mat, fill):
        """Roof whose ridge runs along z, covering x1..x2 (with 1 overhang)."""
        a, b, k = x1 - 1, x2 + 1, 0
        while a < b:
            for z in range(z1 - 1, z2 + 2):
                self.S(a, y0 + k, z, self.stair(mat, "east"))
                self.S(b, y0 + k, z, self.stair(mat, "west"))
            for x in range(a + 1, b):
                self.S(x, y0 + k, z1, fill)
                self.S(x, y0 + k, z2, fill)
            a, b, k = a + 1, b - 1, k + 1
        if a == b:
            for z in range(z1 - 1, z2 + 2):
                self.S(a, y0 + k, z, self.slab(mat))
        return y0 + k

    def gable_x(self, x1, x2, z1, z2, y0, mat, fill):
        """Roof whose ridge runs along x, covering z1..z2."""
        a, b, k = z1 - 1, z2 + 1, 0
        while a < b:
            for x in range(x1 - 1, x2 + 2):
                self.S(x, y0 + k, a, self.stair(mat, "south"))
                self.S(x, y0 + k, b, self.stair(mat, "north"))
            for z in range(a + 1, b):
                self.S(x1, y0 + k, z, fill)
                self.S(x2, y0 + k, z, fill)
            a, b, k = a + 1, b - 1, k + 1
        if a == b:
            for x in range(x1 - 1, x2 + 2):
                self.S(x, y0 + k, a, self.slab(mat))
        return y0 + k

    def cylinder(self, cx, cz, r, y1, y2, s, inside="air"):
        for y in range(y1, y2 + 1):
            for x in range(cx - r, cx + r + 1):
                for z in range(cz - r, cz + r + 1):
                    d = math.hypot(x - cx, z - cz)
                    if d <= r + 0.5:
                        self.S(x, y, z, s if d > r - 0.5 else inside)

    def cone(self, cx, cz, r, y0, s):
        y = y0
        while r >= 0:
            for x in range(cx - r, cx + r + 1):
                for z in range(cz - r, cz + r + 1):
                    if math.hypot(x - cx, z - cz) <= r + 0.5:
                        self.S(x, y, z, s)
            r -= 1
            y += 1
        return y

    def door(self, x, z, facing="south", wood="spruce", hinge="left"):
        self.S(x, 2, z, f"{wood}_door[facing={facing},half=lower,hinge={hinge},open=false,powered=false]")
        self.S(x, 3, z, f"{wood}_door[facing={facing},half=upper,hinge={hinge},open=false,powered=false]")

    def ground(self):
        for x in range(self.sx):
            for z in range(self.sz):
                self.S(x, 0, z, SOLID)
                self.S(x, 1, z, self.m["plaza"])

    # -- wings: reserve a region for a child hut
    def wing(self, x1, z1, x2, z2, hut, path):
        """Region x1..x2, z1..z2, from y1 to the top; `hut` is the wing hut position (absolute)."""
        self.wings.append((x1, z1, x2, z2, hut))
        for y in range(1, self.sy):
            for z in range(z1, z2 + 1):
                for x in range(x1, x2 + 1):
                    self.S(x, y, z, SUBST)
        self.S(*hut, WING, hut_te(self.style, path, (0, 0, 0), hut, {}, child=True))

    def finish(self, hut_state, hut, path, light_beam=None):
        connect_panes(self.bp)
        tags = {(0, 1, 0): ["groundlevel"]}
        self.S(*hut, hut_state, hut_te(self.style, path, (self.sx, self.sy, self.sz), hut, tags))
        self.bp.primary_offset = hut
        self.bp.architects = [self.style]
        self.bp.wings = self.wings
        return self.bp


def wing_bp(style, L, name, size, hut, path, draw):
    """Build a wing child blueprint of the given size; `draw(w)` paints into it (y0 = parent y1)."""
    cw, ch, cd = size
    w = W(style, L, cw, ch, cd, name)
    draw(w)
    w.S(*hut, WING, hut_te(style, path, size, hut, {hut: ["invisible"]}))
    connect_panes(w.bp)
    w.bp.primary_offset = hut
    w.bp.architects = [style]
    return w.bp


# =====================================================================================================
# Cathedral
# =====================================================================================================
def cathedral(style, L):
    SX, SY, SZ = 31, 44, 46
    w = W(style, L, SX, SY, SZ, f"cathedral{L}.blueprint")
    m = w.m
    w.ground()
    nx1, nx2, nz1, nz2 = 9, 21, 11, 38                     # nave
    H = (5, 9, 13, 14, 15)[L - 1]
    for x in range(5, 26):                                  # floor of nave and aisles
        for z in range(nz1, nz2 + 1):
            w.S(x, 1, z, m["floor"])
    # aisles (from level 2)
    if L >= 2:
        for x1, x2 in ((5, 8), (22, 25)):
            w.ring(x1, 13, x2, 36, 2, 7, m["wall"])
            for z in range(14, 36, 4):                      # aisle windows
                xo = x1 if x1 == 5 else x2
                for y in (4, 5):
                    w.S(xo, y, z, m["glass"])
                    w.S(xo, y, z + 1, m["glass"])
            for z in range(13, 37, 4):
                xo = x1 if x1 == 5 else x2
                for y in range(2, 9):
                    w.S(xo, y, z, m["post"])
            w.box(x1, 8, 13, x2, 8, 36, w.slab(m["roof"]) if L == 2 else m["wall2"])
            if L >= 3:                                      # lean-to roofs
                xo = x1 - 1 if x1 == 5 else x2 + 1
                for z in range(12, 38):
                    for x in range(x1, x2 + 1):
                        w.S(x, 9, z, w.slab(m["roof"]))
                    w.S(xo, 8, z, w.stair(m["roof"], "east" if x1 == 5 else "west"))
    # nave walls
    w.ring(nx1, nz1, nx2, nz2, 2, H + 1, m["wall"])
    for z in range(nz1, nz2 + 1, 4):                        # piers
        for x in (nx1, nx2):
            for y in range(2, H + 2):
                w.S(x, y, z, m["post"])
    if L >= 2:                                              # arcade between nave and aisles
        for z in range(14, 36):
            if (z - nz1) % 4 in (1, 2, 3) and z not in (13, 36):
                for x in (nx1, nx2):
                    for y in (2, 3, 4, 5):
                        w.S(x, y, z, "air")
                    w.S(x, 6, z, m["trim"])
    if L >= 3:                                              # clerestory windows above the aisle roofs
        for z in range(nz1 + 2, nz2 - 1, 4):
            for x in (nx1, nx2):
                for y in range(H - 2, H + 1):
                    w.S(x, y, z, m["glass"])
                    w.S(x, y, z + 1, m["glass"])
    # facade + door
    for x in range(14, 17):
        for y in range(2, 6):
            w.S(x, y, nz1, "air")
    w.S(14, 6, nz1, w.stair(m["wall2"] if m["wall2"] in STAIR_BASE else "stone_bricks", "east", "top"))
    w.S(16, 6, nz1, w.stair(m["wall2"] if m["wall2"] in STAIR_BASE else "stone_bricks", "west", "top"))
    if L >= 3:                                              # rose window
        cy = H - 2
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                d = math.hypot(dx, dy)
                if d <= 3.2:
                    w.S(15 + dx, cy + dy, nz1, m["glass"] if d < 2.6 else m["trim"])
        w.S(15, cy, nz1, m["metal"] if L >= 4 else m["trim"])
    for x in range(12, 19):                                 # steps in front
        w.S(x, 1, nz1 - 1, m["trim"])
    # roof
    if L == 1:
        for x in range(nx1, nx2 + 1, 3):                    # scaffolding beams
            w.S(x, H + 2, nz1, m["post"].replace("axis=y", "axis=z") if "axis" in m["post"] else m["post"])
    else:
        top = w.gable_z(nx1, nx2, nz1, nz2, H + 2, m["roof"], m["wall"])
        if L >= 4:                                          # crossing spire
            for y in range(top, top + 4 + L):
                w.S(15, y, 26, m["metal"] if y >= top + 2 + L else m["trim"])
    # apse: half-round end behind the nave
    if L >= 2:
        for x in range(8, 23):
            for z in range(nz2 + 1, nz2 + 8):
                d = math.hypot(x - 15, z - nz2)
                if d <= 6.5:
                    w.S(x, 1, z, m["floor"])
                    for y in range(2, H + 1):
                        w.S(x, y, z, m["wall"] if d > 5.5 else "air")
        for x in range(10, 21):                             # open the nave into the apse
            for y in range(2, H):
                w.S(x, y, nz2, "air")
        r, y = 6, H + 1
        while r >= 0:                                       # stepped half dome
            for x in range(15 - r, 16 + r):
                for z in range(nz2, nz2 + r + 1):
                    if math.hypot(x - 15, z - nz2) <= r + 0.5:
                        w.S(x, y, z, m["roof"] + "_planks" if m["roof"] in ("spruce", "dark_oak", "oak") else m["wall2"])
            r -= 2
            y += 1
    # interior: pews, altar, lights
    for z in range(15, 32, 2):
        for x in list(range(10, 14)) + list(range(17, 21)):
            w.S(x, 2, z, w.stair("spruce" if style == "Cascadia" else "dark_oak" if style == "Hearthwood" else "birch", "north"))
    w.box(13, 2, 35, 17, 2, 35, m["trim"])
    hut = (15, 3, 35)
    w.S(15, 2, 34, m["trim"])
    for z in range(17, 34, 6):
        w.S(15, H, z, m["light"] if m["light"] == "sea_lantern" else "lantern[hanging=true,waterlogged=false]")
    if L >= 5:
        w.S(13, 3, 35, "candle[candles=4,lit=true,waterlogged=false]")
        w.S(17, 3, 35, "candle[candles=4,lit=true,waterlogged=false]")
    # wings: front bell towers
    tower_h = SY - 1
    path = "wonders/cathedralwing0.blueprint"
    w.wing(2, 3, 8, 9, (5, 2, 4), path)
    w.wing(22, 3, 28, 9, (25, 2, 4), path)
    return w.finish(f"neoterra:blockhutcathedral[facing=north]", hut, f"wonders/cathedral{L}.blueprint")


def cathedral_wing(style, L):
    size = (7, 43, 7)                                       # x, y (parent y1..), z
    H = (6, 12, 18, 22, 26)[L - 1]

    def draw(w):
        m = w.m
        for x in range(7):
            for z in range(7):
                w.S(x, 0, z, m["floor"])
        w.ring(0, 0, 6, 6, 1, H, m["wall"])
        for y in range(1, H + 1):
            for x, z in ((0, 0), (0, 6), (6, 0), (6, 6)):
                w.S(x, y, z, m["post"])
        for y in range(1, H + 1, 6):
            w.ring(0, 0, 6, 6, y, y, m["trim"])
        w.door(3, 6, "north")                               # door toward the plaza (low z in the parent... faces +z side)
        w.door(3, 0, "south")
        if L >= 2:                                          # tall slit windows
            for y in range(4, H - 1):
                if y % 6 in (2, 3, 4):
                    for x, z in ((3, 0), (0, 3), (6, 3)):
                        w.S(x, y, z, m["glass"])
        if L >= 3:                                          # belfry openings + bell
            for y in (H - 2, H - 1):
                for x, z in ((2, 0), (3, 0), (4, 0), (0, 2), (0, 3), (0, 4), (6, 2), (6, 3), (6, 4), (2, 6), (3, 6), (4, 6)):
                    w.S(x, y, z, "air")
            w.box(1, H - 3, 1, 5, H - 3, 5, m["floor"])
            w.S(3, H - 1, 3, "bell[attachment=ceiling,facing=north,powered=false]")
            w.box(1, H, 1, 5, H, 5, m["wall"])
            top = w.cone(3, 3, 4, H + 1, m["roof"] + ("_planks" if m["roof"] in ("spruce", "dark_oak", "oak") else "") if L < 4 else w.m["wall2"])
            if L >= 4:
                for y in range(top, min(top + 3, 42)):
                    w.S(3, y, 3, m["metal"] if L == 5 else m["trim"])
        else:
            w.box(0, H + 1, 0, 6, H + 1, 6, w.slab(m["roof"]))

    hut = (3, 1, 3)
    return wing_bp(style, L, f"cathedralwing{L}.blueprint", size, hut, f"wonders/cathedralwing{L}.blueprint", draw)


# =====================================================================================================
# Grand Bridge
# =====================================================================================================
def grandbridge(style, L):
    SX, SY, SZ = 57, 26, 15
    w = W(style, L, SX, SY, SZ, f"grandbridge{L}.blueprint")
    m = w.m
    w.ground()
    z1, z2 = 6, 12                                          # deck width (railings on z1, z2)
    DY = 9                                                  # deck surface (walk on y=10)
    deck = m["wall2"] if L >= 2 else m["floor"]
    # ramps (1 up per block) from x=5..11 and 45..51
    for i in range(DY - 1):
        for z in range(z1, z2 + 1):
            for y in range(2, 2 + i + 1):
                w.S(4 + i, y, z, deck if y == 2 + i else m["wall"])
                w.S(52 - i, y, z, deck if y == 2 + i else m["wall"])
    for x in range(12, 45):
        for z in range(z1, z2 + 1):
            w.S(x, DY, z, deck)
    # piers every 6 blocks, arches between them
    for px in range(12, 45, 6):
        w.box(px, 2, z1, px, DY - 1, z2, m["post"] if L <= 2 else m["wall"])
    if L >= 2:
        for px in range(12, 39, 6):
            for dx in range(1, 6):
                x = px + dx
                rise = round(math.sqrt(max(0.0, 6.25 - (dx - 3) ** 2)))
                for y in range(DY - 1, DY - 1 - (3 - rise) - 1, -1):
                    for z in range(z1, z2 + 1):
                        if z in (z1, z2) or L >= 3:
                            w.S(x, y, z, m["wall"])
    # railings
    for x in range(4, 53):
        top = None
        for y in range(SY - 1, 1, -1):
            g = w.get(x, y, z1)
            if not g.endswith(":air") and "structure_void" not in g:
                top = y
                break
        if top is None:
            continue
        for z in (z1, z2):
            w.S(x, top + 1, z, m["fence"] if L < 3 else ("prismarine_wall" if m["wall2"] == "prismarine_bricks" else f"{STAIR_BASE.get(m['wall2'], m['wall2'])}_wall" if m["wall2"] in ("stone_bricks", "bricks", "cobblestone", "mossy_cobblestone", "prismarine_bricks", "tuff_bricks") else m["fence"]))
    # lamps on the deck
    if L >= 3:
        for x in range(12, 45, 6):
            for z in (z1, z2):
                w.S(x, DY + 2, z, m["post"] if "log" in m["post"] or "pillar" in m["post"] else m["trim"])
                w.S(x, DY + 3, z, m["light"] if m["light"] == "sea_lantern" else "lantern[hanging=false,waterlogged=false]")
    # pavilion in the middle of the deck (the hut)
    cx, cz = 28, 9
    for x in (cx - 2, cx + 2):
        for z in (cz - 2, cz + 2):
            for y in range(DY + 1, DY + 5):
                w.S(x, y, z, m["post"])
    w.gable_x(cx - 2, cx + 2, cz - 2, cz + 2, DY + 5, m["roof"], m["wall"]) if L >= 2 else w.box(cx - 2, DY + 5, cz - 2, cx + 2, DY + 5, cz + 2, w.slab(m["roof"]))
    for x in range(cx - 1, cx + 2):                         # keep the pavilion gable ends open for walking through
        for y in range(DY + 1, DY + 5):
            for z in (cz - 2, cz + 2):
                w.S(x, y, z, "air")
    if L >= 4:
        for x, z in ((cx - 2, cz - 2), (cx + 2, cz - 2), (cx - 2, cz + 2), (cx + 2, cz + 2)):
            w.S(x, DY + 1, z, m["metal"])
    if L >= 5:                                              # banners of gold on the pavilion ridge
        w.S(cx, DY + 9, cz, m["metal"])
    hut = (cx, DY + 1, cz + 1)
    # wings: pylons at both ends beside the ramp (north side)
    path = "wonders/grandbridgewing0.blueprint"
    w.wing(0, 0, 4, 4, (2, 2, 2), path)
    w.wing(52, 0, 56, 4, (54, 2, 2), path)
    return w.finish("neoterra:blockhutgrandbridge[facing=north]", hut, f"wonders/grandbridge{L}.blueprint")


def grandbridge_wing(style, L):
    size = (5, 25, 5)
    H = (5, 9, 13, 16, 19)[L - 1]

    def draw(w):
        m = w.m
        for x in range(5):
            for z in range(5):
                w.S(x, 0, z, m["floor"])
        w.ring(0, 0, 4, 4, 1, H, m["wall"] if L < 4 else m["wall2"])
        for y in range(1, H + 1):
            for x, z in ((0, 0), (0, 4), (4, 0), (4, 4)):
                w.S(x, y, z, m["post"])
        w.door(2, 4, "north")
        if L >= 2:
            for y in range(5, H, 4):
                w.S(2, y, 0, m["glass"])
                w.S(0, y, 2, m["glass"])
                w.S(4, y, 2, m["glass"])
        w.box(0, H + 1, 0, 4, H + 1, 4, m["trim"])
        if L >= 3:
            top = w.cone(2, 2, 2, H + 2, m["wall2"])
            w.S(2, top, 2, m["light"] if m["light"] == "sea_lantern" else "lantern[hanging=false,waterlogged=false]")
            if L >= 5:
                w.S(2, top - 1, 2, m["metal"])

    return wing_bp(style, L, f"grandbridgewing{L}.blueprint", size, (2, 1, 2), f"wonders/grandbridgewing{L}.blueprint", draw)


# =====================================================================================================
# Colossus
# =====================================================================================================
def colossus(style, L):
    SX, SY, SZ = 25, 44, 27
    w = W(style, L, SX, SY, SZ, f"colossus{L}.blueprint")
    m = w.m
    w.ground()
    px1, px2, pz1, pz2 = 6, 18, 8, 20                       # plinth
    w.box(px1, 1, pz1, px2, 1, pz2, m["floor"])
    w.ring(px1, pz1, px2, pz2, 2, 7, m["wall2"])
    w.box(px1, 8, pz1, px2, 8, pz2, m["trim"])
    for x in range(px1, px2 + 1, 3):                        # pilasters
        w.box(x, 2, pz1, x, 7, pz1, m["post"])
    w.door(12, pz1, "south")
    w.S(12, 4, pz1, m["trim"])
    for x in range(px1 + 1, px2):                           # hall lights
        if x % 4 == 0:
            w.S(x, 7, 14, m["light"] if m["light"] == "sea_lantern" else "lantern[hanging=true,waterlogged=false]")
    hut = (12, 2, 17)
    stone = m["wall"] if not w.prem else m["metal"] if style != "Cascadia" else m["wall2"]
    skin = m["wall"]
    # statue, one section per level, on top of the plinth (y >= 9)
    if L >= 1:                                              # feet
        for fx in (9, 14):
            w.box(fx, 9, 13, fx + 1, 9, 16, skin)
    if L >= 2:                                              # legs + hips + tunic
        for fx in (9, 14):
            w.box(fx, 10, 14, fx + 1, 17, 15, skin)
        w.box(9, 18, 13, 15, 20, 16, m["wall2"])
    if L >= 3:                                              # torso + belt
        w.box(9, 21, 13, 15, 27, 16, skin)
        w.box(9, 21, 13, 15, 21, 16, m["accent"])
    if L >= 4:                                              # shoulders, arms, head
        w.box(8, 27, 13, 16, 28, 16, skin)
        w.box(7, 20, 14, 8, 28, 15, skin)                   # left arm down, holding a shield
        w.box(6, 19, 12, 6, 24, 17, m["wall2"])
        w.box(16, 28, 14, 17, 34, 15, skin)                 # right arm raised
        w.box(11, 29, 14, 13, 29, 15, skin)                 # neck
        w.box(10, 30, 13, 14, 34, 16, skin)                 # head
        w.S(11, 32, 13, m["trim"])
        w.S(13, 32, 13, m["trim"])
    if L >= 5:                                              # crown and torch / blade
        for x in range(10, 15):
            w.S(x, 35, 13, m["metal"])
            w.S(x, 35, 16, m["metal"])
        for z in range(13, 17):
            w.S(10, 35, z, m["metal"])
            w.S(14, 35, z, m["metal"])
        for x in (10, 12, 14):
            w.S(x, 36, 13, m["metal"])
        w.box(16, 35, 14, 17, 35, 15, m["metal"])
        w.box(16, 36, 14, 17, 38, 15, "shroomlight" if style != "Neoterra" else "sea_lantern")
    # plaza steps to the door
    for x in range(10, 15):
        w.S(x, 1, pz1 - 1, m["trim"])
    path = "wonders/colossuswing0.blueprint"
    w.wing(1, 1, 5, 5, (3, 2, 3), path)
    w.wing(19, 1, 23, 5, (21, 2, 3), path)
    return w.finish("neoterra:blockhutcolossus[facing=north]", hut, f"wonders/colossus{L}.blueprint")


def colossus_wing(style, L):
    size = (5, 43, 5)
    H = (3, 5, 7, 9, 11)[L - 1]

    def draw(w):
        m = w.m
        for x in range(5):
            for z in range(5):
                w.S(x, 0, z, m["floor"])
        w.ring(0, 0, 4, 4, 1, H, m["wall2"])
        w.door(2, 4, "north")
        w.box(0, H + 1, 0, 4, H + 1, 4, m["trim"])
        if L >= 2:                                          # brazier bowl on top
            w.ring(0, 0, 4, 4, H + 2, H + 2, m["metal"] if L >= 4 else m["trim"])
            w.box(1, H + 2, 1, 3, H + 2, 3, "magma_block")
            w.box(1, H + 3, 1, 3, H + 3, 3, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        if L >= 3:
            for x, z in ((0, 0), (0, 4), (4, 0), (4, 4)):
                w.S(x, H + 3, z, m["post"])

    return wing_bp(style, L, f"colossuswing{L}.blueprint", size, (2, 1, 2), f"wonders/colossuswing{L}.blueprint", draw)


# =====================================================================================================
# Royal Granary
# =====================================================================================================
def royalgranary(style, L):
    SX, SY, SZ = 37, 30, 26
    w = W(style, L, SX, SY, SZ, f"royalgranary{L}.blueprint")
    m = w.m
    w.ground()
    x1, x2, z1, z2 = 8, 28, 6, 20
    H = (4, 7, 7, 8, 9)[L - 1]
    w.box(x1, 1, z1, x2, 1, z2, m["floor"])
    w.ring(x1, z1, x2, z2, 2, H + 1, m["wall"])
    w.ring(x1, z1, x2, z2, 2, 2, m["wall2"])
    for x in range(x1, x2 + 1, 4):
        for z in (z1, z2):
            w.box(x, 2, z, x, H + 1, z, m["post"])
    for z in range(z1, z2 + 1, 4):
        for x in (x1, x2):
            w.box(x, 2, z, x, H + 1, z, m["post"])
    if L >= 2:                                              # windows
        for x in range(x1 + 2, x2 - 1, 4):
            for z in (z1, z2):
                w.S(x, 4, z, m["glass"])
                w.S(x, 5, z, m["glass"])
    # big barn door (4 wide)
    for x in range(17, 20):
        for y in range(2, 6 if H >= 5 else 4):
            w.S(x, y, z1, "air")
    if L >= 3:
        w.S(17, 6, z1, m["trim"]); w.S(18, 6, z1, m["trim"]); w.S(19, 6, z1, m["trim"])
    # roof: gambrel from level 2, flat beams at level 1
    if L == 1:
        for x in range(x1, x2 + 1, 2):
            w.box(x, H + 2, z1, x, H + 2, z2, m["post"].replace("axis=y", "axis=z") if "axis" in m["post"] else m["post"])
    else:
        y = H + 2
        a, b = z1 - 1, z2 + 1
        for step in range(3):                               # steep lower slope
            for x in range(x1 - 1, x2 + 2):
                w.S(x, y, a, m["roof"] + "_planks" if m["roof"] in ("spruce", "dark_oak", "oak") else m["wall2"])
                w.S(x, y, b, m["roof"] + "_planks" if m["roof"] in ("spruce", "dark_oak", "oak") else m["wall2"])
            for z in range(a + 1, b):
                w.S(x1, y, z, m["wall"])
                w.S(x2, y, z, m["wall"])
            y += 1
            if step < 2:
                a, b = a + 1, b - 1
        w.gable_x(x1, x2, a + 1, b - 1, y, m["roof"], m["wall"])
        if L >= 4:                                          # cupola
            for yy in range(y + 7, y + 10):
                w.ring(17, 12, 19, 14, yy, yy, m["post"] if yy < y + 9 else m["trim"])
            w.S(18, y + 10, 13, m["metal"])
    # inside: hay stacks, barrels, composters
    for x in range(x1 + 2, x2 - 1):
        for z in (z2 - 2, z2 - 1):
            if x % 5 != 3:
                for y in range(2, 2 + min(L, 3)):
                    w.S(x, y, z, "hay_block[axis=x]")
    for x in range(x1 + 2, x1 + 2 + 2 * L, 2):
        w.S(x, 2, z1 + 2, "barrel[facing=up,open=false]")
    if L >= 2:
        for x in range(x2 - 2, x2 - 2 - L, -1):
            w.S(x, 2, z1 + 2, "composter[level=0]")
    if L >= 3:
        for x in range(x1 + 4, x2 - 2, 6):
            w.S(x, H + 1, 13, m["light"] if m["light"] == "sea_lantern" else "lantern[hanging=true,waterlogged=false]")
    hut = (18, 2, 10)
    # yard: path to the door
    for x in range(17, 20):
        for z in range(0, z1):
            w.S(x, 1, z, m["trim"])
    path = "wonders/royalgranarywing0.blueprint"
    w.wing(0, 9, 6, 15, (3, 2, 3 + 9), path)
    w.wing(30, 9, 36, 15, (33, 2, 12), path)
    return w.finish("neoterra:blockhutroyalgranary[facing=north]", hut, f"wonders/royalgranary{L}.blueprint")


def royalgranary_wing(style, L):
    size = (7, 29, 7)
    H = (5, 10, 14, 17, 20)[L - 1]

    def draw(w):
        m = w.m
        for x in range(7):
            for z in range(7):
                if math.hypot(x - 3, z - 3) <= 3.5:
                    w.S(x, 0, z, m["floor"])
        w.cylinder(3, 3, 3, 1, H, m["wall"] if L < 3 else m["wall2"])
        for y in range(1, H + 1, 4):                        # hoops
            for x in range(7):
                for z in range(7):
                    d = math.hypot(x - 3, z - 3)
                    if 2.5 < d <= 3.5:
                        w.S(x, y, z, m["trim"])
        w.door(3, 0, "south")
        if L >= 3:
            top = w.cone(3, 3, 3, H + 1, m["roof"] + "_planks" if m["roof"] in ("spruce", "dark_oak", "oak") else "prismarine_bricks" if m["roof"] == "prismarine_brick" else m["wall2"])
            if L >= 5:
                w.S(3, top, 3, m["metal"])
        else:
            w.box(0, H + 1, 0, 6, H + 1, 6, w.slab(m["roof"]))

    return wing_bp(style, L, f"royalgranarywing{L}.blueprint", size, (3, 1, 3), f"wonders/royalgranarywing{L}.blueprint", draw)


WONDERS = {"cathedral": (cathedral, cathedral_wing), "grandbridge": (grandbridge, grandbridge_wing),
           "colossus": (colossus, colossus_wing), "royalgranary": (royalgranary, royalgranary_wing)}


def assemble(parent, wing, region, hut):
    """Parent with a wing pasted into its region (for checking)."""
    x1, z1, x2, z2, _ = region
    for y in range(wing.sy):
        for z in range(wing.sz):
            for x in range(wing.sx):
                if parent.inside(x1 + x, 1 + y, z1 + z):
                    parent.set(x1 + x, 1 + y, z1 + z, wing.get(x, y, z))


def check(style):
    """Walk-check every level with its wings pasted in (as MineColonies will have built them)."""
    import walkcheck
    bad = 0
    for name, (core, wing) in WONDERS.items():
        for L in range(1, 6):
            bp, wb = core(style, L), wing(style, L)
            for region in bp.wings:
                assemble(bp, wb, region, None)
            res = walkcheck.analyse(bp)
            problems = res[1] if isinstance(res, tuple) else res
            if problems:
                bad += 1
                print(f"  {style} {name}{L}: {problems}")
    return bad


def build_all(root: Path, style: str):
    d = root / "wonders"
    d.mkdir(parents=True, exist_ok=True)
    for name, (core, wing) in WONDERS.items():
        for L in range(1, 6):
            bp = core(style, L)
            wb = wing(style, L)
            bp.save(d / f"{name}{L}.blueprint")
            wb.save(d / f"{name}wing{L}.blueprint")
    previews(d, style)
    if check(style):
        raise SystemExit(f"{style}: grand projects failed the assembled walk check")
    print(f"{style}: 4 grand projects x 5 levels + wings (walk-checked with wings)")


def previews(d: Path, style: str):
    """Assembled level-5 renders (docs/previews/wonders) and the Build Tool tab icon."""
    import subprocess
    import tempfile
    from PIL import Image, ImageOps
    here = Path(__file__).resolve().parent
    out = here.parents[2] / "docs" / "previews" / "wonders"
    out.mkdir(parents=True, exist_ok=True)
    fronts = []
    with tempfile.TemporaryDirectory() as tmp:
        for name, (core, wing) in WONDERS.items():
            bp, wb = core(style, 5), wing(style, 5)
            for r in bp.wings:
                assemble(bp, wb, r, None)
            f = Path(tmp) / f"{name}.blueprint"
            bp.save(f)
            subprocess.run([sys.executable, str(here.parent / "render.py"), str(f), str(out / f"{style.lower()}_{name}5")],
                           capture_output=True, check=True)
            fronts.append(Image.open(out / f"{style.lower()}_{name}5_front.png").convert("RGBA"))
    h = max(i.height for i in fronts)
    sheet = Image.new("RGBA", (sum(i.width for i in fronts) + 20 * len(fronts), h), (236, 240, 244, 255))
    x = 0
    for i in fronts:
        sheet.paste(i, (x, h - i.height), i)
        x += i.width + 20
    sheet.convert("RGB").save(out / f"{style.lower()}_wonders.png")
    im = fronts[0]
    side = max(im.size)
    sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    sq.paste(im, ((side - im.width) // 2, (side - im.height) // 2), im)
    icon = sq.resize((20, 20), Image.LANCZOS)
    icon.save(d / "icon.png")
    g = ImageOps.grayscale(icon.convert("RGB")).convert("RGBA")
    g.putalpha(icon.getchannel("A"))
    g.save(d / "icon_disabled.png")


if __name__ == "__main__":
    build_all(Path(sys.argv[1]), sys.argv[2])
