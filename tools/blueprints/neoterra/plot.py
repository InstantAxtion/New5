"""
Neoterra plot pass – clean exteriors on the smallest plot that fits the building.

Runs last (after reshape, massing/signature and detail):

  1. strips nature outside the buildings: trees, bushes, hedges, flowers, grass, vines, window boxes,
     roof plants (green-roof soil becomes roof deck). Plants inside buildings stay; the beekeeper keeps
     its flowers and the animal huts keep their grass pens.
  2. removes free-standing lamp posts on the lot.
  3. paves the remaining open ground as an apron in the building's material.
  4. crops the blueprint to the bounding box of the building (core + landmark modules + everything
     functional) plus a 1-block apron – that edge is the road access point. Hut/anchor offsets, the
     building corners and the groundlevel tag are moved with it. The crop is walk-checked: if any door,
     bed, workstation, rack or seat would lose its access, a 2-block apron is tried, else nothing is cut.
  5. trims empty layers above the building.

usage: python plot.py <pack-or-dir> [...]
"""
from __future__ import annotations

import copy
import re
import sys
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from blueprint import load, AIR  # noqa: E402
from nbtlib import tag as NBT  # noqa: E402
from detail import Detailer, nm, h  # noqa: E402
import themes  # noqa: E402

NATURE = ("leaves", "short_grass", "tall_grass", "fern", "sapling", "azalea", "petals", "vine", "moss_carpet",
          "dead_bush", "roots", "fungus", "sweet_berry", "lily_pad", "lilac", "rose_bush", "peony", "dandelion",
          "poppy", "bluet", "daisy", "allium", "lily_of_the_valley", "cornflower", "tulip", "orchid", "sunflower",
          "amethyst_bud")
SOILS = ("grass_block", "moss_block", "dirt", "coarse_dirt", "gravel", "crimson_nylium", "podzol", "mud")
TRUNKS = ("stripped_oak_log", "stripped_birch_log", "oak_log")
LIGHTS = ("lantern", "end_rod", "froglight", "sea_lantern", "redstone_lamp", "shroomlight", "lightning_rod")
ANIMALS = ("chickenherder", "cowboy", "shepherd", "swineherder", "rabbithutch")


