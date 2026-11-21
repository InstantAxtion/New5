"""
Grand project: the HANGING GARDENS (children grow up faster, farmers harvest more) with two wing child huts.

Neoterra   "Verdant Sky Gardens": a vertical-forest tower (stacked floor plates with staggered tree planters on
           cantilevered balconies, one use per floor: lobby, seed library, children's garden, hydroponic farm,
           cafe, research lab, sky lounge, roof forest) in a grove of glowing super-trees joined by a sky walk,
           a reflecting pool with glass water columns and, from L4, a dragonfly lake.  Wings = glass biodomes
           (white ribbed geodesic domes; at L4-5 a planted mountain with an indoor waterfall).
Hearthwood "Hearthwood Palm House": a great Victorian glass palm house (white cast-iron ribs, curved glass
           roofs, brick plinth) in a walled, terraced English garden: tiered fountain, parterres, canal pond,
           a raised terrace walk with balustrade; inside palms, a lily pool, a spiral stair to the gallery.
           Wings = octagonal glass orangery pavilions with citrus trees in tubs.
Cascadia   "Cascade Gardens": terraced rock gardens climbing a slope, a stream that falls from a spring pool
           down every terrace into the front pond, timber pergolas, a log lodge with a glass conservatory,
           a tea house, rope bridge and lookout as the gardens grow.  Wings = timber-framed potting
           glasshouses on river-rock footings.

Water: only source blocks; every pool is rimmed, every waterfall is a column of sources in a rock notch whose
spill drops straight into a pool (check_water() in this file verifies it while designing).
Wings are pasted without rotation (both share one blueprint), so they are drawn symmetric about their centre.
"""
from hm import Design, design, AIR

WATER = "water[level=0]"
ROOT = "monuments/"
WPATH = ROOT + "hanginggardenswing0.blueprint"
SOLIDSUB = "structurize:blocksolidsubstitution"
D4 = {"north": (0, -1), "south": (0, 1), "west": (-1, 0), "east": (1, 0)}
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}


# ============================================================================================ small helpers
def stair(b, facing, half="bottom", shape="straight"):
    return f"{b}[facing={facing},half={half},shape={shape},waterlogged=false]"


def slab(b, t="bottom"):
    return f"{b}[type={t},waterlogged=false]"


def lantern(hanging=False):
    return f"lantern[hanging={'true' if hanging else 'false'},waterlogged=false]"


def lv(kind):
    return f"{kind}_leaves[distance=1,persistent=true,waterlogged=false]"


def logy(kind):
    return f"{kind}[axis=y]"


def trap(wood, facing, half="bottom", open_=False):
    return f"{wood}_trapdoor[facing={facing},half={half},open={'true' if open_ else 'false'},powered=false,waterlogged=false]"


def disc(r, cx, cz):
    out = set()
    for x in range(int(cx - r - 1), int(cx + r + 2)):
        for z in range(int(cz - r - 1), int(cz + r + 2)):
            if (x - cx) ** 2 + (z - cz) ** 2 <= r * r + 0.3:
                out.add((x, z))
    return out


def ring(r, cx, cz):
    cells = disc(r, cx, cz)
    return {(x, z) for (x, z) in cells
            if any((x + dx, z + dz) not in cells for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))}


def shelf(face, pat=(1, 0, 1, 1, 0, 1)):
    return (f"chiseled_bookshelf[facing={face}," +
            ",".join(f"slot_{i}_occupied={'true' if o else 'false'}" for i, o in enumerate(pat)) + "]")


def dpot(face="north"):
    return f"decorated_pot[cracked=false,facing={face},waterlogged=false]"


SOLIDISH_NO = ("air", "stairs", "slab", "lantern", "torch", "door", "carpet", "flower", "pot", "rail", "chain",
               "bed", "sign", "banner", "button", "plate", "rod", "water", "trapdoor", "leaves", "sapling", "grass",
               "fern", "bush", "lily", "cane", "vine", "candle", "bell", "azalea", "substitution", "head", "campfire")


def connect_walls(d):
    """Set the side connections of every *_wall block (the toolkit only does panes and fences)."""
    bp = d.bp
    for x, y, z, s in list(bp.blocks()):
        name = s.split("[")[0]
        if not name.endswith("_wall") or "sign" in name or "banner" in name or "torch" in name:
            continue
        sides = {}
        for k, (dx, dz) in D4.items():
            if not bp.inside(x + dx, y, z + dz):
                sides[k] = "none"
                continue
            n = bp.get(x + dx, y, z + dz).split("[")[0].split(":")[-1]
            conn = n.endswith("_wall") or n.endswith("fence") or n.endswith("pane") or n.endswith("bars") or \
                not any(t in n for t in SOLIDISH_NO)
            sides[k] = "low" if conn else "none"
        above = bp.get(x, y + 1, z) if bp.inside(x, y + 1, z) else AIR
        straight = (sides["north"] == sides["south"] == "low" and sides["east"] == sides["west"] == "none") or \
                   (sides["east"] == sides["west"] == "low" and sides["north"] == sides["south"] == "none")
        up = "false" if straight and above == AIR else "true"
        if above != AIR and above.split("[")[0].endswith("_wall"):
            for k in sides:
                if sides[k] == "low":
                    sides[k] = "tall"
            up = "true" if not straight else "false"
        bp.grid[y][z][x] = (f"{name}[east={sides['east']},north={sides['north']},south={sides['south']},"
                            f"up={up},waterlogged=false,west={sides['west']}]")


def check_water(d):
    """Design-time check (no placement): every water source must be held by solid blocks / water on its sides
    and below, or spill into a cell whose fall lands in water. Returns a list of leaks."""
    bp = d.bp
    leaks = []

    def name(x, y, z):
        return bp.get(x, y, z).split("[")[0].split(":")[-1] if bp.inside(x, y, z) else "outside"

    def holds(n):
        return n not in ("air", "outside") and not any(k in n for k in ("door", "carpet", "torch", "flower",
                                                                       "pressure_plate", "sign", "lantern",
                                                                       "rail", "fern", "short_grass"))
    for x, y, z, s in bp.blocks():
        if not s.startswith("minecraft:water"):
            continue
        if not holds(name(x, y - 1, z)) and name(x, y - 1, z) != "water":
            leaks.append((x, y, z, "below"))
        for dx, dz in D4.values():
            n = name(x + dx, y, z + dz)
            if n == "water" or holds(n):
                continue
            yy = y
            while name(x + dx, yy - 1, z + dz) == "air":
                yy -= 1
            if name(x + dx, yy - 1, z + dz) != "water":
                leaks.append((x, y, z, (dx, dz)))
    return leaks


# ------------------------------------------------------------------------------------- one-piece placers
def put(d, x, y, z, st):
    d.set(x, y, z, st)


