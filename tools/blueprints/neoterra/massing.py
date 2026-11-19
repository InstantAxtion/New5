"""
Neoterra massing pass – makes the buildings themselves bigger and different from level to level.

Runs after the generators and before the detail pass. For every building it finds the main body
(largest connected block of built columns) and attaches new architecture to it, growing the lot
when it needs room:

  level 1   the core building as generated
  level 2   + entrance canopy on the front
  level 3   + front colonnade, two corner towers at the back
  level 4   + four corner towers, single-storey side wings with roof terraces
  level 5   + taller towers with glowing caps and spires, two-storey side wings, a back wing,
            front plaza with a fountain

Each building gets its own variant (from its name): tower shape (square / round / octagon /
stepped), wing style (glass hall / stepped terraces / sawtooth roof), colonnade style (columns
or arches) and its own material set, so no two buildings grow the same way. Towers have floors,
ladders and doors; wings are open halls the citizens can walk through. Nothing protected
(block entities, tags, hut requirements) is overwritten, nothing is built over paths, and every
addition is walk-checked and dropped if it would block anything.

usage: python massing.py <pack-or-dir> [...]
"""
from __future__ import annotations

import copy
import math
import re
import sys
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from blueprint import load, AIR  # noqa: E402
from detail import Detailer, h, nm, MC, CHEAP_FORBIDDEN, LEAVES, FLEAVES  # noqa: E402

SOLID_SUB = "structurize:blocksolidsubstitution"
NATURE = ("grass", "fern", "flower", "leaves", "log", "tulip", "poppy", "dandelion", "bluet", "daisy", "allium",
          "lily", "cornflower", "petals", "lilac", "rose_bush", "peony", "moss_carpet", "azalea", "sapling", "vine")

# material sets: (wall, wall2, trim, glass, light, fin, roof) per tier
MATS = {
    "cheap": [
        dict(wall="white_concrete", wall2="calcite", trim="tuff_bricks", glass="glass", light="lantern[hanging=false,waterlogged=false]",
             fin="stripped_birch_log[axis=y]", roof="smooth_stone", accent="cyan_terracotta", deck="polished_andesite"),
        dict(wall="calcite", wall2="bone_block[axis=y]", trim="polished_tuff", glass="glass", light="lantern[hanging=false,waterlogged=false]",
             fin="white_concrete", roof="smooth_stone", accent="waxed_oxidized_cut_copper", deck="polished_diorite"),
        dict(wall="white_concrete", wall2="polished_diorite", trim="chiseled_tuff", glass="glass", light="lantern[hanging=false,waterlogged=false]",
             fin="birch_planks", roof="stone_bricks", accent="cyan_concrete", deck="smooth_stone"),
    ],
    "premium": [
        dict(wall="smooth_quartz", wall2="quartz_bricks", trim="polished_deepslate", glass="light_blue_stained_glass",
             light="sea_lantern", fin="quartz_pillar[axis=y]", roof="smooth_quartz", accent="dark_prismarine", deck="calcite"),
        dict(wall="quartz_bricks", wall2="calcite", trim="deepslate_tiles", glass="cyan_stained_glass",
             light="pearlescent_froglight[axis=y]", fin="stripped_warped_stem[axis=y]", roof="smooth_quartz",
             accent="prismarine_bricks", deck="polished_diorite"),
        dict(wall="smooth_quartz", wall2="white_glazed_terracotta[facing=north]", trim="polished_blackstone_bricks",
             glass="light_blue_stained_glass", light="verdant_froglight[axis=y]", fin="quartz_pillar[axis=y]",
             roof="calcite", accent="waxed_oxidized_copper", deck="smooth_quartz"),
    ],
}


def mats_for(name, L):
    tier = "premium" if L >= 4 else "cheap"
    sets = MATS[tier]
    return dict(sets[int(h("mat", re.sub(r"\d", "", name)) * len(sets))])


