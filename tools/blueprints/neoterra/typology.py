"""
Real-world building typology for the hut generator (archgen).

Every hut type is mapped to the building it is in real life – plan, roof, storeys and the features that
make it recognisable (a town hall's portico and clock tower, a hospital's red cross and ambulance canopy,
a bakery's storefront, awning and oven chimney, a warehouse's loading docks, a barn's big doors and silo,
...). Features appear level by level; materials and roof shapes stay in each pack's own style.
"""
from __future__ import annotations

import math

AIR = "minecraft:air"

# archetype roof kind -> archgen roof form, per pack
ROOFMAP = {
    "Cascadia": {"pitched": "gable_steep", "steep": "aframe", "hip": "hip", "barn": "gambrel", "flat": "gable",
                 "industrial": "gable", "battlement": "flat"},
    "Hearthwood": {"pitched": "gable", "steep": "gable_steep", "hip": "hip", "barn": "gambrel", "flat": "hip",
                   "industrial": "shed", "battlement": "flat"},
    "Neoterra": {"pitched": "shed", "steep": "gable", "hip": "flat", "barn": "gambrel", "flat": "flat",
                 "industrial": "flat", "battlement": "flat"},
}

WOOD = {"Cascadia": "spruce", "Hearthwood": "dark_oak", "Neoterra": "birch"}
STONE = {"Cascadia": "stone_bricks", "Hearthwood": "bricks", "Neoterra": "light_gray_concrete"}
FACE = {"Cascadia": "calcite", "Hearthwood": "calcite", "Neoterra": "white_concrete"}
FLAG = {"Cascadia": ["green_wool", "white_wool"], "Hearthwood": ["red_wool", "white_wool"], "Neoterra": ["cyan_wool", "white_wool"]}


def T(plan, roof, floors=None, feats=(), margin=5, skin=None):
    return dict(plan=plan, roof=roof, floors=floors, feats=list(feats), margin=margin, skin=skin)


# wall treatments that make a building type read right (override the pack's default cladding)
SKINS = {
    "barn": {"Cascadia": dict(wall="red_terracotta", batten="stripped_birch_log[axis=y]", frame="stripped_birch_log[axis=y]",
                              post="stripped_birch_log[axis=y]", wall2="red_terracotta"),
             "Hearthwood": dict(wall="red_terracotta", batten="white_terracotta", frame="white_terracotta",
                                post="stripped_birch_log[axis=y]", wall2="red_terracotta"),
             "Neoterra": dict(wall="gray_concrete", batten="white_concrete", frame="white_concrete", post="white_concrete",
                              wall2="gray_concrete")},
    "industrial": {"Cascadia": dict(wall="stone_bricks", batten="stone_bricks", frame="dark_oak_log[axis=y]",
                                    post="dark_oak_log[axis=y]", wall2="stone_bricks"),
                   "Hearthwood": dict(wall="bricks", batten="bricks", frame="stone_bricks", post="stone_bricks", wall2="bricks"),
                   "Neoterra": dict(wall="light_gray_concrete", batten="gray_concrete", frame="gray_concrete",
                                    post="gray_concrete", wall2="light_gray_concrete")},
    "civic": {"Cascadia": dict(wall="spruce_planks", batten="stripped_spruce_log[axis=y]", frame="stone_bricks",
                               post="stone_bricks", wall2="spruce_planks"),
              "Hearthwood": dict(wall="bricks", batten="bricks", frame="stone_bricks", post="stone_bricks", wall2="bricks"),
              "Neoterra": dict(wall="white_concrete", batten="white_concrete", frame="smooth_stone", post="smooth_stone",
                               wall2="white_concrete")},
    "stone": {"Cascadia": dict(wall="cobblestone", batten="mossy_cobblestone", frame="stone_bricks", post="stone_bricks",
                               wall2="stone_bricks"),
              "Hearthwood": dict(wall="stone_bricks", batten="stone_bricks", frame="chiseled_stone_bricks",
                                 post="stone_bricks", wall2="stone_bricks"),
              "Neoterra": dict(wall="light_gray_concrete", batten="smooth_stone", frame="smooth_stone", post="gray_concrete",
                               wall2="light_gray_concrete")},
}


F1 = {1: 1, 2: 1, 3: 1, 4: 2, 5: 2}
F2 = {1: 1, 2: 2, 3: 2, 4: 2, 5: 3}
F3 = {1: 1, 2: 2, 3: 2, 4: 3, 5: 3}