def pot(d, x, y, z, plant):
    d.set(x, y, z, f"potted_{plant}")


def lamp_chain(d, x, y, z, top):
    """A lantern hung at (x, y, z) on a chain reaching up to the ceiling block at `top`."""
    for k in range(y + 1, top):
        d.set(x, k, z, "chain[axis=y,waterlogged=false]")
    d.set(x, y, z, lantern(True))


def bench(d, x, y, z, facing, wood, length=2, along="x", arms=True):
    """Park bench of `length` stair seats whose backs are on side `facing`, trapdoor arms at the ends."""
    dx, dz = (1, 0) if along == "x" else (0, 1)
    for i in range(length):
        d.chair(x + dx * i, y, z + dz * i, facing, wood)
    if arms:
        for (ax, az, f) in ((x - dx, z - dz, "west" if along == "x" else "north"),
                            (x + dx * length, z + dz * length, "east" if along == "x" else "south")):
            if d.bp.inside(ax, y, az) and d.air(ax, y, az):
                d.set(ax, y, az, trap(wood, f, open_=True))


def lamppost(d, x, z, y, h, post, head):
    for k in range(h):
        d.set(x, y + k, z, post)
    d.set(x, y + h, z, head)


def tree(d, x, y, z, h, log, leaves, r=2, top_extra=True):
    """One round-crowned tree on the ground cell below (x, y, z)."""
    for k in range(h):
        d.set(x, y + k, z, logy(log))
    top = y + h
    for dy in range(-1, 2):
        rr = r if dy < 1 else r - 1
        for dx in range(-rr, rr + 1):
            for dz in range(-rr, rr + 1):
                if abs(dx) + abs(dz) > rr + (1 if dy < 0 else 0):
                    continue
                xx, zz, yy = x + dx, z + dz, top + dy
                if d.bp.inside(xx, yy, zz) and d.air(xx, yy, zz):
                    d.set(xx, yy, zz, lv(leaves))
    if top_extra and d.bp.inside(x, top + 2, z) and d.air(x, top + 2, z):
        d.set(x, top + 2, z, lv(leaves))
    d.set(x, top - 1, z, logy(log))


def palm(d, x, y, z, h, fronds=4, log="jungle_log", leaves="jungle"):
    """Palm: slim trunk, a crown of drooping fronds (leaves arms 2-3 long, tips one lower)."""
    for k in range(h):
        d.set(x, y + k, z, logy(log))
    t = y + h
    d.set(x, t, z, lv(leaves))
    arms = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if fronds > 4:
        arms += [(1, 1), (-1, -1), (1, -1), (-1, 1)]
    for dx, dz in arms:
        for k in (1, 2):
            if d.air(x + dx * k, t, z + dz * k):
                d.set(x + dx * k, t, z + dz * k, lv(leaves))
        tx, tz = x + dx * 3, z + dz * 3
        if abs(dx) + abs(dz) == 1 and d.bp.inside(tx, t - 1, tz) and d.air(tx, t - 1, tz):
            d.set(tx, t - 1, tz, lv(leaves))
    d.set(x, t + 1, z, lv(leaves))


def shrub(d, x, y, z, leaves, kind="ball"):
    d.set(x, y, z, lv(leaves))
    if kind == "tall":
        d.set(x, y + 1, z, lv(leaves))


def flower(d, x, y, z, f):
    """Flower on the soil block at y-1 (soil must already be there)."""
    if f in ("peony", "lilac", "rose_bush", "sunflower", "tall_grass", "large_fern"):
        d.set(x, y, z, f"{f}[half=lower]")
        d.set(x, y + 1, z, f"{f}[half=upper]")
    else:
        d.set(x, y, z, f)


