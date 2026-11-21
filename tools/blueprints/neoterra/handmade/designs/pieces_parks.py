"""
Parks & decorations – hand-designed bench, fountain and parks for Neoterra, Hearthwood and Cascadia.

Pieces (sizes and anchors unchanged from the generated set; the decoration controller sits in the ground layer
at the middle of the north edge, where the entrance path meets the street):
  bench       5x5x3    controller (2,1,0)   3 outdoor seats
  fountain    9x12x9   controller (4,1,0)
  smallpark   11x12x11 controller (5,1,0)   4 seats
  mediumpark  17x12x17 controller (8,1,0)   5+ seats
  plaza       19x12x19 controller (9,1,0)   5+ seats
  parklarge   25x12x25 controller (12,1,0)  5+ seats

Conventions: ground surface y = GY = 1 (paths, lawns, water flush with it); everything a visitor uses stands on
y = 2. Every piece's entrance path leaves the north edge (z = 0) centred on the controller column, so it meets a
road sidewalk head-on. Ponds / pools hold their water at y = 1 on a bed laid at y = 0 and are closed on every
side by ground blocks; raised basins are closed by their rims. Jets are single floating source blocks whose water
falls straight back into a pool (falling water does not spread over a water surface).

Ground and furniture are drawn from hand-written ASCII plans (rows north -> south, characters west -> east).
In every plan the letters n / s / e / w are SEATS (pack bench stairs, backrest on that side) and get the
`sit_out` tag; every other character comes from the plan's legend. Trees, lamps, sculptures, pavilions are
single-object helpers called at hand-chosen coordinates.

Packs:
  Neoterra    modern pocket parks / civic plaza: smooth-stone and diorite paving with in-ground sea-lantern
              uplights, raised light-gray concrete planters with birches, moss beds with alliums and white tulips,
              slim column lights, birch-slat benches, white sculptures, reflecting pools, water walls and jet fields.
  Hearthwood  English village: brick and stone-sett paving, gravel walks, box hedges, rose beds, oaks, black
              lamp posts with lanterns, dark-oak benches with arms, market crosses, a sundial rose garden, a
              market square with stalls and a horse trough, a bandstand on a green with a duck pond.
  Cascadia    PNW forest park: coarse-dirt / podzol trails, river-rock boulders, ferns and berry bushes, firs,
              log lamp posts with lanterns, spruce benches and log seats, fire circles, a rock spring, a log
              picnic shelter over a creek, a lodge commons with an outdoor stone fireplace.
"""
from hm import Design, design, AIR

GY = 1
SEATS = "nsew"


# ------------------------------------------------------------------------------------------------ block states
def stairs(n, facing, half="bottom"):
    return f"{n}_stairs[facing={facing},half={half},shape=straight,waterlogged=false]"


def slab(n, t="bottom"):
    return f"{n}_slab[type={t},waterlogged=false]"


def wall(n, ns="none", ew="none", up=True):
    return (f"{n}_wall[east={ew},north={ns},south={ns},up={'true' if up else 'false'},waterlogged=false,"
            f"west={ew}]")


def leaves(n):
    return f"{n}_leaves[distance=1,persistent=true,waterlogged=false]"


def log(n, axis="y"):
    return f"{n}[axis={axis}]"


def trap(n, facing, open_=True, half="bottom"):
    return f"{n}_trapdoor[facing={facing},half={half},open={'true' if open_ else 'false'},powered=false,waterlogged=false]"


def tall(n, half):
    return f"{n}[half={half}]"


LANTERN = "lantern[hanging=false,waterlogged=false]"
HANGING = "lantern[hanging=true,waterlogged=false]"
WATER = "water[level=0]"
LILY = "lily_pad"
CAMPFIRE = "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]"
SEAT_WOOD = {"Neoterra": "birch", "Hearthwood": "dark_oak", "Cascadia": "spruce"}


