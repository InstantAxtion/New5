"""
Real-world military buildings for Neoterra, Hearthwood and Cascadia.

  barracks1-5 + barrackstower1-5   walled fort: curtain wall with battlements and gate, parade ground with flag
                                   and targets, two-storey barracks hall with armoury; corner keeps (child huts,
                                   one more per level) with 4 bunks per level, ladders and battlements
  gatehouse1-3                     castle gatehouse: two flanking towers, arched passage with the gate (wooden,
                                   taller, then a 4-high iron gate), fighting gallery for the archers, bunks
  wallguardtower1-5                bastion tower: stacked floors, bunks and armoury, battlemented top

Hut positions, gate / knight / archer tags, bed and rack counts and the gatehouse footprint are kept as before so
the buildings still fit the walls and MineColonies' requirements.

usage: python military_real.py <pack dir> <Neoterra|Hearthwood|Cascadia>
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import connect_panes, rack_te  # noqa: E402
from twinbuilder import hut_te, SOLID, SUBST  # noqa: E402
from wonders import W  # noqa: E402

RACK = "minecolonies:blockminecoloniesrack[facing={},variant=blockrackemptysingle]"

MIL = {
    "Neoterra": (dict(wall="light_gray_concrete", wall2="gray_concrete", trim="smooth_stone", timber="white_concrete",
                      roof="polished_andesite", floor="polished_andesite", ground="gravel", accent="cyan_concrete",
                      bed="cyan", wood="birch", glass="light_blue_stained_glass_pane"),
                 dict(wall="quartz_bricks", wall2="polished_andesite", trim="smooth_quartz", timber="white_concrete",
                      roof="smooth_quartz", floor="smooth_quartz", ground="gravel", accent="cyan_concrete",
                      bed="cyan", wood="birch", glass="light_blue_stained_glass_pane")),
    "Hearthwood": (dict(wall="stone_bricks", wall2="bricks", trim="chiseled_stone_bricks", timber="stripped_dark_oak_log[axis=y]",
                        roof="dark_oak", floor="dark_oak_planks", ground="gravel", accent="red_wool",
                        bed="red", wood="dark_oak", glass="glass_pane"),
                   dict(wall="deepslate_bricks", wall2="bricks", trim="polished_deepslate", timber="stripped_dark_oak_log[axis=y]",
                        roof="deepslate_tile", floor="dark_oak_planks", ground="gravel", accent="red_wool",
                        bed="red", wood="dark_oak", glass="glass_pane")),
    "Cascadia": (dict(wall="cobblestone", wall2="mossy_cobblestone", trim="stone_bricks", timber="spruce_log[axis=y]",
                      roof="spruce", floor="spruce_planks", ground="coarse_dirt", accent="green_wool",
                      bed="green", wood="spruce", glass="glass_pane"),
                 dict(wall="tuff_bricks", wall2="mossy_cobblestone", trim="polished_basalt[axis=y]", timber="dark_oak_log[axis=y]",
                      roof="dark_oak", floor="dark_oak_planks", ground="coarse_dirt", accent="green_wool",
                      bed="green", wood="spruce", glass="glass_pane")),
}
DIRS = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}


def mats(style, L, maxL=5):
    prem = L == maxL or (style == "Neoterra" and L >= 4)
    return MIL[style][1 if prem else 0]


class B(W):
    def __init__(self, style, L, sx, sy, sz, name, maxL=5):
        super().__init__(style, L, sx, sy, sz, name)
        self.k = mats(style, L, maxL)
        self.tags = {(0, 1, 0): ["groundlevel"]}

    def bed(self, x, y, z, facing):
        """Foot at (x,y,z), head one step towards `facing`."""
        dx, dz = DIRS[facing]
        c = self.k["bed"]
        self.S(x, y, z, f"{c}_bed[facing={facing},occupied=false,part=foot]")
        self.S(x + dx, y, z + dz, f"{c}_bed[facing={facing},occupied=false,part=head]")

    def crenels(self, x1, z1, x2, z2, y, mat):
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                if x in (x1, x2) or z in (z1, z2):
                    self.S(x, y, z, mat)
                    if (x + z) % 2 == 0:
                        self.S(x, y + 1, z, mat)

    def ladder(self, x, z, y1, y2, facing):
        for y in range(y1, y2 + 1):
            self.S(x, y, z, f"ladder[facing={facing},waterlogged=false]")

    def flag(self, x, z, y0, h):
        for y in range(y0, y0 + h):
            self.S(x, y, z, f"{self.k['wood']}_fence")
        for dx in (1, 2, 3):
            for dy in (0, 1):
                self.S(x + dx, y0 + h - 2 + dy, z, self.k["accent"] if (dx + dy) % 2 else "white_wool")

    def finish_hut(self, state, hut, path, tags=None):
        connect_panes(self.bp)
        t = dict(self.tags)
        t.update(tags or {})
        self.S(*hut, state, hut_te(self.style, path, (self.sx, self.sy, self.sz), hut, t))
        self.bp.primary_offset = hut
        self.bp.architects = [self.style]
        return self.bp


# ================================================================================================ barracks
TOWER_CORNERS = [(0, 0), (20, 0), (0, 20), (20, 20)]


def barracks(style, L):
    SX = SZ = 27
    SY = 34
    b = B(style, L, SX, SY, SZ, f"barracks{L}.blueprint")
    k = b.k
    for x in range(SX):
        for z in range(SZ):
            b.S(x, 0, z, SOLID)
            b.S(x, 1, z, k["ground"] if 6 < x < 20 and 6 < z < 17 else k["trim"] if k["trim"] != "polished_basalt[axis=y]" else "stone_bricks")
    # curtain wall with battlements
    WH = 6
    for x in range(SX):
        for z in range(SZ):
            if x in (0, SX - 1) or z in (0, SZ - 1):
                for y in range(2, WH + 1):
                    b.S(x, y, z, k["wall"] if (x + y + z) % 5 else k["wall2"])
    b.crenels(0, 0, SX - 1, SZ - 1, WH + 1, k["wall"])
    for x in range(12, 15):                                 # gate in the front wall
        for y in range(2, 5):
            b.S(x, y, 0, "air")
        b.S(x, 5, 0, k["trim"])
    for x in (11, 15):                                      # gate piers
        for y in range(2, WH + 2):
            b.S(x, y, 0, k["trim"] if k["trim"] != "polished_basalt[axis=y]" else "stone_bricks")
    # barracks hall along the back wall
    hx1, hx2, hz1, hz2 = 7, 19, 17, 25
    floors = 1 if L <= 2 else 2
    top = 1 + 5 * floors
    for x in range(hx1, hx2 + 1):
        for z in range(hz1, hz2 + 1):
            b.S(x, 1, z, k["floor"])
            edge = x in (hx1, hx2) or z in (hz1, hz2)
            for y in range(2, top + 1):
                if not edge:
                    b.S(x, y, z, "air")
                    continue
                corner = x in (hx1, hx2) and z in (hz1, hz2)
                along = x - hx1 if z in (hz1, hz2) else z - hz1
                if corner or along % 4 == 0:
                    s = k["timber"] if style != "Neoterra" else k["wall2"]
                elif (y - 2) % 5 in (1, 2) and along % 2 == 0:
                    s = k["glass"]
                elif y <= 3:
                    s = k["wall"]
                else:
                    s = k["wall2"] if style == "Hearthwood" else k["wall"]
                b.S(x, y, z, s)
        if floors == 2:
            for z in range(hz1 + 1, hz2):
                if hx1 < x < hx2:
                    b.S(x, 6, z, k["floor"])
    if floors == 2:
        b.ladder(hx1 + 1, hz2 - 1, 2, 6, "east")
    if style == "Neoterra":
        b.ring(hx1, hz1, hx2, hz2, top + 1, top + 1, k["trim"])
    else:
        b.gable_x(hx1, hx2, hz1, hz2, top + 1, k["roof"], k["wall"])
    b.door(13, hz1, "south", wood=k["wood"])
    b.S(12, 4, hz1, k["trim"])
    b.S(14, 4, hz1, k["trim"])
    # armoury: anvil, smithing table, barrels; long tables
    b.S(hx1 + 2, 2, hz2 - 1, "anvil[facing=north]")
    if L >= 3:
        b.S(hx1 + 4, 2, hz2 - 1, "smithing_table")
    b.S(hx2 - 2, 2, hz2 - 1, "barrel[facing=up,open=false]")
    b.S(hx2 - 3, 2, hz2 - 1, "barrel[facing=up,open=false]")
    for x in range(hx1 + 3, hx2 - 2):
        if x != 13:
            b.S(x, 2, hz1 + 3, f"{k['wood']}_fence")
            b.S(x, 3, hz1 + 3, f"{k['wood']}_pressure_plate[powered=false]")
    for x in range(hx1 + 2, hx2 - 1, 4):
        b.S(x, top - 1 if floors == 1 else 5, hz1 + 4, "lantern[hanging=true,waterlogged=false]")
    hut = (16, 2, hz2 - 1)
    # parade ground: flag, targets (more each level)
    b.flag(13, 10, 2, 8 + L)
    for i in range(min(L + 1, 5)):
        x = 8 + i * 3 if i < 3 else 18
        z = 6 if i < 3 else 8 + (i - 3) * 3
        b.S(x, 2, z, "hay_block[axis=y]")
        b.S(x, 3, z, "target[power=0]")
    # corner keeps (child huts)
    n = min(L, 4)
    path = "military/barrackstower0.blueprint"
    for i in range(4):
        rx, rz = TOWER_CORNERS[i]
        if i < n:
            for y in range(1, SY):
                for x in range(rx, rx + 7):
                    for z in range(rz, rz + 7):
                        b.S(x, y, z, SUBST)
            th = (rx + 3, 2, rz + 3)
            b.S(*th, "minecolonies:blockhutbarrackstower[facing=north]", hut_te(style, path, (0, 0, 0), th, {}, child=True))
        else:                                               # until the keep is built: a squat corner bastion
            for x in range(rx, rx + 7):
                for z in range(rz, rz + 7):
                    if x in (rx, rx + 6) or z in (rz, rz + 6):
                        for y in range(2, WH + 2):
                            b.S(x, y, z, k["wall"])
            b.crenels(rx, rz, rx + 6, rz + 6, WH + 2, k["wall"])
    return b.finish_hut("minecolonies:blockhutbarracks[facing=north]", hut, f"military/barracks{L}.blueprint")


def barrackstower(style, L):
    SY = 33
    b = B(style, L, 7, SY, 7, f"barrackstower{L}.blueprint")
    k = b.k
    floors = L + 1                                          # ground floor + one bunk floor per level
    for f in range(floors):
        y0 = 4 * f
        for x in range(7):
            for z in range(7):
                edge = x in (0, 6) or z in (0, 6)
                b.S(x, y0, z, k["wall"] if edge else k["floor"])
                for y in range(y0 + 1, y0 + 4):
                    if not edge:
                        b.S(x, y, z, "air")
                        continue
                    corner = x in (0, 6) and z in (0, 6)
                    slit = y == y0 + 2 and (x == 3 or z == 3) and f > 0
                    b.S(x, y, z, k["glass"] if slit else (k["trim"] if corner else k["wall"]))
        if f > 0:                                           # four bunks
            b.bed(1, y0 + 1, 2, "north")
            b.bed(5, y0 + 1, 2, "north")
            b.bed(1, y0 + 1, 4, "south")
            b.bed(5, y0 + 1, 4, "south")
    top = 4 * floors
    b.ladder(3, 5, 1, top, "north")                        # ladder against the back wall, through every floor
    b.box(0, top, 0, 6, top, 6, k["floor"])
    b.S(3, top, 5, f"ladder[facing=north,waterlogged=false]")
    b.crenels(0, 0, 6, 6, top + 1, k["wall"])
    for x, z in ((3, 0), (3, 6), (0, 3), (6, 3)):           # doors on all four sides
        facing = {(3, 0): "south", (3, 6): "north", (0, 3): "east", (6, 3): "west"}[(x, z)]
        b.S(x, 1, z, f"{k['wood']}_door[facing={facing},half=lower,hinge=left,open=false,powered=false]")
        b.S(x, 2, z, f"{k['wood']}_door[facing={facing},half=upper,hinge=left,open=false,powered=false]")
    if L >= 3 and style != "Neoterra":                      # conical cap on raised posts
        for x, z in ((0, 0), (0, 6), (6, 0), (6, 6)):
            b.S(x, top + 2, z, k["timber"] if "log" in k["timber"] else k["wall"])
            b.S(x, top + 3, z, k["timber"] if "log" in k["timber"] else k["wall"])
        b.cone(3, 3, 4, top + 4, k["roof"] + "_planks" if k["roof"] in ("spruce", "dark_oak") else k["wall2"])
    elif L >= 3:
        b.flag(3, 3, top + 1, 5)
    b.S(3, 3, 3, "lantern[hanging=true,waterlogged=false]")
    hut = (3, 1, 3)
    b.tags = {}
    return b.finish_hut("minecolonies:blockhutbarrackstower[facing=north]", hut, f"military/barrackstower{L}.blueprint",
                        {hut: ["invisible"]})


# ================================================================================================ gatehouse
def gatehouse(style, L):
    SX, SY, SZ = 18, 20, 9
    b = B(style, L, SX, SY, SZ, f"gatehouse{L}.blueprint", maxL=3)
    k = b.k
    for x in range(SX):
        for z in range(SZ):
            b.S(x, 0, z, SOLID)
            b.S(x, 1, z, k["trim"] if k["trim"] != "polished_basalt[axis=y]" else "stone_bricks")
    TH = 14
    # flanking towers x 0..5 and 12..17
    for tx1, tx2 in ((0, 5), (12, 17)):
        for y in range(2, TH + 1):
            for x in range(tx1, tx2 + 1):
                for z in range(SZ):
                    edge = x in (tx1, tx2) or z in (0, SZ - 1)
                    if not edge:
                        b.S(x, y, z, "air")
                        continue
                    corner = x in (tx1, tx2) and z in (0, SZ - 1)
                    slit = (y in (4, 11)) and (z == 4 or x == (tx1 + tx2) // 2)
                    b.S(x, y, z, k["glass"] if slit else (k["trim"] if corner else k["wall"]))
        for x in range(tx1 + 1, tx2):                       # floor of the upper storey, walk-on roof
            for z in range(1, SZ - 1):
                b.S(x, 8, z, k["floor"])
                b.S(x, TH, z, k["floor"])
        b.crenels(tx1, 0, tx2, SZ - 1, TH + 1, k["wall"])
    # gate passage x 6..11; arch and fighting gallery above
    for x in range(6, 12):
        for z in range(SZ):
            for y in range(2, 8):
                b.S(x, y, z, "air" if 7 <= x <= 10 and y <= 6 else k["wall"])
            b.S(x, 8, z, k["floor"])
    for x in range(7, 11):                                  # rounded arch over the passage
        for z in (0, SZ - 1):
            b.S(x, 6, z, k["trim"] if x in (7, 10) else "air")
    for x in range(6, 12):                                  # gallery walls + parapet with crenels at the front
        b.S(x, 9, 0, k["wall"])
        if x % 2 == 0:
            b.S(x, 10, 0, k["wall"])
        b.S(x, 9, SZ - 1, k["wall"])
    for z in range(1, SZ - 1):
        for y in range(9, 13):
            b.S(6, y, z, k["wall"] if not (y in (9, 10) and z == 4) else "air")
            b.S(11, y, z, k["wall"] if not (y in (9, 10) and z == 4) else "air")
    if L >= 2:                                              # gallery roof
        for x in range(6, 12):
            for z in range(3, SZ):
                b.S(x, 13, z, k["floor"])
    # gates: wooden (1 high), wooden (2 high), iron portcullis (4 high)
    for x in range(7, 11):
        for y in range(2, 2 + (1, 2, 4)[L - 1]):
            if L < 3:
                b.S(x, y, 2, f"{k['wood']}_fence_gate[facing=south,in_wall=false,open=false,powered=false]")
            else:
                b.S(x, y, 2, "minecolonies:gate_iron[facing=south,half=lower,hinge=left,open=false,powered=false]")
    for x in (5, 12):                                       # towers open onto the gallery
        for y in (9, 10):
            b.S(x, y, 4, "air")
    # doors from the passage into the towers, ladders up
    for x, facing in ((5, "west"), (12, "east")):
        b.S(x, 2, 6, f"{k['wood']}_door[facing={facing},half=lower,hinge=left,open=false,powered=false]")
        b.S(x, 3, 6, f"{k['wood']}_door[facing={facing},half=upper,hinge=left,open=false,powered=false]")
    b.ladder(1, 7, 2, 8, "north")
    b.ladder(16, 7, 2, 8, "north")
    b.ladder(1, 7, 9, TH, "north")
    b.ladder(16, 7, 9, TH, "north")
    # bunks: 4 per tower on the upper floor
    for tx in (1, 13):
        b.bed(tx, 9, 2, "north")
        b.bed(tx + 2, 9, 2, "north")
        b.bed(tx, 9, 5, "south")
        b.bed(tx + 2, 9, 5, "south")
    b.S(2, 2, 2, "barrel[facing=up,open=false]")
    b.S(15, 2, 2, "barrel[facing=up,open=false]")
    for x in (3, 14):
        b.S(x, 7, 4, "lantern[hanging=true,waterlogged=false]")
    if L >= 2:                                              # torches / lanterns by the gate, banners of wool
        for x in (7, 10):
            b.S(x, 7, 0, k["accent"])
    if L >= 3 and style != "Neoterra":                      # pointed caps on the towers
        for tx in (0, 12):
            b.cone(tx + 2, 4, 3, TH + 3, k["roof"] + "_planks" if k["roof"] in ("spruce", "dark_oak") else k["wall2"])
            for x, z in ((tx + 0, 0), (tx + 5, 0), (tx + 0, 8), (tx + 5, 8)):
                b.S(x, TH + 2, z, k["wall"])
    if L >= 3:
        b.flag(8, 4, 14, 5)
    tags = {(x, 1, 2): ["gate"] for x in range(7, 11)}
    tags.update({(7, 1, 5): ["knight"], (10, 1, 5): ["knight"], (7, 8, 2): ["archer"], (10, 8, 2): ["archer"]})
    return b.finish_hut("minecolonies:blockhutgatehouse[facing=north]", (4, 2, 4), f"military/gatehouse{L}.blueprint", tags)


# ================================================================================================ wall guard tower
def wallguardtower(style, L):
    SX, SY, SZ = 13, 28, 11
    b = B(style, L, SX, SY, SZ, f"wallguardtower{L}.blueprint")
    k = b.k
    for x in range(SX):
        for z in range(SZ):
            b.S(x, 0, z, SOLID)
            b.S(x, 1, z, k["trim"] if k["trim"] != "polished_basalt[axis=y]" else "stone_bricks")
    floors = 2 + (L >= 3) + (L >= 5)
    cx, cz, r = 6, 5, 4.6
    round_ = style != "Neoterra"

    def inside(x, z, rr):
        return math.hypot(x - cx, z - cz) <= rr if round_ else (abs(x - cx) <= int(rr) and abs(z - cz) <= int(rr))

    for f in range(floors):
        y0 = 1 + 5 * f
        for x in range(SX):
            for z in range(SZ):
                if not inside(x, z, r):
                    continue
                wall = not inside(x, z, r - 1)
                b.S(x, y0, z, k["wall"] if wall else k["floor"])
                for y in range(y0 + 1, y0 + 5):
                    slit = y == y0 + 2 and wall and (x == cx or z == cz) and f > 0
                    b.S(x, y, z, k["glass"] if slit else (k["wall"] if wall else "air"))
    top = 1 + 5 * floors
    for x in range(SX):
        for z in range(SZ):
            if inside(x, z, r):
                b.S(x, top, z, k["floor"])
                if not inside(x, z, r - 1):
                    b.S(x, top + 1, z, k["wall"])
                    if (x + z) % 2 == 0:
                        b.S(x, top + 2, z, k["wall"])
    # corbelled band under the battlements
    for x in range(SX):
        for z in range(SZ):
            if inside(x, z, r) and not inside(x, z, r - 1):
                b.S(x, top - 1, z, k["trim"] if k["trim"] != "polished_basalt[axis=y]" else "stone_bricks")
    b.ladder(cx, cz + 3, 2, top, "north")
    b.S(cx, 2, cz - 4, f"{k['wood']}_door[facing=south,half=lower,hinge=left,open=false,powered=false]")
    b.S(cx, 3, cz - 4, f"{k['wood']}_door[facing=south,half=upper,hinge=left,open=false,powered=false]")
    # ground floor: armoury racks + barrel; first floor: four bunks
    racks = 1 + (L >= 3) + (L >= 5)
    for x, z, f in ((cx - 2, cz + 2, "north"), (cx + 2, cz + 2, "north"), (cx + 3, cz, "west"))[:racks]:
        b.S(x, 2, z, RACK.format(f), rack_te())
    b.S(cx - 3, 2, cz, "barrel[facing=up,open=false]")
    y1 = 7
    b.bed(cx - 2, y1, cz - 1, "north")
    b.bed(cx + 2, y1, cz - 1, "north")
    b.bed(cx - 2, y1, cz + 1, "south")
    b.bed(cx + 2, y1, cz + 1, "south")
    for f in range(floors):
        b.S(cx, 1 + 5 * f + 4, cz, "lantern[hanging=true,waterlogged=false]")
    if L >= 4:
        b.flag(cx, cz, top + 1, 6)
    hut = (7, 2, 6)
    return b.finish_hut("minecolonies:blockhutguardtower[facing=north]", hut, f"military/wallguardtower{L}.blueprint")


def build_all(root: Path, style: str):
    d = root / "military"
    d.mkdir(parents=True, exist_ok=True)
    for L in range(1, 6):
        barracks(style, L).save(d / f"barracks{L}.blueprint")
        barrackstower(style, L).save(d / f"barrackstower{L}.blueprint")
        wallguardtower(style, L).save(d / f"wallguardtower{L}.blueprint")
    for L in range(1, 4):
        gatehouse(style, L).save(d / f"gatehouse{L}.blueprint")
    print(f"{style}: barracks + keeps, gatehouse, wall guard tower (real-world forms)")


if __name__ == "__main__":
    build_all(Path(sys.argv[1]), sys.argv[2])
