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
            if yy == y or name(x + dx, yy - 1, z + dz) != "water":
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
        d.set(x, y - 1, z, WATER)
        d.set(x, y, z, trap(S.get("trapw", w), "north", "bottom"))
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