class Plot(Detailer):
    def __init__(self, bp, level, name):
        super().__init__(bp, level, name)
        self.base = re.sub(r"\d.*$", "", name)
        self.gy = next((p[1] for p, n in self.tags.items() if "groundlevel" in n), 1)

    def outside(self, x, y, z):
        return not self.covered(x, y, z, 12)

    # -------------------------------------------------------------- 1. nature
    def strip_nature(self):
        bp, gy = self.bp, self.gy
        keep_flowers = self.base == "beekeeper"
        trunks_under = []
        for x, y, z, s in list(bp.blocks()):
            if (x, y, z) in self.protect:
                continue
            n = nm(s)
            if not any(k in n for k in NATURE) or "potted" in n:
                continue
            if not self.outside(x, y, z):
                continue
            if keep_flowers and "leaves" not in n:
                continue
            if self.base in ANIMALS and n in ("short_grass", "tall_grass", "fern") and y == gy + 1:
                continue
            bp.set(x, y, z, AIR)
            if "leaves" in n and any(t in self.n(x, y - 1, z) for t in TRUNKS):
                trunks_under.append((x, y - 1, z))
        for x, y, z in trunks_under:                       # tree trunks below removed crowns
            while y > gy and any(t in self.n(x, y, z) for t in TRUNKS) and (x, y, z) not in self.protect:
                bp.set(x, y, z, AIR)
                y -= 1
        # green-roof soil above ground becomes roof deck
        deck = "smooth_stone" if self.L <= 3 else "calcite"
        for x, y, z, s in list(bp.blocks()):
            if y > gy and nm(s) in ("grass_block", "moss_block") and (x, y, z) not in self.protect \
                    and self.sky(x, y + 1, z):
                bp.set(x, y, z, "minecraft:" + deck)

    # -------------------------------------------------------------- 2. lamp posts
    def strip_posts(self):
        bp, gy = self.bp, self.gy
        for x, y, z, s in list(bp.blocks()):
            if not any(k in nm(s) for k in LIGHTS) or (x, y, z) in self.protect or not self.outside(x, y, z):
                continue
            col = []
            yy = y - 1
            while yy > gy and self.solid(x, yy, z):
                col.append(yy)
                yy -= 1
            if yy != gy or not col:
                continue
            lonely = all(not self.solid(x + dx, c, z + dz) and "pane" not in self.n(x + dx, c, z + dz)
                         for c in col + [y] for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if not lonely or any((x, c, z) in self.protect for c in col):
                continue
            top = y
            while top + 1 < bp.sy and not self.air(x, top + 1, z) and not self.solid(x, top + 1, z):
                top += 1                                    # end rod / rod on top of the light
            for c in range(yy + 1, top + 1):
                bp.set(x, c, z, AIR)

    # -------------------------------------------------------------- 3. apron
    def pave(self):
        bp, gy = self.bp, self.gy
        if self.base in ANIMALS:
            return
        T = self.T
        tile = "polished_andesite" if self.L <= 3 else "calcite"
        line = "smooth_stone" if self.L <= 3 else (T["accent_p"][0] if T else "light_gray_concrete")
        if line.endswith("]") or "glass" in line or "lamp" in line:
            line = "smooth_stone"
        for x in range(bp.sx):
            for z in range(bp.sz):
                if (x, gy, z) in self.protect or nm(bp.get(x, gy, z)) not in SOILS:
                    continue
                if not self.air(x, gy + 1, z):
                    continue
                cover = next((self.n(x, yy, z) for yy in range(gy + 2, bp.sy) if not self.air(x, yy, z)), None)
                if cover and "glass" in cover:          # greenhouse / atrium interiors keep their soil
                    continue
                bp.set(x, gy, z, "minecraft:" + (line if (x % 5 == 0 or z % 5 == 0) else tile))

    # -------------------------------------------------------------- 4. crop
    def extent(self):
        bp, gy = self.bp, self.gy
        xs, zs = [], []
        funcs = {p for p, n in self.tags.items() if "groundlevel" not in n} | set(bp.tile_entities)
        for x, y, z, s in bp.blocks():
            n = nm(s)
            if y > gy and n != "air" and "substitution" not in n:
                xs.append(x)
                zs.append(z)
            elif y <= gy and ((x, y, z) in funcs or n in ("water", "farmland", "composted_dirt", "sand", "coarse_dirt")
                              and (x, y, z) in self.sensitive):
                xs.append(x)
                zs.append(z)
        for x, y, z in funcs:
            xs.append(x)
            zs.append(z)
        if not xs:
            return None
        return min(xs), max(xs), min(zs), max(zs)

    def crop(self, x0, x1, z0, z1):
        bp = self.bp
        x0, z0 = max(0, x0), max(0, z0)
        x1, z1 = min(bp.sx - 1, x1), min(bp.sz - 1, z1)
        nsx, nsz = x1 - x0 + 1, z1 - z0 + 1
        if nsx == bp.sx and nsz == bp.sz:
            return False
        bp.grid = [[row[x0:x1 + 1] for row in layer[z0:z1 + 1]] for layer in bp.grid]
        bp.sx, bp.sz = nsx, nsz
        bp.tile_entities = {(x - x0, y, z - z0): te for (x, y, z), te in bp.tile_entities.items()
                            if x0 <= x <= x1 and z0 <= z <= z1}
        ox, oy, oz = bp.primary_offset
        bp.primary_offset = (ox - x0, oy, oz - z0)
        gy = self.gy
        for (ax, ay, az), te in bp.tile_entities.items():
            bdp = te.get("blueprintDataProvider")
            if bdp is None:
                continue
            c1, c2 = bdp["corner1"], bdp["corner2"]
            if all(int(c[k]) == 0 for c in (c1, c2) for k in "xyz"):
                continue
            c1["x"], c1["z"] = NBT.Int(-ax), NBT.Int(-az)
            c2["x"], c2["z"] = NBT.Int(nsx - 1 - ax), NBT.Int(nsz - 1 - az)
            for e in bdp.get("posTagMap", []):
                if any(str(t["tagName"]) == "groundlevel" for t in e["tagNameList"]):
                    e["tagPos"]["x"], e["tagPos"]["z"] = NBT.Int(-ax), NBT.Int(-az)
                    e["tagPos"]["y"] = NBT.Int(gy - ay)
        return True

    def trim_top(self):
        bp = self.bp
        top = max((y for y in range(bp.sy) if any(c != AIR for row in bp.grid[y] for c in row)), default=0)
        cut = bp.sy - (top + 2)
        if cut <= 0:
            return
        bp.grid = bp.grid[:top + 2]
        bp.sy = top + 2
        for te in bp.tile_entities.values():
            bdp = te.get("blueprintDataProvider")
            if bdp is None:
                continue
            c1, c2 = bdp["corner1"], bdp["corner2"]
            if all(int(c[k]) == 0 for c in (c1, c2) for k in "xyz"):
                continue
            c2["y"] = NBT.Int(int(c2["y"]) - cut)

    def run(self):
        done = []
        if self.guarded(self.strip_nature):
            done.append("nature")
        if self.guarded(self.strip_posts):
            done.append("posts")
        if self.guarded(self.pave):
            done.append("apron")
        ext = self.extent()
        if ext:
            for m in (1, 2):
                snap = (copy.deepcopy(self.bp.grid), self.bp.sx, self.bp.sz, self.bp.primary_offset,
                        {p: copy.deepcopy(t) for p, t in self.bp.tile_entities.items()})
                before = self._score if self._score is not None else self.metric()
                x0, x1, z0, z1 = ext
                if not self.crop(x0 - m, x1 + m, z0 - m, z1 + m):
                    break
                self.tags = self._tags()
                if self.metric() <= before:
                    done.append(f"crop+{m}")
                    break
                (self.bp.grid, self.bp.sx, self.bp.sz, self.bp.primary_offset, self.bp.tile_entities) = snap
                self.tags = self._tags()
        self.trim_top()
        return done


def eligible(path: Path):
    p = path.as_posix()
    m = re.search(r"(\d+)\.blueprint$", path.name)
    if not m or any(k in p for k in ("/mineshafts/", "/supplies/", "/fields/", "/walls/", "/infrastructure/",
                                     "/parks/")):
        return None
    if any(k in path.name for k in ("bunker", "skytower", "barracks", "miner", "fisherman", "gatehouse",
                                    "wallguardtower", "plantation")):
        return None
    lvl = int(m.group(1))
    return lvl if 1 <= lvl <= 5 else None


def process(path_str):
    path = Path(path_str)
    L = eligible(path)
    if not L:
        return f"{path.name}: kept"
    bp = load(path)
    before = (bp.sx, bp.sy, bp.sz)
    pl = Plot(bp, L, path.stem)
    done = pl.run()
    bp.save(path)
    return f"{path.name}: {', '.join(done) or '-'} {before} -> {(bp.sx, bp.sy, bp.sz)}"


def main():
    files = []
    for a in sys.argv[1:]:
        p = Path(a)
        files += sorted(p.rglob("*.blueprint")) if p.is_dir() else [p]
    with Pool() as pool:
        for line in pool.imap_unordered(process, [str(f) for f in files], chunksize=1):
            print(line)


if __name__ == "__main__":
    main()
