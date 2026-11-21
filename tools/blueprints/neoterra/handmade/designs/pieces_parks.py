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


# ================================================================================================= NEOTERRA
NEO = {"P": "smooth_stone", "D": "polished_diorite", "A": "polished_andesite", "G": "grass_block",
       "M": "moss_block", "L": "sea_lantern", "W": WATER, "K": "white_concrete", "C": "light_gray_concrete",
       "Y": "cyan_terracotta", "g": "grass_block", "S": slab("smooth_stone"), "_": slab("smooth_stone"),
       "B": "birch_planks", "b": slab("birch"), "1": "allium", "2": "white_tulip", "3": "cornflower",
       "4": "azure_bluet", "7": "fern", "8": "azalea", "9": "flowering_azalea", "6": "short_grass",
       "|": "light_gray_stained_glass_pane", "#": "light_blue_stained_glass"}


def neo_ring(d, cx, y, z, big=False):
    """Neoterra 'Ring' sculpture standing in the x-y plane at row z, bottom at y, centred on cx.
    small: 3x3 white frame around a pale-blue glass eye; big: 5x5 rounded hoop with a lit base."""
    if not big:
        for dx, dy in ((-1, 0), (0, 0), (1, 0), (-1, 1), (1, 1), (-1, 2), (0, 2), (1, 2)):
            d.set(cx + dx, y + dy, z, "white_concrete")
        d.set(cx, y + 1, z, "light_blue_stained_glass")
        return
    for dx in (-1, 0, 1):
        d.set(cx + dx, y, z, "white_concrete")
        d.set(cx + dx, y + 4, z, "white_concrete")
    for dy in (1, 2, 3):
        d.set(cx - 2, y + dy, z, "white_concrete")
        d.set(cx + 2, y + dy, z, "white_concrete")
    d.set(cx, y + 4, z, "cyan_terracotta")


def solar_tree(d, x, z):
    """Neoterra 'solar tree': white trunk with a lit collar, a canopy of daylight-sensor panels, and four
    seats round its foot facing outward."""
    d.set(x, 2, z, "polished_andesite")
    for y in range(3, 7):
        d.set(x, y, z, "white_concrete")
    d.set(x, 7, z, "sea_lantern")
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            d.set(x + dx, 8, z + dz, "smooth_stone" if (dx, dz) == (0, 0) else slab("smooth_stone", "top"))
            d.set(x + dx, 9, z + dz, "daylight_detector[inverted=false,power=0]")
    for dx, dz, b in ((1, 0, "west"), (-1, 0, "east"), (0, 1, "north"), (0, -1, "south")):
        d.set(x + dx, 2, z + dz, stairs("birch", b))
        d.tag(x + dx, 2, z + dz, "sit_out")


def neo_smallpark(d):
    """Pocket park: path to a small paved square with the Ring sculpture on a plinth, two birch-slat benches
    facing it, raised moss beds with azaleas and alliums, birches in concrete planters at the four corners."""
    plan(d, 1, ["GGGGPPPGGGG",
                "GGGGPLPGGGG",
                "GGGGPPPGGGG",
                "GAAAAPAAAAG",
                "GAPDPDPDPAG",
                "GAPPDLDPPAG",
                "GAPDPDPDPAG",
                "GAPPPPPPPAG",
                "GAAAAAAAAAG",
                "GGGGGGGGGGG",
                "GGGGGGGGGGG"], NEO)
    plan(d, 2, ["CCC.....CCC",
                "CgC.....CgC",
                "CCC.....CCC",
                "...........",
                ".MM.....MM.",
                ".MM.AAA.MM.",
                ".MM.....MM.",
                "..Kss.ssK..",
                "CCC.....CCC",
                "CgC.MMM.CgC",
                "CCC.....CCC"], NEO)
    plan(d, 3, ["...........",
                "...........",
                "...........",
                "...........",
                ".19.....91.",
                ".82.....28.",
                ".19.....91.",
                "..p.....p..",
                "...........",
                "....121....",
                "..........."], dict(NEO, p="potted_white_tulip"))
    neo_ring(d, 5, 3, 5)
    for x, z in ((1, 1), (9, 1), (1, 9), (9, 9)):
        birch(d, x, z, y=3, h=5)
    neo_light(d, 3, 3)
    neo_light(d, 7, 3)
    d.tag(5, 1, 3, "stand_out")


def neo_mediumpark(d):
    """Water garden: forecourt with a park sign, a long reflecting pool lit from below and closed at the far
    end by a water wall (a trough on top spills a sheet of water into the pool), benches on both side walks
    looking across the water, birches and allium beds on the lawns."""
    d.fill(6, 0, 5, 10, 0, 11, "cyan_terracotta")
    for z in (6, 8, 10):
        d.set(8, 0, z, "sea_lantern")
    rows = ["GGGGGGPPPPPGGGGGG",
            "GGGGGGPPLPPGGGGGG",
            "GGGPPPPPPPPPPPGGG",
            "GGGPDPDPDPDPDPGGG",
            "GGGPPAAAAAAAPPGGG"]
    rows += ["GGGPPAWWWWWAPPGGG"] * 7
    rows += ["GGGPPKKKKKKKPPGGG",
             "GGGPPKKKKKKKPPGGG",
             "GGGPLPPPPPPPLPGGG",
             "GGGGGGGGGGGGGGGGG",
             "GGGGGGGGGGGGGGGGG"]
    plan(d, 1, rows, NEO)
    plan(d, 2, [".1.2.........2.1.",
                "4.1...........1.4",
                ".................",
                ".................",
                ".....SSSSSSS.....",
                "...K.S.....S.....",
                "...w.S.....S.....",
                "...w.S.....S.K...",
                "...w.S.....S.e...",
                "...K.S.....S.e...",
                ".....S.....S.e...",
                ".....S.....S.K...",
                ".....KKKKKKK.....",
                ".....KKKKKKK.....",
                ".................",
                ".....9.8.9.......",
                "................."], NEO)
    # water wall: white concrete with a cyan band, trough on top spilling north into the pool
    for x in range(5, 12):
        d.set(x, 3, 12, "cyan_terracotta")
        d.set(x, 3, 13, "white_concrete")
        d.set(x, 4, 12, "white_concrete")
        d.set(x, 4, 13, "white_concrete")
        d.set(x, 5, 13, "white_concrete")
        d.set(x, 6, 13, slab("smooth_stone"))
        d.set(x, 5, 12, WATER if 6 <= x <= 10 else "white_concrete")
    d.set(5, 6, 12, slab("smooth_stone"))
    d.set(11, 6, 12, slab("smooth_stone"))
    # lawns: birches with allium / tulip clumps between them
    for x, z in ((1, 5), (1, 10), (15, 5), (15, 10), (3, 15), (13, 15)):
        birch(d, x, z, h=5)
    for x, z, f in ((1, 7, "allium"), (1, 8, "white_tulip"), (0, 8, "allium"), (15, 7, "white_tulip"),
                    (15, 8, "allium"), (16, 7, "allium"), (2, 12, "cornflower"), (14, 12, "cornflower")):
        d.set(x, 2, z, f)
    # park sign on a white plinth beside the entrance
    d.set(12, 2, 1, "white_concrete")
    d.set(12, 3, 1, "white_concrete")
    d.sign(12, 3, 0, "north", ["", "WATER GARDEN", "", ""], wood="birch", glow=True, color="cyan")
    for x, z in ((3, 2), (13, 2), (3, 14), (13, 14)):
        neo_light(d, x, z)
    d.tag(8, 1, 3, "stand_out")