# ---------------------------------------------------------------------------------------- room plans
# Hand-drawn furniture plans: one character per cell (rows north -> south, columns west -> east).
# ' ' / '.' = leave free.  Everything else is one hand-placed piece (see piece()).
def piece(d, ch, x, y, z, S, face):
    w = S["wood"]
    f = face.get(ch, "north")
    if ch in "1234":
        d.chair(x, y, z, {"1": "north", "2": "east", "3": "south", "4": "west"}[ch], w)
    elif ch == "T":
        d.table(x, y, z, w)
    elif ch == "t":
        d.set(x, y, z, f"{w}_fence")
        d.set(x, y + 1, z, "candle[candles=3,lit=false,waterlogged=false]")
    elif ch == "c":
        d.set(x, y, z, slab(S["counter"], "top"))
    elif ch == "e":
        d.set(x, y, z, slab(S["counter"], "top"))
        d.set(x, y + 1, z, dpot(f))
    elif ch == "g":
        d.set(x, y, z, slab(S["counter"], "top"))
        d.set(x, y + 1, z, "potted_red_tulip")
    elif ch == "i":
        d.set(x, y, z, slab(S["counter"], "top"))
        d.set(x, y + 1, z, "potted_fern")
    elif ch == "j":
        d.set(x, y, z, slab(S["counter"], "top"))
        d.set(x, y + 1, z, lantern())
    elif ch == "r":
        d.set(x, y, z, slab(S["counter"], "top"))
        d.set(x, y + 1, z, "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]")
    elif ch == "a":
        pot(d, x, y, z, "azalea_bush")
    elif ch == "A":
        pot(d, x, y, z, "flowering_azalea_bush")
    elif ch == "f":
        pot(d, x, y, z, "fern")
    elif ch == "z":
        pot(d, x, y, z, "bamboo")
    elif ch == "u":
        pot(d, x, y, z, "red_tulip")
    elif ch == "y":
        pot(d, x, y, z, "blue_orchid")
    elif ch == "x":
        pot(d, x, y, z, "cactus")
    elif ch == "L":
        d.set(x, y, z, "flowering_azalea")
    elif ch == "l":
        d.set(x, y, z, "azalea")
    elif ch == "P":
        d.set(x, y, z, dpot(f))
    elif ch == "b":
        d.set(x, y, z, "barrel[facing=up,open=false]")
    elif ch == "K":
        d.set(x, y, z, f"barrel[facing={f},open=false]")
    elif ch == "B":
        d.bookshelf(x, y, z, 2)
    elif ch == "S":
        d.set(x, y, z, shelf(f))
        d.set(x, y + 1, z, shelf(f, (0, 1, 1, 1, 1, 0)))
    elif ch == "s":
        d.set(x, y, z, shelf(f))
    elif ch == "k":
        d.set(x, y, z, "crafting_table")
    elif ch == "m":
        d.set(x, y, z, "cartography_table")
    elif ch == "n":
        d.set(x, y, z, "fletching_table")
    elif ch == "Q":
        d.set(x, y, z, f"lectern[facing={f},has_book=true,powered=false]")
    elif ch == "W":
        d.set(x, y, z, "water_cauldron[level=3]")
    elif ch == "C":
        d.set(x, y, z, "composter[level=4]")
    elif ch == "M":
        d.set(x, y, z, f"loom[facing={f}]")
    elif ch == "O":
        d.set(x, y, z, f"smoker[facing={f},lit=false]")
    elif ch == "F":
        d.set(x, y, z, f"furnace[facing={f},lit=false]")
    elif ch == "J":
        d.set(x, y, z, "jukebox[has_record=false]")
    elif ch == "N":
        d.set(x, y, z, "note_block[instrument=harp,note=0,powered=false]")
    elif ch == "H":
        d.set(x, y, z, "hay_block[axis=y]")
    elif ch == "h":
        d.set(x, y, z, "hay_block[axis=x]")
        d.set(x, y + 1, z, "hay_block[axis=z]")
    elif ch == "G":
        d.set(x, y, z, "moss_block")
        d.set(x, y + 1, z, "fern")
    elif ch == "E":
        d.set(x, y, z, "moss_block")
        d.set(x, y + 1, z, "azalea")
    elif ch == "Y":
        d.set(x, y, z, "farmland[moisture=7]")
        d.set(x, y + 1, z, "wheat[age=6]")
    elif ch == "U":
        d.set(x, y, z, "farmland[moisture=7]")
        d.set(x, y + 1, z, "carrots[age=5]")
    elif ch == "V":
        d.set(x, y, z, "farmland[moisture=7]")
        d.set(x, y + 1, z, "potatoes[age=6]")
    elif ch == "X":
        d.set(x, y, z, "farmland[moisture=7]")
        d.set(x, y + 1, z, "beetroots[age=3]")
    elif ch == "w":
        d.set(x, y, z, WATER)
    elif ch in "<>^v":
        fac = {"<": "west", ">": "east", "^": "north", "v": "south"}[ch]
        d.bed(x, y, z, fac, S.get("bedcol"))
    elif ch == "R":
        d.set(x, y, z, S["rug"][0] + "_carpet")
    elif ch == "o":
        d.set(x, y, z, S["rug"][1] + "_carpet")
    elif ch == "q":
        d.set(x, y, z, S["rug"][2 if len(S["rug"]) > 2 else 0] + "_carpet")
    elif ch == "#":
        d.set(x, y, z, S["block"])
    elif ch == "|":
        d.set(x, y, z, S["block"])
        d.set(x, y + 1, z, S["block"])
    elif ch == "=":
        d.set(x, y, z, slab(S["counter"], "bottom"))
    elif ch == "p":
        d.set(x, y, z, "white_carpet")
    elif ch == "d":
        d.set(x, y, z, "yellow_carpet")
    elif ch == "%":
        d.set(x, y, z, "lime_carpet")
    elif ch == "&":
        d.set(x, y, z, "light_blue_carpet")
    elif ch == "*":
        d.set(x, y, z, "pink_carpet")
    elif ch == "Z":
        d.set(x, y, z, "bee_nest[facing=south,honey_level=3]")
    elif ch == "D":
        d.set(x, y, z, "big_dripleaf[facing=north,tilt=none,waterlogged=false]")
    elif ch == "I":
        d.set(x, y, z, "smithing_table")
    elif ch == "8":
        d.set(x, y, z, "grindstone[face=floor,facing=north]")
    elif ch == "9":
        d.set(x, y, z, f"stonecutter[facing={f}]")
    elif ch == "0":
        d.set(x, y, z, "dried_kelp_block")
    elif ch == "5":
        d.set(x, y, z, "melon")
    elif ch == "6":
        d.set(x, y, z, "pumpkin")
    elif ch == "7":
        d.set(x, y, z, "white_wool")
        d.set(x, y + 1, z, "brown_carpet")
    else:
        extra = S.get("extra", {})
        if ch in extra:
            v = extra[ch]
            if callable(v):
                v(d, x, y, z)
            else:
                d.set(x, y, z, v)
        else:
            raise ValueError(f"plan symbol {ch!r}")


def plan(d, x0, y, z0, rows, S, face=None, extra=None):
    S = dict(S)
    if extra:
        S["extra"] = extra
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch in " .":
                continue
            piece(d, ch, x0 + c, y, z0 + r, S, face or {})


def lights(d, cells, y, block):
    """Recessed / hanging lights at the hand-chosen cells."""
    for x, z in cells:
        d.set(x, y, z, block)


def wing_design(pack, rel, size):
    return Design(pack, rel, size, gy=0, paving=None)


def place_wings(d, res, wsize, whut, top=None):
    for (x1, z1) in res:
        d.reserve(x1, 1, z1, x1 + wsize[0] - 1, (top or d.sy - 1), z1 + wsize[2] - 1)
        d.child_hut(x1 + whut[0], whut[1] + 1, z1 + whut[2], WPATH)


# =============================================================================================================
#                                     NEOTERRA  -  VERDANT SKY GARDENS
# =============================================================================================================
NT = dict(size=(47, 58, 53), wsize=(13, 18, 13), whut=(4, 1, 4), res=((1, 2), (33, 2)))
NT_FLOORS = {1: 2, 2: 3, 3: 4, 4: 6, 5: 7}
TX1, TX2, TZ1, TZ2 = 17, 29, 19, 31                     # tower walls
NS = dict(wood="birch", counter="smooth_stone_slab", rug=("light_gray", "cyan", "white"), block="white_concrete",
          bedcol="cyan")
GRASS = "grass_block[snowy=false]"

