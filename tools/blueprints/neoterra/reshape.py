"""
Neoterra reshape pass – each level re-forms the main building itself.

MineColonies upgrades place the new level's blueprint over the old one and swap every block that
differs, so the core building does not have to keep its shape. This pass (run after the generators,
before massing and detail) rebuilds the top of the main building per level:

  level 1   base building
  level 2   new roof form on the main roof
  level 3   + one storey, its own roof form
  level 4   + two storeys (stepped back on some buildings), vertical facade fins, balconies
  level 5   + three storeys, cantilevered slabs, a crown (glass dome, stepped glass pyramid,
            glowing halo rings or a needle spire)

Roof forms (gable, barrel vault, hip, sawtooth, overhang deck) rotate with the level and the
building, so consecutive levels never share a silhouette. New storeys are reached by a ladder that
runs up from the floor below beside a structural column. Everything protected (block entities,
tags, hut requirements, ladders, rooftop posts) stays untouched and every change is walk-checked.
"""
from __future__ import annotations

import math
import re
import sys
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from blueprint import load  # noqa: E402
from detail import h, nm, CHEAP_FORBIDDEN, DIRS  # noqa: E402
from massing import Massing, NATURE, kind_level  # noqa: E402

ROOFS = ["gable", "barrel", "hip", "sawtooth", "overhang"]
CROWNS = ["dome", "pyramid", "halo", "spire"]
STOREY = 5


FUNCTIONAL = ("door", "ladder", "bed", "blockhut", "rack", "chest", "barrel", "furnace", "smoker", "anvil", "table",
              "cauldron", "brewing", "composter", "beehive", "lectern", "grave", "obsidian", "loom", "grindstone",
              "stonecutter", "target", "hay_block", "composted", "farmland", "gate", "water", "lava", "substitution",
              "bell", "jukebox", "dummy", "scarecrow", "trapdoor")


