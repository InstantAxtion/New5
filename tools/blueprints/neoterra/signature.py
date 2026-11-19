"""
Neoterra signature modules – the landmark features that give every building its own identity.

Each building's recipe (themes.BUILDINGS) lists modules and the level they appear at; they stay
and grow on later levels (taller, more of them). Modules are drawn in the building's own theme
(themes.THEMES): cheap blocks on levels 1-3, premium ones on 4-5.

  yard modules    placed on free lawn beside the main building (never on paths):
                  clock_tower bell_tower lighthouse watchpost silos water_tower wind_turbines
                  radar_dish observatory greenhouse_dome forge_tower twisted_tower chimneys
                  gantry crate_yard log_stacks solar_canopy pergola ziggurat amphitheater
                  sculpture honeycomb_pillars glass_atrium helipad sky_bridge
  front modules   arch_gate (spans the entrance path), reflecting_pool (flanks it)
  facade modules  hanging_gardens, cantilever_pods
  lot modules     obelisks (lot corners)
"""
from __future__ import annotations

import math

from detail import h
from massing import Massing
import themes

CHEAP = ("quartz", "deepslate", "sea_lantern", "stained_glass", "end_rod", "domum")


class Signature(Massing):
    def __init__(self, bp, level, name):
        super().__init__(bp, level, name)
        self.T = themes.theme(name)
        self.R = themes.recipe(name)
        self.used = []                      # rects already taken by modules (x1, x2, z1, z2)

    # -------------------------------------------------------------- theme access
    @property
    def cheap(self):
        return self.L <= 3

    def t(self, key, i=0):
        v = self.T[f"{key}_{'c' if self.cheap else 'p'}"]
        return v[i % len(v)] if isinstance(v, list) else v

    def light(self):
        lt = self.t("light")
        return f"{lt}[hanging=false,waterlogged=false]" if lt in ("lantern", "soul_lantern") else lt

    def glass(self, i=0):
        return "glass" if self.cheap else self.T["glass_p"][i % len(self.T["glass_p"])]

    def pane(self, i=0):
        g = self.glass(i)
        return "glass_pane" if g == "glass" else g.replace("_glass", "_glass_pane")

    def white(self):
        return "white_concrete" if self.cheap else "smooth_quartz"

    def stair(self, facing, half="bottom"):
        base = "polished_diorite" if self.cheap else "smooth_quartz"
        return f"{base}_stairs[facing={facing},half={half},shape=straight,waterlogged=false]"

    # -------------------------------------------------------------- placement
    def lawn(self, x, z):
        return (self.bp.inside(x, self.gy, z) and not self.paved(x, z)
                and all(self.free(x, y, z) for y in (self.gy + 1, self.gy + 2, self.gy + 3)))

    def find_spot(self, w, d, box, sides, gap=2):
        x1, x2, z1, z2 = box[:4]
        for side in sides:
            horiz = side in ("north", "south")
            span = (x1, x2) if horiz else (z1, z2)
            length = w if horiz else d
            depth = d if horiz else w
            mid = (span[0] + span[1]) // 2
            offsets = sorted(range(span[0] - length - 2, span[1] + 3), key=lambda u: abs(u + length // 2 - mid))
            for u in offsets:
                if side == "north":
                    r = (u, u + w - 1, z1 - gap - d, z1 - gap - 1)
                elif side == "south":
                    r = (u, u + w - 1, z2 + gap + 1, z2 + gap + d)
                elif side == "west":
                    r = (x1 - gap - w, x1 - gap - 1, u, u + d - 1)
                else:
                    r = (x2 + gap + 1, x2 + gap + w, u, u + d - 1)
                if self.rect_ok(r):
                    return r
        return None

    def rect_ok(self, r):
        x1, x2, z1, z2 = r
        for a in self.used:
            if not (x2 + 1 < a[0] or a[1] + 1 < x1 or z2 + 1 < a[2] or a[3] + 1 < z1):
                return False
        return all(self.lawn(x, z) for x in range(x1, x2 + 1) for z in range(z1, z2 + 1))

    def yard(self, w, d, box, sides, builder):
        r = self.find_spot(w, d, box, sides)
        if r is None:
            return False
        self.used.append(r)
        self.ensure_height(self.gy + self.core_h + 24)
        builder(r)
        return True

    # -------------------------------------------------------------- shapes
    def column(self, x, z, y1, y2, s):
        for y in range(y1, y2 + 1):
            self.place(x, y, z, s)

    def ring(self, cx, cz, r, y, s, fill=None):
        for x in range(cx - r - 1, cx + r + 2):
            for z in range(cz - r - 1, cz + r + 2):
                d = math.hypot(x - cx, z - cz)
                if r - .5 <= d < r + .5:
                    self.place(x, y, z, s)
                elif fill and d < r - .5:
                    self.place(x, y, z, fill)

    def cylinder(self, cx, cz, r, y1, y2, wall_fn, floor=None):
        for y in range(y1, y2 + 1):
            for x in range(cx - r - 1, cx + r + 2):
                for z in range(cz - r - 1, cz + r + 2):
                    d = math.hypot(x - cx, z - cz)
                    if r - .5 <= d < r + .5:
                        self.place(x, y, z, wall_fn(x, y, z))
                    elif d < r - .5 and floor and y == y1:
                        self.place(x, y, z, floor)

    def dome(self, cx, cz, r, y0, s_fn):
        for k in range(r + 1):
            rr = math.sqrt(max(0.0, (r + .5) ** 2 - k * k))
            for x in range(cx - r - 1, cx + r + 2):
                for z in range(cz - r - 1, cz + r + 2):
                    d = math.hypot(x - cx, z - cz)
                    if rr - 1.1 <= d < rr:
                        self.place(x, y0 + k, z, s_fn(x, y0 + k, z))

    def cap(self, x, y, z):
        self.place(x, y, z, self.light())
        self.place(x, y + 1, z, "lightning_rod[facing=up,powered=false,waterlogged=false]")

    # ================================================================ modules
    def m_clock_tower(self, box, **_):
        H = self.core_h + 4 + self.L

        def b(r):
            x1, x2, z1, z2 = r
            cx, cz = (x1 + x2) // 2, (z1 + z2) // 2
            gy = self.gy
            for y in range(gy + 1, gy + H + 1):
                for x in range(x1, x2 + 1):
                    for z in range(z1, z2 + 1):
                        e = x in (x1, x2) or z in (z1, z2)
                        corner = x in (x1, x2) and z in (z1, z2)
                        if not e:
                            self.place(x, y, z, "air")
                            continue
                        door = (z == z2 and x == cx and y <= gy + 2)
                        self.place(x, y, z, "air" if door else self.t("trim") if corner else
                                   (self.glass() if (y - gy) % 4 == 2 and (x + z) % 2 else self.t("feature")))
            fy = gy + H - 3                                    # clock faces on all four sides
            for (fx, fz, ax) in ((cx, z1 - 1, "x"), (cx, z2 + 1, "x"), (x1 - 1, cz, "z"), (x2 + 1, cz, "z")):
                for a in (-1, 0, 1):
                    for b_ in (-1, 0, 1):
                        x, z = (fx + a, fz) if ax == "x" else (fx, fz + a)
                        self.place(x, fy + b_, z, "black_concrete" if a == 0 and b_ >= 0 else
                                   ("white_concrete" if (a + b_) % 2 else self.t("accent")))
            for i in range(3):                                 # stepped pyramid cap
                for x in range(x1 + i, x2 - i + 1):
                    for z in range(z1 + i, z2 - i + 1):
                        if x in (x1 + i, x2 - i) or z in (z1 + i, z2 - i):
                            self.place(x, gy + H + 1 + i, z, self.t("accent", i))
            self.cap(cx, gy + H + 4, cz)
            for y in range(gy + 1, gy + H + 1):
                self.place(cx, y, z1 + 1, "ladder[facing=south,waterlogged=false]")
        return self.yard(5, 5, box, self.sides_back, b)

    def m_bell_tower(self, box, **_):
        H = 9 + 2 * self.L

        def b(r):
            x1, x2, z1, z2 = r
            cx, cz = x1 + 1, z1 + 1
            for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
                self.column(x, z, self.gy + 1, self.gy + H, self.t("trim"))
            for y in (self.gy + H // 2, self.gy + H):
                for x in range(x1, x2 + 1):
                    for z in range(z1, z2 + 1):
                        if x in (x1, x2) or z in (z1, z2):
                            self.place(x, y, z, self.t("accent"))
            for x in range(x1, x2 + 1):
                for z in range(z1, z2 + 1):
                    self.place(x, self.gy + H + 1, z, self.t("feature"))
            self.place(cx, self.gy + H, cz, "bell[attachment=ceiling,facing=north,powered=false]")
            self.place(cx, self.gy + H + 2, cz, self.t("feature"))
            self.cap(cx, self.gy + H + 3, cz)
        return self.yard(3, 3, box, self.sides_side, b)

    def m_lighthouse(self, box, **_):
        H = self.core_h + 8 + self.L

        def b(r):
            x1, _, z1, _ = r
            cx, cz = x1 + 2, z1 + 2
            gy = self.gy
            self.cylinder(cx, cz, 2, gy + 1, gy + H,
                          lambda x, y, z: self.t("accent") if (y - gy) // 3 % 2 else self.white(), floor=None)
            for y in range(gy + 1, gy + H + 1):
                self.place(cx, y, cz, "air")
                self.place(cx, y, cz - 1, "ladder[facing=south,waterlogged=false]")
            self.place(cx, gy + 1, cz + 2, "air")
            self.place(cx, gy + 2, cz + 2, "air")
            self.ring(cx, cz, 3, gy + H + 1, self.t("trim"), fill=self.t("feature"))
            self.ring(cx, cz, 3, gy + H + 2, "iron_bars[east=false,north=false,south=false,waterlogged=false,west=false]")
            self.cylinder(cx, cz, 1, gy + H + 2, gy + H + 4, lambda *_: self.glass())
            self.place(cx, gy + H + 2, cz, self.light())
            self.place(cx, gy + H + 3, cz, self.light())
            self.ring(cx, cz, 1, gy + H + 5, self.t("accent"), fill=self.t("accent"))
            self.cap(cx, gy + H + 6, cz)
        return self.yard(5, 5, box, self.sides_side, b)

    def m_watchpost(self, box, **_):
        H = 9 + self.L

        def b(r):
            x1, x2, z1, z2 = r
            for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
                self.column(x, z, self.gy + 1, self.gy + H, self.t("trim"))
            for x in range(x1, x2 + 1):
                for z in range(z1, z2 + 1):
                    self.place(x, self.gy + H, z, self.t("feature"))
                    if x in (x1, x2) or z in (z1, z2):
                        self.place(x, self.gy + H + 1, z, self.pane())
                        self.place(x, self.gy + H + 2, z, self.pane())
                    self.place(x, self.gy + H + 3, z, self.t("accent"))
            for y in range(self.gy + 1, self.gy + H + 1):
                self.place(x1 + 1, y, z1, "ladder[facing=south,waterlogged=false]")
            self.cap(x1 + 1, self.gy + H + 4, z1 + 1)
        return self.yard(3, 3, box, self.sides_side, b)

    def m_silos(self, box, n=2, **_):
        n = min(n + (self.L >= 4), 4)

        def b(r):
            x1, x2, z1, z2 = r
            tops = []
            for i in range(n):
                cx, cz = x1 + 2 + 5 * i, z1 + 2
                H = 9 + 2 * self.L + (i % 2) * 3
                self.cylinder(cx, cz, 2, self.gy + 1, self.gy + H,
                              lambda x, y, z, i=i: self.t("accent", i) if (y - self.gy) % 5 == 0 else self.t("feature"))
                self.dome(cx, cz, 2, self.gy + H + 1, lambda *_: self.t("accent", i + 1))
                self.cap(cx, self.gy + H + 4, cz)
                tops.append((cx, cz, H))
            if n > 1:                                      # catwalk between silo tops
                y = self.gy + min(t[2] for t in tops)
                for x in range(tops[0][0], tops[-1][0] + 1):
                    self.place(x, y, z1 + 2, self.t("trim"))
                    self.place(x, y + 1, z1 + 1, "chain[axis=y,waterlogged=false]")
        return self.yard(5 * n, 5, box, self.sides_back, b)

    def m_water_tower(self, box, **_):
        H = 8 + self.L

        def b(r):
            x1, x2, z1, z2 = r
            cx, cz = x1 + 2, z1 + 2
            for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
                self.column(x, z, self.gy + 1, self.gy + H, self.t("trim"))
            for y in range(self.gy + 3, self.gy + H, 3):
                for x in range(x1, x2 + 1):
                    for z in range(z1, z2 + 1):
                        if (x in (x1, x2) or z in (z1, z2)) and not (x in (x1, x2) and z in (z1, z2)):
                            self.place(x, y, z, "chain[axis=x,waterlogged=false]" if z in (z1, z2)
                                       else "chain[axis=z,waterlogged=false]")
            self.cylinder(cx, cz, 2, self.gy + H + 1, self.gy + H + 4,
                          lambda x, y, z: self.t("accent", y) , floor=self.t("feature"))
            for i in range(3):
                self.ring(cx, cz, 2 - i, self.gy + H + 5 + i, self.t("trim"), fill=self.t("trim"))
            self.cap(cx, self.gy + H + 8, cz)
            for y in range(self.gy + 1, self.gy + H + 1):
                self.place(x1 + 1, y, z1, "ladder[facing=north,waterlogged=false]")
        return self.yard(5, 5, box, self.sides_back, b)

    def m_wind_turbines(self, box, **_):
        n = 2 if self.L < 5 else 3
        H = 11 + 2 * self.L

        def b(r):
            x1, _, z1, _ = r
            for i in range(n):
                x, z = x1 + 1 + 4 * i, z1 + 1
                self.column(x, z, self.gy + 1, self.gy + H, self.white())
                self.place(x, self.gy + H + 1, z, self.t("accent"))
                hub = self.gy + H + 1
                for k in range(1, 5):                          # three blades: up, down-left, down-right
                    self.place(x, hub + k, z - 1, self.white())
                    if k <= 3:
                        self.place(x - k, hub - k // 2 - 1, z - 1, self.white())
                        self.place(x + k, hub - k // 2 - 1, z - 1, self.white())
                self.place(x, hub, z - 1, self.t("accent", 1))
        return self.yard(4 * n - 1, 3, box, self.sides_side, b)

    def m_radar_dish(self, box, **_):
        H = 7 + self.L

        def b(r):
            x1, _, z1, _ = r
            cx, cz = x1 + 3, z1 + 3
            for dx, dz in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
                self.column(cx + dx, cz + dz, self.gy + 1, self.gy + H, self.t("trim"))
            for x in range(cx - 3, cx + 4):                    # bowl
                for z in range(cz - 3, cz + 4):
                    d = math.hypot(x - cx, z - cz)
                    if d < 3.5:
                        self.place(x, self.gy + H + 1 + int(d * d / 5), z, self.white() if d > 1 else self.t("accent"))
            self.column(cx, cz, self.gy + H + 2, self.gy + H + 4, "iron_bars[east=false,north=false,south=false,waterlogged=false,west=false]")
            self.cap(cx, self.gy + H + 5, cz)
        return self.yard(7, 7, box, self.sides_side, b)

    def m_observatory(self, box, **_):
        def b(r):
            x1, _, z1, _ = r
            cx, cz = x1 + 3, z1 + 3
            gy = self.gy
            self.cylinder(cx, cz, 3, gy + 1, gy + 5,
                          lambda x, y, z: self.glass() if y == gy + 3 and (x + z) % 2 else self.t("feature"), floor=None)
            for y in (gy + 1, gy + 2):
                self.place(cx, y, cz + 3, "air")
            self.dome(cx, cz, 3, gy + 6, lambda x, y, z: "air" if x == cx and z <= cz else self.t("accent", y))
            for k in range(4):                                  # telescope poking through the slit
                self.place(cx, gy + 6 + k, cz - k // 2, "iron_block" if not self.cheap else "light_gray_concrete")
            self.place(cx, gy + 10, cz - 2, "end_rod[facing=up]" if not self.cheap else "lightning_rod[facing=up,powered=false,waterlogged=false]")
        return self.yard(7, 7, box, self.sides_back, b)

    def m_greenhouse_dome(self, box, **_):
        r_ = 3 + (self.L >= 4)

        def b(r):
            x1, _, z1, _ = r
            cx, cz = x1 + r_, z1 + r_
            gy = self.gy
            for x in range(cx - r_, cx + r_ + 1):
                for z in range(cz - r_, cz + r_ + 1):
                    if math.hypot(x - cx, z - cz) < r_ - .5 and (x, gy, z) not in self.protect:
                        self.bp.set(x, gy, z, "minecraft:grass_block[snowy=false]")
            self.dome(cx, cz, r_, gy + 1, lambda x, y, z: self.t("trim") if (x - cx) % 3 == 0 or (z - cz) % 3 == 0
                      else self.glass(x + z))
            self.place(cx, gy + 1, cz + r_, "air")
            self.place(cx, gy + 2, cz + r_, "air")
            for k in range(3):
                self.place(cx, gy + 1 + k, cz, "stripped_birch_log[axis=y]")
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    self.place(cx + dx, gy + 4, cz + dz, "flowering_azalea_leaves[distance=1,persistent=true,waterlogged=false]")
            for dx, dz in ((-2, 0), (2, 0), (0, -2), (-2, -2), (2, -2)):
                self.place(cx + dx, gy + 1, cz + dz, ["fern", "azure_bluet", "cornflower", "allium", "poppy"][(dx + dz) % 5])
        return self.yard(2 * r_ + 1, 2 * r_ + 1, box, self.sides_back, b)

    def m_forge_tower(self, box, **_):
        H = self.core_h + 3 + self.L

        def b(r):
            x1, x2, z1, z2 = r
            cx, cz = x1 + 2, z1 + 2
            gy = self.gy
            for y in range(gy + 1, gy + H + 1):
                for x in range(x1, x2 + 1):
                    for z in range(z1, z2 + 1):
                        e = x in (x1, x2) or z in (z1, z2)
                        if e:
                            win = (x == cx or z == cz) and (y - gy) % 4 in (1, 2)
                            self.place(x, y, z, "iron_bars[east=false,north=false,south=false,waterlogged=false,west=false]"
                                       if win else self.t("feature"))
                        else:
                            self.place(x, y, z, "magma_block" if (x == cx and z == cz) else "air")
            for x in range(x1 - 1, x2 + 2):
                for z in range(z1 - 1, z2 + 2):
                    if x in (x1 - 1, x2 + 1) or z in (z1 - 1, z2 + 1):
                        self.place(x, gy + H + 1, z, self.t("accent"))
            for dx, dz in ((0, 0), (1, 1), (-1, -1)):
                self.column(cx + dx, cz + dz, gy + H + 1, gy + H + 3 + (dx == 0) * 2, self.t("trim"))
                self.place(cx + dx, gy + H + 4 + (dx == 0) * 2, cz + dz,
                           "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        return self.yard(5, 5, box, self.sides_back, b)

    def m_twisted_tower(self, box, **_):
        H = self.core_h + 6

        def b(r):
            x1, _, z1, _ = r
            cx, cz = x1 + 3, z1 + 3
            gy = self.gy
            for y in range(gy + 1, gy + H + 1):
                k = (y - gy) // 2 % 4
                for x in range(cx - 3, cx + 4):
                    for z in range(cz - 3, cz + 4):
                        dx, dz = x - cx, z - cz
                        # alternate a square plate and a diamond plate every two blocks -> twisting silhouette
                        inside = (max(abs(dx), abs(dz)) <= 2) if k % 2 == 0 else (abs(dx) + abs(dz) <= 3)
                        edge = inside and ((max(abs(dx), abs(dz)) == 2) if k % 2 == 0 else (abs(dx) + abs(dz) == 3))
                        if edge:
                            slab = (y - gy) % 2 == 0
                            self.place(x, y, z, self.t("accent", k) if slab else self.glass(k))
                        elif inside:
                            self.place(x, y, z, self.t("feature") if (y - gy) % 6 == 0 else "air")
            for y in range(gy + 1, gy + H + 1):
                self.place(cx, y, cz, self.t("trim"))
            self.place(cx, gy + 1, cz + 2, "air")
            self.place(cx, gy + 2, cz + 2, "air")
            self.cap(cx, gy + H + 1, cz)
        return self.yard(7, 7, box, self.sides_side, b)

    def m_chimneys(self, box, n=2, **_):
        x1, x2, z1, z2, top = box
        H = top - self.gy + 3 + self.L
        placed = 0
        for i, (x, z) in enumerate([(x1 - 2, z1 + 2), (x2 + 1, z2 - 3), (x1 - 2, z2 - 3), (x2 + 1, z1 + 2)]):
            if placed >= n:
                break
            if not all(self.lawn(x + dx, z + dz) for dx in (0, 1) for dz in (0, 1)):
                continue
            self.ensure_height(self.gy + H + 4)
            for y in range(self.gy + 1, self.gy + H + 1):
                for dx in (0, 1):
                    for dz in (0, 1):
                        self.place(x + dx, y, z + dz, self.t("accent") if (y - self.gy) % 5 == 0 else self.t("feature"))
            self.place(x, self.gy + H + 1, z, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
            placed += 1
        return placed > 0

    def m_gantry(self, box, **_):
        H = 8 + self.L

        def b(r):
            x1, x2, z1, z2 = r
            for x in (x1, x2):
                for z in (z1, z2):
                    self.column(x, z, self.gy + 1, self.gy + H, self.t("trim"))
            for x in range(x1, x2 + 1):
                for z in (z1, z2):
                    self.place(x, self.gy + H + 1, z, self.t("accent"))
            mid = (x1 + x2) // 2
            for z in range(z1, z2 + 1):
                self.place(mid, self.gy + H + 1, z, self.t("accent", 1))
            for y in range(self.gy + 4, self.gy + H + 1):
                self.place(mid, y, (z1 + z2) // 2, "chain[axis=y,waterlogged=false]")
            self.place(mid, self.gy + 3, (z1 + z2) // 2, "barrel[facing=up,open=false]")
            for x in range(x1 + 1, x2, 2):
                self.place(x, self.gy + 1, z1 + 1, "barrel[facing=up,open=false]")
        return self.yard(9, 5, box, self.sides_back, b)

    def m_crate_yard(self, box, **_):
        def b(r):
            x1, x2, z1, z2 = r
            for x in range(x1, x2 + 1):
                for z in range(z1, z2 + 1):
                    if (x, self.gy, z) not in self.protect:
                        self.bp.set(x, self.gy, z, "minecraft:" + ("gravel" if self.cheap else "polished_andesite"))
                    hgt = int(h("crate", x, z) * (1 + self.L // 2))
                    if (x + z) % 3 and hgt:
                        for y in range(self.gy + 1, self.gy + 1 + hgt):
                            self.place(x, y, z, "barrel[facing=up,open=false]" if (x + y) % 2 else self.t("accent", x + z))
        return self.yard(7, 5, box, self.sides_side, b)

    def m_log_stacks(self, box, **_):
        def b(r):
            x1, x2, z1, z2 = r
            for i, z in enumerate(range(z1, z2 + 1, 2)):
                for k in range(3):
                    for x in range(x1 + k, x2 - k + 1):
                        self.place(x, self.gy + 1 + k, z, f"{'spruce' if i % 2 else 'birch'}_log[axis=x]")
        return self.yard(7, 4, box, self.sides_side, b)

    def m_solar_canopy(self, box, **_):
        def b(r):
            x1, x2, z1, z2 = r
            for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
                self.column(x, z, self.gy + 1, self.gy + 4 + (z == z2), self.t("trim"))
            for x in range(x1, x2 + 1):
                for z in range(z1, z2 + 1):
                    y = self.gy + 5 + (z - z1) * 2 // max(1, z2 - z1)
                    e = x in (x1, x2) or z in (z1, z2)
                    self.place(x, y, z, self.t("accent") if e else "daylight_detector[inverted=false,power=0]")
        return self.yard(9, 7, box, self.sides_side, b)

    def m_pergola(self, box, **_):
        def b(r):
            x1, x2, z1, z2 = r
            for x in range(x1, x2 + 1, 3):
                for z in (z1, z2):
                    self.column(x, z, self.gy + 1, self.gy + 3, self.t("trim"))
            for x in range(x1, x2 + 1):
                for z in range(z1, z2 + 1):
                    if (x, self.gy, z) not in self.protect:
                        self.bp.set(x, self.gy, z, "minecraft:" + self.t("accent"))
                    if z in (z1, z2) or x % 2 == 0:
                        self.place(x, self.gy + 4, z, "stripped_oak_log[axis=x]" if z in (z1, z2) else "stripped_oak_log[axis=z]")

            for x in range(x1 + 1, x2, 3):
                self.place(x, self.gy + 1, (z1 + z2) // 2, self.stair("south"))
        return self.yard(10, 4, box, self.sides_side, b)

    def m_ziggurat(self, box, **_):
        def b(r):
            x1, x2, z1, z2 = r
            for t in range(3):
                for x in range(x1 + 2 * t, x2 - 2 * t + 1):
                    for z in range(z1 + 2 * t, z2 - 2 * t + 1):
                        for y in range(self.gy + 1 + 2 * t, self.gy + 3 + 2 * t):
                            self.place(x, y, z, self.t("feature") if y < self.gy + 2 + 2 * t else
                                       ("grass_block[snowy=false]" if x not in (x1 + 2 * t, x2 - 2 * t) and z not in (z1 + 2 * t, z2 - 2 * t)
                                        else self.t("accent", t)))
                        if (x + z) % 3 == 0 and x not in (x1 + 2 * t, x2 - 2 * t) and z not in (z1 + 2 * t, z2 - 2 * t):
                            self.place(x, self.gy + 3 + 2 * t, z, ["poppy", "fern", "azure_bluet", "oxeye_daisy"][(x + z) % 4])
            cx, cz = (x1 + x2) // 2, (z1 + z2) // 2
            self.place(cx, self.gy + 7, cz, self.t("trim"))
            self.cap(cx, self.gy + 8, cz)
        return self.yard(9, 9, box, self.sides_back, b)

    def m_amphitheater(self, box, **_):
        def b(r):
            x1, x2, z1, z2 = r
            cx = (x1 + x2) // 2
            for x in range(x1, x2 + 1):
                for z in range(z1, z2 + 1):
                    d = math.hypot(x - cx, z - z1)
                    row = int(d) - 2
                    if d < 2.5:
                        if (x, self.gy, z) not in self.protect:
                            self.bp.set(x, self.gy, z, "minecraft:" + self.t("accent"))
                    elif 0 <= row < 4 and d <= 6.5:
                        for y in range(self.gy + 1, self.gy + 1 + row):
                            self.place(x, y, z, self.t("feature"))
                        facing = "north" if abs(x - cx) <= abs(z - z1) else ("west" if x > cx else "east")
                        self.place(x, self.gy + 1 + row, z, self.stair(facing))
        return self.yard(13, 7, box, self.sides_side, b)

    def m_sculpture(self, box, shape="ring", **_):
        def b(r):
            x1, x2, z1, z2 = r
            cx, cz = (x1 + x2) // 2, (z1 + z2) // 2
            gy = self.gy
            for x in range(cx - 1, cx + 2):
                for z in range(cz - 1, cz + 2):
                    self.place(x, gy + 1, z, self.t("trim"))
            base = gy + 2
            if shape == "ring":
                for a in range(0, 360, 8):
                    x = cx + round(4 * math.cos(math.radians(a)))
                    y = base + 4 + round(4 * math.sin(math.radians(a)))
                    self.place(x, y, cz, self.t("accent", a // 45) if a % 32 else self.light())
            elif shape == "orb":
                self.column(cx, cz, base, base + 2, self.t("trim"))
                for x in range(cx - 3, cx + 4):
                    for y in range(base + 3, base + 10):
                        for z in range(cz - 3, cz + 4):
                            d = math.sqrt((x - cx) ** 2 + (y - base - 6) ** 2 + (z - cz) ** 2)
                            if 2.4 <= d < 3.4:
                                self.place(x, y, z, self.glass(x + y) if (x + y + z) % 3 else self.t("accent"))
                            elif d < 1:
                                self.place(x, y, z, self.light())
            elif shape == "arch":
                for i in range(-4, 5):
                    hgt = int(7 - (i * i) * 7 / 16)
                    self.place(cx + i, base + hgt, cz, self.t("accent", i))
                    if abs(i) == 4:
                        self.column(cx + i, cz, base, base + hgt, self.t("feature"))
            elif shape == "cross":
                self.column(cx, cz, base, base + 7, "red_concrete")
                for dx in (-2, -1, 1, 2):
                    self.place(cx + dx, base + 5, cz, "red_concrete")
                self.place(cx, base + 8, cz, self.light())
            elif shape == "anvil":
                for x in range(cx - 1, cx + 2):
                    self.column(x, cz, base, base + 2, self.t("trim"))
                for x in range(cx - 3, cx + 4):
                    for y in (base + 3, base + 4):
                        self.place(x, y, cz, self.t("feature"))
                        self.place(x, y, cz - 1, self.t("feature"))
                self.place(cx + 4, base + 4, cz, self.t("feature"))
            elif shape == "arrow":
                self.column(cx, cz, base, base + 8, self.t("trim"))
                for k in range(3):
                    for dx in range(-k, k + 1):
                        self.place(cx + dx, base + 9 - k, cz, self.t("accent", k))
                for dx in (-2, -1, 1, 2):
                    self.place(cx + dx, base + abs(dx), cz, "white_wool")
        return self.yard(9, 5, box, self.sides_front_side, b)

    def m_honeycomb_pillars(self, box, **_):
        def b(r):
            x1, x2, z1, z2 = r
            for i, x in enumerate(range(x1, x2 + 1, 3)):
                hgt = 3 + (i * 2) % 4 + self.L // 2
                for dx in (0, 1):
                    for dz in (0, 1):
                        self.column(x + dx, z1 + 1 + dz, self.gy + 1, self.gy + hgt, "honeycomb_block")
                self.place(x, self.gy + hgt + 1, z1 + 1, "bee_nest[facing=south,honey_level=0]")
                self.place(x + 1, self.gy + 1, z2, ["dandelion", "cornflower", "allium"][i % 3])
        return self.yard(9, 4, box, self.sides_side, b)

    def m_glass_atrium(self, box, **_):
        def b(r):
            x1, x2, z1, z2 = r
            H = 7 + self.L
            for x in range(x1, x2 + 1):
                for z in range(z1, z2 + 1):
                    e = x in (x1, x2) or z in (z1, z2)
                    corner = x in (x1, x2) and z in (z1, z2)
                    if (x, self.gy, z) not in self.protect:
                        self.bp.set(x, self.gy, z, "minecraft:" + self.t("accent"))
                    for y in range(self.gy + 1, self.gy + H):
                        door = e and not corner and (x == (x1 + x2) // 2 or z == (z1 + z2) // 2) and y <= self.gy + 2
                        self.place(x, y, z, "air" if (not e or door) else (self.t("trim") if corner else self.glass(y)))
                    self.place(x, self.gy + H, z, self.t("accent") if e else self.glass(1))
            cx, cz = (x1 + x2) // 2, (z1 + z2) // 2
            self.bp.set(cx, self.gy, cz, "minecraft:grass_block[snowy=false]")
            for k in range(4):
                self.place(cx, self.gy + 1 + k, cz, "stripped_birch_log[axis=y]")
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for k in (4, 5):
                        self.place(cx + dx, self.gy + 1 + k, cz + dz, "azalea_leaves[distance=1,persistent=true,waterlogged=false]")
        return self.yard(7, 7, box, self.sides_side, b)

    def m_helipad(self, box, **_):
        H = 6

        def b(r):
            x1, x2, z1, z2 = r
            for x, z in ((x1 + 1, z1 + 1), (x2 - 1, z1 + 1), (x1 + 1, z2 - 1), (x2 - 1, z2 - 1)):
                self.column(x, z, self.gy + 1, self.gy + H - 1, self.t("trim"))
            for x in range(x1, x2 + 1):
                for z in range(z1, z2 + 1):
                    e = x in (x1, x2) or z in (z1, z2)
                    hmark = (x in (x1 + 2, x2 - 2) and z1 + 2 <= z <= z2 - 2) or (z == (z1 + z2) // 2 and x1 + 2 <= x <= x2 - 2)
                    self.place(x, self.gy + H, z, self.light() if (e and (x + z) % 3 == 0) else
                               ("yellow_concrete" if hmark else ("white_concrete" if e else "gray_concrete")))
            for y in range(self.gy + 1, self.gy + H):
                self.place(x1 + 1, y, z1, "ladder[facing=north,waterlogged=false]")
        return self.yard(9, 9, box, self.sides_side, b)

    def m_sky_bridge(self, box, **_):
        x1, x2, z1, z2, top = box
        fy = self.gy + 6

        def b(r):
            px1, px2, pz1, pz2 = r
            for x, z in ((px1, pz1), (px2, pz1), (px1, pz2), (px2, pz2)):
                self.column(x, z, self.gy + 1, fy + 4, self.t("trim"))
            for x in range(px1, px2 + 1):
                for z in range(pz1, pz2 + 1):
                    e = x in (px1, px2) or z in (pz1, pz2)
                    self.place(x, fy, z, self.t("accent"))
                    for y in range(fy + 1, fy + 4):
                        self.place(x, y, z, self.glass(y) if e else "air")
                    self.place(x, fy + 4, z, self.t("accent", 1) if e else self.glass(2))
            # bridge from pavilion to the core wall
            cz = (pz1 + pz2) // 2
            if px1 > x2:
                xs = range(x2 + 1, px1)
            else:
                xs = range(px2 + 1, x1)
            for x in xs:
                for dz in (-1, 0, 1):
                    self.place(x, fy, cz + dz, self.t("feature"))
                    if dz:
                        self.place(x, fy + 1, cz + dz, self.pane())
                self.place(x, fy + 3, cz, self.pane())
            wall_x = x2 if px1 > x2 else x1
            pav_x = px1 if px1 > x2 else px2
            for y in (fy + 1, fy + 2):
                self.place(pav_x, y, cz, "air")
                if (wall_x, y, cz) not in self.protect and not self.near_sensitive(wall_x, y, cz, 0):
                    self.bp.set(wall_x, y, cz, "minecraft:air")
            for y in range(self.gy + 1, fy + 1):
                self.place(px1 + 1, y, pz1, "ladder[facing=north,waterlogged=false]")
        sides = [s for s in ("east", "west")]
        r = self.find_spot(7, 7, box, sides, gap=4)
        if r is None:
            return False
        self.used.append(r)
        self.ensure_height(fy + 8)
        b(r)
        return True

    def m_arch_gate(self, box, **_):
        """Monumental gate over the entrance path, in front of the building."""
        x1, x2, z1, z2, _ = box
        side = self.front
        horiz = side in ("north", "south")
        sgn = -1 if side in ("north", "west") else 1
        base = (z1 if side == "north" else z2) if horiz else (x1 if side == "west" else x2)
        span = range(x1, x2 + 1) if horiz else range(z1, z2 + 1)
        for dist in range(5, 12):
            w = base + sgn * dist
            path = [u for u in span if self.paved(*((u, w) if horiz else (w, u)))]
            if not path:
                continue
            a, b_ = min(path) - 2, max(path) + 2
            if b_ - a > 13:
                continue
            H = 6 + self.L
            ok = True
            for u in (a - 1, a, b_, b_ + 1):
                x, z = (u, w) if horiz else (w, u)
                if not (self.bp.inside(x, self.gy, z) and self.free(x, self.gy + 1, z)) or self.paved(x, z):
                    ok = False
            if not ok:
                continue
            self.ensure_height(self.gy + H + 4)
            for u in range(a - 1, b_ + 2):
                x, z = (u, w) if horiz else (w, u)
                if u in (a - 1, a, b_, b_ + 1):
                    self.column(x, z, self.gy + 1, self.gy + H, self.t("feature") if u in (a, b_) else self.t("trim"))
                for y in (self.gy + H + 1, self.gy + H + 2):
                    self.place(x, y, z, self.t("accent", u) if y == self.gy + H + 2 else self.t("feature"))
            mx, mz = (((a + b_) // 2, w) if horiz else (w, (a + b_) // 2))
            self.cap(mx, self.gy + H + 3, mz)
            return True
        return False

    def m_reflecting_pool(self, box, **_):
        def b(r):
            x1, x2, z1, z2 = r
            for x in range(x1, x2 + 1):
                for z in range(z1, z2 + 1):
                    if (x, self.gy, z) in self.protect:
                        continue
                    e = x in (x1, x2) or z in (z1, z2)
                    if e:
                        self.bp.set(x, self.gy, z, "minecraft:" + self.t("trim"))
                    else:
                        self.bp.set(x, self.gy - 1, z, "minecraft:" + self.t("accent"))
                        self.bp.set(x, self.gy, z, "minecraft:water[level=0]")
            cx, cz = (x1 + x2) // 2, (z1 + z2) // 2
            for k, (x, z) in enumerate(((cx, z1 + 2), (cx, cz), (cx, z2 - 2))):
                if z1 < z < z2:
                    self.bp.set(x, self.gy, z, "minecraft:" + self.t("trim"))
                    self.place(x, self.gy + 1, z, self.light())
        return self.yard(5, 11, box, self.sides_front_side, b)

    def m_obelisks(self, box, **_):
        bp = self.bp
        H = 6 + self.L
        n = 0
        for x, z in ((2, 2), (bp.sx - 3, 2), (2, bp.sz - 3), (bp.sx - 3, bp.sz - 3)):
            if not self.lawn(x, z):
                continue
            self.ensure_height(self.gy + H + 3)
            for y in range(self.gy + 1, self.gy + H + 1):
                self.place(x, y, z, self.t("accent", y) if y > self.gy + H - 2 else self.t("feature"))
            self.cap(x, self.gy + H + 1, z)
            n += 1
        return n > 0

    def m_hanging_gardens(self, box, **_):
        """Vertical green stripes cascading down two facades."""
        x1, x2, z1, z2, top = box
        n = 0
        for side in self.sides_side[:2]:
            horiz = side in ("north", "south")
            span = range(x1 + 1, x2) if horiz else range(z1 + 1, z2)
            for u in span:
                if (u - span.start) % 6 != 2:
                    continue
                for y in range(self.gy + 3, top + 1):
                    if horiz:
                        wx, wz, ox, oz = u, (z1 if side == "north" else z2), u, (z1 - 1 if side == "north" else z2 + 1)
                    else:
                        wx, wz, ox, oz = (x1 if side == "west" else x2), u, (x1 - 1 if side == "west" else x2 + 1), u
                    if self.solid(wx, y, wz) and self.air(ox, y, oz) and not self.near_sensitive(ox, y, oz, 0):
                        leaves = ("flowering_azalea_leaves" if (y + u) % 3 else "azalea_leaves")
                        self.place(ox, y, oz, f"{leaves}[distance=1,persistent=true,waterlogged=false]")
                        n += 1
        return n > 0

    def m_cantilever_pods(self, box, **_):
        x1, x2, z1, z2, top = box
        n = 0
        y0 = max(self.gy + 5, top - 6)
        for side in self.sides_side[:2]:
            horiz = side in ("north", "south")
            mid = ((x1 + x2) // 2) if horiz else ((z1 + z2) // 2)
            wall = (z1 if side == "north" else z2) if horiz else (x1 if side == "west" else x2)
            sgn = -1 if side in ("north", "west") else 1
            cells = [(u, wall + sgn * d) for u in range(mid - 2, mid + 2) for d in (1, 2, 3)]
            cells = [(c if horiz else (c[1], c[0])) for c in cells]
            if not all(self.free(x, y, z) for x, z in cells for y in range(y0, y0 + 5)):
                continue
            us = range(mid - 2, mid + 2)
            for (x, z) in cells:
                u = x if horiz else z
                d = abs((z if horiz else x) - wall)
                e = u in (us.start, us.stop - 1) or d == 3
                self.place(x, y0, z, self.t("accent"))
                for y in range(y0 + 1, y0 + 4):
                    self.place(x, y, z, self.glass(y) if e else "air")
                self.place(x, y0 + 4, z, self.t("accent", 1))
            for y in (y0 + 1, y0 + 2):
                wx, wz = (mid, wall) if horiz else (wall, mid)
                if (wx, y, wz) not in self.protect and not self.near_sensitive(wx, y, wz, 0) and self.solid(wx, y, wz):
                    self.bp.set(wx, y, wz, "minecraft:air")
            n += 1
        return n > 0

    # -------------------------------------------------------------- plan
    def run(self):
        if not self.R or self.L < 2:
            return []
        c = self.core()
        if c is None:
            return []
        self.core_h = c[4] - self.gy
        self.front = self.front_side(c)
        opp = {"north": "south", "south": "north", "east": "west", "west": "east"}
        lateral = sorted({"north", "south", "east", "west"} - {self.front, opp[self.front]})
        self.sides_back = [opp[self.front]] + lateral
        self.sides_side = lateral + [opp[self.front]]
        self.sides_front_side = lateral + [self.front, opp[self.front]]
        mods = [(m, p) for m, lvl, p in self.R["modules"] if lvl <= self.L]
        # room for the modules: grow the lot by what the largest yard module needs
        m = {2: 6, 3: 8, 4: 10, 5: 12}[self.L]
        avail = min(c[0], c[2], self.bp.sx - 1 - c[1], self.bp.sz - 1 - c[3])
        grow = max(0, m - avail)
        self.grow_xz(grow)
        box = (c[0] + grow, c[1] + grow, c[2] + grow, c[3] + grow, c[4])
        done = []
        sy0 = self.bp.sy
        for name, params in mods:
            fn = getattr(self, "m_" + name)
            res = []
            if self.guarded(lambda: res.append(fn(box, **params))) and res and res[0]:
                done.append(name)
        self.trim_top(sy0)
        return done

    def trim_top(self, keep):
        """Drop empty layers that ensure_height added beyond what the modules used."""
        bp = self.bp
        top = max((y for y in range(bp.sy) if any(c != "minecraft:air" for row in bp.grid[y] for c in row)), default=0)
        new = max(keep, top + 2)
        cut = bp.sy - new
        if cut <= 0:
            return
        bp.grid = bp.grid[:new]
        bp.sy = new
        for te in bp.tile_entities.values():
            bdp = te.get("blueprintDataProvider")
            if bdp is None:
                continue
            c1, c2 = bdp["corner1"], bdp["corner2"]
            if all(int(c[k]) == 0 for c in (c1, c2) for k in "xyz"):
                continue
            c2["y"] = type(c2["y"])(int(c2["y"]) - cut)