# furniture plans of the tower floors (interior x18..28, z20..30).  Even floors enter from the stair shaft at
# (28, 21), odd floors at (28, 26).
NT_PLANS = {
    0: dict(name="lobby", rows=[           # visitor hall: reception desk with the hut behind it, lounge, kiosk
        "L.f.....f.L",
        "...........",
        "a.......Q.z",
        "...........",
        "...ccecc...",
        "...c.3.c...",
        "4oT2....c.S",
        "4oo2....i.S",
        "4oT2....c.S",
        "a.........a",
        "GEGEGLGEGEG"], face={"Q": "north", "S": "west", "e": "north"},
        lights=[(20, 22), (26, 22), (23, 23), (20, 28), (26, 28)]),
    1: dict(name="seed library", rows=[    # seed library & herbarium: shelves, reading tables, seed drawers
        "SSSS.SSSS.A",
        "...........",
        "B.111.111.y",
        "B.TtT.TtT..",
        "B.333.333..",
        "...........",
        "Q..........",
        "B.KbbK.....",
        "B.bKKb.mk.a",
        "B..........",
        "SSS.AzA.SSS"], face={"S": "south", "Q": "east", "K": "north"},
        face2={"S": "north"}, lights=[(21, 22), (25, 22), (21, 28), (25, 28), (27, 25)]),
    2: dict(name="children's garden", rows=[   # nursery: play rug, music corner, sand pit, nap beds, kids' table
        "A..J.N..PPA",
        "..d%d%d%...",
        ".&d%d%d%&..",
        "..&*&*&*...",
        "...........",
        "4T2.....~~~",
        "4T2.....~~~",
        "........~~~",
        "...........",
        "..........y",
        "(b)b(b)b(.f"], face={"P": "south"},
        lights=[(20, 22), (24, 22), (20, 27), (27, 27), (24, 25)]),
    3: dict(name="hydroponic farm", rows=[   # crop beds with water channels, composters, seed barrels
        "CbK.....b.b",
        "..#...#....",
        ".YwY.UwU.b.",
        ".YwY.UwU.b.",
        ".VwV.XwX...",
        ".VwV.XwX.kc",
        ".YwY.UwU...",
        ".UwU.YwY...",
        ".XwX.VwV.Wc",
        "..#...#....",
        "bbK.C.KbbHH"], face={"K": "up"},
        lights=[(20, 23), (24, 23), (20, 27), (24, 27), (27, 22)]),
    4: dict(name="cafe", rows=[             # garden cafe: kitchen line, serving counter, tables of four
        "OcWccij....",
        "...........",
        "cccc.cc....",
        "...........",
        ".1.....1...",
        "4T2...4T2..",
        ".3.....3...",
        "....1......",
        "...4T2....a",
        "....3......",
        "a.G.E.G.a.z"], face={"O": "south"},
        lights=[(20, 21), (24, 21), (19, 25), (25, 25), (22, 28), (27, 28)]),
    5: dict(name="research lab", rows=[    # botanical lab: brewing benches, trial plots, lecterns, sample bins
        "SSS.rcr.cWc",
        "...........",
        "cic.cec....",
        "3.3.3.3....",
        "...........",
        "GGG..EEE...",
        "GGG..EEE...",
        "...........",
        "Q.m.k.n...b",
        "...........",
        "bKb.CCC..bK"], face={"S": "south", "Q": "east", "K": "west"},
        lights=[(19, 22), (24, 22), (20, 27), (25, 27), (27, 24)]),
    6: dict(name="sky lounge", rows=[       # bar with stools, two sofa groups, music, planters
        "jcccc.....A",
        ".3333......",
        "...........",
        ".RRR...RRR.",
        "4RTR2.4RTR2",
        "4RRR2.4RRR2",
        ".RRR...RRR.",
        "...........",
        "J.........a",
        "...........",
        "A.a.L.a.A.z"], face={},
        lights=[(21, 21), (25, 22), (20, 25), (26, 25), (23, 28)]),
}

# staggered balcony planters per floor (outer edge cells): north row x15..31, west column z18..32, south row
# x15..31.  T birch tree, O oak tree, A flowering azalea, a azalea, f fern, - glass rail.
NT_BALC = {
    1: ("T--A--a--T--A--aT", "-a---T---A---", "A--T--a--A--T--a-"),
    2: ("-A--T--a--O--A---", "T---a--A---T-", "--O--A--T--a--A--"),
    3: ("a--O--A--T--a--O-", "--A---O---a--", "T--a--O--A--a--T-"),
    4: ("--T--a--A--O--T--", "A---T---a---O", "-a--T--A--O--a---"),
    5: ("O--A--T--a--A--O-", "--T---a---T--", "A--O--a--T--A--O-"),
    6: ("-a--O--T--A--a--T", "O---A---T---a", "--T--a--O--A--T--"),
}


def nt_planter(d, x, y, z, ch, out):
    """One balcony planter on the slab cell (x, y-1, z); `out` = direction away from the tower."""
    ox, oz = D4[out]
    d.set(x, y - 1, z, "moss_block")
    if ch in "TO":
        log, lf = ("birch_log", "birch") if ch == "T" else ("oak_log", "oak")
        d.set(x, y, z, logy(log))
        d.set(x, y + 1, z, logy(log))
        d.set(x, y + 2, z, lv(lf))
        for sx, sz in ((ox, oz), (oz, ox), (-oz, -ox)):
            if d.air(x + sx, y + 1, z + sz):
                d.set(x + sx, y + 1, z + sz, lv(lf))
        if d.air(x + ox, y + 2, z + oz):
            d.set(x + ox, y + 2, z + oz, lv(lf))
    elif ch == "A":
        d.set(x, y, z, lv("flowering_azalea"))
        d.set(x, y + 1, z, lv("flowering_azalea"))
        if d.air(x + ox, y, z + oz):
            d.set(x + ox, y, z + oz, lv("azalea"))
    elif ch == "a":
        d.set(x, y, z, "azalea")
    elif ch == "f":
        d.set(x, y, z, "fern")