class Reshape(Massing):
    def __init__(self, bp, level, name):
        super().__init__(bp, level, name)
        self.functional = set(self.tags)
        self.functional |= {p for p in bp.tile_entities if "domum_ornamentum" not in bp.get(*p)}
        for x, y, z, st in bp.blocks():
            if any(k in nm(st) for k in FUNCTIONAL):
                self.functional.add((x, y, z))

    def stair(self, facing, half="bottom"):
        mat = "smooth_quartz" if self.L >= 4 else ("polished_diorite" if h("st", self.base) < .5 else "stone_brick")
        return f"{mat}_stairs[facing={facing},half={half},shape=straight,waterlogged=false]"

    # -------------------------------------------------------------- roof analysis
    def main_roof(self, box):
        """Cut height yc (median column top of the main building) and the columns that can be rebuilt
        above it: they reach yc and hold nothing protected or functional from yc-2 upwards."""
        x1, x2, z1, z2, _ = box
        tops = {}
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                for y in range(self.bp.sy - 1, self.gy + 1, -1):
                    n = self.n(x, y, z)
                    if n == "air" or (n not in ("grass_block", "moss_block") and any(
                            k in n for k in NATURE + ("lantern", "rod", "chain", "pane", "paperwall", "carpet",
                                                      "potted", "detector"))):
                        continue
                    tops[(x, z)] = y
                    break
        if len(tops) < 25:
            return None
        ts = sorted(tops.values())
        yc = ts[len(ts) // 2]
        if yc - self.gy < 4:
            return None
        cells = set()
        for (x, z), t in tops.items():
            if t < yc - 4:
                continue
            if any(((x, y, z) in self.protect and "domum_ornamentum" not in self.get(x, y, z))
                   or (x, y, z) in self.functional for y in range(min(t, yc) - 2, max(t, yc) + 3)):
                continue
            if any((x + dx, y, z + dz) in self.functional for dx in (-1, 0, 1) for dz in (-1, 0, 1) for y in (yc, yc + 1, yc + 2)):
                continue
            cells.add((x, z))
        self.tops = tops
        return yc, cells

    def clear_and_slab(self, r, yc):
        """Remove the old roof above yc inside r and lay a fresh slab at yc + 1."""
        M = self.M
        x1, x2, z1, z2 = r
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                for y in range(yc + 1, self.tops.get((x, z), yc) + 2):
                    if (x, y, z) not in self.protect and self.bp.inside(x, y, z):
                        self.bp.set(x, y, z, "minecraft:air")
                e = x in (x1, x2) or z in (z1, z2)
                self.bp.set(x, yc + 1, z, "minecraft:" + (M["accent"] if e else M["roof"]))
        return yc + 1

    def best_rect(self, cells, cap=21):
        """Largest axis-aligned rectangle (both sides >= 5, at most cap) fully inside cells."""
        if not cells:
            return None
        xs = range(min(x for x, _ in cells), max(x for x, _ in cells) + 1)
        zs = range(min(z for _, z in cells), max(z for _, z in cells) + 1)
        best, area = None, 0
        for xa in xs:
            for xb in range(xa + 4, min(xa + cap, xs.stop)):
                run = 0
                for z in list(zs) + [None]:
                    full = z is not None and all((x, z) in cells for x in range(xa, xb + 1))
                    if full:
                        run += 1
                        d = min(run, cap)
                        if d >= 5 and (xb - xa + 1) * d > area:
                            area = (xb - xa + 1) * d
                            best = (xa, xb, z - d + 1, z)
                    else:
                        run = 0
        return best

    # -------------------------------------------------------------- pieces
    def storey(self, r, y0, glass_style):
        """Walls y0+1..y0+4 on rect r, slab at y0+5. Returns the slab y."""
        M = self.M
        x1, x2, z1, z2 = r
        top = y0 + STOREY
        self.ensure_height(top + 12)
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                e = x in (x1, x2) or z in (z1, z2)
                corner = x in (x1, x2) and z in (z1, z2)
                along = (x - x1) if z in (z1, z2) else (z - z1)
                for y in range(y0 + 1, top):
                    k = y - y0
                    if not e:
                        self.place(x, y, z, "air")
                    elif corner:
                        self.place(x, y, z, M["fin"])
                    elif k == 4:
                        self.place(x, y, z, M["wall"])
                    elif glass_style == "ribbon" and k in (2, 3):
                        self.place(x, y, z, M["glass"])
                    elif glass_style == "grid" and along % 3 and k in (1, 2, 3):
                        self.place(x, y, z, M["glass"])
                    elif glass_style == "slit" and along % 2 == 0 and k in (1, 2, 3):
                        self.place(x, y, z, M["glass"])
                    else:
                        self.place(x, y, z, M["wall"] if (along + k) % 7 else M["wall2"])
                self.place(x, top, z, M["accent"] if e else M["roof"])
        return top

    def ladder_up(self, r, base_y, top_y):
        """Ladder from the floor under the roof (base_y) up to top_y, against a column."""
        x1, x2, z1, z2 = r
        cands = []
        for x in range(x1 + 1, x2):
            for z in range(z1 + 1, z2):
                if not (x in (x1 + 1, x2 - 1) or z in (z1 + 1, z2 - 1)):
                    continue
                # floor below the roof slab
                fy = None
                for y in range(base_y - 1, self.gy, -1):
                    if not self.air(x, y, z):
                        fy = y
                        break
                if fy is None or base_y - fy < 3 or not self.solid(x, fy, z):
                    continue
                if any(self.near_sensitive(x, y, z, 1) for y in range(fy + 1, base_y + 1)):
                    continue
                if (x, base_y, z) in self.protect:
                    continue
                cands.append((abs(x - (x1 + x2) / 2) + abs(z - (z1 + z2) / 2), x, z, fy))
        if not cands:
            return False
        _, lx, lz, fy = max(cands)
        # wall side = towards the rect edge
        if lx == x1 + 1:
            wx, wz, face = lx - 1, lz, "east"
        elif lx == x2 - 1:
            wx, wz, face = lx + 1, lz, "west"
        elif lz == z1 + 1:
            wx, wz, face = lx, lz - 1, "south"
        else:
            wx, wz, face = lx, lz + 1, "north"
        for y in range(fy + 1, top_y + 1):
            if y == base_y or (y > base_y and (y - base_y) % STOREY == 0):
                self.bp.set(lx, y, lz, f"minecraft:ladder[facing={face},waterlogged=false]")
            else:
                self.place(lx, y, lz, f"ladder[facing={face},waterlogged=false]")
            if self.air(wx, y, wz):
                self.place(wx, y, wz, self.M["wall"])
        return True

    def roof_form(self, r, y, form):
        M = self.M
        x1, x2, z1, z2 = r
        w, d = x2 - x1 + 1, z2 - z1 + 1
        if form == "gable":
            along_x = w >= d
            half = (d if along_x else w) // 2
            for i in range(half + 1):
                for u in range((x1 if along_x else z1), (x2 if along_x else z2) + 1):
                    for side in (0, 1):
                        v = (z1 + i if side == 0 else z2 - i) if along_x else (x1 + i if side == 0 else x2 - i)
                        x, z = (u, v) if along_x else (v, u)
                        facing = ("south" if side == 0 else "north") if along_x else ("east" if side == 0 else "west")
                        if i == half:
                            self.place(x, y + 1 + i, z, M["accent"])
                        else:
                            self.place(x, y + 1 + i, z, self.stair(facing))
                        end = u in ((x1, x2) if along_x else (z1, z2))
                        for yy in range(y + 1, y + 1 + i):
                            self.place(x, yy, z, M["glass"] if end else "air")
        elif form == "barrel":
            along_x = w >= d
            span = d if along_x else w
            rad = span / 2
            for u in range((x1 if along_x else z1), (x2 if along_x else z2) + 1):
                rib = (u - (x1 if along_x else z1)) % 4 == 0
                for j in range(span):
                    hgt = int(round(math.sqrt(max(0.0, rad * rad - (j + 0.5 - rad) ** 2)) * 0.8))
                    v = (z1 if along_x else x1) + j
                    x, z = (u, v) if along_x else (v, u)
                    self.place(x, y + 1 + hgt, z, M["wall"] if rib else M["glass"])
                    if u in ((x1, x2) if along_x else (z1, z2)):
                        for yy in range(y + 1, y + 1 + hgt):
                            self.place(x, yy, z, M["glass"])
        elif form == "hip":
            for i in range(0, min(w, d) // 2 + 1):
                for x in range(x1 + i, x2 - i + 1):
                    for z in range(z1 + i, z2 - i + 1):
                        if x in (x1 + i, x2 - i) or z in (z1 + i, z2 - i):
                            self.place(x, y + 1 + i, z, M["glass"] if (i + x + z) % 3 else M["wall"])
        elif form == "sawtooth":
            for x in range(x1, x2 + 1):
                k = (x - x1) % 4
                for z in range(z1, z2 + 1):
                    if k == 0:
                        for yy in range(y + 1, y + 4):
                            self.place(x, yy, z, M["glass"] if z not in (z1, z2) else M["wall"])
                        self.place(x, y + 4, z, M["accent"])
                    else:
                        self.place(x, y + 4 - k, z, self.stair("west"))
        elif form == "overhang":
            for x in range(x1 - 2, x2 + 3):
                for z in range(z1 - 2, z2 + 3):
                    if x1 <= x <= x2 and z1 <= z <= z2:
                        continue
                    ring = x in (x1 - 2, x2 + 2) or z in (z1 - 2, z2 + 2)
                    self.place(x, y, z, M["light"] if (ring and self.L >= 4 and (x + z) % 2 == 0) else
                               (M["accent"] if ring else M["roof"]))
            for x in range(x1, x2 + 1):
                for z in range(z1, z2 + 1):
                    if x in (x1, x2) or z in (z1, z2):
                        self.place(x, y + 1, z, "glass_pane")

    def crown(self, r, y, kind):
        M = self.M
        x1, x2, z1, z2 = r
        cx, cz = (x1 + x2) // 2, (z1 + z2) // 2
        rad = min(x2 - x1, z2 - z1) // 2
        if kind == "dome":
            for yy in range(0, rad + 1):
                rr = math.sqrt(max(0.0, (rad + .5) ** 2 - yy * yy))
                for x in range(cx - rad - 1, cx + rad + 2):
                    for z in range(cz - rad - 1, cz + rad + 2):
                        dd = math.hypot(x - cx, z - cz)
                        if rr - 1.1 <= dd < rr:
                            rib = (x == cx or z == cz)
                            self.place(x, y + 1 + yy, z, M["fin"] if rib else M["glass"])
            top = y + rad + 2
        elif kind == "pyramid":
            for i in range(rad + 1):
                for x in range(cx - rad + i, cx + rad - i + 1):
                    for z in range(cz - rad + i, cz + rad - i + 1):
                        if x in (cx - rad + i, cx + rad - i) or z in (cz - rad + i, cz + rad - i):
                            self.place(x, y + 1 + i, z, M["light"] if i % 3 == 2 else M["glass"])
            top = y + rad + 2
        elif kind == "halo":
            for i, (hy, hr) in enumerate(((3, rad), (6, max(2, rad - 2)), (9, max(1, rad - 4)))):
                for x in range(cx - hr - 1, cx + hr + 2):
                    for z in range(cz - hr - 1, cz + hr + 2):
                        if hr - .6 <= math.hypot(x - cx, z - cz) < hr + .4:
                            self.place(x, y + hy, z, M["light"])
            for yy in range(y + 1, y + 11):
                self.place(cx, yy, cz, M["fin"])
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                for yy in range(y + 1, y + 4):
                    self.place(cx + dx * rad, yy, cz + dz * rad, M["fin"])
            top = y + 11
        else:  # spire
            for yy in range(y + 1, y + 14):
                k = yy - y
                self.place(cx, yy, cz, M["light"] if k % 4 == 0 else M["fin"])
                if k <= 4:
                    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        self.place(cx + dx, yy, cz + dz, M["wall"] if k < 4 else M["accent"])
            top = y + 14
        self.place(cx, top, cz, "end_rod[facing=up]" if self.L >= 4 else "lantern[hanging=false,waterlogged=false]")
        self.place(cx, top + 1, cz, "lightning_rod[facing=up,powered=false,waterlogged=false]")

    def fins(self, box, y_top):
        M = self.M
        x1, x2, z1, z2, _ = box
        for x in range(x1 - 1, x2 + 2):
            for z in range(z1 - 1, z2 + 2):
                if not (x in (x1 - 1, x2 + 1) or z in (z1 - 1, z2 + 1)) or (x + z) % 3:
                    continue
                inward = [(x + dx, z + dz) for dx, dz in DIRS.values()
                          if x1 <= x + dx <= x2 and z1 <= z + dz <= z2]
                if not inward:
                    continue
                for y in range(self.gy + 3, y_top + 1):
                    ix, iz = inward[0]
                    if self.solid(ix, y, iz) and self.air(x, y, z) and not self.near_sensitive(x, y, z, 0):
                        self.place(x, y, z, M["fin"])

    def balconies(self, r, y_floor):
        M = self.M
        x1, x2, z1, z2 = r
        for side in ("north", "south"):
            z_wall = z1 if side == "north" else z2
            zo = z_wall + (-1 if side == "north" else 1)
            third = (x2 - x1) // 3
            for x in range(x1 + third, x2 - third + 1):
                for dz in (0, 1):
                    zz = zo + (-dz if side == "north" else dz)
                    self.place(x, y_floor, zz, M["deck"])
                    if dz == 1 or x in (x1 + third, x2 - third):
                        self.place(x, y_floor + 1, zz, "glass_pane")
            mid = (x1 + x2) // 2
            for y in (y_floor + 1, y_floor + 2):
                if (mid, y, z_wall) not in self.protect:
                    self.bp.set(mid, y, z_wall, "minecraft:air")

    # -------------------------------------------------------------- plan
    def run(self):
        L = self.L
        if L < 2:
            return []
        box = self.core()
        if box is None:
            return []
        res = self.main_roof(box)
        if not res:
            return []
        yc, cells = res
        r = self.best_rect(cells)
        if not r:
            return []
        if not self.guarded(lambda: self.clear_and_slab(r, yc)):
            return []
        ry = yc + 1
        core_h = ry - self.gy
        tall = core_h >= 24
        v = int(h("form", self.base) * 1000)
        form = ROOFS[(v + L) % len(ROOFS)]
        crown = CROWNS[v % len(CROWNS)]
        glass = ["ribbon", "grid", "slit"][v % 3]
        stepped = h("step", self.base) < .5
        storeys = 0 if tall else {2: 0, 3: 1, 4: 2, 5: 3}[L]
        done = []

        def try_(label, fn):
            out = []
            if self.guarded(lambda: out.append(fn())) and out and out[0] is not False:
                done.append(label)
                return out[0]
            return None

        def build():
            y = ry
            rr = r
            rects = []
            for k in range(storeys):
                if k and stepped:
                    rr = (rr[0] + 1, rr[1] - 1, rr[2] + 1, rr[3] - 1)
                    if rr[1] - rr[0] < 4 or rr[3] - rr[2] < 4:
                        break
                rects.append((rr, y))
                y = self.storey(rr, y, glass)
                if L == 5:                                       # cantilevered slab edge
                    for x in range(rr[0] - 1, rr[1] + 2):
                        for z in range(rr[2] - 1, rr[3] + 2):
                            if x in (rr[0] - 1, rr[1] + 1) or z in (rr[2] - 1, rr[3] + 1):
                                self.place(x, y, z, self.M["light"] if (x + z) % 3 == 0 else self.M["accent"])
            if rects:
                self.ladder_up(r, ry, y)
            return rects, y, rr

        rects, top, last = ([], ry, r)
        if storeys:
            out = try_(f"+{storeys} storey{'s' if storeys > 1 else ''}", build)
            if out:
                rects, top, last = out
        if L == 5:
            try_(f"{crown} crown", lambda: self.crown(last, top, crown))
        else:
            try_(f"{form} roof", lambda: self.roof_form(last, top, form))
        if L >= 4:
            try_("fins", lambda: self.fins(box, top))
            for rr, y0 in rects[-2:]:
                try_("balconies", lambda rr=rr, y0=y0: self.balconies(rr, y0))
        return done


def process(path_str):
    path = Path(path_str)
    L = kind_level(path)
    if not L:
        return f"{path.name}: kept"
    bp = load(path)
    rs = Reshape(bp, L, path.stem)
    done = rs.run()
    if L <= 3:
        for x, y, z, s in bp.blocks():
            assert (x, y, z) in rs.protect or not any(w in s for w in CHEAP_FORBIDDEN), f"{path.name}: {s}"
    bp.save(path)
    return f"{path.name}: L{L} {', '.join(done) or '-'} -> {bp.sx}x{bp.sy}x{bp.sz}"


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