def neo_plaza(d):
    """Civic plaza: banded paving, a sunken jet basin (eight floating jets around a lit obelisk) with a slab
    ledge to sit on, long benches backed by moss planters on both sides, birches in raised corner planters,
    a stepped podium with the big Ring sculpture at the far end, column lights on the banding."""
    d.fill(6, 0, 6, 12, 0, 12, "cyan_terracotta")
    rows = ["PPPPPPPPPDPPPPPPPPP",
            "PPPPDPPPPLPPPPDPPPP",
            "PPPPDPPPPDPPPPDPPPP",
            "PPPPDPPPPLPPPPDPPPP",
            "DDDDDDDDDDDDDDDDDDD",
            "PPPPDAAAAAAAAADPPPP"]
    rows += ["PPPPDAWWWWWWWADPPPP"] * 3
    rows += ["PPPPDAWWWAWWWADPPPP"]
    rows += ["PPPPDAWWWWWWWADPPPP"] * 3
    rows += ["PPPPDAAAAAAAAADPPPP",
             "DDDDDDDDDDDDDDDDDDD",
             "PPPPDPAAAAAAAPDPPPP",
             "PPPPDPAAAAAAAPDPPPP",
             "PPPPDPAAAAAAAPDPPPP",
             "PPPPDPPPPPPPPPDPPPP"]
    plan(d, 1, rows, NEO)
    plan(d, 2, ["...................",
                ".CCC...........CCC.",
                ".CgC...........CgC.",
                ".CCC...........CCC.",
                "...................",
                ".....SSSSSSSSS.....",
                ".CC..S.......S..CC.",
                ".MMK.S.......S.KMM.",
                ".MMw.S.......S.eMM.",
                ".MMw.S...K...S.eMM.",
                ".MMw.S.......S.eMM.",
                ".MMK.S.......S.KMM.",
                ".CC..S.......S..CC.",
                ".....SSSSSSSSS.....",
                "......_______......",
                ".CCC..DDDDDDD..CCC.",
                ".CgC..DDDDDDD..CgC.",
                ".CCC..DDDDDDD..CCC.",
                "..................."], NEO)
    plan(d, 3, ["...................",
                "...................",
                "...................",
                "...................",
                "...................",
                "...................",
                "...................",
                ".91.............19.",
                ".28.............82.",
                ".19.............91.",
                ".82.............28.",
                ".91.............19.",
                "..................."], NEO)
    # obelisk with a lit head, eight floating jets around it
    for y, b in ((3, "white_concrete"), (4, "cyan_terracotta"), (5, "white_concrete"), (6, "sea_lantern")):
        d.set(9, y, 9, b)
    d.set(9, 7, 9, slab("smooth_stone"))
    for x, z in ((7, 7), (9, 7), (11, 7), (7, 9), (11, 9), (7, 11), (9, 11), (11, 11)):
        d.set(x, 4, z, WATER)
    neo_ring(d, 9, 3, 16, big=True)
    for x, z in ((2, 2), (16, 2), (2, 16), (16, 16)):
        birch(d, x, z, y=3, h=5)
    for x, z in ((4, 4), (14, 4), (4, 14), (14, 14)):
        neo_light(d, x, z)
    d.tag(9, 1, 4, "stand_out")


def neo_parklarge(d):
    """City park: entry court, axis walk to a round plaza with the big Ring sculpture, a birch grove with a
    reading niche to the west, a long pond with zig-zag floating jets and a birch boardwalk with benches to
    the east, and a glass-roofed pavilion at the south end whose benches look back up the axis."""
    d.fill(17, 0, 6, 22, 0, 17, "cyan_terracotta")
    G11, G8 = "G" * 11, "G" * 8
    pond = "B" + "W" * 6 + "AG"
    rows = [G8 + "PPPPPPPPP" + G8,
            G8 + "PPPDPDPPP" + G8,
            G8 + "PLPDLDPLP" + G8,
            G8 + "PPPDPDPPP" + G8,
            G11 + "DPD" + G11,
            G11 + "DPD" + "GG" + "B" + "AAAAAAA" + "G",
            G11 + "DLD" + "GG" + pond,
            G11 + "DPD" + "GG" + pond,
            G11 + "DPD" + "GG" + pond,
            "G" * 10 + "PPPPP" + "G" + pond,
            "G" * 9 + "PPDDDPP" + pond,
            "GGPPGGGGG" + "PDPPPDP" + pond,
            "GGPPPPPPP" + "DPPAPPD" + pond,
            "GGPPGGGGG" + "PDPPPDP" + pond,
            "G" * 9 + "PPDDDPP" + pond,
            "G" * 10 + "PPPPP" + "G" + pond,
            G11 + "DPD" + "GG" + pond,
            G11 + "DLD" + "GG" + pond,
            G8 + "D" * 9 + "AAAAAAA" + "G"]
    rows += [G8 + "D" * 9 + G8] * 5
    rows += ["G" * 25]
    plan(d, 1, rows, NEO)
    # north lawns: raised planters with grasses and alliums
    for x0 in (2, 19):
        plan(d, 2, ["CCCC", "CMMC", "CCCC"], NEO, x0=x0, z0=1)
        plan(d, 3, ["1961" if x0 == 2 else "1691"], NEO, x0=x0, z0=2)
        d.set(x0, 3, 2, AIR)
        d.set(x0 + 3, 3, 2, AIR)
    # round plaza: big Ring on a plinth, seen from the entrance and from the pavilion
    for x in (11, 12, 13):
        d.set(x, 2, 12, "polished_andesite")
    neo_ring(d, 12, 3, 12, big=True)
    # west grove with a reading niche at the end of the cross walk, facing the ring
    for x, z in ((2, 5), (6, 6), (3, 9), (6, 16), (2, 17), (4, 21), (1, 23 - 1)):
        birch(d, x, z, h=5 if (x + z) % 2 else 6)
    for z in (11, 12, 13):
        d.set(2, 2, z, stairs("birch", "west"))
        d.tag(2, 2, z, "sit_out")
    for x, z, f in ((4, 7, "fern"), (1, 8, "fern"), (5, 10, "short_grass"), (7, 9, "fern"), (4, 15, "fern"),
                    (1, 14, "allium"), (7, 18, "fern"), (3, 19, "short_grass"), (6, 23, "fern"), (1, 20, "allium")):
        d.set(x, 2, z, f)
    # east boardwalk: lights at both ends, two benches looking over the pond
    for z in (7, 8, 15, 16):
        d.set(16, 2, z, stairs("birch", "west"))
        d.tag(16, 2, z, "sit_out")
    for x, z in ((19, 8), (20, 10), (19, 12), (20, 14), (19, 16)):
        d.set(x, 4, z, WATER)
    # pavilion: white posts, glass roof with a white fascia and a light strip, glass screen behind benches
    for x, z in ((8, 18), (16, 18), (8, 23), (16, 23)):
        for y in range(2, 6):
            d.set(x, y, z, "white_concrete")
    for x in range(8, 17):
        for z in range(18, 24):
            edge = x in (8, 16) or z in (18, 23)
            d.set(x, 6, z, "white_concrete" if edge else "light_blue_stained_glass")
    for x in (10, 12, 14):
        d.set(x, 6, 20, "sea_lantern")
    for x in range(9, 16):
        for y in (2, 3, 4):
            d.set(x, y, 23, "light_gray_stained_glass_pane")
    for x in (9, 10, 11, 13, 14, 15):
        d.set(x, 2, 22, stairs("birch", "south"))
        d.tag(x, 2, 22, "sit_out")
    d.set(12, 2, 22, "light_gray_concrete")
    d.set(12, 3, 22, "potted_azalea_bush")
    # south-east lawn: a solar tree with a ring of seats in an allium meadow, reached from the pavilion
    for x in (17, 18, 19):
        d.set(x, 1, 20, "smooth_stone")
    paint_cells = ((20, 20), (21, 20), (22, 20), (20, 21), (22, 21), (20, 22), (21, 22), (22, 22))
    for x, z in paint_cells:
        d.set(x, 1, z, "polished_diorite")
    solar_tree(d, 21, 21)
    for x, z, f in ((18, 22, "allium"), (19, 23, "white_tulip"), (23, 20, "allium"), (18, 23, "cornflower"),
                    (23, 23, "allium"), (20, 19, "white_tulip"), (22, 23, "short_grass")):
        d.set(x, 2, z, f)
    for x, z in ((8, 3), (16, 3), (9, 9), (15, 9), (9, 15), (15, 15), (16, 5), (16, 17)):
        neo_light(d, x, z)
    d.tag(12, 1, 8, "stand_out")