# ------------------------------------------------------------------------------------------------ plan stamping
def plan(d, y, rows, legend, x0=0, z0=0, seat=None):
    """Stamp a hand-drawn plan at height y. ' ' = leave, '.' = air, n/s/e/w = seat with its backrest on that
    side (tagged sit_out), anything else from `legend`."""
    w = len(rows[0])
    for r in rows:
        assert len(r) == w, f"{d.rel} {d.pack} y={y}: ragged plan row {r!r}"
    seat = seat or SEAT_WOOD[d.pack]
    side = {"n": "north", "s": "south", "e": "east", "w": "west"}
    for dz, row in enumerate(rows):
        for dx, ch in enumerate(row):
            x, z = x0 + dx, z0 + dz
            if ch == " ":
                continue
            if ch == ".":
                d.set(x, y, z, AIR)
            elif ch in SEATS and ch not in legend:
                d.set(x, y, z, stairs(seat, side[ch]))
                d.tag(x, y, z, "sit_out")
            else:
                d.set(x, y, z, legend[ch])


def tags_from(d, y, rows, ch, name, x0=0, z0=0):
    """Tag every cell marked `ch` in a hand-drawn tag plan."""
    for dz, row in enumerate(rows):
        for dx, c in enumerate(row):
            if c == ch:
                d.tag(x0 + dx, y, z0 + dz, name)


def new(pack, rel, size, ctrl):
    d = Design(pack, rel, size=size, gy=GY)
    d.ctrl = ctrl
    return d


def done(d):
    """Place the decoration controller last (it replaces the entrance-path block in the ground layer)."""
    d.hut(*d.ctrl)
    return d


# ------------------------------------------------------------------------------------------------ trees
def birch(d, x, z, y=2, h=5):
    """Columnar birch: trunk h high, narrow crown around its top."""
    for k in range(h):
        d.set(x, y + k, z, log("birch_log"))
    t = y + h - 1
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            if (dx, dz) != (0, 0):
                if abs(dx) + abs(dz) == 1:
                    d.set(x + dx, t - 2, z + dz, leaves("birch"))
                d.set(x + dx, t - 1, z + dz, leaves("birch"))
                if abs(dx) + abs(dz) == 1:
                    d.set(x + dx, t, z + dz, leaves("birch"))
    d.set(x, t + 1, z, leaves("birch"))


def oak(d, x, z, y=2, kind="oak"):
    """Broad village oak, crown radius 2 (needs x-2..x+2 / z-2..z+2 clear above y+2)."""
    for k in range(5):
        d.set(x, y + k, z, log(f"{kind}_log"))
    for dy, r in ((2, 2), (3, 2), (4, 1), (5, 1)):
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                if (dx, dz) == (0, 0) and dy < 5:
                    continue
                if abs(dx) == r and abs(dz) == r:
                    continue
                if dy == 5 and abs(dx) + abs(dz) > 1:
                    continue
                d.set(x + dx, y + dy, z + dz, leaves(kind))


def small_oak(d, x, z, y=2, kind="oak"):
    """Garden tree, crown radius 1."""
    for k in range(3):
        d.set(x, y + k, z, log(f"{kind}_log"))
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            if (dx, dz) != (0, 0):
                d.set(x + dx, y + 2, z + dz, leaves(kind))
            d.set(x + dx, y + 3, z + dz, leaves(kind))
    d.set(x, y + 4, z, leaves(kind))


def willow(d, x, z, y=2):
    """Pond-side weeping tree: oak with a wide flat crown and vines hanging from its rim."""
    for k in range(5):
        d.set(x, y + k, z, log("oak_log"))
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            if abs(dx) == 2 and abs(dz) == 2:
                continue
            d.set(x + dx, y + 4, z + dz, leaves("oak"))
            if abs(dx) <= 1 and abs(dz) <= 1:
                d.set(x + dx, y + 5, z + dz, leaves("oak"))
    d.set(x, y + 4, z, log("oak_log"))
    for (dx, dz, f) in ((-3, 0, "east"), (3, 0, "west"), (0, -3, "south"), (0, 3, "north"),
                        (-2, -2, "east"), (2, 2, "west")):
        vine = f"vine[east={'true' if f == 'east' else 'false'},north={'true' if f == 'north' else 'false'}," \
               f"south={'true' if f == 'south' else 'false'},up=false,west={'true' if f == 'west' else 'false'}]"
        if abs(dx) == 2 and abs(dz) == 2:
            continue
        d.set(x + dx, y + 4, z + dz, vine)
        d.set(x + dx, y + 3, z + dz, vine)