class Massing(Detailer):
    def __init__(self, bp, level, name):
        super().__init__(bp, level, name)
        self.base = re.sub(r"\d+", "", name)
        self.M = mats_for(name, level)
        self.gy = self._ground_y()

    # -------------------------------------------------------------- analysis
    def _ground_y(self):
        for p, names in self.tags.items():
            if "groundlevel" in names:
                return p[1]
        return 1

    def free(self, x, y, z):
        if not self.bp.inside(x, y, z) or (x, y, z) in self.protect:
            return False
        n = self.n(x, y, z)
        return n == "air" or any(k in n for k in NATURE) or (y == self.gy and n in ("grass_block", "dirt"))

    def place(self, x, y, z, s):
        if self.free(x, y, z):
            self.bp.set(x, y, z, s if ":" in s else MC + s)
            return True
        return False

    def core(self):
        bp, gy = self.bp, self.gy
        built = set()
        for x in range(bp.sx):
            for z in range(bp.sz):
                cnt = 0
                for y in range(gy + 2, bp.sy):
                    n = self.n(x, y, z)
                    if n not in ("air", "water") and not any(k in n for k in NATURE + ("lantern", "rod", "chain",
                                                                                        "substitution")):
                        cnt += 1
                    elif n == "grass_block" and y >= gy + 3:
                        cnt += 1
                if cnt >= 1:
                    built.add((x, z))
        best = set()
        seen = set()
        for p in built:
            if p in seen:
                continue
            comp, stack = set(), [p]
            seen.add(p)
            while stack:
                c = stack.pop()
                comp.add(c)
                for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                    q = (c[0] + dx, c[1] + dz)
                    if q in built and q not in seen:
                        seen.add(q)
                        stack.append(q)
            if len(comp) > len(best):
                best = comp
        if len(best) < 16:
            return None
        xs, zs = [x for x, _ in best], [z for _, z in best]
        top = max(y for y in range(bp.sy) for x, z in list(best)[::3] if self.solid(x, y, z))
        return min(xs), max(xs), min(zs), max(zs), top

    def paved(self, x, z):
        n = self.n(x, self.gy, z)
        return self.bp.inside(x, self.gy, z) and n not in ("grass_block", "dirt", "air", "moss_block") \
            and "substitution" not in n

    def front_side(self, box):
        x1, x2, z1, z2 = box[:4]
        scores = {}
        strips = {"north": [(x, z1 - k) for x in range(x1, x2 + 1) for k in (1, 2, 3)],
                  "south": [(x, z2 + k) for x in range(x1, x2 + 1) for k in (1, 2, 3)],
                  "west": [(x1 - k, z) for z in range(z1, z2 + 1) for k in (1, 2, 3)],
                  "east": [(x2 + k, z) for z in range(z1, z2 + 1) for k in (1, 2, 3)]}
        for side, cells in strips.items():
            scores[side] = sum(self.paved(x, z) for x, z in cells) + (0.5 if side == "north" else 0)
        return max(scores, key=scores.get)

    # -------------------------------------------------------------- lot growth
    def grow_xz(self, m):
        if m <= 0:
            return
        bp = self.bp
        nsx, nsz = bp.sx + 2 * m, bp.sz + 2 * m
        grid = []
        for y in range(bp.sy):
            layer = []
            for z in range(nsz):
                row = []
                for x in range(nsx):
                    ox, oz = x - m, z - m
                    if 0 <= ox < bp.sx and 0 <= oz < bp.sz:
                        row.append(bp.grid[y][oz][ox])
                    elif y < self.gy:
                        row.append(SOLID_SUB)
                    elif y == self.gy:
                        row.append(MC + "grass_block[snowy=false]")
                    else:
                        row.append(AIR)
                layer.append(row)
            grid.append(layer)
        bp.grid, bp.sx, bp.sz = grid, nsx, nsz
        bp.tile_entities = {(x + m, y, z + m): te for (x, y, z), te in bp.tile_entities.items()}
        ox, oy, oz = bp.primary_offset
        bp.primary_offset = (ox + m, oy, oz + m)
        for te in bp.tile_entities.values():
            bdp = te.get("blueprintDataProvider")
            if bdp is None:
                continue
            c1, c2 = bdp["corner1"], bdp["corner2"]
            if all(int(c[k]) == 0 for c in (c1, c2) for k in "xyz"):
                continue
            for k in "xz":
                c1[k] = type(c1[k])(int(c1[k]) - m)
                c2[k] = type(c2[k])(int(c2[k]) + m)
        self.protect = {(x + m, y, z + m) for x, y, z in self.protect}
        self.sensitive = {(x + m, y, z + m) for x, y, z in self.sensitive}
        self.tags = {(x + m, y, z + m): v for (x, y, z), v in self.tags.items()}

    def ensure_height(self, top):
        if top >= self.bp.sy - 1:
            self.grow(top - self.bp.sy + 2)

    # -------------------------------------------------------------- elements
    def footprint(self, cx, cz, r, shape):
        cells = set()
        for x in range(cx - r - 1, cx + r + 2):
            for z in range(cz - r - 1, cz + r + 2):
                dx, dz = x - cx, z - cz
                if shape == "square" and max(abs(dx), abs(dz)) <= r:
                    cells.add((x, z))
                elif shape == "round" and math.hypot(dx, dz) < r + 0.5:
                    cells.add((x, z))
                elif shape in ("octagon", "stepped") and max(abs(dx), abs(dz)) <= r and abs(dx) + abs(dz) <= r * 1.5:
                    cells.add((x, z))
        return cells

    def area_ok(self, cells, y1, y2):
        return all(self.free(x, y, z) or (y == self.gy) for x, z in cells for y in (y1, y2)) \
            and not any(self.paved(x, z) for x, z in cells)

    def tower(self, cx, cz, r, height, shape, out_dir):
        M, L, gy, bp = self.M, self.L, self.gy, self.bp
        cells = self.footprint(cx, cz, r, shape)
        if not all(bp.inside(x, gy, z) for x, z in cells) or not self.area_ok(cells, gy + 1, min(gy + height, bp.sy - 1)):
            return False
        top = gy + height
        self.ensure_height(top + (9 if L == 5 else 4))
        shell = {(x, z) for x, z in cells if any((x + dx, z + dz) not in cells for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
        inner = cells - shell
        # door on the outward face
        odx, odz = out_dir
        door = max(shell, key=lambda c: (c[0] - cx) * odx + (c[1] - cz) * odz - 0.01 * abs((c[0] - cx) * odz + (c[1] - cz) * odx))
        ladder = min(inner, key=lambda c: (c[0] - cx) * odx + (c[1] - cz) * odz) if inner else None
        step = 1 if shape == "stepped" else 0
        for y in range(gy + 1, top + 1):
            k = y - gy
            shrink = step and k > height * 0.6
            for x, z in cells:
                if shrink and (x, z) in shell:
                    continue
                if (x, z) in shell or (shrink and (x, z) in inner and any(
                        (x + dx, z + dz) in shell for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))):
                    if (x, z) == door and k <= 2:
                        s = "air"
                    elif k % 6 == 0:
                        s = M["light"] if L >= 5 else M["accent"]
                    elif k % 6 in (2, 3, 4) and (x + z) % 2 == 0:
                        s = M["glass"]
                    elif (x, z) in shell and abs(x - cx) + abs(z - cz) == max(abs(a - cx) + abs(b - cz) for a, b in shell):
                        s = M["fin"]
                    else:
                        s = M["wall"] if (y // 3 + x + z) % 5 else M["wall2"]
                    self.place(x, y, z, s)
                else:
                    if k % 5 == 0 and (x, z) != ladder:
                        self.place(x, y, z, M["deck"])
                    else:
                        self.place(x, y, z, "air")
            if ladder:
                lx, lz = ladder
                # ladder faces away from the wall it hangs on
                face = {(1, 0): "west", (-1, 0): "east", (0, 1): "north", (0, -1): "south"}
                wall_dir = next(((dx, dz) for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)) if (lx + dx, lz + dz) in shell),
                                (-odx, -odz))
                self.place(lx, y, lz, f"ladder[facing={face[wall_dir]},waterlogged=false]")
        # cap
        for x, z in cells:
            self.place(x, top + 1, z, M["accent"] if (x, z) in shell else M["roof"])
        if ladder:
            self.place(ladder[0], top + 1, ladder[1], self.get(ladder[0], top, ladder[1]))
        if L >= 4:
            for x, z in shell:
                pane = M["glass"].replace("_glass", "_glass_pane") if "stained" in M["glass"] else "glass_pane"
                self.place(x, top + 2, z, pane)
        if L == 5:
            for i in range(1, 6):
                self.place(cx, top + 1 + i, cz, M["fin"] if i < 5 else M["light"])
            self.place(cx, top + 7, cz, "end_rod[facing=up]")
            self.place(cx, top + 8, cz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        elif L >= 3:
            self.place(cx, top + 2, cz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        return True

    def colonnade(self, box, side, depth, arches):
        M, L, gy = self.M, self.L, self.gy
        x1, x2, z1, z2 = box[:4]
        horiz = side in ("north", "south")
        a, b = (x1, x2) if horiz else (z1, z2)
        sgn = -1 if side in ("north", "west") else 1
        base = (z1 if side == "north" else z2) if horiz else (x1 if side == "west" else x2)
        roof_y = gy + 5
        built = 0
        for u in range(a, b + 1):
            for d in range(1, depth + 1):
                w = base + sgn * d
                x, z = (u, w) if horiz else (w, u)
                if not self.bp.inside(x, roof_y, z):
                    continue
                if self.place(x, roof_y, z, M["light"] if (d == depth and L >= 4 and u % 2 == 0) else
                              (M["accent"] if d == depth else M["roof"])):
                    built += 1
                if d == depth and (u - a) % 3 == 0 and not self.paved(x, z):
                    for y in range(gy + 1, roof_y):
                        self.place(x, y, z, M["fin"])
                if arches and d == depth and (u - a) % 3 in (1, 2):
                    facing = ("east" if (u - a) % 3 == 1 else "west") if horiz else ("south" if (u - a) % 3 == 1 else "north")
                    self.place(x, roof_y - 1, z, f"smooth_quartz_stairs[facing={facing},half=top,shape=straight,waterlogged=false]"
                               if L >= 4 else f"polished_diorite_stairs[facing={facing},half=top,shape=straight,waterlogged=false]")
        return built > 0

    def wing(self, box, side, depth, storeys, style):
        M, L, gy, bp = self.M, self.L, self.gy, self.bp
        x1, x2, z1, z2 = box[:4]
        horiz = side in ("north", "south")
        a, b = (x1 + 3, x2 - 3) if horiz else (z1 + 3, z2 - 3)
        if b - a < 4:
            return False
        sgn = -1 if side in ("north", "west") else 1
        base = (z1 if side == "north" else z2) if horiz else (x1 if side == "west" else x2)

        def xz(u, d):
            w = base + sgn * d
            return (u, w) if horiz else (w, u)
        cells = [xz(u, d) for u in range(a, b + 1) for d in range(1, depth + 1)]
        if not all(bp.inside(x, gy, z) for x, z in cells):
            return False
        if any(self.paved(x, z) for x, z in cells) or not all(self.free(x, gy + 1, z) for x, z in cells):
            return False
        H = 5 * storeys
        self.ensure_height(gy + H + 4)
        mid = (a + b) // 2
        for u in range(a, b + 1):
            for d in range(1, depth + 1):
                x, z = xz(u, d)
                outer = d == depth
                end = u in (a, b)
                roof_h = H
                if style == "stepped":
                    roof_h = H - (d - 1) * 2 // max(1, depth // 2) if storeys > 1 else H
                    roof_h = max(5, roof_h)
                self.place(x, gy, z, M["deck"])
                for y in range(gy + 1, gy + roof_h):
                    k = y - gy
                    if outer or end:
                        door = (end and u in (a, b) and d == depth // 2 + 1 and k <= 2) or \
                               (outer and u == mid and k <= 2)
                        if door:
                            s = "air"
                        elif k % 5 == 0:
                            s = M["accent"]
                        elif (u - a) % 3 == 0:
                            s = M["fin"]
                        elif k % 5 in (2, 3, 4):
                            s = M["glass"]
                        else:
                            s = M["wall"]
                    elif k % 5 == 0:
                        s = M["deck"]
                    else:
                        s = "air"
                    self.place(x, y, z, s)
                ry = gy + roof_h
                if style == "sawtooth" and (u - a) % 3 == 0:
                    self.place(x, ry, z, M["glass"])
                    self.place(x, ry + 1, z, M["accent"])
                else:
                    self.place(x, ry, z, M["accent"] if (outer or end) else M["roof"])
                if outer or end:
                    self.place(x, ry + 1, z, "glass_pane")
        if storeys > 1:      # ladder to the upper floor, inside next to the core wall
            lx, lz = xz(a + 1, 1)
            facing = {"north": "north", "south": "south", "west": "west", "east": "east"}[side]
            for y in range(gy + 1, gy + H):
                self.place(lx, y, lz, f"ladder[facing={facing},waterlogged=false]")
        # light the hall
        for u in range(a + 2, b - 1, 4):
            x, z = xz(u, (depth + 1) // 2)
            for s_ in range(storeys):
                self.place(x, gy + 4 + 5 * s_, z, "lantern[hanging=true,waterlogged=false]")
        return True

    def plaza(self, box, side, size):
        M, gy = self.M, self.gy
        x1, x2, z1, z2 = box[:4]
        horiz = side in ("north", "south")
        cu = (x1 + x2) // 2 if horiz else (z1 + z2) // 2
        sgn = -1 if side in ("north", "west") else 1
        base = (z1 if side == "north" else z2) if horiz else (x1 if side == "west" else x2)
        off = 4
        cw = base + sgn * (off + size // 2)
        cx, cz = (cu, cw) if horiz else (cw, cu)
        for dx in range(-size // 2, size // 2 + 1):
            for dz in range(-size // 2, size // 2 + 1):
                x, z = cx + dx, cz + dz
                if not self.bp.inside(x, gy, z):
                    return False
        for dx in range(-size // 2, size // 2 + 1):
            for dz in range(-size // 2, size // 2 + 1):
                x, z = cx + dx, cz + dz
                if (x, gy, z) in self.protect:
                    continue
                d = max(abs(dx), abs(dz))
                if self.n(x, gy, z) in ("grass_block", "dirt") and self.free(x, gy + 1, z):
                    self.bp.set(x, gy, z, MC + (M["accent"] if d == size // 2 or (dx == 0 or dz == 0) else M["deck"]))
                if d <= 1:
                    if d == 1:
                        self.place(x, gy + 1, z, M["wall"])
                    else:
                        self.bp.set(x, gy, z, MC + "water[level=0]") if (x, gy, z) not in self.protect else None
        self.place(cx, gy + 1, cz, "air")
        for dx, dz in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            self.place(cx + dx, gy + 2, cz + dz, M["light"] if self.L >= 4 else "lantern[hanging=false,waterlogged=false]")
        return True

    # -------------------------------------------------------------- plan
    def run(self):
        L = self.L
        if L < 2:
            return []
        c = self.core()
        if c is None:
            return []
        x1, x2, z1, z2, top = c
        core_h = top - self.gy
        front = self.front_side(c)
        opp = {"north": "south", "south": "north", "east": "west", "west": "east"}
        sides = {"north", "south", "east", "west"}
        lateral = sorted(sides - {front, opp[front]})
        back = opp[front]
        v = h("variant", self.base)
        shape = ["square", "round", "octagon", "stepped"][int(v * 4)]
        wstyle = ["glass", "stepped", "sawtooth"][int(h("wing", self.base) * 3)]
        arches = h("arch", self.base) < .5
        r = 2 if L <= 4 else 3
        # make room
        need = {2: 4, 3: 2 * r + 3, 4: 2 * r + 5, 5: 2 * r + 6}[L]
        avail = min(x1, z1, self.bp.sx - 1 - x2, self.bp.sz - 1 - z2)
        m = max(0, need - avail)
        self.grow_xz(m)
        x1, x2, z1, z2 = x1 + m, x2 + m, z1 + m, z2 + m
        box = (x1, x2, z1, z2, top)
        added = []

        def try_(label, fn):
            res = []
            if self.guarded(lambda: res.append(fn())) and res and res[0]:
                added.append(label)

        try_("canopy" if L == 2 else "colonnade",
             lambda: self.colonnade(box, front, 2 if L == 2 else 3, arches and L >= 3))
        if L >= 3:
            corners = {"north": (z1 - 1 - r), "south": (z2 + 1 + r), "west": (x1 - 1 - r), "east": (x2 + 1 + r)}
            pts = []
            for sx_ in ("west", "east"):
                for sz_ in ("north", "south"):
                    is_back = back in (sx_, sz_)
                    if L == 3 and not is_back:
                        continue
                    pts.append(((corners[sx_], corners[sz_]),
                                (1 if sx_ == "east" else -1, 1 if sz_ == "south" else -1)))
            th = {3: max(8, int(core_h * .6)), 4: max(10, int(core_h * .9)), 5: core_h + 6}[L]
            for (cx, cz), out in pts:
                try_("tower", lambda cx=cx, cz=cz, out=out: self.tower(cx, cz, r, th, shape, out))
        if L >= 4:
            for s in lateral + ([back] if L == 5 else []):
                try_(f"{wstyle} wing", lambda s=s: self.wing(box, s, 5 if L == 4 else 6, 1 if L == 4 else 2, wstyle))
        if L == 5:
            try_("plaza", lambda: self.plaza(box, front, 7))
        return added


def kind_level(path: Path):
    p = path.as_posix()
    m = re.search(r"(\d+)\.blueprint$", path.name)
    if not m or any(k in p for k in ("/mineshafts/", "/supplies/", "/fields/", "/walls/", "/infrastructure/",
                                     "/parks/")):
        return None
    if any(k in path.name for k in ("bunker", "skytower", "barracks", "miner", "fisherman", "gatehouse",
                                    "wallguardtower", "plantation", "tavern")):
        return None       # parents with child huts, tunnels, ponds, wall-bound pieces: keep their exact frame
    lvl = int(m.group(1))
    return lvl if 1 <= lvl <= 5 else None


def process(path_str):
    path = Path(path_str)
    L = kind_level(path)
    if not L:
        return f"{path.name}: kept"
    bp = load(path)
    import themes
    if themes.recipe(path.stem):
        from signature import Signature
        ms = Signature(bp, L, path.stem)
    else:
        ms = Massing(bp, L, path.stem)
    added = ms.run()
    if L <= 3:
        for x, y, z, s in bp.blocks():
            assert (x, y, z) in ms.protect or not any(w in s for w in CHEAP_FORBIDDEN), f"{path.name}: {s}"
    bp.save(path)
    return f"{path.name}: L{L} +{', '.join(added) or 'nothing'} -> {bp.sx}x{bp.sy}x{bp.sz}"


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