@design("smallpark", "mediumpark", "plaza", "parklarge")
def parks(pack, rel, L):
    base = rel.split("/")[-1].split(".")[0]
    size = {"smallpark": 11, "mediumpark": 17, "plaza": 19, "parklarge": 25}[base]
    d = new(pack, rel, (size, 12, size), (size // 2, 1, 0))
    globals()[{"Neoterra": "neo_", "Hearthwood": "hw_", "Cascadia": "cas_"}[pack] + base](d)
    return done(d)


# ================================================================================================= HEARTHWOOD
HW = {"G": "grass_block", "g": "gravel", "K": "bricks", "T": "stone_bricks", "t": "cobblestone",
      "a": "andesite", "c": "cracked_stone_bricks", "H": leaves("oak"), "W": WATER, "D": "dark_oak_planks",
      "S": slab("stone_brick"), "^": trap("dark_oak", "north"), "v": trap("dark_oak", "south"),
      "[": trap("dark_oak", "west"), "]": trap("dark_oak", "east"),
      "r": tall("rose_bush", "lower"), "R": tall("rose_bush", "upper"), "p": tall("peony", "lower"),
      "P": tall("peony", "upper"), "l": tall("lilac", "lower"), "L": tall("lilac", "upper"),
      "1": "red_tulip", "2": "pink_tulip", "3": "white_tulip", "4": "oxeye_daisy", "5": "lily_of_the_valley",
      "6": "cornflower", "7": "poppy", "8": "allium", "9": "azure_bluet", "0": "dandelion"}


def hw_cross(d, x, z, y=2):
    """Village market cross: three-step stone base, chiseled socket, slender shaft and a stone cross head."""
    d.set(x, y, z, "stone_bricks")
    for dx, dz, f in ((0, -1, "south"), (0, 1, "north"), (-1, 0, "east"), (1, 0, "west")):
        d.set(x + dx, y, z + dz, stairs("stone_brick", f))
    for dx in (-1, 1):
        for dz in (-1, 1):
            d.set(x + dx, y, z + dz, slab("stone_brick"))
    d.set(x, y + 1, z, "chiseled_stone_bricks")
    for k in (2, 3, 4):
        d.set(x, y + k, z, wall("stone_brick"))
    d.set(x, y + 5, z, wall("stone_brick", ew="low"))
    d.set(x - 1, y + 5, z, "stone_brick_wall[east=low,north=none,south=none,up=false,waterlogged=false,west=none]")
    d.set(x + 1, y + 5, z, "stone_brick_wall[east=none,north=none,south=none,up=false,waterlogged=false,west=low]")
    d.set(x, y + 6, z, wall("stone_brick"))


def hw_smallpark(d):
    """Village green corner: brick-edged gravel path into a sett circle around a market cross, two arm benches
    facing it, lamp posts at the circle's mouth, a box hedge around the green, rose and peony border with two
    garden oaks at the back."""
    plan(d, 1, ["GGGGKgKGGGG",
                "GGGGKgKGGGG",
                "GGGGKgKGGGG",
                "GGGTTtTTGGG",
                "GGTTtTtTTGG",
                "GGTtTTTtTGG",
                "GGTTtTtTTGG",
                "GGGTTtTTGGG",
                "GGGGGGGGGGG",
                "GGGGGGGGGGG",
                "GGGGGGGGGGG"], HW)
    plan(d, 2, ["HHHH...HHHH",
                "H.........H",
                "H.1.....2.H",
                "H.^.....^.H",
                "H.w.....e.H",
                "H.w.....e.H",
                "H.w.....e.H",
                "H.v.....v.H",
                "H.r.p.p.r.H",
                "..2.3.3.1..",
                "..........."], HW)
    plan(d, 3, ["H.........H",
                "...........",
                "...........",
                "...........",
                "...........",
                "...........",
                "...........",
                "...........",
                "..R.P.P.R..",
                "...........",
                "..........."], HW)
    hw_cross(d, 5, 5)
    hw_lamp(d, 3, 3)
    hw_lamp(d, 7, 3)
    small_oak(d, 1, 9)
    small_oak(d, 9, 9)
    d.tag(5, 1, 3, "stand_out")


def hw_mediumpark(d):
    """Rose garden: a tall box hedge with a rose arch at the entrance, gravel cross walks, four quartered beds
    (roses around a small cherry, peony / tulip / lily edging in a different colour each), a sundial at the
    crossing, lamp posts on the bed corners and benches set into hedge niches at the ends of the walks."""
    bed = "GgGGGGGgggGGGGGgG"
    walk = "G" + "g" * 15 + "G"
    cross = "g" + "g" * 6 + "TtT" + "g" * 6 + "g"
    rows = ["GGGGGGGgggGGGGGGG", walk] + [bed] * 5 + [cross, "g" + "g" * 6 + "tTt" + "g" * 6 + "g", cross] \
        + [bed] * 5 + [walk, "GGGGGGGgggGGGGGGG"]
    plan(d, 1, rows, HW)
    # hedge 2 high around, niches with benches west / east / south
    plan(d, 2, ["HHHHHHH...HHHHHHH"] + ["H...............H"] * 6 +
               ["w...............e"] * 3 + ["H...............H"] * 6 + ["HHHHHHHsssHHHHHHH"], HW)
    plan(d, 3, ["HHHHHHH...HHHHHHH"] + ["H...............H"] * 6 +
               ["................."] * 3 + ["H...............H"] * 6 + ["HHHHHHH...HHHHHHH"], HW)
    for x, z in ((0, 6), (0, 10), (16, 6), (16, 10)):
        d.set(x, 4, z, leaves("oak"))                    # hedge piers framing the niches
    d.set(6, 2, 16, trap("dark_oak", "west"))
    d.set(10, 2, 16, trap("dark_oak", "east"))
    # rose arch over the entrance
    for x in (6, 10):
        d.set(x, 4, 0, leaves("oak"))
    for x in range(6, 11):
        d.set(x, 5, 0, leaves("flowering_azalea") if x % 2 == 0 else leaves("oak"))
    d.set(8, 6, 0, leaves("flowering_azalea"))
    # four beds: outer edging, inner ring of roses, cherry in the middle
    beds = {(2, 2): ("1", "7", "p", "P"), (10, 2): ("2", "8", "p", "P"),
            (2, 10): ("3", "5", "l", "L"), (10, 10): ("4", "6", "l", "L")}
    for (bx, bz), (a, b, t, T) in beds.items():
        plan(d, 2, [f"{a}{t}{b}{t}{a}",
                    f"{t}rrr{t}",
                    f"{b}r.r{b}",
                    f"{t}rrr{t}",
                    f"{a}{t}{b}{t}{a}"], HW, x0=bx, z0=bz)
        plan(d, 3, [f".{T}.{T}.",
                    f"{T}RRR{T}",
                    f".R.R.",
                    f"{T}RRR{T}",
                    f".{T}.{T}."], HW, x0=bx, z0=bz)
        small_oak(d, bx + 2, bz + 2, kind="cherry")
    for x, z in ((6, 6), (10, 6), (6, 10), (10, 10)):
        d.set(x, 3, z, AIR)
        hw_lamp(d, x, z)
    # sundial on a pedestal at the crossing
    d.set(8, 2, 8, "chiseled_stone_bricks")
    d.set(8, 3, 8, wall("stone_brick"))
    d.set(8, 4, 8, "daylight_detector[inverted=false,power=0]")
    d.tag(8, 1, 6, "stand_out")


def hw_stall(d, x0, z0, front, wool, goods):
    """Market stall, 3 wide (x0..x0+2) and 5 long (z0..z0+4): fence posts, a striped wool awning, a counter
    of barrels and planks on the `front` side ('east' or 'west') with goods on it, stock at the back."""
    fx = x0 + 2 if front == "east" else x0
    bx = x0 if front == "east" else x0 + 2
    for z in (z0, z0 + 4):
        for x in (x0, x0 + 2):
            for y in (2, 3, 4):
                d.set(x, y, z, "dark_oak_fence")
    for z in range(z0, z0 + 5):
        for x in range(x0, x0 + 3):
            d.set(x, 5, z, wool[(z - z0) % 2])
        ox = x0 + 3 if front == "east" else x0 - 1
        d.set(ox, 4, z, trap("dark_oak", "west" if front == "east" else "east", open_=False, half="top"))
    d.set(fx, 2, z0 + 1, "barrel[facing=up,open=false]")
    d.set(fx, 2, z0 + 2, "dark_oak_planks")
    d.set(fx, 2, z0 + 3, "barrel[facing=up,open=false]")
    for i, g in enumerate(goods):
        d.set(fx, 3, z0 + 1 + i, g)
    d.set(bx, 2, z0 + 1, "hay_block[axis=y]")
    d.set(bx, 2, z0 + 3, "barrel[facing=" + ("east" if front == "east" else "west") + ",open=false]")


def hw_plaza(d):
    """Market square: stone setts with brick bands, a roofed buttercross on a stepped platform with a round
    seat about its central pillar, two striped market stalls, a horse trough with a pump, a notice board,
    a long bench facing the cross, village oaks at the top corners and double lamp posts."""
    s1 = "TTtTTaTTtTTaTTtTTaT"
    s2 = "TaTTtTTaTTtTTaTTtTT"
    band = "KKKKKKKKKKKKKKKKKKK"
    rows = [s1, s2, s1, s2, band, s1, s2, s1, s2, s1, s2, s1, s2, s1, band, s2, s1, s2, s1]
    plan(d, 1, rows, HW)
    for x in (0, 18):
        for z in range(19):
            d.set(x, 1, z, "bricks")
    # buttercross: stepped platform, four stone piers, central pillar, hip roof of slate
    for x in range(6, 13):
        for z in range(6, 13):
            edge = x in (6, 12) or z in (6, 12)
            d.set(x, 2, z, slab("stone_brick") if edge else "stone_bricks")
    for x, z in ((7, 7), (11, 7), (7, 11), (11, 11)):
        d.set(x, 3, z, "chiseled_stone_bricks")
        d.set(x, 4, z, "stone_bricks")
        d.set(x, 5, z, "stone_bricks")
    for y in range(3, 8):
        d.set(9, y, 9, "stone_bricks" if y != 5 else "chiseled_stone_bricks")
    d.hip(7, 7, 11, 11, 6, stairs="minecraft:deepslate_tile_stairs", cap="minecraft:deepslate_tile_slab")
    d.set(9, 9, 9, "dark_oak_fence")
    d.set(9, 10, 9, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    for x, z, f in ((8, 9, "east"), (10, 9, "west"), (9, 8, "south"), (9, 10, "north")):
        d.set(x, 3, z, stairs("dark_oak", f))
        d.tag(x, 3, z, "sit_out")
    for x, z in ((8, 7), (10, 11)):
        d.set(x, 5, z, HANGING)                          # lanterns under the roof
    # stalls: greengrocer (red) west facing east, florist (blue) east facing west
    hw_stall(d, 1, 7, "east", ("red_wool", "white_wool"), ("pumpkin", "potted_red_tulip", "melon"))
    hw_stall(d, 15, 7, "west", ("blue_wool", "white_wool"),
             ("potted_pink_tulip", "potted_lily_of_the_valley", "potted_allium"))
    # horse trough with a pump (south-west)
    for x in (3, 4, 5):
        d.set(x, 2, 15, "water_cauldron[level=3]")
    d.set(2, 2, 15, log("dark_oak_log"))
    d.set(2, 3, 15, log("dark_oak_log"))
    d.set(2, 4, 15, slab("dark_oak"))
    d.set(3, 3, 15, "lever[face=wall,facing=east,powered=false]")
    # notice board (south-east)
    for x in (14, 16):
        for y in (2, 3, 4):
            d.set(x, y, 15, log("dark_oak_log"))
    d.set(15, 3, 15, "dark_oak_planks")
    d.set(15, 4, 15, "dark_oak_planks")
    for x in (14, 15, 16):
        d.set(x, 5, 15, slab("dark_oak"))
    d.sign(15, 3, 14, "north", ["MARKET DAY", "Tues & Sat", "fresh produce", ""], wood="dark_oak")
    d.sign(15, 4, 14, "north", ["VILLAGE FETE", "on the green", "", ""], wood="dark_oak")
    # bench facing the cross
    for x in range(7, 12):
        d.set(x, 2, 15, stairs("dark_oak", "south"))
        d.tag(x, 2, 15, "sit_out")
    d.set(6, 2, 15, trap("dark_oak", "west"))
    d.set(12, 2, 15, trap("dark_oak", "east"))
    # red pillar box by the entrance
    d.set(13, 2, 1, "red_concrete")
    d.set(13, 3, 1, "red_concrete")
    d.set(13, 4, 1, slab("deepslate_tile"))
    # corner oaks in brick-ringed beds, flower tubs, lamps
    for x, z in ((3, 2), (15, 2)):
        oak(d, x, z)
    for x, z, f in ((2, 1, "red_tulip"), (4, 1, "poppy"), (14, 1, "pink_tulip"), (16, 1, "white_tulip")):
        d.set(x, 1, z, "grass_block")
        d.set(x, 2, z, f)
    for x, z in ((2, 2), (4, 2), (14, 2), (16, 2), (3, 3), (15, 3), (3, 1), (15, 1)):
        d.set(x, 1, z, "grass_block")
    hw_lamp(d, 7, 3, arms=((-1, 0), (1, 0)))
    hw_lamp(d, 11, 3, arms=((-1, 0), (1, 0)))
    hw_lamp(d, 6, 13, arms=((0, 1),))
    hw_lamp(d, 12, 13, arms=((0, 1),))
    d.tag(9, 1, 5, "stand_out")


def grid(n, fill="G"):
    return [[fill] * n for _ in range(n)]


def paint(g, x1, z1, x2, z2, ch):
    """Mark a hand-chosen rectangle of a ground plan (paths, beds, pools)."""
    for z in range(z1, z2 + 1):
        for x in range(x1, x2 + 1):
            g[z][x] = ch


def rows_of(g):
    return ["".join(r) for r in g]


def hw_parklarge(d):
    """Village green: a hedged entrance with lamps, a Victorian bandstand on a brick base (railings, slate roof,
    band chairs and music) ringed by a gravel walk with benches on both sides, a maypole with streamers on the
    west lawn, a duck pond with reeds, lily pads, a duck house and a weeping willow, oaks on the green."""
    g = grid(25)
    paint(g, 11, 0, 13, 5, "g")
    paint(g, 10, 0, 10, 5, "K")
    paint(g, 14, 0, 14, 5, "K")
    for x in range(8, 17):                               # ring walk round the bandstand
        g[6][x] = g[14][x] = "g"
    for z in range(6, 15):
        g[z][8] = g[z][16] = "g"
    paint(g, 11, 15, 13, 16, "g")                        # walk to the pond
    paint(g, 13, 17, 13, 23, "g")
    paint(g, 12, 17, 12, 17, "g")
    pond = {16: (16, 21), 17: (15, 22), 18: (15, 23), 19: (15, 23), 20: (16, 23), 21: (16, 22), 22: (17, 21)}
    for z, (a, b) in pond.items():
        paint(g, a, z, b, z, "W")
    g[20][20] = "M"                                      # island stone for the duck house
    for x, z in ((14, 17), (14, 18), (15, 21), (16, 23), (23, 17), (22, 22), (23, 21), (15, 16)):
        g[z][x] = "s"                                    # sandy reed margins
    paint(g, 3, 11, 5, 13, "g")                          # maypole circle
    g[12][2] = g[12][6] = g[10][4] = g[14][4] = "g"
    paint(g, 7, 12, 7, 12, "g")
    paint(g, 4, 15, 4, 17, "g")                          # maypole -> tea garden
    paint(g, 1, 18, 7, 22, "g")                          # tea garden under the south-west oak
    plan(d, 1, rows_of(g), dict(HW, M="mossy_cobblestone", s="sand"))
    for z, (a, b) in pond.items():
        d.fill(a, 0, z, b, 0, z, "clay")
    # bandstand base and floor
    octo = {7: (10, 14), 8: (9, 15), 9: (9, 15), 10: (9, 15), 11: (9, 15), 12: (9, 15), 13: (10, 14)}
    for z, (a, b) in octo.items():
        for x in range(a, b + 1):
            edge = z in (7, 13) or x in (a, b)
            d.set(x, 2, z, "bricks" if edge else "dark_oak_planks")
    for x, z in ((10, 7), (14, 7), (9, 8), (15, 8), (9, 12), (15, 12), (10, 13), (14, 13)):
        for y in (3, 4, 5):
            d.set(x, y, z, "dark_oak_fence")
    for x in (11, 12, 13):
        d.set(x, 3, 7, "dark_oak_fence")
        d.set(x, 2, 14, stairs("stone_brick", "north"))
    for z in (9, 10, 11):
        d.set(9, 3, z, "dark_oak_fence")
        d.set(15, 3, z, "dark_oak_fence")
    d.hip(9, 7, 15, 13, 7, stairs="minecraft:deepslate_tile_stairs", cap="minecraft:deepslate_tile_slab")
    d.set(12, 11, 10, "dark_oak_fence")
    d.set(12, 9, 10, HANGING)
    for x in (11, 12, 13):
        d.set(x, 3, 9, stairs("dark_oak", "north"))
        d.tag(x, 3, 9, "sit_out")
    d.set(10, 3, 9, "note_block[instrument=harp,note=0,powered=false]")
    d.set(14, 3, 9, "note_block[instrument=harp,note=0,powered=false]")
    d.set(12, 3, 8, "jukebox[has_record=false]")
    # benches either side of the bandstand, on the lawn beside the ring walk
    for z in (9, 10, 11):
        for x, f in ((7, "west"), (17, "east")):
            d.set(x, 2, z, stairs("dark_oak", f))
            d.tag(x, 2, z, "sit_out")
    for x in (7, 17):
        d.set(x, 2, 8, trap("dark_oak", "north"))
        d.set(x, 2, 12, trap("dark_oak", "south"))
    # pond: bench on the west walk, reeds, lilies, duck house on its island, weeping willow
    for z in (18, 19, 20):
        d.set(14, 2, z, stairs("dark_oak", "west"))
        d.tag(14, 2, z, "sit_out")
    for x, z in ((14, 17), (15, 21), (16, 23), (23, 17), (22, 22), (15, 16)):
        d.set(x, 2, z, "sugar_cane[age=0]")
        d.set(x, 3, z, "sugar_cane[age=0]")
    for x, z in ((17, 18), (19, 17), (21, 19), (18, 21), (22, 20)):
        d.set(x, 2, z, LILY)
    d.set(20, 2, 20, "oak_fence")
    d.set(20, 3, 20, "oak_planks")
    d.set(20, 4, 20, slab("dark_oak"))
    d.set(20, 3, 19, trap("oak", "south"))
    willow(d, 21, 13)
    # maypole with four streamers and a flower ring
    for y in range(2, 10):
        d.set(4, y, 12, "birch_fence")
    d.set(4, 10, 12, "white_wool")
    for x, z, f, c in ((3, 12, "west", "red"), (5, 12, "east", "blue"), (4, 11, "north", "yellow"),
                       (4, 13, "south", "lime")):
        d.set(x, 10, z, f"{c}_wall_banner[facing={f}]")
    for x, z, f in ((2, 11, "red_tulip"), (6, 11, "cornflower"), (2, 13, "dandelion"), (6, 13, "pink_tulip"),
                    (3, 10, "oxeye_daisy"), (5, 10, "poppy"), (3, 14, "azure_bluet"), (5, 14, "allium")):
        d.set(x, 2, z, f)
    # entrance hedges, oaks, wildflowers
    for x in list(range(0, 10)) + list(range(15, 25)):
        d.set(x, 2, 0, leaves("oak"))
    oak(d, 4, 4)
    oak(d, 20, 4)
    oak(d, 4, 20)
    # tea garden: two tables with chairs under the oak, herbaceous border along the south hedge
    for x, z in ((2, 21), (6, 19)):
        d.set(x, 2, z, "dark_oak_fence")
        d.set(x, 3, z, "dark_oak_pressure_plate[powered=false]")
    for x, z, b in ((2, 20, "north"), (2, 22, "south"), (1, 21, "west"), (3, 21, "east"),
                    (6, 18, "north"), (6, 20, "south"), (5, 19, "west"), (7, 19, "east")):
        d.set(x, 2, z, stairs("oak", b))
        d.tag(x, 2, z, "sit_out")
    plan(d, 2, ["lprpl1prl2l"], HW, x0=1, z0=23)
    plan(d, 3, ["LPRPL.PRL.L"], HW, x0=1, z0=23)
    for z in range(1, 24):
        d.set(0, 2, z, leaves("oak"))
        d.set(24, 2, z, leaves("oak"))
    for x in range(25):
        d.set(x, 2, 24, leaves("oak"))
    for x, z, f in ((1, 8, "poppy"), (7, 3, "oxeye_daisy"), (18, 9, "dandelion"), (22, 8, "poppy"),
                    (9, 18, "cornflower"), (7, 22, "oxeye_daisy"), (1, 16, "azure_bluet"), (10, 20, "poppy")):
        d.set(x, 2, z, f)
    for x, z in ((10, 1), (14, 1), (8, 6), (16, 6), (8, 14), (16, 14), (12, 17)):
        hw_lamp(d, x, z)
    d.tag(12, 1, 5, "stand_out")


# ================================================================================================= CASCADIA
CAS = {"g": "grass_block", "p": "podzol", "c": "coarse_dirt", "d": "dirt_path", "o": "cobblestone",
       "m": "mossy_cobblestone", "a": "andesite", "T": "tuff", "W": WATER, "P": "spruce_planks",
       "X": log("stripped_spruce_log", "x"), "Z": log("stripped_spruce_log", "z"), "r": "rooted_dirt",
       "f": "fern", "F": tall("large_fern", "lower"), "U": tall("large_fern", "upper"),
       "b": "sweet_berry_bush[age=3]", "_": slab("mossy_cobblestone"), "-": slab("cobblestone"),
       "=": slab("spruce", "bottom"), "l": LILY, "h": "short_grass", "*": CAMPFIRE,
       "1": "lily_of_the_valley", "2": "cornflower", "3": "dandelion"}


def boulder(d, x, z, y=2, big=False):
    """River-rock boulder: mossy cobble core with an andesite shoulder (and a slab cap when big)."""
    d.set(x, y, z, "mossy_cobblestone")
    d.set(x + 1, y, z, "andesite")
    if big:
        d.set(x, y, z + 1, "cobblestone")
        d.set(x, y + 1, z, slab("mossy_cobblestone"))


def fire_pit(d, x, z):
    """Sunken fire pit: campfire in the ground, ring of cobble at ground level with slab rim around it."""
    d.set(x, 1, z, CAMPFIRE)
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            if (dx, dz) != (0, 0):
                d.set(x + dx, 1, z + dz, "cobblestone" if (dx + dz) % 2 else "mossy_cobblestone")
                d.set(x + dx, 2, z + dz, slab("cobblestone" if (dx + dz) % 2 else "mossy_cobblestone"))


def cas_smallpark(d):
    """Forest clearing: a dirt trail between lantern posts into a coarse-dirt clearing with a sunken stone
    fire pit, log benches on three sides, firs around the edge, boulders, ferns, berry bushes and a woodpile."""
    plan(d, 1, ["gpgggdgggpg",
                "ggpggdggpgg",
                "pggggdggggp",
                "gggccdccggg",
                "ggcccccccgg",
                "ggcccccccgg",
                "ggcccccccgg",
                "ggcccccccgg",
                "gggcccccggg",
                "ggpgggggpgg",
                "gpggpgpggpg"], CAS)
    fire_pit(d, 5, 6)
    plan(d, 2, ["...........",
                "...........",
                "...........",
                "..........b",
                "f..........",
                "..w.....e..",
                "..w.....e.m",
                "..w.....e.a",
                "....sss....",
                "...........",
                "..........."], CAS)
    for x, z in ((2, 4), (8, 4), (2, 8), (8, 8)):
        d.set(x, 2, z, log("spruce_log"))              # stump ends of the log benches
    d.set(2, 3, 4, LANTERN)
    d.set(10, 3, 6, slab("mossy_cobblestone"))
    boulder(d, 0, 5)
    d.set(0, 3, 5, slab("mossy_cobblestone"))
    # woodpile and chopping block at the back
    for x in (4, 5, 6):
        d.set(x, 2, 10, log("spruce_log", "x"))
        d.set(x, 3, 10, log("spruce_log", "x") if x != 6 else AIR)
    d.set(7, 2, 10, log("spruce_log"))
    d.set(3, 2, 10, "fern")
    fir(d, 1, 1, h=7 - 1)
    fir(d, 9, 1, h=5)
    fir(d, 1, 9, h=6)
    fir(d, 9, 9, h=6)
    for x, z, f in ((3, 2, "fern"), (7, 2, "fern"), (0, 7, "fern"), (10, 4, "fern"), (3, 9, "fern"),
                    (7, 9, "sweet_berry_bush[age=3]"), (4, 9, "short_grass"), (6, 0, "short_grass")):
        d.set(x, 2, z, f)
    cas_lamp(d, 4, 1)
    cas_lamp(d, 6, 1)
    d.tag(5, 1, 3, "stand_out")


def cas_mediumpark(d):
    """Picnic grounds: a log picnic shelter (gable roof, plank floor, long table with benches), a fire circle
    with log seats, a creek fed by a rock spring that winds west into a reedy pool, a plank footbridge with
    rail fences where the trail crosses it, firs, boulders and an overlook bench at the pool."""
    g = grid(17, "g")
    paint(g, 8, 0, 8, 16, "d")                           # trail
    for z in (0, 3, 6, 9, 14):
        g[z][7] = "c"
        g[z + 1][9] = "c"
    paint(g, 2, 2, 7, 7, "P")                            # shelter floor
    paint(g, 11, 2, 15, 6, "c")                          # fire circle clearing
    paint(g, 2, 11, 14, 12, "W")                         # creek
    paint(g, 1, 10, 4, 13, "W")                          # pool
    g[10][1] = g[13][1] = "m"
    paint(g, 15, 10, 16, 13, "m")                        # spring rocks
    g[11][15] = g[12][15] = "a"
    paint(g, 3, 14, 5, 14, "c")                          # overlook pad
    plan(d, 1, rows_of(g), CAS)
    d.fill(1, 0, 10, 14, 0, 13, "gravel")
    # spring: notch on a boulder pile spilling west into the creek head
    for z in (10, 11, 12, 13):
        d.set(15, 2, z, "mossy_cobblestone" if z % 2 else "cobblestone")
        d.set(16, 2, z, "andesite")
        d.set(16, 3, z, "mossy_cobblestone")
    d.set(15, 3, 10, "cobblestone")
    d.set(15, 3, 11, WATER)
    d.set(15, 3, 12, "mossy_cobblestone")
    d.set(16, 4, 11, slab("mossy_cobblestone"))
    d.set(15, 4, 12, "fern")
    # footbridge: slab deck over the creek with rail fences and lanterns on the end posts
    for x in range(6, 11):
        for z in (11, 12):
            d.set(x, 2, z, slab("spruce"))
    for z in (11, 12):
        d.set(6, 3, z, "spruce_fence")
        d.set(10, 3, z, "spruce_fence")
    d.set(6, 4, 11, LANTERN)
    d.set(10, 4, 12, LANTERN)
    # picnic shelter: log posts, gable roof along x, long table with benches both sides
    for x, z in ((2, 2), (7, 2), (2, 7), (7, 7)):
        for y in (2, 3, 4):
            d.set(x, y, z, log("spruce_log"))
    for x in range(2, 8):
        for z in (2, 7):
            d.set(x, 4, z, log("stripped_spruce_log", "x"))
    d.gable(2, 2, 7, 7, 5, axis="x", stairs="minecraft:spruce_stairs", ridge="minecraft:spruce_slab",
            end="minecraft:spruce_planks")
    for x in range(3, 7):
        d.set(x, 2, 5, slab("spruce", "top"))
        d.set(x, 2, 4, stairs("spruce", "north"))
        d.tag(x, 2, 4, "sit_out")
        d.set(x, 2, 6, stairs("spruce", "south"))
        d.tag(x, 2, 6, "sit_out")
    d.set(3, 6, 5, HANGING)
    d.set(6, 6, 5, HANGING)
    d.set(4, 3, 5, "potted_fern")
    # fire circle
    fire_pit(d, 13, 4)
    for z in (3, 4, 5):
        d.set(11, 2, z, stairs("spruce", "west"))
        d.tag(11, 2, z, "sit_out")
        d.set(15, 2, z, stairs("spruce", "east"))
        d.tag(15, 2, z, "sit_out")
    d.set(13, 2, 6, log("spruce_log", "x"))
    d.set(12, 2, 6, log("spruce_log", "x"))
    d.set(14, 2, 6, log("spruce_log", "x"))
    # overlook bench at the pool, reeds and lilies
    for x in (3, 4, 5):
        d.set(x, 2, 14, stairs("spruce", "south"))
        d.tag(x, 2, 14, "sit_out")
    for x, z in ((0, 11), (0, 12), (5, 10)):
        d.set(x, 2, z, "sugar_cane[age=0]")
        d.set(x, 3, z, "sugar_cane[age=0]")
    for x, z in ((2, 12), (3, 10), (11, 12)):
        d.set(x, 2, z, LILY)
    for x, z, h in ((1, 15, 6), (13, 15, 6), (15, 8, 5), (11, 1, 5), (15, 1, 6), (1, 8, 5)):
        fir(d, x, z, h=h)
    boulder(d, 5, 15, big=True)
    boulder(d, 11, 8)
    for x, z, f in ((6, 9, "fern"), (10, 9, "fern"), (9, 15, "fern"), (4, 16, "sweet_berry_bush[age=3]"),
                    (7, 16, "fern"), (12, 0, "fern"), (1, 0, "short_grass"), (5, 0, "fern"), (14, 8, "fern")):
        d.set(x, 2, z, f)
    cas_lamp(d, 9, 2, arm=(-1, 0))
    cas_lamp(d, 7, 14, arm=(1, 0))
    d.tag(8, 1, 2, "stand_out")


def cas_plaza(d):
    """Lodge commons: a spruce deck framed by stripped logs, a flagstone hearth court in front of a big
    river-rock outdoor fireplace with a timber mantel and chimney, log benches in a horseshoe facing the fire,
    a roofed notice board, a hitching rail with a water trough, potted ferns on stumps, firs and boulders in
    the corners, gallows lamps at the entrance."""
    g = grid(19, "P")
    for i in range(19):
        g[0][i] = g[18][i] = "g"
        g[i][0] = g[i][18] = "g"
    paint(g, 7, 0, 11, 0, "P")
    for x in range(1, 18):
        g[1][x] = "X"
        g[17][x] = "X"
    for z in range(2, 17):
        g[z][1] = "Z"
        g[z][17] = "Z"
    paint(g, 0, 14, 3, 18, "g")                          # back corners: fir islands
    paint(g, 15, 14, 18, 18, "g")
    g[14][3] = g[14][15] = "p"
    flag = ["omaoTomao",
            "aoTmoaToo",
            "mooaomaTo",
            "oTmoaoomo"]
    rows = rows_of(g)
    for z in range(11, 15):
        rows[z] = rows[z][:5] + flag[z - 11] + rows[z][14:]
    plan(d, 1, rows, CAS)
    # outdoor fireplace: river-rock body, timber mantel, campfire on the hearth, chimney
    for x in range(7, 12):
        for z in (15, 16, 17):
            for y in (2, 3, 4):
                d.set(x, y, z, ("mossy_cobblestone" if (x + y + z) % 3 == 0 else
                                "andesite" if (x + y + z) % 3 == 1 else "cobblestone"))
    for x in (8, 9, 10):
        for y in (2, 3):
            d.set(x, y, 15, AIR)
            d.set(x, y, 16, AIR)
        d.set(x, 4, 15, log("stripped_spruce_log", "x"))
    d.set(9, 2, 16, CAMPFIRE)
    d.set(8, 2, 16, "cobblestone")
    d.set(10, 2, 16, "cobblestone")
    for x in range(7, 12):
        d.set(x, 1, 15, "cobblestone")
        d.set(x, 1, 16, "cobblestone")
    for y in (5, 6):
        for x in (8, 9, 10):
            d.set(x, y, 16, "cobblestone" if x != 9 else "mossy_cobblestone")
            d.set(x, y, 17, "andesite" if x != 9 else "cobblestone")
    for y in (7, 8, 9):
        d.set(9, y, 16, "cobblestone" if y % 2 else "mossy_cobblestone")
        d.set(9, y, 17, "andesite")
    d.set(9, 10, 16, slab("cobblestone"))
    d.set(8, 5, 15, "potted_fern")
    d.set(10, 5, 15, LANTERN)
    # horseshoe of log benches facing the fire
    for x in (6, 7, 8, 10, 11, 12):
        d.set(x, 2, 11, stairs("spruce", "north"))
        d.tag(x, 2, 11, "sit_out")
    for z in (12, 13):
        d.set(5, 2, z, stairs("spruce", "west"))
        d.tag(5, 2, z, "sit_out")
        d.set(13, 2, z, stairs("spruce", "east"))
        d.tag(13, 2, z, "sit_out")
    for x, z in ((5, 11), (13, 11), (5, 14), (13, 14)):
        d.set(x, 2, z, log("spruce_log"))
    d.set(5, 3, 11, LANTERN)
    d.set(13, 3, 11, LANTERN)
    # notice board under a little shake roof (north-west)
    for x in (3, 5):
        for y in (2, 3, 4):
            d.set(x, y, 4, log("spruce_log"))
    d.set(4, 3, 4, "spruce_planks")
    d.set(4, 4, 4, "spruce_planks")
    for x in range(2, 7):
        d.set(x, 5, 4, slab("spruce"))
        d.set(x, 5, 3, stairs("spruce", "south"))
        d.set(x, 5, 5, stairs("spruce", "north"))
    d.sign(4, 3, 3, "north", ["CASCADIA", "COMMONS", "", ""], wood="spruce")
    d.sign(4, 4, 3, "north", ["Logging bee", "Saturday", "", ""], wood="spruce")
    # hitching rail and trough (north-east)
    d.set(13, 2, 4, log("spruce_log"))
    d.set(16, 2, 4, log("spruce_log"))
    for x in (14, 15):
        d.set(x, 2, 4, "spruce_fence")
    for x in (14, 15):
        d.set(x, 2, 5, "water_cauldron[level=3]")
    d.set(13, 3, 4, LANTERN)
    d.set(16, 2, 6, "hay_block[axis=y]")
    d.set(16, 2, 7, "barrel[facing=up,open=false]")
    # stumps with potted ferns along the deck, firs and boulders in the corners
    for x, z in ((3, 8), (15, 8), (3, 12), (15, 12)):
        d.set(x, 2, z, log("spruce_log"))
        d.set(x, 3, z, "potted_fern")
    fir(d, 2, 16, h=8)
    fir(d, 16, 16, h=7)
    for x, z, b in ((4, 17, "mossy_cobblestone"), (0, 13, "andesite"), (18, 13, "mossy_cobblestone"),
                    (14, 16, "fern"), (4, 15, "fern"), (0, 5, "fern"), (18, 6, "sweet_berry_bush[age=3]"),
                    (0, 9, "sweet_berry_bush[age=3]"), (18, 10, "fern"), (15, 18, "fern")):
        d.set(x, 2, z, b)
    d.set(4, 3, 17, slab("mossy_cobblestone"))
    # log gateway with a hanging sign over the entrance
    for x in (6, 12):
        for y in range(2, 6):
            d.set(x, y, 0, log("spruce_log"))
    for x in range(5, 14):
        d.set(x, 6, 0, log("stripped_spruce_log", "x"))
    d.set(6, 6, 0, log("spruce_log"))
    d.set(12, 6, 0, log("spruce_log"))
    d.set(9, 5, 0, "spruce_hanging_sign[attached=false,rotation=8,waterlogged=false]")
    d.sign(9, 5, 0, "north", ["", "COMMONS", "", ""], wood="spruce", hanging=True)
    te = d.bp.tile_entities.get((9, 5, 0))
    d.set(9, 5, 0, "spruce_hanging_sign[attached=false,rotation=8,waterlogged=false]", te)
    # woodpile beside the fireplace, fern beds in the deck
    for z in (15, 16, 17):
        for x in (12, 13):
            d.set(x, 2, z, log("spruce_log", "z"))
        d.set(12, 3, z, log("spruce_log", "z"))
    d.set(13, 3, 16, slab("spruce"))
    for x, z, f in ((2, 9, "fern"), (2, 10, "sweet_berry_bush[age=3]"), (16, 9, "sweet_berry_bush[age=3]"),
                    (16, 10, "fern")):
        d.set(x, 1, z, "podzol")
        d.set(x, 2, z, f)
    cas_lamp(d, 6, 1, arm=(1, 0))
    cas_lamp(d, 12, 1, arm=(-1, 0))
    cas_lamp(d, 1, 9)
    cas_lamp(d, 17, 9)
    d.tag(9, 1, 6, "stand_out")


def cas_parklarge(d):
    """Falls park: a winding trail from the street past a trailhead board, a log lean-to facing a fire circle,
    an overlook bench at a pond fed by a waterfall spilling from a mossy rock bluff, a creek with a railed
    footbridge running west into a marsh with reeds, a picnic table under the firs, boulders, ferns, berries."""
    g = grid(25, "g")
    trail = [(12, z) for z in range(0, 5)] + [(11, z) for z in range(4, 10)] + [(10, z) for z in range(9, 14)] \
        + [(11, z) for z in range(13, 19)] + [(12, z) for z in range(18, 22)] + [(13, 21), (14, 21)]
    for x, z in trail:
        g[z][x] = "d"
    for x, z in ((13, 1), (11, 3), (12, 6), (10, 7), (9, 10), (11, 11), (12, 17), (13, 19), (11, 20)):
        g[z][x] = "c"
    pond = {8: (16, 21), 9: (15, 22), 10: (14, 22), 11: (14, 21), 12: (14, 21), 13: (15, 20), 14: (14, 18)}
    for z, (a, b) in pond.items():
        paint(g, a, z, b, z, "W")
    paint(g, 3, 15, 15, 16, "W")                         # creek
    marsh = {14: (2, 5), 15: (1, 3), 16: (1, 3), 17: (1, 6), 18: (2, 5)}
    for z, (a, b) in marsh.items():
        paint(g, a, z, b, z, "W")
    for x, z in ((4, 16), (5, 15), (13, 14), (6, 16)):
        g[z][x] = "W"
    paint(g, 2, 4, 7, 9, "P")                            # lean-to floor
    paint(g, 7, 5, 10, 9, "c")                           # fire clearing
    paint(g, 15, 19, 20, 23, "c")                        # picnic clearing
    for x, z in ((3, 22), (7, 20), (21, 16), (1, 11), (23, 12), (8, 22)):
        g[z][x] = "p"
    plan(d, 1, rows_of(g), CAS)
    for z, (a, b) in list(pond.items()) + list(marsh.items()):
        d.fill(a, 0, z, b, 0, z, "gravel")
    d.fill(3, 0, 15, 15, 0, 16, "gravel")
    for x, z in ((4, 16), (5, 15), (13, 14), (6, 16)):
        d.set(x, 0, z, "gravel")
    # rock bluff with the falls (north-east): hand-laid courses
    plan(d, 2, ["mooaTmo",
                "oamoaom",
                "maoTomo",
                "oTmaomo",
                "amooTam",
                "omamoao",
                ".m.o.a."], CAS, x0=17, z0=1)
    plan(d, 3, [".omaoTm",
                ".maoomo",
                ".oTmaoa",
                ".moaomo",
                "..aomTo",
                "..omaom",
                "...o..."], CAS, x0=17, z0=1)
    plan(d, 4, ["..moaom",
                "..oamTo",
                "..mooma",
                "..aomoo",
                "...moa.",
                "...o.m.",
                "...m..."], CAS, x0=17, z0=1)
    plan(d, 5, ["...mmo.",
                "...oam.",
                "...amo.",
                "...mo..",
                "...o...",
                "...m...",
                "...~..."], dict(CAS, **{"~": WATER}), x0=17, z0=1)
    d.set(19, 5, 6, "mossy_cobblestone")
    d.set(21, 5, 7, "cobblestone")
    d.set(19, 5, 7, "mossy_cobblestone")
    d.set(20, 6, 6, slab("mossy_cobblestone"))
    for x, y, z, f in ((19, 4, 3, "fern"), (18, 3, 5, "fern"), (17, 2, 7, "fern"), (23, 6, 4, "fern")):
        if d.air(x, y, z):
            d.set(x, y, z, f)
    fir(d, 22, 2, y=6, h=5)
    # lean-to: log back and side walls, shed roof falling to the front posts, bench facing the fire
    for z in range(4, 10):
        for y in (2, 3, 4, 5):
            d.set(2, y, z, log("spruce_log", "z") if y in (3, 5) else log("stripped_spruce_log", "z"))
    for x in range(3, 7):
        for z in (4, 9):
            for y in (2, 3):
                d.set(x, y, z, log("spruce_log", "x"))
    for z in (4, 9):
        d.set(6, 4, z, log("spruce_log"))
    for z in range(3, 11):
        d.set(2, 6, z, stairs("spruce", "west"))
        d.set(3, 6, z, stairs("spruce", "west"))
        d.set(4, 5, z, stairs("spruce", "west"))
        d.set(5, 5, z, stairs("spruce", "west"))
        d.set(6, 5, z, slab("spruce"))
        d.set(7, 4, z, stairs("spruce", "west"))
    for z in (5, 6, 7, 8):
        d.set(3, 2, z, stairs("spruce", "west"))
        d.tag(3, 2, z, "sit_out")
    d.set(4, 4, 6, HANGING)
    d.set(3, 3, 5, AIR)
    # fire circle in front of the lean-to
    fire_pit(d, 9, 7)
    for x in (8, 10):
        d.set(x, 2, 5, log("spruce_log", "x"))
    d.set(9, 2, 5, stairs("spruce", "north"))
    d.tag(9, 2, 5, "sit_out")
    d.set(9, 2, 9, stairs("spruce", "south"))
    d.tag(9, 2, 9, "sit_out")
    # overlook bench at the pond's west shore, facing the falls
    for z in (9, 10, 11):
        d.set(13, 2, z, stairs("spruce", "west"))
        d.tag(13, 2, z, "sit_out")
    d.set(13, 2, 8, log("spruce_log"))
    d.set(13, 3, 8, LANTERN)
    # footbridge over the creek
    for x in (10, 11, 12):
        for z in (14, 15, 16, 17):
            d.set(x, 2, z, slab("spruce"))
    for z in (15, 16):
        d.set(10, 3, z, "spruce_fence")
        d.set(12, 3, z, "spruce_fence")
    for x, z in ((10, 14), (12, 14), (10, 17), (12, 17)):
        d.set(x, 2, z, log("spruce_log"))
        d.set(x, 3, z, "spruce_fence")
    d.set(10, 4, 14, LANTERN)
    d.set(12, 4, 17, LANTERN)
    # marsh: reeds, lilies; pond lilies
    for x, z in ((0, 15), (0, 16), (6, 14), (7, 17), (4, 19), (2, 13)):
        d.set(x, 2, z, "sugar_cane[age=0]")
        d.set(x, 3, z, "sugar_cane[age=0]")
    for x, z in ((2, 16), (4, 17), (8, 15), (17, 11), (20, 12), (16, 9)):
        d.set(x, 2, z, LILY)
    # picnic table in the clearing to the south-east
    for x in (16, 17, 18, 19):
        d.set(x, 2, 21, slab("spruce", "top"))
        d.set(x, 2, 20, stairs("spruce", "north"))
        d.tag(x, 2, 20, "sit_out")
        d.set(x, 2, 22, stairs("spruce", "south"))
        d.tag(x, 2, 22, "sit_out")
    d.set(17, 3, 21, "potted_fern")
    # trailhead board
    for x in (14, 16):
        for y in (2, 3, 4):
            d.set(x, y, 2, log("spruce_log"))
    d.set(15, 3, 2, "spruce_planks")
    d.set(15, 4, 2, "spruce_planks")
    for x in (13, 14, 15, 16, 17):
        d.set(x, 5, 2, slab("spruce"))
    d.sign(15, 3, 1, "north", ["CASCADE FALLS", "PARK", "", ""], wood="spruce")
    d.sign(15, 4, 1, "north", ["falls  ->", "lean-to  <-", "", ""], wood="spruce")
    # forest: firs placed around the clearings, boulders, ferns, berries
    for x, z, h in ((1, 1, 6), (6, 1, 6), (2, 20, 8), (5, 22, 7), (9, 20, 6), (22, 20, 8), (23, 15, 6),
                    (16, 16, 6), (8, 12, 5), (1, 11, 6), (23, 23, 5)):
        fir(d, x, z, h=h)
    for x, z, big in ((14, 6, True), (5, 12, False), (21, 17, True), (8, 23, False), (17, 6, False)):
        boulder(d, x, z, big=big)
    for x, z, f in ((4, 2, "fern"), (9, 3, "fern"), (15, 4, "fern"), (13, 6, "large_fern"), (6, 11, "fern"),
                    (9, 17, "fern"), (14, 18, "sweet_berry_bush[age=3]"), (3, 23, "sweet_berry_bush[age=3]"),
                    (11, 23, "fern"), (23, 22, "fern"), (19, 17, "fern"), (24, 10, "fern"),
                    (8, 2, "short_grass"), (16, 0, "short_grass")):
        if f == "large_fern":
            d.set(x, 2, z, tall("large_fern", "lower"))
            d.set(x, 3, z, tall("large_fern", "upper"))
        else:
            d.set(x, 2, z, f)
    cas_lamp(d, 13, 3, arm=(-1, 0))
    cas_lamp(d, 9, 11, arm=(1, 0))
    cas_lamp(d, 13, 19, arm=(-1, 0))
    d.tag(12, 1, 3, "stand_out")