def fir(d, x, z, y=2, h=6):
    """Fir: straight spruce trunk with tiered crown; radius 1 (h<=6) or 2 (h>=7)."""
    for k in range(h - 1):
        d.set(x, y + k, z, log("spruce_log"))
    wide = h >= 7
    base = y + 1 if not wide else y + 2
    if wide:
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                if abs(dx) + abs(dz) <= 3 and (dx, dz) != (0, 0):
                    d.set(x + dx, base, z + dz, leaves("spruce"))
        base += 1
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            if (dx, dz) != (0, 0):
                d.set(x + dx, base, z + dz, leaves("spruce"))
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        d.set(x + dx, base + 1, z + dz, leaves("spruce"))
        if wide:
            d.set(x + dx, base + 3, z + dz, leaves("spruce"))
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            if (dx, dz) != (0, 0) and base + 2 < y + h - 1:
                d.set(x + dx, base + 2, z + dz, leaves("spruce"))
    d.set(x, y + h - 1, z, leaves("spruce"))
    d.set(x, y + h, z, leaves("spruce"))


# ------------------------------------------------------------------------------------------------ lights
def neo_light(d, x, z, y=2):
    """Neoterra column light: andesite foot, slim bar shaft, sea-lantern head, smooth-stone cap."""
    d.set(x, y, z, "polished_andesite")
    d.set(x, y + 1, z, "iron_bars")
    d.set(x, y + 2, z, "iron_bars")
    d.set(x, y + 3, z, "sea_lantern")
    d.set(x, y + 4, z, slab("smooth_stone"))


def hw_lamp(d, x, z, y=2, arms=None):
    """Hearthwood lamp post: black post with a lantern on top; arms=[(dx,dz),..] adds bracket arms with
    hanging lanterns (double lamp for squares)."""
    for k in range(3):
        d.set(x, y + k, z, wall("polished_deepslate"))
    if not arms:
        d.set(x, y + 3, z, LANTERN)
        return
    d.set(x, y + 3, z, wall("polished_deepslate"))
    d.set(x, y + 4, z, LANTERN)
    for dx, dz in arms:
        d.set(x + dx, y + 3, z + dz, "dark_oak_fence")
        d.set(x + dx, y + 2, z + dz, HANGING)


def cas_lamp(d, x, z, y=2, arm=None):
    """Cascadia log lamp post; with arm=(dx,dz) a gallows bracket carries a hanging lantern."""
    if arm:
        for k in range(4):
            d.set(x, y + k, z, log("spruce_log"))
        d.set(x + arm[0], y + 3, z + arm[1], "spruce_fence")
        d.set(x + arm[0], y + 2, z + arm[1], HANGING)
    else:
        for k in range(2):
            d.set(x, y + k, z, log("spruce_log"))
        d.set(x, y + 2, z, "spruce_fence")
        d.set(x, y + 3, z, LANTERN)