def nt_tower_floor(d, s, n, L):
    """Storey s of the tower (walk level y0): slab, curtain wall, balcony with planters, furniture."""
    y0 = 2 + 5 * s
    if s > 0:
        d.fill(TX1, y0 - 1, TZ1, TX2, y0 - 1, TZ2, "polished_diorite")
    else:
        d.fill(TX1 + 1, 1, TZ1 + 1, TX2 - 1, 1, TZ2 - 1, "polished_diorite")
    for x in range(TX1, TX2 + 1):
        for z in range(TZ1, TZ2 + 1):
            edge = x in (TX1, TX2) or z in (TZ1, TZ2)
            for y in range(y0, y0 + 4):
                if not edge:
                    d.set(x, y, z, AIR)
                    continue
                corner = x in (TX1, TX2) and z in (TZ1, TZ2)
                mull = (x - TX1) % 3 == 0 if z in (TZ1, TZ2) else (z - TZ1) % 3 == 0
                if corner:
                    st = "white_concrete"
                elif y == y0 + 3:
                    st = "white_concrete" if s % 2 == 0 else "light_gray_concrete"
                elif mull:
                    st = "light_gray_concrete"
                else:
                    st = "glass_pane"
                d.set(x, y, z, st)
    # stair-shaft door in the east wall
    dz = 21 if s % 2 == 0 else 26
    d.set(TX2, y0, dz, AIR)
    d.set(TX2, y0 + 1, dz, AIR)
    # balcony (the slab of storeys 1+ reaches out 2 cells; the first one is the entrance canopy)
    if s >= 1:
        for x in range(15, 32):
            for z in list(range(17, 19)) + list(range(32, 34)):
                d.set(x, y0 - 1, z, "white_concrete" if z in (17, 33) else "smooth_stone")
        for z in range(19, 32):
            for x in (15, 16):
                d.set(x, y0 - 1, z, "white_concrete" if x == 15 else "smooth_stone")
        for x in (30, 31):
            for z in range(29, 32):
                d.set(x, y0 - 1, z, "smooth_stone")
        north, west, south = NT_BALC[s]
        for i, x in enumerate(range(15, 32)):
            ch = north[i]
            if ch == "-":
                d.set(x, y0, 17, "glass_pane")
            else:
                nt_planter(d, x, y0, 17, ch, "north")
            ch = south[i]
            if ch == "-":
                d.set(x, y0, 33, "glass_pane")
            else:
                nt_planter(d, x, y0, 33, ch, "south")
        for i, z in enumerate(range(18, 33)):
            ch = west[i] if i < len(west) else "-"
            if z in (18, 32):
                continue
            if ch == "-":
                d.set(15, y0, z, "glass_pane")
            else:
                nt_planter(d, 15, y0, z, ch, "west")
        for z in range(29, 33):
            d.set(32, y0, z, "glass_pane")
        d.set(31, y0, 18, "glass_pane")
        d.set(32, y0, 18, "glass_pane") if d.air(32, y0, 18) else None
    # furniture
    p = NT_PLANS[s]
    face = dict(p.get("face", {}))
    extra = {
        "~": lambda d_, x, y, z: (d_.set(x, y - 1, z, "sand"), d_.set(x, y, z, AIR)),
        "(": lambda d_, x, y, z: d_.bed(x, y, z, "south", "yellow"),
        ")": lambda d_, x, y, z: d_.bed(x, y, z, "south", "lime"),
        "w": lambda d_, x, y, z: d_.set(x, y, z, WATER),
    }
    rows = p["rows"]
    if "face2" in p:                    # second facing set for the south-wall shelves
        plan(d, 18, y0, 20, rows[:-1], NS, face, extra)
        plan(d, 18, y0, 30, rows[-1:], NS, p["face2"], extra)
    else:
        plan(d, 18, y0, 20, rows, NS, face, extra)
    lit = "sea_lantern" if L >= 4 else "glowstone"
    for x, z in p["lights"]:
        d.set(x, y0 + 4, z, lit)
    if s == 2:                          # sky-walk door to the west balcony
        d.door(TX1, y0, 24, "west", "birch")


def nt_shaft(d, n):
    """Glass stair shaft east of the tower: switch-back flights from the lobby up to the roof (storey n)."""
    top = 2 + 5 * n + 3
    for y in range(1, top + 1):
        for x in range(30, 33):
            for z in range(19, 29):
                edge = x == 32 or z in (19, 28)
                if not edge:
                    if y >= 2:
                        d.set(x, y, z, AIR)
                    continue
                corner = x == 32 and z in (19, 28) or (x == 30 and z in (19, 28))
                band = (y - 1) % 5 == 0
                d.set(x, y, z, "white_concrete" if corner or band or y == 1 else "glass_pane")
    d.fill(30, top + 1, 19, 32, top + 1, 28, "white_concrete")
    for s in range(n + 1):
        y0 = 2 + 5 * s
        if s % 2 == 0:
            d.fill(30, y0 - 1, 20, 31, y0 - 1, 21, "smooth_stone")
            if s < n:
                for i, z in enumerate(range(22, 26)):
                    d.set(30, y0 + i, z, stair("smooth_stone_stairs" if False else "polished_andesite_stairs", "south"))
        else:
            d.fill(30, y0 - 1, 26, 31, y0 - 1, 27, "smooth_stone")
            if s < n:
                for i, z in enumerate(range(25, 21, -1)):
                    d.set(31, y0 + i, z, stair("polished_andesite_stairs", "north"))
        # wall lantern on each landing
        lz = 20 if s % 2 == 0 else 27
        d.set(31, y0 + 2, lz, AIR)
        d.lamp(31, y0 + 3, lz, "lantern", hanging=True) if False else None
    for s in range(n + 1):
        y0 = 2 + 5 * s
        lz = 20 if s % 2 == 0 else 27
        d.set(30, y0 + 3, lz, lantern(True))


def nt_roof(d, n, L):
    """Roof forest on top of the tower (storey n)."""
    y0 = 2 + 5 * n
    d.fill(TX1, y0 - 1, TZ1, TX2, y0 - 1, TZ2, "smooth_stone")
    for x in range(TX1, TX2 + 1):
        for z in range(TZ1, TZ2 + 1):
            if x in (TX1, TX2) or z in (TZ1, TZ2):
                d.set(x, y0 - 1, z, "white_concrete")
                d.set(x, y0, z, "glass_pane")
    dz = 21 if n % 2 == 0 else 26
    d.set(TX2, y0, dz, AIR)
    # four tree planters (raised moss beds) with a different tree each
    for (cx, cz, log, lf) in ((20, 22, "birch_log", "birch"), (26, 28, "oak_log", "oak"),
                              (20, 28, "cherry_log", "cherry"), (25, 22, "birch_log", "birch")):
        for x in range(cx - 1, cx + 2):
            for z in range(cz - 1, cz + 2):
                d.set(x, y0, z, "moss_block")
        tree(d, cx, y0 + 1, cz, 3, log, lf, r=2)
    for x, z in ((19, 21), (21, 23), (19, 29), (21, 27), (27, 29), (24, 21)):
        d.set(x, y0 + 1, z, "fern") if d.air(x, y0 + 1, z) else None
    # pergola walk across the middle with benches
    for x in (18, 28):
        for z in (24, 26):
            for y in range(y0, y0 + 3):
                d.set(x, y, z, "light_gray_concrete")
    for x in range(18, 29):
        d.set(x, y0 + 3, 24, "birch_planks" if x % 2 else slab("birch_slab", "top"))
        d.set(x, y0 + 3, 26, "birch_planks" if x % 2 else slab("birch_slab", "top"))
        if x % 2 == 0:
            d.set(x, y0 + 3, 25, slab("birch_slab", "top"))
    bench(d, 21, y0, 26, "south", "birch", 2)
    bench(d, 24, y0, 24, "north", "birch", 2)
    for x, z in ((19, 25), (27, 25)):
        d.set(x, y0 + 2, z, lantern(True))
    d.set(23, y0, 25, "potted_flowering_azalea_bush")


