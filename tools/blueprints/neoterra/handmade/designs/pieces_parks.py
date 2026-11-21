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
    # south-east lawn: birch and an allium meadow
    birch(d, 21, 21, h=6)
    for x, z, f in ((18, 20, "allium"), (19, 22, "white_tulip"), (23, 20, "allium"), (18, 23, "cornflower"),
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