# ================================================================================================= BENCH
@design("bench")
def bench(pack, rel, L):
    d = new(pack, rel, (5, 5, 3), (2, 1, 0))
    if pack == "Neoterra":
        # birch-slat bench between two white concrete ends, moss planter with azaleas behind, column light
        plan(d, 1, ["PPPPP",
                    "PPPPP",
                    "GGGGG"], {"P": "smooth_stone", "G": "grass_block"})
        plan(d, 2, [".....",
                    "KsssK",
                    "CMMMA"], {"K": "white_concrete", "C": "light_gray_concrete", "M": "moss_block",
                               "A": "polished_andesite"})
        plan(d, 3, [".....",
                    "p....",
                    ".898I"], {"p": "potted_white_tulip", "8": "azalea", "9": "flowering_azalea",
                               "I": "iron_bars"})
        d.set(4, 4, 2, "sea_lantern")
    elif pack == "Hearthwood":
        # dark-oak garden bench with arms in a box-hedge niche, lamp post at one end, rose bush at the other
        plan(d, 1, ["TTTTT",
                    "BBBBB",
                    "GGGGG"], {"T": "stone_bricks", "B": "bricks", "G": "grass_block"})
        plan(d, 2, [".....",
                    "[sss]",
                    "FHHHr"], {"[": trap("dark_oak", "west"), "]": trap("dark_oak", "east"),
                               "F": "dark_oak_fence", "H": leaves("oak"), "r": tall("rose_bush", "lower")})
        plan(d, 3, [".....",
                    ".....",
                    "FHHHr"], {"F": "dark_oak_fence", "H": leaves("oak"), "r": tall("rose_bush", "upper")})
        d.set(0, 4, 2, LANTERN)
    else:
        # split-log bench between two stumps (one with a lantern), boulder, ferns and a berry bush behind
        plan(d, 1, ["ccdcc",
                    "cdddc",
                    "pgpgg"], {"c": "coarse_dirt", "d": "dirt_path", "p": "podzol", "g": "grass_block"})
        plan(d, 2, [".....",
                    "OsssO",
                    "f#Lb#"], {"O": log("spruce_log"), "f": "fern", "#": "mossy_cobblestone",
                               "L": tall("large_fern", "lower"), "b": "sweet_berry_bush[age=3]"})
        plan(d, 3, [".....",
                    "l....",
                    "._U.."], {"l": LANTERN, "_": slab("mossy_cobblestone"), "U": tall("large_fern", "upper")})
    return done(d)


# ================================================================================================= FOUNTAIN
@design("fountain")
def fountain(pack, rel, L):
    d = new(pack, rel, (9, 12, 9), (4, 1, 0))
    if pack == "Neoterra":
        neo_fountain(d)
    elif pack == "Hearthwood":
        hw_fountain(d)
    else:
        cas_fountain(d)
    return done(d)


def neo_fountain(d):
    """Square sunken basin with a slab ledge, a white column with a cyan band and a lit head throwing a jet,
    four floating corner jets, benches on both sides, planter strip and column lights."""
    d.fill(2, 0, 2, 6, 0, 6, "cyan_terracotta")
    plan(d, 1, ["PPPPPPPPP",
                "PAAAAAAAP",
                "PAWWWWWAP",
                "PAWWWWWAP",
                "PAWWAWWAP",
                "PAWWWWWAP",
                "PAWWWWWAP",
                "PAAAAAAAP",
                "GGGGGGGGG"], {"P": "smooth_stone", "A": "polished_andesite", "W": WATER, "G": "grass_block"})
    plan(d, 2, [".........",
                ".SSSSSSS.",
                "CS.....SC",
                "wS.....Se",
                "wS..K..Se",
                "wS.....Se",
                "CS.....SC",
                ".SSSSSSS.",
                ".MMMMMMM."], {"S": slab("smooth_stone"), "C": "light_gray_concrete", "K": "white_concrete",
                               "M": "moss_block"})
    plan(d, 3, [".........",
                ".........",
                "p.J...J.p",
                ".........",
                "....Y....",
                ".........",
                "p.J...J.p",
                ".........",
                ".1929291."], {"p": "potted_allium", "J": WATER, "Y": "cyan_terracotta", "1": "allium",
                               "2": "white_tulip", "9": "flowering_azalea"})
    d.set(4, 4, 4, "white_concrete")
    d.set(4, 5, 4, "sea_lantern")
    d.set(4, 6, 4, WATER)                      # crown jet: spills into the basin on all four sides
    for x, z in ((0, 0), (8, 0), (0, 8), (8, 8)):
        neo_light(d, x, z)
    d.tag(3, 1, 0, "stand_out")