SPEC = {
    # civic / education
    "townhall": T("civic", "hip", F3, [(1, "flagpole"), (2, "portico"), (3, "clock_tower"), (5, "dome")], 6, skin="civic"),
    "university": T("civic", "hip", F2, [(2, "portico"), (3, "clock_tower"), (4, "flagpole")], 6, skin="civic"),
    "communitycollege": T("longhall_T", "hip", F2, [(1, "cupola"), (2, "portico"), (4, "flagpole")], 6, skin="civic"),
    "school": T("longhall", "hip", F1, [(1, "cupola"), (2, "flagpole"), (3, "entry_canopy")], skin="civic"),
    "library": T("box", "hip", F2, [(2, "portico"), (4, "dome")], 6, skin="civic"),
    "hospital": T("longhall_T", "flat", F3, [(1, "red_cross"), (2, "covered_entry"), (3, "flagpole"), (4, "helipad")], skin="civic"),
    # homes
    "cottage": T("box", "steep", F1, [(1, "chimney"), (2, "porch"), (3, "dormers")]),
    "house": T("house_L", "pitched", F2, [(1, "porch"), (2, "chimney"), (3, "dormers"), (4, "balconies")]),
    "apartment": T("box", "flat", {1: 2, 2: 3, 3: 3, 4: 4, 5: 4}, [(1, "entry_canopy"), (2, "balconies")]),
    "quadplex": T("box_wide", "hip", {1: 2, 2: 2, 3: 2, 4: 3, 5: 3}, [(1, "entry_canopy"), (2, "balconies"), (3, "chimney")]),
    # food & drink
    "tavern": T("house_L", "pitched", {1: 2, 2: 2, 3: 2, 4: 3, 5: 3},
                [(1, "hanging_sign"), (1, "chimney"), (2, "terrace"), (3, "balconies"), (4, "dormers")]),
    "cook": T("shop", "pitched", F1, [(1, "storefront"), (1, "awning"), (2, "terrace"), (3, "chimney"), (4, "hanging_sign")]),
    "cookery": T("shop", "pitched", F1, [(1, "storefront"), (1, "chimney"), (2, "awning"), (3, "terrace")]),
    "baker": T("shop", "pitched", F1, [(1, "storefront"), (1, "awning"), (2, "chimney"), (3, "hanging_sign")]),
    # trades
    "builder": T("longhall", "pitched", F1, [(1, "timber_stack"), (2, "crane"), (3, "awning")], 6),
    "lumberjack": T("lodge_L", "steep", F1, [(1, "log_piles"), (2, "chimney"), (3, "porch")]),
    "sawmill": T("barn", "pitched", F1, [(1, "log_piles"), (2, "water_wheel"), (3, "awning")]),
    "stonemason": T("longhall", "pitched", F1, [(1, "stone_pile"), (2, "crane"), (3, "chimney")], 6),
    "mechanic": T("box_wide", "industrial", F1, [(1, "loading_docks"), (2, "smokestacks"), (3, "crane")], 6, skin="industrial"),
    "deliveryman": T("longhall", "pitched", F1, [(1, "loading_docks"), (1, "hanging_sign"), (2, "flagpole")]),
    "warehouse": T("box_wide", "industrial", F1, [(1, "loading_docks"), (2, "crane"), (4, "flagpole")], 6, skin="industrial"),
    "blacksmith": T("longhall", "pitched", F1, [(1, "forge_chimney"), (2, "awning"), (3, "hanging_sign")], skin="industrial"),
    "fletcher": T("longhall", "pitched", F1, [(1, "awning"), (2, "hanging_sign"), (3, "targets")]),
    "alchemist": T("shop", "steep", F1, [(1, "storefront"), (1, "hanging_sign"), (2, "sunroom")]),
    "dyer": T("longhall", "pitched", F1, [(1, "vats"), (2, "drying_line"), (3, "awning")]),
    "glassblower": T("longhall", "pitched", F1, [(1, "kiln"), (2, "storefront"), (3, "hanging_sign")], skin="industrial"),
    "concretemixer": T("box_wide", "industrial", F1, [(1, "silo"), (2, "smokestacks"), (3, "loading_docks")], 6, skin="industrial"),
    "crusher": T("box_wide", "industrial", F1, [(1, "stone_pile"), (2, "smokestacks")], 6, skin="industrial"),
    "sifter": T("longhall", "pitched", F1, [(1, "stone_pile"), (2, "awning")]),
    "smeltery": T("box_wide", "industrial", F1, [(1, "smokestacks"), (2, "loading_docks")], 6, skin="industrial"),
    "stonesmeltery": T("box_wide", "industrial", F1, [(1, "kiln"), (2, "smokestacks")], 6, skin="industrial"),
    "miner": T("box", "pitched", F1, [(1, "headframe"), (2, "stone_pile")], 6, skin="stone"),
    "netherworker": T("box_wide", "industrial", F1, [(1, "smokestacks")], 6, skin="industrial"),
    # farming
    "farmer": T("barn", "barn", F1, [(1, "barn_doors"), (2, "silo"), (3, "cupola")], 6, skin="barn"),
    "cowboy": T("barn", "barn", F1, [(1, "barn_doors"), (2, "silo")], 6, skin="barn"),
    "shepherd": T("barn", "barn", F1, [(1, "barn_doors"), (3, "cupola")], 6, skin="barn"),
    "swineherder": T("barn", "pitched", F1, [(1, "barn_doors")], skin="barn"),
    "chickenherder": T("box", "pitched", F1, [(1, "barn_doors"), (3, "silo")], 6, skin="barn"),
    "rabbithutch": T("box", "pitched", F1, [(1, "barn_doors")], skin="barn"),
    "stable": T("barn", "barn", F1, [(1, "barn_doors"), (2, "cupola")], skin="barn"),
    "composter": T("barn", "pitched", F1, [(1, "compost_bins"), (2, "silo")], 6, skin="barn"),
    "beekeeper": T("box", "steep", F1, [(1, "porch"), (2, "chimney")]),
    "florist": T("shop", "pitched", F1, [(1, "glass_roof"), (1, "storefront"), (2, "flower_boxes")]),
    "plantation": T("longhall", "pitched", F1, [(1, "sunroom"), (2, "silo")], 6),
    "fisherman": T("box", "pitched", F1, [(1, "porch"), (2, "nets")]),
    # military
    "guardtower": T("tower", "battlement", {1: 2, 2: 2, 3: 3, 4: 3, 5: 4}, [(1, "battlements"), (2, "flagpole")], skin="stone"),
    "archery": T("longhall", "pitched", F1, [(1, "targets"), (2, "flagpole"), (3, "lookout")]),
    "combatacademy": T("longhall_T", "hip", F1, [(1, "flagpole"), (2, "battlements_low"), (3, "portico")], 6, skin="stone"),
    # mystic
    "enchanter": T("box", "steep", F1, [(1, "mage_tower")], 6),
    "graveyard": T("box", "steep", F1, [(1, "steeple")], skin="stone"),
    "mysticalsite": T("box", "hip", F1, [(1, "portico"), (3, "dome")], 6, skin="civic"),
}


