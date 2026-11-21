"""
Fortifications: barracks (+ its child barrackstower), gatehouse, wallguardtower.

Barracks (child huts = the towers with the bunk rooms; one more tower per level, 4 at L4/L5)
  Hearthwood  Stone castle: round corner towers (child) on a crenellated curtain wall with a gate tower and
              portcullis, a stone great hall with a steep tiled roof (armoury, mess table, hearth) along the back
              wall, archery butts and dummies in the bailey. L1-2 a low bailey wall, L3 the full curtain wall with
              wall walk and gate tower, L5 well, flag and banners.
  Cascadia    Frontier stockade fort: log blockhouses with overhanging upper storeys (child) at the corners, a
              pointed log palisade with a firing step and a timber gate with a walkway over it, a log barracks hall
              with porch and stone chimney, targets on the parade ground. L1-2 split-rail fence, L3 palisade.
  Neoterra    Security compound: slim concrete dorm towers with glass bands and roof watch posts (child) at the
              corners, a steel-bar perimeter fence on a concrete plinth with a sliding steel gate and guard booth,
              a glass-fronted HQ (armoury + briefing room) and a shooting range. L3 HQ upper floor, L5 helipad.
Gatehouse / wall guard tower: see the section headers below.
"""
from hm import Design, design, AIR, D4, OPP, CW, KEEP

ST = lambda m, f, h="bottom", s="straight": f"{m}_stairs[facing={f},half={h},shape={s},waterlogged=false]"
SL = lambda m, t="bottom": f"{m}_slab[type={t},waterlogged=false]"
TD = lambda m, f, h="top", o="false": f"{m}_trapdoor[facing={f},half={h},open={o},powered=false,waterlogged=false]"
LOG = lambda m, a="y": f"{m}[axis={a}]"
LANT = "lantern[hanging=true,waterlogged=false]"
LANT_S = "lantern[hanging=false,waterlogged=false]"
ROD = lambda f="up": f"lightning_rod[facing={f},powered=false,waterlogged=false]"
ENDROD = lambda f="up": f"end_rod[facing={f}]"
CHAIN = "chain[axis=y,waterlogged=false]"


def soft(d, fn, *a, **k):
    """Run a drawing helper so that it only writes into air cells."""
    orig = d.set

    def s(x, y, z, b, te=None):
        if d.bp.inside(x, y, z) and d.air(x, y, z):
            orig(x, y, z, b, te)
    d.set = s
    try:
        return fn(*a, **k)
    finally:
        del d.set


def ladder(d, x, z, y1, y2, facing):
    for y in range(y1, y2 + 1):
        d.set(x, y, z, f"ladder[facing={facing},waterlogged=false]")


def dummy(d, x, y, z, facing="north", head="carved_pumpkin"):
    d.set(x, y, z, "oak_fence")
    d.set(x, y + 1, z, "hay_block[axis=y]")
    d.set(x, y + 2, z, f"{head}[facing={facing}]")


def weapon_rack(d, cells, y, wood):
    for x, z in cells:
        d.set(x, y, z, SL(wood, "top"))
        d.set(x, y + 1, z, ROD())


def butt(d, x, y, z, facing="west"):
    """Archery butt: hay bale with the target on top (target counted as a yard fixture)."""
    d.set(x, y, z, "hay_block[axis=y]")
    d.yard_item(x, y + 1, z, "target")


def stone_mix(x, y, z, base="stone_bricks"):
    h = (x * 7 + y * 13 + z * 5) % 11
    if h == 0:
        return "mossy_stone_bricks"
    if h == 1:
        return "andesite" if base == "stone_bricks" else base
    return base


def beds(d, y, slots, n, color=None, ox=0, oz=0):
    for x, z, f in slots[:n]:
        d.bed(ox + x, y, oz + z, f, color)