def hw_fountain(d):
    """Octagonal raised stone basin with chiseled corners, a tiered pedestal whose upper bowl spills into the
    basin, two arm benches facing it, lamp posts at the front corners and rose beds at the back."""
    plan(d, 1, ["TtTtTtTtT",
                "tGGRRRGGt",
                "TGRRRRRGT",
                "tRRRRRRRt",
                "TRRRRRRRT",
                "tRRRRRRRt",
                "TGRRRRRGT",
                "tGGRRRGGt",
                "TtTtTtTtT"], {"T": "stone_bricks", "t": "andesite", "R": "stone_bricks", "G": "grass_block"})
    plan(d, 2, [".........",
                "..fRRRf..",
                ".fXWWWXf.",
                "wRWWWWWRe",
                "wRWWPWWRe",
                "wRWWWWWRe",
                ".gXWWWXg.",
                ".rfRRRfr.",
                "........."], {"R": "stone_bricks", "X": "chiseled_stone_bricks", "W": WATER,
                               "P": "chiseled_stone_bricks", "f": "pink_tulip", "g": "red_tulip",
                               "r": tall("rose_bush", "lower")})
    plan(d, 3, [".........",
                ".........",
                ".........",
                ".........",
                "....|....",
                ".........",
                ".........",
                ".r.....r.",
                "........."], {"|": wall("stone_brick"), "r": tall("rose_bush", "upper")})
    # upper bowl on corbels, water spills off its lip into the basin
    d.set(4, 4, 4, "stone_bricks")
    d.set(3, 4, 4, stairs("stone_brick", "east", "top"))
    d.set(5, 4, 4, stairs("stone_brick", "west", "top"))
    d.set(4, 4, 3, stairs("stone_brick", "south", "top"))
    d.set(4, 4, 5, stairs("stone_brick", "north", "top"))
    d.set(4, 5, 4, WATER)
    # bench arms
    for x in (0, 8):
        d.set(x, 2, 2, trap("dark_oak", "north"))
        d.set(x, 2, 6, trap("dark_oak", "south"))
    hw_lamp(d, 1, 1)
    hw_lamp(d, 7, 1)
    d.tag(3, 1, 0, "stand_out")


def cas_fountain(d):
    """River-rock spring pool: water spills from a notch in a mossy boulder pile into an irregular rock-edged
    pool with lily pads; log benches on both sides, firs at the back corners, lantern posts at the trail."""
    d.fill(2, 0, 2, 6, 0, 6, "gravel")
    plan(d, 1, ["gpccdccpg",
                "ggcodmcgg",
                "gpmWWWapg",
                "gaWWWWWog",
                "gmWWWWWmg",
                "goWWWWWag",
                "gpaWWWmpg",
                "ggmoToagg",
                "gpggpggpg"], {"g": "grass_block", "p": "podzol", "c": "coarse_dirt", "d": "dirt_path",
                               "o": "cobblestone", "m": "mossy_cobblestone", "a": "andesite", "T": "tuff",
                               "W": WATER})
    plan(d, 2, [".........",
                ".f.....f.",
                "..._.....",
                "wa.....oe",
                "w..L....e",
                "w.....L.e",
                ".........",
                "f..mM#...",
                "....T...."], {"f": "fern", "a": slab("andesite"), "o": slab("cobblestone"), "L": LILY,
                               "_": slab("mossy_cobblestone"), "m": "mossy_cobblestone", "M": "cobblestone",
                               "#": "andesite", "T": "tuff", "F": "sweet_berry_bush[age=3]"})
    # the spring: boulder pile with a notch holding a source that spills north into the pool
    plan(d, 3, ["...", "m~#", ".m."], {"m": "mossy_cobblestone", "~": WATER, "#": "cobblestone"}, x0=3, z0=6)
    d.set(3, 3, 6, AIR)
    d.set(5, 3, 6, AIR)
    d.set(4, 3, 6, AIR)
    d.set(4, 4, 7, "mossy_cobblestone")
    d.set(4, 4, 8, "cobblestone")
    d.set(3, 3, 8, "andesite")
    d.set(4, 5, 8, slab("mossy_cobblestone"))
    d.set(3, 4, 7, slab("andesite"))
    d.set(5, 4, 7, "fern")
    fir(d, 1, 7, h=6)
    fir(d, 7, 7, h=5)
    cas_lamp(d, 2, 1)
    cas_lamp(d, 6, 1)
    d.tag(4, 1, 1, "stand_out")