def roof_form(style, kind):
    return ROOFMAP[style][kind]


# ------------------------------------------------------------------------------------------------ helpers
class _Ctx:
    def __init__(self, a):
        self.a = a
        self.bp = a.bp
        self.x1, self.x2, self.z1, self.z2, self.nf, _ = a.vols[0]
        self.gy = a.gy
        self.M = a.M
        self.style = a.style
        self.L = a.L
        self.wood = WOOD[a.style]
        self.dx = a.door_x
        self.cx = (self.x1 + self.x2) // 2
        self.cz = (self.z1 + self.z2) // 2
        self.ytop = a.floor_y(self.nf)

    def S(self, x, y, z, s, force=False):
        self.a.S(x, y, z, s, force=force)

    def get(self, x, y, z):
        return self.bp.get(x, y, z) if self.bp.inside(x, y, z) else AIR

    def free(self, x, y, z):
        return self.bp.inside(x, y, z) and self.bp.get(x, y, z) == AIR and (x, y, z) not in self.a.locked

    def top(self, x, z):
        for y in range(self.bp.sy - 1, -1, -1):
            if self.get(x, y, z) != AIR:
                return y
        return 0

    def stair(self, mat, facing, half="bottom"):
        return f"{mat}_stairs[facing={facing},half={half},shape=straight,waterlogged=false]"

    def fence(self, mat=None):
        return f"{mat or self.wood}_fence[east=false,north=false,south=false,waterlogged=false,west=false]"

    def flag_pole(self, x, z, h):
        for y in range(self.gy + 1, self.gy + h):
            self.S(x, y, z, self.fence())
        cols = FLAG[self.style]
        for i, dx in enumerate((1, 2, 3)):
            for dy in (0, 1):
                self.S(x + dx, self.gy + h - 2 + dy, z, cols[(i + dy) % 2])
        self.S(x, self.gy + h, z, "lightning_rod[facing=up,powered=false,waterlogged=false]")

    def wall_mat(self):
        return self.M["wall"]


# ------------------------------------------------------------------------------------------------ features
def f_flagpole(c):
    x = c.x1 - 3 if c.x1 - 3 >= 1 else c.x2 + 2
    c.flag_pole(x, c.z1 - 3, 9 + c.L)


