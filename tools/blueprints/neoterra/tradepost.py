"""
Trade Post (hut neoterra:blockhuttradepost, levels 1-5) for the Farmworks pack.

The hut comes from the Neoterra jar's Trade Post mod: two posts in different colonies are linked with a
Trade Ledger, requests one colony cannot fulfil are passed to the other one, and the Trade Courier carries
the goods between them. Every level adds racks for goods waiting to be carried.

  L1  timber market stall: open front, oak posts, two racks
  L2  closed oak store with a counter window and a cartography table
  L3  spruce depot on a cobblestone plinth, hay cart and hitching rail in the yard
  L4  stone-and-spruce trading house, dark oak roof, bell at the door, lanterns
  L5  deepslate and copper caravanserai with a lookout tower and loading awning

usage: python tradepost.py <Farmworks pack dir>
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from blueprint import Blueprint  # noqa: E402
from common import connect_panes, rack_te  # noqa: E402
from twinbuilder import hut_te, RACK, SOLID  # noqa: E402

PACK = "Farmworks"
HUT = "neoterra:blockhuttradepost[facing=north]"

# per level: posts, walls, base course, floor, roof (stairs/slab prefix), glass, apron
MATS = {
    1: dict(post="stripped_oak_log[axis=y]", wall="oak_planks", base="oak_planks", floor="oak_planks",
            roof="oak", glass="air", apron="dirt_path"),
    2: dict(post="oak_log[axis=y]", wall="oak_planks", base="cobblestone", floor="oak_planks",
            roof="spruce", glass="glass_pane", apron="dirt_path"),
    3: dict(post="spruce_log[axis=y]", wall="spruce_planks", base="cobblestone", floor="spruce_planks",
            roof="dark_oak", glass="glass_pane", apron="gravel"),
    4: dict(post="stripped_spruce_log[axis=y]", wall="spruce_planks", base="stone_bricks", floor="polished_andesite",
            roof="dark_oak", glass="glass_pane", apron="stone_bricks"),
    5: dict(post="stripped_dark_oak_log[axis=y]", wall="mud_bricks", base="polished_deepslate", floor="polished_deepslate",
            roof="waxed_cut_copper", glass="glass_pane", apron="deepslate_tiles"),
}
RACKS = {1: 2, 2: 4, 3: 6, 4: 8, 5: 10}


def mc(s):
    return s if ":" in s else "minecraft:" + s


def stairs(mat, facing, half="bottom"):
    return mc(f"{mat}_stairs[facing={facing},half={half},shape=straight,waterlogged=false]")


def slab(mat, kind="bottom"):
    return mc(f"{mat}_slab[type={kind},waterlogged=false]")


class Post:
    def __init__(self, L):
        self.L = L
        self.m = MATS[L]
        self.W = 9 + 2 * L                      # 11 .. 19
        self.D = 9 if L <= 2 else 11
        self.H = 4 if L <= 2 else (5 if L == 3 else 6)
        self.ox, self.oz = 2, 4
        self.sx, self.sz = self.W + 4, self.D + 5
        self.tower = L == 5
        self.sy = self.H + 3 + (self.D + 3) // 2 + (8 if self.tower else 1)

    # ---------------------------------------------------------------- shell
    def shell(self, bp):
        m, W, D, H, ox, oz, L = self.m, self.W, self.D, self.H, self.ox, self.oz, self.L
        for x in range(self.sx):
            for z in range(self.sz):
                bp.set(x, 0, z, SOLID)
                bp.set(x, 1, z, mc(m["apron"]))
        mid = ox + W // 2
        for x in range(ox, ox + W):
            for z in range(oz, oz + D):
                edge = x in (ox, ox + W - 1) or z in (oz, oz + D - 1)
                bp.set(x, 1, z, mc(m["base"] if edge else m["floor"]))
                for y in range(2, H + 2):
                    if not edge:
                        bp.set(x, y, z, "minecraft:air")
                        continue
                    corner = x in (ox, ox + W - 1) and z in (oz, oz + D - 1)
                    along = (x - ox) if z in (oz, oz + D - 1) else (z - oz)
                    front = z == oz
                    if corner or along % 4 == 0:
                        s = m["post"]
                    elif L == 1 and front:
                        s = "air"                      # open market stall
                    elif L == 1:
                        s = "oak_fence" if y == 3 else ("oak_planks" if y == 2 else "air")
                        if y == H + 1:
                            s = "oak_planks"
                    elif y == 2:
                        s = m["base"]
                    elif y in (3, 4) and along % 4 in (1, 2, 3) and not (front and abs(x - mid) <= 1):
                        s = m["glass"]
                    else:
                        s = m["wall"]
                    bp.set(x, y, z, mc(s))
        if L >= 2:                                     # double door in the middle of the front
            for x, hinge in ((mid - 1, "left"), (mid, "right")) if W % 2 == 0 else ((mid, "left"),):
                for y, half in ((2, "lower"), (3, "upper")):
                    bp.set(x, y, oz, mc(f"spruce_door[facing=south,half={half},hinge={hinge},open=false,powered=false]"))
            if L >= 3:
                for x in range(mid - 1, mid + 2):
                    bp.set(x, 4, oz, mc(m["post"].replace("axis=y", "axis=x")))
        self.roof(bp)

    def roof(self, bp):
        m, W, D, H, ox, oz = self.m, self.W, self.D, self.H, self.ox, self.oz
        y0 = H + 2
        z1, z2, k = oz - 1, oz + D, 0
        while z1 < z2:
            y = y0 + k
            for x in range(ox - 1, ox + W + 1):
                bp.set(x, y, z1, stairs(m["roof"], "south"))
                bp.set(x, y, z2, stairs(m["roof"], "north"))
            for x in (ox, ox + W - 1):                 # gable ends
                for z in range(z1 + 1, z2):
                    bp.set(x, y, z, mc(m["wall"]))
            z1, z2, k = z1 + 1, z2 - 1, k + 1
        if z1 == z2:
            for x in range(ox - 1, ox + W + 1):
                bp.set(x, y0 + k, z1, slab(m["roof"]))
        # tie beam with lanterns under it
        zc = oz + D // 2
        for x in range(ox + 1, ox + W - 1):
            bp.set(x, y0, zc, mc(self.m["post"].replace("axis=y", "axis=x")))
        for x in range(ox + 3, ox + W - 3, 4):
            bp.set(x, y0 - 1, zc, "minecraft:lantern[hanging=true,waterlogged=false]")

    # ---------------------------------------------------------------- inside
    def furnish(self, bp):
        W, D, ox, oz, L = self.W, self.D, self.ox, self.oz, self.L
        x1, x2 = ox + 1, ox + W - 2
        z_back = oz + D - 2
        n, placed = RACKS[L], 0
        for x in range(x1 + 1, x2):                    # back wall, corners left free
            if placed >= n:
                break
            bp.set(x, 2, z_back, RACK.format("north"), rack_te())
            placed += 1
        for z in range(z_back - 1, oz + 2, -1):        # then the left wall
            if placed >= n:
                break
            bp.set(x1, 2, z, RACK.format("east"), rack_te())
            placed += 1
        hut = (x2, 2, oz + 2)
        if L >= 2:
            bp.set(x2, 2, oz + 4, "minecraft:cartography_table")
        if L >= 3:
            bp.set(x2, 2, oz + 5, "minecraft:barrel[facing=up,open=false]")
        if L >= 4:
            bp.set(x2, 2, oz + 6, "minecraft:lectern[facing=west,has_book=false,powered=false]")
        return hut

    # ---------------------------------------------------------------- yard
    def yard(self, bp):
        m, W, D, H, ox, oz, L = self.m, self.W, self.D, self.H, self.ox, self.oz, self.L
        mid = ox + W // 2
        # path from the plot edge to the door
        for z in range(0, oz):
            for x in range(mid - 1, mid + 2):
                bp.set(x, 1, z, mc("dirt_path" if L <= 3 else m["base"]))
        if L == 1:                                     # counter of barrels along the open front
            for x in range(ox + 2, ox + W - 2):
                if abs(x - mid) > 1:
                    bp.set(x, 2, oz + 1, "minecraft:barrel[facing=up,open=false]")
        if L >= 2:                                     # hitching rail
            for x in range(ox, ox + 4):
                bp.set(x, 2, 1, "minecraft:oak_fence")
        if L >= 3:                                     # hay cart
            for x in range(ox + W - 5, ox + W - 1):
                bp.set(x, 2, 1, "minecraft:hay_block[axis=x]")
            bp.set(ox + W - 6, 2, 1, mc("spruce_trapdoor[facing=east,half=bottom,open=true,powered=false,waterlogged=false]"))
            bp.set(ox + W - 4, 3, 1, "minecraft:hay_block[axis=x]")
        if L >= 4:                                     # bell post by the door
            bp.set(mid + 3, 2, oz - 1, mc(m["post"]))
            bp.set(mid + 3, 3, oz - 1, "minecraft:bell[attachment=floor,facing=south,powered=false]")
            for x in (mid - 2, mid + 2):
                bp.set(x, 2, oz - 1, "minecraft:lantern[hanging=false,waterlogged=false]")
        if L == 5:
            # loading awning over the front
            for x in range(ox + 1, ox + W - 1):
                bp.set(x, H + 1, oz - 1, slab(m["roof"], "top"))
            for x in (ox + 1, ox + W - 2):
                for y in range(2, H + 1):
                    bp.set(x, y, oz - 1, mc(m["post"]))
            # lookout tower on the back-left corner, rising through the roof
            tx, tz = ox, oz + D - 3
            top = self.sy - 3
            for y in range(H + 2, top):
                for dx in range(3):
                    for dz in range(3):
                        edge = dx in (0, 2) or dz in (0, 2)
                        if edge:
                            corner = dx in (0, 2) and dz in (0, 2)
                            bp.set(tx + dx, y, tz + dz, mc(m["post"] if corner else
                                                            ("glass_pane" if y >= top - 2 else m["wall"])))
                        else:
                            bp.set(tx + dx, y, tz + dz, "minecraft:air")
            for dx in range(-1, 4):
                for dz in range(-1, 4):
                    bp.set(tx + dx, top, tz + dz, slab(m["roof"]))
            bp.set(tx + 1, top + 1, tz + 1, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")
            bp.set(tx + 1, top - 1, tz + 1, "minecraft:lantern[hanging=true,waterlogged=false]")

    def build(self):
        bp = Blueprint(self.sx, self.sy, self.sz, f"tradepost{self.L}.blueprint")
        self.shell(bp)
        hut = self.furnish(bp)
        self.yard(bp)
        connect_panes(bp)
        path = f"trade/tradepost{self.L}.blueprint"
        tags = {(0, 1, 0): ["groundlevel"]}
        bp.set(*hut, HUT, hut_te(PACK, path, (self.sx, self.sy, self.sz), hut, tags))
        bp.primary_offset = hut
        bp.architects = ["New5"]
        return bp


def build_all(root: Path):
    d = root / "trade"
    d.mkdir(parents=True, exist_ok=True)
    for L in range(1, 6):
        Post(L).build().save(d / f"tradepost{L}.blueprint")
    print(f"{PACK}: trade post 1-5")


if __name__ == "__main__":
    build_all(Path(sys.argv[1]))
