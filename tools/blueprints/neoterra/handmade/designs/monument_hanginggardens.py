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
        if s.split("[")[0] != "minecraft:water":
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
NT = dict(size=(47, 58, 57), wsize=(13, 18, 13), whut=(4, 1, 4), res=((1, 2), (33, 2)))
NT_FLOORS = {1: 2, 2: 3, 3: 4, 4: 6, 5: 9}
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
        "ASS.J.NSS.A",
        "..d%d%d%...",
        ".&d%d%d%&..",
        "..&*&*&*...",
        "...........",
        "4T2.....~~~",
        "4T2.....~~~",
        "........~~~",
        "...........",
        "..........y",
        "(b)b(b)b(.f"], face={"P": "south", "S": "south"},
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
        lights=[(21, 21), (25, 21), (20, 24), (20, 26), (26, 24), (26, 26), (23, 28)]),
    7: dict(name="tea pavilion", rows=[     # tea room & meditation: low tea tables, zen basin, bonsai shelves
        "zfz.....LyL",
        "...........",
        ".q1q..o1o..",
        ".4T2..4T2..",
        ".q3q..o3o..",
        "...........",
        "S..........",
        "S..&&&&&...",
        "S..&lWl&..a",
        "...&&&&&...",
        "A.z.A.z.A.."], face={"S": "east"},
        lights=[(20, 21), (25, 21), (19, 25), (22, 27), (24, 29), (25, 27), (27, 24)]),
    8: dict(name="garden gallery", rows=[   # exhibition of the gardens: display plinths, a model garden, benches
        "S.e.g.i.e.A",
        "...........",
        "e.........y",
        "...GEGEG...",
        "i..ELWLE..e",
        "...GEGEG...",
        "g.........i",
        "...........",
        "..3333.....",
        "...........",
        "SSS.SzS.SSS"], face={"S": "south", "e": "south"}, face2={"S": "north"},
        lights=[(20, 22), (26, 22), (23, 25), (20, 28), (26, 28)]),
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
    7: ("A--a--O--T--A--a-", "-T---O---a---", "a--T--A--O--a--T-"),
    8: ("-T--A--a--O--T--A", "a---O---T---A", "-O--a--T--A--O--a"),
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
                    d.set(30, y0 + i, z, stair("polished_diorite_stairs" if False else "polished_andesite_stairs", "south"))
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


def nt_supertree(d, x, z, h, plat=None, gaps=(), L=5, by=1):
    """One super-tree standing on the ground at height `by`: planted base ring, a 3x3 trunk clad as a vertical
    garden, a funnel canopy of purple glass on iron ribs with a lit rim. plat = deck height of a sky-walk
    platform around the trunk, gaps = rail cells left open for the walkways."""
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            if max(abs(dx), abs(dz)) == 2:
                d.set(x + dx, by, z + dz, "polished_andesite")
                d.set(x + dx, by + 1, z + dz, "moss_block")
                d.set(x + dx, by + 2, z + dz, ("fern", "azalea", "fern", "flowering_azalea")[(dx * 3 + dz) % 4]
                      if (dx + dz) % 2 == 0 else AIR)
    top = by + 1 + h
    clad = ("moss_block", lv("azalea"), "moss_block", lv("flowering_azalea"))
    for y in range(by + 1, top):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx == 0 and dz == 0:
                    st = "light_gray_concrete"
                elif abs(dx) == 1 and abs(dz) == 1:
                    st = "polished_andesite" if y % 4 else "light_gray_concrete"
                else:
                    st = clad[(y + dx * 2 + dz) % 4]
                d.set(x + dx, y, z + dz, st)
    # funnel canopy: iron ribs fanning out, purple glass between, a lit concrete rim
    for k, r in enumerate((2, 3, 4, 5)):
        yy = top - 3 + k
        for (cx, cz) in ring(r, x, z):
            if not d.bp.inside(cx, yy, cz):
                continue
            ddx, ddz = cx - x, cz - z
            spoke = ddx == 0 or ddz == 0 or abs(ddx) == abs(ddz)
            if r == 5:
                d.set(cx, yy, cz, "light_gray_concrete" if spoke else "purple_stained_glass")
            elif r == 4:
                d.set(cx, yy, cz, "iron_bars" if spoke else "magenta_stained_glass")
            else:
                d.set(cx, yy, cz, "iron_bars" if spoke else "purple_stained_glass_pane")
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
        # platform furniture: two benches against the trunk, planters at the corners, lamps underneath
        d.chair(x - 2, plat + 1, z, "east", "birch")
        d.chair(x + 2, plat + 1, z, "west", "birch")
        for cx, cz in ((x - 2, z - 2), (x + 2, z + 2)):
            d.set(cx, plat + 1, cz, "potted_flowering_azalea_bush")
        for cx, cz in ((x + 2, z - 2), (x - 2, z + 2)):
            d.set(cx, plat + 1, cz, "potted_fern")
        d.set(x, plat - 1, z - 2, lantern(True))
        d.set(x, plat - 1, z + 2, lantern(True))
        for cx, cz in ((x - 3, z - 3), (x + 3, z - 3), (x - 3, z + 3), (x + 3, z + 3)):
            d.set(cx, plat + 1, cz, "light_gray_concrete")
            d.set(cx, plat + 2, cz, lantern())


def nt_skyway(d, x1, z1, x2, z2, y, along):
    """Two-wide sky walk deck at y between (x1,z1)-(x2,z2) with glass rails on both sides, lamps on the rail."""
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            d.set(x, y, z, "smooth_stone")
    if along == "x":
        for x in range(x1, x2 + 1):
            for z, f in ((z1 - 1, "south"), (z2 + 1, "north")):
                d.set(x, y, z, "light_gray_concrete")
                d.set(x, y + 1, z, "glass_pane")
                d.set(x, y - 1, z, stair("polished_andesite_stairs", f, "top"))
            if (x - x1) % 4 == 2:
                d.set(x, y + 2, z1 - 1, lantern())
    else:
        for z in range(z1, z2 + 1):
            for x, f in ((x1 - 1, "east"), (x2 + 1, "west")):
                d.set(x, y, z, "light_gray_concrete")
                d.set(x, y + 1, z, "glass_pane")
                d.set(x, y - 1, z, stair("polished_andesite_stairs", f, "top"))
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


# step garden ("hanging gardens") behind the lake: steps inset 2 on north / east / west, back flush at z=55
NT_STEPS = [(12, 34, 41, 3), (14, 32, 43, 6), (16, 30, 45, 9), (18, 28, 47, 12), (20, 26, 49, 15)]
NT_FALLS = (17, 29)                                      # x of the two cascades (steps 0-2)
NT_STAIR = {1: (20, "east"), 2: (26, "west"), 3: (20, "east"), 4: (26, "west")}


def nt_step_garden(d, L):
    """ACROS-style stepped garden: every step has a planted outer row with draping azalea and a walk behind it,
    zig-zag stairs cut into the risers, and two cascades of basins whose lips spill down the risers."""
    nsteps = 3 if L == 4 else 5
    zb = 55
    stairs = set()
    for k in range(1, nsteps):
        x0, f = NT_STAIR[k]
        sgn = 1 if f == "east" else -1
        for i in range(3):
            stairs.add((x0 + sgn * i, NT_STEPS[k][2]))
    for k, (x1, x2, z1, top) in enumerate(NT_STEPS[:nsteps]):
        y1 = 2 if k == 0 else NT_STEPS[k - 1][3] + 1
        for x in range(x1, x2 + 1):
            for z in range(z1, zb + 1):
                for y in range(y1, top + 1):
                    face = x in (x1, x2) or z in (z1, zb) or y == top
                    d.set(x, y, z, ("white_concrete" if y == top else "light_gray_concrete") if face else SOLIDSUB)
        # planted outer row (front and sides); azalea drapes over the riser
        for x in range(x1, x2 + 1):
            for z in range(z1, zb + 1):
                if not (x in (x1, x2) or z == z1) or (x, z) in stairs or (k == 0 and 22 <= x <= 24 and z == z1):
                    continue
                d.set(x, top, z, "moss_block")
                c = (x * 7 + z * 3 + k) % 6
                d.set(x, top + 1, z, (lv("azalea"), "fern", lv("flowering_azalea"), "azalea", "fern",
                                      "flowering_azalea")[c])
        # cascade basins (steps 0-2)
        if k <= 2:
            for xw in NT_FALLS:
                for z in (z1, z1 + 1):
                    d.set(xw, top, z, WATER)
                    d.set(xw, top + 1, z, AIR)
                for y in range(y1, top):                 # riser notch under the lip
                    d.set(xw, y, z1, WATER)
    # zig-zag stairs cut into the risers
    for x in (22, 23, 24):
        d.set(x, 2, 40, stair("polished_diorite_stairs", "south"))
        d.set(x, 3, 41, stair("polished_diorite_stairs", "south"))
    for k in range(1, nsteps):
        x0, f = NT_STAIR[k]
        sgn = 1 if f == "east" else -1
        z1, top = NT_STEPS[k][2], NT_STEPS[k][3]
        py = NT_STEPS[k - 1][3]
        for i in range(3):
            x = x0 + sgn * i
            d.set(x, py + 1 + i, z1, stair("polished_diorite_stairs", f))
            for y in range(py + 2 + i, top + 3):
                d.set(x, y, z1, AIR)
    # plunge pools where the lowest falls reach the lake
    for xw in NT_FALLS:
        d.set(xw, 1, 40, WATER)
        d.set(xw, 1, 39, WATER)
    # spring: a third source and a spout behind the highest basins
    for xw in NT_FALLS:
        d.set(xw, 9, 47, WATER)
        d.set(xw, 10, 47, AIR)
        d.set(xw, 10, 48, "white_concrete")
        d.set(xw, 11, 48, stair("polished_diorite_stairs", "south"))
    # seats on the step walks facing the lake, lamps (hand-placed)
    seats = [(14, 4, 42), (15, 4, 42), (31, 4, 42), (32, 4, 42), (16, 7, 44), (30, 7, 44), (19, 10, 46),
             (27, 10, 46)]
    lamps = [(13, 4, 42), (33, 4, 42), (15, 7, 44), (31, 7, 44)]
    if nsteps == 5:
        seats += [(25, 13, 48), (21, 16, 50) if False else (25, 13, 48)]
        lamps += [(19, 13, 48), (27, 13, 48)]
    for x, y, z in seats:
        if d.air(x, y, z):
            d.chair(x, y, z, "south", "birch")
    for x, y, z in lamps:
        lamppost(d, x, z, y, 2, "diorite_wall", lantern())
    if nsteps == 5:                                     # top terrace: the tallest super-tree stands on it
        pass
    return NT_STEPS[nsteps - 1]


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
        if not 21 <= x <= 25:
            d.set(x, 1, 16, "smooth_stone")
        d.set(x, 1, 17, "smooth_stone")
    for x1, x2 in ((15, 19), (27, 31)):                  # twin reflecting pools
        for x in range(x1, x2 + 1):
            for z in range(3, 14):
                edge = x in (x1, x2) or z in (3, 13)
                d.set(x, 1, z, "white_concrete" if edge else WATER)
    if L >= 2:
        nt_column(d, 17, 8, 3 + (L >= 4) + (L >= 5))
        nt_column(d, 29, 8, 3 + (L >= 4) + (L >= 5))
    for z in (2, 8, 14):                                 # lamps along the entrance walk
        lamppost(d, 20, z, 2, 3, "diorite_wall", lantern())
        lamppost(d, 26, z, 2, 3, "diorite_wall", lantern())
    bench(d, 20, 2, 5, "west", "birch", 2, along="z", arms=False)
    bench(d, 26, 2, 10, "east", "birch", 2, along="z", arms=False)
    tree(d, 14, 2, 4, 4, "birch_log", "birch", r=2)
    tree(d, 32, 12, 2, 4, "birch_log", "birch", r=2) if False else tree(d, 32, 2, 12, 4, "birch_log", "birch", r=2)
    if L >= 2:
        tree(d, 14, 2, 12, 4, "cherry_log", "cherry", r=2)
        tree(d, 32, 2, 4, 4, "cherry_log", "cherry", r=2)
    # ---------------------------------------------------------------- the tower
    for s in range(n):
        nt_tower_floor(d, s, n, L)
    nt_shaft(d, n)
    nt_roof(d, n, L)
    lit = "sea_lantern" if L >= 4 else "glowstone"
    for s in range(n):                                   # recessed ceiling lights (after the slabs above)
        for x, z in NT_PLANS[s]["lights"]:
            d.set(x, 2 + 5 * s + 4, z, lit)
    d.door(22, 2, TZ1, "north", "birch", "left")
    d.door(24, 2, TZ1, "north", "birch", "right")
    d.set(23, 2, TZ1, "glass_pane")
    d.set(23, 3, TZ1, "glass_pane")
    d.sign(23, 4, TZ1 - 1, "north", ["", "Verdant", "Sky Gardens", ""], "birch", glow=True, color="cyan")
    d.hut(23, 2, 26, facing="north")
    for x in range(17, 30):                              # flower beds along the tower foot
        if 21 <= x <= 25:
            continue
        d.set(x, 1, 18, "moss_block")
        d.set(x, 2, 18, ("azalea", "fern", "flowering_azalea", "fern")[x % 4])
    # ---------------------------------------------------------------- super-tree grove and sky walk
    trees = []
    if L >= 2:
        trees += [("A", 8, 23, {2: 12, 3: 18, 4: 20, 5: 22}[L])]
    if L >= 3:
        trees += [("E", 39, 23, {3: 12, 4: 16, 5: 18}[L]), ("C", 8, 41, {3: 12, 4: 18, 5: 20}[L])]
    if L >= 5:
        trees += [("B", 39, 41, 20), ("F", 5, 50, 11), ("G", 41, 50, 13)]
    plats = {}
    if L >= 3:
        plats["A"] = [(11, 23), (11, 24)] + ([(9, 26), (10, 26)] if L >= 4 else [])
    if L >= 4:
        plats["C"] = [(9, 38), (10, 38)] + ([(11, 39), (11, 40)] if L >= 5 else [])
    if L >= 5:
        plats["B"] = [(36, 39), (36, 40), (41, 38), (42, 38)]
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
        nt_skyway(d, 12, 39, 35, 40, 11, "x")
        nt_skyway(d, 41, 27, 42, 37, 11, "z")
        nt_skyway(d, 33, 20, 35, 21, 11, "x")
        for z in (20, 21):
            for y in (12, 13):
                d.set(32, y, z, AIR)
    # ---------------------------------------------------------------- back garden
    if L >= 2:
        for x, z in ((3, 31), (44, 31)):
            tree(d, x, 2, z, 4, "birch_log", "birch", r=2)
        bench(d, 5, 2, 29, "south", "birch", 2)
        bench(d, 41, 2, 29, "south", "birch", 2)
    if L >= 3:
        for x in range(2, 14):                          # flower meadows west and east of the tower
            for z in (33, 34):
                d.set(x, 1, z, "moss_block")
                d.set(x, 2, z, ("allium", "azure_bluet", "oxeye_daisy", "cornflower", "white_tulip")[(x + z) % 5])
        for x in range(34, 45):
            for z in (33, 34):
                d.set(x, 1, z, "moss_block")
                d.set(x, 2, z, ("cornflower", "allium", "white_tulip", "azure_bluet", "oxeye_daisy")[(x + z) % 5])
        for x, z in ((14, 33), (32, 33)):
            lamppost(d, x, z, 2, 3, "diorite_wall", lantern())
    if L >= 4:                                          # dragonfly lake with a boardwalk, then the step garden
        for x in range(14, 33):
            for z in range(35, 40):
                edge = x in (14, 32) or z in (35, 39)
                d.set(x, 1, z, "white_concrete" if edge else WATER)
        for z in range(35, 40):
            for x in (22, 23, 24):
                d.set(x, 1, z, "birch_planks" if x == 23 else "smooth_stone")
            d.set(21, 2, z, "birch_fence")
            d.set(25, 2, z, "birch_fence")
        for x, z in ((16, 37), (19, 36), (28, 38), (30, 36), (26, 37)):
            d.set(x, 2, z, "lily_pad")
        for x in range(15, 32):                          # irises and ferns on the bank
            if 21 <= x <= 25:
                continue
            d.set(x, 1, 34, "moss_block")
            d.set(x, 2, 34, ("blue_orchid", "fern", "allium", "fern")[x % 4])
        nt_step_garden(d, L)
    if L >= 5:
        nt_supertree(d, 23, 52, 16, None, (), L, by=15)  # the tallest super-tree crowns the step garden
        # crown on the roof: four pylons carrying a solar louvre ring and hanging azalea
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
        # winter-garden arcade linking the two domes across the forecourt
        for x in range(14, 33):
            for z in (15, 18):
                if x % 3 == 2:
                    for y in range(2, 6):
                        d.set(x, y, z, "white_concrete")
            for z in range(15, 19):
                d.set(x, 6, z, "glass" if z in (16, 17) else "white_concrete")
            if x % 3 == 2:
                for z in (16, 17):
                    d.set(x, 6, z, "white_concrete")
                    d.set(x, 5, z, lantern(True)) if z == 16 else None
            d.set(x, 7, 16, slab("smooth_quartz_slab")) if False else None
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
                        d.set(x, 5 + k, z, "white_concrete" if (x in (a, b) and z in (a, b)) else "light_blue_stained_glass")
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
        R = {2: 5.5, 3: 6.5, 4: 6.5, 5: 6.5}[L]
        V = {2: 7, 3: 9.5, 4: 10.5, 5: 13.5}[L]
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
            rib = x == cx or z == cz or y == 1 or (y % 4 == 0 and L >= 3)
            d.set(x, y, z, "white_concrete" if rib else "light_blue_stained_glass")
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