def f_portico(c):
    """Columns, entablature and (except Neoterra) a triangular pediment in front of the door."""
    zf = c.z1 - 3
    width = min(5, (c.x2 - c.x1) // 2 - 1)
    xs = [c.dx + o for o in (-width, -2, 2, width) if c.x1 - 1 <= c.dx + o <= c.x2 + 1]
    col = c.M["post"] if c.style != "Neoterra" else ("quartz_pillar[axis=y]" if c.L >= 4 else "white_concrete")
    top = c.gy + 4
    for x in range(c.dx - width - 1, c.dx + width + 2):
        for z in range(zf, c.z1):
            c.S(x, c.gy, z, STONE[c.style] if c.style != "Neoterra" else c.M["deck"], force=True)
    for x in xs:
        for y in range(c.gy + 1, top):
            c.S(x, y, zf, col)
    for x in range(c.dx - width - 1, c.dx + width + 2):
        for z in range(zf, c.z1):
            c.S(x, top, z, c.M["ridge"] if c.style != "Neoterra" else "smooth_quartz_slab[type=bottom,waterlogged=false]"
                if c.L >= 4 else "smooth_stone_slab[type=bottom,waterlogged=false]")
    if c.style != "Neoterra":
        roof = c.a.M["roof5"] if c.a.top else c.a.M["roof"]
        for k in range(width + 2):
            y = top + 1 + k
            xa, xb = c.dx - width - 1 + k, c.dx + width + 1 - k
            if xa > xb:
                break
            c.S(xa, y, zf, c.stair(roof, "east"))
            c.S(xb, y, zf, c.stair(roof, "west"))
            for x in range(xa + 1, xb):
                c.S(x, y, zf, c.M["wall"])
            for z in range(zf + 1, c.z1):
                for x in range(xa, xb + 1):
                    c.S(x, y, z, c.M["ridge"])


def f_clock_tower(c):
    """Square tower rising from the middle of the roof with clock faces, belfry and spire."""
    r = 2 if (c.x2 - c.x1) >= 10 and (c.z2 - c.z1) >= 8 else 1
    xs, zs = range(c.cx - r, c.cx + r + 1), range(c.cz - r, c.cz + r + 1)
    base = c.ytop + 1
    ridge = max(c.top(x, z) for x in xs for z in zs)
    clock = ridge + 2
    belfry = clock + 3
    for y in range(base, belfry + 3):
        for x in xs:
            for z in zs:
                edge = x in (xs[0], xs[-1]) or z in (zs[0], zs[-1])
                corner = x in (xs[0], xs[-1]) and z in (zs[0], zs[-1])
                if y >= belfry:
                    s = c.M["post"] if corner else AIR
                else:
                    s = (c.M["post"] if corner else c.M["wall"]) if edge else AIR
                c.S(x, y, z, s, force=True)
    for d in range(-min(r, 1), min(r, 1) + 1):              # faces on all four sides
        for dy in (-1, 0, 1) if r == 2 else (0,):
            for x, z in ((c.cx + d, zs[0]), (c.cx + d, zs[-1]), (xs[0], c.cz + d), (xs[-1], c.cz + d)):
                c.S(x, clock + dy, z, FACE[c.style], force=True)
    for x, z in ((c.cx, zs[0]), (c.cx, zs[-1]), (xs[0], c.cz), (xs[-1], c.cz)):
        c.S(x, clock, z, "black_concrete" if c.style == "Neoterra" else "dark_oak_planks", force=True)
    for x in xs:
        for z in zs:
            c.S(x, belfry - 1, z, c.M["ridge"], force=True)
            c.S(x, belfry + 3, z, c.M["ridge"], force=True)
    c.S(c.cx, belfry + 2, c.cz, "bell[attachment=ceiling,facing=north,powered=false]", force=True)
    y = belfry + 4
    if c.style == "Neoterra":
        for k in range(4):
            c.S(c.cx, y + k, c.cz, "sea_lantern" if k == 0 else "end_rod[facing=up]", force=True)
        return
    roof = c.a.M["roof5"] if c.a.top else c.a.M["roof"]
    rr = r + 1
    while rr >= 0:
        for x in range(c.cx - rr, c.cx + rr + 1):
            for z in range(c.cz - rr, c.cz + rr + 1):
                ring = abs(x - c.cx) == rr or abs(z - c.cz) == rr
                if not ring and rr:
                    continue
                if rr == 0:
                    c.S(x, y, z, c.M["ridge"], force=True)
                elif x == c.cx - rr:
                    c.S(x, y, z, c.stair(roof, "east"), force=True)
                elif x == c.cx + rr:
                    c.S(x, y, z, c.stair(roof, "west"), force=True)
                elif z == c.cz - rr:
                    c.S(x, y, z, c.stair(roof, "south"), force=True)
                else:
                    c.S(x, y, z, c.stair(roof, "north"), force=True)
        rr -= 1
        y += 1
    c.S(c.cx, y, c.cz, "lightning_rod[facing=up,powered=false,waterlogged=false]", force=True)


def f_dome(c):
    r = max(2, min(c.x2 - c.x1, c.z2 - c.z1) // 2 - 2)
    if r < 2:
        return
    base = max(c.top(x, z) for x in range(c.cx - r, c.cx + r + 1) for z in range(c.cz - r, c.cz + r + 1)) + 1
    mat = {"Neoterra": "white_concrete", "Hearthwood": "waxed_cut_copper", "Cascadia": "waxed_weathered_cut_copper"}[c.style]
    if c.style == "Neoterra" and c.L >= 4:
        mat = "light_blue_stained_glass"
    for x in range(c.cx - r, c.cx + r + 1):                 # drum
        for z in range(c.cz - r, c.cz + r + 1):
            d = math.hypot(x - c.cx, z - c.cz)
            if r - 0.5 < d <= r + 0.5:
                c.S(x, base, z, c.M["wall"], force=True)
    for x in range(c.cx - r, c.cx + r + 1):
        for z in range(c.cz - r, c.cz + r + 1):
            for y in range(base + 1, base + r + 2):
                d = math.sqrt((x - c.cx) ** 2 + (z - c.cz) ** 2 + (y - base - 1) ** 2)
                if r - 0.6 < d <= r + 0.4:
                    c.S(x, y, z, mat, force=True)
    c.S(c.cx, base + r + 2, c.cz, "lantern[hanging=false,waterlogged=false]", force=True)


def f_red_cross(c):
    if c.nf >= 2:
        y0, z = c.a.floor_y(1) + 1, c.z1
    else:
        y0, z = c.ytop + 1, c.z1
    for dy in range(3):
        c.S(c.dx, y0 + dy, z, "red_concrete", force=True)
    c.S(c.dx - 1, y0 + 1, z, "red_concrete", force=True)
    c.S(c.dx + 1, y0 + 1, z, "red_concrete", force=True)
    if c.nf >= 2:                                         # white backing
        for x in range(c.dx - 2, c.dx + 3):
            for dy in range(-1, 4):
                if c.get(x, y0 + dy, z) not in ("minecraft:red_concrete",):
                    c.S(x, y0 + dy, z, "white_concrete", force=True)


def f_helipad(c):
    if c.a.vols[0][5] != "flat":
        return
    y = c.ytop
    for x in range(c.cx - 2, c.cx + 3):
        for z in range(c.cz - 2, c.cz + 3):
            c.S(x, y, z, "white_concrete", force=True)
    for z in range(c.cz - 2, c.cz + 3):
        c.S(c.cx - 1, y, z, "yellow_concrete", force=True)
        c.S(c.cx + 1, y, z, "yellow_concrete", force=True)
    c.S(c.cx, y, c.cz, "yellow_concrete", force=True)


def f_entry_canopy(c):
    for x in range(c.dx - 2, c.dx + 3):
        for z in range(c.z1 - 2, c.z1):
            c.S(x, c.gy + 3, z, f"{'smooth_stone' if c.style == 'Neoterra' else c.wood}_slab[type=top,waterlogged=false]")
    for x in (c.dx - 2, c.dx + 2):
        for y in range(c.gy + 1, c.gy + 3):
            c.S(x, y, c.z1 - 2, c.fence())


def f_balconies(c):
    for f in range(1, c.nf):
        y = c.a.floor_y(f)
        for x0 in range(c.x1 + 2, c.x2 - 2, 5):
            for x in range(x0, x0 + 3):
                if x > c.x2 - 1:
                    continue
                for z in (c.z1 - 1, c.z1 - 2):
                    c.S(x, y, z, c.M["deck"] if c.style != "Neoterra" else "smooth_stone")
                c.S(x, y + 1, c.z1 - 2, c.fence() if c.style != "Neoterra" else "glass_pane")
            c.S(x0, y + 1, c.z1 - 1, c.fence() if c.style != "Neoterra" else "glass_pane")
            c.S(x0 + 2, y + 1, c.z1 - 1, c.fence() if c.style != "Neoterra" else "glass_pane")


def f_storefront(c):
    acc = c.M["accent"][0]
    for x in range(c.x1 + 1, c.x2):
        if abs(x - c.dx) <= 0:
            continue
        if (x, c.gy + 1, c.z1) in c.a.locked:
            continue
        for y in (c.gy + 1, c.gy + 2):
            c.S(x, y, c.z1, c.M["glass"])
        c.S(x, c.gy + 3, c.z1, acc)


def f_hanging_sign(c):
    x = c.dx + 2 if c.dx + 2 < c.x2 else c.dx - 2
    c.S(x, c.gy + 3, c.z1 - 1, c.fence())
    c.S(x, c.gy + 2, c.z1 - 1, f"{c.wood}_hanging_sign[attached=false,rotation=0,waterlogged=false]")


def f_terrace(c):
    for side in (-1, 1):
        tx = c.dx + side * 4
        if not (1 <= tx - 1 and tx + 1 < c.bp.sx - 1):
            continue
        z = c.z1 - 3
        c.S(tx, c.gy + 1, z, c.fence())
        c.S(tx, c.gy + 2, z, "white_carpet" if c.style != "Cascadia" else "green_carpet")
        c.S(tx - 1, c.gy + 1, z, c.stair(c.wood, "west"))
        c.S(tx + 1, c.gy + 1, z, c.stair(c.wood, "east"))


def f_chimney(c):
    c.a.extra("brick_chimney" if c.style == "Hearthwood" else "stone_chimney")


def f_forge_chimney(c):
    x, z = c.x2 + 1, c.z2 - 2
    top = c.ytop + 9
    for y in range(c.gy + 1, top):
        for dx in (0, 1):
            for dz in (0, 1):
                c.S(x + dx, y, z + dz, STONE[c.style] if y > c.gy + 3 else "cobblestone")
    c.S(x, top, z, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")


def f_smokestacks(c):
    n = 1 + (c.L >= 3) + (c.L >= 5)
    xs = [c.x1 + 2 + i * 4 for i in range(n) if c.x1 + 2 + i * 4 < c.x2]
    z = c.z2 + 1
    mat = {"Cascadia": "stone_bricks", "Hearthwood": "bricks", "Neoterra": "light_gray_concrete"}[c.style]
    for i, x in enumerate(xs):
        top = c.ytop + 10 + 2 * i
        for y in range(c.gy + 1, top):
            c.S(x, y, z, mat if (y // 4) % 3 else ("red_concrete" if c.style == "Neoterra" else mat))
        c.S(x, top, z, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")


def f_loading_docks(c):
    n = 1 + (c.L >= 3)
    spots = [x for x in range(c.x1 + 2, c.x2 - 2, 5) if abs(x + 1 - c.dx) > 2][:n]
    for x0 in spots:
        for x in range(x0, x0 + 3):
            for y in (c.gy + 1, c.gy + 2):
                c.S(x, y, c.z1, AIR)
            c.S(x, c.gy + 3, c.z1, "yellow_concrete" if c.style == "Neoterra" else c.M["post"].replace("axis=y", "axis=x"))
            for z in (c.z1 - 1, c.z1 - 2):
                c.S(x, c.gy, z, "smooth_stone")
                c.S(x, c.gy + 4, z, f"{'smooth_stone' if c.style == 'Neoterra' else c.wood}_slab[type=bottom,waterlogged=false]")


def f_crane(c):
    mx, mz = c.x2 + 3, c.z1 + 1
    H = c.ytop + 8
    mast = "yellow_concrete" if c.style == "Neoterra" else c.M["post"]
    for y in range(c.gy + 1, H + 1):
        c.S(mx, y, mz, mast)
    jib = "yellow_concrete" if c.style == "Neoterra" else c.M["post"].replace("axis=y", "axis=x")
    for x in range(mx - 9, mx + 3):
        c.S(x, H + 1, mz, jib)
    c.S(mx + 2, H, mz, "iron_block" if c.style == "Neoterra" else "cobblestone")
    hx = mx - 7
    for y in range(H - 3, H + 1):
        c.S(hx, y, mz, "chain[axis=y,waterlogged=false]")
    c.S(hx, H - 4, mz, "iron_block" if c.style == "Neoterra" else f"{c.wood}_planks")


def f_timber_stack(c):
    x0, z0 = c.x1 - 4, c.z1
    for i in range(3):
        for x in range(x0 + i // 2, x0 + 3 - (i + 1) // 2):
            for z in range(z0, z0 + 4):
                c.S(x, c.gy + 1 + i, z, f"stripped_{c.wood}_log[axis=z]" if c.style != "Neoterra" else "birch_log[axis=z]")


def f_log_piles(c):
    f_timber_stack(c)
    if c.L >= 3:
        x0, z0 = c.x1 - 4, c.z1 + 5
        for i in range(2):
            for x in range(x0, x0 + 3):
                for z in range(z0, z0 + 3):
                    if i == 0 or (x == x0 + 1):
                        c.S(x, c.gy + 1 + i, z, f"{c.wood}_log[axis=z]")


def f_stone_pile(c):
    x0, z0 = c.x1 - 4, c.z1
    mats = ["stone", "cobblestone", "stone_bricks", "andesite"]
    for x in range(x0, x0 + 3):
        for z in range(z0, z0 + 3):
            hgt = 1 + ((x + z) % 2)
            for y in range(c.gy + 1, c.gy + 1 + hgt):
                c.S(x, y, z, mats[(x * 3 + z + y) % len(mats)])


def f_barn_doors(c):
    """Big X-braced barn doors on the front and a hay-loft hatch above."""
    beam = f"stripped_{c.wood}_log[axis=x]" if c.style != "Neoterra" else "white_concrete"
    plank = f"{'red' if c.style == 'Cascadia' else 'brown' if c.style == 'Hearthwood' else 'light_gray'}_terracotta"
    for x in range(c.dx - 2, c.dx + 3):
        for y in range(c.gy + 1, c.gy + 4):
            if (x, y, c.z1) in c.a.locked or x == c.dx and y < c.gy + 3:
                continue
            diag = abs(x - c.dx) == (y - c.gy - 1) or abs(x - c.dx) == 2 and y == c.gy + 3
            c.S(x, y, c.z1, beam if diag or y == c.gy + 3 else plank)
    loft = c.ytop + 2
    if c.get(c.dx, loft, c.z1) != AIR:
        c.S(c.dx, loft, c.z1, f"{c.wood}_trapdoor[facing=north,half=bottom,open=true,powered=false,waterlogged=false]")
    for x in (c.dx - 4, c.dx + 4):
        if c.x1 - 3 <= x <= c.x2 + 3:
            c.S(x, c.gy + 1, c.z1 - 2, "hay_block[axis=y]")


def f_battlements(c):
    y = c.ytop + 1
    for x in range(c.x1, c.x2 + 1):
        for z in range(c.z1, c.z2 + 1):
            if x in (c.x1, c.x2) or z in (c.z1, c.z2):
                c.S(x, y, z, STONE[c.style], force=True)
                if (x + z) % 2 == 0:
                    c.S(x, y + 1, z, STONE[c.style], force=True)
    for y2 in range(y, y + 5):
        c.S(c.cx, y2, c.cz, c.fence(), force=True)
    cols = FLAG[c.style]
    for i in (1, 2, 3):
        c.S(c.cx + i, y + 3, c.cz, cols[i % 2], force=True)


def f_battlements_low(c):
    for x in range(c.x1, c.x2 + 1, 2):
        c.S(x, c.ytop, c.z1 - 1, STONE[c.style])
        c.S(x, c.ytop + 1, c.z1 - 1, STONE[c.style])


def f_targets(c):
    for z in range(c.z1, c.z2, 3):
        x = c.x2 + 3
        c.S(x, c.gy + 1, z, "hay_block[axis=y]")
        c.S(x, c.gy + 2, z, "target[power=0]")


def f_vats(c):
    for i, x in enumerate(range(c.x1 - 4, c.x1 - 1)):
        c.S(x, c.gy + 1, c.z1 + 1, "water_cauldron[level=3]")
        c.S(x, c.gy + 1, c.z1 + 3, "water_cauldron[level=3]")


def f_drying_line(c):
    xa, xb, z = c.x1 - 4, c.x1 - 1, c.z1 + 6
    for x in (xa, xb):
        for y in range(c.gy + 1, c.gy + 5):
            c.S(x, y, z, c.fence())
    cols = ["red_wool", "blue_wool", "yellow_wool", "green_wool", "purple_wool"]
    for i, x in enumerate(range(xa, xb + 1)):
        c.S(x, c.gy + 4, z, c.fence())
        if xa < x < xb:
            c.S(x, c.gy + 3, z, cols[i % len(cols)])


def f_kiln(c):
    """Bottle kiln: round brick tower that narrows to a chimney."""
    kx, kz = c.x1 - 4, c.cz
    mat = "bricks" if c.style != "Neoterra" else "light_gray_concrete"
    H = c.ytop + 6
    for y in range(c.gy + 1, H + 1):
        r = 2.4 if y < c.gy + (H - c.gy) * 0.6 else 1.4 if y < H - 1 else 0.6
        for x in range(kx - 3, kx + 4):
            for z in range(kz - 3, kz + 4):
                d = math.hypot(x - kx, z - kz)
                if r - 1 < d <= r:
                    c.S(x, y, z, mat)
    c.S(kx, H, kz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")


def f_headframe(c):
    hx, hz = c.x1 - 4, c.z1 + 1
    H = c.ytop + 7
    leg = c.M["post"] if c.style != "Neoterra" else "gray_concrete"
    for y in range(c.gy + 1, H + 1):
        c.S(hx, y, hz, leg)
        c.S(hx, y, hz + 3, leg)
    for y in range(c.gy + 3, H, 3):
        for z in range(hz + 1, hz + 3):
            c.S(hx, y, z, f"{c.wood}_planks" if c.style != "Neoterra" else "iron_bars")
    for z in range(hz, hz + 4):
        c.S(hx, H + 1, z, f"{c.wood}_planks" if c.style != "Neoterra" else "gray_concrete")
    wheel = "iron_bars" if c.style == "Neoterra" else f"{c.wood}_fence"
    for dy in range(2, 5):
        c.S(hx, H + dy, hz, leg)
        c.S(hx, H + dy, hz + 3, leg)
    for z in range(hz, hz + 4):
        c.S(hx, H + 5, z, f"{c.wood}_planks" if c.style != "Neoterra" else "gray_concrete")
    c.S(hx, H + 3, hz + 1, wheel)
    c.S(hx, H + 3, hz + 2, wheel)


def f_compost_bins(c):
    for x in range(c.x1 - 4, c.x1 - 1):
        for z in (c.z1, c.z1 + 2):
            c.S(x, c.gy + 1, z, "composter[level=4]")


def f_glass_roof(c):
    for x in range(c.x1 - 1, c.x2 + 2):
        for z in range(c.z1 - 1, c.z2 + 2):
            for y in range(c.ytop + 1, c.bp.sy):
                s = c.get(x, y, z)
                if s != AIR and ("stairs" in s or "slab" in s or s.endswith("_planks") or s == "minecraft:" + c.M["ridge"]):
                    c.S(x, y, z, "glass", force=True)


def f_flower_boxes(c):
    for x in range(c.x1 + 1, c.x2):
        if abs(x - c.dx) > 1 and (x, c.gy + 1, c.z1 - 1) not in c.a.locked:
            c.S(x, c.gy + 1, c.z1 - 1, "potted_red_tulip" if x % 2 else "potted_cornflower")


def f_nets(c):
    for z in range(c.z1, c.z1 + 4):
        c.S(c.x1 - 2, c.gy + 1, z, c.fence())
        c.S(c.x1 - 2, c.gy + 2, z, c.fence())
    c.S(c.x1 - 3, c.gy + 1, c.z1 + 1, "barrel[facing=up,open=false]")


def f_mage_tower(c):
    tx, tz = c.x2 + 3, c.z1 + 2
    H = c.ytop + 9
    wall = {"Cascadia": "stone_bricks", "Hearthwood": "bricks", "Neoterra": "white_concrete"}[c.style]
    for y in range(c.gy + 1, H + 1):
        for x in range(tx - 2, tx + 3):
            for z in range(tz - 2, tz + 3):
                d = math.hypot(x - tx, z - tz)
                if 1.5 < d <= 2.5:
                    c.S(x, y, z, "purple_stained_glass" if (y % 4 == 0 and (x == tx or z == tz)) else wall)
    r, y = 3, H + 1
    while r >= 0:
        for x in range(tx - r, tx + r + 1):
            for z in range(tz - r, tz + r + 1):
                if math.hypot(x - tx, z - tz) <= r + 0.3:
                    c.S(x, y, z, "purple_terracotta" if c.style != "Neoterra" else "purple_concrete")
        r -= 1
        y += 1
        if r == 0:
            y += 1
    c.S(tx, y, tz, "end_rod[facing=up]")
    # covered link from the tower to the side wall
    for x in range(c.x2 + 1, tx - 1):
        c.S(x, c.gy + 3, tz, f"{c.wood}_slab[type=top,waterlogged=false]" if c.style != "Neoterra" else "smooth_stone_slab[type=top,waterlogged=false]")


def f_steeple(c):
    """Square bell tower on the front gable with a tall spire."""
    xs, zs = range(c.dx - 1, c.dx + 2), range(c.z1, c.z1 + 3)
    base = c.ytop + 1
    ridge = max(c.top(x, z) for x in xs for z in zs)
    top = ridge + 4
    for y in range(base, top + 1):
        for x in xs:
            for z in zs:
                edge = x != c.dx or z != c.z1 + 1
                c.S(x, y, z, (c.M["wall"] if y < top - 1 else c.M["post"]) if edge else AIR, force=True)
    for x, z in ((c.dx, c.z1), (c.dx, c.z1 + 2), (c.dx - 1, c.z1 + 1), (c.dx + 1, c.z1 + 1)):
        c.S(x, top - 1, z, AIR, force=True)
        c.S(x, top, z, AIR, force=True)
    c.S(c.dx, top, c.z1 + 1, "bell[attachment=ceiling,facing=north,powered=false]", force=True)
    for x in xs:
        for z in zs:
            c.S(x, top + 1, z, c.M["ridge"], force=True)
    roof = c.a.M["roof5"] if c.a.top else c.a.M["roof"]
    for k in range(6):
        c.S(c.dx, top + 2 + k, c.z1 + 1, f"{roof}_planks" if roof in ("spruce", "dark_oak", "oak", "birch", "mangrove") else c.M["ridge"], force=True)
    c.S(c.dx, top + 8, c.z1 + 1, "lightning_rod[facing=up,powered=false,waterlogged=false]", force=True)


# archgen's own extras
PASSTHROUGH = ("porch", "covered_entry", "deck", "dormers", "awning", "silo", "water_wheel", "cupola", "lookout", "sunroom")


def apply(a):
    c = _Ctx(a)
    for lvl, name in a.typ["feats"]:
        if a.L < lvl or name in getattr(a, "skip_feats", ()):
            continue
        if name in PASSTHROUGH:
            a.extra(name)
        else:
            globals()["f_" + name](c)