def split(total, floors, cap):
    """Distribute `total` beds over `floors` as evenly as possible (max `cap` each)."""
    out = []
    left = total
    for i in range(floors):
        k = -(-left // (floors - i))
        out.append(min(cap, k))
        left -= out[-1]
    return out


# ============================================================================================ shared toolkit
class _ShiftBP:
    """Blueprint view with an (ox, oz) offset: lets a layout keep its coordinates while the plot grows on the
    west / north side."""
    def __init__(self, bp, ox, oz):
        self._bp, self._ox, self._oz = bp, ox, oz

    def inside(self, x, y, z):
        return self._bp.inside(x + self._ox, y, z + self._oz)

    def get(self, x, y, z):
        return self._bp.get(x + self._ox, y, z + self._oz)

    def set(self, x, y, z, s, te=None):
        return self._bp.set(x + self._ox, y, z + self._oz, s, te)

    def __getattr__(self, k):
        return getattr(self._bp, k)


class Shifted(Design):
    def __init__(self, pack, rel, size, gy=1, paving=None, ox=0, oz=0):
        super().__init__(pack, rel, size, gy=gy, paving=paving)
        self.ox, self.oz = ox, oz
        self._real = self.bp
        self.bp = _ShiftBP(self.bp, ox, oz)

    def finish(self):
        ox, oz = self.ox, self.oz
        self.bp = self._real
        x, y, z = self.hut_pos
        self.hut_pos = (x + ox, y, z + oz)
        self.tags = {(a + ox, b, c + oz): v for (a, b, c), v in self.tags.items()}
        self.child_positions[:] = [(a + ox, b, c + oz, p) for (a, b, c, p) in self.child_positions]
        return super().finish()


WOOD = {"Hearthwood": "dark_oak", "Cascadia": "spruce", "Neoterra": "birch"}
OUT = {"north": (0, -1), "south": (0, 1), "west": (-1, 0), "east": (1, 0)}


def put(d, x, y, z, b, te=None):
    """Set only if inside the plot and currently air (decor that must never clobber structure)."""
    if d.bp.inside(x, y, z) and d.air(x, y, z):
        d.set(x, y, z, b, te)
        return True
    return False


def lamp_post(d, x, z, y=2, h=2, kind="fence"):
    w = WOOD[d.pack]
    if d.pack == "Neoterra":
        for k in range(h + 1):
            put(d, x, y + k, z, "iron_bars" if k else "polished_andesite")
        put(d, x, y + h + 1, z, "sea_lantern")
        put(d, x, y + h + 2, z, "smooth_quartz_slab[type=bottom,waterlogged=false]")
    else:
        for k in range(h + 1):
            put(d, x, y + k, z, f"{w}_fence" if k else ("cobblestone_wall" if d.pack == "Hearthwood" else LOG("spruce_log")))
        put(d, x, y + h + 1, z, LANT_S)


def bench(d, x, z, back, y=2, n=2, along="x"):
    w = WOOD[d.pack]
    dx, dz = (1, 0) if along == "x" else (0, 1)
    for i in range(n):
        put(d, x + dx * i, y, z + dz * i, ST(w, back))
    for s_ in (-1, n):
        put(d, x + dx * s_, y, z + dz * s_, TD(w, ("west" if s_ < 0 else "east") if along == "x" else
                                              ("north" if s_ < 0 else "south"), "bottom", "true"))


def tree(d, x, z, h=4, y=2, kind=None):
    kind = kind or {"Hearthwood": "oak", "Cascadia": "spruce", "Neoterra": "birch"}[d.pack]
    for k in range(h):
        put(d, x, y + k, z, LOG(f"{kind}_log"))
    leaves = f"{kind}_leaves[distance=1,persistent=true,waterlogged=false]"
    top = y + h
    r = 2 if kind != "spruce" else 1
    for yy in range(top - 2, top + 2):
        rr = r if yy < top else 1
        if kind == "spruce":
            rr = 2 if yy < top - 1 else (1 if yy < top + 1 else 0)
        for a in range(-rr, rr + 1):
            for b in range(-rr, rr + 1):
                if abs(a) + abs(b) <= rr + (1 if rr > 1 else 0):
                    put(d, x + a, yy, z + b, leaves)
    put(d, x, top + 1, z, leaves)


def flowers(d, cells, y=2):
    """Flower bed on the hand-listed cells: soil under each, a flower chosen by the cell."""
    fl = {"Hearthwood": ("poppy", "oxeye_daisy", "cornflower", "allium", "azure_bluet"),
          "Cascadia": ("fern", "lily_of_the_valley", "fern", "blue_orchid", "short_grass"),
          "Neoterra": ("azure_bluet", "white_tulip", "short_grass", "blue_orchid", "allium")}[d.pack]
    for x, z in cells:
        if d.bp.inside(x, y - 1, z):
            d.set(x, y - 1, z, "grass_block[snowy=false]" if d.pack != "Cascadia" else "podzol[snowy=false]")
        put(d, x, y, z, fl[(x * 3 + z * 5) % len(fl)])


def carpet(d, y, cells, color):
    for x, z in cells:
        put(d, x, y, z, f"{color}_carpet")


def hedge(d, cells, y=2):
    leaves = {"Hearthwood": "oak_leaves", "Cascadia": "spruce_leaves", "Neoterra": "azalea_leaves"}[d.pack]
    for x, z in cells:
        put(d, x, y, z, f"{leaves}[distance=1,persistent=true,waterlogged=false]")


def cart(d, x, z, along="x", y=2):
    """Hand cart / wagon: plank bed on two wheels, sacks and a barrel on it."""
    w = WOOD[d.pack]
    dx, dz = (1, 0) if along == "x" else (0, 1)
    for i in range(3):
        put(d, x + dx * i, y, z + dz * i, SL(w, "top"))
    put(d, x + dx, y + 1, z + dz, "white_wool" if d.pack != "Neoterra" else "light_gray_wool")
    put(d, x + 2 * dx, y + 1, z + 2 * dz, "barrel[facing=up,open=false]")
    put(d, x - dx, y, z - dz, f"{w}_fence")


def style_of(d, style):
    return style or d.pack


def axb(b, ax="y"):
    """Add an axis to log-like blocks."""
    if "[" in b:
        return b
    if b.endswith("_log") or b.endswith("_wood") or b.endswith("_stem") or b.endswith("_hyphae") \
            or b in ("hay_block", "quartz_pillar", "bone_block", "basalt", "polished_basalt"):
        return f"{b}[axis={ax}]"
    return b


def bld(d, x1, z1, x2, z2, n=1, axis="x", doors=(), style=None, roof=True, sh=4, win=3, chimney=None,
        lad=None, y0=2, upper_doors=(), deco=True, pal=None):
    """A building: walls/floors/windows/doors/roof in the pack style, materials from `pal` (each add-on building
    gets its own palette). n storeys of height sh (walk levels y0, y0+sh, ...; deck at walk+sh-1). doors: (x, z)
    wall cells. lad: (x, z, facing) interior ladder through all decks. Returns (walk levels, ceiling y, ridge y)."""
    st = style or d.pack
    P = dict(pal or {})
    w = P.get("door", WOOD[d.pack])
    shut = P.get("shut", w)
    ys = [y0 + sh * i for i in range(n)]
    top = y0 + sh * n - 1
    door_cells = {(x, z) for x, z in doors}

    def wall(i, x, y, z, corner):
        ax = "x" if z in (z1, z2) else "z"
        if st == "hwstone":
            return "polished_andesite" if corner and y % 2 else stone_mix(x, y, z, P.get("w0", "stone_bricks"))
        if st == "Hearthwood":
            if i == 0:
                if y == y0:
                    return P.get("plinth", "cobblestone") if (x + z) % 3 else P.get("plinth2", "mossy_cobblestone")
                if corner:
                    return P.get("quoin", "polished_andesite") if y % 2 else P.get("quoin2", "stone_bricks")
                w0 = P.get("w0", "stone_bricks")
                return stone_mix(x, y, z) if w0 == "stone_bricks" else w0
            stud = corner or ((x - x1) % 2 == 0 if z in (z1, z2) else (z - z1) % 2 == 0)
            return axb(P.get("frame", "stripped_dark_oak_log")) if stud else P.get("w1", "calcite")
        if st == "Cascadia":
            if i == 0 and y == y0:
                return rock(x, y, z)
            if corner:
                return axb(P.get("corner", "stripped_spruce_log"))
            return axb(P.get("w0" if i == 0 else "w1", P.get("w0", "spruce_log")), ax)
        if corner:
            return P.get("corner", "light_gray_concrete")
        return P.get("w0" if i == 0 else "w1", P.get("w0", "white_concrete"))

    def band(x, z):
        ax = "x" if z in (z1, z2) else "z"
        dflt = {"hwstone": "polished_andesite", "Hearthwood": "dark_oak_log", "Cascadia": "stripped_spruce_log",
                "Neoterra": "cyan_terracotta"}[st]
        return axb(P.get("band", dflt), ax)
    deck = P.get("deck", {"Hearthwood": "oak_planks", "hwstone": "oak_planks", "Cascadia": "spruce_planks",
                          "Neoterra": "light_gray_concrete"}[st])
    floor0 = P.get("floor", {"Hearthwood": "oak_planks", "hwstone": "spruce_planks", "Cascadia": "spruce_planks",
                             "Neoterra": "polished_diorite"}[st])
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            edge = x in (x1, x2) or z in (z1, z2)
            corner = x in (x1, x2) and z in (z1, z2)
            d.set(x, y0 - 1, z, floor0 if not edge else d.get(x, y0 - 1, z))
            for i, y in enumerate(ys):
                for yy in range(y, y + sh):
                    if yy == y + sh - 1:
                        d.set(x, yy, z, band(x, z) if edge else (deck if i < n - 1 else
                              ("smooth_stone" if st == "Neoterra" else deck)))
                    elif edge:
                        d.set(x, yy, z, wall(i, x, yy, z, corner))
                    else:
                        d.set(x, yy, z, AIR)
    glass_n = P.get("glass", "glass_pane")
    for i, y in enumerate(ys):
        for side in ("n", "s", "w", "e"):
            if side in "ns":
                z = z1 if side == "n" else z2
                cells = [(x, z) for x in range(x1 + 2, x2 - 1)]
                out = "north" if side == "n" else "south"
                along = x2 - x1
            else:
                x = x1 if side == "w" else x2
                cells = [(x, z) for z in range(z1 + 2, z2 - 1)]
                out = "west" if side == "w" else "east"
                along = z2 - z1
            for k, (x, z) in enumerate(cells):
                if any(abs(x - a) + abs(z - b) <= 1 for a, b in door_cells):
                    continue
                if st == "Neoterra":
                    if along >= 6 or k % 2 == 0:
                        g = glass_n if i == 0 else P.get("glass2", "light_gray_stained_glass_pane")
                        for yy in range(y + 1, y + sh - 1):
                            d.set(x, yy, z, g)
                        if P.get("fin") and k % 3 == 0:          # coloured vertical fins
                            for yy in range(y, y + sh - 1):
                                d.set(x, yy, z, P["fin"])
                    continue
                if k % win != (win // 2) % max(1, len(cells)):
                    continue
                hi = y + sh - 2
                for yy in range(y + 1, hi + 1):
                    d.set(x, yy, z, glass_n)
    for x, z in doors:
        f = "south" if z == z1 else "north" if z == z2 else "east" if x == x1 else "west"
        d.door(x, y0, z, f, w)
        if sh > 3:
            d.set(x, y0 + 2, z, P.get("lintel", {"Hearthwood": "chiseled_stone_bricks", "hwstone": "chiseled_stone_bricks",
                                                 "Cascadia": LOG("stripped_spruce_log", "x" if z in (z1, z2) else "z"),
                                                 "Neoterra": "glass"}[st]))
    for x, z, i in upper_doors:
        f = "south" if z == z1 else "north" if z == z2 else "east" if x == x1 else "west"
        d.door(x, ys[i], z, f, w)
    if lad:
        lx, lz, lf = lad
        ladder(d, lx, lz, y0, ys[-1] - 1, lf)
    ridge = top
    if roof:
        if st == "Neoterra":
            d.flat(x1, z1, x2, z2, top, P.get("roofdeck", "smooth_quartz"), P.get("parapet", "white_concrete"),
                   P.get("coping", "smooth_quartz_slab"))
            if P.get("green"):                              # green roof
                for x in range(x1 + 2, x2 - 1):
                    for z in range(z1 + 2, z2 - 1):
                        d.set(x, top, z, "moss_block")
            ridge = top + 2
        else:
            rf = P.get("roof", "dark_oak" if st == "Cascadia" else "deepslate_tile")
            rslab = P.get("ridge", LOG("stripped_spruce_log", axis) if st == "Cascadia" else f"{rf}_slab")
            gend = P.get("gable", "spruce_planks" if st == "Cascadia" else
                         ("calcite" if st == "Hearthwood" and n > 1 else "stone_bricks"))
            ridge = soft(d, d.gable, x1, z1, x2, z2, top + 1, axis, f"{rf}_stairs", rslab, gend, 1)
            ends = [(x1, z) for z in range(z1, z2 + 1)] + [(x2, z) for z in range(z1, z2 + 1)] if axis == "x" else \
                [(x, z1) for x in range(x1, x2 + 1)] + [(x, z2) for x in range(x1, x2 + 1)]
            beam = P.get("beam", "dark_oak_log" if st != "Cascadia" else "stripped_spruce_log")
            for x, z in ends:
                if d.get(x, top + 1, z) == "minecraft:" + gend:
                    d.set(x, top + 1, z, axb(beam, "x" if axis == "z" else "z"))
    if chimney:
        cx, cz = chimney
        mat = P.get("chimney", {"Hearthwood": "bricks", "hwstone": "stone_bricks", "Cascadia": "cobblestone",
                                "Neoterra": "light_gray_concrete"}[st])
        for y in range(y0, ridge + 3):
            d.set(cx, y, cz, rock(cx, y, cz) if mat == "rock" else mat)
        d.set(cx, ridge + 3, cz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    return ys, top, ridge

# Palettes of the add-on buildings: every building of every type gets its own roof / wall / trim / accent mix
# from the pack family (Hearthwood: Cotswold sandstone, brick, colour-washed plaster, blue/red/rose/brown roofs;
# Cascadia: dark-oak, red-cedar, birch siding, metal / shake / cedar roofs; Neoterra: concrete, blackstone,
# terracotta panels, copper, green roofs, coloured fins).
PAL = {
    # gatehouse: guard barracks (west of the road) and armoury / stable (east)
    ("gh", "Hearthwood", "a"): dict(w0="smooth_sandstone", plinth="sandstone", plinth2="cut_sandstone",
                                    quoin="cut_sandstone", quoin2="smooth_sandstone", w1="white_terracotta",
                                    frame="stripped_oak_log", band="oak_log", roof="dark_prismarine",
                                    gable="white_terracotta", beam="oak_log", shut="warped", door="oak",
                                    chimney="sandstone", deck="birch_planks"),
    ("gh", "Hearthwood", "b"): dict(w0="bricks", plinth="stone_bricks", plinth2="stone_bricks", quoin="stone_bricks",
                                    quoin2="polished_andesite", roof="mud_brick", gable="bricks", shut="mangrove",
                                    door="spruce", awning="red_wool", floor="bricks"),
    ("gh", "Cascadia", "a"): dict(w0="dark_oak_log", corner="stripped_dark_oak_log", band="stripped_spruce_log",
                                  roof="dark_prismarine", ridge="dark_prismarine_slab", gable="dark_oak_planks",
                                  shut="mangrove", door="dark_oak", deck="dark_oak_planks"),
    ("gh", "Cascadia", "b"): dict(w0="mangrove_planks", corner="stripped_spruce_log", band="stripped_birch_log",
                                  roof="spruce", ridge="spruce_slab", gable="mangrove_planks", shut="birch",
                                  door="spruce", beam="stripped_birch_log"),
    ("gh", "Neoterra", "a"): dict(w0="light_gray_concrete", corner="gray_concrete", band="cyan_concrete",
                                  fin="cyan_concrete", roofdeck="smooth_stone", parapet="light_gray_concrete",
                                  coping="smooth_stone_slab", green=True),
    ("gh", "Neoterra", "b"): dict(w0="polished_blackstone_bricks", corner="polished_blackstone", band="orange_concrete",
                                  fin="orange_terracotta", parapet="polished_blackstone", coping="polished_blackstone_slab",
                                  roofdeck="gray_concrete", glass="gray_stained_glass_pane", awning="orange_wool"),
    # wall guard tower: shed, guardhouse, smithy / armoury, long hall
    ("wt", "Hearthwood", "shed"): dict(w0="mud_bricks", quoin="packed_mud", quoin2="mud_bricks", roof="spruce",
                                       gable="mud_bricks", door="spruce"),
    ("wt", "Hearthwood", "a"): dict(w0="bricks", plinth="stone_bricks", plinth2="stone_bricks", quoin="bricks",
                                    quoin2="bricks", w1="yellow_terracotta", frame="stripped_oak_log", band="oak_log",
                                    roof="granite", gable="yellow_terracotta", beam="oak_log", shut="mangrove",
                                    door="oak"),
    ("wt", "Hearthwood", "b"): dict(w0="stone_bricks", w1="mud_bricks", frame="stripped_spruce_log", band="spruce_log",
                                    roof="brick", gable="mud_bricks", shut="spruce", door="spruce", awning="black_wool",
                                    floor="polished_andesite"),
    ("wt", "Hearthwood", "c"): dict(w0="cobblestone", w1="white_terracotta", frame="stripped_dark_oak_log",
                                    roof="spruce", ridge="spruce_slab", gable="white_terracotta", shut="bamboo",
                                    door="dark_oak"),
    ("wt", "Cascadia", "shed"): dict(w0="birch_planks", corner="stripped_birch_log", roof="spruce", gable="birch_planks"),
    ("wt", "Cascadia", "a"): dict(w0="stripped_spruce_log", corner="spruce_log", band="dark_oak_log", roof="mangrove",
                                  ridge="mangrove_slab", gable="mangrove_planks", shut="spruce", door="mangrove"),
    ("wt", "Cascadia", "b"): dict(w0="cobblestone", w1="spruce_log", corner="spruce_log", band="spruce_log",
                                  roof="cobbled_deepslate", ridge="cobbled_deepslate_slab", gable="spruce_planks",
                                  shut="dark_oak", door="dark_oak", chimney="rock"),
    ("wt", "Cascadia", "c"): dict(w0="birch_planks", corner="stripped_spruce_log", band="green_terracotta",
                                  roof="spruce", gable="birch_planks", shut="spruce", door="spruce",
                                  beam="stripped_spruce_log"),
    ("wt", "Neoterra", "shed"): dict(w0="gray_concrete", corner="polished_andesite", band="yellow_concrete"),
    ("wt", "Neoterra", "a"): dict(w0="white_concrete", w1="mangrove_planks", corner="stripped_mangrove_log",
                                  band="light_gray_concrete", green=True),
    ("wt", "Neoterra", "b"): dict(w0="gray_concrete", corner="polished_deepslate", band="yellow_concrete",
                                  fin="yellow_concrete", parapet="gray_concrete", coping="smooth_stone_slab"),
    ("wt", "Neoterra", "c"): dict(w0="cyan_terracotta", w1="white_terracotta", corner="quartz_pillar",
                                  band="cut_copper", parapet="cut_copper", coping="cut_copper_slab"),
}


# =========================================================================================== BARRACKS TOWERS
# --- Hearthwood: round stone tower, 9x9 box ----------------------------------------------------------------
HW_RING = ["...###...",
           ".##...##.",
           ".#.....#.",
           "#.......#",
           "#.......#",
           "#.......#",
           ".#.....#.",
           ".##...##.",
           "...###..."]


def mask(rows):
    foot, wall, inner = set(), set(), set()
    for z, row in enumerate(rows):
        xs = [x for x, c in enumerate(row) if c == "#"]
        for x in range(min(xs), max(xs) + 1):
            foot.add((x, z))
            (wall if row[x] == "#" else inner).add((x, z))
    return foot, wall, inner


HW_FOOT, HW_WALL, HW_IN = mask(HW_RING)
HW_TB = 9                                   # tower box
HW_THUT = (6, 1, 2)
HW_TST = {1: 2, 2: 3, 3: 3, 4: 4, 5: 5}     # storeys incl. the ground-floor guard room
HW_TSY = 4 * 5 + 7
HW_BED_SLOTS = [(3, 1, "north"), (5, 7, "south"), (5, 1, "north"), (3, 7, "south"), (7, 3, "east"),
                (7, 5, "east")]


def bt_hearthwood(rel, L):
    n = HW_TST[L]
    top = 4 * n
    d = Design("Hearthwood", rel, (HW_TB, HW_TSY, HW_TB), gy=0, paving="spruce_planks")
    for x in range(HW_TB):
        for z in range(HW_TB):
            if (x, z) not in HW_FOOT:
                for y in range(HW_TSY):
                    d.set(x, y, z, KEEP)
    for (x, z) in HW_WALL:
        d.set(x, 0, z, "cobblestone")
        for y in range(1, top + 2):
            d.set(x, y, z, stone_mix(x, y, z))
        d.set(x, 1, z, "cobblestone" if (x + z) % 3 else "mossy_cobblestone")
        # merlons on the parapet
        if (x + z) % 2 == 0:
            d.set(x, top + 2, z, stone_mix(x, top + 2, z))
    # string courses at the floors
    for k in range(1, n + 1):
        for (x, z) in HW_WALL:
            d.set(x, 4 * k, z, "polished_andesite" if k < n else "stone_bricks")
        for (x, z) in HW_IN:
            d.set(x, 4 * k, z, "spruce_planks" if k < n else "stone_bricks")
    # doors north and south, ladder on the west wall up to the roof
    d.door(4, 1, 0, "south", "spruce")
    d.door(4, 1, 8, "north", "spruce")
    d.set(4, 3, 0, "chiseled_stone_bricks")
    d.set(4, 3, 8, "chiseled_stone_bricks")
    ladder(d, 1, 4, 1, top, "east")
    # arrow slits
    for k in range(n):
        y = 4 * k + 2
        d.set(8, y, 4, "glass_pane")
        if k:
            d.set(4, y, 0, "glass_pane")
            d.set(4, y, 8, "glass_pane")
        d.set(1, y + 1, 1, "glass_pane") if k else None
        d.set(7, y + 1, 7, "glass_pane") if k else None
    # ground floor: guard room
    d.hut(*HW_THUT)
    weapon_rack(d, [(7, 3), (7, 5)], 1, "spruce")
    d.set(7, 1, 4, "chest[facing=west,type=single,waterlogged=false]")
    d.keg(2, 1, 6, "east")
    d.keg(2, 2, 6, "north")
    d.banner(7, 3, 4, "west", "red")
    d.lamp(4, 3, 4)
    # bunk floors
    per = split(4 * L, n - 1, 6)
    for k in range(1, n):
        y = 4 * k + 1
        m = per[k - 1]
        beds(d, y, HW_BED_SLOTS, m, "red")
        d.set(1, y, 3, "chest[facing=east,type=single,waterlogged=false]")
        if m <= 4:
            weapon_rack(d, [(7, 3), (7, 5)], y, "spruce")
            d.banner(7, y + 2, 4, "west", "white" if k % 2 else "red")
        else:
            d.set(7, y, 4, SL("spruce", "top"))
            d.candle(7, y + 1, 4, 2)
        carpet(d, y, [(x, z) for x in range(3, 5 + 1) for z in range(3, 5 + 1)], "red")
        d.lamp(4, y + 2, 4)
        # footlockers, shelves, banners
        for x, z in ((4, 1), (4, 7), (1, 5)):
            if d.air(x, y, z):
                d.set(x, y, z, "chest[facing=%s,type=single,waterlogged=false]" % ("south" if z == 1 else "north" if z == 7 else "east"))
        for x, z in ((6, 2), (2, 2)):
            if d.air(x, y, z):
                d.set(x, y, z, SL("spruce", "top"))
                d.set(x, y + 1, z, "decorated_pot[cracked=false,facing=south,waterlogged=false]" if x == 6 else "potted_red_tulip")
        put(d, 2, y, 6, "barrel[facing=north,open=false]")
        for z in (3, 5):
            put(d, 1, y + 2, z, f"{'red' if z == 3 else 'white'}_wall_banner[facing=east]")
    # ground floor: rug and a small table
    carpet(d, 1, [(x, z) for x in range(3, 5 + 1) for z in range(3, 4 + 1)], "red")
    d.table(4, 1, 6, "spruce")
    d.chair(4, 1, 7, "south", "spruce", sit=False) if d.air(4, 1, 7) else None
    # parapet lanterns
    for x, z in ((0, 3), (8, 5), (3, 0), (5, 8)):
        d.set(x, top + 2, z, LANT_S)
    # roof: battlements, brazier, flag at L5
    d.set(6, top + 1, 6, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    if L >= 4:
        for y in range(top + 1, top + 6):
            d.set(4, y, 4, "spruce_fence")
        d.set(5, top + 5, 4, "red_wool")
        d.set(6, top + 5, 4, "red_wool")
        d.set(5, top + 4, 4, "white_wool")
        d.set(6, top + 4, 4, "red_wool") if L == 5 else None
    return d


# --- Cascadia: log blockhouse, 9x9 box (7x7 stone ground storey, 9x9 overhanging log storeys) --------------
CS_TB = 9
CS_THUT = (2, 1, 2)
CS_TUP = {1: 1, 2: 1, 3: 2, 4: 2, 5: 3}     # overhanging log storeys
CS_TSY = 24
CS_BED_SLOTS = [(1, 1, "west"), (7, 1, "east"), (1, 7, "west"), (7, 7, "east"), (1, 3, "west"), (7, 3, "east"),
                (1, 5, "west"), (7, 5, "east")]
RIVER = ["cobblestone", "mossy_cobblestone", "andesite", "cobblestone", "tuff", "mossy_cobblestone"]


def rock(x, y, z):
    return RIVER[(x * 5 + z * 3 + y * 7) % len(RIVER)]


def bt_cascadia(rel, L):
    nu = CS_TUP[L]
    d = Design("Cascadia", rel, (CS_TB, CS_TSY, CS_TB), gy=0, paving="spruce_planks")
    roof_y = 4 * (nu + 1) + 1
    for x in range(CS_TB):
        for z in range(CS_TB):
            ground = 1 <= x <= 7 and 1 <= z <= 7
            for y in range(0, 4 if not ground else 0):
                d.set(x, y, z, KEEP)
            for y in range(roof_y + 6, CS_TSY):
                d.set(x, y, z, KEEP)
    # ground storey: river-rock walls
    for x in range(1, 8):
        for z in range(1, 8):
            if x in (1, 7) or z in (1, 7):
                for y in range(0, 4):
                    d.set(x, y, z, rock(x, y, z))
    d.door(4, 1, 1, "south", "spruce")
    d.door(4, 1, 7, "north", "spruce")
    for z in (3, 5):
        d.set(1, 2, z, "spruce_fence")
        d.set(7, 2, z, "spruce_fence")
    # overhanging log storeys
    for k in range(1, nu + 1):
        d.fill(0, 4 * k, 0, 8, 4 * k, 8, "spruce_planks")
        for x in range(9):
            for z in range(9):
                if x in (0, 8) or z in (0, 8):
                    d.set(x, 4 * k, z, LOG("dark_oak_log", "x" if z in (0, 8) else "z"))
                    corner = x in (0, 8) and z in (0, 8)
                    for y in range(4 * k + 1, 4 * k + 4):
                        d.set(x, y, z, LOG("spruce_log") if corner else
                              LOG("stripped_spruce_log", "x" if z in (0, 8) else "z"))
        y = 4 * k + 2
        for x, z in ((0, 4), (8, 4), (4, 0), (4, 8), (2, 0), (6, 0), (2, 8), (6, 8)):
            d.set(x, y, z, "glass_pane")
        # murder-hole trapdoors under the overhang
        for x in (2, 4, 6):
            d.set(x, 4 * k - 1, 0, TD("spruce", "south", "top")) if k == 1 else None
            d.set(x, 4 * k - 1, 8, TD("spruce", "north", "top")) if k == 1 else None
    top = 4 * (nu + 1)
    d.fill(0, top, 0, 8, top, 8, "spruce_planks")
    for x in range(9):
        for z in range(9):
            if x in (0, 8) or z in (0, 8):
                d.set(x, top, z, LOG("dark_oak_log", "x" if z in (0, 8) else "z"))
    ridge = d.hip(0, 0, 8, 8, top + 1, "dark_oak_stairs", "dark_oak_slab", overhang=0)
    if L >= 3:                                                     # lookout lantern on the roof peak
        d.set(4, ridge + 1, 4, "spruce_fence")
        d.set(4, ridge + 2, 4, LANT_S)
    # central post + ladder
    for y in range(1, top):
        d.set(4, y, 5, LOG("stripped_spruce_log"))
    ladder(d, 4, 4, 1, 4 * nu, "north")
    # ground floor: store and guard room
    d.hut(*CS_THUT)
    d.set(6, 1, 2, "barrel[facing=up,open=false]")
    d.set(6, 2, 2, "barrel[facing=up,open=false]")
    d.set(6, 1, 6, "chest[facing=west,type=single,waterlogged=false]")
    d.set(2, 1, 6, "spruce_log[axis=z]")
    d.set(2, 2, 6, "spruce_log[axis=z]")
    d.set(3, 3, 3, LANT)
    carpet(d, 1, [(x, z) for x in range(3, 3 + 1) for z in range(3, 3 + 1)], "brown")
    put(d, 6, 1, 4, SL("spruce", "top"))
    put(d, 6, 2, 4, "decorated_pot[cracked=false,facing=west,waterlogged=false]")
    put(d, 5, 3, 6, "green_wall_banner[facing=north]") if False else None
    weapon_rack(d, [(2, 4)], 1, "spruce") if d.air(2, 1, 4) else None
    # bunk rooms
    per = split(4 * L, nu, 8)
    for k in range(1, nu + 1):
        y = 4 * k + 1
        beds(d, y, CS_BED_SLOTS, per[k - 1], "brown")
        for x, z in ((1, 2), (1, 6), (7, 4)):                    # footlockers between the bunks
            d.set(x, y, z, "chest[facing=%s,type=single,waterlogged=false]" % ("east" if x == 1 else "west"))
        d.set(3, y + 2, 4, LANT)
        d.set(5, y + 2, 6, LANT)
        for x in (3, 5):
            for z in (1, 2, 3, 6, 7):
                put(d, x, y, z, "brown_carpet" if z % 2 else "green_carpet")
        put(d, 4, y, 1, "green_carpet")
        put(d, 4, y + 2, 7, "green_wall_banner[facing=north]")
        put(d, 4, y + 2, 1, "white_wall_banner[facing=south]")
        put(d, 4, y + 1, 6, "spruce_trapdoor[facing=south,half=top,open=true,powered=false,waterlogged=false]") \
            if False else None
    return d


# --- Neoterra: slim concrete dorm tower, 7x7 ----------------------------------------------------------------
NT_TB = 7
NT_THUT = (1, 1, 1)
NT_TSY = 30
NT_BED_SLOTS = [(1, 1, "west"), (5, 1, "east"), (1, 5, "west"), (5, 5, "east")]


def bt_neoterra(rel, L):
    n = L + 1
    top = 4 * n
    d = Design("Neoterra", rel, (NT_TB, NT_TSY, NT_TB), gy=0, paving="polished_diorite")
    for x in range(7):
        for z in range(7):
            if x in (0, 6) or z in (0, 6):
                corner = x in (0, 6) and z in (0, 6)
                for y in range(1, top + 1):
                    d.set(x, y, z, "light_gray_concrete" if corner else "white_concrete")
    for k in range(1, n + 1):
        d.fill(1, 4 * k, 1, 5, 4 * k, 5, "light_gray_concrete" if k < n else "smooth_stone")
        for x in range(7):
            for z in range(7):
                if (x in (0, 6) or z in (0, 6)) and not (x in (0, 6) and z in (0, 6)):
                    d.set(x, 4 * k, z, "cyan_terracotta")
    # ribbon windows
    for k in range(n):
        y = 4 * k + 2
        for a in (2, 3, 4):
            for yy in (y, y + 1):
                if k:
                    d.set(a, yy, 0, "glass_pane")
                    d.set(a, yy, 6, "glass_pane")
                d.set(0, yy, a, "light_gray_stained_glass_pane")
                d.set(6, yy, a, "light_gray_stained_glass_pane")
    for z in (0, 6):
        for x in (2, 4):
            d.window(x, 1, z, x, 3, z)
    d.door(3, 1, 0, "south", "birch")
    d.door(3, 1, 6, "north", "birch")
    d.set(3, 3, 0, "glass")
    d.set(3, 3, 6, "glass")
    # lift core + ladder
    for y in range(1, top):
        d.set(3, y, 3, "light_gray_concrete")
    ladder(d, 3, 2, 1, top, "north")
    d.hut(*NT_THUT)
    d.set(5, 1, 1, "smooth_quartz_slab[type=top,waterlogged=false]")
    d.set(5, 1, 5, "light_gray_shulker_box[facing=up]")
    d.set(1, 1, 5, "potted_bamboo")
    d.set(3, 3, 4, "sea_lantern")
    for k in range(1, n):
        y = 4 * k + 1
        beds(d, y, NT_BED_SLOTS, 4, "cyan")
        d.set(1, y, 3, "smooth_quartz_slab[type=top,waterlogged=false]")
        d.set(1, y + 1, 3, "potted_bamboo" if k % 2 else "potted_cactus")
        d.set(5, y, 3, "light_gray_shulker_box[facing=up]")
        d.set(3, y + 2, 4, "sea_lantern")
        for x, z in ((3, 1), (3, 4), (3, 5), (2, 2), (4, 2), (2, 4), (4, 4)):
            put(d, x, y, z, "cyan_carpet" if (x + z) % 2 else "light_gray_carpet")
        put(d, 5, y + 1, 3, "potted_bamboo") if d.get(5, y, 3).endswith("shulker_box[facing=up]") else None
        put(d, 3, y + 2, 1, "cyan_wall_banner[facing=south]")
    # roof watch post: glass rail, searchlight, antenna
    for x in range(7):
        for z in range(7):
            if x in (0, 6) or z in (0, 6):
                d.set(x, top + 1, z, "light_gray_concrete" if x in (0, 6) and z in (0, 6) else
                      "light_gray_stained_glass_pane")
    d.set(5, top + 1, 5, "sea_lantern")
    d.set(5, top + 2, 5, "daylight_detector[inverted=false,power=0]")
    for y in range(top + 2, top + 5):
        d.set(0, y, 0, ROD() if y == top + 4 else "iron_bars")
    if L >= 3:
        d.set(6, top + 2, 6, ENDROD())
        d.set(6, top + 2, 0, ENDROD())
        d.set(0, top + 2, 6, ENDROD())
    return d


@design("barrackstower")
def barrackstower(pack, rel, L):
    d = {"Hearthwood": bt_hearthwood, "Cascadia": bt_cascadia, "Neoterra": bt_neoterra}[pack](rel, L)
    common_materials(d, L)
    return d


TOWER = "military/barrackstower0.blueprint"


# ================================================================================================ BARRACKS
def hw_bar(rel, L):
    S = 33
    d = Shifted("Hearthwood", rel, (S, HW_TSY + 2, S + 19), gy=1, paving="grass_block[snowy=false]", oz=19)
    boxes = {"SW": (1, 23), "SE": (23, 23), "NW": (1, 1), "NE": (23, 1)}
    order = ["SW", "SE", "NW", "NE"]
    built = order[:min(L, 4)]
    full = L >= 3
    # bailey ground
    d.fill(4, 1, 4, 28, 1, 28, "coarse_dirt")
    for x in range(15, 18):
        for z in range(2, 19):
            d.set(x, 1, z, "gravel" if (x + z) % 4 else "cobblestone")
    # ---- walls ----------------------------------------------------------------------------------------
    def wall_cells():
        cells = []   # (x, z, role) role: 'out' = outer (parapet) line, 'in' = walk line
        for z in range(3, 30):
            cells.append((3, z, "out"))
            cells.append((4, z, "in"))
            cells.append((29, z, "out"))
            cells.append((28, z, "in"))
        for x in range(5, 28):
            cells.append((x, 3, "out"))
            cells.append((x, 4, "in"))
            if not 10 <= x <= 22:
                cells.append((x, 29, "out"))
                cells.append((x, 28, "in"))
        return cells

    def keep_cell(x, z):
        """False for cells inside a built tower box that are not right where a wall run meets the tower."""
        for k in built:
            X0, Z0 = boxes[k]
            rx, rz = x - X0, z - Z0
            if 0 <= rx < HW_TB and 0 <= rz < HW_TB:
                bands = {"NW": (rz >= 7 or rx >= 7), "NE": (rz >= 7 or rx <= 1),
                         "SW": (rz <= 1 or rx >= 7), "SE": (rz <= 1 or rx <= 1)}[k]
                return bands
        return True

    for x, z, role in wall_cells():
        if not keep_cell(x, z):
            continue
        gate = 15 <= x <= 17 and z in (3, 4)
        if gate:
            continue
        if full:
            if role == "in" and x not in (3, 29) and z not in (3, 29):
                for y in range(2, 6):
                    d.set(x, y, z, stone_mix(x, y, z))
            else:
                for y in range(2, 7):
                    d.set(x, y, z, stone_mix(x, y, z))
                if (x + z) % 2 == 0:
                    d.set(x, 7, z, stone_mix(x, 7, z))
            d.set(x, 2, z, "cobblestone" if (x * 3 + z) % 4 else "mossy_cobblestone")
        elif role == "out":
            d.set(x, 2, z, "stone_bricks")
            d.set(x, 3, z, "mossy_cobblestone_wall" if (x + z) % 5 == 0 else "cobblestone_wall")
    # wall-walk lanes: inner line top is the walk; make sure the corners of the inner line are walkable
    if full:
        # gate tower with winch room and battlements
        for x in range(13, 20):
            for z in range(2, 6):
                edge = x in (13, 19) or z in (2, 5)
                for y in range(2, 11):
                    d.set(x, y, z, stone_mix(x, y, z) if edge or y in (6, 10) or y < 6 else AIR)
                d.set(x, 11, z, stone_mix(x, 11, z) if edge else AIR)
                if edge and (x + z) % 2 == 1:
                    d.set(x, 12, z, stone_mix(x, 12, z))
        d.clear(15, 2, 2, 17, 5, 5)
        for z in (2, 5):
            d.set(15, 5, z, ST("stone_brick", "west", "top"))
            d.set(17, 5, z, ST("stone_brick", "east", "top"))
            d.set(16, 6, z, "chiseled_stone_bricks")
        for x in range(15, 18):
            d.set(x, 5, 3, "iron_bars")                       # raised portcullis
        for x in (14, 18):                                    # torches on the front
            d.set(x, 4, 1, "wall_torch[facing=north]")
        # doorways from the wall walks into the winch room, chains and winch
        for x, f in ((13, "east"), (19, "west")):
            d.set(x, 7, 4, AIR)
            d.set(x, 8, 4, AIR)
        for x in range(15, 18):
            d.set(x, 7, 3, CHAIN)
            d.set(x, 8, 3, CHAIN)
            d.set(x, 9, 3, CHAIN)
        d.set(16, 7, 4, "grindstone[face=floor,facing=east]")
        ladder(d, 18, 3, 7, 10, "west")
        d.set(14, 9, 4, LANT)
        d.set(16, 8, 2, "glass_pane")
        d.banner(14, 8, 1, "north", "red")
        d.banner(18, 8, 1, "north", "red")
        # stairs up to the wall walk on both side walls
        for xs, inner in ((5, 4), (27, 28)):
            for i in range(4):
                z = 18 - i
                d.set(xs, 2 + i, z, ST("stone_brick", "north"))
                for y in range(2, 2 + i):
                    d.set(xs, y, z, "stone_bricks")
        # stairs up to the north wall walk beside the gate tower
        for i in range(4):
            for x in (11, 21):
                d.set(x, 2 + i, 8 - i, ST("stone_brick", "north"))
                for y in range(2, 2 + i):
                    d.set(x, y, 8 - i, "stone_bricks")
    else:
        for x in (14, 18):                                    # gate posts of the bailey wall
            for y in range(2, 5):
                d.set(x, y, 3, "stone_bricks")
            d.set(x, 5, 3, LANT_S)
    # ---- great hall ---------------------------------------------------------------------------------
    hx1, hz1, hx2, hz2 = 10, 19, 22, 29
    HT = 6 if L < 5 else 10                                   # L5: officers' upper floor
    d.box(hx1, 2, hz1, hx2, HT, hz2, "stone_bricks", floor="oak_planks")
    for x in range(hx1, hx2 + 1):
        for z in range(hz1, hz2 + 1):
            if x in (hx1, hx2) or z in (hz1, hz2):
                for y in range(2, HT + 1):
                    d.set(x, y, z, stone_mix(x, y, z))
                d.set(x, 2, z, "cobblestone" if (x + z) % 3 else "mossy_cobblestone")
    d.fill(hx1 + 1, 7, hz1 + 1, hx2 - 1, 7, hz2 - 1, "dark_oak_planks")
    for x in (hx1, hx2):                                      # buttress-like quoins
        for z in (hz1, hz2):
            for y in range(2, HT + 1):
                d.set(x, y, z, "polished_andesite" if y % 2 else "stone_bricks")
    if HT > 6:
        d.fill(hx1 + 1, HT + 1, hz1 + 1, hx2 - 1, HT + 1, hz2 - 1, "dark_oak_planks")
        for x in range(hx1, hx2 + 1):
            for z in (hz1, hz2):
                d.set(x, 7, z, "polished_andesite")
        for x in (12, 14, 18, 20):
            d.window(x, 8, hz1, x, 9, hz1)
            d.window(x, 8, hz2, x, 9, hz2)
            put(d, x, 8, hz1 - 1, ST("stone_brick", "south", "top"))
            put(d, x, 9, hz1 - 1, "potted_red_tulip") if False else None
        ladder(d, 21, 20, 2, 7, "west")
        w = "dark_oak"                                        # castellan's solar
        lay(d, 8, [(11, 22, BOOK("east")), (11, 23, BOOK("east")), (11, 24, BOOK("east")), (11, 25, BOOK("east")),
                   (11, 27, "lectern[facing=east,has_book=false,powered=false]"), (12, 28, "cartography_table"),
                   (14, 27, SLD(w), CAN3), (15, 27, SLD(w), "flower_pot"), (14, 26, ST(w, "north")),
                   ("bed", 19, 28, "south", "red"), (20, 28, SLD(w), CAN1), (18, 28, CH("north")),
                   (18, 23, ST(w, "west")), (18, 25, ST(w, "west")), (18, 24, SLD(w), CAN1),
                   (19, 23, "red_carpet"), (19, 24, "red_carpet"), (19, 25, "red_carpet"),
                   (11, 20, SLD(w), "potted_red_tulip"), (14, 21, "red_carpet"), (15, 21, "red_carpet"),
                   ("lamp", 14, 24), ("lamp", 16, 22)])
        put(d, 16, 10, 20, "red_wall_banner[facing=south]")
        put(d, 16, 10, 28, "white_wall_banner[facing=north]")
    ridge = soft(d, d.gable, hx1, hz1, hx2, hz2, HT + 1, "x", "deepslate_tile_stairs", "deepslate_tile_slab",
                 "stone_bricks", 1)
    for x in (hx1 - 1, hx2 + 1):                              # keep the roof off the towers
        for z in range(hz1 - 1, hz2 + 2):
            for y in range(5, ridge + 1):
                if "deepslate_tile" in d.get(x, y, z):
                    d.set(x, y, z, AIR)
    for z in range(hz1, hz2 + 1):                             # gable ends: tile-hung top
        for x in (hx1, hx2):
            for y in range(HT + 1, ridge):
                if d.get(x, y, z) == "minecraft:stone_bricks" and (z + y) % 4 == 0:
                    d.set(x, y, z, "mossy_stone_bricks")
    # doorway, leaded windows
    d.door(16, 2, hz1, "south", "dark_oak")
    d.set(16, 4, hz1, "chiseled_stone_bricks")
    d.set(15, 4, hz1, ST("stone_brick", "west", "top"))
    d.set(17, 4, hz1, ST("stone_brick", "east", "top"))
    d.set(15, 3, hz1 - 1, "wall_torch[facing=north]")
    d.set(17, 3, hz1 - 1, "wall_torch[facing=north]")
    for x in (12, 13, 19, 20):
        d.window(x, 3, hz1, x, 5, hz1)
    for x in (13, 19):
        d.window(x, 4, hz2, x, 5, hz2)
    d.set(16, 8, hz1, "glass_pane")
    # interior
    d.hut(11, 2, 20)
    weapon_rack(d, [(11, 22), (11, 23), (11, 24)], 2, "dark_oak")
    d.banner(11, 4, 23, "east", "red")
    d.item(13, 2, 26, "anvil", "east")
    d.item(11, 2, 28, "barrel")
    d.item(12, 2, 28, "barrel")
    d.set(11, 2, 27, "grindstone[face=floor,facing=east]")
    if L >= 3:
        d.item(11, 2, 26, "smithing_table")
    d.set(13, 2, 28, "chest[facing=north,type=single,waterlogged=false]")
    d.set(14, 2, 28, "chest[facing=north,type=single,waterlogged=false]")
    # mess table with benches
    for x in range(15, 19):
        d.table(x, 2, 24, "dark_oak", "block", "dark_oak_planks" if x % 2 else "stripped_dark_oak_wood[axis=x]")
        d.chair(x, 2, 23, "north", "dark_oak", sit=False)
        d.chair(x, 2, 25, "south", "dark_oak", sit=False)
    d.set(15, 3, 24, "candle[candles=3,lit=false,waterlogged=false]")
    d.set(18, 3, 24, "candle[candles=2,lit=false,waterlogged=false]")
    # hearth on the east wall, chimney through the roof
    d.hearth(21, 2, 24, "west", ridge + 3, "bricks", "campfire")
    for y in range(2, ridge + 3):
        d.set(22, y, 24, "bricks")
    carpet(d, 2, [(x, z) for x in range(19, 20 + 1) for z in range(23, 25 + 1)], "red")
    d.banner(21, 4, 21, "west", "red")
    d.banner(21, 4, 27, "west", "white")
    for x in (13, 16, 19):
        d.lamp(x, 6, 22)
        d.lamp(x, 6, 26)
    # ---- bailey -------------------------------------------------------------------------------------
    nt = {1: 2, 2: 3, 3: 4, 4: 5, 5: 5}[L]
    for i in range(nt):
        butt(d, 26, 2, 6 + 2 * i)
    for z in (6, 8, 10, 12, 14):
        d.set(21, 1, z, "stone_bricks")                       # shooting line marks
    for x, z in ((8, 9), (8, 13)):
        dummy(d, x, 2, z, "east")
    d.set(7, 2, 16, "hay_block[axis=x]")
    d.set(8, 2, 16, "hay_block[axis=y]")
    d.set(7, 2, 6, "water_cauldron[level=3]")
    d.set(7, 2, 7, "chest[facing=east,type=single,waterlogged=false]") if L >= 2 else None
    if L >= 2:
        for x, z in ((13, 9), (19, 9)):                       # lantern posts by the path
            d.set(x, 2, z, "cobblestone_wall")
            d.set(x, 3, z, "cobblestone_wall")
            d.set(x, 4, z, LANT_S)
    if L >= 4:                                                # flag pole
        for y in range(2, 11):
            d.set(11, y, 12, "spruce_fence")
        d.set(11, 1, 12, "stone_bricks")
        for x, y in ((12, 10), (13, 10), (12, 9), (13, 9)):
            d.set(x, y, 12, "red_wool" if (x + y) % 2 else "white_wool")
    if L >= 5:                                                # well
        for x in range(19, 22):
            for z in range(12, 15):
                d.set(x, 2, z, "cobblestone" if (x, z) != (20, 13) else "water[level=0]")
                d.set(x, 1, z, "cobblestone")
        for x, z in ((19, 12), (21, 12), (19, 14), (21, 14)):
            d.set(x, 3, z, "spruce_fence")
            d.set(x, 4, z, "spruce_fence")
        d.fill(19, 5, 12, 21, 5, 14, "spruce_slab[type=bottom,waterlogged=false]")
        d.set(20, 4, 13, CHAIN)
        for x in (6, 10, 22, 26):                             # banners along the north wall
            if not 12 <= x <= 20:
                d.banner(x, 5, 5, "south", "red")
    # ---- towers (child huts) --------------------------------------------------------------------------
    for k in built:
        X0, Z0 = boxes[k]
        for (rx, rz) in HW_FOOT:
            d.reserve(X0 + rx, 1, Z0 + rz, X0 + rx, HW_TSY, Z0 + rz)
        d.child_hut(X0 + HW_THUT[0], 2, Z0 + HW_THUT[2], TOWER)
    return d


def cs_bar(rel, L):
    d = Shifted("Cascadia", rel, (45, CS_TSY + 2, 29 + 27), gy=1, paving="grass_block[snowy=false]", ox=12, oz=27)
    boxes = {"SW": (1, 19), "NE": (23, 1), "SE": (23, 19), "NW": (1, 1)}
    order = ["SW", "NE", "SE", "NW"]
    built = order[:min(L, 4)]
    full = L >= 3
    # parade ground
    for x in range(4, 29):
        for z in range(4, 25):
            d.set(x, 1, z, "coarse_dirt" if (x * 3 + z * 7) % 5 else "gravel")
    for x in range(15, 18):
        for z in range(0, 13):
            d.set(x, 1, z, "dirt_path")

    def in_ground(x, z):
        for k in built:
            X0, Z0 = boxes[k]
            if 1 <= x - X0 <= 7 and 1 <= z - Z0 <= 7:
                return True
        return False
    lines = [(3, z) for z in range(3, 26)] + [(29, z) for z in range(3, 26)] + \
            [(x, 3) for x in range(4, 29)] + [(x, 25) for x in range(4, 29)]
    inner = {(3, 0): (4, 0), (29, 0): (28, 0)}
    for x, z in lines:
        if in_ground(x, z) or (15 <= x <= 17 and z == 3):
            continue
        if full:
            for y in range(2, 7):
                d.set(x, y, z, LOG("spruce_log"))
            d.set(x, 7, z, "spruce_fence" if (x + z) % 2 else LOG("stripped_spruce_log"))
            d.set(x, 1, z, rock(x, 1, z))
            # firing step on the inside
            ix, iz = (x + (1 if x == 3 else -1 if x == 29 else 0), z + (1 if z == 3 else -1 if z == 25 else 0))
            if 4 <= ix <= 28 and 4 <= iz <= 24 and not in_ground(ix, iz) and not (14 <= ix <= 18 and iz == 4):
                if d.air(ix, 4, iz):
                    d.set(ix, 4, iz, SL("spruce", "top"))
                if (ix + iz) % 4 == 0 and d.air(ix, 3, iz):
                    for y in (2, 3):
                        d.set(ix, y, iz, "spruce_fence")
        else:
            post = (x + z) % 3 == 0
            d.set(x, 2, z, LOG("spruce_log") if post else "spruce_fence")
            d.set(x, 3, z, "spruce_fence" if post else AIR)
    # gate
    if full:
        for x in (14, 18):
            for z in (2, 3, 4):
                for y in range(2, 10 if z == 3 else 7):
                    d.set(x, y, z, LOG("spruce_log"))
                d.set(x, 1, z, rock(x, 1, z))
            d.set(x, 10, 3, LANT_S)
        for x in range(14, 19):
            for z in (2, 3, 4):
                d.set(x, 6, z, "spruce_planks" if 15 <= x <= 17 else d.get(x, 6, z))
            d.set(x, 7, 2, "spruce_fence")
            d.set(x, 9, 3, LOG("stripped_spruce_log", "x"))
        for x in (15, 17):
            d.set(x, 5, 2, ST("spruce", "east" if x == 15 else "west", "top"))
        ladder(d, 14, 5, 2, 6, "south")
        d.set(14, 6, 5, "ladder[facing=south,waterlogged=false]")
        for x in (15, 16, 17):                                # gate leaves swung open against the palisade
            pass
        d.set(13, 2, 4, TD("spruce", "east", "bottom", "true"))
        d.set(19, 2, 4, TD("spruce", "west", "bottom", "true"))
        d.sign(16, 8, 1, "north", ["FORT", "TIMBERLINE", "~ 1872 ~"], "spruce")
        d.set(16, 8, 2, "spruce_planks")
        d.set(15, 8, 2, "spruce_planks")
        d.set(17, 8, 2, "spruce_planks")
        if L >= 5:                                            # roofed walkway with the alarm bell
            for x in range(13, 20):
                d.set(x, 10, 1, ST("dark_oak", "south"))
                d.set(x, 11, 2, ST("dark_oak", "south"))
                d.set(x, 11, 3, SL("dark_oak"))
                d.set(x, 11, 4, ST("dark_oak", "north"))
                d.set(x, 10, 5, ST("dark_oak", "north"))
            d.set(16, 10, 3, "bell[attachment=ceiling,facing=north,powered=false]")
            d.set(14, 10, 3, LOG("spruce_log"))
            d.set(18, 10, 3, LOG("spruce_log"))
    else:
        for x in (14, 18):
            for y in range(2, 5):
                d.set(x, y, 3, LOG("spruce_log"))
            d.set(x, 5, 3, LANT_S)
    # ---- barracks hall: log building with porch and stone chimney -------------------------------------
    x1, z1, x2, z2 = 11, 13, 21, 21
    d.fill(x1, 1, z1, x2, 1, z2, "cobblestone")
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if x in (x1, x2) or z in (z1, z2):
                corner = x in (x1, x2) and z in (z1, z2)
                for y in range(2, 6):
                    d.set(x, y, z, LOG("stripped_spruce_log") if corner else LOG("spruce_log", "x" if z in (z1, z2) else "z"))
                d.set(x, 2, z, rock(x, 2, z))
            else:
                d.set(x, 1, z, "spruce_planks")
                for y in range(2, 6):
                    d.set(x, y, z, AIR)
    for x in range(x1, x2 + 1):
        d.set(x, 6, z1, LOG("stripped_spruce_log", "x"))
        d.set(x, 6, z2, LOG("stripped_spruce_log", "x"))
    for z in range(z1, z2 + 1):
        d.set(x1, 6, z, LOG("stripped_spruce_log", "z"))
        d.set(x2, 6, z, LOG("stripped_spruce_log", "z"))
    d.fill(x1 + 1, 6, z1 + 1, x2 - 1, 6, z2 - 1, "spruce_planks")
    ridge = d.gable(x1, z1, x2, z2, 7, "x", "dark_oak_stairs", "dark_oak_slab", "spruce_planks", 1)
    for z in range(z1, z2 + 1):                               # board-and-batten gables
        for x in (x1, x2):
            for y in range(7, ridge):
                if d.get(x, y, z) == "minecraft:spruce_planks" and z % 2 == 0:
                    d.set(x, y, z, LOG("stripped_spruce_log"))
    d.door(16, 2, z1, "south", "spruce")
    d.set(16, 4, z1, LOG("stripped_spruce_log", "x"))
    for x in (13, 19):
        d.window(x, 3, z1, x, 4, z1)
        d.window(x, 3, z2, x, 4, z2)
    for z in (15, 19):
        d.window(x1, 3, z, x1, 4, z)
    d.window(16, 8, z1 - 0, 16, 9, z1) if d.get(16, 8, z1) == "minecraft:spruce_planks" else None
    # porch
    for x in range(x1, x2 + 1):
        for z in range(z1 - 3, z1):
            d.set(x, 1, z, "spruce_planks")
            d.set(x, 5, z, SL("spruce"))
        d.set(x, 5, z1 - 4, ST("spruce", "south"))
    for x in (x1, 14, 18, x2):
        for y in range(2, 5):
            d.set(x, y, z1 - 3, LOG("spruce_log"))
    for x in range(x1 + 1, x2):
        if x not in (14, 18) and not 15 <= x <= 17:
            d.set(x, 2, z1 - 3, "spruce_fence")
    d.chair(12, 2, z1 - 1, "south", "spruce", sit=False)
    d.chair(20, 2, z1 - 1, "south", "spruce", sit=False)
    d.keg(13, 2, z1 - 1, "north")
    d.set(15, 4, z1 - 2, LANT)
    d.set(17, 4, z1 - 2, LANT)
    d.sign(16, 5, z1 - 1, "north", ["BARRACKS"], "spruce") if False else None
    # stone chimney on the east gable
    d.hearth(x2 - 1, 2, 17, "west", ridge + 2, "cobblestone", "campfire")
    for y in range(1, ridge + 2):
        d.set(x2 + 1, y, 17, rock(x2 + 1, y, 17))
        d.set(x2, y, 17, rock(x2, y, 17))
    # interior
    d.hut(12, 2, 14)
    weapon_rack(d, [(12, 16), (12, 17), (12, 18)], 2, "spruce")
    d.banner(12, 4, 17, "east", "green")
    d.item(12, 2, 20, "barrel")
    d.item(14, 2, 20, "barrel")
    d.item(13, 2, 20, "anvil", "east")
    if L >= 3:
        d.item(15, 2, 20, "smithing_table")
    d.set(12, 3, 20, "barrel[facing=up,open=false]") if False else None
    for x in range(15, 19):
        d.table(x, 2, 17, "spruce", "block", "stripped_spruce_wood[axis=x]")
        d.chair(x, 2, 16, "north", "spruce", sit=False)
    d.set(15, 3, 17, "candle[candles=2,lit=false,waterlogged=false]")
    carpet(d, 2, [(x, z) for x in range(19, 19 + 1) for z in range(16, 18 + 1)], "brown")
    d.chair(19, 2, 15, "north", "spruce", sit=False)
    d.set(20, 2, 14, "chest[facing=west,type=single,waterlogged=false]")
    for x in (13, 16, 19):
        d.lamp(x, 5, 17)
    # behind the hall: woodpile
    for x in range(12, 17):
        d.set(x, 2, 23, LOG("spruce_log", "x"))
        if x % 2:
            d.set(x, 3, 23, LOG("spruce_log", "x"))
    d.set(18, 2, 23, "chopping_block" if False else "spruce_log[axis=y]")
    # ---- parade ground ----------------------------------------------------------------------------
    nt = {1: 2, 2: 3, 3: 4, 4: 5, 5: 5}[L]
    for i in range(nt):
        butt(d, 6, 2, 10 + 2 * i)
    for x, z in ((26, 12), (26, 15)):
        dummy(d, x, 2, z, "west")
    d.set(25, 2, 18, "water_cauldron[level=3]")
    d.set(26, 2, 18, "hay_block[axis=x]")
    d.set(26, 2, 19, "hay_block[axis=y]") if L >= 2 else None
    for i in range(nt):
        d.set(11, 1, 10 + 2 * i, "stripped_spruce_log[axis=x]")
    if L >= 2:                                               # flag pole
        for y in range(2, 13):
            d.set(16, y, 8, LOG("stripped_spruce_log") if y < 3 else "spruce_fence")
        d.set(16, 1, 8, "cobblestone")
        for x, y in ((17, 12), (18, 12), (17, 11), (18, 11)):
            d.set(x, y, 8, "green_wool" if y == 12 else "white_wool")
        for x, z in ((15, 7), (17, 7), (15, 9), (17, 9)):
            d.set(x, 1, z, "cobblestone")
    if L >= 4:
        for x, z in ((8, 6), (24, 6), (8, 22), (24, 22)):
            d.set(x, 2, z, "spruce_fence")
            d.set(x, 3, z, LANT_S)
    if L >= 5:                                               # water well
        for x in range(23, 26):
            for z in range(8, 11):
                d.set(x, 2, z, rock(x, 2, z) if (x, z) != (24, 9) else "water[level=0]")
        for x, z in ((23, 8), (25, 8), (23, 10), (25, 10)):
            d.set(x, 3, z, "spruce_fence")
        d.fill(23, 4, 8, 25, 4, 10, SL("dark_oak"))
    # ---- blockhouses (child huts) -----------------------------------------------------------------
    for k in built:
        X0, Z0 = boxes[k]
        d.reserve(X0 + 1, 1, Z0 + 1, X0 + 7, 4, Z0 + 7)
        d.reserve(X0, 5, Z0, X0 + 8, CS_TSY, Z0 + 8)
        d.child_hut(X0 + CS_THUT[0], 2, Z0 + CS_THUT[2], TOWER)
    return d


def nt_bar(rel, L):
    d = Design("Neoterra", rel, (49, NT_TSY + 2, 33), gy=1, paving="smooth_stone")
    boxes = {"SW": (1, 25), "SE": (19, 25), "NW": (1, 1), "NE": (19, 1)}
    order = ["SW", "SE", "NW", "NE"]
    built = order[:min(L, 4)]
    full = L >= 3

    def in_box(x, z):
        for k in built:
            X0, Z0 = boxes[k]
            if 0 <= x - X0 < 7 and 0 <= z - Z0 < 7:
                return True
        return False
    # ground: parade ground with lane markings, lawn strips
    for x in range(2, 25):
        for z in range(2, 31):
            d.set(x, 1, z, "light_gray_concrete" if (x in (2, 24) or z in (2, 30)) else "smooth_stone")
    for z in range(2, 20):
        d.set(13, 1, z, "yellow_concrete" if z % 2 else "smooth_stone")
    # ---- perimeter fence --------------------------------------------------------------------------
    lines = [(1, z) for z in range(1, 32)] + [(25, z) for z in range(1, 32)] + \
            [(x, 1) for x in range(2, 25)] + [(x, 31) for x in range(2, 25)]
    for x, z in lines:
        if in_box(x, z) or (11 <= x <= 15 and z == 1):
            continue
        d.set(x, 2, z, "light_gray_concrete")
        post = (x + z) % 4 == 0 or (x in (1, 25) and z in (1, 31))
        if full:
            for y in (3, 4, 5):
                d.set(x, y, z, "white_concrete" if post else "iron_bars")
            if post:
                d.set(x, 6, z, ENDROD())
        else:
            d.set(x, 3, z, "white_concrete" if post else "light_gray_stained_glass_pane")
    # gate
    for x in (10, 16):
        for y in range(2, 7 if full else 4):
            d.set(x, y, 1, "gray_concrete" if y % 2 else "cyan_concrete")
        d.set(x, 7 if full else 4, 1, "sea_lantern")
    if full:
        for x in range(4, 10):                               # sliding steel gate, parked open behind the fence
            for y in (3, 4, 5):
                d.set(x, y, 2, "iron_bars")
            d.set(x, 2, 2, "polished_andesite")
        d.set(4, 2, 2, "gray_concrete")
        # guard booth
        for x in range(16, 19):
            for z in range(3, 6):
                edge = x in (16, 18) or z in (3, 5)
                for y in range(2, 5):
                    d.set(x, y, z, ("glass" if y > 2 else "white_concrete") if edge else AIR)
                d.set(x, 5, z, "smooth_quartz_slab[type=bottom,waterlogged=false]")
                d.set(x, 1, z, "polished_diorite")
        d.door(17, 2, 5, "north", "birch")
        d.set(17, 2, 3, "smooth_quartz_slab[type=top,waterlogged=false]")
        d.set(16, 2, 4, "birch_stairs[facing=east,half=bottom,shape=straight,waterlogged=false]") if False else None
        d.sign(11, 6, 0, "north", ["SECURITY", "COMPOUND", "AUTHORISED", "ONLY"], "birch", glow=True, color="cyan") \
            if False else None
    for x in range(11, 16):
        d.set(x, 1, 1, "yellow_concrete" if x % 2 else "black_concrete")
    # ---- HQ ---------------------------------------------------------------------------------------
    x1, z1, x2, z2 = 8, 20, 18, 30
    top = 11 if full else 6
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            edge = x in (x1, x2) or z in (z1, z2)
            d.set(x, 1, z, "polished_diorite")
            for y in range(2, top + 1):
                if y == 7:
                    d.set(x, y, z, "light_gray_concrete" if not edge else "cyan_terracotta")
                else:
                    d.set(x, y, z, ("light_gray_concrete" if x in (x1, x2) and z in (z1, z2) else "white_concrete")
                          if edge else AIR)
    d.flat(x1, z1, x2, z2, top + 1, "smooth_quartz", "white_concrete", "smooth_quartz_slab")
    for x in range(x1 + 1, x2):                               # glass street front
        d.window(x, 2, z1, x, 6, z1, "glass_pane")
        if full:
            d.window(x, 8, z1, x, 11, z1, "light_blue_stained_glass_pane")
    for z in range(z1 + 2, z2 - 1, 3):
        d.window(x1, 3, z, x1, 5, z, "light_gray_stained_glass_pane")
        d.window(x2, 3, z, x2, 5, z, "light_gray_stained_glass_pane")
        if full:
            d.window(x1, 9, z, x1, 10, z, "light_gray_stained_glass_pane")
            d.window(x2, 9, z, x2, 10, z, "light_gray_stained_glass_pane")
    d.double_door(13, 2, z1, "x", "south", "birch")
    for x in range(11, 17):                                   # entrance canopy
        for z in (z1 - 1, z1 - 2):
            d.set(x, 6, z, "smooth_quartz_slab[type=top,waterlogged=false]")
    d.sign(13, 7, z1 - 1, "north", ["GARRISON"], "birch", glow=True, color="cyan")
    d.sign(14, 7, z1 - 1, "north", ["HQ"], "birch", glow=True, color="cyan")
    # interior: armoury (back west), briefing (east), lobby
    d.hut(9, 2, 21)
    d.item(9, 2, 29, "barrel")
    d.item(10, 2, 29, "barrel")
    d.item(11, 2, 29, "anvil", "east")
    if L >= 3:
        d.item(12, 2, 29, "smithing_table")
    for z in range(25, 29):
        d.set(9, 2, z, "smooth_quartz_slab[type=top,waterlogged=false]")
        d.set(9, 3, z, ROD())
    for x in range(9, 14):                                    # glass partition of the armoury
        if x != 11:
            d.set(x, 2, 24, "light_gray_concrete")
            d.set(x, 3, 24, "light_gray_stained_glass_pane")
            d.set(x, 4, 24, "light_gray_stained_glass_pane")
    d.set(13, 2, 25, "light_gray_concrete")
    for z in range(25, 30):
        if z != 27:
            d.set(13, 2, z, "light_gray_concrete")
            d.set(13, 3, z, "light_gray_stained_glass_pane")
    # briefing table
    for z in (25, 26, 27):
        d.table(15, 2, z, "birch", "block", "smooth_quartz")
        d.chair(14, 2, z, "west", "birch", sit=False) if z != 27 else None
        d.chair(16, 2, z, "east", "birch", sit=False)
    for z in range(24, 29):
        d.set(17, 3, z, "black_stained_glass")
    d.set(17, 4, 26, "cyan_stained_glass")
    d.plant(17, 2, 21, "potted_bamboo")
    d.set(16, 2, 21, "smooth_quartz_slab[type=top,waterlogged=false]")
    for x in (10, 13, 16):
        for z in (22, 27):
            d.set(x, 6, z, "sea_lantern")
    if full:                                                  # upper floor: ops room, stair along the east wall
        for i in range(5):
            d.set(17, 2 + i, 21 + i, "smooth_quartz_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]")
            for y in range(2 + i + 1, 2 + i + 4):
                if y <= 7:
                    d.set(17, y, 21 + i, AIR)
        d.set(16, 2, 21, AIR)
        d.set(17, 2, 21, "smooth_quartz_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]")
        d.set(17, 7, 26, AIR)
        for z in range(21, 27):
            d.set(16, 8, z, "light_gray_stained_glass_pane") if z < 26 else None
        for x in (9, 12, 15):
            d.set(x, 8, 22, "smooth_quartz_slab[type=top,waterlogged=false]")
            d.chair(x, 8, 23, "south", "birch", sit=False)
            d.set(x, 9, 22, "black_stained_glass_pane")
        d.set(12, 8, 28, "smooth_quartz")
        d.set(12, 9, 28, "lectern[facing=north,has_book=false,powered=false]") if False else None
        for x in (10, 13, 16):
            d.set(x, 11, 26, "sea_lantern")
        carpet(d, 8, [(x, z) for x in range(9, 15 + 1) for z in range(25, 29 + 1)], "light_gray")
    if L >= 4:                                                # solar panels on the roof
        for x in range(x1 + 2, x2 - 1):
            for z in (z1 + 2, z1 + 3):
                d.set(x, top + 2, z, "daylight_detector[inverted=false,power=0]")
    if L >= 5:                                                # helipad
        for x in range(x1 + 2, x2 - 1):
            for z in range(z1 + 5, z2 - 1):
                d.set(x, top + 1, z, "yellow_concrete" if (x == 11 or x == 15 or (z == 27 and 11 <= x <= 15))
                      else "gray_concrete")
        for x, z in ((x1 + 2, z1 + 5), (x2 - 2, z1 + 5), (x1 + 2, z2 - 2), (x2 - 2, z2 - 2)):
            d.set(x, top + 2, z, "redstone_lamp[lit=true]") if False else d.set(x, top + 2, z, ENDROD())
    # ---- shooting range (east) and parade ground ---------------------------------------------------
    nt = {1: 2, 2: 3, 3: 4, 4: 5, 5: 5}[L]
    for z in range(9, 19):
        for y in (2, 3, 4):
            d.set(24, y, z, "gray_concrete")
    for i in range(nt):
        z = 10 + 2 * i
        d.set(23, 2, z, "polished_andesite")
        d.yard_item(23, 3, z, "target")
    for z in (9, 11, 13, 15, 17, 19):                                 # firing booths
        d.set(17, 2, z, "white_concrete")
        d.set(17, 3, z, "light_gray_stained_glass_pane")
    for z in range(9, 19):
        d.set(20, 1, z, "yellow_concrete") if z % 2 else None
    for x in (4, 6):                                          # planters
        for z in range(10, 18):
            d.set(x, 1, z, "grass_block[snowy=false]")
        for z in (12, 15):
            d.set(x, 2, z, "azalea")
    if L >= 2:                                                # three flag masts at the gate
        for i, x in enumerate((5, 7, 9)):
            for y in range(2, 10):
                d.set(x, y, 7, "iron_bars")
            d.set(x, 1, 7, "polished_andesite")
            d.set(x, 9, 6, ("cyan_wool", "white_wool", "light_blue_wool")[i])
            d.set(x, 8, 6, ("cyan_wool", "white_wool", "light_blue_wool")[i])
    for x, z in ((3, 19), (23, 19), (3, 3), (23, 3)):
        d.set(x, 2, z, "andesite_wall") if not in_box(x, z) else None
        d.set(x, 3, z, ENDROD()) if not in_box(x, z) else None
    # ---- dorm towers (child huts) -----------------------------------------------------------------
    for k in built:
        X0, Z0 = boxes[k]
        d.reserve(X0, 1, Z0, X0 + 6, NT_TSY, Z0 + 6)
        d.child_hut(X0 + NT_THUT[0], 2, Z0 + NT_THUT[2], TOWER)
    return d

# ---- barracks growth beyond the walls (type-specific add-ons) ---------------------------------------------
PAL_BAR = {
    "hw_stable": dict(w0="bricks", plinth="stone_bricks", plinth2="mossy_stone_bricks", quoin="stone_bricks",
                      quoin2="bricks", w1="white_terracotta", frame="stripped_oak_log", band="oak_log",
                      roof="mud_brick", gable="white_terracotta", beam="oak_log", shut="mangrove", door="oak"),
    "hw_smithy": dict(w0="stone_bricks", w1="mud_bricks", frame="stripped_spruce_log", band="spruce_log",
                      roof="brick", gable="mud_bricks", shut="spruce", door="spruce", floor="polished_andesite"),
    "cs_barn": dict(w0="mangrove_planks", w1="mangrove_planks", corner="stripped_spruce_log", band="stripped_birch_log",
                    roof="cobbled_deepslate", ridge="cobbled_deepslate_slab", gable="mangrove_planks", shut="birch",
                    door="spruce", beam="stripped_birch_log"),
    "cs_store": dict(w0="birch_planks", w1="birch_planks", corner="spruce_log", band="yellow_terracotta",
                     roof="mangrove", ridge="mangrove_slab", gable="birch_planks", shut="dark_oak", door="dark_oak",
                     awning="yellow_wool"),
    "cs_officer": dict(w0="spruce_planks", w1="spruce_planks", corner="dark_oak_log", band="white_terracotta",
                       roof="deepslate_tile", ridge="deepslate_tile_slab", gable="spruce_planks", shut="mangrove",
                       door="mangrove", beam="dark_oak_log"),
    "cs_smithy": dict(w0="cobblestone", corner="dark_oak_log", band="dark_oak_log", roof="dark_prismarine",
                      ridge="dark_prismarine_slab", gable="dark_oak_planks", door="dark_oak", chimney="rock"),
    "nt_garage": dict(w0="polished_blackstone_bricks", corner="polished_blackstone", band="orange_concrete",
                      fin="orange_terracotta", parapet="polished_blackstone", coping="polished_blackstone_slab",
                      roofdeck="gray_concrete", glass="gray_stained_glass_pane", green=True),
    "nt_gym": dict(w0="light_gray_concrete", w1="white_terracotta", corner="quartz_pillar", band="lime_concrete",
                   fin="lime_terracotta", parapet="cut_copper", coping="cut_copper_slab",
                   glass2="light_blue_stained_glass_pane"),
}


def hw_bar_outer(d, L):
    """Outer ward in front of the castle (z < 0): L4 stables with hayloft, L5 smithy with armourer's loft, an outer
    curtain wall with a barbican gate, well and garden."""
    if L < 4:
        return
    for z in range(-19, 3):
        for x in range(15, 18):
            d.set(x, 1, z, "cobblestone" if (x + z) % 3 else "gravel")
        d.set(14, 1, z, "stone_bricks")
        d.set(18, 1, z, "stone_bricks")
    ys, top, ridge = bld(d, 2, -16, 12, -8, 2, "x", doors=[(12, -12)], lad=(3, -15, "east"),
                         pal=PAL_BAR["hw_stable"], chimney=None)
    w = "oak"                                                 # stalls on the north wall, tack on the south wall
    lay(d, ys[0], [(5, -15, "hay_block[axis=y]"), (6, -15, "water_cauldron[level=3]"), (7, -15, "oak_fence"),
                   (7, -14, "oak_fence"), (8, -15, "hay_block[axis=y]"), (9, -15, "water_cauldron[level=3]"),
                   (10, -15, "oak_fence"), (10, -14, "oak_fence"), (4, -9, BAR), (5, -9, CH("north")),
                   (6, -9, "hay_block[axis=y]"), (7, -9, "hay_block[axis=x]", "hay_block[axis=y]"),
                   (9, -9, SLD(w), POTD), (10, -9, "water_cauldron[level=3]"), (6, -12, "yellow_carpet"),
                   (8, -13, "yellow_carpet"), ("lamp", 6, -12), ("lamp", 9, -12)])
    lay(d, ys[1], [(6, -15, "hay_block[axis=y]", "hay_block[axis=y]"), (7, -15, "hay_block[axis=y]", "hay_block[axis=y]"),
                   (8, -15, "hay_block[axis=x]"), (9, -15, "hay_block[axis=y]", "hay_block[axis=y]"),
                   (10, -15, "hay_block[axis=x]"), (4, -9, "white_wool", "white_wool"), (5, -9, "brown_wool"),
                   (6, -9, "white_wool"), (9, -9, BAR), (10, -9, BAR, BAR), (11, -9, CH("west")), ("lamp", 7, -12)])
    # paddock with troughs and hay
    for x in range(2, 13):
        put(d, x, 2, -6, "oak_fence")
        put(d, x, 2, -2, "oak_fence")
    for z in range(-6, -1):
        put(d, 2, 2, z, "oak_fence")
    put(d, 12, 2, -4, "oak_fence_gate[facing=east,in_wall=false,open=false,powered=false]")
    put(d, 12, 2, -6, "oak_fence")
    put(d, 12, 2, -5, "oak_fence")
    put(d, 12, 2, -3, "oak_fence")
    put(d, 12, 2, -2, "oak_fence")
    for x, b in ((4, "water_cauldron[level=3]"), (5, "hay_block[axis=x]"), (9, "hay_block[axis=y]")):
        put(d, x, 2, -5, b)
    lamp_post(d, 13, -7)
    lamp_post(d, 19, -7)
    bench(d, 13, -3, "west", along="z")
    if L >= 5:
        ys, top, ridge = bld(d, 20, -16, 30, -8, 2, "x", doors=[(20, -12)], lad=(29, -15, "west"),
                             pal=PAL_BAR["hw_smithy"], chimney=(27, -16))
        w = "spruce"                                          # forge under the chimney, anvil and quench in front
        lay(d, ys[0], [(25, -15, "furnace[facing=south,lit=true]"), (26, -15, "blast_furnace[facing=south,lit=true]"),
                       (27, -15, FIRE("south")), (26, -13, "anvil[facing=east]"), (25, -13, "water_cauldron[level=3]"),
                       (23, -15, "grindstone[face=floor,facing=east]"), (22, -15, SLD(w), ROD()), (24, -15, SLD(w), CHAIN),
                       (24, -11, "crafting_table"), (23, -9, "smithing_table"), (25, -9, CH("north")), (26, -9, CH("north")),
                       (27, -9, BAR), (28, -9, "black_wool"), (29, -9, "coal_block"), ("lamp", 24, -12), ("lamp", 27, -12)])
        lay(d, ys[1], [(22, -15, SLD(w), ROD()), (23, -15, SLD(w), ROD()), (24, -15, SLD(w), ROD()),
                       (26, -15, CH("south")), (22, -9, CH("north")), (24, -9, CH("north")),
                       (27, -9, "grindstone[face=floor,facing=east]"), (25, -11, "oak_fence"), ("lamp", 25, -12)])
        put(d, 25, ys[1] + 1, -11, "hay_block[axis=y]")
        put(d, 25, ys[1] + 2, -11, "carved_pumpkin[facing=west]")
        for x in (22, 24):
            put(d, x, ys[1] + 2, -15, "red_wall_banner[facing=south]")
        # well
        for x in range(23, 26):
            for z in range(-5, -2):
                d.set(x, 2, z, "cobblestone" if (x, z) != (24, -4) else "water[level=0]")
        for x, z in ((23, -5), (25, -5), (23, -3), (25, -3)):
            d.set(x, 3, z, "oak_fence")
            d.set(x, 4, z, "oak_fence")
        d.fill(23, 5, -5, 25, 5, -3, "mud_brick_slab[type=bottom,waterlogged=false]")
        d.set(24, 4, -4, CHAIN)
        flowers(d, [(x, z) for x in range(20, 22 + 1) for z in range(-6, -6 + 1)])
        flowers(d, [(x, z) for x in range(27, 30 + 1) for z in range(-6, -6 + 1)])
        # outer curtain wall with crenels and a barbican
        for x in range(0, 33):
            if 14 <= x <= 18:
                continue
            for y in range(2, 6):
                d.set(x, y, -18, stone_mix(x, y, -18))
            if x % 2 == 0:
                d.set(x, 6, -18, stone_mix(x, 6, -18))
        for z in range(-17, 0):
            for x in (0, 32):
                for y in range(2, 6):
                    d.set(x, y, z, stone_mix(x, y, z))
                if z % 2 == 0:
                    d.set(x, 6, z, stone_mix(x, 6, z))
        for x in range(1, 32):                                  # inner face + walk of the outer wall
            if 14 <= x <= 18:
                continue
            for y in range(2, 6):
                d.set(x, y, -17, stone_mix(x, y, -17))
        for z in range(-16, 0):
            for x in (1, 31):
                for y in range(2, 6):
                    d.set(x, y, z, stone_mix(x, y, z))
        for tx in (12, 18):                                    # barbican turrets
            for x in range(tx, tx + 3):
                for z in range(-19, -15):
                    edge = x in (tx, tx + 2) or z in (-19, -16)
                    for y in range(2, 10):
                        d.set(x, y, z, stone_mix(x, y, z) if edge else (stone_mix(x, y, z) if y == 8 else AIR))
                    if edge and (x + z) % 2 == 0:
                        d.set(x, 10, z, stone_mix(x, 10, z))
            d.set(tx + 1, 5, -19, "glass_pane")
            for x in range(tx, tx + 3):                        # timber hoarding on top
                for z in range(-19, -15):
                    if x in (tx, tx + 2) or z in (-19, -16):
                        d.set(x, 10, z, "dark_oak_planks" if (x + z) % 2 else "stripped_dark_oak_log[axis=y]")
                        d.set(x, 11, z, "dark_oak_fence")
                d.set(x, 12, -19, ST("deepslate_tile", "south"))
                d.set(x, 12, -16, ST("deepslate_tile", "north"))
                d.set(x, 12, -18, "deepslate_tile_slab[type=top,waterlogged=false]")
                d.set(x, 13, -17, "deepslate_tile_slab[type=bottom,waterlogged=false]")
                d.set(x, 13, -18, "deepslate_tile_slab[type=bottom,waterlogged=false]")
                d.set(x, 12, -17, "deepslate_tile_slab[type=top,waterlogged=false]")
            d.banner(tx + 1, 7, -20 + 0, "north", "red") if d.bp.inside(tx + 1, 7, -20) else None
        for x in range(15, 18):
            for z in range(-19, -15):
                d.set(x, 7, z, stone_mix(x, 7, z))
                d.set(x, 8, z, stone_mix(x, 8, z) if z in (-19, -16) else AIR)
            d.set(x, 6, -19, ST("stone_brick", "north", "top"))
            gate = "dark_oak_fence_gate[facing=north,in_wall=false,open=true,powered=false]"
        for x in (15, 17):
            d.set(x, 6, -18, ST("stone_brick", "west" if x == 15 else "east", "top"))
        d.set(14, 4, -20 + 1, "wall_torch[facing=north]") if d.air(14, 4, -19) else None


def sentry_box(d, x, z, door="south", roof="spruce"):
    """3x3 log sentry box / outhouse with a slab roof and a lantern (Cascadia)."""
    for a in range(x, x + 3):
        for b in range(z, z + 3):
            edge = a in (x, x + 2) or b in (z, z + 2)
            for y in range(2, 5):
                d.set(a, y, b, (LOG("spruce_log") if a in (x, x + 2) and b in (z, z + 2) else
                                LOG("stripped_spruce_log", "x" if b in (z, z + 2) else "z")) if edge else AIR)
            d.set(a, 5, b, SL(roof))
    dx, dz = {"south": (1, 2), "north": (1, 0), "east": (2, 1), "west": (0, 1)}[door]
    d.door(x + dx, 2, z + dz, OPP[door], "spruce")
    d.set(x + 1, 4, z + 1, LANT)
    put(d, x + 1, 6, z + 1, "spruce_fence")
    put(d, x + 1, 7, z + 1, LANT_S)


def stall(d, x, z, color, goods=("hay_block[axis=y]", "barrel[facing=up,open=false]", "pumpkin")):
    """Market stall: counter of slabs with goods, fence posts, striped wool awning."""
    w = WOOD[d.pack]
    for i in range(3):
        put(d, x + i, 2, z, SL(w, "top"))
        put(d, x + i, 3, z, goods[i % len(goods)])
        put(d, x + i, 5, z, f"{color}_wool" if i % 2 == 0 else "white_wool")
        put(d, x + i, 5, z + 1, f"{color}_wool" if i % 2 == 0 else "white_wool")
    for a in (x - 1, x + 3):
        for y in (2, 3, 4):
            put(d, a, y, z, f"{w}_fence")
        put(d, a, 5, z, f"{w}_planks")


def cs_bar_outer(d, L):
    """Outside the stockade gate (z < 0): L2 well, garden and hitching rail; L4 red cedar horse barn with a corral;
    L5 sutler's store with porch and a blacksmith shed."""
    if L >= 2:
        for z in range(-27, 4):
            for x in range(15, 18):
                d.set(x, 1, z, "dirt_path")
        for x in range(24, 30):                                 # woodshed: log stack under a slab roof
            for z in (-1, 0):
                put(d, x, 2, z, LOG("spruce_log", "x"))
                put(d, x, 3, z, LOG("spruce_log", "x"))
            for z in (-2, -1, 0):
                d.set(x, 5, z, SL("spruce"))
            if x in (24, 29):
                for y in (2, 3, 4):
                    d.set(x, y, -2, LOG("spruce_log"))
            d.set(x, 4, 0, LOG("spruce_log", "x"))
        for x in range(9, 14):
            put(d, x, 2, -1, "spruce_fence")
        put(d, 9, 3, -1, LANT_S)
        put(d, 13, 3, -1, LANT_S)
        put(d, 11, 2, 0, "water_cauldron[level=3]")
        for x in range(19, 24):                                 # well
            pass
        for x in range(20, 23):
            for z in range(-3, 0):
                d.set(x, 2, z, rock(x, 2, z) if (x, z) != (21, -2) else "water[level=0]")
        for x, z in ((20, -3), (22, -3), (20, -1), (22, -1)):
            d.set(x, 3, z, "spruce_fence")
            d.set(x, 4, z, "spruce_fence")
        d.fill(20, 5, -3, 22, 5, -1, SL("spruce"))
        flowers(d, [(x, z) for x in range(25, 29 + 1) for z in range(-5, -5 + 1)])
        cart(d, 9, -3, "x")
        sentry_box(d, 18, -4, "west")                          # sentry box by the gate road
        for z, c in ((8, "green"), (12, "yellow")):              # sutlers' stalls along the stockade
            stall(d, -9, z, c, ("pumpkin", "barrel[facing=up,open=false]", "melon"))
        lamp_post(d, -6, 10)
        lamp_post(d, -6, 15)
        stall(d, 25, -10, "red") if L < 5 else None
        for x in range(25, 31):                                 # fenced vegetable patch
            for z in (-15, -12):
                put(d, x, 2, z, "spruce_fence") if L < 4 or True else None
        for z in (-14, -13):
            put(d, 25, 2, z, "spruce_fence")
            put(d, 30, 2, z, "spruce_fence")
            for x in range(26, 30):
                d.set(x, 1, z, "farmland[moisture=7]")
                put(d, x, 2, z, ("carrots[age=7]", "potatoes[age=7]", "wheat[age=7]", "beetroots[age=3]")[x % 4])
    if L >= 4:
        ys, top, ridge = bld(d, 1, -16, 12, -7, 2, "z", doors=[(12, -11)], lad=(2, -15, "east"),
                             pal=PAL_BAR["cs_barn"])
        w = "spruce"                                          # horse barn: stalls north, feed and tack south
        lay(d, ys[0], [(4, -15, "hay_block[axis=y]"), (5, -15, "water_cauldron[level=3]"), (6, -15, "spruce_fence"),
                       (6, -14, "spruce_fence"), (7, -15, "hay_block[axis=y]"), (8, -15, "water_cauldron[level=3]"),
                       (9, -15, "spruce_fence"), (9, -14, "spruce_fence"), (10, -15, "hay_block[axis=y]"),
                       (3, -8, BAR), (4, -8, "hay_block[axis=x]"), (5, -8, "hay_block[axis=x]"), (6, -8, CH("north")),
                       (7, -8, SLD(w), POTD), (8, -8, "composter[level=3]"), (9, -8, "water_cauldron[level=3]"),
                       (5, -12, "yellow_carpet"), (8, -12, "yellow_carpet"), ("lamp", 5, -11), ("lamp", 9, -11)])
        lay(d, ys[1], [(5, -15, "hay_block[axis=y]", "hay_block[axis=y]"), (6, -15, "hay_block[axis=y]", "hay_block[axis=y]"),
                       (7, -15, "hay_block[axis=x]"), (8, -15, "hay_block[axis=y]", "hay_block[axis=y]"),
                       (9, -15, "hay_block[axis=x]"), (3, -8, "white_wool"), (4, -8, "brown_wool", "white_wool"),
                       (9, -8, BAR), (10, -8, BAR, BAR), (11, -8, CH("north")), (8, -11, "composter[level=6]"),
                       ("lamp", 6, -11)])
        for x in range(1, 13):                                  # corral
            put(d, x, 2, -5, "spruce_fence")
        put(d, 1, 2, -6, "spruce_fence")
        for x, b in ((4, "hay_block[axis=y]"), (7, "water_cauldron[level=3]")):
            put(d, x, 2, -6, b)
        lamp_post(d, 14, -8)
        lamp_post(d, 18, -8)
        ys, top, ridge = bld(d, 1, -4, 7, 0, 1, "x", doors=[(7, -2)], sh=5, pal=PAL_BAR["cs_smithy"],
                             chimney=(1, -2))
        lay(d, ys[0], [(2, -2, FIRE("east")), (2, -3, "blast_furnace[facing=east,lit=true]"),
                       (2, -1, "furnace[facing=east,lit=true]"), (4, -3, "anvil[facing=east]"),
                       (3, -1, "water_cauldron[level=3]"), (4, -1, SL("spruce", "top"), ROD()), (5, -1, CH("north")),
                       ("lamp", 4, -2)])
        # trestle lookout tower west of the barn
        tx, tz = -10, -25
        for a, b in ((tx, tz), (tx + 4, tz), (tx, tz + 4), (tx + 4, tz + 4)):
            for y in range(2, 16):
                d.set(a, y, b, LOG("spruce_log"))
        for y in (6, 10):
            for a in range(tx + 1, tx + 4):
                for b in (tz, tz + 4):
                    d.set(a, y, b, "spruce_fence")
            for b in range(tz + 1, tz + 4):
                for a in (tx, tx + 4):
                    d.set(a, y, b, "spruce_fence")
        for y in range(2, 12):
            d.set(tx + 2, y, tz + 2, LOG("stripped_spruce_log"))
        d.fill(tx, 12, tz, tx + 4, 12, tz + 4, "spruce_planks")
        for a in range(tx, tx + 5):
            for b in range(tz, tz + 5):
                if a in (tx, tx + 4) or b in (tz, tz + 4):
                    if not (a in (tx, tx + 4) and b in (tz, tz + 4)):
                        d.set(a, 13, b, "stripped_spruce_log[axis=y]" if (a + b) % 2 else "spruce_fence")
                        d.set(a, 14, b, "glass_pane" if (a + b) % 2 == 0 else AIR)
        ladder(d, tx + 2, tz + 3, 2, 12, "south")
        d.fill(tx - 1, 16, tz - 1, tx + 5, 16, tz + 5, SL("cobbled_deepslate"))
        d.fill(tx, 17, tz, tx + 4, 17, tz + 4, SL("cobbled_deepslate"))
        d.set(tx + 2, 18, tz + 2, LANT_S)
        d.set(tx + 2, 15, tz + 2, LANT)
        d.set(tx + 1, 13, tz + 1, "bell[attachment=floor,facing=north,powered=false]")
        cart(d, -9, 18, "x")
        for x in range(-11, -6):                                # log deck for the sawyer
            put(d, x, 2, 22, LOG("spruce_log", "x"))
            put(d, x, 3, 22, LOG("spruce_log", "x")) if x % 2 else None
            put(d, x, 2, 23, LOG("spruce_log", "x"))
        put(d, -5, 2, 22, "stonecutter[facing=north]")
        for x in range(-11, -6):
            put(d, x, 3, 23, LOG("spruce_log", "x"))
            put(d, x, 2, 24, LOG("spruce_log", "x"))
            put(d, x, 3, 24, LOG("spruce_log", "x"))
            put(d, x, 4, 23, LOG("spruce_log", "x")) if x % 2 == 0 else None
        lamp_post(d, -5, 20)
        for z in (26, 27):
            put(d, -10, 2, z, "barrel[facing=up,open=false]")
            put(d, -9, 2, z, "hay_block[axis=y]")
        # lean-to cart shed on the barn's south gable and a hay wagon
        for z in range(-16, -6):
            d.set(0, 5, z, SL("cobbled_deepslate"))
        for z in (-16, -12, -7):
            for y in (2, 3, 4):
                d.set(0, y, z, LOG("spruce_log"))
        cart(d, 19, -10, "z")
        for x in (1, 6, 12):
            lamp_post(d, x, -4) if x != 6 else None
        for z in range(-6, -4):
            put(d, 13, 2, z, "spruce_fence")
        for x in (19, 20):                                       # hay stack by the barn
            for z in (-14, -13):
                for y in (2, 3):
                    put(d, x, y, z, "hay_block[axis=y]")
        put(d, 13, 2, -13, "barrel[facing=up,open=false]")
        put(d, 13, 2, -9, "barrel[facing=up,open=false]")
        put(d, 13, 3, -9, "barrel[facing=north,open=false]")
        put(d, 13, 2, -10, "hay_block[axis=x]")
        put(d, 13, 2, -14, "hay_block[axis=x]")
        put(d, 13, 3, -13, "decorated_pot[cracked=false,facing=east,waterlogged=false]")
        for x in range(1, 13):                                  # second corral rail
            put(d, x, 3, -5, "spruce_fence")
        for x in range(19, 22):
            put(d, x, 2, -16, "hay_block[axis=x]")
            put(d, x, 3, -16, "hay_block[axis=y]") if x != 21 else None
    if L >= 5:
        ys, top, ridge = bld(d, 20, -16, 31, -8, 2, "x", doors=[(25, -8)], lad=(30, -15, "west"),
                             pal=PAL_BAR["cs_store"])
        w = "spruce"                                          # shop: counter across, goods behind, produce in front
        lay(d, ys[0], [(22, -11, SLD(w), POTD), (23, -11, SLD(w)), (24, -11, SLD(w), CAN3),
                       (26, -11, SLD(w), "flower_pot"), (27, -11, SLD(w)), (28, -11, SLD(w), POTD),
                       (26, -12, "lectern[facing=south,has_book=false,powered=false]"),
                       (22, -15, BAR, BAR), (23, -15, BAR, BAR), (24, -15, "white_wool", "brown_wool"),
                       (25, -15, BAR, BAR), (26, -15, CH("south")), (27, -15, "brown_wool", "white_wool"),
                       (21, -9, "pumpkin"), (22, -9, "melon"), (23, -9, BAR), (28, -9, "hay_block[axis=y]"),
                       (29, -9, "white_wool"), ("lamp", 23, -12), ("lamp", 27, -12)])
        lay(d, ys[1], [("bed", 22, -15, "north", "yellow"), (23, -15, SLD(w), CAN1), (24, -15, BOOK("south")),
                       (26, -12, "spruce_fence", "spruce_pressure_plate[powered=false]"), (25, -12, ST(w, "west")),
                       (27, -12, ST(w, "east")), (28, -9, CH("north")), (22, -9, "potted_fern"),
                       (23, -10, "yellow_carpet"), (24, -10, "yellow_carpet"), ("lamp", 26, -12)])
        for x in range(20, 32):                                 # porch
            d.set(x, 5, -7, SL("spruce"))
            d.set(x, 5, -6, SL("spruce"))
            if x in (20, 23, 28, 31):
                for y in (2, 3, 4):
                    d.set(x, y, -6, LOG("spruce_log"))
        d.sign(25, 5, -5, "north", ["SUTLER", "GENERAL", "STORE"], "spruce") if False else None
        bench(d, 21, -7, "south")
        bench(d, 29, -7, "south")
        d.sign(24, 4, -7, "north", ["SUTLER &", "GENERAL", "STORE"], "spruce")
        ys, top, ridge = bld(d, -11, -12, -2, -4, 2, "z", doors=[(-2, -8)], lad=(-10, -11, "east"),
                             pal=PAL_BAR["cs_officer"], chimney=(-6, -12))
        w = "spruce"                                          # commanding officer's office around the fire
        lay(d, ys[0], [(-6, -11, FIRE("south")), (-7, -11, "cobblestone"), (-5, -11, "cobblestone"),
                       (-6, -9, ST(w, "south")), (-6, -7, SLD(w), CAN3), (-5, -7, SLD(w), "flower_pot"),
                       (-6, -6, ST(w, "south")), (-10, -8, BOOK("east")), (-10, -7, BOOK("east")), (-10, -6, BOOK("east")),
                       (-4, -5, "lectern[facing=north,has_book=false,powered=false]"), (-8, -5, "cartography_table"),
                       (-9, -5, "potted_fern"), (-5, -9, "red_carpet"), (-7, -9, "red_carpet"), ("lamp", -6, -8)])
        lay(d, ys[1], [("bed", -8, -5, "south", "red"), (-9, -5, SLD(w), CAN1), (-4, -5, BOOK("north")),
                       (-5, -5, CH("north")), (-4, -10, SLD(w), "flower_pot"), (-5, -10, ST(w, "east")),
                       (-7, -8, "red_carpet"), (-6, -8, "red_carpet"), ("lamp", -6, -8)])
        for z in range(-12, -3):                                # porch on the road side
            d.set(-1, 6, z, SL("deepslate_tile"))
            d.set(0, 6, z, SL("deepslate_tile"))
        for z in (-12, -8 + 3, -4):
            for y in range(2, 6):
                d.set(0, y, z, LOG("spruce_log"))
        bench(d, -1, -11, "west", along="z")
        flowers(d, [(x, z) for x in range(-11, -3 + 1) for z in range(-2, -2 + 1)])
        tree(d, -8, -16, 5)
        tree(d, -4, 3, 5)
        # log chapel with a steeple north of the store
        ys, top, ridge = bld(d, 21, -26, 29, -18, 1, "z", doors=[(25, -18)], sh=6,
                             pal=dict(w0="birch_planks", corner="stripped_spruce_log", band="spruce_log",
                                      roof="dark_oak", ridge="dark_oak_slab", gable="birch_planks", door="spruce",
                                      shut="spruce", beam="spruce_log"))
        for z in range(-24, -19, 2):                            # pews
            for x in (22, 23, 27, 28):
                d.chair(x, 2, z, "south", "spruce", sit=False)
        d.set(25, 2, -25, "lectern[facing=south,has_book=false,powered=false]")
        for x in (23, 27):
            d.set(x, 2, -25, SL("spruce", "top"))
            d.candle(x, 3, -25, 3)
        carpet(d, 2, [(x, z) for x in range(25, 25 + 1) for z in range(-24, -19 + 1)], "red")
        for z in (-23, -20):
            d.set(22, 5, z, LANT)
            d.set(28, 5, z, LANT)
        for x in range(24, 27):                                 # steeple over the entrance gable
            for z in range(-19, -16):
                for y in range(ridge - 2, ridge + 4):
                    edge = x in (24, 26) or z in (-19, -17)
                    if edge:
                        d.set(x, y, z, "birch_planks" if y < ridge + 3 else "spruce_fence")
                    elif y == ridge - 2:
                        d.set(x, y, z, "spruce_planks")
        d.set(25, ridge + 2, -18, "bell[attachment=ceiling,facing=north,powered=false]")
        d.set(25, ridge + 3, -18, "spruce_planks")
        for k in range(3):
            d.fill(24 + k * 0, ridge + 4 + k, -19 + k * 0, 26, ridge + 4 + k, -17, "dark_oak_slab[type=bottom,waterlogged=false]") \
                if k == 0 else None
        d.set(25, ridge + 5, -18, "dark_oak_fence")
        d.set(25, ridge + 6, -18, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        flowers(d, [(x, z) for x in range(19, 20 + 1) for z in range(-25, -19 + 1)])
        lamp_post(d, 19, -18)
        bench(d, 20, -14 + 0, "west", along="z") if False else None


def nt_bar_east(d, L):
    """Compound extension east of the dorm towers: L4 motor pool (garage + vehicle bays), L5 training centre with a
    gym, classrooms and a roof sports deck."""
    if L < 4:
        return
    for x in range(27, 49):
        for z in range(1, 32):
            d.set(x, 1, z, "gray_concrete" if (x + z) % 7 else "light_gray_concrete")
    for x in range(26, 49):                                  # perimeter of the extension
        for z in (1, 31):
            d.set(x, 2, z, "light_gray_concrete")
            d.set(x, 3, z, "iron_bars" if x % 4 else "white_concrete")
            d.set(x, 4, z, "iron_bars" if x % 4 else ENDROD())
    for z in range(1, 32):
        d.set(48, 2, z, "light_gray_concrete")
        d.set(48, 3, z, "iron_bars" if z % 4 else "white_concrete")
        d.set(48, 4, z, "iron_bars" if z % 4 else ENDROD())
    for z in range(10, 14):                                  # opening in the old east fence
        for y in range(2, 7):
            d.set(25, y, z, AIR)
        d.set(25, 1, z, "yellow_concrete" if z % 2 else "black_concrete")
    ys, top, ridge = bld(d, 29, 3, 46, 9, 1, "x", doors=[(37, 9), (38, 9)], sh=6, pal=PAL_BAR["nt_garage"])
    lay(d, ys[0], [(31, 4, "crafting_table"), (32, 4, SST, CHAIN), (33, 4, "grindstone[face=floor,facing=east]"),
                   (34, 4, "anvil[facing=east]"), (35, 4, LOCK), (30, 6, LOCK), (30, 7, LOCK),
                   (41, 5, "gray_concrete"), (42, 5, "gray_concrete"), (41, 6, "gray_concrete", "black_stained_glass"),
                   (42, 6, "gray_concrete", "black_stained_glass"), (41, 7, "gray_concrete"), (42, 7, "gray_concrete"),
                   (44, 4, "black_wool", "black_wool"), (45, 4, "black_wool"), (45, 6, BAR), (45, 7, BAR, BAR),
                   ("lamp", 33, 6, 4), ("lamp", 41, 4, 4)])
    for x in (30, 34, 38, 42):                               # vehicle bays in front
        for z in range(11, 17):
            if x in (30, 34, 38, 42):
                d.set(x, 1, z, "yellow_concrete")
    for x in (32, 40):                                       # parked vehicles (low armoured trucks)
        for z in range(12, 16):
            d.set(x, 2, z, "gray_concrete" if z < 15 else "black_concrete")
            d.set(x + 1, 2, z, "gray_concrete" if z < 15 else "black_concrete")
        d.set(x, 3, 12, "black_stained_glass")
        d.set(x + 1, 3, 12, "black_stained_glass")
        d.set(x, 3, 13, "gray_concrete")
        d.set(x + 1, 3, 13, "gray_concrete")
    lamp_post(d, 28, 11)
    lamp_post(d, 47, 11)
    if L >= 5:
        ys, top, ridge = bld(d, 29, 19, 46, 29, 4, "x", doors=[(37, 19)], lad=(45, 28, "north"),
                             pal=PAL_BAR["nt_gym"])
        mats = [(x, z) for x in (32, 33, 34, 35) for z in (23, 24, 25)]
        lay(d, ys[0], [(30, 22, LOCK), (30, 23, LOCK), (30, 24, LOCK), (30, 25, LOCK), (31, 20, "water_cauldron[level=3]"),
                       (41, 26, ST("birch", "east")), (42, 26, "iron_bars"), (41, 28, ST("birch", "east")),
                       (42, 28, "iron_bars"), (44, 21, "potted_bamboo"), ("lamp", 34, 24), ("lamp", 41, 23)])
        for x, z in mats:
            put(d, x, ys[0], z, "blue_carpet" if (x + z) % 2 else "light_blue_carpet")
        for x in (39, 42):                                    # punching bags
            put(d, x, ys[0] + 2, 22, CHAIN)
            put(d, x, ys[0] + 1, 22, "red_wool")
        lay(d, ys[1], [(32, 23, SST, "black_stained_glass_pane"), (32, 24, ST("birch", "south")),
                       (35, 23, SST, "black_stained_glass_pane"), (35, 24, ST("birch", "south")),
                       (38, 23, SST, "black_stained_glass_pane"), (38, 24, ST("birch", "south")),
                       (41, 23, SST, "black_stained_glass_pane"), (41, 24, ST("birch", "south")),
                       (31, 20, LOCK), (32, 20, LOCK), (33, 20, LOCK), (30, 28, "potted_bamboo"), (43, 20, "potted_bamboo"),
                       (36, 27, "white_concrete"), (37, 27, "white_concrete"), ("lamp", 35, 25), ("lamp", 41, 25)])
        lay(d, ys[2], [(31, 20, "smoker[facing=south,lit=false]"), (32, 20, "water_cauldron[level=3]"),
                       (33, 20, SST, POTD), (34, 20, "white_shulker_box[facing=up]"), (35, 20, SST, "flower_pot"),
                       (38, 24, SST, "potted_cactus"), (37, 24, ST("birch", "west")), (39, 24, ST("birch", "east")),
                       (38, 23, ST("birch", "north")), (41, 24, SST, "flower_pot"), (42, 24, ST("birch", "east")),
                       (41, 25, ST("birch", "south")), (30, 28, "potted_bamboo"), ("lamp", 38, 24), ("lamp", 33, 24)])
        lay(d, ys[3], [("bed", 31, 28, "south", "cyan"), ("bed", 33, 28, "south", "cyan"), ("bed", 35, 28, "south", "cyan"),
                       ("bed", 37, 28, "south", "cyan"), ("bed", 39, 28, "south", "cyan"), (32, 28, LOCK), (34, 28, LOCK),
                       (36, 28, LOCK), (38, 28, LOCK), (31, 20, LOCK), (32, 20, LOCK), (43, 20, "potted_bamboo"),
                       ("lamp", 35, 24), ("lamp", 40, 24)])
        for x in (30, 33, 42, 45):                           # planters along the front
            d.set(x, 1, 18, "grass_block[snowy=false]")
            put(d, x, 2, 18, "azalea")
        bench(d, 31, 17, "north")
        bench(d, 43, 17, "north")
        tree(d, 28, 17, 4)



# ================================================================================================ DECOR PASS
def shutters(d, cells, y, wood, out):
    """Open shutters either side of single window columns on a wall (cells = window (x, z))."""
    ox_, oz_ = OUT[out]
    sx_, sz_ = (1, 0) if out in ("north", "south") else (0, 1)
    for x, z in cells:
        for sgn in (-1, 1):
            put(d, x + ox_ + sx_ * sgn, y, z + oz_ + sz_ * sgn, TD(wood, out, "bottom", "true"))


def safe(d, x, y, z):
    """A detail block may go here: inside, empty, and nobody can stand right below it."""
    return d.bp.inside(x, y, z) and d.air(x, y, z) and (y < 2 or (d.air(x, y - 1, z) and d.air(x, y - 2, z)))


def sput(d, x, y, z, b):
    if safe(d, x, y, z):
        d.set(x, y, z, b)


def log_notches(d, x1, z1, x2, z2, y1, y2, log="spruce_log"):
    """Log-cabin corners: log ends sticking out past the corners on alternate courses."""
    for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        sx = -1 if x == x1 else 1
        sz = -1 if z == z1 else 1
        for y in range(y1, y2 + 1):
            if y % 2:
                sput(d, x + sx, y, z, LOG(log, "x"))
            else:
                sput(d, x, y, z + sz, LOG(log, "z"))


def corbels(d, cells, y, mat):
    """Corbel table: upside-down stairs on the outside of the given wall cells (x, z, outward)."""
    for x, z, out in cells:
        ox_, oz_ = OUT[out]
        sput(d, x + ox_, y, z + oz_, ST(mat, OPP[out], "top"))


def ring_out(foot, X0, Z0):
    """Outer-boundary cells of a footprint mask with the outward direction."""
    out = []
    for (rx, rz) in foot:
        for f, (dx, dz) in OUT.items():
            if (rx + dx, rz + dz) not in foot:
                out.append((X0 + rx, Z0 + rz, f))
    return out


def roof_units(d, cells, y):
    """Rooftop plant: AC units with grilles and a vent pipe (Neoterra)."""
    for x, z in cells:
        if d.air(x, y, z):
            d.set(x, y, z, "light_gray_concrete")
            put(d, x, y + 1, z, "iron_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]")
    if cells:
        x, z = cells[0]
        put(d, x - 1, y, z, "iron_bars")
        put(d, x - 1, y + 1, z, "lightning_rod[facing=up,powered=false,waterlogged=false]")


def fins(d, cells, y1, y2, mat):
    """Vertical facade fins standing proud of the wall (only where nobody walks)."""
    for x, z in cells:
        if all(d.bp.inside(x, y, z) and d.air(x, y, z) for y in range(y1, y2 + 1)):
            for y in range(y1, y2 + 1):
                d.set(x, y, z, mat)


# ---- premium cap: on levels 1-3 Neoterra builds in common materials (L4-5 upgrade to quartz, copper, etc.)
_COMMON = [("smooth_quartz_stairs", "polished_diorite_stairs", True), ("smooth_quartz_slab", "smooth_stone_slab", True),
           ("smooth_quartz", "smooth_stone", False), ("quartz_block", "calcite", False),
           ("quartz_pillar", "polished_diorite", False), ("quartz_slab", "smooth_stone_slab", True),
           ("cut_copper_slab", "smooth_stone_slab", True), ("cut_copper", "orange_terracotta", False),
           ("polished_blackstone_bricks", "deepslate_bricks", False),
           ("polished_blackstone_slab", "polished_deepslate_slab", True),
           ("polished_blackstone", "polished_deepslate", False), ("sea_lantern", "glowstone", False)]


def common_materials(d, L):
    if L > 3 or d.pack != "Neoterra":
        return
    bp = getattr(d, "_real", d.bp)
    for x, y, z, st in list(bp.blocks()):
        name = st.split("[")[0].split(":")[-1]
        props = st[len(st.split("[")[0]):]
        new = None
        for a, b, keep in _COMMON:
            if name == a:
                new = "minecraft:" + b + (props if keep else "")
                break
        if name == "end_rod":
            f = props.split("facing=")[1].split("]")[0].split(",")[0]
            if f == "up":
                new = "minecraft:lantern[hanging=false,waterlogged=false]"
            elif f == "down":
                new = "minecraft:lantern[hanging=true,waterlogged=false]"
            else:
                new = f"minecraft:soul_wall_torch[facing={f}]"
        if new:
            bp.set(x, y, z, new, bp.tile_entities.get((x, y, z)))


def place(d, y, items):
    """Hand-placed furniture: (x, z, block) or (x, z, block, block_on_top); only into empty cells."""
    for it in items:
        x, z, b = it[0], it[1], it[2]
        if put(d, x, y, z, b) and len(it) > 3:
            put(d, x, y + 1, z, it[3])


POT = "decorated_pot[cracked=false,facing=north,waterlogged=false]"
CANDLE = "candle[candles=3,lit=false,waterlogged=false]"


def dress_barracks(d, L):
    pk = d.pack
    if pk == "Hearthwood":
        sl = SL("dark_oak", "top")
        place(d, 2, [(15, 28, sl, POT), (16, 28, sl, CANDLE), (17, 28, "barrel[facing=north,open=false]"),
                     (18, 28, "barrel[facing=up,open=false]", "barrel[facing=north,open=false]"),
                     (19, 28, sl, "potted_red_tulip"), (20, 28, "potted_fern"),       # dresser on the back wall
                     (13, 20, ST("dark_oak", "north")), (14, 20, ST("dark_oak", "north")),  # bench by the door
                     (18, 20, sl, POT), (19, 20, sl, "flower_pot")])
        for z in (23, 25):                                    # fireside chairs facing the hearth
            d.set(19, 2, z, ST("dark_oak", "west"))
        for x in range(11, 22):                               # flower border along the hall front
            if x not in (15, 16, 17):
                flowers(d, [(x, 18)])
        for x in (12, 13, 19, 20):                            # window sills
            put(d, x, 2, 18, ST("stone_brick", "south", "top")) if False else None
        bench(d, 6, 17, "west", along="z") if L >= 2 else None
        cart(d, 22, 16, "x") if L >= 3 else None
        for x, z in ((24, 17), (25, 17)):
            put(d, x, 2, z, "barrel[facing=up,open=false]")
        put(d, 24, 3, 17, "decorated_pot[cracked=false,facing=north,waterlogged=false]")
        weapon_rack(d, [(6, 6), (6, 7)], 2, "spruce") if d.air(6, 2, 6) and d.air(6, 2, 7) else None
        lamp_post(d, 13, 17)
        lamp_post(d, 19, 17)
        HT = 6 if L < 5 else 10
        for x in range(10, 23):                               # dark-oak fascia under both eaves
            put(d, x, HT - 1, 18, TD("dark_oak", "north", "top"))
            put(d, x, HT - 1, 30, TD("dark_oak", "south", "top"))
        for x in (13, 19):                                    # lintels over the back windows
            put(d, x, 6, 30, "stone_brick_slab[type=top,waterlogged=false]") if HT > 6 else None
        for x in (14, 18):                                    # buttresses
            for z, out in ((18, "north"), (30, "south")):
                for y in range(2, HT - 1):
                    put(d, x, y, z, stone_mix(x, y, z))
                put(d, x, HT - 1, z, ST("stone_brick", OPP[out]))
        for y in range(30, 2, -1):                            # chimney cap on the hall flue
            if d.get(22, y, 24) == "minecraft:bricks":
                put(d, 22, y + 1, 24, "brick_wall") if d.get(21, y, 24) != AIR else None
                put(d, 21, y + 1, 24, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
                break
        if L >= 3:                                            # corbel table under the gate-tower parapet
            corbels(d, [(x, 2, "north") for x in range(13, 20)] + [(x, 5, "south") for x in range(13, 20)], 10,
                    "stone_brick")
    elif pk == "Cascadia":
        sl = SL("spruce", "top")
        place(d, 2, [(14, 14, sl, POT), (18, 14, "barrel[facing=south,open=false]"), (19, 14, sl, "potted_fern"),
                     (16, 20, sl, CANDLE), (17, 20, "barrel[facing=north,open=false]"), (18, 20, sl, POT),
                     (19, 20, "potted_fern")])
        for x in range(15, 19):                               # second bench along the mess table
            put(d, x, 2, 18, ST("spruce", "south"))
        shutters(d, [(13, 13), (19, 13)], 4, "dark_oak", "north")
        shutters(d, [(13, 21), (19, 21)], 4, "dark_oak", "south")
        shutters(d, [(11, 15), (11, 19)], 4, "dark_oak", "west")
        for x in (12, 20):                                    # flower barrels on the porch corners
            put(d, x, 2, 11, "barrel[facing=up,open=false]") if False else None
        flowers(d, [(x, z) for x in range(22, 22 + 1) for z in range(13, 20 + 1)])
        lamp_post(d, 14, 9)
        lamp_post(d, 18, 9)
        bench(d, 9, 20, "west", along="z") if L >= 2 else None
        cart(d, 23, 21, "z") if L >= 2 else None
        for x in range(10, 23):                               # spruce fascia under the back eave
            put(d, x, 5, 22, TD("spruce", "south", "top"))
        for x in (13, 19):                                    # window heads on the back wall
            put(d, x, 5, 21, LOG("stripped_spruce_log", "x")) if False else None
        log_notches(d, 11, 13, 21, 21, 3, 5)
        for y in range(30, 2, -1):
            if d.get(22, y, 17).split("[")[0].split(":")[1] in ("cobblestone", "mossy_cobblestone", "andesite", "tuff"):
                put(d, 22, y + 1, 17, "cobblestone_wall")
                put(d, 22, y + 2, 17, "cobblestone_slab[type=bottom,waterlogged=false]")
                break
    else:
        for x, z, b in ((10, 22, "potted_bamboo"), (12, 21, "potted_azalea_bush"), (15, 21, "potted_bamboo")):
            put(d, x, 2, z, b)
        d.chair(10, 2, 23, "west", "birch", sit=False) if d.air(10, 2, 23) else None
        for x in range(9, 14):                                # lockers along the armoury back wall upstairs
            pass
        for x in range(14, 17):
            put(d, x, 2, 29, "light_gray_shulker_box[facing=up]")
        flowers(d, [(x, z) for x in range(8, 11 + 1) for z in range(18, 18 + 1)])
        flowers(d, [(x, z) for x in range(15, 18 + 1) for z in range(18, 18 + 1)])
        for x in (7, 19):
            lamp_post(d, x, 19)
        bench(d, 4, 21, "west", along="z")
        bench(d, 22, 21, "east", along="z")
        top = 12 if L >= 3 else 7
        for x in range(9, 18):                                # ledge over the ground-floor glazing
            put(d, x, 7, 19, SST)
        fins(d, [(8, 19), (18, 19)], 2, top, "cyan_concrete")
        if L < 5:
            roof_units(d, [(10, 28), (11, 28), (15, 28)], top + 2)
        else:
            roof_units(d, [(10, 22), (16, 22)], top + 2)


def dress_gatehouse(d, L):
    pk = d.pack
    if pk == "Hearthwood":
        sl = SL("dark_oak", "top")
        place(d, 2, [(2, 4, "chest[facing=east,type=single,waterlogged=false]"), (2, 5, sl, CANDLE),
                     (5, 3, sl, "potted_red_tulip"), (4, 4, "red_carpet"), (4, 5, "red_carpet"),
                     (17, 4, "chest[facing=west,type=single,waterlogged=false]"), (17, 5, sl, CANDLE),
                     (16, 3, sl, POT), (15, 5, "red_carpet"), (15, 6, "red_carpet")])
        for X0 in (1, 12):
            put(d, X0 + 3, 10, 9, "red_wall_banner[facing=north]")
            put(d, X0 + 3, 10, 2, "white_wall_banner[facing=south]")
        for z in (5, 8):                                      # chained lanterns in the passage
            d.set(9, 6, z, LANT)
            d.set(10, 6, z, LANT)
        for X0 in (1, 12):
            corbels(d, ring_out(D7_FOOT, X0, 1), 11, "stone_brick")
            put(d, X0 + 3, 10, 0, "stone_brick_slab[type=top,waterlogged=false]")   # hood over the upper slit
            put(d, X0 + 3, 10, 11, "stone_brick_slab[type=top,waterlogged=false]")
        d.banner(8, 4, 7, "east", "red") if d.air(8, 4, 7) else None
        d.banner(11, 4, 7, "west", "red") if d.air(11, 4, 7) else None
    elif pk == "Cascadia":
        sl = SL("spruce", "top")
        place(d, 2, [(2, 4, "chest[facing=east,type=single,waterlogged=false]"), (2, 5, sl, CANDLE),
                     (3, 4, "brown_carpet"), (4, 4, "brown_carpet"),
                     (15, 4, sl, POT), (15, 5, "barrel[facing=west,open=false]"), (14, 4, "brown_carpet")])
        for X0 in (1, 11):
            shutters(d, [(X0 + 2, 2)], 9, "dark_oak", "north")
            for x in range(X0 - 1, X0 + 7):                   # fascia under the north and south eaves
                put(d, x, 9, 1, TD("spruce", "north", "top"))
                put(d, x, 9, 8, TD("spruce", "south", "top"))
            log_notches(d, X0, 2, X0 + 5, 7, 5, 9)
            put(d, X0 + 2, 10, 1, LOG("stripped_spruce_log", "x")) if False else None
        for z in (4, 6):
            d.set(8, 6, z, LANT) if d.air(8, 6, z) else None
        d.banner(7, 4, 6, "east", "green") if d.air(7, 4, 6) else None
    else:
        locker = "light_gray_shulker_box[facing=up]"
        st_sl = "smooth_stone_slab[type=top,waterlogged=false]"
        place(d, 2, [(2, 5, locker), (2, 4, locker), (3, 3, st_sl, "potted_bamboo"), (3, 5, "light_gray_carpet"),
                     (19, 5, locker), (19, 4, locker), (18, 3, st_sl, "potted_bamboo"), (17, 5, "light_gray_carpet")])
        for X0 in (1, 14):
            place(d, 7, [(X0 + 3, 3, st_sl, "potted_bamboo"), (X0 + 3, 4, "cyan_carpet"), (X0 + 3, 6, "cyan_carpet")])
        for X0 in (1, 14):
            roof_units(d, [(X0 + 2, 6), (X0 + 3, 6)], 12) if L < 3 else roof_units(d, [(X0 + 2, 7)], 12)
            fins(d, [(X0, 1), (X0 + 6, 1)], 2, 11, "cyan_concrete")
            for x in range(X0 + 1, X0 + 6):                   # ledge over the street glazing
                put(d, x, 5, 1, SST)
        for x in (9, 12):
            d.set(x, 5, 6, "sea_lantern") if False else None


def dress_wallguard(d, L):
    pk = d.pack
    if pk == "Hearthwood":
        sl = SL("dark_oak", "top")
        place(d, 2, [(6, 3, "chest[facing=south,type=single,waterlogged=false]"), (7, 3, sl, CANDLE),
                     (6, 4, "red_carpet"), (8, 4, "red_carpet"), (6, 6, "red_carpet"), (8, 6, "red_carpet")])
        place(d, 8, [(7, 3, sl, CANDLE), (7, 7, "barrel[facing=north,open=false]"),
                     (7, 4, "red_carpet"), (7, 5, "red_carpet"), (7, 6, "red_carpet"), (8, 5, "red_carpet")])
        if L >= 2:
            place(d, 13, [(6, 7, sl, CANDLE), (7, 7, "lectern[facing=north,has_book=false,powered=false]"),
                          (8, 7, sl, POT), (6, 3, sl, "potted_red_tulip")])
        put(d, 6, 4, 9, "red_wall_banner[facing=south]")
        put(d, 8, 4, 9, "white_wall_banner[facing=south]")
        top = 12 if L == 1 else 17
        cells = [(x, 2, "north") for x in range(4, 11)] + [(x, 8, "south") for x in range(4, 11)] + \
                [(4, z, "west") for z in range(3, 8)] + [(10, z, "east") for z in range(3, 8)]
        corbels(d, cells, top, "stone_brick")
        put(d, 7, 10, 1, "stone_brick_slab[type=top,waterlogged=false]")         # hood over the north window
    elif pk == "Cascadia":
        sl = SL("spruce", "top")
        place(d, 2, [(8, 5, sl, POT), (8, 6, "barrel[facing=west,open=false]"), (5, 6, "brown_carpet"),
                     (7, 6, "brown_carpet")])
        place(d, 8, [(5, 3, sl, CANDLE), (7, 3, sl, POT), (9, 9, "chest[facing=north,type=single,waterlogged=false]"),
                     (5, 9, "barrel[facing=north,open=false]"), (7, 9, sl, CANDLE),
                     (5, 6, "green_carpet"), (7, 6, "green_carpet"), (5, 7, "green_carpet"), (7, 7, "green_carpet")])
        shutters(d, [(4, 2), (8, 2), (6, 10)], 10, "dark_oak", "north")
        for a_ in range(1, 12):                               # fascia round the overhanging roof
            put(d, a_, 10, 1, TD("spruce", "north", "top"))
            put(d, a_, 10, 11, TD("spruce", "south", "top"))
            put(d, 1, 10, a_, TD("spruce", "west", "top"))
            put(d, 11, 10, a_, TD("spruce", "east", "top"))
        log_notches(d, 2, 2, 10, 10, 8, 10)
        log_notches(d, 3, 3, 9, 9, 4, 6)
        for y in range(25, 10, -1):
            if "dark_oak_slab" in d.get(6, y, 6) or ("dark_oak" in d.get(6, y, 6) and L == 1):
                put(d, 6, y + 1, 6, "lightning_rod[facing=up,powered=false,waterlogged=false]") if L == 1 else None
                break
    else:
        st_sl = "smooth_stone_slab[type=top,waterlogged=false]"
        place(d, 2, [(4, 3, st_sl, "potted_bamboo"), (6, 3, "light_gray_shulker_box[facing=up]"),
                     (4, 6, "light_gray_carpet"), (6, 6, "light_gray_carpet")])
        place(d, 9, [(5, 7, st_sl, "potted_bamboo"), (4, 4, "cyan_carpet"), (6, 4, "cyan_carpet"),
                     (4, 6, "cyan_carpet"), (6, 6, "cyan_carpet")])
        fins(d, [(1, 2), (9, 2), (1, 8), (9, 8)] if L == 1 else [], 2, 12, "cyan_concrete")
        fins(d, [(x, 9) for x in (3, 7)], 2, 7, "cyan_concrete")
        for x in (4, 5, 6):                                   # ledges under the bunk-room windows
            put(d, x, 9, 1, SST)
            put(d, x, 9, 9, SST)


@design("barracks")
def barracks(pack, rel, L):
    d = {"Hearthwood": hw_bar, "Cascadia": cs_bar, "Neoterra": nt_bar}[pack](rel, L)
    {"Hearthwood": hw_bar_outer, "Cascadia": cs_bar_outer, "Neoterra": nt_bar_east}[pack](d, L)
    dress_barracks(d, L)
    common_materials(d, L)
    return d


# ================================================================================================ GATEHOUSE
# Hearthwood: twin D-shaped stone towers, arched passage with timber gates and (L2+) a raised iron portcullis,
#             crenellated fighting gallery above the arch for the archers, bunk rooms in the towers.
# Cascadia:   timber gate between two log blockhouse towers, plank walkway (roofed from L2) over the gate.
# Neoterra:   security checkpoint: two concrete guard blocks, steel bar gate, glazed control bridge with a roof
#             terrace, bunk pods upstairs.
# Tags: gate = ground under the gate line, knight = ground just behind the gate, archer = wall-walk deck.
D7 = ["..###..",
      ".#...#.",
      "#.....#",
      "#.....#",
      "#.....#",
      "#.....#",
      "#.....#",
      "#.....#",
      "#.....#",
      "#######"]
D7_FOOT, D7_WALL, D7_IN = mask(D7)


GATE_IRON = "minecolonies:gate_iron[facing=south,half=lower,hinge=left,open=false,powered=false]"


def gate_line(d, x, z, L, wood):
    """Real gate blocks standing on the 'gate' tag cell (x, gy, z): fence gate 1 high (L1), 2 high (L2), then the
    MineColonies iron portcullis 4 high (L3)."""
    if L >= 3:
        for y in range(d.gy + 1, d.gy + 5):
            d.set(x, y, z, GATE_IRON)
    else:
        for y in range(d.gy + 1, d.gy + 1 + L):
            d.set(x, y, z, f"{wood}_fence_gate[facing=south,in_wall=false,open=false,powered=false]")


def gate_tags(d, xs, z, kx, kz, ax, adeck, az):
    for x in xs:
        d.tag(x, d.gy, z, "gate")
    for x in kx:
        d.tag(x, d.gy, kz, "knight")
    for x in ax:
        d.tag(x, adeck, az, "archer")


def gh_hearthwood(rel, L):
    d = Shifted("Hearthwood", rel, (38, 18, 24), gy=1, paving="grass_block[snowy=false]", ox=9)
    Z0 = 1
    for X0 in (1, 12):
        for (rx, rz) in D7_WALL:
            x, z = X0 + rx, Z0 + rz
            d.set(x, 1, z, "cobblestone")
            for y in range(2, 13):
                d.set(x, y, z, stone_mix(x, y, z))
            if (x + z) % 2 == 0:
                d.set(x, 13, z, stone_mix(x, 13, z))
        for (rx, rz) in D7_IN:
            x, z = X0 + rx, Z0 + rz
            d.set(x, 1, z, "spruce_planks")
            d.set(x, 7, z, "spruce_planks")
            d.set(x, 11, z, "stone_bricks")
        for (rx, rz) in D7_WALL:
            d.set(X0 + rx, 7, Z0 + rz, "polished_andesite")
        for y in (4, 9):                                      # arrow slits on the round front
            d.set(X0 + 3, y, Z0, "glass_pane")
            d.set(X0, y, Z0 + 4, "glass_pane") if X0 == 1 else d.set(X0 + 6, y, Z0 + 4, "glass_pane")
        d.set(X0 + 3, 9, Z0 + 9, "glass_pane")
    # gate block between the towers: passage x8..11, z3..9
    for x in range(8, 12):
        for z in range(3, 10):
            d.set(x, 1, z, "cobblestone" if (x + z) % 3 else "stone_bricks")
            for y in range(2, 7):
                d.set(x, y, z, AIR)
            d.set(x, 7, z, "stone_bricks")
        for z in (3, 9):
            d.set(x, 8, z, stone_mix(x, 8, z))
            if z == 3 and x % 2 == 0 or z == 9 and False:
                d.set(x, 9, z, stone_mix(x, 9, z))
        for z in range(4, 9):
            d.set(x, 8, z, AIR)
            d.set(x, 9, z, AIR)
    for z in (3, 9):                                          # pointed arch faces
        d.set(8, 6, z, ST("stone_brick", "west", "top"))
        d.set(11, 6, z, ST("stone_brick", "east", "top"))
        d.set(9, 7, z, "chiseled_stone_bricks") if z == 3 else None
    # gates on the gate line z=4
    for x in range(8, 12):
        gate_line(d, x, 4, L, "dark_oak")
        d.set(x, 6, 4, LOG("dark_oak_log", "x"))
        if L == 2:                                            # portcullis hanging raised behind the gates
            d.set(x, 6, 5, "iron_bars")
    gate_tags(d, range(8, 12), 4, (8, 11), 6, (9, 10), 7, 4)
    # doors from the passage into the towers, ladders, gallery doorways
    d.door(7, 2, 7, "west", "dark_oak")
    d.door(12, 2, 7, "east", "dark_oak")
    for x in (7, 12):
        d.set(x, 8, 6, AIR)
        d.set(x, 9, 6, AIR)
    ladder(d, 2, 9, 2, 11, "east")
    ladder(d, 17, 9, 2, 11, "west")
    # guard rooms
    d.hut(3, 2, 3)
    d.item(2, 2, 6, "barrel")
    d.item(17, 2, 6, "barrel")
    weapon_rack(d, [(6, 4), (6, 5)], 2, "dark_oak")
    weapon_rack(d, [(13, 4), (13, 5)], 2, "dark_oak")
    d.set(15, 2, 3, "chest[facing=south,type=single,waterlogged=false]")
    d.dining(4, 2, 8, 1, "x", "dark_oak", ("e",), sit=False)
    d.dining(15, 2, 8, 1, "x", "dark_oak", ("w",), sit=False)
    for x in (4, 15):
        d.lamp(x, 6, 5)
    # bunk rooms
    for X0 in (1, 12):
        y = 8
        for x in (X0 + 1, X0 + 5):
            pass
        d.bed(X0 + 1, y, 4, "west", "red")
        d.bed(X0 + 1, y, 6, "west", "red")
        d.bed(X0 + 5, y, 4, "east", "red") if X0 == 12 else d.bed(X0 + 5, y, 3, "east", "red")
        d.bed(X0 + 5, y, 8, "east", "red") if X0 == 1 else d.bed(X0 + 5, y, 8, "east", "red")
        d.set(X0 + 1, y, 5, SL("dark_oak", "top"))
        d.candle(X0 + 1, y + 1, 5, 2)
        d.lamp(X0 + 3, 10, 5)
        carpet(d, y, [(x, z) for x in range(X0 + 3, X0 + 3 + 1) for z in range(4, 7 + 1)], "red")
    # battlements: gallery front, flags
    for x in range(8, 12):
        d.set(x, 2, 2, AIR)
    for x in (7, 12):
        d.set(x, 5, 2, "wall_torch[facing=north]")
    if L >= 2:
        d.banner(7, 9, 2, "north", "red") if d.air(7, 9, 2) else None
        d.banner(12, 9, 2, "north", "red") if d.air(12, 9, 2) else None
    if L >= 3:                                                # machicolations over the gate, flags on the towers
        for x in range(8, 12):
            d.set(x, 7, 2, ST("stone_brick", "south", "top"))
            d.set(x, 8, 2, stone_mix(x, 8, 2))
            if x % 2 == 0:
                d.set(x, 9, 2, stone_mix(x, 9, 2))
            d.set(x, 9, 3, AIR) if x % 2 == 0 else None
        for X0 in (1, 12):
            for y in range(12, 17):
                d.set(X0 + 3, y, 6, "dark_oak_fence")
            d.set(X0 + 4, 16, 6, "red_wool")
            d.set(X0 + 4, 15, 6, "white_wool")
    for x in range(1, 19):                                    # approach path
        for z in (0, 11, 12):
            if 7 <= x <= 12:
                d.set(x, 1, z, "cobblestone" if (x + z) % 2 else "gravel")
    gh_complex(d, L, 1, 18, 8, 11, 10, 8)
    return d


def gh_cascadia(rel, L):
    d = Shifted("Cascadia", rel, (34, 18, 21), gy=1, paving="coarse_dirt", ox=8)
    for X0 in (1, 11):
        x1, x2, z1, z2 = X0, X0 + 5, 2, 7
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                edge = x in (x1, x2) or z in (z1, z2)
                corner = x in (x1, x2) and z in (z1, z2)
                d.set(x, 1, z, rock(x, 1, z) if edge else "spruce_planks")
                for y in range(2, 11):
                    if not edge:
                        b = AIR
                    elif y <= 3:
                        b = rock(x, y, z)
                    elif corner:
                        b = LOG("spruce_log")
                    else:
                        b = LOG("stripped_spruce_log", "x" if z in (z1, z2) else "z")
                    d.set(x, y, z, b)
                if not edge:
                    d.set(x, 7, z, "spruce_planks")
                else:
                    d.set(x, 7, z, LOG("dark_oak_log", "x" if z in (z1, z2) else "z"))
        d.set(x1, 7, z1, LOG("spruce_log"))
        soft(d, d.hip, x1, z1, x2, z2, 11, "dark_oak_stairs", "dark_oak_slab", 1)
        d.fill(x1 + 1, 11, z1 + 1, x2 - 1, 11, z2 - 1, "spruce_planks")
        for y in (5, 9):
            d.set(X0 + 2, y, z1, "glass_pane")
            d.set(X0 + 3, y, z1, "glass_pane") if y == 9 else None
            d.set(x1 if X0 == 1 else x2, y, 5, "glass_pane")
    # passage x7..10 under the walkway, gate at z=3
    for x in range(7, 11):
        for z in range(1, 9):
            d.set(x, 1, z, "dirt_path")
        gate_line(d, x, 3, L, "spruce")
        d.set(x, 6, 2, LOG("spruce_log", "x"))
        for z in range(2, 8):
            d.set(x, 7, z, "spruce_planks")
        d.set(x, 8, 2, LOG("spruce_log", "x") if x % 2 else "spruce_fence")
        d.set(x, 8, 7, "spruce_fence")
    if L < 3:
        for x in (7, 10):
            d.set(x, 5, 3, ST("spruce", "east" if x == 7 else "west", "top"))
    gate_tags(d, range(7, 11), 3, (7, 10), 5, (8, 9), 7, 3)
    # doors, ladders, walkway doorways
    d.door(6, 2, 5, "west", "spruce")
    d.door(11, 2, 5, "east", "spruce")
    for x in (6, 11):
        d.set(x, 8, 5, AIR)
        d.set(x, 9, 5, AIR)
    ladder(d, 5, 6, 2, 7, "north")
    ladder(d, 12, 6, 2, 7, "north")
    d.hut(2, 2, 3)
    d.item(2, 2, 6, "barrel")
    d.item(15, 2, 3, "barrel")
    d.set(15, 2, 6, "chest[facing=west,type=single,waterlogged=false]")
    weapon_rack(d, [(5, 3)], 2, "spruce")
    weapon_rack(d, [(12, 3)], 2, "spruce")
    d.set(3, 5, 4, LANT)
    d.set(14, 5, 4, LANT)
    # bunks (4 per tower)
    for wx, ex, side in ((2, 5, "east"), (15, 12, "west")):
        d.bed(wx, 8, 3, "north", "brown")
        d.bed(wx, 8, 6, "south", "brown")
        d.bed(ex, 8, 3, side, "brown")
        d.bed(ex, 8, 4, side, "brown")
        d.set((wx + ex) // 2, 10, 5, LANT)
    # palisade stubs on both sides
    for x in (0, 17):
        for z in (4, 5):
            for y in range(2, 9):
                d.set(x, y, z, LOG("spruce_log"))
            d.set(x, 9, z, "spruce_fence")
    if L >= 2:                                                # roof over the walkway
        for x in range(7, 11):
            d.set(x, 11, 1, ST("dark_oak", "south"))
            d.set(x, 11, 8, ST("dark_oak", "north"))
            for z in range(2, 8):
                d.set(x, 12, z, SL("dark_oak"))
            d.set(x, 11, 2, "spruce_planks") if False else None
        for x in (7, 10):
            for z in (2, 7):
                for y in (9, 10, 11):
                    d.set(x, y, z, "spruce_fence")
        d.set(8, 11, 4, LANT)
        d.sign(8, 9, 1, "north", ["CAMP GATE"], "spruce") if False else None
    if L >= 3:
        d.set(9, 11, 5, "bell[attachment=ceiling,facing=north,powered=false]")
        for x in (6, 11):
            d.set(x, 5, 1, "wall_torch[facing=north]")
        d.banner(3, 6, 1, "north", "green")
        d.banner(14, 6, 1, "north", "green")
    gh_complex(d, L, 1, 16, 7, 10, 7, 8)
    return d


def gh_neoterra(rel, L):
    d = Shifted("Neoterra", rel, (38, 18, 22), gy=1, paving="smooth_stone", ox=8)
    for X0 in (1, 14):
        x1, x2, z1, z2 = X0, X0 + 6, 2, 8
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                edge = x in (x1, x2) or z in (z1, z2)
                corner = x in (x1, x2) and z in (z1, z2)
                d.set(x, 1, z, "polished_diorite")
                for y in range(2, 11):
                    d.set(x, y, z, ("light_gray_concrete" if corner else "white_concrete") if edge else AIR)
                d.set(x, 6, z, "cyan_terracotta" if edge and not corner else "light_gray_concrete")
                d.set(x, 11, z, "smooth_quartz")
                if edge:
                    d.set(x, 12, z, "smooth_quartz_slab[type=bottom,waterlogged=false]")
        for x in range(x1 + 1, x2):                           # glazing
            d.window(x, 2, z1, x, 4, z1, "glass_pane")
            d.window(x, 8, z1, x, 9, z1, "light_gray_stained_glass_pane")
            d.window(x, 8, z2, x, 9, z2, "light_gray_stained_glass_pane")
        outer = x1 if X0 == 1 else x2
        for z in range(z1 + 2, z2 - 1):
            d.window(outer, 3, z, outer, 4, z, "light_gray_stained_glass_pane")
    # passage x8..13 with the steel gate on z=3
    for x in range(8, 14):
        for z in range(0, 11):
            d.set(x, 1, z, "gray_concrete" if 9 <= x <= 12 else "light_gray_concrete")
    for z in (0, 10):
        for x in range(9, 13):
            d.set(x, 1, z, "yellow_concrete" if x % 2 else "black_concrete")
    for x in (8, 13):
        d.set(x, 2, 3, "gray_concrete")
        d.set(x, 3, 3, "sea_lantern")
    for x in range(9, 13):
        for y in (2, 3, 4, 5):
            d.set(x, y, 3, GATE_IRON)
    gate_tags(d, range(9, 13), 3, (8, 13), 5, (10, 11), 11, 4)
    # glazed control bridge (upper floor level) with roof terrace
    for x in range(8, 14):
        for z in range(2, 9):
            d.set(x, 6, z, "light_gray_concrete")
            for y in range(7, 11):
                d.set(x, y, z, "light_blue_stained_glass_pane" if z in (2, 8) else AIR)
            d.set(x, 11, z, "smooth_quartz")
        d.set(x, 12, 2, "light_gray_stained_glass_pane")
        d.set(x, 12, 8, "light_gray_stained_glass_pane")
        d.set(x, 5, 2, "smooth_quartz_slab[type=top,waterlogged=false]")
    d.sign(10, 6, 1, "north", ["CHECK", "POINT"], "birch", glow=True, color="cyan")
    d.sign(11, 6, 1, "north", ["GATE", "01"], "birch", glow=True, color="cyan")
    for x in (7, 14):
        d.set(x, 7, 5, AIR)
        d.set(x, 8, 5, AIR)
    for x in range(9, 13):
        d.set(x, 7, 3, "smooth_quartz_slab[type=top,waterlogged=false]")
        d.set(x, 8, 3, "black_stained_glass_pane") if x in (9, 12) else None
    d.chair(10, 7, 4, "south", "birch", sit=False)
    d.chair(11, 7, 4, "south", "birch", sit=False)
    ladder(d, 12, 7, 7, 11, "north")
    d.set(12, 7, 8, "white_concrete")
    for y in range(7, 12):
        d.set(12, y, 8, "white_concrete")
    d.set(9, 10, 6, "sea_lantern")
    # guard blocks: doors from the passage, ladders up, desks
    d.door(7, 2, 5, "west", "birch")
    d.door(14, 2, 5, "east", "birch")
    for X0, lx in ((1, 4), (14, 17)):
        ladder(d, lx, 7, 2, 6, "north")
    d.hut(2, 2, 3)
    d.item(2, 2, 7, "barrel")
    d.item(19, 2, 7, "barrel")
    for z in (3, 4):
        d.set(6, 2, z, "smooth_quartz_slab[type=top,waterlogged=false]")
        d.set(15, 2, z, "smooth_quartz_slab[type=top,waterlogged=false]")
    d.set(6, 3, 3, "black_stained_glass_pane")
    d.set(15, 3, 3, "black_stained_glass_pane")
    d.chair(5, 2, 4, "east", "birch", sit=False)
    d.chair(16, 2, 4, "west", "birch", sit=False)
    d.set(19, 2, 3, "light_gray_shulker_box[facing=up]")
    d.set(3, 5, 5, "sea_lantern")
    d.set(17, 5, 5, "sea_lantern")
    # bunk pods upstairs (4 per block)
    for X0 in (1, 14):
        y = 7
        d.bed(X0 + 1, y, 3, "west", "cyan")
        d.bed(X0 + 1, y, 7, "west", "cyan")
        d.bed(X0 + 5, y, 3, "east", "cyan")
        d.bed(X0 + 5, y, 7, "east", "cyan") if X0 == 1 else d.bed(X0 + 5, y, 7, "east", "cyan")
        d.set(X0 + 1, y, 5, "light_gray_shulker_box[facing=up]")
        d.set(X0 + 3, 10, 4, "sea_lantern")
    # roof terrace access from the bridge, rails, searchlights
    for X0 in (1, 14):
        for x in range(X0, X0 + 7):
            for z in (2, 8):
                pass
    if L >= 2:                                                # planters and bollards on the approach
        for x in (6, 15):
            d.set(x, 1, 0, "grass_block[snowy=false]")
            d.set(x, 2, 0, "azalea")
        for x in (8, 13):
            d.set(x, 2, 0, "polished_andesite")
    if L >= 3:
        for x, z in ((1, 2), (20, 2), (1, 8), (20, 8)):
            d.set(x, 13, z, ENDROD())
        d.set(8, 12, 5, "sea_lantern")
        d.set(13, 12, 5, "sea_lantern")
        for x in range(3, 7):
            d.set(x, 12, 5, "daylight_detector[inverted=false,power=0]")
            d.set(x + 13, 12, 5, "daylight_detector[inverted=false,power=0]")
    gh_complex(d, L, 1, 20, 8, 13, 8, 9)
    return d


def curtain_col(d, x, yw):
    """One cross-section of the pack's town wall (outer face north) with its walk at standing level yw."""
    pk = d.pack
    if pk == "Hearthwood":
        for z in range(3, 7):
            d.set(x, 1, z, "cobblestone")
            for y in range(2, yw):
                d.set(x, y, z, stone_mix(x, y, z))
        d.set(x, yw, 3, stone_mix(x, yw, 3))
        if x % 2 == 0:
            d.set(x, yw + 1, 3, stone_mix(x, yw + 1, 3))
    elif pk == "Cascadia":
        for y in range(2, yw + 1):
            d.set(x, y, 4, LOG("spruce_log"))
        d.set(x, yw + 1, 4, "spruce_fence" if x % 2 else LOG("stripped_spruce_log"))
        d.set(x, 1, 4, rock(x, 1, 4))
        for z in (5, 6):
            d.set(x, yw - 1, z, "spruce_planks")
        if x % 3 == 0:
            for y in range(2, yw - 1):
                d.set(x, y, 6, "spruce_fence")
    else:
        for z in range(4, 7):
            d.set(x, 1, z, "polished_andesite")
            for y in range(2, yw):
                d.set(x, y, z, "white_concrete" if z == 4 else "light_gray_concrete")
        d.set(x, 5, 4, "cyan_terracotta")
        d.set(x, yw, 4, "light_gray_stained_glass_pane")
        d.set(x, yw, 6, "iron_bars")


def gh_complex(d, L, xa, xb, r1, r2, tz, yw):
    """Growth of a gatehouse: L2 town-wall wings with stairs to the walk and a guard post; L3 a guard barracks
    and an armoury / stable flanking the road behind. xa..xb = gatehouse, r1..r2 = road, tz = back z."""
    pk = d.pack
    pave = {"Hearthwood": "cobblestone", "Cascadia": "dirt_path", "Neoterra": "gray_concrete"}[pk]
    border = {"Hearthwood": "stone_bricks", "Cascadia": "coarse_dirt", "Neoterra": "light_gray_concrete"}[pk]
    zmax = d.sz - 1
    for z in range(tz + 1, zmax + 1):
        for x in range(r1, r2 + 1):
            d.set(x, 1, z, pave if pk != "Hearthwood" or (x + z) % 4 else "gravel")
        d.set(r1 - 1, 1, z, border)
        d.set(r2 + 1, 1, z, border)
    for x in range(r1, r2 + 1):
        d.set(x, 1, 0, pave)
    lamp_post(d, r1 - 2, tz + 2)
    lamp_post(d, r2 + 2, tz + 2)
    if L >= 2:
        for x in list(range(xa - 9, xa)) + list(range(xb + 1, xb + 10)):
            curtain_col(d, x, yw)
        mat = {"Hearthwood": "stone_brick", "Cascadia": "spruce", "Neoterra": "smooth_quartz"}[pk]
        sup = {"Hearthwood": "stone_bricks", "Cascadia": "spruce_planks", "Neoterra": "white_concrete"}[pk]
        n = yw - 2
        for side in (-1, 1):
            for i in range(n):
                x = (xa - 2 - i) if side < 0 else (xb + 2 + i)
                d.set(x, 2 + i, 7, ST(mat, "west" if side < 0 else "east"))
                for y in range(2, 2 + i):
                    d.set(x, y, 7, sup)
        for x in (xa - 9, xb + 9):                              # wall-end caps
            for z in (4, 5, 6):
                if pk != "Cascadia":
                    d.set(x, yw, z, "white_concrete" if pk == "Neoterra" else stone_mix(x, yw, z))
        # sentry boxes on the street side and benches / barrels at the gate
        for x in (xa - 2, xb + 2):
            put(d, x, 2, 1, "barrel[facing=up,open=false]")
            put(d, x, 3, 1, LANT_S if pk != "Neoterra" else "sea_lantern")
        if pk == "Cascadia":                                  # firewood stack under a slab roof, hitching rail
            for x in range(xb + 3, xb + 8):
                put(d, x, 2, tz + 1, LOG("spruce_log", "x"))
                put(d, x, 3, tz + 1, LOG("spruce_log", "x"))
                put(d, x, 4, tz + 1, SL("spruce"))
            for x in range(xa - 8, xa - 1):
                put(d, x, 2, tz + 2, "spruce_fence")
            put(d, xa - 7, 3, tz + 2, LANT_S)
            put(d, xa - 4, 2, tz + 3, "water_cauldron[level=3]")
            put(d, xa - 5, 2, tz + 3, "hay_block[axis=x]")
            if L == 2:                                         # guard hut and a trader's stall (replaced at L3)
                sentry_box(d, xb + 5, tz + 4, "west")
                stall(d, xa - 6, tz + 6, "red", ("pumpkin", "barrel[facing=up,open=false]", "melon"))
                cart(d, xa - 6, tz + 9, "x")
                lamp_post(d, xa - 8, tz + 6)
                lamp_post(d, xb + 4, tz + 8)
                for x in (xb + 8, xb + 9):
                    put(d, x, 2, tz + 5, "barrel[facing=up,open=false]")
                put(d, xb + 8, 3, tz + 5, "barrel[facing=north,open=false]")
        bench(d, r1 - 2, tz + 4, "west", along="z")
        bench(d, r2 + 2, tz + 4, "east", along="z")
        if L == 2:
            hedge(d, [(x, tz + 3) for x in range(xa - 8, r1 - 3)] + [(x, tz + 3) for x in range(r2 + 4, xb + 9)])
    if L >= 3:
        wx1, wx2 = xa - 8, r1 - 3
        za, zz = tz + 3, tz + 10
        ys, top, ridge = bld(d, wx1, za, wx2, zz, 2, "x", pal=PAL[("gh", pk, "a")],
                             doors=[(wx2, tz + 8)], lad=(wx1 + 1, za + 1, "east"),
                             chimney=(wx1 + 3, zz) if pk != "Neoterra" else None)
        gh_barracks_in(d, ys, wx1 + 1, wx2 - 1, tz)
        ex1, ex2 = r2 + 3, xb + 8
        kind = {"Hearthwood": "armoury", "Cascadia": "stable", "Neoterra": "armoury"}[pk]
        ys, top, ridge = bld(d, ex1, za, ex2, zz, 1, "x", doors=[(ex1, tz + 8)], sh=5, pal=PAL[("gh", pk, "b")])
        gh_east_in(d, ys[0], ex1 + 1, ex2 - 1, tz)
        if zz + 1 <= zmax:
            flowers(d, [(x, z) for x in range(wx1 + 1, wx2 - 2 + 1) for z in range(zz + 1, zz + 1 + 1)])
            cart(d, ex1 + 3, zz + 1, "x")
        tree(d, ex2 - 1, tz + 7 if False else zz - 9, 4) if False else None
        lamp_post(d, r1 - 2, zz)
        lamp_post(d, r2 + 2, zz)


@design("gatehouse")
def gatehouse(pack, rel, L):
    d = {"Hearthwood": gh_hearthwood, "Cascadia": gh_cascadia, "Neoterra": gh_neoterra}[pack](rel, L)
    dress_gatehouse(d, L)
    common_materials(d, L)
    return d


# ================================================================================================ WALL GUARD TOWER
# Hearthwood: square stone tower astride a crenellated curtain-wall section; armoury below, bunks at wall-walk
#             level with doors onto the walks, battlements; L2 lookout storey, L3 machicolations, L4 flag,
#             L5 tiled spire roof.
# Cascadia:   log blockhouse on a palisade section with a plank firing walk; L2 roof lookout with bell,
#             L3 porch lean-to, L5 flag.
# Neoterra:   concrete watch post on a security wall: lobby/armoury, bunks at wall-walk level, glazed watch cab
#             (L2+) with antenna and searchlights.
RACKS = {1: 1, 2: 1, 3: 2, 4: 2, 5: 3}
LOGW = {"Hearthwood": "stripped_oak_log", "Cascadia": "spruce_log", "Neoterra": "stripped_birch_log"}
WT_WALL = {1: (-7, 7), 2: (-11, 9), 3: (-13, 11), 4: (-15, 15), 5: (-15, 15)}   # wall run, relative to the tower


# ================================================================================================ INTERIORS
# Every room below is laid out by hand: explicit (x, z) positions chosen for that building, that pack and that room.
# lay() only maps the listed positions (u = distance from a reference wall, mirrored for Cascadia's mirrored
# wall-tower complex) and draws each listed piece.
def _mir(b, m):
    if not m:
        return b
    return b.replace("facing=east", "facing=TMP").replace("facing=west", "facing=east").replace("facing=TMP",
                                                                                               "facing=west")


def lay(d, y, items, X=None, m=False):
    """items: (x, z, block[, block on top]) or ("bed", x, z, facing, colour) or ("lamp", x, z) – x is mapped by X."""
    X = X or (lambda u: u)
    for it in items:
        if it[0] == "bed":
            _, u, z, f, c = it
            d.bed(X(u), y, z, _mir(f"facing={f}", m)[7:], c)
        elif it[0] == "lamp":
            _, u, z = it[:3]
            dy = it[3] if len(it) > 3 else 2
            put(d, X(u), y + dy, z, LANT)
        else:
            x, z, b = X(it[0]), it[1], _mir(it[2], m)
            if put(d, x, y, z, b) and len(it) > 3:
                put(d, x, y + 1, z, _mir(it[3], m))


SLD = lambda w: SL(w, "top")
SST = "smooth_stone_slab[type=top,waterlogged=false]"
BAR = "barrel[facing=up,open=false]"
KEG = lambda f: f"barrel[facing={f},open=false]"
CH = lambda f: f"chest[facing={f},type=single,waterlogged=false]"
BOOK = lambda f: (f"chiseled_bookshelf[facing={f},slot_0_occupied=true,slot_1_occupied=true,slot_2_occupied=false,"
                  f"slot_3_occupied=true,slot_4_occupied=false,slot_5_occupied=true]")
FIRE = lambda f: f"campfire[facing={f},lit=true,signal_fire=false,waterlogged=false]"
LOCK = "light_gray_shulker_box[facing=up]"
POTD = "decorated_pot[cracked=false,facing=north,waterlogged=false]"
CAN3 = "candle[candles=3,lit=false,waterlogged=false]"
CAN1 = "candle[candles=1,lit=false,waterlogged=false]"


# ---- wall tower complex -------------------------------------------------------------------------------------
def wt_shed_in(d, cx):
    """Shed (x cx+6..cx+9, z 8..9, door from the west at z 9)."""
    pk = d.pack
    items = {"Hearthwood": [(cx + 7, 8, BAR, BAR), (cx + 8, 8, "white_wool"), (cx + 9, 8, "hay_block[axis=y]"),
                            (cx + 9, 9, KEG("west"))],
             "Cascadia": [(cx + 7, 8, LOG("spruce_log", "x"), LOG("spruce_log", "x")), (cx + 8, 8, LOG("spruce_log", "x")),
                          (cx + 9, 8, "grindstone[face=floor,facing=west]"), (cx + 9, 9, BAR)],
             "Neoterra": [(cx + 7, 8, LOCK, LOCK), (cx + 8, 8, LOCK), (cx + 9, 8, "lightning_rod[facing=up,powered=false,"
                                                                                  "waterlogged=false]"),
                          (cx + 9, 9, BAR)]}[pk]
    lay(d, 2, items)


def wt_guard_in(d, L, ys, U, m, ng):
    """Guardhouse: u = 0 at the far (chimney / ladder) end, u = 8 by the door (z 14); rows z 12..17; chimney in the
    back wall at u = 2, ladder at (0, 17) from L4."""
    pk, w = d.pack, WOOD[d.pack]
    if pk == "Hearthwood":       # guard room: fireplace, mess table, kegs and dresser
        g = [(2, 17, FIRE("north")), (1, 17, "polished_andesite") if ng == 1 else (3, 16, "red_carpet"),
             (3, 17, "polished_andesite"), (2, 16, "red_carpet"), (1, 15, ST(w, "west")), (3, 15, ST(w, "east")),
             (4, 13, ST(w, "north")), (5, 13, ST(w, "north")), (6, 13, ST(w, "north")),
             (4, 14, "stripped_dark_oak_wood[axis=x]", CAN3), (5, 14, "stripped_dark_oak_wood[axis=x]"),
             (6, 14, "stripped_dark_oak_wood[axis=x]", CAN1), (4, 15, ST(w, "south")), (5, 15, ST(w, "south")),
             (6, 15, ST(w, "south")), (5, 17, KEG("north")), (6, 17, KEG("north"), KEG("north")),
             (7, 17, "water_cauldron[level=3]"), (1, 12, SLD(w), POTD), (2, 12, SLD(w), "potted_red_tulip"),
             (3, 12, f"smoker[facing=south,lit=true]"), (8, 12, BAR), (0, 12, "potted_fern"),
             ("lamp", 5, 14), ("lamp", 2, 15)]
    elif pk == "Cascadia":       # mess cabin: iron stove, long table across, wash tub, wood box
        g = [(2, 17, "furnace[facing=north,lit=true]"), (1, 17, LOG("spruce_log", "x")) if ng == 1 else (3, 16, AIR),
             (3, 17, "water_cauldron[level=3]"), (4, 17, SLD(w), POTD),
             (5, 13, "stripped_spruce_wood[axis=z]", CAN3), (5, 14, "stripped_spruce_wood[axis=z]"),
             (5, 15, "stripped_spruce_wood[axis=z]", CAN1), (4, 13, ST(w, "east")), (4, 14, ST(w, "east")),
             (4, 15, ST(w, "east")), (6, 13, ST(w, "west")), (6, 14, ST(w, "west")), (6, 15, ST(w, "west")),
             (0, 12, KEG("east")), (1, 12, KEG("east"), KEG("east")), (2, 12, "hay_block[axis=x]"),
             (8, 17, CH("north")), (7, 17, SLD(w), "lantern[hanging=false,waterlogged=false]"),
             (8, 12, "potted_fern"), ("lamp", 5, 14), ("lamp", 1, 15)]
    else:                        # crew lounge: kitchenette, sofa corner, dining table
        g = [(2, 17, "smoker[facing=north,lit=false]"), (3, 17, "water_cauldron[level=3]"), (4, 17, SST, "flower_pot"),
             (5, 17, "white_shulker_box[facing=up]"), (6, 17, SST, POTD), (0, 12, "potted_bamboo"),
             (1, 12, "birch_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]"),
             (2, 12, "birch_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]"),
             (3, 12, "birch_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]"),
             (2, 13, "birch_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]"),
             (6, 15, SST, "potted_cactus"), (6, 14, ST("birch", "south")), (6, 16, ST("birch", "north")),
             (8, 12, LOCK), (7, 12, LOCK), ("lamp", 2, 15), ("lamp", 6, 15)]
    lay(d, ys[0], g, U, m)
    if ng < 2:
        return
    y = ys[1]
    if pk == "Hearthwood":       # sergeant's room: desk by the window, map table, bookcase wall, cot
        g = [(7, 12, BOOK("south")), (6, 12, BOOK("south")), (5, 12, "lectern[facing=south,has_book=false,powered=false]"),
             (4, 12, "cartography_table"), (8, 15, SLD(w), CAN1), (8, 16, SLD(w), "flower_pot"), (7, 15, ST(w, "east")),
             ("bed", 4, 17, "south", "red"), (5, 17, SLD(w), CAN3), (3, 17, CH("north")),
             (5, 14, "red_carpet"), (6, 14, "red_carpet"), (5, 15, "red_carpet"), (6, 15, "red_carpet"),
             (1, 12, "potted_red_tulip"), ("lamp", 5, 14)]
    elif pk == "Cascadia":       # bunk loft: three bunks along the north wall, footlockers, wash stand
        g = [("bed", 3, 12, "north", "brown"), ("bed", 5, 12, "north", "brown"), ("bed", 7, 12, "north", "brown"),
             (4, 12, SLD(w), CAN1), (6, 12, SLD(w), CAN1), (8, 12, "potted_fern"),
             (3, 17, CH("north")), (5, 17, CH("north")), (7, 17, "water_cauldron[level=3]"), (8, 17, BAR),
             (4, 15, "green_carpet"), (5, 15, "green_carpet"), (6, 15, "green_carpet"), ("lamp", 5, 14)]
    else:                        # duty office: two desks with screens, filing lockers, plant
        g = [(3, 12, SST), (3, 12, SST), (4, 12, SST, "black_stained_glass_pane"), (5, 12, SST),
             (4, 13, ST("birch", "south")), (7, 15, SST, "black_stained_glass_pane"), (7, 16, SST),
             (6, 15, ST("birch", "east")), (2, 17, LOCK), (3, 17, LOCK), (4, 17, LOCK), (8, 12, "potted_bamboo"),
             (5, 15, "cyan_carpet"), (4, 15, "cyan_carpet"), ("lamp", 4, 14), ("lamp", 7, 14)]
    lay(d, y, g, U, m)


def wt_smithy_in(d, ys, U, m):
    """Smithy / armoury: u = 0 next to the door (z 14), u = 8 at the far end; ladder at (8, 12), chimney in the
    back wall at u = 6."""
    pk, w = d.pack, WOOD[d.pack]
    if pk == "Neoterra":         # armoury: rifle racks, ammo lockers, cleaning bench
        g = [(1, 12, SST, ROD()), (2, 12, SST, ROD()), (3, 12, SST, ROD()), (4, 12, LOCK), (5, 12, LOCK),
             (1, 17, LOCK), (2, 17, LOCK), (3, 17, SST, "black_stained_glass_pane"), (4, 17, ST("birch", "south")),
             (6, 17, "grindstone[face=floor,facing=east]"), (7, 17, LOCK), (8, 17, "potted_bamboo"),
             (5, 15, "yellow_carpet"), (6, 15, "yellow_carpet"), ("lamp", 3, 14), ("lamp", 6, 14)]
    else:                        # forge under the chimney, anvil + quench in front, tool wall, coal store
        stone = "polished_andesite" if pk == "Hearthwood" else "cobblestone"
        g = [(6, 17, FIRE("north")), (5, 17, f"blast_furnace[facing=north,lit=true]"), (7, 17, stone),
             (6, 15, "anvil[facing=east]"), (5, 15, "water_cauldron[level=3]"), (3, 17, "grindstone[face=floor,facing=east]"),
             (1, 12, SLD(w), ROD()), (2, 12, SLD(w), CHAIN), (3, 12, SLD(w), ROD()), (4, 12, "smithing_table"),
             (5, 12, CH("south")), (8, 17, "black_wool"), (8, 16, "coal_block"), (1, 17, BAR),
             (2, 15, "crafting_table"), ("lamp", 4, 14), ("lamp", 6, 13)]
    lay(d, ys[0], g, U, m)
    y = ys[1]
    if pk == "Neoterra":         # equipment store: shelving bays of crates
        g = [(1, 12, BAR, BAR), (2, 12, BAR, BAR), (3, 12, BAR), (5, 12, LOCK, LOCK), (6, 12, LOCK),
             (1, 17, "white_wool", "white_wool"), (2, 17, "light_gray_wool"), (4, 17, BAR, LOCK), (5, 17, BAR),
             (7, 17, "potted_bamboo"), (3, 15, BAR), (4, 15, BAR), ("lamp", 2, 14), ("lamp", 6, 14)]
    else:                        # armoury loft: weapon racks, shields (banners), chests, practice dummy
        col = "red" if pk == "Hearthwood" else "green"
        g = [(1, 12, SLD(w), ROD()), (2, 12, SLD(w), ROD()), (3, 12, SLD(w), ROD()), (5, 12, CH("south")),
             (6, 12, CH("south")), (1, 17, CH("north")), (3, 17, SLD(w), POTD), (4, 17, "grindstone[face=floor,facing=east]"),
             (7, 17, "hay_block[axis=y]", f"carved_pumpkin[facing=west]"), ("lamp", 3, 14), ("lamp", 6, 14),
             (2, 14, f"{col}_carpet"), (3, 14, f"{col}_carpet")]
        for u, z, f in ((2, 13, "south"), (4, 16, "north")):
            pass
    lay(d, y, g, U, m)


def wt_hall_in(d, ys, cx):
    """Long hall across the back: x cx-8..cx+8, z 22..26, door at (cx, 22) in the north wall, ladder at (cx+8, 26)."""
    pk, w = d.pack, WOOD[d.pack]
    a = cx - 8
    if pk == "Hearthwood":
        floors = [
            # granary store: barrel bays on the south wall, sack piles, a weighing table
            [(a, 26, BAR, BAR), (a + 1, 26, BAR, BAR), (a + 2, 26, BAR), (a + 4, 26, "white_wool", "white_wool"),
             (a + 5, 26, "white_wool"), (a + 6, 26, "brown_wool"), (a + 8, 26, BAR, BAR), (a + 9, 26, BAR),
             (a + 11, 26, "hay_block[axis=y]", "hay_block[axis=y]"), (a + 12, 26, "hay_block[axis=x]"),
             (a + 14, 26, CH("north")), (a, 22, "hay_block[axis=y]"), (a + 2, 22, "composter[level=4]"),
             (a + 12, 22, SLD(w), POTD), (a + 13, 22, SLD(w), "flower_pot"), (a + 15, 22, BAR),
             (a + 6, 24, SLD(w), CAN1), (a + 7, 24, SLD(w)), ("lamp", a + 3, 24), ("lamp", a + 11, 24)],
            # linen and provisions store
            [(a, 26, CH("north")), (a + 1, 26, CH("north")), (a + 3, 26, "white_wool", "white_wool"),
             (a + 4, 26, "light_gray_wool"), (a + 6, 26, BAR, BAR), (a + 7, 26, BAR, BAR), (a + 10, 26, KEG("north")),
             (a + 11, 26, KEG("north"), KEG("north")), (a + 13, 26, "hay_block[axis=y]"), (a, 22, BAR),
             (a + 5, 22, SLD(w), CAN3), (a + 9, 22, "smoker[facing=south,lit=false]"), (a + 10, 22, SLD(w), POTD),
             ("lamp", a + 4, 24), ("lamp", a + 12, 24)],
            # quartermaster's office
            [(a, 26, BOOK("north")), (a + 1, 26, BOOK("north")), (a + 2, 26, BOOK("north")),
             (a + 3, 26, "lectern[facing=north,has_book=false,powered=false]"), (a + 6, 24, SLD(w), CAN3),
             (a + 7, 24, SLD(w), "flower_pot"), (a + 6, 25, ST(w, "south")), (a + 10, 22, "cartography_table"),
             (a + 11, 22, CH("south")), (a + 13, 26, "bed" if False else SLD(w), "potted_red_tulip"),
             ("bed", a + 14, 26, "south", "red"),
             (a + 5, 23, "red_carpet"), (a + 6, 23, "red_carpet"), (a + 7, 23, "red_carpet"), ("lamp", a + 6, 23)]]
    elif pk == "Cascadia":
        floors = [
            # stable: four stalls along the south wall, tack along the north wall
            [(a + 1, 26, "hay_block[axis=y]"), (a + 2, 26, "water_cauldron[level=3]"), (a + 3, 26, "spruce_fence"),
             (a + 3, 25, "spruce_fence"), (a + 4, 26, "hay_block[axis=y]"), (a + 5, 26, "water_cauldron[level=3]"),
             (a + 6, 26, "spruce_fence"), (a + 6, 25, "spruce_fence"), (a + 9, 26, "hay_block[axis=y]"),
             (a + 10, 26, "water_cauldron[level=3]"), (a + 11, 26, "spruce_fence"), (a + 11, 25, "spruce_fence"),
             (a + 12, 26, "hay_block[axis=y]"), (a + 13, 26, "water_cauldron[level=3]"),
             (a, 22, BAR), (a + 1, 22, SLD(w), "brown_carpet"), (a + 2, 22, SLD(w), "brown_carpet"),
             (a + 5, 22, CH("south")), (a + 11, 22, "hay_block[axis=x]"), (a + 12, 22, "hay_block[axis=x]"),
             ("lamp", a + 4, 24), ("lamp", a + 11, 24)],
            # hay loft
            [(a, 26, "hay_block[axis=y]", "hay_block[axis=y]"), (a + 1, 26, "hay_block[axis=y]", "hay_block[axis=y]"),
             (a + 2, 26, "hay_block[axis=x]"), (a + 4, 26, "hay_block[axis=y]", "hay_block[axis=y]"),
             (a + 5, 26, "hay_block[axis=y]"), (a + 9, 26, "hay_block[axis=x]", "hay_block[axis=x]"),
             (a + 10, 26, "hay_block[axis=x]"), (a + 12, 26, BAR), (a, 22, "composter[level=6]"),
             (a + 3, 22, "white_wool"), (a + 4, 22, "brown_wool"), ("lamp", a + 6, 24)],
            # hands' bunkroom
            [("bed", a + 1, 26, "south", "brown"), ("bed", a + 3, 26, "south", "brown"), ("bed", a + 5, 26, "south", "brown"),
             (a + 2, 26, SLD(w), CAN1), (a + 4, 26, SLD(w), CAN1), (a + 9, 26, CH("north")), (a + 10, 26, CH("north")),
             (a + 12, 24, "spruce_fence", "spruce_pressure_plate[powered=false]"), (a + 11, 24, ST(w, "east")),
             (a + 13, 24, ST(w, "west")), (a, 22, "potted_fern"), (a + 6, 22, "water_cauldron[level=3]"),
             ("lamp", a + 4, 24), ("lamp", a + 12, 23)]]
    else:
        floors = [
            # dorm floor A: pods along the south wall
            [("bed", a + 1, 26, "south", "cyan"), ("bed", a + 3, 26, "south", "cyan"), ("bed", a + 5, 26, "south", "cyan"),
             ("bed", a + 9, 26, "south", "cyan"), ("bed", a + 11, 26, "south", "cyan"), (a + 2, 26, LOCK),
             (a + 4, 26, LOCK), (a + 10, 26, LOCK), (a + 12, 26, LOCK), (a, 22, "potted_bamboo"),
             (a + 3, 22, LOCK), (a + 12, 22, LOCK), ("lamp", a + 4, 24), ("lamp", a + 11, 24)],
            # dorm floor B with a lounge corner
            [("bed", a + 1, 26, "south", "light_gray"), ("bed", a + 3, 26, "south", "light_gray"),
             ("bed", a + 5, 26, "south", "light_gray"), (a + 2, 26, LOCK), (a + 4, 26, LOCK),
             (a + 10, 22, "birch_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]"),
             (a + 11, 22, "birch_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]"),
             (a + 10, 23, "birch_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]"),
             (a + 13, 22, "potted_bamboo"), ("lamp", a + 4, 24), ("lamp", a + 11, 24)],
            # command office
            [(a + 2, 22, SST, "black_stained_glass_pane"), (a + 3, 22, SST), (a + 2, 23, ST("birch", "south")),
             (a + 6, 22, SST, "black_stained_glass_pane"), (a + 7, 22, SST), (a + 6, 23, ST("birch", "south")),
             (a + 11, 25, SST), (a + 12, 25, SST), (a + 11, 24, ST("birch", "north")), (a + 12, 24, ST("birch", "north")),
             (a, 26, LOCK), (a + 1, 26, LOCK), (a + 4, 26, "potted_bamboo"), ("lamp", a + 4, 24), ("lamp", a + 11, 23)],
            # canteen
            [(a, 26, "smoker[facing=north,lit=false]"), (a + 1, 26, "water_cauldron[level=3]"), (a + 2, 26, SST, POTD),
             (a + 3, 26, "white_shulker_box[facing=up]"), (a + 6, 24, SST, "flower_pot"), (a + 5, 24, ST("birch", "west")),
             (a + 7, 24, ST("birch", "east")), (a + 11, 24, SST, "potted_cactus"), (a + 10, 24, ST("birch", "west")),
             (a + 12, 24, ST("birch", "east")), (a + 14, 22, "potted_bamboo"), ("lamp", a + 6, 23), ("lamp", a + 11, 23)]]
    for y, g in zip(ys, floors):
        lay(d, y, g)


# ---- gatehouse: guard barracks west of the road, armoury / stable east --------------------------------------
def gh_barracks_in(d, ys, x1, x2, tz):
    """Interior x x1..x2 (x1 = ladder side), z tz+4..tz+9; ladder at (x1, tz+4); door from the east at (x2, tz+8);
    chimney (Hearthwood / Cascadia) in the south wall at x1+2."""
    pk, w = d.pack, WOOD[d.pack]
    a, n, s = x1, tz + 4, tz + 9          # west x, north row, south row
    if pk == "Hearthwood":       # guards' hall: fireside, long table, kegs, dresser
        g = [(a + 2, s, FIRE("north")), (a + 1, s, "bricks"), (a + 3, s, "bricks"), (a + 1, s - 2, ST(w, "west")),
             (a + 3, s - 2, ST(w, "east")), (a + 5, n + 2, "stripped_dark_oak_wood[axis=x]", CAN3),
             (a + 6, n + 2, "stripped_dark_oak_wood[axis=x]"), (a + 7, n + 2, "stripped_dark_oak_wood[axis=x]", CAN1),
             (a + 5, n + 1, ST(w, "north")), (a + 6, n + 1, ST(w, "north")), (a + 7, n + 1, ST(w, "north")),
             (a + 5, n + 3, ST(w, "south")), (a + 6, n + 3, ST(w, "south")), (a + 7, n + 3, ST(w, "south")),
             (a + 4, n, "smoker[facing=south,lit=true]"), (a + 5, n, "water_cauldron[level=3]"),
             (a + 7, n, SLD(w), POTD), (a + 8, n, SLD(w), "flower_pot"), (a + 5, s, KEG("north")),
             (a + 6, s, KEG("north"), KEG("north")), (a + 7, s, BAR), ("lamp", a + 6, n + 2), ("lamp", a + 2, s - 2)]
        up = [("bed", a + 3, s, "south", "red"), ("bed", a + 5, s, "south", "red"), ("bed", a + 7, s, "south", "red"),
              (a + 4, s, SLD(w), CAN1), (a + 6, s, SLD(w), CAN1), (a + 3, n, CH("south")), (a + 5, n, CH("south")),
              (a + 7, n, BOOK("south")), (a + 8, n, "potted_red_tulip"), (a + 4, n + 2, "red_carpet"),
              (a + 5, n + 2, "red_carpet"), (a + 6, n + 2, "red_carpet"), ("lamp", a + 5, n + 2)]
    elif pk == "Cascadia":       # mess cabin: stove, table along the room, kegs, gun rack
        g = [(a + 2, s, "furnace[facing=north,lit=true]"), (a + 1, s, LOG("spruce_log", "x")),
             (a + 3, s, "water_cauldron[level=3]"), (a + 5, n + 1, "stripped_spruce_wood[axis=z]", CAN3),
             (a + 5, n + 2, "stripped_spruce_wood[axis=z]"), (a + 5, n + 3, "stripped_spruce_wood[axis=z]", CAN1),
             (a + 4, n + 1, ST(w, "east")), (a + 4, n + 2, ST(w, "east")), (a + 4, n + 3, ST(w, "east")),
             (a + 6, n + 1, ST(w, "west")), (a + 6, n + 2, ST(w, "west")), (a + 6, n + 3, ST(w, "west")),
             (a + 8, n, KEG("south")), (a + 9, n, KEG("south"), KEG("south")), (a + 3, n, SLD(w), ROD()),
             (a + 4, n, SLD(w), ROD()), (a + 6, s, SLD(w), POTD), (a + 9, s - 2, "potted_fern"),
             ("lamp", a + 5, n + 2), ("lamp", a + 2, s - 1)]
        up = [("bed", a + 3, n, "north", "brown"), ("bed", a + 5, n, "north", "brown"), ("bed", a + 7, n, "north", "brown"),
              (a + 4, n, SLD(w), CAN1), (a + 6, n, SLD(w), CAN1), (a + 3, s, CH("north")), (a + 5, s, CH("north")),
              (a + 7, s, "water_cauldron[level=3]"), (a + 9, s, BAR), (a + 5, n + 3, "green_carpet"),
              (a + 6, n + 3, "green_carpet"), ("lamp", a + 5, n + 3)]
    else:                        # crew lounge: kitchenette on the north wall, sofa and media wall, dining table
        g = [(a + 3, n, "smoker[facing=south,lit=false]"), (a + 4, n, "water_cauldron[level=3]"), (a + 5, n, SST, POTD),
             (a + 6, n, "white_shulker_box[facing=up]"), (a + 2, s, ST("birch", "south")), (a + 3, s, ST("birch", "south")),
             (a + 4, s, ST("birch", "south")), (a + 3, s - 1, "birch_trapdoor[facing=north,half=top,open=false,"
                                                              "powered=false,waterlogged=false]"),
             (a + 1, s - 2, "black_concrete"), (a + 8, n + 2, SST, "potted_cactus"), (a + 8, n + 1, ST("birch", "south")),
             (a + 8, n + 3, ST("birch", "north")), (a + 10, n, LOCK), (a + 1, n + 1, "potted_bamboo"),
             ("lamp", a + 4, n + 2), ("lamp", a + 8, n + 2)]
        up = [("bed", a, n + 2, "west", "cyan"), ("bed", a, n + 4, "west", "cyan"), ("bed", a + 11, n + 1, "east", "cyan"),
              ("bed", a + 11, n + 3, "east", "cyan"), (a, n + 3, LOCK), (a + 11, n + 2, LOCK), (a + 4, n, SST, "potted_bamboo"),
              (a + 6, n, LOCK), (a + 4, s, LOCK), (a + 5, s, LOCK), (a + 5, n + 2, "cyan_carpet"),
              (a + 6, n + 2, "cyan_carpet"), ("lamp", a + 5, n + 2)]
    lay(d, ys[0], g)
    lay(d, ys[1], up)


def gh_east_in(d, y, x1, x2, tz):
    """East building: interior x x1..x2 (x1 by the west door at z tz+8), z tz+4..tz+9."""
    pk, w = d.pack, WOOD[d.pack]
    a, n, s = x1, tz + 4, tz + 9
    if pk == "Hearthwood":       # armoury with brick vault: racks north, mail chests south, practice dummy
        g = [(a + 2, n, SLD(w), ROD()), (a + 3, n, SLD(w), ROD()), (a + 4, n, SLD(w), ROD()), (a + 6, n, CH("south")),
             (a + 7, n, SLD(w), ROD()), (a + 8, n, SLD(w), ROD()), (a + 10, n, "grindstone[face=floor,facing=east]"),
             (a + 3, s, CH("north")), (a + 4, s, CH("north")), (a + 6, s, SLD(w), POTD), (a + 9, s, BAR),
             (a + 10, s, "anvil[facing=east]"), (a + 7, n + 2, "oak_fence"), ("lamp", a + 4, n + 2), ("lamp", a + 8, n + 3)]
        lay(d, y, g)
        put(d, a + 7, y + 1, n + 2, "hay_block[axis=y]")
        put(d, a + 7, y + 2, n + 2, "carved_pumpkin[facing=west]")
        for x in (a + 2, a + 5, a + 9):
            put(d, x, y + 2, n, "red_wall_banner[facing=south]")
    elif pk == "Cascadia":       # stable: three stalls on the north wall, tack and feed on the south wall
        g = [(a + 2, n, "hay_block[axis=y]"), (a + 3, n, "water_cauldron[level=3]"), (a + 4, n, "spruce_fence"),
             (a + 4, n + 1, "spruce_fence"), (a + 5, n, "hay_block[axis=y]"), (a + 6, n, "water_cauldron[level=3]"),
             (a + 7, n, "spruce_fence"), (a + 7, n + 1, "spruce_fence"), (a + 8, n, "hay_block[axis=y]"),
             (a + 9, n, "water_cauldron[level=3]"), (a + 2, s, BAR), (a + 3, s, SLD(w), "brown_carpet"),
             (a + 4, s, SLD(w), "brown_carpet"), (a + 6, s, CH("north")), (a + 8, s, "hay_block[axis=x]"),
             (a + 9, s, "hay_block[axis=x]", "hay_block[axis=y]"), ("lamp", a + 4, n + 3), ("lamp", a + 8, n + 3)]
        lay(d, y, g)
    else:                        # armoury: rifle racks, lockers, briefing screen
        g = [(a + 2, n, SST, ROD()), (a + 3, n, SST, ROD()), (a + 4, n, SST, ROD()), (a + 6, n, LOCK),
             (a + 7, n, LOCK), (a + 9, n, SST, ROD()), (a + 10, n, SST, ROD()), (a + 3, s, LOCK), (a + 4, s, LOCK),
             (a + 6, s, SST, "black_stained_glass_pane"), (a + 7, s, SST), (a + 6, s - 1, ST("birch", "south")),
             (a + 10, s, "grindstone[face=floor,facing=east]"), (a + 9, n + 2, "orange_carpet"),
             (a + 8, n + 2, "orange_carpet"), ("lamp", a + 4, n + 2), ("lamp", a + 8, n + 3)]
        lay(d, y, g)


def wt_complex(d, L, cx, tz, yw, mirror=False):
    """Town-side growth of a wall tower: stair to the wall walk (L2), guardhouse (L3), smithy / armoury (L4),
    stable / store hall (L5), with paths, lamps, benches and gardens. tz = tower door z (south wall), yw = wall
    walk standing level."""
    pk = d.pack
    s_ = -1 if mirror else 1
    pave = {"Hearthwood": "gravel", "Cascadia": "dirt_path", "Neoterra": "polished_andesite"}[pk]
    border = {"Hearthwood": "cobblestone", "Cascadia": "rooted_dirt", "Neoterra": "light_gray_concrete"}[pk]
    zend = 20 if L < 5 else 28
    for z in range(tz + 1, zend + 1):
        for x in (cx - 1, cx, cx + 1):
            d.set(x, 1, z, pave)
        for x in (cx - 2, cx + 2):
            d.set(x, 1, z, border)
    # stair up to the wall walk, west of the tower, along the wall's town face
    n = yw - 2
    for i in range(n):
        x = cx - 5 - i
        f = "west"
        mat = {"Hearthwood": "stone_brick", "Cascadia": "spruce", "Neoterra": "smooth_quartz"}[pk]
        sup = {"Hearthwood": "stone_bricks", "Cascadia": "spruce_planks", "Neoterra": "white_concrete"}[pk]
        if L >= 2:
            d.set(x, 2 + i, 7, ST(mat, f))
            for y in range(2, 2 + i):
                d.set(x, y, 7, sup)
    lamp_post(d, cx - 3, tz + 2)
    lamp_post(d, cx + 3, tz + 2)
    if L >= 2:
        bench(d, cx - 3, tz + 8, "west", along="z")
        # store shed against the wall east of the tower
        ys, top, ridge = bld(d, cx + 5, 7, cx + 10, 10, 1, "x", doors=[(cx + 5, 9)], sh=4, pal=PAL[("wt", pk, "shed")])
        wt_shed_in(d, cx)
        for k in range(3):                                   # log / crate pile beside the shed
            put(d, cx + 11, 2, 8 + k, LOG("spruce_log" if pk != "Neoterra" else "white_concrete", "z")
                if pk != "Neoterra" else "barrel[facing=up,open=false]")
            put(d, cx + 11, 3, 8 + k, LOG("spruce_log", "z") if pk != "Neoterra" else AIR) if k < 2 and pk != "Neoterra" else None
        lamp_post(d, cx - 6, tz + 6)
        if pk == "Cascadia" and L < 4:                       # outhouse / tool hut (smithy takes the spot at L4)
            sentry_box(d, cx - 12, 9, "east")
        if pk == "Cascadia" and L >= 3:                      # firepit with log benches and a porch roof
            put(d, 2, 2, 21, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
            for x, z, a in ((1, 21, "z"), (3, 21, "z"), (2, 20, "x"), (2, 22, "x")):
                put(d, x, 2, z, LOG("stripped_spruce_log", a))
            for z in range(12, 17):
                put(d, 9, 6, z, SL("mangrove"))
                put(d, 10, 6, z, SL("mangrove"))
            for z in (12, 16):
                for y in range(2, 6):
                    put(d, 9, y, z, LOG("spruce_log"))
        if pk == "Cascadia":                                 # chopping block and water barrels by the shed
            put(d, cx + 12, 2, 8, LOG("stripped_spruce_log"))
            put(d, cx + 12, 3, 8, "lightning_rod[facing=up,powered=false,waterlogged=false]")
            put(d, cx + 13, 2, 9, BAR)
            put(d, cx + 13, 2, 10, BAR)
            put(d, cx + 13, 3, 10, KEG("north"))
            lamp_post(d, cx + 13, 13)
        if pk == "Cascadia":                                 # hitching rail and water trough by the door
            for x in range(cx + 3, cx + 7):
                put(d, x, 2, tz + 9, "spruce_fence")
            put(d, cx + 3, 3, tz + 9, LANT_S)
            put(d, cx + 4, 2, tz + 10, "water_cauldron[level=3]")
            put(d, cx + 5, 2, tz + 10, "hay_block[axis=x]")
            put(d, cx + 6, 2, tz + 10, "hay_block[axis=x]")
            put(d, cx + 6, 3, tz + 10, "hay_block[axis=y]")
        hedge(d, [(cx - 2, z) for z in range(tz + 6, tz + 8)] + [(cx + 2, z) for z in range(tz + 6, tz + 8)])
        put(d, cx - 4, 2, tz + 3, "barrel[facing=up,open=false]")
        put(d, cx - 4, 3, tz + 3, "barrel[facing=north,open=false]")
        put(d, cx - 4, 2, tz + 4, "barrel[facing=up,open=false]")
    # ---- L3: guardhouse (mess below, bunk / office room above)
    if L >= 3:
        ax1, ax2 = sorted((cx - s_ * 15, cx - s_ * 5))
        inner = cx - s_ * 5
        outer_i = ax1 + 1 if s_ == 1 else ax2 - 1
        lf = "east" if s_ == 1 else "west"
        ng = 1 if L == 3 else 2
        ys, top, ridge = bld(d, ax1, 11, ax2, 18, ng, "x", doors=[(inner, 14)], pal=PAL[("wt", pk, "a")],
                             lad=(outer_i, 17, lf) if ng > 1 else None,
                             chimney=(ax1 + 3 if s_ == 1 else ax2 - 3, 18) if pk != "Neoterra" else None)
        wt_guard_in(d, L, ys, lambda u: outer_i + s_ * u, mirror, ng)
        sign_x = inner + s_ * 1
        d.sign(sign_x, 4, 13, "east" if s_ == 1 else "west",
               {"Hearthwood": ["GUARD", "HOUSE"], "Cascadia": ["MESS", "CABIN"], "Neoterra": ["CREW", "ROOM"]}[pk],
               WOOD[pk], glow=pk == "Neoterra", color="cyan" if pk == "Neoterra" else "black") \
            if d.air(sign_x, 4, 13) else None
        for z in (13, 16):
            for x in range(min(inner + s_, cx - s_ * 2), max(inner + s_, cx - s_ * 2) + 1):
                pass
        for z in (12, 15, 18):
            put(d, inner + s_, 2, z, "barrel[facing=up,open=false]") if z != 14 else None
        flowers(d, [(x, 20) for x in range(min(ax1, ax2), max(ax1, ax2) - 3)])
        for wx in (ax1 + 3, ax1 + 6):                          # the two south windows of the guardhouse
            if pk == "Hearthwood":
                put(d, wx, 2, 19, TD("mangrove", "south", "top"))
                put(d, wx, 3, 19, "potted_red_tulip" if wx == ax1 + 3 else "potted_blue_orchid")
            elif pk == "Cascadia":
                put(d, wx - 1, 4, 19, TD("spruce", "south", "bottom", "true"))
                put(d, wx + 1, 4, 19, TD("spruce", "south", "bottom", "true"))
                put(d, wx, 2, 19, "spruce_fence")
                put(d, wx, 3, 19, "potted_fern")
            else:
                put(d, wx, 2, 19, "polished_andesite")
                put(d, wx, 3, 19, "potted_bamboo")
        gx2 = inner + s_                                      # porch corner outside the door
        put(d, gx2, 2, 16, ST(WOOD[pk], "south"))
        put(d, gx2, 2, 17, ST(WOOD[pk], "south"))
        put(d, gx2, 4, 15, LANT_S) if pk != "Neoterra" else put(d, gx2, 4, 15, "lantern[hanging=false,waterlogged=false]")
        px = inner + 2 * s_                                   # lean-to porch over the door
        for z in range(12, 17):
            for x in (inner + s_, px):
                put(d, x, 5, z, SL(WOOD[pk]) if pk != "Neoterra" else "smooth_stone_slab[type=bottom,waterlogged=false]")
        for z in (12, 16):
            for y in (2, 3, 4):
                put(d, px, y, z, LOG(LOGW[pk]) if pk != "Neoterra" else "light_gray_concrete")
        for z in (13, 15):
            put(d, px, 2, z, WOOD[pk] + "_fence")
    # ---- L4: smithy / armoury on the other side, well and cart
    if L >= 4:
        bx1, bx2 = sorted((cx + s_ * 5, cx + s_ * 15))
        inner = cx + s_ * 5
        kind = {"Hearthwood": "smithy", "Cascadia": "smithy", "Neoterra": "armoury"}[pk]
        louter = bx2 - 1 if s_ == 1 else bx1 + 1
        ys, top, ridge = bld(d, bx1, 11, bx2, 18, 2, "x", doors=[(inner, 14)], pal=PAL[("wt", pk, "b")], lad=(louter, 12, "west" if s_ == 1 else "east"),
                             chimney=(bx2 - 3 if s_ == 1 else bx1 + 3, 18) if pk != "Neoterra" else None)
        wt_smithy_in(d, ys, lambda u: inner + s_ * (u + 1), mirror)
        # open-fronted forge lean-to on the yard side
        cart(d, cx + s_ * 7, 20, "x")
        hedge(d, [(x, 20) for x in range(min(bx1, bx2) + 6, max(bx1, bx2) + 1)])
        tree(d, cx + s_ * 13, 22 if L < 5 else 9 + 0, 4) if L < 5 else None
    if L >= 2 and pk == "Cascadia":                          # hay and barrels by the shed
        for z in (11, 12):
            put(d, cx + 11, 2, z, "hay_block[axis=y]")
            put(d, cx + 12, 2, z, "barrel[facing=up,open=false]")
        put(d, cx + 11, 3, 11, "hay_block[axis=y]")
        put(d, cx + 12, 3, 11, "barrel[facing=north,open=false]")
    if L >= 3:
        flowers(d, [(x, z) for x in range(cx + 3, cx + 4 + 1) for z in range(19, 20 + 1)]) if L < 4 else None
        lamp_post(d, cx - 3, 10 + 9)
        stall(d, cx - 2 - 3 * s_ if False else cx + 3, 23, {"Hearthwood": "red", "Cascadia": "green",
                                                           "Neoterra": "cyan"}[pk],
              ("pumpkin", "barrel[facing=up,open=false]", "melon")) if L < 5 else None
        cart(d, cx - 4, 22, "x") if L < 5 else None
        lamp_post(d, cx + 7, 22) if L < 5 else None
    if L >= 4:                                               # well / fountain in the yard
        wx = cx + 4
        for x in range(wx, wx + 3):
            for z in range(21 if L < 5 else 9, 24 if L < 5 else 9):
                pass
    if L >= 3:                                               # weapon rack and water butt by the guardhouse door
        gx = cx - s_ * 4
        for z in (12, 13):
            put(d, gx, 2, z, SL(WOOD[pk], "top") if pk != "Neoterra" else "smooth_stone_slab[type=top,waterlogged=false]")
            put(d, gx, 3, z, ROD())
        put(d, gx, 2, 16, "water_cauldron[level=3]")
        put(d, gx, 2, 17, "barrel[facing=up,open=false]")
    if L >= 4 and pk == "Neoterra":                          # bike shelter and bollards along the path
        for x in range(cx - 8, cx - 4):
            put(d, x, 2, 20, "iron_bars")
            put(d, x, 4, 19, "smooth_stone_slab[type=top,waterlogged=false]")
            put(d, x, 4, 20, "smooth_stone_slab[type=top,waterlogged=false]")
            put(d, x, 4, 21, "smooth_stone_slab[type=top,waterlogged=false]")
        for x in (cx - 8, cx - 5):
            put(d, x, 2, 21, "light_gray_concrete")
            put(d, x, 3, 21, "light_gray_concrete")
        flowers(d, [(x, z) for x in range(cx - 14, cx - 10 + 1) for z in range(19, 20 + 1)])
        flowers(d, [(x, z) for x in range(cx + 10, cx + 14 + 1) for z in range(19, 20 + 1)])
        tree(d, cx - 12, 22, 4)
    if L >= 5 and pk == "Neoterra":                          # plaza fountain, solar field on the long hall
        roof_units(d, [(cx - 7, 26), (cx - 6, 26), (cx + 4, 22)], 18)
        for x in (cx - 7, cx - 5, cx - 3, cx - 1, cx + 1, cx + 3, cx + 5):
            for z in (23, 25):
                put(d, x, 18, z, "daylight_detector[inverted=false,power=0]")
    if L >= 4:
        bench(d, cx - 2, 9 + 0, "north") if False else None
        lamp_post(d, cx + 4, 12)
        lamp_post(d, cx - 4, 12) if pk != "Cascadia" else None
        if pk == "Neoterra":
            bx1 = min(cx + s_ * 5, cx + s_ * 15)
            roof_units(d, [(bx1 + 3, 14), (bx1 + 4, 14), (bx1 + 7, 15)], 11)
    if L >= 5:
        flowers(d, [(x, z) for x in range(cx - 8, cx - 5 + 1) for z in range(20, 20 + 1)])
        flowers(d, [(x, z) for x in range(cx + 5, cx + 8 + 1) for z in range(20, 20 + 1)])
        if pk == "Neoterra":
            roof_units(d, [(cx - 6, 24), (cx - 5, 24), (cx + 4, 24)], 16)
    if L >= 5 and pk == "Hearthwood":                        # orchard trees beside the hall
        tree(d, cx + 12, 20, 4)
        tree(d, cx + 14, 27, 4)
    if L >= 5:
        gx = cx - 15                                          # kitchen garden west of the long hall
        fence = {"Hearthwood": "oak_fence", "Cascadia": "spruce_fence", "Neoterra": "birch_fence"}[pk]
        for x in range(gx, gx + 5):
            put(d, x, 2, 20, fence)
            put(d, x, 2, 28, fence)
        for z in range(21, 28):
            put(d, gx, 2, z, fence)
            put(d, gx + 4, 2, z, fence) if z != 24 else None
        crops = {"Hearthwood": ("carrots[age=7]", "potatoes[age=7]", "wheat[age=7]"),
                 "Cascadia": ("potatoes[age=7]", "beetroots[age=3]", "carrots[age=7]"),
                 "Neoterra": ("wheat[age=7]", "carrots[age=7]", "beetroots[age=3]")}[pk]
        for i, z in enumerate((21, 22, 23, 25, 26, 27)):
            for x in (gx + 1, gx + 2, gx + 3):
                d.set(x, 1, z, "farmland[moisture=7]")
                put(d, x, 2, z, crops[i % 3])
        for x in (gx + 1, gx + 2, gx + 3):
            d.set(x, 1, 24, "water")
        put(d, gx + 2, 2, 24, "oak_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]")
        put(d, gx + 4, 2, 24, fence.replace("_fence", "_fence_gate") + "[facing=east,in_wall=false,open=false,powered=false]")
        put(d, gx, 3, 20, LANT_S)
        put(d, gx + 4, 3, 28, LANT_S)
        for wx in (cx - 6, cx - 3, cx + 3, cx + 6):           # boxes under the hall's front windows
            if pk == "Hearthwood":
                put(d, wx, 2, 20, TD("bamboo", "north", "top"))
                put(d, wx, 3, 20, "potted_poppy")
            elif pk == "Cascadia":
                put(d, wx - 1, 4, 20, TD("spruce", "north", "bottom", "true"))
                put(d, wx + 1, 4, 20, TD("spruce", "north", "bottom", "true"))
            else:
                put(d, wx, 2, 20, "polished_andesite")
                put(d, wx, 3, 20, "potted_bamboo")
    # ---- L5: flanking turrets at both wall ends
    if L >= 5:
        for ex in (cx - 15, cx + 11):
            for x in range(ex, ex + 5):
                for z in range(2, 8):
                    edge = x in (ex, ex + 4) or z in (2, 7)
                    for y in range(2, yw + 2):
                        if pk == "Hearthwood":
                            b = stone_mix(x, y, z) if edge else (stone_mix(x, y, z) if y == yw - 1 else AIR)
                        elif pk == "Cascadia":
                            b = (LOG("spruce_log") if x in (ex, ex + 4) and z in (2, 7) else
                                 LOG("stripped_spruce_log", "x" if z in (2, 7) else "z")) if edge else \
                                ("spruce_planks" if y == yw - 1 else AIR)
                        else:
                            b = ("light_gray_concrete" if y % 3 == 0 else "white_concrete") if edge else \
                                ("smooth_stone" if y == yw - 1 else AIR)
                        if edge and y in (4, yw + 1) and (x == ex + 2 or z == 4):
                            b = "glass_pane" if pk != "Neoterra" else "light_blue_stained_glass_pane"
                        if not edge and y < yw - 1:
                            b = AIR
                        d.set(x, y, z, b)
                    if edge:
                        top_b = {"Hearthwood": stone_mix(x, yw + 2, z) if (x + z) % 2 == 0 else AIR,
                                 "Cascadia": "spruce_fence", "Neoterra": "smooth_quartz_slab[type=bottom,waterlogged=false]"}[pk]
                        d.set(x, yw + 2, z, top_b)
                # open the side facing the wall walk at walk level
                side = ex + 4 if ex < cx else ex
                for z in (4, 5, 6):
                    d.set(side, yw, z, AIR)
                    d.set(side, yw + 1, z, AIR)
            d.set(ex + 2, yw, 4, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]"
                  if pk != "Neoterra" else "sea_lantern")
            d.banner(ex + 2, yw + 1, 1, "north", {"Hearthwood": "red", "Cascadia": "green", "Neoterra": "cyan"}[pk]) \
                if d.air(ex + 2, yw + 1, 1) and pk != "Neoterra" else None
    # ---- L5: long hall across the back (stable / store / dorm), garden and trees
    if L >= 5:
        kind = {"Hearthwood": "store", "Cascadia": "stable", "Neoterra": "dorm"}[pk]
        n = 3 if pk != "Neoterra" else 4
        lad = (cx + 8, 26, "north")
        ys, top, ridge = bld(d, cx - 9, 21, cx + 9, 27, n, "x", doors=[(cx, 21)], lad=lad, sh=4, pal=PAL[("wt", pk, "c")])
        wt_hall_in(d, ys, cx)
        for x in (cx - 13, cx + 13):
            tree(d, x, 24, 5)
        flowers(d, [(x, z) for x in range(cx + 4 * s_ - 2, cx + 4 * s_ + 2 + 1) for z in range(19, 19 + 1)]) if False else None
        lamp_post(d, cx - 3, 19)
        lamp_post(d, cx + 3, 19)


def wt_hearthwood(rel, L):
    d = Shifted("Hearthwood", rel, (31, 30, 30), gy=1, paving="grass_block[snowy=false]", ox=8)
    x1, x2, z1, z2 = 4, 10, 2, 8
    wa, wb = WT_WALL[L]
    wa, wb = 7 + wa, 7 + wb
    # curtain wall: z3 parapet, z4..6 deck at y7
    for x in range(wa, wb + 1):
        if x1 <= x <= x2:
            continue
        for z in range(3, 7):
            d.set(x, 1, z, "cobblestone")
            for y in range(2, 8):
                d.set(x, y, z, stone_mix(x, y, z))
        d.set(x, 8, 3, stone_mix(x, 8, 3))
        if x % 2 == 0:
            d.set(x, 9, 3, stone_mix(x, 9, 3))
        if x in (wa, wb):
            for z in (4, 5, 6):
                d.set(x, 8, z, stone_mix(x, 8, z))
    top = 12 if L == 1 else 17
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            edge = x in (x1, x2) or z in (z1, z2)
            d.set(x, 1, z, "cobblestone" if edge else "spruce_planks")
            for y in range(2, top + 2):
                d.set(x, y, z, stone_mix(x, y, z) if edge else AIR)
            if edge and (x + z) % 2 == 0:
                d.set(x, top + 2, z, stone_mix(x, top + 2, z))
            for yy in (7, 12, 17):
                if yy <= top:
                    d.set(x, yy, z, ("polished_andesite" if edge else ("spruce_planks" if yy < top else "stone_bricks")))
    for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):     # quoins
        for y in range(2, top + 2, 2):
            d.set(x, y, z, "polished_andesite")
    d.door(7, 2, z2, "north", "dark_oak")
    d.set(7, 4, z2, "chiseled_stone_bricks")
    for x in (x1, x2):                                        # doors onto the wall walks
        d.door(x, 8, 5, "east" if x == x1 else "west", "dark_oak")
    for y in (4, 9):
        d.set(7, y, z1, "glass_pane")
        d.set(6, y + 1, z2, "glass_pane") if y == 9 else None
    if L >= 2:
        for x in (6, 8):
            d.window(x, 14, z1, x, 15, z1)
            d.window(x, 14, z2, x, 15, z2)
        d.window(x1, 14, 5, x1, 15, 5)
        d.window(x2, 14, 5, x2, 15, 5)
    ladder(d, 9, 3, 2, top, "south")
    # armoury
    d.hut(5, 2, 3)
    d.item(5, 2, 7, "barrel")
    nr = RACKS[L]
    for i in range(nr):
        d.rack(9, 2, 7 - i, "west")
    weapon_rack(d, [(5, 5), (5, 6)], 2, "dark_oak")
    d.set(7, 2, 5, "grindstone[face=floor,facing=north]")
    d.lamp(7, 6, 5)
    # bunks at wall-walk level
    for x in (5, 6):
        d.bed(x, 8, 3, "north", "red")
        d.bed(x, 8, 7, "south", "red")
    d.set(8, 8, 7, "chest[facing=north,type=single,waterlogged=false]")
    d.lamp(7, 11, 5)
    if L >= 2:                                                # lookout storey
        d.set(5, 13, 7, "chest[facing=north,type=single,waterlogged=false]")
        d.dining(6, 13, 5, 1, "x", "dark_oak", ("w", "e"), sit=False)
        d.set(5, 13, 3, "cartography_table")
        d.lamp(7, 16, 5)
        d.banner(5, 15, 7, "north", "red") if False else None
    if L >= 3:                                                # machicolations round the top
        for x in range(x1, x2 + 1):
            for z in (z1 - 1, z2 + 1):
                d.set(x, top, z, ST("stone_brick", "south" if z == z1 - 1 else "north", "top"))
                d.set(x, top + 1, z, stone_mix(x, top + 1, z))
                if x % 2 == 0:
                    d.set(x, top + 2, z, stone_mix(x, top + 2, z))
    if L >= 4:
        for y in range(top + 1, top + 6):
            d.set(7, y, 5, "dark_oak_fence")
        d.set(8, top + 5, 5, "red_wool")
        d.set(9, top + 5, 5, "red_wool")
        d.set(8, top + 4, 5, "white_wool")
    if L >= 5:
        d.banner(7, 10, z1 - 1, "north", "red") if d.air(7, 10, z1 - 1) else None
        for x in (2, 12):
            d.set(x, 8, 5, LANT_S)
        d.banner(7, 5, z2 + 1, "south", "red")
    wt_complex(d, L, 7, z2, 8)
    return d


def wt_cascadia(rel, L):
    d = Shifted("Cascadia", rel, (31, 24, 32), gy=1, paving="coarse_dirt", ox=9)
    wa, wb = {1: (-6, 6)}.get(L, WT_WALL[L])
    wa, wb = 6 + wa, 6 + wb
    # palisade z4 with a plank walk (deck y7) behind it
    for x in range(wa, wb + 1):
        if 2 <= x <= 10:
            continue
        for y in range(2, 9):
            d.set(x, y, 4, LOG("spruce_log"))
        d.set(x, 9, 4, "spruce_fence" if x % 2 else LOG("stripped_spruce_log"))
        d.set(x, 1, 4, rock(x, 1, 4))
        for z in (5, 6):
            d.set(x, 7, z, "spruce_planks")
        for y in range(2, 7):
            d.set(x, y, 6, "spruce_fence" if x % 3 == 0 else AIR)
    # blockhouse: river-rock ground storey 7x7, overhanging log storey 9x9
    gx1, gz1, gx2, gz2 = 3, 3, 9, 9
    for x in range(gx1, gx2 + 1):
        for z in range(gz1, gz2 + 1):
            edge = x in (gx1, gx2) or z in (gz1, gz2)
            d.set(x, 1, z, rock(x, 1, z) if edge else "spruce_planks")
            for y in range(2, 7):
                d.set(x, y, z, rock(x, y, z) if edge and y < 4 else (LOG("spruce_log", "x" if z in (gz1, gz2) else "z")
                                                                     if edge else AIR))
    d.fill(2, 7, 2, 10, 7, 10, "spruce_planks")
    ux1, uz1, ux2, uz2 = 2, 2, 10, 10
    for x in range(ux1, ux2 + 1):
        for z in range(uz1, uz2 + 1):
            if x in (ux1, ux2) or z in (uz1, uz2):
                corner = x in (ux1, ux2) and z in (uz1, uz2)
                d.set(x, 7, z, LOG("dark_oak_log", "x" if z in (uz1, uz2) else "z"))
                for y in range(8, 11):
                    d.set(x, y, z, LOG("spruce_log") if corner else LOG("stripped_spruce_log", "x" if z in (uz1, uz2) else "z"))
                d.set(x, 11, z, LOG("dark_oak_log", "x" if z in (uz1, uz2) else "z"))
    d.fill(ux1 + 1, 11, uz1 + 1, ux2 - 1, 11, uz2 - 1, "spruce_planks")
    ridge = d.hip(ux1, uz1, ux2, uz2, 12, "dark_oak_stairs", "dark_oak_slab", 1)
    for x, z in ((6, 2), (6, 10), (4, 2), (8, 2)):
        d.set(x, 9, z, "glass_pane")
    for x in (ux1, ux2):
        d.set(x, 9, 7, "glass_pane")
    d.door(6, 2, gz2, "north", "spruce")
    for x in (ux1, ux2):                                      # doors onto the firing walk
        d.door(x, 8, 5, "east" if x == ux1 else "west", "spruce")
    for x in (gx1, gx2):
        d.set(x, 4, 6, "spruce_fence")
    # central post + ladder
    for y in range(2, 11):
        d.set(6, y, 5, LOG("stripped_spruce_log"))
    ladder(d, 6, 4, 2, 7, "north")
    d.hut(4, 2, 4)
    d.item(8, 2, 4, "barrel")
    for i in range(RACKS[L]):
        d.rack(4, 2, 6 + i if i < 2 else 8, "east") if i < 2 else d.rack(8, 2, 8, "west")
    d.set(8, 2, 7, "chest[facing=west,type=single,waterlogged=false]")
    d.set(5, 5, 7, LANT)
    for x in (3, 9):
        d.bed(x, 8, 3, "west" if x == 3 else "east", "brown")
        d.bed(x, 8, 7, "west" if x == 3 else "east", "brown")
    d.set(3, 8, 9, "chest[facing=north,type=single,waterlogged=false]")
    d.set(5, 10, 7, LANT)
    if L >= 2:                                                # roof lookout with alarm bell
        for x, z in ((5, 5), (7, 5), (5, 7), (7, 7)):
            for y in range(ridge, ridge + 3):
                d.set(x, y, z, "spruce_fence")
        d.fill(5, ridge + 3, 5, 7, ridge + 3, 7, SL("dark_oak"))
        d.set(6, ridge + 2, 6, "bell[attachment=ceiling,facing=north,powered=false]")
        d.fill(5, ridge - 1, 5, 7, ridge - 1, 7, "spruce_planks")
        for x in range(5, 8):
            for z in range(5, 8):
                d.set(x, ridge, z, AIR) if (x, z) != (5, 5) and (x, z) != (7, 5) and (x, z) != (5, 7) and (x, z) != (7, 7) else None
    if L >= 3:                                                # lean-to porch over the door
        for x in range(4, 9):
            d.set(x, 5, 11, ST("spruce", "south"))
            d.set(x, 5, 10, SL("spruce"))
        for x in (4, 8):
            for y in (2, 3, 4):
                d.set(x, y, 11, LOG("spruce_log"))
        d.keg(9, 2, 11, "north") if False else None
        d.set(5, 2, 11, "spruce_log[axis=x]")
        d.set(5, 3, 11, AIR)
    if L >= 4:
        for x in (-2, 14):
            d.set(x, 8, 5, LANT_S)
    if L >= 5:
        for y in range(8, 13):
            d.set(-2, y, 6, "spruce_fence")
        d.set(-2, 12, 7, "green_wool")
        d.set(-2, 11, 7, "white_wool")
        for x in range(9, 12):
            d.set(x, 2, 11, LOG("spruce_log", "x"))
    wt_complex(d, L, 6, 9, 8, mirror=True)
    return d


def wt_neoterra(rel, L):
    d = Shifted("Neoterra", rel, (31, 26, 30), gy=1, paving="smooth_stone", ox=10)
    wa, wb = {3: (-15, 15)}.get(L, WT_WALL[L])
    wa, wb = 5 + wa, 5 + wb
    # security wall z4..6, walk deck at y8, glass parapet on the outside
    for x in range(wa, wb + 1):
        if 2 <= x <= 8:
            continue
        for z in range(4, 7):
            d.set(x, 1, z, "polished_andesite")
            for y in range(2, 9):
                d.set(x, y, z, "white_concrete" if z == 4 else "light_gray_concrete")
        d.set(x, 5, 4, "cyan_terracotta")
        d.set(x, 9, 4, "light_gray_stained_glass_pane")
        d.set(x, 9, 6, "iron_bars")
    x1, z1, x2, z2 = 2, 2, 8, 8
    top = 13
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            edge = x in (x1, x2) or z in (z1, z2)
            corner = x in (x1, x2) and z in (z1, z2)
            d.set(x, 1, z, "polished_diorite")
            for y in range(2, top):
                d.set(x, y, z, ("light_gray_concrete" if corner else "white_concrete") if edge else AIR)
            d.set(x, 8, z, "cyan_terracotta" if edge and not corner else "light_gray_concrete")
            d.set(x, top, z, "smooth_quartz")
    for a in (4, 5, 6):                                        # glazing
        for y in (3, 4, 5, 6):
            d.set(a, y, z1, "glass_pane")
        for y in (10, 11):
            d.set(a, y, z1, "light_gray_stained_glass_pane")
            d.set(a, y, z2, "light_gray_stained_glass_pane")
    d.door(5, 2, z2, "north", "birch")
    d.window(4, 2, z2, 4, 6, z2, "glass_pane")
    d.window(6, 2, z2, 6, 6, z2, "glass_pane")
    d.set(5, 4, z2, "glass")
    for x in (x1, x2):
        d.door(x, 9, 5, "east" if x == x1 else "west", "birch")
    # core + ladder
    for y in range(2, top):
        d.set(5, y, 5, "light_gray_concrete")
    yl = top if L == 1 else 18
    ladder(d, 5, 4, 2, yl, "north")
    d.hut(3, 2, 3)
    d.item(7, 2, 3, "barrel")
    for i in range(RACKS[L]):
        d.rack(3, 2, 5 + i, "east")
    d.set(7, 2, 7, "light_gray_shulker_box[facing=up]")
    d.set(7, 2, 6, "smooth_quartz_slab[type=top,waterlogged=false]")
    d.set(7, 3, 6, "black_stained_glass_pane")
    for y in (7,):
        d.set(4, y, 6, "sea_lantern")
    for x in (3, 7):
        d.bed(x, 9, 3, "west" if x == 3 else "east", "cyan")
        d.bed(x, 9, 7, "west" if x == 3 else "east", "cyan")
    d.set(6, 12, 6, "sea_lantern")
    if L == 1:
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                if x in (x1, x2) or z in (z1, z2):
                    d.set(x, top + 1, z, "light_gray_stained_glass_pane")
        d.set(7, top + 1, 7, "sea_lantern")
    else:                                                     # glazed watch cab cantilevered over the wall
        c1, c2 = 1, 9
        for x in range(c1, c2 + 1):
            for z in range(c1, c2 + 1):
                edge = x in (c1, c2) or z in (c1, c2)
                d.set(x, top, z, "smooth_quartz")
                for y in range(top + 1, top + 4):
                    d.set(x, y, z, ("light_gray_concrete" if x in (c1, c2) and z in (c1, c2) else
                                    ("white_concrete" if y == top + 1 else "light_blue_stained_glass_pane"))
                          if edge else AIR)
                d.set(x, top + 4, z, "white_concrete" if edge else "smooth_quartz")
                d.set(x, top + 5, z, "smooth_quartz_slab[type=bottom,waterlogged=false]") if edge else None
        for x in range(c1 + 1, c2):
            d.set(x, top - 1, c1, "smooth_quartz_slab[type=top,waterlogged=false]") if not x1 <= x <= x2 else None
        for z in range(c1, c2 + 1):
            for x in (c1, c2):
                if not z1 <= z <= z2:
                    pass
        d.set(5, top + 4, 4, AIR)
        d.set(5, top + 5, 4, AIR)
        ladder(d, 5, 4, top + 1, top + 5, "north")
        for y in range(top + 1, top + 5):
            d.set(5, y, 5, "light_gray_concrete")
        d.set(3, top + 1, 3, "smooth_quartz_slab[type=top,waterlogged=false]")
        d.set(4, top + 1, 3, "smooth_quartz_slab[type=top,waterlogged=false]")
        d.set(3, top + 2, 3, "black_stained_glass_pane")
        d.chair(3, top + 1, 4, "south", "birch", sit=False)
        d.set(7, top + 3, 7, "sea_lantern")
        # roof: rail, searchlight, antenna
        for x in range(c1, c2 + 1):
            for z in (c1, c2):
                d.set(x, top + 5, z, "light_gray_stained_glass_pane")
        for z in range(c1, c2 + 1):
            for x in (c1, c2):
                d.set(x, top + 5, z, "light_gray_stained_glass_pane")
        if L >= 3:
            d.set(7, top + 5, 3, "sea_lantern")
            d.set(7, top + 6, 3, "daylight_detector[inverted=false,power=0]")
        if L >= 4:
            for y in range(top + 5, top + 9):
                d.set(3, y, 7, "iron_bars" if y < top + 8 else ROD())
        if L >= 5:
            for x, z in ((c1, c1), (c2, c1), (c1, c2), (c2, c2)):
                d.set(x, top + 6, z, ENDROD())
    wt_complex(d, L, 5, 8, 9)
    return d


@design("wallguardtower")
def wallguardtower(pack, rel, L):
    d = {"Hearthwood": wt_hearthwood, "Cascadia": wt_cascadia, "Neoterra": wt_neoterra}[pack](rel, L)
    dress_wallguard(d, L)
    common_materials(d, L)
    return d