# =============================================================================================================
#                                    HEARTHWOOD  -  THE PALM HOUSE
# =============================================================================================================
HW = dict(size=(55, 34, 69), wsize=(11, 18, 11), whut=(3, 1, 5), res=((2, 2), (42, 2)))
HS = dict(wood="dark_oak", counter="dark_oak_slab", rug=("red", "orange", "brown"), block="bricks", bedcol="red")
PH_X1, PH_X2, PH_ZC = 19, 35, 34                         # central pavilion x range, axis of the house
H_CEN = {7: 9, 6: 11, 5: 13, 4: 14, 3: 15, 2: 16, 1: 16, 0: 17}      # shell height by distance from the axis
H_LAN = {7: 9, 6: 11, 5: 13, 4: 14, 3: 15, 2: 18, 1: 19, 0: 20}      # with the clerestory lantern (L3+)
H_WNG = {5: 8, 4: 10, 3: 11, 2: 12, 1: 12, 0: 13}                     # side wings
H_WNG5 = {5: 9, 4: 11, 3: 12, 2: 13, 1: 14, 0: 15}                    # side wings at L5 (taller, crested)
H_TOP = {7: 9, 6: 11, 5: 13, 4: 15, 3: 17, 2: 21, 1: 22, 0: 23}      # L5: the great lantern


def hw_soil(kind):
    def f(d, x, y, z):
        d.set(x, y - 1, z, "podzol" if kind != "grass" else GRASS)
        if kind in ("large_fern", "peony", "rose_bush", "lilac"):
            flower(d, x, y, z, kind)
        elif kind == "bamboo":
            d.set(x, y, z, "bamboo[age=0,leaves=large,stage=0]")
            d.set(x, y + 1, z, "bamboo[age=0,leaves=large,stage=0]")
        elif kind == "dripleaf":
            d.set(x, y, z, "big_dripleaf[facing=north,tilt=none,waterlogged=false]")
        elif kind != "grass":
            d.set(x, y, z, kind)
    return f


HW_EXTRA = {"{": hw_soil("fern"), "}": hw_soil("dripleaf"), "[": hw_soil("large_fern"), "]": hw_soil("azalea"),
            "?": hw_soil("flowering_azalea"), "!": hw_soil("bamboo"), "_": hw_soil("peony"),
            "w": lambda d, x, y, z: d.set(x, y - 1, z, WATER)}


def hw_column(d, x, z, lo, hi, glass, rib):
    glass = "light_blue_stained_glass" if glass == "glass" else glass
    for y in range(lo, hi + 1):
        d.set(x, y, z, "white_concrete" if rib else glass)


def hw_vault(d, x1, x2, zc, H, y0=4, ribstep=3, ends=True, end_open=()):
    """Barrel-vaulted glass house along x between x1..x2 (walls included), shell heights H by |z - zc|.
    White cast-iron ribs every `ribstep` cells, glass between, end walls closed with panes (except end_open)."""
    hw = max(H)
    for x in range(x1, x2 + 1):
        rib = (x - x1) % ribstep == 0 or x in (x1, x2)
        for z in range(zc - hw, zc + hw + 1):
            k = abs(z - zc)
            if k == hw:                                  # vertical side wall
                for y in range(y0, H[k] + 1):
                    d.set(x, y, z, "white_concrete" if rib or y == H[k] else "glass_pane")
                continue
            lo = min(H[k + 1] + 1, H[k])
            hw_column(d, x, z, lo, H[k], "glass", rib)
            for y in range(y0, lo):
                if x in (x1, x2) and ends and (x, z) not in end_open:
                    d.set(x, y, z, "white_concrete" if (z - zc) % 3 == 0 or y == y0 else "glass_pane")
                elif d.get(x, y, z) == AIR or x in (x1, x2):
                    d.set(x, y, z, AIR)


def hw_apse(d, cx, zc, H, side, y0=4):
    """Half-round glass apse closing a wing end: cells west (side=-1) or east (+1) of x=cx."""
    hw = max(H)
    for x in range(cx - hw - 1, cx + hw + 2):
        if (x - cx) * side <= 0:
            continue
        for z in range(zc - hw, zc + hw + 1):
            r = ((x - cx) ** 2 + (z - zc) ** 2) ** 0.5
            k = int(round(r))
            if k > hw:
                continue
            rib = z == zc or abs(z - zc) == abs(x - cx)
            if k == hw:
                for y in range(y0, H[k] + 1):
                    d.set(x, y, z, "white_concrete" if rib or y == H[k] else "glass_pane")
                d.set(x, y0 - 1, z, "bricks")
                d.set(x, y0 - 2, z, "bricks")
                continue
            lo = min(H[k + 1] + 1, H[k])
            hw_column(d, x, z, lo, H[k], "glass", rib)
            d.set(x, y0 - 1, z, "polished_andesite")
            d.set(x, y0 - 2, z, SOLIDSUB)


def hw_plinth(d, x1, x2, z1, z2, floor="polished_andesite"):
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            edge = x in (x1, x2) or z in (z1, z2)
            d.set(x, 2, z, "bricks" if edge else SOLIDSUB)
            d.set(x, 3, z, ("bricks" if edge else floor))


def hw_spiral(d, cx, cz, steps, y0=4):
    """Spiral stair of white iron: post in the middle, one step per ring cell (hand-listed order)."""
    for y in range(y0, y0 + len(steps) + 1):
        d.set(cx, y, cz, "diorite_wall")
    for i, (dx, dz) in enumerate(steps):
        nx, nz = steps[i + 1] if i + 1 < len(steps) else (dx * 2, dz * 2)
        f = {(1, 0): "east", (-1, 0): "west", (0, 1): "south", (0, -1): "north"}.get(
            (max(-1, min(1, nx - dx)), max(-1, min(1, nz - dz))) if abs(nx - dx) + abs(nz - dz) == 1 else (0, 0),
            "north")
        d.set(cx + dx, y0 + i, cz + dz, stair("diorite_stairs" if False else "polished_diorite_stairs", f))


def hw_fountain(d, cx, cz, L):
    """Round stone basin with a tiered fountain: the upper bowl's lips spill into the basin."""
    for x, z in disc(3.5, cx, cz):
        r2 = (x - cx) ** 2 + (z - cz) ** 2
        if r2 <= 6.3:
            d.set(x, 1, z, WATER)
            d.set(x, 0, z, SOLIDSUB)
        else:
            d.set(x, 1, z, "stone_bricks")
            d.set(x, 2, z, slab("stone_brick_slab"))
    if L <= 2:
        for x, z in ((cx - 1, cz), (cx + 1, cz + 1), (cx + 2, cz - 1)):
            d.set(x, 2, z, "lily_pad")
        d.set(cx, 1, cz, "stone_bricks")
        d.set(cx, 2, cz, "stone_brick_wall")
        d.set(cx, 3, cz, "potted_flowering_azalea_bush" if L == 2 else "potted_red_tulip")
        return
    for y in (2, 3):
        d.set(cx, y, cz, "stone_brick_wall")
    d.fill(cx - 1, 4, cz - 1, cx + 1, 4, cz + 1, "stone_bricks")
    for x, z in ((cx - 1, cz - 1), (cx + 1, cz - 1), (cx - 1, cz + 1), (cx + 1, cz + 1)):
        d.set(x, 5, z, "stone_bricks")
    for x, z in ((cx, cz), (cx - 1, cz), (cx + 1, cz), (cx, cz - 1), (cx, cz + 1)):
        d.set(x, 5, z, WATER)
    if L >= 4:                                         # second tier: an urn with a basin of water on top
        d.set(cx, 5, cz, "stone_brick_wall")
        d.set(cx, 6, cz, "stone_brick_wall")
        d.set(cx, 7, cz, "water_cauldron[level=3]")
    for x, z in ((cx - 2, cz + 1), (cx + 2, cz - 1), (cx + 1, cz + 2)):
        d.set(x, 2, z, "lily_pad")


def hw_bench(d, x, z, facing, n=2, along="x", y=2):
    bench(d, x, y, z, facing, "dark_oak", n, along)


def hw_urn(d, x, z, y=2, plant="flowering_azalea"):
    d.set(x, y, z, "stone_brick_wall")
    d.set(x, y + 1, z, "flower_pot") if False else d.set(x, y + 1, z, f"potted_{plant}_bush" if "azalea" in plant
                                                         else f"potted_{plant}")


def hw_parterre(d, x1, z1, x2, z2, flowers):
    """Box-hedge knot bed: clipped hedge edge, a cross of hedge, flowers in the four quarters."""
    cx, cz = (x1 + x2) // 2, (z1 + z2) // 2
    i = 0
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            d.set(x, 1, z, GRASS)
            if x in (x1, x2) or z in (z1, z2) or x == cx or z == cz:
                d.set(x, 2, z, lv("azalea") if (x + z) % 2 == 0 else lv("oak"))
            else:
                d.set(x, 2, z, flowers[i % len(flowers)])
                i += 1
    d.set(cx, 2, cz, "stone_brick_wall")
    d.set(cx, 3, cz, "potted_flowering_azalea_bush")