def nt_supertree(d, x, z, h, plat=None, gaps=(), L=5):
    """One super-tree: planted base ring, a 3x3 trunk clad as a vertical garden, a funnel canopy of purple glass
    and iron ribs with a lit rim. plat = deck height of a sky-walk platform around the trunk, gaps = rail cells
    left open for the walkways."""
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            if max(abs(dx), abs(dz)) == 2:
                d.set(x + dx, 1, z + dz, "polished_andesite")
                d.set(x + dx, 2, z + dz, "moss_block")
                d.set(x + dx, 3, z + dz, ("fern", "azalea", "fern", "flowering_azalea")[(dx * 3 + dz) % 4]
                      if (dx + dz) % 2 == 0 else AIR)
    top = 2 + h
    clad = ("moss_block", lv("azalea"), "moss_block", lv("flowering_azalea"))
    for y in range(2, top):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx == 0 and dz == 0:
                    st = "light_gray_concrete"
                elif abs(dx) == 1 and abs(dz) == 1:
                    st = "polished_andesite" if y % 4 else "light_gray_concrete"
                else:
                    st = clad[(y + dx * 2 + dz) % 4]
                d.set(x + dx, y, z + dz, st)
    # funnel canopy
    glass = "purple_stained_glass_pane" if L >= 3 else "magenta_stained_glass_pane"
    for k, r in enumerate((2, 3, 4, 5)):
        yy = top - 3 + k
        for (cx, cz) in ring(r, x, z):
            if not d.bp.inside(cx, yy, cz):
                continue
            ddx, ddz = cx - x, cz - z
            spoke = ddx == 0 or ddz == 0 or abs(ddx) == abs(ddz)
            if r == 5:
                d.set(cx, yy, cz, "light_gray_concrete" if spoke else "iron_bars")
            else:
                d.set(cx, yy, cz, "iron_bars" if spoke else glass)
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            d.set(x + dx, top, z + dz, "light_gray_concrete" if (dx, dz) != (0, 0) else "glowstone")
    d.set(x, top + 1, z, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    for dx, dz in ((5, 0), (-5, 0), (0, 5), (0, -5)):
        if d.bp.inside(x + dx, top - 1, z + dz):
            d.set(x + dx, top - 1, z + dz, lantern(True))
    if plat is not None:
        for dx in range(-3, 4):
            for dz in range(-3, 4):
                if max(abs(dx), abs(dz)) <= 1:
                    continue
                d.set(x + dx, plat, z + dz, "light_gray_concrete" if max(abs(dx), abs(dz)) == 3 else "smooth_stone")
                if max(abs(dx), abs(dz)) == 3 and (x + dx, z + dz) not in gaps:
                    d.set(x + dx, plat + 1, z + dz, "glass_pane")
        # platform furniture: two benches against the trunk, planters at the corners, a lamp
        d.chair(x - 2, plat + 1, z, "east", "birch")
        d.chair(x + 2, plat + 1, z, "west", "birch")
        for cx, cz in ((x - 2, z - 2), (x + 2, z + 2)):
            d.set(cx, plat + 1, cz, "potted_flowering_azalea_bush")
        for cx, cz in ((x + 2, z - 2), (x - 2, z + 2)):
            d.set(cx, plat + 1, cz, "potted_fern")
        d.set(x, plat - 1, z - 2, lantern(True))
        d.set(x, plat - 1, z + 2, lantern(True))


def nt_skyway(d, x1, z1, x2, z2, y, along):
    """Two-wide sky walk deck at y between (x1,z1)-(x2,z2) with glass rails on both sides."""
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            d.set(x, y, z, "smooth_stone")
            d.set(x, y - 1, z, stair("smooth_stone_stairs" if False else "polished_andesite_stairs",
                                     "north" if along == "x" and z == z1 else "south" if along == "x"
                                     else "west" if x == x1 else "east", "top"))
    if along == "x":
        for x in range(x1, x2 + 1):
            d.set(x, y + 1, z1 - 1, "glass_pane")
            d.set(x, y + 1, z2 + 1, "glass_pane")
            d.set(x, y, z1 - 1, "light_gray_concrete")
            d.set(x, y, z2 + 1, "light_gray_concrete")
            if (x - x1) % 4 == 2:
                d.set(x, y + 2, z1 - 1, lantern())
    else:
        for z in range(z1, z2 + 1):
            d.set(x1 - 1, y + 1, z, "glass_pane")
            d.set(x2 + 1, y + 1, z, "glass_pane")
            d.set(x1 - 1, y, z, "light_gray_concrete")
            d.set(x2 + 1, y, z, "light_gray_concrete")
            if (z - z1) % 4 == 2:
                d.set(x1 - 1, y + 2, z, lantern())


def nt_column(d, x, z, h):
    """Glass water column: a tower of water sources held in a glass tube, standing in the pool."""
    for y in range(2, 2 + h):
        d.set(x, y, z, WATER)
        for dx, dz in D4.values():
            d.set(x + dx, y, z + dz, "glass")
    d.set(x, 2 + h, z, "glass")
    for dx, dz in D4.values():
        d.set(x + dx, 2 + h, z + dz, slab("smooth_stone_slab"))


def nt_gardens(rel, L):
    sx, sy, sz = NT["size"]
    d = Design("Neoterra", rel, NT["size"], paving="smooth_stone")
    n = NT_FLOORS[L]
    # ---------------------------------------------------------------- grounds: lawns, entrance walk, pools
    for x in range(sx):
        for z in range(sz):
            d.set(x, 1, z, GRASS)
    for z in range(0, 19):                               # entrance walk
        for x in range(21, 26):
            d.set(x, 1, z, "polished_diorite" if 22 <= x <= 24 else "smooth_stone")
    for x in range(15, 32):                              # forecourt in front of the tower
        for z in range(15, 19):
            d.set(x, 1, z, "smooth_stone" if (x + z) % 2 else "polished_diorite")
    for x in (7, 39):                                    # paths to the domes (street and garden doors)
        for z in list(range(0, 3)) + list(range(15, 19)):
            for xx in (x - 1, x, x + 1):
                d.set(xx, 1, z, "smooth_stone")
    for x in range(6, 41):
        d.set(x, 1, 16, "smooth_stone") if not (21 <= x <= 25) else None
        d.set(x, 1, 17, "smooth_stone")
    for x1, x2 in ((15, 19), (27, 31)):                  # twin reflecting pools
        for x in range(x1, x2 + 1):
            for z in range(3, 14):
                edge = x in (x1, x2) or z in (3, 13)
                d.set(x, 1, z, "white_concrete" if edge else WATER)
    if L >= 2:
        nt_column(d, 17, 8, 3 + (L >= 4))
        nt_column(d, 29, 8, 3 + (L >= 4))
    # lamps and benches along the entrance walk
    for z in (2, 8, 14):
        lamppost(d, 20, z, 2, 3, "diorite_wall", "lantern[hanging=false,waterlogged=false]")
        lamppost(d, 26, z, 2, 3, "diorite_wall", "lantern[hanging=false,waterlogged=false]")
    bench(d, 20, 2, 5, "west", "birch", 2, along="z", arms=False)
    bench(d, 26, 2, 10, "east", "birch", 2, along="z", arms=False)
    for x, z, tp in ((14, 4, "b"), (14, 12, "c"), (32, 4, "c"), (32, 12, "b")):
        tree(d, x, 2, z, 4, "birch_log" if tp == "b" else "cherry_log", "birch" if tp == "b" else "cherry", r=2)
    # ---------------------------------------------------------------- the tower
    for s in range(n):
        nt_tower_floor(d, s, n, L)
    nt_shaft(d, n)
    nt_roof(d, n, L)
    d.door(22, 2, TZ1, "north", "birch", "left")
    d.door(24, 2, TZ1, "north", "birch", "right")
    d.set(23, 2, TZ1, "glass_pane")
    d.set(23, 3, TZ1, "glass_pane")
    d.sign(23, 4, TZ1 - 1, "north", ["", "Verdant", "Sky Gardens", ""], "birch", glow=True, color="cyan")
    d.hut(23, 2, 26, facing="north")
    # flower beds along the tower foot
    for x in range(17, 30):
        if x in (21, 22, 23, 24, 25):
            continue
        d.set(x, 1, 18, "moss_block")
        d.set(x, 2, 18, ("azalea", "fern", "flowering_azalea", "fern")[x % 4])
    # ---------------------------------------------------------------- super-tree grove
    trees = []
    if L >= 2:
        trees += [("A", 8, 23, {2: 12, 3: 18, 4: 20, 5: 22}[L]), ("E", 39, 23, {2: 10, 3: 14, 4: 16, 5: 18}[L])]
    if L >= 3:
        trees += [("C", 8, 41, {3: 12, 4: 18, 5: 20}[L])]
    if L >= 4:
        trees += [("D", 23, 44, {4: 20, 5: 26}[L]), ("B", 39, 41, {4: 14, 5: 20}[L])]
    plats = {}
    if L >= 3:
        plats["A"] = [(11, 23), (11, 24)] + ([(9, 26), (10, 26)] if L >= 4 else [])
    if L >= 4:
        plats["C"] = [(9, 38), (10, 38)] + ([(11, 41), (11, 42)] if L >= 5 else [])
    if L >= 5:
        plats["D"] = [(20, 41), (20, 42), (26, 41), (26, 42)]
        plats["B"] = [(36, 41), (36, 42), (41, 38), (42, 38)]
        plats["E"] = [(41, 26), (42, 26), (36, 20), (36, 21)]
    for name, x, z, h in trees:
        nt_supertree(d, x, z, h, 11 if name in plats else None, plats.get(name, ()), L)
    if L >= 3:                                           # sky walk from the tower's 2nd-floor balcony
        nt_skyway(d, 12, 23, 14, 24, 11, "x")
        for z in (23, 24):
            d.set(15, 12, z, AIR)
    if L >= 4:
        nt_skyway(d, 9, 27, 10, 37, 11, "z")
    if L >= 5:
        nt_skyway(d, 12, 41, 19, 42, 11, "x")
        nt_skyway(d, 27, 41, 35, 42, 11, "x")
        nt_skyway(d, 41, 27, 42, 37, 11, "z")
        nt_skyway(d, 33, 20, 35, 21, 11, "x")
        for z in (20, 21):
            for y in (12, 13):
                d.set(32, y, z, AIR)
    # ---------------------------------------------------------------- back garden
    if L >= 2:
        for x, z in ((3, 31), (14, 36), (32, 36), (44, 31)):
            tree(d, x, 2, z, 4, "birch_log", "birch", r=2)
        for x, z, f in ((5, 29, "south"), (41, 29, "south")):
            bench(d, x, 2, z, f, "birch", 2)
    if L >= 3:
        for x in range(2, 15):                          # flower meadow strips west and east of the tower
            for z in (33, 34):
                d.set(x, 1, z, "moss_block")
                d.set(x, 2, z, ("allium", "azure_bluet", "oxeye_daisy", "cornflower", "white_tulip")[(x + z) % 5])
        for x in range(33, 45):
            for z in (33, 34):
                d.set(x, 1, z, "moss_block")
                d.set(x, 2, z, ("cornflower", "allium", "white_tulip", "azure_bluet", "oxeye_daisy")[(x + z) % 5])
        for x in (16, 30):
            lamppost(d, x, 34, 2, 3, "diorite_wall", "lantern[hanging=false,waterlogged=false]")
    if L >= 4:                                          # dragonfly lake behind the tower with a boardwalk
        for x in range(14, 33):
            for z in range(35, 40):
                edge = x in (14, 32) or z in (35, 39)
                d.set(x, 1, z, "white_concrete" if edge else WATER)
        for x in range(15, 32):
            if x in (22, 23, 24):
                continue
            d.set(x, 1, 36 if x % 3 else 38, WATER)
        for z in range(35, 40):                          # boardwalk across the lake
            for x in (22, 23, 24):
                d.set(x, 1, z, "birch_planks" if x == 23 else "smooth_stone")
            d.set(21, 2, z, "birch_fence")
            d.set(25, 2, z, "birch_fence")
        for x, z in ((16, 37), (19, 36), (28, 38), (30, 36), (26, 37)):
            d.set(x, 2, z, "lily_pad")
        for x, z in ((15, 38), (31, 38)):
            d.set(x, 2, z, AIR)
        for x in range(14, 33):                          # reeds and irises on the bank
            if x in (21, 22, 23, 24, 25):
                continue
            d.set(x, 1, 34, "moss_block")
            d.set(x, 2, 34, ("blue_orchid", "fern", "allium", "fern")[x % 4])
    if L >= 5:                                          # back terrace with seats looking over the lake
        for x in range(13, 34):
            for z in range(48, 52):
                d.set(x, 1, z, "smooth_stone" if z < 51 else "polished_diorite")
        for x in range(13, 34):
            d.set(x, 2, 52, "birch_leaves[distance=1,persistent=true,waterlogged=false]" if x % 2 else
                  lv("flowering_azalea"))
        for x in (14, 18, 28, 32):
            bench(d, x, 2, 51, "south", "birch", 2)
        for x in (13, 21, 25, 33):
            lamppost(d, x, 49, 2, 3, "diorite_wall", "lantern[hanging=false,waterlogged=false]")
        # crown on the roof: four pylons carrying a solar louvre ring and hanging vines
        y0 = 2 + 5 * n
        for x, z in ((TX1, TZ1), (TX2, TZ1), (TX1, TZ2), (TX2, TZ2)):
            for y in range(y0, y0 + 6):
                d.set(x, y, z, "white_concrete")
        for x in range(TX1, TX2 + 1):
            for z in range(TZ1, TZ2 + 1):
                if x in (TX1, TX2) or z in (TZ1, TZ2):
                    d.set(x, y0 + 6, z, "white_concrete" if (x + z) % 3 == 0 else "light_gray_concrete")
                    d.set(x, y0 + 7, z, "daylight_detector[inverted=false,power=0]")
                elif x in (TX1 + 1, TX2 - 1) or z in (TZ1 + 1, TZ2 - 1):
                    if (x + z) % 2:
                        d.set(x, y0 + 6, z, "white_concrete")
                        d.set(x, y0 + 5, z, lv("azalea"))
        d.set(23, y0 + 6, 25, "sea_lantern")
    place_wings(d, NT["res"], NT["wsize"], NT["whut"])
    connect_walls(d)
    return d


def nt_wing(rel, L):
    """Glass biodome: L1 a glass-pyramid pavilion; L2-5 a ribbed dome growing to 13 wide; L4-5 a planted
    mountain with a waterfall inside (the cloud-forest dome)."""
    d = wing_design("Neoterra", rel, NT["wsize"])
    cx = cz = 6
    hut = NT["whut"]
    if L == 1:
        for x in range(3, 10):
            for z in range(3, 10):
                d.set(x, 0, z, "smooth_stone")
                edge = x in (3, 9) or z in (3, 9)
                for y in range(1, 5):
                    if edge:
                        corner = x in (3, 9) and z in (3, 9)
                        d.set(x, y, z, "white_concrete" if corner or y == 4 else "glass_pane")
        for k, (a, b) in enumerate(((3, 9), (4, 8), (5, 7), (6, 6))):
            for x in range(a, b + 1):
                for z in range(a, b + 1):
                    if x in (a, b) or z in (a, b) or k == 3:
                        d.set(x, 5 + k, z, "white_concrete" if (x in (a, b) and z in (a, b)) else "glass")
        doors = (3, 9)
        rows = ["...........",
                "...........",
                "...........",
                "....f.f....",
                "...GE.EG...",
                "...L...L...",
                "...GE.EG...",
                "...........",
                "...........",
                "...........",
                "..........."]
    else:
        R = {2: 4.5, 3: 5.5, 4: 6.5, 5: 6.5}[L]
        V = {2: 6, 3: 7.5, 4: 9, 5: 12}[L]
        inside = set()
        for x in range(13):
            for z in range(13):
                for y in range(0, 15):
                    if ((x - cx) / R) ** 2 + ((z - cz) / R) ** 2 + (y / V) ** 2 <= 1.0:
                        inside.add((x, y, z))
        for (x, y, z) in inside:
            if y == 0:
                d.set(x, 0, z, "smooth_stone")
                continue
            shell = any((x + a, y + b, z + c) not in inside
                        for a, b, c in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, 0, 1), (0, 0, -1)))
            if not shell:
                continue
            rib = x == cx or z == cz or abs(x - cx) == abs(z - cz) or y == 1
            d.set(x, y, z, "white_concrete" if rib else ("glass" if L < 5 or y % 4 else "light_blue_stained_glass"))
        zmin = min(z for (x, y, z) in inside if x == cx and y == 1)
        zmax = max(z for (x, y, z) in inside if x == cx and y == 1)
        doors = (zmin, zmax)
        rows = {
            2: ["...........",
                "...........",
                "....fyf....",
                "...........",
                "..GE.L.EG..",
                "..E.....E..",
                "..L.333.L..",
                "...........",
                "...A...A...",
                "...........",
                "..........."],
            3: ["...........",
                "....GEG....",
                "..f.....f..",
                ".G.......G.",
                ".E.EE.EE.E.",
                ".L.E...E.L.",
                ".G.D.3.D.G.",
                ".E.......E.",
                "..y.....y..",
                "....GLG....",
                "..........."],
            4: ["...........",
                "...GE.EG...",
                ".A.......A.",
                "GD..LLL..DG",
                "E...M.M...E",
                "G...M.M...G",
                "E....3....E",
                "GD.......DG",
                ".f.......f.",
                "...GE.EG...",
                "..........."],
            5: ["...........",
                "..LGE.EGL..",
                ".D.......D.",
                "GE..LLL..EG",
                "E...M.M...E",
                "GD..M.M..DG",
                "E.........E",
                "GD.......DG",
                ".y.......y.",
                "..LGE.EGL..",
                "..........."],
        }[L]
    # doors north and south on the axis
    for z in doors:
        d.set(cx, 0, z, "smooth_stone")
        d.door(cx, 1, z, "north" if z < cz else "south", "birch")
    for z in range(0, doors[0]):
        d.set(cx, 0, z, "polished_diorite")
    for z in range(doors[1] + 1, 13):
        d.set(cx, 0, z, "polished_diorite")
    extra = {"M": lambda d_, x, y, z: None}
    plan(d, 1, 1, 1, rows, NS, {}, extra)
    if L >= 4:                                          # planted rock mountain with a waterfall on its west face
        H = 6 if L == 4 else 9
        rock = ("mossy_cobblestone", "stone", "andesite", "mossy_stone_bricks", "tuff")
        for x in range(5, 8):
            for z in range(5, 8):
                for y in range(1, H + 1 - (1 if (x, z) != (6, 6) and y == H else 0)):
                    d.set(x, y, z, rock[(x * 3 + y + z * 2) % 5])
        for y in range(1, H):                          # waterfall notch: sources in the west face
            d.set(5, y, 6, WATER)
        for x, z in ((4, 5), (4, 6), (4, 7), (3, 6)):  # plunge pool below
            d.set(x, 0, z, WATER)
        d.set(5, 0, 6, WATER)
        for x, z, y in ((7, 5, 3), (7, 7, 4), (6, 7, 2), (6, 5, 5), (8, 6, 1)):
            if y <= H:
                d.set(x, y, z, lv("azalea"))
        d.set(6, H + 1, 6, "flowering_azalea") if d.air(6, H + 1, 6) else None
        for x, z in ((7, 6), (6, 7), (6, 5)):
            d.set(x, H, z, "moss_carpet") if d.air(x, H, z) else None
        if L == 5:
            for y in (3, 5, 7):
                d.set(7, y, 8, "fern") if False else None
            d.set(8, 1, 5, "fern")
            d.set(8, 1, 7, "fern")
    d.hut(*hut, facing="north")
    d.item(12 - hut[0], 1, hut[2], "composter")
    # hanging lights inside the dome
    if L >= 2:
        top = max(y for y in range(15) if d.get(cx, y, 2 if L >= 4 else 3) != AIR) if False else None
    return d


@design("hanginggardens")
def hanginggardens(pack, rel, L):
    return {"Neoterra": nt_gardens}[pack](rel, L)


@design("hanginggardenswing")
def hanginggardenswing(pack, rel, L):
    return {"Neoterra": nt_wing}[pack](rel, L)