def hw_palm_house(d, L):
    lantern_on = L >= 3
    Hc = H_CEN
    # plinth + floors
    hw_plinth(d, PH_X1, PH_X2, PH_ZC - 7, PH_ZC + 7)
    if L >= 2:
        hw_plinth(d, 8, 18, PH_ZC - 5, PH_ZC + 5)
        hw_plinth(d, 36, 46, PH_ZC - 5, PH_ZC + 5)
        for z in range(PH_ZC - 4, PH_ZC + 5):           # wings open into the pavilion
            for x in (18, 19, 35, 36):
                d.set(x, 3, z, "polished_andesite")
    # the glass shells
    Hw = H_WNG5 if L >= 5 else H_WNG
    if L >= 2:
        hw_vault(d, 8, 18, PH_ZC, Hw, ends=True, end_open={(18, z) for z in range(PH_ZC - 4, PH_ZC + 5)} |
                 ({(8, z) for z in range(PH_ZC - 4, PH_ZC + 5)} if L >= 4 else set()))
        hw_vault(d, 36, 46, PH_ZC, Hw, ends=True, end_open={(36, z) for z in range(PH_ZC - 4, PH_ZC + 5)} |
                 ({(46, z) for z in range(PH_ZC - 4, PH_ZC + 5)} if L >= 4 else set()))
    if L >= 4:
        hw_apse(d, 8, PH_ZC, Hw, -1)
        hw_apse(d, 46, PH_ZC, Hw, 1)
    if L >= 5:                                            # cresting along the wing ridges
        for x in list(range(9, 18, 2)) + list(range(37, 46, 2)):
            d.set(x, 16, PH_ZC, "diorite_wall")
    opening = {(x, z) for x in (PH_X1, PH_X2) for z in range(PH_ZC - 2, PH_ZC + 3)} if L >= 2 else set()
    hw_vault(d, PH_X1, PH_X2, PH_ZC, Hc, end_open=opening)
    if L >= 2:
        for x in (PH_X1, PH_X2):                          # arched openings to the wings
            for z in range(PH_ZC - 2, PH_ZC + 3):
                for y in range(4, 7):
                    d.set(x, y, z, AIR)
                d.set(x, 7, z, "white_concrete")
            d.set(x, 6, PH_ZC - 2, stair("quartz_stairs" if L >= 4 else "polished_diorite_stairs", "north", "top"))
            d.set(x, 6, PH_ZC + 2, stair("quartz_stairs" if L >= 4 else "polished_diorite_stairs", "south", "top"))
    if lantern_on and L < 5:                              # clerestory lantern over the middle bays (L3-4)
        for x in range(23, 32):
            rib = (x - 23) % 2 == 0
            for z in range(PH_ZC - 2, PH_ZC + 3):
                k = abs(z - PH_ZC)
                for y in range(16, 21):
                    d.set(x, y, z, AIR)
                lo = min(H_LAN[k + 1] + 1, H_LAN[k]) if k < 2 else 16
                hw_column(d, x, z, lo, H_LAN[k], "glass", rib and k < 2)
                if k == 2:
                    for y in range(16, 19):
                        d.set(x, y, z, "white_concrete" if rib or y == 18 else "glass_pane")
        for x in (23, 31):
            for z in range(PH_ZC - 1, PH_ZC + 2):
                for y in range(17, H_LAN[abs(z - PH_ZC)]):
                    d.set(x, y, z, "glass_pane")
        for x in range(23, 32, 2):
            d.set(x, 21, PH_ZC, "diorite_wall") if L >= 4 else None
    if L >= 5:                                            # the great dome on a glass drum (L5)
        cx, cz, R, V, yb = 27, PH_ZC, 6.5, 11.0, 14
        disc_ = disc(R, cx, cz)
        rim = ring(R, cx, cz)
        for (x, z) in disc_:
            for y in range(yb, 27):
                inside = ((x - cx) / R) ** 2 + ((z - cz) / R) ** 2 + ((y - yb) / V) ** 2 <= 1.0
                if inside:
                    d.set(x, y, z, AIR)
        for (x, z) in disc_:
            for y in range(yb, 27):
                inside = ((x - cx) / R) ** 2 + ((z - cz) / R) ** 2 + ((y - yb) / V) ** 2 <= 1.0
                if not inside:
                    continue
                out = any(((x + a - cx) / R) ** 2 + ((z + c - cz) / R) ** 2 + ((y + b - yb) / V) ** 2 > 1.0
                          for a, b, c in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, 0, 1), (0, 0, -1)))
                if out:
                    rib = x == cx or z == cz or abs(x - cx) == abs(z - cz) or (y - yb) % 4 == 0
                    d.set(x, y, z, "white_concrete" if rib else "light_blue_stained_glass")
        for (x, z) in rim:                               # drum from the vault up to the dome
            top = max((y for y in range(4, yb) if d.get(x, y, z) != AIR), default=4)
            for y in range(top + 1, yb):
                d.set(x, y, z, "white_concrete" if (x + z) % 3 == 0 or y == yb - 1 else "glass_pane")
        d.set(cx, yb + 11, cz, "white_concrete")
        d.set(cx, yb + 12, cz, "diorite_wall")
        d.set(cx, yb + 13, cz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        for y in range(16, yb + 10):
            d.set(cx, y, cz, "chain[axis=y,waterlogged=false]") if y > 18 else None
        d.set(cx, 18, cz, lantern(True))
        for x in (PH_X1, PH_X2):
            d.set(x, 18, PH_ZC, "diorite_wall")
            d.set(x, 19, PH_ZC, "diorite_wall")
            d.set(x, 20, PH_ZC, "lantern[hanging=false,waterlogged=false]")
    # entrance: steps and door in the north wall, porch from L2
    zn = PH_ZC - 7
    for x in range(26, 29):
        d.set(x, 4, zn, AIR)
        d.set(x, 5, zn, AIR)
    d.door(26, 4, zn, "north", "dark_oak", "left") if False else None
    d.door(27, 4, zn, "north", "birch", "left")
    d.set(26, 4, zn, "glass_pane")
    d.set(28, 4, zn, "glass_pane")
    d.set(26, 5, zn, "glass_pane")
    d.set(28, 5, zn, "glass_pane")
    for x in range(25, 30):
        d.set(x, 2, zn - 2, stair("stone_brick_stairs", "south"))
        d.set(x, 3, zn - 1, stair("stone_brick_stairs", "south"))
        d.set(x, 2, zn - 1, "stone_bricks")
    if L >= 3:                                            # pedimented glass porch
        for x in (25, 29):
            for y in range(4, 8):
                d.set(x, y, zn - 1, "white_concrete")
        for x in range(24, 31):
            d.set(x, 8, zn - 1, "white_concrete")
            d.set(x, 8, zn, "white_concrete")
        for k, (a, b) in enumerate(((24, 30), (25, 29), (26, 28), (27, 27))):
            for x in range(a, b + 1):
                y = 9 + k
                st = "white_concrete" if x in (a, b) else "glass"
                d.set(x, y, zn - 1, st)
        for x in (26, 27, 28):
            d.set(x, 7, zn - 1, lantern(True)) if x == 27 else None
    d.sign(27, 7, zn - 1, "north", ["", "The Palm House", "", ""], "dark_oak") if L <= 2 else \
        d.sign(27, 7, zn - 2, "north", ["", "The Palm House", "", ""], "dark_oak")


def hw_palm_interior(d, L):
    """Central pavilion: lily pool with a fountain urn, palms (taller each level), tropical beds, benches;
    from L3 a gallery all round reached by two white spiral stairs."""
    y = 4
    zc = PH_ZC
    # lily pool
    for x, z in disc(2.3, 27, zc):
        d.set(x, 3, z, WATER)
    for x, z in ring(3.2, 27, zc):
        if d.get(x, 3, z) != "minecraft:water[level=0]":
            d.set(x, 4, z, slab("stone_brick_slab"))
    d.set(27, 4, zc, "stone_brick_wall")
    d.set(27, 5, zc, "water_cauldron[level=3]")
    for x, z in ((26, zc - 2), (28, zc + 1), (25, zc + 1)):
        d.set(x, 4, z, "lily_pad")
    rows = ["{[}]{.......{]}[{"[1:16],          # z=28 (north beds beside the door path)
            "].............]",
            "[.............}",
            "}.............[",
            "{.............{",
            "?.............?",
            "]..1.......1..]",
            "[.............[",
            "}.............}",
            "{.............{",
            "?.............?",
            "].............]",
            "{[}]!{[.[{!]}[{"]                 # z=40 (south beds; door path in the middle)
    plan(d, 20, y, 28, rows, HS, {}, HW_EXTRA)
    palms = [(24, 31), (30, 37), (24, 37), (30, 31)] if L < 3 else [(25, 31), (29, 37), (25, 37), (29, 31)]
    hgt = {1: 7, 2: 8, 3: 9, 4: 9, 5: 10}[L]
    for i, (x, z) in enumerate(palms):
        d.set(x, 3, z, "podzol")
        palm(d, x, 4, z, hgt - (i % 2), 8 if L >= 4 else 4)
    hw_bench(d, 26, zc - 4, "north", 3, "x", 4) if L >= 2 else hw_bench(d, 26, zc - 4, "north", 2, "x", 4)
    hw_bench(d, 26, zc + 4, "south", 3, "x", 4)
    for x, z in ((21, 33), (33, 35)):
        d.set(x, 4, z, "potted_red_tulip")
    d.hut(25, 4, 29, facing="north")
    if L >= 3:
        # gallery deck (two rows) all round, rails on the inner row
        for x in range(20, 35):
            for z in range(20, 41):
                k = abs(z - zc)
                ring_ = x in (20, 21, 33, 34) or k >= 4 and k <= 5
                if ring_ and 29 <= z <= 39:
                    d.set(x, 9, z, "polished_andesite" if x in (20, 34) or k == 5 else "dark_oak_planks")
        for x in range(21, 34):
            for z in (30, 38):
                d.set(x, 10, z, "iron_bars")
        for z in range(30, 39):
            for x in (21, 33):
                d.set(x, 10, z, "iron_bars")
        W = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1)]
        E = [(0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
        for (cx, cz, steps, gap) in ((23, 36, W, (21, 37)), (31, 32, E, (33, 31))):
            for dx, dz in steps:
                for yy in range(4, 12):
                    if d.get(cx + dx, yy, cz + dz) != AIR and yy >= 9:
                        d.set(cx + dx, yy, cz + dz, AIR)
            hw_spiral(d, cx, cz, steps)
            d.set(gap[0], 10, gap[1], AIR)
            d.set(gap[0], 9, gap[1], "dark_oak_planks")
        # gallery furniture: benches and planters looking down into the house
        for x, z, f in ((24, 29, "north"), (30, 39, "south")):
            d.chair(x, 10, z, f, "dark_oak")
            d.chair(x + 1, 10, z, f, "dark_oak")
        for x, z in ((20, 29), (34, 29), (20, 39), (34, 39), (27, 29), (27, 39)):
            d.set(x, 10, z, "potted_fern" if (x + z) % 2 else "potted_flowering_azalea_bush")
        for x, z in ((22, 30), (32, 38), (26, 30), (28, 38)):
            lamp_chain(d, x, 12, z, 14) if False else d.set(x, 13, z, lantern(True))


def hw_wing_rooms(d, L):
    """West wing: temperate house (citrus in tubs, propagation benches); east wing: tropical water-lily house."""
    zc = PH_ZC
    # west temperate house x9..17, z30..38
    rows = ["e?i?g.....",
            "..........",
            "]..ccc..]",
            "...cic...",
            "]........",
            "...cec...",
            "...ccc..]",
            "..........",
            "b?K?b.C.."]
    rows = ["e]i?g?i]e",
            ".........",
            "?.cgc.?..",
            "..cic....",
            "?........",
            "..cec..?.",
            "?.ccc....",
            ".........",
            "bKbCb]{]?"]
    plan(d, 9, 4, 30, rows, HS, {"K": "up"}, HW_EXTRA)
    for x, z in ((15, 32), (11, 35), (15, 36)):           # citrus trees in tubs (orange-blossom azalea)
        d.set(x, 4, z, "composter[level=8]" if False else "barrel[facing=up,open=false]")
        d.set(x, 5, z, lv("flowering_azalea"))
        d.set(x, 6, z, lv("flowering_azalea"))
    for x, z in ((12, 31), (12, 37)):
        d.set(x, 7, z, lantern(True))
    # east water-lily house x37..45, z30..38: a pond with lily pads and stepping stones
    for x in range(38, 45):
        for z in range(32, 37):
            d.set(x, 3, z, WATER)
    for x, z in ((39, 33), (42, 35), (40, 36), (43, 32), (38, 34)):
        d.set(x, 4, z, "lily_pad")
    for x in range(38, 45):
        d.set(x, 3, 34, "polished_andesite") if x % 2 == 0 else None
    rows = ["{}!}{!{}{",
            "!.......!",
            ".........",
            ".........",
            ".........",
            ".........",
            ".........",
            "?.......?",
            "[}{!]{}[{"]
    plan(d, 37, 4, 30, rows, HS, {}, HW_EXTRA)
    for x, z in ((38, 31), (44, 37)):
        d.chair(x, 4, z, "west" if x > 40 else "east", "dark_oak")
    for x, z in ((40, 32), (43, 36)):
        d.set(x, 7, z, lantern(True))
    d.set(41, 4, 31, "potted_blue_orchid")
    d.set(41, 4, 37, "potted_blue_orchid")


def hw_lodge(d, L):
    """Head gardener's lodge & tea room (L4): Tudor, brick plinth, calcite and dark-oak framing, jettied upper
    floor, steep tiled gable roof, kitchen hearth with a brick chimney. Ground: tea room + kitchen; upper:
    office + bedroom. L5: a potting bothy wing on the east side."""
    x1, x2, z1, z2 = 21, 33, 47, 55
    post = "dark_oak_log[axis=y]"
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            d.set(x, 1, z, "spruce_planks" if not (x in (x1, x2) or z in (z1, z2)) else "stone_bricks")
            edge = x in (x1, x2) or z in (z1, z2)
            for y in range(2, 6):
                if not edge:
                    d.set(x, y, z, AIR)
                    continue
                corner = x in (x1, x2) and z in (z1, z2)
                k = (x - x1) if z in (z1, z2) else (z - z1)
                if corner or k % 4 == 0:
                    st = post
                elif y == 2:
                    st = "bricks"
                elif y == 4 and k % 4 == 2 and 0 < k:
                    st = "glass_pane"
                elif y == 3 and k % 4 == 2:
                    st = "glass_pane"
                else:
                    st = "calcite"
                d.set(x, y, z, st)
    # upper floor jettied one cell out north and south
    for x in range(x1, x2 + 1):
        for z in range(z1 - 1, z2 + 2):
            d.set(x, 6, z, "dark_oak_planks" if (z in (z1 - 1, z2 + 1) or x in (x1, x2)) else "spruce_planks")
    for x in range(x1, x2 + 1):
        for z in (z1 - 1, z2 + 1):
            d.set(x, 5, z, stair("dark_oak_stairs", "north" if z < z1 else "south", "top")) if x % 2 == 1 else None
    zu1, zu2 = z1 - 1, z2 + 1
    for x in range(x1, x2 + 1):
        for z in range(zu1, zu2 + 1):
            edge = x in (x1, x2) or z in (zu1, zu2)
            for y in range(7, 11):
                if not edge:
                    d.set(x, y, z, AIR)
                    continue
                corner = x in (x1, x2) and z in (zu1, zu2)
                k = (x - x1) if z in (zu1, zu2) else (z - zu1)
                if corner or k % 4 == 0 or y == 10:
                    st = post if y < 10 else f"dark_oak_log[axis={'x' if z in (zu1, zu2) else 'z'}]"
                elif y in (8, 9) and k % 4 == 2:
                    st = "glass_pane"
                elif y == 7 and k % 2 == 1:
                    st = f"dark_oak_log[axis={'x' if z in (zu1, zu2) else 'z'}]" if False else "calcite"
                else:
                    st = "calcite"
                d.set(x, y, z, st)
    d.gable(x1, zu1, x2, zu2, 11, axis="x", stairs="deepslate_tile_stairs", ridge="deepslate_tile_slab",
            end="calcite", overhang=1)
    for x in (x1, x2):                                   # framed gable ends
        for z in range(zu1 + 2, zu2 - 1, 3):
            for y in range(11, 15):
                if d.get(x, y, z) == "minecraft:calcite":
                    d.set(x, y, z, post)
    # partitions: kitchen (ground, east) and bedroom (upper, east)
    for z in range(z1 + 1, z2):
        for y in range(2, 6):
            d.set(29, y, z, "calcite" if z % 3 else post)
        for y in range(7, 11):
            d.set(28, y, z, "calcite" if z % 3 else post)
    for z in range(zu1 + 1, z1 + 1):
        for y in range(7, 11):
            d.set(28, y, z, "calcite")
    for z in range(z2, zu2):
        for y in range(7, 11):
            d.set(28, y, z, "calcite")
    d.door(29, 2, 51, "east", "dark_oak")
    d.door(28, 7, 50, "east", "dark_oak")
    d.door(27, 2, z1, "north", "dark_oak")
    d.sign(27, 4, z1 - 1, "north", ["", "Tea Room", "", ""], "dark_oak", hanging=False) if False else None
    d.set(28, 4, z1 - 1, "dark_oak_wall_hanging_sign[facing=north,waterlogged=false]") if False else None
    # stair along the south wall: steps x23..26, landing on the upper floor at x27
    for i, x in enumerate(range(23, 27)):
        d.set(x, 2 + i, z2 - 1, stair("dark_oak_stairs", "east"))
    for x in (24, 25, 26):
        d.set(x, 6, z2 - 1, AIR)
    for x in (24, 25, 26):
        d.set(x, 7, z2 - 2, "dark_oak_fence")
    d.set(23, 7, z2 - 1, "dark_oak_fence")
    # kitchen hearth on the east wall with the chimney through the roof
    d.hearth(32, 2, 51, "west", 19, frame="bricks", fire="campfire")
    for y in range(2, 19):
        d.set(33, y, 51, "bricks")
    for z in (50, 52):
        for y in range(7, 19):
            d.set(33, y, z, "bricks") if y >= 11 else None
    d.set(33, 19, 51, "bricks")
    d.set(32, 19, 51, slab("brick_slab")) if False else None
    # ground floor: tea room (west) and kitchen (east)
    gf = ["a.1.1.f",
          "..T.T..",
          "..3.3..",
          "c......",
          "4T2..ce",
          ".......",
          "b......"]
    plan(d, 22, 2, 48, gf, HS, {"e": "north"})
    for x, y, z, st in ((30, 2, 48, "smoker[facing=south,lit=false]"), (31, 2, 48, slab("dark_oak_slab", "top")),
                        (32, 2, 48, "water_cauldron[level=3]"), (30, 2, 54, "barrel[facing=up,open=false]"),
                        (31, 2, 54, slab("dark_oak_slab", "top")), (32, 2, 54, "barrel[facing=up,open=false]"),
                        (31, 3, 54, "potted_red_tulip"), (30, 2, 53, "crafting_table"), (32, 2, 49, "furnace[facing=west,lit=false]")):
        d.set(x, y, z, st)
    for x, z in ((25, 49), (24, 52), (31, 51)):
        lamp_chain(d, x, 4, z, 6)
    d.rug(24, 50, 26, 51, 2, ("red_carpet", "orange_carpet"), "check") if False else None
    # upper floor: office (west) and bedroom (east)
    up = ["BB.Q.B",
          "......",
          "..cmc.",
          "...3..",
          "RooR..",
          "oRRo..",
          "......",
          "......",
          "bK...a"]
    plan(d, 22, 7, 47, up, HS, {"Q": "south", "K": "east"})
    d.bed(30, 7, 48, "north", "green")
    for x, y, z, st in ((29, 7, 47, slab("dark_oak_slab", "top")), (29, 8, 47, "candle[candles=2,lit=false,waterlogged=false]"),
                        (31, 7, 47, slab("dark_oak_slab", "top")), (31, 8, 47, lantern()),
                        (29, 7, 54, "chest[facing=north,type=single,waterlogged=false]"), (30, 7, 55, shelf("north")),
                        (31, 7, 55, shelf("north")), (32, 7, 54, "potted_fern"), (29, 7, 52, "green_carpet"),
                        (30, 7, 52, "green_carpet"), (30, 7, 53, "green_carpet"), (29, 7, 53, "green_carpet"),
                        (32, 7, 47, "potted_red_tulip"), (29, 7, 55, "barrel[facing=up,open=false]")):
        d.set(x, y, z, st)
    for x, z in ((24, 50), (25, 53), (30, 51)):
        d.set(x, 10, z, lantern(True))
    if L >= 4:                                           # potting bothy on the east side
        bx1, bx2, bz1, bz2 = 34, 40, 48, 54
        for x in range(bx1, bx2 + 1):
            for z in range(bz1, bz2 + 1):
                edge = x in (bx1, bx2) or z in (bz1, bz2)
                d.set(x, 1, z, "bricks" if edge else "stone_bricks")
                for y in range(2, 6):
                    if edge:
                        k = (x - bx1) if z in (bz1, bz2) else (z - bz1)
                        d.set(x, y, z, post if (x in (bx1, bx2) and z in (bz1, bz2)) or k % 3 == 0 else
                              ("bricks" if y == 2 else ("glass_pane" if y == 3 and k % 3 == 2 else "calcite")))
                    else:
                        d.set(x, y, z, AIR)
        d.gable(bx1, bz1, bx2, bz2, 6, axis="x", stairs="deepslate_tile_stairs", ridge="deepslate_tile_slab",
                end="calcite", overhang=1)
        d.door(37, 2, bz1, "north", "dark_oak")
        bothy = ["b.....",
                 "......",
                 "C....c",
                 "W....i",
                 "k....e"]
        bothy = ["bb.cgc"[0:5], ".....", "C...i", "W...c", "k8.bK"]
        plan(d, 35, 2, 49, bothy, HS, {"K": "west"})
        d.set(36, 4, 51, lantern(True))
        for x in range(35, 40):
            d.set(x, 4, 53, "dark_oak_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]") \
                if x in (35, 36) else None


def hw_kitchen_garden(d, L):
    """Walled kitchen garden behind the palm house: raised vegetable beds with a dipping tank, bean rows, fruit
    trees, bee hives (L4); L5 a lean-to vinery and peach house along the back wall."""
    beds = [(5, 44, 10, 47, "wheat[age=7]"), (12, 44, 18, 47, "carrots[age=7]"), (36, 44, 42, 46, "potatoes[age=7]"),
            (44, 44, 49, 47, "beetroots[age=3]"), (5, 50, 10, 53, "potatoes[age=7]"), (12, 50, 18, 53, "wheat[age=7]"),
            (44, 50, 49, 53, "carrots[age=7]")]
    for x1, z1, x2, z2, crop in beds:
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                edge = x in (x1, x2) or z in (z1, z2)
                d.set(x, 1, z, "spruce_planks" if False else ("stone_bricks" if edge else "farmland[moisture=7]"))
                d.set(x, 2, z, "dark_oak_slab[type=bottom,waterlogged=false]" if edge else crop)
        cx = (x1 + x2) // 2
        d.set(cx, 1, z1 + 1, WATER)
        d.set(cx, 2, z1 + 1, AIR)
        d.set(cx, 2, z1 + 1, "dark_oak_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]")
    for x, z in ((11, 49), (43, 48)):
        tree(d, x, 2, z, 3, "oak_log", "oak", r=2)
    for x, z in ((42, 51), (42, 53)):
        d.set(x, 2, z, "dark_oak_fence")
        d.set(x, 3, z, "beehive[facing=west,honey_level=3]")
    for x, z in ((19, 44), (35, 44)):
        d.set(x, 2, z, "water_cauldron[level=3]")
        d.set(x, 2, z + 1, "composter[level=6]")
    for xw, f, xi in ((0, "east", 1), (54, "west", 53)):  # lean-to vineries against the side walls
        xo = xi + (2 if xw == 0 else -2)
        xm = xi + (1 if xw == 0 else -1)
        for z in range(44, 57):
            end = z in (44, 56)
            for y in range(2, 8):
                d.set(xw, y, z, "bricks")
            d.set(xi, 1, z, "stone_bricks")
            d.set(xm, 1, z, "stone_bricks")
            d.set(xo, 1, z, "bricks")
            d.set(xo, 2, z, "bricks")
            for y in (3, 4):
                d.set(xo, y, z, "white_concrete" if z % 3 == 0 or end else "glass_pane")
            d.set(xo, 5, z, "white_concrete" if z % 3 == 0 else "glass")
            d.set(xm, 6, z, "white_concrete" if z % 3 == 0 else "glass")
            d.set(xi, 7, z, "white_concrete" if z % 3 == 0 else "glass")
            if end:
                for y in range(2, 6):
                    d.set(xm, y, z, "glass_pane" if y > 2 else "bricks")
                    d.set(xi, y, z, "glass_pane" if y > 2 else "bricks")
                d.set(xi, 6, z, "glass_pane")
            else:
                for y in range(2, 6):
                    d.set(xm, y, z, AIR)
                for y in range(2, 7):
                    d.set(xi, y, z, AIR)
        for z in (46, 49, 52, 55):                       # trained peach trees in tubs against the wall
            d.set(xi, 2, z, "barrel[facing=up,open=false]")
            d.set(xi, 3, z, lv("flowering_azalea"))
            d.set(xi, 4, z, lv("azalea"))
        for z in (47, 53):
            d.set(xi, 2, z, slab("dark_oak_slab", "top"))
            d.set(xi, 3, z, "potted_fern" if z == 47 else "potted_red_tulip")
        for z in (45, 48, 51, 54):
            d.set(xi, 6, z, "cave_vines[age=25,berries=true]")
        d.door(xo, 2, 50, f, "dark_oak")
        d.set(xo, 4, 50, "white_concrete")
    d.set(18, 2, 49, "hay_block[axis=y]")
    d.set(18, 3, 49, "carved_pumpkin[facing=north]")
    for x in range(2, 53):                               # gravel walks
        for z in (48, 49) if False else (42, 43):
            if d.get(x, 1, z) == "minecraft:" + GRASS:
                d.set(x, 1, z, "gravel")
    for z in range(42, 56):
        for x in (26, 27, 28):
            if d.get(x, 1, z) == "minecraft:" + GRASS:
                d.set(x, 1, z, "gravel")


def hw_orangery(d, L):
    """L5: classical orangery across the back of the walled garden: calcite walls between stone pilasters, tall
    windows, a balustraded flat roof with urns and a central pedimented pavilion under a glazed dome.
    Inside: citrus trees in tubs down both sides, benches, and a tea salon under the dome."""
    x1, x2, z1, z2 = 6, 48, 58, 66
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            edge = x in (x1, x2) or z in (z1, z2)
            d.set(x, 1, z, "stone_bricks" if edge else ("polished_andesite" if (x + z) % 2 else "calcite"))
            for y in range(2, 9):
                if not edge:
                    d.set(x, y, z, AIR)
                    continue
                k = (x - x1) if z in (z1, z2) else (z - z1)
                pil = k % 3 == 0
                if y == 2 or y == 8:
                    st = "stone_bricks"
                elif pil:
                    st = "stone_bricks" if y != 7 else "chiseled_stone_bricks"
                elif z == z1 and 3 <= y <= 6:
                    st = "glass_pane"
                elif z == z2 and 4 <= y <= 5:
                    st = "glass_pane"
                elif x in (x1, x2) and 3 <= y <= 6 and k % 3 != 0:
                    st = "glass_pane"
                else:
                    st = "calcite"
                d.set(x, y, z, st)
            if not edge:
                d.set(x, 9, z, "smooth_stone")
            else:
                d.set(x, 9, z, "stone_bricks")
                k = (x - x1) if z in (z1, z2) else (z - z1)
                d.set(x, 10, z, "stone_bricks" if k % 6 == 0 else "stone_brick_wall")
                if k % 6 == 0:
                    d.set(x, 11, z, "potted_flowering_azalea_bush" if z == z1 else "potted_fern")
    for x in range(x1, x2 + 1):                          # cornice
        d.set(x, 8, z1 - 1, stair("stone_brick_stairs", "south", "top"))
    # end pavilions: an upper storey over each end bay (seed library west, herbarium east)
    for (ex1, ex2, lad) in ((x1, x1 + 6, x1 + 1), (x2 - 6, x2, x2 - 1)):
        for x in range(ex1, ex2 + 1):
            for z in range(z1, z2 + 1):
                edge = x in (ex1, ex2) or z in (z1, z2)
                d.set(x, 9, z, "stone_bricks" if edge else "spruce_planks")
                for y in range(10, 14):
                    if not edge:
                        d.set(x, y, z, AIR)
                        continue
                    k = (x - ex1) if z in (z1, z2) else (z - z1)
                    d.set(x, y, z, "stone_bricks" if k % 3 == 0 or y == 13 else
                          ("glass_pane" if y in (11, 12) else "calcite"))
                d.set(x, 14, z, "stone_bricks" if edge else "smooth_stone")
                if edge:
                    corner = x in (ex1, ex2) and z in (z1, z2)
                    d.set(x, 15, z, "stone_bricks" if corner else slab("stone_brick_slab"))
                    if corner:
                        d.set(x, 16, z, "potted_flowering_azalea_bush")
        for y in range(2, 10):
            d.set(lad, y, z2 - 1, f"ladder[facing=north,waterlogged=false]")
        d.set(lad, 9, z2 - 1, f"ladder[facing=north,waterlogged=false]")
        d.set(lad, 10, z2 - 1, AIR)
    lib = ["S.S.S",
           ".....",
           "1.1..",
           "T.T.Q",
           "3.3..",
           ".....",
           "..Bb."]
    lib = ["SSSSS",
           ".....",
           "1.1.b",
           "TtT..",
           "3.3.Q",
           ".....",
           ".BB.."]
    plan(d, x1 + 1, 10, z1 + 1, lib, HS, {"S": "south", "Q": "west"})
    herb = ["...KK",
            "c...b",
            "i.m.c",
            "c.3.e",
            ".....",
            "W...k",
            "...nb"]
    herb = ["KK...",
            "b...c",
            "c.m.i",
            "e.3.c",
            ".....",
            "k...W",
            "bn..."]
    plan(d, x2 - 5, 10, z1 + 1, herb, HS, {"K": "north"})
    for x, z in ((x1 + 3, z1 + 4), (x2 - 3, z1 + 4)):
        d.set(x, 13, z, lantern(True))
    # central pavilion projecting north with a pediment and a glazed dome
    px1, px2, pz = 22, 32, 56
    for x in range(px1, px2 + 1):
        for z in range(pz, z1):
            edge = x in (px1, px2) or z == pz
            d.set(x, 1, z, "stone_bricks")
            for y in range(2, 10):
                if not edge:
                    d.set(x, y, z, AIR)
                    continue
                col = x in (px1, px2, 24, 26, 28, 30) and z == pz
                d.set(x, y, z, ("quartz_pillar[axis=y]" if col and 2 < y < 9 else "stone_bricks") if (col or y in (2, 9))
                      else ("glass_pane" if 3 <= y <= 7 else "calcite"))
        for z in range(pz, z1 + 1):
            d.set(x, 10, z, "stone_bricks")
    for k in range(6):                                   # pediment
        for x in range(px1 + k, px2 - k + 1):
            d.set(x, 11 + k, pz, "calcite" if px1 + k < x < px2 - k else
                  stair("stone_brick_stairs", "east" if x == px1 + k else "west"))
    for x in range(px1, px2 + 1):
        for z in range(pz + 1, z1):
            d.set(x, 10, z, "stone_bricks")
    cx, cz = 27, 62
    for (x, z) in disc(4.2, cx, cz):                     # drum and glazed dome over the tea salon
        for y in range(9, 11):
            if (x, z) in ring(4.2, cx, cz):
                d.set(x, y, z, "stone_bricks" if y == 9 else "calcite")
            else:
                d.set(x, y, z, AIR)
    for y, r in ((11, 4.2), (12, 3.8), (13, 3.2), (14, 2.4), (15, 1.4)):
        for (x, z) in ring(r, cx, cz):
            rib = x == cx or z == cz
            d.set(x, y, z, "white_concrete" if rib else "glass")
    d.set(cx, 16, cz, "white_concrete")
    d.set(cx, 17, cz, "diorite_wall")
    d.set(cx, 18, cz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    for x in (26, 27, 28):
        d.set(x, 2, pz, AIR)
        d.set(x, 3, pz, AIR)
    d.door(26, 2, pz, "north", "dark_oak", "left")
    d.door(28, 2, pz, "north", "dark_oak", "right")
    d.set(27, 2, pz, "glass_pane")
    d.set(27, 3, pz, "glass_pane")
    for x in (12, 42):
        d.door(x, 2, z1, "north", "dark_oak")
    # interior: citrus tubs down both sides, benches between, tea salon under the dome (hand-placed)
    tubs = [8, 11, 15, 18, 36, 39, 43, 46]
    for x in tubs:
        for z in (60, 64):
            d.set(x, 2, z, "barrel[facing=up,open=false]")
            d.set(x, 3, z, lv("flowering_azalea"))
            d.set(x, 4, z, lv("flowering_azalea" if x % 2 else "azalea"))
    for x in (9, 16, 37, 44):
        d.chair(x, 2, 62, "west", "dark_oak")
        d.chair(x + 1, 2, 62, "east", "dark_oak")
    for x, z in ((13, 63), (20, 61), (34, 61), (41, 63), (7, 62), (47, 62)):
        d.set(x, 2, z, ("potted_red_tulip", "potted_fern", "potted_blue_orchid")[(x + z) % 3])
    for x, z in ((20, 64), (34, 64)):
        d.set(x, 2, z, slab("dark_oak_slab", "top"))
        d.set(x, 3, z, dpot("north"))
    salon = [(25, 60), (29, 60), (25, 64), (29, 64)]
    for x, z in salon:
        d.table(x, 2, z, "dark_oak")
        d.chair(x - 1, 2, z, "west", "dark_oak")
        d.chair(x + 1, 2, z, "east", "dark_oak")
    d.set(27, 2, 62, "stone_brick_wall")
    d.set(27, 3, 62, "water_cauldron[level=3]")
    for x, z in ((26, 61), (28, 61), (26, 63), (28, 63)):
        d.set(x, 2, z, "red_carpet")
    for x, z in ((12, 62), (21, 62), (33, 62), (42, 62), (27, 59), (27, 65)):
        lamp_chain(d, x, 7, z, 9)
    for x, z in ((23, 57), (31, 57)):
        d.set(x, 2, z, "potted_flowering_azalea_bush")
        d.set(x, 5, z, lantern(True))
    for xb in (8, 16, 37, 45):                           # benches and tubs along the orangery front
        bench(d, xb, 2, 57, "south", "dark_oak", 2)
    for x in (13, 20, 34, 41):
        d.set(x, 2, 57, "potted_red_tulip" if x in (13, 41) else "potted_fern")


def hw_gatehouse(d):
    """L5: Tudor gatehouse over the garden gate: brick ground storey with a four-centred arch, porter's lodge and
    tool store either side, a timber-framed upper room (garden office) and two octagonal brick turrets."""
    x1, x2, z1, z2 = 21, 33, 0, 5
    post = "dark_oak_log[axis=y]"
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            d.set(x, 1, z, "stone_bricks")
            edge = x in (x1, x2) or z in (z1, z2) or x in (24, 30)
            for y in range(2, 6):
                if 25 <= x <= 29:                        # carriage passage
                    d.set(x, y, z, AIR)
                    continue
                d.set(x, y, z, ("bricks" if not (y == 3 and z in (2, 3) and x in (x1, x2)) else "glass_pane")
                      if edge else AIR)
    for x in range(25, 30):                              # gravel through the arch
        for z in range(z1, z2 + 1):
            d.set(x, 1, z, "gravel")
    for z in (z1, z2):                                   # four-centred arch faces
        d.set(25, 5, z, stair("stone_brick_stairs", "east", "top"))
        d.set(29, 5, z, stair("stone_brick_stairs", "west", "top"))
        for x in (26, 27, 28):
            d.set(x, 5, z, "stone_bricks")
        d.set(27, 4, z, AIR)
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            d.set(x, 6, z, "dark_oak_planks" if (x in (x1, x2) or z in (z1, z2)) else "spruce_planks")
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            edge = x in (x1, x2) or z in (z1, z2)
            for y in range(7, 11):
                if not edge:
                    d.set(x, y, z, AIR)
                    continue
                k = (x - x1) if z in (z1, z2) else (z - z1)
                if (x in (x1, x2) and z in (z1, z2)) or k % 3 == 0 or y == 10:
                    st = post if y < 10 else f"dark_oak_log[axis={'x' if z in (z1, z2) else 'z'}]"
                elif y in (8, 9) and k % 3 != 0 and z in (z1, z2):
                    st = "glass_pane"
                else:
                    st = "calcite"
                d.set(x, y, z, st)
    d.gable(x1, z1, x2, z2, 11, axis="x", stairs="deepslate_tile_stairs", ridge="deepslate_tile_slab",
            end="calcite", overhang=1)
    for tx in (x1 - 1, x2 + 1):                          # turrets
        for z in range(0, 3):
            for x in range(tx - 1, tx + 2):
                if abs(x - tx) + abs(z - 1) == 2 and x != tx and z != 1:
                    continue
                for y in range(2, 14):
                    d.set(x, y, z, "bricks" if (x, z) != (tx, 1) or y < 2 else AIR)
                d.set(x, 14, z, "stone_brick_wall")
        d.set(tx, 2, 1, "bricks")
        for y in (5, 9, 12):
            d.set(tx, y, 0, "glass_pane")
        d.set(tx, 13, 1, "bricks")
        d.set(tx, 14, 1, "stone_bricks")
        d.set(tx, 15, 1, lantern())
    # ladder up from the porter's lodge
    for y in range(2, 7):
        d.set(22, y, 4, "ladder[facing=north,waterlogged=false]")
    d.set(22, 7, 4, AIR) if False else None
    d.door(23, 2, z2, "south", "dark_oak") if False else None
    d.door(24, 2, 3, "east", "dark_oak")
    d.door(30, 2, 3, "west", "dark_oak")
    # furnish: porter's lodge (west), tool store (east), garden office upstairs
    for x, y, z, st in ((23, 2, 1, "barrel[facing=up,open=false]"), (22, 2, 1, slab("dark_oak_slab", "top")),
                        (22, 3, 1, lantern()), (22, 2, 2, stair("dark_oak_stairs", "west")),
                        (23, 2, 4, "potted_fern"),
                        (31, 2, 1, "barrel[facing=up,open=false]"), (32, 2, 1, "barrel[facing=north,open=false]"),
                        (31, 2, 4, "grindstone[face=floor,facing=north]"), (32, 2, 4, "crafting_table"),
                        (32, 2, 2, "composter[level=3]"), (31, 4, 3, lantern(True))):
        d.set(x, y, z, st)
    up = ["Q.c....c.BB",
          "...1.R..o..",
          ".mcc.RoRo.a",
          "...3.......".replace("...", ".", 0)]
    up = [".Q.cmc..BBa",
          "....3...RRo",
          "f.......oRR",
          "...4T2....z"]
    plan(d, 22, 7, 1, up, HS, {"Q": "south"})
    for x, z in ((25, 2), (29, 3)):
        d.set(x, 10, z, lantern(True))
    d.sign(27, 6, -1 + 1, "north", ["", "Hearthwood", "Palm House", ""], "dark_oak") if False else None


def hw_gardens(rel, L):
    sx, sy, sz = HW["size"]
    d = Design("Hearthwood", rel, HW["size"], paving="gravel")
    for x in range(sx):
        for z in range(sz):
            d.set(x, 1, z, GRASS)
    # ------------------------------------------------------------ central walk and the fountain
    for z in range(0, 25):
        for x in range(25, 30):
            d.set(x, 1, z, "gravel" if 26 <= x <= 28 else "stone_bricks")
    for x in range(2, 53):
        for z in (15, 16):
            d.set(x, 1, z, "gravel")
    for x in (7, 47):
        for z in range(0, 2):
            for xx in (x - 1, x, x + 1):
                d.set(xx, 1, z, "gravel")
        for z in range(13, 15):
            d.set(x, 1, z, "gravel")
    hw_fountain(d, 27, 8, L)
    for x in range(22, 33):                              # gravel round the basin
        for z in range(3, 14):
            if d.get(x, 1, z) == "minecraft:" + GRASS:
                if (x - 27) ** 2 + (z - 8) ** 2 <= 30:
                    d.set(x, 1, z, "gravel")
    hw_urn(d, 23, 4)
    hw_urn(d, 31, 4)
    hw_bench(d, 22, 8, "west", 2, "z") if False else bench(d, 22, 2, 7, "west", "dark_oak", 2, "z")
    bench(d, 32, 2, 8, "east", "dark_oak", 2, "z")
    for x, z in ((24, 1), (30, 1), (24, 14), (30, 14)):
        lamppost(d, x, z, 2, 3, "dark_oak_fence", lantern())
    # ------------------------------------------------------------ the palm house
    hw_palm_house(d, L)
    hw_palm_interior(d, L)
    if L >= 2:
        hw_wing_rooms(d, L)
    if L >= 3:
        hw_parterre(d, 14, 3, 20, 11, ("red_tulip", "white_tulip", "poppy", "oxeye_daisy"))
        hw_parterre(d, 34, 3, 40, 11, ("pink_tulip", "cornflower", "allium", "white_tulip"))
        for x, z in ((17, 13), (37, 13)):
            hw_urn(d, x, z, plant="red_tulip")
    # ------------------------------------------------------------ L3: terrace walk and the walled garden
    if L >= 3:
        for x in range(8, 47):
            for z in range(21, 27):
                edge = z == 21 or x in (8, 46)
                d.set(x, 2, z, "bricks" if edge else SOLIDSUB)
                d.set(x, 3, z, "stone_bricks" if edge else ("stone_bricks" if (x + z) % 4 else "mossy_stone_bricks"))
        for x in range(8, 47):                           # balustrade with urns on the piers
            if 24 <= x <= 30 or x in (12, 13, 41, 42):
                continue
            pier = (x - 8) % 6 == 0
            d.set(x, 4, 21, "stone_bricks" if pier else "stone_brick_wall")
            if pier:
                d.set(x, 5, 21, "potted_red_tulip" if L < 5 else "potted_flowering_azalea_bush")
        for x in range(24, 31):                          # central steps
            d.set(x, 2, 20, stair("stone_brick_stairs", "south"))
            d.set(x, 3, 21, stair("stone_brick_stairs", "south"))
            d.set(x, 2, 21, "stone_bricks")
        for x in (12, 13, 41, 42):                       # side steps
            d.set(x, 2, 20, stair("stone_brick_stairs", "south"))
            d.set(x, 3, 21, stair("stone_brick_stairs", "south"))
        for x, z in ((10, 24), (44, 24), (18, 23), (36, 23)):
            bench(d, x - 1, 4, z, "south", "dark_oak", 2) if False else None
        bench(d, 15, 4, 26, "south", "dark_oak", 2)
        bench(d, 38, 4, 26, "south", "dark_oak", 2)
        for x, z in ((10, 23), (44, 23), (21, 23), (33, 23)):
            hw_urn(d, x, z, 4, "flowering_azalea")
        # the garden wall: brick with stone coping, buttress piers, gate piers with lanterns
        for x in range(sx):
            for z in range(sz):
                if not (x in (0, sx - 1) or z in (0, sz - 1)):
                    continue
                if z == 0 and (23 <= x <= 31 or 5 <= x <= 9 or 45 <= x <= 49):
                    continue
                pier = (x + z) % 6 == 0
                for y in range(2, 4 + (1 if pier else 0)):
                    d.set(x, y, z, "bricks")
                d.set(x, 4 + (1 if pier else 0), z, slab("stone_brick_slab"))
        for x in (23, 31) if L < 5 else ():
            for y in range(2, 6):
                d.set(x, y, 0, "stone_bricks")
            d.set(x, 6, 0, "stone_brick_wall")
            d.set(x, 7, 0, lantern())
        for x in (5, 9, 45, 49):
            for y in range(2, 5):
                d.set(x, y, 0, "stone_bricks")
            d.set(x, 5, 0, "potted_red_tulip")
    # ------------------------------------------------------------ L4: lily canals and the kitchen garden
    if L >= 4:
        for x1 in (12, 34):
            for x in range(x1, x1 + 9):
                for z in (17, 18, 19):
                    edge = x in (x1, x1 + 8) or z in (17, 19)
                    d.set(x, 1, z, "stone_bricks" if edge else WATER)
            for x in (x1 + 2, x1 + 5):
                d.set(x, 2, 18, "lily_pad")
        for x1, x2 in ((3, 17), (37, 51)):               # vegetable beds behind the house (farmers' showcase)
            for x in range(x1, x2 + 1):
                for z in (43, 44):
                    crop = ("wheat[age=7]", "carrots[age=7]", "potatoes[age=7]", "beetroots[age=3]")[(x // 3) % 4]
                    d.set(x, 1, z, "farmland[moisture=7]")
                    d.set(x, 2, z, crop)
            d.set((x1 + x2) // 2, 1, 43, WATER)
            d.set((x1 + x2) // 2, 1, 44, WATER)
            d.set((x1 + x2) // 2, 2, 43, AIR)
            d.set((x1 + x2) // 2, 2, 44, AIR)
            d.set((x1 + x2) // 2, 2, 43, "dark_oak_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]")
            d.set((x1 + x2) // 2, 2, 44, "dark_oak_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]")
        for x in range(3, 52):                           # rose arches over the cross walk
            if x % 4 == 1 and not 23 <= x <= 31:
                for z in (15, 16):
                    pass
        for x in range(4, 51, 4):
            if 22 <= x <= 32:
                continue
            for z in (14, 17):
                for y in (2, 3, 4):
                    d.set(x, y, z, "dark_oak_fence")
            for z in (14, 15, 16, 17):
                d.set(x, 5, z, "dark_oak_planks" if z in (14, 17) else lv("flowering_azalea"))
            d.set(x, 4, 15, "rose_bush[half=upper]") if False else None
    if L >= 4:
        hw_lodge(d, L)
        hw_kitchen_garden(d, L)
        zs = PH_ZC + 7                                   # garden door in the south wall of the palm house
        d.door(27, 4, zs, "south", "birch")
        for x in (26, 27, 28):
            d.set(x, 2, zs + 1, "bricks")
            d.set(x, 3, zs + 1, stair("stone_brick_stairs", "north"))
            d.set(x, 2, zs + 2, stair("stone_brick_stairs", "north"))
    if L >= 5:
        hw_orangery(d, L)
        hw_gatehouse(d)
        for xa in (2, 49):                               # rose pergola walks along the side walls
            for z in range(14, 27):
                for x in range(xa, xa + 4):
                    d.set(x, 1, z, "gravel" if xa < x < xa + 3 else GRASS)
                if z % 3 == 2:
                    for x in (xa, xa + 3):
                        for y in (2, 3, 4):
                            d.set(x, y, z, "dark_oak_fence")
                    for x in range(xa, xa + 4):
                        d.set(x, 5, z, "dark_oak_planks" if x in (xa, xa + 3) else
                              f"dark_oak_log[axis=x]")
                else:
                    for x in (xa, xa + 3):
                        flower(d, x, 2, z, ("rose_bush", "peony", "lilac")[z % 3])
                    for x in range(xa, xa + 4):
                        d.set(x, 5, z, lv("flowering_azalea") if x in (xa, xa + 3) else lv("azalea")) \
                            if z % 3 == 1 else None
        for z in range(54, 58):
            for x in (26, 27, 28):
                d.set(x, 1, z, "gravel")
        for x in range(4, 51):
            d.set(x, 1, 57, "gravel") if d.get(x, 1, 57) == "minecraft:" + GRASS else None
        for x, z in ((15, 20), (39, 20)):
            d.set(x, 2, z, "stone_bricks")
            d.set(x, 3, z, "stone_brick_wall")
            d.set(x, 4, z, "lantern[hanging=false,waterlogged=false]")
    place_wings(d, HW["res"], HW["wsize"], HW["whut"])
    connect_walls(d)
    return d


def hw_wing(rel, L):
    """Octagonal orangery pavilion: brick base, tall glass walls between white piers, an ogee roof of tiles with
    a lantern; citrus trees in tubs and a potting bench inside."""
    d = wing_design("Hearthwood", rel, HW["wsize"])
    cx = cz = 5
    r = {1: 3, 2: 4, 3: 4, 4: 5, 5: 5}[L]
    hgt = {1: 3, 2: 4, 3: 5, 4: 5, 5: 7}[L]
    cut = {3: 1, 4: 1, 5: 2}[r]
    x1, x2, z1, z2 = cx - r, cx + r, cz - r, cz + r

    def inside(x, z, rr=r, cc=None):
        c = cut if cc is None else cc
        return abs(x - cx) <= rr and abs(z - cz) <= rr and abs(x - cx) + abs(z - cz) <= 2 * rr - c

    for x in range(11):
        for z in range(11):
            d.set(x, 0, z, "gravel")
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if not inside(x, z):
                continue
            edge = not all(inside(x + a, z + b) for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            d.set(x, 0, z, "bricks" if edge else ("polished_andesite" if (x + z) % 2 else "stone_bricks"))
            for y in range(1, hgt + 1):
                if not edge:
                    continue
                pier = abs(x - cx) == abs(z - cz) or (abs(x - cx) == r and abs(z - cz) == r - cut) or \
                    (abs(z - cz) == r and abs(x - cx) == r - cut)
                if y == 1:
                    st = "bricks"
                elif pier or y == hgt:
                    st = "white_concrete"
                else:
                    st = "glass_pane"
                d.set(x, y, z, st)
    # ogee roof: shrinking octagon rings of tiles, a glass lantern and a finial
    y = hgt + 1
    rr = r
    while rr >= 1:
        for x in range(cx - rr, cx + rr + 1):
            for z in range(cz - rr, cz + rr + 1):
                if not inside(x, z, rr, min(cut, rr)):
                    continue
                edge = not all(inside(x + a, z + b, rr, min(cut, rr)) for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                if not edge and rr > 1:
                    continue
                f = "south" if z < cz else "north" if z > cz else ("east" if x < cx else "west")
                if abs(x - cx) > abs(z - cz):
                    f = "east" if x < cx else "west"
                if rr <= 1 and L >= 3:
                    st = "glass"
                elif L >= 4:
                    st = stair("deepslate_tile_stairs", f)
                else:
                    st = stair("dark_oak_stairs", f) if L < 3 else stair("deepslate_tile_stairs", f)
                d.set(x, y, z, st)
        y += 1
        rr -= 1
    if L >= 5:                                           # glazed lantern on the roof
        for x in range(cx - 1, cx + 2):
            for z in range(cz - 1, cz + 2):
                for yy in (y, y + 1):
                    d.set(x, yy, z, "white_concrete" if (x - cx) * (z - cz) != 0 else "glass")
                d.set(x, y + 2, z, stair("deepslate_tile_stairs", "south" if z < cz else "north" if z > cz else
                                         ("east" if x < cx else "west")) if (x, z) != (cx, cz) else "white_concrete")
        y += 2
    d.set(cx, y, cz, "white_concrete")
    d.set(cx, y + 1, cz, "diorite_wall")
    d.set(cx, y + 2, cz, "lightning_rod[facing=up,powered=false,waterlogged=false]" if L >= 3 else "diorite_wall")
    # doors on the axis
    for z in (cz - r, cz + r):
        d.door(cx, 1, z, "north" if z < cz else "south", "dark_oak")
    d.hut(*HW["whut"], facing="north")
    d.item(10 - HW["whut"][0], 1, HW["whut"][2], "composter")
    # furniture per level (hand-placed)
    if L == 1:
        items = [(4, 1, 7, "barrel"), (6, 1, 7, "potted_flowering_azalea_bush"), (3, 1, 6, "potted_red_tulip"),
                 (7, 1, 6, "potted_fern")]
    else:
        items = [(5, 1, 7 + (r >= 5), "tub"), (3, 1, 3, "potted_flowering_azalea_bush"),
                 (7, 1, 3, "potted_flowering_azalea_bush")]
        if r >= 4:
            items += [(2, 1, 5, "tub"), (8, 1, 5, "tub"), (3, 1, 7, "bench_w"), (7, 1, 7, "bench_e")]
        if r >= 5:
            items += [(2, 1, 3, "potted_red_tulip"), (8, 1, 3, "potted_red_tulip"), (2, 1, 7, "potted_fern"),
                      (8, 1, 7, "potted_fern"), (4, 1, 8, "counter"), (6, 1, 8, "counter_pot")]
    for x, y, z, k in items:
        if k == "tub":
            d.set(x, y, z, "barrel[facing=up,open=false]")
            d.set(x, y + 1, z, lv("flowering_azalea"))
            if hgt >= 5:
                d.set(x, y + 2, z, lv("azalea"))
        elif k == "bench_w":
            d.chair(x, y, z, "west", "dark_oak")
        elif k == "bench_e":
            d.chair(x, y, z, "east", "dark_oak")
        elif k == "counter":
            d.set(x, y, z, slab("dark_oak_slab", "top"))
            d.set(x, y + 1, z, "potted_red_tulip")
        elif k == "counter_pot":
            d.set(x, y, z, slab("dark_oak_slab", "top"))
            d.set(x, y + 1, z, dpot("north"))
        elif k == "barrel":
            d.set(x, y, z, "barrel[facing=up,open=false]")
        else:
            d.set(x, y, z, k)
    d.set(cx, hgt, cz, lantern(True)) if d.air(cx, hgt, cz) else None
    connect_walls(d)
    return d


# =============================================================================================================
#                                    CASCADIA  -  CASCADE GARDENS
# =============================================================================================================
CA = dict(size=(49, 40, 57), wsize=(11, 14, 11), whut=(3, 1, 5), res=((1, 1), (37, 1)))
CS = dict(wood="spruce", counter="spruce_slab", rug=("brown", "green", "orange"), block="spruce_planks",
          bedcol="brown")
# terraces: (x1, x2, z1, z2, top)  - built one per level
CA_T = [(3, 45, 15, 24, 4), (5, 43, 25, 32, 7), (7, 41, 33, 40, 10), (9, 39, 41, 47, 13), (11, 37, 48, 55, 16)]
ROCK = ("cobblestone", "mossy_cobblestone", "andesite", "tuff", "stone", "cobblestone", "mossy_cobblestone")
CA_STAIRS = (19, 20, 28, 29)                              # stair flights either side of the cascade
CA_FALL = (23, 24, 25)                                    # the cascade
_F, _B, _M, _L = "fern", "sweet_berry_bush[age=3]", "mossy_cobblestone", "large_fern"
CA_LIP = {0: [(4, _F), (8, _M), (12, _L), (16, _B), (32, _F), (36, _M), (40, _L), (44, _B)],
          1: [(6, _M), (10, _L), (14, _B), (34, _F), (38, _M), (42, _L)],
          2: [(8, _L), (12, _B), (16, _F), (20, _M), (28, _F) if False else (27, _B)],
          3: [(10, _B), (14, _F), (18, _M), (30, _L), (34, _B), (38, _F)],
          4: [(26, _F), (30, _M), (34, _L)]}


def rock(x, y, z):
    return ROCK[(x * 7 + y * 13 + z * 5) % len(ROCK)]


def ca_terrace(d, k, last):
    """Terrace k: rock-faced block from the ground to its planted top; only the open faces are real rock."""
    x1, x2, z1, z2, top = CA_T[k]
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            for y in range(2, top + 1):
                face = x in (x1, x2) or z == z1 or (z == z2 and last)
                d.set(x, y, z, rock(x, y, z) if face else SOLIDSUB)
            surf = "moss_block" if x in (x1, x2) or z == z1 else ("coarse_dirt" if (x + z * 3) % 13 == 0 else GRASS)
            d.set(x, top, z, surf)
    # ragged top edge: boulders, ferns and berry bushes on the front lip (hand-picked cells per terrace)
    for x, what in CA_LIP[k]:
        if what == "large_fern":
            flower(d, x, top + 1, z1, what)
        else:
            d.set(x, top + 1, z1, what)
    # stairs cut into the front face (both flights)
    py = 1 if k == 0 else CA_T[k - 1][4]
    for x in CA_STAIRS:
        for i in range(3):
            d.set(x, py + 1 + i, z1 + i, stair("cobblestone_stairs" if i % 2 == 0 else "mossy_cobblestone_stairs",
                                                "south"))
            for y in range(py + 2 + i, top + 4):
                d.set(x, y, z1 + i, AIR)
    # the stream: a pool at the back, a three-wide channel to the lip, a notch in the riser below the lip
    for x in CA_FALL:
        for z in range(z1, z2 + 1):
            d.set(x, top, z, WATER)
            d.set(x, top + 1, z, AIR)
        for y in range(py + 1, top):
            d.set(x, y, z1, WATER)
    for x in (22, 26):
        for z in range(z2 - 1, z2 + 1):
            d.set(x, top, z, WATER)
            d.set(x, top + 1, z, AIR)
    for x in (21, 22, 26, 27):                            # mossy boulders along the banks
        if (x + k) % 2:
            d.set(x, top + 1, z1 + 2 + k % 3, "mossy_cobblestone")
    if last:                                              # back wall behind the pool of the highest terrace
        for x in (22, 23, 24, 25, 26):
            d.set(x, top, z2, rock(x, top, z2))
            d.set(x, top + 1, z2, rock(x, top + 1, z2))
        for x in (21, 27):
            d.set(x, top + 1, z2, "mossy_cobblestone")


def ca_aframe(d, x1, x2, z1, z2, y0, end="spruce_planks", ridge_light=False):
    """Steep A-frame roof along x over walls x1..x2 / z1..z2 (wall tops at y0-1): two rises per row,
    shingles of spruce stairs over planks, gable ends closed with `end`. Returns the ridge height."""
    w = z2 - z1 + 2
    half = (w + 1) // 2
    for k in range(half + 1):
        zn, zs = z1 - 1 + k, z2 + 1 - k
        if zn > zs:
            break
        hy = y0 + 2 * k - 1
        for x in range(x1 - 1, x2 + 2):
            for z, f in ((zn, "south"), (zs, "north")):
                if zn == zs:
                    d.set(x, hy, z, "spruce_planks")
                    d.set(x, hy + 1, z, slab("spruce_slab"))
                    continue
                if hy - 1 >= y0 - 1 and k > 0:
                    d.set(x, hy - 1, z, "spruce_planks")
                d.set(x, hy, z, stair("spruce_stairs", f))
        # gable ends
        for x in (x1, x2):
            for z in range(zn + 1, zs):
                for y in range(y0, hy + 1 if zn + 1 < zs else hy):
                    if d.air(x, y, z):
                        d.set(x, y, z, end)
    return y0 + 2 * half


def ca_logwall(d, x1, x2, z1, z2, y1, y2, windows=(), door=None):
    """Log cabin walls: corner posts of spruce log, horizontal stripped logs between, window cells (x, z) glazed
    on rows y1+1..y1+2."""
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if not (x in (x1, x2) or z in (z1, z2)):
                continue
            for y in range(y1, y2 + 1):
                corner = x in (x1, x2) and z in (z1, z2)
                if corner:
                    st = "spruce_log[axis=y]"
                elif (x, z) in windows and y1 + 1 <= y <= y1 + 2:
                    st = "glass_pane"
                else:
                    ax = "x" if z in (z1, z2) else "z"
                    st = f"{'stripped_spruce_log' if (y - y1) % 2 == 0 else 'spruce_log'}[axis={ax}]"
                d.set(x, y, z, st)


def ca_lodge(d, L):
    """The lodge on the first terrace: a log great hall with a stone chimney and an A-frame roof (bunk loft from
    L2), a glass conservatory across its front looking over the pond; at L4 it is raised by a log storey (the
    children's garden school) and the conservatory becomes double height; L5 adds a wrap-round porch deck."""
    y0 = 5
    x1, x2, z1, z2 = 31, 43, 18, 24
    two = L >= 4
    wall_top = y0 + (8 if two else 3)
    for x in range(x1, x2 + 1):
        for z in range(15, z2 + 1):
            d.set(x, 4, z, "spruce_planks")
            for y in range(5, wall_top + 1):
                d.set(x, y, z, AIR)
    ca_logwall(d, x1, x2, z1, z2, y0, y0 + 3, windows={(34, 24), (35, 24), (39, 24), (40, 24), (31, 21), (43, 20)})
    for x in range(x1, x2 + 1):                           # joists
        for z in range(z1, z2 + 1):
            if not (x in (x1, x2) or z in (z1, z2)):
                d.set(x, y0 + 4, z, "spruce_planks")
            else:
                d.set(x, y0 + 4, z, f"spruce_log[axis={'x' if z in (z1, z2) else 'z'}]")
    if two:
        ca_logwall(d, x1, x2, z1, z2, y0 + 5, y0 + 8,
                   windows={(33, 18), (34, 18), (36, 18), (38, 18), (40, 18), (41, 18), (34, 24), (39, 24), (31, 21),
                            (43, 21)})
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                if not (x in (x1, x2) or z in (z1, z2)):
                    d.set(x, y0 + 9, z, "spruce_planks")
    ry = y0 + (9 if two else 4)
    top = ca_aframe(d, x1, x2, z1, z2, ry, end="stripped_spruce_log[axis=y]")
    # stone chimney on the east gable
    for y in range(3, top + 2):
        d.set(44, y, 21, "cobblestone" if y % 3 else "mossy_cobblestone")
        if y < top - 2:
            d.set(44, y, 20, "cobblestone")
            d.set(44, y, 22, "cobblestone")
    d.set(44, top + 2, 21, "cobblestone_wall")
    d.hearth(42, y0, 21, "west", y0 + 4, frame="cobblestone", fire="campfire")
    for y in range(y0 + 2, y0 + 4):
        d.set(43, y, 21, "cobblestone")
    # conservatory: glass walls between log posts, glass roof sloping to the front (double height from L4)
    ch = 8 if not two else 12
    for x in range(x1, x2 + 1):
        post = (x - x1) % 3 == 0
        d.set(x, 4, 15, "cobblestone")
        for y in range(5, ch):
            d.set(x, y, 15, "spruce_log[axis=y]" if post else ("glass_pane" if y > 5 else "spruce_planks"))
        d.set(x, ch, 15, stair("spruce_stairs", "south"))
        d.set(x, ch, 16, "glass" if not post else "spruce_planks")
        d.set(x, ch + 1, 17, "glass" if not post else "spruce_planks")
        if two:
            d.set(x, ch + 1, 16, AIR)
    for z in (16, 17):
        for x in (x1, x2):
            for y in range(5, ch):
                d.set(x, y, z, "glass_pane" if y > 5 else "spruce_planks")
            d.set(x, ch, z, "spruce_planks")
            if z == 17:
                d.set(x, ch + 1, z, "spruce_planks")
    d.door(37, y0, z1, "north", "spruce")
    d.door(x1, y0, 16, "west", "spruce")
    for z in (16, 17):
        d.set(x1 - 1, 4, z, "spruce_planks")
    for x, z, st in ((32, 17, "potted_fern"), (33, 17, "potted_flowering_azalea_bush"), (34, 17, "potted_bamboo"),
                     (35, 17, "potted_red_tulip"), (39, 17, "potted_blue_orchid"), (40, 17, "potted_fern"),
                     (42, 17, "potted_flowering_azalea_bush")):
        d.set(x, y0, z, st)
    d.chair(40, y0, 16, "west", "spruce")
    d.chair(42, y0, 16, "east", "spruce")
    d.set(41, y0, 16, slab("spruce_slab", "top"))
    d.set(41, y0 + 1, 16, "potted_red_tulip")
    if two:                                              # hanging baskets in the tall conservatory
        for x in (34, 37, 40):
            lamp_chain(d, x, 9, 16, ch) if False else None
            d.set(x, 10, 16, lv("azalea"))
            d.set(x, 11, 16, "chain[axis=y,waterlogged=false]")
    # great hall (interior x32..42, z19..23): kitchen corner, dining table, sofas at the fire, hut by the door
    hall = ["OcW.....a..",
            ".........R.",
            ".1.1...4RT.",
            "4TtT2..4oR.",
            ".3.3..K.b.f"]
    plan(d, 32, y0, 19, hall, CS, {"O": "south", "K": "north"})
    for x, z in ((34, 21), (39, 21)):
        lamp_chain(d, x, y0 + 2, z, y0 + 4)
    d.hut(36, y0, 20, facing="north")
    if L >= 2:
        for y in range(y0, ry + 1):                       # ladder from the hall up through the house
            d.set(32, y, 21, "ladder[facing=east,waterlogged=false]")
    if two:                                              # garden school: desks facing a chalkboard, reading nook
        yb = y0 + 5
        school = ["......BB...",
                  ".3.3.3.....",
                  ".T.T.T...RR",
                  ".3.3.3...oR",
                  "..........J"]
        school = ["#####..BB.y",
                  "...........",
                  ".T.T.T..RoR",
                  ".3.3.3..oRo",
                  "z.......b.J"]
        plan(d, 32, yb, 19, school, CS, {})
        for x in range(32, 37):
            d.set(x, yb + 1, 19, "black_concrete" if x != 32 else "black_concrete")
            d.set(x, yb, 19, slab("spruce_slab", "top"))
        d.set(32, yb, 19, "ladder[facing=east,waterlogged=false]") if False else None
        for x, z in ((34, 21), (39, 21)):
            d.set(x, yb + 3, z, lantern(True))
    if L >= 2:                                           # loft in the roof: bunk room for visiting gardeners
        ly = ry + 1
        loft = [(34, 21, "bed_w"), (34, 22, "bed_w2"), (40, 21, "bed_e"), (36, 20, "chest"), (40, 22, "barrel"),
                (39, 20, "lantern"), (36, 21, "carpet"), (36, 22, "carpet"), (37, 21, "carpet"), (37, 22, "carpet")]
        for x, z, k in loft:
            if k == "bed_w":
                d.bed(x, ly, z, "west", "brown")
            elif k == "bed_w2":
                d.bed(x, ly, z, "west", "green")
            elif k == "bed_e":
                d.bed(x, ly, z, "east", "orange")
            elif k == "chest":
                d.set(x, ly, z, "chest[facing=south,type=single,waterlogged=false]")
            elif k == "barrel":
                d.set(x, ly, z, "barrel[facing=up,open=false]")
            elif k == "lantern":
                d.set(x, ly, z, lantern())
            else:
                d.set(x, ly, z, "brown_carpet")
        d.set(37, ly + 2, 21, lantern(True))
    if L >= 4:                                           # porch deck on the west side with rocking chairs
        for x in range(26, 31):
            for z in range(18, 25):
                d.set(x, 4, z, "spruce_planks" if (x + z) % 2 else "stripped_spruce_wood[axis=y]") \
                    if x not in (CA_STAIRS) else None
        for z in range(18, 25):
            if z in (21,):
                continue
            d.set(30, 5, z, AIR) if False else None
        for x, z in ((27, 18), (27, 24)):
            for y in range(5, 9):
                d.set(x, y, z, "spruce_log[axis=y]")
        for x in range(26, 31):
            for z in range(17, 26):
                if x in CA_STAIRS:
                    continue
                d.set(x, 9, z, stair("spruce_stairs", "east") if x == 26 else "spruce_planks") if x <= 30 else None
        d.door(x1, y0, 22, "west", "spruce")
        d.chair(29, 5, 19, "south", "spruce")
        d.chair(30, 5, 19, "south", "spruce")
        d.set(30, 5, 23, "potted_fern")
        d.set(27, 8, 21, lantern(True))


def ca_pergola(d, x1, x2, z1, z2, y, vines=True):
    """Timber pergola: log posts at the hand-set corners and middles, beams and rafters, leafy vines on top."""
    for x in (x1, x2):
        for z in (z1, z2):
            for yy in range(y, y + 3):
                d.set(x, yy, z, "spruce_log[axis=y]")
    for x in range(x1, x2 + 1):
        for z in (z1, z2):
            d.set(x, y + 3, z, "stripped_spruce_log[axis=x]")
    for x in range(x1, x2 + 1, 2):
        for z in range(z1, z2 + 1):
            if z not in (z1, z2):
                d.set(x, y + 3, z, "spruce_fence")
            if vines and (x + z) % 3 == 0:
                d.set(x, y + 4, z, lv("azalea") if (x + z) % 2 else lv("flowering_azalea"))


def ca_teahouse(d):
    """Tea house on the third terrace: timber posts on a stone base, shoji-like paper walls (birch trapdoors),
    deep shingle roof; a tea room with low tables and a tea counter."""
    x1, x2, z1, z2, y = 31, 39, 34, 39, 11
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            d.set(x, y - 1, z, "spruce_planks" if not (x in (x1, x2) or z in (z1, z2)) else "stripped_spruce_wood[axis=y]")
            edge = x in (x1, x2) or z in (z1, z2)
            for yy in range(y, y + 4):
                if not edge:
                    d.set(x, yy, z, AIR)
                    continue
                post = (x in (x1, x2) and z in (z1, z2)) or ((x - x1) % 4 == 0 and z in (z1, z2)) or \
                    ((z - z1) % 5 == 0 and x in (x1, x2))
                if post:
                    d.set(x, yy, z, "spruce_log[axis=y]")
                elif yy == y:
                    d.set(x, yy, z, "spruce_planks")
                elif yy == y + 3:
                    d.set(x, yy, z, f"stripped_spruce_log[axis={'x' if z in (z1, z2) else 'z'}]")
                else:
                    d.set(x, yy, z, "white_stained_glass_pane" if (x + z) % 2 else "glass_pane")
    d.hip(x1, z1, x2, z2, y + 4, stairs="spruce_stairs", cap="spruce_slab", overhang=2)
    d.door(35, y, z1, "north", "spruce")
    rows = ["f.T.T.f",
            "..R.R..",
            "4RoRoR2",
            "...c...",
            "a.cic.K"]
    rows = ["f.....f",
            ".4T2...",
            "...4T2.",
            ".......",
            "a.cic.K"]
    plan(d, 32, y, 35, rows, CS, {"K": "north"})
    for x, z in ((34, 36), (37, 37)):
        d.set(x, y + 3, z, lantern(True))
    for x, z in ((32, 37), (38, 35)):
        d.set(x, y, z, "potted_bamboo") if d.air(x, y, z) else None


def ca_lookout(d):
    """Fire lookout on the top terrace: a braced timber tower with a glazed cab, catwalk and hip roof."""
    cx1, cx2, cz1, cz2 = 30, 35, 49, 54
    base = 17
    cab = 30
    for x in (cx1, cx2):
        for z in (cz1, cz2):
            for y in range(base, cab):
                d.set(x, y, z, "spruce_log[axis=y]")
    for y in range(base + 2, cab, 3):                     # cross bracing between the legs
        for x in range(cx1 + 1, cx2):
            for z in (cz1, cz2):
                d.set(x, y, z, "spruce_fence")
        for z in range(cz1 + 1, cz2):
            for x in (cx1, cx2):
                d.set(x, y, z, "spruce_fence")
    for i, y in enumerate(range(base, cab)):              # zig-zag stair inside the legs
        z = cz1 + 1 + (i % 4)
        x = 32 if (i // 4) % 2 == 0 else 33
        d.set(x, y, z, "ladder[facing=north,waterlogged=false]") if False else None
    for y in range(base, cab + 1):
        d.set(32, y, cz2 - 1, "ladder[facing=north,waterlogged=false]")
    d.set(32, base - 1, cz2 - 1, "cobblestone") if False else None
    # cab platform with catwalk
    for x in range(cx1 - 1, cx2 + 2):
        for z in range(cz1 - 1, cz2 + 2):
            d.set(x, cab, z, "spruce_planks")
            if x in (cx1 - 1, cx2 + 1) or z in (cz1 - 1, cz2 + 1):
                d.set(x, cab + 1, z, "spruce_fence")
    d.set(32, cab, cz2 - 1, "ladder[facing=north,waterlogged=false]")
    for x in range(cx1, cx2 + 1):
        for z in range(cz1, cz2 + 1):
            edge = x in (cx1, cx2) or z in (cz1, cz2)
            for y in range(cab + 1, cab + 4):
                if edge:
                    corner = x in (cx1, cx2) and z in (cz1, cz2)
                    d.set(x, y, z, "spruce_log[axis=y]" if corner else ("spruce_planks" if y == cab + 1 else "glass_pane"))
                else:
                    d.set(x, y, z, AIR)
    d.door(33, cab + 1, cz1, "north", "spruce")
    d.hip(cx1, cz1, cx2, cz2, cab + 4, stairs="spruce_stairs", cap="spruce_slab", overhang=1)
    for x, y, z, st in ((31, cab + 1, cz1 + 1, "cartography_table"), (34, cab + 1, cz1 + 1, "lectern[facing=north,has_book=true,powered=false]"),
                        (31, cab + 1, cz2 - 1, "barrel[facing=up,open=false]"), (34, cab + 1, cz2 - 1, stair("spruce_stairs", "east")),
                        (33, cab + 3, 51, lantern(True)), (31, cab + 1, 52, "potted_fern")):
        d.set(x, y, z, st)


def ca_fernhouse(d):
    """L4: timber fern house on the fourth terrace (west): log frame, glass walls, steep glass gable roof;
    tree ferns, mossy beds and a potting corner inside."""
    x1, x2, z1, z2, y = 10, 20, 42, 47, 14
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            edge = x in (x1, x2) or z in (z1, z2)
            d.set(x, y - 1, z, "cobblestone" if edge else ("spruce_planks" if z in (44, 45) else "moss_block"))
            for yy in range(y, y + 5):
                if not edge:
                    d.set(x, yy, z, AIR)
                    continue
                post = (x in (x1, x2) and z in (z1, z2)) or (z in (z1, z2) and (x - x1) % 2 == 0) or \
                    (x in (x1, x2) and (z - z1) % 5 == 0)
                d.set(x, yy, z, "spruce_log[axis=y]" if post else (rock(x, yy, z) if yy == y else "glass_pane"))
    for k in range(4):                                     # glass gable along x
        zn, zs = z1 - 1 + k, z2 + 1 - k
        yy = y + 5 + k
        for x in range(x1 - 1, x2 + 2):
            rib = (x - x1) % 2 == 0
            for z, f in ((zn, "south"), (zs, "north")):
                if zn >= zs:
                    d.set(x, yy, z, "spruce_planks")
                elif k == 0:
                    d.set(x, yy, z, stair("spruce_stairs", f))
                else:
                    d.set(x, yy, z, "spruce_planks" if rib else "glass")
        for x in (x1, x2):
            for z in range(zn + 1, zs):
                d.set(x, yy, z, "glass_pane")
    d.door(15, y, z1, "north", "spruce")
    for x in (13, 17):                                   # stone lanterns either side of the door
        d.set(x, y, z1 - 1, "cobblestone_wall")
        d.set(x, y + 1, z1 - 1, lantern())
    # planting: tree ferns (log + leaves crowns) in the mossy beds, ferns, a potting bench
    for x, z in ((12, 43), (18, 46), (13, 46), (17, 43)):
        d.set(x, y, z, "spruce_log[axis=y]")
        d.set(x, y + 1, z, "spruce_log[axis=y]")
        d.set(x, y + 2, z, lv("jungle"))
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if d.air(x + a, y + 2, z + b) and x1 < x + a < x2 and z1 < z + b < z2:
                d.set(x + a, y + 2, z + b, lv("jungle"))
    for x, z, st in ((11, 43, "fern"), (14, 43, "fern"), (16, 46, "fern"), (19, 43, "fern"), (11, 46, "fern"),
                     (14, 46, "large_fern"), (19, 46, "fern"), (16, 43, "large_fern")):
        if st == "large_fern":
            flower(d, x, y, z, st)
        else:
            d.set(x, y, z, st)
    for x, st in ((11, slab("spruce_slab", "top")), (12, slab("spruce_slab", "top"))):
        d.set(x, y, 44, st)
    d.set(11, y + 1, 44, "potted_fern")
    d.set(12, y + 1, 44, "potted_blue_orchid")
    d.set(19, y, 45, "water_cauldron[level=3]")
    d.set(15, y + 4, 45, lantern(True))


def ca_ranger(d):
    """L5: ranger's cabin by the spring on the top terrace: a small log cabin with a porch and a stone chimney;
    map table, bunk, stove."""
    x1, x2, z1, z2, y = 12, 18, 51, 55, 17
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            d.set(x, y - 1, z, "spruce_planks")
            for yy in range(y, y + 4):
                d.set(x, yy, z, AIR)
    ca_logwall(d, x1, x2, z1, z2, y, y + 3, windows={(14, 51), (17, 51), (12, 53), (18, 53)})
    ca_aframe(d, x1, x2, z1, z2, y + 4, end="stripped_spruce_log[axis=y]")
    for yy in range(y - 1, y + 10):
        d.set(11, yy, 53, "cobblestone" if yy % 2 else "mossy_cobblestone")
    d.set(11, y + 10, 53, "cobblestone_wall")
    d.door(15, y, z1, "north", "spruce")
    for x in range(x1, x2 + 1):                          # porch
        d.set(x, y - 1, z1 - 1, "spruce_planks")
        if x == x1:
            for yy in range(y, y + 3):
                d.set(x, yy, z1 - 1, "spruce_fence")
        d.set(x, y + 3, z1 - 1, stair("spruce_stairs", "south", "top")) if False else None
    d.chair(13, y, z1 - 1, "north", "spruce")
    d.chair(17, y, z1 - 1, "north", "spruce")
    cab = ["mb..O",
           "4T2.F",
           "<.RRb"]
    plan(d, 13, y, 52, cab, CS, {"O": "west", "F": "west"})
    d.set(16, y + 3, 53, lantern(True))


def ca_drapes(d, n):
    """Hanging gardens: azalea and leaves draping over the front lips of the built terraces (hand-picked x)."""
    picks = {0: (5, 9, 14, 33, 37, 41), 1: (7, 11, 16, 32, 36, 40), 2: (9, 13, 17, 31, 35, 39),
             3: (11, 15, 32, 34, 37), 4: (13, 17, 31, 35)}
    for k in range(n):
        x1, x2, z1, z2, top = CA_T[k]
        py = 1 if k == 0 else CA_T[k - 1][4]
        for x in picks[k]:
            if not x1 < x < x2 or not d.air(x, top, z1 - 1):
                continue
            d.set(x, top, z1 - 1, lv("azalea" if x % 2 else "flowering_azalea"))
            if top - 1 > py + 1 and d.air(x, top - 1, z1 - 1):
                d.set(x, top - 1, z1 - 1, lv("azalea"))


def ca_boathouse(d):
    """L4: a little log boathouse with a pier on the west shore of the bottom pond."""
    x1, x2, z1, z2 = 13, 17, 5, 9
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            d.set(x, 1, z, "spruce_planks" if (x, z) != (x2, 7) else "spruce_planks")
            for y in range(2, 5):
                d.set(x, y, z, AIR)
    ca_logwall(d, x1, x2, z1, z2, 2, 4, windows={(15, 5), (13, 7)})
    for x in range(x1, x2 + 1):
        for z in range(z1 - 1, z2 + 2):
            pass
    d.gable(x1, z1, x2, z2, 5, axis="z", stairs="spruce_stairs", ridge="spruce_slab", end="spruce_planks",
            overhang=1)
    d.door(x2, 2, 7, "east", "spruce")
    for x in range(x2 + 1, x2 + 5):                     # pier into the pond on log piles
        for z in (7, 8):
            d.set(x, 1, z, "spruce_planks")
        d.set(x, 2, 6, "spruce_fence") if x % 2 == 0 else None
    d.set(x2 + 4, 2, 9, "spruce_fence")
    d.set(x2 + 4, 3, 9, lantern())
    for x, y, z, st in ((14, 2, 6, "barrel[facing=up,open=false]"), (14, 2, 8, slab("spruce_slab", "top")),
                        (14, 3, 8, lantern()), (16, 2, 6, "barrel[facing=north,open=false]"),
                        (14, 2, 7, "spruce_trapdoor[facing=east,half=top,open=false,powered=false,waterlogged=false]"),
                        (16, 2, 8, "spruce_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")):
        d.set(x, y, z, st)


def ca_summit(d):
    """L5: open timber pavilion over the spring pool on the top terrace."""
    x1, x2, z1, z2, y = 21, 27, 51, 55, 17
    for x in (x1, x2):
        for z in (z1, z2):
            for yy in range(y, y + 4):
                d.set(x, yy, z, "spruce_log[axis=y]")
    d.hip(x1, z1, x2, z2, y + 4, stairs="spruce_stairs", cap="spruce_slab", overhang=1)
    for x in range(x1, x2 + 1):
        for z in (z1, z2):
            if d.air(x, y + 3, z):
                d.set(x, y + 3, z, "stripped_spruce_log[axis=x]")
    for z in range(z1, z2 + 1):
        for x in (x1, x2):
            if d.air(x, y + 3, z):
                d.set(x, y + 3, z, "stripped_spruce_log[axis=z]")
    d.set(24, y + 3, 53, lantern(True))
    d.chair(x1 + 1, y, z1 + 1, "west", "spruce") if d.air(x1 + 1, y, z1 + 1) else None
    d.chair(x2 - 1, y, z1 + 1, "east", "spruce") if d.air(x2 - 1, y, z1 + 1) else None


def ca_outcrops(d):
    """L5: mossy boulder outcrops at the foot of the terrace sides (hand-placed piles)."""
    piles = [(2, 16, 3), (2, 19, 2), (4, 26, 2), (44, 26, 2), (46, 16, 3), (46, 20, 2), (6, 34, 2), (42, 34, 2),
             (8, 42, 2), (40, 42, 2), (10, 49, 2), (38, 50, 2)]
    for x, z, h in piles:
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                hh = h - (abs(dx) + abs(dz))
                for y in range(2, 2 + max(1, hh)):
                    if d.bp.inside(x + dx, y, z + dz) and d.air(x + dx, y, z + dz):
                        d.set(x + dx, y, z + dz, rock(x + dx, y, z + dz))
        if d.air(x, 2 + h, z):
            d.set(x, 2 + h, z, "fern")


def ca_conservatory(d):
    """L5: the great timber conservatory on the third terrace (west): log posts and beams, tall glass walls,
    a steep glass gable roof with a ridge vent; tree ferns, orchids and a fern pool inside."""
    x1, x2, z1, z2, y = 8, 17, 34, 40, 11
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            edge = x in (x1, x2) or z in (z1, z2)
            d.set(x, y - 1, z, rock(x, y - 1, z) if edge else ("spruce_planks" if z == 37 else "moss_block"))
            for yy in range(y, y + 5):
                if not edge:
                    d.set(x, yy, z, AIR)
                    continue
                post = (x in (x1, x2) and z in (z1, z2)) or (z in (z1, z2) and (x - x1) % 3 == 0) or \
                    (x in (x1, x2) and (z - z1) % 3 == 0)
                if post:
                    st = "spruce_log[axis=y]"
                elif yy == y:
                    st = rock(x, yy, z)
                elif yy == y + 4:
                    st = f"stripped_spruce_log[axis={'x' if z in (z1, z2) else 'z'}]"
                else:
                    st = "glass_pane"
                d.set(x, yy, z, st)
    half = (z2 - z1) // 2 + 1
    for k in range(half + 1):
        zn, zs = z1 - 1 + k, z2 + 1 - k
        yy = y + 5 + k
        for x in range(x1 - 1, x2 + 2):
            rib = (x - x1) % 3 == 0
            for z, f in ((zn, "south"), (zs, "north")):
                if zn > zs:
                    continue
                if zn == zs:
                    d.set(x, yy, z, "spruce_planks")
                    d.set(x, yy + 1, z, "spruce_fence" if x % 2 else slab("spruce_slab"))
                elif k == 0:
                    d.set(x, yy, z, stair("spruce_stairs", f))
                else:
                    d.set(x, yy, z, "spruce_planks" if rib else "glass")
        for x in (x1, x2):
            for z in range(zn + 1, zs):
                d.set(x, yy, z, "glass_pane" if (z - z1) % 3 else "spruce_log[axis=y]")
        if zn >= zs:
            break
    d.door(x2, y, 37, "east", "spruce")
    # planting (hand-placed): tree ferns, orchids, a fern pool with stepping stones
    for x, z in ((10, 35), (15, 39), (10, 39), (15, 35)):
        d.set(x, y, z, "spruce_log[axis=y]")
        d.set(x, y + 1, z, "spruce_log[axis=y]")
        d.set(x, y + 2, z, "spruce_log[axis=y]")
        for a, b in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            if x1 < x + a < x2 and z1 < z + b < z2:
                d.set(x + a, y + 3, z + b, lv("jungle"))
    for x in (12, 13):
        for z in (35, 36):
            d.set(x, y - 1, z, WATER)
    d.set(12, y, 35, "lily_pad")
    for x, z, st in ((9, 35, "fern"), (11, 36, "large_fern"), (14, 36, "fern"), (16, 36, "potted_blue_orchid"),
                     (9, 38, "fern"), (11, 39, "potted_blue_orchid"), (13, 38, "large_fern"), (16, 38, "fern"),
                     (12, 39, "fern"), (14, 39, "potted_red_tulip")):
        if st == "large_fern":
            flower(d, x, y, z, st)
        else:
            d.set(x, y, z, st)
    d.chair(9, y, 37, "west", "spruce")
    d.set(12, y + 4, 37, lantern(True))


def big_spruce(d, x, y, z, h):
    """One old-growth spruce: tall trunk, a cone of spruce boughs in alternating wide/narrow tiers."""
    for k in range(h):
        d.set(x, y + k, z, "spruce_log[axis=y]")
    top = y + h
    for i, yy in enumerate(range(y + 3, top + 1)):
        r = max(0, min(3, (top - yy + 2) // 2)) - (i % 2 if yy < top - 1 else 0)
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                if abs(dx) + abs(dz) > r + (1 if r >= 2 else 0) or (dx, dz) == (0, 0):
                    continue
                if d.bp.inside(x + dx, yy, z + dz) and d.air(x + dx, yy, z + dz):
                    d.set(x + dx, yy, z + dz, lv("spruce"))
    d.set(x, top, z, lv("spruce"))
    d.set(x, top + 1, z, lv("spruce"))


def ca_gazebo(d):
    """L5: octagonal timber gazebo on the east shore of the pond, with a bench ring and a shingle roof."""
    cx, cz = 33, 7
    cells = [(cx + a, cz + b) for a in range(-2, 3) for b in range(-2, 3) if abs(a) + abs(b) <= 3]
    for x, z in cells:
        d.set(x, 1, z, "spruce_planks")
        d.set(x, 0, z, SOLIDSUB)
    for x, z in cells:
        edge = abs(x - cx) == 2 or abs(z - cz) == 2 or abs(x - cx) + abs(z - cz) == 3
        if edge and (abs(x - cx) == 2 and abs(z - cz) == 1 or abs(z - cz) == 2 and abs(x - cx) == 1):
            for y in range(2, 5):
                d.set(x, y, z, "spruce_log[axis=y]")
    d.hip(cx - 2, cz - 2, cx + 2, cz + 2, 5, stairs="spruce_stairs", cap="spruce_slab", overhang=1)
    for x, z, f in ((cx - 1, cz - 2, "north"), (cx + 1, cz + 2, "south"), (cx + 2, cz - 1, "east"), (cx - 2, cz + 1, "west")):
        d.chair(x, 2, z, f, "spruce")
    d.set(cx, 4, cz, lantern(True))
    d.set(cx, 2, cz, "spruce_fence")
    d.set(cx, 3, cz, "potted_fern")


def ca_logbridge(d, z, y):
    """A log footbridge over the stream channel (x 22..26) on a terrace top at walk height y+1."""
    for x in range(21, 28):
        d.set(x, y + 1, z, "stripped_spruce_log[axis=x]" if x in (21, 27) else "spruce_slab[type=bottom,waterlogged=false]")
    for x in (21, 27):
        d.set(x, y + 2, z - 1, "spruce_fence")
        d.set(x, y + 2, z + 1, "spruce_fence")


def ca_gardens(rel, L):
    sx, sy, sz = CA["size"]
    d = Design("Cascadia", rel, CA["size"], paving="coarse_dirt")
    for x in range(sx):
        for z in range(sz):
            d.set(x, 1, z, GRASS)
    n = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5}[L]
    for k in range(n):
        ca_terrace(d, k, k == n - 1)
    # the bottom pond: ragged rock rim, lily pads, the first fall lands in it
    pond = set()
    for x in range(15, 34):
        for z in range(6, 15):
            if ((x - 24) / 9.5) ** 2 + ((z - 11) / 5.0) ** 2 <= 1.0 or (22 <= x <= 26 and z == 14):
                pond.add((x, z))
    for x, z in pond:
        d.set(x, 1, z, WATER)
        d.set(x, 0, z, SOLIDSUB)
    for x in range(13, 36):
        for z in range(4, 15):
            if (x, z) in pond:
                continue
            if any((x + a, z + b) in pond for a in (-1, 0, 1) for b in (-1, 0, 1)):
                d.set(x, 1, z, rock(x, 1, z))
                if (x * 5 + z) % 4 == 0:
                    d.set(x, 2, z, ("mossy_cobblestone", "fern", "large_fern", "fern")[(x + z) % 4]) \
                        if (x + z) % 4 != 2 else flower(d, x, 2, z, "large_fern")
    for x, z in ((18, 10), (21, 8), (28, 9), (30, 12), (25, 7)):
        d.set(x, 2, z, "lily_pad")
    # entrance path round the pond to both stair flights
    for z in range(0, 15):
        for x in (19, 20, 28, 29):
            if (x, z) not in pond and d.get(x, 1, z) == "minecraft:" + GRASS:
                d.set(x, 1, z, "coarse_dirt")
    for x in range(12, 37):
        for z in (1, 2):
            d.set(x, 1, z, "coarse_dirt" if (x + z) % 3 else "gravel")
    for z in range(2, 15):
        for x in (13, 35):
            d.set(x, 1, z, "coarse_dirt")
    for x in range(13, 36):
        if (x, 14) not in pond and d.get(x, 1, 14) == "minecraft:" + GRASS:
            d.set(x, 1, 14, "gravel")
    for x, z in ((12, 3), (36, 3), (17, 14), (31, 14)):
        lamppost(d, x, z, 2, 2, "spruce_fence", lantern())
    bench(d, 16, 2, 3, "north", "spruce", 2)
    bench(d, 31, 2, 3, "north", "spruce", 2)
    # the lodge on the first terrace
    ca_lodge(d, L)
    # first terrace west: pergola walk with benches over the stream view
    ca_pergola(d, 6, 16, 18, 22, 5)
    for x in (8, 12):
        d.chair(x, 5, 19, "north", "spruce")
        d.chair(x + 1, 5, 19, "north", "spruce")
    for x, z in ((7, 21), (15, 21), (11, 21)):
        d.set(x, 5, z, ("potted_fern", "potted_flowering_azalea_bush", "potted_fern")[x % 3])
    tree(d, 4, 5, 23, 4, "spruce_log", "spruce", r=1)
    if L >= 2:                                           # second terrace: terraced vegetable beds and a tool shed
        for x1 in (7, 32):
            for x in range(x1, x1 + 9):
                for z in (27, 28, 30, 31):
                    d.set(x, 7, z, "farmland[moisture=7]")
                    d.set(x, 8, z, ("wheat[age=7]", "carrots[age=7]", "potatoes[age=7]", "beetroots[age=3]")[(z + x1) % 4])
                d.set(x, 7, 29, WATER if x % 4 == 0 else "coarse_dirt")
                d.set(x, 8, 29, AIR)
            d.set(x1 - 1, 8, 29, "composter[level=7]")
            d.set(x1 + 9, 8, 29, "barrel[facing=up,open=false]")
        for x, z in ((6, 26), (42, 26), (17, 31), (31, 26)):
            lamppost(d, x, z, 8, 2, "spruce_fence", lantern())
        bench(d, 13, 8, 26, "north", "spruce", 2)
        bench(d, 34, 8, 26, "north", "spruce", 2) if False else None
    if L >= 3:                                           # third terrace: tea house east, rock garden west
        ca_teahouse(d)
    if L in (3, 4):
        for x, z, st in ((9, 35, "mossy_cobblestone"), (10, 35, "fern"), (12, 36, "andesite"), (13, 37, "large_fern"),
                         (15, 35, "mossy_cobblestone"), (10, 38, "sweet_berry_bush[age=3]"), (16, 38, "fern"),
                         (14, 39, "mossy_cobblestone"), (8, 39, "fern")):
            if st == "large_fern":
                flower(d, x, 11, z, "large_fern")
            else:
                d.set(x, 11, z, st)
        tree(d, 11, 11, 37, 5, "spruce_log", "spruce", r=2)
        tree(d, 17, 11, 39, 4, "birch_log", "birch", r=1)
        bench(d, 13, 11, 34, "north", "spruce", 2)
        for x, z in ((8, 36), (15, 37), (9, 40)):        # stone lanterns in the rock garden
            d.set(x, 11, z, "cobblestone_wall")
            d.set(x, 12, z, "cobblestone_wall")
            d.set(x, 13, z, lantern())
    ca_drapes(d, n)
    if L >= 4:                                           # lanterns at the head of every stair flight
        for k in range(n):
            x1, x2, z1, z2, top = CA_T[k]
            for x in (18, 30):
                if d.air(x, top + 1, z1 + 3):
                    lamppost(d, x, z1 + 3, top + 1, 2, "spruce_fence", lantern())
        bench(d, 13, 11, 40, "south", "spruce", 2) if L == 4 else None
        bench(d, 34, 8, 26, "north", "spruce", 2)
        for x, z in ((22, 43), (26, 43), (22, 45), (26, 45)):   # lanterns hung under the rope bridge rails
            d.set(x, 17, z, lantern())
        for x1, x2 in ((7, 15), (32, 40)):               # hanging baskets in the bean tunnels
            for x in range(x1 + 2, x2 - 1, 3):
                d.set(x, 10, 29, lv("flowering_azalea"))
                d.set(x, 9, 29, "chain[axis=y,waterlogged=false]") if False else None
    if L >= 4:                                           # tea house veranda (engawa) on the north and west
        for x in range(30, 41):
            d.set(x, 10, 33, "spruce_planks")
        for z in range(34, 41):
            d.set(30, 10, z, "spruce_planks")
        d.chair(31, 11, 33, "north", "spruce") if False else None
        d.set(32, 11, 33, "potted_bamboo")
        d.set(38, 11, 33, "potted_fern")
    if L >= 4:                                           # fourth terrace: fern house, orchard, rope bridge
        ca_fernhouse(d)
        ca_boathouse(d)
        ca_pergola(d, 30, 38, 42, 46, 14)
        ca_pergola(d, 7, 15, 27, 31, 8)                  # bean-tunnel pergolas over the vegetable beds
        ca_pergola(d, 32, 40, 27, 31, 8)
        for x, z in ((32, 43), (36, 45), (31, 46)):
            tree(d, x, 14, z, 3, "oak_log", "oak", r=2)
        for x in range(21, 28):
            d.set(x, 15, 44, "spruce_planks" if x % 2 else "stripped_spruce_wood[axis=x]")
            d.set(x, 16, 43, "spruce_fence")
            d.set(x, 16, 45, "spruce_fence")
        for x in (21, 27):
            for y in (14, 15, 16, 17):
                for z in (43, 45):
                    d.set(x, y, z, "spruce_log[axis=y]")
            d.set(x, 18, 43, lantern())
        bench(d, 34, 14, 42, "north", "spruce", 2)
        d.set(18, 14, 42, "beehive[facing=north,honey_level=3]")
        d.set(18, 13, 42, "spruce_planks") if False else None
    if L >= 5:
        ca_lookout(d)
        ca_ranger(d)
        ca_summit(d)
        ca_outcrops(d)
        ca_conservatory(d)
        ca_gazebo(d)
        ca_logbridge(d, 29, 7)
        ca_logbridge(d, 37, 10)
        for x in range(28, 38):                          # lower observation deck round the lookout legs
            for z in range(47, 57):
                if x in (28, 37) or z in (47, 56):
                    if d.bp.inside(x, 23, z):
                        d.set(x, 23, z, "spruce_planks")
                        d.set(x, 24, z, "spruce_fence")
        for x in range(29, 37):
            for z in range(48, 56):
                if (x in (29, 36) or z in (48, 55)) and d.air(x, 23, z):
                    d.set(x, 23, z, "spruce_planks")
        ca_pergola(d, 7, 17, 26, 26, 8) if False else None
        for x, z in ((20, 33), (28, 39)):
            tree(d, x, 11, z, 6, "spruce_log", "spruce", r=2)
        for x, y, z, h in ((12, 17, 48, 12), (37, 17, 50, 11), (38, 14, 46, 10), (40, 11, 38, 9), (6, 8, 27, 9)):
            big_spruce(d, x, y, z, h)                    # old-growth spruces on the summit flanks
        for x, z in ((8, 31), (40, 31)):
            tree(d, x, 8, z, 6, "spruce_log", "spruce", r=2)
        # timber entrance gate with the garden's name board
        for x in (18, 30):
            for y in range(2, 7):
                d.set(x, y, 0, "spruce_log[axis=y]")
            d.set(x, 1, 0, "cobblestone")
        for x in range(17, 32):
            d.set(x, 7, 0, "spruce_log[axis=x]")
            d.set(x, 8, 0, stair("spruce_stairs", "south") if x % 2 else slab("spruce_slab"))
        for x in range(19, 30):
            d.set(x, 6, 0, "stripped_spruce_log[axis=x]") if x in (19, 29) else None
        d.sign(24, 6, 0, "north", ["", "Cascade", "Gardens", ""], "spruce")
        for x in (17, 31):
            d.set(x, 6, 0, lantern(True))
    place_wings(d, CA["res"], CA["wsize"], CA["whut"])
    connect_walls(d)
    return d


def ca_wing(rel, L):
    """Potting glasshouse: river-rock footing, log frame, glass walls and a glass gable roof; potting bench,
    seed trays, tubs and a water butt."""
    d = wing_design("Cascadia", rel, CA["wsize"])
    hx, hz = CA["whut"][0], CA["whut"][2]
    for x in range(11):
        for z in range(11):
            d.set(x, 0, z, "coarse_dirt")
    w = {1: (2, 8, 3, 7), 2: (2, 8, 2, 8), 3: (1, 9, 1, 9), 4: (0, 10, 1, 9), 5: (0, 10, 0, 10)}[L]
    x1, x2, z1, z2 = w
    wall_h = {1: 3, 2: 3, 3: 4, 4: 5, 5: 5}[L]
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            edge = x in (x1, x2) or z in (z1, z2)
            d.set(x, 0, z, "cobblestone" if edge else ("spruce_planks" if (x + z) % 2 else "stripped_spruce_wood[axis=y]"))
            if not edge:
                continue
            for y in range(1, wall_h + 1):
                post = (x in (x1, x2) and z in (z1, z2)) or (z in (z1, z2) and (x - x1) % 2 == 0) or \
                    (x in (x1, x2) and (z - z1) % 2 == 0)
                if y == 1:
                    st = rock(x, y, z)
                elif post:
                    st = "spruce_log[axis=y]"
                else:
                    st = "glass_pane"
                d.set(x, y, z, st)
    # glass gable roof along x
    half = (z2 - z1) // 2 + 1
    for k in range(half + 1):
        zn, zs = z1 - 1 + k, z2 + 1 - k
        y = wall_h + 1 + k
        for x in range(max(0, x1 - (1 if L >= 3 else 0)), min(10, x2 + (1 if L >= 3 else 0)) + 1):
            rib = (x - x1) % 2 == 0
            for z, f in ((zn, "south"), (zs, "north")):
                if zn > zs or not 0 <= z <= 10:
                    continue
                if zn == zs:
                    d.set(x, y, z, "spruce_planks")
                elif k == 0:
                    d.set(x, y, z, stair("spruce_stairs", f))
                else:
                    d.set(x, y, z, "spruce_planks" if rib else "glass")
        for x in (x1, x2):
            for z in range(zn + 1, zs):
                d.set(x, y, z, "glass_pane" if (z - z1) % 2 else "spruce_log[axis=y]")
        if zn >= zs:
            break
    for z in (z1, z2):
        d.door(5, 1, z, "north" if z == z1 else "south", "spruce")
    d.hut(hx, 1, hz, facing="north")
    d.item(10 - hx, 1, hz, "composter")
    # potting bench along the west wall, seed trays, tubs (per level)
    items = [(hx, 1, hz + 1, "slab"), (hx, 2, hz + 1, "pot_f"), (7, 1, hz + 1, "barrel")]
    if L >= 2:
        items += [(2, 1, 3 if z1 <= 2 else 4, "tub"), (8, 1, 7, "tub"), (2, 1, 7, "cauldron")]
    if L >= 3:
        items += [(3, 1, 2, "slab"), (4, 1, 2, "slab"), (3, 2, 2, "pot_t"), (4, 2, 2, "pot_b"), (8, 1, 2, "tub"),
                  (6, 1, 8, "slab"), (6, 2, 8, "pot_f")]
    if L >= 4:
        items += [(1, 1, 5, "slab"), (1, 2, 5, "pot_t"), (9, 1, 5, "slab"), (9, 2, 5, "pot_f"), (4, 1, 8, "barrel")]
    if L >= 5:
        items += [(1, 1, 9, "tub"), (9, 1, 9, "tub"), (1, 1, 1, "tub"), (9, 1, 1, "cauldron")]
    for x, y, z, k in items:
        if k == "slab":
            d.set(x, y, z, slab("spruce_slab", "top"))
        elif k == "pot_f":
            d.set(x, y, z, "potted_fern")
        elif k == "pot_t":
            d.set(x, y, z, "potted_red_tulip")
        elif k == "pot_b":
            d.set(x, y, z, "potted_blue_orchid")
        elif k == "barrel":
            d.set(x, y, z, "barrel[facing=up,open=false]")
        elif k == "cauldron":
            d.set(x, y, z, "water_cauldron[level=3]")
        elif k == "tub":
            d.set(x, y, z, "composter[level=8]" if False else "moss_block")
            d.set(x, y + 1, z, lv("azalea"))
    d.set(5, wall_h, 5, lantern(True)) if L >= 3 else None
    if L >= 5:                                           # stove chimney for the heated glasshouse, rain butts
        for y in range(1, 10):
            d.set(10, y, 10, "cobblestone" if y % 3 else "mossy_cobblestone")
        d.set(10, 10, 10, "cobblestone_wall")
        d.set(9, 1, 9, "furnace[facing=north,lit=false]") if False else None
    return d


@design("hanginggardens")
def hanginggardens(pack, rel, L):
    return {"Neoterra": nt_gardens, "Hearthwood": hw_gardens, "Cascadia": ca_gardens}[pack](rel, L)


@design("hanginggardenswing")
def hanginggardenswing(pack, rel, L):
    return {"Neoterra": nt_wing, "Hearthwood": hw_wing, "Cascadia": ca_wing}[pack](rel, L)
